#!/bin/zsh
# Codex说明(自动生成)： 切换到脚本所在目录，确保后续命令使用项目内的相对路径。
cd "$(dirname "$0")"
# 优先使用项目虚拟环境；未创建时使用系统中可运行的 python3。
python_bin="python3"
if [ -x ".venv/bin/python" ]; then
  python_bin=".venv/bin/python"
fi
# 自动化和无窗口环境继续走既有 CLI；用户双击时启动 WebView 界面。
if [ "${INSERTION_LOSS_TOOL_NO_SHOW:-}" = "1" ]; then
  "$python_bin" main.py
else
  "$python_bin" gui_main.py
fi
# Codex说明(自动生成)： 保存上一条命令的退出码，后续用于展示和原样返回运行状态。
exit_code=$?
# Codex说明(自动生成)： 输出空行，让终端显示更清晰。
echo
# Codex说明(自动生成)： 输出运行结果或提示信息，方便用户确认脚本执行情况。
echo "Exit code: $exit_code"
# Codex说明(自动生成)： 输出运行结果或提示信息，方便用户确认脚本执行情况。
echo "Run log: $(pwd)/last_run_log.txt"
# Codex说明(自动生成)： 输出运行结果或提示信息，方便用户确认脚本执行情况。
echo "Press Enter to close this window."
# Codex说明(自动生成)： 等待用户按回车，避免双击打开的终端窗口立即关闭。
read
# Codex说明(自动生成)： 用主程序的退出码结束脚本，方便外部工具判断运行是否成功。
exit $exit_code
