# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain
**Best Coffee shops in Charlotte**

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
Coffee shops are one of the most popular third spaces across the states -- they spark creativity, connection, and innovation. Yet there's always so many coffee shops around town, and each serve a different purpose. It's hard to get the vibes unless you have visited them all and took notes. So, here's a guide to new people to the city of Charlotte on what coffee shops will fit into what you're looking for. 


*Example questions*
- What's the best place to study late in Charlotte?
- What's a cafe that laptop friendly?
- What's a cafe that's good for reading?
- What's a cafe that has fancy, experimental coffee?
- What's a good cafe if I just want to catch up with my friend or go on a date?


---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit Thread| A thread on good coffess around CLT | https://www.reddit.com/r/Charlotte/comments/1phh3cn/charlotte_has_really_good_coffee/|
| 2 | article / website| A newspaper article on coffee shops around town |https://www.charlotteobserver.com/charlottefive/c5-food-drink/article312516268.html |
| 3 | Reddit Thread | A reddit discussion that discusses the best coffee shops | https://www.reddit.com/r/Charlotte/comments/1kgupce/best_coffee_shop/ |
| 4 | article | Best Laptop-Friendly Cafés in Charlotte | https://cathzine.substack.com/p/best-laptop-friendly-cafes-in-charlotte|
| 5 | website |The Sprudge Guide To Coffee In Charlotte, North Carolina |https://sprudge.com/the-sprudge-guide-to-coffee-in-charlotte-north-carolina-193932.html |
| 6 | website | The Best Coffee Shops Near UNC Charlotte For Studying | https://spoonuniversity.com/school/uncc/the-best-coffee-shops-near-unc-charlotte-for-studying/
| 7 | website | Start Your Day at These 15 Essential Charlotte Coffee Shops | https://www.waywardblog.com/best-coffee-charlotte-north-carolina/ |
| 8 | Website article| The Best Coffee Roasters And Shops in Charlotte, North Carolina | https://www.hopculture.com/best-coffee-charlotte-north-carolina-craft-roasters-shops/|
| 9 | Yelp Ranking/Thread | Best Coffee in Charlotte | The Best Coffee Roasters And Shops in Charlotte, North Carolina|
| 10 | Article | Favorite Charlotte Date Spots | https://www.henhousedesign.co/blog/favorite-charlotte-date-spots

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

My sources are primarily long texts (articles) but there are also a couple of short texts (instagram reel description and reddit thread). Therefore, I want to use a way to emcompass info from both types at the same time.

**Chunk size:** max size 512, min 100 tokens

**Overlap:** ~50 tokens (1-2 sentences)

**Reasoning:** Fortunately, most articles on cafe shops seperate each coffee shop into a seperate paragraph, and 512 tokens is a size that can fit information about a paragraph comfortably, while the minimum token size will capture a thread comment nicely.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

<!-- I feel like I don't know enough! -->

**Embedding model: text-embedding-3-small**

**Top-k: 7**

**Production tradeoff reflection:**
For long paragraphs, I need a large enough capability to process a chunk to be able to retrieve enough meaning for information about a café. `text-embedding-3-small` has 8k token context, 1536-dim vectors, and consistently top-tier MTEB scores. Since I don't have that much data, I think it is okay to sacrifice some computational power in order to capture the most information out of a paragraph. As I read the articles, they often overlap on the best cafes. I believe 5-10 is a good `k` to capture enough information to showcase what the cafe is good for from multiple angles, so I want to start with 7. 
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What's the best place to study late in Charlotte?| Haraz Coffee or Qawah House|
| 2 | What's a cafe that's good for reading? | Smelly Cat|
| 3 | What's a cafe that has fancy, experimental coffee? | Hex Coffee|
| 4 | What's a good cafe if I just want to catch up with my friend or go on a date? | Smelly Cat|
| 5 | What's a cafe that laptop friendly? | Stable Hand, Sumaq Coffee |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. I am concerned that my documents are a mix of short and long texts, causing the potential that some chunks will have elaborate information on one cafe while others will contain multiple cafes, causing loss of information.

2. Certain articles list the cafe names before an intro paragraph, and so my chunking strategy may or may not be able to capture the names in the chunk. There's also the risk that a cafe name could be wrongly assigned to the paragraph before instead of after.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

![alt text](image.png)

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
