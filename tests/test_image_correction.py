"""从像素与已知数学曲线验证人工修正，独立于生产颜色聚类。"""

# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np
# Codex说明(自动生成)： 从 PIL 导入 Image, ImageDraw，提供本文件后续流程需要的库能力。
from PIL import Image, ImageDraw
# Codex说明(自动生成)： 从 insertion_loss_tool.datasheet_digitizer 导入 digitize_plot_image，提供本文件后续流程需要的库能力。
from insertion_loss_tool.datasheet_digitizer import digitize_plot_image


# Codex说明(自动生成)： 定义 ImageCorrectionTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class ImageCorrectionTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_manual_box_and_anchors_recover_gridless_trace，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_manual_box_and_anchors_recover_gridless_trace(self):
        # 无网格双线图必须允许人工框选，并用锚点明确选择其中一条。
        with tempfile.TemporaryDirectory() as directory:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(directory) / "gridless.png"
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Image.new("RGB", (240, 180), "white")
            # Codex说明(自动生成)： 计算并保存 draw，供后续语句继续读取或更新。
            draw = ImageDraw.Draw(image)
            # Codex说明(自动生成)： 调用 draw.line，执行当前流程需要的具体操作或副作用。
            draw.line([(20, 70), (220, 110)], fill=(70, 120, 180), width=2)
            # Codex说明(自动生成)： 调用 draw.line，执行当前流程需要的具体操作或副作用。
            draw.line([(20, 110), (220, 70)], fill=(70, 120, 180), width=2)
            # Codex说明(自动生成)： 调用 image.save，执行当前流程需要的具体操作或副作用。
            image.save(path)
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = digitize_plot_image(
                path,
                start_hz=1e9,
                stop_hz=3e9,
                y_min_db=-40,
                y_max_db=0,
                run_ocr=False,
                plot_box_override=(20, 20, 220, 160),
                trace_specs=[
                    {
                        "id": "rx",
                        "label": "Rx RL",
                        "rgb": [70, 120, 180],
                        "anchors": [[20, 70], [80, 82], [160, 98], [220, 110]],
                    }
                ],
            )
            # Codex说明(自动生成)： 计算并保存 curve，供后续语句继续读取或更新。
            curve = result.curves[0]
            # Codex说明(自动生成)： 计算并保存 expected，供后续语句继续读取或更新。
            expected = 70 + (curve.pixel_points[:, 0] - 20) * 0.2
            # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
            self.assertLessEqual(
                float(np.max(abs(curve.pixel_points[:, 1] - expected))), 2
            )
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(len(result.curves), 1)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("manual_anchor", curve.sample_provenance)

    # Codex说明(自动生成)： 定义函数 test_manual_box_cannot_escape_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_manual_box_cannot_escape_image(self):
        # 越界和退化矩形应主动拒绝，不允许 NumPy 负索引静默选择其他区域。
        with tempfile.TemporaryDirectory() as directory:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(directory) / "image.png"
            # Codex说明(自动生成)： 调用 Image.new('RGB', (100, 100), 'white').save，执行当前流程需要的具体操作或副作用。
            Image.new("RGB", (100, 100), "white").save(path)
            # Codex说明(自动生成)： 进入上下文 self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaises(ValueError):
                # Codex说明(自动生成)： 调用 digitize_plot_image 生成或展示图形，便于观察计算结果。
                digitize_plot_image(
                    path,
                    start_hz=1,
                    stop_hz=2,
                    y_min_db=-40,
                    y_max_db=0,
                    run_ocr=False,
                    plot_box_override=(-10, 0, 80, 90),
                )


# Codex说明(自动生成)： 定义 WorkspaceCorrectionTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class WorkspaceCorrectionTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_recipe_undo_confirmation_and_metadata，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_recipe_undo_confirmation_and_metadata(self):
        # 通过真实 API 修复无网格图，验证保存方案、局部数据、撤销与复核版本。
        from insertion_loss_tool.webview_gui import (
            InsertionLossWebApi,
            InsertionLossJsApi,
        )
        # Codex说明(自动生成)： 从 unittest.mock 导入 patch，组织单元测试和断言。
        from unittest.mock import patch
        # Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
        import json

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as directory:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(directory)
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = folder / "curve.png"
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Image.new("RGB", (240, 180), "white")
            # Codex说明(自动生成)： 计算并保存 draw，供后续语句继续读取或更新。
            draw = ImageDraw.Draw(image)
            # Codex说明(自动生成)： 调用 draw.line，执行当前流程需要的具体操作或副作用。
            draw.line([(20, 70), (220, 110)], fill=(70, 120, 180), width=2)
            # Codex说明(自动生成)： 调用 image.save，执行当前流程需要的具体操作或副作用。
            image.save(path)
            # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
            api = InsertionLossWebApi()
            # Codex说明(自动生成)： 计算并保存 bridge，供后续语句继续读取或更新。
            bridge = InsertionLossJsApi(api)
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([path])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "3GHz", "0.01GHz")
            # Codex说明(自动生成)： 计算并保存 recipe，供后续语句继续读取或更新。
            recipe = bridge.image_edit_recipe(0)["recipe"]
            # Codex说明(自动生成)： 调用 recipe.update，执行当前流程需要的具体操作或副作用。
            recipe.update(
                plot_box=[20, 20, 220, 160],
                traces=[
                    {
                        "id": "rx-rl",
                        "label": "Rx RL",
                        "rgb": [70, 120, 180],
                        "anchors": [[20, 70], [220, 110]],
                    }
                ],
            )
            # Codex说明(自动生成)： 调用 recipe['axis'].update，执行当前流程需要的具体操作或副作用。
            recipe["axis"].update(y_top_db=0, y_bottom_db=-40, y_convention="magnitude")
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = bridge.apply_image_recipe(0, recipe)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(result["ok"], result)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(result["image_update"]["curves"][0]["identity"], "rx-rl")
            # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
            api.set_network_ports(0, 2)
            # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
            api.set_network_reciprocal(0, False)

            # Codex说明(自动生成)： 定义函数 map_curve，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
            def map_curve():
                # Codex说明(自动生成)： 计算并保存 options，供后续语句继续读取或更新。
                options = api.get_defaults()["datasheet"]["networks"][0][
                    "mapping_options"
                ]["S11"]
                # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
                source = next(x for x in options if x.startswith("图1 A"))
                # Codex说明(自动生成)： 遍历 ('S11', 'S12', 'S21', 'S22') 中的 p，逐项执行循环体逻辑。
                for p in ("S11", "S12", "S21", "S22"):
                    # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
                    api.set_mapping(0, p, source if p == "S11" else "匹配 0")

            # Codex说明(自动生成)： 调用 map_curve，执行当前流程需要的具体操作或副作用。
            map_curve()
            # Codex说明(自动生成)： 计算并保存 preview，供后续语句继续读取或更新。
            preview = bridge.preview_image_export(0)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(preview["ok"], preview)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(bridge.confirm_image_export(0, preview["token"])["ok"])
            # Codex说明(自动生成)： 进入上下文 patch('insertion_loss_tool.webview_gui.OUTPUT_DIR', fol...，确保文件、资源或临时状态按作用域正确释放。
            with patch(
                "insertion_loss_tool.webview_gui.OUTPUT_DIR", folder / "exports"
            ):
                # Codex说明(自动生成)： 计算并保存 generated，供后续语句继续读取或更新。
                generated = bridge.generate_datasheet_network(0)
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(generated["ok"], generated)
                # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
                # 元数据中的中文使用 JSON 转义，保持 Touchstone 文件为 ASCII。
                self.assertTrue(Path(generated["output"]).read_bytes().isascii())
                text = Path(generated["output"]).read_text()
                # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                self.assertIn("phase_assumption", text)
                # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                self.assertIn("source_sha256", text)
                # Codex说明(自动生成)： 计算并保存 csv，供后续语句继续读取或更新。
                csv = bridge.export_image_asset(0, "csv")
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(csv["ok"], csv)
                # 将图框内 RGB 转为浮点，避免无符号像素减法溢出。
                values = np.loadtxt(
                    csv["output"], delimiter=",", skiprows=2, usecols=(2, 3)
                )
                # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
                np.testing.assert_allclose(
                    values[:, 1],
                    -40 * (70 + 0.2 * ((values[:, 0] - 1e9) / 1e7) - 20) / 140,
                    atol=0.3,
                )
                # Codex说明(自动生成)： 计算并保存 saved，供后续语句继续读取或更新。
                saved = bridge.export_image_asset(0, "recipe")
                # Codex说明(自动生成)： 计算并保存 frozen，供后续语句继续读取或更新。
                frozen = json.loads(Path(saved["output"]).read_text())
            # 编辑器增加一个锚点，旧确认失效；失败事务必须保持旧曲线。
            bad = dict(frozen, plot_box=[-1, 0, 50, 70])
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(bridge.apply_image_recipe(0, bad)["ok"])
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(bridge.preview_image_export(0)["token"], preview["token"])
            # Codex说明(自动生成)： 调用 frozen['traces'][0]['anchors'].insert 更新列表或集合，把当前步骤产生的数据加入结果。
            frozen["traces"][0]["anchors"].insert(1, [100, 95])
            # Codex说明(自动生成)： 计算并保存 changed，供后续语句继续读取或更新。
            changed = bridge.apply_image_recipe(0, frozen)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(changed["ok"], changed)
            # Codex说明(自动生成)： 调用 map_curve，执行当前流程需要的具体操作或副作用。
            map_curve()
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(bridge.confirm_image_export(0, preview["token"])["ok"])
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(bridge.generate_datasheet_network(0)["ok"])
            # Codex说明(自动生成)： 计算并保存 undone，供后续语句继续读取或更新。
            undone = bridge.undo_image_recipe(0)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(undone["ok"], undone)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(
                undone["image_update"]["edit_recipe"]["traces"][0]["anchors"],
                [[20, 70], [220, 110]],
            )


# Codex说明(自动生成)： 定义 ReviewTransactionBoundaries 类，把相关数据结构、校验规则或操作方法组织在一起。
class ReviewTransactionBoundaries(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_malformed_recipe_is_atomic_and_calibration_is_saved，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_malformed_recipe_is_atomic_and_calibration_is_saved(self):
        # Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
        from insertion_loss_tool.webview_gui import InsertionLossWebApi
        # Codex说明(自动生成)： 导入 copy，提供本文件后续流程需要的库能力。
        import copy

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as directory:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(directory) / "curve.png"
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Image.new("RGB", (100, 100), "white")
            # Codex说明(自动生成)： 调用 ImageDraw.Draw(image).line，执行当前流程需要的具体操作或副作用。
            ImageDraw.Draw(image).line(
                [(10, 40), (90, 60)], fill=(60, 110, 180), width=2
            )
            # Codex说明(自动生成)： 调用 image.save，执行当前流程需要的具体操作或副作用。
            image.save(path)
            # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
            api = InsertionLossWebApi()
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([path])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "0.01GHz")
            # Codex说明(自动生成)： 计算并保存 recipe，供后续语句继续读取或更新。
            recipe = api.image_edit_recipe(0)["recipe"]
            # Codex说明(自动生成)： 调用 recipe.update，执行当前流程需要的具体操作或副作用。
            recipe.update(
                plot_box=[10, 10, 90, 90],
                traces=[
                    {"id": "one", "label": "RL", "rgb": [60, 110, 180], "anchors": []}
                ],
            )
            # Codex说明(自动生成)： 调用 recipe['axis'].update，执行当前流程需要的具体操作或副作用。
            recipe["axis"].update(y_top_db=0, y_bottom_db=-40)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.apply_image_recipe(0, recipe)["ok"])
            # Codex说明(自动生成)： 计算并保存 before，供后续语句继续读取或更新。
            before = api.get_defaults()["datasheet"]
            # Codex说明(自动生成)： 遍历 ({'axis': None}, {'axis': {}}, {'axis': {'start': float... 中的 change，逐项执行循环体逻辑。
            for change in (
                {"axis": None},
                {"axis": {}},
                {"axis": {"start": float("nan")}},
                {"traces": [{"id": "bad", "rgb": [999, 0, 0]}]},
            ):
                # Codex说明(自动生成)： 进入上下文 self.subTest(change=change)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(change=change):
                    # Codex说明(自动生成)： 计算并保存 malformed，供后续语句继续读取或更新。
                    malformed = copy.deepcopy(recipe)
                    # Codex说明(自动生成)： 调用 malformed.update，执行当前流程需要的具体操作或副作用。
                    malformed.update(change)
                    # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
                    self.assertFalse(api.apply_image_recipe(0, malformed)["ok"])
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(api.get_defaults()["datasheet"], before)
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "2GHz", "4GHz", "0.02GHz")
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.digitize_image_with_axis(0, 0, -30, "magnitude")["ok"])
            # Codex说明(自动生成)： 计算并保存 saved，供后续语句继续读取或更新。
            saved = api.image_edit_recipe(0)["recipe"]["axis"]
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(saved["start_hz"], 2e9)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(saved["y_bottom_db"], -30)
            # Codex说明(自动生成)： 遍历 [-1, True, 'x', 100] 中的 index，逐项执行循环体逻辑。
            for index in [-1, True, "x", 100]:
                # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
                self.assertFalse(api.export_image_asset(index, "csv")["ok"])

    # Codex说明(自动生成)： 定义函数 test_model_changes_revoke_confirmation_and_delay_is_explicit，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_model_changes_revoke_confirmation_and_delay_is_explicit(self):
        # Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
        from insertion_loss_tool.webview_gui import InsertionLossWebApi
        # Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 read_touchstone，提供本文件后续流程需要的库能力。
        from insertion_loss_tool.touchstone import read_touchstone
        # Codex说明(自动生成)： 从 unittest.mock 导入 patch，组织单元测试和断言。
        from unittest.mock import patch

        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_frequency_policy，执行当前流程需要的具体操作或副作用。
        api.set_network_frequency_policy(0, "manual", "1GHz", "2GHz", "0.25GHz", False)
        # Codex说明(自动生成)： 计算并保存 preview，供后续语句继续读取或更新。
        preview = api.preview_image_export(0)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(preview["ok"], preview)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.generate_datasheet_network(0)["ok"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(api.confirm_image_export(0, preview["token"])["ok"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(api.set_image_network_model(0, "delay", 0.125, 75)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.generate_datasheet_network(0)["ok"])
        # Codex说明(自动生成)： 计算并保存 updated，供后续语句继续读取或更新。
        updated = api.preview_image_export(0)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(api.confirm_image_export(0, updated["token"])["ok"])
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory(), patch('insertion_loss_tool.webview_gui.OUTPUT_DIR', Pat...，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as directory, patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(directory)
        ):
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = api.generate_datasheet_network(0)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(result["ok"], result)
            # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
            data = read_touchstone(result["output"])
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(data.z0, 75)
            # 用独立 sin/cos 公式核对复数方向，避免角度分支绕回影响比较。
            f = data.frequency_hz
            # Codex说明(自动生成)： 计算并保存 expected，供后续语句继续读取或更新。
            expected = np.cos(2 * np.pi * f * 0.125e-9) - 1j * np.sin(
                2 * np.pi * f * 0.125e-9
            )
            # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
            np.testing.assert_allclose(
                data.s[:, 0, 0] / abs(data.s[:, 0, 0]), expected, atol=1e-10
            )
        # Codex说明(自动生成)： 遍历 [('unknown', 0, 50), ('delay', -1, 50), ('delay', 0, 0)... 中的 model，逐项执行循环体逻辑。
        for model in [
            ("unknown", 0, 50),
            ("delay", -1, 50),
            ("delay", 0, 0),
            ("delay", float("inf"), 50),
        ]:
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(api.set_image_network_model(0, *model)["ok"])
