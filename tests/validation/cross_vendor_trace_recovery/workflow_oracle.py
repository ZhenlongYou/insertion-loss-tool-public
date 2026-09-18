from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    manifest = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    expected = {
        "samtec-cjt-c28s-p6": ("10MHz", "5GHz", "10MHz", "magnitude", 2),
        "jae-wp16rk-differential": ("100MHz", "10GHz", "20MHz", "magnitude", 1),
        "jae-wp16rk-rf": ("100MHz", "10GHz", "20MHz", "magnitude", 1),
        "rosenberger-solderless-pcb-p2": ("100MHz", "110GHz", "100MHz", "positive-loss", 3),
    }
    observed = {}
    for case in manifest["cases"]:
        if case["id"] not in expected:
            continue
        calibration = case["calibration"]
        observed[case["id"]] = (
            calibration["start"],
            calibration["stop"],
            calibration["step"],
            calibration["y_convention"],
            case["expected_trace_count"],
        )
        if calibration["y_convention"] == "positive-loss" and not (
            calibration["y_bottom_db"] > calibration["y_top_db"]
        ):
            raise SystemExit("positive-loss orientation is not downward")
        if calibration["y_convention"] == "magnitude" and not (
            calibration["y_top_db"] > calibration["y_bottom_db"]
        ):
            raise SystemExit("magnitude orientation is not negative downward")
    if observed != expected:
        raise SystemExit(f"frozen workflow contract mismatch: {observed}")
    print("WORKFLOW_ORACLE_OK · 4 frozen calibrations · 2 axis conventions · 2 differing-grid pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
