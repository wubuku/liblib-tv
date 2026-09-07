# Batch 164 — 页脚触发器采样类对齐（源站 2026-09-07 链采样）

## 源站事实（触发器 DOM 链采样）

- 模型触发器：`flex items-center justify-between h-8 w-auto gap-1 rounded-lg
  px-2 py-1 min-w-[88px] shrink-0`，文本 `text-[13px]` 常规字重（非 semibold）。
- 模式触发器：`justify-center py-1 pl-2 pr-2.5`。
- 页脚行：高 32px、无顶部分隔线（`flex w-full items-start gap-1`）。

## 实施

- 模型触发器：`min-w-[88px] justify-between`、文本 `text-[13px]` 常规字重、
  chevron `shrink-0`。
- 模式触发器：`justify-center py-1 pl-2 pr-2.5 shrink-0`。
- 参数触发器：`justify-between min-w-0 shrink`。
- 页脚：`h-9 border-t pt-1` → `h-8`（去分隔线）。

## 验证器迁移

batch21 三处参数菜单 x 偏移随模型触发器增宽 +37：normal 82→119、long 90→127、
mobile 82→119。

## 验收

- `verify-liblib-batch164.py`：8 checks（min-w/justify/字号/内边距/页脚高/无分隔线）。
- 相邻回归绿：21 / 22 / 26 / 33 / 125 / 128 / 149 / 155 / 160 / 161。
- `npm run check`：0 errors、8 warnings（既有基线）。
