# Batch 67 截图与运行证据台账

> 状态：`NO_NEW_SCREENSHOT_INSPECTION_PERFORMED`。
>
> 日期：2026-08-27。

## 1. 成本决策

本批实现的是 Director portable document 的纯数据契约、strict codec 和 contract
verifier。问题可以由 Batch 66 已完成的静态审计、稳定合同、Director 类型定义和
现有 verifier manifest 回答，不涉及新的视觉几何或 source UI 判断。

因此本批不重新打开截图、不做截图识别、不写新的 screenshot artifact。

## 2. 复用证据

- [`../liblib-canvas-batch66-2026-08-27/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch66-2026-08-27/SCREENSHOT_ANALYSIS.md)
- [`../liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md`](../liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md)
- [`../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
- [`../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)
- [`../storyai-3d-director-desk-2026-08-27/EVIDENCE_MATRIX.md`](../storyai-3d-director-desk-2026-08-27/EVIDENCE_MATRIX.md)

## 3. 允许新增识别的条件

仅在以下情况新增截图分析：

1. codec 接入 UI 后暴露 panel/selection/viewport 的视觉回归；
2. 新增 source-authenticated Director evidence，需要量测 exact geometry；
3. verifier 发现只能通过截图而不能通过 DOM/state/静态检查解释的回归。

若触发，必须记录 screenshot path、viewport、状态、DOM-backed fact、视觉估计、
不确定项和不可推出结论；不能用 StoryAI 或 clone screenshot 替代 LibTV source fact。

