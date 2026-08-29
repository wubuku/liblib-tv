# 验证能力台账

> 目的：区分“有研究目录”“有 verifier”“最近有记录通过”“只有源站合同”“被 fixture 阻塞”和“并行 WIP”，防止把不同成熟度混成一个绿色状态。
>
> 本台账只记录当前仓库可发现的验证能力。Batch 50 的浏览器脚本、
> 截图和实施结果已经单独落档；后续批次仍需按同样边界增量维护。
> fixture 身份/隔离/reset 见 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)，
> 历史断言迁移见 [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)，
> Director 当前脚本分级见 [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)，
> 跨项目闸门见 [`../DECISION_REGISTER.md`](../DECISION_REGISTER.md)。

## 1. 状态词汇

| 状态 | 含义 |
|---|---|
| `SCRIPT_AVAILABLE` | 仓库中存在对应专项 verifier，可以按其自身断言运行 |
| `SCRIPT_RECORDED_PASS` | 实施记录或历史日志明确记录过通过；仍需看日期和合同版本 |
| `SOURCE_CONTRACT_ONLY` | 有当前源站 DOM/bundle/截图合同，但没有对应 clone verifier |
| `CLONE_FIXTURE_ONLY` | clone 有本地 fixture/实现记录，但不能证明源站当前行为 |
| `HISTORICAL_CONTRACT` | 只对旧日期 clone 快照有效，不能覆盖当前源站差异 |
| `BLOCKED_BY_FIXTURE` | 需要 ready-video、独立源站项目或其他安全前提，当前不能操作 |
| `PARALLEL_WIP` | 研究或实现目录由其他并行工作推进，尚未纳入稳定门禁 |
| `OUT_OF_SCOPE` | 当前前端原型不验证真实 provider、上传、计费或远端持久化 |

## 2. 脚本覆盖范围

### 2.1 实际存在的 LibTV verifier

当前仓库实际存在：

```text
Batch 4-33
Batch 35-50
Batch 51-54
Batch 56-60
Batch 61-65
Batch 67-88
Batch 77
Batch 78
Batch 79-84
```

Batch 34 没有专项 verifier，是导演台代码考古/研究批次。不要使用会隐式跨过 Batch 34 的 `{4..44}` shell glob。
Batch 57 有独立的普通连接事务 verifier。
Batch 58 有独立的 node-bound UI owner lifecycle verifier。
Batch 59 有独立的 Director asset-library search/preview/add verifier。
Batch 60 有独立的普通图片双浮层 owner/pointer boundary verifier。
Batch 61 有独立的 React Flow change routing/runtime selection verifier。
Batch 67 有独立的 Director Project Document V1 pure codec verifier，不需要浏览器。
Batch 68 有 pure registry verifier 和 fresh-page Director owner/session browser verifier。
Batch 69 有 pure static projection verifier 和 fresh-page authored/runtime browser verifier。
Batch 70 有 pure static command/history verifier 和 fresh-page
project-local history/gesture browser verifier。
Batch 71 有 pure pointer-lifecycle source verifier 和 fresh-page gesture browser verifier。
Batch 72 有 pure reference-aware delete planner verifier 和 fresh-page
delete/resource-closure browser verifier。
Batch 73 有 pure async-authority verifier 和 fresh-page
capture/export result-authority browser verifier。
Batch 74 有 pure persistence verifier 和 fresh-page
reload/storage-failure BrowserContext verifier。
Batch 75 有 pure clipboard packet/remap verifier 和 fresh-page
keyboard/history/project-isolation BrowserContext verifier。
Batch 76 有 pure owner-reachability planner verifier 和 fresh-page
active/inactive/cross-canvas reconciliation verifier。
Batch 77 有 source-aligned canvas navigation + Director TransformControls hybrid
verifier，使用 fresh pages、真实 wheel/mouse pointer 输入和静态 attachment contract。
Batch 78 有 Director pointer cancellation hybrid verifier，使用 fresh pages、真实
mouse pointer、pointer capture、gesture/history 和 stale-pointer 输入，不写截图。
Batch 79 有 whole-project duplicate hybrid verifier，使用 pure two-pass planner 和
fresh-page graph/Director isolation，不写截图。Batch 80 有 durable tombstone/
resource-cleanup hybrid verifier；Batch 81 有 strict project import/export hybrid
verifier；Batch 82 有 local resource materialization hybrid verifier；Batch 83 有
Director command feedback hybrid verifier，均使用 pure corpus + fresh
BrowserContext，不写截图。Batch 84 同样使用 pure source corpus + fresh
BrowserContext，不写截图；Batch 85 增加 selection/CRUD discoverability hybrid
verifier，Batch 87 增加 restore-selection hybrid verifier，Batch 88 增加
selection/timeline authority hybrid verifier，Batch 89 增加
scene-settings/add-camera hybrid verifier，仍使用 pure source corpus + fresh
BrowserContext，不写截图。

### 2.2 脚本分组台账

| 脚本范围 | 主题 | 当前状态 | 主要限制 |
|---|---|---|---|
| `verify-liblib-batch4.py` - `batch8.py` | 分组、多选、移动、复制、导航、整理、视频 parent-child | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 只覆盖各批 clone 合同，不是全量源站回归 |
| `verify-liblib-batch9.py` - `batch11.py` | 图片/视频浮层、图片编辑状态、顶层 overlay 生命周期 | `SCRIPT_AVAILABLE` / `HISTORICAL_CONTRACT` | Batch 9 的 `900.5px`/旧 top gap 仍是 compatibility；Batch 51 单独覆盖 source-confirmed top gap；Batch 10 的旧 AutoLink 不覆盖当前合同 |
| `verify-liblib-batch12.py` - `batch20.py` | 资产、分镜、Agent/share、canvas metadata、zoom、minimap、全景 | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 依赖本地 demo 数据和当时的 clone 状态 |
| `verify-liblib-batch21.py` - `batch25.py` | Seedance 参数/模型、片段重拍、逐帧拉片、智能剪辑空态 | `SCRIPT_AVAILABLE` / `CLONE_FIXTURE_ONLY` | 结果任务、ready-video 源站入口和真实 provider 未验证 |
| `verify-liblib-batch26.py` - `batch33.py` | 续写、去字幕、音视频分离、帧截取、主体编辑、深度、长视频 | `SCRIPT_AVAILABLE` / `CLONE_FIXTURE_ONLY` | 主要验证本地 graph、状态和 undo；源站结果态存在 fixture 阻塞 |
| `verify-liblib-batch35.py` - `batch50.py` | Director R3F、时间轴、路径、导出、手机相机、角色、跟随、运镜、群组/群众、截图图库、模型库、本地模型导入/持久化、视口坐标控件、workspace shell 折叠和键盘边界 | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 是有界 prototype 回归；不是 LibTV/FrameOS 通用行为合同 |
| Batch 34 | Director 既有代码考古和可借鉴性 | `SOURCE_CONTRACT_ONLY` | 没有专项 verifier，不应在全量命令中伪造 |
| Batch 45 | Director character groups/crowd/group tracks | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-45 serial regression 已通过；仍是有界 clone 合同 |
| Batch 46 | Director camera screenshot gallery and bulk return | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-46 serial regression 已通过；仍是有界 clone 合同 |
| Batch 47 | Director model-library categories, proxy insertion and responsive panel | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-47 serial regression 已通过；模型/环境真实资产仍明确不在合同内 |
| Batch 48 | Director local model import, persistence, refresh, re-add and delete cleanup | `SCRIPT_RECORDED_PASS` | focused Playwright 已通过；只验证 clone-owned browser-local descriptors 和 proxy objects；Batch 82 后仍应把真实 FBX/OBJ materialization 视为后续补充，不改写本批历史边界 |
| Batch 49 | Director viewport native coordinate gizmo | `SCRIPT_RECORDED_PASS` | focused Playwright、截图台账、实施记录和 clone-owned 成熟度已闭环；仍不代表 LibTV source-exact renderer/CSS |
| Batch 50 | Director workspace collapse and keyboard boundary | `SCRIPT_RECORDED_PASS` | focused Playwright、四态截图台账、实施记录和 clone-owned 成熟度已闭环；LibTV Director shell exact DOM/CSS、完整 focus trap 和 source “全屏”语义仍未知 |
| Batch 51 | ordinary canvas image toolbar zoom-aware top host geometry | `SCRIPT_RECORDED_PASS` | focused Playwright、结构化 runtime audit 和截图台账已闭环；仅完成 clone-owned geometry，source current action set 和 active image tools 仍未复刻 |
| Batch 52 | current image toolbar action set and page-level read-only Preview | `SCRIPT_RECORDED_PASS` | focused Playwright、desktop/mobile runtime audit、一次性截图台账、Batch 10/11 adjacent regression 和 closeout 文档已闭环；高风险 active tools 仍是独立后续批次 |
| Batch 53 | image annotate empty replacement state | `SCRIPT_RECORDED_PASS` | focused Playwright、desktop/mobile runtime audit、截图识别台账、Batch 52/10/11 adjacent regression 和 closeout 文档已闭环；真实 stroke/save/upload/result 仍不在合同内 |
| Batch 54 | image element-edit empty replacement state | `SCRIPT_RECORDED_PASS` | focused Playwright、desktop/mobile runtime audit、截图识别台账、Batch 53/52/10/11 adjacent regression 和 closeout 文档已闭环；真实 record/object recognition/generate/save/result 仍不在合同内 |
| Batch 55 | source freshness reinspection attempt | `BLOCKED_BY_FIXTURE` | 目标画布重定向首页，浏览器插件版本路径异常；仅完成 blocked handoff，不产生 clone/source parity 结论 |
| Batch 56 | image rotate bounded graph slice | `SCRIPT_RECORDED_PASS` | focused Playwright、desktop/mobile runtime audit、截图识别台账和 closeout 文档已闭环；只证明 media-gated `旋转与镜像` 派生 node/edge/selection/history，不证明真实 bitmap/editor/save/provider |
| Batch 57 | ordinary graph connection normalization, structural guards and zero-mutation transaction boundary | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch57.py` 已通过；覆盖真实 Handle drag、target-start、duplicate/reverse/parallel/self/cycle reject、one-step history、undo/redo、desktop/mobile overflow 与诊断错误；不覆盖 Reference/domain/source invalid feedback/import/sync |
| Batch 58 | node-bound UI owner invalidation and canvas boundary cleanup | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch58.py` 已通过；覆盖纯 reconciliation、preview/annotate/element-edit/Director 删除关闭、四类 owner 换画布关闭、delete-only history、desktop/mobile overflow 与诊断错误；不证明源站 destructive delete、资源回收或完整 relation-aware delete planner |
| Batch 59 | Director asset-library search, preview-only selection and explicit proxy insertion | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch59.py` 已通过；覆盖五分类、搜索、空结果、preview 不写场景、显式加入、对象树/Inspector continuity、desktop/mobile bounds、WebGL nonblank 和普通 graph isolation；不证明真实 asset loading、远程资源或认证后 LibTV exact UI |
| Batch 60 | ordinary image double-overlay owner continuity and pointer boundary | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch60.py` 已通过；覆盖 standard toolbar/panel owner 一致性、selection migration、几何不变量、非交互 panel boundary、textarea/button interaction、active-tool replacement、空白卸载、graph/history isolation、desktop/mobile bounds 和 diagnostics；pointer routing 是 clone-owned decision，不证明源站重叠命中语义 |
| Batch 61 | React Flow whole-batch routing and runtime selection ownership | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch61.py` 已通过；覆盖 exact 12.11.1 change corpus、current snapshot、semantic zero-partial reject、node/edge session selection、drag/measurement/history sanitation、stale race、desktop/mobile bounds 与 diagnostics；不证明 LibTV 源站使用 React Flow，也不覆盖 primary/focus、resize/reconnect 或完整 portable codec |
| Batch 62 | selection command snapshot and one-Escape context | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch62.py` 已通过；覆盖 validated node/edge snapshot、captured node command target、editable/IME pass-through、8 类 blocking foreground surface 的 keyboard suspension、single-layer Escape、canvas focus fallback、pane cleanup、desktop/mobile bounds 与 diagnostics；不证明 source-exact modal/focus、universal mixed primary、mixed edge command、focus trap 或 Asset/Agent containment |
| Batch 67 | Director Project Document V1 strict codec | `PURE_CONTRACT_RECORDED_PASS` | `verify-liblib-batch67.py` 已通过；覆盖 valid round-trip、17 个 malformed/future/unknown/duplicate/dangling/non-finite rejection、zero-partial、input isolation、runtime/media-byte exclusion 和 authoring-order preservation；不证明 owner registry、store integration、history/delete、persistence 或 source parity |
| Batch 68 | Director structured owner registry and session lifecycle | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch68.mjs` 与 `verify-liblib-batch68.py` 已通过；覆盖 structured owner-key collision resistance、create/focus/restore/close/reopen、session/generation、A-B-A/cross-canvas isolation、duplicate reset、active-delete tombstone compatibility、memory capture sidecar 与普通 graph/history isolation；all-canvas reachability 和 two-phase cleanup 由 Batch 76 接续 |
| Batch 69 | Director authored/runtime object authority | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch69.mjs` 与 `verify-liblib-batch69.py` 已通过；覆盖 authored source discoverability、seek/playback/keyframe/speed-curve/path/camera-preset fingerprint stability、object/camera/pose authoring、close/reopen、A-B-A 和普通 graph/history isolation；不证明 async freshness、Director history/reference-aware delete、persistence、真实资源或 source parity |
| Batch 70 | Director project-local command/history/gesture kernel | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch70.mjs` 与 `verify-liblib-batch70.py` 已通过；覆盖 typed command result、semantic one-entry mutation、same-value/no-op、invalid/missing-target rejection、repeated gesture coalescing、undo/redo、redo truncation、A/B owner isolation、close/reopen continuity 和 ordinary graph/history isolation；不证明 Inspector/pose/path/free-draw 全部 pointer lifecycle、reference-aware delete、async freshness、persistence 或 source parity |
| Batch 71 | Director pointer lifecycle and gesture cleanup | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch71.mjs` 与 `verify-liblib-batch71.py` 已通过；覆盖 Inspector numeric、pose、camera、path anchor/Bezier、path transform、pencil/pen 的 commit/cancel/pointercancel、gesture coalescing 和 ordinary graph/history isolation；不证明 reference-aware delete、async freshness、persistence、real resources 或 source parity |
| Batch 72 | Director reference-aware delete and resource closure | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch72.mjs` 与 `verify-liblib-batch72.py` 已通过；覆盖 object/group/camera/track/path/capture/resource closure、camera fallback、last-camera reject、resource block/cascade、selection/runtime repair、exact delete/undo/redo 和 ordinary graph isolation；不证明 inactive-owner reconciliation、async freshness、persistence、copy/paste identity remap、real resources 或 source parity |
| Batch 73 | Director capture/export/phone async result authority | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch73.mjs` 与 `verify-liblib-batch73.py` 已通过；覆盖 operation/attempt identity、owner/session/generation 与 source/request fingerprint、retry supersession、duplicate/terminal conflict、invalid/stale zero mutation、capture/export projection 和 resource transfer/release exactly once；不证明普通画布 async ingress、durable persistence、真实 provider/resource loader 或 source parity |
| Batch 74 | Director browser-local durable project persistence | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch74.mjs` 与 `verify-liblib-batch74.py` 已通过；覆盖 versioned envelope、strict restore、capture byte/runtime/UI exclusion、stale save completion、corrupt/future/owner/project rejection、reload authored restore、A/B key isolation、ordinary graph isolation 和 simulated quota/session-only continuity；不证明普通画布 persistence、remote storage、真实资源 materialization 或 source parity |
| Batch 75 | Director project-scoped clipboard identity remap | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch75.mjs` 与 `verify-liblib-batch75.py` 已通过；覆盖 typed object/group/track/path closure、object/group/track/path/keyframe/anchor two-pass remap、internal/external camera policy、stable resource alias/conflict、deterministic repeated offset、one-entry paste、exact undo/redo、editable/IME/gesture/busy/viewer guard、A-B-A/reload boundary 和 ordinary graph isolation；不证明 system/cross-project clipboard、whole-project duplicate、real resource transfer 或 source parity |
| Batch 76 | Director all-canvas owner reachability reconciliation | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch76.mjs` 与 `verify-liblib-batch76.py` 已通过；覆盖 all-canvas live owner、inactive source/canvas tombstone、active shell/session/runtime two-phase cleanup、rename/switch/unrelated isolation、重复幂等、tombstoned reopen reject、delayed async stale、graph undo 不复活 project、retained persistence 和 ordinary graph history；不证明 durable tombstone、storage/resource cleanup、whole-project duplicate 或 source parity |
| Batch 77 | source-aligned canvas navigation and Director TransformControls binding/gesture cleanup | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch77.py` 已通过；覆盖普通纵/横 wheel 平移、默认中键平移、`Space`/`H` 左键平移、`V` 空白拖动 no-op、`Command`/`Control` wheel 缩放、mobile overflow、真实 Director mug gizmo pointer drag、authored/runtime 同步、one-entry undo/redo、zero-distance zero-history、pointer cleanup、static explicit attachment 和 graph/history isolation；不证明真实触摸板硬件、源站 Director exact DOM/CSS、源站内部实现或真实资产/provider |
| Batch 78 | Director pointer cancellation, cleanup and R3F teardown | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch78.py` 已通过；覆盖 Curve commit/cancel/pointercancel/blur/hidden/begin-rejected、Phone Vcam pointer capture cancel/blur/close/reuse、Timeline scrub cancel/hidden/reuse/stale-move prevention、R3F Canvas cross-owner teardown、zero screenshots 和 zero console/page/request errors；Batch 59、67-78 serial regression 亦通过；不证明源站 Director exact DOM/CSS、真实手机设备或 source parity |

| Batch 79 | Director whole-project duplicate | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch79.mjs` 与 `verify-liblib-batch79.py` 已通过；覆盖 graph/parent/edge 与 Director two-pass identity/reference remap、多 owner/project、fresh missing document、stable resource descriptor、non-portable resource reject、clean target history/session/clipboard、source/target persistence isolation 和 zero diagnostics；不证明 LibTV source duplicate、真实资源 materialization 或 capture/history copy |
| Batch 80 | Director durable tombstone 与安全资源清理 | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch80.mjs` 与 `verify-liblib-batch80.py` 已通过；覆盖 strict tombstone envelope、durable load block、save resurrection guard、stale/malformed/write-failure boundary、active/inactive owner cleanup、capture sidecar 清空、shared/unshared local resource policy、reload reopen rejection、graph/Director history isolation 和 zero diagnostics；不证明 LibTV source delete/recovery、remote persistence 或真实资源 materialization |
| Batch 81 | Director strict project import/export | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch81.mjs` 与 `verify-liblib-batch81.py` 已通过；覆盖 strict V1 export/import、owner/project rebind、capture/runtime/UI exclusion、one-entry history、undo/redo、same-document no-op、invalid zero-partial、download/file-input round trip、ordinary graph/history isolation 和 zero diagnostics；不证明 LibTV source 文件格式/UI、remote sync 或真实资源 materialization |
| Batch 82 | Director local resource lifecycle and finite OBJ/FBX materialization | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch82.mjs` 与 `verify-liblib-batch82.py` 已通过；覆盖 typed descriptor/provenance、attempt freshness、retry/cancel/release、valid OBJ materialization、parse-failure proxy retention、unsupported-extension zero mutation、UI status feedback 和 zero diagnostics；不证明生产 loader/cache、复杂 FBX/纹理、remote persistence 或 LibTV source resource semantics |
| Batch 83 | Director command outcome feedback projection | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch83.mjs` 与 `verify-liblib-batch83.py` 已通过；覆盖 typed disposition/reason mapping、rejected/stale/conflict/meaningful-no-op visible feedback、committed generic feedback suppression、ARIA status semantics、mobile fixed-header geometry、zero-history feedback boundary 和 zero diagnostics；不证明 LibTV source feedback taxonomy、exact copy/color/placement 或 ordinary canvas unified feedback |
| Batch 84 | Director object-tree lock/visibility and locked-target edit protection | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch84.mjs` 与 `verify-liblib-batch84.py` 已通过；覆盖 lock/unlock、Inspector disabled controls、direct locked transform rejection、zero document/history mutation、visibility continuity、unlock recovery、mobile discovery 和 zero diagnostics；不证明 LibTV source Director lock UI、exact copy/color/placement、keyboard policy 或 source parity |
| Batch 85 | Director object-tree selection context and CRUD discoverability | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch85.mjs` 与 `verify-liblib-batch85.py` 已通过；覆盖 selection action bar、single/multi-selection count、project-scoped copy、clear zero-history、reference-aware batch delete、group context、mobile discovery 和 zero diagnostics；不证明 LibTV source Director selection bar、exact copy/color/placement、keyboard policy 或 source parity |
| Batch 86 | Director transform target context and pointer cancellation | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch86.mjs` 与 `verify-liblib-batch86.py` 已通过；覆盖 none/object/locked target context、Inspector position entry、real gizmo drag、authored/runtime sync、one-entry history、undo/redo、pointercancel/lost capture cleanup、mobile geometry 和 zero diagnostics；不证明 LibTV source Director gizmo/target context、exact copy/placement、lock feedback、undo selection policy 或 source parity |
| Batch 87 | Director undo/redo restore selection authority | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch87.mjs` 与 `verify-liblib-batch87.py` 已通过；覆盖 preserve-current restore policy、对象树/Inspector/Viewport/Timeline 一致性、失效对象/分组/track/path/anchor 清理、portable document 排除 selection 和 zero diagnostics；不证明 LibTV source Director undo selection policy、exact copy/placement 或 source parity |
| Batch 88 | Director selection/timeline/TransformControls authority | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch88.mjs` 与 `verify-liblib-batch88.py` 已通过；覆盖单对象 track normalization、多选清理、group track authority、Timeline 反向选择、keyframe/path/anchor ownership、delete repair、locked zero mutation、portable document/history boundary、mobile geometry 和 zero diagnostics；不证明 LibTV source Director selection/Timeline 联动、exact copy/placement、undo policy 或 source parity |
| Batch 89 | Director scene settings and add-camera discoverability | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch89.mjs` 与 `verify-liblib-batch89.py` 已通过；覆盖场景名称、ground/grid 显隐、背景/地面颜色、对象树/Inspector 双新增机位入口、camera object/track/keyframe、active-camera/selection、undo/redo、portable export、mobile geometry 和 zero diagnostics；不证明 LibTV source Director add-camera defaults、shot lifecycle、exact DOM/CSS 或 source parity |

Batch 51 的专项脚本仍是历史合同：2026-08-27 在当前代码上因旧
`900.5px` toolbar 断言失败，而当前 Batch 52 合同已是 `1092.5px`。该结果
记录为 `EXPECTED_HISTORICAL_MISMATCH`，不应通过回退当前图片工具条实现来“修绿”；
当前图片标准态应以 Batch 52 和 Batch 60 为准。

## 3. 当前源站合同覆盖

| 能力/合同 | 当前状态 | 已有证据 | 缺口/下一步 |
|---|---|---|---|
| 图片标准双浮层 | `SOURCE_CONTRACT` + `LOCAL_FIXTURE`（Batch 51/52） | [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、Batch 51/52 `runtime-audit.json` | standard toolbar/panel geometry and current action shell are covered; active-tool replacement remains separate |
| 当前顶部工具条 | `SOURCE_CONTRACT` + `LOCAL_FIXTURE`（Batch 52） | [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 52 | current `1092.5x49`, 13 actions, order, width, disabled boundary and natural clipping are covered |
| image Preview | `SOURCE_CONTRACT` + `LOCAL_FIXTURE`（Batch 52） | [`ImagePreviewOverlay.spec.md`](components/ImagePreviewOverlay.spec.md)、Batch 52 `runtime-audit.json` | page-level open/close/Escape, media ratio, watermark/close geometry and graph immutability are covered |
| active image tool | `SOURCE_CONTRACT` + `LOCAL_FIXTURE`（Batch 53 annotate empty + Batch 54 element-edit empty + Batch 56 rotate graph slice） | [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`liblib-canvas-batch53-2026-08-26/`](liblib-canvas-batch53-2026-08-26/)、[`liblib-canvas-batch54-2026-08-26/`](liblib-canvas-batch54-2026-08-26/)、[`liblib-canvas-batch56-2026-08-26/`](liblib-canvas-batch56-2026-08-26/) | annotate/element-edit empty replacement and rotate graph delta are covered; rotate editor/bitmap, layer separation, download and non-empty save/record semantics remain fixture-gated |
| Auto Link | `SOURCE_CONTRACT_ONLY` | [`LIBTV_AUTOLINK_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)、[`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md) | 需要 editor token、竞态和 graph/reference/mention 事务回归 |
| Seedance 普通/超长参数 | `SOURCE_CONTRACT_ONLY` + `CLONE_FIXTURE_ONLY` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 21/22 | 需区分源站采样值、clone 本地参数和真实 provider |
| 片段重拍 | `BLOCKED_BY_FIXTURE` | bundle 文案、文章证据、Batch 23 clone fixture | 需要 disposable ready-video source fixture 和时间范围/版本合同 |
| 逐帧拉片 | `BLOCKED_BY_FIXTURE` | 空态 DOM、文章结果截图、Batch 24 clone fixture | 需要 ready video 或本地固定结果 fixture 的结果/失败态 |
| 超长视频过程 | `CLONE_FIXTURE_ONLY` + `BLOCKED_BY_FIXTURE` | Batch 33 12/22 graph、文章/源站参数证据 | 需要源站过程图或稳定 mock 合同，不能把 clone graph 当源站事实 |
| 普通画布结构连接事务 | `SOURCE_CONTRACT` + `LOCAL_FIXTURE`（Batch 57） | source static audit、Batch 57 `runtime-audit.json`、`LibTVGraphConnection.contract.md` | structural normalize/guard/transaction 已覆盖；Reference、domain compatibility、invalid feedback、import/batch/sync 仍未覆盖 |
| 节点绑定 UI owner 生命周期 | `CLONE_FIXTURE_ONLY`（Batch 58） | [`liblib-canvas-batch58-2026-08-27/`](liblib-canvas-batch58-2026-08-27/)、[`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、delete impact matrix | clone 的 `canvasId + nodeId` owner reconciliation、删除/换画布 UI cleanup 已覆盖；源站删除语义、Director workspace/media resource lifecycle 仍未确认 |
| Director 资源库搜索/预览/加入场景 | `CLONE_FIXTURE_ONLY`（Batch 59） | [`liblib-canvas-batch59-2026-08-27/`](liblib-canvas-batch59-2026-08-27/)、Batch 47/48 model-library contracts | 搜索、preview-only selection、proxy insertion 和 Inspector continuity 已覆盖；真实模型/环境资产、远程同步、生产持久化和认证后 source-exact surface 仍未知 |
| Director 当前跨批次集成状态 | `HISTORICAL_RECORDED_PASS` + `CURRENT_RELIABILITY_GATES` + `MANIFEST_RECORDED` | [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、[`storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md`](storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md)、Batch 35-50/59/67-89 | 历史脚本仍按成本/副作用/当前价值分级；Batch 59 和 Batch 67-89 形成当前低成本可靠性闸门，Batch 83 增加 clone-owned Director feedback projection，Batch 84 增加 clone-owned lock/editability protection，Batch 85 增加 clone-owned selection/CRUD discoverability，Batch 86 增加 clone-owned transform target context/pointer cleanup，Batch 87 增加 clone-owned restore-selection repair，Batch 88 增加 clone-owned selection/timeline/TransformControls authority，Batch 89 增加 clone-owned scene-settings/add-camera discoverability；不能把历史通过汇总成 source parity，也不能把 Director current gates 推导成 ordinary canvas async/persistence、remote storage、复杂真实资源或 source-exact persistence |
| 普通画布导航与 Director gizmo gesture | `CURRENT_SOURCE` + `LOCAL_FIXTURE`（Batch 77） | [`liblib-canvas-batch77-2026-08-28/`](liblib-canvas-batch77-2026-08-28/)、[`CANVAS_NAVIGATION.md`](../CANVAS_NAVIGATION.md)、Batch 77 source navigation audit | wheel/middle/Space/H/V/modifier zoom、mobile overflow、TransformControls 真实拖动与 gesture cleanup 已覆盖；真实触摸板硬件、source-exact Director surface 和真实资源/provider 仍不在范围 |
| Director pointer cancellation and R3F teardown | `CLONE_FIXTURE_ONLY`（Batch 78） | [`liblib-canvas-batch78-2026-08-28/`](liblib-canvas-batch78-2026-08-28/)、[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、Batch 78 `runtime-audit.json`、Batch 68 teardown regression | Curve/Phone Vcam/Timeline 三类 clone pointer lifecycle、Director gesture cancel baseline、capture release、stale move prevention、R3F Canvas async teardown 防护已覆盖；不证明 LibTV source exact Director pointer behavior、真实触摸板或手机传感器 |
| `LIBTV-VR-024` Director project/session/command authority | `PROJECT_CODEC_FOCUSED_PASS` + `OWNER_SESSION_FOCUSED_PASS` + `AUTHORED_RUNTIME_FOCUSED_PASS` + `HISTORY_FOCUSED_PASS` + `POINTER_LIFECYCLE_FOCUSED_PASS` + `REFERENCE_DELETE_FOCUSED_PASS` + `ASYNC_AUTHORITY_FOCUSED_PASS` + `PERSISTENCE_FOCUSED_PASS` + `CLIPBOARD_REMAP_FOCUSED_PASS` + `OWNER_REACHABILITY_FOCUSED_PASS` + `WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS` + `DURABLE_TOMBSTONE_FOCUSED_PASS` + `IMPORT_EXPORT_FOCUSED_PASS` + `LOCAL_RESOURCE_MATERIALIZATION_FOCUSED_PASS` + `COMMAND_FEEDBACK_FOCUSED_PASS` + `LOCK_EDITABILITY_FOCUSED_PASS` + `SELECTION_CRUD_FOCUSED_PASS` + `TRANSFORM_CONTEXT_FOCUSED_PASS` + `RESTORE_SELECTION_FOCUSED_PASS` + `SELECTION_TIMELINE_AUTHORITY_FOCUSED_PASS` | [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)、[`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)、[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`、Batch 67-88 | Batch 67 strict codec、68 owner registry/session、69 authored/runtime、70 command/history、71 pointer lifecycle、72 reference-aware delete、73 Director async、74 browser-local persistence、75 same-project clipboard remap、76 all-canvas owner reachability、79 whole-project duplicate、80 durable tombstone/storage/resource cleanup、81 strict import/export、82 finite local resource materialization、83 command feedback projection、84 locked-target editability、85 selection/CRUD discoverability、86 transform target context/pointer cleanup、87 restore-selection repair 和 88 selection/timeline/TransformControls authority 均有 focused pass；ordinary canvas async/persistence、remote storage、复杂真实资源、普通画布统一 feedback 和 source parity 仍未实现 |
| 普通图片双浮层 owner/命中边界 | `CLONE_FIXTURE_ONLY`（Batch 60） | [`liblib-canvas-batch60-2026-08-26/`](liblib-canvas-batch60-2026-08-26/)、[`ImageNode.spec.md`](components/ImageNode.spec.md)、[`ImageEditPanel.spec.md`](components/ImageEditPanel.spec.md) | owner identity、selection migration、既有几何、panel controls 和 active-tool replacement 已覆盖；相邻节点被 panel 覆盖像素的真实源站 routing 未取得 |
| 普通画布 graph mutation ingress | `STATIC_CONTRACT_ONLY` + connection island `LOCAL_FIXTURE` | [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、`LIBTV-VR-014` design、Batch 57 | 全 writer/T0-T5 audit 已完成；derived/setter/copy/delete/restore/remote routing runtime 尚未验证或实现 |
| React Flow change transport | `SCRIPT_RECORDED_PASS` / `RUNTIME_PARTIAL` | [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、共同 12.11.1 types/reducer、Open Canvas/clone callback static audit、Batch 61 `runtime-audit.json`、`LIBTV-VR-016` | whole-batch classifier、current-snapshot routing、semantic zero-partial reject、edge session selection、drag/measurement/history sanitation 和 focused browser corpus 已通过；混合 primary/focus、resize/reconnect、portable document 全面 sanitation 仍未完成 |
| 多画布 lifecycle / owner isolation | `STATIC_CONTRACT_ONLY` / `RUNTIME_PARTIAL` | [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、Open Canvas list/route/hydrate/delete/save audit、Batch 16/58/65、`LIBTV-VR-017` design | clone 已有 per-canvas graph/viewport/history、switch selection cleanup、node-bound UI reconciliation、bootstrap-only responsive preset、stored viewport restore 和 current/old viewport callback guard；invalid target、generic page generation、organize/drag/connection、async/resource owner 隔离及完整 focused fixture仍未实现 |
| Command outcome / feedback ownership | `DIRECTOR_FOCUSED_RUNTIME_PASS` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、[`liblib-canvas-batch83-2026-08-29/`](liblib-canvas-batch83-2026-08-29/)、Open Canvas `OC-040..045`、clone local status/timer/Director paths、`LIBTV-VR-018` design | Director 已将 typed disposition/reason 投影到 fixed-header status surface，并验证 ARIA、rejection/no-op visibility、committed suppression、mobile geometry 和 zero-history boundary；普通画布 connection reject、local string/timer islands、clear/retry/dedupe、统一 owner 与 exact source placement/timeout 仍未实现 |
| Selection / focus / command context | `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`liblib-canvas-batch62-2026-08-27/`](liblib-canvas-batch62-2026-08-27/)、Open Canvas `OC-046..052`、Batch 50/61 | clone-owned selection snapshot、editable/IME、blocking foreground suspension、one-Escape、focus fallback 已通过 focused verifier；universal mixed primary、mixed edge command、focus trap、target-scoped containment 和 exact source modal/shortcut/focus 仍 partial |
| Viewport / coordinate / gesture / placement | `FOCUSED_RUNTIME_PASS` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`liblib-canvas-batch63-2026-08-27/`](liblib-canvas-batch63-2026-08-27/)、[`liblib-canvas-batch64-2026-08-27/`](liblib-canvas-batch64-2026-08-27/)、[`liblib-canvas-batch65-2026-08-27/`](liblib-canvas-batch65-2026-08-27/)、Open Canvas `OC-053..060`、Batch 6/7/16/18/19/51/60/61/62、`LIBTV-VR-020` | Batch 63 已通过 actual-host default add；Batch 64 已通过 Asset drawer host-center anchor；Batch 65 已通过 desktop/mobile bootstrap、stable viewport breakpoint preservation、A/B canvas restore、projection echo 和 stale/invalid callback zero mutation。完整 live/stable endpoint、generic generation/host epoch、browser resize anchor、derived/duplicate/organize/overlay composition 和 full fixture 仍未完成，exact source add/fit/resize behavior partial |
| Media ingress / asset-reference / resource lifecycle | `STATIC_CONTRACT_ONLY` / `RUNTIME_MISSING_OR_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、Open Canvas `OC-061..070`、source `LIBTV-SRC-MIR-001..006`、Batch 12/15/17/24/40/46/48/82、`LIBTV-VR-021` design | ordinary Add Resource/Shot/asset path 仍是 mock/partial；Director Batch 82 已有独立 typed local resource lifecycle 和有限 OBJ/FBX materialization，但不属于 ordinary common provider/resource registry；source limits/progress/cancel/placement/register/restore/backend 仍 partial |
| Foreground editor session / commit / local history | `STATIC_CONTRACT_ONLY` / `RUNTIME_FRAGMENTED` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)、Open Canvas `OC-071..080`、Text/Picture/Subtitle/image-mode/video-toolbar specs、`LIBTV-VR-022` design | local draft、gesture history、owner reconciliation and honest empty islands exist；common profile/session/baseline/undo/commit/close/async/resource owner and focused fixture remain missing，source blur/Escape/restore/save/close partial |
| Media rendition / aspect / node geometry | `STATIC_CONTRACT_ONLY` / `RUNTIME_FRAGMENTED` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)、Open Canvas `OC-081..090`、source `LIBTV-MRG-SRC-001..006`、Batch 9/29/31/52/53/54/60、`LIBTV-VR-023` design | ordinary image initial landscape、Director still and animation-method islands exist；generic/derived/Director still authorities diverge，per-output metadata、fit/editor transform、measurement epoch and focused fixture remain missing，source ratio-diverse/video/mixed-output/resize parity partial |
| 普通画布 async result ingress | `STATIC_CONTRACT_ONLY` / `DIRECTOR_FOCUSED_RUNTIME_PASS` / `ORDINARY_RUNTIME_MISSING` | [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、Batch 73、Open Canvas `OC-026..030`、`LIBTV-VR-015` design | Batch 73 已为 Director capture/export/phone 完成 operation/attempt identity、stale/duplicate convergence 和 resource ledger；普通画布 delayed writers、controlled shot-breakdown fixture、projection recovery 和 remote run/poll/cancel/retry 仍未实现 |
| 旋转编辑器/图层分离/标注保存 | `BLOCKED_BY_FIXTURE` | Batch 56 只覆盖旋转入口的 bounded graph delta；当前 bundle/live 空态和一次撤销边界 | 需要 disposable 项目、任务/保存许可和可回滚方案；不要把 Batch 56 graph slice 升级为真实 bitmap/editor parity |
| page shell/source freshness | `SOURCE_CONTRACT_ONLY` | Batch 55 记录了接管失败；既有 2026-08-27 standard image freshness 仍只覆盖 41% selected state | 需要恢复登录态后补 page shell、selection transition、safe zoom 和 mobile；不要把重定向解释成 source drift |

## 4. 如何解读“通过”

### 4.1 `SCRIPT_RECORDED_PASS` 不是当前源站一致

一个 Batch 脚本通过，只能说明其日期、fixture、selector 和断言下的 clone 行为满足要求。例如：

- Batch 9 的旧 `900.5px` 工具条断言仍能保护历史 clone 快照，但不代表当前源站动作集合；
- Batch 10 的固定 AutoLink 候选/前缀写回断言仍能描述旧 clone，不代表 structured mention；
- Batch 21-33 的本地过程图和任务状态是 prototype contract，不代表真实 provider 或源站结果态。

### 4.2 只有同时满足三层，才可称为当前 slice 已闭环

```text
源站合同（SOURCE_CONTRACT）
  + clone 实现/fixture（CLONE_FIXTURE）
  + 专项回归与最新实施记录（REGRESSION_RECORD）
```

缺任何一层，就在本台账保留更保守的状态，不升级为“完成”。

## 5. 授权后的验证命令

### 5.1 单批次

```bash
python3 scripts/verify-liblib-batch<N>.py
```

### 5.2 当前脚本全集

```bash
for script in scripts/verify-liblib-batch{4..33}.py scripts/verify-liblib-batch{35..50}.py scripts/verify-liblib-batch52.py scripts/verify-liblib-batch53.py scripts/verify-liblib-batch54.py scripts/verify-liblib-batch56.py scripts/verify-liblib-batch57.py scripts/verify-liblib-batch58.py scripts/verify-liblib-batch59.py scripts/verify-liblib-batch60.py scripts/verify-liblib-batch61.py scripts/verify-liblib-batch62.py scripts/verify-liblib-batch63.py scripts/verify-liblib-batch64.py scripts/verify-liblib-batch65.py scripts/verify-liblib-batch67.py scripts/verify-liblib-batch68.py scripts/verify-liblib-batch69.py scripts/verify-liblib-batch70.py scripts/verify-liblib-batch71.py scripts/verify-liblib-batch72.py scripts/verify-liblib-batch73.py scripts/verify-liblib-batch74.py scripts/verify-liblib-batch75.py scripts/verify-liblib-batch76.py scripts/verify-liblib-batch77.py scripts/verify-liblib-batch78.py scripts/verify-liblib-batch79.py scripts/verify-liblib-batch80.py scripts/verify-liblib-batch81.py scripts/verify-liblib-batch82.py scripts/verify-liblib-batch83.py; do
  python3 "$script" || exit 1
done
```

这些脚本会写入带日期的视觉参考或依赖本地 dev server，因此必须串行运行；文档-only 研究不应为了更新本台账自动执行它们。

### 5.3 Batch 83 current-gate closeout

Batch 83 的最终 current-gate 串行结果、固定端口、fixture drift、诊断和
artifact 边界见
[`liblib-canvas-batch83-2026-08-29/current-gate-regression.json`](liblib-canvas-batch83-2026-08-29/current-gate-regression.json)。
该记录只覆盖 Batch 59、67-83 的低成本 Director/导航回归，不替代历史全套
截图脚本，也不构成 LibTV source parity。

### 5.4 Batch 86 current-gate closeout

Batch 86 在固定 `localhost:4317` 上串行复跑 Batch 59、67–86，全部通过；结果、
截图成本、历史审计文件边界和零诊断记录见
[`liblib-canvas-batch86-2026-08-29/current-gate-regression.json`](liblib-canvas-batch86-2026-08-29/current-gate-regression.json)。
该结果仍是 clone-owned reliability gate，不提升为 LibTV source parity。

## 6. 台账维护规则

- 新增 verifier：同时更新本台账、[`HARNESS.md`](../HARNESS.md)、对应 Batch `IMPLEMENTATION.md` 和 `docs/research/README.md`；
- 修改断言：记录它覆盖的是历史合同还是当前源站合同；不能只改数字不改证据说明；
- 新增截图：先检查已有 `SCREENSHOT_ANALYSIS.md`，并记录 viewport、zoom、状态和来源；
- 被 fixture 阻塞：使用 `BLOCKED_BY_FIXTURE`，记录所需 fixture，不在共享项目试探；
- 并行 WIP：保留 `PARALLEL_WIP`，待该开发者的脚本、实施记录和验证结果稳定后再升级；
- 任何文档变更都运行 `python3 scripts/verify-docs.py`，并只提交自己的路径。
