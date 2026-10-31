"""Document Management and RAG Query API Endpoints.

Handles uploading, OCR/text extraction, indexing, and grounded querying
of government guidelines, gazettes, and policy PDFs.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
)
from app.services.llm_service import LLMService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])
_llm_service = LLMService()
_doc_service = DocumentService(_llm_service)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload and process a government PDF document.
    
    Extracts text, identifies key clauses and eligibility criteria,
    and indexes content in ChromaDB for semantic question answering.
    """
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    try:
        response = await _doc_service.process_upload(file=file, document_id=document_id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document processing failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/query", response_model=DocumentQueryResponse)
async def query_document(request: DocumentQueryRequest) -> DocumentQueryResponse:
    """Ask a question about an uploaded government document.
    
    Returns a grounded answer with page numbers and confidence scores.
    """
    try:
        response = await _doc_service.query_document(
            document_id=request.document_id,
            question=request.question,
            language=request.language,
        )
        return response
    except Exception as e:
        logger.exception("Document query failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document query error: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete an uploaded document, removing its vector index and temporary files."""
    success = _doc_service.delete_document(document_id)
    return {
        "document_id": document_id,
        "deleted": success,
        "message": f"Document '{document_id}' successfully removed from index."
    }
