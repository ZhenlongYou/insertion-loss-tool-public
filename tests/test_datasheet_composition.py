from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from insertion_loss_tool.datasheet import (
    CurveResource,
    assess_mixed_mode_conversion,
    compose_frequency_grid,
    mixed_mode_parameter_names,
    mixed_mode_to_single_ended,
    resample_curve,
    single_ended_to_mixed_mode,
    transpose_parameter,
)


class DatasheetCompositionTests(unittest.TestCase):
    def test_manual_grid_keeps_dc_and_rejects_negative_frequency(self) -> None:
        """细步进建议可保留真实 DC，不能借此允许负频率。"""
        result = compose_frequency_grid(
            [], policy="manual", manual_start_hz=0,
            manual_stop_hz=1e9, manual_step_hz=0.25e9,
        )
        np.testing.assert_array_equal(result.frequency_hz, [0, 0.25e9, 0.5e9, 0.75e9, 1e9])
        with self.assertRaisesRegex(ValueError, "手动频率范围无效"):
            compose_frequency_grid(
                [], policy="manual", manual_start_hz=-1,
                manual_stop_hz=1e9, manual_step_hz=1e8,
            )

    def test_intersection_builds_one_uniform_master_grid(self) -> None:
        first = CurveResource(
            curve_id="image-1:A",
            parameter="S11",
            frequency_hz=np.array([1.0, 2.0, 3.0, 4.0, 5.0]) * 1e9,
            magnitude_db=np.array([-1.0, -2.0, -3.0, -4.0, -5.0]),
        )
        second = CurveResource(
            curve_id="image-2:A",
            parameter="S21",
            frequency_hz=np.array([2.0, 2.7, 3.4, 4.1]) * 1e9,
            magnitude_db=np.array([-2.0, -2.7, -3.4, -4.1]),
        )

        result = compose_frequency_grid(
            [first, second], policy="intersection_native"
        )

        np.testing.assert_allclose(result.frequency_hz, [2e9, 3.05e9, 4.1e9])
        np.testing.assert_allclose(np.diff(result.frequency_hz), result.step_hz)
        self.assertEqual(result.points, 3)
        self.assertEqual(result.start_hz, 2e9)
        self.assertAlmostEqual(result.stop_hz, 4.1e9, delta=1.0)

    def test_reusable_validation_manifest_matches_public_algorithms(self) -> None:
        manifest_path = Path(__file__).parent / "validation" / "datasheet_composition_cases.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in manifest["cases"]}

        for case_id in (
            "intersection-different-resolution",
            "rounding-noise-deduplication",
            "disjoint-coverage",
        ):
            case = cases[case_id]
            curves = [
                CurveResource(
                    curve_id=f"{case_id}:{index}",
                    parameter=curve["parameter"],
                    frequency_hz=np.asarray(curve["frequency_hz"], dtype=np.float64),
                    magnitude_db=np.asarray(curve["magnitude_db"], dtype=np.float64),
                )
                for index, curve in enumerate(case["curves"])
            ]
            if "expected_error" in case:
                with self.assertRaisesRegex(ValueError, case["expected_error"]):
                    compose_frequency_grid(curves, policy=case["policy"])
                continue
            result = compose_frequency_grid(curves, policy=case["policy"])
            if "expected_frequency_hz" in case:
                np.testing.assert_array_equal(result.frequency_hz, case["expected_frequency_hz"])
            if "expected_point_count" in case:
                self.assertEqual(result.frequency_hz.size, case["expected_point_count"])

        resampling = cases["linear-db-resampling"]
        source = resampling["source"]
        curve = CurveResource(
            curve_id="manifest-resampling",
            parameter=source["parameter"],
            frequency_hz=np.asarray(source["frequency_hz"], dtype=np.float64),
            magnitude_db=np.asarray(source["magnitude_db"], dtype=np.float64),
        )
        result = resample_curve(
            curve, np.asarray(resampling["target_frequency_hz"], dtype=np.float64)
        )
        np.testing.assert_allclose(
            result.magnitude_db, resampling["expected_magnitude_db"], atol=1e-12
        )

    def test_intersection_grid_uses_coarsest_safe_uniform_resolution(self) -> None:
        fine = CurveResource(
            curve_id="image-1:A",
            parameter="SDD21",
            frequency_hz=np.array([10e6, 20e6, 30e6, 40e6, 50e6]),
            magnitude_db=np.array([-1.0, -1.1, -1.2, -1.3, -1.4]),
        )
        coarse = CurveResource(
            curve_id="image-2:A",
            parameter="SCD21",
            frequency_hz=np.array([20e6, 40e6, 60e6]),
            magnitude_db=np.array([-40.0, -35.0, -30.0]),
        )

        result = compose_frequency_grid([fine, coarse], policy="intersection_native")

        np.testing.assert_array_equal(result.frequency_hz, [20e6, 50e6])
        self.assertEqual(result.start_hz, 20e6)
        self.assertEqual(result.stop_hz, 50e6)
        self.assertEqual(result.step_hz, 30e6)
        self.assertEqual(result.points, 2)
        self.assertFalse(result.uses_extrapolation)

    def test_manual_grid_rejects_a_step_that_does_not_divide_the_span(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能整除"):
            compose_frequency_grid(
                [],
                policy="manual",
                manual_start_hz=1e9,
                manual_stop_hz=2e9,
                manual_step_hz=0.3e9,
            )

    def test_default_only_network_can_use_an_explicit_uniform_manual_grid(self) -> None:
        result = compose_frequency_grid(
            [],
            policy="manual",
            manual_start_hz=10e6,
            manual_stop_hz=18e9,
            manual_step_hz=10e6,
        )

        self.assertEqual(result.points, 1800)
        self.assertEqual(result.step_hz, 10e6)
        np.testing.assert_allclose(np.diff(result.frequency_hz), 10e6)

    def test_frequency_knots_with_rounding_noise_are_merged(self) -> None:
        first = CurveResource(
            curve_id="first",
            parameter="S11",
            frequency_hz=np.array([1e9, 2e9, 3e9]),
            magnitude_db=np.array([-1.0, -2.0, -3.0]),
        )
        second = CurveResource(
            curve_id="second",
            parameter="S21",
            frequency_hz=np.array([1e9, 2e9 + 1e-4, 3e9]),
            magnitude_db=np.array([-1.0, -2.0, -3.0]),
        )

        result = compose_frequency_grid([first, second])

        self.assertEqual(result.frequency_hz.size, 3)

    def test_disjoint_curves_are_rejected_instead_of_extrapolated(self) -> None:
        left = CurveResource(
            curve_id="left",
            parameter="SDD11",
            frequency_hz=np.array([10e6, 20e6]),
            magnitude_db=np.array([-10.0, -11.0]),
        )
        right = CurveResource(
            curve_id="right",
            parameter="SCC11",
            frequency_hz=np.array([30e6, 40e6]),
            magnitude_db=np.array([-20.0, -21.0]),
        )

        with self.assertRaisesRegex(ValueError, "没有共同频率范围"):
            compose_frequency_grid([left, right], policy="intersection_native")

    def test_magnitude_only_curve_interpolates_in_db_without_extrapolation(self) -> None:
        curve = CurveResource(
            curve_id="conversion",
            parameter="SCD21",
            frequency_hz=np.array([1e9, 2e9, 3e9]),
            magnitude_db=np.array([-40.0, -30.0, -20.0]),
        )

        result = resample_curve(curve, np.array([1e9, 1.5e9, 2.5e9, 3e9]))

        np.testing.assert_allclose(result.magnitude_db, [-40.0, -35.0, -25.0, -20.0])
        self.assertIsNone(result.phase_deg)
        with self.assertRaisesRegex(ValueError, "超出"):
            resample_curve(curve, np.array([0.5e9, 1e9]))

    def test_manual_and_union_ranges_require_explicit_coverage(self) -> None:
        first = CurveResource(
            curve_id="first",
            parameter="SDD21",
            frequency_hz=np.array([1e9, 2e9, 3e9]),
            magnitude_db=np.array([-1.0, -2.0, -3.0]),
        )
        second = CurveResource(
            curve_id="second",
            parameter="SCD21",
            frequency_hz=np.array([2e9, 3e9, 4e9]),
            magnitude_db=np.array([-30.0, -25.0, -20.0]),
        )

        manual = compose_frequency_grid(
            [first, second],
            policy="manual",
            manual_start_hz=2e9,
            manual_stop_hz=3e9,
            manual_step_hz=0.5e9,
        )
        np.testing.assert_array_equal(manual.frequency_hz, [2e9, 2.5e9, 3e9])
        with self.assertRaisesRegex(ValueError, "超出"):
            compose_frequency_grid(
                [first, second],
                policy="manual",
                manual_start_hz=1e9,
                manual_stop_hz=4e9,
                manual_step_hz=1e9,
            )
        with self.assertRaisesRegex(ValueError, "显式允许"):
            compose_frequency_grid([first, second], policy="union")
        union = compose_frequency_grid(
            [first, second], policy="union", allow_extrapolation=True
        )
        np.testing.assert_array_equal(union.frequency_hz, [1e9, 2e9, 3e9, 4e9])
        self.assertTrue(union.uses_extrapolation)

    def test_common_grid_point_cap_rejects_oversized_output(self) -> None:
        frequency = np.arange(1.0, 100_002.0)
        curve = CurveResource(
            curve_id="large",
            parameter="S21",
            frequency_hz=frequency,
            magnitude_db=np.zeros_like(frequency),
        )

        with self.assertRaisesRegex(ValueError, "超过上限 100000"):
            compose_frequency_grid([curve], max_points=100_000)

    def test_mixed_mode_names_cover_all_blocks_and_transpose_cross_mode(self) -> None:
        names = mixed_mode_parameter_names(4)

        self.assertEqual(len(names), 16)
        for parameter in ("SDD11", "SDC21", "SCD12", "SCC22"):
            self.assertIn(parameter, names)
        self.assertEqual(transpose_parameter("SDD21"), "SDD12")
        self.assertEqual(transpose_parameter("SCC21"), "SCC12")
        self.assertEqual(transpose_parameter("SCD21"), "SDC12")
        self.assertEqual(transpose_parameter("SDC21"), "SCD12")

    def test_complete_complex_mixed_mode_matrix_converts_back_losslessly(self) -> None:
        single_ended = np.array(
            [
                [0.10 + 0.01j, 0.02 - 0.01j, 0.70 - 0.20j, 0.03 + 0.01j],
                [0.01 + 0.02j, 0.11 - 0.02j, 0.04 + 0.01j, 0.68 - 0.18j],
                [0.69 - 0.19j, 0.03, 0.12 + 0.01j, 0.02 - 0.01j],
                [0.02, 0.67 - 0.17j, 0.01 + 0.01j, 0.10 - 0.01j],
            ],
            dtype=np.complex128,
        )

        mixed_mode = single_ended_to_mixed_mode(single_ended)
        restored = mixed_mode_to_single_ended(mixed_mode)

        np.testing.assert_allclose(restored, single_ended, atol=1e-14)

        try:
            import skrf
        except ImportError:  # pragma: no cover - optional independent oracle
            return
        oracle = skrf.Network(f=[1e9], s=single_ended[np.newaxis, :, :], z0=50.0)
        oracle.se2gmm(p=2)
        np.testing.assert_allclose(mixed_mode, oracle.s[0], atol=1e-14)

    def test_non_adjacent_port_pairs_use_the_same_transform_as_readiness(self) -> None:
        rng = np.random.default_rng(20260830)
        single_ended = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
        port_pairs = ((1, 3), (2, 4))

        mixed_mode = single_ended_to_mixed_mode(
            single_ended, port_pairs=port_pairs
        )
        restored = mixed_mode_to_single_ended(
            mixed_mode, port_pairs=port_pairs
        )

        np.testing.assert_allclose(restored, single_ended, atol=1e-14)
        adjacent = single_ended_to_mixed_mode(single_ended)
        self.assertGreater(float(np.max(np.abs(mixed_mode - adjacent))), 1.0)

    def test_malformed_port_pairs_are_not_conversion_ready(self) -> None:
        frequency = np.array([1e9, 2e9])
        curves = [
            CurveResource(
                curve_id=parameter,
                parameter=parameter,
                frequency_hz=frequency,
                magnitude_db=np.array([-20.0, -19.0]),
                phase_deg=np.array([0.0, -10.0]),
                reference_impedance_ohm=50.0,
            )
            for parameter in mixed_mode_parameter_names(4)
        ]

        malformed = assess_mixed_mode_conversion(
            curves,
            physical_port_count=4,
            port_pairs=((1, 2, 3, 4), ()),
        )

        self.assertFalse(malformed.ready)
        self.assertTrue(malformed.port_pairs_invalid)
        for invalid_pairs in (((1.0, 3.0), (2.0, 4.0)), ((True, 3), (2, 4))):
            readiness = assess_mixed_mode_conversion(
                curves,
                physical_port_count=4,
                port_pairs=invalid_pairs,
            )
            self.assertFalse(readiness.ready)
            self.assertTrue(readiness.port_pairs_invalid)
            with self.assertRaisesRegex(ValueError, "非布尔整数"):
                single_ended_to_mixed_mode(
                    np.eye(4, dtype=np.complex128),
                    port_pairs=invalid_pairs,
                )

    def test_magnitude_only_or_incomplete_mixed_mode_data_cannot_claim_conversion(self) -> None:
        frequency = np.array([1e9, 2e9])
        partial = [
            CurveResource(
                curve_id="sdd11",
                parameter="SDD11",
                frequency_hz=frequency,
                magnitude_db=np.array([-20.0, -18.0]),
            ),
            CurveResource(
                curve_id="sdc11",
                parameter="SDC11",
                frequency_hz=frequency,
                magnitude_db=np.array([-40.0, -35.0]),
            ),
        ]

        readiness = assess_mixed_mode_conversion(
            partial, physical_port_count=4, port_pairs=((1, 2), (3, 4))
        )

        self.assertFalse(readiness.ready)
        self.assertIn("SCC22", readiness.missing_parameters)
        self.assertEqual(set(readiness.missing_phase), {"SDD11", "SDC11"})
        self.assertTrue(readiness.reference_impedance_missing)

    def test_complete_complex_blocks_are_conversion_ready(self) -> None:
        frequency = np.array([1e9, 2e9])
        curves = [
            CurveResource(
                curve_id=parameter,
                parameter=parameter,
                frequency_hz=frequency,
                magnitude_db=np.array([-20.0, -19.0]),
                phase_deg=np.array([0.0, -10.0]),
                reference_impedance_ohm=50.0,
            )
            for parameter in mixed_mode_parameter_names(4)
        ]

        readiness = assess_mixed_mode_conversion(
            curves, physical_port_count=4, port_pairs=((1, 2), (3, 4))
        )

        self.assertTrue(readiness.ready, readiness)


if __name__ == "__main__":
    unittest.main()
