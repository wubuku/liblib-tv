# LibTV Director Project And Session Authority Contract

> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` /
> `V1_CODEC_RUNTIME_PASS` / `OWNER_SESSION_FOCUSED_RUNTIME_PASS` /
> `AUTHORED_ASYNC_PERSISTENCE_RUNTIME_MISSING` /
> `SOURCE_PARITY_UNKNOWN_OR_PARTIAL`.
>
> Scope: LibTV clone Director 的 portable project、owner、session、runtime
> projection、resource reference、open/switch/close/delete/duplicate 和 graph bridge。
>
> Evidence baseline:
> [`liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md`](liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md)，
> [`liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md`](liblib-canvas-batch67-2026-08-27/IMPLEMENTATION.md)，
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
- `directorStore` 是单例，只有 `sourceNodeId`，没有 project ID/version/generation；
- `objects` 同时承载 authored values 和 timeline sampled projection；
- capture/export 向普通 canvas 回流时 late-read `activeCanvasId`；
- scene/timeline 不持久化，local model catalog 以全局 localStorage key 持久化；
- graph return 使用普通 canvas graph history，Director 内部没有 domain history。
- Batch 67 已增加独立 `DirectorProjectDocumentV1`、strict
  decode/normalize/encode、current state snapshot adapter 和 pure corpus；
- codec 排除 selection/playback/panel/phone runtime、capture bytes、
  Three.js refs 和 graph `sentNodeId`，并检查 unknown/future/duplicate/dangling/
  non-finite 输入；
- codec 仍未成为 `directorStore` source of truth，单例 session 与
  authored/runtime 混写事实没有因此消失。
- Batch 68 已增加 structured owner key、in-memory project registry、
  project/session/generation、document restore adapter 和 owner-aware
  open/switch/close；
- A/B source、cross-canvas、close/reopen、duplicate reset、active delete close 和
  memory capture sidecar 已通过 focused runtime；
- `objects` authored/sampled 混写、inactive owner tombstone、async graph
  destination、persistence 与 history/delete 仍未解决。

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
| async result | captured owner/generation 和 destination request | [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) |
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

最终 cascade/tombstone/retain 是 `SOURCE_PRODUCT_DECISION_REQUIRED`。

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

## 10. Persistence Contract

### 10.1 Storage-neutral boundary

本合同不选择 localStorage、IndexedDB 或 backend。实现必须先有 storage adapter：

```ts
interface DirectorProjectStorage {
  load(owner: DirectorProjectOwner): Promise<unknown | null>;
  save(record: DirectorProjectRecordV1): Promise<DirectorStorageResult>;
  tombstone(identity: DirectorProjectIdentity): Promise<DirectorStorageResult>;
}
```

第一 prototype slice 可以使用 in-memory registry；如加入 browser persistence，应：

- key包含 route/canvas/source/project/schema；
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
- active source invalid 会 close session，inactive registry tombstone 未接；
- capture bytes/sent graph ID 仅保存在 memory sidecar；
- 没有 browser persistence、async destination 或 authored/runtime split。

### `DIR-PROJECT-I03` Authored/Runtime Projection Split

- timeline sampling不再覆写 document objects；
- R3F/selectors消费 sampled projection；
- current transform/keyframe semantics显式化。

### `DIR-PROJECT-I04` Persistence Adapter

- only after I01-I03；
- storage-neutral tests first；
- browser adapter必须有quota/corrupt/stale fixture；
-不扩展到cloud/backend。

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
owner/session 子项已在 Batch 68 升级为 `OWNER_SESSION_FOCUSED_RUNTIME_PASS`：

1. 两个 source node 和两个 canvas 已证明 project 不串场；
2. open/switch/close、same-owner focus、duplicate reset 和 active delete close
   已有 typed/focused runtime；
3. session/runtime/capture sidecar exclusion 在 store integration 后仍成立；
4. focused verifier、`npm run check`、docs check 和实施台账通过。

整体 project/session authority 仍不能标记 complete，以下条件尚未满足：

1. authored document 在 seek/playback 后 fingerprint 不漂移；
2. inactive owner/source/canvas delete 有 tombstone/reachability reconciliation；
3. delayed capture/export 只写 captured canvas/source/generation；
4. duplicate deep clone/remap 与 resource policy 明确；
5. persistence adapter 有 corrupt/quota/stale fixture。
