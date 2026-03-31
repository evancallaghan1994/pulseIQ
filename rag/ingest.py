"""
Ingest knowledge base documents into ChromaDB.
Reads all .md files from data/knowledge_base/, chunks them, embeds with
sentence-transformers/all-MiniLM-L6-v2, and stores in ChromaDB.

Idempotent: re-running clears and rebuilds the collection.

Usage (from project root):
    python rag/ingest.py
"""

import os
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "rag/chroma_store")
COLLECTION_NAME    = "knowledge_base"
CHUNK_SIZE         = 500   # approximate tokens (words used as proxy)
CHUNK_OVERLAP      = 50
EMBED_MODEL        = "sentence-transformers/all-MiniLM-L6-v2"


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by word count (words ≈ tokens for English)."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def ingest() -> int:
    """
    Ingest all knowledge base documents into ChromaDB.
    Returns total number of chunks stored.
    """
    model = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )

    # Clear existing collection for idempotency
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    md_files = sorted(KNOWLEDGE_BASE_DIR.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md files found in {KNOWLEDGE_BASE_DIR}")

    all_ids        = []
    all_embeddings = []
    all_documents  = []
    all_metadatas  = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8").strip()
        chunks = _chunk_text(text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{md_file.stem}__{i}"
            embedding = model.encode(chunk).tolist()

            all_ids.append(chunk_id)
            all_embeddings.append(embedding)
            all_documents.append(chunk)
            all_metadatas.append({
                "source_file":  md_file.name,
                "chunk_index":  i,
            })

        print(f"  {md_file.name} — {len(chunks)} chunks")

    collection.add(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_documents,
        metadatas=all_metadatas,
    )

    total = len(all_ids)
    print(f"\nIngested {total} chunks from {len(md_files)} documents into ChromaDB.")
    return total


if __name__ == "__main__":
    ingest()
