"""Check that the built wheel contains public package files only."""

from __future__ import annotations

import zipfile
from pathlib import Path


def main() -> int:
    wheels = sorted(Path("dist").glob("cyrisk_ccm-0.1.0-*.whl"))
    if len(wheels) != 1:
        raise SystemExit("expected exactly one cyrisk_ccm v0.1.0 wheel")
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    required = {
        "cyrisk_ccm/__init__.py",
        "cyrisk_ccm/adapter.py",
        "cyrisk_ccm/models.py",
        "cyrisk_ccm/py.typed",
    }
    missing = required - names
    if missing:
        raise SystemExit(f"wheel missing required content: {sorted(missing)}")
    forbidden = {name for name in names if name.startswith("tests/") or ".env" in name}
    if forbidden:
        raise SystemExit(f"wheel contains forbidden content: {sorted(forbidden)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
