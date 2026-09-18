from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = Path(__file__).with_name("cases")


def main() -> int:
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(CASE_DIR.glob("*.json"))
    }
    if set(cases) != {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}:
        return 2
    html = (PROJECT_ROOT / "src" / "insertion_loss_tool" / "webui" / "index.html").read_text(encoding="utf-8")
    required = (
        "function niceStep",
        "function engineeringPhaseStep",
        "function engineeringTicks",
        "function niceAxis",
        'data-x-tick',
    )
    if not all(token in html for token in required) or "function chartTicks" in html:
        return 4
    print("SUITE_OK six engineering-axis partitions and visible tick contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
