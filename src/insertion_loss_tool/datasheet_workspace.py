"""Bounded state controller for the datasheet image-composition workspace."""

from __future__ import annotations

import base64
import copy
import hashlib
import mimetypes
import re
import threading
from collections.abc import Iterable, Mapping
from pathlib import Path

import numpy as np

from .datasheet import (
    CurveResource,
    FrequencyGridResult,
    compose_frequency_grid,
    mixed_mode_to_single_ended,
    mixed_mode_parameter_names,
    normalize_parameter_name,
    transpose_parameter,
)
from .datasheet_digitizer import DigitizedCurve, analyze_plot_image, digitize_plot_image
from .image_frequency import parse_image_frequency
from .models import COMMON_PORT_COUNTS, parse_frequency
from .touchstone import TouchstoneData
from .trace_recovery_policy import MATCHED_FALLBACK_DB


_DISPLAY_COLORS = {
    "Dark blue": "深蓝",
    "Red": "红",
    "Green": "绿",
    "Light blue": "浅蓝",
    "Gray": "灰",
}
MAX_IMAGES = 32
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 128 * 1024 * 1024
MAX_FREQUENCY_POINTS = 200_000
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _format_frequency(value_hz: float | None) -> str:
    if value_hz is None:
        return ""
    for unit, scale in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if value_hz >= scale:
            return f"{value_hz / scale:g}{unit}"
    return f"{value_hz:g}Hz"


def _curve_review_payload(curve: DigitizedCurve) -> dict[str, object]:
    """Serialize local review intervals with enough points for an overlay."""

    regions: list[dict[str, object]] = []
    points = curve.pixel_points
    for region in curve.review_regions:
        context = 2.0
        selected = points[
            (points[:, 0] >= region.start_x - context)
            & (points[:, 0] <= region.end_x + context)
        ]
        if selected.shape[0] < 2:
            x_values = np.asarray([region.start_x, region.end_x], dtype=np.float64)
            selected = np.column_stack(
                (
                    x_values,
                    np.interp(x_values, points[:, 0], points[:, 1]),
                )
            )
        stride = max(1, int(np.ceil(selected.shape[0] / 120)))
        regions.append(
            {
                "start_x": round(float(region.start_x), 2),
                "end_x": round(float(region.end_x), 2),
                "reason": region.reason,
                "severity": region.severity,
                "samples": int(region.samples),
                "preview_points": np.round(selected[::stride], 2).tolist(),
            }
        )
    return {
        "visual_confidence": round(float(curve.visual_confidence), 3),
        "review_status": curve.review_status,
        "review_regions": regions,
    }


def _bounded_integer(value: object, minimum: int, maximum: int) -> int:
    """Parse a JS integer without accepting booleans, fractions, or coercions."""

    if isinstance(value, bool):
        raise ValueError("boolean is not an integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdecimal():
        parsed = int(value.strip())
    else:
        raise ValueError("invalid integer")
    if not minimum <= parsed <= maximum:
        raise ValueError("integer out of range")
    return parsed


def _parameter_names(port_count: int, family: str) -> tuple[str, ...]:
    if family == "single-ended":
        return tuple(
            f"S{out_port}{in_port}"
            for out_port in range(1, port_count + 1)
            for in_port in range(1, port_count + 1)
        )
    if family == "mixed-mode":
        return mixed_mode_parameter_names(port_count)
    raise ValueError("参数类型无效。")


def _is_reflection_parameter(parameter: str, family: str) -> bool:
    """Classify reflection without mistaking SDC/SCD mode conversion for it."""

    if family == "single-ended":
        return parameter[1] == parameter[2]
    return parameter[1:3] in {"DD", "CC"} and parameter[3] == parameter[4]


def _default_mappings(port_count: int, family: str = "single-ended") -> dict[str, str]:
    mappings: dict[str, str] = {}
    for parameter in _parameter_names(port_count, family):
        reflection = _is_reflection_parameter(parameter, family)
        mappings[parameter] = "反射 -20 dB" if reflection else "耦合 -80 dB"
    return mappings


def _new_network(index: int, port_count: int) -> dict[str, object]:
    return {
        "name": f"输出 {index + 1}",
        "output": f"output_{index + 1}.s{port_count}p",
        "port_count": port_count,
        "parameter_family": "single-ended",
        "phase": "zero-degree",
        "reciprocal": True,
        "frequency_policy": {
            "mode": "intersection",
            "start": "",
            "stop": "",
            "step": "",
            "allow_fill": False,
        },
        "mappings": _default_mappings(port_count),
    }


class DatasheetWorkspace:
    """Own images, mappings, and frequency policies independently of the app shell."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._images: list[Path] = []
        self._image_hashes: set[str] = set()
        self._image_payloads: list[dict[str, object]] = []
        self._axis_revisions: list[int] = []
        self._digitized_curve_data: list[dict[str, tuple[np.ndarray, np.ndarray]]] = []
        self._active_digitizations = 0
        self._total_image_bytes = 0
        self._networks = [_new_network(0, 4)]

    def payload(self) -> dict[str, object]:
        """Return the one initial full snapshot, including cached image pixels."""

        with self._lock:
            return {
                "images": copy.deepcopy(self._image_payloads),
                **self._network_state_payload(),
            }

    def register_images(self, paths: Iterable[Path]) -> dict[str, object]:
        """Append bounded local images and return only newly added pixel payloads."""

        added: list[dict[str, object]] = []
        warnings: list[str] = []
        for raw_path in paths:
            path = Path(raw_path).expanduser().resolve()
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                warnings.append(f"已跳过不支持的文件：{path.name}")
                continue
            try:
                byte_count = path.stat().st_size
            except OSError:
                warnings.append(f"无法读取：{path.name}")
                continue
            if byte_count > MAX_IMAGE_BYTES:
                warnings.append(f"图片超过 20 MB：{path.name}")
                continue
            with self._lock:
                if path in self._images:
                    warnings.append(f"图片已存在：{path.name}")
                    continue
                if len(self._images) >= MAX_IMAGES:
                    warnings.append("图片数量已达 32 张上限。")
                    break
                if self._total_image_bytes + byte_count > MAX_TOTAL_IMAGE_BYTES:
                    warnings.append("图片总大小已达 128 MB 上限。")
                    break
            try:
                image_bytes = path.read_bytes()
            except OSError:
                warnings.append(f"无法读取：{path.name}")
                continue
            if len(image_bytes) > MAX_IMAGE_BYTES:
                warnings.append(f"图片超过 20 MB：{path.name}")
                continue
            digest = hashlib.sha256(image_bytes).hexdigest()
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            encoded = base64.b64encode(image_bytes).decode("ascii")
            with self._lock:
                if path in self._images or digest in self._image_hashes:
                    warnings.append(f"图片已存在：{path.name}")
                    continue
                if len(self._images) >= MAX_IMAGES:
                    warnings.append("图片数量已达 32 张上限。")
                    break
                if self._total_image_bytes + len(image_bytes) > MAX_TOTAL_IMAGE_BYTES:
                    warnings.append("图片总大小已达 128 MB 上限。")
                    break
                payload: dict[str, object] = {
                    "index": len(self._images) + 1,
                    "name": path.name,
                    "data_url": f"data:{mime};base64,{encoded}",
                    "sha256": digest,
                    "byte_count": len(image_bytes),
                    "candidates": 0,
                    "axis": {
                        "status": "required",
                        "source": "none",
                        "start": "",
                        "stop": "",
                        "step": "",
                        "spacing": "linear",
                    },
                    "digitization": {
                        "status": "axes-required",
                        "message": "Axes required.",
                    },
                    "curves": [],
                }
                self._images.append(path)
                self._image_hashes.add(digest)
                self._image_payloads.append(payload)
                self._axis_revisions.append(0)
                self._digitized_curve_data.append({})
                self._total_image_bytes += len(image_bytes)
                added.append(copy.deepcopy(payload))
        with self._lock:
            return {
                "ok": True,
                "images_added": added,
                "warnings": warnings,
                "image_count": len(self._images),
                **self._network_state_payload(),
            }

    def remove_image(self, index: object) -> dict[str, object]:
        """Remove one image and keep every surviving image source address valid."""

        try:
            with self._lock:
                if self._active_digitizations:
                    return {"ok": False, "error": "图片识别进行中，暂不能删除图片。"}
                image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                removed_number = image_index + 1
                removed = self._image_payloads[image_index]
                self._total_image_bytes -= int(removed["byte_count"])
                self._image_hashes.discard(str(removed["sha256"]))
                del self._images[image_index]
                del self._image_payloads[image_index]
                del self._axis_revisions[image_index]
                del self._digitized_curve_data[image_index]

                source_pattern = re.compile(r"^图(\d+)(\s.+)$")
                for network in self._networks:
                    mappings = network["mappings"]
                    for parameter, source in tuple(mappings.items()):
                        match = source_pattern.match(str(source))
                        if not match:
                            continue
                        source_number = int(match.group(1))
                        if source_number == removed_number:
                            mappings[parameter] = "未知"
                        elif source_number > removed_number:
                            mappings[parameter] = f"图{source_number - 1}{match.group(2)}"

                for next_index, image in enumerate(self._image_payloads, start=1):
                    image["index"] = next_index

                return {
                    "ok": True,
                    "image_removed": removed_number,
                    "image_count": len(self._images),
                    "image_updates": [
                        self._image_metadata_payload(next_index)
                        for next_index in range(len(self._image_payloads))
                    ],
                    **self._network_state_payload(),
                }
        except (ValueError, IndexError):
            return {"ok": False, "error": "图片无效。"}

    def analyze_image(self, index: object) -> dict[str, object]:
        """Populate editable defaults from visible labels without inventing data."""

        active = False
        try:
            with self._lock:
                image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                path = self._images[image_index]
                digest = str(self._image_payloads[image_index]["sha256"])
                self._axis_revisions[image_index] += 1
                revision = self._axis_revisions[image_index]
                self._image_payloads[image_index]["digitization"] = {
                    "status": "analyzing",
                    "message": "Analyzing image.",
                }
                self._active_digitizations += 1
                active = True
            result = analyze_plot_image(path)
            calibration = result.calibration
            points = None
            step_hz = calibration.step_hz
            axis_source = "detected"
            derived_pixel_step = False
            if (
                step_hz is None
                and calibration.start_hz is not None
                and calibration.stop_hz is not None
                and calibration.stop_hz > calibration.start_hz
                and calibration.spacing == "linear"
            ):
                pixel_points = result.plot_box[2] - result.plot_box[0] + 1
                if 2 <= pixel_points <= MAX_FREQUENCY_POINTS:
                    points = pixel_points
                    step_hz = (
                        calibration.stop_hz - calibration.start_hz
                    ) / (pixel_points - 1)
                    axis_source = "detected-pixel"
                    derived_pixel_step = True
            if (
                calibration.start_hz is not None
                and calibration.stop_hz is not None
                and step_hz is not None
                and calibration.stop_hz > calibration.start_hz
                and points is None
            ):
                points = int(
                    np.floor(
                        (calibration.stop_hz - calibration.start_hz)
                        / step_hz
                    )
                ) + 1
                if not 2 <= points <= MAX_FREQUENCY_POINTS:
                    points = None
            ready = (
                points is not None
                and calibration.start_hz is not None
                and calibration.stop_hz is not None
                and calibration.y_min_db is not None
                and calibration.y_max_db is not None
                and calibration.spacing in {"linear", "log"}
            )
            preview_curves: list[dict[str, object]] = []
            preview_warning: str | None = None
            if not ready:
                try:
                    preview_result = digitize_plot_image(
                        path,
                        start_hz=1.0,
                        stop_hz=2.0,
                        y_min_db=-1.0,
                        y_max_db=0.0,
                        run_ocr=False,
                        spacing="linear",
                    )
                    for curve_index, curve in enumerate(preview_result.curves):
                        curve_id = chr(ord("A") + curve_index)
                        color = _DISPLAY_COLORS.get(curve.color, curve.color)
                        stride = max(
                            1, int(np.ceil(curve.pixel_points.shape[0] / 800))
                        )
                        preview_curves.append(
                            {
                                "id": curve_id,
                                "trace_number": curve_index + 1,
                                "color": color,
                                "parameter": calibration.detected_parameter or "自动",
                                "calibrated": False,
                                "samples": 0,
                                "source_samples": int(curve.frequency_hz.size),
                                "covered_samples": 0,
                                "unresolved_samples": 0,
                                "observed_samples": int(
                                    curve.observed_samples or curve.frequency_hz.size
                                ),
                                "shared_overlap_samples": int(
                                    curve.shared_overlap_samples
                                ),
                                "interpolated_samples": int(
                                    curve.interpolated_samples
                                ),
                                "confidence": round(float(curve.confidence), 3),
                                **_curve_review_payload(curve),
                                "rgb": list(curve.rgb),
                                "preview_points": np.round(
                                    curve.pixel_points[::stride], 2
                                ).tolist(),
                            }
                        )
                except ValueError as exc:
                    preview_warning = str(exc)
            missing = list(calibration.missing)
            if derived_pixel_step:
                missing = [name for name in missing if name != "step"]
            axis: dict[str, object] = {
                "status": "ready" if ready else "review",
                "source": axis_source,
                "start": _format_frequency(calibration.start_hz),
                "stop": _format_frequency(calibration.stop_hz),
                "step": _format_frequency(step_hz),
                "spacing": calibration.spacing or "linear",
                "y_min_db": calibration.y_min_db,
                "y_max_db": calibration.y_max_db,
                "missing": missing,
            }
            if calibration.start_hz is not None:
                axis["start_hz"] = calibration.start_hz
            if calibration.stop_hz is not None:
                axis["stop_hz"] = calibration.stop_hz
            if step_hz is not None:
                axis["step_hz"] = step_hz
            if points is not None:
                axis["points"] = points
            with self._lock:
                if (
                    self._images[image_index] != path
                    or self._image_payloads[image_index]["sha256"] != digest
                    or self._axis_revisions[image_index] != revision
                ):
                    self._active_digitizations -= 1
                    active = False
                    return {"ok": False, "error": "Image changed during analysis."}
                self._invalidate_image_curves(image_index)
                image = self._image_payloads[image_index]
                if preview_curves:
                    image["curves"] = preview_curves
                    image["candidates"] = len(preview_curves)
                image["axis"] = axis
                image["digitization"] = {
                    "status": "ready" if ready else "review",
                    "message": (
                        "Detected"
                        if ready
                        else (
                            f"{len(preview_curves)} trace candidate"
                            f"{'s' if len(preview_curves) != 1 else ''} found; "
                            "set the missing axes, then choose Digitize."
                            if preview_curves
                            else "Set the missing axes, then choose Digitize."
                        )
                    ),
                    "candidate_status": "preview" if preview_curves else "none",
                    "detected_parameter": calibration.detected_parameter,
                    "parameter_analysis_complete": True,
                    "plot_box": list(result.plot_box),
                    "image_width": result.image_width,
                    "image_height": result.image_height,
                    "warnings": [
                        *calibration.warnings,
                        *(
                            [
                                "Sweep step is not printed; native plot-pixel spacing is used as an editable default."
                            ]
                            if derived_pixel_step
                            else []
                        ),
                        *([preview_warning] if preview_warning else []),
                    ],
                }
                self._active_digitizations -= 1
                active = False
                return {
                    "ok": True,
                    "auto_digitize": ready,
                    "image_update": self._image_metadata_payload(image_index),
                    **self._network_state_payload(),
                }
        except Exception as exc:
            message = str(exc) if isinstance(exc, (ValueError, IndexError)) else "Image analysis failed."
            with self._lock:
                if active:
                    self._active_digitizations -= 1
                try:
                    image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                    self._image_payloads[image_index]["digitization"] = {
                        "status": "review",
                        "message": message or "Review axes manually.",
                    }
                    return {
                        "ok": False,
                        "error": message,
                        "image_update": self._image_metadata_payload(image_index),
                        **self._network_state_payload(),
                    }
                except (ValueError, IndexError):
                    return {"ok": False, "error": message}

    def set_image_frequency(
        self,
        index: object,
        start: object,
        stop: object,
        step: object,
        spacing: object = "linear",
    ) -> dict[str, object]:
        try:
            with self._lock:
                image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                spacing_value = str(spacing).strip().lower()
                if spacing_value not in {"linear", "log"}:
                    return {"ok": False, "error": "频率刻度必须是线性或对数。"}
                try:
                    start_hz = parse_image_frequency(start, allow_zero=True)
                except ValueError:
                    return {
                        "ok": False,
                        "error": "图片起始频率必须是非负数；不带单位时按 GHz 处理。",
                    }
                try:
                    stop_hz = parse_image_frequency(stop)
                except ValueError:
                    return {
                        "ok": False,
                        "error": "图片终止频率必须大于 0；不带单位时按 GHz 处理。",
                    }
                try:
                    step_hz = parse_image_frequency(step)
                except ValueError:
                    return {
                        "ok": False,
                        "error": "图片输出步进必须大于 0；不带单位时按 GHz 处理。",
                    }
                if stop_hz <= start_hz:
                    return {"ok": False, "error": "终止频率必须大于起始频率。"}
                if spacing_value == "log" and start_hz <= 0:
                    return {"ok": False, "error": "对数频率必须从正频率开始。"}
                points = int(np.floor((stop_hz - start_hz) / step_hz)) + 1
                if points < 2 or points > MAX_FREQUENCY_POINTS:
                    return {"ok": False, "error": "图片频点数量必须是 2–200000。"}
                self._axis_revisions[image_index] += 1
                self._image_payloads[image_index]["axis"] = {
                    "status": "ready",
                    "source": "manual",
                    "start": str(start).strip(),
                    "stop": str(stop).strip(),
                    "step": str(step).strip(),
                    "spacing": spacing_value,
                    "start_hz": start_hz,
                    "stop_hz": stop_hz,
                    "step_hz": step_hz,
                    "points": points,
                }
                self._invalidate_image_curves(image_index)
                prior_digitization = dict(
                    self._image_payloads[image_index].get("digitization", {})
                )
                self._image_payloads[image_index]["digitization"] = {
                    "status": "ready",
                    "message": "Ready to digitize.",
                    "detected_parameter": prior_digitization.get(
                        "detected_parameter"
                    ),
                    "parameter_analysis_complete": bool(
                        prior_digitization.get("parameter_analysis_complete")
                    ),
                }
                return {
                    "ok": True,
                    "image_update": self._image_metadata_payload(image_index),
                    **self._network_state_payload(),
                }
        except (ValueError, IndexError):
            return {"ok": False, "error": "图片频率设置无效。"}

    def digitize_image(
        self,
        index: object,
        y_min_db: object,
        y_max_db: object,
    ) -> dict[str, object]:
        """Digitize one calibrated image and expose only recovered traces."""

        active = False
        try:
            minimum_db = float(str(y_min_db).strip())
            maximum_db = float(str(y_max_db).strip())
            if not np.isfinite(minimum_db) or not np.isfinite(maximum_db):
                raise ValueError
            if maximum_db <= minimum_db:
                return {"ok": False, "error": "Y 轴最大值必须大于最小值。"}
            with self._lock:
                image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                axis = dict(self._image_payloads[image_index]["axis"])
                if axis.get("status") != "ready":
                    return {"ok": False, "error": "请先完整设置图片坐标轴。"}
                axis.update({"y_min_db": minimum_db, "y_max_db": maximum_db})
                self._image_payloads[image_index]["axis"] = axis
                self._axis_revisions[image_index] += 1
                path = self._images[image_index]
                digest = str(self._image_payloads[image_index]["sha256"])
                prior_digitization = dict(
                    self._image_payloads[image_index].get("digitization", {})
                )
                prior_parameter = str(
                    prior_digitization.get("detected_parameter") or ""
                ).strip()
                parameter_analysis_complete = bool(
                    prior_digitization.get("parameter_analysis_complete")
                )
                axis_revision = self._axis_revisions[image_index]
                self._active_digitizations += 1
                active = True
            result = digitize_plot_image(
                path,
                start_hz=float(axis["start_hz"]),
                stop_hz=float(axis["stop_hz"]),
                y_min_db=minimum_db,
                y_max_db=maximum_db,
                # Image analysis has already read the title in the normal Add flow.
                # Reuse it so auto-digitization does not launch Tesseract twice.
                run_ocr=not parameter_analysis_complete,
                spacing=str(axis.get("spacing", "linear")),
                parameter_hint=prior_parameter or None,
            )
            detected_parameter = result.detected_parameter or prior_parameter or None
            curves: list[dict[str, object]] = []
            curve_data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
            grid_points = int(axis["points"])
            if str(axis.get("spacing", "linear")) == "log":
                display_frequency_hz = np.geomspace(
                    float(axis["start_hz"]), float(axis["stop_hz"]), grid_points
                )
            else:
                display_frequency_hz = float(axis["start_hz"]) + np.arange(
                    grid_points, dtype=np.float64
                ) * float(axis["step_hz"])
            for curve_index, curve in enumerate(result.curves):
                curve_id = chr(ord("A") + curve_index)
                color = _DISPLAY_COLORS.get(curve.color, curve.color)
                parameter = detected_parameter or "自动"
                stride = max(1, int(np.ceil(curve.pixel_points.shape[0] / 800)))
                preview = curve.pixel_points[::stride]
                covered_samples = int(
                    np.count_nonzero(
                        (display_frequency_hz >= curve.frequency_hz[0])
                        & (display_frequency_hz <= curve.frequency_hz[-1])
                    )
                )
                curves.append(
                    {
                        "id": curve_id,
                        "trace_number": curve_index + 1,
                        "color": color,
                        "parameter": parameter,
                        "calibrated": True,
                        # Every destination channel uses this calibrated grid.
                        # Keep raw evidence separate so interpolation is never
                        # presented as pixels that were actually observed.
                        "samples": grid_points,
                        "source_samples": int(curve.frequency_hz.size),
                        "covered_samples": covered_samples,
                        "unresolved_samples": grid_points - covered_samples,
                        "observed_samples": int(
                            curve.observed_samples or curve.frequency_hz.size
                        ),
                        "shared_overlap_samples": int(
                            curve.shared_overlap_samples
                        ),
                        "interpolated_samples": int(curve.interpolated_samples),
                        "confidence": round(float(curve.confidence), 3),
                        **_curve_review_payload(curve),
                        "rgb": list(curve.rgb),
                        "preview_points": np.round(preview, 2).tolist(),
                    }
                )
                curve_data[curve_id] = (curve.frequency_hz.copy(), curve.magnitude_db.copy())
            with self._lock:
                if (
                    self._images[image_index] != path
                    or self._image_payloads[image_index]["sha256"] != digest
                    or self._axis_revisions[image_index] != axis_revision
                ):
                    self._active_digitizations -= 1
                    active = False
                    return {
                        "ok": False,
                        "error": "图片或校准在识别期间已改变，请重试。",
                        "image_update": self._image_metadata_payload(image_index),
                        **self._network_state_payload(),
                    }
                self._invalidate_image_curves(image_index)
                self._digitized_curve_data[image_index] = curve_data
                image = self._image_payloads[image_index]
                image["curves"] = curves
                image["candidates"] = len(curves)
                image["axis"] = axis
                image["digitization"] = {
                    "status": "digitized",
                    "message": f"{len(curves)} traces available · magnitude only",
                    # Multiple traces are valid input.  They remain available to
                    # every compatible mapping, but are never chosen on the
                    # user's behalf when the image does not identify one uniquely.
                    "selection": (
                        "automatic"
                        if len(curves) == 1 and detected_parameter
                        else "optional"
                    ),
                    "axis_source": str(axis.get("source", "manual")),
                    "plot_box": list(result.plot_box),
                    "image_width": result.image_width,
                    "image_height": result.image_height,
                    "detected_parameter": detected_parameter,
                    "parameter_analysis_complete": True,
                    "warnings": list(result.warnings),
                }
                self._apply_detected_parameter(image_index, detected_parameter)
                self._active_digitizations -= 1
                active = False
                return {
                    "ok": True,
                    "image_update": self._image_metadata_payload(image_index),
                    **self._network_state_payload(),
                }
        except Exception as exc:
            message = (
                str(exc) or "图片识别失败。"
                if isinstance(exc, (ValueError, IndexError))
                else "Image digitization failed."
            )
            with self._lock:
                if active:
                    self._active_digitizations -= 1
                    active = False
                try:
                    image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                    self._invalidate_image_curves(image_index)
                    self._image_payloads[image_index]["digitization"] = {
                        "status": "failed",
                        "message": message,
                    }
                    return {
                        "ok": False,
                        "error": message,
                        "image_update": self._image_metadata_payload(image_index),
                        **self._network_state_payload(),
                    }
                except (ValueError, IndexError):
                    pass
            return {"ok": False, "error": message}

    def digitize_image_with_axis(
        self,
        index: object,
        y_top_db: object,
        y_bottom_db: object,
        convention: object = "magnitude",
    ) -> dict[str, object]:
        """Digitize values as printed, including positive-down loss axes."""

        try:
            top_db = float(str(y_top_db).strip())
            bottom_db = float(str(y_bottom_db).strip())
            if not np.isfinite(top_db) or not np.isfinite(bottom_db):
                raise ValueError
            convention_value = str(convention).strip().lower()
            if convention_value == "magnitude":
                if top_db <= bottom_db:
                    return {
                        "ok": False,
                        "error": "幅度 dB 的上边界必须大于下边界。",
                    }
                minimum_db, maximum_db = bottom_db, top_db
            elif convention_value == "positive-loss":
                if bottom_db <= top_db:
                    return {
                        "ok": False,
                        "error": "正插损 dB 的下边界必须大于上边界。",
                    }
                minimum_db, maximum_db = -bottom_db, -top_db
            else:
                return {"ok": False, "error": "Y 轴数值约定无效。"}

            with self._lock:
                image_index = _bounded_integer(
                    index, 0, len(self._image_payloads) - 1
                )
                axis = dict(self._image_payloads[image_index]["axis"])
                axis.update(
                    {
                        "y_convention": convention_value,
                        "y_top_db": top_db,
                        "y_bottom_db": bottom_db,
                    }
                )
                self._image_payloads[image_index]["axis"] = axis
            return self.digitize_image(index, minimum_db, maximum_db)
        except (ValueError, IndexError):
            return {"ok": False, "error": "Y 轴设置无效。"}

    def set_curve_parameter(
        self, index: object, curve_id: object, parameter: object
    ) -> dict[str, object]:
        try:
            with self._lock:
                image_index = _bounded_integer(index, 0, len(self._image_payloads) - 1)
                curve_name = str(curve_id).strip().upper()
                value = str(parameter).strip()
                normalized = "自动" if value == "自动" else normalize_parameter_name(value)
                curves = self._image_payloads[image_index]["curves"]
                for curve in curves:
                    if curve["id"] == curve_name:
                        old_suffix = curve["color"] if curve["parameter"] == "自动" else curve["parameter"]
                        old_source = f"图{image_index + 1} {curve_name} · {old_suffix}"
                        curve["parameter"] = normalized
                        new_suffix = curve["color"] if normalized == "自动" else normalized
                        new_source = f"图{image_index + 1} {curve_name} · {new_suffix}"
                        for network in self._networks:
                            mappings = network["mappings"]
                            for name, source in tuple(mappings.items()):
                                if source == old_source:
                                    mappings[name] = (
                                        new_source
                                        if new_source in self._mapping_options()
                                        else "未知"
                                    )
                            self._auto_apply_compatible_sources(network)
                        return {
                            "ok": True,
                            "image_update": self._image_metadata_payload(image_index),
                            **self._network_state_payload(),
                        }
                return {"ok": False, "error": "曲线编号无效。"}
        except (ValueError, IndexError):
            return {"ok": False, "error": "图片或参数无效。"}

    def set_network_count(self, count: object) -> dict[str, object]:
        try:
            requested = _bounded_integer(count, 1, 6)
        except ValueError:
            return {"ok": False, "error": "输出数量必须是 1–6。"}
        with self._lock:
            while len(self._networks) < requested:
                network = _new_network(len(self._networks), 2)
                self._auto_apply_compatible_sources(network)
                self._networks.append(network)
            del self._networks[requested:]
            return {"ok": True, **self._network_state_payload()}

    def set_network_ports(self, index: object, ports: object) -> dict[str, object]:
        try:
            with self._lock:
                network_index = _bounded_integer(index, 0, len(self._networks) - 1)
                port_count = _bounded_integer(ports, 1, 8)
                if port_count not in COMMON_PORT_COUNTS:
                    choices = "、".join(str(value) for value in COMMON_PORT_COUNTS)
                    return {"ok": False, "error": f"端口必须是 {choices}。"}
                network = self._networks[network_index]
                old_count = int(network["port_count"])
                family = str(network["parameter_family"])
                if family == "mixed-mode" and port_count % 2:
                    return {"ok": False, "error": "混合模需要偶数个物理端口。"}
                old_mappings = dict(network["mappings"])
                mappings = _default_mappings(port_count, family)
                for parameter in mappings:
                    if parameter in old_mappings:
                        mappings[parameter] = old_mappings[parameter]
                network["port_count"] = port_count
                network["mappings"] = mappings
                old_default = f"output_{network_index + 1}.s{old_count}p"
                if network["output"] == old_default:
                    network["output"] = f"output_{network_index + 1}.s{port_count}p"
                if bool(network["reciprocal"]):
                    self._link_network(network)
                self._auto_apply_compatible_sources(network)
                return {"ok": True, "network": self._network_payload(network_index), **self._network_state_payload()}
        except (ValueError, IndexError):
            return {"ok": False, "error": "输出或端口无效。"}

    def set_network_parameter_family(self, index: object, family: object) -> dict[str, object]:
        value = str(family)
        if value not in {"single-ended", "mixed-mode"}:
            return {"ok": False, "error": "参数类型无效。"}
        try:
            with self._lock:
                network_index = _bounded_integer(index, 0, len(self._networks) - 1)
                network = self._networks[network_index]
                port_count = int(network["port_count"])
                if value == "mixed-mode" and port_count % 2:
                    return {"ok": False, "error": "混合模需要偶数个物理端口。"}
                network["parameter_family"] = value
                network["mappings"] = _default_mappings(port_count, value)
                if bool(network["reciprocal"]):
                    self._link_network(network)
                self._auto_apply_compatible_sources(network)
                return {"ok": True, "network": self._network_payload(network_index), **self._network_state_payload()}
        except (ValueError, IndexError):
            return {"ok": False, "error": "输出无效。"}

    def set_network_frequency_policy(
        self,
        index: object,
        mode: object,
        start: object = "",
        stop: object = "",
        step: object = "",
        allow_fill: object = False,
    ) -> dict[str, object]:
        if not isinstance(allow_fill, bool):
            return {"ok": False, "error": "补齐策略无效。"}
        value = str(mode).strip().lower()
        if value not in {"intersection", "manual", "union"}:
            return {"ok": False, "error": "频率范围策略无效。"}
        try:
            with self._lock:
                network_index = _bounded_integer(index, 0, len(self._networks) - 1)
                policy: dict[str, object] = {
                    "mode": value,
                    "start": str(start).strip(),
                    "stop": str(stop).strip(),
                    "step": str(step).strip(),
                    "allow_fill": allow_fill,
                }
                if value == "manual":
                    start_hz = parse_frequency(str(start))
                    stop_hz = parse_frequency(str(stop))
                    step_hz = parse_frequency(str(step))
                    if stop_hz <= start_hz:
                        return {"ok": False, "error": "终止频率必须大于起始频率。"}
                    grid = compose_frequency_grid(
                        [],
                        policy="manual",
                        manual_start_hz=start_hz,
                        manual_stop_hz=stop_hz,
                        manual_step_hz=step_hz,
                        max_points=MAX_FREQUENCY_POINTS,
                    )
                    policy.update(
                        start_hz=start_hz,
                        stop_hz=stop_hz,
                        step_hz=step_hz,
                        points=grid.points,
                    )
                network = self._networks[network_index]
                candidate = {**network, "frequency_policy": policy}
                coverage = self._network_coverage(candidate)
                if coverage.get("status") == "requires-fill" and not allow_fill:
                    return {"ok": False, "error": "该范围超出部分图片，需明确使用默认值补齐。"}
                if coverage.get("status") == "conflict":
                    return {"ok": False, "error": "所选图片没有共同频率范围。"}
                network["frequency_policy"] = policy
                return {"ok": True, "network": self._network_payload(network_index), **self._network_state_payload()}
        except (ValueError, IndexError) as error:
            message = str(error)
            if "不能整除" in message:
                return {"ok": False, "error": message}
            return {"ok": False, "error": "频率范围设置无效。"}

    def set_network_reciprocal(self, index: object, enabled: object) -> dict[str, object]:
        if not isinstance(enabled, bool):
            return {"ok": False, "error": "成对联动值无效。"}
        try:
            with self._lock:
                network_index = _bounded_integer(index, 0, len(self._networks) - 1)
                network = self._networks[network_index]
                network["reciprocal"] = enabled
                if enabled:
                    self._link_network(network)
                return {"ok": True, "network": self._network_payload(network_index), **self._network_state_payload()}
        except (ValueError, IndexError):
            return {"ok": False, "error": "输出无效。"}

    def set_mapping(self, index: object, parameter: object, source: object) -> dict[str, object]:
        try:
            with self._lock:
                network_index = _bounded_integer(index, 0, len(self._networks) - 1)
                network = self._networks[network_index]
                name = str(parameter).upper()
                value = str(source)
                mappings = network["mappings"]
                if name not in mappings:
                    return {"ok": False, "error": "S 参数无效。"}
                if value not in self._mapping_options():
                    return {"ok": False, "error": "曲线来源无效。"}
                mappings[name] = value
                if bool(network["reciprocal"]):
                    transpose = transpose_parameter(name)
                    if transpose in mappings:
                        mappings[transpose] = value
                return {"ok": True, "network": self._network_payload(network_index), **self._network_state_payload()}
        except (ValueError, IndexError):
            return {"ok": False, "error": "输出无效。"}

    def _source_options(self) -> list[str]:
        values = ["自动"]
        for image in self._image_payloads:
            if image.get("digitization", {}).get("status") != "digitized":
                continue
            image_index = int(image["index"])
            for curve in image["curves"]:
                suffix = curve["color"] if curve["parameter"] == "自动" else curve["parameter"]
                values.append(f"图{image_index} {curve['id']} · {suffix}")
        values.extend(["公式", "匹配 0", "反射 -20 dB", "耦合 -80 dB", "未知"])
        return values

    def _mapping_options(self) -> list[str]:
        """Return every digitized trace; detected parameters are hints only."""

        return self._source_options()

    def _detected_parameters(self) -> list[str]:
        values = {
            str(curve["parameter"])
            for image in self._image_payloads
            if image.get("digitization", {}).get("status") == "digitized"
            for curve in image["curves"]
            if curve.get("parameter") != "自动"
        }
        return sorted(values)

    def _auto_apply_compatible_sources(self, network: dict[str, object]) -> None:
        mappings = network["mappings"]
        defaults = {"自动", "匹配 0", "反射 -20 dB", "耦合 -80 dB", "未知"}
        for parameter, current in tuple(mappings.items()):
            if current not in defaults:
                continue
            matching = [
                source
                for source in self._mapping_options()
                if source.startswith("图") and source.endswith(f"· {parameter}")
            ]
            if len(matching) == 1:
                mappings[parameter] = matching[0]
                if bool(network.get("reciprocal")):
                    counterpart = transpose_parameter(parameter)
                    if counterpart in mappings and mappings[counterpart] in defaults:
                        mappings[counterpart] = matching[0]

    def _invalidate_image_curves(self, image_index: int) -> None:
        """Remove stale recognized sources and reset mappings that referenced them."""

        prefix = f"图{image_index + 1} "
        for network in self._networks:
            mappings = network["mappings"]
            for parameter, source in tuple(mappings.items()):
                if str(source).startswith(prefix):
                    mappings[parameter] = "未知"
        self._image_payloads[image_index]["curves"] = []
        self._image_payloads[image_index]["candidates"] = 0
        self._digitized_curve_data[image_index] = {}

    def _apply_detected_parameter(self, image_index: int, parameter: str | None) -> None:
        if not parameter:
            return
        image = self._image_payloads[image_index]
        if len(image["curves"]) != 1:
            return
        source = f"图{image_index + 1} {image['curves'][0]['id']} · {parameter}"
        for network in self._networks:
            mappings = network["mappings"]
            if parameter in mappings and mappings[parameter] in {
                "自动",
                "匹配 0",
                "反射 -20 dB",
                "耦合 -80 dB",
                "未知",
            }:
                mappings[parameter] = source
                if bool(network["reciprocal"]):
                    counterpart = transpose_parameter(parameter)
                    if counterpart in mappings:
                        mappings[counterpart] = source

    @staticmethod
    def _link_network(network: dict[str, object]) -> None:
        mappings = network["mappings"]
        visited: set[str] = set()
        for parameter in tuple(mappings):
            if parameter in visited:
                continue
            transpose = transpose_parameter(parameter)
            if transpose in mappings and transpose != parameter:
                mappings[transpose] = mappings[parameter]
                visited.update((parameter, transpose))

    def _network_payload(self, index: int) -> dict[str, object]:
        network = self._networks[index]
        return {
            "index": index,
            "name": str(network["name"]),
            "output": str(network["output"]),
            "port_count": int(network["port_count"]),
            "parameter_family": str(network["parameter_family"]),
            "phase": str(network["phase"]),
            "reciprocal": bool(network["reciprocal"]),
            "frequency_policy": dict(network["frequency_policy"]),
            "coverage": self._network_coverage(network),
            "single_ended_conversion": {
                "ready": False,
                "reason": "需要完整复数 SDD/SDC/SCD/SCC、端口配对和参考阻抗",
            }
            if network["parameter_family"] == "mixed-mode"
            else {"ready": True, "reason": "已是单端 Sij"},
            "mappings": dict(network["mappings"]),
            "mapping_options": {
                parameter: self._mapping_options()
                for parameter in network["mappings"]
            },
        }

    @staticmethod
    def _source_reference(source: object) -> tuple[int, str] | None:
        match = re.match(r"^图(\d+)\s+([A-Z]+)\s+·", str(source))
        if not match:
            return None
        return int(match.group(1)) - 1, match.group(2)

    def _network_grid_context(
        self, network: Mapping[str, object]
    ) -> tuple[FrequencyGridResult, dict[str, CurveResource], list[int]]:
        resources: dict[str, CurveResource] = {}
        source_images: set[int] = set()
        preferred_steps: list[float] = []
        for parameter, source_value in network["mappings"].items():
            source = str(source_value)
            reference = self._source_reference(source)
            if reference is None or source in resources:
                continue
            image_index, curve_id = reference
            if image_index < 0 or image_index >= len(self._image_payloads):
                raise ValueError(f"图片 {image_index + 1} 不存在。")
            axis = self._image_payloads[image_index]["axis"]
            if axis.get("status") != "ready":
                raise ValueError(f"图片 {image_index + 1} 缺少频率校准。")
            curve_data = self._digitized_curve_data[image_index].get(curve_id)
            if curve_data is None:
                raise ValueError(f"图片 {image_index + 1} 的曲线 {curve_id} 尚未识别。")
            frequency_hz, magnitude_db = curve_data
            resources[source] = CurveResource(
                curve_id=source,
                parameter=str(parameter),
                frequency_hz=frequency_hz,
                magnitude_db=magnitude_db,
            )
            source_images.add(image_index + 1)
            preferred_steps.append(float(axis["step_hz"]))

        policy = network["frequency_policy"]
        mode = str(policy["mode"])
        kwargs: dict[str, object] = {
            "max_points": MAX_FREQUENCY_POINTS,
            "preferred_step_hz": max(preferred_steps) if preferred_steps else None,
        }
        if mode == "intersection":
            grid_policy = "intersection_native"
        elif mode == "manual":
            grid_policy = "manual"
            kwargs.update(
                manual_start_hz=float(policy["start_hz"]),
                manual_stop_hz=float(policy["stop_hz"]),
                manual_step_hz=float(policy["step_hz"]),
                allow_extrapolation=bool(policy["allow_fill"]),
            )
        else:
            grid_policy = "union"
            kwargs["allow_extrapolation"] = bool(policy["allow_fill"])
        grid = compose_frequency_grid(
            list(resources.values()), policy=grid_policy, **kwargs
        )
        return grid, resources, sorted(source_images)

    def compose_network_magnitudes(
        self, index: object
    ) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Normalize image and default magnitudes onto one shared output grid."""

        with self._lock:
            network_index = _bounded_integer(index, 0, len(self._networks) - 1)
            network = self._networks[network_index]
            unresolved = [
                str(parameter)
                for parameter, source in network["mappings"].items()
                if str(source) in {"自动", "未知", "公式"}
            ]
            if unresolved:
                raise ValueError(
                    f"未分配通道：{', '.join(unresolved)}。请选择识别曲线或默认曲线。"
                )
            grid, resources, _ = self._network_grid_context(network)
            values: dict[str, np.ndarray] = {}
            for parameter, source_value in network["mappings"].items():
                source = str(source_value)
                if source == "匹配 0":
                    values[str(parameter)] = np.full(grid.points, MATCHED_FALLBACK_DB)
                elif source == "反射 -20 dB":
                    values[str(parameter)] = np.full(grid.points, -20.0)
                elif source == "耦合 -80 dB":
                    values[str(parameter)] = np.full(grid.points, -80.0)
                elif source in resources:
                    curve = resources[source]
                    inside = (
                        (grid.frequency_hz >= curve.frequency_hz[0])
                        & (grid.frequency_hz <= curve.frequency_hz[-1])
                    )
                    if not np.all(inside) and not bool(
                        network["frequency_policy"]["allow_fill"]
                    ):
                        raise ValueError("输出网格超出图片曲线覆盖范围。")
                    reflection = _is_reflection_parameter(
                        str(parameter), str(network["parameter_family"])
                    )
                    magnitude = np.full(grid.points, -20.0 if reflection else -80.0)
                    magnitude[inside] = np.interp(
                        grid.frequency_hz[inside], curve.frequency_hz, curve.magnitude_db
                    )
                    values[str(parameter)] = magnitude
                else:
                    raise ValueError(f"{parameter} 的曲线来源尚未确定。")
            return grid.frequency_hz.copy(), values

    def compose_network_touchstone(
        self, index: object
    ) -> tuple[TouchstoneData, str, str]:
        """Build one complete complex network on the shared output grid.

        Datasheet images currently provide magnitude only.  Touchstone requires
        complex values, so the export contract uses an explicit zero-degree
        phase for every mapped/default entry.  Mixed-mode matrices are converted
        to physical single-ended ports before serialization.
        """

        with self._lock:
            network_index = _bounded_integer(index, 0, len(self._networks) - 1)
            network = self._networks[network_index]
            port_count = int(network["port_count"])
            family = str(network["parameter_family"])
            output = str(network["output"])
            frequency_hz, magnitudes = self.compose_network_magnitudes(network_index)
            matrix = np.zeros(
                (frequency_hz.size, port_count, port_count), dtype=np.complex128
            )
            if family == "single-ended":
                for parameter, magnitude_db in magnitudes.items():
                    out_port = int(parameter[1]) - 1
                    in_port = int(parameter[2]) - 1
                    matrix[:, out_port, in_port] = np.power(
                        10.0, np.asarray(magnitude_db, dtype=np.float64) / 20.0
                    )
            elif family == "mixed-mode":
                logical_ports = port_count // 2
                for parameter, magnitude_db in magnitudes.items():
                    out_mode_offset = 0 if parameter[1] == "D" else logical_ports
                    in_mode_offset = 0 if parameter[2] == "D" else logical_ports
                    out_port = out_mode_offset + int(parameter[3]) - 1
                    in_port = in_mode_offset + int(parameter[4]) - 1
                    matrix[:, out_port, in_port] = np.power(
                        10.0, np.asarray(magnitude_db, dtype=np.float64) / 20.0
                    )
                matrix = mixed_mode_to_single_ended(matrix)
            else:  # Defensive: normal mutations reject unsupported families.
                raise ValueError("参数类型无效。")
            return TouchstoneData(frequency_hz, matrix), output, family

    def _network_coverage(self, network: Mapping[str, object]) -> dict[str, object]:
        mapped_images = sorted(
            {
                reference[0] + 1
                for source in network["mappings"].values()
                if (reference := self._source_reference(source)) is not None
            }
        )
        if not mapped_images and network["frequency_policy"]["mode"] != "manual":
            return {
                "status": "needs-grid",
                "source_images": [],
                "message": "仅使用默认曲线时请设置手动起始、终止和步进。",
            }
        try:
            grid, resources, source_images = self._network_grid_context(network)
        except ValueError as error:
            message = str(error)
            if "没有共同频率范围" in message:
                status = "conflict"
            elif "必须显式允许" in message or "超出" in message:
                status = "requires-fill"
            elif "缺少频率校准" in message:
                status = "missing-axis"
            else:
                status = "invalid-grid"
            return {
                "status": status,
                "source_images": mapped_images,
                "message": message,
                **(
                    {
                        "missing_images": [
                            image_number
                            for image_number in mapped_images
                            if image_number > len(self._image_payloads)
                            or self._image_payloads[image_number - 1]["axis"].get("status")
                            != "ready"
                        ]
                    }
                    if status == "missing-axis"
                    else {}
                ),
            }

        def matches_grid(curve: CurveResource) -> bool:
            return curve.frequency_hz.shape == grid.frequency_hz.shape and np.allclose(
                curve.frequency_hz, grid.frequency_hz, rtol=1e-12, atol=1e-6
            )

        image_channels = sum(
            self._source_reference(source) is not None
            for source in network["mappings"].values()
        )
        unresolved_channels = sum(
            str(source) in {"自动", "未知", "公式"}
            for source in network["mappings"].values()
        )
        resampled_channels = sum(
            1
            for source in network["mappings"].values()
            if str(source) in resources and not matches_grid(resources[str(source)])
        )
        return {
            "status": "ready" if not unresolved_channels else "unresolved",
            "source_images": source_images,
            "start_hz": grid.start_hz,
            "stop_hz": grid.stop_hz,
            "step_hz": grid.step_hz,
            "points": grid.points,
            "uniform": True,
            "uses_interpolation": bool(resampled_channels),
            "uses_fill": grid.uses_extrapolation,
            "image_channels": image_channels,
            "default_channels": len(network["mappings"]) - image_channels - unresolved_channels,
            "unresolved_channels": unresolved_channels,
            "resampled_channels": resampled_channels,
            "source_sample_counts": {
                source: int(curve.frequency_hz.size) for source, curve in resources.items()
            },
            "channel_points": {
                str(parameter): grid.points for parameter in network["mappings"]
            },
        }

    def _image_metadata_payload(self, index: int) -> dict[str, object]:
        image = self._image_payloads[index]
        return {key: copy.deepcopy(value) for key, value in image.items() if key != "data_url"}

    def _network_state_payload(self) -> dict[str, object]:
        return {
            "networks": [self._network_payload(index) for index in range(len(self._networks))],
            "source_options": self._source_options(),
            "detected_parameters": self._detected_parameters(),
        }
