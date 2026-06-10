"""
Stage 3 & 4: Embedding + Vector Store + Retrieval

Pipeline:
    chunk_all_documents()          (chunk.py)
          ↓
    SentenceTransformer             all-MiniLM-L6-v2  (local, no API key)
          ↓
    ChromaDB collection             persisted to  ./chroma_db/
          ↓
    query(question, k=4)  →  top-4 chunks + source metadata

Usage
-----
Build / rebuild the vector store:
    python embed.py --build

Query interactively:
    python embed.py --query "Which dorm has the best community?"

Run a quick smoke-test (builds if needed, then queries):
    python embed.py
"""

import argparse
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from chunk import chunk_all_documents

# ---------------------------------------------------------------------------
# Config — matches planning.md Retrieval Approach section
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # local, no API key, no cost
COLLECTION_NAME = "grinnell_dorms"
CHROMA_PATH     = "./chroma_db"
TOP_K           = 4                     # chunks returned per query


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def _get_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client stored at CHROMA_PATH."""
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _get_model() -> SentenceTransformer:
    """Load (and cache) the embedding model."""
    print(f"  Loading embedding model: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)


# ---------------------------------------------------------------------------
# Stage 3 — Build
# ---------------------------------------------------------------------------

def build_vector_store(force: bool = False) -> None:
    """
    Embed all chunks and upsert them into ChromaDB.

    Steps
    -----
    1. Load all 195 chunks via chunk_all_documents().
    2. Embed each chunk's text using all-MiniLM-L6-v2.
    3. Upsert into a ChromaDB collection with source + chunk_index metadata.

    Set force=True to wipe and rebuild; otherwise existing entries are
    overwritten by id (upsert is idempotent).
    """
    client = _get_client()

    if force:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # ChromaDB will store raw embeddings; we supply them ourselves
        # so we can control the model exactly.
        metadata={"hnsw:space": "cosine"},
    )

    print("\n=== Stage 3: Building vector store ===\n")

    # 1. Load chunks
    chunks = chunk_all_documents()
    print(f"  Chunks loaded: {len(chunks)}")

    # 2. Embed
    model = _get_model()
    texts = [c["text"] for c in chunks]
    print(f"  Embedding {len(texts)} chunks with {EMBEDDING_MODEL} …")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    print(f"  Embedding shape: {embeddings.shape}")

    # 3. Upsert into ChromaDB
    # IDs must be strings and unique per document.
    ids        = [f"{c['source']}__chunk{c['chunk_index']}" for c in chunks]
    metadatas  = [{"source": c["source"], "chunk_index": c["chunk_index"]}
                  for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    count = collection.count()
    print(f"\n  ✅ Vector store ready — {count} vectors in '{COLLECTION_NAME}'")
    print(f"     Persisted to: {Path(CHROMA_PATH).resolve()}\n")


# ---------------------------------------------------------------------------
# Stage 4 — Retrieval
# ---------------------------------------------------------------------------

def query(question: str, k: int = TOP_K) -> list[dict]:
    """
    Embed `question` and return the top-k most similar chunks.

    Parameters
    ----------
    question : natural-language question from the user
    k        : number of chunks to retrieve (default 4, per planning.md)

    Returns
    -------
    List of dicts, each with:
        text          – chunk content
        source        – source document name (e.g. "sandb_dorm_defense")
        chunk_index   – position within that document
        distance      – cosine distance (lower = more similar)
    """
    client     = _get_client()
    model      = _get_model()
    collection = client.get_collection(COLLECTION_NAME)

    # Embed the question using the same model as the chunks
    q_embedding = model.encode([question])[0].tolist()

    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Unpack ChromaDB's nested-list response format
    retrieved = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "text":        text,
            "source":      meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance":    round(dist, 4),
        })

    return retrieved


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_results(question: str, results: list[dict]) -> None:
    print(f"\nQuery: \"{question}\"\n")
    for i, r in enumerate(results, 1):
        print(f"  {'─'*56}")
        print(f"  Result {i}  |  source: {r['source']}  "
              f"|  chunk #{r['chunk_index']}  |  distance: {r['distance']}")
        print(f"  {'─'*56}")
        print(f"  {r['text'][:400]}")
        if len(r['text']) > 400:
            print("  […]")
        print()


def _smoke_test() -> None:
    """Build (if needed) then run the 5 evaluation questions from planning.md."""
    # Build only if the DB doesn't exist yet
    db_path = Path(CHROMA_PATH)
    if not db_path.exists() or not any(db_path.iterdir()):
        build_vector_store()

    test_questions = [
        "Which dorm is the newest and cleanest?",
        "Are there any dorms that only accept first-years?",
        "What are the three campus clusters and what is each known for?",
        "What do students say about Younker Hall?",
        "What are the downsides of living on South Campus?",
    ]

    print("\n=== Stage 4: Retrieval smoke-test (k=4) ===")
    for q in test_questions:
        results = query(q)
        _print_results(q, results)
        input("  Press Enter for next query…\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed chunks and query ChromaDB.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--build",  action="store_true",
                       help="(Re)build the vector store from all clean documents.")
    group.add_argument("--rebuild", action="store_true",
                       help="Wipe and fully rebuild the vector store.")
    group.add_argument("--query",  type=str, metavar="QUESTION",
                       help="Query the vector store and print top-4 results.")
    args = parser.parse_args()

    if args.build:
        build_vector_store(force=False)
    elif args.rebuild:
        build_vector_store(force=True)
    elif args.query:
        results = query(args.query)
        _print_results(args.query, results)
    else:
        # Default: smoke-test
        _smoke_test()
