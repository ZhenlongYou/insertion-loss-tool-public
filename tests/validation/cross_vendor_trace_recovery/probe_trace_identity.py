from __future__ import annotations

from itertools import permutations
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


def _synthetic_identity_probe() -> tuple[int, float]:
    left, top, right, bottom = 100, 70, 660, 470
    with tempfile.TemporaryDirectory(prefix="trace-identity-probe-") as directory:
        path = Path(directory) / "two-blue-identities.png"
        image = Image.new("RGB", (760, 540), "white")
        draw = ImageDraw.Draw(image)
        for index in range(11):
            x = round(left + (right - left) * index / 10)
            y = round(top + (bottom - top) * index / 10)
            draw.line((x, top, x, bottom), fill=(190, 190, 190))
            draw.line((left, y, right, y), fill=(190, 190, 190))

        expected: list[np.ndarray] = []
        for colour, vertical in (
            ((255, 120, 120), lambda x: 190 + 0.12 * (x - left)),
            ((80, 80, 255), lambda x: 205 + 0.15 * (x - left)),
            ((100, 190, 110), lambda x: 350 + 18 * np.sin((x - left) / 17)),
        ):
            points = np.asarray(
                [(x, round(vertical(x))) for x in range(left, right + 1)],
                dtype=np.float64,
            )
            expected.append(points)
            draw.line(
                [tuple(point.astype(int)) for point in points],
                fill=colour,
                width=2,
            )

        blue_grey: list[tuple[int, int]] = []
        starts = (left, left + 220, left + 288, left + 356, left + 424, left + 492)
        levels = (330, 420, 345, 435, 360, 410)
        for index, start in enumerate(starts):
            stop = starts[index + 1] if index + 1 < len(starts) else right + 1
            points = [
                (x, levels[index] + round(6 * np.sin((x - start) / 10)))
                for x in range(start, stop)
            ]
            blue_grey.extend(points)
            draw.line(points, fill=(100, 140, 180), width=2)
        expected.append(np.asarray(blue_grey, dtype=np.float64))
        image.save(path)

        result = digitize_plot_image(
            path,
            start_hz=50e6,
            stop_hz=40e9,
            y_min_db=-50,
            y_max_db=0,
            run_ocr=False,
        )

    if len(result.curves) != len(expected):
        raise RuntimeError(
            f"expected {len(expected)} physical traces, got {len(result.curves)}"
        )
    errors = np.full((len(expected), len(result.curves)), np.inf)
    for expected_index, reference in enumerate(expected):
        for actual_index, curve in enumerate(result.curves):
            actual_x = curve.pixel_points[:, 0]
            overlap = (reference[:, 0] >= actual_x[0]) & (
                reference[:, 0] <= actual_x[-1]
            )
            if np.count_nonzero(overlap) < reference.shape[0] * 0.95:
                continue
            actual_y = np.interp(
                reference[overlap, 0], actual_x, curve.pixel_points[:, 1]
            )
            errors[expected_index, actual_index] = float(
                np.median(np.abs(actual_y - reference[overlap, 1]))
            )
    best = min(
        max(errors[row, column] for row, column in enumerate(assignment))
        for assignment in permutations(range(len(result.curves)))
    )
    if not np.isfinite(best) or best > 4.0:
        raise RuntimeError(f"no one-to-one physical path assignment: {errors.tolist()}")
    return len(result.curves), float(best)


def _local_wilder_probe() -> tuple[str, float]:
    path = Path(__file__).with_name("local_corpus") / "wilder-910-0077-fig36.png"
    if not path.exists():
        return "not_available", float("nan")
    result = digitize_plot_image(
        path,
        start_hz=50e6,
        stop_hz=40e9,
        y_min_db=-50,
        y_max_db=0,
        run_ocr=False,
    )
    if len(result.curves) != 4:
        raise RuntimeError(f"Wilder Figure 36 expected 4 traces, got {len(result.curves)}")
    left, top, right, bottom = result.plot_box
    width = right - left + 1
    height = bottom - top + 1
    worst_p95 = 0.0
    for index, curve in enumerate(result.curves, 1):
        span = float(curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1)
        if span < width * 0.95:
            raise RuntimeError(f"Wilder Figure 36 trace {index} is partial: span={span}")
        adjacent_jump = np.abs(np.diff(curve.pixel_points[:, 1]))
        p95 = float(np.quantile(adjacent_jump, 0.95))
        worst_p95 = max(worst_p95, p95)
        if p95 > height * 0.03:
            raise RuntimeError(
                f"Wilder Figure 36 trace {index} hops between paths: p95={p95:.3f}"
            )
    curves_by_color = {curve.color: curve for curve in result.curves}
    # These points are manual physical-path anchors on the hash-bound Figure
    # 36 raster.  They target the exact short swaps and same-colour legend
    # excursions that a global p95 statistic previously hid.
    identity_anchors = {
        "Dark blue": {
            576: 755.0,
            585: 762.0,
            1349: 695.0,
            1411: 704.0,
            1453: 710.0,
        },
        "Green": {
            1265: 704.0,
            1280: 698.0,
            1289: 698.0,
            1338: 688.0,
            1349: 695.0,
            1357: 706.0,
            1367: 701.0,
            1377: 687.0,
        },
    }
    for color, anchors in identity_anchors.items():
        curve = curves_by_color.get(color)
        if curve is None:
            raise RuntimeError(f"Wilder Figure 36 missing {color} identity")
        for x_pixel, expected_y in anchors.items():
            actual_y = float(
                np.interp(
                    x_pixel,
                    curve.pixel_points[:, 0],
                    curve.pixel_points[:, 1],
                )
            )
            if abs(actual_y - expected_y) > 15.0:
                raise RuntimeError(
                    "Wilder Figure 36 physical identity mismatch: "
                    f"{color} x={x_pixel} expected_y={expected_y:.1f} "
                    f"actual_y={actual_y:.1f}"
                )
    return "passed", worst_p95


def main() -> int:
    test_id = "probe_ambiguous_hue_identity"
    try:
        trace_count, assignment_error = _synthetic_identity_probe()
        wilder_status, wilder_p95 = _local_wilder_probe()
    except Exception as error:
        print("IMAGE-TRACE-IDENTITY failure-signature")
        print(test_id)
        print(f"behavioural_failure={error}")
        return 9
    print(
        "IMAGE-TRACE-IDENTITY GREEN · "
        f"{test_id} · trace_count={trace_count} · "
        f"assignment_error_px={assignment_error:.3f} · "
        f"wilder={wilder_status} · wilder_worst_p95_px={wilder_p95:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
