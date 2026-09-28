# Batch 566 — 地面高度字段端到端

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：CDP 截图 52
> （2026-09-29，3D 场景面板地面区）——地面含 透明度 0.40 滑杆 **加
> 高度 0.0 滑杆**（batch 548 遗漏字段，本次补齐）。

## 合同

- `DirectorScene` 新增 `groundHeight`（默认 0）；
- V1 文档 optional 字段 + `expectScene` 兼容解码（expectFiniteNumber）；
- 场景属性显示区新增「地面高度」滑杆（-2..2，step 0.1，一位小数
  角标），经 updateScene 持久化，正负值均支持；
- 渲染接线：地面 mesh position Y = groundHeight - 0.01（保持与网格
  0.006 的层叠关系）。

## 内容

- `src/store/directorStore.ts`（schema + defaults + 白名单）；
- `src/lib/directorProjectDocument.ts`（V1 optional + 解码）；
- `src/components/director/DirectorInspector.tsx`（地面高度滑杆）；
- `src/components/director/DirectorViewport.tsx`（地面 mesh Y 接线）；
- `scripts/verify-liblib-batch566.py`（6 检查：默认 0、0.5 持久、-1
  负值、角标）；
- 回归：batch 548/558/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
