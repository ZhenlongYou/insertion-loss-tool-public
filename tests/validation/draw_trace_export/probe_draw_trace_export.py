from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CASE_ROOT = Path(__file__).resolve().with_name("cases")
TEST_ID = "DRAW-TRACE-EXPORT-001"
FAILURE = "failure-signature draw-trace-export-contract-regression"


def fail(detail: str) -> int:
    print(f"{TEST_ID} {FAILURE}: {detail}")
    return 7


def main() -> int:
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(CASE_ROOT.glob("*.json"))
    }
    required = {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}
    if set(cases) != required:
        return fail("missing-input-partition")
    with tempfile.TemporaryDirectory(prefix="il-draw-trace-") as temp_dir:
        evidence = Path(temp_dir) / "renderer.json"
        env = dict(os.environ)
        env["INSERTION_LOSS_RENDERER_PROBE_PATH"] = str(evidence)
        completed = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "gui_main.py"), "--renderer-smoke-test"],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if completed.returncode != 0 or not evidence.exists():
            return fail("real-renderer-rejected-contract")
        probe = json.loads(evidence.read_text(encoding="utf-8"))
    expected_message = cases["known_failure"]["expected_message"]
    colors = list(probe.get("traceColors", []))
    checks = {
        "draw-complete": probe.get("drawGeneratedPlotVisible") is True
        and probe.get("drawGeneratedPlotCount") == cases["nominal"]["expected_plot_count"],
        "draw-editor-restores": probe.get("drawEditorRestored") is True,
        "trace-colors": len(colors) == 2 and len(set(colors)) == 2,
        "trace-swatches": probe.get("swatchColors") == colors,
        "trace-select": probe.get("traceHighlightSelected") is True,
        "unassigned-label": probe.get("unassignedOptionText") == "Unassigned",
        "unassigned-message": probe.get("unassignedPreflightText") == expected_message,
        "no-invalid-export": probe.get("unassignedPreflightBridgeCalls") == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return fail(",".join(failed))
    print(f"{TEST_ID} GREEN 4-plots 2-distinct-traces exact-unassigned-preflight no-bridge-call")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
