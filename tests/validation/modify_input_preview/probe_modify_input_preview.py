from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from insertion_loss_tool.webview_gui import InsertionLossWebApi  # noqa: E402


def main() -> int:
    result = InsertionLossWebApi().inspect_input(
        PROJECT_ROOT / "examples" / "formula_demo.s4p", "ghz"
    )
    checks = (
        result.get("ok") is True,
        result.get("name") == "formula_demo.s4p",
        result.get("ports") == 4,
        result.get("points") == 201,
        result.get("start_hz") == 10e6,
        result.get("stop_hz") == 40e9,
        len(result.get("plot", {}).get("series", [])) == 16,
        result.get("plot", {}).get("series", [])[-1].get("name") == "S44",
    )
    if not all(checks):
        print("MODIFY-INPUT-001 failure-signature stale-or-missing-source-preview")
        return 7
    print("MODIFY-INPUT-001 GREEN 4-ports 201-points 16-series S44")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
