# LibTV Source Freshness Reinspection Runbook

> 目的：为 `LIBTV-PAR-005` 提供一次可重复、只读、带版本和停止条件的 LibTV 源站复核流程。
>
> 本文是研究 runbook，不是源站操作授权，也不是 clone 编码计划。当前共享项目只能作为 `SHARED_READ_ONLY` 观察对象；fixture 边界见 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)。

## 1. 为什么需要重新复核

2026-08-25 的源站快照已经回答了首轮页面壳、10 节点/11 边、默认 viewport、两个底部工具条和图片节点双浮层等问题，但它是 dated snapshot。之后 clone 已经发生多轮实现，源站也可能发生部署、文案、动作集合、几何或响应式变化。

重新复核的目标不是重做全部网站逆向，而是回答以下有限问题：

1. 页面壳和主要入口是否仍然是同一组 surface；
2. 当前共享项目的 node/edge/viewport 是否还能作为 source-shaped 观察基线；
3. 图片上下浮层的动作集合、定位公式和自然裁切是否漂移；
4. top-level surface 的 outside/backdrop/Escape/focus 行为是否变化；
5. 哪些旧截图、脚本和文档仍是 current evidence，哪些应降级为 historical；
6. 后续是否可以授权某个 local clone slice，或仍必须停在 research/fixture gate。

不在目标内：通过生成、上传、保存、下载、AutoLink 接受、图层分离、标注提交或其他会改变共享项目的动作“补齐”未知状态。

## 2. 证据基线与版本规则

### 2.1 先读的文件

| 文件 | 用途 |
|---|---|
| [`liblib-live-2026-08-25/README.md`](liblib-live-2026-08-25/README.md) | 2026-08-25 页面壳、节点基线、图片定位和初始状态 |
| [`liblib-live-2026-08-25/canvas-audit.json`](liblib-live-2026-08-25/canvas-audit.json) | 首屏 DOM、computed style、节点/边结构 |
| [`liblib-live-2026-08-25/full-canvas-audit.json`](liblib-live-2026-08-25/full-canvas-audit.json) | 完整 10 节点/11 边结构化抽取 |
| [`liblib-live-2026-08-25/panel-audit.json`](liblib-live-2026-08-25/panel-audit.json) | 主入口面板、尺寸和可见文案 |
| [`liblib-live-2026-08-25/image-node-state-audit.json`](liblib-live-2026-08-25/image-node-state-audit.json) | 图片节点多状态和面板几何 |
| [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md) | 当前 clone 的 mount owner、关闭和 keyboard 边界 |
| [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | 当前源站双浮层公式和 clone 验收方向 |
| [`design-references/README.md`](../design-references/README.md) | 截图识别和新证据命名纪律 |

先在 `docs/research/` 中搜索目标截图名和 `SCREENSHOT_ANALYSIS.md`。旧记录已经回答的问题，不再次消耗视觉识别预算；只有要验证漂移、记录不同状态或旧记录明确不确定时才打开截图。

### 2.2 新 run 的不可变原则

- 不覆盖 `liblib-live-2026-08-25/` 的 JSON、README 或截图；
- 新观察使用新的日期目录或新的 dated report；
- 每条结论标为 `SOURCE_FACT`、`INFERENCE`、`CLONE_FACT` 或 `DECISION`；
- 记录 URL、登录态前提、采样日期、browser viewport、canvas zoom 和 selected node；
- 如果源站部署更新，记录可见版本/时间或至少记录观察日期和页面 URL；
- 旧数字不因“看起来可能还对”自动升级为 current；
- runbook 只能输出新 source evidence，不能直接改写 clone component spec 或 verifier 断言。

推荐输出目录：

```text
docs/research/liblib-live-YYYY-MM-DD/
  README.md
  SOURCE_FRESHNESS_AUDIT.md
  shell-audit.json
  overlay-audit.json
  surface-lifecycle-audit.json
```

截图仍放在 `docs/design-references/`，文件名包含 `liblib-original`、状态、viewport 和日期，并从新 report 链接回去。

## 3. 安全前提与停止条件

### 3.1 允许动作

| 类别 | 允许内容 | 结果 |
|---|---|---|
| Navigation | 打开指定 URL、等待页面稳定、读取当前 route | 记录 URL/登录态/加载错误 |
| Read DOM | 查找已有节点、按钮、菜单、面板、文本、属性、computed style | 保存结构化证据 |
| Read geometry | 读取 `getBoundingClientRect`、viewport transform、scroll/client bounds | 计算 screen/flow 对照 |
| Selection | 选择已有节点以显示其现有只读 surface | 记录 selection 前后无 graph 写入证据 |
| Non-mutating lifecycle | 打开后关闭已知不写入的帮助、drawer、菜单、预览入口 | 记录 outside/Escape/backdrop/focus 行为 |
| Static source | 读取已经存在的 bundle/网络资源文本和版本 URL | 标为 source evidence 或 inference，不当作公开 API |

### 3.2 禁止动作

下列任一动作出现确认、提交、二次确认或未知副作用可能时，立即停止并记录为 blocked：

- 在 Prompt、contenteditable、textarea 或搜索输入框输入文本；
- 点击 AutoLink switch、ghost、Tab acceptance 或“全部引用”；
- 拖动节点、创建/删除/复制/分组/整理 graph；
- 上传、生成、重拍、续写、逐帧拉片、超长视频提交；
- 旋转提交、图层分离、标注保存、下载或覆盖结果；
- 变更可能持久化的偏好、素材、项目或 canvas metadata；
- 依赖 source undo、reload 或关闭页面声称已清理远端状态；
- 在同一共享项目尝试不同候选数据以“寻找” ready-video/process 状态。

### 3.3 立即停止条件

```text
登录过期 / 页面出现确认提交 / 操作语义不明确 / graph 数量变化
  -> 不继续点击
  -> 记录最后一个安全动作和可见状态
  -> 标记 BLOCKED_BY_FIXTURE 或 SOURCE_CONTRACT_ONLY
```

如果发现共享项目已经被其他操作者改变，不尝试恢复或覆盖；只记录“baseline 不再可验证”，转用独立 disposable project 要求。

## 4. 复核顺序

### Pass 0：环境登记

在打开任何菜单前记录：

- URL、当前账号是否已登录以及是否出现权限/项目加载错误；
- browser viewport 和 device scale factor；
- `document.documentElement`、`body`、React Flow viewport 的 scroll/client 尺寸；
- 当前 canvas zoom、transform 和 selection；
- 页面是否有 loading、toast、modal、drawer 或未关闭的旧 surface；
- console/page error 数量；
- source project 是否为共享研究项目，若是则锁定 `SHARED_READ_ONLY`。

若不能确认项目身份或当前状态是否为上一次研究遗留，停止做状态性比较，只做页面壳读取。

### Pass 1：页面壳 freshness

使用桌面 `1440x900` 或当前可用 viewport 先复核：

| Surface | 观察项 | 必须输出 |
|---|---|---|
| Top navigation | logo、project/canvas entry、workbench/storyboard、share、credits、Agent | visible labels、rect、z-index、开关条件 |
| Main canvas | background、React Flow viewport、node/edge container | client rect、transform、overflow、初始 count |
| Primary bottom toolbar | add、move、toolbox、assets、character、history、shortcuts、tutorial | action order、bounds、disabled/hidden 状态 |
| Canvas controls | asset manager、organize、minimap、edges、snap、zoom | action order、bounds、popover/dropdown ownership |
| Drawers | asset manager、Agent、other read-only panel | width、canvas shrink/overlay、close path |

只比较“surface 是否存在、职责和相对层级”。单个像素变化先记为 observation，不直接判定 clone 需要编码。

### Pass 2：项目与 graph baseline

不移动和不整理节点，只读取当前共享项目：

```text
node count:
edge count:
node type histogram:
selected node IDs or roles:
viewport transform:
visible source/result status:
parent-child markers:
```

与 2026-08-25 快照对照：

| 旧基线 | 复核判定 |
|---|---|
| 10 nodes / 11 edges | 相同才可暂称 source-shaped baseline；否则记录 drift |
| `canvas-2` 约 `translate(-583.8px,260.8px) scale(0.526)` | 只作为旧采样对照，不把 clone viewport 写回源站事实 |
| 视频 group child 的 parent relationship | 只读 DOM/class/相对位置确认，不拖动验证 |
| image empty/prompt/referenced roles | 按可见节点角色记录，ID 变化不代表功能变化 |

节点 ID、文案、媒体状态变化要分开记录。数量相同但 status、parent 或 viewport 不同，仍属于 baseline drift。

### Pass 3：top-level lifecycle

对每个入口只做一次“打开 -> 读取 -> 关闭”：

1. 打开入口前记录其他 surface 数量；
2. 点击已知无写入入口；
3. 等待动画稳定，读取 surface rect、role、aria、backdrop 和 focus；
4. 使用 source 可见的关闭方式关闭：close button、outside、Escape 或返回；
5. 关闭后再次读取 active surface、selection、node/edge count 和 viewport；
6. 若 surface 互斥，记录被卸载的是哪个 surface，不将其推断成全局 modal manager；
7. 若出现输入框、提交按钮或不明确认，立即结束该入口。

Lifecycle 结果应明确区分：

```text
mounted/unmounted
visible/hidden
focus owner
outside behavior
backdrop behavior
Escape behavior
selection/graph/viewport delta
```

### Pass 4：selected-image double overlay

只选择现有图片节点，不点击工具动作。至少选择两个位置不同、内容状态不同的图片角色；优先使用旧快照中有明确记录的 empty/prompt/referenced 样本。

每个样本读取同一 frame 的：

```text
node rect
top toolbar rect
bottom panel rect
React Flow viewport rect/transform
toolbar action IDs/order
panel variant/height
overflow/clipping ancestors
focus/selection state
```

在 `zoom ≈ 0.28`、`0.526` 和一个接近 `1` 的可安全观察 zoom 采样。若源站 zoom 菜单本身不是无副作用入口，则只使用已经可见的 zoom 状态，不为取数改变项目状态。

旧合同的计算对照：

```text
top source host: nodeTop - 24 * zoom - 10
bottom panel gap: 16 * zoom
both horizontal centers: node center
```

这些只是待复核公式。每个新样本都必须保存原始 rect 和 zoom，不能只报告“仍然居中”。同时检查：

- top toolbar 是否 content-sized、动作/顺序/宽度是否变化；
- bottom panel 是否仍以 node-internal absolute + inverse scale 保持屏幕尺寸；
- 靠边节点是否自然裁切，还是出现新的 clamp/avoidance；
- active tool 是否替换标准 double overlay，而不是叠加第三层；
- wheel/pan/selection 是否导致 surface 使用旧 frame。

### Pass 5：响应式对照

优先使用不改变源站 graph 的 viewport 模拟或已有只读页面状态，采样：

| Viewport | 目的 |
|---|---|
| `1440x900` | 宽桌面 page shell、drawer shrink、全量 toolbar |
| `929x874` | 与历史 Batch 9/10 和图片几何脚本可对照 |
| `768x900` | 平板临界点、top-level action 隐藏和 toolbar 换行 |
| `390x844` | 移动端 top nav、底栏堆叠、自然裁切和触控目标 |

对每个 viewport 记录 visible/hidden、stack/order、rect 和 horizontal overflow。不要仅用 screenshot 视觉估计；同时写 DOM/computed measurements。

## 5. 证据记录模板

新建 `SOURCE_FRESHNESS_AUDIT.md` 时使用：

```text
Source URL:
Observation date/time:
Account/session boundary:
Project/space identity:
Fixture classification: SHARED_READ_ONLY / disposable source
Browser viewport(s):
Canvas zoom(s):
Console/page/request errors:
Pre-observation node/edge/selection/viewport:

## Surface observations
Surface:
State and trigger:
DOM selectors/roles:
Rect/computed style:
Focus/outside/backdrop/Escape:
Graph/selection/viewport delta:
Source fact or inference:

## Selected-node observations
Node role/ID:
Node rect:
Top surface rect/action order:
Bottom surface rect/variant:
Formula inputs and result:
Clipping/overflow:

## Drift decision
Unchanged:
Changed:
Unknown:
Historical artifacts affected:
Clone parity IDs affected:
Required follow-up fixture:
```

原始 JSON 至少保存：viewport、surface selector/role、rect、computed style、text/action identity、node/edge counts、selection 和 error list。不要只保存截图。

## 6. Drift 判定与后续动作

| 观察结果 | 文档动作 | clone 动作 |
|---|---|---|
| 页面壳、动作职责和几何仍一致 | 新报告标为 current source confirmation | 不自动编码；可更新证据索引日期 |
| toolbar action/order/width 变化 | 旧合同保留为 historical，追加新版本 | 重新评估 `PAR-001`，不得直接改旧 verifier 数字 |
| top/bottom anchor formula 变化 | 新增版本化 positioning evidence | 等明确授权后设计 replacement verifier |
| node/edge/viewport 变化 | 标记共享项目 baseline drift | 停止把共享项目当 fixture，转 disposable 要求 |
| 新增/删除 top-level surface | 更新 surface lifecycle catalog | 只在确认 source contract 后评估 parity |
| source 出现 ready-video/process | 只读记录是否可安全打开 | 未有写入授权仍不提交任务；记录可申请的 fixture |
| source 需要输入/提交才能确认 | 记录 blocked action、所需权限和观察量 | 保持 `BLOCKED_BY_FIXTURE` |
| login/网络/权限失败 | 记录 source observation unavailable | 不以 clone 或旧截图填补 current source claim |

“未发现变化”必须附 viewport、zoom、样本数量和读取范围；不能把一次首屏观察写成全站无变化。

## 7. 与 Clone 文档的同步边界

完成新 run 后按以下顺序更新：

1. 先写 dated `SOURCE_FRESHNESS_AUDIT.md` 和原始 JSON；
2. 再把稳定 source claim 追加到 [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)；
3. 更新 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的 source-contract 状态和 fixture 阻塞；
4. 更新 [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md) 的 evidence/version/fixture 字段；
5. 只有获得编码授权并确认 clone 行为后，才更新组件合同、verifier 和 implementation history；
6. 旧截图、旧 Batch 和旧数字保留 supersession 说明，不静默重写。

不把以下内容混在 source freshness report：

- clone 的理想实现；
- Open Canvas 的通用启发；
- 未触发的 Provider/任务结果；
- “应该更易用”的可访问性改良；
- 共享源站项目的恢复/清理假设。

## 8. Run Completion Checklist

- [ ] 已读取旧 source screenshot analysis 和结构化 JSON；
- [ ] 已确认当前 URL、账号/session、project identity 和共享只读边界；
- [ ] 已记录 viewport、zoom、selection、node/edge count 和 errors；
- [ ] 已按 page shell、baseline、top-level lifecycle、selected-image overlay、responsive 顺序复核；
- [ ] 未输入、提交、上传、生成、保存、下载或修改共享 graph；
- [ ] 每条观察有 DOM/rect/computed 或截图证据；
- [ ] source fact、inference、clone fact、decision 已分开；
- [ ] 变化、未知项和 required fixture 已赋予后续动作；
- [ ] 新报告没有覆盖旧 dated snapshot；
- [ ] `python3 scripts/verify-docs.py` 通过；
- [ ] 文档变更只做 path-scoped commit/push。

## 9. 当前决策

在没有新的独立 source project、明确写入授权或安全可见 ready-video/process fixture 前，本 runbook 只支持页面壳、已有节点、无副作用浮层和响应式的只读复核。它不能解锁 AutoLink 输入、ready-video 提交、process lifecycle、dirty image action 或 source-only shortcut 的研究。

后续 agent 完成新 run 后，应把结果挂回 [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md) 的 `PAR-005`，并重新检查 [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) 和 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)。
