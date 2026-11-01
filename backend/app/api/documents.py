"""Document Management and RAG Query API Endpoints.

Handles uploading, OCR/text extraction, indexing, and grounded querying
of government guidelines, gazettes, and policy PDFs.
"""

import logging
import secrets
import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, status, Depends
from starlette.concurrency import run_in_threadpool

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
)
from app.services.llm_service import LLMService
from app.services.document_service import DocumentService
from app.utils.rate_limit import document_query_limit, document_query_capacity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])
_llm_service = LLMService()
_doc_service = DocumentService(_llm_service)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """Upload and process a government PDF document.
    
    Extracts text, identifies key clauses and eligibility criteria,
    and indexes content in ChromaDB for semantic question answering.
    """
    document_id = f"doc_{uuid.uuid4().hex}"
    access_token = secrets.token_urlsafe(32)
    try:
        response = await _doc_service.process_upload(
            file=file, document_id=document_id, access_token=access_token
        )
        response.access_token = access_token
        return response
    except HTTPException:
        try:
            _doc_service.discard_upload(document_id)
        except Exception:
            logger.exception("Could not roll back rejected document upload")
        raise
    except Exception as e:
        try:
            _doc_service.discard_upload(document_id)
        except Exception:
            logger.exception("Could not roll back failed document upload")
        logger.exception("Document processing failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded document. Check the file and try again."
        )


@router.post("/query", response_model=DocumentQueryResponse)
async def query_document(
    request: DocumentQueryRequest,
    _: None = Depends(document_query_limit),
    __: None = Depends(document_query_capacity),
) -> DocumentQueryResponse:
    """Ask a question about an uploaded government document.
    
    Returns an answer grounded in retrieved passages with page references.
    """
    try:
        response = await _doc_service.query_document(
            document_id=request.document_id,
            question=request.question,
            access_token=request.access_token,
            language=request.language,
        )
        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.exception("Document query failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document query failed. Please try again."
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    x_document_token: str = Header(default="", alias="X-Document-Token"),
) -> Dict[str, Any]:
    """Delete an uploaded document, removing its vector index and temporary files."""
    _doc_service.require_access(document_id, x_document_token)
    success = await run_in_threadpool(_doc_service.delete_document, document_id)
    return {
        "document_id": document_id,
        "deleted": True,
        "cleanup_complete": success,
        "message": (
            "Document access was revoked and stored data was removed."
            if success else
            "Document access was revoked; storage cleanup is pending and will be retried."
        ),
    }
