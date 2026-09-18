"""Insertion loss Touchstone generation and editing helpers."""

from .touchstone import (
    NetworkTransfer,
    TouchstoneData,
    read_touchstone,
    select_transfer,
    to_magnitude_db,
    write_touchstone,
)
from .validation import (
    SampledNetworkDiagnostics,
    assert_sampled_passive,
    diagnose_sampled_network,
    minimum_s2p_insertion_loss_db,
)

# Codex说明(自动生成)： 计算并保存 __all__，供后续语句继续读取或更新。
__all__ = [
    "NetworkTransfer",
    "SampledNetworkDiagnostics",
    "TouchstoneData",
    "__version__",
    "read_touchstone",
    "assert_sampled_passive",
    "diagnose_sampled_network",
    "minimum_s2p_insertion_loss_db",
    "select_transfer",
    "to_magnitude_db",
    "write_touchstone",
]

# Codex说明(自动生成)： 计算并保存 __version__，供后续语句继续读取或更新。
__version__ = "0.5.0"
