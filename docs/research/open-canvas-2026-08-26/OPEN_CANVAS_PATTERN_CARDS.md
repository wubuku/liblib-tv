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
| OC-PATTERN-06 | current-state change adapter + semantic whitelist | framework delta 旁路领域命令与陈旧闭包覆盖 | 适合收窄 React Flow node/edge change transport | P0，正式合同完成，runtime partial |
| OC-PATTERN-07 | document identity + hydrate owner + switch manifest | 多画布切换时 graph/UI/async owner 串线 | 适合当前 in-place canvas registry | P0，正式合同完成，runtime partial |
| OC-PATTERN-08 | typed outcome + primary surface + owned announcement | 命令效果与反馈文案/落点/生命周期混合 | 适合统一 reject、process、Director 与 utility feedback | P0，正式合同完成，runtime partial |
| OC-PATTERN-09 | validated selection + declared context + owned focus return | selected flags、快捷键、浮层层级和焦点回归分叉 | 适合节点/边/primary selection、Director/modal precedence 与单层 Escape | P0，正式合同完成，runtime partial |
| OC-PATTERN-10 | dual anchor + live/stable viewport + entry-specific placement | browser/host/flow 坐标、移动帧、稳定恢复和创建入口互相覆盖 | 适合 default add、zoom/fit/resize、drag/organize、copy/derived placement 与 overlay composition | P0，正式合同完成，runtime/source parity partial |
| OC-PATTERN-11 | validate/probe/materialize + explicit resource lease | 文件意图、临时 bytes、稳定 asset、node reference、graph/history 与 cleanup 分叉 | 适合 Add Resource、生成历史、Shot Breakdown、普通图片编辑和 Director media boundary | P0，正式合同完成，runtime missing/partial、source parity partial |
| OC-PATTERN-12 | foreground editor session + owned local history + typed commit handoff | baseline、draft、本地撤销、graph history、异步保存和关闭生命周期分叉 | 适合文字、配置、标注、图片编辑、字幕区域、范围选择和请求草稿 | P0，正式合同完成，runtime fragmented、source parity partial |
| OC-PATTERN-13 | selected output + declared frame/rendition + fresh measurement | media/output/request/frame/measured/editor coordinate 混为一组尺寸 | 适合普通图片/视频、详情预览、混合比例版本、标记编辑器与双浮层 anchor | P0，正式合同完成，runtime fragmented、source ratio-diverse parity gated |

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

未收口的 owner 包括 invalid active target、organize snapshot、drag baseline、
connection gesture、generic late viewport generation/host epoch、projection panel、
timer/export destination 和 resource/run lifecycle。Batch 65 已关闭 demo responsive
preset 覆盖 stable viewport 和 current/old canvas viewport callback 的 focused
clone slice，但没有实现完整 lifecycle owner。

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
- final delete、fallback、source-exact responsive policy、background operation 和 resource policy 保持 source/product queue；
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

## 10. OC-PATTERN-08：Typed Outcome + Primary Surface + Owned Announcement

### 10.1 上游 `SOURCE_FACT`

Open Canvas 的 feedback 不是单一 toast 系统：

- root layout 挂全局 bottom-right Sonner Toaster；
- graph command 返回 `ok/code/message`，studio adapter 再投影 error toast；
- node run/upload 把 queued/running/success/error、errorMessage、lastRunId 保留在 node，并投影 card/MiniMap/editor；
- save/dirty/error/conflict 使用持续 header status 和 conflict banner/action；
- provider settings 使用 field error map + summary toast + saving control；
- list CRUD 对 create navigation、same-title noop、cancel、rename/delete/import 采用不同反馈策略。

固定实现同时提供两个反例：具体 reason 主要埋在中文 message，i18n 通过 literal string/标点匹配；global toast call 没有 canvas/operation/attempt/dedupe owner。

### 10.2 LibTV 对应的 `CLONE_FACT`

当前 clone 已有多种反馈 island：

- connection validator 的 stable reason union，但 page reject silent；
- Share/Agent/AddNode/VideoClip 的 string-only surface status；
- VideoNode 的 frame/picture/depth action-specific timer chip；
- toolbar `lastAction`、segment/long-video submitted/busy；
- Director export/phone/camera preset 的 persistent progress/error/retry surface；
- FrameOS 独立 toast，不属于普通 LibTV route。

这些 island 多数保持 graph/history 分离并诚实标记 local prototype，但没有共同 disposition、primary surface、owner、clear/retry/dedupe authority。

### 10.3 `INFERENCE`

```text
typed disposition + reason code/args
  -> graph/history effects
  -> one primary owner-local surface
  -> optional secondary announcement
  -> clear/retry/switch/delete/dedupe lifecycle
```

Durable/recoverable failure 必须留在 node/surface/canvas owner；copy/download 等无持续可见对象的动作适合 transient confirmation；visible graph result 本身是 primary；cancel/noop/stale/duplicate 通常 silent。Toast 不能填补未知 workflow，也不能让 old-canvas completion 宣告当前成功。

### 10.4 `CLONE_DECISION`

- outcome 先归入 committed/started/completed/rejected/noop/failed/canceled/stale/conflict/unknown；
- stable reason/args 与 localized/source display copy 分开；
- reject/noop/stale/unknown 默认 zero graph/history；
- 一个 outcome 只有一个 primary persistent authority；
- field error、node process、canvas conflict、utility confirmation 使用不同 surface；
- local prototype 保持 unavailable/local-preview 诚实边界；
- switch/delete/retry/unmount/burst 明确 owner 和 dedupe；
- 未取得 LibTV source evidence 前不新增 global toast、invalid Handle style 或统一 timeout；
- 不复用 FrameOS toast/store。

### 10.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| identity | disposition/reason/args 稳定；display text 不参与 branching |
| transaction | reject/noop/stale zero graph/history；feedback 不进入 document/history |
| surface | durable error 可恢复；visible result 不靠 toast-only；one primary owner |
| owner | node/canvas/surface/attempt 与 switch/delete/unmount exact |
| timing | retry、timer replace、duplicate terminal、burst dedupe deterministic |
| accessibility | field association、busy state、persistent recovery、no duplicate announcement |
| route | LibTV/FrameOS queue/store/announcement isolation |

设计 authority：[`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、`LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01` 和 `LIBTV-VR-018`。

---

## 11. OC-PATTERN-09：Validated Selection + Declared Context + Owned Focus Return

### 11.1 上游 `SOURCE_FACT`

Open Canvas 把一部分 selection、keyboard 和 focus 责任显式化：

- React Flow node/edge `selected` flags 参与局部 selection 投影；
- editable target guard 阻止画布 Delete 等快捷键吞掉输入编辑；
- 节点编辑器保留局部 draft/commit owner；
- Radix Dialog/Popover 负责部分 focus containment、Escape 和 return-focus；
- pending connection、conflict、menu/editor 形成局部前台上下文。

固定实现也提供边界反例：selected flags 不能独立表达 primary/active canvas；部分全局 key handler 依赖默认事件传播；conflict gate 与弱 Escape handler 不是统一 context resolver；Radix 只能约束其管理的 surface，不能自动协调 canvas、Director 和 route owner。

### 11.2 LibTV 对应的 `CLONE_FACT`

当前 clone 同时存在 node selection projection、edge selected runtime field、page bubble shortcut、modal capture guard、Director foreground isolation 和多个 surface-local Escape/focus effect。静态审计确认：

- node/edge selection 尚无统一 node/edge/primary snapshot；
- editable guard、modal/Director precedence 分散在不同 listener phase；
- Batch 50 后 Director 前台隔离的是所有普通 page shortcut，旧文档曾只描述 Escape；
- surface close 后的 focus return/fallback 没有共同有效性规则；
- selection/focus/context 应属于 active session，不进入 portable document 或 semantic history。

### 11.3 `INFERENCE`

```text
raw node/edge selection events
  -> validate against active canvas + derive primary
  -> resolve top command context from focus/surface stack
  -> dispatch HANDLED / CONSUMED / PASS / BLOCKED / NOOP
  -> apply at most one Escape unwind
  -> return focus to a still-valid owner or deterministic fallback
```

选择集合、焦点位置和命令上下文是三个相关但不等价的 owner。可靠行为不能由 `event.target`、React Flow flags 或组件 mount 状态单独推导；每次 dispatch 都必须使用当前 active canvas generation 和前台 surface snapshot。

### 11.4 `CLONE_DECISION`

- node IDs、edge IDs 和 primary 组成一份经过 active graph 校验的 session selection；
- React Flow `selected` 只作为 transport/projection，不作为 portable document/history authority；
- editable、node control、canvas、modal、Director 和 route 采用声明式 context policy；
- 每个 handler 返回明确 dispatch result，禁止多个层级隐式重复处理；
- 一次 Escape 只退出最上层一个可退出 context；
- modal/Director 必须 containment；close 后仅向仍存在、可见、未 disabled 的 origin 回焦，否则走稳定 fallback；
- switch/delete/undo/unmount 清理 stale selection、surface owner 和 focus return target；
- 不引入全局 modal manager，也不因上游使用 Radix 就改造现有组件栈。

### 11.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| selection | node/edge IDs 属于 active graph；primary 唯一且可推导；stale ID 清理 |
| context | editable/modal/Director/canvas precedence 对每个目标快捷键确定 |
| dispatch | `HANDLED/CONSUMED/PASS/BLOCKED/NOOP` 无重复 graph/history effect |
| Escape | 每次只退一层；不可退出层明确 consumed/blocked；不穿透到底层 |
| focus | acquire/contain/return/fallback 可观察；不回到 stale/hidden/disabled owner |
| lifecycle | switch/delete/undo/unmount 与 canvas generation 隔离；selection/focus zero semantic history |
| route | LibTV 与 FrameOS listener/store/focus owner 独立 |

设计 authority：[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` 和 `LIBTV-VR-019`。

---

## 12. OC-PATTERN-10：Dual Anchor + Live/Stable Viewport + Entry-Specific Placement

### 12.1 上游 `SOURCE_FACT`

固定 Open Canvas shell 同时保存 Quick Add 的 screen surface position 和 graph flow position：前者基于实际 canvas container rect 计算并 clamp，后者由同一次 current React Flow conversion 捕获，菜单贴边不会改写节点落点。普通 Add Node 也读取实际 container center，再调用 `screenToFlowPosition`。

Viewport 存在两个明显阶段：`onMove` 更新 `liveViewport` 供 selected overlay 和当前 projection 使用，`onMoveEnd` 再写稳定 store viewport。Add、drop、paste、duplicate、pending connection 和 initial topology 使用不同放置入口，而不是复用一个“当前中心 + 固定 offset”。对应 fixed evidence 是 `OC-053..060`。

固定实现也提供反例：viewport normalize 会给异常 supplied value 静默 fallback；窄 container menu clamp 可产生负位置；custom panning 未完整声明 pointercancel/blur cleanup；multi-file drop 逐文件异步提交；pending connection 先建 node 再补 edge，不是完整原子 graph plan。

### 12.2 LibTV 对应的 `CLONE_FACT`

当前 clone 已有 per-canvas controlled viewport、V/H/Space blur/visibility cleanup、drag-stop one-history、source-relative derived placement、fixed-flow duplicate、organize layout 和 source-shaped selected-image overlay formula。这些是应保留的正面 island。

跨入口仍有四类缺口：

- default add 使用 `window.innerWidth/innerHeight`，asset panel/compact layout 后不等于 actual React Flow host center；
- page/store/zoom projection 没有明确区分 live frame、stable endpoint 和 bootstrap preset；
- organize/drag/connection/viewport transient 缺 canvas generation/operation identity；
- `{x,y}` 在 client、host、flow、node-local 和 media normalized 之间缺统一声明边界。

### 12.3 `INFERENCE`

```text
current route + canvas generation
  -> measured actual host + host epoch
  -> current live/stable viewport phase
  -> one declared coordinate conversion
  -> named gesture or placement intent
  -> validated plan/result
  -> exact projection/history/selection reconciliation
```

空间正确性不是抽取一个通用 transform 函数，而是确保 host、viewport frame、canvas generation 和 command intent 属于同一 owner。Screen menu/overlay 的可见位置和 graph node 的 flow anchor 可以相关，但不能共享一个会被 clamp 的坐标值。

### 12.4 `CLONE_DECISION`

- 使用 actual React Flow host，不用 browser window，作为 client/local conversion 和 host-center add 的 correctness floor；
- 显式区分 `CLIENT/HOST_LOCAL/FLOW_WORLD/NODE_LOCAL/SCREEN_OVERLAY/MEDIA_NORMALIZED`；
- live viewport 驱动当前 overlay/conversion，stable viewport 只在 current operation end 提交，bootstrap 只用于无用户状态的首次投影；
- pan/zoom/drag/connection/menu/organize 和 delayed point 携带 canvas generation，必要时携带 host epoch/operation ID；
- add、derived、duplicate、paste、organize 等入口分别声明 placement policy、selection 和 history；
- viewport/host/menu/temporary gesture 零 semantic graph history；accepted graph placement 保持专属命令的一步 history；
- 不移植 Quick Add/file drop/pending connection、菜单视觉/数字、Open Canvas zoom/pan/persistence 或 permissive normalize。

### 12.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| domain | 每个 conversion/placement boundary 只有一个 domain；NaN/Infinity/stale owner 零 residue |
| host | full/asset-open/compact 使用实际 React Flow host rect；default add center exact |
| viewport | live frames、stable endpoint、bootstrap guard、interrupted operation 和 switch race exact |
| gesture | start/update/end/cancel/stale idempotent；V/H/Space 现有 cleanup 不回归 |
| placement | default/derived/duplicate/organize 各用声明策略；pan/zoom 不改变 flow delta |
| overlay | actual host + one live viewport + measured world node；LibTV 既有公式保持 tolerance |
| history/route | viewport zero graph history；graph placement exact one-step；FrameOS/Director isolated |

设计 authority：[`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 和 `LIBTV-VR-020`。

---

## 13. OC-PATTERN-11：Validate/Probe/Materialize + Explicit Resource Lease

### 13.1 上游 `SOURCE_FACT`

固定版本 Open Canvas 已提供一条完整但并不完美的 media ingress 路径：

- image/video 控件先按 family、size 做客户端校验，并探测 image dimensions 或 video duration；
- multipart upload route 在服务端再次校验 MIME、空文件和大小，并返回稳定 URL/key/metadata；
- digest key 可以让相同内容复用 storage object，graph node 只保存归一化 descriptor；
- duplicate、paste、save/hydrate 会继续携带 descriptor aliases；
- local asset picker 和 local audio materialization 明确 unavailable，证明能力缺失可以诚实投影。

同时，`OC-061..070` 也固定了不能复制的反例：accept 与 probe 支持面不一致、drop 先建 running node、multi-file 逐项异步部分提交、text/audio 家族能力不对称、没有 expected operation/canvas/node freshness、没有 cancel 和 object URL/resource owner，autosave 还可能保存 running placeholder。

### 13.2 LibTV 对应的 `SOURCE_FACT` 与 `CLONE_FACT`

2026-08-27 的只读 source DOM 记录证明，LibTV 至少有四种不同资源域：

1. Add Resource 上传：multiple chooser，接受 image/video/audio；
2. Generated History：已有生成结果的多来源、多媒体类型选择器；
3. Material Library：风格和特效创建，不是普通媒体历史；
4. Asset Manager：Canvas/Assets 与 Personal/Agent 分域，当前 asset 空态不妨碍画布已有媒体节点。

Shot Breakdown 另有单 `video/*` source entry。当前 clone 则把 Add Resource upload/history 保持为 mock；Shot Breakdown 用 component object URL 做真实 local preview，却提前把 node 标成 ready；Director data/blob locator 进入独立 store，但还没有共同 resource authority。clone 中“我的素材库/预设素材库”的二分也不能继续被当作当前 source 事实。

### 13.3 `INFERENCE`

可迁移方法不是“加一个上传按钮”，而是把以下对象分开：

```text
immutable ingress intent
  -> local bytes + instance-scoped lease
  -> canonical validation + metadata probe
  -> materialization result
  -> stable asset identity
  -> node media reference
  -> provisional UI / semantic graph projection
  -> explicit transfer or exact-once release
```

一旦这些对象混成 `node.data.url`，cancel、retry、canvas switch、node replace、copy/history、delete/undo 和 object URL revoke 就无法共享同一套正确性。资源释放也不能只看 current graph；至少要检查 history、clipboard、editor/preview、active operation、asset registry 和可移植文档的 reachability。

### 13.4 `CLONE_DECISION`

- 采用 validation/probe/materialization/descriptor 的分层方法，不移植 Open Canvas 的 MIME/size 数字、storage、provider、placeholder skin 或逐项 history；
- Add Resource、canvas drop、node replace、Shot upload、history attach、asset attach、local edit export 和 Director ingress 必须用具名 entry profile 声明 transaction/history/selection/feedback/resource policy；
- `File`/`Blob` 与 preview/probe object URL 只进入 operation/lease owner，不进入 semantic history、portable document 或 stable asset identity；
- runtime provisional card 可以独立展示进度和逐项失败，但 accepted cohort 默认形成一个完整 graph plan 和一步 semantic history；
- replace 在新资源 commit 前保留 last-known-good media；invalid/noop/stale/canceled 产生零 semantic graph/history residue；
- 无后端 prototype 只能声明 `LOCAL_PREVIEW` 或 `UNAVAILABLE`，不能用 fake URL 宣称 durable upload；
- graph node 删除不自动删除 reusable remote asset；resource release 只由显式 owner 与完整 reachability ledger 决定；
- 本卡只形成设计/fixture/verifier authority，不授权修改 `src/` 或接入真实上传。

### 13.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| classifier | client convenience gate 与 materializer trust boundary 可区分；family/size/probe failure reason 稳定 |
| identity | ingress/attempt/canvas/node/source/asset/reference identity 不混用；retry 和 stale completion 不串线 |
| cohort | 多文件按原始顺序收敛；失败策略显式；accepted success 默认一步 graph history |
| replace | commit 前保留旧媒体；failure/cancel/stale 不覆盖 last-known-good |
| resource | object URL create/revoke exact-once；transfer/release 有 ledger；history/clipboard/editor reachability 被计入 |
| persistence | `File`/`Blob`/object URL 不冒充 portable locator；data URL 有预算和 provenance |
| surface | upload/history/material/asset/Shot/Director 保持不同 owner，不以相似媒体缩略图合并 |
| honesty | 无 provider/storage 时明确 local preview/unavailable；不伪造 durable/synced/saved |
| isolation | canvas generation、route 和 Director/FrameOS owner stale-safe；cancel/delete/switch 零晚到 residue |

设计 authority：[`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` 和 `LIBTV-VR-021`。

---

## 14. OC-PATTERN-12：Foreground Editor Session + Owned Local History + Typed Commit Handoff

### 14.1 上游 `SOURCE_FACT`

固定版本 Open Canvas 同时存在多类前台编辑会话：

- title/text 以 component-local draft 承接输入，再由 blur、Enter 或 Escape 选择提交/取消；
- rich note 使用 `contentEditable` 和提交前 sanitization；
- 图片编辑器创建随机 sessionId，保存 target node/media/title，并维护 load/stroke 后的完整 `ImageData` 历史；
- bitmap undo/redo 使用 cursor 和 redo truncation，Restore 折叠为单 baseline，最多保留 40 个 entry；
- Save 导出 JPEG 0.92，先关闭 editor，再由 caller 上传并按 node ID patch graph；
- graph dirty/revision/save baseline、editor local history 和浏览器原生 editable history 分属不同 owner。

这些机制证明“编辑器内部试错”和“画布语义提交”应分层；也暴露了不能照搬的缺口：session 不携带 canvas generation/source version，full bitmap 只按 entry 计数可能占用约 2.38 GiB，hidden fetch 没有真正 abort，close-first async save 缺 pending/failure return surface，caller 也可能忽略 no-op/conflict result。

### 14.2 LibTV 对应的 `SOURCE_FACT` 与 `CLONE_FACT`

当前 LibTV clone 已有十类不同成熟度的 foreground editor profile：

- `TextNode` 有 local draft，但 blur commit、Escape cancel 与 active upstream drift 尚未共享 typed session result；
- `ImageEditPanel` 的 Prompt、reference 与 submitted 状态仅在本地，Undo 按钮可见但无效；
- 图片标注已有 canvas/node owner reconciliation，但没有 record/local history，Undo/Redo disabled，Save 看似可用却无 handler；
- `PictureEditPanel` 有 30 步深拷贝 snapshot、gesture coalescing 和一次延迟 graph transaction，但 description/replacement 不进入同一本地历史；
- 字幕区域编辑有 30 步本地历史并立即写 graph，缺 panel-level submitting/idempotency token；
- 续写范围是一份局部草稿和一次 graph transaction；片段重拍草稿 local-only，缺显式 cancel callback；
- camera dialogs 没有已证 caller，取消后的 draft 可能跨 reopen 保留；video toolbar 的 Undo/Redo 是 enabled-looking inert control；
- graph `updateNodeData` 对现有 node 总是推进 history，没有 semantic equality/no-op gate。

这些差异不能被一个“所有弹窗共用 form hook”抹平。正式合同将它们分为 `INLINE_SCALAR`、`INLINE_MULTILINE`、`RICH_TEXT`、`MODAL_CONFIG`、`RECORD_EDITOR`、`BITMAP_EDITOR`、`RANGE_SELECTOR`、`REQUEST_DRAFT`、`LIVE_COALESCED_INSPECTOR` 和 `EMPTY_EVIDENCE_GATED` 十类 profile。

### 14.3 `INFERENCE`

可迁移的方法是让每次前台编辑显式拥有：

```text
session identity + target/source baseline
  -> working draft
  -> native or editor-local history
  -> typed commit intent/result
  -> exact one graph transaction or async handoff descriptor
  -> close/cancel/invalidation/resource convergence
```

Undo 路由必须取决于当前 foreground context：editable 原生 undo、bitmap/record local undo 和背景 graph undo 不能同时消费一个 chord。Baseline drift 也必须声明策略：clean session 可以 rebase，dirty session 默认不能被 effect 静默覆盖。异步保存不能把“关闭 editor”当成成功；handoff 必须绑定 canvas generation、session、target/source version 与 resource owner。

### 14.4 `CLONE_DECISION`

- 采用具名 editor profile、session/baseline/draft、typed commit result 和 native/local/graph undo precedence；
- local gesture 在编辑器内部 coalesce，只有 accepted semantic commit 才产生一步 graph history；invalid/noop/cancel/stale 为零 graph/history residue；
- bitmap history 同时受 entry、byte 与 dimension/pixel budget 约束，拒绝复制 fixed 40-entry full-image 策略；
- commit 前保留 last-known-good graph/media；异步 materialization 期间由明确 surface 显示 pending/failure/retry，不能 close-first 后静默失败；
- inert control 必须 disabled、标记 honest unavailable，或在拥有完整 handler/fixture 前不呈现为可用；
- 不移植 Open Canvas 的 JPEG/0.92、HTML schema、toolbar visual、timeout、session shape、upload/provider 或 graph save/revision 产品语义；
- 本卡只形成设计、fixture 和 verifier authority，不授权修改 `src/`。

### 14.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| session | open/reopen/switch/delete/unmount 形成唯一 owner；旧 callback 不写新 owner |
| baseline | clean rebase、dirty drift、semantic equality/no-op 和 restore policy 按 profile 明确 |
| history | native/local/graph undo 每次只由一个 owner 消费；gesture coalescing 与 redo truncation exact |
| commit | accepted exact one graph transaction 或 typed async handoff；invalid/noop/cancel/stale 零 residue |
| close | Escape/blur/submit/outside/switch/delete 的 close/cancel policy 可区分，focus return 不指向 stale owner |
| async/resource | pending/failure/retry surface 可达；freshness、last-known-good 与 resource transfer/release exact |
| budget | bitmap history 对 bytes/pixels/entries 均有 deterministic guard，不依赖浏览器 OOM 才收敛 |
| honesty | visible enabled control 有实际 handler；未实现能力明确 disabled/unavailable |

设计 authority：[`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)、`LIBTV-FIX-LOCAL-EDITOR-SESSION-01` 和 `LIBTV-VR-022`。

---

## 15. OC-PATTERN-13：Selected Output + Declared Frame/Rendition + Fresh Measurement

### 15.1 上游 `SOURCE_FACT`

固定版本 Open Canvas 把 selected media output 与主 preview 分开，并按 surface role 使用不同呈现方法：node/candidate/thumbnail 多为 cover，full-screen active image 使用 contain；selected index 会随 output collection normalize。图片上传还会先解码尺寸，再把最近 generation ratio 投影到请求设置。

这些做法提供了明确方法，也暴露了边界：`CanvasNodeMedia` 没有 intrinsic dimensions；video probe 只保存 duration；node card 高度跟随 request aspect 而非 selected output intrinsic；编辑输出追加后不更新 aspect 或保存导出尺寸；full/thumbnail metadata freshness、crop transform 和 editor coordinate space 都未形成完整 descriptor。Serialized node dimensions 和 passive measured rect 也不能证明存在 user resize。

### 15.2 LibTV 对应的 `SOURCE_FACT` 与 `CLONE_FACT`

2026-08-27 的 LibTV 共享画布只读测量证明五个 landscape image node 使用 media-shaped frame：`1808x1024 -> 618x350`、`1152x576 -> 700x350`、`1280x720 -> 622x350`，图片内容在 bordered content box 内 centered cover。选中节点后，toolbar 与 lower panel 均以 node center 为横向 anchor；因此 node frame 错误会继续放大为浮层 top/bottom/center 错位。

当前 clone 的初始 fixture 对齐这些值，但 generic image 把 square media 放入 `512x288` frame；多数 derived action 和 Director still capture 也会继承 media dimensions 后重置成 generic landscape frame。Node poster cover、detail preview contain、Director video contain 和 mark editor visible-node normalization 分散在不同 branch，没有具名 rendition profile。普通节点也没有 per-output dimensions/selected output identity，React Flow measurement 没有 media-ready/frame revision freshness contract。

### 15.3 `INFERENCE`

可迁移方法不是把所有媒体都改为 contain，也不是复制 Open Canvas fixed card。它要求先把十类 authority 分开：

```text
media intrinsic + thumbnail intrinsic + selected output
  + generation request + semantic node frame + passive measured rect
  + surface rendition + visible media rect + editor media space
  + export output
```

每个 media-bearing node 声明 frame policy，每个 surface 声明 rendition profile。Cover/contain 只是可逆 display transform；full-media editor 必须把 visible pointer 经过 content-box/crop transform 映射到 intrinsic space。Output switch 若改变 ratio，必须以一个 typed transaction 决定 frame reflow/preserve/reject/source-required，并等待 current measurement 后再断言浮层位置。

### 15.4 `CLONE_DECISION`

- 采用 stable output identity、per-output intrinsic metadata/provenance、具名 frame/rendition profile 和 current measurement epoch；
- current source-backed landscape image 保持 media-shaped centered cover，不以 Open Canvas request-shaped fixed card 替代；
- compact candidate/reference/filmstrip 可继续 fixed-cell cover，但 detail/full-media editor 默认优先 full-content visibility，直到 source evidence 给出其他策略；
- passive React Flow measurement、thumbnail/full swap 和 metadata cache refresh 不进入 semantic graph history；explicit resize 继续 source/product-gated；
- mixed-ratio output switch、frame reflow、selection 和 anchor refresh 形成一个具名 semantic plan，不允许 silent ratio drift；
- mark editor 必须声明 `FULL_INTRINSIC` 或 `VISIBLE_RENDER`；当前 visible-node normalized marks 不升级为 full-media correctness；
- 不移植 Open Canvas card width、aspect control、provider/media schema、rounded visual、crop numbers 或缺失 per-output dimensions 的做法；
- 本卡只形成设计、fixture 和 verifier authority，不授权修改 runtime。

### 15.5 验证门槛

| 检查 | 必须证明的内容 |
|---|---|
| authority | media/output/request/frame/measured/rendition 字段不混用；invalid/zero/missing metadata typed |
| frame | 16:9、2:1、1:1、9:16 和 odd ratio 的 frame decision finite、deterministic、source/prototype provenance 明确 |
| rendition | node cover 与 detail contain 均符合声明 transform；thumbnail/fixed cell 不泄漏到 editor/export |
| output | mixed-ratio selected output identity/metadata 原子更新；reflow/preserve/reject policy 明确 |
| measurement | frame/rendition revision 后 stale rect 不驱动 toolbar/panel；fresh rect 到达前 overlay policy 稳定 |
| editor | visible/intrinsic point round-trip 在 tolerance 内；border/content box、cover offsets、drift baseline 被计入 |
| history | passive measurement/metadata refresh/preview 零 semantic history；accepted frame/output command 最多一步 |
| source | portrait/square/video/mixed-output/resize 未取证时保持 gated，不以 Open Canvas 或 clone coincidence 代替 |

设计 authority：[`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)、`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` 和 `LIBTV-VR-023`。

---

## 16. 十三张卡的共同落地顺序

```text
01 浮层 screen rect 合同
  -> 02 AutoLink stable identity
  -> 04 派生/版本关系
  -> 03 运行、节点、保存状态
  -> 08 command outcome 与 feedback owner
  -> 06 framework change authority
  -> 09 selection、command context 与 focus owner
  -> 07 canvas lifecycle owner isolation
  -> 10 viewport、coordinate、gesture 与 placement owner
  -> 11 media ingress、asset/reference 与 resource lease
  -> 13 media/output/frame/rendition 与 measurement freshness
  -> 12 foreground editor session、local history 与 commit handoff
  -> 05 异步结果入口与陈旧收敛
```

这个顺序不是实现顺序，而是研究依赖：

- 浮层几何是当前已确认的高价值视觉缺口，且不依赖真实后端；
- AutoLink 的身份边界会影响后续引用、候选和派生节点的关系表达；
- 派生/版本关系明确后，才能设计长视频、重拍和过程型状态；
- 运行与保存状态先归纳语义，避免为尚未确认的源站操作预先制造状态机；
- command outcome/feedback 先分开 reason、domain effect 和 presentation，避免用 toast/string 补齐未知 workflow；
- framework callback 先限定 T0/T1，防止命名 graph command 被 generic reducer 旁路；
- selection/context/focus 再统一 active-session authority，避免快捷键和 surface close 穿透或回焦到陈旧 owner；
- canvas lifecycle 先固定 active/document/session owner，避免旧 callback 在新画布收敛；
- spatial authority 再把 actual host、live/stable viewport、gesture generation 和 entry placement 组合到既有 overlay/graph/lifecycle contracts；
- media ingress 随后固定 local bytes、asset/reference、cohort 和 release owner，避免用 URL 字段提前替代资源生命周期；
- media rendition 再固定 selected output、intrinsic metadata、node frame、surface fit 和 measurement freshness，避免编辑器在错误裁切面建立坐标；
- foreground editor session 随后固定 baseline/draft、native/local/graph undo、commit/cancel 和 close policy，避免局部编辑直接旁路 graph/async/media authority；
- 最后才设计 completion ingress，确保它复用已决定的身份、状态、graph 与 resource authority。

## 17. 统一拒绝清单

在后续“借鉴”中，以下做法默认禁止，除非有新的 LibTV 源站证据和用户编码授权：

- 把 Open Canvas 的视觉尺寸、间距、颜色、provider 文案或模型 slug 直接移植到 LibTV；
- 用一个固定 CSS offset 修复所有双浮层，而不检查 measured size、viewport 和选择生命周期；
- 把 AutoLink 的 mention、graph edge、reference role 合并为字符串或单一连接；
- 把 mock `running/success` 文案描述为真实任务后端；
- 把 Open Canvas 的 generic node patch、URL media identity 或 read-modify-write persistence 当成 stale-safe 模板；
- 把 React Flow union 的 add/remove/replace 当作无须 domain validation 的普通 transport；
- 因为 Open Canvas 使用 URL canvasId，就复制其列表页、route、final-delete 或持久化产品语义；
- 依赖 incidental React remount 清理所有 page-local transaction，或让 delayed callback late-read active canvas；
- 用 localized display string 充当 reason，或让 stale completion 在当前 canvas 发 success toast；
- 因为 Open Canvas 有 Sonner Toaster，就为普通 LibTV route 新增全局 toast 或复用 FrameOS toast；
- 把 React Flow selected flags、event target 或单个组件 Escape handler 当成完整 selection/context authority；
- 复制 Open Canvas conflict gate、默认 key propagation 或 Radix 组件树来替代 LibTV 自己的优先级与 focus-return 合同；
- 用 browser window 代替 actual React Flow host，或用 screen clamp 后的 surface position 回写 graph flow anchor；
- 把 Open Canvas Quick Add/drop/pending connection、zoom 范围、menu offset 或 viewport persistence 当成 LibTV 已证产品语义；
- 把 `File`、`Blob`、object URL、stable asset、generated-history item 和 node media reference 合并成一个 `url` 字段或共同 identity；
- 因为 Open Canvas 有 upload route/digest key，就移植其 MIME/size/storage/provider，或把 placeholder-first、sequential partial mutation 和 autosaved running state 当正确模板；
- 因为 Open Canvas 图片编辑器保留 40 个 snapshot，就按 entry count 复制 full-image history，而不设置 byte/pixel budget、gesture coalescing 和资源释放；
- 让 foreground editor 在 commit result 未确认或 async materialization 尚未接管 pending/failure surface 时先关闭，或只按 node ID 回写晚到结果；
- 让 enabled-looking Undo/Redo/Save/Generate 控件没有 handler，或用 graph undo 同时消费 editor-local chord；
- 把 request aspect、thumbnail dimensions、node frame、React Flow measured rect 和 full-media intrinsic dimensions 合并成一组 `width/height`，或把 cover/contain 当成未声明的全局视觉偏好；
- 因 serialized node 有 width/height 就添加 generic resize，或让 passive measurement/thumbnail swap 进入 semantic history；
- 在 cover-cropped node rect 上存 normalized marks 后把它们描述为 full-media coordinates，或在 mixed-ratio output switch 后静默复用旧 editor transform；
- 把 LibTV source 的上传、生成历史、风格/特效素材与 account asset 合并成一个“素材库”，或把 clone 历史文案反写成 source 事实；
- 在无后端 prototype 中把 local preview/fake materializer 宣称为 durable upload、synced asset 或 provider result；
- 因为 Open Canvas 支持复制子图，就擅自改变 LibTV 的派生节点/历史候选语义；
- 修改 LibTV 现有 edge flow effect、Handle 位置、FrameOS 独立 store 或源站未证实的移动端布局。

## 18. 后续研究入口

- LibTV 功能差距与优先级：[`LIBTV_FEATURE_GAP_MATRIX.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)
- LibTV UI 状态层级：[`LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)
- Open Canvas 到 LibTV 的转译：[`UIUX_TRANSLATION.md`](UIUX_TRANSLATION.md)
- Open Canvas 深度报告：[`REPORT.md`](REPORT.md)
- 异步结果入口与陈旧收敛：[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)
- React Flow change routing：[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)
- Multi-canvas lifecycle：[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)
- Command outcome/feedback：[`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)
- Selection/focus/command context：[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)
- Viewport/coordinate/gesture/placement：[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)
- Media ingress/resource lifecycle：[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)
- Editor session/commit/history：[`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)
- Media rendition/aspect/node geometry：[`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)
- 后续研究总计划：[`NEXT_RESEARCH_PLAN.md`](../liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md)

**本卡片集的结论：** Open Canvas 最值得借鉴的是可复核的边界和数据流，而不是“长得像画布”的视觉细节。LibTV 复刻继续以源站证据为准，Open Canvas 只负责帮助我们把已确认的问题拆成可验证、可撤销、可分层的工程合同。
