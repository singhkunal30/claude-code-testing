"""Tiny safe Markdown -> HTML renderer.

Supports: fenced code blocks (```), ATX headings, unordered/ordered lists,
bold (**), italic (*), inline code (`), autolinks ([text](url)), paragraphs.

Always escapes raw HTML in the input. Strips javascript: links.
"""
from __future__ import annotations

import re
from html import escape


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\s)([^*]+?)(?<!\s)\*(?!\*)")
_CODE = re.compile(r"`([^`]+?)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def _safe_url(url: str) -> str:
    url = url.strip()
    lowered = url.lower()
    if lowered.startswith(("javascript:", "data:", "vbscript:")):
        return "#"
    return url


def _inline(line: str) -> str:
    """Apply inline transforms to an already-escaped line."""
    out = _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", line)
    out = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = _ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", out)
    out = _LINK.sub(
        lambda m: f'<a href="{escape(_safe_url(m.group(2)))}">{m.group(1)}</a>',
        out,
    )
    return out


def render(text: str) -> str:
    """Render Markdown subset to safe HTML.

    The strategy: escape first, then unescape known constructs. This means raw
    HTML in the input is rendered literally (good — prevents XSS).
    """
    if not text:
        return ""

    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    list_open: str | None = None  # "ul" or "ol" or None
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            joined = "<br>".join(_inline(escape(ln)) for ln in para_buf)
            out.append(f"<p>{joined}</p>")
            para_buf.clear()

    def flush_list() -> None:
        nonlocal list_open
        if list_open:
            out.append(f"</{list_open}>")
            list_open = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                out.append(f'<pre><code>{escape(chr(10).join(code_buf))}</code></pre>')
                code_buf = []
                in_code = False
            else:
                flush_para()
                flush_list()
                in_code = True
            continue

        if in_code:
            code_buf.append(raw_line)
            continue

        if not line.strip():
            flush_para()
            flush_list()
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            flush_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(escape(m.group(2)))}</h{level}>")
            continue

        m = re.match(r"^[\-\*]\s+(.*)$", line)
        if m:
            flush_para()
            if list_open != "ul":
                flush_list()
                out.append("<ul>")
                list_open = "ul"
            out.append(f"<li>{_inline(escape(m.group(1)))}</li>")
            continue

        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            flush_para()
            if list_open != "ol":
                flush_list()
                out.append("<ol>")
                list_open = "ol"
            out.append(f"<li>{_inline(escape(m.group(1)))}</li>")
            continue

        flush_list()
        para_buf.append(line)

    if in_code:
        out.append(f'<pre><code>{escape(chr(10).join(code_buf))}</code></pre>')
    flush_para()
    flush_list()
    return "\n".join(out)
