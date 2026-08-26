# LibTV Graph Compatibility 静态审计

> 审计批次：`OC-EQ-003` / 2026-08-27
> 研究边界：LibTV 共享登录态项目的 DOM、已加载生产 bundle 和当前已有 graph 的只读分析
> 结论等级：`SOURCE_STATIC_EVIDENCE`；不是一次可丢弃项目上的连接交互验收

## 1. 目的

Open Canvas 的 graph 校验实现把几个容易被 clone 混为一谈的问题分开处理：端点存在性、连接方向、重复边、类型兼容、DAG 和提交后的原子性。本次审计回到 LibTV 当前生产前端，确认它是否也有这些边界，以及这些规则是否落在 React Flow `Handle`、画布连接回调还是领域模型校验中。

本报告只回答 `LIBTV-GI-004..007` 的静态部分：

| ID | 问题 | 本轮目标 |
|---|---|---|
| `LIBTV-GI-004` | exact duplicate / parallel edge identity | 检查连接校验是否比较节点对，是否比较 Handle |
| `LIBTV-GI-005` | self-loop | 检查普通连接和 programmatic connection 是否显式拒绝自身连接 |
| `LIBTV-GI-006` | directed cycle | 检查当前连接路径是否有有向环检测 |
| `LIBTV-GI-007` | Handle / node-type compatibility | 检查 Handle 方向归一化、node action/type matrix 和目标容量校验 |

## 2. 证据坐标与安全边界

| 项目 | 值 |
|---|---|
| Source URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| Page title | `未命名项目 - 画布 2 - LibTV - 专业视频创作工具` |
| 观测时间 | 2026-08-27（Asia/Shanghai；浏览器内部时间为 `2026-08-26T19:09:03.772Z`） |
| Browser viewport | `929x874 CSS px`，`devicePixelRatio=2` |
| Canvas transform | `translate(12.4578px, 200.864px) scale(0.282798)`，约 28% fit view |
| 当前 graph | 13 个可见 node DOM，12 个 edge DOM |
| Bundle | 当前页面已加载的 Next/Turbopack production chunks；关键逻辑见 `0jf40wzwc66-8.js` 和 `2axsluxmmf6m6.js` |
| 已执行动作 | 读取已有 DOM、ARIA、computed style、已加载脚本资源并在本地临时目录解压/AST 检索 |
| 明确未执行 | 拖动 Handle、创建/删除/重连 edge、创建 node、输入、生成、上传、重试、保存、下载、切换模型或修改参数 |

共享项目是 `SHARED_READ_ONLY`。当前静态审计没有改变 graph、selection 以外的页面状态，也没有写入仓库代码、verifier 或 submodule。

## 3. 当前 DOM 事实

### 3.1 Handle 不是“只有一端可拖”的单向 UI

所有可见 node 都渲染了左侧 `target` 和右侧 `source` Handle。当前 DOM 中，两类 Handle 都带有 React Flow 的 `connectablestart` 和 `connectableend` class；当某个 node instance 的一侧不可用时，源站还会移除 `connectable`、`connectionindicator` 并将 `pointer-events` 设为 `none`。

| node DOM type | 可见数量 | target 典型状态 | source 典型状态 | 观测解释 |
|---|---:|---|---|---|
| `image` | 6 | 有的 `connectable`，有的不可连接 | `connectable` | image 的当前数据/角色会影响 target；不是单纯按 node type 固定 |
| `video` | 1 | `connectable` | `connectable` | 普通失败视频实例两端都可见且可交互 |
| `video-clip` | 1 | `connectable` | `connectable` | clip 节点两端都可见 |
| `script-v2` | 1 | `connectable` | `connectable` | typed compatibility 不能由 Handle class 单独推出 |
| `group` | 2 | `connectable` | `connectable` | group 仍参与连接，但 storyboard 语义另有 guard |
| `shot-breakdown` | 1 | `connectable` | 不可连接 | 该实例当前只有接收方向的有效 affordance |
| `text` | 1 | 不可连接 | `connectable` | 该实例当前只有输出方向的有效 affordance |

关键边界：`connectablestart` / `connectableend` 是 React Flow 的交互 class，不等于业务层允许连接。真正结果由 `isValidConnection` 和 `onConnect` 回调决定。相反，`connectable=false` 的 DOM 状态是当前实例已经被 UI 预先收窄的信号，但也不能替代业务校验。

### 3.2 已有 graph 的 edge identity

edge DOM 使用 `data-id`，ARIA label 直接暴露规范化后的端点，例如 `Edge from i-1FQ9tErTcC to b-bTLLuU4w5q`。本次读取到的 12 条边没有 exact duplicate、反向 parallel pair 或 self-loop；从现有边表运行 DFS 也没有发现 directed cycle。

这只能说明当前保存的 graph 样本没有这些结构，不能说明源站允许或拒绝它们。正负行为需要一次可 reset 的 source fixture 才能交互确认。

## 4. 生产 bundle 静态事实

### 4.1 画布连接回调的职责

关键画布 chunk `0jf40wzwc66-8.js` 中，画布组件同时挂载：

- `onConnectStart`：记录发起 node ID 和 `handleType`；
- `isValidConnection`：执行连接前的只读校验，并写入 invalid-target UI 状态；
- `onConnect`：仅在校验通过后调用 `addEdge`，并处理连接后的 node data/model 切换；
- `onConnectEnd`：对无目标或无效目标做清理，并尝试基于光标位置识别可连接节点；
- `tryProgrammaticConnectNodePair`：沿用同一套 validator，再提交结构化 edge。

这说明连接不是“Handle 直接写入 edge”。Handle 提供输入，画布连接层负责归一化、验证和提交。

### 4.2 方向归一化

`onConnect` 对从 `target` Handle 开始的拖拽做反向归一化：

```text
if sourceHandle == "target":
    normalized = {
        source: event.target,
        sourceHandle: "source",
        target: event.source,
        targetHandle: "target"
    }
else:
    normalized = event
```

因此 DOM 中允许两侧 Handle 成为连接起点，并不意味着 edge 会保留用户拖拽的视觉起点。最终 graph 仍使用规范的 `source -> target`。

### 4.3 duplicate / reverse-pair guard

`isValidConnection` 在进入领域兼容性前检查当前 edges：

```text
reject if existing.source == candidate.source
          and existing.target == candidate.target
       or existing.source == candidate.target
          and existing.target == candidate.source
```

该条件没有比较 `sourceHandle` 或 `targetHandle`。因此，在当前普通画布连接路径上，**相同节点对的同向重复边、反向边以及仅改变 Handle 的 parallel edge 都会在静态逻辑上被同一个 guard 覆盖**。这是比“exact duplicate identity 包含 handles”更窄、更强的 source signal。

但 `addEdge` store action、后端同步回流、导入和其他批量入口是否都复用这个 guard，本轮没有替换/触发验证。因此 `GI-004` 仍不能关闭为完整 source contract。

### 4.4 self-loop 与 cycle guard

画布 validator 先建立现有 edge 的 adjacency map，再把候选 edge 加入 map，随后运行递归 DFS：如果从候选 `source` 可再次到达当前 DFS 路径，则返回 invalid。

这带来两个直接结论：

1. 普通 node source 的 `A -> A` 会形成长度为 1 的回到当前节点，进入 cycle guard 并被拒绝；
2. `A -> B -> C` 后提交 `C -> A` 会被同一个 DFS 拒绝，不需要依赖 Open Canvas 的 DAG 实现。

此外，programmatic pair helper 对 `sourceId == targetId` 有独立的 early return。这为 `GI-005` 提供了更强的静态证据。

代码对 `REFERENCE` node 有特殊路径：已有 reference source edge 不进入 adjacency，候选 source 为 reference 时也不会按普通 source 加入 adjacency。该例外可能是 reference 语义，而不是普通 graph 允许环的证明；没有 disposable source 交互和 reference fixture 时，必须保持 `UNKNOWN_EXCEPTION_PATH`。

### 4.5 node action/type compatibility

`2axsluxmmf6m6.js` 导出一个 action-to-action `connections` 映射，`validateGeneratorConnection` 以它为基础继续做领域校验。兼容性不是 Open Canvas 的 `note/text/image/video/audio` 五类 node 表直接移植，而是由 LibTV 的 node action、node type 和当前数据共同决定。

静态可确认的校验层包括：

| 层 | 当前 bundle 事实 | 对复刻的意义 |
|---|---|---|
| Reference 特例 | target 是 `REFERENCE` 时只接受 reference source；source 是 reference 时走特殊允许路径 | 不可用通用 DAG/typed rule 覆盖 |
| action 默认化 | text、image、video、video-clip、shot-breakdown 等 node type 在缺少 action 时推导默认 action | verifier 需要以有效 action 观察，而不是只看 DOM class |
| Script V2 / storyboard group | Script V2 与 image/video storyboard group 存在显式禁止组合 | group 是领域节点，不是普通 container |
| video-clip | 受 blob URL、最大视频片段数量和当前目标 clips 约束 | 目标容量是连接合法性的一部分 |
| text target | image/video 输入按 text 参数中的模型能力和上限计算 | 同一 node type 也可能因参数而不同 |
| generator target | `VIDEO_GENERATE`、`IMAGE_GENERATE`、`AUDIO_GENERATE`、`SCRIPT_GENERATE` 等分别检查 input type、当前 model、素材数量和 `switchToModel` | 兼容性结果可能是 `allowed + switchToModel`，不是 boolean-only |
| material / shot 特例 | material style/lens 和 shot breakdown 有独立的目标类型、重复数量与能力检查 | 不能只维护一张静态 node-type 矩阵 |

当前 `isValidConnection` 最后把 `{allowed, switchToModel}` 写入 invalid-target 状态或保留给 `onConnect`，而不是在 store `addEdge` 中自动修复。验证失败不会调用 `addEdge`。

## 5. `GI-004..007` 状态更新

| ID | 本轮 source static result | 当前判定 | 尚未回答 |
|---|---|---|---|
| `GI-004` | 普通连接 validator 对同向、反向、不同 Handle 的相同节点对使用同一 pair guard | `STATIC_RECORDED / INTERACTION_REQUIRED` | store/import/batch 入口是否同样拒绝；invalid UI 是否有残留 |
| `GI-005` | programmatic pair 显式拒绝同一 ID；普通 source 进入 DFS 也拒绝 self-loop | `STATIC_RECORDED / REFERENCE_EXCEPTION_UNKNOWN` | reference source、真实 Handle 拖拽和 history/no-residue |
| `GI-006` | 普通连接 validator 构造 adjacency 并 DFS 拒绝有向环 | `STATIC_RECORDED / INTERACTION_REQUIRED` | cycle rejection 的 toast/invalid target/connection line 生命周期 |
| `GI-007` | 两侧 Handle 可作为起点但 onConnect 会归一化方向；action matrix + model/capacity validator 决定最终 allowed | `STATIC_RECORDED / CONTEXT_MATRIX_INCOMPLETE` | 所有 node action 的 UI affordance 是否与 validator 完全一致；动态 model 状态 |

### 5.1 对 compatibility case 的直接影响

| Case | 静态预期 | 交互前不能宣称 |
|---|---|---|
| `GC-002` exact duplicate | 普通连接路径拒绝同向重复 pair | 全部入口、toast、history 和 edge residue 已验证 |
| `GC-003` parallel Handle edge | 不因 Handle 改变而绕过 pair guard，普通路径预期拒绝 | 后端回流/import 是否接受 distinct handle edge |
| `GC-004` self-loop | 普通 source 与 programmatic helper 均有拒绝证据 | Reference 例外和 UI 清理已验证 |
| `GC-005` three-node cycle | 普通 source 有 DFS 拒绝证据 | 真实 drag 的 connection line、invalid state 和 no-op history 已验证 |

## 6. 对 Open Canvas 借鉴的收敛结论

Open Canvas 仍然提供三条高价值方法启发：

1. **把校验放在 connection boundary，而不是让低层 edge setter 猜测用户意图。** LibTV 当前生产 bundle 也支持这一方向，但 LibTV 的 action/type/model 领域合同必须保持独立。
2. **先规范化端点，再做 duplicate/cycle/type/capacity 检查。** 这能避免“从 target 拖出”的 UI 手势产生两种 edge 方向。
3. **invalid connection 是一个有结果形状的事务分支。** 至少应区分 `allowed`、invalid target、可选 model switch、UI 清理和“没有 graph/history mutation”；不能只断言 edge count。

不应移植的内容：

- Open Canvas 的五类 node type、Handle 命名或 DAG 结论不能替代 LibTV action matrix；
- Open Canvas 的 `isValidConnection` 具体函数、provider payload、错误文案和 UI 颜色不能直接复制；
- 当前源站的 pair guard 与 Open Canvas 的 graph rule 都不能自动授权修改 clone 的 `canvasStore`；
- `REFERENCE` 特例表明，单纯引入全局 DAG guard 可能破坏 LibTV 的特殊素材关系；
- 不得因为静态 bundle 已有 guard，就在共享源站拖线补截图或修改共享 graph。

## 7. 后续实施交接（仅文档，不是编码授权）

获授权后，`OC-BP-004` 的最小实施顺序应是：

1. 以 `LIBTV-FIX-LOCAL-EMPTY-01` 建立纯 graph compatibility 输入，不先改 Handle UI；
2. 把端点存在性、规范化方向、pair duplicate 和 self-loop/cycle 作为纯逻辑结果测试；
3. 将 node action/type matrix、目标容量和 model capability 接在 graph guard 之后；
4. 保证 invalid path 不新增 node/edge、不移动 selection、不新增 history，不产生孤立 preview；
5. 再把同一 validator 接入实际 Handle callback 和 programmatic entry；
6. 用 `GC-002..005` 的专用 verifier 证明 edge、selection、history、connection line 和 invalid feedback 的完整生命周期；
7. 每条 guard 单独形成 replacement 记录，不能用 Open Canvas 的测试或当前已有 graph 样本替代。

当前仍应保持 `OC-BP-004 = STATIC_AUDIT_RECORDED`，而不是 `IMPLEMENTED` 或 `SOURCE_DECISION_CLOSED`。

## 8. 未决问题与停止点

- 本轮没有取得可独立 reset 的 LibTV disposable project，因此没有执行 duplicate、parallel、self-loop 或 cycle 的实际拖线；
- 当前 graph 没有这些结构，只是样本事实，不是产品允许/拒绝结论；
- `REFERENCE` 连接例外、导入/批量/同步入口的校验覆盖和 invalid UI residue 仍未知；
- model capability 和 `switchToModel` 是动态状态，静态 matrix 不能证明 35-row catalog 中每个模型可运行；
- 只要下一步需要连接、输入、生成、保存或创建节点，就停止在 `BLOCKED_BY_DISPOSABLE_SOURCE`，不在共享项目继续试探。

## 9. 原始证据与追溯

| 证据 | 位置 |
|---|---|
| DOM/edge/Handle 结构化采样 | 本批次结构化 JSON：[`libtv-graph-compatibility-static-audit-2026-08-27.json`](libtv-graph-compatibility-static-audit-2026-08-27.json) |
| source freshness 上下文 | [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](LIBTV_SOURCE_FRESHNESS_2026-08-27.md) |
| Open Canvas graph/validation 方法 | [`OPEN_CANVAS_PATTERN_CARDS.md`](OPEN_CANVAS_PATTERN_CARDS.md)、[`ADOPTION_DECISION_MATRIX.md`](ADOPTION_DECISION_MATRIX.md) |
| LibTV graph authority | [`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#10-libtv-par-008-invariant-and-compatibility-design) |
| 后续证据队列 | [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](NEXT_EVIDENCE_ACQUISITION_PLAN.md) 的 `OC-EQ-003` |
| 主张 ID | `LIBTV-TR-029` |

本报告不保存生产 bundle 副本；bundle URL、chunk 名和检索到的语义均记录在 JSON，避免把随时变化的临时资源伪装成仓库源码基线。
