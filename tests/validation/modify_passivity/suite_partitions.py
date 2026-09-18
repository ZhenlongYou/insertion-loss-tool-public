# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
import json
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

# Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 TouchstoneData, read_touchstone, write_touchstone，提供本文件后续流程需要的库能力。
from insertion_loss_tool.touchstone import TouchstoneData, read_touchstone, write_touchstone  # noqa: E402
# Codex说明(自动生成)： 从 insertion_loss_tool.webview_gui 导入 InsertionLossWebApi，提供本文件后续流程需要的库能力。
from insertion_loss_tool.webview_gui import InsertionLossWebApi  # noqa: E402


# Codex说明(自动生成)： 定义函数 run_modify，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_modify(api: InsertionLossWebApi, source: Path, output: Path, **overrides: object) -> dict:
    # Codex说明(自动生成)： 计算并保存 payload，供后续语句继续读取或更新。
    payload = {
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
    # Codex说明(自动生成)： 调用 payload.update，执行当前流程需要的具体操作或副作用。
    payload.update(overrides)
    # Codex说明(自动生成)： 返回 api.run_generation_sync(payload)，让调用方取得本函数的处理结果。
    return api.run_generation_sync(payload)


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main() -> int:
    # Codex说明(自动生成)： 计算并保存 case_dir，供后续语句继续读取或更新。
    case_dir = Path(__file__).with_name("cases")
    # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(case_dir.glob("*.json"))
    }
    # Codex说明(自动生成)： 检查条件 set(cases) != {'nominal', 'boundary', 'invalid', 'adver...，根据结果选择后续执行路径。
    if set(cases) != {"nominal", "boundary", "invalid", "adversarial", "realistic", "known_failure"}:
        # Codex说明(自动生成)： 返回 2，让调用方取得本函数的处理结果。
        return 2

    # Codex说明(自动生成)： 计算并保存 api，供后续语句继续读取或更新。
    api = InsertionLossWebApi()
    # Codex说明(自动生成)： 计算并保存 nominal_case，供后续语句继续读取或更新。
    nominal_case = cases["nominal"]
    # Codex说明(自动生成)： 计算并保存 boundary_case，供后续语句继续读取或更新。
    boundary_case = cases["boundary"]
    # Codex说明(自动生成)： 计算并保存 invalid_case，供后续语句继续读取或更新。
    invalid_case = cases["invalid"]
    # Codex说明(自动生成)： 计算并保存 adversarial_case，供后续语句继续读取或更新。
    adversarial_case = cases["adversarial"]
    # Codex说明(自动生成)： 计算并保存 realistic_case，供后续语句继续读取或更新。
    realistic_case = cases["realistic"]
    # Codex说明(自动生成)： 计算并保存 known_failure_case，供后续语句继续读取或更新。
    known_failure_case = cases["known_failure"]
    # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
    source = case_dir / str(nominal_case["input"])
    # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
    with tempfile.TemporaryDirectory() as temp_dir:
        # Codex说明(自动生成)： 计算并保存 folder，供后续语句继续读取或更新。
        folder = Path(temp_dir)
        # Codex说明(自动生成)： 计算并保存 nominal，供后续语句继续读取或更新。
        nominal = run_modify(
            api,
            source,
            folder / "nominal.s2p",
            targets=nominal_case["targets"],
            pairs=nominal_case["pairs"],
        )
        # Codex说明(自动生成)： 计算并保存 boundary，供后续语句继续读取或更新。
        boundary = run_modify(
            api,
            case_dir / str(boundary_case["input"]),
            folder / "boundary.s2p",
            targets=boundary_case["targets"],
            pairs=boundary_case["pairs"],
            insert_targets=boundary_case["insert_targets"],
        )
        # Codex说明(自动生成)： 计算并保存 adversarial，供后续语句继续读取或更新。
        adversarial = run_modify(
            api,
            case_dir / str(adversarial_case["input"]),
            folder / "adversarial.s2p",
            targets=adversarial_case["targets"],
            pairs=adversarial_case["pairs"],
        )
        # Codex说明(自动生成)： 计算并保存 nonpassive，供后续语句继续读取或更新。
        nonpassive = folder / "nonpassive.s2p"
        # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
        write_touchstone(
            TouchstoneData(
                np.asarray(invalid_case["frequency_hz"], dtype=float),
                np.full(
                    (2, 2, 2),
                    complex(float(invalid_case["matrix_value"])),
                    dtype=complex,
                ),
            ),
            nonpassive,
        )
        # Codex说明(自动生成)： 计算并保存 invalid，供后续语句继续读取或更新。
        invalid = run_modify(
            api,
            nonpassive,
            folder / "invalid.s2p",
            targets=invalid_case["targets"],
        )
        # Codex说明(自动生成)： 计算并保存 realistic，供后续语句继续读取或更新。
        realistic = run_modify(
            api,
            PROJECT_ROOT / str(realistic_case["input"]),
            folder / "realistic.s2p",
            targets=realistic_case["targets"],
            pairs=realistic_case["pairs"],
        )
        # Codex说明(自动生成)： 计算并保存 known_failure，供后续语句继续读取或更新。
        known_failure = run_modify(
            api,
            case_dir / str(known_failure_case["input"]),
            folder / "known-failure.s2p",
            targets=known_failure_case["targets"],
            pairs=known_failure_case["pairs"],
            smoothness=known_failure_case["smoothness"],
        )
        # Codex说明(自动生成)： 计算并保存 nominal_data，供后续语句继续读取或更新。
        nominal_data = read_touchstone(folder / "nominal.s2p") if nominal.get("ok") else None
        # Codex说明(自动生成)： 计算并保存 checks，供后续语句继续读取或更新。
        checks = (
            nominal.get("ok") is True,
            boundary.get("ok") is True,
            realistic.get("ok") is True,
            known_failure.get("ok") is True,
            invalid.get("ok") is False
            and invalid_case["expected_error"] in invalid.get("error", ""),
            adversarial.get("ok") is False
            and adversarial_case["expected_error"] in adversarial.get("error", ""),
            nominal_data is not None
            and float(np.linalg.svd(nominal_data.s, compute_uv=False).max()) <= 1.0 + 1.0e-9,
        )
    # Codex说明(自动生成)： 检查条件 not all(checks)，根据结果选择后续执行路径。
    if not all(checks):
        # Codex说明(自动生成)： 返回 4，让调用方取得本函数的处理结果。
        return 4
    # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
    print("SUITE_OK six Modify passivity partitions")
    # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
    return 0


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
    raise SystemExit(main())
