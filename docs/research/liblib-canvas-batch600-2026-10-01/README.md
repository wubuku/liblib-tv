# Batch 600 — 车道区容器栈：2px 列间隙、tiny-scrollbar、右缘圆角

日期：2026-10-01
取证：源站导演台 CDP 实测 + 产物样式表取规则（`/tmp/src593/probe43`–`probe46`）
验收：`scripts/verify-liblib-batch600.py`（9 项检查全过）

---

## 一、源站事实

从车道 canvas 往上走，源站右列是**三层**结构（probe43/44）：

```
div.flex.min-h-full.min-w-0.gap-[2px]          1920×130 @(0,1021)   gap: 2px
├─ 左列   z-10 shrink-0 bg-[#1f1f1f]            320×130 @(0,1021)
│                                              border-right: 0px
└─ pane  relative min-w-0 flex-1 bg-[#1f1f1f]   1598×129 @(322,1021)
   └─ scroller  tiny-scrollbar h-full min-w-0
               overflow-x-auto overflow-y-hidden  1598×129，scrollWidth 2124
      └─ wrap  relative shrink-0 overflow-hidden rounded-r-md bg-black/15
                2124×115 @(322,1021)，border-radius 6px 0 0 0
         └─ canvas  block h-full cursor-ew-resize  2124×115
```

### 1.1 两列之间是 2px `gap`，**不是边框**

`elementFromPoint` 在 x=318/319 命中轨道行，x=320/321 命中 flex 父容器本身，
x=322 起才是右列；且左列计算出的 `border-right-width` 是 **0px**。

### 1.2 内容盒按内容排布，圆角落在**内容右端**

内容 2124×115 装在 1598×129 的 pane 里，所以：

- `rounded-r-md` 的 6px 圆角在**滚动范围的尽头**，不是视口右缘
- 内容下方有 14px 露出 pane 的 `#1f1f1f`

### 1.3 scroller 带源站自己的 `.tiny-scrollbar`

从产物样式表
`liblibtv_online/static/_next/static/chunks/2i0zx3s0wp9uo.css`（904KB）里
原样取出（probe45）：

```css
.tiny-scrollbar{scrollbar-gutter:stable;scrollbar-width:thin;
  scrollbar-color:var(--border-emphasis) transparent}
.tiny-scrollbar::-webkit-scrollbar{width:3px;height:3px}
.tiny-scrollbar::-webkit-scrollbar-track{background:0 0}
.tiny-scrollbar::-webkit-scrollbar-thumb{
  background-color:var(--border-emphasis);border-radius:3px}
```

`--border-emphasis` 在源站 `:root` 与该 scroller 上都解析为 **`#86909c`**（probe46），
计算值核对：`scrollbar-width: thin` / `scrollbar-gutter: stable` /
`scrollbar-color: rgb(134,144,156) rgba(0,0,0,0)`。

同文件里还有相邻的 `.tiny-scrollbar-hover`（默认全透明、hover 才显色），
车道区用的是**非 hover** 那个。

---

## 二、clone 改动

### 2.1 `src/components/director/DirectorTimeline.tsx`

| 位置 | 改动 |
|---|---|
| 两列的 flex 容器 | `flex min-h-0 flex-1` → `flex min-h-0 min-w-0 flex-1 gap-[2px]` |
| 左列 | 去掉 `border-r border-white/[0.07]`（源站无右边框） |
| 右列 | 由**一层** scroller 改为 **pane + scroller** 两层：<br>pane `relative min-w-0 flex-1 bg-[#1f1f1f]`<br>scroller `tiny-scrollbar h-full min-w-0 overflow-x-auto overflow-y-hidden` |
| 内容盒（`data-director-timeline-canvas`） | `relative min-h-full min-w-full` → `relative min-w-full shrink-0 overflow-hidden rounded-r-md`（去掉 `min-h-full`，改按内容排布） |

改动后实测：左列 320 宽 @x=0、pane @x=322 宽 1598、内容 @x=322 宽 1779、
圆角右 6px 左 0、`scrollbar-width: thin` + `scrollbar-gutter: stable` +
`scrollbar-color: rgb(134,144,156)`——与源站逐项一致。

### 2.2 `src/app/globals.css`

新增源站 `.tiny-scrollbar` 的四条规则（含 `::-webkit-scrollbar` 三条），
`--border-emphasis` 直接写成 `#86909c`，注释里标明规则出处与取值依据。

---

## 三、未取证 / 不声称（记录，不臆造）

1. **源站内容盒的 `bg-black/15` 观察不到。** 包裹层与 canvas 同为 2124×115，
   而 canvas 逐像素不透明地铺满，所以这层自己的底色永远被盖住。clone 保留
   可观测的 `#212121`（实测的车道底），不去追一个看不见的颜色。
2. **clone 的车道内容比 pane 高，最后一行被裁。** clone 种子数据有两个对象
   （4 条车道行，36+128=164px），源站项目只有一个对象（2 条，100px）。这是
   **种子数据差异**不是容器差异；本批没有为了它去改面板高度（batch 36/592 的
   182/130 高度合同不动）。左列本来就 `overflow-y-auto` 会滚，车道区按源站
   `overflow-y-hidden` 裁切。
3. **`scrollbar-gutter: stable` 在本机观察不到差别**——macOS 用 overlay 滚动条，
   `innerWidth - clientWidth` 实测为 0。规则照抄，行为按平台走。
4. 源站 scroller 的最大滚动量是 `2124 - 1598 = 526`；clone 按自身内容宽
   （zoom 44 / 8s → 1779）为 181。数值不同是内容不同，不是结构不同。

---

## 四、验收合同

`scripts/verify-liblib-batch600.py` 9 项：

1. `globals.css` 声明了 `.tiny-scrollbar`（thin / stable / `#86909c` / 3px）
2. 两列之间是 2px 间隙且左列 `border-right-width === 0px`
3. 左列 320 宽 @x=0，右列 pane @x=322
4. pane 是 `#1f1f1f` 且铺满剩余宽度
5. scroller 带 3px `tiny-scrollbar`，`overflow-x: auto` / `overflow-y: hidden`，
   且 `scrollWidth > clientWidth`（确实可横向滚）
6. 内容盒按内容排布、只有右圆角 6px / 左 0、自身 `overflow: hidden`、宽于 pane
7. 内容盒仍是 `#212121` 车道底
8. 横向滚动只移动内容，左列 x 不变（scrollLeft 120 → 内容 x 322→202）
9. 无 console 报错

## 五、参考图

`docs/design-references/liblib-timeline-lane-frame-1920.png` — clone 1920×1150
下改后的车道区（2px 间隙、右缘 3px 细滚动条、滚动到底可见的右圆角）。
