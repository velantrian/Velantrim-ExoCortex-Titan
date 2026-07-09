#!/usr/bin/env python3
"""Собрать статику консоли в docs/ для GitHub Pages."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static" / "console"
DST = ROOT / "docs" / "console"

# Абсолютные пути FastAPI → относительные файлы в docs/console/
PATH_MAP = {
    "/console/research-app.js": "research-app.js",
    "/console/research-app": "research-app.html",
    "/console/research-roadmap": "research-roadmap.html",
    "/console/research-mode": "research-mode.html",
    "/console/research": "research.html",
    "/console/roadmap": "roadmap.html",
    "/console/help": "https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/master/docs/CONSOLE_BROWSER_TEST.ru.md",
    "/console/research-roadmap.md": "https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/master/docs/EITI_PWA_RESEARCH_ROADMAP.ru.md",
    "/console/": "index.html",
    "/console": "index.html",
}


def _rewrite(text: str) -> str:
    for old, new in sorted(PATH_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(f'href="{old}"', f'href="{new}"')
        text = text.replace(f"href='{old}'", f"href='{new}'")
        text = text.replace(f'src="{old}', f'src="{new}')
        text = text.replace(f"src='{old}", f"src='{new}")
    return text


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True, exist_ok=True)

    for path in SRC.iterdir():
        if not path.is_file():
            continue
        out = DST / path.name
        data = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".html", ".js"}:
            data = _rewrite(data)
        out.write_text(data, encoding="utf-8")

    banner = (
        '<div id="gh-pages-banner" style="position:fixed;bottom:0;left:0;right:0;z-index:9999;'
        'background:#1a2332;border-top:1px solid #3d8bfd;padding:.55rem .9rem;font:13px/1.4 '
        'Segoe UI,system-ui,sans-serif;color:#e7ecf3;text-align:center">'
        "🌐 GitHub Pages: UI только. Для LLM и <code>/query</code> запустите "
        '<a href="http://127.0.0.1:8755/console/" style="color:#3d8bfd">локальный сервер</a> '
        'или <a href="../../" style="color:#3d8bfd">портал</a>. '
        "Research App работает полностью в браузере."
        "</div>"
    )
    index = DST / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        if "gh-pages-banner" not in html:
            html = html.replace("</body>", banner + "\n</body>")
            index.write_text(html, encoding="utf-8")

    pwa_head = (
        '<link rel="manifest" href="../manifest.webmanifest" />\n'
        '  <link rel="icon" href="../icon.svg" type="image/svg+xml" />\n'
        '  <meta name="theme-color" content="#3d8bfd" />\n'
        '  <meta name="apple-mobile-web-app-capable" content="yes" />\n'
        '  <meta name="apple-mobile-web-app-title" content="VELANTRIM" />\n'
        '  <link rel="apple-touch-icon" href="../icon.svg" />'
    )
    research = DST / "research-app.html"
    if research.is_file():
        html = research.read_text(encoding="utf-8")
        if "manifest.webmanifest" not in html:
            html = html.replace("</title>", "</title>\n  " + pwa_head)
            html = html.replace(
                "</body>",
                '  <script>if("serviceWorker"in navigator)navigator.serviceWorker.register("../sw.js").catch(()=>{});</script>\n</body>',
            )
            research.write_text(html, encoding="utf-8")

    (ROOT / "docs" / ".nojekyll").write_text("", encoding="utf-8")
    print(f"OK: {len(list(DST.iterdir()))} files → {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
