# Batch 68 截图识别台账

> 状态：`ZERO_NEW_RECOGNITION_PLANNED`。
>
> 日期：2026-08-27。

## 决策

本批是 Director owner registry/session lifecycle 可靠性切片，不改变 source-exact
视觉目标。现有 StoryAI/Open Canvas 截图不能证明 LibTV Director 的 project/session
语义，Batch 35-50/59 已有 Director clone runtime 视觉记录。

因此计划阶段不打开、不重新识别任何历史截图，也不采集新的源站截图。

## 可复用证据

- Director 当前可见 shell 与 runtime：
  [`storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md`](../storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md)；
- 当前低成本浏览器 smoke：
  [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)；
- Batch 59 的资源库/WebGL/响应式记录：
  [`liblib-canvas-batch59-2026-08-27/`](../liblib-canvas-batch59-2026-08-27/)。

## 重新识别触发条件

仅在以下情况新增最小截图或视觉识别：

- owner/session 接入导致 workspace、tree、Inspector、timeline 可见回归；
- desktop/mobile 边界或 WebGL framing 与 Batch 59 不一致；
- 新的 authenticated LibTV Director fixture 可用于 source calibration；
- prior ledger 明确缺少当前问题所需状态。

若触发，先记录 viewport、owner、project/session/generation、交互状态与最小 crop，
不重复识别整张历史截图。
