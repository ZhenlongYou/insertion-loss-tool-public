"""Directed mutant: restore strict-positive, unitless-Hz image parsing."""

from __future__ import annotations

from .models import parse_frequency


def parse_image_frequency(value: object, *, allow_zero: bool = False) -> float:
    del allow_zero
    return parse_frequency(str(value))
