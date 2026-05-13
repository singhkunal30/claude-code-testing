"""CLI entry points for the TIL journal.

Usage:
    uv run python -m app.cli digest [--period week|month] [--end-date YYYY-MM-DD]
    uv run python -m app.cli stats

Designed to be cron-friendly: writes to the same SQLite DB the API uses
and prints the generated digest (or a brief summary) to stdout.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from app.db import init_db
from app.models.digest import DigestCreate
from app.routers.digests import generate as generate_digest_endpoint


def cmd_digest(args: argparse.Namespace) -> int:
    init_db()
    payload = DigestCreate(
        period=args.period,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
    )
    digest = generate_digest_endpoint(payload)
    print(digest.content)
    print(f"\n# Saved as digest id={digest.id}", file=sys.stderr)
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    from app.db import db_session

    init_db()
    with db_session() as conn:
        n_entries = conn.execute("SELECT COUNT(*) AS c FROM entries").fetchone()["c"]
        n_digests = conn.execute("SELECT COUNT(*) AS c FROM digests").fetchone()["c"]
        latest = conn.execute(
            "SELECT created_at FROM entries ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    print(f"entries: {n_entries}")
    print(f"digests: {n_digests}")
    print(f"latest entry: {latest['created_at'] if latest else '<none>'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="til")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_digest = sub.add_parser("digest", help="Generate a digest")
    p_digest.add_argument("--period", choices=["week", "month"], default="week")
    p_digest.add_argument("--end-date", default=None, help="YYYY-MM-DD; defaults to today UTC")
    p_digest.set_defaults(func=cmd_digest)

    p_stats = sub.add_parser("stats", help="Show DB stats")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
