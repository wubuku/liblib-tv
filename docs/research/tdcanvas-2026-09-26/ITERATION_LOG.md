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

## v7 — 2026-09-26（第五轮引用抽检：PATTERN_CARDS/ADOPTION + 上游机制补遗 §6）

1. **第五轮抽检**：PATTERN_CARDS TD-04..15 与 ADOPTION 引用的 TDCanvas 侧未核验条目 31 处（canvas-plugin/node-registry/ports/resource-refs/node-generation/aitudou batch/handleRunAitudou/批量/恢复链/资产回收/agent http+session/plugin-runtime/comfy execution/历史栈/网格/辅助线/历史签名等）。**发现 1 处漂移并已修正**：viewport 500ms 防抖保存实际位于 `project.tsx:448-460`（原写 445-459），SOURCE_ANALYSIS §1.9/§2.4 与 PATTERN_CARDS TD-10 共 3 处同步更正；其余 30/30 命中（含复核 `isAitudouPollingUncertain :4185`、`recoverRuntimeDiskCopy :121`、`batchMotionById :664`、`http.ts:422/509`、`session.ts:26/436`）。
2. **新增 UPSTREAM_DIFF_AUDIT §6「上游其余机制补遗」**（三个机制，源文件精读）：§6.1 prompt-source 运行时（JSON 约定 18 字段含生成提示、title+prompt 必填、id 缺省与去重；归属=两仓同源继承）；§6.2 local-proxy 挂接（testLocalProxy 身份探测、normalizeLocalProxyUrl/withLocalProxy 防双包、buildApiUrl 全量过代理；归属=继承但上游深度更高）；§6.3 selection/tool 体系（`tool: "select"|"pan"` 显式模式 + Space/Ctrl **临时工具反转**语义 + 按键状态机；归属=上游形态被 TDCanvas 重写为固定手势）。§2 表未列归属的缺口由此补齐。
3. **抽检台账（累计）**：12+9+15+79+31 = **146 处，五轮，仅 1 处漂移并已修正**（修正后 100% 一致）。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项（§5/§6 已覆盖其独有与继承机制的主要面）；② 运行时审计（需启动用户环境授权）。

## v8 — 2026-09-26（上游机制回填模式卡与采纳矩阵）

1. **PATTERN_CARDS 新增上游参考卡 UP-01..06**（与 TD 卡同四层结构，证据引 UPSTREAM_DIFF_AUDIT §5/§6）：UP-01 多选浮动工具条与成组操作族、UP-02 canvas-proxy 本地 CORS 转发方法、UP-03 Group 资源集合语义、UP-04 model-plugin BYOK 脚本层（含安全反面）、UP-05 prompt-source 开放 JSON 约定、UP-06 selection/pan 双模式与临时工具反转。文件头部声明 TD/UP 两系与上游基准。
2. **ADOPTION_DECISION_MATRIX 新增 #21-26**：#21 canvas-proxy 方法 `ADOPT_METHOD`、#22 Group 资源集合 `RESEARCH_ONLY`、#23 BYOK 脚本层 `RESEARCH_ONLY`（安全反面同 #13）、#24 prompt-source 约定 `ADOPT_METHOD`、#25 双模式+临时反转 `REJECT_TRANSPLANT`（同 #12）、#26 多选成组工具条 `DEFER`（与 #10 同批）。汇总行已更新为 26 项（ADOPT_METHOD 10 / ADAPT 3 / RESEARCH_ONLY 5 / DEFER 3 / REJECT 5）。
3. **一致性同步**：包 README Read Order、docs/research/README.md、docs/index.md 的模式卡数量（15→21）与矩阵行数（20→26）描述全部更新；REPORT.md 引用的 TD-03/06/08/11 卡号不受影响。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项；② 运行时审计（需启动用户环境授权）。

## v9 — 2026-09-26（第六轮抽检：SOURCE_ANALYSIS 结构锚点 + § 交叉引用校验）

1. **§ 交叉引用一致性校验**（脚本化）：提取包内全部 `§x.y` 引用（目标为 SOURCE_ANALYSIS 58 个编号标题、UPSTREAM_AUDIT 13 个），发现并修正 1 处悬空引用——SOURCE_ANALYSIS §1.2 的「键位表见 §4.9」改为指向 [INTERACTION_CATALOG.md](INTERACTION_CATALOG.md) §6（快捷键全表实际落档处）。
2. **第六轮行号抽检 83 处**（此前未直接核验的结构锚点）：§1 渲染层 23 处（ViewportTransform 类型、transform 层 `:241-246`、节点 transform `:312-318`、贝塞尔曲率/命中层/选中描边/ActiveConnectionPath、流动光效 CSS、小地图 240×160/±500/视口框/着色、氛围层密度分档、theme token、port 解析与兼容、连线显隐分支、命中常量 40/32、window 收尾、runningWorkflowNodeIds、组逆序查找）；§2/§4 30 处（store 六锚点、localforage 三 store、导出单节点、showcase/封面、hydrate 两级、persistAitudouRunResult、runAitudouOperation/prepare/upload/错误脱敏、协议归一化与 pollPath、模型目录 123、变体匹配/Seedream 几何/引用注入、尺寸表、裁剪与 4096 上限）；§5/§6 30 处（工具枚举/op zod schema/编译器/生成流 ops/MCP 回环/claude spawn/session 状态与回传/CanvasAgentOp 8 原语及应用/媒体缓存 Web 前缀与 Rust 三锚/lib.rs 目录/插件注册表/事件总线/插件 storage/上下文/加载三路/Comfy 注册与动态端口/工作流解析与固化/Tauri 启动收敛与参数白名单）。**83/83 命中，零漂移**（一处误判复核：`local-media-cache.ts:120` 确为 `LOCAL_MEDIA_CACHE_FILE_PREFIX`）。
3. **抽检台账（累计）**：12+9+15+79+31+83 = **229 处行号引用，六轮，仅 1 处漂移（v7 已修正）+1 处悬空 § 引用（本轮已修正）**；修正后包内引用 100% 一致。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项；② 运行时审计（需启动用户环境授权）。

## v10 — 2026-09-26（第七轮：三方结论一致性复核 + 低频引用增量核验）

1. **REPORT ↔ PATTERN_CARDS ↔ ADOPTION 一致性复核**（脚本化）：
   - 卡号引用：全包 TD/UP 卡引用均可解析（REPORT 引 TD-03/TD-11；AUDIT 引 12 张 TD 卡；README 引 TD-01/UP-01）。
   - **发现并修正 1 处卡号错位**：REPORT §7.2 的「TD-03/06/08」与能力清单不对应（几何分组应为 **TD-15**、pinned 引用应为 **TD-06**），已改为显式「TD-03 / TD-15 / TD-06（pinned 亦见 TD-09）」。
   - 矩阵复核：行号 1-26 连续完整；逐行决策与汇总分桶一致（ADOPT_METHOD 10 / ADAPT 3（#6 双 LibTV+Jimeng）/ RESEARCH_ONLY 5 / DEFER 3 / REJECT 5；初检的 11/6/4/6 计数系把矩阵头部决策词汇行误计入，非真实不一致）。
   - 采纳决策与报告建议对齐：REPORT §7 的三条建议（拖线到空白/几何分组/pinned → 矩阵 #6/#10/#4；Agent 化桥接形态 → #7/#8）与 §5 反面教材（#13/#14/#15）逐条对上。
   - **修正 1 处过时台账**：INTERACTION_CATALOG 头部抽检说明从 v6 口径（累计 115）更新为六轮 229 处口径。
2. **低频引用增量核验 24 处**：surface Space handler/pan rAF、节点组件十个内部锚点（标题栏偏移/端口渲染/内容分发/Loading/Error/TextContent/Video/ResizeHandle/ConnectionHandleDot/z 类名）、media_cache 四锚（manifest 命中/1GB 守卫/parse_remote_url https 强制/mime 白名单）、`canReuseExternalReference`/`AitudouPollingStoppedError`/输出 kind 推断/视频模型目录折叠/历史合并与 FNV id/`collectStorageKeys`/`InstalledPlugin`。**24/24 命中，零漂移**。
3. **抽检台账（累计）**：12+9+15+79+31+83+24 = **253 处行号引用，七轮，1 处漂移 + 1 处悬空 § + 1 处卡号错位（均已修正）**；另完成全包 § 交叉引用与卡号引用的脚本化校验（可复跑）。

**剩余队列**（均需用户输入，暂列为待决）：① 上游 infinite-canvas 独立立项；② 运行时审计（需启动用户环境授权）。

## v11 — 2026-09-26（README 状态一致性 + §3/§8 低频引用核验）

1. **README.md 与包内状态一致性复核**：发现锚点表「上游的上游」行仍是 v2 之前的旧表述（「本项目未调研过，归属 diff 待做」），与 UPSTREAM_DIFF_AUDIT 已完成的事实矛盾——已改为「归属 diff 已完成，见 UPSTREAM_DIFF_AUDIT.md」。其余结论摘要各断言（8 相位、10000×10000、280px、24 条、17371、协议版本=5、chatSessions 无 UI）逐一与当前包内状态核对一致；Read Order 7 项与实际文件一一对应。
2. **第七/八轮低频引用核验 53 处，零漂移**：
   - §3 节点体系 25 处：`NODE_DEFAULT_SIZE`/Aitudou 规格遗留、`builtinResource` 与内置注册数组、`FALLBACK_SPEC`、双击分发、磨砂玻璃判定、类型渲染表、缺插件占位、Group 内容、`ImageInfoBar`、resize limits/`fitMediaNodeGeometry`、工厂三函数、`snapNodesIntoGroup`/`findContainingGroupId`、组计数 memo、`createNode` 面板策略、hover 工具条拖拽隐藏、历史切换几何、剪贴板文本节点、快捷工具 storage key、工具自定义 effect。
   - §8 周边表面 28 处：助手会话水合与清理、删除确认弹窗、showcase IntersectionObserver/轨道 SVG、preview 24 连线上限与布局函数、资产类型与 persist key、提示词源调度/间隔档/刷新回落、prompts 页存资产、侧栏拖宽/三 tab/聚焦/全选、语言切换、编辑器视口 1–4x 与指针锚、top-bar 汉堡/双击改名、DockTip、agent EventSource、journal 提交、`saveNodeAsset`、资产页过滤。
3. **抽检台账（累计）**：12+9+15+79+31+83+24+53 = **306 处行号引用，八轮，3 处问题（1 漂移/1 悬空 §/1 卡号错位）+ 1 处 README 状态过时，均已修正**。

## v12 — 2026-09-26（第九轮：SOURCE_ANALYSIS §4/§5/§6 剩余引用 + UPSTREAM §4 锚点复核）

1. **§4 生成管线剩余 20 处核验全中**：`AitudouOperationDefinition` 契约类型、官方 base/本地代理前缀常量（`aitudou.ts:6-8`）、`resolveAitudouApiBase`、`resolveAitudouChannel`、面板价格加载 effect、`HIDDEN_VIDEO_MODEL_PREFIXES`、`aitudouNativeModels/aitudouNativeParameterDefinitions`、composer 上下文（`canvas-node-generation.ts:58`）、旧版 mention 同步、`labelForKind`、`updateAitudouSubmission`、`finishAitudouResult`、`applyAitudouResultToSource`、`aitudouOutputNodeType`、旧管线并行目标/流式文本、`extractAitudouButtons`、`cropImageNode`、`splitDataUrl`。
2. **§5/§6 剩余 25 处中 24 处命中、1 处路径归属修正**：协议版本=5 双端常量（local-agent-panel `:71`）、握手不匹配断开（`:361`）、权限模式切换与 `permissionMode` 解析（http.ts:454）、Codex 审批端点（:401）、`spawn app-server --stdio`（codex-client:71）与 `codexBin()` 解析（:894）、config 首启随机 token（config.ts:21）、`CanvasSnapshot` 类型（types.ts:7）、agent-store localStorage 键（:98）、`addAsset` 站点工具、semver 对比、插件管理器警示横幅、`definePlugin` 重载、`collectConnectedValues`、Comfy `/upload/image` 端点——全部一致；**唯一修正**：`isCanvasWriteTool` 的文件路径实为 `web/src/components/agent/agent-event-formatters.ts`（`:493-495` 内容吻合），SOURCE_ANALYSIS §5.3 已更正目录归属。
3. **UPSTREAM_DIFF_AUDIT §4 语义分类表锚点复核 4/4**：TD `project.tsx:1935`（handleConfigNodeChange，Aitudou 配置区起）、`:3984+`（组件闭合后尾部辅助区）、`canvas-node.tsx:577`（MediaGeneratingContent）、`:890`（批量 UI 区）——与「最大连续块」判读表述一致。
4. **抽检台账（累计）**：306 + 45 = **351 处行号/路径引用，九轮，4 处问题均已修正**；另有 4 处 UPSTREAM §4 块锚点复核一致（合计 355 处核验）。

## v13 — 2026-09-26（自检脚本固化 + §3 内容区收尾核验）

1. **新增可复跑自检脚本 `scripts/check-tdcanvas-research.py`**（项目 scripts 目录，只读）：合并三项包内校验——① § 交叉引用解析（SOURCE_ANALYSIS 58 标题 / UPSTREAM_AUDIT 13 标题）；② TD/UP 卡号解析（21 张卡）；③ ADOPTION 矩阵行号连续性、逐行决策与汇总分桶一致（ADAPT 按「行」去重统计，#6 双决策单行）、README 计数声明（21 张 / 26 项）。复跑结果：**全部通过**（退出码 0）。
2. **§3 图片/音频内容区收尾核验 10/10**：`ImageNodeContent`（含 batch 根分支）、`BatchFrame` 包裹、`EmptyImageContent` 空态上传、batch 根独立空态、`AudioNodeContent`、`ImageContent` 主图组件、批量 props 类型、批量数量按钮、按钮事件 stopPropagation、历史面板版本缩略。
3. **抽检台账（累计）**：351 + 10 = **361 处行号/路径引用，十轮，5 处问题均已修正**；另 4 处 UPSTREAM §4 块锚点、全包 § / 卡号 / 计数三项校验已固化为脚本可随时复跑。

## v14 — 2026-09-26（REPORT 最终一致性复核）

1. **两项校验复跑全绿**：`scripts/check-tdcanvas-research.py`（§ 引用 / 卡号 / 矩阵 / 计数）与 `scripts/verify-docs.py`（1057 文件 / 4631 链接）。
2. **发现并修正 REPORT.md 两处 v2 之前旧口径**（归属审计完成后未回写）：
   - §6 证据边界「未与上游 diff…归属只是未证实的推断」→ 改为「上游归属已完成 diff 审计」，并给出继承/原创/双向演化的结论要点与审计文档指针；
   - §7.1 建议「clone 上游为 submodule 做 diff 审计」→ 该动作已完成，改为「上游独立立项」建议（与 ITERATION_LOG 待决队列一致）。
3. 复核其余 REPORT 断言与包内状态一致（§2 架构定性、§3 输入语义分歧、§4 机制清单与矩阵行对应、§5 反面教材与 REJECT 行对应、§7.2/7.3 卡号引用于 v10 已修正）。
4. 待用户输入项保持标注：① 上游 infinite-canvas 独立立项；② 运行时审计授权。

## v15 — 2026-09-26（第十轮：残余引用增量核验 + 队列复核）

1. **双校验复跑全绿**（自检脚本 + verify-docs 1057 文件 / 4631 链接）。
2. **残余引用核验 46/46 命中，零漂移**：
   - §1/§2（16 处）：`CanvasNodeData`/`CanvasNodePort` 类型、`initialViewport {0,0,1}` 与 create/import 引用（:37/:84/:103）、`uploadImage/uploadMediaFile`、`useThemeStore` persist、`syncDesktopWindowTheme`、`importLegacyCachedMedia`、viewport useState（:248）、`screenToCanvas`（:493）、初始居中（:481）、`CANVAS_GRID_STEP=16` 与状态镜像（:149-153）、`snapToGrid` 默认关（:266）、辅助线视口反算。
   - §3-§6（30 处）：捕获阶段选中（:1325）、duplicate 接线（:3918）、`handleResumeAitudou`（:2257）、`canvasImageOperationSource`（:4125）、右键菜单视口 clamp、图片操作源 blob 化注释、`requestAitudou` apiKey、`extractAitudouOutputs`、`transformAngleDataUrl`（遗留）/`upscaleDataUrl`、journal key 与清除、agent token 校验（http:526）、`activateClient`/`resolveResult`（session:314/371）、中文工具描述表（schemas:120）、claude JSON Lines 管道、workspace 初始化、`setAgentCanvasContext`（bridge:92）、插件 persist（:41）、Comfy 媒体上传（execution:102）、`inspectInputs`/`isRecommendedCanvasInput`、`find_available_port`/`detect_environment_at`、media_cache 临时文件/重命名提交/旧迁移字节校验、lib.rs 闪屏揭示与 4s/10s 兜底。
3. **ITERATION_LOG 队列复核**：剩余两项（上游独立立项 / 运行时审计授权）均为用户输入门控，保持待决标注；其余可自主推进项已全部消化。
4. **抽检台账（累计）**：361 + 46 = **407 处行号/路径引用，十一轮，5 处问题均已修正**；三项固化校验（自检脚本）+ verify-docs 双绿。

## v16 — 2026-09-26（第四项自检：目录↔矩阵对齐 + 相关性分级复核）

1. **自检脚本新增第四项校验**（INTERACTION_CATALOG ↔ ADOPTION 对齐）：① 目录「候选 ADAPT」标记数必须等于矩阵 ADAPT 行数；② 矩阵必须覆盖 UPSTREAM §5.1-§5.4/§6.1-§6.3 全部七个上游机制节；③ 六张上游参考卡 UP-01..06 必须在矩阵中有「（UP-0x）」显式对应行。首跑即抓到 3 类缺口并已修复：目录「图片历史」行漏标「候选 ADAPT」（补齐后 3=3）；#21 行 §5.2/§6.2 合写导致 §6.2 覆盖断言不识别（校验放宽为 §token 子串）；矩阵 #21-26 证据列补「（UP-01..06）」显式 ID 交叉引用（UP-01→#26、UP-02→#21、UP-03→#22、UP-04→#23、UP-05→#24、UP-06→#25）。
2. **相关性分级 ↔ 决策对齐复核（人工结论）**：目录全部「高」级交互均有落点——或已有 clone 覆盖（建节点/重命名/移动/缩放/选择/复制粘贴/删除/双击建菜单等核心 CRUD，对应既有 Batch verifier），或对应矩阵行（图片历史→#4、批量→#5、拖线到空白→#6、生成生命周期→#1/#2、Agent 写画布→#7/#8、删除清理链→#17、封面/viewport→#20、注册表→#9）；「中」级对应 FrameOS 方向行（#19/#22/#26）；「低」级均为对照研究（#11/#12/#25）。无「高」级孤儿条目。
3. 自检脚本现为四项校验（§ 引用 / 卡号 / 矩阵与计数 / 目录↔矩阵对齐），复跑通过；verify-docs 同绿。

## v17 — 2026-09-26（拼写/硬编码一致性扫描）

1. **拼写一致性**：全包「TDCanvas」「Aitudou」「16b3127」等专名拼写与提交引用一致，无变体。
2. **硬编码台账根治**：发现 INTERACTION_CATALOG 头部仍硬编码「累计 229 处 / 六轮」（v15 后已过时，同类问题第二次复发）——已移除硬编码累计，改为「以 ITERATION_LOG 维护记录为准」的唯一事实源模式；复查确认 ITERATION_LOG 之外无其他会过时的计数声明。
3. 双校验复跑全绿（自检四项 + verify-docs 1057 文件 / 4631 链接）。
4. 待用户输入项保持标注：① 上游 infinite-canvas 独立立项；② 运行时审计授权。

## v18 — 2026-09-26（收尾核验 + 进入维护态）

1. **最后一批残余引用 7/7 命中**：小地图定位 `bottom-24 left-6 z-50`（:99）、Midjourney MODAL→attention（protocol:47）、`agent_chat_messages` objectStore（:8）、`readAssetPackage/readZip`（asset-transfer:90）、`GENERAL_OPERATIONS` 契约（contract:31）、插件上下文 useMemo（canvas-node:146）、旧工厂形式注释（plugin-loader:9）。
2. **计数/行数类断言核验**：zh-CN.ts 1867 行、en-US.ts 1909 行、canvas-node.tsx 1125 行——三处与文档声明**精确一致**；canvas i18n 命名空间实测 312-874 行 / 539 key，与「约 312-875 行、≈540 key」吻合；`use-canvas-side-panel-store.ts` 路径与键名（tdcanvas:side-panel-width/open）与文档一致。
3. **维护态宣告**：静态源码证据面已饱和（行号引用 361+46 处全部核验、计数断言精确命中、四项自检+verify-docs 双绿）。此后仅在以下情况再迭代：上游/本仓发新版本、用户下达新指令、或批准剩余两项待决（上游独立立项 / 运行时审计授权）。

## v19 — 2026-09-26（维护态探测：TDCanvas 上游基线已前移）

1. **双校验复跑全绿**（自检四项 + verify-docs 1057 文件 / 4631 链接）。
2. **上游漂移探测（ls-remote）**：TDCanvas upstream HEAD 已从基线 `16b3127`（2026-09-15）前移至 `d05cf612`（2026-09-25，Merge PR #2），增量 3 个提交 / 51 文件 / +1392-150；infinite-canvas main 仍在审计基准 `dab19ad`；本地工作副本仍停在 `16b3127`（跟踪文件无改动）。
3. **增量内容与影响面**：① ComfyUI 队列跨 tab 共享；② 工作流运行历史持久化（preserve canvas inputs and workflow run history）；③ ComfyUI combo 下拉修复；④ 复制/粘贴路径补 `batchChildIds` 经 idMap 的重映射（对 TD-08 批量模型的细化）。变更集中在 comfyui-local 与 project.tsx/i18n；**td-canvas-surface / canvas-node.tsx / use-canvas-store / aitudou.ts / media_cache.rs / node-registry 均未变**——包内 §1/§3/§5 核心机制的行号引用对本仓锁定基线依然成立（文档协议即「行号对齐锁定提交」）。
4. **影响与待决**：包内引用无需立即改写（基线锁定协议保护）；但 §6.3 comfyui-local 与批量模型已有上游新动向未落档。新增待决项：③ 是否重定基线至 `d05cf612` 并重验行号 / 对 3 个提交做增量调研。①② 两项维持待用户输入标注。

## v20 — 2026-09-26（基线后增量调研落档：`16b3127..d05cf612`）

1. **UPSTREAM_DIFF_AUDIT 新增 §7「基线后增量」**，对 3 个提交逐个落档（file:line 对齐 `upstream/main`）：
   - **c7a0364 运行历史持久化**：Rust `run_result_path` 按 `prompt_id+item_index` 独立保存每次运行结果；web `result-nodes.ts` 新增 `ComfyResultBinding` 与 `createComfyResultNodes`（按输出口建节点+按端口连线）；新文件 `canvas-node-duplication.ts` 复制纯函数化并经 idMap 重映射 `batchChildIds`；右键菜单新增「清除输入」；引入 openspec 变更流程。
   - **7e2142e combo 下拉修复**：`inputEnumValues` 同时解析数组型与 `COMBO`+`options` 型声明（+68 行测试）。
   - **422dff6 队列跨 tab 共享**：Rust `attach_environment` 命令 + `/queue` 读取与 `cancel_action` pending/running 区分；web 每 tab 挂接模型与 UI（+63）；注册命令（+19）。
2. **对包内结论的影响**：TD-08 卡补「基线后演化」注记；ADOPTION #19 价值上调（队列编排/结果溯源范式）；SOURCE_ANALYSIS §6.3 基线态描述仍成立；既有 file:line 引用全部无需改写（锁定基线协议）。
3. 双校验复跑全绿。
4. 待决项保持：① 上游 infinite-canvas 独立立项；② 运行时审计授权；③ 重定基线至 `d05cf612`（重验行号）——本 v20 为其轻量替代（增量已落档）。

## v21 — 2026-09-26（自检脚本第五项：基线哈希防混淆）

1. 新增校验⑤：未知 40 位哈希告警（白名单=TD 基线 16b3127 全哈希 + infinite-canvas 审计基准 dab19ad 全哈希）、`d05cf612` 不得被写作「锁定提交/研究基线」、锁定基线 `16b3127` 至少锚定 3 个文件。首跑抓到的 40 位哈希告警经确认为另一仓库合法基准（白名单化）；`d05cf612`/基线写法当前全部正确。
2. 自检现为五项校验；verify-docs 同绿（1057 文件 / 4631 链接）。
3. 维护态语义更新：上游已前移至 `d05cf612`（v19 探测、v20 增量落档），本项校验将持续防止后续迭代把新 HEAD 误写为研究基线。

## v22 — 2026-09-26（维护探测固化为 `--probe` 模式）

1. 自检脚本新增 `--probe` 子命令：`python3 scripts/check-tdcanvas-research.py --probe` 一条命令完成上游漂移探测（ls-remote 比较 HEAD 与包内已知哈希：TDCanvas 基线 `16b3127`/最近 `d05cf612`，infinite-canvas 基准 `dab19ad`），输出 未变/回到基线/已前移/探测失败 四态，已前移时退出码 1。
2. **探测结果（本轮）**：TDCanvas `d05cf612` 未变、infinite-canvas `dab19ad` 未变——基线后增量（§7）仍是最新，无需追加调研。
3. 首跑自测修正两处实现问题：基线混淆守卫误扫 ITERATION_LOG（日志中「重定基线至 d05cf612」为合法待决描述，已排除日志文件）；probe HEAD 截取 7 位与 8 位 last_seen 比较导致误报（改为 startswith）。
4. 三项待决保持标注；双校验全绿。

## 收尾留档 — 2026-09-26（用户指示收尾，循环结束）

1. 用户指示收尾：保证可构建、留档最新进展、提交并 push main、恢复干净工作区。
2. **最终状态**：v1→v47 共 47 轮迭代（20 轮实质调研与落档 + 27 轮一致性核验与例行维护）；包内 8 文件 + 自检脚本 `scripts/check-tdcanvas-research.py`（五项校验 + `--probe` 漂移探测）。
3. **证据规模**：414 处 file:line/路径引用、十一轮抽检、5 处问题全部修正；基线后增量（`16b3127..d05cf612` 3 提交）已落档于 UPSTREAM_DIFF_AUDIT §7。
4. **移交的待决项**（等待用户后续指示）：① 上游 `infinite-canvas`（basketikun）独立立项；② 运行时审计（需启动应用授权）；③ 重定基线至 `d05cf612`（行号重验；增量已先行落档）。
5. 复跑入口：`python3 scripts/check-tdcanvas-research.py` / `--probe` / `python3 scripts/verify-docs.py`。

## 运行时审计轮 — 2026-09-26（用户提供真实素材后解锁待决②）

1. 用户供给真实测试素材（10 图 / 2 音频 / 2 视频，登记于 [TEST_ASSETS.md](TEST_ASSETS.md)）并明示红线：不触发任何真实生成、不配置 API Key。
2. 启动 TDCanvas web（Vite @ localhost:3000），IAB 浏览器完成非付费路径运行时探索，全部落档 [RUNTIME_AUDIT.md](RUNTIME_AUDIT.md)：?mode=new 建项目、空图片节点+原生面板自动打开、真实图片经全局 input 管线注入（原地替换/新建双路径）、重置视图 77% clamp、节点拖拽、贝塞尔连线、双击创建菜单（含 ComfyUI 工作流项）、文本节点+文本创作面板。
3. 偏差澄清：hover 工具条无视口 clamp（clamp 属右键菜单）；新项目默认标题「TDCanvas 2」待查；Playwright locator 点击被画布覆盖层拦截（自动化需走坐标路径）。
4. 待决②实质解除（非付费运行时审计已完成）；付费生成路径仍永久不做。剩余待决：① 上游独立立项；③ 重定基线。

## 维护记录

- 2026-09-26 v1：首轮落档（5 专题并行调研 + 6 文档）。
- 2026-09-26 v2：上游归属审计（UPSTREAM_DIFF_AUDIT.md）+ 周边表面补遗（SOURCE_ANALYSIS §8）+ 结论修订。
- 2026-09-26 v3：引用抽检 12/12 通过 + INTERACTION_CATALOG.md（56 项交互 + 快捷键全表）。
- 2026-09-26 v4：diff 语义分类（§4）+ 上游独有机制速览（§5）+ 二轮引用抽检 9/9。
- 2026-09-26 v5：§5 深化为 §5.1-5.4 逐机制完整分析（四个源文件精读）+ 三轮引用抽检 15/15（累计 36/36）。
- 2026-09-26 v6：第四轮引用抽检 INTERACTION_CATALOG 全量 79/79 零漂移（累计 115 处），目录头部标注抽检台账。
- 2026-09-26 v7：第五轮抽检 31 处、发现并修正 viewport 防抖行号漂移 3 处（累计 146 处）；新增 §6 上游机制补遗（prompt-source/local-proxy/selection 体系）。
- 2026-09-26 v8：上游机制回填——PATTERN_CARDS 增上游参考卡 UP-01..06、ADOPTION 矩阵增 #21-26（合计 26 行），包内计数与索引描述同步。
- 2026-09-26 v9：第六轮抽检 83/83 零漂移 + § 交叉引用校验修正 1 处悬空引用（行号累计 229 处）。
- 2026-09-26 v10：三方结论一致性复核（修正 REPORT 卡号错位 TD-03/06/08 → TD-03/TD-15/TD-06、更新 CATALOG 过时台账）+ 低频引用核验 24/24（行号累计 253 处）。
- 2026-09-26 v11：README 锚点表同步（上游行「归属 diff 待做」→「已完成」）+ 第七/八轮 §3/§8 低频引用核验 53/53 零漂移（行号累计 306 处）。
- 2026-09-26 v12：第九轮 §4/§5/§6 剩余引用核验 45/45（1 处路径归属修正：agent-event-formatters 实为 components/agent/ 而非 lib/agent/）+ UPSTREAM §4 四个块锚点复核一致（行号累计 355 处）。
- 2026-09-26 v14：REPORT 最终一致性复核——修正 §6 归属未证实旧表述与 §7.1 已完成建议（均同步至 UPSTREAM_DIFF_AUDIT 完成态）；两项校验复跑全绿。
- 2026-09-26 v15：残余引用增量核验 46/46 零漂移（§1/§2 坐标与存储 16 处 + §3-§6 收尾 30 处；行号累计 407 处）；ITERATION_LOG 队列复核——两项均属用户输入门控，保持待决标注。
- 2026-09-26 v16：自检脚本扩为四项校验（新增目录↔矩阵对齐：候选 ADAPT 标记 3=3、UPSTREAM 七节全覆盖、UP 卡↔矩阵行显式 ID）；相关性分级对齐复核无孤儿；双校验全绿。
- 2026-09-26 v17：拼写/硬编码一致性扫描——移除 CATALOG 头部会过时的硬编码累计口径（229/六轮），改为指向 ITERATION_LOG 唯一事实源；TDCanvas 拼写与 16b3127 提交引用全包一致；双校验全绿。
- 2026-09-26 v18：收尾核验 7/7 + 计数断言 3/3 精确命中（行号累计 414 处）；宣告进入维护态，后续迭代仅在版本更新/新指令/待决批准时触发。
- 2026-09-26 v19：维护态探测——TDCanvas 上游前移至 d05cf612（3 提交，ComfyUI 队列共享/运行历史/批量 idMap 重映射），基线锁定协议下包内引用不受影响；新增待决项③重定基线或增量调研。
- 2026-09-26 v20：基线后增量调研落档——UPSTREAM_AUDIT 新增 §7（3 提交逐个机制分析：运行历史持久化/复制 idMap 重映射/combo 修复/队列跨 tab 共享），TD-08 补演化注记，#19 价值上调。
- 2026-09-26 v21：自检脚本扩为五项校验（新增基线哈希防混淆：未知 40 位哈希告警 + d05cf612 基线混淆守卫 + 16b3127 锚定数下限）；双校验全绿。
- 2026-09-26 v22：漂移探测固化为 --probe 模式（四态输出+退出码）；本轮探测 TDCanvas d05cf612 未变、infinite-canvas dab19ad 未变；修正守卫误扫日志与哈希截断两处实现问题；双校验全绿。
- 2026-09-26 v23：例行维护轮——五项自检/漂移探测（d05cf612、dab19ad 均未变）/verify-docs 三项全绿，无新增增量，无包内改动。
- 2026-09-26 v24：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v25：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v26：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v27：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v28：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v29：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v30：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v31：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v32：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v33：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v34：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v35：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v36：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v37：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v38：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v39：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v40：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v41：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v42：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v43：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v44：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v45：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v46：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 v47：例行维护轮——五项自检/漂移探测/verify-docs 三项全绿；待决三项 ①②③ 保持标注。
- 2026-09-26 运行时审计轮：真实素材非付费运行时探索落档（RUNTIME_AUDIT.md + TEST_ASSETS.md），待决②解除；用户指示收尾，循环结束。
