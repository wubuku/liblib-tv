# LibTV Graph Document And Snapshot Contract

> Scope: 普通 LibTV route 的运行 graph、命令 history snapshot、可移植 graph document、schema version、migration、load transaction、fixture 和 verifier 设计。
>
> Status: `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` / `PERSISTENCE_DEFERRED`。本文不授权修改 `src/`、测试脚本、普通画布 persistence 或共享源站状态。

## 1. Why This Contract Exists

当前 clone 已经有复杂的 group、派生节点、process metadata、media history 和 50-step graph history，但这些对象仍直接建立在 React Flow `Node[] / Edge[]` 与浅复制 `data` 上。后续继续复刻 LibTV 时，如果不先区分“运行对象”“撤销快照”“可导入文档”和“远端保存记录”，会产生三类风险：

1. nested metadata 被后续 mutation 反向污染旧 history；
2. React Flow 临时字段、selection、DOM measured state 或本地 `blob:` URL 被误当持久合同；
3. 为了借鉴 Open Canvas 的 version/revision，一次性引入当前 prototype 未授权的保存、冲突或协作语义。

本文只完成边界和验证设计。它不声称 LibTV 源站使用同样 schema，也不把文档完成解释为 import/export 已实现。

## 2. Evidence And Inspiration Boundary

### 2.1 `OPEN_CANVAS_FACT`

固定 submodule `cf3a906bb8c35bb940d3267497e7f394b8f42582` 明确分开：

- React Flow runtime nodes/edges/viewport；
- `version: 1` 的 `SerializedCanvasGraph`，只包含 viewport、nodes 和 edges；
- flow <-> graph serialization/normalization；
- API 边界的严格 parse/validate，包括数字、node type、ID、endpoint、数量和 DAG；
- local DB 的 tolerant normalization、DB version、file/KV storage；
- document `revision`、`savedGraphString`、dirty/save/conflict 和 1.2s debounce；
- template snapshot 对 node run-time status 的 reset；
- base/local/remote 三方 revision rebase。

直接源码：[`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts)、[`serialization.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts)、[`validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts)、[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts)、[`local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts)。

这些只证明“分层、版本化、边界校验”是可借鉴方法。Open Canvas 的五类 node、`200/400` 数量上限、DAG 产品约束、revision merge、file/KV persistence、template 字段清理和 provider data 都不是 LibTV 产品事实。

### 2.2 `CLONE_FACT`

当前 clone：

- [`canvasStore.ts`](../../../src/store/canvasStore.ts) 的 `CanvasData` 是 in-memory `id/name/nodes/edges/viewport`；普通画布没有 persist middleware、导入/导出 API 或 save status；
- `GraphSnapshot` 只有 nodes/edges，不含 viewport、selection、canvas metadata、UI 或 save state；
- `cloneGraphSnapshot()` 只复制 node、position、style、顶层 data 和 edge 顶层对象，nested arrays/objects 仍共享引用；
- `duplicateCanvas()` 会重写 node/parent/edge IDs，但 node data、edge data 和 viewport 没有形成独立 portable schema；新 canvas history 为空；
- `duplicateGraphSelection()` 已有 descendant closure、ID map、parent rewrite、内部/外部 edge 分支和位置处理，但它仍消费 runtime `Node/Edge`；
- [`src/types/canvas.ts`](../../../src/types/canvas.ts) 的公开 node union 少于当前 runtime node 类型，不能直接充当完整 serialization schema；
- selection、viewport、canvas lifecycle 和 graph history 已被刻意分成不同 command domain；
- Director 有独立 store/persistence 边界，不能推广为普通画布合同。

## 3. Five Separate Shapes

后续设计必须保留以下五种身份，不能用一个 `CanvasData` 覆盖全部用途。

| Shape | Owner | 包含 | 明确不包含 |
|---|---|---|---|
| `RuntimeGraphState` | React Flow + `canvasStore` | runtime nodes/edges、live viewport、render/interaction fields | portable schema 保证 |
| `GraphHistorySnapshot` | per-canvas undo/redo | 一个命令前的 declared graph fields | viewport、selection、canvas CRUD、UI/save state |
| `PortableGraphDocument` | future import/export/new-canvas construction | versioned JSON-safe graph、layout、semantic data | history、selection、DOM refs、provider task/runtime refs |
| `ClipboardSubgraphPacket` | duplicate/copy/paste | selected closure、relative placement、internal relations、packet version | whole canvas viewport、canvas identity、external edges by default |
| `PersistenceEnvelope` | future product/backend | document ID、revision、timestamps、save/conflict state around a graph document | 当前 prototype 的既成能力 |

`GraphHistorySnapshot` 和 `PortableGraphDocument` 可以复用纯 node/edge codec，但它们不是同一个产品对象。特别是 viewport：portable document 可包含它，当前 graph undo 明确不恢复它。

## 4. Portable Document V1

以下是 clone-only conceptual schema。最终 TypeScript module、parser library 和 exact node-data union 留给获授权计划决定。

```ts
type JsonPrimitive = string | number | boolean | null;
type JsonValue =
  | JsonPrimitive
  | JsonValue[]
  | { [key: string]: JsonValue };

type LibTVGraphDocumentV1 = {
  kind: "libtv-canvas-graph";
  schemaVersion: 1;
  canvas: {
    name: string;
    viewport: { x: number; y: number; zoom: number };
  };
  nodes: SerializedLibTVNodeV1[];
  edges: SerializedLibTVEdgeV1[];
};

type SerializedLibTVNodeV1 = {
  id: string;
  nodeType: string;
  dataVersion: 1;
  position: { x: number; y: number };
  parentId?: string;
  extent?: "parent";
  width?: number;
  height?: number;
  zIndex?: number;
  data: { [key: string]: JsonValue };
};

type SerializedLibTVEdgeV1 = {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  edgeType: "default";
  data?: { [key: string]: JsonValue };
};
```

Design choices:

1. `schemaVersion` 是 portable graph 格式版本，不是 LibTV 产品版本、source date、canvas revision 或 undo index；
2. `dataVersion` 允许不同 node type 独立迁移，避免整个 graph 因一个 metadata 字段变化同时升级；
3. canvas ID、project ID 和 source URL 不成为 portable identity；导入为新 canvas 时生成新的 canvas ID；
4. node/edge ID 在 document 内稳定，用于 parent、edge、mention 和 metadata reference 的迁移；
5. node/edge 数组顺序保留，因为 React Flow render order、group-before-child 和 z-order 可能依赖它；
6. arbitrary `style` 不进入 V1；稳定 layout 只白名单化 width/height/zIndex，避免 CSS/runtime object 变成数据合同；
7. edge renderer 固定为当前 `default` 产品合同；不能通过 import 改写 `DeletableEdge` flow effect；
8. exact node type registry 仍需单独静态审计。当前 `src/types/canvas.ts` 不足以作为 allowlist。

## 5. Field Classification

### 5.1 Persistable semantic fields

可以进入 node `data` 的候选必须满足：

- 对用户工作内容有稳定语义；
- 是 JSON-safe value；
- 不依赖当前 DOM、Page、BrowserContext 或 provider task object；
- 有 nodeType + dataVersion 的 normalize/validate 规则；
- 复制后不会让新节点继续冒充原节点身份。

典型候选：title/prompt、媒体尺寸、duration、ratio、operation kind、time range、regions/marks、source node/version identity、process stage、candidate identity 和 stable asset reference。

### 5.2 Runtime/session fields

以下默认不进入 portable document：

- `selected`、`dragging`、`resizing`、hover、focus、active toolbar/panel/tool；
- React Flow `measured`、DOM rect、internals、event handler、component/ref；
- page-level preview、dialog、toast、pending connection、invalid-target feedback；
- graph history stacks、redo future、current selection；
- Director Three.js runtime refs、renderer、camera object、capture session；
- `File`、`Blob`、`HTMLImageElement`、`CanvasRenderingContext2D`、Promise、Map/Set、Date/function/class instance。

### 5.3 Media references

| Form | V1 decision |
|---|---|
| stable `https:` URL + metadata | JSON-safe reference；不承诺 reload 时仍可访问 |
| stable asset ID + metadata | preferred future identity；当前 backend 未实现 |
| `blob:` object URL | `NON_PORTABLE_MEDIA_REFERENCE`；不得静默保存为可恢复资产 |
| `data:` URL | clone-only embedded asset；必须有 byte budget 和 explicit provenance，不能无限进入 50-step history |
| provider task/request/response object | 不进入 graph document；只存经合同允许的 stable projection |

V1 不定义真实资产上传。遇到 non-portable media 时返回 diagnostics 或显式 unresolved state，不用空字符串伪造成功 round-trip。

## 6. History Snapshot Contract

### 6.1 Included boundary

`GraphHistorySnapshotV1` 只保存命令域内的 nodes/edges 和 schema marker：

```text
schemaVersion
nodes: deep-isolated declared graph fields
edges: deep-isolated declared graph fields
```

它继续不包含 viewport、selection、canvas name/list、project name、top-level UI、save status 或 remote effects。这保持当前 [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md) 已建立的 undo 边界。

### 6.2 Isolation requirements

- snapshot 中每个 nested object/array 必须与 current graph 隔离；
- action 只能以 immutable replacement 更新 node/edge metadata；
- push/undo/redo 后 mutation 新 graph，旧 past/future snapshot 不得变化；
- snapshot clone 失败必须使命令停止，不得先改 graph 再丢 history；
- selection 仍是 transaction output；undo/redo 后按当前合同清空，不从 snapshot 恢复；
- viewport 仍由 viewport command/domain 管理，不因深 snapshot 被顺手加入 graph undo。

`structuredClone` 可能是实现候选，但不能在未审计 data shape 前直接采用。Portable document 需要 JSON-safe codec；history 可以使用更窄的 declared graph codec。两者都不能通过 `JSON.stringify/parse` 静默丢弃 `undefined`、unsupported instances 或超大 embedded media。

### 6.3 Cost boundary

当前 `MAX_HISTORY = 50`。深隔离后需要测量：

- demo/group/long-process graph 每步 payload size；
- marks/regions/process arrays 的复制成本；
- data URL 对 history memory 的放大；
- drag compression 后只产生一个 snapshot 的保证。

未测量前不引入 patch log、Immer history 或 content-addressed asset store。先保证 correctness，再用具名 fixture 证明是否需要优化。

## 7. Parse, Migration And Validation Pipeline

```text
unknown bytes/value
  -> syntax parse
  -> envelope/kind/schemaVersion
  -> supported-version decision
  -> pure sequential migration
  -> node/edge field normalization
  -> structural validation
  -> node-data registry validation
  -> connection/import policy validation
  -> portable-media diagnostics
  -> ready document or zero-mutation result
```

### 7.1 Result shape

```ts
type GraphDocumentLoadResult =
  | { status: "ready"; document: LibTVGraphDocumentV1 }
  | {
      status: "migrated";
      document: LibTVGraphDocumentV1;
      fromVersion: number;
      warnings: GraphDocumentWarning[];
    }
  | { status: "reject"; reason: GraphDocumentRejectionReason }
  | {
      status: "unsupported";
      reason: "UNSUPPORTED_FUTURE_VERSION" | "UNMODELED_NODE_DATA";
    };
```

`unsupported` 不等于空画布，也不等于可以丢弃未知字段后继续。任何非 ready/migrated 结果对 canvas list、graph、selection、history 和 viewport 都是 zero mutation。

### 7.2 Stable rejection reasons

| Reason | Meaning |
|---|---|
| `MALFORMED_JSON` | JSON syntax invalid |
| `INVALID_ENVELOPE` | kind/version/canvas/nodes/edges shape invalid |
| `INVALID_NUMBER` | position/size/viewport contains NaN, Infinity or invalid range |
| `DUPLICATE_NODE_ID` | document-local node identity collision |
| `DUPLICATE_EDGE_ID` | document-local edge identity collision |
| `DANGLING_EDGE` | source or target missing |
| `MISSING_PARENT` | parentId unresolved |
| `PARENT_CYCLE` | parent/child ownership cycle |
| `UNSUPPORTED_NODE_TYPE` | node type has no registered reader/migrator |
| `INVALID_NODE_DATA` | known node data fails its versioned validator |
| `CONNECTION_POLICY_UNRESOLVED` | import edge is unknown under graph connection contract |
| `NON_PORTABLE_MEDIA_REFERENCE` | required media only exists as runtime object/blob URL |
| `EMBEDDED_MEDIA_TOO_LARGE` | data URL exceeds declared fixture/product budget |
| `DOCUMENT_LIMIT_EXCEEDED` | clone-defined count/byte/depth limit exceeded |

Open Canvas 的 `200 nodes / 400 edges` 不能直接填入 `DOCUMENT_LIMIT_EXCEEDED`。LibTV 的 limit 必须在实际 demo/process fixture 上测量后另做 clone-only 决定。

### 7.3 Migration rules

- 只允许显式 `Vn -> Vn+1` pure migration chain；
- migration 不读取 DOM、当前 store、网络、日期或随机数；
- 保持 node/edge identity 和数组顺序，除非该 migration 明确登记 ID map；
- 每次 migration 返回 warnings/provenance，不能静默删除用户字段；
- 高于当前支持版本返回 `UNSUPPORTED_FUTURE_VERSION`；不尝试 downgrade；
- 缺失 version 的 legacy payload 不自动猜 V1。若未来需要 legacy importer，单独登记其 source format 和数据损失；
- migration 后仍需运行完整 structural/domain validation。

## 8. Whole-Document Transaction

### 8.1 First authorized product slice

如果未来实现 import，第一 slice 只允许“从已验证 document 创建新 canvas”：

1. parse/migrate/validate 完整 document；
2. 为 canvas 生成新 ID，保留 document 内 node/edge IDs；若与目标域有跨 canvas 全局约束，再显式 remap；
3. 一次创建新 canvas 并切换 active；
4. selection 为空；
5. 新 canvas history past/future 为空；
6. viewport 使用 document viewport；
7. 任一步失败，canvas list 和 active canvas 均不变。

不以 active-canvas replacement 作为第一 slice。Replacement 同时跨 graph、viewport、selection、canvas metadata 和 history，需要独立 destructive confirmation 与 rollback 合同。

### 8.2 No partial repair

不得采用以下“成功”策略：

- 丢弃未知 node 后保留剩余 edge；
- 删除 dangling edge 后静默载入；
- 把 NaN position 改成 `0,0` 而不报告；
- 把 future schema 当 V1；
- 将 unsupported node 改成 generic image/text；
- 先创建 canvas，再逐 node 导入并在中途失败；
- 把 load failure 转为空画布并覆盖原内容。

可恢复修复只能由显式 migration 完成，并在 result 中记录 warning。

## 9. Fixture Contract

### 9.1 Fixture identity

`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` 是未来 deterministic document/snapshot fixture。当前状态：`DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`。

它包含纯 payload corpus 和 fresh Page browser case；不能依赖共享源站或 Director store。

### 9.2 Pure corpus

| Case | Input | Expected |
|---|---|---|
| empty V1 | 0 node/edge + viewport | exact ready round-trip |
| demo V1 | current demo semantic projection | order/IDs/layout/data retained |
| group V1 | parent + children + internal/external edges | parent resolves; relative positions retained |
| nested metadata | marks/regions/process arrays | deep snapshot isolation across push/undo/redo |
| runtime stripping | selected/dragging/measured/style/ref-like keys | rejected or excluded by declared writer; never round-tripped as semantic data |
| future version | `schemaVersion: 999` | unsupported; zero mutation |
| duplicate/dangling | colliding IDs or missing endpoint | stable rejection reason |
| invalid parent | missing parent or parent cycle | stable rejection reason |
| blob media | required `blob:` URL | non-portable diagnostics; no fake success |
| oversized embedded media | bounded generated data URL | explicit size rejection |
| edge policy unknown | Reference/unmodeled import edge | `CONNECTION_POLICY_UNRESOLVED` |

### 9.3 Browser setup/reset

1. create fresh Page and select `LIBTV-FIX-LOCAL-EMPTY-01`;
2. assert empty graph, empty selection and declared viewport/history;
3. create or load only the scenario payload through the future authorized boundary;
4. assert graph/document result, history isolation and errors;
5. discard Page after the scenario.

Undo、reload、切换 canvas 或清 browser storage 不能代替 fresh Page teardown。普通 graph document fixture 不接触 Director local storage。

## 10. Verifier Contract

Future `LIBTV-VR-010`:

### 10.1 Pure layer

- V1 exact round-trip with preserved ordering;
- runtime-field exclusion and JSON-safe field validation;
- duplicate/dangling/parent-cycle/media/limit reason stability;
- future version unsupported without fallback;
- migration determinism and warning provenance；当前 V1 没有虚构 migration；
- document validation delegates edge policy to `LibTVGraphConnection.contract.md`；
- nested snapshot mutation does not alter any earlier past/future snapshot；
- history excludes viewport/selection/canvas metadata。

### 10.2 Focused browser layer

Before import UI exists, browser scope is history isolation only：

- mutate nested metadata through an authorized real UI transaction；
- undo/redo restores graph content but not stale selection；
- viewport remains in its own domain；
- new command after undo clears future；
- one user command adds declared step count；
- no console/page errors。

Future import-as-new-canvas UI receives a separate browser scenario under the same `VR-010` ID only after its surface contract and coding authorization exist。

## 11. Authorized Implementation Slices

### Slice A: Pure Codec And Validation

- document types/codec/result reasons；
- runtime writer whitelist；
- strict reader with V1 only；
- pure fixture corpus and `VR-010` pure layer。

### Slice B: History Isolation

- replace shallow nested snapshot behavior with declared deep isolation；
- keep viewport/selection/canvas lifecycle outside history；
- focused nested metadata undo/redo verifier；
- measure 50-step memory before optimization。

### Slice C: Import As New Canvas

- explicit local import surface contract；
- whole-document zero-partial transaction；
- new canvas identity/history/selection/viewport policy；
- no active-canvas replacement。

### Slice D: Export And Clipboard Codec Reuse

- portable export provenance and media diagnostics；
- reuse narrow node/edge codec in a separately versioned subgraph packet；
- do not collapse whole-document and clipboard identity policy。

### Slice E: Persistence Envelope

`DEFERRED_PRODUCT_SCOPE`。只有用户明确要求 reload recovery、local save 或 collaboration，才另立 revision/dirty/save/conflict/security/retention 合同。不能因为 Open Canvas 已有 file/KV/revision 就让本 slice 自动进入实现。

No slice is authorized by this document. Slice A/B 也不能顺手修改 FrameOS、Director persistence、edge visual 或 provider runtime。

## 12. Non-Goals And Stop Conditions

- 不声称 LibTV 源站有 JSON import/export、autosave、revision、conflict merge 或 template reset；
- 不移植 Open Canvas node types、limits、provider fields、file/KV store 或 rebase implementation；
- 不把 `src/types/canvas.ts` 当前 union 宣布为完整 runtime registry；
- 不把 selection、viewport、overlay、task/save state 偷塞进 graph undo；
- 不允许 silent repair、partial import、future-version downgrade 或 unsupported node coercion；
- 不接真实 upload、asset store、remote save、billing、collaboration 或 account identity；
- 不修改 shared source project 或 Open Canvas submodule；
- 若一个实现无法在 mutation 前完成 parse/migrate/validate，或无法证明 nested history isolation，停止并回到合同评审。
