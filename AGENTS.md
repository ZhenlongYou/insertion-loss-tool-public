# Insertion Loss Tool — Windows 构建与验收契约

本文件适用于本目录及其子目录。Windows 上的 Codex/Agent 在修改、打包或
交付本工具前，必须遵守以下流程；不要跳过失败项，也不要把 macOS 测试结果
当作 Windows EXE 验收结果。

## 唯一打包入口

1. 使用 64 位 Windows 10/11 和 64 位 Python 3.9 或更高版本。
2. 在本目录直接运行 `build_windows_exe.bat`。不要手工复制 PyInstaller
   命令；交付格式固定为 `--onefile`。
3. 脚本会依次执行完整单元测试、压力测试、源码后台自检、源码 WebView2
   渲染探针、PyInstaller onefile 打包、EXE 后台自检、EXE WebView2 渲染
   探针、压缩和 SHA-256 生成。任何一步失败都视为打包失败。
4. 发布物是 `dist\InsertionLossTool-<version>-windows-x64.zip` 以及对应的
   `.sha256.txt`。ZIP 内只包含 `InsertionLossTool.exe`，不得出现 `_internal`
   目录或要求用户另外复制运行库；解压后直接运行这个 EXE。

## 外部运行条件

- Windows 必须安装 Microsoft Edge WebView2 Runtime；渲染探针会在缺失、
  后端不正确或页面合同失效时让构建失败。
- Tesseract OCR 是图片文字自动标定的外部可选依赖，不随 EXE 打包。需要
  自动识别标题、坐标轴文字时，应安装 Tesseract 并把 `tesseract.exe` 加入
  `PATH`。缺少它时曲线提取仍可用，但必须人工核对参数标签和坐标范围。

## Windows 实机验收

自动脚本成功后，仍需从解压后的发布目录双击 EXE，并至少人工检查：

1. `Linear` 能连续生成两次不同文件，四个 Sij 图均可见。
2. `Draw` 添加控制点后生成完整 S 参数图；放大、平移、复位可用。
3. `Modify` 能载入 `examples\formula_demo.s4p`，生成新文件并显示图表。
4. `Image to S-Parameter` 能执行添加、删除、再次添加；不同 trace 使用不同
   颜色；完成映射后能生成文件，非法/非无源组合显示明确原因而不是无响应。
5. `Open Folder` 能打开输出目录；程序关闭后可再次启动。

记录 Windows 版本、Python 版本、源码 Git OID、压缩包 SHA-256 和人工检查
结果。只有自动脚本与上述 Windows 实机验收都通过，才可声称 Windows EXE
已通过；否则必须明确写 `NOT_RUN`、`INCONCLUSIVE` 或具体失败项。不得声称 Windows EXE 已通过来替代尚未执行的实机检查。
