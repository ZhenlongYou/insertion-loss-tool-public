from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from insertion_loss_tool.webview_gui import InsertionLossWebApi, load_web_ui  # noqa: E402


def main() -> int:
    case_dir = Path(__file__).with_name("cases")
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(case_dir.glob("*.json"))
    }
    if set(cases) != {
        "nominal",
        "boundary",
        "invalid",
        "adversarial",
        "realistic",
        "known_failure",
    }:
        return 2
    api = InsertionLossWebApi()
    nominal = api.inspect_input(PROJECT_ROOT / cases["nominal"]["source"], "ghz")
    boundary = api.inspect_input(PROJECT_ROOT / cases["boundary"]["source"], "ghz")
    invalid = api.inspect_input(PROJECT_ROOT / cases["invalid"]["source"], "ghz")
    adversarial = api.inspect_input(cases["adversarial"]["source"], "ghz")
    html = load_web_ui()
    checks = (
        nominal.get("ok") is True,
        nominal.get("ports") == cases["nominal"]["expected_ports"],
        boundary.get("ok") is True,
        boundary.get("ports") == cases["boundary"]["expected_ports"],
        boundary.get("points") == cases["boundary"]["expected_points"],
        len(boundary.get("plot", {}).get("series", [])) == 16,
        invalid.get("ok") is False,
        adversarial.get("ok") is False,
        'id="modify-input-status"' in html,
        'callApi("inspect_input"' in html,
        '$("#modify-input").addEventListener("change"' in html,
    )
    if not all(checks):
        return 4
    print("SUITE_OK six Modify input partitions and visible event contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
