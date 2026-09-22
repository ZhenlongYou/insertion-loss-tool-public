# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# re escapes temporary paths in parser diagnostics assertions.
import re
# Codex说明(自动生成)： 导入 subprocess，调用 git 或外部命令并读取返回结果。
import subprocess
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 unittest 导入 mock，组织单元测试和断言。
from unittest import mock
# Codex说明(自动生成)： 导入 warnings，提供本文件后续流程需要的库能力。
import warnings

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np

# Codex说明(自动生成)： 导入 insertion_loss_tool，提供本文件后续流程需要的库能力。
import insertion_loss_tool
# Codex说明(自动生成)： 从 insertion_loss_tool 导入 NetworkTransfer, select_transfer，提供本文件后续流程需要的库能力。
from insertion_loss_tool import NetworkTransfer, select_transfer

# Codex说明(自动生成)： 从 insertion_loss_tool.models 导入 TargetPoint, build_network, default_through_pairs, generate_frequency_axis 等名称，提供本文件后续流程需要的库能力。
from insertion_loss_tool.models import (
    TargetPoint,
    build_network,
    default_through_pairs,
    generate_frequency_axis,
    insert_draw_control_frequencies,
    interpolate_drawn_loss,
    linear_loss,
    modify_insertion_loss,
    parse_draw_points,
    parse_target_points,
    parse_frequency,
    resample_with_frequencies,
)
# Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 TouchstoneData, read_touchstone, to_magnitude_db, write_touchstone，提供本文件后续流程需要的库能力。
from insertion_loss_tool.touchstone import (
    TouchstoneData,
    read_touchstone,
    to_magnitude_db,
    write_touchstone,
)
# Codex说明(自动生成)： 导入 main as project_main，提供本文件后续流程需要的库能力。
import main as project_main


# Codex说明(自动生成)： 定义 InsertionLossToolTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class InsertionLossToolTests(unittest.TestCase):
    # Codex说明(自动生成)： 定义函数 test_direct_global_settings_use_the_selected_port_suffix，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_direct_global_settings_use_the_selected_port_suffix(self):
        # Codex说明(自动生成)： 进入上下文 mock.patch.object(project_main, 'OUTPUT_FILE', ''), mock.patch.dict(os.environ, {'INSERTION_LOSS_TOOL_OUTPU...，确保文件、资源或临时状态按作用域正确释放。
        with mock.patch.object(project_main, "OUTPUT_FILE", ""), mock.patch.dict(
            os.environ, {"INSERTION_LOSS_TOOL_OUTPUT_FILE": ""}, clear=False
        ):
            # Codex说明(自动生成)： 遍历 (2, 3, 4, 6, 8) 中的 ports，逐项执行循环体逻辑。
            for ports in (2, 3, 4, 6, 8):
                # Codex说明(自动生成)： 进入上下文 self.subTest(ports=ports), mock.patch.object(project_main, 'PORTS', ports)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(ports=ports), mock.patch.object(
                    project_main, "PORTS", ports
                ):
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(
                        project_main._configured_output("review").suffix,
                        f".s{ports}p",
                    )

    # Codex说明(自动生成)： 定义函数 test_direct_global_settings_generate_every_common_port_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_direct_global_settings_generate_every_common_port_count(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory(), mock.patch.object(project_main, 'ROOT', Path(tmp)), mock.patch.object(project_main, 'OUTPUT_FILE', '')，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            project_main, "ROOT", Path(tmp)
        ), mock.patch.object(project_main, "OUTPUT_FILE", ""), mock.patch.object(
            project_main, "RUN_MODE", "linear"
        ), mock.patch.object(project_main, "F_START", "1GHz"), mock.patch.object(
            project_main, "F_STOP", "2GHz"
        ), mock.patch.object(project_main, "POINTS", 5), mock.patch.object(
            project_main, "LINEAR_LOSS_START_DB", 1.0
        ), mock.patch.object(
            project_main, "LINEAR_LOSS_STOP_DB", 4.0
        ), mock.patch.object(
            project_main, "SHOW_PLOTS", False
        ), mock.patch.object(
            project_main, "SAVE_PLOT_FILES", False
        ), mock.patch.object(
            sys, "argv", ["main.py"]
        ), mock.patch.dict(
            os.environ, {"INSERTION_LOSS_TOOL_OUTPUT_FILE": ""}, clear=False
        ):
            # Codex说明(自动生成)： 遍历 (2, 3, 4, 6, 8) 中的 ports，逐项执行循环体逻辑。
            for ports in (2, 3, 4, 6, 8):
                # Codex说明(自动生成)： 进入上下文 self.subTest(ports=ports), mock.patch.object(project_main, 'PORTS', ports)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(ports=ports), mock.patch.object(
                    project_main, "PORTS", ports
                ):
                    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                    output = Path(tmp) / "examples" / f"linear_configured.s{ports}p"
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(project_main.main(), 0)
                    # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
                    self.assertEqual(read_touchstone(output).n_ports, ports)

    # Codex说明(自动生成)： 定义函数 test_common_port_defaults_use_independent_adjacent_lanes，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_common_port_defaults_use_independent_adjacent_lanes(self):
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(default_through_pairs(2), [(1, 0), (0, 1)])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(default_through_pairs(3), [(1, 0), (0, 1)])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            default_through_pairs(6),
            [(1, 0), (0, 1), (3, 2), (2, 3), (5, 4), (4, 5)],
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            default_through_pairs(8),
            [
                (1, 0),
                (0, 1),
                (3, 2),
                (2, 3),
                (5, 4),
                (4, 5),
                (7, 6),
                (6, 7),
            ],
        )
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'Supported port coun...，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "Supported port counts"):
            # Codex说明(自动生成)： 调用 default_through_pairs，执行当前流程需要的具体操作或副作用。
            default_through_pairs(5)

    # Codex说明(自动生成)： 定义函数 test_cli_generates_an_eight_port_common_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_cli_generates_an_eight_port_common_network(self):
        # Codex说明(自动生成)： 计算并保存 project_root，供后续语句继续读取或更新。
        project_root = Path(__file__).resolve().parents[1]
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = Path(tmp) / "common.s8p"
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "main.py"),
                    "linear",
                    "--ports",
                    "8",
                    "--f-start",
                    "1GHz",
                    "--f-stop",
                    "2GHz",
                    "--points",
                    "5",
                    "--loss-start-db",
                    "1",
                    "--loss-stop-db",
                    "4",
                    "--output",
                    str(output),
                    "--no-show-plot",
                    "--no-save-plot-files",
                ],
                cwd=tempfile.gettempdir(),
                text=True,
                capture_output=True,
                check=False,
            )

            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(read_touchstone(output).n_ports, 8)

    # Codex说明(自动生成)： 定义函数 test_select_transfer_uses_output_input_matrix_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_select_transfer_uses_output_input_matrix_order(self):
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = TouchstoneData(
            frequency_hz=np.array([1e9, 2e9]),
            s=np.array(
                [
                    [[0.0, 0.1], [0.5, 0.0]],
                    [[0.0, 0.2], [0.25, 0.0]],
                ],
                dtype=complex,
            ),
            z0=50.0,
        )

        # Codex说明(自动生成)： 计算并保存 transfer，供后续语句继续读取或更新。
        transfer = select_transfer(network, output_port=2, input_port=1)

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(transfer.frequency_hz, np.array([1e9, 2e9]))
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(transfer.response, np.array([0.5, 0.25]))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(transfer.path, "S21")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(transfer.z0_ohm, 50.0)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_accepts_dc_frequency，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_accepts_dc_frequency(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "starts_at_dc.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(
                "# Hz S RI R 50\n"
                "0 0 0 0.5 0 0.25 0 0 0\n"
                "1 0 0 0.25 0 0.125 0 0 0\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.frequency_hz, np.array([0.0, 1.0]))

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_allows_an_explicit_default_frequency_unit，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_allows_an_explicit_default_frequency_unit(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "implicit_frequency_unit.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(
                "0 0 0 0.5 0 0.25 0 0 0\n"
                "2 0 0 0.25 0 0.125 0 0 0\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path, default_frequency_unit=" hz ")

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.frequency_hz, np.array([0.0, 2.0]))

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_keeps_ghz_as_the_public_default，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_keeps_ghz_as_the_public_default(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 implicit_path，供后续语句继续读取或更新。
            implicit_path = Path(tmp) / "implicit_standard_default.s2p"
            # Codex说明(自动生成)： 调用 implicit_path.write_text 写出文件或数据，保存当前处理结果。
            implicit_path.write_text(
                "0 0 0 0.5 0 0.25 0 0 0\n"
                "2 0 0 0.25 0 0.125 0 0 0\n",
                encoding="ascii",
            )
            # Codex说明(自动生成)： 计算并保存 explicit_path，供后续语句继续读取或更新。
            explicit_path = Path(tmp) / "explicit_option.s2p"
            # Codex说明(自动生成)： 调用 explicit_path.write_text 写出文件或数据，保存当前处理结果。
            explicit_path.write_text(
                "# MHz S RI R 50\n"
                "0 0 0 0.5 0 0.25 0 0 0\n"
                "2 0 0 0.25 0 0.125 0 0 0\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 计算并保存 implicit，供后续语句继续读取或更新。
            implicit = read_touchstone(implicit_path)
            # Codex说明(自动生成)： 计算并保存 explicit，供后续语句继续读取或更新。
            explicit = read_touchstone(
                explicit_path,
                default_frequency_unit="hz",
            )

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(
            implicit.frequency_hz,
            np.array([0.0, 2e9]),
        )
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(
            explicit.frequency_hz,
            np.array([0.0, 2e6]),
        )

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_validates_default_frequency_unit，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_validates_default_frequency_unit(self):
        # Codex说明(自动生成)： 遍历 (None, True, 1) 中的 invalid_type，逐项执行循环体逻辑。
        for invalid_type in (None, True, 1):
            # Codex说明(自动生成)： 进入上下文 self.subTest(invalid_type=invalid_type), self.assertRaises(TypeError)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(invalid_type=invalid_type), self.assertRaises(TypeError):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone("unused.s2p", default_frequency_unit=invalid_type)
        # Codex说明(自动生成)： 遍历 ('', 'seconds', 'mhz_per_second') 中的 invalid_value，逐项执行循环体逻辑。
        for invalid_value in ("", "seconds", "mhz_per_second"):
            # Codex说明(自动生成)： 进入上下文 self.subTest(invalid_value=invalid_value), self.assertRaisesRegex(ValueError, 'default_frequency_u...，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(invalid_value=invalid_value), self.assertRaisesRegex(
                ValueError,
                "default_frequency_unit",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone("unused.s2p", default_frequency_unit=invalid_value)

    # Codex说明(自动生成)： 定义函数 test_select_transfer_rejects_malformed_network_matrix，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_select_transfer_rejects_malformed_network_matrix(self):
        # Codex说明(自动生成)： 计算并保存 malformed，供后续语句继续读取或更新。
        malformed = TouchstoneData(
            frequency_hz=np.array([1e9]),
            s=np.array([0.5 + 0.0j]),
        )

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'three-dimensional')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "three-dimensional"):
            # Codex说明(自动生成)： 调用 select_transfer，执行当前流程需要的具体操作或副作用。
            select_transfer(malformed, output_port=1, input_port=1)

    # Codex说明(自动生成)： 定义函数 test_network_transfer_owns_bytes_backed_immutable_arrays，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_network_transfer_owns_bytes_backed_immutable_arrays(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([0.0, 1e9], dtype=np.float32)
        # Codex说明(自动生成)： 计算并保存 response，供后续语句继续读取或更新。
        response = np.array([0.5, 0.25j], dtype=np.complex64)

        # Codex说明(自动生成)： 计算并保存 transfer，供后续语句继续读取或更新。
        transfer = NetworkTransfer(frequency, response, " S21 ", np.float64(50.0))
        # Codex说明(自动生成)： 计算并保存 frequency[:]，供后续语句继续读取或更新。
        frequency[:] = 7.0
        # Codex说明(自动生成)： 计算并保存 response[:]，供后续语句继续读取或更新。
        response[:] = 9.0

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(transfer.frequency_hz, np.array([0.0, 1e9]))
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(transfer.response, np.array([0.5, 0.25j]))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(transfer.frequency_hz.dtype, np.dtype(np.float64))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(transfer.response.dtype, np.dtype(np.complex128))
        # Codex说明(自动生成)： 调用 self.assertIsInstance 检查测试期望，确认实际结果符合预期。
        self.assertIsInstance(transfer.frequency_hz.base, bytes)
        # Codex说明(自动生成)： 调用 self.assertIsInstance 检查测试期望，确认实际结果符合预期。
        self.assertIsInstance(transfer.response.base, bytes)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(transfer.path, "S21")
        # Codex说明(自动生成)： 进入上下文 self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaises(ValueError):
            # Codex说明(自动生成)： 计算并保存 transfer.frequency_hz[0]，供后续语句继续读取或更新。
            transfer.frequency_hz[0] = 1.0
        # Codex说明(自动生成)： 进入上下文 self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaises(ValueError):
            # Codex说明(自动生成)： 计算并保存 transfer.response[0]，供后续语句继续读取或更新。
            transfer.response[0] = 1.0
        # Codex说明(自动生成)： 进入上下文 self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaises(ValueError):
            # Codex说明(自动生成)： 调用 transfer.frequency_hz.setflags，执行当前流程需要的具体操作或副作用。
            transfer.frequency_hz.setflags(write=True)
        # Codex说明(自动生成)： 进入上下文 self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaises(ValueError):
            # Codex说明(自动生成)： 调用 transfer.response.setflags，执行当前流程需要的具体操作或副作用。
            transfer.response.setflags(write=True)

    # Codex说明(自动生成)： 定义函数 test_network_transfer_is_frozen_slotted_and_uses_public_field_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_network_transfer_is_frozen_slotted_and_uses_public_field_order(self):
        # Codex说明(自动生成)： 计算并保存 transfer，供后续语句继续读取或更新。
        transfer = NetworkTransfer(np.array([0.0]), np.array([1.0]), "S21", 50.0)

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            tuple(NetworkTransfer.__dataclass_fields__),
            ("frequency_hz", "response", "path", "z0_ohm"),
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            NetworkTransfer.__slots__,
            ("frequency_hz", "response", "path", "z0_ohm"),
        )
        # Codex说明(自动生成)： 调用 self.assertNotEqual 检查测试期望，确认实际结果符合预期。
        self.assertNotEqual(
            transfer,
            NetworkTransfer(np.array([0.0]), np.array([1.0]), "S21", 50.0),
        )
        # Codex说明(自动生成)： 进入上下文 self.assertRaises(AttributeError)，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaises(AttributeError):
            # Codex说明(自动生成)： 计算并保存 transfer.path，供后续语句继续读取或更新。
            transfer.path = "S12"

    # Codex说明(自动生成)： 定义函数 test_network_transfer_constructor_rejects_invalid_values，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_network_transfer_constructor_rejects_invalid_values(self):
        # Codex说明(自动生成)： 计算并保存 invalid_arguments，供后续语句继续读取或更新。
        invalid_arguments = (
            (np.array([]), np.array([]), "S21", 50.0),
            (np.array([[0.0]]), np.array([1.0]), "S21", 50.0),
            (np.array([0.0]), np.array([[1.0]]), "S21", 50.0),
            (np.array([0.0, 1.0]), np.array([1.0]), "S21", 50.0),
            (np.array([-1.0]), np.array([1.0]), "S21", 50.0),
            (np.array([0.0, 0.0]), np.array([1.0, 1.0]), "S21", 50.0),
            (np.array([0.0, np.inf]), np.array([1.0, 1.0]), "S21", 50.0),
            (np.array([0.0]), np.array([np.nan + 0.0j]), "S21", 50.0),
            (np.array([0.0]), np.array([1.0 + np.inf * 1j]), "S21", 50.0),
            (np.array([0.0]), np.array([1.0]), " ", 50.0),
            (np.array([0.0]), np.array([1.0]), 21, 50.0),
            (np.array([0.0]), np.array([1.0]), "S21", True),
            (np.array([0.0]), np.array([1.0]), "S21", 0.0),
            (np.array([0.0]), np.array([1.0]), "S21", np.inf),
        )
        # Codex说明(自动生成)： 遍历 invalid_arguments 中的 arguments，逐项执行循环体逻辑。
        for arguments in invalid_arguments:
            # Codex说明(自动生成)： 进入上下文 self.subTest(arguments=arguments), self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                # Codex说明(自动生成)： 调用 NetworkTransfer，执行当前流程需要的具体操作或副作用。
                NetworkTransfer(*arguments)

    # Codex说明(自动生成)： 定义函数 test_network_transfer_reports_overflow_as_field_value_errors，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_network_transfer_reports_overflow_as_field_value_errors(self):
        # Codex说明(自动生成)： 计算并保存 huge，供后续语句继续读取或更新。
        huge = 10**400
        # Codex说明(自动生成)： 计算并保存 constructor_cases，供后续语句继续读取或更新。
        constructor_cases = (
            (([huge], [1.0], "S21", 50.0), "frequency_hz"),
            (([0.0], [huge], "S21", 50.0), "response"),
            (([0.0], [1.0], "S21", huge), "z0_ohm"),
        )
        # Codex说明(自动生成)： 遍历 constructor_cases 中的 (arguments, field_name)，逐项执行循环体逻辑。
        for arguments, field_name in constructor_cases:
            # Codex说明(自动生成)： 进入上下文 self.subTest(field_name=field_name), self.assertRaisesRegex(ValueError, field_name)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError,
                field_name,
            ):
                # Codex说明(自动生成)： 调用 NetworkTransfer，执行当前流程需要的具体操作或副作用。
                NetworkTransfer(*arguments)

        # Codex说明(自动生成)： 计算并保存 malformed_networks，供后续语句继续读取或更新。
        malformed_networks = (
            (
                TouchstoneData(
                    np.array([huge], dtype=object),
                    np.zeros((1, 1, 1)),
                ),
                "frequency_hz",
            ),
            (
                TouchstoneData(
                    np.array([1e9]),
                    np.array([[[huge]]], dtype=object),
                ),
                "S-parameter matrix",
            ),
            (
                TouchstoneData(np.array([1e9]), np.zeros((1, 1, 1)), z0=huge),
                "z0",
            ),
        )
        # Codex说明(自动生成)： 遍历 malformed_networks 中的 (network, field_name)，逐项执行循环体逻辑。
        for network, field_name in malformed_networks:
            # Codex说明(自动生成)： 进入上下文 self.subTest(field_name=field_name), self.assertRaisesRegex(ValueError, field_name)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError,
                field_name,
            ):
                # Codex说明(自动生成)： 调用 select_transfer，执行当前流程需要的具体操作或副作用。
                select_transfer(network, output_port=1, input_port=1)

    # Codex说明(自动生成)： 定义函数 test_select_transfer_distinguishes_s12_and_selects_arbitrary_s4p_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_select_transfer_distinguishes_s12_and_selects_arbitrary_s4p_path(self):
        # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
        s = np.zeros((2, 4, 4), dtype=complex)
        # Codex说明(自动生成)： 计算并保存 s[:, 1, 0]，供后续语句继续读取或更新。
        s[:, 1, 0] = [0.5, 0.25]
        # Codex说明(自动生成)： 计算并保存 s[:, 0, 1]，供后续语句继续读取或更新。
        s[:, 0, 1] = [0.1, 0.2]
        # Codex说明(自动生成)： 计算并保存 s[:, 3, 1]，供后续语句继续读取或更新。
        s[:, 3, 1] = [0.42 + 0.1j, 0.24 - 0.2j]
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = TouchstoneData(np.array([1e9, 2e9]), s, z0=75.0)

        # Codex说明(自动生成)： 计算并保存 s12，供后续语句继续读取或更新。
        s12 = select_transfer(network, output_port=1, input_port=2)
        # Codex说明(自动生成)： 计算并保存 s42，供后续语句继续读取或更新。
        s42 = select_transfer(network, output_port=np.int64(4), input_port=np.int64(2))

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(s12.response, np.array([0.1, 0.2]))
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(s12.path, "S12")
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(
            s42.response,
            np.array([0.42 + 0.1j, 0.24 - 0.2j]),
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(s42.path, "S42")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(s42.z0_ohm, 75.0)

    # Codex说明(自动生成)： 定义函数 test_select_transfer_rejects_invalid_or_boolean_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_select_transfer_rejects_invalid_or_boolean_ports(self):
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = TouchstoneData(
            np.array([1e9]),
            np.zeros((1, 2, 2), dtype=complex),
        )

        # Codex说明(自动生成)： 遍历 ((True, 1), (1, False), (1.0, 1), (1, '2')) 中的 (output_port, input_port)，逐项执行循环体逻辑。
        for output_port, input_port in ((True, 1), (1, False), (1.0, 1), (1, "2")):
            # Codex说明(自动生成)： 进入上下文 self.subTest(output_port=output_port, input_port=input_...，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(output_port=output_port, input_port=input_port):
                # Codex说明(自动生成)： 进入上下文 self.assertRaises(TypeError)，确保文件、资源或临时状态按作用域正确释放。
                with self.assertRaises(TypeError):
                    # Codex说明(自动生成)： 调用 select_transfer，执行当前流程需要的具体操作或副作用。
                    select_transfer(
                        network,
                        output_port=output_port,
                        input_port=input_port,
                    )
        # Codex说明(自动生成)： 遍历 ((0, 1), (3, 1), (1, 0), (1, 3)) 中的 (output_port, input_port)，逐项执行循环体逻辑。
        for output_port, input_port in ((0, 1), (3, 1), (1, 0), (1, 3)):
            # Codex说明(自动生成)： 进入上下文 self.subTest(output_port=output_port, input_port=input_...，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(output_port=output_port, input_port=input_port):
                # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'outside')，确保文件、资源或临时状态按作用域正确释放。
                with self.assertRaisesRegex(ValueError, "outside"):
                    # Codex说明(自动生成)： 调用 select_transfer，执行当前流程需要的具体操作或副作用。
                    select_transfer(
                        network,
                        output_port=output_port,
                        input_port=input_port,
                    )

    # Codex说明(自动生成)： 定义函数 test_select_transfer_uses_authority_validation_before_selection，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_select_transfer_uses_authority_validation_before_selection(self):
        # Codex说明(自动生成)： 计算并保存 malformed_networks，供后续语句继续读取或更新。
        malformed_networks = (
            TouchstoneData(np.array([1e9, 2e9]), np.zeros((1, 2, 2))),
            TouchstoneData(np.array([1e9]), np.zeros((1, 2, 3))),
            TouchstoneData(np.array([1e9]), np.full((1, 2, 2), np.nan)),
            TouchstoneData(np.array([1e9]), np.zeros((1, 2, 2)), z0=True),
        )

        # Codex说明(自动生成)： 遍历 malformed_networks 中的 network，逐项执行循环体逻辑。
        for network in malformed_networks:
            # Codex说明(自动生成)： 进入上下文 self.subTest(network=network), self.assertRaises(ValueError)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(network=network), self.assertRaises(ValueError):
                # Codex说明(自动生成)： 调用 select_transfer，执行当前流程需要的具体操作或副作用。
                select_transfer(network, output_port=1, input_port=1)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_rejects_negative_and_duplicate_frequencies，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_rejects_negative_and_duplicate_frequencies(self):
        # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
        cases = (
            (
                "negative.s2p",
                "# Hz S RI R 50\n-1 0 0 0.5 0 0 0 0 0\n",
                "non-negative",
            ),
            (
                "duplicate.s2p",
                "# Hz S RI R 50\n0 0 0 0.5 0 0 0 0 0\n0 0 0 0.25 0 0 0 0 0\n",
                "strictly increasing",
            ),
            (
                "descending.s2p",
                "# Hz S RI R 50\n2 0 0 0.5 0 0 0 0 0\n1 0 0 0.25 0 0 0 0 0\n",
                "strictly increasing",
            ),
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 遍历 cases 中的 (name, contents, message)，逐项执行循环体逻辑。
            for name, contents, message in cases:
                # Codex说明(自动生成)： 进入上下文 self.subTest(name=name)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(name=name):
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / name
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text(contents, encoding="ascii")
                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, message)，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(ValueError, message):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_rejects_adjacent_s2p_rows_that_borrow_tokens，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_rejects_adjacent_s2p_rows_that_borrow_tokens(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "borrowed_tokens.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(
                "# Hz S RI R 50\n"
                "1 0 0 0.5 0 0.25 0 0\n"
                "2 3 0 0.25 0 0.125 0 0 0 999\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(
                ValueError,
                rf"{re.escape(str(path))}:2:.*expected 9 numeric values",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_rejects_invalid_s4p_continuation_records，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_rejects_invalid_s4p_continuation_records(self):
        # Codex说明(自动生成)： 计算并保存 initial，供后续语句继续读取或更新。
        initial = "1 0 0 0 0 0 0 0 0"
        # Codex说明(自动生成)： 计算并保存 continuation，供后续语句继续读取或更新。
        continuation = "0 0 0 0 0 0 0 0"
        # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
        cases = (
            (
                "truncated_line.s4p",
                "# Hz S RI R 50\n" + initial + "\n0 0 0 0 0 0 0\n",
                3,
                "expected 1 to 4 complex pairs, got 7 numeric values",
            ),
            (
                "truncated_eof.s4p",
                "# Hz S RI R 50\n"
                + initial
                + "\n"
                + continuation
                + "\n"
                + continuation
                + "\n",
                2,
                "truncated S4P record at end of file",
            ),
            (
                "excess_continuation.s4p",
                "# Hz S RI R 50\n"
                + initial
                + "\n"
                + "\n".join([continuation] * 4)
                + "\n",
                6,
                "must start with a frequency and 1 to 4 complex pairs",
            ),
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 遍历 cases 中的 (name, contents, line_number, message)，逐项执行循环体逻辑。
            for name, contents, line_number, message in cases:
                # Codex说明(自动生成)： 进入上下文 self.subTest(name=name)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(name=name):
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / name
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text(contents, encoding="ascii")
                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(
                        ValueError,
                        rf"{re.escape(str(path))}:{line_number}:.*{message}",
                    ):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_touchstone_public_api_exports_channel_network_interface，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_public_api_exports_channel_network_interface(self):
        # Codex说明(自动生成)： 计算并保存 expected_names，供后续语句继续读取或更新。
        expected_names = {
            "TouchstoneData",
            "NetworkTransfer",
            "read_touchstone",
            "write_touchstone",
            "select_transfer",
            "to_magnitude_db",
            "__version__",
        }

        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(expected_names.issubset(set(insertion_loss_tool.__all__)))
        # Codex说明(自动生成)： 遍历 expected_names 中的 name，逐项执行循环体逻辑。
        for name in expected_names:
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(hasattr(insertion_loss_tool, name), name)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(insertion_loss_tool.__version__, "0.6.0")

    # Codex说明(自动生成)： 定义函数 test_main_py_runs_from_global_settings_without_cli_args，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_main_py_runs_from_global_settings_without_cli_args(self):
        # Codex说明(自动生成)： 计算并保存 project_root，供后续语句继续读取或更新。
        project_root = Path(__file__).resolve().parents[1]
        # Codex说明(自动生成)： 计算并保存 env，供后续语句继续读取或更新。
        env = {**os.environ, "INSERTION_LOSS_TOOL_NO_SHOW": "1"}
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = Path(tmp) / f"configured.s{project_main.PORTS}p"
            # Codex说明(自动生成)： 计算并保存 env['INSERTION_LOSS_TOOL_OUTPUT_FILE']，供后续语句继续读取或更新。
            env["INSERTION_LOSS_TOOL_OUTPUT_FILE"] = str(output)
            # Codex说明(自动生成)： 检查条件 project_main.RUN_MODE.strip().lower() == 'draw' and (no...，根据结果选择后续执行路径。
            if (
                project_main.RUN_MODE.strip().lower() == "draw"
                and not project_main.DRAW_CONTROL_POINTS
            ):
                # Codex说明(自动生成)： 计算并保存 env['INSERTION_LOSS_TOOL_DRAW_POINTS']，供后续语句继续读取或更新。
                env["INSERTION_LOSS_TOOL_DRAW_POINTS"] = (
                    f"{project_main.F_START}:-0.2,{project_main.F_STOP}:-20.0"
                )

            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = subprocess.run(
                [sys.executable, str(project_root / "main.py")],
                cwd=tempfile.gettempdir(),
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
            self.assertTrue(output.exists(), f"missing output: {output}")

    # Codex说明(自动生成)： 定义函数 test_direct_global_settings_show_plots_without_saving_pngs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_direct_global_settings_show_plots_without_saving_pngs(self):
        # Codex说明(自动生成)： 计算并保存 old_no_show，供后续语句继续读取或更新。
        old_no_show = os.environ.pop("INSERTION_LOSS_TOOL_NO_SHOW", None)
        # Codex说明(自动生成)： 计算并保存 old_save_plots，供后续语句继续读取或更新。
        old_save_plots = os.environ.pop("INSERTION_LOSS_TOOL_SAVE_PLOTS", None)
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 argv，供后续语句继续读取或更新。
            argv = project_main._argv_from_global_settings()
        # Codex说明(自动生成)： 无论前面是否出错，都执行这里的资源释放或收尾逻辑。
        finally:
            # Codex说明(自动生成)： 检查条件 old_no_show is not None，根据结果选择后续执行路径。
            if old_no_show is not None:
                # Codex说明(自动生成)： 计算并保存 os.environ['INSERTION_LOSS_TOOL_NO_SHOW']，供后续语句继续读取或更新。
                os.environ["INSERTION_LOSS_TOOL_NO_SHOW"] = old_no_show
            # Codex说明(自动生成)： 检查条件 old_save_plots is not None，根据结果选择后续执行路径。
            if old_save_plots is not None:
                # Codex说明(自动生成)： 计算并保存 os.environ['INSERTION_LOSS_TOOL_SAVE_PLOTS']，供后续语句继续读取或更新。
                os.environ["INSERTION_LOSS_TOOL_SAVE_PLOTS"] = old_save_plots

        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--show-plot", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--no-save-plot-files", argv)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("--no-plot", argv)

    # Codex说明(自动生成)： 定义函数 test_direct_global_settings_support_draw_mode，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_direct_global_settings_support_draw_mode(self):
        # Codex说明(自动生成)： 计算并保存 old_draw_points_env，供后续语句继续读取或更新。
        old_draw_points_env = os.environ.pop("INSERTION_LOSS_TOOL_DRAW_POINTS", None)
        # Codex说明(自动生成)： 计算并保存 old_values，供后续语句继续读取或更新。
        old_values = {
            "RUN_MODE": project_main.RUN_MODE,
            "F_START": project_main.F_START,
            "F_STOP": project_main.F_STOP,
            "POINTS": project_main.POINTS,
            "DRAW_CONTROL_POINTS": project_main.DRAW_CONTROL_POINTS,
        }
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 project_main.RUN_MODE，供后续语句继续读取或更新。
            project_main.RUN_MODE = "draw"
            # Codex说明(自动生成)： 计算并保存 project_main.F_START，供后续语句继续读取或更新。
            project_main.F_START = "1GHz"
            # Codex说明(自动生成)： 计算并保存 project_main.F_STOP，供后续语句继续读取或更新。
            project_main.F_STOP = "3GHz"
            # Codex说明(自动生成)： 计算并保存 project_main.POINTS，供后续语句继续读取或更新。
            project_main.POINTS = 5
            # Codex说明(自动生成)： 计算并保存 project_main.DRAW_CONTROL_POINTS，供后续语句继续读取或更新。
            project_main.DRAW_CONTROL_POINTS = ["1GHz:-1.0", "3GHz:-3.0"]

            # Codex说明(自动生成)： 计算并保存 argv，供后续语句继续读取或更新。
            argv = project_main._argv_from_global_settings()
        # Codex说明(自动生成)： 无论前面是否出错，都执行这里的资源释放或收尾逻辑。
        finally:
            # Codex说明(自动生成)： 遍历 old_values.items() 中的 (name, value)，逐项执行循环体逻辑。
            for name, value in old_values.items():
                # Codex说明(自动生成)： 调用 setattr，执行当前流程需要的具体操作或副作用。
                setattr(project_main, name, value)
            # Codex说明(自动生成)： 检查条件 old_draw_points_env is not None，根据结果选择后续执行路径。
            if old_draw_points_env is not None:
                # Codex说明(自动生成)： 计算并保存 os.environ['INSERTION_LOSS_TOOL_DRAW_POINTS']，供后续语句继续读取或更新。
                os.environ["INSERTION_LOSS_TOOL_DRAW_POINTS"] = old_draw_points_env

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(argv[0], "draw")
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--draw-point", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("1GHz:-1.0", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("3GHz:-3.0", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--draw-fit", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("smooth", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--draw-min-spacing-fraction", argv)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--draw-max-slope-db-per-span", argv)

    # Codex说明(自动生成)： 定义函数 test_run_command_wrapper_exits_successfully，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_run_command_wrapper_exits_successfully(self):
        # Codex说明(自动生成)： 检查条件 os.name == 'nt'，根据结果选择后续执行路径。
        if os.name == "nt":
            # Codex说明(自动生成)： 调用 self.skipTest，执行当前流程需要的具体操作或副作用。
            self.skipTest("run.command is a macOS zsh launcher, not a Windows executable")
        # Codex说明(自动生成)： 计算并保存 project_root，供后续语句继续读取或更新。
        project_root = Path(__file__).resolve().parents[1]
        # Codex说明(自动生成)： 计算并保存 wrapper，供后续语句继续读取或更新。
        wrapper = project_root / "run.command"
        # Codex说明(自动生成)： 检查条件 not wrapper.exists()，根据结果选择后续执行路径。
        if not wrapper.exists():
            # Codex说明(自动生成)： 调用 self.skipTest，执行当前流程需要的具体操作或副作用。
            self.skipTest("run.command is only present in the packaged macOS project")

        # Codex说明(自动生成)： 计算并保存 env，供后续语句继续读取或更新。
        env = {**os.environ, "INSERTION_LOSS_TOOL_NO_SHOW": "1"}
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 env['INSERTION_LOSS_TOOL_OUTPUT_FILE']，供后续语句继续读取或更新。
            env["INSERTION_LOSS_TOOL_OUTPUT_FILE"] = str(Path(tmp) / "wrapper.s2p")
            # Codex说明(自动生成)： 检查条件 project_main.RUN_MODE.strip().lower() == 'draw' and (no...，根据结果选择后续执行路径。
            if (
                project_main.RUN_MODE.strip().lower() == "draw"
                and not project_main.DRAW_CONTROL_POINTS
            ):
                # Codex说明(自动生成)： 计算并保存 env['INSERTION_LOSS_TOOL_DRAW_POINTS']，供后续语句继续读取或更新。
                env["INSERTION_LOSS_TOOL_DRAW_POINTS"] = (
                    f"{project_main.F_START}:-0.2,{project_main.F_STOP}:-20.0"
                )
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = subprocess.run(
                [str(wrapper)],
                input="\n",
                cwd=tempfile.gettempdir(),
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Exit code: 0", result.stdout)

    # Codex说明(自动生成)： 定义函数 test_s2p_round_trip_preserves_touchstone_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s2p_round_trip_preserves_touchstone_order(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 2e9])
        # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
        s = np.zeros((2, 2, 2), dtype=complex)
        # Codex说明(自动生成)： 计算并保存 s[:, 0, 0]，供后续语句继续读取或更新。
        s[:, 0, 0] = 0.11
        # Codex说明(自动生成)： 计算并保存 s[:, 1, 0]，供后续语句继续读取或更新。
        s[:, 1, 0] = 0.21
        # Codex说明(自动生成)： 计算并保存 s[:, 0, 1]，供后续语句继续读取或更新。
        s[:, 0, 1] = 0.12
        # Codex说明(自动生成)： 计算并保存 s[:, 1, 1]，供后续语句继续读取或更新。
        s[:, 1, 1] = 0.22
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, np.array([1.0, 2.0]))
        # Codex说明(自动生成)： 计算并保存 data.s，供后续语句继续读取或更新。
        data.s = s

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "roundtrip.s2p"
            # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
            write_touchstone(data, path)
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.s[:, 1, 0], 0.21)
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.s[:, 0, 1], 0.12)

    # Codex说明(自动生成)： 定义函数 test_s4p_round_trip_preserves_matrix_order，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s4p_round_trip_preserves_matrix_order(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9])
        # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
        s = np.zeros((1, 4, 4), dtype=complex)
        # Codex说明(自动生成)： 遍历 range(4) 中的 out_port，逐项执行循环体逻辑。
        for out_port in range(4):
            # Codex说明(自动生成)： 遍历 range(4) 中的 in_port，逐项执行循环体逻辑。
            for in_port in range(4):
                # Codex说明(自动生成)： 计算并保存 real，供后续语句继续读取或更新。
                real = 10 * (out_port + 1) + (in_port + 1)
                # Codex说明(自动生成)： 计算并保存 imag，供后续语句继续读取或更新。
                imag = -real / 100.0
                # Codex说明(自动生成)： 计算并保存 s[0, out_port, in_port]，供后续语句继续读取或更新。
                s[0, out_port, in_port] = real + 1j * imag

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "roundtrip.s4p"
            # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
            write_touchstone(TouchstoneData(frequency, s), path)
            # Codex说明(自动生成)： 计算并保存 data_lines，供后续语句继续读取或更新。
            data_lines = [
                line.split()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith(("!", "#"))
            ]
            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual([len(line) for line in data_lines], [9, 8, 8, 8])
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.s, s)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_s4p_accepts_9_plus_24_token_continuation，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_s4p_accepts_9_plus_24_token_continuation(self):
        # Codex说明(自动生成)： 计算并保存 first_line，供后续语句继续读取或更新。
        first_line = " ".join(["1", *("0" for _ in range(8))])
        # Codex说明(自动生成)： 计算并保存 second_line，供后续语句继续读取或更新。
        second_line = " ".join("0" for _ in range(24))
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 2.0",
                "# Hz S RI R 50",
                "[Number of Ports] 4",
                "[Number of Frequencies] 1",
                "[Matrix Format] Full",
                "[Network Data]",
                first_line,
                second_line,
                "[End]",
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "arbitrary_continuation.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.frequency_hz, np.array([1.0]))
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.s, np.zeros((1, 4, 4), dtype=complex))

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_s4p_accepts_multiple_arbitrary_continuation_splits，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_s4p_accepts_multiple_arbitrary_continuation_splits(self):
        # Codex说明(自动生成)： 计算并保存 first_record，供后续语句继续读取或更新。
        first_record = ["1", *("0" for _ in range(32))]
        # Codex说明(自动生成)： 计算并保存 second_record，供后续语句继续读取或更新。
        second_record = ["2", *("0" for _ in range(32))]
        # Codex说明(自动生成)： 计算并保存 data_lines，供后续语句继续读取或更新。
        data_lines = [
            " ".join(first_record[:1]),
            " ".join(first_record[1:6]),
            " ".join(first_record[6:]),
            " ".join(second_record[:17]),
            " ".join(second_record[17:]),
        ]
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 2.0",
                "# Hz S RI R 50",
                "[Number of Ports] 4",
                "[Number of Frequencies] 2",
                "[Network Data]",
                *data_lines,
                "[End]",
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "multiple_arbitrary_continuations.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.frequency_hz, np.array([1.0, 2.0]))
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.s, np.zeros((2, 4, 4), dtype=complex))

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_declared_frequency_mismatch_reports_keyword_line，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_declared_frequency_mismatch_reports_keyword_line(self):
        # Codex说明(自动生成)： 计算并保存 record，供后续语句继续读取或更新。
        record = " ".join(["1", *("0" for _ in range(32))])
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 2.0",
                "# Hz S RI R 50",
                "[Number of Ports] 4",
                "[Number of Frequencies] 2",
                "[Network Data]",
                record,
                "[End]",
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "declared_count_mismatch.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(
                ValueError,
                rf"{re.escape(str(path))}:4:.*declares 2.*parsed 1",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_incomplete_record_before_keyword_reports_token_origin，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_incomplete_record_before_keyword_reports_token_origin(self):
        # Codex说明(自动生成)： 计算并保存 partial_record，供后续语句继续读取或更新。
        partial_record = " ".join(["1", *("0" for _ in range(8))])
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 2.0",
                "# Hz S RI R 50",
                "[Number of Ports] 4",
                "[Number of Frequencies] 1",
                "[Network Data]",
                partial_record,
                "[End]",
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "keyword_before_complete.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(
                ValueError,
                rf"{re.escape(str(path))}:7:.*started at line 6.*expected 33.*got 9",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_incomplete_record_at_eof_reports_token_origin，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_incomplete_record_at_eof_reports_token_origin(self):
        # Codex说明(自动生成)： 计算并保存 partial_record，供后续语句继续读取或更新。
        partial_record = " ".join(["1", *("0" for _ in range(11))])
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 2.0",
                "# Hz S RI R 50",
                "[Number of Ports] 4",
                "[Number of Frequencies] 1",
                "[Network Data]",
                partial_record,
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "incomplete_at_eof.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(
                ValueError,
                rf"{re.escape(str(path))}:6:.*end of file.*expected 33.*got 12",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_rejects_single_line_and_cumulative_record_excess，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_rejects_single_line_and_cumulative_record_excess(self):
        # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
        cases = (
            ("single_line.s4p", [34], 6, 6),
            ("cumulative.s4p", [20, 14], 7, 6),
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 遍历 cases 中的 (name, line_lengths, error_line, start_line)，逐项执行循环体逻辑。
            for name, line_lengths, error_line, start_line in cases:
                # Codex说明(自动生成)： 进入上下文 self.subTest(name=name)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(name=name):
                    # Codex说明(自动生成)： 计算并保存 tokens，供后续语句继续读取或更新。
                    tokens = ["1", *("0" for _ in range(33))]
                    # Codex说明(自动生成)： 计算并保存 data_lines，供后续语句继续读取或更新。
                    data_lines = []
                    # Codex说明(自动生成)： 计算并保存 start，供后续语句继续读取或更新。
                    start = 0
                    # Codex说明(自动生成)： 遍历 line_lengths 中的 line_length，逐项执行循环体逻辑。
                    for line_length in line_lengths:
                        # Codex说明(自动生成)： 计算并保存 stop，供后续语句继续读取或更新。
                        stop = start + line_length
                        # Codex说明(自动生成)： 调用 data_lines.append 更新列表或集合，把当前步骤产生的数据加入结果。
                        data_lines.append(" ".join(tokens[start:stop]))
                        # Codex说明(自动生成)： 计算并保存 start，供后续语句继续读取或更新。
                        start = stop
                    # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
                    text = "\n".join(
                        [
                            "[Version] 2.0",
                            "# Hz S RI R 50",
                            "[Number of Ports] 4",
                            "[Number of Frequencies] 1",
                            "[Network Data]",
                            *data_lines,
                            "[End]",
                            "",
                        ]
                    )
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / name
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text(text, encoding="ascii")

                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(
                        ValueError,
                        rf"{re.escape(str(path))}:{error_line}:.*started at line "
                        rf"{start_line}.*expected 33.*got 34",
                    ):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_explicit_touchstone_1_s4p_keeps_strict_writer_continuations，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_explicit_touchstone_1_s4p_keeps_strict_writer_continuations(self):
        # Codex说明(自动生成)： 计算并保存 first_line，供后续语句继续读取或更新。
        first_line = " ".join(["1", *("0" for _ in range(8))])
        # Codex说明(自动生成)： 计算并保存 second_line，供后续语句继续读取或更新。
        second_line = " ".join("0" for _ in range(24))
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = "\n".join(
            [
                "[Version] 1.0",
                "# Hz S RI R 50",
                first_line,
                second_line,
                "",
            ]
        )
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "strict_v1.s4p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="ascii")

            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(
                ValueError,
                rf"{re.escape(str(path))}:4:.*expected 1 to 4 complex pairs, got 24",
            ):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_s2p_order_12_21_is_read_correctly，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_s2p_order_12_21_is_read_correctly(self):
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = """[Version] 2.0
# GHZ S RI R 50
[Number of Ports] 2
[Number of Frequencies] 1
[Two-Port Data Order] 12_21
[Network Data]
1 0.11 0 0.12
0 0.21 0 0.22 0
[End]
"""
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "ordered.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="utf-8")
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 0, 0].real, 0.11)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 0, 1].real, 0.12)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 1, 0].real, 0.21)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 1, 1].real, 0.22)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_s2p_order_21_12_is_read_correctly，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_s2p_order_21_12_is_read_correctly(self):
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = """[Version] 2.0
# GHZ S RI R 50
[Number of Ports] 2
[Two-Port Data Order] 21_12
[Network Data]
1 0.11 0 0.21 0 0.12 0 0.22 0
[End]
"""
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "ordered.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="utf-8")
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 0, 0].real, 0.11)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 0, 1].real, 0.12)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 1, 0].real, 0.21)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 1, 1].real, 0.22)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_reference_keyword_is_rejected，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_reference_keyword_is_rejected(self):
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = """[Version] 2.0
# GHZ S RI R 50
[Number of Ports] 2
[Reference] 50 75
[Network Data]
1 0.11 0 0.21 0 0.12 0 0.22 0
[End]
"""
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "reference.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(text, encoding="utf-8")
            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'Reference')，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(ValueError, "Reference"):
                # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_import_rejects_invalid_scalar_reference_impedance，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_import_rejects_invalid_scalar_reference_impedance(self):
        # Codex说明(自动生成)： 计算并保存 template，供后续语句继续读取或更新。
        template = """# GHZ S RI R {z0}
1 0.11 0 0.21 0 0.12 0 0.22 0
"""
        # Codex说明(自动生成)： 遍历 ['0', '-50', 'nan'] 中的 z0，逐项执行循环体逻辑。
        for z0 in ["0", "-50", "nan"]:
            # Codex说明(自动生成)： 进入上下文 self.subTest(z0=z0)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(z0=z0):
                # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
                with tempfile.TemporaryDirectory() as tmp:
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / "bad_z0.s2p"
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text(template.format(z0=z0), encoding="utf-8")
                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'impedance')，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(ValueError, "impedance"):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_rejects_db_conversion_overflow_without_warning，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_rejects_db_conversion_overflow_without_warning(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "overflow.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(
                "# Hz S DB R 50\n"
                "1 0 0 1e308 0 0 0 0 0\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 进入上下文 warnings.catch_warnings()，确保文件、资源或临时状态按作用域正确释放。
            with warnings.catch_warnings():
                # Codex说明(自动生成)： 调用 warnings.simplefilter，执行当前流程需要的具体操作或副作用。
                warnings.simplefilter("error", RuntimeWarning)
                # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
                with self.assertRaisesRegex(
                    ValueError,
                    rf"{re.escape(str(path))}:2:.*S-parameter.*DB.*non-finite",
                ):
                    # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                    read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_read_touchstone_rejects_nonfinite_ri_ma_and_db_values，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_read_touchstone_rejects_nonfinite_ri_ma_and_db_values(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 遍历 ('RI', 'MA', 'DB') 中的 data_format，逐项执行循环体逻辑。
            for data_format in ("RI", "MA", "DB"):
                # Codex说明(自动生成)： 进入上下文 self.subTest(data_format=data_format)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(data_format=data_format):
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / f"nonfinite_{data_format.lower()}.s2p"
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text(
                        f"# Hz S {data_format} R 50\n"
                        "1 nan 0 0 0 0 0 0 0\n",
                        encoding="ascii",
                    )

                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, f'{re.escape(str(pat...，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(
                        ValueError,
                        rf"{re.escape(str(path))}:2:.*Non-finite numeric value",
                    ):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_write_rejects_nonfinite_sparameters，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_write_rejects_nonfinite_sparameters(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9])
        # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
        s = np.zeros((1, 2, 2), dtype=complex)
        # Codex说明(自动生成)： 计算并保存 s[0, 1, 0]，供后续语句继续读取或更新。
        s[0, 1, 0] = np.nan

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "bad.s2p"
            # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'non-finite')，确保文件、资源或临时状态按作用域正确释放。
            with self.assertRaisesRegex(ValueError, "non-finite"):
                # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
                write_touchstone(TouchstoneData(frequency, s), path)

    # Codex说明(自动生成)： 定义函数 test_write_keeps_close_frequencies_distinct，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_write_keeps_close_frequencies_distinct(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 1e9 + 0.001])
        # Codex说明(自动生成)： 计算并保存 s，供后续语句继续读取或更新。
        s = np.zeros((2, 2, 2), dtype=complex)

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "close.s2p"
            # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
            write_touchstone(TouchstoneData(frequency, s), path)
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 self.assertGreater 检查测试期望，确认实际结果符合预期。
        self.assertGreater(loaded.frequency_hz[1], loaded.frequency_hz[0])

    # Codex说明(自动生成)： 定义函数 test_linear_model_hits_endpoint_losses，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_linear_model_hits_endpoint_losses(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 11)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.5, 8.5)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)
        # Codex说明(自动生成)： 计算并保存 s21_loss，供后续语句继续读取或更新。
        s21_loss = -to_magnitude_db(data.s[:, 1, 0])
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(s21_loss[0], 1.5, places=9)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(s21_loss[-1], 8.5, places=9)
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(data.s[:, 1, 0], data.s[:, 0, 1])
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(data.s[:, 0, 0], data.s[:, 1, 1])

    # Codex说明(自动生成)： 定义函数 test_drawn_loss_can_use_linear_line_segments，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_drawn_loss_can_use_linear_line_segments(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 1.5e9, 2e9, 2.5e9, 3e9])
        # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
        control_points = parse_draw_points(["1GHz:-1.0", "2GHz:-3.0", "3GHz:-2.0"])

        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = interpolate_drawn_loss(frequency, control_points, method="linear")

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loss, [1.0, 2.0, 3.0, 2.5, 2.0])

    # Codex说明(自动生成)： 定义函数 test_drawn_loss_smooth_fit_uses_curved_transition，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_drawn_loss_smooth_fit_uses_curved_transition(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 1.5e9, 2e9, 2.5e9, 3e9])
        # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
        control_points = parse_draw_points(["1GHz:0.0", "3GHz:-10.0"])

        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = interpolate_drawn_loss(frequency, control_points)

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loss, [0.0, 1.5625, 5.0, 8.4375, 10.0])

    # Codex说明(自动生成)： 定义函数 test_draw_control_frequencies_are_inserted_into_output_axis，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_draw_control_frequencies_are_inserted_into_output_axis(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 2e9, 3e9])
        # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
        control_points = parse_draw_points(["1GHz:-1.0", "1.5GHz:-4.0", "3GHz:-2.0"])

        # Codex说明(自动生成)： 计算并保存 output_frequency，供后续语句继续读取或更新。
        output_frequency = insert_draw_control_frequencies(frequency, control_points)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = interpolate_drawn_loss(output_frequency, control_points)

        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(1.5e9, output_frequency.tolist())
        # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
        target_index = int(np.where(np.isclose(output_frequency, 1.5e9))[0][0])
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(loss[target_index]), 4.0, places=9)

    # Codex说明(自动生成)： 定义函数 test_draw_rejects_near_vertical_control_segments，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_draw_rejects_near_vertical_control_segments(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1e9, 2e9, 3e9])
        # Codex说明(自动生成)： 计算并保存 too_close，供后续语句继续读取或更新。
        too_close = parse_draw_points(["1GHz:-1.0", "1.00001GHz:-8.0", "3GHz:-2.0"])
        # Codex说明(自动生成)： 计算并保存 too_steep，供后续语句继续读取或更新。
        too_steep = parse_draw_points(["1GHz:-1.0", "1.01GHz:-20.0", "3GHz:-2.0"])

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too close')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too close"):
            # Codex说明(自动生成)： 调用 interpolate_drawn_loss，执行当前流程需要的具体操作或副作用。
            interpolate_drawn_loss(frequency, too_close)
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too steep')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too steep"):
            # Codex说明(自动生成)： 调用 interpolate_drawn_loss，执行当前流程需要的具体操作或副作用。
            interpolate_drawn_loss(frequency, too_steep)

    # Codex说明(自动生成)： 定义函数 test_draw_cli_with_scripted_points_writes_s2p，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_draw_cli_with_scripted_points_writes_s2p(self):
        # Codex说明(自动生成)： 计算并保存 project_root，供后续语句继续读取或更新。
        project_root = Path(__file__).resolve().parents[1]
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = Path(tmp) / "drawn.s2p"
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "main.py"),
                    "draw",
                    "--ports",
                    "2",
                    "--f-start",
                    "1GHz",
                    "--f-stop",
                    "3GHz",
                    "--points",
                    "3",
                    "--draw-point",
                    "1GHz:-1.0",
                    "--draw-point",
                    "1.5GHz:-4.0",
                    "--draw-point",
                    "3GHz:-2.0",
                    "--output",
                    str(output),
                    "--no-show-plot",
                    "--no-save-plot-files",
                ],
                cwd=tempfile.gettempdir(),
                text=True,
                capture_output=True,
                check=False,
            )

            # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(output)

        # Codex说明(自动生成)： 计算并保存 actual_mag_db，供后续语句继续读取或更新。
        actual_mag_db = to_magnitude_db(loaded.s[:, 1, 0])
        # Codex说明(自动生成)： 计算并保存 actual_loss，供后续语句继续读取或更新。
        actual_loss = -actual_mag_db
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(1.5e9, loaded.frequency_hz.tolist())
        # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
        target_index = int(np.where(np.isclose(loaded.frequency_hz, 1.5e9))[0][0])
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(actual_loss[target_index]), 4.0, places=9)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(actual_mag_db[target_index]), -4.0, places=9)

    # Codex说明(自动生成)： 定义函数 test_s2p_generation_forces_reciprocal_through_pair，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s2p_generation_forces_reciprocal_through_pair(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 11)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.5, 8.5)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss, through_pairs=[(1, 0)])

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(data.s[:, 1, 0], data.s[:, 0, 1])

    # Codex说明(自动生成)： 定义函数 test_generation_rejects_diagonal_through_pair，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_generation_rejects_diagonal_through_pair(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 11)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.5, 8.5)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'off-diagonal')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "off-diagonal"):
            # Codex说明(自动生成)： 调用 build_network，执行当前流程需要的具体操作或副作用。
            build_network(frequency, 2, loss, through_pairs=[(0, 0)])

    # Codex说明(自动生成)： 定义函数 test_generation_rejects_power_incompatible_return_and_insertion_loss，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_generation_rejects_power_incompatible_return_and_insertion_loss(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 11)
        # Codex说明(自动生成)： 计算并保存 zero_insertion_loss，供后续语句继续读取或更新。
        zero_insertion_loss = np.zeros_like(frequency)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'passive')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "passive"):
            # Codex说明(自动生成)： 调用 build_network，执行当前流程需要的具体操作或副作用。
            build_network(
                frequency,
                2,
                zero_insertion_loss,
                return_loss_db=3.0,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_insertion_loss_preserves_phase_and_hits_target，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_insertion_loss_preserves_phase_and_hits_target(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss, delay_ps=25.0)
        # Codex说明(自动生成)： 计算并保存 original_phase，供后续语句继续读取或更新。
        original_phase = np.unwrap(np.angle(data.s[:, 1, 0]))

        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
        result = modify_insertion_loss(
            data,
            [TargetPoint(parse_frequency("5.5GHz"), 3.0)],
            [(1, 0), (0, 1)],
            smoothness=0.16,
            insert_targets=True,
        )

        # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
        target_index = int(np.where(np.isclose(result.data.frequency_hz, 5.5e9))[0][0])
        # Codex说明(自动生成)： 计算并保存 achieved，供后续语句继续读取或更新。
        achieved = -to_magnitude_db(result.data.s[target_index, 1, 0])
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(achieved), 3.0, places=6)

        # Codex说明(自动生成)： 计算并保存 expected_phase，供后续语句继续读取或更新。
        expected_phase = np.interp(5.5e9, frequency, original_phase)
        # Codex说明(自动生成)： 计算并保存 actual_phase，供后续语句继续读取或更新。
        actual_phase = np.unwrap(np.angle(result.data.s[:, 1, 0]))[target_index]
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(actual_phase), float(expected_phase), places=9)

    # Codex说明(自动生成)： 定义函数 test_modify_insertion_loss_identifies_an_infeasible_target，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_insertion_loss_identifies_an_infeasible_target(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1.0e9, 2.0e9])
        # Every original matrix is [[0.5, 0.5], [0.5, 0.5]], whose largest
        # singular value is exactly one. Raising only the two through paths to
        # one produces [[0.5, 1], [1, 0.5]], whose largest singular value is 1.5.
        s = np.full((2, 2, 2), 0.5 + 0.0j, dtype=complex)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = TouchstoneData(frequency_hz=frequency, s=s, z0=50.0)

        # 目标采样点本身不可行时必须指出 requested target，而不是归咎于平滑曲线。
        with self.assertRaisesRegex(ValueError, "Requested target.*passivity"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(1.0e9, 0.0), TargetPoint(2.0e9, 0.0)],
                [(0, 1), (1, 0)],
                smoothness=0.2,
                anchor_edges=False,
                insert_targets=False,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_insertion_loss_identifies_a_nonpassive_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_insertion_loss_identifies_a_nonpassive_input(self):
        # 固定矩阵的最大奇异值为 1.2，用于区分输入缺陷和目标不可行两种错误。
        frequency = np.array([1.0e9, 2.0e9])
        # 四个元素均为 0.6 的二端口矩阵在同相激励下会放大功率，因此不是无源输入。
        s = np.full((2, 2, 2), 0.6 + 0.0j, dtype=complex)
        # 构造真实公开数据对象，避免绕过 Modify 的输入边界检查。
        data = TouchstoneData(frequency_hz=frequency, s=s, z0=50.0)

        # 即使请求增加插损，程序也不能静默修复原文件中的非无源矩阵。
        with self.assertRaisesRegex(ValueError, "Input.*not passive"):
            # 目标本身较保守，确保失败原因只能来自输入文件而不是目标功率预算。
            modify_insertion_loss(
                data,
                [TargetPoint(1.0e9, 10.0)],
                [(0, 1), (1, 0)],
                insert_targets=False,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_contracts_only_non_target_passivity_overshoot，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_contracts_only_non_target_passivity_overshoot(self):
        # 中间低损耗点会把未约束的负修正推入增益区，用于复现“可行目标却整次失败”。
        frequency = np.array([1.0e9, 2.0e9, 3.0e9, 4.0e9, 5.0e9])
        # 两个目标位置原始插损为 5 dB，而中间仅 0.2 dB，构成确定性的过冲压力样本。
        loss = np.array([5.0, 5.0, 0.2, 5.0, 5.0])
        # 20 dB 回损对应的解析无源插损下限约为 0.04365 dB。
        data = build_network(frequency, 2, loss, delay_ps=10.0)

        # 两个 1 dB 目标各自都可行，程序应收缩中间过冲而不是拒绝整个操作。
        result = modify_insertion_loss(
            data,
            [TargetPoint(2.0e9, 1.0), TargetPoint(4.0e9, 1.0)],
            [(1, 0), (0, 1)],
            smoothness=0.14,
            anchor_edges=True,
            insert_targets=True,
        )

        # 独立 NumPy SVD 验证所有采样矩阵均未越过无源边界。
        sigma_max = np.linalg.svd(result.data.s, compute_uv=False).max(axis=1)
        # 目标点必须精确命中，不能为了通过无源检查而偷偷改写用户目标。
        achieved_loss = -to_magnitude_db(result.data.s[:, 1, 0])
        # 未选择的反射参数必须逐元素保持原值。
        np.testing.assert_allclose(result.data.s[:, 0, 0], data.s[:, 0, 0])
        # 同时检查两个目标和中间无源边界，防止只验证“不报错”的假绿测试。
        self.assertAlmostEqual(float(achieved_loss[1]), 1.0, places=9)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(achieved_loss[3]), 1.0, places=9)
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(float(np.max(sigma_max)), 1.0 + 1.0e-12)

    # Codex说明(自动生成)： 定义函数 test_modify_without_inserted_targets_reports_the_constrained_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_without_inserted_targets_reports_the_constrained_output(self):
        """Off-grid reports must describe the final passive matrix, not the candidate."""

        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1.0e9, 2.0e9, 3.0e9, 4.0e9, 5.0e9])
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = np.array([5.0, 5.0, 0.2, 5.0, 5.0])
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss, delay_ps=10.0)
        # Codex说明(自动生成)： 计算并保存 targets，供后续语句继续读取或更新。
        targets = [TargetPoint(2.5e9, 1.0), TargetPoint(3.5e9, 1.0)]

        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
        result = modify_insertion_loss(
            data,
            targets,
            [(1, 0), (0, 1)],
            smoothness=0.14,
            anchor_edges=True,
            insert_targets=False,
        )

        # Codex说明(自动生成)： 计算并保存 final_loss，供后续语句继续读取或更新。
        final_loss = -to_magnitude_db(result.data.s[:, 1, 0])
        # Codex说明(自动生成)： 计算并保存 expected，供后续语句继续读取或更新。
        expected = [
            float(np.interp(target.frequency_hz, frequency, final_loss))
            for target in targets
        ]
        # Codex说明(自动生成)： 计算并保存 forward_reports，供后续语句继续读取或更新。
        forward_reports = [item for item in result.results if item.pair == "S21"]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(len(forward_reports), 2)
        # Codex说明(自动生成)： 遍历 zip(forward_reports, expected) 中的 (item, expected_loss)，逐项执行循环体逻辑。
        for item, expected_loss in zip(forward_reports, expected):
            # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
            self.assertAlmostEqual(item.achieved_loss_db, expected_loss, places=12)
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(any(abs(item.achieved_loss_db - 1.0) > 0.5 for item in forward_reports))
        # Codex说明(自动生成)： 计算并保存 sigma_max，供后续语句继续读取或更新。
        sigma_max = np.linalg.svd(result.data.s, compute_uv=False)[:, 0]
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(float(np.max(sigma_max)), 1.0 + 1.0e-12)

    # Codex说明(自动生成)： 定义函数 test_resampling_preserves_every_original_complex_sample_bit_for_bit，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_resampling_preserves_every_original_complex_sample_bit_for_bit(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = np.array([1.0e9, 3.0e9])
        # Codex说明(自动生成)： 计算并保存 source_s，供后续语句继续读取或更新。
        source_s = np.array(
            [
                [[0.0 + 0.0j, 0.25 + 0.125j], [0.5 - 0.25j, 0.0 + 0.0j]],
                [[0.125 - 0.25j, 0.0 + 0.0j], [0.25 + 0.5j, -0.125j]],
            ],
            dtype=complex,
        )
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = TouchstoneData(frequency, source_s)

        # Codex说明(自动生成)： 计算并保存 resampled，供后续语句继续读取或更新。
        resampled = resample_with_frequencies(data, [2.0e9])

        # Codex说明(自动生成)： 计算并保存 source_indices，供后续语句继续读取或更新。
        source_indices = np.searchsorted(resampled.frequency_hz, frequency)
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(resampled.s[source_indices], source_s)

    # Codex说明(自动生成)： 定义函数 test_modify_target_at_sweep_edge_is_not_overridden_by_edge_anchor，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_target_at_sweep_edge_is_not_overridden_by_edge_anchor(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
        result = modify_insertion_loss(
            data,
            [TargetPoint(1e9, 4.0)],
            [(1, 0)],
            smoothness=0.16,
            insert_targets=True,
        )

        # Codex说明(自动生成)： 计算并保存 achieved，供后续语句继续读取或更新。
        achieved = -to_magnitude_db(result.data.s[0, 1, 0])
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(float(achieved), 4.0, places=6)

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_out_of_range_target_without_inserting，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_out_of_range_target_without_inserting(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'inside')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "inside"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(20e9, 4.0)],
                [(1, 0)],
                insert_targets=False,
            )

    # Codex说明(自动生成)： 定义函数 test_duplicate_conflicting_targets_are_rejected，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_duplicate_conflicting_targets_are_rejected(self):
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'Conflicting')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            # Codex说明(自动生成)： 调用 parse_target_points，执行当前流程需要的具体操作或副作用。
            parse_target_points(["5GHz:3.0", "5GHz:8.0"])

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_too_close_conflicting_targets，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_too_close_conflicting_targets(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too close')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too close"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(5e9, 3.0), TargetPoint(5.00001e9, 8.0)],
                [(1, 0)],
                insert_targets=True,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_target_too_close_to_edge_anchor，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_target_too_close_to_edge_anchor(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too close')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too close"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(1.00001e9, 8.0)],
                [(1, 0)],
                insert_targets=True,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_sub_hz_target_too_close_to_edge_anchor，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_sub_hz_target_too_close_to_edge_anchor(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too close')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too close"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(1e9 + 0.001, 8.0)],
                [(1, 0)],
                insert_targets=True,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_near_edge_target_when_edge_anchors_disabled，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_near_edge_target_when_edge_anchors_disabled(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'too close')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "too close"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(1e9 + 0.001, 8.0)],
                [(1, 0)],
                anchor_edges=False,
                insert_targets=True,
            )

    # Codex说明(自动生成)： 定义函数 test_modify_rejects_just_outside_target_when_edge_anchors_disabled，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_modify_rejects_just_outside_target_when_edge_anchors_disabled(self):
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(1e9, 10e9, 10)
        # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
        loss = linear_loss(frequency, 1.0, 10.0)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(frequency, 2, loss)

        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'inside')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "inside"):
            # Codex说明(自动生成)： 调用 modify_insertion_loss，执行当前流程需要的具体操作或副作用。
            modify_insertion_loss(
                data,
                [TargetPoint(1e9 - 0.001, 8.0)],
                [(1, 0)],
                anchor_edges=False,
                insert_targets=True,
            )

    # Codex说明(自动生成)： 定义函数 test_negative_or_nonfinite_loss_values_are_rejected，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_negative_or_nonfinite_loss_values_are_rejected(self):
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'non-negative')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "non-negative"):
            # Codex说明(自动生成)： 调用 parse_target_points，执行当前流程需要的具体操作或副作用。
            parse_target_points(["5GHz:-1.0"])
        # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, 'finite')，确保文件、资源或临时状态按作用域正确释放。
        with self.assertRaisesRegex(ValueError, "finite"):
            # Codex说明(自动生成)： 调用 parse_target_points，执行当前流程需要的具体操作或副作用。
            parse_target_points(["5GHz:nan"])

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_1_accepts_category_ordered_option_fields，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_1_accepts_category_ordered_option_fields(self):
        """Touchstone 2.1 keeps option fields optional and order-independent."""

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "official_style_v21.s2p"
            # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
            path.write_text(
                "[Version] 2.1\n"
                "# S R 75 GHz RI\n"
                "[Number of Ports] 2\n"
                "[Number of Frequencies] 1\n"
                "[Two-Port Data Order] 21_12\n"
                "[Matrix Format] Full\n"
                "[Network Data]\n"
                "1 0.1 0 0.8 0 0.7 0 0.2 0\n"
                "[End]\n",
                encoding="ascii",
            )

            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(loaded.z0, 75.0)
        # Codex说明(自动生成)： 调用 np.testing.assert_array_equal 检查测试期望，确认实际结果符合预期。
        np.testing.assert_array_equal(loaded.frequency_hz, np.array([1e9]))
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 1, 0], 0.8 + 0.0j)
        # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
        self.assertAlmostEqual(loaded.s[0, 0, 1], 0.7 + 0.0j)

    # Codex说明(自动生成)： 定义函数 test_touchstone_2_1_rejects_missing_required_structure，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_touchstone_2_1_rejects_missing_required_structure(self):
        # Codex说明(自动生成)： 计算并保存 base_lines，供后续语句继续读取或更新。
        base_lines = [
            "[Version] 2.1",
            "# S R 75 GHz RI",
            "[Number of Ports] 2",
            "[Number of Frequencies] 1",
            "[Two-Port Data Order] 21_12",
            "[Matrix Format] Full",
            "[Network Data]",
            "1 0.1 0 0.21 0 0.12 0 0.2 0",
            "[End]",
        ]
        # Codex说明(自动生成)： 计算并保存 cases，供后续语句继续读取或更新。
        cases = {
            "missing-order.s2p": (
                [line for line in base_lines if "Two-Port Data Order" not in line],
                "Two-Port Data Order",
            ),
            "missing-network-data.s2p": (
                [line for line in base_lines if line != "[Network Data]"],
                "Network Data",
            ),
            "missing-end.s2p": (
                [line for line in base_lines if line != "[End]"],
                "End",
            ),
            "version-not-first.s2p": (
                [base_lines[2], base_lines[0], *base_lines[1:2], *base_lines[3:]],
                "Version.*first",
            ),
        }
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 遍历 cases.items() 中的 (name, (lines, pattern))，逐项执行循环体逻辑。
            for name, (lines, pattern) in cases.items():
                # Codex说明(自动生成)： 进入上下文 self.subTest(name=name)，确保文件、资源或临时状态按作用域正确释放。
                with self.subTest(name=name):
                    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
                    path = Path(tmp) / name
                    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
                    path.write_text("\n".join(lines) + "\n", encoding="ascii")
                    # Codex说明(自动生成)： 进入上下文 self.assertRaisesRegex(ValueError, pattern)，确保文件、资源或临时状态按作用域正确释放。
                    with self.assertRaisesRegex(ValueError, pattern):
                        # Codex说明(自动生成)： 调用 read_touchstone，执行当前流程需要的具体操作或副作用。
                        read_touchstone(path)

    # Codex说明(自动生成)： 定义函数 test_s5p_writer_limits_each_physical_line_to_four_complex_pairs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s5p_writer_limits_each_physical_line_to_four_complex_pairs(self):
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = np.array([1e9])
        # Codex说明(自动生成)： 计算并保存 matrix，供后续语句继续读取或更新。
        matrix = np.arange(25, dtype=float).reshape(1, 5, 5) / 100.0
        # Codex说明(自动生成)： 计算并保存 original，供后续语句继续读取或更新。
        original = TouchstoneData(frequency_hz=frequency_hz, s=matrix.astype(complex))

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "limited_lines.s5p"
            # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
            write_touchstone(original, path, frequency_unit="hz", data_format="ri")
            # Codex说明(自动生成)： 计算并保存 data_lines，供后续语句继续读取或更新。
            data_lines = [
                line.split()
                for line in path.read_text(encoding="ascii").splitlines()
                if line.strip() and not line.lstrip().startswith(("!", "#"))
            ]
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            [len(line) for line in data_lines],
            [9, 2, 8, 2, 8, 2, 8, 2, 8, 2],
        )
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.s, original.s)

    # Codex说明(自动生成)： 定义函数 test_s3p_round_trip_preserves_full_matrix，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_s3p_round_trip_preserves_full_matrix(self):
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = np.array([1e9, 2e9])
        # Codex说明(自动生成)： 计算并保存 matrix，供后续语句继续读取或更新。
        matrix = np.zeros((2, 3, 3), dtype=complex)
        # Codex说明(自动生成)： 遍历 range(2) 中的 point，逐项执行循环体逻辑。
        for point in range(2):
            # Codex说明(自动生成)： 遍历 range(3) 中的 out_port，逐项执行循环体逻辑。
            for out_port in range(3):
                # Codex说明(自动生成)： 遍历 range(3) 中的 in_port，逐项执行循环体逻辑。
                for in_port in range(3):
                    # Codex说明(自动生成)： 计算并保存 matrix[point, out_port, in_port]，供后续语句继续读取或更新。
                    matrix[point, out_port, in_port] = complex(
                        point + 0.1 * (out_port + 1),
                        -0.01 * (in_port + 1),
                    )
        # Codex说明(自动生成)： 计算并保存 original，供后续语句继续读取或更新。
        original = TouchstoneData(frequency_hz=frequency_hz, s=matrix, z0=50.0)

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path(tmp) / "full_matrix.s3p"
            # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
            write_touchstone(original, path, frequency_unit="hz", data_format="ri")
            # Codex说明(自动生成)： 计算并保存 loaded，供后续语句继续读取或更新。
            loaded = read_touchstone(path)

        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.frequency_hz, original.frequency_hz)
        # Codex说明(自动生成)： 调用 np.testing.assert_allclose 检查测试期望，确认实际结果符合预期。
        np.testing.assert_allclose(loaded.s, original.s)


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 调用 unittest.main，执行当前流程需要的具体操作或副作用。
    unittest.main()
