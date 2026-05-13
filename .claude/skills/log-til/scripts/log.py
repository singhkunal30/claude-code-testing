"""Read JSON {text, source?, tags?} from stdin and create an Entry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from app.db import init_db  # noqa: E402
from app.models.entry import EntryCreate  # noqa: E402
from app.routers.entries import create_entry  # noqa: E402


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("error: expected JSON on stdin with at least a 'text' field", file=sys.stderr)
        return 1
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 1

    init_db()
    entry = create_entry(EntryCreate.model_validate(data))
    print(entry.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
