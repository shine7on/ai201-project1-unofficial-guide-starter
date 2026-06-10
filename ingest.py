"""
Stage 1: Document ingestion and cleaning.

Fetches each source URL, saves raw HTML to documents/raw/,
then cleans and saves plain text to documents/clean/.

Run:  python ingest.py
"""

import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "id": "roomsurf_grinnell",
        "url": "https://roomsurf.com/dorm-reviews/grinnell",
        "description": "RoomSurf Grinnell dorm reviews",
    },
    {
        "id": "sandb_dorm_defense",
        "url": "https://thesandb.com/46692/article/student-speaks-dorm-hall-defense/",
        "description": "S&B: Dorm Hall Defense",
    },
    {
        "id": "sandb_housing_changes_2024",
        "url": "https://thesandb.com/45774/article/loose-hall-closes-renfrow-hall-opens-and-younker-hall-transitions-in-2024-grinnell-college/",
        "description": "S&B: Loose closes, Renfrow opens 2024",
    },
    {
        "id": "sandb_renfrow_suite",
        "url": "https://thesandb.com/50642/features/cribz-renfrow-halls-sweet-suite/",
        "description": "S&B: CRIBZ Renfrow sweet suite",
    },
    {
        "id": "sandb_firstyear_cluster",
        "url": "https://thesandb.com/54752/news/reslife-first-year-housing-cluster-model-met-with-student-disapproval/",
        "description": "S&B: First-year cluster model",
    },
    {
        "id": "ratemydorm_norris",
        "url": "https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-norris-hall",
        "description": "RateMyDorm: Norris Hall",
    },
    {
        "id": "ratemydorm_rose",
        "url": "https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-rose-hall",
        "description": "RateMyDorm: Rose Hall",
    },
    {
        "id": "grinnell_official_halls",
        "url": "https://www.grinnell.edu/campus-life/student-life/living-spaces/residence-halls",
        "description": "Grinnell official hall descriptions",
    },
    {
        "id": "grinnell_official_language_houses",
        "url": "https://www.grinnell.edu/campus-life/student-life/living-spaces/language-project-houses",
        "description": "Grinnell official language/project house descriptions",
    },
    {
        "id": "appily_grinnell",
        "url": "https://www.appily.com/colleges/grinnell-college/reviews",
        "description": "Appily: Grinnell College reviews",
    },
    {
        "id": "niche_grinnell",
        "url": "https://www.niche.com/colleges/grinnell-college/campus-life/",
        "description": "Niche: Grinnell College campus life",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

RAW_DIR = Path("documents/raw")
CLEAN_DIR = Path("documents/clean")
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_raw(source: dict) -> str | None:
    raw_path = RAW_DIR / f"{source['id']}.html"
    if raw_path.exists():
        print(f"  [cache] {source['id']}")
        return raw_path.read_text(encoding="utf-8")
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        raw_path.write_text(resp.text, encoding="utf-8")
        print(f"  [fetched] {source['id']}  ({len(resp.text):,} chars)")
        time.sleep(1.5)
        return resp.text
    except Exception as e:
        print(f"  [ERROR] {source['id']}: {e}")
        return None


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

# Tags whose entire subtree should be dropped
_JUNK_TAGS = {
    "script", "style", "noscript", "iframe", "nav", "header", "footer",
    "aside", "form", "button", "svg", "figure", "figcaption",
    "advertisement", "ads",
}

# CSS class / id fragments that signal boilerplate
_JUNK_PATTERNS = re.compile(
    r"(nav|navbar|menu|header|footer|sidebar|cookie|banner|promo|ad[-_]|"
    r"share|social|comment-count|read-more|related|subscription|widget|"
    r"breadcrumb|pagination|search|modal|overlay|popup|newsletter)",
    re.IGNORECASE,
)

# HTML entities and leftover noise
_ENTITY_RE = re.compile(r"&[a-z]{2,6};|&#\d+;", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\n{3,}")

# Line-level patterns to drop after text extraction
_DROP_LINE_PATTERNS = re.compile(
    r"(need a roommate|get started here|has no reviews yet|"
    r"see all reviews|see grinnell dorms ranked|read full review|"
    r"^see all$|^get started$|^more$|^submit a review$|"
    r"^✌️$|^🧐|"
    # Appily college comparison table rows (city, state pairs)
    r"^(Providence|Stanford|New Haven|Chicago|Evanston|Amherst|Cambridge|"
    r"Northfield|Saint Paul|Saint Louis|Poughkeepsie|Oberlin),\s+(RI|CA|CT|IL|MA|MN|MO|NY|OH)$|"
    r"^(Brown|Stanford|Yale|Northwestern|Amherst College|Harvard|Carleton|"
    r"Macalester|Washington University|Vassar|Oberlin) (University|College)$|"
    r"^University of Chicago$|^See All$|"
    r"^Colleges (in|for|accepting)|"
    r"^(Amherst College|Washington University|Vassar College|Oberlin College|"
    r"Carleton College|Macalester College)$"
    r")",
    re.IGNORECASE,
)


def _is_junk_element(tag) -> bool:
    if not hasattr(tag, "attrs") or tag.attrs is None:
        return False
    for attr in ("class", "id"):
        raw = tag.attrs.get(attr, "")
        val = " ".join(raw) if isinstance(raw, list) else (raw or "")
        if val and _JUNK_PATTERNS.search(val):
            return True
    return False


# CSS selectors that target the real content on specific sites
_CONTENT_SELECTORS = [
    # S&B (Scarlet & Black student newspaper)
    "div.sno-story-body",
    "div.sno-story-wrap",
    # Generic article / main content
    "article",
    "div.entry-content",
    "div.post-content",
    "div.article-content",
    "div.article-body",
    "div[itemprop='articleBody']",
    # RateMyDorm / RoomSurf review lists
    "div.reviews",
    "div.review-list",
    "div#reviews",
    # Grinnell official
    "main",
]


def _extract_content(soup: BeautifulSoup) -> BeautifulSoup | None:
    """Return the first matching content container, or None."""
    for selector in _CONTENT_SELECTORS:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 200:
            return el
    return None


def clean_html(html: str, keep_short_lines: bool = False) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Try to isolate the real content section first
    content = _extract_content(soup)
    working = content if content is not None else soup

    # Remove junk tags by name within the working section
    for tag_name in _JUNK_TAGS:
        for tag in working.find_all(tag_name):
            tag.decompose()

    # Remove elements whose class/id signals boilerplate
    for tag in working.find_all(True):
        if _is_junk_element(tag):
            tag.decompose()

    # Extract remaining text
    text = working.get_text(separator="\n")

    # Decode leftover HTML entities
    text = _ENTITY_RE.sub(" ", text)

    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if len(l) > 1 and not _DROP_LINE_PATTERNS.search(l)]

    # Drop "N Review(s)" count lines — they're noise from RoomSurf
    lines = [l for l in lines if not re.fullmatch(r"\d+ Reviews?", l)]

    # Drop short isolated lines with no long content nearby.
    # Skip this filter for sources where short lines ARE the content (e.g. address lists).
    if keep_short_lines:
        cleaned_lines = lines
    else:
        cleaned_lines = []
        for i, line in enumerate(lines):
            # A short line is only kept if substantive content follows it.
            # This drops trailing empty headers (dorm names with no review after them).
            if len(line) <= 40:
                next_long = any(len(lines[j]) > 60 for j in range(i+1, min(len(lines), i+3)))
                if not next_long:
                    continue
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = _WHITESPACE_RE.sub("\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Stage 1: Ingestion + Cleaning ===\n")
    for source in SOURCES:
        print(f"[{source['id']}]  {source['description']}")
        html = fetch_raw(source)
        if html is None:
            continue
        keep_short = source["id"] == "grinnell_official_language_houses"
        clean = clean_html(html, keep_short_lines=keep_short)
        out_path = CLEAN_DIR / f"{source['id']}.txt"
        out_path.write_text(clean, encoding="utf-8")
        print(f"  -> cleaned: {len(clean):,} chars  saved to {out_path}\n")

    # Print one document for inspection
    print("\n" + "=" * 60)
    print("SAMPLE — sandb_dorm_defense.txt (first 3000 chars)")
    print("=" * 60)
    sample = (CLEAN_DIR / "sandb_dorm_defense.txt")
    if sample.exists():
        print(sample.read_text(encoding="utf-8")[:3000])


if __name__ == "__main__":
    main()