"""Shared helpers, data loading, components and the page layout for LLModel.com."""
import datetime
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "_build"
DATA = BUILD / "data"
SRC = BUILD / "src"
SITE = json.loads((BUILD / "site.json").read_text())
UPDATED = SITE["updated"]

# ---------------------------------------------------------------- helpers

def esc(s):
    return "" if s is None else html.escape(str(s), quote=True)


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "x"


def file_hash(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def fmt_date(d, long=False):
    """'2026-10-07' -> 'Oct 7, 2026'; '2026-04' -> 'Apr 2026'."""
    if not d:
        return "Unknown"
    parts = str(d).split("-")
    names = MONTHS_LONG if long else MONTHS
    if len(parts) == 3:
        return f"{names[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    if len(parts) == 2:
        return f"{names[int(parts[1]) - 1]} {parts[0]}"
    return parts[0]


def date_sort_key(d):
    parts = (str(d) + "-01-01").split("-")[:3]
    return "-".join(p.zfill(2) for p in parts)


def fmt_price(v):
    if v is None:
        return "&mdash;"
    if v == 0:
        return "Free"
    if v >= 1:
        s = f"{v:,.2f}"
        return "$" + (s[:-3] if s.endswith(".00") else s)
    s = f"{v:.3f}".rstrip("0")
    if len(s.split(".")[1]) < 2:
        s = f"{v:.2f}"
    return "$" + s


def fmt_money(v):
    """Totals: $0.42, $18, $1,240, $12.6K"""
    if v is None:
        return "&mdash;"
    if v < 0.01:
        return "<$0.01"
    if v < 10:
        return f"${v:,.2f}"
    if v < 100000:
        return f"${v:,.0f}"
    return f"${v/1000:,.0f}K"


def fmt_tokens(n):
    if not n:
        return "&mdash;"
    n = int(n)
    if n % 1024 == 0:
        k = n // 1024
        if k >= 1024:
            m = k / 1024
            return (f"{m:g}" if m == int(m) else f"{m:.2f}".rstrip("0").rstrip(".")) + "M"
        return f"{k}K"
    if n >= 1_000_000:
        return f"{n/1e6:.2f}".rstrip("0").rstrip(".") + "M"
    return f"{round(n/1000):g}K"


def fmt_int(n):
    return f"{int(n):,}"


def fmt_params(m):
    t, a = m.get("params_total_b"), m.get("params_active_b")
    if not t:
        return "Undisclosed"
    def b(x):
        if x >= 1000:
            return f"{x/1000:.2f}".rstrip("0").rstrip(".") + "T"
        return (f"{x:g}") + "B"
    if a and a != t:
        return f"{b(t)} total, {b(a)} active"
    return b(t)


def blended(m):
    if m.get("price_in") is None or m.get("price_out") is None:
        return None
    return (3 * m["price_in"] + m["price_out"]) / 4


def words(n):
    return f"{n:,}"


# ---------------------------------------------------------------- data

def load_json(name):
    return json.loads((DATA / name).read_text())


PROVIDER_OVERRIDES = {
    "openai": {
        "name": "OpenAI",
        "summary": "OpenAI is the San Francisco company behind ChatGPT and the GPT model families. Its current API lineup is the GPT-6 family: GPT-6 Astra for the most demanding reasoning and coding work, GPT-6.1 Sol as a lower-cost option close to Astra, and GPT-6 Luna for high-volume tasks, with several GPT-5.x models still available. In August 2025 it also released gpt-oss-120b and gpt-oss-20b, Apache 2.0 open-weight reasoning models you can run on your own hardware or through most inference providers.",
        "open_weights": "Yes: gpt-oss-120b and gpt-oss-20b under Apache 2.0. All GPT-6 and GPT-5.x models are proprietary.",
    },
    "google": {
        "name": "Google",
        "summary": "Google develops the Gemini models through Google DeepMind and offers them through the Gemini API, Google AI Studio and Google Cloud. As of October 2026 its stable Gemini text models are Gemini 3.8 Flash, Gemini 3.6 Flash and two Flash-Lite models, while Gemini 3.1 Pro is offered as a preview. Its open-weight Gemma 4 family, released under Apache 2.0, runs from on-device E2B and E4B models up to a 31B dense model and a 26B mixture-of-experts.",
        "open_weights": "Yes: Gemma 4 under Apache 2.0 (earlier Gemma generations used the Gemma Terms of Use). Gemini models are proprietary.",
    },
    "meta": {
        "name": "Meta",
        "summary": "Meta builds AI for its own apps through Meta Superintelligence Labs. Its hosted Muse Spark models are sold through the Meta Model API, a public-preview platform that works with the OpenAI SDK, while Muse Glimmer 30B (August 2026) and the 2025 Llama 4 models are open-weight releases you can download from Hugging Face or call through third-party hosts.",
        "open_weights": "Yes: Llama 4 Scout and Maverick under the Llama 4 Community License, and Muse Glimmer 30B under Apache 2.0. Muse Spark is API-only.",
    },
    "xai": {"name": "xAI", "aka": "SpaceXAI"},
}


def load_models():
    closed = load_json("models-closed.json")
    opened = load_json("models-open.json")
    models = closed["models"] + opened["models"]
    providers = {}
    for p in closed["providers"] + opened["providers"]:
        if p["slug"] in providers:
            continue
        providers[p["slug"]] = dict(p)
    for slug, ov in PROVIDER_OVERRIDES.items():
        if slug in providers:
            providers[slug].update(ov)
    for p in providers.values():
        p["models"] = []
    tier_rank = {"frontier": 0, "advanced": 1, "efficient": 2, "compact": 3}
    status_rank = {"current": 0, "preview": 1, "legacy": 2}
    for m in models:
        m["tier_rank"] = tier_rank.get(m["tier"], 4)
        m["status_rank"] = status_rank.get(m["status"], 3)
        m["blended"] = blended(m)
        m["url_page"] = f"model-{m['slug']}.html"
        m["provider_name"] = providers[m["provider"]]["name"]
        providers[m["provider"]]["models"].append(m)
    for p in providers.values():
        p["url_page"] = f"{p['slug']}-models.html"
        p["models"].sort(key=lambda m: (m["status_rank"], m["tier_rank"], -(m["blended"] or 0)))
    slugs = [m["slug"] for m in models]
    assert len(slugs) == len(set(slugs)), "duplicate model slug"
    return models, providers


META_RE = re.compile(r"<!--meta\s*(\{.*?\})\s*-->", re.S)


def read_src(path):
    t = Path(path).read_text()
    m = META_RE.search(t)
    if not m:
        raise ValueError(f"missing meta block in {path}")
    meta = json.loads(m.group(1))
    return meta, t[m.end():].strip()


def load_guides():
    out = []
    for f in sorted((SRC / "guides").glob("*.html")):
        meta, body = read_src(f)
        meta["body"] = body
        meta["words"] = len(re.sub(r"<[^>]+>", " ", body).split())
        meta["minutes"] = max(1, round(meta["words"] / 230))
        out.append(meta)
    return out


MODELS, PROVIDERS = load_models()
MODEL_BY = {m["slug"]: m for m in MODELS}
GUIDES = load_guides()
GUIDE_BY = {g["slug"]: g for g in GUIDES}
# The glossary is split into one data file and one page per topic. Order here is the order on the glossary hub.
# (category in the data, file and page slug, display name, intro, four example terms for the meta description)
GLOSSARY_TOPICS = [
    ("Fundamentals", "fundamentals", "Fundamentals",
     "The core ideas: what a large language model is, how text becomes tokens, what parameters and context windows are, and the words used to describe different kinds of models.",
     ["tokens", "context windows", "parameters", "reasoning models"]),
    ("Architecture", "architecture", "Model architecture",
     "What sits inside a model: the transformer, attention and its faster variants, positional encodings, mixture-of-experts layers, and alternatives such as state space and diffusion models.",
     ["attention", "transformers", "mixture of experts", "RoPE"]),
    ("Training", "training", "Training",
     "How models learn: pretraining, fine-tuning and LoRA, preference methods such as RLHF, DPO and GRPO, scaling laws, and the problems that show up along the way.",
     ["pretraining", "fine-tuning", "LoRA", "RLHF"]),
    ("Inference & deployment", "inference-deployment", "Inference and deployment",
     "Running models: sampling settings such as temperature and top-p, quantization formats, the KV cache, speed metrics, GPUs and VRAM, and the engines used to serve or self-host models.",
     ["KV cache", "quantization", "temperature", "vLLM"]),
    ("Prompting", "prompting", "Prompting",
     "Techniques for instructing a model: system prompts, few-shot examples, chain-of-thought, prompt chaining and context engineering.",
     ["system prompts", "few-shot prompting", "chain-of-thought", "context engineering"]),
    ("Building apps", "building-apps", "Building LLM apps",
     "Building products on models: retrieval-augmented generation, search and reranking, tool calling, MCP, structured outputs and AI agents.",
     ["RAG", "vector databases", "tool calling", "MCP"]),
    ("Evaluation", "evaluation", "Evaluation and benchmarks",
     "Measuring models: benchmarks such as MMLU, GPQA and SWE-bench, arena Elo ratings, contamination, LLM-as-a-judge and long-context tests.",
     ["benchmarks", "MMLU", "SWE-bench", "LLM-as-a-judge"]),
    ("Safety & governance", "safety-governance", "Safety and governance",
     "Risks, rules and safeguards: prompt injection, jailbreaks, guardrails, red teaming, alignment, privacy, copyright and the EU AI Act.",
     ["prompt injection", "jailbreaks", "guardrails", "the EU AI Act"]),
    ("Business & pricing", "business-pricing", "Business and pricing",
     "What a model costs and how you buy it: per-token pricing, batch APIs, prompt caching, rate limits, dedicated endpoints and model licenses.",
     ["cost per token", "prompt caching", "rate limits", "model licenses"]),
]
GLOSSARY = [t for cat, slug, *_ in GLOSSARY_TOPICS for t in load_json(f"glossary/{slug}.json")["terms"]]
GLOSS_BY = {t["slug"]: t for t in GLOSSARY}
GLOSS_TOPIC_SLUG = {cat: slug for cat, slug, *_ in GLOSSARY_TOPICS}


def glossary_href(term_slug):
    """Link to a term on the topic page that holds its full definition."""
    return f'glossary-{GLOSS_TOPIC_SLUG[GLOSS_BY[term_slug]["category"]]}.html#{term_slug}'


GLOSS_LINK_RE = re.compile(r'href="glossary\.html#([a-z0-9-]+)"')


def glossary_links(doc):
    """Point glossary.html#term links (used in guides and other sources) at the term's topic page."""
    return GLOSS_LINK_RE.sub(lambda m: f'href="{glossary_href(m.group(1))}"' if m.group(1) in GLOSS_BY else m.group(0), doc)
VIDEOS = load_json("videos.json")["videos"]
TIMELINE = load_json("timeline.json")["events"]
PROMPTS = load_json("prompts.json")["prompts"]
for _p in PROMPTS:  # templates are stored one line per array item, which keeps the JSON readable
    if isinstance(_p["prompt"], list):
        _p["prompt"] = "\n".join(_p["prompt"])
RESOURCES = load_json("resources.json")

TIER_LABEL = {"frontier": "Frontier", "advanced": "Advanced", "efficient": "Efficient", "compact": "Compact"}
STATUS_LABEL = {"current": "Current", "preview": "Preview", "legacy": "Legacy"}
MOD_LABEL = {"text": "Text", "image": "Images", "audio": "Audio", "video": "Video", "pdf": "PDF"}


def current_models():
    return [m for m in MODELS if m["status"] != "legacy"]


# ---------------------------------------------------------------- markup helpers

EXT_LINK_RE = re.compile(r'<a\s+href="(https?://[^"]+)"(?![^>]*\brel=)([^>]*)>')


def externalize(body):
    """Add target and rel to external links that don't already declare rel."""
    def rep(m):
        url, rest = m.group(1), m.group(2)
        if "llmodel.com" in url:
            return m.group(0)
        return f'<a href="{url}" target="_blank" rel="noopener"{rest}>'
    return EXT_LINK_RE.sub(rep, body)


def wrap_tables(body):
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    return re.sub(r"</table>", "</table></div>", body)


def h2_list(body):
    return [(i, re.sub(r"<[^>]+>", "", t)) for i, t in re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', body, re.S)]


def text_words(body):
    return len(re.sub(r"<[^>]+>", " ", body).split())


ICONS = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "moon": '<svg class="theme-icon-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "sun": '<svg class="theme-icon-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>',
    "coins": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><ellipse cx="9" cy="7" rx="6" ry="3"/><path d="M3 7v5c0 1.7 2.7 3 6 3s6-1.3 6-3V7"/><path d="M9 15v2c0 1.7 2.7 3 6 3s6-1.3 6-3v-5c0-1.7-2.7-3-6-3"/></svg>',
    "tokens": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="2.5" y="7" width="6" height="10" rx="2"/><rect x="9.5" y="7" width="5" height="10" rx="2"/><rect x="15.5" y="7" width="6" height="10" rx="2"/></svg>',
    "chip": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg>',
    "compass": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/></svg>',
    "window": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 9h19M7 13h6"/></svg>',
    "pen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/></svg>',
    "scale": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 21h14M6 7h12"/><path d="m6 7-3 6a3 3 0 0 0 6 0zM18 7l-3 6a3 3 0 0 0 6 0z"/></svg>',
}

TOOLS = [
    {"slug": "llm-cost-calculator", "name": "LLM API cost calculator", "icon": "coins",
     "desc": "Price a workload across every model with a published rate. Set tokens, requests and caching; get a ranked monthly bill."},
    {"slug": "token-counter", "name": "Token counter", "icon": "tokens",
     "desc": "Paste text to estimate tokens, see how it splits, get an exact count with OpenAI's tokenizer and price it per model."},
    {"slug": "vram-calculator", "name": "GPU and VRAM calculator", "icon": "chip",
     "desc": "Work out the memory an open-weight model needs at each precision, including the KV cache, and which GPUs or Macs fit it."},
    {"slug": "llm-picker", "name": "Which LLM should I use?", "icon": "compass",
     "desc": "Answer five questions about your task, budget and deployment. Get a shortlist of three models with the reasons."},
    {"slug": "context-window-visualizer", "name": "Context window visualizer", "icon": "window",
     "desc": "See what 8K, 128K or 1M tokens hold in pages, books, code and meeting hours, and compare model limits."},
    {"slug": "prompt-builder", "name": "Prompt builder", "icon": "pen",
     "desc": "Assemble a structured prompt from role, task, context, format and constraints. Copy it or download it."},
    {"slug": "self-host-vs-api-calculator", "name": "Self-host vs API calculator", "icon": "scale",
     "desc": "Find the monthly volume where renting GPUs beats paying per token, with your own prices and throughput."},
]
TOOL_BY = {t["slug"]: t for t in TOOLS}

HOUSE_PROMOS = [
    ("Building with LLMs?", "Tell us what you're building and get a vendor-neutral stack plan within 2 business days.", "hire-llm-experts.html", "Get my stack plan"),
    ("The LLM Brief", "One short email a week: new models, price changes and one tool worth trying.", "newsletter.html", "Subscribe free"),
    ("Price your workload", "Compare the monthly bill for your token volume across every priced model.", "llm-cost-calculator.html", "Open the calculator"),
    ("Selling to LLM builders?", "List your model, API or tool where teams compare their options.", "list-your-product.html", "See listing options"),
    ("Keep LLModel independent", "Reader support pays for data checks, new tools and contest prizes.", "support.html", "Support the site"),
    ("Prompt Efficiency Challenge", "Season 1 is open: solve five tasks for the fewest dollars. $500 in prizes.", "contests.html", "Read the brief"),
]


def ad_slot(name, ads=True, promo=0):
    if not ads:
        return ""
    title, desc, href, cta = HOUSE_PROMOS[promo % len(HOUSE_PROMOS)]
    return (f'<aside class="ad-slot" data-ad="{esc(name)}" aria-label="Sponsored message">'
            f'<span class="ad-label">From LLModel</span><div class="ad-fill">'
            f'<div class="house"><div><strong>{esc(title)}</strong><span>{esc(desc)}</span></div>'
            f'<a class="btn btn--ghost btn--sm" href="{href}">{esc(cta)}</a></div></div></aside>')


NEEDS = [
    ("choose-model", "Choose the right model"),
    ("chatbot", "Build a chatbot or assistant"),
    ("rag", "Answer questions over our documents (RAG)"),
    ("agents", "Automate work with AI agents"),
    ("self-host", "Fine-tune or self-host a model"),
    ("cut-costs", "Cut our LLM costs"),
    ("security", "Security, privacy or compliance review"),
    ("not-sure", "Not sure yet"),
]

LEAD_COPY = {
    "default": ("Building with LLMs? Get a vendor-neutral plan.",
                "Tell us what you're building. Within 2 business days you get a model shortlist, an architecture outline and a cost estimate, plus optional introductions to vetted implementation partners."),
    "costs": ("Spending real money on tokens?",
              "Share your workload and current bill. We'll point out routing, caching and model swaps that cut cost without hurting quality."),
    "local": ("Planning to self-host?",
              "Get a second opinion on hardware, serving stack and break-even before you buy or rent GPUs."),
    "choose": ("Still choosing a model?",
               "Send us your use case and constraints. We'll come back with a shortlist and an evaluation plan you can run on your own data."),
    "build": ("Need hands-on help building it?",
              "RAG, agents, fine-tuning or a production chatbot: describe the project and we'll suggest an approach and, if you want, partners who build it."),
}


def lead_band(variant="default", need="", src=""):
    title, text = LEAD_COPY.get(variant, LEAD_COPY["default"])
    opts = "".join(f'<option value="{k}"{" selected" if k == need else ""}>{esc(v)}</option>' for k, v in NEEDS)
    return f'''<section class="lead-band" aria-labelledby="lead-{esc(variant)}-{esc(src or 'x')}">
  <div>
    <h2 id="lead-{esc(variant)}-{esc(src or 'x')}">{esc(title)}</h2>
    <p>{esc(text)}</p>
    <ul><li>Free and vendor-neutral: no model provider pays for placement.</li><li>Your details go only to partners you agree to.</li></ul>
  </div>
  <form class="mini-form" action="hire-llm-experts.html" method="get">
    <label for="need-{esc(variant)}-{esc(src or 'x')}">What do you need help with?</label>
    <select id="need-{esc(variant)}-{esc(src or 'x')}" name="need">{opts}</select>
    <input type="hidden" name="from" value="{esc(src)}">
    <button class="btn btn--yellow btn--block" type="submit">Start my free plan</button>
    <p class="fine">Takes about 2 minutes. No sales calls unless you ask for one.</p>
  </form>
</section>'''


def honeypot():
    return '<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'


def newsletter_box(uid="nl", heading="The LLM Brief", compact=False):
    head = "" if compact else f'<h2 class="h3">{esc(heading)}</h2>'
    return f'''<div class="panel newsletter-box">
  {head}
  <p class="muted" style="margin-top:.4rem">One short email a week: model releases, price changes and one tool worth trying. Free, and you can unsubscribe anytime.</p>
  <form class="form" data-form="newsletter" data-subject="Newsletter signup" novalidate style="margin-top:1rem">
    <div class="inline-form">
      <label class="visually-hidden" for="{uid}-email">Email address</label>
      <input class="input" type="email" id="{uid}-email" name="email" required autocomplete="email" placeholder="Your work email">
      <button class="btn btn--primary" type="submit">Subscribe</button>
    </div>
    {honeypot()}
    <div class="form-status" role="status" aria-live="polite"></div>
  </form>
  <p class="fine" style="margin-top:.6rem">We send one email a week and never sell your address. See the <a href="privacy.html">privacy policy</a>.</p>
</div>'''


def faq_html(items, heading="Frequently asked questions", hid="faq"):
    if not items:
        return ""
    rows = "".join(
        f'<details><summary>{esc(i["q"])}</summary><div class="faq__a"><p>{esc(i["a"])}</p></div></details>'
        for i in items)
    return f'<section class="faq-wrap" aria-labelledby="{hid}"><h2 class="h2" id="{hid}" style="margin-bottom:1rem">{esc(heading)}</h2><div class="faq">{rows}</div></section>'


def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": i["q"], "acceptedAnswer": {"@type": "Answer", "text": i["a"]}} for i in items]}


def video_embed(v):
    vid = esc(v["id"])
    return (f'<div class="video" data-yt="{vid}"><button class="video__btn" type="button" aria-label="Play video: {esc(v["title"])}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
            f'<span class="video__play">{ICONS["play"]}</span></button></div>')


def video_card(v, heading_level=3, show_takeaways=True):
    meta = [esc(v["channel"])]
    if v.get("duration"):
        meta.append(esc(v["duration"]))
    meta.append(esc(v["level"]))
    tk = ""
    if show_takeaways and v.get("takeaways"):
        tk = "<ul>" + "".join(f"<li>{esc(t)}</li>" for t in v["takeaways"]) + "</ul>"
    return (f'<article class="video-card" id="v-{esc(v["id"])}">{video_embed(v)}'
            f'<h{heading_level}>{esc(v["title"])}</h{heading_level}>'
            f'<div class="vc-meta">' + "".join(f"<span>{x}</span>" for x in meta) +
            f'<a href="https://www.youtube.com/watch?v={esc(v["id"])}" target="_blank" rel="noopener">Watch on YouTube</a></div>'
            f'<p class="muted small">{esc(v["summary"])}</p>{tk}</article>')


def badge_status(m):
    return f'<span class="badge badge--{m["status"]}">{STATUS_LABEL[m["status"]]}</span>'


def badge_weights(m):
    return ('<span class="badge badge--open">Open weights</span>' if m["weights"] == "open"
            else '<span class="badge badge--closed">Closed</span>')


def tier_tag(m):
    v = {"frontier": "0", "advanced": "4", "efficient": "6", "compact": "9"}[m["tier"]]
    return f'<span class="tag" data-v="{v}">{TIER_LABEL[m["tier"]]}</span>'


def model_link(m):
    return f'<a href="{m["url_page"]}">{esc(m["name"])}</a>'


def breadcrumbs(crumbs):
    if not crumbs:
        return ""
    items = []
    for i, (name, href) in enumerate(crumbs):
        if href and i < len(crumbs) - 1:
            items.append(f'<li><a href="{href}">{esc(name)}</a></li>')
        else:
            items.append(f'<li aria-current="page">{esc(name)}</li>')
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>'


def crumbs_schema(crumbs):
    out = []
    for i, (name, href) in enumerate(crumbs, 1):
        url = SITE["site_url"] + "/" + (href if href and href != "index.html" else "")
        if not href:
            url = None
        item = {"@type": "ListItem", "position": i, "name": name}
        if url:
            item["item"] = url
        out.append(item)
    return {"@type": "BreadcrumbList", "itemListElement": out}


# ---------------------------------------------------------------- layout

NAV = [
    ("Models", "models.html", "models"),
    ("Compare", "compare.html", "compare"),
    ("Rankings", "leaderboard.html", "rankings"),
    ("Tools", "tools.html", "tools"),
    ("Learn", "guides.html", "learn"),
    ("Videos", "videos.html", "videos"),
]

MOBILE_NAV = [
    ("Models", "models.html"), ("Providers", "providers.html"), ("Compare", "compare.html"),
    ("Rankings", "leaderboard.html"), ("Tools", "tools.html"), ("Guides", "guides.html"),
    ("Glossary", "glossary.html"), ("Videos", "videos.html"), ("Prompt library", "prompts.html"),
    ("Resources", "resources.html"), ("LLM timeline", "llm-timeline.html"), ("Newsletter", "newsletter.html"),
    ("Advertise", "advertise.html"), ("Support us", "support.html"), ("Contests", "contests.html"),
    ("Contact", "contact.html"),
]

FOOTER_COLS = [
    ("Explore", [("Model directory", "models.html"), ("Providers", "providers.html"), ("Compare models", "compare.html"),
                 ("Rankings", "leaderboard.html"), ("LLM timeline", "llm-timeline.html"), ("Search", "search.html")]),
    ("Tools", [(t["name"].replace("LLM API cost calculator", "Cost calculator"), t["slug"] + ".html") for t in TOOLS]),
    ("Learn", [("Guides", "guides.html"), ("Glossary", "glossary.html"), ("Videos", "videos.html"),
               ("Prompt library", "prompts.html"), ("Resources", "resources.html"), ("Newsletter", "newsletter.html")]),
    ("Work with us", [("Get expert help", "hire-llm-experts.html"), ("List your product", "list-your-product.html"),
                      ("Advertise", "advertise.html"), ("Support us", "support.html"), ("Contests", "contests.html"),
                      ("Careers", "careers.html"), ("Contact", "contact.html")]),
    ("About", [("About LLModel", "about.html"), ("Editorial policy", "editorial-policy.html"), ("Privacy policy", "privacy.html"),
               ("Terms of use", "terms.html"), ("Disclaimer", "disclaimer.html"), ("Trademark and copyright", "trademark-copyright.html"),
               ("Site map", "sitemap.html")]),
]

ASSET_V = {}


def asset(path):
    v = ASSET_V.get(path)
    if v is None:
        p = ROOT / path
        v = file_hash(p) if p.exists() else UPDATED
        ASSET_V[path] = v
    return f"{path}?v={v}"


THEME_INIT = ("(function(){var d=document.documentElement,t=null;try{t=localStorage.getItem('llm-theme')}catch(e){}"
              "if(t!=='light'&&t!=='dark'){t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}"
              "d.setAttribute('data-theme',t)})();")


def header_html(section):
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{current if key == section else ""}>{name}</a>' for name, href, key in NAV)
    mob = "".join(f'<li><a href="{h}">{esc(n)}</a></li>' for n, h in MOBILE_NAV)
    return f'''<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html" aria-label="LLModel.com home"><span class="tok tok--a">LL</span><span class="tok tok--b">Model</span></a>
    <nav class="nav" aria-label="Main">{nav}</nav>
    <div class="header-actions">
      <button class="search-btn" type="button" data-open-search aria-label="Search the site">{ICONS["search"]}<span class="search-label">Search</span><span class="kbd" aria-hidden="true">/</span></button>
      <button class="icon-btn" type="button" data-theme-toggle aria-label="Switch between light and dark theme">{ICONS["moon"]}{ICONS["sun"]}</button>
      <a class="btn btn--primary btn--sm header-cta" href="hire-llm-experts.html">Get expert help</a>
      <button class="icon-btn menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="Open menu">{ICONS["menu"]}</button>
    </div>
  </div>
  <nav class="mobile-nav" id="mobile-nav" aria-label="Mobile">
    <ul>{mob}<li class="mobile-cta"><a class="btn btn--primary btn--block" href="hire-llm-experts.html">Get expert help</a></li></ul>
  </nav>
</header>'''


def footer_html():
    cols = ""
    for title, links in FOOTER_COLS:
        items = "".join(f'<li><a href="{h}">{esc(n)}</a></li>' for n, h in links)
        if title == "About":
            items += '<li><button class="linklike" type="button" data-privacy-choices>Privacy and cookie choices</button></li>'
        cols += f'<div><h2>{esc(title)}</h2><ul>{items}</ul></div>'
    return f'''<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-about">
      <a class="brand" href="index.html" aria-label="LLModel.com home"><span class="tok tok--a">LL</span><span class="tok tok--b">Model</span></a>
      <p>{esc(SITE["tagline"])}. Model data checked against provider documentation; last full check {esc(SITE["updated_human"])}.</p>
    </div>
    {cols}
  </div>
  <div class="wrap footer-legal">
    <p>&copy; {SITE["year"]} LLModel.com. Independent: not affiliated with, endorsed by or sponsored by any model provider. Model and company names are trademarks of their respective owners and are used only to identify products. See <a href="trademark-copyright.html">trademark and copyright</a>.</p>
    <p>Prices and specifications change often. Always confirm on the provider's own pricing page before you buy.</p>
  </div>
</footer>'''


PALETTE = '''<div class="palette" id="palette" hidden role="dialog" aria-modal="true" aria-label="Search LLModel">
  <div class="palette__box">
    <label class="visually-hidden" for="palette-input">Search models, tools, guides and terms</label>
    <input class="palette__input" id="palette-input" type="search" placeholder="Search models, tools, guides, terms" autocomplete="off" spellcheck="false" aria-controls="palette-list">
    <ul class="palette__list" id="palette-list" role="listbox"></ul>
    <div class="palette__foot"><span><span class="kbd">&uarr;</span> <span class="kbd">&darr;</span> to move</span><span><span class="kbd">Enter</span> to open</span><span><span class="kbd">Esc</span> to close</span></div>
  </div>
</div>'''


def org_schema():
    return {"@type": "Organization", "@id": SITE["site_url"] + "/#org", "name": "LLModel.com",
            "url": SITE["site_url"] + "/", "logo": SITE["site_url"] + "/assets/img/icon-512.png"}


BLOCK_END_RE = re.compile(r"(</(?:tr|li|dt|dd|details|article|section|table|thead|tbody|ul|ol|div|p|h2|h3|figure|aside|nav|header|footer|form|fieldset|option|optgroup)>)(?!\n)")


def tidy_lines(doc):
    """Put block-level closing tags on their own line (outside <pre>) so no line gets very long,
    and drop trailing spaces. Whitespace between block elements doesn't change rendering."""
    parts = re.split(r"(<pre[\s>].*?</pre>|<script[\s>].*?</script>|<style[\s>].*?</style>|<textarea[\s>].*?</textarea>)", doc, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = wrap_text(BLOCK_END_RE.sub(r"\1\n", parts[i]))
    return "\n".join(line.rstrip() for line in "".join(parts).split("\n"))


def ld_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1)


def wrap_text(seg, width=900):
    """Turn a space in running text into a newline once a line passes `width` characters.
    Only spaces outside tags are touched, which HTML renders identically."""
    out, in_tag, run = [], False, 0
    for ch in seg:
        if ch == "\n":
            run = 0
            out.append(ch)
            continue
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        if ch == " " and not in_tag and run > width:
            out.append("\n")
            run = 0
            continue
        out.append(ch)
        run += 1
    return "".join(out)


def page_html(meta, content):
    """Wrap page content in the full document."""
    return tidy_lines(glossary_links(_page_html(meta, content)))


def _page_html(meta, content):
    slug = meta["slug"]
    href = "index.html" if slug == "index" else f"{slug}.html"
    canonical = SITE["site_url"] + "/" + ("" if slug == "index" else href)
    title = meta["title"]
    if "LLModel" not in title:
        title = f"{title} | LLModel.com"
    desc = meta["description"]
    adsense = meta.get("adsense", True)
    noindex = meta.get("noindex", False)
    og_type = meta.get("og_type", "website")
    section = meta.get("section", "")
    schema = [org_schema()]
    if meta.get("crumbs") and slug != "index":
        schema.append(crumbs_schema(meta["crumbs"]))
    schema.extend(meta.get("schema", []))
    for s in schema:
        s.setdefault("@context", "https://schema.org")
    ld = "\n".join(f'<script type="application/ld+json">{ld_json(s)}</script>' for s in schema)
    ads_tag = ""
    if adsense:
        ads_tag = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={SITE["adsense_client"]}" '
                   f'crossorigin="anonymous"></script>')
    data_js = "".join(f'<script src="{asset("assets/js/data/" + d + ".js")}"></script>' for d in meta.get("data", []))
    page_js = "".join(f'<script src="{asset("assets/js/" + s)}" defer></script>' for s in meta.get("scripts", []))
    robots = "noindex,follow" if noindex else "index,follow,max-image-preview:large,max-snippet:-1"
    extra_head = meta.get("head", "")
    body_class = f"page-{slug}" + (" " + meta["body_class"] if meta.get("body_class") else "")
    crumbs = breadcrumbs(meta.get("crumbs")) if slug != "index" else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta name="google-adsense-account" content="{SITE["adsense_client"]}">
<meta name="theme-color" content="#f4f6fb" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12101e" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="LLModel.com">
<meta property="og:title" content="{esc(meta.get("og_title", meta["title"]))}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE["site_url"]}/assets/img/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="LLModel: the independent field guide to large language models">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<link rel="alternate" type="text/plain" href="llms.txt" title="llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{SITE["fonts"]}">
<link rel="stylesheet" href="{asset("assets/css/style.css")}">
<script>{THEME_INIT}</script>
{ads_tag}
{ld}
{extra_head}
</head>
<body class="{esc(body_class)}">
<a class="skip" href="#main">Skip to content</a>
<div class="partner-bar"><a href="{SITE["partner_url"]}" target="_blank" rel="noopener"><span>{esc(SITE["partner_text"])}</span></a></div>
{header_html(section)}
<main id="main">
{crumbs}
{content}
</main>
{footer_html()}
{PALETTE}
<script src="{asset("assets/js/config.js")}"></script>
{data_js}
<script src="{asset("assets/js/app.js")}" defer></script>
{page_js}
</body>
</html>
'''


def page_head(h1, lede="", meta_items=None, extra=""):
    mi = ""
    if meta_items:
        mi = '<div class="page-meta">' + "".join(f"<span>{x}</span>" for x in meta_items) + "</div>"
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return f'<header class="page-head wrap"><h1>{h1}</h1>{lede_html}{mi}{extra}</header>'


def section(inner, cls="", wrap=True, aria=None, sid=None):
    a = f' aria-labelledby="{aria}"' if aria else ""
    i = f' id="{sid}"' if sid else ""
    w_open, w_close = ('<div class="wrap">', "</div>") if wrap else ("", "")
    return f'<section class="section {cls}"{a}{i}>{w_open}{inner}{w_close}</section>'


def section_head(title, sub="", more=None, hid=None):
    hid = hid or slugify(title)
    more_html = f'<a class="more" href="{more[1]}">{esc(more[0])}</a>' if more else ""
    sub_html = f"<p>{sub}</p>" if sub else ""
    return f'<div class="section-head"><div><h2 id="{hid}">{esc(title)}</h2>{sub_html}</div>{more_html}</div>'
