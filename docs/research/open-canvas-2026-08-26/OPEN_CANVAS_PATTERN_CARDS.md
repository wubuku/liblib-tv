# Open Canvas 可迁移模式卡

> 目的：把固定版本 `ZeroLu/open-canvas` 的源码启发压缩成后续 LibTV UI/UX 复刻可以直接引用的决策单元。
>
> 证据基线：submodule `research/upstream/open-canvas`，commit `cf3a906bb8c35bb940d3267497e7f394b8f42582`。下文的 `SOURCE_FACT` 只描述该固定版本源码或已经完成的 LibTV 现场记录；`INFERENCE` 是跨项目推断；`CLONE_DECISION` 是当前项目的研究决策，不是编码授权。

## 1. 使用方式

一张模式卡不是待办功能，也不是可以直接复制的组件。它回答四个问题：

1. 上游到底解决了什么一般性问题？
2. 这个问题是否已在 LibTV 被观察到，还是仅仅看起来相似？
3. 若确实相关，最小可迁移合同是什么？
4. 哪些上游细节必须明确拒绝，以免改变 LibTV 的源站行为？

后续实现 agent 只能把卡片中的“最小合同”转为设计或测试任务；必须先满足卡片的 LibTV 证据门槛，不能因为存在对应的 Open Canvas 源码就直接编码。

## 2. 卡片总览

| ID | Open Canvas 模式 | 解决的共同问题 | 对 LibTV 的价值 | 当前状态 |
|---|---|---|---|---|
| OC-PATTERN-01 | measured node + live viewport | 节点尺寸、视口和浮层位置分叉 | 直接对应图片节点上下双浮层错位 | P0，源站几何合同已较完整，待 clone 动态验证 |
| OC-PATTERN-02 | typed input buckets + provider projection | 图上的引用语义与执行请求耦合 | 直接对应 AutoLink 的稳定身份和 ordinal 投影 | P0，LibTV AutoLink 合同已落档，待授权实现 |
| OC-PATTERN-03 | node status / run status / save status 分离 | 异步任务、节点展示和保存反馈互相覆盖 | 适合 Seedance 长视频、重拍和过程节点 | P1，先建立状态证据，不引入真实 provider |
| OC-PATTERN-04 | serialized subgraph + ID map | 复制、派生和导入时保持图关系 | 适合复拍、版本链和过程图的可追溯性 | P1，先确认 LibTV 派生关系展示方式 |
| OC-PATTERN-05 | run-keyed polling + stale-safe result ingress | 晚到/重复/乱序结果覆盖当前编辑或错误落图 | 适合拉片、长视频、处理结果与 Director export | P1，控制面方法可借；fixed generic patch 作为反例 |

---

## 3. OC-PATTERN-01：Measured Node + Live Viewport

### 3.1 上游 `SOURCE_FACT`

固定版本的 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964) 对选中节点的编辑浮层单独计算 screen anchor：

- 节点宽高优先读取 `selectedNode.measured`，再回退到 `selectedNode.width/height` 和默认值；
- 节点 flow position 通过同一份 `liveViewport.x/y/zoom` 转成 screen position；
- 编辑器横向锚定节点中心，纵向锚定节点底部并增加固定 screen gap；
- 编辑器宽度根据画布容器宽度计算，并限制在 `360..820px`；
- 同一文件 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6015) 又为图片操作条计算节点顶部和中心；两种浮层虽然承载内容不同，却共享节点尺寸和视口语义。

这是一种“先求节点 screen rect，再求浮层 anchor”的结构。它不是一个通用的 CSS `top: -16px`。

### 3.2 LibTV 对应的 `SOURCE_FACT`

当前 LibTV 研究已经确认图片节点存在两个不同职责的浮层：

- `ImageToolbar` 在节点上方，采用 `NodeToolbar position=Top align=center`；当前生产 chunk 的 host 公式是 `nodeTop - 24 * zoom - 10`，结合 `translateY(-100%)` 后，screen gap 为 `10 + 24 * zoom`；
- `ImageEditPanel` 在节点下方，是节点内容层内的编辑面板，使用节点中心和 `scale(1/zoom)` 保持屏幕尺寸；下方面板的 gap 是 `16 * zoom`；
- 当前工具条是 `w-fit`，2026-08-25 历史快照为 `900.5x49`，2026-08-26 当前五节点快照为 `1092.5x49`；旧 clone 的固定 `900.5px` 和 `offset=16` 均不足以表达当前合同；
- 源站允许节点靠近边缘时自然被画布容器裁切，没有证据支持把浮层强行移到窗口中心。

详细证据见 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) 和 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)。

### 3.3 `INFERENCE`

两项目的共同问题是：节点 DOM 的实际尺寸、React Flow viewport 和浮层渲染层若分别取值，就会出现“节点看起来在这里、上面的条在那里、下面的面板又按另一套缩放”的错位。

Open Canvas 提供的可迁移抽象是一个共享的 `NodeScreenRect` / `OverlayAnchor` 计算边界，而不是它的具体 gap、宽度和 page-level `Panel` 层级。对 LibTV，最小抽象至少要保留：

```text
同一 live viewport snapshot
  -> measured node rect
  -> node center / top / bottom
  -> toolbar anchor + editor anchor
  -> 同一选择生命周期和 z-index contract
```

### 3.4 `CLONE_DECISION`

- P0 研究/实现入口是验证 clone 在拖动、平移、28%/53%/100% zoom、四边裁切、选择切换和空白卸载时，两个浮层是否使用同一份 rect/viewport；
- 允许借鉴“集中计算 screen anchor”和 measured 尺寸回退；
- 不复制 Open Canvas 的 `18px` editor gap、`360..820px` 宽度、页面级 editor Panel 或其图片工具条样式；
- 不添加自动避让、窗口居中或额外 clamp，除非重新获得 LibTV 源站证据；
- 该卡可以授权后续测试设计，但本研究批次不修改 `src/`。

### 3.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| rect 一致性 | 两个浮层都由被选节点同一尺寸和 viewport 推导 |
| 纵向关系 | 顶部使用 LibTV 当前 `10 + 24 * zoom` 合同，底部使用 `16 * zoom` 合同 |
| 尺寸关系 | toolbar 使用动作集合驱动的 fit width，editor 保持源站屏幕尺寸 |
| 生命周期 | 节点拖动、viewport 变化、切换节点和空白点击不留下旧浮层 |
| 边缘行为 | 与源站一样允许容器裁切，不凭感觉重排 |

---

## 4. OC-PATTERN-02：Typed Input Buckets + Provider Projection

### 4.1 上游 `SOURCE_FACT`

固定版本 [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L69) 将媒体任务描述为结构化 descriptor：媒体类型、公开模型、provider、内部模型、scene、prompt、options 和解析后的输入分别存储。输入解析阶段把上游节点按 image/video/audio 分桶，并保留 `nodeId`、媒体 URL 和可选时长；最终才把公开模型投影到 provider route 和执行参数。

固定版本 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L207) 也把节点 patch、run record、媒体输出和节点状态分开，避免 UI 上的一个字符串同时承担图关系、运行路由和媒体身份。

这里真正值得借鉴的是“内部引用身份稳定，外部请求格式最后投影”。provider 名称、模型 slug 和请求字段本身不应成为画布图的主键。

### 4.2 LibTV 对应的 `SOURCE_FACT`

LibTV AutoLink 现场记录已确认：

- 候选来自连接/reference 资产，而不是一个无上下文的全局素材列表；
- Prompt 中可以先出现 inline ghost suggestion，点击或 Tab 接受；Shift+Tab 接受全部，Escape、编辑或 blur 清除；
- 正式 mention 需要保留稳定 node ID、媒体类型和候选序号/职责，提交时再投影为源站所需的显示形式；
- graph connection、reference assignment 和 prompt mention 是三种不同关系，不能用一个字符串前缀代替。

详细合同见 [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md) 和 [`LIBTV_AUTOLINK_STATE_MATRIX.md`](LIBTV_AUTOLINK_STATE_MATRIX.md)。

### 4.3 `INFERENCE`

Open Canvas 的 typed input buckets 与 LibTV AutoLink 不是同一个功能，但共享一个高价值的边界：**引用对象的身份与 provider/文案投影必须分离**。

这能解决 clone 当前固定候选弹窗和“接受后把字符串前缀写回 textarea”的脆弱性：文本只是展示/编辑表面，真正的引用应由结构化 token 或可重建的 mention metadata 管理。这样下游模型切换、候选重排、媒体类型校验和删除引用时，系统不会依赖不可逆的字符串解析。

### 4.4 `CLONE_DECISION`

- 允许借鉴 stable identity、typed bucket、提交前 projection 和错误码分层；
- LibTV 的稳定身份至少应覆盖 `sourceNodeId`、媒体类型、引用职责/handle、候选 ordinal 和当前 token 生命周期；
- 不复制 Open Canvas 的 provider slug、Handle 命名、scene 名称或 API payload；
- 不把 AutoLink 等同为普通 React Flow connection，也不因上游存在 typed handle 就改变 LibTV 的 handle 位置和 edge flow effect；
- 进入编码前，先完成当前 clone 的 token/候选/graph 三向状态测试，并把源站 DOM 证据补入 [`LIBTV_VERIFICATION_COVERAGE.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)。

### 4.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| 候选身份 | 同一节点在重排、切换模型和再次打开 prompt 后仍可识别 |
| 接受行为 | 点击、Tab、Shift+Tab、Escape、blur 与源站生命周期一致 |
| 关系隔离 | graph edge、reference role 和 prompt mention 可独立增删 |
| 投影可逆 | 展示文本改变或 token 删除不会留下幽灵引用 |
| 类型边界 | 图片/视频/音频候选按源站允许的职责过滤 |

---

## 5. OC-PATTERN-03：Node Status / Run Status / Save Status 分离

### 5.1 上游 `SOURCE_FACT`

Open Canvas 的节点数据包含 `idle/queued/running/success/error` 类节点状态；执行层另有 run status，并通过 [`execution.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L815) 在 AI task status、canvas run status 和 node status 之间映射。store 还独立保存 `isDirty`、`saveStatus`、`saveError` 和 `conflictDetected`，见 [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38)。

因此“正在生成”“当前节点显示什么”和“画布有没有保存”不是同一个 loading flag。保存冲突可以阻止新的 graph mutation，但不应伪装成 provider 生成失败；任务结束也不应自动抹掉未保存的用户编辑。

### 5.2 LibTV 对应的 `SOURCE_FACT`

当前研究对象是前端 prototype，尚未授权接入真实 provider、上传、持久化或任务轮询。Seedance 2.5 文章和 LibTV 画布研究却已经暴露出多种需要区分的产品语义：普通生成、长视频分段/续写、片段重拍、逐帧拉片、字幕/音频/深度等过程型能力，以及结果节点和派生节点之间的版本关系。

这些是功能观察，不等于当前 clone 已有真实运行后端。当前 clone-only 行为必须继续保持 mock/本地可验证边界。

### 5.3 `INFERENCE`

如果后续把所有过程都压成一个节点 `status`，用户会无法区分：

- 这张卡片是在等待输入、等待任务还是等待保存；
- 失败是参数校验、任务失败、网络失败还是模拟数据；
- 结果回来后是否覆盖了用户刚刚修改的 prompt/参数。

Open Canvas 的启发是状态边界和转换记录，不是引入它的 provider 或后端实现。

### 5.4 `CLONE_DECISION`

- P1 先为 LibTV 的过程型能力建立状态词汇和可见状态矩阵：编辑草稿、候选任务、运行中、结果版本、失败、保存状态；
- 在没有真实后端授权前，只允许使用可复现的 mock 状态，必须显式标识 mock，不得写成真实 Provider 已接通；
- 长视频、重拍、拉片和音视频处理优先采用“新版本/派生节点”研究模型，是否回写原节点必须以源站行为为准；
- 可借鉴 run 与 save 分离、错误码可观察、异步结果不覆盖后续编辑；
- 不复制 Open Canvas 的 `provider/model/aiTaskId` 作为 LibTV UI 的用户可见合同。

### 5.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| 状态正交 | 运行状态、节点内容状态、保存状态能同时表达而不互相覆盖 |
| 结果保护 | 异步结果落回时不会覆盖更晚的用户编辑 |
| 失败可解释 | 参数、任务、网络、mock 四类失败至少能被区分 |
| 版本可追踪 | 重拍/续写/拉片结果能回溯源节点、操作和版本 |
| 后端边界 | 文档和 UI 不宣称尚未存在的 provider 或持久化能力 |

---

## 6. OC-PATTERN-04：Serialized Subgraph + ID Map

### 6.1 上游 `SOURCE_FACT`

Open Canvas 的画布 store 维护 nodes、edges、viewport、revision 和保存基线；连接前使用图校验和环检测。复制/粘贴由 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896) 提取选中节点及其内部边的结构化快照，paste 时由 [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339) 为每个旧节点生成新 ID，并通过 `idMap` 重写边的 source/target，保留合法的 handle/type/data。

这意味着复制不是把 DOM 或屏幕截图复制过去，而是序列化一个可校验的局部子图，再将内部身份映射到新图。节点位置也按 flow coordinate 加偏移，而非直接复用屏幕坐标。

### 6.2 LibTV 对应的 `SOURCE_FACT`

当前 LibTV 研究正在面对越来越多的派生关系：图片工具动作可能生成新的派生节点，元素编辑与图层分离有独立 surface，Seedance 2.5 亮点还涉及长视频、镜头/片段、重拍、逐帧处理和继续创作。与此同时，现有项目已规定 `canvasStore` 与 `frameosStore` 分离，LibTV graph、edge flow effect 和节点类型不能被 Open Canvas 的五类节点模型替换。

目前没有充分源站证据证明 LibTV 所有这些操作都以“复制子图”呈现，因此这里先记录为结构性研究问题。

### 6.3 `INFERENCE`

一旦结果、过程或重拍版本要在画布中共存，只有媒体 URL 不够：还需要知道它由哪个源节点、哪次操作、哪个输入时间范围/引用关系产生。结构化子图和 ID map 提供了一种保护：派生结果可以新增节点并改写内部连接，同时不会让旧节点的 ID、mention 或下游引用静默指向新对象。

该启发尤其适合验证“复制/派生后上下浮层选中谁”“删除源节点后结果是否仍可用”“下游引用是否跟着当前版本走”等问题。

### 6.4 `CLONE_DECISION`

- P1 研究先绘制 LibTV 的“派生操作关系表”：操作、源节点、输入引用、时间范围、输出节点、边变化、撤销/删除语义；
- 允许借鉴序列化子图、局部合法性校验、新旧 ID 映射和 flow 坐标偏移；
- 不把 Open Canvas 的五类节点、通用 `type/data` 或 clipboard MIME 当作 LibTV 领域模型；
- 若源站实际是原节点内的候选历史，就不能为了复用 ID map 强行创建新节点；反之，若源站明确创建派生节点，就不能把历史版本覆盖在原节点里；
- 在 UI/UX 复刻授权之前，只新增研究矩阵，不修改 graph store、节点类型或边行为。

### 6.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| 身份唯一 | 派生节点与源节点、旧版本、新版本 ID 不混淆 |
| 边完整 | 复制/派生后内部边和引用职责仍可解释，且不形成非法环 |
| 坐标稳定 | flow position 与 viewport 解耦，粘贴偏移不因 zoom 改变 |
| 版本语义 | 当前预览、历史候选和下游引用各自指向明确版本 |
| 撤销边界 | 单次操作的节点、边、媒体和选择状态能整体回滚或明确不可回滚 |

---

## 7. OC-PATTERN-05：Run-keyed Polling + Stale-safe Result Ingress

### 7.1 上游 `SOURCE_FACT`

Open Canvas current studio 在 execute 前保存 graph，把 revision 交给 runner；runner 从 persisted graph 构造 descriptor、创建独立 run，非 terminal 任务由 client 使用 run ID 轮询。Server node patch 会推进 durable canvas revision，client store 同时 patch live node 与 saved graph baseline。页面还可以从 node 的 `queued/running + lastRunId` 恢复 polling。

这套结构把 component timer、run identity、provider result、node projection 和 save baseline 分开，是当前 clone 值得借鉴的控制面。

固定实现也提供了重要反例：node patch 只按 canvas/node ID 应用，不比较 expected current run、source media version 或 field owner；run terminal 与 node patch 是两个独立 local DB 写入；runner 在创建 `running` run 后发生 unsupported/provider exception 时没有统一 terminal cleanup。详见 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) 的 `OC-AR-001..009`。

### 7.2 LibTV 对应的 `CLONE_FACT`

当前 committed clone 没有普通 canvas fetch/run store：

- shot breakdown、audio split、depth motion、smart matting、picture edit 和 long video 由 component-local timer 延迟调用 graph creator；
- 多数结果创建后永久保持 `pending`，没有 completion ingress；
- timer callback 可在用户已选择其他节点后改写全局 selection；
- shot breakdown 可在运行期间继续修改 dimensions，旧 descriptor 结果与新 source data 可能失配；
- Director animation export 是唯一真实 browser-side async asset 完成后再创建 ready canvas result 的路径。

这些行为是 `PROTOTYPE_LATENCY` 或本地导出，不是源站 task backend。

### 7.3 `INFERENCE`

仅把 timer 换成 fetch/poll 不会自动获得正确性。真正需要的是：

```text
captured operation descriptor
  -> run / attempt / result envelope
  -> current owner + source version compare
  -> field ownership check
  -> stale / duplicate / current disposition
  -> validated full graph plan
  -> idempotent commit or zero mutation
```

没有这条链，旧 retry 可以覆盖新 retry、source 删除后结果可以复活节点、translated error 可以被当作 local dirty edit、重复 poll 可以添加重复 result，component unmount 也会不清楚是在停止观察还是取消真实任务。

### 7.4 `CLONE_DECISION`

- 借鉴 run record、runId polling、独立 server authority 和 saved-baseline projection；
- 补充 source media version、descriptor fingerprint、attempt/result identity 和 operation-specific field registry；
- stale/duplicate/reject 默认 zero graph/history/selection mutation；
- progress 不进入 graph history；新 topology/accept result 才形成具名 transaction；
- undo 不自动重放 provider side effect；terminal envelope 与 graph projection 分离时必须可幂等重试；
- 当前无 provenance UI 时拒绝 stale result，不偷偷附加孤立历史节点；
- 不移植 Open Canvas generic `CanvasNodePatch`、URL identity、provider 或 file/KV persistence。

### 7.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| identity | canvas/source/version/operation/run/attempt/result 可独立检查 |
| freshness | source edit/delete、retry race、undo 和 canvas switch 有稳定 disposition |
| idempotency | duplicate/out-of-order completion 不增加 node/edge/history/resource owner |
| field owner | result patch 不覆盖 current draft、graph identity 或 unrelated selection |
| recovery | terminal result 可重试 graph projection，而不重新调用 provider |
| resource | blob/temp output 在 commit transfer 或 reject cleanup 时只处理一次 |

设计 authority：[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` 和 `LIBTV-VR-015`。

---

## 8. OC-PATTERN-06：Current-state Change Adapter + Semantic Whitelist

### 8.1 上游 `SOURCE_FACT`

Open Canvas 与 clone 都锁定 `@xyflow/react@12.11.1`。上游的 `onNodesChange/onEdgesChange` 使用 Zustand functional updater，因此 reducer base 是 callback 执行时的 current store state，而不是创建 callback 时的 React render closure；revision conflict 下，persistent change 还会被 gate。

固定实现同时把 exact framework union 的全部 variant 交给 generic reducer，并以“是不是 select”判断是否 persistent。该版本的 node change 包含 add/remove/replace，edge change 的所有 non-select variant 都是 add/remove/replace；reconnect 不是 EdgeChange，而是独立 callback/helper。上游因此提供了 current-state ownership 的正例，也提供了 semantic mutation 混入 framework transport 的反例。

### 8.2 LibTV 对应的 `CLONE_FACT`

当前 clone 已把 node selection 投影到独立 selected IDs，并把 drag frames 压缩为 drag-stop 一次 history；命名键盘删除和连接也已经有独立 command path。

但 route callback 仍存在：

- node selection 先发生，全部 non-select variant 再 generic apply；
- edge select/add/remove/replace 全部 generic apply；
- edge reducer base 来自 rendered `edges` closure，再整数组写回 store；
- edge selection 可进入 semantic edge/history/document shape；
- measured/dragging/resizing 等 runtime fields 缺少统一 boundary sanitation；
- mixed semantic batch 没有 zero-partial policy。

### 8.3 `INFERENCE`

React Flow 的 reducer 是 deterministic delta executor，不是 LibTV graph policy。把 union 中的 add/remove/replace 当普通 callback payload，会绕过 connection validation、delete repair、node-data registry 和 history command boundary。使用旧 render closure 做 whole-array writeback，还会让“刚刚由另一个 command 创建的 edge”面临被旧 selection callback 覆盖的竞态。

正确链路是：

```text
exact batch parse
  -> classify all variants before mutation
  -> T0 selection owner
  -> T1 existing-node position/passive measurement
  -> T2/T3 semantic command or reject
  -> current active-canvas snapshot commit
  -> document/copy/history runtime-field sanitation
```

### 8.4 `CLONE_DECISION`

- 借 Open Canvas functional current-state ownership，不借 all non-select generic apply；
- selection 是 T0；只有 existing-node finite position 和无 `setAttributes` 的 passive measurement 是 T1；
- edge 没有 non-selection T1 variant；add/remove/replace/reconnect 必须回到命名 command；
- mixed malformed/semantic batch 在任何 selection/position side effect 前 reject 或整批 reroute；
- drag frames 零 history，changed drag stop 正好一个；passive measurement 零 history；
- edge selection 必须有声明 owner，selected/measured/dragging/resizing 不进入 portable graph/copy/semantic history；
- node resize/reconnect 仍需 LibTV source/product evidence，不因 framework API 存在而实现。

### 8.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| exhaustiveness | exact 12.11.1 variant 全分类；unknown 有 stable reject |
| batch atomicity | semantic/malformed mixed batch 没有 partial selection/position |
| current snapshot | stale render callback 不丢失更新较晚的 node/edge，也不写错 active canvas |
| command authority | add/remove/replace/reconnect 不绕过 connection/delete/layout/document contract |
| history | many drag frames + one changed stop 只有一条 history；selection/measurement 为零 |
| sanitation | runtime React Flow fields 不进入 portable document、copy packet 或 semantic hash/history |

设计 authority：[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、`LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` 和 `LIBTV-VR-016`。

---

## 9. OC-PATTERN-07：Document Identity + Hydrate Owner + Switch Manifest

### 9.1 上游 `SOURCE_FACT`

Open Canvas 将 canvas registry summary、URL `canvasId` 和 full document record 分开。List page 只消费 title/revision/preview/timestamps；studio route 按 ID 取一个完整 graph，missing ID not-found。`hydrate` 一次替换 canvasId、nodes/edges、viewport、revision、saved baseline、dirty/save/error/conflict。Delete 还会清理同 canvas runs，并在 registry 为空时创建一张空 document。

这套结构建立了强 document identity，但并不自动解决所有跨 route async：graph PUT 使用旧 `initialCanvas.id` 是正确 durable target；response 后的 global `finishSave/failSave/enterConflict` 却不比较 current store canvasId。旧 route promise 在新 canvas hydrate 后 settle，可能污染新的 local revision/save owner。这是静态竞态推断，不是 live incident。

### 9.2 LibTV 对应的 `CLONE_FACT`

当前 clone 已有：

- `canvases[] + activeCanvasId` 内存 registry；
- 每张 canvas 独立 graph/viewport 和 `historyByCanvas`；
- Batch 16 create/switch/rename/duplicate/delete UI；
- switch/create/duplicate/active delete 清 selection；
- React Flow 以 activeCanvasId key remount；
- Batch 58 preview/annotate/element edit/Director owner reconciliation。

未收口的 owner 包括 invalid active target、demo responsive viewport preset、organize snapshot、drag baseline、connection gesture、late viewport callback、projection panel、timer/export destination 和 resource/run lifecycle。

### 9.3 `INFERENCE`

切换画布不是“换数组”也不是“closeAll”。每一类状态必须声明 preserve、restore、clear、rebind、cancel、detach 或 continue：

```text
project registry persists
canvas graph / viewport / history stay keyed by canvasId
active selection clears
node-bound surface closes
projection panel closes or rebinds atomically
page-local transaction cancels
async operation remains bound to original canvas
resource owner changes only by explicit policy
```

只依赖 React subtree remount 无法清理 route component 外层 refs；只在 delayed callback 执行时读取 active canvas 则会把旧 operation 重新定向。

### 9.4 `CLONE_DECISION`

- 保留 LibTV in-place dropdown UX，不复制 Open Canvas list-card/URL visual；
- unknown canvas target reject/no-op，active ID 始终解析；
- switch 保持 source/target graph、viewport、history，清 current clone selection，零 graph history；
- organize/drag/connection/viewport transient 携带 canvas/generation，switch 后 old owner no-op；
- node-bound UI 继续按 `canvasId + nodeId` 失效；projection panel 明确 close/rebind；global preference 可声明保留；
- duplicate/delete 组合 node-data/copy/delete/resource/async registry，不能只 remap/filter structural graph；
- final delete、fallback、responsive preset、background operation 和 resource policy 保持 source/product queue；
- network request durable target 与 local convergence owner 都必须检查。

### 9.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| registry | active ID resolves、canvas IDs unique、unknown/same target stable |
| switch | source/target graph/viewport/history exact；selection clear；zero history |
| transient | old organize/drag/connection/viewport callbacks cannot mutate target |
| UI | node-bound closes；projection panel target-only；global preference exact |
| duplicate/delete | full identity/resource/run plan；fallback/final policy；zero-partial |
| async | old timer/save/export result cannot late-write current canvas or steal selection |

设计 authority：[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、`LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017`。

---

## 10. 七张卡的共同落地顺序

```text
01 浮层 screen rect 合同
  -> 02 AutoLink stable identity
  -> 04 派生/版本关系
  -> 03 运行、节点、保存状态
  -> 06 framework change authority
  -> 07 canvas lifecycle owner isolation
  -> 05 异步结果入口与陈旧收敛
```

这个顺序不是实现顺序，而是研究依赖：

- 浮层几何是当前已确认的高价值视觉缺口，且不依赖真实后端；
- AutoLink 的身份边界会影响后续引用、候选和派生节点的关系表达；
- 派生/版本关系明确后，才能设计长视频、重拍和过程型状态；
- 运行与保存状态先归纳语义，避免为尚未确认的源站操作预先制造状态机；
- framework callback 先限定 T0/T1，防止命名 graph command 被 generic reducer 旁路；
- canvas lifecycle 先固定 active/document/session owner，避免旧 callback 在新画布收敛；
- 最后才设计 completion ingress，确保它复用已决定的身份、状态和 graph authority。

## 11. 统一拒绝清单

在后续“借鉴”中，以下做法默认禁止，除非有新的 LibTV 源站证据和用户编码授权：

- 把 Open Canvas 的视觉尺寸、间距、颜色、provider 文案或模型 slug 直接移植到 LibTV；
- 用一个固定 CSS offset 修复所有双浮层，而不检查 measured size、viewport 和选择生命周期；
- 把 AutoLink 的 mention、graph edge、reference role 合并为字符串或单一连接；
- 把 mock `running/success` 文案描述为真实任务后端；
- 把 Open Canvas 的 generic node patch、URL media identity 或 read-modify-write persistence 当成 stale-safe 模板；
- 把 React Flow union 的 add/remove/replace 当作无须 domain validation 的普通 transport；
- 因为 Open Canvas 使用 URL canvasId，就复制其列表页、route、final-delete 或持久化产品语义；
- 依赖 incidental React remount 清理所有 page-local transaction，或让 delayed callback late-read active canvas；
- 因为 Open Canvas 支持复制子图，就擅自改变 LibTV 的派生节点/历史候选语义；
- 修改 LibTV 现有 edge flow effect、Handle 位置、FrameOS 独立 store 或源站未证实的移动端布局。

## 12. 后续研究入口

- LibTV 功能差距与优先级：[`LIBTV_FEATURE_GAP_MATRIX.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)
- LibTV UI 状态层级：[`LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)
- Open Canvas 到 LibTV 的转译：[`UIUX_TRANSLATION.md`](UIUX_TRANSLATION.md)
- Open Canvas 深度报告：[`REPORT.md`](REPORT.md)
- 异步结果入口与陈旧收敛：[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)
- React Flow change routing：[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)
- Multi-canvas lifecycle：[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)
- 后续研究总计划：[`NEXT_RESEARCH_PLAN.md`](../liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md)

**本卡片集的结论：** Open Canvas 最值得借鉴的是可复核的边界和数据流，而不是“长得像画布”的视觉细节。LibTV 复刻继续以源站证据为准，Open Canvas 只负责帮助我们把已确认的问题拆成可验证、可撤销、可分层的工程合同。
