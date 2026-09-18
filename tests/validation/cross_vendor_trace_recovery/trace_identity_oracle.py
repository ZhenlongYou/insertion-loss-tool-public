from __future__ import annotations

from itertools import permutations

import numpy as np


def _best_bijective_error(errors: np.ndarray) -> float:
    return float(
        min(
            max(errors[row, column] for row, column in enumerate(assignment))
            for assignment in permutations(range(errors.shape[1]))
        )
    )


def main() -> int:
    threshold_px = 4.0
    # An identity-preserving result has one low-error column for each physical
    # reference.  A count-only or independent-nearest check would incorrectly
    # accept the escaped matrix because two references choose the same trace.
    identity_preserved = np.asarray(
        [
            [0.5, 23.5, 126.0, 144.0],
            [23.0, 0.5, 103.0, 127.0],
            [125.0, 102.0, 0.5, 28.0],
            [129.0, 113.0, 28.0, 0.5],
        ]
    )
    escaped_identity_hop = np.asarray(
        [
            [0.5, 23.5, 24.0, 126.0],
            [23.0, 0.5, 1.0, 103.0],
            [125.5, 102.5, 102.0, 0.0],
            [129.5, 113.5, 113.0, 28.0],
        ]
    )
    if _best_bijective_error(identity_preserved) > threshold_px:
        raise RuntimeError("identity-preserving reference was rejected")
    if _best_bijective_error(escaped_identity_hop) <= threshold_px:
        raise RuntimeError("cross-trace hopping was not rejected")
    print("TRACE_IDENTITY_ORACLE_OK · bijective-path-assignment · threshold_px=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
