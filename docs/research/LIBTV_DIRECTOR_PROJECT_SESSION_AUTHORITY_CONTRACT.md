# LibTV Director Project And Session Authority Contract

> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` /
> `V1_CODEC_RUNTIME_PASS` / `OWNER_SESSION_FOCUSED_RUNTIME_PASS` /
> `AUTHORED_HISTORY_POINTER_DELETE_FOCUSED_RUNTIME_PASS` /
> `ASYNC_AUTHORITY_FOCUSED_RUNTIME_PASS` /
> `PERSISTENCE_FOCUSED_RUNTIME_PASS` /
> `CLIPBOARD_REMAP_FOCUSED_RUNTIME_PASS` /
> `OWNER_REACHABILITY_FOCUSED_RUNTIME_PASS` /
> `SOURCE_PARITY_UNKNOWN_OR_PARTIAL`.
>
> Scope: LibTV clone Director 的 portable project、owner、session、runtime
> projection、resource reference、open/switch/close/delete/duplicate 和 graph bridge。
>
> Evidence baseline:
> [`liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md`](liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md)，
> [`liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md`](liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md)，
> [`liblib-canvas-batch76-2026-08-27/IMPLEMENTATION.md`](liblib-canvas-batch76-2026-08-27/IMPLEMENTATION.md)，
> clone `a7bcf21`，StoryAI `8c8bd36`，Open Canvas
> `cf3a906bb8c35bb940d3267497e7f394b8f42582`。
>
> Authorization boundary: 本文定义后续 runtime 实施合同，不把 StoryAI/Open
> Canvas 行为声明为 LibTV source fact，也不授权移动 submodule pointer、接入后端、
> 云同步或导入上游 JSON。

## 1. Contract Objective

当前 Director 已经是功能丰富的 R3F authoring island，但其作者状态仍是单例
Zustand store。`openSession(sourceNodeId)` 只替换 source ID，scene、objects、
timeline、captures 和 local library 会跨 node 保留；UI surface owner 虽有
`canvasId + nodeId`，authoring document 没有对应 owner。

本合同建立以下分权：

```text
Director project document
  != open editor session
  != playback/render projection
  != temporary browser resources
  != ordinary React Flow result projection
```

必须能回答：

1. 这个 Director project 属于哪个 route/canvas/source node；
2. 当前 document 是哪个 schema version 和 generation；
3. 哪些值可序列化、可迁移、可进入 history；
4. 哪些值只属于当前 session 或 R3F runtime；
5. open/switch/close/delete/duplicate 精确处理哪些 owner；
6. delayed capture/export 如何证明目的地仍然有效；
7. refresh、decode failure 和 storage quota 时如何保持 prototype honest；
8. 哪些行为仍需 LibTV source/product evidence。

## 2. Evidence Boundary

### 2.1 `CLONE_STATIC_FACT`

当前 clone 证明：

- Director 是普通 LibTV route 内 lazy-loaded 全屏 R3F island；
- `uiStore` 持有 `activeDirectorCanvasId + activeDirectorNodeId`；
- `directorStore` 仍是单例实例，但当前 active state 由 structured
  route/canvas/source owner、project ID、session ID 和 generation 绑定；
- `authoredObjects` 承载 portable authored baseline，`objects` 是 timeline/path
  与当前时间派生的 R3F runtime projection；
- capture/export 向普通 canvas 回流时 late-read `activeCanvasId`；
- scene/timeline 不持久化，local model catalog 以全局 localStorage key 持久化；
- graph return 使用普通 canvas graph history，Director document mutation 现在使用
  project-local domain history；两者仍保持隔离。
- Batch 67 已增加独立 `DirectorProjectDocumentV1`、strict
  decode/normalize/encode、current state snapshot adapter 和 pure corpus；
- codec 排除 selection/playback/panel/phone runtime、capture bytes、
  Three.js refs 和 graph `sentNodeId`，并检查 unknown/future/duplicate/dangling/
  non-finite 输入；
- Batch 67 结束时 codec 尚未成为 `directorStore` source of truth；Batch 68/69
  已继续接入 owner registry、snapshot/restore 与 authored/runtime authority。
- Batch 68 已增加 structured owner key、in-memory project registry、
  project/session/generation、document restore adapter 和 owner-aware
  open/switch/close；
- A/B source、cross-canvas、close/reopen、duplicate reset、active delete tombstone 和
  memory capture sidecar 已通过 focused runtime；
- Batch 69 已增加 `authoredObjects` baseline，timeline/path sampling 不再覆盖
  portable snapshot；object/camera/pose authoring 与 close/reopen focused runtime
  已通过；
- Batch 70 已增加 project-local command/history、undo/redo、redo truncation 和
  gesture coalescing；Batch 71 已覆盖 Inspector/pose/camera/path/free-draw
  pointer lifecycle；Batch 72 已覆盖 reference-aware delete、关系闭包、相机回退、
  资源阻断/级联和 exact delete/undo/redo；
- Batch 73 已为 capture、animation export 和 phone take import 增加
  operation/attempt、owner/session/generation、source/request fingerprint、
  terminal convergence 和 resource transfer/release；普通画布 async ingress
  仍未统一接入；
- Batch 74 已增加 clone-owned browser-local versioned storage envelope、
  strict V1 load/normalize、owner/project/generation/fingerprint guard、
  reload authored restore、stale save ignore、corrupt/future/mismatch
  zero-replacement 和 write-failure `SESSION_ONLY` 语义；
- Batch 75 已增加 project-scoped session clipboard、typed entity closure、
  object/group/track/path/keyframe/anchor two-pass remap、camera relation
  detach/remap、stable resource alias、one-entry paste history 和 reload
  non-persistence boundary；
- Batch 76 已增加 all-canvas live owner collection、deterministic reachability
  planner、inactive source/canvas one-time tombstone、active shell/session/runtime
  两阶段 cleanup、repeated reconciliation 幂等和 graph undo/persistence retained
  boundary；
- Batch 79 已增加 whole-project duplicate 的 graph/Director two-pass identity
  remap、stable resource descriptor policy、fresh missing-document policy、clean
  target authority 和 source/target persistence isolation；
- durable tombstone、storage/resource cleanup、ordinary canvas persistence、
  strict import/export、remote persistence 和 source-exact storage 仍未解决。

### 2.2 `STORYAI_UPSTREAM_FACT`

固定 StoryAI 证明一种可借方法：

- `DirectorProject.version`；
- scene/assets/objects/cameras 分层；
- scoped persistence；
- project/runtime internal state 分开；
- open scoped scene、snapshot、copy/paste、undo。

同时存在不能复制的反例：

- runtime shape guard 过浅；
- JSON import 使用 cast；
- persisted snapshot 混入 selection/view/panel UI；
- data URL/localStorage quota 与 lifecycle 不完整；
- undo 无 redo；
- camera shot 双实体和产品语义不等于当前 clone。

### 2.3 `OPEN_CANVAS_FACT`

Open Canvas 提供 stable document ID、schema/normalization、active owner、hydrate、
async convergence、resource lease 和 multi-document lifecycle 的设计问题与参考方法。
它不提供 LibTV Director 的视觉、camera、timeline、resource 或 persistence 真相。

### 2.4 `SOURCE_UNKNOWN`

当前没有足够 LibTV authenticated Director 证据证明：

- source 是否按 node/canvas/project 保存；
- source schema、migration、import/export 和 storage 技术；
- close/switch/delete/duplicate 的 exact 产品语义；
- source project 是否包含 selection、playhead、panel state；
- source capture/export 的 durable resource identity。

以下规则是 clone correctness 决策，不是 source-exact 声明。

## 3. Authority Composition

| Authority | 本合同拥有 | 委托 |
|---|---|---|
| ordinary canvas lifecycle | Director owner 与 canvas generation 的组合 | [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) |
| Director command/history/delete | project mutation 接收与 document snapshot | [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md) |
| media/resource | Director project 只保存 stable descriptor/reference | [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) |
| async result | captured owner/generation、source/request fingerprint、attempt/result convergence 和 destination request | [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) |
| selection/focus | Director 是 foreground command context | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) |
| feedback | project/session lifecycle outcome | [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) |
| graph result | typed result intent与provenance | ordinary canvas graph transaction authority |

本合同不把 Director project 塞进 `canvasStore` graph node data，也不让
`canvasStore` 成为 R3F runtime owner。

## 4. Vocabulary

| Term | Definition |
|---|---|
| Director owner | route/canvas/source node 的稳定组合 |
| project ID | 独立于 source node display ID 的 Director document identity |
| schema version | decoder/migration 使用的 document version |
| owner generation | open/switch/delete/restore 后递增的本地 freshness epoch |
| project document | portable authored state |
| project registry | owner key 到 current project record 的映射 |
| session | 一次打开到关闭的 foreground editor lifetime |
| session UI | selection、playhead、panel、tool 等可丢弃状态 |
| runtime projection | 根据 project + playhead 派生的 R3F render objects |
| resource reference | project 中指向 stable asset/result descriptor 的 serializable ref |
| resource lease | session/runtime 对 File/Blob/data/object URL 的临时持有责任 |
| graph projection | capture/export 在普通 React Flow 中产生的 node/edge/result metadata |
| tombstone | source/project 被删除后保留的不可编辑 lifecycle record |

## 5. Owner And Identity Model

### 5.1 Owner key

概念模型：

```ts
interface DirectorProjectOwner {
  route: "libtv";
  canvasId: string;
  sourceNodeId: string;
}

interface DirectorProjectIdentity extends DirectorProjectOwner {
  projectId: string;
  schemaVersion: 1;
  generation: number;
}
```

规则：

1. `canvasId + sourceNodeId` 在一个 live project registry 中唯一；
2. `projectId` 不从 display name、array index 或 active canvas 推导；
3. generation 是 runtime freshness，不作为跨设备 durable revision；
4. source node duplicate 不得复用 project ID；
5. source node rename/move 不改变 project ID；
6. canvas duplicate 必须显式 clone或reset每个 Director project；
7. missing owner 不自动 fallback 到当前 active canvas。

### 5.2 Registry record

```ts
interface DirectorProjectRecordV1 {
  identity: DirectorProjectIdentity;
  document: DirectorProjectDocumentV1;
  persistence: {
    status: "UNSAVED" | "SAVED_LOCAL" | "SAVE_FAILED" | "UNAVAILABLE";
    updatedAt: string;
    lastErrorReason: string | null;
  };
  lifecycle: "ACTIVE" | "CLOSED" | "TOMBSTONED";
}
```

`persistence.status` 是 storage outcome，不进入 Director semantic history。

## 6. Portable Document V1

以下是合同形状，不要求实现完全使用同名 TypeScript：

```ts
interface DirectorProjectDocumentV1 {
  schemaVersion: 1;
  projectId: string;
  owner: {
    route: "libtv";
    canvasId: string;
    sourceNodeId: string;
  };
  scene: DirectorSceneDocumentV1;
  objects: DirectorObjectDocumentV1[];
  groups: DirectorGroupDocumentV1[];
  activeCameraId: string;
  timeline: DirectorTimelineDocumentV1;
  outputPreferences: {
    aspectRatio: "16:9" | "9:16" | "1:1";
  };
  resourceRefs: DirectorResourceReferenceV1[];
  captureDescriptors: DirectorCaptureDescriptorV1[];
}
```

### 6.1 Project fields

| Current data | V1 disposition |
|---|---|
| scene name/colors/ground/grid | document |
| object identity/kind/primitive/transform/visible/locked | document |
| character rig/pose authored state | document |
| camera fov/target/relation/follow settings | document |
| group identity/label/member IDs/crowd config | document |
| active camera identity | document |
| timeline duration/loop/auto-keyframe | document |
| tracks/keyframes/speed curves | document |
| paths/anchors/handles/transform/initial baseline | document |
| aspect ratio default | document output preference |
| stable local/remote asset metadata | resource reference |
| capture stable descriptor/provenance | capture descriptor |

### 6.2 Excluded fields

不得进入 document：

```text
sourceNodeId as a lone owner field
selection IDs
view/transform mode
thirds/panel collapsed
current playhead and zoom
selected track/keyframe/path/anchor/handle
isPlaying / isCapturing
motionPathDraft
phone recorder status/start/sample buffer/baseline
export progress/error/request ID
File / Blob / object URL
Three.js Object3D/material/texture/renderer/control refs
DOM/native event/pointer capture
sentNodeId graph projection cache
```

### 6.3 Authored object versus sampled projection

这是 V1 的强约束：

```text
document.objects
  = authored baseline and direct semantic edits

runtime.sampledObjects
  = derive(document.objects, timeline, currentTime)
```

seek/playback 不得覆写 `document.objects`。Transform/Inspector edit 必须明确修改：

- authored base transform；
- current-time keyframe；
- 或二者组成的具名 command。

不能继续通过“先 sampled 写回 objects，再猜哪部分可保存”构造 document。

## 7. Session And Runtime Model

### 7.1 Session envelope

```ts
interface DirectorSessionV1 {
  sessionId: string;
  projectId: string;
  owner: DirectorProjectOwner;
  generation: number;
  openedAt: string;
  ui: DirectorSessionUiV1;
  runtime: DirectorRuntimeStateV1;
  resourceLeaseIds: string[];
}
```

### 7.2 Session UI

Session UI 可在同一次 open 内保持，但默认不持久化：

- selected object(s)/group/capture；
- view mode、transform mode、thirds；
- panels collapsed/mobile drawer/export panel；
- current time、timeline zoom、editor mode；
- selected track/keyframe/path/anchor/handle；
- focus-return target。

打开新 project 时，所有 ID 必须对新 document 重新验证。不得把旧 selection 直接套到
新 document。

### 7.3 Runtime

Runtime 包含：

- sampled render objects；
- playback/capture/export/phone recording；
- path drawing draft；
- pointer gesture baseline；
- R3F refs、renderer、controls和 frame handles；
- MediaRecorder、pending promises、animation frame IDs；
- temporary resource leases。

Runtime 由 `sessionId + projectId + generation` 拥有。owner 变化后所有 late callback
必须返回 `STALE`，不能把新 session 当旧 callback 的目标。

## 8. Decode, Migration And Validation

### 8.1 Decode pipeline

```text
unknown input
  -> envelope/type check
  -> exact supported schema version
  -> scalar/tuple finite validation
  -> ID uniqueness
  -> enum and bounded value validation
  -> reference integrity
  -> resource locator portability classification
  -> normalization
  -> migration if explicitly supported
  -> detached canonical document
```

禁止：

- `JSON.parse(...) as DirectorProjectDocumentV1`；
- 只检查顶层 array 存在；
- silently drop unknown enum/reference；
- 对 unsupported future version 当作 V1；
- decode failure 后部分替换 live project。

### 8.2 Validation invariants

1. project ID、owner 和 envelope 一致；
2. object/group/track/keyframe/path/anchor/capture/resource ID 在各自 namespace 唯一；
3. active camera resolves且 kind 为 camera；
4. group member resolves且 kind 为 character，一个 character最多属于一个 group；
5. non-group track object resolves；
6. group track同时解析 `objectId/groupId` 到同一 group；
7. track motion path resolves且 path object matches track object；
8. camera relation target resolves到允许的 object且不能是自己；
9. selection/runtime IDs 不参与 document decode；
10. tuple/number有限，scale/FOV/time/duration在声明范围；
11. object/data URL 由 portability policy处理，不能仅因非空而通过；
12. decode/migration失败为 zero replacement。

### 8.3 Unknown fields

V1 默认：

- envelope unknown top-level field：reject；
- known object 的 unknown field：reject；
- future extension 必须通过 version/migration进入；
- display-only metadata 需先进入 schema registry，不能在 runtime 任意 spread。

严格策略优先于“尽量载入”，因为当前 prototype 没有恢复损坏 project 的 UI。

## 9. Project Lifecycle

### 9.1 States

```text
ABSENT
CREATING
LOADING
OPEN
FLUSHING
CLOSED
TOMBSTONED
LOAD_FAILED
SAVE_FAILED
```

### 9.2 `OPEN_DIRECTOR_PROJECT`

Input：

```text
owner { route, canvasId, sourceNodeId }
expected canvas generation
requested project ID or create policy
```

Rules：

1. validate canvas/source existence；
2. same owner + same open session 是 no-op/focus request；
3. 有当前其他 owner 时先执行 close/switch plan；
4. load/decode registry record；不存在则创建 V1 default；
5. generation 递增；
6. create fresh session/runtime；
7. atomically publish document + session + UI owner；
8. failed load 不以 default scene 覆盖损坏 record，返回 recoverable failure。

### 9.3 `CLOSE_DIRECTOR_SESSION`

Rules：

- busy command是否可取消由其 runtime profile决定；
- accepted project changes先形成稳定 document snapshot；
- storage failure不伪装成功，project可留在 memory registry；
- playback、capture、draft、phone、export、listeners、leases按 manifest停止；
- UI owner清空；
- project可保持 `CLOSED` record；
- close本身不进入 Director semantic history。

### 9.4 `SWITCH_DIRECTOR_OWNER`

```text
close current generation
  -> preserve/flush current project record
  -> load/create target project
  -> create target session generation
  -> validate target IDs and defaults
  -> publish once
```

不得先改 `sourceNodeId`，再继续复用旧 arrays。

### 9.5 `DELETE_SOURCE_OR_CANVAS`

Source/canvas delete 必须获得 Director lifecycle impact：

```ts
type DirectorOwnerDeleteDisposition =
  | "DELETE_PROJECT"
  | "TOMBSTONE_PROJECT"
  | "DETACH_PROJECT"
  | "BLOCK_UNKNOWN";
```

当前 clone correctness 默认：

- active session立即 invalidate/close；
- delayed result变 stale；
- project record先 tombstone，不静默绑定 fallback canvas；
- graph export results可独立保留 provenance；
-真正删除 persistence/resource需独立明确 command。

Batch 76 的 clone runtime 已按该默认实现：

1. page 从全部 `canvases[].nodes` 构造 live Director owner set；
2. 只 reconciliation registry 中已存在且非 `TOMBSTONED` 的 records；
3. inactive owner 只 tombstone 对应后台 project；
4. active owner 先关闭 shell owner并同步 tombstone session，使 async context
   立即 stale；
5. shell teardown 后再清 Director runtime/history/capture/clipboard projection；
6. ordinary graph delete仍只有原 graph history step；
7. graph undo恢复 source node，但不自动 untombstone Director project；
8. durable tombstone 成功后清理 persistence load path、history/capture archive 和
   tombstoned registry transient captures；local resource 只有在其他 live 或
   session-only project 都不引用时释放；
9. storage unavailable/write failure 保留 session-only document/resource，不伪造
   durable cleanup；
10. graph undo 恢复 source node，但不自动 untombstone Director project。

Batch 80 已将上述 clone-owned durable tombstone/resource cleanup 通过 focused
runtime；LibTV source/product 的删除、恢复、提示和远端资源语义仍未确认。

### 9.6 `DUPLICATE_SOURCE_OR_CANVAS`

Duplicate 不是共享同一 document：

1. allocate new owner + project ID；
2. deep clone portable project；
3. remap所有 project-local IDs；
4. rewrite group/camera/track/path/preset/capture refs；
5. reset session/runtime/history；
6. resource reference根据 resource policy alias/copy/block；
7. graph result links/sentNodeId不复制为 live projection；
8. one lifecycle transaction，不能部分 duplicate。

若 remap/resource policy未实现，返回 `BLOCK_UNKNOWN`，不要共享旧 project。

Batch 75 已提供可复用的 object/group/track/path/keyframe/anchor remap machinery。
Batch 79 已将其扩展为独立的 whole-project owner/project allocation、capture
descriptor policy、resource policy、history reset、persistence transaction 和
source/canvas lifecycle fixture；它仍是 clone-owned decision，不能当作 LibTV
source duplicate 语义。

## 10. Persistence Contract

### 10.1 Storage-neutral boundary

本合同保持 storage-neutral 抽象；当前 clone 已在 Batch 74 选择
browser-local `localStorage` 作为可注入 prototype adapter。正式产品后端、
IndexedDB 和云端同步仍不在本批范围。抽象边界为：

```ts
interface DirectorProjectStorage {
  load(owner: DirectorProjectOwner): Promise<unknown | null>;
  save(record: DirectorProjectRecordV1): Promise<DirectorStorageResult>;
  tombstone(identity: DirectorProjectIdentity): Promise<DirectorStorageResult>;
}
```

如加入 browser persistence，应：

- key按 route/canvas/source owner 隔离，envelope 另存 project ID 和 schema；
- 保存 canonical document，不保存 session/runtime；
- 可注入 storage failure/quota；
- write completion比较 generation；
- 禁止 raw File/Blob/Object3D；
- data URL 只有在明确预算/portable policy下允许；
- load failure有显式状态，不自动覆盖坏数据。

### 10.2 Save semantics

- project command commit 与 storage save不是同一 history entry；
- save可 debounce，但每次 request携带 project ID/generation/document fingerprint；
- old save completion不得更新 current project status；
- storage unavailable 时，UI 必须标明 session-only；
- persistence 成功不代表 graph result已materialize或云端同步。

### 10.3 Batch 74 clone implementation

`src/lib/directorProjectPersistence.ts` 是当前 clone 的 storage authority：

- `DirectorProjectStorageEnvelopeV1` 包含 storage schema、project ID、owner、
  generation、savedAt、canonical document 和 document fingerprint；
- load 先做 envelope shape 检查，再调用 `decodeDirectorProjectDocument`，
  校验 document/envelope identity 和 fingerprint；
- capture descriptor 只有在有 stable `resourceRefId` 时才进入 persisted
  document；当前 data URL capture 因没有 stable locator 而保持 session-only；
- `lifecycle: "TOMBSTONED"` envelope 是 owner-scoped durable deletion marker；
  合法 marker 使 load 返回 `PROJECT_TOMBSTONED`，旧 save 不得覆盖，重复写入幂等；
- tombstone generation 低于当前 persisted document 时拒绝，避免 stale cleanup；
- Batch 80 的 store coordinator 只有在 tombstone durable 成功后才清理
  project-local history/capture archive、registry transient capture sidecar 和
  不再共享的 local model descriptor；
- `beginSave`/`completeSave` 对同一 owner 的旧 request 产生
  `STALE_IGNORED`，浏览器同步 adapter 同时拒绝低 generation 覆盖；
- `REJECTED`、`SESSION_ONLY` 和 `STALE_IGNORED` 是 storage outcome，不进入
  Director semantic history，也不改变当前内存 state；
- fresh-page Batch 74 已验证 reload、A/B owner key、corrupt payload 保留、
  runtime/UI exclusion、普通 graph/history isolation 和模拟 quota。

## 11. Graph Bridge

### 11.1 Capture/export request owner

Director 向普通 graph提交前必须冻结：

```ts
interface DirectorGraphResultIntent {
  projectId: string;
  sessionId: string;
  directorGeneration: number;
  destination: {
    canvasId: string;
    canvasGeneration: number;
    sourceNodeId: string;
  };
  resultId: string;
  resultKind: "CAPTURE" | "ANIMATION_EXPORT";
  resourceDescriptor: DirectorResultResourceDescriptor;
  provenance: DirectorResultProvenance;
}
```

`canvasStore.activeCanvasId` 不得作为异步 completion 的目的地。

### 11.2 Commit rules

1. destination canvas/source存在且 generation/fingerprint current；
2. result identity未提交过；
3. resource descriptor可渲染并有明确 lease owner；
4. graph full plan先验证；
5. accepted -> 普通 graph one history step；
6. stale/rejected/duplicate -> zero graph/history；
7. result graph node创建不写 Director project history；
8. graph undo不重放 capture/export；
9. graph delete按 resource/provenance合同处理，不隐式删除 Director project。

## 12. Fixture Contract

预留 fixture：`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`。

必须包含：

```text
canvas A / source DA / project PA / generation 1
canvas A / source DB / project PB / generation 1
canvas B / source DC / project PC / generation 1
portable project with object/group/camera/track/path/capture/resource refs
invalid version/duplicate ID/dangling ref/non-finite corpus
delayed capture/export queue
storage adapter with success/failure/quota/stale completion
deterministic ID and clock
```

场景：

- open A、edit、close、reopen A；
- A -> B source switch不串 scene；
- canvas A -> B switch；
- delete source/canvas during playback/export；
- duplicate source/project remap；
- refresh/load valid；
- corrupt/unsupported project zero replacement；
- seek/playback不改变 authored document；
- storage fail保持 memory project并显示 honest状态；
- stale/duplicate async graph result zero commit。
- same-project clipboard paste remaps typed identities and creates one history；
- cross-project clipboard and reload remain zero-transfer。

## 13. Verifier Contract

预留 verifier：`LIBTV-VR-024`，与 command/history/delete合同共享 authority fixture，
但分 scenario 运行。

最低断言：

```text
owner/project/schema/generation
open-switch-close state
document/session/runtime field allowlist
decode/migration zero-partial
authored-vs-sampled separation
storage stale/failure disposition
graph destination immutability
zero/one history domains
resource lease diagnostics
console/page error
worktree artifact cleanup
```

current smoke只需证明一个低成本 open/switch/close链；full gate再覆盖 corrupt
document、duplicate、delete和 delayed result。

## 14. Implementation Slices

### `DIR-PROJECT-I01` Schema And Pure Codec

状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 67。

- 已增加 V1 types、strict decoder、normalizer 和 deterministic encoder；
- 已将 current Director state 通过显式 adapter 转为 canonical document；
- 已增加 dependency-free pure contract corpus；
- V1 当前对 future version 明确 reject，migration registry 等第二个 schema
  出现时再实现；
- 没有 UI、persistence、history/delete 或 store authority 修改。

### `DIR-PROJECT-I02` Owner Registry And Session Lifecycle

状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 68。

- 已增加 structured owner key 和 in-memory registry；
- 已增加 per-owner project ID、per-open session ID 与 generation；
- 已接 current store snapshot/restore adapter；
- 已验证 A/B、cross-canvas、close/reopen 和 same-owner focus；
- duplicate source 当前采用新默认 project reset，不共享原 project；
- Batch 68 的 active source invalid 兼容路径已随 Batch 76 收敛为
  tombstone + 两阶段 shell/runtime cleanup；
- inactive registry tombstone 已由 Batch 76 的 `DIR-PROJECT-I06` 接入；
- capture bytes/sent graph ID 仅保存在 memory sidecar；
- Batch 73 已接入 capture/export/phone 的 clone-owned async destination
  authority；普通画布 async ingress 和 durable browser persistence 仍未接入；
  authored/runtime split 已由 Batch 69 的 `DIR-PROJECT-I03` 完成。

### `DIR-PROJECT-I03` Authored/Runtime Projection Split

状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 69。

- `authoredObjects` 是 portable document baseline；
- timeline、playback、speed curve、camera preset 和 motion path sampling 从
  authored state 派生 `objects` runtime projection；
- object/camera/pose/group 与对象集合 authoring writer 同步维护 authored state；
- phone live preview 保持 runtime-only；
- close/reopen 在 time-zero 从 authored document 重新派生 runtime；
- focused verifier 已覆盖 seek/playback/path fingerprint stability、authoring
  restore、A/B owner 和普通 graph/history isolation。

### `DIR-PROJECT-I04` Persistence Adapter

- 状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 74；
- browser-local adapter已覆盖quota/corrupt/stale fixture；
- canonical V1 document、owner-scoped key 和 session-only failure 已验证；
- 不扩展到cloud/backend。

### `DIR-PROJECT-I05` Session Clipboard Identity Remap

- 状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 75；
- project-scoped packet、typed closure 和 two-pass remap 已实现；
- stable resource exact alias、external camera detach 和 one-entry history 已验证；
- clipboard/paste ordinal 不持久化、不跨 project；
- whole-project duplicate、resource bytes transfer 和 system clipboard 仍是独立
  lifecycle/resource slices。

### `DIR-PROJECT-I06` Owner Reachability Reconciliation

- 状态：`IMPLEMENTED_FOCUSED_PASS`，见 Batch 76；
- 全部 canvas/source nodes 构成 live owner authority，而非只读取 active canvas；
- pure planner只处理 existing registry records，规范化 invalid/duplicate owner，
  并确定性输出 preserved/tombstone/already-tombstoned/active-invalidated；
- inactive source/canvas 删除只 tombstone对应 project，不影响 foreground；
- active owner采用 shell close -> registry/session tombstone -> R3F teardown ->
  runtime/history/capture/clipboard projection cleanup；
- repeated reconcile不重复增加 generation，rename/switch/unrelated delete不误伤；
- tombstoned owner reopen拒绝，旧 async completion立即 stale；
- ordinary graph history 不受影响；
- Batch 80 已在 durable success 后清理 persistence tombstone、archive、transient
  captures 和 unshared local descriptor；失败保持 session-only；
- graph undo 不 restore project，strict import/export、真实 resource materialization
  和 source parity 保持独立决策。

每个 slice 独立计划、fixture、verifier、commit/push。不得以“建立 project document”
为由一次性重写全部 Director components。

## 15. Decision Queue

| Question | Current default | Unlock |
|---|---|---|
| source node delete后project | tombstone + close | LibTV source/product |
| canvas duplicate时resource | alias stable refs，block unknown local bytes | resource contract |
| last camera可否删除 | 本合同不决定 | command/delete contract + source/product |
| aspect ratio是project还是session | V1 project default + session draft | source evidence |
| capture descriptor持久化 | 只存stable locator；否则session-only | resource materialization |
| storage backend | in-memory first | prototype/product scope |
| LibTV JSON compatibility | absent | source schema evidence |

## 16. Non-Goals

- 不引入 StoryAI iframe/postMessage 或协议名；
- 不复制上游 CSS/visual geometry；
- 不实现 cloud sync、revision conflict 或多人协作；
- 不把普通 React Flow graph document与Director project合成一个store；
- 不让 FrameOS 使用本合同；
- 不把 current local data URL proxy描述成真实 durable asset；
- 不在 project schema批次顺手加 panorama、multi-camera或新面板。

## 17. Completion Criteria

本合同的 codec 子项已在 Batch 67 升级为 `V1_CODEC_RUNTIME_PASS`，同步
owner/session 子项已在 Batch 68 升级为
`OWNER_SESSION_FOCUSED_RUNTIME_PASS`，authored/runtime 子项已在 Batch 69
升级为 `AUTHORED_RUNTIME_FOCUSED_PASS`，owner reachability 子项已在 Batch 76
升级为 `OWNER_REACHABILITY_FOCUSED_RUNTIME_PASS`，whole-project duplicate 子项
已在 Batch 79 升级为 `WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS`：

1. 两个 source node 和两个 canvas 已证明 project 不串场；
2. open/switch/close、same-owner focus、duplicate reset 和 active delete tombstone
   已有 typed/focused runtime；
3. session/runtime/capture sidecar exclusion 在 store integration 后仍成立；
4. seek/playback/path sampling 不污染 authored fingerprint，object/camera/pose
   authoring 可在 close/reopen 后恢复；
5. inactive source/canvas delete、active cleanup、重复 reconcile、stale async、
   graph undo/persistence retained boundary 已有 focused runtime；
6. whole-project duplicate 的 graph/document identity remap、resource policy 和
   clean target authority 已有 focused runtime；
7. focused verifier、`npm run check`、docs check 和实施台账通过。

整体 project/session authority 仍不能标记 complete，以下条件尚未满足：

1. graph undo restore/recreate policy 与用户可见 delete/recovery feedback 仍未确认；
2. 普通画布 delayed result 也只写 captured canvas/source/generation；
3. duplicate deep clone/remap 与 resource policy 已在 clone-owned Batch 79 明确，
  但 LibTV source duplicate 语义仍未知；
4. ordinary canvas graph/document persistence 有独立合同和 fixture；
5. 真实资源 materialization、stable locator 和远程 persistence 有产品范围。

Batch 73 已关闭 Director capture/export/phone 的 async owner freshness 子项；
Batch 74 已关闭 clone-owned Director browser-local durable document persistence
子项；Batch 75 已关闭 same-project session clipboard identity-remap 子项；
Batch 76 已关闭 memory-only owner reachability reconciliation 子项；Batch 79 已
关闭 clone-owned whole-project duplicate 子项；Batch 80 已关闭 clone-owned durable
tombstone/storage/resource cleanup 子项。它们都不关闭 graph undo restore、
ordinary canvas async/persistence、strict import/export、remote storage、真实资源或
source-exact LibTV 子项。
