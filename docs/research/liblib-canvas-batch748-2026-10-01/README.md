# batch 748 — 导演台首轮运行时普查：属性全集与运行时差集分三类对平；`createDirectorAnimationExport` 真跑通

## 起点

741–747 七批**全在画布**，导演台一次都没做过运行时验收。
静态侧 `src/components/director/`（13 个 `.tsx` + 7 个 `.ts`，31k 行）规模不小。

本批做四件事：属性全集普查、运行时与全集的差集（**分三类对账**）、
7 枚 rail 入口逐个点、两个导演台记账命令。

全部读数来自 clone。**源站导演台当前关着，需要点击授权才能进，本批一次都没碰。**

## 决定性读数

### ① 静态侧要报**两个口径** —— 460 与 446 都对，差 14

| 口径 | 数字 |
|---|---|
| 按文件求和（有重复计数） | **460** |
| 去重字面量并集 | **446** |
| 补 `dataset.` 派生名后的**有效并集** | **447** |

按文件：`Inspector 142 / Viewport 86 / Timeline 79 / Desk 46 / PhoneVcam 23 /
ObjectTree 21 / IconRail 20 / AiImportModal 12 / CameraMotionTab 11 / CurveEditor 8 /
ExportPanel 6 / ScenePromptBar 6 / **Mannequin 0**`。

13 个属性名跨文件重复，其中 **`data-director-bottom-bar` 出现在 3 个文件**
（Desk / Timeline / Viewport）⟹ 12×1 + 1×2 = **14**，两个口径正好差 14。

### ② 静态字面量扫描有**已知盲区**：`dataset.xxx =`

```
DirectorViewport.tsx:410   dataset.directorGizmoWebglCanvas = …  ⟹ data-director-gizmo-webgl-canvas
DirectorViewport.tsx:2920  dataset.directorWebglCanvas = …      ⟹ data-director-webgl-canvas
```

正则是 `\b(data-[a-z0-9-]+)`，只认源码里写出来的字面量。
本批差集里 `data-director-gizmo-webgl-canvas` **就是这样落进「非并集」的** ——
它不是「动态加载」，是扫描口径的已知缺口，补进有效并集后归位。

### ③ 运行时与静态的差要**分三类**，不能只报一个残差

| 账 | 数字 |
|---|---|
| 整页 `data-*`：首屏 → 走完 7 枚 rail | 200 → **250** |
| 运行时 250 = 导演台属性 **224** + 非并集 **26** | |
| 非并集 26 = **画布/应用层残留 24** + **无 `data-director-` 前缀的导演台属性 2** | |
| 有效并集 447 − 出现 224 = **没出现 223** | |

⟹ **导演台盖在画布之上、画布仍在 DOM 里** —— 那 24 种里含 `data-open-director`、
`data-inert`、`data-canvas-tool`、`data-edge-delete`、`data-temporary-pan` 等
⟹ **整页 `data-*` 总数不能直接当导演台的数**。

那 2 种无前缀的导演台属性是 `data-director-node` / `data-director-node-id`：
带 `data-director-` 前缀，但**字面量与 `dataset.` 两种扫描都找不到来源** ⟹ 成因未取证。

### ④ 打开导演台**不写 store**

入口 `[data-open-director]` 在 `script-execution` 节点上（种子 `b-bTLLuU4w5q`）。点它之后：

| 标识符 | 值 |
|---|---|
| `data-director-canvas-id` | `canvas-2` |
| `data-director-source-node-id` | `b-bTLLuU4w5q`（= 入口所在节点） |
| `data-director-view` | `director` |
| `data-director-focus-scope` / `-state` | `workspace` / `workspace` |
| `data-director-project-id` / `-session-id` | 现场生成 |

`past` / 节点 / 边**逐项零变化** ⟹ 导演台是独立工作区，切换不进画布历史。
6 个区域齐：workspace(1280×1150) / viewport(718×880, WebGL) / tree / timeline /
shot-bar / bottom-bar，加关闭钮。

### ⑤ 7 枚 rail 入口里**恰好 2 枚点开 0 新增**

| # | `data-director-rail-entry` | `title` | 新增属性种类 |
|---|---|---|---|
| 0 | `scene` | 场景 | **0** |
| 1 | `add-character` | 添加角色 | 3 |
| 2 | `add-camera` | 添加机位 | **34** |
| 3 | `panorama` | 全景图 | 2 |
| 4 | `aspect-ratio` | 选择画幅比例 | 4 |
| 5 | `ai-import` | AI 识图导入 | 7 |
| 6 | `help` | 帮助 | **0** |

「添加机位」一枚就带出 34 种（FOV 滑杆/读数/帮助浮层/旋钮、跟随状态与目标、
look-at、预览 canvas 与状态、相机页签、目标坐标…）。
「场景」与「帮助」两枚**一个 `data-*` 都没带出来** ——
**不判定**这两枚是惰性入口还是它们打开的东西不带测试标记。

### ⑥ `createDirectorAnimationExport` **真跑通了**

「导出视频到画布」点完不是没反应 —— 是**约 9 秒的进度过程**：

```
idle ──► exporting（progress 单调递增 0 → 100，本轮采到 11 个 exporting 样本）
      ──► success（progress 100）
```

期间提交键 `disabled`、文案变「导出中」（11 个样本全部如此）；结束后恢复可点、
文案回「导出视频到画布」。终态 store：

| | 前 → 后 |
|---|---|
| `past` | 0 → **1** |
| 节点 | 10 → **11** |
| 边 | 11 → **12** |
| 新文件 | **「第一集：咖啡馆对峙 动画导出」** |
| `video` 类型计数 | 1 → **2** |

### ⑦ `createDirectorCapture` 的**第一跳是 store 零写入**（两跳）

`data-director-capture`（视口快门）点完 `past`/节点/边零变化，
但 `data-director-capture-preview` 与 `data-director-send-capture` 冒出来
⟹ **快门 → 预览 → 发送**是两跳，`createDirectorCapture` 本批**未触发**。

## 探针与判据返工六处（**全部是我自己的错**）

1. **给一个没测过的数配了否定结论**（本批最重要）—— 第一版探针只在
   0s / 1.2s / 4.2s 三个点读 `data-director-export-status`（全程都在 `exporting`），
   就写下「点了没反应」。实际命令跑完并写进了画布。
   **「没变化」要分层归因**（入口没点到 / 面板没开 / 异步没完成）——
   本例是**异步没完成**，前两者都正常。**固定等待 + 三点采样得出的是假否定。**
2. **拿「按文件求和」当全集** —— 判据 C1 写死 446，扫描器给的是 460。
   差 14 正是线索，顺着它查出 13 个跨文件属性名（其中一个在 3 个文件里）。
   **规矩**：普查类数字必须标明口径。
3. **「跑了一轮就在第 4.2 秒下结论」**（第 1 条的根因）—— 改法是**轮询到状态离开
   `exporting` 为止**（封顶 40 × 700ms），而不是固定等待。
4. **`getAttribute('[data-director-canvas-id]')`** —— 把**整个选择器当属性名**传进去了，
   六个标识符全读成 `null`，差点判成「导演台没渲染」。改法：`sel.slice(1, -1)`。
5. **过程值进了两轮比对** —— `progress` 的逐样本读数（8 vs 7、35 vs 34、44 vs 43）
   差在**我 700ms 的轮询节奏落在动画的不同点上**，是采样产物不是产品不确定性。
   改法：只保留与采样无关的性质（**单调递增**、样本数、首末值），逐样本轨迹只留 stdout。
   这与 745「横幅 1800ms 会消失、要点完立刻读」是同一族：**异步过程值不能当稳定读数**。
6. **整数当字符串比** —— `progressFirst`/`progressLast` 是 `int`，
   判据里写成 `== "0"` / `== "100"` ⟹ C6 连着两轮 FAIL。

## 判据（7/7）

| | 判据 | 读数 |
|---|---|---|
| C1 | 静态：13 个组件，**求和 460 / 并集 446**（13 个跨文件属性名，其中 `data-director-bottom-bar` 在 3 个文件 ⟹ 12×1 + 1×2 = 14）；2 处 `dataset.` 盲区 | 460 / 446 / 14 / 2 |
| C2 | 打开导演台：入口在 `script-execution` 节点；六个标识符齐；**store 零写入** | `canvas-2` / `director` / `workspace` |
| C3 | 差集三笔对平：200 → 250；有效并集 447；250 = 224 + 26；26 = 24 + 2；447 − 224 = 223 | 全对 |
| C4 | 7 枚 rail 入口里恰好 2 枚 0 新增（`scene` / `help`），`add-camera` 34 种 | 0/3/34/2/4/7/0 |
| C5 | `createDirectorCapture` 第一跳：store 零写入，`capture-preview` + `send-capture` 出现 ⟹ 两跳 | 命令未触发 |
| C6 | `createDirectorAnimationExport` **真跑通**：`idle → exporting`（progress 单调、按钮 disabled + 「导出中」）→ `success`(100)；终态 `past`+1、节点+1、边+1、文件名以「 动画导出」结尾 | 全链路 |
| C7 | 6 个区域齐 + 关闭钮 + 7 枚 rail + 1 个 shot 选项 | 齐 |

两轮连跑 **归一化现场 id 后 0 字段差异**；未归一化时 3 处差异
（`director-project-` / `director-session-` 两个时间戳 id 及其派生的判据 detail）。

## 待拍板（需改 `src/`，等授权）

1. **「场景」「帮助」两枚 rail 入口要不要补测试标记 / 补实现** ——
   7 枚里只有这 2 枚点开 0 新增。要么它们是惰性入口（加 `data-inert` 自证），
   要么该补功能。**先要源站行为再定**（源站导演台需点击授权才能进）。
2. **`data-director-node` / `data-director-node-id` 的来源要不要查清** ——
   带 `data-director-` 前缀却两种扫描都找不到。
3. **导出过程要不要给「可否中断」的入口** —— 现在 9 秒里提交键 `disabled`，
   没有取消。源站是否有取消未取证。
4. **`createDirectorCapture` 的发送那一跳** —— 预览已经出来了，
   `data-director-send-capture` 在检查器里；要不要补一次真跑（需改 src/ 才能加标记，
   但**跑它本身不需要改 src/** ⟹ 应该直接进下一批的运行时验证，不进本清单）。
5. **那 223 种「有效并集里有、运行时没出现」要不要逐类归因** ——
   分「条件渲染的面板」与「更深交互才出现的状态」两类统计。纯运行时工作，不需改 src/。

## 不声称

- **未与源站导演台做任何对照** —— 源站导演台关着，需点击授权；本批全部读数只来自 clone。
- **`createDirectorCapture` 的发送键那一跳未跑** —— `data-director-send-capture`
  点下去会发生什么未取证。
- **有效并集里没出现的那 223 种，成因未分类** —— 「条件渲染的面板」与
  「更深交互才出现的状态」两类本批没分开统计。
- **「场景」「帮助」0 新增的成因未取证** —— 不判定为惰性、不判定为缺陷。
- **只开了 1 个 shot、只测了首屏与 7 枚 rail** —— 多个 shot、相机页签切换、
  AI 导入模态内部、导出面板的各选项（`data-director-export-aspect` 有 3 枚，
  本批只用默认值导出一次）都未逐个走。
- **导出的 9 秒时长只测了一次** —— 不声称它恒定；
  `durationMilliseconds` 是否随时间轴长度变化未取证。
- `data-director-node` / `data-director-node-id` 的来源未取证 ——
  本批只报「它们不属于字面量并集」这个事实。
- 「31k 行」是 `src/components/director/*.ts*` 的行数合计（含 7 个 `.ts` 工具模块），
  **不含** app 层接线。
- 导演台的**键盘/焦点围栏未测** —— 737/738 提过 `useDirectorFocusContainment`，
  本批只读了 `focusScope` / `focusState` 两个属性值，没测 Tab 序列。

## 与前批关系

- **741「一个对不上的数字自己就是线索」** —— 本批连续用上三次：
  ① 460 vs 446 差 14 ⟹ 查出跨文件重复；② 残差 223 而不是 196 ⟹ 查出
  **画布仍在 DOM 里**；③ `exportingSamples` 偏小 ⟹ 查出轮询去重导致样本数受节奏影响。
- **745「异步 UI 反馈有时效」+「『没变化』要分层归因」** ——
  本批把「分层归因」用在导出的 4.2 秒假否定上，是该条最贵的一次应用
  （**差点把一个真跑通的命令写成「没反应」**）。
- **746「穷举一个状态的全部读点」** —— 本批 748 的 C6 就是它的延伸：
  `data-director-export-status` 有 `idle` / `submitting` / `created` 三态，
  只读一个时点会漏掉整个 `exporting` 阶段。
- **741「普查数字要标口径」** —— 本批 460 / 446 / 447 三个数并排列出，
  并把「13 个跨文件属性名、其中一个在 3 个文件」作为判据的一部分。
- **741–747 全在画布** —— 本批首次进入导演台。33 个记账命令里仍有 14 个未跑过，
  其中 `createDirectorCapture` / `createDirectorAnimationExport` 两个导演台命令
  本批解决了一个（导出）、一个留到下一批（发送那一跳）。

## 验收器

`scripts/verify-liblib-batch748.py` — 静态扫 13 个组件求两个口径 + 2 处 `dataset.` 盲区
+ 打开导演台的 6 个标识符与 6 个区域 + 7 枚 rail 入口逐个点（累计属性集合）
+ 差集三类分类 + 导出轮询到终态（progress 只留与采样无关的性质）
+ 快门第一跳，两轮连跑归一化现场 id 后逐字段一致。
