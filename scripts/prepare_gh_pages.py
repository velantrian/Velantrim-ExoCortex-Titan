#!/usr/bin/env python3
"""Собрать полный статический сайт в site/ для GitHub Pages."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static" / "console"
SITE = ROOT / "site"
PORTAL = ROOT / "docs"

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

API_BOOTSTRAP = """
<script>
(function () {
  var key = "velantrim_remote_api_base";
  var def = "http://127.0.0.1:8755";
  var base = localStorage.getItem(key) || def;
  if (!/^https?:\\/\\//i.test(base)) base = def;
  window.VELANTRIM_API_BASE = base.replace(/\\/$/, "");
  var host = location.hostname;
  var onGh = host.endsWith("github.io");
  if (onGh && !localStorage.getItem(key)) {
    var bar = document.createElement("div");
    bar.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:99999;background:#3d1f1f;border-bottom:1px solid #f56565;padding:.55rem .8rem;font:13px/1.45 Segoe UI,system-ui,sans-serif;color:#ffe8e8;text-align:center";
    bar.innerHTML = "⚠️ GitHub Pages — только UI. Для LLM укажите URL вашего сервера Velantrim (ПК/VPS/Docker) в настройках консоли или запустите <code style='color:#ffd28a'>scripts\\\\start_console.ps1</code> локально.";
    document.addEventListener("DOMContentLoaded", function () { document.body.prepend(bar); });
  }
})();
</script>
"""


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

    for path in SRC.iterdir():
        if not path.is_file():
            continue
        data = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".html", ".js"}:
            data = _rewrite(data)
        (dst / path.name).write_text(data, encoding="utf-8")

    index = dst / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        if "VELANTRIM_API_BASE" not in html:
            html = html.replace("<head>", "<head>\n" + API_BOOTSTRAP, 1)
            html = html.replace("</body>", (
                '<div id="gh-pages-banner" style="position:fixed;bottom:0;left:0;right:0;z-index:9999;'
                'background:#1a2332;border-top:1px solid #3d8bfd;padding:.55rem .9rem;font:13px/1.4 '
                'Segoe UI,system-ui,sans-serif;color:#e7ecf3;text-align:center">'
                '🌐 Статическая консоль на GitHub Pages. Сервер API: '
                '<a href="http://127.0.0.1:8755/console/" style="color:#3d8bfd">локально</a> '
                'или ваш VPS/Docker. Research App работает без сервера.'
                '</div>\n</body>'
            ))
            index.write_text(html, encoding="utf-8")

    pwa_head = (
        '<link rel="manifest" href="../manifest.webmanifest" />\n'
        '  <link rel="icon" href="../icon.svg" type="image/svg+xml" />\n'
        '  <meta name="theme-color" content="#3d8bfd" />\n'
        '  <meta name="apple-mobile-web-app-capable" content="yes" />\n'
        '  <meta name="apple-mobile-web-app-title" content="VELANTRIM" />\n'
        '  <link rel="apple-touch-icon" href="../icon.svg" />'
    )
    research = dst / "research-app.html"
    if research.is_file():
        html = research.read_text(encoding="utf-8")
        if "manifest.webmanifest" not in html:
            html = html.replace("</title>", "</title>\n  " + pwa_head)
            html = html.replace(
                "</body>",
                '  <script>if("serviceWorker"in navigator)navigator.serviceWorker.register("../sw.js").catch(()=>{});</script>\n</body>',
            )
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
