# TDCanvas → LibTV/FrameOS/Jimeng 采纳决策矩阵

> 决策词汇与 open-canvas 包一致：`ADOPT_METHOD`（借方法不借实现）、`ADAPT_TO_*`（需改造并补合同）、`RESEARCH_ONLY`（仅研究）、`DEFER`（暂缓）、`REJECT_TRANSPLANT`（拒绝移植）。
> **本矩阵不构成实现授权**：任何 `ADAPT` 项在进入实现前仍需走 Par 编号、source/fixture 证据与 verifier 流程（Change Protocol）。
> clone 现状列引用的是本项目已落档的合同/审计（`AGENTS.md` 与 `docs/research/` 既有记录），未逐一重跑 verifier；标注「待证」处需先复核。

| # | TDCanvas 机制 | 证据 | LibTV (React Flow) | FrameOS | Jimeng | 决策 | 理由与条件 |
|---|---|---|---|---|---|---|---|
| 1 | 生成任务 8 相位状态机、partial/attention、停止≠取消 | SOURCE_ANALYSIS §4.4 | 相关（Seedance 异步） | 相关（生成节点） | 相关（生成流） | `ADOPT_METHOD` | 方法论输入进 `LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE` / `VR-007` 的下一次修订评审；不改 runtime |
| 2 | 提交即写 journal 的中断恢复 + 节点级防重复计费守卫 | §4.4 | 高相关 | 高相关 | 高相关 | `ADOPT_METHOD` | clone 需先定任务身份权威（operation identity）；journal 形态可并入 Director completion 设计 |
| 3 | 媒体 URL 哈希稳定文件、manifest 原子写、hydrate 五级恢复链 | §2.5/§2.7 | 相关 | 相关 | 低 | `RESEARCH_ONLY` | clone 是纯 Web 原型；桌面化时再启用，先对照 `VR-021` 的 lease/asset 模型 |
| 4 | 图片历史 24 条版本 + 签名去重 + pinned 引用 | §2.7/§4.6 | 高相关（生成历史） | 中 | 中 | `ADAPT_TO_LIBTV`（候选） | pinned 版本引用是 LibTV 引用槽缺的语义；需 source fixture 证实源站等价物后再立项 |
| 5 | 批量生成堆叠（batch root/child/主图） | §4.6 | 高相关 | 中 | 中 | `ADAPT_TO_LIBTV`（候选） | 与生成历史「尝试列」表达二选一需源站证据；堆叠的删除/拖动联动规则可直接进 fixture |
| 6 | 拖线到空白弹创建菜单 + 几何命中 | §4.1/§1.7 | 高相关 | 中 | 高相关（Jimeng 无线画布） | `ADAPT_TO_LIBTV` / `ADAPT_TO_JIMENG`（候选） | 命中算法可移植 `onConnectEnd`；需 `GI-004..007` disposable fixture 与菜单项源站证据 |
| 7 | 统一画布指令集（Agent 与插件共用 8 原语 applyOps） | §5.4/§6.2 | 中（Director 体系） | 中 | 低 | `ADOPT_METHOD` | FrameOS/LibTV 若做 Agent 化，以「页面为执行主体的回传桥接 + 原语指令集」为蓝本；不与 Director authoredObjects 混淆，需新合同 |
| 8 | Agent 桥接协议（快照上报+SSE 回传、协议版本握手、写确认） | §5.1-5.3 | 中 | 中 | 低 | `RESEARCH_ONLY` | 完整协议形态参考；落地前需评估与 Director auth 边界 |
| 9 | 开放节点注册表（definition 驱动 + 缺插件占位） | §3.1 | 相关（11 类 registry） | 相关 | 相关 | `ADOPT_METHOD` | 印证 V0 registry 方向；「缺插件占位渲染」是未来扩展的必备件 |
| 10 | 几何式分组（groupId + 中心点包含） | §3.5 | 中 | 中 | 中 | `DEFER` | React Flow 无原生分组；若 parity backlog 出现源站分组语义再启用 |
| 11 | 手写内核（transform 层/固定 SVG/280px 裁剪） | §1 | 不适用 | 不适用 | 不适用 | `RESEARCH_ONLY` | clone 已锁 React Flow 12.11.1（`VR-016`）；仅作对照与性能方法论输入 |
| 12 | 输入语义（wheel=zoom、Space 禁用、ctrl 框选） | §1.2 | 不适用（语义相反） | 不适用 | 不适用 | `REJECT_TRANSPLANT` | clone 输入权威是 `CANVAS_NAVIGATION.md`+Batch 77 证据；TDCanvas 不构成源站证据 |
| 13 | 无沙箱插件执行 | §6.2 | — | — | — | `REJECT_TRANSPLANT` | 安全面直接否决；若未来做插件必须 iframe/Worker 沙箱+能力白名单 |
| 14 | 薄 store + 4242 行页面编排 | §2.2 | 不适用 | 不适用 | 不适用 | `REJECT_TRANSPLANT` | 与 clone 组件合同/verifier 治理相反 |
| 15 | 无 schema 版本、无 migrate | §2.9 | — | — | — | `REJECT_TRANSPLANT` | clone 文档模型已有 V1 schema/strict load 方向 |
| 16 | 全量快照 undo（防抖合并+拖拽暂停细节） | §2.3 | 相关（history 层） | 相关 | 相关 | `ADOPT_METHOD` | 「防抖合并」「拖拽合并为一条」两个细节适用于任何快照式 history；权威仍是五层文档模型 `VR-010` |
| 17 | 删除引用清理链（含 13 项悬空 UI 状态清扫） | §3.4 | 高相关 | 中 | 中 | `ADOPT_METHOD` | 「悬空 UI 状态清单」补强 `VR-013` 删除修复矩阵的 UI owner 维度 |
| 18 | 屏幕空间氛围网格/视差 | §1.6 | 低 | 低 | 低 | `DEFER` | 纯视觉可选项；优先级低于 parity backlog |
| 19 | comfyui-local：工作流 JSON→动态端口宏节点 | §6.3 | 中 | 高相关（FrameOS 生成节点范式） | 低 | `ADOPT_METHOD` | 「外部运行时封装为带动态端口的节点」范式适用于 FrameOS runner 节点；沙化启动（loopback+参数白名单）是安全基线 |
| 20 | 项目封面数据推导 + viewport 存文档 | §2.6 | 相关（多画布） | 相关 | 低 | `ADOPT_METHOD` | 对照 `VR-017` lifecycle 的两个细节决策点 |
| 21 | canvas-proxy 本地 CORS 转发方法（上游） | UPSTREAM §5.2/§6.2（UP-02）| 相关（开发态代理场景） | 低 | 低 | `ADOPT_METHOD` | 借「路径内嵌目标 + 双向头剥离 + SSE 透传 + 身份探测」的最小代理方法；引入需 SSRF/白名单合同（对照 #3） |
| 22 | Group 资源集合展平语义（上游） | UPSTREAM §5.3（UP-03）| 相关（引用槽/多选生成） | 中 | 中 | `RESEARCH_ONLY` | 「组=引用打包单位」与 clone 引用语义互补，但需源站「组引用」fixture；须与 `LibTVGraphConnection`/`AutoLink` 合同对齐 |
| 23 | model-plugin BYOK 脚本层（上游） | UPSTREAM §5.4（UP-04）| 低（clone 无 BYOK 需求） | 低 | 低 | `RESEARCH_ONLY` | poll/onDelta 运行时抽象可借鉴；主线程 `new Function` + apiKey 裸注入为安全反面，照搬即 #13 同罪 |
| 24 | prompt-source 开放 JSON 约定（继承） | UPSTREAM §6.1（UP-05）| 相关（提示词库扩展性） | 低 | 低 | `ADOPT_METHOD` | 「一个 JSON 数组即可挂接自定义提示词源」的契约 + 签名变化刷新/失败回落缓存策略可参照；需先定源信任边界 |
| 25 | selection/pan 双模式 + 临时工具反转（上游） | UPSTREAM §6.3（UP-06）| 不适用（语义相反） | 不适用 | 不适用 | `REJECT_TRANSPLANT` | 同 #12：clone 输入权威是 `CANVAS_NAVIGATION.md`+Batch 77 证据，上游形态不构成源站证据 |
| 26 | 多选浮动工具条成组族（上游） | UPSTREAM §5.1（UP-01）| 相关（多选交互） | 中 | 中 | `DEFER` | 与 #10 分组同批评估；成组守卫/GC 细节清单可直接进 fixture 模板 |

## 汇总

- `ADOPT_METHOD`：#1 #2 #7 #9 #16 #17 #19 #20 #21 #24（借方法，均不改 runtime，进入对应合同的下次修订评审输入）。
- `ADAPT`（候选，需源站 fixture + 授权）：#4 图片历史 pinned、#5 批量堆叠、#6 拖线到空白建节点。
- `RESEARCH_ONLY`：#3 媒体桌面缓存、#8 Agent 协议、#11 手写内核、#22 Group 资源集合、#23 BYOK 脚本层。
- `DEFER`：#10 分组、#18 氛围网格、#26 多选成组工具条。
- `REJECT_TRANSPLANT`：#12 输入语义、#13 无沙箱插件、#14 巨型页面、#15 无版本迁移、#25 双模式+临时反转。
