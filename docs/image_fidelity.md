# 图片曲线保真与纠错

本轮工作针对 2026-09-22 用户反馈的漏识别、错线及尖峰、凹口细节丢失。
验收对象是图片中可辨认的曲线及其导出数据；图片没有提供的相位、隐藏曲线
或仪器原始采样点不属于可恢复信息。手动方案沿用图框、排除区、原图取色、
锚点和导出复核流程；Windows 构建状态以公开仓库的 GitHub Actions 页面为准。

## 已知失败及验收方法

审查基线为 `43b26d54c7c7bc454b27a09b1098c68fb7525985`。同一自动
提取路径也存在于保存的修线分支 `44309acbcdad72aebd4248d8047a4b7b8cdc8c98`。

| 失败机制 | 本轮应观察到的行为 |
| --- | --- |
| 按列平均压平窄峰、长竖列被整列删掉 | 可辨认的尖端与局部二维路径保留；按栅格线宽和量化误差核对极值位置、深度及局部最大偏差。无法判明的区域显示需复核。 |
| 纯黑像素被排除、水平灰线被当网格删除 | 同一已知曲线更换为黑色或灰色仍能提取；空网格、坐标轴、短图例不能冒充曲线。 |
| 大图预览按固定间隔丢点 | 有界预览保留首尾和局部极值；只改变显示点选择，不改原始提取数组。 |
| 公共输出网格跨过窄凹口 | 在选定输出范围内报告与已识别路径的差异，提供合法的更细步进；由用户显式采用，不静默改网格。 |
| 局部严重错误被总体置信度隐藏 | 复核结果说明像素证据，不显示未经概率标定的准确率承诺。 |

原失败复现和独立验收入口保存在
[`tests/validation/image_fidelity_20260922/`](../tests/validation/image_fidelity_20260922/)。
解析构图给出的线位置是合成样例的几何真值；像素容差仅适用于相应线宽及
栅格化条件，不是厂商仪器精度或固定 dB 误差标准。

## 输出与复核边界

预览、识别原始点和 Touchstone 输出网格是三个不同对象。更细输出步进能减少
重采样遗漏，不能恢复在图片中或识别时已经丢失的细节。输出继续使用统一
频率网格，原有映射、范围、相位和无源性检查继续生效。实现入口分别为
[`DatasheetWorkspace`](../src/insertion_loss_tool/datasheet_workspace.py) 和
[`ImageExportReview`](../src/insertion_loss_tool/image_export_review.py)。

校准、修线、映射、输出网格、相位或阻抗变化后，前一次导出确认必须失效。
取色与锚点在原图坐标下保存，显示缩放不得改变源图或锚点坐标。人工约束与
插值区段保留来源分类，不能写成独立观测像素。

## 真实样本与验证范围

冻结产品图来源、SHA-256、图框和人工曲线计数见
[`cross_vendor_trace_recovery/cases.json`](../tests/validation/cross_vendor_trace_recovery/cases.json)。
这组 10 图来自四家厂商，计数合同不等于逐点准确度合同。Wilder Figure 36
另外核对已有物理像素锚点，见
[`probe_trace_identity.py`](../tests/validation/cross_vendor_trace_recovery/probe_trace_identity.py)
与 [`test_image_wilder_correction.py`](../tests/test_image_wilder_correction.py)。
这些是已用于开发和回归的样本，不声称是新的盲测集；厂商原图只保存在本地。

实际验收需完成 `gui_main.py` 的识图、校准、修线、映射、导出确认、文件生成
及独立 RI 回读，同时执行项目完整测试。macOS 的执行证据不能替代 Windows
WebView2 或 Windows EXE 验收；公开仓库的 Actions 日志记录自动构建结果。
