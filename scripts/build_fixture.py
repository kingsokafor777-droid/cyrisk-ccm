"""Verify the committed sealed synthetic fixture is reproducible."""

from __future__ import annotations

import json
from pathlib import Path

from cyrisk_ccm.adapter import adapt
from cyrisk_ccm.models import AdapterRequest

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "fixtures" / "synthetic_request.json"
OUTPUT = ROOT / "fixtures" / "synthetic_result.json"


def main() -> int:
    request = AdapterRequest.model_validate_json(INPUT.read_text(encoding="utf-8"))
    rendered = adapt(request).model_dump(mode="json")
    expected = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if rendered != expected:
        raise SystemExit(
            "sealed fixture differs; review the adapter or update fixture deliberately"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
