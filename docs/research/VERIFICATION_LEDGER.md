# 验证能力台账

> 目的：区分“有研究目录”“有 verifier”“最近有记录通过”“只有源站合同”“被 fixture 阻塞”和“并行 WIP”，防止把不同成熟度混成一个绿色状态。
>
> 本台账只记录当前仓库可发现的验证能力。Batch 50 的浏览器脚本、
> 截图和实施结果已经单独落档；后续批次仍需按同样边界增量维护。
> fixture 身份/隔离/reset 见 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)，
> 历史断言迁移见 [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)，
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
Batch 52
Batch 53
Batch 54
Batch 56
Batch 57
```

Batch 34 没有专项 verifier，是导演台代码考古/研究批次。不要使用会隐式跨过 Batch 34 的 `{4..44}` shell glob。
Batch 57 有独立的普通连接事务 verifier。
Batch 58 有独立的 node-bound UI owner lifecycle verifier。

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
| Batch 48 | Director local model import, persistence, refresh, re-add and delete cleanup | `SCRIPT_RECORDED_PASS` | focused Playwright 已通过；只验证 clone-owned browser-local descriptors 和 proxy objects，不证明真实 FBX/OBJ loading 或 LibTV persistence |
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
| 普通画布 graph mutation ingress | `STATIC_CONTRACT_ONLY` + connection island `LOCAL_FIXTURE` | [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、`LIBTV-VR-014` design、Batch 57 | 全 writer/T0-T5 audit 已完成；derived/setter/copy/delete/restore/remote routing runtime 尚未验证或实现 |
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
for script in scripts/verify-liblib-batch{4..33}.py scripts/verify-liblib-batch{35..50}.py scripts/verify-liblib-batch52.py scripts/verify-liblib-batch53.py scripts/verify-liblib-batch54.py scripts/verify-liblib-batch56.py scripts/verify-liblib-batch57.py scripts/verify-liblib-batch58.py; do
  python3 "$script" || exit 1
done
```

这些脚本会写入带日期的视觉参考或依赖本地 dev server，因此必须串行运行；文档-only 研究不应为了更新本台账自动执行它们。

## 6. 台账维护规则

- 新增 verifier：同时更新本台账、[`HARNESS.md`](../HARNESS.md)、对应 Batch `IMPLEMENTATION.md` 和 `docs/research/README.md`；
- 修改断言：记录它覆盖的是历史合同还是当前源站合同；不能只改数字不改证据说明；
- 新增截图：先检查已有 `SCREENSHOT_ANALYSIS.md`，并记录 viewport、zoom、状态和来源；
- 被 fixture 阻塞：使用 `BLOCKED_BY_FIXTURE`，记录所需 fixture，不在共享项目试探；
- 并行 WIP：保留 `PARALLEL_WIP`，待该开发者的脚本、实施记录和验证结果稳定后再升级；
- 任何文档变更都运行 `python3 scripts/verify-docs.py`，并只提交自己的路径。
