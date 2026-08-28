# LibTV 快捷键运行语义 Crosswalk

## 1. 目的与审计边界

本文回答三个容易被混为一谈的问题：

1. 2026-08-25 的 LibTV 源站快捷键面板**宣称**支持什么；
2. 当前 clone 的 `KeyboardShortcutsDialog` **展示**什么；
3. 当前 clone 工作台在运行时**实际处理**什么。

审计基线：

| 对象 | 固定边界 |
|---|---|
| 源站帮助文案 | `docs/research/liblib-live-2026-08-25/panel-audit.json` 的 2026-08-25 登录态快照 |
| clone 代码 | commit `c2c7b46` |
| clone 帮助面板 | `src/components/KeyboardShortcutsDialog.tsx` |
| clone 全局监听器 | `src/app/page.tsx` |
| graph/history 副作用 | `src/store/canvasStore.ts` |

本轮是静态代码和既有证据审计，没有重新操作共享源站，也没有触发 graph mutation。源站帮助文案只能证明“当时可见”，不能证明快捷键在所有状态、平台和焦点上下文中都能执行。

## 2. 状态词汇

| 状态 | 含义 |
|---|---|
| `SOURCE_ADVERTISED` | 2026-08-25 源站帮助文案可见，但未在源站逐项执行 |
| `CLONE_HELP` | clone 帮助面板存在对应行 |
| `CLONE_HANDLER` | clone 普通 LibTV 工作台存在明确运行时处理 |
| `REACT_FLOW_GESTURE` | 能力由 React Flow 指针/滚轮机制承担，不等于键盘监听器 |
| `LOCAL_CONTEXT` | 只在特定编辑器、弹层或 Director 子工作区中成立 |
| `SOURCE_ONLY` | 源站宣称存在，clone 帮助和普通工作台处理均缺失 |
| `HELP_DRIFT` | clone 帮助行与实际处理条件或平台显示不完全一致 |
| `UNVERIFIED_SOURCE` | 需要新的可丢弃 fixture 才能确认源站运行语义 |

## 3. 创作命令三方对照

| 命令 | 源站快照 | clone 帮助 | clone 实际处理 | graph/history 副作用 | 结论 |
|---|---|---|---|---|---|
| 成组 | `G` | `G` | 无 Meta/Ctrl/Alt 时，`G` 调用 `groupSelectedNodes()` | 至少两个非 group 节点时创建 `storyboard-group`，重写子节点 `parentId`/相对坐标，选择 group，压入一次 history | `SOURCE_ADVERTISED` + `CLONE_HANDLER` |
| 合并分镜组 | `Option+G` | 无 | 未找到普通工作台 handler | 无 | `SOURCE_ONLY` + `UNVERIFIED_SOURCE`；不能用现有“成组”冒充分镜组合并 |
| 解组 | `Shift+G` | `Shift+G` | 无 Meta/Ctrl/Alt 时，`Shift+G` 调用 `ungroupSelectedNodes()` | 删除 group、恢复子节点世界坐标、选择 children，压入一次 history | `SOURCE_ADVERTISED` + `CLONE_HANDLER` |
| 连线 | `L` | 无 | 未找到 `L` handler；当前连接入口是 React Flow `<Handle>` 拖动 | 成功连接时由 `onConnect`/store 添加 edge 并记录 history | `SOURCE_ONLY`；现有 pointer gesture 不能证明 `L` 已复刻 |
| 复制节点和连线 | 文案为 `D`，原始快照未显示 Meta/Ctrl | `Command+D` | `Meta/Ctrl+D` 且存在选中节点时调用 `duplicateSelectedNodes()` | 复制选中子图及内部 edge，选择副本，压入一次 history | clone 行为存在，但 source modifier 仍是 `UNVERIFIED_SOURCE` |
| 生成 | `Enter` | 无 | 未找到普通工作台全局生成 handler | 无全局 graph transaction | `SOURCE_ONLY`；局部输入框的 Enter 不能等同于全局生成 |
| 新建节点 | `Tab` | `Tab` | `Tab` 调用 `toggleAddNodePanel()` | 只切换 overlay；选择具体条目后才创建节点 | `SOURCE_ADVERTISED` + `CLONE_HANDLER` |
| 节点复制 | `Option+拖动节点` | 无 | `onNodeDragStart`/`onNodeDragStop` 未读取 `altKey` | 普通拖动只移动节点并按一次 drag transaction 记录 history | `SOURCE_ONLY` |
| 创建副本 | `Option+拖动` | 无 | 未找到 Alt-drag clone 分支 | 无 | `SOURCE_ONLY`；与上一行在源站中的对象范围差异仍待 fixture 复核 |
| 删除 | `Delete`，位于“其他” | `Delete`，位于“创作” | `Delete` 或 `Backspace` 且有选择时调用 `removeSelectedNodes()`；React Flow 默认删除被禁用 | 删除选中节点、后代和相连 edge，清空选择，压入一次 history | 运行语义已实现；分组位置属于帮助信息架构差异 |

### 3.1 “复制节点和连线”的准确边界

clone 的 `duplicateSelectedNodes()` 不是简单复制卡片：它调用 `duplicateGraphSelection()`，复制选择闭包内的节点和内部 edge；单节点且不是 storyboard group 时还有单节点复制分支。源站快照只给出帮助文案，尚不足以确认源站对 group、父子节点、跨选择边和外连边的复制闭包。

后续实现权威是 [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)：`duplicate-selection`、`create-node-copy`、`paste-subgraph` 和 `option-drag-copy` 必须保持具名命令，不能继续由 `includeEdges` 布尔值隐式混用。当前单普通节点复制 incident edge 的分支只标为 `COMPATIBILITY_HOLD`；system clipboard 与 Option-drag 仍分别等待 runtime 和 disposable source fixture。

### 3.2 “连线 L”不能由 Handle 代偿

当前 React Flow 配置允许 `nodesConnectable`，真实 `<Handle>` 提供指针拖线。这证明 clone 有连接能力，但没有证明键盘 `L` 的起点选择、候选目标、取消和确认状态机。后续复刻 `L` 前必须先观察源站，而不是把帮助行直接接到 `addEdge()`。

## 4. 视口与工具命令三方对照

| 命令 | 源站快照 | clone 帮助 | clone 实际处理 | 状态/副作用 | 结论 |
|---|---|---|---|---|---|
| 放大 | 可见“放大”，文本快照无明确 keycap | `Command++` | `Meta/Ctrl` + `+` 或 `=`，每次 `+0.1`，限制在 `0.1..8` | 只改 React Flow viewport，不进入 graph history | clone 运行语义存在；source chord 未证实 |
| 缩小 | 可见“缩小”，文本快照无明确 keycap | `Command+-` | `Meta/Ctrl+-`，每次 `-0.1`，限制在 `0.1..8` | 只改 viewport | 同上 |
| 适应画布 | `0` | `Command+0` | `Meta/Ctrl+0` 调用 `fitView({ padding: 0.12 })` | 只改 viewport | `HELP_DRIFT`：source 快照未证明 modifier |
| 滚轮/触控板缩放 | 触控板、鼠标行可见 | 触控板；`Command`/`Control` + 鼠标 | React Flow wheel path；Batch 77 已验证普通 wheel 平移、修饰键 wheel 缩放 | React Flow gesture；真实物理触摸板未测，Chromium wheel/pinch 路径已核对 | `REACT_FLOW_GESTURE` + `SOURCE_RUNTIME_AUDIT` |
| Space 临时移动 | `Space` | `Space` | keydown 进入 temporary pan；keyup、窗口 blur、页面隐藏时复位 | 不切换持久工具，不进入 graph history | 已实现，并显式接管 React Flow 默认 Space pan |
| V | `V`，源站标签“移动” | `V`，clone 同样显示“移动” | 实际调用 `setCanvasTool("select")` | 切换到选择工具 | `HELP_DRIFT`：显示语义与 handler 名称相冲突，需源站复核 |
| H | `H`，抓手工具 | `H` | 调用 `setCanvasTool("pan")` | 切换持久 pan 工具 | 运行语义一致 |
| 整理画布 | `Option+Shift+F` | `Option+Shift+F` | `Alt+Shift+F` 调用 route-local `organize()` | 重排 nodes、清空选择、记录 graph history，并另存/应用 viewport | 已实现；graph 和 viewport 的恢复边界需与图事务目录联读 |
| 鼠标/触控板移动 | 两行可见 | 两行可见 | `panOnScroll` 开启；普通中键、持久 `H` 和临时 `Space` 左键均可平移 | React Flow gesture | Batch 77 已完成源站运行态行为核对；真实物理触摸板仍未直接测试 |

React Flow 的 `panActivationKeyCode={null}` 和 `deleteKeyCode={[]}` 很关键：默认 Space 激活与默认删除均被关闭，普通工作台由 `page.tsx` 统一接管。不能同时把 React Flow 默认行为和 page handler 记为两个能力。

## 5. 历史与退出命令

| 命令 | 源站快照 | clone 帮助 | clone 实际处理 | 结论 |
|---|---|---|---|---|
| 撤销 | `Z`，快照未证明 modifier | `Command+Z` | `Meta/Ctrl+Z` 调用 `undo()` | clone 存在；source modifier 待复核 |
| 重做 | `Shift+Z`，快照未证明 Meta/Ctrl | `Command+Shift+Z` | `Meta/Ctrl+Shift+Z` 调用 `redo()` | clone 存在；source modifier 待复核 |
| Windows 重做 | 源站快照无独立行 | `Ctrl+Y` | handler 实际接受 `Meta+Y` 或 `Ctrl+Y` | `HELP_DRIFT`：帮助写 Windows-only，但 handler 在 macOS 也接受 Command+Y |
| Escape | 源站面板无独立行 | 无 | 普通工作台清空选择并关闭顶层 overlays；Director active 时直接返回 | `CLONE_HANDLER`，但不是 source-advertised 快捷键 |

`undo()`/`redo()` 恢复的是当前 canvas 的 nodes/edges snapshot，并清空选择。它们不恢复 viewport、普通 overlay、局部编辑器内部 history 或 Director 独立 store。

## 6. 作用域与优先级

### 6.1 可编辑目标优先

普通工作台 handler 首先检查事件目标是否位于 `input`、`textarea` 或两种 `contenteditable`。命中后所有全局分支都跳过。这是防止输入文字时触发删除、成组、工具切换和撤销的首要 guard。

### 6.2 局部编辑器优先于普通 Escape

`VideoContinuationSelector`、`PictureEditPanel` 和 `SubtitleErasePanel` 使用 capture-phase `keydown`，在 Escape 时调用 `preventDefault()`、`stopImmediatePropagation()` 和自己的 `onCancel()`。因此 Escape 的有效优先级是：

```text
局部编辑器 capture handler
  -> 普通工作台 global handler
  -> React Flow / browser fallback
```

不能仅从 `page.tsx` 推断“Escape 总会清空选择并关闭全部面板”。

### 6.3 Native/local/graph undo 只能有一个当前 owner

Editable target guard 只能证明 page graph undo 不穿透输入框，不能证明自定义画布编辑器的 undo 已正确路由。`PictureEditPanel`、`SubtitleErasePanel` 等 local history surface 必须在 command context 中先返回 `HANDLED/CONSUMED`，否则同一 `Meta/Ctrl+Z` 可能既改变 local draft，又触发背景 graph snapshot。反过来，Text/input/contentEditable 应保留浏览器 native undo，不能被 custom editor 或 graph handler接管。

正式 precedence 为：native editable -> active custom editor local history -> foreground surface command -> ordinary graph history -> route fallback。一次 chord 只能由一个 owner 消费；local undo/redo 不改 graph/selection/viewport，accepted commit 关闭后 graph undo 才可恢复前一语义状态。完整 profile、fixture 和 `LIBTV-VR-022` 见 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)。

### 6.4 Director 是独立快捷键域

当 `activeDirectorNodeId` 存在时，普通 page dispatcher 对全部工作台快捷键提前返回；Batch 50 已对 Tab/Space/Delete/undo 的背景隔离形成 recorded runtime。Batch 62 又在普通 LibTV foreground surface 上补充 selection snapshot、editable/IME pass-through、command suspension、one-Escape 和 canvas focus fallback。`DirectorDesk`、`DirectorInspector`、`DirectorTimeline`、`DirectorViewport` 和 phone virtual-camera panel 仍有自己的键盘监听器。本文不把这些局部命令合入普通 LibTV 工作台；完整 selection/focus/listener 静态边界见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)，正式 node/edge/primary、surface policy、one-Escape 和 focus return 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)，Director 领域行为继续由 Batch 35-50 合同维护。

### 6.5 视口不是 graph history

普通缩放、fit view、滚轮和 pan 不进入 `canvasStore` graph history。`organize()` 是组合命令：node 重排进入 graph history，viewport 通过 route/UI store 单独记录。后续编写 verifier 时必须分开断言。

## 7. 当前高价值缺口

| 优先级 | 缺口 | 为什么高价值 | 下一步证据 |
|---|---|---|---|
| P1 | `V` 显示“移动”但实际切到 select | 用户会按帮助行得到相反工具语义 | 在可丢弃源站 fixture 观察 V/H 的 toolbar active state，再决定修文案还是 handler |
| P1 | `L`、`Enter`、`Option+drag`、`Option+G` source-only | 这些是高频创作与 storyboard 结构命令 | 分项记录触发前状态、焦点、selection、取消路径和 graph delta |
| P1 | duplicate 的 source modifier/闭包不明 | 错误复制父子节点或外连 edge 会破坏 graph | 用最小 2-node/1-edge fixture 比对单选、多选、group 和外连边 |
| P1 | foreground editor local/native/graph undo precedence 未统一 | 一个 chord 可能双消费，enabled Undo 也可能无 handler | 用 `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` 验证 Text/Picture/Subtitle/empty-mode，再等待 source disposable fixture |
| P2 | zoom/fit keycap 与 gesture 文案漂移 | 影响跨平台可发现性，但不阻塞核心画布 | 同时采集 macOS/Windows source DOM 与实际事件 |
| P2 | 帮助面板没有 row-level command ID | 文案和 handler 会继续独立漂移 | 获得编码授权后才评估 typed registry，不在研究阶段改代码 |
| P2 | 无 focused shortcut verifier | 现有 Batch 只覆盖部分生命周期或 graph 行为 | 未来按 command ID 验证 guard、side effect 和 no-op 条件 |

## 8. 后续实现闸门

在获得编码授权前，本 crosswalk 只作为审计和规划依据。若后续实施，顺序应为：

1. 在可丢弃源站 fixture 逐项复核 P1 source-only 命令；
2. 先定义命令 ID、平台 chord、上下文 guard、graph/viewport/UI 副作用和 no-op 条件；
3. 再决定是否引入 typed shortcut registry，让帮助面板和 handler 共享结构化定义；
4. 保留局部编辑器和 Director 的独立优先级，不把所有 listener 粗暴合并；
5. 用 focused verifier 同时验证执行结果和帮助文案，最后运行全量门禁。

相关文档：

- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)
- [`components/LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)
- [`components/KeyboardShortcutsDialog.spec.md`](components/KeyboardShortcutsDialog.spec.md)
- [`BEHAVIORS.md`](BEHAVIORS.md)
- [`liblib-canvas-batch3-2026-08-25/`](liblib-canvas-batch3-2026-08-25/README.md)
- [`liblib-canvas-batch4-2026-08-25/`](liblib-canvas-batch4-2026-08-25/README.md)
- [`liblib-canvas-batch6-2026-08-25/`](liblib-canvas-batch6-2026-08-25/README.md)
- [`liblib-canvas-batch7-2026-08-25/`](liblib-canvas-batch7-2026-08-25/README.md)
