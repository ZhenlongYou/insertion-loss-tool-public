"""公开图片导出路径的缺陷回归；原图来自本机版权样本。"""

# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 从 unittest.mock 导入 patch，组织单元测试和断言。
from unittest.mock import patch

# Codex说明(自动生成)： 从 PIL 导入 Image，提供本文件后续流程需要的库能力。
from PIL import Image
# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import InsertionLossWebApi


# Codex说明(自动生成)： 定义 ImageExportReviewTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class ImageExportReviewTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_partial_wilder_trace_cannot_export_without_review，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_partial_wilder_trace_cannot_export_without_review(self):
        # 用用户手册的栅格变体复现残线，而不是向内部状态伪造一条坏曲线。
        corpus = Path(
            os.environ.get(
                "IMAGE_REPAIR_CORPUS",
                str(Path(__file__).parent / "validation" / "cross_vendor_trace_recovery" / "local_corpus"),
            )
        )
        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = corpus / "wilder-910-0077-fig36.png"
        # Codex说明(自动生成)： 检查条件 not source.exists()，根据结果选择后续执行路径。
        if not source.exists():
            # Codex说明(自动生成)： 调用 self.skipTest，执行当前流程需要的具体操作或副作用。
            self.skipTest("Wilder licensed local corpus unavailable")
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as directory:
            # 放大只属于测试扰动，生产入口不得强制放大用户图片。
            folder = Path(directory)
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = folder / "wilder125.png"
            # Codex说明(自动生成)： 进入上下文 Image.open(source)，确保文件、资源或临时状态按作用域正确释放。
            with Image.open(source) as image:
                # Codex说明(自动生成)： 调用 image.resize((2200, 1625), Image.Resampling.LANCZOS).save，执行当前流程需要的具体操作或副作用。
                image.resize((2200, 1625), Image.Resampling.LANCZOS).save(path)
            # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
            api = InsertionLossWebApi()
            # Codex说明(自动生成)： 调用 api.register_images，执行当前流程需要的具体操作或副作用。
            api.register_images([path])
            # Codex说明(自动生成)： 调用 api.set_image_frequency，执行当前流程需要的具体操作或副作用。
            api.set_image_frequency(0, "0.05GHz", "40GHz", "0.05GHz", "linear")
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = api.digitize_image_with_axis(0, 50, -50, "magnitude")
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(result["ok"], result)
            # Codex说明(自动生成)： 调用 api.set_network_ports，执行当前流程需要的具体操作或副作用。
            api.set_network_ports(0, 2)
            # Codex说明(自动生成)： 调用 api.set_network_reciprocal，执行当前流程需要的具体操作或副作用。
            api.set_network_reciprocal(0, False)
            # Codex说明(自动生成)： 计算并保存 choices，供后续语句继续读取或更新。
            choices = api.get_defaults()["datasheet"]["networks"][0]["mapping_options"][
                "S11"
            ]
            # Codex说明(自动生成)： 计算并保存 candidate，供后续语句继续读取或更新。
            candidate = next(x for x in choices if "深蓝" in x)
            # Codex说明(自动生成)： 遍历 ('S11', 'S12', 'S21', 'S22') 中的 parameter，逐项执行循环体逻辑。
            for parameter in ("S11", "S12", "S21", "S22"):
                # Codex说明(自动生成)： 调用 api.set_mapping，执行当前流程需要的具体操作或副作用。
                api.set_mapping(
                    0, parameter, candidate if parameter == "S11" else "匹配 0"
                )
            # 未确认质量和建模假设时，调用真实生成接口必须拒绝且没有文件副作用。
            with patch(
                "insertion_loss_tool.webview_gui.OUTPUT_DIR", folder / "exports"
            ):
                # Codex说明(自动生成)： 计算并保存 generated，供后续语句继续读取或更新。
                generated = api.generate_datasheet_network(0)
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(generated["ok"], "unreviewed partial trace was exported")
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("复核", generated["error"])
            # Codex说明(自动生成)： 调用 self.assertFalse 检查测试期望，确认实际结果符合预期。
            self.assertFalse(list(folder.rglob("*.s2p")))


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 调用 unittest.main，执行当前流程需要的具体操作或副作用。
    unittest.main()
