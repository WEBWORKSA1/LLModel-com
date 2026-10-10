"""Data-driven pages: model profiles, providers, comparisons, use-case hubs, directory, rankings, timeline."""
import math
from .common import (MODELS, PROVIDERS, MODEL_BY, TIMELINE, SITE, UPDATED, TIER_LABEL, STATUS_LABEL, MOD_LABEL,
                     esc, fmt_date, fmt_price, fmt_money, fmt_tokens, fmt_params, fmt_int, date_sort_key,
                     badge_status, badge_weights, tier_tag, model_link, ad_slot, lead_band, faq_html, faq_schema,
                     page_head, section, section_head, current_models, VIDEOS, video_card, newsletter_box, RESOURCES,
                     TOOL_BY, GUIDE_BY)

SCENARIOS = [
    ("Support chatbot", "30,000 conversations a month, 2,000 input and 400 output tokens each", 30000, 2000, 400),
    ("Document summaries", "2,000 documents a month, 12,000 input and 800 output tokens each", 2000, 12000, 800),
    ("Coding agent", "1,000 tasks a month, 60,000 input and 6,000 output tokens each", 1000, 60000, 6000),
]


def scenario_cost(m, n, tin, tout):
    if m.get("price_in") is None or m.get("price_out") is None:
        return None
    return n * (tin * m["price_in"] + tout * m["price_out"]) / 1e6


def mods(m, key="modalities_in"):
    return ", ".join(MOD_LABEL.get(x, x.title()) for x in m.get(key, [])) or "Text"


def words_from_tokens(t):
    return int(t * 0.75)


def human_context(ctx):
    if not ctx:
        return ""
    w = words_from_tokens(ctx)
    pages = w / 500
    if pages >= 100:
        return f"about {fmt_int(round(w, -3))} words, or {fmt_int(round(pages, -1))} pages"
    return f"about {fmt_int(round(w, -2))} words, or {fmt_int(round(pages))} pages"


def weights_gb(params_b, bits):
    return params_b * bits / 8 * 1.0


def mem_table(m):
    t = m.get("params_total_b")
    if not t:
        return ""
    rows = [("16-bit (BF16/FP16)", 16), ("8-bit (FP8/INT8)", 8), ("4-bit (Q4_K_M, about 4.85 bits)", 4.85)]
    body = "".join(f'<tr><td>{esc(n)}</td><td class="num">{weights_gb(t, b):,.0f} GB</td></tr>' for n, b in rows)
    moe = ""
    if m.get("params_active_b") and m["params_active_b"] != t:
        moe = (f'<p class="small muted" style="margin-top:.6rem">This is a mixture-of-experts model: all {fmt_params(m).split(",")[0]} '
               f'parameters must sit in memory, but only about {m["params_active_b"]:g}B are used per token, so it runs faster than a dense model of the same size.</p>')
    return (f'<div class="table-wrap"><table class="table"><thead><tr><th>Precision</th><th class="num">Memory for weights</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>{moe}'
            f'<p class="small muted" style="margin-top:.6rem">Add memory for the KV cache (it grows with context length and concurrent users) and 1-2 GB of runtime overhead. '
            f'<a href="vram-calculator.html?model={esc(m["slug"])}">Size it precisely in the VRAM calculator</a>.</p>')


def alternatives(m, k=4):
    pool = [x for x in MODELS if x["slug"] != m["slug"] and x["status"] != "legacy"]
    def dist(x):
        d = abs(x["tier_rank"] - m["tier_rank"]) * 2
        if m["blended"] and x["blended"]:
            d += abs(math.log(x["blended"] / m["blended"]))
        else:
            d += 1.5
        if x["provider"] == m["provider"]:
            d += 0.8
        if x["weights"] != m["weights"]:
            d += 0.4
        return d
    return sorted(pool, key=dist)[:k]


COMPARISONS = [
    ("claude-opus-5-5", "gpt-6-astra"),
    ("claude-sonnet-5-5", "gpt-6-1-sol"),
    ("claude-haiku-5-5", "gpt-6-luna"),
    ("gemini-3-1-pro", "gpt-6-astra"),
    ("claude-opus-5-5", "gemini-3-1-pro"),
    ("claude-fable-5-1", "gpt-6-astra"),
    ("gemini-3-8-flash", "gpt-6-1-sol"),
    ("grok-4-7", "gpt-6-1-sol"),
    ("deepseek-v4-pro", "claude-opus-5-5"),
    ("qwen3-8-max", "deepseek-v4-pro"),
    ("kimi-k3", "deepseek-v4-pro"),
    ("gpt-oss-120b", "gemma-4-31b"),
]


def cmp_slug(a, b):
    return f"{a}-vs-{b}"


CMP_INDEX = {}
for _a, _b in COMPARISONS:
    CMP_INDEX[frozenset((_a, _b))] = cmp_slug(_a, _b)


def compare_href(a, b):
    s = CMP_INDEX.get(frozenset((a, b)))
    return f"{s}.html" if s else f"compare.html?models={a},{b}"


def model_faq(m):
    p = PROVIDERS[m["provider"]]
    name = m["name"]
    out = []
    if m.get("price_in") is not None:
        cached = f", with cached input at {fmt_price(m['price_cached_in'])}" if m.get("price_cached_in") is not None else ""
        note = (" " + m["price_note"]) if m.get("price_note") else ""
        out.append({"q": f"How much does {name} cost?",
                    "a": f"{name} lists at {fmt_price(m['price_in'])} per million input tokens and {fmt_price(m['price_out'])} per million output tokens{cached} (checked {fmt_date(m['verified'], True)}).{note} Confirm current rates on the provider's pricing page before you commit."})
    else:
        out.append({"q": f"How much does {name} cost?",
                    "a": f"We couldn't confirm a published per-token list price for {name} on {fmt_date(m['verified'], True)}. " + (m.get("price_note") or "") + " Check the provider's pricing page for current rates."})
    if m.get("context"):
        mo = f", and it can write up to {fmt_tokens(m['max_output'])} tokens in a single response" if m.get("max_output") else ""
        out.append({"q": f"What is the context window of {name}?",
                    "a": f"{name} accepts up to {fmt_int(m['context'])} tokens of context ({human_context(m['context'])}){mo}. Long prompts cost more and can be slower, so most apps send only what the task needs."})
    if m["weights"] == "open":
        hf = f" from Hugging Face ({m['hf_repo']})" if m.get("hf_repo") else ""
        out.append({"q": f"Is {name} open source?",
                    "a": f"{name} is an open-weight model released under the {m['license']} license. You can download the weights{hf} and run or fine-tune them yourself, within the license terms. Open weights isn't the same as fully open source: training data and code may not be published."})
        if m.get("params_total_b"):
            out.append({"q": f"Can I run {name} locally?",
                        "a": f"Yes, if you have enough memory. The weights alone need about {weights_gb(m['params_total_b'], 4.85):,.0f} GB at 4-bit quantization and about {weights_gb(m['params_total_b'], 16):,.0f} GB at 16-bit, plus room for the KV cache. Use the VRAM calculator on LLModel.com to check a specific GPU or Mac."})
    else:
        access = ", ".join(a for a in m.get("access", []) if a != "API") or "the provider's apps"
        out.append({"q": f"Is {name} open source?",
                    "a": f"No. {name} is a proprietary model from {p['name']}; its weights aren't published. You can use it through the {p['name']} API and through {access}."})
    caps = []
    caps.append(f"accepts {mods(m).lower()} as input")
    caps.append("has a reasoning (thinking) mode" if m.get("reasoning") else "doesn't offer a separate reasoning mode")
    caps.append("supports tool calling" if m.get("tool_use") else "doesn't document tool calling")
    out.append({"q": f"What is {name} best for?",
                "a": f"{p['name']} positions {name} for {', '.join(m['best_for'][:4])}. It {caps[0]}, {caps[1]} and {caps[2]}. Test it on a sample of your own tasks before you choose it for production."})
    return out


def model_page(m):
    p = PROVIDERS[m["provider"]]
    name = esc(m["name"])
    specs = [
        ("Context window", fmt_tokens(m.get("context")), human_context(m.get("context"))),
        ("Max output", fmt_tokens(m.get("max_output")) if m.get("max_output") else "Not published", "tokens per response" if m.get("max_output") else ""),
        ("Input price", fmt_price(m.get("price_in")), "per 1M tokens" if m.get("price_in") is not None else "no list price confirmed"),
        ("Output price", fmt_price(m.get("price_out")), "per 1M tokens" if m.get("price_out") is not None else ""),
        ("Cached input", fmt_price(m.get("price_cached_in")) if m.get("price_cached_in") is not None else "Not published", "per 1M tokens" if m.get("price_cached_in") is not None else ""),
        ("Weights", "Open" if m["weights"] == "open" else "Closed", m.get("license") or ""),
        ("Parameters", fmt_params(m), m.get("architecture") if m.get("architecture") not in (None, "unknown") else ""),
        ("Input types", mods(m), ""),
        ("Output types", mods(m, "modalities_out"), ""),
        ("Reasoning mode", "Yes" if m.get("reasoning") else "No", ""),
        ("Tool calling", "Yes" if m.get("tool_use") else "Not documented", ""),
        ("Released", fmt_date(m["released"]), STATUS_LABEL[m["status"]]),
    ]
    spec_html = '<dl class="specs">' + "".join(
        f'<div><dt>{esc(k)}</dt><dd>{v}{f"<small>{esc(s)}</small>" if s else ""}</dd></div>' for k, v, s in specs) + "</dl>"
    price_note = f'<p class="small muted" style="margin-top:.75rem">{esc(m["price_note"])}</p>' if m.get("price_note") else ""

    rows = ""
    for label, desc, n, tin, tout in SCENARIOS:
        c = scenario_cost(m, n, tin, tout)
        rows += f'<tr><td><strong>{esc(label)}</strong><span class="m-sub">{esc(desc)}</span></td><td class="num">{fmt_money(c) if c is not None else "No list price"}</td></tr>'
    cost_html = (f'<div class="table-wrap"><table class="table"><thead><tr><th>Workload</th><th class="num">Monthly cost at list price</th></tr></thead><tbody>{rows}</tbody></table></div>'
                 f'<p class="small muted" style="margin-top:.6rem">Standard rates, no caching or batch discounts. '
                 f'<a href="llm-cost-calculator.html?model={esc(m["slug"])}">Run your own numbers</a>.</p>')

    strengths = "".join(f"<li>{esc(s)}</li>" for s in m.get("strengths", []))
    cons = "".join(f"<li>{esc(s)}</li>" for s in m.get("considerations", []))
    best = "".join(f'<span class="tag">{esc(b)}</span>' for b in m.get("best_for", []))
    access = "".join(f'<li>{esc(a)}</li>' for a in m.get("access", []))

    alts = alternatives(m)
    alt_rows = "".join(
        f'<tr><td class="m-name">{model_link(a)}<span class="m-sub">{esc(a["provider_name"])}</span></td>'
        f'<td>{tier_tag(a)}</td><td class="num">{fmt_tokens(a.get("context"))}</td>'
        f'<td class="num">{fmt_price(a.get("price_in"))} / {fmt_price(a.get("price_out"))}</td>'
        f'<td><a href="{compare_href(m["slug"], a["slug"])}">Compare</a></td></tr>' for a in alts)
    alt_html = (f'<div class="table-wrap"><table class="table"><thead><tr><th>Model</th><th>Tier</th><th class="num">Context</th>'
                f'<th class="num">Input / output per 1M</th><th></th></tr></thead><tbody>{alt_rows}</tbody></table></div>')

    sources = []
    for u in [m.get("url"), m.get("pricing_url")] + list(m.get("sources", [])):
        if u and u not in sources:
            sources.append(u)
    src_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u.replace("https://", "").rstrip("/"))}</a></li>' for u in sources)

    self_host = ""
    if m["weights"] == "open":
        hf = (f'<p style="margin-top:.75rem"><a href="https://huggingface.co/{esc(m["hf_repo"])}" target="_blank" rel="noopener">Model card on Hugging Face</a></p>'
              if m.get("hf_repo") else "")
        self_host = (f'<section class="panel" aria-labelledby="run-it"><h2 class="h3" id="run-it">Run it yourself</h2>'
                     f'<p class="muted" style="margin:.4rem 0 1rem">Released under <strong>{esc(m.get("license") or "an open license")}</strong>. '
                     f'Approximate memory needed just to load the weights:</p>{mem_table(m)}{hf}</section>')

    faqs = model_faq(m)
    side = f'''<aside class="aside-box" aria-label="Quick actions">
  <h2 class="h3">Quick actions</h2>
  <ul class="inline-list" style="display:grid;gap:.55rem;margin-top:.5rem">
    <li><a href="llm-cost-calculator.html?model={esc(m["slug"])}">Price {name} for your workload</a></li>
    <li><a href="compare.html?models={esc(m["slug"])},{esc(alts[0]["slug"])}">Compare with {esc(alts[0]["name"])}</a></li>
    {f'<li><a href="vram-calculator.html?model={esc(m["slug"])}">Check GPU memory</a></li>' if m["weights"] == "open" else ''}
    <li><a href="{p["url_page"]}">All {esc(p["name"])} models</a></li>
    <li><a href="{esc(m.get("url") or "#")}" target="_blank" rel="noopener">Official model page</a></li>
  </ul>
  <hr style="border:0;border-top:1px solid var(--rule);margin:1rem 0">
  <p class="small muted">Deploying {name}? Get a second opinion on architecture, cost and risk.</p>
  <a class="btn btn--primary btn--block" style="margin-top:.75rem" href="hire-llm-experts.html?need=choose-model&amp;model={esc(m["slug"])}&amp;from=model">Get expert help</a>
</aside>'''

    main = f'''<div class="wrap grid grid--sidebar" style="padding-bottom:1rem">
<div class="stack" style="--gap:2rem">
  <section aria-labelledby="specs"><h2 class="h2" id="specs" style="margin-bottom:1rem">Specifications</h2>{spec_html}{price_note}</section>
  <section aria-labelledby="costs" style="margin-top:2.5rem"><h2 class="h2" id="costs" style="margin-bottom:1rem">What it costs in practice</h2>{cost_html}</section>
  {ad_slot("model-mid", promo=sum(map(ord, m["slug"])) % 6)}
  <section class="pros-cons" aria-label="Strengths and trade-offs" style="margin-top:2.5rem">
    <div class="panel"><h2 class="h3">Strengths</h2><ul>{strengths}</ul></div>
    <div class="panel"><h2 class="h3">Trade-offs to weigh</h2><ul>{cons}</ul></div>
  </section>
  <section aria-labelledby="fit" style="margin-top:2.5rem"><h2 class="h2" id="fit" style="margin-bottom:.75rem">Where it fits</h2>
    <p class="muted" style="margin-bottom:.75rem">{esc(p["name"])} positions {name} for:</p><div class="tags">{best}</div>
    <h3 style="margin-top:1.5rem">Where you can use it</h3><ul style="margin-top:.5rem">{access}</ul></section>
  {('<div style="margin-top:2.5rem">' + self_host + '</div>') if self_host else ''}
  <section aria-labelledby="alts" style="margin-top:2.5rem"><h2 class="h2" id="alts" style="margin-bottom:1rem">Alternatives to consider</h2>{alt_html}</section>
  <div style="margin-top:2.5rem">{faq_html(faqs)}</div>
  <section class="sources" aria-labelledby="src" style="margin-top:2.5rem"><h2 class="h3" id="src">Sources</h2><ol>{src_html}</ol>
    <p class="small muted" style="margin-top:.5rem">Facts checked against these pages on {fmt_date(m["verified"], True)}. Spot an error? <a href="contact.html?topic=correction">Tell us</a>.</p></section>
</div>
{side}
</div>'''
    head = page_head(name, esc(m["summary"]),
                     [f'By <a href="{p["url_page"]}">{esc(p["name"])}</a>', f'Released {fmt_date(m["released"], True)}',
                      f'Data checked {fmt_date(m["verified"], True)}'],
                     extra=f'<div class="tags" style="margin-top:1rem">{badge_status(m)}{badge_weights(m)}{tier_tag(m)}</div>')
    content = head + main + f'<div class="wrap">{lead_band("choose", "choose-model", "model-" + m["slug"])}</div>'
    price_bit = f"{fmt_price(m['price_in']).replace('&mdash;', 'n/a')}/{fmt_price(m['price_out']).replace('&mdash;', 'n/a')} per 1M tokens, " if m.get("price_in") is not None else ""
    desc = (f"{m['name']} by {p['name']}: {price_bit}{fmt_tokens(m.get('context'))} context, "
            f"{'open weights' if m['weights'] == 'open' else 'closed model'}. Specs, real-world costs, strengths and alternatives.")
    meta = {
        "slug": f"model-{m['slug']}",
        "title": f"{m['name']}: Pricing, Context Window and Specs ({fmt_date(UPDATED)[:3]} {UPDATED[:4]})",
        "description": desc[:300],
        "section": "models",
        "crumbs": [("Home", "index.html"), ("Models", "models.html"), (p["name"], p["url_page"]), (m["name"], None)],
        "schema": [faq_schema(faqs), {"@type": "WebPage", "name": f"{m['name']} specs and pricing", "dateModified": m["verified"],
                                      "about": {"@type": "Thing", "name": m["name"]}}],
        "priority": 0.7,
    }
    return meta, content


# ---------------------------------------------------------------- providers

def provider_page(p):
    ms = p["models"]
    rows = "".join(
        f'<tr><td class="m-name">{model_link(m)}<span class="m-sub">{esc(m["family"])}</span></td><td>{badge_status(m)}</td>'
        f'<td>{badge_weights(m)}</td><td>{tier_tag(m)}</td><td class="num">{fmt_tokens(m.get("context"))}</td>'
        f'<td class="num">{fmt_price(m.get("price_in"))}</td><td class="num">{fmt_price(m.get("price_out"))}</td>'
        f'<td class="nowrap">{fmt_date(m["released"])}</td></tr>' for m in ms)
    table = (f'<div class="table-wrap"><table class="table"><thead><tr><th>Model</th><th>Status</th><th>Weights</th><th>Tier</th>'
             f'<th class="num">Context</th><th class="num">Input / 1M</th><th class="num">Output / 1M</th><th>Released</th></tr></thead>'
             f'<tbody>{rows}</tbody></table></div>')
    cur = [m for m in ms if m["status"] != "legacy"]
    priced = [m for m in cur if m["blended"]]
    summary_bits = []
    if priced:
        cheap = min(priced, key=lambda m: m["blended"])
        summary_bits.append(f'The lowest-priced current model is {model_link(cheap)} at {fmt_price(cheap["price_in"])} input and {fmt_price(cheap["price_out"])} output per million tokens.')
    top = sorted(cur, key=lambda m: (m["tier_rank"], -(m["blended"] or 0)))
    if top:
        summary_bits.append(f'The most capable tier in the lineup is {TIER_LABEL[top[0]["tier"]].lower()}, led by {model_link(top[0])}.')
    longest = max(ms, key=lambda m: m.get("context") or 0)
    if longest.get("context"):
        summary_bits.append(f'The longest context window is {fmt_tokens(longest["context"])} tokens ({model_link(longest)}).')
    kv = [("Headquarters", esc(p.get("hq") or "Not stated")), ("Founded", esc(p.get("founded") or "Not stated")),
          ("Consumer app", esc(p.get("consumer_app") or "None")), ("Open weights", esc(p.get("open_weights") or "No")),
          ("Developer docs", f'<a href="{esc(p.get("api_url") or p["url"])}" target="_blank" rel="noopener">{esc((p.get("api_url") or p["url"]).replace("https://", "").rstrip("/"))}</a>')]
    if p.get("aka"):
        kv.insert(0, ("Also known as", esc(p["aka"])))
    kv_html = '<dl class="kv">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in kv) + "</dl>"
    others = [q for q in PROVIDERS.values() if q["slug"] != p["slug"]]
    other_html = '<div class="pill-nav">' + "".join(f'<a href="{q["url_page"]}">{esc(q["name"])}</a>' for q in others) + "</div>"
    name = p["name"]
    faqs = [
        {"q": f"What models does {name} offer?",
         "a": f"As of {fmt_date(UPDATED, True)}, we track {len(ms)} {name} model{'s' if len(ms) != 1 else ''}: " + ", ".join(m["name"] for m in ms) + ". Status, prices and context windows for each are in the table on this page."},
        {"q": f"How do I access {name} models?",
         "a": (f"Through {name}'s developer platform" + (f" ({(p.get('api_url') or '').replace('https://', '').rstrip('/')})" if p.get("api_url") else "") +
               (f", in the {p['consumer_app']} app" if p.get("consumer_app") else "") +
               ", and for many models through cloud marketplaces and inference providers listed on each model page.")},
        {"q": f"Does {name} release open-weight models?", "a": p.get("open_weights") or "Not that we know of."},
    ]
    content = (page_head(f"{esc(name)} models", esc(p["summary"]),
                         [f"{len(ms)} model{'s' if len(ms) != 1 else ''} tracked", f"Data checked {fmt_date(UPDATED, True)}"]) +
               f'<div class="wrap grid grid--sidebar"><div><section aria-labelledby="lineup"><h2 class="h2" id="lineup" style="margin-bottom:1rem">Lineup</h2>{table}'
               f'<p style="margin-top:1rem">{" ".join(summary_bits)}</p></section>'
               f'{ad_slot("provider-mid", promo=2)}'
               f'<div style="margin-top:2.5rem">{faq_html(faqs)}</div></div>'
               f'<aside class="aside-box"><h2 class="h3">At a glance</h2>{kv_html}'
               f'<p style="margin-top:1rem"><a href="compare.html?models={",".join(m["slug"] for m in cur[:3])}">Compare {esc(name)} models side by side</a></p></aside></div>'
               f'<div class="wrap" style="margin-top:2.5rem"><h2 class="h3" style="margin-bottom:.75rem">Other providers</h2>{other_html}</div>'
               f'<div class="wrap">{lead_band("choose", "choose-model", "provider-" + p["slug"])}</div>')
    meta = {
        "slug": f"{p['slug']}-models",
        "title": f"{name} Models: Full Lineup, Prices and Context Windows ({UPDATED[:4]})",
        "description": f"Every {name} model we track: status, open or closed weights, context windows and per-token prices, checked {fmt_date(UPDATED, True)}.",
        "section": "models",
        "crumbs": [("Home", "index.html"), ("Providers", "providers.html"), (name, None)],
        "schema": [faq_schema(faqs)],
        "priority": 0.6,
    }
    return meta, content


def providers_index():
    rows = ""
    for p in sorted(PROVIDERS.values(), key=lambda p: (-len(p["models"]), p["name"])):
        cur = [m for m in p["models"] if m["status"] != "legacy"]
        open_n = sum(1 for m in p["models"] if m["weights"] == "open")
        flagship = sorted(cur, key=lambda m: (m["tier_rank"], -(m["blended"] or 0)))
        rows += (f'<tr><td class="m-name"><a href="{p["url_page"]}">{esc(p["name"])}</a><span class="m-sub">{esc(p.get("hq") or "")}</span></td>'
                 f'<td class="num">{len(p["models"])}</td><td class="num">{open_n}</td>'
                 f'<td>{model_link(flagship[0]) if flagship else "&mdash;"}</td><td>{esc(p.get("consumer_app") or "None")}</td></tr>')
    table = (f'<div class="table-wrap"><table class="table"><thead><tr><th>Provider</th><th class="num">Models</th><th class="num">Open-weight</th>'
             f'<th>Top current model</th><th>Consumer app</th></tr></thead><tbody>{rows}</tbody></table></div>')
    content = (page_head("LLM providers", f"The {len(PROVIDERS)} companies and labs behind the {len(MODELS)} models in our directory, from closed API platforms to open-weight labs.",
                         [f"Data checked {fmt_date(UPDATED, True)}"]) +
               f'<div class="wrap">{table}<p class="small muted" style="margin-top:.75rem">Open-weight counts include models whose weights you can download, whatever the license. Licenses differ a lot; check each model page.</p>'
               f'{ad_slot("providers", promo=1)}</div>')
    meta = {"slug": "providers", "title": "LLM Providers: Who Makes Which Large Language Models",
            "description": f"The {len(PROVIDERS)} providers behind today's LLMs: OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, Qwen and more, with model counts and open-weight policies.",
            "section": "models", "crumbs": [("Home", "index.html"), ("Providers", None)], "priority": 0.7}
    return meta, content


# ---------------------------------------------------------------- comparisons

def better(a, b, key, lower=True):
    va, vb = a.get(key), b.get(key)
    if va is None or vb is None or va == vb:
        return None
    return a if ((va < vb) if lower else (va > vb)) else b


def compare_page(sa, sb):
    a, b = MODEL_BY[sa], MODEL_BY[sb]
    A, B = esc(a["name"]), esc(b["name"])
    bullets = []
    if a["blended"] and b["blended"]:
        ch = a if a["blended"] < b["blended"] else b
        ex = b if ch is a else a
        ratio = ex["blended"] / ch["blended"]
        if ratio > 1.05:
            bullets.append(f'<strong>Lower list price:</strong> {model_link(ch)}, about {ratio:.1f}&times; cheaper on a blended basis (three parts input to one part output).')
        else:
            bullets.append(f'<strong>Price:</strong> effectively tied on blended list price.')
    cx = better(a, b, "context", lower=False)
    if cx:
        other = b if cx is a else a
        bullets.append(f'<strong>Larger context window:</strong> {model_link(cx)} ({fmt_tokens(cx["context"])} vs {fmt_tokens(other.get("context"))} tokens).')
    elif a.get("context"):
        bullets.append(f'<strong>Context window:</strong> both accept {fmt_tokens(a["context"])} tokens.')
    if a["weights"] != b["weights"]:
        op = a if a["weights"] == "open" else b
        bullets.append(f'<strong>Open weights:</strong> only {model_link(op)} can be downloaded and self-hosted ({esc(op.get("license") or "open license")}).')
    elif a["weights"] == "open":
        bullets.append(f'<strong>Open weights:</strong> both can be self-hosted ({esc(a.get("license"))} and {esc(b.get("license"))}).')
    ma, mb = set(a.get("modalities_in", [])), set(b.get("modalities_in", []))
    if ma != mb:
        bullets.append(f'<strong>Inputs:</strong> {A} accepts {mods(a).lower()}; {B} accepts {mods(b).lower()}.')
    newer = a if date_sort_key(a["released"]) > date_sort_key(b["released"]) else b
    bullets.append(f'<strong>Newer release:</strong> {model_link(newer)} ({fmt_date(newer["released"], True)}).')

    def cell(m, key, fmt, lower=True):
        w = better(a, b, key, lower)
        cls = ' class="num best"' if w is m else ' class="num"'
        return f"<td{cls}>{fmt(m.get(key))}</td>"

    def row(label, va, vb):
        return f"<tr><th scope=\"row\">{esc(label)}</th><td>{va}</td><td>{vb}</td></tr>"

    spec_rows = "".join([
        row("Provider", f'<a href="{PROVIDERS[a["provider"]]["url_page"]}">{esc(a["provider_name"])}</a>', f'<a href="{PROVIDERS[b["provider"]]["url_page"]}">{esc(b["provider_name"])}</a>'),
        row("Released", fmt_date(a["released"]), fmt_date(b["released"])),
        row("Status", badge_status(a), badge_status(b)),
        row("Weights and license", f'{badge_weights(a)} <span class="small muted">{esc(a.get("license"))}</span>', f'{badge_weights(b)} <span class="small muted">{esc(b.get("license"))}</span>'),
        row("Tier", tier_tag(a), tier_tag(b)),
        f'<tr><th scope="row">Context window</th>{cell(a, "context", fmt_tokens, False)}{cell(b, "context", fmt_tokens, False)}</tr>',
        f'<tr><th scope="row">Max output</th>{cell(a, "max_output", fmt_tokens, False)}{cell(b, "max_output", fmt_tokens, False)}</tr>',
        f'<tr><th scope="row">Input per 1M tokens</th>{cell(a, "price_in", fmt_price)}{cell(b, "price_in", fmt_price)}</tr>',
        f'<tr><th scope="row">Output per 1M tokens</th>{cell(a, "price_out", fmt_price)}{cell(b, "price_out", fmt_price)}</tr>',
        f'<tr><th scope="row">Cached input per 1M</th>{cell(a, "price_cached_in", fmt_price)}{cell(b, "price_cached_in", fmt_price)}</tr>',
        row("Input types", mods(a), mods(b)),
        row("Reasoning mode", "Yes" if a.get("reasoning") else "No", "Yes" if b.get("reasoning") else "No"),
        row("Tool calling", "Yes" if a.get("tool_use") else "Not documented", "Yes" if b.get("tool_use") else "Not documented"),
        row("Parameters", fmt_params(a), fmt_params(b)),
    ])
    spec_table = (f'<div class="table-wrap"><table class="table cmp"><thead><tr><th></th><th>{A}</th><th>{B}</th></tr></thead>'
                  f'<tbody>{spec_rows}</tbody></table></div><p class="small muted" style="margin-top:.6rem">Highlighted cells are better on that line: lower price or larger limit. List prices, standard tier, checked {fmt_date(UPDATED, True)}.</p>')

    cost_rows = ""
    for label, desc, n, tin, tout in SCENARIOS:
        ca, cb = scenario_cost(a, n, tin, tout), scenario_cost(b, n, tin, tout)
        diff = ""
        if ca is not None and cb is not None and ca != cb:
            lo, hi = (a, ca) if ca < cb else (b, cb), (b, cb) if ca < cb else (a, ca)
            diff = f'{esc(lo[0]["name"])} saves {fmt_money(hi[1] - lo[1])}'
        cost_rows += (f'<tr><td><strong>{esc(label)}</strong><span class="m-sub">{esc(desc)}</span></td>'
                      f'<td class="num">{fmt_money(ca) if ca is not None else "n/a"}</td><td class="num">{fmt_money(cb) if cb is not None else "n/a"}</td><td>{diff}</td></tr>')
    cost_table = (f'<div class="table-wrap"><table class="table"><thead><tr><th>Workload (monthly)</th><th class="num">{A}</th><th class="num">{B}</th><th>Difference</th></tr></thead>'
                  f'<tbody>{cost_rows}</tbody></table></div>')

    def choose(m, other):
        items = []
        bf = [x for x in m.get("best_for", []) if x not in other.get("best_for", [])]
        if bf:
            items.append(f"you mainly need it for {', '.join(bf[:3])}, which {esc(m['provider_name'])} emphasizes for this model")
        if m["blended"] and other["blended"] and m["blended"] < other["blended"] * 0.95:
            items.append("cost per token is a deciding factor")
        if (m.get("context") or 0) > (other.get("context") or 0):
            items.append(f"you need more than {fmt_tokens(other.get('context'))} tokens of context in one request")
        if m["weights"] == "open" and other["weights"] != "open":
            items.append("you need to self-host, fine-tune or keep data inside your own network")
        if set(m.get("modalities_in", [])) - set(other.get("modalities_in", [])):
            extra = sorted(set(m["modalities_in"]) - set(other["modalities_in"]))
            items.append(f"your inputs include {', '.join(MOD_LABEL.get(x, x).lower() for x in extra)}")
        for s in m.get("strengths", [])[:2]:
            items.append(esc(s[0].lower() + s[1:]) if s else "")
        items = [i for i in items if i][:5]
        return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    shared = sorted(set(a.get("best_for", [])) & set(b.get("best_for", [])))
    shared_txt = f"Both are positioned for {', '.join(shared[:3])}." if shared else "Their providers position them for different jobs."
    take = (f"{shared_txt} On list price the gap is {('about ' + format(max(a['blended'], b['blended']) / min(a['blended'], b['blended']), '.1f') + '&times;') if a['blended'] and b['blended'] else 'unclear because one price is unpublished'}, "
            f"which matters most for high-volume, input-heavy workloads. Quality differences shift with every release, so treat this page as a shortlist tool: "
            f"run 20-50 of your real tasks through both, score the outputs, and divide the bill by the number of tasks each one got right.")

    faqs = []
    if a["blended"] and b["blended"]:
        ch = a if a["blended"] < b["blended"] else b
        faqs.append({"q": f"Which is cheaper, {a['name']} or {b['name']}?",
                     "a": f"{ch['name']} has the lower list price: {fmt_price(ch['price_in'])} input and {fmt_price(ch['price_out'])} output per million tokens, versus {fmt_price((b if ch is a else a)['price_in'])} and {fmt_price((b if ch is a else a)['price_out'])}. Discounts for caching and batch processing can change the real bill, so price your own token mix."})
    faqs.append({"q": f"Which has the bigger context window?",
                 "a": (f"{(cx or a)['name']} accepts {fmt_tokens((cx or a).get('context'))} tokens" + (f", compared with {fmt_tokens((b if cx is a else a).get('context'))} for {(b if cx is a else a)['name']}." if cx else f"; both models have the same limit."))})
    faqs.append({"q": f"Can I run {a['name']} or {b['name']} on my own hardware?",
                 "a": " ".join([f"{m['name']} {'is open-weight (' + (m.get('license') or 'open license') + '), so yes, with enough GPU memory.' if m['weights'] == 'open' else 'is closed, so only through hosted APIs.'}" for m in (a, b)])})
    faqs.append({"q": f"Is {a['name']} better than {b['name']}?",
                 "a": "It depends on the task. Public benchmarks and arena rankings move with every release and rarely match a specific workload. Use the specs here to shortlist, then test both on your own prompts and compare accuracy, latency and cost per correct answer."})

    content = (page_head(f"{A} vs {B}",
                         f"A side-by-side look at {A} from {esc(a['provider_name'])} and {B} from {esc(b['provider_name'])}: list prices, context windows, licensing and capabilities, with monthly costs worked out for three common workloads.",
                         [f"Data checked {fmt_date(UPDATED, True)}", f'<a href="compare.html?models={a["slug"]},{b["slug"]}">Open in the compare tool</a>']) +
               f'''<div class="wrap grid grid--sidebar"><div>
<section class="panel" aria-labelledby="quick"><h2 class="h3" id="quick">The short version</h2><ul style="margin-top:.6rem">{"".join(f"<li>{x}</li>" for x in bullets)}</ul></section>
<section aria-labelledby="specs" style="margin-top:2.5rem"><h2 class="h2" id="specs" style="margin-bottom:1rem">Specs side by side</h2>{spec_table}</section>
<section aria-labelledby="cost" style="margin-top:2.5rem"><h2 class="h2" id="cost" style="margin-bottom:1rem">What they cost for real workloads</h2>{cost_table}
<p class="small muted" style="margin-top:.6rem">Standard rates without caching or batch discounts. <a href="llm-cost-calculator.html?models={a["slug"]},{b["slug"]}">Try your own volumes</a>.</p></section>
{ad_slot("compare-mid", promo=0)}
<section class="pros-cons" style="margin-top:2.5rem" aria-label="When to choose each">
<div class="panel"><h2 class="h3">Choose {A} if</h2>{choose(a, b)}</div>
<div class="panel"><h2 class="h3">Choose {B} if</h2>{choose(b, a)}</div></section>
<section aria-labelledby="take" style="margin-top:2.5rem"><h2 class="h2" id="take" style="margin-bottom:.75rem">Our take</h2><p style="max-width:46rem">{take}</p>
<p style="max-width:46rem;margin-top:.75rem">Read the full profiles: {model_link(a)} and {model_link(b)}. For help designing that test, see <a href="llm-benchmarks-explained.html">how to read LLM benchmarks</a>.</p></section>
<div style="margin-top:2.5rem">{faq_html(faqs)}</div>
</div>
<aside class="aside-box"><h2 class="h3">More comparisons</h2><ul>{"".join(f'<li><a href="{cmp_slug(x, y)}.html">{esc(MODEL_BY[x]["name"])} vs {esc(MODEL_BY[y]["name"])}</a></li>' for x, y in COMPARISONS if (x, y) != (sa, sb))}</ul>
<p style="margin-top:1rem"><a class="btn btn--ghost btn--block" href="compare.html">Build your own comparison</a></p></aside></div>
<div class="wrap">{lead_band("choose", "choose-model", "cmp-" + sa)}</div>''')
    meta = {
        "slug": cmp_slug(sa, sb),
        "title": f"{a['name']} vs {b['name']}: Price, Context and Specs Compared",
        "description": f"{a['name']} vs {b['name']} compared: per-token prices, context windows, licensing and monthly costs for three real workloads. Data checked {fmt_date(UPDATED, True)}.",
        "section": "compare",
        "crumbs": [("Home", "index.html"), ("Compare", "compare.html"), (f"{a['name']} vs {b['name']}", None)],
        "schema": [faq_schema(faqs)],
        "priority": 0.7,
    }
    return meta, content


# ---------------------------------------------------------------- use-case hubs

def rank_key(m):
    return (m["status_rank"], m["tier_rank"], (m["blended"] if m["blended"] is not None else 99))


HUBS = [
    {
        "slug": "best-llms-for-coding", "short": "Coding",
        "title": "Best LLMs for Coding in 2026: Prices, Context and Licensing Compared",
        "h1": "Best LLMs for coding",
        "lede": "Every model in our directory that its provider positions for software work, from frontier models that refactor whole repositories to small open-weight models that autocomplete on a laptop.",
        "intro": ["Coding is where differences between models show up fastest. A stronger model fixes the bug on the first attempt; a weaker one spends tokens on retries. That makes list price a poor guide to cost per solved task, so treat this page as a shortlist and test the top candidates on issues from your own codebase.",
                  "Agentic coding tools send large contexts on every turn: whole files, test output, diffs and tool results. Input price and prompt caching usually matter more than output price, and a long context window keeps more of the repository in view."],
        "filter": lambda m: "coding" in m["best_for"],
        "choose": ["For multi-file changes, refactors and agents that run tests, start with frontier and advanced models that support tool calling and long context.",
                   "For inline completion and quick edits, latency beats peak quality: efficient and compact models answer faster and cost a fraction as much.",
                   "If code can't leave your network, shortlist open-weight models and size the hardware with the <a href=\"vram-calculator.html\">VRAM calculator</a>.",
                   "Check independent coding leaderboards such as <a href=\"https://www.swebench.com\" target=\"_blank\" rel=\"noopener\">SWE-bench</a> and <a href=\"https://aider.chat/docs/leaderboards/\" target=\"_blank\" rel=\"noopener\">Aider's leaderboards</a>, then confirm on your own tasks."],
        "faq": [{"q": "Which LLM is best for coding?", "a": "No single model wins every coding task. Frontier models generally handle complex, multi-file work best, while cheaper efficient models are often good enough for completions and small edits. Shortlist three models from this page and compare them on 20-50 real tasks from your repository, measuring solved tasks per dollar."},
                {"q": "Is a bigger context window better for coding?", "a": "It helps when an agent needs many files, logs and test output in view at once. But every token in the prompt is billed on every call, so good retrieval of relevant files and prompt caching usually save more money than simply sending the whole repository."},
                {"q": "Can I use an open-weight model for coding?", "a": "Yes. Several open-weight models in this list are positioned for coding and can run on your own servers, which keeps source code inside your network. Check the license and the GPU memory you need before you commit."}],
        "tools": ["llm-cost-calculator", "vram-calculator"], "guides": ["how-to-choose-an-llm", "ai-agents-explained"], "lead": "build",
    },
    {
        "slug": "best-llms-for-agents", "short": "Agents",
        "title": "Best LLMs for AI Agents: Tool Use, Context and Cost Compared",
        "h1": "Best LLMs for AI agents",
        "lede": "Models their providers position for agentic work: calling tools, following multi-step plans and recovering from errors over long sessions.",
        "intro": ["An agent multiplies whatever a model gets wrong. If each step succeeds 95% of the time, a 20-step task succeeds only about 36% of the time (0.95 to the 20th power), so reliability on tool calls and instruction following matters more than peak benchmark scores.",
                  "Long context lets an agent keep its plan, tool definitions and results in view, and prompt caching keeps that repeated material cheap. Price agents per completed task, not per token: a pricier model that finishes in fewer steps can cost less."],
        "filter": lambda m: "agents" in m["best_for"],
        "choose": ["Require native tool calling and structured outputs; check the model page for both.",
                   "Prefer models with prompt caching when your system prompt and tool list are long.",
                   "Measure cost per finished task, including retries, rather than cost per token.",
                   "Give agents least-privilege tools and a human approval step for anything irreversible. See <a href=\"llm-security-and-privacy.html\">LLM security and privacy</a>."],
        "faq": [{"q": "What makes an LLM good for agents?", "a": "Dependable tool calling, accurate instruction following over many steps, the ability to recover from errors, and enough context to hold the plan and tool results. Cost per completed task and latency per step also matter because agents make many calls."},
                {"q": "Do I need a reasoning model for agents?", "a": "Not always. Reasoning modes help with planning and tricky steps but add output tokens and latency. Many teams use a reasoning model to plan and a cheaper fast model to execute routine steps."},
                {"q": "Which framework should I use to build an agent?", "a": "Start with your provider's agent SDK or a lightweight framework, and add orchestration only when you need it. Our guide to AI agents compares the main options and when a simple workflow beats a full agent."}],
        "tools": ["llm-cost-calculator", "llm-picker"], "guides": ["ai-agents-explained", "llm-security-and-privacy"], "lead": "build",
    },
    {
        "slug": "best-llms-for-long-documents", "short": "Long documents",
        "title": "Best LLMs for Long Documents: 1M-Token Context Windows Compared",
        "h1": "Best LLMs for long documents",
        "lede": "Models with a context window of at least 1 million tokens, or that their providers position for long-document work.",
        "intro": ["A 1M-token window holds roughly 750,000 words: a stack of contracts, several long books or a mid-size codebase in a single request. That makes whole-document analysis possible without building a retrieval pipeline first.",
                  "A big window isn't free. You pay for every input token on every call, many providers charge higher rates once a prompt passes a threshold, and accuracy on details buried in the middle of a long prompt varies by model. If you only need a few passages, retrieval (RAG) is usually cheaper and more precise."],
        "filter": lambda m: (m.get("context") or 0) >= 1_000_000 or "long documents" in m["best_for"],
        "choose": ["Check the long-context surcharge in each model's price note before you send 500K-token prompts.",
                   "Use prompt caching when you ask many questions about the same document.",
                   "Test recall on your own documents: plant a few facts deep in the text and check that the model finds them.",
                   "Compare against a RAG setup; see <a href=\"rag-explained.html\">RAG explained</a> and <a href=\"context-windows-explained.html\">context windows explained</a>."],
        "faq": [{"q": "How many pages fit in a 1M-token context window?", "a": "Roughly 1,500 pages of plain English text, using the rule of thumb of 0.75 words per token and 500 words per page. Tables, code and non-English text use more tokens per page, so the real number is often lower."},
                {"q": "Is long context better than RAG?", "a": "For questions that need the whole document, such as summarizing a contract or comparing chapters, long context is simpler. For finding specific facts across a large or changing collection, RAG is usually cheaper, faster and easier to keep current. Many production systems combine both."}],
        "tools": ["context-window-visualizer", "token-counter"], "guides": ["context-windows-explained", "rag-explained"], "lead": "build",
    },
    {
        "slug": "cheapest-llm-apis", "short": "Cheapest APIs",
        "title": "Cheapest LLM APIs in 2026: Models Ranked by Price per Token",
        "h1": "Cheapest LLM APIs",
        "lede": "Current models with published list prices, ranked by blended price: three parts input to one part output, in US dollars per million tokens.",
        "intro": ["A blended price makes models with different input and output rates comparable at a glance. Your real ratio may differ: chat and retrieval apps are input-heavy, while content generation and reasoning are output-heavy, so check both columns.",
                  "Discounts can reorder this list. Batch APIs commonly halve prices for work that can wait, cached input often costs a tenth of normal input, and some providers charge more for very long prompts or less at off-peak hours. The calculator applies your own mix."],
        "filter": lambda m: m["blended"] is not None and m["status"] != "legacy",
        "sort": lambda m: m["blended"],
        "limit": 30,
        "choose": ["Pick the cheapest model that passes your quality bar on real tasks; the cheapest overall rarely does.",
                   "Route easy requests to a small model and hard ones to a larger model.",
                   "Turn on prompt caching for repeated system prompts and documents.",
                   "Use batch processing for anything that doesn't need an answer in seconds."],
        "faq": [{"q": "What is the cheapest LLM API?", "a": "On blended list price, the top of this table is the cheapest as of the date shown. Small open-weight models served by inference providers and the lightest models from major labs usually lead. The cheapest model that handles your task reliably is often a different one, so test before you switch."},
                {"q": "Why does output cost more than input?", "a": "Generating each output token takes a full pass through the model, one token at a time, while input tokens are processed in parallel. That makes output more expensive to serve, and providers price it accordingly, typically several times the input rate."}],
        "tools": ["llm-cost-calculator", "self-host-vs-api-calculator"], "guides": ["llm-api-pricing-explained", "how-to-choose-an-llm"], "lead": "costs",
    },
    {
        "slug": "longest-context-llms", "short": "Longest context",
        "title": "LLMs With the Longest Context Windows (2026)",
        "h1": "LLMs with the longest context windows",
        "lede": "Every model we track, sorted by the maximum number of tokens it accepts in one request.",
        "intro": ["Context windows grew from a few thousand tokens in 2022 to a million or more for many current models. The limit covers your prompt, any documents or conversation history you include, and often the response.",
                  "The advertised limit is a ceiling, not a guarantee of quality across the whole window. Accuracy on facts deep inside long prompts varies, and long prompts cost more and take longer to process."],
        "filter": lambda m: bool(m.get("context")) and m["status"] != "legacy",
        "sort": lambda m: (-(m.get("context") or 0), m["tier_rank"]),
        "limit": 30,
        "choose": ["Check the maximum output separately: a huge input window can still come with a modest output limit.",
                   "Look for long-context surcharges in the price notes.",
                   "Use the <a href=\"context-window-visualizer.html\">context window visualizer</a> to see what fits."],
        "faq": [{"q": "Which LLM has the largest context window?", "a": "The model at the top of this table has the largest advertised window among the current models we track. Very large windows exist mainly on a few models; most current frontier models offer around 1 million tokens."},
                {"q": "Does a bigger context window make a model smarter?", "a": "No. It only lets the model see more text at once. Quality on long inputs depends on how the model was trained and evaluated for long context, so test with your own documents."}],
        "tools": ["context-window-visualizer", "token-counter"], "guides": ["context-windows-explained", "rag-explained"], "lead": "build",
    },
    {
        "slug": "best-open-weight-llms", "short": "Open weights",
        "title": "Best Open-Weight LLMs in 2026: Licenses, Sizes and Prices",
        "h1": "Best open-weight LLMs",
        "lede": "Current models whose weights you can download, sorted by capability tier, with licenses and sizes spelled out.",
        "intro": ["Open weights give you control: run the model in your own cloud or data center, fine-tune it, and keep sensitive data inside your network. You can also buy the same model from several inference providers, which keeps prices competitive.",
                  "Open weights don't always mean open source. Some licenses cap revenue, require attribution, restrict serving the model to others or forbid certain uses. Read the license on the model page before you build a product on it."],
        "filter": lambda m: m["weights"] == "open" and m["status"] != "legacy",
        "choose": ["Match model size to your hardware: the weights alone need about 0.6 GB per billion parameters at 4-bit.",
                   "Check the license for commercial limits, especially for the largest releases.",
                   "Compare hosted prices for the same open model across inference providers.",
                   "Read <a href=\"open-source-vs-closed-llms.html\">open-source vs closed LLMs</a> for the full trade-off."],
        "faq": [{"q": "What is the best open-weight LLM?", "a": "The frontier-tier models at the top of this list are the most capable open releases we track, but they need multi-GPU servers. For a single GPU or a laptop, the efficient and compact models are the practical choice. The best one is the most capable model that fits your hardware and license needs."},
                {"q": "Are open-weight models free to use commercially?", "a": "Many are, under licenses such as Apache 2.0 or MIT. Others use custom licenses with revenue caps, attribution rules or extra terms for large service providers. The license name is listed for every model here; read the full text before commercial use."}],
        "tools": ["vram-calculator", "self-host-vs-api-calculator"], "guides": ["open-source-vs-closed-llms", "run-llms-locally"], "lead": "local",
    },
    {
        "slug": "llms-you-can-run-locally", "short": "Run locally",
        "title": "LLMs You Can Run Locally: Models That Fit a GPU or a Mac",
        "h1": "LLMs you can run locally",
        "lede": "Open-weight models small enough to run on a single consumer GPU, a workstation card or a high-memory Mac, with the memory each one needs.",
        "intro": ["Running a model on your own machine keeps data private, works offline and costs nothing per token once you own the hardware. The limit is memory: the weights must fit in GPU memory (or Apple unified memory), with room left for the KV cache.",
                  "Memory figures below are for the weights at 4-bit quantization (about 4.85 bits per weight), the most common setting for local use. Higher precision roughly doubles (8-bit) or quadruples (16-bit) the requirement."],
        "filter": lambda m: m["weights"] == "open" and m["status"] != "legacy" and (m.get("params_total_b") or 999) <= 130,
        "sort": lambda m: (m.get("params_total_b") or 999),
        "local": True,
        "choose": ["8-12 GB GPUs: models up to about 8B parameters at 4-bit.",
                   "16-24 GB GPUs: up to roughly 30B at 4-bit with a moderate context.",
                   "Macs with 64-128 GB of unified memory: up to about 120B mixture-of-experts models at 4-bit.",
                   "Size a specific setup with the <a href=\"vram-calculator.html\">VRAM calculator</a> and follow <a href=\"run-llms-locally.html\">our guide to running LLMs locally</a>."],
        "faq": [{"q": "What is the best LLM to run locally?", "a": "The best local model is the most capable one that fits your memory with room for context. On a 24 GB GPU that's usually a model of around 20-30B parameters at 4-bit; on a 128 GB Mac, mixture-of-experts models above 100B become practical."},
                {"q": "How much RAM do I need to run an LLM?", "a": "For GPU inference, count GPU memory: about 0.6 GB per billion parameters at 4-bit for the weights, plus the KV cache. On Apple Silicon, the GPU can use most of the unified memory, so a 32 GB Mac comfortably runs models in the 8-14B range."}],
        "tools": ["vram-calculator", "self-host-vs-api-calculator"], "guides": ["run-llms-locally", "open-source-vs-closed-llms"], "lead": "local",
    },
    {
        "slug": "multimodal-llms", "short": "Multimodal",
        "title": "Multimodal LLMs: Models That Read Images, Audio, Video and PDFs",
        "h1": "Multimodal LLMs",
        "lede": "Models that accept more than text: images, audio, video or PDF files, sorted by tier and price.",
        "intro": ["Multimodal models read screenshots, charts, scanned documents and photos directly, and some handle audio or video. That replaces separate OCR or transcription steps in many workflows.",
                  "Media inputs are billed as tokens too, and an image or a minute of video can cost far more than a paragraph of text. Check how each provider converts media to tokens before you process large volumes."],
        "filter": lambda m: m["status"] != "legacy" and len(set(m.get("modalities_in", [])) - {"text"}) > 0,
        "multimodal": True,
        "choose": ["Need charts, screenshots or scans? Any model with image input works; test on your own documents.",
                   "Need audio or video understanding? Only a few models accept them natively; see the input column.",
                   "For PDFs, check whether the model reads pages as images (layout-aware) or as extracted text."],
        "faq": [{"q": "What is a multimodal LLM?", "a": "A multimodal LLM accepts inputs other than text, such as images, audio, video or documents, and reasons over them together with your text prompt. Most still output text, though some can also generate images or speech."},
                {"q": "Which LLMs can watch video?", "a": "Only some models accept video input natively. In our directory, the input column shows which ones; others need you to extract frames or a transcript first."}],
        "tools": ["llm-cost-calculator", "llm-picker"], "guides": ["what-is-a-large-language-model", "how-to-choose-an-llm"], "lead": "build",
    },
    {
        "slug": "reasoning-models", "short": "Reasoning",
        "title": "Reasoning Models: LLMs With a Thinking Mode, Compared",
        "h1": "Reasoning models",
        "lede": "Models with a reasoning or thinking mode: they work through a problem in extra tokens before they answer.",
        "intro": ["Reasoning models trade speed and tokens for accuracy on multi-step problems such as math, planning, tricky code and analysis. Most let you set an effort level, so you pay for deep thinking only when the task needs it.",
                  "Reasoning tokens are usually billed as output tokens, and output is the expensive side of the bill. A hard question can cost several times a direct answer, so measure accuracy gained per dollar on your own tasks."],
        "filter": lambda m: m.get("reasoning") and m["status"] != "legacy",
        "choose": ["Use high effort for hard, high-value questions and low or no reasoning for routine ones.",
                   "Set a budget for thinking tokens where the API supports it.",
                   "Ask for the final answer in a structured format so it's easy to validate.",
                   "Prompting advice differs for reasoning models; see <a href=\"prompt-engineering-guide.html\">the prompt engineering guide</a>."],
        "faq": [{"q": "What is a reasoning model?", "a": "A reasoning model is trained to produce an internal chain of reasoning before its final answer, often with reinforcement learning on problems that have checkable answers. It tends to do better on math, logic, planning and complex code, at the cost of more tokens and latency."},
                {"q": "Are reasoning tokens billed?", "a": "On most APIs, yes: thinking tokens count as output tokens even when you don't see them. Check each provider's pricing page and set an effort level or thinking budget to control cost."}],
        "tools": ["llm-cost-calculator", "llm-picker"], "guides": ["how-llms-work", "prompt-engineering-guide"], "lead": "choose",
    },
    {
        "slug": "best-llms-for-customer-support", "short": "Customer support",
        "title": "Best LLMs for Customer Support: Fast, Cheap Models Compared",
        "h1": "Best LLMs for customer support",
        "lede": "Efficient models that are positioned for high-volume, low-latency work such as support chat, ticket triage and routing.",
        "intro": ["Support bots answer similar questions all day, so cost per conversation and response time matter more than peak intelligence. A 30,000-conversation month can cost a few dollars or a few hundred depending on the model.",
                  "Accuracy comes mostly from grounding: retrieving the right help-center articles and policies and instructing the model to answer only from them. Pair a fast model for routine questions with a stronger one for escalations."],
        "filter": lambda m: m["status"] != "legacy" and m["tier"] in ("efficient", "compact", "advanced") and (set(m["best_for"]) & {"customer support", "high volume", "low latency", "chat"}),
        "sort": lambda m: (m["blended"] if m["blended"] is not None else 99),
        "choose": ["Ground answers in your knowledge base with retrieval and citations; see <a href=\"rag-explained.html\">RAG explained</a>.",
                   "Keep humans in the loop for refunds, legal and safety questions.",
                   "Measure resolution rate and escalation rate, not just cost.",
                   "Watch for prompt injection from customer messages; see <a href=\"llm-security-and-privacy.html\">LLM security</a>."],
        "faq": [{"q": "Which LLM is best for customer service?", "a": "Usually a fast, inexpensive model grounded in your own help content, with escalation to a stronger model or a human for complex cases. Start with the efficient models in this list and compare resolution rates on a sample of real tickets."},
                {"q": "How much does an AI support bot cost to run?", "a": "At list prices, a month of 30,000 conversations with about 2,000 input and 400 output tokens each costs from a few dollars on the cheapest models to a few hundred on frontier models. The calculator works it out for your volumes."}],
        "tools": ["llm-cost-calculator", "llm-picker"], "guides": ["rag-explained", "llm-hallucinations"], "lead": "build",
    },
]
HUB_BY = {h["slug"]: h for h in HUBS}


def hub_rows(ms, local=False):
    rows = ""
    for m in ms:
        extra = ""
        if local:
            extra = f'<td class="num">{weights_gb(m["params_total_b"], 4.85):,.0f} GB</td>'
        rows += (f'<tr><td class="m-name">{model_link(m)}<span class="m-sub">{esc(m["provider_name"])}</span></td>'
                 f'<td>{tier_tag(m)}</td><td>{badge_weights(m)}</td>'
                 f'<td class="num">{fmt_tokens(m.get("context"))}</td>{extra}'
                 f'<td class="num">{fmt_price(m.get("price_in"))}</td><td class="num">{fmt_price(m.get("price_out"))}</td>'
                 f'<td class="small">{esc(", ".join(MOD_LABEL.get(x, x) for x in m.get("modalities_in", [])))}</td></tr>')
    head_extra = '<th class="num">Weights at 4-bit</th>' if local else ""
    return (f'<div class="table-wrap"><table class="table"><thead><tr><th>Model</th><th>Tier</th><th>Weights</th><th class="num">Context</th>{head_extra}'
            f'<th class="num">Input / 1M</th><th class="num">Output / 1M</th><th>Inputs</th></tr></thead><tbody>{rows}</tbody></table></div>')


def hub_page(h):
    ms = [m for m in MODELS if h["filter"](m)]
    ms.sort(key=h.get("sort", rank_key))
    if h.get("limit"):
        ms = ms[:h["limit"]]
    if h.get("local"):
        small = [m for m in ms if m["params_total_b"] <= 36]
        big = [m for m in ms if m["params_total_b"] > 36]
        table = (f'<h2 class="h3" style="margin:0 0 .75rem">Fits a single consumer GPU or a 32 GB+ Mac (about 36B parameters or fewer)</h2>{hub_rows(small, True)}'
                 f'<h2 class="h3" style="margin:2rem 0 .75rem">Needs a workstation GPU, two GPUs or a 64-128 GB Mac</h2>{hub_rows(big, True)}')
    else:
        table = hub_rows(ms)
    intro = "".join(f'<p style="max-width:46rem;margin-top:.9rem">{esc(p)}</p>' for p in h["intro"])
    choose = "".join(f"<li>{c}</li>" for c in h["choose"])
    tools = "".join(f'<li><a href="{t}.html">{esc(TOOL_BY[t]["name"])}</a></li>' for t in h["tools"])
    guides = "".join(f'<li><a href="{g}.html">{esc(GUIDE_BY[g]["h1"])}</a></li>' for g in h["guides"])
    others = '<div class="pill-nav">' + "".join(f'<a href="{x["slug"]}.html">{esc(x["short"])}</a>' for x in HUBS if x["slug"] != h["slug"]) + "</div>"
    content = (page_head(esc(h["h1"]), esc(h["lede"]), [f"{len(ms)} models", f"Data checked {fmt_date(UPDATED, True)}"]) +
               f'''<div class="wrap grid grid--sidebar"><div>
<section aria-label="Introduction">{intro}</section>
<section aria-labelledby="list" style="margin-top:2rem"><h2 class="h2" id="list" style="margin-bottom:1rem">The shortlist</h2>{table}
<p class="small muted" style="margin-top:.6rem">Ordered by {"blended list price" if h["slug"] == "cheapest-llm-apis" else ("context window" if h["slug"] == "longest-context-llms" else ("size" if h.get("local") else "status, capability tier and then price"))}. Tiers are our editorial grouping of provider positioning and public benchmark standings, not our own test results. <a href="editorial-policy.html#rankings">How we rank</a>.</p></section>
{ad_slot("hub-mid", promo=3)}
<section aria-labelledby="choose" style="margin-top:2.5rem"><h2 class="h2" id="choose" style="margin-bottom:.75rem">How to choose</h2><ul style="max-width:46rem">{choose}</ul></section>
<div style="margin-top:2.5rem">{faq_html(h["faq"])}</div>
</div>
<aside class="aside-box"><h2 class="h3">Tools for this</h2><ul>{tools}</ul><h2 class="h3" style="margin-top:1rem">Read next</h2><ul>{guides}</ul>
<p style="margin-top:1rem"><a class="btn btn--ghost btn--block" href="models.html">Filter the full directory</a></p></aside></div>
<div class="wrap" style="margin-top:2.5rem"><h2 class="h3" style="margin-bottom:.75rem">Other shortlists</h2>{others}</div>
<div class="wrap">{lead_band(h["lead"], "", "hub-" + h["slug"])}</div>''')
    meta = {"slug": h["slug"], "title": h["title"],
            "description": (h["lede"] + f" {len(ms)} models, data checked {fmt_date(UPDATED, True)}.")[:300],
            "section": "models", "crumbs": [("Home", "index.html"), ("Models", "models.html"), (h["h1"], None)],
            "schema": [faq_schema(h["faq"]), {"@type": "ItemList", "name": h["h1"], "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": SITE["site_url"] + "/" + m["url_page"], "name": m["name"]} for i, m in enumerate(ms[:20])]}],
            "priority": 0.8}
    return meta, content


# ---------------------------------------------------------------- directory, snapshots

def directory_table():
    rows = ""
    for m in sorted(MODELS, key=rank_key):
        mi = " ".join(m.get("modalities_in", []))
        rows += (f'<tr data-slug="{m["slug"]}" data-provider="{m["provider"]}" data-weights="{m["weights"]}" data-tier="{m["tier"]}" '
                 f'data-status="{m["status"]}" data-mods="{mi}" data-reasoning="{1 if m.get("reasoning") else 0}" '
                 f'data-ctx="{m.get("context") or 0}" data-in="{m["price_in"] if m.get("price_in") is not None else ""}" '
                 f'data-out="{m["price_out"] if m.get("price_out") is not None else ""}" data-released="{date_sort_key(m["released"])}" '
                 f'data-name="{esc(m["name"].lower())}" data-tags="{esc(" ".join(m.get("best_for", [])))}" data-tierrank="{m["tier_rank"]}">'
                 f'<td><input type="checkbox" class="cmp-check" aria-label="Select {esc(m["name"])} to compare" value="{m["slug"]}"></td>'
                 f'<td class="m-name">{model_link(m)}<span class="m-sub">{esc(m["provider_name"])}</span></td>'
                 f'<td>{badge_status(m)}</td><td>{badge_weights(m)}</td><td>{tier_tag(m)}</td>'
                 f'<td class="num">{fmt_tokens(m.get("context"))}</td><td class="num">{fmt_price(m.get("price_in"))}</td>'
                 f'<td class="num">{fmt_price(m.get("price_out"))}</td><td class="small">{esc(", ".join(MOD_LABEL.get(x, x) for x in m.get("modalities_in", [])))}</td>'
                 f'<td class="nowrap small">{fmt_date(m["released"])}</td></tr>')
    return (f'<div class="table-wrap"><table class="table" id="dir-table"><thead><tr><th><span class="visually-hidden">Compare</span></th>'
            f'<th aria-sort="none"><button class="sort" type="button" data-sort="name">Model</button></th><th>Status</th><th>Weights</th>'
            f'<th aria-sort="none"><button class="sort" type="button" data-sort="tierrank">Tier</button></th>'
            f'<th class="num" aria-sort="none"><button class="sort" type="button" data-sort="ctx">Context</button></th>'
            f'<th class="num" aria-sort="none"><button class="sort" type="button" data-sort="in">Input / 1M</button></th>'
            f'<th class="num" aria-sort="none"><button class="sort" type="button" data-sort="out">Output / 1M</button></th>'
            f'<th>Inputs</th><th aria-sort="none"><button class="sort" type="button" data-sort="released">Released</button></th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def directory_filters():
    prov = "".join(f'<option value="{p["slug"]}">{esc(p["name"])} ({len(p["models"])})</option>'
                   for p in sorted(PROVIDERS.values(), key=lambda p: p["name"].lower()))
    def chips(group, items):
        return "".join(f'<button type="button" class="chip-toggle" data-filter="{group}" data-value="{v}" aria-pressed="false">{esc(l)}</button>' for v, l in items)
    return f'''<div class="filters" id="dir-filters">
  <div class="filters__top">
    <label class="visually-hidden" for="dir-q">Search models</label>
    <input class="input" id="dir-q" type="search" placeholder="Search by model, provider or use case" autocomplete="off">
    <label class="visually-hidden" for="dir-provider">Provider</label>
    <select class="select" id="dir-provider" style="width:auto;min-width:12rem"><option value="">All providers</option>{prov}</select>
    <button type="button" class="btn btn--ghost btn--sm" id="dir-reset">Reset</button>
  </div>
  <div class="filter-groups">
    <div class="filter-group"><span class="fg-label">Weights</span><div class="tags">{chips("weights", [("open", "Open"), ("closed", "Closed")])}</div></div>
    <div class="filter-group"><span class="fg-label">Tier</span><div class="tags">{chips("tier", [("frontier", "Frontier"), ("advanced", "Advanced"), ("efficient", "Efficient"), ("compact", "Compact")])}</div></div>
    <div class="filter-group"><span class="fg-label">Status</span><div class="tags">{chips("status", [("current", "Current"), ("preview", "Preview"), ("legacy", "Legacy")])}</div></div>
    <div class="filter-group"><span class="fg-label">Inputs</span><div class="tags">{chips("mods", [("image", "Images"), ("audio", "Audio"), ("video", "Video"), ("pdf", "PDF")])}</div></div>
    <div class="filter-group"><span class="fg-label">Capabilities</span><div class="tags">{chips("reasoning", [("1", "Reasoning mode")])}{chips("ctx", [("1000000", "1M+ context")])}</div></div>
  </div>
  <p class="result-count" id="dir-count" aria-live="polite">{len(MODELS)} models</p>
</div>'''


def hub_pills():
    return '<div class="pill-nav">' + "".join(f'<a href="{h["slug"]}.html">{esc(h["short"])}</a>' for h in HUBS) + "</div>"


def snapshot_table(n=10):
    ms = sorted([m for m in MODELS if m["status"] == "current" and m["tier"] in ("frontier", "advanced")],
                key=lambda m: date_sort_key(m["released"]), reverse=True)[:n]
    rows = "".join(
        f'<tr><td class="m-name">{model_link(m)}<span class="m-sub">{esc(m["provider_name"])}</span></td><td>{badge_weights(m)}</td>'
        f'<td class="num">{fmt_tokens(m.get("context"))}</td><td class="num">{fmt_price(m.get("price_in"))}</td>'
        f'<td class="num">{fmt_price(m.get("price_out"))}</td><td class="num">{fmt_money(scenario_cost(m, 30000, 2000, 400))}</td></tr>' for m in ms)
    return (f'<div class="table-wrap"><table class="table"><thead><tr><th>Model</th><th>Weights</th><th class="num">Context</th>'
            f'<th class="num">Input / 1M</th><th class="num">Output / 1M</th><th class="num">Support bot, per month*</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="small muted" style="margin-top:.6rem">*30,000 conversations of 2,000 input and 400 output tokens at list price. Frontier and advanced models, newest first.</p>')


def releases_strip(n=6):
    ms = sorted([m for m in MODELS if m["status"] != "legacy"], key=lambda m: date_sort_key(m["released"]), reverse=True)[:n]
    return '<ul class="releases">' + "".join(
        f'<li><a href="{m["url_page"]}"><span class="r-name">{esc(m["name"])}</span><span class="r-meta">{esc(m["provider_name"])}, {fmt_date(m["released"])}</span></a></li>' for m in ms) + "</ul>"


# ---------------------------------------------------------------- rankings

def index_scores(weights, models=None):
    ms = [m for m in (models or MODELS) if m["status"] != "legacy" and m["blended"]]
    lp = [math.log(m["blended"]) for m in ms]
    lc = [math.log(m["context"]) for m in ms if m.get("context")]
    dts = [date_sort_key(m["released"]) for m in ms]
    dmin, dmax = min(dts), max(dts)
    def dnum(d):
        y, mo, da = (int(x) for x in d.split("-"))
        return y * 372 + mo * 31 + da
    n0, n1 = dnum(dmin), dnum(dmax)
    tier_s = {"frontier": 1.0, "advanced": 0.75, "efficient": 0.5, "compact": 0.3}
    out = []
    for m in ms:
        s = {
            "capability": tier_s[m["tier"]] + (0.05 if m.get("reasoning") else 0),
            "price": 1 - (math.log(m["blended"]) - min(lp)) / ((max(lp) - min(lp)) or 1),
            "context": ((math.log(m["context"]) - min(lc)) / ((max(lc) - min(lc)) or 1)) if m.get("context") else 0,
            "openness": 1.0 if m["weights"] == "open" else 0.0,
            "multimodal": min(1.0, len(set(m.get("modalities_in", [])) - {"text"}) / 3),
            "recency": (dnum(date_sort_key(m["released"])) - n0) / ((n1 - n0) or 1),
        }
        tot = sum(weights.values()) or 1
        score = sum(weights[k] * min(1.0, s[k]) for k in weights) / tot * 100
        out.append((m, score))
    out.sort(key=lambda x: -x[1])
    return out


DEFAULT_WEIGHTS = {"capability": 40, "price": 25, "context": 10, "openness": 10, "multimodal": 5, "recency": 10}


def ranking_list(n=25):
    items = ""
    for m, sc in index_scores(DEFAULT_WEIGHTS)[:n]:
        items += (f'<li><span class="rk-name">{model_link(m)}<small>{esc(m["provider_name"])}, {TIER_LABEL[m["tier"]]}, {fmt_price(m["price_in"])} / {fmt_price(m["price_out"])}</small></span>'
                  f'<span class="b-track" style="height:12px;border-radius:3px;background:var(--surface-2);overflow:hidden;display:block"><span class="b-fill" style="display:block;height:100%;width:{sc:.0f}%;background:var(--v4)"></span></span>'
                  f'<span class="rk-score">{sc:.0f}</span></li>')
    return f'<ol class="rank" id="rank-list">{items}</ol>'


# ---------------------------------------------------------------- timeline

TL_COLORS = {"research": "var(--v2)", "model": "var(--v4)", "open-weights": "var(--v6)", "product": "var(--v0)", "policy": "var(--v8)"}
TL_LABEL = {"research": "Research", "model": "Model release", "open-weights": "Open weights", "product": "Product", "policy": "Policy"}


def timeline_html(events=None):
    events = sorted(events or TIMELINE, key=lambda e: date_sort_key(e["date"]))
    out, year = "", None
    for e in events:
        y = e["date"][:4]
        if y != year:
            if year:
                out += "</ol>"
            out += f'<h2 class="tl-year" id="y{y}">{y}</h2><ol class="timeline">'
            year = y
        out += (f'<li style="--c:{TL_COLORS.get(e["type"], "var(--v4)")}"><div class="tl-date">{fmt_date(e["date"])}</div>'
                f'<div><div class="tl-title"><a href="{esc(e["url"])}" target="_blank" rel="noopener">{esc(e["title"])}</a></div>'
                f'<p class="tl-note">{esc(e["note"])}</p><p class="tl-org">{esc(e["org"])}, {TL_LABEL.get(e["type"], e["type"])}</p></div></li>')
    return out + "</ol>"


def timeline_teaser(n=6):
    events = sorted(TIMELINE, key=lambda e: date_sort_key(e["date"]))[-n:][::-1]
    return '<ol class="timeline">' + "".join(
        f'<li style="--c:{TL_COLORS.get(e["type"], "var(--v4)")}"><div class="tl-date">{fmt_date(e["date"])}</div>'
        f'<div><div class="tl-title">{esc(e["title"])}</div><p class="tl-note">{esc(e["note"])}</p></div></li>' for e in events) + "</ol>"
