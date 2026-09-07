# Batch 159 — 尝试列移入节点卡内（源站 2026-09-07 位置对齐）

## 源站事实（第四轮几何采样）

选中视频节点的完整结构：
- **尝试： 建议列在节点卡内**（预览下方，3 个纵向 pill，h=36，左对齐，
  选后仍驻留卡内）。
- 生成面板是卡下方独立浮层（659×190+），**面板内没有尝试行**。

clone 此前把尝试行放在面板内（Batch 125 时代决策）；本 batch 对齐位置。

## 实施

- `VideoNode.tsx`：新增 `attempt` 状态 + 卡内 `data-video-attempts` 区块
  （标题行 + 3 个纵向 36px pill，aria-pressed 保持），条件与面板一致。
- `VideoGenerationPanel.tsx`：`attempt` 改为 prop（由 VideoNode 持有）；
  联动逻辑迁入 `useEffect`（prevAttemptRef 检测跃迁，128/155 契约不变：
  5分钟→Auto+300s、首尾帧/首帧→Auto+5s、取消 5 分钟钳回 ≤30）；
  删除面板内尝试行。
- 验证器：batch128/155 尝试定位器改页面级（脱离面板作用域）；
  batch21/22 菜单 y 偏移再迁移 -32（面板去掉尝试行后页脚锚点上移）。

## 验收

- 相邻回归绿：21 / 22 / 26 / 33 / 100 / 115 / 125 / 128 / 149 / 151 / 152 / 155。
- `npm run check`：0 errors、8 warnings（既有基线）。
