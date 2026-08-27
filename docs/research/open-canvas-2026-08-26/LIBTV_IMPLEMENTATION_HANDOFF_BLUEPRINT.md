# Open Canvas 启发下的 LibTV 实施交接蓝图

> 状态：`CURRENT_RESEARCH` / `CURRENT_GUIDANCE`
>
> 当前授权：文档与研究 `GO`；修改 `src/`、测试脚本或共享源站状态 `NO-GO`
>
> 用途：把 [`ADOPTION_DECISION_MATRIX.md`](ADOPTION_DECISION_MATRIX.md) 中的高价值机制整理成可独立授权、实施、验证和回退的 LibTV 纵向 slice。本文不是编码计划的批准文件。

## 1. 蓝图定位

Open Canvas 提供的是成熟问题的参考解法，LibTV 源站提供的是复刻真相，当前 clone 提供的是改动边界。实施交接必须同时持有这三种输入：

```text
Open Canvas mechanism
  -> exposes a design question
LibTV source contract
  -> defines visible behavior and side effects
Current clone runtime
  -> defines the smallest ownership boundary
Fixture + verifier
  -> proves the authorized delta without collateral changes
```

缺少其中任何一层时，不进入代码。尤其不能从 Open Canvas 的可运行实现直接跳到 LibTV 组件修改。

## 2. 纵向交接的七层

| 层 | 必须回答 | 正式输入 | 交付物 | 不通过时的停止点 |
|---|---|---|---|---|
| `L0 Evidence` | LibTV 当前表现和 Open Canvas 启发分别是什么 | dated live audit、bundle、`OC-*` claim | source fact / inference / clone decision 分栏 | 继续只读取证 |
| `L1 Identity` | 被操作的 node、media、version、reference、run 是谁 | component contract、typed pattern card | identity、owner、生命周期和序列化边界 | 只写设计合同 |
| `L2 Transaction` | 一个用户动作精确改变什么 | graph transaction catalog、history policy | precondition、node/edge/data/selection/history delta | 不写 store action |
| `L3 Surface` | surface 在哪一层挂载、如何定位和关闭 | UI hierarchy、overlay catalog、source geometry | mount owner、anchor、focus/Escape/outside/replacement | 不改 JSX/CSS |
| `L4 Fixture` | 如何稳定构造、隔离和复位 | fixture catalog | fixture ID、setup、allowed actions、reset assertions | `BLOCKED_BY_FIXTURE` |
| `L5 Verifier` | 什么断言能证明 current contract | replacement map、Harness、historical verifier | selectors、geometry/state/delta/errors、evidence paths | 不替换旧断言 |
| `L6 Provenance` | 谁授权、改了什么、结果如何 | single-slice PLAN/IMPLEMENTATION | commit、push、screenshot ledger、known gaps | 不标 complete |

Open Canvas 的借鉴主要进入 `L1/L2`，坐标方法可进入 `L3`。它不能单独完成 `L0`，也不能替代 `L4/L5`。

## 3. 交接状态机

```text
RESEARCH_ONLY
  -> EVIDENCE_READY
  -> DESIGN_READY
  -> FIXTURE_READY
  -> READY_FOR_AUTHORIZATION
  -> AUTHORIZED_IMPLEMENTATION
  -> FOCUSED_VERIFIED
  -> COMPATIBILITY_VERIFIED
  -> RECORDED_PASS
```

| 状态转换 | 必要条件 |
|---|---|
| `RESEARCH_ONLY -> EVIDENCE_READY` | 有 dated LibTV 事实、Open Canvas claim、clone delta 和不可推出结论 |
| `EVIDENCE_READY -> DESIGN_READY` | `L1-L3` 的身份、事务、surface ownership 已落档 |
| `DESIGN_READY -> FIXTURE_READY` | 本地 fixture 可重复构造；有副作用的源站研究已有 disposable fixture |
| `FIXTURE_READY -> READY_FOR_AUTHORIZATION` | 最小文件边界、out of scope、verifier 和停止条件完整 |
| `READY_FOR_AUTHORIZATION -> AUTHORIZED_IMPLEMENTATION` | 用户明确授权该 slice；不能用“继续推进”推断编码许可 |
| `AUTHORIZED_IMPLEMENTATION -> FOCUSED_VERIFIED` | focused verifier、截图和错误收集通过 |
| `FOCUSED_VERIFIED -> COMPATIBILITY_VERIFIED` | 仓库 gate 和必要 serial regression 通过，其他 WIP 未被覆盖 |
| `COMPATIBILITY_VERIFIED -> RECORDED_PASS` | 实施记录、证据、commit 和 push 完整 |

任何新 source drift 会把受影响 slice 退回 `EVIDENCE_READY`；fixture 不再可重置则退回 `DESIGN_READY`。

## 4. Slice 总览

| Blueprint | 对应决策 | Parity | 当前状态 | 主要 fixture | Replacement |
|---|---|---|---|---|---|
| `OC-BP-001` standard selected image | `OC-ADOPT-001` | `LIBTV-PAR-001` | `READY_FOR_AUTHORIZATION`，但当前未授权 | `LIBTV-FIX-LOCAL-IMAGE-01` | `LIBTV-VR-001` |
| `OC-BP-002` low-risk active surfaces | `OC-ADOPT-001` | `LIBTV-PAR-002` | 分三个待授权 slice | `LIBTV-FIX-LOCAL-IMAGE-01` | `LIBTV-VR-002` |
| `OC-BP-003` typed Auto Link | `OC-ADOPT-002` | `LIBTV-PAR-003` | `DESIGN_READY`；运行 fixture 未实现 | `LIBTV-FIX-LOCAL-AUTOLINK-01` 接收规格已完成 | `LIBTV-VR-003..005` |
| `OC-BP-004` graph transaction hardening | `OC-ADOPT-004..006/016/017/019` | `LIBTV-PAR-008` | connection 与 React Flow routing 有 focused runtime；document/copy/data/delete/entrypoint 保持 design/partial | `GRAPH-CONNECTION-01` + `REACT-FLOW-CHANGES-01` 已运行；其余 fixture 设计完成 | `LIBTV-VR-009/016` focused pass，`VR-010..014` 按各自 maturity；Reference/domain/invalid lifecycle/Option-drag/resize/reconnect/cascade/detach and other runtime ingress remain open |
| `OC-BP-005` process/result lifecycle + async ingress | `OC-ADOPT-003/009/018` | `LIBTV-PAR-009` | state/ingress design complete；runtime/source blocked | `LOCAL-PROCESS-STATES-01` + `LOCAL-ASYNC-INGRESS-01` + 所需 source fixture | `LIBTV-VR-007/015` |
| `OC-BP-006` capability projection audit | `OC-ADOPT-010` | Seedance 参数研究 | `RESEARCH_ONLY` | source read-only + local parameter states | 新立项前不新增 verifier |
| `OC-BP-007` multi-canvas lifecycle isolation | `OC-ADOPT-020` | `LIBTV-PAR-008/011` | design complete；Batch 16/58 islands recorded；cross-owner runtime partial | `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` | `LIBTV-VR-017` |
| `OC-BP-008` command outcome/feedback ownership | `OC-ADOPT-021` | `LIBTV-PAR-004/008..011` | design complete；local reason/status/timer/Director islands；common runtime missing | `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` | `LIBTV-VR-018` |
| `OC-BP-009` selection/focus/command-context ownership | `OC-ADOPT-022` | `LIBTV-PAR-004/007/008/011` | static/design complete；node projection/modal/Director islands；common runtime missing | `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` | `LIBTV-VR-019` |
| `OC-BP-010` viewport/coordinate/gesture/placement authority | `OC-ADOPT-023` | `LIBTV-PAR-001/002/007/008/011` | static/design complete；viewport/navigation/placement/overlay islands；common runtime/source parity partial | `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` | `LIBTV-VR-020` |
| `OC-BP-011` media ingress/resource lifecycle authority | `OC-ADOPT-024` | `LIBTV-PAR-008/009/010/011/014` | static/design complete；mock/local-preview/data/blob islands；common runtime missing or partial、source parity partial | `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` | `LIBTV-VR-021` |
| `OC-BP-012` foreground editor session/commit/history authority | `OC-ADOPT-025` | `LIBTV-PAR-004/008/009/011/015` | static/design complete；ten profile runtime islands；common owner missing、source parity partial | `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` | `LIBTV-VR-022` |
| `OC-BP-013` media rendition/aspect/node geometry authority | `OC-ADOPT-026` | `LIBTV-PAR-001/002/008/009/011/014/015/016` | static/design complete；source-shaped landscape island；generic/derived/Director/editor runtime fragmented、source ratio-diverse parity gated | `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` | `LIBTV-VR-023` |

表中的 Open Canvas decision 只解释设计输入。实施优先级仍以 [`../LIBTV_UIUX_PARITY_BACKLOG.md`](../LIBTV_UIUX_PARITY_BACKLOG.md) 为准。

## 5. `OC-BP-001`：标准图片双浮层

### 5.1 目标与边界

**用户可见目标**：选中标准图片节点后，上方工具条和下方编辑面板各自稳定跟随节点，在当前动作集合、多 zoom、边缘裁切和 selection 变化下符合 LibTV current source。

**借鉴 Open Canvas 的内容**：用 measured node 与 live viewport 形成统一测量输入，显式区分 flow/screen 坐标。

**不得借鉴的内容**：Open Canvas 的 Panel DOM、gap、clamp、尺寸、动作集合和 portal 层级。

### 5.2 实施交接包

| 层 | 当前合同 |
|---|---|
| `L0` | `LIBTV-TR-002..006`、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md) |
| `L1` | anchor identity 是当前单选 node；多选、失焦、virtualization 卸载 surface |
| `L2` | 纯 UI selection state；打开/关闭不得改变 graph count/history |
| `L3` | top toolbar 是 screen-space host；bottom panel 是 node-internal flow offset + inverse zoom；共享 center，不共享 containing block |
| `L4` | `LIBTV-FIX-LOCAL-IMAGE-01`；source 只做 dated read-only comparison |
| `L5` | `LIBTV-VR-001`：动作 ID/order/尺寸、两类 gap、center、desktop/mobile/zoom、natural clipping |
| `L6` | 单独 Batch、单独 screenshot ledger、单独 commit/push |

获授权后候选 ownership 边界仅包括 [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx)、[`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx)、[`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx) 和对应窄 verifier。实际修改前必须重新确认这些文件没有并行 WIP。

**禁止顺手扩大**：active tool、Auto Link、graph transaction、视频 toolbar、全局 overlay manager、viewport clamp。

## 6. `OC-BP-002`：低风险 active surfaces

`Preview`、`Annotate empty`、`Element Edit empty` 必须是三个独立 slice：

| Slice | Surface ownership | 核心断言 | 明确排除 |
|---|---|---|---|
| Preview | page-level L4 overlay | standard double overlay 被替换；close/Escape 后 selection 与 graph 不变 | 下载、水印、会员、保存 |
| Annotate empty | node authoring L3 | dedicated toolbar + DPR canvas；discard 恢复标准态 | 实际绘制、dirty save、派生结果 |
| Element Edit empty | node authoring L3 | dedicated toolbar/stage/empty record；本地 history disabled | 有效 record、mask 生成、上传和任务 |

Open Canvas 在本组只提醒 agent 显式定义 selected editor/action overlay 的 mount owner。LibTV 的 replacement 关系以 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md) 和 [`../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) 为真相。

每个 slice 使用 `LIBTV-FIX-LOCAL-IMAGE-01`，分别形成 `LIBTV-VR-002` 的 focused 场景。dirty annotate、旋转、图层分离不能借 empty surface 的授权进入代码。

## 7. `OC-BP-003`：Typed Auto Link

### 7.1 先完成的设计产物

在任何实现前，必须明确以下身份相互独立：

```text
graph edge
reference role
candidate identity
ghost session
committed mention token
media version
provider projection
```

Open Canvas 的 typed bucket 只证明“结构化身份在边界层投影”是可行方法。LibTV 正式 mention 仍以 [`../components/LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md) 的 stable node ID、media type、ordinal 和当前 source 行为为准。

### 7.2 状态与事务交接

| 维度 | 必须落档 |
|---|---|
| preference | 图片/视频共享范围、默认值、持久化 owner、关闭后的 cleanup |
| candidate | connected/reference pool、稳定 key、排序与 stale invalidation |
| ghost | 不改 committed text；click/Tab 单项、Shift+Tab 全量、Escape/blur/edit/IME cleanup |
| mention | node/media identity 与显示 label 分开；reference reorder 只更新 ordinal |
| transaction | 未连接素材的 connect + reference + mention 成功边界；失败 rollback；undo/redo policy |
| projection | editor state 到模型请求的单向派生，不让 provider 字段反向成为 UI 身份 |

候选 ownership 边界包括 [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx)、[`VideoGenerationPanel.tsx`](../../../src/components/VideoGenerationPanel.tsx)、[`canvasStore.ts`](../../../src/store/canvasStore.ts) 及后续明确的 typed helper。当前这些只是接力定位，不是修改授权。

**进入实现的缺口**：typed identity/state/transaction、fixture topology、deterministic controls、setup/reset 和 `LIBTV-VR-003..005` 拆分已经完成文档设计；但 `LIBTV-FIX-LOCAL-AUTOLINK-01` 仍不是可运行资产，也没有编码授权。后续实现必须提供 deterministic delay、IME、竞争 popover 和失败 transaction；共享源站仍禁止输入 Prompt 或接受候选。

## 8. `OC-BP-004`：Graph Transaction Hardening

### 8.1 借鉴边界

可以借：versioned schema、validation pipeline、type compatibility、cycle/self/dangling/duplicate guard、subgraph ID map、内部边闭包，以及集中 deletion/conflict no-op 的方法。

不能借：Open Canvas 的 node type、edge direction、clipboard payload、DAG 产品约束、store shape 和 scene/provider 字段。

### 8.2 分解顺序

1. **Invariant contract**：合法 ID、endpoint、direction、duplicate/self/cycle、parent-child/group/derived compatibility；
2. **Snapshot contract**：nested data 深度、version、migration、selection/viewport 是否属于 history；
3. **Transaction contract**：guard、graph delta、selection output、history step、failure/no-op；
4. **Copy contract**：selected closure、group descendants、internal/external edges、ID map、placement；
5. **Compatibility verifier**：先纯逻辑 fixture，再真实 UI gesture；保留当前 edge flow 和 Handle affordance。

其中 connection 子切片已有独立 [`LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)：统一 raw/normalized connection、`allow / allow-with-adjustment / reject / unknown` 结果、stable reason、guard precedence、reject 零 mutation 和 accepted one-step history。`unknown` 用于保留 Reference、未建模 action 和未确认入口，不允许 silent allow。

Document/snapshot 子切片已有独立 [`LibTVGraphDocument.contract.md`](../components/LibTVGraphDocument.contract.md)：分开 runtime、history、portable document、clipboard packet 和 future persistence envelope，定义 V1 schema、nested isolation、strict load/migration 和 zero-partial transaction。Open Canvas revision/file/KV/rebase 不进入近期 scope。

Subgraph copy 子切片已有独立 [`LibTVSubgraphCopy.contract.md`](../components/LibTVSubgraphCopy.contract.md)：以具名 command 替代 `includeEdges` boolean，定义 descendant closure、two-pass node/edge map、parent detach/remap、reference role、edge policy、flow placement 和 one-step transaction。Current single-node incident-edge branch 只保留为 compatibility hold。

Node data identity 子切片已有 dated [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md) 和规范 [`LibTVNodeDataIdentity.contract.md`](../components/LibTVNodeDataIdentity.contract.md)：固定 11 runtime types，定义 V0 field roles、named operation profiles、shot/process aggregate、Director shell/workspace 和 media locator boundary。

Delete/repair 子切片已有 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)：固定 Open Canvas 简单 deletion 的可借方法与 LibTV 领域差异，定义 relation inverse index、structural/aggregate/UI/resource impact、cascade/detach/reset/block policy、stable reason 和 full-plan transaction。

Entry-point authority 子切片已有 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：固定 Open Canvas 多层 defense 与 partial ingress 反例，审计 clone 全 direct writer，并定义 T0-T5、transport whitelist、full-draft plan、restore/remote boundary 和 routing verifier。

基础 fixture 使用 `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`、`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01`、`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01`、`LIBTV-FIX-LOCAL-NODE-DATA-01`、`LIBTV-FIX-LOCAL-GRAPH-DELETE-01`、`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01`、`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01`、`LIBTV-FIX-LOCAL-EMPTY-01`、`LIBTV-FIX-LOCAL-DEMO-01`、`LIBTV-FIX-LOCAL-GROUP-01` 和 `LIBTV-FIX-LOCAL-DERIVED-01`。七个专项 fixture 的 topology/corpus、scenario reset 和 `LIBTV-VR-009..014/016` split 已有设计 authority；各自 runtime maturity 必须回到 verifier/fixture ledger，不能用共享源站验证 destructive graph guard。

React Flow transport 是 `OC-BP-004` 的独立首批候选：[`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) 已定义 exact 12.11.1 variant、whole-batch classifier、current-store snapshot、T0/T1 allowlist、semantic reroute、drag history 和 runtime-field sanitation。对应 fixture `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` 与 `LIBTV-VR-016` 只收口 framework adapter，不顺手实现 resize/reconnect 或修改视觉。

该候选已在 [`../liblib-canvas-batch61-2026-08-27/`](../liblib-canvas-batch61-2026-08-27/) 完成 pure classifier、current-snapshot commit、edge session selection、route callback 收口和 focused verifier；真实 marquee 回归暴露的双 ingress 问题也已修复。该 pass 只证明 framework adapter slice，不表示 resize/reconnect、primary/focus 或其余 graph authority 已实现。

候选 ownership 边界是 [`canvasStore.ts`](../../../src/store/canvasStore.ts)、[`canvas.ts`](../../../src/types/canvas.ts) 和经评审后新增的纯 helper。禁止借某个 UI slice 顺手重写整个 store。

## 9. `OC-BP-005`：Process / Result Lifecycle

### 9.1 必须拆开的身份

| 身份 | 回答的问题 |
|---|---|
| source node | 哪个画布对象发起过程 |
| source media version | 任务实际消费哪个媒体版本 |
| operation | 拉片、重拍、续写、长视频的哪一种操作 |
| time range | 哪个区间被分析或替换，单位和端点是什么 |
| run | 一次执行、重试或局部重算的身份 |
| candidate/result | 中间候选、部分结果和最终选中输出的关系 |
| node status | 画布对象能否编辑、显示或继续作为输入 |
| save status | graph/local draft 是否保存，不等于 run 完成 |

### 9.2 当前停止条件

`LIBTV-FIX-LOCAL-LONG-PROCESS-01` 只证明 clone-owned 的 12 节点/22 边 pending topology。它不能证明真实 source 拆分、进度、失败、费用、局部重算或结果替换。进入 `LIBTV-VR-007` 前仍需要固定本地状态矩阵和获授权的 disposable source process fixture，或明确批准的 bounded local mock contract。

Open Canvas 的 node/run/save 分层在这里是高价值设计输入。进一步静态深读证明 current runner 的 descriptor、runId polling、独立 server patch 和 saved-baseline projection 也可作为控制面方法；但 fixed patch 不比较 expected current run/source version/field owner，run terminal 与 graph projection 也不是原子写入，因此 current runner、provider、generic patch 和保存实现都不进入 clone。

完整的五轴状态、能力投影、stale/retry 规则和 fixture 接收规格见 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。

### 9.3 Async ingress 交接

完整机械合同见 [`../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。任何 graph-producing completion 在实施前还必须回答：

| 层 | 必须具备 |
|---|---|
| operation identity | canvas/source/source media version、descriptor fingerprint、operation/run/attempt/result ID |
| freshness | current/stale/duplicate/invalid disposition 和 stable reason |
| field owner | run/result 可写字段与 user draft/graph identity 明确分开 |
| transaction | current graph 上重建并验证 full plan；accepted one commit，reject zero mutation |
| UI/history | completion 默认 preserve unrelated selection/surface；progress 不写 graph history；undo 不重放外部 side effect |
| recovery/resource | terminal envelope 可幂等重试 projection；blob/temp output transfer/release exactly once |
| fixture/verifier | `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` / `LIBTV-VR-015` |

如果未来获得编码授权，第一 slice 应是 deterministic shot-breakdown operation，不是 provider 接入：冻结 dimensions descriptor，覆盖 draft drift、delete/undo、retry/duplicate、selection preserve 和 stale zero-mutation。Long-video multi-node cohort 与 Director blob ownership 分开进入后续 slice。

## 10. `OC-BP-006`：模型能力投影审计

这项保持文档态，输出一张三层矩阵：

| 层 | 需要记录 | 不能混入 |
|---|---|---|
| LibTV visible capability | 模型、模式、字段、默认值、禁用、费用提示、source 日期 | Open Canvas registry 宣称 |
| clone UI capability | 当前组件实际可见和 local feedback | 真实 API 支持声明 |
| execution capability | adapter、request、polling、error、result write-back 的已证明范围 | 仅凭模型菜单或 descriptor |

Open Canvas 的 registry/current runner 漂移（`OC-006..009/016`）应作为审计反例。当前 `LIBTV-PAR-012` 仍是 `OUT_OF_SCOPE`，所以本文不规划 provider 接入。

完整的 source-visible catalog、Seedance 2.5 control projection、UI/descriptor/adapter/run 分层和未决问题见 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)。

## 10.1 `OC-BP-007`：Multi-Canvas Lifecycle Isolation

完整机械合同见 [`../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Batch 16/58 current clone + Open Canvas OC-035..039；source final/fallback/panel behavior remains explicit unknown |
| `L1 Identity` | project registry、canvasId、active generation、node/UI/operation/resource owner |
| `L2 Transaction` | create/switch/rename/duplicate/delete full plan/result；graph/viewport/history/selection exact |
| `L3 Surface` | node-bound close、projection rebind/close、global preference preserve、zoom/minimap target projection |
| `L4 Fixture` | deterministic A/B/C + page transient + fake completion/save + resource ledger |
| `L5 Verifier` | `LIBTV-VR-017` plus Batch 16/58 regressions |
| `L6 Provenance` | no Open Canvas route/list/persistence claims promoted to LibTV source truth |

## 10.2 `OC-BP-008`：Command Outcome And Feedback Ownership

完整机械合同见 [`../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-040..045` + current clone connection/local status/VideoNode/Director inventory；exact LibTV feedback remains source-specific |
| `L1 Identity` | command kind、disposition、reason/args、canvas/node/surface/operation/attempt owner |
| `L2 Transaction` | reject/noop/stale zero mutation/history；accepted domain/history delta；feedback excluded from document/history |
| `L3 Surface` | one primary field/control/node/surface/canvas/toast/modal owner；clear/retry/dedupe/aria/geometry exact |
| `L4 Fixture` | deterministic outcome injection + fake timer/announcement clock + A/B switch/delete/retry/burst/route isolation |
| `L5 Verifier` | `LIBTV-VR-018` composed with connection/delete/async/canvas/overlay verifier families |
| `L6 Provenance` | no Sonner skin/message/provider/save semantics or source-unconfirmed invalid style promoted to LibTV truth |

第一 authorized slice 不应是新增 global toast。应先选择一个现有 owner-local feedback island，将 string/boolean 分解为 stable disposition/reason，并证明 graph/history、timer、switch/delete 和 source geometry 均不回归。

## 10.3 `OC-BP-009`：Selection, Focus And Command-Context Ownership

完整机械合同见 [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-046..052` + dated clone static audit；exact LibTV multi-select/edge/Escape/focus behavior remains explicit partial |
| `L1 Identity` | active canvas/generation、node IDs、edge IDs、primary、focus zone/origin/return target、foreground surface/context |
| `L2 Transaction` | selection/focus/context zero semantic history；delete/undo/switch use named graph/lifecycle authority；stale owner cleanup exact |
| `L3 Surface` | editable/canvas/node control/modal/Director/route policy；single-layer Escape；acquire/contain/return/fallback |
| `L4 Fixture` | deterministic selection sets、focus zones、surface stack、A/B generations、delete/switch/undo/unmount/stale return cases |
| `L5 Verifier` | `LIBTV-VR-019` composed with React Flow routing、multi-canvas、overlay and shortcut regressions |
| `L6 Provenance` | no selected flags、conflict gate、default propagation or Radix product semantics promoted to LibTV truth |

第一 authorized slice 不应先引入全局 context/modal infrastructure。应从一个可界定 surface 的 Escape + focus return 或 edge-selection owner 收口开始，同时证明普通 canvas shortcut、editable isolation、graph/history 和 FrameOS route 均不回归。

## 10.4 `OC-BP-010`：Viewport, Coordinate, Gesture And Placement Authority

完整机械合同见 [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-053..060` + dated clone static audit；exact LibTV add/fit/zoom/resize/drop remains explicit partial |
| `L1 Identity` | route、canvas/generation、host/epoch、viewport phase/operation、gesture session、coordinate domain、placement intent |
| `L2 Transaction` | viewport/host/gesture zero semantic history；accepted placement exact graph/selection/history；stale/invalid/cancel zero residue |
| `L3 Surface` | actual React Flow host、live viewport、screen/flow dual anchor、host resize policy and existing LibTV overlay formula composition |
| `L4 Fixture` | deterministic A/B canvas、full/asset-open/compact host、nested/measured nodes、viewport operation clock and layout/gesture cases |
| `L5 Verifier` | `LIBTV-VR-020` composed with overlay、React Flow routing、multi-canvas、copy、organize and shortcut regressions |
| `L6 Provenance` | no Quick Add/drop/pending connection、Open Canvas menu/zoom/pan/overlay/persistence or source-unconfirmed placement promoted to LibTV truth |

下一批已授权的最小实施入口是 actual-host default add：读取 current React Flow host、以 current live instance 做一次 center-to-flow conversion，并保持现有 add data、selection、history 和 UI。不要在同一 slice 同时重写 viewport phase、全部 placement、resize、overlay 或增加 Open Canvas 产品入口。

## 10.5 `OC-BP-011`：Media Ingress And Resource Lifecycle Authority

完整机械合同见 [`../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-061..070` 正反面 + clone dated static audit + LibTV source `LIBTV-SRC-MIR-001..006`；exact limits/progress/cancel/placement/register/restore 保持 partial |
| `L1 Identity` | ingress、attempt、cohort、route/canvas/generation、target node/version、source item、local lease、stable asset、node reference 和 locator provenance |
| `L2 Transaction` | validation/probe/materialization/freshness 后形成 full projection；provisional zero semantic history；accepted cohort exact one graph step；invalid/noop/stale/cancel zero residue |
| `L3 Surface` | Add Resource、Generated History、Material Library、Asset Manager、Shot Breakdown 和 Director 保持不同 owner；replace 保留 last-known-good；feedback 靠近 operation item |
| `L4 Fixture` | synthetic in-memory files、deterministic probe/fake materializer、A/B generation、resolver clock、asset/reference/reachability ledger、object URL create/revoke counters |
| `L5 Verifier` | `LIBTV-VR-021` 与 graph ingress/history、async、delete、document/copy、multi-canvas、feedback、viewport placement 和 Director isolation 组合 |
| `L6 Provenance` | 不把 Open Canvas MIME/size/storage/provider/placeholder skin、clone 历史素材文案或 source 未证 lifecycle 升级为 LibTV truth |

未来若获得编码授权，第一 slice 仍不应接真实上传。建议先落一个纯 descriptor/classifier/probe result 边界和 deterministic fake materializer fixture，或只让 Add Resource 形成 honest local-preview cohort；必须证明 `File`/`Blob`/object URL 不进入 semantic history/document，invalid/cancel/stale 零 graph residue，cleanup exact-once。不得同批重做 Asset Manager、Shot Breakdown、Director、真实 provider/storage 或 persistence。

## 10.6 `OC-BP-012`：Foreground Editor Session, Commit And History Authority

完整机械合同见 [`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-071..080` 正反面 + dated clone static audit；LibTV exact blur/Enter/Escape/outside/restore/save/close 继续 source-partial |
| `L1 Identity` | route、canvas/generation、editor session/profile、target node/source version、baseline digest、gesture、commit attempt、async/resource owner |
| `L2 Transaction` | native/local/graph history 分权；gesture endpoint one local snapshot；accepted commit exact one graph step 或 typed async handoff；invalid/noop/cancel/stale zero residue |
| `L3 Surface` | dirty/baseline drift、pending/failure/retry、last-known-good、close/focus return 与 enabled/disabled honesty；不把 panel close 当成功 |
| `L4 Fixture` | deterministic text/config/record/range/bitmap sessions、A/B canvas generation、drift/undo/redo/restore/close/async clock、byte/resource counters |
| `L5 Verifier` | `LIBTV-VR-022` 与 graph history/ingress、selection/context、multi-canvas、async/resource、feedback 和 overlay regression 组合 |
| `L6 Provenance` | 不把 Open Canvas 40-step full bitmap、JPEG/0.92、HTML schema、timeout、close-first/node-ID patch 或 clone inert control 升级为 LibTV truth |

未来若获得编码授权，第一 slice 应从一个小而确定的 correctness island 开始，例如 `TextNode` 的 semantic equality/no-op + dirty drift guard，或一个 enabled-looking inert control 的 honest disabled projection。不得在同批创建全局 form framework、重写十类 editor、接真实 upload/provider、统一所有 undo 栈，或改变未经 source 取证的 blur/Escape/close 行为。

## 10.7 `OC-BP-013`：Media Rendition, Aspect And Node Geometry Authority

完整机械合同见 [`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)。交接时必须逐层回答：

| Layer | Required handoff |
|---|---|
| `L0 Evidence` | Open Canvas `OC-081..090` 正反面 + dated clone/static source audit；LibTV portrait/square/video/mixed-output/resize 继续 source-gated |
| `L1 Identity` | route/canvas/generation、node、media/output、full/thumbnail locator/version、intrinsic provenance、request、frame/rendition/measurement revision |
| `L2 Transaction` | output selection + optional frame reflow + anchor preservation atomic；passive measurement/metadata refresh/detail open zero semantic history；invalid/noop/stale/source-required zero residue |
| `L3 Surface` | canvas image/video、candidate/reference/filmstrip、detail、full/visible editor、status/export 各有具名 fit/object-position/content-box policy |
| `L4 Fixture` | 16:9/2:1/1:1/9:16/odd ratio、thumbnail mismatch、poster/full video、mixed outputs、invalid metadata、known editor target 和 measurement clock |
| `L5 Verifier` | `LIBTV-VR-023` 与 overlay、viewport、React Flow routing、editor、graph history、media ingress、async、multi-canvas 和 preview regressions 组合 |
| `L6 Provenance` | 不把 Open Canvas fixed card/request aspect/visual/schema、clone ratio coincidence 或 source 未证 orientation/resize 升级为 LibTV truth |

若未来获得编码授权，第一 slice 应先实现 deterministic local fixture 和纯 frame/rendition decision，或只修正 generic/derived/Director still 中一个已证 ratio mismatch。不得同批增加 generic resize、重写所有 media schema/editor、接真实 provider/output history，或以全局 `object-fit` 替代 per-surface policy。

## 11. 单 Slice 计划模板

后续获得编码授权时，每个 Batch 的 `PLAN.md` 至少包含：

```text
Blueprint ID:
Parity ID:
Open Canvas decision/claim:
LibTV source facts and date:
Current clone fact and stable commit:
User-visible goal:
Exact delta:
Explicit out of scope:
L1 identity owner/lifecycle:
L2 graph/data/selection/history transaction:
L3 mount/anchor/focus/close behavior:
L4 fixture ID, setup, isolation and reset:
L5 verifier ID, selectors, assertions and evidence outputs:
Candidate file boundary:
Parallel-WIP check:
Authorization evidence:
Stop and rollback conditions:
Commit/push plan:
```

字段为空时不开始编码。候选文件边界不是必须修改清单，应在读取当前代码后进一步缩小。

## 12. 验证与交付顺序

```text
pure identity/transaction cases
  -> focused desktop runtime
  -> mobile/responsive when contract requires
  -> multi-zoom/edge/selection lifecycle when geometry requires
  -> graph/selection/history delta when mutation exists
  -> console/page/request errors
  -> repository check
  -> necessary serial compatibility run
  -> screenshot analysis + implementation history
  -> path-scoped commit + push
```

文档-only 设计不运行会覆盖固定截图的历史 verifier，避免干扰并行 WIP。实现后也不能通过删除或放宽旧断言制造通过；replacement protocol 以 [`../LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../LIBTV_VERIFIER_REPLACEMENT_MAP.md) 为准。

## 13. 完成定义

一个 Open Canvas 启发只能在以下条件全部满足时，标为某个 LibTV slice 的 `RECORDED_PASS`：

1. 上游事实、LibTV source fact、inference 和 clone decision 可分别追溯；
2. 实现没有扩大到未授权机制；
3. fixture 可重复、reset 有断言且没有触碰共享源站写入；
4. focused 与必要兼容验证通过；
5. source/clone screenshot 和解释同批落档；
6. 已记录剩余 unknown、prototype boundary 和 verifier maturity；
7. commit 已推送，且没有包含其他开发者 WIP；
8. 文档没有把 local mock、Open Canvas 能力或文章线索升级为 LibTV 真实后端。

## 14. 当前推荐顺序

当前阶段：

1. `OC-BP-003` 的 fixture/data/state/transaction 设计已完成；保持为 `DESIGN_READY`，直到运行 fixture 获授权并实现；
2. `OC-BP-004` 的 connection 与 React Flow T0/T1 routing 已有 focused runtime pass；document/snapshot、subgraph copy、node data identity、relation-aware delete、entrypoint authority 仍按 `LIBTV-VR-010..014` 分别维护。下一步不要重复实现 Batch 61 transport adapter，优先处理具名 command/restore 旁路，并继续补 Reference/导入/批量/同步/Option-drag/resize/reconnect/cascade/detach source/product 决定与 invalid lifecycle；
3. 以 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md) 继续补 source process evidence；固定本地状态矩阵设计已完成，运行 fixture 仍未授权；
4. 以 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) 维护模型/参数 source freshness；projection 审计已完成，不创建 provider backlog；
5. 继续按 `LIBTV-PAR-005` 做安全只读 freshness，更新受影响的 `L0`；
6. 保持 `OC-BP-001/002` 为可单独申请授权的最小视觉 slice；
7. `OC-BP-007` 保持 design complete/runtime partial；若获授权，先做 invalid target + switch transient isolation，再处理 duplicate/delete resource 和 background operation，不把多画布改造成 Open Canvas route/persistence；
8. `OC-BP-008/009` 均保持 design complete/runtime partial；feedback 从现有 owner-local island 收口，selection/context 从单一 surface 或 edge owner 收口，不新造 global toast/modal manager；
9. `OC-BP-010` 保持 design complete/runtime/source parity partial；Batch 63 先关闭 actual-host default add，再分开处理 live/stable viewport、generation-bound gesture 和 resize/overlay composition，不实现 Quick Add/drop/pending connection；
10. `OC-BP-011` 保持 design complete/runtime missing or partial/source parity partial；若获授权先做纯 classifier/probe/descriptor + fake materializer fixture，或 honest local-preview Add Resource cohort，不接真实 upload/storage，不合并 source 四类资源 surface；
11. `OC-BP-012` 保持 design complete/runtime fragmented/source parity partial；若获授权先关闭单一 profile 的 equality/drift/history/honesty 缺口，不统一重写所有 editor，也不接真实 provider/storage；
12. `OC-BP-013` 保持 design complete/runtime fragmented/source ratio-diverse parity gated；若获授权先做 deterministic fixture + pure policy，或关闭一个 generic/derived/Director still mismatch，不增加 generic resize/真实 output history；
13. 保持 provider、真实保存和共享源站 mutation 在边界外。

这套顺序让文档继续降低实施风险，同时不越过用户当前的“只研究、不编码”约束。
