"""Tiny HTML rendering helpers. No template engine; just str + html.escape."""
from __future__ import annotations

from datetime import datetime
from html import escape

from app.models.bookmark import Bookmark
from app.models.digest import Digest
from app.models.entry import Entry


_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5;
       color: #1a1a1a; background: #fafafa; }
header { display: flex; justify-content: space-between; align-items: center;
         border-bottom: 1px solid #ddd; padding-bottom: .75rem; margin-bottom: 1.5rem; }
header nav a { margin-right: 1rem; color: #0066cc; text-decoration: none; }
header nav a:hover { text-decoration: underline; }
h1, h2 { margin: 0 0 .5rem; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.15rem; color: #444; margin-top: 2rem; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
.card { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
        padding: .75rem 1rem; margin-bottom: .75rem; }
.card .meta { color: #888; font-size: .8rem; margin-top: .35rem; }
.tag { display: inline-block; background: #eef; color: #335; padding: 1px 6px;
       border-radius: 3px; font-size: .75rem; margin-right: 4px; }
form { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
       padding: 1rem; margin-bottom: 1rem; }
form label { display: block; font-size: .85rem; color: #555; margin-top: .5rem; }
form input, form textarea { width: 100%; padding: .4rem .5rem; border: 1px solid #ccc;
                            border-radius: 4px; font-size: .95rem; font-family: inherit; }
form button { margin-top: .75rem; padding: .4rem 1rem; background: #0066cc;
              color: white; border: none; border-radius: 4px; cursor: pointer; }
form button.danger { background: #cc4444; padding: 2px 8px; font-size: .8rem; }
.inline-form { background: none; border: none; padding: 0; margin: 0; display: inline; }
pre.digest { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
             padding: 1rem; white-space: pre-wrap; font-family: inherit; }
.empty { color: #888; font-style: italic; }
"""


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · TIL Journal</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>📓 TIL Journal</h1>
  <nav>
    <a href="/">Home</a>
    <a href="/ui/digests">Digests</a>
    <a href="/docs">API</a>
  </nav>
</header>
{body}
</body>
</html>"""


def _tags_html(tags: list[str]) -> str:
    if not tags:
        return ""
    return " ".join(f'<span class="tag">{escape(t)}</span>' for t in tags)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def entry_card(e: Entry) -> str:
    source = f' · <a href="{escape(e.source)}">source</a>' if e.source else ""
    return f"""<div class="card">
  <div>{escape(e.text)}</div>
  <div class="meta">
    {_tags_html(e.tags)}
    · {_fmt_time(e.created_at)}{source}
    · <form class="inline-form" method="post" action="/ui/entries/{e.id}/delete">
        <button class="danger" type="submit" onclick="return confirm('Delete?')">×</button>
      </form>
  </div>
</div>"""


def bookmark_card(b: Bookmark) -> str:
    label = escape(b.title or b.url)
    notes = f"<div>{escape(b.notes)}</div>" if b.notes else ""
    return f"""<div class="card">
  <a href="{escape(b.url)}"><strong>{label}</strong></a>
  {notes}
  <div class="meta">
    {_tags_html(b.tags)}
    · {_fmt_time(b.created_at)}
    · <form class="inline-form" method="post" action="/ui/bookmarks/{b.id}/delete">
        <button class="danger" type="submit" onclick="return confirm('Delete?')">×</button>
      </form>
  </div>
</div>"""


def entry_form() -> str:
    return """<form method="post" action="/ui/entries">
  <label>What did you learn today?</label>
  <textarea name="text" rows="3" required placeholder="Today I learned…"></textarea>
  <label>Source (optional)</label>
  <input name="source" placeholder="https://… or book title">
  <label>Tags (optional, comma-separated; auto-tagged if blank)</label>
  <input name="tags" placeholder="python, fastapi">
  <button type="submit">Log entry</button>
</form>"""


def bookmark_form() -> str:
    return """<form method="post" action="/ui/bookmarks">
  <label>URL</label>
  <input name="url" required placeholder="https://…">
  <label>Title (optional)</label>
  <input name="title">
  <label>Notes (optional)</label>
  <textarea name="notes" rows="2"></textarea>
  <label>Tags (optional, comma-separated)</label>
  <input name="tags">
  <button type="submit">Save bookmark</button>
</form>"""


def home(entries: list[Entry], bookmarks: list[Bookmark]) -> str:
    entries_html = (
        "".join(entry_card(e) for e in entries)
        if entries
        else '<p class="empty">No entries yet.</p>'
    )
    bookmarks_html = (
        "".join(bookmark_card(b) for b in bookmarks)
        if bookmarks
        else '<p class="empty">No bookmarks yet.</p>'
    )
    body = f"""<div class="grid">
  <section>
    <h2>📝 Entries</h2>
    {entry_form()}
    {entries_html}
  </section>
  <section>
    <h2>🔖 Bookmarks</h2>
    {bookmark_form()}
    {bookmarks_html}
  </section>
</div>"""
    return page("Home", body)


def digests_page(digests: list[Digest]) -> str:
    items = (
        "".join(
            f'<div class="card"><strong>{d.period.capitalize()}: '
            f"{d.start_date} → {d.end_date}</strong>"
            f'<div class="meta">{_fmt_time(d.created_at)}</div>'
            f'<pre class="digest">{escape(d.content)}</pre></div>'
            for d in digests
        )
        if digests
        else '<p class="empty">No digests yet.</p>'
    )
    body = f"""<section>
  <h2>📊 Digests</h2>
  <form method="post" action="/ui/digests/generate">
    <label>Period</label>
    <select name="period">
      <option value="week">Week</option>
      <option value="month">Month</option>
    </select>
    <button type="submit">Generate now</button>
  </form>
  {items}
</section>"""
    return page("Digests", body)
