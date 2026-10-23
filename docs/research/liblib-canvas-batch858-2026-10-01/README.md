# batch 858 — 导演台「添加角色」**面板化**（源站左侧面板模式 ＋ crowd 对话框逐字）

> 靶子：batch 857 登记的 **D1**（clone 把「添加角色」做成浮层 ⟹ ⟹ 与场景树完全重叠
> ⟹ ⟹ 场景树看着能点、其实点不动）⟹ ⟹ 改成**源站逐字的左侧面板模式**。
> 顺带把 **D2**（对话框高 208 vs 204）、**D3**（落点 281 vs 280）一并结案。

## 0. 一句话结论

clone 的「添加角色」原先是**盖在场景树上的浮层**；源站是**左侧资源栏的一个视图**
（与场景树**互斥**）。本批按源站逐字改成面板后，**几何逐字命中源站实测**：

| 量 | 源站实测 | clone（本批后） |
| --- | --- | --- |
| 「添加角色」面板 | @(48,52) 宽 **232** | @(48,52) 宽 **232** ✔ |
| 标题条 | h-**48**、12px、文本「添加角色」 | 同 ✔ |
| 11 行 | y=100…420，每行 **32px**/13px、x=**56** 宽 **216** | 同 ✔ |
| 「群众 (3x3)」按钮 | **(56,388) 216×32** | **(56,388) 216×32** ✔ |
| 「几何模型」就地展开 | **(68,452) 204×256**，8 项各 **199×32** | 同 ✔ |
| 群众对话框 | **(280,388) 220×204**、z **1800**、bg `rgba(31,31,31,0.98)` | 同 ✔ |
| 对话框内部三段 | 标题行 20 / 网格 106 / 页脚 28、label 行高 **17.05px** | 同 ✔ |
| 场景树 | **不在场**（模式互斥） | **不在场** ✔ |

★ 而 **D1 的病根**（浮层截走场景树的点击）随之**根治**：切到「添加角色」时
**场景树根本不渲染** ⟹ ⟹ 没有东西可以互相遮挡。

★ **验收**：门禁 **38/38**｜阴性 **7/7**（全部字节级复原）｜回归 **94 条**（红 13 条：
**12 条已知旧账** ＋ 1 条 `626` 经定点归因证明是**时序抖动**、判据已改成对时序鲁棒，
复跑两遍只剩 D7 那条源站同款的旧账）｜受控对照 **3 态**（HEAD 全回退／WORK／
**MIX 半回退**）⟹ ⟹ 稳定 ＋ 有牙 ＋ 复原三项全 True。

## 1. 源站逐字依据（源站 chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）

★ 本批的核心证据是**源站 chunk 的逐字**，不是截图转录：

```
① 左侧资源栏是一个**多视图**容器，五个模式**互斥**：
   e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col bg-[#171717]",
     children:["scene"===z?n:null,"character"===z?(…添加角色…),
               "camera"===z?(…),"panorama"===z?(…),"aspect"===z?(…)]})
   ⟹ ⟹ 「添加角色」**不是浮层**，它是左侧面板的一个**视图**。
   ⟹ ⟹ 切到 character 时 `"scene"===z?n:null` ⟹ ⟹ **场景树不渲染**。

② rail 的按钮是 `aria-pressed={z===r.id}`：
   <button aria-label={r.label} aria-pressed={z===r.id}
     className=cn("text-white/72 hover:bg-white/8 flex size-8 …", z===r.id&&"bg-white/10 text-white")
     onClick={()=>{F(r.id),N(!1),O(null),e&&t(!1)}}>
   ⟹ ⟹ ★ 选中态**完全由左侧面板模式派生** ⟹ ⟹ clone 此前自带一份 `active`
   状态 ⟹ ⟹ 两处真相 ⟹ ⟹ 本批删掉第二份。

③ 标题条 `aO`：
   function aO({children:e}){return (0,i.jsx)("div",{className:"flex h-12 shrink-0
     items-center px-3 text-[12px] leading-5 text-white/90",
     children:(0,i.jsx)("span",{className:"truncate",children:e})})}

④ 行样式 `eu`：
   eu="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-[13px]
       leading-5 text-white/88 transition-colors hover:bg-white/8
       disabled:cursor-not-allowed disabled:opacity-45"

⑤ 列表容器："min-h-0 flex-1 overflow-y-auto px-2 pb-3"

⑥ 几何模型**就地展开**（不是浮层）：
   "geometry"===L?(0,i.jsxs)("div",{className:"border-white/8 ml-3 border-l pl-1", …})

⑦ ★ crowd 与 geometry **共用一个状态变量 L**：
   crowd 按钮  "aria-haspopup":"dialog","aria-expanded":"crowd"===L,
                className=cn(eu,"crowd"===L&&"bg-white/8")
   geometry   className=cn(eu,"geometry"===L&&"bg-white/8")
   ⟹ ⟹ 开一个 ⟹ ⟹ 关另一个 ⟹ ⟹ clone 用**单一** `submenu` 状态复刻。

⑧ 群众对话框逐字：
   role="dialog" aria-label={D("canvas:directorAddCrowdArray")}
   className="nodrag nopan nowheel fixed z-[1800] w-[220px] rounded-xl border
              border-white/10 bg-[rgba(31,31,31,0.98)] p-3 text-white
              shadow-[0_8px_24px_rgba(0,0,0,0.35)] backdrop-blur-xl"
   ⟹ ⟹ ★ z 是 **1800**（clone 此前写死 160）、底色是 **rgba(31,31,31,0.98)**
   （clone 此前自造 #242424）、阴影是 **0_8px_24px_rgba(0,0,0,0.35)**
   （clone 此前自造 0_16px_40px_rgba(0,0,0,0.5)）。
```

★ ★★ **本批最值钱的一条（差点判反）**：源站的对话框高是 **204**、clone 面板化后
实测 **203** ⟹ ⟹ 差 **1px**。**归因过程**（同口径逐段实测，见
`raw/source-858-panel.json` 的 `⑤群众对话框` 与 `raw/clone-858-panel.json` 的
`⑤clone对话框逐段`）：

| 段 | 源站 | clone（补偿前） |
| --- | --- | --- |
| 标题行 | y=401 h=**20** | y=401 h=**20** ✔ |
| 网格 | y=433 h=**106** | y=433 h=**105** ✘ |
| 页脚 | y=551 h=**28** | y=550 h=**28** ✔ |
| label 文字行盒 | **17.05px**（line-height 1.55×11） | **16.5px**（1.5×11） ✘ |

⟹ ⟹ **根因不是漏抄了哪个类名**，而是 **clone 的全局 `line-height` 是 1.5、
源站是 1.55**（都是**无单位** ⟹ ⟹ 随字号缩放 ⟹ ⟹ 11px 文字差 0.55px
⟹ ⟹ 两行累进成 1px）。⟹ ⟹ 修法：给对话框里那三枚 11px 的 label 加
**与源站同构**的 `leading-[1.55]`（源站靠全局、clone 局部补偿）。
⟹ ⟹ 修完：**网格 106、对话框 204**，与源站**逐段逐字一致**。

★ ★ 同理，源站的字体栈是
`-apple-system, "system-ui", "PingFang SC", Inter, "Noto Sans SC", "Microsoft YaHei", …`
而 clone 是 `-apple-system, "system-ui", "Segoe UI", "Helvetica Neue", …`
⟹ ⟹ **缺 `PingFang SC` / `Noto Sans SC`** ⟹ ⟹ 这是**全局排版基线**差异，
本批**只登记不修**（改全局会影响整个应用、4317 又是多人共用）⟹ ⟹ 见 §8 的 D6。

## 2. 源站实测（`probes/source858_panel.py` ⟹ `raw/source-858-panel.json`）

★ 只读探针（**不点「添加」**⟹ ⟹ 无副作用）。

| 读数 | 值 |
| --- | --- |
| 面板 | @(48,52) **232** 宽，`flex w-[232px] min-w-0 flex-col bg-[#171717]` |
| 标题条 | @(48,52) 232×**48**，class 逐字同 `aO`，文本「添加角色」 |
| 11 行 | y=100,132,…,356,**388**(群众),420(几何)；每行 x=**56** 216×**32**、13px |
| 「群众 (3x3)」 | @(56,388) 216×32，`aria-haspopup="dialog"`、`aria-expanded=false` |
| 「几何模型」就地展开 | @(68,**452**) **204×256**；8 项各 @(73,y) **199×32** |
| 场景树 | **不在场**（`sceneTreePresent=false`）⟹ ⟹ ★ 模式互斥被**实测**确认 |
| 群众对话框 | @(280,388) **220×204**、z **1800**、bg `rgba(31,31,31,0.98)`、阴影 `0_8px_24px_rgba(0,0,0,0.35)` |
| 对话框内部 | 标题行 (401,20)／网格 (433,106)／页脚 (551,28)；label 行高 17.05px、input 28px |
| 开几何时 crowd 对话框 | **关闭**（`L` 共用状态的实测） |

★ 顺带**复核**了 batch 590 当时对源站的读数：几何子菜单 **204 宽、每项 199 宽**
⟹ ⟹ 与源站 chunk 的 `ml-3 border-l pl-1` **完全吻合**（列表内容 216 − ml-3 的 12 ＝ **204**；
204 − 1(border) − 4(pl-1) ＝ **199**）⟹ ⟹ ★ **batch 590 当时量到的 (68,452) 204×256
本来就是「就地展开」的坐标** ⟹ ⟹ 它被解读成「浮层」是**解读错了**，数字没错。

## 3. clone 整改（3 个源文件）

### 3.1 新建 `src/components/director/DirectorCharacterPanel.tsx`

源站式「添加角色」**面板**：

- 面板容器 `flex h-full min-h-0 w-full flex-col bg-[#171717]`；
- 标题条逐字 `aO`（`h-12 shrink-0 … text-white/90` ＋ 内层 `span.truncate`）；
- 列表 `min-h-0 flex-1 overflow-y-auto px-2 pb-3`（＋ 源站那两个滚动条任意值走 inline style）；
- 11 行逐字 `eu`（＋ `disabled:*` 两段源站也有）；
- 行图标按源站：`本地上传`＝Upload、8 个体型与「群众」＝人物图标、几何行＝盒子图标；
  ★ 源站的 **6 个几何体共用同一个 `layers` 图标**（「添加空对象」用 `Add`）
  ⟹ ⟹ clone 此前给 6 个几何体**各配了不同图标** ⟹ ⟹ 本批**照抄源站**（都用 `Layers`）；
- ★ crowd 与 geometry **共用一个 `submenu` 状态**（源站的 `L`）⟹ ⟹ 开一个关另一个；
- 「群众 (3x3)」行带 `aria-haspopup="dialog"` ＋ `aria-expanded` ＋ 展开态 `bg-white/8`；
- 「几何模型」**就地展开**（`border-white/8 ml-3 border-l pl-1`）；
- crowd 对话框逐字改成源站样式（z **1800**、bg `rgba(31,31,31,0.98)`、阴影
  `0_8px_24px_rgba(0,0,0,0.35)`、标题 `text-[13px] font-medium text-white/90`、
  计数 `text-[11px] text-white/45`、label `text-[11px] text-white/55`、
  input `h-7 min-w-0 … bg-white/[0.06] px-2 text-[12px] text-white`、
  ★ 间距那一格 `col-span-2`（**在 grid 里**，clone 此前另起一块））。

### 3.2 `src/components/director/DirectorIconRail.tsx` —— 删掉浮层

★ 删掉「添加角色」浮层的**全部**东西：菜单表、几何子菜单表、crowd 对话框、
上传 input、ack 气泡 ＋ 它们的状态／ref／effect／handler（**−19751 字符**）。
⟹ ⟹ rail 只剩「全景图」「画幅比例」两个浮层（这两枚**也是**源站面板模式，
见 §8 的 D9）。

★ 另外把 **rail 的选中态改成派生**：源站逐字 `aria-pressed={z===r.id}`
⟹ ⟹ 选中态由**左侧面板模式**（新 prop `panelView`）派生 ⟹ ⟹ 删掉本地那份
`active` 状态（两处真相 ⟹ ⟹ 点「添加角色」时按钮不亮）。

★ ★ **差点做成一个功能缺口**：点「全景图」时，源站逐字会**改写面板模式**
（`F(r.id)`）⟹ ⟹ 「添加角色」面板必须**让位**；clone 的浮层实现不会改面板模式
⟹ ⟹ 于是两个面板会**同时**留在左侧。⟹ ⟹ 处置：`select()` 里点全景图/画幅比例时
先 `onOpenCharacterPanel?.(false)` ＋ `onOpenCameraPresets?.(false)`。

### 3.3 `src/components/director/DirectorDesk.tsx` —— 左侧资源栏变成多视图

- `leftPanelView` 的取值改成**与源站一一对应**：`"scene" | "character" | "camera" |
  "panorama" | "aspect"`（原 `"tree" | "camera-presets"`）；
- 左侧 aside 改成**模式互斥**渲染：`camera` ⟹ 机位预设面板、`character` ⟹
  「添加角色」面板、其余 ⟹ 场景树 ⟹ ⟹ ★ **场景树与「添加角色」永远不同时出现**；
- ★ `DirectorCharacterPanel` **必须常驻挂载**（哪怕 `active=false`）：移动端视口
  工具条那枚 crowd 入口靠 `director:open-crowd-dialog` 事件把按钮矩形递进来
  ⟹ ⟹ 监听器在面板里 ⟹ ⟹ 面板被卸载 ⟹ ⟹ 移动端那枚就成了「点了没反应」的死按钮
  ⟹ ⟹ 所以用 `key={leftPanelView}`：常驻、但**切模式时重挂载** ⟹ ⟹ 面板内部的
  子菜单状态随之清零（与源站逐字一致：源站切 `z` 时会 `O(null)`）；
- aside 加 `data-director-left-panel-view`（模式感知的稳定选择器）；
  `aria-label` 随模式走（场景树时仍是「场景对象」⟹ ⟹ 老门禁 35/36/50/536 照旧）。

## 4. ★ 差点判反的两处

★ **其一：以为「源站的 crowd / geometry 是两个独立布尔量」** ⟹ ⟹ 于是给 clone 写了
两个独立状态。⟹ ⟹ 源站逐字是**一个** `L`（`"crowd"===L` 与 `"geometry"===L`）
⟹ ⟹ 开一个必须关另一个。⟹ ⟹ 本批用单一 `submenu` 复刻 ⟹ ⟹ 门禁有
`crowd:geometry-closed-because-source-shares-one-state` 钉住。

★ **其二：以为 1px 的差是「漏抄了某个类名」** ⟹ ⟹ 差点去改对话框的 padding。
⟹ ⟹ 逐段实测才发现是**全局 line-height 1.5 vs 源站 1.55**（无单位 ⟹ 随字号缩放）
⟹ ⟹ 只在对话框那三枚 11px 的 label 上做**局部补偿**（`leading-[1.55]`）
⟹ ⟹ **不动全局**（全局改动会影响整个应用、4317 又是多人共用）⟹ ⟹ D6 只登记。

## 5. 判据（`scripts/verify-liblib-batch858.py`，**38/38**）

| 组 | 判据 |
| --- | --- |
| 静态（7） | 面板容器类名／标题条 `aO`／行 `eu`／几何就地展开类名／对话框 `z-[1800]`＋`w-[220px]`／rail 不再拥有 character 浮层／Desk 按模式切面板 |
| 类名可用性（1） | ★ 本批引入的 17 个 Tailwind 类名**必须真的在构建产物 CSS 里**（4317 的扫描是冻结的 ⟹ ⟹ 新类名可能**静默无样式**）⟹ ⟹ 用 `scripts/check-tailwind-classes-in-css.py` 实测（**注意**：类名在 CSS 里是**转义**的，`.text-white\/88` ⟹ ⟹ 朴素子串搜索会**误报 MISS**） |
| 初始态（2） | 左侧面板模式 ＝ scene、场景树在场、rail「场景」pressed |
| 面板（9） | 打开／宽 232 @x=48／标题条 h-48 12px ＋ 截断 span／**场景树不在场**／rail「添加角色」pressed／11 行顺序逐字／行几何 32px 13px @x=56 宽 216／行 y 逐字等于源站实测／crowd 行 `aria-haspopup=dialog`／子菜单行有箭头 |
| 几何（3） | 就地展开 @(68,452) 204×256／**在面板内、不是 portal**／8 项 199×32 |
| crowd（9） | 对话框 @(280,388) 220×204／z 1800 ＋ bg 逐字／**内部三段**逐字／label 行高 17.05px ＋ input 28px／开 crowd ⟹ 几何关闭（共用状态）／计数「共9人」／三个输入量程逐字／间距 1.55→**1.6**／再点一次关／点外面关 |
| 切换（3） | 切回「场景」⟹ 面板关闭、树回来、rail 场景 pressed／点「全景图」⟹ 面板**让位** |
| 移动端（1） | 移动端那枚仍能打开同一个对话框（宽度 220） |

★ 期望值**全部来自源站实测或源站逐字**，没有一个是 clone 自己算的
（期望值表就写在门禁文件头的 `SOURCE` 里，附出处）。

## 6. 阴性对照（`probes/neg858.py`）

★ 7 条变异，每条都**先断言文件真的被改了**（SHA-256）⟹ ⟹ 跑完整门禁 ⟹ ⟹
记录**红了哪几条** ⟹ ⟹ **字节级复原** ⟹ ⟹ 收尾再复核全部文件 == 基线。

| 变异 | 期望翻红的判据 |
| --- | --- |
| N1 面板与场景树不再互斥 | `panel:scene-tree-is-gone-mutually-exclusive` |
| N2 行高 `h-8`→`h-10` | 行几何 + 行 y ＋ crowd 按钮矩形 |
| N3 去掉 `leading-[1.55]` 补偿 | 对话框矩形 + 内部三段 |
| N4 crowd 行去掉 `aria-haspopup` | `panel:crowd-row-has-aria-haspopup-dialog` |
| N5 几何改成绝对定位浮层 | 几何矩形 + 「在面板内不是 portal」 |
| N6 rail 选中态与面板模式脱钩 | `panel:rail-add-character-is-pressed` |
| N7 几何与 crowd 不再互斥 | 几何矩形 + 8 项 |

★ ★ N7 的归因关键字**是跑完第一次变异、读首条红灯原文之后才定的**
（第一版按「我以为的落点」写成「crowd 关掉了几何」那条 ⟹ ⟹ 实际首条红灯落在
「几何就地展开」⟹ ⟹ 报告「未命中」⟹ ⟹ 读原文后改正）。

## 6.5 ★ 受控对照（`probes/attrib858.py` ＋ `probes/attrib858_mix.py`）

★ 目的：**证明门禁不是空转的**（有牙），并且「老的红不是本批引入的」。

### 6.5.1 三种态

| 态 | 源码 | 用途 |
| --- | --- | --- |
| `HEAD-1`／`HEAD-2` | **三个文件全换回 HEAD** | 门禁在旧源码上是否翻红 |
| `WORK-1`／`WORK-2` | 本批工作副本 | 门禁在本批源码上是否全绿 ＋ **两遍读数一致**（无抖动） |
| `MIX` | **只把 `DirectorIconRail.tsx` ＋ `DirectorDesk.tsx` 换回 HEAD**，**保留本批新建的 `DirectorCharacterPanel.tsx`** | ★ **逼出判据层的牙**（见 6.5.2） |

★ 状态顺序刻意是 **HEAD → WORK** ⟹ ⟹ 跑完留在磁盘上的门禁产物
（`runtime-audit.json`／截图）就是 **WORK 态**读出来的，不是 HEAD 态的。

### 6.5.2 ★ 为什么必须有 MIX 态（第一版 attrib 的盲区）

全回退态下 `DirectorCharacterPanel.tsx`（本批新建）在 HEAD 里**不存在** ⟹ ⟹
门禁 **45／857／738** 在**读源文件那一步**就 `FileNotFoundError` 崩掉
⟹ ⟹ **根本没走到浏览器层的判据**。

⟹ ⟹ 那只证明「门禁依赖本批的新源码」，**没证明「迁移后的判据本身有牙」**。

★ MIX 态保留新文件 ⟹ ⟹ 门禁能读得到源文件 ⟹ ⟹ 会一路走到浏览器层 ⟹ ⟹
**判据本身**必须翻红。

### 6.5.3 读数（`controlled-comparison.json` ＋ `raw/attrib/<态>/<门禁>.txt`）

| 门禁 | HEAD 全回退 | **MIX 半回退** | WORK | MIX 态红条原文 |
| --- | --- | --- | --- | --- |
| `858.py`（新） | 红（崩在读文件） | ★ **红 21 条** | 绿 | `source:rail-no-longer-owns-a-character-flyout`、`panel:opens`、`panel:width-232-at-x-48`、`crowd:dialog-is-at-the-source-measured-rect` …（3 条源码静态 ＋ 18 条运行时几何/行为） |
| `536.py` | 红 | 红 | 绿 | `panel:opens` |
| `589.py` | 红 | 红 | 绿 | `character:opens` |
| `613.py` | 红 | 红 | 绿 | `flyout:opens` |
| `625.py` | 红 | 红 | 绿 | `add-character-is-a-side-panel-not-a-portal-flyout`、`geometry-submenu-expands-in-place-not-in-a-portal` |
| `45.py` | 红（崩在读文件） | 红（**超时**，非具名判据） | 绿 | `TimeoutError: waiting for locator("[data-director-character-panel]")` |
| `738.py` | 红（崩在读文件） | 红 | 绿 | `C1 群众弹窗 portal + z-1800`、`C5 几何子菜单就地展开`、`C7 根外 button` …（4 条） |
| `857.py` | 红（崩在读文件） | ★ **绿** | 绿 | （无）⟹ ⟹ 见 **D10** |

★ 判据：两遍读数一致（**稳定 = True**）｜新门禁有牙（**True**）｜复原自检（**True**，SHA-256 逐字节核对）。

### 6.5.4 ★ 两条结论（都是本批查出来的真东西）

**① 「红了」≠「判据红了」。**
`857.py` 在 HEAD 全回退态是红的，但那红来自 `FileNotFoundError`（读不到文件）
⟹ ⟹ **假牙**；MIX 态下它 **12/12 全绿**。
⟹ ⟹ 只有「**具名判据**翻红」才叫有牙；「崩了」只能证明「依赖这份源码」。

**② `857.py` 是「归档型门禁」⟹ ⟹ 结构上没有运行时牙（D10）。**
它的 S2–S10 读的**全是 batch 857 当时录下的 JSON 产物**
（`raw/source-857-*.json`／`raw/clone-857-crowd.json`）⟹ ⟹ **不是实时 DOM**
⟹ ⟹ 把源码换回去它照样绿；它的静态源码断言只覆盖
`DirectorViewport.tsx`／`DirectorCharacterPanel.tsx`／`directorStore.ts`
⟹ ⟹ **压根不覆盖 rail/desk 的结构**。
⟹ ⟹ 这是**职责边界**、不是漏洞：crowd 对话框契约归 857，
「面板 vs 浮层」这个结构归 **live DOM 门禁**（858 等）。
⟹ ⟹ 已在 `scripts/verify-liblib-batch857.py` 的文件头**写明**这一点。

## 7. 迁移的老门禁（**11 条**）

| 门禁 | 撞上的「旧前提」 | 本批怎么改的 |
| --- | --- | --- |
| `45.py` | crowd 段的**静态契约**在 rail 源码里 | 对话框搬到了新组件 ⟹ ⟹ 静态契约跟着搬（**断言内容一字未改**） |
| `536.py` | 「添加机位**不**抢 rail 选中态、**不**开面板」（batch 540 的旧读数，832 已推翻） | 改成源站逐字：点「添加机位」⟹ **它**pressed、场景不pressed、**场景树被替换**；并补「添加角色」面板**替换**场景树 + 切回时树回来 |
| `541.py` | 「点『群众 (3x3)』**直接**加人群」（batch 590 的旧前提） | 改成源站流程：点 ⟹ **对话框开** ⟹ ⟹ 填 ⟹ ⟹ 点「添加」⟹ ⟹ 对象数增加 ＋ ack；并补「面板**不**关」（源站逐字） |
| `589.py` | 标题条自己带 `truncate` | 源站逐字是**内层 span** 带 `truncate` ⟹ ⟹ 断言跟着改成「标题条里有 `span.truncate`」 |
| `613.py` | 切到别的 rail 条目 ⟹ 关掉上一个浮层 | ★ 本批**发现并修掉**一个真问题：切到全景图时「添加角色」面板**不让位** ⟹ ⟹ 改成源站逐字（切模式 ⟹ 面板关闭） |
| `619.py` | 「添加角色浮层」必须遮住 ≥1 枚控件 | 它现在是**侧栏**⟹ ⟹ **不遮**任何控件 ⟹ ⟹ 改成「面板不遮任何控件」 |
| `625.py` | 五个 rail 浮层（含 character 浮层 ＋ 几何子菜单）都要 portal | 两者**不再是浮层** ⟹ ⟹ 从清单移除 ⟹ ⟹ 补**结构性**断言：面板必须**留在 aside 里**、几何必须**留在面板里**（不是 body 级 portal） |
| `626.py` | 浮层必须整体装进视口；几何子菜单要钳制 | 两者都不是浮层 ⟹ ⟹ 移除 ⟹ ⟹ 补**面板口径**的判据：面板在视口内、列表**可滚动**、几何项**滚得到**（或明确是**被时间线盖住**——源站逐字 aside z-30 < timeline z-40） |
| `648.py` | 626 点名的「视口群众面板」`[data-director-crowd-panel]`（batch 857 已删） | 打开路径已不存在 ⟹ ⟹ 改成**现在**的路径（rail → 群众 → 对话框，两步） |
| `738.py` | 对话框 `z-160`；几何子菜单 `z-50`/absolute/fixed portal；**根外 button 轨迹写死 47→52→55** | z 改 **1800**（源站逐字）；几何改成**就地展开**（z auto / static / **在根内**）；★ 写死的个数轨迹改成**结构性**断言（几何 **+0**、对话框 **+5**） |
| `857.py` | 间距 1 位小数的代码在 rail 源码里 | 代码搬到了新组件 ⟹ ⟹ 静态契约跟着搬（**判据内容一字未改**） |

★ 「写死的个数」那条（738 的 C7）正是**老门禁「旧前提」的通用形状**：
它编码的是「浮层在根外 ＋ 对话框在根外 ＋ 几何在根外」这个**旧前提** ⟹ ⟹
改成断言「**谁**在根外」，而不是「根外恰好几枚」。

### 7.1 ★ 回归里冒出一条新红的定点归因（`626.py`）

★ 回归 94 条 ⟹ ⟹ 红 13 条 ⟹ ⟹ 其中 **12 条是已知旧账**
（`831`／`835`／`741`／`91`／`736`／`748`／`749`／`782`／`546`／`542`／`656`／`648`），
但 `626.py` 有一条**不在旧账里**：
`side-panel-unhittable-row-is-the-timeline/1280x540/add-character-panel`。

★ 这条判据是**本批迁移时新增的**（原来量「浮层」、现在量「左侧面板」）
⟹ ⟹ 所以它是**新判据第一次亮红**，**不是**老判据回归
⟹ ⟹ 必须查清「clone 真缺陷」还是「判据写错了」。

**① 定点复跑 ⟹ ⟹ 它就绿了** ⟹ ⟹ 指向**时序抖动**，不是结构缺陷。

**② 但「复跑就绿」本身不足以结案** ⟹ ⟹ 把红条的**细节补全**再跑一遍读原文
（原来只打 `timelineTop=358` ⟹ ⟹ 看不出「是被盖住还是压根不在那儿」），
补全后读到的原文是：

```
timelineTop=358 rowRect=[56, 420, 216, 32] rowFound=True coveredByTimeline=True
timelineRect=[0, 358, 1280, 182] listScrollTop=0 listScrollHeight=440 listClientHeight=440
```

⟹ ⟹ **那一行在 (56,420) 216×32、时间线在 (0,358) 1280×182（z=40）**
⟹ ⟹ 竖直方向**确实重叠** ⟹ ⟹ `coveredByTimeline=True` ✔。

**③ 另写探针（`probes/attrib626.py`）做阳性对照** ⟹ ⟹ 读**那一行中心点上真正是哪个元素**：

| 视口 | 面板 | 列表 | 几何行 | 时间线 | 行中心命中的元素 | 点击 |
| --- | --- | --- | --- | --- | --- | --- |
| 1440×900 | (48,52) 232×848 | (48,100) 232×800 | **(56,420) 216×32** | (0,718) 182 | 该行自己的 `span` | 成功 |
| 1280×720 | (48,52) 232×668 | (48,100) 232×620 | **(56,420) 216×32** | (0,538) 182 | 该行自己的 `span` | 成功 |
| **1280×540** | (48,52) 232×488 | (48,100) 232×440 | **(56,420) 216×32** | **(0,358) 182 z=40** | ★ **时间线的 object row**（`data-director-timeline-object-row=…`） | ★ 失败（被截走） |

⟹ ⟹ **坐实**：1280×540 那一行点不到，是因为**时间线盖在上面**
（层序是**源站逐字**的：aside `z-30` < timeline `z-40`）⟹ ⟹ **源站同款**，不是本批的缺陷。

★ 那为什么回归那一轮会报 `coveredByTimeline=False`？⟹ ⟹ **面板刚打开时那一行可能还没挂上 DOM**
⟹ ⟹ 读到的 `rowRect` 是 `null` ⟹ ⟹ `coveredByTimeline` 恒 `False`
⟹ ⟹ **把时序抖动报成了「没被盖住」**。

**④ 修法（两条，都在 `626.py` 里）**：
① 判据**对时序鲁棒**：点之前 `wait_for(state="attached")`，
   读几何之前**再等一次**（那一行可能是在点击超时的 10 秒里才渲染出来的）；
② **红条细节要自足**：把「那一行矩形／有没有挂上／列表滚动状态／时间线矩形」
   一起打出来 ⟹ ⟹ 否则下一个 agent 还得另写探针反推（★ 本批就是这么干的，
   见 `probes/attrib626.py`）。

★ 修完连跑两遍 ⟹ ⟹ **两遍都只剩 D7 那条旧账**
（`live-controls-reachable/1280x720/crowd-dialog` ⟹ ⟹ 源站逐字 `z-[1900]` 的
引导气泡比对话框 `z-[1800]` 高 ⟹ ⟹ 短视口盖住「间距」输入框 ⟹ ⟹ **源站同款**）。

## 8. ★ 登记的差异（如实登记，不假装已对齐）

| 编号 | 内容 | 处置 |
| --- | --- | --- |
| **D1** | clone 的「添加角色」是浮层、源站是左侧面板模式 | ★ **已在本批结案**（面板化，源站逐字 ＋ 实测逐字命中） |
| **D2** | clone 的对话框高 208、源站 204 | ★ **已结案**（本批 204；根因归到全局 line-height，已局部补偿） |
| **D3** | clone 的对话框落点 left ＝ 281、源站 280 | ★ **已结案**（本批 280） |
| **D4** | clone 把 crowd 成员**自动包成一个组**、源站**不建组** | **只登记不删**（影响 7 个文件；857 登记） |
| **D5** | clone 的**移动端专用** crowd 入口 | clone 自己的扩展（源站无移动端布局）⟹ ⟹ 如实登记 |
| **D6** | clone 的**全局排版基线**与源站不同：字体栈缺 `PingFang SC` / `Noto Sans SC`、`line-height` 1.5 vs 源站 1.55 | **只登记不修**（改全局影响整个应用、4317 多人共用）；本批只在对话框那一处做**局部补偿** |
| **D7** | 时间线引导气泡（源站逐字 `z-[1900]`）比 crowd 对话框（`z-[1800]`）**高** ⟹ ⟹ 短视口下它会盖住对话框的「间距」输入框 | **源站同款**（两个 z 都是源站逐字）⟹ ⟹ **只登记**；它正是 626 在 1280×720 那条红的根因 |
| **D8** | ★ **源站的「全景图」「选择画幅比例」也是左侧面板模式**（不是浮层）⟹ ⟹ clone 的这两个浮层同样是「解读错了」 | **batch 859 整改**；证据见 §9 |
| **D9** | clone 的「添加角色」8 个体型预设**只是占位提示**（不生成 3D 模型） | 854 登记的旧账，未结 |
| **D10** | `857.py` 是**归档型门禁**（S2–S10 读 batch 857 录下的 JSON 产物，不是实时 DOM）⟹ ⟹ **结构上没有运行时牙** | 受控对照 MIX 态实测 12/12 全绿（见 §6.5.4）；已在该脚本文件头写明；运行时牙由 858 等 live DOM 门禁提供 |

★ **不声称**：源站与 clone 的**画面**逐像素一致（本批对齐的是**机制与可观测读数**）。

## 9. ★ D8 的证据：源站的 panorama / aspect 也是面板模式

★ 这是本批**顺手挖出来**的下一处「糊弄」⟹ ⟹ 证据是硬的：

① 源站 chunk 逐字：左侧那个 232 面板里**还有** `"panorama"===z?(…)` 与
`"aspect"===z?(…)` ⟹ ⟹ **五个模式**都在同一个面板容器里。
② 源站 nav 逐字：`onClick: () => { F(r.id), … }` ⟹ ⟹ 点每一枚条目都**改写面板模式**。
③ 源站**根本没有**全景图/画幅比例的 portal（唯一的 portal 是 crowd 对话框）。
④ ★ **batch 589/590 当时对源站的实测读数本身就已经是面板坐标**：
   全景图 232 宽 @(48,100)（48 ＝ rail 之后、100 ＝ 标题条之下 ⟹ ⟹ **不是**
   「rail 按钮 right+8、top ＝ 按钮 top」那个浮层公式）；几何 204 宽 @(68,452)
   （68 ＝ 56 + ml-3 ⟹ ⟹ **就地展开**）⟹ ⟹ ★ **数字没错、解读错了**。
⟹ ⟹ ⇒ **batch 859 的靶子**：把这两个也改成面板模式 ⟹ ⟹ 顺带把「全景图卡片有
圆角底板、标题在卡片外」这种 clone 自造的观感一并去掉（源站是**纯行**、无卡片）。

## 10. ★ 用户可达（用户硬要求：**从根可达 ＋ 写清怎么测**）

根地址：**`http://localhost:4317/`**（**无参数**）。

### 10.1 桌面端（1440×900）：从根走到「添加角色」面板

1. 打开 `http://localhost:4317/`；
2. 在画布上找到标题为「**第一集：咖啡馆对峙**」的那张 **导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）；
3. **鼠标悬停**在它上面 ⟹ 卡片里出现「**打开导演台 →**」按钮（按钮默认透明，
   悬停才显形，与源站一致）；
4. 点它 ⟹ **导演台**盖在画布上 ⟹ 等约 **6.5 秒**；
5. 点左侧窄图标栏（rail）里的「**添加角色**」（第 2 枚，`[data-director-rail-entry='add-character']`）
   ⟹ ⟹ ★ **左侧资源栏切成一个面板**（标题条「添加角色」＋ 11 行）
   ⟹ ⟹ ★ **场景树消失**（源站逐字：两者互斥）；
6. 点「**群众 (3x3)**」⟹ ⟹ 弹出「添加群众阵列」对话框
   （实测 **220×204 @(280,388)**，落在按钮**右侧**、**贴着按钮顶**）；
7. 改行/列/间距 ⟹ ⟹ 点「**添加**」⟹ ⟹ 3D 场景里多出 `行×列` 个人偶
   （★ 源站**不建组**，clone **建组** ⟹ ⟹ 见 §8 的 D4）；
8. ★ 点 rail 的「**场景**」⟹ ⟹ 面板关闭、**场景树回来**（源站逐字的模式互斥）；
9. 想看几何 ⟹ ⟹ 面板里点「**几何模型**」⟹ ⟹ 8 项**就地展开**在面板里
   （实测 @(68,452) 204×256）。

★ 三个选择器就够自己写探针：
`[data-director-character-panel]`（面板本体）、
`[data-director-character-option='crowd-3x3']`（那一行）、
`[data-director-crowd-dialog]`（对话框）。

### 10.2 移动端（390×844）

★ 源站**没有移动端布局**（实测 390px 下源站渲染的仍是桌面画布）⟹ ⟹ 移动端这枚
入口是 **clone 自己的扩展**。rail 在 <899px 是 `hidden` ⟹ ⟹ 入口在**视口底部
工具条**的「添加群众阵列」按钮（`[data-director-crowd-mobile-trigger]`，桌面不出现）
⟹ ⟹ 它开的是**同一个**对话框（量程／默认值／落点规则与桌面完全同源）。

## 11. 复现步骤

```bash
export PATH="$HOME/.pyenv/versions/node/v24.6.0/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"

# ① 源站实测（★ 只读：不点「添加」⟹ ⟹ 无副作用）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/source858_panel.py

# ② clone 实测（桌面 ＋ 移动端，含与源站的逐字比对）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/clone858_panel.py

# ③ 门禁（38/38）
python3 scripts/verify-liblib-batch858.py

# ④ 阴性（会**改源码**做变异 ⟹ ⟹ 跑完必须确认文件已复原）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/neg858.py

# ⑤ 回归（既有门禁清单）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/regress858.py

# ⑤' ★ 626 那条新红的定点归因（读「那一行中心点上真正是哪个元素」）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/attrib626.py

# ⑥ 受控对照（★ 会把源码换回 HEAD ⟹ ⟹ 跑完确认已复原）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/attrib858.py

# ⑥' 受控对照·MIX 半回退态（★ 保留新面板文件、只回退 rail+desk ⟹ ⟹ 逼出判据层的牙）
python3 docs/research/liblib-canvas-batch858-2026-10-01/probes/attrib858_mix.py

# ⑦ 类名可用性（★ 冻结的 Tailwind 扫描 ⟹ ⟹ 新类名可能静默无样式）
python3 scripts/check-tailwind-classes-in-css.py --list-from <你的类名清单>
```
