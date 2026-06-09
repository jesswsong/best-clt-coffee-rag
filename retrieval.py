"""
retrieval.py — Embedding, vector store ingestion, and retrieval
Charlotte Coffee Shop RAG Pipeline — Milestone 3

Embedding model : sentence-transformers/all-MiniLM-L6-v2 (local, no API key)
Vector store    : ChromaDB (persistent, on-disk)
"""

import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Config — tweak these without touching any other code
# ---------------------------------------------------------------------------

CHUNKS_FILE   = Path("chunks.json")
CHROMA_DIR    = Path("chroma_db")       # where ChromaDB persists its data
COLLECTION    = "charlotte_coffee"      # ChromaDB collection name
EMBED_MODEL   = "all-MiniLM-L6-v2"
TOP_K         = 5                       # default number of results to return

# ---------------------------------------------------------------------------
# Load embedding model (once at import time so callers don't re-pay the cost)
# ---------------------------------------------------------------------------

print(f"Loading embedding model ({EMBED_MODEL})...")
_embed_model = SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    """Return L2-normalised embeddings for a list of strings."""
    return _embed_model.encode(texts, normalize_embeddings=True).tolist()


# ---------------------------------------------------------------------------
# Build / refresh the ChromaDB collection from chunks.json
# ---------------------------------------------------------------------------

def build_index(force_rebuild: bool = False) -> chromadb.Collection:
    """
    Load chunks.json, embed every chunk, and upsert into ChromaDB.

    Args:
        force_rebuild: if True, drop and recreate the collection even if it
                       already exists and has the same number of documents.

    Returns:
        The populated ChromaDB collection.
    """
    # --- Load chunks ---
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} not found — run ingest.py first."
        )
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")

    # --- Connect to ChromaDB ---
    CHROMA_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if force_rebuild:
        try:
            client.delete_collection(COLLECTION)
            print(f"Dropped existing collection '{COLLECTION}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )

    # --- Skip if already populated and not forcing rebuild ---
    existing = collection.count()
    if existing == len(chunks) and not force_rebuild:
        print(f"Collection '{COLLECTION}' already has {existing} docs — skipping re-embed.")
        return collection

    # --- Embed and upsert in batches (ChromaDB handles large batches fine,
    #     but batching keeps peak memory predictable) ---
    BATCH = 128
    total = len(chunks)
    for start in range(0, total, BATCH):
        batch = chunks[start : start + BATCH]

        ids        = [c["chunk_id"]          for c in batch]
        texts      = [c["text"]              for c in batch]
        metadatas  = [
            {
                "source_id":          c["source_id"],
                "source_type":        c["source_type"],
                "source_description": c["source_description"],
                "token_count":        c["token_count"],
                # position of chunk within its source document
                "chunk_index":        int(c["chunk_id"].rsplit("__", 1)[-1]),
            }
            for c in batch
        ]
        embeddings = embed(texts)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"  Upserted {min(start + BATCH, total)}/{total} chunks...")

    print(f"Index ready — {collection.count()} documents in '{COLLECTION}'.")
    return collection


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def get_collection() -> chromadb.Collection:
    """Return the existing ChromaDB collection (does NOT rebuild)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION)


def retrieve(
    query: str,
    k: int = TOP_K,
    collection: chromadb.Collection | None = None,
) -> list[dict]:
    """
    Embed `query` and return the top-k most relevant chunks.

    Args:
        query      : plain-text question or search phrase
        k          : number of results to return (default TOP_K = 5)
        collection : pass an already-open collection to avoid re-connecting;
                     if None, opens the persisted collection from disk.

    Returns:
        List of dicts, each containing:
            rank              — 1-indexed position (1 = most relevant)
            score             — cosine similarity (higher = more relevant)
            text              — the chunk text
            source_id         — stem of the source file
            source_type       — article / reddit / instagram / pdf
            source_description— human-readable label
            chunk_index       — position of this chunk in its source doc
    """
    if collection is None:
        collection = get_collection()

    query_embedding = embed([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]   # cosine distance (lower = closer)

    hits = []
    for rank, (text, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        hits.append(
            {
                "rank":               rank,
                "score":              dist,   # convert distance → similarity
                "text":               text,
                "source_id":          meta["source_id"],
                "source_type":        meta["source_type"],
                "source_description": meta["source_description"],
                "chunk_index":        meta["chunk_index"],
            }
        )
    return hits


# ---------------------------------------------------------------------------
# CLI — python retrieval.py "your query here"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Build (or verify) the index on every direct run
    col = build_index()

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "best coffee shop in Charlotte"
    print(f'\nQuery: "{query}"\n{"─" * 50}')

    hits = retrieve(query, k=TOP_K, collection=col)
    for hit in hits:
        print(
            f"[{hit['rank']}] score={hit['score']}  "
            f"{hit['source_id']} (chunk {hit['chunk_index']})\n"
            f"    {hit['text'][:200].replace(chr(10), ' ')}...\n"
        )
