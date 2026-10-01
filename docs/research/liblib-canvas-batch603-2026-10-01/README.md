# Batch 603 — 属性面板页签条：几何与胶囊样式对齐源站

日期：2026-10-01
取证：源站导演台 CDP 实测（`/tmp/src593/probe49`，选中 主机位 时采样）
验收：`scripts/verify-liblib-batch603.py`（12 项检查全过）

---

## 一、源站事实

源站的页签条是**两层**：外层 `<section>` 负责边框与内边距，内层是横向滚动但
**隐藏滚动条**的页签条。

```
section.border-white/8.relative.w-full.min-w-0.max-w-full.overflow-hidden
       .border-b.px-4.pb-3                        280×57 @(1640,48)
  div.scrollbar-hide.flex.w-full.min-w-0.max-w-full.gap-2
      .overflow-x-auto.overflow-y-hidden.pt-4      248×44 @(1656,48)
```

高度拆得开：`pt-4` 16 + 页签 28 + `pb-3` 12 + 1px 下边框 = **57**。

页签逐字为
`relative flex h-7 min-w-12 shrink-0 items-center justify-center rounded-lg px-3
text-[13px] font-normal transition-colors`——**内容自适应 + 48px 下限**，
不是等分列：

| 页签 | 盒 | 间隙 | 状态 | 配色 |
|---|---|---|---|---|
| 属性 | 50×28 @(1656,64) | – | 选中 | `bg-white/10` / `text-neutral-50` |
| 运动轨迹 | **76**×28 @(1714,64) | 8 | 未选中 | `text-white/45` / `hover:bg-white/6` |
| 截图 | 50×28 @(1798,64) | 8 | 未选中 | 同上 |

`运动轨迹` 上挂 NEW 角标，逐字为
`span[aria-hidden].pointer-events-none.absolute.right-0.top-0.z-10.flex.h-5
-translate-y-[70%].items-center.justify-center.rounded-t-lg.rounded-bl-sm
.rounded-br-lg.bg-[#5DDCFF].px-1.5.text-[11px].font-medium.leading-3.text-black`。

clone 原先是 `grid h-9 grid-cols-3 p-1`：**等宽分列 + 固定 36px 高**，
页签 `rounded`（4px）、11px 字号，选中 `bg-[#292929] text-[#d9d9d9]`，
NEW 角标是 `rounded-full` + 8px + `bg-[#09caf5]`。

---

## 二、clone 改动

### 2.1 `src/components/director/DirectorInspector.tsx`

摄像机页签条：

- `<nav>` 外壳 → 源站 `<section>` 的类：
  `relative w-full min-w-0 max-w-full shrink-0 overflow-hidden border-b border-white/8 px-4 pb-3`
- 内层新增 `<div className="scrollbar-hide flex w-full min-w-0 max-w-full gap-2 overflow-x-auto overflow-y-hidden pt-4">`
- 页签 → 源站逐字类（`h-7 min-w-12 rounded-lg px-3 text-[13px] font-normal`），
  选中 `bg-white/10 text-neutral-50`，未选中 `text-white/45 hover:bg-white/6 hover:text-white/75`
- 文字包一层 `<span className="shrink-0">`（与源站 innerHTML 一致）
- NEW 角标 → 源站逐字类（`#5DDCFF`、`h-5`、`-translate-y-[70%]`、四角异形、11px medium black、`aria-hidden` + `pointer-events-none`）

角色页签条同步换成同一套外壳与胶囊样式。

### 2.2 `src/app/globals.css`

新增源站 `.scrollbar-hide`（`-ms-overflow-style:none; scrollbar-width:none`
+ `::-webkit-scrollbar{display:none}`），规则同样取自产物样式表
`2i0zx3s0wp9uo.css`。

改后实测：section 287×57、strip 255×44、页签 50/76/50 全部 28 高、
gap 8、radius 8px、13px、`#5DDCFF` 角标 38×20 —— 与源站逐项一致（绝对 x 因
面板宽度不同而不同，见下）。

---

## 三、未取证 / 不声称（记录，不臆造）

1. **页签集合本身没动。** 源站**摄像机**检查器实测就是「属性 / 运动轨迹 / 截图」，
   与 clone 自 batch 581 起就一致，所以无需改。**角色**检查器的页签集合在源站
   没采到样（当前工程只有机位是已选中状态，切到角色需要在源站点选对象），
   clone 的「属性 / 姿势」保留，只对齐共用外壳——**这一项是推断**。
2. **绝对 x 没对齐。** 源站 section @x=1640 宽 280，clone @x=1633 宽 287。
   面板宽度/位置是另一件事，本批只钉页签条自身。
3. 「截图」页签的行为仍未取证（点它可能触发真实截图或写工程），本批**没有**新增
   任何不可验证的行为。

---

## 四、参考图

`docs/design-references/liblib-inspector-tabs-603-1920.png` — clone 1920×1150
下改后的摄像机属性面板页签条（50/76/50 + NEW 角标）。
