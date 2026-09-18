"""Touchstone source loading contract for the Modify workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .touchstone import TouchstoneData, read_touchstone


@dataclass(frozen=True)
class ModifyInputSource:
    """Validated Modify input plus the metadata shown in the GUI."""

    path: Path
    data: TouchstoneData
    ports: int
    points: int
    start_hz: float
    stop_hz: float


def load_modify_input(path: object) -> ModifyInputSource:
    """Read one Touchstone file and expose its exact source sweep metadata."""

    text = str(path).strip()
    if not text:
        raise ValueError("请选择 Touchstone 输入文件。")
    source_path = Path(text).expanduser().resolve()
    data = read_touchstone(source_path)
    return ModifyInputSource(
        path=source_path,
        data=data,
        ports=data.n_ports,
        points=int(data.frequency_hz.size),
        start_hz=float(data.frequency_hz[0]),
        stop_hz=float(data.frequency_hz[-1]),
    )
