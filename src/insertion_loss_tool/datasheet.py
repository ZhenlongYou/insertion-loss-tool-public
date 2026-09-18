"""Frequency-safe composition primitives for datasheet-derived curves.

Each curve keeps its native frequency samples.  Composition creates one shared
Touchstone axis without pretending that interpolation adds measurement detail.
The module is independent from OCR so recognition can be cached and replaced
without changing the numerical contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Sequence

import numpy as np
from numpy.typing import NDArray


GridPolicy = Literal["intersection_native", "manual", "union"]
InterpolationDomain = Literal["linear", "log"]
_SINGLE_ENDED_RE = re.compile(r"^S([1-9])([1-9])$")
_MIXED_MODE_RE = re.compile(r"^S([DC])([DC])([1-9])([1-9])$")


@dataclass(frozen=True)
class CurveResource:
    """One recognized curve with its own calibrated frequency axis."""

    curve_id: str
    parameter: str
    frequency_hz: NDArray[np.float64]
    magnitude_db: NDArray[np.float64]
    phase_deg: NDArray[np.float64] | None = None
    confidence: float | None = None
    reference_impedance_ohm: float | None = None

    def __post_init__(self) -> None:
        frequency = np.asarray(self.frequency_hz, dtype=np.float64)
        magnitude = np.asarray(self.magnitude_db, dtype=np.float64)
        if frequency.ndim != 1 or magnitude.ndim != 1 or frequency.size != magnitude.size:
            raise ValueError("频率与幅度必须是一维等长数组。")
        if frequency.size < 2 or not np.all(np.isfinite(frequency)) or np.any(frequency < 0):
            raise ValueError("曲线至少需要两个有限的非负频率点。")
        if np.any(np.diff(frequency) <= 0):
            raise ValueError("曲线频率必须严格递增且不能重复。")
        if not np.all(np.isfinite(magnitude)):
            raise ValueError("曲线幅度必须是有限值。")
        phase = None if self.phase_deg is None else np.asarray(self.phase_deg, dtype=np.float64)
        if phase is not None and (phase.shape != frequency.shape or not np.all(np.isfinite(phase))):
            raise ValueError("相位必须与频率等长且为有限值。")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("识别置信度必须在 0 到 1 之间。")
        if self.reference_impedance_ohm is not None and (
            not np.isfinite(self.reference_impedance_ohm)
            or self.reference_impedance_ohm <= 0
        ):
            raise ValueError("参考阻抗必须是有限正数。")
        object.__setattr__(self, "frequency_hz", frequency)
        object.__setattr__(self, "magnitude_db", magnitude)
        object.__setattr__(self, "phase_deg", phase)


@dataclass(frozen=True)
class FrequencyGridResult:
    """Shared output frequency axis and its coverage semantics."""

    frequency_hz: NDArray[np.float64]
    start_hz: float
    stop_hz: float
    step_hz: float
    points: int
    uses_extrapolation: bool
    policy: GridPolicy


@dataclass(frozen=True)
class ConversionReadiness:
    """Evidence required before an invertible mixed-mode conversion is enabled."""

    ready: bool
    missing_parameters: tuple[str, ...]
    missing_phase: tuple[str, ...]
    duplicate_parameters: tuple[str, ...]
    frequency_mismatch: bool
    reference_impedance_missing: bool
    reference_impedance_mismatch: bool
    port_pairs_invalid: bool


def _nominal_curve_step_hz(curves: Sequence[CurveResource]) -> float:
    """Return the coarsest median native spacing without claiming new detail."""

    return max(
        float(np.median(np.diff(curve.frequency_hz)))
        for curve in curves
    )


def _uniform_frequency_grid(
    start_hz: float,
    stop_hz: float,
    requested_step_hz: float,
    *,
    max_points: int,
    require_exact_step: bool,
) -> tuple[NDArray[np.float64], float]:
    """Build an inclusive, exactly uniform output grid.

    Automatic grids retain both coverage endpoints and may become slightly
    coarser than the requested/native resolution. Manual grids fail when the
    requested step cannot divide the requested span; appending an irregular
    final interval is never allowed.
    """

    span_hz = stop_hz - start_hz
    if span_hz <= 0 or requested_step_hz <= 0:
        raise ValueError("公共频率范围或步进无效。")
    ratio = span_hz / requested_step_hz
    if require_exact_step:
        intervals = int(round(ratio))
        if intervals < 1 or not np.isclose(ratio, intervals, rtol=1e-10, atol=1e-10):
            raise ValueError("手动步进不能整除起始与终止频率范围。")
    else:
        intervals = max(1, int(np.floor(ratio * (1.0 + 1e-12))))
    point_count = intervals + 1
    if point_count > max_points:
        raise ValueError(f"公共频点超过上限 {max_points}。")
    frequency_hz = np.linspace(start_hz, stop_hz, point_count, dtype=np.float64)
    return frequency_hz, span_hz / intervals


def mixed_mode_parameter_names(physical_port_count: int) -> tuple[str, ...]:
    """Return SDD/SDC/SCD/SCC names for paired physical ports."""

    if physical_port_count < 2 or physical_port_count % 2:
        raise ValueError("混合模需要偶数个物理端口。")
    logical_ports = physical_port_count // 2
    return tuple(
        f"S{output_mode}{input_mode}{output_port}{input_port}"
        for output_mode in "DC"
        for input_mode in "DC"
        for output_port in range(1, logical_ports + 1)
        for input_port in range(1, logical_ports + 1)
    )


def transpose_parameter(parameter: str) -> str:
    """Return the reciprocity counterpart in single-ended or mixed-mode form."""

    name = str(parameter).upper()
    single = _SINGLE_ENDED_RE.fullmatch(name)
    if single:
        return f"S{single.group(2)}{single.group(1)}"
    mixed = _MIXED_MODE_RE.fullmatch(name)
    if mixed:
        output_mode, input_mode, output_port, input_port = mixed.groups()
        return f"S{input_mode}{output_mode}{input_port}{output_port}"
    raise ValueError("S 参数名称无效。")


def normalize_parameter_name(parameter: object) -> str:
    """Validate and normalize one single-ended or mixed-mode parameter name."""

    name = str(parameter).strip().upper()
    if _SINGLE_ENDED_RE.fullmatch(name) or _MIXED_MODE_RE.fullmatch(name):
        return name
    raise ValueError("S 参数名称无效。")


def _normalize_port_pairs(
    physical_port_count: int,
    port_pairs: Sequence[tuple[int, int]] | None,
) -> tuple[tuple[int, int], ...]:
    """Validate a complete 1-based physical-port pairing."""

    if physical_port_count < 2 or physical_port_count % 2:
        raise ValueError("混合模矩阵必须具有偶数个物理端口。")
    pairs = (
        tuple((port, port + 1) for port in range(1, physical_port_count + 1, 2))
        if port_pairs is None
        else tuple(tuple(pair) for pair in port_pairs)
    )
    if len(pairs) != physical_port_count // 2 or any(len(pair) != 2 for pair in pairs):
        raise ValueError("端口配对必须由二元组组成并覆盖全部物理端口。")
    if any(
        isinstance(port, bool) or not isinstance(port, (int, np.integer))
        for pair in pairs
        for port in pair
    ):
        raise ValueError("端口编号必须是非布尔整数。")
    pairs = tuple(tuple(int(port) for port in pair) for pair in pairs)
    flattened = [port for pair in pairs for port in pair]
    if len(set(flattened)) != len(flattened) or set(flattened) != set(
        range(1, physical_port_count + 1)
    ):
        raise ValueError("端口配对必须无重复地覆盖全部物理端口。")
    return pairs


def _mixed_mode_transform(
    physical_port_count: int,
    port_pairs: Sequence[tuple[int, int]] | None = None,
) -> NDArray[np.float64]:
    """Build the orthonormal [D1..Dn,C1..Cn] transform for explicit pairs."""

    pairs = _normalize_port_pairs(physical_port_count, port_pairs)
    pair_count = physical_port_count // 2
    transform = np.zeros((physical_port_count, physical_port_count), dtype=np.float64)
    scale = 1.0 / np.sqrt(2.0)
    for pair, (positive_port, negative_port) in enumerate(pairs):
        positive, negative = positive_port - 1, negative_port - 1
        transform[pair, positive] = scale
        transform[pair, negative] = -scale
        transform[pair_count + pair, positive] = scale
        transform[pair_count + pair, negative] = scale
    return transform


def single_ended_to_mixed_mode(
    s_single_ended: NDArray[np.complex128],
    *,
    port_pairs: Sequence[tuple[int, int]] | None = None,
) -> NDArray[np.complex128]:
    """Convert a complete complex S matrix using equal normalized pair references.

    Physical ports must be ordered as adjacent positive/negative pairs.  The
    returned modal order is D1..Dn,C1..Cn.  Callers must separately establish
    compatible power-wave normalization and reference impedances.
    """

    values = np.asarray(s_single_ended, dtype=np.complex128)
    if values.ndim < 2 or values.shape[-1] != values.shape[-2]:
        raise ValueError("单端 S 参数必须是方阵。")
    transform = _mixed_mode_transform(values.shape[-1], port_pairs)
    return transform @ values @ transform.T


def mixed_mode_to_single_ended(
    s_mixed_mode: NDArray[np.complex128],
    *,
    port_pairs: Sequence[tuple[int, int]] | None = None,
) -> NDArray[np.complex128]:
    """Invert a complete complex mixed-mode matrix under the same convention."""

    values = np.asarray(s_mixed_mode, dtype=np.complex128)
    if values.ndim < 2 or values.shape[-1] != values.shape[-2]:
        raise ValueError("混合模 S 参数必须是方阵。")
    transform = _mixed_mode_transform(values.shape[-1], port_pairs)
    return transform.T @ values @ transform


def assess_mixed_mode_conversion(
    curves: Sequence[CurveResource],
    *,
    physical_port_count: int,
    port_pairs: Sequence[tuple[int, int]] | None,
) -> ConversionReadiness:
    """Check whether complete complex mixed-mode data can be inverted safely."""

    required = mixed_mode_parameter_names(physical_port_count)
    grouped: dict[str, list[CurveResource]] = {}
    for curve in curves:
        try:
            parameter = normalize_parameter_name(curve.parameter)
        except ValueError:
            continue
        if parameter in required:
            grouped.setdefault(parameter, []).append(curve)
    missing_parameters = tuple(parameter for parameter in required if parameter not in grouped)
    duplicates = tuple(parameter for parameter in required if len(grouped.get(parameter, ())) > 1)
    unique_curves = [grouped[parameter][0] for parameter in required if parameter in grouped]
    missing_phase = tuple(
        parameter
        for parameter in required
        if parameter in grouped and grouped[parameter][0].phase_deg is None
    )
    frequency_mismatch = False
    if unique_curves:
        reference_frequency = unique_curves[0].frequency_hz
        frequency_mismatch = any(
            curve.frequency_hz.shape != reference_frequency.shape
            or not np.array_equal(curve.frequency_hz, reference_frequency)
            for curve in unique_curves[1:]
        )
    impedances = [curve.reference_impedance_ohm for curve in unique_curves]
    impedance_missing = len(unique_curves) != len(required) or any(
        impedance is None for impedance in impedances
    )
    known_impedances = [float(value) for value in impedances if value is not None]
    impedance_mismatch = bool(
        known_impedances
        and not np.allclose(known_impedances, known_impedances[0], rtol=1e-12, atol=0.0)
    )
    try:
        _normalize_port_pairs(physical_port_count, port_pairs)
        pairs_invalid = port_pairs is None
    except (TypeError, ValueError):
        pairs_invalid = True
    ready = not any(
        (
            missing_parameters,
            missing_phase,
            duplicates,
            frequency_mismatch,
            impedance_missing,
            impedance_mismatch,
            pairs_invalid,
        )
    )
    return ConversionReadiness(
        ready=ready,
        missing_parameters=missing_parameters,
        missing_phase=missing_phase,
        duplicate_parameters=duplicates,
        frequency_mismatch=frequency_mismatch,
        reference_impedance_missing=impedance_missing,
        reference_impedance_mismatch=impedance_mismatch,
        port_pairs_invalid=pairs_invalid,
    )


def compose_frequency_grid(
    curves: Sequence[CurveResource],
    *,
    policy: GridPolicy = "intersection_native",
    max_points: int = 200_000,
    manual_start_hz: float | None = None,
    manual_stop_hz: float | None = None,
    manual_step_hz: float | None = None,
    preferred_step_hz: float | None = None,
    allow_extrapolation: bool = False,
) -> FrequencyGridResult:
    """Build one inclusive uniform output grid without silent extrapolation."""

    if not curves and policy != "manual":
        raise ValueError("没有图片曲线时必须显式设置手动频率网格。")
    common_start_hz = (
        max(float(curve.frequency_hz[0]) for curve in curves) if curves else None
    )
    common_stop_hz = (
        min(float(curve.frequency_hz[-1]) for curve in curves) if curves else None
    )
    union_start_hz = (
        min(float(curve.frequency_hz[0]) for curve in curves) if curves else None
    )
    union_stop_hz = (
        max(float(curve.frequency_hz[-1]) for curve in curves) if curves else None
    )
    if curves:
        native_step_hz = _nominal_curve_step_hz(curves)
        automatic_step_hz = (
            native_step_hz
            if preferred_step_hz is None
            else max(native_step_hz, float(preferred_step_hz))
        )
        if not np.isfinite(automatic_step_hz) or automatic_step_hz <= 0:
            raise ValueError("公共频率步进无效。")
    uses_extrapolation = False
    if policy == "intersection_native":
        assert common_start_hz is not None and common_stop_hz is not None
        start_hz, stop_hz = common_start_hz, common_stop_hz
        if stop_hz <= start_hz:
            raise ValueError("所选曲线没有共同频率范围。")
        frequency_hz, step_hz = _uniform_frequency_grid(
            start_hz,
            stop_hz,
            automatic_step_hz,
            max_points=max_points,
            require_exact_step=False,
        )
    elif policy == "manual":
        values = (manual_start_hz, manual_stop_hz, manual_step_hz)
        if any(value is None or not np.isfinite(value) for value in values):
            raise ValueError("手动频率范围需要有效的起始、终止和步进。")
        start_hz = float(manual_start_hz)
        stop_hz = float(manual_stop_hz)
        step_hz = float(manual_step_hz)
        if start_hz <= 0 or stop_hz <= start_hz or step_hz <= 0:
            raise ValueError("手动频率范围无效。")
        uses_extrapolation = bool(
            curves
            and (
                start_hz < float(common_start_hz)
                or stop_hz > float(common_stop_hz)
            )
        )
        if uses_extrapolation and not allow_extrapolation:
            raise ValueError("手动频率范围超出部分曲线覆盖范围。")
        frequency_hz, step_hz = _uniform_frequency_grid(
            start_hz,
            stop_hz,
            step_hz,
            max_points=max_points,
            require_exact_step=True,
        )
    elif policy == "union":
        assert union_start_hz is not None and union_stop_hz is not None
        start_hz, stop_hz = union_start_hz, union_stop_hz
        uses_extrapolation = any(
            curve.frequency_hz[0] > start_hz or curve.frequency_hz[-1] < stop_hz
            for curve in curves
        )
        if uses_extrapolation and not allow_extrapolation:
            raise ValueError("全部范围存在缺口，必须显式允许并选择填充策略。")
        frequency_hz, step_hz = _uniform_frequency_grid(
            start_hz,
            stop_hz,
            automatic_step_hz,
            max_points=max_points,
            require_exact_step=False,
        )
    else:
        raise ValueError("频率策略无效。")
    if frequency_hz.size < 2:
        raise ValueError("共同频率范围内至少需要两个频点。")
    if frequency_hz.size > max_points:
        raise ValueError(f"公共频点超过上限 {max_points}。")
    return FrequencyGridResult(
        frequency_hz=frequency_hz,
        start_hz=start_hz,
        stop_hz=stop_hz,
        step_hz=step_hz,
        points=int(frequency_hz.size),
        uses_extrapolation=uses_extrapolation,
        policy=policy,
    )


def resample_curve(
    curve: CurveResource,
    target_frequency_hz: NDArray[np.float64],
    *,
    domain: InterpolationDomain = "linear",
) -> CurveResource:
    """Interpolate dB and unwrapped phase without silently extrapolating."""

    target = np.asarray(target_frequency_hz, dtype=np.float64)
    if target.ndim != 1 or target.size < 2 or np.any(np.diff(target) <= 0):
        raise ValueError("目标频率必须是一维严格递增数组。")
    if target[0] < curve.frequency_hz[0] or target[-1] > curve.frequency_hz[-1]:
        raise ValueError("目标频率超出曲线覆盖范围。")
    if domain == "linear":
        source_x = curve.frequency_hz
        target_x = target
    elif domain == "log":
        if curve.frequency_hz[0] <= 0 or target[0] <= 0:
            raise ValueError("对数插值要求所有频率严格大于 0。")
        source_x = np.log(curve.frequency_hz)
        target_x = np.log(target)
    else:
        raise ValueError("插值域必须是 linear 或 log。")
    magnitude_db = np.interp(target_x, source_x, curve.magnitude_db)
    phase_deg = None
    if curve.phase_deg is not None:
        phase_rad = np.unwrap(np.deg2rad(curve.phase_deg))
        phase_deg = np.rad2deg(np.interp(target_x, source_x, phase_rad))
    return CurveResource(
        curve_id=curve.curve_id,
        parameter=curve.parameter,
        frequency_hz=target,
        magnitude_db=magnitude_db,
        phase_deg=phase_deg,
        confidence=curve.confidence,
        reference_impedance_ohm=curve.reference_impedance_ohm,
    )
