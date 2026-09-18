from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


def main() -> int:
    test_id = "probe_unique_hue_full_span"
    left, top, right, bottom = 100, 70, 660, 470
    try:
        with tempfile.TemporaryDirectory(prefix="partial-trace-probe-") as directory:
            path = Path(directory) / "wilder-fragmented-prefix.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            boundaries = (left, 212, 296, right + 1)
            levels = (220, 350, 275)
            for start, stop, level in zip(boundaries, boundaries[1:], levels):
                points = [
                    (x, level + round(4 * np.sin((x - left) / 17)))
                    for x in range(start, stop)
                ]
                draw.line(points, fill=(216, 54, 64), width=2)
            for x in range(150, 651, 100):
                draw.point((x, 410), fill=(216, 54, 64))
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=50e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )
        if len(result.curves) != 1:
            raise RuntimeError(f"expected one physical hue, got {len(result.curves)}")
        curve = result.curves[0]
        if curve.pixel_points[0, 0] > left + 2:
            raise RuntimeError(
                f"prefix missing: first x is {curve.pixel_points[0, 0]:.1f}"
            )
        if curve.pixel_points[-1, 0] < right - 2:
            raise RuntimeError(
                f"suffix missing: last x is {curve.pixel_points[-1, 0]:.1f}"
            )
        if curve.observed_samples < round((right - left + 1) * 0.95):
            raise RuntimeError(
                f"insufficient observed support: {curve.observed_samples}"
            )
    except Exception as error:
        print("IMAGE-PARTIAL-TRACE failure-signature")
        print(test_id)
        print(f"behavioural_failure={error}")
        return 7
    print(
        "IMAGE-PARTIAL-TRACE GREEN · "
        f"{test_id} · full-span-observed-hue · sparse-contamination-tolerated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
