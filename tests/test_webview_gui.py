# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 builtins，提供本文件后续流程需要的库能力。
import builtins
# Codex说明(自动生成)： 导入 inspect，提供本文件后续流程需要的库能力。
import inspect
# Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
import json
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 threading，提供本文件后续流程需要的库能力。
import threading
# Codex说明(自动生成)： 导入 time，提供本文件后续流程需要的库能力。
import time
# Codex说明(自动生成)： 导入 tomllib，提供本文件后续流程需要的库能力。
import tomllib
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 从 unittest 导入 mock，组织单元测试和断言。
from unittest import mock

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np

# Codex说明(自动生成)： 从 insertion_loss_tool.datasheet_digitizer 导入 AxisCalibration, DigitizationResult, DigitizedCurve, ImageAnalysis，提供本文件后续流程需要的库能力。
from insertion_loss_tool.datasheet_digitizer import (
    AxisCalibration,
    CurveReviewRegion,
    DigitizationResult,
    DigitizedCurve,
    ImageAnalysis,
)
# Codex说明(自动生成)： 从 insertion_loss_tool.datasheet_workspace 导入 DatasheetWorkspace，提供本文件后续流程需要的库能力。
from insertion_loss_tool.datasheet_workspace import DatasheetWorkspace
# Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 TouchstoneData, read_touchstone, to_magnitude_db, write_touchstone，提供本文件后续流程需要的库能力。
from insertion_loss_tool.touchstone import (
    TouchstoneData,
    read_touchstone,
    to_magnitude_db,
    write_touchstone,
)
# Codex说明(自动生成)： 导入 insertion_loss_tool，提供本文件后续流程需要的库能力。
import insertion_loss_tool
# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossJsApi, InsertionLossWebApi, load_web_ui, run_smoke_test 等名称，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import (
    InsertionLossJsApi,
    InsertionLossWebApi,
    load_web_ui,
    run_smoke_test,
    select_webview_backend,
    validate_renderer_probe,
    validate_web_ui_contract,
)


# Codex说明(自动生成)： 定义 WebviewGuiTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class WebviewGuiTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 _stub_digitization，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _stub_digitization(*_args: object, **kwargs: object) -> DigitizationResult:
        # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
        points = int(kwargs.pop("_points", 5))
        # 把原图水平像素位置映射到线性或对数频率，单位 Hz。
        frequency = np.linspace(
            float(kwargs["start_hz"]), float(kwargs["stop_hz"]), points
        )

        # Codex说明(自动生成)： 返回 DigitizationResult(image_width=100, image_height=80, pl...，让调用方取得本函数的处理结果。
        return DigitizationResult(
            image_width=100,
            image_height=80,
            plot_box=(10, 10, 90, 70),
            curves=(
                DigitizedCurve(
                    color="Dark blue",
                    rgb=(36, 76, 206),
                    frequency_hz=frequency,
                    magnitude_db=np.linspace(-1.0, -4.0, points),
                    pixel_points=np.column_stack(
                        (np.linspace(10, 90, points), np.linspace(20, 50, points))
                    ),
                    confidence=0.9,
                ),
            ),
        )

    def test_digitization_payload_exposes_local_visual_review_regions(self) -> None:
        """The GUI receives exact source-pixel intervals, not only one score."""

        api = InsertionLossWebApi()
        frequency = np.linspace(1e9, 5e9, 9)
        detected = DigitizationResult(
            image_width=100,
            image_height=80,
            plot_box=(10, 10, 90, 70),
            curves=(
                DigitizedCurve(
                    color="Dark blue",
                    rgb=(36, 76, 206),
                    frequency_hz=frequency,
                    magnitude_db=np.linspace(-1.0, -4.0, 9),
                    pixel_points=np.column_stack(
                        (np.linspace(10, 90, 9), np.linspace(20, 50, 9))
                    ),
                    confidence=0.9,
                    visual_confidence=0.72,
                    review_status="review",
                    review_regions=(
                        CurveReviewRegion(
                            start_x=38.0,
                            end_x=52.0,
                            reason="raster_gap",
                            severity="medium",
                            samples=3,
                        ),
                    ),
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "review-region.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            api.set_image_frequency(0, "1GHz", "5GHz", "0.5GHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                response = api.digitize_image(0, -10, 0)

        self.assertTrue(response["ok"], response)
        curve = response["image_update"]["curves"][0]
        self.assertEqual(curve["review_status"], "review")
        self.assertEqual(curve["visual_confidence"], 0.72)
        self.assertEqual(curve["review_regions"][0]["reason"], "raster_gap")
        self.assertGreaterEqual(len(curve["review_regions"][0]["preview_points"]), 2)

    # Codex说明(自动生成)： 定义函数 test_preserved_visual_probe_exposes_the_escaped_regressions，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_preserved_visual_probe_exposes_the_escaped_regressions(self) -> None:
        # Codex说明(自动生成)： 计算并保存 validation_dir，供后续语句继续读取或更新。
        validation_dir = Path(__file__).with_name("validation")
        # Codex说明(自动生成)： 计算并保存 red，供后续语句继续读取或更新。
        red = json.loads(
            (validation_dir / "webview_visual_red_probe.json").read_text(encoding="utf-8")
        )
        # Codex说明(自动生成)： 计算并保存 green，供后续语句继续读取或更新。
        green = json.loads(
            (validation_dir / "webview_visual_green_probe.json").read_text(
                encoding="utf-8"
            )
        )

        # Codex说明(自动生成)： 计算并保存 failures，供后续语句继续读取或更新。
        failures = red["observed_failures"]
        # Codex说明(自动生成)： 计算并保存 requirements，供后续语句继续读取或更新。
        requirements = red["required_behavior"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(failures["draw_board_css_height"], 110)
        # Codex说明(自动生成)： 调用 self.assertLess 检查测试期望，确认实际结果符合预期。
        self.assertLess(
            failures["responsive_draw_board_width"],
            requirements["draw_board_min_width"],
        )
        # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
        self.assertNotEqual(
            failures["draw_top_left_click_token"],
            requirements["draw_top_left_click_token"],
        )
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(
            green["responsiveDrawBoardWidth"], requirements["draw_board_min_width"]
        )
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(
            green["responsiveDrawBoardHeight"], requirements["draw_board_min_height"]
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            green["drawClickToken"], requirements["draw_top_left_click_token"]
        )
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(green["responsiveMaxOutputAccessible"])

    # Codex说明(自动生成)： 定义函数 test_generator_and_datasheet_share_common_port_choices，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_generator_and_datasheet_share_common_port_choices(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 html，供后续语句继续读取或更新。
        html = load_web_ui()

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(api.get_defaults()["port_options"], [2, 3, 4, 6, 8])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(html.count("data-common-ports"), 2)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("defaults.port_options", html)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("for(let port=1;port<=8;port++)", html)

    # Codex说明(自动生成)： 定义函数 test_datasheet_defaults_to_one_output_network_and_can_expand，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_defaults_to_one_output_network_and_can_expand(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 html，供后续语句继续读取或更新。
        html = load_web_ui()

        # Codex说明(自动生成)： 计算并保存 networks，供后续语句继续读取或更新。
        networks = api.get_defaults()["datasheet"]["networks"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(networks), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(networks[0]["output"], "output_1.s4p")
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'id="network-count" type="number" min="1" max="6" value="1"',
            html,
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(api.set_network_count(3)["networks"]), 3)

    # Codex说明(自动生成)： 定义函数 test_web_generator_writes_every_common_port_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_web_generator_writes_every_common_port_count(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(temp_dir)
            # Codex说明(自动生成)： 遍历 (2, 3, 4, 6, 8) 中的 ports，逐项执行循环体逻辑。
            for ports in (2, 3, 4, 6, 8):
                # Codex说明(自动生成)： 进入上下文 self.subTest(ports=ports)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(ports=ports):
                    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                    output = folder / f"common.s{ports}p"
                    # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                    response = api.run_generation_sync(
                        {
                            "mode": "linear",
                            "ports": str(ports),
                            "f_start": "1GHz",
                            "f_stop": "2GHz",
                            "points": "5",
                            "spacing": "linear",
                            "format": "ri",
                            "frequency_unit": "ghz",
                            "return_loss_db": "20",
                            "crosstalk_db": "80",
                            "delay_ps": "25",
                            "phase_offset_deg": "0",
                            "z0": "50",
                            "through_pairs": "",
                            "loss_start_db": "1",
                            "loss_stop_db": "4",
                            "output": str(output),
                        }
                    )
                    # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                    self.assertTrue(response["ok"], response)
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(len(response["plot"]["series"]), ports * ports)
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(read_touchstone(output).n_ports, ports)

    # Codex说明(自动生成)： 定义函数 test_web_generator_rejects_a_non_common_port_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_web_generator_rejects_a_non_common_port_count(self) -> None:
        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = InsertionLossWebApi().run_generation_sync(
            {
                "mode": "linear",
                "ports": "5",
                "f_start": "1GHz",
                "f_stop": "2GHz",
                "points": "5",
                "loss_start_db": "1",
                "loss_stop_db": "4",
            }
        )

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("2、3、4、6、8", response["error"])

    # Codex说明(自动生成)： 定义函数 test_modify_input_inspection_returns_source_metadata_and_preview，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_input_inspection_returns_source_metadata_and_preview(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
            source = Path(temp_dir) / "source.s4p"
            # Codex说明(自动生成)： 计算并保存 generated，供后续语句继续读取或更新。
            generated = api.run_generation_sync(
                {
                    "mode": "linear",
                    "ports": "4",
                    "f_start": "10MHz",
                    "f_stop": "40GHz",
                    "points": "811",
                    "loss_start_db": "0.2",
                    "loss_stop_db": "20",
                    "output": str(source),
                }
            )
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(generated["ok"], generated)

            # Codex说明(自动生成)： 计算并保存 inspected，供后续语句继续读取或更新。
            inspected = api.inspect_input(source, "ghz")

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(inspected["ok"], inspected)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["name"], "source.s4p")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["ports"], 4)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["points"], 811)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["start_hz"], 10e6)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["stop_hz"], 40e9)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(inspected["plot"]["unit"], "GHz")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(inspected["plot"]["series"]), 16)

    # Codex说明(自动生成)： 定义函数 test_default_modify_configuration_writes_a_sampled_passive_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_default_modify_configuration_writes_a_sampled_passive_network(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 defaults，供后续语句继续读取或更新。
        defaults = api.get_defaults()
        # Codex说明(自动生成)： 计算并保存 modify，供后续语句继续读取或更新。
        modify = defaults["modify"]

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = Path(temp_dir) / "default-modified.s2p"
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.run_generation_sync(
                {
                    "mode": "modify",
                    "input": modify["input"],
                    "targets": modify["targets"],
                    "pairs": modify["pairs"],
                    "smoothness": modify["smoothness"],
                    "smooth_domain": modify["smooth_domain"],
                    "anchor_edges": modify["anchor_edges"],
                    "insert_targets": modify["insert_targets"],
                    "format": defaults["format"],
                    "frequency_unit": defaults["frequency_unit"],
                    "output": str(output),
                }
            )

            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(response["ok"], response)
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(output)
            # Codex说明(自动生成)： 计算并保存 singular_values，供后续语句继续读取或更新。
            singular_values = np.linalg.svd(loaded.s, compute_uv=False)
            # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
            self.assertLessEqual(float(np.max(singular_values)), 1.0 + 1.0e-9)
            # Codex说明(自动生成)： 遍历 ((5000000000.0, 3.0), (12000000000.0, 8.0)) 中的 (frequency_hz, expected_loss_db)，逐项执行循环体逻辑。
            for frequency_hz, expected_loss_db in ((5.0e9, 3.0), (12.0e9, 8.0)):
                # Codex说明(自动生成)： 计算并保存 index，供后续语句继续读取或更新。
                index = int(np.where(np.isclose(loaded.frequency_hz, frequency_hz))[0][0])
                # Codex说明(自动生成)： 遍历 ((1, 0), (0, 1)) 中的 (out_port, in_port)，逐项执行循环体逻辑。
                for out_port, in_port in ((1, 0), (0, 1)):
                    # Codex说明(自动生成)： 计算并保存 achieved，供后续语句继续读取或更新。
                    achieved = -to_magnitude_db(loaded.s[index, out_port, in_port])
                    # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
                    self.assertAlmostEqual(float(achieved), expected_loss_db, places=6)

    # Codex说明(自动生成)： 定义函数 test_web_modify_attributes_a_nonpassive_source_before_targets，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_web_modify_attributes_a_nonpassive_source_before_targets(self) -> None:
        # 同相 0.6 常数矩阵的最大奇异值为 1.2，是可手算的非无源文件样本。
        frequency = np.array([1.0e9, 2.0e9])
        # 两个频点使用同一矩阵，排除频率插值对错误归因的影响。
        matrix = np.full((2, 2, 2), 0.6 + 0.0j, dtype=complex)

        # 通过真实 Touchstone 文件和 Web API 边界复现用户能看到的错误消息。
        with tempfile.TemporaryDirectory() as temp_dir:
            # 输入和输出均放在隔离目录，失败路径不得留下半成品。
            source = Path(temp_dir) / "nonpassive.s2p"
            # 写出器只负责格式合同，因此允许保存用于负向验证的非无源矩阵。
            write_touchstone(TouchstoneData(frequency, matrix), source)
            # 使用保守目标，确保拒绝原因来自输入文件而不是目标功率预算。
            response = InsertionLossWebApi().run_generation_sync(
                {
                    "mode": "modify",
                    "input": str(source),
                    "targets": "1GHz:10.0",
                    "pairs": "S21,S12",
                    "output": str(Path(temp_dir) / "should-not-exist.s2p"),
                }
            )

        # GUI 后端必须明确指出 Input，不能继续显示模糊的 Modified/Resampled 错误。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Input S-parameter matrix is not passive", response["error"])
    # Codex说明(自动生成)： 定义函数 test_auto_name_creates_a_new_file_on_every_generation，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_auto_name_creates_a_new_file_on_every_generation(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 config，供后续语句继续读取或更新。
        config = {
            "mode": "linear",
            "ports": "2",
            "f_start": "1GHz",
            "f_stop": "2GHz",
            "points": "5",
            "spacing": "linear",
            "format": "ri",
            "frequency_unit": "ghz",
            "return_loss_db": "20",
            "crosstalk_db": "80",
            "delay_ps": "25",
            "phase_offset_deg": "0",
            "z0": "50",
            "through_pairs": "",
            "loss_start_db": "1",
            "loss_stop_db": "4",
            "output": "",
            "overwrite": False,
        }
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory(), mock.patch('insertion_loss_tool.webview_gui.OUTPUT_DIR'...，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(temp_dir)
        ):
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = api.run_generation_sync(config)
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = api.run_generation_sync(config)

            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(first["ok"], first)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(second["ok"], second)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(Path(first["output"]).name, "linear_web.s2p")
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(Path(second["output"]).name, "linear_web_001.s2p")
            # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
            self.assertNotEqual(first["output"], second["output"])
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(read_touchstone(first["output"]).n_ports, 2)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(read_touchstone(second["output"]).n_ports, 2)

    # Codex说明(自动生成)： 定义函数 test_web_ui_is_compact_and_has_one_image_action，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_web_ui_is_compact_and_has_one_image_action(self) -> None:
        # Codex说明(自动生成)： 计算并保存 html，供后续语句继续读取或更新。
        html = load_web_ui()

        # Codex说明(自动生成)： 遍历 ('Insertion Loss Tool', 'Generate and Modify S-Paramete... 中的 expected，逐项执行循环体逻辑。
        for expected in (
            "Insertion Loss Tool",
            "Generate and Modify S-Parameter",
            "Image to S-Parameter",
            "Linear",
            "Formula",
            "Draw",
            "Modify",
            "Digitize",
            "Reciprocal",
            ">Add</button>",
            "backdrop-filter: blur",
            "radial-gradient",
        ):
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn(expected, html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'data-tab="generator">Generate and Modify S-Parameter</button>', html
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'data-tab="datasheet">Image to S-Parameter</button>', html
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("detected labels are hints", html)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("Reciprocal (Sij = Sji)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="image-spacing"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("analyze_image",imageIndex)', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('family!=="mixed-mode" || port%2===0', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("grid-template-rows:auto auto auto minmax(0,1fr)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("engineeringTicks", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("state.plot.unit", html)
        # Codex说明(自动生成)： 遍历 (('ghz', 'GHz'), ('mhz', 'MHz'), ('khz', 'kHz'), ('hz',... 中的 (value, label)，逐项执行循环体逻辑。
        for value, label in (("ghz", "GHz"), ("mhz", "MHz"), ("khz", "kHz"), ("hz", "Hz")):
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn(f'<option value="{value}">{label}</option>', html)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(html.count('data-action="choose-images"'), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(html.count("window.pywebview.api["), 1)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("window.insertionLossBridgeCalls", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("escapeHtml(image.name)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("class=\"card panel asset-panel\"", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("class=\"card panel image-panel\"", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("grid-column:1/3", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="image-f-start"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="image-y-max"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="image-y-min"', html)
        self.assertIn('id="image-y-convention"', html)
        self.assertIn("Frequency values without units use GHz", html)
        self.assertIn('value="positive-loss"', html)
        self.assertNotIn('id="image-f-start" placeholder=', html)
        self.assertNotIn('id="image-f-stop" placeholder=', html)
        self.assertNotIn('id="image-f-step" placeholder=', html)
        self.assertIn(
            'callApi("digitize_image_with_axis",imageIndex,yTop,yBottom,value("#image-y-convention"))',
            html,
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="digitize-image"', html)
        self.assertIn('id="visual-review-help"', html)
        self.assertIn("Orange dashed areas need visual review", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('startsWith("detected")', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('"Required"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('"Manual"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="remove-image"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('class="card panel asset-panel"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("grid-template-columns:220px minmax(680px,1.6fr) minmax(390px,.72fr)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="mapping-hint"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("network.mapping_options", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("digitization?.detected_parameter", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('class="curve-swatch"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function displayCurveSource(source)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function curveLabel(curveId)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function traceProvenance(curve)", html)
        self.assertIn("function traceReview(curve)", html)
        self.assertIn("function curveUsage(image,curve)", html)
        self.assertNotIn('data-curve="${escapeHtml(curve.id)}"', html)
        self.assertIn('class="curve-usage"', html)
        self.assertIn('if(curve?.calibrated===false)', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("${total} grid", html)
        self.assertIn("${covered} covered", html)
        self.assertIn("${source} source", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("unresolved_samples", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("curveLabel(curve.id)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Detected Traces", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("traceSummary(image)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("displaySource(curve.color)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function highlightTrace(curveId, persist=false)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-overlay-trace="${escapeHtml(curve.id)}"', html)
        self.assertIn('data-overlay-review="${escapeHtml(curve.id)}"', html)
        self.assertIn("review_regions", html)
        self.assertIn("image accuracy not assessed", html)
        self.assertNotIn("heuristic score", html)
        self.assertIn("Review ${regions.length} highlighted", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-trace-row="${escapeHtml(curve.id)}"', html)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn('<b>${escapeHtml(curve.id)}</b>', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="network-family"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="frequency-policy"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="image-zoom"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="zoom-in"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="zoom-out"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="zoom-reset"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-plot-action="zoom"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-plot-action="pan"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-plot-action="reset"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function bindPlotInteractions()", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Phase (deg)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-draw-y-axis', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-draw-x-axis', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-x-unit', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Magnitude (dB)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="generate-network"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("callApi('generate_datasheet_network',pendingExport.index)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="open-image-output"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("open_datasheet_output_dir")', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('id="modify-input-status"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("inspect_input"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('loadModifyInput(response.path)', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('$("#modify-input").addEventListener("change"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function niceStep", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function niceAxis", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function engineeringTicks", html)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("function chartTicks", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function showGeneratedPlots", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function traceDisplayRgb", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('"自动":"Unassigned"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("function displayMessage(message)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("input.disabled=!image || state.digitizing", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('$("#add-images").disabled=!state.datasheet||state.digitizing||state.importing', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('state.importing ? "Selecting…"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('status.textContent="Opening image picker"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('status.textContent="Image selection cancelled"', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('status.textContent="Unable to import images. Try again."', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'for(const transient of ["images_added","image_update","image_removed","image_updates"])delete payload[transient]',
            html,
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('$("#remove-image").disabled=!image || state.digitizing', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("remove_image",imageIndex)', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("renderDatasheet(calibrated)", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("const imageIndex=state.selectedImage", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("set_image_frequency",imageIndex', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('callApi("digitize_image",imageIndex', html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('data-image="${index}" ${state.digitizing ? "disabled"', html)
        # Codex说明(自动生成)： 计算并保存 digitize_handler，供后续语句继续读取或更新。
        digitize_handler = html.split(
            '$("#digitize-image").addEventListener', 1
        )[1].split('const zoomDialog=', 1)[0]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(digitize_handler.count("state.selectedImage"), 1)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'file_types=("Images ', inspect.getsource(InsertionLossWebApi.choose_images)
        )
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("status.textContent=response.error", html)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("status.textContent=payload.error", html)
        # Codex说明(自动生成)： 遍历 ('常规生成', '图片组合', '协议公式', '成对联动', '添加图片', '互易网络', '导入图片'... 中的 forbidden，逐项执行循环体逻辑。
        for forbidden in (
            "常规生成",
            "图片组合",
            "协议公式",
            "成对联动",
            "添加图片",
            "互易网络",
            "导入图片",
            "＋ 图片",
            "家具组合",
            "线缆组合",
        ):
            # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
            self.assertNotIn(forbidden, html)
        # Codex说明(自动生成)： 调用 validate_web_ui_contract，执行当前流程需要的具体操作或副作用。
        validate_web_ui_contract(html)

    # Codex说明(自动生成)： 定义函数 test_image_workspace_generates_a_uniform_zero_phase_touchstone_file，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_workspace_generates_a_uniform_zero_phase_touchstone_file(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
        digitized = self._stub_digitization(start_hz=1e9, stop_hz=2e9)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(temp_dir)
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = folder / "s12.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "250MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=digitized,
            ):
                # Codex说明(自动生成)： 调用 api.digitize_image，执行当前流程需要的具体操作或副作用。
                api.digitize_image(0, -10, 0)
            # Codex说明(自动生成)： 调用 api.set_curve_parameter，执行当前流程需要的具体操作或副作用。
            api.set_curve_parameter(0, "A", "S12")
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S12", "图1 A · S12")

            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.OUTPUT_DIR'...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.webview_gui.OUTPUT_DIR", folder / "outputs"
            ):
                # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
                review = api.preview_image_export(0)
                self.assertTrue(review["ok"], review)
                self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
                first = api.generate_datasheet_network(0)
                # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
                second = api.generate_datasheet_network(0)

            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(first["ok"], first)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(second["ok"], second)
            # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
            self.assertNotEqual(first["output"], second["output"])
            # Codex说明(自动生成)： 计算并保存 generated，供后续语句继续读取或更新。
            generated = read_touchstone(first["output"])
            # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
            np.testing.assert_allclose(
                generated.frequency_hz,
                np.linspace(1e9, 2e9, 5),
                rtol=0,
                atol=1e-6,
            )
            # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
            np.testing.assert_allclose(
                to_magnitude_db(generated.s[:, 0, 1]),
                np.linspace(-1.0, -4.0, 5),
                rtol=0,
                atol=1e-9,
            )
            # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
            np.testing.assert_allclose(np.angle(generated.s), 0.0, rtol=0, atol=1e-12)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(first["phase_assumption"], "zero-degree")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.subprocess...., mock.patch('insertion_loss_tool.webview_gui.sys.platfor...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.webview_gui.subprocess.Popen"
            ) as launch, mock.patch(
                "insertion_loss_tool.webview_gui.sys.platform", "darwin"
            ):
                # Codex说明(自动生成)： 计算并保存 opened，供后续语句继续读取或更新。
                opened = api.open_datasheet_output_dir()
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(opened["ok"], opened)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(Path(opened["path"]), Path(first["output"]).parent)
            # Codex说明(自动生成)： 调用 launch.assert_called_once_with 检查测试期望，确认实际结果符合预期。
            launch.assert_called_once_with(["open", str(Path(first["output"]).parent)])

    # Codex说明(自动生成)： 定义函数 test_image_workspace_generation_reports_a_missing_frequency_grid，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_workspace_generation_reports_a_missing_frequency_grid(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.generate_datasheet_network(0)

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("手动", response["error"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.open_datasheet_output_dir()["ok"])

    # Codex说明(自动生成)： 定义函数 test_image_open_folder_does_not_reuse_generator_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_open_folder_does_not_reuse_generator_output(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.run_generation_sync(
                {
                    "mode": "linear",
                    "ports": "2",
                    "f_start": "1GHz",
                    "f_stop": "2GHz",
                    "points": "5",
                    "loss_start_db": "1",
                    "loss_stop_db": "4",
                    "output": str(Path(temp_dir) / "generator.s2p"),
                }
            )

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 计算并保存 opened，供后续语句继续读取或更新。
        opened = api.open_datasheet_output_dir()
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(opened["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("图片页", opened["error"])

    # Codex说明(自动生成)： 定义函数 test_image_workspace_converts_a_mixed_mode_matrix_before_export，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_workspace_converts_a_mixed_mode_matrix_before_export(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_parameter_family，执行当前流程需要的具体操作或副作用。
        api.set_network_parameter_family(0, "mixed-mode")
        # Codex说明(自动生成)： 调用 api.set_network_frequency_policy，执行当前流程需要的具体操作或副作用。
        api.set_network_frequency_policy(
            0, "manual", "1GHz", "2GHz", "500MHz", False
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory(), mock.patch('insertion_loss_tool.webview_gui.OUTPUT_DIR'...，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(temp_dir)
        ):
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            review = api.preview_image_export(0)
            self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
            response = api.generate_datasheet_network(0)

            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(response["ok"], response)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(response["parameter_family"], "mixed-mode")
            # Codex说明(自动生成)： 计算并保存 generated，供后续语句继续读取或更新。
            generated = read_touchstone(response["output"])
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(generated.n_ports, 4)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(generated.frequency_hz.size, 3)
            # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
            self.assertLessEqual(
                float(np.linalg.svd(generated.s, compute_uv=False).max()), 1.0
            )

    # Codex说明(自动生成)： 定义函数 test_image_workspace_refuses_to_write_a_non_passive_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_workspace_refuses_to_write_a_non_passive_mapping(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
        digitized = self._stub_digitization(start_hz=1e9, stop_hz=2e9)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(temp_dir)
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = folder / "strong.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "250MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=digitized,
            ):
                # Codex说明(自动生成)： 调用 api.digitize_image，执行当前流程需要的具体操作或副作用。
                api.digitize_image(0, -10, 0)
            # Codex说明(自动生成)： 调用 api.set_curve_parameter，执行当前流程需要的具体操作或副作用。
            api.set_curve_parameter(0, "A", "S12")
            # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
            source = "图1 A · S12"
            # Codex说明(自动生成)： 遍历 ('S11', 'S12', 'S21', 'S22') 中的 parameter，逐项执行循环体逻辑。
            for parameter in ("S11", "S12", "S21", "S22"):
                # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
                api.set_mapping(0, parameter, source)

            # Codex说明(自动生成)： 计算并保存 output_dir，供后续语句继续读取或更新。
            output_dir = folder / "outputs"
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.OUTPUT_DIR'...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.webview_gui.OUTPUT_DIR", output_dir
            ):
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                review = api.preview_image_export(0)
                self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
                response = api.generate_datasheet_network(0)

            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(response["ok"])
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("not passive", response["error"])
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(output_dir.exists())

    # Codex说明(自动生成)： 定义函数 test_image_workspace_lists_every_unassigned_channel_before_export，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_workspace_lists_every_unassigned_channel_before_export(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_frequency_policy，执行当前流程需要的具体操作或副作用。
        api.set_network_frequency_policy(
            0, "manual", "1GHz", "2GHz", "500MHz", False
        )
        # Codex说明(自动生成)： 遍历 ('S12', 'S21', 'S22') 中的 parameter，逐项执行循环体逻辑。
        for parameter in ("S12", "S21", "S22"):
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.set_mapping(0, parameter, "自动")["ok"])

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.generate_datasheet_network(0)

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("S12, S21, S22", response["error"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("默认曲线", response["error"])

    # Codex说明(自动生成)： 定义函数 test_windows_uses_webview2_and_macos_uses_wkwebview_default，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_windows_uses_webview2_and_macos_uses_wkwebview_default(self) -> None:
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(select_webview_backend("win32"), "edgechromium")
        # Codex说明(自动生成)： 调用 self.assertIsNone 检查测试期望，确认实际结果符合预期。
        self.assertIsNone(select_webview_backend("darwin"))
        # Codex说明(自动生成)： 计算并保存 probe，供后续语句继续读取或更新。
        probe = {
            "initialViewportWidth": 1380,
            "title": "Insertion Loss Tool",
            "background": "radial-gradient(rgb(0, 0, 0), rgba(0, 0, 0, 0))",
            "backdrop": "blur(18px)",
            "tabs": 2,
            "tabLabels": [
                "Generate and Modify S-Parameter",
                "Image to S-Parameter",
            ],
            "activePanels": 1,
            "overflowFree": True,
            "webview2": True,
            "bridgeCalls": 0,
            "modifyInputSummary": "Loaded formula_demo.s4p · 4 ports · 201 points · 10MHz–40GHz",
            "modifyInputPorts": 4,
            "modifyInputPoints": 201,
            "modifyInputStart": "10MHz",
            "modifyInputStop": "40GHz",
            "modifyPlotCount": 16,
            "modifyHasS44": True,
            "modifyBridgeCalls": 2,
            "modifyInvalidErrorVisible": True,
            "modifyInvalidPlotCleared": True,
            "imagePreviewWidth": 500,
            "imagePreviewHeight": 400,
            "imagePanelWidth": 700,
            "detailPanelWidth": 500,
            "outputPanelWidth": 150,
            "digitizeButton": True,
            "networkOutputWidth": 360,
            "frequencyPolicyWidth": 155,
            "zoomDialogOpen": True,
            "zoomLevelBefore": "100%",
            "zoomLevelAfter": "125%",
            "zoomWidthBefore": 300,
            "zoomWidthAfter": 500,
            "zoomScrollable": True,
            "generatorPortOptions": [2, 3, 4, 6, 8],
            "datasheetPortOptions": [2, 3, 4, 6, 8],
            "modeLabels": ["Linear", "Formula", "Draw", "Modify"],
            "wrappedModeLabels": 0,
            "modelUnitLabels": ["GHz", "MHz", "kHz", "Hz"],
            "frequencyUnitLabels": ["GHz", "MHz", "kHz", "Hz"],
            "drawBoardWidth": 800,
            "drawBoardHeight": 440,
            "drawClickToken": "10MHz:0",
            "drawAxisText": "Magnitude (dB) Frequency (GHz)",
            "drawXAxisCenterError": 0.0,
            "drawTickUnits": False,
            "drawGeneratedPlotVisible": True,
            "drawGeneratedPlotCount": 4,
            "drawEditorRestored": True,
            "outputItemCount": 2,
            "outputItemsClipped": False,
            "maxOutputAccessible": True,
            "mappingGridTop": 360,
            "detailTop": 120,
            "plotSharedScaleGap": 120,
            "plotAxisText": "Magnitude (dB) Frequency (GHz)",
            "plotFrequencyTicks": [0, 10, 20, 30, 40],
            "plotMagnitudeTicks": [-25, -20, -15, -10, -5, 0],
            "plotXAxisCenterError": 0.0,
            "plotUnusedFraction": 0.02,
            "plotToolbarCount": 3,
            "plotToolbarIconCount": 3,
            "plotToolbarText": "",
            "plotInitialMode": "pan",
            "plotWheelChanged": True,
            "plotResetRestored": True,
            "plotPanChanged": True,
            "plotBoxZoomChanged": True,
            "phaseUnitOverlapsTicks": False,
            "plotPhaseTicks": [-1440, -1080, -720, -360, 0, 360],
            "phaseAxisText": "Phase (deg) Frequency (GHz)",
            "generateNetworkButton": True,
            "imageOpenFolderButton": True,
            "translatedErrorText": "Generation is already in progress.",
            "bodyHasHan": False,
            "responsiveRequestedWindowWidth": 960,
            "responsiveRequestedWindowHeight": 640,
            "responsiveViewportWidth": 960,
            "responsiveViewportHeight": 640,
            "responsiveDrawBoardWidth": 612,
            "responsiveDrawBoardHeight": 416,
            "responsiveOutputItemsClipped": False,
            "responsiveMaxOutputAccessible": True,
            "responsiveOverflowFree": True,
            "detailHorizontalOverflow": False,
            "coverageStatusClipped": False,
            "mappingGridHorizontalOverflow": False,
            "mappingSelectMinWidth": 300,
            "traceColors": ["139,222,248", "239,117,189"],
            "swatchColors": ["139,222,248", "239,117,189"],
            "traceUsageTexts": [
                "Used by Output 1 S11",
                "Not used · choose it in the S-parameter panel",
            ],
            "traceHighlightSelected": True,
            "visualReviewOverlayCount": 1,
            "visualReviewCardText": "Review 1 highlighted area · image accuracy not assessed",
            "visualReviewHelpText": "Orange dashed areas need visual review · 1 highlighted",
            "visualReviewMappingHint": "2 traces available · 1 need highlighted-area review · detected labels are hints",
            "visualReviewHighlightSelected": True,
            "unassignedOptionText": "Unassigned",
            "unassignedPreflightText": "Unassigned channels: S12, S21, S22. Choose a detected trace, Matched · exact zero, Return loss −20 dB, or Crosstalk −80 dB.",
            "candidateTraceCount": 2,
            "candidateOverlayCount": 2,
            "editorCalibrationSent": True,
            "candidateHasParameterSelect": False,
            "candidateListStatus": "2 trace candidates · Calibrate axes",
            "candidateTitle": "Trace Candidates · 2",
            "yConventionOptions": ["magnitude", "positive-loss"],
            "unassignedPreflightBridgeCalls": 0,
            "reimportImageCount": 1,
        }
        # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
        validate_renderer_probe(probe, "win32")
        with self.assertRaisesRegex(RuntimeError, "trace candidates"):
            validate_renderer_probe({**probe, "candidateOverlayCount": 0}, "darwin")
        with self.assertRaisesRegex(RuntimeError, "unsaved X/Y"):
            validate_renderer_probe({**probe, "editorCalibrationSent": False}, "darwin")
        with self.assertRaisesRegex(RuntimeError, "局部风险区"):
            validate_renderer_probe(
                {**probe, "visualReviewOverlayCount": 0}, "darwin"
            )
        # At the exact CSS breakpoint the detail panel intentionally spans the
        # second row, so it may be wider than the image panel.
        validate_renderer_probe(
            {
                **probe,
                "initialViewportWidth": 1050,
                "imagePanelWidth": 520,
                "imagePreviewWidth": 500,
                "detailPanelWidth": 900,
            },
            "win32",
        )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'viewport 1051px')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "viewport 1051px"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {
                    **probe,
                    "initialViewportWidth": 1051,
                    "imagePanelWidth": 520,
                    "imagePreviewWidth": 500,
                    "detailPanelWidth": 900,
                },
                "win32",
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'initial viewport ...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "initial viewport width"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "initialViewportWidth": 0}, "win32")
        # The 220 px mapping track contains 18 px of card padding/borders, and
        # native select geometry may round by 2 px across renderers.
        validate_renderer_probe({**probe, "mappingSelectMinWidth": 200}, "win32")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'actual 199px, min...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "actual 199px, minimum 200px"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "mappingSelectMinWidth": 199}, "win32")
        # Windows WebView2 reports the client viewport after native borders,
        # so a requested 960x640 window can validly expose about 944x601.
        validate_renderer_probe(
            {
                **probe,
                "responsiveViewportWidth": 944,
                "responsiveViewportHeight": 601,
                "responsiveDrawBoardWidth": 596,
            },
            "win32",
        )
        # Exact Draw-width boundaries bind the CSS horizontal-chrome formula.
        validate_renderer_probe(
            {
                **probe,
                "responsiveViewportWidth": 944,
                "responsiveViewportHeight": 601,
                "responsiveDrawBoardWidth": 594,
                "responsiveDrawBoardHeight": 360,
            },
            "win32",
        )
        # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
        validate_renderer_probe(
            {
                **probe,
                "responsiveDrawBoardWidth": 610,
                "responsiveDrawBoardHeight": 360,
            },
            "darwin",
        )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Responsive Draw')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Responsive Draw"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {
                    **probe,
                    "responsiveViewportWidth": 944,
                    "responsiveViewportHeight": 601,
                    "responsiveDrawBoardWidth": 593,
                },
                "win32",
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Responsive Draw')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Responsive Draw"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {**probe, "responsiveDrawBoardWidth": 609}, "darwin"
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Responsive Draw')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Responsive Draw"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {**probe, "responsiveDrawBoardHeight": 359}, "darwin"
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'WebView2')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "WebView2"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "webview2": False}, "win32")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '页签')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "页签"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "activePanels": 2}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '页签名称')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "页签名称"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {**probe, "tabLabels": ["Generator", "Datasheet"]}, "darwin"
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '切换')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "切换"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "switchMs": 999}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Python')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Python"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "bridgeCalls": 1}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Modify')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Modify"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "modifyInputPoints": 801}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Modify')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Modify"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "modifyInvalidErrorVisible": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Modify')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Modify"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "modifyInvalidPlotCleared": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '缩放')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "缩放"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "zoomLevelAfter": "100%"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '放大')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "放大"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "zoomScrollable": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '端口')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "端口"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "datasheetPortOptions": list(range(1, 9))}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'mode labels')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "mode labels"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "modeLabels": ["Linear", "Protocol Formula", "Draw", "Modify"]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'wrapped')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "wrapped"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "wrappedModeLabels": 1}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'frequency units')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "frequency units"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "modelUnitLabels": ["ghz", "mhz", "khz", "hz"]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'drawing area')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "drawing area"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawBoardHeight": 110}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'click coordinates')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "click coordinates"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawClickToken": "2.78825GHz:-1.962"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Draw mode axes')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Draw mode axes"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawAxisText": "dB GHz"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Draw mode frequen...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Draw mode frequency-axis"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawXAxisCenterError": 10.0}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'complete S-parame...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "complete S-parameter"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawGeneratedPlotVisible": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'drawing board')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "drawing board"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "drawEditorRestored": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'output network')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "output network"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "outputItemsClipped": True}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'output network')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "output network"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "maxOutputAccessible": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'mappings')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "mappings"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "mappingGridTop": 500}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'shared calibrated...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "shared calibrated Y scale"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotSharedScaleGap": 1}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'axis ticks or uni...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "axis ticks or units"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotAxisText": "Magnitude"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'frequency ticks')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "frequency ticks"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotFrequencyTicks": [0.01, 13.34, 26.67, 40]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'magnitude ticks')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "magnitude ticks"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotMagnitudeTicks": [0.99, -4.56, -10.1, -15.64, -21.19]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Generated plot fr...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Generated plot frequency-axis"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotXAxisCenterError": 10.0}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'unused vertical s...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "unused vertical space"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotUnusedFraction": 0.5}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'ResponseLab')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "ResponseLab"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotToolbarCount": 2}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'icon-only')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "icon-only"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotToolbarText": "Pan"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'zoom, pan, or res...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "zoom, pan, or reset"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotWheelChanged": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'zoom, pan, or res...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "zoom, pan, or reset"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotPanChanged": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'zoom, pan, or res...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "zoom, pan, or reset"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotBoxZoomChanged": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Phase unit')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Phase unit"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "phaseUnitOverlapsTicks": True}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'phase ticks')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "phase ticks"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "plotPhaseTicks": [-1226.5, -878.82, -531.14, -183.46, 164.21]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'generation button')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "generation button"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "generateNetworkButton": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Open Folder')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Open Folder"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "imageOpenFolderButton": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'English')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "English"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "bodyHasHan": True}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'error messages')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "error messages"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "translatedErrorText": "正在生成。"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '960x640')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "960x640"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveViewportWidth": 1380}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'request')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "request"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {**probe, "responsiveRequestedWindowWidth": 1380}, "darwin"
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '960x640')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "960x640"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveViewportWidth": 880}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '960x640')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "960x640"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveViewportWidth": 1040}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '960x640')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "960x640"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {
                    **probe,
                    "responsiveViewportWidth": 900,
                    "responsiveViewportHeight": 590,
                },
                "darwin",
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '960x640')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "960x640"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveViewportHeight": 860}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Responsive Draw')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Responsive Draw"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveDrawBoardWidth": 582}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'Responsive Datash...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "Responsive Datasheet"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "responsiveMaxOutputAccessible": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '识别按钮')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "识别按钮"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "digitizeButton": False}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '图片工作区')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "图片工作区"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "imagePanelWidth": 560}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '输出列表占用')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "输出列表占用"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "outputPanelWidth": 300}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '输出文件字段')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "输出文件字段"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "networkOutputWidth": 120}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, '频率范围字段')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "频率范围字段"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "frequencyPolicyWidth": 100}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'detail panel')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "detail panel"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "detailHorizontalOverflow": True}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'coverage status')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "coverage status"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "coverageStatusClipped": True}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'mapping grid')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "mapping grid"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe(
                {**probe, "mappingGridHorizontalOverflow": True}, "darwin"
            )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'mapping selector')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "mapping selector"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "mappingSelectMinWidth": 162}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'distinct display ...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "distinct display colors"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "traceColors": ["201,145,170", "201,145,170"]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'swatches')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "swatches"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "swatchColors": ["201,145,170", "201,145,170"]}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'isolate')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "isolate"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "traceHighlightSelected": False}, "darwin")
        with self.assertRaisesRegex(RuntimeError, "read-only S-parameter usage"):
            validate_renderer_probe({**probe, "traceUsageTexts": []}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'mislabeled')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "mislabeled"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "unassignedOptionText": "Default"}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 'unassigned channe...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "unassigned channels"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "unassignedPreflightBridgeCalls": 1}, "darwin")
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(RuntimeError, 're-imported')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(RuntimeError, "re-imported"):
            # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
            validate_renderer_probe({**probe, "reimportImageCount": 0}, "darwin")

    # Codex说明(自动生成)： 定义函数 test_headless_smoke_does_not_require_pywebview，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_headless_smoke_does_not_require_pywebview(self) -> None:
        # Codex说明(自动生成)： 计算并保存 original_import，供后续语句继续读取或更新。
        original_import = builtins.__import__

        # Codex说明(自动生成)： 定义函数 guarded_import，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def guarded_import(name: str, *args: object, **kwargs: object) -> object:
            # Codex说明(自动生成)： 检查条件 name == 'webview'，根据结果选择后续执行路径。
            if name == "webview":
                # Codex说明(自动生成)： 抛出 ModuleNotFoundError('webview intentionally unavailable')，明确提示输入、状态或处理流程无法继续。
                raise ModuleNotFoundError("webview intentionally unavailable")
            # Codex说明(自动生成)： 返回 original_import(name, *args, **kwargs)，让调用方取得本函数的处理结果。
            return original_import(name, *args, **kwargs)

        # Codex说明(自动生成)： 进入上下文 mock.patch('builtins.__import__', side_effect=guarded_i...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch("builtins.__import__", side_effect=guarded_import):
            # Codex说明(自动生成)： 调用 run_smoke_test，执行当前流程需要的具体操作或副作用。
            run_smoke_test(real_window=False)

    # Codex说明(自动生成)： 定义函数 test_datasheet_reciprocal_linking_is_real_and_can_be_disabled，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_reciprocal_linking_is_real_and_can_be_disabled(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.set_mapping(0, "S31", "公式")
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = response["network"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(network["mappings"]["S31"], "公式")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(network["mappings"]["S13"], "公式")

        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.set_mapping(0, "S31", "未知")
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = response["network"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(network["mappings"]["S31"], "未知")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(network["mappings"]["S13"], "公式")

    # Codex说明(自动生成)： 定义函数 test_datasheet_mixed_mode_uses_all_four_blocks_and_correct_reciprocity，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_mixed_mode_uses_all_four_blocks_and_correct_reciprocity(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.set_network_parameter_family(0, "mixed-mode")

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = response["network"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(network["parameter_family"], "mixed-mode")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(network["mappings"]), 16)
        # Codex说明(自动生成)： 遍历 ('SDD11', 'SDC21', 'SCD12', 'SCC22') 中的 parameter，逐项执行循环体逻辑。
        for parameter in ("SDD11", "SDC21", "SCD12", "SCC22"):
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn(parameter, network["mappings"])
        # Codex说明(自动生成)： 计算并保存 linked，供后续语句继续读取或更新。
        linked = api.set_mapping(0, "SCD21", "公式")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(linked["network"]["mappings"]["SDC12"], "公式")
        # Codex说明(自动生成)： 计算并保存 rejected，供后续语句继续读取或更新。
        rejected = api.set_network_ports(0, 3)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(rejected["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("偶数", rejected["error"])

    # Codex说明(自动生成)： 定义函数 test_datasheet_count_port_and_source_boundaries，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_count_port_and_source_boundaries(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(api.set_network_count(1)["networks"]), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(api.set_network_count(6)["networks"]), 6)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_count(0)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_count(99)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_count("bad")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_ports(0, 0)["ok"])
        # Codex说明(自动生成)： 遍历 (1, 5, 7) 中的 unsupported，逐项执行循环体逻辑。
        for unsupported in (1, 5, 7):
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(api.set_network_ports(0, unsupported)["ok"])
        # Codex说明(自动生成)： 遍历 (2, 3, 4, 6, 8) 中的 supported，逐项执行循环体逻辑。
        for supported in (2, 3, 4, 6, 8):
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.set_network_ports(0, supported)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_ports(0, 9)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_ports(-1, 2)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_ports(99, 2)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_reciprocal(-1, True)["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_network_reciprocal(0, "false")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_mapping(0, "S99", "自动")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_mapping(-1, "S11", "自动")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_mapping(0, "S11", "任意脚本")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_mapping(0, "S11", "图999 A · 深蓝")["ok"])

    # Codex说明(自动生成)： 定义函数 test_datasheet_state_mutations_are_serialized，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_state_mutations_are_serialized(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(2)
        # Codex说明(自动生成)： 计算并保存 entered，供后续语句继续读取或更新。
        entered = threading.Event()
        # Codex说明(自动生成)： 计算并保存 release，供后续语句继续读取或更新。
        release = threading.Event()

        # Codex说明(自动生成)： 定义 BlockingSource 类，把相关数据结构、校验规则或操作方法组织在一起。
        class BlockingSource:
            # Codex说明(自动生成)： 定义函数 __str__，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
            def __str__(self) -> str:
                # Codex说明(自动生成)： 调用 entered.set，执行当前流程需要的具体操作或副作用。
                entered.set()
                # Codex说明(自动生成)： 调用 release.wait，执行当前流程需要的具体操作或副作用。
                release.wait(timeout=2)
                # Codex说明(自动生成)： 返回 '自动'，让调用方取得本函数的处理结果。
                return "自动"

        # Codex说明(自动生成)： 声明并保存 outcomes，同时保留类型信息方便维护和静态检查。
        outcomes: list[object] = []

        # Codex说明(自动生成)： 定义函数 update_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def update_mapping() -> None:
            # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
            try:
                # Codex说明(自动生成)： 调用 outcomes.append 更新列表或集合，把当前步骤产生的数据加入结果。
                outcomes.append(api.set_mapping(1, "S21", BlockingSource()))
            # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
            except Exception as exc:  # pragma: no cover - regression sentinel
                # Codex说明(自动生成)： 调用 outcomes.append 更新列表或集合，把当前步骤产生的数据加入结果。
                outcomes.append(exc)

        # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
        first = threading.Thread(target=update_mapping)
        # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
        second = threading.Thread(target=lambda: outcomes.append(api.set_network_count(1)))
        # Codex说明(自动生成)： 调用 first.start，执行当前流程需要的具体操作或副作用。
        first.start()
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(entered.wait(timeout=1))
        # Codex说明(自动生成)： 调用 second.start，执行当前流程需要的具体操作或副作用。
        second.start()
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.02)
        # Codex说明(自动生成)： 调用 release.set，执行当前流程需要的具体操作或副作用。
        release.set()
        # Codex说明(自动生成)： 调用 first.join，执行当前流程需要的具体操作或副作用。
        first.join(timeout=2)
        # Codex说明(自动生成)： 调用 second.join，执行当前流程需要的具体操作或副作用。
        second.join(timeout=2)

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(outcomes), 2)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(all(isinstance(item, dict) and item["ok"] for item in outcomes), outcomes)

    # Codex说明(自动生成)： 定义函数 test_image_registration_appends_deduplicates_without_fake_curve_options，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_registration_appends_deduplicates_without_fake_curve_options(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(temp_dir)
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = folder / "a.png"
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = folder / "b.jpg"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 second.write_bytes 写出文件或数据，保存当前处理结果。
            second.write_bytes(b"\xff\xd8\xff")
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.register_images([first, second, first])

            # Codex说明(自动生成)： 计算并保存 mapping_response，供后续语句继续读取或更新。
            mapping_response = api.set_mapping(0, "S21", "图1 A · 深蓝")

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            [item["name"] for item in response["images_added"]],
            ["a.png", "b.jpg"],
        )
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("图1 A · 深蓝", response["source_options"])
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("图2 D · 浅蓝", response["source_options"])
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("复制 S21", response["source_options"])
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("images", mapping_response)

    # Codex说明(自动生成)： 定义函数 test_image_picker_accepts_a_single_string_path_from_native_dialog，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_picker_accepts_a_single_string_path_from_native_dialog(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "single.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 计算并保存 window，供后续语句继续读取或更新。
            window = mock.Mock()
            # Codex说明(自动生成)： 计算并保存 window.create_file_dialog.return_value，供后续语句继续读取或更新。
            window.create_file_dialog.return_value = str(image)
            # Codex说明(自动生成)： 调用 api.bind_window，执行当前流程需要的具体操作或副作用。
            api.bind_window(window)

            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.choose_images()

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_count"], 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["images_added"][0]["name"], "single.png")

    # Codex说明(自动生成)： 定义函数 test_image_picker_surfaces_native_dialog_failure，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_picker_surfaces_native_dialog_failure(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 window，供后续语句继续读取或更新。
        window = mock.Mock()
        # Codex说明(自动生成)： 计算并保存 window.create_file_dialog.side_effect，供后续语句继续读取或更新。
        window.create_file_dialog.side_effect = OSError("native dialog failed")
        # Codex说明(自动生成)： 调用 api.bind_window，执行当前流程需要的具体操作或副作用。
        api.bind_window(window)

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.choose_images()

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["error"], "无法打开图片选择窗口，请重试。")

    # Codex说明(自动生成)： 定义函数 test_modify_picker_accepts_a_single_string_path_from_native_dialog，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_picker_accepts_a_single_string_path_from_native_dialog(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 window，供后续语句继续读取或更新。
        window = mock.Mock()
        # Codex说明(自动生成)： 计算并保存 window.create_file_dialog.return_value，供后续语句继续读取或更新。
        window.create_file_dialog.return_value = "/tmp/source.s4p"
        # Codex说明(自动生成)： 调用 api.bind_window，执行当前流程需要的具体操作或副作用。
        api.bind_window(window)

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.choose_input()

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["path"], str(Path("/tmp/source.s4p").resolve()))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["name"], "source.s4p")

    # Codex说明(自动生成)： 定义函数 test_modify_picker_surfaces_native_dialog_failure，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_picker_surfaces_native_dialog_failure(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 window，供后续语句继续读取或更新。
        window = mock.Mock()
        # Codex说明(自动生成)： 计算并保存 window.create_file_dialog.side_effect，供后续语句继续读取或更新。
        window.create_file_dialog.side_effect = OSError("native dialog failed")
        # Codex说明(自动生成)： 调用 api.bind_window，执行当前流程需要的具体操作或副作用。
        api.bind_window(window)

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = api.choose_input()

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            response["error"], "无法打开 Touchstone 选择窗口，请重试。"
        )

    # Codex说明(自动生成)： 定义函数 test_duplicate_image_selection_returns_visible_warning，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_duplicate_image_selection_returns_visible_warning(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "same.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])

            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.register_images([image])

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["images_added"], [])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["warnings"], ["图片已存在：same.png"])

    # Codex说明(自动生成)： 定义函数 test_removed_image_can_be_added_again_as_a_fresh_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_removed_image_can_be_added_again_as_a_fresh_image(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "again.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = api.register_images([image])
            # Codex说明(自动生成)： 计算并保存 removed，供后续语句继续读取或更新。
            removed = api.remove_image(0)
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = api.register_images([image])

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(first["image_count"], 1)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(removed["ok"], removed)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(removed["image_count"], 0)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(second["image_count"], 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(second["warnings"], [])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(second["images_added"][0]["name"], "again.png")

    # Codex说明(自动生成)： 定义函数 test_image_registration_deduplicates_identical_content_across_paths，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_registration_deduplicates_identical_content_across_paths(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = Path(temp_dir) / "first.png"
            # Codex说明(自动生成)： 计算并保存 copied，供后续语句继续读取或更新。
            copied = Path(temp_dir) / "copied.png"
            # Codex说明(自动生成)： 计算并保存 payload，供后续语句继续读取或更新。
            payload = b"\x89PNG\r\n\x1a\nidentical"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(payload)
            # Codex说明(自动生成)： 调用 copied.write_bytes 写出文件或数据，保存当前处理结果。
            copied.write_bytes(payload)

            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.register_images([first, copied])

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(response["images_added"]), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["images_added"][0]["name"], "first.png")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(response["images_added"][0]["sha256"]), 64)

    # Codex说明(自动生成)： 定义函数 test_removing_an_image_reindexes_sources_and_clears_only_its_mappings，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_removing_an_image_reindexes_sources_and_clears_only_its_mappings(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = Path(temp_dir) / "first.png"
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = Path(temp_dir) / "second.png"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(b"\x89PNG\r\n\x1a\nfirst")
            # Codex说明(自动生成)： 调用 second.write_bytes 写出文件或数据，保存当前处理结果。
            second.write_bytes(b"\x89PNG\r\n\x1a\nsecond")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([first, second])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "10MHz")
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(1, "1GHz", "2GHz", "10MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=self._stub_digitization,
            ):
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(0, -10, 0)["ok"])
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(1, -10, 0)["ok"])
            # Codex说明(自动生成)： 调用 api.set_curve_parameter，执行当前流程需要的具体操作或副作用。
            api.set_curve_parameter(0, "A", "S11")
            # Codex说明(自动生成)： 调用 api.set_curve_parameter，执行当前流程需要的具体操作或副作用。
            api.set_curve_parameter(1, "A", "S21")
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S11", "图1 A · S11")
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S21", "图2 A · S21")

            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.remove_image(0)

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_removed"], 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_count"], 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_updates"][0]["index"], 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_updates"][0]["name"], "second.png")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["networks"][0]["mappings"]["S11"], "未知")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["networks"][0]["mappings"]["S21"], "图1 A · S21")
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("图1 A · S21", response["source_options"])
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("图2 A · S21", response["source_options"])

    # Codex说明(自动生成)： 定义函数 test_image_removal_is_rejected_while_digitization_is_active，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_removal_is_rejected_while_digitization_is_active(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 entered，供后续语句继续读取或更新。
        entered = threading.Event()
        # Codex说明(自动生成)： 计算并保存 release，供后续语句继续读取或更新。
        release = threading.Event()
        # Codex说明(自动生成)： 声明并保存 result，同时保留类型信息方便维护和静态检查。
        result: dict[str, object] = {}

        # Codex说明(自动生成)： 定义函数 delayed_digitization，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def delayed_digitization(*args: object, **kwargs: object) -> DigitizationResult:
            # Codex说明(自动生成)： 调用 entered.set，执行当前流程需要的具体操作或副作用。
            entered.set()
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(release.wait(2))
            # Codex说明(自动生成)： 返回 self._stub_digitization(*args, **kwargs)，让调用方取得本函数的处理结果。
            return self._stub_digitization(*args, **kwargs)

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "active.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\nactive")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "10MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=delayed_digitization,
            ):
                # Codex说明(自动生成)： 计算并保存 worker，供后续语句继续读取或更新。
                worker = threading.Thread(
                    target=lambda: result.update(api.digitize_image(0, -10, 0))
                )
                # Codex说明(自动生成)： 调用 worker.start，执行当前流程需要的具体操作或副作用。
                worker.start()
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(entered.wait(2))
                # Codex说明(自动生成)： 计算并保存 rejected，供后续语句继续读取或更新。
                rejected = api.remove_image(0)
                # Codex说明(自动生成)： 调用 release.set，执行当前流程需要的具体操作或副作用。
                release.set()
                # Codex说明(自动生成)： 调用 worker.join，执行当前流程需要的具体操作或副作用。
                worker.join(2)

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(rejected["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("识别", rejected["error"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(result["ok"], result)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(api.get_defaults()["datasheet"]["images"][0]["name"], "active.png")

    # Codex说明(自动生成)： 定义函数 test_later_image_registration_is_incremental_and_resource_bounded，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_later_image_registration_is_incremental_and_resource_bounded(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = Path(temp_dir) / "first.png"
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = Path(temp_dir) / "second.png"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(b"\x89PNG\r\n\x1a\nfirst")
            # Codex说明(自动生成)： 调用 second.write_bytes 写出文件或数据，保存当前处理结果。
            second.write_bytes(b"\x89PNG\r\n\x1a\nsecond")

            # Codex说明(自动生成)： 计算并保存 initial，供后续语句继续读取或更新。
            initial = api.register_images([first])
            # Codex说明(自动生成)： 计算并保存 later，供后续语句继续读取或更新。
            later = api.register_images([second])

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(initial["images_added"]), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(later["images_added"]), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(later["images_added"][0]["name"], "second.png")
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("images", later)
        # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
        self.assertNotEqual(
            later["images_added"][0]["data_url"],
            initial["images_added"][0]["data_url"],
        )

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 third，供后续语句继续读取或更新。
            third = Path(temp_dir) / "third.png"
            # Codex说明(自动生成)： 调用 third.write_bytes 写出文件或数据，保存当前处理结果。
            third.write_bytes(b"\x89PNG\r\n\x1a\nthird")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.MAX...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch("insertion_loss_tool.datasheet_workspace.MAX_IMAGES", 2):
                # Codex说明(自动生成)： 计算并保存 count_limited，供后续语句继续读取或更新。
                count_limited = api.register_images([third])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(count_limited["images_added"], [])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(count_limited["warnings"])

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 oversized，供后续语句继续读取或更新。
            oversized = Path(temp_dir) / "oversized.png"
            # Codex说明(自动生成)： 进入上下文 oversized.open('wb')，确保文件、资源或临时状态按作用域正确释放。
            with oversized.open("wb") as stream:
                # Codex说明(自动生成)： 调用 stream.truncate，执行当前流程需要的具体操作或副作用。
                stream.truncate(21 * 1024 * 1024)
            # Codex说明(自动生成)： 计算并保存 rejected，供后续语句继续读取或更新。
            rejected = api.register_images([oversized])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(rejected["images_added"], [])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(rejected["warnings"])

    # Codex说明(自动生成)： 定义函数 test_image_frequency_is_editable_but_unrecognized_curves_stay_unavailable，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_image_frequency_is_editable_but_unrecognized_curves_stay_unavailable(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "mixed.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 计算并保存 registered，供后续语句继续读取或更新。
            registered = api.register_images([image])

            # Codex说明(自动生成)： 计算并保存 imported，供后续语句继续读取或更新。
            imported = registered["images_added"][0]
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(imported["axis"]["status"], "required")
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(imported["axis"]["source"], "none")
            # Codex说明(自动生成)： 计算并保存 blocked，供后续语句继续读取或更新。
            blocked = api.digitize_image(0, -10, 0)
            # Codex说明(自动生成)： 计算并保存 calibrated，供后续语句继续读取或更新。
            calibrated = api.set_image_frequency(
                0, "10MHz", "18GHz", "10MHz", "linear"
            )
            # Codex说明(自动生成)： 计算并保存 labeled，供后续语句继续读取或更新。
            labeled = api.set_curve_parameter(0, "A", "SCD21")

        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("images", calibrated)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("data_url", calibrated["image_update"])
        # Codex说明(自动生成)： 计算并保存 axis，供后续语句继续读取或更新。
        axis = calibrated["image_update"]["axis"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["start_hz"], 10e6)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["stop_hz"], 18e9)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["step_hz"], 10e6)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["points"], 1800)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["status"], "ready")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(axis["source"], "manual")
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(blocked["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("坐标轴", blocked["error"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(registered["images_added"][0]["axis"]["status"], "required")
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(labeled["ok"])
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("图1 A", " ".join(calibrated["source_options"]))
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_curve_parameter(0, "A", "SDX21")["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(api.set_image_frequency(0, "18GHz", "10MHz", "10MHz", "linear")["ok"])

    def test_axis_review_still_exposes_trace_candidates_in_the_image_overlay(self) -> None:
        """Missing OCR axes must not make visible curves look undetected."""

        api = InsertionLossWebApi()
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="review",
                y_min_db=-4.0,
                y_max_db=0.0,
                missing=("start", "stop", "step", "spacing"),
                warnings=("Some axis labels require review.",),
            ),
        )
        preview = self._stub_digitization(start_hz=1.0, stop_hz=2.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "axis-review.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            with (
                mock.patch(
                    "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                    return_value=analysis,
                ),
                mock.patch(
                    "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                    return_value=preview,
                ) as detect_candidates,
            ):
                response = api.analyze_image(0)

        self.assertTrue(response["ok"], response)
        self.assertFalse(response["auto_digitize"])
        update = response["image_update"]
        self.assertEqual(update["axis"]["status"], "review")
        self.assertEqual(update["digitization"]["status"], "review")
        self.assertEqual(update["digitization"]["candidate_status"], "preview")
        self.assertEqual(update["candidates"], 1)
        self.assertEqual([curve["id"] for curve in update["curves"]], ["A"])
        self.assertEqual(update["curves"][0]["calibrated"], False)
        self.assertTrue(update["curves"][0]["preview_points"])
        self.assertNotIn("图1 A", " ".join(response["source_options"]))
        detect_candidates.assert_called_once_with(
            image.resolve(),
            start_hz=1.0,
            stop_hz=2.0,
            y_min_db=-1.0,
            y_max_db=0.0,
            run_ocr=False,
            spacing="linear",
        )

    def test_positive_loss_axis_is_converted_to_negative_s_parameter_magnitude(self) -> None:
        """Users may enter the positive-down loss values printed by a vendor."""

        api = InsertionLossWebApi()
        detected = self._stub_digitization(start_hz=10e6, stop_hz=110e9)
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "positive-loss.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            api.set_image_frequency(0, "10MHz", "110GHz", "100MHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ) as digitize:
                response = api.digitize_image_with_axis(
                    0, 0, 10, "positive-loss"
                )

        self.assertTrue(response["ok"], response)
        axis = response["image_update"]["axis"]
        self.assertEqual(axis["y_convention"], "positive-loss")
        self.assertEqual(axis["y_top_db"], 0.0)
        self.assertEqual(axis["y_bottom_db"], 10.0)
        self.assertEqual(axis["y_max_db"], 0.0)
        self.assertEqual(axis["y_min_db"], -10.0)
        digitize.assert_called_once()
        self.assertEqual(digitize.call_args.kwargs["y_max_db"], 0.0)
        self.assertEqual(digitize.call_args.kwargs["y_min_db"], -10.0)

        rejected = api.digitize_image_with_axis(0, 10, 0, "positive-loss")
        self.assertFalse(rejected["ok"])
        self.assertIn("下边界", rejected["error"])

    def test_linear_image_frequency_accepts_dc_and_unitless_values_as_ghz(self) -> None:
        """The image-axis form follows the visible GHz plot and permits linear DC."""

        api = InsertionLossWebApi()
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "dc-axis.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])

            explicit = api.set_image_frequency(0, "0GHz", "5GHz", "0.1GHz", "linear")
            self.assertTrue(explicit["ok"], explicit)
            self.assertEqual(explicit["image_update"]["axis"]["start_hz"], 0.0)
            self.assertEqual(explicit["image_update"]["axis"]["stop_hz"], 5e9)
            self.assertEqual(explicit["image_update"]["axis"]["step_hz"], 0.1e9)
            self.assertEqual(explicit["image_update"]["axis"]["points"], 51)

            unitless = api.set_image_frequency(0, "0", "5", "0.1", "linear")
            self.assertTrue(unitless["ok"], unitless)
            self.assertEqual(unitless["image_update"]["axis"]["start_hz"], 0.0)
            self.assertEqual(unitless["image_update"]["axis"]["stop_hz"], 5e9)
            self.assertEqual(unitless["image_update"]["axis"]["step_hz"], 0.1e9)

            logarithmic = api.set_image_frequency(0, "0GHz", "5GHz", "0.1GHz", "log")
            self.assertFalse(logarithmic["ok"])
            self.assertIn("对数频率", logarithmic["error"])

    def test_dc_calibrated_image_trace_generates_and_rereads_touchstone(self) -> None:
        """Accepting 0 GHz must remain valid through mapping and file reread."""

        api = InsertionLossWebApi()
        api.set_network_ports(0, 2)
        frequency = np.array([0.0, 2.5e9, 5e9])
        detected = DigitizationResult(
            image_width=100,
            image_height=80,
            plot_box=(10, 10, 90, 70),
            curves=(
                DigitizedCurve(
                    color="Dark blue",
                    rgb=(36, 76, 206),
                    frequency_hz=frequency,
                    magnitude_db=np.array([-0.1, -1.0, -2.0]),
                    pixel_points=np.column_stack(
                        (np.linspace(10, 90, 3), np.linspace(10, 20, 3))
                    ),
                    confidence=1.0,
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(temp_dir)
        ):
            image = Path(temp_dir) / "dc-trace.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            calibrated = api.set_image_frequency(0, "0", "5", "0.1", "linear")
            self.assertTrue(calibrated["ok"], calibrated)
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                digitized = api.digitize_image(0, -6, 0)
            self.assertTrue(digitized["ok"], digitized)
            source = next(
                option
                for option in digitized["networks"][0]["mapping_options"]["S21"]
                if option.startswith("图1 A ·")
            )
            for parameter, choice in (
                ("S11", "匹配 0"),
                ("S22", "匹配 0"),
                ("S21", source),
            ):
                self.assertTrue(api.set_mapping(0, parameter, choice)["ok"])
            # Codex说明(自动生成)： 计算并保存 review，供后续语句继续读取或更新。
            review = api.preview_image_export(0)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(review["ok"], review)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
            generated = api.generate_datasheet_network(0)
            self.assertTrue(generated["ok"], generated)
            reread = read_touchstone(generated["output"])

        self.assertEqual(reread.frequency_hz[0], 0.0)
        self.assertEqual(reread.frequency_hz[-1], 5e9)
        self.assertTrue(np.all(np.diff(reread.frequency_hz) > 0))

    def test_exact_matched_fallback_allows_a_zero_db_transmission_trace(self) -> None:
        """An unknown reflection may be explicitly set to exact matched zero."""

        api = InsertionLossWebApi()
        api.set_network_ports(0, 2)
        frequency = np.array([1e9, 2e9, 3e9])
        detected = DigitizationResult(
            image_width=100,
            image_height=80,
            plot_box=(10, 10, 90, 70),
            curves=(
                DigitizedCurve(
                    color="Dark blue",
                    rgb=(36, 76, 206),
                    frequency_hz=frequency,
                    magnitude_db=np.array([0.0, -0.1, -0.2]),
                    pixel_points=np.column_stack(
                        (np.linspace(10, 90, 3), np.linspace(10, 20, 3))
                    ),
                    confidence=1.0,
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch(
            "insertion_loss_tool.webview_gui.OUTPUT_DIR", Path(temp_dir)
        ):
            image = Path(temp_dir) / "zero-db.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            api.set_image_frequency(0, "1GHz", "3GHz", "1GHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                digitized = api.digitize_image(0, -1, 0)
            source = next(
                option
                for option in digitized["networks"][0]["mapping_options"]["S21"]
                if option.startswith("图1 A ·")
            )
            self.assertTrue(api.set_mapping(0, "S11", "匹配 0")["ok"])
            self.assertTrue(api.set_mapping(0, "S22", "匹配 0")["ok"])
            self.assertTrue(api.set_mapping(0, "S21", source)["ok"])
            # Codex说明(自动生成)： 计算并保存 review，供后续语句继续读取或更新。
            review = api.preview_image_export(0)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(review["ok"], review)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.confirm_image_export(0, review["token"])["ok"])
            generated = api.generate_datasheet_network(0)
            self.assertTrue(generated["ok"], generated)
            reread = read_touchstone(generated["output"])

        np.testing.assert_array_equal(reread.s[:, 0, 0], 0.0)
        np.testing.assert_array_equal(reread.s[:, 1, 1], 0.0)
        self.assertLessEqual(generated["sigma_max"], 1.0 + 1e-12)

    # Codex说明(自动生成)： 定义函数 test_detected_defaults_are_reused_without_duplicate_ocr_or_ambiguous_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_detected_defaults_are_reused_without_duplicate_ocr_or_ambiguous_mapping(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)
        # Codex说明(自动生成)： 调用 api.set_network_parameter_family，执行当前流程需要的具体操作或副作用。
        api.set_network_parameter_family(0, "mixed-mode")
        # Codex说明(自动生成)： 计算并保存 analysis，供后续语句继续读取或更新。
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="detected",
                start_hz=10e6,
                stop_hz=18e9,
                step_hz=10e6,
                y_min_db=-9,
                y_max_db=1,
                spacing="linear",
                detected_parameter="SDD21",
            ),
        )
        # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
        first = self._stub_digitization(start_hz=10e6, stop_hz=18e9).curves[0]
        # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
        second = DigitizedCurve(
            color="Red",
            rgb=(210, 45, 55),
            frequency_hz=first.frequency_hz.copy(),
            magnitude_db=first.magnitude_db - 0.15,
            pixel_points=first.pixel_points + np.array([0.0, 2.0]),
            confidence=0.88,
        )
        # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
        digitized = DigitizationResult(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            curves=(first, second),
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "two-traces.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.ana...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                return_value=analysis,
            ):
                # Codex说明(自动生成)： 计算并保存 detected，供后续语句继续读取或更新。
                detected = api.analyze_image(0)
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=digitized,
            ) as digitize:
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                response = api.digitize_image(0, -9, 1)

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(detected["auto_digitize"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(digitize.call_args.kwargs["run_ocr"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(digitize.call_args.kwargs["parameter_hint"], "SDD21")
        # Codex说明(自动生成)： 计算并保存 curves，供后续语句继续读取或更新。
        curves = response["image_update"]["curves"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual([curve["parameter"] for curve in curves], ["SDD21", "SDD21"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual([curve["trace_number"] for curve in curves], [1, 2])
        # Codex说明(自动生成)： 计算并保存 mappings，供后续语句继续读取或更新。
        mappings = response["networks"][0]["mappings"]
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn(mappings["SDD21"], {"图1 A · SDD21", "图1 B · SDD21"})
        # Codex说明(自动生成)： 计算并保存 options，供后续语句继续读取或更新。
        options = response["networks"][0]["mapping_options"]["SDD21"]
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("图1 A · SDD21", options)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("图1 B · SDD21", options)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_update"]["digitization"]["selection"], "optional")
        # Codex说明(自动生成)： 遍历 ('图1 A · SDD21', '图1 B · SDD21') 中的 source，逐项执行循环体逻辑。
        for source in ("图1 A · SDD21", "图1 B · SDD21"):
            # 选择当前累计代价最低的候选索引。
            selected = api.set_mapping(0, "SDD21", source)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(selected["ok"], selected)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(selected["network"]["mappings"]["SDD21"], source)

    # Codex说明(自动生成)： 定义函数 test_recognized_trace_is_selectable_for_any_output_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_recognized_trace_is_selectable_for_any_output_mapping(self) -> None:
        # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
        cases = (
            ("S21", "single-ended", "S11"),
            ("SDD21", "mixed-mode", "SCC21"),
            ("SDC21", "mixed-mode", "SDD21"),
            ("SCD21", "mixed-mode", "SCC21"),
            ("SCC21", "mixed-mode", "SDC21"),
        )
        # Codex说明(自动生成)： 遍历 cases 中的 (parameter, family, incompatible_parameter)，逐项执行循环体逻辑。
        for parameter, family, incompatible_parameter in cases:
            # Codex说明(自动生成)： 进入上下文 self.subTest(parameter=parameter)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(parameter=parameter):
                # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
                api = InsertionLossWebApi()
                # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
                api.set_network_count(1)
                # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
                api.set_network_ports(0, 4 if family == "mixed-mode" else 2)
                # Codex说明(自动生成)： 调用 api.set_network_parameter_family，执行当前流程需要的具体操作或副作用。
                api.set_network_parameter_family(0, family)
                # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
                digitized = self._stub_digitization(start_hz=10e6, stop_hz=18e9)
                # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
                    image = Path(temp_dir) / f"{parameter}.png"
                    # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
                    image.write_bytes(b"\x89PNG\r\n\x1a\n")
                    # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
                    api.register_images([image])
                    # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
                    api.set_image_frequency(0, "10MHz", "18GHz", "10MHz")
                    # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
                    with mock.patch(
                        "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                        return_value=DigitizationResult(
                            image_width=digitized.image_width,
                            image_height=digitized.image_height,
                            plot_box=digitized.plot_box,
                            curves=digitized.curves,
                            detected_parameter=parameter,
                        ),
                    ):
                        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                        response = api.digitize_image(0, -10, 0)

                # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
                source = f"图1 A · {parameter}"
                # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
                network = response["networks"][0]
                # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                self.assertIn(source, network["mapping_options"][parameter])
                # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                self.assertIn(source, network["mapping_options"][incompatible_parameter])
                # 选择当前累计代价最低的候选索引。
                selected = api.set_mapping(0, incompatible_parameter, source)
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(selected["ok"], selected)
                # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                self.assertEqual(
                    selected["network"]["mappings"][incompatible_parameter], source
                )

    # Codex说明(自动生成)： 定义函数 test_ambiguous_title_stays_unassigned_after_axis_edit_and_digitization，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_ambiguous_title_stays_unassigned_after_axis_edit_and_digitization(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)
        # Codex说明(自动生成)： 调用 api.set_network_parameter_family，执行当前流程需要的具体操作或副作用。
        api.set_network_parameter_family(0, "mixed-mode")
        # Codex说明(自动生成)： 计算并保存 analysis，供后续语句继续读取或更新。
        analysis = ImageAnalysis(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            calibration=AxisCalibration(
                status="detected",
                start_hz=10e6,
                stop_hz=18e9,
                step_hz=10e6,
                y_min_db=-50,
                y_max_db=50,
                spacing="linear",
                detected_parameter=None,
                warnings=(
                    "Multiple S-parameter labels were found; choose the mapping manually.",
                ),
            ),
        )
        # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
        first = self._stub_digitization(start_hz=10e6, stop_hz=18e9).curves[0]
        # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
        second = DigitizedCurve(
            color="Red",
            rgb=(210, 45, 55),
            frequency_hz=first.frequency_hz.copy(),
            magnitude_db=first.magnitude_db - 0.15,
            pixel_points=first.pixel_points + np.array([0.0, 2.0]),
            confidence=0.88,
        )
        # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
        digitized = DigitizationResult(
            image_width=640,
            image_height=480,
            plot_box=(80, 50, 560, 410),
            curves=(first, second),
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "ambiguous-title.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.ana...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.analyze_plot_image",
                return_value=analysis,
            ):
                # Codex说明(自动生成)： 计算并保存 analyzed，供后续语句继续读取或更新。
                analyzed = api.analyze_image(0)
            # Codex说明(自动生成)： 计算并保存 edited，供后续语句继续读取或更新。
            edited = api.set_image_frequency(0, "10MHz", "18GHz", "10MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=digitized,
            ) as digitize:
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                response = api.digitize_image(0, -50, 50)

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(analyzed["auto_digitize"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(edited["ok"], edited)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(digitize.call_args.kwargs["run_ocr"])
        # Codex说明(自动生成)： 调用 self.assertIsNone 检查测试期望，确认实际结果符合预期。
        self.assertIsNone(response["image_update"]["digitization"]["detected_parameter"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            [curve["parameter"] for curve in response["image_update"]["curves"]],
            ["自动", "自动"],
        )
        # Codex说明(自动生成)： 遍历 ('SDD11', 'SDD21') 中的 parameter，逐项执行循环体逻辑。
        for parameter in ("SDD11", "SDD21"):
            # Codex说明(自动生成)： 计算并保存 choices，供后续语句继续读取或更新。
            choices = response["networks"][0]["mapping_options"][parameter]
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(any(choice.startswith("图1 A") for choice in choices))
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(any(choice.startswith("图1 B") for choice in choices))

    # Codex说明(自动生成)： 定义函数 test_detected_parameter_is_a_hint_not_an_automatic_cross_family_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_detected_parameter_is_a_hint_not_an_automatic_cross_family_mapping(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "sdd21.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\nsdd21")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "10MHz", "18GHz", "10MHz")
            # Codex说明(自动生成)： 计算并保存 detected，供后续语句继续读取或更新。
            detected = self._stub_digitization(
                start_hz=10e6,
                stop_hz=18e9,
            )
            # Codex说明(自动生成)： 计算并保存 detected，供后续语句继续读取或更新。
            detected = DigitizationResult(
                image_width=detected.image_width,
                image_height=detected.image_height,
                plot_box=detected.plot_box,
                curves=detected.curves,
                detected_parameter="SDD21",
            )
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                response = api.digitize_image(0, -10, 0)

        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = "图1 A · SDD21"
        # Codex说明(自动生成)： 计算并保存 single_ended，供后续语句继续读取或更新。
        single_ended = response["networks"][0]
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("SDD21", response["detected_parameters"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(source, single_ended["mapping_options"]["S11"])
        # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
        self.assertNotEqual(single_ended["mappings"]["S11"], source)

        # Codex说明(自动生成)： 计算并保存 switched，供后续语句继续读取或更新。
        switched = api.set_network_parameter_family(0, "mixed-mode")
        # Codex说明(自动生成)： 计算并保存 mixed_mode，供后续语句继续读取或更新。
        mixed_mode = switched["network"]
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(source, mixed_mode["mapping_options"]["SDD21"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(mixed_mode["mappings"]["SDD21"], source)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(source, mixed_mode["mapping_options"]["SDD12"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(mixed_mode["mappings"]["SDD12"], source)

    def test_unequal_source_traces_report_one_common_frequency_grid(self) -> None:
        """UI totals describe the output grid, while source coverage stays explicit."""

        api = InsertionLossWebApi()
        full_frequency = np.linspace(1e9, 5e9, 5)
        partial_frequency = np.linspace(2e9, 4e9, 3)
        digitized = DigitizationResult(
            image_width=100,
            image_height=80,
            plot_box=(10, 10, 90, 70),
            curves=(
                DigitizedCurve(
                    color="Dark blue",
                    rgb=(36, 76, 206),
                    frequency_hz=full_frequency,
                    magnitude_db=np.linspace(-1.0, -5.0, 5),
                    pixel_points=np.column_stack(
                        (np.linspace(10, 90, 5), np.linspace(20, 50, 5))
                    ),
                    confidence=0.9,
                    observed_samples=5,
                ),
                DigitizedCurve(
                    color="Red",
                    rgb=(210, 45, 55),
                    frequency_hz=partial_frequency,
                    magnitude_db=np.linspace(-2.0, -4.0, 3),
                    pixel_points=np.column_stack(
                        (np.linspace(30, 70, 3), np.linspace(25, 45, 3))
                    ),
                    confidence=0.8,
                    observed_samples=3,
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "unlabelled-curves.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            api.register_images([image])
            api.set_image_frequency(0, "1GHz", "5GHz", "1GHz")
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=digitized,
            ):
                response = api.digitize_image(0, -10, 0)

        curves = response["image_update"]["curves"]
        self.assertEqual([curve["samples"] for curve in curves], [5, 5])
        self.assertEqual([curve["source_samples"] for curve in curves], [5, 3])
        self.assertEqual([curve["covered_samples"] for curve in curves], [5, 3])
        self.assertEqual([curve["unresolved_samples"] for curve in curves], [0, 2])
        self.assertEqual([curve["parameter"] for curve in curves], ["自动", "自动"])

    # Codex说明(自动生成)： 定义函数 test_s31_trace_can_drive_s12_without_changing_curve_values，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s31_trace_can_drive_s12_without_changing_curve_values(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 4)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 计算并保存 digitized，供后续语句继续读取或更新。
        digitized = self._stub_digitization(start_hz=10e6, stop_hz=18e9)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "s31.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "10MHz", "18GHz", "4497.5MHz")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=DigitizationResult(
                    image_width=digitized.image_width,
                    image_height=digitized.image_height,
                    plot_box=digitized.plot_box,
                    curves=digitized.curves,
                    detected_parameter="S31",
                ),
            ):
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                response = api.digitize_image(0, -10, 0)

        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = "图1 A · S31"
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = response["networks"][0]
        # Codex说明(自动生成)： 遍历 network['mappings'] 中的 destination，逐项执行循环体逻辑。
        for destination in network["mappings"]:
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn(source, network["mapping_options"][destination])
        # 选择当前累计代价最低的候选索引。
        selected = api.set_mapping(0, "S12", source)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(selected["ok"], selected)
        # Codex说明(自动生成)： 计算并保存 (frequency_hz, magnitudes)，供后续语句继续读取或更新。
        frequency_hz, magnitudes = api._datasheet.compose_network_magnitudes(0)
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(
            frequency_hz,
            np.linspace(10e6, 18e9, 5),
            rtol=0,
            atol=1e-6,
        )
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(
            magnitudes["S12"],
            np.linspace(-1.0, -4.0, 5),
            rtol=0,
            atol=1e-12,
        )

    # Codex说明(自动生成)： 定义函数 test_user_can_explicitly_relabel_a_detected_curve_for_sij_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_user_can_explicitly_relabel_a_detected_curve_for_sij_mapping(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "sdd21.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\nsdd21")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([image])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "10MHz", "18GHz", "10MHz")
            # Codex说明(自动生成)： 计算并保存 detected，供后续语句继续读取或更新。
            detected = self._stub_digitization(start_hz=10e6, stop_hz=18e9)
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=DigitizationResult(
                    image_width=detected.image_width,
                    image_height=detected.image_height,
                    plot_box=detected.plot_box,
                    curves=detected.curves,
                    detected_parameter="SDD21",
                ),
            ):
                # Codex说明(自动生成)： 调用 api.digitize_image，执行当前流程需要的具体操作或副作用。
                api.digitize_image(0, -10, 0)

            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.set_curve_parameter(0, "A", "S11")

        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = "图1 A · S11"
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["image_update"]["curves"][0]["parameter"], "S11")
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(source, response["networks"][0]["mapping_options"]["S11"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(response["networks"][0]["mappings"]["S11"], source)

    # Codex说明(自动生成)： 定义函数 test_network_coverage_uses_intersection_of_only_mapped_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_network_coverage_uses_intersection_of_only_mapped_images(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = DatasheetWorkspace()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = Path(temp_dir) / "fine.png"
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = Path(temp_dir) / "coarse.png"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(b"\x89PNG\r\n\x1a\n")
            # Codex说明(自动生成)： 调用 second.write_bytes 写出文件或数据，保存当前处理结果。
            second.write_bytes(b"\x89PNG\r\n\x1a\ncoarse")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([first, second])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "10MHz", "18GHz", "10MHz", "linear")
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(1, "100MHz", "16GHz", "50MHz", "linear")
            # Codex说明(自动生成)： 计算并保存 unequal_digitizations，供后续语句继续读取或更新。
            unequal_digitizations = (
                self._stub_digitization(
                    start_hz=10e6, stop_hz=18e9, _points=5
                ),
                self._stub_digitization(
                    start_hz=100e6, stop_hz=16e9, _points=8
                ),
            )
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=unequal_digitizations,
            ):
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(0, -10, 0)["ok"])
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(1, -10, 0)["ok"])
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S11", "图1 A · 深蓝")
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.set_mapping(0, "S21", "图2 A · 深蓝")

        # Codex说明(自动生成)： 计算并保存 coverage，供后续语句继续读取或更新。
        coverage = response["network"]["coverage"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["status"], "ready")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["start_hz"], 100e6)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["stop_hz"], 16e9)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["source_images"], [1, 2])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(coverage["uses_interpolation"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(coverage["uniform"])
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(coverage["points"], 2)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(set(coverage["channel_points"].values()), {coverage["points"]})
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["source_sample_counts"], {
            "图1 A · 深蓝": 5,
            "图2 A · 深蓝": 8,
        })
        # Codex说明(自动生成)： 计算并保存 (frequency_hz, magnitudes)，供后续语句继续读取或更新。
        frequency_hz, magnitudes = api.compose_network_magnitudes(0)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(frequency_hz.size, coverage["points"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual({values.size for values in magnitudes.values()}, {coverage["points"]})
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(magnitudes["S12"], np.full(coverage["points"], -80.0))
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(magnitudes["S22"], np.full(coverage["points"], -20.0))
        # Codex说明(自动生成)： 计算并保存 expected_s11_start，供后续语句继续读取或更新。
        expected_s11_start = -1.0 - 3.0 * ((100e6 - 10e6) / (18e9 - 10e6))
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(magnitudes["S11"][0]), expected_s11_start, places=12)
        # Codex说明(自动生成)： 计算并保存 manual，供后续语句继续读取或更新。
        manual = api.set_network_frequency_policy(
            0, "manual", "100MHz", "16GHz", "10MHz", False
        )
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(manual["ok"], manual)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(manual["network"]["coverage"]["points"], 1591)
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(
            api.set_network_frequency_policy(0, "union", "", "", "", False)["ok"]
        )
        # Codex说明(自动生成)： 计算并保存 union，供后续语句继续读取或更新。
        union = api.set_network_frequency_policy(0, "union", "", "", "", True)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(union["ok"], union)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(union["network"]["coverage"]["uses_fill"])

    # Codex说明(自动生成)： 定义函数 test_default_only_channels_require_and_then_share_one_manual_grid，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_default_only_channels_require_and_then_share_one_manual_grid(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = DatasheetWorkspace()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)

        # Codex说明(自动生成)： 计算并保存 initial，供后续语句继续读取或更新。
        initial = api.payload()["networks"][0]["coverage"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(initial["status"], "needs-grid")

        # Codex说明(自动生成)： 计算并保存 rejected，供后续语句继续读取或更新。
        rejected = api.set_network_frequency_policy(
            0, "manual", "1GHz", "2GHz", "300MHz", False
        )
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(rejected["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("不能整除", rejected["error"])

        # Codex说明(自动生成)： 计算并保存 accepted，供后续语句继续读取或更新。
        accepted = api.set_network_frequency_policy(
            0, "manual", "10MHz", "18GHz", "10MHz", False
        )
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(accepted["ok"], accepted)
        # Codex说明(自动生成)： 计算并保存 coverage，供后续语句继续读取或更新。
        coverage = accepted["network"]["coverage"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["status"], "ready")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["points"], 1800)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(coverage["step_hz"], 10e6)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(set(coverage["channel_points"].values()), {1800})
        # Codex说明(自动生成)： 计算并保存 (frequency_hz, magnitudes)，供后续语句继续读取或更新。
        frequency_hz, magnitudes = api.compose_network_magnitudes(0)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(frequency_hz.size, 1800)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual({values.size for values in magnitudes.values()}, {1800})

    # Codex说明(自动生成)： 定义函数 test_disjoint_images_can_use_explicit_union_fill，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_disjoint_images_can_use_explicit_union_fill(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 调用 api.set_network_count，执行当前流程需要的具体操作或副作用。
        api.set_network_count(1)
        # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
        api.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        api.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = Path(temp_dir) / "left.png"
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = Path(temp_dir) / "right.png"
            # Codex说明(自动生成)： 调用 first.write_bytes 写出文件或数据，保存当前处理结果。
            first.write_bytes(b"\x89PNG\r\n\x1a\nleft")
            # Codex说明(自动生成)： 调用 second.write_bytes 写出文件或数据，保存当前处理结果。
            second.write_bytes(b"\x89PNG\r\n\x1a\nright")
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([first, second])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "1GHz", "2GHz", "10MHz", "linear")
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(1, "3GHz", "4GHz", "10MHz", "linear")
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                side_effect=self._stub_digitization,
            ):
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(0, -10, 0)["ok"])
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(api.digitize_image(1, -10, 0)["ok"])
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S11", "图1 A · 深蓝")
            # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
            api.set_mapping(0, "S21", "图2 A · 深蓝")

        # Codex说明(自动生成)： 计算并保存 rejected，供后续语句继续读取或更新。
        rejected = api.set_network_frequency_policy(0, "union", "", "", "", False)
        # Codex说明(自动生成)： 计算并保存 accepted，供后续语句继续读取或更新。
        accepted = api.set_network_frequency_policy(0, "union", "", "", "", True)

        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(rejected["ok"])
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(accepted["ok"], accepted)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(accepted["network"]["coverage"]["status"], "ready")
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(accepted["network"]["coverage"]["uses_fill"])

    # Codex说明(自动生成)： 定义函数 test_mixed_mode_conversion_fill_uses_coupling_not_reflection_default，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_mixed_mode_conversion_fill_uses_coupling_not_reflection_default(self) -> None:
        # Codex说明(自动生成)： 计算并保存 workspace，供后续语句继续读取或更新。
        workspace = DatasheetWorkspace()
        # Codex说明(自动生成)： 调用 workspace.set_network_count，执行当前流程需要的具体操作或副作用。
        workspace.set_network_count(1)
        # Codex说明(自动生成)： 调用 workspace.set_network_ports，执行当前流程需要的具体操作或副作用。
        workspace.set_network_ports(0, 2)
        # Codex说明(自动生成)： 调用 workspace.set_network_parameter_family，执行当前流程需要的具体操作或副作用。
        workspace.set_network_parameter_family(0, "mixed-mode")
        # Codex说明(自动生成)： 调用 workspace.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
        workspace.set_network_reciprocal(0, False)
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = Path(temp_dir) / "sdc11.png"
            # Codex说明(自动生成)： 调用 image.write_bytes 写出文件或数据，保存当前处理结果。
            image.write_bytes(b"\x89PNG\r\n\x1a\nmixed-mode-fill")
            # Codex说明(自动生成)： 调用 workspace.register_images，执行当前流程需要的具体操作或副作用。
            workspace.register_images([image])
            # Codex说明(自动生成)： 调用 workspace.set_image_frequency，执行当前流程需要的具体操作或副作用。
            workspace.set_image_frequency(0, "1GHz", "3GHz", "500MHz", "linear")
            # Codex说明(自动生成)： 计算并保存 detected，供后续语句继续读取或更新。
            detected = self._stub_digitization(
                start_hz=1e9, stop_hz=3e9, _points=5
            )
            # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.datasheet_workspace.dig...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch(
                "insertion_loss_tool.datasheet_workspace.digitize_plot_image",
                return_value=detected,
            ):
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(workspace.digitize_image(0, -10, 0)["ok"])
            # Codex说明(自动生成)： 调用 workspace.set_curve_parameter，执行当前流程需要的具体操作或副作用。
            workspace.set_curve_parameter(0, "A", "SDC11")
            # Codex说明(自动生成)： 调用 workspace.set_mapping，执行当前流程需要的具体操作或副作用。
            workspace.set_mapping(0, "SDC11", "图1 A · SDC11")

        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = workspace.set_network_frequency_policy(
            0, "manual", "500MHz", "3.5GHz", "500MHz", True
        )
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(response["ok"], response)
        # Codex说明(自动生成)： 计算并保存 (_, magnitudes)，供后续语句继续读取或更新。
        _, magnitudes = workspace.compose_network_magnitudes(0)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(float(magnitudes["SDC11"][0]), -80.0)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(float(magnitudes["SDC11"][-1]), -80.0)

    # Codex说明(自动生成)： 定义函数 test_web_api_generates_all_four_modes_on_the_real_backend，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_web_api_generates_all_four_modes_on_the_real_backend(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(temp_dir)
            # Codex说明(自动生成)： 计算并保存 base，供后续语句继续读取或更新。
            base = {
                "ports": "2",
                "f_start": "1GHz",
                "f_stop": "5GHz",
                "points": "17",
                "spacing": "linear",
                "format": "ri",
                "frequency_unit": "ghz",
                "return_loss_db": "20",
                "crosstalk_db": "80",
                "delay_ps": "25",
                "phase_offset_deg": "0",
                "z0": "50",
                "through_pairs": "",
            }
            # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
            cases = [
                ("linear", {"loss_start_db": "0.5", "loss_stop_db": "6"}),
                ("formula", {"a": "0.08", "b": "0.6", "c": "0.1", "model_frequency_unit": "ghz"}),
                ("draw", {"control_points": "1GHz:-1,2.5GHz:-4,5GHz:-2.5", "fit": "smooth", "fit_domain": "linear", "min_spacing_fraction": "0.0001", "max_slope_db_per_span": "500"}),
            ]
            # Codex说明(自动生成)： 声明并保存 outputs，同时保留类型信息方便维护和静态检查。
            outputs: dict[str, Path] = {}
            # Codex说明(自动生成)： 遍历 cases 中的 (mode, specific)，逐项执行循环体逻辑。
            for mode, specific in cases:
                # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                output = folder / f"{mode}.s2p"
                # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
                response = api.run_generation_sync({**base, **specific, "mode": mode, "output": str(output)})
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(response["ok"], response)
                # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                self.assertTrue(output.is_file())
                # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                self.assertEqual(len(response["plot"]["series"]), 4)
                # Codex说明(自动生成)： 计算并保存 outputs[mode]，供后续语句继续读取或更新。
                outputs[mode] = output

            # Codex说明(自动生成)： 计算并保存 repeated，供后续语句继续读取或更新。
            repeated = api.run_generation_sync(
                {**base, **cases[0][1], "mode": "linear", "output": str(outputs["linear"])}
            )
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(repeated["ok"])
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("已存在", repeated["error"])
            # Codex说明(自动生成)： 计算并保存 overwritten，供后续语句继续读取或更新。
            overwritten = api.run_generation_sync(
                {
                    **base,
                    **cases[0][1],
                    "mode": "linear",
                    "output": str(outputs["linear"]),
                    "overwrite": True,
                }
            )
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(overwritten["ok"], overwritten)

            # Codex说明(自动生成)： 计算并保存 invalid_draw，供后续语句继续读取或更新。
            invalid_draw = api.run_generation_sync(
                {**base, "mode": "draw", "control_points": "1GHz:-1", "output": str(folder / "bad.s2p")}
            )
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(invalid_draw["ok"])
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("至少需要 2 个控制点", invalid_draw["error"])

            # Codex说明(自动生成)： 计算并保存 modify_output，供后续语句继续读取或更新。
            modify_output = folder / "modified.s2p"
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.run_generation_sync(
                {
                    **base,
                    "mode": "modify",
                    "input": str(outputs["linear"]),
                    "output": str(modify_output),
                    "targets": "3GHz:2",
                    "pairs": "S21,S12",
                    "smoothness": "0.18",
                    "smooth_domain": "log",
                    "anchor_edges": True,
                    "insert_targets": True,
                }
            )
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(response["ok"], response)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(modify_output.with_suffix(".s2p.report.txt").is_file())
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(modify_output)
            # Codex说明(自动生成)： 计算并保存 index，供后续语句继续读取或更新。
            index = list(loaded.frequency_hz).index(3e9)
            # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
            self.assertAlmostEqual(float(to_magnitude_db(loaded.s[index, 1, 0])), -2.0, places=6)

    # Codex说明(自动生成)： 定义函数 test_js_bridge_is_a_small_allow_list，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_js_bridge_is_a_small_allow_list(self) -> None:
        # Codex说明(自动生成)： 计算并保存 exposed，供后续语句继续读取或更新。
        exposed = {name for name in dir(InsertionLossJsApi(InsertionLossWebApi())) if not name.startswith("_")}
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            exposed,
            {
                "image_edit_recipe", "apply_image_recipe", "undo_image_recipe",
                "export_image_asset", "preview_image_export", "confirm_image_export",
                "set_image_network_model",
                "choose_images",
                "choose_input",
                "choose_output",
                "analyze_image",
                "digitize_image",
                "digitize_image_with_axis",
                "generate_datasheet_network",
                "get_defaults",
                "inspect_input",
                "open_output_dir",
                "open_datasheet_output_dir",
                "remove_image",
                "run_generation",
                "set_curve_parameter",
                "set_image_frequency",
                "set_mapping",
                "set_network_count",
                "set_network_frequency_policy",
                "set_network_parameter_family",
                "set_network_ports",
                "set_network_reciprocal",
            },
        )

    # Codex说明(自动生成)： 定义函数 test_datasheet_ui_shows_the_uniform_output_grid_summary，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_ui_shows_the_uniform_output_grid_summary(self) -> None:
        # Codex说明(自动生成)： 计算并保存 html，供后续语句继续读取或更新。
        html = load_web_ui()

        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Set Manual Start / Stop / Step", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Step ${formatFrequency(coverage.step_hz)}", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("${coverage.points} points", html)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("coverage.resampled_channels", html)

    # Codex说明(自动生成)： 定义函数 test_public_entrypoints_and_packages_use_webview，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_public_entrypoints_and_packages_use_webview(self) -> None:
        # Codex说明(自动生成)： 计算并保存 project，供后续语句继续读取或更新。
        project = Path(__file__).resolve().parents[1]
        # Codex说明(自动生成)： 计算并保存 pyproject，供后续语句继续读取或更新。
        pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            pyproject["project"]["scripts"]["insertion-loss-tool"],
            "insertion_loss_tool.webview_gui:main",
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("pywebview==6.2.1", pyproject["project"]["dependencies"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(insertion_loss_tool.__version__, pyproject["project"]["version"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            pyproject["tool"]["setuptools"]["package-data"]["insertion_loss_tool"],
            ["webui/*.html"],
        )
        # Codex说明(自动生成)： 计算并保存 launcher，供后续语句继续读取或更新。
        launcher = (project / "gui_main.py").read_text(encoding="utf-8")
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('import_module("insertion_loss_tool.webview_gui")', launcher)
        # Codex说明(自动生成)： 遍历 ('build_macos_app.command', 'build_windows_exe.bat') 中的 build_name，逐项执行循环体逻辑。
        for build_name in ("build_macos_app.command", "build_windows_exe.bat"):
            # Codex说明(自动生成)： 计算并保存 build，供后续语句继续读取或更新。
            build = (project / build_name).read_text(encoding="utf-8")
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("insertion_loss_tool.webview_gui", build)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("webui", build)

    # Codex说明(自动生成)： 定义函数 test_async_generation_rejects_a_second_run，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_async_generation_rejects_a_second_run(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 声明并保存 created，同时保留类型信息方便维护和静态检查。
        created: list[dict[str, object]] = []

        # Codex说明(自动生成)： 定义 HeldThread 类，把相关数据结构、校验规则或操作方法组织在一起。
        class HeldThread:
            # Codex说明(自动生成)： 定义函数 __init__，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
            def __init__(self, **kwargs: object) -> None:
                # Codex说明(自动生成)： 调用 created.append 更新列表或集合，把当前步骤产生的数据加入结果。
                created.append(kwargs)

            # Codex说明(自动生成)： 定义函数 start，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
            def start(self) -> None:
                # Codex说明(自动生成)： 返回 None，让调用方取得本函数的处理结果。
                return None

        # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.threading.T...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch("insertion_loss_tool.webview_gui.threading.Thread", HeldThread):
            # Codex说明(自动生成)： 计算并保存 first，供后续语句继续读取或更新。
            first = api.run_generation({})
            # Codex说明(自动生成)： 计算并保存 second，供后续语句继续读取或更新。
            second = api.run_generation({})
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(first["ok"])
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(second["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("正在生成", second["error"])
        # Codex说明(自动生成)： 进入上下文 mock.patch.object(api, 'run_generation_sync', return_va...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch.object(api, "run_generation_sync", return_value={"ok": True}):
            # Codex说明(自动生成)： 调用 created[0]['target']，执行当前流程需要的具体操作或副作用。
            created[0]["target"](*created[0]["args"])
        # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.threading.T...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch("insertion_loss_tool.webview_gui.threading.Thread", HeldThread):
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(api.run_generation({})["ok"])

    # Codex说明(自动生成)： 定义函数 test_async_generation_reports_thread_start_failure，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_async_generation_reports_thread_start_failure(self) -> None:
        # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
        api = InsertionLossWebApi()
        # Codex说明(自动生成)： 计算并保存 blocker，供后续语句继续读取或更新。
        blocker = mock.Mock()
        # Codex说明(自动生成)： 计算并保存 blocker.start.side_effect，供后续语句继续读取或更新。
        blocker.start.side_effect = RuntimeError("thread unavailable")
        # Codex说明(自动生成)： 进入上下文 mock.patch('insertion_loss_tool.webview_gui.threading.T...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch("insertion_loss_tool.webview_gui.threading.Thread", return_value=blocker):
            # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
            response = api.run_generation({})
        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
        self.assertFalse(response["ok"])
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("无法启动", response["error"])


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 调用 unittest.main，执行当前流程需要的具体操作或副作用。
    unittest.main()
