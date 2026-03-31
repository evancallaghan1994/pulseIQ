"""
RAG query and answer module.
Embeds a question, retrieves top-5 relevant chunks from ChromaDB,
and calls the Claude API to generate a grounded answer.

Usage:
    from rag.query import answer_question
    result = answer_question("How do we handle pricing objections?")
    print(result["answer"])
    print(result["sources"])
"""

import os
from pathlib import Path

import anthropic
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "rag/chroma_store")
COLLECTION_NAME    = "knowledge_base"
EMBED_MODEL        = "sentence-transformers/all-MiniLM-L6-v2"
CLAUDE_MODEL       = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")
TOP_K              = 5

SYSTEM_PROMPT = """You are a sales assistant for PulseIQ, a B2B AI sales intelligence platform.
Answer the user's question using ONLY the context provided below.
If the answer is not present in the context, respond with: "I don't have information on that in my knowledge base."
Be concise and specific. Do not invent details not present in the context."""


def answer_question(question: str) -> dict:
    """
    Answer a question using RAG over the knowledge base.

    Args:
        question: Natural language question from a sales rep.

    Returns:
        dict with keys:
            "answer"  — Claude's grounded response
            "sources" — list of source filenames used
    """
    # Embed the question
    model = SentenceTransformer(EMBED_MODEL)
    question_embedding = model.encode(question).tolist()

    # Retrieve top-K chunks from ChromaDB
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]
    sources   = sorted(set(m["source_file"] for m in metadatas))

    # Build context block
    context_parts = []
    for chunk, meta in zip(chunks, metadatas):
        context_parts.append(f"[Source: {meta['source_file']}]\n{chunk}")
    context = "\n\n---\n\n".join(context_parts)

    # Call Claude
    claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }
        ],
    )

    answer = message.content[0].text.strip()
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    test_questions = [
        "How do we handle pricing objections?",
        "What makes PulseIQ better than competitors?",
        "What are the available pricing tiers?",
        "What is the weather forecast for tomorrow?",   # out of scope
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        result = answer_question(q)
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print("-" * 60)
