from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    dataset = Path("evals/queries.example.jsonl")
    if not dataset.exists():
        raise SystemExit("Missing eval dataset")

    rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(rows)} eval queries")
    print("Wire this script to call /v1/ask and compute citation coverage + groundedness.")


if __name__ == "__main__":
    main()
