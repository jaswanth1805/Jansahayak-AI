"""RAG package initialization."""

from app.rag.embeddings import (
    get_embedding_function,
    chunk_text,
    get_or_create_collection,
    add_documents_to_collection,
    search_collection,
    delete_collection,
    get_chroma_client,
)

__all__ = [
    "get_embedding_function",
    "chunk_text",
    "get_or_create_collection",
    "add_documents_to_collection",
    "search_collection",
    "delete_collection",
    "get_chroma_client",
]
