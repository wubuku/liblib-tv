# Director Reliability Authority 静态审计

> 状态：`CURRENT_CLONE_STATIC_AUDIT`。
>
> 审计日期：2026-08-27。
>
> 审计基线：`a7bcf21`。
>
> 固定参考上游：`storyai-3d-director-desk@8c8bd36`。

## 1. 审计问题与证据边界

本审计回答三个问题：

1. 当前 Director 作者数据究竟由谁拥有，打开、切换、关闭和删除时发生什么；
2. 现有 85 个 store action 哪些是 UI/runtime 更新，哪些应成为语义 command；
3. 删除 object/group/camera/asset 时，哪些引用必须修复或保留。

证据分级：

| 级别 | 可回答 | 不可回答 |
|---|---|---|
| `CLONE_STATIC_FACT` | 当前代码字段、调用、引用和副作用 | 当前交互一定在所有浏览器正确 |
| `UPSTREAM_FACT` | 固定 StoryAI 的 schema、history、delete 和 persistence 做法 | LibTV 原站也采用相同做法 |
| `HISTORICAL_RECORDED_PASS` | 历史 verifier 在记录日期通过 | 当前 HEAD 仍通过 |
| `RECOMMENDATION` | 下一实现批次的 clone-owned 工程决策 | LibTV source-exact 产品事实 |
| `UNKNOWN` | 当前证据无法回答的问题 | 可以用上游或 clone 截图补齐 |

本批没有重新识别截图，也没有获得新的 authenticated LibTV Director 运行证据。

## 2. 当前 authority 拓扑

```text
React Flow source node
  -> uiStore.activeDirectorCanvasId + activeDirectorNodeId
  -> <DirectorDesk sourceNodeId>
  -> singleton useDirectorStore
       scene / objects / groups / timeline / captures / local library
  -> canvasStore.createDirectorCapture / createDirectorAnimationExport
       late-read canvasStore.activeCanvasId
```

当前存在两套不对称 owner：

| Authority | 当前身份 | 生命周期 |
|---|---|---|
| workspace surface | `activeDirectorCanvasId + activeDirectorNodeId` | 切 canvas、删 source node 时由 page reconciliation 关闭 |
| Director authoring state | `sourceNodeId` + 单例 store | `openSession` 只换 node ID，其余状态继续保留 |
| graph result destination | action 调用时的 `activeCanvasId + sourceId` | 没有 immutable captured canvas owner |
| local model catalog | 全局 localStorage key `liblib-tv-director-local-model-library-v1` | 不按 canvas/node/project 隔离 |

因此“surface 已正确关闭”不等于“项目状态已隔离”，也不等于“异步结果拥有稳定目的地”。

## 3. Store 面积与身份盘点

[`directorStore.ts`](../../../src/store/directorStore.ts) 当前声明：

- 19 个顶层状态字段；
- 85 个 action；
- 5 个默认 scene object；
- 1 个默认 camera；
- transform/camera/pose/group 四类 timeline track；
- object/group/camera/track/keyframe/path/anchor/capture/local asset/phone take
  等多套相互引用身份。

### 3.1 顶层状态字段

| 当前字段 | 当前角色 | 建议 authority |
|---|---|---|
| `sourceNodeId` | 当前 workspace source | session owner；不能单独作为 project identity |
| `scene` | 场景作者数据 | portable project |
| `objects` | 作者数据与 timeline sampled projection 混合 | portable authored objects + runtime sampled projection 必须拆开 |
| `groups` | 角色组合与 crowd 参数 | portable project |
| `selectedObjectId/Ids` | UI selection | session UI |
| `selectedGroupId` | UI selection | session UI |
| `activeCameraId` | capture/export camera 与视图选择 | portable project 的 active camera identity；session 可另有 preview camera |
| `viewMode` | 导演/机位视图 | session UI |
| `transformMode` | 变换工具 | session UI |
| `aspectRatio` | viewport/capture/export 默认比例 | 明确的 project output preference 或 session override；不能隐式两者兼任 |
| `showThirds` | viewport helper | session UI |
| `viewportPanelsCollapsed` | shell 布局 | session UI |
| `isCapturing` | screenshot runtime lock | runtime/transient |
| `captures` | data URL、camera provenance、graph result link | resource/projection；portable document 只存稳定 descriptor |
| `activeCaptureId` | viewer selection | session UI |
| `localModelLibrary` | data URL catalog | resource registry；不能嵌入 project bytes |
| `timeline` | authored tracks/path 与播放/UI/draft 混合 | 必须拆为 project、session 和 runtime 三部分 |
| `phoneVcam` | preference、baseline、recording、import result 混合 | preference/session/runtime/result 分层 |

### 3.2 稳定身份与引用

| 身份 | 生产位置 | 被引用位置 | 当前风险 |
|---|---|---|---|
| canvas ID | `canvasStore` | `uiStore.activeDirectorCanvasId` | Director store 不持有 |
| source node ID | React Flow node | `uiStore`、`DirectorDesk`、`directorStore.sourceNodeId`、result metadata | project 与 source node 仍是一对未声明关系 |
| project ID | 不存在 | 不存在 | 无法区分同一 node 的 document generation |
| schema version | 不存在 | 不存在 | 无 strict decode/migration |
| owner generation | 不存在 | 不存在 | async completion 无 stale owner token |
| object ID | fixture/Date.now actions | selection、group、camera relation、track、path | 无统一 delete closure |
| group ID | group/crowd actions | selection、group track | 无通用 delete command |
| camera object ID | object identity | `activeCameraId`、capture、phone vcam | 无 camera delete/fallback |
| local asset ID | local library import | object `libraryAssetId` | 删除会级联实例，但修复不完整 |
| track ID | timeline actions | selection、draft、phone import、preset record | 删除路径有局部修复 |
| keyframe ID | track | selection、camera preset generated IDs | 全局按 ID 删除，依赖跨 track 唯一性 |
| motion path ID | path | track、selection | path/track detach 已局部实现 |
| anchor ID | path | anchor/handle selection | 最低 2 anchor guard 已实现 |
| capture ID | capture action | active capture、sent result | 删除只影响 gallery，不处理 graph result |
| graph result node ID | `canvasStore` | capture `sentNodeId`、workspace close selection | graph node 后续删除不会反向清理 capture link |
| video object URL | recorder result | graph video node | 不在 Director store；lease/revoke authority 未统一 |

### 3.3 当前 ID 生成

大部分动态 identity 使用 `Date.now()`。这对单用户原型通常足够，但不满足：

- deterministic unit fixture；
- 同毫秒批量 command 的强唯一性证明；
- import/migration 后的 namespace；
- project duplicate 时的显式 ID remap；
- async result 与 owner generation 的关联。

下一实现不能只把现有 state 包进 JSON；必须先定义 ID namespace、decode collision
policy 和 duplicate remap。

## 4. 四层状态分离

### 4.1 Portable project document

建议进入 `DirectorProjectDocumentV1`：

```text
schemaVersion
projectId
owner { route, canvasId, sourceNodeId, generation }
scene
objects
groups
activeCameraId
timeline {
  duration
  loop
  autoKeyframe
  tracks
  motionPaths
}
outputPreferences {
  aspectRatio
}
resourceRefs
captureDescriptors
```

这里的 `objects` 必须是 authored baseline，不能是任意 playhead 时刻被采样后的对象。
`captureDescriptors` 只能保存稳定 locator、尺寸、时间和 provenance；无稳定 locator
时应明确为 session-only，而不是把 data URL 冒充 durable media。

### 4.2 Session UI

建议按 `projectId + sessionId` 管理：

```text
selectedObjectId / selectedObjectIds / selectedGroupId
viewMode / transformMode
showThirds / viewportPanelsCollapsed
timeline.currentTime / timeline.zoom / timeline.editorMode
selectedTrackId / selectedKeyframeId
selectedMotionPathId / anchorId / handle
activeCaptureId
open panels / export panel draft
```

session UI 默认不进入 project undo。若未来希望恢复布局，应存独立 session snapshot，
不能污染 portable project schema。

### 4.3 Runtime/transient

以下内容必须在 close/switch/generation change 时取消或重建：

```text
timeline.isPlaying
motionPathDraft
isCapturing
phone recording status/start/sample buffer/baseline
R3F refs / Three.js Object3D / renderer / controls
pointer capture / gesture baseline
MediaRecorder / render loop / pending request
export progress / error / request token
```

当前 `motionPathDraft` 位于 timeline，phone baseline 位于 store，export request 位于
`DirectorDesk` local state。位置不同不等于 owner 已明确；三者都需要 generation-bound
cancel/discard 规则。

### 4.4 Resource/projection

资源层至少区分：

```text
local bytes or File
session URL / data URL / object URL lease
stable asset descriptor
scene instance reference
capture/export result descriptor
React Flow graph projection
```

不得进入 portable project 的值：

- `File`、`Blob`、object URL；
- Three.js objects、materials、textures、renderer refs；
- pointer/native events；
- raw MediaRecorder；
- 未声明 durability 的 data URL；
- `sentNodeId` 这类当前 graph projection cache。

## 5. Lifecycle 静态审计

| 事件 | 当前行为 | 缺口 | 推荐 disposition |
|---|---|---|---|
| open node A | `openSession(A)`；保留已有 project | 首次与恢复不可区分 | load/create A owner document，创建新 session generation |
| close A | 只关闭 `uiStore` surface | authoring/runtime state 仍在单例 | cancel runtime，flush accepted project，释放 session lease |
| reopen A | 看到上次单例内容 | 不是按 A 恢复，只是碰巧保留 | 按 project registry 恢复 A |
| open node B | source ID 改为 B，A 内容继续存在 | cross-node project bleed | switch 前 flush A，decode/load/create B |
| switch canvas | page reconciliation 关闭 surface | store/project 仍属于旧 owner | close old generation；不得把旧 state 绑定新 canvas |
| delete source node | surface 被 reconciliation 关闭 | project/resource retention 未定义 | tombstone/delete/detach policy 必须显式 |
| duplicate source node | 普通 graph duplicate | 没有 Director document clone | clone document + remap IDs，或显式创建空 project |
| refresh page | scene/timeline 回到 fixture；local catalog 全局恢复 | project 不可恢复且 catalog 不隔离 | strict persisted envelope + quota/error policy |
| async capture/export complete | action late-read当前 `activeCanvasId` | destination 可漂移；source 可能 stale | 捕获 immutable owner + generation，commit 前 freshness guard |

`uiStore` 的 reconciliation 是正确的 surface safety island，应保留；它不能替代 project
lifecycle。下一实现必须让 UI owner 与 document owner 能相互校验，而不是删除前者。

## 6. Mutation 与 history 审计

### 6.1 当前 mutation 入口

85 个 action 可以按目标语义分为五类：

| 类别 | 当前代表 action | 未来 history |
|---|---|---|
| session/transient | selection、view/transform mode、playing/time、panel、capture busy | zero Director project history |
| gesture update | transform、curve handle、path anchor/handle、free draw、phone pose | pointermove/onChange 阶段 zero entry |
| gesture commit | TransformControls mouse-up、numeric edit commit、curve/path drag end | 一次有效 gesture -> one entry |
| semantic command | add/group/ungroup、rename、toggle、track/keyframe/path、preset | valid changed command -> one entry |
| async result | capture、phone take import、video export graph return | project 与 graph 各自按 owner/transaction 记账 |

当前 action 没有统一 disposition。很多 invalid input 返回原 state，但另一些 action
即使目标不存在也会创建新的 array/object wrapper。若直接在 Zustand `set` 外包一层
snapshot，会把 invalid/noop 误记为 history。

### 6.2 已证的 entry 粒度问题

| Surface | 当前写入 | 风险 |
|---|---|---|
| object TransformControls | mouse-up 后 9 次 `updateObjectTransform` + 1 次 keyframe record | 一个拖拽会形成多 entry |
| object Inspector number | 每个 `onChange` 更新 transform，再 record keyframe | 输入中间态和自动帧爆栈 |
| group Inspector number | 每次 change 更新全组并 record | 多对象快照成本高 |
| pose slider | 每个 change 更新 rig 并 upsert pose keyframe | 连续 slider drag 爆栈 |
| curve handle | pointermove 直接 `setTrackSpeedCurveControl` | 高频 mutation |
| path control | TransformControls mouse-up 单 action | 粒度较好，但缺 gesture baseline/history |
| free pencil/pen | 每个 pointer event 更新 draft | draft 应是 transient；finish 才是 command |
| phone vcam | pose/sample/time 高频更新；take import 创建 camera+track | import 应 one entry，录制过程不进 project history |
| screenshot/video return | `canvasStore` 各自 push 普通 graph history | 必须继续与 Director domain history 分开 |

### 6.3 command contract 最低要求

每个 future command 必须返回：

```text
status: committed | noop | rejected | stale
reason: stable reason code
projectDelta
selectionResult
historyDisposition
resourceDisposition
graphProjectionDisposition
```

并满足：

1. invalid/rejected/stale/noop -> zero project mutation、zero history；
2. one semantic action或one completed gesture -> one Director history entry；
3. undo/redo 只恢复 portable authored project，不恢复 playback、pointer、recorder；
4. graph result return 仍是普通 canvas graph 的一步 history；
5. undo graph result 不重放 screenshot/video side effect；
6. new project commit 清空 redo；session-only change不清空 redo；
7. asynchronous commit 必须比较 project ID、owner generation 和 source existence。

## 7. Reference graph 与删除闭包

### 7.1 当前引用图

```text
project owner -> source node
group -> characterIds[] -> object
activeCameraId -> camera object
camera.lookAtObjectId -> object
camera.followTargetId -> object
track.objectId -> object or group
group track.groupId -> group
track.motionPathId -> motion path
motionPath.objectId -> object
selection IDs -> object/group/track/keyframe/path/anchor/capture
camera preset.application -> track + generated keyframes
capture.cameraId -> camera
capture.sentNodeId -> graph result node
local library item -> object.libraryAssetId
phoneVcam.importedCameraId/importedTrackId -> camera/track
```

其中 capture camera/result identity 可作为 provenance 弱引用保留；其余参与运行解析的
引用必须在 commit 后满足完整性。

### 7.2 当前删除实现

| 删除入口 | 当前修复 | 当前缺口 |
|---|---|---|
| ungroup | 删除 group 和 group track，恢复成员选择 | 没有统一 command/history；未来 group path 扩展需闭包 |
| remove local asset | 删除 catalog、实例 object、实例 tracks/paths 和部分 selection | 不修复 camera look-at/follow、capture/result、project resource lease |
| remove track | 删除 track 与绑定 path，修复 track/path selection/draft | phone imported track、preset application 引用未清理 |
| delete keyframe | 从所有 track 按 ID filter，清 selection | preset generated IDs 未修复；无最小 keyframe policy |
| delete path | track detach，删除 path 和 path selection/draft | 缺 history/resource outcome |
| delete anchor | 保留至少 2 个 anchor，选择邻近 anchor | 缺 one-entry history |
| remove/clear capture | 删除 gallery record | graph result继续存在；该 retain 行为未正式声明 |
| scene object delete | 不存在 | group/track/path/camera relation/selection 全部未定义 |
| camera delete | 不存在 | active fallback、view mode、capture/phone/preset 未定义 |

### 7.3 推荐 delete disposition

| 被删实体 | 强引用处理 | 弱引用/provenance | fallback |
|---|---|---|---|
| character/prop | 从 group detach；删 owned tracks/paths；camera relation 转 manual | 历史 capture 可保留 name/ID snapshot | selection 选邻近对象或 scene |
| camera | 删 camera tracks/paths；清 phone/preset runtime | capture/export provenance 保留 snapshot | 选择首个 surviving camera；无 camera 时 block 或同 transaction 创建默认 camera |
| group | 默认 ungroup/detach，不删成员；删 group track/path | 无 | selection 回成员 |
| local asset | 默认先检查 instance refs；明确 cascade 或 block | import audit 可保留 metadata | lease reachability 为零后释放 |
| track | 删 owned path；清 preset/imported track ref | 无 | 选择邻近 track |
| path | detach 所有引用它的 track，再删 path | 无 | 保留 track |
| capture | gallery descriptor 可删；graph node不是隐式级联 | graph node metadata保留 | active capture选邻近项 |
| source graph node | 关闭 session；project 按产品策略 tombstone/delete | exported graph results可独立保留 | 不重新绑定到 active canvas |

所有 delete 必须先构建 full plan，再一次 commit。不能边 filter 边触发 resource revoke。

## 8. 当前主要 failure modes

| ID | Failure mode | 严重度 |
|---|---|---|
| `DIR-FAIL-01` | 打开第二个 Director node 继承第一个 node 的完整 scene/timeline/capture | P0 |
| `DIR-FAIL-02` | timeline seek/playback 把 sampled 值写回 authored `objects`，document/history 边界不清 | P0 |
| `DIR-FAIL-03` | capture/export action late-read active canvas，缺 immutable destination owner | P0 |
| `DIR-FAIL-04` | object/camera 无通用删除，复杂引用只能继续累积 | P0 |
| `DIR-FAIL-05` | 高频输入直接 mutation，未来 naive undo 会产生多 entry 或中间态 | P0 |
| `DIR-FAIL-06` | 无 schema/version/strict decode/migration，无法可靠恢复或复制 project | P0 |
| `DIR-FAIL-07` | local model data URL 用全局 key 持久化，quota、owner、cleanup 不透明 | P1 |
| `DIR-FAIL-08` | capture sentNodeId 与 graph node 生命周期未双向校验 | P1 |
| `DIR-FAIL-09` | Date.now ID 无 namespace/remap/import collision policy | P1 |
| `DIR-FAIL-10` | 17 个历史 verifier 没有 current manifest，无法说明当前 HEAD 成熟度 | P1 |

## 9. StoryAI 可借与不可借

可借的方法：

- `DirectorProject.version` 和 project/assets/objects/cameras 分层；
- scoped persistence key；
- `commitMutation`、undo batch 和 copy/paste 的 transaction 思路；
- 删除 camera target、linked camera 和 asset instance 的 reference repair；
- runtime internal state 与 project state 分离。

不可直接复制：

- 浅层 `isDirectorProjectShape` 或 `JSON.parse(...) as DirectorProject`；
- 把 selection/panel/view state 与 project 一起持久化；
- 只有 undo 没有 redo；
- data URL 长期写 localStorage；
- StoryAI 的 camera shot 双实体、CSS、协议名和视觉数字；
- 上游 action surface 对当前 typed timeline/path/phone/export 的缺失处理。

Open Canvas 提供 transaction、identity、async convergence、resource lease 和 verifier
治理方法；它同样不是 LibTV Director 产品行为证据。

## 10. 实施解锁顺序

本审计支持以下顺序：

1. `DirectorProjectDocumentV1` 纯 schema、strict decoder、migration、owner key；
2. singleton store 内先建立按 owner 的 project registry/open-switch-close authority；
3. 分离 authored project 与 sampled runtime projection；
4. typed command result + history past/future + gesture transaction；
5. object/camera/reference-aware delete；
6. current verifier gate；
7. 之后才进入真实 mesh/panorama/multi-camera。

第一代码 slice 不应同时重写 3,800 行 store。最小可审查边界是：

```text
schema/types + pure decoder/migration
project registry/open-switch-close
focused store tests
one low-cost Director runtime verifier
```

history/delete 作为后续独立 slice，建立在稳定 project identity 之上。

## 11. 审计结论

当前 Director 的功能纵深已经足够，可靠性风险也已经具体化。最高价值问题不是缺少
更多面板，而是 authoring data 没有 document owner，runtime projection 与 authored
object 混合，复杂 mutation 没有 command/history authority，删除没有完整引用闭包。

这些结论来自 clone 静态代码和固定上游方法比较，不是 LibTV source-exact 声明。
下一步应据此建立两份正式合同和 current verifier manifest，再选择最小实现批次。
