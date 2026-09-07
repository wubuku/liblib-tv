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
