from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


TESTS = (
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_wilder_style_plot_recovers_all_four_visible_traces",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_adaptive_colour_clusters_do_not_claim_the_same_antialias_pixel",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_unlabelled_gray_trace_is_recovered_without_treating_grid_as_data",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_unlabelled_dashed_gray_trace_remains_one_visible_curve",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_workspace_exposes_unlabelled_gray_trace_for_manual_mapping",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_unlabelled_repeated_overlap_uses_two_sided_visual_evidence",
    "tests.test_datasheet_digitizer."
    "DatasheetDigitizerTests."
    "test_more_than_eight_candidate_traces_fail_closed",
    "tests.test_webview_gui."
    "WebviewGuiTests."
    "test_unequal_source_traces_report_one_common_frequency_grid",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _read_partitions() -> int:
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    required = {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}
    actual = set(cases["partitions"])
    if actual != required:
        raise RuntimeError(f"partition mismatch: {sorted(actual)}")
    return len(actual)


def _archived_source(repo: Path, revision: str, destination: Path) -> Path:
    archive = destination / "source.tar"
    with archive.open("wb") as stream:
        completed = subprocess.run(
            [
                "git",
                "archive",
                revision,
                "src",
            ],
            cwd=repo,
            stdout=stream,
            stderr=subprocess.PIPE,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    with tarfile.open(archive) as bundle:
        bundle.extractall(destination, filter="data")
    return destination / "src"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-revision")
    arguments = parser.parse_args()
    repo = _repo_root()
    partition_count = _read_partitions()
    with tempfile.TemporaryDirectory(prefix="wilder-recovery-") as directory:
        if arguments.source_revision:
            source = _archived_source(repo, arguments.source_revision, Path(directory))
        else:
            source = repo / "src"
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(source)
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", *TESTS, "-v"],
            cwd=repo,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    if completed.returncode:
        print("WILDER-RECOVERY failure-signature")
        failed_cases = [
            line.strip()
            for line in completed.stderr.splitlines()
            if line.startswith(("FAIL: ", "ERROR: "))
        ]
        print(f"behavioural_failures={len(failed_cases)}")
        for failed_case in failed_cases:
            print(failed_case)
        return 7
    print(f"WILDER-RECOVERY GREEN · {partition_count} partitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
