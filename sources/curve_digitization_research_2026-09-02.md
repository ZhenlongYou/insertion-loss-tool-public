# 曲线图像数字化方案调研（2026-09-02）

本记录用于说明 Insertion Loss Tool 曲线识别优化的技术依据。外部项目仅用于阅读和比较算法思想，没有复制其实现代码。

## 工程项目

### WebPlotDigitizer

- 项目：https://github.com/automeris-io/WebPlotDigitizer
- 调研版本：`3a3ecb11606945d0701c8a488777e6861be70056`
- 许可证：AGPL-3.0。
- 相关实现：`javascript/core/autoDetection.js` 使用目标颜色距离建立二值候选；`javascript/core/curve_detection/averagingWindowCore.js` 对每列像素形成垂直 blob，再以水平和垂直窗口聚合。
- 可采用的思想：颜色候选与曲线跟踪分层；自动结果必须允许人工颜色/区域约束。
- 不直接采用的部分：其平均窗口是局部方法，不能单独解决同色交叉和遮挡；AGPL 实现不复制到本项目。

### Engauge Digitizer

- 项目：https://github.com/markummitchell/engauge-digitizer
- 项目说明：https://markummitchell.github.io/engauge-digitizer/
- 可采用的思想：自动提取与人工校准并存；轴检查、撤销和结果复核是数字化工作流的一部分；少量控制点可以使用样条插值。
- 边界：成熟交互工具并不等于所有图片都可以无复核自动恢复。

### PlotDigitizer（Python 实验项目）

- 项目：https://github.com/anadb/PlotDigitizer
- 调研版本：`91a68a02b3b1983f42eac8d719babe6e68629a65`
- 可采用的思想：HSV 色相候选之外单独处理 achromatic 灰度曲线；先抑制跨越大部分画布的灰色网格行/列；每列采用紧密像素簇；深陷波需用密度门限防止把孤立噪声当作竖直曲线。
- 风险：调研版本仓库没有发现根目录许可证文件，且默认每列中位数/样条仍可能在交叉处换线，因此只借鉴公开说明中的方法分层。

## 论文

### Parsing Line Chart Images Using Linear Programming

- Hajime Kato et al., WACV 2022, pp. 2109-2118。
- 论文与书目信息：https://openaccess.thecvf.com/content/WACV2022/html/Kato_Parsing_Line_Chart_Images_Using_Linear_Programming_WACV_2022_paper.html
- DOI：https://doi.org/10.1109/WACV51458.2022.00261
- 核心结论：先预测像素级线型概率，再构图，把多曲线追踪建模为 minimum-cost flow；相较逐条贪心，它能联合处理遮挡、虚线和不同线型，并且不强制依赖图例。
- 本项目采用：以候选像素/垂直观测为节点，用颜色身份、连续性和已观测锚点形成全局代价；只补有双侧证据的内部缺口。
- 本项目暂不采用：论文的语义分割网络及线性规划求解器会显著增加模型、运行时和 Windows EXE 依赖。

### LineEX

- Shivasankaran V. P. et al., WACV 2023。
- 论文：https://openaccess.thecvf.com/content/WACV2023/papers/P._LineEX_Data_Extraction_From_Scientific_Line_Charts_WACV_2023_paper.pdf
- 代码：https://github.com/Shiva-sankaran/LineEX
- 核心结论：曲线提取应拆成关键点提取、图表元素/OCR、关键点分组、图例映射和数值标定；论文使用包含 43 万张合成线图的数据集。
- 对本项目的启示：参数文字属于映射信息，不应成为恢复可见几何的硬条件；合成真值必须覆盖线宽、网格、颜色、交叉和无图例变化。

### LineFormer

- Jay Lal et al., ICDAR 2023。
- 论文：https://arxiv.org/abs/2305.01837
- 代码：https://github.com/TheJaeLal/LineFormer
- 调研版本：`7952e27b4653dea025394618fbd655f41d82ab6b`
- 核心结论：多线图中的交叉、遮挡、拥挤以及缺少图例是实例分割问题，不能仅靠局部颜色阈值；模型直接输出各条线的实例掩码。
- 暂不作为默认后端：官方环境依赖 PyTorch 1.13.1、CUDA 11.7、MMDetection 和外部 checkpoint，不适合当前轻量离线单文件 EXE。

### ChartOCR

- Luo et al., WACV 2021。
- 论文：https://openaccess.thecvf.com/content/WACV2021/papers/Luo_ChartOCR_Data_Extraction_From_Charts_Images_via_a_Deep_Hybrid_WACV_2021_paper.pdf
- 代码：https://github.com/zmykevin/ChartOCR
- 对本项目的启示：OCR、图表元素检测和数值提取应独立评估；OCR 失败不能等同于曲线像素不存在。

## 本轮采用的混合方案

1. 画布边界和坐标标定与曲线几何分离；OCR 只产生可编辑建议。
2. 有色曲线继续采用抗锯齿稳定的颜色方向和互斥颜色簇。
3. 新增灰度/黑色候选：根据中性色和亮度提取，先删除长直网格带及其邻域，再做连续路径验证。
4. 临时保留低覆盖候选，以便全局关联识别“消失—重现”的同一轨迹；没有全局证据的候选在返回前恢复到正常覆盖门限。
5. 无标签的两条曲线只有在两种视觉身份分别出现于两个不相连区间时，才允许联合动态规划补中间共享段。
6. 前缀、后缀或长缺口没有双侧证据时不推测；输出继续区分 observed、shared overlap、interpolated 和 unresolved。
7. 跟踪代价同时约束位置连续性、绝对 RGB 距离和归一化颜色方向，避免交叉点附近从红线跳到蓝线。
8. 当前联合关联上限为 8 条候选；超过上限时停止自动输出并要求裁剪/拆图，避免把局部片段误报为完整曲线。

## 官方 Wilder 实图复核

- 来源：Wilder PCIe Gen 5 M.2 Socket 3 User Manual, 910-0077-000 Rev E, 2025-09-09：<https://wilder-tech.com/wp-content/uploads/2025/03/Wilder-PCIe-Gen-5-M2-Socket-3-User-Manual-910-0077-000-Rev-E-9-9-2025-Protected.pdf>
- Figure 36：四条可见曲线返回四条候选；加入颜色方向约束前会在红/蓝交叉附近产生第五个片段。
- Figure 37：没有把图例文字作为几何提取前提，仍返回四条候选。
- Figure 38：图中十多条曲线颜色重复且密集交叉，当前返回 dense-overlap 复核提示，不宣称自动恢复成功。
- 验证使用 PDF 页面原始渲染裁剪，没有在识别入口对图片降采样或压缩；超出解码像素安全上限的图片会被拒绝，而不是静默缩小。

## 未解决边界

- 完全同色、同线型且只在一个位置分开时，光栅本身不提供唯一身份；应保持部分曲线或人工确认。
- 十多条密集重叠线仍需要实例分割模型或人工裁剪；轻量经典视觉不能声称可靠逐条恢复。
- 相机拍摄导致透视、弯曲纸张或严重 JPEG 块效应，需要独立的几何矫正/质量评估，不应混入曲线跟踪器。

## 跨厂商产品图复核

本轮新增 8 张产品或器件资料中的插损图作为本机复核语料，覆盖 Samtec、JAE 与 Rosenberger。修复前只有 3/8 的物理曲线数量与人工目视一致；修复后 8/8 的图框与曲线数量均与冻结清单一致。清单位于 `tests/validation/cross_vendor_trace_recovery/cases.json`。

- Samtec CJT/C28S RF Characterization Report：5 张插损图。报告说明插损使用 S21，且三件样品只显示最小/最大曲线。来源：<https://suddendocs.samtec.com/testreports/rfc-report_cjt-c28s_web.pdf>
- JAE WP16RK 产品页：差分和 RF 两张插损图。来源：<https://products.jae.com/gl/en/connectors/content-library/featured-content/full-shield-btob-wp16rk/>
- Rosenberger Solderless PCB Mount Connectors：第 2 页插损图包含三条连接器曲线。来源：<https://www.rosenberger.com/fileadmin/content/headquarter/Downloads/RF_Coaxial_Connectors/TM_MWJ_SolderlessPCB_2013.pdf>

厂商图片及 PDF 受各自版权约束，不进入仓库。仓库只保存官方来源地址、尺寸、SHA-256、期望图框和期望曲线数量；实际复核由 `probe_cross_vendor_recovery.py` 对本机文件执行。图框和数量通过不等于每个像素点数值都已获得计量级精度，坐标标定与曲线映射仍须由用户复核。
