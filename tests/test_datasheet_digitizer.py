from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image, ImageDraw

import insertion_loss_tool.datasheet_digitizer as digitizer_module
from insertion_loss_tool.datasheet_digitizer import (
    AxisCalibration,
    ImageAnalysis,
    OcrLine,
    detect_axis_calibration,
    detect_parameter_text,
    digitize_plot_image,
)
from insertion_loss_tool.webview_gui import InsertionLossWebApi


def _write_known_plot(path: Path) -> dict[str, object]:
    manifest = json.loads(
        Path(__file__)
        .with_name("validation")
        .joinpath("datasheet_digitization_cases.json")
        .read_text(encoding="utf-8")
    )
    case = manifest["cases"][0]
    image_spec = case["image"]
    left, top, right, bottom = image_spec["plot_box"]
    image = Image.new("RGB", (image_spec["width"], image_spec["height"]), "white")
    draw = ImageDraw.Draw(image)
    for index in range(image_spec["grid_divisions"] + 1):
        x = round(left + (right - left) * index / image_spec["grid_divisions"])
        y = round(top + (bottom - top) * index / image_spec["grid_divisions"])
        draw.line((x, top, x, bottom), fill=(190, 190, 190), width=1)
        draw.line((left, y, right, y), fill=(190, 190, 190), width=1)
    x_pixels = np.arange(left, right + 1, dtype=np.float64)
    x_normalized = (x_pixels - left) / (right - left)
    formulas = {
        "Dark blue": -2.0 - 8.0 * x_normalized,
        "Red": -5.0 - 20.0 * x_normalized,
    }
    for curve in case["curves"]:
        magnitude_db = formulas[curve["color"]]
        y_pixels = top + (case["axis"]["y_max_db"] - magnitude_db) * (
            bottom - top
        ) / (case["axis"]["y_max_db"] - case["axis"]["y_min_db"])
        draw.line(
            list(zip(x_pixels.astype(int), np.rint(y_pixels).astype(int))),
            fill=tuple(curve["rgb"]),
            width=3,
        )
    image.save(path)
    return case


class DatasheetDigitizerTests(unittest.TestCase):
    def test_colour_identity_gate_keeps_antialias_shade_but_rejects_hue_swap(
        self,
    ) -> None:
        self.assertTrue(
            digitizer_module._colour_identity_is_compatible(
                (218, 150, 159), (210, 142, 146)
            )
        )
        self.assertFalse(
            digitizer_module._colour_identity_is_compatible(
                (218, 150, 159), (143, 139, 206)
            )
        )

    def test_more_than_eight_candidate_traces_fail_closed(self) -> None:
        curve = digitizer_module.DigitizedCurve(
            color="Red",
            rgb=(220, 40, 40),
            frequency_hz=np.asarray([1e9]),
            magnitude_db=np.asarray([-3.0]),
            pixel_points=np.asarray([[10.0, 20.0]]),
            confidence=0.8,
            observed_samples=1,
            sample_provenance=("observed",),
        )

        with self.assertRaisesRegex(ValueError, "Dense overlapping traces"):
            digitizer_module._ensure_supported_trace_density([curve] * 9)

    def test_regular_grid_does_not_extend_to_unrelated_outer_frame_lines(self) -> None:
        centres = np.asarray(
            [26.5, 31, 70.5, 161.5, 183, 216.5, 229, 271, 325.5,
             380, 434.5, 488.5, 543.5, 598, 653, 732.5, 811, 813]
        )

        self.assertEqual(digitizer_module._regular_grid_extent(centres), (162, 653))

    def test_plot_box_ignores_a_full_height_outer_frame_line(self) -> None:
        image = Image.new("RGB", (640, 480), "white")
        draw = ImageDraw.Draw(image)
        draw.line((32, 50, 32, 410), fill=(100, 100, 100))
        for index in range(11):
            x = 80 + 48 * index
            y = 50 + 36 * index
            draw.line((x, 50, x, 410), fill=(190, 190, 190))
            draw.line((80, y, 560, y), fill=(190, 190, 190))

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (80, 50, 560, 410),
        )

    def test_plot_box_keeps_full_grid_when_traces_interrupt_horizontal_lines(self) -> None:
        image = Image.new("RGB", (760, 540), "white")
        draw = ImageDraw.Draw(image)
        for index in range(11):
            x = 100 + 56 * index
            y = 70 + 40 * index
            draw.line((x, 70, x, 470), fill=(190, 190, 190))
            draw.line((100, y, 660, y), fill=(190, 190, 190))
        # Real Wilder plots have dense coloured return-loss traces that cover
        # sizeable portions of several horizontal grid lines.  The grid is
        # still complete; support must not be based on an arbitrary 75% vote.
        for index in range(4):
            y = 70 + 40 * (index + 2)
            draw.line((101, y, 350, y), fill="white", width=5)
            draw.line((101, y, 350, y + 1), fill=(216, 54, 64), width=1)

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (100, 70, 660, 470),
        )

    def test_plot_box_uses_visible_border_when_dense_traces_hide_internal_rows(self) -> None:
        image = Image.new("RGB", (760, 540), "white")
        draw = ImageDraw.Draw(image)
        for index in range(11):
            x = 100 + 56 * index
            y = 70 + 40 * index
            draw.line((x, 70, x, 470), fill=(190, 190, 190))
            draw.line((100, y, 660, y), fill=(190, 190, 190))
        # Conversion-loss plots can cover two lower grid rows almost entirely,
        # while their lower border and vertical grid still remain visible.
        for y in (390, 430):
            draw.line((101, y, 659, y), fill="white", width=5)
            draw.line((101, y, 659, y + 1), fill=(130, 150, 205), width=2)

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (100, 70, 660, 470),
        )

    def test_plot_box_accepts_product_graph_with_only_four_horizontal_grid_lines(
        self,
    ) -> None:
        """A short 0 to -3 dB product plot still has a provable 2-D grid."""

        image = Image.new("RGB", (1030, 430), "white")
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = 55, 54, 972, 276
        for index in range(6):
            x = round(left + (right - left) * index / 5)
            draw.line((x, top, x, bottom), fill=(150, 150, 150))
        for index in range(4):
            y = round(top + (bottom - top) * index / 3)
            draw.line((left, y, right, y), fill=(150, 150, 150))

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (left, top, right, bottom),
        )

    def test_plot_box_accepts_pale_product_graph_grid(self) -> None:
        """Low-resolution datasheets may render their grid above level 230."""

        image = Image.new("RGB", (389, 321), "white")
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = 44, 62, 372, 261
        for index in range(11):
            x = round(left + (right - left) * index / 10)
            draw.line((x, top, x, bottom), fill=(242, 242, 242))
        for index in range(6):
            y = round(top + (bottom - top) * index / 5)
            draw.line((left, y, right, y), fill=(242, 242, 242))

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (left, top, right, bottom),
        )

    def test_black_bordered_internal_grid_wins_over_article_text(self) -> None:
        """A product plot embedded above prose is located from its internal grid."""

        image = Image.new("RGB", (390, 560), "white")
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = 64, 29, 331, 216
        draw.rectangle((left, top, right, bottom), outline=(0, 0, 0))
        for index in range(1, 11):
            x = round(left + (right - left) * index / 11)
            draw.line((x, top, x, bottom), fill=(150, 150, 150))
        for index in range(1, 5):
            y = round(top + (bottom - top) * index / 5)
            draw.line((left, y, right, y), fill=(150, 150, 150))
        draw.line((left, 48, right, 130), fill=(23, 111, 192), width=2)
        draw.line((left, 48, right, 170), fill=(0, 166, 80), width=2)
        for y in range(384, 560, 16):
            for x in range(17, 190, 24):
                draw.line((x, y, min(x + 12, 189), y), fill=(90, 90, 90))

        self.assertEqual(
            digitizer_module._detect_plot_box(np.asarray(image)),
            (left, top, right, bottom),
        )

    def test_antialias_bridge_track_is_not_reported_as_a_third_curve(self) -> None:
        """A blended middle colour is raster evidence, not a physical trace."""

        x_full = np.arange(481, dtype=np.float64)
        x_sparse = x_full[::2]

        def curve(
            rgb: tuple[int, int, int],
            x_values: np.ndarray,
            y_values: np.ndarray,
        ) -> digitizer_module.DigitizedCurve:
            return digitizer_module.DigitizedCurve(
                color="Synthetic",
                rgb=rgb,
                frequency_hz=x_values.copy(),
                magnitude_db=-y_values.copy(),
                pixel_points=np.column_stack((x_values, y_values)),
                confidence=0.8,
                observed_samples=x_values.size,
                sample_provenance=("observed",) * x_values.size,
            )

        orange = curve((244, 151, 60), x_full, 100 + 0.02 * x_full)
        green = curve((156, 186, 86), x_full, 104 + 0.02 * x_full)
        blended = curve((178, 176, 76), x_sparse, 102 + 0.02 * x_sparse)

        recovered = digitizer_module._collapse_antialias_alias_tracks(
            (orange, green, blended),
            (0, 0, 480, 200),
        )

        self.assertEqual(len(recovered), 2)
        self.assertEqual({item.rgb for item in recovered}, {orange.rgb, green.rgb})

    def test_two_shades_of_one_antialiased_path_are_merged(self) -> None:
        """A dark centre and pale edge may become separate overlapping tracks."""

        x_first = np.arange(0, 351, dtype=np.float64)
        x_second = np.arange(180, 481, dtype=np.float64)

        def curve(
            rgb: tuple[int, int, int], x_values: np.ndarray
        ) -> digitizer_module.DigitizedCurve:
            y_values = 80 + 0.1 * x_values
            return digitizer_module.DigitizedCurve(
                color="Dark blue",
                rgb=rgb,
                frequency_hz=x_values.copy(),
                magnitude_db=-y_values.copy(),
                pixel_points=np.column_stack((x_values, y_values)),
                confidence=0.7,
                observed_samples=x_values.size,
                sample_provenance=("observed",) * x_values.size,
            )

        pale = curve((116, 123, 141), x_first)
        dark = curve((68, 76, 104), x_second)
        recovered = digitizer_module._collapse_antialias_alias_tracks(
            (pale, dark),
            (0, 0, 480, 200),
        )

        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].pixel_points[0, 0], 0)
        self.assertEqual(recovered[0].pixel_points[-1, 0], 480)

    def test_distinct_broad_pale_hue_recovers_a_second_physical_path(self) -> None:
        """A second hue remains recoverable when low-resolution pixels blend."""

        image = Image.new("RGB", (481, 201), "white")
        draw = ImageDraw.Draw(image)
        x_values = np.arange(481, dtype=np.float64)
        base_y = 96 + 0.02 * x_values
        draw.line(
            list(zip(x_values.astype(int), np.rint(base_y + 8).astype(int))),
            fill=(223, 238, 202),
            width=2,
        )
        existing = digitizer_module.DigitizedCurve(
            color="Yellow",
            rgb=(189, 171, 92),
            frequency_hz=x_values.copy(),
            magnitude_db=-base_y.copy(),
            pixel_points=np.column_stack((x_values, base_y)),
            confidence=0.8,
            observed_samples=x_values.size,
            sample_provenance=("observed",) * x_values.size,
        )

        recovered = digitizer_module._recover_distinct_antialias_companion(
            np.asarray(image),
            (existing,),
            (0, 0, 480, 200),
            start_hz=1e9,
            stop_hz=5e9,
            y_min_db=-40,
            y_max_db=0,
            spacing="linear",
        )

        self.assertEqual(len(recovered), 2)
        self.assertEqual(recovered[1].color, "Green")

    def test_axis_labels_become_editable_detected_defaults(self) -> None:
        lines = (
            OcrLine("1.00 dB/", 30, 12, 80, 18),
            OcrLine("1.00", 28, 62, 42, 18),
            OcrLine("0.00", 28, 98, 42, 18),
            OcrLine("-9.00", 22, 386, 48, 18),
            OcrLine("10.00 MHz (Step 10.00 MHz)", 78, 420, 180, 20),
            OcrLine("18000.00 MHz", 500, 420, 110, 20),
            OcrLine("SDD21", 275, 12, 90, 24),
        )

        result = detect_axis_calibration(
            lines,
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.status, "detected")
        self.assertEqual(result.start_hz, 10e6)
        self.assertEqual(result.stop_hz, 18e9)
        self.assertEqual(result.step_hz, 10e6)
        self.assertEqual(result.y_max_db, 1.0)
        self.assertEqual(result.y_min_db, -9.0)
        self.assertEqual(result.spacing, "linear")
        self.assertEqual(result.detected_parameter, "SDD21")

    def test_incomplete_axis_labels_are_prefilled_but_not_auto_accepted(self) -> None:
        result = detect_axis_calibration(
            (
                OcrLine("0", 30, 60, 20, 15),
                OcrLine("-40", 20, 390, 35, 15),
                OcrLine("1 GHz", 80, 420, 55, 18),
                OcrLine("5 GHz", 520, 420, 55, 18),
            ),
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.status, "review")
        self.assertEqual(result.start_hz, 1e9)
        self.assertEqual(result.stop_hz, 5e9)
        self.assertIsNone(result.step_hz)
        self.assertEqual(result.missing, ("step", "spacing"))

    def test_linear_division_label_identifies_spacing_without_fabricating_sweep_step(self) -> None:
        result = detect_axis_calibration(
            (
                OcrLine("50.000", 25, 52, 42, 16),
                OcrLine("-50.000", 18, 405, 52, 16),
                OcrLine("0.01 GHz", 78, 420, 62, 20),
                OcrLine("4.009 8.008 12.007 16.006 20.005", 160, 420, 220, 20),
                OcrLine("40 GHz", 500, 420, 60, 20),
                OcrLine("3.999 GHz/div", 570, 420, 88, 20),
            ),
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.start_hz, 10e6)
        self.assertEqual(result.stop_hz, 40e9)
        self.assertEqual(result.spacing, "linear")
        self.assertIsNone(result.step_hz)
        self.assertEqual(result.missing, ("step",))

    def test_internal_frequency_ticks_are_not_mistaken_for_axis_endpoints(self) -> None:
        result = detect_axis_calibration(
            (
                OcrLine("0", 30, 60, 20, 15),
                OcrLine("-40", 20, 390, 35, 15),
                OcrLine("1 GHz (Step 1 GHz)", 180, 420, 100, 18),
                OcrLine("4 GHz", 440, 420, 48, 18),
                OcrLine("S21", 280, 15, 45, 18),
            ),
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.status, "review")
        self.assertIsNone(result.start_hz)
        self.assertIsNone(result.stop_hz)
        self.assertIn("start", result.missing)
        self.assertIn("stop", result.missing)

    def test_numeric_frequency_ticks_use_positioned_axis_title_unit(self) -> None:
        result = detect_axis_calibration(
            (
                OcrLine("0", 78, 420, 12, 18),
                OcrLine("10", 190, 420, 20, 18),
                OcrLine("20", 310, 420, 20, 18),
                OcrLine("30", 430, 420, 20, 18),
                OcrLine("40", 548, 420, 20, 18),
                OcrLine("Frequency (GHz)", 260, 447, 130, 18),
                OcrLine("0", 30, 52, 20, 18),
                OcrLine("-40", 18, 402, 40, 18),
                OcrLine("SDC21", 280, 15, 65, 20),
            ),
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.start_hz, 0.0)
        self.assertEqual(result.stop_hz, 40e9)
        self.assertIsNone(result.step_hz)
        self.assertEqual(result.detected_parameter, "SDC21")

    def test_internal_y_ticks_are_not_mistaken_for_axis_endpoints(self) -> None:
        result = detect_axis_calibration(
            (
                OcrLine("-10", 20, 120, 40, 18),
                OcrLine("-30", 20, 330, 40, 18),
                OcrLine("1 GHz (Step 1 GHz)", 78, 420, 120, 18),
                OcrLine("5 GHz", 520, 420, 55, 18),
                OcrLine("S21", 280, 15, 45, 18),
            ),
            plot_box=(80, 50, 560, 410),
            image_width=640,
            image_height=480,
        )

        self.assertEqual(result.status, "review")
        self.assertIsNone(result.y_max_db)
        self.assertIsNone(result.y_min_db)
        self.assertIn("y_max", result.missing)
        self.assertIn("y_min", result.missing)

    def test_ocr_parameter_label_must_be_unambiguous(self) -> None:
        self.assertEqual(detect_parameter_text("SDD21 2:SDD21"), ("SDD21", ()))
        parameter, warnings = detect_parameter_text("SDD11 2SDD21")
        self.assertIsNone(parameter)
        self.assertIn("Multiple", warnings[0])
        parameter, warnings = detect_parameter_text("SCD21 and SCC11")
        self.assertIsNone(parameter)
        self.assertIn("Multiple", warnings[0])
        parameter, warnings = detect_parameter_text("curve without a label")
        self.assertIsNone(parameter)
        self.assertIn("No S-parameter", warnings[0])

    def test_two_known_colored_curves_are_recovered_in_db(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            case = _write_known_plot(path)
            result = digitize_plot_image(
                path,
                start_hz=case["axis"]["start_hz"],
                stop_hz=case["axis"]["stop_hz"],
                y_min_db=case["axis"]["y_min_db"],
                y_max_db=case["axis"]["y_max_db"],
                run_ocr=False,
            )

        image_spec = case["image"]
        x_normalized = np.linspace(0.0, 1.0, image_spec["plot_box"][2] - image_spec["plot_box"][0] + 1)
        expected_by_color = {
            "Dark blue": -2.0 - 8.0 * x_normalized,
            "Red": -5.0 - 20.0 * x_normalized,
        }
        tolerance = case["tolerance"]
        self.assertTrue(
            np.allclose(result.plot_box, image_spec["plot_box"], atol=tolerance["plot_edge_px"])
        )
        actual_by_color = {curve.color: curve for curve in result.curves}
        self.assertEqual(set(actual_by_color), set(expected_by_color))
        for color, expected in expected_by_color.items():
            curve = actual_by_color[color]
            expected_at_samples = np.interp(
                curve.frequency_hz,
                np.linspace(
                    case["axis"]["start_hz"],
                    case["axis"]["stop_hz"],
                    expected.size,
                ),
                expected,
            )
            self.assertLessEqual(
                float(np.max(np.abs(curve.magnitude_db - expected_at_samples))),
                tolerance["magnitude_db"],
            )

    def test_log_frequency_axis_uses_geometric_pixel_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            result = digitize_plot_image(
                path,
                start_hz=1e6,
                stop_hz=1e9,
                y_min_db=-40,
                y_max_db=0,
                spacing="log",
                run_ocr=False,
            )

        curve = max(result.curves, key=lambda item: item.frequency_hz.size)
        middle = curve.frequency_hz[curve.frequency_hz.size // 2]
        self.assertAlmostEqual(np.log10(middle), 7.5, delta=0.03)

    def test_arbitrary_curve_colors_keep_their_actual_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arbitrary-colors.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 100, 560, 220), fill=(240, 130, 30), width=3)
            draw.line((80, 250, 560, 360), fill=(145, 55, 210), width=3)
            image.save(path)
            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        actual = np.asarray([curve.rgb for curve in result.curves])
        self.assertEqual(actual.shape[0], 2)
        for expected in ((240, 130, 30), (145, 55, 210)):
            self.assertLess(np.min(np.linalg.norm(actual - expected, axis=1)), 20)

    def test_blank_plot_fails_instead_of_advertising_fake_curves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            image.save(path)
            with self.assertRaisesRegex(ValueError, "No supported coloured"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )

    def test_image_without_a_locatable_plot_area_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "curves-without-grid.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            draw.line((30, 100, 610, 240), fill=(36, 76, 206), width=3)
            draw.line((30, 160, 610, 330), fill=(216, 54, 64), width=3)
            image.save(path)

            with self.assertRaisesRegex(ValueError, "regular plot grid"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )

    def test_short_colored_legend_inside_grid_is_not_a_curve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legend-only.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((90, 70, 190, 70), fill=(216, 54, 64), width=3)
            image.save(path)
            with self.assertRaisesRegex(ValueError, "No supported coloured"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )

    def test_two_full_width_tracks_with_the_same_color_are_kept_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ambiguous-red-tracks.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 140, 560, 140), fill=(216, 54, 64), width=3)
            draw.line((80, 320, 560, 320), fill=(216, 54, 64), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        medians = sorted(float(np.median(curve.magnitude_db)) for curve in result.curves)
        self.assertGreater(medians[1] - medians[0], 15.0)

    def test_unlabelled_gray_trace_is_recovered_without_treating_grid_as_data(
        self,
    ) -> None:
        """A neutral trace is data even when no legend or parameter text exists."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unlabelled-gray-trace.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 80, 50, 560, 410
            for index in range(11):
                x = left + 48 * index
                y = top + 36 * index
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            expected = np.asarray(
                [
                    (
                        x,
                        round(145 + 0.22 * (x - left) + 5 * np.sin((x - left) / 31)),
                    )
                    for x in range(left, right + 1)
                ],
                dtype=np.float64,
            )
            draw.line(
                [tuple(point.astype(int)) for point in expected],
                fill=(72, 72, 72),
                width=3,
            )
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(result.detected_parameter, None)
        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        actual_y = np.interp(
            expected[:, 0], curve.pixel_points[:, 0], curve.pixel_points[:, 1]
        )
        self.assertLess(float(np.median(np.abs(actual_y - expected[:, 1]))), 2.5)
        self.assertGreater(curve.observed_samples, expected.shape[0] * 0.80)

    def test_unlabelled_dashed_gray_trace_remains_one_visible_curve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unlabelled-dashed-gray-trace.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 80, 50, 560, 410
            for index in range(11):
                x = left + 48 * index
                y = top + 36 * index
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            expected_y: dict[int, float] = {}
            for dash_start in range(left, right + 1, 24):
                points: list[tuple[int, int]] = []
                for x in range(dash_start, min(dash_start + 15, right + 1)):
                    y = round(170 + 0.18 * (x - left) + 4 * np.sin((x - left) / 37))
                    points.append((x, y))
                    expected_y[x] = float(y)
                if len(points) >= 2:
                    draw.line(points, fill=(82, 82, 82), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        sample_x = np.asarray(sorted(expected_y), dtype=np.float64)
        sample_y = np.asarray([expected_y[int(x)] for x in sample_x])
        actual_y = np.interp(sample_x, curve.pixel_points[:, 0], curve.pixel_points[:, 1])
        self.assertLess(float(np.median(np.abs(actual_y - sample_y))), 2.5)
        self.assertGreater(curve.observed_samples, 220)

    def test_sparse_partial_companion_trace_remains_available_for_manual_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial-companion.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 150, 560, 250), fill=(188, 168, 184), width=2)
            for x in range(80, 341):
                if x % 3:
                    y = round(158 + (x - 80) * 100 / 480)
                    draw.point((x, y), fill=(165, 145, 162))
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        self.assertTrue(any(curve.frequency_hz.size < 300 for curve in result.curves))

    def test_occluded_same_parameter_prefix_is_shared_from_unique_full_trace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "occluded-prefix.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            split_x = 230
            full_trace = [
                (x, 130 + round(0.18 * (x - 80))) for x in range(80, 561)
            ]
            visible_companion = [
                (
                    x,
                    130
                    + round(0.18 * (x - 80))
                    + round(0.028 * (x - split_x)),
                )
                for x in range(split_x, 561)
            ]
            draw.line(full_trace, fill=(36, 176, 206), width=3)
            draw.line(visible_companion, fill=(230, 120, 28), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-9,
                y_max_db=1,
                run_ocr=False,
                parameter_hint="SDD21",
            )

        self.assertEqual(len(result.curves), 2)
        curves = sorted(result.curves, key=lambda curve: curve.shared_overlap_samples)
        donor, completed = curves
        self.assertEqual(donor.shared_overlap_samples, 0)
        self.assertEqual(donor.observed_samples, 462)
        self.assertEqual(donor.interpolated_samples, 19)
        self.assertEqual(completed.observed_samples, 331)
        self.assertGreater(completed.shared_overlap_samples, 100)
        self.assertEqual(
            completed.observed_samples
            + completed.shared_overlap_samples
            + completed.interpolated_samples,
            completed.frequency_hz.size,
        )
        self.assertEqual(completed.frequency_hz.size, donor.frequency_hz.size)
        self.assertAlmostEqual(completed.frequency_hz[0], donor.frequency_hz[0])
        shared = completed.shared_overlap_samples
        np.testing.assert_allclose(
            completed.magnitude_db[:shared], donor.magnitude_db[:shared]
        )
        self.assertLess(completed.confidence, donor.confidence)

    def test_occluded_prefix_is_not_invented_without_parameter_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unassigned-partial.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 150, 560, 230), fill=(36, 176, 206), width=3)
            draw.line((230, 175, 560, 260), fill=(230, 120, 28), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-9,
                y_max_db=1,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        self.assertTrue(all(curve.shared_overlap_samples == 0 for curve in result.curves))
        self.assertGreater(
            max(curve.frequency_hz[0] for curve in result.curves)
            - min(curve.frequency_hz[0] for curve in result.curves),
            1e9,
        )

    def test_repeated_overlap_uses_one_common_grid_without_collapsing_separation(
        self,
    ) -> None:
        """Two low-saturation traces may repeatedly merge and separate."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repeated-overlap.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            purple_points: list[tuple[int, int]] = []
            rose_points: list[tuple[int, int]] = []
            for x in range(80, 561):
                base = 270 + round(0.05 * (x - 80) + 3 * np.sin((x - 80) / 35))
                if 230 <= x < 380:
                    purple_offset, rose_offset = -7, 7
                elif x >= 440:
                    purple_offset, rose_offset = -9, 9
                else:
                    purple_offset = rose_offset = 0
                purple_notch = round(65 * np.exp(-((x - 340) / 10) ** 2))
                rose_notch = round(45 * np.exp(-((x - 340) / 12) ** 2))
                purple_points.append((x, base + purple_offset + purple_notch))
                rose_points.append((x, base + rose_offset + rose_notch))
            draw.line(purple_points, fill=(172, 150, 167), width=2)
            draw.line(rose_points, fill=(196, 179, 186), width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=50,
                run_ocr=False,
                parameter_hint="SCC11",
            )

        self.assertEqual(len(result.curves), 2)
        expected_samples = result.plot_box[2] - result.plot_box[0] + 1
        self.assertEqual(
            [curve.frequency_hz.size for curve in result.curves],
            [expected_samples, expected_samples],
        )
        for curve in result.curves:
            self.assertAlmostEqual(curve.frequency_hz[0], 10e6)
            self.assertAlmostEqual(curve.frequency_hz[-1], 18e9)
            self.assertEqual(
                curve.observed_samples
                + curve.shared_overlap_samples
                + curve.interpolated_samples,
                expected_samples,
            )
            self.assertGreater(curve.shared_overlap_samples, 100)
        tail_difference = np.abs(
            result.curves[0].magnitude_db[-80:]
            - result.curves[1].magnitude_db[-80:]
        )
        self.assertGreater(float(np.median(tail_difference)), 2.0)

    def test_unlabelled_repeated_overlap_uses_two_sided_visual_evidence(
        self,
    ) -> None:
        """Legend text is not required when both identities reappear visibly."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unlabelled-repeated-overlap.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            first: list[tuple[int, int]] = []
            second: list[tuple[int, int]] = []
            for x in range(80, 561):
                base = 270 + round(0.05 * (x - 80) + 3 * np.sin((x - 80) / 35))
                if 230 <= x < 380:
                    first_offset, second_offset = -7, 7
                elif x >= 440:
                    first_offset, second_offset = -9, 9
                else:
                    first_offset = second_offset = 0
                first.append(
                    (
                        x,
                        base
                        + first_offset
                        + round(65 * np.exp(-((x - 340) / 10) ** 2)),
                    )
                )
                second.append(
                    (
                        x,
                        base
                        + second_offset
                        + round(45 * np.exp(-((x - 340) / 12) ** 2)),
                    )
                )
            draw.line(first, fill=(172, 150, 167), width=2)
            draw.line(second, fill=(196, 179, 186), width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=50,
                run_ocr=False,
            )

        self.assertIsNone(result.detected_parameter)
        self.assertEqual(len(result.curves), 2)
        expected_samples = result.plot_box[2] - result.plot_box[0] + 1
        self.assertEqual(
            [curve.frequency_hz.size for curve in result.curves],
            [expected_samples, expected_samples],
        )
        self.assertTrue(
            all(curve.shared_overlap_samples > 80 for curve in result.curves)
        )

    def test_repeated_overlap_only_interpolates_short_two_sided_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repeated-overlap-short-gap.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            first: list[tuple[int, int]] = []
            second: list[tuple[int, int]] = []
            for x in range(80, 561):
                base = 230 + round(0.08 * (x - 80))
                separation = 0 if x < 230 or 360 <= x < 440 else 14
                first.append((x, base - separation))
                second.append((x, base + separation))
            draw.line(first, fill=(172, 150, 167), width=2)
            draw.line(second, fill=(196, 179, 186), width=2)
            draw.rectangle((318, 230, 320, 241), fill="white")
            draw.rectangle((318, 257, 320, 269), fill="white")
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=50,
                run_ocr=False,
                parameter_hint="SCC11",
            )

        self.assertEqual(len(result.curves), 2)
        expected_samples = result.plot_box[2] - result.plot_box[0] + 1
        self.assertEqual(
            [curve.frequency_hz.size for curve in result.curves],
            [expected_samples, expected_samples],
        )
        for curve in result.curves:
            self.assertGreaterEqual(curve.interpolated_samples, 3)
            self.assertEqual(
                curve.observed_samples
                + curve.shared_overlap_samples
                + curve.interpolated_samples,
                expected_samples,
            )

    def test_repeated_overlap_does_not_bridge_long_unsupported_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repeated-overlap-long-gap.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            first: list[tuple[int, int]] = []
            second: list[tuple[int, int]] = []
            for x in range(80, 561):
                base = 230 + round(0.08 * (x - 80))
                separation = 0 if x < 230 or 360 <= x < 440 else 14
                first.append((x, base - separation))
                second.append((x, base + separation))
            draw.line(first, fill=(172, 150, 167), width=2)
            draw.line(second, fill=(196, 179, 186), width=2)
            draw.rectangle((314, 230, 324, 241), fill="white")
            draw.rectangle((314, 257, 324, 269), fill="white")
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=18e9,
                y_min_db=-50,
                y_max_db=50,
                run_ocr=False,
                parameter_hint="SCC11",
            )

        self.assertEqual(len(result.curves), 2)
        expected_samples = result.plot_box[2] - result.plot_box[0] + 1
        self.assertTrue(
            any(curve.frequency_hz.size < expected_samples for curve in result.curves)
        )
        self.assertTrue(
            all(curve.shared_overlap_samples == 0 for curve in result.curves)
        )

    def test_coupled_gap_pairings_are_bounded(self) -> None:
        observations = [
            digitizer_module._TraceObservation(
                center=float(index), rgb=np.zeros(3, dtype=np.float64)
            )
            for index in range(5)
        ]

        completed = digitizer_module._fill_short_observation_gaps(
            [observations, [], observations], maximum_gap=3
        )

        self.assertIsNone(completed)

    def test_near_overlapping_different_colours_are_kept_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "near-overlapping-tracks.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            blue_points: list[tuple[int, int]] = []
            red_points: list[tuple[int, int]] = []
            for x in range(80, 561):
                center = 150 + round(0.18 * (x - 80))
                blue_points.append((x, center - 2))
                red_points.append((x, center + 2))
            draw.line(blue_points, fill=(36, 76, 206), width=2)
            draw.line(red_points, fill=(216, 54, 64), width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        actual = np.asarray([curve.rgb for curve in result.curves])
        for expected in ((36, 76, 206), (216, 54, 64)):
            self.assertLess(float(np.min(np.linalg.norm(actual - expected, axis=1))), 45.0)

    def test_fully_saturated_bright_green_trace_is_not_treated_as_white(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bright-green.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 160, 560, 250), fill=(0, 255, 0), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        self.assertEqual(result.curves[0].color, "Green")
        self.assertGreater(result.curves[0].observed_samples, 400)

    def test_adjacent_red_and_orange_traces_are_not_blended(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adjacent-red-orange.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 158, 560, 244), fill=(216, 54, 64), width=2)
            draw.line((80, 162, 560, 248), fill=(240, 130, 30), width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        actual = np.asarray([curve.rgb for curve in result.curves])
        for expected in ((216, 54, 64), (240, 130, 30)):
            self.assertLess(float(np.min(np.linalg.norm(actual - expected, axis=1))), 45.0)

    def test_fallback_does_not_join_two_half_width_coloured_traces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "separate-half-width-traces.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 160, 319, 160), fill=(216, 54, 64), width=3)
            draw.line((321, 210, 560, 210), fill=(36, 76, 206), width=3)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        self.assertTrue(all(curve.frequency_hz.size < 300 for curve in result.curves))
        spans = [curve.frequency_hz[-1] - curve.frequency_hz[0] for curve in result.curves]
        self.assertTrue(all(span < 2.2e9 for span in spans))

    def test_fallback_rejects_two_subthreshold_coloured_segments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "subthreshold-coloured-segments.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 160, 291, 160), fill=(216, 54, 64), width=3)
            draw.line((349, 210, 560, 210), fill=(36, 76, 206), width=3)
            image.save(path)

            with self.assertRaisesRegex(ValueError, "No supported coloured magnitude trace"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )

    def test_disconnected_same_colour_fragment_cannot_raise_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "disconnected-same-colour-fragment.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 160, 291, 160), fill=(216, 54, 64), width=3)
            draw.line((540, 160, 550, 160), fill=(216, 54, 64), width=3)
            image.save(path)

            with self.assertRaisesRegex(ValueError, "No supported coloured magnitude trace"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )

    def test_vertical_jump_starts_a_new_trace_even_for_similar_colours(self) -> None:
        cases = (
            (321, (216, 54, 64)),
            (340, (240, 110, 30)),
        )
        for second_start, second_colour in cases:
            with self.subTest(second_start=second_start, colour=second_colour):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "vertical-jump.png"
                    image = Image.new("RGB", (640, 480), "white")
                    draw = ImageDraw.Draw(image)
                    for index in range(11):
                        x = 80 + 48 * index
                        y = 50 + 36 * index
                        draw.line((x, 50, x, 410), fill=(190, 190, 190))
                        draw.line((80, y, 560, y), fill=(190, 190, 190))
                    draw.line((80, 160, 319, 160), fill=(216, 54, 64), width=3)
                    draw.line(
                        (second_start, 210, 560, 210),
                        fill=second_colour,
                        width=3,
                    )
                    image.save(path)

                    result = digitize_plot_image(
                        path,
                        start_hz=1e9,
                        stop_hz=5e9,
                        y_min_db=-40,
                        y_max_db=0,
                        run_ocr=False,
                    )

                self.assertEqual(len(result.curves), 2)
                self.assertTrue(
                    all(
                        float(np.max(np.abs(np.diff(curve.pixel_points[:, 1])))) < 20.0
                        for curve in result.curves
                    )
                )

    def test_pixel_connected_narrow_notch_remains_one_deep_trace(self) -> None:
        cases = (
            (3, 3),
            (2, 1),
        )
        for half_width, line_width in cases:
            with self.subTest(half_width=half_width, line_width=line_width):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "narrow-notch.png"
                    image = Image.new("RGB", (640, 480), "white")
                    draw = ImageDraw.Draw(image)
                    for index in range(11):
                        x = 80 + 48 * index
                        y = 50 + 36 * index
                        draw.line((x, 50, x, 410), fill=(190, 190, 190))
                        draw.line((80, y, 560, y), fill=(190, 190, 190))
                    draw.line(
                        (
                            (80, 160),
                            (320 - half_width, 160),
                            (320, 220),
                            (320 + half_width, 160),
                            (560, 160),
                        ),
                        fill=(216, 54, 64),
                        width=line_width,
                    )
                    image.save(path)

                    result = digitize_plot_image(
                        path,
                        start_hz=1e9,
                        stop_hz=5e9,
                        y_min_db=-40,
                        y_max_db=0,
                        run_ocr=False,
                    )

                self.assertEqual(len(result.curves), 1)
                self.assertGreater(float(np.max(result.curves[0].pixel_points[:, 1])), 200.0)

    def test_repeated_deep_notches_do_not_make_real_coloured_traces_disappear(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wilder-like-notches.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 100 + 56 * index
                y = 70 + 40 * index
                draw.line((x, 70, x, 470), fill=(190, 190, 190))
                draw.line((100, y, 660, y), fill=(190, 190, 190))
            for colour, offset, baseline_offset in (
                ((205, 141, 143), 0, 0),
                ((156, 188, 157), 6, 20),
            ):
                points: list[tuple[int, int]] = []
                for x in range(100, 661):
                    phase = (x - 100 + offset) % 18
                    notch = (
                        max(0, 3 - abs(phase - 9)) * 140 / 3
                        if abs(phase - 9) <= 3
                        else 0
                    )
                    baseline = (
                        300
                        + baseline_offset
                        + round(6 * np.sin((x - 100) / 23))
                    )
                    points.append((x, min(468, baseline + notch)))
                draw.line(points, fill=colour, width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=10e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertGreaterEqual(len(result.curves), 2)
        actual = np.asarray([curve.rgb for curve in result.curves])
        for expected in ((205, 141, 143), (156, 188, 157)):
            self.assertLess(float(np.min(np.linalg.norm(actual - expected, axis=1))), 55.0)

    def test_unique_hue_evidence_completes_a_trace_split_by_steep_notches(self) -> None:
        """One physical hue must not lose its prefix after narrow VNA notches."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wilder-fragmented-prefix.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 100, 70, 660, 470
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))

            # The hue is present in every plot column, but two one-pixel-wide
            # steep transitions split the continuity tracker into fragments.
            # The shorter prefix fragments mirror the Wilder Figure 33 failure.
            boundaries = (left, 212, 296, right + 1)
            levels = (220, 350, 275)
            for start, stop, level in zip(boundaries, boundaries[1:], levels):
                points = [
                    (x, level + round(4 * np.sin((x - left) / 17)))
                    for x in range(start, stop)
                ]
                draw.line(points, fill=(216, 54, 64), width=2)
            # A few isolated same-hue pixels model raster contamination. They
            # make the path slightly ambiguous, but far below the 5% limit.
            for x in range(150, 651, 100):
                draw.point((x, 410), fill=(216, 54, 64))
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=50e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        self.assertLessEqual(float(curve.pixel_points[0, 0]), left + 2)
        self.assertGreaterEqual(float(curve.pixel_points[-1, 0]), right - 2)
        self.assertGreaterEqual(curve.observed_samples, round((right - left + 1) * 0.95))

    def test_ambiguous_blue_hues_keep_one_physical_identity_per_trace(self) -> None:
        """A full-width fallback must not hop between two blue-family paths."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wilder-blue-identity.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 100, 70, 660, 470
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))

            expected_paths: list[np.ndarray] = []
            for colour, vertical in (
                (
                    (255, 120, 120),
                    lambda x: 190 + 0.12 * (x - left),
                ),
                (
                    (80, 80, 255),
                    lambda x: 205 + 0.15 * (x - left),
                ),
                (
                    (100, 190, 110),
                    lambda x: 350 + 18 * np.sin((x - left) / 17),
                ),
            ):
                points = np.asarray(
                    [(x, round(vertical(x))) for x in range(left, right + 1)],
                    dtype=np.float64,
                )
                expected_paths.append(points)
                draw.line(
                    [tuple(point.astype(int)) for point in points],
                    fill=colour,
                    width=2,
                )

            # Blue insertion loss and blue-grey return loss land in one broad
            # hue cluster after rasterisation.  The long first return-loss run
            # is an identity anchor; later unconnected steep transitions model
            # the line breaks seen in Wilder Figure 36.
            return_loss_points: list[tuple[int, int]] = []
            segment_starts = (
                left,
                left + 220,
                left + 288,
                left + 356,
                left + 424,
                left + 492,
            )
            segment_levels = (330, 420, 345, 435, 360, 410)
            for segment_index, start in enumerate(segment_starts):
                stop = (
                    segment_starts[segment_index + 1]
                    if segment_index + 1 < len(segment_starts)
                    else right + 1
                )
                points = [
                    (
                        x,
                        segment_levels[segment_index]
                        + round(6 * np.sin((x - start) / 10)),
                    )
                    for x in range(start, stop)
                ]
                return_loss_points.extend(points)
                draw.line(points, fill=(100, 140, 180), width=2)
            expected_paths.append(
                np.asarray(return_loss_points, dtype=np.float64)
            )
            # Raster exports can lose one pale return-loss sample while the
            # saturated blue insertion-loss trace remains visible in that
            # column.  The tracker must represent the pale trace as a short
            # gap; it must not borrow the other blue trace to stay full-width.
            missing_return_loss_columns = (left + 454, left + 518)
            expected_return_loss = expected_paths[-1]
            for missing_x in missing_return_loss_columns:
                expected_y = int(
                    expected_return_loss[expected_return_loss[:, 0] == missing_x, 1][0]
                )
                draw.rectangle(
                    (missing_x - 1, expected_y - 3, missing_x + 1, expected_y + 3),
                    fill="white",
                )
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=50e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 4)
        errors = np.full((len(expected_paths), len(result.curves)), np.inf)
        for expected_index, expected in enumerate(expected_paths):
            for actual_index, actual in enumerate(result.curves):
                actual_x = actual.pixel_points[:, 0]
                overlap = (expected[:, 0] >= actual_x[0]) & (
                    expected[:, 0] <= actual_x[-1]
                )
                if np.count_nonzero(overlap) < expected.shape[0] * 0.95:
                    continue
                actual_y = np.interp(
                    expected[overlap, 0],
                    actual_x,
                    actual.pixel_points[:, 1],
                )
                errors[expected_index, actual_index] = float(
                    np.median(np.abs(actual_y - expected[overlap, 1]))
                )
        best_assignment = np.argmin(errors, axis=1)
        self.assertEqual(len(set(best_assignment.tolist())), 4, errors)
        self.assertTrue(np.all(np.min(errors, axis=1) <= 4.0), errors)
        recovered_return_loss = result.curves[int(best_assignment[3])]
        for missing_x in missing_return_loss_columns:
            expected_y = float(
                expected_return_loss[expected_return_loss[:, 0] == missing_x, 1][0]
            )
            actual_y = float(
                np.interp(
                    missing_x,
                    recovered_return_loss.pixel_points[:, 0],
                    recovered_return_loss.pixel_points[:, 1],
                )
            )
            self.assertAlmostEqual(actual_y, expected_y, delta=5.0)
        self.assertEqual(recovered_return_loss.review_status, "review")
        self.assertLess(recovered_return_loss.visual_confidence, 1.0)
        interpolated_regions = [
            region
            for region in recovered_return_loss.review_regions
            if region.reason == "interpolated"
        ]
        self.assertTrue(interpolated_regions)
        for missing_x in missing_return_loss_columns:
            self.assertTrue(
                any(
                    region.start_x <= missing_x <= region.end_x
                    for region in interpolated_regions
                ),
                (missing_x, interpolated_regions),
            )

    def test_same_colour_plot_annotation_cannot_replace_a_trace_segment(self) -> None:
        """Short legend glyphs inside the grid are not physical curve samples."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotation-over-fragmented-trace.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 100, 70, 660, 470
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))

            expected_y: dict[int, int] = {}
            boundaries = (left, 212, 296, right + 1)
            levels = (320, 400, 335)
            for start, stop, level in zip(boundaries, boundaries[1:], levels):
                points = []
                for x in range(start, stop):
                    y = level + round(4 * np.sin((x - left) / 17))
                    expected_y[x] = y
                    points.append((x, y))
                draw.line(points, fill=(55, 155, 55), width=2)

            annotation_runs = (
                (510, 518),
                (525, 532),
                (540, 548),
                (555, 562),
                (570, 578),
                (585, 592),
            )
            for start, stop in annotation_runs:
                draw.rectangle((start, 105, stop, 111), fill=(55, 155, 55))
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=50e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        for start, stop in annotation_runs:
            for x in (start, (start + stop) // 2, stop):
                actual_y = float(
                    np.interp(x, curve.pixel_points[:, 0], curve.pixel_points[:, 1])
                )
                self.assertAlmostEqual(actual_y, expected_y[x], delta=6.0)
        self.assertGreater(curve.interpolated_samples, 0)

    def test_visual_review_flags_a_short_supported_upward_excursion(self) -> None:
        """A locally supported glyph-like detour must not hide as observed data."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supported-upward-excursion.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 80, 50, 560, 410
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            points = []
            for x in range(left, right + 1):
                y = 300 + round(5 * np.sin((x - left) / 30))
                if 310 <= x <= 318:
                    y = 170
                points.append((x, y))
            draw.line(points, fill=(50, 160, 70), width=2)
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        self.assertEqual(curve.review_status, "review")
        excursion_regions = [
            region
            for region in curve.review_regions
            if region.reason == "upward_excursion"
        ]
        self.assertTrue(excursion_regions, curve.review_regions)
        self.assertTrue(
            any(region.start_x <= 314 <= region.end_x for region in excursion_regions)
        )

    def test_visual_review_exposes_a_short_gap_in_source_raster_support(self) -> None:
        """Missing source columns stay visible even when interpolation looks smooth."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short-source-gap.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 80, 50, 560, 410
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            points = [
                (x, 250 + round(20 * np.sin((x - left) / 50)))
                for x in range(left, right + 1)
            ]
            draw.line(points, fill=(210, 50, 60), width=2)
            draw.rectangle((315, 200, 324, 300), fill="white")
            image.save(path)

            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 1)
        curve = result.curves[0]
        gaps = [
            region for region in curve.review_regions if region.reason == "raster_gap"
        ]
        self.assertTrue(gaps, curve.review_regions)
        self.assertTrue(any(region.start_x <= 320 <= region.end_x for region in gaps))

    def test_wilder_style_plot_recovers_all_four_visible_traces(self) -> None:
        """A lossless reference must retain four independently drawn paths."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wilder-four-traces.png"
            image = Image.new("RGB", (760, 540), "white")
            draw = ImageDraw.Draw(image)
            left, top, right, bottom = 100, 70, 660, 470
            for index in range(11):
                x = round(left + (right - left) * index / 10)
                y = round(top + (bottom - top) * index / 10)
                draw.line((x, top, x, bottom), fill=(190, 190, 190))
                draw.line((left, y, right, y), fill=(190, 190, 190))
            for x in (250, 430):
                for y in range(top, bottom, 8):
                    draw.line((x, y, x, min(y + 3, bottom)), fill=(130, 130, 130))

            expected_paths: list[np.ndarray] = []
            for colour, vertical in (
                (
                    (181, 185, 216),
                    lambda x: 272 + 0.10 * (x - left) + 4 * np.sin((x - left) / 45),
                ),
                (
                    (242, 200, 204),
                    lambda x: 275 + 0.08 * (x - left) + 3 * np.sin((x - left) / 52 + 1),
                ),
            ):
                points = np.asarray(
                    [(x, round(vertical(x))) for x in range(left, right + 1)],
                    dtype=np.float64,
                )
                expected_paths.append(points)
                draw.line([tuple(point.astype(int)) for point in points], fill=colour, width=2)

            for colour, offset, baseline_offset in (
                ((209, 233, 212), 0, 0),
                ((210, 229, 230), 6, 12),
            ):
                points: list[tuple[int, int]] = []
                for x in range(left, right + 1):
                    phase = (x - left + offset) % 18
                    notch = (
                        max(0, 3 - abs(phase - 9)) * 60 / 3
                        if abs(phase - 9) <= 3
                        else 0
                    )
                    baseline = 350 + baseline_offset + round(
                        5 * np.sin((x - left) / 23)
                    )
                    points.append((x, min(bottom - 2, round(baseline + notch))))
                expected = np.asarray(points, dtype=np.float64)
                expected_paths.append(expected)
                draw.line(points, fill=colour, width=2)

            image.save(path)
            result = digitize_plot_image(
                path,
                start_hz=50e6,
                stop_hz=40e9,
                y_min_db=-50,
                y_max_db=50,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 4)
        errors = np.full((len(expected_paths), len(result.curves)), np.inf)
        for expected_index, expected in enumerate(expected_paths):
            for actual_index, actual in enumerate(result.curves):
                actual_x = actual.pixel_points[:, 0]
                overlap = (expected[:, 0] >= actual_x[0]) & (expected[:, 0] <= actual_x[-1])
                # Raw digitization preserves the part that is actually visible.
                # Common-grid resampling is a separate workspace responsibility.
                if np.count_nonzero(overlap) < expected.shape[0] * 0.6:
                    continue
                actual_y = np.interp(
                    expected[overlap, 0],
                    actual_x,
                    actual.pixel_points[:, 1],
                )
                errors[expected_index, actual_index] = float(
                    np.median(np.abs(actual_y - expected[overlap, 1]))
                )
        best_assignment = np.argmin(errors, axis=1)
        self.assertEqual(len(set(best_assignment.tolist())), 4, errors)
        raster_tolerance = max(4.0, (bottom - top) * 0.03)
        self.assertTrue(
            np.all(np.min(errors, axis=1) <= raster_tolerance), errors
        )
        self.assertFalse(
            any(
                region.reason == "upward_excursion"
                for curve in result.curves
                for region in curve.review_regions
            ),
            [curve.review_regions for curve in result.curves],
        )

    def test_crossing_different_colours_keep_identity_instead_of_swapping_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "crossing-tracks.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            for x in range(80, 560):
                fraction = (x - 80) / 480
                red_y = round(120 + 200 * fraction)
                red_next = round(120 + 200 * (fraction + 1 / 480))
                blue_y = round(320 - 200 * fraction)
                blue_next = round(320 - 200 * (fraction + 1 / 480))
                draw.line((x, red_y, x + 1, red_next), fill=(216, 54, 64), width=3)
                draw.line((x, blue_y, x + 1, blue_next), fill=(36, 76, 206), width=3)
            image.save(path)
            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
            )

        self.assertEqual(len(result.curves), 2)
        red = min(result.curves, key=lambda item: np.linalg.norm(np.asarray(item.rgb) - (216, 54, 64)))
        blue = min(result.curves, key=lambda item: np.linalg.norm(np.asarray(item.rgb) - (36, 76, 206)))
        self.assertAlmostEqual(float(red.pixel_points[0, 1]), 120, delta=4)
        self.assertAlmostEqual(float(red.pixel_points[-1, 1]), 320, delta=4)
        self.assertAlmostEqual(float(blue.pixel_points[0, 1]), 320, delta=4)
        self.assertAlmostEqual(float(blue.pixel_points[-1, 1]), 120, delta=4)
        self.assertFalse(
            any(
                region.reason == "upward_excursion"
                for curve in result.curves
                for region in curve.review_regions
            )
        )

    def test_positive_gain_interval_rejects_whole_passive_track(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "active-trace.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line((80, 140, 560, 320), fill=(216, 54, 64), width=3)
            image.save(path)
            with self.assertRaisesRegex(ValueError, "No supported coloured"):
                digitize_plot_image(
                    path,
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-10,
                    y_max_db=5,
                    run_ocr=False,
                )

    def test_fallback_does_not_invent_a_third_alternating_same_colour_trace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for separation in (13, 14, 16, 18, 180):
                for block_width in (1, 4, 8, 10):
                    with self.subTest(
                        separation=separation, block_width=block_width
                    ):
                        path = (
                            Path(directory)
                            / f"alternating-{separation}-{block_width}.png"
                        )
                        image = Image.new("RGB", (640, 480), "white")
                        draw = ImageDraw.Draw(image)
                        for index in range(11):
                            x = 80 + 48 * index
                            y = 50 + 36 * index
                            draw.line((x, 50, x, 410), fill=(190, 190, 190))
                            draw.line((80, y, 560, y), fill=(190, 190, 190))
                        colour = (180, 55, 70)
                        for x in range(80, 561):
                            block = (x - 80) // block_width
                            y = 140 if block % 2 == 0 else 140 + separation
                            draw.point((x, y), fill=colour)
                        image.save(path)

                        result = digitize_plot_image(
                            path,
                            start_hz=1e9,
                            stop_hz=5e9,
                            y_min_db=-40,
                            y_max_db=0,
                            run_ocr=False,
                        )

                        self.assertEqual(len(result.curves), 2)
                        self.assertEqual(
                            sorted(curve.frequency_hz.size for curve in result.curves),
                            [240, 241],
                        )

    def test_excessive_decoded_pixel_count_is_rejected_before_conversion(self) -> None:
        opened = mock.MagicMock()
        opened.__enter__.return_value = opened
        opened.width = 10_000
        opened.height = 10_000
        with mock.patch(
            "insertion_loss_tool.datasheet_digitizer.Image.open", return_value=opened
        ):
            with self.assertRaisesRegex(ValueError, "megapixel limit"):
                digitize_plot_image(
                    "large.png",
                    start_hz=1e9,
                    stop_hz=5e9,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                )
        opened.convert.assert_not_called()

    def test_ocr_decode_error_keeps_curves_and_falls_back_to_manual_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            case = _write_known_plot(path)
            with mock.patch(
                "insertion_loss_tool.datasheet_digitizer.shutil.which",
                return_value="/usr/bin/tesseract",
            ), mock.patch(
                "insertion_loss_tool.datasheet_digitizer.subprocess.run",
                side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
            ):
                result = digitize_plot_image(
                    path,
                    start_hz=case["axis"]["start_hz"],
                    stop_hz=case["axis"]["stop_hz"],
                    y_min_db=case["axis"]["y_min_db"],
                    y_max_db=case["axis"]["y_max_db"],
                    run_ocr=True,
                )
        self.assertEqual(len(result.curves), 2)
        self.assertIsNone(result.detected_parameter)
        self.assertIn("OCR did not complete", result.warnings[0])

    def test_adaptive_color_masks_are_bounded_arrays_with_observed_rgb(self) -> None:
        crop = np.full((600, 800, 3), 255, dtype=np.uint8)
        crop[:, 100:103] = (216, 54, 64)
        masks = digitizer_module._adaptive_color_masks(crop)

        self.assertEqual(len(masks), 1)
        name, rgb, mask, chroma = masks[0]
        self.assertEqual(name, "Red")
        self.assertEqual(rgb, (216, 54, 64))
        self.assertEqual(mask.dtype, np.bool_)
        self.assertEqual(chroma.dtype, np.uint8)
        self.assertEqual(mask.shape, (600, 800))

    def test_adaptive_colour_clusters_do_not_claim_the_same_antialias_pixel(self) -> None:
        crop = np.full((30, 300, 3), 255, dtype=np.uint8)
        crop[5:8, :] = (209, 233, 212)
        crop[15:18, :] = (210, 229, 230)
        crop[10, :] = (209, 232, 221)

        masks = digitizer_module._adaptive_color_masks(crop)

        self.assertGreaterEqual(len(masks), 2)
        membership = np.sum(
            np.asarray([mask for _name, _rgb, mask, _chroma in masks]), axis=0
        )
        self.assertLessEqual(int(np.max(membership)), 1)

    def test_analyzed_axes_are_editable_defaults_and_enable_auto_digitize(self) -> None:
        api = InsertionLossWebApi()
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="detected",
                start_hz=10e6,
                stop_hz=18e9,
                step_hz=10e6,
                y_min_db=-9.0,
                y_max_db=1.0,
                spacing="linear",
                detected_parameter="SDD21",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            api.register_images([path])
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                return_value=analysis,
            ):
                response = api.analyze_image(0)

        self.assertTrue(response["ok"])
        self.assertTrue(response["auto_digitize"])
        axis = response["image_update"]["axis"]
        self.assertEqual(axis["source"], "detected")
        self.assertEqual(axis["status"], "ready")
        self.assertEqual(axis["start"], "10MHz")
        self.assertEqual(axis["stop"], "18GHz")
        self.assertEqual(axis["step"], "10MHz")
        self.assertEqual(axis["y_min_db"], -9.0)
        self.assertEqual(axis["y_max_db"], 1.0)

    def test_partial_analysis_prefills_values_but_does_not_auto_digitize(self) -> None:
        api = InsertionLossWebApi()
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="review",
                start_hz=1e9,
                stop_hz=5e9,
                y_min_db=-40,
                y_max_db=0,
                missing=("step", "spacing"),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            api.register_images([path])
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                return_value=analysis,
            ):
                response = api.analyze_image(0)

        self.assertTrue(response["ok"])
        self.assertFalse(response["auto_digitize"])
        self.assertEqual(response["image_update"]["axis"]["status"], "review")
        self.assertEqual(response["image_update"]["axis"]["start"], "1GHz")
        self.assertEqual(response["image_update"]["axis"]["step"], "")

    def test_visible_linear_axes_use_native_pixel_spacing_as_editable_default(self) -> None:
        api = InsertionLossWebApi()
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="review",
                start_hz=10e6,
                stop_hz=40e9,
                step_hz=None,
                y_min_db=-50,
                y_max_db=50,
                spacing="linear",
                missing=("step",),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            api.register_images([path])
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                return_value=analysis,
            ):
                response = api.analyze_image(0)

        self.assertTrue(response["ok"])
        self.assertTrue(response["auto_digitize"])
        axis = response["image_update"]["axis"]
        self.assertEqual(axis["source"], "detected-pixel")
        self.assertEqual(axis["points"], 481)
        self.assertAlmostEqual(axis["step_hz"], (40e9 - 10e6) / 480)

    def test_workspace_exposes_curves_only_after_explicit_digitization(self) -> None:
        api = InsertionLossWebApi()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            registered = api.register_images([path])
            self.assertNotIn("图1 A", " ".join(registered["source_options"]))
            self.assertFalse(api.digitize_image(0, -40, 0)["ok"])
            calibrated = api.set_image_frequency(0, "1GHz", "5GHz", "10MHz")
            self.assertEqual(calibrated["image_update"]["digitization"]["status"], "ready")
            recognized = api.digitize_image(0, -40, 0)

        self.assertTrue(recognized["ok"], recognized)
        update = recognized["image_update"]
        self.assertEqual(update["digitization"]["status"], "digitized")
        self.assertEqual(len(update["curves"]), 2)
        self.assertGreater(update["curves"][0]["samples"], 300)
        self.assertLessEqual(len(update["curves"][0]["preview_points"]), 800)
        self.assertIn("图1 A · 深蓝", recognized["source_options"])
        self.assertIn("图1 B · 红", recognized["source_options"])

    def test_workspace_exposes_unlabelled_gray_trace_for_manual_mapping(self) -> None:
        api = InsertionLossWebApi()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace-gray.png"
            image = Image.new("RGB", (640, 480), "white")
            draw = ImageDraw.Draw(image)
            for index in range(11):
                x = 80 + 48 * index
                y = 50 + 36 * index
                draw.line((x, 50, x, 410), fill=(190, 190, 190))
                draw.line((80, y, 560, y), fill=(190, 190, 190))
            draw.line(
                [
                    (x, round(150 + 0.20 * (x - 80) + 4 * np.sin((x - 80) / 31)))
                    for x in range(80, 561)
                ],
                fill=(72, 72, 72),
                width=3,
            )
            image.save(path)
            api.register_images([path])
            api.set_image_frequency(0, "10MHz", "18GHz", "10MHz")
            recognized = api.digitize_image(0, -50, 0)

        self.assertTrue(recognized["ok"], recognized)
        curve = recognized["image_update"]["curves"][0]
        self.assertEqual(curve["parameter"], "自动")
        self.assertEqual(curve["color"], "灰")
        self.assertIn("图1 A · 灰", recognized["source_options"])

    def test_failed_redigitization_clears_stale_curves_and_returns_ui_state(self) -> None:
        api = InsertionLossWebApi()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            api.register_images([path])
            api.set_image_frequency(0, "1GHz", "5GHz", "10MHz")
            self.assertTrue(api.digitize_image(0, -40, 0)["ok"])
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=RuntimeError("unexpected decoder failure"),
            ):
                failed = api.digitize_image(0, -40, 0)

        self.assertFalse(failed["ok"])
        self.assertEqual(failed["image_update"]["digitization"]["status"], "failed")
        self.assertEqual(failed["image_update"]["curves"], [])
        self.assertNotIn("图1 A", " ".join(failed["source_options"]))

    def test_axis_change_during_digitization_rejects_the_stale_result(self) -> None:
        api = InsertionLossWebApi()
        started = threading.Event()
        resume = threading.Event()
        original_digitize = digitize_plot_image
        result_holder: dict[str, object] = {}

        def delayed_digitize(*args: object, **kwargs: object) -> object:
            started.set()
            self.assertTrue(resume.wait(timeout=2))
            return original_digitize(*args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "known-curves.png"
            _write_known_plot(path)
            api.register_images([path])
            api.set_image_frequency(0, "1GHz", "5GHz", "10MHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=delayed_digitize,
            ):
                worker = threading.Thread(
                    target=lambda: result_holder.update(api.digitize_image(0, -40, 0))
                )
                worker.start()
                self.assertTrue(started.wait(timeout=2))
                changed = api.set_image_frequency(0, "2GHz", "4GHz", "20MHz")
                resume.set()
                worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertFalse(result_holder["ok"])
        self.assertEqual(changed["image_update"]["axis"]["start"], "2GHz")
        self.assertEqual(result_holder["image_update"]["axis"]["start"], "2GHz")
        self.assertEqual(result_holder["image_update"]["digitization"]["status"], "ready")
        self.assertEqual(result_holder["image_update"]["curves"], [])


if __name__ == "__main__":
    unittest.main()
