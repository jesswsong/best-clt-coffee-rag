import gradio as gr
from query import ask

SOURCE_URLS = {
    "cathzine":          "https://cathzine.substack.com/p/best-laptop-friendly-cafes-in-charlotte",
    "sprudge":           "https://sprudge.com/the-sprudge-guide-to-coffee-in-charlotte-north-carolina-193932.html",
    "hopculture":        "https://www.hopculture.com/best-coffee-charlotte-north-carolina-craft-roasters-shops/",
    "henhouse":          "https://www.henhousedesign.co/blog/favorite-charlotte-date-spots",
    "wayward":           "https://www.waywardblog.com/best-coffee-charlotte-north-carolina/",
    "spoon":             "https://spoonuniversity.com/school/uncc/the-best-coffee-shops-near-unc-charlotte-for-studying/",
    "reddit_good_coffee":"https://www.reddit.com/r/Charlotte/comments/1phh3cn/charlotte_has_really_good_coffee/",
    "reddit_best_coffee":"https://www.reddit.com/r/Charlotte/comments/1kgupce/best_coffee_shop/",
}

def _sources_html(sources: list[dict]) -> str:
    if not sources:
        body = "<p style='color:#b89878; font-style:italic; font-size:0.85rem;'>No sources cited.</p>"
    else:
        items = []
        for s in sources:
            url = SOURCE_URLS.get(s["id"])
            label = s["description"]
            if url:
                items.append(
                    f'<li><a href="{url}" target="_blank" rel="noopener" '
                    f'style="color:#5c3a1e; font-size:0.85rem; line-height:2; '
                    f'text-decoration:underline; text-underline-offset:3px;">'
                    f'{label}</a></li>'
                )
            else:
                items.append(
                    f'<li style="color:#6b5640; font-size:0.85rem; line-height:2;">{label}</li>'
                )
        body = f'<ul style="list-style:none; padding:0; margin:0;">{"".join(items)}</ul>'

    return (
        '<div class="sources-panel">'
        '<p class="sources-panel-label">Sources used</p>'
        f'{body}'
        '</div>'
    )

def handle_query(question):
    if not question.strip():
        return "", ""
    result = ask(question)
    return result["answer"], _sources_html(result["sources"])

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');

body, .gradio-container {
    background: #f0ebe3 !important;
    font-family: 'Inter', sans-serif !important;
}

/* hero card */
.hero-card {
    background: #e8e0d4;
    border-radius: 24px;
    padding: 32px 36px 32px 32px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 36px;
    align-items: center;
    margin-bottom: 20px;
}
.hero-illustration {
    background: #c9b89a;
    border-radius: 16px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}
.hero-eyebrow {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8c7355;
    margin-bottom: 10px;
}
.hero-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    color: #2a1a0a !important;
    line-height: 1.15 !important;
    margin: 0 0 12px !important;
}
.hero-sub {
    font-size: 0.88rem;
    color: #6b5640;
    line-height: 1.7;
    margin-bottom: 20px;
}

/* search row inside hero */
.search-row { display: flex; gap: 10px; align-items: center; }
.search-row input {
    flex: 1;
    background: #fff9f2 !important;
    border: 1.5px solid #c9a87c !important;
    border-radius: 50px !important;
    padding: 10px 20px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    color: #2a1a0a !important;
}
.search-row input::placeholder { color: #b89878; font-style: italic; }

.ask-btn {
    background: #2a1a0a !important;
    color: #f0ebe3 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 10px 24px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
.ask-btn:hover { background: #3d2810 !important; }

/* result panels */
.gradio-container .block {
    background: #fff9f2 !important;
    border: 1.5px solid #e0cdb4 !important;
    border-radius: 16px !important;
}
.gradio-container label span {
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #8c7355 !important;
    font-weight: 500 !important;
}
.gradio-container textarea {
    background: #fff9f2 !important;
    color: #2a1a0a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    border: none !important;
}

/* examples */
.examples-holder {
    background: transparent !important;
    border: none !important;
}
.examples-holder button {
    background: #e8e0d4 !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-style: italic !important;
    font-size: 0.8rem !important;
    color: #5c3a1e !important;
}
.examples-holder button:hover { background: #ddd0be !important; }

/* sources HTML panel */
.sources-panel {
    background: #fff9f2;
    border: 1.5px solid #e0cdb4;
    border-radius: 16px;
    padding: 14px 18px;
    min-height: 160px;
}
.sources-panel-label {
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8c7355;
    font-weight: 500;
    margin-bottom: 10px;
}

footer { display: none !important; }
"""

HERO = """
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<div class="hero-card">
  <div class="hero-illustration">
    <svg width="260" height="200" viewBox="0 0 260 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="260" height="200" fill="#b8956a"/>
      <rect x="20" y="100" width="110" height="80" rx="4" fill="#8c6642"/>
      <rect x="32" y="112" width="86" height="58" rx="2" fill="#f0ebe3" opacity="0.55"/>
      <ellipse cx="170" cy="138" rx="40" ry="34" fill="#6b4423"/>
      <ellipse cx="170" cy="133" rx="32" ry="26" fill="#3d2010"/>
      <ellipse cx="170" cy="130" rx="24" ry="19" fill="#2a1206"/>
      <path d="M154 100 Q159 84 164 100" stroke="#c9a87c" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      <path d="M164 100 Q169 80 174 100" stroke="#c9a87c" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      <path d="M174 100 Q179 90 184 100" stroke="#c9a87c" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      <rect x="132" y="160" width="76" height="12" rx="6" fill="#8c6642"/>
      <rect x="127" y="172" width="86" height="8" rx="4" fill="#6b4423"/>
      <rect x="62" y="28" width="140" height="88" rx="8" fill="#1a1a1a" opacity="0.88"/>
      <rect x="68" y="34" width="128" height="72" rx="5" fill="#2d2d2d"/>
      <line x1="76" y1="50" x2="134" y2="50" stroke="#c9a87c" stroke-width="2" opacity="0.7"/>
      <line x1="76" y1="62" x2="152" y2="62" stroke="#c9a87c" stroke-width="2" opacity="0.45"/>
      <line x1="76" y1="74" x2="144" y2="74" stroke="#c9a87c" stroke-width="2" opacity="0.35"/>
      <line x1="76" y1="86" x2="158" y2="86" stroke="#c9a87c" stroke-width="2" opacity="0.25"/>
      <rect x="166" y="40" width="14" height="10" rx="3" fill="#c9a87c" opacity="0.55"/>
      <rect x="182" y="40" width="14" height="10" rx="3" fill="#a0714f" opacity="0.45"/>
    </svg>
  </div>
  <div>
    <p class="hero-eyebrow">Charlotte, NC &nbsp;·&nbsp; Coffee Guide</p>
    <h1 class="hero-title">Best Coffee<br>in CLT</h1>
    <p class="hero-sub">Ask anything about Charlotte's coffee scene — answers sourced from local guides, Reddit, and more. Every answer cites its sources.</p>
  </div>
</div>
"""

with gr.Blocks(
    css=CSS,
    theme=gr.themes.Base(
        font=[gr.themes.GoogleFont("Inter")],
    ),
    title="Best Coffee in CLT",
) as demo:

    gr.HTML(HERO)

    with gr.Row():
        inp = gr.Textbox(
            placeholder="e.g. best cozy café to work from in NoDa?",
            label="Your question",
            lines=1,
            scale=4,
        )
        btn = gr.Button("Ask ☕", elem_classes="ask-btn", variant="primary", scale=1)

    with gr.Row():
        answer_box = gr.Textbox(label="Answer", lines=7, interactive=False, scale=3)
        sources_box = gr.HTML(
            value="",
            label="Sources used",
        )

    gr.Examples(
        examples=[
            ["Best spots for studying near UNCC?"],
            ["Where's good for a date in Charlotte?"],
            ["Where can I find specialty espresso?"],
            ["Laptop-friendly cafés in NoDa?"],
        ],
        inputs=inp,
        label="— try one of these —",
    )

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

demo.launch()