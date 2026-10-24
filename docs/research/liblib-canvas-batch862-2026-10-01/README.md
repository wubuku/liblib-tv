# batch 862 —— 取景框上的「构图参考线」开关（源站逐字对齐）

> ★ **一句话结论**：源站的构图参考线（分线）开关**长在机位取景框的右上角**，
> 并且**只在选了具体画幅比例时存在**；clone 此前**只有那条线、没有开关**
> （开关在 clone 自己的视口底部胶囊里）⟹ ⟹ 本批把**源站那枚开关**逐字补上，
> 并把框的描边与三分线颜色改成源站逐字。
>
> ★ **诚实标注**：本批**没有**做「机位级写入」（源站会把比例与参考线写进机位对象）
> 与「取景框像素几何对齐」（源站是全屏 1080 高、clone 的 3D 区只有 810 高）
> ⟹ ⟹ 两件都**如实登记**（D17／D18），不假装已对齐。

---

## 1. 靶子：clone 的取景框缺了源站那枚开关

★ batch 860 把「画幅比例」接到了机位取景框上（源站逐字：`aj` 的 value 是数值比例，
  写进的是 `aspect_ratio` 事件 ⟹ ⟹ 改的是**机位取景框**，不是画布）。
★ 本批回头核对取景框的**全部呈现**，发现两处与源站逐字不同：

| | 源站（逐字 ＋ 实测） | clone（本批之前） |
|---|---|---|
| 构图参考线**开关** | ★ **长在取景框右上角**，32×32，`title="构图参考线"` | ✗ **没有**（开关在 clone 自己的视口底部胶囊，`aria-label="开启九宫格辅助线"`） |
| 框的描边 | `outline-white/18 absolute rounded-xl outline -outline-offset-1`（**outline**，白 18%，内缩 1px，圆角 12px） | `border border-white/75`（**border**，白 75%，直角，无 outline） |
| 三分线颜色 | `bg-(--color-white-alpha-50)`（**白 50%**） | `bg-white/35`（白 35%） |

★ ★ **判据要区分「源站有、clone 没有」与「clone 多出来的」**：
  clone 底部胶囊里那枚按钮是 **clone 自己的扩展**（batch 722 的 clone-only 清单里
  已登记「九宫格」这一枚 ⟹ ⟹ 仓库既有立场是「clone 自己的扩展不擅自删」）
  ⟹ ⟹ 本批**保留**它，同时**补上源站那枚** ⟹ ⟹ 两个入口共享同一个
  `showThirds` 状态 ⟹ ⟹ 不会打架（登记 **D19**）。

---

## 2. 源站取证

### 2.1 源站逐字（chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）

★ **组件 `mP`**（取景框 ＋ 遮罩 ＋ 开关，三者同一个组件）：

```js
function mP({aspectRatio:e,leftPanelWidth:t=281,rightPanelWidth:r=281,
             showCompositionGrid:n=!1,onToggleCompositionGrid:a}){
  ...
  if(!e) return void p(null);          // ★ 没有比例 ⟹ 不画框
  ...
  a?(0,i.jsx)("button",{
      type:"button",
      title:s("canvas:directorAspectFrameOverlay"),
      className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8
        items-center justify-center rounded-lg transition-colors
        ${n?"bg-(--btn-secondary-bg) text-btn-primary"
           :"text-white/50 hover:bg-white/10 hover:text-white/80"}`,
      style:{left:u.left+u.width-40,top:u.top+8},
      onClick:a,
      children:(0,i.jsx)(d.f,{className:"h-4 w-4 shrink-0","aria-hidden":!0})
  }):null
}
```

★ **调用点**（同一份 chunk）：

```js
(0,i.jsx)(mP,{
  aspectRatio:tr, leftPanelWidth:tO, rightPanelWidth:tU,
  showCompositionGrid:ti,
  onToggleCompositionGrid:null!==tr?()=>{
      let e=!ti, t=e1||rL.cameras[0]?.id;
      t&&n4(t,"reference_line",(0,nZ.p)(e),"right_panel");
      to(e)
  }:void 0
})
```

⟹ ⟹ 三条**逐字**结论：

1. 开关**长在取景框右上角**：`left = 框左 + 框宽 − 40`、`top = 框上 + 8`
   （按钮宽 32 ⟹ ⟹ 相对框就是「右边内缩 8px、上边内缩 8px」）；
2. 开关**只在选了具体比例时存在**（`tr===null` ⟹ ⟹ `onToggleCompositionGrid` 是
   `undefined` ⟹ ⟹ 按钮不在场）⟹ ⟹ **与「取景框不在场」是同一个条件**；
3. 切换三分线时，源站会**写进机位**：`n4(cameraId,"reference_line",bool,"right_panel")`
   （选中机位优先，没选中就取第一个机位）⟹ ⟹ 比例也是同样写法
   （`o$` ＝ `tn(e); let t=e1||rL.cameras[0]?.id; t&&n4(t,"aspect_ratio",…)`）
   ⟹ ⟹ **机位级写入本批没做 ⟹ 登记 D17**。

★ **顺带确认了 batch 860 的架构判断是对的**：源站的取景框比例取的是
**组件级单一 state** `tr`（`aspectRatio:tr`），**不是**每个机位各存一份
⟹ ⟹ clone 的全局 `frameAspectRatio` 与源站**同构** ✔。

### 2.2 源站运行时实测

★ 探针：`probes/source862_frame_thirds.py`（读框／按钮／三分线 ＋ 点开关）、
  `probes/source862_frame_thirds_icon.py`（取按钮的 svg 逐字）、
  `probes/source862_frame_thirds_style.py`（计算样式 ＋ **颜色归一化**）。

| 读数 | 值 | 出处 |
|---|---|---|
| 「自适应」时的框 | **不在场** | `raw/source-862-frame-thirds.json` |
| 「自适应」时的开关 | **不在场**（按钮列表为空） | 同上 |
| 16:9 的框 | @(329,185) **1262×710** | 同上 |
| 框上开关 | @(1551,193) **32×32**，`title="构图参考线"` | 同上 |
| 位置公式 | 329 + 1262 − 40 ＝ **1551** ✔；185 + 8 ＝ **193** ✔ | 同上（公式**实测命中**） |
| 开关的 svg | 16×16、`viewBox="0 0 16 16"`、**单 path**、`fill=currentColor` | `raw/source-862-frame-thirds-icon.json` |
| 点开关后的三分线 | **4 条**（`bg-(--color-white-alpha-50)`） | `raw/source-862-frame-thirds.json` |
| 框的描边 | outline **1px**、offset **−1px**、白 **18%**、圆角 **12px** | `raw/source-862-frame-thirds-style.json` |
| 三分线颜色（归一化） | `rgba(255,255,255,0.5)` ×4 | 同上 |
| 开关开启态（归一化） | 前景 `rgb(9,202,245)`、背景 `rgba(255,255,255,0.1)` | 同上 |
| 开关关闭态前景 | `lab(100 … / 0.5)` ⟹ 归一化后白 **50%** | 同上 |

★ ★ **颜色为什么要「归一化」**：源站把颜色写成 CSS 变量类
  （`bg-(--color-white-alpha-50)`／`bg-(--btn-secondary-bg)`／`text-btn-primary`）
  ⟹ ⟹ `getComputedStyle` 读回来是 `lab(...)` **函数值**，而 clone 那边是
  `rgba(...)` ⟹ ⟹ **两边字符串不可能逐字相等** ⟹ ⟹ 必须用 **canvas 画一遍再读像素**
  把两边归一到同一口径（源站侧就是这么做的 ⟹ ⟹ clone 侧也照做 ⟹ 见 §6 方法学②）。

★ **副作用声明**：本批只点「画幅比例」与「取景框上的开关」⟹ ⟹ 都是本地视图态；
  **绝不点**「AI生成」「本地上传」「截图」（真实生成／上传）。

★ **取证截图**（clone 侧三态，`probes/clone862_frame_shots.py`）：
  `images/862clone_frame_toggle_off.png`（框 ＋ 关闭态开关）、
  `images/862clone_frame_toggle_on.png`（框 ＋ 4 条分线 ＋ 变青的开关）、
  `images/862clone_frame_auto.png`（「自适应」⟹ ⟹ 框与开关**都不在场**）。

---

## 3. clone 整改（2 个源文件）

### 3.1 `src/components/director/DirectorViewport.tsx`

★ **新增组件 `DirectorFrameThirdsToggle`**（放在 `AspectFrame` 之前）：

- `data-director-frame-thirds-toggle`、`title="构图参考线"`、`aria-label="构图参考线"`、
  `aria-pressed` 跟随状态；
- 关闭态类名**逐字照抄**源站（那几个类 clone 已在用 ⟹ 4317 的 Tailwind 扫描
  是冻结的，但这些类**已生成**）：
  `nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 items-center
  justify-center rounded-lg transition-colors text-white/50 hover:bg-white/10
  hover:text-white/80`；
- 开启态：源站用 `bg-(--btn-secondary-bg) text-btn-primary` ⟹ ⟹ **clone 全仓 0 命中**
  这两个变量 ⟹ ⟹ 用**源站实测值**兜底（`rgba(255,255,255,0.1)` ＋ `rgb(9,202,245)`）；
- 位置：**源站逐字公式** `left = frameWidth − 40`、`top = 8`
  （源站按钮是遮罩容器的绝对定位子节点 ⟹ ⟹ 换算成「相对框」就是右边内缩 8px）；
- 图标：**源站逐字的 svg**（16×16、单 path、`fill=currentColor`），
  path 字符串与 `raw/source-862-frame-thirds-icon.json` 里的**逐字相等**
  ⟹ ⟹ 门禁直接拿源站原文比对。

★ **`AspectFrame` 的三处改动**：

1. 框的描边：`border border-white/75` ⟹ ⟹ **去掉**，改用**源站逐字的 outline**
   （`1px solid rgba(255,255,255,0.18)` ＋ `outlineOffset: "-1px"` ＋
   `borderRadius: "12px"`，走 inline style ⟹ ⟹ 绕开「任意值类在冻结的 Tailwind
   扫描下不生成」这个坑）；
2. 三分线颜色：`bg-white/35` ⟹ ⟹ `rgba(255,255,255,0.5)`（inline style，同上）；
3. 挂上那枚开关（**与框同生共死** ⟹ ⟹ 「自适应」时框不在场 ⟹ ⟹ 按钮也不在场，
   与源站 `null!==tr` 的条件等价）。

★ **没有动**的：底部胶囊里那枚 clone 自己的「九宫格辅助线」按钮（见 D19）。

### 3.2 `src/components/director/DirectorAspectPanel.tsx`

★ **本批只改注释**（代码那行 `disabled` 绑定是本批补上的源站逐字结构，
  注释是把它**为什么不可达**讲清楚）：

- 源站的「无机位」态**未能实测**（源站机位行只有「隐藏」「锁定」，
  `Delete`／`Backspace` 都删不掉 ⟹ ⟹ 该分支在源站近乎死代码）；
- ★ ★ **clone 侧同样不可达**：删除规划器里有守卫
  （`src/lib/directorDeletePlanner.ts`：`survivingCameras.length === 0`
  ⟹ ⟹ `DIRECTOR_LAST_CAMERA_REQUIRED`「至少需要保留一个机位」），
  **而且**主机位另有一条 `DIRECTOR_PRIMARY_CAMERA_REQUIRED`
  ⟹ ⟹ **clone 永远至少有一个机位** ⟹ ⟹ 那行 `disabled` 绑定**永远不生效**
  ⟹ ⟹ 门禁只能是**源码逐字判据**，不许假装有运行时读数。

★ ★★ **顺手立了一条注释纪律**：**注释里不许抄 clone 自己的 JSX 字面量**
  （★ 负控按字面量替换时，会先命中**注释里**那一份 ⟹ ⟹ 改不到代码
  ⟹ ⟹ 门禁绿是**假绿** ⟹ ⟹ 负控打空 ⟹ ⟹ 本批第一版 N7 就是这么打空的 ⟹ ⟹ 见 §6 方法学①）。

---

## 4. 验收

★ **门禁**：`scripts/verify-liblib-batch862.py` —— **57 判据，0 失败**
  （S1 源码契约 12 条／S2 源站运行时 7 条／S3 clone 运行时 34 条／S4 同口径对照 2 条）。
  门禁里**源站的期望值全部来自入库的源站读数**
  （`raw/source-862-frame-thirds.json`／`…-style.json`／`…-icon.json`），
  **不写死「看起来对」的数字**。

★ **阴性对照**：`probes/neg862.py` —— **7/7 通过**
  （每条变异都独立、都**行数中性**、跑完整门禁、**字节级还原**）：

  | # | 变异 | 首条红灯 |
  |---|---|---|
  | N1 | 位置公式 `−40` 改 `−30` | `source:toggle-uses-the-source-position-formula` |
  | N2 | 开关 `title` 改字 | `source:toggle-is-titled-composition-guides` |
  | N3 | 三分线颜色 0.5 改 0.4 | `source:thirds-use-the-source-colour` |
  | N4 | 框描边 0.18 改 0.28 | `source:frame-uses-outline-not-border` |
  | N5 | 开关 svg path 改一个字符 | `source:toggle-icon-path-matches-the-source-verbatim` |
  | N6 | 三分线恒显示（绕过 `showThirds`） | `clone:thirds-are-off-before-the-click` |
  | N7 | 面板的 `disabled` 绑定去掉 | `source:aspect-panel-keeps-the-source-disabled-contract` |

★ **回归**：`probes/regress862.py` —— 见 §4.1。
★ **受控对照**：`probes/attrib862.py` —— 见 §4.2。

### 4.1 回归

★ 清单 **107 条**（比上一批多 9 条：新增本批 `862`，并把**看取景框与底部胶囊**
  的老门禁 `35`／`645`／`722`／`629`／`815`／`816`／`817` 拉进来
  ⟹ ⟹ **扩大了回归清单**；★ 扩大后新出现的红必须**定点对照归因**）。

★ **第一轮**：红 **18** 条 ⟹ ⟹ 其中 **14 条是上一批的同集合旧账**
  （`831`／`835`／`741`／`91`／`736`／`748`／`749`／`782`／`656`／`648`×2／
  `626` 的 D7／`542`＋`546` 的 fixture 缺失／`738`）
  ⟹ ⟹ **另外 4 条是「扩大清单才第一次看见」的**：`35`／`645`／`722`／`629`。

★ **定点归因**（`probes/attrib862_legacy.py`：把这 4 条在 **HEAD 态**与
  **WORK 态**各跑一遍，比对红条集合）⟹ ⟹ **4 条的红条逐条相同**
  ⟹ ⟹ ★ **全是旧账、本批引入 0 条**，且**复原自检通过**。

★ **`35` 的旧前提**（本批顺手整改）：它原本**直接读**取景框，隐含前提是
  「框默认在场且是 16:9」⟹ ⟹ 而 **batch 860** 按源站实测把**初始取景比例**改成
  「自适应」⟹ ⟹ 源站逐字 `if(!e) return void p(null)` ⟹ ⟹ **刚打开导演台时框不在场**
  ⟹ ⟹ 直接读框必然 30s 超时。⟹ ⟹ 本批**迁移**成**结构性**判据：
  **先选比例，再读框**（测的仍是「框的比例随选择而变」）。
  ★ **迁移必须有阴性**：`probes/neg862_migration35.py` **2/2**
  （M1 还原旧前提 ⟹ ⟹ 必须超时；M2 把比例期望改成 4/3 ⟹ ⟹ 必须断言失败；
  两条都**行数中性**、**字节级还原**）。

★ **最终一轮**（35 迁移之后重跑，`raw/regression.json`）：**106 条，红 17 条** ⟹ ⟹
  · **14 条** ＝ 上一批的**同集合**旧账（`831`／`835`／`741`／`91`／`736`／`748`／
    `749`／`782`／`626` 的 D7／`542`＋`546` 的 fixture 缺失／`738`／`656`／`648`×2）；
  · **3 条** ＝ 扩大清单带来的旧账（`645`／`722`／`629`，已定点归因）；
  · ★ **`35` 迁移后转绿**（rc=0）；
  · ★ 本批门禁 `862`、以及 `860`／`859`／`861`／`590`／`617` **全绿** ⟹ ⟹ **零新红**。

### 4.2 受控对照

★ `probes/attrib862.py`：**四态**（HEAD-1／HEAD-2／WORK-1／WORK-2 ＋ MIX 半回退态）
  ⟹ ⟹ 目的有三：
  ① **新门禁有牙**：源码换回 HEAD ⟹ ⟹ `verify-liblib-batch862.py` 必须**翻红**；
  ② **两遍读数一致**（否则是抖动，不能当因果）；
  ③ **MIX 半回退态**：**只**回退 `DirectorViewport.tsx`、保留 panel 的改动
     ⟹ ⟹ **运行时**那批判据必须红、**静态**那条必须绿 ⟹ ⟹ 证明「隔离干净」。

★ 结果（`controlled-comparison.json`）：

| 判据 | 结果 |
|---|---|
| 两遍读数一致（稳定） | ✔ True |
| **新门禁在 HEAD 态翻红**（有牙） | ✔ True（**38 条具名红条、零 CRASH**） |
| **新门禁在 WORK 态全绿** | ✔ 0 条红 |
| MIX 半回退态的**隔离** | ✔ 运行时红 **22** 条、静态红 **8** 条；而 `source:aspect-panel-keeps-the-source-disabled-contract`（面板那处）在 MIX 里**保持绿** ⟹ ⟹ **隔离干净** |
| 老门禁 860／859 的差分 | ✔ `diffs` ＝ 空（两态都绿 ⟹ ⟹ 本批没改坏它们） |
| 复原自检（SHA-256） | ✔ True |

★ ★ **中途修掉的两个「门禁脚本自己的 bug」**（都是判据错、不是产品错）：
① 第一版受控对照里 HEAD 态的红是 **CRASH（点击超时）** ⟹ ⟹ 因为 HEAD 态
   **没有那枚新开关** ⟹ ⟹ 改成**点之前先计数**（`clone:the-toggle-is-mounted-before-it-is-clicked`）
   ＋ 缺失就**跳过点击** ⟹ ⟹ 于是 HEAD 态给出**具名**红条；
② 改完之后又冒出 **CRASH: IndexError** ⟹ ⟹ 原因是「分线」列表为空时
   `.get("线", [{}])[i]` **越界** ⟹ ⟹ 改成**按长度安全取**。

---

## 5. 差异登记（如实登记，不假装已对齐）

| 编号 | 差异 | 本批处置 |
|---|---|---|
| **D16** | 源站 aspect 七格的 `disabled:!hasCameras`（`hasCameras: rL.cameras.length>0`） | ★ **本批补上了 clone 侧的源码结构**（面板七格都带上 `disabled` 绑定，绑定到 `hasCameras` 的取反）；★ 但**运行时两侧都不可达**（源站机位删不掉、clone 有 `DIRECTOR_LAST_CAMERA_REQUIRED` 守卫）⟹ ⟹ 门禁只能是**源码逐字判据** ⟹ ⟹ 诚实标注，不假装有运行时读数 |
| **D17** | 源站把比例与参考线**写进机位对象**（`n4(cameraId,"aspect_ratio"/"reference_line",…)`，选中机位优先、否则第一个机位） | ✗ **本批未做**（clone 的机位对象还没有这两个字段 ⟹ ⟹ 要动持久化 schema ⟹ ⟹ 属于另一个批次；★ 用户当前**看不到**差别） |
| **D18** | 取景框的**像素几何**不同：源站逐字是「减左右面板宽（281＋281）＋ 上下共 224」，而 clone 是「视口减 padding（40／32／88）」；★ 且源站导演台是**全屏 1080 高**（时间轴是浮层），clone 的 3D 区只有 **810 高** | ✗ **本批未做**（这是**布局级**差异，不是取景框本身的问题）⟹ ⟹ 实测差：16:9 源站 1262×710 vs clone 1227×690；4:3 源站 1141×856 vs clone 920×690 ⟹ ⟹ **竖档差得最多** |
| **D19** | clone 视口底部胶囊里那枚「九宫格辅助线」按钮是 **clone 自己的扩展**（源站的开关在框上，源站底部胶囊里没有这枚） | ★ **保留**（仓库既有立场：clone 自己的扩展不擅自删；它也早已登记在 batch 722 的 clone-only 清单里）＋ ★ **补上源站那枚** ⟹ ⟹ 两个入口共享同一个 `showThirds` |
| **D20** | 源站的框外遮罩是 `bg-black/20 backdrop-blur-md` ＋ CSS mask（框外变暗**并模糊**）；clone 用 `shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`（变暗但**不模糊**） | ✗ **本批未做**（沿用 batch 860 的登记） |

★ **不声称**：源站与 clone 的画面逐像素一致。本批对齐的是**机制与可观测读数**
  （开关的位置公式／尺寸／在场条件／图标／颜色／框的描边与圆角）。

---

## 6. 本批新增的方法学（三条，都是自己踩的）

① **「同名在别处出现」⟹ 静态判据假绿 ⟹ 负控打空**
   ⟹ 本批第一版 N7（把面板的 `disabled` 绑定去掉）**打空了**：源码里那个字面量
   **出现两次**——一次在代码、一次**在我自己写的注释里** ⟹ ⟹ 负控的
   `replace(..., 1)` 改的是**注释里**那次 ⟹ ⟹ 代码没变 ⟹ ⟹ 门禁绿是**对的**
   （判据读的是剥注释后的代码）⟹ ⟹ 但**变异没生效**。
   ★ **修法两条**：① **注释里不许抄 clone 自己的代码字面量**（本批已在
   `DirectorAspectPanel.tsx` 里立了这条纪律）；② 负控锚点**带缩进定位到代码那一行**
   （`"\n            disabled={!hasCameras}"`）⟹ ⟹ 改完立刻命中预期判据。

② **「两条 raw 必须同口径」⟹ 本批在**判据**里犯了**
   ⟹ clone 的 CSS `rgba(255,255,255,0.5)`（alpha 0..1）与源站的 canvas 像素
   （alpha 0..255）**不是同一口径** ⟹ ⟹ 我第一版判据用 `int()` 取 alpha
   ⟹ ⟹ `0.5` 被截成 **0** ⟹ ⟹ **三条颜色判据假红**（而产品其实是对的）。
   ★ **修法**：**两侧都走 canvas 归一化**（源站侧本来就这么做 ⟹ ⟹ clone 侧照做）
   ⟹ ⟹ 之后比的是**像素**，不是字符串。

③ **绝对像素不可比时，比「相对偏移」这个不变量**
   ⟹ 源站与 clone 的框**像素本来就不同**（D18）⟹ ⟹ 判据不比绝对位置，
   比「**开关相对框的偏移 ＝ (框宽 − 40, 8)**」⟹ ⟹ 这个不变量**跨六档、跨视口
   尺寸都成立** ⟹ ⟹ 六档全部命中。

★ 另附一条**取证纪律**：源站逐字给了位置公式 ⟹ ⟹ 还要**运行时实测验证那个公式**
  （实测 1551／193 ＝ 329＋1262−40／185＋8 ✔）⟹ ⟹ 才敢把它写成判据。

④ **「HEAD 态翻红」要翻成**具名**红条，不是 CRASH**
   ⟹ 受控对照第一版里，源码换回 HEAD 后那枚新开关**根本不存在** ⟹ ⟹ 门禁去点它
   ⟹ ⟹ `click()` 30s 超时 ⟹ ⟹ 门禁报出来的是 **CRASH: TimeoutError**
   ⟹ ⟹ 归因时看不出「是哪条判据不成立」⟹ ⟹ 只知道「红了」。
   ★ **修法**：**点之前先计数**⟹ ⟹ 先出一条具名判据
   （`clone:the-toggle-is-mounted-before-it-is-clicked`）⟹ ⟹ 缺失时**跳过点击**
   ⟹ ⟹ 于是 HEAD 态给出的是**具名**红条（而不是崩溃签名）。
   ★ ★ 通用式：**门禁里凡是要点「本批新增的元素」，都要先断言它在**——
   否则受控对照的红永远是「超时」，而不是「哪条判据不成立」。

---

## 7. 用户可达（怎么点、怎么测）

★ **clone 跑起来**：见 `docs/research/LIBTV_CLONE_REACHABILITY.md` 的 §0
  （`npm run dev` ⟹ 浏览器打开 `http://localhost:4317/`）。

★ **点到那枚新开关的路径**：

1. 打开 `http://localhost:4317/`；
2. hover 画布上的**导演台卡片** ⟹ ⟹ 点「**打开导演台 →**」；
3. 左侧 **rail** 点「**选择画幅比例**」；
4. 点「**16:9**」⟹ ⟹ ★ **机位取景框出现在视口里**（16:9 时是 1227×690）；
5. ★ **取景框的右上角**多了一枚 **32×32 的圆角小按钮**
   （`title="构图参考线"`，关闭态是半透明白 ⟹ ⟹ 悬停变亮）；
6. **点它** ⟹ ⟹ 框内出现**三分线**（2 竖 2 横、白 50%）；
   ★ 按钮变成**青色前景**（源站的 `text-btn-primary`）；
7. **再点** ⟹ ⟹ 三分线消失 ⟹ ⟹ 按钮回到半透明白；
8. 回到第 3 步点「**自适应**」⟹ ⟹ **取景框与那枚按钮一起消失**
   （源站逐字：`null!==tr` 才给 `onToggleCompositionGrid`）。

★ **选择器**（给自动化用）：

- 取景框：`[data-director-aspect-frame]`（带 `data-director-aspect-ratio="16:9"` 等标记）
- 框上那枚开关：`[data-director-frame-thirds-toggle]`
- 三分线：`[data-director-thirds]`（内含 4 条 `span`）
- 面板七格：`[data-director-aspect-option]`（值即档名，如 `16:9`／`自适应`）
- ★ clone 自己的那枚底部按钮也还在：`aria-label="开启九宫格辅助线"`（D19）

★ **自己跑门禁**：

```bash
python3 scripts/verify-liblib-batch862.py      # 期望：57 判据，0 失败
python3 docs/research/liblib-canvas-batch862-2026-10-01/probes/neg862.py   # 期望：7/7
python3 docs/research/liblib-canvas-batch862-2026-10-01/probes/regress862.py
```

---

## 8. 复现步骤（一条链）

1. **契约提取**：源站 chunk 的 `mP` 组件 ＋ 调用点（§2.1，逐字抄在上面的注释里）；
2. **源站实测**：`probes/source862_frame_thirds.py`／`…_icon.py`／`…_style.py`
   ⟹ ⟹ `raw/source-862-frame-thirds*.json`；
3. **clone 实测**：`probes/clone862_frame_thirds.py`（六档 ＋ 点击 ＋ 自适应）
   ⟹ ⟹ `raw/clone-862-frame-thirds.json`；
4. **门禁**：`scripts/verify-liblib-batch862.py`（源站期望值**只从 raw 读**）；
5. **阴性**：`probes/neg862.py`（行数中性 ＋ 字节级还原）；
6. **回归**：`probes/regress862.py`（107 条，扩大了清单）；
7. **受控对照**：`probes/attrib862.py`（四态 ＋ MIX 半回退态）。
