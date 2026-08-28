# Batch 79 计划：Director Whole-Project Duplicate

> **状态**：`WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS`
>
> **日期**：2026-08-28
>
> **目标**：为普通 LibTV canvas duplicate 建立一个不会丢失或串用
> Director project 的整批复制事务。

## 1. 为什么现在做

Batch 67-78 已经逐层补齐了 Director 的 portable document、owner/session、
authored/runtime、command/history、pointer lifecycle、reference-aware delete、
async authority、browser-local persistence、same-project clipboard remap 和
owner reachability。剩下的高价值断点不是另一个孤立的 Director 控件，而是
这些能力在 `duplicateCanvas` 这一跨域生命周期动作上的组合。

当前行为形成了一个容易误解的落差：

```text
duplicateCanvas
  -> 新 canvas + 新 graph node/edge/parent ID
  -> 新 Director owner
  -> 新 Director project reset
  -> 原 Director authored scene/timeline/path/capture 不随副本复制
```

这对 Director 用户是实质性数据语义问题。用户复制一个包含导演台节点的
画布，通常期望复制场景、角色、机位、轨道和路径；若只得到默认场景，画布
看起来复制成功，但最有价值的作者状态已经丢失。

本批优先级高于继续增加新的 Director feature，原因是它会直接验证并复用
前七轮可靠性工作的组合边界：

| 已有能力 | Batch 79 要验证的组合价值 |
|---|---|
| Batch 67 V1 strict document | duplicate 输入和输出都有可验证的 portable schema |
| Batch 68/76 owner registry | source/target canvas 与 Director owner 不串场 |
| Batch 69 authored/runtime split | 复制 authored baseline，不复制 playhead/runtime projection |
| Batch 70/71/78 history/gesture lifecycle | target 从 clean session 开始，不继承活动手势或历史 |
| Batch 72 reference-aware delete | 复制后的关系图不会留下 dangling reference |
| Batch 73 async authority | source 的晚到 capture/export 不写入 target |
| Batch 74 persistence | source/target 使用独立 storage identity |
| Batch 75 clipboard remap | 复用两阶段映射方法，但不误用 selection-paste 语义 |
| Batch 76 owner reachability | target owner 可达，source tombstone 不被错误复活 |

## 2. 证据与主张边界

### 2.1 当前 clone 固定事实

以下事实由当前代码和既有台账支持：

1. `src/store/canvasStore.ts` 的 `duplicateCanvas` 会复制 nodes、edges、viewport，
   重映射 node/parent/edge ID，创建空的目标 graph history，并激活新 canvas；
2. 普通 `script-execution` node 只把 node ID 作为 Director `sourceNodeId` 入口，
   Director scene/objects/groups/timeline 是独立 project document，不存进该 node
   的 graph data；
3. Batch 68 的 duplicate 兼容路径是新 owner 的 project reset，不共享旧 project；
4. Batch 74 的 persistence key 由 owner 组成，document 内有独立 `projectId`、
   owner 和 fingerprint；
5. Batch 75 的 remap 只处理同一 Director project 内被选中的
   object/group/track/path/keyframe/anchor closure；
6. Batch 76 的 tombstone 只处理 owner reachability，不会把 graph undo 自动变成
   Director project restore；
7. Director V1 document 的 camera 是 `objects[]` 中的 `kind: "camera"` 对象；
   group、track、path、keyframe、anchor、capture 和 resource reference 都有
   独立身份或引用关系。

固定代码入口：

- [`src/store/canvasStore.ts`](../../../src/store/canvasStore.ts)
- [`src/store/directorStore.ts`](../../../src/store/directorStore.ts)
- [`src/lib/directorProjectDocument.ts`](../../../src/lib/directorProjectDocument.ts)
- [`src/lib/directorProjectRegistry.ts`](../../../src/lib/directorProjectRegistry.ts)
- [`src/lib/directorProjectPersistence.ts`](../../../src/lib/directorProjectPersistence.ts)
- [`src/lib/directorClipboard.ts`](../../../src/lib/directorClipboard.ts)
- [`src/lib/directorOwnerReconciliation.ts`](../../../src/lib/directorOwnerReconciliation.ts)

### 2.2 可借鉴但不是 LibTV source fact

StoryAI 的 `DirectorProject.version`、scene/assets/objects/cameras 分层、
scoped persistence 和 copy/undo 是结构启发。Open Canvas 的 stable document ID、
hydrate、full-document replacement、resource lease 和 lifecycle ownership 是
方法启发。

这些项目都不能证明 LibTV 原站在复制一个 canvas 或 Director 节点时的精确
行为。当前没有足够 source-exact LibTV authenticated evidence 证明：

- duplicate source node/canvas 是否复制 Director authoring document；
- source/target 是否共享资产、重新物化资产或只复制引用；
- capture gallery、导出结果和手机录制是否属于 duplicate；
- duplicate 期间的 active session、undo history 和 selection 如何处理；
- source 画布复制失败时原站的 toast、modal、恢复或部分成功语义。

因此，本批所有合同、reason、资源策略和 verifier 都必须标记为
`CLONE_DECISION`，不能标记为 `SOURCE_FACT`。

## 3. 建议的 clone contract

### 3.1 命令形状

规划一个独立的 lifecycle command，而不是给当前 `duplicateCanvas` 追加一个
布尔参数：

```text
duplicateCanvasWithDirectorProjects(sourceCanvasId)
  -> resolve source canvas and all Director root nodes
  -> snapshot graph, registry, persistence and active-operation boundaries
  -> allocate target canvas/node/edge/project/entity identities
  -> build complete graph + Director deep-copy plan
  -> validate all references and resource policies
  -> commit graph and in-memory Director registry atomically
  -> persist target documents with explicit per-owner status
  -> activate target canvas with cleared selection and no Director shell
```

命令必须返回 typed result，至少区分：

```text
COMMITTED
COMMITTED_SESSION_ONLY
REJECTED
STALE
BLOCK_UNKNOWN
```

具体 reason 需要在实施前落为稳定 union，候选包括：

```text
DUPLICATE_SOURCE_CANVAS_MISSING
DUPLICATE_SOURCE_DIRECTOR_MISSING
DUPLICATE_SOURCE_TOMBSTONED
DUPLICATE_SOURCE_DOCUMENT_INVALID
DUPLICATE_REFERENCE_UNMODELED
DUPLICATE_NONPORTABLE_RESOURCE
DUPLICATE_RESOURCE_CONFLICT
DUPLICATE_IDENTITY_ALLOCATION_FAILED
DUPLICATE_STORAGE_SESSION_ONLY
DUPLICATE_OWNER_STALE
```

### 3.2 Owner 与 lifecycle policy

对 source canvas 的每一个 `script-execution` node，先得到：

```text
source owner = { route: "libtv", canvasId: sourceCanvasId, sourceNodeId }
target owner = { route: "libtv", canvasId: targetCanvasId, sourceNodeId: mappedNodeId }
```

规则：

1. target 必须分配新的 canvas ID、Director project ID 和所有 project-local entity ID；
2. target owner 不能只替换 `canvasId` 后继续共享 source document；
3. source project 的 `ACTIVE`/`CLOSED` record 需先冻结为 canonical document；
4. registry 没有 record 时，可尝试按 target owner 对应的严格 persistence envelope
   读取 source document；
5. registry、persistence 都没有 source project 时，只有在 source node 确实没有
   authored Director document 的情况下才创建 fresh target project；
6. source record 是 `TOMBSTONED`、owner/document 不匹配或 document 无法严格
   解码时，默认整批 `REJECTED/BLOCK_UNKNOWN`，不得静默 reset；
7. target record 以无 active session、无 playback/runtime、无 gesture、无
   clipboard、无 project history 的 `CLOSED` 状态登记；
8. duplicate 不进入 Director semantic history，也不把 source history 复制到 target；
9. 当前 UI 行为沿用普通 canvas duplicate：target canvas 成为 active，普通 selection
   清空，Director shell 不自动打开；
10. source active session/gesture 不因 duplicate 被取消或写入 target；它们继续只
    属于 captured source owner，晚到 completion 也不能写 target。

这里的 `CLOSED` 是 clone-owned registry 生命周期状态，不是对 LibTV 原站 UI
关闭语义的声明。

### 3.3 两阶段身份映射

不得在遍历对象时边复制边猜引用。先分配完整 ID map，再重写字段：

```text
Phase 1: allocate
  graph node -> graph node
  graph edge -> graph edge
  Director project -> Director project
  object -> object
  group -> group
  track -> track
  keyframe -> keyframe
  motion path -> motion path
  anchor -> anchor
  resource reference -> target-local resource reference
  capture descriptor -> capture descriptor

Phase 2: rewrite
  graph source/target/parent and Director node provenance
  project owner/project ID
  group members
  object assetRefId
  camera active/lookAt/follow references
  track object/group/path references
  group member-offset keys
  path object references and anchor/handle IDs
  capture camera/resource references
  Director-linked graph result source/edge/capture/camera references
```

全部 target IDs 必须与 source IDs 和 target 中已有 IDs 不冲突。生产 ID 可以继续
使用现有 opaque factory；pure verifier 必须注入 deterministic factory，禁止用
时间或随机值作为断言依据。

### 3.4 Director document mapping

对 `DirectorProjectDocumentV1` 逐字段处理：

| Document area | Duplicate policy |
|---|---|
| `schemaVersion` | 只接受当前 V1；先 strict decode/normalize |
| `projectId` / `owner` | 新 project ID；owner 指向 target canvas/mapped node |
| `scene` / `outputPreferences` | 深拷贝 semantic values |
| `objects` | 全量 deep clone；每个 object 分配新 ID |
| camera object | 作为 object 一并映射；`activeCameraId` 必须映射 |
| object camera relations | `lookAtObjectId`、`followTargetId` 映射到 target object |
| `groups` | 新 group ID；`characterIds` 和 crowd metadata 映射 |
| timeline tracks | 新 track ID；`objectId`、`groupId`、`motionPathId` 映射 |
| track keyframes | 新 keyframe ID；value 从 authored source 深拷贝 |
| motion paths | 新 path/anchor ID；`objectId`、anchors、handles 全量映射 |
| `resourceRefs` | 按 3.5 的 alias/copy/block policy 处理 |
| capture descriptors | 新 capture ID；camera/resource refs 映射，bytes 不直接复制 |
| selection/playhead/panel/phone/runtime | 不进入 document，也不进入 target session |

Whole-project duplicate 与 Batch 75 的 clipboard paste 的关键差别：

- clipboard 只复制 selection closure，并可以对外部 camera relation detach/freeze；
- whole-project duplicate 复制一个完整 document，所有合法 project-local relation
  默认都应映射，不应因为不是 selection 成员而 detach；
- clipboard 的 `sourceProjectId` 不能变成 target `projectId`；
- clipboard paste ordinal/selection/history 不得进入 target lifecycle；
- 不能直接调用 paste planner 后把结果包成 canvas duplicate。

### 3.5 Resource、capture 与结果投影

本批默认采用显式、保守的资源策略：

1. `catalog`、`remote` 或有稳定 locator 的 `canvas` resource：target 分配新的
   project-local reference ID，但底层稳定资源只做 alias，不复制 bytes；
2. `local`、`data:`、`blob:`、object URL 或 memory-only locator：没有稳定物化身份
   时返回 `DUPLICATE_NONPORTABLE_RESOURCE`，不静默复制坏 locator、假造 ready
   状态或丢掉依赖对象；
3. source 中存在 resource conflict、缺 descriptor、不可解析 locator 或引用
   不完整时，整批 zero-partial reject；
4. capture descriptor 只有在其 `resourceRefId` 能按上述规则映射时才作为 durable
   capture metadata 复制；
5. capture bytes、`File`、`Blob`、object URL、Three.js refs、phone sample buffer、
   active export/capture progress 不复制；
6. Director-linked graph result node 只有在 `sourceNodeId`、`edgeId`、`captureId`
   和 `cameraId` 等已登记引用可映射时才复制其 provenance；
7. ephemeral `videoUrl`/data URL 不能被当作 target 的 durable media；若结果无法
   进入明确的 stable-resource 或 detached-history policy，整批阻断；
8. source active operation 的 terminal completion 继续写 source owner 或变 stale，
   不因 target canvas 激活而改写 target。

这套策略可能让包含 session-only 本地模型或 data URL capture 的 duplicate 暂时
被阻断，但它符合当前 prototype 的 honesty 要求。后续若产品决定“复制语义状态、
不复制 session-only 资源”，必须先增加独立 policy/feedback 合同，不能在实现中
暗中删字段。

### 3.6 Transaction 与 persistence boundary

实施时要显式区分三种原子性：

```text
semantic plan atomicity
  -> graph + target owner/project document 全部接受或全部拒绝

in-memory commit atomicity
  -> source graph/document 不变；target graph/registry 一次可见

browser persistence outcome
  -> 每个 target owner 独立报告 SAVED 或 SESSION_ONLY
```

建议的 commit 顺序：

1. 读取 source canvas、全部 Director records、persistence snapshot 和 active
   operation context；
2. 生成 target graph/document/persistence envelope 的完整 staged plan；
3. strict validate graph/document/references/resource diagnostics；
4. validate target ID uniqueness、owner reachability 和 source immutability；
5. 一次提交 source/target graph 与 target in-memory registry；
6. target persistence 按 owner 写入；写失败不回滚已验证的 memory duplicate，
   但必须返回 `COMMITTED_SESSION_ONLY` 并保留可发现的 failure reason；
7. 激活 target canvas，清普通 selection，不打开 Director；
8. 任何步骤 1-4 的 reject 都不得写 graph、registry、history、selection 或
   persistence；步骤 5 之后不得出现“半个 target graph + 半个 Director document”。

普通 canvas lifecycle 不进入 graph `historyByCanvas`。source graph history、
Director source history 和 target empty history 必须分别保留；不能用 graph undo
偷偷回滚整个 duplicate。

## 4. 实施切片

本批获得编码授权后，按以下顺序实施；不跨切片重写所有 Director action。

### Slice A：静态入口与 pure whole-project planner

- 盘点 `duplicateCanvas`、Director owner registry、persistence、capture archive、
  result provenance 的读写边界；
- 新增独立 pure helper，例如 `src/lib/directorWholeProjectDuplicate.ts`；
- 定义 source snapshot、target allocation、ID map、resource disposition、
  staged graph/document 和 typed result；
- 先实现 strict input validation、identity allocation、two-pass rewrite 和
  zero-partial planning；
- 不在第一步直接修改 `canvasStore` 或 `directorStore`。

### Slice B：Director document/resource policy

- 用 `DirectorProjectDocumentV1` 做 source/target document boundary；
- 覆盖 camera/group/track/path/keyframe/anchor/capture/reference mapping；
- 对 stable alias、non-portable local resource、missing/conflicting resource
  建立稳定 reason；
- 明确 capture descriptor 与 memory capture sidecar 的分离；
- 先把不支持的 graph result provenance 变成 block，而不是复制 stale ID。

### Slice C：canvas + registry coordinator

- 为 ordinary `duplicateCanvas` 增加 named lifecycle coordinator 或替代入口；
- 一次 plan 后再 commit graph、owner registry、target document；
- target owner 关联到已 remap 的 Director root node，而非旧 node ID；
- target session/runtime/history/clipboard 以 clean state 开始；
- active source operation 的 owner/generation fence 保持；
- source/target graph history 和 Director history 隔离。

### Slice D：persistence outcome

- 为每个 target owner 生成独立 envelope；
- 复用 Batch 74 的 strict save/request/generation/fingerprint guard；
- 明确多 target owner 中某一个 storage failure 的 aggregate result；
- reload source/target 时分别恢复正确 project，不能从 source fallback；
- storage failure 只表现为 `SESSION_ONLY`，不伪造 durable success。

### Slice E：focused verifier 与治理

- 新增 proposed `LIBTV-VR-025` focused verifier；
- pure planner 使用 deterministic IDs/clock；
- browser 使用 fresh BrowserContext 和明确的 persistence cleanup；
- 更新 fixture catalog、verification ledger、traceability、decision register、
  current roadmap、Big Picture/Agent Task Map 和研究索引；
- 在 changed slice 后运行 Batch 59、67-79 current gates，以及 `npm run check`、
  `npm run docs:check` 和 `git diff --check`；
- 关键进展先 commit，实施结果和 runtime audit 先落档，再 push。

## 5. Fixture 设计

拟新增 fixture：
`LIBTV-FIX-LOCAL-DIRECTOR-WHOLE-PROJECT-DUPLICATE-01`。

状态：`REQUIRED_DISPOSABLE`；本计划阶段只有设计，没有可运行 fixture。

### 5.1 Source canvas

```text
canvas A
  script-execution source DA -> Director project PA
  script-execution source DB -> Director project PB
  ordinary node U
  Director-linked capture/export result nodes
  structural group/parent and ordinary edges
  per-canvas graph history
```

Director project PA 至少包含：

```text
scene settings
character + prop + two camera objects
one character group
transform/camera/pose/group tracks
one edited motion path with anchors and handles
internal camera look-at/follow references
stable catalog/remote resource reference
non-portable local/data/blob resource case
stable capture descriptor and session-only capture case
authored edits, non-zero playhead, active selection
project history, clipboard, phone runtime and one delayed operation context
```

Director project PB 用于验证多个 root owner 的批量映射和 partial failure
policy，不能只测试单一 Director node。

### 5.2 Target and isolation

duplicate 后目标应满足：

- new canvas ID；
- all graph node/parent/edge IDs new and structurally valid；
- DA/DB 分别映射到新 source node IDs；
- PA/PB 分别得到新 project IDs 和 new owner records；
- target documents strict-valid，所有内部 refs 指向 target entity；
- target no active session、no selection、no playback、no phone samples、
  no clipboard、no Director history；
- source documents、source graph、source history、source persistence 不变；
- target persistence key 与 source key 不同；
- target 的 stable resource 只 alias descriptor，不复制 bytes；
- non-portable policy 按 declared block/feedback result 执行；
- source delayed completion 对 source/target 都不产生错误写入。

### 5.3 Reset

每个 browser scenario 使用新 `BrowserContext`：

```text
new BrowserContext
  -> fresh Page
  -> goto localhost clone
  -> clear only clone-owned Director persistence fixtures
  -> construct or inject the named source canvas fixture
  -> open/edit Director source projects as the scenario requires
  -> execute one duplicate scenario
  -> inspect graph/registry/persistence/async snapshots
  -> discard context
```

不能把共享登录态 LibTV 项目当作 duplicate fixture，也不能依赖 undo 作为
teardown。若需要源站核对，只能在独立可丢弃项目和明确动作授权后另行记录，
不能将源站 destructive action 混入本批 verifier。

## 6. Verifier 设计

拟新增 `scripts/verify-liblib-batch79.mjs` 与
`scripts/verify-liblib-batch79.py`；本计划阶段不创建脚本，也不把它加入 current
manifest。

### 6.1 Pure scenarios

| 场景 | 必须证明 |
|---|---|
| valid single Director owner | new canvas/project/owner IDs，document deep isolation |
| multiple Director owners | all root mappings are complete and deterministic |
| graph node/edge/parent map | structural graph copy has no old owned IDs |
| object/group/camera map | all target references resolve；active camera maps |
| track/path/keyframe/anchor map | all timeline/path references and keys are new |
| camera relation map | look-at/follow/internal object refs map exactly |
| capture/resource map | stable refs alias by policy；capture refs remain valid |
| local/data/blob resource | declared `NONPORTABLE` block and zero mutation |
| invalid/tombstoned/mismatched source | stable reject and no staged partial output |
| deterministic allocator | same fixture/seed yields same plan shape and maps |
| input isolation | source snapshots and nested values are not mutated |
| runtime exclusion | selection/playhead/history/clipboard/phone/active op absent |
| provenance rewrite | Director-linked graph result refs map or block; never stale |

### 6.2 Browser scenarios

| 场景 | 必须证明 |
|---|---|
| duplicate through product entry | target canvas is active; ordinary selection is cleared |
| source graph continuity | source nodes/edges/viewport/history remain unchanged |
| target graph continuity | target parent/edge/node structure is fully remapped |
| source Director continuity | source project reopens with authored state and history |
| target Director continuity | target opens as independent copied authored state |
| A/B owner isolation | edits to target never alter source or sibling project |
| clean target session | no inherited panel, selection, playhead, gesture or clipboard |
| target reload | target persistence restores target project only |
| source reload | source persistence restores source project only |
| delayed source completion | old operation commits source or becomes stale; never target |
| persistence failure | duplicate remains visible as explicit `SESSION_ONLY` when allowed |
| rejected non-portable case | graph/registry/history/selection/persistence stay unchanged |
| ordinary graph history | duplicate remains lifecycle action; target history starts empty |
| mobile/desktop shell | target can be opened and Director shell remains usable |
| diagnostics | zero console/page/request errors; screenshots default to zero |

真实触摸板硬件、源站 Director DOM/CSS、真实 Provider、远端 storage 和真实
mesh/panorama materialization 不属于本 verifier。

## 7. 验收条件

只有同时满足以下条件，Batch 79 才能从 `PLANNED` 升级：

1. pure planner 对 graph、所有 Director entity、camera relations、resource、
   capture 和 result provenance 有完整 two-pass map；
2. accepted plan 是 graph + target Director owner/document 的语义整批提交；
3. source document、source graph、source history 和 source persistence 不被改写；
4. target project ID、owner 和所有 project-local IDs 都是新的；
5. target document strict-valid，没有 dangling reference 或旧 source-owned ID；
6. target session/runtime/history/clipboard 不从 source 泄漏；
7. stable resource 只按明确 alias policy 共享 descriptor，不复制不透明 bytes；
8. non-portable/missing/unmodeled resource 或 tombstoned source 默认稳定阻断，
   reject 为 zero mutation；
9. active source async completion 受 owner/session/generation fence 保护；
10. target persistence 具有独立 key/fingerprint，storage failure 明确为
    `SESSION_ONLY`，不伪造 durable success；
11. ordinary graph history 与 Director semantic history 的步数边界清楚；
12. fresh BrowserContext、desktop/mobile、diagnostics 和必要 reload 场景通过；
13. Batch 59、67-79 current gate、`npm run check`、`npm run docs:check` 和
    `git diff --check` 均有 dated 记录；
14. 实施结果、runtime audit、verifier manifest、fixture、traceability 和
    decision register 已更新；
15. 关键进展已 commit/push，主 worktree 唯一且干净。

## 8. 不在本批范围

- 证明 LibTV 原站 exact duplicate UI、菜单、toast、modal、快捷键或数据语义；
- 操作共享源站创建、复制、保存、删除、导出或生成；
- system clipboard、跨 project/canvas clipboard、跨窗口传输；
- 真实远端资源复制、上传、账号资产、云同步、计费和 Provider；
- local FBX/OBJ、panorama、Blob/File/object URL 的真实物化；
- ordinary canvas 全部 11 类 node data 的通用 portable codec；
- graph undo 自动恢复 source/target Director project；
- duplicate 的项目级 undo/redo；
- 把 Session-only capture/resource 强行转成 durable data；
- 一次性包装全部 Director store action 或重写全部 React Flow ingress。

## 9. 依赖、风险与停止条件

### 9.1 依赖

- [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
- [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)
- [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)
- [`LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md)
- [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)
- Batch 74/75/76 implementation records
- 当前主 worktree 的 source code 和 existing owner/persistence APIs

### 9.2 风险

| 风险 | 防护 |
|---|---|
| 把 clipboard paste 误当 whole-project duplicate | 独立 command、完整 document fixture 和 two-phase plan |
| 复制旧 project ID 或 owner | target allocation + strict identity assertions |
| 只复制 graph，丢 Director authored state | registry/persistence source snapshot 是 plan 输入 |
| stale camera/track/path/capture refs | complete ID map + strict decode before commit |
| local/data/blob 资源伪装可复制 | stable alias/block policy，默认 fail closed |
| source active async 写入 target | captured owner/session/generation verifier |
| localStorage 多 key 部分成功 | memory semantic atomicity + explicit per-owner `SESSION_ONLY` |
| ordinary graph data 含未建模 Director provenance | result projection map 或整批 block |
| 误把 clone decision 写成 source fact | README/PLAN 明确 claim boundary，source evidence 单独记录 |

### 9.3 必须停止的情况

出现以下任一条件，保持 `PLANNED` 或升级为 `BLOCKED_BY_FIXTURE`，不开始业务
实现：

- 没有明确编码授权；
- source/target owner 或 project identity 仍只能靠 display name/index 推导；
- 任何 project-local reference 没有 map/preserve/reset/block 规则；
- 资源 policy 仍会静默复制 bytes、丢 capture 或保留 stale URL；
- 不能提供多个 Director owner、持久化和 delayed operation 的本地 fixture；
- 现有 parallel WIP 触及 `canvasStore`、Director registry/persistence 或
  duplicate entry，导致无法划定窄边界；
- storage/graph/registry 的 partial failure 语义没有可观察结果；
- 需要向共享 LibTV 源站写入或消耗任务，但没有 disposable fixture 和动作授权。

## 10. 本批状态与下一步

本轮目标是完成 Slice A-D 的最小闭环：pure planner、Director registry
registration、普通 canvas coordinator、per-owner persistence outcome 和
focused verifier。实现不得扩展为通用 graph codec，也不得把 session-only
capture/resource 静默复制到 target。

### 10.1 已锁定的实施决策

1. `duplicateCanvas` 保留现有产品入口和 target-active/selection-clear
   语义，但返回 typed lifecycle result 供 verifier 和未来反馈层观察。
2. 没有 registry record 且 persistence 明确为 `MISSING` 的 Director root
   视为尚未建立 authoring document，target 创建 fresh project；storage
   `REJECTED`、tombstone 或 malformed document 不允许静默 reset。
3. `catalog`、`remote`、`canvas` resource 只 alias descriptor 并分配新的
   target-local reference ID；`local` resource 和没有 durable capture
   reference 的 session-only capture 不复制，若 graph result 依赖它则整批
   reject。
4. target Director record 以 `CLOSED`、generation `1`、空 history/session/
   clipboard/runtime 登记；target 打开时才创建新的 active session。
5. persistence 写入是 memory commit 之后的独立 outcome；全部成功为
   `COMMITTED`，任一 owner 只能 session-only 时返回
   `COMMITTED_SESSION_ONLY`，不回滚已验证的 memory duplicate。

### 10.2 实际实施结果

- [x] `planDirectorWholeProjectDuplicate` pure planner；
- [x] graph/parent/edge 与 Director project-local identity 两阶段映射；
- [x] source owner/document/lifecycle/persistence strict gate；
- [x] `DirectorProjectRegistry.registerCopies` 原子批量登记；
- [x] `canvasStore.duplicateCanvas` coordinator 和 typed result；
- [x] target `CLOSED + generation 1`、空 history/session/clipboard/runtime；
- [x] stable resource descriptor copy 与 local/ephemeral resource block；
- [x] pure verifier、fresh-page Playwright verifier 和 `runtime-audit.json`；
- [x] 移除 planner 临时类型断言，并校验外部 `targetSourceNodeId` 必须与 graph
  map 一致；
- [x] Batch 59、67-79 current gate、`npm run check`、`npm run docs:check` 和
  `git diff --check`；
- [x] 实施记录、治理台账、commit/push 和干净主 worktree。

实际偏差：

1. persistence 仍是当前 browser-local synchronous adapter；写失败不回滚已登记
   的 memory project，而是返回 `COMMITTED_SESSION_ONLY`；
2. portable capture descriptor 只复制具有 stable resource reference 的条目，
   memory capture bytes 不复制；
3. 本批未重构普通 canvas 全局 ID allocator，只保证 target canvas 和本次
   graph/Director identity 不复用 source。
