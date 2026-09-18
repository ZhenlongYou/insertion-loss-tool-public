from __future__ import annotations

import json
from pathlib import Path


REQUIRED = {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}


def main() -> int:
    cases = json.loads((Path(__file__).with_name("cases.json")).read_text(encoding="utf-8"))
    if set(cases) != REQUIRED:
        raise AssertionError(f"partition mismatch: {set(cases)!r}")
    for name, case in cases.items():
        if not case.get("description"):
            raise AssertionError(f"{name} has no observable description")
    print("SUITE_OK six visual-review partitions are frozen and non-empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
