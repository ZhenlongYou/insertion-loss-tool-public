"""Independent sampled-domain diagnostics for generated channel files.

These checks intentionally operate on the final S-matrix, after serialization
and reread when used by the packaged self-test. They certify only the sampled
matrix passivity condition; they do not claim broadband causality or physical
realizability between frequency points.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import ClassVar

import numpy as np

from .touchstone import TouchstoneData


@dataclass(frozen=True)
class SampledNetworkDiagnostics:
    __slots__ = (
        "maximum_singular_value",
        "worst_frequency_hz",
        "passivity_margin",
        "sampled_passive",
    )

    maximum_singular_value: float
    worst_frequency_hz: float
    passivity_margin: float
    sampled_passive: bool
    classification: ClassVar[str] = (
        "sampled-passive engineering approximation; broadband causality is not certified"
    )


def diagnose_sampled_network(
    data: TouchstoneData,
    *,
    tolerance: float = 1.0e-9,
) -> SampledNetworkDiagnostics:
    """Measure the worst sampled singular value of a finite S-matrix."""

    if not isinstance(data, TouchstoneData):
        raise TypeError("data must be a TouchstoneData instance")
    frequency_hz = np.asarray(data.frequency_hz, dtype=float)
    matrix = np.asarray(data.s, dtype=complex)
    if frequency_hz.ndim != 1 or frequency_hz.size == 0:
        raise ValueError("frequency_hz must be a nonempty one-dimensional array")
    if matrix.ndim != 3 or matrix.shape != (
        frequency_hz.size,
        matrix.shape[1],
        matrix.shape[1],
    ):
        raise ValueError("S-parameter data must be a square matrix at every frequency")
    if not np.all(np.isfinite(frequency_hz)) or not np.all(np.isfinite(matrix)):
        raise ValueError("diagnostics require finite frequency and S-parameter values")
    if not isinstance(tolerance, Real) or isinstance(tolerance, bool):
        raise TypeError("tolerance must be a real number")
    tolerance = float(tolerance)
    if not np.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("tolerance must be finite and non-negative")

    per_frequency = np.linalg.svd(matrix, compute_uv=False).max(axis=1)
    worst_index = int(np.argmax(per_frequency))
    maximum = float(per_frequency[worst_index])
    return SampledNetworkDiagnostics(
        maximum_singular_value=maximum,
        worst_frequency_hz=float(frequency_hz[worst_index]),
        passivity_margin=1.0 - maximum,
        sampled_passive=maximum <= 1.0 + tolerance,
    )


def assert_sampled_passive(
    data: TouchstoneData,
    *,
    context: str = "Network",
    tolerance: float = 1.0e-9,
) -> SampledNetworkDiagnostics:
    """Return diagnostics or reject a matrix that fails sampled passivity."""

    diagnostics = diagnose_sampled_network(data, tolerance=tolerance)
    if not diagnostics.sampled_passive:
        raise ValueError(
            f"{context} S-parameter matrix is not passive: maximum singular "
            f"value {diagnostics.maximum_singular_value:.6g} at "
            f"{diagnostics.worst_frequency_hz:.6g} Hz"
        )
    return diagnostics


def minimum_s2p_insertion_loss_db(return_loss_db: float) -> float:
    """Closed-form loss floor for this reciprocal quadrature-reflection S2P.

    With reflection magnitude ``r`` and through magnitude ``t``, the model's
    singular value is ``sqrt(r**2 + t**2)``. Passivity therefore requires
    ``t**2 <= 1 - r**2``.
    """

    if not isinstance(return_loss_db, Real) or isinstance(return_loss_db, bool):
        raise TypeError("return_loss_db must be a real number")
    return_loss_db = float(return_loss_db)
    if not np.isfinite(return_loss_db) or return_loss_db <= 0.0:
        raise ValueError("return_loss_db must be positive and finite")
    reflected_power = 10.0 ** (-return_loss_db / 10.0)
    return float(-10.0 * np.log10(1.0 - reflected_power))
