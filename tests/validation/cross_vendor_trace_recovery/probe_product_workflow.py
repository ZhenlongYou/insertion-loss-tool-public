from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from insertion_loss_tool.touchstone import read_touchstone
from insertion_loss_tool.webview_gui import InsertionLossWebApi


def _case_by_id(manifest: dict[str, object], case_id: str) -> dict[str, object]:
    return next(case for case in manifest["cases"] if case["id"] == case_id)


def _register_and_digitize(
    api: InsertionLossWebApi,
    image_root: Path,
    case: dict[str, object],
) -> dict[str, object]:
    calibration = case["calibration"]
    image_path = image_root / case["file"]
    payload = image_path.read_bytes()
    with Image.open(image_path) as image:
        actual_size = list(image.size)
    api.register_images([image_path])
    image_index = len(api.get_defaults()["datasheet"]["images"]) - 1
    analyzed = api.analyze_image(image_index)
    frequency = api.set_image_frequency(
        image_index,
        calibration["start"],
        calibration["stop"],
        calibration["step"],
        calibration.get("spacing", "linear"),
    )
    digitized = api.digitize_image_with_axis(
        image_index,
        calibration["y_top_db"],
        calibration["y_bottom_db"],
        calibration["y_convention"],
    )
    update = digitized.get("image_update", {})
    preview_mode = case.get("preview_mode", "manual-axis")
    if preview_mode == "auto-axis":
        preview_ok = bool(analyzed.get("ok") and analyzed.get("auto_digitize"))
    else:
        preview_ok = (
            analyzed.get("image_update", {}).get("digitization", {}).get(
                "candidate_status"
            )
            == "preview"
            and int(analyzed.get("image_update", {}).get("candidates", -1))
            == case["expected_trace_count"]
        )
    plot_box = update.get("digitization", {}).get("plot_box", [])
    full_span_ok = True
    trace_spans: list[dict[str, float]] = []
    if case.get("expected_full_span"):
        if len(plot_box) != 4 or not update.get("curves"):
            full_span_ok = False
        else:
            left, _top, right, _bottom = (float(value) for value in plot_box)
            width = max(right - left, 1.0)
            for curve in update["curves"]:
                points = curve.get("preview_points", [])
                if not points:
                    full_span_ok = False
                    continue
                start_fraction = (float(points[0][0]) - left) / width
                stop_fraction = (float(points[-1][0]) - left) / width
                trace_spans.append(
                    {
                        "start_fraction": start_fraction,
                        "stop_fraction": stop_fraction,
                    }
                )
                full_span_ok = (
                    full_span_ok
                    and start_fraction <= 0.05
                    and stop_fraction >= 0.95
                )
    return {
        "id": case["id"],
        "hash_ok": hashlib.sha256(payload).hexdigest() == case["sha256"],
        "size_ok": actual_size == case["size"],
        "analysis_ok": bool(analyzed.get("ok")),
        "preview_trace_count": int(
            analyzed.get("image_update", {}).get("candidates", -1)
        ),
        "preview_ok": preview_ok,
        "frequency_ok": bool(frequency.get("ok")),
        "digitize_ok": bool(digitized.get("ok")),
        "trace_count": len(update.get("curves", [])),
        "trace_count_ok": len(update.get("curves", []))
        == case["expected_trace_count"],
        "trace_spans": trace_spans,
        "full_span_ok": full_span_ok,
    }


def _first_source(api: InsertionLossWebApi, image_number: int) -> str:
    options = api.get_defaults()["datasheet"]["networks"][0]["mapping_options"][
        "S21"
    ]
    prefix = f"图{image_number} A ·"
    return next(option for option in options if option.startswith(prefix))


def _generate_pair(
    image_root: Path,
    manifest: dict[str, object],
    first_id: str,
    second_id: str,
) -> dict[str, object]:
    first = _case_by_id(manifest, first_id)
    second = _case_by_id(manifest, second_id)
    with tempfile.TemporaryDirectory() as output_dir, mock.patch(
        "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(output_dir)
    ):
        api = InsertionLossWebApi()
        api.set_network_ports(0, 2)
        api.set_network_reciprocal(0, False)
        first_result = _register_and_digitize(api, image_root, first)
        second_result = _register_and_digitize(api, image_root, second)
        first_source = _first_source(api, 1)
        second_source = _first_source(api, 2)
        mappings_ok = all(
            api.set_mapping(0, parameter, source)["ok"]
            for parameter, source in (
                ("S11", "匹配 0"),
                ("S22", "匹配 0"),
                ("S21", first_source),
                ("S12", second_source),
            )
        )
        coverage = api.get_defaults()["datasheet"]["networks"][0]["coverage"]
        generated = api.generate_datasheet_network(0)
        reread_ok = False
        if generated.get("ok"):
            data = read_touchstone(generated["output"])
            reread_ok = bool(
                data.n_ports == 2
                and data.frequency_hz.size == generated["points"]
                and np.all(np.diff(data.frequency_hz) > 0)
                and np.isclose(data.frequency_hz[0], coverage["start_hz"])
                and np.isclose(data.frequency_hz[-1], coverage["stop_hz"])
            )
        grids_differ = any(
            first["calibration"][key] != second["calibration"][key]
            for key in ("start", "stop", "step")
        )
        return {
            "id": f"{first_id}__{second_id}",
            "source_cases_ok": first_result["trace_count_ok"]
            and second_result["trace_count_ok"],
            "source_grids_differ": grids_differ,
            "mappings_ok": mappings_ok,
            "coverage_status": coverage.get("status"),
            "uses_interpolation": bool(coverage.get("uses_interpolation")),
            "uses_fill": bool(coverage.get("uses_fill")),
            "generated_ok": bool(generated.get("ok")),
            "reread_ok": reread_ok,
            "points": generated.get("points"),
            "error": generated.get("error"),
        }


def _generate_dc_case(
    image_root: Path,
    manifest: dict[str, object],
) -> dict[str, object]:
    """Generate and reread the exact Samtec p9 workflow reported by the user."""

    case = _case_by_id(manifest, "samtec-cjt-c28s-p9")
    with tempfile.TemporaryDirectory() as output_dir, mock.patch(
        "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(output_dir)
    ):
        api = InsertionLossWebApi()
        api.set_network_ports(0, 2)
        case_result = _register_and_digitize(api, image_root, case)
        source = _first_source(api, 1)
        mappings_ok = all(
            api.set_mapping(0, parameter, choice)["ok"]
            for parameter, choice in (
                ("S11", "匹配 0"),
                ("S22", "匹配 0"),
                ("S21", source),
            )
        )
        generated = api.generate_datasheet_network(0)
        first_hz = last_hz = None
        reread_ok = False
        if generated.get("ok"):
            data = read_touchstone(generated["output"])
            first_hz = float(data.frequency_hz[0])
            last_hz = float(data.frequency_hz[-1])
            reread_ok = bool(
                data.n_ports == 2
                and data.frequency_hz.size == 51
                and first_hz == 0.0
                and last_hz == 5e9
                and np.all(np.diff(data.frequency_hz) > 0)
            )
        return {
            "id": case["id"],
            "source_case_ok": case_result["trace_count_ok"],
            "mappings_ok": mappings_ok,
            "generated_ok": bool(generated.get("ok")),
            "reread_ok": reread_ok,
            "points": generated.get("points"),
            "first_hz": first_hz,
            "last_hz": last_hz,
            "error": generated.get("error"),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exercise real vendor images through preview, mapping, generation, and reread."
    )
    parser.add_argument("images", type=Path, help="Directory containing hashed crops")
    args = parser.parse_args()
    manifest = json.loads(
        Path(__file__).with_name("cases.json").read_text(encoding="utf-8")
    )
    cases = [
        _register_and_digitize(InsertionLossWebApi(), args.images, case)
        for case in manifest["cases"]
    ]
    pairs = [
        _generate_pair(
            args.images,
            manifest,
            "samtec-cjt-c28s-p6",
            "jae-wp16rk-differential",
        ),
        _generate_pair(
            args.images,
            manifest,
            "jae-wp16rk-rf",
            "rosenberger-solderless-pcb-p2",
        ),
    ]
    dc_case = _generate_dc_case(args.images, manifest)
    cases_passed = all(
        all(
            outcome[key]
            for key in (
                "hash_ok",
                "size_ok",
                "analysis_ok",
                "preview_ok",
                "frequency_ok",
                "digitize_ok",
                "trace_count_ok",
                "full_span_ok",
            )
        )
        for outcome in cases
    )
    pairs_passed = all(
        outcome["source_cases_ok"]
        and outcome["source_grids_differ"]
        and outcome["mappings_ok"]
        and outcome["coverage_status"] == "ready"
        and outcome["uses_interpolation"]
        and not outcome["uses_fill"]
        and outcome["generated_ok"]
        and outcome["reread_ok"]
        for outcome in pairs
    )
    dc_passed = all(
        dc_case[key]
        for key in ("source_case_ok", "mappings_ok", "generated_ok", "reread_ok")
    )
    passed = cases_passed and pairs_passed and dc_passed
    print(
        json.dumps(
            {"passed": passed, "cases": cases, "pairs": pairs, "dc_case": dc_case},
            ensure_ascii=False,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
