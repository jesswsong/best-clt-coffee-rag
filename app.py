import gradio as gr
from query import ask

def handle_query(question):
    if not question.strip():
        return "", ""
    result = ask(question)
    sources = "\n".join(f"• {s['description']}" for s in result["sources"])
    return result["answer"], sources

CSS = """
/* ── Page background ── */
body, .gradio-container {
    background: linear-gradient(160deg, #1a0a00 0%, #2d1200 40%, #1a0a00 100%) !important;
}

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 32px 16px 8px;
    font-family: 'Playfair Display', serif;
}
.hero .logo-art {
    font-size: 3.2rem;
    letter-spacing: 0.15em;
    line-height: 1.1;
    color: #f5c97a;
    text-shadow: 0 0 30px #a0520088, 0 2px 8px #000a;
}
.hero h1 {
    font-size: 2rem !important;
    font-weight: 700;
    color: #f5c97a !important;
    margin: 6px 0 4px !important;
    letter-spacing: 0.04em;
    text-shadow: 0 2px 12px #0008;
}
.hero .tagline {
    color: #c49a52;
    font-size: 0.95rem;
    letter-spacing: 0.06em;
    margin-bottom: 0;
}

/* ── Steam divider ── */
.steam-bar {
    text-align: center;
    font-size: 1.3rem;
    color: #c49a5288;
    letter-spacing: 0.5em;
    margin: 4px 0 20px;
}

/* ── Panels ── */
.gradio-container .block, .gradio-container label, .gradio-container textarea,
.gradio-container input {
    background: #1e0c03 !important;
    border-color: #5c3317 !important;
    color: #f0e2c8 !important;
}
.gradio-container label span { color: #c49a52 !important; font-weight: 600; }

/* ── Ask button ── */
.ask-btn {
    background: linear-gradient(135deg, #7b3a10, #a0520a) !important;
    color: #fff5e0 !important;
    border: 1px solid #c47a2a !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.05em;
    transition: all 0.2s;
}
.ask-btn:hover {
    background: linear-gradient(135deg, #a0520a, #c47a2a) !important;
    box-shadow: 0 0 18px #c47a2a66 !important;
}

/* ── Examples row ── */
.examples-holder { background: #120600 !important; border-color: #3b1f0a !important; }
.examples-holder button { color: #c49a52 !important; }

/* ── Footer ── */
footer { display: none !important; }
"""

HEADER = """
<div class="hero">
  <div class="logo-art">☕🫘☕</div>
  <h1>Best Coffee in CLT RAG System</h1>
  <p class="tagline">☁ freshly brewed answers from local sources ☁</p>
</div>
<div class="steam-bar">~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~</div>
"""

with gr.Blocks(
    css=CSS,
    theme=gr.themes.Soft(
        primary_hue="orange",
        neutral_hue="stone",
        font=[gr.themes.GoogleFont("Playfair Display"), gr.themes.GoogleFont("Inter")],
    ),
    title="Best Coffee in CLT RAG System",
) as demo:

    gr.HTML(HEADER)

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                placeholder="e.g. Where's a good laptop-friendly café in NoDa?",
                label="☕  Your question",
                lines=2,
            )
            btn = gr.Button("Ask  ☕", elem_classes="ask-btn", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label="🫘  Answer",
                lines=7,
                interactive=False,
            )
        with gr.Column(scale=1):
            sources_box = gr.Textbox(
                label="📜  Sources used",
                lines=7,
                interactive=False,
            )

    gr.Markdown("<p style='text-align:center; color:#5c3317; font-size:0.85rem;'>— try one of these —</p>")
    gr.Examples(
        examples=[
            ["What are the best coffee shops in Charlotte for studying?"],
            ["Which cafés in Charlotte are good for a date?"],
            ["Where can I find specialty espresso in Charlotte?"],
            ["What coffee shops are near UNCC?"],
        ],
        inputs=inp,
        label="",
    )

    gr.HTML(
        "<p style='text-align:center; color:#3b1f0a; font-size:0.8rem; margin-top:24px;'>"
        "☕ · 🫘 · ☕ · 🫘 · ☕ · 🫘 · ☕ · 🫘 · ☕</p>"
    )

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

demo.launch()