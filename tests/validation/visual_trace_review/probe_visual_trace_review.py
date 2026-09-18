from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))


def _base_image() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(image)
    for index in range(11):
        x = 80 + 48 * index
        y = 50 + 36 * index
        draw.line((x, 50, x, 410), fill=(190, 190, 190))
        draw.line((80, y, 560, y), fill=(190, 190, 190))
    return image, draw


def _digitize(path: Path):
    return digitize_plot_image(
        path,
        start_hz=1e9,
        stop_hz=5e9,
        y_min_db=-40,
        y_max_db=0,
        run_ocr=False,
    )


def _reason_covering(curve, reason: str, x: float) -> bool:
    return any(
        region.reason == reason and region.start_x <= x <= region.end_x
        for region in curve.review_regions
    )


def _check_local_wilder() -> str:
    path = ROOT.parent / "cross_vendor_trace_recovery" / "local_corpus" / "wilder-910-0077-fig36.png"
    if not path.exists():
        return "not_available"
    result = digitize_plot_image(
        path,
        start_hz=50e6,
        stop_hz=40e9,
        y_min_db=-50,
        y_max_db=0,
        run_ocr=False,
    )
    by_colour = {curve.color: curve for curve in result.curves}
    required = {
        "Dark blue": (576, 585, 1349, 1411, 1453),
        "Green": (1265, 1280, 1289, 1338, 1349, 1357, 1367, 1377),
    }
    for colour, locations in required.items():
        curve = by_colour.get(colour)
        if curve is None:
            raise AssertionError(f"Wilder Figure 36 has no {colour} trace")
        for x in locations:
            if not any(region.start_x <= x <= region.end_x for region in curve.review_regions):
                raise AssertionError(f"Wilder Figure 36 {colour} x={x} is not exposed")
    return "passed"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)

        nominal, draw = _base_image()
        draw.line(
            [(x, 250 + round(20 * np.sin((x - 80) / 50))) for x in range(80, 561)],
            fill=(210, 50, 60),
            width=2,
        )
        nominal_path = folder / "nominal.png"
        nominal.save(nominal_path)
        nominal_curve = _digitize(nominal_path).curves[0]
        if nominal_curve.review_status != "clear":
            print("VISUAL-REVIEW-001 failure-signature nominal false positive")
            return 7

        gap_image = nominal.copy()
        ImageDraw.Draw(gap_image).rectangle((315, 200, 324, 300), fill="white")
        gap_path = folder / "known-failure-gap.png"
        gap_image.save(gap_path)
        gap_curve = _digitize(gap_path).curves[0]
        probe_x = float(CASES["known_failure"]["probe_x"])
        if not _reason_covering(gap_curve, "raster_gap", probe_x):
            print("VISUAL-REVIEW-001 failure-signature sparse gap was hidden")
            return 7

        excursion, draw = _base_image()
        points = []
        for x in range(80, 561):
            y = 300 + round(5 * np.sin((x - 80) / 30))
            if 310 <= x <= 318:
                y = 170
            points.append((x, y))
        draw.line(points, fill=(50, 160, 70), width=2)
        excursion_path = folder / "same-colour-excursion.png"
        excursion.save(excursion_path)
        excursion_curve = _digitize(excursion_path).curves[0]
        if not _reason_covering(excursion_curve, "upward_excursion", 314):
            print("VISUAL-REVIEW-001 failure-signature local topology error was hidden")
            return 7

        try:
            digitize_plot_image(
                nominal_path,
                start_hz=CASES["invalid"]["start_hz"],
                stop_hz=CASES["invalid"]["stop_hz"],
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )
        except ValueError as exc:
            if CASES["invalid"]["expected_error"] not in str(exc):
                raise
        else:
            print("VISUAL-REVIEW-001 failure-signature invalid calibration accepted")
            return 7

    wilder = _check_local_wilder()
    print(
        "VISUAL-REVIEW-001 GREEN local regions visible through public digitizer "
        f"wilder_figure_36={wilder}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
