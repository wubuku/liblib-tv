# Open Canvas 对 LibTV Seedance 2.5 画布能力的交叉研究

> 定位：把 Open Canvas 的可迁移交互/数据机制，与当前项目已经取证和复刻的 LibTV Seedance 2.5 能力进行对照。
> 本文回答“Open Canvas 能给 LibTV 后续 UI/UX 什么启发”，不重新定义 LibTV 功能，也不授权修改业务代码。

## 1. 输入与证据边界

### 1.1 LibTV 能力输入

主要输入是用户指定的外部调研文档：

```text
/Users/yangjiefeng/.hermes/workspace/seedance-research/docs/drafts/视频模型/LibTV-Seedance2.5功能调研与实现展望-2026-08-07.md
```

该文档明确区分文章陈述、截图观察、实现推断和另一个项目的实现展望。本交叉报告只采用其中关于“LibTV 有什么、画布上如何呈现”的内容，不采用它面向 scenemill 的实施方案作为当前 clone 规格。

当前仓库的原站复核和实现边界见：

- [`LibTV Seedance 2.5 画布能力研究`](../liblib-seedance-2.5-2026-08-25/README.md)；
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)；
- [`IMPLEMENTATION.md`](../liblib-seedance-2.5-2026-08-25/IMPLEMENTATION.md)；
- [`VideoGenerationPanel.spec.md`](../components/VideoGenerationPanel.spec.md)；
- [`LongVideoProcessGraph.spec.md`](../liblib-canvas-batch33-2026-08-26/LONG_VIDEO_PROCESS_GRAPH.spec.md)。

### 1.2 Open Canvas 输入

Open Canvas 以 git submodule 固定在 `cf3a906bb8c35bb940d3267497e7f394b8f42582`。本报告只引用其固定源码事实，不把官网 preview、README provider 宣称或未执行的真实 provider 请求当作可用能力。

交互层细节已集中在 [`INTERACTION_CATALOG.md`](INTERACTION_CATALOG.md)，本文只摘出与 Seedance 视频工作流直接相关的部分。

## 2. LibTV 当前已经有什么

### 2.1 五条能力链

| LibTV 能力 | 当前可见形态 | 当前证据边界 |
|---|---|---|
| Seedance 2.5 生成 | 视频节点下方生成面板：模型、模式、比例、清晰度、时长、音频、数量、积分和提交 | 登录原站菜单/参数复核 + clone 截图；没有真实 provider 任务 |
| 片段重拍 | 就绪视频工具栏进入；4 秒时间段选择；最多 5 个片段；范围 token 投影到 Prompt | 文章截图、线上 bundle 文案和 clone 前端闭环；未提交真实重拍 |
| Auto Link | 画布素材作为候选；参考缩略条；Prompt 中的图片编号；用户接受后才写入 | 原站当前视频面板开关/引用 token + clone 可审核原型 |
| 超长视频 Beta | `30-300s`，`300s / 14700`；提交后转到画布过程图，可查看中间节点 | 原站当前菜单/参数实测 + clone 12 节点/22 边 pending 过程图 |
| 逐帧拉片 | 独立 `shot-breakdown` 节点；分镜/动态/音乐三个维度；结果是媒体卡组 | 原站空态节点和 bundle 事实 + 文章结果截图 + clone 结构化结果节点 |

这五条能力不是五个孤立的按钮：它们围绕“视频版本、时间区间、素材职责、生成任务、派生结果”组织。Open Canvas 的价值在于帮助我们把这组关系显式化，而不是替代 LibTV 的工具栏和参数面板。

### 2.2 当前 clone 的关键实现边界

- 视频生成面板属于选中视频节点的节点内编辑层，采用 `660px` 稳定屏幕宽度和节点锚定的 inverse zoom；参见 [`VideoGenerationPanel.spec.md`](../components/VideoGenerationPanel.spec.md#positioning)。
- 2026-08-26 的现场抽查进一步记录了图片节点在 `929x874`、约 `27.81%` zoom 下的上下浮层矩形、中心误差和边缘裁切；详见 [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#8-2026-08-26-浏览器现场几何抽查)。
- 长视频过程图是 clone-only 的本地 pending 过程表达，提交一次对应一个 graph transaction；其节点数、布局和状态不是 LibTV API 契约。
- 逐帧拉片和智能剪辑是不同节点类型，不能因为都处理视频就合并为同一个通用面板。
- 片段重拍、Auto Link、拉片和长视频均不触发真实模型、上传、计费或后台任务。
- 图编辑、节点历史、父子关系、导演捕获和视频派生属于当前项目已有领域逻辑；不能被 Open Canvas 的五类节点模型简单覆盖。

## 3. 对照结论

### 3.1 结论一：LibTV 的“画布”是对象上下文，Open Canvas 的“画布”是执行 graph

Open Canvas 的核心交互围绕可执行 graph 展开：输入节点通过边进入目标节点，目标节点从上游数据解析 text/image/video/audio buckets，随后构造 task descriptor。相关源码见 [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L191) 和 [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L449)。

LibTV 的当前画布同样用节点承载素材和操作，但近期重点能力需要更多领域语义：

```text
源视频版本
  -> 时间区间 / 片段重拍
  -> 替换片段任务
  -> 新视频版本

参考视频
  -> 拉片候选
  -> 关键帧 / 动态片段 / BGM
  -> 人工审核后成为可引用素材

源视频 + 结构化素材职责 + 长视频计划
  -> 多段任务
  -> 拼接过程
  -> 最终成片版本
```

**交叉判断：** Open Canvas 证明“节点图可以成为运行入口”，但不证明 LibTV 应把所有视频操作都变成自由连线。当前 clone 的长视频过程图可借鉴 graph 可追踪性，同时继续用现有 Scene/Segment/VideoTask/结果版本表达业务真相。

### 3.2 结论二：Open Canvas 的引用分桶适合启发 Auto Link，但不能代替 LibTV 的语义 token

Open Canvas 会按 incoming edge 的目标 Handle 把输入分成文字、普通图片、style reference、omni reference、视频和音频；图片/视频/音频 node data 也有独立字段。相关源码见 [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L191) 和 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L84)。

LibTV Auto Link 的关键不只是“附加 N 张图片”，还包括：

- 角色、场景、道具等候选的职责；
- Prompt 中引用 token 与素材顺序的同步；
- 用户接受、替换、移除的审核闭环；
- Seedance 对图片、视频、音频和首尾帧等输入模式的差异。

因此推荐用两层数据：

```text
内部语义层：assetId + role + confidence + source version
请求投影层：image 1 / video 1 / audio 1 + provider-specific options
```

Open Canvas 的 input bucket 是后一层之前的结构启发；它不能替换当前项目的 mention binding、职责标注和最终参数授权。

### 3.3 结论三：Open Canvas 的媒体历史可启发视频结果回选，但不能抹平 LibTV 的“候选/派生版本”差异

Open Canvas 的 video node data 包含 `video`、`videoHistory`、`selectedVideoIndex`、`inputMode`、`referenceMode`、`aspectRatio`、`resolution` 和 `duration`。规范化时会根据 selected index 选出当前媒体，节点预览也允许切换历史结果。见 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L98) 和 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L1528)。

这对 LibTV 有一个高价值问题：用户在一个视频节点看到多个候选时，当前选中候选是否是“同一节点的输出版本”，还是已经形成一个需要保留来源和任务关系的派生视频实体？这需要源站继续取证，不能通过 Open Canvas 字段名直接决定。

当前研究应保持两个可能模型：

| 模型 | 适用场景 | 需要确认 |
|---|---|---|
| 节点内候选历史 | 同一生成请求的多个 output，切换只改变当前预览/引用 | 下游边是否跟随 selected index |
| 派生视频版本 | 重拍、续写、拼接和编辑，结果来自不同任务或时间区间 | 源版本、任务、时间范围、替换关系是否可回溯 |

Open Canvas 的 history/index 更适合第一种；LibTV 的片段重拍和超长视频必须保留第二种关系。

### 3.4 结论四：Open Canvas 的状态分离适合长视频过程图和拉片结果的反馈

Open Canvas 将 node status/run status 与 canvas save status 分开：任务可以 `queued/running/success/error`，画布可以 `dirty/saving/saved/error/conflict`。见 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L11) 和 [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38)。

对 LibTV 五条能力链，至少应区分：

```text
用户编辑状态：已选择、已修改、等待确认
任务状态：未提交、排队、运行中、成功、失败
媒体处理状态：抽帧中、裁剪中、拼接中、结果待审核
版本状态：当前、候选、派生、已替换、已废弃
```

当前前端 prototype 可以把这些状态做成本地可见 mock，但不能因显示“处理中”就暗示真的调用了 Seedance 或完成了后端持久化。尤其是长视频的 `pending` 过程节点必须保持“待生成/待确认”文案。

## 4. 五项能力的逐项交叉表

### 4.1 Seedance 2.5 生成面板

**LibTV 源站事实/当前复刻：**

- 模型菜单显示 Seedance 2.5 及“30s 音画同步”能力描述；
- 普通模式支持 `4-30s`，超长模式切换到 `30-300s`；
- 生成参数和预计积分靠近提交按钮；
- 选中视频后上下文面板保持节点锚定，而不是浏览器固定面板。

**Open Canvas 启发：**

- video node data 把 model、scene、duration、ratio、resolution 和 input history 分开保存；
- 执行 descriptor 只在提交时决定 provider-specific key，避免把 UI label 直接当 API 合同；
- `isModelSelectableForNode` 根据输入引用和 supported scenes 过滤模型，说明“参数显示”可以由能力矩阵驱动。

**当前决策：** 保留 LibTV 的 `VideoGenerationPanel` 视觉与节点内定位。可以参考能力矩阵和最终 descriptor snapshot 的概念，但不能把 Open Canvas 的 model slug、provider 或场景命名引入 LibTV。

**后续验证：** 模式切换时哪些字段隐藏/禁用、300 秒对应的任务确认、音频状态、模型能力变化是否影响面板高度和上下浮层几何。

### 4.2 片段重拍

**LibTV 源站事实/当前复刻：**

- 4 秒选择粒度和最多 5 个片段来自文章截图/线上文案及本地复刻合同；
- Prompt 会带视频编号和时间范围；
- 片段重拍是就绪视频的上下文工具，而不是普通空视频节点的默认模式。

**Open Canvas 启发：**

- video history/index 提醒保存 source output 与 selected output 的关系；
- node/run status 分离提醒“片段已选”“任务已提交”“替换已完成”不能共用一个布尔值；
- copy/graph mutation 的版本化思路适合记录一次局部替换的 source graph snapshot。

**当前决策：** 第一阶段只保留一个明确连续区间或当前已有前端选择闭环；真实重拍实现前必须定义视频版本、区间、任务和替换结果关系，不在原 URL 上原地覆盖。

**后续验证：** 多区间是否允许重叠、未选区间如何保证不变、音频如何处理、重拍后旧结果是否仍可回选、工具栏和下方面板如何在结果版本切换时更新。

### 4.3 Auto Link

**LibTV 源站事实/当前复刻：**

- 候选作用域是当前画布可见的素材；
- Prompt 中的编号与底部参考缩略条同步；
- 用户可以检查并接受，不准确时替换，不应直接覆盖原 Prompt。

**Open Canvas 启发：**

- incoming edges 具有明确类型和目标 Handle；
- reference card 可以区分媒体类型、标题、职责和预览；
- media inputs 在执行前才投影成 descriptor options。

**当前决策：** 把 Auto Link 继续放在现有 mention binding 之前，输出“推荐绑定”而不是自动提交。内部保存稳定 asset ID/职责，最终请求再生成连续编号。

**后续验证：** 推荐绑定是否会改变节点边、是否需要在画布上插入显式边、手动替换后编号如何重排、低置信匹配如何展示、跨项目权限如何阻断。

### 4.4 超长视频

**LibTV 源站事实/当前复刻：**

- 当前原站显示超长视频 Beta、`300s` 和采样积分 `14700`；
- 生成过程以画布过程图展示中间素材、镜头、候选、汇聚和最终成片；
- 当前 clone 将一次提交建模为一次 graph transaction，并保留 source selection。

**Open Canvas 启发：**

- graph 是可序列化 DAG，节点/边/viewport 和 node data 共同形成可回放文档；
- Quick Add/pending connection 展示了“创建节点后再建立语义连接”的状态链；
- save/run 状态分离适合过程图的局部重试和保存反馈；
- clipboard/ID map 提醒复制过程图时必须重写所有内部引用，不保留旧节点 ID。

**当前决策：** 过程图可以继续作为 clone-only 的可视化验证台，但必须明确是本地 pending graph，不宣称完成 300 秒生成。业务真相继续由现有长视频 process metadata 和节点数据承载，不把 Open Canvas 五类 node 当成 LibTV 的领域模型。

**后续验证：** 原站中间镜头是可编辑节点还是只读过程；单个镜头修改是否重新生成整个成片；长视频过程是否允许断点恢复、候选回选和局部拼接；一次确认实际触发多少 create。

### 4.5 逐帧拉片

**LibTV 源站事实/当前复刻：**

- “逐帧拉片”是独立节点类型，不是普通视频节点的一个 tab；
- 输入可来自上传或画布视频；
- 分镜、动态、音乐是三种维度；结果是关键帧、动作片段和音频卡片。

**Open Canvas 启发与缺口：**

- Open Canvas 的五类节点和媒体 history 能启发“分析结果应成为结构化媒体 data”；
- 它的 execution descriptor 能启发结果保存 source media、input role 和 run record；
- 固定版本没有证据证明存在 LibTV 同款 shot breakdown、镜头切分或 BGM 拆解节点。

**当前决策：** 保留专用 `shot-breakdown` / `shot-breakdown-result` 节点。分析结果先是候选派生产物，用户审核后才转正式素材或分镜；不把 Open Canvas 的 video node 误当作拉片实现。

**后续验证：** 原站结果卡是否能单独删除/替换/引用，拉片分析是否有版本，源视频替换后候选是否失效，分镜结果是否自动创建正式业务实体。

## 5. 高价值启发排序

| 优先级 | 启发 | 对 LibTV 的直接收益 | 当前动作 |
|---:|---|---|---|
| P0 | 统一“事件→坐标→状态→graph/data mutation→反馈”链 | 诊断双浮层、长视频过程图和节点创建时的状态分叉 | 继续源站取证，保持不编码 |
| P1 | 输入引用按职责/类型分桶，最终再投影 provider 参数 | 让 Auto Link、首尾帧、视频/音频参考可解释 | 对照现有 mention binding 和 VideoGenerationPanel |
| P1 | 媒体 history + selected index 与派生版本分开 | 避免候选轮播和片段重拍/拼接版本混成一件事 | 建立源站结果态证据 |
| P1 | run/save/media-processing 状态分离 | 长视频和拉片的过程反馈不再只有一个 loading | 保持本地 mock，先写状态合同 |
| P2 | pending connection/Quick Add | 适合研究关系型过程图的连接入口 | 仅在 LibTV 源站证明同类入口后实施 |
| P2 | versioned subgraph clipboard | 适合复制过程图或素材集合 | 先比对当前 canvasStore 的父子/派生逻辑 |
| P3 | Open Canvas provider registry/BYOK | 对当前 LibTV UI/UX 复刻帮助很小，风险高 | 不引入 |

## 6. 未来 batch 合同

### `LIBTV-SEEDANCE-OC-01`：视频输出候选与版本身份

**问题：** 当前视频节点的多个 output、重拍结果、续写结果和长视频最终成片分别是什么身份？

**最小证据：** 原站可用视频节点；切换多个候选；执行/重拍/续写入口；记录 node rect、工具栏、下方面板、当前输出、边和可回选状态。

**交付：** `SOURCE_FACT`、输出/版本关系图、选中 index 与下游引用矩阵。

**停止条件：** 没有真实源站结果态时，不把 `videoHistory` 或 clone process node 升级为 LibTV 数据契约。

### `LIBTV-SEEDANCE-OC-02`：Auto Link 引用职责与投影

**问题：** Auto Link 推荐是否形成显式边，还是仅形成本次请求的引用列表？

**最小证据：** 3 个以上画布候选；自动匹配；接受/替换/移除；Prompt token、缩略条、节点边和提交摘要前后快照。

**交付：** asset ID/职责/编号三层映射表和低置信失败态。

**停止条件：** 未确认权限和替换规则前，不扩大候选搜索范围，不将所有画布素材自动发送到 provider。

### `LIBTV-SEEDANCE-OC-03`：长视频过程图的局部修改

**问题：** 原站过程图中的中间节点是否可单独编辑并更新最终成片？

**最小证据：** 当前原站的 300 秒过程入口；每个阶段的选择态、修改入口、确认步骤、任务数量和结果版本。

**交付：** 有向关系/状态矩阵、一次确认的 create 次数、局部重算边界。

**停止条件：** 不能从 `300s / 14700` 推导后台拆分算法或自动重试策略。

### `LIBTV-SEEDANCE-OC-04`：逐帧拉片候选生命周期

**问题：** 分镜/动态/音乐结果是一次性展示、可复用素材，还是正式业务实体？

**最小证据：** 真实或已有结果态；分别预览、删除、替换、加入生成引用、保存后重新打开。

**交付：** candidate → accepted asset/storyboard 的状态图和源视频版本关系。

**停止条件：** 文章截图只能支持结果形态，不能单独支持持久化和自动建实体。

## 7. 对当前 clone 的约束

1. `VideoGenerationPanel` 继续遵守 LibTV 节点内 `660px`、inverse zoom 和 source-calibrated 上下浮层合同。
2. `ShotBreakdownNode`、`VideoClipNode`、`LongVideoProcessNode` 保持专用节点边界，不因 Open Canvas 五类 node 简化类型。
3. 长视频过程图、拉片结果、片段重拍和 Auto Link 的本地状态必须标明 clone/mock，不伪装真实任务或媒体。
4. Open Canvas 的 `Panel`、Handle、edge hit path、clipboard 和 provider 机制只能作为研究启发；LibTV 源站事实优先。
5. 不将 Open Canvas 的 graph store 合并进 `canvasStore`，更不能影响独立的 `frameosStore`。
6. 不修改当前已取证的 edge flow effect、连接方向、边缘裁剪策略和移动端退化规则，除非有新的 LibTV 源站证据。

## 8. 交叉研究结论

当前最有价值的结论不是“Open Canvas 也有视频节点”，而是：

```text
LibTV 的产品能力：视频创作工作流和媒体语义
Open Canvas 的工程启发：显式 graph/data/status/coordinate contracts
当前 clone 的实施边界：保留 LibTV UI/UX 真相，只吸收可测试的结构方法
```

因此，后续工作顺序应是：先解决 LibTV 源站双浮层和视频面板的几何/生命周期，再验证输出版本和 Auto Link，再研究长视频过程图与拉片候选的可审计关系。只有当源站证据说明某个交互确实存在，Open Canvas 的同类机制才可以进入 clone-only 设计；在此之前，它只是帮助我们提出更准确问题的研究对象。
