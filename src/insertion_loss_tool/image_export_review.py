"""图片建模的版本绑定复核；与无源性检查分别回答数据来源和模型问题。"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# 摘要绑定用户看过的图像、校准、曲线与输出选择，防止旧确认被新数据复用。
import copy
# Codex说明(自动生成)： 导入 hashlib，提供本文件后续流程需要的库能力。
import hashlib
# Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
import json
# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np
from .image_sampling import finer_uniform_step, sampling_message


# Codex说明(自动生成)： 定义 ImageExportReview 类，把相关数据结构、校验规则或操作方法组织在一起。
class ImageExportReview:
    """供 DatasheetWorkspace 使用，所有状态读取在其可重入锁内完成。"""

    # Codex说明(自动生成)： 定义函数 set_image_network_model，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_image_network_model(self, index, phase="zero-degree", delay_ns=0, z0=50):
        # 相位和参考阻抗必须由用户显式选择，数值单位分别为 ns 和 ohm。
        try:
            # Codex说明(自动生成)： 计算并保存 (delay, impedance)，供后续语句继续读取或更新。
            delay, impedance = float(delay_ns), float(z0)
            # Codex说明(自动生成)： 检查条件 phase not in ('zero-degree', 'delay') or not np.isfinit...，根据结果选择后续执行路径。
            if (
                phase not in ("zero-degree", "delay")
                or not np.isfinite(delay)
                or delay < 0
            ):
                # Codex说明(自动生成)： 抛出 ValueError('相位模型无效；延迟必须是非负有限 ns。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("相位模型无效；延迟必须是非负有限 ns。")
            # Codex说明(自动生成)： 检查条件 not np.isfinite(impedance) or impedance <= 0，根据结果选择后续执行路径。
            if not np.isfinite(impedance) or impedance <= 0:
                # Codex说明(自动生成)： 抛出 ValueError('参考阻抗必须为正的有限 ohm。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("参考阻抗必须为正的有限 ohm。")
            # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
            with self._lock:
                # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
                network = self._networks[self._checked_network(index)]
                # Codex说明(自动生成)： 调用 network.update，执行当前流程需要的具体操作或副作用。
                network.update(phase=phase, delay_ns=delay, z0=impedance)
                # Codex说明(自动生成)： 返回 {'ok': True, **self._network_state_payload()}，让调用方取得本函数的处理结果。
                return {"ok": True, **self._network_state_payload()}
        # Codex说明(自动生成)： 捕获 (ValueError, IndexError, TypeError)，执行对应的恢复、记录或重新报错逻辑。
        except (ValueError, IndexError, TypeError) as error:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(error)}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(error)}

    # Codex说明(自动生成)： 定义函数 _checked_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _checked_network(self, index):
        # JS 只能提供整数索引，不能把布尔值或负索引转成另一个输出。
        from .datasheet_workspace import _bounded_integer

        # Codex说明(自动生成)： 返回 _bounded_integer(index, 0, len(self._networks) - 1)，让调用方取得本函数的处理结果。
        return _bounded_integer(index, 0, len(self._networks) - 1)

    # Codex说明(自动生成)： 定义函数 _export_review_record，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _export_review_record(self, index):
        # 生成频率网格沿用产品实现；此处只附加可追溯的解释和确认约束。
        network = self._networks[index]
        # Codex说明(自动生成)： 计算并保存 unresolved，供后续语句继续读取或更新。
        unresolved = [
            p
            for p, source in network["mappings"].items()
            if source in ("自动", "未知", "公式")
        ]
        # Codex说明(自动生成)： 检查条件 unresolved，根据结果选择后续执行路径。
        if unresolved:
            # Codex说明(自动生成)： 抛出 ValueError(f'未分配通道：{', '.join(unresolved)}。请选择识别曲线或默认曲线。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError(
                f"未分配通道：{', '.join(unresolved)}。请选择识别曲线或默认曲线。"
            )
        # Codex说明(自动生成)： 计算并保存 (grid, _, _)，供后续语句继续读取或更新。
        grid, resources, _ = self._network_grid_context(network)
        checks = self._sampling_checks(grid.frequency_hz, resources)
        sampling = {check["source"]: check for check in checks}
        # Codex说明(自动生成)： 计算并保存 (sources, warnings)，供后续语句继续读取或更新。
        sources, warnings = [], []
        # Codex说明(自动生成)： 计算并保存 seen，供后续语句继续读取或更新。
        seen = set()
        # Codex说明(自动生成)： 遍历 network['mappings'].items() 中的 (parameter, source)，逐项执行循环体逻辑。
        for parameter, source in network["mappings"].items():
            # Codex说明(自动生成)： 计算并保存 reference，供后续语句继续读取或更新。
            reference = self._source_reference(source)
            # Codex说明(自动生成)： 检查条件 reference is None or reference in seen，根据结果选择后续执行路径。
            if reference is None or reference in seen:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 调用 seen.add，执行当前流程需要的具体操作或副作用。
            seen.add(reference)
            # Codex说明(自动生成)： 计算并保存 (image_index, curve_id)，供后续语句继续读取或更新。
            image_index, curve_id = reference
            source_label = f"Image {image_index + 1}, trace {curve_id}"
            # Codex说明(自动生成)： 计算并保存 item，供后续语句继续读取或更新。
            item = self._image_payloads[image_index]
            # Codex说明(自动生成)： 检查条件 hashlib.sha256(self._images[image_index].read_bytes())....，根据结果选择后续执行路径。
            if (
                hashlib.sha256(self._images[image_index].read_bytes()).hexdigest()
                != item["sha256"]
            ):
                # Codex说明(自动生成)： 抛出 ValueError('原图文件已变化，请移除后重新导入并复核。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("原图文件已变化，请移除后重新导入并复核。")
            # Codex说明(自动生成)： 计算并保存 curve，供后续语句继续读取或更新。
            curve = next(c for c in item["curves"] if c["id"] == curve_id)
            # Codex说明(自动生成)： 计算并保存 (frequency, magnitude)，供后续语句继续读取或更新。
            frequency, magnitude = self._digitized_curve_data[image_index][curve_id]
            # 浮点原始数组也进入摘要；只保存端点不足以发现局部修线或重新识别。
            digest = hashlib.sha256(
                frequency.tobytes() + magnitude.tobytes()
            ).hexdigest()
            # Codex说明(自动生成)： 计算并保存 regions，供后续语句继续读取或更新。
            regions = curve.get("review_regions", [])
            # Codex说明(自动生成)： 检查条件 regions or curve.get('review_status') == 'review'，根据结果选择后续执行路径。
            if regions or curve.get("review_status") == "review":
                # Codex说明(自动生成)： 调用 warnings.append 更新列表或集合，把当前步骤产生的数据加入结果。
                warnings.append(f"{source_label}: {len(regions)} highlighted intervals need visual review.")
            # Codex说明(自动生成)： 计算并保存 axis，供后续语句继续读取或更新。
            axis = item["axis"]
            # Codex说明(自动生成)： 检查条件 frequency[0] > axis['start_hz'] or frequency[-1] < axis...，根据结果选择后续执行路径。
            if frequency[0] > axis["start_hz"] or frequency[-1] < axis["stop_hz"]:
                # Codex说明(自动生成)： 调用 warnings.append 更新列表或集合，把当前步骤产生的数据加入结果。
                warnings.append(
                    f"{source_label}: extracted coverage is {frequency[0]/1e9:.6g}–{frequency[-1]/1e9:.6g} GHz; it does not cover the full calibrated range."
                )
            warning = sampling_message(source, sampling[source])
            if warning:
                warnings.append(warning)
            # Codex说明(自动生成)： 调用 sources.append 更新列表或集合，把当前步骤产生的数据加入结果。
            sources.append(
                {
                    "image": item["name"],
                    "sha256": item["sha256"],
                    "axis_revision": self._axis_revisions[image_index],
                    "axis": copy.deepcopy(axis),
                    "trace": curve_id,
                    "label": curve.get("label", ""),
                    "data_sha256": digest,
                    "source_samples": len(frequency),
                    "sampling_check": sampling[source],
                    "review_regions": copy.deepcopy(regions),
                    "edit_recipe": copy.deepcopy(item.get("edit_recipe", {})),
                    "sample_provenance": list(curve.get("sample_provenance", [])),
                    "frequency_range_hz": [float(frequency[0]), float(frequency[-1])],
                }
            )
        # 把原图、映射、校准、缺口和建模假设合并为可复核版本。
        record = {
            "schema_version": 1,
            "kind": "image-derived magnitude model",
            "phase_assumption": network["phase"],
            "delay_ns": network.get("delay_ns", 0),
            "reference_impedance_ohm": network.get("z0", 50),
            "parameter_family": network["parameter_family"],
            "mappings": copy.deepcopy(network["mappings"]),
            "ports": network["port_count"],
            "reciprocal": network["reciprocal"],
            "frequency_policy": copy.deepcopy(network["frequency_policy"]),
            "frequency_grid": {
                "start_hz": grid.start_hz,
                "stop_hz": grid.stop_hz,
                "points": grid.points,
                "step_hz": grid.step_hz,
            },
            "suggested_step_hz": finer_uniform_step(
                grid.frequency_hz, [curve.frequency_hz for curve in resources.values()]
            ) if any(sampling_message(check["source"], check) for check in checks) else None,
            "sources": sources,
            "limitations": [
                "Magnitude digitization is not the original complex vendor network.",
                "Sampled passivity does not prove causality or image accuracy.",
                "Sampling diagnostics compare extracted magnitude samples, not the original device response.",
            ],
        }
        # 摘要覆盖局部曲线数据，旧确认不能用于修改后的网络。
        token = hashlib.sha256(
            json.dumps(record, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        # Codex说明(自动生成)： 返回 (record, token, warnings)，让调用方取得本函数的处理结果。
        return record, token, warnings

    # Codex说明(自动生成)： 定义函数 preview_image_export，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def preview_image_export(self, index):
        # 用户先看频段、缺口和建模假设，再确认这一个不可变版本。
        try:
            # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
            with self._lock:
                # Codex说明(自动生成)： 计算并保存 (record, token, warnings)，供后续语句继续读取或更新。
                record, token, warnings = self._export_review_record(
                    self._checked_network(index)
                )
                # Codex说明(自动生成)： 返回 {'ok': True, 'token': token, 'record': record, 'warning...，让调用方取得本函数的处理结果。
                return {
                    "ok": True,
                    "token": token,
                    "record": record,
                    "warnings": warnings,
                }
        # Codex说明(自动生成)： 捕获 (ValueError, IndexError, KeyError, StopIteration, OSError)，执行对应的恢复、记录或重新报错逻辑。
        except (ValueError, IndexError, KeyError, StopIteration, OSError) as error:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(error) or '映射尚未完整。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(error) or "映射尚未完整。"}

    # Codex说明(自动生成)： 定义函数 confirm_image_export，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def confirm_image_export(self, index, token):
        # 不接受旧预览或猜测的令牌，确认后仍在导出时重新计算摘要。
        try:
            # Codex说明(自动生成)： 进入上下文 self._lock，确保文件、资源或临时状态按作用域正确释放。
            with self._lock:
                # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
                number = self._checked_network(index)
                # Codex说明(自动生成)： 计算并保存 (_, current, _)，供后续语句继续读取或更新。
                _, current, _ = self._export_review_record(number)
                # Codex说明(自动生成)： 检查条件 token != current，根据结果选择后续执行路径。
                if token != current:
                    # Codex说明(自动生成)： 抛出 ValueError('复核版本已变化，请重新预览并确认。')，明确提示输入、状态或处理流程无法继续。
                    raise ValueError("复核版本已变化，请重新预览并确认。")
                # Codex说明(自动生成)： 计算并保存 self._networks[number]['review_confirmation']，供后续语句继续读取或更新。
                self._networks[number]["review_confirmation"] = current
                # Codex说明(自动生成)： 返回 {'ok': True}，让调用方取得本函数的处理结果。
                return {"ok": True}
        # Codex说明(自动生成)： 捕获 (ValueError, IndexError, KeyError, StopIteration, OSError)，执行对应的恢复、记录或重新报错逻辑。
        except (ValueError, IndexError, KeyError, StopIteration, OSError) as error:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(error)}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(error)}

    # Codex说明(自动生成)： 定义函数 compose_reviewed_image_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def compose_reviewed_image_network(self, index):
        # 复核与复制复数矩阵保持原子性，生成中的 UI 改动不修改此次快照。
        with self._lock:
            # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
            number = self._checked_network(index)
            # Codex说明(自动生成)： 计算并保存 (record, token, _)，供后续语句继续读取或更新。
            record, token, _ = self._export_review_record(number)
            # Codex说明(自动生成)： 检查条件 self._networks[number].get('review_confirmation') != token，根据结果选择后续执行路径。
            if self._networks[number].get("review_confirmation") != token:
                # Codex说明(自动生成)： 抛出 ValueError('请先复核曲线、输出频段和相位假设，再确认当前版本。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("请先复核曲线、输出频段和相位假设，再确认当前版本。")
            # Codex说明(自动生成)： 计算并保存 (data, output, family)，供后续语句继续读取或更新。
            data, output, family = self.compose_network_touchstone(number)
            # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
            network = self._networks[number]
            # Codex说明(自动生成)： 检查条件 network['phase'] == 'delay'，根据结果选择后续执行路径。
            if network["phase"] == "delay":
                # Codex说明(自动生成)： 基于旧值更新 data.s，累积当前循环或处理步骤的结果。
                data.s *= np.exp(
                    -2j * np.pi * data.frequency_hz * network.get("delay_ns", 0) * 1e-9
                )[:, None, None]
            # Codex说明(自动生成)： 计算并保存 data.z0，供后续语句继续读取或更新。
            data.z0 = network.get("z0", 50)
            # Codex说明(自动生成)： 计算并保存 record['review_token']，供后续语句继续读取或更新。
            record["review_token"] = token
            # Codex说明(自动生成)： 计算并保存 record['review_status']，供后续语句继续读取或更新。
            record["review_status"] = "user-confirmed"
            # Codex说明(自动生成)： 返回 (data, output, family, record)，让调用方取得本函数的处理结果。
            return data, output, family, record
