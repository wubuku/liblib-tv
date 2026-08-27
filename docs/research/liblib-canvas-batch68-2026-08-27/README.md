# Batch 68: Director Owner Registry And Session Lifecycle

> 状态：`COMPLETE / OWNER_SESSION_FOCUSED_PASS`。
>
> 建档日期：2026-08-27。
>
> 前置批次：[`liblib-canvas-batch67-2026-08-27`](../liblib-canvas-batch67-2026-08-27/README.md)。

## 目标

把 Director 从“`sourceNodeId` 变化、其余单例状态继续沿用”推进为按
`route + canvasId + sourceNodeId` 隔离的内存 project/session authority：

- 每个 owner 有独立且稳定的 project ID；
- 每次成功 open/reopen 有可验证的 session ID 与 generation；
- A -> B -> A、跨 canvas 切换不再串 scene、objects、timeline 和 captures；
- close 只结束当前 session，内存 project 可重新打开；
- source owner 失效时当前 session 被关闭，延迟工作可依据 generation 判 stale；
- Batch 67 `DirectorProjectDocumentV1` 作为 portable project payload。

本批优先修复 StoryAI/Open Canvas 评估共同指出的可靠性短板，不增加新的 Director
视觉面板、真实资产、云存储或 LibTV source-exact 主张。

## 证据边界

- LibTV clone 事实与正式边界：
  [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)。
- Batch 67 已完成 strict codec，但没有接入 store authority：
  [`liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md`](../liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md)。
- StoryAI 的 versioned project、scoped session/persistence 只作为方法启发：
  [`BORROWING_DECISION_MATRIX.md`](../storyai-3d-director-desk-2026-08-27/BORROWING_DECISION_MATRIX.md)。
- Open Canvas 的 stable document owner、hydrate 和 multi-document lifecycle 只作为
  方法启发：[`ADOPTION_DECISION_MATRIX.md`](../open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md)。
- 当前没有新的 authenticated LibTV Director UI 或 persistence 证据。

## 交接入口

- [`PLAN.md`](PLAN.md)：实施切片、决策、验收与停止条件；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图零重复识别台账；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：后续代码、验证和提交记录；
- [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  `LIBTV-VR-024` 当前 gate。

## 本批明确不解决

```text
browser persistence / cloud sync / import-export UI
authored objects 与 timeline sampled projection 的最终拆分
Director undo/redo / gesture history / reference-aware object delete
真实 mesh / panorama / resource lease
multi-camera / shot lifecycle
capture/export 的完整 async graph destination transaction
LibTV source-exact DOM/CSS/文案校准
```

## 工作方式

本批及后续实现保持在 `master` 主工作区。除非用户明确要求某个功能使用隔离
worktree，不再自动创建并行 worktree。

## 完成结论

Batch 68 已实现并验证：

- structured `route + canvasId + sourceNodeId` owner key；
- per-owner project ID、per-open session ID 与 monotonic generation；
- A -> B -> A、cross-canvas、close/reopen document 和 capture sidecar 隔离；
- same active owner focus no-op；
- duplicate owner 使用新默认 project，不共享原 project；
- active source delete 关闭 session，不回绑其他 canvas/source；
- Director session open/switch/close 对普通 graph/history 零额外 mutation。

本批没有完成 authored/runtime split、inactive owner tombstone reconciliation、
async capture/export destination、Director history/delete 或 persistence。下一批最高
价值切片是 `DIR-PROJECT-I03` authored/runtime projection split。
