from __future__ import annotations

import tempfile
import sys
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.datasheet_digitizer import DigitizationResult, DigitizedCurve
from insertion_loss_tool.touchstone import read_touchstone
from insertion_loss_tool.webview_gui import InsertionLossWebApi


def main() -> int:
    api = InsertionLossWebApi()
    api.set_network_ports(0, 2)
    frequency = np.array([1e9, 2e9, 3e9])
    detected = DigitizationResult(
        image_width=100,
        image_height=80,
        plot_box=(10, 10, 90, 70),
        curves=(
            DigitizedCurve(
                color="Dark blue",
                rgb=(36, 76, 206),
                frequency_hz=frequency,
                magnitude_db=np.array([0.0, -0.1, -0.2]),
                pixel_points=np.column_stack((np.linspace(10, 90, 3), np.linspace(10, 20, 3))),
                confidence=1.0,
            ),
        ),
    )
    try:
        with tempfile.TemporaryDirectory(prefix="matched-zero-probe-") as directory, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(directory)
        ):
            image = Path(directory) / "zero-db.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            api.set_image_frequency(0, "1GHz", "3GHz", "1GHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                digitized = api.digitize_image(0, -1, 0)
            source = next(
                option
                for option in digitized["networks"][0]["mapping_options"]["S21"]
                if option.startswith("图1 A ·")
            )
            for parameter, choice in (("S11", "匹配 0"), ("S22", "匹配 0"), ("S21", source)):
                if not api.set_mapping(0, parameter, choice).get("ok"):
                    raise RuntimeError(f"mapping failed: {parameter}")
            generated = api.generate_datasheet_network(0)
            if not generated.get("ok"):
                raise RuntimeError(str(generated.get("error")))
            reread = read_touchstone(generated["output"])
            if not np.all(reread.s[:, 0, 0] == 0.0) or not np.all(
                reread.s[:, 1, 1] == 0.0
            ):
                raise RuntimeError(
                    "matched fallback is not exact zero: "
                    f"S11={reread.s[:, 0, 0].tolist()} S22={reread.s[:, 1, 1].tolist()}"
                )
            if float(generated["sigma_max"]) > 1.0 + 1e-12:
                raise RuntimeError("sampled passivity exceeded")
    except Exception as error:
        print("IMAGE-WORKFLOW-MATCHED-ZERO failure-signature")
        print("test_id=probe_exact_matched_zero")
        print(f"behavioural_failure={error}")
        return 7
    print("IMAGE-WORKFLOW-MATCHED-ZERO GREEN · test_id=probe_exact_matched_zero")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
