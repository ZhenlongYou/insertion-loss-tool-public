#!/usr/bin/env python3
"""Deterministic stress tests for the insertion-loss tool.

The normal unit tests cover fixed examples. This script pushes more parameter
combinations through the public model and Touchstone I/O paths: S2P/S4P,
linear/log sweeps, all writer formats, draw smoothing with negative dB control
points, and phase-preserving imported-file modification. It is intentionally
standalone so it can be run from source or from CI-style shell scripts without
pytest.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import tempfile
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from insertion_loss_tool.models import (
    TargetPoint,
    build_network,
    generate_frequency_axis,
    insert_draw_control_frequencies,
    interpolate_drawn_loss,
    linear_loss,
    modify_insertion_loss,
    parse_draw_points,
    parse_pairs,
    protocol_loss,
)
from insertion_loss_tool.touchstone import read_touchstone, to_magnitude_db, write_touchstone
from insertion_loss_tool.gui import run_self_test
from insertion_loss_tool.validation import minimum_s2p_insertion_loss_db


def run_stress(iterations: int, seed: int, output_dir: Path) -> int:
    """Run randomized but reproducible end-to-end checks.

    Returns the number of checked cases. Any failed invariant raises an
    AssertionError or ValueError and stops the script with a non-zero exit code.
    """

    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = 0
    safe_loss_floor = minimum_s2p_insertion_loss_db(20.0) + 0.15

    for index in range(iterations):
        ports = 2 if index % 2 == 0 else 4
        spacing = "log" if index % 3 == 0 else "linear"
        data_format = ["ri", "ma", "db"][index % 3]
        unit = ["hz", "mhz", "ghz"][index % 3]
        start_hz = float(10 ** rng.uniform(6.0, 9.3))
        stop_hz = float(start_hz * 10 ** rng.uniform(0.7, 2.1))
        points = int(rng.integers(5, 180))
        f = generate_frequency_axis(start_hz, stop_hz, points, spacing=spacing)

        start_loss = float(rng.uniform(safe_loss_floor, 3.0))
        stop_loss = float(rng.uniform(start_loss + 0.2, 35.0))
        loss = linear_loss(f, start_loss, stop_loss)
        data = build_network(
            f,
            ports,
            loss,
            delay_ps=float(rng.uniform(0.0, 180.0)),
            phase_offset_deg=float(rng.uniform(-30.0, 30.0)),
        )
        path = output_dir / f"linear_{index:04d}.s{ports}p"
        write_touchstone(data, path, frequency_unit=unit, data_format=data_format)
        loaded = read_touchstone(path)
        _assert_basic_network(loaded, ports)
        if ports == 2:
            np.testing.assert_allclose(loaded.s[:, 1, 0], loaded.s[:, 0, 1], rtol=1e-9, atol=1e-12)
        loaded_loss = -to_magnitude_db(loaded.s[:, 1, 0])
        _assert_close(float(loaded_loss[0]), start_loss, 2e-6, "linear start loss")
        _assert_close(float(loaded_loss[-1]), stop_loss, 2e-6, "linear stop loss")
        cases += 1

        formula_loss = protocol_loss(
            f,
            a=float(rng.uniform(0.0, 0.2)),
            b=float(rng.uniform(0.05, 1.4)),
            c=float(rng.uniform(0.0, 0.8)),
            model_frequency_unit="ghz",
        )
        formula_loss = np.maximum(formula_loss, safe_loss_floor)
        formula_data = build_network(f, ports, formula_loss, delay_ps=float(rng.uniform(0.0, 100.0)))
        formula_path = output_dir / f"formula_{index:04d}.s{ports}p"
        write_touchstone(formula_data, formula_path, frequency_unit=unit, data_format=data_format)
        _assert_basic_network(read_touchstone(formula_path), ports)
        cases += 1

        draw_controls = _draw_controls(start_hz, stop_hz, rng)
        draw_axis = insert_draw_control_frequencies(f, draw_controls)
        draw_loss = interpolate_drawn_loss(draw_axis, draw_controls, method="smooth")
        draw_data = build_network(draw_axis, 2, draw_loss)
        draw_path = output_dir / f"draw_{index:04d}.s2p"
        # Draw mode inserts the user's exact control frequencies into the
        # output grid. Some randomized sweeps place those inserted points too
        # close together to serialize distinctly in coarse units such as GHz,
        # so this stress path writes in Hz while linear/formula cases continue
        # to cover the randomized output-unit matrix.
        write_touchstone(draw_data, draw_path, frequency_unit="hz", data_format=data_format)
        draw_loaded = read_touchstone(draw_path)
        for point in draw_controls:
            idx = int(np.where(np.isclose(draw_loaded.frequency_hz, point.frequency_hz))[0][0])
            actual_mag = float(to_magnitude_db(draw_loaded.s[idx, 1, 0]))
            _assert_close(actual_mag, -point.loss_db, 3e-6, "draw control magnitude")
        cases += 1

        modify_source = build_network(f, 2, loss, delay_ps=float(rng.uniform(10.0, 120.0)))
        target_freqs = np.quantile(f, [0.3, 0.68])
        source_target_losses = np.interp(target_freqs, f, loss)
        targets = [
            TargetPoint(
                float(target_freqs[0]),
                float(source_target_losses[0] + rng.uniform(0.1, 0.8)),
            ),
            TargetPoint(
                float(target_freqs[1]),
                float(source_target_losses[1] + rng.uniform(0.1, 0.8)),
            ),
        ]
        phase_before = {
            (1, 0): np.unwrap(np.angle(modify_source.s[:, 1, 0])),
            (0, 1): np.unwrap(np.angle(modify_source.s[:, 0, 1])),
        }
        modified = modify_insertion_loss(
            modify_source,
            targets,
            parse_pairs(["S21", "S12"], 2),
            smoothness=0.16,
            smooth_domain="linear",
            insert_targets=True,
        )
        for target in targets:
            idx = int(np.where(np.isclose(modified.data.frequency_hz, target.frequency_hz))[0][0])
            for pair in ((1, 0), (0, 1)):
                achieved = float(-to_magnitude_db(modified.data.s[idx, pair[0], pair[1]]))
                _assert_close(achieved, target.loss_db, 2e-5, "modify target loss")
                expected_phase = float(np.interp(target.frequency_hz, f, phase_before[pair]))
                actual_phase = float(np.unwrap(np.angle(modified.data.s[:, pair[0], pair[1]]))[idx])
                _assert_close(actual_phase, expected_phase, 2e-10, "modify phase preservation")
        cases += 1

    _assert_invalid_cases()
    cases += 4

    self_test_paths = run_self_test(output_dir / "gui_self_test")
    if len(self_test_paths) < 5:
        raise AssertionError("GUI self-test did not write all expected files")
    cases += 1
    return cases


def _draw_controls(start_hz: float, stop_hz: float, rng: np.random.Generator) -> list[TargetPoint]:
    """Create smooth-enough negative-dB draw controls inside the sweep."""

    xs = np.linspace(start_hz, stop_hz, 4)
    middle_loss = float(rng.uniform(3.0, 16.0))
    safe_loss_floor = minimum_s2p_insertion_loss_db(20.0) + 0.15
    values = [
        f"{xs[0]:.17g}Hz:{-float(rng.uniform(safe_loss_floor, 2.0)):.6g}",
        f"{xs[1]:.17g}Hz:{-middle_loss:.6g}",
        f"{xs[2]:.17g}Hz:{-float(rng.uniform(2.0, 18.0)):.6g}",
        f"{xs[3]:.17g}Hz:{-float(rng.uniform(1.0, 24.0)):.6g}",
    ]
    return parse_draw_points(values)


def _assert_basic_network(data, ports: int) -> None:
    if data.n_ports != ports:
        raise AssertionError(f"expected {ports} ports, got {data.n_ports}")
    if data.s.shape != (data.frequency_hz.size, ports, ports):
        raise AssertionError(f"bad S matrix shape: {data.s.shape}")
    if not np.all(np.diff(data.frequency_hz) > 0):
        raise AssertionError("frequency axis is not strictly increasing")
    if np.any(~np.isfinite(data.s.real)) or np.any(~np.isfinite(data.s.imag)):
        raise AssertionError("network contains non-finite S-parameters")


def _assert_invalid_cases() -> None:
    frequency = np.array([1e9, 2e9, 3e9])
    loss = np.array([1.0, 2.0, 3.0])
    _expect_failure(lambda: generate_frequency_axis(3e9, 1e9, 3), "frequency order")
    _expect_failure(lambda: build_network(frequency, 2, loss, through_pairs=[(0, 0)]), "diagonal pair")
    _expect_failure(
        lambda: interpolate_drawn_loss(
            frequency,
            parse_draw_points(["1GHz:-1.0", "1.00001GHz:-9.0", "3GHz:-2.0"]),
        ),
        "near vertical draw",
    )
    _expect_failure(
        lambda: build_network(frequency, 2, np.zeros_like(frequency), return_loss_db=20.0),
        "nonpassive zero-loss network",
    )


def _expect_failure(func, label: str) -> None:
    try:
        func()
    except Exception:
        return
    raise AssertionError(f"expected failure did not occur: {label}")


def _assert_close(actual: float, expected: float, tolerance: float, label: str) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{label}: expected {expected}, got {actual}, tol {tolerance}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic insertion-loss stress tests.")
    parser.add_argument("--iterations", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260704)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()
    if args.iterations <= 0:
        raise SystemExit("--iterations must be positive")

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            # Keep a temporary scratch parent for any libraries that need it,
            # while durable stress artifacts go to the requested output dir.
            _ = tmp
            cases = run_stress(args.iterations, args.seed, output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="iltool-stress-") as tmp:
            output_dir = Path(tmp)
            cases = run_stress(args.iterations, args.seed, output_dir)

    print(f"STRESS TEST PASSED: cases={cases}, iterations={args.iterations}, seed={args.seed}")
    print(f"stress output: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
