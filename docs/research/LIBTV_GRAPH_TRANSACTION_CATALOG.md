# LibTV Graph Transaction Catalog

## 1. 目的与基线

本文是普通 LibTV React Flow 工作台的图事务目录。它把用户动作、route 适配层、`canvasStore` action、nodes/edges 变化、selection 结果、history 边界和证据成熟度放在同一张地图中，供后续复刻、评审和 verifier 设计使用。

审计基线：

| 对象 | 固定边界 |
|---|---|
| clone 代码 | commit `7b746aa`；后续 `502b469` 仅增加快捷键文档，不改变 graph runtime |
| route owner | `src/app/page.tsx` |
| graph owner | `src/store/canvasStore.ts` |
| 通用 history 合同 | [`COMMAND_HISTORY.spec.md`](liblib-canvas-batch3-2026-08-25/COMMAND_HISTORY.spec.md) |
| 专项合同 | Batch 4-8、20、24、26-33、35、40 |

本文记录的是当前 clone 事实和既有源站证据的关系，不把 Zustand action 的存在反推为 LibTV 源站内部实现。Batch 合同中的模拟 task、静态 preview 和本地 metadata 也不代表真实后端协议。

## 2. 术语与成熟度

| 标记 | 含义 |
|---|---|
| `CLONE_INFRA` | clone 为 React Flow 编辑、history 或 project lifecycle 建立的基础设施 |
| `SOURCE_BACKED_SHAPE` | 入口、主要拓扑或状态由源站 DOM/bundle/运行证据支撑，但 clone 仍是前端原型 |
| `SOURCE_SHAPED_CLONE` | 使用源站可见形状和产品流校准，精确 transaction 或 placement 含 clone 决策 |
| `PRODUCT_FLOW_INFERENCE` | graph 表达来自产品流程推断，没有观察到源站精确 nodes/edges transaction |
| `CLONE_ONLY` | 当前仅是 clone 内部行为，不能作为源站事实 |

“原子”在本文中只表示一次用户提交调用一次 store `set` 并压入一个 graph snapshot。它不表示数据库事务、服务幂等、跨标签页一致性或持久化。

## 3. History 内核

### 3.1 存储模型

```text
historyByCanvas[canvasId] = {
  past: GraphSnapshot[],
  future: GraphSnapshot[]
}

GraphSnapshot = {
  nodes: Node[],
  edges: Edge[]
}
```

稳定规则：

- 每个 canvas 独立维护 history；
- `past` 最多 50 项；
- 新事务把命令前 graph 放入 `past`，并清空 `future`；
- `undo()` 恢复最后一个 `past`，把当前 graph 放到 `future`；
- `redo()` 恢复第一个 `future`，把当前 graph 放回 `past`；
- undo/redo 后 `selectedNodeIds=[]`、`selectedNodeId=null`；
- selection、viewport、overlay、局部编辑器草稿和 Director 独立 store 不属于 graph snapshot；
- history 只在内存中存在，刷新页面后丢失。

### 3.2 Snapshot 深度限制

`cloneGraphSnapshot()` 复制 node、`position`、`style` 和顶层 `data`，复制 edge 顶层对象；它不会深复制 `data` 内的数组、对象或媒体 runtime value。因此 history 正确性依赖后续 action 对嵌套 metadata 保持不可变更新。

这是当前实现约束，不是建议忽略的问题。后续若允许原地修改 marks、regions、process metadata 或其他 nested data，旧 snapshot 可能被一起污染。

### 3.3 不进入 graph history 的状态

| 状态 | Owner | 说明 |
|---|---|---|
| 单选/多选 | `canvasStore` selection fields | 普通选择不入栈；undo/redo 主动清空 |
| pan/zoom/fit view | canvas viewport + route/React Flow | 普通 viewport 变化不入栈 |
| overlay open/close | `uiStore` | 帮助、素材、Agent、参数面板等不入栈 |
| editor-local marks/regions | component state | 只有最终 submit 才写 graph；局部 undo/redo 与 graph undo/redo 分离 |
| Director scene/timeline | `directorStore` | 只有 capture/export 回画布时调用 `canvasStore` transaction |

## 4. Route 适配层

`page.tsx` 不是纯渲染器，它负责把 React Flow 的连续事件压缩为 store transaction。

| Route 入口 | Store 调用 | History 行为 | 关键边界 |
|---|---|---|---|
| `onNodesChange` | `setNodes(nextNodes)` | 默认不入栈 | selection change 被单独抽出；drag 中间帧和 measured changes 只更新 graph |
| `onNodeDragStart` | 无写入 | 保存拖动前 `GraphSnapshot` 和参与 node IDs | snapshot 是后续单事务锚点 |
| `onNodeDragStop` | `setNodes(currentNodes, {recordHistory:true, historySnapshot})` | 位置确实变化时只入栈一次 | 多选/group 以 React Flow 最终位置为准，不重新计算鼠标 delta |
| `onEdgesChange` | `setEdges(applyEdgeChanges(...))` | 默认不入栈 | 当前主要承接 React Flow 内部 edge change；不能拿它实现用户删除命令 |
| `onConnect` | `addEdge(edge)` | 入栈一次 | 由真实 `<Handle>` 指针连接触发 |
| `delete-edge` custom event | `removeEdge(id)` | 入栈一次 | `DeletableEdge` 的显式删除入口 |
| `organize()` | `setNodes(organized,{recordHistory:true})` + viewport updates | nodes 入 graph history，viewport 单独保存 | 一次命令同时跨 graph 与 viewport 两个状态域 |
| `restoreOrganize()` | `setNodes(previous,{recordHistory:true})` + viewport restore | 恢复动作自身再产生一个 graph history step | 不是通用 `undo()`；route-local snapshot 只保存最近一次 organize |

React Flow 的持续 position 更新先写 store、drag stop 再用显式 `historySnapshot` 压入“拖动前”状态。这解释了为什么 `setNodes()` 默认不能自动记录 history：否则一次拖动会产生大量中间快照。

## 5. Project 与 Canvas 生命周期

这些 action 会改变 canvas 集合或整张 graph，但不属于当前 graph undo/redo。

| Action | 结果 | History 边界 | 成熟度 |
|---|---|---|---|
| `setProjectName` | trim 后更新项目名；空字符串 no-op | 不入栈 | `CLONE_INFRA` |
| `addCanvas` | 创建空 canvas、切换 active、清空 selection | 新 canvas 没有 graph history | `CLONE_INFRA` |
| `removeCanvas` | 至少保留一个 canvas；删除目标及其 history；必要时切换 active | 不可由 graph undo 恢复 | `CLONE_INFRA` |
| `renameCanvas` | 更新 canvas name | 不入栈 | `CLONE_INFRA` |
| `setActiveCanvas` | 切换 active 并清空 selection | 各 canvas history 保留 | `CLONE_INFRA` |
| `duplicateCanvas` | 深度有限地复制 nodes/edges、重映射 node/parent/edge IDs，切换到副本 | 新 canvas history 为空；不继承 source history | `CLONE_INFRA` |

项目/画布删除、复制与 graph history 是两个命令域。后续若复刻源站项目级 undo，不应直接扩张 `GraphSnapshot`。

## 6. 通用 Graph Actions

| Action | No-op guard | Graph delta | Selection 结果 | History | 主要入口/风险 |
|---|---|---|---|---|---|
| `addNode` | 无 active canvas | 计算 viewport center 后委托 `addNodeAtPosition` | 新节点 | 1 step | Add Node、Character Library 等；`CLONE_INFRA` |
| `addNodeAtPosition` | 无 active canvas | `+1 node` | 新节点 | 1 step | 当前普通 UI 未发现直接调用；保留为坐标型基础 action |
| `addDerivedNode` | source 不存在 | `+1 node +1 direct edge`，默认放 source 右侧 | target | 1 step | Panorama、逐帧拉片及部分图片动作；通用性过强，见第 9 节 |
| `updateNodeData` | node 不存在 | merge 顶层 `data` | 不改变 | 1 step | Text/Image/ShotBreakdown；没有 equality guard，等值更新也会污染 history |
| `setNodes` | 无 active canvas | 替换全部 nodes | 不改变 | 默认 0；显式 option 才记录 | route adapter 专用低层 API，不应直接当用户命令 |
| `setEdges` | 无 active canvas | 替换全部 edges | 不改变 | 默认 0；显式 option 才记录 | 同上 |
| `addEdge` | 只检查 active canvas | `+1 edge` | 不改变 | 1 step | Handle connect；没有 endpoint、重复边或 self-loop guard |
| `removeEdge` | edge 不存在 | `-1 edge` | 不改变 | 1 step | DeletableEdge custom event |
| `removeNode` | node 不存在 | 删除 node、全部后代和所有相连 edge | 从 selection 移除被删 IDs | 1 step | 普通 LibTV UI 当前未发现直接 caller |
| `removeSelectedNodes` | selection 为空或无有效 node | 删除选择、全部后代和相连 edge | 清空 | 1 step | Delete/Backspace |
| `groupSelectedNodes` | 少于 2 个非 group 节点 | `+1 storyboard-group`，选中节点改为 children 与相对坐标 | group | 1 step | `G`；不等同于源站 `Option+G` 合并分镜组 |
| `ungroupSelectedNodes` | 找不到 group 或无 children | `-1 group`，children 恢复世界坐标 | children | 1 step | `Shift+G` |
| `duplicateNode` | source 不存在 | `+1 node`；默认复制所有 incident edges，并把一端换成副本 | 副本 | 1 step | 当前普通 LibTV UI 未发现 caller；外连边语义与 multi-copy 不同 |
| `duplicateSelectedNodes` | 无有效选择 | 复制选择闭包、group descendants 和相应 edges | 用户请求节点的副本 | 1 step | `Meta/Ctrl+D`；单个非 group 复制 incident edges，多选/group 只复制内部 edges |
| `undo` / `redo` | 对应 stack 为空 | 整体替换当前 canvas nodes/edges | 清空 | stack move | 快捷键与 history 命令 |

## 7. 专项创作事务

### 7.1 单/双输出事务

| Action | 调用 owner | Guard / normalize | Graph delta | Selection | 成熟度与合同 |
|---|---|---|---|---|---|
| `createVideoContinuation` | `VideoNode` continuation selector | source 必须存在；范围 clamp 到 `4..30s` | `+1 empty video +1 source edge`，保存 continuation metadata | target | `SOURCE_BACKED_SHAPE`；[Batch 26](liblib-canvas-batch26-2026-08-25/README.md) |
| `clearVideoContinuation` | continuation target `VideoNode` | target 必须含有效 metadata | 保留 target，删除 `continuation` data 与声明 edge | 不改变 | `SOURCE_SHAPED_CLONE`；create/clear 分别 1 step |
| `createSubtitleErase` | `VideoNode` + `SubtitleErasePanel` | region 模式必须至少一个 region；坐标 clamp 到 `0..1` | `+1 pending video +1 source edge` | target | `SOURCE_BACKED_SHAPE`；[Batch 27](liblib-canvas-batch27-2026-08-25/README.md) |
| `createAudioSplit` | `VideoNode` processing toolbar | source 必须存在 | `+1 audio +1 silent video +2 source edges` | silent video | `SOURCE_BACKED_SHAPE`；[Batch 28](liblib-canvas-batch28-2026-08-25/README.md) |
| `createVideoFrameCapture` | `VideoNode` toolbar / player camera | last frame 要求 duration > 0；time clamp | `+1 image +1 source edge`，重复结果向下避让 | source | `SOURCE_BACKED_SHAPE`；[Batch 29](liblib-canvas-batch29-2026-08-25/FRAME_CAPTURE_WORKFLOW.spec.md) |
| `createSmartMatting` | `VideoNode` + `SmartMattingPanel` | source 必须存在 | `+1 pending video +1 source edge`，重复结果避让 | source | `SOURCE_BACKED_SHAPE`；[Batch 30](liblib-canvas-batch30-2026-08-25/README.md) |
| `createPictureEdit` | `VideoNode` + `PictureEditPanel` | 至少一个 mark；坐标/points clamp | `+1 pending video +1 source edge`，保存 mode/marks | source | `SOURCE_BACKED_SHAPE`；[Batch 31](liblib-canvas-batch31-2026-08-26/PICTURE_EDIT_WORKFLOW.spec.md) |
| `createDepthMotionCapture` | `VideoNode` depth panel | source 必须存在；非法 duration 回退 source duration | `+1 pending video +1 source edge` | source | `SOURCE_SHAPED_CLONE`；[Batch 32](liblib-canvas-batch32-2026-08-26/DEPTH_MOTION_WORKFLOW.spec.md) |
| `createDirectorCapture` | `DirectorDesk` | source 与非空 PNG data URL | `+1 image +1 director source edge`，保存 camera/ratio/capture metadata | target | `SOURCE_SHAPED_CLONE`；[Batch 35](liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md) |
| `createDirectorAnimationExport` | `DirectorDesk` | source、video URL、`sizeBytes>0` | `+1 ready video +1 director source edge` | target | `SOURCE_SHAPED_CLONE`；浏览器 WebM 是 clone 边界，[Batch 40](liblib-canvas-batch40-2026-08-26/DIRECTOR_ANIMATION_EXPORT.spec.md) |

所有表中 action 在成功时只压入一个 history snapshot。`pending`/`ready` 是本地前端状态，不证明真实任务已经创建、上传、计费或完成。

### 7.2 多节点过程事务

| Action | Guard | Graph delta | Selection | 原子性 | 成熟度与合同 |
|---|---|---|---|---|---|
| `completeShotBreakdown` | source 存在；尚无任何 result；至少一个启用 dimension | source 改 `complete`；按 dimension 创建 result nodes 与 direct edges；默认 5 nodes/5 edges | 第一个 result | 整批 1 step | `SOURCE_SHAPED_CLONE`；[Batch 24](liblib-canvas-batch24-2026-08-25/SHOT_BREAKDOWN_WORKFLOW.spec.md) |
| `createLongVideoProcess` | source 存在；参数 normalize | `+12 long-video-process nodes +22 edges`；3 material、3 shot、4 candidate、assembly、final | source | 整批 1 step | `PRODUCT_FLOW_INFERENCE`；[Batch 33](liblib-canvas-batch33-2026-08-26/LONG_VIDEO_PROCESS_GRAPH.spec.md) |

长视频的 12/22 精确拓扑是 screenshot-shaped clone calibration，不是 LibTV 数据协议。Shot breakdown 的“已有任一 result 即整体 no-op”能防止重复生成，但也意味着手工删掉部分 result 后不能补齐缺项；这是当前幂等近似。

## 8. Selection 是事务输出，不是 History 输入

不同 action 的 selection 结果是产品流程的一部分：

| 策略 | Actions | 意图 |
|---|---|---|
| 选择新 target | add node/derived、continuation、subtitle、audio split 的 silent video、Director capture/export | 立即进入结果节点或下一阶段编辑 |
| 保留 source | frame capture、smart matting、picture edit、depth motion、long-video process | 允许连续触发、保留 source toolbar 或参数入口 |
| 选择聚合结果 | group、ungroup、shot breakdown | 明确结构命令的新焦点 |
| 不改变 | edge add/remove、data update、clear continuation | 避免隐式焦点迁移 |
| 清空 | remove selected、undo、redo | 避免 selection 引用已消失 graph entity |

因为 selection 不进入 snapshot，redo 不会恢复事务完成时的 target/source selection。focused verifier 应分别断言“提交后的 selection”和“undo/redo 后清空”，不能假设 redo 回到原焦点。

## 9. 已知风险与停止条件

| 风险 | 当前事实 | 后续规则 |
|---|---|---|
| `addDerivedNode` 语义过宽 | 多数旧图片 toolbar action 仍被压成 `+node +edge` | 预览、标注、元素编辑、旋转、图层分离必须先按 UI/task/graph 分类；见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md) |
| 低层 setter 默认无 history | `setNodes/setEdges` 不传 option 就替换 graph 且不入栈 | 只用于连续 React Flow 同步；用户命令必须显式定义 snapshot 边界 |
| `updateNodeData` 无 equality guard | 等值 merge 也会清空 redo 并新增 past | 后续高频编辑先做语义 diff 或在 commit/blur 时调用 |
| Snapshot 只浅复制 nested data | 嵌套对象原地 mutation 会污染旧 history | 所有 graph metadata 使用 immutable replacement；引入可变结构前补测试 |
| `addEdge` 不校验 | 可加入 duplicate、dangling 或 self edge | 连接约束应在 domain/route 明确，不依赖 store 自动修复 |
| 两套 duplicate 语义 | `duplicateNode` 默认复制 incident edges；selection 复制对 multi/group 只保留 internal edges | 新入口统一走已验证的 selection contract，除非明确需要 external-edge copy |
| canvas lifecycle 不可撤销 | remove/duplicate canvas 不进 graph history | 不把 project-level undo 偷塞进当前 `historyByCanvas` |
| 专项 action 重复手写 | placement、metadata、edge、selection、history 模板高度重复 | 只有在新增能力前先定义共同不变量且能降低真实错误时才抽象；不为形式统一抹掉不同 selection/guard |
| backend 仍不存在 | pending/ready、静态图和 blob URL 都是本地 prototype | 文档和 UI 不宣称真实 Provider、任务轮询、持久化或计费 |

## 10. `LIBTV-PAR-008` Invariant And Compatibility Design

本节将 Open Canvas 的 validation/DAG/subgraph 方法转成 LibTV 的评审问题，不把上游规则直接升级为当前产品决定。分类含义：

| 分类 | 含义 |
|---|---|
| `REQUIRED_CORRECTNESS` | 不依赖源站产品选择也必须保持的数据一致性 |
| `CURRENT_CLONE_FACT` | 当前实现已存在的语义，变更前需兼容评估 |
| `SOURCE_DECISION_REQUIRED` | 需要 LibTV 源站证据或明确 clone-only 产品决定 |
| `PROTOTYPE_BOUNDARY` | 当前可记录，但不应伪装成后端/协作保证 |

### 10.1 Invariant register

| ID | Invariant / question | Classification | Current evidence | Decision before coding |
|---|---|---|---|---|
| `LIBTV-GI-001` | node ID 在同一 canvas 内非空且唯一 | `REQUIRED_CORRECTNESS` | store actions and React Flow identity depend on it | validation must reject or normalize invalid fixture/import before runtime |
| `LIBTV-GI-002` | edge ID 在同一 canvas 内唯一 | `REQUIRED_CORRECTNESS` | edge removal/rendering use ID | define collision handling; never silently overwrite another edge |
| `LIBTV-GI-003` | edge source/target point to existing nodes | `REQUIRED_CORRECTNESS` | dangling edges cannot render a coherent transaction | define add/import/copy failure policy and no partial mutation |
| `LIBTV-GI-004` | exact duplicate edge identity includes source/target/handles | `SOURCE_DECISION_REQUIRED` | 2026-08-27 LibTV bundle pair guard rejects same or reverse node pair without comparing handles on the normal connection path | treat same-node-pair parallel handles as statically blocked in that path; confirm store/import/batch/sync coverage before clone decision |
| `LIBTV-GI-005` | self-loop is accepted or rejected | `SOURCE_DECISION_REQUIRED` | 2026-08-27 programmatic pair helper rejects equal IDs; ordinary non-Reference source reaches DFS self-loop guard | preserve Reference exception as unknown; confirm real drag cleanup and history before clone decision |
| `LIBTV-GI-006` | directed cycle is accepted or rejected | `SOURCE_DECISION_REQUIRED` | 2026-08-27 LibTV bundle adds candidate edge to adjacency and runs recursive DFS for ordinary connection path | confirm invalid feedback, connection-line cleanup and all entry points before clone decision |
| `LIBTV-GI-007` | source/target Handle and node-type compatibility | `SOURCE_DECISION_REQUIRED` | 2026-08-27 both Handle sides may start; target-start is direction-normalized; action/type/model/capacity validator returns `allowed` and optional `switchToModel` | preserve source Handle affordance; complete context matrix and UI/validator equivalence before clone decision |
| `LIBTV-GI-008` | parent/group references resolve and do not create orphan descendants | `REQUIRED_CORRECTNESS` | group/delete/duplicate actions traverse descendants | define import/copy/delete closure and invalid-parent handling |
| `LIBTV-GI-009` | selected IDs are a subset of current nodes after transaction | `REQUIRED_CORRECTNESS` | delete/undo/redo already clear or rewrite selection | every command declares selection output; stale selection is not tolerated |
| `LIBTV-GI-010` | one user command produces its declared history step count | `CURRENT_CLONE_FACT` | graph actions target one snapshot; route drag compresses many frames | no-op/equality and multi-node actions need exact compatibility cases |
| `LIBTV-GI-011` | graph snapshot metadata is not mutated through shared nested references | `REQUIRED_CORRECTNESS` | current snapshot is only shallow for nested `data` | document/snapshot deep-isolation contract complete；runtime missing |
| `LIBTV-GI-012` | graph history is in-memory and excludes viewport/UI/save state | `PROTOTYPE_BOUNDARY` | current `historyByCanvas` contract | do not infer persistence, collaboration or project-level undo |
| `LIBTV-GI-013` | every runtime node type/dataVersion and identity-bearing field has one registry rule | `REQUIRED_CORRECTNESS` | 11-type static audit and node-data contract complete；runtime uses generic Node/Record | unknown type/version/field blocks codec/operation before mutation |
| `LIBTV-GI-014` | owned node/edge metadata refs resolve or use an explicit external provenance mode | `REQUIRED_CORRECTNESS` | sourceNodeId/edgeId exist in derived metadata；continuation cleanup dereferences edgeId | map both refs, apply declared detach recipe, or reject；never retain stale edge ownership |
| `LIBTV-GI-015` | shot reciprocal refs and long-video process cohort remain internally consistent | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | resultNodeIds/sourceBreakdownId and shared processId bypass parent closure | exact copy validates/maps full aggregate；delete cascade/detach remains product decision |
| `LIBTV-GI-016` | accepted delete leaves no stale structural、owned data or aggregate relation | `REQUIRED_CORRECTNESS` | current node/selection delete repairs descendants/endpoints only | plan inverse refs and aggregate impact before one mutation；unresolved policy returns unknown |
| `LIBTV-GI-017` | graph delete reports node-bound UI invalidation and resource impact without folding them into graph history | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | uiStore owners and data/blob locators have separate lifetimes | route applies UI cleanup；media bytes/workspace/run destruction needs explicit owner |
| `LIBTV-GI-018` | every graph write ingress has one declared T0-T5 authority | `REQUIRED_CORRECTNESS` | addEdge is protected；derived/setter/restore paths are heterogeneous | no unclassified direct graph mutation |
| `LIBTV-GI-019` | React Flow transport cannot add/delete/replace semantic entities through generic apply/set | `REQUIRED_CORRECTNESS` | current node/edge changes flow to public whole-array setters | whitelist transport fields；route semantic changes to commands |
| `LIBTV-GI-020` | multi-entity command validates complete final draft before one commit | `REQUIRED_CORRECTNESS` | derived/process/shot creators append direct arrays | reject/unknown is zero-partial；accepted command is one history step |
| `LIBTV-GI-021` | history/document restore validates schema/invariants before atomic swap | `REQUIRED_CORRECTNESS` | undo/redo directly restore shallow snapshot arrays | invalid restore keeps graph and history cursor unchanged |
| `LIBTV-GI-022` | remote/server patch declares revision/base identity and field ownership | `FUTURE_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | ordinary remote ingress absent | stale/conflicting patch cannot silently overwrite graph/user fields |
| `LIBTV-GI-023` | every graph-producing completion carries operation/run/result identity | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | current timers call graph creators directly | no anonymous delayed graph write |
| `LIBTV-GI-024` | completion compares canvas/source/type/media-version/current owner before planning | `REQUIRED_CORRECTNESS` | current delayed actions mostly check source existence only | stale/invalid returns stable zero-mutation disposition |
| `LIBTV-GI-025` | async patch writes only operation-registered fields | `REQUIRED_CORRECTNESS` | no remote patch；generic data writer exists | never overwrite graph identity or unrelated current draft |
| `LIBTV-GI-026` | duplicate/out-of-order completion is idempotent | `REQUIRED_CORRECTNESS` | no result/version ingress | no duplicate node/edge/media/history/selection effect |
| `LIBTV-GI-027` | accepted result delta uses one validated full-draft command | `REQUIRED_CORRECTNESS` | delayed creators append precomputed graph directly | existing GI/GC validation before one commit |
| `LIBTV-GI-028` | component unmount and accepted operation lifecycle are separate | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | current timer cleanup semantics differ by surface | accepted operation remains observable or explicitly canceled |
| `LIBTV-GI-029` | async completion does not steal unrelated selection/surface | `REQUIRED_CORRECTNESS` | several delayed creators rewrite global selection | default preserve or declared contextual transition |
| `LIBTV-GI-030` | async resource ownership transfers or releases exactly once | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | Director has partial blob failure cleanup | stale/reject/delete/commit failure have deterministic release |
| `LIBTV-GI-031` | every React Flow change batch is exhaustively classified before any owner mutation | `REQUIRED_CORRECTNESS` | current clone splits selection then generically applies the remainder | unknown/semantic/malformed batch rejects or reroutes before partial effect |
| `LIBTV-GI-032` | T1 accepts only existing-node finite position and passive measurement | `REQUIRED_CORRECTNESS` | exact 12.11.1 union includes semantic variants | selection is T0；edge has no non-selection T1 variant；attribute resize is T2 |
| `LIBTV-GI-033` | node/edge add/remove/replace and reconnect use named semantic authority | `REQUIRED_CORRECTNESS` | current generic callbacks can bypass named connect/delete | no semantic identity/relation mutation through framework reducer |
| `LIBTV-GI-034` | framework reducer base is current active-canvas store state | `REQUIRED_CORRECTNESS` | current edge callback uses render-closure array | stale callback cannot overwrite a later graph command or another canvas |
| `LIBTV-GI-035` | selection has one validated active-session authority separate from semantic graph | `REQUIRED_CORRECTNESS` | node selection is projected；edge selection remains on edge objects | node/edge/primary snapshot is normalized against the active canvas；no selection in portable document/copy/semantic history |
| `LIBTV-GI-036` | passive measurement and explicit resize have different history/authority | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | no current NodeResizer/expandParent path found | measurement zero history；future source-authorized resize one named command |
| `LIBTV-GI-037` | React Flow runtime fields are sanitized at graph boundaries | `REQUIRED_CORRECTNESS` | measured/dragging/resizing/edge selected may enter arrays | codec/copy/history/hash explicitly project declared semantic fields |
| `LIBTV-GI-038` | activeCanvasId resolves to exactly one existing canvas | `REQUIRED_CORRECTNESS` | current setter accepts arbitrary ID | unknown target reject/no-op；never blank invalid active owner |
| `LIBTV-GI-039` | canvas IDs are unique and lifecycle allocation is zero-partial | `REQUIRED_CORRECTNESS` | module counter + timestamp/random copy suffix | create/duplicate plan validates identity before registry mutation |
| `LIBTV-GI-040` | graph、viewport and history remain keyed to one canvas | `REQUIRED_CORRECTNESS` | CanvasData + historyByCanvas partially implement | switch preserves source/target exact；delete removes target owner |
| `LIBTV-GI-041` | selection is active-session state and subset of active graph | `REQUIRED_CORRECTNESS` / `CURRENT_CLONE_FACT` | create/switch/duplicate/active delete clear | no inactive node selection or history leakage |
| `LIBTV-GI-042` | organize/drag/connection/viewport transaction carries canvas owner/generation | `REQUIRED_CORRECTNESS` | route refs/state are not canvas-keyed | old callback cannot commit after switch |
| `LIBTV-GI-043` | node-bound UI owner cannot cross canvas | `REQUIRED_CORRECTNESS` | Batch 58 covers preview/annotate/element/Director | every future surface enters reconciliation manifest |
| `LIBTV-GI-044` | canvas lifecycle remains outside graph undo | `CURRENT_CLONE_FACT` / `SOURCE_DECISION_REQUIRED` | current per-canvas history excludes CRUD/viewport | project undo is a separate future contract |
| `LIBTV-GI-045` | delayed graph write carries declared canvas identity | `REQUIRED_CORRECTNESS` | current component actions often late-read active canvas | switch does not retarget timer/promise/poll/export result |
| `LIBTV-GI-046` | duplicate/delete external operation/resource impact is explicit | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | current graph-only lifecycle has no ledger | map/reset/detach/retain/release/unknown exact |
| `LIBTV-GI-047` | target canvas viewport is switch restore authority | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | demo canvas responsive effect overwrites stored viewport | seed preset cannot silently replace user-owned viewport |
| `LIBTV-GI-048` | async local convergence checks current canvas/generation | `REQUIRED_CORRECTNESS` / `PROTOTYPE_BOUNDARY` | Open Canvas request URL is explicit but finishSave global | old durable result cannot rewrite new in-memory owner |
| `LIBTV-GI-049` | typed command outcome exists before presentation projection | `REQUIRED_CORRECTNESS` | current clone mixes reason unions、strings、booleans and timers | UI never infers disposition from string/exception presence |
| `LIBTV-GI-050` | reason code/args are separate from localized/source copy | `REQUIRED_CORRECTNESS` | connection reasons positive；Open Canvas literal message lookup negative | branching/verifier/retry never depend on display text |
| `LIBTV-GI-051` | rejected/noop/stale/unknown outcome is zero-history by default | `REQUIRED_CORRECTNESS` | multiple command contracts already require zero mutation | feedback cannot become hidden graph/history residue |
| `LIBTV-GI-052` | presentation feedback is outside graph history/document | `REQUIRED_CORRECTNESS` | current local states mostly separate | undo/redo never replays toast、timer、focus or local prototype status |
| `LIBTV-GI-053` | one outcome has one primary persistent visual owner | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | Open Canvas node error + toast demonstrates layered need and duplication risk | secondary announcement cannot become competing state authority |
| `LIBTV-GI-054` | durable failure/conflict remains visible and recoverable | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | Director/Open Canvas persistent surfaces positive | timeout-only feedback cannot carry required recovery |
| `LIBTV-GI-055` | stale result cannot announce current success | `REQUIRED_CORRECTNESS` | async/canvas lifecycle owner rules | no selection、toast or status theft across owner |
| `LIBTV-GI-056` | prototype feedback states unavailable/local preview honestly | `PROTOTYPE_BOUNDARY` | current Share/Agent/AddNode use explicit local copy | no fake remote run、progress、credits or completion |
| `LIBTV-GI-057` | every feedback projection has deterministic clear/retry/dedupe lifecycle | `REQUIRED_CORRECTNESS` | current timer/string policies are component-local | no accidental cleanup by rerender/unrelated action |
| `LIBTV-GI-058` | LibTV and FrameOS feedback owners remain route-isolated | `REQUIRED_CORRECTNESS` | stores/routes are independent；FrameOS has its own toast | no route mode or cross-route queue residue |
| `LIBTV-GI-059` | every spatial point at a planning/conversion boundary has one declared coordinate domain | `REQUIRED_CORRECTNESS` | current plain `{x,y}` spans client/flow/node/media meanings | no implicit client/host/flow/node/media conversion |
| `LIBTV-GI-060` | client/local conversion uses the current actual React Flow host | `REQUIRED_CORRECTNESS` | default add currently derives browser window center | panel/compact layout cannot shift graph placement away from visible host intent |
| `LIBTV-GI-061` | accepted viewport/coordinate values are finite and owner-valid | `REQUIRED_CORRECTNESS` | current viewport setter is permissive | invalid/stale value leaves graph/selection/history/viewport unchanged |
| `LIBTV-GI-062` | live viewport is current projection authority；stable viewport commits once at operation end | `REQUIRED_CORRECTNESS` | current page/store update on every callback without explicit phase | overlays/conversion use one live frame；switch restore uses one stable endpoint |
| `LIBTV-GI-063` | bootstrap viewport never overwrites user-owned stable viewport | `REQUIRED_CORRECTNESS` | demo responsive effect can reapply preset | breakpoint/layout change uses declared resize reconciliation |
| `LIBTV-GI-064` | screen surface clamp/flip cannot mutate captured graph flow anchor | `REQUIRED_CORRECTNESS` | Open Canvas dual anchor is positive evidence | future menu placement and current overlay geometry keep domains separate |
| `LIBTV-GI-065` | viewport、host frame and temporary gesture state stay outside semantic graph history | `REQUIRED_CORRECTNESS` / `CURRENT_CLONE_FACT` | current graph history excludes viewport | pan/zoom/resize/cancel adds zero graph snapshots |
| `LIBTV-GI-066` | every gesture/placement carries current canvas generation and delayed local point also carries host epoch | `REQUIRED_CORRECTNESS` | organize/drag/connection/viewport transients are unkeyed | stale completion cannot retarget active canvas or new host |
| `LIBTV-GI-067` | one named placement command has one declared anchor/strategy and exact graph/selection/history result | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | add/derived/duplicate/organize use different current rules | no generic “create node somewhere” policy；source-specific entries remain gated |
| `LIBTV-GI-068` | default add clone correctness floor is actual-host center with declared node dimensions | `REQUIRED_CORRECTNESS` / `SOURCE_DECISION_REQUIRED` | current store uses browser dimensions | exact source anchor remains open；window center is not accepted fallback |
| `LIBTV-GI-069` | overlay inputs belong to one current host/viewport/node frame | `REQUIRED_CORRECTNESS` | source-shaped formulas and measured/live islands exist | no stable/live or old/new host mixing；LibTV visual formula remains separate authority |
| `LIBTV-GI-070` | FrameOS graph viewport、ordinary LibTV viewport and Director 3D viewport remain domain-isolated | `REQUIRED_CORRECTNESS` | route/store domains are separate | no shared route mode、gesture session or transform state |
| `LIBTV-GI-071` | every ingress carries immutable intent/attempt/cohort/route/canvas/generation and target/source identity | `REQUIRED_CORRECTNESS` | current media paths use component-local or loosely typed values | retry、replace、switch and late completion cannot retarget current owner |
| `LIBTV-GI-072` | `File`、`Blob` and object URL never enter semantic graph history or portable document | `REQUIRED_CORRECTNESS` | Shot/Director local locators can reach runtime data | nonportable bytes remain operation/lease scoped until materialized or released |
| `LIBTV-GI-073` | one canonical media classifier feeds client convenience validation and materializer trust-boundary validation | `REQUIRED_CORRECTNESS` | Open Canvas accept/probe/server family drift is a counterexample | same payload cannot be accepted by one stage and silently reclassified by another |
| `LIBTV-GI-074` | metadata probe and preview URL are explicit leases with exact-once create/transfer/release | `REQUIRED_CORRECTNESS` | current component object URL has no common ledger | failure、cancel、retry、replace、delete and unmount have deterministic cleanup |
| `LIBTV-GI-075` | stable asset identity、generated-history item and node media reference remain distinct | `REQUIRED_CORRECTNESS` / `SOURCE_FACT` | source upload/history/material/asset surfaces are separate | attach、register、copy、replace and delete cannot collapse into URL equality |
| `LIBTV-GI-076` | validation、probe、materialization and freshness complete before semantic graph projection plan is accepted | `REQUIRED_CORRECTNESS` | Open Canvas placeholder-first and clone ready-before-durability are counterexamples | provisional UI may exist；graph mutation requires a full owner-valid plan |
| `LIBTV-GI-077` | provisional ingress UI adds zero semantic graph snapshots and is excluded from document/clipboard | `REQUIRED_CORRECTNESS` | current Add Resource mock and source progress behavior are incomplete | progress/errors/cancel can update operation state without polluting undo/history |
| `LIBTV-GI-078` | one multi-item cohort preserves original order and commits accepted successes in one declared graph/history transaction | `REQUIRED_CORRECTNESS` | Open Canvas sequential partial mutation is a counterexample | completion order cannot alter node order；failure policy is explicit and atomic |
| `LIBTV-GI-079` | node-bound media replacement preserves last-known-good media until current replacement commit | `REQUIRED_CORRECTNESS` | Shot/Image replace semantics are not centralized | invalid/failed/canceled/stale replacement cannot blank or downgrade current node |
| `LIBTV-GI-080` | invalid、noop、stale、duplicate and canceled media completion leaves graph/selection/history/current success feedback unchanged | `REQUIRED_CORRECTNESS` | common async ingress runtime is missing | no late residue、false success or redo truncation |
| `LIBTV-GI-081` | every resource ownership transfer has exactly one destination owner；every terminal non-transfer releases exactly once | `REQUIRED_CORRECTNESS` | clone object URLs/data/blob paths lack common owner | no leak、double revoke or use-after-revoke |
| `LIBTV-GI-082` | resource release requires zero reachability across graph、history、clipboard、editor/preview、operation、asset registry and portable export owner | `REQUIRED_CORRECTNESS` | graph-only delete is insufficient | undo/copy/open editor/reusable asset remain valid after current node deletion |
| `LIBTV-GI-083` | graph node deletion never implies deletion of a stable reusable/remote asset without a separate authorized asset command | `REQUIRED_CORRECTNESS` / `SOURCE_FACT` | source Asset Manager is distinct from Canvas node index | graph cleanup and account asset lifecycle remain separate transactions |
| `LIBTV-GI-084` | ordinary LibTV、Director and FrameOS media operations keep independent route/store/resource owners；prototype capability is projected honestly | `REQUIRED_CORRECTNESS` | current route stores and capability islands are separate | no cross-route locator/resource transfer；local preview/unavailable cannot masquerade as durable/provider success |

### 10.2 Compatibility case queue

| Case | Setup | Action | Required observation | Current status |
|---|---|---|---|---|
| `LIBTV-GC-001` dangling endpoint | one valid node + missing target ID | add/import edge | no partial edge; graph/history/selection delta explicitly defined | design contracted; runtime missing |
| `LIBTV-GC-002` exact duplicate | one existing edge with same handles | connect same pair again | ordinary source path has a same-pair guard; still assert no graph/history/feedback residue | design contracted + static recorded; source interaction pending |
| `LIBTV-GC-003` parallel handle edge | same nodes, different source/target handles | connect | ordinary source pair guard does not compare handles, so it is expected to reject; import/batch behavior remains open | design contracted + static recorded; entry-point decision pending |
| `LIBTV-GC-004` self-loop | one node with reachable handles | connect node to itself | ordinary non-Reference and programmatic paths have rejection evidence; assert Handle/line/history cleanup | design contracted + static recorded; Reference/source UI pending |
| `LIBTV-GC-005` three-node cycle | A -> B -> C | connect C -> A | ordinary source path has DFS rejection evidence; assert no UI/edge/history residue | design contracted + static recorded; source UI pending |
| `LIBTV-GC-006` group/child copy | selected group with descendants and internal/external edges | duplicate selection | ID map, parent IDs, internal closure, external-edge policy and placement exact | design contracted；current runtime partial |
| `LIBTV-GC-007` partial multi-copy | selected nodes share one internal and two external edges | duplicate selection | internal edge copied once; external behavior matches declared command | design contracted；current runtime partial |
| `LIBTV-GC-008` equal data update | node data merge is semantically unchanged | update | no-op history policy explicitly asserted | current clone currently records a step |
| `LIBTV-GC-009` nested metadata history | node has marks/regions/process arrays | mutate via immutable update, undo, redo | old/new snapshots stay isolated | fixture/verifier design complete；runtime missing |
| `LIBTV-GC-010` delete selected subtree | selected parent/group with child/reference edges | delete | node/edge closure, selection clear and one-step undo/redo exact | compare current cascade behavior |
| `LIBTV-GC-011` transaction failure | derived action fails validation after computing draft IDs | submit | no orphan node/edge, no selection shift, no history step | design required |
| `LIBTV-GC-012` canvas boundary | two canvases with independent graph/history | mutate, switch, undo | only active canvas graph/history changes | current clone contract exists |
| `LIBTV-GC-013` shot aggregate copy/delete | complete or broken source/result reciprocal set | duplicate/delete | both directions and edges map/repair atomically；partial reason stable | data registry/fixture design complete；runtime/source delete policy missing |
| `LIBTV-GC-014` process cohort copy/delete | complete or partial shared processId set | duplicate/delete | one new aggregate ID for complete copy；partial mutation rejects unless separately specified | data registry/fixture design complete；runtime/source lifecycle missing |
| `LIBTV-GC-015` media portability | repo/https/data/blob locators | history/copy/export/import | locator class, alias, budget and non-portable diagnostics explicit | data registry/document design complete；runtime missing |
| `LIBTV-GC-016` semantic edge deletion | derived target stores sourceNodeId/edgeId | delete edge/source | relation-specific clear/detach/cascade or stable unknown；no stale edgeId | delete matrix/fixture design complete；runtime/source policy missing |
| `LIBTV-GC-017` delete UI/canvas/resource boundary | node-bound overlay + two canvases + media locator | delete node/canvas、undo | selection/overlay/fallback/history/resource diagnostic exact | delete matrix/fixture design complete；runtime/resource owner missing |
| `LIBTV-GC-018` ingress-equivalent connection reject | same invalid edge through gesture/programmatic | connect | same structural reason；zero mutation | Batch 57 covers first two local paths |
| `LIBTV-GC-019` invalid derived draft | valid new node + invalid edge/data ref | derived command | entire plan reject/unknown；no partial node/ID/history | entrypoint design complete；runtime missing |
| `LIBTV-GC-020` semantic React Flow change bypass | edge add/replace/remove change | `onEdgesChange` | reroute or reject before generic apply | current route uses generic setEdges |
| `LIBTV-GC-021` malformed history restore | invalid snapshot at past/future head | undo/redo | restore reject；history cursor unchanged | document/entrypoint design complete；runtime missing |
| `LIBTV-GC-022` invalid clipboard/import relation | valid structure + invalid aggregate/data ref | paste/import | whole packet reject with path diagnostic | document/data/entrypoint design complete；runtime absent |
| `LIBTV-GC-023` stale server result | old revision/run patches replaced node | remote patch | stale/conflict result；no overwrite | future backend boundary only |
| `LIBTV-GC-024` draft drift | descriptor A submitted, current draft becomes B | A completes | A belongs to captured operation；B unchanged | async-ingress design complete；runtime absent |
| `LIBTV-GC-025` source version drift | run reads V1, source becomes V2 | V1 result | stale/superseded；current output unchanged | source media version runtime absent |
| `LIBTV-GC-026` delete/undo during run | operation placeholder/source removed | completion | no resurrection、selection steal or partial graph | async/delete composition designed |
| `LIBTV-GC-027` retry race | A old attempt, B current attempt | B then A completion | B remains current；A stale | run/attempt runtime absent |
| `LIBTV-GC-028` duplicate delivery | same result/version delivered twice | second ingress | exact no-op incl. history/resource | idempotency design complete |
| `LIBTV-GC-029` UI owner drift | user selects unrelated node/surface | completion | current owner preserved unless contextual transition passes | current delayed creators may rewrite selection |
| `LIBTV-GC-030` graph drift | placement/relation changes after submit | completion | replan on current graph or stable reject | current creators precompute before set |
| `LIBTV-GC-031` projection recovery | terminal envelope stored, graph commit fails | retry projection | provider not re-invoked；eventual one commit | future backend boundary |
| `LIBTV-GC-032` rejected resource | blob/temp result exists, ingress stale/invalid | reject | release exactly once | Director-focused future fixture |
| `LIBTV-GC-033` polling history | progress/failure/success sequence | observe/complete | no per-poll graph history；terminal transaction exact | future local fixture |
| `LIBTV-GC-034` node selection owner | selected node change | `onNodesChange` | validated node IDs/primary change；semantic graph/history unchanged | formal design complete；current node projection partial |
| `LIBTV-GC-035` edge selection owner | selected edge change | `onEdgesChange` | validated edge IDs/primary change；semantic edge/document/history unchanged | formal design complete；edge runtime owner missing |
| `LIBTV-GC-036` valid node drag frame | finite position + dragging | `onNodesChange` | current node position only；no frame history | current behavior partial；current-snapshot routing missing |
| `LIBTV-GC-037` passive measurement | measured dimensions without setAttributes | `onNodesChange` | runtime measured state only；no semantic resize/history | design complete；boundary sanitation missing |
| `LIBTV-GC-038` attribute resize | dimensions with setAttributes | `onNodesChange` | named layout command required；generic callback zero mutation | source/product unsupported |
| `LIBTV-GC-039` mixed semantic batch | selection/position followed by add/remove/replace | framework callback | whole batch reject/reroute；no partial selection/position | design complete；runtime missing |
| `LIBTV-GC-040` stale rendered edges | store gains edge before old callback runs | edge selection callback | new edge preserved；selection cannot whole-array overwrite | focused race fixture missing |
| `LIBTV-GC-041` stale element ID | node deleted before queued drag/measure | framework callback | no resurrection or cross-canvas write；stable stale result | focused fixture missing |
| `LIBTV-GC-042` same-ID reducer precedence | remove/add/position for same ID | framework callback | app classifier rejects before reducer replacement-like semantics | pure fixture missing |
| `LIBTV-GC-043` runtime field sanitation | selected/measured/dragging/resizing present | history/copy/document projection | portable/semantic outputs exclude undeclared fields | composes document/copy verifier |
| `LIBTV-GC-044` valid canvas switch | A/B distinct graph/viewport/history | A -> B -> A | each owner exact；selection clear；zero history | lifecycle design complete；runtime partial |
| `LIBTV-GC-045` unknown canvas target | valid A active | switch missing ID | stable reject/no-op；A unchanged | current setter creates invalid active ID |
| `LIBTV-GC-046` same canvas target | A active | switch A | exact no-op；no owner flicker/reset | fixture missing |
| `LIBTV-GC-047` organize switch race | A organize snapshot armed | switch B then restore | B unchanged；old transaction canceled | current route snapshot unkeyed |
| `LIBTV-GC-048` drag switch race | A drag baseline armed | switch B before late stop | no B graph/history write | current ref unkeyed |
| `LIBTV-GC-049` viewport switch race | A viewport callback queued | switch B then callback | B viewport unchanged | current owner token missing |
| `LIBTV-GC-050` node-bound UI switch | A preview/annotate/Director open | switch B | surface closes；graph/history unchanged | Batch 58 recorded for four owners |
| `LIBTV-GC-051` projection panel switch | asset/history/agent open on A | switch B | close or target-only rebind；no mixed data | manifest/source decision pending |
| `LIBTV-GC-052` complex canvas duplicate | group/derived/shot/process/Director/media | duplicate A | one valid B；mapped/reset resource policy；empty history/selection | current structural copy partial |
| `LIBTV-GC-053` inactive canvas delete | A active/selected；B target | delete B | A all owners exact；B history/UI/ops removed | runtime graph/history partial |
| `LIBTV-GC-054` active canvas delete | A active；B/C exist | delete A | valid deterministic fallback；selection/UI/transient clear | current first-item fallback；source decision open |
| `LIBTV-GC-055` final canvas delete | one canvas | delete | exact reject or replace-empty；registry remains valid | clone rejects；Open Canvas replaces empty |
| `LIBTV-GC-056` old timer completion | operation starts A | switch B；A completes | explicit A/stale result；never B/selection steal | async/lifecycle composition missing |
| `LIBTV-GC-057` old save completion | save A pending | hydrate B；A returns | durable A may finish；B in-memory baseline/status unchanged | Open Canvas-inspired race fixture |
| `LIBTV-GC-058` canvas resource delete | A owns blob/run/workspace | delete A | exact cancel/detach/release/retain once | resource ledger missing |
| `LIBTV-GC-059` invalid connection feedback | duplicate pair | drag connect | stable reason、zero graph/history、source-gated projection、gesture clear | local reason exists；source UI blocked |
| `LIBTV-GC-060` valid connection feedback | valid A -> B | connect | visible edge + one history；no required generic success toast | Batch 57 graph slice recorded |
| `LIBTV-GC-061` same-value command | unchanged title/value | submit | exact silent noop、zero history | command-specific audit needed |
| `LIBTV-GC-062` field rejection | empty required field | submit | field-local reason/focus；no started/success state | feedback fixture missing |
| `LIBTV-GC-063` prototype unavailable | remote service absent | click | honest action-adjacent local disclosure | current islands exist |
| `LIBTV-GC-064` node guard timer | unsupported media duration | invoke | node-local reason、zero graph/history、deterministic replace/clear | current action-specific timers partial |
| `LIBTV-GC-065` visible graph result | frame capture succeeds | invoke | result node/selection/history primary；announcement source-specific | Batch 29 behavior recorded |
| `LIBTV-GC-066` async started | operation accepted | submit | busy/process owner；not completed success | current booleans can conflate |
| `LIBTV-GC-067` async failed/retry | owned operation fails | retry | persistent reason/recovery；new attempt owns future completion | async runtime missing |
| `LIBTV-GC-068` stale completion announcement | A operation then switch B | A success | B unchanged；no B success announcement | owner fixture missing |
| `LIBTV-GC-069` duplicate terminal announcement | same terminal event twice | converge | one result/announcement；second no-op | dedupe runtime missing |
| `LIBTV-GC-070` local panel close | local-only status visible | close/reopen | status cleared；no hidden operation | current islands vary |
| `LIBTV-GC-071` background panel close | real operation visible | close | operation transfers to declared owner；not lost/misowned | product/owner decision needed |
| `LIBTV-GC-072` feedback owner delete | node/canvas error owner | delete | projection closes；operation/resource policy explicit | composes delete/lifecycle |
| `LIBTV-GC-073` history feedback replay | accepted result then undo/redo | undo/redo | graph follows snapshot；toast/timer not replayed | fixture missing |
| `LIBTV-GC-074` feedback burst | multiple file/result errors | batch | bounded aggregate/dedupe；no toast storm | policy/runtime missing |
| `LIBTV-GC-075` route feedback isolation | FrameOS toast active | enter LibTV | no shared store/queue/announcement | architectural invariant |
| `LIBTV-GC-076` client/host/flow round trip | offset host + translated/zoomed viewport | convert client -> flow -> client | finite round trip within declared tolerance | pure fixture designed |
| `LIBTV-GC-077` actual-host center add | asset panel narrows/shifts React Flow host | add ordinary node | node center aligns actual host center；one graph history；selection exact | runtime uses browser window center |
| `LIBTV-GC-078` live/stable pan | stable baseline | pan frames then end | live follows every current frame；stable commits once；zero graph history | phase runtime missing |
| `LIBTV-GC-079` pan/zoom cancel | current viewport session | pointercancel/blur/interruption | live returns declared baseline；stable/history unchanged | owner/cancel runtime missing |
| `LIBTV-GC-080` interrupted programmatic zoom | operation A then newer B | A completion arrives after B | A stale；B final stable exact；one endpoint | operation ID runtime missing |
| `LIBTV-GC-081` responsive bootstrap guard | user has stable viewport | breakpoint/layout changes | preserve declared graph anchor；bootstrap not reapplied | current demo preset can overwrite |
| `LIBTV-GC-082` viewport switch race | A gesture/animation pending | switch B then A callback | B live/stable unchanged；A result stale | composes lifecycle `GC-049` |
| `LIBTV-GC-083` nested-node projection | child with valid parent chain | compute overlay/placement world point | full ancestor world sum before viewport transform | pure fixture designed |
| `LIBTV-GC-084` invalid parent geometry | dangling or cyclic parent | project child | invalid result；no fabricated partial position/surface | pure fixture designed |
| `LIBTV-GC-085` screen clamp dual anchor | pointer menu near host edge | clamp/flip menu | screen anchor changes；captured flow anchor exact | future entry remains unsupported |
| `LIBTV-GC-086` fixed-flow duplicate under zoom | same selection at two viewports | duplicate | equal world `+40,+40` delta；one history | current compatibility island |
| `LIBTV-GC-087` derived placement under viewport | source node at two pan/zoom states | add derived output | same world source-relative/collision result | current useful partial |
| `LIBTV-GC-088` host resize overlay composition | selected image + asset/compact layout change | resize host | one current host/live/node frame；existing LibTV toolbar/panel residuals remain in tolerance | formal composition designed |
| `LIBTV-GC-089` invalid spatial payload | NaN/Infinity/out-of-range zoom/stale host epoch | viewport/placement callback | stable typed reject/stale；zero graph/selection/history/viewport residue | validation runtime missing |
| `LIBTV-GC-090` route spatial isolation | Director or FrameOS active | ordinary LibTV spatial callback | no cross-route transform/gesture/graph effect | architectural invariant |
| `LIBTV-GC-091` chooser cancel | no active ingress | open chooser then cancel | zero operation residue、zero graph/history/feedback；no lease created | local fixture required |
| `LIBTV-GC-092` all-invalid cohort | synthetic wrong family/size/probe failures | submit multi-item ingress | stable per-item reasons in original order；zero graph/selection/history；all temporary leases released | classifier/probe fixture required |
| `LIBTV-GC-093` mixed cohort | valid A、invalid B、valid C | resolve all probes/materialization | explicit profile commits A/C in original order as one graph/history step or rejects full cohort；never sequential partial history | policy/profile fixture required |
| `LIBTV-GC-094` out-of-order materialization | A/B/C accepted | resolve C then A then B | provisional completion may update；final graph order follows original indices；one history | deterministic resolver clock required |
| `LIBTV-GC-095` cohort cancel | accepted items with one pending | cancel during materialization | profile-declared rollback/accepted boundary exact；pending completion stale；terminal leases exact | cancel semantics source-partial |
| `LIBTV-GC-096` node replace success | node has stable old media | current replacement resolves valid | old remains visible until one commit；new reference exact；old release only after reachability check；one history | local replacement fixture required |
| `LIBTV-GC-097` node replace failure | node has stable old media | validation/probe/materialization fails | old media/reference unchanged；persistent item-local error/retry owner；zero graph history | source exact feedback partial |
| `LIBTV-GC-098` delete target during ingress | node-bound operation pending | delete node then resolve | delete transaction wins；completion stale；no recreated node/current success；lease release exact | composes delete/async fixtures |
| `LIBTV-GC-099` switch canvas during ingress | A operation pending | switch B then resolve A | B graph/selection/history/feedback unchanged；A follows explicit background/cancel policy only | composes lifecycle fixture |
| `LIBTV-GC-100` retry race | attempt 1 pending/failed then attempt 2 current | resolve attempt 1 after attempt 2 | attempt 1 stale；attempt 2 is sole commit/feedback owner；no double transfer/release | attempt identity required |
| `LIBTV-GC-101` generated-history attach | stable history items already exist | select supported items and attach | no file upload/materializer claim；source item identity preserved；declared node refs/placement/selection/one history | source exact projection partial |
| `LIBTV-GC-102` shared asset alias deletion | two nodes reference one reusable asset | delete one node | surviving node and asset remain valid；only deleted reference removed；no remote asset delete | asset/reference ledger required |
| `LIBTV-GC-103` Shot local preview | synthetic video selected | probe and bind under no-backend profile | honest `LOCAL_PREVIEW` locator/state；not durable ready/uploaded；replace/history policy exact | current clone labels ready too early |
| `LIBTV-GC-104` probe failure cleanup | preview/probe lease created | metadata probe rejects/errors | no graph mutation；object URL revoke exactly once；typed reason retained by operation owner | lease counter fixture required |
| `LIBTV-GC-105` duplicate terminal callback | current operation already committed/failed/canceled | same result arrives again | typed duplicate；zero graph/history/feedback/resource delta | composes async idempotency |
| `LIBTV-GC-106` blob reachability across delete/undo | graph/history/editor share one blob-backed result | delete、undo、redo、close editor | lease remains while reachable；release only at final zero reachability；never use-after-revoke | resource ledger fixture required |
| `LIBTV-GC-107` data locator portability budget | data URL below/above declared local budget | project/export/copy | small allowed case keeps provenance；oversize rejected or materialized；never silently durable | prototype-only policy required |
| `LIBTV-GC-108` media route/capability isolation | Director/FrameOS operation or unavailable provider selected | ordinary LibTV callback/action | zero cross-route graph/resource effect；honest unavailable/local-only projection | architectural + UI assertion |

### 10.3 Decision and verification order

1. Lock `GI-001..003/008..030` data-correctness portions as pure cases, while keeping source/product branches explicit;
2. obtain source evidence or explicit clone decision for `GI-004..007`;
3. use the versioned result/reason/precedence shape in [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md) without adopting Open Canvas node types or payload;
4. the Batch 57 structural connection slice is now implemented and recorded through `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`; keep its source-invalid/Reference/domain branches separate;
5. use `LIBTV-FIX-LOCAL-DEMO-01/GROUP-01/DERIVED-01` for existing command compatibility;
6. only after authorization, integrate one guard at a time and keep Handle/edge visuals unchanged;
7. treat `LIBTV-VR-009` as partially closed: structural clone acceptance is recorded by Batch 57, while source invalid lifecycle, Reference/domain compatibility and other entry points remain open.

### 10.4 2026-08-27 静态审计补充

本次 source bundle/DOM 结果和原始结构化证据见 [`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md) 与 [`libtv-graph-compatibility-static-audit-2026-08-27.json`](open-canvas-2026-08-26/libtv-graph-compatibility-static-audit-2026-08-27.json)。它把 Open Canvas 的一般性 DAG/typed validation 启发收敛为 LibTV 当前连接 boundary 的四个静态信号：

- `onConnect` 不是低层 `addEdge` 的别名，而是先做 target-start 方向归一化，再执行 validator，再提交 edge；
- normal connection path 的 pair guard 按 unordered node pair 去重，不给不同 Handle 留 parallel edge 旁路；
- ordinary non-Reference path 使用候选 edge 的 adjacency + DFS 拒绝 self-loop/cycle，programmatic pair 对 equal IDs 还有独立 guard；
- node action/type matrix、目标容量、当前 model capability 和可选 `switchToModel` 仍是最终兼容性的一部分，不能用 DOM Handle class 或 Open Canvas 五类 node 替代。

以上仍是 `SOURCE_STATIC_EVIDENCE`，不关闭 `SOURCE_DECISION_REQUIRED`。Reference exception、导入/批量/同步入口、invalid feedback、connection-line 生命周期和 history/no-residue 必须在 disposable source fixture 或明确 clone-only 决策中处理。本节不授权添加 DAG guard、修改 `canvasStore` 或改变已确认的 edge flow effect。

This register is a design input. It does not authorize adding DAG validation, changing edge direction or rewriting `canvasStore`.

### 10.5 Connection contract handoff

[`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md) is now the connection-specific authority for:

- raw gesture and target-start direction normalization;
- `allow / allow-with-adjustment / reject / unknown` result shape and stable clone-only reason codes;
- duplicate/self/cycle precedence and explicit source-policy unknowns;
- rejected/unknown zero mutation and accepted one-step graph history;
- `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` plus `LIBTV-VR-009` pure/browser acceptance design;
- four independently authorized implementation slices: structural, React Flow boundary, domain compatibility and import/batch/sync.

Status: `STRUCTURAL_SLICE_RECORDED_PASS / SOURCE_EXCEPTION_BLOCKED / DOMAIN_COMPATIBILITY_OPEN`. Batch 57 closes the local structural connection transaction only; it does not close Reference, domain compatibility, source invalid lifecycle, import/batch/sync or persistence.

### 10.6 Graph document and snapshot handoff

[`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md) is now the document/snapshot-specific authority for:

- runtime graph、history snapshot、portable document、clipboard packet 和 future persistence envelope 的五层分离；
- clone-only V1 conceptual schema、node data version 和 runtime-field whitelist；
- nested metadata deep isolation，同时继续排除 viewport、selection、canvas CRUD 和 UI/save state；
- strict parse、future-version stop、pure migration、node/edge/parent/media diagnostics 和 zero-partial load；
- `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` plus `LIBTV-VR-010` pure/history acceptance design；
- codec、history isolation、import-as-new-canvas、export/clipboard reuse 和 deferred persistence 的独立授权 slice。

Status remains `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / PERSISTENCE_DEFERRED`。这不表示普通画布已有 import/export、reload recovery、revision、conflict 或 remote save。

### 10.7 Subgraph copy and duplicate handoff

[`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md) is now the copy-specific authority for：

- duplicate-selection、node-only、paste-subgraph 和 future Option-drag 的具名命令；
- root sanitize、recursive descendant closure 和 ancestor/child dedupe；
- two-pass nodeMap/edgeMap、parent remap/detach 和 flow-space placement；
- node data reference role：owned、external provenance、edge、asset、run/task、session 和 display projection；
- `none / internal-only / incident-compatibility` edge policy；
- full-plan validation、zero-partial failure 和 accepted one-step history；
- `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` plus `LIBTV-VR-011` pure/browser acceptance design。

Current runtime is `PARTIAL`：Batch 3/5/8 已有结构 closure 和 history，reference-role/aggregate registry 已完成设计但没有 runtime codec/system clipboard；single-node incident edge 分支保持 compatibility hold。Option-drag 仍需 disposable source fixture。

### 10.8 Node data identity and aggregate handoff

[`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md) is the dated clone-fact inventory；[`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) is the normative design authority for：

- 11 runtime node types and current `dataVersion: 0` migration baseline；
- canonical field roles for semantic/display/node/edge/aggregate/scoped/catalog/asset/media/provenance/run/session data；
- named operation profiles for history、selection/node copy、canvas duplicate、clipboard、portable import and delete repair；
- shot breakdown reciprocal aggregate and long-video process complete-cohort policy；
- Director shell/workspace boundary and repo/https/data/blob portability；
- stable reject/unknown reasons、zero-partial integrity pass、`LIBTV-FIX-LOCAL-NODE-DATA-01` and `LIBTV-VR-012`。

Status is `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / SOURCE_PRODUCT_DECISIONS_PARTIAL`。It closes the registry audit/design gap, not the runtime schema gap；no graph/store/type/test code is authorized by this handoff。

### 10.9 Delete impact and reference repair handoff

[`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) is the delete-specific authority for：

- Open Canvas centralized node/edge/selection deletion and conflict no-op as method-only inspiration；
- current clone `removeNode/removeSelectedNodes/removeEdge/clearVideoContinuation/removeCanvas` impact inventory；
- structural、owned-edge、provenance、shot reciprocal、process aggregate、UI owner、media and canvas relation classes；
- named command、inverse relation index、full-plan validation and ready/reject/unknown results；
- per-relation active/proposed/source-required/deferred policy and `LIBTV-DEL-DQ-001..008`；
- `LIBTV-FIX-LOCAL-GRAPH-DELETE-01`、`LIBTV-FIX-SOURCE-GRAPH-DELETE-01` and `LIBTV-VR-013`。

Status is `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / SOURCE_PRODUCT_DECISIONS_PARTIAL`。No delete planner、fixture adapter、verifier、cascade/detach behavior or media/workspace destruction is authorized by this handoff。

### 10.10 Graph mutation entry-point authority handoff

[`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md) is the ingress-specific authority for：

- fixed Open Canvas store/local guard、serialization、full-graph save/API validation、revision and server-patch layers；
- upstream clipboard、framework delta、handle-retarget、tolerant normalize and edge-rebase limitations that must not be copied；
- current clone canvas/node/derived/copy/group/delete/data/setter/connection/history/future ingress inventory；
- `PROTECTED / PARTIAL / TRUSTED_OUTPUT_UNPROVEN / BYPASS / DEFERRED` maturity；
- T0 presentation、T1 transport、T2 proposal、T3 planned command、T4 restore and T5 remote authority；
- `LIBTV-ING-DQ-001..008`、`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01`、`LIBTV-VR-014` and `GI-018..022/GC-018..023`。

Status is `STATIC_AUDIT_COMPLETE / DESIGN_SPEC_COMPLETE / RUNTIME_PARTIAL`。Batch 57 protects only the local structural connection island；no generic setter restriction、derived command planner、restore codec、clipboard/import or remote authority is authorized by this handoff。

### 10.11 Async result ingress and convergence handoff

[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) is the completion-specific authority for：

- fixed Open Canvas descriptor/run/runId polling/server-patch/revision/saved-baseline chain；
- upstream missing expected-run/source-version/field-owner compare、stranded-run、two-write projection and storage RMW limitations；
- committed clone shot/video/long-video timer and Director async completion inventory；
- operation descriptor、result envelope、current/stale/duplicate/invalid disposition and operation-specific field ownership；
- selection/history/undo/redo/resource transfer and recoverable projection policy；
- `LIBTV-ASYNC-DQ-001..010`、`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01`、`LIBTV-VR-015` and `GI-023..030/GC-024..033`。

Status is `STATIC_AUDIT_COMPLETE / DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`。Current timers remain `PROTOTYPE_LATENCY`；no async schema、fixture queue、provider、polling、persistence or source task action is authorized by this handoff。

### 10.12 Viewport, coordinate, gesture and placement handoff

[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) is the spatial authority for：

- `CLIENT/HOST_LOCAL/FLOW_WORLD/NODE_LOCAL/SCREEN_OVERLAY/MEDIA_NORMALIZED` coordinate domains and strict finite validation；
- actual React Flow host frame/epoch，plus `BOOTSTRAP/LIVE/STABLE/TARGET` viewport ownership；
- pan/zoom/drag/connection/menu/organize gesture start/update/end/cancel/stale lifecycle；
- `HOST_CENTER/EXPLICIT_FLOW/SOURCE_RIGHT_SLOT/FIXED_FLOW_DELTA/FLOW_ANCHOR/FRAMEWORK_DRAG/ORGANIZE_LAYOUT/BOOTSTRAP_TOPOLOGY` placement strategies；
- host resize anchor preservation、canvas generation、history/document boundary and overlay-frame composition；
- `LIBTV-VGP-I-001..032`、`LIBTV-VGP-DQ-001..012`、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01`、`LIBTV-VR-020` and `GI-059..070/GC-076..090`。

Status is `STATIC_AUDIT_COMPLETE / DESIGN_SPEC_COMPLETE / RUNTIME_PARTIAL / SOURCE_PARITY_PARTIAL`。Current V/H/Space、per-canvas viewport、drag history、derived/duplicate/organize placement and selected-overlay formulas remain positive islands；no spatial helper、store/page adapter、fixture、verifier、Quick Add/drop/pending connection or source mutation is authorized by this handoff。

### 10.13 Media ingress and resource lifecycle handoff

[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) is the cross-entry media authority for：

- Add Resource、canvas drop、node replace、Shot source、generated-history attach、asset attach、canvas reference、local edit export and two Director profiles；
- immutable ingress/attempt/cohort/canvas/node/source identities plus local lease、stable asset、node reference and locator provenance；
- canonical validation、metadata probe、materialization、freshness reconciliation and full projection plan；
- provisional UI versus semantic graph/history/document、multi-item order/commit policy and last-known-good replacement；
- explicit resource transfer/release and reachability across graph/history/clipboard/editor/operation/asset/export owners；
- Open Canvas `OC-061..070` positive methods and classifier/placeholder/partial/autosave/no-cleanup counterexamples；
- source `LIBTV-SRC-MIR-001..006` surface separation and exact behavior decision queue；
- `LIBTV-MIR-I-001..036`、`LIBTV-MIR-DQ-001..014`、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`、`LIBTV-VR-021` and `GI-071..084/GC-091..108`。

Status is `STATIC_AUDIT_COMPLETE / DESIGN_SPEC_COMPLETE / RUNTIME_MISSING_OR_PARTIAL / SOURCE_PARITY_PARTIAL`。Current Add Resource mocks、Shot component-local preview and Director data/blob paths remain evidence islands；no common classifier/materializer/lease/asset registry/fixture/verifier、real upload/storage/provider or source mutation is authorized by this handoff。

## 11. 新事务立项模板

任何新的 LibTV graph 能力，在编码授权前至少落档以下字段：

```text
Command ID:
Source evidence / inference boundary:
Owner component:
Preconditions and no-op guards:
Input normalization:
Node delta:
Edge delta and direction:
Parent/child implications:
Placement rule in world coordinates:
Selection after success:
History snapshot boundary:
Undo result:
Redo result:
Local editor history relationship:
Repeated invocation / idempotency:
Stable selectors:
Focused verifier fixture:
Backend/prototype boundary:
```

最低验收顺序：

1. guard 失败时 nodes、edges、history 均不变；
2. 成功时 graph delta、edge direction、metadata、placement 和 selection 精确；
3. 一次 undo 回退整批，一次 redo 恢复整批；
4. 新命令清空 redo；
5. multi-selection、group/child、重复提交和移动端不破坏既有合同；
6. source fact、evidence-backed inference 和 clone-only decision 在实施记录中分开。

## 12. 相关入口

- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：键盘命令到 store transaction 的运行语义。
- [`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)：overlay、editor-local state、preview、task 和 graph mutation 分层。
- [`COMMAND_HISTORY.spec.md`](liblib-canvas-batch3-2026-08-25/COMMAND_HISTORY.spec.md)：通用 history 权威合同。
- [`MULTI_MOVE.spec.md`](liblib-canvas-batch5-2026-08-25/MULTI_MOVE.spec.md)：拖动压缩为单事务的合同。
- [`ORGANIZE_CANVAS.spec.md`](liblib-canvas-batch7-2026-08-25/ORGANIZE_CANVAS.spec.md)：graph 与 viewport 跨域命令。
- [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)：新能力的研究/授权闸门。
- [`open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md`](open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md)：上游 graph 模式的采纳、改造与拒绝边界。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：`PAR-008` 的本地 fixture 和 reset 规则。
- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：node/edge/primary selection、focus zone、command context、单层 Escape 和 `VR-019` 的正式设计权威。
- [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)：media intent、temporary lease、asset/reference、cohort transaction、reachability/release 和 `VR-021` 的正式设计权威。
