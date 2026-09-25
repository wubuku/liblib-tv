# ITERATION LOG — TDCanvas 调研包维护史

本文件记录调研包的版本演进、每轮迭代的方法与覆盖面、以及下一轮证据队列。目标协议：持续迭代改进，直到用户喊停。

## v1 — 2026-09-26（首轮落档）

**方法**：锁定提交 `16b3127`（upstream master，2026-09-15，v0.14.0）的干净工作树；5 个并行专题只读调研（渲染内核 / 状态与持久化 / 节点体系 / 交互与生成流 / Agent 与插件），全部结论带 file:line 证据；随后落档本包。

**交付物**：
- README.md（锚点 + Read Order + 结论摘要）
- REPORT.md（面向决策的完整结论）
- SOURCE_ANALYSIS.md（7 章：版本锚点/渲染内核/状态与持久化/节点体系/交互与生成流/Agent 通道/插件与 comfyui-local/证据边界）
- PATTERN_CARDS.md（TD-01..15 模式卡）
- ADOPTION_DECISION_MATRIX.md（20 行采纳矩阵）
- ITERATION_LOG.md（本文件）

**已知覆盖面缺口（按价值排序）**：
1. `chatSessions` 画布 AI 助手会话：数据模型已进项目文档，但助手面板（local-agent-panel 之外）的交互细节未深挖。
2. canvas-home 首页（项目列表页）UI 结构、i18n 双语机制、`CanvasRefreshShell` 挂载细节。
3. `use-canvas-ui-store`/素材库（assets store 全 API）、提示词库（prompt source store）。
4. Rust 侧 lib.rs 全量命令面（除 media_cache 外：窗口、updater、本地文件 reveal 等）。
5. 与上游 `basketikun/infinite-canvas` 的 diff（继承 vs 原创归属）——需要先 clone 上游。

**证据边界声明**：全部为静态源码阅读；未运行应用；行号随上游演进老化。

## 下一证据队列（带停止条件）

| # | 动作 | 产出 | 停止条件 |
|---|---|---|---|
| Q1 | clone `basketikun/infinite-canvas` 为 `research/upstream/infinite-canvas` submodule，diff `16b3127` | UPSTREAM_DIFF_AUDIT.md：机制归属表（继承/改造/新增） | 归属表覆盖 PATTERN_CARDS 全部 15 卡 |
| Q2 | 深挖 chatSessions/助手面板 | SOURCE_ANALYSIS §2 增补 + 交互目录条目 | 面板事件流与数据写回路径闭环 |
| Q3 | 首页/资产库/提示词库/侧栏盘点 | SOURCE_ANALYSIS 增补章 | 全部用户可达 surface 有 file:line 条目 |
| Q4 | Rust 命令面盘点 | 附录表 | invoke() 调用点全部映射到 lib.rs command |
| Q5 | 若上游发新版本：按 UPSTREAM_VERSION_IMPACT 协议（借鉴 open-canvas 包同名片）重审主张 | 版本影响审计 | claims 重核完成 |

## v2 — 2026-09-26（上游归属审计 + 周边表面补遗）

**动作与产出**：
1. **上游 diff 审计**（ITERATION_LOG v1 Q1 提前完成）：浅克隆 `basketikun/infinite-canvas` main（基准 `dab19ad`，2026-09-23，v0.19.0——**比 TDCanvas v0.14.0 更新**）到 /tmp 做机械对照，落档 [UPSTREAM_DIFF_AUDIT.md](UPSTREAM_DIFF_AUDIT.md)。关键修正：node-registry/plugin-loader/小地图逐字节相同（继承）；Agent 通道/Group/主题/i18n/wheel=zoom 承自上游；任务状态机、批量堆叠、图片历史、objectReferences、对齐辅助线、氛围层、Aitudou、Tauri/comfyui 为 TDCanvas 原创；上游独有 `canvas-selection-toolbar`、`canvas-node-reference-bar`（Group 资源集合）、`canvas-proxy`、Space=临时工具（被 TDCanvas 移除）。PATTERN_CARDS 的归属表述以审计表为准。
2. **周边表面补遗**（v1 Q2/Q3/Q4 完成）：SOURCE_ANALYSIS 新增 §8——chatSessions 证实为**无 UI 遗留子系统**（数据链全就绪、零聊天 UI，真实助手走 agent 面板）；首页/showcase/preview、资产库（五路存为资产入口）、提示词库（无内置预设源、TTL 1h 缓存）、侧栏 canvas tab、Rust 命令面（7 个命令）、i18n（canvas 段 ≈540 key）、图片预览仅为纯 Modal（编辑器视口 hook 服务于三个对话框）。

**结论修订**：REPORT.md §6 的「上游归属未证实」已解决；`chatSessions` 从「待深挖」改为「已定性为遗留子系统」。

**剩余缺口（v3 候选队列）**：
1. 上游 `infinite-canvas` 自身作为独立研究对象（selection-toolbar 多选浮动工具条、canvas-proxy BYOK 渠道、Group 资源集合、prompt-source OpenAI 兼容层；上游 v0.19.0 可能还有 TDCanvas 没有的新机制）——是否立项等用户决定。
2. TDCanvas 与上游的 `project.tsx`/`canvas-node.tsx` 逐段 diff（3456/955 行差异的语义分类，当前只做了机制级归属）。
3. 运行时审计（启动 desktop:dev 或 web dev，采样 DOM/网络/交互手感）——需要用户环境授权。

## v3 — 2026-09-26（引用抽检 + 交互目录）

1. **引用质量抽检**：对包内 12 处跨文件关键引用（wheel handler、Space 禁用、10000×10000 SVG、280px 裁剪、persist 防抖、history `slice(-49)`、端口等分公式、`MAX_CANVAS_IMAGE_HISTORY=24`、`MAX_MEDIA_BYTES` 1GB、phase 枚举、`DEFAULT_PORT=17371`、插件 Blob import）逐一 `sed -n` 比对原文，**12/12 一致**。
2. **新增 [INTERACTION_CATALOG.md](INTERACTION_CATALOG.md)**：6 组交互表（视口手势 10 项 / 节点生命周期 18 项 / 连线与引用 7 项 / 生成工作流 12 项 / 周边表面 9 项）+ 键盘快捷键全表，每项带触发→行为→file:line→clone 相关性分级。

**剩余缺口（v4 候选队列）**：
1. 上游 `infinite-canvas` 自身作为独立研究对象（selection-toolbar 多选浮动工具条、canvas-proxy BYOK 渠道、Group 资源集合、prompt-source OpenAI 兼容层；上游 v0.19.0 可能还有 TDCanvas 没有的新机制）——是否立项等用户决定。
2. TDCanvas 与上游的 `project.tsx`/`canvas-node.tsx` 逐段 diff（3456/955 行差异的语义分类，当前只做了机制级归属）。
3. 运行时审计（启动 desktop:dev 或 web dev，采样 DOM/网络/交互手感）——需要用户环境授权。

## v4 — 2026-09-26（diff 语义分类 + 上游独有机制 + 二轮引用抽检）

1. **逐文件语义分类**（v2/v3 队列 #2）：`project.tsx`（3456 行差异）与 `canvas-node.tsx`（955 行）全量 hunk 关键词粗分类 + 最大连续块人工判读，落档 UPSTREAM_DIFF_AUDIT §4。要点：Aitudou 管线 +495 行大块纯新增；批量 UI 约 425+115 行；objectReferences 替换上游 Group 引用逻辑；图片历史为纯新增。
2. **上游独有机制速览**（UPSTREAM_DIFF_AUDIT §5）：canvas-proxy（npm 本地 CORS 转发）、Group 资源集合展平（`getGroupResourceNodes`）、Space/Ctrl 临时工具、model-plugin 用户自建模插件模板——TDCanvas 移除/替换的四个上游机制。
3. **二轮引用抽检**：§8 补遗的 9 处引用逐一比对，**9/9 一致**（累计 21/21）。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项；② 运行时审计（需启动用户环境授权）。

## v5 — 2026-09-26（上游独有机制逐个深化 + 三轮引用抽检）

1. **§5 深化为逐机制完整分析**（4 个机制，全部精读源文件后落档，见 UPSTREAM_DIFF_AUDIT §5.1-5.4）：
   - **canvas-selection-toolbar**（85 行全文）：仅 Group/Ungroup 两按钮的多选工具条 + 虚线包围盒双重视觉；接线三入口（工具条/右键/Cmd+G±Shift）；分组操作族六函数（包裹矩形顶部留标题 padding、扁平化嵌套组、空组 GC、选中还原）；TD 对比：删除组件与 Cmd+G，分组改为「先建空组再拖入」。
   - **canvas-proxy**（132 行全文）：目标内嵌路径协议（decodeURI+`//`修复+https 校验）、双向头剥离清单、宽松 CORS 注入、SSE 逐块透传与断连 destroy、状态即打日志、502/版本 JSON；客户端 `withLocalProxy`（use-config-store.ts:490）挂接点；TD 以 Tauri http + media_cache 中继替代。
   - **Group 资源集合**（147 行全文）：`resourceKind` 资格 → `getGroupResourceNodes` 成员筛选 → `isCanvasReferenceNode` 连线资格 → `expandGroupResourceNodes` 展平去重 → Config 路由优先的三级解析管线 → 「图片 N」标签序列化 → `resolveCanvasReferenceImages` dataUrl 化；TD 对比：Config 路由保留、组展平删除（objectReferences 替代）、Group 退回纯视觉容器。
   - **model-plugin**（993 行骨架+关键段）：`new Function` 17 参数无沙箱执行（apiKey 入作用域）、http/request/poll/sleep/signal/onDelta 注入运行时、17 变量能力 scoping 文档、**8 模板 = 4 能力 × {OpenAI, Gemini}**；TD 以固定 Aitudou 后端替换、失去 BYOK 脚本层。
2. **第三轮引用抽检**：对本轮新写入的 15 处引用逐一 `sed` 比对，**15/15 一致**（三轮累计 36/36）。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项（§5 已覆盖其四个独有机制，独立包可聚焦剩余面：selection 体系其余部分、prompt-source 运行时、Docker 部署形态等）；② 运行时审计（需启动用户环境授权）。

## v6 — 2026-09-26（第四轮引用抽检：INTERACTION_CATALOG 全量覆盖）

- **范围**：INTERACTION_CATALOG.md 六张交互表中前三轮未抽检的全部条目 + 快捷键全表（guard `:1737-1739` 与键位分支 `:1744/:1746/:1753/:1759/:1768/:1774/:1780/:1788/:1807`）+ §4 生成管线 12 处（含 `pollAitudouSubmission :567`、`confirmStopAitudouPolling :2353`、`createAitudouOutputNode :4081`、输出签名去重 `:2096`、journal `:71`、反推提示词 `:2462` 等）。
- **结果**：79/79 命中，**零行号漂移，无需修正**。一处复核确认：`canvas-resource-references.ts:174-190` 的 pinned 语义由 `resolveCanvasObjectReferenceResource` 内 `:176`（`versionMode==="pinned"` 查 imageHistory）实现，原表述准确。
- **抽检台账（累计）**：v1 期 12 + v2 期 9 + v5 期 15 + v6 期 79 = **115 处，四轮 100% 一致**；INTERACTION_CATALOG 头部已标注抽检状态。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项；② 运行时审计（需启动用户环境授权）。

## 维护记录

- 2026-09-26 v1：首轮落档（5 专题并行调研 + 6 文档）。
- 2026-09-26 v2：上游归属审计（UPSTREAM_DIFF_AUDIT.md）+ 周边表面补遗（SOURCE_ANALYSIS §8）+ 结论修订。
- 2026-09-26 v3：引用抽检 12/12 通过 + INTERACTION_CATALOG.md（56 项交互 + 快捷键全表）。
- 2026-09-26 v4：diff 语义分类（§4）+ 上游独有机制速览（§5）+ 二轮引用抽检 9/9。
- 2026-09-26 v5：§5 深化为 §5.1-5.4 逐机制完整分析（四个源文件精读）+ 三轮引用抽检 15/15（累计 36/36）。
- 2026-09-26 v6：第四轮引用抽检 INTERACTION_CATALOG 全量 79/79 零漂移（累计 115 处），目录头部标注抽检台账。
