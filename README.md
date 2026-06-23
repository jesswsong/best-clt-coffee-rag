# A guide to the best coffee shops in Charlotte 👑☕️

A retrieval-augmented generation system that answers questions about Charlotte, NC coffee shops using only information sourced from local guides, Reddit threads, and curated articles. Every answer cites the documents it draws from — the system is designed to refuse rather than hallucinate. Built this because I kept getting generic Google results when I moved to Charlotte, and wanted something grounded in real community knowledge.

---

## Demo

```
python app.py
```
<img width="1080" height="654" alt="image" src="https://github.com/user-attachments/assets/fbb9abc1-b449-4e78-946d-9e488279b396" />

---

## Architecture

Five stages, each producing a clean artifact consumed by the next:

```
Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
```

| Stage | File | What it does |
|---|---|---|
| Ingestion | `ingest.py` Step 1–2 | Scrapes web articles and Reddit via `requests` + `BeautifulSoup`; extracts PDFs with `pdfplumber`. Saves everything as `.txt` to `raw_docs/`. |
| Chunking | `ingest.py` Step 3 | Cleans text, splits with LangChain `SemanticChunker` (topic-boundary splits, not fixed character counts), applies per-source-type token guardrails and 30-token overlap. Outputs `chunks.json`. |
| Embedding | `retrieval.py` | Embeds all chunks with `all-MiniLM-L6-v2` (local, no API key). Stores vectors + metadata in a persistent ChromaDB collection using cosine similarity. |
| Retrieval | `retrieval.py` | Embeds the query with the same model, returns top-k chunks ranked by cosine similarity. |
| Generation | `query.py` | Injects retrieved chunks as numbered context into a Groq `llama-3.3-70b-versatile` prompt. Forces structured JSON output `{"answer": "...", "citations": [1, 3]}`. Validates citation numbers and runs NER to verify coffee shop names appear in cited chunks. |

---

## Grounding & Citation Validation

Most RAG demos rely entirely on a system prompt instruction to stay on-topic. This system adds two layers on top of that:

**Structured output enforcement** — the LLM is required to return JSON with an explicit `citations` array of the source numbers it used. Any hallucinated source number (e.g. citing Source 9 when only 7 chunks were retrieved) is programmatically stripped before the response is returned.

**NER-based entity verification** — a BERT NER model (`dslim/bert-base-NER`) extracts coffee shop names mentioned in the answer and checks that each name appears literally in the text of the cited chunks. If a shop name can't be verified, a warning is appended to the response rather than silently surfacing a potentially hallucinated recommendation.

**System prompt:**
```
You are a helpful local guide specialising in Charlotte, NC coffee shops.
Answer the user's question using ONLY the information in the numbered source
documents provided. Do not use any outside knowledge.

You MUST respond with valid JSON in exactly this format and nothing else:
{"answer": "<your answer here>", "citations": [<source numbers you used>]}

Rules:
- Every claim in your answer must be backed by a cited source.
- If the documents don't contain enough information, set "answer" to
  "I don't have enough information on that." and "citations" to [].
- Never invent details (hours, prices, addresses) not present in the documents.
- Output raw JSON only — no markdown fences, no extra keys, no explanation.
```

---

## Data Sources

10 sources covering articles, community discussions, and social content:


| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit Thread| A thread on good coffess around CLT | https://www.reddit.com/r/Charlotte/comments/1phh3cn/charlotte_has_really_good_coffee/|
| 2 | article / website| A newspaper article on coffee shops around town |https://www.charlotteobserver.com/charlottefive/c5-food-drink/article312516268.html |
| 3 | Reddit Thread | A reddit discussion that discusses the best coffee shops | https://www.reddit.com/r/Charlotte/comments/1kgupce/best_coffee_shop/ |
| 4 | article | Best Laptop-Friendly Cafés in Charlotte | https://cathzine.substack.com/p/best-laptop-friendly-cafes-in-charlotte|
| 5 | article |The Sprudge Guide To Coffee In Charlotte, North Carolina |https://sprudge.com/the-sprudge-guide-to-coffee-in-charlotte-north-carolina-193932.html |
| 6 | article | Start Your Day at These 15 Essential Charlotte Coffee Shops |https://www.waywardblog.com/best-coffee-charlotte-north-carolina/ |
| 7 | article | The Best Coffee Shops Near UNC Charlotte For Studying | https://spoonuniversity.com/school/uncc/the-best-coffee-shops-near-unc-charlotte-for-studying/ |
| 8 | Website article| The Best Coffee Roasters And Shops in Charlotte, North Carolina | https://www.hopculture.com/best-coffee-charlotte-north-carolina-craft-roasters-shops/|
| 9 | Yelp Ranking/Thread | Best Coffee in Charlotte | The Best Coffee Roasters And Shops in Charlotte, North Carolina|
| 10 | Article | Favorite Charlotte Date Spots | https://www.henhousedesign.co/blog/favorite-charlotte-date-spots

Instagram content was saved manually as text files since Instagram blocks scraping. PDFs were extracted with `pdfplumber` including table-to-text conversion.

---

## Chunking Strategy

Source type is passed as a parameter to the chunking function because different source formats have naturally different information density:

| Source type | Min tokens | Max tokens | Overlap |
|---|---|---|---|
| Articles | 50 | 110 | 30 |
| Reddit / Instagram | 10 | 30 | 10 |

Splitting uses LangChain's `SemanticChunker` with a percentile-95 breakpoint threshold — it splits where sentence-embedding similarity drops most sharply rather than at fixed character counts. This keeps café-specific paragraphs together instead of cutting mid-recommendation.

The 30-token overlap on articles preserves context across chunk boundaries (e.g. a pronoun in chunk N+1 that refers to a café named in chunk N).

**Total chunks: 54**

---

## Embedding Model

**`sentence-transformers/all-MiniLM-L6-v2`** — chosen because it runs fully locally (no API key or rate limits), is well-established as a retrieval baseline, and performs well on general English text. Charlotte coffee shops are a general-domain topic, so a domain-specific model isn't needed.

The main limitation is its 256-token context window. Chunks are sized to stay within this limit (110 token max), so no content is silently truncated during embedding.

**Production tradeoff:** At scale I would evaluate `text-embedding-3-small` (OpenAI) for better accuracy, or `e5-large-v2` for a stronger local alternative with a longer context window. I would also add a re-ranking step (e.g. Cohere Rerank) between retrieval and generation to improve precision at high recall.

---

## Evaluation

Five test questions run against the live system:

| # | Question | Expected | System response | Retrieval | Accuracy |
|---|----------|----------|-----------------|-----------|----------|
| 1 | What's the best place to study late in Charlotte? | Haraz Coffee or Qawah House | "I don't have enough information on that." | Partially relevant | Accurate |
| 2 | What's a café that's good for reading? | Smelly Cat | Summit Coffee — studying atmosphere, comfortable seating | Relevant | Accurate |
| 3 | What's a café that has fancy or artisan coffee? | Hex Coffee | Vavela (Turkish coffee), Amelie's (French café atmosphere) | Relevant | Accurate |
| 4 | What's a good café to catch up with a friend or go on a date? | Smelly Cat | Stable Hand — energetic, social atmosphere | Relevant | Accurate |
| 5 | What's a laptop-friendly café? | Stable Hand, Sumaq Coffee | Undercurrent, Stable Hand — reliable WiFi and comfortable seating | Relevant | Accurate |

### Failure case

**Question:** "What's the best place to study late at night?"

**Returned:** "I don't have enough information on that."

**Root cause (Retrieval stage):** The corpus contains a chunk that mentions a café being open late, but the top-7 retrieved chunks didn't include it. The embedding for "late at night" matched more strongly against chunks containing time-adjacent tokens like "8:31 pm" (a website timestamp) and "Moonlight" (a drink name), which pulled the retrieval results off-target. The relevant chunk existed but ranked below the cutoff.

**Fix:** Better cleaning during ingestion to strip timestamps, menu item names, and navigational text that create noisy token matches. Expanding k from 7 to 9 for ambiguous time-based queries would also help.

---

## Setup

```bash
git clone https://github.com/jesswsong/ai201-project1-unofficial-guide-starter
cd ai201-project1-unofficial-guide-starter

pip install -r requirements.txt

cp .env.example .env
# add your GROQ_API_KEY to .env

python ingest.py       # scrape sources, chunk, save chunks.json
python retrieval.py    # embed chunks, build ChromaDB index
python app.py          # launch Gradio UI
```

Requires Python 3.11+

---

## Stack

| Component | Tool |
|---|---|
| LLM | Groq `llama-3.3-70b-versatile` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB (persistent, on-disk) |
| Semantic chunking | LangChain `SemanticChunker` |
| Web scraping | `requests` + `BeautifulSoup4` |
| PDF extraction | `pdfplumber` |
| NER grounding check | `dslim/bert-base-NER` (HuggingFace) |
| UI | Gradio |

---

> Built during [CodePath AI201](https://www.codepath.org/).
