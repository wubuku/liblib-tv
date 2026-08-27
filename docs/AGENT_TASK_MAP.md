# Agent 任务导读

> 目的：让 agent 按任务进入最小、正确的证据集合，而不是从根目录或最近一个 Batch 猜项目规则。
>
> 使用顺序：先读本页对应行，再读 `AGENTS.md` 和任务列出的主文档；只有证据不足时才扩大搜索范围。

## 1. 总体路径

```text
任务识别
  -> AGENTS.md 硬约束
  -> 本页任务入口
  -> 路由/架构文档
  -> 组件合同或源站证据
  -> 最小修改/研究记录
  -> 窄验证 + 全量门禁
```

本页是导航，不替代组件规格、源站审计、Batch 实施记录或代码注释。若文档之间出现冲突，优先级按 [`DECISION_REGISTER.md`](DECISION_REGISTER.md) 和 `AGENTS.md` 的硬约束处理，再回到最新的源站证据。

## 2. 任务到文档矩阵

| 任务 | 先读 | 继续读 | 关键停止条件 |
|---|---|---|---|
| 了解项目全貌 | [`AGENTS.md`](../AGENTS.md)、[`BIG_PICTURE.md`](BIG_PICTURE.md) | [`ARCHITECTURE.md`](ARCHITECTURE.md)、[`GLOSSARY.md`](GLOSSARY.md) | 不把 LibTV 与 FrameOS 合并理解 |
| 选择下一项 LibTV UI/UX 研究或复刻 | [`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 对应 gap 的 traceability、runtime catalog、组件合同和 fixture gate | backlog 排名不等于编码授权；一次只选一个有界 slice，不跨过 source/fixture/parallel-WIP 停止条件 |
| 启动/验证本地项目 | [`DEVELOPMENT.md`](DEVELOPMENT.md)、[`HARNESS.md`](HARNESS.md) | [`QUALITY.md`](QUALITY.md) | 先确认端口和其他开发者 server，不覆盖现有进程 |
| 选择/构造 LibTV 测试夹具 | [`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`HARNESS.md`](HARNESS.md) | [`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md)、[`VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md)、对应 Batch verifier/implementation | 先区分 demo baseline、空画布 UI 构造、transaction-derived、Director store 和共享源站只读态；新 Page 不会自动清除 BrowserContext persistence |
| 修改 LibTV 节点/面板 | [`ARCHITECTURE.md`](ARCHITECTURE.md)、[`research/components/COVERAGE_MATRIX.md`](research/components/COVERAGE_MATRIX.md)、对应 `research/components/*.spec.md` | [`BEHAVIORS.md`](research/BEHAVIORS.md)、对应 Batch `PLAN.md`/`IMPLEMENTATION.md` | 先确认是独立 spec、父合同、批次合同还是 `NEEDS_SPEC`；不以旧截图或相似项目替代当前源站合同 |
| 修复图片节点上下浮层 | [`ImageNode.spec.md`](research/components/ImageNode.spec.md)、[`ImageEditPanel.spec.md`](research/components/ImageEditPanel.spec.md) | [`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | 先确认 measured size、同帧 live viewport、actual host rect、canvas generation 和 selection lifecycle；不先凭感觉改 offset/clamp |
| 修改 LibTV viewport/zoom/fit/放置/拖动/画布 resize | [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`BottomToolbar.spec.md`](research/components/BottomToolbar.spec.md)、[`NAVIGATION_GESTURES.spec.md`](research/liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md) | [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) | 先声明 client/host/flow/node/media domain、live/stable/bootstrap phase、canvas generation 和 named placement；default add 使用 actual host，不用 browser window；viewport 不进 semantic graph history |
| 修改 LibTV 上传/拖入/素材历史/资产/媒体替换 | [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md) | [`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](research/LIBTV_VERIFIER_REPLACEMENT_MAP.md)、[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、[`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | 先声明 entry profile、intent/attempt/cohort、local lease、asset/reference、provisional/semantic transaction 和 release reachability；不把 object URL 当 durable asset，不合并 upload/history/material/asset surface，不接真实 provider/storage，未授权不改代码 |
| 修改图片工具动作 | [`LIBTV_IMAGE_ACTION_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | `ImageNode.spec.md`、相关 source evidence | 标注/预览/旋转/图层分离不是同一种 `addDerivedNode` 副作用 |
| 修改 Auto Link | [`LibTVAutoLink.contract.md`](research/components/LibTVAutoLink.contract.md)、[`LIBTV_AUTOLINK_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md) | [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 不把 graph edge、reference role、mention token 合并；没有 fixture 不操作共享源站 |
| 修改 Seedance 参数/视频生成 | [`LIBTV_FEATURE_GAP_MATRIX.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)、[`VideoGenerationPanel.spec.md`](research/components/VideoGenerationPanel.spec.md) | [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)、Batch 21/22、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 采样数字和菜单可见性都不是永久后端契约；不接真实 Provider，不把 UI 可选误写成 runner 可执行 |
| 修改片段重拍/逐帧拉片/长视频 | [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md)、[`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)、[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | `SegmentReshootPanel.spec.md`、`ShotBreakdownNode.spec.md`、`LongVideoProcessNode.spec.md`、对应 Batch | 分开 source/version/run/result/save；异步 completion 必须声明 operation/run/result、stale policy、selection/history/resource；没有 ready-video/process fixture 时标记 `BLOCKED_BY_FIXTURE` |
| 修改 LibTV selection/focus/快捷键/帮助面板 | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)、[`KeyboardShortcutsDialog.spec.md`](research/components/KeyboardShortcutsDialog.spec.md) | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、Batch 3/4/6/7/50、`page.tsx` handler、相关 store action | selection 不是 focus，chord 不是 command；先解析 node/edge/primary selection、foreground context 和 local/native/route precedence；没有 source/fixture 不猜 `L`/Enter/Option-drag 或 modal exact behavior |
| 修改 LibTV overlay/uiStore/关闭语义 | [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | Batch 11/50、[`PAGE_TOPOLOGY.md`](research/PAGE_TOPOLOGY.md)、对应 surface component spec | 先区分 top-level 互斥、route-local confirmation、节点相对 surface、active tool 和 Director；不把兼容 state 当 mounted UI，不默认统一 outside/Escape/keyboard/focus 策略 |
| 修改 LibTV 命令结果/错误/进度/提示 | [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、对应 command/component contract | [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | 先定 disposition/reason/owner/primary surface；不以 toast 代替 workflow，不把 display string 当 reason，不让 stale completion 宣告当前成功，不复用 FrameOS toast |
| 修改 LibTV graph/edge/history/delete/多画布 | [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、[`LibTVGraphConnection.contract.md`](research/components/LibTVGraphConnection.contract.md)、[`LibTVGraphDocument.contract.md`](research/components/LibTVGraphDocument.contract.md)、[`LibTVSubgraphCopy.contract.md`](research/components/LibTVSubgraphCopy.contract.md)、[`LibTVNodeDataIdentity.contract.md`](research/components/LibTVNodeDataIdentity.contract.md)、[`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](research/LIBTV_VERIFIER_REPLACEMENT_MAP.md)、Batch 5/8/16/24/26/33/57/58 | 先给入口/owner 定 authority；React Flow callback 先整批分类且只放行 T0/T1；canvas switch 保持 graph/viewport/history、清 selection、取消旧 page transaction；reject/unknown 零 mutation；copy/delete/restore 不得绕过专属合同 |
| 修改 FrameOS | [`research/frameos/IMPLEMENTATION.md`](research/frameos/IMPLEMENTATION.md)、[`research/frameos/RUNBOOK.md`](research/frameos/RUNBOOK.md) | [`research/frameos/BEHAVIORS.md`](research/frameos/BEHAVIORS.md)、[`frameosStore` 相关代码] | 不引入 LibTV store/data；处理 xyflow selected-state reset |
| 研究 LibTV 源站 | [`research/INSPECTION_GUIDE.md`](research/INSPECTION_GUIDE.md)、[`research/liblib-live-2026-08-25/README.md`](research/liblib-live-2026-08-25/README.md) | 目标能力的专项 `LIVE_AUDIT.md`、`SCREENSHOT_ANALYSIS.md`、bundle evidence | 先查已有截图分析；不在共享项目输入/提交/上传/保存/生成 |
| 做源站 freshness refresh | [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](research/LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)、[`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md) | [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、旧 dated source JSON/截图 | 只读复核 page shell、已有节点、浮层和响应式；遇到输入/提交/graph mutation 立即停止，不把共享项目当可重置 fixture |
| 规划 verifier replacement | [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](research/LIBTV_VERIFIER_REPLACEMENT_MAP.md)、[`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md) | [`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md)、[`LIBTV_VERIFICATION_COVERAGE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)、对应 Batch `IMPLEMENTATION.md` | 历史断言先保留并标版本；没有 current source、fixture 和编码授权，不删除/放宽旧断言 |
| 研究 Open Canvas / 将启发交接给 LibTV | [`research/open-canvas-2026-08-26/README.md`](research/open-canvas-2026-08-26/README.md)、[`ADOPTION_DECISION_MATRIX.md`](research/open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md) | [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](research/open-canvas-2026-08-26/NEXT_EVIDENCE_ACQUISITION_PLAN.md)、固定 submodule、[`SOURCE_ANALYSIS.md`](research/open-canvas-2026-08-26/SOURCE_ANALYSIS.md)、[`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](research/open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md)、[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、[`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、[`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](research/open-canvas-2026-08-26/UPSTREAM_VERSION_IMPACT_PROTOCOL.md) | 上游是启发，不是 LibTV 视觉或行为真相；同时记录可借结构和上游反例；URL/hydrate、toast/node/save surface、selected flags/Radix、dual anchor/live viewport、validate/probe/materialize/resource lease 等方法必须转译到现有 in-place owner，不复制产品路由/视觉/依赖/storage；没有 source/parity/fixture/verifier/授权链时停在文档；未经批准不移动 submodule |
| 复刻 website/新能力立项 | [`../.codex/skills/clone-website/SKILL.md`](../.codex/skills/clone-website/SKILL.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 目标路由的源站证据和组件合同 | 用户未明确授权编码时只做研究/计划/文档 |
| 只做文档维护 | [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md)、[`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md) | [`DOCUMENTATION_PLAN.md`](DOCUMENTATION_PLAN.md)、[`docs/index.md`](index.md)、[`research/README.md`](research/README.md) | 先判断当前指引/历史合同/兼容入口/证据/WIP；新正式文档更新 docs index；不改代码 |
| 修改 Next.js API | `AGENTS.md` 的硬约束 | `node_modules/next/dist/docs/` 相关指南、`DEVELOPMENT.md` | 先读本地 Next 文档，再最小修改并运行对应验证 |

## 3. 证据读取顺序

### 3.1 源站复刻

```text
现有 SCREENSHOT_ANALYSIS / LIVE_AUDIT
  -> 当前 DOM / computed style / bundle
  -> 组件合同
  -> clone 当前代码和验证脚本
  -> 研究或实现记录
```

不要先打开一张截图再凭视觉写代码。需要重新操作源站时，先确认登录态、共享项目、是否会产生 graph mutation，以及是否有可丢弃 fixture。

### 3.2 Open Canvas 借鉴

```text
固定 submodule commit
  -> SOURCE_ANALYSIS / EVIDENCE_MATRIX
  -> 一张 pattern card
  -> LibTV 源站证据
  -> ADOPTION_DECISION_MATRIX
  -> parity / fixture / verifier
  -> LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT
  -> 获授权后的单一纵向 slice
```

上游源码不能填补 LibTV 的未知行为。只能借鉴已经被 LibTV 问题验证过的抽象，例如统一 screen anchor、结构化引用身份、状态分离和子图 ID 映射。
如果上游 commit 变化，先按 `UPSTREAM_VERSION_IMPACT_PROTOCOL` 比较 immutable SHA 并重审受影响主张；不能先移动 submodule 再改写研究结论。

### 3.3 代码修改

```text
明确授权
  -> 对应组件合同
  -> 最小 slice
  -> local/disposable fixture
  -> 窄 Playwright
  -> npm run check
  -> 实施记录和 commit/push
```

若其他开发者 WIP 造成测试阻塞，记录阻塞并保持业务实现不动；只有接口稳定时才可做最小测试夹具适配。

## 4. 输出模板

### 研究输出

- `SOURCE_FACT`：直接观察或固定源码支持的事实；
- `ARTICLE_EVIDENCE`：第三方文章截图/陈述，只作为线索；
- `OPEN_CANVAS_INSPIRATION`：上游提供的通用机制；
- `INFERENCE`：从证据推导的解释；
- `CLONE_DECISION`：当前 prototype 的局部选择；
- `BLOCKED_BY_FIXTURE`：需要独立可丢弃项目/素材才能继续的未知。

### 实施输出

- 目标 slice 和不包含的范围；
- 触及的 route/store/component；
- 源站合同与 clone-only 选择；
- 桌面、移动、zoom、selection、graph/history 验证；
- 未解决问题、测试阻塞和下一步。

## 5. 最短安全检查清单

1. 我是否确认了任务属于 LibTV、FrameOS、共享基础设施还是纯文档？
2. 我是否读了对应组件合同和已有截图分析？
3. 我是否把源站事实、推断和 clone 决策分开？
4. 我是否会触发共享源站写入、任务消耗或 graph mutation？
5. 我是否知道最窄验证命令和需要更新的实施/研究记录？
6. 我是否会只暂存自己的路径，并保留其他人的 WIP？

不能回答其中任一项时，先停在文档和证据整理，不开始编码。
