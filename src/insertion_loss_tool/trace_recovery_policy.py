"""Reliability limits for automatic raster trace association."""

# The coupled tracker retains at most eight independent observations in one
# plot column.  A result with more candidate paths cannot prove every crossing
# identity and must be sent to manual review instead of exported automatically.
MAX_RELIABLE_AUTO_TRACES = 8

# Product datasheets may expose only a 0 to -3 dB vertical range, so four
# horizontal grid lines are the minimum accepted by the two-dimensional
# fallback.  Fewer lines do not prove a regular plot grid.
MINIMUM_PRODUCT_GRID_LINES = 4

# PDF rasterisation commonly lifts a dotted neutral grid above level 230.
# Level 245 retains those lines while excluding the white page background.
PALE_GRID_MAX_INTENSITY = 245

# Two raster shades may represent one physical path only when their chromatic
# directions are nearly identical.  This is intentionally much stricter than
# the per-pixel antialias grouping used during initial tracking.
ANTIALIAS_SHADE_DIRECTION_DISTANCE = 0.12

# A blended middle-colour path must remain sparse before it can be classified
# as antialias evidence between two longer physical traces.
ANTIALIAS_BRIDGE_DENSITY_LIMIT = 0.70

# A fragmented hue may be completed only when at least 92% of populated
# columns contain one vertical path, and an observed fragment already covers
# a quarter of the plot.  The small ambiguity allowance covers real crossings
# and steep VNA notches; two coexisting same-hue paths are handled separately
# by anchored association and never by a column median.
MAX_UNIQUE_HUE_AMBIGUOUS_COLUMN_FRACTION = 0.08
MAX_SINGLE_ANCHOR_HUE_AMBIGUOUS_COLUMN_FRACTION = 0.15
MINIMUM_UNIQUE_HUE_PARTIAL_SPAN = 0.25
MAX_UNIQUE_HUE_TRANSITION_GAP = 3

# The anchored ambiguous-hue tracker is deliberately a two-identity solver:
# one full-width path and one substantial partial path.  More identities are
# not auto-associated because the available raster evidence is insufficient.
AMBIGUOUS_HUE_PAIR_SIZE = 2

# Short raster artifacts (a missing antialias sample or same-colour legend
# glyph) may be repaired only when they are internally bounded and occupy at
# most this fraction of the horizontal samples.  Zero disables both repairs;
# the mutation gate uses that value to reproduce the escaped Figure 36 error.
MAX_SHORT_RASTER_ARTIFACT_RUN_FRACTION = 0.012

# The final visual-review pass must stay independent from the association
# decision: it exposes local interpolation, shared evidence, raster gaps, and
# glyph-like excursions even when the recovered full path looks plausible.
# The directed test mutant disables this switch to prove the public workflow
# does not silently regress to a whole-trace confidence number.
VISUAL_REVIEW_ENABLED = True

# An ideal matched fallback must be exactly zero in linear magnitude.  A very
# small finite dB value can still make a unity through path appear non-passive.
MATCHED_FALLBACK_DB = float("-inf")
