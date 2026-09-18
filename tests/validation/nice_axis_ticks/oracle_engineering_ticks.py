from __future__ import annotations

import json
import math
from pathlib import Path


CASE_DIR = Path(__file__).with_name("cases")


def nice_step(minimum: float, maximum: float, intervals: int) -> float:
    raw = abs(maximum - minimum) / max(1, intervals)
    power = 10 ** math.floor(math.log10(raw))
    fraction = raw / power
    multiplier = 1 if fraction <= 1 else 2 if fraction <= 2 else 5 if fraction <= 5 else 10
    return multiplier * power


def phase_step(minimum: float, maximum: float, intervals: int) -> float:
    raw = abs(maximum - minimum) / max(1, intervals)
    for candidate in (1, 2, 5, 10, 15, 30, 45, 90, 180, 360):
        if candidate >= raw:
            return float(candidate)
    return 360 * nice_step(0, raw / 360, 1)


def ticks(minimum: float, maximum: float, intervals: int, kind: str) -> list[int | float]:
    step = phase_step(minimum, maximum, intervals) if kind == "phase" else nice_step(minimum, maximum, intervals)
    low = math.floor(minimum / step) * step
    high = math.ceil(maximum / step) * step
    return [round(low + index * step, 12) for index in range(round((high - low) / step) + 1)]


def main() -> int:
    expected = {
        "nominal": [0, 10, 20, 30, 40],
        "boundary": [-25, -20, -15, -10, -5, 0],
        "adversarial": [-1440, -1080, -720, -360, 0, 360],
    }
    for name, wanted in expected.items():
        case = json.loads((CASE_DIR / f"{name}.json").read_text(encoding="utf-8"))
        if ticks(case["minimum"], case["maximum"], case["target_intervals"], case["kind"]) != wanted:
            return 3
    print("ORACLE_OK engineering 1-2-5 frequency/dB ticks and 360-degree phase grid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
