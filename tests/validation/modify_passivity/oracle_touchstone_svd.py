# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np


# Codex说明(自动生成)： 计算并保存 PROJECT_ROOT，供后续语句继续读取或更新。
PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Codex说明(自动生成)： 调用 sys.path.insert 更新列表或集合，把当前步骤产生的数据加入结果。
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import InsertionLossWebApi  # noqa: E402


# Codex说明(自动生成)： 定义函数 read_ri_s2p，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def read_ri_s2p(path: Path) -> tuple[np.ndarray, np.ndarray]:
    # Codex说明(自动生成)： 声明并保存 rows，同时保留类型信息方便维护和静态检查。
    rows: list[list[float]] = []
    # Codex说明(自动生成)： 遍历 path.read_text(encoding='utf-8').splitlines() 中的 line，逐项执行循环体逻辑。
    for line in path.read_text(encoding="utf-8").splitlines():
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = line.strip()
        # Codex说明(自动生成)： 检查条件 text and (not text.startswith(('!', '#', '[')))，根据结果选择后续执行路径。
        if text and not text.startswith(("!", "#", "[")):
            # Codex说明(自动生成)： 调用 rows.append 更新列表或集合，把当前步骤产生的数据加入结果。
            rows.append([float(value) for value in text.split()])
    # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
    values = np.asarray(rows, dtype=float)
    # Codex说明(自动生成)： 计算并保存 matrix，供后续语句继续读取或更新。
    matrix = np.empty((len(values), 2, 2), dtype=complex)
    # Codex说明(自动生成)： 计算并保存 matrix[:, 0, 0]，供后续语句继续读取或更新。
    matrix[:, 0, 0] = values[:, 1] + 1j * values[:, 2]
    # Codex说明(自动生成)： 计算并保存 matrix[:, 1, 0]，供后续语句继续读取或更新。
    matrix[:, 1, 0] = values[:, 3] + 1j * values[:, 4]
    # Codex说明(自动生成)： 计算并保存 matrix[:, 0, 1]，供后续语句继续读取或更新。
    matrix[:, 0, 1] = values[:, 5] + 1j * values[:, 6]
    # Codex说明(自动生成)： 计算并保存 matrix[:, 1, 1]，供后续语句继续读取或更新。
    matrix[:, 1, 1] = values[:, 7] + 1j * values[:, 8]
    # Codex说明(自动生成)： 返回 (values[:, 0] * 1000000000.0, matrix)，让调用方取得本函数的处理结果。
    return values[:, 0] * 1.0e9, matrix


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main() -> int:
    # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
    source = Path(__file__).with_name("cases") / "known_failure.s2p"
    # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
    with tempfile.TemporaryDirectory() as temp_dir:
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = Path(temp_dir) / "oracle-output.s2p"
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
                "format": "ri",
                "frequency_unit": "ghz",
            }
        )
        # Codex说明(自动生成)： 检查条件 not response.get('ok')，根据结果选择后续执行路径。
        if not response.get("ok"):
            # Codex说明(自动生成)： 返回 5，让调用方取得本函数的处理结果。
            return 5
        # Codex说明(自动生成)： 计算并保存 (frequency_hz, matrix)，供后续语句继续读取或更新。
        frequency_hz, matrix = read_ri_s2p(output)
    # Codex说明(自动生成)： 计算并保存 sigma，供后续语句继续读取或更新。
    sigma = np.linalg.svd(matrix, compute_uv=False)[:, 0]
    # Codex说明(自动生成)： 计算并保存 target_indices，供后续语句继续读取或更新。
    target_indices = [int(np.where(frequency_hz == value)[0][0]) for value in (2e9, 4e9)]
    # Codex说明(自动生成)： 计算并保存 target_loss，供后续语句继续读取或更新。
    target_loss = [-20.0 * np.log10(abs(matrix[index, 1, 0])) for index in target_indices]
    # Codex说明(自动生成)： 检查条件 float(np.max(sigma)) > 1.0 + 1e-09 or not np.allclose(t...，根据结果选择后续执行路径。
    if float(np.max(sigma)) > 1.0 + 1.0e-9 or not np.allclose(target_loss, [1.0, 1.0], atol=1e-6):
        # Codex说明(自动生成)： 返回 6，让调用方取得本函数的处理结果。
        return 6
    # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
    print(f"ORACLE_OK independent RI parser NumPy SVD max={float(np.max(sigma)):.12g}")
    # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
    return 0


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
    raise SystemExit(main())
