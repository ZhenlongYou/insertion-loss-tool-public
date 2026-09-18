"""Command-line interface for the insertion loss Touchstone tool."""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 argparse，解析命令行参数，支持用户从终端覆盖默认配置。
import argparse
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys

# Codex说明(自动生成)： 从 models 导入 COMMON_PORT_COUNTS，提供本文件后续流程需要的库能力。
from .models import COMMON_PORT_COUNTS


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main(argv: list[str] | None = None) -> int:
    # Codex说明(自动生成)： 计算并保存 parser，供后续语句继续读取或更新。
    parser = build_parser()
    # Codex说明(自动生成)： 计算并保存 args，供后续语句继续读取或更新。
    args = parser.parse_args(argv)
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 调用 args.func，执行当前流程需要的具体操作或副作用。
        args.func(args)
        # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
        return 0
    # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
    except Exception as exc:  # pragma: no cover - CLI boundary
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print(f"error: {exc}", file=sys.stderr)
        # Codex说明(自动生成)： 返回 2，让调用方取得本函数的处理结果。
        return 2


# Codex说明(自动生成)： 定义函数 build_parser，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def build_parser() -> argparse.ArgumentParser:
    # Codex说明(自动生成)： 计算并保存 parser，供后续语句继续读取或更新。
    parser = argparse.ArgumentParser(
        description="Generate, modify, and plot multi-port Touchstone insertion-loss files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 main.py linear --ports 2 --f-start 10MHz --f-stop 40GHz "
            "--points 801 --loss-start-db 0.2 --loss-stop-db 20 --output linear.s2p\n"
            "  python3 main.py formula --ports 4 --a 0.08 --b 0.6 --c 0.1 "
            "--model-frequency-unit ghz --output protocol.s4p\n"
            "  python3 main.py draw --ports 2 --f-start 10MHz --f-stop 40GHz "
            "--points 801 --output drawn.s2p\n"
            "  python3 main.py modify --input measured.s2p --target 5GHz:6.5 "
            "--target 12GHz:12.0 --pair S21 --pair S12 --output tuned.s2p\n"
        ),
    )
    # Codex说明(自动生成)： 计算并保存 subparsers，供后续语句继续读取或更新。
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Codex说明(自动生成)： 计算并保存 linear，供后续语句继续读取或更新。
    linear = subparsers.add_parser("linear", help="Generate linear insertion loss.")
    # Codex说明(自动生成)： 调用 add_generation_args，执行当前流程需要的具体操作或副作用。
    add_generation_args(linear)
    # Codex说明(自动生成)： 调用 linear.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    linear.add_argument("--loss-start-db", type=float, required=True)
    # Codex说明(自动生成)： 调用 linear.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    linear.add_argument("--loss-stop-db", type=float, required=True)
    # Codex说明(自动生成)： 调用 linear.set_defaults，执行当前流程需要的具体操作或副作用。
    linear.set_defaults(func=run_linear)

    # Codex说明(自动生成)： 计算并保存 formula，供后续语句继续读取或更新。
    formula = subparsers.add_parser(
        "formula", help="Generate a*f + b*sqrt(f) + c insertion loss."
    )
    # Codex说明(自动生成)： 调用 add_generation_args，执行当前流程需要的具体操作或副作用。
    add_generation_args(formula)
    # Codex说明(自动生成)： 调用 formula.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    formula.add_argument("--a", type=float, required=True)
    # Codex说明(自动生成)： 调用 formula.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    formula.add_argument("--b", type=float, required=True)
    # Codex说明(自动生成)： 调用 formula.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    formula.add_argument("--c", type=float, required=True)
    # Codex说明(自动生成)： 调用 formula.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    formula.add_argument(
        "--model-frequency-unit",
        default="ghz",
        choices=["hz", "khz", "mhz", "ghz"],
        help="Unit used for f in a*f + b*sqrt(f) + c. Default: ghz.",
    )
    # Codex说明(自动生成)： 调用 formula.set_defaults，执行当前流程需要的具体操作或副作用。
    formula.set_defaults(func=run_formula)

    # Codex说明(自动生成)： 计算并保存 draw，供后续语句继续读取或更新。
    draw = subparsers.add_parser(
        "draw",
        help="Draw insertion loss with an interactive matplotlib window.",
    )
    # Codex说明(自动生成)： 调用 add_generation_args，执行当前流程需要的具体操作或副作用。
    add_generation_args(draw)
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--loss-min-db",
        type=float,
        default=-40.0,
        help="Lower y-axis limit for the drawing window. Default: -40 dB.",
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--loss-max-db",
        type=float,
        default=0.0,
        help="Upper y-axis limit for the drawing window. Default: 0 dB.",
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-point",
        action="append",
        help=(
            "Optional scripted control point as frequency:magnitude_db, for example "
            "5GHz:-3.5. Repeat to bypass the interactive drawing window."
        ),
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-window-title",
        default="Draw insertion loss",
        help="Title for the interactive drawing window.",
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-fit",
        choices=["smooth", "linear"],
        default="smooth",
        help="How to fill between drawn points. Default: smooth.",
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-fit-domain",
        choices=["linear", "log"],
        default="linear",
        help="Frequency domain used by the draw fit. Default: linear.",
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-min-spacing-fraction",
        type=float,
        default=1e-4,
        help=(
            "Minimum allowed spacing between drawn points as a fraction of the "
            "draw-fit span. Default: 1e-4."
        ),
    )
    # Codex说明(自动生成)： 调用 draw.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    draw.add_argument(
        "--draw-max-slope-db-per-span",
        type=float,
        default=500.0,
        help=(
            "Maximum allowed drawn loss slope, normalized to the full fit span. "
            "Default: 500 dB/span."
        ),
    )
    # Codex说明(自动生成)： 调用 draw.set_defaults，执行当前流程需要的具体操作或副作用。
    draw.set_defaults(func=run_draw)

    # Codex说明(自动生成)： 计算并保存 modify，供后续语句继续读取或更新。
    modify = subparsers.add_parser(
        "modify",
        help="Import Touchstone and smoothly adjust selected insertion-loss points.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument("--input", required=True, help="Input .sNp file.")
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument("--output", required=True, help="Output .sNp file.")
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--target",
        action="append",
        required=True,
        help="Target insertion loss as frequency:loss_db, for example 5GHz:8.0.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--pair",
        action="append",
        help="S-parameter path to modify, for example S21. Default: adjacent reciprocal lanes.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--smoothness",
        type=float,
        default=0.12,
        help="Shape-preserving curve tension. Larger values retain more local slope.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--smooth-domain",
        choices=["log", "linear"],
        default="log",
        help="Domain used for smooth correction. Default: log.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--no-anchor-edges",
        action="store_true",
        help="Do not force correction back to 0 dB at the sweep edges.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument(
        "--no-insert-targets",
        action="store_true",
        help="Do not insert target frequencies that are absent from the source file.",
    )
    # Codex说明(自动生成)： 调用 modify.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    modify.add_argument("--report", help="Optional text report path.")
    # Codex说明(自动生成)： 调用 add_write_plot_args 生成或展示图形，便于观察计算结果。
    add_write_plot_args(modify)
    # Codex说明(自动生成)： 调用 modify.set_defaults，执行当前流程需要的具体操作或副作用。
    modify.set_defaults(func=run_modify)

    # Codex说明(自动生成)： 返回 parser，让调用方取得本函数的处理结果。
    return parser


# Codex说明(自动生成)： 定义函数 add_generation_args，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def add_generation_args(parser: argparse.ArgumentParser) -> None:
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--ports", type=int, choices=COMMON_PORT_COUNTS, default=2)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--f-start", default="10MHz")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--f-stop", default="40GHz")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--points", type=int, default=801)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--spacing", choices=["linear", "log"], default="linear")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--through-pair",
        action="append",
        help="Through path to fill, for example S21 or 2,1. Repeat as needed.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--return-loss-db", type=float, default=20.0)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--crosstalk-db", type=float, default=80.0)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--delay-ps", type=float, default=0.0)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--phase-offset-deg", type=float, default=0.0)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--z0", type=float, default=50.0)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--output", help="Output Touchstone path. Defaults to mode.sNp.")
    # Codex说明(自动生成)： 调用 add_write_plot_args 生成或展示图形，便于观察计算结果。
    add_write_plot_args(parser)


# Codex说明(自动生成)： 定义函数 add_write_plot_args，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def add_write_plot_args(parser: argparse.ArgumentParser) -> None:
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--format",
        choices=["ri", "ma", "db"],
        default="ri",
        help="Touchstone output format. Default: ri.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--output-frequency-unit",
        choices=["hz", "khz", "mhz", "ghz"],
        default="ghz",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--plot", help="Magnitude plot path. Defaults next to output.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--phase-plot", help="Phase plot path. Defaults next to output.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--no-plot", action="store_true", help="Skip plots.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--no-phase-plot", action="store_true", help="Skip phase plot.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--show-plot",
        dest="show_plot",
        action="store_true",
        help="Display S-parameter plots in matplotlib windows.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--no-show-plot",
        dest="show_plot",
        action="store_false",
        help="Do not display matplotlib plot windows.",
    )
    # Codex说明(自动生成)： 调用 parser.set_defaults，执行当前流程需要的具体操作或副作用。
    parser.set_defaults(show_plot=False)
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--plot-block",
        dest="plot_block",
        action="store_true",
        default=True,
        help="When showing plots, wait until plot windows are closed. Default: true.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--no-plot-block",
        dest="plot_block",
        action="store_false",
        help="When showing plots, do not wait for plot windows to close.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--save-plot-files",
        dest="save_plot_files",
        action="store_true",
        default=True,
        help="Save plot PNG files next to the output. Default for CLI: true.",
    )
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument(
        "--no-save-plot-files",
        dest="save_plot_files",
        action="store_false",
        help="Do not save plot PNG files; useful when only interactive plotting is wanted.",
    )


# Codex说明(自动生成)： 定义函数 run_linear，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_linear(args: argparse.Namespace) -> None:
    # Codex说明(自动生成)： 从 models 导入 generate_frequency_axis, linear_loss, parse_frequency，提供本文件后续流程需要的库能力。
    from .models import generate_frequency_axis, linear_loss, parse_frequency

    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = generate_frequency_axis(
        parse_frequency(args.f_start),
        parse_frequency(args.f_stop),
        args.points,
        spacing=args.spacing,
    )
    # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
    loss_db = linear_loss(frequency_hz, args.loss_start_db, args.loss_stop_db)
    # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
    data = make_generated_network(args, frequency_hz, loss_db)
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = Path(args.output or f"linear.s{args.ports}p")
    # Codex说明(自动生成)： 调用 write_and_plot 生成或展示图形，便于观察计算结果。
    write_and_plot(data, output, args)


# Codex说明(自动生成)： 定义函数 run_formula，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_formula(args: argparse.Namespace) -> None:
    # Codex说明(自动生成)： 从 models 导入 generate_frequency_axis, parse_frequency, protocol_loss，提供本文件后续流程需要的库能力。
    from .models import generate_frequency_axis, parse_frequency, protocol_loss

    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = generate_frequency_axis(
        parse_frequency(args.f_start),
        parse_frequency(args.f_stop),
        args.points,
        spacing=args.spacing,
    )
    # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
    loss_db = protocol_loss(
        frequency_hz,
        a=args.a,
        b=args.b,
        c=args.c,
        model_frequency_unit=args.model_frequency_unit,
    )
    # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
    data = make_generated_network(args, frequency_hz, loss_db)
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = Path(args.output or f"formula.s{args.ports}p")
    # Codex说明(自动生成)： 调用 write_and_plot 生成或展示图形，便于观察计算结果。
    write_and_plot(data, output, args)


# Codex说明(自动生成)： 定义函数 run_draw，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_draw(args: argparse.Namespace) -> None:
    """Run the hand-drawn insertion-loss workflow.

    Without --draw-point this opens a matplotlib window where the user clicks
    the insertion-loss control points. With --draw-point it becomes fully
    scriptable, which keeps automated tests and batch usage deterministic.
    """

    # Codex说明(自动生成)： 从 models 导入 draw_loss_points_interactive, generate_frequency_axis, insert_draw_control_frequencies, interpolate_drawn_loss 等名称，提供本文件后续流程需要的库能力。
    from .models import (
        draw_loss_points_interactive,
        generate_frequency_axis,
        insert_draw_control_frequencies,
        interpolate_drawn_loss,
        parse_draw_points,
        parse_frequency,
    )

    # Codex说明(自动生成)： 计算并保存 start_hz，供后续语句继续读取或更新。
    start_hz = parse_frequency(args.f_start)
    # Codex说明(自动生成)： 计算并保存 stop_hz，供后续语句继续读取或更新。
    stop_hz = parse_frequency(args.f_stop)
    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = generate_frequency_axis(
        start_hz,
        stop_hz,
        args.points,
        spacing=args.spacing,
    )
    # Codex说明(自动生成)： 检查条件 args.draw_point，根据结果选择后续执行路径。
    if args.draw_point:
        # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
        control_points = parse_draw_points(args.draw_point)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 计算并保存 control_points，供后续语句继续读取或更新。
        control_points = draw_loss_points_interactive(
            start_hz,
            stop_hz,
            loss_min_db=args.loss_min_db,
            loss_max_db=args.loss_max_db,
            frequency_unit=args.output_frequency_unit,
            title=args.draw_window_title,
            fit_method=args.draw_fit,
            fit_domain=args.draw_fit_domain,
            min_spacing_fraction=args.draw_min_spacing_fraction,
            max_slope_db_per_span=args.draw_max_slope_db_per_span,
        )
    # Codex说明(自动生成)： 计算并保存 frequency_hz，供后续语句继续读取或更新。
    frequency_hz = insert_draw_control_frequencies(frequency_hz, control_points)
    # Codex说明(自动生成)： 计算并保存 loss_db，供后续语句继续读取或更新。
    loss_db = interpolate_drawn_loss(
        frequency_hz,
        control_points,
        method=args.draw_fit,
        fit_domain=args.draw_fit_domain,
        min_spacing_fraction=args.draw_min_spacing_fraction,
        max_slope_db_per_span=args.draw_max_slope_db_per_span,
    )
    # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
    data = make_generated_network(args, frequency_hz, loss_db)
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = Path(args.output or f"draw.s{args.ports}p")
    # Codex说明(自动生成)： 调用 write_and_plot 生成或展示图形，便于观察计算结果。
    write_and_plot(data, output, args)


# Codex说明(自动生成)： 定义函数 run_modify，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_modify(args: argparse.Namespace) -> None:
    # Codex说明(自动生成)： 从 models 导入 modify_insertion_loss, parse_pairs, parse_target_points，提供本文件后续流程需要的库能力。
    from .models import modify_insertion_loss, parse_pairs, parse_target_points
    # Codex说明(自动生成)： 从 touchstone 导入 read_touchstone，提供本文件后续流程需要的库能力。
    from .touchstone import read_touchstone

    # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
    data = read_touchstone(args.input)
    # Codex说明(自动生成)： 计算并保存 targets，供后续语句继续读取或更新。
    targets = parse_target_points(args.target)
    # Codex说明(自动生成)： 计算并保存 pairs，供后续语句继续读取或更新。
    pairs = parse_pairs(args.pair, data.n_ports)
    # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
    result = modify_insertion_loss(
        data,
        targets,
        pairs,
        smoothness=args.smoothness,
        smooth_domain=args.smooth_domain,
        anchor_edges=not args.no_anchor_edges,
        insert_targets=not args.no_insert_targets,
    )
    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
    output = Path(args.output)
    # Codex说明(自动生成)： 调用 write_and_plot 生成或展示图形，便于观察计算结果。
    write_and_plot(result.data, output, args)
    # Codex说明(自动生成)： 计算并保存 report_path，供后续语句继续读取或更新。
    report_path = Path(args.report) if args.report else output.with_suffix(output.suffix + ".report.txt")
    # Codex说明(自动生成)： 调用 write_modification_report，执行当前流程需要的具体操作或副作用。
    write_modification_report(report_path, result.results)
    # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
    print(f"wrote {report_path}")


# Codex说明(自动生成)： 定义函数 make_generated_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def make_generated_network(
    args: argparse.Namespace,
    frequency_hz,
    loss_db,
):
    # Codex说明(自动生成)： 从 models 导入 build_network, parse_pairs，提供本文件后续流程需要的库能力。
    from .models import build_network, parse_pairs

    # Codex说明(自动生成)： 计算并保存 pairs，供后续语句继续读取或更新。
    pairs = parse_pairs(args.through_pair, args.ports)
    # Codex说明(自动生成)： 返回 build_network(frequency_hz, args.ports, loss_db, throug...，让调用方取得本函数的处理结果。
    return build_network(
        frequency_hz,
        args.ports,
        loss_db,
        through_pairs=pairs,
        return_loss_db=args.return_loss_db,
        crosstalk_db=args.crosstalk_db,
        delay_ps=args.delay_ps,
        phase_offset_deg=args.phase_offset_deg,
        z0=args.z0,
    )


# Codex说明(自动生成)： 定义函数 write_and_plot，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def write_and_plot(data, output: Path, args: argparse.Namespace) -> None:
    # Codex说明(自动生成)： 从 models 导入 plot_sparameters，提供本文件后续流程需要的库能力。
    from .models import plot_sparameters
    # Codex说明(自动生成)： 从 touchstone 导入 write_touchstone，提供本文件后续流程需要的库能力。
    from .touchstone import write_touchstone

    # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
    write_touchstone(
        data,
        output,
        frequency_unit=args.output_frequency_unit,
        data_format=args.format,
    )
    # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
    print(f"wrote {output}")
    # Codex说明(自动生成)： 检查条件 args.no_plot，根据结果选择后续执行路径。
    if args.no_plot:
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return
    # Codex说明(自动生成)： 计算并保存 (mag_plot, phase_plot)，供后续语句继续读取或更新。
    mag_plot, phase_plot = default_plot_paths(output, args)
    # Codex说明(自动生成)： 检查条件 not args.save_plot_files，根据结果选择后续执行路径。
    if not args.save_plot_files:
        # Codex说明(自动生成)： 计算并保存 mag_plot，供后续语句继续读取或更新。
        mag_plot = None
        # Codex说明(自动生成)： 计算并保存 phase_plot，供后续语句继续读取或更新。
        phase_plot = None
    # Codex说明(自动生成)： 计算并保存 show_phase，供后续语句继续读取或更新。
    show_phase = not args.no_phase_plot
    # Codex说明(自动生成)： 调用 plot_sparameters 生成或展示图形，便于观察计算结果。
    plot_sparameters(
        data,
        mag_plot,
        kind="magnitude",
        frequency_unit=args.output_frequency_unit,
        show=args.show_plot,
        block=args.plot_block and not show_phase,
    )
    # Codex说明(自动生成)： 检查条件 mag_plot is not None，根据结果选择后续执行路径。
    if mag_plot is not None:
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print(f"wrote {mag_plot}")
    # Codex说明(自动生成)： 检查条件 args.show_plot，根据结果选择后续执行路径。
    if args.show_plot:
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print("displayed magnitude plot")
    # Codex说明(自动生成)： 检查条件 not args.no_phase_plot，根据结果选择后续执行路径。
    if not args.no_phase_plot:
        # Codex说明(自动生成)： 调用 plot_sparameters 生成或展示图形，便于观察计算结果。
        plot_sparameters(
            data,
            phase_plot,
            kind="phase",
            frequency_unit=args.output_frequency_unit,
            show=args.show_plot,
            block=args.plot_block,
        )
        # Codex说明(自动生成)： 检查条件 phase_plot is not None，根据结果选择后续执行路径。
        if phase_plot is not None:
            # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
            print(f"wrote {phase_plot}")
        # Codex说明(自动生成)： 检查条件 args.show_plot，根据结果选择后续执行路径。
        if args.show_plot:
            # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
            print("displayed phase plot")


# Codex说明(自动生成)： 定义函数 default_plot_paths，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def default_plot_paths(output: Path, args: argparse.Namespace) -> tuple[Path, Path]:
    # Codex说明(自动生成)： 计算并保存 mag_plot，供后续语句继续读取或更新。
    mag_plot = Path(args.plot) if args.plot else output.with_name(f"{output.stem}_mag.png")
    # Codex说明(自动生成)： 计算并保存 phase_plot，供后续语句继续读取或更新。
    phase_plot = (
        Path(args.phase_plot)
        if args.phase_plot
        else output.with_name(f"{output.stem}_phase.png")
    )
    # Codex说明(自动生成)： 返回 (mag_plot, phase_plot)，让调用方取得本函数的处理结果。
    return mag_plot, phase_plot


# Codex说明(自动生成)： 定义函数 write_modification_report，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def write_modification_report(path: Path, results) -> None:
    # Codex说明(自动生成)： 调用 path.parent.mkdir，执行当前流程需要的具体操作或副作用。
    path.parent.mkdir(parents=True, exist_ok=True)
    # Codex说明(自动生成)： 计算并保存 lines，供后续语句继续读取或更新。
    lines = [
        "Insertion loss modification report",
        "",
        "pair,frequency_hz,requested_loss_db,original_loss_db,achieved_loss_db,phase_delta_deg",
    ]
    # Codex说明(自动生成)： 遍历 results 中的 item，逐项执行循环体逻辑。
    for item in results:
        # Codex说明(自动生成)： 调用 lines.append 更新列表或集合，把当前步骤产生的数据加入结果。
        lines.append(
            f"{item.pair},{item.frequency_hz:.12g},{item.requested_loss_db:.6g},"
            f"{item.original_loss_db:.6g},{item.achieved_loss_db:.6g},{item.phase_delta_deg:.6g}"
        )
    # Codex说明(自动生成)： 调用 path.write_text 写出文件或数据，保存当前处理结果。
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
