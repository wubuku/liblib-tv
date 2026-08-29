# Batch 81：Director 严格项目导入/导出

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-29。

Batch 81 把已有 `DirectorProjectDocumentV1` codec 变成一个可发现、可恢复、
可验证的本地工作流：用户可以导出当前导演台的 authored project JSON，也可以
选择一个 JSON 文件，在严格校验通过后替换当前 Director project。

## 入口

- [`PLAN.md`](PLAN.md)：范围、决策、fixture、验证和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施历史、运行结果和 checkpoint；
- [`current-gate-regression.json`](current-gate-regression.json)：本批专项与回归
  结果；
- [`../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  owner、session、document、persistence 和 lifecycle 总合同；
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  `LIBTV-VR-024` 当前 Director gate；
- [`../liblib-canvas-batch80-2026-08-28/`](../liblib-canvas-batch80-2026-08-28/)：
  durable tombstone 与 cleanup 前置边界。
- [`runtime-audit.json`](runtime-audit.json)：本批 pure/browser 验证结果、端口、
  诊断和 source-parity 边界。

## 结果

Batch 81 已完成 strict Director project JSON import/export 的 clone-owned
vertical slice。fresh BrowserContext 验证确认：下载文件可回读，导入会将
owner/project identity 重绑定到当前 session，保留 authored entity/reference
identity，排除 capture/runtime/UI bytes，并以一条 Director history 支持
undo/redo；非法输入为 zero-partial，同文档导入为 `NOOP`，ordinary graph/history
保持不变。

本批没有新增 LibTV 原站 source-exact 结论，也没有引入远端同步或真实资源
materialization。

## 重要边界

- 这是 clone-owned 本地文件 workflow，不是 LibTV 原站导入/导出行为的
  source-exact 证明；
- 文件格式只接受当前严格 `DirectorProjectDocumentV1`，未知字段、future schema、
  dangling reference、非有限数值和 data/blob resource locator 都拒绝；
- 导入文件的 `projectId`、owner、generation 只作为被验证的来源 metadata，成功
  导入后重绑定到当前 active Director project，避免跨节点身份串用；
- 导入是一个 Director semantic replacement，成功时产生一个 history entry，可用
  undo/redo 恢复前后 authored state；
- 导入不伪造截图 bytes、local File、Blob、Object URL、Three.js object、selection、
  playhead、panel、phone runtime 或 ordinary canvas graph state；
- persistence 写失败沿用 Batch 74/80 的 `SESSION_ONLY` 语义，不阻止当前会话继续
  使用，也不把失败报告为 durable export/import。

## 相关代码

- [`src/lib/directorProjectDocument.ts`](../../../src/lib/directorProjectDocument.ts)
- [`src/lib/directorProjectRuntimeAdapter.ts`](../../../src/lib/directorProjectRuntimeAdapter.ts)
- [`src/store/directorStore.ts`](../../../src/store/directorStore.ts)
- [`src/components/director/DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx)
- [`scripts/verify-liblib-batch81.mjs`](../../../scripts/verify-liblib-batch81.mjs)
- [`scripts/verify-liblib-batch81.py`](../../../scripts/verify-liblib-batch81.py)
