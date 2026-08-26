# 验证能力台账

> 目的：区分“有研究目录”“有 verifier”“最近有记录通过”“只有源站合同”“被 fixture 阻塞”和“并行 WIP”，防止把不同成熟度混成一个绿色状态。
>
> 本台账只记录当前仓库可发现的验证能力。Batch 48 的浏览器脚本、
> 截图和实施结果已经单独落档；后续批次仍需按同样边界增量维护。

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
Batch 35-48
```

Batch 34 没有专项 verifier，是导演台代码考古/研究批次。不要使用会隐式跨过 Batch 34 的 `{4..44}` shell glob。

### 2.2 脚本分组台账

| 脚本范围 | 主题 | 当前状态 | 主要限制 |
|---|---|---|---|
| `verify-liblib-batch4.py` - `batch8.py` | 分组、多选、移动、复制、导航、整理、视频 parent-child | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 只覆盖各批 clone 合同，不是全量源站回归 |
| `verify-liblib-batch9.py` - `batch11.py` | 图片/视频浮层、图片编辑状态、顶层 overlay 生命周期 | `SCRIPT_AVAILABLE` / `HISTORICAL_CONTRACT` | Batch 9 的 `900.5px`/旧 top gap 和 Batch 10 的旧 AutoLink 不覆盖当前合同 |
| `verify-liblib-batch12.py` - `batch20.py` | 资产、分镜、Agent/share、canvas metadata、zoom、minimap、全景 | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 依赖本地 demo 数据和当时的 clone 状态 |
| `verify-liblib-batch21.py` - `batch25.py` | Seedance 参数/模型、片段重拍、逐帧拉片、智能剪辑空态 | `SCRIPT_AVAILABLE` / `CLONE_FIXTURE_ONLY` | 结果任务、ready-video 源站入口和真实 provider 未验证 |
| `verify-liblib-batch26.py` - `batch33.py` | 续写、去字幕、音视频分离、帧截取、主体编辑、深度、长视频 | `SCRIPT_AVAILABLE` / `CLONE_FIXTURE_ONLY` | 主要验证本地 graph、状态和 undo；源站结果态存在 fixture 阻塞 |
| `verify-liblib-batch35.py` - `batch48.py` | Director R3F、时间轴、路径、导出、手机相机、角色、跟随、运镜、群组/群众、截图图库、模型库、本地模型导入/持久化 | `SCRIPT_AVAILABLE` / `SCRIPT_RECORDED_PASS` | 是有界 prototype 回归；不是 LibTV/FrameOS 通用行为合同 |
| Batch 34 | Director 既有代码考古和可借鉴性 | `SOURCE_CONTRACT_ONLY` | 没有专项 verifier，不应在全量命令中伪造 |
| Batch 45 | Director character groups/crowd/group tracks | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-45 serial regression 已通过；仍是有界 clone 合同 |
| Batch 46 | Director camera screenshot gallery and bulk return | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-46 serial regression 已通过；仍是有界 clone 合同 |
| Batch 47 | Director model-library categories, proxy insertion and responsive panel | `SCRIPT_RECORDED_PASS` | focused Playwright 与 Batch 35-47 serial regression 已通过；模型/环境真实资产仍明确不在合同内 |
| Batch 48 | Director local model import, persistence, refresh, re-add and delete cleanup | `SCRIPT_RECORDED_PASS` | focused Playwright 已通过；只验证 clone-owned browser-local descriptors 和 proxy objects，不证明真实 FBX/OBJ loading 或 LibTV persistence |

## 3. 当前源站合同覆盖

| 能力/合同 | 当前状态 | 已有证据 | 缺口/下一步 |
|---|---|---|---|
| 图片标准双浮层 | `SOURCE_CONTRACT_ONLY` | [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) | 授权后补当前动作集合、拖动/平移时序和 clone screen rect 回归 |
| 当前顶部工具条 | `SOURCE_CONTRACT_ONLY` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md) | clone 仍需授权后更新动作集合和版本化断言 |
| active image tool | `SOURCE_CONTRACT_ONLY` | [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | 预览/空标注可低风险，旋转/图层分离需 fixture |
| Auto Link | `SOURCE_CONTRACT_ONLY` | [`LIBTV_AUTOLINK_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)、[`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md) | 需要 editor token、竞态和 graph/reference/mention 事务回归 |
| Seedance 普通/超长参数 | `SOURCE_CONTRACT_ONLY` + `CLONE_FIXTURE_ONLY` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 21/22 | 需区分源站采样值、clone 本地参数和真实 provider |
| 片段重拍 | `BLOCKED_BY_FIXTURE` | bundle 文案、文章证据、Batch 23 clone fixture | 需要 disposable ready-video source fixture 和时间范围/版本合同 |
| 逐帧拉片 | `BLOCKED_BY_FIXTURE` | 空态 DOM、文章结果截图、Batch 24 clone fixture | 需要 ready video 或本地固定结果 fixture 的结果/失败态 |
| 超长视频过程 | `CLONE_FIXTURE_ONLY` + `BLOCKED_BY_FIXTURE` | Batch 33 12/22 graph、文章/源站参数证据 | 需要源站过程图或稳定 mock 合同，不能把 clone graph 当源站事实 |
| 旋转/图层分离/标注保存 | `BLOCKED_BY_FIXTURE` | 当前 bundle/live 空态和一次撤销边界 | 需要 disposable 项目、任务/保存许可和可回滚方案 |

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
for script in scripts/verify-liblib-batch{4..33}.py scripts/verify-liblib-batch{35..48}.py; do
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
