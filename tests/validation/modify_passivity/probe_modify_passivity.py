# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile


# Codex说明(自动生成)： 计算并保存 PROJECT_ROOT，供后续语句继续读取或更新。
PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Codex说明(自动生成)： 调用 sys.path.insert 更新列表或集合，把当前步骤产生的数据加入结果。
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 read_touchstone, to_magnitude_db，提供本文件后续流程需要的库能力。
from insertion_loss_tool.touchstone import read_touchstone, to_magnitude_db  # noqa: E402
# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import InsertionLossWebApi  # noqa: E402


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main() -> int:
    # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
    source = Path(__file__).with_name("cases") / "known_failure.s2p"
    # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
    with tempfile.TemporaryDirectory() as temp_dir:
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = Path(temp_dir) / "modified.s2p"
        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = InsertionLossWebApi().run_generation_sync(
            {
                "mode": "modify",
                "input": str(source),
                "output": str(output),
                "targets": "2GHz:1,4GHz:1",
                "pairs": "S21,S12",
                "smoothness": "0.14",
                "smooth_domain": "linear",
                "anchor_edges": True,
                "insert_targets": True,
            }
        )
        # Codex说明(自动生成)： 检查条件 not response.get('ok') or not output.is_file()，根据结果选择后续执行路径。
        if not response.get("ok") or not output.is_file():
            # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
            print("MODIFY-PASSIVITY-001 failure-signature public-modify-rejected")
            # Codex说明(自动生成)： 返回 7，让调用方取得本函数的处理结果。
            return 7
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = read_touchstone(output)
        # Codex说明(自动生成)： 计算并保存 singular_values，供后续语句继续读取或更新。
        singular_values = __import__("numpy").linalg.svd(data.s, compute_uv=False)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = -to_magnitude_db(data.s[:, 1, 0])
        # Codex说明(自动生成)： 计算并保存 checks，供后续语句继续读取或更新。
        checks = (
            float(singular_values.max()) <= 1.0 + 1.0e-9,
            abs(float(loss[1]) - 1.0) <= 1.0e-6,
            abs(float(loss[3]) - 1.0) <= 1.0e-6,
        )
        # Codex说明(自动生成)： 检查条件 not all(checks)，根据结果选择后续执行路径。
        if not all(checks):
            # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
            print("MODIFY-PASSIVITY-001 failure-signature passive-or-target-contract")
            # Codex说明(自动生成)： 返回 7，让调用方取得本函数的处理结果。
            return 7
    # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
    print("MODIFY-PASSIVITY-001 GREEN public Modify passive exact targets")
    # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
    return 0


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
    raise SystemExit(main())
