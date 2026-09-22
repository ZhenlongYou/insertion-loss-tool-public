"""Conservative two-dimensional evidence for raster trace turns.

A thick, almost vertical stroke occupies many rows in one column. Its column
mean is a useful association observation, but is not the tip of a narrow notch.
This module keeps those observations for association and repairs only isolated
two-sided turns backed by one connected source-pixel lobe. It does not estimate
an instrument response or subpixel truth from an under-resolved raster.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RasterTurn:
    """Source interval and raster-supported endpoint of one sharp turn."""

    start_x: float
    end_x: float
    sample_index: int
    tip_y: float
    linewidth: float
    ambiguous: bool = False


def colour_evidence_mask(rgb, colour):
    """Match a trace's colour without treating pale background as a trace.

    Neutral identity uses intensity; chromatic identity permits white-blended
    edges. This is evidence for an already associated trace, not a new identity
    classifier. Disconnected matching pixels never establish a turn by themselves.
    """

    values = np.asarray(rgb, dtype=float)
    colour = np.asarray(colour, dtype=float)
    spread = np.ptp(values, axis=2)
    target = colour - colour.min()
    if np.linalg.norm(target) < 8:
        return (spread <= 8) & (values.max(axis=2) <= 240) & (np.abs(values.mean(axis=2) - colour.mean()) <= 28)
    chroma = values - values.min(axis=2)[..., None]
    norm = np.linalg.norm(chroma, axis=2)
    direction = chroma / np.maximum(norm[..., None], 1)
    return (spread >= 10) & (
        np.linalg.norm(direction - target / np.linalg.norm(target), axis=2) < 0.24
    )


def _connected_pixels(mask, seed):
    """Flood one local 8-connected component; other matching blobs stay out."""

    height, width = mask.shape
    y, x = seed
    if not (0 <= y < height and 0 <= x < width and mask[y, x]):
        return np.zeros_like(mask)
    component = np.zeros_like(mask)
    component[y, x] = True
    pending = [(y, x)]
    while pending:
        y, x = pending.pop()
        for ny in range(max(0, y - 1), min(height, y + 2)):
            for nx in range(max(0, x - 1), min(width, x + 2)):
                if mask[ny, nx] and not component[ny, nx]:
                    component[ny, nx] = True
                    pending.append((ny, nx))
    return component


def raster_turns(mask, points):
    """Find isolated turns in local image coordinates, retaining their direction.

    The tip must join both observed shoulders through source pixels, sit away
    from window boundaries, and have at most two horizontal branches. Narrow
    source pillars remain ambiguous at raster resolution even when their visible
    endpoint is recoverable; callers must expose the returned interval for review.
    Sparse gaps are never bridged by this operation.
    """

    points = np.asarray(points, dtype=float)
    if len(points) < 9:
        return ()
    height, width = mask.shape
    xs, ys = points.T
    radius = max(8, min(24, round(width * 0.035)))
    # The lower quartile of short, selected cross sections estimates visible
    # stroke width without allowing a steep column to masquerade as a fat pen.
    widths = []
    for x, y in points[::max(1, len(points) // 100)]:
        column = int(round(x))
        row = int(round(y))
        if not (0 <= column < width and 0 <= row < height and mask[row, column]):
            continue
        lo = hi = row
        while lo > 0 and mask[lo - 1, column]:
            lo -= 1
        while hi + 1 < height and mask[hi + 1, column]:
            hi += 1
        if hi - lo + 1 <= 15:
            widths.append(hi - lo + 1)
    linewidth = max(1.0, float(np.percentile(widths, 25))) if widths else 3.0
    threshold = max(8.0, linewidth * 4)
    found = []
    claimed = set()
    for index in range(2, len(points) - 2):
        # A local extremum with shoulders on both sides is essential. A single
        # monotone steep section must retain its centre, not an arbitrary edge.
        lo = int(np.searchsorted(xs, xs[index] - radius))
        hi = int(np.searchsorted(xs, xs[index] + radius, side="right")) - 1
        if lo >= index or hi <= index or xs[index] - xs[lo] < radius * 0.7 or xs[hi] - xs[index] < radius * 0.7:
            continue
        if np.any(np.diff(xs[lo:hi + 1]) > 1.5):
            continue
        for direction in (-1, 1):
            level = direction * ys[index]
            if level < max(direction * ys[index - 1], direction * ys[index + 1]):
                continue
            if min(direction * (ys[index] - ys[lo]), direction * (ys[index] - ys[hi])) < threshold:
                continue
            if (index, direction) in claimed:
                continue
            x0, x1 = int(round(xs[lo])), int(round(xs[hi]))
            if x0 < 0 or x1 >= width:
                continue
            local = mask[:, x0:x1 + 1]
            cx = int(round(xs[index])) - x0
            rows = np.flatnonzero(local[:, cx])
            if not rows.size:
                continue
            seed_y = int(rows[np.argmin(abs(rows - ys[index]))])
            if abs(seed_y - ys[index]) > linewidth + 1:
                continue
            component = _connected_pixels(local, (seed_y, cx))
            if not all(np.any(component[max(0, int(round(y - linewidth))):min(height, int(round(y + linewidth)) + 1), x]) for x, y in ((0, ys[lo]), (x1 - x0, ys[hi]))):
                continue
            # The connected component must enter/leave through only the two
            # selected shoulders. A same-colour crossing can join a flat target
            # to another trace's notch: both shoulders still match, but the
            # extra boundary branch proves that connectivity is not identity.
            # Preserve this counterevidence even when the other trace's endpoint
            # lies too far sideways to qualify as an ordinary recoverable tip.
            branched = any(
                np.any(np.diff(np.flatnonzero(component[:, edge])) > max(2, linewidth))
                for edge in (0, component.shape[1] - 1)
            )
            cy, _ = np.nonzero(component)
            if not cy.size:
                continue
            extreme_y = int(cy.max() if direction > 0 else cy.min())
            tip_columns = np.flatnonzero(component[extreme_y])
            tip_x = float(np.mean(tip_columns) + x0)
            # A neighbouring peak or a long flat annotation is not this turn.
            if not branched and (abs(tip_x - xs[index]) > max(2, linewidth) or np.ptp(tip_columns) > max(5, linewidth * 2)):
                continue
            tip_index = int(np.argmin(abs(xs - tip_x)))
            baseline = max(ys[lo], ys[hi]) if direction > 0 else min(ys[lo], ys[hi])
            y_range = np.arange(height)[direction * (np.arange(height) - baseline) > threshold / 2]
            for row in y_range:
                occupied = np.flatnonzero(component[row])
                if occupied.size and np.count_nonzero(np.diff(occupied) > 1) >= 2:
                    branched = True
                    break
            # Deduplicate a raster plateau's adjacent maxima.
            for offset in range(max(0, tip_index - int(linewidth) - 1), min(len(points), tip_index + int(linewidth) + 2)):
                claimed.add((offset, direction))
            tip_y = extreme_y - direction * (linewidth - 1) / 2
            found.append(RasterTurn(float(xs[lo]), float(xs[hi]), tip_index, float(tip_y), linewidth, branched))
    return tuple(found)


def preserve_raster_turns(mask, points, *, protected_indexes=()):
    """Restore visible lobe endpoints without moving manual anchors or gaps.

    Only a turn endpoint is replaced; ordinary column centres and association
    decisions remain intact. Isolated noise is excluded by connectivity, and
    multi-branch components require manual identity review instead of correction.
    """

    repaired = np.asarray(points, dtype=float).copy()
    protected = set(protected_indexes)
    for turn in raster_turns(mask, repaired):
        if not turn.ambiguous and turn.sample_index not in protected:
            repaired[turn.sample_index, 1] = turn.tip_y
    return repaired
