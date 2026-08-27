# Open Canvas 源码考古报告

## 1. 研究边界

本报告分析的是 git submodule `research/upstream/open-canvas` 在提交
`cf3a906bb8c35bb940d3267497e7f394b8f42582` 的源码，而不是当前工作区对它的猜测性改写。
该提交时间为 2026-07-01，提交说明为 `Make README default to Chinese`。上游仓库的版本号仍为
`0.1.0`、状态为 alpha；因此这里的结论是“固定版本的可复核事实”，不能自动等同于官网未来版本。

证据分级：

- **源码事实**：能直接由固定 submodule 中的代码或配置得到。
- **运行事实**：在 2026-08-26 通过官网页面 DOM 和截图观察到。
- **推断/建议**：依据事实对当前 LibTV/FrameOS 克隆项目作出的判断，必须在实施前重新验证。

## 2. 产品与技术边界

### 2.1 产品定位

上游 README 把 Open Canvas 定义为从 Cyberbara 内部 canvas 方向抽出的 local-first 工作流画布。核心承诺不是“复制一个托管平台”，而是：

1. 用户自带 API Key（BYOK）；
2. 画布和运行记录能在本地工作；
3. 图中不同节点可以组织文本、图片、视频和音频工作流；
4. 通过 JSON 导入/导出和可替换的存储/provider 层保持可 fork 性。

源码中的依赖组合为 Next.js 15.5.7、React 19.2.1、`@xyflow/react` 12.10.2、Zustand 5、Tailwind 4、Zod 4、next-intl，以及 OpenNext Cloudflare 适配器。上游 `package.json` 的脚本只有开发、构建、启动、lint 和 Cloudflare 构建/预览/部署，没有测试脚本。

参考：[`package.json`](../../../research/upstream/open-canvas/package.json#L1)、[`README.md`](../../../research/upstream/open-canvas/README.md#L8)。

### 2.2 当前实际入口

有效路由链是：

```mermaid
flowchart LR
  Home[app/[locale]/page.tsx] --> Landing[components/landing-page.tsx]
  ListRoute[app/[locale]/canvas/page.tsx] --> List[components/canvas-list-page.tsx]
  ListRoute --> DB1[listLocalCanvasDocuments]
  StudioRoute[app/[locale]/canvas/[canvasId]/page.tsx] --> Shell[components/open-canvas-shell.tsx]
  StudioRoute --> DB2[findLocalCanvasDocumentById]
  Shell --> Studio[CanvasStudioShell]
  Studio --> Store[shared/stores/canvas-store.ts]
  Studio --> Flow[@xyflow/react]
  Store --> Graph[serialized graph v1]
  Graph --> DB[local-canvas-store]
  Graph --> Execute[local-canvas-runner]
  Execute --> Provider[Cyberbara API in current route]
```

源码事实：

- 首页只渲染 `LandingPage`：[`app/[locale]/page.tsx`](../../../research/upstream/open-canvas/app/[locale]/page.tsx#L1)。
- 画布列表页服务端读取本地画布：[`app/[locale]/canvas/page.tsx`](../../../research/upstream/open-canvas/app/[locale]/canvas/page.tsx#L1)。
- 具体画布页按 ID 读取记录，然后渲染 `OpenCanvasShell`：[`app/[locale]/canvas/[canvasId]/page.tsx`](../../../research/upstream/open-canvas/app/[locale]/canvas/[canvasId]/page.tsx#L1)。
- `OpenCanvasShell` 负责 studio 外层的 JSON 导入/导出菜单，真正的画布交互由 `CanvasStudioShell` 负责：[`components/open-canvas-shell.tsx`](../../../research/upstream/open-canvas/components/open-canvas-shell.tsx#L21)。
- `components/canvas-app.tsx` 是体量较大的旧实现，但当前三条页面入口没有引用它。研究时不要把 legacy 代码当成运行时契约。

这一区分对克隆项目很重要：读到一个组件并不代表用户当前会走到该组件，必须先从 App Router 入口反向确认调用链。

## 3. 图模型：节点是可持久化的执行单元

### 3.1 节点类型与运行状态

固定版本的节点类型只有五种：`text`、`note`、`image`、`video`、`audio`。节点状态为 `idle`、`queued`、`running`、`success`、`error`；运行记录状态另有 `pending`、`running`、`success`、`failed`、`canceled`。

每个节点的公共数据包含：

- 标题、副标题和节点类型；
- prompt 与 public model 字符串；
- 状态、错误信息、最近运行 ID、完成时间、最近场景、credits 成本；
- 类型专属输入/输出数据。

类型专属字段如下：

| 节点 | 主要字段 | 交互含义 |
|---|---|---|
| Text | `plainText` | 文本上下文或文本生成结果 |
| Note | `noteHtml` | 仅作画布内富文本备注，不执行 |
| Image | `image`、`imageOutputs`、选中索引、输入模式、场景、比例、分辨率、引用权重 | 生成/上传图片，可保留多个输出 |
| Video | `video`、`videoHistory`、选中索引、输入模式、引用模式、比例、分辨率、时长 | 生成/上传视频，可回看历史输出 |
| Audio | `audio`、输入模式、循环、节拍、调性 | 音频上传/生成模型参数 |

媒体不是裸 URL，而是带 `source`（`generated`/`uploaded`）、可选 `assetId`、mime、缩略图、时长和尺寸的结构。这使画布可以区分“作品输出”和“用户上传的输入”，也允许 UI 做历史列表、缩略图和后续资源管理。

参考：[`shared/lib/canvas/types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L11)、[`shared/lib/canvas/types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L50)、[`shared/lib/canvas/types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L226)。

### 3.2 默认值与归一化

默认模型是：Text `gemini-3-flash`、Image `nano-banana-pro`、Video `seedance-2-fast-stable`、Audio `suno-sound-v5`。图片默认 1:1、1K、生成模式；视频默认 16:9、720p、5 秒、生成模式和自动引用模式。

所有从 JSON、服务端或 UI 进入的节点数据都经过 `normalizeCanvasNodeData` 一类的归一化函数。其价值不只是防御脏数据，还包括：

- 输出历史按 `assetId` 或 URL 去重；
- 选中媒体索引被限制在合法范围；
- 不认可的状态、字段和参数回到默认值；
- 模板快照可清除运行时状态；
- 节点标题、场景和模型在修改后维持类型合同。

因此，克隆项目若只在 React 组件中维护临时字段，会很快在刷新、导入、复制和运行回写时产生分叉。应把“作者输入”和“运行时结果”视为同一图模型中的两个明确层次。

### 3.3 序列化合同

持久化图为 version 1：

```text
SerializedCanvasGraph {
  version: 1
  viewport: { x, y, zoom }
  nodes: [{ id, type, position, width?, height?, data? }]
  edges: [{ id, source, target, sourceHandle?, targetHandle?, type?, data? }]
}
```

React Flow 的运行时字段不会原样写入数据库；`buildCanvasGraphFromFlow` 只保留位置、尺寸、类型、归一化 data、边的端点/handles/type/data。新节点 ID 由类型、时间戳和随机短串组成。边默认是 source=`right`、target=`left`；若导入图的 handle 方向表现为反向，序列化/解析阶段会将 source/target 与 handle 一起交换。

参考：[`shared/lib/canvas/serialization.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts#L20)、[`shared/lib/canvas/serialization.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts#L43)、[`shared/lib/canvas/serialization.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts#L124)。

## 4. 图校验与连接合同

### 4.1 服务端图校验

图校验不是仅靠 React Flow 的前端行为。固定版本的服务端/共享 validator：

- 节点上限 200，边上限 400；
- 检查节点/边对象、ID、类型、位置、尺寸、data 类型；
- 检查重复节点 ID、重复边 ID、边是否引用不存在的节点；
- 禁止自边；
- 用 DFS 检测已有环；
- 新连接用从 target 反向追踪的方式判断是否会形成环；
- 将缺失 handle 归一化为右侧输出和左侧输入。

这意味着 Open Canvas 把画布定义为 DAG，而不是允许任意自由连线的白板。DAG 合同为执行顺序、上游输出解析和冲突恢复提供了基础。

参考：[`shared/lib/canvas/validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L8)、[`shared/lib/canvas/validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L239)、[`shared/lib/canvas/validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L319)、[`shared/lib/canvas/validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L418)。

### 4.2 节点兼容性与特殊引用

studio 层进一步限制语义连接：

- Note 不能作为可执行连接参与者；
- Audio source 只允许指向 Video；
- Video source 只允许指向 Video；
- Audio target 只接受 Text；
- 默认情况下，其余类型按通用输入处理；
- Image 的 `style-reference` 和 `omni-reference` 是独立 handle，不应与普通 image 输入混淆。

执行解析器会把进入目标节点的边分桶为 `textInputs`、`imageInputs`、`styleReferenceInputs`、`omniReferenceInputs`、`videoInputs`、`audioInputs`。这比“所有边都转成一个数组”更接近 AI 工作流的真实合同：同一张图作为普通内容参考和作为风格参考，其下游请求字段、权重和模型能力可能不同。

参考：[`shared/lib/canvas/execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L26)、[`shared/lib/canvas/execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L105)。UI 中真实的连接锚点是 `@xyflow/react` 的 `<Handle>`，不是覆盖在节点上的装饰层；这一点也符合当前项目的 React Flow 红线。

## 5. 执行模型：先构造 descriptor，再交给 provider

### 5.1 场景推断

`inferCanvasExecutionScene` 把图结构和节点类型翻译为可执行场景：

| 节点 | 推断规则 |
|---|---|
| Text | 有 image 输入则 `image-to-text`，否则 `text-to-text` |
| Image | 手动场景优先；存在图像输入则 `image-to-image`，否则 `text-to-image` |
| Video | 有视频输入为 `video-to-video`；有图片输入为 `image-to-video`；否则 `text-to-video` |
| Audio | `text-to-audio` |
| Note | 不可执行 |

在构造 descriptor 前，执行层会拒绝不支持的组合，例如 Text/Image 不接受 video/audio，Audio 只接受文本上下文且不接受媒体，Note 不可执行。prompt 由当前节点请求和上游 Text 内容组合而成，并把输入媒体以结构化描述传给 provider。

参考：[`shared/lib/canvas/execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L119)、[`shared/lib/canvas/execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L134)。

### 5.2 模型选项不是一套通用表单

public model registry 将用户可见模型名映射为 provider 和内部 model；当前注册表包含 Kie、PiAPI、Ark、Dashscope、Fal 等内部 provider 路由，也包含图片、视频、音频、Gemini Omni、Seedance 多个变体。`model-options.ts` 再按模型和 scene 提供比例、分辨率、时长及是否需要发送某字段的规则。

执行 descriptor 的媒体 options 会按场景携带：

- 图像的比例、分辨率、图片输入；
- Midjourney 的特殊字段和引用权重；
- 音频循环、节拍、调性；
- 视频模型支持的比例、分辨率、时长；
- Seedance 的 `seedance_mode`/`ark_mode`；
- Gemini Omni 的 `video_input` 等特殊输入。

这是值得当前克隆项目借鉴的“模型能力矩阵”思路：UI 的字段可见性和请求构造应由模型能力合同驱动，不能只根据节点类型硬编码一套参数。

参考：[`shared/services/public-ai-models.ts`](../../../research/upstream/open-canvas/shared/services/public-ai-models.ts#L1)、[`shared/services/public-ai-models.ts`](../../../research/upstream/open-canvas/shared/services/public-ai-models.ts#L527)、[`shared/lib/canvas/model-options.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/model-options.ts#L45)。

## 6. 状态、保存和并发

### 6.1 Zustand store 的职责

`canvas-store.ts` 管理 canvasId、nodes、edges、viewport、revision、savedGraphString、hydration 状态、dirty 状态、保存状态、错误和冲突标记。动作覆盖：

- hydrate 初始服务端记录；
- add/duplicate/delete node；
- copy/paste 节点和内部边；
- delete edge、删除选中项和单条上游引用；
- React Flow node/edge changes；
- connect 前的重复边、上限、handle 和 cycle 检查；
- updateNodeData 后重新归一化；
- saving/saved/error/conflict 状态转移。

复制/粘贴会生成新的节点 ID，维护剪贴板内的旧 ID 到新 ID 映射，只恢复剪贴板内部边，并对位置做偏移；外部引用不会被伪造。这是一个很实用的工作流编辑语义。

参考：[`shared/stores/canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L80)、[`shared/stores/canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L221)、[`shared/stores/canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L283)、[`shared/stores/canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339)。

### 6.2 React Flow change routing

Open Canvas 与当前 clone 的 lockfile 都固定到 `@xyflow/react@12.11.1`，所以可以在同一 framework contract 上做机制比较。上游 store callback 使用 Zustand functional updater 读取 current nodes/edges，避免由旧 React render closure 生成 whole-array 覆盖；发生 conflict 时，persistent change 也会被 gate。

但固定实现的 `hasPersistentNodeChanges/hasPersistentEdgeChanges` 只区分 `select` 与 non-select，并把整个 union 交给 `applyNodeChanges/applyEdgeChanges`。在精确类型中，node 包含 `add/remove/replace`，edge 的 non-select variant 全是 `add/remove/replace`，reconnect 还是独立 callback。Generic reducer 能执行这些 delta，却不知道 graph identity、delete repair、connection policy 或 history command。

因此这是一个同时包含正例和反例的研究对象：借 current-store ownership 和 conflict gate；不要复制“所有 non-select 都是普通 persistent delta”。完整 reducer precedence、clone callback 风险和 T0/T1/T2/T3 转译见 [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)。

### 6.3 自动保存与版本冲突

studio 在图改变后约 1.2 秒自动保存。保存请求携带 revision；服务端只有 revision 未变化时才写入并加一。前端 `finishSave` 会再次比较当前图和刚保存的 graph string，避免“请求返回期间用户又编辑了内容”时错误地清除 dirty 状态。

发生版本冲突时，当前实现尝试以当前用户编辑为基础做 rebase；无法安全合并则进入显式 conflict 状态，要求加载最新版本。这个合同比简单的最后写入覆盖更适合画布，因为拖拽位置、节点 data 和运行时输出可能交错更新。

### 6.4 本地存储分层

`local-canvas-store.ts` 把数据库抽象成：

- Cloudflare 环境：按 `open_canvas_client_id` 读取/写入 KV，键为 `canvas-db:${clientId}`；
- 本地 Next.js：写入 `data/open-canvas-db.json`；
- 文件写入使用临时文件再 `rename`，降低半写文件风险；
- canvas 文档和 runs 在同一个 JSON 数据库中；
- 删除最后一张画布时自动创建一张空画布。

`updateDb` 本身是 read-modify-write。图保存会在当前读出的对象副本上做 application-level revision compare，但 storage 层没有 CAS；列表元数据、运行记录及节点 patch 也各自共享一次完整 DB 读写。由此可推断，在多实例或高并发 KV 场景下仍需要更强的原子更新/锁/队列策略；这是运营风险，不是当前源码已经声明的 bug。

参考：[`shared/models/local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L20)、[`shared/models/local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L77)、[`shared/models/local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L160)、[`shared/models/local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L302)。

### 6.5 Run polling 与结果回写 authority

current studio 在执行前调用 `saveGraphNow`，把返回 revision 交给 execute route；runner 在 durable graph 上构造 descriptor，创建独立 run，并把非 terminal run ID 交回 client。Client 以 run ID 管理 polling timer，且可在 hydrate 后从 node 的 `queued/running + lastRunId` 恢复轮询。Terminal node patch 会在 server 增加 canvas revision，client 的 `applyServerNodePatch` 同时 patch live node 和 `savedGraphString` baseline。这是比 component-local spinner 更完整的控制面分层。

但 fixed implementation 尚未把它收口成 stale-safe transaction：

- execute 的 revision compare、run creation 和 current-node owner claim 不是同一原子写；
- `applyLocalCanvasNodePatch` 只验证 canvas/node 存在，不比较 expected revision、expected `lastRunId` 或 source version；
- client `applyServerNodePatch` 也不检查 patch 是否仍来自 current run，且 `plainText` 一类字段可能同时承担 user draft 和 generated output；
- run terminal update 与 node patch 是两个独立 `updateDb`；中间失败需要 recoverable projection，但当前没有 projection state；
- runner 在创建 `running` run 后才进入 audio unsupported/provider 调用，异常路径没有统一 terminal cleanup；
- failed/canceled polling 在应用 server patch 后又走本地 `updateNodeData`，会混合 server result 与 local dirty authority。

因此 Open Canvas 可以证明 descriptor/run/poll/server-patch/revision 应分层，不能证明“有 revision 就不会有 stale result”。完整正反面审计与 LibTV 转译见 [`../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。

参考：[`shared/services/canvas/local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L90)、[`shared/models/local-canvas-store.ts`](../../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L337)、[`shared/stores/canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L836)、[`shared/blocks/canvas/canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5187)。

### 6.6 Canvas registry、hydrate 与跨 route owner

Open Canvas 将列表摘要和可编辑 document 分开。`/canvas` 读取按更新时间排序的 summary；`/canvas/[canvasId]` 按稳定 ID 读取 full record，missing ID 直接 not-found。Create 返回新空 document 后导航到其 URL；rename 在 API 边界要求 trimmed non-empty title；delete 清 document 和同 canvas runs，最后一张删除后自动创建空 document。Studio 不在同一 React Flow 内切换另一张 canvas，而是返回列表再进入 URL。

进入 studio 时，`hydrate` 一次替换 canvasId、nodes/edges、viewport、revision、saved baseline、dirty/save/error/conflict；hydration effect 再应用 title 和 React Flow viewport。这是比依次 setNodes/setEdges/setViewport 更清晰的 active-document owner boundary。

固定实现仍有跨 route async 限制。Save request URL 使用 `initialCanvas.id`，所以 durable target 明确；但 response 后调用 global store 的 `finishSave/failSave/enterConflict` 时不携带 expected canvas ID。旧 route promise 可在新 canvas hydrate 后 settle，并更新当前 in-memory revision/save baseline/status。该结论是静态竞态推断，不是 live incident；完整正反面转译见 [`../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。

### 6.7 Command outcome 与 feedback surface

固定版本不是只用 toast。它同时存在四类 presentation owner：

1. root layout 的全局 Sonner `Toaster`，由 studio/list/settings/media/shell 直接发 success/error；
2. node data 的 queued/running/success/error、errorMessage、lastRunId，投影到 card/MiniMap/editor；
3. canvas save/dirty/error/conflict 的持续 header status 与 conflict banner/action；
4. provider settings 的 field error map、saving control 和 summary toast。

CRUD 还证明 outcome-sensitive policy：create success 用 navigation/新 document 体现，rename 同名与用户 cancel silent，delete 先 confirm，rename/delete/import 的完成/失败再 toast。可借的是 transient、persistent、field 和 control projection 分层，不是“每个 handler 调 toast”。

固定实现也有明确反例：store result code 主要只有 `invalid_graph/graph_cycle_detected`，具体 identity 放在中文 message；`translateCanvasRuntimeMessage` 再匹配整段中文/标点做 i18n。Global toast call 也没有显式 canvasId、operationId、attempt 或 dedupe key，因此 old-canvas async terminal 可能在新 owner 上下文发出无归属 announcement。完整转译见 [`../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)。

### 6.8 Selection、focus 与 command context

固定 studio 将 node/edge `selected` 留在 React Flow records：selected-node editor 只要求恰好一个 selected node，selected count 同时统计 node/edge，clipboard 从 selected nodes 构造 internal-edge subgraph，delete selection 则删除 selected node/edge 与 incident edge。这个结构让 command closure 直接，但 selection、primary editor 和 portable graph shape 没有天然分层。

`onNodesChange/onEdgesChange` 在 conflict 下整体 return，因此 React Flow `select` change 也与 persistent mutation 一起被冻结；这是不能直接移植到 LibTV 的 authority coupling。文档级 copy/paste 另有更好的局部边界：`isEditableTarget` 覆盖 input/textarea/select/contenteditable/role textbox，image preview active 时暂停 graph clipboard；title/note/text editor 则各自拥有 focus 与 Enter/Escape commit/cancel。

fixed implementation 没有一个 app-level undo/tool/group/duplicate shortcut dispatcher。Quick Add Escape 是不阻止传播的 document bubble listener，部分 destructive key 仍依赖 React Flow/default focus；Dialog/Dropdown 又主要委托 Radix primitive。它提供的是 local ownership 与 framework delegation 的正反面对照，不是 LibTV shortcut/focus 规格。完整双向审计见 [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)；转译后的 validated selection、context precedence、single-layer Escape 和 focus-return 设计见 [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。

## 7. Provider 事实与关键缺口

### 7.1 声明层和旧 API 层

README 声称：Text 可走 Cyberbara/OpenRouter，Image/Video 可走 Cyberbara/Replicate，上传可走 Cyberbara/S3-compatible。legacy `app/api/execute/route.ts` 确实存在这三类分支：

- Text：Cyberbara 或 OpenRouter；
- Image/Video：Cyberbara 或 Replicate；
- 轮询：Replicate prediction 或 Cyberbara task。

### 7.2 当前运行入口的实际行为

当前 `CanvasStudioShell` 调用的是 `/api/canvas/[canvasId]/nodes/[nodeId]/execute`，该路由进入 `executeLocalCanvasNode`。在固定提交中：

- `getProviderMessage` 要求 `cyberbaraApiKey`；
- run 记录写死 `provider: 'cyberbara'`；
- Text 调用 `runCyberbaraText`；
- 图片/视频调用 `createCyberbaraGeneration`；
- 轮询调用 Cyberbara task 查询；
- Audio 直接抛出 `Audio generation is not wired into the local OSS shell yet.`；
- runner 没有根据 descriptor.provider 分派到 OpenRouter、Replicate 或 registry 中的 Kie/PiAPI/Ark/Dashscope/Fal。

这产生一个高优先级、可复核的“声明与运行不一致”：模型注册表和 UI 已能展示更丰富的 provider/model 能力，但真实 studio 执行路径并未接通它们。旧 `/api/execute` 的能力不能抵消这一点，因为页面当前没有走旧组件和旧 endpoint。

参考：[`shared/services/canvas/local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L30)、[`shared/services/canvas/local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L90)、[`shared/services/canvas/local-canvas-runner.ts`](../../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L190)、[`app/api/execute/route.ts`](../../../research/upstream/open-canvas/app/api/execute/route.ts#L1)。

对当前项目的意义是：若借鉴 Open Canvas 的节点和面板外形，应先确认当前 clone 的“视觉实现”与“可执行合同”是否需要同步；不能因为下拉框里出现模型名称就把它记录为已支持。

## 8.1 API surface 速查

| 路径 | 方法 | 主要职责 | 研究备注 |
|---|---|---|---|
| `/api/canvas` | GET/POST | 列表、创建画布 | local client namespace |
| `/api/canvas/[canvasId]` | GET/PATCH/DELETE | 读取、重命名、删除画布 | 删除最后一张会补空画布 |
| `/api/canvas/[canvasId]/graph` | PUT | 带 revision 保存 graph | validator + conflict response |
| `/api/canvas/[canvasId]/nodes/[nodeId]/execute` | POST | current studio 执行入口 | 进入 local runner |
| `/api/canvas/[canvasId]/runs/[runId]` | GET | 查询异步 run | current runner 轮询 provider |
| `/api/canvas/[canvasId]/template` | POST | 模板相关写入入口 | 与 README known limits 存在漂移，待运行态复核 |
| `/api/canvas/uploads/images`、`videos` | POST | canvas 资源上传 | 与 storage provider 相关 |
| `/api/uploads/images`、`videos` | POST | 通用上传入口 | 与上面存在并行 API surface |
| `/api/storage/upload-audio` | POST | 音频上传入口 | 不等同于音频生成 |
| `/api/provider-settings` | GET/POST | 读取/写入 provider settings | 当前使用 cookie |
| `/api/media/proxy` | GET | 媒体代理 | 需要单独核对跨域/安全边界 |
| `/api/execute` | POST | legacy provider execution | 不应当作 current studio route |

入口源码可从 [`app/api/canvas/route.ts`](../../../research/upstream/open-canvas/app/api/canvas/route.ts) 及其同级路由复核；其中 current canvas path 与 legacy endpoint 的分离是本研究识别 provider 漂移的关键。

## 8. Provider 设置与身份边界

设置表单包含 OpenRouter API Key/Base URL、Replicate Token、Cyberbara Key/Base URL 和 S3-compatible 配置。Zod 会校验 URL、Cyberbara 存储必需的 key、S3 endpoint/access/secret/bucket。

当前实现把完整归一化设置 JSON 编码进 `open_canvas_provider_settings` cookie，cookie 设置为 `httpOnly: false`、`sameSite: lax`、`secure: false`、30 天。这是 local-first alpha 的便利方案，但生产部署应视为硬化项：浏览器脚本可读取 API key，且非 HTTPS 环境也可能携带该 cookie。报告只记录风险，不在研究轮次修改上游或本仓库业务代码。

另一个身份事实是：`open_canvas_client_id` 是随机 UUID 的本地命名空间 cookie，不是登录认证。KV 的画布数据按此 ID 隔离；持有同一 cookie 的请求即可进入同一命名空间。对单机个人工具合理，对公开托管应用则需要鉴权、访问控制和密钥托管。

参考：[`lib/provider-settings-cookie.ts`](../../../research/upstream/open-canvas/lib/provider-settings-cookie.ts#L19)、[`lib/provider-settings-cookie.ts`](../../../research/upstream/open-canvas/lib/provider-settings-cookie.ts#L42)、[`middleware.ts`](../../../research/upstream/open-canvas/middleware.ts#L13)。

## 9. UI 结构的源码线索

`CanvasStudioShell` 是一个约 7600 行的综合组件，承担画布编辑、节点渲染、连接边、选中态面板、设置/模板/预览/编辑器对话框、拖放上传、快捷复制粘贴、自动保存和执行轮询。它的主要可观察结构包括：

- `BaseCanvasNode`：按节点类型设定不同卡片宽度，渲染标题、状态、文本/富文本、媒体预览和输出历史；
- `<Handle>`：左右输入输出以及 Image 的 style/omni 特殊输入；
- `CanvasConnectionEdge`：Bezier 边、选中/hover 样式、边上的操作入口；
- `CanvasStudioInner`：把 React Flow、Zustand、选中节点 descriptor 和各种面板状态编排在一起；
- React Flow `Panel`：顶部工具区、选中节点控制区、缩略图/视图等固定浮层；
- 选中节点面板：generate/upload 两种模式，prompt、model、引用、图片/视频/音频专属设置和执行按钮。

源码搜索结果显示 `<Panel>` 在 studio 主 JSX 的 6259、6331、6399、6439 行附近，`<Handle>` 在 `BaseCanvasNode` 的 3235、3256、3266 行附近。要研究“点击节点后上下浮层的锚定关系”，应继续使用运行截图和 DOM 几何核验，不能仅凭这个大组件的代码顺序推测视觉位置。

## 10. 维护性判断

### 10.1 可借鉴

1. 以版本化 graph 作为单一持久化合同；
2. 把输入解析、场景推断、模型能力选项和 provider 路由拆成纯逻辑层；
3. 把输出历史与当前选中输出一起建模；
4. 在连接和服务端导入两侧都执行 DAG/数量/引用校验；
5. copy/paste 只恢复内部边，避免隐式连错外部节点；
6. 自动保存必须保留 dirty、saving、saved、conflict，而不是只有一个 loading flag。

### 10.2 需要警惕

1. `canvas-studio-shell.tsx` 过于集中，视觉修复容易误伤执行/保存逻辑；
2. legacy `CanvasApp` 与当前 `CanvasStudioShell` 并存，文档、模型注册表和真实运行路径已出现漂移；
3. 公开 model registry 的 provider 路由比实际设置/runner 更宽；
4. Audio 已进入 graph/UI/data contract，但当前 OSS shell 的执行明确未接通；
5. provider keys 放在非 HttpOnly cookie，不适合作为生产级密钥方案；
6. 未发现单元、集成或 Playwright 测试目录/脚本，行为变更主要依赖手工检查。

以上各项是后续克隆实现的风险清单，不是本轮编码任务。完整优先级和实施门槛见 [`IMPLEMENTATION_IMPLICATIONS.md`](IMPLEMENTATION_IMPLICATIONS.md)。

## 11. 静态验证边界

本次源码分析没有安装上游依赖、没有启动上游 dev server、没有调用真实 provider，也没有执行 Cloudflare 部署。上游 `package.json` 只有 lint/build 等脚本，未发现 test/e2e/vitest/jest 脚本或测试目录。因此：

- 路由、类型、调用链、常量和分支结论可由固定源码复核；
- provider 是否能在当前公网配置下成功生成，不能由本轮静态研究确认；
- studio 的真实 DOM 几何必须通过浏览器运行态补证；
- 任何实施前的 live 结论都应在 `EVIDENCE_MATRIX.md` 新增或升级 claim。
