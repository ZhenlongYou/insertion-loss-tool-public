"""Directed fault: keep the old 801-point GUI value after loading a source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .touchstone import TouchstoneData, read_touchstone


@dataclass(frozen=True)
class ModifyInputSource:
    path: Path
    data: TouchstoneData
    ports: int
    points: int
    start_hz: float
    stop_hz: float


def load_modify_input(path: object) -> ModifyInputSource:
    source_path = Path(str(path)).expanduser().resolve()
    data = read_touchstone(source_path)
    return ModifyInputSource(
        path=source_path,
        data=data,
        ports=data.n_ports,
        points=801,
        start_hz=float(data.frequency_hz[0]),
        stop_hz=float(data.frequency_hz[-1]),
    )
