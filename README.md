# Insertion Loss Touchstone Tool

This project generates, validates, edits, and plots Touchstone S-parameter files.
The desktop generator offers the common 2-, 3-, 4-, 6-, and 8-port engineering
topologies; the shared full-matrix reader/writer can also round-trip `.sNp`
files for other positive port counts.

完整中文界面说明、每个页签和按钮的用途、Modify 无源拒绝原因、图片映射与
Windows 单文件版运行要求，见
[《Insertion Loss Tool 使用说明书》](docs/user_manual/InsertionLossTool_使用说明书.html)。

0.6.0 的图片曲线保真、手动纠错和输出采样提示见
[图片曲线保真与纠错](docs/image_fidelity.md)。Windows 单文件构建由公开仓库的
GitHub Actions workflow 执行，结果和可下载 artifact 位于仓库的 Actions 页面。

## Standalone Desktop App

The desktop GUI entry point is:

```bash
python3 gui_main.py
```

It opens **Insertion Loss Tool** in the same pywebview shell on both supported
platforms: macOS uses WKWebView and Windows uses Edge WebView2. The
`Generate and Modify S-Parameter` page keeps all four modes—`Linear`,
`Formula`, `Draw`, and `Modify`—and
displays every Sij trace as magnitude or phase. Switching pages
only changes the HTML panel; it does not rebuild native Tk widgets.

In `Modify`, choosing a Touchstone file or entering its path and pressing Enter
loads it immediately. The source port count, point count, start, and stop replace
the temporary sweep display, and the right side previews every source S-parameter
before generation. An unreadable path shows an inline error and clears any stale
preview; switching back to a generator mode restores the prior generator sweep.

`Generate and Modify S-Parameter` and single-ended `Image to S-Parameter`
outputs use the same compact port
choices: 2, 3, 4, 6, and 8. Mixed-mode outputs expose only the physically
pairable 2, 4, 6, and 8 choices. Generated networks default to adjacent
reciprocal lanes (1↔2, 3↔4,
and so on). In the 3-port case, port 3 stays at the configured reflection and
crosstalk floor until the user supplies explicit through paths; the tool does
not silently assume a splitter or circulator topology.

The `Image to S-Parameter` page is a composition workbench for plot images. Its
`Add` action appends PNG/JPEG/GIF/WebP files and deduplicates equal content;
`Remove` deletes the selected image and safely reindexes or clears mappings that
referred to it. `Output Networks`, image metadata, detected traces, and network
details share one wide row
at the normal window size; the responsive layout moves the details below them
without clipping the output list. The image panel provides a large preview plus
wheel/button zoom and drag-to-pan, and keeps each image's
start, stop, step, X Scale, Y Max, and Y Min settings independent. After `Add`,
the tool automatically locates the regular plot grid and reads positioned axis
labels plus an unambiguous S-parameter label with local Tesseract OCR. Complete
results become editable detected defaults and are digitized immediately. A
partial result preserves every value that was actually read but remains
`Review`; it is never silently completed from unrelated defaults. Even before
axis calibration, recovered pixel paths are shown as disabled `Trace Candidates`
so the user can verify whether the physical lines were separated. After Start,
Stop, Output Step, Y Top, and Y Bottom are supplied, `Re-digitize` converts those
same candidates into calibrated traces that can be mapped. `Y Values` accepts
either ordinary S-parameter dB (loss is negative) or a positive-loss axis (loss
increases downward and is converted to negative S-parameter magnitude). For
image calibration only, a frequency without a suffix is interpreted as GHz,
so `0 / 5 / 0.1` is equivalent to `0GHz / 5GHz / 0.1GHz`. Linear plots may start
at DC; logarithmic plots still require a strictly positive Start frequency.
Some VNA exports print Start, Stop,
and `GHz/div` but omit the acquisition sweep Step. For a visibly linear plot,
the app then uses native horizontal plot-pixel spacing as the editable Step and
marks its source `detected-pixel`; this is raster sampling resolution, not a
claim about the vendor's original VNA sweep configuration.

Trace extraction follows continuous chromatic paths rather than a fixed
red/blue palette, retains the RGB sampled from the current image, and supports
separate same-colour paths. The overlay shows the detected plot rectangle and
all recovered traces for review. Each recovered trace receives a stable,
high-contrast display colour even when two source traces were both sampled as
the same magenta/grey raster colour; the original sampled colour remains visible
as provenance text. Hovering or selecting a trace highlights only its matching
overlay. A second, independent local review pass marks interpolated/shared
evidence, missing raster columns, and short glyph-like upward detours with an
orange dashed segment at the exact source-image position. The trace card shows
its visual confidence and the number of highlighted areas. These marks request
visual confirmation; they do not prove that the curve is wrong, and a clear
trace does not prove the vendor's underlying measurement. The trace card is
read-only and reports whether an output currently
uses it; the right-side S-parameter dropdowns are the sole mapping controls and
list every recovered trace by stable number and sampled colour. Multiple traces do
not block digitization or generation: mappings stay on their defaults until the
user assigns them. A steep VNA notch may split a raster path into continuity
fragments. The fallback completes that trace only when the same hue spans at
least 80% of the plot, almost every populated column contains one vertical path,
exactly one matching partial track already exists, and each split is a narrow
raster gap. This recovers the missing prefixes seen in Wilder 910-0077-000 Rev E
Figures 33 and 36 without joining two disjoint or competing same-hue curves.
When several same-hue paths are genuinely ambiguous, the tool keeps the partial
traces for manual review instead of inventing a full-width curve.
No image curve is offered as a source before successful
digitization, and a failed retry clears stale results. When one OCR parameter
label corresponds to multiple traces, it remains metadata and no arbitrary trace
is auto-selected for an output mapping. Later imports send only
newly added pixels. Calibration fields are locked while recognition runs, and
an axis revision token prevents an older result from overwriting a newer
calibration. The bounded cache accepts at most 32 images, 20 MB per image, and
128 MB total; decoded images are limited to 12 megapixels. Color classification
uses bounded decoded arrays. A raster with no locatable regular plot area is
rejected. Visible curve identities are stable
`Trace 1`, `Trace 2`, and so on, accompanied by the color actually sampled from
that image; color names are not used as curve identities.
Curves that are pixel-identical in the raster cannot be separated honestly;
such intervals are treated as one resolvable observation instead of inventing
independent data.

An output can use ordinary `Sij` or the four mixed-mode blocks `SDD`, `SDC`,
`SCD`, and `SCC`. Keysight's balanced-measurement notation places the output
mode before the input mode, so `SCD21` means differential input to common-mode
output ([Keysight FlexDCA, “T and S Parameters,” Balanced Devices](https://helpfiles.keysight.com/scopes/FlexDCA-UG/Content/Topics/TDR-TDT-Mode/Parameters/a_ST_parameters.htm)).
For differently sampled images, `Common Range` is the safe default; `Manual`
specifies one output grid, while `Full Range` requires explicit `Fill Missing
Range` outside an image's coverage. Interpolation is reported and never
described as increased source resolution. Raw recognized sample counts may
differ, but every mapped image curve and generated default channel is normalized
onto one inclusive, uniform output grid. The UI reports its start, stop, step,
point count, and resampled-channel count. A manual step must divide the selected
span exactly; default-only outputs require an explicit manual grid. The
`Reciprocal` option uses the
standard network term and remains explicit rather than silently forcing
symmetry.

Mixed-mode curves are not silently renamed to single-ended `Sij`. Exact
conversion is enabled only when a complete complex mixed-mode matrix, physical
port pairing, and compatible reference impedances are available. This follows
the invertible matrix transformation and ordering contract in the
[Touchstone File Format Specification 2.0](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf),
Introduction to Mixed-Mode Concepts (printed pp. 19–20), `[Mixed-Mode Order]`
(pp. 20–22), and Appendix A (pp. 28–32). A datasheet magnitude trace alone
lacks phase and the remaining matrix blocks, so it remains a mixed-mode curve.

Curve digitization is magnitude-only. The raster does not contain phase,
reference-impedance normalization, or a complete complex matrix, so it cannot
recreate the vendor's original Touchstone file. `Generate File` therefore uses
the explicit zero-degree phase approximation and reports it in the status area;
`Open Folder` opens the directory of the latest file generated by this page,
independently of files generated by the other page.

The plot frequency axis is always displayed on a linear scale. Mode controls
named **Fit axis** or **Smooth axis** affect only the numerical fitting domain
used to generate or modify insertion loss; they do not change the displayed
plot axis. The frequency unit, such as GHz, remains the same because
linear/log changes spacing, not physical units.

Generated and Modify previews choose readable engineering tick intervals rather
than dividing the visible span into arbitrary decimals. Frequency and magnitude
use `1/2/5 × 10^n` steps; phase prefers familiar degree intervals such as
`30°`, `45°`, `90°`, `180°`, and `360°`. This changes only the displayed axis
limits and labels: the Touchstone frequency samples and complex S-parameter data
are not rounded, resampled, or otherwise modified.

For draw mode, point values use the usual S-parameter magnitude convention:
`0 dB` is the top of the axis and insertion loss is drawn as negative dB, for
example `5GHz:-4.0`. Click the in-page drawing area to add points, or edit the
control-point field directly. Its axes use the same `Magnitude (dB)` and
centered `Frequency (<selected unit>)` labels as the generated plots.
After Draw generation succeeds, the drawing board is replaced by the complete
S-parameter magnitude/phase plot set, just like Linear and Formula. Editing a
control point or a Draw axis value returns to the drawing board for the next
revision.

In the Image workspace, `Unassigned` means that no trace or fallback curve has
been chosen; it is not a valid default. A generatable channel must select a
detected trace, `Matched · exact zero`, `Return loss −20 dB`, or
`Crosstalk −80 dB`. The exact-zero choice is intended for an ideal matched
fallback and avoids adding a tiny nonzero reflection to a near-0 dB transmission.
Export preflight
lists every unassigned S-parameter before calling the backend.

### Build a macOS App

On macOS:

```bash
./build_macos_app.command
dist/InsertionLossTool.app/Contents/MacOS/InsertionLossTool --self-test
```

The `.app` bundle includes Python and the required packages, so the recipient
does not need to install Python. A `.app` built on this Mac is for Apple
Silicon macOS. It is locally/ad-hoc signed by PyInstaller, not Apple-notarized,
so macOS Gatekeeper may require the recipient to right-click and choose Open or
to approve the app in System Settings.

### Build a Windows EXE

PyInstaller builds native executables for the operating system it runs on. A
real Windows `.exe` must be built on Windows; a macOS build cannot be renamed
into a Windows executable. To produce the Windows `.exe`, copy this project to
Windows and run:

```bat
build_windows_exe.bat
```

The script is the only supported Windows packaging entry point. It runs the
full source tests and renderer probe, builds a single-file `--onefile`
application, repeats the backend and renderer checks against the packaged EXE, and then creates
`dist\InsertionLossTool-<version>-windows-x64.zip` plus its SHA-256 file. Read
`AGENTS.md` for the required Windows acceptance checklist. The ZIP contains
only `InsertionLossTool.exe`; there is no `_internal` directory.
The recipient does not need Python; the build machine needs 64-bit Windows
Python and internet access once to install dependencies. Edge WebView2 Runtime
is required. Tesseract is an optional external dependency for automatic OCR;
without it, image traces can still be extracted but labels and axes must be
reviewed manually.

The public repository workflow at `.github/workflows/windows-build.yml` runs the
same contract on `windows-2022`. A manual dispatch can upload the verified
single-EXE ZIP and, when requested, publish that ZIP with its SHA-256 manifest
as a GitHub Release.

## Stress Test

Run the deterministic stress suite before sharing a build:

```bash
python3 stress_test.py --iterations 80
```

The stress test exercises S2P/S4P generation, RI/MA/DB Touchstone round trips,
linear/log sweeps, negative-dB draw controls, modify-mode target insertion,
phase preservation, sampled passivity, and deliberately invalid power budgets.

## Physical meaning and release safety

Generated files are **sampled-passive engineering approximations**. Before a
file is written, the tool checks the largest singular value of the full
S-matrix at every generated frequency. The packaged `--self-test` then rereads
each output and repeats that sampled-domain check, so serialization errors or a
non-passive release cannot be reported as a successful self-test.

This is not a broadband causality or realizability certificate. Finite sampled
passivity does not prove that the response between points is causal, stable, or
representative of a specific cable, connector, package, or compliance channel.
Use measured or EM-extracted data, denser frequency coverage, and a rational
model/passivity workflow when those claims matter.

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Direct Run: Edit `main.py`

The easiest local workflow is:

1. Open `main.py`.
2. Edit the top `用户参数区` globals such as `RUN_MODE`, `PORTS`,
   `F_START`, `F_STOP`, `LINEAR_LOSS_START_DB`, `MODIFY_INPUT_FILE`, and
   `MODIFY_TARGETS`. For hand drawing, set `RUN_MODE = "draw"` and edit
   `DRAW_LOSS_MIN_DB`, `DRAW_LOSS_MAX_DB`, and optional `DRAW_CONTROL_POINTS`.
3. Run:

```bash
python3 main.py
```

With the default settings, this creates a Touchstone file and displays the S
parameter plots in matplotlib windows:

- `examples/linear_configured.s2p`

By default the plots are shown interactively rather than saved as PNG photos.
To save PNGs too, set this at the top of `main.py`:

```python
SAVE_PLOT_FILES = True
```

To run without opening plot windows, set:

```python
SHOW_PLOTS = False
```

On macOS, you can also double-click `run.command`. It starts the WebView desktop
interface and prefers the project `.venv` when available. Automated no-window
runs continue to use `main.py`.

Every run writes `last_run_log.txt` in the project folder. If local execution
fails, this file records the Python executable, current directory, arguments,
and exit code/error.

Command-line usage is also available:

```bash
python3 main.py --help
```

## Mode 1: Linear Insertion Loss

```bash
python3 main.py linear \
  --ports 2 \
  --f-start 10MHz \
  --f-stop 40GHz \
  --points 801 \
  --loss-start-db 0.2 \
  --loss-stop-db 20 \
  --delay-ps 80 \
  --output examples/linear_demo.s2p
```

For S2P, generated `S11=S22` and `S12=S21`. If you pass only one S2P through
path such as `--through-pair S21`, the reciprocal path is still generated so
`S12=S21` remains true. For S4P, the default model is two independent
reciprocal lanes: `S21/S12` and `S43/S34`.

## Mode 2: Protocol Formula Insertion Loss

The protocol formula is:

```text
loss_db = a*f + b*sqrt(f) + c
```

`f` uses `--model-frequency-unit`, defaulting to GHz. The coefficients therefore
depend on the selected frequency unit.

```bash
python3 main.py formula \
  --ports 4 \
  --f-start 10MHz \
  --f-stop 40GHz \
  --points 801 \
  --a 0.08 \
  --b 0.6 \
  --c 0.1 \
  --model-frequency-unit ghz \
  --delay-ps 80 \
  --output examples/formula_demo.s4p
```

Use `--through-pair` to select another 4-port convention, for example:

```bash
python3 main.py formula --ports 4 --a 0.08 --b 0.6 --c 0.1 \
  --through-pair S31 --through-pair S13 --through-pair S42 --through-pair S24 \
  --output examples/formula_alt_ports.s4p
```

## Mode 3: Smoothly Modify Imported S-Parameters

This mode imports an existing `.sNp`, then adjusts selected insertion-loss paths
to requested loss values at selected frequencies.

It does not make a single-point discontinuous edit. Instead, it computes a
shape-preserving dB correction curve through the requested points. The curve
cannot overshoot the neighboring correction controls. The phase of each
modified S-parameter is preserved from the imported file.

```bash
python3 main.py modify \
  --input measured.s2p \
  --target 5GHz:6.5 \
  --target 12GHz:12.0 \
  --pair S21 \
  --pair S12 \
  --smoothness 0.12 \
  --output tuned.s2p
```

Targets can also be comma-separated:

```bash
python3 main.py modify --input measured.s2p \
  --target "5GHz:6.5,12GHz:12.0,20GHz:18.0" \
  --output tuned.s2p
```

By default, target frequencies that are missing from the imported file are
inserted by interpolating magnitude and unwrapped phase. Use
`--no-insert-targets` to keep the original frequency grid; in that case the
report shows the interpolated achieved value at the requested frequency.

`--smoothness` controls the shape-preserving curve tension: larger values retain
more of the limited local slope, while smaller values flatten the curve near
control points. It no longer controls an unconstrained radial-basis width.

The imported matrix is checked before editing. A non-passive source is reported
as an input-file error. After fitting, non-target samples that would exceed
`sigma_max = 1` are contracted toward the original matrix; feasible target
samples remain exact. A target that is itself non-passive is rejected with its
frequency and singular value instead of being silently changed.

Target frequencies must be inside the imported sweep range. Duplicate target
frequencies with conflicting loss values are rejected. Targets that are too
close to each other or too close to a sweep edge are also rejected because they
would require an abrupt local correction rather than a smooth insertion-loss
change.

## Mode 4: Hand-Drawn Insertion Loss

This mode lets you set the frequency span first, then draw the insertion-loss
shape in a matplotlib window. The drawing axis follows the usual S-parameter
magnitude convention: 0 dB is at the top, and insertion loss is drawn downward
on the negative dB axis. The clicked points are sorted by frequency and, by
default, fitted with a smooth shape-preserving cubic curve. The generated curve
still passes through the drawn points, but the points between them are filled
with a continuous-slope fit instead of hard straight segments.

Each drawn control frequency is inserted into the output frequency axis before
the Touchstone file is written. That means a control point drawn at, for
example, 1.5 GHz is present as a real row in the output file even if the
original generated sweep points were only 1 GHz, 2 GHz, and 3 GHz.

If the first or last clicked point is not exactly on the sweep edge, that end
loss is held constant to the edge instead of extrapolating an abrupt slope.
Control points that are too close together or imply an extremely steep local
loss change are rejected because even a smoothed fit would still behave like a
near-vertical jump.

In `main.py`, use:

```python
RUN_MODE = "draw"
F_START = "10MHz"
F_STOP = "40GHz"
POINTS = 801
DRAW_CONTROL_POINTS = []
DRAW_LOSS_MIN_DB = -40.0
DRAW_LOSS_MAX_DB = 0.0
DRAW_FIT = "smooth"
DRAW_FIT_DOMAIN = "linear"
DRAW_MIN_SPACING_FRACTION = 1e-4
DRAW_MAX_SLOPE_DB_PER_SPAN = 500.0
```

Run `python3 main.py`. In the drawing window:

- Left click adds a control point.
- Right click removes the most recently added point.
- Press Enter or close the window to generate the Touchstone file.

For scripted runs or tests, provide points directly and the drawing window is
skipped:

```bash
python3 main.py draw \
  --ports 2 \
  --f-start 1GHz \
  --f-stop 3GHz \
  --points 5 \
  --draw-point 1GHz:-1.0 \
  --draw-point 2GHz:-3.0 \
  --draw-point 3GHz:-2.0 \
  --output examples/drawn_demo.s2p
```

For draw mode, scripted points use negative magnitude dB. For example,
`2GHz:-3.0` means the generated through path is `-3 dB` at 2 GHz.

Use `--draw-fit linear` only when you explicitly want the old point-to-point
straight-line behavior. For very wide sweeps, `--draw-fit-domain log` can make
the smoothing follow log-frequency spacing.

`--draw-fit-domain linear` fits against the raw frequency values, so equal
frequency intervals receive equal smoothing weight. `--draw-fit-domain log`
fits against `log10(frequency)`, so equal ratios such as 1 GHz to 2 GHz and
10 GHz to 20 GHz are treated more similarly. This changes the generated curve,
not the plot window's axis scale.

If you deliberately need very close or very steep control points, tune
`--draw-min-spacing-fraction` and `--draw-max-slope-db-per-span`, but the
defaults are chosen to avoid accidental nonphysical jumps.

## Touchstone Support Notes

The reader supports full-matrix `.sNp` files with `RI`, `MA`, or `DB` data. It
uses the common Touchstone 1.x S2P order `S11 S21 S12 S22`, and also supports
Touchstone 2.0 and 2.1 `[Two-Port Data Order]` for S2P files. Option-line fields
are parsed by category, so legal optional fields are not tied to one token
position. See the official
[Touchstone 2.1 specification](https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf).

For 2.x input, the reader requires `[Version]` first, then the option line,
`[Number of Ports]`, an explicit `[Two-Port Data Order]` for S2P, `[Network
Data]`, and `[End]`. The 1.x writer limits every physical line to four complex
parameter pairs, including matrices with five or more ports.

Unsupported Touchstone 2.x constructs that can change interpretation or cannot
be preserved by this scalar-impedance writer, such as `[Reference]`, are
rejected with a clear error instead of being silently ignored.

## Open-source references used for the hardening plan

- [scikit-rf](https://github.com/scikit-rf/scikit-rf) is the differential
  validation reference for Touchstone I/O, network algebra, passivity, and
  vector fitting. It remains an optional validation dependency and is enabled
  only on Python versions supported by the pinned scikit-rf release.
- [PyBERT](https://github.com/capn-freako/PyBERT) is a useful reference for a
  SerDes-oriented end-to-end channel workflow and user-facing plots.
- [SignalIntegrity](https://github.com/TeledyneLeCroy/SignalIntegrity) is a
  reference for schematic/topology-oriented signal-integrity workflows.
- [Qucs-S](https://github.com/ra3xdh/qucs_s) and
  [openEMS](https://github.com/thliebig/openEMS-Project) illustrate the boundary
  between a curve generator, a circuit simulator, and an EM solver. Their GPL
  code is not copied into this project.

## Plots

Every run writes the Touchstone file. Magnitude and phase S-parameter plots are
then handled according to the selected workflow:

- Direct `python3 main.py` mode displays plots interactively by default and
  does not save PNG files unless `SAVE_PLOT_FILES = True`.
- CLI commands save PNG files by default for script/batch compatibility.
- CLI commands can also display plot windows:

```bash
python3 main.py linear --loss-start-db 0.2 --loss-stop-db 20 --show-plot
```

For S2P the plots include `S11`, `S12`, `S21`, and `S22`. For S4P the plots
include all sixteen S-parameters.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 图片曲线修正

0.6.0 保留图框、排除区、原图取色、锚点修线和方案保存恢复；识别结果仍应在
界面中复核，尤其是同色交叉、文字干扰和深尖峰/凹口。实现与有限回归范围见
[图片曲线保真与纠错](docs/image_fidelity.md)。
