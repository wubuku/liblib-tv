# Batch 84：Director 对象树锁定与编辑保护

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。

本批将 StoryAI 上游对象树的 visibility/lock 并列控制方法，适配到当前独立
R3F Director clone，并补齐 locked object 的编辑拒绝边界。

## 入口

- [PLAN.md](PLAN.md)：范围、合同和验收标准。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：代码变更、验证和证据边界。
- [runtime-audit.json](runtime-audit.json)：fresh-page Playwright 结构化结果。
- [`DirectorObjectTree.tsx`](../../../src/components/director/DirectorObjectTree.tsx)：对象树控制。
- [`DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)：属性/姿态/路径保护。
- [`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)：R3F TransformControls 保护。
- [`DirectorTimeline.tsx`](../../../src/components/director/DirectorTimeline.tsx)：路径/关键帧入口保护。
- [`DirectorCurveEditor.tsx`](../../../src/components/director/DirectorCurveEditor.tsx)：速度曲线保护。
- [`directorStore.ts`](../../../src/store/directorStore.ts)：直接 action guard。

## 当前结论

- 锁定入口可在对象树和 Inspector 发现；
- locked object 仍可选择、隐藏/显示和结构删除；
- locked object 的属性、变换、相机、姿态、路径和曲线编辑被停用或 typed reject；
- locked reject 使用 `DIRECTOR_TARGET_LOCKED`，不修改 project document，不新增 history；
- 解锁后原有编辑路径恢复；
- 结论属于 clone-owned contract，不能替代 LibTV authenticated source evidence。
