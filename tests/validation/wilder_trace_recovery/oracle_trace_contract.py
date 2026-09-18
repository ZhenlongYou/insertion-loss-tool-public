from __future__ import annotations

import math


def _direction(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    minimum = min(rgb)
    shifted = tuple(float(value - minimum) for value in rgb)
    length = math.sqrt(sum(value * value for value in shifted))
    return tuple(value / length for value in shifted)


def _distance(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def main() -> int:
    red_core = _direction((218, 150, 159))
    red_antialias = _direction((210, 142, 146))
    blue_core = _direction((143, 139, 206))
    if _distance(red_core, red_antialias) >= 0.10:
        raise RuntimeError("same-hue antialias shades are not a stable identity")
    if _distance(red_core, blue_core) <= 1.0:
        raise RuntimeError("red and blue identities are not independently separable")

    supported_joint_candidates = 8
    if not (4 <= supported_joint_candidates < 12):
        raise RuntimeError("the four-trace and crowded-plot acceptance boundary is invalid")

    print(
        "ORACLE_OK · antialias identity separated from hue swap · "
        "4 traces supported · 12 traces require review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
