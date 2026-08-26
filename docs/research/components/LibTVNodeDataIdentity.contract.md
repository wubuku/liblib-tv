# LibTV Node Data Identity And Reference Contract

> Status: `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / SOURCE_PRODUCT_DECISIONS_PARTIAL`
>
> Scope: 普通 LibTV route 的 runtime node type registry、per-type data version、field role、cross-node/aggregate integrity、media portability，以及 history/copy/document/delete operation policy。
>
> Static evidence: [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)
>
> Related authorities: [`LibTVGraphDocument.contract.md`](LibTVGraphDocument.contract.md)、[`LibTVSubgraphCopy.contract.md`](LibTVSubgraphCopy.contract.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md)

## 1. Contract Objective

Current LibTV graph code can map React Flow node/edge IDs, but node data also contains source/edge/process/result/capture/media identities. This contract makes those fields explicit before any broad copy, import/export or deletion hardening is implemented。

It answers four questions for every registered node type：

1. Which fields are accepted at a given `dataVersion`?
2. Which fields are content, graph references, aggregate identities, external provenance, media locators or session state?
3. For a named operation, is each field preserved, mapped, reset, recomputed, diagnosed or rejected?
4. Which cross-node invariants must be valid before one atomic mutation can commit?

This is a clone correctness contract. It does not claim the source LibTV uses the same TypeScript types or payload。

## 2. Evidence And Inspiration Boundary

### 2.1 Open Canvas method

At fixed commit `cf3a906bb8c35bb940d3267497e7f394b8f42582`, Open Canvas proves a useful method：

- closed `CanvasNodeType` union；
- discriminated `CanvasNodeData` union；
- per-type defaults and `normalizeCanvasNodeData()`；
- versioned serialized graph；
- normalized media object；
- explicit runtime status reset；
- serializer outputs a whitelist rather than arbitrary component state。

### 2.2 LibTV adaptation

LibTV currently has 11 runtime node types, parent/group ownership, derived operation metadata, reciprocal shot/result refs, process aggregates and Director cross-store provenance. Therefore Open Canvas's five data shapes and reset rules are not transplanted. Only its boundary discipline is adopted。

### 2.3 Source unknowns

The source LibTV has not been destructively tested for：

- copying complete/partial shot breakdown results；
- copying a long-video process cohort；
- duplicating a Director node and its workspace；
- deleting a source while derived results remain；
- external provenance behavior across canvases；
- clipboard handling of non-portable media。

These remain `SOURCE_PRODUCT_DECISION_REQUIRED`. The contract may still reject unsafe clone operations until evidence exists。

## 3. Canonical Registry Model

### 3.1 Registry key

Every codec/operation rule is selected by the pair：

```text
(node.type, dataVersion)
```

Current runtime data has no stored `dataVersion`. It is treated as migration baseline `0`, not silently promoted to a future version。

```ts
type LibTVRuntimeNodeType =
  | "script"
  | "image"
  | "text"
  | "video"
  | "script-execution"
  | "storyboard-group"
  | "shot-breakdown"
  | "shot-breakdown-result"
  | "video-clip"
  | "audio"
  | "long-video-process";

type LibTVNodeDataVersion = 0;
```

This is a design shape, not current code. The future runtime registry must become the one source from which renderer compatibility, data validation, document codec and copy policy are derived. `src/types/canvas.ts` is not the authority。

### 3.2 Registry entry requirements

Each entry must declare：

```text
runtimeType
dataVersion
creationClass
acceptedFields
normalize/validate
fieldRoles
statusPolicy
mediaPolicy
copyProfiles
integrityRules
connectionCapabilityRef
```

An arbitrary `Record<string, unknown>` may exist at React component boundaries during migration, but it must not cross copy/document/history codecs without a registry result。

### 3.3 Runtime type registry

| Type | Creation class | V0 content class | Special integrity | Design copy support |
|---|---|---|---|---|
| `script` | public | text content | none | baseline |
| `text` | public | text content | none | baseline |
| `image` | public + derived | media/authoring + provenance variants | optional source/edge metadata | conditional |
| `video` | public + derived | media/authoring + operation variants | optional source/edge metadata | conditional |
| `audio` | public + derived | media + split provenance | optional source/edge metadata | conditional |
| `video-clip` | public | editor shell | component-local editor state excluded | baseline shell |
| `storyboard-group` | structural | ownership shell | parent/descendant closure | group closure |
| `script-execution` | public | Director shell projection | external Director workspace | shell-only, workspace blocked |
| `shot-breakdown` | public + derived | authoring/source snapshot | resultNodeIds aggregate | aggregate-aware |
| `shot-breakdown-result` | generated | result catalog snapshot | sourceBreakdownId back-ref | aggregate-aware |
| `long-video-process` | generated | process stage projection | shared processId cohort | complete cohort only |

Unknown type、unregistered current writer field or unsupported future dataVersion returns `unknown/reject`; it is never normalized to `{}` and rendered as a valid blank node。

## 4. Canonical Field Roles

This table extends the role vocabulary introduced by [`LibTVSubgraphCopy.contract.md`](LibTVSubgraphCopy.contract.md#7-node-data-reference-roles). It is the detailed authority for node data fields；the copy contract remains authority for command closure and transaction behavior。

| Role | Meaning | Default transform |
|---|---|---|
| `SEMANTIC_VALUE` | user content, dimensions, enum, prompt, time/range/parameter | deep preserve after validation |
| `DISPLAY_PROJECTION` | title suffix, source label/name, ordinal, derived summary | recompute when stable source maps；otherwise preserve only as declared snapshot |
| `OWNED_NODE_REF` | points to a node required by the same logical copied document/aggregate | map through nodeMap；missing target rejects |
| `EXTERNAL_PROVENANCE_NODE_REF` | intentionally remembers a graph node outside copied ownership | same-canvas preserve only with explicit provenance mode；cross-document resolve/diagnose |
| `OWNED_EDGE_REF` | points to an edge whose identity drives node behavior | map through edgeMap；missing edge rejects unless a declared detach recipe removes the dependent feature |
| `AGGREGATE_ID` | groups multiple nodes into one logical process/cohort | allocate once per copied aggregate and map all members；partial cohort rejects |
| `SCOPED_LOCAL_ID` | identity unique only inside one node payload/editor | deep preserve；do not pass through graph nodeMap |
| `CATALOG_KEY` | stable definition/model/result key | preserve after allowlist validation |
| `GLOBAL_ASSET_REF` | stable future asset/media version identity | preserve reference；do not duplicate asset implicitly |
| `MEDIA_LOCATOR` | repo/remote/data/blob location used to render bytes | preserve/diagnose by locator class and operation |
| `EXTERNAL_PROVENANCE_ID` | capture/export/camera identity from another store/session | preserve as provenance；do not treat as graph-owned or automatically dereference |
| `RUN_OR_TASK_ID` | provider run/task/request/attempt identity | reset/new/unresolved by type；never reuse as a live run identity |
| `SESSION_OR_UI_ID` | selection, active panel/tool, DOM/ref/blob object owner, temporary editor state | exclude/reset |

Field names do not determine roles. `resultKey` is a catalog key, `processId` is an aggregate ID, `captureId` is external provenance, and `regions[].id` is node-scoped local identity。

## 5. Named Operation Profiles

Field transforms depend on the operation. One generic `cloneNodeData()` is not sufficient。

| Profile | Identity intent | Graph ID behavior | Runtime/session behavior |
|---|---|---|---|
| `HISTORY_SNAPSHOT` | restore the exact prior logical graph state | preserve all graph/aggregate IDs | deep isolate declared graph data；exclude page/UI state |
| `DUPLICATE_SELECTION` | create a new logical subgraph in same canvas | allocate/map node/edge/aggregate IDs | preserve content；apply per-type status/provenance policy |
| `CREATE_NODE_COPY` | create a standalone authoring/media copy | allocate node ID；edge policy none | apply explicit detach/reset recipe；unsupported derived types reject |
| `DUPLICATE_CANVAS` | create a new full canvas document | map all graph and aggregate IDs | clear selection/history/UI；preserve validated content |
| `CLIPBOARD_PASTE` | create a new subgraph from a versioned packet | allocate/map packet-local IDs | external graph refs/media require portability resolution |
| `PORTABLE_IMPORT` | load a complete validated document as a new canvas | preserve document-local graph IDs unless collision policy says map | reset session/run fields；diagnose media |
| `DELETE_REPAIR` | remove graph entities without corrupting survivors | remove requested structural closure | repair/reset/reject affected metadata/aggregate refs atomically |

### 5.1 Transform verbs

Every accepted field receives one explicit verb：

```text
PRESERVE_DEEP
MAP_NODE
MAP_EDGE
MAP_AGGREGATE
PRESERVE_PROVENANCE
PRESERVE_SCOPED
RECOMPUTE
RESET
EXCLUDE
DIAGNOSE
REJECT
```

No field falls back to shallow object spread。

## 6. Structural Field Policy

| Path | Role | History | Duplicate/paste | Portable import |
|---|---|---|---|---|
| `node.id` | graph identity | preserve | allocate/map | preserve within validated new canvas；map only on collision policy |
| `node.type` | registry discriminator | preserve | preserve registered type | strict allowlist |
| `node.parentId` | ownership node ref | preserve | map parent；child-only node copy detaches by copy contract | require existing parent and acyclic chain |
| `node.extent` | ownership/layout constraint | preserve | preserve only with mapped parent；otherwise clear | validate allowed value |
| position/width/height/zIndex | layout semantic | deep preserve | transform in flow coordinates | finite/range validation |
| `selected/dragging/measured` | session/runtime | exclude | exclude | exclude |
| `edge.id` | graph identity | preserve | allocate/map | preserve within document |
| edge source/target | owned node refs | preserve | map both accepted endpoints | both endpoints must exist |
| source/target handles | connection identity | preserve | preserve then validate | normalize/validate through connection contract |
| edge renderer/data | renderer/semantic | declared whitelist | preserve declared fields only | fixed renderer boundary；unknown data rejects |

## 7. Common Data Policy

### 7.1 Content and labels

`title/content/prompt/filename/model/ratio/resolution/duration/generationSettings` and declared booleans/enums are `SEMANTIC_VALUE` unless a per-type entry narrows them. Duplicate title suffix is a command-level `DISPLAY_PROJECTION`, not an identity mutation。

### 7.2 Status

There is no global LibTV `status` type. Every node type must define its own policy：

| Type | V0 status | History | Content-preserving copy | Standalone copy |
|---|---|---|---|---|
| image/script/text/group/script-execution | none | n/a | n/a | n/a |
| video | `empty/ready/failed/pending` | preserve | `empty/ready` may preserve if media valid；`failed/pending` require declared reset recipe | derived pending/failed copy rejects until recipe |
| audio | no explicit status | n/a | preserve media/provenance policy | provenance-bearing copy conditional |
| video-clip | `empty/ready` | preserve | preserve shell status | local editor mode resets |
| shot-breakdown | `empty/ready/running/complete/failed` | preserve | complete only with valid aggregate；running/failed require reset decision | reset to `ready` when source snapshot exists, otherwise `empty`; clear results |
| long-video-process | currently `pending` only | preserve | preserve only for complete mock cohort with new aggregate ID | single stage copy rejected |

Future provider `runId/taskId` is independent of visible node status and follows `RUN_OR_TASK_ID` reset policy。

### 7.3 Display projections

Fields such as `sourceLabel/sourceFilename/sourceName/title/subtitle` may be useful snapshots but cannot prove referential integrity. When source maps, recompute from mapped source where a deterministic projector exists. When source remains external, preserve only as provenance display and mark the stable source unresolved/resolved separately in a future schema。

## 8. Per-Type Field Registry

### 8.1 `script` and `text`

| Type | V0 accepted fields | Roles | Copy notes |
|---|---|---|---|
| script | `title`, `content` | semantic/display | deep copy；title suffix is command projection |
| text | `content` | semantic | deep copy；component draft is excluded session state |

### 8.2 `storyboard-group`

Accepted V0 data：`title`、`variant`、`groupKind`。

- ownership lives in child `parentId`, not data；
- group duplicate includes recursive descendants per subgraph copy contract；
- group data never substitutes for parent integrity；
- `variant/groupKind` are catalog/semantic enums, not source LibTV proof。

### 8.3 `video-clip`

Accepted V0 data：`title`、`status`。

The active edit mode is component-local and always `EXCLUDE/RESET`. Copying the shell does not promise copying an in-progress local edit session。

### 8.4 `script-execution`

Accepted V0 data：`title`、`steps[]`、`objectCount`、`cameraCount`。

The node is a shell/projection for the separate Director store：

- `HISTORY_SNAPSHOT` preserves shell data only；
- `DUPLICATE_SELECTION/CREATE_NODE_COPY/DUPLICATE_CANVAS/PORTABLE_IMPORT` may duplicate the shell, but return `DIRECTOR_WORKSPACE_NOT_INCLUDED` diagnostics；
- no operation may claim Director workspace duplication；
- if a caller explicitly requires workspace duplication, return `DIRECTOR_WORKSPACE_COPY_UNSUPPORTED` / zero mutation until Director has a keyed document codec；
- capture/export result nodes remain media/provenance snapshots, not proof of workspace ownership。

### 8.5 `image`

Base accepted V0 fields：

```text
filename, width, height, imageUrl, watermarkUrl,
placeholderKind, editorVariant, editorHeight, prompt,
references[], generationSettings, portraitEnhanced
```

Nested variant registry：

| Variant | Node ref | Edge ref | Other IDs | Required copy rule |
|---|---|---|---|---|
| `rotateMirror` | `sourceNodeId` | none | none | map source if copied；otherwise explicit external provenance；sourceFilename recompute/preserve snapshot |
| `frameCapture` | `sourceNodeId` | `edgeId` | none | node and edge must map together or declared detach rejects |
| `directorCapture` | `sourceNodeId` | `edgeId` | captureId/cameraId external | map graph refs；preserve external provenance IDs；diagnose data URL budget |

An image without nested provenance may be copied as standalone content. `references[]` are media locators, not node IDs。

### 8.6 `video` and `audio`

Base video V0 fields include declared component fields plus current writer fields：

```text
filename, model, status, durationSeconds, resolution,
posterUrl, videoUrl, prompt,
generationMode, generationCount, generatorType,
isSmartMattingOutput, isPictureEditOutput,
sourceWidth, sourceHeight
```

Audio V0 fields：`filename`、`duration`、optional `durationSeconds`、`audioSplit`。

Derived metadata registry：

| Path | sourceNodeId | edgeId | Local/external identity | Policy |
|---|---|---|---|---|
| continuation | conditional node ref | required owned edge | none | map both；without edge, reject because cleanup dereferences edgeId |
| subtitleErase | conditional node ref | required owned edge | regions[].id scoped local | map graph refs；preserve region IDs within payload |
| audioSplit | conditional node ref | required owned edge | outputKind semantic | map graph refs；each output remains independently valid only with its own edge |
| depthMotionCapture | conditional node ref | required owned edge | model/request catalog values | map graph refs；preserve descriptor projection |
| pictureEdit | conditional node ref | required owned edge | marks[].id scoped local | map graph refs；deep preserve marks/points/replacement snapshot |
| smartMatting | conditional node ref | required owned edge | provider/model catalog values | map graph refs；never infer task identity from provider fields |
| directorAnimationExport | conditional node ref | required owned edge | exportId/cameraId external | map graph refs；preserve provenance IDs；`blob:` media blocks portable copy/import |

“Conditional node ref” means：

1. if source is inside the copied document, it is `OWNED_NODE_REF` and must map；
2. if source stays in the same canvas, it may be `EXTERNAL_PROVENANCE_NODE_REF` only under an explicit command policy；
3. cross-canvas packet/import cannot preserve a raw graph ID as resolved truth；it must include source or return unresolved/reject；
4. V0 has no explicit provenance-resolution marker, so broad runtime consolidation stays blocked。

### 8.7 Shot breakdown source/result

#### Exact aggregate

For a content-preserving duplicate, aggregate membership is：

```text
one shot-breakdown source
all IDs in source.data.resultNodeIds
all shot-breakdown-result nodes whose sourceBreakdownId equals source.id
all connecting internal edges
```

Both directional sets must match. Missing/extra refs return `SHOT_BREAKDOWN_REFERENCE_MISMATCH` before mutation。

Transforms：

- source `resultNodeIds[]` -> `MAP_NODE` preserving array order；
- result `sourceBreakdownId` -> `MAP_NODE`；
- result `resultKey` and `items[].id` -> `CATALOG_KEY/PRESERVE_DEEP`；
- result media -> media policy；
- source/result connecting edges -> `MAP_EDGE` structurally。

#### Authoring reset

Only explicit `CREATE_NODE_COPY` may detach a shot source from results：

```text
resultNodeIds = []
status = source snapshot available ? "ready" : "empty"
```

Result-only copy has no accepted V0 detach recipe and returns `PARTIAL_SHOT_BREAKDOWN_AGGREGATE`。

#### Delete repair

Deleting source or result nodes must update both directions and status in the same history transaction. Exact source-site cascade behavior remains unknown；the clone may choose cascade or authoring reset only after product review, but it cannot leave stale refs。

Command inventory、relation inverse index、shot/process policy candidates、UI/resource impact、`LIBTV-FIX-LOCAL-GRAPH-DELETE-01` and `LIBTV-VR-013` are specified in [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)。This contract remains authority for field roles；the delete matrix is authority for command impact and repair planning。

### 8.8 Long-video process

The aggregate key is `longVideoProcess.processId`。

Current V0 complete cohort is the bounded clone prototype：3 material + 3 shot + 4 candidate + 1 assembly + 1 final nodes，with 22 declared process edges. This count is not a LibTV source contract or future backend limit。

For `DUPLICATE_SELECTION` or `DUPLICATE_CANVAS`：

1. collect all current nodes sharing the processId；
2. validate unique `(stage, stageIndex)` and declared batchIndex；
3. require the complete expected V0 cohort before content-preserving copy；
4. allocate one new processId；
5. map every member's aggregate ID to it；
6. allocate graph node/edge IDs independently；do not parse identity from old node ID strings；
7. map sourceNodeId when source is copied；otherwise apply explicit same-canvas external provenance policy；
8. keep `pending` only as bounded prototype state, never as a reused live task。

Single-stage or partial-cohort copy returns `PARTIAL_LONG_VIDEO_PROCESS_AGGREGATE`. `CREATE_NODE_COPY` has no V0 recipe。

Delete repair must either delete the complete cohort or define a source-evidenced partial-stage lifecycle. Current runtime has neither, so partial deletion remains blocked for future hardening。

## 9. Media Locator Policy

### 9.1 Locator classes

| Class | Recognition | Same-canvas duplicate | Clipboard/document |
|---|---|---|---|
| `REPO_ASSET_PATH` | normalized local `/...` path | preserve alias | preserve with deployment-dependency diagnostic |
| `REMOTE_URL` | `https:` | preserve alias | preserve with access/expiry diagnostic |
| `EMBEDDED_DATA_URL` | `data:` | preserve only under byte budget | packet/document byte budget required |
| `SESSION_BLOB_URL` | `blob:` | may alias inside current BrowserContext | reject as portable；must resolve/upload/embed first |
| `STABLE_ASSET_ID` | future typed asset reference | preserve identity | preferred；resolver still required |

### 9.2 Byte and alias rules

- media bytes are not duplicated merely because a graph node is duplicated；
- history deep isolation does not mean copying binary payload on every step；future implementation needs bounded immutable asset references；
- `data:` without byte count/budget returns `MEDIA_BUDGET_UNKNOWN` for portable operations；
- `blob:` returns `NON_PORTABLE_MEDIA_REFERENCE` outside the current BrowserContext；
- empty string never substitutes for unresolved media。

## 10. Validation Result And Reason Taxonomy

```ts
type LibTVNodeDataPlanResult =
  | {
      status: "ready";
      normalizedNodes: unknown[];
      diagnostics: NodeDataDiagnostic[];
    }
  | { status: "reject"; reason: NodeDataRejectionReason }
  | { status: "unknown"; reason: NodeDataUnknownReason };
```

Conceptual rejection reasons：

| Reason | Meaning |
|---|---|
| `UNKNOWN_NODE_TYPE` | no runtime/data registry entry |
| `UNSUPPORTED_DATA_VERSION` | no explicit migration path |
| `INVALID_NODE_DATA` | accepted field has invalid type/range/enum |
| `UNMODELED_FIELD` | field is not in the V0 allowlist |
| `UNMODELED_REFERENCE_FIELD` | identity-looking field has no role |
| `DANGLING_NODE_REFERENCE` | required node ref cannot resolve |
| `DANGLING_EDGE_REFERENCE` | required edge ref cannot resolve |
| `SHOT_BREAKDOWN_REFERENCE_MISMATCH` | source/results reciprocal sets disagree |
| `PARTIAL_SHOT_BREAKDOWN_AGGREGATE` | exact result aggregate is incomplete |
| `PARTIAL_LONG_VIDEO_PROCESS_AGGREGATE` | process cohort is incomplete |
| `AGGREGATE_ID_COLLISION` | one logical copied aggregate maps inconsistently |
| `DIRECTOR_WORKSPACE_COPY_UNSUPPORTED` | operation would falsely imply workspace copy |
| `NON_PORTABLE_MEDIA_REFERENCE` | media locator cannot survive operation |
| `MEDIA_BUDGET_EXCEEDED` | embedded payload exceeds declared limit |

Conceptual unknown reasons：

| Reason | Meaning |
|---|---|
| `EXTERNAL_PROVENANCE_POLICY_REQUIRED` | raw source ref would leave copied ownership |
| `ACTIVE_STATE_RESET_POLICY_REQUIRED` | node-specific pending/running/failed state has no reset rule |
| `DELETE_CASCADE_POLICY_REQUIRED` | source behavior must decide cascade vs detach/reset |
| `MEDIA_BUDGET_UNKNOWN` | embedded byte accounting unavailable |
| `SOURCE_COPY_SEMANTICS_UNCONFIRMED` | exact source behavior is required for fidelity decision |

Both reject and unknown are zero-mutation results. Diagnostics may accompany `ready` only when they do not invalidate structural/behavioral integrity。

Current non-fatal diagnostic examples include `DIRECTOR_WORKSPACE_NOT_INCLUDED`、`DEPLOYMENT_ASSET_DEPENDENCY`、`REMOTE_MEDIA_ACCESS_UNVERIFIED` and explicit external-provenance resolution status。

## 11. Atomic Integrity Pass

Before any accepted graph mutation：

```text
resolve registry entries
  -> normalize declared fields
  -> classify field roles
  -> collect structural closure
  -> collect aggregate closure
  -> allocate node/edge/aggregate maps
  -> transform refs/media/status
  -> validate reciprocal refs and connections
  -> compute diagnostics
  -> one graph/history commit
```

No operation may add nodes first and repair their data refs afterward. Undo restores the exact pre-operation graph in one step；redo restores the same planned identities from snapshot, not a fresh allocation。

## 12. Fixture Contract

### 12.1 Fixture identity

`LIBTV-FIX-LOCAL-NODE-DATA-01`

Status：`REQUIRED_DISPOSABLE / DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`。

### 12.2 Corpus

The fixture contains：

1. one valid V0 sample for all 11 runtime types；
2. image variants for rotate/frame/Director capture；
3. video/audio variants for every current nested operation metadata type；
4. complete and broken shot breakdown aggregates；
5. complete and partial long-video process cohorts；
6. Director shell plus data/blob exported results；
7. repo path、https、data and blob media locators；
8. unknown type、future dataVersion、unknown field and unmodeled reference cases；
9. nested marks/regions/items arrays with mutation sentinels；
10. deterministic node/edge/aggregate ID providers。

Each scenario starts from fresh pure input or fresh Page. Undo is not fixture teardown。

### 12.3 Required assertions

| Case | Required result |
|---|---|
| registry completeness | every runtime renderer type has exactly one V0 entry |
| unknown type/version | stable reject/unknown；zero partial graph |
| nested history | no shared marks/regions/items references across snapshots |
| graph ref map | sourceNodeId/edgeId map exactly or operation blocks |
| scoped IDs | region/mark/item keys are not passed through graph nodeMap |
| shot aggregate exact | both directions and edges map in one transaction |
| shot aggregate partial | reject or explicit authoring reset only |
| process aggregate exact | one new processId shared by complete copied cohort |
| process aggregate partial | reject with stable reason |
| Director shell | no false workspace-copy claim |
| blob/data media | stable portability diagnostic/budget result |
| delete repair | no surviving stale owned refs after accepted transaction |

## 13. `LIBTV-VR-012` Replacement Design

### 13.1 Pure suite

Future pure verifier should cover：

- registry type/dataVersion allowlist；
- per-type normalize and unknown-field behavior；
- role classification completeness；
- operation profile transform matrix；
- node/edge/aggregate ID mapping；
- reciprocal shot refs；
- complete/partial process cohort；
- status reset decisions；
- media locator classification and byte budget；
- deep nested isolation；
- stable reason precedence and zero mutation。

### 13.2 Browser suite

Future browser checks should use only sanctioned fixture setup and assert：

- all registered runtime types render the expected shell；
- copy/duplicate selection produces inspectable mapped data attributes where components expose them；
- one-step undo/redo restores node/edge/data identity；
- no active overlay/Director/editor session is serialized as graph data；
- aggregate/rejection cases produce no partial nodes, edges, selection or history。

### 13.3 Historical coverage

`VR-012` supplements, not replaces：

- Batch 5 duplicate closure/history coverage；
- `LIBTV-VR-009` graph connection validation；
- `LIBTV-VR-010` document/snapshot codec；
- `LIBTV-VR-011` subgraph copy planner；
- Director domain verifiers for Director-internal object/timeline state。

Exit condition：all 11 types and every current identity-bearing V0 path have a tested registry rule, and no supported operation depends on arbitrary `Record<string, unknown>` spread。

## 14. Implementation Slices After Authorization

### Slice A: pure registry and validators

- add canonical runtime type/data registry；
- represent current data as explicit V0；
- normalize exact accepted fields；
- return typed reason/diagnostic results；
- do not change UI behavior。

### Slice B: deep history codec

- replace shallow nested snapshot aliases with registry-driven deep isolation；
- preserve exact logical IDs/status；
- keep viewport/selection/UI excluded。

### Slice C: reference and aggregate integrity

- add source/edge/shot/process scanners；
- expose full-cohort plans；
- block dangling/partial mutations before commit。

### Slice D: copy integration

- connect registry transforms to `LibTVSubgraphCopy` planner；
- separate exact aggregate copy and standalone authoring reset；
- preserve current single-node incident edge only as reviewed compatibility branch。

### Slice E: document/clipboard integration

- use the same normalizers with operation-specific policies；
- enforce dataVersion/media diagnostics；
- keep whole-document and packet identity policies separate。

### Slice F: delete repair

`SOURCE_PRODUCT_DECISION_REQUIRED` for shot result cascade、process partial delete and derived provenance detach. Use the planner、reason and fixture boundary in [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)；implement only after behavior choice is documented，and keep every accepted variant a one-step graph transaction。

## 15. Non-Goals

- no runtime/store/type/component/test edits in this research batch；
- no backend asset store、provider runner、billing、remote persistence or collaboration design；
- no attempt to serialize Director Three.js objects/timeline under the LibTV graph contract；
- no source claim that LibTV uses these field names or aggregate rules；
- no generic suffix-based ID rewrite；
- no silent unknown-field drop for copy/import/history；
- no `blob:` URL presented as portable media；
- no partial aggregate mutation followed by best-effort repair。

If a field cannot be classified before mutation, return to registry review rather than extending object spread。
