# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Coffee shops are one of the most popular third spaces across the states -- they spark creativity, connection, and innovation. Yet there's always so many coffee shops around town, and each serve a different purpose. It's hard to get the vibes unless you have visited them all and took notes. So, here's a guide to new people to the city of Charlotte on what coffee shops will fit into what you're looking for. 

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit Thread| A thread on good coffess around CLT | https://www.reddit.com/r/Charlotte/comments/1phh3cn/charlotte_has_really_good_coffee/|
| 2 | article / website| A newspaper article on coffee shops around town |https://www.charlotteobserver.com/charlottefive/c5-food-drink/article312516268.html |
| 3 | Reddit Thread | A reddit discussion that discusses the best coffee shops | https://www.reddit.com/r/Charlotte/comments/1kgupce/best_coffee_shop/ |
| 4 | article | Best Laptop-Friendly Cafés in Charlotte | https://cathzine.substack.com/p/best-laptop-friendly-cafes-in-charlotte|
| 5 | article |The Sprudge Guide To Coffee In Charlotte, North Carolina |https://sprudge.com/the-sprudge-guide-to-coffee-in-charlotte-north-carolina-193932.html |
| 6 | Instagram reel | 5 must visit coffee shops in CLT |https://www.instagram.com/reel/DVv-XEqjh2h/?hl=en |
| 7 | Instagram reel | 10 best coffee shops in CLT | https://www.instagram.com/reel/C7j0rL0RcWI/?hl=en |
| 8 | Website article| The Best Coffee Roasters And Shops in Charlotte, North Carolina | https://www.hopculture.com/best-coffee-charlotte-north-carolina-craft-roasters-shops/|
| 9 | Yelp Ranking/Thread | Best Coffee in Charlotte | The Best Coffee Roasters And Shops in Charlotte, North Carolina|
| 10 | Article | Favorite Charlotte Date Spots | https://www.henhousedesign.co/blog/favorite-charlotte-date-spots

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

| | min chunk size | max chunk size | overlap |
|--------|----|----|----|
| article | 50 | 110 | 30 |
| non-article | 10| 30 | 10 |

**Why these choices fit your documents:**
Since I looked for a diverse set of sources, such as Reddit and online blog posts, the chunk size that makes sense for each source is also differnt. Therefore, I added source type as a input to the chunking function. 

**Final chunk count: 54**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used: all-MiniLM-L6-v2**

**Production tradeoff reflection:**
I used this model because it's one the standard baselines for embedding models. It's small, it's fast, and it is easily supported. If I was deploying this system for real users, I would want to use a model that allows for larger context length limits than 256 tokens, what MiniLM supports. MiniLM is trained on general web text, and since coffee shops are a pretty generic topic, I think MiniLM is enough for that. My topic also doesn't require extensive multilingal support or extremely good quality, so I think MiniLM is a pretty good fit. 

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
```
"""\
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
```

**How source attribution is surfaced in the response:**
The context is created by a join of the top 7 chunks retrieved and the query above. The structured output forces the json to contain a mandatory citations field. If this field doesn't contain anything, then I force the LLM to regenerate a response through the context. In addition, if the citation is source 7 but there were only 5 chunks, that citation is stripped. Lastly, I implemented a NER system to identify the coffee shop names recommended in the prompt, and validate that this name appear in the text of the citation.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What's the best place to study late in Charlotte?| Haraz Coffee or Qawah House| not enough information | partially relevant | accurate
| 2 | What's a cafe that's good for reading? | Smelly Cat| Summit Coffee, reading wasn't mentioned but has the right vibe for studying | Relevant | Accurate
| 3 | What's a cafe that has fancy or artisan coffee? | Hex Coffee| Vavela cafe with Turkish coffee, Amelie's French Bakery with French Cafe atmosphere | Relevant | Accurate
| 4 | What's a good cafe if I just want to catch up with my friend or go on a date? | Smelly Cat| Stable Hand, a cafe with energetic atmosphere | Relevant | Accurate
| 5 | What's a cafe that laptop friendly? | Stable Hand, Sumaq Coffee | Undercurrent, Stable Hand - reliable WiFi and comfortable seating | Relevant | Accurate

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->


**Question that failed:** What's the best place to study late at night?

**What the system returned:** I don't have enough information on that.

**Root cause (tied to a specific pipeline stage):** Retrieval
Even though there are chunks that specifically mention open late, the top 7 chunks didn't include them. Instead, the retrieval code retrieved chunks that contained info that's more relevant to (e.g. 8 : 31 pm, moonlight (a drink, in the original context)) rather than the one chunk that includes 'open late'. 

**What you would change to fix it:**
I believe certain noises got into the scraped text, such as timestamps on the website. I would ensure the data is cleaner w/o noise texts from ads to fix it.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
`planning.md` gave me a clear idea of what I was building before I started building. I think in this age of vibe coding it's so easy to just tell Claude to develop a RAG system. Having `planning.md` on really ensured that I thought about what model is and what chunking strategy I was choosing before just driving straight into development.

**One way your implementation diverged from the spec, and why:**
The specs asked for one chunking size, yeah, Darren development because I chose a variety of different sources. I noticed that the the same chunking sizes are not working for all of my documents. Articles naturally contain longer chunks than Reddit threads, so I made the choice to create that divergence.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I gave the AI instruction to implement a system that ensures theit's using retrieved chunks as context. 
- *What it produced:* It added validation in instruction and tuned temperature lower, but didn't implement a strategy to ensure that the content is straight from the context
- *What I changed or overrode:* I asked it to add a NER section to identify the coffee shop names recommended in the prompt, and validate that this name appear in the text of the citation.

**Instance 2**

- *What I gave the AI:* I gave the AI instructions to implement a chunking method with min and max token limits. 
- *What it produced:* It implemented it with 500 as the max token limit.
- *What I changed or overrode:* Through just reading through my texts, I knew that 500 is too large of a chunk size. I did a few rounds of testing and decided 110 created the best results. 
