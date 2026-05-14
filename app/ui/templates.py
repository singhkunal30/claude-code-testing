"""Tiny HTML rendering helpers. No template engine; just str + html.escape."""
from __future__ import annotations

from datetime import datetime
from html import escape

from app.models.bookmark import Bookmark
from app.models.digest import Digest
from app.models.entry import Entry
from app.models.reaction import Reaction
from app.models.stats import Stats
from app.ui.markdown import render as md


_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5;
       color: #1a1a1a; background: #fafafa; }
header { display: flex; justify-content: space-between; align-items: center;
         border-bottom: 1px solid #ddd; padding-bottom: .75rem; margin-bottom: 1.5rem;
         flex-wrap: wrap; gap: .5rem; }
header nav a { margin-right: 1rem; color: #0066cc; text-decoration: none; }
header nav a:hover { text-decoration: underline; }
h1, h2 { margin: 0 0 .5rem; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.15rem; color: #444; margin-top: 2rem; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
.card { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
        padding: .75rem 1rem; margin-bottom: .75rem; }
.card .meta { color: #888; font-size: .8rem; margin-top: .35rem;
              display: flex; flex-wrap: wrap; align-items: center; gap: .35rem; }
.card .body { font-size: .95rem; }
.card .body p { margin: .25rem 0; }
.card .body pre { background: #f4f4f4; padding: .5rem; border-radius: 4px;
                  overflow-x: auto; font-size: .85rem; }
.card .body code { background: #f4f4f4; padding: 1px 4px; border-radius: 3px;
                   font-size: .85rem; }
.card .body pre code { padding: 0; background: none; }
.tag { display: inline-block; background: #eef; color: #335; padding: 1px 6px;
       border-radius: 3px; font-size: .75rem; }
.actions { display: inline-flex; gap: .25rem; align-items: center; }
.btn-link { background: none; border: 1px solid #ddd; border-radius: 3px;
            padding: 1px 6px; font-size: .8rem; cursor: pointer; color: #444; }
.btn-link:hover { background: #eef; }
.btn-link.active { background: #ffe; border-color: #cc4; }
.danger { background: none; border: 1px solid #fcc; color: #c33; }
.danger:hover { background: #fee; }
form { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
       padding: 1rem; margin-bottom: 1rem; }
form label { display: block; font-size: .85rem; color: #555; margin-top: .5rem; }
form input, form textarea, form select { width: 100%; padding: .4rem .5rem;
       border: 1px solid #ccc; border-radius: 4px; font-size: .95rem; font-family: inherit; }
form button { margin-top: .75rem; padding: .4rem 1rem; background: #0066cc;
              color: white; border: none; border-radius: 4px; cursor: pointer; }
form.inline { background: none; border: none; padding: 0; margin: 0; display: inline; }
form.inline button { margin: 0; }
form.row { display: flex; gap: .5rem; align-items: flex-end; }
form.row input { flex: 1; }
form.row button { margin-top: 0; }
pre.digest { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
             padding: 1rem; white-space: pre-wrap; font-family: inherit; }
.empty { color: #888; font-style: italic; }
.banner { background: #fffbe6; border: 1px solid #f0e68c; border-radius: 6px;
          padding: .75rem 1rem; margin-bottom: 1rem; font-size: .9rem; color: #665; }
.banner strong { color: #443; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
             gap: .75rem; margin: 1rem 0; }
.stat-grid .stat { background: white; border: 1px solid #e2e2e2; border-radius: 6px;
                   padding: .75rem 1rem; text-align: center; }
.stat .num { font-size: 1.75rem; font-weight: 600; color: #0066cc; }
.stat .label { font-size: .8rem; color: #888; }
.sparkline { display: flex; align-items: flex-end; height: 60px; gap: 3px;
             background: white; border: 1px solid #e2e2e2; border-radius: 6px;
             padding: .5rem; }
.sparkline .bar { flex: 1; background: #0066cc; min-height: 2px;
                  border-radius: 2px 2px 0 0; opacity: .8; }
.sparkline .bar:hover { opacity: 1; }
.share-url { background: #f4f4f4; padding: .25rem .5rem; border-radius: 3px;
             font-family: monospace; font-size: .8rem; user-select: all; }
.note { color: #888; font-size: .85rem; margin-top: .5rem; }
.user-chip { font-size: .85rem; color: #444; margin-left: .5rem;
             padding: 2px 8px; background: #eef; border-radius: 10px; }
"""


def page(title: str, body: str, user_email: str | None = None) -> str:
    user_chunk = (
        f"""<span class="user-chip">{escape(user_email)}</span>
    <form class="inline" method="post" action="/logout">
      <button class="btn-link" type="submit">Sign out</button>
    </form>"""
        if user_email
        else ""
    )
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
    <a href="/ui/stats">Stats</a>
    <a href="/ui/ask">Ask</a>
    <a href="/export.md">Export</a>
    <a href="/docs">API</a>
    {user_chunk}
  </nav>
</header>
{body}
</body>
</html>"""


def auth_page(mode: str, error: str | None = None) -> str:
    """Render /login or /signup. `mode` is 'login' or 'signup'."""
    title = "Sign in" if mode == "login" else "Create your journal"
    button = "Sign in" if mode == "login" else "Create account"
    other_label = "Need an account? Sign up" if mode == "login" else "Already have an account? Sign in"
    other_href = "/signup" if mode == "login" else "/login"
    action = f"/{mode}"
    err_html = f'<p style="color:#c33">{escape(error)}</p>' if error else ""
    body = f"""<section style="max-width:380px;margin:2rem auto">
  <h2>{title}</h2>
  {err_html}
  <form method="post" action="{action}">
    <label>Email</label>
    <input type="email" name="email" required autocomplete="email">
    <label>Password</label>
    <input type="password" name="password" required minlength="6" autocomplete="{'current-password' if mode == 'login' else 'new-password'}">
    <button type="submit">{button}</button>
  </form>
  <p><a href="{other_href}">{other_label}</a></p>
</section>"""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · TIL Journal</title>
<style>{_CSS}</style>
</head>
<body>
<header><h1>📓 TIL Journal</h1></header>
{body}
</body>
</html>"""


def _tags_html(tags: list[str]) -> str:
    if not tags:
        return ""
    return " ".join(f'<span class="tag">{escape(t)}</span>' for t in tags)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


_DEFAULT_EMOJIS = ["🔥", "💡", "🤯", "👍"]


def _reactions_html(entry_id: int, reactions: list[Reaction]) -> str:
    by_emoji = {r.emoji: r.count for r in reactions}
    buttons = []
    for emoji in _DEFAULT_EMOJIS:
        count = by_emoji.get(emoji, 0)
        active = " active" if count > 0 else ""
        buttons.append(
            f'<form class="inline" method="post" action="/ui/entries/{entry_id}/react">'
            f'<input type="hidden" name="emoji" value="{emoji}">'
            f'<button class="btn-link{active}" type="submit">{emoji} {count or ""}</button>'
            f"</form>"
        )
    return '<span class="actions">' + "".join(buttons) + "</span>"


def entry_card(
    e: Entry,
    reactions: list[Reaction] | None = None,
    is_highlighted: bool = False,
) -> str:
    source = f' · <a href="{escape(e.source)}">source</a>' if e.source else ""
    star_state = "active" if is_highlighted else ""
    star_label = "★ highlighted" if is_highlighted else "☆ highlight"
    share_state = "active" if e.share_token else ""
    share_label = "🔗 shared" if e.share_token else "🔗 share"
    return f"""<div class="card">
  <div class="body">{md(e.text)}</div>
  <div class="meta">
    {_tags_html(e.tags)}
    · {_fmt_time(e.created_at)}{source}
    · {_reactions_html(e.id, reactions or [])}
    · <form class="inline" method="post" action="/ui/entries/{e.id}/highlight">
        <button class="btn-link {star_state}" type="submit">{star_label}</button>
      </form>
    · <form class="inline" method="post" action="/ui/entries/{e.id}/share/toggle">
        <button class="btn-link {share_state}" type="submit">{share_label}</button>
      </form>
    · <form class="inline" method="post" action="/ui/entries/{e.id}/delete">
        <button class="btn-link danger" type="submit" onclick="return confirm('Delete?')">×</button>
      </form>
  </div>
</div>"""


def bookmark_card(b: Bookmark) -> str:
    label = escape(b.title or b.url)
    notes = f'<div class="body">{md(b.notes)}</div>' if b.notes else ""
    return f"""<div class="card">
  <a href="{escape(b.url)}"><strong>{label}</strong></a>
  {notes}
  <div class="meta">
    {_tags_html(b.tags)}
    · {_fmt_time(b.created_at)}
    · <form class="inline" method="post" action="/ui/bookmarks/{b.id}/delete">
        <button class="btn-link danger" type="submit" onclick="return confirm('Delete?')">×</button>
      </form>
  </div>
</div>"""


def entry_form() -> str:
    return """<form method="post" action="/ui/entries">
  <label>What did you learn today? (Markdown supported)</label>
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
  <label>Notes (optional, Markdown supported)</label>
  <textarea name="notes" rows="2"></textarea>
  <label>Tags (optional, comma-separated)</label>
  <input name="tags">
  <button type="submit">Save bookmark</button>
</form>"""


def search_form(q: str = "") -> str:
    return f"""<form class="row" method="get" action="/">
  <input name="q" placeholder="Search entries…" value="{escape(q)}">
  <button type="submit">Search</button>
</form>"""


def home(
    entries: list[Entry],
    bookmarks: list[Bookmark],
    reactions_by_entry: dict[int, list[Reaction]],
    highlighted_ids: set[int],
    daily_prompt: str | None = None,
    q: str = "",
    user_email: str | None = None,
) -> str:
    prompt_html = (
        f'<div class="banner">💭 <strong>Today\'s prompt:</strong> {escape(daily_prompt)}</div>'
        if daily_prompt
        else ""
    )
    entries_html = (
        "".join(
            entry_card(e, reactions_by_entry.get(e.id, []), e.id in highlighted_ids)
            for e in entries
        )
        if entries
        else '<p class="empty">No entries yet.</p>'
    )
    bookmarks_html = (
        "".join(bookmark_card(b) for b in bookmarks)
        if bookmarks
        else '<p class="empty">No bookmarks yet.</p>'
    )
    body = f"""{prompt_html}
<div class="grid">
  <section>
    <h2>📝 Entries</h2>
    {search_form(q)}
    {entry_form()}
    {entries_html}
  </section>
  <section>
    <h2>🔖 Bookmarks</h2>
    {bookmark_form()}
    {bookmarks_html}
  </section>
</div>"""
    return page("Home", body, user_email)


def digests_page(digests: list[Digest], user_email: str | None = None) -> str:
    items = (
        "".join(
            f'<div class="card"><strong>{d.period.capitalize()}: '
            f"{d.start_date} → {d.end_date}</strong>"
            f'<div class="meta">{_fmt_time(d.created_at)}</div>'
            f'<div class="body">{md(d.content)}</div></div>'
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
    return page("Digests", body, user_email)


def stats_page(s: Stats, user_email: str | None = None) -> str:
    max_count = max((w.count for w in s.weekly_counts), default=1) or 1
    bars = "".join(
        f'<div class="bar" title="{w.week_start}: {w.count}" '
        f'style="height: {max(2, int(w.count * 56 / max_count))}px"></div>'
        for w in s.weekly_counts
    )
    tag_html = (
        " ".join(
            f'<span class="tag">{escape(name)} ×{count}</span>'
            for name, count in s.top_tags.items()
        )
        if s.top_tags
        else '<span class="empty">No tags yet.</span>'
    )
    body = f"""<section>
  <h2>📈 Stats</h2>
  <div class="stat-grid">
    <div class="stat"><div class="num">{s.total_entries}</div><div class="label">Total entries</div></div>
    <div class="stat"><div class="num">{s.entries_this_week}</div><div class="label">This week</div></div>
    <div class="stat"><div class="num">{s.current_streak_days}</div><div class="label">Current streak (days)</div></div>
    <div class="stat"><div class="num">{s.longest_streak_days}</div><div class="label">Longest streak (days)</div></div>
  </div>
  <h2>Last 12 weeks</h2>
  <div class="sparkline">{bars}</div>
  <h2>Top tags</h2>
  <p>{tag_html}</p>
</section>"""
    return page("Stats", body, user_email)


def ask_page(
    question: str = "",
    answer: str | None = None,
    sources: list[Entry] | None = None,
    user_email: str | None = None,
) -> str:
    answer_html = ""
    if answer is not None:
        sources_html = (
            "".join(
                f'<div class="card"><div class="body">{md(s.text)}</div>'
                f'<div class="meta">{_tags_html(s.tags)} · {_fmt_time(s.created_at)}</div></div>'
                for s in (sources or [])
            )
            if sources
            else '<p class="empty">No relevant entries.</p>'
        )
        answer_html = f"""<h2>Answer</h2>
<div class="card"><div class="body">{md(answer)}</div></div>
<h2>Cited sources</h2>
{sources_html}"""
    body = f"""<section>
  <h2>💬 Ask your journal</h2>
  <form method="post" action="/ui/ask">
    <label>Question</label>
    <input name="question" required placeholder="What did I learn about Python this month?"
           value="{escape(question)}">
    <button type="submit">Ask</button>
  </form>
  {answer_html}
</section>"""
    return page("Ask", body, user_email)


def share_view(e: Entry) -> str:
    body = f"""<section>
  <div class="card">
    <div class="body">{md(e.text)}</div>
    <div class="meta">
      {_tags_html(e.tags)}
      · {_fmt_time(e.created_at)}
      {f' · <a href="{escape(e.source)}">source</a>' if e.source else ''}
    </div>
  </div>
  <p class="note">Shared from a TIL Journal.</p>
</section>"""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shared TIL</title>
<style>{_CSS}</style>
</head>
<body>
<header><h1>📓 Shared TIL</h1></header>
{body}
</body>
</html>"""
