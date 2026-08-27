# Batch 61 计划：React Flow Change Routing 与运行态选择权威

> 状态：`PLAN_RECORDED` / `IMPLEMENTATION_NOT_STARTED`。
>
> 计划基线：`4202890`，`master == origin/master`，工作区在建档前干净。
>
> 日期：2026-08-27。
>
> 风险等级：中高。视觉不应变化，但该批触及普通画布 selection、drag、
> measurement、edge selection 和 graph callback 入口。

## 1. 候选排序与本轮决策

本轮先比较 Open Canvas 专题已经形成正式合同、但尚未进入 runtime 的高价值
候选。分数沿用 parity backlog 的 `V/E/T/R` 口径。

| 候选 | V | E | T | R | 当前阻塞 | 决策 |
|---|---:|---:|---:|---:|---|---|
| React Flow change routing | 4 | 5 | 4 | 3 | 仅缺本地 adapter/fixture 编码 | **Batch 61** |
| Multi-canvas lifecycle | 4 | 4 | 2 | 4 | page transient、async/resource owner 范围更广 | 后续 |
| Selection/focus/context 全量统一 | 4 | 4 | 2 | 4 | source exact focus/Escape 仍 partial | 只取 edge selection 相邻子切片 |
| Media ingress/resource | 5 | 4 | 2 | 5 | common materializer/backend/source fixture 缺失 | 不实施 |
| Foreground editor session | 5 | 5 | 2 | 5 | 十类 editor runtime 分散、source dirty/save partial | 不实施 |
| Media rendition/geometry | 5 | 5 | 2 | 5 | ratio-diverse source 与 focused fixture 缺失 | 不实施 |
| Auto Link | 5 | 4 | 2 | 4 | deterministic runtime fixture 与 disposable source 缺失 | 不实施 |

选择 React Flow routing 的原因不是它最显眼，而是它能在不引入 source 未知或
后端能力的前提下，关闭一个已被代码静态证明的 graph correctness 旁路，并为
后续 graph、media、editor 和 multi-canvas slice 提供可靠底座。

## 2. 已读取的事实与边界

### 2.1 `FRAMEWORK_FACT`

- 项目与固定 Open Canvas 都锁定 `@xyflow/react@12.11.1`。
- `NodeChange` 包含 `select/position/dimensions/add/remove/replace`。
- `EdgeChange` 包含 `select/add/remove/replace`，没有 non-selection T1
  transport variant。
- reconnect 是独立 callback，不属于 `EdgeChange`。
- `apply*Changes` 只执行 framework delta，不知道 LibTV graph、history、
  aggregate、resource 或 command authority。

### 2.2 `OPEN_CANVAS_FACT`

- 可借鉴：callback 读取 Zustand current state，而不是只依赖 render closure；
  runtime graph 还会经过 serialization 和完整 document validation。
- 不能照搬：固定版本同样把所有 framework variant 交给 generic reducer，
  semantic `add/remove/replace` 可以先进入 runtime，再等待保存边界发现问题。

### 2.3 `CLONE_FACT`

- [`src/app/page.tsx`](../../../src/app/page.tsx) 的 `onNodesChange` 先应用
  selection，再把所有 non-select change 交给 `applyNodeChanges`。
- 同文件的 `onEdgesChange` 使用 render 时的 `edges` closure，直接
  `applyEdgeChanges -> setStoreEdges`。
- node selection 已有 `selectedNodeIds` session owner；edge selection 仍混在
  semantic edge record。
- `setNodes/setEdges` 是 whole-array commit primitive，同时仍可被多个调用方
  当作广权限 setter。
- named connect/delete 和 drag-stop one-history 已存在，不能因本批回退。

### 2.4 `DECISION`

- 整批先分类，unsupported/malformed semantic batch 在任何 selection 或
  transport mutation 前退出。
- T0 只负责 node/edge selection；T1 只负责 existing-node finite position
  和 passive measurement。
- edge selection 使用 active-session owner，不再成为 semantic edge data。
- accepted plan 基于同一个 current active-canvas snapshot；active canvas 在
  plan/commit 间变化则零副作用退出。
- routine stale event 只返回结构化 diagnostic，不增加未证实的源站 toast。

## 3. 本批范围

### Slice A：纯 classifier 与稳定结果

新增纯 helper，负责：

- exact 12.11.1 variant exhaustiveness；
- whole-batch `accept/reject` 规划；
- existing ID、finite position、nonnegative dimensions 校验；
- passive dimensions 与 `setAttributes` semantic resize 分流；
- stable result code：
  `APPLIED_SELECTION`、`APPLIED_TRANSPORT`、
  `APPLIED_MIXED_RUNTIME`、`STALE_ELEMENT_ID`、
  `INVALID_NUMERIC_PAYLOAD`、`SEMANTIC_CHANGE_REQUIRES_COMMAND`、
  `ATTRIBUTE_RESIZE_REQUIRES_COMMAND`、`UNSUPPORTED_CHANGE_VARIANT`、
  `ACTIVE_CANVAS_CHANGED`。

本批默认不做 `REROUTED_TO_COMMAND`。只有已有 callback 能无歧义对应现有 named
command 时才允许接管；其他 semantic variant 一律零副作用拒绝。

### Slice B：current-snapshot store routing

在 store 或与 store 同权威的 adapter 中：

- 一次读取 active canvas ID、nodes、edges 和 selection；
- 基于同一 snapshot 计算 T0/T1 结果；
- position/measurement 只更新已存在 node；
- 不使用 route render closure 作为 whole-array reducer base；
- plan/commit owner 不一致时返回 `ACTIVE_CANVAS_CHANGED`；
- drag frame 不写 history，drag stop 保留现有 pre-drag snapshot one-history。

不把全部 graph command 迁移到新 adapter，也不公开新的 generic graph setter。

### Slice C：edge selection session owner

- 在普通 `canvasStore` 增加最小 `selectedEdgeIds` / `selectEdges` session state；
- node/edge selected flags都由 route projection 产生；
- selection 不进入 graph history、copy、document 或 async baseline；
- canvas switch、delete、undo/redo 后只保留仍属于 active graph 的 selection；
- 本批不实现统一 primary selection、focus zone、Escape 或 modal manager；
  这些仍由 `LIBTV-VR-019` 后续处理。

### Slice D：route callback 收口

- `onNodesChange/onEdgesChange` 只调用已分类 adapter；
- 不再对 unclassified union 直接调用 `applyNodeChanges/applyEdgeChanges`；
- mixed valid T0/T1 使用同一 snapshot；
- node/edge semantic variant 不产生 partial selection、graph 或 history；
- named `onConnect`、keyboard delete、edge scissors delete 保持原入口；
- React Flow 默认删除仍保持 `deleteKeyCode={[]}`。

### Slice E：fixture、verifier 与证据

- 新增 `scripts/verify-liblib-batch61.py`；
- 提供 verifier-only change-routing debug hook，输入合成 change corpus 并返回
  structured result；不提供产品 UI 或持久化能力；
- 浏览器场景仍通过真实 node/edge click、drag、connect 和 delete 验证 observed
  callback/UX；
- 输出 `runtime-audit.json`，记录 callback batch、result、graph、selection、
  history 和 active canvas；
- 只有视觉确实变化或需要证明 selected edge/overlay 状态时才新增截图；否则在
  `SCREENSHOT_ANALYSIS.md` 记录 `NO_NEW_SCREENSHOT_REQUIRED`，复用既有
  Batch 57/60 视觉证据。

## 4. 预期文件边界

| 路径 | 预期职责 |
|---|---|
| `src/lib/libtvReactFlowChangeRouting.ts` | 纯 classifier、payload validation、result vocabulary |
| `src/store/canvasStore.ts` | current-snapshot commit、edge selection session owner、debug hook |
| `src/app/page.tsx` | projection 与 callback adapter；移除 unclassified generic apply |
| `scripts/verify-liblib-batch61.py` | focused Playwright + pure/runtime corpus |
| `docs/research/liblib-canvas-batch61-2026-08-27/` | 计划、实施、runtime audit、截图成本台账 |
| 稳定治理文档 | 实施后同步 maturity、traceability、fixture、verifier 和 coverage |

若实际实现需要修改 `src/types/canvas.ts`，必须先证明是公开 session/result 类型
的正确归属；不能把 framework runtime fields 加入 portable node schema。

编码前必须先阅读：

- `node_modules/next/dist/docs/01-app/01-getting-started/05-server-and-client-components.md`
- `node_modules/next/dist/docs/01-app/03-api-reference/01-directives/use-client.md`
- `node_modules/next/dist/docs/01-app/02-guides/testing/playwright.md`

并再次核对安装版本的 xyflow types/reducer，不能依赖记忆中的其他版本。

## 5. `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01`

### 5.1 Setup 与 reset

- 每个 destructive browser scenario 使用 fresh Page；
- 使用本地 `canvas-1` 空画布或 deterministic debug corpus；
- 所有 synthetic changes 只作用于当前本地 clone；
- scenario 结束后关闭 Page，不用 undo 充当全局 reset；
- 不访问、输入或修改 LibTV 共享源站。

### 5.2 必测场景

| 组 | 场景 | 预期 |
|---|---|---|
| T0 | node select / deselect | graph/history 不变 |
| T0 | edge select / deselect | semantic edge record/history 不变，视觉选中仍存在 |
| T1 | finite position | 只改变目标 node position |
| T1 | multi-frame drag + stop | frame 零 history，stop 恰好一条 |
| T1 | no-op drag stop | 零 history |
| T1 | passive dimensions | 零 semantic history，不变成 explicit resize |
| mixed | valid select + position | 同一 snapshot 一次接受 |
| reject | node add/remove/replace | graph/selection/history 全不变 |
| reject | edge add/remove/replace | graph/selection/history 全不变 |
| reject | dimensions `setAttributes` | 返回 resize requires command |
| reject | unknown / NaN / Infinity | 稳定 reason，零 partial mutation |
| stale | delete 后 queued position | 不复活 node |
| stale | render 后新增 edge，再 edge-select | 不丢失新 edge |
| stale | canvas switch before commit | 不写入新 active canvas |
| precedence | same-ID remove/add/position mixed | classifier 先拒绝，不让 reducer 隐式 replacement |

### 5.3 Boundary sanitation

- stored semantic nodes/edges 不含 `selected`；
- history/copy/document 不因本批新增 runtime selection 字段；
- passive `measured/dragging/resizing` 的保留范围必须在实施记录中明确；
- 本批若无法在不扩大 document/copy codec 的前提下证明完整 sanitation，至少
  关闭 callback 新泄漏并把既有历史问题保留在 `LIBTV-VR-010..012`，不得伪称
  portable boundary 已整体完成。

## 6. 验收标准

### Pure/runtime

- exact installed variants 有 exhaustive test；
- unsupported semantic/malformed mixed batch 在第一项副作用前退出；
- current store snapshot 中比 route closure 更新的 node/edge 不被覆盖；
- missing element 和 old canvas event 不创建、不复活、不跨画布写入；
- edge selection 不再改变 semantic edge payload；
- result code 可被 verifier 稳定断言，不依赖中文 copy。

### Existing UX

- node click、多选、框选、空白清选行为不回归；
- edge hover/select 的 pulse、glow 和 scissors affordance 不回归；
- real node drag、group drag、pan/zoom 和 snap 不回归；
- named connect、delete、undo/redo 保持原 transaction cardinality；
- Batch 60 图片双浮层 owner/selection migration 和几何不回归；
- desktop `929x874` 与 mobile `390x844` 无 document/body 横向溢出；
- 无 console error、page error 或 unexpected request failure。

## 7. 验证顺序

1. pure classifier/result cases；
2. Batch 61 focused Playwright；
3. `python3 scripts/verify-liblib-batch3.py`；
4. `python3 scripts/verify-liblib-batch4.py`；
5. `python3 scripts/verify-liblib-batch5.py`；
6. `python3 scripts/verify-liblib-batch6.py`；
7. `python3 scripts/verify-liblib-batch57.py`；
8. `python3 scripts/verify-liblib-batch58.py`；
9. `python3 scripts/verify-liblib-batch60.py`；
10. `npm run check`；
11. `npm run docs:check`。

这些 Playwright 脚本串行运行，避免共享 dev server、截图和 browser timing 相互
干扰。Batch 51 的旧 `900.5px` 断言不进入本批回归，也不回退 Batch 52+ 当前
图片合同。

## 8. 停止条件

- 真实 React Flow callback 发出合同未覆盖的 variant 或 payload；
- 为保持现有 UX 必须引入 source 未证的 resize/reconnect；
- edge selection 迁移需要同时重写完整 focus/command-context；
- current-snapshot commit 无法与现有 drag one-history 组合而不产生双 history；
- runtime field sanitation 必须先完成完整 document/copy codec 才能继续；
- 出现 FrameOS route/store 共享改造需求；
- 工作区出现影响目标文件的并行 WIP，且无法在不覆盖它的情况下继续。

遇到停止条件时先把实际 callback、状态和 blocker 写入 `IMPLEMENTATION.md`，
建立保护性 checkpoint；不扩大为一次性 store 重构。

## 9. Checkpoint 与留档

1. **规划 checkpoint**：本计划、Research Hub、Documentation Hub、parity
   backlog 和 Open Canvas handoff 可发现性；运行 docs check 后 commit/push。
2. **实现 checkpoint**：pure classifier + store/route adapter + focused fixture
   首次通过后，补 `IMPLEMENTATION.md` 和 runtime audit，commit/push。
3. **收口 checkpoint**：跨批回归、`npm run check`、docs check 和截图成本台账
   完成后，更新 verifier/fixture/coverage/traceability/decision maturity，
   commit/push 并确认工作区干净。

每个 checkpoint 只声明当时已实际完成的层级；规划通过不等于 runtime 或 source
parity 完成。
