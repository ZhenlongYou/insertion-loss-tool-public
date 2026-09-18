from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))[
        "cases"
    ]
    expected_counts = [2, 2, 2, 2, 1, 1, 1, 3]
    if [case["expected_trace_count"] for case in cases] != expected_counts:
        raise RuntimeError("human-counted vendor trace contract changed")
    if len({case["source"] for case in cases}) != 3:
        raise RuntimeError("cross-vendor source independence was lost")
    for case in cases:
        left, top, right, bottom = case["expected_plot_box"]
        width, height = case["size"]
        if not (0 <= left < right < width and 0 <= top < bottom < height):
            raise RuntimeError(f"invalid human-reviewed plot box: {case['id']}")
    print("ORACLE_OK · 8 human-counted plots · 3 official vendors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
