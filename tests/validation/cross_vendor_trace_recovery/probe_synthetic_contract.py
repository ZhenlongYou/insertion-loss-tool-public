from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

source_root = Path(__file__).resolve().parents[3] / "src"
package = types.ModuleType("insertion_loss_tool")
package.__path__ = [str(source_root / "insertion_loss_tool")]
sys.modules["insertion_loss_tool"] = package

from insertion_loss_tool.datasheet_digitizer import (
    DigitizedCurve,
    _collapse_antialias_alias_tracks,
    digitize_plot_image,
)


def _digitize(path: Path) -> tuple[int, tuple[int, int, int, int]]:
    result = digitize_plot_image(
        path,
        start_hz=1.0,
        stop_hz=40e9,
        y_min_db=-50.0,
        y_max_db=0.0,
        run_ocr=False,
    )
    return len(result.curves), result.plot_box


def _four_line_product_plot(path: Path) -> None:
    image = Image.new("RGB", (1030, 430), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 55, 54, 972, 276
    for index in range(6):
        x = round(left + (right - left) * index / 5)
        draw.line((x, top, x, bottom), fill=(150, 150, 150))
    for index in range(4):
        y = round(top + (bottom - top) * index / 3)
        draw.line((left, y, right, y), fill=(150, 150, 150))
    draw.line((left, 100, right, 170), fill=(244, 151, 60), width=2)
    draw.line((left, 108, right, 184), fill=(156, 186, 86), width=2)
    image.save(path)


def _pale_product_plot(path: Path) -> None:
    image = Image.new("RGB", (389, 321), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 44, 62, 372, 261
    for index in range(11):
        x = round(left + (right - left) * index / 10)
        draw.line((x, top, x, bottom), fill=(242, 242, 242))
    for index in range(6):
        y = round(top + (bottom - top) * index / 5)
        draw.line((left, y, right, y), fill=(242, 242, 242))
    draw.line((left, 96, right, 130), fill=(246, 184, 45), width=2)
    image.save(path)


def _curve(rgb: tuple[int, int, int], x: np.ndarray, y: np.ndarray) -> DigitizedCurve:
    return DigitizedCurve(
        color="Synthetic",
        rgb=rgb,
        frequency_hz=x.copy(),
        magnitude_db=-y.copy(),
        pixel_points=np.column_stack((x, y)),
        confidence=0.8,
        observed_samples=x.size,
        sample_provenance=("observed",) * x.size,
    )


def _verify_antialias_contract() -> None:
    x_full = np.arange(481, dtype=np.float64)
    x_sparse = x_full[::2]
    curves = (
        _curve((244, 151, 60), x_full, 100 + 0.02 * x_full),
        _curve((156, 186, 86), x_full, 104 + 0.02 * x_full),
        _curve((178, 176, 76), x_sparse, 102 + 0.02 * x_sparse),
    )
    recovered = _collapse_antialias_alias_tracks(curves, (0, 0, 480, 200))
    if len(recovered) != 2:
        raise RuntimeError(f"blended alias returned {len(recovered)} traces")


def main() -> int:
    partitions = json.loads(
        Path(__file__).with_name("partitions.json").read_text(encoding="utf-8")
    )["partitions"]
    required = {
        "nominal",
        "boundary",
        "invalid",
        "adversarial",
        "realistic",
        "known_failure",
    }
    try:
        if set(partitions) != required:
            raise RuntimeError("partition mismatch")
        with tempfile.TemporaryDirectory(prefix="cross-vendor-contract-") as directory:
            root = Path(directory)
            boundary = root / "four-line.png"
            _four_line_product_plot(boundary)
            count, box = _digitize(boundary)
            if (count, box) != (2, (55, 54, 972, 276)):
                raise RuntimeError(f"four-line result was count={count}, box={box}")

            pale = root / "pale.png"
            _pale_product_plot(pale)
            count, box = _digitize(pale)
            if (count, box) != (1, (44, 62, 372, 261)):
                raise RuntimeError(f"pale-grid result was count={count}, box={box}")

            blank = root / "blank.png"
            Image.new("RGB", (640, 480), "white").save(blank)
            try:
                _digitize(blank)
            except ValueError as error:
                if "regular plot grid" not in str(error):
                    raise
            else:
                raise RuntimeError("blank page did not fail closed")
        _verify_antialias_contract()
    except Exception as error:
        print("CROSS-VENDOR-RECOVERY failure-signature")
        print(f"behavioural_failure={error}")
        return 7
    print("CROSS-VENDOR-RECOVERY GREEN · 6 partitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
