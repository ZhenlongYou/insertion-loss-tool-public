# Codex说明(自动生成)： 导入 importlib.util，提供本文件后续流程需要的库能力。
import importlib.util
# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 unittest 导入 mock，组织单元测试和断言。
from unittest import mock

# Codex说明(自动生成)： 从 insertion_loss_tool.gui 导入 default_example_path, run_self_test，提供本文件后续流程需要的库能力。
from insertion_loss_tool.gui import default_example_path, run_self_test
# Codex说明(自动生成)： 从 insertion_loss_tool.touchstone 导入 read_touchstone, to_magnitude_db，提供本文件后续流程需要的库能力。
from insertion_loss_tool.touchstone import read_touchstone, to_magnitude_db


# Codex说明(自动生成)： 定义 GuiEntrypointTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class GuiEntrypointTests(unittest.TestCase):
    """Smoke tests for the desktop-app backend paths.

    These tests avoid creating a Tk window so they can run in headless
    automation, but they still prove the packaged GUI entry point can execute
    all four backend workflows and write valid Touchstone files.
    """

    # Codex说明(自动生成)： 定义函数 test_gui_self_test_writes_valid_outputs，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_gui_self_test_writes_valid_outputs(self):
        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as tmp:
            # Codex说明(自动生成)： 计算并保存 paths，供后续语句继续读取或更新。
            paths = run_self_test(tmp)
            # Codex说明(自动生成)： 计算并保存 names，供后续语句继续读取或更新。
            names = {Path(path).name for path in paths}

            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("selftest_linear.s2p", names)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("selftest_formula.s4p", names)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("selftest_draw.s2p", names)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("selftest_modified.s2p", names)
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn("selftest_modified.s2p.report.txt", names)

            # Codex说明(自动生成)： 计算并保存 draw，供后续语句继续读取或更新。
            draw = read_touchstone(Path(tmp) / "selftest_draw.s2p")
            # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
            target_index = list(draw.frequency_hz).index(2.5e9)
            # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
            self.assertAlmostEqual(
                float(to_magnitude_db(draw.s[target_index, 1, 0])),
                -4.0,
                places=6,
            )

            # Codex说明(自动生成)： 计算并保存 modified，供后续语句继续读取或更新。
            modified = read_touchstone(Path(tmp) / "selftest_modified.s2p")
            # Codex说明(自动生成)： 计算并保存 modified_index，供后续语句继续读取或更新。
            modified_index = list(modified.frequency_hz).index(3e9)
            # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
            self.assertAlmostEqual(
                float(to_magnitude_db(modified.s[modified_index, 1, 0])),
                -2.0,
                places=6,
            )
            # Codex说明(自动生成)： 调用 self.assertAlmostEqual 检查测试期望，确认实际结果符合预期。
            self.assertAlmostEqual(
                float(to_magnitude_db(modified.s[modified_index, 0, 1])),
                -2.0,
                places=6,
            )

    # Codex说明(自动生成)： 定义函数 test_default_modify_example_is_available，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_default_modify_example_is_available(self):
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(default_example_path().exists(), default_example_path())

    # Codex说明(自动生成)： 定义函数 test_macos_build_keeps_pyinstaller_cache_inside_project，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_macos_build_keeps_pyinstaller_cache_inside_project(self):
        # Codex说明(自动生成)： 计算并保存 build_script，供后续语句继续读取或更新。
        build_script = (Path(__file__).parents[1] / "build_macos_app.command").read_text(
            encoding="utf-8"
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn('PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$PWD/.pyinstaller-cache}"', build_script)

    # Codex说明(自动生成)： 定义函数 test_finder_launch_path_exposes_user_tesseract_directory，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_finder_launch_path_exposes_user_tesseract_directory(self):
        # Codex说明(自动生成)： 计算并保存 entrypoint，供后续语句继续读取或更新。
        entrypoint = Path(__file__).parents[1] / "gui_main.py"
        # Codex说明(自动生成)： 计算并保存 spec，供后续语句继续读取或更新。
        spec = importlib.util.spec_from_file_location("packaged_gui_main", entrypoint)
        # Codex说明(自动生成)： 调用 self.assertIsNotNone 检查测试期望，确认实际结果符合预期。
        self.assertIsNotNone(spec)
        # Codex说明(自动生成)： 调用 self.assertIsNotNone 检查测试期望，确认实际结果符合预期。
        self.assertIsNotNone(spec.loader)
        # Codex说明(自动生成)： 计算并保存 module，供后续语句继续读取或更新。
        module = importlib.util.module_from_spec(spec)
        # Codex说明(自动生成)： 调用 spec.loader.exec_module，执行当前流程需要的具体操作或副作用。
        spec.loader.exec_module(module)

        # Codex说明(自动生成)： 进入上下文 tempfile.TemporaryDirectory()，确保文件、资源或临时状态按作用域正确释放。
        with tempfile.TemporaryDirectory() as temp_dir:
            # Codex说明(自动生成)： 计算并保存 home，供后续语句继续读取或更新。
            home = Path(temp_dir)
            # Codex说明(自动生成)： 计算并保存 local_bin，供后续语句继续读取或更新。
            local_bin = home / ".local" / "bin"
            # Codex说明(自动生成)： 调用 local_bin.mkdir，执行当前流程需要的具体操作或副作用。
            local_bin.mkdir(parents=True)
            # Codex说明(自动生成)： 进入上下文 mock.patch.dict(os.environ, {'PATH': '/usr/bin'}, clear...，确保文件、资源或临时状态按作用域正确释放。
            with mock.patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False):
                # Codex说明(自动生成)： 调用 module._configure_external_tool_path 生成或展示图形，便于观察计算结果。
                module._configure_external_tool_path(home)
                # Codex说明(自动生成)： 计算并保存 paths，供后续语句继续读取或更新。
                paths = os.environ["PATH"].split(os.pathsep)

        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(paths[0], str(local_bin))
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("/usr/bin", paths)

    # Codex说明(自动生成)： 定义函数 test_windows_packaging_contract_is_fail_closed，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_windows_packaging_contract_is_fail_closed(self):
        # Codex说明(自动生成)： 计算并保存 project，供后续语句继续读取或更新。
        project = Path(__file__).parents[1]
        # Codex说明(自动生成)： 计算并保存 agent_contract，供后续语句继续读取或更新。
        agent_contract = (project / "AGENTS.md").read_text(encoding="utf-8")
        # Codex说明(自动生成)： 计算并保存 build_script，供后续语句继续读取或更新。
        build_script = (project / "build_windows_exe.bat").read_text(
            encoding="utf-8"
        )

        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("build_windows_exe.bat", agent_contract)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("ZIP 内只包含 `InsertionLossTool.exe`", agent_contract)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Windows 实机验收", agent_contract)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("不得声称 Windows EXE 已通过", agent_contract)

        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("set PYTHONUTF8=1", build_script)
        # Codex说明(自动生成)： 计算并保存 python_bootstrap_contract，供后续语句继续读取或更新。
        python_bootstrap_contract = """if not exist "%PYTHON_EXE%" (
  REM Prefer python.exe from PATH so CI/setup-python and user-selected shells keep their exact version.
  where python.exe >nul 2>&1
  if not errorlevel 1 (
    python.exe -c "import struct,sys; sys.exit(0 if sys.version_info >= (3,9) and struct.calcsize('P') * 8 == 64 else 1)"
    if not errorlevel 1 (
      python.exe -m venv .venv
      if errorlevel 1 goto :fail
      goto :venv_ready
    )
  )
  where py.exe >nul 2>&1
  if errorlevel 1 goto :missing_python
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
:venv_ready
"%PYTHON_EXE%" -c "import struct,sys; sys.exit(0 if sys.version_info >= (3,9) and struct.calcsize('P') * 8 == 64 else 1)"
if errorlevel 1 goto :unsupported_python"""
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(python_bootstrap_contract, build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("-m unittest discover -s tests", build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("gui_main.py --self-test", build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("gui_main.py --renderer-smoke-test", build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("--onefile", build_script)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("--onedir", build_script)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("_internal", build_script)
        # Avoid cmd.exe `for /f` command-substitution quoting around a Python
        # path that can contain spaces; the release version uses a temp file.
        self.assertNotIn("for /f", build_script.lower())
        # Codex说明(自动生成)： 计算并保存 version_read_contract，供后续语句继续读取或更新。
        version_read_contract = r"""set "VERSION="
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -c "import insertion_loss_tool; print(insertion_loss_tool.__version__)" > "%VERSION_FILE%"
if errorlevel 1 goto :fail
set /p VERSION=<"%VERSION_FILE%"
if not defined VERSION goto :fail
del /q "%VERSION_FILE%"
if errorlevel 1 goto :fail
set "ARCHIVE=%CD%\dist\InsertionLossTool-%VERSION%-windows-x64.zip"""
        # Bind the complete order so removing or reversing an empty-version
        # guard cannot leave a false-green packaging test.
        self.assertIn(version_read_contract, build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'start "" /wait "%APP_EXE%" --self-test',
            build_script,
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn(
            'start "" /wait "%APP_EXE%" --renderer-smoke-test',
            build_script,
        )
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("if errorlevel 1 goto :fail", build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Compress-Archive", build_script)
        # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
        self.assertIn("Get-FileHash", build_script)
        # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
        self.assertNotIn("^|", build_script)

        # Codex说明(自动生成)： 计算并保存 fail_closed_commands，供后续语句继续读取或更新。
        fail_closed_commands = (
            '"%PYTHON_EXE%" -m pip install --upgrade pip',
            '"%PYTHON_EXE%" -m pip install -r requirements.txt -r requirements-build.txt',
            '"%PYTHON_EXE%" -m unittest discover -s tests',
            '"%PYTHON_EXE%" stress_test.py --iterations 80',
            '"%PYTHON_EXE%" gui_main.py --self-test --self-test-output "%SOURCE_SELFTEST%"',
            '"%PYTHON_EXE%" gui_main.py --renderer-smoke-test',
            'start "" /wait "%APP_EXE%" --self-test --self-test-output "%PACKAGED_SELFTEST%"',
            'start "" /wait "%APP_EXE%" --renderer-smoke-test',
            '"%PYTHON_EXE%" -c "import insertion_loss_tool; print(insertion_loss_tool.__version__)" > "%VERSION_FILE%"',
            "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"$ErrorActionPreference='Stop'; $line=(Get-FileHash -Algorithm SHA256 $env:ARCHIVE).Hash + '  ' + [IO.Path]::GetFileName($env:ARCHIVE); [IO.File]::WriteAllText($env:ARCHIVE + '.sha256.txt', $line + [Environment]::NewLine, [Text.Encoding]::ASCII)\"",
        )
        # Codex说明(自动生成)： 遍历 fail_closed_commands 中的 command，逐项执行循环体逻辑。
        for command in fail_closed_commands:
            # Codex说明(自动生成)： 进入上下文 self.subTest(command=command)，确保文件、资源或临时状态按作用域正确释放。
            with self.subTest(command=command):
                # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
                self.assertIn(
                    command + "\nif errorlevel 1 goto :fail",
                    build_script,
                )


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 调用 unittest.main，执行当前流程需要的具体操作或副作用。
    unittest.main()
