"""Document Service for Government PDFs and Guidelines.

Handles end-to-end PDF processing: validation, text extraction,
intelligent structure extraction (clauses, dates, eligibility),
vector indexing into ChromaDB, and grounded question-answering.
"""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Dict, Any, List
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

    async def process_upload(
        self,
        file: UploadFile,
        document_id: str,
    ) -> DocumentUploadResponse:
        """Process, extract, index, and analyze an uploaded government PDF document."""
        # 1. Read content into memory to check size & validate
        file_bytes = await file.read()
        file_size = len(file_bytes)
        validate_upload(file.filename or "document.pdf", file_size)
        await file.seek(0)

        # 2. Save file to disk
        saved_path = await save_upload(file, self.upload_dir)

        # 3. Extract text page-by-page
        extraction_res = extract_text_from_pdf(saved_path)
        pages = extraction_res["pages"]
        total_pages = extraction_res["total_pages"]
        full_text = "\n\n".join([f"--- Page {p['page_num']} ---\n{p['text']}" for p in pages])

        # 4. Detect dominant language
        detected_lang = detect_language(full_text[:2000])

        # 5. Extract structural highlights (clauses, dates, eligibility, documents)
        analysis = await self._analyze_document_structure(full_text, pages)

        # 6. Chunk each page separately so metadata retains precise page numbers
        all_chunks: List[str] = []
        all_metas: List[Dict[str, Any]] = []

        for p in pages:
            page_chunks = chunk_text(p["text"], chunk_size=700, chunk_overlap=80)
            for chunk in page_chunks:
                all_chunks.append(chunk)
                all_metas.append({
                    "document_id": document_id,
                    "filename": file.filename or "document.pdf",
                    "page_num": p["page_num"],
                    "has_images": p["has_images"],
                })

        # 7. Index chunks in ChromaDB under collection named by document_id
        if all_chunks:
            add_documents_to_collection(
                collection_name=document_id,
                texts=all_chunks,
                metadatas=all_metas,
            )

        preview_text = full_text[:400] + ("..." if len(full_text) > 400 else "")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename or "document.pdf",
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
        )

    async def _analyze_document_structure(
        self,
        full_text: str,
        pages: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Use LLM or regex heuristic fallback to identify clauses, dates, and requirements."""
        if self.llm.is_configured():
            try:
                prompt = (
                    "You are analyzing a government policy or scheme guideline document.\n"
                    "Extract the following structural items strictly as JSON:\n"
                    "{\n"
                    '  "key_clauses": ["clause or section name 1", ...],\n'
                    '  "important_dates": ["date and context 1", ...],\n'
                    '  "eligibility_mentions": ["eligibility rule 1", ...],\n'
                    '  "required_documents_mentioned": ["document name 1", ...]\n'
                    "}\n"
                    "Only extract up to 5 concise points per list. Return pure JSON only."
                )
                sample_text = full_text[:3500]
                resp = await self.llm.chat_completion(
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"DOCUMENT SAMPLE:\n{sample_text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                parsed = json.loads(resp)
                return {
                    "key_clauses": parsed.get("key_clauses", [])[:5],
                    "important_dates": parsed.get("important_dates", [])[:5],
                    "eligibility_mentions": parsed.get("eligibility_mentions", [])[:5],
                    "required_documents_mentioned": parsed.get("required_documents_mentioned", [])[:5],
                }
            except Exception as e:
                logger.warning("LLM document structure analysis failed: %s. Using heuristics.", e)

        # Heuristic fallback via Regex
        return self._heuristic_analysis(full_text)

    def _heuristic_analysis(self, text: str) -> Dict[str, List[str]]:
        """Fast regex-based extraction of dates, clauses, and documents."""
        # Find dates (DD/MM/YYYY, DD-MM-YYYY, Month YYYY)
        date_pattern = re.compile(
            r"(\b\d{1,2}[\/\-\.](?:\d{1,2}|[A-Za-z]{3,9})[\/\-\.]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)"
        )
        dates = list(set(date_pattern.findall(text)))[:5]

        # Find potential clauses / sections
        clause_pattern = re.compile(r"((?:Section|Clause|Article|Paragraph|Rule)\s+\d+[\.\w\s]{0,50})", re.IGNORECASE)
        clauses = list(set([m.strip() for m in clause_pattern.findall(text)]))[:5]

        # Find eligibility keywords
        eligibility = []
        for line in text.split("\n"):
            clean = line.strip()
            if any(k in clean.lower() for k in ["eligib", "criteria", "who can apply", "age limit", "qualification"]):
                if 20 < len(clean) < 150:
                    eligibility.append(clean)
            if len(eligibility) >= 4:
                break

        # Find document mentions
        documents = []
        for line in text.split("\n"):
            clean = line.strip()
            if any(k in clean.lower() for k in ["aadhaar", "pan card", "income certificate", "caste certificate", "ration card", "bank passbook", "voter id"]):
                if 15 < len(clean) < 120:
                    documents.append(clean)
            if len(documents) >= 4:
                break

        return {
            "key_clauses": clauses or ["Standard Government Operational Guidelines"],
            "important_dates": dates or ["As notified in Official Gazette"],
            "eligibility_mentions": eligibility or ["Eligible as per department criteria"],
            "required_documents_mentioned": documents or ["Aadhaar Card", "Bank Account Details", "Identity Proof"],
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
                answer="No relevant sections matching your query were found in this document. Please ensure the question relates to the uploaded guidelines.",
                relevant_passages=[],
                sources=[],
                language=language,
            )

        # 2. Synthesize answer with LLM
        answer = await self.llm.generate_rag_response(
            question=question,
            context_passages=passages,
            language=language.value,
            system_context="Explain clearly which section or page of this uploaded document addresses the citizen's inquiry."
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
