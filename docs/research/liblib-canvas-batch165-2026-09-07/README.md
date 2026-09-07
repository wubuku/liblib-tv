# Batch 165 — 引用槽行布局对齐（源站 2026-09-07 槽行类）

## 源站事实

承载节点槽行容器类：`nopan flex w-full min-w-0 flex-wrap items-start gap-2
pl-1`，行高 55（即槽高，无固定行高）；所有已采样面板状态中均无
「Auto Link：」汇总文字。

## clone 缺陷

槽行 `flex h-12 items-center gap-2`（48px）——55px 槽被行高裁切/溢出 7px，
且带源站不存在的 Auto Link 汇总。

## 实施

- 槽行改为采样类：`flex w-full min-w-0 shrink-0 flex-wrap items-start gap-2 pl-1`。
- 移除「Auto Link：{referenceSummary}」段落与未用的 useMemo。
- 工具行的「3 个匹配」AutoLink 芯片保留（底部面板时代采样，本次面板状态
  未出现，存疑不删）。

## 验收

- `verify-liblib-batch165.py`：7 checks（行高 ≥55 / items-start / 槽 48×55 /
  无 Auto Link 文字 / 0 diagnostics）。
- 相邻回归绿：21 / 22 / 125 / 128 / 155 / 160 / 164。
- `npm run check`：0 errors、8 warnings（既有基线）。
