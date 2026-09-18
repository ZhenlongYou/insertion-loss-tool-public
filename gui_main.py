#!/usr/bin/env python3
"""Desktop GUI entry point for the insertion-loss tool.

This file is intentionally tiny because PyInstaller uses it as the executable
entry point. It bootstraps the local `src/` folder for source-tree runs, then
delegates all application behavior to `insertion_loss_tool.webview_gui`.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _configure_external_tool_path(home: Path | None = None) -> None:
    """Expose common package-manager binaries to Finder-launched apps.

    Finder starts applications with a minimal ``PATH``.  The datasheet OCR
    intentionally uses the user's installed Tesseract instead of bundling a
    second copy, so add only existing, conventional binary directories.
    """

    user_home = home or Path.home()
    candidates = (
        user_home / ".local" / "bin",
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin"),
    )
    current = [item for item in os.environ.get("PATH", "").split(os.pathsep) if item]
    additions = [str(path) for path in candidates if path.is_dir()]
    os.environ["PATH"] = os.pathsep.join(dict.fromkeys((*additions, *current)))


def _configure_matplotlib_cache() -> None:
    """Keep Matplotlib's font cache persistent for packaged GUI runs.

    PyInstaller apps otherwise tend to use transient runtime locations, which
    can make Matplotlib rebuild its font cache every launch. That rebuild is
    CPU-heavy and shows up to users as a frozen first plot, so the GUI entry
    point sets a stable per-user cache before any Matplotlib-related import can
    happen.
    """

    is_frozen = bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))
    if os.environ.get("MPLCONFIGDIR") and not is_frozen:
        return

    if sys.platform == "darwin":
        cache_root = Path.home() / "Library" / "Caches" / "InsertionLossTool"
    elif os.name == "nt":
        cache_root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "InsertionLossTool"
    else:
        cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "InsertionLossTool"

    matplotlib_cache = cache_root / "matplotlib"
    try:
        matplotlib_cache.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    os.environ["MPLCONFIGDIR"] = str(matplotlib_cache)


def _load_gui_main():
    """Load the GUI entry point after bootstrapping `src/`.

    Keeping this as a dynamic import avoids PyCharm marking the file red when
    it has not indexed `src/` as a source root, while the runtime behavior is
    the same as importing `insertion_loss_tool.webview_gui.main` directly.
    """

    return importlib.import_module("insertion_loss_tool.webview_gui").main


_configure_external_tool_path()
_configure_matplotlib_cache()


if __name__ == "__main__":
    raise SystemExit(_load_gui_main()())
