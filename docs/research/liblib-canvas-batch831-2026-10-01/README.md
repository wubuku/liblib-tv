# batch 831 — clone 导演台：「帮助 → 快捷键」面板（**实施批次**）＋ ★★ 一条自证式判据的翻车实录

> 批次性质：**实施批次**（有 `src/` 改动 ⟹ 已跑 `npm run build`）
> 日期：2026-10-21
> 门禁：`scripts/verify-liblib-batch831.py` ⟹ **主检查 17/17 ｜ 阴性对照 17/17**
> 源站测试项目：**本批只读，未改动**
> 源站素材：导演台组件 chunk `0fmehki05gkzw.js.js`（1,018,130 字节，batch 830 抓的那一份）

---

## 一、一句话结论

源站导演台 rail 底部的「**帮助**」圆钮点开的是一枚**向上弹的 `role=menu`**
（不是页签），菜单里两枚 menuitem：**快捷键** / **使用教程**；
「快捷键」打开一枚 `role=dialog aria-modal="true"` 的 **480×314** 面板
（**写死的绝对偏移** `left-[297px] top-[60px]`，不是居中），两列各 192px、**12 行**、
键帽上的 ⌘ 与 ⌫ 是 **16×16 的 SVG**。

⟹ 本批把 clone 里那枚**点了没反应**的「帮助」圆钮（batch 830 登记的产品缺口）
按源站的当前形态建了出来，**几何逐字相等**。

⟹ ★★ 但本批真正的收获不在这个面板，而在**一条判据是怎么骗过自己的**：
第一版门禁 S12 的期望值是**我手打**的源站 ⌘ path ⟹ 于是它成了**自证式判据**
⟹ 而我手打时确实**抄错了**（把 path 下半部两条臂的先后顺序抄反了）
⟹ 门禁却照样报 15/15 全绿。详见 §5。

---

## 二、源站形态（2026-10-21 活体实测 + 源码）

### 2.1 「帮助」入口与菜单

| 序 | 对象 | 盒 | 其它读数 |
| --- | --- | --- | --- |
| 序 1 | 「帮助」圆钮 | 32×32 @(8,1040) | `aria-haspopup="menu"`、`aria-expanded`、图标 20px |
| 序 2 | 菜单（`role=menu`） | 120×78 @(8,954) | **向上弹**（`absolute bottom-full left-0 z-50 pb-2`） |
| 序 3 | menuitem「快捷键」 | 110×32 @(13,959) | `role="menuitem"` |
| 序 4 | menuitem「使用教程」 | 110×32 @(13,995) | `role="menuitem"` |

★ **菜单底边 y=954，按钮顶边 y=1040 ⟹ 差 86px**
⟹ 菜单是「按钮正上方 8px」（`bottom-full` + `pb-2`），**不是**贴着按钮。

### 2.2 快捷键对话框

| 序 | 对象 | 盒 | 其它读数 |
| --- | --- | --- | --- |
| 序 1 | 对话框 | 480×314 @(297,60) | `role=dialog`、`aria-modal=true`、`aria-label=快捷键` |
| 序 2 | 标题 h2「快捷键」 | 48×22 @(322,**81**) | 16px / weight 500 |
| 序 3 | 左列 | 192×228 @(322,123) | `justify-between` |
| 序 4 | 右列 | 192×228 @(563,123) | 中间 1px 竖线、左右各 24px |
| 序 5 | 行数 | **12** | 每行 `h-7`（28px） |
| 序 6 | SVG 图标 | **4** 个 16×16 | ⌘×3 ＋ ⌫×1 |

★ 12 行的键帽盒**逐行**（源站原文，单位 px）：

| 序 | 标签 | 标签盒 | 键帽文字 | 键帽盒 |
| --- | --- | --- | --- | --- |
| 序 1 | 俯视视角 | 56×20 @(322,127) | `T` | 28×28 @(486,123) |
| 序 2 | 重置视角 | 56×20 @(322,167) | `H` | 28×28 @(486,163) |
| 序 3 | 移动 | 28×20 @(322,207) | `V` | 28×28 @(486,203) |
| 序 4 | 旋转 | 28×20 @(322,247) | `R` | 28×28 @(486,243) |
| 序 5 | 缩放 | 28×20 @(322,287) | `F` | 28×28 @(486,283) |
| 序 6 | 移动当前视角 | 84×20 @(322,327) | `WASDQE` | 74×28 @(440,323) |
| 序 7 | 正面视角 | 56×20 @(563,127) | `Y` | 28×28 @(726,123) |
| 序 8 | 网格吸附 | 56×20 @(563,167) | `X` | 28×28 @(726,163) |
| 序 9 | 打组 | 28×20 @(563,207) | ⌘＋`G` | 66×28 @(688,203) |
| 序 10 | 解组 | 28×20 @(563,247) | ⌘＋`⇧`＋`D` | 102×28 @(652,243) |
| 序 11 | 撤销 | 28×20 @(563,287) | ⌘＋`Z` | 66×28 @(688,283) |
| 序 12 | 删除 | 28×20 @(563,327) | （⌫ 图标） | 30×28 @(724,323) |

### 2.3 源站代码原文（chunk `0fmehki05gkzw.js.js`）

帮助菜单（偏移 145788 附近）：

```js
("div",{ref:er,className:"relative mt-auto",children:[
  (0,i.jsx)("button",{type:"button","aria-label":D("canvas:directorHelp"),
    "aria-haspopup":"menu","aria-expanded":B,
    className:"text-white/72 hover:bg-white/8 flex size-8 items-center justify-center rounded-lg …"}),
  B?(0,i.jsx)("div",{className:"absolute bottom-full left-0 z-50 pb-2",
    children:(0,i.jsxs)("div",{role:"menu",
      className:"nodrag nopan nowheel flex w-[120px] flex-col gap-1 rounded-xl border border-white/10 bg-[rgba(31,31,31,0.94)] p-1 shadow-[0_8px_24px_rgba(0,0,0,0.35)] backdrop-blur-xl",
      children:[ … menuitem「快捷键」… menuitem「使用教程」… ]})}):null]})
```

对话框挂载（偏移 1009752 附近）：

```js
tN?(0,i.jsx)("div",{className:"absolute inset-0 z-40",onMouseDown:()=>tL(!1),role:"presentation",
  children:(0,i.jsx)("div",{className:"absolute left-[297px] top-[60px]",
    onMouseDown:e=>e.stopPropagation(),children:(0,i.jsx)(mI,{})})}):null
```

面板组件 `mI`（偏移 827463 附近）：

```js
(0,i.jsx)("div",{role:"dialog","aria-modal":"true","aria-label":e("canvas:directorShortcutsTitle"),
  className:"nodrag nopan nowheel relative h-[314px] w-[480px] rounded-2xl border border-white/10 bg-[#1f1f1f]/95 p-6 text-neutral-50 shadow-[0_2px_4px_rgba(0,0,0,0.04),0_4px_10px_rgba(0,0,0,0.10)] backdrop-blur-[32px]",
  children:[
    (0,i.jsx)("div",{className:"flex h-[22px] items-center justify-between",
      children:(0,i.jsx)("h2",{className:"text-base font-medium leading-[22px] text-neutral-50", …})}),
    (0,i.jsxs)("div",{className:"mt-4 flex h-[228px] w-[432px] items-stretch",children:[
      (0,i.jsx)("div",{className:"flex w-[192px] flex-col justify-between", …6 行…}),
      (0,i.jsx)("div",{className:"mx-6 w-px shrink-0 bg-white/10","aria-hidden":!0}),
      (0,i.jsx)("div",{className:"flex w-[192px] flex-col justify-between", …6 行…})]})]})
```

★ 这些原文与 16 个类名锚点已由 `probes/extract831.py` **机器提取**入库
`raw/source-831-shortcut-code.json`（含 chunk 内偏移、chunk sha256、代码摘录）。

---

## 三、clone 侧实施

### 3.1 新增 `src/components/director/DirectorShortcutsDialog.tsx`

- `role="dialog"` + `aria-modal="true"` + `aria-label="快捷键"`
- 挂在导演台根节点内，**绝对偏移 left 297 / top 60**（照抄源站的写死值）
- 遮罩 `absolute inset-0 z-40` + `onMouseDown` 关闭；对话框自身 `stopPropagation`
- Esc 关闭（组件内 `keydown` 捕获 + 导演台全局键盘处理里也有一条）
- 两列各 192、竖线 `margin: 0 24px`、行 `h-7`
- ⌘ / ⌫ 用**从源站 chunk 机器提取**的 path（§5）

### 3.2 `DirectorIconRail.tsx`：把「帮助」从死按钮变成菜单

- 加 `aria-haspopup="menu"` / `aria-expanded={helpMenuOpen}`
- 加 `role="menu"` 容器 + 两枚 `role="menuitem"`
- 菜单 `absolute bottom-full left-0 z-50 pb-2`（**向上弹**）

### 3.3 `DirectorDesk.tsx`：接线

- `shortcutsOpen` 状态 + 挂载对话框
- 「使用教程」→ 清 `localStorage` 的「已跳过」标记 ＋ `setTimelinePanelOpen(true)`
  ＋ `dispatchEvent(new CustomEvent("director:open-tutorial"))`
  ⟹ ★ 它**不是死按钮**：源站那套 5 步引导的 clone 版本只有第 1 步（batch 552/553），
  本批让「使用教程」**真的能唤出引导气泡**（否则点了什么也不会发生）

### 3.4 `DirectorTimeline.tsx`：引导气泡改用 `createPortal(…, document.body)`

★ 本批**顺手修掉一个旧缺陷**：

| 项 | 修之前 | 修之后 |
| --- | --- | --- |
| 渲染位置 | 时间轴 section 内 | `document.body`（源站同款） |
| 绝对 y | **1749**（视口只有 1080 ⟹ 看不见） | **850**（260×114 @(163,850)） |

★ **根因**：气泡是 `position: fixed`，但它原先渲染在时间轴 section 里
⟹ **有个祖先创建了 containing block**（`transform` / `filter` / `will-change` 之一）
⟹ `top: calc(100vh - 230px)` 被当成相对那个祖先算 ⟹ 掉到视口外。

★ z 用 `1800`（portal 到 body 后脱离导演台的 `z-[100]` 上下文 ⟹ 要用源站引导浮层同款的层级）。

---

## 四、逐字几何对照（源站 vs clone）

★ 源站与 clone 的读数用**同一段读数 JS** 采（`probes/help831.py` / `probes/clone831.py`），
视口同为 1920×1080 ⟹ 绝对几何可直接比。

| 序 | 对象 | 源站 | clone | 相等 |
| --- | --- | --- | --- | --- |
| 序 1 | 「帮助」按钮盒 | 32×32 @(8,1040) | 32×32 @(8,1040) | ✔ |
| 序 2 | 菜单盒 | 120×78 @(8,954) | 120×78 @(8,954) | ✔ |
| 序 3 | 菜单项 1（快捷键） | 110×32 @(13,959) | 110×32 @(13,959) | ✔ |
| 序 4 | 菜单项 2（使用教程） | 110×32 @(13,995) | 110×32 @(13,995) | ✔ |
| 序 5 | 对话框盒 | 480×314 @(297,60) | 480×314 @(297,60) | ✔ |
| 序 6 | 标题盒 | 48×22 @(322,81) | 48×22 @(322,81) | ✔ |
| 序 7 | 左列 | 192×228 @(322,123) | 192×228 @(322,123) | ✔ |
| 序 8 | 右列 | 192×228 @(563,123) | 192×228 @(563,123) | ✔ |
| 序 9 | 12 行标签盒＋键帽盒 | 逐行 | 逐行 | ✔ 全等 |
| 序 10 | 12 行标签文字 | 12 条 | 12 条 | ✔ 逐字相同 |
| 序 11 | 4 个 SVG 图标位置 | (695,209)/(659,249)/(695,289)/(731,329) | 同 | ✔ |

### ★ 那 4px 的来源（标题 81 而不是 85）

源站 h2 的计算样式是 **`margin: 0px 0px 8px`** —— 即 **UA 默认的 `margin-bottom: 8px`**，
源站的 CSS **没有重置标题的下外边距**。

⟹ 标题行是 `flex h-[22px] items-center` ⟹ h2 的**外边距盒**（22 + 8 = 30px）
在 22px 高的行里居中 ⟹ **边框盒被抬到行顶之上 4px** ⟹ 落在 **81** 而不是 **85**。

⟹ clone 的 Tailwind preflight 把标题 margin 清零了 ⟹ 直接照抄会低 4px
⟹ 本批用 inline `marginBottom: 8` 复现源站这个行为（门禁 S5 钉住）。

---

## 五、★★ 本批抓到的一条**自证式判据**（本批最重要的收获）

### 5.1 发生了什么

第一版门禁 S12 长这样：

```python
SRC_COMMAND_PATH = (            # ← ★ 我手打的
    "M5.25 5.25H10.75V10.75H5.25V5.25ZM5.25 5.25H4.25C3.42157 5.25 2.75 4.57843 2.75 "
    "3.75C2.75 2.92157 3.42157 2.25 4.25 2.25C5.07843 2.25 5.75 2.92157 5.75 4.25V5.25…"
)
ok("S12 …", SRC_COMMAND_PATH in dialog_src and SRC_DELETE_PATH in dialog_src, …)
```

⟹ 这条判据**只证明**「clone 里那段文字 == 我手打的那段文字」
⟹ **不证明**「那段文字 == 源站的 path」。

⟹ 而我手打时**抄错了**：源站的 ⌘ path 是

```
… 10.25 3.75V4.25M5.25 10.75H4.25C3.42157 10.75 2.75 11.4216 2.75 12.25C2.75 13.0784
  3.42157 13.75 4.25 13.75C5.07843 13.75 5.75 13.0784 5.75 12.25V11.75M10.75 10.75H11.75…
```

（下半部**先左后右**），我抄成了**先右后左** ⟹ **门禁照样 15/15 全绿**。

### 5.2 怎么发现的

★ 不是靠眼睛看（16px 的 ⌘ 图标，肉眼看不出臂的顺序反了），
而是靠**机器提取源站原文**再逐字 diff：

```python
# 从 chunk 里正则抓 d:"..."
re.search(r'd:"([^"]+)"', chunk_text[idx:idx+1500]).group(1)
```

⟹ diff 报出 12 处 `replace` ⟹ 全部集中在下半部两条臂。

### 5.3 修法（三层）

1. **期望值从 raw 读**（`raw/source-831-shortcut-code.json`，由 `probes/extract831.py`
   **机器提取**）⟹ 门禁核验的是「clone == **源站原文**」，不是「clone == 我抄的」。
2. **raw 自证**（门禁 S16）：raw 里的两段 path 必须**嵌在它们自己的源站代码 excerpt 里**
   （excerpt 是从 chunk 原文截下来的）⟹ raw 不是「一个来源不明的字符串常量」。
3. **像素级判据**（门禁 S17）：把 clone 截图与源站截图里**同一坐标**的 16×16 徽标
   逐像素比 ⟹ 这才证明**渲染**一致，而不只是**数据**一致。

### 5.4 ★ 证明这条判据真的有牙

| 场景 | 最大绝对差 | 差 > 8 的像素 | 判定 |
| --- | --- | --- | --- |
| path **抄错**那版 | **54** / 255 | **10** / 256 | 不同形 |
| path **抄对**（现状） | **5** / 255 | **0** / 256 | 同形 |

⟹ ★★ 阈值定在「最大差 ≤ 24 且差>8 的像素 ≤ 2」
⟹ **远小于**抄错版的实测差异 ⟹ 这条判据**有能力**区分两者。

⟹ 并且做过**真实注入自检**：把 clone 的 path 改一个字（`3.75V4.25` → `3.75V4.15`）
⟹ 门禁 **S12 立刻翻红**（15/16）⟹ 复原后 17/17。

### 5.5 这条教训的通用形态

★ **手打的标识符是输入，不是测量** —— 它一旦被门禁读回，就从「我的抄写」
变成「关于世界的断言」，之后每一轮都在为一个**从未存在**的事实作证。

⟹ 与本仓已记录的几条同族：
「读数是空 ≠ 东西不存在」（读的是**词**）、
「判据扫的元素类型必须与界面真实元素类型相交」（读的是**类型**）、
「门禁自己也要有阴性对照」（判据**强度**）、
「N 从数据反推」（**样本量**）。

⟹ **本条讲的是判据的**期望值**从哪来**：必须是**被测对象的原文**，
不能是「我抄的」——★ 哪怕我抄的那份**当时看起来完全合理**。

---

## 六、★ 一处**如实记账、不改**的差异：「帮助」按钮的可达性

| 序 | 场景 | 源站 | clone |
| --- | --- | --- | --- |
| 序 1 | 时间轴**关**（默认） | 「帮助」**可达**（命中它自己） | 「帮助」**可达** |
| 序 2 | 时间轴**开** | 「帮助」**被盖住**（命中的是时间轴的条） | 「帮助」**被盖住**（命中「收起属性」） |

⟹ ★ **「被盖住」这件事两边是同构的** ⟹ 真正的差别**只在默认值**：
源站时间轴默认**关** ⟹ 帮助按钮平时可达；**clone 默认开** ⟹ 被盖住。

⟹ ★ **本批不改 clone 的时间轴默认态**：**88 个门禁脚本**依赖 clone 的时间轴存在
⟹ 改默认值会把它们全打红 ⟹ 属于另一个批次的范围。

⟹ ⟹ **用户当前要打开 clone 的「帮助」，需先关掉时间轴**
（点底部胶囊里的「动画时间轴」开关）。

⟹ 门禁 S15 把这个前提**显式断言**（clone 展开时命中「收起属性」；
源站展开时命中的**也不是**「帮助」）。

---

## 七、门禁

`scripts/verify-liblib-batch831.py` ⟹ **主检查 17/17 ｜ 阴性对照 17/17**

| 序 | 判据 | 核验什么 |
| --- | --- | --- |
| 序 1 | S1 | 源站读数自洽（几何、12 行、4 个 SVG） |
| 序 2 | S2 | clone 菜单盒 == 源站 |
| 序 3 | S3 | 两枚菜单项（文字＋盒）== 源站 |
| 序 4 | S4 | 对话框盒 + `role`/`aria-modal` == 源站 |
| 序 5 | S5 | 标题盒 == 源站（含那 4px 的来源） |
| 序 6 | S6 | 两列 == 源站 |
| 序 7 | S7 | 12 行**几何**逐行 == 源站 |
| 序 8 | S8 | 12 行**文字**逐字 == 源站 |
| 序 9 | S9 | 4 个 SVG 徽标（16×16）== 源站 |
| 序 10 | S10 | 点外面关 + Esc 关 |
| 序 11 | S11 | 「使用教程」不是死按钮 + 引导泡**在视口内** |
| 序 12 | S12 | 两段 path 逐字 == **raw 里的源站原文** |
| 序 13 | S13 | `aria-haspopup` / `aria-expanded` / `role=menuitem` |
| 序 14 | S14 | 引导泡必须 `createPortal(…, document.body)` |
| 序 15 | S15 | 「帮助」可达性的前提（时间轴默认态差异）显式断言 |
| 序 16 | S16 | **raw 自身可信**（path 嵌在自己的源站 excerpt 里） |
| 序 17 | S17 | ⌘ 徽标**像素**与源站同形 |

★ **每条阴性只翻它自己那一条**（17 条阴性逐条核过「实际翻红集合 == {期望}」）。

★ 判据**分字段**：S7 只读盒、S8 只读文字 ⟹ 两者的阴性互不串门。

---

## 八、★ 不声称

- ★ **不声称源站的「使用教程」与 clone 等价**：源站那套是 **5 步**引导（源码 `cC` 组件），
  clone **只有第 1 步**（batch 552/553 的既有决策）⟹ 本批只保证「点了会真的唤出引导」。
- ★ **不声称源站「使用教程」对话框的几何**：本批探针点到源站那枚 menuitem 后，
  抓到的是一枚 **Agent promo card**（280×311 @(1040,700)，`aria-label="Agent 已升级为 TV Director"`），
  **不是**引导本体 ⟹ 源站引导对话框的盒**未采到** ⟹ 不设源站对照判据。
- ★ **不声称源站面板的「使用教程」页签内容**：面板本身只有一个「快捷键」页
  （源码里就是一个 `role=dialog`，没有页签）⟹ 源站的「使用教程」在**另一条路径**上。
- ★ **不声称 clone 的时间轴默认态已与源站一致**：见 §6（如实记账，未改）。
- ★ **不声称 ⌘ / ⌫ 之外的那些键帽**（T/H/V/R/F/Y/X/WASDQE/G/⇧D/Z）的**功能**已验证：
  本批只核验了**面板的呈现**，不核验按键在 clone 里是否真的生效
  （batch 830 已核过源站侧的 T 与 ⌘Z）。
- ★ **像素比对只做了 ⌘ 那一枚**（⌫ 在源站那枚没有独立的 16×16 读数可裁，
  它的盒与 ⌘ 不同 ⟹ 未纳入像素判据）。

---

## 九、证据清单

| 序 | 文件 | 内容 |
| --- | --- | --- |
| 序 1 | `raw/source-831-help-geometry.json` | 源站：帮助按钮 / 菜单 / 对话框 / 使用教程 四组读数 |
| 序 2 | `raw/source-831-help-zorder.json` | 源站：时间轴未开 / 已开时的命中栈（可达性前提） |
| 序 3 | `raw/source-831-title-detail.json` | 源站：标题行与 h2 的计算样式（含 `margin: 0px 0px 8px`） |
| 序 4 | `raw/source-831-shortcut-code.json` | **机器提取**的源站代码证据（两段 path + 16 个类名锚点 + 代码摘录 + chunk sha256） |
| 序 5 | `raw/glyph-831-pixel-compare.json` | ⌘ 徽标的逐像素比对读数（两张 16×16 矩阵） |
| 序 6 | `raw/clone-831-help-geometry.json` | clone：⓪/⓪b/①/②/③/④/⑤/⑥ 八组读数（**活体重跑复核过**） |
| 序 7 | `probes/help831.py` | 源站探针 |
| 序 8 | `probes/clone831.py` | clone 探针（**与源站同一段读数 JS**） |
| 序 9 | `probes/extract831.py` | ★ 源站 path 的**机器提取**脚本 |
| 序 10 | `probes/glyphcmp831.py` | ★ 像素比对脚本 |
| 序 11 | `probes/title831.py`、`probes/zorder831.py`、`probes/diag831.py`、`probes/coach831.py` | 专项探针 |
| 序 12 | `images/source-831_*.png`、`images/clone-831_*.png` | 两边各 3 张（menu / shortcuts / tutorial） |
| 序 13 | `verify-report.json` | 门禁产物 |

★ clone 的读数**活体重跑复核过**：重跑后与入库版本 **9/9 个键逐字全等** ⟹ 入库读数不是陈旧的。
