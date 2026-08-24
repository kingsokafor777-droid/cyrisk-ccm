"""Local JSON-in/JSON-out entry point for the offline adapter."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .adapter import adapt
from .models import AdapterRequest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Adapt supplied CCM references without network access."
    )
    parser.add_argument("input", type=Path, help="AdapterRequest JSON path")
    parser.add_argument("output", type=Path, help="AdapterResult JSON path")
    args = parser.parse_args(argv)
    request = AdapterRequest.model_validate_json(args.input.read_text(encoding="utf-8"))
    result = adapt(request)
    args.output.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
