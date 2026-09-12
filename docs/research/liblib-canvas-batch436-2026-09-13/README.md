# Batch 436 — VR-017 Slice B：page transaction invalidation（页面级事务按画布作废）

> 状态：`IMPLEMENTATION_RECORDED`（多画布 lifecycle 合同 Slice B；
> clone-only 正确性，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch436-organize-cancel-929-2026-09-13.png`、
> `scripts/verify-liblib-batch436.py`。

## 变更（src/app/page.tsx）

§5.5 三个页面级 transient holder 此前无画布身份，跨切换可把旧画布的
快照/基线/手势写进新画布。本批按 batch 65 的 owner 模式收口：

- **organizeSnapshot**：武装时捕获 `canvasId`；确认条可见性**派生自
  武装画布**（`liveOrganizeSnapshot`）——切到其它画布即隐藏且失效；
  `restoreOrganize` 在当前激活画布 ≠ 武装画布时只丢弃不应用
  （GC-047 不变量：旧快照不得改写新画布）。回到武装画布条带复现，
  还原在其自身画布上仍可用（owner 作用域事务，而非清空式取消）；
- **dragHistorySnapshot**：拖拽基线捕获 `canvasId`；迟到 stop 落在
  其它画布时早退、不记录任何历史（GC-048）；
- **connectionGesture**：仍只写不读（诊断占位）；
- **switch 清理**：`activeCanvasId` 变更的 effect 清空两个匿名 ref
  holder（organizeSnapshot 走派生可见性，规避 effect 内同步 setState
  的级联渲染 lint 规则）。

viewport 路径的 captured-canvasId 守卫 batch 65 已建，本批未动；
正常 UI 几何不变。

## 验收（verify-liblib-batch436.py，SCRIPT_RECORDED_PASS）

- **drag_history_regression**：真实节点拖拽仍恰好 +1 条历史、位置变更
  （owner 绑定不改变正常几何）；
- **organize_switch_cancel（GC-047）**：整理后确认条可见；切画布 →
  条带消失且目标画布 graph/history 逐字节不变；切回武装画布 → 条带
  复现、整理结果保留；点击 还原 → 历史 +1、布局还原、条带关闭；
- console/pageerror/requestfailed 为 0；desktop 929 无溢出。

## 浏览器未断言（代码守卫 + 结构性关闭）

- connectionGesture 迟到窗口（holder 从不被读取；切换即清）；
- 跨画布迟到 drag stop 分支（React Flow `key={activeCanvasId}` 重挂载
  关闭该窗口；代码内仍有 owner 守卫兜底）。

## 后续（VR-017 剩余）

demo viewport ownership 余项（resize anchor、live/stable endpoint）、
async/resource isolation（Slice E）。
