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
Batch 67-96
Batch 77
Batch 78
Batch 79-93
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
scene-settings/add-camera hybrid verifier，Batch 90 增加 project/session-scene
command verifier，Batch 91 增加 object/camera/group command verifier，Batch 92
增加 local-resource lifecycle/lease verifier，Batch 93 增加最终桌面/移动端与
跨批回归 verifier，Batch 94 增加 Director focus-containment verifier；这些脚本均使用 pure source corpus 或 fresh
BrowserContext，不写截图。Batch 95 增加 canvas-media ingress verifier，Batch 96
增加 multi-camera/Shot verifier；两批均使用 pure source corpus 或 fresh
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
| Batch 90 | Director project/session diagnostics and scene semantic command | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch90.mjs` 与 `verify-liblib-batch90.py` 已通过；覆盖 session outcome/lifecycle diagnostics、scene draft、Enter/blur commit、typed scene command、persistence、one-entry history、no-op/rejection、undo/redo、mobile Inspector 和 zero diagnostics；不证明 LibTV source Director project/session/history/persistence semantics 或 source parity |
| Batch 91 | Director object/camera/group command and history boundary | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch91.mjs` 与 `verify-liblib-batch91.py` 已通过；覆盖对象属性、相机设置、角色组创建/重命名/变换、name draft/commit、camera reference validation、persistence、one-entry history、invalid/no-op zero mutation 和 zero diagnostics；不证明 LibTV source Director command/history/persistence semantics 或 source parity |
| Batch 92 | Director local resource lifecycle and session lease | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch92.mjs` 与 `verify-liblib-batch92.py` 已通过；Batch 82 历史 fresh-page verifier 已按当前 owner/lease 合同适配并通过；覆盖 strict descriptor/decoded-byte budget、owner-scoped request/lease、terminal invariant、deferred/final release、有限 OBJ materialization、失败 proxy、retry/cancel 和 zero diagnostics；不证明 LibTV source resource semantics、生产 loader/cache、复杂 FBX/纹理、remote persistence 或 ordinary canvas media ingress |
| Batch 93 | Director final desktop/mobile and cross-batch regression | `FINAL_REGRESSION_RECORDED_PASS` | `verify-liblib-batch93.py`、普通画布 `57/60/61/63/64/65/77` 与 Director `59/67-92` current gates 已通过；覆盖 desktop/mobile workspace/R3F/tree/Inspector/Timeline、折叠/抽屉、close/reopen、overflow、serial current-gate 和 zero diagnostics；不证明 LibTV source parity |
| Batch 94 | Director focus containment and keyboard boundary | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch94.py` 已通过；覆盖 desktop/mobile workspace 与 tree/Inspector drawer 的 Tab/Shift+Tab containment、focus return、editable boundary、ARIA/inert、overflow 和 zero diagnostics；不证明 LibTV source Director exact focus trap、inert、DOM/CSS 或键盘实现 |
| Batch 95 | Director canvas image ingress and session-only environment preview | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch95.py` 已通过；覆盖当前 Director 节点直接上游图片 typed ingress、Inspector 默认/切换/清除、stale source、R3F 非交互环境预览、portable export exclusion、desktop/mobile/failure isolation 和 `0/0/0` diagnostics；不证明 LibTV source-exact panorama UI、Three.js/R3F 实现、ordinary media provider 或 remote persistence |
| Batch 96 | Director multi-camera and Shot workflow | `FOCUSED_RUNTIME_RECORDED_PASS` | `verify-liblib-batch96.py` 已通过；覆盖旧 V1 无 `shots` 兼容 decode、规范化 export、Shot create/switch/update、history undo/redo、capture provenance/gallery、camera/Shot delete repair、last-camera guard、clipboard/whole-project duplicate remap、reload/import/export、desktop/mobile overflow 和 `0/0/0` diagnostics；不证明 LibTV source Shot schema、camera/time-range semantics、exact DOM/CSS 或 source parity |
| Batch 97 | Agent drawer current-source alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch97.py` 已通过；覆盖头部动作集合与 disabled 态、源站命名 Skill 卡与换一批、composer 五控件、选择模型菜单单列表双分区 15 项目录与 premium 角标、生成模式菜单默认/切换、Escape 分层、本地 status 与 `0/0/0` diagnostics；batch14 两处断言已按 2026-09-05 源站更新；不证明 LibTV source-exact Drawer DOM/CSS、真实模型调用或服务接入 |
| Batch 98 | Add-node panel current-source alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch98.py` 已通过；覆盖智能剪辑命名、脚本 NEW/（旧版）Beta flyout 与旧版创建、素材库风格库/特效库 flyout、搜索过滤/清空/空态、上传与生成历史本地 status 和 `0/0/0` diagnostics；batch15 素材库子菜单断言已按 2026-09-05 源站更新；不证明新脚本节点能力、搜索源站样式或真实 media ingress |
| Batch 99 | Shortcuts help panel copy alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch99.py` 已通过；覆盖四栏条目/顺序、kbd 数量与 suffix、删除位于其他栏、画布节点搜索 `⌘F` 行、Windows 重做移除、关闭行为和 `0/0/0` diagnostics；`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` 源站快照列已按 2026-09-05 复核刷新；不证明新快捷键运行时 handler、删除源站 keycap 或弹窗精确几何 |
| Batch 100 | Empty-canvas state and quick-create chips | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch100.py` 已通过；覆盖空态提示与 4 芯片（含 SD 2.5 角标）、芯片本地 status、`canvas-1`/`canvas-2` 切换隔离与 graph 保持、mobile `390x844` 无溢出和 `0/0/0` diagnostics；不证明芯片真实生成流、双击生成 UI 或源站精确视觉 |
| Batch 101 | Generation-history panel alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch101.py` 已通过；覆盖标题、尺寸 slider、本画布 chip、三 tab 计数、评级本地菜单与收藏过滤、时间倒序/批量操作、空态文案、Escape 与 `0/0/0` diagnostics；工具条入口更名 生成历史；不证明真实历史数据、评级后端或非空态源站样式 |
| Batch 102 | Asset manager drawer alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch102.py` 已通过；覆盖双 tab、搜索/筛选 aria、评级/展示设置控件与本地 hint、`共 10 节点` 计数、`收起节点侧栏` 关闭、空画布 `画布暂无节点` 和 `0/0/0` diagnostics；不证明评级/展示设置真实语义、资产 tab 空态源站样式或双开精确几何 |
| Batch 103 | Top-bar mode toggle alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch103.py` 已通过；覆盖 工作流/故事板 aria、pressed 双态、故事板+Agent 联动、工作台往返 graph 保持和 `0/0/0` diagnostics；batch11/13/14/17 aria 断言按 2026-09-05 源站迁移；不证明源站图标形状、几何或内容性「分镜」文案 |
| Batch 104 | Storyboard three-section alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch104.py` 已通过；覆盖列序 文本/图片/视频、放大按钮、暂空文案、空画布侧栏隐藏、demo 投影不变和工作台往返 `0/0/0` diagnostics；batch13 空态文案断言已按 2026-09-05 源站更新；不证明放大按钮行为或非空画布源站布局 |
| Batch 105 | Collaborative follow banner | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch105.py` 已通过；覆盖淡出默认、置态可见、文案、取消退出、ESC 单层优先（添加面板保留）与 `0/0/0` diagnostics；不证明真实协作、跟随视口联动或触发入口 |
| Batch 108 | 97-107 series cross-batch regression | `REGRESSION_RECORDED_PASS` | 串行 101 项 verifier：81 项通过；batch65/67-73/76 为 node PATH 环境修复后通过；batch6/9/40/41/44/46/48/49/51/72/74/75 经基线 `86673b6` 复跑归因为既有漂移（非 97-107 引入）；无本系列回归；旧漂移项待 replacement 协议处置 |
| Batch 110 | Aged-gate deprecation | `DOCS_RECORDED` | batch6/9/40/41/44/46/48/49/51/72/74/75 脚本头已标 `AGED_GATE / HISTORICAL_CONTRACT`（Batch 108 基线归因为证），replacement map 新增 §4.z；当前通过口径以 current manifest 为准；不改变任何运行时行为 |
| Batch 111 | Character library modal alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch111.py` 已通过；覆盖模态壳 1304x731@68、四图标签与列比、甜妹标签集、说明模板、应用至画布、close 关闭和 `0/0/0` diagnostics；batch11 关闭按钮断言已按 2026-09-05 源站迁移；不证明其余角色标签、多视口几何或卡片条精确几何 |
| Batch 112 | Character filter panel alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch112.py` 已通过；覆盖五组芯片集合、清空筛选、男芯片过滤（甜妹隐藏/霸总保留）、面板开合与 `0/0/0` diagnostics；文化区域选项与真实筛选服务不证明 |
| Batch 113 | Uniform character strip spacing | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch113.py` 已通过；前 6 张卡片 x 轴间距一致、`0/0/0` diagnostics；源站精确像素为截图粗读 |
| Batch 114 | Multi-canvas dropdown alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch114.py` 已通过；覆盖行双按钮结构与 aria、最新在前排序、四项行级菜单、新建画布 3、重命名、副本命名与自动切换、删除确认框文案/取消/fallback 和 `0/0/0` diagnostics；在新窗口打开行为与副本再复制命名不证明 |
| Batch 115 | Canvas double-click add panel | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch115.py` 已通过；双击打开面板/不建节点/Escape 关闭/可重复触发和 `0/0/0` diagnostics |
| Batch 116 | Script-generator node type | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch116.py` 已通过；脚本NEW 创建 脚本生成器（350x350、三尝试/参考图/GVLM 3.1/积分 6）、尝试选择与本地提示词、尺寸样式与 `0/0/0` diagnostics；batch98 两处断言随采样迁移；真实生成/子界面不证明 |
| Batch 117 | Director node card alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch117.py` 已通过；卡片标题/说明/打开导演台 CTA、工作区经节点按钮进入、Escape 关闭、节点保留和 `0/0/0` diagnostics；工作区内部结构与默认场景经采样确认与 clone 一致 |
| Batch 119 | /project list page | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch119.py` 已通过；页面结构（返回/全部项目/回收站/新建文件夹/创建卡/画布卡）、创建卡建画布、卡片导航激活、logo 菜单 全部项目 路由和 `0/0/0` diagnostics；回收站行为与源站分页不证明 |
| Batch 124 | Canvas recycle bin | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch124.py` 已通过；覆盖软删除快照、回收站面板文案/条目/日期/恢复、恢复后内容完整（≥10 节点）与 `0/0/0` diagnostics；batch119 回收站断言随本批迁移；30 天自动清除与 Director 数据恢复完整性不证明 |
| Batch 148 | Project card cover placeholders | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch148.py` 已通过；渐变封面区/节点计数角标/卡片布局和 `0/0/0` diagnostics |
| Batch 149 | 高级设置纵向列 + 默认模型 2.0 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch149.py` 已通过（15 checks）；触发器缩写/菜单选中态/积分 135/纵向列几何/引用槽 48x55，`0` diagnostics |
| Batch 150 | /project 新开标签 + 面板容器视觉 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch150.py` 已通过（9 checks）；新标签契约/容器圆角/毛玻璃，`0` diagnostics |
| Batch 151 | 工具行/积分块微对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch151.py` 已通过（7 checks）；pill h26/积分块灰调右对齐/135 回归，`0` diagnostics |
| Batch 152 | /project 卡副行仅日期 + 覆盖矩阵刷新 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch152.py` 已通过（7 checks）；日期唯一/无前缀/计数保留，`0` diagnostics |
| Batch 153 | Auto 因子证实 + 面板行为边界（证据 batch） | `DOCS_RECORDED` | 无代码变更；230=5×46 源站直证记录于 liblib-canvas-batch153-2026-09-07，矩阵/文档已更新 |
| Batch 154 | 全量回归扫描（124 验证器） | `SWEEP_RECORDED_PASS` | 112 通过 + 12 老化（清单一致）；batch124 弹窗契约迁移后通过；batch93 时序 flake 复跑通过 |
| Batch 155 | 5分钟芯片时长范围修复 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch155.py` 已通过（10 checks）；菜单 long 布局/滑杆 30..300/取消钳制，`0` diagnostics |
| Batch 156 | batch93 抽屉关闭点击加固 | `SCRIPT_RECORDED_PASS` | 连续 3 次通过；根因记录（全屏遮罩中心点落在抽屉内）；导演台 36/43/77 回归绿 |
| FrameOS Batch 157 | 右键菜单端到端验证 | `SCRIPT_RECORDED_PASS` | `verify-frameos-batch157.py` 已通过（12 checks）；BEHAVIORS.md 陈旧行修正 |
| Batch 158 | 默认模型回落 2.5 + 勘误 | `SCRIPT_RECORDED_PASS` | batch128 联动受控复现（Auto·300s·2.5）；batch149/22/33 回落迁移后回归绿 |
| Batch 159 | 尝试列移入节点卡内 | `SCRIPT_RECORDED_PASS` | 相邻回归 12 项全绿；batch128/155 定位器页面级迁移；y 偏移 -32 |
| Batch 160 | 芯片选长视频模式 + 槽空态 + 去新功能条 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch160.py` 已通过（9 checks）；14700 直证；batch21/22 偏移 -24 |
| Batch 161 | 面板增高 397px 修复溢出 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch161.py` 已通过（4 checks）；提示词 95px/无越界测量断言 |
| Batch 162 | 移动端 390 断点核查 | `SCRIPT_RECORDED_PASS` | 桌面+移动 10 checks；无页面溢出/提示词完好/截图存档 |
| Batch 163 | 平板断点核查（768/1024） | `SCRIPT_RECORDED_PASS` | 桌面+移动+平板 20 checks；无页面溢出/提示词完好/截图存档 |
| Batch 164 | 页脚触发器采样类对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch164.py` 已通过（8 checks）；batch21 x 偏移 +37 迁移 |
| Batch 165 | 引用槽行布局对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch165.py` 已通过（7 checks）；行高 ≥55/无 Auto Link 文字 |
| Batch 166 | 提示词区视觉 + AutoLink 芯片移除 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch166.py` 已通过（6 checks）；透明底/无圆角/无芯片 |
| Batch 167 | /project 次级表面对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch167.py` 已通过（14 checks）；实心按钮/创建卡结构/aspect-video 封面 |
| Batch 168 | /project 左侧边栏 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch168.py` 已通过（13 checks）；导航顺序/激活态/促销文案 |
| Batch 169 | 角色库页签 + 承诺书门模拟 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch169.py` 已通过（12 checks）；承诺书未代用户同意（本地状态模拟） |
| Batch 170 | 顶栏工作区重命名输入 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch170.py` 已通过（8 checks）；默认名迁移 未命名工作区 |
| Batch 171 | 左下资产管理栏几何对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch171.py` 已通过（8 checks）；栏 items-end/rounded-lg/13px |
| Batch 172 | 画布右键菜单（空白+节点） | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch172.py` 已通过（15 checks）；点击点定位/六项顺序/快捷键/禁用态/双分隔线/Escape/撤销接线/添加节点开面板；回归 batch160-171 全过 |
| Batch 173 | 节点右键菜单 + 模型菜单选中态 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch173.py` 已通过（11 checks）；七项节点菜单勘误/⌘C⌘D⌘V⌘⌫/问号图标/创建副本删除接线/选中行白 15% 背景；batch172 节点段迁移后 15 checks 全过；batch22/160-171 回归绿 |
| Batch 174 | 模型菜单行系统 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch174.py` 已通过（11 checks）；三态直测全行固定 52px/选中白 15%/hover 白 10%/34px 瓦片/描述常驻；batch22 58/48 旧合同迁移为当前源站合同后全过；21/33/149/164-173 回归绿 |
| Batch 175 | 模式菜单 + 参数菜单对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch175.py` 已通过（13 checks）；菜单仅 5 项/空节点仅文生视频可用/行 32px/比例 6 格无 Auto/62px 瓦片；batch21/33 长视频入口迁移到尝试芯片后全过；22/26/128/149/155/160/165-174 回归绿 |
| Batch 176 | 长模式参数菜单 + 模型联动 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch176.py` 已通过（12 checks）；长菜单 7 格含 Auto 选中/提示原文/30..300/无数量区/芯片切模型 2.5；batch21 长阶段迁移后全过；22/26/33/128/149/155/160/165-175 回归绿 |
| Batch 177 | 模型行 hover 滑层 + 芯片非 toggle | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch177.py` 已通过（9 checks）；滑层四类名/hover 归位/行高 52/再点不取消；batch128/155/160 取消合同迁移为保持选中后全过；21/22/26/33/149/165-176 回归绿 |
| Batch 178 | 芯片选中标记 + 取消路径 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch178.py` 已通过（11 checks）；选中白 10%/#f7f7f7/rounded-lg/图标；ESC 不取消（持久合同新增）；模式菜单切出清芯片+钳 30；21-177 全量回归绿 |
| Batch 179 | canvas token 收割对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch179.py` 已通过（10 checks）；9 项 token 定义与值/hover 用 token/菜单文字 #fff；batch169 承诺书门复验绿；21-178 全量回归绿 |
| Batch 180 | 芯片图标原字形 + z 评估 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch180.py` 已通过（7 checks）；三枚芯片 svg viewBox/path 与源站直采一致；z 迁移评估记录为维持映射不迁移；21-179 全量回归绿 |
| Batch 181 | 老化验证器修复（72/74） | `SCRIPT_RECORDED_PASS` | batch72 fixture 补 shot 级联（Batch 96 校验收紧后未随更）+ batch74 修复 documentForPersistence 剪枝 shot.captureIds 的真回归；两者 PASS，batch49 确认自愈；Director 89-96 与画布 21-180 全量回归绿 |
| Batch 182 | batch75 超时根因闭环 | `SCRIPT_RECORDED_PASS` | 可证伪实验：还原 Batch 181 持久化修复精确复现 30s 超时，恢复即全绿——下游症状定性成立，零代码改动复活；老化名单降至 10；72/74/89-96 与画布 21-180 复跑绿 |
| Batch 183 | batch9/51 几何断言核对复活 | `SCRIPT_RECORDED_PASS` | 工具条宽度断言 900.5→1092.5（Batch 51/52 源站直采合同迁移漏项）；视频面板等待 450ms 时序修正；错误的图片面板 397 迁移经源站直采（空态 660×191）回滚保持 274；batch20 确认本就绿；老化名单降至 6 |
| Batch 184 | 剩余 6 个老化验证器核对 | `TRIAGE_RECORDED` | 逐个失败形态存档并确认 AGED_GATE（现行门已覆盖、batch6 被 Batch 77 取代、batch40 为 fixture 媒体伪影）；零代码改动，脚本头部自文档化；抽样回归绿 |
| Batch 544 | batch 26 画布下拉超时抖动根治 | `HARDENING_RECORDED` | 根因：`domcontentloaded`+固定 600ms 后点击触发器，React 预水合点击被静默丢弃（并行 harness 加载共用 dev server 时高发，539/540 观察项收口）；验证器改为等待 `window.__libtv_store` 水合标记 + 触发点击重试×3，逆向条件下 3/3 绿；零产品代码改动 |
| Batch 185 | 172-178 表面 390 断点核查 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch185.py` 14 checks；双变体右键菜单视口内/芯片图标+白10%/滑层保留/无横向溢出；22 移动相位与 161 移动+平板复验绿 |
| Batch 186 | footer 图标按钮组对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch186.py` 8 checks；顺序/两枚新按钮/两枚直采字形/credits 位次；batch21 改字体无关的触发器相对偏移（三连跑绿）；batch125 补非 toggle 迁移；24 项全量回归绿 |
| Batch 187 | footer 按钮点击惰性证实 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch187.py` 9 checks；源站点击无弹层/无 toggle/无新层（类名差异仅 hover 噪声）；clone 占位一致，惰性固化为回归合同；186/21/22/125/172/178 回归绿 |
| Batch 188 | 工具条 pill 图标原字形 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch188.py` 12 checks；五枚 pill svg viewBox/path 与源站直采一致（含 g transform）；22/151/166/172/178/185/186 回归绿 |
| Batch 191 | 特效库横排 + pill 惰性采样 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch191.py` 10 checks；特效库开合/四卡/结构/外部关闭；运镜/参考/标记空节点惰性记录（运镜合同保留）；146/151/166/172/186/188 回归绿 |
| Batch 192 | 特效卡点击选用行为 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch192.py` 5 checks；点卡生成 素材-特效-名 节点 + 连线指入视频节点（显式 handle 方向）；33/125/172/178/185/186/187/191 回归绿 |
| Batch 193 | 参考/标记提示词态惰性 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch193.py` 6 checks；提示词前置仍惰性（真实前置未定位）；clone 占位一致，固化为合同；146/151/172/191 回归绿 |
| Batch 194 | 素材前置尝试 + 特效库锚点发现 | `EVIDENCE_RECORDED` | 前置建立再次失败（卡片定位到视口外 y≈912）；新发现源站特效库锚点状态依赖（与 clone 固定锚定分歧，记开放问题）；参考/标记惰性持续成立；191/193/172 复验绿 |
| Batch 195 | 特效库锚定规则闭环 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch195.py` 8 checks；三态采样盒子恒定 → 静态屏幕定位（推翻 194 结论）；clone portal 到 body + top-444；191/192/193/172-189 回归绿 |
| Batch 196 | 顶栏/底栏图标原字形 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch196.py` 16 checks；七枚组件定义与 viewBox 合同 + DOM 面板开关存在；一次错误映射（下拉箭头当 pill 图标）当场回滚；22/121/172/188/191 回归绿 |
| Batch 197 | 画布下拉箭头原字形 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch197.py` 7 checks；g transform/viewBox 直采合同 + TopNavBar 使用；22/121/172/196 回归绿 |
| Batch 198 | 顶栏右侧集群原字形 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch198.py` 12 checks；四枚组件定义/viewBox + DOM 闪电定位 + TopNavBar 使用；22/121/172/196/197 回归绿 |
| Batch 212 | 角色库模态尺寸规则破解 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch212.py` 6 checks；三档视口恒 1280×720 居中/克隆迁移/pill 接线；111（迁移后 19）/112/169/172/22 回归绿 |
| Batch 223 | 全量回归清扫 | `STABILITY_CONFIRMED` | 175 验证器：155 PASS / 20 已归因 FAIL（全部为历史合同或老化门）；Batch 172-222 零回归 |
| Batch 224 | 左侧栏字形审计 | `EVIDENCE_RECORDED` | 已对齐字形全量确认/零代码改动；check 基线稳定 |
| Batch 199 | Agent 抽屉重采 + 第四句标题 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch199.py` 9 checks；Skill 批次与 97 记录互证一致；横幅文案一致；抽屉宽度开放问题；107 轮换同步后两跑绿 |
| Batch 200 | 抽屉宽度规则 + Skill 芯片 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch200.py` 9 checks；三档视口 400px 恒定（更正 199 的 427 伪影）；点卡芯片入输入区可移除；22/107/121/172/185/196-199 回归绿 |
| Batch 202 | 资产管理抽屉重采 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch202.py` 10 checks；宽度 240→280（源站直采）/文案页签已一致；102/114/121/172 回归绿 |
| Batch 204 | 展示设置=节点类型筛选菜单 | `SCRIPT_RECORDED_PASS` | 源站直采 10 项菜单实装（data-asset-manager-typemenu）；batch102 hint 断言迁移（14 checks）；202 资产页签断言适配非空画布 |
| Batch 213 | 运镜 23 卡画廊实装 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch213.py` 8 checks；23 运动卡片/缩略图/选中关菜单；batch146 迁移后 13 checks 绿；151/172/22/191 回归绿 |
| Batch 214 | 运镜菜单纯启动器证实 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch214.py` 6 checks；选中/未选卡片类名标记一致/pill 不变/无提示词注入；✓ 已选标记移除；213/146/22/172 回归绿 |
| Batch 215 | 特效 pill 替换语义 + 参考/标记惰性扩展 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch215.py` 4 checks；素材连线后 pill 变替换；参考/标记仍惰性；213/146/192/22/172 回归绿 |
| Batch 216 | 参考选择模式横幅 + 方法勘误 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch216.py` 6 checks；参考 pill JS 点击开选择模式横幅（364×56 顶部居中）；勘误：此前 y>826 鼠标点击全落空，参考/标记惰性结论部分失效；213/215/191/22/172 回归绿 |
| Batch 217 | 标记选择模式横幅 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch217.py` 6 checks；316×56 顶部居中横幅逐字文案；216/215/213/172/22 回归绿 |
| Batch 218 | 标记选择模式蓝色横幅 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch218.py` 10 checks；蓝底圆角/魔棒图标/双行文案/返回节点/× 关闭；217 迁移后 8 checks 绿；216/215/213/22/172 回归绿 |
| Batch 219 | 剧本预填全文采样 | `PARTIAL_EVIDENCE` | text 节点渲染层含 markdown-content 样式，真实 prefill 需编辑态；clone 预填维持「剧本」；源站清零 |
| Batch 220 | 全量稳定性确认 | `STABILITY_CONFIRMED` | 42 活跃验证器全绿，零回归 |
| Batch 220 | 剧本预填完整内容采样受阻 | `EVIDENCE_RECORDED` | 空画布芯片依赖 Agent 抽屉已开状态，无头自动采样中难以可靠复现；deferred |
| Batch 205 | 类型筛选列表联动 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch205.py` 8 checks；十项映射/图片视频互斥过滤/全部恢复；102（14）/114/202/22/172 回归绿 |
| Batch 211 | 角色库模态重采 | `EVIDENCE_RECORDED` | 模态 1280×710 @1920 直采（clone 1304×731@1440）；尺寸规则两视口不可推导，clone 不动；双页签/公共页签行为与 169 一致 |
| Batch 206 | 空画布芯片点击采样 | `EVIDENCE_RECORDED` | 芯片成对创建 text+script-v2（源站新类型，无连线）；芯片集合随会话变化；script-v2 实装另立批次；源站清零 |
| Batch 207 | script-v2 节点类型实装 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch207.py` 8 checks；成对创建原子单历史/text 预填剧本/script-v2 350×350 无连线/undo 单次移除；会话发送搁置（挂起+账号残留风险）；100/102/114/205/22/172 回归绿 |
| Batch 208 | script-v2 选中态内部对齐 | `SCRIPT_RECORDED_PASS` | 悬浮标题条/卡壳 #171717/rounded-xl 直采实装；选中不开面板（与 clone 一致）；batch207 增 floating-header 断言后 9 checks 绿；205/22/100/172 回归绿 |
| Batch 209 | 画布 chrome 对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch209.py` 5 checks；attribution 隐藏/minimap 默认关/无 controls；22/9/51/172/205 回归绿 |
| Batch 210 | logo 下拉菜单几何对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch210.py` 6 checks；四项逐字/200 宽/行高 44/分隔线；119（16 checks）/22/172 回归绿 |
| Batch 203 | 所有评级筛选菜单实装 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch203.py` 8 checks；菜单 180×225 六项逐字标签/选 3 更新/重置；batch102 hint 断言迁移后全绿；114/121/172 回归绿 |
| Batch 201 | 换一批真实 Skill 目录 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch201.py` 7 checks；四批 15 Skill 直采（批 3 三张）+ 环绕；107/199/200/172 回归绿 |
| Batch 189 | 比例瓦片字形结构对齐 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch189.py` 20 checks；17px 盒 + 1.5px border-current 内框逐比例 px 直采；6/7 格模型依赖假设记为开放问题（clone 维持 175/176 合同）；21/22/155/160/175/176/185/186/188 回归绿 |
| Batch 190 | 比例格模型依赖复测（否定） | `SCRIPT_RECORDED_PASS` | 2.5→2.0 双向直采均 7 格含 Auto，假设否定；clone 网格统一 7 格 grid-cols-5，batch175/21 迁移后全绿；26 项回归绿 |
| Batch 125 | Video panel attempts/new-feature alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch125.py` 已通过；尝试行三芯片选择/取消、新功能条、placeholder 对齐、工具行保留、生成流程与 `0/0/0` diagnostics；尝试子界面/模型菜单/积分 135 不证明 |
| Batch 128 | Attempt chips driving settings linkage | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch128.py` 已通过；5分钟超长视频→Auto·300s、首尾帧→Auto·5s、deselect 保持设置和 `0/0/0` diagnostics；取消联动源站不证明 |
| Batch 131 | Second full regression sweep | `REGRESSION_RECORDED_PASS` | 串行 114 项：104 通过、batch16/21 修复、batch93 flake 复跑通过、12 aged gates 归因不变；零新增回归 |
| Batch 135 | Credits ratio factor | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch125/128.py` 复跑通过（积分随联动与比例更新）；16:9→135/Auto→230 两数据点校准比例因子；其余比例/模型定价 `SOURCE_UNKNOWN` |
| Batch 143 | Video panel default duration 6s→5s | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch21.py`（时长迁移后）与 `verify-liblib-batch125.py` 复跑通过；`npm run check` + docs check 通过；batch22 无需迁移 |
| Batch 139 | Topbar credits supermarket split | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch139.py` 已通过；积分超市/积分余额 独立入口、顺序与 `0/0/0` diagnostics；商城页行为不证明 |
| Batch 136 | Recycle bin selection and batch restore | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch136.py` 已通过；删除→回收站条目/勾选/计数/批量恢复/回列表与 `0/0/0` diagnostics；勾选批量操作源站交互不证明 |
| Batch 146b | Character filter 文化区域 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch146b.py` 已通过；文化区域四芯片/清空/恢复和 `0/0/0` diagnostics；源站文化区域选项不证明 |
| Batch 146b | Character filter 文化区域 | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch146b.py` 已通过；文化区域四芯片/清空/恢复和 `0/0/0` diagnostics；源站文化区域选项不证明 |
| Batch 141 | Video model menu full catalog | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch22.py`（矩阵迁移至 35 项采样目录）与 `verify-liblib-batch125/126/128/21.py` 复跑通过；`0/0/0` diagnostics；premium 完整分布不证明 |
| Batch 133 | FrameOS duplicate node insertion | `SCRIPT_RECORDED_PASS` | `verify-frameos-batch133.py` 已通过；Cmd+D 插入副本节点/副本标题/视觉选中/undo/redo/复制 toast 和 `0/0/0` diagnostics；修复文档记录的缺口 |
| Batch 134 | FrameOS copy/paste clipboard cycle | `SCRIPT_RECORDED_PASS` | `verify-frameos-batch134.py` 已通过；Cmd+C→Cmd+V 插入选中副本、undo、重复粘贴和 `0/0/0` diagnostics；writeText Promise 拒绝已捕获（修复潜在 pageerror） |
| Batch 106 | Project menu alignment | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch106.py` 已通过；覆盖四项命名与分组、本地 status、outside-close、教程 popover 四项和 `0/0/0` diagnostics；不证明四项真实跳转/确认流或菜单精确几何 |
| Batch 107 | Skill headline rotation | `SCRIPT_RECORDED_PASS` | `verify-liblib-batch107.py` 已通过；覆盖三条源站观察标题随 换一批 轮换与回绕、卡片集合不变和 `0/0/0` diagnostics；不证明源站轮换真实驱动 |

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
| Director 当前跨批次集成状态 | `HISTORICAL_RECORDED_PASS` + `CURRENT_RELIABILITY_GATES` + `FINAL_REGRESSION_RECORDED_PASS` + `FOCUS_CONTAINMENT_RECORDED_PASS` + `CANVAS_MEDIA_INGRESS_RECORDED_PASS` + `MULTI_CAMERA_SHOT_RECORDED_PASS` + `MANIFEST_RECORDED` | [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、[`liblib-canvas-batch93-2026-08-29/`](liblib-canvas-batch93-2026-08-29/)、[`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/)、[`liblib-canvas-batch95-2026-08-29/`](liblib-canvas-batch95-2026-08-29/)、[`liblib-canvas-batch96-2026-08-29/`](liblib-canvas-batch96-2026-08-29/)、[`storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md`](storyai-3d-director-desk-2026-08-27/PROGRESS_AUDIT_2026-08-27.md)、Batch 35-50/59/67-96 | 历史脚本仍按成本/副作用/当前价值分级；Batch 93 已完成 Director 桌面/移动端、普通画布跨批和 Batch 59/67-92 current gates，Batch 94 完成 workspace/drawer focus containment，Batch 95 完成 canvas-media session projection，Batch 96 完成 multi-camera/Shot authoring 与 provenance；不能把历史通过汇总成 source parity，也不能把 Director current gates 推导成 ordinary canvas async/persistence、remote storage、复杂真实资源或 source-exact persistence |
| 普通画布导航与 Director gizmo gesture | `CURRENT_SOURCE` + `LOCAL_FIXTURE`（Batch 77） | [`liblib-canvas-batch77-2026-08-28/`](liblib-canvas-batch77-2026-08-28/)、[`CANVAS_NAVIGATION.md`](../CANVAS_NAVIGATION.md)、Batch 77 source navigation audit | wheel/middle/Space/H/V/modifier zoom、mobile overflow、TransformControls 真实拖动与 gesture cleanup 已覆盖；真实触摸板硬件、source-exact Director surface 和真实资源/provider 仍不在范围 |
| Director pointer cancellation and R3F teardown | `CLONE_FIXTURE_ONLY`（Batch 78） | [`liblib-canvas-batch78-2026-08-28/`](liblib-canvas-batch78-2026-08-28/)、[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、Batch 78 `runtime-audit.json`、Batch 68 teardown regression | Curve/Phone Vcam/Timeline 三类 clone pointer lifecycle、Director gesture cancel baseline、capture release、stale move prevention、R3F Canvas async teardown 防护已覆盖；不证明 LibTV source exact Director pointer behavior、真实触摸板或手机传感器 |
| `LIBTV-VR-024` Director project/session/command authority | `PROJECT_CODEC_FOCUSED_PASS` + `OWNER_SESSION_FOCUSED_PASS` + `AUTHORED_RUNTIME_FOCUSED_PASS` + `HISTORY_FOCUSED_PASS` + `POINTER_LIFECYCLE_FOCUSED_PASS` + `REFERENCE_DELETE_FOCUSED_PASS` + `ASYNC_AUTHORITY_FOCUSED_PASS` + `PERSISTENCE_FOCUSED_PASS` + `CLIPBOARD_REMAP_FOCUSED_PASS` + `OWNER_REACHABILITY_FOCUSED_PASS` + `WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS` + `DURABLE_TOMBSTONE_FOCUSED_PASS` + `IMPORT_EXPORT_FOCUSED_PASS` + `LOCAL_RESOURCE_MATERIALIZATION_FOCUSED_PASS` + `COMMAND_FEEDBACK_FOCUSED_PASS` + `LOCK_EDITABILITY_FOCUSED_PASS` + `SELECTION_CRUD_FOCUSED_PASS` + `TRANSFORM_CONTEXT_FOCUSED_PASS` + `RESTORE_SELECTION_FOCUSED_PASS` + `SELECTION_TIMELINE_AUTHORITY_FOCUSED_PASS` + `SCENE_COMMAND_FOCUSED_PASS` + `OBJECT_CAMERA_GROUP_COMMAND_FOCUSED_PASS` + `FINAL_REGRESSION_RECORDED_PASS` | [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)、[`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)、[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、[`liblib-canvas-batch93-2026-08-29/`](liblib-canvas-batch93-2026-08-29/)、`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`、Batch 67-93 | Batch 67 strict codec、68 owner registry/session、69 authored/runtime、70 command/history、71 pointer lifecycle、72 reference-aware delete、73 Director async、74 browser-local persistence、75 same-project clipboard remap、76 all-canvas owner reachability、79 whole-project duplicate、80 durable tombstone/storage/resource cleanup、81 strict import/export、82 finite local resource materialization、83 command feedback projection、84 locked-target editability、85 selection/CRUD discoverability、86 transform target context/pointer cleanup、87 restore-selection repair、88 selection/timeline/TransformControls authority、89 scene settings/add-camera、90 project/session diagnostics + scene command、91 object/camera/group command boundary、92 local resource owner/lease lifecycle 和 93 final desktop/mobile/cross-batch/governance regression 均有 focused/current recorded pass；ordinary canvas async/persistence、remote storage、复杂真实资源、普通画布统一 feedback 和 source parity 仍未实现 |
| 普通图片双浮层 owner/命中边界 | `CLONE_FIXTURE_ONLY`（Batch 60） | [`liblib-canvas-batch60-2026-08-26/`](liblib-canvas-batch60-2026-08-26/)、[`ImageNode.spec.md`](components/ImageNode.spec.md)、[`ImageEditPanel.spec.md`](components/ImageEditPanel.spec.md) | owner identity、selection migration、既有几何、panel controls 和 active-tool replacement 已覆盖；相邻节点被 panel 覆盖像素的真实源站 routing 未取得 |
| 普通画布 graph mutation ingress | `STATIC_CONTRACT_ONLY` + connection island `LOCAL_FIXTURE` | [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、`LIBTV-VR-014` design、Batch 57 | 全 writer/T0-T5 audit 已完成；derived/setter/copy/delete/restore/remote routing runtime 尚未验证或实现 |
| React Flow change transport | `SCRIPT_RECORDED_PASS` / `RUNTIME_PARTIAL` | [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、共同 12.11.1 types/reducer、Open Canvas/clone callback static audit、Batch 61 `runtime-audit.json`、`LIBTV-VR-016` | whole-batch classifier、current-snapshot routing、semantic zero-partial reject、edge session selection、drag/measurement/history sanitation 和 focused browser corpus 已通过；混合 primary/focus、resize/reconnect、portable document 全面 sanitation 仍未完成 |
| 多画布 lifecycle / owner isolation | `STATIC_CONTRACT_ONLY` / `RUNTIME_PARTIAL` | [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、Open Canvas list/route/hydrate/delete/save audit、Batch 16/58/65、`LIBTV-VR-017` design | clone 已有 per-canvas graph/viewport/history、switch selection cleanup、node-bound UI reconciliation、bootstrap-only responsive preset、stored viewport restore 和 current/old viewport callback guard；invalid target、generic page generation、organize/drag/connection、async/resource owner 隔离及完整 focused fixture仍未实现 |
| Command outcome / feedback ownership | `DIRECTOR_FOCUSED_RUNTIME_PASS` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、[`liblib-canvas-batch83-2026-08-29/`](liblib-canvas-batch83-2026-08-29/)、Open Canvas `OC-040..045`、clone local status/timer/Director paths、`LIBTV-VR-018` design | Director 已将 typed disposition/reason 投影到 fixed-header status surface，并验证 ARIA、rejection/no-op visibility、committed suppression、mobile geometry 和 zero-history boundary；普通画布 connection reject、local string/timer islands、clear/retry/dedupe、统一 owner 与 exact source placement/timeout 仍未实现 |
| Selection / focus / command context | `DIRECTOR_FOCUSED_RUNTIME_PASS` / `RUNTIME_PARTIAL` / `SOURCE_PARITY_PARTIAL` | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`liblib-canvas-batch62-2026-08-27/`](liblib-canvas-batch62-2026-08-27/)、[`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/)、Open Canvas `OC-046..052`、Batch 50/61 | clone-owned selection snapshot、editable/IME、blocking foreground suspension、one-Escape、focus fallback，以及 Director workspace/drawer containment 与回焦已通过 focused verifier；ordinary canvas universal mixed primary、mixed edge command、exact source modal/shortcut/focus 和非-Director surface containment 仍 partial |
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

### 5.5 Batch 93 final regression closeout

Batch 93 在固定 `localhost:4317` 上完成最终收口，结果见
[`liblib-canvas-batch93-2026-08-29/runtime-audit.json`](liblib-canvas-batch93-2026-08-29/runtime-audit.json)
和
[`liblib-canvas-batch93-2026-08-29/current-gate-regression.json`](liblib-canvas-batch93-2026-08-29/current-gate-regression.json)。
专项 verifier 覆盖 Director `1440x900` 与 `390x844` fresh contexts、R3F
nonblank、object tree、Inspector、Timeline、折叠/抽屉、close/reopen 和
overflow；同批还串行复跑普通画布 `57/60/61/63/64/65/77` 与 Director
`59/67-92` current gates。desktop/mobile diagnostics 均为 `0/0/0`，没有写入
截图或执行截图识别。该结果只证明当前 clone-owned prototype reliability，
不证明 LibTV 原站 Director 的 exact DOM/CSS、项目/资源协议或 source parity。

### 5.6 Batch 94 focus containment closeout

Batch 94 在固定 `localhost:4317` 上完成 Director workspace 与移动抽屉的焦点
边界收口，结果见
[`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/)。
专项 verifier 覆盖 desktop `1440x900`、mobile `390x844`、workspace 正/反向
Tab containment、tree/Inspector 局部循环、关闭/Escape/backdrop 回焦、editable
input boundary、inactive drawer `aria-hidden`/`inert`、横向溢出和
console/page/request `0/0/0`。本批没有生成截图或执行截图识别；普通画布完整
回归沿用 Batch 93 的已记录结果，不把本次中断的重复序列记为新的全量通过。
该结果是 clone-owned Director reliability，不证明 LibTV 原站的 exact focus
trap、`inert`、DOM/CSS、快捷键或焦点回收实现。

### 5.7 Batch 95 canvas-media ingress closeout

Batch 95 在固定 `localhost:4317` 上完成普通画布图片到 Director session-only
环境预览的纵向切片，结果见
[`liblib-canvas-batch95-2026-08-29/runtime-audit.json`](liblib-canvas-batch95-2026-08-29/runtime-audit.json)
和
[`liblib-canvas-batch95-2026-08-29/IMPLEMENTATION.md`](liblib-canvas-batch95-2026-08-29/IMPLEMENTATION.md)。
专项 verifier 覆盖 desktop `1440x900`、mobile `390x844`、直接上游图片候选、
默认/切换/清除、source stale 自动清理、portable project 排除、R3F 环境预览
ready、横向溢出和非法 base64 data URL 失败隔离。最终 desktop/mobile/failure
diagnostics 均为 `console/page/request = 0/0/0`；没有生成截图或执行截图识别。
本批实现了共享的明显非法图片 data URL 预检，避免普通 `ImageNode` 与 Director
`TextureLoader` 对同一坏输入各自产生浏览器错误。
该结果只证明 clone-owned session projection，不证明 LibTV 原站的 panorama
协议、Three.js/R3F 技术、exact DOM/CSS、普通画布真实上传或资源 provider。

### 5.8 Batch 96 multi-camera and Shot closeout

Batch 96 在固定 `localhost:4317` 上完成 Director 多机位与 Shot authoring
纵向切片，结果见
[`liblib-canvas-batch96-2026-08-29/runtime-audit.json`](liblib-canvas-batch96-2026-08-29/runtime-audit.json)
和
[`liblib-canvas-batch96-2026-08-29/IMPLEMENTATION.md`](liblib-canvas-batch96-2026-08-29/IMPLEMENTATION.md)。
专项 verifier 覆盖旧 V1 兼容 decode、规范化 export、Shot create/switch/update、
单条 history、undo/redo、capture provenance/gallery、camera/Shot delete repair、
最后机位阻断、clipboard/whole-project duplicate remap、reload/import/export、
desktop/mobile `1440x900`/`390x844`、无横向溢出和 `0/0/0` diagnostics。

本批没有新增截图或截图识别。结果只证明 clone-owned Shot authoring 与引用
完整性，不证明 LibTV 原站存在相同 Shot schema、camera/time-range semantics、
DOM/CSS、视觉布局或 source parity。

## 6. 台账维护规则

- 新增 verifier：同时更新本台账、[`HARNESS.md`](../HARNESS.md)、对应 Batch `IMPLEMENTATION.md` 和 `docs/research/README.md`；
- 修改断言：记录它覆盖的是历史合同还是当前源站合同；不能只改数字不改证据说明；
- 新增截图：先检查已有 `SCREENSHOT_ANALYSIS.md`，并记录 viewport、zoom、状态和来源；
- 被 fixture 阻塞：使用 `BLOCKED_BY_FIXTURE`，记录所需 fixture，不在共享项目试探；
- 并行 WIP：保留 `PARALLEL_WIP`，待该开发者的脚本、实施记录和验证结果稳定后再升级；
- 任何文档变更都运行 `python3 scripts/verify-docs.py`，并只提交自己的路径。
| Batch 226 | 视频节点卡结构采样 | `EVIDENCE_RECORDED` | 源站多轮交互后状态不稳定，wrapper 不可达；零代码改动；画布清零 |
| Batch 227 | 视频节点卡结构确认 | `EVIDENCE_RECORDED` | 刷新后恢复标准渲染态，卡结构简单单层（面板级对齐已充分覆盖）；零代码改动；源站清零 |
| Batch 228 | 源站连线渲染样式采样 | `EVIDENCE_RECORDED` | 节点连线交互复杂度阻塞（+按钮机制 vs 拖拽 handle）；零代码改动；源站清零 |
| Batch 226 | 左侧栏/底栏字形审计 | `EVIDENCE_RECORDED` | 已对齐字形全量确认，零遗漏；零代码改动 |
| Batch 230 | 源站画布空态 + storyboard-group 结构 | `EVIDENCE_RECORDED` | 测试项目已清空；storyboard-group 源站结构需原始项目采样；clone 已通过 canvas-2 预设充分覆盖 |
| Batch 232 | Agent 抽屉模型选择器采样 | `PARTIAL_EVIDENCE` | Agent 按钮找到但抽屉未稳定打开（页面状态漂移）；模型选择器采样推迟 |
| Batch 234 | Agent 抽屉模型选择器目录 | `SCRIPT_RECORDED_PASS` | 15 模型目录完整采得（7 图片 + 8 视频）+ 缩略图 URL + 描述；替代 Batch 232 的部分采样 |
| Batch 528 | 脚本生成器入口跟随接线 | `SCRIPT_RECORDED_PASS` | 源站第五/八轮采样（exploration NOTES §140）单击尝试入口仅选中/跟随（正在跟随/取消ESC）；clone 接通 batch 105 FollowBanner：入口点击→跟随态，取消/ESC 退出，无子流程；`verify-liblib-batch528.py` 14 检查 + batch 116 回归绿 |
| Batch 529 | 素材库风格库/特效库大版面浮层 | `SCRIPT_RECORDED_PASS` | 源站第六/七/八轮采样（exploration NOTES §132-145 + 截图 31/32/34/35）；clone 新增 LibraryShowcasePanel 双变体：广场页签/分类行/商用卡/本地搜索/暂无素材空态；缩略图为 CLONE_DECISION 渐变占位；附带 batch 462 先例 aged 再对齐——batch 15/98 的「生成历史未连接」断言迁移至 batch 478 fixture 子菜单合同；`verify-liblib-batch529.py` 24 检查 + batch 11/15/98/116/478 回归绿 |
| Batch 530 | 图片节点模型触发菜单 | `SCRIPT_RECORDED_PASS` | 源站第一轮采样实测可开（exploration NOTES §3 + 截图 03b）；clone 新增 ImageModelMenu：7 模型目录（时长胶囊 + Qwen image 3.0 上新徽标 + 选中态描述），芯片闭合态显示当前模型名（Lib Image 2.5 Pro，当前源站合同；panorama 保持 batch 20 旧合同）；选择仅本地草稿不触发生成；`verify-liblib-batch530.py` 23 检查 + batch 10/20 回归绿 |
| Batch 531 | 自写分镜脚本全屏编辑器 | `SCRIPT_RECORDED_PASS` | 2026-09-27 有头浏览器 CDP 补采（截图 38，单实例原则不杀既有浏览器）：自写入口打开 3 步 stepper + 10 列分镜表格全屏编辑器，修正 batch 528 round-8「未展开子流程」结论（该结论仅限剧本/角色生成入口）；clone 新增 StoryboardScriptEditor + uiStore storyboard-editor 阻塞面（ESC/✕ 关闭），单元格本地草稿编辑、添加镜头、行数联动 stepper；下一步按钮可视不推进（第 2/3 步未采样）；`verify-liblib-batch531.py` 31 检查 + batch 528/116 回归绿 |
| Batch 532 | 分镜编辑器三步导航 | `SCRIPT_RECORDED_PASS` | CDP 补采第 2/3 步（截图 40/41）：准备资产步 = 角色/场景/道具 新增虚线卡 + 资产已生成覆盖提示；合成提示词步 = 表格最终提示词列高亮 + 一键合成全部提示词（可视不触发付费生成）；无上一步按钮（源站仅前进）；clone 扩展 StoryboardScriptEditor 三步导航，batch 531/528 回归绿；`verify-liblib-batch532.py` 16 检查 |
| Batch 533 | 脚本 V2 进度卡卡体 | `SCRIPT_RECORDED_PASS` | CDP 补采（截图 39 + 节点 DOM）：分镜会话后 script-v2 卡内为 ①确认镜头—②准备资产—③合成提示词 进度卡 + 打开脚本节点→ 重入按钮；clone 替换 207 占位卡体（标题合同保留，进度卡为唯一实证内部形态），按钮接通 batch 531/532 编辑器；`verify-liblib-batch533.py` 14 检查 + batch 207 回归绿 |
| Batch 534 | 自写会话↔脚本生成器卡转换 | `SCRIPT_RECORDED_PASS` | 源站实测（截图 39 + 画布 DOM）：自写会话后卡片持久转进度卡；clone 增加 uiStore.storyboardSessionNodeId（有意不随 closedOverlayState 重置），ScriptGeneratorNode 会话后渲染步进条 + 打开脚本节点→；531 verifier 重入步骤对齐源站流程；`verify-liblib-batch534.py` 11 检查 + batch 531/528/116 回归绿 |
| Batch 535 | 导演台底部场景输入条 | `SCRIPT_RECORDED_PASS` | 第二轮采样实证（exploration NOTES §8 + 截图 18）：视口底部胶囊条 = 光标/相机/手 模式段 + 描述想要搭建的场景 输入 + ↑ 提交；clone 新增 DirectorScenePromptBar，模式单选切换 + 本地草稿 + 提交仅本地确认回显（云端 AI 动作不触发，diagnostics:zero 覆盖无网络）；`verify-liblib-batch535.py` 8 检查 + batch 70 回归绿 |
| Batch 536 | 导演台左侧图标栏 | `SCRIPT_RECORDED_PASS` | 第二轮采样实证（exploration NOTES §8 + 截图 18）：46px 窄栏六入口 图层/人物/机位/帧/文件夹/导入，图层默认激活；clone 新增 DirectorIconRail，未采样五项仅视觉切换不导航（CLONE_DECISION 标注），树面板/视口偏移适配 + 移动端滑出归零；`verify-liblib-batch536.py` 14 检查 + batch 70/341 回归绿 |
| Batch 537 | 导演台 rail 标签 DOM 修正 + 添加角色 flyout | `SCRIPT_RECORDED_PASS` | CDP DOM 补采（aria-label 枚举）：rail 实际七入口 场景/添加角色/添加机位/全景图/选择画幅比例/AI 识图导入 + 帮助（? 圆钮），修正 536 推断标签；新增添加角色 flyout（本地上传 + 8 预设 + 群众 (3x3)/几何模型 子菜单，3D 加建不实现）；536 verifier 迁移至修正合同；回归 batch 536/70 绿 |
| Batch 538 | 导演台全景图/画幅比例 flyout | `SCRIPT_RECORDED_PASS` | 已存截图转录（44-rail-25/26，零新采样）：全景图 flyout = 本地上传/历史记录/AI 生成；选择画幅比例 = 自适应（默认）+21:9/16:9/4:3/1:1/3:4/9:16 七卡单选含比例矩形示意；AI 生成纯可视不触发付费动作；三 flyout 互斥展开；`verify-liblib-batch538.py` 20 检查 + batch 536/70 回归绿 |
| Batch 539 | 导演台 AI 识图导入模态 | `SCRIPT_RECORDED_PASS` | 已存截图转录（44-rail-27，零新采样）：居中模态 = 本地上传/历史记录页签 + 拖拽上传区 + 覆盖场景单选组（插入默认/覆盖）+ 生成站位参考禁用钮（云端 AI 动作永不触发）；历史记录空态；backdrop/✕ 双关闭；`verify-liblib-batch539.py` 17 检查 + batch 536/70 回归绿 + npm run check 全门绿 |
| Batch 540 | rail 添加机位接通场景树同源动作 | `SCRIPT_RECORDED_PASS` | 源站实证（537 DOM 枚举）：rail 添加机位为直接动作无面板；clone 接通 directorStore.addDirectorCamera（场景树/Inspector 同源），动作项不抢激活态；536 verifier 的激活态迁移断言迁移至本合同；`verify-liblib-batch540.py` 7 检查 + batch 536/70 回归绿 |
| Batch 541 | 添加角色 flyout 预设本地等效 | `SCRIPT_RECORDED_PASS` | 源站采样（537 截图 44-23）：预设点击加 3D 角色变体；clone 本地等效——群众 (3x3) 接 addCrowdArray(3/3/1.2)（Viewport 群众面板同源）真实增对象 + ack 回显，预设体型 ack 本地等效占位不伪造 3D，上传/几何静默收起，ack 2s 淡出；`verify-liblib-batch541.py` 9 检查 + batch 536/540/70 回归绿 |
| Batch 542 | 角色本地上传接模型库管线 | `SCRIPT_RECORDED_PASS` | 源站采样（537 截图 44-23）：本地上传传自定义角色模型；clone 复用 readDirectorLocalModelFiles→addLocalModelLibraryItem 既有管线（与 Viewport 模型库同源），file chooser + 有效 .fbx/.obj 入库 + ack 回显（管线正则不含 glb/gltf——实测确认）；`verify-liblib-batch542.py` 7 检查 + batch 536/540/541 回归绿 |
| Batch 543 | 导演台重置视角按钮 | `SCRIPT_RECORDED_PASS` | 第二轮采样实证（exploration NOTES §8 + 截图 18）：姿态 gizmo 正下方重置视角胶囊；clone 补齐按钮并接通 DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT 相机复位（新引用触发 CameraController 重应用，恢复导演台默认机位 6.2/4.25/7.4→0/1/0 fov45）；纯本地无网络；`verify-liblib-batch543.py` 7 检查 + batch 70/535 回归绿 |
| Batch 545 | 场景树条目右键菜单 | `SCRIPT_RECORDED_PASS` | CDP 补采（截图 47，2026-09-28）：右键条目弹出 打组/显示隐藏/锁定解锁/创建副本/删除 五项菜单；clone 接既有 store 同源动作（group/updateObject visible/toggleObjectLocked/copy+paste/DELETE_OBJECT），外部与 ESC 关闭；视口空白右键 SOURCE_INCONCLUSIVE 不克隆；原 544 编号被 batch 26 画布下拉抖动根治占用，功能批改号 545；`verify-liblib-batch545.py` 12 检查 + batch 536/70 回归绿 |
| Batch 546 | AI 识图导入历史页签本地等效 | `SCRIPT_RECORDED_PASS` | 源站仅空态采样（539）；clone 历史页签列出 localModelLibrary 已导入模型（batch 542 管线产物）为识别源候选——云端识图任务史未采样，CLONE_DECISION 本地等效注记；空态合同保持；`verify-liblib-batch546.py` 4 检查 + batch 539/542 回归绿 |
| Batch 547 | 摄像机面板切换机位下拉 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 47）：摄像机面板 名称→切换机位→位置…；clone 补齐 切换机位 select（列 camera 对象，经绑定 shot 走 selectShot 更新 activeCameraId），不强制切机位视角（源站视角独立管理）；无 shot 绑定的机位选项 disabled；`verify-liblib-batch547.py` 8 检查 + batch 70/536 回归绿 |
| Batch 548 | 3D 场景设置面板扩展 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 18/45 右栏）：显示区含 天空颜色 #060608/角色标签开/网格吸附关/高斯地面吸附开/地面透明度 0.40；clone DirectorScene additive 扩展 5 字段（updateScene 白名单+校验同步；V1 文档 optional 向后兼容，restore 兜底），Inspector 补 5 行控件持久化；场景变换/全景球暂不克隆（无渲染实现）；`verify-liblib-batch548.py` 10 检查 + batch 70/536/547 回归绿 |
| Batch 549 | 场景显示字段接入渲染 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 18 角色A 浮标）：clone 将 batch 548 三字段接入渲染——角色头顶 drei Html 名称浮标受 showCharacterLabels 控制（pointer-events 关闭、zIndex 压低）、地面材质透明度接 groundOpacity、无全景时背景接 skyColor（雾色保持 backgroundColor）；`verify-liblib-batch549.py` 6 检查 + batch 70/548 回归绿 |
| Batch 550 | 网格吸附接入变换系统 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 45 网格吸附默认关）；clone 三处 TransformControls（对象/分组 rig/路径锚点）接 translationSnap=0.5（snapToGrid 开启时），关闭自由移动；开关经 updateScene 持久化且选中对象后保持；高斯地面吸附数据态待渲染语义；`verify-liblib-batch550.py` 5 检查 + batch 70/548/549 回归绿 |
| Batch 551 | 高斯地面吸附角色落地约束 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 45 高斯地面吸附默认开；吸附开启时机位 Y 仍 2.2——机位不参与实证）；clone updateObjectTransform 角色对象 Y<0 夹紧至 0（authored 持久层合同；runtime 投影由时间线采样可覆盖——按 authored 断言）；关闭自由/重开约束；调试期间发现并修复 dev server Turbopack 坏 chunk（共享服务重启）；`verify-liblib-batch551.py` 6 检查 + batch 70/548/550 回归绿 |
| Batch 552 | 导演台时间线打开态深采 | `EVIDENCE_RECORDED` | CDP 补采（截图 48）：时间线左端控制簇（播放/循环/时间输入 0.00-10.00s）+ 新建轨道按钮（1/5 引导 onboarding）+ 标尺 1s-4s + 主机位绘制轨迹行 + 导出视频到画布；零代码改动（新建轨道 store 语义留待实现批，clone 无公开动作） |
| Batch 553 | 时间线新建轨道按钮与 store 动作 | `SCRIPT_RECORDED_PASS` | 源站证据（552 截图 48）：+ 新建轨道为选中角色/摄像机创建变换轨道；clone 新增 createTrackForSelectedObject（before/after 快照 + 历史提交，getDirectorDocumentSnapshot 模式）+ 时间线按钮（无合格选中禁用）；clone 创建路径保证角色/机位恒有轨道故点击恒 NOOP（CLONE_DECISION 保留源站按钮形态）；`verify-liblib-batch553.py` 5 检查 + batch 70/536/549 回归绿 |
| Batch 554 | AI 导入拖拽上传落地画布 | `SCRIPT_RECORDED_PASS` | 源站注记实证（539 转录「上传后画布将新连一个图片节点」）：clone 拖拽区升级为可用上传——dataURL→画布 image 节点 + 连边至导演台 source 节点（走图连接校验）；自动替换图源留待（全景源状态在 Desk，CLONE_DECISION）；纯本地无云端识别；`verify-liblib-batch554.py` 6 检查 + batch 539/546/70 回归绿 |
| Batch 555 | 全景球旋转/半径滑杆 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 45/48 全景球组）：水平旋转（度）+ 球形半径两滑杆接入渲染（rotation-y + sphereGeometry 半径 props）；半径默认 30 保持 clone 现渲染（源站示值 60，SOURCE_DIFF 留痕）；字段 additive + V1 optional 兼容解码；`verify-liblib-batch555.py` 7 检查 + batch 548/70 回归绿 |
| Batch 556 | 时间线引导气泡 1/5 | `SCRIPT_RECORDED_PASS` | 源站证据（552 截图 48）：时间线打开时左下角「请选择一个角色或者摄像机后，可新建轨道」+ 1/5 + 跳过/下一步气泡；clone 实现挂载级气泡（跳过/下一步均收起——步骤 2-5 未采样，CLONE_DECISION），每次挂载再现；`verify-liblib-batch556.py` 9 检查 + batch 70/548/553 回归绿 |
| Batch 557 | 摄像机轨道行绘制轨迹 affordance | `SCRIPT_RECORDED_PASS` | 源站证据（552 截图 48 轨道行 1 主机位右侧 ⓘ绘制轨迹）：clone camera 轨道行（未绑定 motion path）渲染 span-role 绘制轨迹 affordance（避免嵌套 button hydration 警告），点击选中轨道并打开与控制簇同源的运动路径菜单；`verify-liblib-batch557.py` 5 检查 + batch 70/553/556 回归绿 |
| Batch 558 | 高斯地面吸附渲染端夹紧 | `SCRIPT_RECORDED_PASS` | 源站证据（截图 45 角色贴地）：SceneObject 渲染位 character Y = max(authored, 0)（gaussianGroundSnap 开），机位/道具/关闭态自由——渲染端兜底 551 的 authored 夹紧（实测 runtime 投影继承夹紧，防御性）；TransformControls attach 瞬态显式过滤（553 留痕）；`verify-liblib-batch558.py` 5 检查 + batch 70/548/551 回归绿 |
| Batch 560 | 场景变换接入渲染分组 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 45/48 场景缩放/平移/旋转）：DirectorScene additive 3 字段（V1 optional + expectTuple3 解码），场景属性面板顶部 场景变换 section（缩放滑杆百分比角标 + 平移/旋转三轴输入），视口 objects+groups 包进 scene transform group（地面/网格/灯光/全景球为辅助不参与）；缩放默认 1（源站会话示值 300% 记 SOURCE_DIFF）；`verify-liblib-batch560.py` 7 检查 + batch 70/548/558 回归绿 |
| Batch 561 | 全景背景已连接/提示标签 | `SCRIPT_RECORDED_PASS` | 源站采样（截图 45/48 全景背景 section）：已连接全景图 状态文本 + 空上游虚线提示框（请将图片节点连接到导演台左侧输入口）；clone 场景属性画布环境区补标题/标签/提示框；`verify-liblib-batch561.py` 5 检查 + batch 539/70 回归绿 |
| Batch 562 | AI 导入自动替换当前图源 | `SCRIPT_RECORDED_PASS` | 源站注记（539/554「自动替换当前图源」后半）：全景源选择状态自 DirectorDesk 经 DirectorIconRail 提升传入 AI 导入模态（onPanoramaSourceChange），上传后自动选中新图片节点（画布环境 select value = 新节点 id），全景运行时既有联动加载；`verify-liblib-batch562.py` 7 检查 + batch 554/561/70 回归绿 |
| Batch 563 | 摄像机面板三页签 + 运动轨迹(NEW) | `SCRIPT_RECORDED_PASS` | CDP 采样（截图 50/51）：摄像机面板三页签 属性|运动轨迹(NEW)|截图，运动轨迹页签 = 虚拟相机（QR 连接 + 录制/重试）+ 预设运镜 + 创建运动轨迹；clone 新增 DirectorCameraMotionTab——QR 点击接 connectPhoneVcamLocal、录制接 startPhoneVcamRecording（未连接禁用），预设/建轨迹提示态（完整面板在时间线控制簇）；`verify-liblib-batch563.py` 17 检查 + batch 70/547/561 回归绿 |
| Batch 564 | 机位跟随目标↔预设运镜联动 | `SCRIPT_RECORDED_PASS` | 源站证据（截图 47 跟随目标字段 + 时间线预设运镜禁用语义）：零产品代码改动端到端验证批——updateCamera 设置/清除 followTargetId 驱动 trigger 禁用/恢复 + 跟随目标时不可使用预设运镜警告 span；`verify-liblib-batch564.py` 7 检查 + batch 70/547/553 回归绿 |
| Batch 565 | 全景背景联动端到端核对 | `SCRIPT_RECORDED_PASS` | 零产品代码改动端到端验证批——连接上游图片节点后 canvasMediaInputs 收集→select 自动选中（resolved 默认第一个 input）→全景运行时 ready→已连接全景图 标签；调试确认 fixture 需为站点可达路径（/tmp 绝对路径 TextureLoader 不可达）；`verify-liblib-batch565.py` 6 检查 + batch 548/561 回归绿 |
| Batch 575 | 摄像机面板轴向关键帧菱形标记 | `SCRIPT_RECORDED_PASS` | 源站证据（574 截图 60 X/Y/Z 输入右侧青色菱形）：AxisFields 新增 keyframedAxes prop（轴标签旁青色菱形标记），摄像机面板从变换/相机轨道反查当前播头时间的轴关键帧（相机轨道 value 形如 {transform,...} 取 transform[field]）；新增机位创建关键帧即覆盖三轴（徽标立现）；`verify-liblib-batch575.py` 4 检查 + batch 36/70/563 回归绿 |
| Batch 566 | 地面高度字段端到端 | `SCRIPT_RECORDED_PASS` | CDP 补采（截图 52 地面区）：地面含 高度 0.0 滑杆（batch 548 遗漏）；clone DirectorScene additive groundHeight（默认 0，-2..2 滑杆），V1 optional 兼容解码，地面 mesh Y 接线（保持网格层叠 -0.01 偏移）；正负值均持久化；`verify-liblib-batch566.py` 6 检查 + batch 548/558/70 回归绿 |
| Batch 571 续 | 菱形拖拽采样 | `INCONCLUSIVE` | CDP 补采：菱形命中坐标过小（6-20px 候选未命中），拖拽行为未采得——留待精确命中补采；零代码改动（NOTES §16 续） |
| Batch 571 续2 | 运动路径关键帧编辑面板采样 | `EVIDENCE_RECORDED` | CDP 补采（截图 64）：菱形 SPAN 精确命中+拖拽未改时（INCONCLUSIVE 续），但联动出摄像机面板 运动轨迹页签 的运动路径关键帧编辑 UI——时长 0.1 滑杆 + 位置 3.3/2.2/10 镜像 + 旋转/缩放/统一缩放字段组；实现批候选（关键帧选中态联动面板编辑）；零代码改动（NOTES §17） |
| Batch 574 | 关键帧菱形交互与轴标记深采 | `EVIDENCE_RECORDED` | CDP 补采（截图 60/61/62）：位置子行菱形点击/右键无可见状态变化（INCONCLUSIVE）；新对齐点——摄像机面板 X/Y/Z 输入右侧青色菱形关键帧标记（clone 变换输入无此标记，实现批候选）；零代码改动 |
| Batch 579 | 关键帧菱形点击 seek 播头 | `SCRIPT_RECORDED_PASS` | 源站证据（578 截图 63：播头 2s 点击 0s 菱形后跳回 0s、时间输入 0.00）：clone 菱形 onClick 追加 setTimelineTime(keyframe.time)（选中 + seek）；scrub 仍跳过菱形（既有守卫）；verifier 动态读取 keyframe-time（selectObject 会重置播头——实测留痕）；`verify-liblib-batch579.py` 5 检查 + batch 36/70/553 回归绿 |
| Batch 573 | 自动帧图标化 + 图标栏移动端隐藏 | `SCRIPT_RECORDED_PASS` | 源站证据（567 CDP 枚举：自动帧 24px 图标钮无文字）：clone 自动关键帧文字钮对齐为图标钮（aria-label 自动帧，data 合同保留）；回归发现 536 DirectorIconRail 移动端覆盖场景对象 toggle（batch 36 移动流超时根因）——rail 移动端隐藏修复；batch 36 add-track/关键帧流迁移至角色（源站 onboarding 仅角色/摄像机）；`verify-liblib-batch36.py` 迁移后全绿 + batch 536/557/563/566/70 回归绿 |
| Batch 567 | 时间线控制簇对齐确认 | `EVIDENCE_RECORDED` | CDP 补采（截图 55，aria-label 枚举）：源站控制簇 = 播放/自动帧/循环播放 + 时间输入 + 新建轨道（1/5 引导跨重载持久），无独立添加关键帧按钮——clone 的添加关键帧/删除关键帧为 clone 侧扩展（既有文档），控制簇与 clone 对齐确认；lane 点击/双击无新交互；零代码改动 |
| Batch 571 | 时间线状态持久化差异 | `EVIDENCE_RECORDED` | CDP 补采（截图 58）：源站引导气泡 1/5 跨重载持久（clone 挂载级——潜在对齐点）、自动帧默认关不跨会话、点标尺移播头（时间输入同步 2.90）；零代码改动，引导持久化为实现批候选 |
| Batch 572 | 引导气泡收起状态持久化对齐 | `SCRIPT_RECORDED_PASS` | 源站证据（571 截图 58 跨重载持久）：clone coachDismissed 以 localStorage 对齐（初始化读取 + dismissCoach 写入，storage 不可用降级会话内）；556 verifier 迁移至持久化合同（收起→重载→仍收起）；`verify-liblib-batch556.py` 8 检查（迁移后）+ batch 563/566/70 回归绿 |
| Batch 568 | 时间线当前时间可编辑输入 | `SCRIPT_RECORDED_PASS` | 源站证据（552/567 截图 48/55：时间输入为可编辑带边框框）：clone 时间显示升级为 input（Enter 后 setTimelineTime seek，钳制 [0, duration]，currentTime 变更时显示同步），时长只读 label 拆分；`verify-liblib-batch568.py` 6 检查 + batch 553/556/70 回归绿 |
| Batch 570 | 自动帧关键帧生成对齐确认 | `EVIDENCE_RECORDED` | CDP 补采（截图 57）：自动帧开 + 摄像机位置改值 → 主机位轨道下生成 位置子行 + 关键帧菱形 + 元组 3.3,2.2,10 + 视口相机同步 + 注视旋转重算——与 clone 既有自动关键帧实现行为对齐确认；零代码改动 |
| Batch 609 | 属性面板三轴字段行换源站形态 + 20×28 关键帧菱形开关 | `SCRIPT_RECORDED_PASS` | 源站证据（probe66 整棵子树 + probe67 精确计算样式，2026-10-01）：字段组 60px（28 高标签 + mb-1 + 28 高控件）、三轴格 80×28 rounded-lg bg-white/10 无描边、grid-cols-3 gap-1、轴片 20×28 absolute 压在数值框左侧（pl-6 让开、左对齐 12px）、每格右端 20×28 关键帧开关（`当前帧无关键帧` bg-white/[0.04]+fill=none ↔ `当前帧有关键帧` bg-[#263E43] text-[#5DDCFF]+fill=currentColor，9×9 svg 内 rotate(45) 6.1 rx=1 rect）；注视坐标等非对象变换行不挂开关。clone 原为 32 高带描边格 + 24 宽流内轴片 + 右对齐 11px 输入 + 一枚 6px 只读菱形且无开关。改动：AxisFields 换源站形态、新增 KeyframeToggleButton 并接上打/删播放头关键帧（force=true）、名称输入换源站形态、`data-director-keyframed-axis` 合同迁到「有」态按钮（batch 575 定位器不变）。顺带修既有 bug：keyframedAxes 只读 `value.transform`（相机轨道形态），角色/道具的 transform 轨道恒判 false——角色关键帧标记从未亮过，此前仅被 batch 575 的相机用例掩盖。不声称：源站开关点击行为（需授权）；on/off 粒度为字段而非轴（clone 关键帧存整份 DirectorTransform），故一枚关键帧同亮三行，此点在验收中断言而非绕开。`verify-liblib-batch609.py` 73 检查 + 回归 35/36/37/43/47/49/575/583/84/86 全绿 |
| Batch 610 | 属性面板列宽归位 280 + 三枚 select 换源站形态 + FOV 段重建 | `SCRIPT_RECORDED_PASS` | 源站证据（probe66 右头整棵子树 + probe68 FOV 段精确样式）：右列 280 宽 @x=1640、px-4 内容 248 @x=1656；切换机位/跟随目标/注视目标三枚 select 均 248×28 `h-7 rounded-lg border-0 bg-white/10 px-2 text-[12px] appearance-none`，标签 28 高 13px text-white/45；FOV 段为 `视野角度 (FOV)` 91.7×13 + 16×16 `?` 徽标（文案是 opacity-0 + group-hover:opacity-100 的 208 宽浮层，z-1700 bg-[#2b2b2b]），控件行 170+8+70=248（4px #5c5c5c 轨道 + #09caf5 填充 + 12×12 白圆钮 border-[#262626] + 透明 range min=15 max=90 step=1；70×28 数值框含 49×28 text-center text-[13px] 输入与 20px 关键帧开关），填充比 79.3/170 与 (50-15)/(90-15) 互证。本批推翻一处历史读数：batch 581 的 `fov:above-name` 把 sticky 预览缩略图的 `FOV 50°` 角标（absolute left-3 top-3 y=134）当成控件，live 读数的真控件在 y=798（名称 321 与注视坐标 721 之后）；582 的「默认展开 + 点击开关」亦为 hover 浮层。581 合同按约定迁移而非删除（fov:above-name → fov:below-name；help 四条 → hover 显隐 + 浮层几何；读数迁到数值框 value）。改动：去掉自造左边框且列宽 w-72 → 280、抽出 FieldLabel/FIELD_CONTROL 三枚 select 换源站形态、体内边距 px-3 → px-4、删失效 CameraFovHelp 并按源站重建 FOV 段、数值框与滑块同提交路径双向同步且两端钳制。顺带修既有矛盾：updateCamera 守卫写 fov 20–120 与实测 15–90 冲突（旧 UI 只有 range 滑杆提交不了区间外值故一直藏着，加了可自由输入的数值框后一钳到 15 就被拒），已改为引用新增的 DIRECTOR_CAMERA_FOV_MIN/MAX。不声称：sticky 预览缩略图（240×135 canvas + FOV n° 角标 + 24×24 放大钮）clone 尚无；源站 FOV 拖拽行为（需授权）。`verify-liblib-batch610.py` 97 检查 + 回归 581(31)/609(73)/47/84/86/93/90 全绿 |

| Batch 611 | 属性面板顶部 sticky 机位预览缩略图（真·离屏渲染） | `SCRIPT_RECORDED_PASS` | 源站证据（probe66 右头整棵子树 + crop611 对 2× 截图裁切二次确认画布内容）：`section [1640,105,280,168] sticky top-0 z-20 border-b border-white/8 bg-[rgba(33,33,33,0.98)] px-4 py-4 shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md`；盒 `[1656,121,240,135] relative overflow-hidden rounded-xl border` bg `rgba(8,8,16,0.95)`，内 `canvas [1657,122,240,135]`；`FOV n°` 角标 `[1669,134,51.3,13] pointer-events-none absolute left-3 top-3 text-[13px] leading-none text-white/55`；放大钮 `[1859,219,24,24] hover:bg-white/16 absolute bottom-3 right-3 flex size-6 rounded-lg bg-white/10 text-white/85` + 14×14 对角双箭头，可访问名「切换到机位视角」。高度自洽 16+135+16+1=168；left-3/right-3 相对 padding box 量（盒+1px 边框）四项逐字吻合。裁图确认画布里是该机位视角下的**真 3D 渲染**（网格地面、地平线、站桌边的角色），故不做 2D 假图——新增 directorCameraPreview.ts（模块级 sink + WebGLRenderTarget 建/复用/释放 + readRenderTargetPixels 逐行翻转 Y + composeDirectorCameraPreviewCamera 朝向规则与视口 CameraController 一致），CameraPreviewRenderer 挂在**已有**的 Canvas 内（不新增 WebGL 上下文）以机位/时间/对象签名门控重绘，CameraPreviewSection 几何逐字照抄并复用已验证的 selectShot+setViewMode（不新增 store 动作，标 INFERENCE）。顺带修一个真 bug（与 batch 604 同类：看起来能点、其实点不动）：导出面板向上弹出后「比例」三枚按钮被属性面板字段行盖住（batch 40 的 `9:16` 点击超时）——基线对照（cp 到 /tmp 再 git checkout --，不用 stash）确认是**已推送的 batch 610 引入**（610 把 FOV 数值框移到源站位置 y=842，正好落进按钮 [1727,832,84,32] 的 footprint，而 610 之前那区间是空的）；根因是 `backdrop-filter` 创建层叠上下文把导出面板的 `z-50` 关在里面，而时间轴 section 自身 `z-index:auto` 输给属性面板列的 `z-30`，修法是给 DirectorTimeline 的 section 加 `z-40`。不声称：源站放大钮点击行为（需授权）。`verify-liblib-batch611.py` 49 检查（含「是渲染不是填充」像素断言：亮度跨度>40、均值不近黑/白、亮像素占比 0.02–0.95、8×6 亮度网格≥3 区域；WebGL 上下文数前后对比 2→2→2）+ 回归 609(73)/610(97)/70 全绿 |
| Batch 612 | 控件普查扫尾：轴片 aria 分工 + 大画布底部两簇几何 + 跟随胶囊文案 | `SCRIPT_RECORDED_PASS` | 源站证据（diff609.py 重跑控件全集普查 src 113 vs clone 126 + probe612c 两簇精确读数 + probe612b 跟随浮层子树）：普查逮到三项真缺陷，第一项是 batch 609 自己引入的——源站轴片 `aria-label="左右拖动调整 X 轴"` 用**大写轴名**而 DOM 文本是小写 `x`、靠 `text-transform: uppercase` 渲染，609 把轴名一并小写传下去导致 clone aria 变 `… x 轴`，普查按名比对根本匹配不上（在数量层面完全隐形）；修为轴名保持大写、字形下沉到 SceneAxisScrub 内部。底部左簇源站 28 高 @y=1104 起点 x=14、**簇内 4px**、rounded-lg、14px 图标，clone 原为 y=1110/x=16/gap-2(8)/rounded-md/15px 图标，误差逐枚累积最远一枚偏 22px；资产管理 `px-2 gap-2`(91)→`px-3 gap-1`(94)、缩放选项去掉源站没有的 min-w-10 与 tabular-nums（40.2→36.3），改后六枚 x/y/w/h 逐字相同。底部中簇源站**均质**（每枚 32×32 幽灵 + 20px 图标 + 8px 间隙，生成历史↔快捷键 17px 分隔），clone 却给「添加节点」单做了 40×40 `bg-[#edf0f5] text-[#171717]` 实心主按钮并把整簇左顶 19.5px——删除 `prominent` prop 与变体，图标统一 20px，快捷键前补 `ml-[9px]`；**剩余 20px 偏移来自 clone 独有的「打开工具箱」按钮，保留**（不删 clone 功能来对齐几何），验收只比尺寸不比 x。跟随浮层「取消」胶囊源站是单文本节点 `own='取消ESC'` 无子元素 12px/12px/500 63.7 宽，clone 曾拆成两层，改为单文本节点；顺带记录源站自身 a11y 矛盾（`aria-label="退出跟随"` 与可见文案 `取消ESC` 不符）——两边都不默默修正，clone 保留 pointer-events-auto（源站那枚继承 pointer-events:none 是死按钮，沿用 batch 605 原则）。附带读数：hover 提示 `absolute left-1/2 top-full z-10 mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1 text-xs font-normal text-white opacity-0`，82.1×24 @(960.9,33)，由 peer-hover 显形。验收脚本自纠两处：`rounded-full` 在 Tailwind v4 是 `calc(infinity * 1px)`，computed 出 `3.35544e+07px` 而非 v3 的 `9999px`，断言改判幅度；首版把轴片断言放在大画布页读而轴片在导演台里，移进导演台后读并补 Y/Z 对称断言。不声称：源站这一批按钮的点击行为（点了会写进用户真实项目），改完能用由 clone 侧四枚面板（添加节点/缩放选项/快捷键/生成历史）能正常打开来证明。`verify-liblib-batch612.py` 112 检查 + 回归 609(76)/610(97)/611(49) 全绿 |
| Batch 613 | 导演台左列：资源栏 + 场景树按源站容器树归位 | `SCRIPT_RECORDED_PASS` | 源站证据（换普查口径：probe613 走**每个可交互元素**而非只比可访问名——源站 150 项 vs clone 47 项，冒出源站 `帮助` 在 [7.5,1110,32,32] 而 clone 在 [7.5,928,32,32]，差 182px；probe613d/e 从 `场景` 逐层往上走才见根因；probe613g 扫 y52..88 横带；probe613h 全 DOM nav/tab/role=tab + 文案 镜头/机位N 搜索；probe613i 左列精确读数；probe613f 命中测试；crop613 裁图）：源站左列是**一块** `aside.absolute.inset-y-0.left-0.z-30.overflow-hidden.border-r.border-white/10.bg-[#171717]` [0,0,281,1150]，内含 header [0,0,280,52] `flex h-[52px] items-center border-b` + div [0,52,280,1098] `flex h-[calc(100%-52px)]`，后者并排放 nav [0,52,48,1098] 资源栏与 div [48,52,232,1098] 场景树（`flex w-[232px] flex-col bg-[#171717]`，自身无边框，整列那 1px border-r white/10 落在 x280..281）——**两者都从 52 起纵贯视口底**，时间线是浮在中间列上的覆盖层。clone 原把两者 `absolute inset-y-0` 挂在中间 flex 子节点里：顶边被 clone 独有的 36px 镜头条顶到 88（七枚 rail 每枚低 36px）、底边停在该子节点下沿 968（`帮助` 差 182px）、场景树成了 46/220 且底色 `#191919` 浅两阶。顺带补上 batch 602 的洞：其 docstring 早写明源站 rail `48x1098 @(0,52)`，但断言只查宽/pad/gap/底色/右边框与条目**相对**间距，从未查 y 与 h，故 rail 放多高都绿；本批补 `rail:spans-[0,52]to-the-viewport-bottom`（9→10 项，对旧状态非空：y=88≠52 会红）。另证源站导演台**无任何整幅页签行**（probe613h 只命中 canvasNavbar [0,8,1920,32]、资源栏、视口底部浮动药丸 [780,968,128,48]），故 clone 的 `导演台镜头` 是 clone 独有功能——按既定原则保留，只加 `min-[900px]:ml-12` 让开归位后的 rail 48px（否则「镜头」标签被吃），底色仍 `#171717` 与源站该处场景树同色。唯一修不好的一处：probe613f 证明**源站自己的「帮助」是死控件**——中心 (23.5,1126) 命中时间线左簇 `div.z-10.shrink-0.bg-[#1f1f1f]`，裁图同区域纯黑；本批让 clone 复现同一行为（时间线 z-40 > rail z-30），时间线最小化后 `帮助` 回到 [7.5,1110,32,32] 且可命中可点击（两条都断言）；反向抬高 rail 会埋掉时间线自己的 播放/自动帧/循环播放/时间输入 四枚活控件，故照抄源站并记录、不默默修正。改动：资源栏与场景树提到工作区根（fixed 即包含块）并 `top-[52px] bottom-0`，场景树 `min-[900px]:left-12 top-[52px] w-[233px]`（233 = 232 内容 + 1px border-box，令边框落在 280..281 与源站整列同位）、树底色 #171717、镜头条 `min-[900px]:ml-12`。验收脚本两处自纠：(1) `帮助` 所在的 (23.5,1126) 正是 Next dev server `nextjs-portal` build 角标的挂载点，elementFromPoint 与 click 都被**工具**截走，该 overlay 只存在于 `next dev`、生产与源站均无，故命中测试前摘掉并写明理由；(2) 先写的 `flyout:closes-on-second-click` 跑出红，查代码发现 `select("panorama")` 本就不 toggle（无条件 `setOpenFlyout`），而源站 rail flyout 点击语义属未取证项——**断言两边都没有的行为不诚实**，改为断言真实契约：点另一枚 rail 项会关掉当前 flyout（`select()` 开头 `setOpenFlyout(null)`）。另记既有缺口（未改，不在本批靶心）：导演台 Escape 链里无 flyout 档，flyout 开着时按 Escape 会落到 `closeWorkspace()` 关掉整个导演台。回归：613(53)/602(10)/587(27)/536(27)/538(20)/590(85)/93/96/89/95/35/36/50/604(34)/605(38)/606(28)/608(15)/609(76)/610(97)/611(49)/612(112)/40 全绿；**94 失败但与本批无关**——移动端顶栏视角切换器（`left-1/2 -translate-x-1/2`，170px，`z-10`）压住「收起」钮，基线对照（cp 到 /tmp 再 git checkout --，不用 stash）确认撤掉本批改动后同样失败，已记为下一批靶心。不声称：源站资源栏/场景树/镜头条点击行为（会写进真实项目）；镜头条位置（clone 独有功能，只保证不被 rail 吃掉）；场景树内部（clone 多两条 36px 工具条，列表起点 172 vs 源站 100）。`verify-liblib-batch613.py` 53 检查 |
| Batch 614 | 导演台属性列：面板底色/左边框 + 标题条 + 列的顶边与下沿 | `SCRIPT_RECORDED_PASS` | 源站证据（probe613 全量普查冒出的容器差异 + probe614 列整棵子树 / 614b 高度是内容驱动还是视口锚定 / 614c 滚动区直接子节点 / 614d 边框色与标题条子节点数及 computed 字体 / 614e 3D canvas 盒）：源站属性列是浮在满幅 body 上的覆盖层 `div.absolute.right-0.top-0.z-20.flex.w-[281px].flex-col.overflow-hidden` → `[1639,0,281,1020]`，内层 `div.flex.min-h-0.flex-1.flex-col.overflow-hidden.border.w-[281px].border-y-0.border-l.border-r-0` 底色实测 `rgb(33,33,33)`=#212121、四条边里只有 `border-left: 1px rgba(255,255,255,0.08)`（落 1639..1640），再内是 48px 标题条 `div.flex.shrink-0.items-center.justify-between.h-12.px-3` @`[1640,0,280,48]`、**恰 1 个**子节点 `span.text-[15px].font-medium.text-neutral-50`「摄像机」@`[1652,11.9,45,23.3]`、computed `15px/23.25px/500 rgb(247,247,247)`（`justify-between` 配单子节点即贴左，x=1652=1640+px-3 逐字吻合），末层 `div.min-h-0.flex-1.overflow-y-auto` @`[1640,48,280,972]`。clone 原为 `[1640,88,280,880]`（低 36px、窄 1px、无左边框、底色 #191919 浅两阶、标题条自造 border-b 且是两段 12px 以下小字）。**推翻两条历史读数**：(1) batch 610「源站该列没有左边框」只对一半——没有的是**整列**边框，列**内部**面板有 1px `border-l`，正确 border-box 是 281@1639、内容仍 280@1640；按约定**迁移**其 `panel:width-280`/`panel:x-1640` → `panel:width-281-border-box`/`panel:x-1639`，并补 `panel:1px-left-border-white-8` 与 `panel:content-origin-still-1640` 钉住「内容起点没变」（610 现 99/99）。(2) batch 606「右头 280px 定宽列 = 选中对象名」被推翻：它量的那条带就是**属性列自己的标题条**，文字是对象**类别名**（该工程机位名为「机位1」，标题却是「摄像机」，名字在更下面的「名称」字段）——606 元素认对了却另建通栏顶栏带着第二份拷贝；本批修标题条本身，顶栏右组不动（自带 28 条合同），相撞后果记录在案。**两处有意偏离**：(a) 顶边取 52 而非源站的 0——源站顶栏只有左头 280px（就在左列那块 aside 里）故右列上方为空，clone 顶栏是**通栏** grid（606 建）右组占 `[1640,0,280,51]`，放到 top-0 会把标题条整个盖住等于新造看不见的控件，故用 `-top-9`（中间区从 88 起，88−36=52）提上去；(b) 下沿止于时间线上沿而非内容驱动——614b 实测源站 `scrollHeight == clientHeight == 972` 根本不滚动、computed `bottom:130px` 只是派生值，但 clone 相机面板内容实测 1185（比源站 907 高 278，多出 可见/未锁定、当前镜头、镜头名称 等行，属另一靶心），照抄内容驱动会冲出视口 140px；**先试「拉满到视口底」被 batch 95 回归当场抓到真回归**——clone 时间线比源站高 52px（182 vs 130），拉满后时间线盖住面板下段、`data-director-panorama-clear` 点不到（Playwright 报 `导出视频到画布 … intercepts pointer events`），故下沿交给中间区止于 968，正是源站 1020 与时间线 1021 的关系；验收专加 `panel:deep-content-stays-reachable` 守这个坑。z 保留 30 而非源站 20（窄屏抽屉须压过 z-20 遮罩，桌面无重叠）。顺带修：标题行高补 `leading-[23.25px]`（源站 23.25 vs clone 22.5，`text-[15px]` 只设字号）；视口框内缩 `left-[46px]/left-[266px]/right-[288px]` 与 613 改完的列几何对不上，改为 `left-[48px]/left-[281px]/right-[281px]`，3D canvas 由 `[266,88,1366,880]` 变 `[281,88,1358,880]`，左右缘分别贴两列。验收脚本三处自纠：`querySelector('canvas')` 先命中 240×135 机位预览小画布（改用 `canvas[data-engine]`）；面板 border-box 起点是 1639、内容起点才是 1640；移动端抽屉是 `right-0`+281 宽，390 视口下开在 x=109 贴右缘（非靠左），且触发器 `打开属性面板` 在 `div.absolute.left-3.top-3.max-[899px]:flex` 里而非底部药丸 `data-director-viewport-toolbar`。**记下不改（下一批靶心）**：(1) 源站 3D canvas 是**满幅** `[0,0,1920,1150]`（场景铺满整窗、面板浮在上面），clone 是 `[281,88,1358,880]` 内缩框——取景差异非仅外框；(2) 面板内容高差 278px，源站滚动区是 6 个 `<section class="border-b border-white/8 px-4 py-4">`（页签在**滚动区内**、sticky 预览、摄像机属性、FOV、相机截图、隐藏的虚拟相机），clone 是一条 `space-y-4 px-4 py-3` 加若干 label/div 且页签行在滚动区**外面**；(3) 移动端顶栏视角切换器（170px、`left-1/2 -translate-x-1/2`、`z-10`）压住「收起」钮，94 移动腿点 56 次命中不了，基线对照（cp+git checkout --，不用 stash）确认与 613/614 无关。不声称：标题条文字**只在选中机位这一态**有源站读数，未把源站驱动到其它类别，故 clone 既有措辞（角色/群众/角色组/场景物体/Scene）原样保留标为推断；源站属性列是容器本身无点击行为可录。`verify-liblib-batch614.py` 48 检查（桌面+移动两腿）+ 回归 610(99)/95/613(53)/606(28)/609(76)/611(49)/587(27)/605(38)/608(15)/612(112)/93/96/89/35/36/50 全绿 |
| Batch 615 | 窄屏顶栏：「收起」钮不再被居中视角切换器压住 | `SCRIPT_RECORDED_PASS` | 非普查靶心，而是**回归一直红着**：batch 94 移动端腿整轮未绿，`Locator.click: Timeout 30000ms` 于 `[data-director-panels-toggle]`，日志连报 56 次 `waiting for element to be visible, enabled and stable` + `<div class="flex h-9 w-[170px] …"> from <div role="group" aria-label="导演台视角" class="pointer-events-auto absolute left-1/2 top-2 z-10 -translate-x-1/2"> subtree intercepts pointer events` —— 一枚画在屏幕上却点不着的控件，与 batch 604 被吞的 prompt 胶囊、batch 611 被属性面板埋掉的导出按钮同类。**基线对照**（cp 到 /tmp 再 git checkout --，不用 stash）确认撤掉 613/614 后同样失败，是既有缺陷非本轮连带。根因（probe615 在 390×844 量顶栏整棵树）：切换器是绝对定位 + **170px 定宽**内行，**完全无视**外层 `grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]`，直接骑在正中 —— 390 下占 110..280；左列分到 (390−95)/2=147.5，收起落在 99.5..139.5，切换器左缘 110 切进按钮内 10.5px 把圆心 119.5 盖住。修法：左列加窄屏上限 `max-w-[calc(50vw-85px)]`（85 = 170/2）—— 390 时左列收成 110、收起落到 62..102 与切换器相接不重叠、命中测试回到自己的 svg；**≥900px 时 50vw−85 ≥ 395 > 280，该上限永不生效**，源站 280px 定宽左头与 `关闭 @(0,5.5)` / `收起 @(240,5.5)` 一字未动（606 的 28 条照旧全绿，本批验收也把这两条读数单列钉住）。只压左列不动右列：右列 `justify-end` 控件靠右缘 ≈320..382，与切换器右缘 280 不冲突（验收里 导出/导入 两枚命中测试也断言了）。**源站窄屏未取证**（probe615b 另开 tab、device-metrics override 只作用于新 tab、共享会话原 tab 全程未碰且未发任何点击，结果落到画布页——导演台需点击才进），故源站手机宽度下顶栏会不会也撞**不声称**；本批只拿掉一枚点不动的控件，不动任何有源站读数支撑的桌面几何。验收 390 腿：切换器仍 170 宽仍居中、左列宽 ≤ 切换器左缘、两者不重叠、关闭/收起/导出/导入 四枚逐枚 elementFromPoint 命中自己、点收起后 `data-director-panels-collapsed="true"`；1920 腿：左列仍 280、max-width 上限不生效、关闭 @(0,5.5,40,40)、收起 @(240,5.5,40,40)、切换器仍 @(875,…)，并跑 收起→场景 往返验证几何复原。往返只放桌面段：恢复入口是 rail 的「场景」项而 rail 在 <900px 是 hidden（batch 573 既有设计），窄屏那条恢复路径本就不存在。`verify-liblib-batch615.py` 22 检查 + **batch 94 由红转绿** + 回归 606(28)/614(48)/613(53)/605(38)/93 全绿 |
