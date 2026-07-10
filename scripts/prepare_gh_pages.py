#!/usr/bin/env python3
"""Собрать полный статический сайт в site/ для GitHub Pages.

Сайт работает в двух режимах:
  1. На localhost:8755 — полная консоль с Python-сервером (LLM, SQLite)
  2. На GitHub Pages — PWA: IndexedDB + прямые API-вызовы к LLM (без сервера)
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static" / "console"
SITE = ROOT / "site"
PORTAL = ROOT / "docs"

# Карта перезаписи путей: абсолютные URL FastAPI → относительные файлы
PATH_MAP = {
    "/console/research-app.js": "research-app.js",
    "/console/research-app": "research-app.html",
    "/console/research-roadmap": "research-roadmap.html",
    "/console/research-mode": "research-mode.html",
    "/console/research": "research.html",
    "/console/roadmap": "roadmap.html",
    "/console/help": (
        "https://github.com/velantrian/Velantrim-ExoCortex-Titan"
        "/blob/master/docs/CONSOLE_BROWSER_TEST.ru.md"
    ),
    "/console/research-roadmap.md": (
        "https://github.com/velantrian/Velantrim-ExoCortex-Titan"
        "/blob/master/docs/EITI_PWA_RESEARCH_ROADMAP.ru.md"
    ),
    "/console/": "index.html",
    "/console": "index.html",
}

# Внедряется в <head> консольного index.html — PWA-мост
PWA_MODE_SCRIPT = """
<script>
(function(){var h=window.location.hostname||"";
if(h.endsWith("github.io")||h==="velantrian.github.io"){
document.write('<script src="./pwa-mode.js?v=3"><\\/script>');
}})();
</script>
"""

# Баннер внизу — только на GitHub Pages
PWA_BANNER = """
<div id="gh-pages-banner" style="position:fixed;bottom:0;left:0;right:0;z-index:9999;
background:#1a2332;border-top:1px solid #3d8bfd;padding:.55rem .9rem;
font:13px/1.4 Segoe UI,system-ui,sans-serif;color:#e7ecf3;text-align:center">
⚡ PWA-режим: память в IndexedDB · LLM через прямые API (ключ в панели сверху).
<a href="http://127.0.0.1:8755/console/" style="color:#3d8bfd">Локальный сервер</a> —
полная консоль с SQLite и всеми провайдерами.
</div>
"""

# PWA-теги в research-app.html
PWA_HEAD = (
    '<link rel="manifest" href="../manifest.webmanifest" />\n'
    '  <link rel="icon" href="../icon.svg" type="image/svg+xml" />\n'
    '  <meta name="theme-color" content="#3d8bfd" />\n'
    '  <meta name="apple-mobile-web-app-capable" content="yes" />\n'
    '  <meta name="apple-mobile-web-app-title" content="VELANTRIM" />\n'
    '  <link rel="apple-touch-icon" href="../icon.svg" />'
)

PWA_SW_SCRIPT = (
    '  <script>'
    'if("serviceWorker"in navigator)'
    'navigator.serviceWorker.register("../sw.js").catch(function(){});'
    "</script>\n</body>"
)


def _rewrite(text: str) -> str:
    for old, new in sorted(PATH_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(f'href="{old}"', f'href="{new}"')
        text = text.replace(f"href='{old}'", f"href='{new}'")
        text = text.replace(f'src="{old}', f'src="{new}')
        text = text.replace(f"src='{old}", f"src='{new}")
    return text


def _copy_portal_files() -> None:
    for name in ("index.html", "manifest.webmanifest", "sw.js", "icon.svg"):
        src = PORTAL / name
        if src.is_file():
            shutil.copy2(src, SITE / name)


def _build_console() -> None:
    dst = SITE / "console"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    # Копируем все файлы консоли
    for path in SRC.iterdir():
        if not path.is_file():
            continue
        data = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".html", ".js"}:
            data = _rewrite(data)
        (dst / path.name).write_text(data, encoding="utf-8")

    # ── index.html: внедряем PWA-мост и баннер ──
    index = dst / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        if "pwa-mode.js" not in html:
            html = html.replace("<head>", "<head>\n" + PWA_MODE_SCRIPT.strip(), 1)
        if "gh-pages-banner" not in html:
            html = html.replace("</body>", PWA_BANNER.strip() + "\n</body>")
        index.write_text(html, encoding="utf-8")

    # ── research-app.html: PWA-теги + service worker ──
    research = dst / "research-app.html"
    if research.is_file():
        html = research.read_text(encoding="utf-8")
        if "manifest.webmanifest" not in html:
            html = html.replace("</title>", "</title>\n  " + PWA_HEAD)
        if "serviceWorker" not in html:
            html = html.replace("</body>", PWA_SW_SCRIPT)
        research.write_text(html, encoding="utf-8")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    _copy_portal_files()
    _build_console()
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    n = sum(1 for _ in SITE.rglob("*") if _.is_file())
    print(f"OK: {n} files → {SITE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
