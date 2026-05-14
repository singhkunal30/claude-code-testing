from __future__ import annotations

from app.ui.markdown import render


def test_paragraph() -> None:
    assert render("hello world") == "<p>hello world</p>"


def test_headings() -> None:
    assert "<h1>Title</h1>" in render("# Title")
    assert "<h3>Sub</h3>" in render("### Sub")


def test_bold_italic_code() -> None:
    out = render("**bold** *italic* `code`")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out
    assert "<code>code</code>" in out


def test_fenced_code_block_escapes_html() -> None:
    out = render("```\n<script>alert(1)</script>\n```")
    assert "<pre><code>" in out
    assert "&lt;script&gt;" in out
    assert "<script>" not in out


def test_unordered_list() -> None:
    out = render("- one\n- two")
    assert "<ul>" in out
    assert "<li>one</li>" in out
    assert "<li>two</li>" in out


def test_ordered_list() -> None:
    out = render("1. first\n2. second")
    assert "<ol>" in out and "<li>first</li>" in out


def test_link_rendered() -> None:
    out = render("see [docs](https://example.com)")
    assert '<a href="https://example.com">docs</a>' in out


def test_javascript_link_neutralised() -> None:
    out = render('click [me](javascript:alert(1))')
    assert "javascript:" not in out
    assert 'href="#"' in out


def test_raw_html_escaped() -> None:
    out = render("<img src=x onerror=alert(1)>")
    assert "<img" not in out
    assert "&lt;img" in out
