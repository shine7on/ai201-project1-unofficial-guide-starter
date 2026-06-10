"""
Stage 2: Chunking

Implements the strategy from planning.md:

  - S&B articles  → paragraph-first split, then cap each paragraph at
                     ARTICLE_CHUNK_SIZE chars with OVERLAP carry-over.
  - Review / official pages → fixed-size character chunking at
                     REVIEW_CHUNK_SIZE chars with OVERLAP carry-over.

Each chunk is a dict:
    {
        "text":   str,          # the chunk content
        "source": str,          # filename without extension, e.g. "sandb_dorm_defense"
        "chunk_index": int,     # position within the document (0-based)
    }

Run:
    python chunk.py             # prints 5 sample chunks and a summary
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Config — matches planning.md
# ---------------------------------------------------------------------------

REVIEW_CHUNK_SIZE   = 400   # characters, for review/official sources
ARTICLE_CHUNK_SIZE  = 500   # characters, for multi-paragraph S&B articles
OVERLAP             = 50    # characters carried over between consecutive chunks
MIN_CHUNK_LENGTH    = 60    # drop tail fragments shorter than this

CLEAN_DIR = Path("documents/clean")

# Sources that are multi-paragraph articles → paragraph-first strategy
ARTICLE_SOURCES = {
    "sandb_dorm_defense",
    "sandb_housing_changes_2024",
    "sandb_renfrow_suite",
    "sandb_firstyear_cluster",
}

# Sources where each line is one review entry — split by line first,
# then fall back to fixed-size if a single review is unusually long.
LINE_REVIEW_SOURCES = {
    "roomsurf_grinnell",
    "ratemydorm_norris",
    "ratemydorm_rose",
    "appily_grinnell",
}


# ---------------------------------------------------------------------------
# Core chunking helpers
# ---------------------------------------------------------------------------

def _fixed_size_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split `text` into chunks of at most `chunk_size` chars.
    Each chunk after the first starts `overlap` chars before the end
    of the previous chunk, so context is shared across boundaries.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Next chunk starts `overlap` chars before where this one ended
        start = end - overlap
    return chunks


def _paragraph_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split `text` by blank lines (paragraphs) first.
    If a paragraph fits within chunk_size, keep it whole.
    If it exceeds chunk_size, fall back to fixed-size splitting within it.
    Overlap is applied only when a paragraph is split; whole paragraphs
    are emitted as-is (they already have natural boundaries).
    """
    paragraphs = re.split(r"\n{2,}", text)
    chunks = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            # Long paragraph: split it with overlap
            chunks.extend(_fixed_size_chunks(para, chunk_size, overlap))
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _line_review_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    For review list sources where each line is one review (e.g. RoomSurf):
    treat each non-empty line as its own chunk.
    If a single line exceeds chunk_size, split it with overlap.
    This prevents a single 400-char window from spanning two different dorm reviews.
    """
    chunks = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) <= chunk_size:
            chunks.append(line)
        else:
            chunks.extend(_fixed_size_chunks(line, chunk_size, overlap))
    return chunks


def chunk_document(text: str, source_name: str) -> list[dict]:
    """
    Chunk one document.

    Parameters
    ----------
    text        : cleaned plain text of the document
    source_name : filename stem, e.g. "sandb_dorm_defense"
                  (used to pick the right chunking strategy and stored
                  as metadata on every chunk)

    Returns
    -------
    List of chunk dicts with keys: text, source, chunk_index
    """
    text = text.strip()
    if not text:
        return []

    if source_name in ARTICLE_SOURCES:
        raw_chunks = _paragraph_chunks(text, ARTICLE_CHUNK_SIZE, OVERLAP)
    elif source_name in LINE_REVIEW_SOURCES:
        raw_chunks = _line_review_chunks(text, REVIEW_CHUNK_SIZE, OVERLAP)
    else:
        raw_chunks = _fixed_size_chunks(text, REVIEW_CHUNK_SIZE, OVERLAP)

    return [
        {"text": chunk, "source": source_name, "chunk_index": i}
        for i, chunk in enumerate(raw_chunks)
        if len(chunk.strip()) >= MIN_CHUNK_LENGTH  # drop useless tail fragments
    ]


def chunk_all_documents() -> list[dict]:
    """Load every .txt file in CLEAN_DIR and chunk it."""
    all_chunks = []
    for path in sorted(CLEAN_DIR.glob("*.txt")):
        source_name = path.stem
        text = path.read_text(encoding="utf-8")
        chunks = chunk_document(text, source_name)
        all_chunks.extend(chunks)
    return all_chunks


# ---------------------------------------------------------------------------
# Inspection / __main__
# ---------------------------------------------------------------------------

def _print_chunk(chunk: dict, label: str) -> None:
    border = "─" * 60
    print(f"\n{border}")
    print(f"  {label}")
    print(f"  source : {chunk['source']}  |  chunk #{chunk['chunk_index']}"
          f"  |  {len(chunk['text'])} chars")
    print(border)
    print(chunk["text"])


if __name__ == "__main__":
    all_chunks = chunk_all_documents()

    print(f"\n{'='*60}")
    print(f"  Total chunks produced: {len(all_chunks)}")
    print(f"{'='*60}")

    # Per-source breakdown
    from collections import Counter
    counts = Counter(c["source"] for c in all_chunks)
    for src, n in sorted(counts.items()):
        print(f"  {src:<45} {n:>3} chunks")

    # -----------------------------------------------------------------------
    # Print 5 representative chunks — chosen to cover different source types
    # -----------------------------------------------------------------------
    print("\n\n" + "=" * 60)
    print("  5 REPRESENTATIVE CHUNKS FOR INSPECTION")
    print("=" * 60)

    # 1. A mid-article S&B chunk (paragraph boundary, article source)
    sandb = [c for c in all_chunks if c["source"] == "sandb_dorm_defense"]
    if len(sandb) >= 3:
        _print_chunk(sandb[2], "① S&B article — mid-article paragraph")

    # 2. A review-style chunk from RateMyDorm Norris
    norris_reviews = [c for c in all_chunks if c["source"] == "ratemydorm_norris"]
    if norris_reviews:
        _print_chunk(norris_reviews[0], "② RateMyDorm — Norris Hall review")

    # 3. A RoomSurf review chunk
    roomsurf = [c for c in all_chunks if c["source"] == "roomsurf_grinnell"]
    if len(roomsurf) >= 2:
        _print_chunk(roomsurf[1], "③ RoomSurf — mid-document review")

    # 4. An official hall description chunk (fixed-size on structured content)
    renfrow = [c for c in all_chunks if c["source"] == "grinnell_official_renfrow"]
    if len(renfrow) >= 2:
        _print_chunk(renfrow[1], "④ Official description — Renfrow Hall")

    # 5. A chunk near a boundary (tests overlap: should start mid-sentence from prev)
    housing = [c for c in all_chunks if c["source"] == "sandb_housing_changes_2024"]
    if len(housing) >= 4:
        _print_chunk(housing[3], "⑤ S&B article — boundary / overlap chunk")

    # -----------------------------------------------------------------------
    # Sanity checks
    # -----------------------------------------------------------------------
    print("\n\n" + "=" * 60)
    print("  SANITY CHECKS")
    print("=" * 60)

    lengths = [len(c["text"]) for c in all_chunks]
    over_limit = [c for c in all_chunks if len(c["text"]) > max(REVIEW_CHUNK_SIZE, ARTICLE_CHUNK_SIZE) + 5]
    empty = [c for c in all_chunks if len(c["text"].strip()) == 0]

    print(f"  Min chunk length : {min(lengths)} chars")
    print(f"  Max chunk length : {max(lengths)} chars")
    print(f"  Avg chunk length : {sum(lengths)//len(lengths)} chars")
    print(f"  Chunks over size limit : {len(over_limit)}")
    print(f"  Empty chunks           : {len(empty)}")
    if over_limit:
        print("  ⚠️  Over-size chunks (source, index, length):")
        for c in over_limit[:5]:
            print(f"     {c['source']}  #{c['chunk_index']}  {len(c['text'])} chars")
