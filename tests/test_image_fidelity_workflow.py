"""预览与统一网格回归：手工已知极值、真实图像入口及独立 ASCII RI 读回。

合成图用于重现抽点/采样缺陷，不据此声明真实厂商曲线识别准确度。测试
既验证源点未改，也验证粗网格保持原样并有可操作提示，而细网格须显式选用。
"""

from pathlib import Path
import copy
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from insertion_loss_tool.image_sampling import extrema_preview, finer_uniform_step, sampling_check
from insertion_loss_tool.webview_gui import InsertionLossWebApi, InsertionLossJsApi


def write_notch_image(path):
    """1801 列图中在 x=982 画窄凹口；其频率落在 10 MHz 格点上。"""
    left, top, right, bottom = 80, 50, 1880, 410
    x = np.arange(left, right + 1)
    y = np.rint(170 + 150 * np.exp(-0.5 * ((x - 982) / 2.0) ** 2)).astype(int)
    image = Image.new("RGB", (1960, 480), "white")
    draw = ImageDraw.Draw(image)
    for index in range(11):
        draw.line((left + 180 * index, top, left + 180 * index, bottom), fill=(190, 190, 190))
        draw.line((left, top + 36 * index, right, top + 36 * index), fill=(190, 190, 190))
    draw.line(list(zip(x.tolist(), y.tolist())), fill=(220, 40, 40), width=1)
    image.save(path)


def read_s21_ri(path):
    """独立读取产品固定的 Hz RI 2-port ASCII 排列，不调用产品解析器。"""
    lines = Path(path).read_text().splitlines()
    header = next(line.upper().split() for line in lines if line.startswith("#"))
    if header[1:4] != ["HZ", "S", "RI"]:
        raise AssertionError(header)
    rows = np.array([[float(cell) for cell in line.split()] for line in lines
                     if line.strip() and not line.startswith(("#", "!"))])
    if rows.shape[1] != 9:
        raise AssertionError(rows.shape)
    return rows[:, 0], 20 * np.log10(np.hypot(rows[:, 3], rows[:, 4]))


class ImageSamplingUnitTests(unittest.TestCase):
    def test_preview_keeps_both_extrema_endpoints_and_input_unchanged(self):
        points = np.column_stack((np.arange(1801), np.zeros(1801)))
        points[902, 1], points[907, 1] = 100, -90
        points[-1, 1] = 7
        original = points.copy()
        preview = extrema_preview(points)
        self.assertLessEqual(len(preview), 800)
        np.testing.assert_array_equal(preview[[0, -1]], points[[0, -1]])
        self.assertEqual(float(preview[:, 1].max()), 100)
        self.assertEqual(float(preview[:, 1].min()), -90)
        self.assertTrue(np.all(np.diff(preview[:, 0]) > 0))
        np.testing.assert_array_equal(points, original)
        self.assertLessEqual(len(extrema_preview(points, 120)), 120)

    def test_local_extremum_loss_survives_unchanged_global_extremes(self):
        # 全局最小 -20 和最大 0 均保留，仍应发现 x=3 的局部 -5 被遗漏。
        frequency = np.arange(9, dtype=float)
        magnitude = np.array([0, -10, -20, -5, -10, -10, -10, -10, 0], dtype=float)
        report = sampling_check(frequency, magnitude, frequency[::2], 0.1)
        self.assertEqual(report["source_minimum_db"], report["output_minimum_db"])
        self.assertEqual(report["source_maximum_db"], report["output_maximum_db"])
        self.assertEqual(report["changed_extrema_count"], 1)
        self.assertEqual(report["extremum_losses"][0]["frequency_hz"], 3)
        self.assertEqual(report["extremum_losses"][0]["loss_db"], 5)

    def test_truncated_range_and_subpixel_differences_are_not_loss_alerts(self):
        frequency = np.arange(9, dtype=float)
        magnitude = np.array([0, -50, 0, -0.01, 0, 0, 0, 0, 0])
        report = sampling_check(frequency, magnitude, np.array([2, 4, 6, 8]), 0.1)
        self.assertEqual(report["source_minimum_db"], -0.01)
        self.assertEqual(report["status"], "sampling-difference")
        self.assertAlmostEqual(report["max_reconstruction_difference_db"], 0.01)
        agreement = sampling_check(frequency, magnitude, frequency)
        self.assertEqual(agreement["status"], "sampled-agreement")

    def test_finer_suggestion_divides_span_and_respects_resource_limit(self):
        source = np.linspace(0, 18e9, 1801)
        output = np.arange(100e6, 18e9 + 1, 100e6)
        step = finer_uniform_step(output, [source])
        self.assertEqual(step, 10e6)
        self.assertAlmostEqual((output[-1] - output[0]) / step, 1790)
        self.assertIsNone(finer_uniform_step(output, [source], max_points=100))


class ImageEditorCalibrationTests(unittest.TestCase):
    """仅通过真实 facade 复现频率修改后直接编辑及未提交 Y 表单。"""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "axis.png"
        image = Image.new("RGB", (240, 180), "white")
        ImageDraw.Draw(image).line([(20, 70), (220, 110)], fill=(70, 120, 180), width=2)
        image.save(self.path)
        self.api = InsertionLossWebApi()
        self.bridge = InsertionLossJsApi(self.api)
        self.api.register_images([self.path])
        self.assertTrue(self.api.set_image_frequency(0, "1GHz", "2GHz", "10MHz")["ok"])
        recipe = self.bridge.image_edit_recipe(0)["recipe"]
        recipe.update(plot_box=[20, 20, 220, 160], traces=[{
            "id": "line", "label": "line", "rgb": [70, 120, 180],
            "anchors": [[20, 70], [220, 110]],
        }])
        recipe["axis"].update(y_top_db=0, y_bottom_db=-40, y_convention="magnitude")
        self.assertTrue(self.bridge.apply_image_recipe(0, recipe)["ok"])
        self.saved = self.bridge.image_edit_recipe(0)["recipe"]
        self.api.set_network_ports(0, 2)
        source = next(value for value in self.api.get_defaults()["datasheet"]["networks"][0]["mapping_options"]["S21"] if value.startswith("图1 A"))
        for parameter, value in (("S11", "匹配 0"), ("S22", "匹配 0"), ("S21", source)):
            self.assertTrue(self.api.set_mapping(0, parameter, value)["ok"])
        self.review = self.bridge.preview_image_export(0)
        self.assertTrue(self.review["ok"], self.review)
        self.assertTrue(self.bridge.confirm_image_export(0, self.review["token"])["ok"])

    def test_live_axis_seeds_recipe_after_frequency_change_without_digitize(self):
        self.assertTrue(self.api.set_image_frequency(0, "2GHz", "4GHz", "20MHz")["ok"])
        recipe = self.bridge.image_edit_recipe(0)["recipe"]
        self.assertEqual(recipe["axis"]["start_hz"], 2e9)
        self.assertEqual(recipe["axis"]["stop_hz"], 4e9)
        self.assertEqual(recipe["axis"]["y_bottom_db"], -40)
        applied = self.bridge.apply_image_recipe(0, recipe)
        self.assertTrue(applied["ok"], applied)
        self.assertEqual(applied["image_update"]["axis"]["start_hz"], 2e9)
        self.assertEqual(applied["image_update"]["axis"]["stop_hz"], 4e9)
        self.assertFalse(self.bridge.confirm_image_export(0, self.review["token"])["ok"])

    def test_pending_positive_loss_and_dc_axis_are_read_only_until_apply(self):
        before = self.api.get_defaults()["datasheet"]
        form = {"start": "0", "stop": "4", "step": ".02", "spacing": "linear",
                "y_top_db": "0", "y_bottom_db": "60", "y_convention": "positive-loss"}
        opened = self.bridge.image_edit_recipe(0, form)
        self.assertTrue(opened["ok"], opened)
        axis = opened["recipe"]["axis"]
        self.assertEqual((axis["start_hz"], axis["stop_hz"], axis["step_hz"]), (0, 4e9, 20e6))
        self.assertEqual((axis["y_min_db"], axis["y_max_db"]), (-60, 0))
        self.assertEqual(self.api.get_defaults()["datasheet"], before)
        self.assertEqual(self.bridge.preview_image_export(0)["token"], self.review["token"])
        applied = self.bridge.apply_image_recipe(0, opened["recipe"])
        self.assertTrue(applied["ok"], applied)
        self.assertEqual(applied["image_update"]["axis"]["y_convention"], "positive-loss")
        self.assertEqual(applied["image_update"]["axis"]["y_min_db"], -60)
        # 显式传回保存方案仍可恢复原 X/Y；普通打开编辑器不会隐式做此操作。
        restored = self.bridge.apply_image_recipe(0, self.saved)
        self.assertTrue(restored["ok"], restored)
        self.assertEqual(restored["image_update"]["axis"]["start_hz"], 1e9)
        self.assertEqual(restored["image_update"]["axis"]["y_min_db"], -40)
        self.assertEqual(restored["image_update"]["axis"]["y_convention"], "magnitude")

    def test_invalid_axes_preserve_last_good_data_and_review(self):
        before = self.api.get_defaults()["datasheet"]
        for changes in ({"start": ""}, {"y_top_db": ""}, {"y_bottom_db": "nan"},
                        {"spacing": "log", "start": "0"},
                        {"y_convention": "positive-loss", "y_top_db": 0, "y_bottom_db": -40}):
            with self.subTest(changes=changes):
                axis = {**self.saved["axis"], **changes}
                self.assertFalse(self.bridge.image_edit_recipe(0, axis)["ok"])
                invalid = copy.deepcopy(self.saved)
                invalid["axis"] = axis
                self.assertFalse(self.bridge.apply_image_recipe(0, invalid)["ok"])
                self.assertEqual(self.api.get_defaults()["datasheet"], before)
                self.assertEqual(self.bridge.preview_image_export(0)["token"], self.review["token"])
        log_axis = {**self.saved["axis"], "start": "2", "stop": "4", "step": ".02", "spacing": "log"}
        checked = self.bridge.image_edit_recipe(0, log_axis)
        self.assertTrue(checked["ok"], checked)
        self.assertEqual(checked["recipe"]["axis"]["start_hz"], 2e9)
        self.assertEqual(checked["recipe"]["axis"]["spacing"], "log")


class ImageFidelityPublicWorkflowTests(unittest.TestCase):
    def test_narrow_notch_export_and_stale_review_through_public_api(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path = folder / "narrow notch.png"
            write_notch_image(path)
            api = InsertionLossWebApi()
            self.assertTrue(api.register_images([path])["ok"])
            self.assertTrue(api.set_image_frequency(0, "0", "18GHz", "100MHz")["ok"])
            result = api.digitize_image(0, -60, 0)
            self.assertTrue(result["ok"], result)
            curve = result["image_update"]["curves"][0]
            original_pixels = np.array(curve["source_pixel_points"])
            preview = np.array(curve["preview_points"])
            self.assertEqual(preview[:, 1].max(), original_pixels[:, 1].max())
            self.assertLessEqual(len(preview), 800)
            self.assertTrue(api.set_network_ports(0, 2)["ok"])
            choices = api.get_defaults()["datasheet"]["networks"][0]["mapping_options"]["S21"]
            source = next(value for value in choices if value.startswith("图1 A ·"))
            for parameter, value in (("S11", "匹配 0"), ("S22", "匹配 0"), ("S21", source)):
                self.assertTrue(api.set_mapping(0, parameter, value)["ok"])
            with patch("insertion_loss_tool.webview_gui.OUTPUT_DIR", folder / "exports"):
                # 一键更细步进也必须适用于 Common Range 从 DC 开始，不能暗改起点。
                common = api.get_defaults()["datasheet"]["networks"][0]["coverage"]
                self.assertEqual(common["start_hz"], 0)
                dc_review = api.preview_image_export(0)
                self.assertTrue(api.confirm_image_export(0, dc_review["token"])["ok"])
                dc_finer = api.set_network_frequency_policy(
                    0, "manual", "0Hz", "18GHz", f"{common['suggested_step_hz']}Hz", False)
                self.assertTrue(dc_finer["ok"], dc_finer)
                self.assertEqual(dc_finer["network"]["coverage"]["start_hz"], 0)
                self.assertEqual(dc_finer["network"]["coverage"]["points"], 1801)
                self.assertFalse(api.confirm_image_export(0, dc_review["token"])["ok"])
                self.assertFalse(api.generate_datasheet_network(0)["ok"])
                coarse = api.set_network_frequency_policy(0, "manual", "100MHz", "18GHz", "100MHz", False)
                self.assertTrue(coarse["ok"], coarse)
                coverage = coarse["network"]["coverage"]
                self.assertEqual(coverage["step_hz"], 100e6)
                self.assertEqual(coverage["suggested_step_hz"], 10e6)
                self.assertTrue(any("output sampling" in text for text in coverage["sampling_warnings"]))
                review = api.preview_image_export(0)
                check = review["record"]["sources"][0]["sampling_check"]
                self.assertGreater(check["changed_extrema_count"], 0)
                self.assertGreater(check["output_minimum_db"] - check["source_minimum_db"], 5)
                self.assertFalse(api.generate_datasheet_network(0)["ok"])
                self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
                generated = api.generate_datasheet_network(0)
                self.assertTrue(generated["ok"], generated)
                f_coarse, db_coarse = read_s21_ri(generated["output"])
                np.testing.assert_array_equal(np.diff(f_coarse), np.full(len(f_coarse) - 1, 100e6))
                self.assertAlmostEqual(db_coarse.min(), check["output_minimum_db"], places=7)
                # 显式改用更细网格：旧确认必须失效，不能生成或接受旧摘要。
                self.assertTrue(api.set_network_frequency_policy(0, "manual", "100MHz", "18GHz", "10MHz", False)["ok"])
                self.assertFalse(api.confirm_image_export(0, review["token"])["ok"])
                self.assertFalse(api.generate_datasheet_network(0)["ok"])
                self.assertEqual(len(list((folder / "exports").glob("*.s2p"))), 1)
                fine_review = api.preview_image_export(0)
                self.assertNotEqual(fine_review["token"], review["token"])
                self.assertEqual(fine_review["record"]["sources"][0]["sampling_check"]["status"], "sampled-agreement")
                self.assertTrue(api.confirm_image_export(0, fine_review["token"])["ok"])
                fine = api.generate_datasheet_network(0)
                self.assertTrue(fine["ok"], fine)
                f_fine, db_fine = read_s21_ri(fine["output"])
                np.testing.assert_array_equal(np.diff(f_fine), np.full(len(f_fine) - 1, 10e6))
                self.assertAlmostEqual(db_fine.min(), check["source_minimum_db"], places=7)
                self.assertGreater(db_coarse.min() - db_fine.min(), 5)


if __name__ == "__main__":
    unittest.main()
