"""图片曲线的显示抽点与输出采样诊断；不修改提取值或用户网格。

显示层在连续分桶内保留纵坐标最小/最大值和全局首尾。有限显示预算不能
保留任意多个局部转折，因此编辑器仍使用完整原图坐标。采样诊断比较已经
提取的离散幅度与实际统一网格，不把图像像素或重建差解释为仪器准确率。
"""

from __future__ import annotations

import re

import numpy as np


def extrema_preview(points: np.ndarray, max_points: int = 800) -> np.ndarray:
    """返回按原顺序排列的源点子集，最多 max_points 个，且包含首尾和极值。

    每个连续分桶最多提供两个真实源点。仅选择索引，不插值、不平滑、不
    写入调用者数组；四点预算是同时保留两个端点和内部双极值的最低要求。
    """
    values = np.asarray(points, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 2 or max_points < 4:
        raise ValueError("Preview requires Nx2 points and a budget of at least four.")
    if len(values) <= max_points:
        return values.copy()
    indices = {0, len(values) - 1}
    buckets = (max_points - 2) // 2
    edges = np.linspace(1, len(values) - 1, buckets + 1, dtype=int)
    for start, stop in zip(edges[:-1], edges[1:]):
        column = values[start:stop, 1]
        indices.add(int(start + np.argmin(column)))
        indices.add(int(start + np.argmax(column)))
    return values[sorted(indices)].copy()


def sampling_check(frequency_hz: np.ndarray, magnitude_db: np.ndarray,
                   output_hz: np.ndarray, vertical_resolution_db: float | None = None) -> dict[str, object]:
    """量化统一网格遗漏的已提取形状，检查范围只含双方实际覆盖的频段。

    输出幅度与正式导出一样采用 dB 线性插值。局部极值包括平顶/平底区段，
    将极值与它两侧输出采样点中最接近该极值的幅度比较；同时报告从输出
    点线性重建到源频率时的最大差。容差仅用于浮点舍入，不是精度门槛。
    """
    frequency = np.asarray(frequency_hz, dtype=float)
    magnitude = np.asarray(magnitude_db, dtype=float)
    output = np.asarray(output_hz, dtype=float)
    output = output[(output >= frequency[0]) & (output <= frequency[-1])]
    if output.size < 2:
        return {"status": "insufficient-coverage", "message": "Fewer than two output samples cover this trace; sampling detail cannot be assessed."}
    inside = (frequency >= output[0]) & (frequency <= output[-1])
    source_f, source_db = frequency[inside], magnitude[inside]
    sampled_db = np.interp(output, frequency, magnitude)
    if source_f.size == 0:
        return {"status": "insufficient-coverage", "message": "No source samples lie between the covered output endpoints."}
    reconstructed = np.interp(source_f, output, sampled_db)
    differences = np.abs(reconstructed - source_db)
    roundoff = 64 * np.finfo(float).eps * max(1.0, float(np.max(np.abs(magnitude))))
    # 合并幅度完全相同的相邻点；平台两端均检查，避免窄平台被其中心位置误判。
    changes = np.flatnonzero(np.diff(source_db) != 0)
    starts = np.r_[0, changes + 1]
    ends = np.r_[changes, len(source_db) - 1]
    levels = source_db[starts]
    losses = []
    extrema_count = 0
    for run in range(1, len(levels) - 1):
        is_minimum = levels[run] < levels[run - 1] and levels[run] < levels[run + 1]
        is_maximum = levels[run] > levels[run - 1] and levels[run] > levels[run + 1]
        if not (is_minimum or is_maximum):
            continue
        extrema_count += 1
        first, last = int(starts[run]), int(ends[run])
        lower = max(0, int(np.searchsorted(output, source_f[first], side="right")) - 1)
        upper = min(len(output) - 1, int(np.searchsorted(output, source_f[last], side="left")))
        neighbour = float(np.min(sampled_db[lower:upper + 1]) if is_minimum else np.max(sampled_db[lower:upper + 1]))
        loss = neighbour - levels[run] if is_minimum else levels[run] - neighbour
        if loss > roundoff:
            losses.append({"kind": "minimum" if is_minimum else "maximum",
                           "frequency_hz": float(source_f[first]), "source_db": float(levels[run]),
                           "output_neighbour_db": neighbour, "loss_db": float(loss)})
    losses.sort(key=lambda item: item["loss_db"], reverse=True)
    worst = int(np.argmax(differences))
    maximum_difference = float(differences[worst])
    # 一纵向像素仅决定何时显示可操作提示；所有实际数值差仍保留在诊断中。
    # 它不是仪器误差、置信区间或允许误差。未知分辨率时退回数值差提示。
    visible_scale = max(roundoff, vertical_resolution_db or 0.0)
    status = "sampled-agreement" if maximum_difference <= roundoff else "sampling-difference"
    if maximum_difference > visible_scale:
        status = "sampling-loss"
    return {
        "status": status,
        "comparison_range_hz": [float(output[0]), float(output[-1])],
        "source_samples": int(len(source_f)), "output_samples": int(len(output)),
        "source_minimum_db": float(np.min(source_db)), "output_minimum_db": float(np.min(sampled_db)),
        "source_maximum_db": float(np.max(source_db)), "output_maximum_db": float(np.max(sampled_db)),
        "max_reconstruction_difference_db": maximum_difference,
        "worst_frequency_hz": float(source_f[worst]),
        "local_extrema_count": extrema_count, "changed_extrema_count": len(losses),
        "extremum_losses": losses[:12], "floating_point_tolerance_db": roundoff,
        "vertical_resolution_db_per_pixel": vertical_resolution_db,
    }


def sampling_message(source: str, check: dict[str, object]) -> str:
    """供频率设置旁和导出复核使用的相同英文提示，准确率不由此推断。"""
    match = re.match(r"^图(\d+)\s+([A-Z]+)\s+·", source)
    if match:
        source = f"Image {match[1]}, trace {match[2]}"
    if check["status"] == "insufficient-coverage":
        return f"{source}: {check['message']}"
    if check["status"] != "sampling-loss":
        return ""
    scale = check.get("vertical_resolution_db_per_pixel")
    scale_text = f" (one source-image pixel = {scale:.6g} dB)" if scale else ""
    return (f"{source}: output sampling changes {check['changed_extrema_count']} local extrema; "
            f"minimum {check['source_minimum_db']:.6g} → {check['output_minimum_db']:.6g} dB. "
            f"Maximum reconstruction difference {check['max_reconstruction_difference_db']:.6g} dB{scale_text}. "
            "Try a finer step and review again; this compares extracted samples, not image accuracy.")


def finer_uniform_step(output_hz: np.ndarray, frequencies: list[np.ndarray],
                       max_points: int = 200_000) -> float | None:
    """建议可整除当前范围且不大于最小源点间距的步进，绝不自动应用。

    最小源间距只是可操作起点，不保证所有非对齐局部极值都落在统一网格上。
    超过产品频点上限时不给出不可用建议。
    """
    if not frequencies or len(output_hz) < 2:
        return None
    target = min(float(np.min(np.diff(values))) for values in frequencies if len(values) > 1)
    span = float(output_hz[-1] - output_hz[0])
    intervals = max(2 * (len(output_hz) - 1), int(np.ceil(span / target - 1e-9)))
    return span / intervals if intervals + 1 <= max_points else None
