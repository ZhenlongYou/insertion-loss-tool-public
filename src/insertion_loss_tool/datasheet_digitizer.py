"""Digitize magnitude traces from rasterized datasheet plots.

The digitizer deliberately treats the image as a magnitude-only source.  It
recovers the plot rectangle from the regular grid and samples coloured traces
at the native horizontal pixel resolution; it never invents phase data or
additional independent samples.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import colorsys
from pathlib import Path
import re
import shutil
import subprocess
from typing import Sequence, cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .curve_visual_review import CurveReviewRegion, attach_visual_review
from .raster_path_geometry import colour_evidence_mask, preserve_raster_turns
from .trace_recovery_policy import (
    AMBIGUOUS_HUE_PAIR_SIZE,
    ANTIALIAS_BRIDGE_DENSITY_LIMIT,
    ANTIALIAS_SHADE_DIRECTION_DISTANCE,
    MAX_UNIQUE_HUE_AMBIGUOUS_COLUMN_FRACTION,
    MAX_UNIQUE_HUE_TRANSITION_GAP,
    MAX_RELIABLE_AUTO_TRACES,
    MAX_SINGLE_ANCHOR_HUE_AMBIGUOUS_COLUMN_FRACTION,
    MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION,
    MINIMUM_UNIQUE_HUE_PARTIAL_SPAN,
    MINIMUM_PRODUCT_GRID_LINES,
    PALE_GRID_MAX_INTENSITY,
)


_PARAMETER_RE = re.compile(
    r"(?<![A-Za-z])(?:[1-9]\s*:?\s*)?"
    r"(?P<parameter>S(?:[1-8][1-8]|[DC][DC][1-4][1-4]))\b",
    re.IGNORECASE,
)
_FREQUENCY_RE = re.compile(
    r"(?<![\w.])([0-9]+(?:\.[0-9]+)?)\s*(GHz|MHz|kHz|Hz)\b",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"^\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$")
_LEADING_NUMBER_RE = re.compile(r"^\s*([+-]?[0-9]+(?:\.[0-9]+)?)\b")
_FREQUENCY_DIVISION_RE = re.compile(
    r"\b(?:GHz|MHz|kHz|Hz)\s*[/|iIlL1]?\s*d[iIlL1]v\b",
    re.IGNORECASE,
)
_FREQUENCY_AXIS_UNIT_RE = re.compile(
    r"\bfrequency\b[^\n]*?\b(GHz|MHz|kHz|Hz)\b",
    re.IGNORECASE,
)
MAX_DECODED_IMAGE_PIXELS = 12_000_000
MINIMUM_TRACE_COVERAGE = 0.45
# A passive fixture/cable magnitude plot may cross 0 dB by a small raster or
# calibration error. Larger positive excursions are annotations or grid leaks,
# not a physically credible passive S-parameter trace.
PASSIVE_MAGNITUDE_TOLERANCE_DB = 0.5
# Chromatic direction is invariant to white-background antialiasing. Saturated
# pixels use a stricter direction gate so adjacent warm hues cannot collapse
# into a fabricated intermediate colour; pale antialias shades stay grouped.
COLOR_DIRECTION_CLUSTER_DISTANCE = 0.8
COLOR_DIRECTION_STRICT_DISTANCE = 0.4
COLOR_SATURATION_STRICT_FLOOR = 0.35
MAX_COUPLED_OBSERVATIONS_PER_COLUMN = 8
MAX_COUPLED_INTERPOLATION_PAIRINGS = 16


@dataclass(frozen=True)
class DigitizedCurve:
    """One magnitude trace sampled at its visible horizontal pixels."""

    color: str
    rgb: tuple[int, int, int]
    frequency_hz: NDArray[np.float64]
    magnitude_db: NDArray[np.float64]
    pixel_points: NDArray[np.float64]
    confidence: float
    observed_samples: int = 0
    shared_overlap_samples: int = 0
    interpolated_samples: int = 0
    sample_provenance: tuple[str, ...] = ()
    visual_confidence: float = 1.0
    review_status: str = "clear"
    review_regions: tuple[CurveReviewRegion, ...] = ()


@dataclass(frozen=True)
class _TraceObservation:
    """One coloured vertical cluster available to the coupled tracker."""

    center: float
    rgb: NDArray[np.float64]
    observed: bool = True


@dataclass(frozen=True)
class DigitizationResult:
    """Plot geometry and the traces recovered from one image."""

    image_width: int
    image_height: int
    plot_box: tuple[int, int, int, int]
    curves: tuple[DigitizedCurve, ...]
    warnings: tuple[str, ...] = ()
    detected_parameter: str | None = None


@dataclass(frozen=True)
class OcrLine:
    """One OCR line and its image-space bounding rectangle."""

    text: str
    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True)
class AxisCalibration:
    """Conservative editable defaults recovered from visible axis labels."""

    status: str
    start_hz: float | None = None
    stop_hz: float | None = None
    step_hz: float | None = None
    y_min_db: float | None = None
    y_max_db: float | None = None
    spacing: str | None = None
    detected_parameter: str | None = None
    missing: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImageAnalysis:
    """Plot geometry plus conservative OCR-derived calibration."""

    image_width: int
    image_height: int
    plot_box: tuple[int, int, int, int]
    calibration: AxisCalibration


def _cluster_positions(mask: NDArray[np.bool_]) -> NDArray[np.float64]:
    positions = np.flatnonzero(mask)
    if not positions.size:
        return np.empty(0, dtype=np.float64)
    boundaries = np.flatnonzero(np.diff(positions) > 1) + 1
    return np.asarray(
        [float(np.mean(group)) for group in np.split(positions, boundaries)],
        dtype=np.float64,
    )


def _regular_grid_extent(
    centres: NDArray[np.float64],
    *,
    minimum_lines: int = 5,
    minimum_extent: float = 0.0,
    preferred_completeness: float = 0.9,
) -> tuple[int, int]:
    """Return endpoints of the strongest permitted regular progression."""

    if minimum_lines < 4:
        raise ValueError("A regular plot grid needs at least four lines.")
    if centres.size < minimum_lines:
        raise ValueError("Could not locate a regular plot grid.")
    best_score: tuple[int, int, float, float, int] | None = None
    best_extent: tuple[float, float] | None = None
    for left_index in range(centres.size - minimum_lines + 1):
        for right_index in range(left_index + minimum_lines - 1, centres.size):
            left = float(centres[left_index])
            right = float(centres[right_index])
            if right - left < minimum_extent:
                continue
            for intervals in range(minimum_lines - 1, 17):
                step = (right - left) / intervals
                if step < 8.0:
                    continue
                expected = left + step * np.arange(intervals + 1)
                distance = np.min(np.abs(expected[:, None] - centres[None, :]), axis=1)
                tolerance = max(2.25, step * 0.055)
                matched = int(np.count_nonzero(distance <= tolerance))
                if matched < minimum_lines:
                    continue
                mean_error = float(np.mean(distance[distance <= tolerance]))
                # A complete progression is stronger evidence than extending a
                # real grid to unrelated page/frame lines merely to gain one
                # match. Then prefer more lines, a wider plot, and lower error.
                completeness = matched / (intervals + 1)
                score = (
                    int(completeness >= preferred_completeness),
                    matched,
                    right - left,
                    -mean_error,
                    -intervals,
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_extent = (left, right)
    if best_extent is None:
        raise ValueError("Could not locate a regular plot grid.")
    return round(best_extent[0]), round(best_extent[1])


def _regular_grid_extent_with_supported_endpoints(
    centres: NDArray[np.float64], endpoint_support: NDArray[np.float64]
) -> tuple[int, int] | None:
    """Recover a wider grid when dense traces hide one or two internal rows."""

    best_score: tuple[int, float, float, float, int] | None = None
    best_extent: tuple[float, float] | None = None
    for left_index in range(centres.size - 4):
        if endpoint_support[left_index] < 0.75:
            continue
        for right_index in range(left_index + 4, centres.size):
            if endpoint_support[right_index] < 0.75:
                continue
            left = float(centres[left_index])
            right = float(centres[right_index])
            for intervals in range(4, 17):
                step = (right - left) / intervals
                if step < 8.0:
                    continue
                expected = left + step * np.arange(intervals + 1)
                distance = np.min(
                    np.abs(expected[:, None] - centres[None, :]), axis=1
                )
                tolerance = max(2.25, step * 0.055)
                matched = int(np.count_nonzero(distance <= tolerance))
                completeness = matched / (intervals + 1)
                if matched < 8 or completeness < 0.72:
                    continue
                mean_error = float(np.mean(distance[distance <= tolerance]))
                score = (
                    matched,
                    right - left,
                    completeness,
                    -mean_error,
                    -intervals,
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_extent = (left, right)
    if best_extent is None:
        return None
    return round(best_extent[0]), round(best_extent[1])


def _detect_plot_box_from_neutral_lines(
    rgb: NDArray[np.uint8],
    neutral_line: NDArray[np.bool_],
    *,
    minimum_horizontal_lines: int,
) -> tuple[int, int, int, int]:
    """Locate one 2-D grid from a prequalified neutral-pixel mask."""

    horizontal = _cluster_positions(neutral_line.sum(axis=1) >= rgb.shape[1] * 0.34)
    minimum_extent = max(80.0, rgb.shape[0] * 0.22)
    if minimum_horizontal_lines == 3:
        # A short vertical scale can have just its two borders and one centre
        # grid line. Require a complete, equally spaced triple here; the dense
        # independent vertical progression below is still mandatory. This is
        # used only after the existing four/five-line locators have failed.
        triples = []
        for first in range(len(horizontal) - 2):
            for last in range(first + 2, len(horizontal)):
                span = float(horizontal[last] - horizontal[first])
                if span < minimum_extent:
                    continue
                midpoint = (horizontal[first] + horizontal[last]) / 2
                errors = abs(horizontal[first + 1:last] - midpoint)
                if errors.size and errors.min() <= max(2.25, span * 0.0125):
                    triples.append((span, -float(errors.min()), int(round(horizontal[first])), int(round(horizontal[last]))))
        if not triples:
            raise ValueError("Could not locate a regular plot grid.")
        _span, _error, top, bottom = max(triples)
    else:
        top, bottom = _regular_grid_extent(
            horizontal,
            minimum_lines=minimum_horizontal_lines,
            minimum_extent=minimum_extent,
            preferred_completeness=0.8,
        )
    horizontal_rows = [
        int(round(position))
        for position in horizontal
        if top - 2 <= position <= bottom + 2
    ]
    horizontal_support = np.mean(
        np.asarray(
            [
                np.any(
                    neutral_line[
                        max(0, row - 2) : min(rgb.shape[0], row + 3)
                    ],
                    axis=0,
                )
                for row in horizontal_rows
            ]
        ),
        axis=0,
    )
    # Thin coloured traces and deep notches commonly overwrite several grid
    # rows in exported VNA screenshots.  Six of ten divisions still provide
    # strong repeated horizontal evidence; requiring 75% truncated real
    # Wilder plots to an internal subset of their grid.
    supported_columns = np.flatnonzero(horizontal_support >= 0.60)
    if not supported_columns.size:
        raise ValueError("Could not locate a regular plot grid.")
    supported_gap = max(4, round(rgb.shape[1] * 0.01))
    boundaries = np.flatnonzero(np.diff(supported_columns) > supported_gap) + 1
    spans = [
        group
        for group in np.split(supported_columns, boundaries)
        if group.size >= 80
    ]
    if spans:
        horizontal_span = max(spans, key=lambda group: group.size)
        span_left = int(horizontal_span[0])
        span_right = int(horizontal_span[-1])
    else:
        # Dotted grids can shift their dash phase from row to row, leaving no
        # column supported by 60% of horizontal lines.  The later regular
        # vertical progression remains mandatory, so using the full width here
        # does not accept an isolated pale page rule as a plot.
        span_left = 0
        span_right = rgb.shape[1] - 1
    margin = max(4.0, (span_right - span_left) * 0.03)

    vertical_extents: set[tuple[int, int]] = set()
    for support in (0.75, 0.34, 0.20):
        vertical = _cluster_positions(
            neutral_line[top : bottom + 1].sum(axis=0)
            >= (bottom - top + 1) * support
        )
        vertical = vertical[
            (vertical >= span_left - margin) & (vertical <= span_right + margin)
        ]
        try:
            extent = _regular_grid_extent(vertical)
        except ValueError:
            continue
        vertical_extents.add(extent)
    if not vertical_extents:
        raise ValueError("Could not locate a regular plot grid.")
    left, right = min(
        vertical_extents,
        key=lambda item: (
            abs(item[0] - span_left) + abs(item[1] - span_right),
            -(item[1] - item[0]),
        ),
    )
    vertical_grid = _cluster_positions(
        neutral_line[top : bottom + 1].sum(axis=0)
        >= (bottom - top + 1) * 0.34
    )
    vertical_grid = vertical_grid[
        (vertical_grid >= left - 3) & (vertical_grid <= right + 3)
    ]
    if vertical_grid.size >= 5 and horizontal.size >= 5:
        endpoint_support = np.asarray(
            [
                np.mean(
                    [
                        np.any(
                            neutral_line[
                                max(0, int(round(y_position)) - 2) : min(
                                    rgb.shape[0], int(round(y_position)) + 3
                                ),
                                max(0, int(round(x_position)) - 2) : min(
                                    rgb.shape[1], int(round(x_position)) + 3
                                ),
                            ]
                        )
                        for x_position in vertical_grid
                    ]
                )
                for y_position in horizontal
            ],
            dtype=np.float64,
        )
        recovered_vertical_extent = _regular_grid_extent_with_supported_endpoints(
            horizontal, endpoint_support
        )
        if recovered_vertical_extent is not None:
            top, bottom = recovered_vertical_extent
    if right - left < 80 or bottom - top < 80:
        raise ValueError("Detected plot area is too small.")
    return left, top, right, bottom


def _chromatic_pixel_support(
    rgb: NDArray[np.uint8], box: tuple[int, int, int, int]
) -> int:
    left, top, right, bottom = box
    crop = rgb[top : bottom + 1, left : right + 1].astype(np.float32)
    maximum = crop.max(axis=2)
    chroma = maximum - crop.min(axis=2)
    saturation = np.divide(
        chroma, maximum, out=np.zeros_like(chroma), where=maximum > 0
    )
    return int(np.count_nonzero((chroma >= 10) & (saturation >= 0.04)))


def _detect_plot_box_from_internal_grid(
    rgb: NDArray[np.uint8], neutral_line: NDArray[np.bool_]
) -> tuple[int, int, int, int] | None:
    """Recover black-bordered plots from their repeated internal gray grid."""

    vertical = _cluster_positions(
        neutral_line.sum(axis=0) >= rgb.shape[0] * 0.15
    )
    try:
        internal_left, internal_right = _regular_grid_extent(
            vertical,
            minimum_lines=5,
            minimum_extent=max(80.0, rgb.shape[1] * 0.25),
            preferred_completeness=0.8,
        )
    except ValueError:
        return None
    internal_columns = vertical[
        (vertical >= internal_left - 2) & (vertical <= internal_right + 2)
    ]
    if internal_columns.size < 5:
        return None
    vertical_step = float(np.median(np.diff(internal_columns)))
    if vertical_step < 8.0:
        return None
    left = max(0, round(internal_left - vertical_step))
    right = min(rgb.shape[1] - 1, round(internal_right + vertical_step))
    if right - left < 80:
        return None

    horizontal = _cluster_positions(
        neutral_line[:, left : right + 1].sum(axis=1)
        >= (right - left + 1) * 0.25
    )
    if horizontal.size < 4:
        return None
    border_neutral = (np.ptp(rgb, axis=2) <= 12) & (np.max(rgb, axis=2) <= 245)
    candidates: list[tuple[int, int, tuple[int, int, int, int]]] = []
    for top_index in range(horizontal.size - 3):
        for bottom_index in range(top_index + 3, horizontal.size):
            observed_top = float(horizontal[top_index])
            observed_bottom = float(horizontal[bottom_index])
            for intervals in range(3, 17):
                step = (observed_bottom - observed_top) / intervals
                if step < 8.0:
                    continue
                expected = observed_top + step * np.arange(intervals + 1)
                distance = np.min(
                    np.abs(expected[:, None] - horizontal[None, :]), axis=1
                )
                tolerance = max(2.25, step * 0.055)
                matched = int(np.count_nonzero(distance <= tolerance))
                if matched < 4 or matched / (intervals + 1) < 0.8:
                    continue
                expanded_top = max(0, round(observed_top - step))
                expanded_bottom = min(
                    rgb.shape[0] - 1, round(observed_bottom + step)
                )
                top_support = float(
                    np.mean(
                        np.any(
                            border_neutral[
                                max(0, expanded_top - 2) : expanded_top + 3,
                                left : right + 1,
                            ],
                            axis=0,
                        )
                    )
                )
                bottom_support = float(
                    np.mean(
                        np.any(
                            border_neutral[
                                max(0, expanded_bottom - 2) : min(
                                    rgb.shape[0], expanded_bottom + 3
                                ),
                                left : right + 1,
                            ],
                            axis=0,
                        )
                    )
                )
                if min(top_support, bottom_support) < 0.55:
                    continue
                box = (left, expanded_top, right, expanded_bottom)
                candidates.append(
                    (
                        _chromatic_pixel_support(rgb, box),
                        (right - left + 1) * (expanded_bottom - expanded_top + 1),
                        box,
                    )
                )
    if not candidates:
        return None
    support, _area, box = max(candidates, key=lambda item: (item[0], item[1]))
    if support < (box[2] - box[0] + 1) * 0.5:
        return None
    return box


def _detect_plot_box(rgb: NDArray[np.uint8]) -> tuple[int, int, int, int]:
    channel_spread = np.ptp(rgb, axis=2)
    intensity = np.max(rgb, axis=2)
    # Prefer the original strict mask.  Product PDFs may rasterise dotted grids
    # just above level 230, so a second pass admits pale neutral pixels while
    # still requiring a regular grid in both axes.  Four horizontal lines are
    # sufficient only in that 2-D fallback: short 0 to -3 dB plots commonly
    # contain three vertical divisions and cannot provide a fifth row.
    attempts = (
        ((channel_spread <= 7) & (intensity >= 55) & (intensity <= 230), 5),
        (
            (channel_spread <= 12)
            & (intensity >= 55)
            & (intensity <= PALE_GRID_MAX_INTENSITY),
            5,
        ),
        (
            (channel_spread <= 12)
            & (intensity >= 55)
            & (intensity <= PALE_GRID_MAX_INTENSITY),
            MINIMUM_PRODUCT_GRID_LINES,
        ),
        (
            (channel_spread <= 12) & (intensity <= PALE_GRID_MAX_INTENSITY),
            5,
        ),
        (
            (channel_spread <= 12) & (intensity <= PALE_GRID_MAX_INTENSITY),
            MINIMUM_PRODUCT_GRID_LINES,
        ),
    )
    first_result: tuple[int, int, int, int] | None = None
    for neutral_line, minimum_horizontal_lines in attempts:
        try:
            result = _detect_plot_box_from_neutral_lines(
                rgb,
                neutral_line,
                minimum_horizontal_lines=minimum_horizontal_lines,
            )
            if first_result is None:
                first_result = result
        except ValueError:
            continue
    internal_result = _detect_plot_box_from_internal_grid(rgb, attempts[0][0])
    if internal_result is not None:
        internal_support = _chromatic_pixel_support(rgb, internal_result)
        if first_result is None:
            return internal_result
        first_support = _chromatic_pixel_support(rgb, first_result)
        first_width = first_result[2] - first_result[0] + 1
        internal_width = internal_result[2] - internal_result[0] + 1
        if (
            first_support < first_width * 0.5
            and internal_support > first_support + internal_width * 0.5
        ):
            return internal_result
    if first_result is not None:
        return first_result
    # A three-line horizontal scale is accepted only with the existing dense
    # vertical-grid and endpoint support contract. It must not weaken a plot
    # rectangle already found using the stronger four/five-line evidence.
    for neutral_line, _minimum_lines in (attempts[0], attempts[-1]):
        try:
            return _detect_plot_box_from_neutral_lines(
                rgb, neutral_line, minimum_horizontal_lines=3
            )
        except ValueError:
            continue
    raise ValueError("Could not locate a regular plot grid.")


def _frequency_hz(value: str, unit: str) -> float:
    return float(value) * {
        "hz": 1.0,
        "khz": 1e3,
        "mhz": 1e6,
        "ghz": 1e9,
    }[unit.lower()]


def detect_axis_calibration(
    lines: Sequence[OcrLine],
    *,
    plot_box: tuple[int, int, int, int],
    image_width: int,
    image_height: int,
) -> AxisCalibration:
    """Infer only axes that are visibly supported by positioned OCR labels."""

    left, top, right, bottom = plot_box
    plot_width = right - left
    plot_height = bottom - top
    frequency_candidates: list[tuple[float, float, str]] = []
    step_hz: float | None = None
    y_candidates: list[tuple[float, float]] = []
    all_text = "\n".join(line.text for line in lines)
    detected_parameter, parameter_warnings = detect_parameter_text(all_text)

    division_label_visible = bool(_FREQUENCY_DIVISION_RE.search(all_text))
    positioned_axis_units = {
        match.group(1).lower()
        for line in lines
        if (
            (match := _FREQUENCY_AXIS_UNIT_RE.search(line.text)) is not None
            and bottom <= line.top + line.height / 2 <= min(
                image_height, bottom + plot_height * 0.35
            )
            and line.left + line.width >= left
            and line.left <= right
        )
    }
    numeric_axis_unit = (
        next(iter(positioned_axis_units))
        if len(positioned_axis_units) == 1
        else None
    )

    for line in lines:
        center_x = line.left + line.width / 2
        center_y = line.top + line.height / 2
        matches = list(_FREQUENCY_RE.finditer(line.text))
        matches = [
            match
            for match in matches
            if not re.match(
                r"^\s*[/|iIlL1]?\s*d[iIlL1]v\b",
                line.text[match.end() : match.end() + 8],
                re.IGNORECASE,
            )
        ]
        step_position = line.text.lower().find("step")
        if step_position >= 0 and len(matches) >= 2:
            step_match = min(
                (match for match in matches if match.start() > step_position),
                key=lambda match: match.start(),
                default=matches[1],
            )
            step_hz = _frequency_hz(step_match.group(1), step_match.group(2))
            matches = [match for match in matches if match is not step_match]
        if (
            matches
            and bottom - 4 <= center_y <= min(image_height, bottom + plot_height * 0.24)
            and left - plot_width * 0.08 <= center_x <= right + plot_width * 0.08
        ):
            selected_matches = (matches[0], matches[-1]) if len(matches) > 1 else (matches[0],)
            for match in selected_matches:
                character_center = (match.start() + match.end()) / 2
                match_x = line.left + line.width * character_center / max(
                    len(line.text), 1
                )
                frequency_candidates.append(
                    (
                        match_x,
                        _frequency_hz(match.group(1), match.group(2)),
                        line.text,
                    )
                )
        elif (
            numeric_axis_unit is not None
            and bottom - 4
            <= center_y
            <= min(image_height, bottom + plot_height * 0.24)
            and left - plot_width * 0.08
            <= center_x
            <= right + plot_width * 0.08
        ):
            numeric_tick = _NUMBER_RE.fullmatch(line.text)
            if numeric_tick is not None:
                frequency_candidates.append(
                    (
                        center_x,
                        _frequency_hz(numeric_tick.group(1), numeric_axis_unit),
                        line.text,
                    )
                )
        number = _NUMBER_RE.fullmatch(line.text) or _LEADING_NUMBER_RE.match(line.text)
        if (
            number
            and left - plot_width * 0.24 <= line.left < left - 2
            and top - plot_height * 0.04 <= center_y <= bottom + plot_height * 0.02
        ):
            y_candidates.append((center_y, float(number.group(1))))

    start_hz: float | None = None
    stop_hz: float | None = None
    if len(frequency_candidates) >= 2:
        ordered = sorted(frequency_candidates, key=lambda item: item[0])
        first, last = ordered[0], ordered[-1]
        endpoints_visible = (
            abs(first[0] - left) <= plot_width * 0.12
            and abs(last[0] - right) <= plot_width * 0.12
        )
        if endpoints_visible and last[1] > first[1] >= 0:
            start_hz, stop_hz = first[1], last[1]

    y_max_db: float | None = None
    y_min_db: float | None = None
    if len(y_candidates) >= 2:
        minimum_position = min(item[0] for item in y_candidates)
        maximum_position = max(item[0] for item in y_candidates)
        top_values = [
            value
            for position, value in y_candidates
            if position <= minimum_position + plot_height * 0.04
        ]
        bottom_values = [
            value
            for position, value in y_candidates
            if position >= maximum_position - plot_height * 0.04
        ]
        candidate_max = max(top_values)
        candidate_min = min(bottom_values)
        endpoints_visible = (
            abs(minimum_position - top) <= plot_height * 0.08
            and abs(maximum_position - bottom) <= plot_height * 0.08
        )
        if (
            endpoints_visible
            and candidate_max > candidate_min
        ):
            y_max_db, y_min_db = candidate_max, candidate_min

    spacing = "linear" if step_hz is not None or division_label_visible else None
    fields = {
        "start": start_hz,
        "stop": stop_hz,
        "step": step_hz,
        "y_max": y_max_db,
        "y_min": y_min_db,
        "spacing": spacing,
    }
    missing = tuple(name for name, value in fields.items() if value is None)
    status = "detected" if not missing else "review"
    warnings = tuple(parameter_warnings)
    if missing:
        warnings = (*warnings, "Some axis labels require review.")
    return AxisCalibration(
        status=status,
        start_hz=start_hz,
        stop_hz=stop_hz,
        step_hz=step_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing,
        detected_parameter=detected_parameter,
        missing=missing,
        warnings=warnings,
    )


def _hue_name(degrees: float) -> str:
    if degrees < 15 or degrees >= 345:
        return "Red"
    if degrees < 45:
        return "Orange"
    if degrees < 75:
        return "Yellow"
    if degrees < 165:
        return "Green"
    if degrees < 200:
        return "Cyan"
    if degrees < 255:
        return "Blue"
    if degrees < 290:
        return "Purple"
    return "Magenta"


def _adaptive_color_masks(
    crop: NDArray[np.uint8],
) -> tuple[tuple[str, tuple[int, int, int], NDArray[np.bool_], NDArray[np.uint8]], ...]:
    """Cluster saturated plot pixels by observed hue without a fixed palette."""

    values = crop.astype(np.float32)
    maximum = values.max(axis=2)
    minimum = values.min(axis=2)
    delta = maximum - minimum
    saturation = np.divide(
        delta,
        maximum,
        out=np.zeros_like(delta),
        where=maximum > 0,
    )
    # Datasheet exports often anti-alias thin traces almost to grey.  A low
    # chroma floor still excludes neutral grids while retaining those pixels.
    valid = (delta >= 10) & (saturation >= 0.04)
    hue = np.zeros_like(maximum, dtype=np.float32)
    nonzero = delta > 0
    red = nonzero & (values[..., 0] == maximum)
    green = nonzero & (values[..., 1] == maximum) & ~red
    blue = nonzero & ~(red | green)
    hue[red] = np.mod((values[..., 1][red] - values[..., 2][red]) / delta[red], 6.0)
    hue[green] = (values[..., 2][green] - values[..., 0][green]) / delta[green] + 2.0
    hue[blue] = (values[..., 0][blue] - values[..., 1][blue]) / delta[blue] + 4.0
    hue = np.mod(hue * 60.0, 360.0)
    bin_count = 72
    hue_bins = np.floor(hue / (360.0 / bin_count)).astype(np.int16) % bin_count
    histogram = np.bincount(hue_bins[valid], minlength=bin_count).astype(np.float64)
    smoothed = histogram + 0.6 * (np.roll(histogram, 1) + np.roll(histogram, -1))
    minimum_support = max(20.0, crop.shape[1] * 0.10)
    candidates = [
        index
        for index in np.argsort(smoothed)[::-1]
        if smoothed[index] >= minimum_support
    ]
    peaks: list[int] = []
    for candidate in candidates:
        if all(
            min((candidate - peak) % bin_count, (peak - candidate) % bin_count) >= 8
            for peak in peaks
        ):
            peaks.append(int(candidate))
        if len(peaks) >= 8:
            break
    masks: list[tuple[str, tuple[int, int, int], NDArray[np.bool_], NDArray[np.uint8]]] = []
    chroma = np.clip(delta, 0, 255).astype(np.uint8)
    if not peaks:
        return ()
    nearest_peak = np.zeros(hue_bins.shape, dtype=np.int8)
    nearest_distance = np.full(hue_bins.shape, bin_count, dtype=np.int16)
    for peak_index, peak in enumerate(peaks):
        distance = np.minimum(
            (hue_bins - peak) % bin_count,
            (peak - hue_bins) % bin_count,
        )
        closer = distance < nearest_distance
        nearest_distance[closer] = distance[closer]
        nearest_peak[closer] = peak_index
    for peak_index, peak in enumerate(peaks):
        # Anti-aliased pixels can lie between two pale trace hues.  Assign each
        # pixel to one nearest cluster so two fallback traces cannot consume
        # the same raster evidence and collapse into one median path.
        mask = valid & (nearest_peak == peak_index) & (nearest_distance <= 6)
        if np.count_nonzero(mask) < minimum_support:
            continue
        representative = tuple(
            int(round(value)) for value in np.median(crop[mask], axis=0)
        )
        color_name = _hue_name(peak * 360.0 / bin_count)
        if color_name == "Blue" and max(representative) < 210:
            color_name = "Dark blue"
        elif color_name == "Blue":
            color_name = "Light blue"
        masks.append(
            (
                color_name,
                representative,
                mask,
                chroma,
            )
        )
    return tuple(masks)


def _chromatic_direction(rgb: Sequence[float]) -> NDArray[np.float64]:
    values = np.asarray(rgb, dtype=np.float64)
    chromatic = values - np.min(values)
    norm = float(np.linalg.norm(chromatic))
    return chromatic / norm if norm else chromatic


def _colour_identity_is_compatible(
    first_rgb: Sequence[float], second_rgb: Sequence[float]
) -> bool:
    """Keep antialias shades together without allowing a hue identity swap."""

    first = np.asarray(first_rgb, dtype=np.float64)
    second = np.asarray(second_rgb, dtype=np.float64)
    direction_distance = float(
        np.linalg.norm(_chromatic_direction(first) - _chromatic_direction(second))
    )
    first_saturation = float(
        (np.max(first) - np.min(first)) / max(np.max(first), 1.0)
    )
    second_saturation = float(
        (np.max(second) - np.min(second)) / max(np.max(second), 1.0)
    )
    direction_limit = (
        COLOR_DIRECTION_STRICT_DISTANCE
        if min(first_saturation, second_saturation)
        >= COLOR_SATURATION_STRICT_FLOOR
        else COLOR_DIRECTION_CLUSTER_DISTANCE
    )
    return direction_distance <= direction_limit


def _split_colour_subgroups(
    crop: NDArray[np.uint8],
    chroma: NDArray[np.float32],
    group: NDArray[np.int64],
    x_pixel: int,
) -> list[NDArray[np.int64]]:
    """Keep adjacent, visibly different trace colours as separate observations."""

    pixels = crop[group, x_pixel].astype(np.float64)
    chromatic = pixels - np.min(pixels, axis=1, keepdims=True)
    norms = np.linalg.norm(chromatic, axis=1, keepdims=True)
    signatures = np.divide(
        chromatic,
        norms,
        out=np.zeros_like(chromatic),
        where=norms > 0,
    )
    clusters: list[list[int]] = []
    centres: list[NDArray[np.float64]] = []
    rgb_centres: list[NDArray[np.float64]] = []
    weights = chroma[group, x_pixel].astype(np.float64)
    for local_index in np.argsort(weights)[::-1]:
        signature = signatures[local_index]
        pixel_rgb = pixels[local_index]
        pixel_saturation = float(
            (np.max(pixel_rgb) - np.min(pixel_rgb)) / max(np.max(pixel_rgb), 1.0)
        )
        compatible: list[tuple[int, float]] = []
        for index, (centre, rgb_centre) in enumerate(zip(centres, rgb_centres)):
            direction_distance = float(np.linalg.norm(signature - centre))
            centre_saturation = float(
                (np.max(rgb_centre) - np.min(rgb_centre))
                / max(np.max(rgb_centre), 1.0)
            )
            if (
                direction_distance <= COLOR_DIRECTION_CLUSTER_DISTANCE
                and (
                    direction_distance <= COLOR_DIRECTION_STRICT_DISTANCE
                    or min(pixel_saturation, centre_saturation)
                    < COLOR_SATURATION_STRICT_FLOOR
                )
            ):
                compatible.append((index, direction_distance))
        if compatible:
            cluster_index = min(compatible, key=lambda item: item[1])[0]
            clusters[cluster_index].append(int(local_index))
            members = np.asarray(clusters[cluster_index], dtype=np.int64)
            centre = np.average(
                signatures[members],
                axis=0,
                weights=np.maximum(weights[members], 1.0),
            )
            centre_norm = float(np.linalg.norm(centre))
            centres[cluster_index] = centre / centre_norm if centre_norm else centre
            rgb_centres[cluster_index] = np.average(
                pixels[members],
                axis=0,
                weights=np.maximum(weights[members], 1.0),
            )
        else:
            clusters.append([int(local_index)])
            centres.append(signature.copy())
            rgb_centres.append(pixel_rgb.copy())
    return [group[np.asarray(cluster, dtype=np.int64)] for cluster in clusters]


def _dilated_line_mask(flags: NDArray[np.bool_], radius: int) -> NDArray[np.bool_]:
    """Expand one-dimensional grid-line detections by a small raster radius."""

    expanded = flags.copy()
    for offset in range(1, radius + 1):
        expanded[offset:] |= flags[:-offset]
        expanded[:-offset] |= flags[offset:]
    return expanded


def _extract_achromatic_curves(
    rgb: NDArray[np.uint8],
    plot_box: tuple[int, int, int, int],
    *,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str,
    allow_sparse: bool = False,
) -> tuple[DigitizedCurve, ...]:
    """Recover neutral gray/black traces after suppressing neutral grid bands.

    Colour direction cannot distinguish a gray curve from a gray grid.  The
    useful distinction is geometric: grid and axis pixels form long straight
    rows or columns, while a plotted trace forms a horizontally continuous
    path.  Grid bands are therefore removed before the same continuity and
    coverage contract used for coloured traces is applied.
    """

    left, top, right, bottom = plot_box
    crop = rgb[top : bottom + 1, left : right + 1]
    height, width = crop.shape[:2]
    values = crop.astype(np.int16)
    maximum = values.max(axis=2)
    minimum = values.min(axis=2)
    neutral = (
        ((maximum - minimum) <= 5)
        & (maximum <= 235)
    )

    def repeated_neutral_lines(axis: int, line_length: int) -> NDArray[np.bool_]:
        """Find gray grid bands even where a coloured trace interrupts them."""

        hits = neutral.sum(axis=axis)
        lines = np.zeros(hits.shape, dtype=np.bool_)
        candidates = np.flatnonzero(
            hits >= max(12, round(line_length * 0.30))
        )
        if candidates.size < 3:
            return lines
        # Consecutive rows belong to ONE stroke, not three independent grid
        # lines. A long horizontal trace alone must survive this test.
        bands = np.split(candidates, np.flatnonzero(np.diff(candidates) > 2) + 1)
        if len(bands) < 3:
            return lines
        # Fit ONE dominant lattice to the already detected plot boundaries.
        # Unrelated triples can accidentally be equally spaced; accepting all
        # such triples would classify a flat data trace as another grid row.
        best = None
        for intervals in range(2, 17):
            step = (len(lines) - 1) / intervals
            if step < 6:
                continue
            expected = np.linspace(0, len(lines) - 1, intervals + 1)
            # A curve crossing a grid column can broaden its candidate band.
            # Use distance to the band, so that crossing cannot shift the grid
            # centre and leave a whole vertical grid stroke in the trace mask.
            lower = np.asarray([band[0] for band in bands])
            upper = np.asarray([band[-1] for band in bands])
            distances = np.maximum(np.maximum(lower[None, :] - expected[:, None], expected[:, None] - upper[None, :]), 0)
            tolerance = max(2, step * 0.025)
            nearest = distances.min(axis=1)
            matched = nearest <= tolerance
            if matched.sum() < 3 or matched.mean() < 0.70:
                continue
            # Three independent bands prove only the complete two-division
            # grid. Incomplete larger lattices with three chance matches do
            # not prove that an isolated horizontal trace is a grid line.
            if matched.sum() == 3 and (intervals != 2 or not matched.all()):
                continue
            score = (int(matched.sum()), float(matched.mean()), -float(nearest[matched].mean()))
            selected = np.flatnonzero(distances.min(axis=0) <= tolerance)
            if best is None or score > best[0]:
                best = (score, selected)
        if best is not None:
            for match in best[1]:
                lines[bands[match]] = True
        return lines

    # Suppress complete or periodically repeated grid/spine bands, including
    # their anti-aliased neighbours.
    grid_rows = repeated_neutral_lines(axis=1, line_length=width)
    grid_columns = repeated_neutral_lines(axis=0, line_length=height)
    usable = neutral.copy()
    # JPEG/resampled grid strokes contain many neutral edge shades. Suppress
    # those bands while retaining pixels substantially darker than their core;
    # black/dark-gray traces over pale grid lines keep their crossings. A pale
    # trace at a grid intersection is ambiguous and keeps an explicit gap.
    for axis, flags in ((1, grid_rows), (0, grid_columns)):
        indexes = np.flatnonzero(flags)
        bands = np.split(indexes, np.flatnonzero(np.diff(indexes) > 2) + 1) if indexes.size else []
        # Use the repeated bands' dark cores, not one pale antialias row. A
        # data curve can overwrite one grid band; the median over independent
        # bands prevents that one crossing from redefining the grid's shade.
        core_shades = []
        edge_shades = []
        for band in bands:
            samples = maximum[band, :] if axis == 1 else maximum[:, band]
            supported = neutral[band, :] if axis == 1 else neutral[:, band]
            core_shades.append(float(np.percentile(samples[supported], 10)))
            edge_shades.append(float(np.percentile(samples[supported], 90)))
        grid_core = float(np.median(core_shades)) if core_shades else 0
        grid_edge = float(np.median(edge_shades)) if edge_shades else 255
        dark_limit = grid_core * 0.55
        # For an unblended uniform grid a much lighter trace is distinguishable
        # too. Resampled/JPEG grids do not have that evidence; their pale edges
        # must remain suppressed rather than become additional gray traces.
        light_limit = grid_edge + 28 if grid_edge - grid_core <= 8 else 255
        for band in bands:
            start, stop = max(0, int(band[0]) - 2), min(len(flags), int(band[-1]) + 3)
            if axis == 1:
                usable[start:stop, :] &= (maximum[start:stop, :] < dark_limit) | (maximum[start:stop, :] > light_limit)
            else:
                usable[:, start:stop] &= (maximum[:, start:stop] < dark_limit) | (maximum[:, start:stop] > light_limit)
    border = max(2, round(min(height, width) * 0.004))
    usable[:border, :] = False
    usable[-border:, :] = False
    usable[:, :border] = False
    usable[:, -border:] = False

    # A dashed neutral curve can lose additional pixels where a dash crosses a
    # removed horizontal or vertical grid band.  Permit a wider *predicted*
    # continuation than for coloured solid traces; the vertical jump and
    # final coverage gates still reject unrelated fragments.
    maximum_gap = max(12, round(width * 0.08))
    row_group_gap = max(2, round(height * 0.008))

    tracks: list[dict[str, object]] = []

    def allowed_jump(gap: int) -> float:
        return min(
            height * 0.08,
            max(8.0, height * 0.035)
            + height * 0.01 * max(gap - 1, 0),
        )

    for x_pixel in range(width):
        rows = np.flatnonzero(usable[:, x_pixel])
        observations: list[tuple[float, int, int, float]] = []
        if rows.size:
            boundaries = np.flatnonzero(np.diff(rows) > row_group_gap) + 1
            for group in np.split(rows, boundaries):
                # Darker centre pixels carry more evidence than pale
                # antialiasing pixels, but all neutral shades remain eligible.
                weights = np.maximum(236 - maximum[group, x_pixel], 1.0)
                observations.append(
                    (
                        float(np.average(group, weights=weights)),
                        int(np.min(group)),
                        int(np.max(group)),
                        float(np.average(maximum[group, x_pixel], weights=weights)),
                    )
                )

        candidates: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(tracks):
            gap = x_pixel - int(track["last_x"])
            if gap <= 0 or gap > maximum_gap:
                continue
            recent_x = np.asarray(track["x"][-16:], dtype=np.float64)
            recent_y = np.asarray(track["y"][-16:], dtype=np.float64)
            predicted_y = float(track["last_y"])
            if recent_x.size >= 3 and recent_x[-1] > recent_x[0]:
                predicted_y += float(np.polyfit(recent_x, recent_y, 1)[0]) * gap
            expected_value = float(np.median(track["value"]))
            jump_limit = allowed_jump(gap)
            for observation_index, (
                center,
                row_min,
                row_max,
                observed_value,
            ) in enumerate(observations):
                distance = abs(center - predicted_y)
                row_gap = max(
                    row_min - int(track["last_row_max"]) - 1,
                    int(track["last_row_min"]) - row_max - 1,
                    0,
                )
                pixel_connected = gap == 1 and row_gap <= 1
                if distance <= jump_limit or pixel_connected:
                    candidates.append(
                        (
                            distance / jump_limit
                            + abs(observed_value - expected_value) / 80.0,
                            track_index,
                            observation_index,
                        )
                    )

        used_tracks: set[int] = set()
        used_observations: set[int] = set()
        for _score, track_index, observation_index in sorted(candidates):
            if track_index in used_tracks or observation_index in used_observations:
                continue
            center, row_min, row_max, observed_value = observations[observation_index]
            track = tracks[track_index]
            track["x"].append(x_pixel)
            track["y"].append(center)
            track["value"].append(observed_value)
            track["last_x"] = x_pixel
            track["last_y"] = center
            track["last_row_min"] = row_min
            track["last_row_max"] = row_max
            used_tracks.add(track_index)
            used_observations.add(observation_index)
        for observation_index, (
            center,
            row_min,
            row_max,
            observed_value,
        ) in enumerate(observations):
            if observation_index in used_observations:
                continue
            tracks.append(
                {
                    "x": [x_pixel],
                    "y": [center],
                    "value": [observed_value],
                    "last_x": x_pixel,
                    "last_y": center,
                    "last_row_min": row_min,
                    "last_row_max": row_max,
                }
            )

    minimum_samples = max(
        20,
        round(width * (0.25 if allow_sparse else MINIMUM_TRACE_COVERAGE)),
    )
    curves: list[DigitizedCurve] = []
    for track in tracks:
        if len(track["x"]) < minimum_samples:
            continue
        x_array = np.asarray(track["x"], dtype=np.float64)
        y_array = np.asarray(track["y"], dtype=np.float64)
        span = float(x_array[-1] - x_array[0] + 1)
        # A neutral trace may have a smaller specified bandwidth than the
        # coloured traces (for example 40 GHz in a 110 GHz plot). Require a
        # dense observed run anchored at the left boundary; text in an internal
        # legend cannot qualify merely by occupying many columns.
        left_anchored_partial = (
            allow_sparse and x_array[0] <= max(3, width * 0.02)
            and span >= width * 0.30 and x_array.size / span >= 0.85
        )
        if span < width * (0.45 if allow_sparse else 0.70) and not left_anchored_partial:
            continue
        normalized_x = x_array / max(width - 1, 1)
        if spacing == "log":
            frequency_hz = np.exp(
                np.log(start_hz)
                + normalized_x * (np.log(stop_hz) - np.log(start_hz))
            )
        else:
            frequency_hz = start_hz + normalized_x * (stop_hz - start_hz)
        magnitude_db = y_max_db - y_array / max(height - 1, 1) * (
            y_max_db - y_min_db
        )
        if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
            continue
        gray_value = int(round(float(np.median(track["value"]))))
        coverage = x_array.size / width
        curves.append(
            DigitizedCurve(
                color="Gray",
                rgb=(gray_value, gray_value, gray_value),
                frequency_hz=frequency_hz,
                magnitude_db=magnitude_db,
                pixel_points=np.column_stack((x_array + left, y_array + top)),
                confidence=float(min(0.92, coverage / 0.85)),
                observed_samples=int(frequency_hz.size),
                sample_provenance=("observed",) * int(frequency_hz.size),
            )
        )
    return tuple(curves)


def _repair_short_upward_annotation_runs(
    x_values: NDArray[np.float64],
    y_values: NDArray[np.float64],
    *,
    height: int,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Replace short same-colour annotation excursions by two-sided gaps.

    Product plots often print a coloured legend inside the plot rectangle.  A
    hue-wide fallback can otherwise alternate between the real lower trace and
    short text glyphs near the top.  Only short, internally bounded upward
    excursions are repaired; downward return-loss notches are left intact.
    """

    repaired = y_values.astype(np.float64, copy=True)
    interpolated = np.zeros(repaired.size, dtype=np.bool_)
    if repaired.size < 5 or MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION <= 0:
        return repaired, interpolated
    horizontal_gaps = np.diff(x_values)
    jump_limit = max(8.0, height * 0.035)
    boundaries = np.flatnonzero(
        (np.abs(np.diff(repaired)) > jump_limit) & (horizontal_gaps <= 3)
    ) + 1
    segments = np.split(np.arange(repaired.size, dtype=np.int64), boundaries)
    maximum_run = max(
        12,
        round(repaired.size * MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION),
    )
    minimum_excursion = max(30.0, height * 0.12)
    stable_neighbours = max(12.0, height * 0.05)

    for segment_index in range(1, len(segments) - 1):
        segment = segments[segment_index]
        if not segment.size or segment.size > maximum_run:
            continue
        start = int(segment[0])
        stop = int(segment[-1])
        if x_values[start] - x_values[start - 1] > 3 or x_values[stop + 1] - x_values[stop] > 3:
            continue
        before = float(repaired[start - 1])
        after = float(repaired[stop + 1])
        if abs(before - after) > stable_neighbours:
            continue
        expected = np.linspace(before, after, segment.size + 2)[1:-1]
        # Image rows grow downward, so text above the physical path has a
        # large positive expected-minus-observed displacement.
        if float(np.median(expected - repaired[segment])) < minimum_excursion:
            continue
        repaired[segment] = expected
        interpolated[segment] = True
    return repaired, interpolated


def _extract_curves(
    rgb: NDArray[np.uint8],
    plot_box: tuple[int, int, int, int],
    *,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str,
    allow_sparse: bool = False,
) -> tuple[DigitizedCurve, ...]:
    left, top, right, bottom = plot_box
    crop = rgb[top : bottom + 1, left : right + 1]
    width = crop.shape[1]
    height = crop.shape[0]
    values = crop.astype(np.float32)
    maximum = values.max(axis=2)
    minimum = values.min(axis=2)
    chroma = maximum - minimum
    saturation = np.divide(
        chroma,
        maximum,
        out=np.zeros_like(chroma),
        where=maximum > 0,
    )
    mask = (
        (chroma >= 10)
        & (saturation >= 0.04)
        & ((maximum < 235) | (saturation >= 0.20))
    )
    # A long coloured column can be a real narrow notch. Keep its two-dimensional
    # extent for connected tracking; total column occupancy is not grid evidence.

    tracks: list[dict[str, object]] = []
    maximum_gap = max(12, round(width * 0.05))
    row_group_gap = max(2, round(height * 0.008))

    # Dense separated glyph/legend groups are not one vertical stroke. Retain
    # the old annotation guard there, but never erase a single connected notch
    # merely because its vertical extent is large.
    for column in np.flatnonzero(mask.sum(axis=0) > max(24, round(height * 0.45))):
        occupied = np.flatnonzero(mask[:, column])
        groups = np.split(occupied, np.flatnonzero(np.diff(occupied) > row_group_gap) + 1)
        if len(groups) > 1:
            # Detached speckles must not make a connected tall lobe disappear.
            supported = [group for group in groups if group.size > max(24, round(height * 0.45))]
            mask[:, column] = False
            for group in supported:
                mask[group, column] = True

    def allowed_center_jump(gap: int) -> float:
        """Use one continuity threshold in primary and fallback tracking."""

        return min(
            height * 0.08,
            max(8.0, height * 0.035)
            + height * 0.01 * max(gap - 1, 0),
        )

    for x_pixel in range(width):
        rows = np.flatnonzero(mask[:, x_pixel])
        observations: list[tuple[float, tuple[int, int, int], int, int]] = []
        if rows.size:
            boundaries = np.flatnonzero(np.diff(rows) > row_group_gap) + 1
            for group in np.split(rows, boundaries):
                for colour_group in _split_colour_subgroups(
                    crop, chroma, group, x_pixel
                ):
                    weights = np.maximum(chroma[colour_group, x_pixel], 1.0)
                    center = float(np.average(colour_group, weights=weights))
                    representative = tuple(
                        int(round(value))
                        for value in np.median(crop[colour_group, x_pixel], axis=0)
                    )
                    observations.append(
                        (
                            center,
                            representative,
                            int(np.min(colour_group)),
                            int(np.max(colour_group)),
                        )
                    )
        candidates: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(tracks):
            gap = x_pixel - int(track["last_x"])
            if gap <= 0 or gap > maximum_gap:
                continue
            recent_x = np.asarray(track["x"][-16:], dtype=np.float64)
            recent_y = np.asarray(track["y"][-16:], dtype=np.float64)
            predicted_y = float(track["last_y"])
            if recent_x.size >= 3 and recent_x[-1] > recent_x[0]:
                slope = float(np.polyfit(recent_x, recent_y, 1)[0])
                predicted_y += slope * gap
            track_rgb = np.median(
                # Use the accumulated colour identity, not only the most recent
                # pixels.  A short anti-aliased overlap must not gradually
                # recolour a track and make two traces exchange identities.
                np.asarray(track["rgb"], dtype=np.float64), axis=0
            )
            # Missing antialias pixels may create a short horizontal gap, but a
            # large vertical teleport is not continuity. Keep the tolerance
            # bounded even at the largest permitted gap so separate same-colour
            # segments cannot be joined into a fabricated path.
            allowed_jump = allowed_center_jump(gap)
            for observation_index, (
                center,
                observed_rgb,
                row_min,
                row_max,
            ) in enumerate(observations):
                distance = abs(center - predicted_y)
                observed_values = np.asarray(observed_rgb, dtype=np.float64)
                color_distance = float(np.linalg.norm(observed_values - track_rgb))
                if not _colour_identity_is_compatible(track_rgb, observed_values):
                    continue
                if len(track["x"]) >= 4 and color_distance > 120.0:
                    continue
                last_row_min = int(track["last_row_min"])
                last_row_max = int(track["last_row_max"])
                row_gap = max(
                    row_min - last_row_max - 1,
                    last_row_min - row_max - 1,
                    0,
                )
                pixel_connected = gap == 1 and row_gap <= 1
                if distance <= allowed_jump or pixel_connected:
                    score = distance / allowed_jump + color_distance / 100.0
                    candidates.append((score, track_index, observation_index))
        used_tracks: set[int] = set()
        used_observations: set[int] = set()
        for _distance, track_index, observation_index in sorted(candidates):
            if track_index in used_tracks or observation_index in used_observations:
                continue
            center, observed_rgb, row_min, row_max = observations[observation_index]
            track = tracks[track_index]
            track["x"].append(x_pixel)
            track["y"].append(center)
            track["rgb"].append(observed_rgb)
            track["last_x"] = x_pixel
            track["last_y"] = center
            track["last_row_min"] = row_min
            track["last_row_max"] = row_max
            used_tracks.add(track_index)
            used_observations.add(observation_index)
        for observation_index, (
            center,
            observed_rgb,
            row_min,
            row_max,
        ) in enumerate(observations):
            if observation_index in used_observations:
                continue
            tracks.append(
                {
                    "x": [x_pixel],
                    "y": [center],
                    "rgb": [observed_rgb],
                    "last_x": x_pixel,
                    "last_y": center,
                    "last_row_min": row_min,
                    "last_row_max": row_max,
                }
            )

    minimum_trace_samples = max(
        20,
        round(width * (0.25 if allow_sparse else MINIMUM_TRACE_COVERAGE)),
    )

    def has_minimum_support(track: dict[str, object]) -> bool:
        x_values = cast(list[int], track["x"])
        if len(x_values) >= minimum_trace_samples:
            return True
        return (
            len(x_values) >= max(20, round(width * 0.30))
            and x_values[-1] - x_values[0] >= max(20, round((width - 1) * 0.45))
        )

    curves: list[DigitizedCurve] = []
    for track in tracks:
        x_values = track["x"]
        y_values = track["y"]
        if not has_minimum_support(track):
            continue
        x_array = np.asarray(x_values, dtype=np.float64)
        y_array = np.asarray(y_values, dtype=np.float64)
        representative_rgb = tuple(
            int(round(value))
            for value in np.median(np.asarray(track["rgb"], dtype=np.float64), axis=0)
        )
        red, green, blue = (value / 255.0 for value in representative_rgb)
        hue, saturation_value, value = colorsys.rgb_to_hsv(red, green, blue)
        name = "Gray"
        if saturation_value >= 0.02:
            name = _hue_name(hue * 360.0)
            if name == "Blue":
                name = "Dark blue" if value < 0.82 else "Light blue"
        normalized_x = x_array / max(width - 1, 1)
        if spacing == "log":
            frequency_hz = np.exp(
                np.log(start_hz)
                + normalized_x * (np.log(stop_hz) - np.log(start_hz))
            )
        else:
            frequency_hz = start_hz + normalized_x * (stop_hz - start_hz)
        magnitude_db = y_max_db - y_array / max(height - 1, 1) * (y_max_db - y_min_db)
        # Never splice a positive-gain interval out of the middle of a trace:
        # doing so would make later interpolation bridge data that never existed.
        # This tool models passive cable/fixture loss, so reject the whole track.
        if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
            continue
        pixel_points = np.column_stack((x_array + left, y_array + top))
        coverage = x_array.size / width
        curves.append(
            DigitizedCurve(
                color=name,
                rgb=representative_rgb,
                frequency_hz=frequency_hz,
                magnitude_db=magnitude_db,
                pixel_points=pixel_points,
                confidence=float(min(1.0, coverage / 0.8)),
                observed_samples=int(frequency_hz.size),
                sample_provenance=("observed",) * int(frequency_hz.size),
            )
        )

    # Deep, narrow return-loss notches can split one visible hue into many
    # short continuity tracks even though the hue is present across almost the
    # whole plot.  Recover only broad, observed hue masks that the primary
    # tracker did not already explain.  This is deliberately not a generic
    # segment join: a qualifying run must contain pixels in at least 55% of
    # plot columns, so legends and two short disconnected segments stay out.
    for color_name, representative_rgb, color_mask, color_chroma in _adaptive_color_masks(crop):
        column_counts = np.count_nonzero(color_mask, axis=0)
        usable = color_mask.copy()
        usable[:, column_counts > max(24, round(height * 0.45))] = False
        passive_row = int(
            np.floor(
                (y_max_db - PASSIVE_MAGNITUDE_TOLERANCE_DB)
                / (y_max_db - y_min_db)
                * max(height - 1, 1)
            )
        )
        usable[: max(0, passive_row), :] = False
        present_columns = np.flatnonzero(np.any(usable, axis=0))
        if not present_columns.size:
            continue
        # If this hue mask already supports one full track and one substantial
        # partial track, its column median has two possible identities.  Keep
        # both primary anchors intact for the joint association pass below.
        mask_supported_curves: list[DigitizedCurve] = []
        for existing in curves:
            supported_points = 0
            for x_value, y_value in existing.pixel_points:
                x_pixel = int(round(float(x_value) - left))
                y_pixel = int(round(float(y_value) - top))
                if not (0 <= x_pixel < width and 0 <= y_pixel < height):
                    continue
                if np.any(
                    usable[
                        max(0, y_pixel - 3) : min(height, y_pixel + 4),
                        max(0, x_pixel - 1) : min(width, x_pixel + 2),
                    ]
                ):
                    supported_points += 1
            if supported_points / max(existing.pixel_points.shape[0], 1) >= 0.70:
                mask_supported_curves.append(existing)
        supported_spans = [
            float(curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1)
            / width
            for curve in mask_supported_curves
        ]
        anchored_ambiguous_pair = (
            len(mask_supported_curves) == AMBIGUOUS_HUE_PAIR_SIZE
            and sum(span >= 0.90 for span in supported_spans) == 1
            and sum(
                MINIMUM_UNIQUE_HUE_PARTIAL_SPAN <= span < 0.75
                for span in supported_spans
            )
            == 1
        )
        if anchored_ambiguous_pair:
            continue
        boundaries = np.flatnonzero(np.diff(present_columns) > maximum_gap) + 1
        for run in np.split(present_columns, boundaries):
            if run.size < max(20, round(width * 0.55)):
                continue
            if run[0] > width * 0.05 or run[-1] < (width - 1) * 0.95:
                continue
            x_array = run.astype(np.float64)
            y_values: list[float] = []
            rgb_values: list[tuple[int, int, int]] = []
            for x_pixel in run:
                rows = np.flatnonzero(usable[:, x_pixel])
                weights = np.maximum(color_chroma[rows, x_pixel].astype(np.float64), 1.0)
                order = np.argsort(rows)
                ordered_rows = rows[order]
                cumulative = np.cumsum(weights[order])
                median_index = int(np.searchsorted(cumulative, cumulative[-1] / 2.0))
                y_values.append(float(ordered_rows[min(median_index, ordered_rows.size - 1)]))
                rgb_values.append(
                    tuple(
                        int(round(value))
                        for value in np.median(crop[rows, x_pixel], axis=0)
                    )
                )
            y_array = np.asarray(y_values, dtype=np.float64)
            if x_array.size >= 3:
                previous_expected = y_array[:-2]
                next_expected = y_array[2:]
                local_expected = (
                    previous_expected + next_expected
                ) / 2.0
                isolated_upward = (
                    y_array[1:-1]
                    < local_expected - max(12.0, height * 0.08)
                ) & (
                    np.abs(previous_expected - next_expected)
                    <= max(8.0, height * 0.04)
                )
                if np.any(isolated_upward):
                    keep = np.ones(x_array.size, dtype=np.bool_)
                    keep[1:-1] &= ~isolated_upward
                    x_array = x_array[keep]
                    y_array = y_array[keep]
                    rgb_values = [
                        rgb_value
                        for rgb_value, retained in zip(rgb_values, keep)
                        if retained
                    ]
            y_array, annotation_interpolated = _repair_short_upward_annotation_runs(
                x_array,
                y_array,
                height=height,
            )
            horizontal_gaps = np.diff(x_array).astype(np.int64)
            vertical_jumps = np.abs(np.diff(y_array))
            representative_values = np.asarray(representative_rgb, dtype=np.float64)
            representative_saturation = float(
                (np.max(representative_values) - np.min(representative_values))
                / max(np.max(representative_values), 1.0)
            )
            candidate_direction = _chromatic_direction(representative_rgb)
            same_hue_curves = [
                existing
                for existing in curves
                if np.linalg.norm(
                    candidate_direction - _chromatic_direction(existing.rgb)
                )
                <= 0.10
            ]
            has_one_partial_same_hue_curve = (
                len(same_hue_curves) == 1
                and width * MINIMUM_UNIQUE_HUE_PARTIAL_SPAN
                <= (
                    same_hue_curves[0].pixel_points[-1, 0]
                    - same_hue_curves[0].pixel_points[0, 0]
                    + 1
                )
                < width * 0.90
            )
            ambiguous_hue_columns = sum(
                np.count_nonzero(
                    np.diff(np.flatnonzero(usable[:, int(x_pixel)]))
                    > row_group_gap
                )
                > 0
                for x_pixel in run
            )
            unique_hue_path = (
                ambiguous_hue_columns / max(run.size, 1)
                <= MAX_UNIQUE_HUE_AMBIGUOUS_COLUMN_FRACTION
            )
            discontinuity_boundaries: list[int] = []
            for point_index in np.flatnonzero(
                vertical_jumps
                > np.asarray(
                    [allowed_center_jump(int(gap)) for gap in horizontal_gaps],
                    dtype=np.float64,
                )
            ):
                previous_x = int(x_array[point_index])
                next_x = int(x_array[point_index + 1])
                if next_x - previous_x != 1:
                    discontinuity_boundaries.append(int(point_index) + 1)
                    continue
                previous_rows = np.flatnonzero(usable[:, previous_x])
                next_rows = np.flatnonzero(usable[:, next_x])
                if (
                    previous_rows.size == 0
                    or next_rows.size == 0
                    or int(
                        np.min(
                            np.abs(
                                previous_rows[:, None]
                                - next_rows[None, :]
                            )
                        )
                    )
                    > 1
                ):
                    discontinuity_boundaries.append(int(point_index) + 1)
            unique_hue_completion = (
                unique_hue_path
                and has_one_partial_same_hue_curve
                and bool(discontinuity_boundaries)
                and all(
                    int(horizontal_gaps[boundary - 1])
                    <= MAX_UNIQUE_HUE_TRANSITION_GAP
                    for boundary in discontinuity_boundaries
                )
            )
            single_anchor_completion = (
                len(mask_supported_curves) == 1
                and len(supported_spans) == 1
                and MINIMUM_UNIQUE_HUE_PARTIAL_SPAN
                <= supported_spans[0]
                < 0.75
                and bool(discontinuity_boundaries)
                and ambiguous_hue_columns / max(run.size, 1)
                <= MAX_SINGLE_ANCHOR_HUE_AMBIGUOUS_COLUMN_FRACTION
                and all(
                    int(horizontal_gaps[boundary - 1])
                    <= MAX_UNIQUE_HUE_TRANSITION_GAP
                    for boundary in discontinuity_boundaries
                )
            )
            broad_observed_hue = (
                run.size >= round(width * 0.80)
                and representative_saturation >= 0.075
                # A large number of breaks is evidence against a coherent
                # path, not evidence for one.  Ambiguous hue masks are handled
                # later by an anchored multi-path association pass; taking a
                # column median here can hop between physical traces.
                and (unique_hue_completion or single_anchor_completion)
            )
            if discontinuity_boundaries and not broad_observed_hue:
                segments = np.split(
                    np.arange(x_array.size, dtype=np.int64),
                    discontinuity_boundaries,
                )
                longest = max(segments, key=lambda segment: segment.size)
                if longest.size < max(20, round(width * 0.55)):
                    continue
                x_array = x_array[longest]
                y_array = y_array[longest]
                annotation_interpolated = annotation_interpolated[longest]
                rgb_values = [rgb_values[int(index)] for index in longest]
            if not (unique_hue_completion or single_anchor_completion) and any(
                np.linalg.norm(
                    candidate_direction - _chromatic_direction(existing.rgb)
                )
                <= 0.10
                and (
                    existing.pixel_points[-1, 0]
                    - existing.pixel_points[0, 0]
                )
                >= width * 0.45
                for existing in curves
            ):
                # Existing continuity evidence remains stronger than a
                # hue-wide weighted median, which can jump where pale traces
                # cross. The only exception is one geometrically unique hue
                # completing exactly one partial same-hue track; it continues
                # to the overlap and length checks below.
                continue
            duplicate_indexes: list[int] = []
            candidate_values = np.asarray(representative_rgb, dtype=np.float64)
            candidate_saturation = float(
                (np.max(candidate_values) - np.min(candidate_values))
                / max(np.max(candidate_values), 1.0)
            )
            for existing_index, existing in enumerate(curves):
                existing_values = np.asarray(existing.rgb, dtype=np.float64)
                existing_saturation = float(
                    (np.max(existing_values) - np.min(existing_values))
                    / max(np.max(existing_values), 1.0)
                )
                direction_limit = (
                    0.30
                    if min(candidate_saturation, existing_saturation) < 0.24
                    else 0.24
                )
                if (
                    np.linalg.norm(
                        candidate_direction - _chromatic_direction(existing.rgb)
                    )
                    > direction_limit
                ):
                    continue
                existing_x = existing.pixel_points[:, 0] - left
                overlap_left = max(float(x_array[0]), float(existing_x[0]))
                overlap_right = min(float(x_array[-1]), float(existing_x[-1]))
                if overlap_right <= overlap_left:
                    continue
                sample_x = np.linspace(overlap_left, overlap_right, 64)
                candidate_y = np.interp(sample_x, x_array, y_array)
                existing_y = np.interp(
                    sample_x,
                    existing_x,
                    existing.pixel_points[:, 1] - top,
                )
                if float(np.median(np.abs(candidate_y - existing_y))) <= max(
                    4.0, height * 0.015
                ):
                    duplicate_indexes.append(existing_index)
            if duplicate_indexes:
                if len(duplicate_indexes) > 1:
                    continue
                longest_existing = max(
                    existing.frequency_hz.size
                    for index, existing in enumerate(curves)
                    if index in duplicate_indexes
                )
                if run.size <= longest_existing * 1.25:
                    continue
                curves = [
                    existing
                    for index, existing in enumerate(curves)
                    if index not in duplicate_indexes
                ]
            normalized_x = x_array / max(width - 1, 1)
            if spacing == "log":
                frequency_hz = np.exp(
                    np.log(start_hz)
                    + normalized_x * (np.log(stop_hz) - np.log(start_hz))
                )
            else:
                frequency_hz = start_hz + normalized_x * (stop_hz - start_hz)
            magnitude_db = y_max_db - y_array / max(height - 1, 1) * (
                y_max_db - y_min_db
            )
            if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
                continue
            observed_rgb = tuple(
                int(round(value))
                for value in np.median(np.asarray(rgb_values, dtype=np.float64), axis=0)
            )
            curves.append(
                DigitizedCurve(
                    color=color_name,
                    rgb=observed_rgb,
                    frequency_hz=frequency_hz,
                    magnitude_db=magnitude_db,
                    pixel_points=np.column_stack((x_array + left, y_array + top)),
                    confidence=float(min(0.85, run.size / width)),
                    observed_samples=int(
                        frequency_hz.size - np.count_nonzero(annotation_interpolated)
                    ),
                    interpolated_samples=int(
                        np.count_nonzero(annotation_interpolated)
                    ),
                    sample_provenance=tuple(
                        "interpolated" if repaired else "observed"
                        for repaired in annotation_interpolated
                    ),
                )
            )
    dense_curves = [
        curve
        for curve in curves
        if curve.frequency_hz.size
        / max(curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1, 1)
        >= 0.60
    ]
    filtered_curves: list[DigitizedCurve] = []
    for curve in curves:
        span = max(
            curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1,
            1,
        )
        density = curve.frequency_hz.size / span
        duplicate_sparse_track = False
        if density < 0.45:
            for dense in dense_curves:
                if dense is curve or np.linalg.norm(
                    _chromatic_direction(curve.rgb)
                    - _chromatic_direction(dense.rgb)
                ) > 0.10:
                    continue
                overlap_left = max(
                    float(curve.pixel_points[0, 0]),
                    float(dense.pixel_points[0, 0]),
                )
                overlap_right = min(
                    float(curve.pixel_points[-1, 0]),
                    float(dense.pixel_points[-1, 0]),
                )
                if overlap_right - overlap_left < width * 0.30:
                    continue
                sample_x = np.linspace(overlap_left, overlap_right, 64)
                separation = np.median(
                    np.abs(
                        np.interp(
                            sample_x,
                            curve.pixel_points[:, 0],
                            curve.pixel_points[:, 1],
                        )
                        - np.interp(
                            sample_x,
                            dense.pixel_points[:, 0],
                            dense.pixel_points[:, 1],
                        )
                    )
                )
                if separation <= max(4.0, height * 0.015):
                    duplicate_sparse_track = True
                    break
        if not duplicate_sparse_track:
            filtered_curves.append(curve)
    return tuple(
        sorted(
            filtered_curves,
            key=lambda curve: (
                float(np.median(curve.pixel_points[:, 1])),
                curve.color,
            ),
        )
    )


def _recover_anchored_ambiguous_hue_pairs(
    rgb: NDArray[np.uint8],
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
    *,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str,
) -> tuple[DigitizedCurve, ...]:
    """Complete one partial path when a broad hue contains two identities.

    Datasheet rasterisation can put a saturated blue insertion-loss trace and
    a pale blue-grey return-loss trace in the same hue cluster.  A per-column
    median is then undefined as a trace identity.  This pass is enabled only
    when the primary tracker already supplies exactly two independent anchors:
    one full-width path and one substantial partial path supported by the same
    raster mask.  A joint dynamic program keeps both identities through the
    ambiguous columns.  Without those anchors the digitizer stays partial.
    """

    if len(curves) < 2:
        return curves
    left, top, right, bottom = plot_box
    width = right - left + 1
    height = bottom - top + 1
    crop = rgb[top : bottom + 1, left : right + 1]
    completed = list(curves)

    def mask_support(curve: DigitizedCurve, mask: NDArray[np.bool_]) -> float:
        hits = 0
        for x_value, y_value in curve.pixel_points:
            x_pixel = int(round(float(x_value) - left))
            y_pixel = int(round(float(y_value) - top))
            if not (0 <= x_pixel < width and 0 <= y_pixel < height):
                continue
            if np.any(
                mask[
                    max(0, y_pixel - 3) : min(height, y_pixel + 4),
                    max(0, x_pixel - 1) : min(width, x_pixel + 2),
                ]
            ):
                hits += 1
        return hits / max(curve.pixel_points.shape[0], 1)

    for _name, _representative, color_mask, color_chroma in _adaptive_color_masks(
        crop
    ):
        column_counts = np.count_nonzero(color_mask, axis=0)
        usable = color_mask.copy()
        usable[:, column_counts > max(24, round(height * 0.45))] = False
        present = np.flatnonzero(np.any(usable, axis=0))
        if (
            present.size < round(width * 0.90)
            or present[0] > width * 0.03
            or present[-1] < (width - 1) * 0.97
        ):
            continue

        supported = [
            index
            for index, curve in enumerate(completed)
            if mask_support(curve, usable) >= 0.70
        ]
        if len(supported) != AMBIGUOUS_HUE_PAIR_SIZE:
            continue
        spans = [
            float(
                completed[index].pixel_points[-1, 0]
                - completed[index].pixel_points[0, 0]
                + 1
            )
            / width
            for index in supported
        ]
        full_positions = [index for index, span in enumerate(spans) if span >= 0.90]
        partial_positions = [
            index
            for index, span in enumerate(spans)
            if MINIMUM_UNIQUE_HUE_PARTIAL_SPAN <= span < 0.75
        ]
        if len(full_positions) != 1 or len(partial_positions) != 1:
            continue
        pair_indexes = (
            supported[full_positions[0]],
            supported[partial_positions[0]],
        )
        pair = [completed[index] for index in pair_indexes]
        if (
            np.linalg.norm(
                _chromatic_direction(pair[0].rgb)
                - _chromatic_direction(pair[1].rgb)
            )
            <= COLOR_DIRECTION_STRICT_DISTANCE
        ):
            # Near-identical low-saturation traces use the existing coupled
            # overlap tracker, which preserves shared-overlap provenance.
            continue

        row_group_gap = max(2, round(height * 0.008))
        observed_columns: list[list[_TraceObservation]] = []
        for x_pixel in range(width):
            rows = np.flatnonzero(usable[:, x_pixel])
            boundaries = (
                np.flatnonzero(np.diff(rows) > row_group_gap) + 1
                if rows.size
                else ()
            )
            observations: list[_TraceObservation] = []
            for group in np.split(rows, boundaries) if rows.size else ():
                weights = np.maximum(
                    color_chroma[group, x_pixel].astype(np.float64), 1.0
                )
                observations.append(
                    _TraceObservation(
                        center=float(np.average(group, weights=weights)),
                        rgb=np.median(crop[group, x_pixel], axis=0).astype(
                            np.float64
                        ),
                    )
                )
            observed_columns.append(observations)
        if any(
            len(column) > MAX_COUPLED_OBSERVATIONS_PER_COLUMN
            for column in observed_columns
        ):
            continue
        columns = _fill_short_observation_gaps(
            observed_columns,
            maximum_gap=max(3, round(width * 0.008)),
        )
        if columns is None:
            continue

        anchors = [
            {
                int(round(float(x_value) - left)): float(y_value) - top
                for x_value, y_value in curve.pixel_points
                if 0 <= int(round(float(x_value) - left)) < width
            }
            for curve in pair
        ]
        prototypes = [np.asarray(curve.rgb, dtype=np.float64) for curve in pair]
        costs: list[dict[tuple[int, int], float]] = []
        parents: list[dict[tuple[int, int], tuple[int, int] | None]] = []
        for x_pixel, column in enumerate(columns):
            states = [
                (first, second)
                for first in range(len(column))
                for second in range(len(column))
            ]
            current_costs: dict[tuple[int, int], float] = {}
            current_parents: dict[
                tuple[int, int], tuple[int, int] | None
            ] = {}
            for state in states:
                emission = 0.0
                for trace_index, observation_index in enumerate(state):
                    observation = column[observation_index]
                    emission += float(
                        np.linalg.norm(observation.rgb - prototypes[trace_index])
                    ) / 60.0
                    anchor = anchors[trace_index].get(x_pixel)
                    if anchor is not None:
                        emission += abs(observation.center - anchor)
                if state[0] == state[1] and len(column) > 1:
                    emission += 12.0
                if x_pixel == 0:
                    current_costs[state] = emission
                    current_parents[state] = None
                    continue
                best_parent: tuple[int, int] | None = None
                best_cost = float("inf")
                for previous_state, previous_cost in costs[-1].items():
                    transition = 0.0
                    for trace_index in range(2):
                        delta = abs(
                            column[state[trace_index]].center
                            - columns[x_pixel - 1][
                                previous_state[trace_index]
                            ].center
                        )
                        transition += (
                            delta / 7.0
                            if delta <= 14.0
                            else 2.0 + (delta - 14.0) / 2.5
                        )
                    candidate = previous_cost + transition + emission
                    if candidate < best_cost:
                        best_cost = candidate
                        best_parent = previous_state
                current_costs[state] = best_cost
                current_parents[state] = best_parent
            costs.append(current_costs)
            parents.append(current_parents)
        if not costs or not costs[-1]:
            continue
        state = min(costs[-1], key=costs[-1].get)
        path = [state]
        for x_pixel in range(width - 1, 0, -1):
            parent = parents[x_pixel][path[-1]]
            if parent is None:
                path = []
                break
            path.append(parent)
        if not path:
            continue
        path.reverse()

        anchor_tolerance = max(4.0, height * 0.015)
        recovered_pair: list[DigitizedCurve] = []
        common_x = np.arange(left, right + 1, dtype=np.float64)
        normalized_x = (common_x - left) / max(right - left, 1)
        if spacing == "log":
            common_frequency = np.exp(
                np.log(start_hz)
                + normalized_x * (np.log(stop_hz) - np.log(start_hz))
            )
        else:
            common_frequency = start_hz + normalized_x * (stop_hz - start_hz)
        valid_pair = True
        for trace_index, curve in enumerate(pair):
            selected = [
                columns[x_pixel][path[x_pixel][trace_index]]
                for x_pixel in range(width)
            ]
            anchor_errors = [
                abs(selected[x_pixel].center - anchor)
                for x_pixel, anchor in anchors[trace_index].items()
            ]
            if anchor_errors and float(np.quantile(anchor_errors, 0.95)) > anchor_tolerance:
                valid_pair = False
                break
            y_relative = np.asarray(
                [observation.center for observation in selected],
                dtype=np.float64,
            )
            for x_pixel, anchor in anchors[trace_index].items():
                y_relative[x_pixel] = anchor
            magnitude_db = y_max_db - y_relative / max(height - 1, 1) * (
                y_max_db - y_min_db
            )
            if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
                valid_pair = False
                break
            provenance = tuple(
                (
                    "shared_overlap"
                    if observation.observed
                    and path[x_pixel][0] == path[x_pixel][1]
                    else "observed"
                    if observation.observed
                    else "interpolated"
                )
                for x_pixel, observation in enumerate(selected)
            )
            recovered_pair.append(
                DigitizedCurve(
                    color=curve.color,
                    rgb=curve.rgb,
                    frequency_hz=common_frequency.copy(),
                    magnitude_db=magnitude_db,
                    pixel_points=np.column_stack((common_x, y_relative + top)),
                    confidence=float(min(curve.confidence, 0.85)),
                    observed_samples=provenance.count("observed"),
                    shared_overlap_samples=provenance.count("shared_overlap"),
                    interpolated_samples=provenance.count("interpolated"),
                    sample_provenance=provenance,
                )
            )
        if not valid_pair or len(recovered_pair) != 2:
            continue
        recovered_pair = list(
            _repair_short_shared_identity_excursions(
                tuple(recovered_pair),
                top=top,
                height=height,
                y_min_db=y_min_db,
                y_max_db=y_max_db,
            )
        )
        separation = np.abs(
            recovered_pair[0].pixel_points[:, 1]
            - recovered_pair[1].pixel_points[:, 1]
        )
        if float(np.median(separation)) < max(4.0, height * 0.015):
            continue
        for output_index, curve_index in enumerate(pair_indexes):
            completed[curve_index] = recovered_pair[output_index]

    return tuple(completed)


def _repair_short_shared_identity_excursions(
    pair: tuple[DigitizedCurve, DigitizedCurve],
    *,
    top: int,
    height: int,
    y_min_db: float,
    y_max_db: float,
) -> tuple[DigitizedCurve, DigitizedCurve]:
    """Turn a short borrowed observation into an explicit interpolated gap.

    A broad colour mask can contain two physical traces.  When one trace has
    no usable pixels for one or two columns, the joint tracker previously kept
    both paths full-width by assigning both identities to the only remaining
    observation.  That is valid at a real crossing, but not when one path
    teleports to the other and immediately returns.  Compare each shared run
    with its own two-sided continuation: only the identity with a large local
    excursion is repaired, while genuine crossings and steep notches remain
    untouched.
    """

    first, second = pair
    if MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION <= 0 or (
        first.pixel_points.shape != second.pixel_points.shape
        or first.pixel_points.shape[0] < 3
        or not np.allclose(
            first.pixel_points[:, 0], second.pixel_points[:, 0], rtol=0, atol=1e-6
        )
    ):
        return pair

    y_values = [
        first.pixel_points[:, 1].astype(np.float64, copy=True),
        second.pixel_points[:, 1].astype(np.float64, copy=True),
    ]
    provenance = [
        list(first.sample_provenance),
        list(second.sample_provenance),
    ]
    shared = np.abs(y_values[0] - y_values[1]) <= max(3.0, height * 0.0045)
    starts = np.flatnonzero(shared & np.r_[True, ~shared[:-1]])
    stops = np.flatnonzero(shared & np.r_[~shared[1:], True])
    maximum_run = max(
        2,
        round(
            first.pixel_points.shape[0]
            * MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION
        ),
    )
    stable_error = max(6.0, height * 0.015)
    identity_excursion = max(18.0, height * 0.04)

    for start, stop in zip(starts, stops):
        run_size = int(stop - start + 1)
        if start == 0 or stop >= shared.size - 1 or run_size > maximum_run:
            continue
        expected = [
            np.linspace(values[start - 1], values[stop + 1], run_size + 2)[1:-1]
            for values in y_values
        ]
        errors = [
            float(np.max(np.abs(values[start : stop + 1] - predicted)))
            for values, predicted in zip(y_values, expected)
        ]
        stable = [error <= stable_error for error in errors]
        escaped = [error >= identity_excursion for error in errors]
        if stable[0] and escaped[1]:
            repair_index = 1
        elif stable[1] and escaped[0]:
            repair_index = 0
        else:
            continue
        y_values[repair_index][start : stop + 1] = expected[repair_index]
        provenance[repair_index][start : stop + 1] = ["interpolated"] * run_size

    repaired: list[DigitizedCurve] = []
    for curve, curve_y, curve_provenance in zip(pair, y_values, provenance):
        magnitude_db = y_max_db - (curve_y - top) / max(height - 1, 1) * (
            y_max_db - y_min_db
        )
        points = curve.pixel_points.copy()
        points[:, 1] = curve_y
        repaired.append(
            DigitizedCurve(
                color=curve.color,
                rgb=curve.rgb,
                frequency_hz=curve.frequency_hz.copy(),
                magnitude_db=magnitude_db,
                pixel_points=points,
                confidence=curve.confidence,
                observed_samples=curve_provenance.count("observed"),
                shared_overlap_samples=curve_provenance.count("shared_overlap"),
                interpolated_samples=curve_provenance.count("interpolated"),
                sample_provenance=tuple(curve_provenance),
            )
        )
    return cast(tuple[DigitizedCurve, DigitizedCurve], tuple(repaired))


def _coupled_trace_observations(
    rgb: NDArray[np.uint8],
    plot_box: tuple[int, int, int, int],
) -> list[list[_TraceObservation]]:
    """Return coloured row clusters for every horizontal plot pixel.

    This intentionally uses the same chroma and colour-direction contract as
    the primary tracker.  It is a second association pass, not a looser colour
    detector, so annotations rejected by the normal path do not suddenly
    become valid trace evidence.
    """

    left, top, right, bottom = plot_box
    crop = rgb[top : bottom + 1, left : right + 1]
    height, width = crop.shape[:2]
    values = crop.astype(np.float32)
    maximum = values.max(axis=2)
    minimum = values.min(axis=2)
    chroma = maximum - minimum
    saturation = np.divide(
        chroma,
        maximum,
        out=np.zeros_like(chroma),
        where=maximum > 0,
    )
    mask = (
        (chroma >= 10)
        & (saturation >= 0.04)
        & ((maximum < 235) | (saturation >= 0.20))
    )
    vertical_count = mask.sum(axis=0)
    mask[:, vertical_count > max(24, round(height * 0.45))] = False
    row_group_gap = max(2, round(height * 0.008))

    columns: list[list[_TraceObservation]] = []
    for x_pixel in range(width):
        rows = np.flatnonzero(mask[:, x_pixel])
        observations: list[_TraceObservation] = []
        if rows.size:
            boundaries = np.flatnonzero(np.diff(rows) > row_group_gap) + 1
            for group in np.split(rows, boundaries):
                for colour_group in _split_colour_subgroups(
                    crop, chroma, group, x_pixel
                ):
                    weights = np.maximum(chroma[colour_group, x_pixel], 1.0)
                    observations.append(
                        _TraceObservation(
                            center=float(
                                np.average(colour_group, weights=weights)
                            ),
                            rgb=np.median(
                                crop[colour_group, x_pixel], axis=0
                            ).astype(np.float64),
                        )
                    )
        columns.append(observations)
    return columns


def _fill_short_observation_gaps(
    columns: list[list[_TraceObservation]],
    *,
    maximum_gap: int,
) -> list[list[_TraceObservation]] | None:
    """Bridge only short raster holes using all boundary pairings.

    Keeping every left/right pairing lets the later dynamic program decide
    which continuation is physically smoother.  A long or edge gap has no
    two-sided evidence and therefore fails closed.
    """

    completed = [list(column) for column in columns]
    index = 0
    while index < len(completed):
        if completed[index]:
            index += 1
            continue
        start = index
        while index < len(completed) and not completed[index]:
            index += 1
        stop = index
        gap = stop - start
        if start == 0 or stop == len(completed) or gap > maximum_gap:
            return None
        before = completed[start - 1]
        after = completed[stop]
        if len(before) * len(after) > MAX_COUPLED_INTERPOLATION_PAIRINGS:
            return None
        for offset in range(gap):
            fraction = (offset + 1) / (gap + 1)
            completed[start + offset] = [
                _TraceObservation(
                    center=(1.0 - fraction) * left.center
                    + fraction * right.center,
                    rgb=(1.0 - fraction) * left.rgb + fraction * right.rgb,
                    observed=False,
                )
                for left in before
                for right in after
            ]
    return completed


def _has_reappearing_identity_evidence(
    columns: list[list[_TraceObservation]],
    prototypes: Sequence[NDArray[np.float64]],
) -> bool:
    """Return true when two visual identities separate in two disjoint runs.

    Parameter text is semantic metadata, not geometric evidence.  For an
    unlabelled plot we can still recover an *internal* shared overlap when both
    trace colours are independently visible before and after that overlap.
    A trace that appears only once has no such evidence and remains partial.
    """

    if len(prototypes) != 2 or not columns:
        return False
    minimum_run = max(8, round(len(columns) * 0.025))
    minimum_separation = max(6, round(len(columns) * 0.04))
    for trace_index, prototype in enumerate(prototypes):
        other = prototypes[1 - trace_index]
        distinctive_columns: list[int] = []
        for x_pixel, column in enumerate(columns):
            if len(column) < 2:
                continue
            distances = np.asarray(
                [np.linalg.norm(observation.rgb - prototype) for observation in column],
                dtype=np.float64,
            )
            best_index = int(np.argmin(distances))
            other_distance = float(
                np.linalg.norm(column[best_index].rgb - other)
            )
            if other_distance - float(distances[best_index]) >= 8.0:
                distinctive_columns.append(x_pixel)
        if not distinctive_columns:
            return False
        positions = np.asarray(distinctive_columns, dtype=np.int64)
        boundaries = np.flatnonzero(np.diff(positions) > 3) + 1
        runs = [run for run in np.split(positions, boundaries) if run.size >= minimum_run]
        if len(runs) < 2:
            return False
        if not any(
            int(right[0] - left[-1]) >= minimum_separation
            for left, right in zip(runs, runs[1:])
        ):
            return False
    return True


def _complete_repeated_overlaps(
    rgb: NDArray[np.uint8],
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
    *,
    parameter: str | None,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str,
) -> tuple[DigitizedCurve, ...]:
    """Jointly associate two same-parameter traces on one horizontal grid.

    A single raster cluster may legitimately represent two traces while they
    overlap.  The state space therefore permits both paths to use the same
    observation, while anchored visible pixels, colour fit and continuity keep
    their identities when the traces separate again.  A parameter label allows
    the established labelled workflow; without one, two disjoint runs of
    independently visible colour identity are required.
    """

    if len(curves) != 2:
        return curves
    normalized_parameter = None
    if parameter is not None:
        normalized_parameter, _warnings = detect_parameter_text(parameter)
    left, top, right, bottom = plot_box
    width = right - left + 1
    height = bottom - top + 1
    edge_tolerance = max(3.0, (right - left) * 0.02)
    if (
        min(float(curve.pixel_points[0, 0]) for curve in curves)
        > left + edge_tolerance
        or max(float(curve.pixel_points[-1, 0]) for curve in curves)
        < right - edge_tolerance
    ):
        return curves
    overlap_left = max(float(curve.pixel_points[0, 0]) for curve in curves)
    overlap_right = min(float(curve.pixel_points[-1, 0]) for curve in curves)
    if overlap_right - overlap_left < max(12.0, (right - left) * 0.15):
        return curves
    if all(
        curve.frequency_hz.size == width
        and abs(float(curve.pixel_points[0, 0]) - left) <= 1.0
        and abs(float(curve.pixel_points[-1, 0]) - right) <= 1.0
        for curve in curves
    ):
        return curves

    observed_columns = _coupled_trace_observations(rgb, plot_box)
    if any(
        len(column) > MAX_COUPLED_OBSERVATIONS_PER_COLUMN
        for column in observed_columns
    ):
        return curves
    prototypes = [np.asarray(curve.rgb, dtype=np.float64) for curve in curves]
    if normalized_parameter is None and not _has_reappearing_identity_evidence(
        observed_columns, prototypes
    ):
        return curves
    columns = _fill_short_observation_gaps(
        observed_columns,
        maximum_gap=max(3, round(width * 0.008)),
    )
    if columns is None:
        return curves
    anchors: list[dict[int, float]] = []
    for curve in curves:
        anchors.append(
            {
                int(round(x - left)): float(y - top)
                for x, y in curve.pixel_points
                if 0 <= int(round(x - left)) < width
            }
        )

    costs: list[dict[tuple[int, int], float]] = []
    parents: list[dict[tuple[int, int], tuple[int, int] | None]] = []
    for x_pixel, column in enumerate(columns):
        states = [
            (first, second)
            for first in range(len(column))
            for second in range(len(column))
        ]
        current_costs: dict[tuple[int, int], float] = {}
        current_parents: dict[tuple[int, int], tuple[int, int] | None] = {}
        for state in states:
            emission = 0.0
            for trace_index, observation_index in enumerate(state):
                observation = column[observation_index]
                emission += float(
                    np.linalg.norm(observation.rgb - prototypes[trace_index])
                ) / 90.0
                anchor = anchors[trace_index].get(x_pixel)
                if anchor is not None:
                    emission += abs(observation.center - anchor) / 1.5
            if state[0] == state[1]:
                emission += 0.0 if len(column) == 1 else 2.5
            elif abs(column[state[0]].center - column[state[1]].center) < 1.0:
                emission += 0.25
            if x_pixel == 0:
                current_costs[state] = emission
                current_parents[state] = None
                continue
            best_parent: tuple[int, int] | None = None
            best_cost = float("inf")
            for previous_state, previous_cost in costs[-1].items():
                transition = 0.0
                for trace_index in range(2):
                    delta = abs(
                        column[state[trace_index]].center
                        - columns[x_pixel - 1][
                            previous_state[trace_index]
                        ].center
                    )
                    transition += (
                        delta / 7.0
                        if delta <= 14.0
                        else 2.0 + (delta - 14.0) / 2.5
                    )
                candidate_cost = previous_cost + transition + emission
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_parent = previous_state
            current_costs[state] = best_cost
            current_parents[state] = best_parent
        costs.append(current_costs)
        parents.append(current_parents)

    state = min(costs[-1], key=costs[-1].get)
    path = [state]
    for x_pixel in range(width - 1, 0, -1):
        parent = parents[x_pixel][path[-1]]
        if parent is None:
            return curves
        path.append(parent)
    path.reverse()
    join_tolerance = max(4.0, height * 0.015)
    for trace_index in range(2):
        anchor_errors = [
            abs(columns[x][path[x][trace_index]].center - anchor)
            for x, anchor in anchors[trace_index].items()
        ]
        if anchor_errors and float(np.quantile(anchor_errors, 0.95)) > join_tolerance:
            return curves

    common_x = np.arange(left, right + 1, dtype=np.float64)
    normalized_x = (common_x - left) / max(right - left, 1)
    if spacing == "log":
        common_frequency = np.exp(
            np.log(start_hz)
            + normalized_x * (np.log(stop_hz) - np.log(start_hz))
        )
    else:
        common_frequency = start_hz + normalized_x * (stop_hz - start_hz)
    completed: list[DigitizedCurve] = []
    for trace_index, curve in enumerate(curves):
        y_relative: list[float] = []
        provenance: list[str] = []
        for x_pixel, selected_state in enumerate(path):
            first_index, second_index = selected_state
            selected = columns[x_pixel][selected_state[trace_index]]
            if first_index == second_index:
                available_anchors = [
                    anchors[index][x_pixel]
                    for index in range(2)
                    if x_pixel in anchors[index]
                ]
                if (
                    len(available_anchors) == 2
                    and abs(available_anchors[0] - available_anchors[1])
                    > join_tolerance
                ):
                    return curves
                y_relative.append(
                    float(np.mean(available_anchors))
                    if available_anchors
                    else selected.center
                )
                provenance.append(
                    "shared_overlap" if selected.observed else "interpolated"
                )
                continue
            anchor = anchors[trace_index].get(x_pixel)
            y_relative.append(anchor if anchor is not None else selected.center)
            provenance.append("observed" if selected.observed else "interpolated")
        y_array = np.asarray(y_relative, dtype=np.float64)
        magnitude_db = y_max_db - y_array / max(bottom - top, 1) * (
            y_max_db - y_min_db
        )
        if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
            return curves
        observed_samples = provenance.count("observed")
        shared_samples = provenance.count("shared_overlap")
        interpolated_samples = provenance.count("interpolated")
        completed.append(
            DigitizedCurve(
                color=curve.color,
                rgb=curve.rgb,
                frequency_hz=common_frequency.copy(),
                magnitude_db=magnitude_db,
                pixel_points=np.column_stack((common_x, y_array + top)),
                # Additional classified pixels and shared overlap never raise
                # confidence above the original visible-track estimate.
                confidence=curve.confidence,
                observed_samples=observed_samples,
                shared_overlap_samples=shared_samples,
                interpolated_samples=interpolated_samples,
                sample_provenance=tuple(provenance),
            )
        )
    return tuple(completed)


def _complete_occluded_prefixes(
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
    *,
    parameter: str | None,
    start_hz: float,
    stop_hz: float,
    spacing: str,
) -> tuple[DigitizedCurve, ...]:
    """Copy a unique donor prefix when a same-parameter trace was occluded.

    A raster cannot identify the hidden colour directly.  Completion is only
    enabled after one unambiguous parameter label has been read or confirmed,
    and only when the visible companion joins one full-width donor smoothly
    before measurably separating from it.  The donor horizontal samples become
    the common grid; non-observed points remain explicitly labelled.
    """

    if parameter is None or len(curves) < 2:
        return curves
    normalized_parameter, _warnings = detect_parameter_text(parameter)
    if normalized_parameter is None:
        return curves
    left, top, right, bottom = plot_box
    width = max(right - left, 1)
    height = max(bottom - top, 1)
    edge_tolerance = max(3.0, width * 0.02)
    join_tolerance = max(4.0, height * 0.015)
    minimum_interior_start = left + max(10.0, width * 0.08)
    completed = list(curves)

    for partial_index, partial in enumerate(curves):
        partial_x = partial.pixel_points[:, 0]
        partial_y = partial.pixel_points[:, 1]
        if (
            partial_x[0] < minimum_interior_start
            or partial_x[-1] < right - edge_tolerance
        ):
            continue
        donors: list[tuple[int, DigitizedCurve]] = []
        for donor_index, donor in enumerate(curves):
            if donor_index == partial_index:
                continue
            donor_x = donor.pixel_points[:, 0]
            donor_y = donor.pixel_points[:, 1]
            if (
                donor_x[0] > left + edge_tolerance
                or abs(float(donor_x[-1] - partial_x[-1])) > 1.0
            ):
                continue
            overlap_right = min(float(donor_x[-1]), float(partial_x[-1]))
            join_right = min(
                overlap_right,
                float(partial_x[0] + max(12.0, width * 0.04)),
            )
            if join_right <= partial_x[0]:
                continue
            join_x = np.linspace(float(partial_x[0]), join_right, 16)
            join_distance = np.abs(
                np.interp(join_x, partial_x, partial_y)
                - np.interp(join_x, donor_x, donor_y)
            )
            if float(np.median(join_distance)) > join_tolerance:
                continue
            comparison_x = np.linspace(float(partial_x[0]), overlap_right, 64)
            separation = np.abs(
                np.interp(comparison_x, partial_x, partial_y)
                - np.interp(comparison_x, donor_x, donor_y)
            )
            if float(np.quantile(separation, 0.8)) <= join_tolerance:
                continue
            donors.append((donor_index, donor))
        if len(donors) != 1:
            continue

        _donor_index, donor = donors[0]
        donor_x = donor.pixel_points[:, 0]
        donor_y = donor.pixel_points[:, 1]
        common_x = np.arange(
            int(np.ceil(donor_x[0])),
            int(np.floor(donor_x[-1])) + 1,
            dtype=np.float64,
        )
        normalized_x = (common_x - left) / width
        if spacing == "log":
            common_frequency = np.exp(
                np.log(start_hz)
                + normalized_x * (np.log(stop_hz) - np.log(start_hz))
            )
        else:
            common_frequency = start_hz + normalized_x * (stop_hz - start_hz)
        donor_observed_mask = np.isin(
            np.rint(common_x).astype(np.int64),
            np.rint(donor_x).astype(np.int64),
        )
        donor_interpolated_mask = ~donor_observed_mask
        common_donor_magnitude = np.interp(
            common_x,
            donor_x,
            donor.magnitude_db,
        )
        common_donor_y = np.interp(common_x, donor_x, donor_y)
        completed[_donor_index] = DigitizedCurve(
            color=donor.color,
            rgb=donor.rgb,
            frequency_hz=common_frequency.copy(),
            magnitude_db=common_donor_magnitude,
            pixel_points=np.column_stack((common_x, common_donor_y)),
            confidence=donor.confidence,
            observed_samples=int(np.count_nonzero(donor_observed_mask)),
            interpolated_samples=int(np.count_nonzero(donor_interpolated_mask)),
            sample_provenance=tuple(
                "observed" if observed else "interpolated"
                for observed in donor_observed_mask
            ),
        )
        prefix_mask = common_x < partial_x[0]
        observed_x = np.rint(partial_x).astype(np.int64)
        common_x_integer = np.rint(common_x).astype(np.int64)
        observed_mask = np.isin(common_x_integer, observed_x) & ~prefix_mask
        within_visible = ~prefix_mask
        interpolated_mask = within_visible & ~observed_mask

        common_magnitude = np.interp(
            common_x,
            partial_x,
            partial.magnitude_db,
        )
        common_y = np.interp(common_x, partial_x, partial_y)
        common_magnitude[prefix_mask] = common_donor_magnitude[prefix_mask]
        common_y[prefix_mask] = common_donor_y[prefix_mask]
        provenance = tuple(
            "shared_overlap"
            if shared
            else "observed"
            if observed
            else "interpolated"
            for shared, observed in zip(prefix_mask, observed_mask)
        )
        completed[partial_index] = DigitizedCurve(
            color=partial.color,
            rgb=partial.rgb,
            frequency_hz=common_frequency.copy(),
            magnitude_db=common_magnitude,
            pixel_points=np.column_stack((common_x, common_y)),
            # Confidence remains based on the original visible pixels. Copied
            # or interpolated samples must never improve it.
            confidence=partial.confidence,
            observed_samples=int(np.count_nonzero(observed_mask)),
            shared_overlap_samples=int(np.count_nonzero(prefix_mask)),
            interpolated_samples=int(np.count_nonzero(interpolated_mask)),
            sample_provenance=provenance,
        )
    return tuple(completed)


def _merge_sparse_same_colour_fragments(
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
) -> tuple[DigitizedCurve, ...]:
    """Join disjoint evidence for one labelled companion before gap recovery.

    The merge is intentionally unavailable without an unambiguous parameter
    label.  It only combines same-colour fragments that are individually below
    normal coverage, do not overlap horizontally, and jointly exceed it.
    Missing columns remain missing; the coupled tracker decides separately
    whether a short, two-sided gap can be interpolated.
    """

    if len(curves) < 3:
        return curves
    left, _top, right, _bottom = plot_box
    width = right - left + 1
    sparse_indexes = [
        index
        for index, curve in enumerate(curves)
        if curve.frequency_hz.size < width * MINIMUM_TRACE_COVERAGE
    ]
    used: set[int] = set()
    merged: list[DigitizedCurve] = []
    for seed_index in sparse_indexes:
        if seed_index in used:
            continue
        seed = curves[seed_index]
        group = [seed_index]
        for candidate_index in sparse_indexes:
            if candidate_index == seed_index or candidate_index in used:
                continue
            candidate = curves[candidate_index]
            if np.linalg.norm(
                _chromatic_direction(seed.rgb)
                - _chromatic_direction(candidate.rgb)
            ) > 0.10 or np.linalg.norm(
                np.asarray(seed.rgb, dtype=np.float64)
                - np.asarray(candidate.rgb, dtype=np.float64)
            ) > 45.0:
                continue
            intervals = [
                (
                    float(curves[index].pixel_points[0, 0]),
                    float(curves[index].pixel_points[-1, 0]),
                )
                for index in group
            ]
            candidate_interval = (
                float(candidate.pixel_points[0, 0]),
                float(candidate.pixel_points[-1, 0]),
            )
            if any(
                min(stop, candidate_interval[1])
                - max(start, candidate_interval[0])
                > 2.0
                for start, stop in intervals
            ):
                continue
            group.append(candidate_index)
        if len(group) < 2 or sum(
            curves[index].frequency_hz.size for index in group
        ) < width * MINIMUM_TRACE_COVERAGE:
            continue
        ordered = sorted(
            group, key=lambda index: curves[index].pixel_points[0, 0]
        )
        frequency_hz = np.concatenate(
            [curves[index].frequency_hz for index in ordered]
        )
        magnitude_db = np.concatenate(
            [curves[index].magnitude_db for index in ordered]
        )
        pixel_points = np.concatenate(
            [curves[index].pixel_points for index in ordered]
        )
        order = np.argsort(pixel_points[:, 0], kind="stable")
        representative = tuple(
            int(round(value))
            for value in np.median(
                np.asarray([curves[index].rgb for index in ordered]), axis=0
            )
        )
        provenance = tuple(
            item
            for index in ordered
            for item in (
                curves[index].sample_provenance
                or ("observed",) * curves[index].frequency_hz.size
            )
        )
        merged.append(
            DigitizedCurve(
                color=seed.color,
                rgb=representative,
                frequency_hz=frequency_hz[order],
                magnitude_db=magnitude_db[order],
                pixel_points=pixel_points[order],
                confidence=min(curves[index].confidence for index in ordered),
                observed_samples=sum(
                    curves[index].observed_samples
                    or curves[index].frequency_hz.size
                    for index in ordered
                ),
                sample_provenance=provenance,
            )
        )
        used.update(group)
    if not used:
        return curves
    return tuple(
        [curve for index, curve in enumerate(curves) if index not in used]
        + merged
    )


def _curve_overlap_geometry(
    first: DigitizedCurve,
    second: DigitizedCurve,
    *,
    minimum_overlap: float,
) -> tuple[float, float] | None:
    """Return robust separation statistics for a sufficiently long overlap."""

    overlap_left = max(
        float(first.pixel_points[0, 0]), float(second.pixel_points[0, 0])
    )
    overlap_right = min(
        float(first.pixel_points[-1, 0]), float(second.pixel_points[-1, 0])
    )
    if overlap_right - overlap_left + 1 < minimum_overlap:
        return None
    sample_x = np.linspace(overlap_left, overlap_right, 128)
    separation = np.abs(
        np.interp(sample_x, first.pixel_points[:, 0], first.pixel_points[:, 1])
        - np.interp(sample_x, second.pixel_points[:, 0], second.pixel_points[:, 1])
    )
    return float(np.median(separation)), float(np.quantile(separation, 0.90))


def _merge_antialias_shades(
    first: DigitizedCurve, second: DigitizedCurve
) -> DigitizedCurve:
    """Combine two raster shades while retaining the stronger observed pixel."""

    candidates: dict[int, tuple[float, int, int]] = {}
    curves = (first, second)
    for curve_index, curve in enumerate(curves):
        rgb = np.asarray(curve.rgb, dtype=np.float64)
        chroma = float(np.max(rgb) - np.min(rgb))
        darkness = 255.0 - float(np.max(rgb))
        evidence = chroma + darkness * 0.05
        for sample_index, x_value in enumerate(curve.pixel_points[:, 0]):
            x_key = int(round(float(x_value)))
            previous = candidates.get(x_key)
            if previous is None or evidence > previous[0]:
                candidates[x_key] = (evidence, curve_index, sample_index)
    selected = [candidates[x_key] for x_key in sorted(candidates)]
    source_curves = [curves[item[1]] for item in selected]
    source_indexes = [item[2] for item in selected]
    strongest = max(
        curves,
        key=lambda curve: (
            max(curve.rgb) - min(curve.rgb),
            255 - max(curve.rgb),
        ),
    )
    provenance: list[str] = []
    for curve, sample_index in zip(source_curves, source_indexes):
        if curve.sample_provenance:
            provenance.append(curve.sample_provenance[sample_index])
        else:
            provenance.append("observed")
    return DigitizedCurve(
        color=strongest.color,
        rgb=strongest.rgb,
        frequency_hz=np.asarray(
            [
                curve.frequency_hz[index]
                for curve, index in zip(source_curves, source_indexes)
            ],
            dtype=np.float64,
        ),
        magnitude_db=np.asarray(
            [
                curve.magnitude_db[index]
                for curve, index in zip(source_curves, source_indexes)
            ],
            dtype=np.float64,
        ),
        pixel_points=np.asarray(
            [
                curve.pixel_points[index]
                for curve, index in zip(source_curves, source_indexes)
            ],
            dtype=np.float64,
        ),
        confidence=min(first.confidence, second.confidence),
        observed_samples=provenance.count("observed"),
        shared_overlap_samples=provenance.count("shared_overlap"),
        interpolated_samples=provenance.count("interpolated"),
        sample_provenance=tuple(provenance),
    )


def _collapse_antialias_alias_tracks(
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
) -> tuple[DigitizedCurve, ...]:
    """Collapse raster shades without merging independently separated traces.

    PDF antialiasing can create either two shades of one physical line or a
    short blended colour between two nearby lines.  Both cases require tight
    geometric overlap and explicit colour evidence; position alone is never
    enough to reduce the returned trace count.
    """

    if len(curves) < 2:
        return curves
    left, top, right, bottom = plot_box
    width = right - left + 1
    height = bottom - top + 1
    median_limit = max(2.0, height * 0.012)
    quantile_limit = max(5.0, height * 0.025)

    working = list(curves)
    changed = True
    while changed:
        changed = False
        for first_index in range(len(working) - 1):
            for second_index in range(first_index + 1, len(working)):
                first = working[first_index]
                second = working[second_index]
                direction_distance = float(
                    np.linalg.norm(
                        _chromatic_direction(first.rgb)
                        - _chromatic_direction(second.rgb)
                    )
                )
                rgb_distance = float(
                    np.linalg.norm(
                        np.asarray(first.rgb, dtype=np.float64)
                        - np.asarray(second.rgb, dtype=np.float64)
                    )
                )
                geometry = _curve_overlap_geometry(
                    first,
                    second,
                    minimum_overlap=width * 0.30,
                )
                if (
                    direction_distance > ANTIALIAS_SHADE_DIRECTION_DISTANCE
                    or rgb_distance < 30.0
                    or geometry is None
                    or geometry[0] > median_limit
                    or geometry[1] > quantile_limit
                ):
                    continue
                merged = _merge_antialias_shades(first, second)
                working = [
                    curve
                    for index, curve in enumerate(working)
                    if index not in {first_index, second_index}
                ]
                working.append(merged)
                changed = True
                break
            if changed:
                break

    if len(working) < 3:
        return tuple(working)

    remove: set[int] = set()
    for candidate_index, candidate in enumerate(working):
        candidate_span = float(
            candidate.pixel_points[-1, 0] - candidate.pixel_points[0, 0] + 1
        )
        candidate_density = candidate.frequency_hz.size / max(candidate_span, 1.0)
        if candidate_density >= ANTIALIAS_BRIDGE_DENSITY_LIMIT:
            continue
        companions: list[int] = []
        for other_index, other in enumerate(working):
            if other_index == candidate_index:
                continue
            geometry = _curve_overlap_geometry(
                candidate,
                other,
                minimum_overlap=width * 0.30,
            )
            if (
                geometry is not None
                and geometry[0] <= median_limit
                and geometry[1] <= quantile_limit
                and candidate.frequency_hz.size <= other.frequency_hz.size * 0.80
            ):
                companions.append(other_index)
        for first_offset, first_index in enumerate(companions[:-1]):
            for second_index in companions[first_offset + 1 :]:
                first_rgb = np.asarray(working[first_index].rgb, dtype=np.float64)
                second_rgb = np.asarray(working[second_index].rgb, dtype=np.float64)
                candidate_rgb = np.asarray(candidate.rgb, dtype=np.float64)
                segment = second_rgb - first_rgb
                denominator = float(np.dot(segment, segment))
                if denominator <= 0:
                    continue
                fraction = float(
                    np.clip(
                        np.dot(candidate_rgb - first_rgb, segment) / denominator,
                        0.0,
                        1.0,
                    )
                )
                blend_distance = float(
                    np.linalg.norm(
                        candidate_rgb - (first_rgb + fraction * segment)
                    )
                )
                if 0.10 <= fraction <= 0.90 and blend_distance <= 35.0:
                    remove.add(candidate_index)
                    break
            if candidate_index in remove:
                break
    return tuple(
        curve for index, curve in enumerate(working) if index not in remove
    )


def _recover_distinct_antialias_companion(
    rgb: NDArray[np.uint8],
    curves: tuple[DigitizedCurve, ...],
    plot_box: tuple[int, int, int, int],
    *,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str,
) -> tuple[DigitizedCurve, ...]:
    """Recover one broad second hue hidden by low-resolution pixel blending."""

    if len(curves) != 1:
        return curves
    existing = curves[0]
    left, top, right, bottom = plot_box
    crop = rgb[top : bottom + 1, left : right + 1]
    height, width = crop.shape[:2]
    radius = max(12.0, height * 0.08)
    candidates: list[tuple[float, DigitizedCurve]] = []
    existing_rgb = np.asarray(existing.rgb, dtype=np.float64)
    for color_name, representative_rgb, color_mask, color_chroma in _adaptive_color_masks(crop):
        direction_distance = float(
            np.linalg.norm(
                _chromatic_direction(representative_rgb)
                - _chromatic_direction(existing.rgb)
            )
        )
        rgb_distance = float(
            np.linalg.norm(
                np.asarray(representative_rgb, dtype=np.float64) - existing_rgb
            )
        )
        if direction_distance < 0.25 or rgb_distance < 70.0:
            continue
        x_values: list[int] = []
        y_values: list[float] = []
        rgb_values: list[tuple[int, int, int]] = []
        for x_pixel in range(width):
            rows = np.flatnonzero(color_mask[:, x_pixel])
            if not rows.size:
                continue
            anchor = float(
                np.interp(
                    x_pixel + left,
                    existing.pixel_points[:, 0],
                    existing.pixel_points[:, 1],
                )
                - top
            )
            rows = rows[np.abs(rows - anchor) <= radius]
            if not rows.size:
                continue
            weights = np.maximum(
                color_chroma[rows, x_pixel].astype(np.float64), 1.0
            )
            x_values.append(x_pixel)
            y_values.append(float(np.average(rows, weights=weights)))
            rgb_values.append(
                tuple(
                    int(round(value))
                    for value in np.median(crop[rows, x_pixel], axis=0)
                )
            )
        if len(x_values) < round(width * 0.50):
            continue
        x_array = np.asarray(x_values, dtype=np.float64)
        if x_array[-1] - x_array[0] + 1 < width * 0.85:
            continue
        y_array = np.asarray(y_values, dtype=np.float64)
        existing_y = np.interp(
            x_array + left,
            existing.pixel_points[:, 0],
            existing.pixel_points[:, 1] - top,
        )
        separation = np.abs(y_array - existing_y)
        if float(np.median(separation)) < max(3.0, height * 0.015):
            continue
        normalized_x = x_array / max(width - 1, 1)
        if spacing == "log":
            frequency_hz = np.exp(
                np.log(start_hz)
                + normalized_x * (np.log(stop_hz) - np.log(start_hz))
            )
        else:
            frequency_hz = start_hz + normalized_x * (stop_hz - start_hz)
        magnitude_db = y_max_db - y_array / max(height - 1, 1) * (
            y_max_db - y_min_db
        )
        if np.any(magnitude_db > PASSIVE_MAGNITUDE_TOLERANCE_DB):
            continue
        observed_rgb = tuple(
            int(round(value))
            for value in np.median(np.asarray(rgb_values, dtype=np.float64), axis=0)
        )
        candidates.append(
            (
                rgb_distance,
                DigitizedCurve(
                    color=color_name,
                    rgb=observed_rgb,
                    frequency_hz=frequency_hz,
                    magnitude_db=magnitude_db,
                    pixel_points=np.column_stack((x_array + left, y_array + top)),
                    confidence=float(min(0.80, len(x_values) / width)),
                    observed_samples=len(x_values),
                    sample_provenance=("observed",) * len(x_values),
                ),
            )
        )
    if not candidates:
        return curves
    companion = max(candidates, key=lambda item: item[0])[1]
    return (existing, companion)


def _ensure_supported_trace_density(curves: Sequence[DigitizedCurve]) -> None:
    """Fail closed when a crowded plot exceeds the proven association limit."""

    if len(curves) > MAX_RELIABLE_AUTO_TRACES:
        raise ValueError(
            "Dense overlapping traces could not be separated reliably; "
            "crop the plot or use a less crowded trace view."
        )


def detect_parameter_text(text: str) -> tuple[str | None, tuple[str, ...]]:
    """Return one unambiguous S-parameter label from OCR text."""

    matches = tuple(
        dict.fromkeys(
            match.group("parameter").upper() for match in _PARAMETER_RE.finditer(text)
        )
    )
    if len(matches) == 1:
        return matches[0], ()
    if len(matches) > 1:
        return None, ("Multiple S-parameter labels were found; choose the mapping manually.",)
    return None, ("No S-parameter label was read; choose the mapping manually.",)


def _read_parameter_with_ocr(path: Path) -> tuple[str | None, tuple[str, ...]]:
    executable = shutil.which("tesseract")
    if not executable:
        return None, ("OCR is unavailable; choose the mapping manually.",)
    try:
        completed = subprocess.run(
            [executable, str(path), "stdout", "--psm", "11"],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return None, ("OCR did not complete; choose the mapping manually.",)
    if completed.returncode != 0:
        return None, ("OCR could not read this image; choose the mapping manually.",)
    return detect_parameter_text(completed.stdout)


def _read_ocr_lines(
    path: Path, *, page_segmentation: int = 6
) -> tuple[tuple[OcrLine, ...], tuple[str, ...]]:
    """Read positioned OCR text while failing safely when OCR is unavailable."""

    executable = shutil.which("tesseract")
    if not executable:
        return (), ("OCR is unavailable; review the axes manually.",)
    try:
        completed = subprocess.run(
            [
                executable,
                str(path),
                "stdout",
                "--psm",
                str(page_segmentation),
                "tsv",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return (), ("OCR did not complete; review the axes manually.",)
    if completed.returncode != 0:
        return (), ("OCR could not read this image; review the axes manually.",)

    groups: dict[tuple[int, int, int, int], list[tuple[int, int, int, int, str]]] = {}
    for raw_line in completed.stdout.splitlines()[1:]:
        columns = raw_line.split("\t")
        if len(columns) < 12:
            continue
        text = columns[11].strip()
        if not text:
            continue
        try:
            key = tuple(int(columns[index]) for index in (1, 2, 3, 4))
            left, top, width, height = (int(columns[index]) for index in (6, 7, 8, 9))
            word_number = int(columns[5])
        except ValueError:
            continue
        groups.setdefault(key, []).append((word_number, left, top, width, height, text))

    lines: list[OcrLine] = []
    for words in groups.values():
        ordered = sorted(words)
        left = min(word[1] for word in ordered)
        top = min(word[2] for word in ordered)
        right = max(word[1] + word[3] for word in ordered)
        bottom = max(word[2] + word[4] for word in ordered)
        lines.append(
            OcrLine(
                " ".join(word[5] for word in ordered),
                left,
                top,
                right - left,
                bottom - top,
            )
        )
        # Keep the real image-space X position of standalone numeric ticks.
        # Grouping a whole baseline into one OCR line loses the endpoint
        # positions needed when the unit is printed only in "Frequency (GHz)".
        for word in ordered:
            if _NUMBER_RE.fullmatch(word[5]):
                lines.append(
                    OcrLine(
                        word[5],
                        word[1],
                        word[2],
                        word[3],
                        word[4],
                    )
                )
        # Preserve positioned frequency phrases as well as the full OCR line.
        # A VNA axis often prints every tick on one long baseline; estimating a
        # word's X position from proportional character count selected the
        # trailing "GHz/div" value as the stop frequency on Wilder exports.
        for size in (2, 3):
            for start in range(0, len(ordered) - size + 1):
                phrase_words = ordered[start : start + size]
                phrase = " ".join(word[5] for word in phrase_words)
                if not _FREQUENCY_RE.search(phrase):
                    continue
                phrase_left = min(word[1] for word in phrase_words)
                phrase_top = min(word[2] for word in phrase_words)
                phrase_right = max(word[1] + word[3] for word in phrase_words)
                phrase_bottom = max(word[2] + word[4] for word in phrase_words)
                lines.append(
                    OcrLine(
                        phrase,
                        phrase_left,
                        phrase_top,
                        phrase_right - phrase_left,
                        phrase_bottom - phrase_top,
                    )
                )
    return tuple(sorted(lines, key=lambda line: (line.top, line.left))), ()


def _decode_image(path: Path) -> NDArray[np.uint8]:
    try:
        with Image.open(path) as image:
            if image.width * image.height > MAX_DECODED_IMAGE_PIXELS:
                raise ValueError("The decoded image exceeds the 12-megapixel limit.")
            return np.asarray(image.convert("RGB"), dtype=np.uint8)
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The image could not be decoded.") from exc


def analyze_plot_image(path: str | Path) -> ImageAnalysis:
    """Recover plot geometry and conservative editable axis defaults."""

    image_path = Path(path).expanduser().resolve()
    rgb = _decode_image(image_path)
    plot_box = _detect_plot_box(rgb)
    lines, ocr_warnings = _read_ocr_lines(image_path, page_segmentation=6)
    calibration = detect_axis_calibration(
        lines,
        plot_box=plot_box,
        image_width=rgb.shape[1],
        image_height=rgb.shape[0],
    )
    if (
        calibration.status != "detected"
        or calibration.detected_parameter is None
    ) and not ocr_warnings:
        sparse_lines, sparse_warnings = _read_ocr_lines(
            image_path, page_segmentation=11
        )
        if sparse_lines:
            lines = (*lines, *sparse_lines)
            calibration = detect_axis_calibration(
                lines,
                plot_box=plot_box,
                image_width=rgb.shape[1],
                image_height=rgb.shape[0],
            )
        ocr_warnings = sparse_warnings
    if ocr_warnings:
        calibration = AxisCalibration(
            **{
                **calibration.__dict__,
                "warnings": (*calibration.warnings, *ocr_warnings),
            }
        )
    return ImageAnalysis(
        image_width=rgb.shape[1],
        image_height=rgb.shape[0],
        plot_box=plot_box,
        calibration=calibration,
    )


def digitize_plot_image(
    path: str | Path,
    *,
    start_hz: float,
    stop_hz: float,
    y_min_db: float,
    y_max_db: float,
    spacing: str = "linear",
    run_ocr: bool = True,
    parameter_hint: str | None = None,
    plot_box_override=None,
    trace_specs=None,
    exclusion_boxes=(),
) -> DigitizationResult:
    """Recover visible magnitude traces from one datasheet graph image.

    OCR is optional.  Positioned labels become editable defaults when they are
    available; callers can still supply corrected calibration without changing
    the numerical trace extraction contract.
    """

    values = (float(start_hz), float(stop_hz), float(y_min_db), float(y_max_db))
    if not all(np.isfinite(value) for value in values):
        raise ValueError("Axis limits must be finite.")
    if stop_hz <= start_hz:
        raise ValueError("Stop frequency must be greater than start frequency.")
    if y_max_db <= y_min_db:
        raise ValueError("Y Max must be greater than Y Min.")
    spacing_value = str(spacing).strip().lower()
    if spacing_value not in {"linear", "log"}:
        raise ValueError("Frequency spacing must be linear or log.")
    if spacing_value == "log" and start_hz <= 0:
        raise ValueError("Log frequency spacing requires a positive start frequency.")
    image_path = Path(path).expanduser().resolve()
    rgb = _decode_image(image_path)
    normalized_hint: str | None = None
    if parameter_hint is not None and str(parameter_hint).strip():
        normalized_hint, _hint_warnings = detect_parameter_text(
            str(parameter_hint).strip().upper()
        )
        if normalized_hint is None:
            raise ValueError("Parameter hint must identify one S-parameter.")
    # 人工图框与排除区直接参与提取，不修改原始图像。
    from .image_path_editor import checked_box, edited_curves
    # Codex说明(自动生成)： 计算并保存 plot_box，供后续语句继续读取或更新。
    plot_box = checked_box(plot_box_override, rgb.shape) if plot_box_override is not None else _detect_plot_box(rgb)
    # Codex说明(自动生成)： 检查条件 trace_specs is not None，根据结果选择后续执行路径。
    if trace_specs is not None:
        # Codex说明(自动生成)： 计算并保存 curves，供后续语句继续读取或更新。
        curves = edited_curves(rgb, plot_box, trace_specs, exclusion_boxes,
            start_hz=start_hz, stop_hz=stop_hz, y_min_db=y_min_db,
            y_max_db=y_max_db, spacing=spacing_value)
        # Codex说明(自动生成)： 返回 DigitizationResult(image_width=rgb.shape[1], image_heig...，让调用方取得本函数的处理结果。
        return DigitizationResult(image_width=rgb.shape[1], image_height=rgb.shape[0],
            plot_box=plot_box, curves=attach_visual_review(curves, plot_box, rgb=rgb),
            warnings=("人工路径：请复核身份、缺口和锚点。",), detected_parameter=normalized_hint)
    # Codex说明(自动生成)： 检查条件 exclusion_boxes，根据结果选择后续执行路径。
    if exclusion_boxes:
        # 自动模式同样支持图例遮罩，像素副本仅供算法读取。
        rgb = rgb.copy()
        # Codex说明(自动生成)： 遍历 exclusion_boxes 中的 rectangle，逐项执行循环体逻辑。
        for rectangle in exclusion_boxes:
            # Codex说明(自动生成)： 计算并保存 (x1, y1, x2, y2)，供后续语句继续读取或更新。
            x1,y1,x2,y2 = checked_box(rectangle,rgb.shape)
            # Codex说明(自动生成)： 计算并保存 rgb[y1:y2 + 1, x1:x2 + 1]，供后续语句继续读取或更新。
            rgb[y1:y2+1,x1:x2+1] = 255
    detected_parameter, warnings = (
        _read_parameter_with_ocr(image_path) if run_ocr else (None, ())
    )
    if detected_parameter is None:
        detected_parameter = normalized_hint
    curves = _extract_curves(
        rgb,
        plot_box,
        start_hz=start_hz,
        stop_hz=stop_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing_value,
        # Sparse candidates are retained temporarily so a global association
        # pass can prove that an unlabelled trace disappears and reappears.
        # Unproved candidates are filtered back to the normal coverage floor
        # before returning the result.
        allow_sparse=True,
    )
    curves = _collapse_antialias_alias_tracks(curves, plot_box)
    curves = _recover_anchored_ambiguous_hue_pairs(
        rgb,
        curves,
        plot_box,
        start_hz=start_hz,
        stop_hz=stop_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing_value,
    )
    curves = _recover_distinct_antialias_companion(
        rgb,
        curves,
        plot_box,
        start_hz=start_hz,
        stop_hz=stop_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing_value,
    )
    achromatic_curves = _extract_achromatic_curves(
        rgb,
        plot_box,
        start_hz=start_hz,
        stop_hz=stop_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing_value,
        allow_sparse=True,
    )
    if achromatic_curves:
        curves = tuple(curves) + achromatic_curves
    if not curves:
        left, top, right, bottom = plot_box
        colour_masks = _adaptive_color_masks(
            rgb[top : bottom + 1, left : right + 1]
        )
        coloured_support = sum(
            int(np.count_nonzero(mask))
            for _name, _rgb, mask, _chroma in colour_masks
        )
        if len(colour_masks) >= 3 and coloured_support >= (right - left + 1) * 2:
            raise ValueError(
                "Dense overlapping traces could not be separated reliably; "
                "crop the plot or use a less crowded trace view."
            )
        raise ValueError(
            "No supported coloured magnitude trace or achromatic magnitude "
            "trace was found in the plot area."
        )
    _ensure_supported_trace_density(curves)
    if detected_parameter is not None:
        curves = _merge_sparse_same_colour_fragments(curves, plot_box)
    curves = _complete_occluded_prefixes(
        curves,
        plot_box,
        parameter=detected_parameter,
        start_hz=start_hz,
        stop_hz=stop_hz,
        spacing=spacing_value,
    )
    curves = _complete_repeated_overlaps(
        rgb,
        curves,
        plot_box,
        parameter=detected_parameter,
        start_hz=start_hz,
        stop_hz=stop_hz,
        y_min_db=y_min_db,
        y_max_db=y_max_db,
        spacing=spacing_value,
    )
    if detected_parameter is None:
        left, _top, right, _bottom = plot_box
        width = right - left + 1
        curves = tuple(
            curve
            for curve in curves
            if curve.frequency_hz.size >= round(width * MINIMUM_TRACE_COVERAGE)
            or (
                curve.frequency_hz.size >= max(20, round(width * 0.30))
                and curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1
                >= round(width * 0.45)
            )
            or (
                np.ptp(curve.rgb) <= 5
                and curve.pixel_points[0, 0] - left <= max(3, width * 0.02)
                and curve.frequency_hz.size >= max(20, round(width * 0.30))
                and curve.frequency_hz.size / (curve.pixel_points[-1, 0] - curve.pixel_points[0, 0] + 1) >= 0.85
            )
        )
        if not curves:
            raise ValueError(
                "No supported coloured magnitude trace or achromatic magnitude "
                "trace was found in the plot area."
            )
    # Association uses column centres. Recover isolated source-supported tips
    # afterwards, without changing identities, sparse coverage, or shared runs.
    left, top, right, bottom = plot_box
    crop = rgb[top:bottom + 1, left:right + 1]
    refined = []
    for curve in curves:
        local_points = curve.pixel_points - (left, top)
        compatible = [other for other in curves if other is not curve and _colour_identity_is_compatible(np.asarray(curve.rgb, float), np.asarray(other.rgb, float))]
        # Same-colour tracks cannot independently claim a merged turning lobe.
        # Retain their association and let pixel review expose the ambiguity.
        if not compatible:
            protected = [index for index, source in enumerate(curve.sample_provenance) if source != "observed"]
            local_points = preserve_raster_turns(colour_evidence_mask(crop, curve.rgb), local_points, protected_indexes=protected)
        refined.append(replace(curve, pixel_points=local_points + (left, top), magnitude_db=y_max_db - local_points[:, 1] / max(bottom - top, 1) * (y_max_db - y_min_db)))
    curves = attach_visual_review(refined, plot_box, rgb=rgb)
    return DigitizationResult(
        image_width=rgb.shape[1],
        image_height=rgb.shape[0],
        plot_box=plot_box,
        curves=curves,
        warnings=warnings,
        detected_parameter=detected_parameter,
    )
