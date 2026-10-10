#!/usr/bin/env python3
"""Quality checks for the built site. Run after `python3 _build/build.py`. Prints "No problems found." when clean."""
import base64
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[2]
SITE = json.loads((ROOT / "_build" / "site.json").read_text())
ADS_TAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6620975821265271" '
           'crossorigin="anonymous"></script>')
NO_ADSENSE = {"404.html", "thank-you.html"}
problems = []


def bad(msg):
    problems.append(msg)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.h1, self.dupes, self.imgs_noalt = [], [], 0, [], 0
        self.ld, self._in_ld, self._buf = [], False, ""
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.dupes.append(a["id"])
            self.ids.append(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("link",) and a.get("href") and a.get("rel") in ("stylesheet", "icon", "manifest", "apple-touch-icon"):
            self.links.append(a["href"])
        if tag == "script" and a.get("src"):
            self.links.append(a["src"])
        if tag == "img" and "alt" not in a:
            self.imgs_noalt += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._buf = True, ""
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self.ld.append(self._buf)
            self._in_ld = False
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_ld:
            self._buf += data
        if self._in_title:
            self.title = (self.title or "") + data


def inbox():
    cfg = (ROOT / "assets/js/config.js").read_text()
    r = json.loads(re.search(r"window\.__r\s*=\s*(\[[^\]]*\])", cfg).group(1))
    k = re.search(r'window\.__k\s*=\s*"([^"]*)"', cfg).group(1)
    return "".join(chr(v ^ ord(k[i % len(k)])) for i, v in enumerate(r))


def main():
    pages = sorted(ROOT.glob("*.html"))
    parsed = {}
    for f in pages:
        t = f.read_text()
        p = Page()
        p.feed(t)
        parsed[f.name] = (t, p)

    for name, (t, p) in parsed.items():
        if f'<a href="{SITE["partner_url"]}" target="_blank" rel="noopener"><span>{SITE["partner_text"]}</span></a>' not in t:
            bad(f"{name}: partner bar missing or changed")
        if name in NO_ADSENSE:
            if "adsbygoogle.js" in t:
                bad(f"{name}: AdSense script must not load on this page")
        else:
            if ADS_TAG not in t:
                bad(f"{name}: AdSense tag missing or altered")
        if '<meta name="google-adsense-account" content="ca-pub-6620975821265271">' not in t:
            bad(f"{name}: AdSense account meta missing")
        if p.h1 != 1:
            bad(f"{name}: {p.h1} h1 elements")
        if not p.title or len(p.title) > 110:
            bad(f"{name}: title missing or too long ({len(p.title or '')})")
        m = re.search(r'<meta name="description" content="([^"]*)"', t)
        if not m or not (50 <= len(m.group(1)) <= 320):
            bad(f"{name}: meta description missing or odd length")
        if '<link rel="canonical"' not in t:
            bad(f"{name}: canonical missing")
        if re.search(r"\{\{[a-z_]+(:[^}]*)?\}\}", re.sub(r"<pre.*?</pre>", "", t, flags=re.S)):
            bad(f"{name}: unrendered placeholder")
        if p.dupes:
            bad(f"{name}: duplicate ids {sorted(set(p.dupes))[:5]}")
        if p.imgs_noalt:
            bad(f"{name}: {p.imgs_noalt} images without alt")
        for block in p.ld:
            try:
                json.loads(block)
            except ValueError as e:
                bad(f"{name}: bad JSON-LD ({e})")
        for href in p.links:
            u = urlparse(href)
            if u.scheme in ("http", "https", "mailto", "tel", "javascript") or href.startswith("//"):
                continue
            path, frag = unquote(u.path), u.fragment
            target = name if not path else path
            if target.startswith("/"):
                bad(f"{name}: root-relative link {href} breaks on GitHub Pages project URLs")
                continue
            if not (ROOT / target).exists():
                bad(f"{name}: broken link {href}")
                continue
            if frag and target.endswith(".html") and target in parsed and frag not in parsed[target][1].ids:
                bad(f"{name}: missing anchor #{frag} in {target}")
        for form in re.findall(r"<form[^>]*data-form=[^>]*>.*?</form>", t, re.S):
            if "data-custom" not in form and "_honey" not in form:
                bad(f"{name}: form without honeypot")
            if 'class="form-status"' not in form:
                bad(f"{name}: form without status region")

    # inbox must never be exposed
    addr = inbox()
    user, domain = addr.split("@")
    needles = {addr, addr[::-1], base64.b64encode(addr.encode()).decode(), addr.replace("@", "%40"), addr.replace("@", "&#64;"),
               user + "&#", user + " at ", user + "[at]", "mailto:" + user}
    scanned = 0
    for f in ROOT.rglob("*"):
        if not f.is_file() or ".git" in f.parts or f.suffix in (".png", ".woff2", ".b64"):
            continue
        try:
            txt = f.read_text()
        except UnicodeDecodeError:
            continue
        scanned += 1
        low = txt.lower()
        for n in needles:
            if n.lower() in low:
                bad(f"inbox exposed in {f.relative_to(ROOT)}")
    # ads.txt, robots, sitemap
    if (ROOT / "ads.txt").read_text().strip() != "google.com, pub-6620975821265271, DIRECT, f08c47fec0942fa0":
        bad("ads.txt content is wrong")
    if "Sitemap:" not in (ROOT / "robots.txt").read_text():
        bad("robots.txt has no sitemap line")
    sm = (ROOT / "sitemap.xml").read_text()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
        rel = loc.replace(SITE["site_url"] + "/", "") or "index.html"
        if not (ROOT / rel).exists():
            bad(f"sitemap lists missing page {rel}")
    for name, (t, p) in parsed.items():
        if 'name="robots" content="index' in t and name != "index.html" and f"/{name}<" not in sm:
            bad(f"{name} is indexable but missing from sitemap.xml")
    # JS syntax
    for js in (ROOT / "assets/js").rglob("*.js"):
        r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        if r.returncode:
            bad(f"JS syntax error in {js.relative_to(ROOT)}: {r.stderr.strip()[:200]}")
    json.loads((ROOT / "assets/data/search.json").read_text())

    print(f"Checked {len(pages)} pages and {scanned} text files.")
    if problems:
        print(f"{len(problems)} problems:")
        for x in problems[:200]:
            print(" -", x)
        sys.exit(1)
    print("No problems found.")


if __name__ == "__main__":
    main()
