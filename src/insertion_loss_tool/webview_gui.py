"""pywebview desktop shell for Insertion Loss Tool.

The HTML document is shared by macOS WKWebView and Windows WebView2.  Python
remains responsible for validation, S-parameter calculations, file dialogs,
Touchstone I/O, and sampled-passivity checks; JavaScript only renders controls
and lightweight SVG plots.
"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 argparse，解析命令行参数，支持用户从终端覆盖默认配置。
import argparse
# Codex说明(自动生成)： 导入 json，读写结构化 JSON 配置或结果文件。
import json
# Codex说明(自动生成)： 导入 os，提供本文件后续流程需要的库能力。
import os
# Codex说明(自动生成)： 导入 subprocess，调用 git 或外部命令并读取返回结果。
import subprocess
# Codex说明(自动生成)： 导入 sys，访问解释器路径、退出码和标准错误输出。
import sys
# Codex说明(自动生成)： 导入 threading，提供本文件后续流程需要的库能力。
import threading
# Codex说明(自动生成)： 导入 time，提供本文件后续流程需要的库能力。
import time
# Codex说明(自动生成)： 从 collections.abc 导入 Iterable, Mapping, Sequence，提供本文件后续流程需要的库能力。
from collections.abc import Iterable, Mapping, Sequence
# Codex说明(自动生成)： 从 importlib.resources 导入 files，提供本文件后续流程需要的库能力。
from importlib.resources import files
# Codex说明(自动生成)： 从 pathlib 导入 Path，用 Path 对象处理跨平台文件路径。
from pathlib import Path
# Codex说明(自动生成)： 从 typing 导入 Any，提供类型标注辅助名称，方便维护和静态检查。
from typing import Any

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np

# Codex说明(自动生成)： 从 cli 导入 write_modification_report，提供本文件后续流程需要的库能力。
from .cli import write_modification_report
# Codex说明(自动生成)： 从 datasheet_workspace 导入 DatasheetWorkspace，提供本文件后续流程需要的库能力。
from .datasheet_workspace import DatasheetWorkspace
# Codex说明(自动生成)： 从 gui 导入 default_example_path, run_backend_self_test，提供本文件后续流程需要的库能力。
from .gui import default_example_path, run_self_test as run_backend_self_test
# Codex说明(自动生成)： 从 modify_input 导入 load_modify_input，提供本文件后续流程需要的库能力。
from .modify_input import load_modify_input
# Codex说明(自动生成)： 从 models 导入 COMMON_PORT_COUNTS, build_network, default_through_pairs, generate_frequency_axis 等名称，提供本文件后续流程需要的库能力。
from .models import (
    COMMON_PORT_COUNTS,
    build_network,
    default_through_pairs,
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
# Codex说明(自动生成)： 从 validation 导入 assert_sampled_passive，提供本文件后续流程需要的库能力。
from .validation import assert_sampled_passive


# Codex说明(自动生成)： 计算并保存 APP_NAME，供后续语句继续读取或更新。
APP_NAME = "Insertion Loss Tool"
# Codex说明(自动生成)： 计算并保存 RESPONSIVE_WINDOW_SIZE，供后续语句继续读取或更新。
RESPONSIVE_WINDOW_SIZE = (960, 640)
# Codex说明(自动生成)： 计算并保存 RESPONSIVE_NATIVE_FRAME_ALLOWANCE，供后续语句继续读取或更新。
RESPONSIVE_NATIVE_FRAME_ALLOWANCE = (20, 50)
# Codex说明(自动生成)： 计算并保存 RESPONSIVE_DRAW_HORIZONTAL_CHROME，供后续语句继续读取或更新。
RESPONSIVE_DRAW_HORIZONTAL_CHROME = 350
# The CSS mapping track is 220 px wide. Its 8 px padding and 1 px border on
# both sides leave a 202 px select; allow 2 px for native-control rounding.
MAPPING_SELECT_MIN_WIDTH = 200
# This must match the Web UI media query that changes Datasheet from three
# columns to two rows with the detail panel spanning both columns.
RESPONSIVE_LAYOUT_BREAKPOINT = 1050
# Codex说明(自动生成)： 计算并保存 WEB_UI_RESOURCE，供后续语句继续读取或更新。
WEB_UI_RESOURCE = "webui/index.html"
# Codex说明(自动生成)： 计算并保存 OUTPUT_DIR，供后续语句继续读取或更新。
OUTPUT_DIR = Path.home() / "Documents" / "InsertionLossToolOutputs"
# Codex说明(自动生成)： 计算并保存 REQUIRED_UI_TOKENS，供后续语句继续读取或更新。
REQUIRED_UI_TOKENS = (
    APP_NAME,
    "Generate and Modify S-Parameter",
    "Image to S-Parameter",
    "Digitize",
    "Formula",
    "Reciprocal",
    'id="add-images"',
    'id="remove-image"',
    'data-action="choose-images"',
    "backdrop-filter: blur",
    "radial-gradient",
)
# Codex说明(自动生成)： 计算并保存 FORBIDDEN_UI_TOKENS，供后续语句继续读取或更新。
FORBIDDEN_UI_TOKENS = (
    "常规生成",
    "图片组合",
    "协议公式",
    "成对联动",
    "添加图片",
    "互易网络",
    "导入图片",
    "＋ 图片",
    "家具组合",
    "线缆组合",
)
# Codex说明(自动生成)： 计算并保存 RENDERER_PROBE_SCRIPT，供后续语句继续读取或更新。
RENDERER_PROBE_SCRIPT = r"""
(() => {
  const initialViewportWidth = window.innerWidth;
  const app = document.querySelector('.app');
  const card = document.querySelector('.card');
  const outputPanel = document.querySelector('.asset-panel');
  const imagePanel = document.querySelector('.image-panel');
  const detailPanel = document.querySelector('.detail');
  const imagePreview = document.querySelector('.image-preview');
  const zoomDialog = document.querySelector('#image-zoom');
  const zoomLevel = document.querySelector('#zoom-level');
  const tabButtons = [...document.querySelectorAll('[data-tab]')];
  const modeButtons = [...document.querySelectorAll('[data-mode]')];
  const modelUnit = document.querySelector('#model-unit');
  const frequencyUnit = document.querySelector('#frequency-unit');
  const networkOutput = document.querySelector('#network-output');
  const frequencyPolicy = document.querySelector('#frequency-policy');
  const bridgeBefore = Number(window.insertionLossBridgeCalls || 0);
  const switchStart = performance.now();
  for (let index = 0; index < 100; index += 1) {
    tabButtons[1].click();
    tabButtons[0].click();
  }
  const switchMs = performance.now() - switchStart;
  tabButtons[1].click();
  const outputPanelHeight = outputPanel.getBoundingClientRect().height;
  const imagePanelWidth = imagePanel.getBoundingClientRect().width;
  const detailPanelWidth = detailPanel.getBoundingClientRect().width;
  const outputPanelWidth = outputPanel.getBoundingClientRect().width;
  const imagePreviewWidth = imagePreview.getBoundingClientRect().width;
  const imagePreviewHeight = imagePreview.getBoundingClientRect().height;
  const networkOutputWidth = networkOutput.getBoundingClientRect().width;
  const frequencyPolicyWidth = frequencyPolicy.getBoundingClientRect().width;
  zoomDialog.showModal();
  const zoomLevelBefore = zoomLevel.value;
  document.querySelector('#zoom-in').click();
  const zoomLevelAfter = zoomLevel.value;
  const zoomDialogOpen = zoomDialog.open;
  zoomDialog.close();
  tabButtons[0].click();
  modeButtons[2].click();
  const drawBoard = document.querySelector('#draw-board');
  const drawBoardRect = drawBoard.getBoundingClientRect();
  const controlPoints = document.querySelector('#control-points');
  const originalControlPoints = controlPoints.value;
  drawBoard.dispatchEvent(new MouseEvent('click', {
    bubbles: true,
    clientX: drawBoardRect.left + drawBoardRect.width * 62 / 900,
    clientY: drawBoardRect.top + drawBoardRect.height * 24 / 500
  }));
  const drawClickToken = controlPoints.value.split(',').at(-1).trim();
  const drawXAxis = drawBoard.querySelector('[data-draw-x-axis]');
  const drawXAxisBox = drawXAxis?.getBoundingClientRect();
  const drawCenterPoint = drawBoard.createSVGPoint();
  drawCenterPoint.x = (62 + 872) / 2;
  drawCenterPoint.y = 493;
  const drawCenterScreen = drawCenterPoint.matrixTransform(drawBoard.getScreenCTM());
  const drawXAxisCenterError = drawXAxisBox ? Math.abs((drawXAxisBox.left + drawXAxisBox.right) / 2 - drawCenterScreen.x) : 999;
  const drawAxisText = drawBoard.textContent || '';
  const drawTickUnits = [...drawBoard.querySelectorAll('[data-draw-x-tick]')].some(tick=>/[A-Za-z]/.test(tick.textContent || ''));
  controlPoints.value = originalControlPoints;
  controlPoints.dispatchEvent(new Event('input', {bubbles: true}));
  tabButtons[1].click();
  const outputList = document.querySelector('#network-list');
  const outputItems = [...document.querySelectorAll('.network-item')];
  const outputRect = outputList.getBoundingClientRect();
  const outputItemsClipped = outputItems.some(item => {
    const rect = item.getBoundingClientRect();
    return rect.top < outputRect.top - 1 || rect.bottom > outputRect.bottom + 1;
  });
  const originalOutputHtml = outputList.innerHTML;
  while (outputList.children.length < 6) {
    outputList.append(outputList.lastElementChild.cloneNode(true));
  }
  outputList.scrollTop = outputList.scrollHeight;
  const outputListRect = outputList.getBoundingClientRect();
  const lastOutputRect = outputList.lastElementChild.getBoundingClientRect();
  const maxOutputAccessible = lastOutputRect.top >= outputListRect.top - 1 &&
    lastOutputRect.bottom <= outputListRect.bottom + 1 &&
    outputListRect.bottom <= outputPanel.getBoundingClientRect().bottom + 1;
  outputList.innerHTML = originalOutputHtml;
  const mappingGrid = document.querySelector('#mapping-grid');
  const mappingGridTop = mappingGrid.getBoundingClientRect().top;
  const detailTop = detailPanel.getBoundingClientRect().top;
  const coverageStatus = document.querySelector('#coverage-status');
  const mappingSelectWidths = [...mappingGrid.querySelectorAll('select')]
    .map(select => select.getBoundingClientRect().width);
  const fakeTraceImage = {
    index: 1, name: 'same-source-color.png', data_url: 'data:image/png;base64,iVBORw0KGgo=', sha256: 'same-source-color', byte_count: 12,
    axis: {status:'ready',source:'detected',start:'10MHz',stop:'18GHz',step:'10MHz',spacing:'linear',y_min_db:-9,y_max_db:1},
    digitization: {status:'digitized',message:'2 traces',image_width:100,image_height:60,plot_box:[5,5,95,55]},
    curves: [
      {id:'A',parameter:'SDD21',color:'Magenta',rgb:[201,145,170],samples:5,observed_samples:5,preview_points:[[10,42],[45,28],[90,18]]},
      {id:'B',parameter:'SDD21',color:'Magenta',rgb:[201,145,170],samples:5,observed_samples:5,
       visual_confidence:0.72,review_status:'review',preview_points:[[10,44],[45,30],[90,20]],
       review_regions:[{start_x:42,end_x:49,reason:'interpolated',severity:'medium',samples:2,preview_points:[[42,31],[49,29]]}]}
    ]
  };
  const fakeCandidateImage = {
    index: 1, name: 'candidate-before-axes.png', data_url: 'data:image/png;base64,iVBORw0KGgo=', sha256: 'candidate-before-axes', byte_count: 12,
    axis: {status:'review',source:'none',start:'',stop:'',step:'',spacing:'linear'},
    digitization: {status:'review',candidate_status:'preview',candidates:2,message:'2 trace candidates found; set missing axes.'},
    curves: [
      {id:'A',parameter:'自动',color:'Magenta',rgb:[201,145,170],samples:5,observed_samples:5,calibrated:false,preview_points:[[10,42],[45,28],[90,18]]},
      {id:'B',parameter:'自动',color:'Cyan',rgb:[91,192,222],samples:5,observed_samples:5,calibrated:false,preview_points:[[10,44],[45,30],[90,20]]}
    ]
  };
  const fakeSources = ['自动','图1 A · SDD21','图1 B · SDD21','反射 -20 dB','耦合 -80 dB','未知'];
  const fakeMappings = {S11:'图1 A · SDD21',S12:'自动',S21:'自动',S22:'自动'};
  window.insertionLossUiProbe.render({images:[fakeCandidateImage], detected_parameters:[], source_options:['自动','匹配 0','反射 -20 dB','耦合 -80 dB'], networks:[]});
  const candidateTraceCount=document.querySelectorAll('[data-trace-row]').length;
  const candidateHasParameterSelect=Boolean(document.querySelector('[data-trace-row] select'));
  const candidateListStatus=document.querySelector('.image-item small:last-child')?.textContent.trim() || '';
  const candidateTitle=document.querySelector('#curve-title')?.textContent.trim() || '';
  const yConventionOptions=[...document.querySelector('#image-y-convention').options].map(option=>option.value);
  window.insertionLossUiProbe.render({
    images:[fakeTraceImage], detected_parameters:['SDD21'], source_options:fakeSources,
    networks:[{name:'输出 1',output:'output_1.s2p',port_count:2,parameter_family:'single-ended',reciprocal:false,
      frequency_policy:{mode:'intersection',start:'',stop:'',step:'',allow_fill:false},
      coverage:{status:'unresolved',start_hz:1e7,stop_hz:18e9,step_hz:1e7,points:1800,unresolved_channels:3,resampled_channels:0,uses_fill:false},
      mappings:fakeMappings,mapping_options:{S11:fakeSources,S12:fakeSources,S21:fakeSources,S22:fakeSources}}
    ]
  });
  const traceColors=[...document.querySelectorAll('[data-overlay-trace]')].map(item=>item.dataset.traceColor);
  const swatchColors=[...document.querySelectorAll('.curve-swatch')].map(item=>item.dataset.traceColor);
  const traceUsageTexts=[...document.querySelectorAll('.curve-usage')].map(item=>item.textContent.trim());
  const traceRows=[...document.querySelectorAll('[data-trace-row]')];
  traceRows[1]?.dispatchEvent(new MouseEvent('click',{bubbles:true}));
  const traceHighlightSelected=document.querySelector('[data-overlay-trace="B"]')?.style.strokeWidth === '4.5' &&
    document.querySelector('[data-overlay-trace="A"]')?.style.opacity === '0.16' && traceRows[1]?.classList.contains('active');
  const visualReviewOverlayCount=document.querySelectorAll('[data-overlay-review]').length;
  const visualReviewCardText=traceRows[1]?.querySelector('.curve-review')?.textContent.trim() || '';
  const visualReviewHelpText=document.querySelector('#visual-review-help')?.textContent.trim() || '';
  const visualReviewMappingHint=document.querySelector('#mapping-hint')?.textContent.trim() || '';
  const visualReviewHighlightSelected=document.querySelector('[data-overlay-review="B"]')?.style.strokeWidth === '8';
  const unassignedOptionText=[...document.querySelectorAll('[data-mapping]')].find(select=>select.value==='自动')?.selectedOptions[0]?.textContent.trim() || '';
  const bridgeBeforeUnassigned=Number(window.insertionLossBridgeCalls || 0);
  document.querySelector('#generate-network').click();
  const unassignedPreflightText=document.querySelector('#status').textContent.trim();
  const unassignedPreflightBridgeCalls=Number(window.insertionLossBridgeCalls || 0)-bridgeBeforeUnassigned;
  window.insertionLoss.receive({type: 'error', error: '正在生成。'});
  const translatedErrorText = document.querySelector('#status').textContent.trim();
  tabButtons[0].click();
  modeButtons[2].click();
  window.insertionLoss.receive({
    type: 'success', mode: 'draw', sigma_max: 1,
    plot: {
      frequency: [0.01, 40], unit: 'GHz',
      series: [
        {name: 'S11', magnitude: [-20, -20], phase: [-1080, 180]},
        {name: 'S12', magnitude: [-1, -5], phase: [-720, 0]},
        {name: 'S21', magnitude: [-1, -5], phase: [-720, 0]},
        {name: 'S22', magnitude: [-20, -20], phase: [-1080, 180]}
      ]
    }
  });
  const drawGeneratedPlotVisible=!document.querySelector('#plot-workspace').classList.contains('hidden') && document.querySelector('#draw-workspace').classList.contains('hidden');
  const drawGeneratedPlotCount=document.querySelectorAll('.plot-item').length;
  controlPoints.dispatchEvent(new Event('input',{bubbles:true}));
  const drawEditorRestored=!document.querySelector('#draw-workspace').classList.contains('hidden') && document.querySelector('#plot-workspace').classList.contains('hidden');
  modeButtons[0].click();
  const plotItems = [...document.querySelectorAll('.plot-item')];
  const tracePaths = plotItems.map(item => [...item.querySelectorAll('path')].at(-1)?.getAttribute('d') || '');
  const firstTraceY = tracePaths.map(path => Number((path.match(/^M[0-9.]+\s+([0-9.]+)/) || [])[1]));
  const plotSharedScaleGap = Math.abs(firstTraceY[0] - firstTraceY[1]);
  const plotAxisText = plotItems[0]?.querySelector('svg')?.textContent || '';
  const plotFrequencyTicks = [...(plotItems[0]?.querySelectorAll('[data-x-tick]') || [])].map(item=>Number(item.textContent));
  const plotMagnitudeTicks = [...(plotItems[0]?.querySelectorAll('[data-y-tick]') || [])].map(item=>Number(item.textContent));
  const plotXAxis = plotItems[0]?.querySelector('[data-x-unit]');
  const plotXAxisBox = plotXAxis?.getBoundingClientRect();
  const plotSvg = plotItems[0]?.querySelector('svg');
  const plotCenterPoint = plotSvg?.createSVGPoint();
  if (plotCenterPoint) { plotCenterPoint.x = (64 + 352) / 2; plotCenterPoint.y = 192; }
  const plotCenterScreen = plotCenterPoint?.matrixTransform(plotSvg.getScreenCTM());
  const plotXAxisCenterError = plotXAxisBox && plotCenterScreen ? Math.abs((plotXAxisBox.left + plotXAxisBox.right) / 2 - plotCenterScreen.x) : 999;
  const plotGridRect = document.querySelector('#plot-grid').getBoundingClientRect();
  const plotBottom = Math.max(...plotItems.map(item => item.getBoundingClientRect().bottom));
  const plotUnusedFraction = Math.max(0, plotGridRect.bottom - plotBottom) / Math.max(1, plotGridRect.height);
  const plotToolbarCount = document.querySelectorAll('[data-plot-action]').length;
  const plotToolbarIconCount = document.querySelectorAll('[data-plot-action] svg').length;
  const plotToolbarText = [...document.querySelectorAll('[data-plot-action]')].map(button=>button.textContent.trim()).join('');
  const plotInitialMode = document.querySelector('[data-plot-action].active')?.dataset.plotAction || '';
  const firstPlot = document.querySelector('.plot-item');
  const domainBefore = firstPlot?.dataset.domain || '';
  const firstSvg = firstPlot?.querySelector('svg');
  const firstSvgRect = firstSvg?.getBoundingClientRect();
  firstSvg?.dispatchEvent(new WheelEvent('wheel', {bubbles:true, cancelable:true, deltaY:-120, clientX:firstSvgRect.left+firstSvgRect.width/2, clientY:firstSvgRect.top+firstSvgRect.height/2}));
  const domainAfterWheel = document.querySelector('.plot-item')?.dataset.domain || '';
  document.querySelector('[data-plot-action="reset"]')?.click();
  const domainAfterReset = document.querySelector('.plot-item')?.dataset.domain || '';
  const panSvg = document.querySelector('.plot-item svg');
  const panRect = panSvg?.getBoundingClientRect();
  const domainBeforePan = document.querySelector('.plot-item')?.dataset.domain || '';
  panSvg?.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, button:0, clientX:panRect.left+panRect.width/2, clientY:panRect.top+panRect.height/2}));
  window.dispatchEvent(new PointerEvent('pointermove', {bubbles:true, clientX:panRect.left+panRect.width/2+30, clientY:panRect.top+panRect.height/2+15}));
  window.dispatchEvent(new PointerEvent('pointerup', {bubbles:true, clientX:panRect.left+panRect.width/2+30, clientY:panRect.top+panRect.height/2+15}));
  const plotPanChanged = document.querySelector('.plot-item')?.dataset.domain !== domainBeforePan;
  document.querySelector('[data-plot-action="reset"]')?.click();
  document.querySelector('[data-plot-action="zoom"]')?.click();
  const zoomPlotSvg = document.querySelector('.plot-item svg');
  const zoomPlotRect = zoomPlotSvg?.getBoundingClientRect();
  const domainBeforeBoxZoom = document.querySelector('.plot-item')?.dataset.domain || '';
  zoomPlotSvg?.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, button:0, clientX:zoomPlotRect.left+zoomPlotRect.width*.25, clientY:zoomPlotRect.top+zoomPlotRect.height*.25}));
  window.dispatchEvent(new PointerEvent('pointermove', {bubbles:true, clientX:zoomPlotRect.left+zoomPlotRect.width*.75, clientY:zoomPlotRect.top+zoomPlotRect.height*.75}));
  window.dispatchEvent(new PointerEvent('pointerup', {bubbles:true, clientX:zoomPlotRect.left+zoomPlotRect.width*.75, clientY:zoomPlotRect.top+zoomPlotRect.height*.75}));
  const plotBoxZoomChanged = document.querySelector('.plot-item')?.dataset.domain !== domainBeforeBoxZoom;
  document.querySelector('[data-plot-action="reset"]')?.click();
  document.querySelector('[data-plot="phase"]')?.click();
  const phaseItem = document.querySelector('.plot-item');
  const phaseUnit = phaseItem?.querySelector('[data-y-unit]')?.getBoundingClientRect();
  const phaseTicks = [...(phaseItem?.querySelectorAll('[data-y-tick]') || [])].map(item=>item.getBoundingClientRect());
  const plotPhaseTicks = [...(phaseItem?.querySelectorAll('[data-y-tick]') || [])].map(item=>Number(item.textContent));
  const phaseUnitOverlapsTicks = Boolean(phaseUnit && phaseTicks.some(tick => !(phaseUnit.right < tick.left || phaseUnit.left > tick.right || phaseUnit.bottom < tick.top || phaseUnit.top > tick.bottom)));
  const phaseAxisText = phaseItem?.querySelector('svg')?.textContent || '';
  return {
    initialViewportWidth,
    title: document.title,
    background: getComputedStyle(app).backgroundImage,
    backdrop: getComputedStyle(card).backdropFilter || getComputedStyle(card).webkitBackdropFilter || '',
    tabs: document.querySelectorAll('[data-tab]').length,
    tabLabels: tabButtons.map(button => button.textContent.trim()),
    activePanels: document.querySelectorAll('.workspace.active').length,
    switchMs,
    bridgeCalls: Number(window.insertionLossBridgeCalls || 0) - bridgeBefore,
    overflowFree: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    outputPanelHeight,
    imagePanelWidth,
    detailPanelWidth,
    outputPanelWidth,
    imagePreviewWidth,
    imagePreviewHeight,
    zoomLevelBefore,
    zoomLevelAfter,
    zoomDialogOpen,
    digitizeButton: Boolean(document.querySelector('#digitize-image')),
    networkOutputWidth,
    frequencyPolicyWidth,
    generatorPortOptions: [...document.querySelector('#ports').options].map(option => Number(option.value)),
    datasheetPortOptions: [...document.querySelector('#network-ports').options].map(option => Number(option.value)),
    modeLabels: modeButtons.map(button => button.textContent.trim()),
    wrappedModeLabels: modeButtons.filter(button => button.scrollHeight > button.clientHeight + 1 || getComputedStyle(button).whiteSpace !== 'nowrap').length,
    modelUnitLabels: [...modelUnit.options].map(option => option.textContent.trim()),
    frequencyUnitLabels: [...frequencyUnit.options].map(option => option.textContent.trim()),
    drawBoardWidth: drawBoardRect.width,
    drawBoardHeight: drawBoardRect.height,
    drawClickToken,
    drawAxisText,
    drawXAxisCenterError,
    drawTickUnits,
    drawGeneratedPlotVisible,
    drawGeneratedPlotCount,
    drawEditorRestored,
    outputItemCount: outputItems.length,
    outputItemsClipped,
    maxOutputAccessible,
    mappingGridTop,
    detailTop,
    detailHorizontalOverflow: detailPanel.scrollWidth > detailPanel.clientWidth + 1,
    coverageStatusClipped: coverageStatus.scrollWidth > coverageStatus.clientWidth + 1,
    mappingGridHorizontalOverflow: mappingGrid.scrollWidth > mappingGrid.clientWidth + 1,
    mappingSelectMinWidth: mappingSelectWidths.length ? Math.min(...mappingSelectWidths) : 0,
    traceColors,
    swatchColors,
    traceUsageTexts,
    traceHighlightSelected,
    visualReviewOverlayCount,
    visualReviewCardText,
    visualReviewHelpText,
    visualReviewMappingHint,
    visualReviewHighlightSelected,
    candidateTraceCount,
    candidateHasParameterSelect,
    candidateListStatus,
    candidateTitle,
    yConventionOptions,
    unassignedOptionText,
    unassignedPreflightText,
    unassignedPreflightBridgeCalls,
    plotSharedScaleGap,
    plotAxisText,
    plotFrequencyTicks,
    plotMagnitudeTicks,
    plotXAxisCenterError,
    plotUnusedFraction,
    plotToolbarCount,
    plotToolbarIconCount,
    plotToolbarText,
    plotInitialMode,
    plotWheelChanged: domainAfterWheel !== domainBefore,
    plotResetRestored: domainAfterReset === domainBefore,
    plotPanChanged,
    plotBoxZoomChanged,
    phaseUnitOverlapsTicks,
    phaseUnitRect: phaseUnit ? {left:phaseUnit.left,right:phaseUnit.right,top:phaseUnit.top,bottom:phaseUnit.bottom} : null,
    phaseTickRects: phaseTicks.map(tick=>({left:tick.left,right:tick.right,top:tick.top,bottom:tick.bottom})),
    plotPhaseTicks,
    phaseAxisText,
    generateNetworkButton: Boolean(document.querySelector('#generate-network')),
    imageOpenFolderButton: Boolean(document.querySelector('#open-image-output')),
    translatedErrorText,
    bodyHasHan: /[\u3400-\u9fff]/.test(document.body.innerText),
    webview2: Boolean(window.chrome && window.chrome.webview)
  };
})()
"""
# Codex说明(自动生成)： 计算并保存 RESPONSIVE_RENDERER_PROBE_SCRIPT，供后续语句继续读取或更新。
RESPONSIVE_RENDERER_PROBE_SCRIPT = """
(() => {
  const tabs = [...document.querySelectorAll('[data-tab]')];
  tabs[0].click();
  document.querySelector('[data-mode="draw"]').click();
  const drawRect = document.querySelector('#draw-board').getBoundingClientRect();
  tabs[1].click();
  const outputPanel = document.querySelector('.asset-panel');
  const outputList = document.querySelector('#network-list');
  const outputRect = outputList.getBoundingClientRect();
  const outputItems = [...document.querySelectorAll('.network-item')];
  const outputItemsClipped = outputItems.some(item => {
    const rect = item.getBoundingClientRect();
    return rect.top < outputRect.top - 1 || rect.bottom > outputRect.bottom + 1;
  });
  const originalOutputHtml = outputList.innerHTML;
  while (outputList.children.length < 6) {
    outputList.append(outputList.lastElementChild.cloneNode(true));
  }
  outputList.scrollTop = outputList.scrollHeight;
  const listRect = outputList.getBoundingClientRect();
  const lastRect = outputList.lastElementChild.getBoundingClientRect();
  const maxOutputAccessible = lastRect.top >= listRect.top - 1 &&
    lastRect.bottom <= listRect.bottom + 1 &&
    listRect.bottom <= outputPanel.getBoundingClientRect().bottom + 1;
  outputList.innerHTML = originalOutputHtml;
  const uiProbe = window.insertionLossUiProbe;
  const fakeImage = {
    index: 1, name: 'reimport-probe.png', data_url: 'data:image/png;base64,iVBORw0KGgo=',
    sha256: 'reimport-probe', axis: {status: 'required', source: 'none', start: '', stop: '', step: '', spacing: 'linear'},
    digitization: {status: 'axes-required', message: 'Axes required.'}, curves: []
  };
  uiProbe.render({images: [], networks: [], source_options: [], detected_parameters: []});
  uiProbe.render({images_added: [fakeImage], image_count: 1, networks: [], source_options: [], detected_parameters: []});
  uiProbe.render({image_removed: 1, image_updates: [], image_count: 0, networks: [], source_options: [], detected_parameters: []});
  uiProbe.render({images_added: [fakeImage], image_count: 1, networks: [], source_options: [], detected_parameters: []});
  uiProbe.rerender();
  const reimportImageCount = uiProbe.imageCount();
  return {
    responsiveViewportWidth: window.innerWidth,
    responsiveViewportHeight: window.innerHeight,
    responsiveDrawBoardWidth: drawRect.width,
    responsiveDrawBoardHeight: drawRect.height,
    responsiveOutputItemsClipped: outputItemsClipped,
    responsiveMaxOutputAccessible: maxOutputAccessible,
    responsiveOverflowFree: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    reimportImageCount
  };
})()
"""


# Codex说明(自动生成)： 定义函数 load_web_ui，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def load_web_ui() -> str:
    """Load the single packaged HTML/CSS/JS visual contract."""

    # Codex说明(自动生成)： 返回 files('insertion_loss_tool').joinpath(WEB_UI_RESOURCE)....，让调用方取得本函数的处理结果。
    return files("insertion_loss_tool").joinpath(WEB_UI_RESOURCE).read_text(encoding="utf-8")


# Codex说明(自动生成)： 定义函数 validate_web_ui_contract，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def validate_web_ui_contract(html: str | None = None) -> None:
    """Fail early if packaging or later edits break an approved UI contract."""

    # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
    source = html if html is not None else load_web_ui()
    # Codex说明(自动生成)： 计算并保存 missing，供后续语句继续读取或更新。
    missing = [token for token in REQUIRED_UI_TOKENS if token not in source]
    # Codex说明(自动生成)： 计算并保存 forbidden，供后续语句继续读取或更新。
    forbidden = [token for token in FORBIDDEN_UI_TOKENS if token in source]
    # Codex说明(自动生成)： 检查条件 source.count('data-action="choose-images"') != 1，根据结果选择后续执行路径。
    if source.count('data-action="choose-images"') != 1:
        # Codex说明(自动生成)： 调用 missing.append 更新列表或集合，把当前步骤产生的数据加入结果。
        missing.append("唯一图片入口")
    # Codex说明(自动生成)： 检查条件 missing or forbidden，根据结果选择后续执行路径。
    if missing or forbidden:
        # Codex说明(自动生成)： 声明并保存 details，同时保留类型信息方便维护和静态检查。
        details: list[str] = []
        # Codex说明(自动生成)： 检查条件 missing，根据结果选择后续执行路径。
        if missing:
            # Codex说明(自动生成)： 调用 details.append 更新列表或集合，把当前步骤产生的数据加入结果。
            details.append("缺少: " + ", ".join(missing))
        # Codex说明(自动生成)： 检查条件 forbidden，根据结果选择后续执行路径。
        if forbidden:
            # Codex说明(自动生成)： 调用 details.append 更新列表或集合，把当前步骤产生的数据加入结果。
            details.append("出现禁用文案: " + ", ".join(forbidden))
        # Codex说明(自动生成)： 抛出 RuntimeError('Web UI 合同无效（' + '；'.join(details) + '）')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Web UI 合同无效（" + "；".join(details) + "）")


# Codex说明(自动生成)： 定义函数 select_webview_backend，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def select_webview_backend(platform_name: str | None = None) -> str | None:
    """Force Edge WebView2 on Windows; macOS uses pywebview's WKWebView."""

    # Codex说明(自动生成)： 计算并保存 platform，供后续语句继续读取或更新。
    platform = platform_name or sys.platform
    # Codex说明(自动生成)： 返回 'edgechromium' if platform.startswith('win') else None，让调用方取得本函数的处理结果。
    return "edgechromium" if platform.startswith("win") else None


# Codex说明(自动生成)： 定义函数 validate_renderer_probe，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def validate_renderer_probe(
    probe: Mapping[str, object], platform_name: str | None = None
) -> None:
    """Validate essential properties in the real native web renderer."""

    # Codex说明(自动生成)： 计算并保存 platform，供后续语句继续读取或更新。
    platform = platform_name or sys.platform
    # Codex说明(自动生成)： 检查条件 probe.get('title') != APP_NAME，根据结果选择后续执行路径。
    if probe.get("title") != APP_NAME:
        # Codex说明(自动生成)： 抛出 RuntimeError('桌面界面标题未正确加载。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("桌面界面标题未正确加载。")
    # Codex说明(自动生成)： 检查条件 'gradient' not in str(probe.get('background', ''))，根据结果选择后续执行路径。
    if "gradient" not in str(probe.get("background", "")):
        # Codex说明(自动生成)： 抛出 RuntimeError('桌面背景未正确渲染。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("桌面背景未正确渲染。")
    # Codex说明(自动生成)： 检查条件 str(probe.get('backdrop', '')) in {'', 'none'}，根据结果选择后续执行路径。
    if str(probe.get("backdrop", "")) in {"", "none"}:
        # Codex说明(自动生成)： 抛出 RuntimeError('玻璃卡片未正确渲染。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("玻璃卡片未正确渲染。")
    # Codex说明(自动生成)： 检查条件 probe.get('tabs') != 2 or probe.get('activePanels') != 1，根据结果选择后续执行路径。
    if probe.get("tabs") != 2 or probe.get("activePanels") != 1:
        # Codex说明(自动生成)： 抛出 RuntimeError('页签状态不正确。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("页签状态不正确。")
    # Codex说明(自动生成)： 检查条件 probe.get('tabLabels') != ['Generate and Modify S-Param...，根据结果选择后续执行路径。
    if probe.get("tabLabels") != [
        "Generate and Modify S-Parameter",
        "Image to S-Parameter",
    ]:
        # Codex说明(自动生成)： 抛出 RuntimeError('页签名称未正确加载。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("页签名称未正确加载。")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('overflowFree'))，根据结果选择后续执行路径。
    if not bool(probe.get("overflowFree")):
        # Codex说明(自动生成)： 抛出 RuntimeError('界面出现横向溢出。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("界面出现横向溢出。")
    # Codex说明(自动生成)： 检查条件 probe.get('switchMs') is not None and float(probe['swit...，根据结果选择后续执行路径。
    if probe.get("switchMs") is not None and float(probe["switchMs"]) > 250.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('页签切换耗时异常。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("页签切换耗时异常。")
    # Codex说明(自动生成)： 检查条件 int(probe.get('bridgeCalls', 0)) != 0，根据结果选择后续执行路径。
    if int(probe.get("bridgeCalls", 0)) != 0:
        # Codex说明(自动生成)： 抛出 RuntimeError('页签切换不应调用 Python。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("页签切换不应调用 Python。")
    # Codex说明(自动生成)： 检查条件 not str(probe.get('modifyInputSummary', '')).startswith...，根据结果选择后续执行路径。
    if (
        not str(probe.get("modifyInputSummary", "")).startswith("Loaded formula_demo.s4p")
        or int(probe.get("modifyInputPorts", 0)) != 4
        or int(probe.get("modifyInputPoints", 0)) != 201
        or probe.get("modifyInputStart") != "10MHz"
        or probe.get("modifyInputStop") != "40GHz"
        or int(probe.get("modifyPlotCount", 0)) != 16
        or not bool(probe.get("modifyHasS44"))
        or int(probe.get("modifyBridgeCalls", 0)) < 1
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Modify 输入文件未刷新扫频元数据和 S 参数预览。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Modify 输入文件未刷新扫频元数据和 S 参数预览。")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('modifyInvalidErrorVisible')) or not...，根据结果选择后续执行路径。
    if not bool(probe.get("modifyInvalidErrorVisible")) or not bool(
        probe.get("modifyInvalidPlotCleared")
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Modify 无效输入文件错误不可见或仍显示陈旧预览。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Modify 无效输入文件错误不可见或仍显示陈旧预览。")
    # Codex说明(自动生成)： 计算并保存 expected_ports，供后续语句继续读取或更新。
    expected_ports = list(COMMON_PORT_COUNTS)
    # Codex说明(自动生成)： 检查条件 probe.get('generatorPortOptions') != expected_ports or ...，根据结果选择后续执行路径。
    if probe.get("generatorPortOptions") != expected_ports or probe.get(
        "datasheetPortOptions"
    ) != expected_ports:
        # Codex说明(自动生成)： 抛出 RuntimeError('两个页签的端口选项必须一致。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("两个页签的端口选项必须一致。")
    # Codex说明(自动生成)： 检查条件 probe.get('modeLabels') != ['Linear', 'Formula', 'Draw'...，根据结果选择后续执行路径。
    if probe.get("modeLabels") != ["Linear", "Formula", "Draw", "Modify"]:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generator mode labels are not the approve...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generator mode labels are not the approved English names.")
    # Codex说明(自动生成)： 检查条件 int(probe.get('wrappedModeLabels', 0)) != 0，根据结果选择后续执行路径。
    if int(probe.get("wrappedModeLabels", 0)) != 0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generator mode label wrapped onto multipl...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generator mode label wrapped onto multiple lines.")
    # Codex说明(自动生成)： 计算并保存 expected_units，供后续语句继续读取或更新。
    expected_units = ["GHz", "MHz", "kHz", "Hz"]
    # Codex说明(自动生成)： 检查条件 probe.get('modelUnitLabels') != expected_units or probe...，根据结果选择后续执行路径。
    if probe.get("modelUnitLabels") != expected_units or probe.get(
        "frequencyUnitLabels"
    ) != expected_units:
        # Codex说明(自动生成)： 抛出 RuntimeError('Visible frequency units must be GHz, MHz,...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Visible frequency units must be GHz, MHz, kHz, and Hz.")
    # Codex说明(自动生成)： 检查条件 float(probe.get('drawBoardWidth', 0.0)) < 600.0 or floa...，根据结果选择后续执行路径。
    if float(probe.get("drawBoardWidth", 0.0)) < 600.0 or float(
        probe.get("drawBoardHeight", 0.0)
    ) < 360.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Draw mode drawing area is too small.')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Draw mode drawing area is too small.")
    # Codex说明(自动生成)： 检查条件 probe.get('drawClickToken') != '10MHz:0'，根据结果选择后续执行路径。
    if probe.get("drawClickToken") != "10MHz:0":
        # Codex说明(自动生成)： 抛出 RuntimeError('Draw mode click coordinates do not match ...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Draw mode click coordinates do not match the plotted axes.")
    # Codex说明(自动生成)： 计算并保存 draw_axis_text，供后续语句继续读取或更新。
    draw_axis_text = str(probe.get("drawAxisText", ""))
    # Codex说明(自动生成)： 检查条件 'Magnitude (dB)' not in draw_axis_text or 'Frequency (G...，根据结果选择后续执行路径。
    if (
        "Magnitude (dB)" not in draw_axis_text
        or "Frequency (GHz)" not in draw_axis_text
        or bool(probe.get("drawTickUnits"))
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Draw mode axes do not match generated plo...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Draw mode axes do not match generated plot units.")
    # Codex说明(自动生成)： 检查条件 float(probe.get('drawXAxisCenterError', 999.0)) > 2.0，根据结果选择后续执行路径。
    if float(probe.get("drawXAxisCenterError", 999.0)) > 2.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Draw mode frequency-axis title is not cen...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Draw mode frequency-axis title is not centered.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('drawGeneratedPlotVisible')) or int(...，根据结果选择后续执行路径。
    if not bool(probe.get("drawGeneratedPlotVisible")) or int(
        probe.get("drawGeneratedPlotCount", 0)
    ) != 4:
        # Codex说明(自动生成)： 抛出 RuntimeError('Draw generation does not show the complet...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Draw generation does not show the complete S-parameter plots.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('drawEditorRestored'))，根据结果选择后续执行路径。
    if not bool(probe.get("drawEditorRestored")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Editing Draw control points does not rest...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Editing Draw control points does not restore the drawing board.")
    # Codex说明(自动生成)： 检查条件 int(probe.get('outputItemCount', 0)) < 1 or bool(probe....，根据结果选择后续执行路径。
    if int(probe.get("outputItemCount", 0)) < 1 or bool(
        probe.get("outputItemsClipped")
    ) or not bool(probe.get("maxOutputAccessible")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Datasheet output network list is clipped.')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Datasheet output network list is clipped.")
    # Codex说明(自动生成)： 检查条件 probe.get('mappingGridTop') is not None and probe.get('...，根据结果选择后续执行路径。
    if probe.get("mappingGridTop") is not None and probe.get("detailTop") is not None:
        # Codex说明(自动生成)： 检查条件 float(probe['mappingGridTop']) - float(probe['detailTop...，根据结果选择后续执行路径。
        if float(probe["mappingGridTop"]) - float(probe["detailTop"]) > 320.0:
            # Codex说明(自动生成)： 抛出 RuntimeError('Datasheet mappings are pushed below the v...，明确提示输入、状态或处理流程无法继续。
            raise RuntimeError("Datasheet mappings are pushed below the visible controls.")
    # Codex说明(自动生成)： 检查条件 probe.get('plotSharedScaleGap') is not None and float(p...，根据结果选择后续执行路径。
    if probe.get("plotSharedScaleGap") is not None and float(
        probe["plotSharedScaleGap"]
    ) < 50.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plots do not use a shared calib...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plots do not use a shared calibrated Y scale.")
    # Codex说明(自动生成)： 检查条件 probe.get('plotAxisText') is not None，根据结果选择后续执行路径。
    if probe.get("plotAxisText") is not None:
        # Codex说明(自动生成)： 计算并保存 axis_text，供后续语句继续读取或更新。
        axis_text = str(probe["plotAxisText"])
        # Codex说明(自动生成)： 检查条件 'dB' not in axis_text or 'GHz' not in axis_text，根据结果选择后续执行路径。
        if "dB" not in axis_text or "GHz" not in axis_text:
            # Codex说明(自动生成)： 抛出 RuntimeError('Generated plots are missing axis ticks or...，明确提示输入、状态或处理流程无法继续。
            raise RuntimeError("Generated plots are missing axis ticks or units.")
    # Codex说明(自动生成)： 检查条件 probe.get('plotFrequencyTicks') != [0, 10, 20, 30, 40]，根据结果选择后续执行路径。
    if probe.get("plotFrequencyTicks") != [0, 10, 20, 30, 40]:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plot frequency ticks are not en...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plot frequency ticks are not engineering-friendly.")
    # Codex说明(自动生成)： 检查条件 probe.get('plotMagnitudeTicks') != [-25, -20, -15, -10,...，根据结果选择后续执行路径。
    if probe.get("plotMagnitudeTicks") != [-25, -20, -15, -10, -5, 0]:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plot magnitude ticks are not en...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plot magnitude ticks are not engineering-friendly.")
    # Codex说明(自动生成)： 检查条件 float(probe.get('plotXAxisCenterError', 999.0)) > 2.0，根据结果选择后续执行路径。
    if float(probe.get("plotXAxisCenterError", 999.0)) > 2.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plot frequency-axis title is no...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plot frequency-axis title is not centered.")
    # Codex说明(自动生成)： 检查条件 float(probe.get('plotUnusedFraction', 1.0)) > 0.12，根据结果选择后续执行路径。
    if float(probe.get("plotUnusedFraction", 1.0)) > 0.12:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plots leave excessive unused ve...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plots leave excessive unused vertical space.")
    # Codex说明(自动生成)： 检查条件 int(probe.get('plotToolbarCount', 0)) != 3，根据结果选择后续执行路径。
    if int(probe.get("plotToolbarCount", 0)) != 3:
        # Codex说明(自动生成)： 抛出 RuntimeError('Plot toolbar must match ResponseLab zoom,...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Plot toolbar must match ResponseLab zoom, pan, and reset controls.")
    # Codex说明(自动生成)： 检查条件 int(probe.get('plotToolbarIconCount', 0)) != 3 or str(p...，根据结果选择后续执行路径。
    if (
        int(probe.get("plotToolbarIconCount", 0)) != 3
        or str(probe.get("plotToolbarText", ""))
        or probe.get("plotInitialMode") != "pan"
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Plot toolbar must use ResponseLab icon-on...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Plot toolbar must use ResponseLab icon-only controls with Pan selected.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('plotWheelChanged')) or not bool(pro...，根据结果选择后续执行路径。
    if (
        not bool(probe.get("plotWheelChanged"))
        or not bool(probe.get("plotResetRestored"))
        or not bool(probe.get("plotPanChanged"))
        or not bool(probe.get("plotBoxZoomChanged"))
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plot zoom, pan, or reset intera...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plot zoom, pan, or reset interaction did not change its view.")
    # Codex说明(自动生成)： 检查条件 bool(probe.get('phaseUnitOverlapsTicks')) or 'Phase (de...，根据结果选择后续执行路径。
    if bool(probe.get("phaseUnitOverlapsTicks")) or "Phase (deg)" not in str(
        probe.get("phaseAxisText", "")
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Phase unit overlaps the Y-axis tick label...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Phase unit overlaps the Y-axis tick labels.")
    # Codex说明(自动生成)： 检查条件 probe.get('plotPhaseTicks') != [-1440, -1080, -720, -36...，根据结果选择后续执行路径。
    if probe.get("plotPhaseTicks") != [-1440, -1080, -720, -360, 0, 360]:
        # Codex说明(自动生成)： 抛出 RuntimeError('Generated plot phase ticks are not engine...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Generated plot phase ticks are not engineering-friendly.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('generateNetworkButton'))，根据结果选择后续执行路径。
    if not bool(probe.get("generateNetworkButton")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Image to S-Parameter generation button is...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Image to S-Parameter generation button is missing.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('imageOpenFolderButton'))，根据结果选择后续执行路径。
    if not bool(probe.get("imageOpenFolderButton")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Image to S-Parameter Open Folder button i...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Image to S-Parameter Open Folder button is missing.")
    # Codex说明(自动生成)： 检查条件 bool(probe.get('bodyHasHan'))，根据结果选择后续执行路径。
    if bool(probe.get("bodyHasHan")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Rendered pages must use English UI copy.')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Rendered pages must use English UI copy.")
    # Codex说明(自动生成)： 检查条件 probe.get('translatedErrorText') != 'Generation is alre...，根据结果选择后续执行路径。
    if probe.get("translatedErrorText") != "Generation is already in progress.":
        # Codex说明(自动生成)： 抛出 RuntimeError('WebView error messages must be rendered i...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("WebView error messages must be rendered in English.")
    # Codex说明(自动生成)： 计算并保存 responsive_width，供后续语句继续读取或更新。
    responsive_width = float(probe.get("responsiveViewportWidth", 0.0))
    # Codex说明(自动生成)： 计算并保存 responsive_height，供后续语句继续读取或更新。
    responsive_height = float(probe.get("responsiveViewportHeight", 0.0))
    # Codex说明(自动生成)： 计算并保存 requested_width，供后续语句继续读取或更新。
    requested_width = int(probe.get("responsiveRequestedWindowWidth", 0))
    # Codex说明(自动生成)： 计算并保存 requested_height，供后续语句继续读取或更新。
    requested_height = int(probe.get("responsiveRequestedWindowHeight", 0))
    # Codex说明(自动生成)： 检查条件 (requested_width, requested_height) != RESPONSIVE_WINDO...，根据结果选择后续执行路径。
    if (requested_width, requested_height) != RESPONSIVE_WINDOW_SIZE:
        # Codex说明(自动生成)： 抛出 RuntimeError('Responsive renderer probe did not request...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Responsive renderer probe did not request the 960x640 window.")
    # Codex说明(自动生成)： 计算并保存 minimum_client_width，供后续语句继续读取或更新。
    minimum_client_width = requested_width - RESPONSIVE_NATIVE_FRAME_ALLOWANCE[0]
    # Codex说明(自动生成)： 计算并保存 minimum_client_height，供后续语句继续读取或更新。
    minimum_client_height = requested_height - RESPONSIVE_NATIVE_FRAME_ALLOWANCE[1]
    # Codex说明(自动生成)： 检查条件 not minimum_client_width <= responsive_width <= request...，根据结果选择后续执行路径。
    if not minimum_client_width <= responsive_width <= requested_width or not (
        minimum_client_height <= responsive_height <= requested_height
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError(f'Responsive renderer probe did not reach ...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError(
            "Responsive renderer probe did not reach the bounded 960x640 client viewport "
            f"(actual {responsive_width:g}x{responsive_height:g})."
        )
    # Codex说明(自动生成)： 计算并保存 responsive_draw_width，供后续语句继续读取或更新。
    responsive_draw_width = float(probe.get("responsiveDrawBoardWidth", 0.0))
    # Codex说明(自动生成)： 计算并保存 responsive_draw_height，供后续语句继续读取或更新。
    responsive_draw_height = float(probe.get("responsiveDrawBoardHeight", 0.0))
    # Codex说明(自动生成)： 计算并保存 minimum_draw_width，供后续语句继续读取或更新。
    minimum_draw_width = max(
        0.0, responsive_width - RESPONSIVE_DRAW_HORIZONTAL_CHROME
    )
    # Codex说明(自动生成)： 检查条件 responsive_draw_width < minimum_draw_width or responsiv...，根据结果选择后续执行路径。
    if responsive_draw_width < minimum_draw_width or responsive_draw_height < 360.0:
        # Codex说明(自动生成)： 抛出 RuntimeError(f'Responsive Draw mode drawing area is too...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError(
            "Responsive Draw mode drawing area is too small "
            f"(actual {responsive_draw_width:g}x{responsive_draw_height:g}, "
            f"minimum {minimum_draw_width:g}x360)."
        )
    # Codex说明(自动生成)： 检查条件 bool(probe.get('responsiveOutputItemsClipped')) or not ...，根据结果选择后续执行路径。
    if bool(probe.get("responsiveOutputItemsClipped")) or not bool(
        probe.get("responsiveMaxOutputAccessible")
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('Responsive Datasheet output network list ...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Responsive Datasheet output network list is clipped.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('responsiveOverflowFree'))，根据结果选择后续执行路径。
    if not bool(probe.get("responsiveOverflowFree")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Responsive interface has horizontal overf...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Responsive interface has horizontal overflow.")
    # Codex说明(自动生成)： 检查条件 int(probe.get('reimportImageCount', 0)) != 1，根据结果选择后续执行路径。
    if int(probe.get("reimportImageCount", 0)) != 1:
        # Codex说明(自动生成)： 抛出 RuntimeError('Removed image could not be re-imported in...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Removed image could not be re-imported in the rendered interface.")
    # Codex说明(自动生成)： 检查条件 bool(probe.get('detailHorizontalOverflow'))，根据结果选择后续执行路径。
    if bool(probe.get("detailHorizontalOverflow")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Datasheet detail panel has horizontal ove...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Datasheet detail panel has horizontal overflow.")
    # Codex说明(自动生成)： 检查条件 bool(probe.get('coverageStatusClipped'))，根据结果选择后续执行路径。
    if bool(probe.get("coverageStatusClipped")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Datasheet coverage status is clipped.')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Datasheet coverage status is clipped.")
    # Codex说明(自动生成)： 检查条件 bool(probe.get('mappingGridHorizontalOverflow'))，根据结果选择后续执行路径。
    if bool(probe.get("mappingGridHorizontalOverflow")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Datasheet mapping grid has horizontal ove...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Datasheet mapping grid has horizontal overflow.")
    # Measure the usable select itself, not the 220 px outer CSS grid track.
    mapping_select_width = float(probe.get("mappingSelectMinWidth", 0.0))
    # Codex说明(自动生成)： 检查条件 mapping_select_width < MAPPING_SELECT_MIN_WIDTH，根据结果选择后续执行路径。
    if mapping_select_width < MAPPING_SELECT_MIN_WIDTH:
        # Codex说明(自动生成)： 抛出 RuntimeError(f'Datasheet mapping selector is too narrow...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError(
            "Datasheet mapping selector is too narrow to read "
            f"(actual {mapping_select_width:g}px, minimum {MAPPING_SELECT_MIN_WIDTH}px)."
        )
    # Codex说明(自动生成)： 计算并保存 trace_colors，供后续语句继续读取或更新。
    trace_colors = list(probe.get("traceColors", []))
    # Codex说明(自动生成)： 检查条件 len(trace_colors) < 2 or len(set(trace_colors)) != len(...，根据结果选择后续执行路径。
    if len(trace_colors) < 2 or len(set(trace_colors)) != len(trace_colors):
        # Codex说明(自动生成)： 抛出 RuntimeError('Detected image traces do not use distinct...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Detected image traces do not use distinct display colors.")
    # Codex说明(自动生成)： 检查条件 list(probe.get('swatchColors', [])) != trace_colors，根据结果选择后续执行路径。
    if list(probe.get("swatchColors", [])) != trace_colors:
        # Codex说明(自动生成)： 抛出 RuntimeError('Detected trace swatches do not match thei...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Detected trace swatches do not match their overlay colors.")
    # Codex说明(自动生成)： 检查条件 not bool(probe.get('traceHighlightSelected'))，根据结果选择后续执行路径。
    if not bool(probe.get("traceHighlightSelected")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Selecting a detected trace does not isola...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Selecting a detected trace does not isolate its image overlay.")
    if (
        int(probe.get("visualReviewOverlayCount", 0)) != 1
        or probe.get("visualReviewCardText")
        != "Review 1 highlighted area · 72% confidence"
        or probe.get("visualReviewHelpText")
        != "Orange dashed areas need visual review · 1 highlighted"
        or probe.get("visualReviewMappingHint")
        != "2 traces available · 1 need highlighted-area review · detected labels are hints"
        or not bool(probe.get("visualReviewHighlightSelected"))
    ):
        raise RuntimeError("图片识别局部风险区未在真实界面中正确显示或联动高亮。")
    # Codex说明(自动生成)： 检查条件 probe.get('unassignedOptionText') != 'Unassigned'，根据结果选择后续执行路径。
    if probe.get("unassignedOptionText") != "Unassigned":
        # Codex说明(自动生成)： 抛出 RuntimeError('An unassigned image mapping is mislabeled...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("An unassigned image mapping is mislabeled as a default curve.")
    # Codex说明(自动生成)： 计算并保存 expected_unassigned，供后续语句继续读取或更新。
    expected_unassigned = (
        "Unassigned channels: S12, S21, S22. Choose a detected trace, "
        "Matched · exact zero, Return loss −20 dB, or Crosstalk −80 dB."
    )
    # Codex说明(自动生成)： 检查条件 probe.get('unassignedPreflightText') != expected_unassi...，根据结果选择后续执行路径。
    if probe.get("unassignedPreflightText") != expected_unassigned or int(
        probe.get("unassignedPreflightBridgeCalls", -1)
    ) != 0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Image generation does not explain unassig...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Image generation does not explain unassigned channels before export.")
    if (
        int(probe.get("candidateTraceCount", 0)) != 2
        or bool(probe.get("candidateHasParameterSelect"))
        or probe.get("candidateListStatus") != "2 trace candidates · Calibrate axes"
        or probe.get("candidateTitle") != "Trace Candidates · 2"
    ):
        raise RuntimeError(
            "Uncalibrated image trace candidates are not visible and safely disabled in the rendered interface."
        )
    if probe.get("traceUsageTexts") != [
        "Used by Output 1 S11",
        "Not used · choose it in the S-parameter panel",
    ]:
        raise RuntimeError(
            "Detected trace cards do not show read-only S-parameter usage."
        )
    if probe.get("yConventionOptions") != ["magnitude", "positive-loss"]:
        raise RuntimeError("Image axis controls do not expose both S-parameter and positive-loss conventions.")
    # Codex说明(自动生成)： 检查条件 probe.get('imagePreviewWidth') is not None and float(pr...，根据结果选择后续执行路径。
    if probe.get("imagePreviewWidth") is not None and float(probe["imagePreviewWidth"]) < 360.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('图片预览区域过窄。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片预览区域过窄。")
    # Codex说明(自动生成)： 检查条件 probe.get('imagePreviewHeight') is not None and float(p...，根据结果选择后续执行路径。
    if probe.get("imagePreviewHeight") is not None and float(probe["imagePreviewHeight"]) < 360.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('图片预览区域过矮。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片预览区域过矮。")
    # Codex说明(自动生成)： 检查条件 probe.get('imagePanelWidth') is not None and probe.get(...，根据结果选择后续执行路径。
    if (
        probe.get("imagePanelWidth") is not None
        and probe.get("imagePreviewWidth") is not None
        and float(probe["imagePanelWidth"]) <= float(probe["imagePreviewWidth"])
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('图片列表与预览布局无效。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片列表与预览布局无效。")
    # Codex说明(自动生成)： 检查条件 probe.get('digitizeButton') is False，根据结果选择后续执行路径。
    if probe.get("digitizeButton") is False:
        # Codex说明(自动生成)： 抛出 RuntimeError('图片识别按钮缺失。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片识别按钮缺失。")
    # Codex说明(自动生成)： 计算并保存 initial_viewport_width，供后续语句继续读取或更新。
    initial_viewport_width = float(probe.get("initialViewportWidth", 0.0))
    # Codex说明(自动生成)： 检查条件 initial_viewport_width <= 0.0，根据结果选择后续执行路径。
    if initial_viewport_width <= 0.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('Renderer probe did not report its initial...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Renderer probe did not report its initial viewport width.")
    # The desktop-only ratio must not be applied after the CSS media query
    # intentionally moves the detail panel below and spans it across both columns.
    if (
        initial_viewport_width > RESPONSIVE_LAYOUT_BREAKPOINT
        and probe.get("imagePanelWidth") is not None
        and probe.get("detailPanelWidth") is not None
        and float(probe["imagePanelWidth"]) <= float(probe["detailPanelWidth"]) * 1.15
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError(f'图片工作区必须明显宽于输出配置区 (viewport {initial_view...，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError(
            "图片工作区必须明显宽于输出配置区 "
            f"(viewport {initial_viewport_width:g}px)."
        )
    # Codex说明(自动生成)： 检查条件 probe.get('outputPanelWidth') is not None and probe.get...，根据结果选择后续执行路径。
    if (
        probe.get("outputPanelWidth") is not None
        and probe.get("imagePanelWidth") is not None
        and float(probe["outputPanelWidth"]) >= float(probe["imagePanelWidth"]) * 0.4
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('输出列表占用空间过大。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("输出列表占用空间过大。")
    # Codex说明(自动生成)： 检查条件 probe.get('networkOutputWidth') is not None and float(p...，根据结果选择后续执行路径。
    if probe.get("networkOutputWidth") is not None and float(
        probe["networkOutputWidth"]
    ) < 260.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('输出文件字段过窄。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("输出文件字段过窄。")
    # Codex说明(自动生成)： 检查条件 probe.get('frequencyPolicyWidth') is not None and float...，根据结果选择后续执行路径。
    if probe.get("frequencyPolicyWidth") is not None and float(
        probe["frequencyPolicyWidth"]
    ) < 145.0:
        # Codex说明(自动生成)： 抛出 RuntimeError('频率范围字段过窄。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("频率范围字段过窄。")
    # Codex说明(自动生成)： 检查条件 probe.get('zoomDialogOpen') is False or (probe.get('zoo...，根据结果选择后续执行路径。
    if probe.get("zoomDialogOpen") is False or (
        probe.get("zoomLevelBefore") is not None
        and probe.get("zoomLevelAfter") == probe.get("zoomLevelBefore")
    ):
        # Codex说明(自动生成)： 抛出 RuntimeError('图片缩放控件未生效。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片缩放控件未生效。")
    # Codex说明(自动生成)： 检查条件 probe.get('zoomWidthBefore') is not None and float(prob...，根据结果选择后续执行路径。
    if (
        probe.get("zoomWidthBefore") is not None
        and float(probe.get("zoomWidthAfter", 0.0)) <= float(probe["zoomWidthBefore"])
    ) or probe.get("zoomScrollable") is False:
        # Codex说明(自动生成)： 抛出 RuntimeError('图片放大或平移区域未生效。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片放大或平移区域未生效。")
    # Codex说明(自动生成)： 检查条件 platform.startswith('win') and (not bool(probe.get('web...，根据结果选择后续执行路径。
    if platform.startswith("win") and not bool(probe.get("webview2")):
        # Codex说明(自动生成)： 抛出 RuntimeError('Windows 未使用 Edge WebView2 渲染器。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Windows 未使用 Edge WebView2 渲染器。")


# Codex说明(自动生成)： 定义函数 _split_text_values，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _split_text_values(value: object) -> list[str]:
    # Codex说明(自动生成)： 声明并保存 values，同时保留类型信息方便维护和静态检查。
    values: list[str] = []
    # Codex说明(自动生成)： 遍历 str(value or '').splitlines() 中的 line，逐项执行循环体逻辑。
    for line in str(value or "").splitlines():
        # Codex说明(自动生成)： 调用 values.extend 更新列表或集合，把当前步骤产生的数据加入结果。
        values.extend(part.strip() for part in line.split(",") if part.strip())
    # Codex说明(自动生成)： 返回 values，让调用方取得本函数的处理结果。
    return values


# Codex说明(自动生成)： 定义 InsertionLossWebApi 类，把相关数据结构、校验规则或操作方法组织在一起。
class InsertionLossWebApi:
    """Thread-safe controller exposed through a deliberately small JS facade."""

    # Codex说明(自动生成)： 定义函数 __init__，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def __init__(self) -> None:
        # Codex说明(自动生成)： 声明并保存 self._window，同时保留类型信息方便维护和静态检查。
        self._window: Any | None = None
        # Codex说明(自动生成)： 计算并保存 self._state_lock，供后续语句继续读取或更新。
        self._state_lock = threading.RLock()
        # Codex说明(自动生成)： 计算并保存 self._run_lock，供后续语句继续读取或更新。
        self._run_lock = threading.Lock()
        # Codex说明(自动生成)： 计算并保存 self._output_lock，供后续语句继续读取或更新。
        self._output_lock = threading.Lock()
        # Codex说明(自动生成)： 计算并保存 self._running，供后续语句继续读取或更新。
        self._running = False
        # Codex说明(自动生成)： 声明并保存 self._last_output，同时保留类型信息方便维护和静态检查。
        self._last_output: Path | None = None
        # Codex说明(自动生成)： 声明并保存 self._last_datasheet_output，同时保留类型信息方便维护和静态检查。
        self._last_datasheet_output: Path | None = None
        # Codex说明(自动生成)： 计算并保存 self._datasheet，供后续语句继续读取或更新。
        self._datasheet = DatasheetWorkspace()

    # Codex说明(自动生成)： 定义函数 bind_window，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def bind_window(self, window: Any) -> None:
        # Codex说明(自动生成)： 计算并保存 self._window，供后续语句继续读取或更新。
        self._window = window

    # Codex说明(自动生成)： 定义函数 get_defaults，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def get_defaults(self) -> dict[str, object]:
        """Return engineering-safe defaults and the current datasheet state."""

        # Codex说明(自动生成)： 返回 {'mode': 'linear', 'ports': '2', 'port_options': list(C...，让调用方取得本函数的处理结果。
        return {
            "mode": "linear",
            "ports": "2",
            "port_options": list(COMMON_PORT_COUNTS),
            "f_start": "10MHz",
            "f_stop": "40GHz",
            "points": "801",
            "spacing": "linear",
            "format": "ri",
            "frequency_unit": "ghz",
            "return_loss_db": "20.0",
            "crosstalk_db": "80.0",
            "delay_ps": "80.0",
            "phase_offset_deg": "0.0",
            "z0": "50.0",
            "through_pairs": "",
            "output": "",
            "overwrite": False,
            "linear": {"loss_start_db": "0.2", "loss_stop_db": "20.0"},
            "formula": {"a": "0.08", "b": "0.6", "c": "0.1", "model_frequency_unit": "ghz"},
            "draw": {
                "control_points": "",
                "loss_min_db": "-40.0",
                "loss_max_db": "0.0",
                "fit": "smooth",
                "fit_domain": "linear",
                "min_spacing_fraction": "0.0001",
                "max_slope_db_per_span": "500.0",
            },
            "modify": {
                "input": str(default_example_path()),
                "targets": "5GHz:3.0,12GHz:8.0",
                "pairs": "S21,S12",
                "smoothness": "0.14",
                "smooth_domain": "log",
                "anchor_edges": True,
                "insert_targets": True,
            },
            "datasheet": self._datasheet.payload(),
        }

    # Codex说明(自动生成)： 定义函数 choose_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_output(self, ports: object = 2) -> dict[str, object]:
        # Codex说明(自动生成)： 检查条件 self._window is None，根据结果选择后续执行路径。
        if self._window is None:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '窗口尚未准备好。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "窗口尚未准备好。"}
        # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
        import webview

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 count，供后续语句继续读取或更新。
            count = int(ports)
        # Codex说明(自动生成)： 捕获 (TypeError, ValueError)，执行对应的恢复、记录或重新报错逻辑。
        except (TypeError, ValueError):
            # Codex说明(自动生成)： 计算并保存 count，供后续语句继续读取或更新。
            count = 2
        # Codex说明(自动生成)： 计算并保存 selected，供后续语句继续读取或更新。
        selected = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=f"insertion_loss.s{count}p",
            file_types=(f"Touchstone (*.s{count}p)",),
        )
        # Codex说明(自动生成)： 检查条件 not selected，根据结果选择后续执行路径。
        if not selected:
            # Codex说明(自动生成)： 返回 {'ok': True, 'cancelled': True}，让调用方取得本函数的处理结果。
            return {"ok": True, "cancelled": True}
        # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
        value = selected[0] if isinstance(selected, (list, tuple)) else selected
        # Codex说明(自动生成)： 返回 {'ok': True, 'path': str(Path(value).expanduser().resol...，让调用方取得本函数的处理结果。
        return {"ok": True, "path": str(Path(value).expanduser().resolve())}

    # Codex说明(自动生成)： 定义函数 choose_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_input(self) -> dict[str, object]:
        # Codex说明(自动生成)： 检查条件 self._window is None，根据结果选择后续执行路径。
        if self._window is None:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '窗口尚未准备好。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "窗口尚未准备好。"}
        # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
        import webview

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 selected，供后续语句继续读取或更新。
            selected = self._window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False,
                file_types=("Touchstone (*.s1p;*.s2p;*.s3p;*.s4p;*.s5p;*.s6p;*.s7p;*.s8p)",),
            )
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception:  # Native picker failures vary by pywebview backend.
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '无法打开 Touchstone 选择窗口，请重试。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "无法打开 Touchstone 选择窗口，请重试。"}
        # Codex说明(自动生成)： 检查条件 not selected，根据结果选择后续执行路径。
        if not selected:
            # Codex说明(自动生成)： 返回 {'ok': True, 'cancelled': True}，让调用方取得本函数的处理结果。
            return {"ok": True, "cancelled": True}
        # Codex说明(自动生成)： 计算并保存 value，供后续语句继续读取或更新。
        value = selected[0] if isinstance(selected, (list, tuple)) else selected
        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = Path(value).expanduser().resolve()
        # Codex说明(自动生成)： 返回 {'ok': True, 'path': str(path), 'name': path.name}，让调用方取得本函数的处理结果。
        return {"ok": True, "path": str(path), "name": path.name}

    # Codex说明(自动生成)： 定义函数 inspect_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def inspect_input(
        self, path: object, frequency_unit: object = "ghz"
    ) -> dict[str, object]:
        """Read a Modify source and return metadata plus a plot-ready preview."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
            source = load_modify_input(path)
            # Codex说明(自动生成)： 返回 {'ok': True, 'path': str(source.path), 'name': source.p...，让调用方取得本函数的处理结果。
            return {
                "ok": True,
                "path": str(source.path),
                "name": source.path.name,
                "ports": source.ports,
                "points": source.points,
                "start_hz": source.start_hz,
                "stop_hz": source.stop_hz,
                "plot": self._plot_payload(source.data, str(frequency_unit)),
            }
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception as exc:  # noqa: BLE001 - bridge errors must be visible.
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(exc) or exc.__class__.__name__}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(exc) or exc.__class__.__name__}

    # Codex说明(自动生成)： 定义函数 choose_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_images(self) -> dict[str, object]:
        # Codex说明(自动生成)： 检查条件 self._window is None，根据结果选择后续执行路径。
        if self._window is None:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '窗口尚未准备好。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "窗口尚未准备好。"}
        # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
        import webview

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 selected，供后续语句继续读取或更新。
            selected = self._window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=True,
                file_types=("Images (*.png;*.jpg;*.jpeg;*.gif;*.webp)",),
            )
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception:  # Native picker failures vary by pywebview backend.
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '无法打开图片选择窗口，请重试。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "无法打开图片选择窗口，请重试。"}
        # Codex说明(自动生成)： 检查条件 not selected，根据结果选择后续执行路径。
        if not selected:
            # Codex说明(自动生成)： 返回 {'ok': True, 'cancelled': True}，让调用方取得本函数的处理结果。
            return {"ok": True, "cancelled": True}
        # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
        values = selected if isinstance(selected, (list, tuple)) else (selected,)
        # Codex说明(自动生成)： 返回 self.register_images((Path(value) for value in values))，让调用方取得本函数的处理结果。
        return self.register_images(Path(value) for value in values)

    # Codex说明(自动生成)： 定义函数 register_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def register_images(self, paths: Iterable[Path]) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.register_images(paths)，让调用方取得本函数的处理结果。
        return self._datasheet.register_images(paths)

    # Codex说明(自动生成)： 定义函数 remove_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def remove_image(self, index: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.remove_image(index)，让调用方取得本函数的处理结果。
        return self._datasheet.remove_image(index)

    # Codex说明(自动生成)： 定义函数 analyze_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def analyze_image(self, index: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.analyze_image(index)，让调用方取得本函数的处理结果。
        return self._datasheet.analyze_image(index)

    # Codex说明(自动生成)： 定义函数 set_image_frequency，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_image_frequency(
        self,
        index: object,
        start: object,
        stop: object,
        step: object,
        spacing: object = "linear",
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_image_frequency(index, start, stop,...，让调用方取得本函数的处理结果。
        return self._datasheet.set_image_frequency(index, start, stop, step, spacing)

    # Codex说明(自动生成)： 定义函数 digitize_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def digitize_image(
        self, index: object, y_min_db: object, y_max_db: object
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.digitize_image(index, y_min_db, y_max_db)，让调用方取得本函数的处理结果。
        return self._datasheet.digitize_image(index, y_min_db, y_max_db)

    def digitize_image_with_axis(
        self,
        index: object,
        y_top_db: object,
        y_bottom_db: object,
        convention: object,
    ) -> dict[str, object]:
        return self._datasheet.digitize_image_with_axis(
            index, y_top_db, y_bottom_db, convention
        )

    # Codex说明(自动生成)： 定义函数 set_curve_parameter，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_curve_parameter(
        self, index: object, curve_id: object, parameter: object
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_curve_parameter(index, curve_id, pa...，让调用方取得本函数的处理结果。
        return self._datasheet.set_curve_parameter(index, curve_id, parameter)

    # Codex说明(自动生成)： 定义函数 set_network_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_count(self, count: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_network_count(count)，让调用方取得本函数的处理结果。
        return self._datasheet.set_network_count(count)

    # Codex说明(自动生成)： 定义函数 set_network_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_ports(self, index: object, ports: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_network_ports(index, ports)，让调用方取得本函数的处理结果。
        return self._datasheet.set_network_ports(index, ports)

    # Codex说明(自动生成)： 定义函数 set_network_parameter_family，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_parameter_family(self, index: object, family: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_network_parameter_family(index, fam...，让调用方取得本函数的处理结果。
        return self._datasheet.set_network_parameter_family(index, family)

    # Codex说明(自动生成)： 定义函数 set_network_frequency_policy，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_frequency_policy(
        self,
        index: object,
        mode: object,
        start: object = "",
        stop: object = "",
        step: object = "",
        allow_fill: object = False,
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_network_frequency_policy(index, mod...，让调用方取得本函数的处理结果。
        return self._datasheet.set_network_frequency_policy(
            index, mode, start, stop, step, allow_fill
        )

    # Codex说明(自动生成)： 定义函数 set_network_reciprocal，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_reciprocal(self, index: object, enabled: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_network_reciprocal(index, enabled)，让调用方取得本函数的处理结果。
        return self._datasheet.set_network_reciprocal(index, enabled)

    # Codex说明(自动生成)： 定义函数 set_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_mapping(self, index: object, parameter: object, source: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._datasheet.set_mapping(index, parameter, source)，让调用方取得本函数的处理结果。
        return self._datasheet.set_mapping(index, parameter, source)

    # Codex说明(自动生成)： 定义函数 generate_datasheet_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def generate_datasheet_network(self, index: object) -> dict[str, object]:
        """Generate the selected image-composed network as a Touchstone file."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 (data, output_name, family)，供后续语句继续读取或更新。
            data, output_name, family = self._datasheet.compose_network_touchstone(index)
            # Codex说明(自动生成)： 计算并保存 expected_suffix，供后续语句继续读取或更新。
            expected_suffix = f".s{data.n_ports}p"
            # Codex说明(自动生成)： 计算并保存 safe_name，供后续语句继续读取或更新。
            safe_name = Path(output_name).name
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = OUTPUT_DIR / safe_name
            # Codex说明(自动生成)： 检查条件 output.suffix.lower() != expected_suffix，根据结果选择后续执行路径。
            if output.suffix.lower() != expected_suffix:
                # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                output = output.with_suffix(expected_suffix)
            # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
            output = output.resolve()
            # Codex说明(自动生成)： 进入上下文 self._output_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._output_lock:
                # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                output = self._next_available_output_path(
                    output, includes_report=False
                )
                # Codex说明(自动生成)： 计算并保存 diagnostics，供后续语句继续读取或更新。
                diagnostics = assert_sampled_passive(
                    data, context="Image output preflight"
                )
                # Codex说明(自动生成)： 调用 output.parent.mkdir，执行当前流程需要的具体操作或副作用。
                output.parent.mkdir(parents=True, exist_ok=True)
                # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
                write_touchstone(
                    data, output, frequency_unit="hz", data_format="ri"
                )
            # Codex说明(自动生成)： 进入上下文 self._state_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._state_lock:
                # Codex说明(自动生成)： 计算并保存 self._last_output，供后续语句继续读取或更新。
                self._last_output = output
                # Codex说明(自动生成)： 计算并保存 self._last_datasheet_output，供后续语句继续读取或更新。
                self._last_datasheet_output = output
            # Codex说明(自动生成)： 返回 {'ok': True, 'output': str(output), 'points': int(data....，让调用方取得本函数的处理结果。
            return {
                "ok": True,
                "output": str(output),
                "points": int(data.frequency_hz.size),
                "ports": data.n_ports,
                "parameter_family": family,
                "phase_assumption": "zero-degree",
                "sigma_max": diagnostics.maximum_singular_value,
            }
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception as exc:  # noqa: BLE001 - bridge errors must be visible.
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(exc) or exc.__class__.__name__}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(exc) or exc.__class__.__name__}


    # Codex说明(自动生成)： 定义函数 run_generation，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def run_generation(self, config: Mapping[str, object]) -> dict[str, object]:
        """Run generation off the bridge thread so the HTML stays responsive."""

        # Codex说明(自动生成)： 进入上下文 self._run_lock，确保文件、资源或临时状态按作用域正确释放。
        with self._run_lock:
            # Codex说明(自动生成)： 检查条件 self._running，根据结果选择后续执行路径。
            if self._running:
                # Codex说明(自动生成)： 返回 {'ok': False, 'error': '正在生成。'}，让调用方取得本函数的处理结果。
                return {"ok": False, "error": "正在生成。"}
            # Codex说明(自动生成)： 计算并保存 self._running，供后续语句继续读取或更新。
            self._running = True
        # Codex说明(自动生成)： 计算并保存 worker，供后续语句继续读取或更新。
        worker = threading.Thread(
            target=self._generation_worker,
            args=(dict(config),),
            name="insertion-loss-web-worker",
            daemon=False,
        )
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 worker.start，执行当前流程需要的具体操作或副作用。
            worker.start()
        # Codex说明(自动生成)： 捕获 RuntimeError，执行对应的恢复、记录或重新报错逻辑。
        except RuntimeError as exc:
            # Codex说明(自动生成)： 进入上下文 self._run_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._run_lock:
                # Codex说明(自动生成)： 计算并保存 self._running，供后续语句继续读取或更新。
                self._running = False
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': f'无法启动生成任务：{exc}'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": f"无法启动生成任务：{exc}"}
        # Codex说明(自动生成)： 返回 {'ok': True, 'started': True}，让调用方取得本函数的处理结果。
        return {"ok": True, "started": True}

    # Codex说明(自动生成)： 定义函数 run_generation_sync，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def run_generation_sync(self, config: Mapping[str, object]) -> dict[str, object]:
        """Execute one real backend run, used by the worker and public tests."""

        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 auto_name，供后续语句继续读取或更新。
            auto_name = not str(config.get("output", "")).strip()
            # Codex说明(自动生成)： 计算并保存 mode，供后续语句继续读取或更新。
            mode = str(config.get("mode", "linear")).strip().lower()
            # Codex说明(自动生成)： 检查条件 mode == 'modify'，根据结果选择后续执行路径。
            if mode == "modify":
                # Codex说明(自动生成)： 计算并保存 (data, output, report)，供后续语句继续读取或更新。
                data, output, report = self._run_modify(config)
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 计算并保存 (data, output)，供后续语句继续读取或更新。
                data, output = self._run_generated(mode, config)
                # Codex说明(自动生成)： 计算并保存 report，供后续语句继续读取或更新。
                report = None
            # Codex说明(自动生成)： 进入上下文 self._output_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._output_lock:
                # Codex说明(自动生成)： 检查条件 auto_name，根据结果选择后续执行路径。
                if auto_name:
                    # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
                    output = self._next_available_output_path(
                        output, includes_report=report is not None
                    )
                    # Codex说明(自动生成)： 检查条件 report is not None，根据结果选择后续执行路径。
                    if report is not None:
                        # Codex说明(自动生成)： 计算并保存 report，供后续语句继续读取或更新。
                        report = output.with_suffix(output.suffix + ".report.txt")
                # Codex说明(自动生成)： 计算并保存 existing，供后续语句继续读取或更新。
                existing = [
                    path for path in (output, report) if path is not None and path.exists()
                ]
                # Codex说明(自动生成)： 检查条件 existing and (not bool(config.get('overwrite', False)))，根据结果选择后续执行路径。
                if existing and not bool(config.get("overwrite", False)):
                    # Codex说明(自动生成)： 抛出 FileExistsError(f'输出文件已存在：{existing[0]}')，明确提示输入、状态或处理流程无法继续。
                    raise FileExistsError(f"输出文件已存在：{existing[0]}")
                # Codex说明(自动生成)： 计算并保存 diagnostics，供后续语句继续读取或更新。
                diagnostics = assert_sampled_passive(
                    data, context="Web UI output preflight"
                )
                # Codex说明(自动生成)： 调用 output.parent.mkdir，执行当前流程需要的具体操作或副作用。
                output.parent.mkdir(parents=True, exist_ok=True)
                # Codex说明(自动生成)： 调用 write_touchstone，执行当前流程需要的具体操作或副作用。
                write_touchstone(
                    data,
                    output,
                    frequency_unit=str(config.get("frequency_unit", "ghz")).lower(),
                    data_format=str(config.get("format", "ri")).lower(),
                )
                # Codex说明(自动生成)： 检查条件 report is not None，根据结果选择后续执行路径。
                if report is not None:
                    # Codex说明(自动生成)： 调用 write_modification_report，执行当前流程需要的具体操作或副作用。
                    write_modification_report(report, self._last_modification_results)
            # Codex说明(自动生成)： 进入上下文 self._state_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._state_lock:
                # Codex说明(自动生成)： 计算并保存 self._last_output，供后续语句继续读取或更新。
                self._last_output = output
            # Codex说明(自动生成)： 声明并保存 payload，同时保留类型信息方便维护和静态检查。
            payload: dict[str, object] = {
                "type": "success",
                "ok": True,
                "mode": mode,
                "output": str(output),
                "report": str(report) if report is not None else None,
                "sigma_max": diagnostics.maximum_singular_value,
                "plot": self._plot_payload(data, str(config.get("frequency_unit", "ghz"))),
            }
            # Codex说明(自动生成)： 调用 self._emit，执行当前流程需要的具体操作或副作用。
            self._emit(payload)
            # Codex说明(自动生成)： 返回 payload，让调用方取得本函数的处理结果。
            return payload
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception as exc:  # noqa: BLE001 - bridge failures must become visible messages.
            # Codex说明(自动生成)： 计算并保存 payload，供后续语句继续读取或更新。
            payload = {"type": "error", "ok": False, "error": str(exc) or exc.__class__.__name__}
            # Codex说明(自动生成)： 调用 self._emit，执行当前流程需要的具体操作或副作用。
            self._emit(payload)
            # Codex说明(自动生成)： 返回 payload，让调用方取得本函数的处理结果。
            return payload

    # Codex说明(自动生成)： 定义函数 open_output_dir，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def open_output_dir(self) -> dict[str, object]:
        # Codex说明(自动生成)： 进入上下文 self._state_lock，确保文件、资源或临时状态按作用域正确释放。
        with self._state_lock:
            # Codex说明(自动生成)： 计算并保存 last_output，供后续语句继续读取或更新。
            last_output = self._last_output
        # Codex说明(自动生成)： 检查条件 last_output is None，根据结果选择后续执行路径。
        if last_output is None:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '尚未生成文件。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "尚未生成文件。"}
        # Codex说明(自动生成)： 返回 self._open_directory(last_output.parent)，让调用方取得本函数的处理结果。
        return self._open_directory(last_output.parent)

    # Codex说明(自动生成)： 定义函数 open_datasheet_output_dir，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def open_datasheet_output_dir(self) -> dict[str, object]:
        """Open the folder containing the latest Image workspace export."""

        # Codex说明(自动生成)： 进入上下文 self._state_lock，确保文件、资源或临时状态按作用域正确释放。
        with self._state_lock:
            # Codex说明(自动生成)： 计算并保存 last_output，供后续语句继续读取或更新。
            last_output = self._last_datasheet_output
        # Codex说明(自动生成)： 检查条件 last_output is None，根据结果选择后续执行路径。
        if last_output is None:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': '图片页尚未生成文件。'}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": "图片页尚未生成文件。"}
        # Codex说明(自动生成)： 返回 self._open_directory(last_output.parent)，让调用方取得本函数的处理结果。
        return self._open_directory(last_output.parent)

    # Codex说明(自动生成)： 定义函数 _open_directory，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _open_directory(path: Path) -> dict[str, object]:
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 检查条件 sys.platform == 'darwin'，根据结果选择后续执行路径。
            if sys.platform == "darwin":
                # Codex说明(自动生成)： 调用 subprocess.Popen，执行当前流程需要的具体操作或副作用。
                subprocess.Popen(["open", str(path)])
            # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 os.name == 'nt'。
            elif os.name == "nt":
                # Codex说明(自动生成)： 调用 os.startfile，执行当前流程需要的具体操作或副作用。
                os.startfile(str(path))  # type: ignore[attr-defined]
            # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
            else:
                # Codex说明(自动生成)： 调用 subprocess.Popen，执行当前流程需要的具体操作或副作用。
                subprocess.Popen(["xdg-open", str(path)])
        # Codex说明(自动生成)： 捕获 OSError，执行对应的恢复、记录或重新报错逻辑。
        except OSError as exc:
            # Codex说明(自动生成)： 返回 {'ok': False, 'error': str(exc)}，让调用方取得本函数的处理结果。
            return {"ok": False, "error": str(exc)}
        # Codex说明(自动生成)： 返回 {'ok': True, 'path': str(path)}，让调用方取得本函数的处理结果。
        return {"ok": True, "path": str(path)}

    # Codex说明(自动生成)： 定义函数 _run_generated，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_generated(
        self, mode: str, config: Mapping[str, object]
    ) -> tuple[TouchstoneData, Path]:
        # Codex说明(自动生成)： 计算并保存 ports，供后续语句继续读取或更新。
        ports = int(config.get("ports", 2))
        # Codex说明(自动生成)： 检查条件 ports not in COMMON_PORT_COUNTS，根据结果选择后续执行路径。
        if ports not in COMMON_PORT_COUNTS:
            # Codex说明(自动生成)： 计算并保存 choices，供后续语句继续读取或更新。
            choices = "、".join(str(value) for value in COMMON_PORT_COUNTS)
            # Codex说明(自动生成)： 抛出 ValueError(f'常规生成仅支持 {choices} 端口。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError(f"常规生成仅支持 {choices} 端口。")
        # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
        frequency = generate_frequency_axis(
            parse_frequency(str(config.get("f_start", "10MHz"))),
            parse_frequency(str(config.get("f_stop", "40GHz"))),
            int(config.get("points", 801)),
            spacing=str(config.get("spacing", "linear")),
        )
        # Codex说明(自动生成)： 检查条件 mode == 'linear'，根据结果选择后续执行路径。
        if mode == "linear":
            # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
            loss = linear_loss(
                frequency,
                float(config.get("loss_start_db", 0.2)),
                float(config.get("loss_stop_db", 20.0)),
            )
        # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 mode == 'formula'。
        elif mode == "formula":
            # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
            loss = protocol_loss(
                frequency,
                a=float(config.get("a", 0.08)),
                b=float(config.get("b", 0.6)),
                c=float(config.get("c", 0.1)),
                model_frequency_unit=str(config.get("model_frequency_unit", "ghz")),
            )
        # Codex说明(自动生成)： 当前一分支未命中时，继续检查条件 mode == 'draw'。
        elif mode == "draw":
            # Codex说明(自动生成)： 计算并保存 tokens，供后续语句继续读取或更新。
            tokens = _split_text_values(config.get("control_points", ""))
            # Codex说明(自动生成)： 检查条件 len(tokens) < 2，根据结果选择后续执行路径。
            if len(tokens) < 2:
                # Codex说明(自动生成)： 抛出 ValueError('手绘至少需要 2 个控制点。')，明确提示输入、状态或处理流程无法继续。
                raise ValueError("手绘至少需要 2 个控制点。")
            # Codex说明(自动生成)： 计算并保存 controls，供后续语句继续读取或更新。
            controls = parse_draw_points(tokens)
            # Codex说明(自动生成)： 计算并保存 frequency，供后续语句继续读取或更新。
            frequency = insert_draw_control_frequencies(frequency, controls)
            # Codex说明(自动生成)： 计算并保存 loss，供后续语句继续读取或更新。
            loss = interpolate_drawn_loss(
                frequency,
                controls,
                method=str(config.get("fit", "smooth")),
                fit_domain=str(config.get("fit_domain", "linear")),
                min_spacing_fraction=float(config.get("min_spacing_fraction", 0.0001)),
                max_slope_db_per_span=float(config.get("max_slope_db_per_span", 500.0)),
            )
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 抛出 ValueError('生成模式无效。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("生成模式无效。")
        # Codex说明(自动生成)： 计算并保存 pair_tokens，供后续语句继续读取或更新。
        pair_tokens = _split_text_values(config.get("through_pairs", ""))
        # Codex说明(自动生成)： 计算并保存 pairs，供后续语句继续读取或更新。
        pairs = parse_pairs(pair_tokens, ports) if pair_tokens else default_through_pairs(ports)
        # Codex说明(自动生成)： 计算并保存 data，供后续语句继续读取或更新。
        data = build_network(
            frequency,
            ports,
            loss,
            through_pairs=pairs,
            return_loss_db=float(config.get("return_loss_db", 20.0)),
            crosstalk_db=float(config.get("crosstalk_db", 80.0)),
            delay_ps=float(config.get("delay_ps", 80.0)),
            phase_offset_deg=float(config.get("phase_offset_deg", 0.0)),
            z0=float(config.get("z0", 50.0)),
        )
        # Codex说明(自动生成)： 返回 (data, self._output_path(config, ports, mode))，让调用方取得本函数的处理结果。
        return data, self._output_path(config, ports, mode)

    # Codex说明(自动生成)： 定义函数 _run_modify，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _run_modify(
        self, config: Mapping[str, object]
    ) -> tuple[TouchstoneData, Path, Path]:
        # Codex说明(自动生成)： 计算并保存 source_path，供后续语句继续读取或更新。
        source_path = Path(str(config.get("input", ""))).expanduser().resolve()
        # Codex说明(自动生成)： 计算并保存 source，供后续语句继续读取或更新。
        source = read_touchstone(source_path)
        # Codex说明(自动生成)： 计算并保存 result，供后续语句继续读取或更新。
        result = modify_insertion_loss(
            source,
            parse_target_points(_split_text_values(config.get("targets", ""))),
            parse_pairs(_split_text_values(config.get("pairs", "")), source.n_ports),
            smoothness=float(config.get("smoothness", 0.14)),
            smooth_domain=str(config.get("smooth_domain", "log")),
            anchor_edges=bool(config.get("anchor_edges", True)),
            insert_targets=bool(config.get("insert_targets", True)),
        )
        # Codex说明(自动生成)： 计算并保存 self._last_modification_results，供后续语句继续读取或更新。
        self._last_modification_results = result.results
        # Codex说明(自动生成)： 计算并保存 output，供后续语句继续读取或更新。
        output = self._output_path(config, source.n_ports, "modified")
        # Codex说明(自动生成)： 返回 (result.data, output, output.with_suffix(output.suffix ...，让调用方取得本函数的处理结果。
        return result.data, output, output.with_suffix(output.suffix + ".report.txt")

    # Codex说明(自动生成)： 定义函数 _output_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _output_path(config: Mapping[str, object], ports: int, stem: str) -> Path:
        # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
        text = str(config.get("output", "")).strip()
        # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
        path = Path(text).expanduser() if text else OUTPUT_DIR / f"{stem}_web.s{ports}p"
        # Codex说明(自动生成)： 检查条件 not path.is_absolute()，根据结果选择后续执行路径。
        if not path.is_absolute():
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = Path.cwd() / path
        # Codex说明(自动生成)： 计算并保存 expected，供后续语句继续读取或更新。
        expected = f".s{ports}p"
        # Codex说明(自动生成)： 检查条件 path.suffix.lower() != expected，根据结果选择后续执行路径。
        if path.suffix.lower() != expected:
            # Codex说明(自动生成)： 计算并保存 path，供后续语句继续读取或更新。
            path = path.with_suffix(expected)
        # Codex说明(自动生成)： 返回 path.resolve()，让调用方取得本函数的处理结果。
        return path.resolve()

    # Codex说明(自动生成)： 定义函数 _next_available_output_path，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _next_available_output_path(path: Path, *, includes_report: bool) -> Path:
        """Choose a stable unused auto-name without changing explicit paths."""

        # Codex说明(自动生成)： 计算并保存 candidate，供后续语句继续读取或更新。
        candidate = path
        # Codex说明(自动生成)： 计算并保存 index，供后续语句继续读取或更新。
        index = 0
        # Codex说明(自动生成)： 当条件 candidate.exists() or (includes_report and candidate.wi... 成立时，重复执行循环体逻辑。
        while candidate.exists() or (
            includes_report
            and candidate.with_suffix(candidate.suffix + ".report.txt").exists()
        ):
            # Codex说明(自动生成)： 基于旧值更新 index，累积当前循环或处理步骤的结果。
            index += 1
            # Codex说明(自动生成)： 计算并保存 candidate，供后续语句继续读取或更新。
            candidate = path.with_name(f"{path.stem}_{index:03d}{path.suffix}")
        # Codex说明(自动生成)： 返回 candidate，让调用方取得本函数的处理结果。
        return candidate

    # Codex说明(自动生成)： 定义函数 _plot_payload，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    @staticmethod
    def _plot_payload(data: TouchstoneData, frequency_unit: str) -> dict[str, object]:
        # Codex说明(自动生成)： 计算并保存 unit，供后续语句继续读取或更新。
        unit = frequency_unit.lower()
        # Codex说明(自动生成)： 计算并保存 scales，供后续语句继续读取或更新。
        scales = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}
        # Codex说明(自动生成)： 检查条件 unit not in scales，根据结果选择后续执行路径。
        if unit not in scales:
            # Codex说明(自动生成)： 抛出 ValueError('频率单位无效。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("频率单位无效。")
        # Codex说明(自动生成)： 计算并保存 stride，供后续语句继续读取或更新。
        stride = max(1, int(np.ceil(data.frequency_hz.size / 500)))
        # Codex说明(自动生成)： 计算并保存 indices，供后续语句继续读取或更新。
        indices = np.arange(0, data.frequency_hz.size, stride)
        # Codex说明(自动生成)： 检查条件 indices[-1] != data.frequency_hz.size - 1，根据结果选择后续执行路径。
        if indices[-1] != data.frequency_hz.size - 1:
            # Codex说明(自动生成)： 计算并保存 indices，供后续语句继续读取或更新。
            indices = np.append(indices, data.frequency_hz.size - 1)
        # Codex说明(自动生成)： 计算并保存 series，供后续语句继续读取或更新。
        series = []
        # Codex说明(自动生成)： 遍历 range(data.n_ports) 中的 out_port，逐项执行循环体逻辑。
        for out_port in range(data.n_ports):
            # Codex说明(自动生成)： 遍历 range(data.n_ports) 中的 in_port，逐项执行循环体逻辑。
            for in_port in range(data.n_ports):
                # Codex说明(自动生成)： 计算并保存 values，供后续语句继续读取或更新。
                values = data.s[indices, out_port, in_port]
                # Codex说明(自动生成)： 调用 series.append 更新列表或集合，把当前步骤产生的数据加入结果。
                series.append(
                    {
                        "name": f"S{out_port + 1}{in_port + 1}",
                        "magnitude": np.round(to_magnitude_db(values), 7).tolist(),
                        "phase": np.round(np.rad2deg(np.unwrap(np.angle(values))), 7).tolist(),
                    }
                )
        # Codex说明(自动生成)： 返回 {'frequency': np.round(data.frequency_hz[indices] / sca...，让调用方取得本函数的处理结果。
        return {
            "frequency": np.round(data.frequency_hz[indices] / scales[unit], 10).tolist(),
            "unit": {"hz": "Hz", "khz": "kHz", "mhz": "MHz", "ghz": "GHz"}[unit],
            "series": series,
        }

    # Codex说明(自动生成)： 定义函数 _generation_worker，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _generation_worker(self, config: dict[str, object]) -> None:
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 self.run_generation_sync，执行当前流程需要的具体操作或副作用。
            self.run_generation_sync(config)
        # Codex说明(自动生成)： 无论前面是否出错，都执行这里的资源释放或收尾逻辑。
        finally:
            # Codex说明(自动生成)： 进入上下文 self._run_lock，确保文件、资源或临时状态按作用域正确释放。
            with self._run_lock:
                # Codex说明(自动生成)： 计算并保存 self._running，供后续语句继续读取或更新。
                self._running = False

    # Codex说明(自动生成)： 定义函数 _emit，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _emit(self, payload: Mapping[str, object]) -> None:
        # Codex说明(自动生成)： 检查条件 self._window is None，根据结果选择后续执行路径。
        if self._window is None:
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return
        # Codex说明(自动生成)： 计算并保存 serialized，供后续语句继续读取或更新。
        serialized = json.dumps(dict(payload), ensure_ascii=False)
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 self._window.evaluate_js，执行当前流程需要的具体操作或副作用。
            self._window.evaluate_js(f"window.insertionLoss.receive({serialized});")
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception:  # noqa: BLE001 - UI observation cannot change a completed file write.
            # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
            return

    # Codex说明(自动生成)： 定义函数 _handle_close_request，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _handle_close_request(self) -> bool:
        # Codex说明(自动生成)： 进入上下文 self._run_lock，确保文件、资源或临时状态按作用域正确释放。
        with self._run_lock:
            # Codex说明(自动生成)： 计算并保存 running，供后续语句继续读取或更新。
            running = self._running
        # Codex说明(自动生成)： 检查条件 running，根据结果选择后续执行路径。
        if running:
            # Codex说明(自动生成)： 调用 self._emit，执行当前流程需要的具体操作或副作用。
            self._emit({"type": "notice", "message": "生成完成后再关闭窗口。"})
            # Codex说明(自动生成)： 返回 False，让调用方取得本函数的处理结果。
            return False
        # Codex说明(自动生成)： 返回 True，让调用方取得本函数的处理结果。
        return True


# Codex说明(自动生成)： 定义 InsertionLossJsApi 类，把相关数据结构、校验规则或操作方法组织在一起。
class InsertionLossJsApi:
    """Explicit allow-list exposed to the trusted local HTML document."""

    # Codex说明(自动生成)： 定义函数 __init__，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def __init__(self, controller: InsertionLossWebApi) -> None:
        # Codex说明(自动生成)： 计算并保存 self._controller，供后续语句继续读取或更新。
        self._controller = controller

    # Codex说明(自动生成)： 定义函数 get_defaults，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def get_defaults(self) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.get_defaults()，让调用方取得本函数的处理结果。
        return self._controller.get_defaults()

    # Codex说明(自动生成)： 定义函数 choose_output，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_output(self, ports: object = 2) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.choose_output(ports)，让调用方取得本函数的处理结果。
        return self._controller.choose_output(ports)

    # Codex说明(自动生成)： 定义函数 choose_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_input(self) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.choose_input()，让调用方取得本函数的处理结果。
        return self._controller.choose_input()

    # Codex说明(自动生成)： 定义函数 inspect_input，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def inspect_input(
        self, path: object, frequency_unit: object = "ghz"
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.inspect_input(path, frequency_unit)，让调用方取得本函数的处理结果。
        return self._controller.inspect_input(path, frequency_unit)

    # Codex说明(自动生成)： 定义函数 choose_images，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def choose_images(self) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.choose_images()，让调用方取得本函数的处理结果。
        return self._controller.choose_images()

    # Codex说明(自动生成)： 定义函数 remove_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def remove_image(self, index: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.remove_image(index)，让调用方取得本函数的处理结果。
        return self._controller.remove_image(index)

    # Codex说明(自动生成)： 定义函数 analyze_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def analyze_image(self, index: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.analyze_image(index)，让调用方取得本函数的处理结果。
        return self._controller.analyze_image(index)

    # Codex说明(自动生成)： 定义函数 set_image_frequency，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_image_frequency(
        self, index: object, start: object, stop: object, step: object, spacing: object
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_image_frequency(index, start, stop...，让调用方取得本函数的处理结果。
        return self._controller.set_image_frequency(index, start, stop, step, spacing)

    # Codex说明(自动生成)： 定义函数 digitize_image，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def digitize_image(
        self, index: object, y_min_db: object, y_max_db: object
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.digitize_image(index, y_min_db, y_max_db)，让调用方取得本函数的处理结果。
        return self._controller.digitize_image(index, y_min_db, y_max_db)

    def digitize_image_with_axis(
        self,
        index: object,
        y_top_db: object,
        y_bottom_db: object,
        convention: object,
    ) -> dict[str, object]:
        return self._controller.digitize_image_with_axis(
            index, y_top_db, y_bottom_db, convention
        )

    # Codex说明(自动生成)： 定义函数 set_curve_parameter，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_curve_parameter(
        self, index: object, curve_id: object, parameter: object
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_curve_parameter(index, curve_id, p...，让调用方取得本函数的处理结果。
        return self._controller.set_curve_parameter(index, curve_id, parameter)

    # Codex说明(自动生成)： 定义函数 run_generation，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def run_generation(self, config: Mapping[str, object]) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.run_generation(config)，让调用方取得本函数的处理结果。
        return self._controller.run_generation(config)

    # Codex说明(自动生成)： 定义函数 open_output_dir，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def open_output_dir(self) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.open_output_dir()，让调用方取得本函数的处理结果。
        return self._controller.open_output_dir()

    # Codex说明(自动生成)： 定义函数 open_datasheet_output_dir，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def open_datasheet_output_dir(self) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.open_datasheet_output_dir()，让调用方取得本函数的处理结果。
        return self._controller.open_datasheet_output_dir()

    # Codex说明(自动生成)： 定义函数 set_network_count，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_count(self, count: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_network_count(count)，让调用方取得本函数的处理结果。
        return self._controller.set_network_count(count)

    # Codex说明(自动生成)： 定义函数 set_network_ports，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_ports(self, index: object, ports: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_network_ports(index, ports)，让调用方取得本函数的处理结果。
        return self._controller.set_network_ports(index, ports)

    # Codex说明(自动生成)： 定义函数 set_network_parameter_family，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_parameter_family(self, index: object, family: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_network_parameter_family(index, fa...，让调用方取得本函数的处理结果。
        return self._controller.set_network_parameter_family(index, family)

    # Codex说明(自动生成)： 定义函数 set_network_frequency_policy，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_frequency_policy(
        self,
        index: object,
        mode: object,
        start: object,
        stop: object,
        step: object,
        allow_fill: object,
    ) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_network_frequency_policy(index, mo...，让调用方取得本函数的处理结果。
        return self._controller.set_network_frequency_policy(
            index, mode, start, stop, step, allow_fill
        )

    # Codex说明(自动生成)： 定义函数 set_network_reciprocal，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_network_reciprocal(self, index: object, enabled: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_network_reciprocal(index, enabled)，让调用方取得本函数的处理结果。
        return self._controller.set_network_reciprocal(index, enabled)

    # Codex说明(自动生成)： 定义函数 set_mapping，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def set_mapping(self, index: object, parameter: object, source: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.set_mapping(index, parameter, source)，让调用方取得本函数的处理结果。
        return self._controller.set_mapping(index, parameter, source)

    # Codex说明(自动生成)： 定义函数 generate_datasheet_network，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def generate_datasheet_network(self, index: object) -> dict[str, object]:
        # Codex说明(自动生成)： 返回 self._controller.generate_datasheet_network(index)，让调用方取得本函数的处理结果。
        return self._controller.generate_datasheet_network(index)


# Codex说明(自动生成)： 定义函数 create_webview_window，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def create_webview_window(
    api: InsertionLossWebApi | None = None,
) -> tuple[Any, InsertionLossWebApi]:
    """Create the native desktop window from the packaged HTML document."""

    # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
    import webview

    # Codex说明(自动生成)： 计算并保存 html，供后续语句继续读取或更新。
    html = load_web_ui()
    # Codex说明(自动生成)： 调用 validate_web_ui_contract，执行当前流程需要的具体操作或副作用。
    validate_web_ui_contract(html)
    # Codex说明(自动生成)： 计算并保存 bridge，供后续语句继续读取或更新。
    bridge = api or InsertionLossWebApi()
    # Codex说明(自动生成)： 计算并保存 window，供后续语句继续读取或更新。
    window = webview.create_window(
        APP_NAME,
        html=html,
        js_api=InsertionLossJsApi(bridge),
        width=1380,
        height=860,
        min_size=(960, 640),
        background_color="#18192D",
        text_select=True,
        confirm_close=False,
    )
    # Codex说明(自动生成)： 检查条件 window is None，根据结果选择后续执行路径。
    if window is None:
        # Codex说明(自动生成)： 抛出 RuntimeError('无法创建桌面窗口。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("无法创建桌面窗口。")
    # Codex说明(自动生成)： 调用 bridge.bind_window，执行当前流程需要的具体操作或副作用。
    bridge.bind_window(window)
    # Codex说明(自动生成)： 基于旧值更新 window.events.closing，累积当前循环或处理步骤的结果。
    window.events.closing += bridge._handle_close_request
    # Codex说明(自动生成)： 返回 (window, bridge)，让调用方取得本函数的处理结果。
    return window, bridge


# Codex说明(自动生成)： 定义函数 _write_renderer_probe，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def _write_renderer_probe(window: Any, evidence_path: str | None = None) -> dict[str, object]:
    # Codex说明(自动生成)： 检查条件 not window.events.loaded.wait(15)，根据结果选择后续执行路径。
    if not window.events.loaded.wait(15):
        # Codex说明(自动生成)： 抛出 RuntimeError('桌面界面加载超时。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("桌面界面加载超时。")
    # Codex说明(自动生成)： 计算并保存 deadline，供后续语句继续读取或更新。
    deadline = time.monotonic() + 5.0
    # Codex说明(自动生成)： 当条件 time.monotonic() < deadline 成立时，重复执行循环体逻辑。
    while time.monotonic() < deadline:
        # Codex说明(自动生成)： 检查条件 window.evaluate_js('Boolean(window.insertionLossReady)')，根据结果选择后续执行路径。
        if window.evaluate_js("Boolean(window.insertionLossReady)"):
            # Codex说明(自动生成)： 提前结束当前循环，跳出后不再执行本轮循环后续迭代。
            break
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.05)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 RuntimeError('桌面界面默认设置加载超时。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("桌面界面默认设置加载超时。")
    # Codex说明(自动生成)： 计算并保存 probe，供后续语句继续读取或更新。
    probe = dict(window.evaluate_js(RENDERER_PROBE_SCRIPT))
    # Codex说明(自动生成)： 计算并保存 modify_source，供后续语句继续读取或更新。
    modify_source = default_example_path().with_name("formula_demo.s4p")
    # Codex说明(自动生成)： 计算并保存 bridge_before_modify，供后续语句继续读取或更新。
    bridge_before_modify = int(
        window.evaluate_js("Number(window.insertionLossBridgeCalls || 0)")
    )
    # Codex说明(自动生成)： 调用 window.evaluate_js，执行当前流程需要的具体操作或副作用。
    window.evaluate_js(
        "document.querySelector('[data-tab=\"generator\"]').click();"
        "document.querySelector('[data-mode=\"modify\"]').click();"
        f"document.querySelector('#modify-input').value={json.dumps(str(modify_source))};"
        "document.querySelector('#modify-input').dispatchEvent(new Event('change',{bubbles:true}));"
    )
    # Codex说明(自动生成)： 计算并保存 modify_deadline，供后续语句继续读取或更新。
    modify_deadline = time.monotonic() + 5.0
    # Codex说明(自动生成)： 当条件 time.monotonic() < modify_deadline 成立时，重复执行循环体逻辑。
    while time.monotonic() < modify_deadline:
        # Codex说明(自动生成)： 检查条件 window.evaluate_js("document.querySelector('#modify-inp...，根据结果选择后续执行路径。
        if window.evaluate_js(
            "document.querySelector('#modify-input-status').textContent.startsWith('Loaded ')"
        ):
            # Codex说明(自动生成)： 提前结束当前循环，跳出后不再执行本轮循环后续迭代。
            break
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.05)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 RuntimeError('Modify 输入文件未在真实界面中加载。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("Modify 输入文件未在真实界面中加载。")
    # Codex说明(自动生成)： 计算并保存 modify_probe，供后续语句继续读取或更新。
    modify_probe = window.evaluate_js(
        "(() => ({"
        "modifyInputSummary:document.querySelector('#modify-input-status').textContent,"
        "modifyInputPorts:Number(document.querySelector('#ports').value),"
        "modifyInputPoints:Number(document.querySelector('#points').value),"
        "modifyInputStart:document.querySelector('#f-start').value,"
        "modifyInputStop:document.querySelector('#f-stop').value,"
        "modifyPlotCount:document.querySelectorAll('.plot-item').length,"
        "modifyHasS44:[...document.querySelectorAll('.plot-item strong')].some(item=>item.textContent==='S44'),"
        f"modifyBridgeCalls:Number(window.insertionLossBridgeCalls || 0)-{bridge_before_modify}"
        "}))()"
    )
    # Codex说明(自动生成)： 调用 probe.update，执行当前流程需要的具体操作或副作用。
    probe.update(dict(modify_probe))
    # Codex说明(自动生成)： 调用 window.evaluate_js，执行当前流程需要的具体操作或副作用。
    window.evaluate_js(
        "document.querySelector('#modify-input').value='/missing/modify-source.s4p';"
        "document.querySelector('#modify-input').dispatchEvent(new Event('change',{bubbles:true}));"
    )
    # Codex说明(自动生成)： 计算并保存 invalid_modify_deadline，供后续语句继续读取或更新。
    invalid_modify_deadline = time.monotonic() + 5.0
    # Codex说明(自动生成)： 当条件 time.monotonic() < invalid_modify_deadline 成立时，重复执行循环体逻辑。
    while time.monotonic() < invalid_modify_deadline:
        # Codex说明(自动生成)： 检查条件 window.evaluate_js("document.querySelector('#modify-inp...，根据结果选择后续执行路径。
        if window.evaluate_js(
            "document.querySelector('#modify-input-status').classList.contains('error')"
        ):
            # Codex说明(自动生成)： 计算并保存 probe['modifyInvalidErrorVisible']，供后续语句继续读取或更新。
            probe["modifyInvalidErrorVisible"] = True
            # Codex说明(自动生成)： 计算并保存 probe['modifyInvalidPlotCleared']，供后续语句继续读取或更新。
            probe["modifyInvalidPlotCleared"] = (
                int(window.evaluate_js("document.querySelectorAll('.plot-item').length"))
                == 0
            )
            # Codex说明(自动生成)： 提前结束当前循环，跳出后不再执行本轮循环后续迭代。
            break
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.05)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 计算并保存 probe['modifyInvalidErrorVisible']，供后续语句继续读取或更新。
        probe["modifyInvalidErrorVisible"] = False
        # Codex说明(自动生成)： 计算并保存 probe['modifyInvalidPlotCleared']，供后续语句继续读取或更新。
        probe["modifyInvalidPlotCleared"] = False
    # Codex说明(自动生成)： 调用 window.evaluate_js，执行当前流程需要的具体操作或副作用。
    window.evaluate_js(
        "document.querySelector('#zoom-image').src="
        "'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22800%22 height=%221600%22%3E%3Crect width=%22800%22 height=%221600%22 fill=%22white%22/%3E%3C/svg%3E';"
        "document.querySelector('#image-zoom').showModal();"
    )
    # Codex说明(自动生成)： 计算并保存 zoom_deadline，供后续语句继续读取或更新。
    zoom_deadline = time.monotonic() + 2.0
    # Codex说明(自动生成)： 当条件 time.monotonic() < zoom_deadline 成立时，重复执行循环体逻辑。
    while time.monotonic() < zoom_deadline:
        # Codex说明(自动生成)： 检查条件 window.evaluate_js("document.querySelector('#zoom-image...，根据结果选择后续执行路径。
        if window.evaluate_js("document.querySelector('#zoom-image').naturalWidth > 0"):
            # Codex说明(自动生成)： 提前结束当前循环，跳出后不再执行本轮循环后续迭代。
            break
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.02)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 RuntimeError('图片缩放探针加载超时。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("图片缩放探针加载超时。")
    # Codex说明(自动生成)： 计算并保存 zoom_probe，供后续语句继续读取或更新。
    zoom_probe = window.evaluate_js(
        "(() => {"
        "const dialog=document.querySelector('#image-zoom'),stage=document.querySelector('#zoom-stage'),image=document.querySelector('#zoom-image'),level=document.querySelector('#zoom-level');"
        "document.querySelector('#zoom-reset').click();"
        "const zoomLevelBefore=level.value,zoomWidthBefore=image.getBoundingClientRect().width,zoomStyleBefore=image.style.width;"
        "for(let index=0;index<12;index+=1)document.querySelector('#zoom-in').click();"
        "const result={zoomDialogOpen:dialog.open,zoomLevelBefore,zoomLevelAfter:level.value,zoomWidthBefore,zoomWidthAfter:image.getBoundingClientRect().width,zoomStyleBefore,zoomStyleAfter:image.style.width,zoomNaturalWidth:image.naturalWidth,zoomStageWidth:stage.clientWidth,zoomStageHeight:stage.clientHeight,zoomScrollWidth:stage.scrollWidth,zoomScrollHeight:stage.scrollHeight,zoomScrollable:stage.scrollWidth>stage.clientWidth||stage.scrollHeight>stage.clientHeight};"
        "dialog.close();return result;})()"
    )
    # Codex说明(自动生成)： 调用 probe.update，执行当前流程需要的具体操作或副作用。
    probe.update(dict(zoom_probe))
    # Codex说明(自动生成)： 计算并保存 probe['responsiveRequestedWindowWidth']，供后续语句继续读取或更新。
    probe["responsiveRequestedWindowWidth"] = RESPONSIVE_WINDOW_SIZE[0]
    # Codex说明(自动生成)： 计算并保存 probe['responsiveRequestedWindowHeight']，供后续语句继续读取或更新。
    probe["responsiveRequestedWindowHeight"] = RESPONSIVE_WINDOW_SIZE[1]
    # Codex说明(自动生成)： 调用 window.resize，执行当前流程需要的具体操作或副作用。
    window.resize(*RESPONSIVE_WINDOW_SIZE)
    # Codex说明(自动生成)： 计算并保存 resize_deadline，供后续语句继续读取或更新。
    resize_deadline = time.monotonic() + 2.0
    # Codex说明(自动生成)： 当条件 time.monotonic() < resize_deadline 成立时，重复执行循环体逻辑。
    while time.monotonic() < resize_deadline:
        # Codex说明(自动生成)： 计算并保存 current_width，供后续语句继续读取或更新。
        current_width = float(window.evaluate_js("window.innerWidth"))
        # Codex说明(自动生成)： 计算并保存 current_height，供后续语句继续读取或更新。
        current_height = float(window.evaluate_js("window.innerHeight"))
        # Codex说明(自动生成)： 检查条件 current_width <= RESPONSIVE_WINDOW_SIZE[0] and current_...，根据结果选择后续执行路径。
        if (
            current_width <= RESPONSIVE_WINDOW_SIZE[0]
            and current_height <= RESPONSIVE_WINDOW_SIZE[1]
        ):
            # Codex说明(自动生成)： 提前结束当前循环，跳出后不再执行本轮循环后续迭代。
            break
        # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
        time.sleep(0.02)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # Codex说明(自动生成)： 抛出 RuntimeError('桌面界面最小窗口缩放超时。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("桌面界面最小窗口缩放超时。")
    # Codex说明(自动生成)： 调用 time.sleep，执行当前流程需要的具体操作或副作用。
    time.sleep(0.05)
    # Codex说明(自动生成)： 调用 probe.update，执行当前流程需要的具体操作或副作用。
    probe.update(dict(window.evaluate_js(RESPONSIVE_RENDERER_PROBE_SCRIPT)))
    # Codex说明(自动生成)： 计算并保存 path_text，供后续语句继续读取或更新。
    path_text = evidence_path or os.environ.get("INSERTION_LOSS_RENDERER_PROBE_PATH")
    # Codex说明(自动生成)： 检查条件 path_text，根据结果选择后续执行路径。
    if path_text:
        # Codex说明(自动生成)： 计算并保存 target，供后续语句继续读取或更新。
        target = Path(path_text).expanduser().resolve()
        # Codex说明(自动生成)： 调用 target.parent.mkdir，执行当前流程需要的具体操作或副作用。
        target.parent.mkdir(parents=True, exist_ok=True)
        # Codex说明(自动生成)： 调用 target.write_text 写出文件或数据，保存当前处理结果。
        target.write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    # Codex说明(自动生成)： 调用 validate_renderer_probe，执行当前流程需要的具体操作或副作用。
    validate_renderer_probe(probe)
    # Codex说明(自动生成)： 返回 probe，让调用方取得本函数的处理结果。
    return probe


# Codex说明(自动生成)： 定义函数 run_smoke_test，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_smoke_test(*, real_window: bool = False) -> None:
    """Validate resources and optionally instantiate the native renderer."""

    # Codex说明(自动生成)： 调用 validate_web_ui_contract，执行当前流程需要的具体操作或副作用。
    validate_web_ui_contract(load_web_ui())
    # Codex说明(自动生成)： 检查条件 not real_window，根据结果选择后续执行路径。
    if not real_window:
        # Codex说明(自动生成)： 提前返回 None，结束当前函数这一分支，不再执行后续逻辑。
        return
    # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
    import webview

    # Codex说明(自动生成)： 检查条件 not hasattr(webview, 'create_window') or not hasattr(we...，根据结果选择后续执行路径。
    if not hasattr(webview, "create_window") or not hasattr(webview, "start"):
        # Codex说明(自动生成)： 抛出 RuntimeError('pywebview 安装不完整。')，明确提示输入、状态或处理流程无法继续。
        raise RuntimeError("pywebview 安装不完整。")
    # Codex说明(自动生成)： 计算并保存 (window, _api)，供后续语句继续读取或更新。
    window, _api = create_webview_window()
    # Codex说明(自动生成)： 声明并保存 errors，同时保留类型信息方便维护和静态检查。
    errors: list[Exception] = []

    # Codex说明(自动生成)： 定义函数 verify_after_load，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def verify_after_load() -> None:
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 调用 _write_renderer_probe，执行当前流程需要的具体操作或副作用。
            _write_renderer_probe(window)
        # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
        except Exception as exc:  # noqa: BLE001
            # Codex说明(自动生成)： 调用 errors.append 更新列表或集合，把当前步骤产生的数据加入结果。
            errors.append(exc)
        # Codex说明(自动生成)： 无论前面是否出错，都执行这里的资源释放或收尾逻辑。
        finally:
            # Codex说明(自动生成)： 调用 window.destroy，执行当前流程需要的具体操作或副作用。
            window.destroy()

    # Codex说明(自动生成)： 调用 webview.start，执行当前流程需要的具体操作或副作用。
    webview.start(verify_after_load, gui=select_webview_backend(), private_mode=True)
    # Codex说明(自动生成)： 检查条件 errors，根据结果选择后续执行路径。
    if errors:
        # Codex说明(自动生成)： 抛出 errors[0]，明确提示输入、状态或处理流程无法继续。
        raise errors[0]


# Codex说明(自动生成)： 定义函数 run_self_test，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def run_self_test(output_dir: str | Path | None = None) -> list[Path]:
    """Validate the WebView shell plus all four existing backend workflows."""

    # Codex说明(自动生成)： 调用 run_smoke_test，执行当前流程需要的具体操作或副作用。
    run_smoke_test(real_window=False)
    # Codex说明(自动生成)： 返回 run_backend_self_test(output_dir)，让调用方取得本函数的处理结果。
    return run_backend_self_test(output_dir)


# Codex说明(自动生成)： 定义函数 main，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
def main(argv: Sequence[str] | None = None) -> int:
    # Codex说明(自动生成)： 计算并保存 parser，供后续语句继续读取或更新。
    parser = argparse.ArgumentParser(description=f"Launch {APP_NAME}.")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--self-test", action="store_true")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--self-test-output")
    # Codex说明(自动生成)： 调用 parser.add_argument 注册命令行参数，让用户可以从终端配置运行选项。
    parser.add_argument("--renderer-smoke-test", action="store_true")
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
    # Codex说明(自动生成)： 检查条件 args.renderer_smoke_test，根据结果选择后续执行路径。
    if args.renderer_smoke_test:
        # Codex说明(自动生成)： 调用 run_smoke_test，执行当前流程需要的具体操作或副作用。
        run_smoke_test(real_window=True)
        # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
        print("Renderer smoke test passed")
        # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
        return 0

    # Codex说明(自动生成)： 导入 webview，提供本文件后续流程需要的库能力。
    import webview

    # Codex说明(自动生成)： 计算并保存 (window, _api)，供后续语句继续读取或更新。
    window, _api = create_webview_window()
    # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
    try:
        # Codex说明(自动生成)： 计算并保存 evidence_path，供后续语句继续读取或更新。
        evidence_path = os.environ.get("INSERTION_LOSS_RENDERER_PROBE_PATH")
        # Codex说明(自动生成)： 检查条件 evidence_path，根据结果选择后续执行路径。
        if evidence_path:
            # Codex说明(自动生成)： 调用 webview.start，执行当前流程需要的具体操作或副作用。
            webview.start(
                lambda: _write_renderer_probe(window, evidence_path),
                gui=select_webview_backend(),
                private_mode=True,
            )
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # Codex说明(自动生成)： 调用 webview.start，执行当前流程需要的具体操作或副作用。
            webview.start(gui=select_webview_backend(), private_mode=True)
    # Codex说明(自动生成)： 捕获 Exception，执行对应的恢复、记录或重新报错逻辑。
    except Exception:  # backend error types vary by operating system.
        # Codex说明(自动生成)： 检查条件 sys.platform.startswith('win')，根据结果选择后续执行路径。
        if sys.platform.startswith("win"):
            # Codex说明(自动生成)： 计算并保存 message，供后续语句继续读取或更新。
            message = "无法启动 Edge WebView2。请安装 WebView2 Runtime 后重试。"
            # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
            try:
                # Codex说明(自动生成)： 导入 ctypes，提供本文件后续流程需要的库能力。
                import ctypes

                # Codex说明(自动生成)： 调用 ctypes.windll.user32.MessageBoxW，执行当前流程需要的具体操作或副作用。
                ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
            # Codex说明(自动生成)： 捕获 (AttributeError, OSError)，执行对应的恢复、记录或重新报错逻辑。
            except (AttributeError, OSError):
                # Codex说明(自动生成)： 输出面向用户的运行信息，帮助确认当前脚本进度或结果路径。
                print(message, file=sys.stderr)
            # Codex说明(自动生成)： 返回 2，让调用方取得本函数的处理结果。
            return 2
        # Codex说明(自动生成)： 抛出 异常，明确提示输入、状态或处理流程无法继续。
        raise
    # Codex说明(自动生成)： 返回 0，让调用方取得本函数的处理结果。
    return 0
