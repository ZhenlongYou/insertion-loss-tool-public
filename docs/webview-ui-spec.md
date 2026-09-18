# WebView 界面迁移规格

## 目标

将正式桌面入口从 Tk/ttk 切换到与协议对比工具相同的 pywebview 架构：macOS 使用 WKWebView，Windows 强制使用 Edge WebView2。现有 S 参数模型、Touchstone 读写和无源性预检保持不变。

## 用户界面

- 顶部只保留两个页签：`Auto`、`Image to S-Parameter`。页签切换仅切换 HTML 面板，不调用 Python。
- Auto 保留四种模式：`Linear`、`Formula`、`Draw`、`Modify`，四个名称必须保持单行。
- 常用字段直接显示；较少使用的格式、阻抗、相位等放入 `More Parameters`。
- 生成结果在页面内显示幅度和相位曲线，不再嵌入 Tk Matplotlib 画布。
- Image to S-Parameter 只保留一个 `Add Images` 操作；多次选择采用追加并去重。后续追加只传输新增图片，限制为 32 张、单张 20 MB、合计 128 MB。
- 正常窗口下 `Output Networks`、`Images` 和网络详情为同一行三列；输出栏保持窄栏，图片工作区必须明显宽于网络详情，输出文件字段仍完整可见。小于等于 1050 px 时，输出与图片同处第一行，详情移到第二行并由 Image to S-Parameter 工作区滚动。
- Draw 的 SVG 不放在窄控制栏，而占用右侧主工作区；真实窗口绘图区不得小于 600×360 px，并显示坐标网格。
- Image to S-Parameter 允许创建 1–6 个输出，每个输出独立选择 2、3、4、6、8 个物理端口；单端模式显示 Sij，混合模模式要求偶数物理端口并显示完整 SDD/SDC/SCD/SCC 块。
- 每张图片独立保存起始、终止和步进。输出频率支持 `Common Range`、`Manual`、`Full Range`；最后一种只有明确选择 `Fill Missing Range` 才可使用。
- 开关使用行业术语 `Reciprocal (Sij = Sji)`；启用后单端模式联动 Sij/Sji，混合模模式还正确联动 SCDij/SDCji，关闭后允许独立映射。
- 每张图在设置频率起止/步进和 Y 轴上下限后，由用户点击 `Digitize`。Python 识别规则网格、提取受支持的彩色幅度轨迹，并把检测框和曲线叠加回原图供复核。未识别前不提供虚构的 A–D 来源；失败重试清除旧结果。
- OCR 只在本机可用时建议唯一的 Sij/SDD/SDC/SCD/SCC 标签，缺失、超时或多标签时回退到手动选择。图片只提供幅度，不宣称恢复相位或原始 Touchstone 文件。
- 识别期间锁定该图片的频率和 Y 轴输入，并用校准版本号拒绝过期结果；单张解码图上限为 1200 万像素，颜色分类按固定行块处理。
- 页面、正常状态和错误状态均使用英文；频率单位统一显示为 `GHz`、`MHz`、`kHz`、`Hz`。
- 混合模转单端必须同时具备完整复数矩阵、物理端口配对和兼容参考阻抗；幅度图片不满足条件时保持混合模。依据：IBIS Open Forum, [Touchstone File Format Specification 2.0](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf)，混合模概念与参考阻抗条件（印刷页 19–20）、`[Mixed-Mode Order]`（页 20–22）、Appendix A（页 28–32）。

## Python / JavaScript 边界

- Python 是生成、文件选择、Touchstone 写入、无源性检查和映射状态的权威来源。
- JavaScript 只负责表单、页签、轻量 SVG 曲线显示和事件转发。
- JS 桥接面使用显式白名单，不暴露任意文件或 Python 执行能力。
- 长耗时生成在后台线程运行；重复点击生成时直接拒绝第二个任务。

## 兼容与入口

- `gui_main.py` 和安装后的 `insertion-loss-tool` 启动 WebView 界面。
- `gui_main.py --self-test` 在无 pywebview 时仍可无窗口验证 Web UI 资源和四种生成路径；`--renderer-smoke-test` 独立验证 pywebview 可用性与真实渲染器。
- 原 `insertion_loss_tool.gui` 暂时保留，供旧测试和故障回退使用，但不再是正式启动入口。
- `main.py` 仍是命令行/可编辑参数入口，不改行为。

## 验收

1. Windows 后端选择为 `edgechromium`；macOS 不强制后端，由 pywebview 使用 WKWebView。
2. Web UI 合同中只有一个 `Add Images` 按钮，不含旧中文页签或图片入口。
3. 打开联动后 S12/S21 以及任意 Sij/Sji 都同步；关闭后可独立修改。
4. Web API 可通过公开路径生成并独立回读线性、公式、手绘和修改结果。
5. 真实原生窗口完成加载探针，页签切换不触发 Python API 调用且无横向溢出。
6. 真实窗口的图片预览宽度和高度均不小于 360 px；缩放窗口必须能实际增大图片并产生可平移区域。
7. 现有全量测试、新增 WebView 测试、真实入口 self-test 和 test-effectiveness 门禁通过。
8. 原生渲染探针验证英文模式名不换行、频率单位大小写、Draw 实际尺寸、Output Networks 条目未裁切、正常与失败状态无中文。
9. 原生渲染探针要求存在 `Digitize`，图片区宽于详情区至少 15%，输出栏小于图片区 30%，输出文件字段至少 260 px，频率范围字段至少 145 px。
10. 已知解析曲线的独立数值真值、空白图失败、同色多轨迹拒绝、识别前无虚假来源和失败重试清除旧结果均通过最终版本验证；两张临时用户图片仅保留早期版本的参考读数，不计入最终验收。
