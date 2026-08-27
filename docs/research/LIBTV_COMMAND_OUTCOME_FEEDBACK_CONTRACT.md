# LibTV Command Outcome And Feedback Ownership Contract

> Scope: 普通 LibTV route 与 Director 中用户命令的结果分类、reason identity、busy/progress/error/success projection、inline/node/surface/toast/modal ownership、清理时机、history 边界，以及 Open Canvas 固定版本提供的正反面方法。
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL`。
>
> Clone baseline: `04b3fcd`。Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`。
>
> Authorization boundary: 本文只记录研究、设计、fixture 与 verifier，不授权修改 `src/`、测试脚本、Open Canvas submodule、FrameOS 或真实服务。

## 1. Why This Contract Exists

当前项目已经有不少局部反馈：

- 普通 graph connection 返回结构化 rejection reason，但 page callback 静默结束；
- Share、Agent、Add Node 和智能剪辑把 local-only 文案保存在组件 state；
- VideoNode 用多个独立 timer 在媒体内部显示短提示；
- 长视频、逐帧拉片和 Director 使用 busy/progress/result surface；
- Batch 57、async ingress、graph delete 和 canvas lifecycle 合同都要求 stable result；
- FrameOS 有自己的 route-local toast，但普通 LibTV route 没有统一 toast owner。

这些实现单独看都可以工作，合起来却没有回答：

1. 命令是 `accepted`、`rejected`、`noop`、`started`、`completed`、`failed`、`stale` 还是 `unknown`；
2. reason 是稳定机器身份，还是一段恰好可显示的字符串；
3. 反馈应位于字段、控件、节点、面板、画布、全局 toast 还是阻断 modal；
4. 哪些状态是业务事实，哪些只是 presentation projection；
5. 画布切换、节点删除、surface 关闭、retry 和异步完成后由谁清理；
6. 一次结果是否被 node error、toast、toolbar 文案和 history 重复表达；
7. prototype 如何诚实表达“本地模拟”，而不是用 success feedback 暗示真实服务。

没有统一合同，后续 LibTV UI/UX 复刻很容易出现两类失真：

- 把源站的持续 workflow、结果节点或可恢复错误缩成一次 toast；
- 为了让按钮“有反馈”，把 transient 文案、timer 或 loading 写进 graph/history。

本合同的目标链是：

```text
user intent
  -> named command
  -> typed outcome + stable reason + owner
  -> declared domain/history effects
  -> one primary presentation projection
  -> optional secondary transient announcement
  -> explicit clear/retry/reconcile lifecycle
```

## 2. Evidence And Claim Boundary

### 2.1 `OPEN_CANVAS_FACT`

固定 Open Canvas 版本的直接证据来自：

- [`app/layout.tsx`](../../research/upstream/open-canvas/app/layout.tsx#L4)：全局 Sonner `Toaster`，`bottom-right`、`richColors`；
- [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L45)：graph command 返回 `ok/code/message`；
- [`i18n.ts`](../../research/upstream/open-canvas/shared/lib/canvas/i18n.ts#L29)：运行 message 通过中文字符串 lookup 投影到 translation key；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3197)：node status 改变 card tone/shadow；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3970)：clipboard/graph command rejection 投影为 toast；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5180)：run polling 同时写 node error/status 与 terminal toast；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5914)：save/dirty/error/conflict 用持续 inline status 和 conflict banner 表达；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L7264)：selected node editor 持续显示 `errorMessage`；
- [`canvas-list-page.tsx`](../../research/upstream/open-canvas/components/canvas-list-page.tsx#L229)：create/rename/delete/import 的 pending、silent no-op、confirm 和 toast；
- [`provider-settings-dialog.tsx`](../../research/upstream/open-canvas/components/provider-settings-dialog.tsx#L339)：字段错误 map、summary toast、busy 和成功/失败关闭路径；
- [`canvas-media-control.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-media-control.tsx#L270)：upload 同时拥有 local busy、node status/error 和 toast。

这些事实只说明 Open Canvas 固定代码如何做，不证明官网部署版本、LibTV 源站或最佳通用 UX。

### 2.2 `CLONE_FACT`

当前 clone 的静态事实来自：

- [`page.tsx`](../../src/app/page.tsx#L254)：connection validator 先返回结构 reason，但 reject 在 `onConnect` 静默结束；
- [`libtvGraphConnection.ts`](../../src/lib/libtvGraphConnection.ts#L27)：connection 使用稳定 rejection reason union；
- [`TopNavBar.tsx`](../../src/components/TopNavBar.tsx#L18)、[`AgentDrawer.tsx`](../../src/components/AgentDrawer.tsx#L86)、[`AddNodePanel.tsx`](../../src/components/AddNodePanel.tsx#L43) 和 [`VideoClipEditPanel.tsx`](../../src/components/VideoClipEditPanel.tsx#L27)：多个 surface 自有 local status；
- [`VideoNode.tsx`](../../src/components/nodes/VideoNode.tsx#L124)：frame/picture/depth 三类 node-local timer feedback；
- [`VideoProcessingToolbar.tsx`](../../src/components/VideoProcessingToolbar.tsx#L50)：toolbar `lastAction` 持续到替换/卸载；
- [`VideoGenerationPanel.tsx`](../../src/components/VideoGenerationPanel.tsx#L140) 和 [`ShotBreakdownNode.tsx`](../../src/components/nodes/ShotBreakdownNode.tsx#L34)：local busy 与 graph-producing completion 并存；
- [`DirectorDesk.tsx`](../../src/components/director/DirectorDesk.tsx#L78)、[`DirectorPhoneVcamPanel.tsx`](../../src/components/director/DirectorPhoneVcamPanel.tsx#L269) 和 [`DirectorTimeline.tsx`](../../src/components/director/DirectorTimeline.tsx#L156)：Director 已有 progress/error/retry 的 owner-local surface；
- Batch 14/15/23/24/29/30/32/33/40/41/44/57/58/60 的计划、实现和 screenshot 记录。

### 2.3 `INFERENCE`

以下是证据支持的工程推断，不是源站事实：

- durable/recoverable 状态需要 owner-local 持续 projection，不能只靠 transient toast；
- toast 适合“动作已完成但没有持续可见对象”的轻量确认，不适合替代 workflow；
- stale/duplicate completion 不应显示成功 toast，因为用户当前可见 owner 未必获得结果；
- reason identity 与 display copy 必须分开，否则 i18n、verifier 和 retry policy 会依赖字符串；
- 同一 outcome 可以有一个 primary surface 和一个辅助 announcement，但不能在多个独立 owner 中各自成为权威。

### 2.4 `DECISION`

本文定义的 outcome taxonomy、owner model、projection matrix、invariants、fixture 和 verifier 都是 clone-only correctness design。精确 LibTV 文案、颜色、timeout、motion、toast placement、invalid Handle style 和是否显示某个 surface，仍由 LibTV current source evidence 决定。

### 2.5 Explicit exclusions

- 不新增全局 LibTV toast；
- 不复用 FrameOS toast 作为普通 LibTV route 方案；
- 不接 provider、上传、计费、远端 task、保存或通知服务；
- 不把 Open Canvas 的 Sonner skin、message 文案或 timeout 当 LibTV 规格；
- 不为 source 未确认的 invalid connection 擅自增加红色、toast 或 cursor；
- 不把 presentation feedback 写进 graph history。

## 3. Outcome Model

### 3.1 Command disposition

每个具名命令至少归入一个稳定 disposition：

| Disposition | 含义 | Graph/history 默认 | Presentation 默认 |
|---|---|---|---|
| `COMMITTED` | 同步命令已完成声明的 mutation | 按 command plan，一次 history 或 zero-history | visible result 通常足够；必要时轻量确认 |
| `STARTED` | 异步 operation 已被接受并拥有 identity | descriptor/placeholder 按合同提交 | busy/progress 绑定 owner；不是完成成功 |
| `COMPLETED` | operation terminal success 已收敛 | result projection 一次提交 | owner-local result；detached 时可 announcement |
| `REJECTED` | 前置/校验失败，命令未执行 | zero mutation / zero history | 靠近 action 的原因与恢复路径 |
| `NOOP` | 合法但没有变化或用户取消 | zero mutation / zero history | 通常 silent；重复提示会制造噪音 |
| `FAILED` | 已开始的动作无法完成 | 按 rollback/partial policy | persistent recoverable error + retry；可辅助 toast |
| `CANCELED` | 用户/系统终止且结果未提交 | 按命令 cancel policy | 用户主动取消通常 silent |
| `STALE` | 结果 owner/version 已失效 | zero target mutation | silent/diagnostic；不能宣告当前成功 |
| `CONFLICT` | 当前 owner 无法安全自动合并 | zero unsafe mutation | persistent banner/modal + recovery action |
| `UNKNOWN` | 没有足够规则安全处理 | zero mutation / zero history | generic bounded feedback；记录诊断，不猜成功 |

`STARTED` 和 `COMPLETED` 是两个不同 outcome。显示“已提交/运行中”不能使用完成态 checkmark 或“已生成”文案。

### 3.2 Stable reason identity

Outcome reason 必须是机器稳定身份，display copy 是 presentation projection：

```text
reason code + structured args
  -> route/surface/source-specific message mapping
  -> localized display copy
  -> accessibility announcement
```

Reason 不应是：

- 任意 server error string；
- 需要 trim 标点后匹配的中文文案；
- 把 node ID、URL、provider response 或 stack 直接展示给用户；
- 只有 `invalid_graph` 但无法区分 duplicate、cycle、limit 和 conflict 的过粗 code。

当前 clone connection 的 `MISSING_ENDPOINT / INVALID_HANDLE_DIRECTION / DANGLING_ENDPOINT / DUPLICATE_NODE_PAIR / SELF_LOOP / DIRECTED_CYCLE` 是可借的 reason 形状。精确用户文案仍未取得 source interaction evidence。

### 3.3 Owner envelope

任何非即时 projection 至少需要：

| Field | 用途 |
|---|---|
| `commandKind` | 决定 reason registry、history 和 surface policy |
| `operationId` | async、retry、dedupe、terminal convergence |
| `projectId` | project-level lifecycle |
| `canvasId` | 防止跨画布 feedback/result |
| `canvasGeneration` | 防止旧 route/page callback |
| `nodeId` / `surfaceId` | node/surface local owner |
| `attempt` | retry 与旧 attempt 区分 |
| `disposition` / `reason` | 稳定结果身份 |
| `occurredAt` | timer、ordering、diagnostic；不是业务 identity |

并非每个同步按钮都需要完整 runtime object；但设计和 fixture 必须能回答这些 owner 中哪些适用。

## 4. Presentation Surface Taxonomy

| Surface | 适用结果 | Owner | 清理条件 | 不适用 |
|---|---|---|---|---|
| control state | submitting、busy、disabled、success check | command control | completion/cancel/retry/unmount | 长期错误解释 |
| field inline | required、format、range、permission | field + form surface | edit/valid submit/reset | 跨 surface 成功 |
| node-local chip | media guard、短动作确认、selected node operation | canvas + node + command | timeout/new attempt/delete/switch | project/save 状态 |
| node status/editor error | queued/running/error、recoverable node state | canvas + node + operation | retry/success/delete | 纯 clipboard confirmation |
| surface-local status/banner | local prototype、panel workflow、Director export | mounted surface + owner | explicit action/edit/close/owner change | 已关闭 surface 的后台结果 |
| canvas status/banner | conflict、save/recovery、canvas-wide block | canvas + generation | resolve/reload/switch | 单节点输入错误 |
| global transient toast | copy/download/import/rename 等无持续 result 的确认；当前 surface 外重要失败 | route + operation | library timeout/dismiss/owner invalidation | workflow 唯一状态、stale success |
| modal/confirmation | destructive/irreversible/permission boundary | command target | confirm/cancel/owner invalidation | routine validation failure |
| silent + diagnostic | user cancel、same-value no-op、stale/duplicate callback | diagnostic identity | bounded log/fixture reset | 用户必须采取恢复动作的失败 |

### 4.1 Primary and secondary projection

每个 outcome 只有一个 primary visual authority。辅助 announcement 只能帮助发现，不得改变语义：

```text
node generation failure
  primary: node status + selected editor error + retry
  secondary: one error toast when failure first arrives
  forbidden: toast is the only durable error
```

```text
copy image success
  primary: transient toast or local status
  secondary: none
  forbidden: graph/history mutation just to preserve feedback
```

```text
stale completion for canvas A while B active
  primary: A operation ledger/background indicator if product requires
  secondary: no B success toast
  forbidden: select result in B or claim visible completion
```

## 5. Open Canvas Feedback Audit

### 5.1 Global transient channel

Open Canvas 在 root layout 挂一个 Sonner `Toaster`。Studio、list、provider settings、media control 和 shell 都直接调用全局 `toast.success/error`。这提供统一 placement 和色彩，但 call site 自己决定 message、owner、dedupe 和时机。

可借方法：

- route-level transient channel 不属于 graph；
- copy/import/export/rename/delete 等动作可以用短确认；
- command rejection 可以在 UI adapter 把 typed result 投影成 feedback。

不能照抄：

- 固定代码没有显式 toast ID、canvas owner 或 operation attempt；
- old-canvas async completion 可能在用户已进入另一 canvas 时显示全局 toast；
- 多文件 drop 会逐文件 toast，缺少批量汇总/节流；
- hard-coded English/Chinese 与 i18n key 混用。

### 5.2 Typed result and localized message counterexample

Store mutation result 至少有 `ok` 与 `code`，这是正确方向。但 code 主要只有 `invalid_graph / graph_cycle_detected`，更具体的语义放在中文 `message`。UI 的 `translateCanvasRuntimeMessage` 再以整段中文和去尾标点后的中文做 lookup。

这意味着：

- copy 变更可能破坏 translation mapping；
- verifier 容易依赖显示字符串而非 reason；
- retry/focus/aria policy 无法只由 code 决定；
- server message、domain reason 和 presentation copy 混在一起。

LibTV 应借 `result -> UI adapter` 形状，拒绝“本地化字符串就是领域身份”。

### 5.3 Node operation has persistent and transient layers

Open Canvas node generation/upload 的正面结构是：

1. node data 保存 `queued/running/success/error`、`errorMessage` 和 `lastRunId`；
2. node card tone/shadow、MiniMap color 和 execute button disabled 读取该状态；
3. selected editor 持续显示 error message；
4. run started/completed/failed 另有 toast；
5. retry/new run 会清 error 并建立新 run。

可借的是 persistent owner 与 transient announcement 分开。风险是：

- node patch 和 local `updateNodeData` 不是统一原子 authority；
- terminal failure 既写 node error 又 toast，若 owner 已切换会产生上下文错位；
- success toast 不说明结果是否已投影、是否 stale、是否仍可见；
- generic error message 可能覆盖更具体 field recovery。

### 5.4 Save/conflict uses persistent canvas surface

Save 不是 toast-only：header status pill 持续显示 saving/error/dirty/saved，error meta 可保留；conflict 还有 persistent banner、load-latest action 和大范围 mutation disable。只有检测到 newer version 的转折会额外 toast。

这是高价值正面模式：用户必须采取恢复动作的 canvas-wide state 应有持续 surface。它不授权 clone 实现 autosave/conflict，也不证明 LibTV 有同类 UI。

### 5.5 Field and form summary

Provider settings 先构造 field error map，再用 toast 给出“修复高亮字段”的 summary。Field 是 primary，toast 是辅助。保存期间有 `isSaving`，成功后关闭 dialog，失败保留 surface。

这个模式可用于未来 LibTV 参数 panel：定位到具体字段，summary 不替代字段原因。Open Canvas 的 provider 设置本身仍是 reject transplant。

### 5.6 CRUD, cancel and no-op

List page 的实际策略：

- create success 通过 navigation/新 document 体现，不再 success toast；failure toast；
- rename 空标题 toast，同名直接退出 edit 且 silent，成功/失败 toast；
- delete 先 native confirm，成功/失败 toast；
- user cancel、无 file、同名 no-op silent；
- pending ID 或 local busy 防止重复提交。

说明“每次点击都 toast”并不是固定实现自己的规则。结果已通过明显 UI transition 呈现时，额外 success toast 未必有价值。

## 6. Current Clone Feedback Audit

### 6.1 Inventory

| Clone path | Current feedback owner | Lifecycle | Strength | Gap |
|---|---|---|---|---|
| graph connection | typed reason in validator；page silent reject | gesture callback | reason identity 已存在 | source feedback、gesture cleanup、aria、surface projection 未决 |
| Share | panel-local string | button replaces；panel unmount clears | 明确 `本地原型` | no command/result identity；无 close-after-action contract |
| Agent | drawer-local string | skill/edit/refresh clears；unmount | prototype boundary honest | submit/cancel/attempt 不成体系 |
| Add Node resource | menu-local string | another action/close clears | close owner 清楚 | upload/history 是 unavailable，不应伪装 started |
| Video clip | editor-local string | input edit/close clears | proximity good | “已创建本地任务”容易与 durable operation 混淆 |
| Video frame/picture/depth | node-local chip + separate timer | 1.4/1.8s、unmount cleanup | source-shaped proximity and independent timer | reason/code/attempt 不稳定；switch/delete owner 依赖 unmount |
| Video toolbar preview | `lastAction` text | replace/unmount | visible local action | 没有 timeout/owner/reason；可能挤压 toolbar |
| Segment reshoot | panel submitted/check/status | edit/close lifecycle 不完整 | 明示本地预览 | submitted 与 started/completed 混用 |
| long video / breakdown | local busy then graph result | timer + graph command | workflow 不止 toast | descriptor/stale/operation owner 见 async contract |
| Director export | panel progress/error/success | explicit retry/close | 当前最完整的 owner surface | canvas switch/resource transfer 仍需 lifecycle 组合验证 |
| Director phone/camera preset | panel/timeline inline error and retry | owner surface | recovery action 清楚 | route/source parity 分开维护 |
| Canvas CRUD | dropdown transition | action closes menu | visible result | invalid target/name/final delete feedback policy 未统一 |

### 6.2 Positive clone patterns

- connection reason 是 stable union，不依赖显示文案；
- prototype-only commands 明示“本地原型/未连接”，没有伪称服务成功；
- VideoNode 三类反馈使用独立 state/timer，避免不同命令共享一条 message；
- Director export 的 progress/error/retry 保留在工作 surface，而不是 toast-only；
- graph/history 与多数 local feedback 分离；
- FrameOS toast 保持 route/store 分离，没有被普通 LibTV 随意复用。

### 6.3 Clone risks

1. **Reason dropped.** Connection validator 返回具体 reason，page adapter 只 `return`，无法验证 source feedback 或 accessibility。
2. **String-only state.** 多个 surface 只保存 display string，无法区分 unavailable/rejected/started/completed。
3. **Timer identity absent.** Video node timer 清理靠 component ref，没有 command attempt/canvas generation；重复动作和 owner switch 只靠局部 ordering。
4. **Started looks completed.** “已创建本地任务”、checkmark、submitted boolean 可能把 presentation delay 或 local graph creation误读为真实完成。
5. **No global LibTV policy.** 这不等于需要全局 toast；它表示没有统一 projection decision，导致每个组件自定位置、timeout、清理和 aria。
6. **No dedupe/queue contract.** 多个 node/operation 同时完成时，没有 owner-aware aggregation。
7. **Surface closure loses result.** Panel-local status 在关闭后消失；若 action 真的是后台 operation，需要其他 owner 接管。
8. **Feedback width can affect geometry.** Toolbar `lastAction`、node chip 和 panel status 都可能改变 fixed-format surface 的可用空间。

## 7. Normative Projection Decision

按以下顺序选择 surface：

```text
1. Is the result a durable domain state or recoverable workflow state?
   yes -> owner-local persistent surface
2. Is there a specific field/control that can fix the rejection?
   yes -> field/control inline + focus/aria mapping
3. Does the accepted result create/select a visible graph object?
   yes -> visible result is primary; toast only with source/product reason
4. Will the owner surface remain mounted while work continues?
   yes -> surface busy/progress/error
5. Is this a context-free utility completion such as copy/download?
   yes -> transient local/global confirmation
6. Is the outcome cancel/noop/stale/duplicate?
   yes -> usually silent + diagnostic
7. Is recovery blocked across the entire canvas/project?
   yes -> persistent canvas/project banner or modal
```

### 7.1 Command-family defaults

| Command family | Primary projection | Optional secondary | Forbidden shortcut |
|---|---|---|---|
| connect/reconnect | gesture-local invalid state or source-confirmed feedback | one bounded toast only if source proves | adding edge then error toast rollback |
| add/copy/delete node | visible graph/selection/history result | destructive confirm/source feedback | success toast as only evidence |
| import/drop | aggregate progress/result surface or per-file bounded summary | terminal toast | unbounded one-toast-per-item flood |
| copy/download/share link | transient confirmation | control check | durable graph state |
| node generation/process | node/process status + progress/error/retry | transition announcement | toast-only workflow |
| field validation | inline field reason | form summary | generic toast without location |
| canvas conflict/block | persistent canvas banner/modal | transition toast once | disappearing timeout-only error |
| local prototype unavailable | action-adjacent honest disclosure | none | success wording, fake progress or fake remote ID |
| cancel/no-op/same target | silent | diagnostic | success/error noise |
| stale/duplicate completion | original operation ledger or silent | diagnostic | current-canvas success toast |

### 7.2 Geometry and overlay rule

Feedback cannot move the source-authoritative anchor or resize fixed controls unexpectedly：

- node-local chip must have stable max width/wrap/overflow strategy；
- toolbar feedback cannot push source actions offscreen unless source proves it；
- toast/global announcement cannot intercept React Flow Handle, drag or wheel；
- inline error insertion must preserve editor anchor and mobile clipping contract；
- modal/banner stacking must follow overlay owner catalog。

## 8. Lifecycle And Reconciliation

| Event | Required reconciliation |
|---|---|
| edit invalid field | clear/recompute only that field reason；do not clear unrelated operation error |
| retry | allocate new attempt；old terminal callback becomes stale |
| new same command | replace/dedupe same owner feedback；do not stack identical notices |
| node selection change | persistent node status stays with node；selected-editor projection rebinds |
| node deletion | node-local feedback/error/operation surface closes；background/resource policy explicit |
| canvas switch | old node/surface projection closes；background result cannot announce as target success |
| canvas delete | every feedback/operation owner reconciles with delete/resource plan |
| panel close | purely local feedback clears；true background operation transfers to declared owner |
| Escape | closes current surface per overlay contract；does not silently cancel remote work unless command says so |
| undo/redo | feedback not restored from history；domain state follows graph snapshot rules |
| stale completion | zero target mutation；no success announcement；diagnostic disposition retained |
| duplicate terminal event | idempotent no-op；no duplicate toast |

Cross-owner rules compose with [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) and [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。

## 9. History And Document Boundary

### 9.1 Presentation-only state

以下默认不进入 graph/history/portable document：

- toast queue、dismiss timestamp；
- field validation projection、focus target；
- local prototype status；
- transient node chip；
- menu/toolbar `lastAction`；
- submitting spinner、button checkmark；
- stale/duplicate diagnostic；
- global announcement bookkeeping。

### 9.2 Domain/operation state

以下可能是 document 或 external owner，但必须由对应合同决定，不因显示在 UI 上就自动持久化：

- node media candidate/result/version；
- process placeholder and operation ID；
- recoverable node error tied to a run；
- Director exported media/resource ownership；
- future save/revision/conflict state。

Undo/redo 只恢复 graph snapshot 中声明的 domain state。它不应“重新弹出旧 toast”，也不应恢复旧 timer。

## 10. Accessibility And Focus

后续获授权实施时，必须同时验证：

- field rejection 与具体 input 的 accessible description/focus 关联；
- busy control 使用真实 disabled/`aria-busy` 或等价状态，不只改变颜色；
- transient announcement 不重复朗读 node inline error；
- persistent error 可通过键盘找到 retry/resolve action；
- timeout feedback 不承载唯一关键信息；
- toast 不抢走 prompt、node editor、Handle drag 或 Director shortcut focus；
- mobile 下长 reason 可换行，不覆盖按钮或节点内容。

精确 ARIA role/live politeness 需按最终 surface 和 source evidence 决定；本文不预设所有 feedback 都用 assertive alert。

快捷键 dispatch、foreground surface precedence、single-layer Escape 和 close 后 focus-return validity 由 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) 负责；本文只定义 outcome 到反馈 owner 的投影，不能借 toast/focus effect 夺取 command-context authority。

## 11. Invariants

### `LIBTV-GI-049` — Outcome precedes projection

每个可见 feedback 来自 typed outcome；UI 不从“是否抛异常/是否有字符串”猜 disposition。

### `LIBTV-GI-050` — Reason and copy are separate

Reason code/args 是稳定 identity，localized/source-exact display copy 只存在于 presentation mapping。

### `LIBTV-GI-051` — Reject/noop/stale are zero-history

`REJECTED / NOOP / STALE / UNKNOWN` 默认不改变 graph、selection、history、viewport 或 model；例外必须由 command plan 声明。

### `LIBTV-GI-052` — Feedback is not graph history

Toast、inline validation、timer chip、focus 和 local prototype status 不进入 graph history 或 portable document。

### `LIBTV-GI-053` — One primary authority

同一 outcome 只有一个 primary persistent visual owner；secondary announcement 不成为另一份状态权威。

### `LIBTV-GI-054` — Durable failure stays recoverable

用户必须处理的 failure/conflict 不能只通过 timeout toast 表达；owner surface 保留原因和 recovery action。

### `LIBTV-GI-055` — Stale result cannot announce current success

旧 canvas/node/attempt 的 completion 不选择、改写或宣告当前 owner 成功。

### `LIBTV-GI-056` — Prototype boundary is explicit

未接服务的动作使用 unavailable/local-prototype 语义，不显示 fake run ID、真实费用、完成百分比或远端成功。

### `LIBTV-GI-057` — Feedback lifecycle is deterministic

每个 projection 声明 clear/edit/retry/close/delete/switch/timeout/dedupe 路径；不存在“直到某次偶然重渲染”。

### `LIBTV-GI-058` — Route owners remain isolated

LibTV 与 FrameOS feedback channel、store 和 route lifecycle 分离；不能为了复用 toast 形成 route `mode` authority。

## 12. Compatibility Cases

| Case | Setup | Action | Expected |
|---|---|---|---|
| `LIBTV-GC-059` invalid connection | duplicate pair | drag connect | stable reason；zero graph/history；source-gated feedback；gesture clears |
| `LIBTV-GC-060` valid connection | valid A -> B | connect | visible edge + one history；no required generic success toast |
| `LIBTV-GC-061` same rename | title unchanged | submit | `NOOP`、silent、zero graph/history |
| `LIBTV-GC-062` field rejection | empty required Prompt | submit | field inline/focus；no fake started state |
| `LIBTV-GC-063` prototype unavailable | Share service absent | click publish | action-adjacent honest local disclosure；no remote success |
| `LIBTV-GC-064` node guard | video duration unsupported | choose action | node-local reason；zero graph/history；timer/retry lifecycle exact |
| `LIBTV-GC-065` visible result | frame capture succeeds | capture | result node/selection/history are primary；source-confirmed chip may announce |
| `LIBTV-GC-066` async start | long-video accepted | submit | `STARTED` busy/process owner；not `COMPLETED` |
| `LIBTV-GC-067` async fail | owned operation fails | terminal event | persistent owner error + retry；one optional announcement |
| `LIBTV-GC-068` stale completion | A operation, switch B | A terminal success | B unchanged/unselected；no B success toast |
| `LIBTV-GC-069` duplicate terminal | same operation event twice | converge twice | one result/announcement；second `NOOP` diagnostic |
| `LIBTV-GC-070` panel close | local-only status visible | close/reopen | local status cleared；no hidden operation |
| `LIBTV-GC-071` background close | real owned operation visible | close panel | operation retained by declared owner；result not lost or misowned |
| `LIBTV-GC-072` node delete | node error/result owner | delete node | projections close；resource/operation policy explicit |
| `LIBTV-GC-073` undo | accepted graph result then undo | undo/redo | graph follows history；old toast/timer not replayed |
| `LIBTV-GC-074` multi-file errors | several unsupported files | drop batch | bounded aggregate/per-item policy；no unbounded toast storm |
| `LIBTV-GC-075` route isolation | FrameOS toast active | navigate LibTV | no shared queue/store residue |

## 13. Local Fixture Contract

Fixture ID: `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01`。

### 13.1 Required controls

- deterministic command result injection for every disposition；
- stable reason registry with args and display mapping；
- fake timers and explicit toast/announcement clock；
- A/B canvases、node A1/B1 and operation attempts `op-1/op-2`；
- mounted/unmounted node, panel, dropdown and Director surfaces；
- controlled graph/history/selection/viewport snapshots；
- feedback event ledger separate from DOM screenshot；
- reset that clears timer、queue、operation、focus and owner state。

### 13.2 Required scenes

1. connection allow/reject with exact reason and zero-residue assertion；
2. field reject then edit/retry；
3. local prototype unavailable action；
4. node-local short guard with timer replacement；
5. visible graph result with optional announcement；
6. started -> progress -> completed；
7. started -> failed -> retry -> old attempt stale -> new success；
8. switch A -> B before terminal event；
9. delete node/canvas before terminal event；
10. panel close for local-only versus background operation；
11. duplicate terminal and duplicate toast suppression；
12. multi-file/burst outcomes and bounded aggregation；
13. undo/redo without feedback replay；
14. desktop/mobile long message and fixed geometry；
15. FrameOS/LibTV route isolation。

### 13.3 Reset assertions

After each scene：

- graph/history/selection equal declared baseline or accepted delta；
- no pending timer or orphan announcement；
- no feedback owner from prior canvas/node/attempt；
- no focus left in unmounted surface；
- no stale success wording；
- no console/page error；
- prototype scene never reports real provider completion。

## 14. Verification Replacement

Verifier ID: `LIBTV-VR-018`。

| Layer | Assertions |
|---|---|
| static registry | every user command family has disposition/reason/primary surface/owner/clear path |
| pure outcome | stable reason code/args；display copy not used for branching；unknown fallback bounded |
| transaction | reject/noop/stale zero mutation；accepted exact history；feedback excluded from history |
| owner | node/canvas/surface/operation identity and generation exact；switch/delete reconciliation |
| timing | timer replacement、retry attempt、duplicate terminal、burst dedupe deterministic |
| accessibility | field association、busy state、persistent recovery、no duplicate announcement |
| browser | desktop/mobile geometry、overlay/pointer/focus、route isolation、console/page errors |
| source extension | exact LibTV feedback text/color/timeout/invalid gesture only with disposable source evidence |

`LIBTV-VR-018` composes with `LIBTV-VR-009` connection、`VR-013` delete、`VR-015` async、`VR-017` canvas lifecycle and overlay/shortcut verifiers；it does not replace their graph or source semantics。

## 15. Decision Queue

| ID | Question | Current default | Required evidence |
|---|---|---|---|
| `LIBTV-FB-DQ-001` | ordinary LibTV route 是否需要 global toast host | no new host；use existing owner surfaces | current source toast DOM/placement + repeated action matrix |
| `LIBTV-FB-DQ-002` | invalid connection exact feedback | source-blocked；keep structural reject | disposable source connection fixture |
| `LIBTV-FB-DQ-003` | success visible result 是否仍 toast | no generic toast | source action-specific evidence |
| `LIBTV-FB-DQ-004` | timeout values | preserve recorded per-action values only | source timing capture；accessibility review |
| `LIBTV-FB-DQ-005` | toast dedupe/stack limit | one per operation transition；bounded queue | burst fixture + source observation |
| `LIBTV-FB-DQ-006` | background completion after switch | original owner; no target success | operation-specific product/source contract |
| `LIBTV-FB-DQ-007` | local prototype wording | explicit unavailable/local preview | product copy decision；no fake backend |
| `LIBTV-FB-DQ-008` | node error belongs to portable data? | only if domain/operation contract says so | node data registry profile |
| `LIBTV-FB-DQ-009` | destructive confirmation style | keep existing source/clone action-specific behavior | source delete/download/publish evidence |
| `LIBTV-FB-DQ-010` | ARIA live strategy | no blanket assertive channel | final surfaces + accessibility fixture |

## 16. Implementation Slices After Authorization

### Slice A — Inventory and reason projection

- catalog ordinary LibTV command adapters；
- preserve existing connection reason union；
- define UI-only mapping without changing graph validation；
- keep source-unconfirmed presentation disabled/diagnostic。

### Slice B — Local surface lifecycle

- make Add Node/Share/Agent/Video clip statuses use explicit disposition；
- declare clear/edit/close behavior；
- preserve source geometry and prototype copy boundary。

### Slice C — Node feedback ownership

- bind timer/retry to canvas + node + command attempt；
- preserve existing action-specific selectors/timing where source-backed；
- prevent one action from clearing another action's error。

### Slice D — Async/Director composition

- reuse operation/result owner from async contract；
- keep Director progress/error surface primary；
- suppress stale/duplicate completion announcement。

### Slice E — Optional route transient channel

Only if source/product evidence requires：

- LibTV-only host and queue；
- operation/canvas owner、dedupe、mobile placement and pointer isolation；
- no FrameOS store/component reuse；
- verifier before broad adoption。

每个 slice 都需要用户明确编码授权；本文不因列出顺序而自动授权实施。

## 17. Open Canvas Adoption Verdict

### Adopt

- command result 在 UI adapter 投影，而不是 validator 直接操作 DOM；
- field error + form summary；
- persistent node/run error 与 transient announcement 分开；
- save/conflict 这类可恢复 canvas-wide 状态使用持续 surface；
- cancel/no-op 不必制造 feedback。

### Adapt

- 将 `ok/code/message` 细化为稳定 disposition/reason/args；
- 为 toast/announcement 增加 canvas/operation/attempt owner；
- 将多文件和 burst feedback 汇总/限流；
- 只在 LibTV source 证明时使用 global toast/invalid connection visual；
- 保持当前 clone 的 local-prototype honesty 和 Director owner surface。

### Reject

- 用本地化字符串匹配驱动 reason/i18n；
- 全局 toast 没有 owner/dedupe；
- 用 success toast 代替节点、过程或图结果；
- stale completion 在当前 canvas 宣告成功；
- 把 Open Canvas Sonner skin、位置、message、provider 和 save/conflict 产品语义当 LibTV 规格；
- 复用 FrameOS toast 形成跨 route 状态。

## 18. Completion Criteria

只有同时满足以下条件，feedback slice 才可标记完成：

- 所有目标命令有 disposition、reason、owner、primary surface 和 clear/retry policy；
- reason 与 display copy 分离；
- reject/noop/stale/unknown 的 graph/history residue 为零；
- durable failure/conflict 有持续 recovery surface；
- visible result 不靠 generic success toast 证明；
- timer、retry、duplicate、switch、delete、unmount 和 burst 都可确定性复现；
- prototype 不宣称真实 provider/保存/计费/远端任务；
- LibTV/FrameOS route 隔离；
- exact source presentation 只由 current source evidence 决定；
- `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` 和 `LIBTV-VR-018` 通过；
- `npm run check` 和相关 browser regression 通过；
- 研究、实施、验证和 commit/push 历史落档。

当前最准确的总结是：

> Open Canvas 值得借鉴的不是“到处调用 toast”，而是它已经区分了 transient notification、node status/error、save/conflict surface 和 control busy；其 localized message identity 与无 owner 的 async toast 又提供了明确反例。当前 LibTV clone 有若干更好的局部 reason/owner 形状，但缺少统一 outcome-to-surface authority。后续复刻应先证明 command outcome，再决定反馈落点；不能用 toast 补齐未知 workflow，也不能让 transient UI 污染 graph/history。
