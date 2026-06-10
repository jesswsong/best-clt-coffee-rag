import gradio as gr
from query import ask

def handle_query(question):
    if not question.strip():
        return "", ""
    result = ask(question)
    sources = "\n".join(f"• {s['description']}" for s in result["sources"])
    return result["answer"], sources

CSS = """
h1 { text-align: center; }
.subtitle { text-align: center; color: #6b7280; margin-top: -8px; margin-bottom: 24px; }
.ask-btn { background: #3b1f0a !important; color: #fff !important; }
.ask-btn:hover { background: #5c3317 !important; }
footer { display: none !important; }
"""

with gr.Blocks(
    css=CSS,
    theme=gr.themes.Soft(
        primary_hue="orange",
        neutral_hue="stone",
        font=gr.themes.GoogleFont("Inter"),
    ),
    title="Best Coffee in CLT RAG System",
) as demo:

    gr.Markdown("# ☕ Best Coffee in CLT RAG System")
    gr.Markdown(
        "<p class='subtitle'>Ask anything about Charlotte's coffee scene — "
        "answers sourced from local guides, Reddit, and more.</p>"
    )

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                placeholder="e.g. Where's a good laptop-friendly café in NoDa?",
                label="Your question",
                lines=2,
            )
            btn = gr.Button("Ask ☕", elem_classes="ask-btn", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(label="Answer", lines=6, interactive=False)
        with gr.Column(scale=1):
            sources_box = gr.Textbox(label="Sources used", lines=6, interactive=False)

    gr.Examples(
        examples=[
            "What are the best coffee shops in Charlotte for studying?",
            "Which cafés in Charlotte are good for a date?",
            "Where can I find specialty espresso in Charlotte?",
            "What coffee shops are near UNCC?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

demo.launch()