# Batch 515 — VR-012 focused fixture：默认 node-data 注册表聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> `getDefaultNodeData`（dev-only window 暴露）：11 个 runtime 类型全部
> 有默认数据、两次调用深相等（确定性）、JSON round-trip 深相等
> （JSON 安全）、默认数据无 selected/dragging/measured/style 等
> runtime/session 键。`style`/`effect` 两个非 runtime 默认分支存在
> （与 STATIC_AUDIT §4 一致）——按 STATIC_FACT 留档不判失败。

## 内容

- `src/app/page.tsx`：`__libtv_default_node_data` 暴露（dev-only，
  含对称 cleanup）；`canvasStore.getDefaultNodeData` 加 export；
- `scripts/verify-liblib-batch515.py`：4 断言 + 额外分支发现；
- FIXTURE_CATALOG NODE-DATA 状态升级；
- `runtime-audit.json`：本目录。
