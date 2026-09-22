"""图片修正事务和方案恢复；失败时保留用户原数据，成功后使旧映射失效。"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 copy，提供本文件后续流程需要的库能力。
import copy
# Codex说明(自动生成)： 导入 hashlib，提供本文件后续流程需要的库能力。
import hashlib
# Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
import json
import numpy as np


def _validated_recipe_axis(axis):
    """验证编辑用 X/Y 校准副本，不提交工作区，也不补用旧方案的空白值。

    频率沿图片表单的 GHz 裸值、DC/Log、频点上限合同；Y 同时保存用户
    印刷坐标和内部负幅度坐标。导入旧方案与打开编辑器共用这一检查。
    """
    from .datasheet_workspace import MAX_FREQUENCY_POINTS
    from .image_frequency import parse_image_frequency

    if not isinstance(axis, dict):
        raise ValueError("Set Start, Stop, Output Step and Y Top/Bottom before editing.")
    clean = copy.deepcopy(axis)
    try:
        start = parse_image_frequency(axis.get("start", ""), allow_zero=True)
        stop = parse_image_frequency(axis.get("stop", ""))
        step = parse_image_frequency(axis.get("step", ""))
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("Set valid Start, Stop and Output Step; values without units use GHz.") from error
    spacing = str(axis.get("spacing", "linear")).strip().lower()
    if stop <= start or spacing not in ("linear", "log") or (spacing == "log" and start <= 0):
        raise ValueError("Stop must exceed Start; Log Start must be greater than zero.")
    count = int(np.floor((stop - start) / step)) + 1
    if not 2 <= count <= MAX_FREQUENCY_POINTS:
        raise ValueError("Image frequency grid must contain 2–200000 points.")
    convention = str(axis.get("y_convention", "magnitude")).strip().lower()
    if convention not in ("magnitude", "positive-loss"):
        raise ValueError("Choose Magnitude dB or Positive loss dB for the Y axis.")
    # 旧方案允许只保存 y_min/max；显式空白 top/bottom 必须报错，不能回退旧值。
    fallback_top, fallback_bottom = axis.get("y_max_db"), axis.get("y_min_db")
    if convention == "positive-loss":
        fallback_top = -fallback_top if fallback_top is not None else None
        fallback_bottom = -fallback_bottom if fallback_bottom is not None else None
    try:
        top = float(str(axis.get("y_top_db", fallback_top)).strip())
        bottom = float(str(axis.get("y_bottom_db", fallback_bottom)).strip())
    except (ValueError, TypeError) as error:
        raise ValueError("Set finite Y Top and Y Bottom values before editing.") from error
    if not np.isfinite(top) or not np.isfinite(bottom):
        raise ValueError("Set finite Y Top and Y Bottom values before editing.")
    if convention == "magnitude" and top <= bottom:
        raise ValueError("Magnitude dB requires Y Top greater than Y Bottom.")
    if convention == "positive-loss" and bottom <= top:
        raise ValueError("Positive loss dB requires Y Bottom greater than Y Top.")
    clean.update(status="ready", source="manual", start_hz=start, stop_hz=stop,
                 step_hz=step, points=count, spacing=spacing, y_convention=convention,
                 y_top_db=top, y_bottom_db=bottom,
                 y_max_db=top if convention == "magnitude" else -top,
                 y_min_db=bottom if convention == "magnitude" else -bottom)
    return clean


# Codex说明(自动生成)： 定义 ImageWorkspaceEditing 类，把相关数据结构、校验规则或操作方法组织在一起。
class ImageWorkspaceEditing:
    # Codex说明(自动生成)： 定义函数 image_edit_recipe，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def image_edit_recipe(self, index, calibration=None):
        # 以图像哈希绑定编辑对象，Trace UUID 独立于显示顺序。
        from .datasheet_workspace import _bounded_integer

        try:
            return self._image_edit_recipe_snapshot(index, calibration)
        except (ValueError, IndexError, TypeError, OverflowError) as error:
            return {"ok": False, "error": str(error)}

    def _image_edit_recipe_snapshot(self, index, calibration):
        """旧方案保留路径，但默认校准只取当前轴；显式表单值校验后仅写返回副本。"""
        from .datasheet_workspace import _bounded_integer

        with self._lock:
            # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
            number = _bounded_integer(index, 0, len(self._images) - 1)
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = self._image_payloads[number]
            axis = (copy.deepcopy(image["axis"]) if calibration is None
                    else _validated_recipe_axis(calibration))
            # Codex说明(自动生成)： 检查条件 image.get('edit_recipe')，根据结果选择后续执行路径。
            if image.get("edit_recipe"):
                # Codex说明(自动生成)： 返回 {'ok': True, 'recipe': copy.deepcopy(image['edit_recipe...，让调用方取得本函数的处理结果。
                recipe = copy.deepcopy(image["edit_recipe"])
                recipe["axis"] = axis
                return {"ok": True, "recipe": recipe}
            # Codex说明(自动生成)： 计算并保存 box，供后续语句继续读取或更新。
            box = image.get("digitization", {}).get("plot_box")
            # Codex说明(自动生成)： 计算并保存 specs，供后续语句继续读取或更新。
            specs = [
                {
                    "id": image["sha256"][:12] + "-" + c["id"],
                    "label": c.get("label") or c["color"],
                    "rgb": c["rgb"],
                    "anchors": [],
                }
                for c in image["curves"]
            ]
            # Codex说明(自动生成)： 返回 {'ok': True, 'recipe': {'schema_version': 1, 'source_sh...，让调用方取得本函数的处理结果。
            return {
                "ok": True,
                "recipe": {
                    "schema_version": 1,
                    "source_sha256": image["sha256"],
                    "plot_box": box,
                    "exclusions": [],
                    "traces": specs,
                    "axis": axis,
                },
            }

    # Codex说明(自动生成)： 定义函数 apply_image_recipe，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def apply_image_recipe(self, index, recipe):
        # 验证全部结构后才提交；不允许导入方案引用另一个文件或任意输出路径。
        from .datasheet_workspace import _bounded_integer
        # Codex说明(自动生成)： 从 datasheet_digitizer 导入 _decode_image，提供本文件后续流程需要的库能力。
        from .datasheet_digitizer import _decode_image
        # Codex说明(自动生成)： 从 image_path_editor 导入 checked_box，提供本文件后续流程需要的库能力。
        from .image_path_editor import checked_box

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 检查条件 not isinstance(recipe, dict) or len(json.dumps(recipe, ...，根据结果选择后续执行路径。
            if (
                not isinstance(recipe, dict)
                or len(json.dumps(recipe, allow_nan=False)) > 250000
            ):
                # Codex说明(自动生成)： 抛出 ValueError('修线方案无效或过大。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("修线方案无效或过大。")
            # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
            with self._lock:
                # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
                number = _bounded_integer(index, 0, len(self._images) - 1)
                # Codex说明(自动生成)： 检查条件 self._active_digitizations，根据结果选择后续执行路径。
                if self._active_digitizations:
                    # Codex说明(自动生成)： 抛出 ValueError('请等待当前图片识别结束。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("请等待当前图片识别结束。")
                # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
                image = self._image_payloads[number]
                # 以内容 SHA-256 绑定原图或数组版本，发现文件替换或局部改线。
                digest = hashlib.sha256(self._images[number].read_bytes()).hexdigest()
                # Codex说明(自动生成)： 检查条件 type(recipe.get('schema_version')) is not int or recipe...，根据结果选择后续执行路径。
                if (
                    type(recipe.get("schema_version")) is not int
                    or recipe.get("schema_version") != 1
                    or recipe.get("source_sha256") != image["sha256"]
                    or digest != image["sha256"]
                ):
                    # Codex说明(自动生成)： 抛出 ValueError('修线方案与当前图片哈希不一致，请重新导入。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("修线方案与当前图片哈希不一致，请重新导入。")
                # Codex说明(自动生成)： 计算并保存 pixels，供后续语句继续读取或更新。
                pixels = _decode_image(self._images[number])
                # Codex说明(自动生成)： 计算并保存 box，供后续语句继续读取或更新。
                box = checked_box(recipe["plot_box"], pixels.shape)
                # Codex说明(自动生成)： 计算并保存 exclusions，供后续语句继续读取或更新。
                exclusions = recipe.get("exclusions", [])
                # Codex说明(自动生成)： 检查条件 not isinstance(exclusions, list) or len(exclusions) > 32，根据结果选择后续执行路径。
                if not isinstance(exclusions, list) or len(exclusions) > 32:
                    # Codex说明(自动生成)： 抛出 ValueError('最多允许 32 个排除区域。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("最多允许 32 个排除区域。")
                # Codex说明(自动生成)： 计算并保存 exclusions，供后续语句继续读取或更新。
                exclusions = [list(checked_box(r, pixels.shape)) for r in exclusions]
                # 方案必须保存身份和原图像素锚点；深拷贝阻断调用者后续原地修改。
                clean = {
                    "schema_version": 1,
                    "source_sha256": digest,
                    "plot_box": list(box),
                    "exclusions": exclusions,
                    "traces": copy.deepcopy(recipe.get("traces")),
                    "axis": _validated_recipe_axis(recipe.get("axis", image["axis"])),
                }
                # Codex说明(自动生成)： 计算并保存 specs，供后续语句继续读取或更新。
                specs = clean["traces"]
                # Codex说明(自动生成)： 检查条件 not isinstance(specs, list) or not 1 <= len(specs) <= 8，根据结果选择后续执行路径。
                if not isinstance(specs, list) or not 1 <= len(specs) <= 8:
                    # Codex说明(自动生成)： 抛出 ValueError('请保留 1–8 条目标曲线。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("请保留 1–8 条目标曲线。")
                # Codex说明(自动生成)： 遍历 specs 中的 spec，逐项执行循环体逻辑。
                for spec in specs:
                    # Codex说明(自动生成)： 检查条件 not isinstance(spec, dict) or not isinstance(spec.get('...，根据结果选择后续执行路径。
                    if (
                        not isinstance(spec, dict)
                        or not isinstance(spec.get("id"), str)
                        or len(spec["id"]) > 120
                        or len(str(spec.get("label", ""))) > 160
                    ):
                        # Codex说明(自动生成)： 抛出 ValueError('曲线身份或名称无效。')，明确提示输入、状态或处理流程无法继续。
                        raise ValueError("曲线身份或名称无效。")
                # 冻结当前图片状态，失败或撤销时从快照恢复。
                snapshot = copy.deepcopy(image)
                # 保存修线前幅度和频率数组，防止失败留下半成品。
                prior_data = copy.deepcopy(self._digitized_curve_data[number])
                # 保存原映射和复核状态，供失败事务完整回滚。
                prior_networks = copy.deepcopy(self._networks)
                # 记录修线前校准版本，仅失败回滚恢复此版本。
                prior_revision = self._axis_revisions[number]
                # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
                try:
                    # Codex说明(自动生成)： 计算并保存 image['edit_recipe']，供后续语句继续读取或更新。
                    image["edit_recipe"] = clean
                    # Codex说明(自动生成)： 计算并保存 axis，供后续语句继续读取或更新。
                    axis = clean["axis"]
                    # 与 UI 共用校准入口；异常和正常返回的失败都回滚整个事务。
                    frequency = self.set_image_frequency(
                        number,
                        axis["start"],
                        axis["stop"],
                        axis["step"],
                        axis.get("spacing", "linear"),
                    )
                    # Codex说明(自动生成)： 检查条件 frequency['ok']，根据结果选择后续执行路径。
                    if frequency["ok"]:
                        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
                        result = self.digitize_image_with_axis(
                            number,
                            axis.get("y_top_db", axis.get("y_max_db")),
                            axis.get("y_bottom_db", axis.get("y_min_db")),
                            axis.get("y_convention", "magnitude"),
                        )
                    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
                    else:
                        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
                        result = frequency
                # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
                except Exception:
                    # Codex说明(自动生成)： 计算并保存 self._image_payloads[number]，供后续语句继续读取或更新。
                    self._image_payloads[number] = snapshot
                    # Codex说明(自动生成)： 计算并保存 self._digitized_curve_data[number]，供后续语句继续读取或更新。
                    self._digitized_curve_data[number] = prior_data
                    # Codex说明(自动生成)： 计算并保存 self._networks，供后续语句继续读取或更新。
                    self._networks = prior_networks
                    # Codex说明(自动生成)： 计算并保存 self._axis_revisions[number]，供后续语句继续读取或更新。
                    self._axis_revisions[number] = prior_revision
                    # Codex说明(自动生成)： 抛出 异常，明确提示输入、状态或处理流程无法继续。
                    raise
                # Codex说明(自动生成)： 检查条件 not result['ok']，根据结果选择后续执行路径。
                if not result["ok"]:
                    # Codex说明(自动生成)： 计算并保存 self._image_payloads[number]，供后续语句继续读取或更新。
                    self._image_payloads[number] = snapshot
                    # Codex说明(自动生成)： 计算并保存 self._digitized_curve_data[number]，供后续语句继续读取或更新。
                    self._digitized_curve_data[number] = prior_data
                    # Codex说明(自动生成)： 计算并保存 self._networks，供后续语句继续读取或更新。
                    self._networks = prior_networks
                    # Codex说明(自动生成)： 计算并保存 self._axis_revisions[number]，供后续语句继续读取或更新。
                    self._axis_revisions[number] = prior_revision
                    # Codex说明(自动生成)： 返回 result，让调用方取得本函数的处理结果。
                    return result
                # 撤销保存一次用户动作，不恢复旧导出确认。只保留十步以限制内存。
                if not hasattr(self, "_image_edit_undo"):
                    # Codex说明(自动生成)： 计算并保存 self._image_edit_undo，供后续语句继续读取或更新。
                    self._image_edit_undo = {}
                # Codex说明(自动生成)： 计算并保存 history，供后续语句继续读取或更新。
                history = self._image_edit_undo.setdefault(digest, [])
                # Codex说明(自动生成)： 调用 history.append 更新列表或集合，把当前步骤产生的数据加入结果。
                history.append((snapshot, prior_data))
                # Codex说明(自动生成)： 删除 history[:-10]，释放不再需要的引用或状态。
                del history[:-10]
                # Codex说明(自动生成)： 返回 result，让调用方取得本函数的处理结果。
                return result
        # Codex说明(自动生成)： 捕获 (ValueError, IndexError, KeyError, TypeError, OSError, ...，执行对应的恢复、记录或重新报错逻辑。
        except (
            ValueError,
            IndexError,
            KeyError,
            TypeError,
            OSError,
            OverflowError,
        ) as error:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(error) or '修线方案无效。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(error) or "修线方案无效。"}

    # Codex说明(自动生成)： 定义函数 undo_image_recipe，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def undo_image_recipe(self, index):
        # 撤销曲线与校准，相关映射重新选择，防止旧序号指向不同身份。
        from .datasheet_workspace import _bounded_integer

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
            with self._lock:
                # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
                number = _bounded_integer(index, 0, len(self._images) - 1)
                # Codex说明(自动生成)： 检查条件 self._active_digitizations，根据结果选择后续执行路径。
                if self._active_digitizations:
                    # Codex说明(自动生成)： 抛出 ValueError('请等待当前图片识别结束。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("请等待当前图片识别结束。")
                # 以内容 SHA-256 绑定原图或数组版本，发现文件替换或局部改线。
                digest = self._image_payloads[number]["sha256"]
                # Codex说明(自动生成)： 计算并保存 history，供后续语句继续读取或更新。
                history = getattr(self, "_image_edit_undo", {}).get(digest, [])
                # Codex说明(自动生成)： 检查条件 not history，根据结果选择后续执行路径。
                if not history:
                    # Codex说明(自动生成)： 抛出 ValueError('没有可撤销的修线操作。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("没有可撤销的修线操作。")
                # Codex说明(自动生成)： 计算并保存 (snapshot, data)，供后续语句继续读取或更新。
                snapshot, data = history.pop()
                # Codex说明(自动生成)： 调用 self._invalidate_image_curves，执行当前流程需要的具体操作或副作用。
                self._invalidate_image_curves(number)
                # Codex说明(自动生成)： 计算并保存 snapshot['index']，供后续语句继续读取或更新。
                snapshot["index"] = number + 1
                # Codex说明(自动生成)： 计算并保存 self._image_payloads[number]，供后续语句继续读取或更新。
                self._image_payloads[number] = snapshot
                # Codex说明(自动生成)： 计算并保存 self._digitized_curve_data[number]，供后续语句继续读取或更新。
                self._digitized_curve_data[number] = data
                # Codex说明(自动生成)： 基于旧值更新 self._axis_revisions[number]，累积当前循环或处理步骤的结果。
                self._axis_revisions[number] += 1
                # Codex说明(自动生成)： 返回 {'ok': True, 'image_update': self._image_metadata_paylo...，让调用方取得本函数的处理结果。
                return {
                    "ok": True,
                    "image_update": self._image_metadata_payload(number),
                    **self._network_state_payload(),
                }
        # Codex说明(自动生成)： 捕获 (ValueError, IndexError)，执行对应的恢复、记录或重新报错逻辑。
        except (ValueError, IndexError) as error:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(error)}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(error)}

    # Codex说明(自动生成)： 定义函数 image_curve_csv，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def image_curve_csv(self, index):
        # 原始幅度样本独立于复数模型导出；每点说明像素证据，缺列不自动填满。
        import csv
        # Codex说明(自动生成)： 导入 io，把字符串包装成类文件对象，供 tokenizer 等接口读取。
        import io
        # Codex说明(自动生成)： 从 datasheet_workspace 导入 _bounded_integer，提供本文件后续流程需要的库能力。
        from .datasheet_workspace import _bounded_integer

        # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
        with self._lock:
            # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
            number = _bounded_integer(index, 0, len(self._images) - 1)
            # Codex说明(自动生成)： 计算并保存 image，供后续语句继续读取或更新。
            image = self._image_payloads[number]
            # Codex说明(自动生成)： 检查条件 not image['curves'] or image.get('digitization', {}).ge...，根据结果选择后续执行路径。
            if (
                not image["curves"]
                or image.get("digitization", {}).get("status") != "digitized"
            ):
                # Codex说明(自动生成)： 抛出 ValueError('请先校准并识别曲线。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("请先校准并识别曲线。")
            # Codex说明(自动生成)： 计算并保存 stream，供后续语句继续读取或更新。
            stream = io.StringIO()
            # Codex说明(自动生成)： 调用 stream.write 写出文件或数据，保存当前处理结果。
            stream.write(
                "# magnitude-only; no measured phase; source_sha256="
                + image["sha256"]
                + "\n"
            )
            # Codex说明(自动生成)： 计算并保存 writer，供后续语句继续读取或更新。
            writer = csv.writer(stream)
            # Codex说明(自动生成)： 调用 writer.writerow 写出文件或数据，保存当前处理结果。
            writer.writerow(
                [
                    "trace_id",
                    "label",
                    "frequency_hz",
                    "magnitude_db",
                    "pixel_x",
                    "pixel_y",
                    "evidence",
                ]
            )
            # Codex说明(自动生成)： 遍历 image['curves'] 中的 curve，逐项执行循环体逻辑。
            for curve in image["curves"]:
                # Codex说明(自动生成)： 计算并保存 (f, m)，供后续语句继续读取或更新。
                f, m = self._digitized_curve_data[number][curve["id"]]
                # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
                points = curve.get("source_pixel_points", [])
                # Codex说明(自动生成)： 计算并保存 provenance，供后续语句继续读取或更新。
                provenance = curve.get("sample_provenance", [])
                # Codex说明(自动生成)： 遍历 enumerate(zip(f, m)) 中的 (i, (frequency, magnitude))，逐项执行循环体逻辑。
                for i, (frequency, magnitude) in enumerate(zip(f, m)):
                    # Codex说明(自动生成)： 计算并保存 pixel，供后续语句继续读取或更新。
                    pixel = points[i] if i < len(points) else ["", ""]
                    # Codex说明(自动生成)： 调用 writer.writerow 写出文件或数据，保存当前处理结果。
                    writer.writerow(
                        [
                            curve.get("identity", curve["id"]),
                            curve.get("label", curve["color"]),
                            frequency,
                            magnitude,
                            *pixel,
                            provenance[i] if i < len(provenance) else "unknown",
                        ]
                    )
            # Codex说明(自动生成)： 返回 stream.getvalue()，让调用方取得本函数的处理结果。
            return stream.getvalue()
