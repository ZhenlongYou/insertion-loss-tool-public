from __future__ import annotations

import argparse
import hashlib
import json
import sys
import types
from pathlib import Path

from PIL import Image

source_root = Path(__file__).resolve().parents[3] / "src"
package = types.ModuleType("insertion_loss_tool")
package.__path__ = [str(source_root / "insertion_loss_tool")]
sys.modules["insertion_loss_tool"] = package

from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the local-only cross-vendor product-plot corpus."
    )
    parser.add_argument("images", type=Path, help="Directory containing hashed crops")
    args = parser.parse_args()
    manifest_path = Path(__file__).with_name("cases.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    axis = manifest["axis_for_trace_count_probe"]
    outcomes: list[dict[str, object]] = []
    for case in manifest["cases"]:
        image_path = args.images / case["file"]
        payload = image_path.read_bytes()
        actual_hash = hashlib.sha256(payload).hexdigest()
        with Image.open(image_path) as image:
            actual_size = list(image.size)
        result = digitize_plot_image(
            image_path,
            start_hz=axis["start_hz"],
            stop_hz=axis["stop_hz"],
            y_min_db=axis["y_min_db"],
            y_max_db=axis["y_max_db"],
            run_ocr=False,
        )
        outcome = {
            "id": case["id"],
            "hash_ok": actual_hash == case["sha256"],
            "size_ok": actual_size == case["size"],
            "plot_box": list(result.plot_box),
            "plot_box_ok": list(result.plot_box) == case["expected_plot_box"],
            "trace_count": len(result.curves),
            "trace_count_ok": len(result.curves) == case["expected_trace_count"],
        }
        outcomes.append(outcome)
    passed = all(
        all(outcome[key] for key in ("hash_ok", "size_ok", "plot_box_ok", "trace_count_ok"))
        for outcome in outcomes
    )
    print(json.dumps({"passed": passed, "cases": outcomes}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
