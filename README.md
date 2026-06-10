# The Unofficial Guide — Project 1

---

## Domain

This system covers student experiences living in Grinnell College's residence halls across North, South, and East Campus. The knowledge is valuable because Grinnell's official website lists amenities and building specs but doesn't capture what students actually think such as which dorms are noisy, which have the best community, which are worth requesting, and which to avoid. That real knowledge lives scattered across student newspaper articles and review sites. A prospective student or incoming first-year trying to make a housing decision cannot find it in one place through official channels.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RoomSurf | Student dorm reviews (4 halls) | https://roomsurf.com/dorm-reviews/grinnell |
| 2 | The Scarlet & Black | Article: Dorm Hall Defense — students defend their campus | https://thesandb.com/46692/article/student-speaks-dorm-hall-defense/ |
| 3 | The Scarlet & Black | Article: Loose closes, Renfrow opens, Younker transitions (2024) | https://thesandb.com/45774/article/loose-hall-closes-renfrow-hall-opens-and-younker-hall-transitions-in-2024-grinnell-college/ |
| 4 | The Scarlet & Black | Article: CRIBZ — Renfrow Hall's sweet suite feature | https://thesandb.com/50642/features/cribz-renfrow-halls-sweet-suite/ |
| 5 | The Scarlet & Black | Article: First-year housing cluster model met with disapproval | https://thesandb.com/54752/news/reslife-first-year-housing-cluster-model-met-with-student-disapproval/ |
| 6 | RateMyDorm | Student reviews — Norris Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-norris-hall |
| 7 | RateMyDorm | Student reviews — Rose Hall | https://www.ratemydorm.com/reviews/grinnell-college/grinnell-college-rose-hall |
| 8 | Grinnell College official website | Official residence hall descriptions (all halls) | https://www.grinnell.edu/campus-life/student-life/living-spaces/residence-halls |
| 9 | Grinnell College official website | Language and project house descriptions | https://www.grinnell.edu/campus-life/student-life/living-spaces/language-project-houses |
| 10 | Appily | College reviews mentioning dorm life | https://www.appily.com/colleges/grinnell-college/reviews |
| 11 | Manually added | Per-hall official pages (Clark, Cleveland, Cowles, Dibble, Gates, Haines, James, Kershaw, Langan, Lazier, Loose, Main, Norris, Rathje, Rawson, Read, Renfrow, Rose, Smith, Younker) | documents/clean/grinnell_official_*.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters for review and official sources; 500 characters for multi-paragraph S&B articles.

**Overlap:** 50 characters carried over between consecutive chunks.

**Why these choices fit your documents:**
My corpus is a mix of short student reviews (2–5 sentences) and longer newspaper articles (multiple paragraphs). For review sources like RoomSurf and RateMyDorm, I used line-first splitting. Each line is one review for one dorm, so splitting by line prevents a single 400-character window from spanning two unrelated dorm reviews. For official hall pages, fixed-size character chunking at 400 characters captures one feature section (e.g., laundry, lounges, history) per chunk without merging unrelated amenities. For S&B articles, I split by paragraph first, then cap at 500 characters, so natural topic boundaries in the article are respected. The 50-character overlap ensures that if a key opinion spans a chunk boundary (e.g., "noisy but great community"), both adjacent chunks carry enough context to be retrievable. I also added a minimum chunk length of 60 characters to drop useless tail fragments — tiny leftovers like `"1920"` or `"ago."` produced by fixed-size splitting hitting the end of a document.

**Final chunk count:** 195 chunks across 30 source files.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`. It runs locally with no API key, no cost, and no rate limits. It produces 384-dimensional vectors and embeds all 195 chunks in under 10 seconds on a laptop CPU.

**Production tradeoff reflection:**
If deploying for real users with no cost constraint, I would switch to OpenAI's `text-embedding-3-large`. The main tradeoffs I would weigh are accuracy on domain-specific text and latency. Grinnell jargon like "self-gov," "JRC," "HSSC," and "loggia" are likely out-of-vocabulary or low-frequency for MiniLM, which was trained on general web text — a larger model trained on more diverse data generalizes better to these terms. Latency matters when real users are waiting for a response; larger API-hosted models add a round-trip network call on top of the inference time. Context length is less of a concern for this domain since dorm reviews are short. The core tradeoff is accuracy and vocabulary coverage (text-embedding-3-large) versus cost-free local operation with no internet dependency (MiniLM).

---

## Grounded Generation

**System prompt grounding instruction:**
The system prompt gives the model hard rules, not suggestions. The exact instruction is:

```
STRICT RULES:
1. You may ONLY use information from the provided context passages below. Do not use any outside knowledge, even if you are confident about it.
2. If the context does not contain enough information to answer the question, you MUST respond with: "I don't have enough information in my sources to answer that question."
3. Do not speculate, infer beyond what the passages say, or add general college advice.
```

The words "ONLY," "MUST," and "Do not" are hard prohibitions, not polite suggestions. The fallback phrase is explicitly quoted in the prompt so the model has a script to follow when it cannot answer, rather than deciding how to express uncertainty. Temperature is set to 0.2 to minimize creative drift away from the retrieved text.

The user message also ends with: *"Answer using only the context passages above,"* reinforcing the constraint at the point where the model actually reads the context.

**How source attribution is surfaced in the response:**
Source attribution is handled entirely by code, not by the LLM. After retrieval, `format_sources(chunks)` builds the source list directly from ChromaDB metadata — it reads `chunk["source"]` for each retrieved chunk and maps it to a human-readable label. The model never decides which sources to cite; the UI always shows every source that was retrieved, regardless of whether the model mentioned it in its answer text. This means attribution is programmatically guaranteed rather than dependent on the model's behavior.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which dorm is the newest and cleanest? | Renfrow | Says East Campus dorms are newer/nicer and notes Norris is "like a hotel" — mentions both but does not name Renfrow | Partially relevant | Partially accurate |
| 2 | Are there any dorms that only accept first-years? | Yes — Cleveland, James, Main (South); Rathje, Rose (East); Norris, Smith (North) | "I don't have enough information"; the specific hall list existed in the corpus but ranked just outside top-4 | Off-target | Inaccurate |
| 3 | What are the three campus clusters and what is each known for? | North=athletes/rowdy, South=community/events/loggia, East=quiet/AC/new | Correctly names all three clusters and their characteristics; mentions AC, community, concerts, proximity to academic buildings | Relevant | Accurate |
| 4 | What do students say about Younker Hall? | Centrally located, JRC/HSSC proximity, strong community feel, popular with returning students | Correctly describes experience at Yonker such as central location, proximity to JRC/HSSC, social hub, returns every year | Relevant | Accurate |
| 5 | What are the downsides of living on South Campus? | No AC, noisy, oldest facility | "I don't have enough information"; retrieved chunks covered South Campus positives; the chunk containing "no air conditioning and occasional noise" ranked 5th | Off-target | Inaccurate |

---

## Failure Case Analysis

**Question that failed:** *"Are there any dorms that only accept first-years?"*

**What the system returned:** `"I don't have enough information in my sources to answer that question."` Even though `sandb_firstyear_cluster` chunk #1 contains the exact answer: *"the new first-year clusters will be Cleveland, James and Main in South Campus, Rathje and Rose in East Campus and Norris and Smith in North Campus."*

**Root cause (tied to a specific pipeline stage):**
Two pipeline problems compounded each other.

First, **chunking**: the 50-character overlap caused chunk #1 of the first-year cluster article to start mid-sentence — `"an email to The S&B, Vice President of Student Affairs JC Lopez wrote that the new first-year clusters will be Cleveland…"`. The chunk's most important content (the list of hall names) is buried 60 characters into a fragment that opens with bureaucratic email metadata. The embedding of this chunk is pulled toward the topic of email correspondence, not first-year housing clusters — which weakened its similarity score.

Second, **vocabulary mismatch at the embedding stage**: the query phrase *"dorms that only accept first-years"* doesn't match the article's language, which uses *"first-year only housing clusters"* and *"implementing clusters."* MiniLM (`all-MiniLM-L6-v2`) encodes meaning from training frequency, and the paraphrase distance between "only accept" and "housing cluster model" is large enough in 384-dimensional space that chunk #1 ranked 5th — just outside the k=4 cutoff.

**What you would change to fix it:**
Two targeted fixes. First, increase k from 4 to 6 for queries that contain the word "first-year" or "only" — this would have surfaced chunk #1 in the context. Second, add a sentence-level pre-processing step that keeps the first full sentence of each article chunk intact rather than starting at the overlap boundary, so the hall name list appears at the start of chunk #1 where the embedding weights it more heavily.

---

## Spec Reflection

**One way the spec helped you during implementation:**
The Chunking Strategy section of planning.md forced me to decide before writing any code that review sources and article sources needed different strategies. When I actually implemented `chunk.py`, having that decision already made meant I knew immediately to write three separate functions — `_line_review_chunks` for review lists, `_paragraph_chunks` for S&B articles, and `_fixed_size_chunks` for official pages — rather than reaching for one universal approach. Without that prior decision, I would likely have applied fixed-size chunking everywhere and only discovered the cross-dorm merging problem (a 400-character window spanning two different dorm reviews) during testing, not design.

**One way your implementation diverged from the spec, and why:**
The spec described a single chunking function with one chunk size (400 characters) and one overlap (50 characters). The implementation ended up with three distinct strategies and two chunk sizes (400 for reviews, 500 for articles). This diverged because during inspection of the first chunked outputs, it became clear that fixed-size splitting on review list sources like RoomSurf was merging a Gates Hall review and a Norris Hall review into the same chunk — meaning a query about one hall could retrieve a chunk that was mostly about a different hall. The line-first strategy for review sources was added to fix this. The spec was written before seeing real document structure; the implementation adjusted once the actual data made the problem visible.

---

## AI Usage

**Instance 1: Generating the full ingestion and cleaning pipeline**

- *What I gave the AI:* My Documents section from planning.md (the list of 11 source URLs with descriptions), and a description of the noise present in each source type — HTML tags, navigation menus, cookie banners, "Read more" links, and site-specific boilerplate like RoomSurf's "Need a Roommate?" banners and Appily's college comparison table.
- *What it produced:* A complete `ingest.py` with `fetch_raw()` caching raw HTML to `documents/raw/`, a `clean_html()` function using BeautifulSoup to strip junk tags and boilerplate CSS classes, and a `main()` that saved cleaned text to `documents/clean/`. It also added site-specific CSS selectors (e.g., `div.sno-story-body` for S&B) to extract article content before cleaning.
- *What I changed or overrode:* The initial cleaner was too aggressive — S&B articles were being reduced to 163 characters because the `header` tag removal was stripping article headers along with navigation. I directed the AI to add content-targeting selectors to isolate the article body first. I also added the `_DROP_LINE_PATTERNS` regex to remove site-specific boilerplate (RoomSurf's "1 Review" count lines, Appily's college comparison table rows) that the HTML cleaning missed because those were plain text inside content divs. I also added the `keep_short_lines` flag for the language houses file, which has short address lines that the isolated-line filter was incorrectly dropping.

**Instance 2: Generating the generation and Gradio interface**

- *What I gave the AI:* The Grounded Generation section of planning.md (answer from retrieved chunks only, cite sources, use Groq llama-3.3-70b-versatile), the `query()` function signature from `embed.py` showing the return format `{text, source, chunk_index, distance}`, and the requirement that source attribution be programmatically guaranteed rather than left to the LLM.
- *What it produced:* A complete `app.py` with a `SYSTEM_PROMPT` using grounding rules, a `generate_answer()` function calling Groq, a `format_sources()` function building the source list from metadata, and a `gr.Blocks()` Gradio UI with question input, answer box, sources box, and example questions wired to both button click and Enter key.
- *What I changed or overrode:* The first version of the system prompt used soft language ("try to use only the provided context"). I directed the AI to rewrite it with hard rules using "ONLY," "MUST," and "Do not" — and to include the explicit fallback phrase quoted verbatim so the model had a script rather than deciding how to express uncertainty. I also overrode the `temperature` from the default (1.0) to 0.2 to reduce creative drift. After running the 5 eval questions and seeing that Q5 ("downsides of South Campus") correctly triggered the fallback rather than hallucinating, I confirmed the grounding was working and kept the prompt as-is.
