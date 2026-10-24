# batch 859 — 导演台「全景图」「选择画幅比例」**面板化**（源站左侧面板模式）

> 本批整改的是 **batch 858 登记的 D8**。
> ★ 一句话：**源站的「全景图」「选择画幅比例」不是 rail 上的浮层，而是左侧那个
> 232px 面板的第五、第六个模式**；clone 此前把两者做成了 `portal` 浮层 ⟹ ⟹
> 本批改成面板模式，并按源站逐字对齐几何、类名与选中态。

---

## 0. 一句话结论

clone 的导演台左侧资源栏此前只有三个模式（场景树／添加角色／添加机位），
「全景图」「选择画幅比例」是 **rail 上的两个 portal 浮层**；
源站则是**五模式互斥容器**（`scene`／`character`／`camera`／`panorama`／`aspect`）
里的两个模式。

本批把两者改成面板，并做到**逐字命中源站实测**：

| | 源站实测 | clone 实测 |
|---|---|---|
| 全景图面板 | @(48,52) 232×**1028** | 同 |
| 全景图标题条 | 232×48 / **12px** | 同 |
| 全景图容器 | `px-2` @(48,100) 232×96 | 同 |
| 全景图三行 | @(56,100)/(56,132)/(56,164) 各 **216×32**、**13px**/**20px** | 同 |
| 全景图图标 | 14×14 @(64,109) | 同 |
| 画幅网格 | @(48,100) 232×324、列 `104px 104px`、gap **8px**、pad `0px 8px 12px` | 同 |
| 画幅七格 | 各 **104×72**、**12px**、圆角 **12px**、边框 **1px** | 同 |
| 选中／未选描边 | `0.85`／`0.1` | 同 |
| 场景树 | **不在场**（模式互斥） | 同 |

门禁 **48/48** 绿、阴性对照 **9/9** 有效、受控对照四态 ＋ MIX 半回退态全跑完。

---

## 1. 源站逐字依据（源站 chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）

### 1.1 ★ 左侧面板是**五模式互斥容器**（这是 D8 的直接证据）

源站 `aU` 组件（偏移 ≈150398）：

```js
e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col bg-[#171717]",
  children:["scene"===z?n:null,"character"===z?(…),"camera"===z?(…),
            "panorama"===z?(…),"aspect"===z?(…)]})
```

⟹ ⟹ `"panorama"===z` 与 `"aspect"===z` 是**同一个 `div` 的两个子分支**
⟹ ⟹ **它们是面板模式**，不是 rail 浮层。

### 1.2 `"panorama"===z`（偏移 ≈150398）

```js
(0,i.jsxs)("div",{className:"flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90",
  children:D("canvas:directorPanorama")}),
(0,i.jsxs)("div",{className:"px-2",children:[
  // ① 本地上传：u.p.Upload ／ D("canvas:directorLocalUpload")
  // ② 历史记录：u.p.HistoryN ／ D("canvas:directorHistory")
  // ③ AI生成  ：aM.f、aria-hidden:!0、disabled:E ／
  //             E?D("canvas:directorGenerating"):D("canvas:directorAiGenerate")
]})
```

三枚是**行**（行类 `eu`），**不是**卡片。

### 1.3 `"aspect"===z`（偏移 ≈151169）

```js
(0,i.jsxs)("div",{className:"flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90",
  children:D("canvas:directorSelectAspectRatioHint")}),
(0,i.jsxs)("div",{className:"grid grid-cols-2 gap-2 px-2 pb-3",children:aj.map(e=>
  (0,i.jsxs)("button",{className:clsx(
     "hover:bg-white/8 flex h-[72px] flex-col items-center justify-center gap-2 rounded-xl border text-[12px] text-white/90 transition-colors disabled:cursor-not-allowed disabled:opacity-35",
     t?"border-white/85":"border-white/10"),…}))})
```

其中 `t` ＝「这一项是不是当前选中」，判定逐字：

```js
null===e.value||null===l ? e.value===l : .001>Math.abs(e.value-l)
```

### 1.4 ★ 源站的选项表 `aj`（逐字）

```js
[{label:null,value:null},{label:"21:9",value:21/9},{label:"16:9",value:16/9},
 {label:"4:3",value:4/3},{label:"1:1",value:1},{label:"3:4",value:.75},
 {label:"9:16",value:9/16}]
```

⟹ ⟹ 第一项 `label:null` ⟹ ⟹ 文本走 i18n 兜底（源站实测显示「自适应」）。

---

## 2. 源站实测（`probes/source859_panels.py` ⟹ `raw/source-859-panels.json`）

只读探针：登录复用 `/tmp/liblib-cookie.json`，**不点「添加」** ⟹ ⟹ 无副作用。

| 读数 | 值 |
|---|---|
| rail 六枚 | y = 60 / 116 / 156 / 196 / 236 / 276 |
| 全景图面板 | @(48,52) 232×**1028**、类 `flex w-[232px] min-w-0 flex-col bg-[#171717]`、`panelCount=1` |
| 全景图标题条 | @(48,52) 232×48 / **12px**、文本「全景图」 |
| 全景图容器 | `px-2`、padding `0px 8px`、@(48,100) 232×96 |
| 全景图三行 | 本地上传 @(56,100) 216×32／历史记录 @(56,132)／AI生成 @(56,164)，各 **13px**/**20px**、圆角 8px、图标 14×14 @(64,109/141/173) |
| 全景图时 rail | 第 4 枚（y=196）「全景图」`pressed=true` |
| ★ 场景树 | **不在场**（`sceneTreePresent=false`） |
| 画幅面板 | @(48,52) 232×**1028** |
| 画幅标题条 | @(48,52) 232×48 / **12px**、文本「选择画幅比例」 |
| 画幅网格 | @(48,100) 232×**324**、列 `104px 104px`、gap **8px**、padding `0px 8px 12px` |
| 画幅七格 | 自适应 @(56,100)／21:9 @(168,100)／16:9 @(56,180)／4:3 @(168,180)／1:1 @(56,260)／3:4 @(168,260)／9:16 @(56,340)，各 **104×72**、**12px**、圆角 **12px**、边框 **1px** |
| 画幅时 rail | 第 5 枚（y=236）「选择画幅比例」`pressed=true` |
| ★ 场景树 | **不在场** |

★ 源站的 `borderColor` 实测是 `lab(100 -0.0000298023 0.0000119209 / 0.85)`
⟹ ⟹ 判据**不能**假设颜色字符串形态（见 §5.2）。

---

## 3. clone 整改（4 个源文件）

### 3.1 新建 `src/components/director/DirectorPanoramaPanel.tsx`

- 根类 `flex h-full min-h-0 w-full flex-col bg-[#171717]`
  （★ **必须 `h-full`**，否则面板只有内容高 144 而不是占满整列 1028）；
- 标题条逐字 `aO`、容器 `px-2`、三枚逐字 `eu` 行；
- ★ **条件渲染**（`if (!active) return null`）⟹ ⟹ 与源站 `"panorama"===z?(…):null`
  逐字一致，**不是** `hidden` ⟹ ⟹ 「旧浮层选择器 count=0」这类判据继续成立。

### 3.2 新建 `src/components/director/DirectorAspectPanel.tsx`

- 标题条 ＋ 网格 `grid grid-cols-2 gap-2 px-2 pb-3` ＋ 七枚 **104×72** 卡片；
- `ASPECT_GLYPH` 字形表（从 rail 搬来，batch 590 的实测值）；
- 选择状态放在组件内 `useState` ⟹ ⟹ 组件**常驻挂载** ⟹ ⟹ **选中项跨模式保留**。

### 3.3 `src/components/director/DirectorIconRail.tsx`

- 删掉 panorama／aspect 两个 portal 浮层（连同 `FLYOUT_WIDTH`／
  `FLYOUT_CARD_CLASS`／`RAIL_FLYOUT_Z`／`useFlyoutAnchor`／`portalFlyout`／
  `anchors`／`openFlyout`／`aspectRatio` 本地 state）；
  ★ **保留**那段「z 陷阱」的知识注释（但门禁查死代码时必须先剥注释）；
- `isEntryPressed` **五枚全部**由 `panelView` 派生；
- ★ 两个 `open?` 回调**合并成单一 `onSelectLeftPanelView(view)`**
  ⟹ ⟹ 源站逐字 `F(r.id)` ⟹ ⟹ **一次切换**、无「先关后开」的顺序脆弱。

### 3.4 `src/components/director/DirectorDesk.tsx`

- 引入并渲染两个新面板；
- aside 的 `aria-label` 随模式走（添加角色／全景图／选择画幅比例／场景对象）；
- rail 改传 `onSelectLeftPanelView`。

### 3.5 ★ 踩到并修掉的一个真 bug

三个面板最初都写 `key={leftPanelView}` ⟹ ⟹ **兄弟节点 key 重复**
⟹ ⟹ React 错配（面板不可见、格子点不动）⟹ ⟹ 改为**只有「添加角色」面板保留 key**
（新两个不加 key ⟹ ⟹ 比例选中项跨模式保留，也更贴源站：
源站切 `z` 时清掉的是**子菜单**，画幅比例的选中项是画布级状态、不会清）。

---

## 4. ★ 差点判反的一处

★ **「面板撑满整列」不是源站的类名，而是 clone 的布局需要。**
源站左侧那个容器是 `flex w-[232px] min-w-0 flex-col`（**没有 `h-full`**），
因为源站它本身就是 `absolute bottom-0 top-[52px]` 的那一列；
而 clone 的 aside 内部还有一层 ⟹ ⟹ clone 的面板必须自己 `h-full` 才占满。

⟹ ⟹ 若照抄源站类名，clone 的面板会只有内容高（全景图 144／画幅 372）
⟹ ⟹ 与源站实测的 1028 不符。
⇒ **判据取「源站实测的绝对几何」，不取「源站的类串」**——
这正是本批把期望值分两栏（类串逐字 ＋ 几何实测）的原因。

---

## 5. 判据（`scripts/verify-liblib-batch859.py`，**48/48**）

| 段 | 内容 | 条数 |
|---|---|---|
| S1 | 源码契约（静态、**剥注释后**比类串） | 11 |
| S2 | 源站实测产物必须存在且自洽 | 5 |
| S3/S4/S5 | clone 实测（live DOM）逐字比对源站 | 30 |
| S6 | 选中项跨模式保留 | 1 |
| S7 | 类名可用性（冻结的 Tailwind 扫描） | 1 |

### 5.1 ★ 静态判据必须**剥掉注释**再比类串

★ 本批实测：写 M5 变异时发现锚点命中 **2 次**——因为两个新面板的**文件头注释里
逐字抄了源站类串**（`DirectorAspectPanel.tsx` 第 13–16 行把
`h-[72px] flex-col …` 原样写在注释里）。

⟹ ⟹ 若拿**整个文件**去 `in` 一个类串，**注释里的那份拷贝就足以让判据变绿**
⟹ ⟹ 真正被改坏的**代码**反而测不出来。
⇒ 静态契约判据一律只读**代码**（`strip_comments()`）。

★ 这与 batch 858 踩的坑是**同一族**但方向相反：
858 是「注释里的 `portalFlyout` 被当成死代码」⟹ ⟹ 假红；
859 是「注释里的类串被当成契约成立」⟹ ⟹ 假绿。
⇒ **判据读的东西必须与它声称的东西同粒度**。

### 5.2 ★ 颜色字符串的形态**不能假设**

`getComputedStyle().borderColor` 在本机拿到的是
`oklab(0.999994 0.0000455678 0.0000200868 / 0.85)`，
而源站探针拿到的是 `lab(100 -0.0000298023 0.0000119209 / 0.85)`。

⟹ ⟹ 第一版用一条正则 `/\s*([0-9.]+)\)/` 硬啃，**碰巧**匹配上了；
⟹ ⟹ 本批改成 `extract_alpha()`：**三种形态**都认
（斜杠形式／`rgba(r,g,b,a)` 第 4 分量／百分号形式），
**提取不到就返回空串 ⟹ ⟹ 判据红**（而不是默默当成 0 蒙混过去）。

### 5.3 ★ 源文件缺失时**不许崩**

受控对照会把源码换回 HEAD ⟹ ⟹ HEAD 里**没有**本批新建的两个面板文件
⟹ ⟹ 门禁若直接 `read_text` ⟹ ⟹ 会**抛异常**退出
⟹ ⟹ 那条「红」是**崩出来的**、不是判据判出来的 ⟹ ⟹ 属于**假牙**
（★ batch 858 的教训：崩在读文件上的红是假牙）。

⇒ 缺失时把源码当**空串**继续走 ⟹ ⟹ 每条静态判据**各自**报红
⟹ ⟹ 受控对照能看到「哪些判据因为文件没了而红」。

---

## 6. 阴性对照（`probes/neg859.py` ⟹ `negative-audit.json`）

**9/9 条负控有效**，字节级复原自检 True。

| 变异 | 改坏什么 | 期望翻红的判据 | 实际命中 |
|---|---|---|---|
| M1 | 面板去掉 `h-full`（高 1028→144） | `panel:panorama-rect` | ✔ |
| M2 | 行字号 13px→12px | `source:panorama-row-class…` ＋ 三条 `panel:panorama-row-*` | ✔ |
| M3 | 「AI生成」→「AI 生成」 | `panel:panorama-row-AI生成` | ✔ |
| M4 | 网格 gap 8px→0 | `source:aspect-grid-class…` ＋ `panel:aspect-grid` | ✔ |
| M5 | 格子高 72px→64px | `source:aspect-cell-class…` ＋ `panel:aspect-cell-*` | ✔ |
| M6 | 选中描边 0.85→0.1 | `panel:aspect-cell-自适应` | ✔ |
| M7 | rail 选中态与模式脱钩 | `panel:rail-entry-is-pressed` | ✔ |
| M8 | 画幅面板常驻（两模式同时在 DOM） | `panel:only-one-mode-in-dom` | ✔ |
| M9 | 旧浮层属性复活 | `panel:old-flyouts-are-gone` | ✔ |

★ 纪律：每个变异先断言文件**真的被改了**（SHA-256）⟹ ⟹ 不会出现
「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」；
变异**行数中性**；每条变异后**字节级复原**；收尾再复核一遍全部文件 == 基线。

★ **M5 的锚点自检抓到一条真问题**：锚点命中 2 次（代码 ＋ 注释）
⟹ ⟹ 于是把门禁的静态判据改成剥注释后比（§5.1）⟹ ⟹ 顺手把一条**假绿**的口子补上了。

---

## 7. ★ 受控对照（四态 ＋ MIX 半回退态）

### 7.1 状态与读数

- `probes/attrib859.py`：**HEAD-1 → HEAD-2 → WORK-1 → WORK-2**（★ WORK 在最后
  ⟹ ⟹ 磁盘上留下的产物是**本批源码**读出来的）；
- `probes/attrib859_mix.py`：**MIX 半回退态**（紧接其后跑）。

★ MIX 态＝**只**把 `DirectorIconRail.tsx` ＋ `DirectorDesk.tsx` 换回 HEAD
（⟹ ⟹ 回到浮层模型），**保留**本批新建的两个面板文件。

| 判据 | HEAD 全回退 | MIX 半回退 | WORK |
|---|---|---|---|
| 新门禁 859 | **红**（多条） | **红**（判据层） | 绿 |
| 迁移过的老门禁 | 红 | 红 | 绿 |
| 857（归档型门禁，D10） | **绿** | **绿** | 绿 |

★ **为什么 MIX 必须单独一个脚本**：MIX 态必须**紧接在 WORK 态之后**才可比；
若混在同一脚本里且排在最后 ⟹ ⟹ 磁盘上留下的会是 MIX 态的产物 ⟹ ⟹ **不对**。

★ **全回退只证明「门禁依赖新源码」**；MIX 才逼出**判据层**的牙
（两个新面板文件在位 ⟹ ⟹ 静态判据不该全红；rail/desk 不认识它们 ⟹ ⟹ 行为判据必须红）。

---

## 7.5 回归（`probes/regress859.py`）

**96 条，红 14 条 ⟹ 全部是已知旧账、零新红。**

| 门禁 | 红因 | 性质 |
|---|---|---|
| 门禁 831 | S14／S15／S16／S17 | 旧账 |
| 门禁 835 | 判据 6/7 | 旧账 |
| 门禁 741 | 判据 11/13 | 旧账 |
| 门禁 91 | TransformControls 瞬态 | 旧账 |
| 门禁 736 | 判据 6/10 | 旧账 |
| 门禁 748 | 判据 4/7 | 旧账 |
| 门禁 749 | 判据 7/9 | 旧账 |
| 门禁 782 | 不通过 | 旧账 |
| 门禁 626 | **只剩** `live-controls-reachable/1280x720/crowd-dialog`（**D7**） | 旧账（源站同款） |
| 门禁 546／542 | fixture `/private/tmp/batch542-fixture/hero-character.fbx` 缺失 | 旧账 |
| 门禁 738 | 判据 8/9 | 旧账 |
| 门禁 656 | 2 条 | 旧账 |
| 门禁 648 | 2 条 | 旧账 |

★ ★ **626 那条要特别说**：batch 858 时它是**红 13 条**（12 旧账 ＋ 1 条新红），
本批**只剩 D7 那 1 条**（源站逐字 `z-[1900]` 引导气泡盖住 `z-[1800]` 对话框）
⟹ ⟹ **858 修的时序鲁棒性没有退化**。

★ 本批新门禁在回归里 **rc=0（48 判据，0 失败）** ✓

---

## 8. 迁移的老门禁（**8 条**）

| 门禁 | 迁移内容 |
|---|---|
| 门禁 538 | 浮层 → 面板；`count` → **不可见** |
| 门禁 589 | 选择器换面板 ＋ `aspect:single-open` 改成「**五个分支只有一个在 DOM 里**」 |
| 门禁 613 | 选择器换面板 ＋ x=48 的几何前提仍成立 |
| 门禁 617 | `TRANSIENT_OVERLAYS` 选择器换面板 |
| 门禁 619 | 两个状态的 `covers` 改 False |
| 门禁 624 | 选择器换面板 |
| 门禁 625 | `FLOUTS` 移出两条 ＋ `BEFORE` 写死矩形移出 ＋ 新增 `PANEL_CHECK_JS` **结构性断言** |
| 门禁 626 | `OVERLAYS` 移出两条 ＋ 新增 `run_mode_panels()` 与 `MODE_PANEL_JS`（4 视口 × 2 模式） |

★ 迁移原则：**「浮层尺子」对面板不适用** ⟹ ⟹ 迁移成**结构性**断言
（留在 `aside` 里 ＋ 不是 `body` 的直接子元素 ＋ 旧浮层选择器清零）。

---

## 9. ★ 登记的差异（如实登记，不假装已对齐）

### D11（本批新登记，**只登记不修**）

★ clone 的「选择画幅比例」**选中项不改画布宽高比**。

- 源站 `aj` 的 `value` 是**数值比例**（`21/9`、`16/9`…），
  选中后 `d(e.value)` **写进画布状态** ⟹ ⟹ 画布宽高比真的变；
- clone 的 store 里 `aspectRatio` 是**截图/导出**用的三值
  （`"16:9" | "9:16" | "1:1"`）⟹ ⟹ **与画布宽高比不是一回事**；
- ⟹ ⟹ 本批的选择**只改面板里的高亮**（描边 0.85／0.1）。

**为什么不修**：这个缺口牵涉**视口布局实现**（画布尺寸算法），
与「面板化」是**两个独立的缺口**；混在一起改风险大 ⟹ ⟹ 本批只做面板化，
把功能缺口**如实登记**。

★ 另：全景图三行在 clone 里**仍是占位**（点「本地上传」「历史记录」「AI生成」
无动作）⟹ ⟹ 源站这三行各自有真实流程（选文件／拉历史／调生图）⟹ ⟹ 同属另一个缺口。

---

## 10. ★ 用户可达（用户硬要求：**从根可达 ＋ 写清怎么测**）

根地址：**`http://localhost:4317/`**（**无参数**）。

### 10.1 桌面端（1920×1080，实测视口）：从根走到「全景图」面板

1. 打开 `http://localhost:4317/`；
2. 在画布上找到标题为「**第一集：咖啡馆对峙**」的那张 **导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）；
3. **鼠标悬停**在它上面 ⟹ 卡片里出现「**打开导演台 →**」按钮
   （按钮默认透明，悬停才显形，与源站一致）；
4. 点它 ⟹ **导演台**盖在画布上 ⟹ 等约 **6.5 秒**；
5. 点左侧窄图标栏（rail）里的「**全景图**」（第 **4** 枚，y=196，
   `[data-director-rail-entry='panorama']`）
   ⟹ ⟹ ★ **左侧资源栏切成一个面板**（标题条「全景图」＋ 三行）
   ⟹ ⟹ ★ **场景树消失**（源站逐字：两者互斥）；
   ⟹ ⟹ ★ **不再是浮层**（旧的 portal 浮层已删除）；
6. ★ 面板里三行逐字为「**本地上传**」「**历史记录**」「**AI生成**」
   （★ 源站逐字，**「AI生成」中间没有空格**）；
   ⟹ ⟹ 三行在 clone 里**仍是占位**（点了没动作，见 §9）；
7. 点 rail 的「**场景**」（第 1 枚）⟹ ⟹ 面板关闭、**场景树回来**（模式互斥）；
8. 点 rail 的「**选择画幅比例**」（第 **5** 枚，y=236，
   `[data-director-rail-entry='aspect-ratio']`）
   ⟹ ⟹ 面板切成一个 2 列网格、七格逐字为
   「**自适应**」「21:9」「16:9」「4:3」「1:1」「3:4」「9:16」；
9. ★ 点其中一格 ⟹ ⟹ 它的描边从 `0.1` 变 `0.85`（选中态）；
   ⟹ ⟹ ★ **切到别的模式再切回来，选中项还在**（组件常驻挂载）；
10. ★ 想知道「面板是面板、不是浮层」 ⟹ ⟹ 打开 DevTools，
    在 Console 里跑：
    ```js
    document.querySelectorAll('[data-director-panorama-flyout]').length  // 0
    document.querySelectorAll('[data-director-aspect-flyout]').length    // 0
    document.querySelector('[data-director-panorama-panel]').closest('aside') !== null  // true
    ```

★ 三个选择器就够自己写探针：
`[data-director-panorama-panel]`（面板本体）、
`[data-director-panorama-option]`（那三行）、
`[data-director-aspect-panel]` ＋ `[data-director-aspect-option]`（七格）。

### 10.2 移动端（390×844）

★ 源站**没有移动端布局**（实测 390px 下源站渲染的仍是桌面画布）⟹ ⟹ 移动端这枚
入口是 **clone 自己的扩展**。rail 在 <899px 是 `hidden` ⟹ ⟹ 本批两个新面板在
移动端**同样走 rail 的模式切换**（桌面/移动共用同一套 `leftPanelView`）。

---

## 11. 复现步骤

```bash
export PATH="$HOME/.pyenv/versions/node/v24.6.0/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"

# ① 源站实测（★ 只读：不点「添加」⟹ ⟹ 无副作用）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/source859_panels.py

# ② clone 实测（含与源站的逐字比对）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/clone859_panels.py

# ③ 门禁（48/48）
python3 scripts/verify-liblib-batch859.py

# ④ 阴性（会**改源码**做变异 ⟹ ⟹ 跑完必须确认文件已复原）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/neg859.py

# ⑤ 回归（既有门禁清单）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/regress859.py

# ⑥ 受控对照·四态（★ 会把源码换回 HEAD ⟹ ⟹ 跑完确认已复原）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/attrib859.py

# ⑥' 受控对照·MIX 半回退态（★ 保留新面板文件、只回退 rail/desk）
python3 docs/research/liblib-canvas-batch859-2026-10-01/probes/attrib859_mix.py

# ⑦ 类名可用性（★ 冻结的 Tailwind 扫描 ⟹ ⟹ 新类名可能静默无样式）
python3 scripts/check-tailwind-classes-in-css.py --list-from <类名清单>
```

---

## 12. 产物清单

| 文件 | 说明 |
|---|---|
| `probes/source859_panels.py` | 源站只读探针（复用 `/tmp/liblib-cookie.json`） |
| `probes/clone859_panels.py` | clone 同口径探针（期望值表内置） |
| `probes/neg859.py` | 阴性对照（9 条行数中性变异 ＋ 字节级复原） |
| `probes/regress859.py` | 回归（既有门禁清单 ＋ 859） |
| `probes/attrib859.py` | 受控对照四态 |
| `probes/attrib859_mix.py` | 受控对照 MIX 半回退态 |
| `raw/source-859-panels.json` | 源站实测原始读数 |
| `raw/clone-859-panels.json` | clone 实测原始读数 |
| `raw/attrib/<态>/<门禁>.txt` | 受控对照每态每门禁的**完整 stdout+stderr** |
| `negative-audit.json` | 阴性对照结果 |
| `controlled-comparison.json` | 受控对照结果（含 MIX） |
| `runtime-audit.json` | 门禁的 live DOM 读数 |
| `images/859src_*.png` ＋ `images/859clone_*.png` | 源站／clone 截图 |
