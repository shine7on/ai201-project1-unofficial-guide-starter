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

# Every hall that has a grinnell_official_<name> source file.
# Maps every name a user might type → the source id stem.
_HALL_ALIASES: dict[str, str] = {
    # straightforward matches
    "clark":           "clark",
    "cleveland":       "cleveland",
    "cowles":          "cowles",
    "dibble":          "dibble",
    "gates":           "gates",
    "haines":          "haines",
    "james":           "james",
    "kershaw":         "kershaw",
    "langan":          "langan",
    "lazier":          "lazier",
    "loose":           "loose",
    "main":            "main",
    "norris":          "norris",
    "rathje":          "rathje",
    "rawson":          "rawson",
    "read":            "read",
    "renfrow":         "renfrow",
    "rose":            "rose",
    "smith":           "smith",
    "younker":         "younker",
    # common alternate spellings / nicknames
    "kersh":           "kershaw",
    "kershoff":        "kershaw",
    "gardner":         "main",      # Gardner Lounge is in Main Hall
    "bob's":           "main",      # Bob's Underground is on South / Main area
}

import re as _re

def _detect_hall(question: str) -> str | None:
    """
    Return the grinnell_official_<hall> source name if any hall name is
    mentioned in the question, else None.
    Matches whole words only (so 'james' doesn't fire on 'james bond').
    """
    q_lower = question.lower()
    for alias, hall_stem in _HALL_ALIASES.items():
        if _re.search(rf"\b{_re.escape(alias)}\b", q_lower):
            return f"grinnell_official_{hall_stem}"
    return None


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

    # If the question names a specific hall, pin that official source first,
    # then fill remaining slots from the global search.
    hall_source = _detect_hall(question)

    def _run_query(where_filter=None, n=k) -> list[dict]:
        kwargs = dict(
            query_embeddings=[q_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        if where_filter:
            kwargs["where"] = where_filter
        results = collection.query(**kwargs)
        out = []
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            out.append({
                "text":        text,
                "source":      meta["source"],
                "chunk_index": meta["chunk_index"],
                "distance":    round(dist, 4),
            })
        return out

    if hall_source:
        # Split k into: up to 2 slots from the official page + rest from global.
        # This guarantees factual official info AND student opinions both appear.
        OFFICIAL_SLOTS = min(2, k)

        # Step 1: top-2 most relevant chunks from the official hall page
        hall_chunks = _run_query(
            where_filter={"source": {"$eq": hall_source}},
            n=OFFICIAL_SLOTS,
        )

        # Step 2: fill remaining slots with global semantic search
        # (excludes the official page so we get reviews/articles, not more official text)
        remaining = k - len(hall_chunks)
        global_chunks = _run_query(
            where_filter={"source": {"$ne": hall_source}},
            n=remaining + 2,  # fetch a few extra in case of duplicates
        )

        # Merge: official first, then global fill-ins
        seen_ids = {(c["source"], c["chunk_index"]) for c in hall_chunks}
        for c in global_chunks:
            if (c["source"], c["chunk_index"]) not in seen_ids:
                hall_chunks.append(c)
                seen_ids.add((c["source"], c["chunk_index"]))
            if len(hall_chunks) >= k:
                break
        return hall_chunks[:k]

    return _run_query()


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
