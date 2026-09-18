"""Insertion-loss models, smooth editing, and plotting."""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 dataclasses 导入 dataclass，声明轻量数据结构并减少样板初始化代码。
from dataclasses import dataclass
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 re，执行正则匹配和文本规则识别。
import re
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 从 typing 导入 Iterable, Sequence，提供类型标注辅助名称，方便维护和静态检查。
from typing import Iterable, Sequence

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np

# Modify's passivity projection is isolated so its failure mode can be tested directly.
from .modify_passivity import constrain_smoothed_points_to_passivity
# Codex说明(自动生成)： 从 touchstone 导入 TouchstoneData, to_magnitude_db，提供本文件后续流程需要的库能力。
from .touchstone import TouchstoneData, to_magnitude_db


# Codex说明(自动生成)： 计算并保存 FREQUENCY_UNITS，供后续语句继续读取或更新。
FREQUENCY_UNITS = {
    "hz": 1.0,
    "h": 1.0,
    "khz": 1e3,
    "k": 1e3,
    "mhz": 1e6,
    "m": 1e6,
    "ghz": 1e9,
    "g": 1e9,
}

# The compact desktop UI exposes the port counts most often used for cables,
# fixtures, and small multi-port interconnects.  Keep this in the model layer
# so every front end presents the same choices.
COMMON_PORT_COUNTS = (2, 3, 4, 6, 8)


# Codex说明(自动生成)： 定义 TargetPoint 类，把相关数据结构、校验规则或操作方法组织在一起。
@dataclass(frozen=True)
class TargetPoint:
    # Codex说明(自动生成)： 声明并保存 frequency_hz，同时保留类型信息方便维护和静态检查。
    frequency_hz: float
    # Codex说明(自动生成)： 声明并保存 loss_db，同时保留类型信息方便维护和静态检查。
    loss_db: float


# Codex说明(自动生成)： 定义 TargetResult 类，把相关数据结构、校验规则或操作方法组织在一起。
@dataclass
class TargetResult:
    # Codex说明(自动生成)： 声明并保存 pair，同时保留类型信息方便维护和静态检查。
    pair: str
    # Codex说明(自动生成)： 声明并保存 frequency_hz，同时保留类型信息方便维护和静态检查。
    frequency_hz: float
    # Codex说明(自动生成)： 声明并保存 requested_loss_db，同时保留类型信息方便维护和静态检查。
    requested_loss_db: float
    # Codex说明(自动生成)： 声明并保存 original_loss_db，同时保留类型信息方便维护和静态检查。
    original_loss_db: float
    # Codex说明(自动生成)： 声明并保存 achieved_loss_db，同时保留类型信息方便维护和静态检查。
    achieved_loss_db: float
    # Codex说明(自动生成)： 声明并保存 phase_delta_deg，同时保留类型信息方便维护和静态检查。
    phase_delta_deg: float


# Codex说明(自动生成)： 定义 ModificationResult 类，把相关数据结构、校验规则或操作方法组织在一起。
@dataclass
class ModificationResult:
    # Codex说明(自动生成)： 声明并保存 data，同时保留类型信息方便维护和静态检查。
    data: TouchstoneData
    # Codex说明(自动生成)： 声明并保存 results，同时保留类型信息方便维护和静态检查。
    results: list[TargetResult]


# Codex说明(自动生成)： 定义函数 parse_frequency，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def parse_frequency(value: str | float | int) -> float:
    """Parse a frequency such as 10GHz, 2500MHz, or 1.2e9."""

    # Codex说明(自动生成)： 检查条件 isinstance(value, (int, float))，根据结果选择后续执行路径。
    if isinstance(value, (int, float)):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = float(value)
        # Codex说明(自动生成)： 检查条件 not np.isfinite(frequency) or frequency <= 0，根据结果选择后续执行路径。
        if not np.isfinite(frequency) or frequency <= 0:
            # Codex说明(自动生成)： 抛出 ValueError('Frequency must be positive')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("Frequency must be positive")
        # Codex说明(自动生成)： 返回 frequency，让调用方取得本函数的处理结果。
        return frequency

    # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
    text = str(value).strip().lower().replace(" ", "")
    # Codex说明(自动生成)： 计算并保存 match，供后续语句继续读取或更新。
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)([a-z]*)", text)
    # Codex说明(自动生成)： 检查条件 not match，根据结果选择后续执行路径。
    if not match:
        # Codex说明(自动生成)： 抛出 ValueError(f'Could not parse frequency value: {value!r}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Could not parse frequency value: {value!r}")
    # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
    number = float(match.group(1))
    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    unit = match.group(2) or "hz"
    # Codex说明(自动生成)： 检查条件 unit not in FREQUENCY_UNITS，根据结果选择后续执行路径。
    if unit not in FREQUENCY_UNITS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported frequency unit in {value!r}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported frequency unit in {value!r}")
    # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
    frequency = number * FREQUENCY_UNITS[unit]
    # Codex说明(自动生成)： 检查条件 not np.isfinite(frequency) or frequency <= 0，根据结果选择后续执行路径。
    if not np.isfinite(frequency) or frequency <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Frequency must be positive')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequency must be positive")
    # Codex说明(自动生成)： 返回 frequency，让调用方取得本函数的处理结果。
    return frequency


# Codex说明(自动生成)： 定义函数 parse_target_points，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def parse_target_points(values: Sequence[str]) -> list[TargetPoint]:
    """Parse target strings like '5GHz:8.5' or '5GHz=8.5'."""

    # Codex说明(自动生成)： 声明并保存 targets，同时保留类型信息方便维护和静态检查。
    targets: list[TargetPoint] = []
    # Codex说明(自动生成)： 遍历 values 中的 value，逐项执行循环体逻辑。
    for value in values:
        # Codex说明(自动生成)： 遍历 str(value).split(',') 中的 part，逐项执行循环体逻辑。
        for part in str(value).split(","):
            # Codex说明(自动生成)： 计算并保存 part，供后续语句继续读取或更新。
            part = part.strip()
            # Codex说明(自动生成)： 检查条件 not part，根据结果选择后续执行路径。
            if not part:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 ':' in part，根据结果选择后续执行路径。
            if ":" in part:
                # Codex说明(自动生成)： 计算并保存 (freq_text, loss_text)，供后续语句继续读取或更新。
                freq_text, loss_text = part.split(":", 1)
            # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 '=' in part。
            elif "=" in part:
                # Codex说明(自动生成)： 计算并保存 (freq_text, loss_text)，供后续语句继续读取或更新。
                freq_text, loss_text = part.split("=", 1)
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 抛出 ValueError(f"Target {part!r} must use 'frequency:loss_d...，明确提示输入、状态或处理流程无法继续。
                raise ValueError(
                    f"Target {part!r} must use 'frequency:loss_db', for example 5GHz:8.0"
                )
            # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
            loss_db = float(loss_text)
            # Codex说明(自动生成)： 调用 _validate_loss_value，执行当前流程需要的具体操作或副作用。
            _validate_loss_value(loss_db, "Target insertion loss")
            # Codex说明(自动生成)： 调用 targets.append 更新列表或集合，把当前步骤产生的数据加入结果。
            targets.append(TargetPoint(parse_frequency(freq_text), loss_db))
    # Codex说明(自动生成)： 检查条件 not targets，根据结果选择后续执行路径。
    if not targets:
        # Codex说明(自动生成)： 抛出 ValueError('At least one target point is required')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("At least one target point is required")
    # Codex说明(自动生成)： 返回 normalize_target_points(targets)，让调用方取得本函数的处理结果。
    return normalize_target_points(targets)


# Codex说明(自动生成)： 定义函数 parse_draw_points，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def parse_draw_points(values: Sequence[str]) -> list[TargetPoint]:
    """Parse hand-drawn control points supplied from the CLI or main.py.

    Draw mode needs at least two control points so it can form a fitted curve.
    Values at or below 0 dB are treated as the usual S-parameter magnitude,
    so `5GHz:-8` becomes an internal positive insertion loss of 8 dB. Positive
    values are still accepted as legacy positive insertion-loss inputs.
    """

    # Codex说明(自动生成)： 声明并保存 points，同时保留类型信息方便维护和静态检查。
    points: list[TargetPoint] = []
    # Codex说明(自动生成)： 遍历 values 中的 value，逐项执行循环体逻辑。
    for value in values:
        # Codex说明(自动生成)： 遍历 str(value).split(',') 中的 part，逐项执行循环体逻辑。
        for part in str(value).split(","):
            # Codex说明(自动生成)： 计算并保存 part，供后续语句继续读取或更新。
            part = part.strip()
            # Codex说明(自动生成)： 检查条件 not part，根据结果选择后续执行路径。
            if not part:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 ':' in part，根据结果选择后续执行路径。
            if ":" in part:
                # Codex说明(自动生成)： 计算并保存 (freq_text, level_text)，供后续语句继续读取或更新。
                freq_text, level_text = part.split(":", 1)
            # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 '=' in part。
            elif "=" in part:
                # Codex说明(自动生成)： 计算并保存 (freq_text, level_text)，供后续语句继续读取或更新。
                freq_text, level_text = part.split("=", 1)
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 抛出 ValueError(f"Draw point {part!r} must use 'frequency:db...，明确提示输入、状态或处理流程无法继续。
                raise ValueError(
                    f"Draw point {part!r} must use 'frequency:db', for example 5GHz:-8.0"
                )
            # Codex说明(自动生成)： 计算并保存 level_db，供后续语句继续读取或更新。
            level_db = float(level_text)
            # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
            loss_db = _draw_level_to_loss_db(level_db)
            # Codex说明(自动生成)： 调用 points.append 更新列表或集合，把当前步骤产生的数据加入结果。
            points.append(TargetPoint(parse_frequency(freq_text), loss_db))
    # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
    points = normalize_target_points(points)
    # Codex说明(自动生成)： 检查条件 len(points) < 2，根据结果选择后续执行路径。
    if len(points) < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Draw mode requires at least two insertion-l...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw mode requires at least two insertion-loss points")
    # Codex说明(自动生成)： 返回 points，让调用方取得本函数的处理结果。
    return points


# Codex说明(自动生成)： 定义函数 interpolate_drawn_loss，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def interpolate_drawn_loss(
    frequency_hz: np.ndarray,
    control_points: Sequence[TargetPoint],
    *,
    method: str = "smooth",
    fit_domain: str = "linear",
    min_spacing_fraction: float = 1e-4,
    max_slope_db_per_span: float = 500.0,
) -> np.ndarray:
    """Create an insertion-loss curve from hand-drawn control points.

    The default `smooth` method fits a shape-preserving cubic Hermite curve
    through the user's points. This avoids the sharp derivative changes of
    straight line segments while still passing through the requested losses.
    `linear` is kept as an explicit option for users who want the old behavior.
    """

    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = np.asarray(frequency_hz, dtype=float)
    # Codex说明(自动生成)： 调用 _validate_frequency_grid 生成或展示图形，便于观察计算结果。
    _validate_frequency_grid(frequency_hz)
    # Codex说明(自动生成)： 计算并保存 (control_frequencies, control_losses)，供后续语句继续读取或更新。
    control_frequencies, control_losses = _prepare_draw_controls(
        frequency_hz,
        control_points,
        fit_domain=fit_domain,
        min_spacing_fraction=min_spacing_fraction,
        max_slope_db_per_span=max_slope_db_per_span,
    )

    # Codex说明(自动生成)： 计算并保存 query_x，供后续语句继续读取或更新。
    query_x = _draw_fit_domain(frequency_hz, fit_domain)
    # Codex说明(自动生成)： 计算并保存 control_x，供后续语句继续读取或更新。
    control_x = _draw_fit_domain(control_frequencies, fit_domain)
    # Codex说明(自动生成)： 计算并保存 method，供后续语句继续读取或更新。
    method = method.lower()
    # Codex说明(自动生成)： 检查条件 method == 'linear'，根据结果选择后续执行路径。
    if method == "linear":
        # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
        loss_db = np.interp(query_x, control_x, control_losses)
    # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 method == 'smooth'。
    elif method == "smooth":
        # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
        loss_db = _shape_preserving_cubic_interpolate(query_x, control_x, control_losses)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 ValueError("Draw interpolation method must be 'smooth' ...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw interpolation method must be 'smooth' or 'linear'")
    # Codex说明(自动生成)： 调用 _validate_loss_array，执行当前流程需要的具体操作或副作用。
    _validate_loss_array(loss_db, "Drawn insertion loss")
    # Codex说明(自动生成)： 返回 loss_db，让调用方取得本函数的处理结果。
    return loss_db


# Codex说明(自动生成)： 定义函数 insert_draw_control_frequencies，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def insert_draw_control_frequencies(
    frequency_hz: np.ndarray,
    control_points: Sequence[TargetPoint],
) -> np.ndarray:
    """Return a frequency axis that contains every drawn control frequency.

    This keeps the written Touchstone file from merely approximating user
    control points that fall between the original sweep samples.
    """

    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = np.asarray(frequency_hz, dtype=float)
    # Codex说明(自动生成)： 调用 _validate_frequency_grid 生成或展示图形，便于观察计算结果。
    _validate_frequency_grid(frequency_hz)
    # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
    points = normalize_target_points(control_points)
    # Codex说明(自动生成)： 检查条件 len(points) < 2，根据结果选择后续执行路径。
    if len(points) < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Draw mode requires at least two insertion-l...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw mode requires at least two insertion-loss points")
    # Codex说明(自动生成)： 计算并保存 control_frequencies，供后续语句继续读取或更新。
    control_frequencies = np.asarray([point.frequency_hz for point in points], dtype=float)
    # Codex说明(自动生成)： 检查条件 np.any(control_frequencies < frequency_hz[0]) or np.any...，根据结果选择后续执行路径。
    if (
        np.any(control_frequencies < frequency_hz[0])
        or np.any(control_frequencies > frequency_hz[-1])
    ):
        # Codex说明(自动生成)： 抛出 ValueError('Draw control points must be inside the gene...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control points must be inside the generated frequency range")
    # Codex说明(自动生成)： 返回 np.unique(np.concatenate([frequency_hz, control_frequen...，让调用方取得本函数的处理结果。
    return np.unique(np.concatenate([frequency_hz, control_frequencies]))


# Codex说明(自动生成)： 定义函数 draw_loss_points_interactive，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def draw_loss_points_interactive(
    start_hz: float,
    stop_hz: float,
    *,
    loss_min_db: float = -40.0,
    loss_max_db: float = 0.0,
    frequency_unit: str = "ghz",
    title: str = "Draw insertion loss",
    fit_method: str = "smooth",
    fit_domain: str = "linear",
    min_spacing_fraction: float = 1e-4,
    max_slope_db_per_span: float = 500.0,
) -> list[TargetPoint]:
    """Open a matplotlib window and collect insertion-loss control points.

    Left click adds a point, right click removes the most recently added point,
    and Enter/Return closes the window. The preview curve uses the same fit
    method as the generated S-parameter file, so the user sees the smoothed
    result rather than only a straight-line control polygon.
    """

    # Codex说明(自动生成)： 检查条件 start_hz <= 0 or stop_hz <= start_hz，根据结果选择后续执行路径。
    if start_hz <= 0 or stop_hz <= start_hz:
        # Codex说明(自动生成)： 抛出 ValueError('Draw frequency range must satisfy 0 < start...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw frequency range must satisfy 0 < start < stop")
    # Codex说明(自动生成)： 调用 _validate_draw_axis_limits，执行当前流程需要的具体操作或副作用。
    _validate_draw_axis_limits(loss_min_db, loss_max_db)
    # Codex说明(自动生成)： 检查条件 loss_max_db <= loss_min_db，根据结果选择后续执行路径。
    if loss_max_db <= loss_min_db:
        # Codex说明(自动生成)： 抛出 ValueError('Draw dB maximum must be larger than the min...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw dB maximum must be larger than the minimum")

    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    unit = frequency_unit.lower()
    # Codex说明(自动生成)： 检查条件 unit not in FREQUENCY_UNITS，根据结果选择后续执行路径。
    if unit not in FREQUENCY_UNITS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported draw frequency unit: {frequenc...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported draw frequency unit: {frequency_unit}")
    # Codex说明(自动生成)： 计算并保存 scale，供后续语句继续读取或更新。
    scale = FREQUENCY_UNITS[unit]
    # Codex说明(自动生成)： 计算并保存 x_start，供后续语句继续读取或更新。
    x_start = start_hz / scale
    # Codex说明(自动生成)： 计算并保存 x_stop，供后续语句继续读取或更新。
    x_stop = stop_hz / scale

    # Codex说明(自动生成)： 导入 matplotlib.pyplot as plt，绘制仿真结果和诊断图形。
    import matplotlib.pyplot as plt

    # Codex说明(自动生成)： 计算并保存 (fig, ax)，供后续语句继续读取或更新。
    fig, ax = plt.subplots(figsize=(9, 5))
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 调用 fig.canvas.manager.set_window_title 生成或展示图形，便于观察计算结果。
        fig.canvas.manager.set_window_title(title)
    # Codex说明(自动生成)： 捕获 AttributeError，执行对应的恢复、记录或重新报错逻辑。
    except AttributeError:
        # Codex说明(自动生成)： 保留空实现位置，表示这个分支当前不需要额外动作。
        pass
    # Codex说明(自动生成)： 调用 ax.set_title 生成或展示图形，便于观察计算结果。
    ax.set_title(f"{title} - left click add, right click undo, Enter finish")
    # Codex说明(自动生成)： 调用 ax.set_xlabel 生成或展示图形，便于观察计算结果。
    ax.set_xlabel(unit.upper())
    # Codex说明(自动生成)： 调用 ax.set_ylabel 生成或展示图形，便于观察计算结果。
    ax.set_ylabel("Through magnitude (dB)")
    # Codex说明(自动生成)： 调用 ax.set_xlim，执行当前流程需要的具体操作或副作用。
    ax.set_xlim(x_start, x_stop)
    # Codex说明(自动生成)： 调用 ax.set_ylim，执行当前流程需要的具体操作或副作用。
    ax.set_ylim(loss_min_db, loss_max_db)
    # Codex说明(自动生成)： 调用 ax.grid 生成或展示图形，便于观察计算结果。
    ax.grid(True, alpha=0.3)
    # Codex说明(自动生成)： 计算并保存 (curve_line,)，供后续语句继续读取或更新。
    (curve_line,) = ax.plot([], [], linewidth=1.8)
    # Codex说明(自动生成)： 计算并保存 (point_line,)，供后续语句继续读取或更新。
    (point_line,) = ax.plot([], [], linestyle="none", marker="o")
    # Codex说明(自动生成)： 声明并保存 points，同时保留类型信息方便维护和静态检查。
    points: list[tuple[float, float]] = []

    # Codex说明(自动生成)： 定义函数 redraw，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def redraw() -> None:
        # Codex说明(自动生成)： 计算并保存 ordered，供后续语句继续读取或更新。
        ordered = sorted(points, key=lambda item: item[0])
        # Codex说明(自动生成)： 检查条件 ordered，根据结果选择后续执行路径。
        if ordered:
            # Codex说明(自动生成)： 计算并保存 (xs, ys)，供后续语句继续读取或更新。
            xs, ys = zip(*ordered)
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 计算并保存 (xs, ys)，供后续语句继续读取或更新。
            xs, ys = [], []
        # Codex说明(自动生成)： 调用 point_line.set_data，执行当前流程需要的具体操作或副作用。
        point_line.set_data(xs, ys)
        # Codex说明(自动生成)： 检查条件 len(ordered) >= 2，根据结果选择后续执行路径。
        if len(ordered) >= 2:
            # Codex说明(自动生成)： 计算并保存 dense_x，供后续语句继续读取或更新。
            dense_x = np.linspace(x_start, x_stop, 400)
            # Codex说明(自动生成)： 计算并保存 preview_points，供后续语句继续读取或更新。
            preview_points = [
                TargetPoint(
                    frequency_hz=x_value * scale,
                    loss_db=_draw_level_to_loss_db(y_value),
                )
                for x_value, y_value in ordered
            ]
            # Codex说明(自动生成)： 计算并保存 preview_loss，供后续语句继续读取或更新。
            preview_loss = interpolate_drawn_loss(
                dense_x * scale,
                preview_points,
                method=fit_method,
                fit_domain=fit_domain,
                min_spacing_fraction=min_spacing_fraction,
                max_slope_db_per_span=max_slope_db_per_span,
            )
            # Codex说明(自动生成)： 调用 curve_line.set_data，执行当前流程需要的具体操作或副作用。
            curve_line.set_data(
                dense_x,
                _loss_db_to_draw_level(preview_loss, loss_min_db, loss_max_db),
            )
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 调用 curve_line.set_data，执行当前流程需要的具体操作或副作用。
            curve_line.set_data([], [])
        # Codex说明(自动生成)： 调用 fig.canvas.draw_idle，执行当前流程需要的具体操作或副作用。
        fig.canvas.draw_idle()

    # Codex说明(自动生成)： 定义函数 on_click，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def on_click(event) -> None:
        # Codex说明(自动生成)： 检查条件 event.inaxes is not ax or event.xdata is None or event....，根据结果选择后续执行路径。
        if event.inaxes is not ax or event.xdata is None or event.ydata is None:
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 检查条件 event.button == 1，根据结果选择后续执行路径。
        if event.button == 1:
            # Codex说明(自动生成)： 计算并保存 x_value，供后续语句继续读取或更新。
            x_value = min(max(float(event.xdata), x_start), x_stop)
            # Codex说明(自动生成)： 计算并保存 y_value，供后续语句继续读取或更新。
            y_value = min(max(float(event.ydata), loss_min_db), loss_max_db)
            # Codex说明(自动生成)： 调用 points.append 更新列表或集合，把当前步骤产生的数据加入结果。
            points.append((x_value, y_value))
            # Codex说明(自动生成)： 调用 redraw，执行当前流程需要的具体操作或副作用。
            redraw()
        # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 event.button == 3 and points。
        elif event.button == 3 and points:
            # Codex说明(自动生成)： 调用 points.pop，执行当前流程需要的具体操作或副作用。
            points.pop()
            # Codex说明(自动生成)： 调用 redraw，执行当前流程需要的具体操作或副作用。
            redraw()

    # Codex说明(自动生成)： 定义函数 on_key，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def on_key(event) -> None:
        # Codex说明(自动生成)： 检查条件 event.key in {'enter', 'return'}，根据结果选择后续执行路径。
        if event.key in {"enter", "return"}:
            # Codex说明(自动生成)： 调用 plt.close，执行当前流程需要的具体操作或副作用。
            plt.close(fig)

    # Codex说明(自动生成)： 调用 fig.canvas.mpl_connect，执行当前流程需要的具体操作或副作用。
    fig.canvas.mpl_connect("button_press_event", on_click)
    # Codex说明(自动生成)： 调用 fig.canvas.mpl_connect，执行当前流程需要的具体操作或副作用。
    fig.canvas.mpl_connect("key_press_event", on_key)
    # Codex说明(自动生成)： 调用 plt.show 生成或展示图形，便于观察计算结果。
    plt.show(block=True)

    # Codex说明(自动生成)： 检查条件 len(points) < 2，根据结果选择后续执行路径。
    if len(points) < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Draw at least two insertion-loss points bef...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw at least two insertion-loss points before closing the window")
    # Codex说明(自动生成)： 返回 normalize_target_points([TargetPoint(frequency_hz=x_val...，让调用方取得本函数的处理结果。
    return normalize_target_points(
        [
            TargetPoint(
                frequency_hz=x_value * scale,
                loss_db=_draw_level_to_loss_db(y_value),
            )
            for x_value, y_value in points
        ]
    )


# Codex说明(自动生成)： 定义函数 _draw_level_to_loss_db，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _draw_level_to_loss_db(level_db: float) -> float:
    """Convert draw-mode user dB input into internal positive insertion loss."""

    # Codex说明(自动生成)： 检查条件 not np.isfinite(level_db)，根据结果选择后续执行路径。
    if not np.isfinite(level_db):
        # Codex说明(自动生成)： 抛出 ValueError('Draw dB value must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw dB value must be finite")
    # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
    loss_db = -level_db if level_db <= 0.0 else level_db
    # Codex说明(自动生成)： 调用 _validate_loss_value，执行当前流程需要的具体操作或副作用。
    _validate_loss_value(loss_db, "Draw insertion loss")
    # Codex说明(自动生成)： 返回 float(loss_db)，让调用方取得本函数的处理结果。
    return float(loss_db)


# Codex说明(自动生成)： 定义函数 _loss_db_to_draw_level，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _loss_db_to_draw_level(
    loss_db: np.ndarray,
    axis_min_db: float,
    axis_max_db: float,
) -> np.ndarray:
    """Convert internal positive insertion loss back to the draw-axis convention."""

    # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
    loss_db = np.asarray(loss_db, dtype=float)
    # Codex说明(自动生成)： 检查条件 axis_max_db <= 0.0，根据结果选择后续执行路径。
    if axis_max_db <= 0.0:
        # Codex说明(自动生成)： 返回 -loss_db，让调用方取得本函数的处理结果。
        return -loss_db
    # Codex说明(自动生成)： 检查条件 axis_min_db >= 0.0，根据结果选择后续执行路径。
    if axis_min_db >= 0.0:
        # Codex说明(自动生成)： 返回 loss_db，让调用方取得本函数的处理结果。
        return loss_db
    # Codex说明(自动生成)： 返回 -loss_db，让调用方取得本函数的处理结果。
    return -loss_db


# Codex说明(自动生成)： 定义函数 _validate_draw_axis_limits，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_draw_axis_limits(min_db: float, max_db: float) -> None:
    """Validate draw y-axis limits, which are normally negative dB to 0 dB."""

    # Codex说明(自动生成)： 检查条件 not np.isfinite(min_db) or not np.isfinite(max_db)，根据结果选择后续执行路径。
    if not np.isfinite(min_db) or not np.isfinite(max_db):
        # Codex说明(自动生成)： 抛出 ValueError('Draw dB axis limits must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw dB axis limits must be finite")
    # Codex说明(自动生成)： 检查条件 max_db <= min_db，根据结果选择后续执行路径。
    if max_db <= min_db:
        # Codex说明(自动生成)： 抛出 ValueError('Draw dB maximum must be larger than the min...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw dB maximum must be larger than the minimum")


# Codex说明(自动生成)： 定义函数 _prepare_draw_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _prepare_draw_controls(
    frequency_hz: np.ndarray,
    control_points: Sequence[TargetPoint],
    *,
    fit_domain: str,
    min_spacing_fraction: float,
    max_slope_db_per_span: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize, edge-pad, and validate draw control points."""

    # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
    points = normalize_target_points(control_points)
    # Codex说明(自动生成)： 检查条件 len(points) < 2，根据结果选择后续执行路径。
    if len(points) < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Draw mode requires at least two insertion-l...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw mode requires at least two insertion-loss points")

    # Codex说明(自动生成)： 计算并保存 control_frequencies，供后续语句继续读取或更新。
    control_frequencies = np.asarray([point.frequency_hz for point in points], dtype=float)
    # Codex说明(自动生成)： 计算并保存 control_losses，供后续语句继续读取或更新。
    control_losses = np.asarray([point.loss_db for point in points], dtype=float)
    # Codex说明(自动生成)： 检查条件 np.any(control_frequencies < frequency_hz[0]) or np.any...，根据结果选择后续执行路径。
    if (
        np.any(control_frequencies < frequency_hz[0])
        or np.any(control_frequencies > frequency_hz[-1])
    ):
        # Codex说明(自动生成)： 抛出 ValueError('Draw control points must be inside the gene...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control points must be inside the generated frequency range")

    # Codex说明(自动生成)： 检查条件 control_frequencies[0] > frequency_hz[0]，根据结果选择后续执行路径。
    if control_frequencies[0] > frequency_hz[0]:
        # Codex说明(自动生成)： 计算并保存 control_frequencies，供后续语句继续读取或更新。
        control_frequencies = np.concatenate([[frequency_hz[0]], control_frequencies])
        # Codex说明(自动生成)： 计算并保存 control_losses，供后续语句继续读取或更新。
        control_losses = np.concatenate([[control_losses[0]], control_losses])
    # Codex说明(自动生成)： 检查条件 control_frequencies[-1] < frequency_hz[-1]，根据结果选择后续执行路径。
    if control_frequencies[-1] < frequency_hz[-1]:
        # Codex说明(自动生成)： 计算并保存 control_frequencies，供后续语句继续读取或更新。
        control_frequencies = np.concatenate([control_frequencies, [frequency_hz[-1]]])
        # Codex说明(自动生成)： 计算并保存 control_losses，供后续语句继续读取或更新。
        control_losses = np.concatenate([control_losses, [control_losses[-1]]])

    # Codex说明(自动生成)： 计算并保存 control_x，供后续语句继续读取或更新。
    control_x = _draw_fit_domain(control_frequencies, fit_domain)
    # Codex说明(自动生成)： 调用 _validate_draw_control_shape，执行当前流程需要的具体操作或副作用。
    _validate_draw_control_shape(
        control_x,
        control_losses,
        min_spacing_fraction=min_spacing_fraction,
        max_slope_db_per_span=max_slope_db_per_span,
    )
    # Codex说明(自动生成)： 返回 (control_frequencies, control_losses)，让调用方取得本函数的处理结果。
    return control_frequencies, control_losses


# Codex说明(自动生成)： 定义函数 _draw_fit_domain，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _draw_fit_domain(frequency_hz: np.ndarray, fit_domain: str) -> np.ndarray:
    """Map draw-fit frequencies into the x-domain used by the smoother."""

    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = np.asarray(frequency_hz, dtype=float)
    # Codex说明(自动生成)： 计算并保存 fit_domain，供后续语句继续读取或更新。
    fit_domain = fit_domain.lower()
    # Codex说明(自动生成)： 检查条件 fit_domain == 'linear'，根据结果选择后续执行路径。
    if fit_domain == "linear":
        # Codex说明(自动生成)： 返回 frequency_hz，让调用方取得本函数的处理结果。
        return frequency_hz
    # Codex说明(自动生成)： 检查条件 fit_domain == 'log'，根据结果选择后续执行路径。
    if fit_domain == "log":
        # Codex说明(自动生成)： 返回 np.log10(frequency_hz)，让调用方取得本函数的处理结果。
        return np.log10(frequency_hz)
    # Codex说明(自动生成)： 抛出 ValueError("Draw fit domain must be 'linear' or 'log'")，明确提示输入、状态或处理流程无法继续。
    raise ValueError("Draw fit domain must be 'linear' or 'log'")


# Codex说明(自动生成)： 定义函数 _validate_draw_control_shape，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_draw_control_shape(
    control_x: np.ndarray,
    control_y: np.ndarray,
    *,
    min_spacing_fraction: float,
    max_slope_db_per_span: float,
) -> None:
    """Reject control points that would create near-vertical fitted segments."""

    # Codex说明(自动生成)： 检查条件 min_spacing_fraction < 0，根据结果选择后续执行路径。
    if min_spacing_fraction < 0:
        # Codex说明(自动生成)： 抛出 ValueError('Draw minimum spacing fraction must be non-n...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw minimum spacing fraction must be non-negative")
    # Codex说明(自动生成)： 检查条件 max_slope_db_per_span < 0，根据结果选择后续执行路径。
    if max_slope_db_per_span < 0:
        # Codex说明(自动生成)： 抛出 ValueError('Draw maximum slope must be non-negative')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw maximum slope must be non-negative")
    # Codex说明(自动生成)： 计算并保存 span，供后续语句继续读取或更新。
    span = float(control_x[-1] - control_x[0])
    # Codex说明(自动生成)： 检查条件 not np.isfinite(span) or span <= 0，根据结果选择后续执行路径。
    if not np.isfinite(span) or span <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Draw control frequency span must be positive')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control frequency span must be positive")

    # Codex说明(自动生成)： 计算并保存 spacing，供后续语句继续读取或更新。
    spacing = np.diff(control_x)
    # Codex说明(自动生成)： 计算并保存 loss_delta，供后续语句继续读取或更新。
    loss_delta = np.abs(np.diff(control_y))
    # Codex说明(自动生成)： 检查条件 np.any(spacing <= 0)，根据结果选择后续执行路径。
    if np.any(spacing <= 0):
        # Codex说明(自动生成)： 抛出 ValueError('Draw control frequencies must be strictly i...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control frequencies must be strictly increasing")

    # Codex说明(自动生成)： 检查条件 min_spacing_fraction > 0，根据结果选择后续执行路径。
    if min_spacing_fraction > 0:
        # Codex说明(自动生成)： 计算并保存 min_spacing，供后续语句继续读取或更新。
        min_spacing = min_spacing_fraction * span
        # Codex说明(自动生成)： 计算并保存 too_close，供后续语句继续读取或更新。
        too_close = (spacing < min_spacing) & (loss_delta > 1e-9)
        # Codex说明(自动生成)： 检查条件 np.any(too_close)，根据结果选择后续执行路径。
        if np.any(too_close):
            # Codex说明(自动生成)： 抛出 ValueError('Draw control points are too close for a smo...，明确提示输入、状态或处理流程无法继续。
            raise ValueError(
                "Draw control points are too close for a smooth insertion-loss fit; "
                "spread the points farther apart or lower the minimum spacing"
            )

    # Codex说明(自动生成)： 检查条件 max_slope_db_per_span > 0，根据结果选择后续执行路径。
    if max_slope_db_per_span > 0:
        # Codex说明(自动生成)： 计算并保存 normalized_slope，供后续语句继续读取或更新。
        normalized_slope = loss_delta / (spacing / span)
        # Codex说明(自动生成)： 检查条件 np.any(normalized_slope > max_slope_db_per_span)，根据结果选择后续执行路径。
        if np.any(normalized_slope > max_slope_db_per_span):
            # Codex说明(自动生成)： 抛出 ValueError('Draw control points are too steep for a smo...，明确提示输入、状态或处理流程无法继续。
            raise ValueError(
                "Draw control points are too steep for a smooth insertion-loss fit; "
                "add gentler intermediate points or raise the maximum slope"
            )


# Codex说明(自动生成)： 定义函数 _shape_preserving_cubic_interpolate，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _shape_preserving_cubic_interpolate(
    query_x: np.ndarray,
    control_x: np.ndarray,
    control_y: np.ndarray,
    *,
    slope_scale: float = 1.0,
) -> np.ndarray:
    """Evaluate a monotone-safe cubic Hermite curve through control points.

    The slope limiter follows the same idea as PCHIP: local extrema get zero
    slope and monotonic intervals keep their shape. Each evaluated interval is
    clipped to the two neighboring control losses as a final guard against
    small numerical overshoot.
    """

    # Codex说明(自动生成)： 计算并保存 query_x，供后续语句继续读取或更新。
    query_x = np.asarray(query_x, dtype=float)
    # Codex说明(自动生成)： 计算并保存 control_x，供后续语句继续读取或更新。
    control_x = np.asarray(control_x, dtype=float)
    # Codex说明(自动生成)： 计算并保存 control_y，供后续语句继续读取或更新。
    control_y = np.asarray(control_y, dtype=float)
    # Codex说明(自动生成)： 检查条件 control_x.ndim != 1 or control_y.ndim != 1 or control_x...，根据结果选择后续执行路径。
    if control_x.ndim != 1 or control_y.ndim != 1 or control_x.size != control_y.size:
        # Codex说明(自动生成)： 抛出 ValueError('Draw control arrays must be one-dimensional...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control arrays must be one-dimensional and aligned")
    # Codex说明(自动生成)： 检查条件 control_x.size < 2，根据结果选择后续执行路径。
    if control_x.size < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Draw mode requires at least two insertion-l...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw mode requires at least two insertion-loss points")
    # Codex说明(自动生成)： 检查条件 np.any(np.diff(control_x) <= 0)，根据结果选择后续执行路径。
    if np.any(np.diff(control_x) <= 0):
        # Codex说明(自动生成)： 抛出 ValueError('Draw control frequencies must be strictly i...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Draw control frequencies must be strictly increasing")

    # 斜率缩放用于调节曲线张力；0 表示控制点处趋平，1 表示完整 PCHIP 斜率。
    slopes = slope_scale * _shape_preserving_slopes(control_x, control_y)
    # Codex说明(自动生成)： 计算并保存 segment，供后续语句继续读取或更新。
    segment = np.searchsorted(control_x, query_x, side="right") - 1
    # Codex说明(自动生成)： 计算并保存 segment，供后续语句继续读取或更新。
    segment = np.clip(segment, 0, control_x.size - 2)
    # Codex说明(自动生成)： 计算并保存 x0，供后续语句继续读取或更新。
    x0 = control_x[segment]
    # Codex说明(自动生成)： 计算并保存 x1，供后续语句继续读取或更新。
    x1 = control_x[segment + 1]
    # Codex说明(自动生成)： 计算并保存 y0，供后续语句继续读取或更新。
    y0 = control_y[segment]
    # Codex说明(自动生成)： 计算并保存 y1，供后续语句继续读取或更新。
    y1 = control_y[segment + 1]
    # Codex说明(自动生成)： 计算并保存 m0，供后续语句继续读取或更新。
    m0 = slopes[segment]
    # Codex说明(自动生成)： 计算并保存 m1，供后续语句继续读取或更新。
    m1 = slopes[segment + 1]
    # Codex说明(自动生成)： 计算并保存 h，供后续语句继续读取或更新。
    h = x1 - x0
    # Codex说明(自动生成)： 计算并保存 t，供后续语句继续读取或更新。
    t = (query_x - x0) / h

    # Codex说明(自动生成)： 计算并保存 h00，供后续语句继续读取或更新。
    h00 = 2.0 * t**3 - 3.0 * t**2 + 1.0
    # Codex说明(自动生成)： 计算并保存 h10，供后续语句继续读取或更新。
    h10 = t**3 - 2.0 * t**2 + t
    # Codex说明(自动生成)： 计算并保存 h01，供后续语句继续读取或更新。
    h01 = -2.0 * t**3 + 3.0 * t**2
    # Codex说明(自动生成)： 计算并保存 h11，供后续语句继续读取或更新。
    h11 = t**3 - t**2
    # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
    y = h00 * y0 + h10 * h * m0 + h01 * y1 + h11 * h * m1

    # Codex说明(自动生成)： 计算并保存 lower，供后续语句继续读取或更新。
    lower = np.minimum(y0, y1)
    # Codex说明(自动生成)： 计算并保存 upper，供后续语句继续读取或更新。
    upper = np.maximum(y0, y1)
    # Codex说明(自动生成)： 返回 np.clip(y, lower, upper)，让调用方取得本函数的处理结果。
    return np.clip(y, lower, upper)


# Codex说明(自动生成)： 定义函数 _shape_preserving_slopes，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _shape_preserving_slopes(control_x: np.ndarray, control_y: np.ndarray) -> np.ndarray:
    """Compute limited Hermite slopes for smooth drawn insertion-loss fitting."""

    # Codex说明(自动生成)： 计算并保存 n_points，供后续语句继续读取或更新。
    n_points = control_x.size
    # Codex说明(自动生成)： 计算并保存 h，供后续语句继续读取或更新。
    h = np.diff(control_x)
    # Codex说明(自动生成)： 计算并保存 delta，供后续语句继续读取或更新。
    delta = np.diff(control_y) / h
    # Codex说明(自动生成)： 计算并保存 slopes，供后续语句继续读取或更新。
    slopes = np.zeros(n_points, dtype=float)
    # Codex说明(自动生成)： 检查条件 n_points == 2，根据结果选择后续执行路径。
    if n_points == 2:
        # With only two clicked points there is no local curvature information.
        # Zero endpoint slopes produce a smoothstep transition instead of a
        # visually abrupt straight ramp.
        return slopes

    # Codex说明(自动生成)： 遍历 range(1, n_points - 1) 中的 index，逐项执行循环体逻辑。
    for index in range(1, n_points - 1):
        # Codex说明(自动生成)： 计算并保存 left，供后续语句继续读取或更新。
        left = delta[index - 1]
        # Codex说明(自动生成)： 计算并保存 right，供后续语句继续读取或更新。
        right = delta[index]
        # Codex说明(自动生成)： 检查条件 left == 0.0 or right == 0.0 or np.sign(left) != np.sign...，根据结果选择后续执行路径。
        if left == 0.0 or right == 0.0 or np.sign(left) != np.sign(right):
            # Codex说明(自动生成)： 计算并保存 slopes[index]，供后续语句继续读取或更新。
            slopes[index] = 0.0
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        # Codex说明(自动生成)： 计算并保存 w1，供后续语句继续读取或更新。
        w1 = 2.0 * h[index] + h[index - 1]
        # Codex说明(自动生成)： 计算并保存 w2，供后续语句继续读取或更新。
        w2 = h[index] + 2.0 * h[index - 1]
        # Codex说明(自动生成)： 计算并保存 slopes[index]，供后续语句继续读取或更新。
        slopes[index] = (w1 + w2) / (w1 / left + w2 / right)

    # Codex说明(自动生成)： 计算并保存 slopes[0]，供后续语句继续读取或更新。
    slopes[0] = _limited_endpoint_slope(h[0], h[1], delta[0], delta[1])
    # Codex说明(自动生成)： 计算并保存 slopes[-1]，供后续语句继续读取或更新。
    slopes[-1] = _limited_endpoint_slope(h[-1], h[-2], delta[-1], delta[-2])
    # Codex说明(自动生成)： 返回 slopes，让调用方取得本函数的处理结果。
    return slopes


# Codex说明(自动生成)： 定义函数 _limited_endpoint_slope，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _limited_endpoint_slope(
    h_edge: float,
    h_next: float,
    delta_edge: float,
    delta_next: float,
) -> float:
    """Limit an endpoint slope so the fitted draw curve stays shape-preserving."""

    # Codex说明(自动生成)： 计算并保存 slope，供后续语句继续读取或更新。
    slope = ((2.0 * h_edge + h_next) * delta_edge - h_edge * delta_next) / (
        h_edge + h_next
    )
    # Codex说明(自动生成)： 检查条件 slope == 0.0 or np.sign(slope) != np.sign(delta_edge)，根据结果选择后续执行路径。
    if slope == 0.0 or np.sign(slope) != np.sign(delta_edge):
        # Codex说明(自动生成)： 返回 0.0，让调用方取得本函数的处理结果。
        return 0.0
    # Codex说明(自动生成)： 检查条件 np.sign(delta_edge) != np.sign(delta_next) and abs(slop...，根据结果选择后续执行路径。
    if np.sign(delta_edge) != np.sign(delta_next) and abs(slope) > abs(3.0 * delta_edge):
        # Codex说明(自动生成)： 返回 3.0 * delta_edge，让调用方取得本函数的处理结果。
        return 3.0 * delta_edge
    # Codex说明(自动生成)： 返回 slope，让调用方取得本函数的处理结果。
    return slope


# Codex说明(自动生成)： 定义函数 parse_pair，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def parse_pair(value: str, n_ports: int) -> tuple[int, int]:
    """Parse S-parameter pair syntax, accepting S21 or 2,1."""

    # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
    text = value.strip().lower()
    # Codex说明(自动生成)： 计算并保存 match，供后续语句继续读取或更新。
    match = re.fullmatch(r"s([1-9])([1-9])", text)
    # Codex说明(自动生成)： 检查条件 match，根据结果选择后续执行路径。
    if match:
        # Codex说明(自动生成)： 计算并保存 out_port，供后续语句继续读取或更新。
        out_port = int(match.group(1)) - 1
        # Codex说明(自动生成)： 计算并保存 in_port，供后续语句继续读取或更新。
        in_port = int(match.group(2)) - 1
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 计算并保存 match，供后续语句继续读取或更新。
        match = re.fullmatch(r"([1-9])\s*[,/:]\s*([1-9])", text)
        # Codex说明(自动生成)： 检查条件 not match，根据结果选择后续执行路径。
        if not match:
            # Codex说明(自动生成)： 抛出 ValueError(f'Pair {value!r} must look like S21 or 2,1')，明确提示输入、状态或处理流程无法继续。
            raise ValueError(f"Pair {value!r} must look like S21 or 2,1")
        # Codex说明(自动生成)： 计算并保存 out_port，供后续语句继续读取或更新。
        out_port = int(match.group(1)) - 1
        # Codex说明(自动生成)： 计算并保存 in_port，供后续语句继续读取或更新。
        in_port = int(match.group(2)) - 1

    # Codex说明(自动生成)： 检查条件 out_port >= n_ports or in_port >= n_ports，根据结果选择后续执行路径。
    if out_port >= n_ports or in_port >= n_ports:
        # Codex说明(自动生成)： 抛出 ValueError(f'Pair {value!r} is outside an S{n_ports}P m...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Pair {value!r} is outside an S{n_ports}P matrix")
    # Codex说明(自动生成)： 返回 (out_port, in_port)，让调用方取得本函数的处理结果。
    return out_port, in_port


# Codex说明(自动生成)： 定义函数 parse_pairs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def parse_pairs(values: Sequence[str] | None, n_ports: int) -> list[tuple[int, int]]:
    # Codex说明(自动生成)： 检查条件 not values，根据结果选择后续执行路径。
    if not values:
        # Codex说明(自动生成)： 返回 default_through_pairs(n_ports)，让调用方取得本函数的处理结果。
        return default_through_pairs(n_ports)
    # Codex说明(自动生成)： 声明并保存 pairs，同时保留类型信息方便维护和静态检查。
    pairs: list[tuple[int, int]] = []
    # Codex说明(自动生成)： 遍历 values 中的 value，逐项执行循环体逻辑。
    for value in values:
        # Codex说明(自动生成)： 遍历 str(value).split() 中的 part，逐项执行循环体逻辑。
        for part in str(value).split():
            # Codex说明(自动生成)： 调用 pairs.append 更新列表或集合，把当前步骤产生的数据加入结果。
            pairs.append(parse_pair(part, n_ports))
    # Codex说明(自动生成)： 返回 _dedupe_pairs(pairs)，让调用方取得本函数的处理结果。
    return _dedupe_pairs(pairs)


# Codex说明(自动生成)： 定义函数 default_through_pairs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def default_through_pairs(n_ports: int) -> list[tuple[int, int]]:
    """Default through paths.

    Ports are paired as independent reciprocal lanes: 1<->2, 3<->4, and so
    on.  For an odd three-port network the final port is left matched with the
    configured crosstalk floor.  Use --through-pair/--pair to describe another
    topology such as a splitter or circulator explicitly.
    """

    # Codex说明(自动生成)： 检查条件 n_ports not in COMMON_PORT_COUNTS，根据结果选择后续执行路径。
    if n_ports not in COMMON_PORT_COUNTS:
        # Codex说明(自动生成)： 计算并保存 allowed，供后续语句继续读取或更新。
        allowed = ", ".join(str(value) for value in COMMON_PORT_COUNTS)
        # Codex说明(自动生成)： 抛出 ValueError(f'Supported port counts are {allowed}; got {...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Supported port counts are {allowed}; got {n_ports}")
    # Codex说明(自动生成)： 返回 [pair for first in range(0, n_ports - 1, 2) for pair in...，让调用方取得本函数的处理结果。
    return [
        pair
        for first in range(0, n_ports - 1, 2)
        for pair in ((first + 1, first), (first, first + 1))
    ]


# Codex说明(自动生成)： 定义函数 pair_name，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def pair_name(pair: tuple[int, int]) -> str:
    # Codex说明(自动生成)： 返回 f'S{pair[0] + 1}{pair[1] + 1}'，让调用方取得本函数的处理结果。
    return f"S{pair[0] + 1}{pair[1] + 1}"


# Codex说明(自动生成)： 定义函数 linear_loss，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def linear_loss(
    frequency_hz: np.ndarray,
    loss_start_db: float,
    loss_stop_db: float,
) -> np.ndarray:
    # Codex说明(自动生成)： 计算并保存 fraction，供后续语句继续读取或更新。
    fraction = (frequency_hz - frequency_hz[0]) / (frequency_hz[-1] - frequency_hz[0])
    # Codex说明(自动生成)： 返回 loss_start_db + fraction * (loss_stop_db - loss_start_db)，让调用方取得本函数的处理结果。
    return loss_start_db + fraction * (loss_stop_db - loss_start_db)


# Codex说明(自动生成)： 定义函数 protocol_loss，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def protocol_loss(
    frequency_hz: np.ndarray,
    *,
    a: float,
    b: float,
    c: float,
    model_frequency_unit: str = "ghz",
) -> np.ndarray:
    """Evaluate the protocol insertion-loss formula ``a*f + b*sqrt(f) + c``.

    ``f`` is expressed in ``model_frequency_unit`` and the result is insertion
    loss in dB. The formula defines the magnitude curve; sampled passivity and
    broadband causality remain separate properties of the complete S-matrix.
    """
    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    unit = model_frequency_unit.lower()
    # Codex说明(自动生成)： 检查条件 unit not in FREQUENCY_UNITS，根据结果选择后续执行路径。
    if unit not in FREQUENCY_UNITS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported model frequency unit: {model_f...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported model frequency unit: {model_frequency_unit}")
    # Codex说明(自动生成)： 计算并保存 f_model，供后续语句继续读取或更新。
    f_model = frequency_hz / FREQUENCY_UNITS[unit]
    # Codex说明(自动生成)： 返回 a * f_model + b * np.sqrt(f_model) + c，让调用方取得本函数的处理结果。
    return a * f_model + b * np.sqrt(f_model) + c
# Codex说明(自动生成)： 定义函数 generate_frequency_axis，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def generate_frequency_axis(
    start_hz: float,
    stop_hz: float,
    points: int,
    *,
    spacing: str = "linear",
) -> np.ndarray:
    # Codex说明(自动生成)： 检查条件 points < 2，根据结果选择后续执行路径。
    if points < 2:
        # Codex说明(自动生成)： 抛出 ValueError('At least two frequency points are required')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("At least two frequency points are required")
    # Codex说明(自动生成)： 检查条件 start_hz <= 0 or stop_hz <= 0 or stop_hz <= start_hz，根据结果选择后续执行路径。
    if start_hz <= 0 or stop_hz <= 0 or stop_hz <= start_hz:
        # Codex说明(自动生成)： 抛出 ValueError('Frequency sweep must satisfy 0 < start < st...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequency sweep must satisfy 0 < start < stop")
    # Codex说明(自动生成)： 检查条件 spacing == 'linear'，根据结果选择后续执行路径。
    if spacing == "linear":
        # Codex说明(自动生成)： 返回 np.linspace(start_hz, stop_hz, points)，让调用方取得本函数的处理结果。
        return np.linspace(start_hz, stop_hz, points)
    # Codex说明(自动生成)： 检查条件 spacing == 'log'，根据结果选择后续执行路径。
    if spacing == "log":
        # Codex说明(自动生成)： 返回 np.geomspace(start_hz, stop_hz, points)，让调用方取得本函数的处理结果。
        return np.geomspace(start_hz, stop_hz, points)
    # Codex说明(自动生成)： 抛出 ValueError("Spacing must be 'linear' or 'log'")，明确提示输入、状态或处理流程无法继续。
    raise ValueError("Spacing must be 'linear' or 'log'")


# Codex说明(自动生成)： 定义函数 _ensure_passive_matrix，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _ensure_passive_matrix(
    frequency_hz: np.ndarray,
    s: np.ndarray,
    *,
    context: str,
    tolerance: float = 1.0e-9,
) -> None:
    """Reject a sampled S matrix whose worst singular value exceeds one."""

    # Codex说明(自动生成)： 计算并保存 singular_values，供后续语句继续读取或更新。
    singular_values = np.linalg.svd(s, compute_uv=False)
    # Codex说明(自动生成)： 计算并保存 maximum_singular_value，供后续语句继续读取或更新。
    maximum_singular_value = np.max(singular_values, axis=1)
    # Codex说明(自动生成)： 计算并保存 worst_index，供后续语句继续读取或更新。
    worst_index = int(np.argmax(maximum_singular_value))
    # Codex说明(自动生成)： 计算并保存 worst_value，供后续语句继续读取或更新。
    worst_value = float(maximum_singular_value[worst_index])
    # Codex说明(自动生成)： 检查条件 worst_value > 1.0 + tolerance，根据结果选择后续执行路径。
    if worst_value > 1.0 + tolerance:
        # Codex说明(自动生成)： 抛出 ValueError(f'{context} S-parameter matrix is not passiv...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            f"{context} S-parameter matrix is not passive: "
            f"maximum singular value {worst_value:.6g} "
            f"at {float(frequency_hz[worst_index]):.6g} Hz."
        )


# Codex说明(自动生成)： 定义函数 build_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def build_network(
    frequency_hz: np.ndarray,
    n_ports: int,
    insertion_loss_db: np.ndarray,
    *,
    through_pairs: Sequence[tuple[int, int]] | None = None,
    return_loss_db: float = 20.0,
    crosstalk_db: float = 80.0,
    delay_ps: float = 0.0,
    phase_offset_deg: float = 0.0,
    z0: float = 50.0,
) -> TouchstoneData:
    """Create a reciprocal network made from independent adjacent lanes."""

    # Codex说明(自动生成)： 检查条件 n_ports not in COMMON_PORT_COUNTS，根据结果选择后续执行路径。
    if n_ports not in COMMON_PORT_COUNTS:
        # Codex说明(自动生成)： 计算并保存 allowed，供后续语句继续读取或更新。
        allowed = ", ".join(str(value) for value in COMMON_PORT_COUNTS)
        # Codex说明(自动生成)： 抛出 ValueError(f'Supported port counts are {allowed}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Supported port counts are {allowed}")
    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = np.asarray(frequency_hz, dtype=float)
    # Codex说明(自动生成)： 调用 _validate_frequency_grid 生成或展示图形，便于观察计算结果。
    _validate_frequency_grid(frequency_hz)
    # Codex说明(自动生成)： 调用 _validate_loss_value，执行当前流程需要的具体操作或副作用。
    _validate_loss_value(return_loss_db, "Return loss")
    # Codex说明(自动生成)： 调用 _validate_loss_value，执行当前流程需要的具体操作或副作用。
    _validate_loss_value(crosstalk_db, "Crosstalk loss")
    # Codex说明(自动生成)： 检查条件 not np.isfinite(delay_ps)，根据结果选择后续执行路径。
    if not np.isfinite(delay_ps):
        # Codex说明(自动生成)： 抛出 ValueError('Delay must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Delay must be finite")
    # Codex说明(自动生成)： 检查条件 not np.isfinite(phase_offset_deg)，根据结果选择后续执行路径。
    if not np.isfinite(phase_offset_deg):
        # Codex说明(自动生成)： 抛出 ValueError('Phase offset must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Phase offset must be finite")
    # Codex说明(自动生成)： 检查条件 not np.isfinite(z0) or z0 <= 0，根据结果选择后续执行路径。
    if not np.isfinite(z0) or z0 <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Reference impedance z0 must be positive and...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Reference impedance z0 must be positive and finite")

    # Codex说明(自动生成)： 计算并保存 through_pairs，供后续语句继续读取或更新。
    through_pairs = _normalize_generation_through_pairs(
        list(through_pairs or default_through_pairs(n_ports)),
        n_ports,
    )
    # Codex说明(自动生成)： 计算并保存 insertion_loss_db，供后续语句继续读取或更新。
    insertion_loss_db = np.asarray(insertion_loss_db, dtype=float)
    # Codex说明(自动生成)： 检查条件 insertion_loss_db.shape != frequency_hz.shape，根据结果选择后续执行路径。
    if insertion_loss_db.shape != frequency_hz.shape:
        # Codex说明(自动生成)： 抛出 ValueError('Insertion loss array must match the frequen...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Insertion loss array must match the frequency axis")
    # Codex说明(自动生成)： 调用 _validate_loss_array，执行当前流程需要的具体操作或副作用。
    _validate_loss_array(insertion_loss_db, "Insertion loss")

    # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
    s = np.zeros((frequency_hz.size, n_ports, n_ports), dtype=complex)
    # Codex说明(自动生成)： 计算并保存 delay_s，供后续语句继续读取或更新。
    delay_s = delay_ps * 1e-12
    # Codex说明(自动生成)： 计算并保存 through_phase，供后续语句继续读取或更新。
    through_phase = np.deg2rad(phase_offset_deg) - 2.0 * np.pi * frequency_hz * delay_s
    # Codex说明(自动生成)： 计算并保存 through，供后续语句继续读取或更新。
    through = 10.0 ** (-insertion_loss_db / 20.0) * np.exp(1j * through_phase)

    # 对称互易二端口若反射与传输同相，即使每一项单独都小于 1，也可能因
    # 相干叠加而违反无源条件。把反射相位放在传输相位的正交方向，是这个
    # 简化 matched-loss 模型的物理选择；随后仍用整矩阵奇异值做最终无源检查。
    reflection_magnitude = 10.0 ** (-return_loss_db / 20.0)
    # Codex说明(自动生成)： 计算并保存 reflection，供后续语句继续读取或更新。
    reflection = reflection_magnitude * np.exp(1j * (through_phase + 0.5 * np.pi))
    # Codex说明(自动生成)： 遍历 range(n_ports) 中的 port，逐项执行循环体逻辑。
    for port in range(n_ports):
        # Codex说明(自动生成)： 计算并保存 s[:, port, port]，供后续语句继续读取或更新。
        s[:, port, port] = reflection

    # Codex说明(自动生成)： 计算并保存 through_set，供后续语句继续读取或更新。
    through_set = set(through_pairs)
    # Codex说明(自动生成)： 计算并保存 crosstalk，供后续语句继续读取或更新。
    crosstalk = 10.0 ** (-crosstalk_db / 20.0) * np.exp(1j * through_phase)
    # Codex说明(自动生成)： 遍历 range(n_ports) 中的 out_port，逐项执行循环体逻辑。
    for out_port in range(n_ports):
        # Codex说明(自动生成)： 遍历 range(n_ports) 中的 in_port，逐项执行循环体逻辑。
        for in_port in range(n_ports):
            # Codex说明(自动生成)： 检查条件 out_port == in_port，根据结果选择后续执行路径。
            if out_port == in_port:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 (out_port, in_port) in through_set，根据结果选择后续执行路径。
            if (out_port, in_port) in through_set:
                # Codex说明(自动生成)： 计算并保存 s[:, out_port, in_port]，供后续语句继续读取或更新。
                s[:, out_port, in_port] = through
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 计算并保存 s[:, out_port, in_port]，供后续语句继续读取或更新。
                s[:, out_port, in_port] = crosstalk

    # Codex说明(自动生成)： 调用 _ensure_passive_matrix，执行当前流程需要的具体操作或副作用。
    _ensure_passive_matrix(frequency_hz, s, context="Generated")

    # Codex说明(自动生成)： 返回 TouchstoneData(frequency_hz=np.asarray(frequency_hz), s...，让调用方取得本函数的处理结果。
    return TouchstoneData(frequency_hz=np.asarray(frequency_hz), s=s, z0=z0)


# Codex说明(自动生成)： 定义函数 modify_insertion_loss，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def modify_insertion_loss(
    data: TouchstoneData,
    targets: Sequence[TargetPoint],
    pairs: Sequence[tuple[int, int]],
    *,
    smoothness: float = 0.12,
    smooth_domain: str = "log",
    anchor_edges: bool = True,
    insert_targets: bool = True,
) -> ModificationResult:
    """Smoothly adjust selected insertion-loss paths to target loss values.

    Magnitude is adjusted by a shape-preserving correction in dB. The original
    complex phase of each selected S-parameter is preserved exactly.
    """

    # Codex说明(自动生成)： 检查条件 not np.isfinite(smoothness) or smoothness <= 0，根据结果选择后续执行路径。
    if not np.isfinite(smoothness) or smoothness <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Smoothness must be positive')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Smoothness must be positive")
    # Codex说明(自动生成)： 检查条件 not pairs，根据结果选择后续执行路径。
    if not pairs:
        # Codex说明(自动生成)： 抛出 ValueError('At least one S-parameter pair is required')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("At least one S-parameter pair is required")
    # 修改器不能把输入文件原有的非无源问题误报成目标频点问题，因此先检查原矩阵。
    _ensure_passive_matrix(data.frequency_hz, data.s, context="Input")
    # Codex说明(自动生成)： 计算并保存 targets，供后续语句继续读取或更新。
    targets = normalize_target_points(targets)
    # Codex说明(自动生成)： 计算并保存 working，供后续语句继续读取或更新。
    working = data
    # Codex说明(自动生成)： 计算并保存 target_frequencies，供后续语句继续读取或更新。
    target_frequencies = np.asarray([target.frequency_hz for target in targets])
    # Codex说明(自动生成)： 计算并保存 target_losses，供后续语句继续读取或更新。
    target_losses = np.asarray([target.loss_db for target in targets])
    # Codex说明(自动生成)： 调用 _validate_target_range，执行当前流程需要的具体操作或副作用。
    _validate_target_range(data.frequency_hz, target_frequencies)
    # Codex说明(自动生成)： 调用 _validate_control_spacing，执行当前流程需要的具体操作或副作用。
    _validate_control_spacing(
        data.frequency_hz,
        target_frequencies,
        smooth_domain=smooth_domain,
    )

    # Codex说明(自动生成)： 检查条件 insert_targets，根据结果选择后续执行路径。
    if insert_targets:
        # Codex说明(自动生成)： 计算并保存 working，供后续语句继续读取或更新。
        working = resample_with_frequencies(working, target_frequencies)

    # Codex说明(自动生成)： 计算并保存 modified_s，供后续语句继续读取或更新。
    modified_s = np.array(working.s, copy=True)
    # Codex说明(自动生成)： 声明并保存 results，同时保留类型信息方便维护和静态检查。
    results: list[TargetResult] = []

    # Codex说明(自动生成)： 遍历 pairs 中的 pair，逐项执行循环体逻辑。
    for pair in pairs:
        # Codex说明(自动生成)： 计算并保存 (out_port, in_port)，供后续语句继续读取或更新。
        out_port, in_port = pair
        # Codex说明(自动生成)： 计算并保存 original，供后续语句继续读取或更新。
        original = working.s[:, out_port, in_port]
        # Codex说明(自动生成)： 计算并保存 original_loss_grid，供后续语句继续读取或更新。
        original_loss_grid = -to_magnitude_db(original)
        # Codex说明(自动生成)： 计算并保存 original_loss_at_targets，供后续语句继续读取或更新。
        original_loss_at_targets = np.interp(
            target_frequencies, working.frequency_hz, original_loss_grid
        )
        # Codex说明(自动生成)： 计算并保存 delta_at_targets，供后续语句继续读取或更新。
        delta_at_targets = target_losses - original_loss_at_targets
        # 形状保持修正精确经过目标点，并避免无约束 RBF 在目标点之间产生正负振荡。
        correction = smooth_shape_preserving_correction(
            working.frequency_hz,
            target_frequencies,
            delta_at_targets,
            smoothness=smoothness,
            domain=smooth_domain,
            anchor_edges=anchor_edges,
        )
        # Codex说明(自动生成)： 计算并保存 new_loss_grid，供后续语句继续读取或更新。
        new_loss_grid = original_loss_grid + correction
        # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(new_loss_grid))，根据结果选择后续执行路径。
        if np.any(~np.isfinite(new_loss_grid)):
            # Codex说明(自动生成)： 抛出 ValueError('Smoothing generated non-finite insertion-lo...，明确提示输入、状态或处理流程无法继续。
            raise ValueError("Smoothing generated non-finite insertion-loss values")
        # Codex说明(自动生成)： 计算并保存 phase_unit，供后续语句继续读取或更新。
        phase_unit = np.exp(1j * np.angle(original))
        # Codex说明(自动生成)： 计算并保存 modified_s[:, out_port, in_port]，供后续语句继续读取或更新。
        modified_s[:, out_port, in_port] = 10.0 ** (-new_loss_grid / 20.0) * phase_unit
        # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(modified_s[:, out_port, in_port]))，根据结果选择后续执行路径。
        if np.any(~np.isfinite(modified_s[:, out_port, in_port])):
            # Codex说明(自动生成)： 抛出 ValueError('Smoothing generated non-finite S-parameter ...，明确提示输入、状态或处理流程无法继续。
            raise ValueError("Smoothing generated non-finite S-parameter values")

        # Codex说明(自动生成)： 计算并保存 achieved_loss_grid，供后续语句继续读取或更新。
        achieved_loss_grid = -to_magnitude_db(modified_s[:, out_port, in_port])
        # Codex说明(自动生成)： 遍历 zip(targets, target_losses, original_loss_at_targets) 中的 (target, requested, before)，逐项执行循环体逻辑。
        for target, requested, before in zip(targets, target_losses, original_loss_at_targets):
            # Codex说明(自动生成)： 计算并保存 achieved，供后续语句继续读取或更新。
            achieved = float(np.interp(target.frequency_hz, working.frequency_hz, achieved_loss_grid))
            # Codex说明(自动生成)： 计算并保存 phase_before，供后续语句继续读取或更新。
            phase_before = np.interp(
                target.frequency_hz,
                working.frequency_hz,
                np.unwrap(np.angle(original)),
            )
            # Codex说明(自动生成)： 计算并保存 phase_after，供后续语句继续读取或更新。
            phase_after = np.interp(
                target.frequency_hz,
                working.frequency_hz,
                np.unwrap(np.angle(modified_s[:, out_port, in_port])),
            )
            # Codex说明(自动生成)： 调用 results.append 更新列表或集合，把当前步骤产生的数据加入结果。
            results.append(
                TargetResult(
                    pair=pair_name(pair),
                    frequency_hz=target.frequency_hz,
                    requested_loss_db=float(requested),
                    original_loss_db=float(before),
                    achieved_loss_db=achieved,
                    phase_delta_deg=float(np.rad2deg(phase_after - phase_before)),
                )
            )

    # 非目标频点若仅因平滑曲线超限，就沿原矩阵到候选矩阵的凸线段收缩修改量。
    modified_s = constrain_smoothed_points_to_passivity(
        working.frequency_hz,
        working.s,
        modified_s,
        target_frequencies,
    )
    # 约束可能改变非插入目标的邻近样点，因此报告必须从最终矩阵重新计算。
    final_results: list[TargetResult] = []
    # 每条旧记录保留目标请求和修改前读数，只刷新最终达到值与相位差。
    for item in results:
        # 报告中的标准 Sij 名称重新解析为矩阵下标，确保多端口方向不被转置。
        out_port, in_port = parse_pair(item.pair, working.n_ports)
        # 最终插损从约束后的复数矩阵计算，不能复用约束前的临时曲线。
        final_loss_grid = -to_magnitude_db(modified_s[:, out_port, in_port])
        # 未插入目标频点时仍按输出网格线性插值报告实际达到值。
        achieved = float(
            np.interp(item.frequency_hz, working.frequency_hz, final_loss_grid)
        )
        # 修改前相位使用与既有合同一致的解缠相位插值。
        phase_before = np.interp(
            item.frequency_hz,
            working.frequency_hz,
            np.unwrap(np.angle(working.s[:, out_port, in_port])),
        )
        # 修改后相位从最终矩阵读取，验证无源收缩没有引入相位旋转。
        phase_after = np.interp(
            item.frequency_hz,
            working.frequency_hz,
            np.unwrap(np.angle(modified_s[:, out_port, in_port])),
        )
        # 写入最终报告记录，保留用户请求、原始插损和标准端口名称。
        final_results.append(
            TargetResult(
                pair=item.pair,
                frequency_hz=item.frequency_hz,
                requested_loss_db=item.requested_loss_db,
                original_loss_db=item.original_loss_db,
                achieved_loss_db=achieved,
                phase_delta_deg=float(np.rad2deg(phase_after - phase_before)),
            )
        )
    # 用最终记录替换候选阶段记录，GUI 和文本报告都会看到真实输出数据。
    results = final_results
    # 最终仍用完整 S 矩阵做失败关闭检查，不能用单条 S21 幅度代替无源条件。
    _ensure_passive_matrix(
        working.frequency_hz,
        modified_s,
        context="Modified",
    )
    # Codex说明(自动生成)： 返回 ModificationResult(data=TouchstoneData(frequency_hz=wor...，让调用方取得本函数的处理结果。
    return ModificationResult(
        data=TouchstoneData(
            frequency_hz=working.frequency_hz,
            s=modified_s,
            z0=working.z0,
            source_path=working.source_path,
        ),
        results=results,
    )


# Codex说明(自动生成)： 定义函数 resample_with_frequencies，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def resample_with_frequencies(
    data: TouchstoneData,
    extra_frequencies_hz: Sequence[float],
) -> TouchstoneData:
    """Insert points with unwrapped phase and sampled-passive normalization."""

    # Codex说明(自动生成)： 计算并保存 extra，供后续语句继续读取或更新。
    extra = np.asarray(extra_frequencies_hz, dtype=float)
    # Codex说明(自动生成)： 调用 _validate_target_range，执行当前流程需要的具体操作或副作用。
    _validate_target_range(data.frequency_hz, extra)
    # Codex说明(自动生成)： 计算并保存 combined，供后续语句继续读取或更新。
    combined = np.unique(np.concatenate([data.frequency_hz, extra]))
    # Codex说明(自动生成)： 检查条件 combined.size == data.frequency_hz.size，根据结果选择后续执行路径。
    if combined.size == data.frequency_hz.size:
        # Codex说明(自动生成)： 返回 data，让调用方取得本函数的处理结果。
        return data

    # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
    n_ports = data.n_ports
    # Codex说明(自动生成)： 计算并保存 resampled，供后续语句继续读取或更新。
    resampled = np.zeros((combined.size, n_ports, n_ports), dtype=complex)
    # Codex说明(自动生成)： 遍历 range(n_ports) 中的 out_port，逐项执行循环体逻辑。
    for out_port in range(n_ports):
        # Codex说明(自动生成)： 遍历 range(n_ports) 中的 in_port，逐项执行循环体逻辑。
        for in_port in range(n_ports):
            # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
            values = data.s[:, out_port, in_port]
            # 幅度仍在 dB 域插值，保持已有 Modify 文件的插值合同。
            mag_db = to_magnitude_db(values)
            # 相位先解缠再插值，避免跨越正负 180 度时产生错误跳变。
            phase = np.unwrap(np.angle(values))
            # 新频点幅度采用相邻原始样点的线性 dB 插值。
            new_mag_db = np.interp(combined, data.frequency_hz, mag_db)
            # 新频点相位采用同一频率坐标上的解缠相位插值。
            new_phase = np.interp(combined, data.frequency_hz, phase)
            # 正幅度与插值相位重新合成复数 S 参数，随后统一检查完整矩阵。
            resampled[:, out_port, in_port] = 10.0 ** (new_mag_db / 20.0) * np.exp(
                1j * new_phase
            )
    # 找回每个源频率在合并网格中的精确位置，随后恢复原始复数值，避免极坐标重构漂移。
    source_indices = np.searchsorted(combined, data.frequency_hz)
    # combined 由源频率直接拼接得到；若映射不精确，继续处理会破坏原始样点合同。
    if not np.array_equal(combined[source_indices], data.frequency_hz):
        # Codex说明(自动生成)： 抛出 RuntimeError('Failed to preserve original frequencies w...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Failed to preserve original frequencies while resampling")
    # 原始行逐元素写回，精确零、实部、虚部和符号位均不经过 dB/相位往返。
    resampled[source_indices] = data.s
    # 只把新插入点交给无源归一化；源文件的每一个复数样点保持 bit-for-bit 不变。
    source_mask = np.zeros(combined.size, dtype=bool)
    # Codex说明(自动生成)： 计算并保存 source_mask[source_indices]，供后续语句继续读取或更新。
    source_mask[source_indices] = True
    # 每个新插入频点单独归一化完整 S 矩阵，正比例缩放不会改变任何元素相位。
    for index in np.flatnonzero(~source_mask):
        # 最大奇异值给出该矩阵满足无源条件所需的唯一统一缩放上界。
        sigma_max = float(np.linalg.svd(resampled[index], compute_uv=False)[0])
        # 只处理超出单位边界的插入点，已经无源的插值结果保持原样。
        if sigma_max > 1.0:
            # 除以最大奇异值把该频点精确拉回无源边界，同时保持端口比例和相位。
            resampled[index] = resampled[index] / sigma_max
    # Codex说明(自动生成)： 调用 _ensure_passive_matrix，执行当前流程需要的具体操作或副作用。
    _ensure_passive_matrix(combined, resampled, context="Resampled")
    # Codex说明(自动生成)： 返回 TouchstoneData(frequency_hz=combined, s=resampled, z0=d...，让调用方取得本函数的处理结果。
    return TouchstoneData(
        frequency_hz=combined,
        s=resampled,
        z0=data.z0,
        source_path=data.source_path,
    )


# 形状保持修改器与 Draw 共用经过验证的 Hermite/PCHIP 斜率限制规则。
def smooth_shape_preserving_correction(
    frequency_hz: np.ndarray,
    target_frequencies_hz: np.ndarray,
    target_delta_db: np.ndarray,
    *,
    smoothness: float,
    domain: str,
    anchor_edges: bool,
) -> np.ndarray:
    """Interpolate exact target corrections without control-point overshoot."""

    # Codex说明(自动生成)： 计算并保存 x，供后续语句继续读取或更新。
    x = _frequency_domain(frequency_hz, domain)
    # Codex说明(自动生成)： 计算并保存 controls_x，供后续语句继续读取或更新。
    controls_x = _frequency_domain(target_frequencies_hz, domain)
    # Codex说明(自动生成)： 计算并保存 controls_y，供后续语句继续读取或更新。
    controls_y = np.asarray(target_delta_db, dtype=float)

    # Codex说明(自动生成)： 检查条件 anchor_edges，根据结果选择后续执行路径。
    if anchor_edges:
        # Codex说明(自动生成)： 检查条件 not np.any(controls_x == x[0])，根据结果选择后续执行路径。
        if not np.any(controls_x == x[0]):
            # Codex说明(自动生成)： 计算并保存 controls_x，供后续语句继续读取或更新。
            controls_x = np.concatenate([[x[0]], controls_x])
            # Codex说明(自动生成)： 计算并保存 controls_y，供后续语句继续读取或更新。
            controls_y = np.concatenate([[0.0], controls_y])
        # Codex说明(自动生成)： 检查条件 not np.any(controls_x == x[-1])，根据结果选择后续执行路径。
        if not np.any(controls_x == x[-1]):
            # Codex说明(自动生成)： 计算并保存 controls_x，供后续语句继续读取或更新。
            controls_x = np.concatenate([controls_x, [x[-1]]])
            # Codex说明(自动生成)： 计算并保存 controls_y，供后续语句继续读取或更新。
            controls_y = np.concatenate([controls_y, [0.0]])

    # Codex说明(自动生成)： 计算并保存 (controls_x, unique_indices)，供后续语句继续读取或更新。
    controls_x, unique_indices = np.unique(controls_x, return_index=True)
    # Codex说明(自动生成)： 计算并保存 controls_y，供后续语句继续读取或更新。
    controls_y = controls_y[unique_indices]
    # 单目标且未锚定边缘时仍需局部修改，正权 Gaussian 不会越过零和目标修正量。
    if controls_x.size == 1:
        # Codex说明(自动生成)： 计算并保存 span，供后续语句继续读取或更新。
        span = max(float(x[-1] - x[0]), 1e-12)
        # Codex说明(自动生成)： 计算并保存 sigma，供后续语句继续读取或更新。
        sigma = max(smoothness * span, 1e-12)
        # Codex说明(自动生成)： 返回 controls_y[0] * np.exp(-0.5 * ((x - controls_x[0]) / si...，让调用方取得本函数的处理结果。
        return controls_y[0] * np.exp(-0.5 * ((x - controls_x[0]) / sigma) ** 2)

    # 正张力参数映射到有限区间，避免极端输入产生无限斜率或数值不稳定。
    slope_scale = float(smoothness / (smoothness + 0.1))
    # 形状保持 Hermite 曲线精确经过控制点，并在每段内限制到相邻控制值范围。
    correction = _shape_preserving_cubic_interpolate(
        x,
        controls_x,
        controls_y,
        slope_scale=slope_scale,
    )
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(correction))，根据结果选择后续执行路径。
    if np.any(~np.isfinite(correction)):
        # Codex说明(自动生成)： 抛出 ValueError('Smoothing generated non-finite correction v...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Smoothing generated non-finite correction values")
    # Codex说明(自动生成)： 返回 correction，让调用方取得本函数的处理结果。
    return correction


# Codex说明(自动生成)： 定义函数 plot_sparameters，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def plot_sparameters(
    data: TouchstoneData,
    output_path: str | Path | None,
    *,
    kind: str = "magnitude",
    frequency_unit: str = "ghz",
    show: bool = False,
    block: bool = True,
) -> None:
    """Plot all Sij traces as a matrix grid.

    `output_path=None` means "show only, do not save a PNG". This keeps the
    interactive inspection workflow separate from optional file export.
    """

    # Codex说明(自动生成)： 导入 matplotlib，绘制仿真结果和诊断图形。
    import matplotlib

    # Codex说明(自动生成)： 检查条件 not show and 'matplotlib.pyplot' not in sys.modules，根据结果选择后续执行路径。
    if not show and "matplotlib.pyplot" not in sys.modules:
        # Codex说明(自动生成)： 调用 matplotlib.use 生成或展示图形，便于观察计算结果。
        matplotlib.use("Agg")
    # Codex说明(自动生成)： 导入 matplotlib.pyplot as plt，绘制仿真结果和诊断图形。
    import matplotlib.pyplot as plt

    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    unit = frequency_unit.lower()
    # Codex说明(自动生成)： 检查条件 unit not in FREQUENCY_UNITS，根据结果选择后续执行路径。
    if unit not in FREQUENCY_UNITS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported plot frequency unit: {frequenc...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported plot frequency unit: {frequency_unit}")
    # Codex说明(自动生成)： 计算并保存 x，供后续语句继续读取或更新。
    x = data.frequency_hz / FREQUENCY_UNITS[unit]
    # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
    n_ports = data.n_ports
    # Codex说明(自动生成)： 计算并保存 (fig, axes)，供后续语句继续读取或更新。
    fig, axes = plt.subplots(
        n_ports,
        n_ports,
        figsize=(3.2 * n_ports, 2.45 * n_ports),
        squeeze=False,
        sharex=True,
    )

    # Codex说明(自动生成)： 遍历 range(n_ports) 中的 out_port，逐项执行循环体逻辑。
    for out_port in range(n_ports):
        # Codex说明(自动生成)： 遍历 range(n_ports) 中的 in_port，逐项执行循环体逻辑。
        for in_port in range(n_ports):
            # Codex说明(自动生成)： 计算并保存 ax，供后续语句继续读取或更新。
            ax = axes[out_port, in_port]
            # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
            values = data.s[:, out_port, in_port]
            # Codex说明(自动生成)： 检查条件 kind == 'magnitude'，根据结果选择后续执行路径。
            if kind == "magnitude":
                # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
                y = to_magnitude_db(values)
                # Codex说明(自动生成)： 调用 ax.set_ylabel 生成或展示图形，便于观察计算结果。
                ax.set_ylabel("dB")
            # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 kind == 'phase'。
            elif kind == "phase":
                # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
                y = np.rad2deg(np.unwrap(np.angle(values)))
                # Codex说明(自动生成)： 调用 ax.set_ylabel 生成或展示图形，便于观察计算结果。
                ax.set_ylabel("deg")
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 抛出 ValueError("Plot kind must be 'magnitude' or 'phase'")，明确提示输入、状态或处理流程无法继续。
                raise ValueError("Plot kind must be 'magnitude' or 'phase'")
            # Codex说明(自动生成)： 调用 ax.plot 生成或展示图形，便于观察计算结果。
            ax.plot(x, y, linewidth=1.5)
            # Codex说明(自动生成)： 调用 ax.set_title 生成或展示图形，便于观察计算结果。
            ax.set_title(pair_name((out_port, in_port)), fontsize=10)
            # Codex说明(自动生成)： 调用 ax.grid 生成或展示图形，便于观察计算结果。
            ax.grid(True, alpha=0.3)
            # Codex说明(自动生成)： 检查条件 out_port == n_ports - 1，根据结果选择后续执行路径。
            if out_port == n_ports - 1:
                # Codex说明(自动生成)： 调用 ax.set_xlabel 生成或展示图形，便于观察计算结果。
                ax.set_xlabel(unit.upper())

    # Codex说明(自动生成)： 计算并保存 title，供后续语句继续读取或更新。
    title = "S-parameter magnitude" if kind == "magnitude" else "S-parameter phase"
    # Codex说明(自动生成)： 调用 fig.suptitle 生成或展示图形，便于观察计算结果。
    fig.suptitle(title, fontsize=14)
    # Codex说明(自动生成)： 调用 fig.tight_layout，执行当前流程需要的具体操作或副作用。
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    # Codex说明(自动生成)： 检查条件 output_path is not None，根据结果选择后续执行路径。
    if output_path is not None:
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = Path(output_path)
        # Codex说明(自动生成)： 调用 output.parent.mkdir，执行当前流程需要的具体操作或副作用。
        output.parent.mkdir(parents=True, exist_ok=True)
        # Codex说明(自动生成)： 调用 fig.savefig 生成或展示图形，便于观察计算结果。
        fig.savefig(output, dpi=180)
    # Codex说明(自动生成)： 检查条件 show，根据结果选择后续执行路径。
    if show:
        # Codex说明(自动生成)： 调用 fig.show 生成或展示图形，便于观察计算结果。
        fig.show()
        # Codex说明(自动生成)： 检查条件 block，根据结果选择后续执行路径。
        if block:
            # Codex说明(自动生成)： 调用 plt.show 生成或展示图形，便于观察计算结果。
            plt.show(block=True)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 调用 plt.close，执行当前流程需要的具体操作或副作用。
        plt.close(fig)


# Codex说明(自动生成)： 定义函数 _frequency_domain，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _frequency_domain(frequency_hz: np.ndarray, domain: str) -> np.ndarray:
    # Codex说明(自动生成)： 检查条件 domain == 'linear'，根据结果选择后续执行路径。
    if domain == "linear":
        # Codex说明(自动生成)： 返回 np.asarray(frequency_hz, dtype=float)，让调用方取得本函数的处理结果。
        return np.asarray(frequency_hz, dtype=float)
    # Codex说明(自动生成)： 检查条件 domain == 'log'，根据结果选择后续执行路径。
    if domain == "log":
        # Codex说明(自动生成)： 返回 np.log10(np.asarray(frequency_hz, dtype=float))，让调用方取得本函数的处理结果。
        return np.log10(np.asarray(frequency_hz, dtype=float))
    # Codex说明(自动生成)： 抛出 ValueError("Smooth domain must be 'linear' or 'log'")，明确提示输入、状态或处理流程无法继续。
    raise ValueError("Smooth domain must be 'linear' or 'log'")


# Codex说明(自动生成)： 定义函数 normalize_target_points，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def normalize_target_points(targets: Sequence[TargetPoint]) -> list[TargetPoint]:
    # Codex说明(自动生成)： 检查条件 not targets，根据结果选择后续执行路径。
    if not targets:
        # Codex说明(自动生成)： 抛出 ValueError('At least one target point is required')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("At least one target point is required")

    # Codex说明(自动生成)： 计算并保存 normalized，供后续语句继续读取或更新。
    normalized = sorted(targets, key=lambda target: target.frequency_hz)
    # Codex说明(自动生成)： 声明并保存 output，同时保留类型信息方便维护和静态检查。
    output: list[TargetPoint] = []
    # Codex说明(自动生成)： 遍历 normalized 中的 target，逐项执行循环体逻辑。
    for target in normalized:
        # Codex说明(自动生成)： 检查条件 not np.isfinite(target.frequency_hz) or target.frequenc...，根据结果选择后续执行路径。
        if not np.isfinite(target.frequency_hz) or target.frequency_hz <= 0:
            # Codex说明(自动生成)： 抛出 ValueError('Target frequency must be positive and finite')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("Target frequency must be positive and finite")
        # Codex说明(自动生成)： 调用 _validate_loss_value，执行当前流程需要的具体操作或副作用。
        _validate_loss_value(target.loss_db, "Target insertion loss")
        # Codex说明(自动生成)： 检查条件 output and np.isclose(target.frequency_hz, output[-1].f...，根据结果选择后续执行路径。
        if output and np.isclose(
            target.frequency_hz,
            output[-1].frequency_hz,
            rtol=1e-12,
            atol=1e-6,
        ):
            # Codex说明(自动生成)： 检查条件 np.isclose(target.loss_db, output[-1].loss_db, rtol=1e-...，根据结果选择后续执行路径。
            if np.isclose(target.loss_db, output[-1].loss_db, rtol=1e-12, atol=1e-9):
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 抛出 ValueError(f'Conflicting insertion-loss targets at {tar...，明确提示输入、状态或处理流程无法继续。
            raise ValueError(
                f"Conflicting insertion-loss targets at {target.frequency_hz:.12g} Hz"
            )
        # Codex说明(自动生成)： 调用 output.append 更新列表或集合，把当前步骤产生的数据加入结果。
        output.append(target)
    # Codex说明(自动生成)： 返回 output，让调用方取得本函数的处理结果。
    return output


# Codex说明(自动生成)： 定义函数 _normalize_generation_through_pairs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _normalize_generation_through_pairs(
    pairs: Sequence[tuple[int, int]],
    n_ports: int,
) -> list[tuple[int, int]]:
    # Codex说明(自动生成)： 遍历 pairs 中的 (out_port, in_port)，逐项执行循环体逻辑。
    for out_port, in_port in pairs:
        # Codex说明(自动生成)： 检查条件 out_port == in_port，根据结果选择后续执行路径。
        if out_port == in_port:
            # Codex说明(自动生成)： 抛出 ValueError('Generated through paths must be off-diagona...，明确提示输入、状态或处理流程无法继续。
            raise ValueError("Generated through paths must be off-diagonal S-parameters")

    # Codex说明(自动生成)： 检查条件 n_ports == 2，根据结果选择后续执行路径。
    if n_ports == 2:
        # Codex说明(自动生成)： 返回 [(1, 0), (0, 1)]，让调用方取得本函数的处理结果。
        return [(1, 0), (0, 1)]
    # Codex说明(自动生成)： 返回 _dedupe_pairs(pairs)，让调用方取得本函数的处理结果。
    return _dedupe_pairs(pairs)


# Codex说明(自动生成)： 定义函数 _validate_frequency_grid，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_frequency_grid(frequency_hz: np.ndarray) -> None:
    # Codex说明(自动生成)： 检查条件 frequency_hz.ndim != 1 or frequency_hz.size < 2，根据结果选择后续执行路径。
    if frequency_hz.ndim != 1 or frequency_hz.size < 2:
        # Codex说明(自动生成)： 抛出 ValueError('Frequency axis must be a one-dimensional sw...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequency axis must be a one-dimensional sweep with at least two points")
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(frequency_hz))，根据结果选择后续执行路径。
    if np.any(~np.isfinite(frequency_hz)):
        # Codex说明(自动生成)： 抛出 ValueError('Frequency axis contains non-finite values')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequency axis contains non-finite values")
    # Codex说明(自动生成)： 检查条件 np.any(frequency_hz <= 0)，根据结果选择后续执行路径。
    if np.any(frequency_hz <= 0):
        # Codex说明(自动生成)： 抛出 ValueError('All frequencies must be positive')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("All frequencies must be positive")
    # Codex说明(自动生成)： 检查条件 np.any(np.diff(frequency_hz) <= 0)，根据结果选择后续执行路径。
    if np.any(np.diff(frequency_hz) <= 0):
        # Codex说明(自动生成)： 抛出 ValueError('Frequencies must be strictly increasing')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequencies must be strictly increasing")


# Codex说明(自动生成)： 定义函数 _validate_target_range，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_target_range(
    frequency_hz: np.ndarray,
    target_frequencies_hz: np.ndarray,
) -> None:
    # Codex说明(自动生成)： 检查条件 target_frequencies_hz.size == 0，根据结果选择后续执行路径。
    if target_frequencies_hz.size == 0:
        # Codex说明(自动生成)： 抛出 ValueError('At least one target frequency is required')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("At least one target frequency is required")
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(target_frequencies_hz))，根据结果选择后续执行路径。
    if np.any(~np.isfinite(target_frequencies_hz)):
        # Codex说明(自动生成)： 抛出 ValueError('Target frequencies must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Target frequencies must be finite")

    # Codex说明(自动生成)： 计算并保存 start，供后续语句继续读取或更新。
    start = float(frequency_hz[0])
    # Codex说明(自动生成)： 计算并保存 stop，供后续语句继续读取或更新。
    stop = float(frequency_hz[-1])
    # Codex说明(自动生成)： 检查条件 np.any(target_frequencies_hz < start) or np.any(target_...，根据结果选择后续执行路径。
    if np.any(target_frequencies_hz < start) or np.any(target_frequencies_hz > stop):
        # Codex说明(自动生成)： 抛出 ValueError('Target frequencies must be inside the impor...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Target frequencies must be inside the imported file frequency range")


# Codex说明(自动生成)： 定义函数 _validate_control_spacing，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_control_spacing(
    frequency_hz: np.ndarray,
    target_frequencies_hz: np.ndarray,
    *,
    smooth_domain: str,
) -> None:
    # Codex说明(自动生成)： 计算并保存 x，供后续语句继续读取或更新。
    x = _frequency_domain(np.asarray(frequency_hz, dtype=float), smooth_domain)
    # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
    controls = list(_frequency_domain(np.asarray(target_frequencies_hz, dtype=float), smooth_domain))
    # Codex说明(自动生成)： 检查条件 not any((control == x[0] for control in controls))，根据结果选择后续执行路径。
    if not any(control == x[0] for control in controls):
        # Codex说明(自动生成)： 调用 controls.append 更新列表或集合，把当前步骤产生的数据加入结果。
        controls.append(float(x[0]))
    # Codex说明(自动生成)： 检查条件 not any((control == x[-1] for control in controls))，根据结果选择后续执行路径。
    if not any(control == x[-1] for control in controls):
        # Codex说明(自动生成)： 调用 controls.append 更新列表或集合，把当前步骤产生的数据加入结果。
        controls.append(float(x[-1]))
    # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
    controls = sorted(controls)
    # Codex说明(自动生成)： 检查条件 len(controls) < 2，根据结果选择后续执行路径。
    if len(controls) < 2:
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return

    # Codex说明(自动生成)： 计算并保存 source_steps，供后续语句继续读取或更新。
    source_steps = np.diff(x)
    # Codex说明(自动生成)： 计算并保存 positive_steps，供后续语句继续读取或更新。
    positive_steps = source_steps[source_steps > 0]
    # Codex说明(自动生成)： 检查条件 positive_steps.size == 0，根据结果选择后续执行路径。
    if positive_steps.size == 0:
        # Codex说明(自动生成)： 抛出 ValueError('Imported frequency grid must be strictly in...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Imported frequency grid must be strictly increasing")
    # Codex说明(自动生成)： 计算并保存 min_allowed，供后续语句继续读取或更新。
    min_allowed = float(np.min(positive_steps)) * 1e-3
    # Codex说明(自动生成)： 计算并保存 close_steps，供后续语句继续读取或更新。
    close_steps = np.diff(controls)
    # Codex说明(自动生成)： 检查条件 np.any(close_steps < min_allowed)，根据结果选择后续执行路径。
    if np.any(close_steps < min_allowed):
        # Codex说明(自动生成)： 抛出 ValueError('Target frequencies are too close to each ot...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            "Target frequencies are too close to each other or to a sweep edge "
            "for a smooth correction"
        )


# Codex说明(自动生成)： 定义函数 _validate_loss_array，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_loss_array(values: np.ndarray, label: str) -> None:
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(values))，根据结果选择后续执行路径。
    if np.any(~np.isfinite(values)):
        # Codex说明(自动生成)： 抛出 ValueError(f'{label} contains non-finite values')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"{label} contains non-finite values")
    # Codex说明(自动生成)： 检查条件 np.any(values < 0)，根据结果选择后续执行路径。
    if np.any(values < 0):
        # Codex说明(自动生成)： 抛出 ValueError(f'{label} must be non-negative')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"{label} must be non-negative")


# Codex说明(自动生成)： 定义函数 _validate_loss_value，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_loss_value(value: float, label: str) -> None:
    # Codex说明(自动生成)： 检查条件 not np.isfinite(value)，根据结果选择后续执行路径。
    if not np.isfinite(value):
        # Codex说明(自动生成)： 抛出 ValueError(f'{label} must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"{label} must be finite")
    # Codex说明(自动生成)： 检查条件 value < 0，根据结果选择后续执行路径。
    if value < 0:
        # Codex说明(自动生成)： 抛出 ValueError(f'{label} must be non-negative')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"{label} must be non-negative")


# Codex说明(自动生成)： 定义函数 _dedupe_pairs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _dedupe_pairs(pairs: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    # Codex说明(自动生成)： 声明并保存 seen，同时保留类型信息方便维护和静态检查。
    seen: set[tuple[int, int]] = set()
    # Codex说明(自动生成)： 声明并保存 output，同时保留类型信息方便维护和静态检查。
    output: list[tuple[int, int]] = []
    # Codex说明(自动生成)： 遍历 pairs 中的 pair，逐项执行循环体逻辑。
    for pair in pairs:
        # Codex说明(自动生成)： 检查条件 pair in seen，根据结果选择后续执行路径。
        if pair in seen:
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        # Codex说明(自动生成)： 调用 seen.add，执行当前流程需要的具体操作或副作用。
        seen.add(pair)
        # Codex说明(自动生成)： 调用 output.append 更新列表或集合，把当前步骤产生的数据加入结果。
        output.append(pair)
    # Codex说明(自动生成)： 返回 output，让调用方取得本函数的处理结果。
    return output
