"""Inject I18N.de into console index.html."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "static" / "console" / "index.html"
JS_MAP = Path(__file__).with_name("_inject_de.js")


def load_de_map() -> dict:
    text = JS_MAP.read_text(encoding="utf-8")
    start = text.index("const map = {")
    end = text.index("\n  };", start)
    body = text[start + len("const map = {") : end]
    out = {}
    pos = 0
    key_re = re.compile(r'(?:"([^"]+)"|([a-zA-Z_][\w.]*))\s*:\s*')
    while pos < len(body):
        m = key_re.search(body, pos)
        if not m:
            break
        key = m.group(1) or m.group(2)
        i = m.end()
        if i >= len(body):
            break
        ch = body[i]
        if ch == '"':
            val, j = read_quoted(body, i, '"')
        elif ch == "'":
            val, j = read_quoted(body, i, "'")
        else:
            break
        out[key] = val
        pos = j
        while pos < len(body) and body[pos] in " \t,\n\r":
            pos += 1
    return out


def parse_en_block(body: str) -> dict:
    out = {}
    pos = 0
    key_re = re.compile(r'"([^"]+)":\s*')
    while pos < len(body):
        m = key_re.search(body, pos)
        if not m:
            break
        key = m.group(1)
        i = m.end()
        if i >= len(body):
            break
        ch = body[i]
        if ch == '"':
            val, j = read_quoted(body, i, '"')
        elif ch == "'":
            val, j = read_quoted(body, i, "'")
        else:
            break
        out[key] = val
        pos = j
        while pos < len(body) and body[pos] in " \t,":
            pos += 1
    return out


def read_quoted(s: str, start: int, q: str) -> tuple[str, int]:
    i = start + 1
    parts = []
    while i < len(s):
        c = s[i]
        if c == "\\":
            parts.append(s[i : i + 2])
            i += 2
            continue
        if c == q:
            raw = q + "".join(parts) + q
            try:
                return json.loads(raw), i + 1
            except json.JSONDecodeError:
                inner = "".join(parts)
                return inner, i + 1
        parts.append(c)
        i += 1
    raise ValueError("unterminated string")


def translate(key: str, en: str, de_map: dict) -> str:
    return de_map.get(key, en)


def main() -> None:
    de_map = load_de_map()
    h = HTML.read_text(encoding="utf-8")
    en_start = h.index("      en: {")
    en_end = h.index("      },\n    };", en_start)
    en_body = h[en_start + len("      en: {") : en_end]
    en = parse_en_block(en_body)
    de = {k: translate(k, v, de_map) for k, v in en.items()}
    patch = "\n    I18N.de = " + json.dumps(de, ensure_ascii=False, indent=2).replace("\n", "\n    ") + ";\n"
    marker = "    };\n\n    function detectBrowserLang()"
    if "I18N.de =" in h:
        h = re.sub(r"\n    I18N\.de = [\s\S]*?;\n(?=\n    function detectBrowserLang)", patch, h, count=1)
    else:
        h = h.replace(marker, "    };" + patch + "\n    function detectBrowserLang()")
    HTML.write_text(h, encoding="utf-8")
    print(f"Injected I18N.de: {len(de)} keys, {sum(1 for k in en if k in de_map)} translated")


if __name__ == "__main__":
    main()
