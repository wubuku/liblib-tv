# Batch 166 — 提示词区视觉对齐 + AutoLink 芯片移除（源站 2026-09-07）

## 源站事实

- 提示词滚动区 `generator-prompt-scroll-region` **无底色、无圆角**
  （`relative z-10 -mr-2 w-auto min-h-20 max-h-[100px]`）；clone 的
  `rounded-xl bg-black/10` 黑底圆角框为多余视觉。
- 两种已采样面板状态（预设承载节点、新建节点）的工具行都只有 5 个 pill，
  无「3 个匹配」AutoLink 芯片；且该芯片打开的 advanced 弹窗早已被
  Batch 149 内联列取代（死 UI）。

## 实施

- 提示词 textarea 去 `rounded-xl bg-black/10`（保留 p-2 内边距与 flex-1）。
- 移除「3 个匹配」芯片及其注释（`autoLink` 状态仍驱动高级设置开关行）。

## 验收

- `verify-liblib-batch166.py`：6 checks（透明底/无圆角/可编辑/无芯片/工具行
  5 pill 保留/0 diagnostics）。
- 相邻回归绿：21 / 22 / 26 / 125 / 128 / 155 / 160 / 164。
- `npm run check`：0 errors、8 warnings（既有基线）。
