"""Frequency parsing rules specific to datasheet image calibration."""

from __future__ import annotations

import re

import numpy as np

from .models import FREQUENCY_UNITS


_IMAGE_FREQUENCY_RE = re.compile(
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)([a-z]*)",
    re.IGNORECASE,
)


def parse_image_frequency(value: object, *, allow_zero: bool = False) -> float:
    """Parse an image-axis value; omitted units mean GHz in this GUI."""

    text = str(value).strip().lower().replace(" ", "")
    match = _IMAGE_FREQUENCY_RE.fullmatch(text)
    if match is None:
        raise ValueError("invalid image frequency")
    number = float(match.group(1))
    unit = match.group(2) or "ghz"
    if unit not in FREQUENCY_UNITS:
        raise ValueError("unsupported image frequency unit")
    frequency_hz = number * FREQUENCY_UNITS[unit]
    if not np.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("image frequency must be non-negative")
    if not allow_zero and frequency_hz == 0:
        raise ValueError("image frequency must be positive")
    return frequency_hz
