# LibTV Fixture Catalog

> 目的：为后续 LibTV UI/UX 研究、复刻和回归提供统一的 fixture 身份、构造、隔离、reset 和副作用合同。
>
> 本文来自 2026-08-26 对 `canvasStore`、`page.tsx`、Batch 4-48 verifier、当前源站研究边界和 Batch 48 clone-owned local model workflow 的只读审计。本文不授权修改代码、测试、截图或源站项目。
>
> 选择复刻 slice 时先读 [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)；判断是否允许操作时再读 [`liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)。

## 1. 结论

当前仓库不是“缺少所有 fixture”，而是混有五类性质不同的状态：

1. `canvas-2` 是源码内置的 source-shaped demo baseline；
2. `canvas-1` 是本地空画布，现有 Batch 24-33 主要通过真实 UI 在这里构造确定性状态；
3. graph 结果态由 store transaction 派生，不是远端任务结果；
4. Director verifier 可通过 `window.__director_store` 直接驱动 domain state，Batch 48 还引入 browser-local persistence；
5. 当前登录态源站项目只是共享的只读观察对象，不是可重置测试 fixture。

因此，后续 agent 不应再笼统写“使用 disposable fixture”。必须引用本文的 fixture ID，或者新增一个包含 owner、构造、reset 和禁止动作的 ID。

## 2. 状态词表

| 状态 | 含义 | 是否可直接用于后续本地回归 |
|---|---|---|
| `AVAILABLE_BASELINE` | 源码加载即存在，节点 ID 和初始 graph 可静态审计 | 可以，但必须先断言 baseline 未漂移 |
| `UI_CONSTRUCTED` | 在新 Page 中通过产品 UI 从空画布构造 | 可以；优先于测试直接写 store |
| `TRANSACTION_DERIVED` | 通过 store action/UI command 由基础节点生成 | 可以；必须断言 graph/history delta |
| `DIRECT_STORE_DRIVEN` | verifier 经公开到 `window` 的 Director store 读取或驱动 | 仅用于 Director 专项合同 |
| `SHARED_READ_ONLY` | 登录态共享源站，只允许无副作用观察 | 只能取证，不能作可重复回归 fixture |
| `REQUIRED_DISPOSABLE` | 所需状态尚不存在，必须另建可丢弃本地或源站对象 | 不可以；保持 `BLOCKED_BY_FIXTURE` |
| `PARALLEL_WIP` | 其他开发者正在修改 fixture、持久化或 verifier | 只读避让，稳定后再登记 |
| `OUT_OF_SCOPE` | 需要真实 Provider、计费、账号或远端任务系统 | 当前前端原型不建设 |

这些词描述 fixture 本身。验证成熟度仍使用 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的 `SCRIPT_AVAILABLE`、`SOURCE_CONTRACT_ONLY` 等状态，两套词不能互换。

## 3. 运行时隔离事实

### 3.1 普通 LibTV 画布

`useCanvasStore` 是模块内 Zustand store，当前没有 `persist` middleware，也没有把 store 暴露为 `window.__canvas_store`。初始值直接定义在 `src/store/canvasStore.ts`：

```text
projectName: 未命名项目
canvases: canvas-1(empty), canvas-2(source-shaped demo)
activeCanvasId: canvas-2
selection: empty
historyByCanvas: empty
```

现有普通 LibTV verifier 的实际隔离方式是：

```text
browser.new_page()
  -> page.goto(local clone)
  -> 新文档重新建立模块内 store
  -> 需要空态时从 UI 切到 canvas-1
  -> 从 Add Node 等真实入口构造状态
  -> 在该 Page 内完成断言
  -> Page 被丢弃
```

普通 Batch 脚本中的 `page.evaluate` 主要读取 DOM overflow 或执行 `element.click()`，不是统一的 canvas fixture 注入器。后续不能声称仓库已有通用 `setState` fixture API。

### 3.2 新 Page、reload、切换 canvas 不是同一 reset 等级

| 操作 | 能恢复的内容 | 不能作为默认承诺的内容 |
|---|---|---|
| 新建 Playwright Page 后 `goto` | 普通 canvas/ui 模块内初始状态；最接近现有脚本合同 | 同一 BrowserContext 的 local/session storage、认证 cookie |
| reload 当前 Page | 理论上会重建当前文档和普通内存 store | 现有脚本没有把它作为统一 reset 原语；必须重新断言 graph/selection/history |
| 切到 `canvas-1` | 得到源码初始空 graph，selection 被清空 | 若同一 Page 之前已经修改过 `canvas-1`，不会恢复；其他 canvas/history/UI state 也不会清零 |
| undo | 最近一次有 history 记录的 graph snapshot | viewport、canvas CRUD、project name、UI store、selection、远端副作用 |
| Escape/空白点击 | selection 或局部 overlay，取决于 surface | graph、history、媒体版本和持久化数据 |

结论：普通本地行为测试以“每个独立场景使用新 Page”为强 reset；在同一 Page 复用 `canvas-1` 前必须显式证明它仍是 `0 nodes / 0 edges`。

### 3.3 History 不是 fixture reset 系统

当前 graph snapshot 只克隆 node 顶层、`position`、`style` 和一层 `data`，nested `data` 仍是浅边界。另有以下事实：

- `setNodes`/`setEdges` 默认不记录 history；
- `updateNodeData` 会记录 history，但可能产生 no-op snapshot；
- undo/redo 恢复 graph 后清空 selection；
- viewport 不属于 graph history；
- canvas add/remove/rename/duplicate 不属于 graph undo；
- Director 有独立 store/history，不能用 canvas undo 清理。

所以 fixture teardown 不得只写“最后按 Cmd+Z”。Undo/redo 可以是被测合同，也可以验证 transaction 原子性，但不能替代新 Page reset。

### 3.4 Director 是另一套 fixture 域

Batch 35-48 的 Director verifier 可以读取或调用 `window.__director_store.getState()`。这是 Director 专项测试入口，不是普通 LibTV graph 的通用注入规范。

Batch 48 新增了 browser-local model-library storage。它已有完整 workflow、
稳定 verifier、截图台账和成熟度记录，但只定义了 clone-owned prototype
边界：

- 测试必须显式清理
  `liblib-tv-director-local-model-library-v1`，不能把“新 Page”误认为足以
  清理同一 BrowserContext 的 persistence；
- import 应通过多个合法 `.fbx`/`.obj` 文件和真实 UI input 构造；
- descriptor 恢复应在 fresh Page/context 中重新断言；
- 不把 localStorage descriptor 或 proxy object 升级为真实 LibTV 生产资产合同。

### 3.5 Director local-model fixture reset

Batch 48 的最小可重复 setup/teardown：

```text
new BrowserContext
  -> new Page
  -> goto clone
  -> localStorage.removeItem("liblib-tv-director-local-model-library-v1")
  -> open Director
  -> import via [data-director-model-library-local-input]
  -> assert localStorage/card/scene state
  -> remove final local card
  -> assert storage === []
  -> discard context
```

固定断言：

- 初始 `我的模型` 是空态，input `multiple` 且接受 `.fbx,.obj`；
- 非法扩展名不产生 card 或 browser error；
- persistence 只包含 `DirectorLocalModelLibraryItem` 的 bounded fields；
- fresh context 能恢复卡片；
- 删除资产会删除全部关联 local proxy object、timeline track 和 motion path；
- 最后一张卡删除后 storage 为空并回到 empty state。

## 4. 当前可用本地 Fixture

### 4.1 总表

| Fixture ID | 状态 | 构造/owner | 初始关键状态 | 主要用途 |
|---|---|---|---|---|
| `LIBTV-FIX-LOCAL-DEMO-01` | `AVAILABLE_BASELINE` | `canvasStore.initialCanvas2` | `canvas-2`，10 nodes / 11 edges，source-shaped viewport | 历史图片/视频浮层、分组、整理、asset/tree、baseline topology |
| `LIBTV-FIX-LOCAL-EMPTY-01` | `AVAILABLE_BASELINE` | `defaultCanvas("canvas-1")` | 0 nodes / 0 edges / zoom 1 | 隔离构造单节点、派生 graph 和响应式场景 |
| `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` | `AVAILABLE_LOCAL` / `DESIGN_SPEC_COMPLETE` / `RECORDED_PASS` | fresh Page + `LOCAL-EMPTY-01` + Batch 57 local graph setup | ordinary A/B/C aliases；per-scenario edge/history boundary；无 pending/invalid state | direction normalize、duplicate/self/cycle、reject no-op 和 accepted one-step history |
| `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | pure V1 payload corpus + fresh Page + `LOCAL-EMPTY-01` | empty/demo/group/nested metadata/invalid version-ID-parent-media cases | document codec、strict load、migration boundary、nested history isolation 和 import zero-partial |
| `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + deterministic ID provider + group/child/external/derived topology | named roots、descendant closure、internal/external edges、reference roles、placement/history boundary | copy planner、ID/reference map、detach/group、zero-partial 和 one-step undo/redo |
| `LIBTV-FIX-LOCAL-NODE-DATA-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | pure V0 corpus + fresh Page + deterministic node/edge/aggregate IDs | all 11 runtime types、nested provenance、shot/process aggregates、repo/https/data/blob media、invalid type/version/ref cases | registry completeness、operation transforms、deep isolation、aggregate integrity、media diagnostics 和 zero-partial |
| `LIBTV-FIX-LOCAL-GRAPH-DELETE-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | pure delete corpus + fresh Page + deterministic graph/relation/UI owner state | plain/group/selected-edge/derived/shot/process/canvas/media scenes；ready/reject/unknown policy | structural closure、inverse refs、aggregate repair、UI invalidation、resource diagnostics、one-step undo/redo 和 zero-partial |
| `LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | composition of connection/document/copy/data/delete fixtures + fresh Page | ordinary/group/derived/aggregate/history/remote aliases；same proposal over multiple ingress | T0-T5 routing、transport whitelist、full-draft reject、restore/remote stale 和 zero-partial |
| `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + deterministic operation/run/result IDs + fake clock/completion queue + resource ledger | C1/C2、S1@V1/V2、draft A/B、old/current attempts、placeholder/result/resource aliases | current/stale/duplicate/invalid disposition、field owner、selection/history、projection recovery、resource transfer/release |
| `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + exact 12.11.1 change corpus + deterministic store/render timing | node/edge select、position/measure、semantic/unknown/mixed/stale/current-canvas cases | whole-batch T0/T1 routing、current snapshot、one drag history、zero-partial reject 和 runtime-field sanitation |
| `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + deterministic A/B/C graph/viewport/history + UI/transient/async/resource controls | valid/invalid/same switch、organize/drag/viewport race、duplicate/delete/final fallback、old timer/save cases | registry/active/selection/history atomicity、owner manifest、stale callback isolation、resource impact 和 zero-partial lifecycle |
| `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + deterministic dispositions/reasons + fake timer/announcement clock + A/B canvas/node/surface/operation owners | field/connection reject、prototype unavailable、node guard、visible result、async fail/retry/stale/duplicate、switch/delete/close、burst/route isolation | reason/copy separation、primary surface、zero-history feedback、owner cleanup、dedupe、accessibility 和 prototype honesty |
| `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + deterministic node/edge/primary selections + editable/surface/modal/Director focus zones + A/B canvas generations | click/multi-select/edge select、editable keys、foreground contexts、single Escape、switch/delete/undo、focus return/fallback、route isolation | validated active selection、declared dispatch result、zero-history selection/focus、one-layer unwind、focus containment/return 和 stale-owner cleanup |
| `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `FOCUSED_RUNTIME_PARTIAL` | Batch 63/64/65 fresh Page slices + future deterministic canvas generations、measured host epochs、nested/top-level nodes和 controlled viewport operation clock | implemented identity/translated/invalid、desktop/mobile asset-open default add、drawer reconciliation、desktop/mobile bootstrap、breakpoint stable preservation、A/B switch restore、stale/invalid callback；future pan/zoom endpoint/cancel、browser resize、derived/duplicate/organize、selected overlay | Batch 63 host-center add、Batch 64 Asset host-resize 和 Batch 65 bootstrap/stored viewport owner pass；full live/stable endpoint、generic generation/host epoch、cancel/idempotent gesture and full placement/overlay composition仍缺 |
| `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | fresh Page + synthetic in-memory image/video/audio/text files + deterministic classifier/probe/fake materializer/resolver clock + A/B generations + asset/reference/resource ledger | cancel、invalid/mixed/out-of-order cohorts、replace success/failure、retry/delete/switch races、history/asset attach、blob/data reachability、route isolation | typed validation/probe、full-plan cohort commit、last-known-good、zero stale residue、exact history/selection/feedback、lease transfer/release and honest capability projection |
| `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | pure session reducer + fresh Page + deterministic text/config/record/range/4x4 bitmap owners + fake clock/async acceptor + graph/resource/focus/feedback oracles | open/cancel/blur/noop/commit、gesture/undo/redo/reset、drift/delete/switch、async accept/fail/late、budget/IME/empty-command cases | unique owner、semantic dirty/no-op、one local gesture、one accepted graph step、zero cancel/stale residue、byte/release budget、undo precedence and honest controls |
| `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` | pure frame/rendition/fit model + fresh Page + deterministic 16:9/2:1/1:1/9:16/odd media/output descriptors + thumbnail/full/poster aliases + fake measurement clock | matching/mismatching/invalid metadata、same/mixed-ratio output switch、cover/contain/editor round-trip、status transition、stale measurement、detail/route isolation | finite authority/provenance、atomic selection/frame policy、zero passive-measure history、fresh overlay anchor、full/visible editor intent and no fabricated resize |
| `LIBTV-FIX-LOCAL-IMAGE-01` | `UI_CONSTRUCTED` | 在空画布从 Add Node 添加图片 | 本地图片、`editorVariant=empty`、selected | 标准图片浮层、Preview/Annotate/Element Edit 的低风险本地状态 |
| `LIBTV-FIX-LOCAL-VIDEO-READY-01` | `UI_CONSTRUCTED` | 在空画布从 Add Node 添加视频 | `status=ready`、30s、1280x720、Seedance 2.5、selected | Batch 23、26-33 视频入口和本地处理动作 |
| `LIBTV-FIX-LOCAL-IMAGE-VARIANTS-01` | `AVAILABLE_BASELINE` | `canvas-2` 五个图片节点 | empty、prompt、referenced 三类 editor state | 历史 Batch 9/10 panel 高度与内容状态 |
| `LIBTV-FIX-LOCAL-GROUP-01` | `AVAILABLE_BASELINE` | `canvas-2` 两个 storyboard groups | image group、video parent-child group | group/ungroup、parent-child、organize 和 subgraph 研究 |
| `LIBTV-FIX-LOCAL-DERIVED-01` | `TRANSACTION_DERIVED` | UI/store 的 derived actions | 动态 node/edge ID、atomic history 视 action 而定 | continuation、subtitle、audio、frame、matting、picture/depth edit |
| `LIBTV-FIX-LOCAL-LONG-PROCESS-01` | `TRANSACTION_DERIVED` | ready video 切 long-video 后提交 | 1 source + 12 process nodes / 22 edges；process status `pending` | 本地超长视频 process topology、重复提交、undo/redo |
| `LIBTV-FIX-DIRECTOR-BASE-01` | `DIRECT_STORE_DRIVEN` | Director store + Batch 35-48 setup | scene/object/camera/timeline domain state | Director 专项视觉、轨道、路径、拍摄、导出和 model-library proxy |
| `LIBTV-FIX-DIRECTOR-LOCAL-MODEL-01` | `UI_CONSTRUCTED` | Batch 48 verifier + local input | fresh context + cleared clone-owned storage | local descriptor import/persistence, refresh recovery, proxy re-add and cleanup |
| `LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` | `PURE_CODEC_RECORDED_PASS` / `OWNER_SESSION_FOCUSED_PASS` / `AUTHORED_RUNTIME_FOCUSED_PASS` / `HISTORY_FOCUSED_PASS` / `POINTER_LIFECYCLE_FOCUSED_PASS` / `REFERENCE_DELETE_FOCUSED_PASS` / `ASYNC_AUTHORITY_FOCUSED_PASS` / `PERSISTENCE_FOCUSED_PASS` / `CLIPBOARD_REMAP_FOCUSED_PASS` / `OWNER_REACHABILITY_FOCUSED_PASS` | Batch 67 pure `DirectorProjectDocumentV1` corpus + Batch 68-76 fresh Director page with deterministic route/canvas/source owner、session/generation、authored/runtime fingerprints、project-local history、memory capture sidecar、gesture boundaries、reference closure、async operation/resource ledger、browser-local persistence envelope、project-scoped clipboard packet and all-canvas live owner set | implemented valid/invalid/future documents、A/B source owners、cross-canvas owners、focus/close/reopen/active-delete/duplicate-reset、seek/playback/path sampling、object/camera/pose authoring、no-op/rejection outcomes、gesture coalescing、undo/redo、Inspector/R3F/free-draw commit/cancel/pointercancel、object/group/camera/track/path/capture/resource delete closure、capture/export/phone async owner/source/attempt/result convergence、reload restore、stale save、runtime/UI/resource-byte exclusion and storage failure、typed clipboard closure/remap、camera detach/freeze、resource alias、repeated offsets、A-B-A/reload isolation、inactive source/canvas tombstone、active two-phase cleanup、repeated reconciliation、graph undo and retained persistence；future durable tombstone/storage/resource cleanup、whole-project duplicate and ordinary canvas persistence | strict codec、owner registry/session lifecycle、authored/runtime split、synchronous command/history、pointer lifecycle、reference-aware delete、Director async-authority、Director browser-local persistence、same-project clipboard-remap and owner-reachability slices 已覆盖；ordinary canvas async/persistence、durable tombstone cleanup、whole-project duplicate、remote storage 和 source parity 仍缺 |

### 4.2 `LIBTV-FIX-LOCAL-DEMO-01`

稳定源码身份：

```text
canvas: canvas-2 / 画布 2
viewport: x=-583.8, y=260.8, zoom=0.526
nodes: 10
edges: 11
```

关键节点：

| ID | 类型/状态 | 可支持的研究 |
|---|---|---|
| `i-1FQ9tErTcC` | image / empty editor | 标准图片节点和资产入口 |
| `i-dnwoZQ7jsG` | image / prompt | Prompt 面板和图片内容态 |
| `i-YDfWhFlthe` | image / referenced | 引用缩略图、较高 panel、历史 overlay geometry |
| `v-UGQZzZOpbv` | video / `failed` / group child | failed 分支、parent-child；**不是 ready-video fixture** |
| `g-245IDFh8sB` | image storyboard group | organize/group topology |
| `g-EFbbHpwq5w` | video group | parent-child 和 cascade behavior |

使用规则：

- 脚本开始先断言目标 ID 和 10/11 baseline，避免源码演示数据漂移后出现误判；
- 测试若移动、分组、复制、删除或派生节点，应在独立 Page 完成；
- 历史 Batch 9/10 可继续使用这些 ID，但其 toolbar/AutoLink 断言仍是 dated clone contract；
- 不能把源码 demo 的节点位置、文案或 failed video 当作当前源站事实。

### 4.3 `LIBTV-FIX-LOCAL-EMPTY-01`

构造步骤：

```text
new Page -> goto / -> open canvas dropdown -> select canvas-1
         -> assert 0 nodes / 0 edges
```

它是目前最可靠的普通 LibTV fixture substrate。Batch 24-33 中多个脚本使用这一模式。适合每个场景只构造一个 source node，再观察明确的 graph delta。

限制：`canvas-1` 不是特殊的自动清理空间；它只在新 store 实例中初始为空。同一 Page 一旦写入，后续切走再切回仍会保留内容。

### 4.4 `LIBTV-FIX-LOCAL-IMAGE-01`

从空画布点击“添加节点 -> 图片”得到：

- node shell 默认 `512 x 288`；
- data 中媒体尺寸默认 `512 x 512`；
- 本地图片 URL 和 watermark URL；
- `editorVariant=empty`、`editorHeight=191`；
- 新节点自动成为单选 selection；
- add-node transaction 进入 canvas history。

node shell 比例和媒体 data 比例不同是当前 clone 事实，不能被文档静默抹平。几何测试应明确自己使用 measured node rect 还是媒体 metadata。

### 4.5 `LIBTV-FIX-LOCAL-VIDEO-READY-01`

从空画布点击“添加节点 -> 视频”得到：

```text
filename: 视频节点 5-片段重拍
status: ready
durationSeconds: 30
resolution: 1280 x 720
posterUrl: local image
model: Seedance 2.5
```

这解释了为何 Batch 23、26-33 能验证 clone 的 ready-video 工具，而 `canvas-2` 的既有视频仍是 `failed`。该 fixture 只证明 clone 分支；它不能推出源站 ready toolbar 的动作顺序、菜单、状态或结果版本语义。

### 4.6 `LIBTV-FIX-LOCAL-DERIVED-01`

现有 derived transaction 常见模式是：

```text
ready source
  -> open one active tool/menu
  -> submit local mock action
  -> create target node(s) + direct source/result edges
  -> update selection or keep source selection according to action
  -> record one graph snapshot
  -> assert undo/redo atomically removes/restores the graph delta
```

动态 ID 通常包含时间或随机后缀。测试应从 selected node、`data-*` metadata 或 source/target edge 关系获取 ID，不能硬编码本次运行生成的 ID。

`LIBTV-FIX-LOCAL-LONG-PROCESS-01` 是其规模最大的现有例子：一次提交增加 12 个 process nodes 和 22 条 edges；加上 source 后页面总量为 13 nodes / 22 edges。所有 process 节点当前都是 bounded mock 的 `pending`，不是后台任务快照。

## 5. 源站观察对象

### 5.1 `LIBTV-FIX-SOURCE-SHARED-01`

| 字段 | 当前合同 |
|---|---|
| URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| 状态 | `SHARED_READ_ONLY` |
| Owner | 用户共享的登录态研究项目；不是 agent 独占 disposable project |
| Reset | 未知；不得假设 source undo、reload 或关闭页面能消除远端副作用 |
| 用途 | DOM、computed style、screen rect、可见文案、bundle、无副作用 surface lifecycle 取证 |

允许的动作：

- 打开/切换只读页面区域；
- 选择已有节点并读取可见工具条、面板、DOM 和 computed rect；
- 打开后关闭不写入的菜单、帮助、预览或 drawer；
- 截图和记录当前日期、viewport、zoom、selection 和已知 fixture 状态；
- 在已有文档不足时读取 bundle 字符串，但把 bundle-only 结论标为 inference/contract evidence。

禁止的动作：

- 输入或提交 Prompt、接受 AutoLink 候选；
- 新增、移动、连接、复制、分组或删除 graph 对象；
- 上传、生成、重拍、续写、标注保存、旋转提交、图层分离；
- 切换可能持久化的全局偏好；
- 下载、消耗积分、启动任务、覆盖媒体版本；
- 用一次 source undo 作为“已清理”的充分证据。

共享源站可以回答“当前看见什么”，不能满足“每次回到相同 graph、viewport、selection、media version”的 fixture 定义。

## 6. 必须另备的 Disposable Fixture

| Fixture ID | 环境 | 最小状态 | 允许研究后应观察 | 当前状态 |
|---|---|---|---|---|
| `LIBTV-FIX-SOURCE-IMAGE-DIRTY-01` | 独立源站项目 | 可编辑图片、已知 graph/version、允许保存/撤销 | rotate/layer/annotate 的 task、graph、version、save/undo boundary | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-AUTOLINK-01` | 独立源站项目 | 至少两个 connected/reference candidates、可输入 Prompt | ghost、Tab/Shift+Tab/Escape/IME、single/all accept、mention identity | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-VIDEO-READY-01` | 独立源站项目 | 可播放 ready video、已知 duration/version、允许打开工具 | toolbar order、hover menu、active replacement、discard/submit delta | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-SHORTCUT-01` | 独立源站项目 | 可丢弃 subgraph、group、internal/external edges | `L`、Enter、Option-drag、Option+G、duplicate closure 和 cancel | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-GRAPH-CONNECTION-01` | 独立源站项目 | ordinary A/B/C、可连接 Handle、已知初始 edge/selection/history、允许销毁 | target-start normalize、duplicate/reverse/self/cycle、invalid target/line/feedback 和 no-residue | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-GRAPH-DELETE-01` | 独立源站项目 | plain/group/derived/shot/process 已知状态、明确逐动作授权、remote cleanup owner | source/result/member/semantic-edge 删除、确认、selection/overlay、undo/redo 和 persisted cleanup | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-PROCESS-01` | 独立源站项目 | 可观察 pending/failed/partial/success/retry 的任务或已授权 mock | run/node/save status、candidate/result version、局部重算和替换 | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-MEDIA-INGRESS-01` | 独立源站项目 | synthetic non-private files、已知 graph/assets/history、明确 upload/task/credit/delete 授权和 cleanup owner | exact limits/reasons、placeholder/progress/cancel/retry、multi-file placement/order、replace retention、history attach、asset registration、refresh restoration | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-EDITOR-SESSION-01` | 独立源站项目 | 可编辑 text/config/region/image surfaces、已知 graph/history/source version、明确 save/task/credit/cleanup 授权 | blur/Enter/Escape/IME、local/global undo、reset/redo、dirty close、source drift、submit/close/failure/retry、graph history cardinality | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-MEDIA-RENDITION-01` | 独立源站项目 | landscape/square/portrait image、ready video、可切换 mixed-ratio outputs、已知 node/media/version，明确只读/选择/播放/切换/resize 授权与 reset | frame bounds/policy、poster/full fit、detail composition、output switch/reflow、measurement/overlay lifecycle、object position、resize presence/history | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-LOCAL-AUTOLINK-01` | clone | typed candidates/ghost/mention/session 和可控延迟 | keyboard/IME/stale-result/transaction consistency | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` | clone | ordinary A/B/C aliases、per-scenario edge/history boundary、可控 proposal/result | pure/browser normalize、guard precedence、zero-mutation reject、one-step accept | `AVAILABLE_LOCAL` / `DESIGN_SPEC_COMPLETE` / `RECORDED_PASS` |
| `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` | clone | V1 payload corpus、fresh Page、nested marks/regions/process arrays、invalid version/ID/parent/media cases | strict round-trip、runtime-field exclusion、stable reason、deep history isolation、zero-partial load | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` | clone | G/A/B/C/X/Y/D aliases、deterministic node/edge IDs、owned/external/unmodeled refs | closure/dedupe、parent detach/remap、edge policy、reference role、placement、atomic history | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-NODE-DATA-01` | clone | 11-type V0 corpus、all current identity paths、complete/broken shot/process aggregates、media locator classes | field role/operation policy、deep normalize、map/reset/reject、stable diagnostics、delete repair boundary | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-GRAPH-DELETE-01` | clone | deterministic nodes/edges/selection、registered inverse refs、complete/broken aggregates、UI owners、media locators | closure、cascade/detach/reset/block、stable plan/reason、overlay/resource result、undo/redo | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` | clone | A/B/C、group/derived/shot/process、valid/invalid history、current/stale patch aliases | equivalent ingress、change whitelist、planned command、restore and remote authority | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` | clone | deterministic canvas/source/version/operation/run/attempt/result + fake clock/completion queue/resource ledger | draft/source drift、delete/undo、retry race、duplicate delivery、UI/graph drift、projection recovery、invalid payload | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` | clone | exact change variants、same-ID mixed order、finite/invalid numbers、stale render/store snapshots、active canvas switch | T0/T1 accepted batches、semantic/unknown rejection、selection owner、drag history、runtime-field projection | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` | clone | deterministic A/B/C IDs、distinct graph/viewport/history、selection/UI/transient owners、fake timer/save/resource ledger | switch/unknown/same、duplicate/delete/fallback、old organize/drag/viewport/completion convergence | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` | clone | stable disposition/reason/args、fake timers、feedback ledger、A/B canvas/node/surface/attempt owners | reject/noop/start/complete/fail/stale/duplicate、edit/retry/close/switch/delete/undo/burst | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` | clone | node/edge/primary selection sets、editable/surface/modal/Director zones、focus origin/fallback、A/B canvas generations | click/multi-select/edge select、Delete/undo/redo、editable isolation、modal/Director precedence、single Escape、switch/delete/undo | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` | clone | Batch 63/64/65 fresh Page slices + future canvas generation/host epoch、distinct stable viewports、actual host full/asset-open/compact rect、nested/top-level measured nodes、fake viewport operation IDs | conversion、host-center add、Asset resize、bootstrap/stable breakpoint、A/B restore、stale/invalid callback；future pan/zoom end/cancel、browser resize、drag/organize/placement/overlay composition | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `FOCUSED_RUNTIME_PARTIAL` |
| `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` | clone | synthetic files、deterministic classifier/probe/materializer clock、ingress/attempt/cohort/asset/reference aliases、lease/reachability counters | chooser cancel、invalid/mixed/out-of-order cohort、replace/retry/delete/switch races、history/asset attach、blob/data/route cases | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` | clone | deterministic text/config/record/range/request/empty owners、small bitmap buffers、session/source versions、fake async/resource/focus/history oracles | dirty/noop/cancel/blur、gesture/undo/redo/reset、drift/IME/delete/switch、submit race/late result、budget eviction、inert-control honesty | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` | clone | deterministic ratio/media/output/request/frame/rendition/content-box descriptors + invalid metadata + fake measurement clock | frame derivation、same/mixed output、thumbnail/full/poster swap、fit/editor round-trip、status/stale/detail/route cases | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` | clone | Batch 67 V1 snapshot with scene、character/prop/camera、group、four track kinds、edited path、resource/capture descriptor；Batch 68 A/B route/canvas/source owners、session generations、memory capture sidecar；Batch 69 authored/runtime fingerprints；Batch 70 command/history fixture；Batch 71 Inspector/R3F/free-draw gesture fixture；Batch 72 reference-closure/delete fixture；Batch 73 async authority/resource ledger fixture；Batch 74 browser-local persistence envelope and reload/failure fixture；Batch 75 project-scoped clipboard packet and deterministic ID provider；Batch 76 all-canvas live owner/reconciliation fixture | implemented codec round-trip/reject/isolation plus create/focus/restore/close/reopen/active-delete/duplicate-reset/cross-canvas owner isolation、seek/playback/path/object/camera/pose authored stability、semantic history、no-op/rejection、gesture coalescing、undo/redo、Inspector/R3F/free-draw commit/cancel/pointercancel、object/group/camera/track/path/capture/resource closure、capture/export/phone owner/source/attempt/result convergence、resource transfer/release exactly once、reload restore、stale save、runtime/UI/resource-byte exclusion and storage failure continuity、clipboard typed closure/two-pass remap、camera detach/freeze、resource alias/conflict、one-entry history、A-B-A/reload isolation、inactive source/canvas tombstone、active two-phase cleanup、repeated reconciliation、graph undo and retained persistence；future ordinary canvas async/persistence、durable tombstone/storage/resource cleanup and whole-project duplicate | `PURE_CODEC_RECORDED_PASS` / `OWNER_SESSION_FOCUSED_PASS` / `AUTHORED_RUNTIME_FOCUSED_PASS` / `HISTORY_FOCUSED_PASS` / `POINTER_LIFECYCLE_FOCUSED_PASS` / `REFERENCE_DELETE_FOCUSED_PASS` / `ASYNC_AUTHORITY_FOCUSED_PASS` / `PERSISTENCE_FOCUSED_PASS` / `CLIPBOARD_REMAP_FOCUSED_PASS` / `OWNER_REACHABILITY_FOCUSED_PASS` |
| `LIBTV-FIX-LOCAL-PROCESS-STATES-01` | clone | 固定 pending/failed/partial/success/retry data | UI lifecycle、graph delta、selection、undo/redo | `REQUIRED_DISPOSABLE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING` |
| `LIBTV-FIX-LOCAL-SHORTCUT-01` | clone | 固定 node/group/internal/external-edge subgraph | handler precondition、focus guard、graph closure、history | `REQUIRED_DISPOSABLE` |

`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` 的当前实现状态以 Batch 67-76
专题台账为准：reference-aware delete/resource closure、Director async authority、
browser-local persistence、same-project clipboard remap 和 all-canvas owner
reachability 均已有 focused pass；
下方旧 fixture 说明只保留历史设计语境。
`LIBTV-FIX-LOCAL-AUTOLINK-01` 的 topology、deterministic controls、setup/reset 和 verifier split 见 [`components/LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md#9-fixture-acceptance-and-verifier-split)。`LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` 的 A/B/C topology、direction/duplicate/self/cycle 场景、reason precedence 和 `VR-009` split 见 [`components/LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md#11-fixture-contract)，其 Batch 57 local runtime 结果见 [`liblib-canvas-batch57-2026-08-27/`](liblib-canvas-batch57-2026-08-27/)。`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` 的 payload corpus、strict load、nested isolation、media diagnostics 和 `VR-010` split 见 [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md#9-fixture-contract)。`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` 的 group/child/external/derived topology、reference roles、placement、history 和 `VR-011` split 见 [`components/LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md#12-fixture-contract)。`LIBTV-FIX-LOCAL-NODE-DATA-01` 的 11-type corpus、field roles、operation profiles、aggregate/media cases 和 `VR-012` split 见 [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md#12-fixture-contract)。`LIBTV-FIX-LOCAL-GRAPH-DELETE-01` 的 plain/group/derived/shot/process/canvas/media scenes、repair policies 和 `VR-013` split 见 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md#14-local-fixture-contract)。`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` 的 composed aliases、same-proposal ingress、T0-T5 routing、restore/remote cases 和 `VR-014` split 见 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md#13-local-fixture-contract)。`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` 的 identity aliases、controlled completion、stale/duplicate/retry/delete/UI/resource cases 和 `VR-015` split 见 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md#14-libtv-fix-local-async-ingress-01)。`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` 的 exact variant、mixed batch、stale snapshot、history 和 sanitation cases 见 [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md#15-focused-fixture-catalog)。`LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` 的 A/B/C owner、switch/duplicate/delete、transient/async/resource race cases 见 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md#11-local-fixture-contract)。`LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` 的 disposition/reason/primary-surface、timer/retry/dedupe/switch/delete/burst cases 见 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md#13-local-fixture-contract)。`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` 的 selection normalization、focus zone、dispatch/Escape precedence、switch/delete/undo 和 focus-return cases 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md#13-local-fixture-contract)。`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 的 six-domain conversion、actual host、live/stable viewport、gesture owner、placement/resize/overlay cases 见 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md#17-local-fixture-contract)，其 Batch 63/64/65 focused runtime 结果见对应 batch 目录。`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` 的 ten entry profiles、classifier/probe/materializer clock、cohort/replace/race、asset/reference/reachability、lease counter cases 见 [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md#21-local-fixture-contract)。`LIBTV-FIX-LOCAL-EDITOR-SESSION-01` 的 text/config/record/range/request/bitmap aliases、drift/undo/commit/async/budget cases 和 `VR-022` split 见 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md#22-libtv-fix-local-editor-session-01)。`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` 的 ratio corpus、intrinsic/request/frame/rendition authority、mixed outputs、fit/editor transform、measurement clock and `VR-023` split 见 [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md#18-libtv-fix-local-media-rendition-01)。`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` 的 V1 valid/invalid/future/reference corpus 和 `VR-024` pure slice 见 [`liblib-canvas-batch67-2026-08-27/`](liblib-canvas-batch67-2026-08-27/)，owner/session focused browser slice 见 [`liblib-canvas-batch68-2026-08-27/`](liblib-canvas-batch68-2026-08-27/)，authored/runtime focused slice 见 [`liblib-canvas-batch69-2026-08-27/`](liblib-canvas-batch69-2026-08-27/)，command/history/gesture focused slice 见 [`liblib-canvas-batch70-2026-08-27/`](liblib-canvas-batch70-2026-08-27/)；reference-aware delete、async freshness、inactive-owner reconciliation 和 persistence 仍未实现。`LIBTV-FIX-LOCAL-PROCESS-STATES-01` 的五轴场景、stale/retry 和 source fixture 接收条件见 [`open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。除已标明 `RECORDED_PASS`、`PURE_CODEC_RECORDED_PASS`、`OWNER_SESSION_FOCUSED_PASS`、`AUTHORED_RUNTIME_FOCUSED_PASS` 或 `FOCUSED_RUNTIME_PARTIAL` 的局部 fixture 外，其余列出的 fixture 仍是设计完成但运行 fixture 未实现。

上方历史长句中的 `reference-aware delete、async freshness、inactive-owner
reconciliation、persistence` 是旧版 fixture 叙述；当前状态以 Batch 72-76
专题台账为准：Director delete、Director
capture/export/phone async authority、browser-local project persistence 和
same-project clipboard remap、owner reachability 已分别通过 focused runtime，
普通画布 async/persistence、durable tombstone/storage/resource cleanup、
whole-project duplicate、remote storage 和 source parity 仍未实现。

### 6.1 源站 disposable fixture 的接收条件

开始任何写入型源站研究前，必须同时记录：

1. fixture owner 和独立 project/space 身份；
2. 允许的动作、积分/任务消耗上限和停止条件；
3. 初始 graph、node IDs、media version、duration/time range；
4. 每一步预期观测量和截图/DOM 输出路径；
5. 远端清理方式，以及谁确认没有遗留任务或版本；
6. 失败、中断、登录过期或 API 不可用时不继续试探的条件。

缺任一项，状态保持 `BLOCKED_BY_FIXTURE`。

### 6.2 本地 disposable fixture 的接收条件

本地 fixture 不等于随便写一组 demo data。它至少需要：

- deterministic ID 或稳定的 identity 查询方式；
- 明确 node/edge/selection/viewport/history 初始值；
- 区分 source ID、media version、operation、run、candidate 和 result；
- 不依赖真实网络、登录、Provider 或当前日期；
- 每个测试新 Page，或显式 setup/teardown 后断言完全复位；
- source fact、clone mock 和测试控制字段分开命名；
- 实施授权后才允许新增代码/测试 fixture。

## 7. Parity Backlog 映射

| Backlog | 最小 fixture | 当前可做 | 当前缺口/停止条件 |
|---|---|---|---|
| `LIBTV-PAR-001` | `LOCAL-DEMO-01` 或 `LOCAL-IMAGE-01` + `SOURCE-SHARED-01` | 合同/计划已足够；可继续只读 freshness | 编码和 replacement verifier 等待明确授权 |
| `LIBTV-PAR-002` | `LOCAL-IMAGE-01` + `SOURCE-SHARED-01` | Preview/Annotate/Element Edit 空态可规划 | dirty annotate/rotate/layer 需要 `SOURCE-IMAGE-DIRTY-01` |
| `LIBTV-PAR-003` | `LOCAL-AUTOLINK-01` + `SOURCE-AUTOLINK-01` | typed data/state/transaction design | 没有设计合同和 disposable source 时不编码、不输入共享 Prompt |
| `LIBTV-PAR-004` | 本地 page overlay states + `DIRECTOR-BASE-01` + `SOURCE-SHARED-01` | 可只读研究 keyboard/outside/focus | 不凭可访问性常识猜 source parity，不顺手建 modal manager |
| `LIBTV-PAR-005` | `SOURCE-SHARED-01` | 安全只读 page-shell freshness refresh | 不能修改共享 graph 或偏好；观察结果要带日期 |
| `LIBTV-PAR-006` | `LOCAL-VIDEO-READY-01` + `SOURCE-VIDEO-READY-01` | clone 侧历史工具回归可读 | source toolbar 继续 `BLOCKED_BY_FIXTURE` |
| `LIBTV-PAR-007` | `LOCAL-SHORTCUT-01` + `SOURCE-SHORTCUT-01` | 现有 help/handler crosswalk 可继续完善 | source-only 命令不得在共享 graph 试探 |
| `LIBTV-PAR-008` | `LOCAL-GRAPH-CONNECTION-01` + `LOCAL-GRAPH-DOCUMENT-01` + `LOCAL-SUBGRAPH-COPY-01` + `LOCAL-NODE-DATA-01` + `LOCAL-GRAPH-DELETE-01` + `LOCAL-GRAPH-ENTRYPOINT-01` + `LOCAL-REACT-FLOW-CHANGES-01` + `LOCAL-DEMO/EMPTY/GROUP/DERIVED` | connection structural slice 已由 Batch 57 通过；document/copy/data/delete/entrypoint/React Flow routing contracts and `VR-010..016` remain design-complete | source invalid lifecycle/Reference/domain/Option-drag/cascade/detach；runtime transport/planner/restore boundaries missing；persistence deferred |
| `LIBTV-PAR-009` | `LOCAL-LONG-PROCESS-01`、`LOCAL-PROCESS-STATES-01`、`LOCAL-ASYNC-INGRESS-01`、`SOURCE-PROCESS-01` | 状态与 async ingress 接收规格已设计；当前可记录 bounded mock topology | runtime fixture、真实 lifecycle/局部重算继续被编码授权、source fixture 和业务接口阻塞 |
| `LIBTV-PAR-010` | `LOCAL-DEMO-01` | 显式 local mock boundary 已可验证 | 不升级为真实服务承诺 |
| `LIBTV-PAR-011` | 静态 store/runtime 审计 | 文档已有冗余/unmounted state 清单 | 没有编码授权不清理 store |
| `LIBTV-PAR-001/002/007/008/011` spatial cross-cutting | `LOCAL-VIEWPORT-COORDINATE-01` + existing image/graph/lifecycle fixtures | six-domain、actual-host、live/stable、gesture/placement/overlay fixture design complete | runtime fixture/adapter 未实现；exact source add/zoom/resize/drop 仍需独立证据；未授权编码 |
| `LIBTV-PAR-008/009/010/011/014` media ingress cross-cutting | `LOCAL-MEDIA-INGRESS-01` + graph/async/delete/document/lifecycle/feedback fixtures | ten entry profiles、classifier/probe/materializer、cohort/replace、asset/reference、lease/reachability fixture design complete | runtime fixture/common owner 未实现；source limits/progress/cancel/placement/register/restore 需 disposable fixture；未授权编码 |
| `LIBTV-PAR-004/008/009/011/015` editor session cross-cutting | `LOCAL-EDITOR-SESSION-01` + graph/async/lifecycle/feedback/selection/resource fixtures | ten profiles、baseline/draft、native/local/graph undo、commit/close/drift/budget/honesty fixture design complete | runtime fixture/common owner 未实现；source blur/Escape/restore/save/close 需 disposable fixture；未授权编码 |
| `LIBTV-PAR-001/002/008/009/011/014/015/016` media rendition cross-cutting | `LOCAL-MEDIA-RENDITION-01` + image/video/overlay/viewport/editor/media-ingress fixtures | ratio corpus、authority/frame/rendition/fit/output/measurement/editor-transform fixture design complete | runtime fixture/policy 未实现；source portrait/square/video/mixed-output/resize 需 `SOURCE-MEDIA-RENDITION-01`；未授权编码 |
| `LIBTV-PAR-012` | 无 | 记录 scope boundary | Provider/计费/远端持久化是 `OUT_OF_SCOPE` |
| `LIBTV-PAR-013` | `DIRECTOR-LOCAL-MODEL-01` | Batch 48 已形成 recorded pass；读取其稳定 verifier 和 reset 合同 | 不把 local descriptor/proxy 升级为真实资产或远端持久化 |

表内简称省略了 `LIBTV-FIX-` 前缀。

## 8. Verifier 使用规则

### 8.1 新场景优先顺序

```text
pure helper/data contract
  -> new Page + existing baseline
  -> empty canvas + real UI construction
  -> transaction-derived state
  -> direct store driving only when domain contract already exposes it
  -> source observation kept in a separate research script/run
```

不要先增加全局 fixture injector。只有多个授权 slice 确实重复同一套复杂 setup，且真实 UI 构造导致不稳定或无法表达失败态时，才评审测试 helper 或 fixture factory。

### 8.2 每个 verifier 的最小前置断言

- 当前 URL、viewport 和目标 canvas；
- 初始 node/edge 数量；
- 目标 node identity、type 和关键 status；
- selection 初态；
- history 若为被测对象，先证明 past/future 起点；
- active overlay/tool 未被前一场景遗留；
- 对 localStorage 有依赖时，显式记录 key 和清理验证；
- console error、page error 和必要 request error collection 已安装。

### 8.3 有 graph mutation 的最小后置断言

- 精确 node/edge delta，而不只断言“出现了卡片”；
- 新节点的 source/result/version/operation metadata；
- selection output；
- undo 一次是否完整移除本 transaction；
- redo 一次是否恢复同一 identity/metadata 或合同允许的新 identity；
- viewport/overlay 是否按合同保留或关闭；
- 最后丢弃 Page，不把场景状态交给下一项测试。

### 8.4 串行执行

现有 Batch verifier 共用本地 dev server，并会覆盖带固定日期文件名的视觉参考；因此继续串行运行。文档-only 工作不自动运行这些脚本，以免触碰共享截图 WIP。

## 9. Fixture 记录模板

新增 fixture 时复制以下字段到 PLAN 或本文：

```text
Fixture ID:
Environment: local clone / disposable source / shared source / Director
Owner:
Purpose and parity IDs:
Construction path:
Stable identities:
Initial graph/selection/viewport/history:
Media/run/version state:
Allowed actions:
Forbidden actions:
Expected graph/UI/storage side effects:
Reset method:
Reset assertions:
Evidence output paths:
Authorization status:
Stop conditions:
Supersedes:
```

不得用“刷新即可”“可撤销”“测试数据”替代 reset method 和 reset assertions。

## 10. 下一步文档/研究顺序

1. 用本文完成 `PAR-005` source freshness refresh 的观察 checklist，不操作共享 graph；
2. 保持 `PAR-003` AutoLink，以及 `PAR-009` process-state/async-ingress fixture 接收规格为文档权威；运行 fixture 等待独立编码授权；
3. 保持 `PAR-008` 的 document/snapshot、subgraph copy、node data identity、relation-aware delete 与 graph entrypoint authority fixture/result/verifier contract 为 `DESIGN_SPEC_COMPLETE`；Batch 57 structural connection slice 和 Director Batch 72 reference-aware delete slice 已有实现和记录，其余普通 graph runtime 仍 missing/partial，Reference/domain/source invalid lifecycle 不扩展；
4. 为 `PAR-007` 设计 local shortcut subgraph，不修改实现；
5. 等用户提供独立源站 project/权限后，再启用 `SOURCE-GRAPH-CONNECTION-01`、`SOURCE-GRAPH-DELETE-01`、`SOURCE-VIDEO-READY-01` 等真实 fixture identity；
6. 继续维护 `DIRECTOR-LOCAL-MODEL-01` 的 storage reset、fresh-context 和 proxy-cleanup 断言；
7. 获得编码授权后，每个 parity slice 单独新增 fixture、verifier、screenshot ledger、implementation 和 commit。

## 11. Maintenance

以下事件必须更新本文：

- `initialCanvas2` 节点/边/ID/viewport 改变；
- default image/video data 或 Add Node 构造路径改变；
- canvas store 获得 persistence、window debug API 或正式 reset action；
- history snapshot 深度或 selection/viewport policy 改变；
- Director 新增/移除 browser persistence；
- disposable source fixture 获得 owner、权限或被销毁；
- parity backlog item 的 fixture 状态从 blocked 升级为 available；
- graph connection reason/result、Reference policy 或 accepted/rejected history contract 改变；
- graph document schema、node data version、media portability、snapshot isolation 或 import transaction 改变；
- subgraph copy command、edge policy、parent closure、reference role、placement 或 clipboard packet 改变；
- runtime node type、dataVersion、identity role、aggregate closure、status reset 或 media locator policy 改变；
- verifier 改用新的 setup/teardown 策略。

维护时同时检查 [`HARNESS.md`](../HARNESS.md)、[`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)、[`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md) 和对应 Batch 实施记录。
