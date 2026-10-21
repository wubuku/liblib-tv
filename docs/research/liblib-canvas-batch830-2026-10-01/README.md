# batch 830 — 源站导演台：时间轴缩放（**关闭 batch 599/604 遗留**）与撤销语义（**★ 两处读数翻案**）

> 批次性质：**纯测量与门禁修正**（零 `src/` 改动 ⟹ `npm run build` 跳过）
> 日期：2026-10-21
> 门禁：`scripts/verify-liblib-batch830.py` ⟹ **主检查 15/15 ｜ 阴性对照 15/15**
> 源站测试项目：**已复原并经全新 context 复验**（FOV 67 / 机位1 / 缩放 44）

---

## 一、一句话结论

源站导演台的「**时间轴缩放**」**不跨会话保留**（关台重开、刷新页面后都回到 44）
⟹ ⟹ **batch 599 / 604 留下的那条遗留「源站关闭再打开导演台时 zoom 是否保留」到此关闭，答案是「不保留」**。

同时，本批把上一批写进 raw 的**两条撤销读数翻案**：

| 上一批写的 | 实情 | 怎么翻的 |
| --- | --- | --- |
| 「撤销 = `Z`」 | 实为 **⌘Z**（⌘ 是 **SVG 图标**，纯文本读数器读不到它） | 读源站组件代码 |
| 「按 `Z` 撤不掉 FOV / 改名」 | **前提不满足**（源站撤销**必须**带 ⌘/Ctrl，裸 Z 被源码明确排除）⟹ 用 ⌘Z 重测：**撤得掉**，且 ⌘⇧Z 能重做 | 读源码 + ⌘Z 重测 |
| 「clone 多了一项源站没有的能力 / 快捷键不一致」 | **不成立** ⟹ clone 的 `Cmd/Ctrl+Z` 与源站的 ⌘Z **一致** | 同上 |

⟹ ⟹ **clone 与源站在「撤销」这件事上是同构的**，上一批的「不一致」结论作废。

---

## 二、证据分层：实测 · 源码 · clone

本批最重要的方法论收获：**盲按快捷键测不出东西，必须读源站代码**。

### 2.1 为什么必须读代码（实测踩的坑）

上一批用来「把焦点从输入框挪开」的选择器是
`[data-director-workspace] h1, [role=dialog] h1` —— **它在源站 DOM 里根本不存在**
（本批用同一选择器复现了 `TimeoutError: waiting for locator(...)`）
⟹ 那个「挪焦点」的动作**从来没执行过** ⟹ 后续按键读数全都不可信。

于是去读代码，发现**缓存的 161 个源站 chunk 里连导演台的组件代码都没有**：

| 检索 | 结果 |
| --- | --- |
| `directorShortcutUndo` | 只出现在 **i18n 字典 chunk**（`e602a5b3e…`） |
| `directorViewModeDirector`（「导演视角」按钮的标签） | **同样**只出现在 i18n 字典 chunk |
| `directorConsoleTitle` | 同上 |

⟹ 导演台的组件代码是**开台时懒加载**的 chunk，不在旧缓存里。
⟹ 本批开台时录网络请求，把**新出现的 159 个 chunk** 抓到 `/tmp/liblib_srcjs2/`，
导演台组件代码在 `0fmehki05gkzw.js.js`（1,018,130 字节）。
⟹ 24 个关键锚点已抽成 `raw/source-830-shortcut-code.json`（**含原文片段 + chunk 内偏移**），
门禁 S5/S6/S7 直接核验这些原文 ⟹ 核验的是「源站代码长什么样」，不是我自己的转述。

### 2.2 源站键盘处理（源码原文）

```js
// 快捷键面板（mI 组件）：撤销那一行
{label:e("canvas:directorShortcutUndo"), keys:[{id:"undo-command", icon:"command"}, {id:"undo-key", label:"Z"}]}
// 打组 / 解组 同款
{label:e("canvas:directorShortcutGroup"),   keys:[{id:"group-command",  icon:"command"}, {id:"group-key",  label:"G"}]}
{label:e("canvas:directorShortcutUngroup"), keys:[{id:"ungroup-command",icon:"command"}, {id:"ungroup-shift",label:"⇧"}, {id:"ungroup-key",label:"D"}]}

// 两组键
hY = new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"]);
hX = new Set(["w","a","s","d","q","e"]);

// window + 捕获阶段
window.addEventListener("keydown", e, !0);

// 修饰键约束（★ 本批的核心）
if(hY.has(n) && ("z"!==n||e.ctrlKey||e.metaKey)
             && ("g"!==n||e.ctrlKey||e.metaKey)
             && ("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
             && ("c"!==n||e.ctrlKey||e.metaKey)
             && ("h"!==n||!e.ctrlKey&&!e.metaKey&&!e.altKey)) {
  …
  else if("z"===n) e.shiftKey ? nu() : nd();      // ⌘⇧Z = redo，⌘Z = undo
}
```

⟹ ★★ **裸 `z` 被第一道条件明确排除**（`"z"!==n||ctrl||meta`）⟹ 上一批按裸 Z 的读数**无效**。
⟹ `z`/`g`/`d`/`c` 要带 ⌘/Ctrl，`d` 还要 ⇧，`h` 反过来**必须不带**修饰键。
⟹ `w/a/s/d/q/e` 走 `hX` 那一支（**不带**修饰键）。

### 2.3 源站撤销栈（源码原文）

```js
// 只有这些 action 进历史栈（27 项）
lX = new Set(["ADD_CHARACTER", …, "UPDATE_CHARACTER", "UPDATE_CHARACTERS", "UPDATE_CAMERA",
              "UPDATE_EMPTY_OBJECT", "UPDATE_PROP", "ADD_ANIM_TRACK", …,
              "UPDATE_TIMELINE", "REMOVE_MOTION_PATH", "UPDATE_ENV", "IMPORT", "CLEAR"]);

// 撤销 / 重做
if("UNDO"===t.type){ if(0===(e=lZ(e)).past.length) return e; let t=e.past.at(-1);
  return {past:e.past.slice(0,-1), present:t, future:[e.present,...e.future], transientPast:null}; }

// 瞬时记账：拖拽中的改动先不记账，失焦/提交时才补一条
n = r && "transient"===("history" in t && t.history ? t.history : "record")
// 栈深：past.slice(-49) ⟹ 最多留 50 条
```

⟹ ★★ **`UPDATE_CAMERA` 在可撤销集里** ⟹ 机位属性（FOV、改名）**理应**能被 ⌘Z 撤
⟹ 这与实测完全吻合。
⟹ ★★ **`transient` 机制与 clone 同构**（batch 828 测到的 clone：手势期间「值已落盘但不记账」，
关台才提交成一条 `camera-fov` 条目）⟹ 同一个设计。

### 2.4 源站实测读数（全部入库 `raw/`）

| 格 | 读数 | 产物 |
| --- | --- | --- |
| 时间轴缩放控件 | `input[type=range][aria-label="时间轴缩放"]`、**min 0 / max 100**、`.value` 显示 **44**、**`value` 属性真值 `43.77510040160642`** | `source-830-timeline-zoom.json`、`source-830-undo-cmdz2.json` |
| 改缩放（精确法） | 44 → **82**（回读校验过） | 同上 |
| **关台重开后** | **44**（**不保留**）⟹ ★★ 关闭 599/604 | `source-830-timeline-zoom.json` |
| **刷新页面后** | **44**（**不保留**） | 同上 |
| 快捷键面板 | 撤销 **⌘Z** ／ 打组 **⌘G** ／ 解组 **⌘⇧D** ／ 俯视视角 T ／ 重置视角 H ／ 移动当前视角 WASDQE | `source-830-shortcut-code.json` |
| **⌘Z 撤 FOV** | 67 → 45 → ⌘Z → **67** ⟹ 撤得掉 | `source-830-undo-cmdz.json` |
| **⌘⇧Z 重做 FOV** | → **45** | 同上 |
| **⌘Z 撤改名** | 「机位1-830」→ ⌘Z → **「机位1」** ⟹ 撤得掉 | 同上 |
| **⌘⇧Z 重做改名** | → **「机位1-830」** | 同上 |
| **⌘Z 撤缩放** | 44 → 82 →（**失焦提交后**）⌘Z → **82** ⟹ **撤不掉**（缩放不进栈） | `source-830-undo-cmdz2.json` |
| 阳性对照：裸键 **T** | 视口像素差 **67.014%** ⟹ 俯视视角**确实生效** ⟹ 快捷键管线是活的 | `source-830-t-screenshot-diff.json`、`images/830_T_*.png` |
| T 之后按 ⌘Z | 视口像素差 **0.000%** ⟹ 视图一动不动；同一个 ⌘Z 撤掉的是 **FOV**（50→67）⟹ **视图不入撤销栈** | 同上、`images/830_v10_T_*.png` |

---

## 三、与 clone 的对照（三项全同构）

| 维度 | 源站 | clone | 判定 |
| --- | --- | --- | --- |
| 撤销键 | **⌘Z**（源码条件 + 面板 ⌘ 图标） | `Cmd/Ctrl+Z`（`DirectorDesk.tsx` 的 `if (modifier && event.key.toLowerCase() === "z")`） | ★★ **一致**（上一批说「不一致」是错的） |
| 撤销覆盖机位属性 | ⌘Z 能撤 FOV / 改名（实测） | `Cmd+Z` 能撤 FOV / 改名（batch 828：`UNDO/COMMITTED`、改名真被撤掉） | ★★ **一致** |
| 撤销覆盖「时间轴缩放」 | ⌘Z **撤不掉**（实测，失焦提交后仍 82） | `setTimelineZoom` 只改 `timeline.zoom`，**不写历史条目** | ★★ **一致** |
| 缩放跨会话 | 关台重开 / 刷新后**都回 44** | 刷新后回默认 | ★★ **一致** |
| 瞬时记账 | `history:"transient"` ＋ `COMMIT_TRANSIENT` | 手势期间不记账、关台提交成一条 `camera-fov`（batch 828） | ★★ **同构** |

⟹ ⟹ **batch 830 相对 828 的净结论：没有发现 clone 的撤销与源站有差异**（上一批说的那处差异是读数缺陷造成的）。

---

## 四、本批推翻了什么（更正已写进原 raw 文件）

按「前缀/后缀式文档不可重写」的纪律，**原始观测一个字没改**，只在四个 raw 文件末尾**追加**了 `★读数更正`；
门禁 S2 会检查更正还在（缺了就红），S5/S6 会检查更正内容与源码锚点一致。

| 文件 | 原读数 | 更正 |
| --- | --- | --- |
| `source-830-timeline-zoom.json` | `②改缩放.after = null`、`★没调到 = true` | 含义是「没**精确命中**手打的目标值 70」，**不是「没改成」**（四次点击回读都是 75） |
| `source-830-shortcuts.json` | 面板「撤销 = Z」 | 实为 **⌘Z**（⌘ 是 SVG 图标 ⟹ 文本读数器读不到它） |
| `source-830-undo-fov.json` | 「按 Z 后 FOV 不变」 | **前提不满足的无效读数**（源站撤销要 ⌘Z）⟹ 用 ⌘Z 重测：**撤得掉** |
| `source-830-undo-rename.json` | 「按 Z 后名字不变」 | 同上 ⟹ 用 ⌘Z 重测：**撤得掉** |

---

## 五、方法论收获（本批踩的坑，六条）

1. ★★★ **改值动作的判据必须是「等于目标值」，不是「不等于原值」。**
   v10 的复原函数判据是「点一下，值**变了**就返回」⟹ 复原 FOV=67 时第一击**正好命中 67**，
   判据不满足「变了」⟹ **继续点** ⟹ 第二击把 FOV 改成 **64** ⟹ 而 FOV 会**落盘到服务端**
   ⟹ ⟹ ★★ **把用户的项目改脏了**。修法：判据改成「命中即停」，并用 `fixfov830.py` 修回 67，
   **经全新 context 复验**（服务端值 67、名称「机位1」、缩放 44）。

2. ★★★ **读数器扫的元素类型，必须与界面真实元素类型相交。**
   面板上的 ⌘ 是 `<svg>`（16×16），**没有文字** ⟹ 纯文本 leaves 读数器只看见「Z」⟹
   「撤销 = Z」这个**看起来很正常**的读数，恰恰是读数器的盲区。
   ⟹ 用法：断言面板内容要**读源码**（或读 SVG/图标节点），不要读文本。

3. ★★ **可见性判据对源站的原生控件必然为 false。**
   源站的滑杆（时间轴缩放 / 场景缩放 / 水平旋转 / 球形半径 / FOV）**全是** `opacity:0` 的原生
   `<input type=range>` 盖在自绘轨道上 ⟹ 任何「祖先或自身 opacity≤0 ⇒ 不可见」的判定，
   对它们**一律返回 false** ⟹ 「读数说它不可见」**不能**当成「它不存在」。
   ⟹ 本批读数器改成**按标签行取结构**，不按可见性过滤。

4. ★★★ **判据读的不是「被测性质所在的字段」，就会拿到假阴性。**
   本批第一版判「按 T 无反应」——因为读的是**场景世界变换**（场景平移/旋转/缩放），
   而 T 改的是 **editor camera pose**（3D 视口的机位）⟹ 读数口径不对 ⟹ 假阴性。
   ⟹ 改用**视口区域截图像素差**：T 前后 **67.014%** ⟹ 生效；按 ⌘Z 后 **0.000%** ⟹ 撤不掉。
   ⟹ ★ 像素比较**必须限定区域**：排除右栏，否则「⌘Z 撤 FOV」会让右栏数字变化，
   被误读成「视图也变了」。

5. ★★ **选择器在源站不存在 ⇒ 那个动作根本没发生。**
   `focus_desk` 用的 `[data-director-workspace] h1, [role=dialog] h1` 在源站**零命中**
   ⟹ 盲测一圈全是「无变化」，差点得出「源站的快捷键都是死的」这个**完全相反**的结论。
   ⟹ 用法：任何「先做 X 再看 Y」的探针，**先证明 X 真的发生了**（读回值 / 截图 / 像素差）。

6. ★★ **复刻 Web 应用：读原站 bundle，别从行为反推。**
   本批盲测三轮（v7/v8/v10 前段）全部空手而归；**读一次代码**就把「撤销是 ⌘Z」
   「撤销栈覆盖 UPDATE_CAMERA」「transient 记账」三条一次性说清，
   而且**每一条都能被门禁静态核验**。

---

## 六、登记一个产品缺口（下一批实施）

源站导演台**有**「帮助 → 快捷键」面板：
`role="dialog" aria-modal="true" aria-label="快捷键"`，**480×314**、`rounded-2xl`、
`bg-[#1f1f1f]/95`、`p-6`，标题 + **两列各 192px**（中间 1px 分隔线）+ 每行 12 行快捷键表，
每行右侧是**键帽徽标**（⌘ 是 SVG、⇧ 是文字、其余是字母）。

⟹ ★★ **clone 的导演台没有这个面板**：`src/components/director/` 里没有任何「快捷键 / 使用教程」浮层，
只有 `DirectorIconRail.tsx` 里那枚 `aria-label="帮助"` 的圆钮（**点了没反应**）。
⟹ 证据（本批备好）：面板渲染代码在 `raw/source-830-shortcut-code.json`，
面板几何在 `raw/source-830-shortcuts.json`（两列 12 行的 leaves 读数，含每行的坐标）。
⟹ ★ 这属于「**有入口、没内容**」的缺口，与 batch 824 那条「有功能、用户找不到」同类但相反。

---

## 七、不声称（本批**没有**证明的）

- ★ **源站的撤销栈跨刷新 / 跨关台重开是否保留**：未实测。源码看是 React `useReducer` 的
  `past/present/future` ⟹ **推断**不保留，但**没有实测**，不下结论。
- ★ **源站的 ⌘C 复制 / ⌘G 打组 / ⌘⇧D 解组**：源码里有，本批**未实测**。
- ★ **WASDQE 移动视口**：只证明了按键会到 handler（T 生效可证管线是活的），
  **视口移动本身没做像素对照** ⟹ 「W 能不能移动视口」**仍未判定**（上一批那一格因读数口径错而作废）。
- ★ **clone 与源站的撤销覆盖是否完全等价**：本批只对了 **FOV** 与 **改名** 两格；
  源站的 `UPDATE_CAMERA` 还涵盖位置/旋转等，clone 的对应覆盖**未逐项对齐**。
- ★ **源站时间轴缩放真值 43.7751 是怎么算出来的**：观察到它是浮点（显示值 44 是四舍五入），
  但**没读出它的计算公式** ⟹ clone 用固定 44，差 **0.2249 个百分点**，属**已知差异、未定性**。
- ★ **源站的快捷键面板是否有「使用教程」页签内容**：面板代码里有两个页签的 i18n 键
  （`directorTutorial` / `directorShortcuts`），本批**只读了快捷键那一页**。

---

## 八、产物清单

| 类别 | 路径 |
| --- | --- |
| 门禁 | `scripts/verify-liblib-batch830.py`（主检查 15 条 · 阴性 15 条 · 离线） |
| 门禁产物 | `docs/research/liblib-canvas-batch830-2026-10-01/verify-report.json` |
| 源站读数 | `raw/source-830-timeline-zoom.json`（含更正）、`raw/source-830-undo-fov.json`（含更正）、`raw/source-830-undo-rename.json`（含更正）、`raw/source-830-shortcuts.json`（含更正）、`raw/source-830-i18n-director.json`、`raw/source-830-nameinput.json` |
| 本批新增读数 | `raw/source-830-undo-cmdz.json`（⌘Z/⌘⇧Z 实测）、`raw/source-830-undo-cmdz2.json`（缩放 ⌘Z + T 视图）、`raw/source-830-shortcut-code.json`（24 个源码锚点）、`raw/source-830-t-screenshot-diff.json`（像素差）、`raw/source-830-recon-focus.json`（焦点侦察）、`raw/source-830-pipeline-v8.json`（管线探测）、`raw/source-830-fixfov.json`（项目复原复验） |
| 截图 | `images/830_T_before.png`、`images/830_T_after.png`、`images/830_v10_T_{before,after,undo}.png` |
| 探针 | `probes/`：`measure830.py`、`recon830{a,b,c}.py`、`undo830{c,e}.py`、`diag830d.py`、`recon830g.py`、`undo830{g,i,j}.py`、`fixfov830.py`、`fetch830.py`、`extract830_code.py`、`annotate830.py` |

---

## 九、验收

```
主检查 15/15 ｜ 阴性对照 15/15
```

★ 阴性对照**每一条只翻它自己那一条**（改动落在该性质真正读取的字段上）：
N1 改「精确法改前」⟹ S1 红；N2 改「精确法改后」⟹ S2 红；N3／N4 改「关台重开后」「刷新后」⟹ S3／S4 红；
N5 去掉撤销行的 ⌘ 图标 ⟹ S5 红；N6 把撤销键条件改成裸 Z 可用 ⟹ S6 红；
N7 从可撤销集里去掉 `UPDATE_CAMERA` ⟹ S7 红；N8／N9 改「⌘Z 后的 FOV／名字」⟹ S8／S9 红；
N10 改「失焦后 ⌘Z 的缩放」⟹ S10 红；N11／N12 改两组像素差 ⟹ S11／S12 红；
N13 把 clone 的 z 判定改成裸 Z ⟹ S13 红；N14 改 i18n 键 ⟹ S14 红；N15 把「已复原」改成 False ⟹ S15 红。

★ 本批**零 `src/` 改动** ⟹ `npm run build` 跳过（工作树里的 `src/components/jimeng/*` 是**他人 WIP**，不在本批范围）。
★ 源站测试项目：**已复原**（FOV 67 / 机位1 / 缩放 44），并经**全新浏览器 context** 复验（`raw/source-830-fixfov.json`）。
