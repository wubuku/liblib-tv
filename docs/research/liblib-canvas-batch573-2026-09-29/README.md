# Batch 573 — 自动帧图标化 + 图标栏移动端隐藏（两处源站对齐修复）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批，含两处对齐）。

## 1. 自动帧 toggle 图标化（源站对齐）

- 源站证据：CDP 枚举（截图 55，batch 567）——自动帧为 24px **图标钮**
  （aria-label 自动帧，无文字）；clone 此前为「圆点 + 自动关键帧」
  文字钮；
- 对齐：图标钮 h-7 w-7（圆点 + aria-label/title 自动帧 +
  aria-pressed），data-director-auto-keyframe 合同保留。

## 2. 图标栏移动端隐藏（batch 536 缺陷修复）

- 回归发现：batch 536 的 DirectorIconRail 在移动端 (390px) 以
  left-0 z-30 覆盖 x 0-46px，遮住 DirectorViewport 移动端「打开场景
  对象」toggle（(12,96)），batch 36 移动流点击超时；
- 修复：rail `hidden min-[900px]:flex`（桌面 ≥900px 显示，与桌面
  布局 left-[46px] 偏移一致；移动端布局无 rail 不受影响）。

## 内容

- `src/components/director/DirectorTimeline.tsx`（自动帧图标化）；
- `src/components/director/DirectorIconRail.tsx`（移动端隐藏）；
- `scripts/verify-liblib-batch36.py`（add-track locator .first 修复 +
  add-track/关键帧流迁移至角色对象——源站 onboarding 仅角色/摄像机
  可新建轨道；TransformControls 瞬态过滤 553/558/563 留痕）；
- 回归：batch 36/536/557/563/566/70 全绿；typecheck 净；verify-docs
  pass。
