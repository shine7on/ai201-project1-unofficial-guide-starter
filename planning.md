# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
This Unofficial Guide covers student experiences living in Grinnell College's residence halls across North, South, and East Campus. While Grinnell's official website lists dorm amenities and locations, it doesn't capture what students actually think such as which dorms are noisy, which have the best community, which are worth requesting, and which to avoid. That real knowledge lives scattered across Reddit threads, student newspaper articles, review sites, and word of mouth between students.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RoomSurf |  Grinnell College Dorm Reviews ; 4 Reviews (Main/Gate/Loose/Norris) | https://roomsurf.com/dorm-reviews/grinnell |
| 2 | S&B Student Article | Student speaks: Dorm Hall Defense; students defend North/South/East campus | https://thesandb.com/46692/article/student-speaks-dorm-hall-defense/ |
| 3 | S&B article | recent housing changes 2024 | https://thesandb.com/45774/article/loose-hall-closes-renfrow-hall-opens-and-younker-hall-transitions-in-2024-grinnell-college/ |
| 4 | S&B article | CRIBZ: Renfrow Hall’s sweet suite; story about new dorm | https://thesandb.com/50642/features/cribz-renfrow-halls-sweet-suite/ |
| 5 | S&B article | Story about first-year only dorm | https://thesandb.com/54752/news/reslife-first-year-housing-cluster-model-met-with-student-disapproval/ |
| 6 | RateMyDorm | Review for Norris Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-norris-hall |
| 7 | RateMyDorm | Review for Rose Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-rose-hall|
| 8 | Grinnell College Website | Official hall descriptions | https://www.grinnell.edu/campus-life/student-life/living-spaces/residence-halls |
| 9 | Grinnell College Website | Official language house descriptions | https://www.grinnell.edu/campus-life/student-life/living-spaces/language-project-houses |
| 10 | Appily Review | Review about Grinnell College | https://www.appily.com/colleges/grinnell-college/reviews |
| 11 | Niche Review | Review about Grinnell College | https://www.niche.com/colleges/grinnell-college/campus-life/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ.
     Guiding questions — use these to think it through before deciding:
     - Are your documents short reviews (1–3 sentences) or long guides (many paragraphs)? How does that affect the right chunk size?
     - If a key fact spans two adjacent chunks, will either chunk be retrievable on its own? What does overlap help with?
     - How would you know if your chunks are too small? Too large? What would bad retrieval results look like in each case?

     Useful AI prompts:
     - "Explain how chunk size affects retrieval quality for short, opinion-based reviews."
     - "What are the tradeoffs between chunking by paragraph vs. fixed character count for [my document type]?"
     - "If I use 200-character chunks for review text, what kinds of queries might this fail for?"]
-->

**Chunk size:**
400 characters

**Overlap:**
50 characters

**Reasoning:**

My documents are a mix of short student reviews (2–5 sentences each) and longer student newspaper articles (multiple paragraphs). 

For review-heavy sources (Roomsurf, RateMyDorm, Niche), I will use fixed-size chunking with a chunk size of ~400 characters and an overlap of ~50 characters. Reviews are short and opinion-dense, so 400 characters is enough to capture one complete thought without merging unrelated reviews.

For article sources (Scarlet & Black), I will split by paragraph first, then cap at 500 characters, so natural topic boundaries are respected.

Overlap of 50 characters ensures that if a key opinion spans a chunk boundary (e.g. "noisy but great community"), both chunks carry enough context to be retrievable.

I chose NOT to use 200-character chunks because they would fragment individual reviews into incomplete thoughts that lose their meaning without surrounding context.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2
It runs locally so no API key, no cost, no rate limits.

**Top-k:**
Top-k means how many chunks you pull from the vector store to give the LLM as context.
We will start with k=4.

**Production tradeoff reflection:**
If deploying for real users with no cost constraint, I would switch to OpenAI's text-embedding-3-large. 
The main tradeoffs I would weigh are accuracy on domain-specific text (Grinnell jargon like "self-gov", "JRC", and "loggia" are unknown to MiniLM but a larger model generalizes better) and latency (larger models are slower per request, which matters when real users are waiting). Context length is less of a concern for this domain since dorm reviews are short. The tradeoff is that text-embedding-3-large costs money per API call and requires internet access, while all-MiniLM-L6-v2 runs free and locally.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which dorm is the newest/cleanest? | Renfrow |
| 2 |  Are there any dorms that only accept first-years? | Yes. For 2026-27, the first-year clusters are Cleveland, James, and Main on South Campus; Rathje and Rose on East Campus; and Norris and Smith on North Campus.  |
| 3 | What are the three campus clusters and what is each known for? | North Campus is known for athletes and social/rowdy atmosphere; South Campus for community, events, and the loggia; East Campus for quiet, AC, and newer facilities |
| 4 | What do students say about Younker Hall? | Students say Younker is centrally located near the JRC and HSSC, has a strong community feel, and is a popular choice for returning students. |
| 5 | What are the downsides of living on South Campus? | South Campus has no air conditioning, can be noisy, and is the oldest facility — though students say the community and social atmosphere make up for it. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Many Grinnell dorms have very few or zero online reviews (Dibble, Rawson, Lazier, Cleveland have almost nothing on RateMyDorm or  Roomsurf). This means queries about those specific dorms may return irrelevant chunks from other dorms, or gives wrong answer.

2. Terms like "self-gov", "JRC", "HSSC", "loggia", "10/10", "Bob's Underground" are Grinnell-specific and likely out-of-vocabulary for all-MiniLM-L6-v2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

## Architecture



## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->


I will use Claude (claude.ai) as my primary AI tool throughout the project. 

**Document ingestion + cleaning script**
Input: my Documents section, the list of .txt file names, and a description of the noise in each source 
(HTML leftovers, nav text, ads).
Expected output: a Python script that loads all .txt files from /documents, cleans them, and outputs structured text ready for chunking.

**Chunking implementation**
Input: my Chunking Strategy section (400 char cap, 50 char overlap, paragraph-first logic) and the pipeline diagram.
Expected output: a chunk_text() function that implements paragraph splitting with a character cap and overlap, and attaches source filename as metadata to each chunk.

**Embedding + ChromaDB setup**
Input: my Retrieval Approach section (MiniLM, k=4, ChromaDB) and the pipeline diagram.
Expected output: a script that embeds all chunks using sentence-transformers and loads them into ChromaDB with source metadata.

**Retrieval function**
Input: the ChromaDB schema from step 3 and my top-k=4 requirement.
Expected output: a query() function that takes a question string and returns the top 4 chunks with their source document names.

**5. Grounded generation + Gradio UI**
Input: my grounding requirement (answer from retrieved chunks only, cite sources), the retrieval function output format, and the Gradio skeleton from the project spec.
Expected output: a complete app.py that wires retrieval to Groq llama-3.3-70b-versatile and displays answer + sources 
in a Gradio interface.

For each of these I will review what Claude generates, verify it matches my spec, and correct anything that doesn't fit my document structure or chunking decisions before running it.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
