# Batch 78 计划：Director Pointer Cancellation Audit

> **目的**：补齐 Director 非 R3F 指针手势的取消、失焦、页面隐藏和卸载
> 清理，避免局部 pointer 状态或全局 Director gesture 残留。
>
> **日期**：2026-08-28。
>
> **前置**：Batch 71 的 DOM gesture boundary、Batch 77 的 TransformControls
> pointer lifecycle 与当前 Director history owner 合同。

## 1. 为什么现在做

Batch 77 修复了真实 R3F gizmo 拖动，但相邻的三个 DOM/runtime 交互仍有
生命周期缺口：

| 区域 | 当前风险 | 影响 |
|---|---|---|
| Curve Editor | 只监听 `pointermove`/`pointerup`，忽略 begin 结果 | `pointercancel` 或卸载后可能留下 active gesture；提交可能误消费其他 owner |
| 手机虚拟运镜姿态盘 | `pointercancel` 不释放 capture、不清 pointerId | 关闭/失焦后下一次姿态交互可能被 stale pointer 阻塞 |
| Timeline scrub | 只移除 `pointermove`/`pointerup` | scrub 取消后可能继续响应 stale pointermove |

这三处不应通过截图推断；本批使用 DOM 结构、pointer event runtime 和
store/history 状态验证。

## 2. 实施范围

### Slice A：Curve Editor

- 只有 `beginDirectorGesture` 返回 `COMMITTED` 才激活本地 drag；
- 记录 pointer id，忽略其他 pointer；
- `pointerup` 提交一次；
- `pointercancel`、窗口 `blur`、页面 `visibilitychange=hidden` 和卸载取消；
- 清理所有 listener 和 pointer capture；
- 取消恢复曲线 baseline，零 history residue。

### Slice B：Phone Vcam pose pad

- 为姿态盘保存 DOM ref；
- 统一释放 pointer capture 和清空 pointer id；
- 增加 `pointercancel`、`lostpointercapture`、窗口 blur 和页面隐藏清理；
- 关闭/卸载时清理，但不把 runtime-only 姿态写入 Director history。

### Slice C：Timeline scrub

- 记录 scrub pointer id 和触发元素；
- `pointerup`、`pointercancel`、blur、页面隐藏和卸载都移除监听；
- 取消不改变已发生的 scrub 时间更新以外的任何 history/graph 状态；
- stale pointermove 不得继续 seek。

## 3. 验收条件

| 场景 | 期望 |
|---|---|
| Curve pointerup | 只提交一条 gesture history，active gesture 清空 |
| Curve pointercancel/blur/hidden/unmount | 恢复 baseline，0 条新增 history，active gesture 清空 |
| Curve begin rejected | 不注册 listener，不提交/取消其他 gesture |
| Phone pose pointerup | pointer capture 释放，下一次 pointerdown 可用 |
| Phone pose pointercancel/blur/hidden/close | pointer capture 释放，pointer id 清空 |
| Timeline scrub pointerup | pointermove listener 清理，正常 seek |
| Timeline scrub pointercancel/blur/hidden/unmount | 不再响应 stale pointermove |
| Director isolation | graph、Director history owner 与已有行为不回归 |
| Project gates | Batch 78 专项、Batch 71/77、跨批回归、docs check、`npm run check` 通过 |

## 4. 不在本批范围

- 改变 LibTV 源站未核实的视觉样式或交互语义；
- 把 phone runtime-only pose 强行纳入 Director undo/redo；
- 重构所有组件为一个通用 pointer hook；
- 重新识别已有截图；若需视觉证据，先阅读既有
  `SCREENSHOT_ANALYSIS.md` 记录。

## 5. 交付物

- 三处组件的最小生命周期修复；
- `scripts/verify-liblib-batch78.py` 专项 Playwright verifier；
- `runtime-audit.json`、`IMPLEMENTATION.md`、`README.md`；
- `docs/research/README.md`、验证台账和 traceability 更新；
- 保护性 commit/push，主工作区干净。

## 6. 当前状态

- [x] 读取 Batch 71/77 合同和现有实现；
- [x] 确认三处相似指针生命周期风险；
- [x] 本计划落档；
- [x] 实施三处修复；
- [x] 发现并修复跨批回归暴露的 R3F Canvas 异步 teardown 风险；
- [x] 运行 Batch 78 专项 verifier；
- [x] 运行 Batch 59、67-78 当前闸门串行回归；
- [x] 运行 `npm run check`、`npm run docs:check` 和 diff/脚本门禁；
- [x] 更新台账并 commit/push。

## 7. 实施后停止条件

本批在以下条件同时满足后结束：

- Director 三类 DOM/runtime pointer 入口在 commit、cancel、失焦、隐藏和卸载
  后均无 stale listener/capture；
- Director 快速切换、跨 canvas 自动关闭、duplicate/delete teardown 不产生
  R3F `pageerror`；
- Batch 59、67-78 当前回归、`npm run check` 和 `npm run docs:check` 均通过；
- 本文、Batch README、验证台账和 current verifier manifest 已记录结果；
- 主 worktree 是唯一 worktree，checkpoint 已提交并推送。
