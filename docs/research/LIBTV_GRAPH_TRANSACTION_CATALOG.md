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

### 10.3 Decision and verification order

1. Lock `GI-001..003/008..015` data-correctness portions as pure cases, while keeping source/product branches explicit;
2. obtain source evidence or explicit clone decision for `GI-004..007`;
3. use the versioned result/reason/precedence shape in [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md) without adopting Open Canvas node types or payload;
4. implement and run the designed `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` only after coding authorization;
5. use `LIBTV-FIX-LOCAL-DEMO-01/GROUP-01/DERIVED-01` for existing command compatibility;
6. only after authorization, integrate one guard at a time and keep Handle/edge visuals unchanged;
7. implement the designed `LIBTV-VR-009` replacement before claiming the connection sub-slice complete.

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

Status remains `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / SOURCE_EXCEPTION_BLOCKED`. This closes a documentation gap, not a runtime gap; it does not authorize code, fixture or verifier changes.

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
