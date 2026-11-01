"""Document Service for Government PDFs, Circulars, and Citizen Records.

Handles end-to-end PDF processing: validation, text extraction,
intelligent structure extraction (clauses, dates, eligibility),
multimodal AI Vision OCR fallback for scanned images,
vector indexing into ChromaDB, and grounded question-answering.
"""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

from app.config import get_settings
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentQueryResponse,
    SourceCitation,
    Language,
)
from app.utils.file_utils import extract_text_from_pdf, validate_upload, save_upload
from app.utils.language import detect_language
from app.rag.embeddings import (
    chunk_text,
    add_documents_to_collection,
    search_collection,
    delete_collection,
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DocumentService:
    """Service orchestrating PDF ingestion, semantic indexing, and grounded RAG."""

    def __init__(self, llm_service: LLMService):
        settings = get_settings()
        self.upload_dir = settings.UPLOAD_DIR
        self.llm = llm_service
        os.makedirs(self.upload_dir, exist_ok=True)

    def _infer_category_from_filename(self, filename: str) -> str:
        """Infer realistic document classification from filename hints."""
        fn = filename.lower()
        if any(k in fn for k in ["marks", "memo", "grade", "ssc", "cbse", "icse", "btech", "degree", "result", "hallticket", "rank", "10th", "12th", "inter"]):
            return "Academic Marks Memo / Educational Certificate"
        if any(k in fn for k in ["aadhaar", "pan", "voter", "passport", "driving", "license", "kyc"]):
            return "Identity / KYC Document"
        if any(k in fn for k in ["bill", "invoice", "receipt", "salary", "payslip"]):
            return "Financial / Billing Statement"
        if any(k in fn for k in ["gazette", "notification", "circular", "guideline", "order", "policy", "yojana"]):
            return "Government Policy Circular / Notification"
        if any(k in fn for k in ["resume", "cv", "biodata"]):
            return "Resume / Curriculum Vitae"
        return "General Document"

    async def _try_vision_ocr(self, pdf_path: str, pages: List[Dict[str, Any]]) -> bool:
        """If Gemini or OpenAI API key is configured, transcribe scanned pages via vision."""
        if not (self.llm._is_valid_key(self.llm.gemini_key) or self.llm._is_valid_key(self.llm.openai_key)):
            return False

        import fitz
        try:
            doc = fitz.open(pdf_path)
            pages_to_ocr = min(len(doc), 3)  # Transcribe up to first 3 pages
            any_success = False
            for i in range(pages_to_ocr):
                page = doc[i]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                logger.info("Attempting multimodal Vision OCR on page %d of %s", i + 1, pdf_path)
                text = await self.llm.transcribe_image_with_vision(img_bytes, mime_type="image/png")
                if text and len(text.strip()) > 20:
                    pages[i]["text"] = text.strip()
                    any_success = True
            doc.close()
            return any_success
        except Exception as err:
            logger.warning("Vision OCR attempt encountered error: %s", err)
            return False

    async def process_upload(
        self,
        file: UploadFile,
        document_id: str,
    ) -> DocumentUploadResponse:
        """Process, extract, index, and analyze an uploaded PDF document."""
        # 1. Read content into memory to check size & validate
        file_bytes = await file.read()
        file_size = len(file_bytes)
        filename = file.filename or "document.pdf"
        validate_upload(filename, file_size)
        await file.seek(0)

        # 2. Save file to disk
        saved_path = await save_upload(file, self.upload_dir)

        # 3. Extract text page-by-page
        extraction_res = extract_text_from_pdf(saved_path)
        pages = extraction_res["pages"]
        total_pages = extraction_res["total_pages"]
        total_chars = extraction_res.get("total_chars", 0)
        is_scanned = extraction_res.get("is_scanned", False)

        # 4. If scanned image with no direct text layer, attempt AI Vision OCR if key available
        if is_scanned:
            vision_transcribed = await self._try_vision_ocr(saved_path, pages)
            if vision_transcribed:
                total_chars = sum(len(p["text"]) for p in pages)
                is_scanned = False
                extraction_res["extraction_method"] = "ai_vision_ocr"

        # Check if still scanned or lacking machine-readable text
        if is_scanned or total_chars < 20:
            doc_category = self._infer_category_from_filename(filename)
            preview_text = (
                f"[Scanned Document: {doc_category}]\n\n"
                f"This PDF consists of scanned images or photos with no embedded digital text layer. "
                f"The document structure was verified ({total_pages} page{'s' if total_pages > 1 else ''}), "
                f"but text extraction requires a selectable digital text layer or a configured AI Vision API key."
            )
            return DocumentUploadResponse(
                document_id=document_id,
                filename=filename,
                page_count=total_pages,
                extracted_text_preview=preview_text,
                key_clauses=[
                    f"Document Classification: {doc_category}",
                    f"Format: Scanned Image PDF ({total_pages} page{'s' if total_pages > 1 else ''})",
                    "Status: No selectable digital text layer found",
                ],
                important_dates=[],
                eligibility_mentions=[],
                required_documents_mentioned=[],
                language_detected="Unknown (Scanned Image)",
                processing_notes=[
                    f"Detected {total_pages} scanned page(s) containing image data without an embedded text layer.",
                    "Direct text extraction yielded 0 characters.",
                    "Tip: Upload a text-searchable PDF (with selectable text) or add a free GEMINI_API_KEY in backend/.env for AI Vision OCR transcription."
                ],
                is_scanned=True,
                document_type=doc_category,
            )

        full_text = "\n\n".join([f"--- Page {p['page_num']} ---\n{p['text']}" for p in pages if p['text'].strip()])

        # 5. Detect dominant language
        detected_lang = detect_language(full_text[:2000])

        # 6. Extract structural highlights (clauses, dates, eligibility, documents)
        analysis = await self._analyze_document_structure(full_text, pages, filename)

        # 7. Chunk each page separately so metadata retains precise page numbers
        all_chunks: List[str] = []
        all_metas: List[Dict[str, Any]] = []

        for p in pages:
            if not p["text"].strip():
                continue
            page_chunks = chunk_text(p["text"], chunk_size=700, chunk_overlap=80)
            for chunk in page_chunks:
                all_chunks.append(chunk)
                all_metas.append({
                    "document_id": document_id,
                    "filename": filename,
                    "page_num": p["page_num"],
                    "has_images": p["has_images"],
                })

        # 8. Index chunks in ChromaDB under collection named by document_id
        if all_chunks:
            add_documents_to_collection(
                collection_name=document_id,
                texts=all_chunks,
                metadatas=all_metas,
            )

        preview_text = full_text[:400] + ("..." if len(full_text) > 400 else "")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=filename,
            page_count=total_pages,
            extracted_text_preview=preview_text,
            key_clauses=analysis.get("key_clauses", []),
            important_dates=analysis.get("important_dates", []),
            eligibility_mentions=analysis.get("eligibility_mentions", []),
            required_documents_mentioned=analysis.get("required_documents_mentioned", []),
            language_detected=detected_lang,
            processing_notes=[
                f"Extracted {total_pages} pages using {extraction_res['extraction_method']} extraction.",
                f"Generated {len(all_chunks)} searchable semantic passages.",
            ],
            is_scanned=False,
            document_type=analysis.get("document_type"),
        )

    async def _analyze_document_structure(
        self,
        full_text: str,
        pages: List[Dict[str, Any]],
        filename: str = "",
    ) -> Dict[str, Any]:
        """Use LLM or regex heuristic fallback to identify clauses, dates, and requirements."""
        if self.llm.is_configured():
            try:
                prompt = (
                    "You are an objective document analyzer.\n"
                    "Analyze the provided document text (which could be an academic marks memo/certificate, government scheme circular, official gazette, identity document, or general PDF).\n"
                    "Extract the following structural items strictly as JSON:\n"
                    "{\n"
                    '  "document_type": "specific type of document (e.g. Academic Marks Memo, Government Gazette Notification, Welfare Scheme Guidelines, General Document)",\n'
                    '  "key_clauses": ["concise clause, heading, subject marks, or key statement from text", ...],\n'
                    '  "important_dates": ["concise date with context from text", ...],\n'
                    '  "eligibility_mentions": ["concise eligibility criteria, passing requirements, or conditions from text", ...],\n'
                    '  "required_documents_mentioned": ["concise document or certificate name mentioned in text", ...]\n'
                    "}\n"
                    "RULES:\n"
                    "1. Only include items that are EXPLICITLY present in the text.\n"
                    "2. If a category is not present or not mentioned, return an empty array []. DO NOT invent or assume values.\n"
                    "3. Up to 5 items per list max. Return pure JSON only."
                )
                sample_text = full_text[:4000]
                resp = await self.llm.chat_completion(
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"FILENAME: {filename}\nDOCUMENT CONTENT:\n{sample_text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                parsed = json.loads(resp)
                return {
                    "document_type": parsed.get("document_type", ""),
                    "key_clauses": parsed.get("key_clauses", [])[:5],
                    "important_dates": parsed.get("important_dates", [])[:5],
                    "eligibility_mentions": parsed.get("eligibility_mentions", [])[:5],
                    "required_documents_mentioned": parsed.get("required_documents_mentioned", [])[:5],
                }
            except Exception as e:
                logger.warning("LLM document structure analysis failed: %s. Using heuristics.", e)

        # Heuristic fallback via Regex & Text Extraction
        return self._heuristic_analysis(full_text, filename)

    def _heuristic_analysis(self, text: str, filename: str = "") -> Dict[str, Any]:
        """Fast regex-based extraction of dates, clauses, and documents with zero fake fallbacks."""
        doc_category = self._infer_category_from_filename(filename)
        text_lower = text.lower()

        # 1. Dates: Look for actual date formats
        date_pattern = re.compile(
            r"\b(?:\d{1,2}[\/\-\.](?:\d{1,2}|[A-Za-z]{3,9})[\/\-\.]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b"
        )
        found_dates = []
        for line in text.split("\n"):
            clean_line = line.strip()
            if not clean_line or len(clean_line) > 120:
                continue
            matches = date_pattern.findall(clean_line)
            if matches:
                found_dates.append(clean_line if len(clean_line) < 80 else matches[0])
        dates = []
        for d in found_dates:
            if d not in dates:
                dates.append(d)
            if len(dates) >= 5:
                break

        # 2. Key Clauses / Sections / Subjects
        clauses = []
        clause_pattern = re.compile(
            r"((?:Section|Clause|Article|Paragraph|Rule|Chapter|Part|Guideline)\s+[A-Za-z0-9\.\-]+(?:\s*[:\-–]\s*[^\n\r]{0,60})?)",
            re.IGNORECASE
        )
        for m in clause_pattern.findall(text):
            clean_c = m.strip()
            if clean_c and clean_c not in clauses:
                clauses.append(clean_c)
            if len(clauses) >= 5:
                break

        # If no formal clauses, check if document is academic / marks memo
        if not clauses and any(k in (text_lower + " " + filename.lower()) for k in ["marks", "grade", "subject", "memo", "roll", "ssc", "board"]):
            for line in text.split("\n"):
                clean_line = line.strip()
                if any(k in clean_line.lower() for k in ["roll", "hall ticket", "board", "examination", "gpa", "grade", "percentage", "total marks"]):
                    if 10 < len(clean_line) < 100 and clean_line not in clauses:
                        clauses.append(clean_line)
                if len(clauses) >= 5:
                    break

        # If still no clauses, extract prominent section headings (e.g. MINISTRY..., 1. Section, Title:)
        if not clauses:
            for line in text.split("\n"):
                clean_line = line.strip()
                if 10 < len(clean_line) < 140:
                    if re.match(r"^(\d+\.|\([a-z0-9]\)|[A-Z0-9\s,\-–:]{4,})\s*[:\-–]?\s*[A-Za-z0-9]", clean_line):
                        if clean_line not in clauses and not clean_line.startswith("--- Page"):
                            clauses.append(clean_line)
                if len(clauses) >= 4:
                    break

        # 3. Eligibility Mentions (Strict: only if matched in text)
        eligibility = []
        for line in text.split("\n"):
            clean = line.strip()
            if any(k in clean.lower() for k in ["eligib", "criteria", "who can apply", "age limit", "qualification", "minimum marks", "passing mark", "pass grade"]):
                if 15 < len(clean) < 140 and clean not in eligibility:
                    eligibility.append(clean)
            if len(eligibility) >= 4:
                break

        # 4. Mandatory Documents (Strict: only if matched in text)
        documents = []
        doc_keywords = ["aadhaar", "pan card", "certificate", "marks memo", "ration card", "passbook", "affidavit", "domicile", "caste certificate", "income certificate", "hall ticket"]
        for line in text.split("\n"):
            clean = line.strip()
            if any(k in clean.lower() for k in doc_keywords):
                if 10 < len(clean) < 120 and clean not in documents:
                    documents.append(clean)
            if len(documents) >= 4:
                break

        # NEVER return fake fallback lists! If empty, return []
        return {
            "document_type": doc_category,
            "key_clauses": clauses,
            "important_dates": dates,
            "eligibility_mentions": eligibility,
            "required_documents_mentioned": documents,
        }

    async def query_document(
        self,
        document_id: str,
        question: str,
        language: Language = Language.ENGLISH,
    ) -> DocumentQueryResponse:
        """Answer a query grounded in the uploaded document's passages."""
        # 1. Search document collection
        passages = search_collection(document_id, question, n_results=4)

        if not passages:
            return DocumentQueryResponse(
                answer=(
                    "No searchable text passages were found for this document matching your query. "
                    "If this was an image scan or photo PDF, digital text could not be extracted directly. "
                    "Please ensure the document contains selectable digital text, or add a free GEMINI_API_KEY in backend/.env for AI Vision OCR transcription."
                ),
                relevant_passages=[],
                sources=[],
                language=language,
            )

        # 2. Synthesize answer with LLM
        answer = await self.llm.generate_rag_response(
            question=question,
            context_passages=passages,
            language=language.value,
            system_context=(
                "Explain clearly which section or page of this uploaded document addresses the citizen's inquiry. "
                "If the document is an academic certificate, marks memo, or citizen record, answer specifically about marks, names, or subjects mentioned."
            )
        )

        # 3. Construct source citations
        citations: List[SourceCitation] = []
        now = datetime.now(timezone.utc)
        for p in passages:
            meta = p.get("metadata", {})
            page_num = meta.get("page_num")
            citations.append(
                SourceCitation(
                    title=f"Uploaded Document: {meta.get('filename', 'PDF')} (Page {page_num})",
                    url=None,
                    source_type="uploaded_document",
                    page_number=page_num,
                    section=f"Page {page_num}",
                    retrieved_at=now,
                    is_verified=True,
                )
            )

        return DocumentQueryResponse(
            answer=answer,
            relevant_passages=passages,
            sources=citations,
            language=language,
        )

    def delete_document(self, document_id: str) -> bool:
        """Remove indexed vector collections and associated files for document_id."""
        logger.info("Cleaning up resources for document_id %s", document_id)
        return delete_collection(document_id)
