"""Sampled-passivity constraints used by Modify smoothing."""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np


# Codex说明(自动生成)： 定义函数 constrain_smoothed_points_to_passivity，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def constrain_smoothed_points_to_passivity(
    frequency_hz: np.ndarray,
    original_s: np.ndarray,
    candidate_s: np.ndarray,
    target_frequencies_hz: np.ndarray,
    *,
    tolerance: float = 1.0e-12,
) -> np.ndarray:
    """Keep feasible targets exact and contract only non-target overshoot.

    At each non-target frequency, the spectral-norm unit ball is convex.  A
    bisection along the line from the original passive matrix to the smoothed
    candidate therefore finds the largest passive fraction of the requested
    edit without rotating phases or changing untouched source samples.
    """

    # Codex说明(自动生成)： 计算并保存 constrained，供后续语句继续读取或更新。
    constrained = np.array(candidate_s, copy=True)
    # Codex说明(自动生成)： 计算并保存 target_mask，供后续语句继续读取或更新。
    target_mask = np.any(
        np.isclose(
            frequency_hz[:, None],
            target_frequencies_hz[None, :],
            rtol=8.0 * np.finfo(float).eps,
            atol=0.0,
        ),
        axis=1,
    )
    # Codex说明(自动生成)： 遍历 enumerate(frequency_hz) 中的 (index, frequency)，逐项执行循环体逻辑。
    for index, frequency in enumerate(frequency_hz):
        # Codex说明(自动生成)： 计算并保存 candidate_sigma，供后续语句继续读取或更新。
        candidate_sigma = float(np.linalg.svd(constrained[index], compute_uv=False)[0])
        # Codex说明(自动生成)： 检查条件 candidate_sigma <= 1.0 + tolerance，根据结果选择后续执行路径。
        if candidate_sigma <= 1.0 + tolerance:
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        # Codex说明(自动生成)： 检查条件 bool(target_mask[index])，根据结果选择后续执行路径。
        if bool(target_mask[index]):
            # Codex说明(自动生成)： 抛出 ValueError(f'Requested target cannot satisfy sampled pa...，明确提示输入、状态或处理流程无法继续。
            raise ValueError(
                "Requested target cannot satisfy sampled passivity: "
                f"maximum singular value {candidate_sigma:.6g} "
                f"at {float(frequency):.6g} Hz."
            )

        # Codex说明(自动生成)： 计算并保存 lower，供后续语句继续读取或更新。
        lower = 0.0
        # Codex说明(自动生成)： 计算并保存 upper，供后续语句继续读取或更新。
        upper = 1.0
        # Codex说明(自动生成)： 遍历 range(60) 中的 _，逐项执行循环体逻辑。
        for _ in range(60):
            # Codex说明(自动生成)： 计算并保存 fraction，供后续语句继续读取或更新。
            fraction = 0.5 * (lower + upper)
            # Codex说明(自动生成)： 计算并保存 trial，供后续语句继续读取或更新。
            trial = original_s[index] + fraction * (
                candidate_s[index] - original_s[index]
            )
            # Codex说明(自动生成)： 检查条件 float(np.linalg.svd(trial, compute_uv=False)[0]) <= 1.0，根据结果选择后续执行路径。
            if float(np.linalg.svd(trial, compute_uv=False)[0]) <= 1.0:
                # Codex说明(自动生成)： 计算并保存 lower，供后续语句继续读取或更新。
                lower = fraction
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 计算并保存 upper，供后续语句继续读取或更新。
                upper = fraction
        # Codex说明(自动生成)： 计算并保存 constrained[index]，供后续语句继续读取或更新。
        constrained[index] = original_s[index] + lower * (
            candidate_s[index] - original_s[index]
        )
    # Codex说明(自动生成)： 返回 constrained，让调用方取得本函数的处理结果。
    return constrained
