#!/usr/bin/env python3
"""Render the social image and app icons into assets/img.

In GitHub Actions:  python3 _build/images/render.py --ci
Locally (offline):  python3 _build/images/render.py --fonts-from /path/to/dir/with/shot.py

Uses Playwright and Chromium so the social image is drawn with the brand fonts. If Playwright
isn't available, it falls back to drawing the icons with Pillow and skips the social image.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "assets" / "img"
ICONS = [("favicon-32.png", 32), ("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)]
FONTS_CSS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800"
             "&family=Martian+Mono:wght@400..500&display=block")


def pillow_icons():
    from PIL import Image, ImageDraw
    for name, size in ICONS:
        s = 512 * 4
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        k = s / 512
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(112 * k), fill="#440154")
        d.rounded_rectangle([int(72 * k), int(160 * k), int(208 * k), int(352 * k)], radius=int(40 * k), fill="#fde725")
        d.rounded_rectangle([int(232 * k), int(160 * k), int(440 * k), int(352 * k)], radius=int(40 * k), fill="#21918c")
        im.resize((size, size), Image.LANCZOS).save(OUT / name)
        print("icon", name)


def playwright_render(route=None):
    from playwright.sync_api import sync_playwright
    mark = (ROOT / "assets/img/mark.svg").read_text()
    html = (HERE / "og.html").read_text().replace(
        "<style>", f'<link rel="stylesheet" href="{FONTS_CSS}"><style>', 1)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        if route:
            pg.route("**/*", route)
        pg.set_content(html, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT / "og-image.png"))
        print("social image og-image.png")
        for name, s in ICONS:
            pg.set_viewport_size({"width": s, "height": s})
            svg = mark.replace("<svg ", f'<svg width="{s}" height="{s}" ', 1)
            pg.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
            pg.screenshot(path=str(OUT / name), omit_background=True)
            print("icon", name)
        b.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    route = None
    if "--fonts-from" in sys.argv:
        sys.path.insert(0, sys.argv[sys.argv.index("--fonts-from") + 1])
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
        from shot import route as local_route  # serves brand fonts offline
        route = local_route
    try:
        playwright_render(route)
    except Exception as e:  # noqa: BLE001
        print("Playwright render failed, drawing icons with Pillow instead:", e)
        pillow_icons()


if __name__ == "__main__":
    main()
