@echo off
REM Fail-closed Windows x64 build and packaged-app acceptance entry point.
REM See AGENTS.md before changing this script or distributing its output.
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 goto :fail

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1
set "PYINSTALLER_CONFIG_DIR=%CD%\.pyinstaller-cache"
set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
set "SOURCE_SELFTEST=%TEMP%\InsertionLossTool-source-selftest"
set "PACKAGED_SELFTEST=%TEMP%\InsertionLossTool-packaged-selftest"
set "VERSION_FILE=%TEMP%\InsertionLossTool-version.txt"
set "APP_EXE=%CD%\dist\InsertionLossTool.exe"

echo [1/10] Preparing a Windows x64 Python environment...
if not exist "%PYTHON_EXE%" (
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
if errorlevel 1 goto :unsupported_python

echo [2/10] Installing pinned runtime and build dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :fail

echo [3/10] Running the complete source test suite...
set "PYTHONPATH=%CD%\src"
"%PYTHON_EXE%" -m unittest discover -s tests
if errorlevel 1 goto :fail
"%PYTHON_EXE%" stress_test.py --iterations 80
if errorlevel 1 goto :fail

echo [4/10] Running source backend self-test...
if exist "%SOURCE_SELFTEST%" rmdir /s /q "%SOURCE_SELFTEST%"
if errorlevel 1 goto :fail
"%PYTHON_EXE%" gui_main.py --self-test --self-test-output "%SOURCE_SELFTEST%"
if errorlevel 1 goto :fail

echo [5/10] Running source Edge WebView2 renderer probe...
"%PYTHON_EXE%" gui_main.py --renderer-smoke-test
if errorlevel 1 goto :fail

echo [6/10] Building the single-file application...
if exist build rmdir /s /q build
if errorlevel 1 goto :fail
if exist dist rmdir /s /q dist
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name InsertionLossTool ^
  --paths "src" ^
  --add-data "examples;examples" ^
  --add-data "src/insertion_loss_tool/webui;insertion_loss_tool/webui" ^
  --hidden-import "insertion_loss_tool.webview_gui" ^
  --hidden-import "insertion_loss_tool.gui" ^
  --hidden-import "matplotlib.backends.backend_tkagg" ^
  --exclude-module "skrf" ^
  --exclude-module "scipy" ^
  --exclude-module "pandas" ^
  gui_main.py
if errorlevel 1 goto :fail
if not exist "%APP_EXE%" goto :missing_exe

echo [7/10] Running packaged backend self-test...
if exist "%PACKAGED_SELFTEST%" rmdir /s /q "%PACKAGED_SELFTEST%"
if errorlevel 1 goto :fail
start "" /wait "%APP_EXE%" --self-test --self-test-output "%PACKAGED_SELFTEST%"
if errorlevel 1 goto :fail

echo [8/10] Running packaged Edge WebView2 renderer probe...
start "" /wait "%APP_EXE%" --renderer-smoke-test
if errorlevel 1 goto :fail

echo [9/10] Creating the complete release archive...
set "VERSION="
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -c "import insertion_loss_tool; print(insertion_loss_tool.__version__)" > "%VERSION_FILE%"
if errorlevel 1 goto :fail
set /p VERSION=<"%VERSION_FILE%"
if not defined VERSION goto :fail
del /q "%VERSION_FILE%"
if errorlevel 1 goto :fail
set "ARCHIVE=%CD%\dist\InsertionLossTool-%VERSION%-windows-x64.zip"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Compress-Archive -Path $env:APP_EXE -DestinationPath $env:ARCHIVE -Force"
if errorlevel 1 goto :fail

echo [10/10] Writing the SHA-256 manifest...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $line=(Get-FileHash -Algorithm SHA256 $env:ARCHIVE).Hash + '  ' + [IO.Path]::GetFileName($env:ARCHIVE); [IO.File]::WriteAllText($env:ARCHIVE + '.sha256.txt', $line + [Environment]::NewLine, [Text.Encoding]::ASCII)"
if errorlevel 1 goto :fail

echo.
echo BUILD PASSED
echo Application: %APP_EXE%
echo Archive:     %ARCHIVE%
echo Checksum:    %ARCHIVE%.sha256.txt
echo Complete the manual Windows acceptance checklist in AGENTS.md before release.
endlocal
exit /b 0

:missing_python
echo ERROR: The Python launcher was not found. Install 64-bit Python 3.9 or newer.
goto :fail

:unsupported_python
echo ERROR: The build requires 64-bit Python 3.9 or newer.
goto :fail

:missing_exe
echo ERROR: PyInstaller returned without creating %APP_EXE%.
goto :fail

:fail
set "BUILD_EXIT=%ERRORLEVEL%"
if "%BUILD_EXIT%"=="0" set "BUILD_EXIT=1"
echo.
echo BUILD FAILED. Do not distribute files from dist.
endlocal & exit /b %BUILD_EXIT%
