# LibTV UI/UX Parity Backlog

> 建档日期：2026-08-26。
> 稳定 clone 基线：Batch 48 closeout checkpoint；本批已从并行 WIP 升级为
> 有界历史合同。真实 mesh loading、远程同步和 LibTV 生产持久化仍不在合同内。
> 目的：面向后续 LibTV UI/UX 复刻，统一回答“当前真正还差什么、先研究什么、什么已可申请编码、怎样验证”。
> 本文是研究与排期文档，不授权修改 `src/`、测试脚本或共享源站状态。

## 1. Authority And Non-goals

本文聚合全路由当前差距，但不替代专项证据：

| 文档 | 继续负责 | 本文负责 |
|---|---|---|
| `liblib-live-2026-08-25/README.md` | 2026-08-25 页面壳、节点、入口和截图事实 | 不再承担当前排期权威。 |
| `LIBTV_FEATURE_GAP_MATRIX.md` | Seedance 五项主推能力的产品/状态缺口 | 将其中可执行项放入全局优先队列。 |
| `LIBTV_VERIFICATION_COVERAGE.md` | 图片、AutoLink、视频工作流的测试覆盖解释 | 只引用测试准备度，不复制完整断言。 |
| `TRACEABILITY_MATRIX.md` | 从主张反查源站/clone/Open Canvas 证据 | 给 gap 排价值、依赖和停止条件。 |
| `LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` | 当前 overlay state、mount owner、close/focus/anchor 行为 | 把运行时风险转成研究或实施队列。 |
| `LIBTV_GRAPH_TRANSACTION_CATALOG.md` | nodes/edges/selection/history 的实际副作用 | 判断某项能否作为独立、可撤销 slice。 |
| `LIBTV_RESEARCH_GO_NO_GO.md` | 编码授权和 fixture 总闸门 | 给每个 backlog item 指定具体闸门。 |

不在本文范围内：

- 将文章截图、Open Canvas 或 clone 当前行为提升为 LibTV 源站事实；
- 设计真实 Provider、上传、积分、计费、远端任务或账户持久化；
- 替 Batch 48 决定实现或修改其已收口的历史合同；
- 因为某项“高价值”就自动获得编码授权。

## 2. Status Vocabulary

| 状态 | 含义 | 当前允许动作 |
|---|---|---|
| `READY_FOR_AUTHORIZATION` | 源站合同和 clone delta 足够明确，可提出单 slice 编码申请 | 继续写计划/验收；没有授权仍不改代码。 |
| `DESIGN_FIRST` | 事实明确，但数据结构、history 或 ownership 设计尚需先落档 | 文档、纯 helper 合同、fixture 设计。 |
| `RESEARCH_FIRST` | 当前证据不足以决定源站一致行为 | 只读 DOM/bundle/截图复核；不猜实现。 |
| `BLOCKED_BY_FIXTURE` | 必须有可丢弃源站或本地状态才能继续 | 先定义 fixture，不操作共享项目。 |
| `PROTOTYPE_BOUNDARY` | 当前 local mock 是有意边界，不是待立即补后端的 bug | 只校正可见 UI/UX 和明确的本地反馈。 |
| `DEFERRED_ENGINEERING` | 有维护价值，但用户可见收益低于 fidelity 工作 | 保持记录，等待相关代码触发。 |
| `OUT_OF_SCOPE` | 不属于当前前端原型研究 | 需要新的产品/后端授权和合同。 |
| `PARALLEL_WIP` | 由其他开发者正在推进 | 只读、链接、避让，不覆盖。 |
| `RECORDED_PASS` | clone-owned 有界 slice 已完成实现和验证 | 读取其历史合同，不把结果升级为源站事实。 |

## 3. Scoring Method

每项使用四个 1-5 分维度。分数帮助排序，不替代证据和停止条件。

| 维度 | 1 | 5 |
|---|---|---|
| `V` 用户/产品价值 | 边缘维护 | 高频、首屏或产品识别核心 |
| `E` 证据成熟度 | 线索/推测 | 当前 DOM/bundle/多状态合同完整 |
| `T` 验证准备度 | 没有 fixture/selector | 可本地确定性验证且有历史脚本基础 |
| `R` 实施/副作用风险 | 局部只读 UI | graph/任务/持久化/跨组件数据模型 |

排序规则：先看用户价值和是否解锁后续工作，再看证据与验证准备度；高风险项即使高价值，也不会越过 fixture 或编码授权闸门。

## 4. Current Priority Queue

### 4.1 Summary

| Rank | ID | Slice | V | E | T | R | 状态 |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `LIBTV-PAR-001` | 当前图片标准双浮层的动作集合与几何 | 5 | 5 | 4 | 2 | `READY_FOR_AUTHORIZATION` |
| 2 | `LIBTV-PAR-002` | Preview/Annotate/Element Edit 的 L2 -> L3/L4 替换 | 5 | 5 | 3 | 3 | `READY_FOR_AUTHORIZATION` |
| 3 | `LIBTV-PAR-003` | Auto Link ghost + structured mention | 5 | 4 | 2 | 4 | `DESIGN_FIRST` |
| 4 | `LIBTV-PAR-004` | Top-level modal/Director 的 keyboard 与 focus ownership | 4 | 3 | 3 | 3 | `RESEARCH_FIRST` |
| 5 | `LIBTV-PAR-005` | 当前源站页面壳与主入口只读 freshness refresh | 4 | 3 | 5 | 1 | `RESEARCH_FIRST` |
| 6 | `LIBTV-PAR-006` | Ready-video 顶部处理工具条与 mode replacement | 5 | 3 | 2 | 4 | `BLOCKED_BY_FIXTURE` |
| 7 | `LIBTV-PAR-007` | 快捷键 source-only 命令与 help/handler 一致性 | 4 | 3 | 2 | 4 | `BLOCKED_BY_FIXTURE` |
| 8 | `LIBTV-PAR-008` | 普通画布 graph transaction 健壮性 | 4 | 5 | 3 | 4 | `DESIGN_FIRST` |
| 9 | `LIBTV-PAR-009` | 逐帧拉片/超长视频的真实过程与结果生命周期 | 4 | 3 | 2 | 5 | `BLOCKED_BY_FIXTURE` |
| 10 | `LIBTV-PAR-010` | Agent/Share/Toolbox/History/Upload 的 local mock 边界 | 3 | 4 | 4 | 3 | `PROTOTYPE_BOUNDARY` |
| 11 | `LIBTV-PAR-011` | `uiStore` 冗余/unmounted/unreachable 状态清理 | 2 | 5 | 4 | 2 | `DEFERRED_ENGINEERING` |
| 12 | `LIBTV-PAR-012` | Provider、上传、计费、远端任务、账户持久化 | 5 | 1 | 1 | 5 | `OUT_OF_SCOPE` |
| - | `LIBTV-PAR-013` | Batch 48 local model-library persistence | 4 | 4 | 4 | 4 | `RECORDED_PASS` |

### 4.2 `LIBTV-PAR-001`: current standard image state

**为什么排第一**

这是用户直接指出的高频识别态，也是所有图片 active tool 的入口基线。当前 source contract 已经足够精确，而 clone 仍停在历史版本。

| 项 | 当前结论 |
|---|---|
| `SOURCE_FACT` | toolbar 以 node screen center 为横向 anchor；host top 为 `nodeTop - 24 * zoom - 10` 后向上平移自身；当前 action set 为 9 个文字动作 + 4 个图标动作，已观察 `1092.5x49`。 |
| `CLONE_FACT` | `ImageToolbar` 使用 `NodeToolbar offset=16`、7 个文字动作和约 `900.5px` 固定宽；bottom panel 使用节点内 absolute + inverse zoom。 |
| 差距 | top action/order/width/formula 尚未升级；historical Batch 9 断言不能证明当前 source parity。 |
| 最小 slice | 只做 standard selected image；不顺手实现 active tools、Auto Link 或 backend。 |
| 验收 | 同 frame 读取 node/toolbar/panel/viewport；多 zoom center/gap；desktop/mobile；自然裁切；空选/多选卸载；graph count 不变。 |
| 停止条件 | 没有明确编码授权；或当前源站重新取证发现 action set/formula 已变。 |

主要证据：`LIBTV-TR-002..006`、`LibTVOverlayPositioning.contract.md`、`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`。

### 4.3 `LIBTV-PAR-002`: low-risk active surfaces

标准态之后，优先按一个 action 一个批次处理：

| 子项 | Source state | 最小 clone 目标 | 明确不包含 |
|---|---|---|---|
| Preview | page-level read-only overlay；关闭后回到原 selection | open/close/Escape、媒体比例、unchanged graph/selection | 下载、水印、会员逻辑 |
| Annotate empty | dedicated `536x49` toolbar + DPR canvas；standard bottom panel absent | empty enter/Escape/discard，恢复 standard L2 | 绘制保存、远端任务 |
| Element Edit empty | dedicated toolbar/stage/record panel；standard L2 absent | empty enter/Escape、disabled local history | 有效 record、生成结果 |

三个子项不能合成一个“通用图片弹窗”。Preview 属于 page L4；Annotate/Element Edit 属于 node authoring L3。旋转、图层分离和 dirty save 继续留在高风险 fixture 队列。

### 4.4 `LIBTV-PAR-003`: Auto Link

**当前状态**

- source 是全局偏好、connected/reference candidate pool、inline ghost、单项/全量接受和 structured mention；
- clone 是固定候选、独立 confirmation popover 和普通字符串前缀；
- graph edge、reference role、Prompt mention 和模型 ordinal 必须保持不同身份。

**先设计的原因**

它会同时触及 ImageEditPanel、VideoGenerationPanel、稳定 node ID、reference projection、keyboard/IME/race guard 和 transaction consistency。没有 typed token/candidate/session 合同就直接改 UI，会把旧固定 popover 扩大成更难迁移的数据债。

**设计输出闸门**

1. candidate、ghost、committed mention、reference role 的类型和 owner；
2. click/Tab/Shift+Tab/Escape/edit/blur/IME/stale result 状态图；
3. graph/reference/mention 成功与失败的原子边界；
4. 图片/视频共用什么，Provider 投影留在哪一层；
5. deterministic local fixture 和 replacement verifier。

### 4.5 `LIBTV-PAR-004`: page keyboard and focus ownership

当前 clone runtime 已证明：

- Character/History backdrop 阻断 pointer，但没有统一 focus trap 或 page shortcut boundary；
- Shortcuts 不是带 backdrop 的 modal；普通 button 上的 Delete/Tab/group 等仍会到 page handler；
- Director 只让 page Escape 提前返回，其他 global shortcuts 仍可能在 full-screen workspace 背后改变 overlay 或 graph；
- CanvasDropdown 的 local Escape 与 page Escape 可同时观察事件；active node tools 又有 capture-phase listener。

这既是 correctness 风险，也是 fidelity 未知。下一步先只读复核源站 modal、Agent、Share、Director 的 keyboard/outside/focus 行为，再决定 clone 应采用 source parity 还是显式可访问性改良。没有证据前不引入全局 modal manager。

### 4.6 `LIBTV-PAR-005`: source freshness refresh

2026-08-25 live audit 对 page shell、主入口和 10/11 graph 基线价值很高，但大量实现批次已在其后发生。下一次安全只读复核应回答：

1. 顶部导航、两个底栏、drawer 宽度和响应式隐藏规则是否变化；
2. top-level surface 的 outside/backdrop/Escape/focus 行为；
3. source 帮助面板、主入口 label/badge 和图片 action set 是否再次漂移；
4. 当前共享项目 node/edge/viewport 是否仍可作为 fixture；
5. 哪些旧 Batch screenshot 只剩 historical value。

允许动作仅限打开、选择、读取 DOM/computed style 和无副作用的 close/reopen。输入、上传、生成、保存、下载、任务提交和 graph mutation 继续禁止。

### 4.7 `LIBTV-PAR-006`: ready-video toolbar

当前 clone 已实现多个视频处理工具，但当前共享源站没有安全 ready-video fixture。需要先确认：

- ready 与 failed/pending 视频的 toolbar 分支；
- 当前 action order、hover menu、disabled/busy 和 active-tool replacement；
- reshoot/continue/subtitle/matting/picture-edit/depth 的互斥关系；
- Escape/discard/submit 后 selection、source/result 和 graph delta。

没有 disposable ready-video fixture 时保持 `BLOCKED_BY_FIXTURE`，不能用 clone 已有按钮顺序反推源站。

### 4.8 `LIBTV-PAR-007`: shortcut parity

优先复核：

```text
V label/active tool
L connection mode
Enter generate
Option+drag node/copy
Option+G storyboard merge
duplicate modifier and subgraph closure
```

这些 source-advertised 命令需要记录 precondition、focus、selection、cancel、graph/viewport/UI delta。它们不能由现有 Handle、局部 Enter 或普通 duplicate action“功能近似”代偿。

### 4.9 `LIBTV-PAR-008`: graph transaction hardening

这是 fidelity 工具的可靠性前置，不是视觉重构。当前 catalog 已记录：

- `setNodes`/`setEdges` 默认不记 history；
- `updateNodeData` 可产生 no-op history；
- graph snapshot 对 nested `data` 是浅复制；
- `addEdge` 缺少 duplicate/dangling/self-loop guard；
- 单节点 duplicate 与 selection duplicate 的 incident-edge 语义不同；
- selection 是 transaction output，但不是 history input；redo 清 selection；
- canvas lifecycle 不属于 graph undo。

后续必须先定义 guard、snapshot depth、selection policy 和 compatibility tests，再逐项改；不能借某个 UI slice 顺手重写整个 store。

### 4.10 `LIBTV-PAR-009`: process and result lifecycle

逐帧拉片、片段重拍和超长视频已经有有界 clone prototype，但 source 的处理中/失败/部分成功/重试/局部重算/版本替换仍不完整。进入实现前需要：

- disposable video/process fixture；
- source ID、media version、time range、operation、candidate/result identity；
- run/node/save status 分离；
- one transaction 的 node/edge/selection/history 期望；
- 不伪造真实 provider progress、费用或输出质量。

### 4.11 `LIBTV-PAR-010..013`: boundaries

| ID | 当前决策 |
|---|---|
| `010` | Agent/Share/Toolbox/History/AddNode resource action 继续使用显式 local feedback。只有源站可见结构/生命周期差距值得继续复刻；不把“按钮可点”升级成真实服务。 |
| `011` | 冗余 primary booleans、Notification/UserMenu unmounted state、`toggleGrid` 无 caller 已记录。等相关 store 获得编码授权或新入口证据时再清理。 |
| `012` | Provider、上传、计费、远端任务、账号和协作持久化需要新的产品/后端合同，当前不排入前端 parity 实施。 |
| `013` | Batch 48 已完成 browser-local model descriptor/persistence、focused verifier、截图台账和成熟度评估；真实 mesh loading、远程同步和 LibTV 生产持久化仍不在合同内。后续只读其历史合同，不把 clone-only 结果升级为源站事实。 |

## 5. Dependency Order

```text
source freshness refresh (PAR-005)
  -> top-level keyboard/focus decision (PAR-004)

standard selected image (PAR-001)
  -> low-risk active surfaces (PAR-002)
  -> high-risk image actions only after disposable fixture

typed identity/session design (PAR-003)
  -> Auto Link implementation

graph transaction guards (PAR-008)
  -> graph-mutating active tools/process results

disposable ready-video/process fixture
  -> PAR-006 / PAR-007 source-only commands / PAR-009
```

不要把 dependency order 误读成“大版本”。每个节点仍应形成一个可独立评审、验证、撤销的 batch。

## 6. Work Waves

### Wave A: research/documentation only

当前无需编码授权即可继续：

1. 按 `PAR-005` 对 page shell/top-level surface 做安全只读 freshness refresh；
2. 建立 disposable fixture catalog，列出 image/ready-video/process/shortcut 所需状态；
3. 给 historical/current verifier assertion 加版本标签和 replacement plan；
4. 为 `PAR-003` 写 typed Auto Link data/state/transaction design；
5. 将新的 source claim 追加到 traceability matrix，不静默改旧快照。

### Wave B: authorization-ready local slices

明确编码授权后优先：

1. `PAR-001` standard selected image；
2. `PAR-002` Preview；
3. `PAR-002` Annotate empty；
4. `PAR-002` Element Edit empty。

每项单独实施、单独 verifier、单独 screenshot ledger、单独 commit/push。

### Wave C: fixture-dependent

- ready-video toolbar/segment workflows；
- source-only shortcuts；
- shot-breakdown/long-video live lifecycle；
- rotate/layer separation/dirty save/download。

### Wave D: new product scope

- real Provider、upload、billing、account persistence、remote task polling；
- production model parsing/assets/licenses beyond the bounded Director plans。

## 7. Batch Entry Template

后续 agent 从本文选一个 item 时，先落下：

```text
Backlog ID:
User-visible goal:
Source fact and date:
Clone fact and stable commit:
Exact delta:
Out of scope:
Route/store/components:
Graph/selection/history delta:
Fixture and reset method:
Desktop/mobile/zoom states:
Selectors and assertions:
Source/clone evidence outputs:
Authorization status:
Stop conditions:
```

任何字段为空时保持 research/plan，不开始编码。

## 8. Completion Rules

一个 backlog item 只能在以下条件同时满足时标记 parity slice complete：

1. source fact、inference 和 clone decision 分开；
2. 当前 delta 在稳定 commit 上重新确认；
3. 明确 graph/viewport/selection/local-state 副作用；
4. desktop/mobile 和必要 zoom/edge-clipping 状态有断言；
5. focused verifier、console/page/request error checks 和 repository gate 有记录；
6. implementation/screenshot history 落档；
7. commit 已 push；
8. 没有把 local mock 或 bounded proxy 误写成真实后端/source 完成度。

“已经有按钮”“历史 Batch 曾通过”“截图看起来接近”都不能单独满足完成条件。

## 9. Maintenance

发生以下事件时更新本文：

- 新源站日期改变 action、geometry、lifecycle 或 fixture 可用性；
- clone slice 获得授权、实施、验证或被 supersede；
- verifier 从 historical compatibility 升级为 current source contract；
- graph/overlay/shortcut catalog 暴露新的跨组件风险；
- parallel WIP 稳定或边界前移。

本表只保留当前优先级。旧优先级变化应在 Changelog/实施记录/Documentation Audit 中保留原因，不复制一份新的“最终 backlog”。

## 10. Related Documents

- [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)
- [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)
- [`liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)
- [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)
- [`components/LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md)
