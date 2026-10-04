# batch 749 — 把 `createDirectorCapture` 的发送那一跳走完；把「有静态、无运行时」的残差从**一个数**变成**一族一族的门**

## 起点

748 导演台首轮普查报出：有效并集 447、运行时出现 224、**没出现 223**，
并明确写了「本批不区分成因」。本批做两件事：

A. `createDirectorCapture` 的发送那一跳（748 只点到快门，命令本身没被触发）
B. 那 223 种按**门族**归因，并对两族代表做运行时验证

全部读数来自 clone。**源站导演台关着，本批一次都没碰。**

## A. 采集链路：两跳 + 幂等

```
DirectorViewport.tsx:3586   data-director-capture          ← 第 1 跳 快门（store 零写入）
DirectorInspector.tsx:288   data-director-capture-preview  ← 预览
DirectorInspector.tsx:307   data-director-send-capture     ← 第 2 跳 发送到画布
DirectorDesk.tsx:589-591    const sendCapture = (c) => { if (c.sentNodeId) return;
                                                     createDirectorCapture(sourceNodeId, …) }
```

| 步骤 | `past` | 节点 | 边 | 可见变化 |
|---|---|---|---|---|
| ① 快门 | **0→0** | ±0 | ±0 | 预览出现（`638 × 359`、`alt`「机位01 · 对峙中景构图截图」）、`capture-status="ready"`、文案「**1 张构图**」 |
| ② 发送 | 0→**1** | 10→**11** | 11→**12** | 新文件「**导演台截图-机位01 · 对峙中景**」、`image` 类型 5→**6** |
| ③ 再点（已 disabled） | **1→1** | ±0 | ±0 | 零变化（`nodeIds` 逐项相同） |

**截图落画布是 `image` 节点，不是视频** —— `canvasStore.ts:2818 type: "image"`、
`:2824 filename: \`导演台截图-${capture.cameraName}\``。这与 748 的动画导出
（建 `video` 节点）是两种不同的产出。

**发送后 UI 双向翻转**：按钮文案「发送到画布」→「**已发送到画布**」+ `disabled`；
`data-director-capture-status` 文案「1 张构图」→「**已回到画布**」。
**幂等**由 `DirectorDesk.tsx:590 if (capture.sentNodeId) return;` 保证。

### 导演台的产出在**画布侧**被打上 6 个标记

```
ImageNode.tsx:216-221
  "data-director-capture-node": true,          "data-director-capture-id": …
  "data-director-capture-source-id": …,        "data-director-capture-camera-id": …,
  "data-director-capture-aspect": …,           "data-director-capture-edge-id": …,
```

**快门只带出导演台侧的 2 种**（`capture-preview` / `send-capture`）；
这 6 个标记**由发送带出** ⟹ **画布节点组件知道导演台的存在** ——
耦合点不只在 store，还在画布节点的渲染层。

### 发送还会把画布选中态切到新节点

发送这一步除 6 个 capture 标记外，还带出 **8 种**图片编辑器属性：
`data-image-edit-panel` / `data-image-editor-control` / `-footer-icon` / `-model` /
`-settings` / `-top-controls` / `data-image-toolbar` / `data-owner-node-id`
⟹ 新建的图片节点在画布上是**被选中**的。合计 14 种。

## B. 残差：一族一族的门

748 报出的 223 种（走完 7 枚 rail 之后）按属性前缀可归成 **283 个族**。
本批运行时验证其中两族：

### 族① 采集图库族（11 种）

门：**选中机位 → 相机页签的「截图」子页**（`DirectorInspector.tsx:2332`
`selected.kind === "camera" && cameraTab === "captures"`）

| | 图库读数 |
|---|---|
| 进页时（A 阶段那张已发送） | `items: 1`、`groups: 1`、`sendAllDisabled: **true**` |
| 该机位下再拍 2 张后 | `items: **3**`、`groups: 1`、`empty: false`、`sendAllDisabled: **false**` |

⟹ **图库条目数随快门次数逐张 +1**；
`send-all` 的 disabled 语义是「**没有未发送项就禁用**」
（`DirectorInspector.tsx:638 disabled={!captures.some(c => !c.sentNodeId)}`）
—— A 阶段那张已发送所以禁用，拍 2 张未发送后解禁。

### 族② 姿势族（10 种）

门：**选中角色 → 角色页签的「姿势」子页**（`:2338`
`selected.kind === "character" && characterTab === "pose"`）
⟹ `pose-panel` / `pose-group` / `pose-control` / `pose-value` / `pose-preset` /
`pose-side` / `pose-state` + `data-expanded` / `data-pose-preset` /
`data-pose-control-count`。点「属性」页签 **+0** 种。

### 页签是「同名不同值」

| 属性 | 三个/两个值与文案 |
|---|---|
| `data-director-camera-tab` | `properties`（属性）/ `motion`（运动轨迹**NEW**）/ `captures`（截图） |
| `data-director-character-tab` | `properties`（属性）/ `pose`（**姿势**，不是「姿态」） |

## 探针与判据返工六处（**全部是我自己的错**）

1. **按属性名去重枚举门 ⟹ 同名不同值的页签只点了一个**（本批最重要）——
   749c 枚举开启器时用 `seen` 按 `a.name` 去重，于是 `data-director-camera-tab` 的
   3 个值只算 1 枚门，点它也只点中第一个值 ⟹ 「选中 7 个 treeitem **+0 种**」。
   **那不是「门特别深」，是探针粒度错了。** 改法：门要按 `(属性名, 属性值)` 枚举。
2. **树行不是 `<button>`** —— 我按 `[data-director-tree] button` 找对象行，
   只找到「打组」「解组」两枚。树行是
   `<div role="treeitem" data-director-object-id=…>`（`DirectorObjectTree.tsx:458-465`），
   **而且它没有 `data-director-` 前缀**。
3. **被截断的普查输出不能当全集** —— 748 那次 446 种的终端输出是 head+tail 截断，
   我据此以为「没有 `data-director-object-*`」，实际它在中间那段。
4. **页签文案别凭直觉写** —— 我按源码变量名 `characterTab` 猜标签是「姿态」，
   实际 DOM 文案是「**姿势**」；`cameraTab` 的 `motion` 值文案还带「**NEW**」角标。
5. **判据 C6 的基线取早了** —— 我在**快门之前**取属性基线，
   于是 `capture-preview` / `send-capture`（快门带出的）被算进「发送带出」。
   改法：基线取在快门之后、发送之前，才能把两跳的贡献分开。
6. **判据 C7 用了探针的读数、没考虑状态已变** —— 749d 是从**全新页面**测的
   （图库 `items: 0`），而验收器里 A 阶段已经拍过并发送过 1 张
   ⟹ 进页时 `items: 1`、且 `sendAllDisabled: true`。
   **改法**：不写死「+4 再 +8」这种依赖初始状态的增量，改判与初始状态无关的性质
   （条目数逐张 +1、`send-all` 的 disabled 语义）。

## 判据（9/9）

| | 判据 | 读数 |
|---|---|---|
| C1 | 静态：有效并集 447；`createDirectorCapture` 恰好两处；`sendCapture` 有 `sentNodeId` 幂等守卫；`ImageNode.tsx` 6 个 capture 标记；store 落点 `type:"image"` | 全定位 |
| C2 | 第 1 跳快门：store 零写入；预览有 alt 与尺寸；`capture-status=ready`、文案「1 张构图」 | `638×359` |
| C3 | 第 2 跳发送：`past`+1、节点+1、边+1；新文件「导演台截图-\<机位名\>」；`image` +1 | 5→6 |
| C4 | 发送后 UI 翻转：按钮「已发送到画布」+ `disabled`；状态文案「已回到画布」 | 双向 |
| C5 | 幂等：再点已 disabled 的发送键 ⟹ `past`/节点/边/`nodeIds` 逐项零变化 | 零变化 |
| C6 | 6 个 `data-director-capture-*` 由**发送**带出（快门只带 2 种）；发送另带 8 种图片编辑器属性 | 2 / 6 / 8 |
| C7 | 族①：机位→「截图」带出 11 种；条目数逐张 +1；`send-all` = 「无未发送项则禁用」 | 1→3、true→false |
| C8 | 族②：角色页签 2 枚；点「姿势」+10、点「属性」+0 | +10 / +0 |
| C9 | 残差按前缀成族：447 种归成 283 个族，最大族 24；本批验证可打开 21 种 | 283 族 |

两轮连跑 **0 字段差异**。

## 待拍板

**需改 `src/`，等授权：**

1. **发送截图后自动选中新节点、弹出图片编辑器** —— 要不要保持？
   本批未验这个选中态能否撤销（740 记过「undo 只恢复 nodes/edges，不恢复选区」）。
2. **图库里已发送的条目要不要弱化** —— 现在已发送的条目和未发送的并排，
   只有「批量发送」会跳过它们（`:606-608`）。
3. **「运动轨迹」页签的 `NEW` 角标要不要长期保留** —— 未取证源站是否长期带。

**纯运行时工作，不需改 `src/`（应直接进后续批次）：**

4. **其余残差族逐族验证** —— 运动路径/路径锚点族（20 + 6 种，最大）、
   场景设置族、全景图族、分组族、锁定提示族。
5. **`data-director-camera-tab="motion"`（`CameraMotionTab` 11 种）本批没点。**
6. **批量发送与清空图库的功能本身** —— 本批只读到 `disabled` 翻转，没点。
7. **图库的分组维度** —— 种子只有 1 个机位，`capture-group={cameraName}`
   的多机位分组未验。

## 不声称

- **其余残差族未逐族验证** —— 223 种里本批只打开 21 种；
  运动路径族、场景族、全景族、分组族、锁定提示族**只从源码守卫表达式推断，无运行时读数**。
- **不声称**「拍照 638×359」是稳定尺寸 —— 随视口与机位参数变化，
  本批只在本视口（1280×1150）下读到该值。
- **发送后的选中态能否撤销未验。**
- **多机位分组未验**（种子只有 1 个机位）。
- **未与源站导演台做任何对照** —— 源站关着，需点击授权。

## 与前批关系

- **748「本批不区分成因，只报数」** —— 本批把那个 223 从**一个数**变成
  **一族一族的门**，并对两族做了运行时验证。**一条待办从「不声称」变成有读数。**
- **748「`createDirectorCapture` 未触发」** —— 本批走完发送那一跳，命令真跑通；
  33 个记账命令里未跑的从 15 个降到 **14 个**。
- **748「`createDirectorAnimationExport` 建 `video` 节点」** vs 本批
  「`createDirectorCapture` 建 `image` 节点」—— **导演台两种产出落到画布的节点类型不同**。
- **741「一个对不上的数字自己就是线索」** —— 本批又用上一次：
  「选中 7 个 treeitem **+0 种**」看起来像「门很深」，实际是**我按属性名去重**漏了同名不同值的页签。
- **744/746/748「穷举一个状态的全部读点」** —— 本批把它用在页签上：
  `data-director-camera-tab` 有 3 个值，每个值是一个独立的状态面。
- **740「undo 只恢复 nodes/edges 不恢复选区」** —— 本批新读数「发送后自动选中新节点」
  与它相关，但**本批未验撤销**，不下结论。

## 验收器

`scripts/verify-liblib-batch749.py` — 静态扫 13 个组件求有效并集 + 采集链路 10 个行号
+ 采集三跳（快门 / 发送 / 幂等）+ 快门与发送的属性贡献分离
+ 族①（机位→截图，含图库条目数与 `send-all` 语义）
+ 族②（角色→姿势）+ 残差前缀族表，两轮连跑逐字段一致。
