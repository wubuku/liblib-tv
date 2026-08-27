# Batch 66: Director Reliability Authority

> 状态：`STATIC_AUDIT_RECORDED / CONTRACTS_IN_PROGRESS`。
>
> 建档日期：2026-08-27。
>
> 基线：`ca2f4e5`，Batch 65 已收口并推送。
>
> 上游固定版本：`storyai-3d-director-desk@8c8bd36`。

## 目标

本批吸收 Open Canvas 与 StoryAI Director Desk 两轮评估中最高价值的工程结论，
为当前 Director 建立三项可执行权威：

1. project / session / owner / persistence 边界；
2. command / history / reference-aware delete 边界；
3. 17 个历史 Director verifier 的 current manifest。

当前 Director 的可见能力已经足够丰富，下一阶段优先降低单例 session、不可恢复
项目、无领域 undo/redo、删除引用悬空和回归入口碎片化带来的风险。

## 证据边界

- StoryAI 只提供 `UPSTREAM_FACT` 和可借方法，不代表 LibTV 原站实现；
- 当前代码提供 `CLONE_STATIC_FACT`；
- 历史 batch 只提供 `HISTORICAL_RECORDED_PASS`；
- 没有新的登录态 Director 证据时，不新增 `LIBTV_SOURCE_FACT`；
- 本批不重复识别历史截图，不从 clone 或 StoryAI 视觉推导 source-exact UI。

## 接力入口

- [`PLAN.md`](PLAN.md)：问题、价值排序、产物、验证和停止条件；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图复用与零重复识别台账；
- [`STATIC_AUDIT_2026-08-27.md`](STATIC_AUDIT_2026-08-27.md)：当前
  project/session、mutation/history 和 reference/delete 静态审计；
- [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)：上游、clone、历史验证、建议和未知项；
- 后续 implementation record 将继续放在本目录；
- 稳定合同与 current manifest 将放在 `docs/research/` 并接入文档 Hub。
