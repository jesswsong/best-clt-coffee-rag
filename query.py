"""
generation.py — RAG generation and CLI interface
Charlotte Coffee Shop RAG Pipeline — Milestone 3

LLM     : Groq  llama-3.3-70b-versatile  (free tier, OpenAI-compatible)
Retrieval: retrieval.py  (ChromaDB + all-MiniLM-L6-v2)
Output  : answer with inline [Source N] citations  +  appended source list
"""

import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from transformers import pipeline

from retrieval import build_index, retrieve, TOP_K

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LLM_MODEL   = "llama-3.3-70b-versatile"
MAX_TOKENS  = 512
TEMPERATURE = 0.2       # low = more factual / grounded

SYSTEM_PROMPT = """\
You are a helpful local guide specialising in Charlotte, NC coffee shops.
Answer the user's question using ONLY the information in the numbered source \
documents provided. Do not use any outside knowledge.

You MUST respond with valid JSON in exactly this format and nothing else:
{"answer": "<your answer here>", "citations": [<source numbers you used>]}

Rules:
- "answer": your response as a plain string. Keep it concise (2–4 sentences).
- "citations": a JSON array of the integer source numbers (e.g. [1, 3]) whose \
text you actually used. Every claim in your answer must be backed by a cited source.
- If the documents don't contain enough information, set "answer" to \
"I don't have enough information on that." and "citations" to [].
- Never invent details (hours, prices, addresses) not present in the documents.
- Output raw JSON only — no markdown fences, no extra keys, no explanation.\
"""

# ---------------------------------------------------------------------------
# Entity-level grounding check
# ---------------------------------------------------------------------------

# Loaded once at import time; dslim/bert-base-NER is small (~400 MB) and
# recognises ORG entities well enough for business names.
_ner = pipeline(
    "ner",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple",   # merges sub-word tokens into full spans
)


def _extract_shop_names(text: str) -> list[str]:
    """Return ORG entity spans found in *text* by the NER model."""
    entities = _ner(text)
    return [e["word"] for e in entities if e["entity_group"] == "ORG"]


def validate_shop_names(answer: str, cited_hits: list[dict]) -> dict:
    """
    Extract coffee shop names mentioned in *answer*, then verify each one
    appears literally in the text of at least one cited chunk.

    Returns:
        {
          "all_valid": bool,
          "results": [
            {"name": str, "found": bool, "found_in_sources": [int, ...]},
            ...
          ]
        }
    """
    shop_names = _extract_shop_names(answer)
    cited_text_by_rank = {h["rank"]: h["text"] for h in cited_hits}

    results = []
    for name in shop_names:
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        found_in = [
            rank for rank, text in cited_text_by_rank.items()
            if pattern.search(text)
        ]
        results.append({
            "name": name,
            "found": len(found_in) > 0,
            "found_in_sources": found_in,
        })

    return {
        "all_valid": all(r["found"] for r in results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context(hits: list[dict]) -> str:
    """Numbered context block injected into the user message."""
    blocks = []
    for hit in hits:
        blocks.append(
            f"[Source {hit['rank']}] {hit['source_description']}\n{hit['text']}"
        )
    return "\n\n".join(blocks)


def _format_sources(hits: list[dict], cited_only: set[int] | None = None) -> str:
    """
    Deduplicated source list appended below the answer.
    If cited_only is provided, only show sources whose rank is in that set.
    """
    seen: dict[str, str] = {}
    for hit in hits:
        if cited_only and hit["rank"] not in cited_only:
            continue
        if hit["source_id"] not in seen:
            seen[hit["source_id"]] = hit["source_description"]
    if not seen:
        return "Sources: none cited"
    lines = ["Sources:"]
    for desc in seen.values():
        lines.append(f"  • {desc}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask(
    query: str,
    k: int = TOP_K,
    collection=None,
    client: Groq | None = None,
) -> dict:
    """
    Full RAG pipeline: retrieve → generate → format.

    Returns:
        question  — original query string
        answer    — LLM response with inline [Source N] citations
        sources   — deduplicated list of {id, type, description} dicts
        hits      — raw retrieval results (useful for debugging or UI display)
    """
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    hits = retrieve(query, k=k, collection=collection)

    user_message = f"Documents:\n{_build_context(hits)}\n\nQuestion: {query}"

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )
    raw = response.choices[0].message.content.strip()

    # Parse structured output; fall back gracefully if the model misbehaves
    try:
        parsed = json.loads(raw)
        answer_text = str(parsed["answer"])
        citation_nums = [int(n) for n in parsed.get("citations", [])]
    except (json.JSONDecodeError, KeyError):
        # Model didn't return valid JSON — treat the whole response as the answer
        answer_text = raw
        citation_nums = []

    # Map citation numbers back to the actual retrieved hits (1-indexed)
    valid_ranks = {hit["rank"] for hit in hits}
    citation_nums = [n for n in citation_nums if n in valid_ranks]

    cited_hits = [hit for hit in hits if hit["rank"] in set(citation_nums)]
    seen: dict[str, dict] = {}
    for hit in cited_hits:
        if hit["source_id"] not in seen:
            seen[hit["source_id"]] = {
                "id":          hit["source_id"],
                "type":        hit["source_type"],
                "description": hit["source_description"],
            }

    # Entity-level grounding: verify every shop name in the answer appears
    # in the text of the chunks it claims to cite.
    shop_validation = validate_shop_names(answer_text, cited_hits)
    if not shop_validation["all_valid"]:
        unverified = [r["name"] for r in shop_validation["results"] if not r["found"]]
        answer_text = (
            f"{answer_text}\n\n"
            f"⚠️ Note: the following recommendation(s) could not be verified "
            f"in the cited sources: {', '.join(unverified)}."
        )

    return {
        "question":         query,
        "answer":           answer_text,
        "citations":        citation_nums,
        "sources":          list(seen.values()),
        "hits":             hits,
        "shop_validation":  shop_validation,   # {"all_valid": bool, "results": [...]}
    }


def format_response(result: dict, show_scores: bool = False) -> str:
    """Render an ask() result as a readable string for the terminal."""
    thin  = "─" * 62
    thick = "═" * 62
    lines = [
        thick,
        f"  ☕  {result['question']}",
        thin,
        "",
        f"  {result['answer']}",
        "",
        thin,
        _format_sources(result["hits"], cited_only=set(result.get("citations", []))),
        thick,
    ]
    if show_scores:
        lines += ["", "  Retrieved chunks:"]
        for hit in result["hits"]:
            preview = hit["text"][:120].replace("\n", " ")
            lines.append(
                f"    [{hit['rank']}] score={hit['score']:.4f}  "
                f"{hit['source_id']} (chunk {hit['chunk_index']})"
            )
            lines.append(f"        {preview}...")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interactive REPL
# ---------------------------------------------------------------------------

def run_interface() -> None:
    """
    Interactive CLI loop.

    Commands:
        /quit or /exit  — exit
        /scores         — toggle retrieved-chunk score display
        /rebuild        — force-rebuild the ChromaDB index from chunks.json
        /k <n>          — change number of retrieved chunks (default 5)
    """
    banner = r"""
  ____          __  __            _          ___ _   _    _____
 |  _ \        / _|/ _|          (_)        / __| | | |  |_   _|
 | |_) | ___  | |_| |_ ___  ___   _ _ __  | |   | |_| |    | |
 |  _ < / _ \ |  _|  _/ _ \/ _ \ | | '_ \ | |   |  _  |    | |
 | |_) |  __/ | | | ||  __/  __/ | | | | || |___| | | |    | |
 |____/ \___| |_| |_| \___|\___| |_|_| |_| \____|_| |_|    |_|

        ☕  Best Coffee in CLT RAG System  ☕
    """
    print(banner)
    print("─" * 62)
    print("  Building / verifying vector index...")
    col = build_index()

    groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    show_scores = False
    k = TOP_K

    print(f"\n  Ready. Retrieving top-{k} chunks per query.")
    print("  Commands: /quit  /scores  /rebuild  /k <n>")
    print("─" * 62 + "\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not query:
            continue

        if query.lower() in ("/quit", "/exit"):
            print("Bye!")
            break

        if query.lower() == "/scores":
            show_scores = not show_scores
            print(f"  [chunk scores {'ON' if show_scores else 'OFF'}]")
            continue

        if query.lower() == "/rebuild":
            col = build_index(force_rebuild=True)
            continue

        if query.lower().startswith("/k "):
            try:
                k = int(query.split()[1])
                print(f"  [k = {k}]")
            except ValueError:
                print("  Usage: /k <integer>")
            continue

        try:
            result = ask(query, k=k, collection=col, client=groq_client)
            print(f"\n{format_response(result, show_scores=show_scores)}\n")
        except Exception as e:
            print(f"  Error: {e}")


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if not os.environ.get("GROQ_API_KEY"):
        raise EnvironmentError(
            "GROQ_API_KEY not set — copy .env.example to .env and add your key."
        )

    # Single-shot mode: python generation.py "your question"
    if len(sys.argv) > 1:
        col = build_index()
        query = " ".join(sys.argv[1:])
        result = ask(query, collection=col)
        print(format_response(result))
    else:
        run_interface()
