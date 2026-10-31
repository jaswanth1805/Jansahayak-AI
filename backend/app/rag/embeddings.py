"""Vector Embeddings and ChromaDB Management.

Provides text chunking using LangChain recursive text splitters,
OpenAI text-embedding-3-small integration with local fallback,
and ChromaDB persistent vector collection indexing and similarity search.
"""

import logging
import os
import uuid
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

logger = logging.getLogger(__name__)

_CHROMA_CLIENT: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Initialize and return a persistent ChromaDB client instance."""
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        settings = get_settings()
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info("ChromaDB initialized at '%s'", settings.CHROMADB_PATH)
    return _CHROMA_CLIENT


def get_embedding_function():
    """Return an embedding function for ChromaDB.
    
    Prefers OpenAI text-embedding-3-small if OPENAI_API_KEY is configured.
    Falls back to ChromaDB's default embedding function or sentence-transformers.
    """
    settings = get_settings()
    
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() and not settings.OPENAI_API_KEY.startswith("your_"):
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.EMBEDDING_MODEL
            )
        except Exception as err:
            logger.warning("Failed to initialize OpenAI embedding function: %s. Using default.", err)
            
    # Default local embedding function (all-MiniLM-L6-v2)
    from chromadb.utils import embedding_functions
    return embedding_functions.DefaultEmbeddingFunction()


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks using LangChain RecursiveCharacterTextSplitter.
    
    Args:
        text: The source text document or string.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlapping characters between consecutive chunks.
        
    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "।", "॥", ".", " ", ""],
    )
    return splitter.split_text(text)


def sanitize_collection_name(name: str) -> str:
    """Format and sanitize collection name to comply with ChromaDB naming rules:
    3-63 characters, alphanumeric, underscores or hyphens.
    """
    import re
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    if len(clean) < 3:
        clean = f"col_{clean}"
    if len(clean) > 63:
        clean = clean[:63]
    return clean


def get_or_create_collection(collection_name: str) -> chromadb.Collection:
    """Retrieve an existing Chroma collection or create a new one.
    
    Args:
        collection_name: Identifier for the collection.
        
    Returns:
        chromadb.Collection instance.
    """
    client = get_chroma_client()
    safe_name = sanitize_collection_name(collection_name)
    embed_fn = get_embedding_function()
    
    return client.get_or_create_collection(
        name=safe_name,
        embedding_function=embed_fn,
        metadata={"description": "JanSahayak policy and document chunks"}
    )


def add_documents_to_collection(
    collection_name: str,
    texts: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> int:
    """Embed and store a list of text chunks in the specified Chroma collection.
    
    Args:
        collection_name: Target collection name.
        texts: List of chunked texts.
        metadatas: Corresponding metadata dictionaries for each chunk.
        ids: Unique identifiers for each document.
        
    Returns:
        Number of documents added.
    """
    if not texts:
        return 0
        
    collection = get_or_create_collection(collection_name)
    
    if ids is None:
        ids = [f"{sanitize_collection_name(collection_name)}_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(texts))]
        
    if metadatas is None:
        metadatas = [{"index": i} for i in range(len(texts))]
    else:
        # Sanitize metadata values: Chroma only accepts primitive types
        sanitized_metadatas = []
        for m in metadatas:
            safe_meta = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    safe_meta[k] = v
                elif v is None:
                    safe_meta[k] = ""
                else:
                    safe_meta[k] = str(v)
            sanitized_metadatas.append(safe_meta)
        metadatas = sanitized_metadatas
        
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
    )
    logger.info("Added %d chunks to ChromaDB collection '%s'", len(texts), collection_name)
    return len(texts)


def search_collection(
    collection_name: str,
    query: str,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """Perform semantic similarity search on a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to query.
        query: User question or natural language query.
        n_results: Maximum passages to retrieve.
        
    Returns:
        List of dicts: [{"text": str, "metadata": dict, "distance": float, "id": str}]
    """
    if not query or not query.strip():
        return []
        
    client = get_chroma_client()
    safe_name = sanitize_collection_name(collection_name)
    
    try:
        collection = client.get_collection(
            name=safe_name,
            embedding_function=get_embedding_function()
        )
    except Exception as e:
        logger.warning("Collection '%s' not found for search: %s", safe_name, e)
        return []
        
    count = collection.count()
    if count == 0:
        return []
        
    actual_k = min(n_results, count)
    results = collection.query(
        query_texts=[query],
        n_results=actual_k
    )
    
    formatted_results = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else 0.0
            doc_id = ids[i] if i < len(ids) else ""
            
            formatted_results.append({
                "text": doc,
                "metadata": meta,
                "distance": dist,
                "confidence": max(0.0, round(1.0 - (dist if dist <= 1.0 else 0.5), 2)),
                "id": doc_id,
            })
            
    return formatted_results


def delete_collection(collection_name: str) -> bool:
    """Delete a Chroma collection safely.
    
    Returns True if deleted or did not exist, False on failure.
    """
    client = get_chroma_client()
    safe_name = sanitize_collection_name(collection_name)
    try:
        client.delete_collection(name=safe_name)
        logger.info("Deleted ChromaDB collection '%s'", safe_name)
        return True
    except Exception as err:
        logger.debug("Collection '%s' did not exist or could not be deleted: %s", safe_name, err)
        return False
