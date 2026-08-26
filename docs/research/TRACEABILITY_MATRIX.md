# 研究主张可追溯矩阵

> 目的：从当前项目的重要产品/架构主张反查证据、适用范围和不能据此推出的结论。
>
> 本文是索引，不替代专项研究。主张 ID 只作为导航和评审引用；如果事实发生变化，应追加新证据和日期，不能静默覆盖历史快照。

## 1. 证据分类

| 类别 | 含义 | 可支持的用途 |
|---|---|---|
| `SOURCE_FACT` | LibTV/FrameOS 当前登录态 DOM、computed rect、bundle 或可重复源站交互事实 | 当前源站行为合同，带日期和状态边界 |
| `ARTICLE_EVIDENCE` | 第三方文章中的截图或陈述 | 产品线索、功能形态和待复核问题 |
| `CLONE_FACT` | 当前仓库代码、fixture 或已运行脚本直接支持 | clone 现状和历史实现合同 |
| `OPEN_CANVAS_FACT` | 固定 submodule 源码/官网研究支持 | 通用机制启发，不是 LibTV 视觉真相 |
| `INFERENCE` | 从多个事实推导的解释 | 研究假设，必须保留推理链 |
| `DECISION` | 当前项目为安全、范围或工程一致性作出的选择 | clone-only 规则，不可冒充源站事实 |

## 2. LibTV 与项目主张

| ID | 主张 | 类别 | 主要证据 | 适用范围 | 不能据此推出 |
|---|---|---|---|---|---|
| LIBTV-TR-001 | 当前项目是 LibTV + FrameOS 两条独立前端画布原型，后端服务未实现 | `CLONE_FACT` / `DECISION` | [`AGENTS.md`](../../AGENTS.md)、[`ARCHITECTURE.md`](../ARCHITECTURE.md)、[`BIG_PICTURE.md`](../BIG_PICTURE.md) | route、store、产品边界 | 不代表源站没有后端能力 |
| LIBTV-TR-002 | LibTV 图片节点标准态同时有上方工具条和下方编辑面板 | `SOURCE_FACT` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、[`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md) | 当前已观测的图片节点选择态 | 不代表 active tool 仍叠加标准双浮层 |
| LIBTV-TR-003 | 当前图片工具条使用 9 个文字动作 + 4 个图标动作，外层宽度为 `1092.5x49` | `SOURCE_FACT` | [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md) | 2026-08-26 当前采样版本 | 不覆盖 2026-08-25 的历史 `900.5x49` 快照 |
| LIBTV-TR-004 | 当前顶部工具条 host 公式为 `nodeTop - 24 * zoom - 10`，结合自身 transform 形成 `10 + 24 * zoom` 的 screen gap | `SOURCE_FACT` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | 标准图片工具条 | 不代表标注/旋转/元素编辑使用同一 host |
| LIBTV-TR-005 | 当前下方面板 gap 为 `16 * zoom`，以节点中心为横向 anchor 并保持屏幕尺寸 | `SOURCE_FACT` / `INFERENCE` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`ImageEditPanel.spec.md`](components/ImageEditPanel.spec.md) | 图片/视频节点下方面板已测场景 | 不代表任意新面板都能复用该尺寸 |
| LIBTV-TR-006 | 源站靠近画布边缘时允许浮层自然裁切，不应凭感觉移到浏览器中心 | `SOURCE_FACT` / `DECISION` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) | 当前图片节点边缘样本 | 不代表所有 page-level modal 都允许裁切 |
| LIBTV-TR-007 | 标注、元素编辑、预览、旋转、图层分离具有不同 UI/任务/graph 副作用 | `SOURCE_FACT` / `INFERENCE` | [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | 当前安全观察和 bundle 分支 | 不代表所有高风险动作的最终提交合同已确认 |
| LIBTV-TR-008 | Auto Link 是全局偏好、候选池、inline ghost 和 structured mention 的组合 | `SOURCE_FACT` | [`LIBTV_AUTOLINK_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)、[`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md) | 当前生产前端的状态链 | 不代表 clone 当前固定 popover 已经等价 |
| LIBTV-TR-009 | graph edge、reference role 和 Prompt mention 是不同关系，正式 mention 需要稳定 node identity | `SOURCE_FACT` / `DECISION` | [`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md)、[`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md) | Auto Link 和后续素材复用 | 不代表必须复制 Open Canvas 的 Handle/provider 语义 |
| LIBTV-TR-010 | Seedance 普通/超长生成面板将模型、模式、参数、音频、数量和费用放在同一提交上下文 | `SOURCE_FACT` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 21/22 研究记录 | 当前采样的生成面板 | 不代表真实 provider 或计费已接入 clone |
| LIBTV-TR-011 | `4s`、最多 `5` 段、`30-300s`、`300s / 14700` 是采样时产品表现，不是永久 API 合同 | `SOURCE_FACT` / `DECISION` | [`LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)、[`LIBTV_DEPENDENCY_RISK_QUEUE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 文章、bundle 和现场交叉解释 | 不应把采样数字直接写入后端假设 |
| LIBTV-TR-012 | 逐帧拉片是独立节点，结果形态包含分镜/动态/音乐等结构化媒体卡 | `SOURCE_FACT` / `ARTICLE_EVIDENCE` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 24 记录、`evidence/` | 入口和文章结果形态 | 不代表当前共享项目已执行真实分析任务 |
| LIBTV-TR-013 | 片段重拍依赖 ready video、时间范围、Prompt token 和结果版本关系 | `SOURCE_FACT` / `ARTICLE_EVIDENCE` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 23、[`LIBTV_DEPENDENCY_RISK_QUEUE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 入口文案、bundle 和文章截图 | 不代表共享项目具备安全 ready-video fixture |
| LIBTV-TR-014 | 超长视频过程图和局部重算的源站状态仍不完整，当前 clone 的 12 节点/22 边只是本地 prototype fixture | `CLONE_FACT` / `ARTICLE_EVIDENCE` / `INFERENCE` | Batch 33、[`LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md) | 区分 clone 形态和源站未知 | 不代表源站真实任务拆分已经复刻 |
| LIBTV-TR-015 | 研究阶段没有明确编码授权时，不修改 `src/`、回归脚本或共享源站状态 | `DECISION` | [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)、[`DECISION_REGISTER.md`](../DECISION_REGISTER.md) | 当前研究-only 工作 | 用户明确授权后可按单 slice 进入编码 |

## 3. Open Canvas 启发主张

| ID | 主张 | 类别 | 主要证据 | 可迁移范围 | 不能据此推出 |
|---|---|---|---|---|---|
| OC-TR-001 | Open Canvas 固定版本使用 measured node + live viewport 组织 selected editor/action overlay | `OPEN_CANVAS_FACT` | [`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)、上游 [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964) | 统一 screen anchor 的方法 | 不替代 LibTV 的 gap、Panel 层级或裁切合同 |
| OC-TR-002 | Open Canvas 将 typed inputs 分桶，最后才投影到 provider route/task descriptor | `OPEN_CANVAS_FACT` | [`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)、上游 [`execution.ts`](../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L69) | 稳定引用身份和请求投影分离 | 不代表 LibTV 使用同样 provider 或 scene 名 |
| OC-TR-003 | Open Canvas 把 node status、run status、save/conflict status 分开 | `OPEN_CANVAS_FACT` | 上游 [`types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L60)、[`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38) | 过程型 UI 的状态分层 | 不代表当前 clone 已有真实任务或保存后端 |
| OC-TR-004 | Open Canvas 复制粘贴以结构化子图和 ID map 保持内部边关系 | `OPEN_CANVAS_FACT` | 上游 [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896)、[`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339) | 派生/复制时的身份与坐标边界 | 不代表 LibTV 的历史候选必须改成复制子图 |

## 4. 证据更新规则

### 4.1 什么会使主张过期

- 同一源站路径在新日期出现不同 DOM/行为；
- 生产 chunk 或当前 route 版本改变，使旧公式/按钮集合不再适用；
- clone 实现或 verifier 更新，使原来的 `CLONE_FACT` 只剩历史意义；
- Open Canvas submodule 更新，导致固定行号或调用链改变；
- 用户授权后某个 clone-only 决策被实现并形成新的实施合同。

### 4.2 更新动作

1. 在专项证据文档追加新的观察或实施记录；
2. 在本表增加或更新主张 ID 的状态和日期；
3. 将旧主张标为 `HISTORICAL`，不要无说明删除；
4. 更新 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的覆盖解释；
5. 运行 `python3 scripts/verify-docs.py`，并对文档变更做 path-scoped commit/push。

## 5. 当前最重要的反向查找

| 想确认什么 | 从哪里开始 |
|---|---|
| 图片双浮层为什么会乱 | LIBTV-TR-002 到 LIBTV-TR-007 |
| Auto Link 是否只是字符串前缀 | LIBTV-TR-008、LIBTV-TR-009 |
| Seedance 文章数字能否直接写死 | LIBTV-TR-010、LIBTV-TR-011 |
| 长视频/重拍是否已经完成 | LIBTV-TR-012 到 LIBTV-TR-014，再查验证台账 |
| Open Canvas 能借鉴什么 | OC-TR-001 到 OC-TR-004，再查模式卡 |
| 现在能不能编码 | LIBTV-TR-015 和 [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) |

