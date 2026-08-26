# LibTV Seedance 2.5 能力缺口总矩阵

> 目的：回答“LibTV 当前有什么、在画布上如何呈现、clone 还缺什么、下一步值不值得做”。
> 本文只研究 LibTV 的产品表现，不采纳外部调研文档对其他项目的实现展望；没有用户授权时，不修改 `src/`。
>
> 本文继续负责 Seedance 五项能力；跨 page shell、selected-node、active tool、
> shortcut、overlay 和 graph 的当前统一排序见
> [`../LIBTV_UIUX_PARITY_BACKLOG.md`](../LIBTV_UIUX_PARITY_BACKLOG.md)。
>
> 进入后续研究/复刻前，先用 [`../LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md) 判断状态是否可重复，用 [`../LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../LIBTV_VERIFIER_REPLACEMENT_MAP.md) 判断历史断言是否可迁移，并用 [`../TRACEABILITY_MATRIX.md`](../TRACEABILITY_MATRIX.md) 反查主张证据；跨项目授权和安全红线见 [`../../DECISION_REGISTER.md`](../../DECISION_REGISTER.md)。

## 1. 阅读结论

当前 LibTV 的 Seedance 2.5 亮点不是五个孤立按钮，而是围绕“一个素材节点”组织的四层工作流：

```text
素材节点
├── 生成：模型 / 模式 / 参数 / 音频 / 费用在同一个提交上下文
├── 编辑：片段重拍、续写、去字幕、主体处理等节点上下文动作
├── 分析：逐帧拉片把视频变成分镜、动态和音乐等可复用产物
└── 编排：Auto Link 和超长视频把素材、提示词、子任务和结果组织起来
```

因此，clone 的关键缺口不是“再加几个中文按钮”，而是没有完整表达以下状态边界：

1. 入口、编辑草稿、任务提交和结果节点是不同阶段；
2. 结果应该继续出现在画布上，并能成为后续输入；
3. 自动匹配需要可检查、可替换的中间态；
4. 高成本或可能改变 graph 的动作必须有明确的提交/撤销边界。

## 2. 证据等级

| 等级 | 含义 | 本文处理方式 |
|---|---|---|
| `SOURCE_FACT` | 当前登录态 DOM、当前生产 bundle 或可重复几何直接支持 | 可作为 clone 研究合同，但仍记录采样日期 |
| `ARTICLE_EVIDENCE` | 2026-08-07 第三方文章截图或文章陈述 | 只证明产品线索和展示形态，不推断后端事实 |
| `SOURCE_INFERENCE` | 根据源站 UI、状态命名和模型边界作出的解释 | 必须标注推断，不得写成 LibTV 官方架构 |
| `CLONE_FACT` | 当前仓库代码或已有 Playwright 记录直接支持 | 只说明 clone 现状，不等于源站行为 |
| `CLONE_DECISION` | 面向后续 prototype 的待授权选择 | 不得在未授权时转成代码 |

## 3. 五项主推能力总矩阵

| LibTV 能力 | 源站呈现 | 最高证据 | 当前 clone | 关键缺口 | 价值/优先级 |
|---|---|---|---|---|---|
| Seedance 2.5 生成 | 视频节点下方 `660px` 生成面板；模型、模式、比例、清晰度、时长、音频、数量、预计积分同屏；模式/模型/参数使用邻近 popover | `SOURCE_FACT`：模型、模式、`4-30s`、`30-300s`、`300s / 14700` 已现场读取 | 已有参数面板和本地提交态 | 图片/视频浮层动作集合和源站当前版本持续漂移；真实 Provider 不在原型边界 | P0：决定主流程是否像 LibTV |
| 片段重拍 | 就绪视频顶部工具栏进入；横向时间带以 `4s` 为粒度；最多 `5` 段；选区写入 Prompt 的视频/时间范围 token；提交后只替换目标区间 | `ARTICLE_EVIDENCE` + `SOURCE_FACT`：bundle 文案和文章截图；当前共享项目没有可安全执行的就绪视频 | 已有五段选择、disabled 尾段、token 投影和本地提交反馈 | 尚缺当前登录态就绪视频的实际入口、替换结果和边界帧行为 | P1：高频、高识别度；需可丢弃素材 |
| Auto Link | 高级设置中的全局开关；从 connected/reference 素材池匹配；Prompt 内联 ghost 建议；逐项或全量接受后生成带 node ID/media type/ordinal 的正式 mention | `SOURCE_FACT`：当前 bundle + 图片/视频面板 DOM | 已有固定候选、独立确认 popover、批量写入字符串 | 候选作用域、ghost 生命周期、单项接受/替换/撤销和正式 token 语义不一致 | P0：影响引用可信度和所有生成入口；合同见 [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md) |
| 超长视频 Beta | 生成模式中的独立入口；参数允许 `30-300s`；底栏显示 `300s / 14700`；查看过程后在画布中观察素材、镜头、候选和成片关系 | `SOURCE_FACT`：模式与参数；`ARTICLE_EVIDENCE`：过程图 | 已有 12 节点/22 边的本地 pending 过程图和 atomic undo/redo | 源站过程图的真实状态、局部重算、版本替换和费用/任务拆分仍未现场完成 | P1：价值高但状态和成本复杂；先保持只读过程 |
| 逐帧拉片 | 视频工具栏或独立节点进入；选择“分镜/动态/音乐”；结果是 `S01...` 关键帧、`M01...` 动态片段、BGM 波形卡，可继续作为参考 | `SOURCE_FACT`：独立 `shot-breakdown` 空态；`ARTICLE_EVIDENCE`：结果截图；bundle 有失败/处理中状态 | 已有独立节点、三维度选择和持久化结果组 | 当前项目没有真实就绪视频，因此尚缺当前结果态、分析进度和重试细节 | P1：能把“分析”转成可复用素材，产品差异明显 |

### 3.1 相邻但不可混并的 LibTV 能力

| 能力 | 源站边界 | clone 研究处理 |
|---|---|---|
| 智能剪辑 Beta | 独立 `video-clip` 节点，四种剪辑模式，不等于逐帧拉片 | 保持独立节点，不把它并入 Seedance 生成面板 |
| 图片节点工具 | 当前图片工具条已包含人像质感、全景、多角度、打光、九宫格、高清、元素编辑、图层分离、宫格切分及标注/旋转/下载/预览 | 标准双浮层与 active-tool 替换合同优先于逐个补按钮；详见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md) |
| 视频后处理 | 就绪视频才显示顶部处理工具条；失败视频当前主要展示生成面板 | 不得用失败视频的 DOM 推断就绪态工具条布局 |

## 4. 当前 clone 差距清单

### P0：先修“状态和呈现”

| 差距 | 源站事实 | clone 现状 | 最小可验证目标 |
|---|---|---|---|
| 图片标准双浮层 | 上方 toolbar 与下方 panel 同时锚定节点中心；toolbar 当前 `1092.5x49`，panel `660px`，上下间距都随 zoom 参与计算 | 仍是旧动作集合和旧顶部 `NodeToolbar offset=16`；下方面板合同已较接近 | 先锁定当前动作集合、screen rect、active-tool 替换，再改视觉；合同见 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) |
| 图片动作语义 | 预览是 page overlay；标注/元素编辑是 local authoring；旋转可能创建派生节点；图层分离是异步 composition | `ImageNode` 将多数动作统一走 `addDerivedNode` | 每个入口至少有独立状态分类；未实现动作显示 prototype 边界，不伪造完成结果 |
| Auto Link | 全局偏好 + candidate pool + inline ghost + structured mention | 固定候选 + confirmation popover + 字符串前缀写回 | 先把 source/clone 差异写成测试合同，后续授权后再拆状态，不继续扩大旧 popover |
| 生成参数上下文 | 参数和费用靠近提交；模式改变会联动时长、数量和可用状态 | 已有 clone 参数模型，需持续避免把数字写成模型永久契约 | 验证每次 mode change 的 control matrix、费用公式和 disabled 状态都来自明确本地原型规则 |

### P1：形成“素材可再利用”闭环

| 差距 | 源站目标体验 | clone 当前可复用基础 | 下一步 |
|---|---|---|---|
| 片段重拍 | 选区、Prompt token、替换版本和原视频关系可追溯 | `SegmentReshootPanel` 已有 filmstrip 和本地状态 | 只在 disposable ready-video fixture 上补 source 几何/结果边界；不改真实项目 |
| 逐帧拉片 | 分析结果是结构化图像/视频/音频卡，不是分析文本 | `shot-breakdown` 与 result groups 已有持久 graph 形态 | 先用固定 fixture 验证结果卡之间的 selection、source ID、时间范围和重试态 |
| 超长视频过程 | 多任务过程必须能查看并定位到中间镜头 | 本地 12/22 graph 已有状态和 undo | 只补过程状态和局部版本语义，不扩展到模拟真实 provider 进度 |

### P2：高风险或证据未闭环的动作

| 差距 | 为什么暂缓 |
|---|---|
| 图层分离 | bundle 中存在 splitting、redrawing、merging、任务提交和 composition patch，入口可能改变远端/graph 状态 |
| 旋转与镜像 | 当前共享 fixture 的入口点击已实际产生“旋转与镜像”派生节点；虽然已撤销，但不能把入口当成纯 local CSS 编辑 |
| 标注 dirty/保存 | 空态进入已证实，绘制后退出确认和保存写入尚未在可丢弃副本上验证 |
| 下载水印分支 | 需要读取会员/水印偏好并触发浏览器下载，和纯 DOM 研究不同 |

## 5. 源站如何组织这些能力

### 5.1 节点是上下文，而不是单纯卡片

源站把当前选中的图片或视频作为操作上下文：顶部工具条表达“对这个节点做什么”，下方编辑面板表达“准备提交什么”。节点失去选择时，两个浮层一起卸载；进入 active tool 时，标准双浮层被替换，而不是继续叠加第三层。

这解释了为什么位置合同必须拆成 toolbar/panel 两条公式，也解释了为什么图片动作不能都调用一个 `addDerivedNode`：呈现层、草稿层和 graph 写入层并不相同。

### 5.2 参数、费用和提交保持同一动作上下文

Seedance 2.5 的模型和模式在输入区附近选择；时长、清晰度、画幅、音频、数量和预计积分紧邻提交按钮。`超长视频` 虽然把单次参数延展到 `300s`，仍然使用同一生成上下文，而不是跳到另一套孤立页面。

### 5.3 自动化先给候选，再变成正式引用

Auto Link 的当前实现不是把画布素材静默塞进请求，而是先在 Prompt 内形成 ghost suggestion，再由用户逐项接受。正式 mention 保存稳定节点身份和媒体职责，后续模型编号只是提交时的投影。这种分层是 clone 后续做“引用可信度”的最低必要条件。

### 5.4 结果回到画布，形成可解释的派生关系

片段重拍、逐帧拉片和超长视频都将结果或过程放回画布附近：用户可以从源节点找到时间范围、派生结果和中间镜头，而不是只得到一个无法追溯的下载文件。clone 已经有多种本地派生节点基础，但还需要统一保存 source ID、时间范围、操作类型和版本。

## 6. 价值排序与后续队列

这里的排序只表示“复刻 LibTV UI/UX 的研究和原型价值”，不是后端交付承诺：

| 顺序 | 研究/实现主题 | UI/UX 价值 | 证据成熟度 | 风险 | 决策 |
|---:|---|---:|---:|---:|---|
| 1 | 图片双浮层当前动作集合、active-tool 替换和定位公式 | 5 | 5 | 2 | 已形成合同；等待编码授权 |
| 2 | Auto Link inline ghost 与 structured mention | 5 | 4 | 3 | 先补测试/状态设计，再申请编码 |
| 3 | 就绪视频工具条与片段重拍上下文 | 5 | 3 | 4 | 需要 disposable ready-video fixture |
| 4 | 逐帧拉片结果卡与可复用引用 | 5 | 4 | 3 | 可用本地固定 fixture 做只读验证 |
| 5 | 超长视频过程图只读审阅 | 4 | 3 | 4 | 保持当前本地过程图边界 |
| 6 | 标注空态和预览 | 4 | 5 | 1 | 研究证据完整，适合授权后小批实现 |
| 7 | 旋转、图层分离、下载水印 | 4 | 2 | 5 | 暂停 live 探索，等可丢弃副本/明确授权 |

## 7. 后续工作闸门

在用户明确允许编码前，本项目只做以下工作：

- 读取源站 DOM、生产 chunk、已有截图和结构化 JSON；
- 读取 clone 代码并记录真实差距；
- 补充研究文档、组件合同、验证断言和批次计划；
- 在不提交任务、不上传、不保存的前提下复核安全的空态或只读状态；
- 每个关键研究批次单独提交并推送。

获得编码授权后，每个主题仍需先读对应组件规格，再小范围实现并验证：

```text
研究证据 -> 组件合同 -> 明确授权 -> 最小实现 -> 浏览器验证 -> 实施记录 -> commit/push
```

## 8. 证据索引

- 外部能力输入：`/Users/yangjiefeng/.hermes/workspace/seedance-research/docs/drafts/视频模型/LibTV-Seedance2.5功能调研与实现展望-2026-08-07.md`（仓库外原始输入，不建立仓库内相对链接）
- 当前登录态总审计：[`LIVE_AUDIT.md`](LIVE_AUDIT.md)
- 源站动作状态：[`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)
- Auto Link 状态：[`LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)
- Auto Link 组件合同：[`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)
- 双浮层多 zoom：[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)
- 图片组件合同：[`ImageNode.spec.md`](../components/ImageNode.spec.md)、[`ImageEditPanel.spec.md`](../components/ImageEditPanel.spec.md)
- 视频工作流合同：[`VideoGenerationPanel.spec.md`](../components/VideoGenerationPanel.spec.md)、[`SegmentReshootPanel.spec.md`](../components/SegmentReshootPanel.spec.md)
- Fixture 与 reset 合同：[`LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md)
- 历史 verifier replacement：[`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../LIBTV_VERIFIER_REPLACEMENT_MAP.md)
- 主张证据与不可推出结论：[`TRACEABILITY_MATRIX.md`](../TRACEABILITY_MATRIX.md)
- 跨项目长期决策：[`../../DECISION_REGISTER.md`](../../DECISION_REGISTER.md)
