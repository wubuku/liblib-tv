# Batch 87：Director undo/redo selection authority

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是 clone-owned Director 恢复一致性修复，不是 LibTV 原站 Director
> source-exact 结论。

## 入口

- [`PLAN.md`](PLAN.md)：背景、策略、范围和验收标准；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、回归和证据边界；
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果；
- [`../../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  当前 Director verifier 入口；
- [`../liblib-canvas-batch86-2026-08-29/`](../liblib-canvas-batch86-2026-08-29/)：
  变换目标上下文与 pointer cleanup 前置合同；
- [`../../../src/store/directorStore.ts`](../../../src/store/directorStore.ts)：
  selection repair 与文档恢复实现。

## 本批结论

- Director portable V1 document 继续不保存 selection、viewport、panel 或
  playhead 等 UI runtime；
- 首次打开/重开仍使用确定性默认选择；
- undo/redo 和 gesture cancel 的文档恢复使用当前 selection 的
  preserve-and-repair 策略；
- 恢复后会清理不存在的对象、分组、track、keyframe、motion path 和 anchor
  selection；
- 对象树、Inspector、Viewport transform context 和 Timeline 不再因为恢复动作
  各自选择不同目标；
- 该策略属于 clone-owned authority，LibTV 原站 Director 的 undo selection policy
  仍为 `SOURCE_UNKNOWN`。

## 验证摘要

`runtime-audit.json` 记录了以下 fresh-page 场景：

- 对象选择与 timeline track 基线一致；
- accepted object mutation 只增加一条 history；
- undo/redo 后对象树、Inspector、Viewport 仍指向同一对象；
- 非法 object/group/timeline selection 被清理；
- export 后的 portable document 不含 selection 字段；
- console/page/request diagnostics 为 `0 / 0 / 0`。

本批没有新增截图；执行截图识别前应先查已有
`SCREENSHOT_ANALYSIS.md`，本批问题由 store/document contract 直接回答。

