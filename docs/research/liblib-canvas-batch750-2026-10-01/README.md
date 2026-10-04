# batch 750 — 运动/路径/曲线三族：把 749 只从源码推断的残差打开；以及一次「我把自己的结论推翻」

## 起点

749 把 748 报出的 223 种「有静态、无运行时」残差按前缀归成 283 个族，
只验了采集图库（11 种）与姿势（10 种）两族，并明确写了：

> 其余残差族未逐族验证（运动路径/场景/全景/分组/锁定族只从源码守卫表达式推断、无运行时读数）

本批做两件事：

- **A.** 打开三族 —— `data-director-motion` / `data-director-path` / `data-director-curve`，
  静态共 **52 种**（31 + 15 + 6），是 749 残差里最大的一片
- **B.** 途中发现自己 750 第一版写下的「导演台没有历史栈」是错的，做受控实验推翻它

全部读数来自 clone。**源站导演台关着，本批一次都没碰。**

## B. 先说推翻自己的那一条

750 的第一版我在探针跑完前先下了一条结论：

> 初始 store 的 undo/redo/history 键：`None`
> 撤销入口：`{"undoBtn": 0, "redoBtn": 0, "anyUndoText": []}`
> ⟹ **导演台无撤销**

前两个读数是真的。**结论是错的。** 错在两处：

| 我做的 | 真相 |
|---|---|
| `grep -c "pushHistory\|undoStack\|redoStack" src/store/directorStore.ts` → 0 | 历史栈的真名是 **`undoDirector` / `redoDirector`**，那三个词在 store 里确实 0 处 |
| 「全页没有撤销入口」 | 入口不是按钮，是 `DirectorDesk.tsx:506-516` 挂在 **window keydown** 上的快捷键 |

（`undoDirector` 的接口声明在 `directorStore.ts:577`、实现在 `:3742` ——
两处签名不同：声明是 `() => DirectorCommandResult;`、实现是 `() => {`。
**光按 `undoDirector:` 匹配会同时命中两处**，这是本批第一次取行号取错。）

随后 750e 顺手按了一次 `Cmd+Z`，读数 `path-count 1 → 0`，与自己的结论直接冲突。
于是做了受控往返实验（每格一个新页面，避免上一格状态污染下一格）：

| 格 | 按键 | `path-count` 轨迹 | 名字 / 锚点数 |
|---|---|---|---|
| A 对照 | 不按 | `1` | 「机位自动帧轨迹」/ `[2]` |
| B | `Cmd+Z` | `1 → 0` | — |
| C | `Cmd+Shift+Z`（重做栈空） | `1 → 1` | 无操作 |
| D | `Cmd+Z` → `Cmd+Shift+Z` | `1 → 0 → 1` | 名字与锚点数**逐项复原** |
| E | `Cmd+Y` | `1 → 1` | 无操作 |
| F | `Cmd+Z` ×2 | `1 → 0 → 0` | 第二次无操作（建路径是一条原子命令） |

**修正后的结论**：导演台的撤销/重做**功能完整**（往返可复原、栈空时正确无操作、
空栈连按第二次无操作），但**只有键盘**——
151 个可交互节点里，文本 / `title` / `aria-label` / 属性名四条路全查，**0 个**是撤销/重做入口。

规矩补一条：**断言「某能力不存在」前，先穷举该能力的全部命名形态**
（动词 + 名词 + 缩写 + 快捷键表），别拿一个命名习惯当全集。

> 与画布对照：画布的 `undo()` 挂在 `src/app/page.tsx:1342-1346`，
> 导演台的 `undoDirector()` 挂在 `DirectorDesk.tsx:506-516`，是**两套独立监听**。

## A. 三族的门链

```
① 选中机位（对象树）
   └→ DirectorInspector 相机页签 motion
        └→ DirectorCameraMotionTab 顶层 6 种
② 选中一条时间线轨道
   │  注意：可点目标是行内一个**没有 data-* 标记**的 role="button"
   └→ data-director-create-motion-path 解禁 → 点开
        └→ 路径菜单：自由绘制 2 工具 + 3 预设
             ├─ 选预设 → createMotionPath ⟹ sr-only 层长出整条路径的 DOM
             └─ 选工具 → 绘制面板（两种工具手势不同，见下）
③ 选中轨道 + 点 data-director-open-curve-editor
   └→ editorMode timeline → curve ⟹ 曲线族 6 种
```

### ① 运动页签（`camera-tab="motion"`）

749 记录过这枚页签但没点。点开后顶层同时出现 6 种：
`motion-vcam` / `motion-qr` / `motion-record` / `motion-retry` /
`motion-preset-button` / `motion-create-path`。

相机页签三值是 **`properties`（属性）/ `motion`（运动轨迹**NEW**）/ `captures`（截图）**。

**两个按钮完全没有 `onClick`。** 这不是源码读数，是运行时读 React props：

| 按钮 | `__reactProps$` 的键 | `onClick` |
|---|---|---|
| `[data-director-motion-preset-button]`「⟳ 预设运镜」 | `type` / `data-…` / `title` / `className` | **无** |
| `[data-director-motion-create-path]`「创建运动轨迹」 | 同上 | **无** |
| `[data-director-motion-qr]` | … / **`onClick`** / `className` | 有 |
| `[data-director-motion-record]` | … / **`onClick`** / `disabled` / `title` | 有 |
| `[data-director-motion-retry]` | … / **`onClick`** / `className` | 有 |

点完两个死按钮：属性集 **0 增 0 减**、`path-count` 仍 **0**、视口截图差异落在噪声门内
（尺子怎么标定的见「判据方法」）。它们唯一的交互是 `title`
「预设运镜面板位于时间线控制簇」「创建运动轨迹面板位于时间线控制簇」——
`DirectorCameraMotionTab.tsx:12-17` 把这记为有意的 `CLONE_DECISION`。

另两个读数：
- `motion-retry` 的**唯一效果是改下面那行说明文案**：为「机位01 · 对峙中景」创建运动轨迹
  → 为「机位01 · 对峙中景」创建运动轨迹**（重试 1 次）**
- `motion-qr` 点一下就把「录制」解禁：`disabled: true`（`title`「请先连接虚拟相机」）→ `false`、`title` 清空

### ② 路径菜单与「一跳入口」

菜单 **176×204**，5 个按钮全部 enabled：

```
自由绘制
  铅笔路径(pencil)  钢笔路径(pen)        ← 自由绘制段
  直线路径(line)   圆环路径(ring)  矩形路径(rectangle)
```

**`data-director-track-draw-trail` 是「选轨道 + 开菜单」的一跳入口**（86×24、
`aria-label`「绘制轨迹」、`aria-pressed`）：一次点击后轨道选中切到
`director-track-camera-main` 且菜单同时打开。

#### 轨道行的真正可点目标没有 `data-*`

| 读法 | 结果 |
|---|---|
| 点 `[data-director-track-row]` **外壳** | 选中态**逐项不变**（外壳源码 `DirectorTimeline.tsx:1708-1726` 里就没有 `onClick`） |
| 点行内 `[role="button"]` | 选中态切到 camera 轨道 ✅ |

行内那个可点目标是 `<div role="button" tabIndex={0} title="机位01 · 对峙中景 · 机位">`
（`DirectorTimeline.tsx:1751-1756`）—— **没有任何 `data-*` 标记**。

我第一版就是点了外壳，于是读出「选中 camera 轨道后建路径落到角色身上」。
`tracksAfter` 里 camera 仍 `selected="false"` 本来就说明我没点上。**该读数撤回。**

### ③ 建路径之后长出什么

选中 camera 轨道、菜单里选「直线路径」：

| | 读数 |
|---|---|
| `path-count` | `0 → 1` |
| 路径 id | `director-motion-path-director-camera-main-<时间戳>` |
| 名字 | 「**机位自动帧轨迹**」（角色轨道则是「角色自动帧轨迹」） |
| 锚点 | **2 个**，都是 `type="vertex"`、`handles: []` |
| sr-only 层盒子 | **1×1** |
| 锚点盒子宽 | **0** |

本批带出 **18 种**属性（`path-id` / `-anchor` / `-anchor-id` / `-anchor-type` /
`-anchor-selected` / `-world-anchor` / `-handle` / `-visible` / `-pivot` /
`-inspector` / `-locked` / `-enabled` / `-orient` / `path-anchor-list` /
`path-anchor-option` / `path-name` / `path-reset` / `path-reset-offset` /
`path-transform-axis` / `path-transform-field`）。

> 走完整条链（选 camera 轨道 → 建 line → 开曲线编辑器）后，
> 三族从 **2 种涨到 27 种，本批打开 25 种**；静态 52 种里**仍缺 25 种**，
> 全在「运动页签顶层」与「路径绘制态」——它们各自要另一个前置条件。

`data-director-path-reset` 走的是 `resetMotionPath`（`:1096`）——**重置锚点，不是删除**：
点完 `count 1 → 1`、锚点数 `2 → 2`。

#### 路径在 3D 里画出来了，但只占视口的万分之零点几

运动轨迹不是 SVG，是 react-three-fiber 的 `<Line>`（`DirectorViewport.tsx:1571-1600`）。
用像素差间接量：同一机位下建一条**矩形**路径，视口差 **212 像素 / 0.0112%**（视口 718×880）。

| 动作 | 视口像素差 | 占比 |
|---|---|---|
| 点两个死按钮 | 0–4 | ~0% |
| **建一条矩形路径**（默认机位） | **212** | **0.0112%** |
| 同一动作，**先把机位旋转开** | **99 572** | 5.25% |
| 拖动视口旋转（尺子标定） | **839 034** | **44.26%** |

⟹ **确实画了**，但默认机位下这条轨迹只占视口的万分之零点几；
**把机位转开之后同一动作的可见量差 469 倍**。这就是「创建成功却像没反应」的来源。

#### 两种工具的手势不一样（我第一版用错了手势）

| 工具 | 手势 | 源码 | 实测 |
|---|---|---|---|
| 铅笔路径 | **拖拽即成** | `DirectorViewport.tsx:1678-1711`：`pointerdown` 播种 → `pointermove` 追加 → **`pointerup` 立刻 `finishMotionPathDrawing()`** | 8 次 move 后松手 ⟹ **9 个锚点**、名字「**铅笔路径1**」；拖拽全程面板保持打开 |
| 钢笔路径 | **逐点点击 + 完成键** | 同上，但 `tool !== "pencil"` 走 `updateMotionPathDraftLastHandle` | 3 次点击后面板仍在、此时 `count` 仍 0；点「**完成钢笔路径**」⟹ **3 个锚点**、「钢笔路径1」 |

我第一版用无移动的 `mouse.click` 测铅笔，读出「第一次点视口就死」——
**撤回**。铅笔本来就是「按住拖、松手即完成」的工具，点一下就松手等于让它立刻收工。

### ④ 曲线编辑器是**另一个编辑器模式**

`data-director-open-curve-editor`（`DirectorTimeline.tsx:1136-1141`）
把 `data-director-timeline-mode` 从 **`timeline` 改成 `curve`**，
曲线族 6 种齐现（`curve-editor` / `-track-id` / `-preset` / `-values` / `-handle` / `-locked`），
并出现「**返回时间线**」按钮回到时间线模式。

### ⑤ 轨道名的键盘死路

| 读数 | 值 |
|---|---|
| `activeElement` | 就是那个 `<div role="button" tabindex="0">`（**可聚焦**） |
| `title` | 「机位01 · 对峙中景 · 机位」 |
| `onKeyDown` | **不存在** |
| 按 `Enter` | 选中态**逐项不变** |
| 按 `Space` | 选中态**逐项不变** |

焦点能停在上面、键盘却用不了。ARIA 要求 `role="button"` 必须响应 Enter 与 Space。

## 判据

| # | 判据 | 读数 |
|---|---|---|
| C1 | 静态：三族共 52 种；`createMotionPath` 声明与实现各一处；两个 motion 按钮源码里无 `onClick` | 全定位 |
| C1b | **本批自我推翻**：错词 `pushHistory\|undoStack\|redoStack` 在 store 0 处，真名是 `undoDirector`/`redoDirector`，快捷键在 `DirectorDesk` 不在 `page.tsx` | 行号齐全且两者不同 |
| C2 | 门=选中机位→相机页签 motion ⟹ 顶层 6 种齐现；三页签值 = 属性/运动轨迹NEW/截图 | 6/6 |
| C3 | 两个 motion 按钮无 `onClick`（另三个有）；点完 0 属性增 0 属性减；截图差异在标定阈值内 | 三重对账 |
| C4 | 路径菜单 176×204、2 工具 + 3 预设全 enabled；`draw-trail` 86×24 是「选轨道+开菜单」一跳 | 一跳成立 |
| C5 | 轨道行外壳不可点；可点目标是行内无 `data-*` 的 `role=button` | 外壳点击零变化 |
| C6 | 建 line ⟹ `count 0→1`、「机位自动帧轨迹」、2 锚点；sr-only 层 1×1、锚点盒宽 0 | 带出 18 种 |
| C7 | 铅笔拖拽 9 锚点 / 钢笔点击+完成 3 锚点 | 两种手势分别成立 |
| C8 | `path-reset` 是重置不是删除 | `count 1→1`、锚点 `2→2` |
| C9 | 曲线编辑器：`editorMode` timeline→curve，曲线族 6 种齐现 + 「返回时间线」 | 6/6 |
| C10 | 轨道名可聚焦但 Enter/Space 无效 | 选中态三项相同 |
| C11 | 三族残差 `2 → 27`，打开 25 种 = 27−2 | 对平 |
| C12 | 撤销/重做往返完整但只有键盘；151 节点 0 入口 | 六格全对 |

**判据 13/13，两轮读数一致。**

## 探针与判据返工（全是我自己的错）

1. `REACT_PROPS` 用 `Object.keys().find(前缀)` 找 `__reactProps$`，但 `__reactFiber$` 排在前面
   ⟹ 命中 fiber，「有没有 `onClick`」**根本没读出来**。
2. SVG 探针取 `document.querySelector('svg')` = 第一个 svg（一个 22×14 的图标），
   而运动轨迹是 **react-three-fiber 的 `<Line>`**，不是 SVG ⟹ 那条读数整条作废。
3. 读 `window.__libtv_director` 取 store —— **导演台 store 根本没挂 window**
   （与画布的 `__libtv_store` 不同）⟹ `motionPaths=null` 是「没读到」不是「没有」，
   差点当成结论。改为一律经 DOM 读。
4. 基线本来就选中了一条 transform 轨道 ⟹「选轨道带出 0 种」不构成门的证据。
5. `DUMP` 返回 dict，我按 set 用 ⟹ `TypeError`。
6. 把 `data-director-path-reset` 当成「清空路径」，它其实是 `resetMotionPath`
   ⟹ 第二个问题的起点已经有 1 条路径，**三个问题全部作废**。
   规矩：**一条链路只问一个问题，问之前必须能从 `path-count` 读到 0**。
7. 「选中 camera 轨道后建路径落到角色身上」——撤回（点错了节点，见上）。
8. 「铅笔第一次点视口就死」——撤回（用错了手势，见上）。
   规矩：**工具的交互模型不同，不能用同一种手势测两个工具**。
9. **判据自己也有三个 bug**：`list.sort()` 返回 `None` 恒不等 ⟹ C9 假失败；
   C11 差值符号写反；C8 要的 `resetHandler` 键探针根本没采。
10. **PNG 字节相同不是稳定判据**：同一画面两次渲染 PNG 长度 72787 vs 72788。
11. **「像素必须为 0」不是稳定判据**：WebGL 同一状态两次渲染抖动 0 与 4 个像素交替（0.00021%）。
12. **用「建路径」当阳性对照也失败**：它只有 ~212 像素的变化（0.0112%），
    WebGL 合成下时灵时不灵 —— 同一序列一次读到 212、一次读到 0。
    **小信号不能当标尺。** 第三版改用「拖动视口旋转」当标尺（稳定 839034 像素 / 44.26%），
    判据只断言「尺子有效」+「死按钮点击落在 0.1% 门内」，建路径的像素差只作记录。
    顺带查清：元素截图与整页裁剪在视口区域只差 5 个像素 ⟹ **元素截图能拍到 WebGL**，
    不是截图工具的锅。「先怀疑探针、再怀疑产品」这条规矩第二次生效。
13. 探针第三轮又踩一次**顺序错**：`pathCountAfterClicks` 是在建完路径之后才读的，
    读到 1 ⟹ C3 假失败。规矩：探针里每个读数都要先问「这一刻之前我动过什么」。
14. 静态取行号取错两处：`undoDirector` 的接口声明与实现都匹配 `undoDirector: () =>`，
    报出来是同一个行号（用 `=> {` 才区分得开）；铅笔收尾的
    `if (draft.tool === "pencil")` 在文件里出现两次，取到了 onPointerMove 里那处
    （要取第二处、onPointerUp 里的）。
    **规矩：同一个模式在文件里出现多次时，先数清有几处再决定取哪一处。**
15. **「导演台没有历史栈」被运行时推翻**（见 B 节）。

## 待拍板（需改 `src/`，等授权）

1. 运动页签那两个**没有 `onClick`** 的按钮要不要改成真入口（打开时间线控制簇对应面板），
   还是加 `disabled` + 说明让用户知道它此刻不可用？现状是「看起来能点、点着没反应、
   只有鼠标悬停才看得出原因」。
2. `motion-retry` 唯一效果是改一行说明文案，要不要给它一个真实动作
   （重试虚拟相机连接）？
3. 撤销/重做**要不要给按钮**？功能已完整（往返可复原），但 151 个可交互节点里 0 个入口，
   鼠标用户完全无路。
4. 轨道名的 `role="button"` **要不要补 `onKeyDown`**（Enter/Space）？
   现在可聚焦但键盘不可用，是明确的 ARIA 违规。
5. 运动轨迹行的可点目标**要不要加 `data-*` 标记**（与全项目其他可点元素不一致）？
6. `data-director-path-reset`「重置」要不要补 tooltip 说明它重置的是锚点不是删除路径？
7. 「自由绘制」两个工具手势差别很大（铅笔拖拽即成 / 钢笔点+完成键），
   要不要在按钮 `title` 上写出来？
8. 新建的运动轨迹在默认机位下只占视口 0.0112%，转开机位后同一动作差 469 倍 ——
   要不要在建完后自动把机位对准这条轨迹（或给一个「聚焦轨迹」动作）？
   这是「创建成功却像没反应」的来源。

## 纯运行时、不需改 `src/`（应进后续批次）

9. 三族**仍缺 25 种**逐个打开：运动页签的 `motion-qr`/`-record`/`-retry`/`-vcam`/
   `-slider`/`-slider-value`/`-preset-button`/`-create-path` 需要进运动页签；
   `path-menu`/`-free-draw`/`-draw-tool`/`-drawing`/`-drawing-cancel`/
   `-anchor-handle`/`-anchor-handle-axis`/`-anchor-position`/`-anchor-type-option`/
   `-locked`/`-orientation-hint` 需要进绘制态。
10. 关键帧编辑器门（`motion-keyframe-editor` + `keyframe-field` + `keyframe-axis`）
    需要先选中一个关键帧。
11. 锚点的 `type` 只有 `vertex` 出现过 —— `handle`（贝塞尔手柄）要一条非直线路径才出现。
12. 749 残差里其余族（场景 25 / 全景 9 / 分组 8 / 锁定 / 人群 / 手机 vcam 面板）
    仍全部未验证。
13. 导演台其他命令的撤销粒度（本批只验了「建路径」一条是原子的）。

## 不声称

- 除本批打开的三族外，749 的其余残差族仍未逐族验证。
- 运动轨迹在 3D 场景里的可见渲染只用像素差**间接**证明（约 212 像素 / 0.0112%）：
  确实画了，但默认机位下小到几乎看不见。没有做像素级定位，
  也没验证线的颜色 / 粗细 / 选中态配色。该差值本身不稳定（读到过 212 也读到过 0）。
- sr-only 层无条件渲染全部路径、3D 层只画 `enabled` 的
  （`DirectorViewport.tsx:1582-1583` 有 `.filter(path => path.enabled)`）——
  这处不一致是**源码读数**，本批没有构造「禁用路径 + 读屏」的场景实测。
- 「`role=button` 没有键盘通路」只验了轨道名这一个，导演台其他 `role=button` 未普查。
- 撤销/重做只验了运动路径这一条命令的往返。
- `Cmd+Z` 走 `DirectorDesk` 的 window keydown（`:506-516`），与画布 `page.tsx:1342` 的 `undo()`
  是两套；两者在导演台打开时是否互相抢键（谁先 `preventDefault`）本批**未测**。
- 铅笔只跑了一次 8 步直线拖动，锚点采样密度与真实手绘的差异未测。
- 钢笔的 3 次点击用固定屏幕坐标，锚点世界坐标随之确定；没有验证锚点是否都落在绘制平面上。
- 未与源站导演台做任何对照（源站关着，需点击授权）。
