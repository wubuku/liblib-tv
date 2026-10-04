# batch 744 — VideoNode 面板门控分层：16 个记账命令分 **A 档 8 / B 档 8**；`status === "ready"` 是 L2 硬门控

## 起点

743 测出两态按钮文案一致，写下「`status` 不是门控」。
本批去查这句话的**适用边界**——读 `VideoNode.tsx` 的渲染结构才发现，
这句话**对一半成立、对另一半不成立**：
`VideoProcessingToolbar` 整块被 `status === "ready"` 硬门控，
而它的回调里挂着另外 8 个记账命令。

全部读数来自 clone，**不碰源站**。

## 三层门控（源码）

```
L1  showSingleNodeEditor = selected && selectedNodeCount <= 1        VideoNode.tsx:120
L2  status === "ready" && !subtitleMode && activeTool !== "picture-edit"
      → <VideoProcessingToolbar …>                                   VideoNode.tsx:412-415
L3  activeTool === "generator" && status !== "pending"
      → <VideoGenerationPanel …> 与尝试列 data-video-attempts       VideoNode.tsx:658-659
    status === "ready" && activeTool === "continue"
      → <VideoContinuationSelector …>                               VideoNode.tsx:740
```

## 决定性读数

### ① 16 个记账命令分两档（逐个点名，附调用行 + store 实现行）

| 档 | 门控 | 命令（`VideoNode.tsx` 调用行 / `canvasStore.ts` 实现行） |
|---|---|---|
| **A**<br>两态都可达 | L3<br>`status !== "pending"` | `createFirstFrameReference` 677/1319 · `createFirstLastFrameReference` 679/1393 · `createLongVideoProcess` 730/2244 · `addNodeAtPosition` 714/1577（选特效） · `addEdge` 721/3620（选特效） · `destroyFirstFrameReference` 725/1544 · `clearVideoContinuation` 733/2974 · `updateNodeData` 125/3368（`setAttempt`） |
| **B**<br>只有 `status==="ready"` 可达 | L2<br>`status === "ready"` | `addDerivedNode` 201/1608（`createBreakdown`） · `createSubtitleErase` 227/1766 · `createAudioSplit` 257/1899 · `createPictureEdit` 396/2615 · `createSmartMatting` 372/2508 · `createDepthMotionCapture` 296/2143 · `createVideoFrameCapture` 304/2032 · `createVideoContinuation` 219/1663（「智能续写」`VideoProcessingToolbar.tsx:133`） |

**A 档 8 / B 档 8**。B 档全部经 `VideoProcessingToolbar` 的回调进入，
而那块 UI 在 `failed` 卡上**整块不渲染**。

### ② L2 门控实测：failed 卡上工具栏**一个元素都没有**

| | 工具栏（`aria-label="撤销视频处理"`，**document 级**） | 同上但**节点内**查询 | 尝试列 `data-video-attempt` |
|---|---|---|---|
| failed 卡 `v-UGQZzZOpbv` | **0** | 0 | 3 |
| ready 卡（新建） | **1** | **0** | 3 |

⚠ **工具栏的 DOM 不在 `.react-flow__node` 内**（`NodeToolbar` + portal），
节点级查询**两态都恒 0**。门控判定必须用 document 级——
这是 737/738 的 portal 教训在视频卡上的第三次复现。

### ③ failed 卡上 3 枚尝试芯片逐个点真按钮（每枚**重载页面**、基线独立为 `past=0`）

| 芯片 | 命令 | `past` | 节点 | 边 | 该卡 `data.attempt` |
|---|---|---|---|---|---|
| 首帧生成视频 | `createFirstFrameReference:1319` | 0 → **1** | 10 → 10 | 11 → 11 | `None` → **`"首帧生成视频"`** |
| 首尾帧生成视频 | `createFirstLastFrameReference:1393` | 0 → **1** | 10 → 10 | 11 → 11 | `None` → **`"首尾帧生成视频"`** |
| 5分钟超长视频 | `updateNodeData`（`setAttempt`） | 0 → **1** | 10 → 10 | 11 → 11 | `None` → **`"5分钟超长视频"`** |

三枚都记账、都不新建节点（种子的 failed 卡已有 image 入边 ⟹ 承 batch 255 的
「既有 image→video 边时仅记录 attempt、跳过图创建」）。

### ④ ready 卡上「智能续写」可点开

入口按钮命中并点击后，页面出现「续写」相关 UI 与 2 个时间输入控件
（`VideoContinuationSelector`）⟹ B 档里唯一的两段式命令**入口可达**。
第二段「选区间 + 确认」本批未执行。

## 与 743 的关系（743 那句话的边界被收窄）

- 743 的「`status` 不是门控」**读数对、理由过宽**：11 个芯片都在
  `VideoGenerationPanel` / 尝试列里，那两块只排除 `pending`。
  但同一组件里还有另一块被 `status === "ready"` 硬门控的 `VideoProcessingToolbar`。
- 743 读到的「工具栏 2 枚 `data-inert`（撤销/重做视频处理）只在 ready 出现」
  正是 L2 门控的表现；本批把它从**现象**升格为**源码 + 运行时双证的门控条件**。

## 探针返工六处（全部是我自己的错）

1. 裸匹配 `VideoProcessingToolbar` 先命中**顶部 import 行**（`:51`）⟹ 要匹配 JSX 标签 `<VideoProcessingToolbar`。
2. 单行匹配 `status === "ready" && !subtitleMode` **匹配不到**（源码跨两行）⟹ 改成匹配前半截。
3. store 实现行只匹配 `name:` ⟹ 先命中顶部 import 列表（`createFirstFrameReference` 读成 `:320` 而不是 `:1319`）；改成只认 `name: (`。
4. **又用了 `(?<![\w.$])name\s*\(`** ⟹ 把 `useCanvasStore.getState().cmd(` 这种正常调用又杀了
   （3 个命令读成「未找到调用行」）。**742 刚为同一件事踩过一次并写下规矩，这里重新引入了一次。**
5. 用 `data-video-toolbar-menu` 当工具栏存在性标记 ⟹ 那是 **`ToolbarMenu` 弹出菜单**的属性，菜单不开时恒 0，两态都读成「不存在」。
6. `page.evaluate(expr, a, b)` 传了两个参数（Playwright 只收一个）⟹ 打包成对象。

另有一处口径教训记在判据里：芯片必须**每枚重载页面**取独立基线
（第一版共用一页，`past` 累加成 1→2→3→4，每步仍 +1 但「独立基线」这句话不成立）。

## 判据（6/6）

| | 判据 | 读数 |
|---|---|---|
| C1 | 三层门控源码位置在位（L1 `:120` / L2 `:412`+`:415` / L3 `:658`+`:659`+`:740`） | 续写入口 `Toolbar:133` |
| C2 | 工具栏 document 级：failed **0** / ready **≥1**；节点内两态恒 **0**（portal） | `0 / 1`、`0 / 0` |
| C3 | 16 个命令 A 8 / B 8，每个都指得到调用行与实现行 | `missing: 无` |
| C4 | failed 卡 3 枚芯片逐个可点、逐个记账（**独立基线 `past` 0→1**） | 3/3 |
| C5 | ready 卡「智能续写」入口存在且可点 | `bodyHasContinue: true` |
| C6 | 743 那句的边界：L3 成立（两态各 3 枚芯片）、L2 不成立（工具栏只在 ready） | `attempts [3,3]` / `toolbarDoc [0,1]` |

## 不声称

- B 档 8 个命令里**只对「智能续写」的入口**做了实测；其余 7 个（去字幕 / 音频切分 /
  图片编辑 / 智能抠像 / 深度运动 / 抽帧 / 逐帧拉片）未逐个走完两段式确认。
- 不声称 A 档 8 个在 `ready` 态下都可用 —— 只验了 `failed` 态下 3 枚尝试芯片。
- 「续写」的第二段（选时间区间并确认 → `createVideoContinuation`）**未执行**。
- 不声称 `failed` 态**不该**有工具栏 —— 未取证；本批只报「读不到」。
- 多选态（`selectedNodeCount > 1` ⟹ `showSingleNodeEditor` 为 false）下 16 个命令**全部不可达**，
  本批未测那一格。

## 验收器

`scripts/verify-liblib-batch744.py` — 静态门控结构 + 4 组运行时读数
（两态工具栏存在性、3 枚芯片逐个点击、智能续写入口），两轮连跑逐字段一致。
