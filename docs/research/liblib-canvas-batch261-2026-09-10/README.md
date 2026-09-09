# Batch 261 — Probe B 定论：单 target 把手，拖拽连线被拒（源站 2026-09-10）

> 状态：`BLOCKED_AUTOMATION`（音频满足路径的自动化探索终结；无代码变更）。

## 定论（`SOURCE_FACT` + 负结果）

- OmniHuman 态视频节点 target 把手枚举：**仅 1 个**（左侧，
  `data-handleid=target`）——「图片/音频专用多把手」假设**证伪**；
- audio.source → 该唯一 target 的拖拽连线（12 步插值）**未建立边**
  （边 id 差分 added: []）。

## 综合判定（跨 batch 257–261）

音频需求满足路径的自动化探索已穷尽可见手段：

- 音频标签点击：无文件选择器（batch 257）；
- 需求行 DOM 无槽容器/上传供体（batch 260）；
- 唯一把手拖拽连线：被拒（本批）。

剩余可能路径（需人工或更深自动化）：素材库面板拖拽供体、导演台流、
或 Agent 代办。标记 `BLOCKED_AUTOMATION`（同 Style Video / 动作迁移）。

## 方法学沉淀

源站节点 id 前缀：视频 `v-`、音频 `a-`、图片 `i-`、分组 `g-`——
跨批次探针一律按 id 前缀 + selected 节点双重定位。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
