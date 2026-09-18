"""Conservative Touchstone reader/writer for full S-parameter matrices."""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 dataclasses 导入 dataclass，声明轻量数据结构并减少样板初始化代码。
from dataclasses import dataclass
# ``Integral`` rejects floating-point port labels while ``Real`` accepts
# Python and NumPy scalar impedances through one authority check.
from numbers import Integral, Real
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 re，执行正则匹配和文本规则识别。
import re
# Codex说明(自动生成)： 从 typing 导入 Sequence，提供类型标注辅助名称，方便维护和静态检查。
from typing import Sequence

# Codex说明(自动生成)： 导入 np，执行数组、向量化和数值仿真计算。
import numpy as np


# Codex说明(自动生成)： 计算并保存 FREQUENCY_MULTIPLIERS，供后续语句继续读取或更新。
FREQUENCY_MULTIPLIERS = {
    "HZ": 1.0,
    "KHZ": 1e3,
    "MHZ": 1e6,
    "GHZ": 1e9,
}


def _is_touchstone_2(version: str) -> bool:
    """Return whether keyword-oriented Touchstone 2.x record rules apply."""

    return version in {"2.0", "2.1"}


# Codex说明(自动生成)： 定义 TouchstoneData 类，把相关数据结构、校验规则或操作方法组织在一起。
@dataclass
class TouchstoneData:
    """S-parameter data in SI frequency units.

    The matrix convention is s[f_index, output_port, input_port], so S21 is
    stored at s[:, 1, 0].
    """

    # Codex说明(自动生成)： 声明并保存 frequency_hz，同时保留类型信息方便维护和静态检查。
    frequency_hz: np.ndarray
    # Codex说明(自动生成)： 声明并保存 s，同时保留类型信息方便维护和静态检查。
    s: np.ndarray
    # Codex说明(自动生成)： 声明并保存 z0，同时保留类型信息方便维护和静态检查。
    z0: float = 50.0
    # Codex说明(自动生成)： 声明并保存 source_path，同时保留类型信息方便维护和静态检查。
    source_path: str | None = None

    # Codex说明(自动生成)： 定义函数 n_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @property
    def n_ports(self) -> int:
        # Codex说明(自动生成)： 返回 int(self.s.shape[1])，让调用方取得本函数的处理结果。
        return int(self.s.shape[1])


@dataclass(frozen=True, eq=False)
class NetworkTransfer:
    """One immutable output/input transfer selected from a channel network.

    Arrays are normalized to their public dtypes and rebuilt over private
    ``bytes`` buffers.  This makes the transfer independent from caller-owned
    arrays and prevents callers from re-enabling NumPy's write flag.
    """

    __slots__ = ("frequency_hz", "response", "path", "z0_ohm")

    frequency_hz: np.ndarray
    response: np.ndarray
    path: str
    z0_ohm: float

    def __post_init__(self) -> None:
        if np.iscomplexobj(self.frequency_hz):
            raise ValueError("frequency_hz must contain real values")
        try:
            frequency = np.asarray(self.frequency_hz, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("frequency_hz must contain float64-compatible values") from exc
        try:
            response = np.asarray(self.response, dtype=np.complex128)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("response must contain complex128-compatible values") from exc
        if frequency.ndim != 1:
            raise ValueError("frequency_hz must be a one-dimensional array")
        if response.ndim != 1:
            raise ValueError("response must be a one-dimensional array")
        _validate_frequency_axis(frequency)
        if response.size != frequency.size:
            raise ValueError("frequency_hz and response must have the same nonzero length")
        if not np.all(np.isfinite(response.real)) or not np.all(
            np.isfinite(response.imag)
        ):
            raise ValueError("response must contain only finite values")
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("path must be a nonempty string")
        if isinstance(self.z0_ohm, bool) or not isinstance(self.z0_ohm, Real):
            raise ValueError("z0_ohm must be a real number, not bool")
        try:
            z0_ohm = float(self.z0_ohm)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("z0_ohm must be float-compatible") from exc
        if not np.isfinite(z0_ohm) or z0_ohm <= 0.0:
            raise ValueError("z0_ohm must be positive and finite")

        object.__setattr__(self, "frequency_hz", _immutable_array(frequency))
        object.__setattr__(self, "response", _immutable_array(response))
        object.__setattr__(self, "path", self.path.strip())
        object.__setattr__(self, "z0_ohm", z0_ohm)


def select_transfer(
    data: TouchstoneData,
    *,
    output_port: int,
    input_port: int,
) -> NetworkTransfer:
    """Select ``S(output_port)(input_port)`` using one-indexed port labels."""

    if not isinstance(data, TouchstoneData):
        raise TypeError("data must be a TouchstoneData instance")
    _validate_touchstone_data(data)
    for name, port in (("output_port", output_port), ("input_port", input_port)):
        if isinstance(port, bool) or not isinstance(port, Integral):
            raise TypeError(f"{name} must be an integer, not bool")
    output_port = int(output_port)
    input_port = int(input_port)
    s_matrix = np.asarray(data.s)
    n_ports = int(s_matrix.shape[1])
    if not 1 <= output_port <= n_ports or not 1 <= input_port <= n_ports:
        raise ValueError("selected transfer path is outside the network port range")
    return NetworkTransfer(
        frequency_hz=data.frequency_hz,
        response=s_matrix[:, output_port - 1, input_port - 1],
        path=f"S{output_port}{input_port}",
        z0_ohm=data.z0,
    )


def _immutable_array(values: np.ndarray) -> np.ndarray:
    """Return an independently owned NumPy array backed by immutable bytes."""

    return np.frombuffer(values.tobytes(order="C"), dtype=values.dtype)


# Codex说明(自动生成)： 定义函数 read_touchstone，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def read_touchstone(
    path: str | Path,
    *,
    default_frequency_unit: str = "GHZ",
) -> TouchstoneData:
    """Read a full-matrix Touchstone S-parameter file.

    Supported option formats are RI, MA, and DB. The reader understands the
    Touchstone 2.x two-port data order keyword, and rejects unsupported 2.x
    constructs that would otherwise be unsafe to ignore.  Files without a
    ``#`` option line use ``default_frequency_unit``; the public default follows
    the Touchstone standard and remains GHz.
    """

    if not isinstance(default_frequency_unit, str):
        raise TypeError("default_frequency_unit must be a string")
    unit = default_frequency_unit.strip().upper()
    if unit not in FREQUENCY_MULTIPLIERS:
        supported = ", ".join(FREQUENCY_MULTIPLIERS)
        raise ValueError(
            f"default_frequency_unit must be one of {supported}, got {default_frequency_unit!r}"
        )
    # Codex说明(自动生成)： 计算并保存 file_path，供后续语句继续读取或更新。
    file_path = Path(path)
    # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
    n_ports = _ports_from_suffix(file_path)
    values_per_point = 1 + 2 * n_ports * n_ports
    version = "1.0"
    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    # Codex说明(自动生成)： 计算并保存 parameter，供后续语句继续读取或更新。
    parameter = "S"
    # Codex说明(自动生成)： 计算并保存 data_format，供后续语句继续读取或更新。
    data_format = "MA"
    # Codex说明(自动生成)： 计算并保存 z0，供后续语句继续读取或更新。
    z0 = 50.0
    # Each inner list is one complete frequency record. Keeping physical-line
    # boundaries prevents a short row from borrowing tokens from the next row.
    records: list[list[float]] = []
    record_start_lines: list[int] = []
    pending_record: list[float] | None = None
    pending_record_line: int | None = None
    pending_v1_continuations = 0
    # Codex说明(自动生成)： 计算并保存 two_port_data_order，供后续语句继续读取或更新。
    two_port_data_order = "21_12"
    # Codex说明(自动生成)： 计算并保存 expected_two_port_order，供后续语句继续读取或更新。
    expected_two_port_order = False
    # Codex说明(自动生成)： 声明并保存 number_of_frequencies，同时保留类型信息方便维护和静态检查。
    number_of_frequencies: int | None = None
    number_of_frequencies_line: int | None = None
    # Codex说明(自动生成)： 计算并保存 inside_information，供后续语句继续读取或更新。
    inside_information = False
    meaningful_content_seen = False
    version_line: int | None = None
    option_line_seen = False
    number_of_ports_seen = False
    two_port_data_order_seen = False
    network_data_seen = False
    end_seen = False

    # Codex说明(自动生成)： 遍历 file_path.read_text(encoding='utf-8', errors='replace')... 中的 raw_line，逐项执行循环体逻辑。
    for line_number, raw_line in enumerate(
        file_path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        # Codex说明(自动生成)： 计算并保存 line，供后续语句继续读取或更新。
        line = raw_line.split("!", 1)[0].strip()
        # Codex说明(自动生成)： 检查条件 not line，根据结果选择后续执行路径。
        if not line:
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        if end_seen:
            raise ValueError(
                f"{file_path}:{line_number}: content is not allowed after [End]"
            )
        if pending_record is not None and (
            line.startswith("[") or line.startswith("#")
        ):
            if _is_touchstone_2(version):
                raise ValueError(
                    f"{file_path}:{line_number}: incomplete Touchstone 2.x record "
                    f"started at line {pending_record_line}; expected "
                    f"{values_per_point} numeric values, got {len(pending_record)}"
                )
            raise ValueError(
                f"{file_path}:{line_number}: incomplete S4P record started at "
                f"line {pending_record_line}; expected 8 numeric continuation values"
            )
        # Codex说明(自动生成)： 检查条件 line.startswith('[')，根据结果选择后续执行路径。
        if line.startswith("["):
            # Codex说明(自动生成)： 计算并保存 (keyword, rest)，供后续语句继续读取或更新。
            keyword, rest = _parse_keyword_line(line)
            if keyword == "version":
                if meaningful_content_seen or version_line is not None:
                    raise ValueError(
                        f"{file_path}:{line_number}: [Version] must be the first "
                        "non-comment line"
                    )
                version = rest.split()[0] if rest else ""
                if version not in {"1.0", "2.0", "2.1"}:
                    raise ValueError(
                        f"{file_path}:{line_number}: unsupported Touchstone "
                        f"[Version] value {rest!r}"
                    )
                version_line = line_number
                meaningful_content_seen = True
                continue
            if version_line is None:
                raise ValueError(
                    f"{file_path}:{line_number}: [Version] must be the first "
                    "non-comment line before Touchstone keywords"
                )
            if _is_touchstone_2(version) and not option_line_seen:
                raise ValueError(
                    f"{file_path}:{line_number}: Touchstone 2.x option line must "
                    "follow [Version] before other keywords"
                )
            # Codex说明(自动生成)： 检查条件 keyword == 'end' or keyword == 'end information'，根据结果选择后续执行路径。
            if keyword == "end" or keyword == "end information":
                # Codex说明(自动生成)： 计算并保存 inside_information，供后续语句继续读取或更新。
                inside_information = False
                # Codex说明(自动生成)： 检查条件 keyword == 'end'，根据结果选择后续执行路径。
                if keyword == "end":
                    if _is_touchstone_2(version) and not network_data_seen:
                        raise ValueError(
                            f"{file_path}:{line_number}: [Network Data] is required "
                            "before [End]"
                        )
                    end_seen = True
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 inside_information，根据结果选择后续执行路径。
            if inside_information:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'begin information'，根据结果选择后续执行路径。
            if keyword == "begin information":
                # Codex说明(自动生成)： 计算并保存 inside_information，供后续语句继续读取或更新。
                inside_information = True
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'two-port data order'，根据结果选择后续执行路径。
            if keyword == "two-port data order":
                # Codex说明(自动生成)： 检查条件 n_ports != 2，根据结果选择后续执行路径。
                if n_ports != 2:
                    # Codex说明(自动生成)： 抛出 ValueError('[Two-Port Data Order] is only valid for S2P...，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("[Two-Port Data Order] is only valid for S2P files")
                if _is_touchstone_2(version) and not number_of_ports_seen:
                    raise ValueError(
                        "[Number of Ports] must precede [Two-Port Data Order]"
                    )
                if two_port_data_order_seen:
                    raise ValueError("[Two-Port Data Order] may appear only once")
                two_port_data_order_seen = True
                # Codex说明(自动生成)： 检查条件 rest，根据结果选择后续执行路径。
                if rest:
                    # Codex说明(自动生成)： 计算并保存 two_port_data_order，供后续语句继续读取或更新。
                    two_port_data_order = _parse_two_port_data_order(rest)
                # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
                else:
                    # Codex说明(自动生成)： 计算并保存 expected_two_port_order，供后续语句继续读取或更新。
                    expected_two_port_order = True
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'number of ports'，根据结果选择后续执行路径。
            if keyword == "number of ports":
                if number_of_ports_seen:
                    raise ValueError("[Number of Ports] may appear only once")
                # Codex说明(自动生成)： 计算并保存 declared_ports，供后续语句继续读取或更新。
                declared_ports = _parse_positive_int_keyword(keyword, rest)
                # Codex说明(自动生成)： 检查条件 declared_ports != n_ports，根据结果选择后续执行路径。
                if declared_ports != n_ports:
                    # Codex说明(自动生成)： 抛出 ValueError(f'[Number of Ports] declares {declared_ports...，明确提示输入、状态或处理流程无法继续。
                    raise ValueError(
                        f"[Number of Ports] declares {declared_ports}, but extension is S{n_ports}P"
                    )
                number_of_ports_seen = True
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'number of frequencies'，根据结果选择后续执行路径。
            if keyword == "number of frequencies":
                # Codex说明(自动生成)： 计算并保存 number_of_frequencies，供后续语句继续读取或更新。
                number_of_frequencies = _parse_positive_int_keyword(keyword, rest)
                number_of_frequencies_line = line_number
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            if keyword == "matrix format":
                matrix_format = rest.split()[0].upper() if rest else ""
                if not _is_touchstone_2(version) or matrix_format != "FULL":
                    raise ValueError(
                        f"{file_path}:{line_number}: only Touchstone 2.x "
                        "[Matrix Format] Full is supported"
                    )
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'network data'，根据结果选择后续执行路径。
            if keyword == "network data":
                if network_data_seen:
                    raise ValueError("[Network Data] may appear only once")
                if _is_touchstone_2(version) and not number_of_ports_seen:
                    raise ValueError("[Number of Ports] must precede [Network Data]")
                if (
                    _is_touchstone_2(version)
                    and n_ports == 2
                    and not two_port_data_order_seen
                ):
                    raise ValueError(
                        "[Two-Port Data Order] is required before [Network Data] "
                        "for Touchstone 2.x S2P"
                    )
                network_data_seen = True
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 检查条件 keyword == 'reference'，根据结果选择后续执行路径。
            if keyword == "reference":
                # Codex说明(自动生成)： 抛出 ValueError('Touchstone 2.0 [Reference] is unsupported b...，明确提示输入、状态或处理流程无法继续。
                raise ValueError(
                    "Touchstone 2.x [Reference] is unsupported because this tool "
                    "preserves only a scalar # ... R impedance"
                )
            # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported Touchstone 2.0 keyword: [{keyw...，明确提示输入、状态或处理流程无法继续。
            raise ValueError(f"Unsupported Touchstone 2.x keyword: [{keyword}]")
        # Codex说明(自动生成)： 检查条件 inside_information，根据结果选择后续执行路径。
        if inside_information:
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        # Codex说明(自动生成)： 检查条件 expected_two_port_order，根据结果选择后续执行路径。
        if expected_two_port_order:
            # Codex说明(自动生成)： 计算并保存 two_port_data_order，供后续语句继续读取或更新。
            two_port_data_order = _parse_two_port_data_order(line)
            # Codex说明(自动生成)： 计算并保存 expected_two_port_order，供后续语句继续读取或更新。
            expected_two_port_order = False
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        # Codex说明(自动生成)： 检查条件 line.startswith('#')，根据结果选择后续执行路径。
        if line.startswith("#"):
            if _is_touchstone_2(version):
                if version_line is None:
                    raise ValueError(
                        f"{file_path}:{line_number}: [Version] must precede the "
                        "Touchstone 2.x option line"
                    )
                if option_line_seen:
                    raise ValueError("Touchstone 2.x option line may appear only once")
                if number_of_ports_seen or network_data_seen:
                    raise ValueError(
                        "Touchstone 2.x option line must precede network keywords"
                    )
                option_line_seen = True
            # Codex说明(自动生成)： 计算并保存 (unit, parameter, data_format, z0)，供后续语句继续读取或更新。
            unit, parameter, data_format, z0 = _parse_option_line(line)
            meaningful_content_seen = True
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue
        meaningful_content_seen = True
        if _is_touchstone_2(version) and not network_data_seen:
            raise ValueError(
                f"{file_path}:{line_number}: [Network Data] is required before "
                "numeric network records"
            )
        try:
            row_values = [_parse_float(token) for token in line.split()]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{file_path}:{line_number}: {exc}") from exc

        if _is_touchstone_2(version):
            if pending_record is None:
                pending_record = []
                pending_record_line = line_number
            pending_record.extend(row_values)
            if len(pending_record) > values_per_point:
                raise ValueError(
                    f"{file_path}:{line_number}: Touchstone 2.x record started at "
                    f"line {pending_record_line} expected {values_per_point} numeric "
                    f"values, got {len(pending_record)}"
                )
            if len(pending_record) == values_per_point:
                records.append(pending_record)
                record_start_lines.append(int(pending_record_line))
                pending_record = None
                pending_record_line = None
            continue

        if n_ports == 2:
            if len(row_values) != 9:
                raise ValueError(
                    f"{file_path}:{line_number}: S2P record expected 9 numeric values, "
                    f"got {len(row_values)}"
                )
            records.append(row_values)
            record_start_lines.append(line_number)
            continue

        if pending_record is None:
            if 3 <= len(row_values) <= 9 and len(row_values) % 2 == 1:
                pending_record = row_values
                pending_record_line = line_number
                pending_v1_continuations = 0
                if len(pending_record) == values_per_point:
                    records.append(pending_record)
                    record_start_lines.append(line_number)
                    pending_record = None
                    pending_record_line = None
                continue
            raise ValueError(
                f"{file_path}:{line_number}: S{n_ports}P record must start with "
                "a frequency and 1 to 4 complex pairs; "
                f"got {len(row_values)} numeric values"
            )

        if len(row_values) < 2 or len(row_values) > 8 or len(row_values) % 2:
            raise ValueError(
                f"{file_path}:{line_number}: S{n_ports}P continuation for record started at "
                f"line {pending_record_line} expected 1 to 4 complex pairs, "
                f"got {len(row_values)} numeric values"
            )
        pending_record.extend(row_values)
        pending_v1_continuations += 1
        if len(pending_record) > values_per_point:
            raise ValueError(
                f"{file_path}:{line_number}: S{n_ports}P record started at line "
                f"{pending_record_line} expected {values_per_point} numeric values, "
                f"got {len(pending_record)}"
            )
        if len(pending_record) == values_per_point:
            records.append(pending_record)
            record_start_lines.append(int(pending_record_line))
            pending_record = None
            pending_record_line = None
            pending_v1_continuations = 0

    # Codex说明(自动生成)： 检查条件 expected_two_port_order，根据结果选择后续执行路径。
    if expected_two_port_order:
        # Codex说明(自动生成)： 抛出 ValueError('[Two-Port Data Order] is missing its order ...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("[Two-Port Data Order] is missing its order value")
    if pending_record is not None:
        if _is_touchstone_2(version):
            raise ValueError(
                f"{file_path}:{pending_record_line}: truncated Touchstone 2.x record "
                f"at end of file; expected {values_per_point} numeric values, "
                f"got {len(pending_record)}"
            )
        raise ValueError(
            f"{file_path}:{pending_record_line}: truncated S{n_ports}P record at end of file; "
            f"got {len(pending_record)} of {values_per_point} numeric values"
        )
    if _is_touchstone_2(version):
        if not option_line_seen:
            raise ValueError("Touchstone 2.x requires an option line after [Version]")
        if not number_of_ports_seen:
            raise ValueError("Touchstone 2.x requires [Number of Ports]")
        if n_ports == 2 and not two_port_data_order_seen:
            raise ValueError("Touchstone 2.x S2P requires [Two-Port Data Order]")
        if not network_data_seen:
            raise ValueError("Touchstone 2.x requires [Network Data]")
        if not end_seen:
            raise ValueError("Touchstone 2.x requires [End]")

    # Codex说明(自动生成)： 检查条件 parameter != 'S'，根据结果选择后续执行路径。
    if parameter != "S":
        # Codex说明(自动生成)： 抛出 ValueError(f'Only S-parameter files are supported, got ...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Only S-parameters are supported, got {parameter!r}")
    # Codex说明(自动生成)： 检查条件 data_format not in {'RI', 'MA', 'DB'}，根据结果选择后续执行路径。
    if data_format not in {"RI", "MA", "DB"}:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported Touchstone data format: {data_...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported Touchstone data format: {data_format!r}")

    groups = (
        np.asarray(records, dtype=float)
        if records
        else np.empty((0, values_per_point), dtype=float)
    )
    # Codex说明(自动生成)： 检查条件 number_of_frequencies is not None and groups.shape[0] !...，根据结果选择后续执行路径。
    if number_of_frequencies is not None and groups.shape[0] != number_of_frequencies:
        # Codex说明(自动生成)： 抛出 ValueError(f'[Number of Frequencies] declares {number_o...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            f"{file_path}:{number_of_frequencies_line}: [Number of Frequencies] "
            f"declares {number_of_frequencies}, "
            f"but parsed {groups.shape[0]} frequency points"
        )
    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    try:
        with np.errstate(over="raise", invalid="raise"):
            frequency_hz = groups[:, 0] * FREQUENCY_MULTIPLIERS[unit]
    except FloatingPointError as exc:
        source_line = record_start_lines[0] if record_start_lines else 1
        raise ValueError(
            f"{file_path}:{source_line}: frequency_hz conversion produced "
            "non-finite values"
        ) from exc
    # Codex说明(自动生成)： 计算并保存 order，供后续语句继续读取或更新。
    order = touchstone_order(n_ports, two_port_data_order=two_port_data_order)
    # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
    s = np.zeros((groups.shape[0], n_ports, n_ports), dtype=complex)

    # Codex说明(自动生成)： 遍历 enumerate(groups) 中的 (point_index, row)，逐项执行循环体逻辑。
    for point_index, row in enumerate(groups):
        # Codex说明(自动生成)： 计算并保存 pair_values，供后续语句继续读取或更新。
        pair_values = row[1:].reshape((-1, 2))
        # Codex说明(自动生成)： 遍历 enumerate(order) 中的 (value_index, (out_port, in_port))，逐项执行循环体逻辑。
        for value_index, (out_port, in_port) in enumerate(order):
            # Codex说明(自动生成)： 计算并保存 (first, second)，供后续语句继续读取或更新。
            first, second = pair_values[value_index]
            # Codex说明(自动生成)： 计算并保存 s[point_index, out_port, in_port]，供后续语句继续读取或更新。
            try:
                with np.errstate(over="raise", invalid="raise"):
                    converted = _pair_to_complex(first, second, data_format)
            except (FloatingPointError, OverflowError) as exc:
                raise ValueError(
                    f"{file_path}:{record_start_lines[point_index]}: S-parameter "
                    f"{data_format} conversion produced a non-finite value for "
                    f"S{out_port + 1}{in_port + 1}"
                ) from exc
            if not np.isfinite(converted.real) or not np.isfinite(converted.imag):
                raise ValueError(
                    f"{file_path}:{record_start_lines[point_index]}: S-parameter "
                    f"{data_format} conversion produced a non-finite value for "
                    f"S{out_port + 1}{in_port + 1}"
                )
            s[point_index, out_port, in_port] = converted

    data = TouchstoneData(
        frequency_hz=frequency_hz,
        s=s,
        z0=z0,
        source_path=str(file_path),
    )
    # Validate the complete network before returning it. This catches any
    # non-finite conversion result as well as malformed frequency ordering.
    try:
        _validate_touchstone_data(data)
    except ValueError as exc:
        source_line = record_start_lines[0] if record_start_lines else 1
        raise ValueError(f"{file_path}:{source_line}: {exc}") from exc
    return data


# Codex说明(自动生成)： 定义函数 write_touchstone，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def write_touchstone(
    data: TouchstoneData,
    path: str | Path,
    *,
    frequency_unit: str = "GHZ",
    data_format: str = "RI",
) -> None:
    """Write a full matrix in a simple Touchstone 1.x-compatible form."""

    # Codex说明(自动生成)： 计算并保存 output_path，供后续语句继续读取或更新。
    output_path = Path(path)
    # Codex说明(自动生成)： 调用 output_path.parent.mkdir，执行当前流程需要的具体操作或副作用。
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
    n_ports = data.n_ports
    # Codex说明(自动生成)： 检查条件 n_ports not in {2, 4}，根据结果选择后续执行路径。
    if n_ports < 1:
        raise ValueError("Touchstone output requires at least one port")
    # Codex说明(自动生成)： 调用 _validate_touchstone_data，执行当前流程需要的具体操作或副作用。
    _validate_touchstone_data(data)
    # Codex说明(自动生成)： 计算并保存 suffix_ports，供后续语句继续读取或更新。
    suffix_ports = _ports_from_suffix(output_path)
    # Codex说明(自动生成)： 检查条件 suffix_ports != n_ports，根据结果选择后续执行路径。
    if suffix_ports != n_ports:
        # Codex说明(自动生成)： 抛出 ValueError(f'Output extension {output_path.suffix!r} do...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            f"Output extension {output_path.suffix!r} does not match S{n_ports}P data"
        )

    # Codex说明(自动生成)： 计算并保存 frequency_unit，供后续语句继续读取或更新。
    frequency_unit = frequency_unit.upper()
    # Codex说明(自动生成)： 计算并保存 data_format，供后续语句继续读取或更新。
    data_format = data_format.upper()
    # Codex说明(自动生成)： 检查条件 frequency_unit not in FREQUENCY_MULTIPLIERS，根据结果选择后续执行路径。
    if frequency_unit not in FREQUENCY_MULTIPLIERS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported frequency unit: {frequency_uni...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported frequency unit: {frequency_unit}")
    # Codex说明(自动生成)： 检查条件 data_format not in {'RI', 'MA', 'DB'}，根据结果选择后续执行路径。
    if data_format not in {"RI", "MA", "DB"}:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported data format: {data_format}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported data format: {data_format}")

    # Codex说明(自动生成)： 计算并保存 order，供后续语句继续读取或更新。
    order = touchstone_order(n_ports)
    # Codex说明(自动生成)： 计算并保存 frequency_scale，供后续语句继续读取或更新。
    frequency_scale = FREQUENCY_MULTIPLIERS[frequency_unit]
    # Codex说明(自动生成)： 计算并保存 serialized_frequencies，供后续语句继续读取或更新。
    serialized_frequencies = [
        _format_float(freq / frequency_scale) for freq in data.frequency_hz
    ]
    # Codex说明(自动生成)： 计算并保存 parsed_serialized_frequencies，供后续语句继续读取或更新。
    parsed_serialized_frequencies = np.asarray(
        [float(value) for value in serialized_frequencies],
        dtype=float,
    )
    # Codex说明(自动生成)： 检查条件 len(parsed_serialized_frequencies) > 1 and np.any(np.di...，根据结果选择后续执行路径。
    if len(parsed_serialized_frequencies) > 1 and np.any(
        np.diff(parsed_serialized_frequencies) <= 0
    ):
        # Codex说明(自动生成)： 抛出 ValueError('Frequency points are too close to serialize...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            "Frequency points are too close to serialize distinctly; "
            "use a smaller output frequency unit"
        )
    # Codex说明(自动生成)： 计算并保存 lines，供后续语句继续读取或更新。
    lines = [
        "! Generated by insertion_loss_tool",
        "! Matrix convention: Sij means output port i due to input port j",
        f"# {frequency_unit} S {data_format} R {data.z0:g}",
    ]

    # Codex说明(自动生成)： 遍历 zip(serialized_frequencies, data.s) 中的 (freq_text, matrix)，逐项执行循环体逻辑。
    for freq_text, matrix in zip(serialized_frequencies, data.s):
        # Codex说明(自动生成)： 计算并保存 serialized_pairs，供后续语句继续读取或更新。
        serialized_pairs = [_complex_to_pair(matrix[i, j], data_format) for i, j in order]
        # Codex说明(自动生成)： 检查条件 n_ports == 2，根据结果选择后续执行路径。
        if n_ports == 2:
            # Codex说明(自动生成)： 计算并保存 fields，供后续语句继续读取或更新。
            fields = [freq_text]
            # Codex说明(自动生成)： 遍历 serialized_pairs 中的 (first, second)，逐项执行循环体逻辑。
            for first, second in serialized_pairs:
                # Codex说明(自动生成)： 调用 fields.extend 更新列表或集合，把当前步骤产生的数据加入结果。
                fields.extend([_format_float(first), _format_float(second)])
            # Codex说明(自动生成)： 调用 lines.append 更新列表或集合，把当前步骤产生的数据加入结果。
            lines.append(" ".join(fields))
            # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
            continue

        first_physical_line = True
        for matrix_row in range(n_ports):
            row_pairs = serialized_pairs[
                matrix_row * n_ports : (matrix_row + 1) * n_ports
            ]
            for chunk_start in range(0, n_ports, 4):
                fields = [freq_text] if first_physical_line else [" " * 16]
                for first, second in row_pairs[chunk_start : chunk_start + 4]:
                    fields.extend([_format_float(first), _format_float(second)])
                lines.append(" ".join(fields))
                first_physical_line = False

    # Codex说明(自动生成)： 调用 output_path.write_text 写出文件或数据，保存当前处理结果。
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Codex说明(自动生成)： 定义函数 touchstone_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def touchstone_order(
    n_ports: int,
    *,
    two_port_data_order: str = "21_12",
) -> list[tuple[int, int]]:
    """Return the serialized S-parameter order for supported file types."""

    # Codex说明(自动生成)： 检查条件 n_ports == 2，根据结果选择后续执行路径。
    if n_ports == 2:
        # Codex说明(自动生成)： 检查条件 two_port_data_order == '21_12'，根据结果选择后续执行路径。
        if two_port_data_order == "21_12":
            # Codex说明(自动生成)： 返回 [(0, 0), (1, 0), (0, 1), (1, 1)]，让调用方取得本函数的处理结果。
            return [(0, 0), (1, 0), (0, 1), (1, 1)]
        # Codex说明(自动生成)： 检查条件 two_port_data_order == '12_21'，根据结果选择后续执行路径。
        if two_port_data_order == "12_21":
            # Codex说明(自动生成)： 返回 [(0, 0), (0, 1), (1, 0), (1, 1)]，让调用方取得本函数的处理结果。
            return [(0, 0), (0, 1), (1, 0), (1, 1)]
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported S2P data order: {two_port_data...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported S2P data order: {two_port_data_order}")
    if n_ports < 1:
        raise ValueError("Touchstone matrices require at least one port")
    return [
        (out_port, in_port)
        for out_port in range(n_ports)
        for in_port in range(n_ports)
    ]


# Codex说明(自动生成)： 定义函数 to_magnitude_db，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def to_magnitude_db(values: np.ndarray, *, floor_db: float = -300.0) -> np.ndarray:
    """Convert complex or real magnitudes to dB with a finite floor."""

    # Codex说明(自动生成)： 计算并保存 magnitude，供后续语句继续读取或更新。
    magnitude = np.abs(values)
    # Codex说明(自动生成)： 进入上下文 np.errstate(divide='ignore')，确保文件、资源或临时状态按作用域正确释放。
    with np.errstate(divide="ignore"):
        # Codex说明(自动生成)： 计算并保存 db，供后续语句继续读取或更新。
        db = 20.0 * np.log10(magnitude)
    # Codex说明(自动生成)： 返回 np.maximum(db, floor_db)，让调用方取得本函数的处理结果。
    return np.maximum(db, floor_db)


# Codex说明(自动生成)： 定义函数 _ports_from_suffix，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _ports_from_suffix(path: Path) -> int:
    # Codex说明(自动生成)： 计算并保存 match，供后续语句继续读取或更新。
    match = re.search(r"\.s([1-9][0-9]*)p$", path.name, flags=re.IGNORECASE)
    # Codex说明(自动生成)： 检查条件 not match，根据结果选择后续执行路径。
    if not match:
        # Codex说明(自动生成)： 抛出 ValueError(f'File extension must be .s2p or .s4p: {path}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"File extension must be .sNp with N >= 1: {path}")
    # Codex说明(自动生成)： 返回 int(match.group(1))，让调用方取得本函数的处理结果。
    return int(match.group(1))


# Codex说明(自动生成)： 定义函数 _parse_option_line，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _parse_option_line(line: str) -> tuple[str, str, str, float]:
    # Codex说明(自动生成)： 计算并保存 tokens，供后续语句继续读取或更新。
    tokens = line[1:].strip().upper().split()
    # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
    unit = "GHZ"
    # Codex说明(自动生成)： 计算并保存 parameter，供后续语句继续读取或更新。
    parameter = "S"
    # Codex说明(自动生成)： 计算并保存 data_format，供后续语句继续读取或更新。
    data_format = "MA"
    # Codex说明(自动生成)： 计算并保存 z0，供后续语句继续读取或更新。
    z0 = 50.0

    categories = {
        "unit": set(FREQUENCY_MULTIPLIERS),
        "parameter": {"S", "Y", "Z", "H", "G"},
        "format": {"MA", "DB", "RI"},
    }
    seen: set[str] = set()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "R":
            if "reference" in seen:
                raise ValueError("Touchstone option line repeats R")
            if index + 1 >= len(tokens):
                raise ValueError("Touchstone option line has R without an impedance value")
            try:
                z0 = _parse_float(tokens[index + 1])
            except ValueError as exc:
                raise ValueError(
                    "Touchstone option line has an invalid reference impedance R value"
                ) from exc
            seen.add("reference")
            index += 2
            continue

        category = next(
            (name for name, allowed in categories.items() if token in allowed),
            None,
        )
        if category is None:
            raise ValueError(f"Unsupported Touchstone option token: {token}")
        if category in seen:
            raise ValueError(f"Touchstone option line repeats {category}")
        seen.add(category)
        if category == "unit":
            unit = token
        elif category == "parameter":
            parameter = token
        else:
            data_format = token
        index += 1

    # Codex说明(自动生成)： 检查条件 unit not in FREQUENCY_MULTIPLIERS，根据结果选择后续执行路径。
    if unit not in FREQUENCY_MULTIPLIERS:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported Touchstone frequency unit: {un...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported Touchstone frequency unit: {unit}")
    # Codex说明(自动生成)： 检查条件 not np.isfinite(z0) or z0 <= 0，根据结果选择后续执行路径。
    if not np.isfinite(z0) or z0 <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Touchstone reference impedance R must be po...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Touchstone reference impedance R must be positive and finite")
    # Codex说明(自动生成)： 返回 (unit, parameter, data_format, z0)，让调用方取得本函数的处理结果。
    return unit, parameter, data_format, z0


# Codex说明(自动生成)： 定义函数 _parse_keyword_line，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _parse_keyword_line(line: str) -> tuple[str, str]:
    # Codex说明(自动生成)： 计算并保存 close_index，供后续语句继续读取或更新。
    close_index = line.find("]")
    # Codex说明(自动生成)： 检查条件 close_index < 0，根据结果选择后续执行路径。
    if close_index < 0:
        # Codex说明(自动生成)： 抛出 ValueError(f'Malformed Touchstone keyword line: {line!r}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Malformed Touchstone keyword line: {line!r}")
    # Codex说明(自动生成)： 计算并保存 keyword，供后续语句继续读取或更新。
    keyword = line[1:close_index].strip().lower()
    # Codex说明(自动生成)： 计算并保存 rest，供后续语句继续读取或更新。
    rest = line[close_index + 1 :].strip()
    # Codex说明(自动生成)： 检查条件 not keyword，根据结果选择后续执行路径。
    if not keyword:
        # Codex说明(自动生成)： 抛出 ValueError(f'Malformed Touchstone keyword line: {line!r}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Malformed Touchstone keyword line: {line!r}")
    # Codex说明(自动生成)： 返回 (keyword, rest)，让调用方取得本函数的处理结果。
    return keyword, rest


# Codex说明(自动生成)： 定义函数 _parse_positive_int_keyword，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _parse_positive_int_keyword(keyword: str, value: str) -> int:
    # Codex说明(自动生成)： 检查条件 not value，根据结果选择后续执行路径。
    if not value:
        # Codex说明(自动生成)： 抛出 ValueError(f'[{keyword}] is missing its value')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"[{keyword}] is missing its value")
    # Codex说明(自动生成)： 计算并保存 token，供后续语句继续读取或更新。
    token = value.split()[0]
    # Codex说明(自动生成)： 计算并保存 parsed，供后续语句继续读取或更新。
    parsed = int(token)
    # Codex说明(自动生成)： 检查条件 parsed <= 0，根据结果选择后续执行路径。
    if parsed <= 0:
        # Codex说明(自动生成)： 抛出 ValueError(f'[{keyword}] must be positive')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"[{keyword}] must be positive")
    # Codex说明(自动生成)： 返回 parsed，让调用方取得本函数的处理结果。
    return parsed


# Codex说明(自动生成)： 定义函数 _parse_two_port_data_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _parse_two_port_data_order(value: str) -> str:
    # Codex说明(自动生成)： 计算并保存 token，供后续语句继续读取或更新。
    token = value.split()[0].upper()
    # Codex说明(自动生成)： 检查条件 token in {'21_12', '12_21'}，根据结果选择后续执行路径。
    if token in {"21_12", "12_21"}:
        # Codex说明(自动生成)： 返回 token，让调用方取得本函数的处理结果。
        return token
    # Codex说明(自动生成)： 抛出 ValueError('[Two-Port Data Order] must be either 21_12 ...，明确提示输入、状态或处理流程无法继续。
    raise ValueError(
        "[Two-Port Data Order] must be either 21_12 or 12_21 for S2P files"
    )


# Codex说明(自动生成)： 定义函数 _parse_float，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _parse_float(token: str) -> float:
    # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
    value = float(token.replace("D", "E").replace("d", "e"))
    # Codex说明(自动生成)： 检查条件 not np.isfinite(value)，根据结果选择后续执行路径。
    if not np.isfinite(value):
        # Codex说明(自动生成)： 抛出 ValueError(f'Non-finite numeric value in Touchstone dat...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Non-finite numeric value in Touchstone data: {token!r}")
    # Codex说明(自动生成)： 返回 value，让调用方取得本函数的处理结果。
    return value


# Codex说明(自动生成)： 定义函数 _format_float，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _format_float(value: float) -> str:
    # Codex说明(自动生成)： 返回 f'{value:.17g}'，让调用方取得本函数的处理结果。
    return f"{value:.17g}"


# Codex说明(自动生成)： 定义函数 _pair_to_complex，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _pair_to_complex(first: float, second: float, data_format: str) -> complex:
    # Codex说明(自动生成)： 检查条件 data_format == 'RI'，根据结果选择后续执行路径。
    if data_format == "RI":
        # Codex说明(自动生成)： 返回 complex(first, second)，让调用方取得本函数的处理结果。
        return complex(first, second)
    # Codex说明(自动生成)： 计算并保存 angle，供后续语句继续读取或更新。
    angle = np.deg2rad(second)
    # Codex说明(自动生成)： 检查条件 data_format == 'MA'，根据结果选择后续执行路径。
    if data_format == "MA":
        # Codex说明(自动生成)： 计算并保存 magnitude，供后续语句继续读取或更新。
        magnitude = first
    # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 data_format == 'DB'。
    elif data_format == "DB":
        # Codex说明(自动生成)： 计算并保存 magnitude，供后续语句继续读取或更新。
        magnitude = 10.0 ** (first / 20.0)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported Touchstone data format: {data_...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported Touchstone data format: {data_format}")
    # Codex说明(自动生成)： 返回 complex(magnitude * np.cos(angle), magnitude * np.sin(a...，让调用方取得本函数的处理结果。
    return complex(magnitude * np.cos(angle), magnitude * np.sin(angle))


# Codex说明(自动生成)： 定义函数 _complex_to_pair，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _complex_to_pair(value: complex, data_format: str) -> tuple[float, float]:
    # Codex说明(自动生成)： 检查条件 data_format == 'RI'，根据结果选择后续执行路径。
    if data_format == "RI":
        # Codex说明(自动生成)： 返回 (float(np.real(value)), float(np.imag(value)))，让调用方取得本函数的处理结果。
        return float(np.real(value)), float(np.imag(value))
    # Codex说明(自动生成)： 计算并保存 magnitude，供后续语句继续读取或更新。
    magnitude = abs(value)
    # Codex说明(自动生成)： 计算并保存 angle_deg，供后续语句继续读取或更新。
    angle_deg = float(np.rad2deg(np.angle(value)))
    # Codex说明(自动生成)： 检查条件 data_format == 'MA'，根据结果选择后续执行路径。
    if data_format == "MA":
        # Codex说明(自动生成)： 返回 (float(magnitude), angle_deg)，让调用方取得本函数的处理结果。
        return float(magnitude), angle_deg
    # Codex说明(自动生成)： 检查条件 data_format == 'DB'，根据结果选择后续执行路径。
    if data_format == "DB":
        # Codex说明(自动生成)： 检查条件 magnitude == 0.0，根据结果选择后续执行路径。
        if magnitude == 0.0:
            # Codex说明(自动生成)： 返回 (-300.0, angle_deg)，让调用方取得本函数的处理结果。
            return -300.0, angle_deg
        # Codex说明(自动生成)： 返回 (float(20.0 * np.log10(magnitude)), angle_deg)，让调用方取得本函数的处理结果。
        return float(20.0 * np.log10(magnitude)), angle_deg
    # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported Touchstone data format: {data_...，明确提示输入、状态或处理流程无法继续。
    raise ValueError(f"Unsupported Touchstone data format: {data_format}")


# Codex说明(自动生成)： 定义函数 _validate_frequency_axis，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_frequency_axis(frequency_hz: Sequence[float]) -> None:
    # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
    frequency = np.asarray(frequency_hz)
    if frequency.ndim != 1:
        raise ValueError("Frequencies must be one-dimensional")
    if np.iscomplexobj(frequency):
        raise ValueError("Frequencies must be real")
    try:
        frequency = frequency.astype(np.float64, copy=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("frequency_hz must contain float64-compatible values") from exc
    # Codex说明(自动生成)： 检查条件 len(frequency) == 0，根据结果选择后续执行路径。
    if len(frequency) == 0:
        # Codex说明(自动生成)： 抛出 ValueError('Touchstone file contains no frequency points')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Touchstone file contains no frequency points")
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(frequency))，根据结果选择后续执行路径。
    if np.any(~np.isfinite(frequency)):
        # Codex说明(自动生成)： 抛出 ValueError('Frequencies must be finite')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequencies must be finite")
    # DC is a valid Touchstone frequency used by waveform-channel fixtures.
    if np.any(frequency < 0):
        raise ValueError("All frequencies must be non-negative")
    # Codex说明(自动生成)： 检查条件 len(frequency) > 1 and np.any(np.diff(frequency) <= 0)，根据结果选择后续执行路径。
    if len(frequency) > 1 and np.any(np.diff(frequency) <= 0):
        # Codex说明(自动生成)： 抛出 ValueError('Frequencies must be strictly increasing')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Frequencies must be strictly increasing")


# Codex说明(自动生成)： 定义函数 _validate_touchstone_data，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _validate_touchstone_data(data: TouchstoneData) -> None:
    # Codex说明(自动生成)： 调用 _validate_frequency_axis，执行当前流程需要的具体操作或副作用。
    _validate_frequency_axis(data.frequency_hz)
    try:
        s_matrix = np.asarray(data.s, dtype=np.complex128)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("S-parameter matrix must contain numeric values") from exc
    if s_matrix.ndim != 3:
        raise ValueError("S-parameter matrix must be three-dimensional")
    if s_matrix.shape[1] == 0 or s_matrix.shape[1] != s_matrix.shape[2]:
        raise ValueError("S-parameter matrix port dimensions must be nonzero and square")
    # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
    n_ports = int(s_matrix.shape[1])
    # Codex说明(自动生成)： 计算并保存 expected_shape，供后续语句继续读取或更新。
    expected_shape = (len(data.frequency_hz), n_ports, n_ports)
    # Codex说明(自动生成)： 检查条件 data.s.shape != expected_shape，根据结果选择后续执行路径。
    if s_matrix.shape != expected_shape:
        # Codex说明(自动生成)： 抛出 ValueError(f'S-parameter matrix shape {data.s.shape} do...，明确提示输入、状态或处理流程无法继续。
        raise ValueError(
            f"S-parameter matrix shape {s_matrix.shape} does not match {expected_shape}"
        )
    # Codex说明(自动生成)： 检查条件 np.any(~np.isfinite(data.s))，根据结果选择后续执行路径。
    if not np.all(np.isfinite(s_matrix.real)) or not np.all(np.isfinite(s_matrix.imag)):
        # Codex说明(自动生成)： 抛出 ValueError('S-parameter matrix contains non-finite valu...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("S-parameter matrix contains non-finite values")
    # Codex说明(自动生成)： 检查条件 not np.isfinite(data.z0) or data.z0 <= 0，根据结果选择后续执行路径。
    if isinstance(data.z0, bool) or not isinstance(data.z0, Real):
        raise ValueError("Reference impedance z0 must be a real number, not bool")
    try:
        z0 = float(data.z0)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Reference impedance z0 must be float-compatible") from exc
    if not np.isfinite(z0) or z0 <= 0:
        # Codex说明(自动生成)： 抛出 ValueError('Reference impedance z0 must be positive and...，明确提示输入、状态或处理流程无法继续。
        raise ValueError("Reference impedance z0 must be positive and finite")
