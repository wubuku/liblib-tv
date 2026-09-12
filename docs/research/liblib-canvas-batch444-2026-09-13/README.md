# Batch 444 — VR-023 Slice D：本地混合比例输出 fixture（per-output 身份 + 选择重排）

> 状态：`IMPLEMENTATION_RECORDED`（media rendition/geometry 合同
> Slice D；clone-only fixture 政策，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch444-output-reflow-929-2026-09-13.png`、
> `scripts/verify-liblib-batch444.py`。

## 变更

- **`getLibTVNodeIntrinsicDimensions`（权威模块）output-aware 化**：
  `data.outputs` 数组 + `selectedOutputId` 命中时，选中输出的声明
  尺寸即固有权威；回落链不变（数值宽高 → resolution 显示串）。
- **`canvasStore.selectNodeOutput(nodeId, outputId)`（新动作）**：
  校验输出存在（未知节点/输出 → 稳定 false NOOP）后写
  `selectedOutputId` 并按 Slice B 政策重排节点帧（高保持 288 级、
  宽 = round(高 × 新比例)、钳制 [160, 640]）；**rendition 状态、
  不入 graph 历史**（合同：history integration 出圈）。

## 验收（verify-liblib-batch444.py，SCRIPT_RECORDED_PASS —— 注入混合比例 fixture）

- `out-square`(512×512) 起始帧 288×288 → 选 `out-portrait`
  (720×1280) → 重排 **162×288**、selectedOutputId 记录；
- 选 `out-wide`(1920×1080) → **512×288**（16:9 级回通用）；
- `out-missing` → 稳定 false、帧与 selectedOutputId 零部分变更；
- 全程 `historyByCanvas["canvas-1"]` 无任何入栈（历史出圈声明）；
- 441 检测器对该节点零冲突（政策/检测器一致）；
- console/pageerror/requestfailed 为 0；无溢出。

## 附带

jimeng-canvas README §7 同步 batch 39（分组 ⌘G/⌘⇧G，SOURCE_FACT 与
batch 18 快捷键面板交叉一致）/ batch 40（生成面板 textarea + mock
toast，CLONE_DECISION）条目。

## 后续（VR-023）

Slice E 为 source-driven refinement（OC-EQ-009 证据后）——源站恢复
前 gated。至此 VR-023 的 clone 侧 runtime 切片（A–D）全部关闭。
