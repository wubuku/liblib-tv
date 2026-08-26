# LibTV Verifier Replacement Map

> 目的：区分历史 clone 回归、当前 source contract、local fixture contract 和尚未具备 source fixture 的断言，给后续授权 batch 一条可审计的替换路径。
>
> 本文是文档和测试规划，不修改现有 verifier，也不把任何历史通过升级为当前 LibTV parity。当前 fixture 身份与 reset 见 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)；跨项目长期闸门见 [`DECISION_REGISTER.md`](../DECISION_REGISTER.md) 的 DEC-021 至 DEC-023。

## 1. 核心规则

现有 verifier 的“通过”只说明某个日期、某个 clone 实现、某个 fixture 和某个 selector 集合满足断言。它不自动说明：

- 当前源站仍然使用相同动作、几何或数据结构；
- clone 已经覆盖当前源站；
- 共享源站项目具备可重复的 ready/process/dirty fixture；
- 本地 mock 已经具备真实 Provider、上传、计费或持久化语义。

因此替换采用双轨策略：

```text
历史 verifier 保留为 compatibility regression
  + 新 source-shaped/local fixture verifier 并行建立
  -> 新 verifier 稳定并记录 source/clone 边界
  -> 再决定旧断言是保留、降级或退役
```

禁止为了让新实现通过而直接放宽、删除或重写旧断言。旧断言如果与当前 source contract 冲突，应先标成 `HISTORICAL_CONTRACT`，保留其 provenance。

## 2. 状态分类

| 分类 | 解释 | 允许的后续动作 |
|---|---|---|
| `CURRENT_SOURCE` | 当前日期 source DOM/bundle/截图或安全交互直接支持 | 可形成 source contract；仍需 clone fixture 才能回归 |
| `HISTORICAL_CLONE` | 旧日期 clone 实现/截图/脚本直接支持 | 保留兼容回归；不能推导 current source |
| `LOCAL_FIXTURE` | 当前 clone 通过稳定本地构造或 bounded transaction 支持 | 可回归 clone prototype；不称 source parity |
| `BLOCKED_SOURCE` | 需要 ready-video、输入、提交、保存或独立项目 | 登记所需 fixture 和停止条件，不在共享项目试探 |
| `REPLACEMENT_READY` | source contract、clone 实现、fixture 和新 verifier 都已具备 | 可在独立 commit 中申请替换旧断言 |
| `PARALLEL_WIP` | 其他开发者正在修改相关实现、fixture 或脚本 | 只读；不把当前文件当稳定基线 |
| `OUT_OF_SCOPE` | 需要真实 Provider、账户、计费、远程任务或生产资产 | 不创建前端 verifier 假装覆盖 |

这些分类与 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的 maturity 状态相关但不相同。一个 verifier 可以同时是 `SCRIPT_AVAILABLE` + `HISTORICAL_CLONE`，也可以是 `SCRIPT_AVAILABLE` + `LOCAL_FIXTURE`。

## 3. 按 Batch 的保留与替换矩阵

| Batch | 当前 verifier 价值 | 分类 | 需要替换/补充的内容 | 处理决策 |
|---|---|---|---|---|
| 4-8 | 分组、多选、移动、复制、导航、整理、parent-child 的 clone 行为 | `HISTORICAL_CLONE` + `LOCAL_FIXTURE` | 只有在 source contract 改变时补 source evidence | 保留；不把普通 graph 通过解释成全量源站一致 |
| 9 | 图片/视频双浮层中心、bottom gap、pan/zoom follow、自然裁切 | `HISTORICAL_CLONE` | current top action set、`1092.5px` width、`10 + 24 * zoom` top formula、同 frame rect | 保留旧脚本；授权后增加 current toolbar replacement |
| 10 | 五种图片 panel 内容/高度、旧 AutoLink popover | 混合 | 固定候选、56px popover、全量接受、textarea 前缀写回必须替换 | 保留图片 variant compatibility；AutoLink 断言隔离为 historical |
| 11 | top-level overlay 互斥、Escape、mobile overflow | `HISTORICAL_CLONE` + `LOCAL_FIXTURE` | 当前 modal/focus/backdrop 行为若 source refresh 漂移 | 保留；source freshness 后再补缺失 focus contract |
| 12-20 | asset、storyboard、Agent/share、canvas metadata、zoom/minimap、panorama | `LOCAL_FIXTURE` | 新 source evidence 仅在能力发生漂移时补 | 保留 bounded clone contracts |
| 21-22 | Seedance 普通/超长参数与模型菜单 | `LOCAL_FIXTURE` + source sampled | 当前 source action/number 版本化；真实 provider 不纳入 | 保留 prototype；数字标为 sampled |
| 23-25 | 片段重拍、逐帧拉片结果结构、智能剪辑空态 | `LOCAL_FIXTURE` + `BLOCKED_SOURCE` | source ready-video、result/version/process lifecycle | 保留 clone fixture；新增 source-ready contract 前不替换 |
| 26-33 | 续写、字幕、音视频分离、截帧、主体编辑、深度、长视频 | `LOCAL_FIXTURE` + `BLOCKED_SOURCE` | source ready/process/dirty fixture、失败和重试状态 | 保留 bounded graph/history；真实 lifecycle 单独新增 |
| 35-47 | Director R3F、timeline、path、capture/export、phone、pose、camera、groups、model proxy | `LOCAL_FIXTURE` + `HISTORICAL_CLONE` | source locale/entry 与 clone implementation 分开；真实资产不推导 | 保留 bounded Director regression；不迁移成普通 LibTV verifier |
| 48 | Director local model import/persistence workflow | `LOCAL_FIXTURE` + `HISTORICAL_CLONE` | 保留 clone-owned storage reset、focused verifier 和 bounded maturity；真实 mesh/远端同步另行阻塞 | 作为有界 Director regression 保留；不迁移成普通 LibTV 或源站 parity verifier |

Batch 34 是 research-only，不是缺失的 verifier；不要为它创建“补跑脚本”以填充编号。

## 4. 旧断言到新合同的迁移

### 4.1 `verify-liblib-batch9.py`

当前旧断言：

```text
toolbar width = 900.5px
toolbar height = 49px
toolbar top gap = 16px
bottom panel gap = 16 * zoom
center(toolbar) = center(node)
center(panel) = center(node)
```

处理方式：

| 断言 | 保留理由 | 新合同动作 |
|---|---|---|
| height `49px` | 与当前 source evidence 仍可能兼容 | 新 verifier 重新采样后确认 |
| bottom `16 * zoom` | 当前 source/clone positioning contract | 保留并补 panel height variants |
| 两者 node-center | 关键定位不变量 | 保留，要求同一 frame 读取 rect |
| width `900.5px` | 旧动作集合的结果 | 标为 historical；current source 目标为 content-sized `1092.5x49` |
| top gap `16px` | 旧 clone snapshot | 标为 historical；current source 目标为 `10 + 24 * zoom` |

新 verifier `VR-001` 只有在 `LIBTV-FIX-LOCAL-IMAGE-01`、当前 action-set contract 和明确编码授权都存在时才建立。它不能通过改写旧 Batch 9 的常量来完成替换。

### 4.2 `verify-liblib-batch10.py`

当前旧断言把下列 clone-only 行为当作一个 AutoLink 流程：

```text
Prompt 非空且 references 为空
  -> 显示固定“陈默、咖啡”候选
  -> 一个“引用”按钮全部接受
  -> 普通字符串前缀写回 textarea
```

它与当前 source contract 的 `global preference -> connected/reference candidate pool -> inline ghost -> structured mention` 不同。处理方式：

- 图片五种 panel variant 的尺寸、Prompt/reference 展示仍保留为历史图片编辑 compatibility；
- AutoLink popover selector、固定候选文案和全量接受断言标成 `HISTORICAL_CLONE`；
- 新 `VR-003..005` 不复用旧 selector，也不添加更多固定候选；
- 新断言使用 stable node ID、ghost/badge data marker、text version、IME 和 graph/reference/mention transaction；
- 没有 local AutoLink fixture 时只写纯 contract test/plan，不运行共享源站输入。

### 4.3 `verify-liblib-batch21.py` - `batch33.py`

这些脚本的主要价值是 clone UI closure、bounded graph transaction、selection 和 undo/redo。它们不能证明源站结果态。保留规则：

- 参数、菜单、空态、pending graph 和 mock 费用是 `LOCAL_FIXTURE`；
- `300s / 14700` 等值只作为日期化采样，不成为永久 API 断言；
- 12 process nodes / 22 edges 是本地 process shape，不是源站任务拆分；
- source-ready toolbar、real segment replacement、partial/failed/retry lifecycle 均进入 `BLOCKED_SOURCE`；
- 任何新 source verifier 必须使用独立 source fixture，并记录 version/time range/run/node/save status。

### 4.4 `verify-liblib-batch35.py` - `batch48.py`

Director 脚本的 domain state 通过 `window.__director_store` 驱动或读取，并拥有独立的 R3F、timeline、history、capture/export 语义。它们：

- 可以继续保护 bounded Director prototype；
- 不能作为普通 LibTV `canvasStore` fixture 或 source parity 验证；
- 真实 mesh/FBX/OBJ、摄影机设备、Provider 和远端资源不在当前合同内；
- Batch 48 已补齐 clone-owned local model 的 setup/teardown、storage boundary 和 focused verifier；这些断言仍只证明 Director prototype。
- 新增 Director persistence 或 local model fixture 时，必须由 owner 维护 setup/teardown 和 storage boundary，不得把普通 LibTV 的 reset 规则套进来。

## 5. Replacement Queue

### `LIBTV-VR-001`：当前 selected-image geometry/action set

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-001` |
| Old verifier | Batch 9 |
| Required fixture | `LIBTV-FIX-LOCAL-IMAGE-01`，current source read-only image role |
| New checks | current action IDs/order/width/height；top/bottom center；`10 + 24 * zoom`；`16 * zoom`；natural clipping |
| Blockers | coding authorization；current source action-set confirmation |
| Exit | focused desktop/mobile/zoom verifier + old Batch 9 compatibility retained |

### `LIBTV-VR-002`：active image low-risk replacement states

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-002` |
| Old verifier | 无 |
| Required fixture | local image；source empty Preview/Annotate/Element Edit read-only observations |
| New checks | standard double overlay replaced；open/close；selection/graph unchanged；mobile bounds |
| Blockers | explicit coding authorization；source state confirmation |
| Exit | one focused verifier per low-risk state，不能把 high-risk dirty action 混进来 |

### `LIBTV-VR-003`：AutoLink preference and candidate identity

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` |
| Old verifier | Batch 10 fixed popover assertions |
| Required fixture | `LIBTV-FIX-LOCAL-AUTOLINK-01`；source disposable only for input behavior |
| New checks | global preference；connected/reference candidate scope；stable node ID；ordinal projection |
| Blockers | typed editor/data design；local deterministic candidates；source input authorization |
| Exit | image/video cross-node preference and candidate changes are separately asserted |

### `LIBTV-VR-004`：AutoLink ghost and keyboard race

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` / `PAR-004` |
| Old verifier | 无 |
| Required fixture | deterministic delayed detection、IME composition、competing popover |
| New checks | ghost does not mutate committed text；click/Tab single；Shift+Tab all；Escape/blur/edit cleanup；stale discard |
| Blockers | editor representation and race contract |
| Exit | no stale badge, no keyboard theft, no layout detachment after pan/zoom |

### `LIBTV-VR-005`：AutoLink graph/reference/mention transaction

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-003` / `PAR-008` |
| Old verifier | 无 |
| Required fixture | connected and unconnected candidates；success/failure connection outcomes |
| New checks | connect + mention atomicity；failure rollback；reference reorder changes ordinal only；undo/redo policy |
| Blockers | stable graph transaction contract；no orphan badge/edge rule |
| Exit | node identity, reference role and mention token remain independently inspectable |

### `LIBTV-VR-006`：source ready-video toolbar

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-006` |
| Old verifier | Batch 27-32 local tool checks |
| Required fixture | `LIBTV-FIX-LOCAL-VIDEO-READY-01` + `LIBTV-FIX-SOURCE-VIDEO-READY-01` |
| New checks | ready/failed/pending branches；action order；hover menu；active replacement；discard/submit delta |
| Blockers | source disposable ready video |
| Exit | source contract and clone local contract are separate records |

### `LIBTV-VR-007`：process/result lifecycle

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-009` |
| Old verifier | Batch 24/33 bounded results/process graph |
| Required fixture | local fixed status matrix + disposable source process if authorized |
| New checks | pending/failed/partial/success/retry；run/node/save status；version/time range；replacement and retry |
| Blockers | stable business interface or explicit local mock contract |
| Exit | no claim of real progress, billing or output quality |

正交 identity/state、stale completion、retry、local/source fixture 和 graph/history 断言统一见 [`open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。该矩阵完成的是 verifier 设计，不表示 fixture 或实现已经存在。

### `LIBTV-VR-008`：source-only shortcuts

| 字段 | 规划 |
|---|---|
| Backlog | `LIBTV-PAR-007` |
| Old verifier | Batch 3/4/6/7 partial clone handlers |
| Required fixture | local and disposable source shortcut subgraph with internal/external edges |
| New checks | precondition、focus、cancel、selection、graph/viewport/history delta |
| Blockers | source fixture or explicit source contract |
| Exit | help row、handler、React Flow gesture and local context are separately asserted |

## 6. Replacement Protocol

每个 `VR-*` 都按下列顺序执行：

1. 读取对应 source contract、fixture catalog 和旧 Batch implementation；
2. 在 PLAN 中写明 old verifier、new contract、fixture ID、out of scope 和 stop conditions；
3. 没有编码授权时只补文档、pure contract 或 source read-only evidence；
4. 获得授权后，先新增 verifier，不删旧 verifier；
5. 使用新 Page 或显式 fixture reset，记录初始/终态 graph、selection、viewport、history 和 storage；
6. 桌面、移动端、必要 zoom/边缘裁切和 console/page/request errors 分开断言；
7. 记录 focused pass、serial regression、截图解释、source/clone boundary；
8. 只有当新 contract 稳定、旧兼容价值已评估、文档已链接后，才考虑退役过时断言；
9. 每个 batch 做 path-scoped commit/push，不混入其他开发者 WIP。

## 7. 不能作为替换证据的事情

| 看似有用的信号 | 实际不能证明 |
|---|---|
| 历史 screenshot “final” | 当前源码仍相同 |
| 旧脚本 exit 0 | 当前 source parity |
| clone 按钮能点击 | source action、task 或 graph lifecycle |
| 一次 source undo | 远端 mutation 已清理 |
| clone `status=ready` | source ready-video toolbar |
| clone 12/22 process graph | source 真实任务拆分 |
| Open Canvas 有 typed state | LibTV 使用同样数据结构 |
| Batch 48 local storage 成功读写 | 普通 LibTV store 已具备持久化 |

## 8. Current Decision

截至 2026-08-27：

- Batch 9/10 的历史断言继续保留，不扩写为当前 source contract；
- Batch 21-33 的 local process/result checks 继续保留为 bounded clone fixture；
- Batch 35-47 继续保留为 bounded Director regression，不迁移到普通 LibTV；
- Batch 48 已是 bounded Director `recorded pass`，保留其 setup、storage、脚本、截图和实施记录；不把 local descriptor/proxy 解释为真实资产、远端同步或 LibTV persistence；
- 新 current-source verifier 只有在 source freshness report、fixture ID、明确授权和 replacement plan 同时存在时才进入实现批次；
- 在此之前，最有价值的后续工作仍是文档、纯合同和安全只读证据整理。

相关入口：[`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)、[`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)、[`liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)。
