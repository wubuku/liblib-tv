# LibTV Verifier Replacement Map

> 目的：区分历史 clone 回归、当前 source contract、local fixture contract 和尚未具备 source fixture 的断言，给后续授权 batch 一条可审计的替换路径。
>
> 本文是文档和测试规划，不修改现有 verifier，也不把任何历史通过升级为当前 LibTV parity。当前 fixture 身份与 reset 见 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)；跨项目长期闸门见 [`DECISION_REGISTER.md`](../DECISION_REGISTER.md) 的 DEC-021 至 DEC-023。

## 1. 核心规则

现有 verifier 的“通过”只说明某个日期、某个 clone 实现、某个 fixture 和某个 selector 集合满足断言。它不自动说明：

- 当前源站仍然使用相同动作、几何或数据结构；
- clone 已经覆盖当前源站；
- 共享源站项目具备可重复的 ready/process/dirty fixture；
- 本地 mock 已经具备真实 Provider、上传、计费或持久化语义。

因此替换采用双轨策略：

```text
历史 verifier 保留为 compatibility regression
  + 新 source-shaped/local fixture verifier 并行建立
  -> 新 verifier 稳定并记录 source/clone 边界
  -> 再决定旧断言是保留、降级或退役
```

禁止为了让新实现通过而直接放宽、删除或重写旧断言。旧断言如果与当前 source contract 冲突，应先标成 `HISTORICAL_CONTRACT`，保留其 provenance。

## 2. 状态分类

| 分类 | 解释 | 允许的后续动作 |
|---|---|---|
| `CURRENT_SOURCE` | 当前日期 source DOM/bundle/截图或安全交互直接支持 | 可形成 source contract；仍需 clone fixture 才能回归 |
| `HISTORICAL_CLONE` | 旧日期 clone 实现/截图/脚本直接支持 | 保留兼容回归；不能推导 current source |
| `LOCAL_FIXTURE` | 当前 clone 通过稳定本地构造或 bounded transaction 支持 | 可回归 clone prototype；不称 source parity |
| `BLOCKED_SOURCE` | 需要 ready-video、输入、提交、保存或独立项目 | 登记所需 fixture 和停止条件，不在共享项目试探 |
| `REPLACEMENT_READY` | source contract、clone 实现、fixture 和新 verifier 都已具备 | 可在独立 commit 中申请替换旧断言 |
| `PARALLEL_WIP` | 其他开发者正在修改相关实现、fixture 或脚本 | 只读；不把当前文件当稳定基线 |
| `OUT_OF_SCOPE` | 需要真实 Provider、账户、计费、远程任务或生产资产 | 不创建前端 verifier 假装覆盖 |

这些分类与 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的 maturity 状态相关但不相同。一个 verifier 可以同时是 `SCRIPT_AVAILABLE` + `HISTORICAL_CLONE`，也可以是 `SCRIPT_AVAILABLE` + `LOCAL_FIXTURE`。

## 3. 按 Batch 的保留与替换矩阵

| Batch | 当前 verifier 价值 | 分类 | 需要替换/补充的内容 | 处理决策 |
|---|---|---|---|---|
| 4-8 | 分组、多选、移动、复制、导航、整理、parent-child 的 clone 行为 | `HISTORICAL_CLONE` + `LOCAL_FIXTURE` | 只有在 source contract 改变时补 source evidence | 保留；不把普通 graph 通过解释成全量源站一致 |
| 9 | 图片/视频双浮层中心、bottom gap、pan/zoom follow、自然裁切 | `HISTORICAL_CLONE` | current top action set、`1092.5px` width、`10 + 24 * zoom` top formula、同 frame rect | 保留旧脚本；授权后增加 current toolbar replacement |
| 10 | 五种图片 panel 内容/高度、旧 AutoLink popover | 混合 | 固定候选、56px popover、全量接受、textarea 前缀写回必须替换 | 保留图片 variant compatibility；AutoLink 断言隔离为 historical |
| 11 | top-level overlay 互斥、Escape、mobile overflow | `HISTORICAL_CLONE` + `LOCAL_FIXTURE` | 当前 modal/focus/backdrop 行为若 source refresh 漂移 | 保留；source freshness 后再补缺失 focus contract |
| 12-20 | asset、storyboard、Agent/share、canvas metadata、zoom/minimap、panorama | `LOCAL_FIXTURE` | 新 source evidence 仅在能力发生漂移时补 | 保留 bounded clone contracts |
| 21-22 | Seedance 普通/超长参数与模型菜单 | `LOCAL_FIXTURE` + source sampled | 当前 source action/number 版本化；真实 provider 不纳入 | 保留 prototype；数字标为 sampled |
| 23-25 | 片段重拍、逐帧拉片结果结构、智能剪辑空态 | `LOCAL_FIXTURE` + `BLOCKED_SOURCE` | source ready-video、result/version/process lifecycle | 保留 clone fixture；新增 source-ready contract 前不替换 |
| 26-33 | 续写、字幕、音视频分离、截帧、主体编辑、深度、长视频 | `LOCAL_FIXTURE` + `BLOCKED_SOURCE` | source ready/process/dirty fixture、失败和重试状态 | 保留 bounded graph/history；真实 lifecycle 单独新增 |
| 35-47 | Director R3F、timeline、path、capture/export、phone、pose、camera、groups、model proxy | `LOCAL_FIXTURE` + `HISTORICAL_CLONE` | source locale/entry 与 clone implementation 分开；真实资产不推导 | 保留 bounded Director regression；不迁移成普通 LibTV verifier |
| 48 | Director local model import/persistence workflow | `LOCAL_FIXTURE` + `HISTORICAL_CLONE` | 保留 clone-owned storage reset、focused verifier 和 bounded maturity；真实 mesh/远端同步另行阻塞 | 作为有界 Director regression 保留；不迁移成普通 LibTV 或源站 parity verifier |

Batch 34 是 research-only，不是缺失的 verifier；不要为它创建“补跑脚本”以填充编号。

## 4. 旧断言到新合同的迁移

### 4.1 `verify-liblib-batch9.py`

当前旧断言：

```text
toolbar width = 900.5px
toolbar height = 49px
toolbar top gap = 16px
bottom panel gap = 16 * zoom
center(toolbar) = center(node)
center(panel) = center(node)
```

处理方式：

| 断言 | 保留理由 | 新合同动作 |
|---|---|---|
| height `49px` | 与当前 source evidence 仍可能兼容 | 新 verifier 重新采样后确认 |
| bottom `16 * zoom` | 当前 source/clone positioning contract | 保留并补 panel height variants |
| 两者 node-center | 关键定位不变量 | 保留，要求同一 frame 读取 rect |
| width `900.5px` | 旧动作集合的结果 | 标为 historical；current source 目标为 content-sized `1092.5x49` |
| top gap `16px` | 旧 clone snapshot | 标为 historical；current source 目标为 `10 + 24 * zoom` |

新 verifier `VR-001` 只有在 `LIBTV-FIX-LOCAL-IMAGE-01`、当前 action-set contract 和明确编码授权都存在时才建立。它不能通过改写旧 Batch 9 的常量来完成替换。

### 4.2 `verify-liblib-batch10.py`

当前旧断言把下列 clone-only 行为当作一个 AutoLink 流程：

```text
Prompt 非空且 references 为空
  -> 显示固定“陈默、咖啡”候选
  -> 一个“引用”按钮全部接受
  -> 普通字符串前缀写回 textarea
```

它与当前 source contract 的 `global preference -> connected/reference candidate pool -> inline ghost -> structured mention` 不同。处理方式：

- 图片五种 panel variant 的尺寸、Prompt/reference 展示仍保留为历史图片编辑 compatibility；
- AutoLink popover selector、固定候选文案和全量接受断言标成 `HISTORICAL_CLONE`；
- 新 `VR-003..005` 不复用旧 selector，也不添加更多固定候选；
- 新断言使用 stable node ID、ghost/badge data marker、text version、IME 和 graph/reference/mention transaction；
- 没有 local AutoLink fixture 时只写纯 contract test/plan，不运行共享源站输入。

### 4.3 `verify-liblib-batch21.py` - `batch33.py`

这些脚本的主要价值是 clone UI closure、bounded graph transaction、selection 和 undo/redo。它们不能证明源站结果态。保留规则：

- 参数、菜单、空态、pending graph 和 mock 费用是 `LOCAL_FIXTURE`；
- `300s / 14700` 等值只作为日期化采样，不成为永久 API 断言；
- 12 process nodes / 22 edges 是本地 process shape，不是源站任务拆分；
- source-ready toolbar、real segment replacement、partial/failed/retry lifecycle 均进入 `BLOCKED_SOURCE`；
- 任何新 source verifier 必须使用独立 source fixture，并记录 version/time range/run/node/save status。

### 4.4 `verify-liblib-batch35.py` - `batch48.py`

Director 脚本的 domain state 通过 `window.__director_store` 驱动或读取，并拥有独立的 R3F、timeline、history、capture/export 语义。它们：

- 可以继续保护 bounded Director prototype；
- 不能作为普通 LibTV `canvasStore` fixture 或 source parity 验证；
- 真实 mesh/FBX/OBJ、摄影机设备、Provider 和远端资源不在当前合同内；
- Batch 48 已补齐 clone-owned local model 的 setup/teardown、storage boundary 和 focused verifier；这些断言仍只证明 Director prototype。
- 新增 Director persistence 或 local model fixture 时，必须由 owner 维护 setup/teardown 和 storage boundary，不得把普通 LibTV 的 reset 规则套进来。

## 5. Replacement Queue

### `LIBTV-VR-001`：当前 selected-image geometry/action set

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-001` |
| Old verifier | Batch 9 |
| Required fixture | `LIBTV-FIX-LOCAL-IMAGE-01`，current source read-only image role |
| New checks | current action IDs/order/width/height；top/bottom center；`10 + 24 * zoom`；`16 * zoom`；natural clipping |
| Blockers | coding authorization；current source action-set confirmation |
| Exit | focused desktop/mobile/zoom verifier + old Batch 9 compatibility retained |

### `LIBTV-VR-002`：active image low-risk replacement states

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-002` |
| Old verifier | 无 |
| Required fixture | local image；source empty Preview/Annotate/Element Edit read-only observations |
| New checks | standard double overlay replaced；open/close；selection/graph unchanged；mobile bounds |
| Blockers | explicit coding authorization；source state confirmation |
| Exit | one focused verifier per low-risk state，不能把 high-risk dirty action 混进来 |

### `LIBTV-VR-003`：AutoLink preference and candidate identity

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` |
| Old verifier | Batch 10 fixed popover assertions |
| Required fixture | `LIBTV-FIX-LOCAL-AUTOLINK-01`；source disposable only for input behavior |
| New checks | global preference；connected/reference candidate scope；stable node ID；ordinal projection |
| Blockers | runtime fixture implementation；local deterministic candidate adapter；source input authorization |
| Exit | image/video cross-node preference and candidate changes are separately asserted |

### `LIBTV-VR-004`：AutoLink ghost and keyboard race

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` / `PAR-004` |
| Old verifier | 无 |
| Required fixture | deterministic delayed detection、IME composition、competing popover |
| New checks | ghost does not mutate committed text；click/Tab single；Shift+Tab all；Escape/blur/edit cleanup；stale discard |
| Blockers | runtime editor/fixture implementation；deterministic race controls；编码授权 |
| Exit | no stale badge, no keyboard theft, no layout detachment after pan/zoom |

### `LIBTV-VR-005`：AutoLink graph/reference/mention transaction

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` / `PAR-008` |
| Old verifier | 无 |
| Required fixture | connected and unconnected candidates；success/failure connection outcomes |
| New checks | connect + mention atomicity；failure rollback；reference reorder changes ordinal only；undo/redo policy |
| Blockers | graph connection contract 已完成；Reference/source invalid lifecycle 仍未决；runtime transaction fixture；no orphan badge/edge implementation |
| Exit | node identity, reference role and mention token remain independently inspectable |

### `LIBTV-VR-006`：source ready-video toolbar

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-006` |
| Old verifier | Batch 27-32 local tool checks |
| Required fixture | `LIBTV-FIX-LOCAL-VIDEO-READY-01` + `LIBTV-FIX-SOURCE-VIDEO-READY-01` |
| New checks | ready/failed/pending branches；action order；hover menu；active replacement；discard/submit delta |
| Blockers | source disposable ready video |
| Exit | source contract and clone local contract are separate records |

### `LIBTV-VR-007`：process/result lifecycle

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-009` |
| Old verifier | Batch 24/33 bounded results/process graph |
| Required fixture | `LIBTV-FIX-LOCAL-PROCESS-STATES-01` + disposable source process if authorized；async mechanics compose `ASYNC-INGRESS-01` |
| New checks | pending/failed/partial/success/retry；run/node/save status；version/time range；replacement and retry；completion mechanics delegated to `VR-015` |
| Blockers | stable business interface or explicit local mock contract |
| Exit | no claim of real progress, billing or output quality |

正交 identity/state、stale completion、retry、local/source fixture 和 graph/history 断言统一见 [`open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。该矩阵完成的是 verifier 设计，不表示 fixture 或实现已经存在。

### `LIBTV-VR-008`：source-only shortcuts

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-007` |
| Old verifier | Batch 3/4/6/7 partial clone handlers |
| Required fixture | local and disposable source shortcut subgraph with internal/external edges |
| New checks | precondition、focus、cancel、selection、graph/viewport/history delta |
| Blockers | source fixture or explicit source contract |
| Exit | help row、handler、React Flow gesture and local context are separately asserted |

### `LIBTV-VR-009`：graph connection validation and transaction

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` |
| Old verifier | Batch 4-8 普通 graph regressions；保留，不改写为 current source parity |
| Required fixture | `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`；source static audit；真实 invalid lifecycle 另需 `LIBTV-FIX-SOURCE-GRAPH-CONNECTION-01` |
| Pure checks | 两侧 Handle direction normalize；missing/dangling；unordered pair duplicate precedence；self/cycle；stable result/reason；Reference/domain unknown |
| Browser checks | accepted normalized edge；rejected zero node/edge/selection/history delta；one-step accepted history；connection line/invalid feedback cleanup；pan/zoom identity；console/page errors |
| Blockers | Batch 57 已关闭 local structural validator/fixture；Reference/entry-point/source UI feedback、domain compatibility 和其他 graph entry points 仍未决 |
| Exit | pure + focused browser verifier 已 recorded；旧 Batch graph compatibility retained；source-only claims separate；完整 connection parity 仍未声称 |

结果形状、reason taxonomy、pipeline precedence、transaction no-op/atomicity、fixture topology 和授权 slice 统一见 [`components/LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)。该合同完成的是设计，不表示 runtime、verifier 或 source disposable fixture 已存在。

### `LIBTV-VR-010`：graph document and snapshot isolation

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` |
| Old verifier | Batch 3-8 undo/redo、selection copy、group 和 canvas duplicate regressions；保留各自历史合同 |
| Required fixture | `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` + `LOCAL-EMPTY/DEMO/GROUP/DERIVED` |
| Pure checks | V1 round-trip/order；runtime-field exclusion；future-version/ID/edge/parent/media reason；migration provenance；nested past/future isolation；viewport/selection exclusion |
| Browser checks | nested metadata command -> undo/redo；future clear；selection clear；viewport 独立；history step count；future import-as-new-canvas 另待 surface contract |
| Blockers | codec/validator/fixture/runtime 未实现；node data registry 设计已完成但 runtime missing；编码授权；import UI 未立项 |
| Exit | pure corpus + focused history verifier recorded；旧 Batch regressions retained；不宣称 persistence/source parity |

五层 shape、V1 conceptual schema、field/media 分类、parse/migration pipeline、zero-partial load、fixture corpus 和授权 slice 统一见 [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)。Open Canvas revision/file/KV/rebase 仍是 `DEFERRED_PRODUCT_SCOPE`，不是 `VR-010` 目标。

### `LIBTV-VR-011`：subgraph copy, identity rewrite and placement

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` |
| Old verifier | Batch 3/5/8 duplicate、group/child 和 undo/redo regressions；保留历史 source/clone 边界 |
| Required fixture | `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` + `LOCAL-GROUP/DERIVED` |
| Pure checks | root sanitize/closure/dedupe；parent map/detach；nodeMap/edgeMap；none/internal/incident policy；reference role；placement；connection abort；stable result/reason |
| Browser checks | single/multi/group/child duplicate；node/edge/parent/data/selection；pan/zoom-invariant offset；one-step undo/redo；editable/modal/preview ownership |
| Blockers | pure planner、reference-role registry、fixture 未实现；node data registry 设计已完成但 runtime missing；编码授权；system clipboard/Option-drag 另有 source/surface blocker |
| Exit | pure planner + focused current duplicate verifier recorded；old Batch retained；clipboard/Option-drag 不被虚构为 covered |

具名 copy command、closure、two-pass identity、parent/placement、node-data reference roles、edge policies、atomic transaction、packet、fixture 和授权 slice 统一见 [`components/LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)。Current single-node incident-edge 行为是 `COMPATIBILITY_HOLD`，不是新命令默认值。

### `LIBTV-VR-012`：node data registry, aggregate integrity and portability

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` / process and Director boundaries |
| Old verifier | Batch 5 copy、Batch 24/33 process/result、Batch 35-48 Director exported-result regressions；各自保留 bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-NODE-DATA-01` + `LOCAL-GRAPH-DOCUMENT/SUBGRAPH-COPY/LONG-PROCESS` |
| Pure checks | 11-type V0 allowlist；normalize/unknown field；field role；operation transform；nested isolation；shot reciprocal refs；process cohort；media class/budget；stable reason |
| Browser checks | registered shells render；mapped data attrs；one-step undo/redo；aggregate reject zero residue；UI/Director/editor session excluded |
| Blockers | canonical runtime registry、codec、fixture and verifier missing；编码授权；shot/process delete cascade and Director workspace semantics source/product-blocked |
| Exit | every runtime type and current identity-bearing V0 path has a tested rule；supported operations no longer rely on arbitrary shallow spread |

Registry model、canonical field roles、operation profiles、per-type/aggregate/media policy、reason taxonomy、fixture corpus 和 implementation slices 统一见 [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)。Static inventory 见 [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)。

### `LIBTV-VR-013`：relation-aware delete planning and repair

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` / process、overlay and resource boundaries |
| Old verifier | Batch 3 delete/history、Batch 8 group cascade、Batch 24 shot、Batch 26 clear continuation、Batch 27-33 derived/process、Batch 35/40 Director outputs；各自保留 bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-GRAPH-DELETE-01` + `LOCAL-NODE-DATA/GROUP/DERIVED/LONG-PROCESS`；source policy 使用 `SOURCE-GRAPH-DELETE-01` |
| Pure checks | requested/descendant/incident closure；selected-edge dedupe；registered inverse refs；owned ref repair/block；shot reciprocity；process cohort；stable plan/reason；zero mutation；media diagnostics |
| Browser checks | Delete focus ownership；edge scissors/relation clear；group cascade；edge-only selection；selection/top-bottom overlay/UI owner cleanup；one-step undo/redo；canvas fallback |
| Blockers | pure impact index/planner、fixture and verifier missing；编码授权；derived source、shot result、process member、Director workspace 和 active-run semantics source/product-blocked |
| Exit | every accepted delete leaves structural/data/aggregate/selection integrity；unknown/reject leaves graph/history/UI unchanged；old bounded regressions retained |

Delete command inventory、Open Canvas boundary、relation topology、policy matrix、decision queue、fixture scenes and implementation slices 统一见 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)。

### `LIBTV-VR-014`：graph mutation entry-point authority

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` cross-entrypoint correctness |
| Old verifier | Batch 3-8 graph/history/group、Batch 24/26-33 derived/process、Batch 57 connection；各自保留 bounded semantic contract |
| Required fixture | `LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` composed from `GRAPH-CONNECTION/DOCUMENT/SUBGRAPH-COPY/NODE-DATA/GRAPH-DELETE` |
| Static checks | enumerate graph-writing actions/callers；T0-T5 classification；flag unclassified direct writes and generic setter bypass；exclude FrameOS |
| Pure checks | equivalent ingress reason；T1 whitelist；T3 full-draft zero-partial；T4 invalid restore cursor stability；T5 stale patch；one-step accepted history |
| Browser checks | real Handle retained；drag/organize field allowlist；edge/node deletion routes；undo/redo owner cleanup；no console/visual edge regression |
| Blockers | authority boundary、transport whitelist、planner/restore/remote adapters and fixture missing；编码授权；future backend/persistence deferred |
| Exit | every graph write ingress classified；no semantic mutation bypasses `VR-009..013` authority；accepted/rejected history behavior exact |

Ingress inventory、Open Canvas layered boundary/limitations、T0-T5 model、decision queue、fixture and implementation slices 统一见 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)。

### `LIBTV-VR-015`：async result ingress and stale convergence

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-009` completion correctness；composes `PAR-008` graph authorities |
| Old verifier | Batch 24 shot completion、Batch 27/30-33 delayed derived/process、Batch 40 Director export；各自保留 bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` + `LOCAL-EMPTY-01` + reused graph data/delete/entrypoint authorities |
| Static checks | enumerate timer/promise/poll/subscription graph writers；operation/run/result/source-version identity；no anonymous delayed write |
| Pure checks | current/stale/duplicate/invalid disposition；field owner；draft/source drift；retry race；delete/undo；idempotent projection；resource transfer/release |
| Browser checks | controlled completion queue/fake clock；unrelated selection/surface preserved；no per-poll history；one accepted graph commit；zero-mutation reject |
| Recovery checks | terminal envelope survives injected projection failure；retry does not re-invoke provider；duplicate delivery exact no-op |
| Blockers | identity/reconciliation runtime、fixture queue/resource ledger missing；编码授权；source version and real backend/provider remain blocked/out of scope |
| Exit | every graph-producing completion is owner-checked and idempotent；stale/duplicate cannot overwrite draft、selection、history or graph；resource owner exact |

Open Canvas positive control-plane evidence、fixed stale-write limitations、clone delayed-writer inventory、`GI-023..030/GC-024..033` and implementation slices 统一见 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。`VR-015` 检查 completion mechanics，`VR-007` 检查 process/result state meaning；二者不互相替代。

### `LIBTV-VR-016`：React Flow change routing and transport whitelist

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008` T0/T1 framework adapter correctness；sub-verifier of `VR-014` |
| Old verifier | Batch 3/5 selection/drag/history、Batch 57 connect/delete compatibility；保留各自 bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` + fresh Page + exact 12.11.1 change corpus |
| Static checks | exhaustive NodeChange/EdgeChange classifier；no direct unclassified apply；edge has selection-only T0；semantic variants use named command |
| Pure checks | whole-batch reject/reroute；finite payload；same-ID ordering；stale element/canvas；runtime-field projection |
| Store checks | reducer base is current store snapshot；stale render cannot drop newer edge；mixed invalid batch has zero partial effects |
| Browser/history | real node/edge selection、drag frames + one stop、measurement、named delete/connect；no visual/overlay regression |
| Current maturity | Batch 61 `SCRIPT_RECORDED_PASS`：classifier/store adapter、edge session owner、fixture corpus、真实 browser/history 与相邻回归已通过 |
| Remaining blockers | resize/reconnect source/product scope blocked；primary/focus/context 交给 `VR-019`；portable document 全面 sanitation 仍由 `VR-010..012` 组合验证 |
| Exit | only T0 selection and allowed T1 node transport reach generic reducer；semantic identity never bypasses command；history and sanitation exact |

Exact framework taxonomy、Open Canvas comparison、routing matrix、stable result vocabulary、`GI-031..037/GC-034..043` and implementation slices 统一见 [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)。`VR-016` 细化 `VR-014` 的 framework adapter，不替代 connection/delete/document/copy 专项 verifier。

### `LIBTV-VR-017`：multi-canvas lifecycle and owner isolation

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008/011` graph-lifecycle + UI-owner cross-cutting correctness |
| Old verifier | Batch 16 canvas CRUD/dropdown、Batch 17 active projection、Batch 58 node-bound owner；各自保留 bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` with deterministic A/B/C graph/viewport/history/UI/transient/async/resource owners |
| Static checks | canvas owner manifest；unknown active target guard；page refs/callbacks and delayed writers carry canvas/generation；FrameOS excluded |
| Pure checks | create/switch/rename/duplicate/delete plan/result；active/fallback/final policy；zero-partial；resource/operation impacts |
| Store checks | registry/active/selection/history atomicity；target viewport restore；duplicate empty history；delete target cleanup |
| Race checks | organize/drag/connection/viewport callback after switch；old timer/save response cannot mutate current owner |
| UI/browser | node-bound close；projection panel close/rebind；global preference exact；Batch 16/58 desktop/mobile regressions |
| Blockers | lifecycle planner/generation/transient registry/resource ledger/fixture missing；编码授权；source final/fallback/panel/background decisions |
| Exit | no graph/UI/history/viewport/async/resource owner crosses canvas implicitly；every lifecycle command has exact one-result behavior |

Open Canvas positive URL/hydrate/delete methods、stale local-convergence counterexample、clone owner audit、`GI-038..048/GC-044..058` and decision queue 统一见 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。`VR-017` composes `VR-010..016`，不取代其 graph/data/async 专项断言。

### `LIBTV-VR-018`：command outcome and feedback ownership

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-004/008..011` command result、feedback、owner、prototype-boundary cross-cutting correctness |
| Old verifier | Batch 14/15/23/24/29/30/32/33/40/41/44/57/58/60；各自保留 source/local bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` with deterministic disposition/reason、fake timer/announcement clock and A/B owner scenes |
| Static checks | every target command has reason registry、primary surface、owner、clear/retry/dedupe policy；FrameOS isolated |
| Pure checks | disposition/reason/args stable；display copy not branch identity；unknown fallback bounded；prototype honesty |
| Transaction | reject/noop/stale zero graph/history；accepted exact history；toast/timer/focus excluded from document/history |
| Owner/timing | node/canvas/surface/attempt identity；switch/delete/unmount/retry/duplicate/burst reconciliation exact |
| UI/browser | persistent recovery、field association、busy state、no duplicate announcement、desktop/mobile geometry/pointer/focus |
| Blockers | common outcome adapter、feedback owner ledger、fixture、encoding authorization；exact source toast/invalid style/timeout unavailable |
| Exit | one primary authority per outcome；durable error recoverable；visible result not toast-only；stale never announces current success |

Open Canvas toast/node/save/form 正反面、clone feedback inventory、`GI-049..058/GC-059..075` and decision queue 统一见 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)。`VR-018` composes connection/delete/async/canvas/overlay verifiers，不取代其 source/graph semantics。

### `LIBTV-VR-019`：selection, focus and command-context ownership

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-004/007/008/011` selection、keyboard、foreground surface、focus and route-isolation correctness |
| Old verifier | Batch 3/4/6/7/11/50/58/60；各自保留 source/local bounded contract |
| Required fixture | `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` with deterministic node/edge/primary selections、focus zones、surface stack and A/B canvas generations |
| Static checks | every target surface declares selection/context/focus policy；node/edge/primary owner unique；FrameOS isolated |
| Pure checks | selection normalization、context precedence、dispatch result、single-layer Escape and focus fallback deterministic |
| Transaction | selection/focus/context transitions are zero semantic history；mixed delete/undo/switch outcomes preserve graph/history authority |
| Owner/timing | canvas generation、surface owner、focus origin/return target validated；delete/switch/unmount/stale return cleanup exact |
| UI/browser | activeElement、editable isolation、modal containment、Director precedence、one Escape per layer、fallback focus and desktop/mobile parity |
| Blockers | exact source multi-select/edge/Escape/focus details remain partial；universal mixed primary、focus trap 和 target-scoped containment 未实现 |
| Exit | one validated active selection；one top command context；one Escape unwinds one layer；focus never returns to stale/hidden owner；clone-owned focused slice is recorded |

Open Canvas selected flags/editable/Radix delegation 和 clone node/edge/listener/modal/Director audit 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)，正式状态、优先级、fixture 和 verifier 合同见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。`VR-019` 组合 graph routing、multi-canvas、overlay 和 shortcut verifier，不替代各自的 source/semantic contract。

### `LIBTV-VR-020`：viewport, coordinate, gesture and placement authority

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-001/002/007/008/011` spatial、overlay、navigation、graph-placement and canvas-lifecycle correctness |
| Old verifier | Batch 6/7/16/18/19/51/60/61/62；Batch 63 actual-host default-add、Batch 64 Asset host-resize 与 Batch 65 responsive bootstrap ownership focused slices；各自保留 bounded navigation、organize、canvas、zoom/minimap、routing/context、overlay、default-add、drawer-layout and viewport-owner contract |
| Required fixture | `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` with deterministic A/B canvas generations、actual host epochs、nested/measured nodes、layout states and viewport operation clock |
| Static checks | every conversion and placement writer declares domain/owner/strategy；ordinary default add does not use browser window center；FrameOS/Director viewport domains isolated |
| Pure checks | finite validation、client/host/flow round trip、parent-world resolution、host-center placement、resize anchor preservation、stale/idempotent session reduction |
| Store/transaction | live/stable/bootstrap ownership exact；viewport zero semantic history；drag/add/duplicate/organize preserve adjacent one-step history and selection contracts |
| UI/browser | actual host rect、pan/zoom frames/end/cancel、asset-open/compact resize、canvas switch stale callbacks、default/derived/duplicate placement and selected-overlay same-frame geometry |
| Implemented slice | Batch 63：finite host-center helper、page-owned `screenToFlowPosition`、Add Node/Character callback；Batch 64：Asset open/close/X/Canvas-context capture/reconcile、operation/canvas/instance/viewport guards；Batch 65：bootstrap/stable page-session owner、stored viewport restore、projection echo and stale/invalid callback guards；三批均验证 zero graph/history/selection mutation |
| Blockers | full live/stable endpoint split、generic generation/host epoch/session owner、browser resize anchor、full fixture、derived/duplicate/organize/selected-overlay composition；exact source add/fit/zoom/resize/drop behavior partial |
| Exit | one domain per point；one current spatial owner；actual-host placement exact；stale/cancel leaves zero residue；overlay and graph/history contracts compose without visual transplant |

Open Canvas dual-anchor/live-stable/placement evidence、clone host/window and transient audit、`LIBTV-VGP-I-001..032` and decision queue 统一见 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)。`VR-020` 组合 overlay、React Flow routing、multi-canvas、copy、organize 和 shortcut verifier，不取代其 source visual、graph semantic 或 route-specific contract。

### `LIBTV-VR-021`：media ingress and resource lifecycle authority

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-008/009/010/011/014` media intent、graph projection、prototype honesty、canvas isolation and resource lifecycle correctness |
| Old verifier | Batch 12/15 Add Resource、Batch 17 asset/canvas projection、Batch 24 Shot、Batch 40/46/48 Director media；各自保留 bounded mock/local-preview/data/blob contract |
| Required fixture | `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` with synthetic files、deterministic classifier/probe/fake materializer/resolver clock、A/B generations、asset/reference/reachability ledger and object URL counters |
| Static checks | every ingress declares profile/owner/identity/classifier/materializer；`File`/`Blob`/object URL excluded from semantic history/document；upload/history/material/asset/Shot/Director surfaces remain distinct |
| Pure checks | typed validation/probe result；original-order cohort convergence；full projection plan；replace last-known-good；stale/duplicate/cancel disposition；locator portability and capability honesty |
| Transaction | provisional zero graph/history；accepted cohort exact declared graph/selection/history；invalid/noop/stale/cancel zero residue；asset attach does not claim upload |
| Resource checks | preview/probe lease create/transfer/release exact；delete/undo/redo/copy/editor/history reachability；stable asset delete separate from graph delete；no leak/double revoke/use-after-revoke |
| UI/browser | chooser cancel、mixed/out-of-order cohort、item-local error/retry、replace failure retention、switch/delete/retry races、honest local-preview/unavailable、route isolation |
| Blockers | common classifier/materializer/lease/asset/reference runtime、fixture and encoding authorization；source exact limits/progress/cancel/placement/register/restore and real backend remain blocked/out of scope |
| Exit | every media entry has one current owner and declared transaction；semantic commit only after owner-valid materialization；resource transfer/release exact；no surface or capability is falsely conflated |

Open Canvas `OC-061..070` 正反面、clone/source dated audit、ten entry profiles、`GI-071..084/GC-091..108` and implementation slices 统一见 [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)。`VR-021` 组合 `VR-010/012..015/017/018/020`，但不取代 graph codec、node data、delete、async、canvas、feedback、placement 或 Director 专项合同。

### `LIBTV-VR-022`：foreground editor session, commit and local-history authority

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-004/008/009/011/015` foreground context、graph history、request/result、owner cleanup and editor-session correctness |
| Old verifier | Text/Picture/Subtitle/Segment/Camera/image-mode/video-toolbar Batch verifiers；各自保留 bounded local/runtime contract，不推导共同 session/history authority |
| Required fixture | `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` with deterministic text/config/record/range/request/empty owners、small bitmap buffers、session/source versions、fake async/resource/focus/graph oracles |
| Static checks | every editor declares profile/session/baseline/history/commit/close policy；enabled commands have handlers；bitmap/history resources excluded from semantic graph document |
| Pure checks | semantic dirty/no-op、legal transitions、gesture coalescing/redo truncation、byte eviction/release、drift/delete/switch/IME、async descriptor/idempotency and route isolation |
| Transaction | unaccepted/local edits zero graph history；accepted sync edit exact one graph step；invalid/noop/cancel/stale zero residue；graph undo after close does not revive local session |
| UI/browser | cancel blur guard、local-vs-graph undo precedence、duplicate submit lock、owner invalidation、focus return、empty-mode disabled commands、small bitmap budget crossing |
| Blockers | common profile/session/history/commit runtime、fixture and encoding authorization；source exact blur/Enter/Escape/outside/restore/save/close and real raster/provider remain blocked/out of scope |
| Exit | one current editor owner、one declared undo owner、typed commit/close result、deterministic budget/resource cleanup and no enabled inert command |

Open Canvas `OC-071..080` 正反面、clone dated audit、ten profiles、`LIBTV-EDS-I-001..040`、`GI-085..100/GC-109..126` and implementation slices 统一见 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)。`VR-022` 组合 `VR-010/013..015/017..021`，但不取代各 profile 的 source visual、graph/async/resource、selection/focus 或 route-specific contract。

### `LIBTV-VR-023`：media rendition, aspect and node geometry authority

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-001/002/008/009/011/014/015/016` visual geometry、media truth、graph projection、prototype honesty、canvas isolation、editor continuity and rendition correctness |
| Old verifier | Batch 9/29/31/52/53/54/60 以及 Shot/Director 相关 bounded contracts；各自保留已证 surface/fixture，不推导共同 media/frame/node geometry authority |
| Required fixture | `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` with square/portrait/landscape/odd-size stills、video poster/video descriptors、mixed-output identity、invalid metadata and deterministic measurement clock |
| Static checks | intrinsic、declared、media-frame、graph-node、measured and editor-stage dimensions各有唯一 owner；每个 surface 声明 rendition profile、fit policy、frame policy、fallback and mutation authority |
| Pure checks | finite/provenance validation；contain/cover transform；frame derivation；mixed-output disposition；status-independent geometry；measurement epoch and stale-result rejection |
| Transaction | accepted output/frame change is one declared graph/history transaction；passive load、measurement、preview、detail and metadata observation are zero graph history；invalid/stale/no-op leaves zero residue |
| UI/browser | square/portrait/odd-size composition；node/detail/editor rendering；status transition stability；selected toolbar/panel freshness；editor round-trip；zoom/resize/switch/delete and route isolation |
| Blockers | common rendition/profile/measurement runtime、focused fixture and implementation authorization；source portrait/square/video/mixed-output/resize evidence remains partial |
| Exit | one authority per dimension；current frame/fit is explicit；no stale anchor/editor transform；no silent crop, distortion, fabricated resize or metadata-driven graph mutation |

Open Canvas `OC-081..090` 正反面、clone/source dated audit、surface profiles、`LIBTV-MRG-I-001..040`、`GI-101..116/GC-127..145` and decision queue 统一见 [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)。`VR-023` 组合 `VR-001/002/010/013..022`，但不取代 source visual、editor-session、graph、resource、overlay positioning 或 route-specific contract。

## 6. Replacement Protocol

每个 `VR-*` 都按下列顺序执行：

1. 读取对应 source contract、fixture catalog 和旧 Batch implementation；
2. 在 PLAN 中写明 old verifier、new contract、fixture ID、out of scope 和 stop conditions；
3. 没有编码授权时只补文档、pure contract 或 source read-only evidence；
4. 获得授权后，先新增 verifier，不删旧 verifier；
5. 使用新 Page 或显式 fixture reset，记录初始/终态 graph、selection、viewport、history 和 storage；
6. 桌面、移动端、必要 zoom/边缘裁切和 console/page/request errors 分开断言；
7. 记录 focused pass、serial regression、截图解释、source/clone boundary；
8. 只有当新 contract 稳定、旧兼容价值已评估、文档已链接后，才考虑退役过时断言；
9. 每个 batch 做 path-scoped commit/push，不混入其他开发者 WIP。

## 7. 不能作为替换证据的事情

| 看似有用的信号 | 实际不能证明 |
|---|---|
| 历史 screenshot “final” | 当前源码仍相同 |
| 旧脚本 exit 0 | 当前 source parity |
| clone 按钮能点击 | source action、task 或 graph lifecycle |
| 一次 source undo | 远端 mutation 已清理 |
| clone `status=ready` | source ready-video toolbar |
| clone 12/22 process graph | source 真实任务拆分 |
| Open Canvas 有 typed state | LibTV 使用同样数据结构 |
| Batch 48 local storage 成功读写 | 普通 LibTV store 已具备持久化 |
| clone 能显示 object URL/data URL 预览 | 已完成上传、可刷新恢复、资源可安全释放或 asset 已注册 |

## 8. Current Decision

截至 2026-08-27：

- Batch 9/10 的历史断言继续保留，不扩写为当前 source contract；
- Batch 21-33 的 local process/result checks 继续保留为 bounded clone fixture；
- Batch 35-47 继续保留为 bounded Director regression，不迁移到普通 LibTV；
- Batch 48 已是 bounded Director `recorded pass`，保留其 setup、storage、脚本、截图和实施记录；不把 local descriptor/proxy 解释为真实资产、远端同步或 LibTV persistence；
- 新 current-source verifier 只有在 source freshness report、fixture ID、明确授权和 replacement plan 同时存在时才进入实现批次；
- `LIBTV-VR-009` 的 local structural slice 已由 Batch 57 实现并通过；Reference/domain/source invalid lifecycle、import/batch/sync 仍保持未完成，不得把 Batch 57 升级为完整 connection parity；
- `LIBTV-VR-010` 的 document/snapshot contract、fixture corpus 和 replacement design 已完成，但保持 `RUNTIME_MISSING`；不得用 JSON round-trip 静默丢字段，或把 import failure 退化为空画布；
- `LIBTV-VR-011` 的 copy planner/reference/fixture/replacement design 已完成，但保持 `RUNTIME_MISSING`；不得把 incident-edge compatibility 推广到 group/clipboard，也不得只 remap structure 而忽略 node data identity；
- `LIBTV-VR-012` 的 11-type registry、aggregate/media fixture 和 replacement design 已完成，但保持 `RUNTIME_MISSING`；不得把 `Record<string, unknown>`、suffix-based ID rewrite 或 shallow spread 当作 codec；
- `LIBTV-VR-013` 的 relation-aware delete planner、repair policy、fixture scenes 和 replacement design 已完成，但保持 `RUNTIME_MISSING`；不得先删 node/edge 再以 UI effect 或 suffix heuristic 修补 surviving refs；
- `LIBTV-VR-014` 的入口审计、T0-T5 authority、fixture composition 和 replacement design 已完成，但保持 `RUNTIME_PARTIAL`；不得用 Batch 57 `addEdge` 通过推导所有 direct writer 已受保护；
- `LIBTV-VR-015` 的 Open Canvas/clone static audit、freshness/field/history/resource contract、fixture corpus 和 replacement design 已完成，但保持 `RUNTIME_MISSING`；不得把 component timer、node status 或 generic patch 当成 accepted operation owner；
- `LIBTV-VR-016` 已由 Batch 61 形成 focused `SCRIPT_RECORDED_PASS`；`LIBTV-VR-017..019` 的 multi-canvas lifecycle、command feedback、selection/focus/context replacement design 已完成，runtime maturity 分别维护；不得用 routing pass、局部 selected flag、组件 Escape handler、toast 或 focus effect 推导全局 authority已统一；
- `LIBTV-VR-020` 的 six-domain spatial model、actual host、live/stable/bootstrap viewport、gesture/placement owner、fixture corpus 和 replacement design 已完成；Batch 63/64/65 已分别关闭 actual-host default add、Asset host-resize anchor 与 responsive bootstrap/stored-viewport owner 的 focused runtime slices，但整体保持 `RUNTIME_PARTIAL / SOURCE_PARITY_PARTIAL`；不得用这些局部 pass、controlled viewport 或 Open Canvas Quick Add 推导普通 LibTV 空间权威已经统一；
- `LIBTV-VR-021` 的 ten entry profiles、validation/probe/materialization、cohort/replace、asset/reference、lease/reachability、fixture corpus 和 replacement design 已完成，但保持 `RUNTIME_MISSING_OR_PARTIAL / SOURCE_PARITY_PARTIAL`；不得用 mock upload、object URL preview、data/blob locator 或 Open Canvas upload route 推导 durable asset/resource lifecycle 已实现；
- `LIBTV-VR-022` 的 ten editor profiles、baseline/draft、native/local/graph undo、commit/close/drift、bitmap budget、fixture corpus 和 replacement design 已完成，但保持 `RUNTIME_FRAGMENTED / SOURCE_PARITY_PARTIAL`；不得用局部 `useState`、30-step snapshot、submitted copy 或可见 Undo/Save 图标推导共同 editor authority 已实现；
- `LIBTV-VR-023` 的 dimension authority、rendition/frame/fit profiles、measurement epoch、mixed-output disposition、fixture corpus 和 replacement design 已完成，但保持 `RUNTIME_FRAGMENTED / SOURCE_PARITY_PARTIAL`；不得用 landscape 单样本、CSS width/height、图片 `onLoad`、Director animation method 或可见 contain/cover 结果推导共同 media geometry authority 已实现；
- 在此之前，最有价值的后续工作仍是文档、纯合同和安全只读证据整理。

相关入口：[`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)、[`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)、[`liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)。
