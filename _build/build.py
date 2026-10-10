#!/usr/bin/env python3
"""Build LLModel.com: renders every page into the repository root.

Usage:
    python3 _build/build.py            # build the site
    python3 _build/tests/qa.py         # then run the checks
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.common import (ROOT, SRC, SITE, UPDATED, MODELS, PROVIDERS, GUIDES, GLOSSARY, VIDEOS, PROMPTS, RESOURCES, TIMELINE,
                        TOOLS, TOOL_BY, esc, read_src, page_html, page_head, ad_slot, lead_band, newsletter_box, faq_html,
                        faq_schema, externalize, wrap_tables, fmt_date, fmt_tokens, fmt_price, ICONS)
from lib import datapages as dp
from lib import contentpages as cp

KV_NOTES = {
    "hybrid": "Mixes sliding-window or linear-attention layers with full-attention layers, so its KV cache is much smaller than the standard estimate.",
    "latent": "Uses compressed (latent) attention, so its KV cache is much smaller than the standard estimate.",
    "ssm": "Mostly state-space (Mamba) layers: only a few layers keep a KV cache.",
}
KV_ADJUST = {
    "llama-4-maverick": ("hybrid", 0.25), "llama-4-scout": ("hybrid", 0.25), "muse-glimmer-30b": ("hybrid", 0.25),
    "mistral-large-3": ("latent", 0.012), "mistral-small-4": ("latent", 0.05), "glm-5-3": ("latent", 0.023),
    "deepseek-v4-1-flash": ("latent", 0.5), "deepseek-v4-pro": ("latent", 0.5),
    "qwen3-8-2-4t-a95b": ("hybrid", 0.25), "qwen3-8-27b": ("hybrid", 0.25), "qwen3-6-35b-a3b": ("hybrid", 0.25),
    "gemma-4-31b": ("hybrid", 0.2), "gemma-4-26b-a4b": ("hybrid", 0.2), "gemma-4-e4b": ("hybrid", 0.2),
    "gpt-oss-120b": ("hybrid", 0.5), "gpt-oss-20b": ("hybrid", 0.5),
    "nemotron-3-ultra": ("ssm", 0.11), "nemotron-3-5-lightning-30b-a3b": ("ssm", 0.11),
    "olmo-3-1-32b-think": ("hybrid", 0.25),
}


# ---------------------------------------------------------------- placeholders

def tools_index():
    return '<ul class="tool-index">' + "".join(
        f'<li><a href="{t["slug"]}.html"><span class="ti-ico">{ICONS[t["icon"]]}</span><span><span class="ti-name">{esc(t["name"])}</span>'
        f'<span class="ti-desc">{esc(t["desc"])}</span></span></a></li>' for t in TOOLS) + "</ul>"


def compare_popular(limit=None):
    pairs = dp.COMPARISONS[:int(limit)] if limit else dp.COMPARISONS
    return '<ul class="rowlist">' + "".join(
        f'<li><a class="row" href="{dp.cmp_slug(a, b)}.html"><span class="row__title">{esc(dp.MODEL_BY[a]["name"])} vs {esc(dp.MODEL_BY[b]["name"])}</span>'
        f'<span class="row__desc">{esc(dp.MODEL_BY[a]["provider_name"])} vs {esc(dp.MODEL_BY[b]["provider_name"])}: prices, context and costs for three workloads</span>'
        f'<span class="row__meta">{fmt_price(dp.MODEL_BY[a]["price_in"])} vs {fmt_price(dp.MODEL_BY[b]["price_in"])} input</span></a></li>' for a, b in pairs) + "</ul>"


def counts():
    return {
        "models_count": str(len(MODELS)),
        "providers_count": str(len(PROVIDERS)),
        "open_count": str(sum(1 for m in MODELS if m["weights"] == "open")),
        "guides_count": str(len(GUIDES)),
        "terms_count": str(len(GLOSSARY)),
        "videos_count": str(len(VIDEOS)),
        "prompts_count": str(len(PROMPTS)),
        "resources_count": str(len(RESOURCES["items"])),
        "timeline_count": str(len(TIMELINE)),
        "updated_human": SITE["updated_human"],
        "comparisons_count": str(len(dp.COMPARISONS)),
    }


PH_RE = re.compile(r"\{\{([a-z_]+)(?::([^}]*))?\}\}")


def render_body(body, meta):
    state = {"ad": 0}
    c = counts()

    def rep(m):
        name, arg = m.group(1), m.group(2)
        if name in c:
            return c[name]
        if name == "ad":
            state["ad"] += 1
            return ad_slot(arg or "content", ads=meta.get("ads", True), promo=state["ad"] + len(meta["slug"]))
        if name == "lead":
            parts = (arg or "default").split(",")
            return lead_band(parts[0], parts[1] if len(parts) > 1 else "", meta["slug"])
        if name == "newsletter":
            return newsletter_box("nl-" + meta["slug"] + (arg or ""))
        if name == "faq":
            return faq_html(meta.get("faq", []))
        if name == "releases":
            return dp.releases_strip()
        if name == "snapshot":
            return dp.snapshot_table()
        if name == "tools_index":
            return tools_index()
        if name == "guides_featured":
            return cp.guides_featured()
        if name == "videos":
            a = (arg or "3").split(",")
            return cp.video_grid(a[0], a[1] if len(a) > 1 else None)
        if name == "timeline_teaser":
            return dp.timeline_teaser()
        if name == "directory":
            return dp.directory_filters() + dp.directory_table()
        if name == "hub_pills":
            return dp.hub_pills()
        if name == "ranking":
            return dp.ranking_list()
        if name == "compare_popular":
            return compare_popular(arg)
        if name == "glossary_spotlight":
            return cp.glossary_spotlight()
        if name == "leaderboard_links":
            return cp.leaderboard_links()
        if name == "honeypot":
            return '<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
        raise KeyError(f"unknown placeholder {{{{{name}}}}} in {meta['slug']}")

    return PH_RE.sub(rep, body)


def authored_pages():
    out = []
    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = read_src(f)
        meta.setdefault("slug", f.stem)
        content = render_body(body, meta)
        content = wrap_tables(externalize(content)) if meta.get("prose") else externalize(content)
        if not meta.get("custom_head"):
            items = meta.get("head_meta", [])
            content = page_head(meta.get("h1", meta["title"]), meta.get("lede", ""), items) + content
        if meta.get("faq") and "{{faq}}" not in body and not meta.get("no_auto_faq"):
            content += f'<div class="wrap" style="margin-top:3rem">{faq_html(meta["faq"])}</div>'
        schema = list(meta.get("schema", []))
        if meta.get("faq"):
            schema.append(faq_schema(meta["faq"]))
        if meta["slug"] in TOOL_BY:
            schema.append({"@type": "WebApplication", "name": TOOL_BY[meta["slug"]]["name"], "url": f'{SITE["site_url"]}/{meta["slug"]}.html',
                           "applicationCategory": "DeveloperApplication", "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
                           "description": TOOL_BY[meta["slug"]]["desc"], "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}})
        if meta["slug"] == "index":
            schema.append({"@type": "WebSite", "name": "LLModel.com", "url": SITE["site_url"] + "/",
                           "potentialAction": {"@type": "SearchAction", "target": SITE["site_url"] + "/search.html?q={search_term_string}",
                                               "query-input": "required name=search_term_string"}})
        meta["schema"] = schema
        if meta.get("crumbs"):
            meta["crumbs"] = [tuple(c) for c in meta["crumbs"]]
        meta["h1_plain"] = re.sub(r"<[^>]+>", "", meta.get("h1", meta["title"]))
        out.append((meta, content))
    return out


# ---------------------------------------------------------------- data files for scripts

def models_js():
    data = []
    for m in MODELS:
        att, kvf = KV_ADJUST.get(m["slug"], ("full", 1.0))
        data.append({
            "s": m["slug"], "n": m["name"], "p": m["provider"], "pn": m["provider_name"], "f": m["family"], "r": m["released"],
            "st": m["status"], "w": m["weights"], "l": m.get("license"), "pt": m.get("params_total_b"), "pa": m.get("params_active_b"),
            "c": m.get("context"), "mo": m.get("max_output"), "i": m.get("price_in"), "o": m.get("price_out"), "ci": m.get("price_cached_in"),
            "mi": m.get("modalities_in", []), "rs": bool(m.get("reasoning")), "tu": bool(m.get("tool_use")), "t": m["tier"],
            "bf": m.get("best_for", []), "hf": m.get("hf_repo"), "a": m.get("arch"), "u": m["url_page"], "pu": m.get("pricing_url"),
            "note": m.get("price_note"), "att": att, "kvf": kvf,
        })
    payload = {"updated": UPDATED, "models": data, "providers": {k: v["name"] for k, v in PROVIDERS.items()}, "kvNotes": KV_NOTES,
               "comparisons": [[a, b, dp.cmp_slug(a, b)] for a, b in dp.COMPARISONS]}
    models_txt = ",\n".join(json.dumps(m, ensure_ascii=False, separators=(",", ":")) for m in payload.pop("models"))
    rest = json.dumps(payload, ensure_ascii=False, indent=1)
    return ("/* Generated by _build/build.py. Do not edit by hand. */\nwindow.LLM_DATA = " + rest[:-2] +
            ',\n "models": [\n' + models_txt + "\n]};\n")


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def main():
    # data script first so the asset hash in page links is current
    write("assets/js/data/models.js", models_js())

    pages = authored_pages()
    for g in GUIDES:
        pages.append(cp.guide_page(g))
    pages.append(cp.guides_hub())
    pages.extend(cp.glossary_pages())
    pages.append(cp.videos_page())
    pages.append(cp.prompts_page())
    pages.append(cp.resources_page())
    pages.append(cp.timeline_page())
    pages.append(dp.providers_index())
    for m in MODELS:
        pages.append(dp.model_page(m))
    for p in PROVIDERS.values():
        pages.append(dp.provider_page(p))
    for a, b in dp.COMPARISONS:
        pages.append(dp.compare_page(a, b))
    for h in dp.HUBS:
        pages.append(dp.hub_page(h))

    metas = [m for m, _ in pages]
    pages.append(cp.sitemap_html(metas))
    metas = [m for m, _ in pages]

    slugs = [m["slug"] for m in metas]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise SystemExit(f"duplicate page slugs: {sorted(dupes)}")

    # remove stale generated pages
    keep = {f"{s}.html" for s in slugs}
    for f in ROOT.glob("*.html"):
        if f.name not in keep:
            f.unlink()

    for meta, content in pages:
        name = "index.html" if meta["slug"] == "index" else f'{meta["slug"]}.html'
        write(name, page_html(meta, content))

    write("assets/data/search.json", "[\n" + ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in cp.build_search_index(metas)) + "\n]\n")
    write("sitemap.xml", cp.sitemap_xml(metas))
    write("llms.txt", cp.llms_txt())
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /thank-you.html\nDisallow: /search.html\n\nSitemap: {SITE['site_url']}/sitemap.xml\n")
    write("ads.txt", f"google.com, {SITE['adsense_client'].replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n")
    write("site.webmanifest", json.dumps({
        "name": "LLModel.com", "short_name": "LLModel", "description": SITE["description"], "start_url": "./index.html",
        "scope": "./", "display": "standalone", "background_color": "#f4f6fb", "theme_color": "#440154",
        "icons": [{"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "assets/img/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}, indent=2) + "\n")
    if SITE.get("custom_domain"):
        write("CNAME", SITE["custom_domain"] + "\n")
    elif (ROOT / "CNAME").exists():
        (ROOT / "CNAME").unlink()
    print(f"Built {len(pages)} pages: {len(MODELS)} models, {len(PROVIDERS)} providers, {len(GUIDES)} guides, "
          f"{len(dp.COMPARISONS)} comparisons, {len(dp.HUBS)} shortlists.")


if __name__ == "__main__":
    main()
