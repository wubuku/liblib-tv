# LibTV Fixture Catalog

> 目的：为后续 LibTV UI/UX 研究、复刻和回归提供统一的 fixture 身份、构造、隔离、reset 和副作用合同。
>
> 本文来自 2026-08-26 对 `canvasStore`、`page.tsx`、Batch 4-48 verifier、当前源站研究边界和 Batch 48 clone-owned local model workflow 的只读审计。本文不授权修改代码、测试、截图或源站项目。
>
> 选择复刻 slice 时先读 [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)；判断是否允许操作时再读 [`liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)。

## 1. 结论

当前仓库不是“缺少所有 fixture”，而是混有五类性质不同的状态：

1. `canvas-2` 是源码内置的 source-shaped demo baseline；
2. `canvas-1` 是本地空画布，现有 Batch 24-33 主要通过真实 UI 在这里构造确定性状态；
3. graph 结果态由 store transaction 派生，不是远端任务结果；
4. Director verifier 可通过 `window.__director_store` 直接驱动 domain state，Batch 48 还引入 browser-local persistence；
5. 当前登录态源站项目只是共享的只读观察对象，不是可重置测试 fixture。

因此，后续 agent 不应再笼统写“使用 disposable fixture”。必须引用本文的 fixture ID，或者新增一个包含 owner、构造、reset 和禁止动作的 ID。

## 2. 状态词表

| 状态 | 含义 | 是否可直接用于后续本地回归 |
|---|---|---|
| `AVAILABLE_BASELINE` | 源码加载即存在，节点 ID 和初始 graph 可静态审计 | 可以，但必须先断言 baseline 未漂移 |
| `UI_CONSTRUCTED` | 在新 Page 中通过产品 UI 从空画布构造 | 可以；优先于测试直接写 store |
| `TRANSACTION_DERIVED` | 通过 store action/UI command 由基础节点生成 | 可以；必须断言 graph/history delta |
| `DIRECT_STORE_DRIVEN` | verifier 经公开到 `window` 的 Director store 读取或驱动 | 仅用于 Director 专项合同 |
| `SHARED_READ_ONLY` | 登录态共享源站，只允许无副作用观察 | 只能取证，不能作可重复回归 fixture |
| `REQUIRED_DISPOSABLE` | 所需状态尚不存在，必须另建可丢弃本地或源站对象 | 不可以；保持 `BLOCKED_BY_FIXTURE` |
| `PARALLEL_WIP` | 其他开发者正在修改 fixture、持久化或 verifier | 只读避让，稳定后再登记 |
| `OUT_OF_SCOPE` | 需要真实 Provider、计费、账号或远端任务系统 | 当前前端原型不建设 |

这些词描述 fixture 本身。验证成熟度仍使用 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的 `SCRIPT_AVAILABLE`、`SOURCE_CONTRACT_ONLY` 等状态，两套词不能互换。

## 3. 运行时隔离事实

### 3.1 普通 LibTV 画布

`useCanvasStore` 是模块内 Zustand store，当前没有 `persist` middleware，也没有把 store 暴露为 `window.__canvas_store`。初始值直接定义在 `src/store/canvasStore.ts`：

```text
projectName: 未命名项目
canvases: canvas-1(empty), canvas-2(source-shaped demo)
activeCanvasId: canvas-2
selection: empty
historyByCanvas: empty
```

现有普通 LibTV verifier 的实际隔离方式是：

```text
browser.new_page()
  -> page.goto(local clone)
  -> 新文档重新建立模块内 store
  -> 需要空态时从 UI 切到 canvas-1
  -> 从 Add Node 等真实入口构造状态
  -> 在该 Page 内完成断言
  -> Page 被丢弃
```

普通 Batch 脚本中的 `page.evaluate` 主要读取 DOM overflow 或执行 `element.click()`，不是统一的 canvas fixture 注入器。后续不能声称仓库已有通用 `setState` fixture API。

### 3.2 新 Page、reload、切换 canvas 不是同一 reset 等级

| 操作 | 能恢复的内容 | 不能作为默认承诺的内容 |
|---|---|---|
| 新建 Playwright Page 后 `goto` | 普通 canvas/ui 模块内初始状态；最接近现有脚本合同 | 同一 BrowserContext 的 local/session storage、认证 cookie |
| reload 当前 Page | 理论上会重建当前文档和普通内存 store | 现有脚本没有把它作为统一 reset 原语；必须重新断言 graph/selection/history |
| 切到 `canvas-1` | 得到源码初始空 graph，selection 被清空 | 若同一 Page 之前已经修改过 `canvas-1`，不会恢复；其他 canvas/history/UI state 也不会清零 |
| undo | 最近一次有 history 记录的 graph snapshot | viewport、canvas CRUD、project name、UI store、selection、远端副作用 |
| Escape/空白点击 | selection 或局部 overlay，取决于 surface | graph、history、媒体版本和持久化数据 |

结论：普通本地行为测试以“每个独立场景使用新 Page”为强 reset；在同一 Page 复用 `canvas-1` 前必须显式证明它仍是 `0 nodes / 0 edges`。

### 3.3 History 不是 fixture reset 系统

当前 graph snapshot 只克隆 node 顶层、`position`、`style` 和一层 `data`，nested `data` 仍是浅边界。另有以下事实：

- `setNodes`/`setEdges` 默认不记录 history；
- `updateNodeData` 会记录 history，但可能产生 no-op snapshot；
- undo/redo 恢复 graph 后清空 selection；
- viewport 不属于 graph history；
- canvas add/remove/rename/duplicate 不属于 graph undo；
- Director 有独立 store/history，不能用 canvas undo 清理。

所以 fixture teardown 不得只写“最后按 Cmd+Z”。Undo/redo 可以是被测合同，也可以验证 transaction 原子性，但不能替代新 Page reset。

### 3.4 Director 是另一套 fixture 域

Batch 35-48 的 Director verifier 可以读取或调用 `window.__director_store.getState()`。这是 Director 专项测试入口，不是普通 LibTV graph 的通用注入规范。

Batch 48 新增了 browser-local model-library storage。它已有完整 workflow、
稳定 verifier、截图台账和成熟度记录，但只定义了 clone-owned prototype
边界：

- 测试必须显式清理
  `liblib-tv-director-local-model-library-v1`，不能把“新 Page”误认为足以
  清理同一 BrowserContext 的 persistence；
- import 应通过多个合法 `.fbx`/`.obj` 文件和真实 UI input 构造；
- descriptor 恢复应在 fresh Page/context 中重新断言；
- 不把 localStorage descriptor 或 proxy object 升级为真实 LibTV 生产资产合同。

### 3.5 Director local-model fixture reset

Batch 48 的最小可重复 setup/teardown：

```text
new BrowserContext
  -> new Page
  -> goto clone
  -> localStorage.removeItem("liblib-tv-director-local-model-library-v1")
  -> open Director
  -> import via [data-director-model-library-local-input]
  -> assert localStorage/card/scene state
  -> remove final local card
  -> assert storage === []
  -> discard context
```

固定断言：

- 初始 `我的模型` 是空态，input `multiple` 且接受 `.fbx,.obj`；
- 非法扩展名不产生 card 或 browser error；
- persistence 只包含 `DirectorLocalModelLibraryItem` 的 bounded fields；
- fresh context 能恢复卡片；
- 删除资产会删除全部关联 local proxy object、timeline track 和 motion path；
- 最后一张卡删除后 storage 为空并回到 empty state。

## 4. 当前可用本地 Fixture

### 4.1 总表

| Fixture ID | 状态 | 构造/owner | 初始关键状态 | 主要用途 |
|---|---|---|---|---|
| `LIBTV-FIX-LOCAL-DEMO-01` | `AVAILABLE_BASELINE` | `canvasStore.initialCanvas2` | `canvas-2`，10 nodes / 11 edges，source-shaped viewport | 历史图片/视频浮层、分组、整理、asset/tree、baseline topology |
| `LIBTV-FIX-LOCAL-EMPTY-01` | `AVAILABLE_BASELINE` | `defaultCanvas("canvas-1")` | 0 nodes / 0 edges / zoom 1 | 隔离构造单节点、派生 graph 和响应式场景 |
| `LIBTV-FIX-LOCAL-IMAGE-01` | `UI_CONSTRUCTED` | 在空画布从 Add Node 添加图片 | 本地图片、`editorVariant=empty`、selected | 标准图片浮层、Preview/Annotate/Element Edit 的低风险本地状态 |
| `LIBTV-FIX-LOCAL-VIDEO-READY-01` | `UI_CONSTRUCTED` | 在空画布从 Add Node 添加视频 | `status=ready`、30s、1280x720、Seedance 2.5、selected | Batch 23、26-33 视频入口和本地处理动作 |
| `LIBTV-FIX-LOCAL-IMAGE-VARIANTS-01` | `AVAILABLE_BASELINE` | `canvas-2` 五个图片节点 | empty、prompt、referenced 三类 editor state | 历史 Batch 9/10 panel 高度与内容状态 |
| `LIBTV-FIX-LOCAL-GROUP-01` | `AVAILABLE_BASELINE` | `canvas-2` 两个 storyboard groups | image group、video parent-child group | group/ungroup、parent-child、organize 和 subgraph 研究 |
| `LIBTV-FIX-LOCAL-DERIVED-01` | `TRANSACTION_DERIVED` | UI/store 的 derived actions | 动态 node/edge ID、atomic history 视 action 而定 | continuation、subtitle、audio、frame、matting、picture/depth edit |
| `LIBTV-FIX-LOCAL-LONG-PROCESS-01` | `TRANSACTION_DERIVED` | ready video 切 long-video 后提交 | 1 source + 12 process nodes / 22 edges；process status `pending` | 本地超长视频 process topology、重复提交、undo/redo |
| `LIBTV-FIX-DIRECTOR-BASE-01` | `DIRECT_STORE_DRIVEN` | Director store + Batch 35-48 setup | scene/object/camera/timeline domain state | Director 专项视觉、轨道、路径、拍摄、导出和 model-library proxy |
| `LIBTV-FIX-DIRECTOR-LOCAL-MODEL-01` | `UI_CONSTRUCTED` | Batch 48 verifier + local input | fresh context + cleared clone-owned storage | local descriptor import/persistence, refresh recovery, proxy re-add and cleanup |

### 4.2 `LIBTV-FIX-LOCAL-DEMO-01`

稳定源码身份：

```text
canvas: canvas-2 / 画布 2
viewport: x=-583.8, y=260.8, zoom=0.526
nodes: 10
edges: 11
```

关键节点：

| ID | 类型/状态 | 可支持的研究 |
|---|---|---|
| `i-1FQ9tErTcC` | image / empty editor | 标准图片节点和资产入口 |
| `i-dnwoZQ7jsG` | image / prompt | Prompt 面板和图片内容态 |
| `i-YDfWhFlthe` | image / referenced | 引用缩略图、较高 panel、历史 overlay geometry |
| `v-UGQZzZOpbv` | video / `failed` / group child | failed 分支、parent-child；**不是 ready-video fixture** |
| `g-245IDFh8sB` | image storyboard group | organize/group topology |
| `g-EFbbHpwq5w` | video group | parent-child 和 cascade behavior |

使用规则：

- 脚本开始先断言目标 ID 和 10/11 baseline，避免源码演示数据漂移后出现误判；
- 测试若移动、分组、复制、删除或派生节点，应在独立 Page 完成；
- 历史 Batch 9/10 可继续使用这些 ID，但其 toolbar/AutoLink 断言仍是 dated clone contract；
- 不能把源码 demo 的节点位置、文案或 failed video 当作当前源站事实。

### 4.3 `LIBTV-FIX-LOCAL-EMPTY-01`

构造步骤：

```text
new Page -> goto / -> open canvas dropdown -> select canvas-1
         -> assert 0 nodes / 0 edges
```

它是目前最可靠的普通 LibTV fixture substrate。Batch 24-33 中多个脚本使用这一模式。适合每个场景只构造一个 source node，再观察明确的 graph delta。

限制：`canvas-1` 不是特殊的自动清理空间；它只在新 store 实例中初始为空。同一 Page 一旦写入，后续切走再切回仍会保留内容。

### 4.4 `LIBTV-FIX-LOCAL-IMAGE-01`

从空画布点击“添加节点 -> 图片”得到：

- node shell 默认 `512 x 288`；
- data 中媒体尺寸默认 `512 x 512`；
- 本地图片 URL 和 watermark URL；
- `editorVariant=empty`、`editorHeight=191`；
- 新节点自动成为单选 selection；
- add-node transaction 进入 canvas history。

node shell 比例和媒体 data 比例不同是当前 clone 事实，不能被文档静默抹平。几何测试应明确自己使用 measured node rect 还是媒体 metadata。

### 4.5 `LIBTV-FIX-LOCAL-VIDEO-READY-01`

从空画布点击“添加节点 -> 视频”得到：

```text
filename: 视频节点 5-片段重拍
status: ready
durationSeconds: 30
resolution: 1280 x 720
posterUrl: local image
model: Seedance 2.5
```

这解释了为何 Batch 23、26-33 能验证 clone 的 ready-video 工具，而 `canvas-2` 的既有视频仍是 `failed`。该 fixture 只证明 clone 分支；它不能推出源站 ready toolbar 的动作顺序、菜单、状态或结果版本语义。

### 4.6 `LIBTV-FIX-LOCAL-DERIVED-01`

现有 derived transaction 常见模式是：

```text
ready source
  -> open one active tool/menu
  -> submit local mock action
  -> create target node(s) + direct source/result edges
  -> update selection or keep source selection according to action
  -> record one graph snapshot
  -> assert undo/redo atomically removes/restores the graph delta
```

动态 ID 通常包含时间或随机后缀。测试应从 selected node、`data-*` metadata 或 source/target edge 关系获取 ID，不能硬编码本次运行生成的 ID。

`LIBTV-FIX-LOCAL-LONG-PROCESS-01` 是其规模最大的现有例子：一次提交增加 12 个 process nodes 和 22 条 edges；加上 source 后页面总量为 13 nodes / 22 edges。所有 process 节点当前都是 bounded mock 的 `pending`，不是后台任务快照。

## 5. 源站观察对象

### 5.1 `LIBTV-FIX-SOURCE-SHARED-01`

| 字段 | 当前合同 |
|---|---|
| URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| 状态 | `SHARED_READ_ONLY` |
| Owner | 用户共享的登录态研究项目；不是 agent 独占 disposable project |
| Reset | 未知；不得假设 source undo、reload 或关闭页面能消除远端副作用 |
| 用途 | DOM、computed style、screen rect、可见文案、bundle、无副作用 surface lifecycle 取证 |

允许的动作：

- 打开/切换只读页面区域；
- 选择已有节点并读取可见工具条、面板、DOM 和 computed rect；
- 打开后关闭不写入的菜单、帮助、预览或 drawer；
- 截图和记录当前日期、viewport、zoom、selection 和已知 fixture 状态；
- 在已有文档不足时读取 bundle 字符串，但把 bundle-only 结论标为 inference/contract evidence。

禁止的动作：

- 输入或提交 Prompt、接受 AutoLink 候选；
- 新增、移动、连接、复制、分组或删除 graph 对象；
- 上传、生成、重拍、续写、标注保存、旋转提交、图层分离；
- 切换可能持久化的全局偏好；
- 下载、消耗积分、启动任务、覆盖媒体版本；
- 用一次 source undo 作为“已清理”的充分证据。

共享源站可以回答“当前看见什么”，不能满足“每次回到相同 graph、viewport、selection、media version”的 fixture 定义。

## 6. 必须另备的 Disposable Fixture

| Fixture ID | 环境 | 最小状态 | 允许研究后应观察 | 当前状态 |
|---|---|---|---|---|
| `LIBTV-FIX-SOURCE-IMAGE-DIRTY-01` | 独立源站项目 | 可编辑图片、已知 graph/version、允许保存/撤销 | rotate/layer/annotate 的 task、graph、version、save/undo boundary | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-AUTOLINK-01` | 独立源站项目 | 至少两个 connected/reference candidates、可输入 Prompt | ghost、Tab/Shift+Tab/Escape/IME、single/all accept、mention identity | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-VIDEO-READY-01` | 独立源站项目 | 可播放 ready video、已知 duration/version、允许打开工具 | toolbar order、hover menu、active replacement、discard/submit delta | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-SHORTCUT-01` | 独立源站项目 | 可丢弃 subgraph、group、internal/external edges | `L`、Enter、Option-drag、Option+G、duplicate closure 和 cancel | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-SOURCE-PROCESS-01` | 独立源站项目 | 可观察 pending/failed/partial/success/retry 的任务或已授权 mock | run/node/save status、candidate/result version、局部重算和替换 | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-LOCAL-AUTOLINK-01` | clone | typed candidates/ghost/mention/session 和可控延迟 | keyboard/IME/stale-result/transaction consistency | `REQUIRED_DISPOSABLE` / `DESIGN_FIRST` |
| `LIBTV-FIX-LOCAL-PROCESS-STATES-01` | clone | 固定 pending/failed/partial/success/retry data | UI lifecycle、graph delta、selection、undo/redo | `REQUIRED_DISPOSABLE` |
| `LIBTV-FIX-LOCAL-SHORTCUT-01` | clone | 固定 node/group/internal/external-edge subgraph | handler precondition、focus guard、graph closure、history | `REQUIRED_DISPOSABLE` |

### 6.1 源站 disposable fixture 的接收条件

开始任何写入型源站研究前，必须同时记录：

1. fixture owner 和独立 project/space 身份；
2. 允许的动作、积分/任务消耗上限和停止条件；
3. 初始 graph、node IDs、media version、duration/time range；
4. 每一步预期观测量和截图/DOM 输出路径；
5. 远端清理方式，以及谁确认没有遗留任务或版本；
6. 失败、中断、登录过期或 API 不可用时不继续试探的条件。

缺任一项，状态保持 `BLOCKED_BY_FIXTURE`。

### 6.2 本地 disposable fixture 的接收条件

本地 fixture 不等于随便写一组 demo data。它至少需要：

- deterministic ID 或稳定的 identity 查询方式；
- 明确 node/edge/selection/viewport/history 初始值；
- 区分 source ID、media version、operation、run、candidate 和 result；
- 不依赖真实网络、登录、Provider 或当前日期；
- 每个测试新 Page，或显式 setup/teardown 后断言完全复位；
- source fact、clone mock 和测试控制字段分开命名；
- 实施授权后才允许新增代码/测试 fixture。

## 7. Parity Backlog 映射

| Backlog | 最小 fixture | 当前可做 | 当前缺口/停止条件 |
|---|---|---|---|
| `LIBTV-PAR-001` | `LOCAL-DEMO-01` 或 `LOCAL-IMAGE-01` + `SOURCE-SHARED-01` | 合同/计划已足够；可继续只读 freshness | 编码和 replacement verifier 等待明确授权 |
| `LIBTV-PAR-002` | `LOCAL-IMAGE-01` + `SOURCE-SHARED-01` | Preview/Annotate/Element Edit 空态可规划 | dirty annotate/rotate/layer 需要 `SOURCE-IMAGE-DIRTY-01` |
| `LIBTV-PAR-003` | `LOCAL-AUTOLINK-01` + `SOURCE-AUTOLINK-01` | typed data/state/transaction design | 没有设计合同和 disposable source 时不编码、不输入共享 Prompt |
| `LIBTV-PAR-004` | 本地 page overlay states + `DIRECTOR-BASE-01` + `SOURCE-SHARED-01` | 可只读研究 keyboard/outside/focus | 不凭可访问性常识猜 source parity，不顺手建 modal manager |
| `LIBTV-PAR-005` | `SOURCE-SHARED-01` | 安全只读 page-shell freshness refresh | 不能修改共享 graph 或偏好；观察结果要带日期 |
| `LIBTV-PAR-006` | `LOCAL-VIDEO-READY-01` + `SOURCE-VIDEO-READY-01` | clone 侧历史工具回归可读 | source toolbar 继续 `BLOCKED_BY_FIXTURE` |
| `LIBTV-PAR-007` | `LOCAL-SHORTCUT-01` + `SOURCE-SHORTCUT-01` | 现有 help/handler crosswalk 可继续完善 | source-only 命令不得在共享 graph 试探 |
| `LIBTV-PAR-008` | `LOCAL-DEMO-01`、`LOCAL-EMPTY-01`、`LOCAL-DERIVED-01` | 可继续设计 guard/snapshot/selection compatibility cases | 修改 store 仍需授权；不要用 source fixture |
| `LIBTV-PAR-009` | `LOCAL-LONG-PROCESS-01`、`LOCAL-PROCESS-STATES-01`、`SOURCE-PROCESS-01` | 当前可记录 bounded mock topology | 真实 lifecycle/局部重算继续被 fixture 和业务接口阻塞 |
| `LIBTV-PAR-010` | `LOCAL-DEMO-01` | 显式 local mock boundary 已可验证 | 不升级为真实服务承诺 |
| `LIBTV-PAR-011` | 静态 store/runtime 审计 | 文档已有冗余/unmounted state 清单 | 没有编码授权不清理 store |
| `LIBTV-PAR-012` | 无 | 记录 scope boundary | Provider/计费/远端持久化是 `OUT_OF_SCOPE` |
| `LIBTV-PAR-013` | `DIRECTOR-LOCAL-MODEL-01` | Batch 48 已形成 recorded pass；读取其稳定 verifier 和 reset 合同 | 不把 local descriptor/proxy 升级为真实资产或远端持久化 |

表内简称省略了 `LIBTV-FIX-` 前缀。

## 8. Verifier 使用规则

### 8.1 新场景优先顺序

```text
pure helper/data contract
  -> new Page + existing baseline
  -> empty canvas + real UI construction
  -> transaction-derived state
  -> direct store driving only when domain contract already exposes it
  -> source observation kept in a separate research script/run
```

不要先增加全局 fixture injector。只有多个授权 slice 确实重复同一套复杂 setup，且真实 UI 构造导致不稳定或无法表达失败态时，才评审测试 helper 或 fixture factory。

### 8.2 每个 verifier 的最小前置断言

- 当前 URL、viewport 和目标 canvas；
- 初始 node/edge 数量；
- 目标 node identity、type 和关键 status；
- selection 初态；
- history 若为被测对象，先证明 past/future 起点；
- active overlay/tool 未被前一场景遗留；
- 对 localStorage 有依赖时，显式记录 key 和清理验证；
- console error、page error 和必要 request error collection 已安装。

### 8.3 有 graph mutation 的最小后置断言

- 精确 node/edge delta，而不只断言“出现了卡片”；
- 新节点的 source/result/version/operation metadata；
- selection output；
- undo 一次是否完整移除本 transaction；
- redo 一次是否恢复同一 identity/metadata 或合同允许的新 identity；
- viewport/overlay 是否按合同保留或关闭；
- 最后丢弃 Page，不把场景状态交给下一项测试。

### 8.4 串行执行

现有 Batch verifier 共用本地 dev server，并会覆盖带固定日期文件名的视觉参考；因此继续串行运行。文档-only 工作不自动运行这些脚本，以免触碰共享截图 WIP。

## 9. Fixture 记录模板

新增 fixture 时复制以下字段到 PLAN 或本文：

```text
Fixture ID:
Environment: local clone / disposable source / shared source / Director
Owner:
Purpose and parity IDs:
Construction path:
Stable identities:
Initial graph/selection/viewport/history:
Media/run/version state:
Allowed actions:
Forbidden actions:
Expected graph/UI/storage side effects:
Reset method:
Reset assertions:
Evidence output paths:
Authorization status:
Stop conditions:
Supersedes:
```

不得用“刷新即可”“可撤销”“测试数据”替代 reset method 和 reset assertions。

## 10. 下一步文档/研究顺序

1. 用本文完成 `PAR-005` source freshness refresh 的观察 checklist，不操作共享 graph；
2. 为 `PAR-003` 落 typed AutoLink fixture/data/state/transaction design；
3. 为 `PAR-007` 设计 local shortcut subgraph，不修改实现；
4. 等用户提供独立源站 project/权限后，再登记 `SOURCE-VIDEO-READY-01` 等真实 fixture identity；
5. 继续维护 `DIRECTOR-LOCAL-MODEL-01` 的 storage reset、fresh-context 和 proxy-cleanup 断言；
6. 获得编码授权后，每个 parity slice 单独新增 fixture、verifier、screenshot ledger、implementation 和 commit。

## 11. Maintenance

以下事件必须更新本文：

- `initialCanvas2` 节点/边/ID/viewport 改变；
- default image/video data 或 Add Node 构造路径改变；
- canvas store 获得 persistence、window debug API 或正式 reset action；
- history snapshot 深度或 selection/viewport policy 改变；
- Director 新增/移除 browser persistence；
- disposable source fixture 获得 owner、权限或被销毁；
- parity backlog item 的 fixture 状态从 blocked 升级为 available；
- verifier 改用新的 setup/teardown 策略。

维护时同时检查 [`HARNESS.md`](../HARNESS.md)、[`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)、[`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md) 和对应 Batch 实施记录。
