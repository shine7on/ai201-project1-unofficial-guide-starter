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
| 6 | RateMyProfessor | Review for Norris Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-norris-hall |
| 7 | RateMyProfessor | Review for Rose Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-rose-hall|
| 8 | Grinnell College Website | Official hall descriptions | https://www.grinnell.edu/campus-life/student-life/living-spaces/residence-halls |
| 9 | Grinnell College Website | Official language house descriptions | https://www.grinnell.edu/campus-life/student-life/living-spaces/language-project-houses |
| 10 | Appily Review | Review about Grinnell College | https://www.appily.com/colleges/grinnell-college/reviews |
| 11 | Niche Review | Review about Grinnell College | https://www.niche.com/colleges/grinnell-college/campus-life/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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
