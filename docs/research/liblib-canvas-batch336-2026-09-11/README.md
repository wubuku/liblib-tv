# Batch 336 — 故事板待确认生成卡：确认/取消交互（`CLONE_DECISION` 实装）

> 状态：pending 视频卡的确认/取消条实装并通过验证
> （`verify-liblib-batch336.py` 17 checks 全绿）。
> 源站交互细节未采得——**CLONE_DECISION**，非源站直证。

## 源站状态（2026-09-11）

- 模型菜单交互持续失效（batch 333 记录的僵尸层缺陷），BLOCKED_SOURCE
  维持：Hailuo 系条件分解、480P 批量采样、Style Video 费率均未补采；
- 待确认卡（Wan 3.0 Prime，`待确认后生成`）已从测试画布资源栏过期
  消失，其确认/取消交互同样无法采样。

## Clone 实现（`CLONE_DECISION`，文档明标）

- 故事板视频卡 `data-storyboard-video-status="pending"` 在**选中**
  时显示确认条（`data-storyboard-pending-strip`，卡片兄弟节点——
  button 不可嵌套）：
  - `data-storyboard-pending-confirm`「确认生成」→ 本地
    `updateNodeData(status: "ready")`（播放圆钮完成态）；
  - `data-storyboard-pending-cancel`「取消」→
    `updateNodeData(status: "empty")`（暂无预览）；
- 非选中态确认条不渲染；store 与 UI 状态双向一致。

## 验收

- `verify-liblib-batch336.py` 17 checks：状态机往返（pending →
  cancel → empty → pending → confirm → ready）、标签文案、选中前
  不渲染、store 终态、双视图往返、console 零错误；
- 回归：334/100/268/238/240 全绿；`npm run check` 0 errors；
  docs check 通过（895 Markdown）。

## 后续候选

- 源站恢复后：以真实交互替换 CLONE_DECISION（含确认后的服务端
  行为观察——消费积分、卡片状态流转）；
- 视频栏 全部 ∨ 过滤器选项采样与建模；
- BLOCKED_SOURCE 三项补采。
