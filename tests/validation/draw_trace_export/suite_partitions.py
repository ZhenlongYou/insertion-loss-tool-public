from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from insertion_loss_tool.datasheet_workspace import DatasheetWorkspace  # noqa: E402
from insertion_loss_tool.webview_gui import load_web_ui  # noqa: E402


def main() -> int:
    case_dir = Path(__file__).with_name("cases")
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(case_dir.glob("*.json"))
    }
    if set(cases) != {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}:
        return 2
    html = load_web_ui()
    workspace = DatasheetWorkspace()
    workspace.set_network_ports(0, 2)
    workspace.set_network_parameter_family(0, "single-ended")
    workspace.set_network_reciprocal(0, False)
    workspace.set_mapping(0, "S11", "反射 -20 dB")
    for parameter in ("S12", "S21", "S22"):
        workspace.set_mapping(0, parameter, "自动")
    try:
        workspace.compose_network_magnitudes(0)
    except ValueError as exc:
        backend_error = str(exc)
    else:
        backend_error = ""
    checks = {
        "draw-plots": 'function showGeneratedPlots()' in html,
        "draw-success": 'if(payload.mode==="draw")showGeneratedPlots()' in html,
        "trace-palette": 'function traceDisplayRgb(curve,index=0)' in html,
        "unassigned-label": '"自动":"Unassigned"' in html,
        "unassigned-preflight": 'function unassignedNetworkMessage(network)' in html,
        "backend-detail": backend_error
        == "未分配通道：S12, S21, S22。请选择识别曲线或默认曲线。",
        "flexible-mapping": cases["realistic"]["allow_cross_parameter_mapping"] is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        print(f"SUITE_FAILURE {','.join(failed)} backend={backend_error}")
        return 4
    print("SUITE_OK six draw-trace-export partitions and backend/UI contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
