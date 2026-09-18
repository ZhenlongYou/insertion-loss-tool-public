#!/usr/bin/env bash
# Build a standalone macOS .app bundle for Insertion Loss Tool.
#
# The generated app includes Python, numpy, matplotlib, pywebview, and
# this project's source modules, so recipients do not need to install Python.
# It must be built on macOS; build_windows_exe.bat is provided for Windows.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$PWD/.pyinstaller-cache}"
if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt -r requirements-build.txt

rm -rf build dist
.venv/bin/python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "InsertionLossTool" \
  --paths "src" \
  --add-data "examples:examples" \
  --add-data "src/insertion_loss_tool/webui:insertion_loss_tool/webui" \
  --hidden-import "insertion_loss_tool.webview_gui" \
  --hidden-import "insertion_loss_tool.gui" \
  --hidden-import "matplotlib.backends.backend_tkagg" \
  --exclude-module "skrf" \
  --exclude-module "scipy" \
  --exclude-module "pandas" \
  gui_main.py

VERSION="$(PYTHONPATH=src .venv/bin/python -c 'import insertion_loss_tool; print(insertion_loss_tool.__version__)')"
APP_PATH="dist/InsertionLossTool.app"
PLIST_PATH="$APP_PATH/Contents/Info.plist"
ARCH="$(uname -m)"
ZIP_PATH="dist/InsertionLossTool-${VERSION}-macos-${ARCH}.zip"

if /usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$PLIST_PATH" >/dev/null 2>&1; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$PLIST_PATH"
else
  /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$PLIST_PATH"
fi
if /usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$PLIST_PATH" >/dev/null 2>&1; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST_PATH"
else
  /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST_PATH"
fi
if /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$PLIST_PATH" >/dev/null 2>&1; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.rinysproject.insertion-loss-tool" "$PLIST_PATH"
else
  /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.rinysproject.insertion-loss-tool" "$PLIST_PATH"
fi
codesign --force --deep --sign - "$APP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo "Built $APP_PATH"
echo "Archive: $ZIP_PATH"
echo "Self-test command:"
echo "  $APP_PATH/Contents/MacOS/InsertionLossTool --self-test"
