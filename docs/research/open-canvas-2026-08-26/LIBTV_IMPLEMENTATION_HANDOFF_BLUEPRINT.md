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
| `OC-BP-004` graph transaction hardening | `OC-ADOPT-004..006/016/017` | `LIBTV-PAR-008` | connection/document/copy/data/delete/entrypoint contracts complete；runtime maturity 按 verifier 独立维护 | `GRAPH-CONNECTION-01` + `GRAPH-DOCUMENT-01` + `SUBGRAPH-COPY-01` + `NODE-DATA-01` + `GRAPH-DELETE-01` + `GRAPH-ENTRYPOINT-01` 设计完成 | `LIBTV-VR-009..014` 有 authority；Reference/domain/invalid lifecycle/Option-drag/cascade/detach and runtime ingress migration remain open |
| `OC-BP-005` process/result lifecycle | `OC-ADOPT-003/009` | `LIBTV-PAR-009` | `BLOCKED_BY_FIXTURE` | `LIBTV-FIX-LOCAL-LONG-PROCESS-01` + 所需 source fixture | `LIBTV-VR-007` |
| `OC-BP-006` capability projection audit | `OC-ADOPT-010` | Seedance 参数研究 | `RESEARCH_ONLY` | source read-only + local parameter states | 新立项前不新增 verifier |

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

基础 fixture 使用 `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`、`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01`、`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01`、`LIBTV-FIX-LOCAL-NODE-DATA-01`、`LIBTV-FIX-LOCAL-GRAPH-DELETE-01`、`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01`、`LIBTV-FIX-LOCAL-EMPTY-01`、`LIBTV-FIX-LOCAL-DEMO-01`、`LIBTV-FIX-LOCAL-GROUP-01` 和 `LIBTV-FIX-LOCAL-DERIVED-01`。六个专项 fixture 的 topology/corpus、scenario reset 和 `LIBTV-VR-009..014` split 已有设计 authority；各自 runtime maturity 必须回到 verifier/fixture ledger，不能用共享源站验证 destructive graph guard。

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

Open Canvas 的 node/run/save 分层在这里是高价值设计输入，但 current runner、轮询和保存实现不进入 clone。

完整的五轴状态、能力投影、stale/retry 规则和 fixture 接收规格见 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。

## 10. `OC-BP-006`：模型能力投影审计

这项保持文档态，输出一张三层矩阵：

| 层 | 需要记录 | 不能混入 |
|---|---|---|
| LibTV visible capability | 模型、模式、字段、默认值、禁用、费用提示、source 日期 | Open Canvas registry 宣称 |
| clone UI capability | 当前组件实际可见和 local feedback | 真实 API 支持声明 |
| execution capability | adapter、request、polling、error、result write-back 的已证明范围 | 仅凭模型菜单或 descriptor |

Open Canvas 的 registry/current runner 漂移（`OC-006..009/016`）应作为审计反例。当前 `LIBTV-PAR-012` 仍是 `OUT_OF_SCOPE`，所以本文不规划 provider 接入。

完整的 source-visible catalog、Seedance 2.5 control projection、UI/descriptor/adapter/run 分层和未决问题见 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)。

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

在仍然只有文档授权的当前阶段：

1. `OC-BP-003` 的 fixture/data/state/transaction 设计已完成；保持为 `DESIGN_READY`，直到运行 fixture 获授权并实现；
2. `OC-BP-004` 的 connection、document/snapshot、subgraph copy、node data identity、relation-aware delete 和 entrypoint authority schema/result/fixture/`LIBTV-VR-009..014` 设计已完成；下一步按 verifier 维护 runtime maturity，优先收窄 transport/command/restore 旁路，并继续补 Reference/导入/批量/同步/Option-drag/cascade/detach source/product 决定与 invalid lifecycle，不再新建同主题总览；
3. 以 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md) 继续补 source process evidence；固定本地状态矩阵设计已完成，运行 fixture 仍未授权；
4. 以 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) 维护模型/参数 source freshness；projection 审计已完成，不创建 provider backlog；
5. 继续按 `LIBTV-PAR-005` 做安全只读 freshness，更新受影响的 `L0`；
6. 保持 `OC-BP-001/002` 为可单独申请授权的最小视觉 slice；
7. 保持 provider、真实保存和共享源站 mutation 在边界外。

这套顺序让文档继续降低实施风险，同时不越过用户当前的“只研究、不编码”约束。
