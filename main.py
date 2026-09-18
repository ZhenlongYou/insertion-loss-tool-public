#!/usr/bin/env python3
"""Insertion-loss Touchstone tool entry point.

直接运行方式：

    python3 main.py

不用命令行参数时，脚本会读取下面“用户参数区”的全局变量。你只需要在
本文件顶部改模式、频率范围、插损目标、输入输出文件等常用参数，不需要
翻到 `src/` 里的内部函数。

命令行方式仍然保留：

    python3 main.py linear --ports 2 --loss-start-db 0.2 --loss-stop-db 20
    python3 main.py formula --ports 4 --a 0.08 --b 0.6 --c 0.1
    python3 main.py draw --ports 2 --f-start 10MHz --f-stop 40GHz
    python3 main.py modify --input measured.s2p --target 5GHz:6.5 --output tuned.s2p
"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 从 datetime 导入 datetime，提供本文件后续流程需要的库能力。
from datetime import datetime
# Codex说明(自动生成)： 导入 importlib.util，提供本文件后续流程需要的库能力。
import importlib.util
# Codex说明(自动生成)： 导入 importlib，提供本文件后续流程需要的库能力。
import importlib
# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# Codex说明(自动生成)： 导入 site，提供本文件后续流程需要的库能力。
import site
# Codex说明(自动生成)： 导入 subprocess，调用 git 或外部命令并读取返回结果。
import subprocess
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys


# =============================================================================
# 用户参数区：直接改这里，然后运行 `python3 main.py`
# =============================================================================

# 运行模式：
#   "linear"  = 生成线性插损
#   "formula" = 生成 a*f + b*sqrt(f) + c 插损
#   "draw"    = 弹出窗口手动画插损折线
#   "modify"  = 导入已有 s 参数文件，并平滑修改指定频点插损
# Codex说明(自动生成)： 计算并保存 RUN_MODE，供后续语句继续读取或更新。
RUN_MODE = "formula"

# 通用输出设置。OUTPUT_FILE 为空时，脚本会根据模式自动写到 examples/。
# Codex说明(自动生成)： 计算并保存 PORTS，供后续语句继续读取或更新。
PORTS = 2  # 支持 2、3、4、6、8，对应 s2p/s3p/s4p/s6p/s8p。
# Codex说明(自动生成)： 计算并保存 OUTPUT_FILE，供后续语句继续读取或更新。
OUTPUT_FILE = ""  # 例如 "examples/my_result.s2p"；留空自动命名。
# Codex说明(自动生成)： 计算并保存 OUTPUT_FORMAT，供后续语句继续读取或更新。
OUTPUT_FORMAT = "ri"  # "ri", "ma", "db"。
# Codex说明(自动生成)： 计算并保存 OUTPUT_FREQUENCY_UNIT，供后续语句继续读取或更新。
OUTPUT_FREQUENCY_UNIT = "ghz"  # "hz", "khz", "mhz", "ghz"。
# Codex说明(自动生成)： 计算并保存 WRITE_MAGNITUDE_PLOT，供后续语句继续读取或更新。
WRITE_MAGNITUDE_PLOT = True
# Codex说明(自动生成)： 计算并保存 WRITE_PHASE_PLOT，供后续语句继续读取或更新。
WRITE_PHASE_PLOT = True

# 默认直接弹出 matplotlib 图窗用于检查 S 参数，而不是保存 PNG 照片。
# 如果你也想保存图片，把 SAVE_PLOT_FILES 改成 True。
# Codex说明(自动生成)： 计算并保存 SHOW_PLOTS，供后续语句继续读取或更新。
SHOW_PLOTS = True
# Codex说明(自动生成)： 计算并保存 PLOT_BLOCK，供后续语句继续读取或更新。
PLOT_BLOCK = True  # True 表示脚本会等你关闭图窗后再结束。
# Codex说明(自动生成)： 计算并保存 SAVE_PLOT_FILES，供后续语句继续读取或更新。
SAVE_PLOT_FILES = False

# 生成类模式共用的扫频/端口参数：linear、formula、draw 都会使用。
# Codex说明(自动生成)： 计算并保存 F_START，供后续语句继续读取或更新。
F_START = "10MHz"
# Codex说明(自动生成)： 计算并保存 F_STOP，供后续语句继续读取或更新。
F_STOP = "40GHz"
# Codex说明(自动生成)： 计算并保存 POINTS，供后续语句继续读取或更新。
POINTS = 201
# Codex说明(自动生成)： 计算并保存 SPACING，供后续语句继续读取或更新。
SPACING = "linear"  # "linear" 或 "log"。
# Codex说明(自动生成)： 计算并保存 RETURN_LOSS_DB，供后续语句继续读取或更新。
RETURN_LOSS_DB = 20.0  # 生成模式下 S11/S22 等反射项的回损。
# Codex说明(自动生成)： 计算并保存 CROSSTALK_DB，供后续语句继续读取或更新。
CROSSTALK_DB = 80.0  # S4P 非 through 通道的默认串扰幅度。
# Codex说明(自动生成)： 计算并保存 DELAY_PS，供后续语句继续读取或更新。
DELAY_PS = 80.0  # through 通道相位延迟；设为 0 表示零相位。
# Codex说明(自动生成)： 计算并保存 PHASE_OFFSET_DEG，供后续语句继续读取或更新。
PHASE_OFFSET_DEG = 0.0
# Codex说明(自动生成)： 计算并保存 Z0，供后续语句继续读取或更新。
Z0 = 50.0
# Codex说明(自动生成)： 计算并保存 THROUGH_PAIRS，供后续语句继续读取或更新。
THROUGH_PAIRS = []  # S4P 可填 ["S31", "S13", "S42", "S24"]；S2P 会自动保持 S12=S21。

# 模式 1：线性插损参数。
# Codex说明(自动生成)： 计算并保存 LINEAR_LOSS_START_DB，供后续语句继续读取或更新。
LINEAR_LOSS_START_DB = 0.2
# Codex说明(自动生成)： 计算并保存 LINEAR_LOSS_STOP_DB，供后续语句继续读取或更新。
LINEAR_LOSS_STOP_DB = 20.0

# 模式 2：协议常用公式 loss_db = a*f + b*sqrt(f) + c。
# MODEL_FREQUENCY_UNIT 决定公式里的 f 用什么单位，默认 GHz。
# Codex说明(自动生成)： 计算并保存 FORMULA_A，供后续语句继续读取或更新。
FORMULA_A = 0.08
# Codex说明(自动生成)： 计算并保存 FORMULA_B，供后续语句继续读取或更新。
FORMULA_B = 0.6
# Codex说明(自动生成)： 计算并保存 FORMULA_C，供后续语句继续读取或更新。
FORMULA_C = 0.1
# Codex说明(自动生成)： 计算并保存 MODEL_FREQUENCY_UNIT，供后续语句继续读取或更新。
MODEL_FREQUENCY_UNIT = "ghz"

# 模式 3：导入并修改 s 参数。
# 默认输入指向 zip 里自带的线性示例，改成你的 measured.s2p/measured.s4p 即可。
# Codex说明(自动生成)： 计算并保存 MODIFY_INPUT_FILE，供后续语句继续读取或更新。
MODIFY_INPUT_FILE = "examples/linear_demo.s2p"
# Codex说明(自动生成)： 计算并保存 MODIFY_TARGETS，供后续语句继续读取或更新。
MODIFY_TARGETS = ["5GHz:3.0", "12GHz:8.0"]  # 每个元素是 "频点:插损dB"。
# Codex说明(自动生成)： 计算并保存 MODIFY_PAIRS，供后续语句继续读取或更新。
MODIFY_PAIRS = ["S21", "S12"]  # S4P 可按实际通道填写，例如 ["S31", "S13"]。
# Codex说明(自动生成)： 计算并保存 MODIFY_SMOOTHNESS，供后续语句继续读取或更新。
MODIFY_SMOOTHNESS = 0.14
# Codex说明(自动生成)： 计算并保存 MODIFY_SMOOTH_DOMAIN，供后续语句继续读取或更新。
MODIFY_SMOOTH_DOMAIN = "log"  # "log" 通常更适合宽频扫频。
# Codex说明(自动生成)： 计算并保存 MODIFY_ANCHOR_EDGES，供后续语句继续读取或更新。
MODIFY_ANCHOR_EDGES = True  # True 会让校正曲线在扫频两端回到 0 dB 修正。
# Codex说明(自动生成)： 计算并保存 MODIFY_INSERT_TARGETS，供后续语句继续读取或更新。
MODIFY_INSERT_TARGETS = True  # True 会把目标频点插入输出频轴，便于精确命中。
# Codex说明(自动生成)： 计算并保存 MODIFY_REPORT_FILE，供后续语句继续读取或更新。
MODIFY_REPORT_FILE = ""  # 留空时自动生成 .report.txt。

# 模式 4：手动画插损折线。
# 运行 RUN_MODE = "draw" 时会先弹出画线窗口：左键添加折线点，右键撤销
# 最后一个点，按 Enter 或直接关闭窗口后生成 Touchstone。默认用平滑拟合
# 补齐点间曲线，避免简单折线导致的直上直下或硬拐点。
# 如果 DRAW_CONTROL_POINTS 非空，则不弹窗口，直接按这些点生成，便于脚本化和测试。
# draw 模式的用户输入按 S 参数幅度 dB 习惯填写：0 dB 在上，下面是负轴。
DRAW_LOSS_MIN_DB = -40.0
DRAW_LOSS_MAX_DB = 0.0
DRAW_CONTROL_POINTS = []  # 例如 ["10MHz:-0.2", "5GHz:-4.0", "40GHz:-20.0"]。
DRAW_WINDOW_TITLE = "Draw insertion loss"
DRAW_FIT = "smooth"  # "smooth" 平滑拟合；"linear" 保留旧的直线连接。
DRAW_FIT_DOMAIN = "linear"  # "linear" 或 "log"，宽频手绘时可尝试 "log"。
DRAW_MIN_SPACING_FRACTION = 1e-4  # 防止控制点太近导致近似垂直跳变。
DRAW_MAX_SLOPE_DB_PER_SPAN = 500.0  # 防止过陡的局部插损变化。

# 如果本地没装 numpy/matplotlib，默认自动执行：
#   python3 -m pip install -r requirements.txt
# 这样解压后直接 `python3 main.py` 更容易跑通。若你不希望脚本自动安装依赖，
# 把这里改成 False，脚本会只打印安装提示。
# Codex说明(自动生成)： 计算并保存 AUTO_INSTALL_MISSING_PACKAGES，供后续语句继续读取或更新。
AUTO_INSTALL_MISSING_PACKAGES = True

# 每次运行时写一份日志，方便排查“本地跑不通”到底卡在 Python、路径、
# 依赖安装还是参数设置。日志默认写在项目根目录的 last_run_log.txt。
# Codex说明(自动生成)： 计算并保存 WRITE_RUN_LOG，供后续语句继续读取或更新。
WRITE_RUN_LOG = True
# Codex说明(自动生成)： 计算并保存 RUN_LOG_FILE，供后续语句继续读取或更新。
RUN_LOG_FILE = "last_run_log.txt"


# Codex说明(自动生成)： 计算并保存 ROOT，供后续语句继续读取或更新。
ROOT = Path(__file__).resolve().parent
# Codex说明(自动生成)： 计算并保存 SRC，供后续语句继续读取或更新。
SRC = ROOT / "src"
# Codex说明(自动生成)： 检查条件 str(SRC) not in sys.path，根据结果选择后续执行路径。
if str(SRC) not in sys.path:
    # Codex说明(自动生成)： 调用 sys.path.insert 更新列表或集合，把当前步骤产生的数据加入结果。
    sys.path.insert(0, str(SRC))


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main() -> int:
    """Run either CLI arguments or the editable globals above.

    有命令行参数时，完全交给原 CLI；没有参数时，把本文件顶部的全局
    参数转换成同一套 CLI 参数。这样测试、文档和直接运行只维护一条路径。
    """

    # Codex说明(自动生成)： 调用 _ensure_dependencies，执行当前流程需要的具体操作或副作用。
    _ensure_dependencies()
    # Codex说明(自动生成)： 计算并保存 cli_main，供后续语句继续读取或更新。
    cli_main = _load_cli_main()

    # Codex说明(自动生成)： 检查条件 len(sys.argv) > 1，根据结果选择后续执行路径。
    if len(sys.argv) > 1:
        # Codex说明(自动生成)： 返回 cli_main(sys.argv[1:])，让调用方取得本函数的处理结果。
        return cli_main(sys.argv[1:])
    # Codex说明(自动生成)： 返回 cli_main(_argv_from_global_settings())，让调用方取得本函数的处理结果。
    return cli_main(_argv_from_global_settings())


# Codex说明(自动生成)： 定义函数 _argv_from_global_settings，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _argv_from_global_settings() -> list[str]:
    # Codex说明(自动生成)： 计算并保存 mode，供后续语句继续读取或更新。
    mode = RUN_MODE.strip().lower()
    # Codex说明(自动生成)： 检查条件 mode == 'linear'，根据结果选择后续执行路径。
    if mode == "linear":
        # Codex说明(自动生成)： 返回 _linear_argv()，让调用方取得本函数的处理结果。
        return _linear_argv()
    # Codex说明(自动生成)： 检查条件 mode == 'formula'，根据结果选择后续执行路径。
    if mode == "formula":
        # Codex说明(自动生成)： 返回 _formula_argv()，让调用方取得本函数的处理结果。
        return _formula_argv()
    # Codex说明(自动生成)： 检查条件 mode == 'draw'，根据结果选择后续执行路径。
    if mode == "draw":
        return _draw_argv()
    # Codex说明(自动生成)： 检查条件 mode == 'modify'，根据结果选择后续执行路径。
    if mode == "modify":
        # Codex说明(自动生成)： 返回 _modify_argv()，让调用方取得本函数的处理结果。
        return _modify_argv()
    # Codex说明(自动生成)： 抛出 ValueError("RUN_MODE must be 'linear', 'formula', or 'm...，明确提示输入、状态或处理流程无法继续。
    raise ValueError("RUN_MODE must be 'linear', 'formula', 'draw', or 'modify'")


# Codex说明(自动生成)： 定义函数 _linear_argv，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _linear_argv() -> list[str]:
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = _configured_output("linear_configured")
    # Codex说明(自动生成)： 计算并保存 argv，供后续语句继续读取或更新。
    argv = [
        "linear",
        "--ports",
        str(PORTS),
        "--f-start",
        F_START,
        "--f-stop",
        F_STOP,
        "--points",
        str(POINTS),
        "--spacing",
        SPACING,
        "--loss-start-db",
        str(LINEAR_LOSS_START_DB),
        "--loss-stop-db",
        str(LINEAR_LOSS_STOP_DB),
        "--output",
        str(output),
    ]
    # Codex说明(自动生成)： 返回 _add_generation_common_args(argv)，让调用方取得本函数的处理结果。
    return _add_generation_common_args(argv)


# Codex说明(自动生成)： 定义函数 _formula_argv，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _formula_argv() -> list[str]:
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = _configured_output("formula_configured")
    # Codex说明(自动生成)： 计算并保存 argv，供后续语句继续读取或更新。
    argv = [
        "formula",
        "--ports",
        str(PORTS),
        "--f-start",
        F_START,
        "--f-stop",
        F_STOP,
        "--points",
        str(POINTS),
        "--spacing",
        SPACING,
        "--a",
        str(FORMULA_A),
        "--b",
        str(FORMULA_B),
        "--c",
        str(FORMULA_C),
        "--model-frequency-unit",
        MODEL_FREQUENCY_UNIT,
        "--output",
        str(output),
    ]
    # Codex说明(自动生成)： 返回 _add_generation_common_args(argv)，让调用方取得本函数的处理结果。
    return _add_generation_common_args(argv)


def _draw_argv() -> list[str]:
    """Build CLI arguments for the interactive hand-drawn insertion-loss mode."""

    output = _configured_output("draw_configured")
    argv = [
        "draw",
        "--ports",
        str(PORTS),
        "--f-start",
        F_START,
        "--f-stop",
        F_STOP,
        "--points",
        str(POINTS),
        "--spacing",
        SPACING,
        "--loss-min-db",
        str(DRAW_LOSS_MIN_DB),
        "--loss-max-db",
        str(DRAW_LOSS_MAX_DB),
        "--draw-window-title",
        DRAW_WINDOW_TITLE,
        "--draw-fit",
        DRAW_FIT,
        "--draw-fit-domain",
        DRAW_FIT_DOMAIN,
        "--draw-min-spacing-fraction",
        str(DRAW_MIN_SPACING_FRACTION),
        "--draw-max-slope-db-per-span",
        str(DRAW_MAX_SLOPE_DB_PER_SPAN),
        "--output",
        str(output),
    ]
    env_draw_points = os.environ.get("INSERTION_LOSS_TOOL_DRAW_POINTS", "").strip()
    draw_points = [env_draw_points] if env_draw_points else DRAW_CONTROL_POINTS
    for point in draw_points:
        argv.extend(["--draw-point", point])
    return _add_generation_common_args(argv)


# Codex说明(自动生成)： 定义函数 _modify_argv，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _modify_argv() -> list[str]:
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = _configured_output("modified_configured")
    # Codex说明(自动生成)： 计算并保存 argv，供后续语句继续读取或更新。
    argv = [
        "modify",
        "--input",
        str(_project_path(MODIFY_INPUT_FILE)),
        "--output",
        str(output),
        "--smoothness",
        str(MODIFY_SMOOTHNESS),
        "--smooth-domain",
        MODIFY_SMOOTH_DOMAIN,
    ]
    # Codex说明(自动生成)： 遍历 MODIFY_TARGETS 中的 target，逐项执行循环体逻辑。
    for target in MODIFY_TARGETS:
        # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.extend(["--target", target])
    # Codex说明(自动生成)： 遍历 MODIFY_PAIRS 中的 pair，逐项执行循环体逻辑。
    for pair in MODIFY_PAIRS:
        # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.extend(["--pair", pair])
    # Codex说明(自动生成)： 检查条件 not MODIFY_ANCHOR_EDGES，根据结果选择后续执行路径。
    if not MODIFY_ANCHOR_EDGES:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-anchor-edges")
    # Codex说明(自动生成)： 检查条件 not MODIFY_INSERT_TARGETS，根据结果选择后续执行路径。
    if not MODIFY_INSERT_TARGETS:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-insert-targets")
    # Codex说明(自动生成)： 检查条件 MODIFY_REPORT_FILE，根据结果选择后续执行路径。
    if MODIFY_REPORT_FILE:
        # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.extend(["--report", str(_project_path(MODIFY_REPORT_FILE))])
    # Codex说明(自动生成)： 返回 _add_write_plot_args(argv)，让调用方取得本函数的处理结果。
    return _add_write_plot_args(argv)


# Codex说明(自动生成)： 定义函数 _add_generation_common_args，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _add_generation_common_args(argv: list[str]) -> list[str]:
    # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
    argv.extend(
        [
            "--return-loss-db",
            str(RETURN_LOSS_DB),
            "--crosstalk-db",
            str(CROSSTALK_DB),
            "--delay-ps",
            str(DELAY_PS),
            "--phase-offset-deg",
            str(PHASE_OFFSET_DEG),
            "--z0",
            str(Z0),
        ]
    )
    # Codex说明(自动生成)： 遍历 THROUGH_PAIRS 中的 pair，逐项执行循环体逻辑。
    for pair in THROUGH_PAIRS:
        # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.extend(["--through-pair", pair])
    # Codex说明(自动生成)： 返回 _add_write_plot_args(argv)，让调用方取得本函数的处理结果。
    return _add_write_plot_args(argv)


# Codex说明(自动生成)： 定义函数 _add_write_plot_args，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _add_write_plot_args(argv: list[str]) -> list[str]:
    # Codex说明(自动生成)： 调用 argv.extend 更新列表或集合，把当前步骤产生的数据加入结果。
    argv.extend(
        [
            "--format",
            OUTPUT_FORMAT,
            "--output-frequency-unit",
            OUTPUT_FREQUENCY_UNIT,
        ]
    )
    # Codex说明(自动生成)： 检查条件 not WRITE_MAGNITUDE_PLOT，根据结果选择后续执行路径。
    if not WRITE_MAGNITUDE_PLOT:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-plot")
    # Codex说明(自动生成)： 检查条件 not WRITE_PHASE_PLOT，根据结果选择后续执行路径。
    if not WRITE_PHASE_PLOT:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-phase-plot")
    # Codex说明(自动生成)： 检查条件 _env_flag('INSERTION_LOSS_TOOL_NO_SHOW')，根据结果选择后续执行路径。
    if _env_flag("INSERTION_LOSS_TOOL_NO_SHOW"):
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-show-plot")
    # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 SHOW_PLOTS。
    elif SHOW_PLOTS:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--show-plot")
    # Codex说明(自动生成)： 检查条件 not PLOT_BLOCK，根据结果选择后续执行路径。
    if not PLOT_BLOCK:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-plot-block")
    # Codex说明(自动生成)： 检查条件 _env_flag('INSERTION_LOSS_TOOL_SAVE_PLOTS') or SAVE_PLO...，根据结果选择后续执行路径。
    if _env_flag("INSERTION_LOSS_TOOL_SAVE_PLOTS") or SAVE_PLOT_FILES:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--save-plot-files")
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 调用 argv.append 更新列表或集合，把当前步骤产生的数据加入结果。
        argv.append("--no-save-plot-files")
    # Codex说明(自动生成)： 返回 argv，让调用方取得本函数的处理结果。
    return argv


# Codex说明(自动生成)： 定义函数 _configured_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _configured_output(stem: str) -> Path:
    env_output = os.environ.get("INSERTION_LOSS_TOOL_OUTPUT_FILE", "").strip()
    if env_output:
        return _project_path(env_output)
    # Codex说明(自动生成)： 检查条件 OUTPUT_FILE，根据结果选择后续执行路径。
    if OUTPUT_FILE:
        # Codex说明(自动生成)： 返回 _project_path(OUTPUT_FILE)，让调用方取得本函数的处理结果。
        return _project_path(OUTPUT_FILE)
    # Codex说明(自动生成)： 计算并保存 suffix，供后续语句继续读取或更新。
    suffix = f".s{PORTS}p"
    # Codex说明(自动生成)： 返回 ROOT / 'examples' / f'{stem}{suffix}'，让调用方取得本函数的处理结果。
    return ROOT / "examples" / f"{stem}{suffix}"


# Codex说明(自动生成)： 定义函数 _project_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _project_path(value: str | Path) -> Path:
    # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
    path = Path(value)
    # Codex说明(自动生成)： 检查条件 path.is_absolute()，根据结果选择后续执行路径。
    if path.is_absolute():
        # Codex说明(自动生成)： 返回 path，让调用方取得本函数的处理结果。
        return path
    # Codex说明(自动生成)： 返回 ROOT / path，让调用方取得本函数的处理结果。
    return ROOT / path


# Codex说明(自动生成)： 定义函数 _ensure_dependencies，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _ensure_dependencies() -> None:
    """Make required packages importable or exit with a useful setup message."""

    # Codex说明(自动生成)： 计算并保存 missing，供后续语句继续读取或更新。
    missing = [
        package
        for package in ("numpy", "matplotlib")
        if importlib.util.find_spec(package) is None
    ]
    # Codex说明(自动生成)： 检查条件 not missing，根据结果选择后续执行路径。
    if not missing:
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return

    # Codex说明(自动生成)： 计算并保存 package_list，供后续语句继续读取或更新。
    package_list = ", ".join(missing)
    # Codex说明(自动生成)： 检查条件 AUTO_INSTALL_MISSING_PACKAGES，根据结果选择后续执行路径。
    if AUTO_INSTALL_MISSING_PACKAGES:
        # Codex说明(自动生成)： 计算并保存 command，供后续语句继续读取或更新。
        command = [sys.executable, "-m", "pip", "install"]
        # Codex说明(自动生成)： 检查条件 sys.prefix == getattr(sys, 'base_prefix', sys.prefix)，根据结果选择后续执行路径。
        if sys.prefix == getattr(sys, "base_prefix", sys.prefix):
            # Codex说明(自动生成)： 调用 command.append 更新列表或集合，把当前步骤产生的数据加入结果。
            command.append("--user")
        # Codex说明(自动生成)： 调用 command.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        command.extend(["-r", str(ROOT / "requirements.txt")])
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print(f"Installing missing packages: {package_list}", flush=True)
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 subprocess.check_call，执行当前流程需要的具体操作或副作用。
            subprocess.check_call(command)
        # Codex说明(自动生成)： 捕获 subprocess.CalledProcessError，执行对应的恢复、记录或重新报错逻辑。
        except subprocess.CalledProcessError as exc:
            # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
            raise SystemExit(
                f"Automatic dependency installation failed with exit code {exc.returncode}.\n"
                "Run this command manually from the project directory:\n"
                f"  {sys.executable} -m pip install -r requirements.txt"
            ) from exc
        # Codex说明(自动生成)： 调用 _refresh_import_paths_after_install，执行当前流程需要的具体操作或副作用。
        _refresh_import_paths_after_install()
        # Codex说明(自动生成)： 计算并保存 still_missing，供后续语句继续读取或更新。
        still_missing = [
            package
            for package in ("numpy", "matplotlib")
            if importlib.util.find_spec(package) is None
        ]
        # Codex说明(自动生成)： 检查条件 still_missing，根据结果选择后续执行路径。
        if still_missing:
            # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
            raise SystemExit(
                "Packages were installed, but this Python process still cannot import: "
                f"{', '.join(still_missing)}\n"
                "Please run `python3 main.py` again, or install dependencies manually with:\n"
                f"  {sys.executable} -m pip install -r requirements.txt"
            )
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return

    # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
    raise SystemExit(
        f"Missing Python packages: {package_list}\n"
        f"Run this once from the project directory:\n"
        f"  {sys.executable} -m pip install -r requirements.txt"
    )


# Codex说明(自动生成)： 定义函数 _load_cli_main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _load_cli_main():
    """Load the CLI module without a static package import that PyCharm flags.

    PyCharm often marks `from insertion_loss_tool...` as unresolved unless
    `src/` is manually configured as a source root. Loading by file path keeps
    `main.py` clean for users who just open and run this single file.
    """

    # Codex说明(自动生成)： 计算并保存 package_name，供后续语句继续读取或更新。
    package_name = "_insertion_loss_tool_runtime"
    # Codex说明(自动生成)： 计算并保存 package_dir，供后续语句继续读取或更新。
    package_dir = SRC / "insertion_loss_tool"
    # Codex说明(自动生成)： 检查条件 package_name not in sys.modules，根据结果选择后续执行路径。
    if package_name not in sys.modules:
        # Codex说明(自动生成)： 计算并保存 package_spec，供后续语句继续读取或更新。
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            package_dir / "__init__.py",
            submodule_search_locations=[str(package_dir)],
        )
        # Codex说明(自动生成)： 检查条件 package_spec is None or package_spec.loader is None，根据结果选择后续执行路径。
        if package_spec is None or package_spec.loader is None:
            # Codex说明(自动生成)： 抛出 ImportError(f'Cannot load package from {package_dir}')，明确提示输入、状态或处理流程无法继续。
            raise ImportError(f"Cannot load package from {package_dir}")
        # Codex说明(自动生成)： 计算并保存 package_module，供后续语句继续读取或更新。
        package_module = importlib.util.module_from_spec(package_spec)
        # Codex说明(自动生成)： 更新 sys.modules[package_name]，把当前配置或计算结果写入对应对象。
        sys.modules[package_name] = package_module
        # Codex说明(自动生成)： 调用 package_spec.loader.exec_module，执行当前流程需要的具体操作或副作用。
        package_spec.loader.exec_module(package_module)

    # Codex说明(自动生成)： 计算并保存 module_name，供后续语句继续读取或更新。
    module_name = f"{package_name}.cli"
    # Codex说明(自动生成)： 计算并保存 module_spec，供后续语句继续读取或更新。
    module_spec = importlib.util.spec_from_file_location(
        module_name,
        package_dir / "cli.py",
    )
    # Codex说明(自动生成)： 检查条件 module_spec is None or module_spec.loader is None，根据结果选择后续执行路径。
    if module_spec is None or module_spec.loader is None:
        # Codex说明(自动生成)： 抛出 ImportError(f'Cannot load CLI module from {package_dir ...，明确提示输入、状态或处理流程无法继续。
        raise ImportError(f"Cannot load CLI module from {package_dir / 'cli.py'}")
    # Codex说明(自动生成)： 计算并保存 module，供后续语句继续读取或更新。
    module = importlib.util.module_from_spec(module_spec)
    # Codex说明(自动生成)： 更新 sys.modules[module_name]，把当前配置或计算结果写入对应对象。
    sys.modules[module_name] = module
    # Codex说明(自动生成)： 调用 module_spec.loader.exec_module，执行当前流程需要的具体操作或副作用。
    module_spec.loader.exec_module(module)
    # Codex说明(自动生成)： 返回 module.main，让调用方取得本函数的处理结果。
    return module.main


# Codex说明(自动生成)： 定义函数 _env_flag，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _env_flag(name: str) -> bool:
    # Codex说明(自动生成)： 返回 os.environ.get(name, '').strip().lower() in {'1', 'true...，让调用方取得本函数的处理结果。
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


# Codex说明(自动生成)： 定义函数 _refresh_import_paths_after_install，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _refresh_import_paths_after_install() -> None:
    """Make packages installed with --user visible without restarting Python."""

    # Codex说明(自动生成)： 计算并保存 candidate_paths，供后续语句继续读取或更新。
    candidate_paths = []
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 调用 candidate_paths.append 更新列表或集合，把当前步骤产生的数据加入结果。
        candidate_paths.append(site.getusersitepackages())
    # Codex说明(自动生成)： 捕获 AttributeError，执行对应的恢复、记录或重新报错逻辑。
    except AttributeError:
        # Codex说明(自动生成)： 保留空实现位置，表示这个分支当前不需要额外动作。
        pass
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 调用 candidate_paths.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        candidate_paths.extend(site.getsitepackages())
    # Codex说明(自动生成)： 捕获 AttributeError，执行对应的恢复、记录或重新报错逻辑。
    except AttributeError:
        # Codex说明(自动生成)： 保留空实现位置，表示这个分支当前不需要额外动作。
        pass

    # Codex说明(自动生成)： 遍历 candidate_paths 中的 path，逐项执行循环体逻辑。
    for path in candidate_paths:
        # Codex说明(自动生成)： 检查条件 path and path not in sys.path，根据结果选择后续执行路径。
        if path and path not in sys.path:
            # Codex说明(自动生成)： 调用 sys.path.append 更新列表或集合，把当前步骤产生的数据加入结果。
            sys.path.append(path)
    # Codex说明(自动生成)： 调用 importlib.invalidate_caches，执行当前流程需要的具体操作或副作用。
    importlib.invalidate_caches()


# Codex说明(自动生成)： 定义函数 _append_run_log，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _append_run_log(message: str) -> None:
    # Codex说明(自动生成)： 检查条件 not WRITE_RUN_LOG，根据结果选择后续执行路径。
    if not WRITE_RUN_LOG:
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return
    # Codex说明(自动生成)： 计算并保存 log_path，供后续语句继续读取或更新。
    log_path = _project_path(RUN_LOG_FILE)
    # Codex说明(自动生成)： 计算并保存 timestamp，供后续语句继续读取或更新。
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Codex说明(自动生成)： 调用 log_path.write_text 写出文件或数据，保存当前处理结果。
    log_path.write_text(
        (log_path.read_text(encoding="utf-8") if log_path.exists() else "")
        + f"[{timestamp}] {message}\n",
        encoding="utf-8",
    )


# Codex说明(自动生成)： 定义函数 _run_with_log，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _run_with_log() -> int:
    # Codex说明(自动生成)： 调用 _append_run_log，执行当前流程需要的具体操作或副作用。
    _append_run_log(
        "start "
        f"python={sys.executable!r} cwd={str(Path.cwd())!r} args={sys.argv[1:]!r}"
    )
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 计算并保存 exit_code，供后续语句继续读取或更新。
        exit_code = main()
    # Codex说明(自动生成)： 捕获 BaseException，执行对应的恢复、记录或重新报错逻辑。
    except BaseException as exc:
        # Codex说明(自动生成)： 调用 _append_run_log，执行当前流程需要的具体操作或副作用。
        _append_run_log(f"failed exception={type(exc).__name__}: {exc}")
        # Codex说明(自动生成)： 抛出 异常，明确提示输入、状态或处理流程无法继续。
        raise
    # Codex说明(自动生成)： 调用 _append_run_log，执行当前流程需要的具体操作或副作用。
    _append_run_log(f"exit_code={exit_code}")
    # Codex说明(自动生成)： 返回 exit_code，让调用方取得本函数的处理结果。
    return exit_code


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 结束当前命令行脚本，并把退出码交给操作系统；非零退出码表示运行失败。
    raise SystemExit(_run_with_log())
