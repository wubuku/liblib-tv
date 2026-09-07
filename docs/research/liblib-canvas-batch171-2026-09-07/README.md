# Batch 171 — 左下资产管理栏几何对齐（源站 2026-09-07 采样）

## 源站事实（画布左下 DOM）

- 栏容器 `fixed bottom-3 left-4 z-10 flex items-end gap-2`（280×40），
  无内边距盒。
- 「资产管理」按钮 94×28（rounded-lg、13px、hover token）。
- 缩放「100%」胶囊 42×28（rounded-lg、13px），右对齐。

## 实施

- 栏容器 `h-10 items-center gap-1 p-1.5` → `h-10 items-end gap-2`。
- 资产管理按钮 `rounded-md text-xs` → `rounded-lg text-[13px]`。
- 缩放胶囊 `rounded-md text-xs` → `rounded-lg text-[13px]`。
- 中间功能图标（整理/缩略图/连线）保留（功能性原型特性，源站对应位置未采样）。

## 验收

- `verify-liblib-batch171.py`：8 checks（资产按钮/缩放胶囊几何与圆角/0 diagnostics）。
- 相邻回归绿：17 / 100 / 115。
- `npm run check`：0 errors、8 warnings（既有基线）。

## 源站重探（同期）

模型菜单仍不挂载（遮挡限流），菜单选中态/300s 参数展开继续阻塞。
