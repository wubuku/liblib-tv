# Batch 442 — VR-023 Slice B：确定性 frame/rendition 政策（aspect-aware 派生帧）

> 状态：`IMPLEMENTATION_RECORDED`（media rendition/geometry 合同
> Slice B；clone-only 政策，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch442-aspect-aware-frames-929-2026-09-13.png`、
> `scripts/verify-liblib-batch442.py`。

## 变更

- **`planLibTVAspectAwareDerivedFrame`（权威模块新增政策函数）**：
  源固有比例与通用帧比例差 ≤2%（16:9 级）→ 返回 null（保留通用
  512×288，源站 backed landscape fixture 不变）；否则帧高保持
  profile 高度 288、宽 = round(288 × 比例)，钳制 [160, 640]，钳制外
  回退通用帧（batch 441 检测器随之再次标记——政策/检测器一致）。
- **`getDerivedFrameDimensions`（canvasStore 私有助手）**：接线六个
  派生构建点——`addDerivedNode`（无显式 dimensions 时）、
  `createAudioSplit`（无声视频目标）、`createVideoFrameCapture`、
  `createDepthMotionCapture`、`createSmartMatting`、`createPictureEdit`。
  其余显式尺寸流（长视频、字幕擦除候选、Director 岛）本批不动。
- 源固有取值顺序：数值 data.width/height → `resolution` 显示串解析
  （显示串投影在此首次成为可计算的 intrinsic 输入）。

## 验收（verify-liblib-batch442.py，SCRIPT_RECORDED_PASS）

- 方形 512×512 源 → 派生帧 **288×288**；竖版 720×1280 → **162×288**；
- 横版 1280×720 → 通用 **512×288** 保持（landscape fixture 不变）；
- 极端 360×1440（钳制外）→ 通用回退 **且检测器标记**
  `derived-frame-generic-default`（政策/检测器闭环）；
- 视频源 portrait `resolution` 显示串 → **162×288**（解析输入驱动
  政策）；
- 全量维护集 54 项 + jimeng1 零级联通过（landscape 路径几何未变）；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-023）

Slice C（编辑器变换正确性：content-box cover/contain、基线 revision、
marks 平面映射）、Slice D（本地混合比例输出 fixture）。
