"""CLI entry points for the TIL journal.

Usage:
    uv run python -m app.cli digest [--period week|month] [--end-date YYYY-MM-DD]
    uv run python -m app.cli stats

Reads SUPABASE_URL / SUPABASE_KEY from the environment (or .env).
Designed to be cron-friendly: writes the digest to stdout.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from app.models.digest import DigestCreate
from app.routers.digests import generate as generate_digest_endpoint
from app.supabase import client


def cmd_digest(args: argparse.Namespace) -> int:
    payload = DigestCreate(
        period=args.period,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
    )
    digest = generate_digest_endpoint(payload)
    print(digest.content)
    print(f"\n# Saved as digest id={digest.id}", file=sys.stderr)
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    sb = client()
    entries = sb.select("entries", order="created_at.desc", limit=1)
    n_entries = len(sb.select("entries", limit=500))
    n_digests = len(sb.select("digests", limit=500))
    print(f"entries: {n_entries}")
    print(f"digests: {n_digests}")
    print(f"latest entry: {entries[0]['created_at'] if entries else '<none>'}")
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
