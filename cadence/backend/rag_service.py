"""
RAG service — semantic search over the knowledge base.
Activates automatically when knowledge_chunks are present in the database.
Uses pgvector for similarity search when embeddings exist,
falls back to PostgreSQL full-text search otherwise.
"""
import os
from database import query

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBEDDING_MODEL)
        except Exception:
            _embedder = None
    return _embedder


def embed_text(text):
    embedder = _get_embedder()
    if embedder is None:
        return None
    return embedder.encode(text).tolist()


def has_knowledge_base():
    row = query("SELECT COUNT(*) as cnt FROM knowledge_chunks", one=True)
    return row and row["cnt"] > 0


def retrieve_relevant_chunks(query_text, top_k=5):
    if not has_knowledge_base():
        return []

    # Try vector search first
    embedding = embed_text(query_text)
    if embedding:
        try:
            rows = query(
                "SELECT book_title, chunk_text, "
                "1 - (embedding <=> %s::vector) AS similarity "
                "FROM knowledge_chunks "
                "ORDER BY embedding <=> %s::vector LIMIT %s",
                (embedding, embedding, top_k)
            )
            if rows:
                return [{"book": r["book_title"], "text": r["chunk_text"],
                         "similarity": r["similarity"]} for r in rows]
        except Exception:
            pass

    # Fallback: PostgreSQL full-text search
    rows = query(
        "SELECT book_title, chunk_text, "
        "ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) AS rank "
        "FROM knowledge_chunks "
        "WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', %s) "
        "ORDER BY rank DESC LIMIT %s",
        (query_text, query_text, top_k)
    )
    return [{"book": r["book_title"], "text": r["chunk_text"], "similarity": r["rank"]}
            for r in rows] if rows else []


def format_rag_context(chunks):
    if not chunks:
        return ""
    lines = ["\n## KNOWLEDGE BASE — RELEVANT FRAMEWORKS"]
    for c in chunks:
        lines.append(f"\n### {c['book']}\n{c['text']}")
    return "\n".join(lines)


def ingest_knowledge_base(content_md):
    """
    Ingest a markdown knowledge base document.
    Expected format:
      # Book Title
      - principle or insight
      - another principle
    """
    import re
    embedder = _get_embedder()
    chunks = []

    current_book = "General"
    for line in content_md.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            current_book = line[2:].strip()
        elif line.startswith("## "):
            current_book = line[3:].strip()
        elif line and len(line) > 30:
            embedding = embed_text(line) if embedder else None
            chunks.append((current_book, line, embedding))

    from database import execute
    import json
    for book, text, emb in chunks:
        if emb:
            execute(
                "INSERT INTO knowledge_chunks (book_title, chunk_text, embedding) "
                "VALUES (%s, %s, %s::vector)",
                (book, text, json.dumps(emb))
            )
        else:
            execute(
                "INSERT INTO knowledge_chunks (book_title, chunk_text) VALUES (%s, %s)",
                (book, text)
            )

    return len(chunks)
