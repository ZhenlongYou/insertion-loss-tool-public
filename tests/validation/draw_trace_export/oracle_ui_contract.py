from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "cases").glob("*.json"))
    }
    nominal = cases["nominal"]
    invalid = cases["invalid"]
    known = cases["known_failure"]
    expected_channels = list(invalid["expected_unassigned"])
    independently_derived_message = (
        f"Unassigned channels: {', '.join(expected_channels)}. Choose a detected trace, "
        "Return loss −20 dB, or Crosstalk −80 dB."
    )
    if nominal["expected_plot_count"] != nominal["ports"] ** 2:
        return 3
    if independently_derived_message != known["expected_message"]:
        return 4
    if cases["boundary"]["expected_distinct_colors"] != 2:
        return 5
    print("ORACLE_OK 2-port=4-plots two-traces=distinct exact-unassigned=S12,S21,S22")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
