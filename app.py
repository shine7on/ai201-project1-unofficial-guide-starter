"""
Stage 5: Grounded generation + Gradio interface

Pipeline:
    User question
        ↓
    query(question, k=4)          embed.py  →  ChromaDB top-4 chunks
        ↓
    build_prompt(question, chunks)  →  Groq  llama-3.3-70b-versatile
        ↓
    answer  +  source list (programmatic, from chunk metadata)
        ↓
    Gradio UI

Grounding contract
------------------
- The system prompt *forbids* the model from using outside knowledge.
- If the retrieved chunks don't contain the answer, the model must say so.
- Source attribution is built by the CODE from chunk metadata — the LLM
  never decides which sources to cite.  It only writes the answer text.

Run:
    python app.py
"""

import os
from dotenv import load_dotenv
import gradio as gr
from groq import Groq

from embed import query as retrieve   # returns list of {text, source, chunk_index, distance}

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_MODEL  = "llama-3.3-70b-versatile"
TOP_K       = 4

# ---------------------------------------------------------------------------
# Grounded generation
# ---------------------------------------------------------------------------

# System prompt — grounding is a hard rule, not a suggestion.
# "only" and "must" are load-bearing words here.
SYSTEM_PROMPT = """You are the Unofficial Grinnell Dorm Guide — a helpful assistant that answers questions about living in Grinnell College residence halls.

STRICT RULES:
1. You may ONLY use information from the provided context passages below. Do not use any outside knowledge, even if you are confident about it.
2. If the context does not contain enough information to answer the question, you MUST respond with: "I don't have enough information in my sources to answer that question."
3. Do not speculate, infer beyond what the passages say, or add general college advice.
4. Write in a helpful, conversational tone — as if a current Grinnell student is answering.
5. Keep answers concise: 2–4 sentences unless the question clearly requires more detail."""


def build_context_block(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a numbered context block for the prompt.
    Each passage is labelled with its source so the model sees where it came from
    (useful for coherence) but source attribution in the UI is handled by code, not the LLM.
    """
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[Passage {i} — source: {chunk['source']}]\n{chunk['text']}")
    return "\n\n".join(lines)


def generate_answer(question: str, chunks: list[dict]) -> str:
    """Call Groq with the grounded system prompt + retrieved context."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    context_block = build_context_block(chunks)

    user_message = f"""Context passages:
{context_block}

Question: {question}

Answer using only the context passages above."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # low temperature → more faithful to context, less creative drift
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def format_sources(chunks: list[dict]) -> str:
    """
    Build the source list programmatically from chunk metadata.
    This is NOT left to the LLM — the code always shows every source
    that was retrieved, regardless of what the model chose to mention.
    """
    # Deduplicate by source name while preserving order
    seen = set()
    sources = []
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            seen.add(src)
            sources.append(src)

    # Make source names readable
    label_map = {
        "sandb_dorm_defense":         "The Scarlet & Black — Dorm Hall Defense (2024)",
        "sandb_housing_changes_2024":  "The Scarlet & Black — Housing Changes 2024",
        "sandb_renfrow_suite":         "The Scarlet & Black — Renfrow Hall Feature",
        "sandb_firstyear_cluster":     "The Scarlet & Black — First-Year Cluster Policy",
        "roomsurf_grinnell":           "RoomSurf — Grinnell Dorm Reviews",
        "ratemydorm_norris":           "RateMyDorm — Norris Hall",
        "ratemydorm_rose":             "RateMyDorm — Rose Hall",
        "appily_grinnell":             "Appily — Grinnell College Reviews",
        "grinnell_official_halls":     "Grinnell College — Official Hall Descriptions",
        "grinnell_official_language_houses": "Grinnell College — Language & Project Houses",
    }

    lines = []
    for src in sources:
        # Official per-hall pages follow the pattern grinnell_official_<hallname>
        if src.startswith("grinnell_official_"):
            hall = src.replace("grinnell_official_", "").replace("_", " ").title()
            label = f"Grinnell College — Official {hall} Hall Page"
        else:
            label = label_map.get(src, src)
        lines.append(f"• {label}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline — called by Gradio on each submission
# ---------------------------------------------------------------------------

def answer_question(question: str) -> tuple[str, str]:
    """
    Full RAG pipeline: retrieve → generate → attribute.

    Returns
    -------
    answer  : str  — grounded answer text
    sources : str  — newline-separated source labels (always programmatic)
    """
    question = question.strip()
    if not question:
        return "Please enter a question.", ""

    # Stage 4: retrieve top-k chunks
    chunks = retrieve(question, k=TOP_K)

    # Stage 5a: generate grounded answer
    answer = generate_answer(question, chunks)

    # Stage 5b: build source list from metadata (never from LLM output)
    sources = format_sources(chunks)

    return answer, sources


# ---------------------------------------------------------------------------
# Gradio interface
# ---------------------------------------------------------------------------

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Grinnell Unofficial Dorm Guide") as demo:

        gr.Markdown("""
# 🏠 The Unofficial Grinnell Dorm Guide
Ask anything about living in Grinnell College residence halls — which dorms have AC,
which campuses are social vs. quiet, what students actually think about specific halls.

*Answers are grounded in student reviews and S&B articles. Sources shown below each answer.*
        """)

        with gr.Row():
            with gr.Column(scale=3):
                question_box = gr.Textbox(
                    label="Your question",
                    placeholder="e.g. What are the downsides of living on South Campus?",
                    lines=2,
                )
                submit_btn = gr.Button("Ask", variant="primary")

        with gr.Row():
            with gr.Column(scale=3):
                answer_box = gr.Textbox(
                    label="Answer",
                    lines=6,
                    interactive=False,
                )
            with gr.Column(scale=2):
                sources_box = gr.Textbox(
                    label="Sources used",
                    lines=6,
                    interactive=False,
                )

        # Example questions from the evaluation plan
        gr.Examples(
            examples=[
                ["Which dorm is the newest and cleanest?"],
                ["Are there any dorms that only accept first-years?"],
                ["What are the three campus clusters and what is each known for?"],
                ["What do students say about Younker Hall?"],
                ["What are the downsides of living on South Campus?"],
            ],
            inputs=question_box,
        )

        # Wire up both the button click and Enter key (submit on textbox)
        submit_btn.click(
            fn=answer_question,
            inputs=question_box,
            outputs=[answer_box, sources_box],
        )
        question_box.submit(
            fn=answer_question,
            inputs=question_box,
            outputs=[answer_box, sources_box],
        )

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting Grinnell Unofficial Dorm Guide…")
    print(f"  Model : {GROQ_MODEL}")
    print(f"  Top-k : {TOP_K}")
    app = build_ui()
    app.launch(theme=gr.themes.Soft())
