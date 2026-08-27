# LibTV UI/UX Parity Backlog

> 建档日期：2026-08-26。
> 稳定 clone 基线：Batch 60 closeout；普通图片双浮层 owner 连续性和 panel
> 命中边界已形成 clone-owned 有界合同。Director 资源库搜索、preview-only
> selection 和 proxy insertion 也已形成有界 clone 合同。真实 mesh loading、
> 远程同步、LibTV 生产持久化和
> source-exact gizmo renderer 仍不在合同内。
> 目的：面向后续 LibTV UI/UX 复刻，统一回答“当前真正还差什么、先研究什么、什么已可申请编码、怎样验证”。
> 本文是研究与排期文档，不授权修改 `src/`、测试脚本或共享源站状态。

## 1. Authority And Non-goals

本文聚合全路由当前差距，但不替代专项证据：

| 文档 | 继续负责 | 本文负责 |
|---|---|---|
| `liblib-live-2026-08-25/README.md` | 2026-08-25 页面壳、节点、入口和截图事实 | 不再承担当前排期权威。 |
| `LIBTV_FEATURE_GAP_MATRIX.md` | Seedance 五项主推能力的产品/状态缺口 | 将其中可执行项放入全局优先队列。 |
| `LIBTV_VERIFICATION_COVERAGE.md` | 图片、AutoLink、视频工作流的测试覆盖解释 | 只引用测试准备度，不复制完整断言。 |
| `TRACEABILITY_MATRIX.md` | 从主张反查源站/clone/Open Canvas 证据 | 给 gap 排价值、依赖和停止条件。 |
| `LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` | 当前 overlay state、mount owner、close/focus/anchor 行为 | 把运行时风险转成研究或实施队列。 |
| `LIBTV_GRAPH_TRANSACTION_CATALOG.md` | nodes/edges/selection/history 的实际副作用 | 判断某项能否作为独立、可撤销 slice。 |
| `LIBTV_RESEARCH_GO_NO_GO.md` | 编码授权和 fixture 总闸门 | 给每个 backlog item 指定具体闸门。 |
| `LIBTV_FIXTURE_CATALOG.md` | fixture 身份、构造、隔离、reset、storage 和副作用边界 | 判断 gap 是否具备可重复的本地/源站前置状态。 |
| `LIBTV_SOURCE_FRESHNESS_REINSPECTION.md` | 共享源站的版本化只读复核顺序和停止条件 | 判断 source evidence 是否需要 refresh，以及未知是否必须阻塞。 |
| `LIBTV_VERIFIER_REPLACEMENT_MAP.md` | 历史 verifier、current source contract 和 replacement queue | 判断旧断言应保留、标历史、补充还是申请替换。 |
| `DECISION_REGISTER.md` | 跨项目长期的授权、安全、fixture 和协作决策 | 处理 backlog 排序不能自行解锁的全局闸门。 |

不在本文范围内：

- 将文章截图、Open Canvas 或 clone 当前行为提升为 LibTV 源站事实；
- 设计真实 Provider、上传、积分、计费、远端任务或账户持久化；
- 替 Batch 48 决定实现或修改其已收口的历史合同；
- 因为某项“高价值”就自动获得编码授权。

## 2. Status Vocabulary

| 状态 | 含义 | 当前允许动作 |
|---|---|---|
| `READY_FOR_AUTHORIZATION` | 源站合同和 clone delta 足够明确，可提出单 slice 编码申请 | 继续写计划/验收；没有授权仍不改代码。 |
| `DESIGN_FIRST` | 事实明确，但数据结构、history 或 ownership 设计尚需先落档 | 文档、纯 helper 合同、fixture 设计。 |
| `RESEARCH_FIRST` | 当前证据不足以决定源站一致行为 | 只读 DOM/bundle/截图复核；不猜实现。 |
| `BLOCKED_BY_FIXTURE` | 必须有可丢弃源站或本地状态才能继续 | 先定义 fixture，不操作共享项目。 |
| `PROTOTYPE_BOUNDARY` | 当前 local mock 是有意边界，不是待立即补后端的 bug | 只校正可见 UI/UX 和明确的本地反馈。 |
| `DEFERRED_ENGINEERING` | 有维护价值，但用户可见收益低于 fidelity 工作 | 保持记录，等待相关代码触发。 |
| `OUT_OF_SCOPE` | 不属于当前前端原型研究 | 需要新的产品/后端授权和合同。 |
| `PARALLEL_WIP` | 由其他开发者正在推进 | 只读、链接、避让，不覆盖。 |
| `RECORDED_PASS` | clone-owned 有界 slice 已完成实现和验证 | 读取其历史合同，不把结果升级为源站事实。 |

## 3. Scoring Method

每项使用四个 1-5 分维度。分数帮助排序，不替代证据和停止条件。

| 维度 | 1 | 5 |
|---|---|---|
| `V` 用户/产品价值 | 边缘维护 | 高频、首屏或产品识别核心 |
| `E` 证据成熟度 | 线索/推测 | 当前 DOM/bundle/多状态合同完整 |
| `T` 验证准备度 | 没有 fixture/selector | 可本地确定性验证且有历史脚本基础 |
| `R` 实施/副作用风险 | 局部只读 UI | graph/任务/持久化/跨组件数据模型 |

排序规则：先看用户价值和是否解锁后续工作，再看证据与验证准备度；高风险项即使高价值，也不会越过 fixture 或编码授权闸门。

## 4. Current Priority Queue

### 4.1 Summary

| Rank | ID | Slice | V | E | T | R | 状态 |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `LIBTV-PAR-001` | 当前图片标准双浮层的动作集合与几何 | 5 | 5 | 5 | 2 | `RECORDED_PASS (geometry only)` |
| 2 | `LIBTV-PAR-002` | Preview/Annotate/Element Edit/Rotate 的 L2 -> L3/L4/graph slice | 5 | 5 | 5 | 3 | `RECORDED_PASS (empty states + bounded rotate graph)` |
| 3 | `LIBTV-PAR-003` | Auto Link ghost + structured mention | 5 | 4 | 2 | 4 | `BLOCKED_BY_FIXTURE`；design spec complete |
| 4 | `LIBTV-PAR-004` | Top-level modal/Director 的 keyboard 与 focus ownership | 4 | 3 | 3 | 3 | `RESEARCH_FIRST` |
| 5 | `LIBTV-PAR-005` | 当前源站页面壳与主入口只读 freshness refresh | 4 | 3 | 5 | 1 | `RESEARCH_FIRST` / `PARTIAL_RECORDED` |
| 6 | `LIBTV-PAR-006` | Ready-video 顶部处理工具条与 mode replacement | 5 | 3 | 2 | 4 | `BLOCKED_BY_FIXTURE` |
| 7 | `LIBTV-PAR-007` | 快捷键 source-only 命令与 help/handler 一致性 | 4 | 3 | 2 | 4 | `BLOCKED_BY_FIXTURE` |
| 8 | `LIBTV-PAR-008` | 普通画布 graph transaction 健壮性 | 4 | 5 | 3 | 4 | connection structural slice `RECORDED_PASS`（Batch 57）；document/copy/data/delete/entrypoint authority design complete，runtime 仍 partial |
| 9 | `LIBTV-PAR-009` | 逐帧拉片/超长视频的真实过程与结果生命周期 | 4 | 3 | 2 | 5 | `BLOCKED_BY_FIXTURE` |
| 10 | `LIBTV-PAR-010` | Agent/Share/Toolbox/History/Upload 的 local mock 边界 | 3 | 4 | 4 | 3 | `PROTOTYPE_BOUNDARY` |
| 11 | `LIBTV-PAR-011` | `uiStore` owner identity 与冗余/unmounted/unreachable 状态清理 | 3 | 5 | 5 | 2 | Batch 58 owner lifecycle `RECORDED_PASS`；冗余 boolean/unmounted state 仍 deferred |
| 12 | `LIBTV-PAR-012` | Provider、上传、计费、远端任务、账户持久化 | 5 | 1 | 1 | 5 | `OUT_OF_SCOPE` |
| - | `LIBTV-PAR-013` | Batch 48 local model-library persistence | 4 | 4 | 4 | 4 | `RECORDED_PASS` |
| - | `LIBTV-PAR-014` | 媒体接入、asset/reference 与 temporary resource lifecycle correctness | 5 | 4 | 2 | 5 | `DESIGN_FIRST`；static/design complete，runtime missing/partial、source parity partial |
| - | `LIBTV-DIR-000` | Batch 49 Director viewport native coordinate gizmo | 4 | 4 | 5 | 2 | `RECORDED_PASS` |
| - | `LIBTV-DIR-001` | Batch 50 Director workspace keyboard/focus ownership and panel collapse | 4 | 3 | 5 | 3 | `RECORDED_PASS` |
| - | `LIBTV-DIR-002` | Batch 59 Director asset-library search/preview/add-object flow | 4 | 2 | 5 | 2 | `RECORDED_PASS`；clone-owned，source exact blocked by authentication |

### 4.2 `LIBTV-PAR-001`: current standard image state

**为什么排第一**

这是用户直接指出的高频识别态，也是所有图片 active tool 的入口基线。当前 source contract 已经足够精确，而 clone 仍停在历史版本。

| 项 | 当前结论 |
|---|---|
| `SOURCE_FACT` | toolbar 以 node screen center 为横向 anchor；host top 为 `nodeTop - 24 * zoom - 10` 后向上平移自身；当前 action set 为 9 个文字动作 + 4 个图标动作，已观察 `1092.5x49`。 |
| `CLONE_FACT` | Batch 52 后 `ImageToolbar` 使用 `NodeToolbar offset=10 + 24 * zoom`，当前 clone action shell 为 `1092.5x49`、13 项 source-shaped actions；Preview 已是 page-level read-only overlay；bottom panel 继续使用节点内 absolute + inverse zoom。 |
| 差距 | top action/order/width/formula 尚未升级；historical Batch 9 断言不能证明当前 source parity。 |
| 最小 slice | 只做 standard selected image；不顺手实现 active tools、Auto Link 或 backend。 |
| 验收 | 同 frame 读取 node/toolbar/panel/viewport；多 zoom center/gap；desktop/mobile；自然裁切；空选/多选卸载；graph count 不变。 |
| 停止条件 | 没有明确编码授权；或当前源站重新取证发现 action set/formula 已变。 |

主要证据：`LIBTV-TR-002..006`、`LibTVOverlayPositioning.contract.md`、`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`。

Batch 51 已完成 clone-owned 的几何 slice：`ImageToolbar` 的 top host
现在使用 `10 + 24 * zoom`，并由专项 verifier 覆盖约 28%/放大/pan；
bottom panel 合同保持 `16 * zoom`。当前 source action set 与 clone
`900.5px` 旧动作集合的差异仍未实施，active image tool 也继续单独排队。

Batch 60 在该图片基线之上补齐了 standard pair 的 owner identity 和 selection
迁移回归：`ImageToolbar` 与 `ImageEditPanel` 必须携带同一
`data-owner-node-id`，旧 pair 在切换时卸载，新 pair 在同一选中态下挂载；
panel 非交互区域不 blanket 捕获 pointer，控件仍保持交互。该命中策略是
clone-owned decision，不证明源站在 panel 覆盖相邻节点时的真实 routing，也
不改变既有几何、自然裁切或 graph/history 合同。

### 4.3 `LIBTV-PAR-002`: low-risk active surfaces

标准态之后，优先按一个 action 一个批次处理：

| 子项 | Source state | 最小 clone 目标 | 明确不包含 |
|---|---|---|---|
| Preview | page-level read-only overlay；关闭后回到原 selection | Batch 52 已覆盖 open/close/Escape、媒体比例、watermark/close geometry、unchanged graph/selection、mobile clipping | 多媒体历史切换、下载、水印偏好、会员逻辑 |
| Annotate empty | dedicated `536x49` toolbar + DPR canvas；standard bottom panel absent | empty enter/Escape/discard，恢复 standard L2 | 绘制保存、远端任务 |
| Element Edit empty | dedicated toolbar/stage/record panel；standard L2 absent | Batch 54 已覆盖 empty enter/Escape、tool/brush-size controls、disabled local history、geometry and keyboard isolation | 有效 record、对象识别、生成结果 |
| Rotate graph entry | 有媒体时点击 `旋转` 新增并选中 `旋转与镜像` 节点；source edge 可见；无媒体 disabled | Batch 56 已覆盖 media gate、node/edge/selection、typed `rotateMirror`、atomic undo/redo 和 desktop/mobile overflow | 真实 bitmap、角度/镜像编辑器、dirty/save、provider 和最终结果状态 |

这些子项不能合成一个“通用图片弹窗”。Preview 属于 page L4；Annotate/Element Edit 属于 node authoring L3；Batch 56 的 Rotate 只覆盖 graph-visible entry。旋转编辑器、图层分离和 dirty save 继续留在高风险 fixture 队列。

### 4.4 `LIBTV-PAR-003`: Auto Link

**当前状态**

- source 是全局偏好、connected/reference candidate pool、inline ghost、单项/全量接受和 structured mention；
- clone 是固定候选、独立 confirmation popover 和普通字符串前缀；
- graph edge、reference role、Prompt mention 和模型 ordinal 必须保持不同身份。

**为何先设计，以及当前结论**

它会同时触及 ImageEditPanel、VideoGenerationPanel、稳定 node ID、reference projection、keyboard/IME/race guard 和 transaction consistency。没有 typed token/candidate/session 合同就直接改 UI，会把旧固定 popover 扩大成更难迁移的数据债。

**设计输出闸门**

1. candidate、ghost、committed mention、reference role 的类型和 owner；
2. click/Tab/Shift+Tab/Escape/edit/blur/IME/stale result 状态图；
3. graph/reference/mention 成功与失败的原子边界；
4. 图片/视频共用什么，Provider 投影留在哪一层；
5. deterministic local fixture 和 replacement verifier。

上述五项已经由 [`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md) 的 identity/state/transaction 与 fixture acceptance 章节完成文档设计。当前 blocker 已从“缺设计”收窄为“运行 fixture 未实现、共享源站无 disposable input fixture、编码未授权”；不能因此把该项升级为已实现或 verifier-ready。

### 4.5 `LIBTV-PAR-004`: page keyboard and focus ownership

当前 clone runtime 已证明：

- Character/History backdrop 阻断 pointer，但没有统一 focus trap 或 page shortcut boundary；
- Shortcuts 不是带 backdrop 的 modal；普通 button 上的 Delete/Tab/group 等仍会到 page handler；
- Batch 50 已让 page dispatcher 在 Director active 时对全部普通画布快捷键提前返回，并记录 workspace focus owner；完整 focus trap、focus return 和 LibTV source-exact Director keyboard contract 仍未知；
- CanvasDropdown 的 local Escape 与 page Escape 可同时观察事件；active node tools 又有 capture-phase listener。
- node selection 已有独立 session projection，但 edge selection 仍由 generic `onEdgesChange` 留在 stored edge record，Delete 又只读取 node selection。

完整 fixed audit 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)；正式设计权威是 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)，已定义 node/edge/primary active-session selection、focus zone、surface policy、`HANDLED/CONSUMED/PASS/BLOCKED/NOOP`、one-Escape、focus return、`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` 和 `LIBTV-VR-019`。下一步仍需只读复核源站 modal、Agent、Share、Shortcuts 的 keyboard/outside/focus 行为并等待编码授权；不因设计完成就引入全局 modal manager。

### 4.6 `LIBTV-PAR-005`: source freshness refresh

2026-08-25 live audit 对 page shell、主入口和 10/11 graph 基线价值很高，但大量实现批次已在其后发生。下一次安全只读复核应回答：

1. 顶部导航、两个底栏、drawer 宽度和响应式隐藏规则是否变化；
2. top-level surface 的 outside/backdrop/Escape/focus 行为；
3. source 帮助面板、主入口 label/badge 和图片 action set 是否再次漂移；
4. 当前共享项目 node/edge/viewport 是否仍可作为 fixture；
5. 哪些旧 Batch screenshot 只剩 historical value。

允许动作仅限打开、选择、读取 DOM/computed style 和无副作用的 close/reopen。输入、上传、生成、保存、下载、任务提交和 graph mutation 继续禁止。

### 4.7 `LIBTV-PAR-006`: ready-video toolbar

当前 clone 已实现多个视频处理工具，但当前共享源站没有安全 ready-video fixture。需要先确认：

- ready 与 failed/pending 视频的 toolbar 分支；
- 当前 action order、hover menu、disabled/busy 和 active-tool replacement；
- reshoot/continue/subtitle/matting/picture-edit/depth 的互斥关系；
- Escape/discard/submit 后 selection、source/result 和 graph delta。

没有 disposable ready-video fixture 时保持 `BLOCKED_BY_FIXTURE`，不能用 clone 已有按钮顺序反推源站。

### 4.8 `LIBTV-PAR-007`: shortcut parity

优先复核：

```text
V label/active tool
L connection mode
Enter generate
Option+drag node/copy
Option+G storyboard merge
duplicate modifier and subgraph closure
```

这些 source-advertised 命令需要记录 precondition、focus、selection、cancel、graph/viewport/UI delta。它们不能由现有 Handle、局部 Enter 或普通 duplicate action“功能近似”代偿。

### 4.9 `LIBTV-PAR-008`: graph transaction hardening

这是 fidelity 工具的可靠性前置，不是视觉重构。当前 catalog 已记录：

- `setNodes`/`setEdges` 默认不记 history；
- `updateNodeData` 可产生 no-op history；
- graph snapshot 对 nested `data` 是浅复制；
- `addEdge` 缺少 duplicate/dangling/self-loop guard；
- 单节点 duplicate 与 selection duplicate 的 incident-edge 语义不同；
- selection 是 transaction output，但不是 history input；redo 清 selection；
- canvas lifecycle 不属于 graph undo。

后续必须先定义 guard、snapshot depth、selection policy 和 compatibility tests，再逐项改；不能借某个 UI slice 顺手重写整个 store。

Connection 子切片已完成 Batch 57 的本地 structural runtime slice。权威入口仍是 [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)，Batch 57 记录与 verifier 见 [`liblib-canvas-batch57-2026-08-27/`](liblib-canvas-batch57-2026-08-27/)：result/reason、guard precedence、reject 零 mutation、accepted one-step history、`LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` 已在 clone fixture 上闭环。它只能标记为 `STRUCTURAL_SLICE_RECORDED_PASS`，不能升级为完整 connection parity；Reference、domain compatibility、invalid feedback、导入/批量/同步仍 blocked。

Document/snapshot 子切片的设计前置也已完成，权威入口是 [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)：runtime/history/portable document/clipboard/persistence 五层、V1 schema、strict load、nested isolation、`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` 和 `LIBTV-VR-010` 均已定义。它同样是 `RUNTIME_MISSING`，普通画布 import/export/persistence 未实现；该合同不代替 connection/copy runtime。

Subgraph copy 子切片的设计前置见 [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)：具名 command、descendant closure、two-pass identity、parent detach/remap、node-data reference roles、edge policy、flow placement、atomic history、`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` 和 `LIBTV-VR-011` 已定义。当前 Batch 3/5/8 runtime 只是 `PARTIAL`，single-node incident edge 是 compatibility hold；system clipboard 和 Option-drag 仍 blocked。

Node data identity 子切片已经完成 fixed static audit 与规范设计，权威入口是 [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md) 和 [`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)：11-type V0 registry、field roles、named operation profiles、shot reciprocal aggregate、long-video process cohort、Director shell/workspace boundary、media locator、`LIBTV-FIX-LOCAL-NODE-DATA-01` 和 `LIBTV-VR-012` 已定义。Runtime 仍使用 generic Node/Record 与浅 data spread；shot/process delete cascade 继续需要 source/product decision。

Delete/reference repair 子切片也已完成设计，权威入口是 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)：当前 destructive entry、Open Canvas 方法边界、relation inverse index、aggregate/UI/resource impact、cascade/detach/reset/block 队列、`LIBTV-FIX-LOCAL-GRAPH-DELETE-01`、`LIBTV-FIX-SOURCE-GRAPH-DELETE-01` 和 `LIBTV-VR-013` 已定义。Batch 58 已实现其中 clone-owned 的 node-bound UI owner invalidation slice；runtime 仍只做 descendants/incident-edge filter，derived、shot、process、Director workspace/resource 和 source cascade/detach 用户语义保持 source/product-blocked。

Batch 58 的实现入口是 [`liblib-canvas-batch58-2026-08-27/`](liblib-canvas-batch58-2026-08-27/)：`ImagePreviewState`、`ImageAnnotateState`、`ImageElementEditState` 和 Director owner 都携带 canvas identity；纯 reconciliation 只关闭失效 UI owner，不写 graph/history。它不能替代 `LIBTV-VR-013` 的 relation-aware planner。

Graph ingress 子切片也已完成全入口静态审计与设计，权威入口是 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：Open Canvas store/save/API/revision/server-patch 分层与 clipboard/framework delta 反例、clone direct writers、T0-T5、full-draft command plan、`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` 和 `LIBTV-VR-014` 已定义。Runtime 只有 Batch 57 connection/addEdge island 受保护；transport whitelist、derived/copy/delete plan、history restore 和 remote authority 未实现。

其中 React Flow framework delta 已完成独立细化，权威入口是 [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：两个项目共同的 12.11.1 variant/reducer 语义、Open Canvas current-state 正面模式与 generic acceptance 反例、clone render-closure/whole-array/mixed-batch 风险、T0 selection、T1 existing-node position/passive measurement、semantic reroute、runtime-field sanitation、`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` 和 `LIBTV-VR-016` 已定义。Runtime 仍未收窄；node resize/reconnect 保持 source/product-blocked。

Viewport/coordinate/gesture/placement 也已完成 fixed audit 与正式设计，权威入口是 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：actual React Flow host、six coordinate domains、live/stable/bootstrap/target phases、gesture/operation owner、entry-specific placement、resize reconciliation、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 和 `LIBTV-VR-020` 已定义。它横跨 `PAR-001/002` overlay、`PAR-007` navigation、`PAR-008` graph placement 和 `PAR-011` canvas/UI owner；runtime 仍缺 actual-host default add、phase split、host epoch/generation owner 与 focused fixture，source exact add/fit/resize/drop 继续 gated。

Media ingress/resource lifecycle 已完成 Open Canvas/clone/source 三向 static audit 与正式设计，权威入口是 [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)：ten named entry profiles、validation/probe/materialization、ingress/attempt/cohort identity、temporary lease、stable asset/node reference、provisional/semantic projection、multi-item commit、last-known-good replace、reachability/release、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` 和 `LIBTV-VR-021` 已定义。它作为 `PAR-014` 横跨 `PAR-008` graph transaction、`PAR-009` result identity、`PAR-010` prototype honesty、`PAR-011` owner cleanup 和 `PAR-012` backend boundary；当前 upload/history 是 mock、Shot 是 local preview、Director data/blob 为独立 island，common runtime/fixture 未实现，source exact limits/progress/cancel/placement/register/restore 继续 gated。

多画布 lifecycle 也已从“下拉菜单可操作”提升为 cross-owner correctness 合同，权威入口是 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)：Open Canvas summary/full record、URL/not-found、hydrate、per-canvas viewport、delete/run cleanup 与 stale save local convergence 正反面已审计；clone registry/document/history/session/external owner、create/switch/rename/duplicate/delete command matrix、switch manifest、`LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017` 已定义。它同时横跨 `PAR-008` graph owner 与 `PAR-011` UI owner；runtime 仍缺 invalid target guard、demo viewport ownership、page transaction generation、late callback 和 async/resource isolation。

Async result ingress 也已完成 implementation 前的双向静态审计，权威入口是 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：Open Canvas descriptor/run/runId polling/server patch/revision/saved baseline 的可借结构与 expected-run/source-version/field-owner/two-write 缺口、clone 7 类 delayed/Director completion、operation envelope、freshness disposition、selection/history/resource、`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` 和 `LIBTV-VR-015` 已定义。Runtime 仍没有共同 operation owner；当前短 timer 只算 `PROTOTYPE_LATENCY`，不能升级为真实 task lifecycle。

Command outcome 与 feedback ownership 已完成独立设计，权威入口是 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)：Open Canvas global toast、node status/error、save/conflict、field/pending 的分层正面证据，以及 localized message matching、owner-less async announcement 反例均已固定；clone connection reason、local string status、VideoNode timer 和 Director persistent progress/error/retry 已纳入同一 disposition/reason/primary-surface/owner lifecycle。它横跨 `PAR-004` connection invalid feedback、`PAR-008` graph command、`PAR-009` async process 和 `PAR-011` surface lifecycle；`LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` / `LIBTV-VR-018` 尚未实现，且不得因 Open Canvas 使用 Sonner 就默认新增 LibTV global toast。

### 4.10 `LIBTV-PAR-009`: process and result lifecycle

逐帧拉片、片段重拍和超长视频已经有有界 clone prototype，但 source 的处理中/失败/部分成功/重试/局部重算/版本替换仍不完整。进入实现前需要：

- disposable video/process fixture；
- source ID、media version、time range、operation、candidate/result identity；
- run/node/save status 分离；
- completion 的 run/attempt/result envelope、current/stale/duplicate/invalid disposition 和 operation-specific field ownership；
- one transaction 的 node/edge/selection/history 期望；
- delete/undo/retry race、projection recovery 与 blob/temp resource transfer/release；
- 不伪造真实 provider progress、费用或输出质量。

### 4.11 `LIBTV-PAR-010..014`: boundaries

| ID | 当前决策 |
|---|---|
| `010` | Agent/Share/Toolbox/History/AddNode resource action 继续使用显式 local feedback。只有源站可见结构/生命周期差距值得继续复刻；不把“按钮可点”升级成真实服务。 |
| `011` | 冗余 primary booleans、Notification/UserMenu unmounted state、`toggleGrid` 无 caller 已记录。等相关 store 获得编码授权或新入口证据时再清理。 |
| `012` | Provider、上传、计费、远端任务、账号和协作持久化需要新的产品/后端合同，当前不排入前端 parity 实施。 |
| `013` | Batch 48 已完成 browser-local model descriptor/persistence、focused verifier、截图台账和成熟度评估；真实 mesh loading、远程同步和 LibTV 生产持久化仍不在合同内。后续只读其历史合同，不把 clone-only 结果升级为源站事实。 |
| `014` | media intent、local byte/lease、stable asset、node reference 和 provisional/semantic projection 必须分权；只允许 validation/local preview/fake materializer 的 honest prototype，真实 upload/storage/provider 仍归 `PAR-012 OUT_OF_SCOPE`。 |
| `DIR-001` | Batch 50 已完成 clone-owned workspace collapse/restore、viewport expansion、mobile drawer recovery、focus owner、page shortcut isolation、editable-target guard 和 Escape layering；LibTV Director shell exact DOM/CSS、完整 focus trap 和 source “全屏”语义仍是 `UNKNOWN`，后续只读其历史合同，不升级为 source parity。 |
| `DIR-002` | Batch 59 已完成资源搜索、preview-only selection、显式加入 proxy object、对象树/Inspector continuity 和 desktop/mobile focused verifier；卡片主体仍保留 Batch 47 快速加入兼容路径。真实 FBX/OBJ mesh、远程资源和认证后 LibTV 资源库 DOM/CSS 仍是 `UNKNOWN`。 |

## 5. Dependency Order

```text
source freshness refresh (PAR-005)
  -> top-level keyboard/focus decision (PAR-004)

standard selected image (PAR-001)
  -> low-risk active surfaces (PAR-002)
  -> high-risk image actions only after disposable fixture

typed identity/session design (PAR-003)
  -> Auto Link implementation

graph transaction guards (PAR-008)
  -> graph-mutating active tools/process results

media ingress/resource design (PAR-014)
  -> honest local fixture/profile
  -> only then authorized Add Resource/replace/history/asset slices

disposable ready-video/process fixture
  -> PAR-006 / PAR-007 source-only commands / PAR-009
```

不要把 dependency order 误读成“大版本”。每个节点仍应形成一个可独立评审、验证、撤销的 batch。

## 6. Work Waves

### Wave A: research/documentation only

当前无需编码授权即可继续：

1. 按 `PAR-005` 对 page shell/top-level surface 做安全只读 freshness refresh；
2. 建立 disposable fixture catalog，列出 image/ready-video/process/shortcut 所需状态；
3. 给 historical/current verifier assertion 加版本标签和 replacement plan；
4. 为 `PAR-003` 写 typed Auto Link data/state/transaction design；
5. 将新的 source claim 追加到 traceability matrix，不静默改旧快照。
6. 维护 `PAR-014` 的 source decision queue，只有独立 disposable fixture 才取 exact limits/progress/cancel/placement/register/restore；共享画布保持只读。

### Wave B: authorization-ready local slices

明确编码授权后优先：

1. `PAR-001` standard selected image；
2. `PAR-002` Preview；
3. `PAR-002` Annotate empty；
4. `PAR-002` Element Edit empty。

每项单独实施、单独 verifier、单独 screenshot ledger、单独 commit/push。

### Wave C: fixture-dependent

- ready-video toolbar/segment workflows；
- source-only shortcuts；
- shot-breakdown/long-video live lifecycle；
- rotate/layer separation/dirty save/download。
- source media upload/history/asset/Shot lifecycle exact parity。

### Wave D: new product scope

- real Provider、upload、billing、account persistence、remote task polling；
- production model parsing/assets/licenses beyond the bounded Director plans。

## 7. Batch Entry Template

后续 agent 从本文选一个 item 时，先落下：

```text
Backlog ID:
User-visible goal:
Source fact and date:
Clone fact and stable commit:
Exact delta:
Out of scope:
Route/store/components:
Graph/selection/history delta:
Fixture and reset method:
Desktop/mobile/zoom states:
Selectors and assertions:
Source/clone evidence outputs:
Authorization status:
Stop conditions:
```

任何字段为空时保持 research/plan，不开始编码。

## 8. Completion Rules

一个 backlog item 只能在以下条件同时满足时标记 parity slice complete：

1. source fact、inference 和 clone decision 分开；
2. 当前 delta 在稳定 commit 上重新确认；
3. 明确 graph/viewport/selection/local-state 副作用；
4. desktop/mobile 和必要 zoom/edge-clipping 状态有断言；
5. focused verifier、console/page/request error checks 和 repository gate 有记录；
6. implementation/screenshot history 落档；
7. commit 已 push；
8. 没有把 local mock 或 bounded proxy 误写成真实后端/source 完成度。

“已经有按钮”“历史 Batch 曾通过”“截图看起来接近”都不能单独满足完成条件。

## 9. Maintenance

发生以下事件时更新本文：

- 新源站日期改变 action、geometry、lifecycle 或 fixture 可用性；
- clone slice 获得授权、实施、验证或被 supersede；
- verifier 从 historical compatibility 升级为 current source contract；
- graph/overlay/shortcut catalog 暴露新的跨组件风险；
- parallel WIP 稳定或边界前移。

本表只保留当前优先级。旧优先级变化应在 Changelog/实施记录/Documentation Audit 中保留原因，不复制一份新的“最终 backlog”。

## 10. Related Documents

- [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)
- [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)
- [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)
- [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)
- [`../DECISION_REGISTER.md`](../DECISION_REGISTER.md)
- [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)
- [`components/LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md)
