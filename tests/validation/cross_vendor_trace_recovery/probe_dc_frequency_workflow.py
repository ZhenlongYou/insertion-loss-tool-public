from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.datasheet_digitizer import DigitizationResult, DigitizedCurve
from insertion_loss_tool.touchstone import read_touchstone
from insertion_loss_tool.webview_gui import InsertionLossWebApi


def main() -> int:
    test_id = "probe_dc_frequency_workflow"
    try:
        api = InsertionLossWebApi()
        api.set_network_ports(0, 2)
        with tempfile.TemporaryDirectory(prefix="dc-frequency-probe-") as directory, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(directory)
        ):
            image = Path(directory) / "dc-trace.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            explicit = api.set_image_frequency(0, "0GHz", "5GHz", "0.1GHz", "linear")
            if not explicit.get("ok") or explicit["image_update"]["axis"]["points"] != 51:
                raise RuntimeError(f"explicit GHz DC calibration failed: {explicit}")
            unitless = api.set_image_frequency(0, "0", "5", "0.1", "linear")
            axis = unitless.get("image_update", {}).get("axis", {})
            if not unitless.get("ok") or (
                axis.get("start_hz"), axis.get("stop_hz"), axis.get("step_hz")
            ) != (0.0, 5e9, 0.1e9):
                raise RuntimeError(f"unitless GHz calibration failed: {unitless}")
            logarithmic = api.set_image_frequency(0, "0", "5", "0.1", "log")
            if logarithmic.get("ok") or "对数频率" not in str(logarithmic.get("error")):
                raise RuntimeError("logarithmic DC was not rejected")

            result = DigitizationResult(
                image_width=100,
                image_height=80,
                plot_box=(10, 10, 90, 70),
                curves=(
                    DigitizedCurve(
                        color="Dark blue",
                        rgb=(36, 76, 206),
                        frequency_hz=np.array([0.0, 2.5e9, 5e9]),
                        magnitude_db=np.array([-0.1, -1.0, -2.0]),
                        pixel_points=np.column_stack(
                            (np.linspace(10, 90, 3), np.linspace(10, 20, 3))
                        ),
                        confidence=1.0,
                    ),
                ),
            )
            api.set_image_frequency(0, "0", "5", "0.1", "linear")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=result,
            ):
                digitized = api.digitize_image(0, -6, 0)
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
            if reread.frequency_hz[0] != 0.0 or reread.frequency_hz[-1] != 5e9:
                raise RuntimeError("Touchstone DC endpoints were not preserved")
    except Exception as error:
        print("IMAGE-DC-FREQUENCY failure-signature")
        print(test_id)
        print(f"behavioural_failure={error}")
        return 7
    print(f"IMAGE-DC-FREQUENCY GREEN · {test_id} · explicit-and-unitless-GHz · DC-reread")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
