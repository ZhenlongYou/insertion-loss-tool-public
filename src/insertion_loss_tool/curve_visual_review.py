"""Local evidence and topology review for recovered raster curves."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol, Sequence, TypeVar

import numpy as np
from numpy.typing import NDArray

from .trace_recovery_policy import VISUAL_REVIEW_ENABLED


@dataclass(frozen=True)
class CurveReviewRegion:
    """One source-image interval that deserves visual confirmation."""

    start_x: float
    end_x: float
    reason: str
    severity: str
    samples: int


class ReviewableCurve(Protocol):
    pixel_points: NDArray[np.float64]
    confidence: float
    observed_samples: int
    shared_overlap_samples: int
    interpolated_samples: int
    sample_provenance: tuple[str, ...]


CurveT = TypeVar("CurveT", bound=ReviewableCurve)


def _provenance_regions(curve: ReviewableCurve) -> tuple[CurveReviewRegion, ...]:
    """Convert non-observed samples into exact local review intervals."""

    provenance = curve.sample_provenance
    if not provenance or len(provenance) != curve.pixel_points.shape[0]:
        return ()
    regions: list[CurveReviewRegion] = []
    start = 0
    while start < len(provenance):
        reason = provenance[start]
        if reason == "observed":
            start += 1
            continue
        stop = start
        while (
            stop + 1 < len(provenance)
            and provenance[stop + 1] == reason
            and curve.pixel_points[stop + 1, 0]
            - curve.pixel_points[stop, 0]
            <= 1.5
        ):
            stop += 1
        regions.append(
            CurveReviewRegion(
                start_x=float(curve.pixel_points[start, 0]),
                end_x=float(curve.pixel_points[stop, 0]),
                reason=reason,
                severity="high" if reason == "shared_overlap" else "medium",
                samples=stop - start + 1,
            )
        )
        start = stop + 1
    return tuple(regions)


def _upward_excursion_regions(
    curve: ReviewableCurve,
    plot_box: tuple[int, int, int, int],
) -> tuple[CurveReviewRegion, ...]:
    """Find short two-sided upward detours with a local geometric oracle."""

    points = curve.pixel_points
    if points.shape[0] < 25:
        return ()
    left, top, right, bottom = plot_box
    width = right - left + 1
    height = bottom - top + 1
    radius = max(12, round(width * 0.035))
    if points.shape[0] <= radius * 2:
        return ()
    x_values = points[:, 0]
    y_values = points[:, 1]
    suspicious = np.zeros(points.shape[0], dtype=np.bool_)
    threshold = max(20.0, height * 0.08)
    for index in range(radius, points.shape[0] - radius):
        left_index = index - radius
        right_index = index + radius
        horizontal_span = x_values[right_index] - x_values[left_index]
        if horizontal_span <= 0 or horizontal_span > radius * 3.0:
            continue
        fraction = (x_values[index] - x_values[left_index]) / horizontal_span
        expected = y_values[left_index] + fraction * (
            y_values[right_index] - y_values[left_index]
        )
        suspicious[index] = expected - y_values[index] >= threshold

    starts = np.flatnonzero(suspicious & np.r_[True, ~suspicious[:-1]])
    stops = np.flatnonzero(suspicious & np.r_[~suspicious[1:], True])
    maximum_run = max(24, round(width * 0.08))
    stable_limit = max(12.0, height * 0.05)
    regions: list[CurveReviewRegion] = []
    for start, stop in zip(starts, stops):
        if stop - start + 1 > maximum_run:
            continue
        neighbour_count = max(6, radius // 2)
        before = y_values[max(0, start - neighbour_count) : start]
        after = y_values[stop + 1 : stop + 1 + neighbour_count]
        if before.size < 4 or after.size < 4:
            continue
        before_level = float(np.median(before))
        after_level = float(np.median(after))
        if abs(before_level - after_level) > stable_limit:
            continue
        excursion_level = float(np.median(y_values[start : stop + 1]))
        if min(before_level, after_level) - excursion_level < threshold * 0.55:
            continue
        regions.append(
            CurveReviewRegion(
                start_x=float(x_values[start]),
                end_x=float(x_values[stop]),
                reason="upward_excursion",
                severity="high",
                samples=int(stop - start + 1),
            )
        )
    return tuple(regions)


def _raster_gap_regions(curve: ReviewableCurve) -> tuple[CurveReviewRegion, ...]:
    """Expose source-image columns that contain no sample for this path."""

    if curve.pixel_points.shape[0] < 2:
        return ()
    x_values = curve.pixel_points[:, 0]
    gaps = np.flatnonzero(np.diff(x_values) > 1.5)
    minimum_gap = max(3, round((x_values[-1] - x_values[0] + 1) * 0.004))
    return tuple(
        CurveReviewRegion(
            start_x=float(np.floor(x_values[index]) + 1),
            end_x=float(np.ceil(x_values[index + 1]) - 1),
            reason="raster_gap",
            severity="medium",
            samples=max(1, int(round(x_values[index + 1] - x_values[index] - 1))),
        )
        for index in gaps
        if x_values[index + 1] - x_values[index] - 1 >= minimum_gap
    )


def attach_visual_review(
    curves: Sequence[CurveT],
    plot_box: tuple[int, int, int, int],
) -> tuple[CurveT, ...]:
    """Attach local evidence and topology review results to every trace."""

    if not VISUAL_REVIEW_ENABLED:
        return tuple(curves)
    reviewed: list[CurveT] = []
    for curve in curves:
        regions = (
            *_provenance_regions(curve),
            *_raster_gap_regions(curve),
            *_upward_excursion_regions(curve, plot_box),
        )
        sample_count = max(curve.pixel_points.shape[0], 1)
        risk = (
            curve.interpolated_samples
            + 0.5 * curve.shared_overlap_samples
            + sum(
                region.samples
                for region in regions
                if region.reason in {"raster_gap", "upward_excursion"}
            )
        ) / sample_count
        reviewed.append(
            replace(
                curve,
                visual_confidence=float(
                    np.clip(min(curve.confidence, 1.0 - risk), 0.0, 1.0)
                ),
                review_status="review" if regions else "clear",
                review_regions=regions,
            )
        )
    return tuple(reviewed)
