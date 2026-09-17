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

## 10. 2026-09-12 Run 记录：客户端渲染劣化观察（Batch 358-359 挂接 PAR-005）

> 只读观察，无写入操作；viewport 1920×1150（CDP 覆盖）；账号为既有
> 登录态共享只读项目（SHARED_READ_ONLY）。

### 10.1 观察到的劣化（`SOURCE_FACT`，2026-09-12）

1. **模型菜单交互失效**（batch 333-352 反复复现）：菜单可打开
   （双击/单击均可），但滚动后虚拟化窗口重叠、行 DOM 成对出现
   （同 text 同 y），点击行命中相邻模型或无效果——
   `elementFromPoint` 命中验证与三种点击机制均无法稳定选中
   「Hailuo 2.3 Fast」（见 `LIBTV_VERIFIER_REPLACEMENT_MAP.md`
   §5.z3、`liblib-canvas-batch333/346/352`）；
2. **节点创建链路损坏**（batch 340 首次实证）：空画布「双击画布」
   创建菜单渲染到视口左上角原点，全部条目叠在同一坐标
   （x=33,y=81），点击无法创建节点（`+` 按钮路径同样失效）；
3. **画布页资源总览水合失败**（batch 356-359 观察）：goto 后
   bodyLen ≈ 90-311（仅顶栏壳），音频/图片/视频列内容与
   「待确认后生成」卡不渲染，且多次 reload 不可恢复；
4. **Agent「正在跟随」横幅**常驻顶栏中央（正在跟随/取消ESC/
   按 ESC 退出），取消按钮点击不生效，reload 后恢复。

### 10.2 判定与影响

- 判定：客户端 SPA 在共享项目会话中进入不可自愈的劣化态
  （可能与部署/灰度相关，非本工具侧可修复）；
- 影响：**BLOCKED_SOURCE 三项**（Hailuo 系条件分解、480P 档批量、
  Style Video 费率）与故事板 CLONE_DECISION 替换维持阻塞；
- clone 侧无回归（维护集 46 项 + jimeng batch 1 全绿）。

### 10.2b 复测运行日志

batch 433（对照批）重建本表：先前的追加脚本产生过整段重复行，并混入
早于实际执行的「预写行」（batch 433-436 / 第四十二次——这些探测从未
运行，无对应提交；已删除）。历史行按批次号排序、逐次去重后保留；
第 N 次标注存在两套序列（见表后说明），按各批 commit message 原样保留。

| 日期 | 挂接批次 | 结果 | 备注 |
|---|---|---|---|
| 2026-09-11 | batch 333-336 探测 | still-broken | 模型菜单虚拟化重叠 + 创建链路损坏首证 |
| 2026-09-11 | batch 338/340 探测 | still-broken | 资源总览水合失败（bodyLen≈311）|
| 2026-09-12 | batch 351/359 探测 | still-broken | PAR-005 §10 记录四项劣化观察 |
| 2026-09-12 | batch 364/368 探测 | still-broken | 探测脚本入库后首次复测 |
| 2026-09-12 | batch 369-371 探测 | still-broken | 本批前最后一次重测 |
| 2026-09-12 | batch 381 探测（脚本已入库） | still-broken | HARNESS.md 增补维护集权威清单 |
| 2026-09-12 | batch 382 探测 | still-broken | 第八次重测；工作区并行 jimeng WIP（batch 8+）持续 |
| 2026-09-12 | batch 384 探测 | still-broken | 第九次重测；jimeng 路线 batch 8 后暂无新提交 |
| 2026-09-12 | batch 390 探测 | still-broken | 第十次重测；49 项维护集全绿 |
| 2026-09-12 | batch 391 探测 | still-broken | 第十一次重测 |
| 2026-09-12 | batch 392-393 探测 | still-broken | 第十二、十三次重测（§3.3 审计/巡检批次） |
| 2026-09-12 | batch 394-396 探测 | still-broken | 第十四~十六次重测（心跳/巡检/对照批次） |
| 2026-09-12 | batch 397 探测 | still-broken | 第十七次重测 |
| 2026-09-12 | batch 398 探测 | still-broken | 第十八次重测 |
| 2026-09-12 | batch 399 探测 | still-broken | 第十九次重测；jimeng 路线仍为 batch 8 |
| 2026-09-12 | batch 400-403 探测 | still-broken | 第二十~二十三次重测（心跳批次） |
| 2026-09-12 | batch 404-409 探测 | still-broken | 第二十四~二十九次重测（心跳批次） |
| 2026-09-12 | batch 410 探测 | still-broken | 第三十次重测（留档批） |
| 2026-09-12 | batch 413-414 探测 | still-broken | 第三十一~三十二次重测；jimeng 验证器覆盖已扩至 batch 13 |
| 2026-09-12 | batch 416 探测 | still-broken | 第二十四次重测（此起标注序列重置，见表后说明） |
| 2026-09-12 | batch 417-423 探测 | still-broken | 第二十五~三十一次重测（心跳批次） |
| 2026-09-13 | batch 424-432 探测 | still-broken | 第三十二~四十次重测（心跳批次） |
| 2026-09-13 | batch 433 探测 | still-broken | 第四十一次重测；jimeng batch 28–32 对照同步入 §7 |
| 2026-09-13 | batch 434 探测 | still-broken | 第四十二次重测；jimeng batch 33 对照同步入 §7 |
| 2026-09-13 | batch 435 探测 | still-broken | 第四十三次重测；VR-017 INVALID_TARGET 切片关闭（batch 435） |
| 2026-09-13 | batch 436 探测 | still-broken | 第四十四次重测；VR-017 Slice B 关闭（batch 436） |
| 2026-09-13 | batch 437 探测 | still-broken | 第四十五次重测；VR-017 Slice E 关闭（batch 437） |
| 2026-09-13 | batch 438 探测 | still-broken | 第四十六次重测；VGP §7.2 resize anchor 关闭（batch 438） |
| 2026-09-13 | batch 439 探测 | still-broken | 第四十七次重测；VGP §6.3 endpoint phase 关闭（batch 439） |
| 2026-09-13 | batch 440 探测 | still-broken | 第四十八次重测；Batch History 索引补全（batch 440） |
| 2026-09-13 | batch 441 探测 | still-broken | 第四十九次重测；VR-023 Slice A 关闭（batch 441） |
| 2026-09-13 | batch 442 探测 | still-broken | 第五十次重测；VR-023 Slice B 关闭（batch 442） |
| 2026-09-13 | batch 443 探测 | still-broken | 第五十一次重测；VR-023 Slice C 关闭（batch 443） |
| 2026-09-13 | batch 444 探测 | still-broken | 第五十二次重测；VR-023 Slice D 关闭（batch 444） |
| 2026-09-13 | batch 445 探测 | still-broken | 第五十三次重测；VR-022 Slice A 关闭（batch 445） |
| 2026-09-13 | batch 446 探测 | still-broken | 第五十四次重测；VR-022 Slice B 关闭（batch 446） |
| 2026-09-13 | batch 447 探测 | still-broken | 第五十五次重测；VR-022 Slice C（record-editor 幂等）关闭（batch 447） |
| 2026-09-13 | batch 448 探测 | still-broken | 第五十六次重测；VR-022 Slice D 关闭（batch 448） |
| 2026-09-13 | batch 449 探测 | still-broken | 第五十七次重测；VR-022 Slice E 关闭（batch 449） |
| 2026-09-13 | batch 450 探测 | still-broken | 第五十八次重测；VR-021 Slice A 关闭（batch 450） |
| 2026-09-13 | batch 451 探测 | still-broken | 第五十九次重测；VR-021 Slice B 关闭（batch 451） |
| 2026-09-13 | batch 452 探测 | still-broken | 第六十次重测；jimeng 41–48 对照同步（batch 452） |
| 2026-09-13 | batch 453 探测 | still-broken | 第六十一次重测；VR-021 Slice C 关闭（batch 453） |
| 2026-09-13 | batch 454 探测 | still-broken | 第六十二次重测；VR-021 Slice D 关闭（batch 454） |
| 2026-09-14 | batch 455 探测 | still-broken | 第六十三次重测；VR-021 Slice E 关闭（batch 455） |
| 2026-09-14 | batch 456 探测 | still-broken | 第六十四次重测；VR-021 Slice F 关闭（batch 456） |
| 2026-09-14 | batch 457 探测 | still-broken | 第六十五次重测；jimeng 49–51 对照同步（batch 457） |
| 2026-09-14 | batch 458 探测 | still-broken | 第六十六次重测；jimeng 52 对照同步（batch 458） |
| 2026-09-14 | batch 460 探测 | still-broken | 第六十八次重测；§5.z4 老化处置 + jimeng 53 对照（batch 460） |
| 2026-09-14 | batch 462 探测 | still-broken | 第七十次重测；§5.z5 老化重写首批 5/9 回绿（batch 462） |
| 2026-09-14 | batch 463 探测 | still-broken | 第七十一次重测；viewport §6.4 move-end 竞态修复（batch 463） |
| 2026-09-14 | batch 464 探测 | still-broken | 第七十二次重测；batch 64 placement 专项调研（batch 464） |
| 2026-09-14 | batch 465 探测 | still-broken | 第七十三次重测；jimeng 56 对照同步（batch 465） |
| 2026-09-14 | batch 466 探测 | still-broken | 第七十四次重测；live 相 ownership 翻转精化（batch 466） |
| 2026-09-14 | batch 467 探测 | still-broken | 第七十五次重测；VR-018 Slice A 关闭（batch 467） |
| 2026-09-14 | batch 468 探测 | still-broken | 第七十六次重测；VR-018 Slice B 子项（batch 468） |
| 2026-09-14 | batch 471 探测 | still-broken | 第七十九次重测；jimeng 58 对照同步（batch 471） |
| 2026-09-14 | batch 472 探测 | still-broken | 第八十次重测；jimeng 59 对照同步（batch 472） |
| 2026-09-14 | batch 480 探测 | still-broken | 第九十次重测；batch 64 稳定性五连绿确认（batch 480） |
| 2026-09-14 | batch 479 探测 | still-broken | 第八十九次重测；jimeng 57 同步收尾（batch 479） |
| 2026-09-14 | batch 478 探测 | still-broken | 第八十八次重测；最新验证器稳定点检（batch 478） |
| 2026-09-14 | batch 473 探测 | still-broken | 第八十一次重测；VR-018 Slice C 合规审计（batch 473） |
| 2026-09-14 | batch 470 探测 | still-broken | 第七十八次重测；VR-018 Slice D 子项（batch 470） |
| 2026-09-14 | batch 469 探测 | still-broken | 第七十七次重测；jimeng 57 审计对照（batch 469） |
| 2026-09-14 | batch 459 探测 | still-broken | 第六十七次重测；全量验证器扫描（batch 459） |
| 2026-09-14 | batch 461 探测 | still-broken | 第七十二次重测；§5.z5 老化重写 53/65/119/167（batch 461） |
| 2026-09-14 | batch 474 探测 | still-broken | 第八十五次重测；VR-022 会话基线捕获（batch 474） |
| 2026-09-14 | batch 475 探测 | still-broken | 第八十六次重测；jimeng 61 对照同步（batch 475） |
| 2026-09-14 | batch 476 探测 | still-broken | 第八十七次重测；全量复扫部分 193/216（batch 476） |
| 2026-09-15 | batch 477 探测 | still-broken | 第八十八次重测；clip 面板 disposition（batch 477） |
| 2026-09-14 | batch 481 探测 | still-broken | 第九十一次重测；全量修复在位审计（batch 481） |
| 2026-09-14 | batch 482 探测 | still-broken | 第九十二次重测；影响面验证器点检（batch 482） |
| 2026-09-15 | batch 483 探测 | still-broken | 第九十三次重测；全量维护集新鲜运行（batch 483） |
| 2026-09-15 | batch 484 探测 | still-broken | 第九十四次重测；维护集新鲜运行 + jimeng 62 确认已自行录入（batch 484） |
| 2026-09-15 | batch 485 探测 | still-broken | 第九十五次重测；jimeng 63 对照同步（batch 485） |
| 2026-09-15 | batch 486 探测 | still-broken | 第九十六次重测；最新验证器稳定点检（batch 486） |
| 2026-09-15 | batch 487 探测 | still-broken | 第九十七次重测；freshness 行修复（batch 487） |
| 2026-09-15 | batch 488 探测 | still-broken | 第九十八次重测；jimeng 61–65 对照同步（batch 488） |
| 2026-09-15 | batch 489 探测 | still-broken | 第九十九次重测；freshness 完整性审计通过（batch 489） |
| 2026-09-15 | batch 490 探测 | still-broken | 第一百次重测里程碑；最新验证器点检全绿（batch 490） |
| 2026-09-15 | batch 491 探测 | still-broken | 第一百零一次重测；全量维护集运行（batch 491） |
| 2026-09-15 | batch 492 探测 | still-broken | 第一百零二次重测；jimeng 66 对照同步（batch 492） |
| 2026-09-15 | batch 493 探测 | still-broken | 第一百零三次重测；freshness 完整性确认（batch 493） |
| 2026-09-15 | batch 494 探测 | still-broken | 第一百零四次重测；全量维护集运行（batch 494） |
| 2026-09-15 | batch 495 探测 | still-broken | 第一百零五次重测；jimeng 67 对照同步 + 72/73 自行录入确认（batch 495） |
| 2026-09-15 | batch 496 探测 | still-broken | 第一百零六次重测；VR-018 Slice B 子项 + jimeng 73 自行录入确认（batch 496） |
| 2026-09-15 | batch 497 探测 | still-broken | 第一百一十三次重测；jimeng 74 对照同步（batch 497；序数按提交 ed2ae39 自记补记，行曾缺失） |
| 2026-09-14 | batch 498 探测 | still-broken | 第一百一十九次重测；10.2b 台账尾部修复——EOF 孤儿行并入去重、剔除 498–512 backfill 幻影行（batch 498） |
| 2026-09-14 | batch 499 探测 | still-broken | 第一百二十次重测；全量维护集新鲜运行 67/67（PIL 四项 21/22/26/33 经原生 shell 复跑，x86_64 父进程 subprocess 继承陷阱入 HARNESS 执行约定）（batch 499） |
| 2026-09-14 | batch 500 探测 | still-broken | 第一百二十一次重测；jimeng 96 自行录入确认 + 13/14/18/96 独立点检全绿（fixture 回写已按约定恢复）（batch 500） |
| 2026-09-14 | batch 501 探测 | still-broken | 第一百二十二次重测；VR-018 Slice B 收口——Share overlay + AgentDrawer 状态 disposition 化（batch 501） |
| 2026-09-14 | batch 502 探测 | still-broken | 第一百二十三次重测；jimeng 98 自行录入确认 + batch 501 影响面巡检（11/14/97/121/343 全绿，回写已恢复）（batch 502） |
| 2026-09-14 | batch 503 探测 | still-broken | 第一百二十四次重测；Batch History 索引修复——440–488 孤立单行表并回主表、补 14 个缺失批次行、batch478/501 目录补 README（batch 503） |
| 2026-09-14 | batch 504 探测 | still-broken | 第一百二十五次重测；VR-018 catalog 收尾——ProjectMenu 状态 disposition 化（106 回归绿，batch504 verifier PASS）（batch 504） |
| 2026-09-14 | batch 505 探测 | still-broken | 第一百二十六次重测；VR-018 全扫收口——CanvasEmptyState 芯片 disposition 化 + graph result 零反馈（batch 505） |
| 2026-09-14 | batch 506 探测 | still-broken | 第一百二十七次重测；全量维护集新鲜运行 68/68（67 liblib + jimeng1，原生 shell；回写 fixture 已恢复）；jimeng 99/100 自行录入确认（batch 506） |
| 2026-09-14 | batch 507 探测 | still-broken | 第一百二十八次重测；BIG_PICTURE §命令反馈段时效更新——VR-018 status-line 面已收口、graph connection 静默 reject 为唯一未决（BLOCKED_SOURCE）（batch 507） |
| 2026-09-14 | batch 508 探测 | still-broken | 第一百二十九次重测；TRACEABILITY TR-040 行时效化——VR-018 状态面收口 + connection 未决 + FIX fixture 维持 RUNTIME_MISSING（batch 508） |
| 2026-09-14 | batch 509 探测 | still-broken | 第一百三十次重测；VR-018 §18 完成度逐条审计——差距收敛为 connection 反馈（BLOCKED_SOURCE）+ FIX-01 确定性 fixture 两项（batch 509） |
| 2026-09-14 | batch 510 探测 | still-broken | 第一百三十一次重测；FIX-01 确定性 fixture runtime 落地（PURE_RUNTIME_RECORDED_PASS，15 场景）——§18 差距收敛为 connection 反馈一项；jimeng 101 自行录入确认（batch 510） |
| 2026-09-14 | batch 511 探测 | still-broken | 第一百三十二次重测；FIXTURE_CATALOG 状态核对审计——6 项 RUNTIME_MISSING 升级 FOCUSED_RUNTIME_PARTIAL（VR-016/017/019/021/022/023 聚焦闭环证据），其余维持（batch 511） |
| 2026-09-14 | batch 512 探测 | still-broken | 第一百三十三次重测；全量维护集新鲜运行 69/69（67 liblib + jimeng1 + batch510，覆盖 page.tsx window 挂载改动；回写已恢复）（batch 512） |
| 2026-09-14 | batch 513 探测 | still-broken | 第一百三十四次重测；VR-010 Slice A——纯 graph-document codec + §9.2 corpus 10/10（PURE_CODEC_RECORDED_PASS）（batch 513） |
| 2026-09-14 | batch 514 探测 | still-broken | 第一百三十五次重测；VR-010 Slice B——history isolation focused browser 层 4 场景；发现空栈 undo 的 viewport 回写异常（BLOCKED_SOURCE 留档）（batch 514） |
| 2026-09-14 | batch 515 探测 | still-broken | 第一百三十六次重测；VR-012 focused fixture——默认 node-data 注册表 11 类型聚焦验收（style/effect 额外分支 STATIC_FACT 留档）（batch 515） |
| 2026-09-14 | batch 516 探测 | still-broken | 第一百三十七次重测；SUBGRAPH-COPY focused fixture——duplicate 新身份/内部边重映射/外部边不剥离/一步 undo（batch 516） |
| 2026-09-14 | batch 517 探测 | still-broken | 第一百三十八次重测；GRAPH-DELETE focused fixture——plain 场景边闭合/选择失效/零残缺 undo-redo（batch 517） |
| 2026-09-14 | batch 518 探测 | still-broken | 第一百三十九次重测；GRAPH-ENTRYPOINT focused fixture——同一提案跨入口一致性（T 门拒绝零残缺 vs 命令受理一步）（batch 518） |
| 2026-09-14 | batch 519 探测 | still-broken | 第一百四十次重测；全量维护集新鲜运行 70/70（67 liblib + jimeng1 + b510 + b513；回写已恢复）；ASYNC-INGRESS 聚焦验收评估为不应做——普通画布无 run store 属如实边界非债务（batch 519） |
| 2026-09-14 | batch 520 探测 | still-broken | 第一百四十一次重测；GRAPH-DELETE 派生修复场景探证——createFirstFrameReference 在无就绪媒体下静默 no-op，确认 BLOCKED_BY_FIXTURE 入档（batch 520） |
| 2026-09-14 | batch 521 探测 | still-broken | 第一百四十二次重测；GRAPH-DELETE derived-reference 场景聚焦验收 4 场景 + **勘误 batch 520**——no-op 实为防重守卫非 fixture 门，派生场景已可驱动并已验收（batch 521） |
| 2026-09-14 | batch 522 探测 | still-broken | 第一百四十三次重测；GRAPH-DELETE shot 聚合场景聚焦验收——cohort 创建带反向引用、删除 breakdown 后 cohort 存活、零残缺 undo（batch 522） |
| 2026-09-14 | batch 523 探测 | still-broken | 第一百四十四次重测；long-video process cohort 探针确认（LongVideoProcessInput 单事务 12 节点/一步 history；删除与已验收 removeNode 合同同径未单列场景）（batch 523） |
| 2026-09-14 | batch 524 探测 | still-broken | 第一百四十五次重测；Batch History 索引增量补全——504–522 共 11 个新批次目录入索引（batch 524） |
| 2026-09-14 | batch 525 探测 | still-broken | 第一百四十六次重测；留档批次——用户下达留档暂停指令，到期维护集运行中止（下次循环重跑），中止产生的 6 个回写 fixture 已恢复（batch 525） |
| 2026-09-14 | batch 526 探测 | still-broken | 第一百四十七次重测；补跑到期全量维护集 67/67（batch 26 连跑抖动、单跑两次复绿）+ jimeng1 + b510/513/514/521/522；jimeng 111–113 已自行归档 §10（batch 526） |
| 2026-09-14 | batch 527 探测 | still-broken | 第一百四十八次重测；GRAPH-DELETE canvas 场景聚焦验收——软删快照/history 清理/相邻回退/restore 恢复；四组场景全部验收完毕（batch 527） |
| 2026-09-14 | batch 528 探测 | still-broken | 第一百四十九次重测；HARNESS 维护集权威清单扩容——fixture/聚焦验收家族 10 项（510–527）纳入基线，10/10 全绿（batch 528） |
| 2026-09-14 | batch 529 探测 | still-broken | 第一百五十次重测；全量 `npm run check` 门补跑全绿（0 errors；nvm PATH 陷阱入 HARNESS 约定）（batch 529） |
| 2026-09-14 | batch 530 探测 | still-broken | 第一百五十一次重测；jimeng 归档声明核对——82 验证器脚本计数精确吻合、编号缺口全与「观察批次无验证器」既录一致、抽样 91/92/93 全绿；整表 restore 纪律违规再现（回滚并行 PNG batch53，可由其 harness 重生成），commit message 披露（batch 530） |
| 2026-09-14 | batch 531 探测 | still-broken | 第一百五十二次重测；liblib 验证器编号缺口审计（254 个脚本）——缺口段全部对应 docs-only/观察批次与 jimeng 共号空间，最新脚本为 batch 527，无异常（batch 531） |
| 2026-09-14 | batch 532 探测 | still-broken | 第一百五十三次重测；到期全量维护集新鲜运行 78/78（67 liblib + 10 fixture 家族 + jimeng1，扩容清单首次全量执行；回写 14 项显式恢复）（batch 532） |
| 2026-09-14 | batch 533 探测 | still-broken | 第一百五十四次重测；巡检批次——并行开发者 harness 重捕获 batch80 截图进行中（WIP 保留），无新落库需同步（batch 533） |
| 2026-09-14 | batch 534 探测 | still-broken | 第一百五十五次重测；Batch History 索引补 batch 527 行（524 增量后的遗漏）（batch 534） |
| 2026-09-14 | batch 535 探测 | still-broken | 第一百五十六次重测；巡检批次——并行 harness 截图重捕获持续（batch40/80，WIP 保留），无新落库需同步（batch 535） |
| 2026-09-15 | batch 536 探测 | still-broken | 第一百五十七次重测；到期全量维护集新鲜运行 78/78；恢复清单误含并行 batch40/80 两张 WIP 截图（第三次同类违规，可由其 harness 重生成），commit 披露并重申恢复前须剔除已知并行路径（batch 536） |
| 2026-09-16 | batch 537 探测 | still-broken | 第一百五十八次重测；巡检批次——工作区净、无新落库需同步；维护集未到期（上次 batch 536）（batch 537） |
| 2026-09-16 | batch 538 探测 | still-broken | 第一百五十九次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 538） |
| 2026-09-16 | batch 539 探测 | still-broken | 第一百六十次重测；到期维护集新鲜运行 76/77——batch 26 本轮 2 败 1 过（已知媒体时序抖动族，src 自上次全绿无变更，列观察项）；并行 WIP batch85 截图按规则保留（batch 539） |
| 2026-09-16 | batch 540 探测 | still-broken | 第一百六十一次重测；batch 26 抖动观察采样——3 连败（签名实为画布下拉等待超时，非媒体时序，纠正 539 初判）+ 随后 2 次通过；与并行 harness 共用 dev server 的并发争用为最可能解释，维持观察（batch 540） |
| 2026-09-16 | batch 541 探测 | still-broken | 第一百六十二次重测；batch 26 观察续采样 2/2 通过（并行 harness 静默窗口），累计 F3P4 支持并发争用假说，维持观察；本批零回写（batch 541） |
| 2026-09-16 | batch 542 探测 | still-broken | 第一百六十三次重测；到期全量维护集新鲜运行 78/78（含 batch 26 本轮通过——静默窗口内 F 未复现）；并行 harness 8 张 PNG 静默窗口重捕获已归零，本运行 14 项回写显式恢复（batch 542） |
| 2026-09-16 | batch 543 探测 | still-broken | 第一百六十四次重测；巡检批次——并行 harness 重捕获恢复活跃（batch16 截图 WIP 保留），无新落库需同步；维护集未到期（batch 543） |
| 2026-09-16 | batch 544 探测 | still-broken | 第一百六十五次重测；batch 26 抖动根治——预水合点击落空定性 + 验证器加固（水合标记等待 + 点击重试，逆向条件 3/3 绿）入 VERIFICATION_LEDGER；维护集未到期（batch 544） |
| 2026-09-16 | batch 545 探测 | still-broken | 第一百六十六次重测；巡检批次——无新落库需同步；维护集未到期（batch 545） |
| 2026-09-16 | batch 546 探测 | still-broken | 第一百六十七次重测；巡检批次——无新落库需同步；维护集下批到期（batch 546） |
| 2026-09-16 | batch 547 探测 | still-broken | 第一百六十八次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；并行 harness 正在实时运行 liblib 回归（恢复后同批文件即时再脏），停止竞争性恢复、全部保留（batch 547） |
| 2026-09-16 | batch 548 探测 | still-broken | 第一百六十九次重测；工作区评估——18 个脏文件全部为并行回归运行的输出（7 张 jimeng 重捕获 + 11 张 liblib 回写），无本侧遗留，全部保留（batch 548） |
| 2026-09-16 | batch 549 探测 | still-broken | 第一百七十次重测；巡检批次——18 个并行脏文件仍未提交（待其自行处理），无新落库需同步；维护集未到期（batch 549） |
| 2026-09-16 | batch 550 探测 | still-broken | 第一百七十一次重测；巡检批次——并行脏文件状态不变（保留待其所有者处理）；无新落库；维护集未到期（batch 550） |
| 2026-09-16 | batch 551 探测 | still-broken | 第一百七十二次重测；巡检批次——并行脏文件状态不变；维护集下批到期（batch 551） |
| 2026-09-16 | batch 552 探测 | still-broken | 第一百七十三次重测；到期全量维护集新鲜运行 78/78；13 项 liblib 回写显式恢复（jimeng-clone-batch* 并行路径全部剔除保留）（batch 552） |
| 2026-09-16 | batch 553 探测 | still-broken | 第一百七十四次重测；巡检批次——10 个并行拥有的脏 fixture 状态不变（保留）；无新落库；维护集未到期（batch 553） |
| 2026-09-16 | batch 554 探测 | still-broken | 第一百七十五次重测；巡检批次——并行脏 fixture 状态不变；无新落库；维护集未到期（batch 554） |
| 2026-09-16 | batch 555 探测 | still-broken | 第一百七十六次重测；巡检批次——并行脏 fixture 状态不变；无新落库；维护集未到期（batch 555） |
| 2026-09-16 | batch 556 探测 | still-broken | 第一百七十七次重测；巡检批次——并行脏 fixture 状态不变；无新落库；维护集未到期（batch 556） |
| 2026-09-16 | batch 557 探测 | still-broken | 第一百七十八次重测；巡检批次——并行开发者自行提交 ec1db8a（jimeng batch 153，49–96 回归绿 + 截图刷新），10 张脏 fixture 归零；维护集下批到期（batch 557） |
| 2026-09-16 | batch 558 探测 | still-broken | 第一百七十九次重测；到期全量维护集新鲜运行 78/78；13 项 liblib 回写显式恢复（并行 6 项 jimeng-clone-batch* 路径剔除保留）（batch 558） |
| 2026-09-16 | batch 559 探测 | still-broken | 第一百八十次重测；巡检批次——6 个并行拥有路径状态不变（保留）；无新落库；维护集未到期（batch 559） |
| 2026-09-16 | batch 560 探测 | still-broken | 第一百八十一次重测；巡检批次——并行自行落库 33796ce（jimeng batch 154，1–48 回归绿 + 截图刷新），工作区归零；维护集未到期（batch 560） |
| 2026-09-16 | batch 561 探测 | still-broken | 第一百八十二次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 561） |
| 2026-09-16 | batch 562 探测 | still-broken | 第一百八十三次重测；巡检批次——工作区净、无新落库；维护集约 batch 564 到期（batch 562） |
| 2026-09-16 | batch 563 探测 | still-broken | 第一百八十四次重测；巡检批次——工作区净、无新落库；维护集下批到期（batch 563） |
| 2026-09-16 | batch 564 探测 | still-broken | 第一百八十五次重测；到期全量维护集新鲜运行 78/78；并行 harness batch53 截图 WIP 保留（batch 564） |
| 2026-09-16 | batch 565 探测 | still-broken | 第一百八十六次重测；巡检批次——并行 harness 重捕获持续（batch11/14/53/57 WIP 保留），无新落库；维护集未到期（batch 565） |
| 2026-09-16 | batch 566 探测 | still-broken | 第一百八十七次重测；巡检批次——并行 WIP 状态不变（保留）；无新落库；维护集未到期（batch 566） |
| 2026-09-16 | batch 567 探测 | still-broken | 第一百八十八次重测；到期全量维护集新鲜运行 78/78；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径全部剔除保留）（batch 567） |
| 2026-09-16 | batch 568 探测 | still-broken | 第一百八十九次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 571 到期（batch 568） |
| 2026-09-16 | batch 569 探测 | still-broken | 第一百九十次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（batch 569） |
| 2026-09-16 | batch 570 探测 | still-broken | 第一百九十一次重测；巡检批次——工作区状态不变；无新落库；维护集未到期（batch 570） |
| 2026-09-16 | batch 571 探测 | still-broken | 第一百九十二次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 576 到期（batch 571） |
| 2026-09-16 | batch 572 探测 | still-broken | 第一百九十三次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 576 到期（batch 572） |
| 2026-09-16 | batch 573 探测 | still-broken | 第一百九十五次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 576 到期（batch 573） |
| 2026-09-16 | batch 574 探测 | still-broken | 第一百九十六次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 576 到期（batch 574） |
| 2026-09-16 | batch 575 探测 | still-broken | 第一百九十七次重测；巡检批次——工作区状态不变；无新落库；维护集下批到期（batch 575） |
| 2026-09-16 | batch 576 探测 | still-broken | 第一百九十八次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）（batch 576） |
| 2026-09-16 | batch 577 探测 | still-broken | 第一百九十九次重测；巡检批次——并行重捕获持续（batch14/40/50 WIP 保留）；无新落库；维护集约 batch 582 到期（batch 577） |
| 2026-09-16 | batch 578 探测 | still-broken | 第二百次重测（里程碑）；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（batch 578） |
| 2026-09-16 | batch 579 探测 | still-broken | 第二百零一次重测；巡检批次——并行 batch14/40/50 WIP 状态不变（保留）；无新落库；维护集未到期（batch 579） |
| 2026-09-16 | batch 580 探测 | still-broken | 第二百零二次重测；巡检批次——并行 WIP 状态不变；无新落库；维护集约 batch 582 到期（batch 580） |
| 2026-09-16 | batch 581 探测 | still-broken | 第二百零三次重测；巡检批次——并行 batch14/40/50 截图重捕获新增 batch50（WIP 保留）；无新落库；维护集下批到期（batch 581） |
| 2026-09-16 | batch 582 探测 | still-broken | 第二百零四次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 582） |
| 2026-09-16 | batch 583 探测 | still-broken | 第二百零五次重测；巡检批次——并行 6 项脏 fixture 状态不变（保留）；无新落库；维护集约 batch 588 到期（batch 583） |
| 2026-09-16 | batch 584 探测 | still-broken | 第二百零六次重测；巡检批次——并行 6 项脏 fixture 状态不变（保留）；无新落库；维护集约 batch 588 到期（batch 584） |
| 2026-09-16 | batch 585 探测 | still-broken | 第二百零七次重测；巡检批次——并行 6 项脏 fixture 状态不变（保留）；无新落库；维护集约 batch 588 到期（batch 585） |
| 2026-09-16 | batch 586 探测 | still-broken | 第二百零八次重测；巡检批次——并行 6 项脏 fixture 状态不变（保留）；无新落库；维护集约 batch 588 到期（batch 586） |
| 2026-09-16 | batch 587 探测 | still-broken | 第二百零九次重测；巡检批次——并行 6 项脏 fixture 状态不变（保留）；无新落库；维护集约 batch 588 到期（batch 587） |
| 2026-09-16 | batch 588 探测 | still-broken | 第二百一十次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 588） |
| 2026-09-16 | batch 589 探测 | still-broken | 第二百一十一次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 589） |
| 2026-09-16 | batch 590 探测 | still-broken | 第二百一十二次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 590） |
| 2026-09-16 | batch 591 探测 | still-broken | 第二百一十三次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 591） |
| 2026-09-16 | batch 592 探测 | still-broken | 第二百一十四次重测；巡检批次——工作区净、无新落库；维护集约 batch 594 到期（batch 592） |
| 2026-09-16 | batch 593 探测 | still-broken | 第二百一十五次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 593） |
| 2026-09-16 | batch 594 探测 | still-broken | 第二百一十六次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 594） |
| 2026-09-16 | batch 595 探测 | still-broken | 第二百一十七次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 595） |
| 2026-09-16 | batch 596 探测 | still-broken | 第二百一十八次重测；巡检批次——工作区净、无新落库；维护集约 batch 599 到期（batch 596） |
| 2026-09-16 | batch 597 探测 | still-broken | 第二百一十九次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 599 到期（batch 597） |
| 2026-09-16 | batch 598 探测 | still-broken | 第二百二十次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集下批到期（batch 598） |
| 2026-09-16 | batch 599 探测 | still-broken | 第二百二十一次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 599） |
| 2026-09-16 | batch 600 探测 | still-broken | 第二百二十二次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集未到期（batch 600） |
| 2026-09-16 | batch 601 探测 | still-broken | 第二百二十三次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 607 到期（batch 601） |
| 2026-09-16 | batch 602 探测 | still-broken | 第二百二十四次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 607 到期（batch 602） |
| 2026-09-16 | batch 603 探测 | still-broken | 第二百二十五次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 607 到期（batch 603） |
| 2026-09-16 | batch 604 探测 | still-broken | 第二百二十六次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 607 到期（batch 604） |
| 2026-09-16 | batch 605 探测 | still-broken | 第二百二十七次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 607 到期（batch 605） |
| 2026-09-16 | batch 606 探测 | still-broken | 第二百二十八次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 606） |
| 2026-09-16 | batch 607 探测 | still-broken | 第二百二十九次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 607） |
| 2026-09-16 | batch 608 探测 | still-broken | 第二百三十次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 608） |
| 2026-09-16 | batch 609 探测 | still-broken | 第二百三十一次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 609） |
| 2026-09-16 | batch 610 探测 | still-broken | 第二百三十二次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 610） |
| 2026-09-16 | batch 611 探测 | still-broken | 第二百三十三次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 612 到期（batch 611） |
| 2026-09-16 | batch 612 探测 | still-broken | 第二百三十五次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 612） |
| 2026-09-16 | batch 613 探测 | still-broken | 第二百三十六次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 618 到期（batch 613） |
| 2026-09-16 | batch 614 探测 | still-broken | 第二百三十七次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 618 到期（batch 614） |
| 2026-09-16 | batch 615 探测 | still-broken | 第二百三十八次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 618 到期（batch 615） |
| 2026-09-16 | batch 616 探测 | still-broken | 第二百三十九次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 623 到期（batch 616） |
| 2026-09-16 | batch 617 探测 | still-broken | 第二百四十次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集未到期（batch 617） |
| 2026-09-16 | batch 618 探测 | still-broken | 第二百四十一次重测；巡检批次——并行自行落库 0405903（jimeng batch 191，1–96 全量 exit-code 回归绿 + 截图刷新），工作区归零；维护集约 batch 623 到期（batch 618） |
| 2026-09-16 | batch 619 探测 | still-broken | 第二百四十二次重测；巡检批次——工作区净、无新落库；维护集约 batch 623 到期（batch 619） |
| 2026-09-16 | batch 620 探测 | still-broken | 第二百四十三次重测；巡检批次——工作区净、无新落库；维护集约 batch 623 到期（batch 620） |
| 2026-09-16 | batch 621 探测 | still-broken | 第二百四十四次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 621） |
| 2026-09-16 | batch 622 探测 | still-broken | 第二百四十五次重测；巡检批次——工作区净、无新落库；维护集约 batch 626 到期（batch 622） |
| 2026-09-16 | batch 623 探测 | still-broken | 第二百四十六次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 623） |
| 2026-09-16 | batch 624 探测 | still-broken | 第二百四十七次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 624） |
| 2026-09-16 | batch 625 探测 | still-broken | 第二百四十八次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 625） |
| 2026-09-16 | batch 626 探测 | still-broken | 第二百四十九次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 626） |
| 2026-09-16 | batch 627 探测 | still-broken | 第二百五十次重测；巡检批次——工作区净、无新落库；维护集约 batch 632 到期（batch 627） |
| 2026-09-16 | batch 628 探测 | still-broken | 第二百五十一次重测；巡检批次——工作区净、无新落库；维护集约 batch 632 到期（batch 628） |
| 2026-09-16 | batch 629 探测 | still-broken | 第二百五十二次重测；巡检批次——工作区净、无新落库；维护集约 batch 632 到期（batch 629） |
| 2026-09-16 | batch 630 探测 | still-broken | 第二百五十三次重测；巡检批次——工作区净、无新落库；维护集约 batch 638 到期（batch 630） |
| 2026-09-16 | batch 631 探测 | still-broken | 第二百五十四次重测；巡检批次——工作区净、无新落库；维护集约 batch 638 到期（batch 631） |
| 2026-09-16 | batch 632 探测 | still-broken | 第二百五十五次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 632） |
| 2026-09-16 | batch 633 探测 | still-broken | 第二百五十六次重测；巡检批次——工作区净、无新落库；维护集约 batch 638 到期（batch 633） |
| 2026-09-16 | batch 634 探测 | still-broken | 第二百五十七次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 638 到期（batch 634） |
| 2026-09-16 | batch 635 探测 | still-broken | 第二百五十八次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 638 到期（batch 635） |
| 2026-09-16 | batch 636 探测 | still-broken | 第二百五十九次重测；巡检批次——工作区状态不变（5 项并行 WIP 保留）；无新落库；维护集约 batch 638 到期（batch 636） |
| 2026-09-16 | batch 637 探测 | still-broken | 第二百六十次重测；巡检批次——并行自行落库 jimeng 195（截取帧下拉恢复，jimeng 路线解除 BLOCKED_BY_FIXTURE）；liblib 路线仍 still-broken（batch 637） |
| 2026-09-16 | batch 638 探测 | still-broken | 第二百六十一次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 638） |
| 2026-09-16 | batch 639 探测 | still-broken | 第二百六十二次重测；巡检批次——工作区状态不变（7 项并行 WIP 保留）；无新落库；维护集约 batch 644 到期（batch 639） |
| 2026-09-16 | batch 640 探测 | still-broken | 第二百六十三次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 644 到期（batch 640） |
| 2026-09-16 | batch 641 探测 | still-broken | 第二百六十四次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 644 到期（batch 641） |
| 2026-09-16 | batch 642 探测 | still-broken | 第二百六十五次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 642） |
| 2026-09-16 | batch 643 探测 | still-broken | 第二百六十六次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 643） |
| 2026-09-16 | batch 644 探测 | still-broken | 第二百六十七次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 644） |
| 2026-09-16 | batch 645 探测 | still-broken | 第二百六十八次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 645） |
| 2026-09-16 | batch 646 探测 | still-broken | 第二百七十九次重测；巡检批次——工作区状态不变（9 项并行 WIP 保留）；无新落库；维护集未到期（batch 646） |
| 2026-09-16 | batch 647 探测 | still-broken | 第二百八十次重测；巡检批次——工作区状态不变（9 项并行 WIP 保留）；无新落库；维护集未到期（batch 647） |
| 2026-09-16 | batch 648 探测 | still-broken | 第二百八十一次重测；巡检批次——并行自行落库 jimeng 205（移除误采样截帧标记，全量 86/86 绿），工作区归零；维护集约 batch 652 到期（batch 648） |
| 2026-09-17 | batch 649 探测 | still-broken | 第二百八十二次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 649） |
| 2026-09-17 | batch 650 探测 | still-broken | 第二百九十四次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；并行自行落库 jimeng 262；无新落库需同步；维护集未到期（batch 650） |
| 2026-09-17 | batch 655 探测 | still-broken | 第二百九十五次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 661 到期（batch 655） |
| 2026-09-17 | batch 656 探测 | still-broken | 第二百九十六次重测；巡检批次——并行自行落库 jimeng 264（音频节点 Add tags 颜色标记），工作区净；维护集约 batch 664 到期（batch 656） |
| 2026-09-17 | batch 657 探测 | still-broken | 第二百九十七次重测；巡检批次——并行自行落库 jimeng 265（旋转切片 65-101 绿 25/25），工作区净；维护集未到期（batch 657） |
| 2026-09-17 | batch 658 探测 | still-broken | 第二百九十八次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 664 到期（batch 658） |
| 2026-09-17 | batch 659 探测 | still-broken | 第二百九十九次重测；巡检批次——并行自行落库 jimeng 266（drawer 芯片采样因渲染器阻塞延后 + 状态还原），工作区净；维护集约 batch 664 到期（batch 659） |
| 2026-09-17 | batch 660 探测 | still-broken | 第三百次重测（里程碑）；巡检批次——并行自行落库 jimeng 267（旋转切片 1-33 绿 33/33），工作区净；维护集未到期（batch 660） |
| 2026-09-17 | batch 661 探测 | still-broken | 第三百零一次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集未到期（batch 661） |
| 2026-09-17 | batch 668 探测 | still-broken | 第二百九十二次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 673 到期（batch 668） |
| 2026-09-17 | batch 669 探测 | still-broken | 第二百九十三次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；并行自行落库 jimeng 273（batch 255 筛选截图补充）；无新落库需同步；维护集约 batch 673 到期（batch 669） |
| 2026-09-17 | batch 662 探测 | still-broken | 第三百零二次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集未到期（batch 662） |
| 2026-09-17 | batch 663 探测 | still-broken | 第三百零三次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 668 到期（batch 663） |
| 2026-09-17 | batch 664 探测 | still-broken | 第三百零四次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 668 到期（batch 664） |
| 2026-09-17 | batch 665 探测 | still-broken | 第二百八十九次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 669 到期（batch 665） |
| 2026-09-17 | batch 666 探测 | still-broken | 第二百九十次重测；巡检批次——并行自行落库 jimeng 270（全量 1..103 绿 90 验证器 + 截图刷新），工作区净；维护集约 batch 673 到期（batch 666） |
| 2026-09-17 | batch 667 探测 | still-broken | 第二百九十一次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 673 到期（batch 667） |
| 2026-09-17 | batch 654 探测 | still-broken | 第二百九十四次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 652 到期（batch 654） |
| 2026-09-17 | batch 655 探测 | still-broken | 第二百九十五次重测；巡检批次——并行自行落库 jimeng 251（全量 1..103 绿 90 验证器 + 截图刷新），工作区净；维护集约 batch 661 到期（batch 655） |
| 2026-09-17 | batch 656 探测 | still-broken | 第二百九十六次重测；巡检批次——并行自行落库 jimeng 253（旋转切片 34-48 绿 15/15），工作区净；维护集未到期（batch 656） |
| 2026-09-17 | batch 657 探测 | still-broken | 第二百九十七次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集未到期（batch 657） |
| 2026-09-17 | batch 658 探测 | still-broken | 第二百九十八次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 664 到期（batch 658） |
| 2026-09-17 | batch 659 探测 | still-broken | 第二百九十九次重测；巡检批次——并行自行落库 jimeng 256（全量 1..103 绿 90 验证器 + 截图刷新），工作区净；维护集约 batch 664 到期（batch 659） |
| 2026-09-17 | batch 660 探测 | still-broken | 第二百八十四次重测；巡检批次——并行自行落库 jimeng 257（语言筛选下拉采样并实装），1 项 batch14 WIP 保留；无新落库需同步；维护集未到期（batch 660） |
| 2026-09-17 | batch 661 探测 | still-broken | 第二百八十五次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集未到期（batch 661） |
| 2026-09-17 | batch 662 探测 | still-broken | 第二百八十六次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 664 到期（batch 662） |
| 2026-09-17 | batch 663 探测 | still-broken | 第二百八十七次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集未到期（batch 663） |
| 2026-09-17 | batch 664 探测 | still-broken | 第二百八十八次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 668 到期（batch 664） |
| 2026-09-17 | batch 665 探测 | still-broken | 第二百八十九次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集未到期（batch 645） |
| 2026-09-17 | batch 650 探测 | still-broken | 第二百八十三次重测；巡检批次——并行自行落库 jimeng 206–208（截图解锁 + batch195 两处误读纠正），并行 WIP 保留；无新落库需同步；维护集未到期（batch 650） |
| 2026-09-17 | batch 657 探测 | still-broken | 第二百九十一次重测；巡检批次——并行自行落库 jimeng 240（全量 1..101 绿，88 验证器 + 截图刷新），工作区净；维护集未到期（batch 657） |
| 2026-09-17 | batch 658 探测 | still-broken | 第二百九十二次重测；巡检批次——工作区状态不变；无新落库；维护集约 batch 678 到期（batch 658） |
| 2026-09-17 | batch 659 探测 | still-broken | 第二百八十二次重测；巡检批次——并行自行落库 jimeng 241（文本编辑富文本工具条），工作区净；维护集未到期（batch 659） |
| 2026-09-17 | batch 660 探测 | still-broken | 第二百八十三次重测；巡检批次——并行自行落库 jimeng 242（旋转切片 65-101 绿 25/25），工作区净；维护集未到期（batch 660） |
| 2026-09-17 | batch 661 探测 | still-broken | 第二百八十四次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 661） |
| 2026-09-17 | batch 662 探测 | still-broken | 第二百八十五次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集未到期（batch 662） |
| 2026-09-17 | batch 663 探测 | still-broken | 第二百八十七次重测；巡检批次——工作区状态不变（4 项并行 WIP 保留）；无新落库；维护集未到期（batch 663） |
| 2026-09-17 | batch 664 探测 | still-broken | 第二百八十八次重测；巡检批次——并行自行落库 jimeng 244/245（全量 1..103 绿 90 验证器 + 音频生成下拉采样），工作区净；维护集未到期（batch 664） |
| 2026-09-17 | batch 651 探测 | still-broken | 第二百八十四次重测；巡检批次——工作区状态不变（10 项并行 WIP 保留）；无新落库；维护集未到期（batch 651） |
| 2026-09-16 | batch 646 探测 | still-broken | 第二百六十九次重测；巡检批次——工作区净、无新落库；维护集约 batch 652 到期（batch 646） |
| 2026-09-16 | batch 647 探测 | still-broken | 第二百七十次重测；巡检批次——工作区净、无新落库；维护集约 batch 652 到期（batch 647） |
| 2026-09-16 | batch 648 探测 | still-broken | 第二百七十一次重测；巡检批次——工作区净、无新落库；维护集约 batch 652 到期（batch 648） |
| 2026-09-16 | batch 649 探测 | still-broken | 第二百七十二次重测；巡检批次——并行自行落库 jimeng 200/201 归档（探针环境诊断 + 自定义拾取器复验延后），工作区归零；维护集未到期（batch 649） |
| 2026-09-16 | batch 650 探测 | still-broken | 第二百七十三次重测；巡检批次——并行 JimengFramePicker.tsx 编辑中（WIP 保留），维护集顺延至其落库后；无新落库（batch 650） |
| 2026-09-16 | batch 651 探测 | still-broken | 第二百七十四次重测；巡检批次——并行 harness 活动持续，维护集维持顺延；无新落库（batch 651） |
| 2026-09-16 | batch 652 探测 | still-broken | 第二百七十五次重测；静默窗口补跑全量维护集 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 652） |
| 2026-09-16 | batch 653 探测 | still-broken | 第二百七十六次重测；巡检批次——并行自行落库 jimeng 211（rail/dock 逐项验证零漂移），54 张截图刷新 WIP 保留；无新落库需同步；维护集未到期（batch 653） |
| 2026-09-16 | batch 654 探测 | still-broken | 第二百七十七次重测；巡检批次——并行自行落库 jimeng 204（自定义截帧标题采样），2 张并行截图 WIP 保留；无新落库需同步；维护集未到期（batch 654） |
| 2026-09-17 | batch 656 探测 | still-broken | 第二百七十九次重测；巡检批次——工作区净、无新落库；维护集未到期（batch 656） |
| 2026-09-17 | batch 657 探测 | still-broken | 第二百八十次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 663 到期（batch 657） |
| 2026-09-17 | batch 658 探测 | still-broken | 第二百八十一次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 658） |
| 2026-09-17 | batch 659 探测 | still-broken | 第二百八十二次重测；巡检批次——工作区状态不变（4 项并行 WIP 保留）；无新落库；维护集未到期（batch 659） |
| 2026-09-17 | batch 660 探测 | still-broken | 第二百八十三次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；无新落库；维护集未到期（batch 660） |
| 2026-09-17 | batch 661 探测 | still-broken | 第二百八十五次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 661） |
| 2026-09-17 | batch 662 探测 | still-broken | 第二百八十六次重测；巡检批次——并行自行落库 jimeng 238（文本节点 368×368 方形），工作区净；维护集未到期（batch 662） |
| 2026-09-17 | batch 644 探测 | still-broken | 第二百八十八次重测；巡检批次——工作区状态不变（10 项并行 WIP 保留）；无新落库；维护集约 batch 668 到期（batch 644） |
| 2026-09-17 | batch 645 探测 | still-broken | 第二百八十九次重测；巡检批次——并行自行落库 jimeng 246（音频生成下拉接线至采样项），工作区净；维护集未到期（batch 645） |
| 2026-09-17 | batch 646 探测 | still-broken | 第二百九十次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；并行自行落库 jimeng 260；无新落库需同步；维护集未到期（batch 646） |
| 2026-09-17 | batch 647 探测 | still-broken | 第二百九十一次重测；巡检批次——并行自行落库 jimeng 261（rail 图片插入 320×320 采样对齐），工作区净；无新落库需同步；维护集约 batch 678 到期（batch 647） |
| 2026-09-17 | batch 648 探测 | still-broken | 第二百九十二次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 678 到期（batch 648） |
| 2026-09-17 | batch 649 探测 | still-broken | 第二百九十三次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 678 到期（batch 649） |
| 2026-09-17 | batch 646 探测 | still-broken | 第二百九十次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 646） |
| 2026-09-17 | batch 647 探测 | still-broken | 第二百九十一次重测；巡检批次——并行自行落库 jimeng 248（Seed TTS 下拉采样），1 项 batch1-default WIP 保留；无新落库需同步；维护集未到期（batch 647） |
| 2026-09-17 | batch 648 探测 | still-broken | 第二百九十二次重测；巡检批次——并行自行落库 jimeng 250（声音下拉网格采样），工作区净；维护集约 batch 665 到期（batch 648） |
| 2026-09-17 | batch 649 探测 | still-broken | 第二百九十三次重测；巡检批次——工作区状态不变（2 项并行 WIP 保留）；无新落库；维护集约 batch 652 到期（batch 649） |
| 2026-09-17 | batch 645 探测 | still-broken | 第二百八十九次重测；巡检批次——工作区状态不变（5 项并行 WIP 保留）；无新落库；维护集未到期（batch 645） |
| 2026-09-17 | batch 646 探测 | still-broken | 第二百九十次重测；巡检批次——工作区状态不变（10 项并行 WIP 保留）；无新落库；维护集未到期（batch 646） |
| 2026-09-17 | batch 663 探测 | still-broken | 第二百八十七次重测；巡检批次——工作区状态不变（8 项并行 WIP 保留）；无新落库；维护集未到期（batch 663） |
| 2026-09-17 | batch 661 探测 | still-broken | 第二百八十四次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；无新落库；维护集未到期（batch 661） |
| 2026-09-17 | batch 662 探测 | still-broken | 第二百八十五次重测；巡检批次——并行自行落库 jimeng 216（提示词反推 → AI drawer 视频反解预填），工作区净；维护集约 batch 664 到期（batch 662） |
| 2026-09-17 | batch 663 探测 | still-broken | 第二百八十七次重测；巡检批次——工作区状态不变（3 项并行 WIP 保留）；无新落库；维护集约 batch 668 到期（batch 663） |
| 2026-09-17 | batch 664 探测 | still-broken | 第二百八十八次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 664） |
| 2026-09-17 | batch 665 探测 | still-broken | 第二百八十九次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；无新落库；维护集未到期（batch 665） |
| 2026-09-17 | batch 666 探测 | still-broken | 第二百九十次重测；巡检批次——并行自行落库 jimeng 220（全量 exit-code 扫 1..101 绿，87 验证器 + 截图刷新），工作区归零；维护集未到期（batch 666） |
| 2026-09-17 | batch 667 探测 | still-broken | 第二百九十一次重测；巡检批次——并行自行落库 jimeng 221（右键菜单精化），1 项并行 WIP 保留；无新落库需同步；维护集未到期（batch 667） |
| 2026-09-17 | batch 668 探测 | still-broken | 第二百九十二次重测；巡检批次——并行自行落库 jimeng 222（窗格右键菜单子菜单扩展至 10 项），工作区净；维护集约 batch 673 到期（batch 668） |
| 2026-09-17 | batch 669 探测 | still-broken | 第二百九十三次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 669） |
| 2026-09-17 | batch 670 探测 | still-broken | 第二百九十四次重测；巡检批次——工作区状态不变（5 项并行 WIP 保留）；无新落库；维护集未到期（batch 670） |
| 2026-09-17 | batch 671 探测 | still-broken | 第二百九十五次重测；巡检批次——并行自行落库 jimeng 226（redo 提示修复后全量绿 + batch 4 前缀匹配 redo），并行 WIP 保留；无新落库需同步；维护集未到期（batch 671） |
| 2026-09-17 | batch 672 探测 | still-broken | 第二百九十六次重测；巡检批次——并行自行落库 jimeng 227（搜索覆盖层对齐源站 242px），工作区净；维护集未到期（batch 672） |
| 2026-09-17 | batch 673 探测 | still-broken | 第二百九十七次重测；巡检批次——并行自行落库 jimeng 228（plus 供给菜单验证与 clone 对齐），工作区净；维护集未到期（batch 673） |
| 2026-09-17 | batch 674 探测 | still-broken | 第二百九十八次重测；巡检批次——并行自行落库 jimeng 229（旋转切片 34-48 绿 15/15），工作区净；维护集约 batch 678 到期（batch 674） |
| 2026-09-17 | batch 675 探测 | still-broken | 第二百九十九次重测；巡检批次——并行自行落库 jimeng 230（plus 菜单禁用态 + 无效连接 toast 采样），工作区净；维护集约 batch 676 到期（batch 675） |
| 2026-09-17 | batch 676 探测 | still-broken | 第三百次重测（里程碑）；巡检批次——并行自行落库 jimeng 231（无效连接 toast 无法连接这些节点），工作区净；维护集未到期（batch 676） |
| 2026-09-17 | batch 677 探测 | still-broken | 第三百零一次重测；巡检批次——工作区状态不变（6 项并行 WIP 保留）；无新落库；维护集未到期（batch 677） |
| 2026-09-17 | batch 678 探测 | still-broken | 第三百零二次重测；巡检批次——工作区状态不变（7 项并行 WIP 保留）；无新落库；维护集未到期（batch 678） |
| 2026-09-17 | batch 679 探测 | still-broken | 第三百零三次重测；巡检批次——工作区状态不变（8 项并行 WIP 保留）；无新落库；维护集未到期（batch 679） |
| 2026-09-17 | batch 680 探测 | still-broken | 第三百零四次重测；巡检批次——并行自行落库 jimeng 273（batch 255 筛选截图补充），工作区净；维护集约 batch 649 到期（batch 680） |
| 2026-09-17 | batch 681 探测 | still-broken | 第三百零五次重测；巡检批次——并行自行落库 jimeng 274（skills 弹出层采样 BLOCKED_BY_RENDERER），工作区净；维护集未到期（batch 681） |
| 2026-09-18 | batch 682 探测 | still-broken | 第三百零六次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（batch 682） |
| 2026-09-18 | batch 683 探测 | still-broken | 第三百零七次重测；巡检批次——并行自行落库 jimeng 277/278（selector aria 前缀对齐、filter 交互 BLOCKED_BY_RENDERER），工作区净；维护集未到期（batch 683） |
| 2026-09-18 | batch 684 探测 | still-broken | 第三百零八次重测；巡检批次——并行 WIP 截图 jimeng-clone-batch11-task-mock-1680.png 在途（按规则保留不动），无新落库批次；维护集未到期（batch 684） |
| 2026-09-18 | batch 685 探测 | still-broken | 第三百零九次重测；巡检批次——并行 WIP 截图仍在途（保留不动），无新落库批次；维护集未到期（batch 685） |
| 2026-09-18 | batch 686 探测 | still-broken | 第三百一十次重测；巡检批次——并行 WIP 截图仍在途（保留不动），无新落库批次；维护集未到期（batch 686，距全量约 3 批） |
| 2026-09-18 | batch 687 探测 | still-broken | 第三百一十一次重测；巡检批次——并行 WIP 截图增至两张（batch11/batch40，保留不动），无新落库批次；维护集未到期（batch 687，距全量约 2 批） |
| 2026-09-18 | batch 688 探测 | still-broken | 第三百一十二次重测；巡检批次——并行 WIP 截图两张仍在途（保留不动），无新落库批次；下批（batch 689）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 689 探测 | still-broken | 第三百一十三次重测；到期全量维护集新鲜运行 78/78（13 项 liblib 回写按显式路径恢复；并行自行落库 jimeng 279——exit-code sweep 1..103 全绿 90 验证器+截图刷新，batch 280 WIP 截图与 README 在途均保留不动）（batch 689） |
| 2026-09-18 | batch 690 探测 | still-broken | 第三百一十四次重测；巡检批次——并行 batch 280（renderer recovered、hover 截图零漂移）已由其自行推送，无 batch 281；工作区净；维护集未到期（batch 690，距全量约 6 批） |
| 2026-09-18 | batch 691 探测 | still-broken | 第三百一十五次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 691，距全量约 5 批） |
| 2026-09-18 | batch 692 探测 | still-broken | 第三百一十六次重测；巡检批次——并行自行落库 jimeng 281（rotation slice 20-33 绿 14/14），工作区净；维护集未到期（batch 692，距全量约 4 批） |
| 2026-09-18 | batch 693 探测 | still-broken | 第三百一十七次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 693，距全量约 3 批） |
| 2026-09-18 | batch 694 探测 | still-broken | 第三百一十八次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 694，距全量约 2 批） |
| 2026-09-18 | batch 695 探测 | still-broken | 第三百一十九次重测；巡检批次——并行 WIP JimengAudioGenPanel.tsx 在途（保留不动），无新落库批次；下批（batch 696）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 696 探测 | still-broken | 第三百二十次重测；到期全量维护集新鲜运行 78/78（20 项回写按显式路径恢复，batch1 截图按并行路径剔除恢复；并行自行落库 jimeng 282/283——gender filter 生效、age=老年 4 音色，工作区净）（batch 696） |
| 2026-09-18 | batch 697 探测 | still-broken | 第三百二十一次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 697，距全量约 6 批） |
| 2026-09-18 | batch 698 探测 | still-broken | 第三百二十二次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 698，距全量约 5 批） |
| 2026-09-18 | batch 699 探测 | still-broken | 第三百二十三次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 699，距全量约 4 批） |
| 2026-09-18 | batch 700 探测 | still-broken | 第三百二十四次重测；巡检批次——无并行新落库（jimeng 284 之后无新增），工作区净；维护集未到期（batch 700，距全量约 3 批） |
| 2026-09-18 | batch 701 探测 | still-broken | 第三百二十五次重测；巡检批次——并行 WIP JimengAudioGenPanel.tsx 在途（保留不动），无新落库批次；维护集未到期（batch 701，距全量约 2 批） |
| 2026-09-18 | batch 702 探测 | still-broken | 第三百二十六次重测；巡检批次——并行自行落库 jimeng 285（语言=英文 8 音色 + lang filter），WIP 已吸收，工作区净；下批（batch 703）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 703 探测 | still-broken | 第三百二十七次重测；到期全量维护集新鲜运行 78/78（11 项回写按显式路径恢复，batch1 截图按并行路径剔除恢复；并行自行落库 jimeng 286——适合口播维度 8 新音色目录 ≥52，其新 WIP 在途保留不动）（batch 703） |
| 2026-09-18 | batch 704 探测 | still-broken | 第三百二十八次重测；巡检批次——并行自行落库 jimeng 287（中文方言音色采样与实现），WIP 已吸收，工作区净；维护集未到期（batch 704，距全量约 6 批） |
| 2026-09-18 | batch 705 探测 | still-broken | 第三百二十九次重测；巡检批次——并行 WIP 截图 batch11-task-mock 在途（保留不动），无新落库批次；维护集未到期（batch 705，距全量约 5 批） |
| 2026-09-18 | batch 706 探测 | still-broken | 第三百三十次重测；巡检批次——并行 WIP 截图仍在途（保留不动），无新落库批次；维护集未到期（batch 706，距全量约 4 批） |
| 2026-09-18 | batch 707 探测 | still-broken | 第三百三十一次重测；巡检批次——并行 WIP 截图仍在途（保留不动），无新落库批次；维护集未到期（batch 707，距全量约 3 批） |
| 2026-09-18 | batch 708 探测 | still-broken | 第三百三十二次重测；巡检批次——并行 WIP 截图仍在途（保留不动），无新落库批次；维护集未到期（batch 708，距全量约 2 批） |
| 2026-09-18 | batch 709 探测 | still-broken | 第三百三十三次重测；巡检批次——并行 batch 288 已落库吸收 WIP，工作区净；下批（batch 710）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 710 探测 | still-broken | 第三百三十四次重测；到期全量维护集新鲜运行 78/78（15 项回写按显式路径恢复，batch1 截图按并行路径剔除恢复；并行自行落库 jimeng 289——voice grid 分页验证零漂移，工作区净）（batch 710） |
| 2026-09-18 | batch 711 探测 | still-broken | 第三百三十五次重测；巡检批次——并行自行落库 jimeng 290（rotation slices 49-64 + 65-101 绿 39/39），工作区净；维护集未到期（batch 711，距全量约 6 批） |
| 2026-09-18 | batch 712 探测 | still-broken | 第三百三十六次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 712，距全量约 5 批） |
| 2026-09-18 | batch 713 探测 | still-broken | 第三百三十七次重测；巡检批次——并行自行落库 jimeng 291（rotation 34-48 绿 15/15 + 工具栏演化扫描零漂移），工作区净；维护集未到期（batch 713，距全量约 4 批） |
| 2026-09-18 | batch 714 探测 | still-broken | 第三百三十八次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 714，距全量约 3 批） |
| 2026-09-18 | batch 715 探测 | still-broken | 第三百三十九次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 715，距全量约 2 批） |
| 2026-09-18 | batch 716 探测 | still-broken | 第三百四十次重测；巡检批次——并行自行落库 jimeng 292（rotation 1-19/20-33 重跑后绿 33/33），工作区净；下批（batch 717）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 717 探测 | still-broken | 第三百四十一次重测；到期全量维护集新鲜运行 78/78（15 项回写按显式路径恢复，batch1/batch19 两张截图按并行路径剔除恢复；并行自行落库 jimeng 293——audio gen 面板高度 196、Current price 1.1，工作区净）（batch 717） |
| 2026-09-18 | batch 718 探测 | still-broken | 第三百四十二次重测；巡检批次——并行 WIP JimengAudioGenPanel.tsx 在途（保留不动），无新落库批次；维护集未到期（batch 718，距全量约 6 批） |
| 2026-09-18 | batch 719 探测 | still-broken | 第三百四十三次重测；巡检批次——并行 WIP 仍在途（保留不动），无新落库批次；维护集未到期（batch 719，距全量约 5 批） |
| 2026-09-18 | batch 720 探测 | still-broken | 第三百四十四次重测；巡检批次——并行 WIP 仍在途（保留不动），无新落库批次；维护集未到期（batch 720，距全量约 4 批） |
| 2026-09-18 | batch 721 探测 | still-broken | 第三百四十五次重测；巡检批次——并行 WIP 三件（组件/截图/README）仍在途（保留不动），无新落库批次；维护集未到期（batch 721，距全量约 3 批） |
| 2026-09-18 | batch 722 探测 | still-broken | 第三百四十六次重测；巡检批次——并行 batch 294 已落库吸收组件/README WIP，仅剩 batch19 截图 WIP 在途（保留不动）；维护集未到期（batch 722，距全量约 2 批） |
| 2026-09-18 | batch 723 探测 | still-broken | 第三百四十七次重测；巡检批次——并行 WIP 组件+截图在途（保留不动），无新落库批次；下批（batch 724）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 724 探测 | still-broken | 第三百四十八次重测；到期全量维护集新鲜运行 78/78（13 项回写按显式路径恢复，batch1/batch19 截图按并行路径剔除恢复；并行自行落库 jimeng 295/296——SeedMusic 模型下拉、时长分段选择器，均按新鲜采样，工作区净）（batch 724） |
| 2026-09-18 | batch 725 探测 | still-broken | 第三百四十九次重测；巡检批次——并行 batch 297 WIP 四件在途（组件/截图/README/price-diff.json，保留不动），无新落库批次；维护集未到期（batch 725，距全量约 6 批） |
| 2026-09-18 | batch 726 探测 | still-broken | 第三百五十次重测；巡检批次——并行 batch 297 已落库吸收四件 WIP，仅剩 batch19 截图 WIP 在途（保留不动）；维护集未到期（batch 726，距全量约 5 批） |
| 2026-09-18 | batch 727 探测 | still-broken | 第三百五十一次重测；巡检批次——并行自行落库 jimeng 298（duration→price 映射不确定：合成点击受限），batch19 截图 WIP 仍在途（保留不动）；维护集未到期（batch 727，距全量约 4 批） |
| 2026-09-18 | batch 728 探测 | still-broken | 第三百五十二次重测；巡检批次——无并行新落库，batch19 截图 WIP 仍在途（保留不动）；维护集未到期（batch 728，距全量约 3 批） |
| 2026-09-18 | batch 729 探测 | still-broken | 第三百五十三次重测；巡检批次——无并行新落库，batch19 截图 WIP 仍在途（保留不动）；维护集未到期（batch 729，距全量约 2 批） |
| 2026-09-18 | batch 730 探测 | still-broken | 第三百五十四次重测；巡检批次——无并行新落库，batch19 截图 WIP 仍在途（保留不动）；下批（batch 731）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 731 探测 | still-broken | 第三百五十五次重测；到期全量维护集新鲜运行 78/78（19 项回写按显式路径恢复，其中 4 张 batch1/19/20/40 截图按并行路径剔除恢复；并行自行落库 jimeng 299——duration→price 映射 BLOCKED_BY_INTERACTION，工作区净）（batch 731） |
| 2026-09-18 | batch 732 探测 | still-broken | 第三百五十六次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 732，距全量约 6 批） |
| 2026-09-18 | batch 733 探测 | still-broken | 第三百五十七次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 733，距全量约 5 批） |
| 2026-09-18 | batch 734 探测 | still-broken | 第三百五十八次重测；巡检批次——并行自行落库 jimeng 300 里程碑（sweep 1..103 全绿 90 验证器 + §10 快照刷新至 batch-300 态），工作区净；维护集未到期（batch 734，距全量约 4 批） |
| 2026-09-18 | batch 735 探测 | still-broken | 第三百五十九次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 735，距全量约 3 批） |
| 2026-09-18 | batch 736 探测 | still-broken | 第三百六十次重测；巡检批次——并行 batch 301 WIP 四件在途（组件/截图/README/evolution-scan.json，保留不动），无新落库批次；维护集未到期（batch 736，距全量约 2 批） |
| 2026-09-18 | batch 737 探测 | still-broken | 第三百六十一次重测；巡检批次——并行自行落库 jimeng 301（audio 面板占位/高度随生成模式自适应），仅剩 batch19 截图 WIP 在途（保留不动）；下批（batch 738）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 738 探测 | still-broken | 第三百六十二次重测；到期全量维护集新鲜运行 78/78（15 项回写按显式路径恢复，batch1/batch19 截图按并行路径剔除恢复；并行自行落库 jimeng 302 双模式 gen 面板验证器 105 + 303 工具栏演化扫描零漂移，工作区净）（batch 738） |
| 2026-09-18 | batch 739 探测 | still-broken | 第三百六十三次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 739，距全量约 6 批） |
| 2026-09-18 | batch 740 探测 | still-broken | 第三百六十四次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 740，距全量约 5 批） |
| 2026-09-18 | batch 741 探测 | still-broken | 第三百六十五次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 741，距全量约 4 批） |
| 2026-09-18 | batch 742 探测 | still-broken | 第三百六十六次重测；巡检批次——并行 WIP 两件（verify-jimeng-batch19 验证器/audio 面板组件，保留不动），无新落库批次；维护集未到期（batch 742，距全量约 3 批） |
| 2026-09-18 | batch 743 探测 | still-broken | 第三百六十七次重测；巡检批次——并行 WIP 三件仍在途（保留不动），无新落库批次；维护集未到期（batch 743，距全量约 2 批） |
| 2026-09-18 | batch 744 探测 | still-broken | 第三百六十八次重测；巡检批次——并行 WIP 三件仍在途（保留不动），无新落库批次；下批（batch 745）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 745 探测 | still-broken | 第三百六十九次重测；到期全量维护集新鲜运行 78/78（15 项回写按显式路径恢复，batch1/105/19 三张截图按并行路径剔除恢复；并行自行落库 jimeng 305——验证器 105 适配 overlay 占位机制，工作区净）（batch 745） |
| 2026-09-18 | batch 746 探测 | still-broken | 第三百七十次重测；巡检批次——并行 batch53 截图 WIP 在途（保留不动），无新落库批次；维护集未到期（batch 746，距全量约 6 批） |
| 2026-09-18 | batch 747 探测 | still-broken | 第三百七十一次重测；巡检批次——并行 WIP 截图增至两张（batch53/batch63，保留不动），无新落库批次；维护集未到期（batch 747，距全量约 5 批） |
| 2026-09-18 | batch 748 探测 | still-broken | 第三百七十二次重测；巡检批次——并行 WIP 截图增至三张（batch53/batch63/batch96，保留不动），无新落库批次；维护集未到期（batch 748，距全量约 4 批） |
| 2026-09-18 | batch 749 探测 | still-broken | 第三百七十三次重测；巡检批次——并行自行落库 jimeng 306（audio 面板 overlay 变更后 rotation 49-64 + 65-101 绿 39/39），README WIP 已吸收，三张截图 WIP 仍在途（保留不动）；维护集未到期（batch 749，距全量约 3 批） |
| 2026-09-18 | batch 750 探测 | still-broken | 第三百七十四次重测；巡检批次——无并行新落库，三张截图 WIP 仍在途（保留不动）；维护集未到期（batch 750，距全量约 2 批） |
| 2026-09-18 | batch 751 探测 | still-broken | 第三百七十五次重测；巡检批次——并行 WIP 截图增至四张（batch105/batch53/batch63/batch96，保留不动），无新落库批次；下批（batch 752）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 752 探测 | still-broken | 第三百七十六次重测；到期全量维护集新鲜运行 78/78（17 项回写按显式路径恢复，batch1/105/19/20/76 五张截图按并行路径剔除恢复；无并行新落库，工作区净）（batch 752） |
| 2026-09-18 | batch 753 探测 | still-broken | 第三百七十七次重测；巡检批次——并行自行落库 jimeng 307（exit-code sweep 1..103 全绿 91 验证器含 105 + 截图刷新），工作区净；维护集未到期（batch 753，距全量约 6 批） |
| 2026-09-18 | batch 754 探测 | still-broken | 第三百七十八次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 754，距全量约 5 批） |
| 2026-09-18 | batch 755 探测 | still-broken | 第三百七十九次重测；巡检批次——并行自行落库 jimeng 308（contenteditable 微状态 BLOCKED），工作区净；维护集未到期（batch 755，距全量约 4 批） |
| 2026-09-18 | batch 756 探测 | still-broken | 第三百八十次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 756，距全量约 3 批） |
| 2026-09-18 | batch 757 探测 | still-broken | 第三百八十一次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 757，距全量约 2 批） |
| 2026-09-18 | batch 758 探测 | still-broken | 第三百八十二次重测；巡检批次——并行自行落库 jimeng 309（audio 面板重采样零漂移，music mode 保持），工作区净；下批（batch 759）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 759 探测 | still-broken | 第三百八十三次重测；到期全量维护集新鲜运行 78/78（15 项回写按显式路径恢复，batch1/73 两张截图按并行路径剔除恢复；并行自行落库 jimeng 310——rotation 34-48 + 65-101 绿 40/40，工作区净）（batch 759） |
| 2026-09-18 | batch 760 探测 | still-broken | 第三百八十四次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 760，距全量约 6 批） |
| 2026-09-18 | batch 761 探测 | still-broken | 第三百八十五次重测；巡检批次——并行 WIP 截图两件（batch19/batch20，保留不动），无新落库批次；维护集未到期（batch 761，距全量约 5 批） |
| 2026-09-18 | batch 762 探测 | still-broken | 第三百八十六次重测；巡检批次——并行自行落库 jimeng 311（rotation 1-33 + 49-64 绿 47/47），两张截图 WIP 仍在途（保留不动）；维护集未到期（batch 762，距全量约 4 批） |
| 2026-09-18 | batch 763 探测 | still-broken | 第三百八十七次重测；巡检批次——无并行新落库，两张截图 WIP 仍在途（保留不动）；维护集未到期（batch 763，距全量约 3 批） |
| 2026-09-18 | batch 764 探测 | still-broken | 第三百八十八次重测；巡检批次——无并行新落库，两张截图 WIP 仍在途（保留不动）；维护集未到期（batch 764，距全量约 2 批） |
| 2026-09-18 | batch 765 探测 | still-broken | 第三百八十九次重测；巡检批次——并行自行落库 jimeng 312（三表面演化扫描零漂移），两张截图 WIP 仍在途（保留不动）；下批（batch 766）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 766 探测 | still-broken | 第三百九十次重测；到期全量维护集新鲜运行 78/78（20 项回写按显式路径恢复，batch1/11/19/20 四张截图按并行路径剔除恢复；无并行新落库，工作区净）（batch 766） |
| 2026-09-18 | batch 767 探测 | still-broken | 第三百九十一次重测；巡检批次——并行自行落库 jimeng 313（rotation 1-33 + 65-101 绿 58/58），工作区净；维护集未到期（batch 767，距全量约 6 批） |
| 2026-09-18 | batch 768 探测 | still-broken | 第三百九十二次重测；巡检批次——并行 batch20 截图 WIP 在途（保留不动），无新落库批次；维护集未到期（batch 768，距全量约 5 批） |
| 2026-09-18 | batch 769 探测 | still-broken | 第三百九十三次重测；巡检批次——并行 WIP 截图两件（batch20/batch40，保留不动），无新落库批次；维护集未到期（batch 769，距全量约 4 批） |
| 2026-09-18 | batch 770 探测 | still-broken | 第三百九十四次重测；巡检批次——并行自行落库 jimeng 314（rotation 20-48 绿 29/29），两件截图 WIP 仍在途（保留不动）；维护集未到期（batch 770，距全量约 3 批） |
| 2026-09-18 | batch 771 探测 | still-broken | 第三百九十五次重测；巡检批次——无并行新落库，两件截图 WIP 仍在途（保留不动）；维护集未到期（batch 771，距全量约 2 批） |
| 2026-09-18 | batch 772 探测 | still-broken | 第三百九十六次重测；巡检批次——并行 WIP 截图三件（batch19/batch20/batch40，保留不动），无新落库批次；下批（batch 773）执行到期全量维护集新鲜运行 |
| 2026-09-18 | batch 773 探测 | still-broken | 第三百九十七次重测；到期全量维护集新鲜运行 78/78（18 项回写按显式路径恢复，batch1/19/20/40 四张截图按并行路径剔除恢复；并行自行落库 jimeng 315/316——rotation 1-19 + 65-101 绿 44/44、三表面扫描零漂移，工作区净）（batch 773） |
| 2026-09-18 | batch 774 探测 | still-broken | 第三百九十八次重测；巡检批次——无并行新落库，工作区净；维护集未到期（batch 774，距全量约 6 批） |
| 2026-09-18 | batch 775 探测 | still-broken | 第三百九十九次重测；巡检批次——无并行新落库，并行截图 WIP 三件（batch105/19/20，保留不动）；维护集未到期（batch 775，距全量约 5 批） |
| 2026-09-18 | batch 776 探测 | still-broken | 第四百次重测；巡检批次——无并行新落库，截图 WIP 增至五件（batch105/19/20/40/50，保留不动）；维护集未到期（batch 776，距全量约 4 批） |
| 2026-09-17 | batch 680 探测 | still-broken | 第三百零四次重测；巡检批次——并行自行落库 jimeng 232（全量 1..101 绿 + 截图刷新），工作区净；维护集未到期（batch 680） |
| 2026-09-16 | batch 645 探测 | still-broken | 第二百七十八次重测；到期全量维护集新鲜运行 78/78（batch 26 扫内通过）；仅 liblib 路径回写恢复（jimeng-clone-batch* 并行路径剔除保留）（batch 645） |

序列说明：batch 397–414 行使用序列 A（batch 413-414 = 第三十一、三十二次）；
batch 416 起各批 commit message 改用序列 B（batch 416 = 第二十四次 …
batch 432 = 第四十次）。两序列不连续是历史标注误差——每次心跳批次恰好
执行一次探测、结果全部 still-broken，绝对次数以提交链为准。本表后续行
沿用序列 B 继续计数。

2026-09-14 台账修复（batch 498）：文件尾曾堆积一段追加在 §10.3 之后的孤儿行
（batch 461–512 区间，含重复副本与计数冲突），已并入上表去重。其中
batch 498–512 的行来自 backfill 预登记提交（0eb82d6、aab2888），提交链中
不存在对应循环批次提交，全部剔除；batch 497 的序数按提交 ed2ae39 自记的
113th 补记（该提交只改了 jimeng README，台账行曾缺失）。114th–118th 在
台账与提交链中均无痕迹，按心跳指令流计数保留序数空缺，119th 锚定于
batch 498（本批）。历史行内 82nd–84th 等零星序数空缺为早期标注误差，
不再回填。

### 10.3 复测触发条件

任意后续批次在批次开头运行
`~/.venvs/liblib-harness/bin/python scripts/probe-source-recovery.py`
（仓库内归档脚本；输出 `RECOVERY: menu-opens` 即恢复，仍为
`still-broken` 则继续等待），恢复后按 §8 checklist 补采。
