from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))


def main() -> int:
    width = 481
    gap_start, gap_stop = CASES["known_failure"]["gap"]
    missing = gap_stop - gap_start + 1
    sparse_fraction = missing / width
    if sparse_fraction >= 0.05:
        raise AssertionError("known failure is not sparse enough to challenge p95")
    if not (gap_start <= CASES["known_failure"]["probe_x"] <= gap_stop):
        raise AssertionError("absolute local oracle does not probe the known gap")
    excursion_start, excursion_stop = CASES["adversarial"]["excursion"]
    if excursion_stop - excursion_start + 1 >= width * 0.05:
        raise AssertionError("adversarial excursion is not locally sparse")
    if CASES["nominal"]["expected_review_reasons"]:
        raise AssertionError("nominal curve must remain clear")
    print(
        "ORACLE_OK sparse local intervals are absolute; "
        f"known gap is {100 * sparse_fraction:.2f}% and can evade whole-curve p95"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
