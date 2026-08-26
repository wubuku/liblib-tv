# LibTV Node Data Static Audit

> Status: `STATIC_AUDIT_COMPLETE / RUNTIME_SCHEMA_MISSING`
>
> Audit date: 2026-08-27
>
> Clone baseline: `fd52b9f`
>
> Open Canvas baseline: `research/upstream/open-canvas@cf3a906bb8c35bb940d3267497e7f394b8f42582`
>
> Scope: 普通 LibTV route 的 runtime node registry、node data shape、identity/reference fields、media locator、aggregate relation，以及 copy/delete/history/document 边界。FrameOS 与 Director 内部对象图不进入本表；Director 导出到 LibTV node data 的字段进入本表。

## 1. Why This Audit Exists

[`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md) 和 [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md) 已经要求 exact node type registry、`dataVersion`、reference role 和 runtime-field whitelist，但此前没有一份文件枚举当前 clone 的实际字段。

如果继续把 `Node<Record<string, unknown>>` 当作 schema，会出现四类不可由 React Flow structural ID map 自动修复的问题：

1. node data 仍指向旧 node/edge；
2. 一个 process aggregate 被复制或删除成半个 cohort；
3. `blob:`、`data:` 和跨 store provenance 被误写成 portable content；
4. history、duplicate、clipboard 和 import 对同一字段使用互相矛盾的 preserve/reset 规则。

本文只记录静态事实和直接风险，不宣布源站 LibTV 的产品语义，也不代表已授权修改代码。

## 2. Evidence Method

本轮只读以下边界：

- runtime registry：`src/app/page.tsx` 的 `nodeTypes`；
- public creation：`src/components/AddNodePanel.tsx`；
- graph/data mutation：`src/store/canvasStore.ts`；
- component-local data interfaces：`src/components/nodes/*.tsx`；
- legacy/shared types：`src/types/canvas.ts`；
- session UI references：`src/store/uiStore.ts`；
- Director export boundary：`src/store/directorStore.ts`、`src/components/director/DirectorDesk.tsx`、`directorVideoExport.ts`；
- Open Canvas typed data、normalization、serialization 和 runtime reset：fixed submodule 的 `shared/lib/canvas/types.ts`、`serialization.ts`。

审计时共享工作区另有未提交的 Batch 57 connection validation WIP，涉及 `page.tsx` connection handlers、`canvasStore.addEdge` 和新 helper。该 WIP 没有改变本表枚举的 node registry、node data writer、copy/delete/history 或 aggregate fields，因此不作为本文 baseline，也未被暂存或修改。

证据词汇：

| Label | Meaning |
|---|---|
| `STATIC_FACT` | 当前固定 clone/upstream 文件直接可读 |
| `STATIC_RISK` | 可从现有 mutation 与 field relation 直接推出的不一致风险 |
| `DESIGN_INPUT` | 值得进入后续合同，但不是当前 runtime 行为 |
| `SOURCE_UNKNOWN` | 仍需 LibTV disposable source fixture 或业务决定 |

## 3. Open Canvas Inspiration Boundary

### 3.1 What the fixed upstream proves

Open Canvas 在固定版本中提供了一条完整、但比 LibTV 简单的 data path：

```text
CanvasNodeType union
  -> discriminated CanvasNodeData union
  -> createDefaultCanvasNodeData(nodeType)
  -> normalizeCanvasNodeData(nodeType, unknown)
  -> buildCanvasGraphFromFlow()
  -> normalizeCanvasGraph()
  -> resetCanvasNodeRuntimeState()
```

`STATIC_FACT`：

- node type 是 `text | note | image | video | audio` 的封闭 union；
- node data 同时携带 `nodeType` discriminator，并按类型 normalize；
- unknown data 不通过 object spread 原样进入 normalized graph；
- media 使用 `{ url, source, assetId?, mimeType?, thumbnailUrl?, durationSec?, size? }`；
- `status/errorMessage/lastRunId/lastCompletedAt/lastScene/costCredits` 有显式 runtime reset；
- serialized graph 是 version 1，node/edge 只输出白名单 structural fields 和 normalized data。

### 3.2 What it does not prove for LibTV

Open Canvas 当前五类节点没有 LibTV 的 parent/group、derived provenance、shot/result 双向引用、long-video process cohort、Director cross-store export 或多套 operation metadata。因此可借鉴的是“封闭 registry + normalize + operation-specific reset”的方法，不能直接移植其 field union 或 reset policy。

## 4. Runtime Node Type Inventory

当前普通 LibTV `nodeTypes` 注册 11 类；Add Node 面板公开 8 类；另外 3 类只由结构或业务动作创建。

| Runtime type | Render owner | Creation class | Default data owner | Current schema status |
|---|---|---|---|---|
| `script` | `ScriptNode` | public add | `getDefaultNodeData` | component-local partial interface |
| `image` | `ImageNode` | public + derived | `getDefaultNodeData` + creators | broad interface；nested metadata partly external |
| `text` | `TextNode` | public add | `getDefaultNodeData` | minimal component-local interface |
| `video` | `VideoNode` | public + many derived operations | `getDefaultNodeData` + creators | broad interface but several writer fields undeclared |
| `script-execution` | `ScriptExecutionNode` | public add | no dedicated default case | interface omits runtime-read counts |
| `storyboard-group` | `StoryboardGroupNode` | initial data + group command | group command / initial data | interface omits `groupKind` |
| `shot-breakdown` | `ShotBreakdownNode` | public + derived from video | default + creator | interface carries result refs |
| `shot-breakdown-result` | `ShotBreakdownResultNode` | generated only | `completeShotBreakdown` | explicit interface with source back-reference |
| `video-clip` | `VideoClipNode` | public add | `getDefaultNodeData` | minimal interface；editor mode is component-local |
| `audio` | `AudioNode` | public + derived split output | default + creator | interface carries split provenance |
| `long-video-process` | `LongVideoProcessNode` | generated 12-node cohort only | `createLongVideoProcess` | explicit nested metadata；no aggregate validator |

### 4.1 Three competing type surfaces

`STATIC_FACT`：当前存在三套不一致的“node type”表述：

1. `page.tsx.nodeTypes` 是实际 renderer allowlist，共 11 类；
2. `AddNodePanel` 是 public creation allowlist，共 8 类；
3. `src/types/canvas.ts.CanvasNodeType` 只有 `script/image/storyboard/scriptExecution/text`，其中 `storyboard` 和 `scriptExecution` 还与 runtime hyphenated key 不同。

此外，`getDefaultNodeData()` 有 `style`、`effect` 分支，但普通 LibTV route 没有对应 renderer 或 Add Node entry。`addNode(type: string, data?: Record<string, unknown>)` 本身也不限制 type。

因此 `src/types/canvas.ts`、default-data switch 和 public Add Node 列表都不能单独作为 import/copy allowlist。当前唯一 runtime renderer 事实是 `page.tsx.nodeTypes`，但它也不是 data schema。

## 5. Schema Ownership Audit

### 5.1 Current shape

`STATIC_FACT`：

- store graph 使用无泛型收窄的 `Node[]` / `Edge[]`；
- `CanvasData.nodes`、`GraphSnapshot.nodes` 和所有 graph actions 都接受 generic React Flow `Node`；
- `updateNodeData(nodeId, data: Record<string, unknown>)` 允许任意浅层 patch；
- 多数 component interface 继承 `Record<string, unknown>`，所以未声明 writer field 仍可静默存在；
- `cloneGraphSnapshot()`、selection duplicate 和 canvas duplicate 只对 `node.data` 做一层 object spread；
- 当前没有 `dataVersion`、per-type parser、unknown-field policy 或 reference integrity pass。

### 5.2 Declared/read/written drift

| Type | Drift |
|---|---|
| `script-execution` | component 读取 `objectCount/cameraCount`，interface 未声明；default writer 返回 `{}`，UI 使用 fallback |
| `storyboard-group` | group command 写 `groupKind: selection`，interface 未声明 |
| `video` | creators 写 `generationMode/generationCount/generatorType/isSmartMattingOutput/isPictureEditOutput/sourceWidth/sourceHeight`，`VideoNodeData` 未声明全部字段 |
| `shot-breakdown` | local upload preview 使用 component state 的 object URL；graph data 不持有该 preview URL，重新 mount 后不是同一 data contract |
| all types | no runtime discriminator in `data`；renderer key 与 data shape 只能靠调用者保持一致 |

## 6. Field Inventory By Node Family

### 6.1 Content and structural shell nodes

| Type | Stable-looking semantic fields | Identity/reference fields | Runtime/session notes |
|---|---|---|---|
| `script` | `title`, `content` | none | duplicate appends `副本` only to title |
| `text` | `content` | none | edit draft is component-local until commit |
| `video-clip` | `title`, `status` | none | selected mode is component `useState`; duplicate/history do not preserve it |
| `storyboard-group` | `title`, `variant`, `groupKind` | structural children use `node.parentId`; not stored in data | size/z-index live in node structural fields |
| `script-execution` | `title`, `steps`, `objectCount`, `cameraCount` | node ID is passed into Director as `sourceNodeId` | Director scene is a separate global store, not graph-owned per-node data |

### 6.2 Image node

Base content fields:

```text
filename, width, height, imageUrl, watermarkUrl,
placeholderKind, editorVariant, editorHeight, prompt,
references[], generationSettings, portraitEnhanced
```

Nested identity-bearing variants:

| Path | Current meaning | Relation class |
|---|---|---|
| `rotateMirror.sourceNodeId` | source image node | node provenance reference |
| `rotateMirror.sourceFilename` | copied source label | display projection |
| `frameCapture.sourceNodeId` | source video node | node provenance reference |
| `frameCapture.edgeId` | source-to-result edge | edge-owned reference |
| `directorCapture.sourceNodeId` | Director root graph node | cross-node provenance |
| `directorCapture.edgeId` | root-to-capture edge | edge-owned reference |
| `directorCapture.captureId` | Director capture identity | external/session provenance ID |
| `directorCapture.cameraId` | Director camera identity | external store reference or null |
| `directorCapture.createdAt` | captured event timestamp | immutable provenance scalar |

`imageUrl`、`watermarkUrl`、`references[]` 同时可能是 repo path、remote URL、`data:` 或 future asset locator；当前 shape 只用 string，无法表达 portability class。

### 6.3 Video and audio nodes

Video base fields include filename/model/status/duration/resolution/poster/video/prompt plus generation and operation projections. Audio base fields include filename/duration and optional split metadata。

| Nested path | Node types | Node ref | Edge ref | Local/external IDs | Notes |
|---|---|---|---|---|---|
| `continuation` | video | `sourceNodeId` | `edgeId` | none | `clearVideoContinuation()` dereferences stored edgeId |
| `subtitleErase` | video | `sourceNodeId` | `edgeId` | `regions[].id` | region IDs are scoped to one editor payload |
| `audioSplit` | video/audio | `sourceNodeId` | `edgeId` | none | one action creates audio + silent-video outputs |
| `depthMotionCapture` | video | `sourceNodeId` | `edgeId` | none | carries model/request projection |
| `pictureEdit` | video | `sourceNodeId` | `edgeId` | `marks[].id` | mark IDs are scoped to one editor payload |
| `smartMatting` | video | `sourceNodeId` | `edgeId` | none | provider/task type are descriptor projections, not task identity |
| `directorAnimationExport` | video | `sourceNodeId` | `edgeId` | `exportId`, `cameraId` | `videoUrl` is currently a browser object URL |
| `frameCapture` | image | `sourceNodeId` | `edgeId` | none | result media aliases source poster URL |
| `directorCapture` | image | `sourceNodeId` | `edgeId` | `captureId`, `cameraId` | image content is a `data:` URL |

`STATIC_FACT`：`SubtitleEraseRegion.id` 和 `PictureEditMark.id` 由 component-local counters 生成，主要用于 local selection、React key 和 data attributes；它们不是 graph node ID。不同 node payload 之间已经可能出现相同字符串，因此只能按 node-scoped local ID 理解。

### 6.4 Shot breakdown aggregate

```text
shot-breakdown.data.resultNodeIds[]
  <-> shot-breakdown-result.data.sourceBreakdownId
```

`STATIC_FACT`：这些 result nodes 与 source 通过 edge 相连，但不是 `parentId` descendants。Result data 还包含：

- `resultKey`：固定结果定义 key；
- `items[].id`：`S01/M01/BGM` 等 catalog/display key；
- `items[].imageUrl`：媒体 locator；
- `category/title/summary/kind/resolution`：semantic/display data。

`STATIC_RISK`：

- duplicate source alone shallow-copies `resultNodeIds`，会指向原 results；
- duplicate result alone shallow-copies `sourceBreakdownId`，会指向原 source；
- delete source does not cascade to result nodes because they are not descendants；
- delete one result does not remove its ID from source `resultNodeIds`；
- source status may remain `complete` after result loss，阻止现有 start path 再执行。

### 6.5 Long-video process aggregate

一次 `createLongVideoProcess()` 创建 12 nodes / 22 edges。每个 process node 都保存同一个：

```text
longVideoProcess.processId
longVideoProcess.sourceNodeId
```

并保存 stage/stageIndex/batchIndex、prompt/model/ratio/resolution/duration/audio/credits/referenceCount/status。

`STATIC_FACT`：`processId` 不是任一单独 node ID，但当前 node ID 以它为字符串前缀；runtime 没有 cohort validator，也没有按 `processId` 的 copy/delete closure。

`STATIC_RISK`：

- copy 一个 process node 会保留原 `processId`，形成新旧 cohort identity collision；
- copy 全部 process nodes 也不会生成新的 shared `processId`；
- delete 任一 process node 会留下 partial cohort；
- `status: pending` 是每个 node 的固定展示状态，不是独立 run identity；
- `sourceNodeId` 和 source edge 可在 copy/delete 后分别悬空。

### 6.6 Director root and exported results

`script-execution` node ID 被传入 `uiStore.activeDirectorNodeId` 和 `directorStore.sourceNodeId`，但 Director scene/objects/groups/timeline 是一个独立全局 store，不按 LibTV graph node ID 建立 document map。

`STATIC_RISK`：复制一个 `script-execution` node 只复制画布 shell data，不复制独立 Director workspace。新副本进入 Director 后仍使用同一份当前 store state；这不能被描述为“导演台项目复制”。

Director export result data 是已经渲染的 provenance snapshot：

- image capture：`data:` URL + capture/camera IDs；
- animation export：`blob:` URL + export/camera IDs；
- source graph node + edge IDs；
- createdAt、dimensions、mime/size/duration 等 projection。

## 7. Structural And Metadata Relation Topology

| Relation | Structural carrier | Data carrier | Current closure |
|---|---|---|---|
| group ownership | `parentId` / `extent` | none | duplicate/delete recurse descendants |
| ordinary graph dependency | edge source/target/handles | sometimes sourceNodeId/edgeId | edge and metadata are not jointly validated |
| generic derived image/shot node | edge | sometimes only media/label snapshot | `addDerivedNode` does not require source metadata |
| shot breakdown results | edges | resultNodeIds + sourceBreakdownId | no copy/delete repair |
| long-video process | 22 edges | processId + sourceNodeId | no aggregate closure |
| Director workspace | graph node ID passed at open time | separate store sourceNodeId | no per-node workspace ownership |
| overlay/editor session | none | `uiStore.*.nodeId` outside graph data | selection/close lifecycle only |

The same string suffix `Id` therefore has at least six meanings. A suffix heuristic cannot safely decide map/preserve/reset behavior.

## 8. Media And Portability Audit

| Locator form | Current examples | Same-page duplicate | History | Portable document risk |
|---|---|---|---|---|
| repo path | `/images/scene-coffee-1.png` | aliases same path | shallow string | only valid with same deployment assets |
| remote URL | future/current arbitrary string fields | aliases URL | shallow string | auth/CORS/expiry unknown |
| `data:` URL | Director capture | duplicates full string | repeated in every snapshot | unbounded payload and memory amplification |
| `blob:` URL | Director animation export | aliases current BrowserContext object URL | snapshot stores non-restorable locator | invalid after revoke/reload/new context |
| stable asset ID | absent in LibTV clone graph | n/a | n/a | preferred future identity but backend not implemented |

ShotBreakdown local upload uses a component-local object URL for preview and does not commit that URL into graph data. It is session UI state, not portable media。

## 9. Current Operation Behavior

| Operation | Structural IDs | Nested node data | Cross-node/aggregate refs | UI/session state |
|---|---|---|---|---|
| graph history snapshot | preserves | one-level clone only | preserves strings/arrays/objects by nested reference | excludes uiStore, but nested aliasing remains |
| `duplicateNode` | new node；optional incident edges | one-level clone | no source/edge/process/result rewrite | selection moves to copy |
| `duplicateSelectedNodes` | new closure node/edge IDs + parent remap | one-level clone | no metadata/aggregate rewrite | copied roots selected |
| `duplicateCanvas` | maps node/parent/edge IDs | one-level clone | no metadata/process/result rewrite | new history empty, selection empty |
| remove node/selection | parent descendants + incident edges | other node data untouched | leaves metadata/aggregate dangling risk | removed selection cleared |
| import/export | not implemented | no codec | no integrity pass | n/a |
| UI overlay open/close | none | graph data unchanged | uiStore nodeId may become invalid until lifecycle closes it | explicitly session-owned |

## 10. Ranked Findings

### P0: no authoritative runtime data registry

Renderer allowlist, public creation list, legacy types, component interfaces and default-data switch disagree. Import/copy cannot validate safely until `(node.type, dataVersion)` has one authority。

### P0: reciprocal and aggregate references bypass structural closure

Shot/result and long-video process relations can become invalid through ordinary duplicate/delete actions even when all React Flow node/edge IDs remain unique。

### P0: nested edge IDs can drive later destructive behavior

At least continuation cleanup deletes an edge by `data.continuation.edgeId`. A shallow-copied stale edge ID is not inert display metadata。

### P1: media string shape hides lifecycle and portability

Repo paths、remote URLs、`data:` and `blob:` have different copy/history/import properties but share plain string fields。

### P1: Director node duplication has a false ownership implication

The graph shell and Director workspace do not share a document identity. Future UI/UX copy work must not promise full Director-project duplication without a separate Director document contract。

### P1: status has node-specific meaning

`video.status`、`shot-breakdown.status`、`video-clip.status` and `longVideoProcess.status` use different unions and lifecycles. A global `status` reset rule would corrupt content or invent run semantics。

### P2: node-scoped IDs and catalog keys must not be remapped as graph IDs

Region/mark IDs、resultKey and item IDs look like identities but are scoped semantic/local keys. Name-based `*Id` rewriting would be wrong。

## 11. Handoff To The Normative Contract

[`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) now defines the following design inputs without changing runtime code：

1. canonical runtime type registry and `dataVersion: 0` migration baseline；
2. field roles that extend the copy contract without creating a second vocabulary；
3. per-operation policy for history、duplicate-selection、node-only copy、duplicate-canvas、clipboard and portable import；
4. full-cohort rules for shot breakdown and long-video process；
5. media locator classes and diagnostics；
6. unknown type/version/reference behavior；
7. `LIBTV-FIX-LOCAL-NODE-DATA-01` and `LIBTV-VR-012` acceptance design；
8. deletion/reference integrity decisions that remain source/product blocked。

No `src/`、test、fixture runtime、shared LibTV source state、FrameOS or upstream submodule content was modified during this audit。
