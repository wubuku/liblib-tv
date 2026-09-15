# Batch 518 — GRAPH-ENTRYPOINT focused fixture：跨入口一致性聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。同一语义提案
> （新增 text 节点）经两条入口的结果对比：React Flow change 回调入口被
> T 门拒绝（零残缺），命名命令 `addNode` 入口受理且恰一步 history；
> 纯选择批次（T0）经 change 回调放行（APPLIED_SELECTION）；陈旧快照
> （未知节点 id）被拒。`planLibTVReactFlowChanges` 以 dev-only window
> 暴露（含对称 cleanup）。组合式全量 corpus 未建（留档）。

## 内容

- `src/app/page.tsx`：`__libtv_change_routing_plan` 暴露；
- `scripts/verify-liblib-batch518.py`（4 场景）；
- FIXTURE_CATALOG GRAPH-ENTRYPOINT 状态升级（双表）；
- `runtime-audit.json`：本目录。
