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
| 启动/验证本地项目 | [`DEVELOPMENT.md`](DEVELOPMENT.md)、[`HARNESS.md`](HARNESS.md) | [`QUALITY.md`](QUALITY.md) | 先确认端口和其他开发者 server，不覆盖现有进程 |
| 修改 LibTV 节点/面板 | [`ARCHITECTURE.md`](ARCHITECTURE.md)、[`research/components/COVERAGE_MATRIX.md`](research/components/COVERAGE_MATRIX.md)、对应 `research/components/*.spec.md` | [`BEHAVIORS.md`](research/BEHAVIORS.md)、对应 Batch `PLAN.md`/`IMPLEMENTATION.md` | 先确认是独立 spec、父合同、批次合同还是 `NEEDS_SPEC`；不以旧截图或相似项目替代当前源站合同 |
| 修复图片节点上下浮层 | [`ImageNode.spec.md`](research/components/ImageNode.spec.md)、[`ImageEditPanel.spec.md`](research/components/ImageEditPanel.spec.md) | [`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)、[`LIBTV_VERIFICATION_COVERAGE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md) | 先确认 measured size、live viewport、selection lifecycle；不先凭感觉改 offset/clamp |
| 修改图片工具动作 | [`LIBTV_IMAGE_ACTION_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | `ImageNode.spec.md`、相关 source evidence | 标注/预览/旋转/图层分离不是同一种 `addDerivedNode` 副作用 |
| 修改 Auto Link | [`LibTVAutoLink.contract.md`](research/components/LibTVAutoLink.contract.md)、[`LIBTV_AUTOLINK_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md) | [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 不把 graph edge、reference role、mention token 合并；没有 fixture 不操作共享源站 |
| 修改 Seedance 参数/视频生成 | [`LIBTV_FEATURE_GAP_MATRIX.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)、[`VideoGenerationPanel.spec.md`](research/components/VideoGenerationPanel.spec.md) | Batch 21/22、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 采样数字不是永久后端契约；不接真实 Provider |
| 修改片段重拍/逐帧拉片/长视频 | [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | `SegmentReshootPanel.spec.md`、`ShotBreakdownNode.spec.md`、`LongVideoProcessNode.spec.md`、对应 Batch | 没有 ready-video/process fixture 时标记 `BLOCKED_BY_FIXTURE` |
| 修改 LibTV graph/edge/history | [`ARCHITECTURE.md`](ARCHITECTURE.md)、[`LAYERS.md`](LAYERS.md) | 相关 Batch `PLAN.md`/`IMPLEMENTATION.md`、`canvasStore` 组件合同 | 保持 edge flow effect、Handle 和 atomic history 语义；先定义 mutation 边界 |
| 修改 FrameOS | [`research/frameos/IMPLEMENTATION.md`](research/frameos/IMPLEMENTATION.md)、[`research/frameos/RUNBOOK.md`](research/frameos/RUNBOOK.md) | [`research/frameos/BEHAVIORS.md`](research/frameos/BEHAVIORS.md)、[`frameosStore` 相关代码] | 不引入 LibTV store/data；处理 xyflow selected-state reset |
| 研究 LibTV 源站 | [`research/INSPECTION_GUIDE.md`](research/INSPECTION_GUIDE.md)、[`research/liblib-live-2026-08-25/README.md`](research/liblib-live-2026-08-25/README.md) | 目标能力的专项 `LIVE_AUDIT.md`、`SCREENSHOT_ANALYSIS.md`、bundle evidence | 先查已有截图分析；不在共享项目输入/提交/上传/保存/生成 |
| 研究 Open Canvas | [`research/open-canvas-2026-08-26/README.md`](research/open-canvas-2026-08-26/README.md)、固定 submodule | [`SOURCE_ANALYSIS.md`](research/open-canvas-2026-08-26/SOURCE_ANALYSIS.md)、[`OPEN_CANVAS_PATTERN_CARDS.md`](research/open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md) | 上游是启发，不是 LibTV 视觉或行为真相；不修改 submodule |
| 复刻 website/新能力立项 | [`../.codex/skills/clone-website/SKILL.md`](../.codex/skills/clone-website/SKILL.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 目标路由的源站证据和组件合同 | 用户未明确授权编码时只做研究/计划/文档 |
| 只做文档维护 | [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md)、[`DOCUMENTATION_PLAN.md`](DOCUMENTATION_PLAN.md) | [`docs/index.md`](index.md)、[`research/README.md`](research/README.md) | 新正式文档更新 docs index；新研究更新 research index；不改代码 |
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
  -> clone-only 决策
```

上游源码不能填补 LibTV 的未知行为。只能借鉴已经被 LibTV 问题验证过的抽象，例如统一 screen anchor、结构化引用身份、状态分离和子图 ID 映射。

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
