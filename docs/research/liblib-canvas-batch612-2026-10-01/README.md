# Batch 612 — 控件普查扫尾：轴片 aria、大画布底部两簇、跟随胶囊文案

日期：2026-10-01
验收脚本：`scripts/verify-liblib-batch612.py`（112 项）
回归：`verify-liblib-batch609.py`（76/76）、`verify-liblib-batch610.py`（97/97）、`verify-liblib-batch611.py`（49/49）
参考图：`docs/design-references/liblib-bottom-clusters-612-1920.png`
审计：`docs/research/liblib-canvas-batch612-2026-10-01/runtime-audit.json`

## 靶心

照例重跑**控件全集普查**（`/tmp/src593/diff609.py src|clone`）：源站 113 个可访问名 vs clone 126 个。剩余的「源站有 / clone 无」大多是普查在**角色被选中**时跑（于是混进了源站相机面板的一批控件），或跑在了**大画布页**而非导演台。

但普查逮到三项真缺陷，其中第一项还是**我自己上一批引入的**。普查的价值不只在于找源站缺什么 —— 逐名比对会把「我抄错了但两边数量都能对上」的那类错漏出来。

## 1. 轴片的 aria/字形分工（batch 609 引入的缺陷）

源站可拖动轴片实测：

```html
<button aria-label="左右拖动调整 X 轴" class="... uppercase ...">x</button>
```

aria 用**大写轴名**，DOM 文本却是**小写 `x`**，靠 CSS `text-transform: uppercase` 渲染成大写。batch 609 我把轴名一并小写传给了 `SceneAxisScrub`，于是 clone 的 aria 变成 `左右拖动调整 x 轴` —— 普查脚本按名字比对，**根本匹配不上**，这个错漏在数量层面完全隐形。

修法：轴名保持大写传下去，字形大小写下沉到 `SceneAxisScrub` 内部（`{axis.toLowerCase()}`），`AxisFields` 传回大写。

batch 609 的验收脚本补 3 条断言（`chip:aria-upper-case-axis` / `chip:glyph-lower-case` / `chip:text-transform-uppercase`），本批再补 Y/Z 两轴的对称断言。

## 2. 大画布页底部左簇：低 6px、每枚松 4px

源站（`/tmp/src593/probe612c.py`）28 高、起点 x=14、y=1104、**簇内间隙 4px**、`rounded-lg`、14px 图标。clone 原本 y=1110 / x=16 / `gap-2`(8) / `rounded-md` / 15px 图标，误差逐枚累积：

| 控件 | 源站 | clone 改前 | clone 改后 |
|---|---|---|---|
| 资产管理 | `[14,1104,94,28]` | `[16,1110,91,28]` | `[14,1104,94,28]` |
| 整理画布，Option+Shift+F | `[112,1104,28,28]` | `[115,1110,28,28]` | `[112,1104,28,28]` |
| 切换小地图 | `[144,1104,28,28]` | `[151,1110,28,28]` | `[144,1104,28,28]` |
| 隐藏节点连线 | `[176,1104,28,28]` | `[187,1110,28,28]` | `[176,1104,28,28]` |
| 网格吸附 | `[208,1104,28,28]` | `[223,1110,28,28]` | `[208,1104,28,28]` |
| 缩放选项 | `[240,1104,36.3,28]` | `[259,1110,40.2,28]` | `[240,1104,36,28]` |

最远一枚偏了 **22px**。改法：容器 `fixed bottom-[18px] left-[14px] gap-1` + `rounded-lg` + 图标 15→14；资产管理 `px-2 gap-2` → `px-3 gap-1`（91→94）；缩放选项去掉源站没有的 `min-w-10` 与 `tabular-nums`、`px-1.5`→`px-1`（40.2→36.3）。改后六枚的 x/y/w/h **逐字相同**。

## 3. 大画布页底部中簇：我自造的 40×40 实心主按钮

源站这一簇是**均质**的，每一枚都是同一个类：

```
relative flex items-center justify-center rounded-lg transition-colors
h-8 w-8 hover:bg-canvas-controls-hover cursor-pointer      + 20px 图标
```

没有主按钮变体。clone 却给「添加节点」单做了一个 `prominent` 变体 —— 40×40、`bg-[#edf0f5] text-[#171717] hover:bg-white` 的**实心浅色药丸**：既比源站大 8px，又把整簇左顶了 19.5px。

删掉 `prominent` prop 与变体；「添加节点」图标 22→20、全部图标 17→20；并在快捷键前补 `ml-[9px]`，凑出源站生成历史↔快捷键之间那 17px 的分隔（其余枚是 8px）。

**剩余 20px x 偏移来自 clone 独有的「打开工具箱」按钮，保留** —— 删 clone 功能来对齐几何不是本工作的目的，这处偏移在验收脚本里显式记录、只比对尺寸不比 x。

## 4. 跟随浮层「取消」胶囊是单文本节点

源站实测（`/tmp/src593/probe612b.py`）：`own='取消ESC'`，**无子元素**，整枚 12px/12px/500，63.7 宽。clone 拆成了「取消」+ 10px 的 `ESC` 两层。改回单文本节点。

**顺带记录源站自身的 a11y 矛盾**：可访问名 `aria-label="退出跟随"` 与可见文案 `取消ESC` 不符。这是源站的问题，两边都**不默默「修正」**，只记录。

clone 保留 `pointer-events-auto`（源站那枚继承 `pointer-events:none`，是个点不动的死按钮）—— 这处有意偏离沿用 batch 605 的既定原则。

## 附带记录

hover 提示精确读数（`probe612b`）：`absolute left-1/2 top-full z-10 mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1 text-xs font-normal text-white opacity-0`，实测 82.1×24 @(960.9, 33)，由按钮的 `peer-hover` 显形。

## 验收设计上的两处自纠

- `rounded-full` 在 **Tailwind v4** 是 `border-radius: calc(infinity * 1px)`，computed 值是 `3.35544e+07px` 而非 v3 的 `9999px`。断言改成判幅度不判字符串。
- 首版把轴片断言放在**大画布页**读，而轴片在导演台里 —— 移到进导演台之后读；顺手补上 Y/Z 两轴。

## 不声称

- 源站这一批按钮的**点击行为**未取证（点了会写进用户真实项目）。几何、配色、字号、字形尺寸都是实测的；「改完还能用」由 clone 侧的面板能正常打开来证明（添加节点 / 缩放选项 / 快捷键 / 生成历史四枚都点了）。
- 底部中簇的 x 不声称逐字相同（clone 多一枚按钮，见上）。
