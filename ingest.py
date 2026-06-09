"""
ingest.py — Document ingestion, cleaning, and semantic chunking
Charlotte Coffee Shop RAG Pipeline — Milestone 3

Sources: articles, Reddit threads, Instagram reel descriptions, local PDFs
Chunking: SemanticChunker (all-MiniLM-L6-v2) with 100–512 token guardrails
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict

import pdfplumber
import requests
from bs4 import BeautifulSoup
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoTokenizer


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "id": "cathzine",
        "type": "article",
        "url": "https://cathzine.substack.com/p/best-laptop-friendly-cafes-in-charlotte",
        "description": "Cathzine — Best laptop-friendly cafes",
    },
    {
        "id": "sprudge",
        "type": "article",
        "url": "https://sprudge.com/the-sprudge-guide-to-coffee-in-charlotte-north-carolina-193932.html",
        "description": "Sprudge Guide to Coffee in Charlotte",
    },
    {
        "id": "hopculture",
        "type": "article",
        "url": "https://www.hopculture.com/best-coffee-charlotte-north-carolina-craft-roasters-shops/",
        "description": "Hop Culture — Best Coffee Roasters and Shops",
    },
    {
        "id": "henhouse",
        "type": "article",
        "url": "https://www.henhousedesign.co/blog/favorite-charlotte-date-spots",
        "description": "Hen House — Favorite Charlotte Date Spots",
    },
    {
        "id": "wayward",
        "type": "article",
        "url": "https://www.waywardblog.com/best-coffee-charlotte-north-carolina/",
        "description": "Start Your Day at These 15 Essential Charlotte Coffee Shops",
    },
    {
        "id": "spoon",
        "type": "article",
        "url": "https://spoonuniversity.com/school/uncc/the-best-coffee-shops-near-unc-charlotte-for-studying/",
        "description": "The Best Coffee Shops Near UNC Charlotte For Studying",
    },
    
    # Instagram reels: descriptions must be saved manually as .txt files
    # since Instagram blocks scraping. Place them in raw_docs/ as:
    #   raw_docs/instagram_reel_1.txt
    #   raw_docs/instagram_reel_2.txt
]

CHUNK_MIN_TOKENS = 50
CHUNK_MAX_TOKENS = 110
CHUNK_OVERLAP_TOKENS = 30   # tokens of previous chunk to prepend as context
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

RAW_DIR = Path("raw_docs")
PDF_DIR = Path("raw_pdfs")
CHUNKS_OUT = Path("chunks.json")

RAW_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Tokenizer (for guardrail enforcement)
# ---------------------------------------------------------------------------

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Hard-truncate a string to max_tokens."""
    ids = tokenizer.encode(text, add_special_tokens=False)
    if len(ids) <= max_tokens:
        return text
    return tokenizer.decode(ids[:max_tokens], skip_special_tokens=True)


# ---------------------------------------------------------------------------
# Fetching — web sources
# ---------------------------------------------------------------------------

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RAG-student-project/1.0)"}


def fetch_article(url: str) -> str:
    """Fetch and extract main body text from a generic article URL."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove nav, footer, sidebar, scripts, styles
    for tag in soup(["nav", "footer", "aside", "script", "style", "header"]):
        tag.decompose()

    # Prefer <article> or <main> if present
    container = soup.find("article") or soup.find("main") or soup.body
    if container is None:
        return ""

    # Extract paragraphs and headings
    blocks = []
    for el in container.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = el.get_text(separator=" ", strip=True)
        if text:
            blocks.append(text)

    return "\n\n".join(blocks)


def fetch_reddit(json_url: str) -> str:
    """Fetch a Reddit thread via its .json endpoint and return flattened text."""
    resp = requests.get(json_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    lines = []

    def walk_comments(node):
        if isinstance(node, dict):
            kind = node.get("kind")
            d = node.get("data", {})
            if kind == "t3":  # post
                title = d.get("title", "")
                selftext = d.get("selftext", "")
                if title:
                    lines.append(f"POST: {title}")
                if selftext:
                    lines.append(selftext)
            elif kind == "t1":  # comment
                body = d.get("body", "")
                if body and body not in ("[deleted]", "[removed]"):
                    lines.append(f"COMMENT: {body}")
                # Recurse into replies
                replies = d.get("replies")
                if isinstance(replies, dict):
                    walk_comments(replies)
            elif kind == "Listing":
                for child in d.get("children", []):
                    walk_comments(child)
        elif isinstance(node, list):
            for item in node:
                walk_comments(item)

    walk_comments(data)
    return "\n\n".join(lines)


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF scraper — local files in raw_pdfs/
# ---------------------------------------------------------------------------

def load_pdf(path: Path) -> str:
    """Extract text from a local PDF using pdfplumber.

    Strategy:
    - Page-by-page extraction preserving paragraph breaks.
    - Tables are converted to pipe-delimited rows so café comparison tables
      survive as readable text rather than being stripped.
    - Pages with no extractable text (scanned images) are skipped with a
      warning — add OCR via pytesseract if you ever need them.
    """
    pages = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            # --- Extract tables and convert to pipe-delimited rows ---
            table_texts = []
            for table in page.extract_tables():
                rows = []
                for row in table:
                    cleaned_row = [cell.strip() if cell else "" for cell in row]
                    rows.append(" | ".join(cleaned_row))
                table_texts.append("\n".join(rows))

            # --- Extract prose text ---
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""

            # --- Combine prose + tables for this page ---
            if table_texts:
                combined = text + "\n\n" + "\n\n".join(table_texts)
            else:
                combined = text

            combined = combined.strip()
            if not combined:
                print(f"  ⚠ Page {page_num} has no extractable text (possibly scanned), skipping")
                continue

            pages.append(combined)

    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalise whitespace, remove boilerplate patterns."""
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown image tags
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Strip common boilerplate phrases
    boilerplate = [
        r"subscribe to our newsletter.*",
        r"sign up for.*newsletter.*",
        r"follow us on.*",
        r"advertisement\b",
        r"skip to (main )?content",
        r"cookie policy.*",
        r"all rights reserved.*",
    ]
    for pat in boilerplate:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    # Final strip
    return text.strip()


# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    source_type: str
    source_description: str
    text: str
    token_count: int


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def enforce_token_guardrails(
    chunks: list[str],
    min_tokens: int = CHUNK_MIN_TOKENS,
    max_tokens: int = CHUNK_MAX_TOKENS,
) -> list[str]:
    """
    Post-processing:
    - Drop chunks below min_tokens (too small to be meaningful)
    - Hard-truncate chunks above max_tokens
    Defaults to the global config values; callers can pass tighter limits
    for short documents.
    """
    result = []
    for chunk in chunks:
        n = count_tokens(chunk)
        if n < min_tokens:
            continue  # discard
        if n > max_tokens:
            chunk = truncate_to_tokens(chunk, max_tokens)
        result.append(chunk)
    return result


def apply_overlap(chunks: list[str], overlap_tokens: int) -> list[str]:
    """
    Prepend the last `overlap_tokens` tokens of chunk[i-1] to chunk[i].
    This gives each chunk a short window of context from the previous one
    so retrieval doesn't lose meaning at hard semantic boundaries.

    The overlap is trimmed to keep the final chunk within CHUNK_MAX_TOKENS.
    The first chunk is unchanged.
    """
    if overlap_tokens <= 0 or len(chunks) < 2:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_ids = tokenizer.encode(chunks[i - 1], add_special_tokens=False)
        tail_ids = prev_ids[-overlap_tokens:]          # last N tokens of previous chunk
        tail_text = tokenizer.decode(tail_ids, skip_special_tokens=True)

        combined = tail_text.rstrip() + " " + chunks[i].lstrip()

        # Re-enforce the max-token cap (overlap must not blow the budget)
        combined = truncate_to_tokens(combined, CHUNK_MAX_TOKENS)
        result.append(combined)

    return result


def chunk_document(text: str, splitter: SemanticChunker, stype: str) -> list[str]:
    # Short documents get tighter guardrails so small content isn't thrown away
    if stype == "article":
        min_tok, max_tok, overlap = CHUNK_MIN_TOKENS, CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS
    else:
        min_tok, max_tok, overlap = 10, 30, 10

    raw_chunks = splitter.split_text(text)
    guardrailed = enforce_token_guardrails(raw_chunks, min_tok, max_tok)
    return apply_overlap(guardrailed, overlap)


# ---------------------------------------------------------------------------
# Source type hints — edit this to control how each .txt is labelled
# Add an entry here only if you want a non-default source_type or description.
# Files not listed get source_type="article" and description=stem.
# ---------------------------------------------------------------------------

SOURCE_META: dict[str, dict] = {
    "reddit_best_coffee":  {"source_type": "reddit",    "description": "Reddit — Best coffee shop"},
    "reddit_good_coffee":  {"source_type": "reddit",    "description": "Reddit — Charlotte has really good coffee"},
    "ig_best":             {"source_type": "instagram", "description": "Instagram — Best coffee shops"},
    "ig_5_must_visit":     {"source_type": "instagram", "description": "Instagram — 5 must-visit coffee shops"},
    "cathzine":            {"source_type": "article",   "description": "Cathzine — Best laptop-friendly cafes"},
    "sprudge":             {"source_type": "article",   "description": "Sprudge Guide to Coffee in Charlotte"},
    "hopculture":          {"source_type": "article",   "description": "Hop Culture — Best Coffee Roasters and Shops"},
    "henhouse":            {"source_type": "article",   "description": "Hen House — Favorite Charlotte Date Spots"},
    "wayward":             {"source_type": "article",   "description": "Wayward — 15 Essential Charlotte Coffee Shops"},
    "spoon":               {"source_type": "article",   "description": "Spoon University — Best Coffee Shops Near UNC Charlotte"},
    "yelp_top10":          {"source_type": "pdf",       "description": "Yelp — Top 10 Coffee Shops"},
    "charlotte_observer":  {"source_type": "pdf",       "description": "Charlotte Observer — Coffee Guide"},
}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run():
    # ------------------------------------------------------------------
    # STEP 1 — Scrape / fetch web sources listed in SOURCES → raw_docs/
    # Already-cached .txt files are loaded from disk; missing ones are
    # fetched from the network and saved so re-runs are fast.
    # ------------------------------------------------------------------
    print("=== Step 1: Web scraping → raw_docs ===")
    for src in SOURCES:
        sid = src["id"]
        stype = src["type"]
        raw_path = RAW_DIR / f"{sid}.txt"

        if raw_path.exists():
            print(f"  [skip] {sid} already cached")
            continue

        print(f"  Fetching [{sid}] ({stype})...")
        try:
            if stype == "reddit":
                raw = fetch_reddit(src["url"])
            elif stype == "article":
                raw = fetch_article(src["url"])
            else:
                print(f"  ⚠ Unknown type '{stype}', skipping")
                continue
            raw_path.write_text(raw, encoding="utf-8")
            print(f"  → saved ({len(raw)} chars)")
        except Exception as e:
            print(f"  ✗ Failed to fetch: {e}")

    # ------------------------------------------------------------------
    # STEP 2 — Convert any PDFs in raw_pdfs/ to .txt files in raw_docs/
    # ------------------------------------------------------------------
    print("\n=== Step 2: PDF → raw_docs ===")
    for pdf_file in sorted(PDF_DIR.glob("*.pdf")):
        out_path = RAW_DIR / (pdf_file.stem + ".txt")
        if out_path.exists():
            print(f"  [skip] {pdf_file.name} already extracted")
            continue
        print(f"  Extracting {pdf_file.name}...")
        try:
            text = load_pdf(pdf_file)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue
        if not text.strip():
            print(f"  ⚠ No text extracted, skipping")
            continue
        out_path.write_text(text, encoding="utf-8")
        print(f"  → saved to {out_path.name} ({len(text)} chars)")

    # ------------------------------------------------------------------
    # STEP 3 — Chunk every .txt in raw_docs/ into chunks.json
    # ------------------------------------------------------------------
    print("\n=== Step 3: Chunking raw_docs/*.txt ===")
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=95,
    )

    all_chunks: list[Chunk] = []

    for txt_file in sorted(RAW_DIR.glob("*.txt")):
        sid = txt_file.stem
        meta = SOURCE_META.get(sid, {})
        stype = meta.get("source_type", "article")
        desc = meta.get("description", sid)

        print(f"\n[{sid}]")
        raw = load_text_file(txt_file)
        cleaned = clean_text(raw)
        if not cleaned:
            print(f"  ⚠ Empty after cleaning, skipping")
            continue

        chunks = chunk_document(cleaned, splitter, stype)
        print(f"  → {len(chunks)} chunks")

        for i, chunk_text in enumerate(chunks):
            all_chunks.append(Chunk(
                chunk_id=f"{sid}__{i:03d}",
                source_id=sid,
                source_type=stype,
                source_description=desc,
                text=chunk_text,
                token_count=count_tokens(chunk_text),
            ))

    # --- Save output ---
    output = [asdict(c) for c in all_chunks]
    CHUNKS_OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Total chunks: {len(all_chunks)}")
    token_counts = [c.token_count for c in all_chunks]
    if token_counts:
        print(f"Token range:  {min(token_counts)} – {max(token_counts)}")
        print(f"Mean tokens:  {sum(token_counts) // len(token_counts)}")
    by_source = {}
    for c in all_chunks:
        by_source.setdefault(c.source_id, 0)
        by_source[c.source_id] += 1
    print("\nChunks per source:")
    for k, v in by_source.items():
        print(f"  {k:<30} {v}")
    print(f"\nSaved → {CHUNKS_OUT}")


if __name__ == "__main__":
    run()
