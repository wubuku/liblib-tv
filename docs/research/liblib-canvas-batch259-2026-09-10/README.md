# Batch 259 — 音频连线迭代：未建立连接 + 多把手假设（源站 2026-09-10）

> 状态：`PARTIAL`（连线仍未建立；记录新假设与配方修正）。

## 本轮结果

- 边 id 集合差分就位：拖拽前后 **added: [] / removed: []**——audio.source
  → video.target 的拖拽**未建立任何边**（亦未替换既有边）；
- 视频节点按 data-id 重选恢复面板：脚本笔误（`out.push` 应为
  `out.slots.push`）中断，已修正待下轮复用。

## 新假设（下一迭代要点）

**OmniHuman 模式下视频节点可能有多个 target 把手**（图片专用 + 音频
专用）：本轮把手枚举只取了「最后一个 target」，可能连到了图片把手
（无效连接被 React Flow 校验拒绝）。下一轮：

1. 枚举 OmniHuman 态视频节点的**全部** target 把手（数量/位置/类名）；
2. 逐个尝试 audio.source → 各 target 的拖拽，边差分判定哪个把手
   接受音频连接；
3. 连接成功后立即按 data-id 重选视频节点读取满足态。

## 累计配方资产（跨批次沉淀）

- 音频节点创建：空白处 dblclick + 添加面板 音频（`a-` 前缀，位置随
  dblclick 偏移）；
- 把手定位：`.react-flow__handle.source/.target` 中心坐标；
- 边差分：`data-id` 集合前后对比（新增/替换/删除判定）；
- 面板恢复：`.react-flow__node[data-id=…]` force 点击。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
