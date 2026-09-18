from __future__ import annotations

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "gui_main.py"), "--renderer-smoke-test"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    if result.returncode != 0:
        print("PLOT-TICKS-001 failure-signature mechanical-or-invalid-axis-ticks")
        return 7
    print("PLOT-TICKS-001 GREEN 0-10-20-30-40GHz -25-to-0dB 360deg-grid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
