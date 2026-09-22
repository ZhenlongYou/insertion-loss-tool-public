"""Wilder 压缩退化回归：修线锚点与冻结像素核对点分开。"""

# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 unittest.mock 导入 patch，组织单元测试和断言。
from unittest.mock import patch
# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np
# Codex说明(自动生成)： 从 PIL 导入 Image，提供本文件后续流程需要的库能力。
from PIL import Image
# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi, InsertionLossJsApi，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import InsertionLossWebApi, InsertionLossJsApi

# Codex说明(自动生成)： 计算并保存 CORPUS，供后续语句继续读取或更新。
CORPUS = Path(
    os.environ.get(
        "IMAGE_REPAIR_CORPUS",
        str(Path(__file__).parent / "validation" / "cross_vendor_trace_recovery" / "local_corpus"),
    )
)
# Codex说明(自动生成)： 计算并保存 HELDOUT，供后续语句继续读取或更新。
HELDOUT = {
    "Rx RL": {576: 755, 585: 762, 1349: 695, 1411: 704, 1453: 710},
    "Tx RL": {
        1265: 704,
        1280: 698,
        1289: 698,
        1338: 688,
        1349: 695,
        1357: 706,
        1367: 701,
        1377: 687,
    },
}
# Codex说明(自动生成)： 计算并保存 COLOURS，供后续语句继续读取或更新。
COLOURS = {
    "Tx IL": [255, 131, 132],
    "Rx IL": [126, 125, 255],
    "Tx RL": [151, 202, 152],
    "Rx RL": [146, 173, 198],
}


# Codex说明(自动生成)： 定义 WilderCorrectionTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class WilderCorrectionTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_four_variants_recipe_export_and_independent_readback，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_four_variants_recipe_export_and_independent_readback(self):
        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = CORPUS / "wilder-910-0077-fig36.png"
        # Codex说明(自动生成)： 检查条件 not source.exists()，根据结果选择后续执行路径。
        if not source.exists():
            # Codex说明(自动生成)： 调用 self.skipTest，执行当前流程需要的具体操作或副作用。
            self.skipTest("Licensed Wilder corpus unavailable; set IMAGE_REPAIR_CORPUS")
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory(), Image.open(source)，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as directory, Image.open(source) as image:
            # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
            folder = Path(directory)
            # Codex说明(自动生成)： 遍历 [('original', 1), ('scale075', 0.75), ('scale125', 1.25... 中的 (name, scale)，逐项执行循环体逻辑。
            for name, scale in [
                ("original", 1),
                ("scale075", 0.75),
                ("scale125", 1.25),
                ("jpeg90", 1),
            ]:
                # Codex说明(自动生成)： 进入上下文 self.subTest(variant=name)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(variant=name):
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = folder / (name + (".jpg" if name == "jpeg90" else ".png"))
                    # Codex说明(自动生成)： 计算并保存 variant，供后续语句继续读取或更新。
                    variant = image.convert("RGB").resize(
                        (round(image.width * scale), round(image.height * scale)),
                        Image.Resampling.LANCZOS,
                    )
                    # Codex说明(自动生成)： 调用 variant.save，执行当前流程需要的具体操作或副作用。
                    variant.save(path, **({"quality": 90} if name == "jpeg90" else {}))
                    # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
                    api = InsertionLossWebApi()
                    # Codex说明(自动生成)： 计算并保存 bridge，供后续语句继续读取或更新。
                    bridge = InsertionLossJsApi(api)
                    # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
                    api.register_images([path])
                    # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
                    api.set_image_frequency(0, "0.05GHz", "40GHz", "0.05GHz")
                    # Codex说明(自动生成)： 计算并保存 recipe，供后续语句继续读取或更新。
                    recipe = bridge.image_edit_recipe(0)["recipe"]
                    # Codex说明(自动生成)： 调用 recipe.update，执行当前流程需要的具体操作或副作用。
                    recipe.update(
                        plot_box=[round(x * scale) for x in [200, 98, 1464, 1029]],
                        exclusions=[[round(x * scale) for x in [1230, 115, 1460, 250]]],
                        traces=[
                            {
                                "id": n,
                                "label": n,
                                "rgb": c,
                                "anchors": (
                                    [[1380, 695], [1460, 710]]
                                    if name == "jpeg90" and n == "Rx RL"
                                    else (
                                        [[200, 565]]
                                        if name == "jpeg90" and n == "Tx IL"
                                        else []
                                    )
                                ),
                            }
                            for n, c in COLOURS.items()
                        ],
                    )
                    # Codex说明(自动生成)： 调用 recipe['axis'].update，执行当前流程需要的具体操作或副作用。
                    recipe["axis"].update(
                        y_top_db=50, y_bottom_db=-50, y_convention="magnitude"
                    )
                    # Codex说明(自动生成)： 计算并保存 applied，供后续语句继续读取或更新。
                    applied = bridge.apply_image_recipe(0, recipe)
                    # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                    self.assertTrue(applied["ok"], applied)
                    # Codex说明(自动生成)： 计算并保存 curves，供后续语句继续读取或更新。
                    curves = applied["image_update"]["curves"]
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(len(curves), 4)
                    # 5 像素仅是冻结栅格点的局部验收界限，不表示整图或 dB 精度。
                    for curve in curves:
                        # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
                        points = np.asarray(curve["source_pixel_points"]) / scale
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(points[0, 0], round(200 * scale) / scale)
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(points[-1, 0], round(1464 * scale) / scale)
                        # Codex说明(自动生成)： 遍历 HELDOUT.get(curve['label'], {}).items() 中的 (x, y)，逐项执行循环体逻辑。
                        for x, y in HELDOUT.get(curve["label"], {}).items():
                            # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
                            self.assertLessEqual(
                                abs(np.interp(x, points[:, 0], points[:, 1]) - y), 5
                            )
                    # Codex说明(自动生成)： 检查条件 name == 'jpeg90'，根据结果选择后续执行路径。
                    if name == "jpeg90":
                        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                        self.assertIn("manual_guided", curves[3]["sample_provenance"])
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(curves[3]["review_status"], "review")
                    # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
                    api.set_network_ports(0, 2)
                    # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
                    api.set_network_reciprocal(0, False)
                    # Codex说明(自动生成)： 计算并保存 options，供后续语句继续读取或更新。
                    options = api.get_defaults()["datasheet"]["networks"][0][
                        "mapping_options"
                    ]["S11"]
                    # 选择当前累计代价最低的候选索引。
                    selected = next(s for s in options if s.startswith("图1 D"))
                    # Codex说明(自动生成)： 遍历 ('S11', 'S12', 'S21', 'S22') 中的 p，逐项执行循环体逻辑。
                    for p in ("S11", "S12", "S21", "S22"):
                        # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
                        api.set_mapping(0, p, selected if p == "S11" else "匹配 0")
                    # 同一真实 facade 导出；独立解析 RI 行，不使用生产读取器验证自身。
                    with patch(
                        "insertion_loss_tool.webview_gui.OUTPUT_DIR", folder / "exports"
                    ):
                        # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
                        self.assertFalse(bridge.generate_datasheet_network(0)["ok"])
                        # Codex说明(自动生成)： 计算并保存 preview，供后续语句继续读取或更新。
                        preview = bridge.preview_image_export(0)
                        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                        self.assertTrue(preview["ok"], preview)
                        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                        self.assertTrue(
                            bridge.confirm_image_export(0, preview["token"])["ok"]
                        )
                        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                        output = bridge.generate_datasheet_network(0)
                        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                        self.assertTrue(output["ok"], output)
                        # Codex说明(自动生成)： 计算并保存 lines，供后续语句继续读取或更新。
                        lines = Path(output["output"]).read_text().splitlines()
                        # 将图框内 RGB 转为浮点，避免无符号像素减法溢出。
                        values = np.asarray(
                            [
                                [float(x) for x in line.split()]
                                for line in lines
                                if line and not line.startswith(("!", "#"))
                            ]
                        )
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(values.shape, (800, 9))
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(values[0, 0], 50e6)
                        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                        self.assertEqual(values[-1, 0], 40e9)
                        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
                        self.assertTrue(np.all(np.diff(values[:, 0]) == 50e6))
                        # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
                        points = np.asarray(curves[3]["source_pixel_points"])
                        # Codex说明(自动生成)： 计算并保存 box，供后续语句继续读取或更新。
                        box = recipe["plot_box"]
                        # Codex说明(自动生成)： 计算并保存 raw_f，供后续语句继续读取或更新。
                        raw_f = 50e6 + (points[:, 0] - box[0]) * 39.95e9 / (
                            box[2] - box[0]
                        )
                        # Codex说明(自动生成)： 计算并保存 raw_db，供后续语句继续读取或更新。
                        raw_db = 50 - (points[:, 1] - box[1]) * 100 / (box[3] - box[1])
                        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
                        np.testing.assert_allclose(
                            20 * np.log10(abs(values[:, 1] + 1j * values[:, 2])),
                            np.interp(values[:, 0], raw_f, raw_db),
                            atol=1e-8,
                        )
                        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                        self.assertIn("Image provenance:", "\n".join(lines))
                    # Codex说明(自动生成)： 调用 path.write_bytes 写出文件或数据，保存当前处理结果。
                    path.write_bytes(b"changed source")
                    # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
                    self.assertFalse(bridge.preview_image_export(0)["ok"])
