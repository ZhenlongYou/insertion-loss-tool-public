"""Tkinter desktop interface for generating and editing Touchstone files.

The GUI is a thin, user-friendly shell over the same model functions used by
the command-line workflow. Keeping the calculation path shared matters here:
stress tests and CLI tests exercise the same generation, draw smoothing,
Touchstone I/O, and phase-preserving modification code that the packaged app
uses at runtime.
"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 dataclasses 导入 dataclass，声明轻量数据结构并减少样板初始化代码。
from dataclasses import dataclass
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 argparse，解析命令行参数，支持用户从终端覆盖默认配置。
import argparse
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 导入 tempfile，创建测试或 demo 使用的临时文件目录。
import tempfile
# Codex说明(自动生成)： 从 typing 导入 Iterable，提供类型标注辅助名称，方便维护和静态检查。
from typing import Iterable

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np

# Codex说明(自动生成)： 从 cli 导入 write_modification_report，提供本文件后续流程需要的库能力。
from .cli import write_modification_report
# Codex说明(自动生成)： 从 models 导入 COMMON_PORT_COUNTS, build_network, default_through_pairs, draw_loss_points_interactive 等名称，提供本文件后续流程需要的库能力。
from .models import (
    COMMON_PORT_COUNTS,
    build_network,
    default_through_pairs,
    draw_loss_points_interactive,
    generate_frequency_axis,
    insert_draw_control_frequencies,
    interpolate_drawn_loss,
    linear_loss,
    modify_insertion_loss,
    parse_draw_points,
    parse_frequency,
    parse_pairs,
    parse_target_points,
    protocol_loss,
)
# Codex说明(自动生成)： 从 touchstone 导入 TouchstoneData, read_touchstone, to_magnitude_db, write_touchstone，提供本文件后续流程需要的库能力。
from .touchstone import TouchstoneData, read_touchstone, to_magnitude_db, write_touchstone
# Codex说明(自动生成)： 从 validation 导入 assert_sampled_passive, diagnose_sampled_network，提供本文件后续流程需要的库能力。
from .validation import assert_sampled_passive, diagnose_sampled_network


# Codex说明(自动生成)： 计算并保存 APP_NAME，供后续语句继续读取或更新。
APP_NAME = "Insertion Loss Tool"
# Codex说明(自动生成)： 计算并保存 DEFAULT_WINDOW_SIZE，供后续语句继续读取或更新。
DEFAULT_WINDOW_SIZE = (1380, 860)
# Codex说明(自动生成)： 计算并保存 BASE_MINIMUM_WINDOW_SIZE，供后续语句继续读取或更新。
BASE_MINIMUM_WINDOW_SIZE = (1100, 680)

# Codex说明(自动生成)： 计算并保存 DATASHEET_CURVES，供后续语句继续读取或更新。
DATASHEET_CURVES = (
    ("A", "深蓝"),
    ("B", "红"),
    ("C", "绿"),
    ("D", "浅蓝"),
)


# Codex说明(自动生成)： 定义 _OperationCancelled 类，把相关数据结构、校验规则或操作方法组织在一起。
class _OperationCancelled(RuntimeError):
    """A normal user cancellation that should not be presented as an error."""
# Codex说明(自动生成)： 计算并保存 OUTPUT_DIR，供后续语句继续读取或更新。
OUTPUT_DIR = Path.home() / "Documents" / "InsertionLossToolOutputs"


# Codex说明(自动生成)： 定义 GeneratedResult 类，把相关数据结构、校验规则或操作方法组织在一起。
@dataclass
class GeneratedResult:
    """Result bundle returned by the GUI generation routines.

    `report_path` is used only by modify mode. The GUI keeps it with the
    generated Touchstone path so the status panel can tell the user exactly
    where all durable output landed.
    """

    # Codex说明(自动生成)： 声明并保存 data，同时保留类型信息方便维护和静态检查。
    data: TouchstoneData
    # Codex说明(自动生成)： 声明并保存 output_path，同时保留类型信息方便维护和静态检查。
    output_path: Path
    # Codex说明(自动生成)： 声明并保存 report_path，同时保留类型信息方便维护和静态检查。
    report_path: Path | None = None


# Codex说明(自动生成)： 定义 InsertionLossStudio 类，把相关数据结构、校验规则或操作方法组织在一起。
class InsertionLossStudio:
    """Main desktop window.

    The interface deliberately stays dense and work-focused: common sweep
    settings live in a fixed control rail, mode-specific settings sit beside
    them, and the S-parameter matrix plot occupies the largest area. This makes
    repeated engineering checks faster than navigating a wizard-style flow.
    """

    # Codex说明(自动生成)： 定义函数 __init__，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def __init__(self, root):
        # Codex说明(自动生成)： 导入 tkinter as tk，提供本文件后续流程需要的库能力。
        import tkinter as tk
        # Codex说明(自动生成)： 从 tkinter 导入 ttk，提供本文件后续流程需要的库能力。
        from tkinter import ttk

        # Codex说明(自动生成)： 计算并保存 self.tk，供后续语句继续读取或更新。
        self.tk = tk
        # Codex说明(自动生成)： 计算并保存 self.ttk，供后续语句继续读取或更新。
        self.ttk = ttk
        # Codex说明(自动生成)： 计算并保存 self.root，供后续语句继续读取或更新。
        self.root = root
        # Codex说明(自动生成)： 调用 self.root.title 生成或展示图形，便于观察计算结果。
        self.root.title(APP_NAME)
        # Codex说明(自动生成)： 调用 self.root.geometry，执行当前流程需要的具体操作或副作用。
        self.root.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")
        # Codex说明(自动生成)： 调用 self.root.minsize，执行当前流程需要的具体操作或副作用。
        self.root.minsize(*BASE_MINIMUM_WINDOW_SIZE)

        # Codex说明(自动生成)： 计算并保存 self.mode_var，供后续语句继续读取或更新。
        self.mode_var = tk.StringVar(value="linear")
        # Codex说明(自动生成)： 计算并保存 self.plot_kind_var，供后续语句继续读取或更新。
        self.plot_kind_var = tk.StringVar(value="magnitude")
        # Codex说明(自动生成)： 计算并保存 self.status_var，供后续语句继续读取或更新。
        self.status_var = tk.StringVar(value="就绪")
        # Codex说明(自动生成)： 声明并保存 self.current_data，同时保留类型信息方便维护和静态检查。
        self.current_data: TouchstoneData | None = None
        # Codex说明(自动生成)： 声明并保存 self.datasheet_image_path，同时保留类型信息方便维护和静态检查。
        self.datasheet_image_path: Path | None = None
        # Codex说明(自动生成)： 声明并保存 self.datasheet_image_paths，同时保留类型信息方便维护和静态检查。
        self.datasheet_image_paths: list[Path] = []
        # Codex说明(自动生成)： 声明并保存 self.datasheet_image_previewable，同时保留类型信息方便维护和静态检查。
        self.datasheet_image_previewable: list[bool] = []
        # Codex说明(自动生成)： 计算并保存 self.datasheet_preview_canvases，供后续语句继续读取或更新。
        self.datasheet_preview_canvases = []
        # Codex说明(自动生成)： 计算并保存 self.datasheet_networks，供后续语句继续读取或更新。
        self.datasheet_networks = []
        # Codex说明(自动生成)： 计算并保存 self.datasheet_selected_network，供后续语句继续读取或更新。
        self.datasheet_selected_network = 0

        # Codex说明(自动生成)： 调用 self._init_variables，执行当前流程需要的具体操作或副作用。
        self._init_variables()
        # Codex说明(自动生成)： 调用 self._configure_style 生成或展示图形，便于观察计算结果。
        self._configure_style()
        # Codex说明(自动生成)： 调用 self._build_layout，执行当前流程需要的具体操作或副作用。
        self._build_layout()
        # Codex说明(自动生成)： 调用 self._select_mode，执行当前流程需要的具体操作或副作用。
        self._select_mode("linear")
        # Codex说明(自动生成)： 调用 self._apply_content_minimum_size，执行当前流程需要的具体操作或副作用。
        self._apply_content_minimum_size()

    # Codex说明(自动生成)： 定义函数 _apply_content_minimum_size，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _apply_content_minimum_size(self) -> None:
        """Keep every page inside the smallest window on the current platform."""

        # Codex说明(自动生成)： 调用 self.root.update_idletasks，执行当前流程需要的具体操作或副作用。
        self.root.update_idletasks()
        # Codex说明(自动生成)： 计算并保存 minimum_width，供后续语句继续读取或更新。
        minimum_width = min(
            DEFAULT_WINDOW_SIZE[0],
            max(BASE_MINIMUM_WINDOW_SIZE[0], self.root.winfo_reqwidth()),
        )
        # Codex说明(自动生成)： 计算并保存 minimum_height，供后续语句继续读取或更新。
        minimum_height = min(
            DEFAULT_WINDOW_SIZE[1],
            max(BASE_MINIMUM_WINDOW_SIZE[1], self.root.winfo_reqheight()),
        )
        # Codex说明(自动生成)： 调用 self.root.minsize，执行当前流程需要的具体操作或副作用。
        self.root.minsize(minimum_width, minimum_height)

    # Codex说明(自动生成)： 定义函数 _init_variables，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _init_variables(self) -> None:
        """Create Tk variables with engineering-safe defaults."""

        # Codex说明(自动生成)： 计算并保存 tk，供后续语句继续读取或更新。
        tk = self.tk
        # Codex说明(自动生成)： 计算并保存 self.common，供后续语句继续读取或更新。
        self.common = {
            "ports": tk.StringVar(value="2"),
            "f_start": tk.StringVar(value="10MHz"),
            "f_stop": tk.StringVar(value="40GHz"),
            "points": tk.StringVar(value="801"),
            "spacing": tk.StringVar(value="linear"),
            "format": tk.StringVar(value="ri"),
            "frequency_unit": tk.StringVar(value="ghz"),
            "return_loss_db": tk.StringVar(value="20.0"),
            "crosstalk_db": tk.StringVar(value="80.0"),
            "delay_ps": tk.StringVar(value="80.0"),
            "phase_offset_deg": tk.StringVar(value="0.0"),
            "z0": tk.StringVar(value="50.0"),
            "through_pairs": tk.StringVar(value=""),
            "output": tk.StringVar(value=""),
        }
        # Codex说明(自动生成)： 计算并保存 self.linear，供后续语句继续读取或更新。
        self.linear = {
            "loss_start_db": tk.StringVar(value="0.2"),
            "loss_stop_db": tk.StringVar(value="20.0"),
        }
        # Codex说明(自动生成)： 计算并保存 self.formula，供后续语句继续读取或更新。
        self.formula = {
            "a": tk.StringVar(value="0.08"),
            "b": tk.StringVar(value="0.6"),
            "c": tk.StringVar(value="0.1"),
            "model_frequency_unit": tk.StringVar(value="ghz"),
        }
        # Codex说明(自动生成)： 计算并保存 self.draw，供后续语句继续读取或更新。
        self.draw = {
            "loss_min_db": tk.StringVar(value="-40.0"),
            "loss_max_db": tk.StringVar(value="0.0"),
            "fit": tk.StringVar(value="smooth"),
            "fit_domain": tk.StringVar(value="linear"),
            "min_spacing_fraction": tk.StringVar(value="0.0001"),
            "max_slope_db_per_span": tk.StringVar(value="500.0"),
        }
        # Codex说明(自动生成)： 计算并保存 self.modify，供后续语句继续读取或更新。
        self.modify = {
            "input": tk.StringVar(value=str(default_example_path())),
            "targets": tk.StringVar(value="5GHz:3.0,12GHz:8.0"),
            "pairs": tk.StringVar(value="S21,S12"),
            "smoothness": tk.StringVar(value="0.14"),
            "smooth_domain": tk.StringVar(value="log"),
            "anchor_edges": tk.BooleanVar(value=True),
            "insert_targets": tk.BooleanVar(value=True),
        }
        # Codex说明(自动生成)： 计算并保存 self.datasheet，供后续语句继续读取或更新。
        self.datasheet = {
            "status": tk.StringVar(value="未生成"),
            "network_count": tk.StringVar(value="2"),
            "selected_network_summary": tk.StringVar(value="网络 1 · 4 端口 · 16 个 Sij"),
        }
        # Codex说明(自动生成)： 计算并保存 self.datasheet_networks，供后续语句继续读取或更新。
        self.datasheet_networks = [
            self._new_datasheet_network(0, 4),
            self._new_datasheet_network(1, 2),
        ]

    # Codex说明(自动生成)： 定义函数 _configure_style，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _configure_style(self) -> None:
        """Apply the protocol-comparison product family's dark visual system."""

        # Codex说明(自动生成)： 计算并保存 ttk，供后续语句继续读取或更新。
        ttk = self.ttk
        # Codex说明(自动生成)： 计算并保存 self.colors，供后续语句继续读取或更新。
        self.colors = {
            "bg": "#18192D",
            "panel": "#24253D",
            "panel_alt": "#2A2B47",
            "field": "#191A2D",
            "text": "#F7F5FF",
            "muted": "#AAA6BC",
            "accent": "#8BDEF8",
            "accent_2": "#8273FF",
            "accent_pink": "#EF75BD",
            "line": "#514E6B",
            "danger": "#FF8A9F",
        }
        # Codex说明(自动生成)： 调用 self.root.configure 生成或展示图形，便于观察计算结果。
        self.root.configure(bg=self.colors["bg"])
        # Codex说明(自动生成)： 调用 ttk.Style().theme_use，执行当前流程需要的具体操作或副作用。
        ttk.Style().theme_use("clam")
        # Codex说明(自动生成)： 计算并保存 style，供后续语句继续读取或更新。
        style = ttk.Style()
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(".", background=self.colors["bg"], foreground=self.colors["text"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Shell.TFrame", background=self.colors["bg"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Panel.TFrame", background=self.colors["panel"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Alt.TFrame", background=self.colors["panel_alt"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Card.TFrame",
            background=self.colors["panel"],
            borderwidth=1,
            relief="solid",
            bordercolor=self.colors["line"],
            lightcolor=self.colors["line"],
            darkcolor=self.colors["line"],
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Status.TFrame", background="#20213A")
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Muted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Status.TLabel", background="#20213A", foreground=self.colors["muted"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Title.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=("Helvetica", 22, "bold"),
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Header.TFrame",
            background=self.colors["bg"],
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Mode.TButton",
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            bordercolor=self.colors["line"],
            focusthickness=0,
            padding=(15, 12),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map("Mode.TButton", background=[("active", "#343553")])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "SelectedMode.TButton",
            background=self.colors["accent_2"],
            foreground=self.colors["text"],
            bordercolor=self.colors["accent_2"],
            focusthickness=0,
            padding=(15, 12),
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="#17182A",
            bordercolor=self.colors["accent"],
            focusthickness=0,
            font=("Helvetica", 13, "bold"),
            padding=(16, 12),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map("Accent.TButton", background=[("active", "#A9E9FB")])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Secondary.TButton",
            background="#403F66",
            foreground=self.colors["text"],
            bordercolor="#615E7E",
            focusthickness=0,
            padding=(11, 8),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map("Secondary.TButton", background=[("active", "#514F7A")])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Ghost.TButton",
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            bordercolor=self.colors["line"],
            padding=(10, 8),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map("Ghost.TButton", background=[("active", "#343553")])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "TEntry",
            fieldbackground=self.colors["field"],
            foreground=self.colors["text"],
            bordercolor=self.colors["line"],
            insertcolor=self.colors["text"],
            padding=(8, 7),
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "TCombobox",
            fieldbackground=self.colors["field"],
            background=self.colors["field"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["text"],
            bordercolor=self.colors["line"],
            padding=(8, 7),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.colors["field"])],
            foreground=[("readonly", self.colors["text"])],
            selectbackground=[("readonly", self.colors["field"])],
            selectforeground=[("readonly", self.colors["text"])],
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("TCheckbutton", background=self.colors["panel"], foreground=self.colors["text"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure("Alt.TLabel", background=self.colors["panel_alt"], foreground=self.colors["text"])
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "DatasheetTitle.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=("Helvetica", 18, "bold"),
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Workspace.TNotebook",
            background=self.colors["bg"],
            bordercolor=self.colors["bg"],
            borderwidth=0,
            lightcolor=self.colors["bg"],
            darkcolor=self.colors["bg"],
            tabmargins=(24, 14, 0, 0),
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Workspace.TNotebook.Tab",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            bordercolor=self.colors["line"],
            lightcolor=self.colors["line"],
            darkcolor=self.colors["line"],
            padding=(20, 10),
            font=("Helvetica", 11, "bold"),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map(
            "Workspace.TNotebook.Tab",
            background=[("selected", "#403F66"), ("active", self.colors["panel_alt"])],
            foreground=[("selected", self.colors["text"])],
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Plot.TNotebook",
            background=self.colors["panel"],
            bordercolor=self.colors["line"],
        )
        # Codex说明(自动生成)： 调用 style.configure 生成或展示图形，便于观察计算结果。
        style.configure(
            "Plot.TNotebook.Tab",
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            padding=(16, 8),
        )
        # Codex说明(自动生成)： 调用 style.map，执行当前流程需要的具体操作或副作用。
        style.map(
            "Plot.TNotebook.Tab",
            background=[("selected", self.colors["accent_2"])],
            foreground=[("selected", self.colors["text"])],
        )

    # Codex说明(自动生成)： 定义函数 _build_layout，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_layout(self) -> None:
        """Build the fixed navigation, controls, plot area, and status log."""

        # Codex说明(自动生成)： 计算并保存 ttk，供后续语句继续读取或更新。
        ttk = self.ttk
        # Codex说明(自动生成)： 计算并保存 self.workspace_notebook，供后续语句继续读取或更新。
        self.workspace_notebook = ttk.Notebook(self.root, style="Workspace.TNotebook")
        # Codex说明(自动生成)： 调用 self.workspace_notebook.pack，执行当前流程需要的具体操作或副作用。
        self.workspace_notebook.pack(fill="both", expand=True)
        # Codex说明(自动生成)： 计算并保存 self.generator_page，供后续语句继续读取或更新。
        self.generator_page = ttk.Frame(self.workspace_notebook, style="Shell.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.datasheet_page，供后续语句继续读取或更新。
        self.datasheet_page = ttk.Frame(self.workspace_notebook, style="Shell.TFrame")
        # Codex说明(自动生成)： 调用 self.workspace_notebook.add，执行当前流程需要的具体操作或副作用。
        self.workspace_notebook.add(self.generator_page, text="常规生成")
        # Codex说明(自动生成)： 调用 self.workspace_notebook.add，执行当前流程需要的具体操作或副作用。
        self.workspace_notebook.add(self.datasheet_page, text="图片生成")

        # Codex说明(自动生成)： 计算并保存 outer，供后续语句继续读取或更新。
        outer = ttk.Frame(self.generator_page, style="Shell.TFrame", padding=(24, 20, 24, 22))
        # Codex说明(自动生成)： 调用 outer.pack，执行当前流程需要的具体操作或副作用。
        outer.pack(fill="both", expand=True)
        # Codex说明(自动生成)： 调用 outer.columnconfigure 生成或展示图形，便于观察计算结果。
        outer.columnconfigure(1, weight=1)
        # Codex说明(自动生成)： 调用 outer.rowconfigure 生成或展示图形，便于观察计算结果。
        outer.rowconfigure(1, weight=1)

        # Codex说明(自动生成)： 计算并保存 header，供后续语句继续读取或更新。
        header = ttk.Frame(outer, style="Header.TFrame")
        # Codex说明(自动生成)： 调用 header.grid 生成或展示图形，便于观察计算结果。
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        # Codex说明(自动生成)： 调用 header.columnconfigure 生成或展示图形，便于观察计算结果。
        header.columnconfigure(1, weight=1)
        # Codex说明(自动生成)： 计算并保存 self.brand_mark，供后续语句继续读取或更新。
        self.brand_mark = self.tk.Canvas(
            header,
            width=38,
            height=34,
            bg=self.colors["bg"],
            highlightthickness=0,
            bd=0,
        )
        # Codex说明(自动生成)： 调用 self.brand_mark.create_rectangle，执行当前流程需要的具体操作或副作用。
        self.brand_mark.create_rectangle(3, 3, 25, 25, fill=self.colors["accent_2"], outline="")
        # Codex说明(自动生成)： 调用 self.brand_mark.create_rectangle，执行当前流程需要的具体操作或副作用。
        self.brand_mark.create_rectangle(11, 10, 33, 32, fill=self.colors["accent_pink"], outline="")
        # Codex说明(自动生成)： 调用 self.brand_mark.grid 生成或展示图形，便于观察计算结果。
        self.brand_mark.grid(row=0, column=0, sticky="w", padx=(0, 10))
        # Codex说明(自动生成)： 计算并保存 title，供后续语句继续读取或更新。
        title = ttk.Label(header, text="插损生成器", style="Title.TLabel")
        # Codex说明(自动生成)： 调用 title.grid 生成或展示图形，便于观察计算结果。
        title.grid(row=0, column=1, sticky="w")
        # Codex说明(自动生成)： 计算并保存 self.run_button，供后续语句继续读取或更新。
        self.run_button = ttk.Button(
            header,
            text="生成",
            style="Accent.TButton",
            command=self.generate,
        )
        # Codex说明(自动生成)： 调用 self.run_button.grid 生成或展示图形，便于观察计算结果。
        self.run_button.grid(row=0, column=2, sticky="e")

        # Codex说明(自动生成)： 计算并保存 sidebar，供后续语句继续读取或更新。
        sidebar = ttk.Frame(outer, style="Card.TFrame", padding=16)
        # Codex说明(自动生成)： 调用 sidebar.grid 生成或展示图形，便于观察计算结果。
        sidebar.grid(row=1, column=0, sticky="nsw", padx=(0, 16))
        # Codex说明(自动生成)： 计算并保存 self.mode_buttons，供后续语句继续读取或更新。
        self.mode_buttons = {}
        # Codex说明(自动生成)： 遍历 enumerate([('linear', '线性'), ('formula', '协议公式'), ('dra... 中的 (row, (mode, label))，逐项执行循环体逻辑。
        for row, (mode, label) in enumerate(
            [
                ("linear", "线性"),
                ("formula", "协议公式"),
                ("draw", "手绘"),
                ("modify", "修改"),
            ]
        ):
            # Codex说明(自动生成)： 计算并保存 button，供后续语句继续读取或更新。
            button = ttk.Button(
                sidebar,
                text=label,
                style="Mode.TButton",
                command=lambda value=mode: self._select_mode(value),
            )
            # Codex说明(自动生成)： 调用 button.grid 生成或展示图形，便于观察计算结果。
            button.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            # Codex说明(自动生成)： 计算并保存 self.mode_buttons[mode]，供后续语句继续读取或更新。
            self.mode_buttons[mode] = button
        # Codex说明(自动生成)： 调用 sidebar.columnconfigure 生成或展示图形，便于观察计算结果。
        sidebar.columnconfigure(0, minsize=128)

        # Codex说明(自动生成)： 计算并保存 work，供后续语句继续读取或更新。
        work = ttk.Frame(outer, style="Shell.TFrame")
        # Codex说明(自动生成)： 调用 work.grid 生成或展示图形，便于观察计算结果。
        work.grid(row=1, column=1, sticky="nsew")
        # Codex说明(自动生成)： 调用 work.columnconfigure 生成或展示图形，便于观察计算结果。
        work.columnconfigure(1, weight=1)
        # Codex说明(自动生成)： 调用 work.rowconfigure 生成或展示图形，便于观察计算结果。
        work.rowconfigure(0, weight=1)

        # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
        controls = self._build_scrollable_controls(work)
        # Codex说明(自动生成)： 调用 self._build_common_controls，执行当前流程需要的具体操作或副作用。
        self._build_common_controls(controls)

        # Codex说明(自动生成)： 计算并保存 plot_panel，供后续语句继续读取或更新。
        plot_panel = ttk.Frame(work, style="Card.TFrame", padding=16)
        # Codex说明(自动生成)： 调用 plot_panel.grid 生成或展示图形，便于观察计算结果。
        plot_panel.grid(row=0, column=1, sticky="nsew")
        # Codex说明(自动生成)： 调用 plot_panel.columnconfigure 生成或展示图形，便于观察计算结果。
        plot_panel.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 plot_panel.rowconfigure 生成或展示图形，便于观察计算结果。
        plot_panel.rowconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 self._build_plot_panel 生成或展示图形，便于观察计算结果。
        self._build_plot_panel(plot_panel)

        # Codex说明(自动生成)： 计算并保存 self.status_bar，供后续语句继续读取或更新。
        self.status_bar = ttk.Frame(outer, style="Status.TFrame", padding=(14, 10))
        # Codex说明(自动生成)： 调用 self.status_bar.grid 生成或展示图形，便于观察计算结果。
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        # Codex说明(自动生成)： 调用 self.status_bar.columnconfigure 生成或展示图形，便于观察计算结果。
        self.status_bar.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 ttk.Label(self.status_bar, textvariable=self.status_var....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(self.status_bar, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        # Codex说明(自动生成)： 调用 self._build_datasheet_page，执行当前流程需要的具体操作或副作用。
        self._build_datasheet_page(self.datasheet_page)

    # Codex说明(自动生成)： 定义函数 _build_datasheet_page，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_datasheet_page(self, parent) -> None:
        """Build a composable multi-image, multi-network datasheet workbench."""

        # Codex说明(自动生成)： 计算并保存 ttk，供后续语句继续读取或更新。
        ttk = self.ttk
        # Codex说明(自动生成)： 调用 parent.columnconfigure 生成或展示图形，便于观察计算结果。
        parent.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 parent.rowconfigure 生成或展示图形，便于观察计算结果。
        parent.rowconfigure(1, weight=1)

        # Codex说明(自动生成)： 计算并保存 header，供后续语句继续读取或更新。
        header = ttk.Frame(parent, style="Shell.TFrame", padding=(24, 20, 24, 16))
        # Codex说明(自动生成)： 调用 header.grid 生成或展示图形，便于观察计算结果。
        header.grid(row=0, column=0, sticky="ew")
        # Codex说明(自动生成)： 调用 header.columnconfigure 生成或展示图形，便于观察计算结果。
        header.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 ttk.Label(header, text='图片生成 S 参数', style='DatasheetTit....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(header, text="图片生成 S 参数", style="DatasheetTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        # Codex说明(自动生成)： 调用 ttk.Button(header, text='导入图片', style='Accent.TButton',....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(
            header,
            text="导入图片",
            style="Accent.TButton",
            command=self._browse_datasheet_images,
        ).grid(row=0, column=1, sticky="e")

        # Codex说明(自动生成)： 计算并保存 body，供后续语句继续读取或更新。
        body = ttk.Frame(parent, style="Shell.TFrame", padding=(24, 0, 24, 14))
        # Codex说明(自动生成)： 调用 body.grid 生成或展示图形，便于观察计算结果。
        body.grid(row=1, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 body.columnconfigure 生成或展示图形，便于观察计算结果。
        body.columnconfigure(0, weight=0, minsize=240)
        # Codex说明(自动生成)： 调用 body.columnconfigure 生成或展示图形，便于观察计算结果。
        body.columnconfigure(1, weight=0, minsize=360)
        # Codex说明(自动生成)： 调用 body.columnconfigure 生成或展示图形，便于观察计算结果。
        body.columnconfigure(2, weight=1)
        # Codex说明(自动生成)： 调用 body.rowconfigure 生成或展示图形，便于观察计算结果。
        body.rowconfigure(0, weight=1)

        # Codex说明(自动生成)： 计算并保存 task_panel，供后续语句继续读取或更新。
        task_panel = self._datasheet_panel(body, "输出")
        # Codex说明(自动生成)： 调用 task_panel.grid 生成或展示图形，便于观察计算结果。
        task_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # Codex说明(自动生成)： 调用 task_panel.rowconfigure 生成或展示图形，便于观察计算结果。
        task_panel.rowconfigure(2, weight=1)
        # Codex说明(自动生成)： 计算并保存 count_row，供后续语句继续读取或更新。
        count_row = ttk.Frame(task_panel, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 count_row.grid 生成或展示图形，便于观察计算结果。
        count_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # Codex说明(自动生成)： 调用 count_row.columnconfigure 生成或展示图形，便于观察计算结果。
        count_row.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 ttk.Label(count_row, text='数量', style='Muted.TLabel').grid 生成或展示图形，便于观察计算结果。
        ttk.Label(count_row, text="数量", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        # Codex说明(自动生成)： 调用 ttk.Combobox(count_row, textvariable=self.datasheet['ne....grid 生成或展示图形，便于观察计算结果。
        ttk.Combobox(
            count_row,
            textvariable=self.datasheet["network_count"],
            values=[str(value) for value in range(1, 7)],
            state="readonly",
            width=4,
        ).grid(row=0, column=1, padx=(8, 4))
        # Codex说明(自动生成)： 调用 ttk.Button(count_row, text='应用', style='Ghost.TButton',....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(
            count_row,
            text="应用",
            style="Ghost.TButton",
            command=self._apply_datasheet_network_count,
        ).grid(row=0, column=2)
        # Codex说明(自动生成)： 计算并保存 self.datasheet_network_list，供后续语句继续读取或更新。
        self.datasheet_network_list = ttk.Frame(task_panel, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 self.datasheet_network_list.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_network_list.grid(row=2, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 ttk.Button(task_panel, text='＋ 输出', style='Ghost.TButto....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(task_panel, text="＋ 输出", style="Ghost.TButton", command=self._add_datasheet_network).grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        # Codex说明(自动生成)： 计算并保存 source_panel，供后续语句继续读取或更新。
        source_panel = self._datasheet_panel(body, "图片")
        # Codex说明(自动生成)： 调用 source_panel.grid 生成或展示图形，便于观察计算结果。
        source_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        # Codex说明(自动生成)： 调用 source_panel.rowconfigure 生成或展示图形，便于观察计算结果。
        source_panel.rowconfigure(2, weight=1)
        # Codex说明(自动生成)： 计算并保存 self.datasheet_resource_list，供后续语句继续读取或更新。
        self.datasheet_resource_list = ttk.Frame(source_panel, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 self.datasheet_resource_list.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_resource_list.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # Codex说明(自动生成)： 调用 self._create_datasheet_preview，执行当前流程需要的具体操作或副作用。
        self._create_datasheet_preview(source_panel, row=2, width=360, height=320)
        # Codex说明(自动生成)： 计算并保存 axis_bar，供后续语句继续读取或更新。
        axis_bar = ttk.Frame(source_panel, style="Alt.TFrame", padding=(8, 6))
        # Codex说明(自动生成)： 调用 axis_bar.grid 生成或展示图形，便于观察计算结果。
        axis_bar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        # Codex说明(自动生成)： 调用 axis_bar.columnconfigure 生成或展示图形，便于观察计算结果。
        axis_bar.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 ttk.Label(axis_bar, text='0.01–40 GHz · −50–50 dB · 100....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(
            axis_bar,
            text="0.01–40 GHz · −50–50 dB · 1001 点",
            style="Alt.TLabel",
        ).grid(row=0, column=0, sticky="w")
        # Codex说明(自动生成)： 调用 ttk.Button(axis_bar, text='校准', style='Ghost.TButton', ....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(axis_bar, text="校准", style="Ghost.TButton", state="disabled").grid(
            row=0, column=1, padx=(8, 0)
        )
        # Codex说明(自动生成)： 调用 ttk.Button(source_panel, text='＋ 图片', style='Ghost.TBut....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(
            source_panel,
            text="＋ 图片",
            style="Ghost.TButton",
            command=self._browse_datasheet_images,
        ).grid(row=4, column=0, sticky="ew", pady=(9, 0))

        # Codex说明(自动生成)： 计算并保存 self.datasheet_detail_host，供后续语句继续读取或更新。
        self.datasheet_detail_host = ttk.Frame(body, style="Shell.TFrame")
        # Codex说明(自动生成)： 调用 self.datasheet_detail_host.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_detail_host.grid(row=0, column=2, sticky="nsew")
        # Codex说明(自动生成)： 调用 self.datasheet_detail_host.columnconfigure 生成或展示图形，便于观察计算结果。
        self.datasheet_detail_host.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 self.datasheet_detail_host.rowconfigure 生成或展示图形，便于观察计算结果。
        self.datasheet_detail_host.rowconfigure(0, weight=1)

        # Codex说明(自动生成)： 计算并保存 self.datasheet_footer，供后续语句继续读取或更新。
        self.datasheet_footer = ttk.Frame(parent, style="Status.TFrame", padding=(18, 10))
        # Codex说明(自动生成)： 调用 self.datasheet_footer.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        # Codex说明(自动生成)： 调用 self.datasheet_footer.columnconfigure 生成或展示图形，便于观察计算结果。
        self.datasheet_footer.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 ttk.Label(self.datasheet_footer, textvariable=self.data....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(self.datasheet_footer, textvariable=self.datasheet["status"], style="Status.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        # Codex说明(自动生成)： 调用 ttk.Button(self.datasheet_footer, text='检查', style='Sec....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(
            self.datasheet_footer,
            text="检查",
            style="Secondary.TButton",
            command=self._check_datasheet_mappings,
        ).grid(row=0, column=1, padx=(10, 8))
        # Codex说明(自动生成)： 调用 ttk.Button(self.datasheet_footer, text='预览', style='Acc....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(self.datasheet_footer, text="预览", style="Accent.TButton", state="disabled").grid(row=0, column=2)
        # Codex说明(自动生成)： 调用 ttk.Label(self.datasheet_footer, textvariable=self.data....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(
            self.datasheet_footer,
            textvariable=self.datasheet["selected_network_summary"],
            style="Status.TLabel",
        ).grid(row=0, column=3, sticky="e", padx=(14, 0))

        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_network_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_network_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_resource_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_resource_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_detail()

    # Codex说明(自动生成)： 定义函数 _new_datasheet_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _new_datasheet_network(self, index: int, port_count: int):
        # Codex说明(自动生成)： 计算并保存 number，供后续语句继续读取或更新。
        number = index + 1
        # Codex说明(自动生成)： 计算并保存 name，供后续语句继续读取或更新。
        name = f"输出 {number}"
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = f"output_{number}.s{port_count}p"
        # Codex说明(自动生成)： 返回 {'name': self.tk.StringVar(value=name), 'output': self....，让调用方取得本函数的处理结果。
        return {
            "name": self.tk.StringVar(value=name),
            "output": self.tk.StringVar(value=output),
            "port_count": self.tk.StringVar(value=str(port_count)),
            "phase": self.tk.StringVar(value="延迟模型 · 人工确认"),
            "reciprocal": self.tk.BooleanVar(value=True),
            "mappings": self._new_datasheet_mappings(port_count),
        }

    # Codex说明(自动生成)： 定义函数 _new_datasheet_mappings，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _new_datasheet_mappings(self, port_count: int, existing=None):
        # Codex说明(自动生成)： 计算并保存 mappings，供后续语句继续读取或更新。
        mappings = {}
        # Codex说明(自动生成)： 计算并保存 existing，供后续语句继续读取或更新。
        existing = existing or {}
        # Codex说明(自动生成)： 遍历 range(1, port_count + 1) 中的 output_port，逐项执行循环体逻辑。
        for output_port in range(1, port_count + 1):
            # Codex说明(自动生成)： 遍历 range(1, port_count + 1) 中的 input_port，逐项执行循环体逻辑。
            for input_port in range(1, port_count + 1):
                # Codex说明(自动生成)： 计算并保存 parameter，供后续语句继续读取或更新。
                parameter = f"S{output_port}{input_port}"
                # Codex说明(自动生成)： 检查条件 parameter in existing，根据结果选择后续执行路径。
                if parameter in existing:
                    # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
                    value = existing[parameter].get()
                # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 parameter == 'S12'。
                elif parameter == "S12":
                    # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
                    value = "复制 S21"
                # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 output_port == input_port。
                elif output_port == input_port:
                    # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
                    value = "默认 −20 dB"
                # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
                else:
                    # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
                    value = "默认 −80 dB"
                # Codex说明(自动生成)： 计算并保存 mappings[parameter]，供后续语句继续读取或更新。
                mappings[parameter] = self.tk.StringVar(value=value)
        # Codex说明(自动生成)： 返回 mappings，让调用方取得本函数的处理结果。
        return mappings

    # Codex说明(自动生成)： 定义函数 _datasheet_source_options，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _datasheet_source_options(self):
        # Codex说明(自动生成)： 计算并保存 options，供后续语句继续读取或更新。
        options = ["自动"]
        # Codex说明(自动生成)： 遍历 enumerate(self.datasheet_image_previewable, start=1) 中的 (image_index, previewable)，逐项执行循环体逻辑。
        for image_index, previewable in enumerate(self.datasheet_image_previewable, start=1):
            # Codex说明(自动生成)： 检查条件 not previewable，根据结果选择后续执行路径。
            if not previewable:
                # Codex说明(自动生成)： 跳过本轮剩余逻辑，直接进入下一轮循环判断。
                continue
            # Codex说明(自动生成)： 遍历 DATASHEET_CURVES 中的 (curve_name, color_name)，逐项执行循环体逻辑。
            for curve_name, color_name in DATASHEET_CURVES:
                # Codex说明(自动生成)： 调用 options.append 更新列表或集合，把当前步骤产生的数据加入结果。
                options.append(f"图{image_index}-{curve_name} · {color_name}")
        # Codex说明(自动生成)： 调用 options.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        options.extend(
            [
                "复制转置",
                "复制 S21",
                "公式",
                "默认 −20 dB",
                "默认 −80 dB",
                "未知",
            ]
        )
        # Codex说明(自动生成)： 返回 options，让调用方取得本函数的处理结果。
        return options

    # Codex说明(自动生成)： 定义函数 _invalidate_unavailable_datasheet_sources，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _invalidate_unavailable_datasheet_sources(self) -> None:
        # Codex说明(自动生成)： 计算并保存 available，供后续语句继续读取或更新。
        available = set(self._datasheet_source_options())
        # Codex说明(自动生成)： 遍历 self.datasheet_networks 中的 network，逐项执行循环体逻辑。
        for network in self.datasheet_networks:
            # Codex说明(自动生成)： 遍历 network['mappings'].values() 中的 variable，逐项执行循环体逻辑。
            for variable in network["mappings"].values():
                # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
                value = variable.get()
                # Codex说明(自动生成)： 检查条件 value.startswith('图') and value not in available，根据结果选择后续执行路径。
                if value.startswith("图") and value not in available:
                    # Codex说明(自动生成)： 调用 variable.set，执行当前流程需要的具体操作或副作用。
                    variable.set("未知")

    # Codex说明(自动生成)： 定义函数 _apply_datasheet_network_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _apply_datasheet_network_count(self) -> None:
        # Codex说明(自动生成)： 计算并保存 requested，供后续语句继续读取或更新。
        requested = int(self.datasheet["network_count"].get())
        # Codex说明(自动生成)： 计算并保存 requested，供后续语句继续读取或更新。
        requested = min(6, max(1, requested))
        # Codex说明(自动生成)： 当条件 len(self.datasheet_networks) < requested 成立时，重复执行循环体逻辑。
        while len(self.datasheet_networks) < requested:
            # Codex说明(自动生成)： 计算并保存 index，供后续语句继续读取或更新。
            index = len(self.datasheet_networks)
            # Codex说明(自动生成)： 调用 self.datasheet_networks.append 更新列表或集合，把当前步骤产生的数据加入结果。
            self.datasheet_networks.append(self._new_datasheet_network(index, 2))
        # Codex说明(自动生成)： 删除 self.datasheet_networks[requested:]，释放不再需要的引用或状态。
        del self.datasheet_networks[requested:]
        # Codex说明(自动生成)： 计算并保存 self.datasheet_selected_network，供后续语句继续读取或更新。
        self.datasheet_selected_network = min(self.datasheet_selected_network, requested - 1)
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_network_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_network_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_detail()
        # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
        self.datasheet["status"].set(f"{requested} 个输出")

    # Codex说明(自动生成)： 定义函数 _add_datasheet_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _add_datasheet_network(self) -> None:
        # Codex说明(自动生成)： 计算并保存 current，供后续语句继续读取或更新。
        current = len(self.datasheet_networks)
        # Codex说明(自动生成)： 检查条件 current >= 6，根据结果选择后续执行路径。
        if current >= 6:
            # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
            self.datasheet["status"].set("最多 6 个输出")
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 调用 self.datasheet['network_count'].set，执行当前流程需要的具体操作或副作用。
        self.datasheet["network_count"].set(str(current + 1))
        # Codex说明(自动生成)： 调用 self._apply_datasheet_network_count，执行当前流程需要的具体操作或副作用。
        self._apply_datasheet_network_count()
        # Codex说明(自动生成)： 调用 self._select_datasheet_network，执行当前流程需要的具体操作或副作用。
        self._select_datasheet_network(current)

    # Codex说明(自动生成)： 定义函数 _select_datasheet_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _select_datasheet_network(self, index: int) -> None:
        # Codex说明(自动生成)： 检查条件 index < 0 or index >= len(self.datasheet_networks)，根据结果选择后续执行路径。
        if index < 0 or index >= len(self.datasheet_networks):
            # Codex说明(自动生成)： 抛出 IndexError(f'Datasheet network index out of range: {ind...，明确提示输入、状态或处理流程无法继续。
            raise IndexError(f"Datasheet network index out of range: {index}")
        # Codex说明(自动生成)： 计算并保存 self.datasheet_selected_network，供后续语句继续读取或更新。
        self.datasheet_selected_network = index
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_network_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_network_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_detail()

    # Codex说明(自动生成)： 定义函数 _apply_selected_network_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _apply_selected_network_ports(self) -> None:
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = self.datasheet_networks[self.datasheet_selected_network]
        # Codex说明(自动生成)： 计算并保存 port_count，供后续语句继续读取或更新。
        port_count = min(8, max(1, int(network["port_count"].get())))
        # Codex说明(自动生成)： 调用 network['port_count'].set，执行当前流程需要的具体操作或副作用。
        network["port_count"].set(str(port_count))
        # Codex说明(自动生成)： 计算并保存 network['mappings']，供后续语句继续读取或更新。
        network["mappings"] = self._new_datasheet_mappings(port_count, network["mappings"])
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = network["output"].get()
        # Codex说明(自动生成)： 计算并保存 default_prefix，供后续语句继续读取或更新。
        default_prefix = f"output_{self.datasheet_selected_network + 1}.s"
        # Codex说明(自动生成)： 检查条件 output.startswith(default_prefix) and output.endswith('p')，根据结果选择后续执行路径。
        if output.startswith(default_prefix) and output.endswith("p"):
            # Codex说明(自动生成)： 调用 network['output'].set，执行当前流程需要的具体操作或副作用。
            network["output"].set(f"{default_prefix}{port_count}p")
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_network_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_network_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_detail()
        # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
        self.datasheet["status"].set(f"{port_count} 端口 · {port_count * port_count} 个 Sij")

    # Codex说明(自动生成)： 定义函数 _rebuild_datasheet_network_list，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _rebuild_datasheet_network_list(self) -> None:
        # Codex说明(自动生成)： 遍历 self.datasheet_network_list.winfo_children() 中的 child，逐项执行循环体逻辑。
        for child in self.datasheet_network_list.winfo_children():
            # Codex说明(自动生成)： 调用 child.destroy，执行当前流程需要的具体操作或副作用。
            child.destroy()
        # Codex说明(自动生成)： 遍历 enumerate(self.datasheet_networks) 中的 (index, network)，逐项执行循环体逻辑。
        for index, network in enumerate(self.datasheet_networks):
            # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
            ports = network["port_count"].get()
            # Codex说明(自动生成)： 计算并保存 selected，供后续语句继续读取或更新。
            selected = index == self.datasheet_selected_network
            # Codex说明(自动生成)： 计算并保存 button，供后续语句继续读取或更新。
            button = self.ttk.Button(
                self.datasheet_network_list,
                text=f"{network['name'].get()} · {ports}P · {network['output'].get()}",
                style="SelectedMode.TButton" if selected else "Ghost.TButton",
                command=lambda value=index: self._select_datasheet_network(value),
            )
            # Codex说明(自动生成)： 调用 button.grid 生成或展示图形，便于观察计算结果。
            button.grid(row=index, column=0, sticky="ew", pady=(0, 7))
        # Codex说明(自动生成)： 调用 self.datasheet_network_list.columnconfigure 生成或展示图形，便于观察计算结果。
        self.datasheet_network_list.columnconfigure(0, weight=1)

    # Codex说明(自动生成)： 定义函数 _rebuild_datasheet_resource_list，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _rebuild_datasheet_resource_list(self) -> None:
        # Codex说明(自动生成)： 遍历 self.datasheet_resource_list.winfo_children() 中的 child，逐项执行循环体逻辑。
        for child in self.datasheet_resource_list.winfo_children():
            # Codex说明(自动生成)： 调用 child.destroy，执行当前流程需要的具体操作或副作用。
            child.destroy()
        # Codex说明(自动生成)： 检查条件 not self.datasheet_image_paths，根据结果选择后续执行路径。
        if not self.datasheet_image_paths:
            # Codex说明(自动生成)： 调用 self.ttk.Label(self.datasheet_resource_list, text='暂无图片....grid 生成或展示图形，便于观察计算结果。
            self.ttk.Label(
                self.datasheet_resource_list,
                text="暂无图片",
                style="Muted.TLabel",
            ).grid(row=0, column=0, sticky="w", pady=6)
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 遍历 enumerate(self.datasheet_image_paths) 中的 (index, path)，逐项执行循环体逻辑。
        for index, path in enumerate(self.datasheet_image_paths):
            # Codex说明(自动生成)： 计算并保存 previewable，供后续语句继续读取或更新。
            previewable = self.datasheet_image_previewable[index]
            # Codex说明(自动生成)： 计算并保存 source_state，供后续语句继续读取或更新。
            source_state = "4 候选" if previewable else "预览受限"
            # Codex说明(自动生成)： 计算并保存 item，供后续语句继续读取或更新。
            item = self.ttk.Frame(self.datasheet_resource_list, style="Alt.TFrame", padding=(9, 7))
            # Codex说明(自动生成)： 调用 item.grid 生成或展示图形，便于观察计算结果。
            item.grid(row=index, column=0, sticky="ew", pady=(0, 5))
            # Codex说明(自动生成)： 调用 item.columnconfigure 生成或展示图形，便于观察计算结果。
            item.columnconfigure(0, weight=1)
            # Codex说明(自动生成)： 调用 self.ttk.Label(item, text=f'图{index + 1} · {path.name} ....grid 生成或展示图形，便于观察计算结果。
            self.ttk.Label(
                item,
                text=f"图{index + 1} · {path.name} · {source_state}",
                style="Alt.TLabel",
                font=("Helvetica", 10, "bold"),
            ).grid(row=0, column=0, sticky="w")
            # Codex说明(自动生成)： 调用 self.ttk.Button(item, text='查看', style='Ghost.TButton',....grid 生成或展示图形，便于观察计算结果。
            self.ttk.Button(
                item,
                text="查看",
                style="Ghost.TButton",
                command=lambda value=index: self._show_datasheet_image(value),
            ).grid(row=0, column=1, padx=(8, 0))
        # Codex说明(自动生成)： 调用 self.datasheet_resource_list.columnconfigure 生成或展示图形，便于观察计算结果。
        self.datasheet_resource_list.columnconfigure(0, weight=1)

    # Codex说明(自动生成)： 定义函数 _rebuild_datasheet_detail，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _rebuild_datasheet_detail(self) -> None:
        # Codex说明(自动生成)： 遍历 self.datasheet_detail_host.winfo_children() 中的 child，逐项执行循环体逻辑。
        for child in self.datasheet_detail_host.winfo_children():
            # Codex说明(自动生成)： 调用 child.destroy，执行当前流程需要的具体操作或副作用。
            child.destroy()
        # Codex说明(自动生成)： 计算并保存 network，供后续语句继续读取或更新。
        network = self.datasheet_networks[self.datasheet_selected_network]
        # Codex说明(自动生成)： 计算并保存 port_count，供后续语句继续读取或更新。
        port_count = int(network["port_count"].get())
        # Codex说明(自动生成)： 计算并保存 detail，供后续语句继续读取或更新。
        detail = self._datasheet_panel(
            self.datasheet_detail_host,
            f"Sij · 网络 {self.datasheet_selected_network + 1}",
        )
        # Codex说明(自动生成)： 调用 detail.grid 生成或展示图形，便于观察计算结果。
        detail.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 detail.rowconfigure 生成或展示图形，便于观察计算结果。
        detail.rowconfigure(2, weight=1)
        # Codex说明(自动生成)： 计算并保存 settings，供后续语句继续读取或更新。
        settings = self.ttk.Frame(detail, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.datasheet_settings，供后续语句继续读取或更新。
        self.datasheet_settings = settings
        # Codex说明(自动生成)： 调用 settings.grid 生成或展示图形，便于观察计算结果。
        settings.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # Codex说明(自动生成)： 遍历 range(6) 中的 column，逐项执行循环体逻辑。
        for column in range(6):
            # Codex说明(自动生成)： 调用 settings.columnconfigure 生成或展示图形，便于观察计算结果。
            settings.columnconfigure(column, weight=1 if column in {1, 4, 5} else 0)
        # Codex说明(自动生成)： 调用 self.ttk.Label(settings, text='名称', style='Muted.TLabel').grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(settings, text="名称", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        # Codex说明(自动生成)： 调用 self.ttk.Entry(settings, textvariable=network['name'], ....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Entry(settings, textvariable=network["name"], width=18).grid(row=0, column=1, columnspan=3, sticky="ew", padx=(6, 12))
        # Codex说明(自动生成)： 调用 self.ttk.Checkbutton(settings, text='互易网络', variable=ne....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Checkbutton(settings, text="互易网络", variable=network["reciprocal"]).grid(row=0, column=4, columnspan=2, sticky="e")
        # Codex说明(自动生成)： 调用 self.ttk.Label(settings, text='端口', style='Muted.TLabel').grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(settings, text="端口", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(7, 0))
        # Codex说明(自动生成)： 调用 self.ttk.Combobox(settings, textvariable=network['port_....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Combobox(
            settings,
            textvariable=network["port_count"],
            values=[str(value) for value in COMMON_PORT_COUNTS],
            state="readonly",
            width=6,
        ).grid(row=1, column=1, sticky="w", padx=(6, 4), pady=(7, 0))
        # Codex说明(自动生成)： 调用 self.ttk.Button(settings, text='应用', style='Ghost.TButt....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Button(settings, text="应用", style="Ghost.TButton", command=self._apply_selected_network_ports).grid(row=1, column=2, padx=(0, 12), pady=(7, 0))
        # Codex说明(自动生成)： 调用 self.ttk.Label(settings, text='输出', style='Muted.TLabel').grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(settings, text="输出", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(7, 0))
        # Codex说明(自动生成)： 计算并保存 self.datasheet_output_entry，供后续语句继续读取或更新。
        self.datasheet_output_entry = self.ttk.Entry(settings, textvariable=network["output"], width=20)
        # Codex说明(自动生成)： 调用 self.datasheet_output_entry.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_output_entry.grid(
            row=2,
            column=1,
            columnspan=5,
            sticky="ew",
            padx=(6, 0),
            pady=(7, 0),
        )
        # Codex说明(自动生成)： 调用 self.ttk.Label(settings, text='相位', style='Muted.TLabel').grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(settings, text="相位", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(7, 0))
        # Codex说明(自动生成)： 计算并保存 self.datasheet_phase_combo，供后续语句继续读取或更新。
        self.datasheet_phase_combo = self.ttk.Combobox(
            settings,
            textvariable=network["phase"],
            values=["延迟模型 · 人工确认", "最小相位 · 假设", "零相位 · 仅调试"],
            state="readonly",
            width=20,
        )
        # Codex说明(自动生成)： 调用 self.datasheet_phase_combo.grid 生成或展示图形，便于观察计算结果。
        self.datasheet_phase_combo.grid(
            row=3,
            column=1,
            columnspan=5,
            sticky="ew",
            padx=(6, 0),
            pady=(7, 0),
        )

        # Codex说明(自动生成)： 计算并保存 viewport，供后续语句继续读取或更新。
        viewport = self.ttk.Frame(detail, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 viewport.grid 生成或展示图形，便于观察计算结果。
        viewport.grid(row=2, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 viewport.rowconfigure 生成或展示图形，便于观察计算结果。
        viewport.rowconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 viewport.columnconfigure 生成或展示图形，便于观察计算结果。
        viewport.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 计算并保存 canvas，供后续语句继续读取或更新。
        canvas = self.tk.Canvas(viewport, bg=self.colors["panel"], highlightthickness=0)
        # Codex说明(自动生成)： 计算并保存 y_scroll，供后续语句继续读取或更新。
        y_scroll = self.ttk.Scrollbar(viewport, orient="vertical", command=canvas.yview)
        # Codex说明(自动生成)： 计算并保存 x_scroll，供后续语句继续读取或更新。
        x_scroll = self.ttk.Scrollbar(viewport, orient="horizontal", command=canvas.xview)
        # Codex说明(自动生成)： 调用 canvas.configure 生成或展示图形，便于观察计算结果。
        canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        # Codex说明(自动生成)： 调用 canvas.grid 生成或展示图形，便于观察计算结果。
        canvas.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 y_scroll.grid 生成或展示图形，便于观察计算结果。
        y_scroll.grid(row=0, column=1, sticky="ns")
        # Codex说明(自动生成)： 调用 x_scroll.grid 生成或展示图形，便于观察计算结果。
        x_scroll.grid(row=1, column=0, sticky="ew")
        # Codex说明(自动生成)： 计算并保存 matrix，供后续语句继续读取或更新。
        matrix = self.ttk.Frame(canvas, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 window_id，供后续语句继续读取或更新。
        window_id = canvas.create_window((0, 0), window=matrix, anchor="nw")
        # Codex说明(自动生成)： 计算并保存 columns，供后续语句继续读取或更新。
        columns = min(port_count, 2)
        # Codex说明(自动生成)： 计算并保存 options，供后续语句继续读取或更新。
        options = self._datasheet_source_options()
        # Codex说明(自动生成)： 遍历 enumerate(network['mappings'].items()) 中的 (ordinal, (parameter, variable))，逐项执行循环体逻辑。
        for ordinal, (parameter, variable) in enumerate(network["mappings"].items()):
            # Codex说明(自动生成)： 计算并保存 cell，供后续语句继续读取或更新。
            cell = self.ttk.Frame(matrix, style="Alt.TFrame", padding=(8, 7))
            # Codex说明(自动生成)： 调用 cell.grid 生成或展示图形，便于观察计算结果。
            cell.grid(row=ordinal // columns, column=ordinal % columns, sticky="nsew", padx=3, pady=3)
            # Codex说明(自动生成)： 调用 matrix.columnconfigure 生成或展示图形，便于观察计算结果。
            matrix.columnconfigure(ordinal % columns, weight=1)
            # Codex说明(自动生成)： 调用 self.ttk.Label(cell, text=parameter, style='Alt.TLabel'....grid 生成或展示图形，便于观察计算结果。
            self.ttk.Label(
                cell,
                text=parameter,
                style="Alt.TLabel",
                foreground=self.colors["accent"],
                font=("Helvetica", 11, "bold"),
            ).grid(row=0, column=0, sticky="w")
            # Codex说明(自动生成)： 调用 self.ttk.Combobox(cell, textvariable=variable, values=o....grid 生成或展示图形，便于观察计算结果。
            self.ttk.Combobox(
                cell,
                textvariable=variable,
                values=options,
                state="readonly",
                width=16,
            ).grid(row=1, column=0, sticky="ew", pady=(5, 0))
        # Codex说明(自动生成)： 调用 matrix.bind，执行当前流程需要的具体操作或副作用。
        matrix.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        # Codex说明(自动生成)： 调用 canvas.bind，执行当前流程需要的具体操作或副作用。
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )
        # Codex说明(自动生成)： 调用 self.datasheet['selected_network_summary'].set，执行当前流程需要的具体操作或副作用。
        self.datasheet["selected_network_summary"].set(
            f"网络 {self.datasheet_selected_network + 1} · {port_count} 端口 · {port_count * port_count} 个 Sij"
        )

    # Codex说明(自动生成)： 定义函数 _check_datasheet_mappings，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _check_datasheet_mappings(self) -> None:
        # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
        values = [
            variable.get()
            for network in self.datasheet_networks
            for variable in network["mappings"].values()
        ]
        # Codex说明(自动生成)： 计算并保存 default_count，供后续语句继续读取或更新。
        default_count = sum(value.startswith("默认") for value in values)
        # Codex说明(自动生成)： 计算并保存 pending_count，供后续语句继续读取或更新。
        pending_count = sum(
            value in {"自动", "未知"} or value.startswith("图")
            for value in values
        )
        # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
        self.datasheet["status"].set(f"默认 {default_count} · 待定 {pending_count}")

    # Codex说明(自动生成)： 定义函数 _datasheet_panel，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _datasheet_panel(self, parent, title: str, *, padding=14):
        # Codex说明(自动生成)： 计算并保存 panel，供后续语句继续读取或更新。
        panel = self.ttk.Frame(parent, style="Card.TFrame", padding=padding)
        # Codex说明(自动生成)： 调用 panel.columnconfigure 生成或展示图形，便于观察计算结果。
        panel.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 self.ttk.Label(panel, text=title, font=('Helvetica', 12....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(panel, text=title, font=("Helvetica", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        # Codex说明(自动生成)： 返回 panel，让调用方取得本函数的处理结果。
        return panel


    # Codex说明(自动生成)： 定义函数 _create_datasheet_preview，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _create_datasheet_preview(self, parent, *, row: int, width: int, height: int) -> None:
        # Codex说明(自动生成)： 计算并保存 canvas，供后续语句继续读取或更新。
        canvas = self.tk.Canvas(
            parent,
            width=width,
            height=height,
            bg="#f1f2f3",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        # Codex说明(自动生成)： 调用 canvas.grid 生成或展示图形，便于观察计算结果。
        canvas.grid(row=row, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 canvas.preview_width，供后续语句继续读取或更新。
        canvas.preview_width = width
        # Codex说明(自动生成)： 计算并保存 canvas.preview_height，供后续语句继续读取或更新。
        canvas.preview_height = height
        # Codex说明(自动生成)： 调用 self.datasheet_preview_canvases.append 更新列表或集合，把当前步骤产生的数据加入结果。
        self.datasheet_preview_canvases.append(canvas)
        # Codex说明(自动生成)： 调用 self._draw_datasheet_placeholder，执行当前流程需要的具体操作或副作用。
        self._draw_datasheet_placeholder(canvas)

    # Codex说明(自动生成)： 定义函数 _draw_datasheet_placeholder，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _draw_datasheet_placeholder(self, canvas) -> None:
        """Draw a deterministic engineering-chart placeholder without image dependencies."""

        # Codex说明(自动生成)： 检查条件 hasattr(canvas, 'preview_photo')，根据结果选择后续执行路径。
        if hasattr(canvas, "preview_photo"):
            # Codex说明(自动生成)： 删除 canvas.preview_photo，释放不再需要的引用或状态。
            del canvas.preview_photo
        # Codex说明(自动生成)： 调用 canvas.delete，执行当前流程需要的具体操作或副作用。
        canvas.delete("all")
        # Codex说明(自动生成)： 计算并保存 width，供后续语句继续读取或更新。
        width = int(canvas.preview_width)
        # Codex说明(自动生成)： 计算并保存 height，供后续语句继续读取或更新。
        height = int(canvas.preview_height)
        # Codex说明(自动生成)： 计算并保存 (left, top, right, bottom)，供后续语句继续读取或更新。
        left, top, right, bottom = 55, 34, width - 24, height - 48
        # Codex说明(自动生成)： 调用 canvas.create_rectangle，执行当前流程需要的具体操作或副作用。
        canvas.create_rectangle(left, top, right, bottom, fill="#fafafa", outline="#70767b")
        # Codex说明(自动生成)： 遍历 range(1, 10) 中的 index，逐项执行循环体逻辑。
        for index in range(1, 10):
            # Codex说明(自动生成)： 计算并保存 x，供后续语句继续读取或更新。
            x = left + (right - left) * index / 10
            # Codex说明(自动生成)： 调用 canvas.create_line，执行当前流程需要的具体操作或副作用。
            canvas.create_line(x, top, x, bottom, fill="#c5c9cc")
        # Codex说明(自动生成)： 遍历 range(1, 10) 中的 index，逐项执行循环体逻辑。
        for index in range(1, 10):
            # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
            y = top + (bottom - top) * index / 10
            # Codex说明(自动生成)： 调用 canvas.create_line，执行当前流程需要的具体操作或副作用。
            canvas.create_line(left, y, right, y, fill="#c5c9cc")
        # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
        canvas.create_text(left, bottom + 22, text="0.01 GHz", anchor="w", fill="#30363a")
        # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
        canvas.create_text(right, bottom + 22, text="40 GHz", anchor="e", fill="#30363a")
        # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
        canvas.create_text(left - 8, top, text="50 dB", anchor="e", fill="#30363a")
        # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
        canvas.create_text(left - 8, bottom, text="−50 dB", anchor="e", fill="#30363a")
        # Codex说明(自动生成)： 计算并保存 x_values，供后续语句继续读取或更新。
        x_values = [left + (right - left) * index / 80 for index in range(81)]
        # Codex说明(自动生成)： 计算并保存 tx_il，供后续语句继续读取或更新。
        tx_il = [top + (bottom - top) * (0.49 + 0.045 * index / 80) for index in range(81)]
        # Codex说明(自动生成)： 计算并保存 rx_il，供后续语句继续读取或更新。
        rx_il = [top + (bottom - top) * (0.49 + 0.09 * index / 80) for index in range(81)]
        # Codex说明(自动生成)： 计算并保存 tx_rl，供后续语句继续读取或更新。
        tx_rl = [
            top + (bottom - top) * (0.66 + 0.035 * np.sin(index * 0.75) ** 2 + 0.08 * (index % 17 == 8))
            for index in range(81)
        ]
        # Codex说明(自动生成)： 计算并保存 rx_rl，供后续语句继续读取或更新。
        rx_rl = [
            top + (bottom - top) * (0.65 + 0.04 * np.sin(index * 0.68 + 0.8) ** 2 + 0.07 * (index % 19 == 5))
            for index in range(81)
        ]
        # Codex说明(自动生成)： 遍历 ((tx_il, '#355cff'), (rx_il, '#6d9ee8'), (tx_rl, '#ff4f... 中的 (values, color)，逐项执行循环体逻辑。
        for values, color in ((tx_il, "#355cff"), (rx_il, "#6d9ee8"), (tx_rl, "#ff4f4f"), (rx_rl, "#49bf63")):
            # Codex说明(自动生成)： 计算并保存 points，供后续语句继续读取或更新。
            points = [coordinate for pair in zip(x_values, values) for coordinate in pair]
            # Codex说明(自动生成)： 调用 canvas.create_line，执行当前流程需要的具体操作或副作用。
            canvas.create_line(*points, fill=color, width=2, smooth=True)
        # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
        canvas.create_text(
            (left + right) / 2,
            top + 16,
            text="示例：4 个待确认候选",
            fill="#344047",
            font=("Helvetica", 11, "bold"),
        )

    # Codex说明(自动生成)： 定义函数 _browse_datasheet_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _browse_datasheet_images(self) -> None:
        # Codex说明(自动生成)： 从 tkinter 导入 filedialog，提供本文件后续流程需要的库能力。
        from tkinter import filedialog

        # Codex说明(自动生成)： 计算并保存 paths，供后续语句继续读取或更新。
        paths = filedialog.askopenfilenames(
            title="批量导入规格书页面或曲线图片",
            filetypes=[
                ("Datasheet pages", "*.png *.gif *.jpg *.jpeg *.pdf"),
                ("All files", "*.*"),
            ],
        )
        # Codex说明(自动生成)： 检查条件 not paths，根据结果选择后续执行路径。
        if not paths:
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 计算并保存 combined，供后续语句继续读取或更新。
        combined = []
        # Codex说明(自动生成)： 遍历 (*self.datasheet_image_paths, *(Path(path) for path in ... 中的 path，逐项执行循环体逻辑。
        for path in (*self.datasheet_image_paths, *(Path(path) for path in paths)):
            # Codex说明(自动生成)： 检查条件 path not in combined，根据结果选择后续执行路径。
            if path not in combined:
                # Codex说明(自动生成)： 调用 combined.append 更新列表或集合，把当前步骤产生的数据加入结果。
                combined.append(path)
        # Codex说明(自动生成)： 调用 self._load_datasheet_images，执行当前流程需要的具体操作或副作用。
        self._load_datasheet_images(combined)

    # Codex说明(自动生成)： 定义函数 _load_datasheet_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _load_datasheet_images(self, paths) -> None:
        """Register image pages and expose only decodable manual candidate slots."""

        # Codex说明(自动生成)： 计算并保存 self.datasheet_image_paths，供后续语句继续读取或更新。
        self.datasheet_image_paths = [Path(path) for path in paths]
        # Codex说明(自动生成)： 计算并保存 self.datasheet_image_path，供后续语句继续读取或更新。
        self.datasheet_image_path = self.datasheet_image_paths[0] if self.datasheet_image_paths else None
        # Codex说明(自动生成)： 检查条件 not self.datasheet_image_paths，根据结果选择后续执行路径。
        if not self.datasheet_image_paths:
            # Codex说明(自动生成)： 计算并保存 self.datasheet_image_previewable，供后续语句继续读取或更新。
            self.datasheet_image_previewable = []
            # Codex说明(自动生成)： 调用 self._invalidate_unavailable_datasheet_sources，执行当前流程需要的具体操作或副作用。
            self._invalidate_unavailable_datasheet_sources()
            # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
            self.datasheet["status"].set("未生成")
            # Codex说明(自动生成)： 遍历 self.datasheet_preview_canvases 中的 canvas，逐项执行循环体逻辑。
            for canvas in self.datasheet_preview_canvases:
                # Codex说明(自动生成)： 调用 self._draw_datasheet_placeholder，执行当前流程需要的具体操作或副作用。
                self._draw_datasheet_placeholder(canvas)
            # Codex说明(自动生成)： 调用 self._rebuild_datasheet_resource_list，执行当前流程需要的具体操作或副作用。
            self._rebuild_datasheet_resource_list()
            # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
            self._rebuild_datasheet_detail()
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 计算并保存 self.datasheet_image_previewable，供后续语句继续读取或更新。
        self.datasheet_image_previewable = [
            self._can_preview_datasheet_image(path)
            for path in self.datasheet_image_paths
        ]
        # Codex说明(自动生成)： 调用 self._invalidate_unavailable_datasheet_sources，执行当前流程需要的具体操作或副作用。
        self._invalidate_unavailable_datasheet_sources()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_resource_list，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_resource_list()
        # Codex说明(自动生成)： 调用 self._rebuild_datasheet_detail，执行当前流程需要的具体操作或副作用。
        self._rebuild_datasheet_detail()
        # Codex说明(自动生成)： 计算并保存 previewable_count，供后续语句继续读取或更新。
        previewable_count = sum(self.datasheet_image_previewable)
        # Codex说明(自动生成)： 计算并保存 restricted_count，供后续语句继续读取或更新。
        restricted_count = len(self.datasheet_image_paths) - previewable_count
        # Codex说明(自动生成)： 计算并保存 candidate_count，供后续语句继续读取或更新。
        candidate_count = previewable_count * len(DATASHEET_CURVES)
        # Codex说明(自动生成)： 检查条件 previewable_count，根据结果选择后续执行路径。
        if previewable_count:
            # Codex说明(自动生成)： 计算并保存 preview_index，供后续语句继续读取或更新。
            preview_index = self.datasheet_image_previewable.index(True)
            # Codex说明(自动生成)： 调用 self._show_datasheet_image 生成或展示图形，便于观察计算结果。
            self._show_datasheet_image(preview_index)
            # Codex说明(自动生成)： 计算并保存 status，供后续语句继续读取或更新。
            status = f"{len(self.datasheet_image_paths)} 图 · {candidate_count} 候选"
            # Codex说明(自动生成)： 检查条件 restricted_count，根据结果选择后续执行路径。
            if restricted_count:
                # Codex说明(自动生成)： 基于旧值更新 status，累积当前循环或处理步骤的结果。
                status += f" · {restricted_count} 受限"
            # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
            self.datasheet["status"].set(status)
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 调用 self._show_datasheet_image 生成或展示图形，便于观察计算结果。
            self._show_datasheet_image(0)
            # Codex说明(自动生成)： 调用 self.datasheet['status'].set，执行当前流程需要的具体操作或副作用。
            self.datasheet["status"].set(
                f"{len(self.datasheet_image_paths)} 文件 · 预览受限"
            )

    # Codex说明(自动生成)： 定义函数 _show_datasheet_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _show_datasheet_image(self, index: int) -> bool:
        # Codex说明(自动生成)： 检查条件 index < 0 or index >= len(self.datasheet_image_paths)，根据结果选择后续执行路径。
        if index < 0 or index >= len(self.datasheet_image_paths):
            # Codex说明(自动生成)： 抛出 IndexError(f'Datasheet image index out of range: {index}')，明确提示输入、状态或处理流程无法继续。
            raise IndexError(f"Datasheet image index out of range: {index}")
        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = self.datasheet_image_paths[index]
        # Codex说明(自动生成)： 计算并保存 self.datasheet_image_path，供后续语句继续读取或更新。
        self.datasheet_image_path = path
        # Codex说明(自动生成)： 计算并保存 shown，供后续语句继续读取或更新。
        shown = 0
        # Codex说明(自动生成)： 遍历 self.datasheet_preview_canvases 中的 canvas，逐项执行循环体逻辑。
        for canvas in self.datasheet_preview_canvases:
            # Codex说明(自动生成)： 检查条件 self._render_datasheet_image(canvas, path)，根据结果选择后续执行路径。
            if self._render_datasheet_image(canvas, path):
                # Codex说明(自动生成)： 基于旧值更新 shown，累积当前循环或处理步骤的结果。
                shown += 1
        # Codex说明(自动生成)： 返回 shown > 0，让调用方取得本函数的处理结果。
        return shown > 0

    # Codex说明(自动生成)： 定义函数 _can_preview_datasheet_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _can_preview_datasheet_image(self, path: Path) -> bool:
        """Return whether Tk can decode the file; decoding is not curve recognition."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 self.tk.PhotoImage，执行当前流程需要的具体操作或副作用。
            self.tk.PhotoImage(file=str(path))
        # Codex说明(自动生成)： 捕获 self.tk.TclError，执行对应的恢复、记录或重新报错逻辑。
        except self.tk.TclError:
            # Codex说明(自动生成)： 返回 False，让调用方取得本函数的处理结果。
            return False
        # Codex说明(自动生成)： 返回 True，让调用方取得本函数的处理结果。
        return True

    # Codex说明(自动生成)： 定义函数 _render_datasheet_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _render_datasheet_image(self, canvas, path: Path) -> bool:
        """Render a PNG/GIF on one canvas and retain its Tk image reference."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
            source = self.tk.PhotoImage(file=str(path))
        # Codex说明(自动生成)： 捕获 self.tk.TclError，执行对应的恢复、记录或重新报错逻辑。
        except self.tk.TclError:
            # Codex说明(自动生成)： 调用 self._draw_datasheet_placeholder，执行当前流程需要的具体操作或副作用。
            self._draw_datasheet_placeholder(canvas)
            # Codex说明(自动生成)： 调用 canvas.create_text，执行当前流程需要的具体操作或副作用。
            canvas.create_text(
                canvas.preview_width / 2,
                canvas.preview_height - 18,
                text="无法预览",
                fill="#8b3d21",
            )
            # Codex说明(自动生成)： 返回 False，让调用方取得本函数的处理结果。
            return False
        # Codex说明(自动生成)： 计算并保存 factor，供后续语句继续读取或更新。
        factor = max(
            1,
            int(np.ceil(source.width() / max(1, canvas.preview_width - 20))),
            int(np.ceil(source.height() / max(1, canvas.preview_height - 20))),
        )
        # Codex说明(自动生成)： 计算并保存 photo，供后续语句继续读取或更新。
        photo = source.subsample(factor, factor)
        # Codex说明(自动生成)： 调用 canvas.delete，执行当前流程需要的具体操作或副作用。
        canvas.delete("all")
        # Codex说明(自动生成)： 调用 canvas.create_image，执行当前流程需要的具体操作或副作用。
        canvas.create_image(
            canvas.preview_width / 2,
            canvas.preview_height / 2,
            image=photo,
            anchor="center",
        )
        # Codex说明(自动生成)： 计算并保存 canvas.preview_photo，供后续语句继续读取或更新。
        canvas.preview_photo = photo
        # Codex说明(自动生成)： 返回 True，让调用方取得本函数的处理结果。
        return True

    # Codex说明(自动生成)： 定义函数 _build_scrollable_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_scrollable_controls(self, parent):
        """Create a vertically scrollable left control rail.

        The mode-specific controls are intentionally dense, and on a laptop
        screen the lower rows can otherwise fall below the visible window. A
        canvas-backed scroll region keeps the top Run button fixed while making
        every parameter reachable without requiring the user to maximize.
        """

        # Codex说明(自动生成)： 计算并保存 shell，供后续语句继续读取或更新。
        shell = self.ttk.Frame(parent, style="Card.TFrame")
        # Codex说明(自动生成)： 调用 shell.grid 生成或展示图形，便于观察计算结果。
        shell.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        # Codex说明(自动生成)： 调用 shell.rowconfigure 生成或展示图形，便于观察计算结果。
        shell.rowconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 shell.columnconfigure 生成或展示图形，便于观察计算结果。
        shell.columnconfigure(0, weight=1)

        # Codex说明(自动生成)： 计算并保存 canvas，供后续语句继续读取或更新。
        canvas = self.tk.Canvas(
            shell,
            width=360,
            bg=self.colors["panel"],
            highlightthickness=0,
            bd=0,
        )
        # Codex说明(自动生成)： 计算并保存 scrollbar，供后续语句继续读取或更新。
        scrollbar = self.ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        # Codex说明(自动生成)： 调用 canvas.configure 生成或展示图形，便于观察计算结果。
        canvas.configure(yscrollcommand=scrollbar.set)
        # Codex说明(自动生成)： 调用 canvas.grid 生成或展示图形，便于观察计算结果。
        canvas.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 scrollbar.grid 生成或展示图形，便于观察计算结果。
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
        controls = self.ttk.Frame(canvas, style="Panel.TFrame", padding=16)
        # Codex说明(自动生成)： 计算并保存 window_id，供后续语句继续读取或更新。
        window_id = canvas.create_window((0, 0), window=controls, anchor="nw")

        # Codex说明(自动生成)： 定义函数 update_scroll_region，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def update_scroll_region(_event=None) -> None:
            # Codex说明(自动生成)： 调用 canvas.configure 生成或展示图形，便于观察计算结果。
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Codex说明(自动生成)： 定义函数 sync_inner_width，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def sync_inner_width(event) -> None:
            # Codex说明(自动生成)： 调用 canvas.itemconfigure 生成或展示图形，便于观察计算结果。
            canvas.itemconfigure(window_id, width=event.width)

        # Codex说明(自动生成)： 定义函数 on_mousewheel，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def on_mousewheel(event) -> None:
            # Codex说明(自动生成)： 检查条件 event.delta，根据结果选择后续执行路径。
            if event.delta:
                # Codex说明(自动生成)： 计算并保存 units，供后续语句继续读取或更新。
                units = -1 if event.delta > 0 else 1
                # Codex说明(自动生成)： 调用 canvas.yview_scroll，执行当前流程需要的具体操作或副作用。
                canvas.yview_scroll(units * 3, "units")

        # Codex说明(自动生成)： 调用 controls.bind，执行当前流程需要的具体操作或副作用。
        controls.bind("<Configure>", update_scroll_region)
        # Codex说明(自动生成)： 调用 canvas.bind，执行当前流程需要的具体操作或副作用。
        canvas.bind("<Configure>", sync_inner_width)
        # Codex说明(自动生成)： 调用 canvas.bind，执行当前流程需要的具体操作或副作用。
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        # Codex说明(自动生成)： 调用 canvas.bind，执行当前流程需要的具体操作或副作用。
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        # Codex说明(自动生成)： 计算并保存 self.controls_canvas，供后续语句继续读取或更新。
        self.controls_canvas = canvas
        # Codex说明(自动生成)： 返回 controls，让调用方取得本函数的处理结果。
        return controls

    # Codex说明(自动生成)： 定义函数 _build_common_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_common_controls(self, parent) -> None:
        """Create shared sweep and output controls plus the mode stack."""

        # Codex说明(自动生成)： 计算并保存 ttk，供后续语句继续读取或更新。
        ttk = self.ttk
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = 0
        # Codex说明(自动生成)： 调用 ttk.Label(parent, text='扫频', font=('Helvetica', 12, 'bo....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(parent, text="扫频", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(
            parent,
            row,
            "端口",
            self.common["ports"],
            [str(value) for value in COMMON_PORT_COUNTS],
        )
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "起始频率", self.common["f_start"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "终止频率", self.common["f_stop"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "点数", self.common["points"], width=8)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(parent, row, "间隔", self.common["spacing"], ["linear", "log"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(parent, row, "格式", self.common["format"], ["ri", "ma", "db"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(
            parent,
            row,
            "频率单位",
            self.common["frequency_unit"],
            ["hz", "khz", "mhz", "ghz"],
        )
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "回波损耗 (dB)", self.common["return_loss_db"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "串扰 (dB)", self.common["crosstalk_db"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "延迟 (ps)", self.common["delay_ps"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "相位 (deg)", self.common["phase_offset_deg"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "阻抗 (Ω)", self.common["z0"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(parent, row, "直通路径", self.common["through_pairs"])

        # Codex说明(自动生成)： 调用 ttk.Label(parent, text='输出文件', font=('Helvetica', 12, '....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(parent, text="输出文件", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(16, 3)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 ttk.Label(parent, text='采样无源 · 宽带因果性未认证', style='Muted.....grid 生成或展示图形，便于观察计算结果。
        ttk.Label(
            parent,
            text="采样无源 · 宽带因果性未认证",
            style="Muted.TLabel",
            wraplength=330,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(3, 8))
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 计算并保存 output_row，供后续语句继续读取或更新。
        output_row = ttk.Frame(parent, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 output_row.grid 生成或展示图形，便于观察计算结果。
        output_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)
        # Codex说明(自动生成)： 调用 output_row.columnconfigure 生成或展示图形，便于观察计算结果。
        output_row.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = ttk.Entry(output_row, textvariable=self.common["output"], width=28)
        # Codex说明(自动生成)： 调用 output.grid 生成或展示图形，便于观察计算结果。
        output.grid(row=0, column=0, sticky="ew")
        # Codex说明(自动生成)： 调用 ttk.Button(output_row, text='选择', style='Secondary.TBut....grid 生成或展示图形，便于观察计算结果。
        ttk.Button(output_row, text="选择", style="Secondary.TButton", command=self._browse_output).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1

        # Codex说明(自动生成)： 计算并保存 self.mode_stack，供后续语句继续读取或更新。
        self.mode_stack = ttk.Frame(parent, style="Panel.TFrame")
        # Codex说明(自动生成)： 调用 self.mode_stack.grid 生成或展示图形，便于观察计算结果。
        self.mode_stack.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        # Codex说明(自动生成)： 调用 self.mode_stack.columnconfigure 生成或展示图形，便于观察计算结果。
        self.mode_stack.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 计算并保存 self.mode_frames，供后续语句继续读取或更新。
        self.mode_frames = {}
        # Codex说明(自动生成)： 调用 self._build_linear_controls，执行当前流程需要的具体操作或副作用。
        self._build_linear_controls()
        # Codex说明(自动生成)： 调用 self._build_formula_controls，执行当前流程需要的具体操作或副作用。
        self._build_formula_controls()
        # Codex说明(自动生成)： 调用 self._build_draw_controls，执行当前流程需要的具体操作或副作用。
        self._build_draw_controls()
        # Codex说明(自动生成)： 调用 self._build_modify_controls，执行当前流程需要的具体操作或副作用。
        self._build_modify_controls()

        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(parent)

    # Codex说明(自动生成)： 定义函数 _build_linear_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_linear_controls(self) -> None:
        # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
        frame = self.ttk.Frame(self.mode_stack, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.mode_frames['linear']，供后续语句继续读取或更新。
        self.mode_frames["linear"] = frame
        # Codex说明(自动生成)： 调用 frame.grid 生成或展示图形，便于观察计算结果。
        frame.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = 0
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='线性插损', font=('Helvetica', 1....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="线性插损", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 self._field，执行当前流程需要的具体操作或副作用。
        self._field(frame, row, "起始插损 (dB)", self.linear["loss_start_db"], width=10)
        # Codex说明(自动生成)： 调用 self._field，执行当前流程需要的具体操作或副作用。
        self._field(frame, row + 1, "终止插损 (dB)", self.linear["loss_stop_db"], width=10)

    # Codex说明(自动生成)： 定义函数 _build_formula_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_formula_controls(self) -> None:
        # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
        frame = self.ttk.Frame(self.mode_stack, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.mode_frames['formula']，供后续语句继续读取或更新。
        self.mode_frames["formula"] = frame
        # Codex说明(自动生成)： 调用 frame.grid 生成或展示图形，便于观察计算结果。
        frame.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = 0
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='协议公式', font=('Helvetica', 1....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="协议公式", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='Loss = a·f + b·√f + c', sty....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(
            frame,
            text="Loss = a·f + b·√f + c",
            style="Muted.TLabel",
            wraplength=330,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 5))
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "a (dB/unit)", self.formula["a"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "b (dB/sqrt unit)", self.formula["b"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "c (dB)", self.formula["c"], width=10)
        # Codex说明(自动生成)： 调用 self._choice，执行当前流程需要的具体操作或副作用。
        self._choice(
            frame,
            row,
            "f 单位",
            self.formula["model_frequency_unit"],
            ["hz", "khz", "mhz", "ghz"],
        )

    # Codex说明(自动生成)： 定义函数 _build_draw_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_draw_controls(self) -> None:
        # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
        frame = self.ttk.Frame(self.mode_stack, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.mode_frames['draw']，供后续语句继续读取或更新。
        self.mode_frames["draw"] = frame
        # Codex说明(自动生成)： 调用 frame.grid 生成或展示图形，便于观察计算结果。
        frame.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = 0
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='手绘曲线', font=('Helvetica', 1....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="手绘曲线", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "Y min (dB)", self.draw["loss_min_db"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "Y max (dB)", self.draw["loss_max_db"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(frame, row, "拟合", self.draw["fit"], ["smooth", "linear"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(frame, row, "拟合轴", self.draw["fit_domain"], ["linear", "log"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "最小间距", self.draw["min_spacing_fraction"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "最大斜率", self.draw["max_slope_db_per_span"], width=10)
        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(frame)
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='控制点', width=12).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="控制点", width=12).grid(
            row=row,
            column=0,
            sticky="nw",
            padx=(0, 12),
            pady=3,
        )
        # Codex说明(自动生成)： 计算并保存 self.draw_points_text，供后续语句继续读取或更新。
        self.draw_points_text = self.tk.Text(
            frame,
            height=4,
            width=24,
            bg=self.colors["field"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            highlightbackground=self.colors["line"],
            highlightcolor=self.colors["accent"],
            highlightthickness=1,
        )
        # Codex说明(自动生成)： 调用 self.draw_points_text.grid 生成或展示图形，便于观察计算结果。
        self.draw_points_text.grid(row=row, column=1, sticky="ew", pady=3)

    # Codex说明(自动生成)： 定义函数 _build_modify_controls，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_modify_controls(self) -> None:
        # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
        frame = self.ttk.Frame(self.mode_stack, style="Panel.TFrame")
        # Codex说明(自动生成)： 计算并保存 self.mode_frames['modify']，供后续语句继续读取或更新。
        self.mode_frames["modify"] = frame
        # Codex说明(自动生成)： 调用 frame.grid 生成或展示图形，便于观察计算结果。
        frame.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = 0
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='修改文件', font=('Helvetica', 1....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="修改文件", font=("Helvetica", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(frame)
        # Codex说明(自动生成)： 调用 self.ttk.Label(frame, text='输入文件', width=12).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(frame, text="输入文件", width=12).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )
        # Codex说明(自动生成)： 调用 self.ttk.Entry(frame, textvariable=self.modify['input']....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Entry(frame, textvariable=self.modify["input"], width=24).grid(
            row=row, column=1, sticky="ew", pady=3
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 self.ttk.Button(frame, text='选择文件', style='Secondary.TB....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Button(frame, text="选择文件", style="Secondary.TButton", command=self._browse_input).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 7)
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "目标点 (f:dB)", self.modify["targets"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "路径 (Sij)", self.modify["pairs"])
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._field(frame, row, "曲线张力", self.modify["smoothness"], width=10)
        # Codex说明(自动生成)： 计算并保存 row，供后续语句继续读取或更新。
        row = self._choice(frame, row, "平滑轴", self.modify["smooth_domain"], ["log", "linear"])
        # Codex说明(自动生成)： 调用 self.ttk.Checkbutton(frame, text='固定边缘', variable=self.....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Checkbutton(frame, text="固定边缘", variable=self.modify["anchor_edges"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        # Codex说明(自动生成)： 基于旧值更新 row，累积当前循环或处理步骤的结果。
        row += 1
        # Codex说明(自动生成)： 调用 self.ttk.Checkbutton(frame, text='插入目标频点', variable=sel....grid 生成或展示图形，便于观察计算结果。
        self.ttk.Checkbutton(frame, text="插入目标频点", variable=self.modify["insert_targets"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )

    # Codex说明(自动生成)： 定义函数 _build_plot_panel，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_plot_panel(self, parent) -> None:
        """Create magnitude and phase plot pages."""

        # Codex说明(自动生成)： 计算并保存 ttk，供后续语句继续读取或更新。
        ttk = self.ttk
        # Codex说明(自动生成)： 计算并保存 self.plot_notebook，供后续语句继续读取或更新。
        self.plot_notebook = ttk.Notebook(parent, style="Plot.TNotebook")
        # Codex说明(自动生成)： 调用 self.plot_notebook.grid 生成或展示图形，便于观察计算结果。
        self.plot_notebook.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 self.plot_frames，供后续语句继续读取或更新。
        self.plot_frames = {}
        # Codex说明(自动生成)： 计算并保存 self.canvas_widgets，供后续语句继续读取或更新。
        self.canvas_widgets = {}
        # Codex说明(自动生成)： 计算并保存 self.figure_canvases，供后续语句继续读取或更新。
        self.figure_canvases = {}
        # Codex说明(自动生成)： 遍历 (('magnitude', '幅度'), ('phase', '相位')) 中的 (kind, label)，逐项执行循环体逻辑。
        for kind, label in (("magnitude", "幅度"), ("phase", "相位")):
            # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
            frame = ttk.Frame(self.plot_notebook, style="Alt.TFrame")
            # Codex说明(自动生成)： 调用 frame.columnconfigure 生成或展示图形，便于观察计算结果。
            frame.columnconfigure(0, weight=1)
            # Codex说明(自动生成)： 调用 frame.rowconfigure 生成或展示图形，便于观察计算结果。
            frame.rowconfigure(0, weight=1)
            # Codex说明(自动生成)： 调用 self.plot_notebook.add 生成或展示图形，便于观察计算结果。
            self.plot_notebook.add(frame, text=label)
            # Codex说明(自动生成)： 计算并保存 self.plot_frames[kind]，供后续语句继续读取或更新。
            self.plot_frames[kind] = frame
            # Codex说明(自动生成)： 计算并保存 self.canvas_widgets[kind]，供后续语句继续读取或更新。
            self.canvas_widgets[kind] = None

    # Codex说明(自动生成)： 定义函数 _field，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _field(self, parent, row: int, label: str, variable, *, width: int = 18) -> int:
        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(parent)
        # Codex说明(自动生成)： 调用 self.ttk.Label(parent, text=label, width=18).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(parent, text=label, width=18).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )
        # Codex说明(自动生成)： 调用 self.ttk.Entry(parent, textvariable=variable, width=width).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Entry(parent, textvariable=variable, width=width).grid(
            row=row, column=1, sticky="ew", pady=3
        )
        # Codex说明(自动生成)： 返回 row + 1，让调用方取得本函数的处理结果。
        return row + 1

    # Codex说明(自动生成)： 定义函数 _combo，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _combo(self, parent, row: int, label: str, variable, values: list[str]) -> int:
        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(parent)
        # Codex说明(自动生成)： 调用 self.ttk.Label(parent, text=label, width=18).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(parent, text=label, width=18).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )
        # Codex说明(自动生成)： 计算并保存 combo，供后续语句继续读取或更新。
        combo = self.ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=14)
        # Codex说明(自动生成)： 调用 combo.grid 生成或展示图形，便于观察计算结果。
        combo.grid(row=row, column=1, sticky="ew", pady=3)
        # Codex说明(自动生成)： 返回 row + 1，让调用方取得本函数的处理结果。
        return row + 1

    # Codex说明(自动生成)： 定义函数 _choice，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _choice(
        self,
        parent,
        row: int,
        label: str,
        variable,
        values: list[str],
    ) -> int:
        """Use stable segmented choices with explicit colors on every platform."""

        # Codex说明(自动生成)： 调用 self._configure_form_columns 生成或展示图形，便于观察计算结果。
        self._configure_form_columns(parent)
        # Codex说明(自动生成)： 调用 self.ttk.Label(parent, text=label, width=18).grid 生成或展示图形，便于观察计算结果。
        self.ttk.Label(parent, text=label, width=18).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )
        # Codex说明(自动生成)： 计算并保存 frame，供后续语句继续读取或更新。
        frame = self.tk.Frame(parent, bg=self.colors["panel"])
        # Codex说明(自动生成)： 调用 frame.grid 生成或展示图形，便于观察计算结果。
        frame.grid(row=row, column=1, sticky="ew", pady=3)
        # Codex说明(自动生成)： 遍历 range(len(values)) 中的 col，逐项执行循环体逻辑。
        for col in range(len(values)):
            # Codex说明(自动生成)： 调用 frame.columnconfigure 生成或展示图形，便于观察计算结果。
            frame.columnconfigure(col, weight=1)
        # Codex说明(自动生成)： 计算并保存 buttons，供后续语句继续读取或更新。
        buttons = []

        # Codex说明(自动生成)： 定义函数 set_value，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
        def set_value(value: str) -> None:
            # Codex说明(自动生成)： 调用 variable.set，执行当前流程需要的具体操作或副作用。
            variable.set(value)
            # Codex说明(自动生成)： 遍历 buttons 中的 (button, button_value)，逐项执行循环体逻辑。
            for button, button_value in buttons:
                # Codex说明(自动生成)： 计算并保存 selected，供后续语句继续读取或更新。
                selected = button_value == variable.get()
                # Codex说明(自动生成)： 调用 button.configure 生成或展示图形，便于观察计算结果。
                button.configure(
                    bg=self.colors["accent"] if selected else self.colors["panel_alt"],
                    fg="#17182A" if selected else self.colors["text"],
                )

        # Codex说明(自动生成)： 遍历 enumerate(values) 中的 (col, value)，逐项执行循环体逻辑。
        for col, value in enumerate(values):
            # Codex说明(自动生成)： 计算并保存 button，供后续语句继续读取或更新。
            button = self.tk.Label(
                frame,
                text=value.upper() if len(value) <= 3 else value,
                relief="flat",
                bd=0,
                padx=8,
                pady=7,
                highlightthickness=1,
                highlightbackground=self.colors["line"],
                font=("Helvetica", 10),
                cursor="hand2",
            )
            # Codex说明(自动生成)： 调用 button.grid 生成或展示图形，便于观察计算结果。
            button.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 3, 0))
            # Codex说明(自动生成)： 调用 button.bind，执行当前流程需要的具体操作或副作用。
            button.bind("<Button-1>", lambda _event, selected=value: set_value(selected))
            # Codex说明(自动生成)： 调用 buttons.append 更新列表或集合，把当前步骤产生的数据加入结果。
            buttons.append((button, value))
        # Codex说明(自动生成)： 调用 set_value，执行当前流程需要的具体操作或副作用。
        set_value(variable.get())
        # Codex说明(自动生成)： 返回 row + 1，让调用方取得本函数的处理结果。
        return row + 1

    # Codex说明(自动生成)： 定义函数 _configure_form_columns，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _configure_form_columns(self, parent) -> None:
        """Keep left labels readable while letting inputs absorb extra width."""

        # Codex说明(自动生成)： 调用 parent.columnconfigure 生成或展示图形，便于观察计算结果。
        parent.columnconfigure(0, minsize=160, weight=0)
        # Codex说明(自动生成)： 调用 parent.columnconfigure 生成或展示图形，便于观察计算结果。
        parent.columnconfigure(1, weight=1)

    # Codex说明(自动生成)： 定义函数 _select_mode，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _select_mode(self, mode: str) -> None:
        """Raise the selected mode controls and refresh default output."""

        # Codex说明(自动生成)： 调用 self.mode_var.set，执行当前流程需要的具体操作或副作用。
        self.mode_var.set(mode)
        # Codex说明(自动生成)： 调用 self.mode_frames[mode].tkraise，执行当前流程需要的具体操作或副作用。
        self.mode_frames[mode].tkraise()
        # Codex说明(自动生成)： 遍历 self.mode_buttons.items() 中的 (button_mode, button)，逐项执行循环体逻辑。
        for button_mode, button in self.mode_buttons.items():
            # Codex说明(自动生成)： 调用 button.configure 生成或展示图形，便于观察计算结果。
            button.configure(
                style="SelectedMode.TButton" if button_mode == mode else "Mode.TButton"
            )
        # Codex说明(自动生成)： 计算并保存 current_output，供后续语句继续读取或更新。
        current_output = self.common["output"].get().strip()
        # Codex说明(自动生成)： 检查条件 not current_output or self._is_auto_output_path(current...，根据结果选择后续执行路径。
        if not current_output or self._is_auto_output_path(current_output):
            # Codex说明(自动生成)： 调用 self.common['output'].set，执行当前流程需要的具体操作或副作用。
            self.common["output"].set(
                str(self._default_output_path(self._mode_output_stem(mode), ports=self._ports_or_default()))
            )
        # Codex说明(自动生成)： 计算并保存 mode_labels，供后续语句继续读取或更新。
        mode_labels = {
            "linear": "线性",
            "formula": "协议公式",
            "draw": "手绘",
            "modify": "修改",
        }
        # Codex说明(自动生成)： 调用 self.status_var.set，执行当前流程需要的具体操作或副作用。
        self.status_var.set(f"当前：{mode_labels[mode]}")

    # Codex说明(自动生成)： 定义函数 _set_plot_kind，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _set_plot_kind(self, kind: str) -> None:
        # Codex说明(自动生成)： 调用 self.plot_kind_var.set 生成或展示图形，便于观察计算结果。
        self.plot_kind_var.set(kind)
        # Codex说明(自动生成)： 检查条件 hasattr(self, 'plot_notebook') and kind in self.plot_fr...，根据结果选择后续执行路径。
        if hasattr(self, "plot_notebook") and kind in self.plot_frames:
            # Codex说明(自动生成)： 调用 self.plot_notebook.select 生成或展示图形，便于观察计算结果。
            self.plot_notebook.select(self.plot_frames[kind])

    # Codex说明(自动生成)： 定义函数 _browse_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _browse_output(self) -> None:
        # Codex说明(自动生成)： 从 tkinter 导入 filedialog，提供本文件后续流程需要的库能力。
        from tkinter import filedialog

        # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
        ports = self._parse_ports()
        # Codex说明(自动生成)： 计算并保存 default，供后续语句继续读取或更新。
        default = self._default_output_path(self.mode_var.get(), ports=ports)
        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = filedialog.asksaveasfilename(
            title="Save Touchstone",
            initialdir=str(default.parent),
            initialfile=default.name,
            defaultextension=default.suffix,
            filetypes=[("Touchstone", "*.s2p *.s3p *.s4p *.s6p *.s8p"), ("All files", "*.*")],
        )
        # Codex说明(自动生成)： 检查条件 path，根据结果选择后续执行路径。
        if path:
            # Codex说明(自动生成)： 调用 self.common['output'].set，执行当前流程需要的具体操作或副作用。
            self.common["output"].set(path)

    # Codex说明(自动生成)： 定义函数 _browse_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _browse_input(self) -> None:
        # Codex说明(自动生成)： 从 tkinter 导入 filedialog，提供本文件后续流程需要的库能力。
        from tkinter import filedialog

        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = filedialog.askopenfilename(
            title="Open Touchstone",
            filetypes=[("Touchstone", "*.s2p *.s3p *.s4p *.s6p *.s8p"), ("All files", "*.*")],
        )
        # Codex说明(自动生成)： 检查条件 path，根据结果选择后续执行路径。
        if path:
            # Codex说明(自动生成)： 调用 self.modify['input'].set，执行当前流程需要的具体操作或副作用。
            self.modify["input"].set(path)

    # Codex说明(自动生成)： 定义函数 generate，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def generate(self) -> None:
        """Generate or modify a network, write it to disk, and refresh plots."""

        # Codex说明(自动生成)： 从 tkinter 导入 messagebox，提供本文件后续流程需要的库能力。
        from tkinter import messagebox

        # Codex说明(自动生成)： 调用 self.root.configure 生成或展示图形，便于观察计算结果。
        self.root.configure(cursor="watch")
        # Codex说明(自动生成)： 调用 self.root.update_idletasks，执行当前流程需要的具体操作或副作用。
        self.root.update_idletasks()
        # Codex说明(自动生成)： 调用 self.run_button.configure 生成或展示图形，便于观察计算结果。
        self.run_button.configure(state="disabled")
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 mode，供后续语句继续读取或更新。
            mode = self.mode_var.get()
            # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
            result = self._run_mode(mode)
            # Codex说明(自动生成)： 计算并保存 self.current_data，供后续语句继续读取或更新。
            self.current_data = result.data
            # Codex说明(自动生成)： 调用 self._render_plot 生成或展示图形，便于观察计算结果。
            self._render_plot(result.data)
            # Codex说明(自动生成)： 计算并保存 diagnostics，供后续语句继续读取或更新。
            diagnostics = diagnose_sampled_network(result.data)
            # Codex说明(自动生成)： 计算并保存 message，供后续语句继续读取或更新。
            message = (
                f"Wrote {result.output_path} | sampled passivity "
                f"sigma_max={diagnostics.maximum_singular_value:.6f}"
            )
            # Codex说明(自动生成)： 检查条件 result.report_path is not None，根据结果选择后续执行路径。
            if result.report_path is not None:
                # Codex说明(自动生成)： 基于旧值更新 message，累积当前循环或处理步骤的结果。
                message += f" | report {result.report_path}"
            # Codex说明(自动生成)： 调用 self.status_var.set，执行当前流程需要的具体操作或副作用。
            self.status_var.set(message)
        # Codex说明(自动生成)： 捕获 _OperationCancelled，执行对应的恢复、记录或重新报错逻辑。
        except _OperationCancelled as exc:  # pragma: no cover - GUI boundary
            # Codex说明(自动生成)： 调用 self.status_var.set，执行当前流程需要的具体操作或副作用。
            self.status_var.set(str(exc))
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception as exc:  # pragma: no cover - GUI boundary
            # Codex说明(自动生成)： 调用 self.status_var.set，执行当前流程需要的具体操作或副作用。
            self.status_var.set(f"Error: {exc}")
            # Codex说明(自动生成)： 调用 messagebox.showerror 生成或展示图形，便于观察计算结果。
            messagebox.showerror(
                APP_NAME,
                f"Could not complete the operation.\n\n{exc}\n\n"
                "Check the highlighted mode values and output path, then try again.",
                parent=self.root,
            )
        # Codex说明(自动生成)： 无论前面是否出错，都执行这里的资源释放或收尾逻辑。
        finally:
            # Codex说明(自动生成)： 调用 self.run_button.configure 生成或展示图形，便于观察计算结果。
            self.run_button.configure(state="normal")
            # Codex说明(自动生成)： 调用 self.root.configure 生成或展示图形，便于观察计算结果。
            self.root.configure(cursor="")

    # Codex说明(自动生成)： 定义函数 _run_mode，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_mode(self, mode: str) -> GeneratedResult:
        """Dispatch the selected mode to the shared computational backend."""

        # Codex说明(自动生成)： 检查条件 mode == 'linear'，根据结果选择后续执行路径。
        if mode == "linear":
            # Codex说明(自动生成)： 返回 self._run_linear()，让调用方取得本函数的处理结果。
            return self._run_linear()
        # Codex说明(自动生成)： 检查条件 mode == 'formula'，根据结果选择后续执行路径。
        if mode == "formula":
            # Codex说明(自动生成)： 返回 self._run_formula()，让调用方取得本函数的处理结果。
            return self._run_formula()
        # Codex说明(自动生成)： 检查条件 mode == 'draw'，根据结果选择后续执行路径。
        if mode == "draw":
            # Codex说明(自动生成)： 返回 self._run_draw()，让调用方取得本函数的处理结果。
            return self._run_draw()
        # Codex说明(自动生成)： 检查条件 mode == 'modify'，根据结果选择后续执行路径。
        if mode == "modify":
            # Codex说明(自动生成)： 返回 self._run_modify()，让调用方取得本函数的处理结果。
            return self._run_modify()
        # Codex说明(自动生成)： 抛出 ValueError(f'Unsupported mode: {mode}')，明确提示输入、状态或处理流程无法继续。
        raise ValueError(f"Unsupported mode: {mode}")

    # Codex说明(自动生成)： 定义函数 _run_linear，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_linear(self) -> GeneratedResult:
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = self._frequency_axis()
        # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
        loss_db = linear_loss(
            frequency_hz,
            float(self.linear["loss_start_db"].get()),
            float(self.linear["loss_stop_db"].get()),
        )
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = self._build_generated_network(frequency_hz, loss_db)
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = self._resolved_output_path("linear", data.n_ports)
        # Codex说明(自动生成)： 调用 self._write_network，执行当前流程需要的具体操作或副作用。
        self._write_network(data, output)
        # Codex说明(自动生成)： 返回 GeneratedResult(data=data, output_path=output)，让调用方取得本函数的处理结果。
        return GeneratedResult(data=data, output_path=output)

    # Codex说明(自动生成)： 定义函数 _run_formula，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_formula(self) -> GeneratedResult:
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = self._frequency_axis()
        # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
        loss_db = protocol_loss(
            frequency_hz,
            a=float(self.formula["a"].get()),
            b=float(self.formula["b"].get()),
            c=float(self.formula["c"].get()),
            model_frequency_unit=self.formula["model_frequency_unit"].get(),
        )
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = self._build_generated_network(frequency_hz, loss_db)
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = self._resolved_output_path("formula", data.n_ports)
        # Codex说明(自动生成)： 调用 self._write_network，执行当前流程需要的具体操作或副作用。
        self._write_network(data, output)
        # Codex说明(自动生成)： 返回 GeneratedResult(data=data, output_path=output)，让调用方取得本函数的处理结果。
        return GeneratedResult(data=data, output_path=output)

    # Codex说明(自动生成)： 定义函数 _run_draw，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_draw(self) -> GeneratedResult:
        # Codex说明(自动生成)： 计算并保存 start_hz，供后续语句继续读取或更新。
        start_hz = parse_frequency(self.common["f_start"].get())
        # Codex说明(自动生成)： 计算并保存 stop_hz，供后续语句继续读取或更新。
        stop_hz = parse_frequency(self.common["f_stop"].get())
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = self._frequency_axis()
        # Codex说明(自动生成)： 计算并保存 point_text，供后续语句继续读取或更新。
        point_text = self.draw_points_text.get("1.0", "end").strip()
        # Codex说明(自动生成)： 检查条件 point_text，根据结果选择后续执行路径。
        if point_text:
            # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
            control_points = parse_draw_points(_split_text_values(point_text))
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
            control_points = draw_loss_points_interactive(
                start_hz,
                stop_hz,
                loss_min_db=float(self.draw["loss_min_db"].get()),
                loss_max_db=float(self.draw["loss_max_db"].get()),
                frequency_unit=self.common["frequency_unit"].get(),
                title=APP_NAME,
                fit_method=self.draw["fit"].get(),
                fit_domain=self.draw["fit_domain"].get(),
                min_spacing_fraction=float(self.draw["min_spacing_fraction"].get()),
                max_slope_db_per_span=float(self.draw["max_slope_db_per_span"].get()),
            )
        # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
        frequency_hz = insert_draw_control_frequencies(frequency_hz, control_points)
        # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
        loss_db = interpolate_drawn_loss(
            frequency_hz,
            control_points,
            method=self.draw["fit"].get(),
            fit_domain=self.draw["fit_domain"].get(),
            min_spacing_fraction=float(self.draw["min_spacing_fraction"].get()),
            max_slope_db_per_span=float(self.draw["max_slope_db_per_span"].get()),
        )
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = self._build_generated_network(frequency_hz, loss_db)
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = self._resolved_output_path("draw", data.n_ports)
        # Codex说明(自动生成)： 调用 self._write_network，执行当前流程需要的具体操作或副作用。
        self._write_network(data, output)
        # Codex说明(自动生成)： 返回 GeneratedResult(data=data, output_path=output)，让调用方取得本函数的处理结果。
        return GeneratedResult(data=data, output_path=output)

    # Codex说明(自动生成)： 定义函数 _run_modify，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_modify(self) -> GeneratedResult:
        # Codex说明(自动生成)： 计算并保存 input_path，供后续语句继续读取或更新。
        input_path = self._project_or_absolute_path(self.modify["input"].get())
        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = read_touchstone(input_path)
        # Codex说明(自动生成)： 计算并保存 targets，供后续语句继续读取或更新。
        targets = parse_target_points(_split_text_values(self.modify["targets"].get()))
        # Codex说明(自动生成)： 计算并保存 pairs，供后续语句继续读取或更新。
        pairs = parse_pairs(_split_text_values(self.modify["pairs"].get()), source.n_ports)
        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
        result = modify_insertion_loss(
            source,
            targets,
            pairs,
            smoothness=float(self.modify["smoothness"].get()),
            smooth_domain=self.modify["smooth_domain"].get(),
            anchor_edges=bool(self.modify["anchor_edges"].get()),
            insert_targets=bool(self.modify["insert_targets"].get()),
        )
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = self._resolved_output_path("modified", source.n_ports)
        # Codex说明(自动生成)： 调用 self._write_network，执行当前流程需要的具体操作或副作用。
        self._write_network(result.data, output)
        # Codex说明(自动生成)： 计算并保存 report_path，供后续语句继续读取或更新。
        report_path = output.with_suffix(output.suffix + ".report.txt")
        # Codex说明(自动生成)： 调用 write_modification_report，执行当前流程需要的具体操作或副作用。
        write_modification_report(report_path, result.results)
        # Codex说明(自动生成)： 返回 GeneratedResult(data=result.data, output_path=output, r...，让调用方取得本函数的处理结果。
        return GeneratedResult(data=result.data, output_path=output, report_path=report_path)

    # Codex说明(自动生成)： 定义函数 _frequency_axis，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _frequency_axis(self) -> np.ndarray:
        # Codex说明(自动生成)： 返回 generate_frequency_axis(parse_frequency(self.common['f_...，让调用方取得本函数的处理结果。
        return generate_frequency_axis(
            parse_frequency(self.common["f_start"].get()),
            parse_frequency(self.common["f_stop"].get()),
            int(self.common["points"].get()),
            spacing=self.common["spacing"].get(),
        )

    # Codex说明(自动生成)： 定义函数 _build_generated_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _build_generated_network(self, frequency_hz: np.ndarray, loss_db: np.ndarray) -> TouchstoneData:
        # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
        ports = self._parse_ports()
        # Codex说明(自动生成)： 计算并保存 through_pairs_text，供后续语句继续读取或更新。
        through_pairs_text = _split_text_values(self.common["through_pairs"].get())
        # Codex说明(自动生成)： 计算并保存 through_pairs，供后续语句继续读取或更新。
        through_pairs = parse_pairs(through_pairs_text, ports) if through_pairs_text else default_through_pairs(ports)
        # Codex说明(自动生成)： 返回 build_network(frequency_hz, ports, loss_db, through_pai...，让调用方取得本函数的处理结果。
        return build_network(
            frequency_hz,
            ports,
            loss_db,
            through_pairs=through_pairs,
            return_loss_db=float(self.common["return_loss_db"].get()),
            crosstalk_db=float(self.common["crosstalk_db"].get()),
            delay_ps=float(self.common["delay_ps"].get()),
            phase_offset_deg=float(self.common["phase_offset_deg"].get()),
            z0=float(self.common["z0"].get()),
        )

    # Codex说明(自动生成)： 定义函数 _write_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _write_network(self, data: TouchstoneData, output: Path) -> None:
        # Codex说明(自动生成)： 检查条件 output.exists()，根据结果选择后续执行路径。
        if output.exists():
            # Codex说明(自动生成)： 从 tkinter 导入 messagebox，提供本文件后续流程需要的库能力。
            from tkinter import messagebox

            # Codex说明(自动生成)： 计算并保存 overwrite，供后续语句继续读取或更新。
            overwrite = messagebox.askyesno(
                APP_NAME,
                f"The output already exists:\n{output}\n\nReplace it?",
                parent=self.root,
            )
            # Codex说明(自动生成)： 检查条件 not overwrite，根据结果选择后续执行路径。
            if not overwrite:
                # Codex说明(自动生成)： 抛出 _OperationCancelled('Cancelled: existing output was not...，明确提示输入、状态或处理流程无法继续。
                raise _OperationCancelled("Cancelled: existing output was not replaced")
        # Codex说明(自动生成)： 计算并保存 diagnostics，供后续语句继续读取或更新。
        diagnostics = assert_sampled_passive(data, context="Output preflight")
        # Codex说明(自动生成)： 调用 self.status_var.set，执行当前流程需要的具体操作或副作用。
        self.status_var.set(
            f"Preflight: sampled passivity sigma_max={diagnostics.maximum_singular_value:.6f}"
        )
        # Codex说明(自动生成)： 调用 output.parent.mkdir，执行当前流程需要的具体操作或副作用。
        output.parent.mkdir(parents=True, exist_ok=True)
        # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
        write_touchstone(
            data,
            output,
            frequency_unit=self.common["frequency_unit"].get(),
            data_format=self.common["format"].get(),
        )

    # Codex说明(自动生成)： 定义函数 _render_plot，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _render_plot(self, data: TouchstoneData) -> None:
        """Render magnitude and phase Sij matrices inside the desktop window."""

        # Codex说明(自动生成)： 遍历 ('magnitude', 'phase') 中的 kind，逐项执行循环体逻辑。
        for kind in ("magnitude", "phase"):
            # Codex说明(自动生成)： 调用 self._render_plot_kind 生成或展示图形，便于观察计算结果。
            self._render_plot_kind(data, kind)

    # Codex说明(自动生成)： 定义函数 _render_plot_kind，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _render_plot_kind(self, data: TouchstoneData, kind: str) -> None:
        """Render one plot page while keeping the other page available."""

        # Codex说明(自动生成)： 从 matplotlib.backends.backend_tkagg 导入 FigureCanvasTkAgg, NavigationToolbar2Tk，绘制仿真结果和诊断图形。
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        # Codex说明(自动生成)： 从 matplotlib.figure 导入 Figure，绘制仿真结果和诊断图形。
        from matplotlib.figure import Figure

        # Codex说明(自动生成)： 定义 SParameterToolbar 类，把相关数据结构、校验规则或操作方法组织在一起。
        class SParameterToolbar(NavigationToolbar2Tk):
            """Navigation tools expected during S-parameter inspection.

            Keeping the toolbar focused avoids introducing a Save button that
            conflicts with the app's default behavior of plotting interactively
            rather than writing screenshot files behind the user's back.
            """

            # Codex说明(自动生成)： 计算并保存 toolitems，供后续语句继续读取或更新。
            toolitems = tuple(
                item
                for item in NavigationToolbar2Tk.toolitems
                if item[0] in {"Home", "Back", "Forward", "Pan", "Zoom"}
            )

        # Codex说明(自动生成)： 计算并保存 old_widget，供后续语句继续读取或更新。
        old_widget = self.canvas_widgets.get(kind)
        # Codex说明(自动生成)： 检查条件 old_widget is not None，根据结果选择后续执行路径。
        if old_widget is not None:
            # Codex说明(自动生成)： 调用 old_widget.destroy，执行当前流程需要的具体操作或副作用。
            old_widget.destroy()
            # Codex说明(自动生成)： 计算并保存 self.canvas_widgets[kind]，供后续语句继续读取或更新。
            self.canvas_widgets[kind] = None
            # Codex说明(自动生成)： 计算并保存 self.figure_canvases[kind]，供后续语句继续读取或更新。
            self.figure_canvases[kind] = None

        # Codex说明(自动生成)： 计算并保存 n_ports，供后续语句继续读取或更新。
        n_ports = data.n_ports
        # Codex说明(自动生成)： 计算并保存 fig，供后续语句继续读取或更新。
        fig = Figure(
            figsize=(2.7 * n_ports, 2.2 * n_ports),
            dpi=100,
            facecolor=self.colors["panel_alt"],
            constrained_layout=True,
        )
        # Codex说明(自动生成)： 计算并保存 axes，供后续语句继续读取或更新。
        axes = fig.subplots(n_ports, n_ports, squeeze=False, sharex=True)
        # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
        unit = self.common["frequency_unit"].get()
        # Codex说明(自动生成)： 计算并保存 scale，供后续语句继续读取或更新。
        scale = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}[unit]
        # Codex说明(自动生成)： 计算并保存 x，供后续语句继续读取或更新。
        x = data.frequency_hz / scale
        # Codex说明(自动生成)： 遍历 range(n_ports) 中的 out_port，逐项执行循环体逻辑。
        for out_port in range(n_ports):
            # Codex说明(自动生成)： 遍历 range(n_ports) 中的 in_port，逐项执行循环体逻辑。
            for in_port in range(n_ports):
                # Codex说明(自动生成)： 计算并保存 ax，供后续语句继续读取或更新。
                ax = axes[out_port][in_port]
                # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
                values = data.s[:, out_port, in_port]
                # Codex说明(自动生成)： 检查条件 kind == 'phase'，根据结果选择后续执行路径。
                if kind == "phase":
                    # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
                    y = np.rad2deg(np.unwrap(np.angle(values)))
                    # Codex说明(自动生成)： 计算并保存 ylabel，供后续语句继续读取或更新。
                    ylabel = "deg"
                # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
                else:
                    # Codex说明(自动生成)： 计算并保存 y，供后续语句继续读取或更新。
                    y = to_magnitude_db(values)
                    # Codex说明(自动生成)： 计算并保存 ylabel，供后续语句继续读取或更新。
                    ylabel = "dB"
                # Codex说明(自动生成)： 调用 ax.plot 生成或展示图形，便于观察计算结果。
                ax.plot(
                    x,
                    y,
                    color=self.colors["accent"] if kind == "magnitude" else self.colors["accent_2"],
                    linewidth=1.7,
                )
                # Codex说明(自动生成)： 调用 ax.set_title 生成或展示图形，便于观察计算结果。
                ax.set_title(f"S{out_port + 1}{in_port + 1}", color=self.colors["text"], fontsize=10)
                # Codex说明(自动生成)： 调用 ax.set_facecolor，执行当前流程需要的具体操作或副作用。
                ax.set_facecolor(self.colors["field"])
                # Codex说明(自动生成)： 调用 ax.tick_params，执行当前流程需要的具体操作或副作用。
                ax.tick_params(colors=self.colors["muted"], labelsize=8)
                # Codex说明(自动生成)： 调用 ax.grid 生成或展示图形，便于观察计算结果。
                ax.grid(True, color=self.colors["line"], alpha=0.65, linewidth=0.6)
                # Codex说明(自动生成)： 遍历 ax.spines.values() 中的 spine，逐项执行循环体逻辑。
                for spine in ax.spines.values():
                    # Codex说明(自动生成)： 调用 spine.set_color，执行当前流程需要的具体操作或副作用。
                    spine.set_color(self.colors["line"])
                # Codex说明(自动生成)： 检查条件 out_port == n_ports - 1，根据结果选择后续执行路径。
                if out_port == n_ports - 1:
                    # Codex说明(自动生成)： 调用 ax.set_xlabel 生成或展示图形，便于观察计算结果。
                    ax.set_xlabel(
                        f"Frequency ({unit.upper()}, linear scale)",
                        color=self.colors["muted"],
                        fontsize=8,
                    )
                # Codex说明(自动生成)： 检查条件 in_port == 0，根据结果选择后续执行路径。
                if in_port == 0:
                    # Codex说明(自动生成)： 调用 ax.set_ylabel 生成或展示图形，便于观察计算结果。
                    ax.set_ylabel(ylabel, color=self.colors["muted"], fontsize=8)

        # Codex说明(自动生成)： 计算并保存 shell，供后续语句继续读取或更新。
        shell = self.ttk.Frame(self.plot_frames[kind], style="Alt.TFrame")
        # Codex说明(自动生成)： 调用 shell.grid 生成或展示图形，便于观察计算结果。
        shell.grid(row=0, column=0, sticky="nsew")
        # Codex说明(自动生成)： 调用 shell.columnconfigure 生成或展示图形，便于观察计算结果。
        shell.columnconfigure(0, weight=1)
        # Codex说明(自动生成)： 调用 shell.rowconfigure 生成或展示图形，便于观察计算结果。
        shell.rowconfigure(1, weight=1)

        # Codex说明(自动生成)： 计算并保存 canvas，供后续语句继续读取或更新。
        canvas = FigureCanvasTkAgg(fig, master=shell)
        # Codex说明(自动生成)： 调用 canvas.draw，执行当前流程需要的具体操作或副作用。
        canvas.draw()
        # Codex说明(自动生成)： 计算并保存 toolbar，供后续语句继续读取或更新。
        toolbar = SParameterToolbar(canvas, shell, pack_toolbar=False)
        # Codex说明(自动生成)： 调用 self._style_plot_toolbar 生成或展示图形，便于观察计算结果。
        self._style_plot_toolbar(toolbar)
        # Codex说明(自动生成)： 调用 toolbar.update，执行当前流程需要的具体操作或副作用。
        toolbar.update()
        # Codex说明(自动生成)： 调用 toolbar.grid 生成或展示图形，便于观察计算结果。
        toolbar.grid(row=0, column=0, sticky="ew")
        # Codex说明(自动生成)： 计算并保存 widget，供后续语句继续读取或更新。
        widget = canvas.get_tk_widget()
        # Codex说明(自动生成)： 调用 widget.grid 生成或展示图形，便于观察计算结果。
        widget.grid(row=1, column=0, sticky="nsew")
        # Codex说明(自动生成)： 计算并保存 self.canvas_widgets[kind]，供后续语句继续读取或更新。
        self.canvas_widgets[kind] = shell
        # Codex说明(自动生成)： 计算并保存 self.figure_canvases[kind]，供后续语句继续读取或更新。
        self.figure_canvases[kind] = canvas

    # Codex说明(自动生成)： 定义函数 _style_plot_toolbar，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _style_plot_toolbar(self, toolbar) -> None:
        """Blend Matplotlib's native navigation toolbar into the dark app chrome."""

        # Codex说明(自动生成)： 调用 toolbar.configure 生成或展示图形，便于观察计算结果。
        toolbar.configure(background=self.colors["panel_alt"])
        # Codex说明(自动生成)： 遍历 toolbar.winfo_children() 中的 child，逐项执行循环体逻辑。
        for child in toolbar.winfo_children():
            # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
            try:
                # Codex说明(自动生成)： 调用 child.configure 生成或展示图形，便于观察计算结果。
                child.configure(
                    background=self.colors["panel_alt"],
                    foreground=self.colors["text"],
                    activebackground=self.colors["line"],
                    activeforeground=self.colors["text"],
                    borderwidth=0,
                    highlightthickness=0,
                )
            # Codex说明(自动生成)： 捕获 self.tk.TclError，执行对应的恢复、记录或重新报错逻辑。
            except self.tk.TclError:
                # Codex说明(自动生成)： 保留空实现位置，表示这个分支当前不需要额外动作。
                pass

    # Codex说明(自动生成)： 定义函数 _parse_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _parse_ports(self) -> int:
        # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
        ports = int(self.common["ports"].get())
        # Codex说明(自动生成)： 检查条件 ports not in COMMON_PORT_COUNTS，根据结果选择后续执行路径。
        if ports not in COMMON_PORT_COUNTS:
            # Codex说明(自动生成)： 计算并保存 choices，供后续语句继续读取或更新。
            choices = ", ".join(str(value) for value in COMMON_PORT_COUNTS)
            # Codex说明(自动生成)： 抛出 ValueError(f'Ports must be one of {choices}')，明确提示输入、状态或处理流程无法继续。
            raise ValueError(f"Ports must be one of {choices}")
        # Codex说明(自动生成)： 返回 ports，让调用方取得本函数的处理结果。
        return ports

    # Codex说明(自动生成)： 定义函数 _ports_or_default，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _ports_or_default(self) -> int:
        """Use the typed port count when valid, otherwise keep the UI responsive."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 返回 self._parse_ports()，让调用方取得本函数的处理结果。
            return self._parse_ports()
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception:
            # Codex说明(自动生成)： 返回 2，让调用方取得本函数的处理结果。
            return 2

    # Codex说明(自动生成)： 定义函数 _resolved_output_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _resolved_output_path(self, stem: str, ports: int) -> Path:
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = self.common["output"].get().strip()
        # Codex说明(自动生成)： 检查条件 text，根据结果选择后续执行路径。
        if text:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = self._project_or_absolute_path(text)
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = self._default_output_path(stem, ports=ports)
        # Codex说明(自动生成)： 计算并保存 suffix，供后续语句继续读取或更新。
        suffix = f".s{ports}p"
        # Codex说明(自动生成)： 检查条件 path.suffix.lower() != suffix，根据结果选择后续执行路径。
        if path.suffix.lower() != suffix:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = path.with_suffix(suffix)
        # Codex说明(自动生成)： 返回 path，让调用方取得本函数的处理结果。
        return path

    # Codex说明(自动生成)： 定义函数 _default_output_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _default_output_path(self, stem: str, *, ports: int | None = None) -> Path:
        # Codex说明(自动生成)： 检查条件 ports is None，根据结果选择后续执行路径。
        if ports is None:
            # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
            ports = self._parse_ports()
        # Codex说明(自动生成)： 返回 OUTPUT_DIR / f'{stem}_gui.s{ports}p'，让调用方取得本函数的处理结果。
        return OUTPUT_DIR / f"{stem}_gui.s{ports}p"

    # Codex说明(自动生成)： 定义函数 _is_auto_output_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _is_auto_output_path(self, value: str) -> bool:
        """Return true when `value` is one of this GUI's generated defaults."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = self._project_or_absolute_path(value).resolve()
        # Codex说明(自动生成)： 捕获 OSError，执行对应的恢复、记录或重新报错逻辑。
        except OSError:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = self._project_or_absolute_path(value)
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 default_parent，供后续语句继续读取或更新。
            default_parent = OUTPUT_DIR.resolve()
        # Codex说明(自动生成)： 捕获 OSError，执行对应的恢复、记录或重新报错逻辑。
        except OSError:
            # Codex说明(自动生成)： 计算并保存 default_parent，供后续语句继续读取或更新。
            default_parent = OUTPUT_DIR
        # Codex说明(自动生成)： 检查条件 path.parent != default_parent，根据结果选择后续执行路径。
        if path.parent != default_parent:
            # Codex说明(自动生成)： 返回 False，让调用方取得本函数的处理结果。
            return False
        # Codex说明(自动生成)： 计算并保存 default_names，供后续语句继续读取或更新。
        default_names = {
            self._default_output_path(stem, ports=ports).name
            for stem in ("linear", "formula", "draw", "modified")
            for ports in COMMON_PORT_COUNTS
        }
        # Codex说明(自动生成)： 返回 path.name in default_names，让调用方取得本函数的处理结果。
        return path.name in default_names

    # Codex说明(自动生成)： 定义函数 _mode_output_stem，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _mode_output_stem(mode: str) -> str:
        # Codex说明(自动生成)： 返回 'modified' if mode == 'modify' else mode，让调用方取得本函数的处理结果。
        return "modified" if mode == "modify" else mode

    # Codex说明(自动生成)： 定义函数 _project_or_absolute_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _project_or_absolute_path(self, value: str) -> Path:
        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = Path(value).expanduser()
        # Codex说明(自动生成)： 检查条件 path.is_absolute()，根据结果选择后续执行路径。
        if path.is_absolute():
            # Codex说明(自动生成)： 返回 path，让调用方取得本函数的处理结果。
            return path
        # Codex说明(自动生成)： 计算并保存 resource_path，供后续语句继续读取或更新。
        resource_path = resource_root() / path
        # Codex说明(自动生成)： 检查条件 resource_path.exists()，根据结果选择后续执行路径。
        if resource_path.exists():
            # Codex说明(自动生成)： 返回 resource_path，让调用方取得本函数的处理结果。
            return resource_path
        # Codex说明(自动生成)： 返回 Path.cwd() / path，让调用方取得本函数的处理结果。
        return Path.cwd() / path


# Codex说明(自动生成)： 定义函数 _split_text_values，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _split_text_values(text: str) -> list[str]:
    """Split comma/newline separated GUI fields into parser-ready tokens."""

    # Codex说明(自动生成)： 声明并保存 values，同时保留类型信息方便维护和静态检查。
    values: list[str] = []
    # Codex说明(自动生成)： 遍历 str(text).splitlines() 中的 line，逐项执行循环体逻辑。
    for line in str(text).splitlines():
        # Codex说明(自动生成)： 遍历 line.split(',') 中的 part，逐项执行循环体逻辑。
        for part in line.split(","):
            # Codex说明(自动生成)： 计算并保存 part，供后续语句继续读取或更新。
            part = part.strip()
            # Codex说明(自动生成)： 检查条件 part，根据结果选择后续执行路径。
            if part:
                # Codex说明(自动生成)： 调用 values.append 更新列表或集合，把当前步骤产生的数据加入结果。
                values.append(part)
    # Codex说明(自动生成)： 返回 values，让调用方取得本函数的处理结果。
    return values


# Codex说明(自动生成)： 定义函数 resource_root，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def resource_root() -> Path:
    """Return the directory that holds bundled resources such as examples/.

    In source runs this is the project root. In PyInstaller builds, `_MEIPASS`
    points at the unpacked application resources, where build scripts place the
    bundled `examples/` directory. Keeping this lookup in one place prevents
    default GUI paths from depending on the user's current working directory.
    """

    # Codex说明(自动生成)： 计算并保存 bundle_root，供后续语句继续读取或更新。
    bundle_root = getattr(sys, "_MEIPASS", None)
    # Codex说明(自动生成)： 检查条件 bundle_root，根据结果选择后续执行路径。
    if bundle_root:
        # Codex说明(自动生成)： 返回 Path(bundle_root)，让调用方取得本函数的处理结果。
        return Path(bundle_root)
    # Codex说明(自动生成)： 返回 Path(__file__).resolve().parents[2]，让调用方取得本函数的处理结果。
    return Path(__file__).resolve().parents[2]


# Codex说明(自动生成)： 定义函数 default_example_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def default_example_path() -> Path:
    """Return the packaged default S2P file used by Modify mode."""

    # Codex说明(自动生成)： 返回 resource_root() / 'examples' / 'linear_demo.s2p'，让调用方取得本函数的处理结果。
    return resource_root() / "examples" / "linear_demo.s2p"


# Codex说明(自动生成)： 定义函数 run_self_test，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_self_test(output_dir: str | Path | None = None) -> list[Path]:
    """Exercise GUI backend workflows without opening a display window.

    Packaged executables call this through `--self-test`, which proves the
    bundled Python runtime can import numpy, matplotlib-adjacent code, the
    Touchstone reader/writer, and all four generation paths.
    """

    # Import the GUI plotting stack without constructing a Tk root. This catches
    # missing PyInstaller hooks for tkinter or Matplotlib's TkAgg canvas while
    # still keeping self-test safe in headless verification environments.
    import tkinter  # noqa: F401
    # Codex说明(自动生成)： 从 matplotlib.backends.backend_tkagg 导入 FigureCanvasTkAgg, NavigationToolbar2Tk，绘制仿真结果和诊断图形。
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # noqa: F401
    # Codex说明(自动生成)： 从 matplotlib.figure 导入 Figure，绘制仿真结果和诊断图形。
    from matplotlib.figure import Figure  # noqa: F401

    # Codex说明(自动生成)： 计算并保存 out_dir，供后续语句继续读取或更新。
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ilstudio-selftest-"))
    # Codex说明(自动生成)： 调用 out_dir.mkdir，执行当前流程需要的具体操作或副作用。
    out_dir.mkdir(parents=True, exist_ok=True)
    # Codex说明(自动生成)： 声明并保存 written，同时保留类型信息方便维护和静态检查。
    written: list[Path] = []

    # Codex说明(自动生成)： 检查条件 not default_example_path().exists()，根据结果选择后续执行路径。
    if not default_example_path().exists():
        # Codex说明(自动生成)： 抛出 RuntimeError(f'default example is missing: {default_exa...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError(f"default example is missing: {default_example_path()}")

    # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
    frequency = generate_frequency_axis(1e9, 5e9, 9)
    # Codex说明(自动生成)： 计算并保存 linear_data，供后续语句继续读取或更新。
    linear_data = build_network(frequency, 2, linear_loss(frequency, 0.5, 6.0), delay_ps=25)
    # Codex说明(自动生成)： 计算并保存 linear_path，供后续语句继续读取或更新。
    linear_path = out_dir / "selftest_linear.s2p"
    # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
    write_touchstone(linear_data, linear_path)
    # Codex说明(自动生成)： 调用 written.append 更新列表或集合，把当前步骤产生的数据加入结果。
    written.append(linear_path)

    # Codex说明(自动生成)： 计算并保存 formula_frequency，供后续语句继续读取或更新。
    formula_frequency = generate_frequency_axis(1e9, 8e9, 13, spacing="log")
    # Codex说明(自动生成)： 计算并保存 formula_loss，供后续语句继续读取或更新。
    formula_loss = protocol_loss(formula_frequency, a=0.08, b=0.6, c=0.1)
    # Codex说明(自动生成)： 计算并保存 formula_data，供后续语句继续读取或更新。
    formula_data = build_network(formula_frequency, 4, formula_loss, delay_ps=40)
    # Codex说明(自动生成)： 计算并保存 formula_path，供后续语句继续读取或更新。
    formula_path = out_dir / "selftest_formula.s4p"
    # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
    write_touchstone(formula_data, formula_path)
    # Codex说明(自动生成)： 调用 written.append 更新列表或集合，把当前步骤产生的数据加入结果。
    written.append(formula_path)

    # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
    controls = parse_draw_points(["1GHz:-1.0", "2.5GHz:-4.0", "5GHz:-2.5"])
    # Codex说明(自动生成)： 计算并保存 draw_frequency，供后续语句继续读取或更新。
    draw_frequency = insert_draw_control_frequencies(frequency, controls)
    # Codex说明(自动生成)： 计算并保存 draw_loss，供后续语句继续读取或更新。
    draw_loss = interpolate_drawn_loss(draw_frequency, controls)
    # Codex说明(自动生成)： 计算并保存 draw_data，供后续语句继续读取或更新。
    draw_data = build_network(draw_frequency, 2, draw_loss)
    # Codex说明(自动生成)： 计算并保存 draw_path，供后续语句继续读取或更新。
    draw_path = out_dir / "selftest_draw.s2p"
    # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
    write_touchstone(draw_data, draw_path)
    # Codex说明(自动生成)： 计算并保存 draw_loaded，供后续语句继续读取或更新。
    draw_loaded = read_touchstone(draw_path)
    # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
    target_index = int(np.where(np.isclose(draw_loaded.frequency_hz, 2.5e9))[0][0])
    # Codex说明(自动生成)： 检查条件 abs(float(to_magnitude_db(draw_loaded.s[target_index, 1...，根据结果选择后续执行路径。
    if abs(float(to_magnitude_db(draw_loaded.s[target_index, 1, 0])) + 4.0) > 1e-6:
        # Codex说明(自动生成)： 抛出 RuntimeError('draw self-test did not preserve the -4 dB...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("draw self-test did not preserve the -4 dB control point")
    # Codex说明(自动生成)： 调用 written.append 更新列表或集合，把当前步骤产生的数据加入结果。
    written.append(draw_path)

    # Codex说明(自动生成)： 计算并保存 modified，供后续语句继续读取或更新。
    modified = modify_insertion_loss(
        linear_data,
        parse_target_points(["3GHz:2.0"]),
        parse_pairs(["S21", "S12"], 2),
        smoothness=0.18,
        insert_targets=True,
    )
    # Codex说明(自动生成)： 计算并保存 modify_path，供后续语句继续读取或更新。
    modify_path = out_dir / "selftest_modified.s2p"
    # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
    write_touchstone(modified.data, modify_path)
    # Codex说明(自动生成)： 计算并保存 report_path，供后续语句继续读取或更新。
    report_path = modify_path.with_suffix(modify_path.suffix + ".report.txt")
    # Codex说明(自动生成)： 调用 write_modification_report，执行当前流程需要的具体操作或副作用。
    write_modification_report(report_path, modified.results)
    # Codex说明(自动生成)： 调用 written.extend 更新列表或集合，把当前步骤产生的数据加入结果。
    written.extend([modify_path, report_path])

    # Codex说明(自动生成)： 计算并保存 modified_loaded，供后续语句继续读取或更新。
    modified_loaded = read_touchstone(modify_path)
    # Codex说明(自动生成)： 计算并保存 target_index，供后续语句继续读取或更新。
    target_index = int(np.where(np.isclose(modified_loaded.frequency_hz, 3e9))[0][0])
    # Codex说明(自动生成)： 遍历 ((1, 0), (0, 1)) 中的 (out_port, in_port)，逐项执行循环体逻辑。
    for out_port, in_port in ((1, 0), (0, 1)):
        # Codex说明(自动生成)： 计算并保存 achieved_loss，供后续语句继续读取或更新。
        achieved_loss = float(-to_magnitude_db(modified_loaded.s[target_index, out_port, in_port]))
        # Codex说明(自动生成)： 检查条件 abs(achieved_loss - 2.0) > 1e-06，根据结果选择后续执行路径。
        if abs(achieved_loss - 2.0) > 1e-6:
            # Codex说明(自动生成)： 抛出 RuntimeError(f'modify self-test missed target on S{out_...，明确提示输入、状态或处理流程无法继续。
            raise RuntimeError(
                f"modify self-test missed target on S{out_port + 1}{in_port + 1}: {achieved_loss}"
            )
    # Codex说明(自动生成)： 遍历 modified.results 中的 result，逐项执行循环体逻辑。
    for result in modified.results:
        # Codex说明(自动生成)： 检查条件 abs(result.phase_delta_deg) > 1e-08，根据结果选择后续执行路径。
        if abs(result.phase_delta_deg) > 1e-8:
            # Codex说明(自动生成)： 抛出 RuntimeError(f'modify self-test changed phase on {resul...，明确提示输入、状态或处理流程无法继续。
            raise RuntimeError(
                f"modify self-test changed phase on {result.pair}: {result.phase_delta_deg} deg"
            )

    # Codex说明(自动生成)： 遍历 written 中的 path，逐项执行循环体逻辑。
    for path in written:
        # Codex说明(自动生成)： 检查条件 not path.exists()，根据结果选择后续执行路径。
        if not path.exists():
            # Codex说明(自动生成)： 抛出 RuntimeError(f'self-test output missing: {path}')，明确提示输入、状态或处理流程无法继续。
            raise RuntimeError(f"self-test output missing: {path}")
        # Codex说明(自动生成)： 检查条件 path.suffix.lower() in {'.s1p', '.s2p', '.s3p', '.s4p'}，根据结果选择后续执行路径。
        if path.suffix.lower() in {".s1p", ".s2p", ".s3p", ".s4p"}:
            # Codex说明(自动生成)： 计算并保存 reread，供后续语句继续读取或更新。
            reread = read_touchstone(path)
            # Codex说明(自动生成)： 调用 assert_sampled_passive 检查测试期望，确认实际结果符合预期。
            assert_sampled_passive(reread, context=f"Self-test output {path.name}")
    # Codex说明(自动生成)： 返回 written，让调用方取得本函数的处理结果。
    return written


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main(argv: Iterable[str] | None = None) -> int:
    """Run the desktop GUI or a non-interactive packaged-app self-test."""

    # Codex说明(自动生成)： 计算并保存 parser，供后续语句继续读取或更新。
    parser = argparse.ArgumentParser(description="Launch Insertion Loss Tool.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--self-test", action="store_true", help="Run bundled backend checks and exit.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--self-test-output", help="Directory for --self-test files.")
    # Codex说明(自动生成)： 计算并保存 args，供后续语句继续读取或更新。
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Codex说明(自动生成)： 检查条件 args.self_test，根据结果选择后续执行路径。
    if args.self_test:
        # Codex说明(自动生成)： 计算并保存 written，供后续语句继续读取或更新。
        written = run_self_test(args.self_test_output)
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print("GUI self-test passed")
        # Codex说明(自动生成)： 遍历 written 中的 path，逐项执行循环体逻辑。
        for path in written:
            # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
            print(path)
        # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
        return 0

    # Codex说明(自动生成)： 导入 tkinter as tk，提供本文件后续流程需要的库能力。
    import tkinter as tk

    # Codex说明(自动生成)： 计算并保存 root，供后续语句继续读取或更新。
    root = tk.Tk()
    # Codex说明(自动生成)： 调用 InsertionLossStudio，执行当前流程需要的具体操作或副作用。
    InsertionLossStudio(root)
    # Codex说明(自动生成)： 调用 root.mainloop，执行当前流程需要的具体操作或副作用。
    root.mainloop()
    # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
    return 0
