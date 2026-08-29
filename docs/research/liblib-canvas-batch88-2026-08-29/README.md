# Batch 88：Director selection、Timeline 与变换目标一致性

> 状态：`RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是当前五批连续迭代中的第五批，也是本轮最后一批。完成后暂停，
> 等待 review，不启动 Batch 89。

## 入口

- [`PLAN.md`](PLAN.md)：本批缺口、clone-owned 决策、范围和验收标准；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证命令、回归和证据边界；
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果；
- [`current-gate-regression.json`](current-gate-regression.json)：Batch 59、67–88
  current-gate 串行结果；
- [`../../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  Director 当前验证入口；
- [`../../../src/store/directorStore.ts`](../../../src/store/directorStore.ts)：
  selection normalization、删除修复和直接编辑入口；
- [`../../../src/components/director/DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)：
  Inspector 与 Timeline selected track authority。

## 本批结论

- 单对象选择会保留同一对象的当前 track；切换对象时优先使用该对象的非
  pose track，再退化到 pose track；无轨道则清空 Timeline entity selection。
- 多对象选择不再继承单目标的 track、keyframe、motion path 或 anchor。
- 分组选择只使用当前 group 的 group track；没有 group track 时保持空的
  Timeline entity selection。
- Timeline track、keyframe 和 motion-path anchor 反向更新对象树、Inspector、
  Viewport transform context 和 R3F 目标。
- 删除、undo/redo、gesture cancel 和直接对象/相机/姿态/路径/剪贴板入口都经过
  同一套合法性约束，避免悬挂目标。
- selection、Timeline UI 状态和 TransformControls 引用仍不进入 portable Director
  document 或 Director document history。

这些是当前 clone 的可靠性决策，不是 LibTV 原站 Director 的 source-exact
selection、Timeline 联动或 undo policy。

## 验证摘要

```bash
node --experimental-strip-types scripts/verify-liblib-batch88.mjs
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch88.py
```

两项专项 verifier 均通过。fresh-page 场景覆盖对象切换、多选、分组轨道、
Timeline 反向选择、关键帧/路径归属、删除修复、锁定零变更、portable document
边界、移动端几何和 browser diagnostics。

本批不新增截图；问题由 store/component authority 和结构化 runtime audit 回答。
执行截图识别前仍应先查已有 `SCREENSHOT_ANALYSIS.md`。

## Closeout Note

最终串行回归中先发现并修复了两个相邻兼容问题：

- Batch 72：对非当前选择相机更新关系时不应抢占当前 object/group selection；
- Batch 87：restore repair 清理非法 track 后不应按 fallback 规则凭空重新选择
  该对象的其他轨道。

两项修复后的 Batch 59、67–88 串行结果均为通过；本批文档、全量检查和
commit/push 已完成。
