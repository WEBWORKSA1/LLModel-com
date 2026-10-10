"""Content pages: guides, guides hub, glossary, videos, prompts, resources, timeline, search index, sitemaps."""
import json
import re
from collections import OrderedDict
from .common import (SITE, UPDATED, GUIDES, GUIDE_BY, GLOSSARY, GLOSS_BY, GLOSSARY_TOPICS, glossary_href,
                     VIDEOS, PROMPTS, RESOURCES, TIMELINE, MODELS,
                     PROVIDERS, TOOLS, TOOL_BY, esc, fmt_date, slugify, externalize, wrap_tables, h2_list, ad_slot,
                     lead_band, faq_html, faq_schema, page_head, section_head, video_embed, video_card, newsletter_box, fmt_price, fmt_tokens)
from .datapages import timeline_html, TL_COLORS, TL_LABEL, HUBS, COMPARISONS, cmp_slug, MODEL_BY

GUIDE_CATS = ["Fundamentals", "Choosing & buying", "Building", "Running & deploying", "Safety & quality"]
LEAD_FOR_CAT = {"Fundamentals": "choose", "Choosing & buying": "choose", "Building": "build",
                "Running & deploying": "local", "Safety & quality": "build"}


def videos_for_guide(slug):
    return [v for v in VIDEOS if v.get("guide") == slug]


def guide_page(g):
    body = g["body"]
    heads = h2_list(body)
    # insert ads before the 3rd and 7th h2, and the best video before the 5th
    h2_positions = [m.start() for m in re.finditer(r"<h2 ", body)]
    inserts = []
    if len(h2_positions) >= 3:
        inserts.append((h2_positions[2], ad_slot("in-article", promo=sum(map(ord, g["slug"])) % 6)))
    vids = videos_for_guide(g["slug"])
    if vids and len(h2_positions) >= 5:
        v = vids[0]
        fig = (f'<figure class="video-figure">{video_embed(v)}<figcaption>Watch: {esc(v["title"])} ({esc(v["channel"])}). '
               f'{esc(v["summary"])}</figcaption></figure>')
        inserts.append((h2_positions[4], fig))
    if len(h2_positions) >= 7:
        inserts.append((h2_positions[6], ad_slot("in-article-2", promo=(sum(map(ord, g["slug"])) + 1) % 6)))
    for pos, html_ in sorted(inserts, key=lambda x: -x[0]):
        body = body[:pos] + html_ + "\n" + body[pos:]
    body = wrap_tables(externalize(body))

    toc = "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in heads)
    take = "".join(f"<li>{esc(t)}</li>" for t in g.get("key_takeaways", []))
    srcs = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></li>' for s in g.get("sources", []))
    url = f'{SITE["site_url"]}/{g["slug"]}.html'
    share = (f'<div class="share" aria-label="Share this guide"><span class="muted">Share:</span>'
             f'<button type="button" data-copy-link>Copy link</button>'
             f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={esc(url)}" target="_blank" rel="noopener">LinkedIn</a>'
             f'<a href="https://twitter.com/intent/tweet?url={esc(url)}&amp;text={esc(g["h1"])}" target="_blank" rel="noopener">X</a>'
             f'<a href="https://news.ycombinator.com/submitlink?u={esc(url)}&amp;t={esc(g["h1"])}" target="_blank" rel="noopener">Hacker News</a>'
             f'<a href="https://www.reddit.com/submit?url={esc(url)}&amp;title={esc(g["h1"])}" target="_blank" rel="noopener">Reddit</a></div>')
    tools = [TOOL_BY[t] for t in g.get("related_tools", []) if t in TOOL_BY]
    tools_html = "".join(f'<li><a href="{t["slug"]}.html">{esc(t["name"])}</a></li>' for t in tools)
    side = (f'<aside class="article__side" aria-label="Related">'
            f'<div class="panel"><h2 class="h3">Try the tools</h2><ul style="margin:.5rem 0 0;padding-left:1.1rem">{tools_html}</ul></div>'
            f'<div class="panel"><h2 class="h3">Need hands-on help?</h2><p class="small muted" style="margin-top:.4rem">Get a vendor-neutral plan for your project within 2 business days.</p>'
            f'<a class="btn btn--primary btn--block" style="margin-top:.8rem" href="hire-llm-experts.html?from=guide-{esc(g["slug"])}">Get expert help</a></div>'
            f'{newsletter_box("nl-side", compact=True)}</aside>')
    rel = [GUIDE_BY[s] for s in g.get("related_guides", []) if s in GUIDE_BY][:3]
    rel_html = "".join(
        f'<a class="card" href="{r["slug"]}.html"><span class="card__kicker">{esc(r["category"])}</span><span class="card__title">{esc(r["h1"])}</span>'
        f'<span class="card__desc">{esc(r["summary"])}</span><span class="card__foot"><span>{esc(r["level"])}</span><span>{r["minutes"]} min read</span></span></a>' for r in rel)
    more_vids = ""
    if len(vids) > 1:
        more_vids = ('<section class="wrap" aria-labelledby="more-videos" style="margin-top:3rem"><h2 class="h2" id="more-videos" style="margin-bottom:1rem">More videos on this topic</h2>'
                     '<div class="grid grid--3">' + "".join(video_card(v, show_takeaways=False) for v in vids[1:4]) + "</div></section>")
    content = f'''<div class="read-progress" id="read-progress" aria-hidden="true"></div>
{page_head(esc(g["h1"]), esc(g["summary"]), [esc(g["category"]), esc(g["level"]), f'{g["minutes"]} min read', f'Updated {fmt_date(g["updated"], True)}'])}
<div class="wrap article">
  <nav class="article__toc toc" aria-label="On this page"><p class="toc-title">On this page</p><ol>{toc}</ol></nav>
  <article class="prose" id="article">
    <div class="takeaways"><h2>Key takeaways</h2><ul>{take}</ul></div>
    {body}
    <section class="sources" aria-labelledby="sources"><h2 id="sources">Sources</h2><ol>{srcs}</ol>
      <p class="small muted">Written by the LLModel editorial team and checked against the sources above on {fmt_date(g["updated"], True)}. Found an error? <a href="contact.html?topic=correction">Send a correction</a>.</p></section>
    {share}
  </article>
  {side}
</div>
<div class="wrap wrap--read" style="margin-top:3rem">{faq_html(g.get("faq", []))}</div>
{more_vids}
<section class="wrap" aria-labelledby="related" style="margin-top:3rem"><h2 class="h2" id="related" style="margin-bottom:1rem">Keep reading</h2><div class="cardlist">{rel_html}</div></section>
<div class="wrap">{lead_band(LEAD_FOR_CAT.get(g["category"], "default"), "", "guide-" + g["slug"])}</div>'''
    schema = [{"@type": "Article", "headline": g["title"][:110], "description": g["description"], "datePublished": g["updated"],
               "dateModified": g["updated"], "inLanguage": "en", "mainEntityOfPage": url, "image": SITE["site_url"] + "/assets/img/og-image.png",
               "author": {"@type": "Organization", "name": "LLModel editorial team", "url": SITE["site_url"] + "/about.html"},
               "publisher": {"@id": SITE["site_url"] + "/#org"}, "keywords": ", ".join(g.get("keywords", []))}]
    if g.get("faq"):
        schema.append(faq_schema(g["faq"]))
    meta = {"slug": g["slug"], "title": g["title"], "description": g["description"], "section": "learn", "og_type": "article",
            "crumbs": [("Home", "index.html"), ("Guides", "guides.html"), (g["h1"], None)], "schema": schema, "priority": 0.8,
            "scripts": ["article.js"]}
    return meta, content


def guide_card(g):
    return (f'<a class="card" href="{g["slug"]}.html"><span class="card__kicker">{esc(g["category"])}</span><span class="card__title">{esc(g["h1"])}</span>'
            f'<span class="card__desc">{esc(g["summary"])}</span><span class="card__foot"><span>{esc(g["level"])}</span><span>{g["minutes"]} min read</span></span></a>')


def guides_featured(n=6):
    order = ["what-is-a-large-language-model", "how-to-choose-an-llm", "llm-api-pricing-explained", "run-llms-locally",
             "rag-explained", "prompt-engineering-guide", "ai-agents-explained", "llm-hallucinations"]
    gs = [GUIDE_BY[s] for s in order if s in GUIDE_BY][:n]
    return '<div class="cardlist">' + "".join(guide_card(g) for g in gs) + "</div>"


def guides_hub():
    total_words = sum(g["words"] for g in GUIDES)
    out = ""
    for cat in GUIDE_CATS:
        gs = [g for g in GUIDES if g["category"] == cat]
        if not gs:
            continue
        out += (f'<section class="section" aria-labelledby="cat-{slugify(cat)}"><div class="wrap"><div class="section-head"><div><h2 id="cat-{slugify(cat)}">{esc(cat)}</h2></div></div>'
                f'<div class="cardlist">' + "".join(guide_card(g) for g in gs) + "</div></div></section>")
    content = (page_head("Learn how large language models work", f"{len(GUIDES)} in-depth guides, about {total_words // 1000}K words in all, written in plain English and checked against primary sources. Start with the fundamentals or jump to what you're building.",
                         [f"Updated {fmt_date(UPDATED, True)}", '<a href="glossary.html">Glossary</a>', '<a href="videos.html">Videos</a>']) +
               out + f'<div class="wrap">{ad_slot("guides-hub", promo=1)}{lead_band("default", "", "guides")}</div>')
    meta = {"slug": "guides", "title": "LLM Guides: How Large Language Models Work, Cost and Fail",
            "description": f"{len(GUIDES)} plain-English guides to large language models: how they work, how to choose one, pricing, RAG, agents, running models locally, security and more.",
            "section": "learn", "crumbs": [("Home", "index.html"), ("Guides", None)], "priority": 0.9,
            "schema": [{"@type": "CollectionPage", "name": "LLM guides", "hasPart": [{"@type": "Article", "headline": g["h1"], "url": f'{SITE["site_url"]}/{g["slug"]}.html'} for g in GUIDES]}]}
    return meta, content


# ---------------------------------------------------------------- glossary

def _term_entry(t, here=None):
    """A glossary entry. On a topic page (here = that topic's category) it carries the full definition and related
    terms; on the hub it is a compact line linking to the topic page."""
    aka = f'<span class="aka">{esc(", ".join(t["aka"]))}</span>' if t.get("aka") else ""
    text = esc(" ".join([t["term"]] + t.get("aka", [])).lower())
    head = f'<article class="term" id="{esc(t["slug"])}" data-cat="{esc(t["category"])}" data-text="{text}">'
    if here is None:
        topic = next(d for c, _, d, *_ in GLOSSARY_TOPICS if c == t["category"])
        return (head + f'<h3><a href="{glossary_href(t["slug"])}">{esc(t["term"])}</a> {aka}</h3>'
                f'<p class="def">{esc(t["short"])}</p><p class="small muted">{esc(topic)}</p></article>')
    rel = ""
    if t.get("related"):
        links = []
        for r in t["related"]:
            if r in GLOSS_BY:
                href = f"#{r}" if GLOSS_BY[r]["category"] == here else glossary_href(r)
                links.append(f'<a class="tag" href="{href}">{esc(GLOSS_BY[r]["term"])}</a>')
        rel = '<div class="rel tags">' + "".join(links) + "</div>"
    return (head + f'<h3>{esc(t["term"])} {aka}<a class="anchor" href="#{esc(t["slug"])}" aria-label="Link to {esc(t["term"])}">#</a></h3>'
            f'<p class="short">{esc(t["short"])}</p><p class="def">{esc(t["definition"])}</p>{rel}</article>')


def _topic_name(display):
    return display[0].lower() + display[1:]


def glossary_pages():
    """The glossary hub (every term A to Z, with short definitions) plus one page per topic with the full entries."""
    pages = []
    total = len(GLOSSARY)
    terms = sorted(GLOSSARY, key=lambda t: t["term"].lower())
    letters = OrderedDict()
    for t in terms:
        L = t["term"][0].upper()
        letters.setdefault(L if L.isalpha() else "#", []).append(t)
    az = "".join(f'<a href="#letter-{"num" if L == "#" else L}">{esc(L)}</a>' for L in letters)
    chips = "".join(f'<button type="button" class="chip-toggle" data-cat="{esc(c)}" aria-pressed="false">{esc(d)}</button>'
                    for c, _, d, *_ in GLOSSARY_TOPICS)
    counts = {c: sum(1 for t in GLOSSARY if t["category"] == c) for c, *_ in GLOSSARY_TOPICS}
    cards = "".join(f'<a class="card" href="glossary-{s}.html"><span class="card__kicker">{counts[c]} terms</span>'
                    f'<span class="card__title">{esc(d)}</span><span class="card__desc">{esc(intro)}</span></a>'
                    for c, s, d, intro, _ in GLOSSARY_TOPICS)
    blocks = "".join(f'<h2 class="letter" id="letter-{"num" if L == "#" else L}">{esc(L)}</h2><div class="terms">' +
                     "".join(_term_entry(t) for t in ts) + "</div>" for L, ts in letters.items())
    content = (page_head("LLM glossary", f"{total} large-language-model terms explained in plain English, from attention to zero data retention. "
                         "Browse by topic for full definitions, or filter the A to Z list.",
                         [f"Updated {fmt_date(UPDATED, True)}", '<a href="guides.html">Guides</a>']) +
               f'''<div class="wrap">
{section_head("Browse by topic", "Each topic page gives every term a short definition, a fuller explanation and links to related terms.", hid="topics")}
<div class="grid grid--3">{cards}</div>
<div style="margin-top:3rem">{section_head("Every term, A to Z", hid="a-z")}</div>
<div class="filters"><div class="filters__top"><label class="visually-hidden" for="gl-q">Filter terms</label><input class="input" id="gl-q" type="search" placeholder="Filter {total} terms" autocomplete="off"></div>
<div class="tags" role="group" aria-label="Topic">{chips}</div><p class="result-count" id="gl-count" aria-live="polite">{total} terms</p></div>
<nav class="az" aria-label="Jump to letter">{az}</nav>
{ad_slot("glossary-top", promo=2)}
<div id="gl-list">{blocks}</div>
<p class="empty" id="gl-empty" hidden>No terms match that filter. Try a shorter word.</p>
{lead_band("default", "", "glossary")}
</div>''')
    schema = [{"@type": "CollectionPage", "name": "LLM glossary", "url": SITE["site_url"] + "/glossary.html",
               "hasPart": [{"@type": "DefinedTermSet", "name": f"LLM glossary: {_topic_name(d)}", "url": f'{SITE["site_url"]}/glossary-{s}.html'}
                           for c, s, d, *_ in GLOSSARY_TOPICS]}]
    pages.append(({"slug": "glossary", "title": f"LLM Glossary: {total} AI and Large Language Model Terms Explained",
                   "description": f"Plain-English definitions of {total} large language model terms: tokens, context windows, RAG, quantization, KV cache, reasoning models, MCP and more.",
                   "section": "learn", "crumbs": [("Home", "index.html"), ("Glossary", None)], "schema": schema, "priority": 0.8,
                   "search_type": "Glossary", "scripts": ["pages/glossary.js"]}, content))

    for i, (cat, s, display, intro, examples) in enumerate(GLOSSARY_TOPICS):
        ts = [t for t in terms if t["category"] == cat]
        others = '<nav class="pill-nav" aria-label="Other glossary topics">' + "".join(
            f'<a href="glossary-{s2}.html">{esc(d2)}</a>' for c2, s2, d2, *_ in GLOSSARY_TOPICS if s2 != s) + "</nav>"
        entries = [_term_entry(t, here=cat) for t in ts]
        if len(entries) > 16:
            entries.insert(10, ad_slot("in-article-2", promo=(i + 3) % 6))
        name = _topic_name(display)
        h1 = f"LLM glossary: {name}"
        content = (page_head(h1, f"{intro} {len(ts)} terms, each with a short definition, a fuller explanation and links to related terms.",
                             [f"Updated {fmt_date(UPDATED, True)}", f'<a href="glossary.html">All {total} terms</a>']) +
                   f'''<div class="wrap">
{others}
<div class="filters" style="margin-top:1.5rem"><div class="filters__top"><label class="visually-hidden" for="gl-q">Filter terms</label><input class="input" id="gl-q" type="search" placeholder="Filter {len(ts)} terms" autocomplete="off"></div>
<p class="result-count" id="gl-count" aria-live="polite">{len(ts)} terms</p></div>
{ad_slot("glossary-top", promo=i % 6)}
<div id="gl-list"><div class="terms">{"".join(entries)}</div></div>
<p class="empty" id="gl-empty" hidden>No terms on this page match that filter. Try a shorter word, or filter <a href="glossary.html">all {total} terms</a>.</p>
{lead_band("default", "", "glossary")}
</div>''')
        url = f'{SITE["site_url"]}/glossary-{s}.html'
        schema = [{"@type": "DefinedTermSet", "name": h1, "url": url,
                   "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["term"], "description": t["short"], "url": f'{url}#{t["slug"]}'} for t in ts]}]
        title_name = " ".join(w if w in ("and", "LLM") else w[:1].upper() + w[1:] for w in display.split())
        pages.append(({"slug": f"glossary-{s}", "title": f"{title_name} Terms: LLM Glossary ({len(ts)} Definitions)",
                       "description": f"Plain-English definitions of {len(ts)} {name} terms for large language models, including "
                                      f"{examples[0]}, {examples[1]}, {examples[2]} and {examples[3]}.",
                       "h1_plain": h1, "section": "learn", "search_type": "Glossary",
                       "crumbs": [("Home", "index.html"), ("Glossary", "glossary.html"), (display, None)], "schema": schema,
                       "priority": 0.6, "scripts": ["pages/glossary.js"]}, content))
    return pages


def glossary_spotlight():
    picks = ["kv-cache", "mixture-of-experts", "prompt-caching", "quantization", "speculative-decoding", "grounding"]
    t = GLOSS_BY.get(picks[int(UPDATED[-2:]) % len(picks)]) or GLOSSARY[0]
    return (f'<div class="panel"><p class="small muted">Term of the week</p><h3 style="margin-top:.25rem"><a href="{glossary_href(t["slug"])}">{esc(t["term"])}</a></h3>'
            f'<p style="margin-top:.5rem">{esc(t["short"])}</p><p class="small" style="margin-top:.75rem"><a href="glossary.html">Browse all {len(GLOSSARY)} terms</a></p></div>')


# ---------------------------------------------------------------- videos

VIDEO_CATS = ["Fundamentals", "How transformers work", "Using LLMs well", "Building with LLMs", "Running models locally", "Safety & limits"]


def videos_page():
    out = ""
    nav = '<div class="pill-nav">' + "".join(f'<a href="#{slugify(c)}">{esc(c)}</a>' for c in VIDEO_CATS) + "</div>"
    for i, c in enumerate(VIDEO_CATS):
        vs = [v for v in VIDEOS if v["category"] == c]
        if not vs:
            continue
        out += (f'<section class="section" aria-labelledby="{slugify(c)}"><div class="wrap"><div class="section-head"><div><h2 id="{slugify(c)}">{esc(c)}</h2></div></div>'
                f'<div class="grid grid--3">' + "".join(video_card(v) for v in vs) + "</div>"
                + (ad_slot("videos-" + str(i), promo=i) if i in (1, 3) else "") + "</div></section>")
    content = (page_head("LLM videos worth your time", f"{len(VIDEOS)} hand-picked talks and explainers on how large language models work and how to use them well. Each one is summarized so you can pick what to watch.",
                         [f"Checked {fmt_date(UPDATED, True)}", "Videos play from YouTube in privacy-enhanced mode"], extra=f'<div style="margin-top:1.25rem">{nav}</div>') +
               out + '<div class="wrap" id="yt-channel-slot"></div>' + f'<div class="wrap">{lead_band("default", "", "videos")}</div>')
    schema = []
    for v in VIDEOS:
        if v.get("uploaded"):
            schema.append({"@type": "VideoObject", "name": v["title"], "description": v["summary"], "uploadDate": v["uploaded"],
                           "thumbnailUrl": f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg', "embedUrl": f'https://www.youtube-nocookie.com/embed/{v["id"]}',
                           "contentUrl": f'https://www.youtube.com/watch?v={v["id"]}'})
    meta = {"slug": "videos", "title": "Best Videos on Large Language Models: Explainers, Talks and Tutorials",
            "description": f"{len(VIDEOS)} curated videos on LLMs, from Karpathy and 3Blue1Brown explainers to RAG, agents, prompting and running models locally, each with a short summary.",
            "section": "videos", "crumbs": [("Home", "index.html"), ("Videos", None)], "schema": schema, "priority": 0.7}
    return meta, content


def video_grid(n=3, cat=None):
    vs = [v for v in VIDEOS if (cat is None or v["category"] == cat)][:int(n)]
    return '<div class="grid grid--3">' + "".join(video_card(v, show_takeaways=False) for v in vs) + "</div>"


# ---------------------------------------------------------------- prompts

PROMPT_CATS = ["Writing & editing", "Coding", "Data & analysis", "Research & learning", "Business & strategy", "Marketing & sales",
               "Customer support", "Product & UX", "Productivity", "Builders"]


def prompts_page():
    chips = "".join(f'<button type="button" class="chip-toggle" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in PROMPT_CATS)
    out = ""
    for i, c in enumerate(PROMPT_CATS):
        ps = [p for p in PROMPTS if p["category"] == c]
        cards = ""
        for p in ps:
            cards += (f'<article class="prompt-card" id="{esc(p["id"])}" data-cat="{esc(c)}" data-text="{esc((p["title"] + " " + p["use_case"]).lower())}">'
                      f'<h3>{esc(p["title"])}</h3><p class="muted small">{esc(p["use_case"])}</p>'
                      f'<pre>{esc(p["prompt"])}</pre><p class="small">{esc(p["tips"])}</p>'
                      f'<div class="pc-meta"><span class="tag">{esc(p["level"])}</span><button type="button" class="btn btn--ghost btn--sm" data-copy-target="{esc(p["id"])}">Copy prompt</button>'
                      f'<a class="small" href="#{esc(p["id"])}">Link</a></div></article>')
        out += (f'<section class="prompt-group" data-cat="{esc(c)}" aria-labelledby="pc-{slugify(c)}" style="margin-top:2.5rem"><h2 class="h2" id="pc-{slugify(c)}" style="margin-bottom:1rem">{esc(c)}</h2>'
                f'<div class="grid grid--2">{cards}</div></section>' + (ad_slot("prompts-" + str(i), promo=i + 2) if i in (2, 6) else ""))
    content = (page_head("Prompt library", f"{len(PROMPTS)} tested prompt templates for writing, coding, analysis, support and building LLM apps. Copy one, fill in the variables in curly braces, and adapt it to your model.",
                         [f"Updated {fmt_date(UPDATED, True)}", '<a href="prompt-builder.html">Build your own prompt</a>', '<a href="prompt-engineering-guide.html">Prompting guide</a>']) +
               f'''<div class="wrap"><div class="filters"><div class="filters__top"><label class="visually-hidden" for="pr-q">Search prompts</label><input class="input" id="pr-q" type="search" placeholder="Search prompts" autocomplete="off"></div>
<div class="tags" role="group" aria-label="Category">{chips}</div><p class="result-count" id="pr-count" aria-live="polite">{len(PROMPTS)} prompts</p></div>
{out}<p class="empty" id="pr-empty" hidden>No prompts match. Try another word or clear the category.</p>
{lead_band("build", "", "prompts")}</div>''')
    meta = {"slug": "prompts", "title": f"Prompt Library: {len(PROMPTS)} Prompt Templates for ChatGPT, Claude, Gemini and Open Models",
            "description": f"{len(PROMPTS)} copy-ready, model-agnostic prompt templates for writing, coding, data analysis, customer support, product work and building LLM apps.",
            "section": "learn", "crumbs": [("Home", "index.html"), ("Prompt library", None)], "priority": 0.7,
            "scripts": ["pages/prompts.js"]}
    return meta, content


# ---------------------------------------------------------------- resources

def resources_page():
    cats = RESOURCES["categories"]
    items = RESOURCES["items"]
    nav = '<div class="pill-nav">' + "".join(f'<a href="#r-{c["id"]}">{esc(c["name"])}</a>' for c in cats) + "</div>"
    out = ""
    for i, c in enumerate(cats):
        its = [x for x in items if x["category"] == c["id"]]
        rows = "".join(
            f'<li><a class="row" href="{esc(x["url"])}" target="_blank" rel="noopener" data-aff="{esc(x.get("aff_key", ""))}">'
            f'<span class="row__title">{esc(x["name"])}</span><span class="row__desc">{esc(x["description"])}</span>'
            f'<span class="row__meta">{esc(x["type"])}</span></a></li>' for x in its)
        out += (f'<section class="section" aria-labelledby="r-{c["id"]}"><div class="wrap"><div class="section-head"><div><h2 id="r-{c["id"]}">{esc(c["name"])}</h2>'
                f'<p>{esc(c["description"])}</p></div></div><ul class="rowlist">{rows}</ul>' + (ad_slot("resources-" + str(i), promo=i) if i in (2, 7) else "") + "</div></section>")
    content = (page_head("LLM resources", f"{len(items)} vendor-neutral picks: model APIs, local runners, serving engines, frameworks, vector databases, evaluation tools, courses and the papers that started it all.",
                         [f"Checked {fmt_date(UPDATED, True)}", "No paid placements in this list"], extra=f'<div style="margin-top:1.25rem">{nav}</div>') +
               out + f'<div class="wrap"><p class="small muted">Know a tool that belongs here? <a href="list-your-product.html">Suggest it</a>. Editorial picks are never paid for; sponsored listings are labeled.</p>{lead_band("build", "", "resources")}</div>')
    meta = {"slug": "resources", "title": "LLM Resources: Tools, Frameworks, Vector Databases, Courses and Papers",
            "description": f"A curated, vendor-neutral directory of {len(items)} LLM resources: APIs, Ollama and local runners, vLLM, LangChain, vector databases, evals, fine-tuning tools, courses and key papers.",
            "section": "learn", "crumbs": [("Home", "index.html"), ("Resources", None)], "priority": 0.7}
    return meta, content


def leaderboard_links():
    hubs = [x for x in RESOURCES["items"] if x["category"] == "hubs"]
    return '<ul class="rowlist">' + "".join(
        f'<li><a class="row" href="{esc(x["url"])}" target="_blank" rel="noopener"><span class="row__title">{esc(x["name"])}</span>'
        f'<span class="row__desc">{esc(x["description"])}</span><span class="row__meta">{esc(x["type"])}</span></a></li>' for x in hubs) + "</ul>"


# ---------------------------------------------------------------- timeline

def timeline_page():
    legend = '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{esc(TL_LABEL[k])}</span>' for k, c in TL_COLORS.items()) + "</div>"
    years = sorted({e["date"][:4] for e in TIMELINE})
    ynav = '<div class="pill-nav" style="margin-top:1rem">' + "".join(f'<a href="#y{y}">{y}</a>' for y in years) + "</div>"
    content = (page_head("The history of large language models", f"{len(TIMELINE)} milestones from the 2017 Transformer paper to this month's releases: research breakthroughs, model launches, open-weight releases and the rules that followed. Every date links to a primary source.",
                         [f"Updated {fmt_date(UPDATED, True)}"], extra=legend + ynav) +
               f'<div class="wrap wrap--read">{timeline_html()}{ad_slot("timeline", promo=1)}</div><div class="wrap">{lead_band("default", "", "timeline")}</div>')
    meta = {"slug": "llm-timeline", "title": "LLM Timeline: The History of Large Language Models, 2017 to 2026",
            "description": f"A dated timeline of {len(TIMELINE)} large language model milestones, from Attention Is All You Need and GPT-3 to ChatGPT, open-weight models and 2026 releases.",
            "section": "models", "crumbs": [("Home", "index.html"), ("LLM timeline", None)], "priority": 0.7}
    return meta, content


# ---------------------------------------------------------------- search index, sitemaps, llms.txt

def build_search_index(pages):
    idx = []
    for meta in pages:
        if meta.get("noindex"):
            continue
        slug = meta["slug"]
        url = "index.html" if slug == "index" else f"{slug}.html"
        t = meta.get("search_type") or ("Model" if slug.startswith("model-") else "Comparison" if "-vs-" in slug else
                                         "Tool" if slug in TOOL_BY else "Guide" if slug in GUIDE_BY else
                                         "Provider" if slug.endswith("-models") else "Page")
        title = meta.get("h1_plain") or re.sub(r"\s*\|.*$", "", meta["title"])
        idx.append({"t": title, "u": url, "y": t, "d": meta["description"][:140], "k": meta.get("keywords", "")})
    for term in GLOSSARY:
        idx.append({"t": term["term"], "u": glossary_href(term["slug"]), "y": "Glossary", "d": term["short"],
                    "k": " ".join(term.get("aka", []))})
    for m in MODELS:
        for e in idx:
            if e["u"] == m["url_page"]:
                e["t"] = m["name"]
                e["d"] = f'{m["provider_name"]}, {fmt_tokens(m.get("context")).replace("&mdash;", "n/a")} context, {fmt_price(m.get("price_in")).replace("&mdash;", "n/a")} in / {fmt_price(m.get("price_out")).replace("&mdash;", "n/a")} out'
                e["k"] = " ".join([m["family"], m["provider"], " ".join(m.get("best_for", []))])
    return idx


def sitemap_xml(pages):
    urls = []
    for meta in pages:
        if meta.get("noindex"):
            continue
        slug = meta["slug"]
        loc = SITE["site_url"] + "/" + ("" if slug == "index" else f"{slug}.html")
        pr = meta.get("priority", 0.5)
        urls.append(f"<url><loc>{loc}</loc><lastmod>{UPDATED}</lastmod><priority>{pr:.1f}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
            "\n".join(urls) + "\n</urlset>\n")


def sitemap_html(pages):
    groups = OrderedDict([("Start here", []), ("Models and providers", []), ("Comparisons", []), ("Shortlists", []), ("Tools", []),
                          ("Guides", []), ("Learn more", []), ("Work with us", []), ("About and legal", [])])
    hub_slugs = {h["slug"] for h in HUBS}
    learn = {"glossary", "videos", "prompts", "resources", "guides", "llm-timeline", "newsletter"}
    work = {"hire-llm-experts", "list-your-product", "advertise", "support", "contests", "contest-rules", "careers", "contact"}
    for meta in pages:
        if meta.get("noindex") or meta["slug"] == "sitemap":
            continue
        s = meta["slug"]
        url = "index.html" if s == "index" else f"{s}.html"
        name = meta.get("h1_plain") or re.sub(r"\s*[:|].*$", "", meta["title"])
        if s.startswith("model-"):
            name = MODEL_BY[s[6:]]["name"]
            g = "Models and providers"
        elif s.endswith("-models") or s in ("models", "providers", "leaderboard"):
            g = "Models and providers"
        elif "-vs-" in s or s == "compare":
            g = "Comparisons"
        elif s in hub_slugs:
            g = "Shortlists"
        elif s in TOOL_BY or s == "tools":
            g = "Tools"
        elif s in GUIDE_BY:
            g = "Guides"
        elif s in learn or s.startswith("glossary-"):
            g = "Learn more"
        elif s in work:
            g = "Work with us"
        elif s == "index":
            g = "Start here"
        else:
            g = "About and legal"
        groups[g].append((name, url))
    cols = "".join(f'<section><h2>{esc(g)}</h2><ul>' + "".join(f'<li><a href="{u}">{esc(n)}</a></li>' for n, u in items) + "</ul></section>"
                   for g, items in groups.items() if items)
    content = page_head("Site map", "Every page on LLModel.com, grouped by section.") + f'<div class="wrap sitemap-cols">{cols}</div>'
    meta = {"slug": "sitemap", "title": "Site Map", "description": "Every page on LLModel.com: models, providers, comparisons, tools, guides, glossary, videos and more.",
            "section": "", "crumbs": [("Home", "index.html"), ("Site map", None)], "priority": 0.3, "ads": False}
    return meta, content


def llms_txt():
    lines = [f"# LLModel.com", "", f"> {SITE['tagline']}. Independent, vendor-neutral data and guides on large language models: "
             f"{len(MODELS)} models from {len(PROVIDERS)} providers with list prices and context windows checked {fmt_date(UPDATED, True)}, "
             "free calculators, and plain-English guides.", "",
             "## Directory", f"- [Model directory]({SITE['site_url']}/models.html): every model with price, context, weights and status",
             f"- [Providers]({SITE['site_url']}/providers.html)", f"- [Rankings and value index]({SITE['site_url']}/leaderboard.html)",
             f"- [LLM timeline]({SITE['site_url']}/llm-timeline.html)", "", "## Tools"]
    lines += [f"- [{t['name']}]({SITE['site_url']}/{t['slug']}.html): {t['desc']}" for t in TOOLS]
    lines += ["", "## Guides"]
    lines += [f"- [{g['h1']}]({SITE['site_url']}/{g['slug']}.html): {g['summary']}" for g in GUIDES]
    lines += ["", "## Reference", f"- [Glossary]({SITE['site_url']}/glossary.html): {len(GLOSSARY)} terms, A to Z"]
    lines += [f"- [Glossary: {d[0].lower() + d[1:]}]({SITE['site_url']}/glossary-{s}.html)" for c, s, d, *_ in GLOSSARY_TOPICS]
    lines += [f"- [Prompt library]({SITE['site_url']}/prompts.html)",
              f"- [Resources]({SITE['site_url']}/resources.html)", f"- [Editorial policy]({SITE['site_url']}/editorial-policy.html)", ""]
    return "\n".join(lines)
