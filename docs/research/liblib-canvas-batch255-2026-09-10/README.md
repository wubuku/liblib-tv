# Batch 255 — attempt 持久化迁移至节点数据（源站收敛，batch 254 发散收敛）

> 状态：`IMPLEMENTED`（batch 254 记录的 clone 发散 → 实施 → 13 checks
> 验收 → 回归绿）。
>
> 源站证据：`../liblib-canvas-batch254-2026-09-10/README.md`（提交态为
> 节点持久态，去选重选不恢复）——本批无新增源站采样。

## 复刻内容

`attempt` 自 VideoNode **组件态**迁移至**节点数据**（`data.attempt`）：

1. `VideoNodeData.attempt?: string | null`；VideoNode 的
   `attempt`/`setAttempt` 改为节点数据读写（`updateNodeData`，可撤销）；
2. **首帧/首尾帧/销毁三个图动作在各自事务内合并 attempt 写入**——芯片
   提交 = 单条历史记录，撤销不经过「有 attempt 无图节点」中间态；
3. **守卫语义修正（batch 246/255）**：既有 image→video 边（如预设图）
   时仅记录 attempt 状态、跳过图创建——芯片提交语义不因防重丢失
   （batch 128 迁移后依赖此行为）；
4. `onDestroyFirstFrame` 精简为单一 store 调用（销毁事务同车清除
   attempt）。

## 实施过程记录（方法学）

- 首版验证器用 UI 重选（去选 → 重选新节点）断言持久化——预设画布节点
  屏幕重叠导致点击始终命中预设节点（force 也无法重定向 OS 事件）、
  拖拽预设节点又误触画布切换（画布 2）——**放弃几何重选，改经暴露的
  `window.__libtv_store` 直接断言 `node.data.attempt`**（持久化合同
  的本质）；
- 重构后守卫提前返回连带吞掉 attempt 写入（batch128 `linkage:shouwei`
  复炸暴露）→ 守卫语义修正（见上）。

## 验收

- `verify-liblib-batch255.py`：**13 checks**（store 断言：初态无
  attempt/无参考边；提交后 node.data.attempt + 1 参考边；销毁同事务
  清除；重提交后单次 undo 同时移除节点+边+attempt = 原子单条历史）。
- 回归绿：125 / 128 / 149 / 160 / 176 / 177 / 178 / 22 / 236 / 237 /
  238 / 239 / 240 / 244 / 248 / 249 / 252。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。

## 不证明 / 后续候选

- 源站去选重选的 UI 层表现已采（batch 254），clone 的 UI 重选路径在
  自动化下不可靠（节点重叠），人工验证可行；
- OmniHuman 音频上传流；
- Style Video / Kling3.0 动作迁移（BLOCKED_AUTOMATION）。
