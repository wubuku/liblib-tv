# Batch 602 — 左侧 rail：节奏、分隔线与配色对齐源站

日期：2026-10-01
取证：源站导演台 CDP 实测（`/tmp/src593/probe50` + nav 子节点枚举）
验收：`scripts/verify-liblib-batch602.py`（9 项检查全过）

---

## 一、源站事实

源站的图标栏是一个 `<nav>`（`/tmp/src593/probe50`）：

```
nav.border-white/8.flex.w-12.shrink-0.flex-col.items-center.gap-2.border-r.p-2
    48×1098 @(0,52)    padding 8、gap 8、border-right white/8
  嵌在 aside.absolute.inset-y-0.left-0.z-30.overflow-hidden
       .border-r.border-white/10.bg-[#171717]      281×1150，底色 rgb(23,23,23)
  上面是 52px header（左边 关闭 40×40 @(0,6)，右边 收起 40×40 @(240,6)）
```

条目一律 32×32、`rounded-lg`、**20px 图标**（`svg.size-5`），x 全为 8：

| 条目 | y | 间隙 | 状态 | 配色 |
|---|---|---|---|---|
| 场景 | 60 | – | `aria-pressed=false` | `text-white/72` / 透明 |
| **分隔线** | 100 | | 32×8 `border-white/8 h-2 w-8 border-b` | |
| 添加角色 | 116 | **24** | `aria-pressed=true` | `bg-white/10` / `text-white` |
| 添加机位 | 156 | 8 | `aria-pressed=false` | `text-white/72` / 透明 |
| 全景图 | 196 | 8 | `aria-pressed=false` | 同上 |
| 选择画幅比例 | 236 | 8 | `aria-pressed=false` | 同上 |
| AI 识图导入 | 276 | 8 | 无 `aria-pressed` | 同上 |
| 帮助 | 1110 | – | 贴 nav 底 | `rounded-lg`、20px |

**间隙序列是 [24, 8, 8, 8, 8]**——第一处 24 是「8px gap + 8px 分隔线 + 8px gap」，
其余是 8px。所以步进是 56 / 40 / 40 / 40 / 40。

clone 原先是：46px 宽、`gap-1`（**没有分隔线**，步进恒为 36）、16px 图标、
`text-[#a5a5a5]` 未选中 / `bg-white/[0.12]` 选中、`bg-[#1a1a1a]` 底色、
「帮助」是 `rounded-full`。

---

## 二、clone 改动

`src/components/director/DirectorIconRail.tsx`

1. **容器** `w-[46px] gap-1 py-3 border-r border-white/[0.07] bg-[#1a1a1a]`
   → `w-12 gap-2 p-2 border-r border-white/8 bg-[#171717]`（源站 `<nav>` 的逐字类）
2. **内层列** `gap-1` → `gap-2`
3. **新增分隔线**：`场景` 之后插一条
   `<span data-director-rail-divider class="block h-2 w-8 border-b border-white/8" />`，
   用 `Fragment` 与按钮包裹 div **平级**（源站里它也是 nav 的直接子节点）
4. **配色**：未选中 `text-white/72 hover:bg-white/8 hover:text-white`；
   选中叠 `bg-white/10 text-white`
5. **图标** 16 → 20（`<Icon size={20} />`）
6. **帮助** `rounded-full` → `rounded-lg`，同款配色，图标 20px

改后实测：rail 48 宽 / `p-2` / `gap-2` / `#171717` / `white/8`；
条目 x=8、32×32、r8、图标 20；间隙 [24, 8, 8, 8, 8]；分隔线 32×8 @(8,132)。

---

## 三、未取证 / 不声称（记录，不臆造）

1. **绝对 y 偏移没有对齐。** 源站首项在 y=60（52px header 之下），clone 在 y=92
   （84px 顶栏之下）。这不是 rail 的问题——两者上方的头部结构不同。对齐它要动
   顶栏，那是另一个面，本批只钉**节奏**。
2. **默认选中项不同。** 源站当前选中「添加角色」，clone 打开时选中「场景」。
   这是各自工程状态，验收脚本改为**驱动 clone 自己的选中态**再断言配色，
   不假设默认值。
3. **header 里的 `关闭` / `收起` 未动。** 源站 `收起` 在 280px 宽的左列 header
   右缘（x=240），clone 的顶栏是另一套结构（见下）。

---

## 四、回归

引用 rail 的 15 个既有 verifier 全部通过：50 / 536 / 538 / 539 / 540 / 542 /
546 / 554 / 562 / 586 / 587 / 589 / 590 / 93。

**batch541（`crowd:objects-increase`）失败属既有失败**：把
`DirectorIconRail.tsx` 还原到 HEAD 重跑，同一处同样失败，与本批无关。

> 注：仓库里存在他人留下的 `stash@{0}: in-progress-edit-for-revert`。
> 本批全程未使用 stash，只用 `cp` + `git checkout --` 做基线对照。

## 五、参考图

`docs/design-references/liblib-rail-602-1920.png` — clone 1920×1150 下改后的左侧 rail。
