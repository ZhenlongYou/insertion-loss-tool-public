"""Public-image regression tests with independently drawn raster geometry.

The oracle is the supplied drawing, not a production colour helper. The tip
tolerance is half the visible pen width plus one pixel of raster quantisation;
it is deliberately not an instrument-amplitude or subpixel-accuracy claim.
"""

from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


class ImageTraceFidelityTests(unittest.TestCase):
    """Protect both turn directions, neutral traces, manual paths and noise."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.box = (80, 50, 560, 410)
        self.x = np.arange(80, 561)

    def _image(self, y, colour, stroke=3, noise=False):
        """Draw an ordinary neutral grid and one independently specified trace."""

        image = Image.new("RGB", (640, 480), "white")
        draw = ImageDraw.Draw(image)
        for index in range(11):
            draw.line((80 + index * 48, 50, 80 + index * 48, 410), fill=(190,) * 3)
            draw.line((80, 50 + index * 36, 560, 50 + index * 36), fill=(190,) * 3)
        draw.line(list(zip(self.x, y)), fill=colour, width=stroke)
        if noise:
            # Same-colour speckles above/below the curve must not define tips.
            draw.rectangle((320, 372, 325, 379), fill=colour)
            draw.rectangle((280, 70, 285, 76), fill=colour)
        path = Path(self.directory.name) / "source.png"
        image.save(path)
        return path

    def _read(self, path, colour=None, anchors=()):
        """Exercise the public native-image path, including manual trace specs."""

        options = {}
        if colour is not None:
            options.update(plot_box_override=self.box, trace_specs=[{
                "id": "specified", "label": "Specified trace", "rgb": colour,
                "anchors": anchors,
            }])
        result = digitize_plot_image(path, start_hz=0, stop_hz=1e9,
            y_min_db=-60, y_max_db=0, run_ocr=False, **options)
        self.assertEqual(len(result.curves), 1)
        return result.curves[0]

    def test_both_turn_directions_colours_and_linewidths(self):
        for direction in (-1, 1):
            for stroke in (1, 3, 5):
                for colour in ((210, 35, 35), (30, 65, 210), (0, 0, 0), (72, 72, 72)):
                    with self.subTest(direction=direction, stroke=stroke, colour=colour):
                        center = 170 if direction == 1 else 300
                        y = np.round(center + direction * 145 * np.exp(-((self.x - 323) / 2) ** 2))
                        curve = self._read(self._image(y, colour, stroke))
                        tip = float(np.interp(323, *curve.pixel_points.T))
                        self.assertLessEqual(abs(tip - (center + direction * 145)), stroke / 2 + 1)
                        self.assertEqual(curve.review_status, "review")
                        self.assertLess(curve.visual_confidence, 1)

    def test_subpixel_narrow_notch_retains_visible_tip_and_ignores_speckles(self):
        y = np.round(170 + 180 * np.exp(-((self.x - 323) / 1) ** 2))
        curve = self._read(self._image(y, (210, 35, 35), noise=True))
        self.assertLessEqual(abs(np.max(curve.pixel_points[:, 1]) - 350), 2.5)
        self.assertLessEqual(abs(np.min(curve.pixel_points[:, 1]) - 170), 2.5)

    def test_dark_and_horizontal_neutral_lines_are_not_grids(self):
        for value in (0, 12, 24, 72, 232):
            for horizontal in (False, True):
                with self.subTest(value=value, horizontal=horizontal):
                    y = np.full(len(self.x), 175) if horizontal else 145 + .22 * (self.x - 80)
                    curve = self._read(self._image(y, (value,) * 3))
                    expected = np.interp(curve.pixel_points[:, 0], self.x, y)
                    self.assertLessEqual(float(np.max(abs(curve.pixel_points[:, 1] - expected))), 2.5)
                    self.assertGreater(len(curve.pixel_points), .95 * len(self.x))

    def test_manual_path_uses_the_same_tip_evidence(self):
        colour = (210, 35, 35)
        y = np.round(170 + 180 * np.exp(-((self.x - 323) / 1) ** 2))
        path = self._image(y, colour)
        curve = self._read(path, colour=colour)
        self.assertLessEqual(abs(np.interp(323, *curve.pixel_points.T) - 350), 2.5)
        anchored = self._read(path, colour=colour, anchors=((80, 170), (323, 340), (560, 170)))
        self.assertEqual(np.interp(323, *anchored.pixel_points.T), 340)
        self.assertEqual(anchored.review_status, "review")

    def test_manual_pale_gray_does_not_select_white_background(self):
        y = np.full(len(self.x), 175)
        curve = self._read(self._image(y, (232,) * 3), colour=(232,) * 3)
        self.assertLessEqual(float(np.max(abs(curve.pixel_points[:, 1] - 175))), 2.5)

    def test_dark_chromatic_curve_is_not_rejected_by_brightness(self):
        y = 145 + .22 * (self.x - 80)
        curve = self._read(self._image(y, (24, 0, 0)))
        expected = np.interp(curve.pixel_points[:, 0], self.x, y)
        self.assertLessEqual(float(np.max(abs(curve.pixel_points[:, 1] - expected))), 2.5)

    def test_short_left_anchored_black_trace_keeps_its_bandwidth(self):
        # Different bandwidths share one plot; the short black trace is not
        # extended to the full-span coloured trace or exchanged for a legend.
        path = self._image(np.full(len(self.x), 280), (210, 35, 35))
        image = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.line([(80, 110), (250, 130)], fill=(0, 0, 0), width=3)
        draw.text((290, 145), "BLACK TRACE LABEL", fill=(0, 0, 0))
        image.save(path)
        result = digitize_plot_image(path, start_hz=0, stop_hz=1e9,
            y_min_db=-60, y_max_db=0, run_ocr=False)
        self.assertEqual(len(result.curves), 2)
        neutral = next(curve for curve in result.curves if np.ptp(curve.rgb) <= 5)
        self.assertLessEqual(neutral.pixel_points[-1, 0], 252)
        self.assertLessEqual(float(np.max(abs(neutral.pixel_points[:, 1] - (110 + (neutral.pixel_points[:, 0] - 80) * 20 / 170)))), 2.5)
        self.assertEqual(neutral.review_status, "review")
        self.assertTrue(any(region.reason == "missing_endpoint" for region in neutral.review_regions))

    def test_three_horizontal_grid_lines_do_not_become_a_trace(self):
        # Two plot borders and one middle grid line are three independent
        # bands, even though the image has fewer than four horizontal bands.
        for explicit_box in (False, True):
            for colour in (None, (210, 35, 35), (72, 72, 72), (190, 190, 190)):
                with self.subTest(explicit_box=explicit_box, colour=colour):
                    image = Image.new("RGB", (640, 480), "white")
                    draw = ImageDraw.Draw(image)
                    for x in range(80, 561, 48):
                        draw.line((x, 50, x, 410), fill=(190,) * 3)
                    for y in (50, 230, 410):
                        draw.line((80, y, 560, y), fill=(190,) * 3)
                    if colour is not None:
                        draw.line((80, 175, 560, 175), fill=colour, width=3)
                    path = Path(self.directory.name) / "three-grid-lines.png"
                    image.save(path)
                    options = {"plot_box_override": self.box} if explicit_box else {}
                    if colour is None:
                        with self.assertRaisesRegex(ValueError, "No supported"):
                            digitize_plot_image(path, start_hz=0, stop_hz=1e9,
                                y_min_db=-60, y_max_db=0, run_ocr=False, **options)
                    else:
                        result = digitize_plot_image(path, start_hz=0, stop_hz=1e9,
                            y_min_db=-60, y_max_db=0, run_ocr=False, **options)
                        self.assertEqual(result.plot_box, self.box)
                        self.assertEqual(len(result.curves), 1)
                        self.assertLessEqual(float(np.max(abs(result.curves[0].pixel_points[:, 1] - 175))), 2.5)

    def test_manual_flat_trace_cannot_claim_a_crossing_same_colour_notch(self):
        # Endpoint anchors select the flat trace. Near a same-colour crossing,
        # pixels alone do not establish which branch owns the deep endpoint.
        # Require conservative unchanged association with a HIGH ambiguity flag;
        # this does not assert perfect recovery of the flat line in the overlap.
        for stroke in (1, 3, 5):
            for sigma in (1, 2, 3):
                with self.subTest(stroke=stroke, sigma=sigma):
                    colour = (210, 35, 35)
                    y = np.round(150 + 190 * np.exp(-((self.x - 323) / sigma) ** 2))
                    path = self._image(y, colour, stroke)
                    image = Image.open(path).convert("RGB")
                    ImageDraw.Draw(image).line((80, 200, 560, 200), fill=colour, width=stroke)
                    image.save(path)
                    curve = self._read(path, colour=colour, anchors=((80, 200), (560, 200)))
                    # The rejected notch belongs to the other trace at y340.
                    # A 300px ceiling separates wrong-branch restoration from
                    # the unresolved local column-centre deviations (<100px).
                    self.assertLess(float(np.max(curve.pixel_points[:, 1])), 300)
                    self.assertEqual(curve.pixel_points[0, 1], 200)
                    self.assertEqual(curve.pixel_points[-1, 1], 200)
                    self.assertTrue(any(region.reason == "unresolved_raster_turn" and region.severity == "high" for region in curve.review_regions))
                    self.assertFalse(any(region.reason == "raster_turn" for region in curve.review_regions))


if __name__ == "__main__":
    unittest.main()
