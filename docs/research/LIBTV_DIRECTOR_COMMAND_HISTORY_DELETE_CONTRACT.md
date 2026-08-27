# LibTV Director Command, History And Delete Contract

> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` /
> `HISTORY_FOCUSED_PASS` / `POINTER_LIFECYCLE_FOCUSED_PASS` /
> `REFERENCE_DELETE_FOCUSED_PASS` / `ASYNC_AUTHORITY_FOCUSED_PASS` /
> `PERSISTENCE_FOCUSED_PASS` / `CLIPBOARD_REMAP_FOCUSED_PASS` /
> `SOURCE_PARITY_UNKNOWN_OR_PARTIAL`.
>
> Scope: Director project semantic command、gesture transaction、undo/redo、
> copy/paste、reference-aware object/group/camera/track/path/capture/resource delete，
> 以及普通 canvas graph history 的边界。
>
> Evidence baseline:
> [`liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md`](liblib-canvas-batch66-2026-08-27/STATIC_AUDIT_2026-08-27.md)，
> [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)，
> clone Batch 70-75 implementation，StoryAI `8c8bd36`。
>
> Authorization boundary: 本文是设计合同。它不授权一次性包装 85 个 action、
> 复制上游 store、修改 source fixture 或把 clone defaults称为LibTV source行为。

## 1. Contract Objective

当前 Director 有 85 个 store action，涵盖 object/group/camera/pose/timeline/path/
capture/local asset/phone vcam。mutation 已经形成复杂引用图，却没有共同 command
outcome、domain undo/redo 或 object/camera delete。

本合同建立：

```text
UI intent
  -> typed command proposal
  -> current project/session validation
  -> reference-aware full plan
  -> normalized semantic equality
  -> one project commit or zero mutation
  -> one history entry or declared zero entry
  -> session/runtime/resource/graph outcome projection
```

核心规则：

> 一个完成的用户语义动作最多产生一个 Director project history entry。无效、
> noop、rejected、stale、cancelled 和 pointermove 中间态产生零 entry。

## 2. Evidence Boundary

### 2.1 Current clone facts

- object TransformControls mouse-up执行9次字段写入和一次keyframe record；
- Inspector numeric input每次 `onChange` 写 object/group/path/camera并可能record；
- pose slider和curve handle在连续输入阶段直接mutation；
- free path draft每个pointer event更新store，finish才建立正式path；
- Batch 72 已将 object/group/camera/track/path/capture/resource 删除统一到
  `deleteDirectorEntity`；planner 在写入前计算 closure，并以 strict V1 post-state
  gate 保证 accepted one-commit 或 rejected zero-mutation；
- Batch 73 已将 capture/export/phone result completion 置于 typed async
  authority；stale/invalid/duplicate completion 不产生 graph/history side effect，
  export resource 只 transfer 或 release 一次；
- Batch 75 已将 session clipboard 置于 typed portable packet authority；copy
  不修改 document/history，paste 对 object/group/track/path/keyframe/anchor
  two-pass remap，内部 camera refs 映射、外部 refs detach/freeze，stable resource
  只 exact alias，accepted paste 恰好一条 history；
- camera relation、active camera、group membership、track/path reciprocal refs、
  capture provenance、selection/runtime draft 和 local resource block/cascade 已有
  明确 repair policy；
- screenshot/video graph return各自在普通canvas push一步history；
- Batch 70 已提供 Director project-local `past/future` 和 typed command result，
  Batch 71 已补齐 focused pointer lifecycle，Batch 72 已补齐 reference-aware
  delete；Batch 75 已关闭同 project copy/paste identity-remap focused slice；
  所有旧 action 的统一 command 化仍未完成。

### 2.1.1 Batch 70 current implementation boundary

Batch 70 已将 `DIR-CMD-I01` command kernel 和 `DIR-CMD-I02`
project-local history 落地，并以 focused runtime verifier 记录：

- semantic document mutation 自动生成 bounded history entry；
- same-value、invalid-value、missing-target、cancel 和 stale 路径为零 entry；
- undo/redo、redo future truncation、project A/B 隔离和 close/reopen continuity
  只作用于 Director portable document；
- object/group TransformControls 与 speed-curve handle 已接入真实
  begin/commit gesture adapter。

`DIR-CMD-I03` 的 Inspector numeric input、pose slider/control、motion-path
anchor/Bezier handle、path transform 和 free-path draft 已由 Batch 71 收口
pointerup、blur、Escape、pointercancel、stale、no-op 和 cancel 的提交边界；
当前仍需把所有旧 action 统一迁移为 typed command。

### 2.2 StoryAI facts

固定上游提供：

- `commitMutation` + undo snapshot；
- `beginUndoBatch/endUndoBatch`；
- copy/paste ID remap；
- object/camera/asset删除的部分引用修复。

保留反例：

- 无redo；
- snapshot包含UI state；
- shallow validation；
-不覆盖当前timeline/group/path/phone/export引用；
- mutation wrapper仍可能依赖object identity判断noop；
-上游camera/object模型不等于clone。

### 2.3 Source unknown

未证实 LibTV source：

- undo/redo control与shortcut；
-哪些Inspector change live-preview、blur commit或pointer-up commit；
-删除对象、最后机位、capture和asset的exact交互；
- copy/paste；
- history limit、selection restoration和feedback copy。

本合同只规定数据完整性与clone correctness floor。

## 3. Authority Composition

| Authority | 本合同拥有 | 委托 |
|---|---|---|
| project identity/document | command读取和commit目标 | [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md) |
| foreground key routing | Director undo/redo/delete是否收到event | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) |
| outcome surface | reason、owner、retry/announcement | [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) |
| resource release | delete plan中的lease diagnostics | [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) |
| graph return | ordinary canvas node/edge/history | canvas graph transaction authority |
| async freshness | capture/export/phone result generation | [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) |

Director project history 不能调用普通 `canvasStore.undo/redo`，普通 graph undo也不能
还原 Director project。

## 4. Command Vocabulary

### 4.1 Disposition

```ts
type DirectorCommandDisposition =
  | "COMMITTED"
  | "NOOP"
  | "REJECTED"
  | "STALE"
  | "CONFLICT"
  | "UNKNOWN";
```

### 4.2 Command result

```ts
interface DirectorCommandResult {
  commandId: string;
  projectId: string;
  generation: number;
  disposition: DirectorCommandDisposition;
  reason: string | null;
  projectChanged: boolean;
  historyEntries: 0 | 1;
  selectionResult: DirectorSelectionResult | null;
  resourceEffects: DirectorResourceEffect[];
  graphEffects: DirectorGraphEffect[];
}
```

Stable reason families：

```text
DIRECTOR_OWNER_STALE
DIRECTOR_PROJECT_MISSING
DIRECTOR_TARGET_MISSING
DIRECTOR_TARGET_LOCKED
DIRECTOR_INVALID_VALUE
DIRECTOR_REFERENCE_INVALID
DIRECTOR_COMMAND_NO_CHANGE
DIRECTOR_DELETE_BLOCKED
DIRECTOR_LAST_CAMERA_REQUIRED
DIRECTOR_RESOURCE_IN_USE
DIRECTOR_GESTURE_NOT_ACTIVE
DIRECTOR_HISTORY_EMPTY
DIRECTOR_HISTORY_CONFLICT
DIRECTOR_POLICY_UNKNOWN
```

UI copy不能作为reason identity。

## 5. Command Classes

| Class | Examples | Project history |
|---|---|---|
| `SESSION_UI` | select、view/transform mode、thirds、panel、timeline zoom/editor mode | 0 |
| `RUNTIME_CONTROL` | play/pause/seek、capture busy、phone live pose、draft pointer update | 0 |
| `GESTURE_BEGIN` | transform/curve/path/slider/numeric edit开始 | 0，捕获baseline |
| `GESTURE_UPDATE` | pointermove/input live preview | 0，更新runtime preview或coalesced draft |
| `GESTURE_COMMIT` | pointerup/blur/Enter/profile Apply | semantic changed时1 |
| `SEMANTIC_COMMAND` | add/group/rename/toggle/keyframe/path/preset/delete | changed时1 |
| `ASYNC_ACCEPT` | phone take import、capture descriptor materialize | accepted project result时0/1按profile |
| `GRAPH_PROJECTION` | screenshot/video node回流 | Director 0；ordinary graph 1 |
| `PERSISTENCE_STATUS` | save success/fail | 0 |

### 5.1 Current action routing

后续 adapter 至少按以下簇迁移：

| Action cluster | Future class |
|---|---|
| `select*`、`setViewMode`、`setTransformMode`、panel/thirds | `SESSION_UI` |
| timeline time/play/advance/zoom/editor selection | `RUNTIME_CONTROL` / `SESSION_UI` |
| scene/object/group/camera name/color/toggle | `SEMANTIC_COMMAND` 或 field gesture commit |
| object/group transform | transform gesture |
| pose control | slider gesture；preset是semantic command |
| curve control | curve gesture；preset是semantic command |
| path draft append/handle | runtime draft gesture；finish是semantic commit |
| path anchor/transform | gesture commit或semantic field command |
| add/remove track/keyframe/path | semantic command |
| phone live pose/sample/time | runtime；import take是semantic command |
| capture select/view | session；capture add/remove按resource profile |
| local library hydrate | resource/session；add/remove asset是resource command |

迁移不要求一次删掉所有旧 action。允许 legacy adapter调用typed planner，但任何新
mutation不得新增绕过command authority的direct writer。

## 6. Semantic Equality And No-Op

每个 command先规范化后比较：

- finite number与范围clamp；
- tuple逐值比较；
- color/name按profile normalization；
- arrays按稳定顺序/identity；
- rig/keyframe/path深比较；
- reference set比较；
- NaN/Infinity直接reject；
- missing target直接reject或noop，由command定义；
-同值patch为`NOOP`。

禁止用“Zustand返回了新object”判断changed。当前一些map/spread action即使目标缺失
也会生成新wrapper，这不能进入history。

## 7. Director History

### 7.1 State

```ts
interface DirectorHistoryState {
  past: DirectorHistoryEntry[];
  future: DirectorHistoryEntry[];
  activeGesture: DirectorGestureTransaction | null;
  limit: number;
}

interface DirectorHistoryEntry {
  entryId: string;
  commandId: string;
  commandKind: string;
  projectId: string;
  before: DirectorProjectDocumentV1;
  after: DirectorProjectDocumentV1;
  committedAt: string;
}
```

实现可使用snapshot、delta或inverse command。observable contract是：

- exact before/after document；
- project-local ordering；
- redo；
- one gesture one entry；
- invalid/noop zero entry；
- session/runtime/resource object不进snapshot；
-新commit清future；
-limit deterministic且不会破坏present。

### 7.2 Undo/redo

Undo：

1. Director foreground且无更高优先级editable/local tool；
2. validate current project/history entry identity；
3. cancel playback和active project gesture；
4. restore previous portable document；
5. reconcile selection到surviving IDs；
6. rebuild sampled runtime projection；
7. move entry past -> future；
8. zero ordinary graph history。

Redo相反。

History restore不：

- restart playback/recording/export；
- recreate/revoke external resource side effects；
- reopen capture viewer/panel；
- write普通canvas graph；
- restore stale focus DOM；
-跨project消费entry。

### 7.3 History limit

第一实现可使用 bounded entry count，但必须预留byte estimate。含capture data URL或
large embedded resource的document不能用完整snapshot无限复制；正确修复是把bytes移出
document，而不是提高limit。

## 8. Gesture Transaction

### 8.1 Lifecycle

```text
IDLE
  -> BEGIN(capture project fingerprint + target baseline)
  -> UPDATE(runtime preview/coalesced draft)*
  -> COMMIT(normalize + compare + full command)
  -> IDLE

or CANCEL -> restore baseline/runtime -> IDLE
```

gesture identity包含：

```text
gestureId
projectId
generation
target identity
field scope
baseline fingerprint/value
startedAt
```

### 8.2 Surface rules

| Surface | Begin | Update | Commit |
|---|---|---|---|
| R3F TransformControls | drag start | Three runtime object preview | mouse/pointer up一次object/group command |
| Inspector numeric | focus/pointerdown | field draft/live preview | blur/Enter/step endpoint按profile一次 |
| pose slider | pointerdown/keyboard start | rig preview | pointerup/keyboard idle一次 |
| curve handle | pointerdown | control point preview | pointerup一次 |
| path anchor/handle | transform start | path preview | pointerup一次 |
| free pencil/pen | pointerdown | transient draft anchors | finish一次create/replace path |
| phone live vcam | record start | runtime samples | import take一次camera+track command |

Pointer cancel、owner switch、Escape、unmount必须明确cancel或commit，不能遗留
`activeGesture`。

### 8.3 Current TransformControls correction

未来不能在mouse-up循环调用9个field action。应读取完整transform并提交：

```ts
UPDATE_OBJECT_TRANSFORM {
  objectId,
  before,
  after,
  keyframePolicy
}
```

object transform与auto-keyframe upsert是同一个command plan和history entry。

## 9. Reference Registry

### 9.1 Strong references

必须解析且在commit后有效：

| Ref | Target |
|---|---|
| group `characterIds[]` | character object |
| `activeCameraId` | camera object |
| camera `lookAtObjectId` | allowed object |
| camera `followTargetId` | allowed object |
| track `objectId` | object or group by track kind |
| group track `groupId` | group |
| track `motionPathId` | path |
| path `objectId` | track/object |
| selected session IDs | current project entities |
| phone imported camera/track | current project entities while session live |
| preset application track/generated keyframes | current project entities |

### 9.2 Weak provenance

可以在target删除后保留snapshot identity，但不能继续用于运行解析：

- capture `cameraId/cameraName`；
- capture `sentNodeId`；
- export camera/project/result IDs；
- deleted resource display metadata；
- tombstoned source node ID。

Weak ref必须有显式provenance status，例如 `RESOLVED/UNRESOLVED/TOMBSTONED`，
不能继续伪装strong ref。

### 9.3 Inverse index

Delete/copy/import validation使用typed registry构建inverse index。禁止：

- 搜索所有以 `Id` 结尾字段；
- 依赖 ID prefix；
- 只删incident timeline item；
- 边删边发现引用。

## 10. Delete Planner

### 10.1 Commands

```ts
type DirectorDeleteCommand =
  | { kind: "DELETE_OBJECT"; objectId: string }
  | { kind: "DELETE_GROUP"; groupId: string; memberPolicy: "UNGROUP" | "CASCADE" }
  | { kind: "DELETE_CAMERA"; cameraId: string }
  | { kind: "DELETE_TRACK"; trackId: string }
  | { kind: "DELETE_KEYFRAME"; trackId: string; keyframeId: string }
  | { kind: "DELETE_MOTION_PATH"; pathId: string }
  | { kind: "DELETE_MOTION_ANCHOR"; pathId: string; anchorId: string }
  | { kind: "DELETE_CAPTURE"; captureId: string }
  | { kind: "DELETE_LOCAL_ASSET"; assetId: string; instancePolicy: "BLOCK" | "CASCADE" };
```

### 10.2 Plan

```ts
interface DirectorDeletePlan {
  disposition: "READY" | "NOOP" | "REJECTED" | "UNKNOWN";
  reason: string | null;
  deleteObjectIds: string[];
  deleteGroupIds: string[];
  deleteTrackIds: string[];
  deleteKeyframeIds: string[];
  deletePathIds: string[];
  deleteCaptureIds: string[];
  deleteResourceIds: string[];
  objectPatches: DirectorObjectPatch[];
  groupPatches: DirectorGroupPatch[];
  trackPatches: DirectorTrackPatch[];
  capturePatches: DirectorCapturePatch[];
  selectionResult: DirectorSelectionResult;
  runtimeInvalidations: DirectorRuntimeInvalidation[];
  resourceEffects: DirectorResourceEffect[];
  historyEntries: 0 | 1;
}
```

Planner是pure function。只有完整post-state通过integrity validation后才能commit。

## 11. Delete Policy Matrix

### 11.1 Object

删除 character/prop：

1. 从所有group member detach；
2. 空group默认保留还是删除必须由command policy声明；
3. 删除object-owned transform/pose/camera track；
4. 删除这些track绑定path；
5. 删除object-owned path；
6. 所有camera look-at/follow指向该object时，freeze当前resolved target，切manual并清ID；
7. 清selection/path/track/keyframe references；
8. preset/phone runtime指向该object时invalidate；
9. object asset instance ref decrement；
10. capture/export provenance不自动删。

Accepted -> one history entry。

### 11.2 Camera

camera是object的specialized delete：

-执行object closure；
- active camera选择deterministic surviving camera；
- camera view切到fallback；
- phone live/recording/import refs清理；
- camera preset application清理；
- camera captures保留snapshot provenance或按explicit command删除；
-若无surviving camera：
  - clone correctness默认`REJECTED / DIRECTOR_LAST_CAMERA_REQUIRED`；
  -未来可在同一transaction创建default camera；
  -不能留下invalid activeCameraId。

最后机位exact UX是source/product unknown。

### 11.3 Group

默认显式区分：

| Intent | Members | Group track/path | History |
|---|---|---|---|
| `UNGROUP` | 保留对象 | 删除group track/path | 1 |
| `CASCADE` | 逐object closure删除 | 删除 | 1 |

UI 中不能把两种 intent都标成模糊“删除”。

### 11.4 Track/keyframe/path/anchor

- track delete同时删除owned path；
- track delete清phone imported track和preset application；
- keyframe delete必须指定track + keyframe，不能只靠全局ID filter；
-删除preset-generated keyframe后，preset application record重算或清空；
- path delete先detach所有track；
- anchor delete保持path有效最小数量；
- closed path降到不足3点时需显式open或reject；
-每个accepted command 1 history entry。

### 11.5 Capture

Capture gallery descriptor与graph result分开：

- delete capture默认不删除已发送graph node；
- `sentNodeId`变成historical provenance或移除projection cache；
-删除graph node默认不删除capture；
-若capture只持有session resource lease，删除可release；
-stable asset reference按registry decrement；
-bulk clear是一个command/history entry，不是N次循环。

### 11.6 Local asset

两种明确策略：

| Policy | Behavior |
|---|---|
| `BLOCK` | 有scene instance时拒绝，提示引用数量 |
| `CASCADE` | 删除全部instance，并对每个instance执行完整object closure |

当前 runtime相当于不完整`CASCADE`。未来不能只删object/track/path而遗漏camera relation、
selection、history、lease和storage outcome。

Resource bytes只有reachability为零且resource authority确认exclusive时释放。删除
storage descriptor失败不能回滚已提交project，除非command设计为真正原子storage
transaction；默认应返回project committed + cleanup failed的typed outcome。

## 12. Copy/Paste Contract

Copy/paste排在delete/history之后，但identity规则现在固定：

1. copy读取portable project entities，不复制session/runtime；
2. selected group可选择group closure；policy必须具名；
3. object-local tracks/paths和internal refs进入clipboard packet；
4. external camera relation默认detach/freeze，或由policy明确保留；
5. paste分配new IDs并two-pass remap；
6. resource stable ref alias；session/local bytes无portable lease时block；
7. paste selection指向new entities；
8. accepted paste one history entry；
9. no valid clipboard zero entry；
10.不得复制capture `sentNodeId`成live graph link。

StoryAI copy/paste只提供ID map方法，不提供当前typed timeline closure。

### 12.1 Batch 75 clone implementation

当前 clone 的 copy/paste observable contract：

- clipboard packet 只存在于当前 browser session，并绑定 `projectId`；
- selected group 复制完整 member closure；普通 multi-selection 不隐式扩展 group；
- packet 包含 object-local tracks/paths 和所需 stable resource descriptors；
- object/group/track/path/keyframe/anchor 全部分配新 ID；
- internal camera look-at/follow references remap，external references detach 并冻结
  当前 target/transform；
- repeated paste 使用 `0.6 * ordinal` 的 X/Z deterministic offset；
- stable resource 只在目标 document 已存在完全一致 descriptor 时 alias；
- missing/conflicting resource、cross-project、empty/invalid packet 和 allocation
  failure 全部 zero mutation；
- accepted paste 通过 canonical document/history/persistence authority 一次提交；
- clipboard、paste ordinal、capture、bytes、`sentNodeId`、selection UI、runtime、
  history/persistence metadata 不进入 packet 或 durable envelope；
- editable、IME、active gesture、busy 和 capture viewer 优先于 Director shortcut；
- 没有 source evidence 时不新增 visible clipboard toolbar/context menu/feedback。

该实现是 clone correctness floor，不证明 LibTV source 的 shortcut、placement、
feedback、cross-project 或 system clipboard 行为。

## 13. Async And Graph Boundaries

### 13.1 Phone take

recording samples属于runtime。`IMPORT_PHONE_TAKE`：

-冻结validated sample set；
-创建camera + camera track + keyframes；
-restore/commit baseline policy明确；
-active camera/selection/session同步；
-one project history entry；
-invalid/insufficient samples zero entry；
-owner/generation stale zero entry。

### 13.2 Capture

Capture生成可分：

- R3F screenshot side effect；
- Director capture descriptor commit；
- ordinary graph result projection。

这三步的history不能混成一个全局undo。若capture descriptor保存进project，可产生一个
Director entry；graph send另产生普通graph entry。重复send按result identity noop。

### 13.3 Video export

视频录制本身不进入project history。完成后：

- resource owner接受object URL；
- ordinary graph result intent使用immutable destination；
-graph accepted one history；
-Director project zero history，除非另建stable export descriptor command；
-失败/stale时exact release且zero history。

## 14. Integrity Invariants

每个 accepted command 后必须满足：

1. document通过project contract strict validation；
2. strong reference全部解析；
3. active camera有效；
4. selection是current project实体子集；
5. timeline track/path/object对应；
6. group membership合法；
7. camera relation不指向deleted/self/invalid target；
8. preset/phone runtime refs可解析或已清理；
9. one command history cardinality符合声明；
10. resource effect只由resource owner执行；
11. ordinary graph state/history除graph projection command外不变；
12. FrameOS store不变。

Reject/noop/stale/unknown：

```text
project unchanged
history unchanged
selection unchanged
runtime unchanged except allowed feedback/gesture cleanup
ordinary graph unchanged
resource unchanged except exact cleanup of unaccepted temporary lease
```

## 15. Shortcut And Focus Routing

Director foreground context默认：

| Key | Priority |
|---|---|
| editable native undo/redo | browser/native editor first |
| active path/curve/local gesture undo | local tool if declared |
| Director project undo/redo | Director command authority |
| ordinary canvas undo/redo | blocked while Director foreground |
| Delete/Backspace | editable text first；otherwise Director selected entity if source/product/UI policy exposes delete |
| Escape | cancel top gesture/panel/viewer first，then close workspace |

一个event最多由一个context消费。Batch 50背景shortcut guard继续保留。

## 16. Fixture And Verifier

共享 fixture：`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`。

Command corpus：

```text
same-value/no-target/non-finite/locked/stale commands
object with group + transform/pose track + path
camera looking/following deleted target
active camera with captures + phone/preset refs
local asset with multiple instances and camera relation
group ungroup/cascade
track/path/keyframe/anchor edge cases
gesture begin/update/commit/cancel
history past/future and project switch
capture/video graph projection
```

`LIBTV-VR-024` minimum scenarios：

1. transform drag -> one Director entry；
2. numeric/slider/curve repeated update -> one entry；
3. invalid/noop -> zero entry；
4. undo/redo exact document round-trip；
5. object delete repairs group/track/path/camera refs；
6. last camera delete rejected or valid same-transaction fallback；
7. local asset cascade完整或block；
8. capture delete不误删graph result；
9. Director undo不改ordinary graph；
10. graph undo不改Director project；
11. source/canvas switch使active gesture和late command stale；
12. all integrity/reference assertions pass。

## 17. Implementation Slices

### `DIR-CMD-I01` Command Kernel

- [x] typed result/reason；
- [x] pure semantic equality；
- [x] project snapshot commit；
- [x] 先迁移一个低风险 command 簇验证 adapter；
- [x] no UI rewrite beyond the focused adapters。

### `DIR-CMD-I02` History Past/Future

- [x] project-local history；
- [x] undo/redo；
- [x] foreground routing；
- [x] session/runtime reconciliation；
- [x] 不实现 delete/copy。

### `DIR-CMD-I03` Gesture Coalescing

- [x] object/group transform；
- [x] numeric/pose/curve/path 全部统一；
- [x] free draw finish；
- [x] 已覆盖的 gesture 满足 one gesture one entry；
- [x] 所有当前纳入 Batch 71 的 Director pointer lifecycle 满足 one gesture one entry。

### `DIR-CMD-I04` Object/Camera Delete

- [x] typed reference registry/inverse index；
- [x] full planner；
- [x] last camera policy；
- [x] focused integrity tests。

### `DIR-CMD-I05` Remaining Delete And Copy/Paste

- [x] group/track/path/capture/local asset；
- [x] resource diagnostics；
- [x] clipboard packet/remap；
- [x] prior command/history/pointer/delete slices are stable enough for the remaining copy/paste slice。

### `DIR-CMD-I06` Async Result Authority

- [x] capture/export/phone operation descriptor；
- [x] owner/session/generation and source/request fingerprint；
- [x] retry attempt supersession and terminal conflict handling；
- [x] duplicate/stale/invalid completion disposition；
- [x] resource transfer/release exactly once；
- [ ] ordinary canvas async ingress；
- [ ] durable result envelope/persistence。

每个 slice 独立commit/push和current verifier update。不得把所有85个action在一个提交中
批量机械包装。

## 18. Non-Goals

- 不从StoryAI复制store文件；
-不把CSS或UI按钮作为history authority；
-不实现source-unconfirmed destructive UX；
-不让Director undo恢复普通canvas graph；
-不把resource delete等同project ref delete；
-不在history批次接入真实mesh/panorama/multi-camera；
-不以17个历史visual verifier替代command unit/integrity tests。

## 19. Completion Criteria

Runtime从fragmented升级需要：

1. typed command result和stable reason；
2. project-local past/future；
3.至少transform、numeric、pose或curve三类gesture证明one-entry；
4. invalid/noop/stale zero-entry；
5. object/camera delete完整引用修复；
6. Director/graph history隔离；
7. integrity checker覆盖全部strong ref；
8. focused unit/runtime verifier通过；
9. current manifest、verification ledger和coverage更新；
10. `npm run check`、docs check、commit/push完成。
