# TDCanvas 调研报告（面向项目决策）

> 上游：[`AICoderTudou/TDCanvas`](https://github.com/AICoderTudou/TDCanvas)，锁定提交 `16b3127`（2026-09-15，v0.14.0）。
> 事实与 file:line 证据在 [SOURCE_ANALYSIS.md](SOURCE_ANALYSIS.md)；可迁移模式在 [PATTERN_CARDS.md](PATTERN_CARDS.md)；采纳判断在 [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)。
> 本报告区分三类陈述：**源码事实**（已核对）、**证据支撑的推断**（标注）、**clone 决策建议**（不改变现有实现，等待授权）。

## 1. 一句话结论

TDCanvas 是「**零画布库依赖的手写 DOM 画布 + 本地优先（local-first）持久化 + 插件/Agent 双扩展通道**」的桌面端 AI 无限画布；它对本项目的核心价值不是视觉皮肤，而是**三条对照轴线**：(a) 与 React Flow 路线相反的手写内核在真实产品里如何落地；(b) 生成任务状态机与媒体资源生命周期（防重复计费、中断恢复、稳定本地地址）的工程化程度；(c) Agent/插件共用一套 `applyOps` 画布指令集的扩展架构。

## 2. 架构定性（源码事实）

| 维度 | TDCanvas | 对本项目（LibTV/FrameOS/Jimeng clone，React Flow 12）的意义 |
|---|---|---|
| 画布内核 | 纯手写：单一 transform 层 + DOM div 节点 + 固定 10000×10000 SVG 连线层 | 证明「React Flow 之外的完整路线」可行，且其 viewport/命中/虚拟化逻辑可逐条与 React Flow v12 的实现对照 |
| 状态 | 薄 store（仅项目文档 CRUD+persist）+ 4242 行页面编排（48 useState/25 useRef） | 与本项目「Zustand store 承载 graph」相反的取舍；代价是编辑态不进全局、收益是拖拽帧不放大订阅 |
| undo/redo | 页面级全量快照双栈（180ms 防抖合并、拖拽暂停、上限 50） | 无命令模式；对照 clone 的 history 层设计 |
| 持久化 | 全自动三级漏斗（页面 effect → 400ms 防抖 → localforage IndexedDB），无手动保存、无 schema 版本 | local-first 桌面形态；对照 clone 的多画布 lifecycle 与持久化边界 |
| 媒体 | 双轨制：IndexedDB Blob + 桌面 `media-cache`（URL SHA-256 去重、SSRF 防护、孤儿回收、hydrate 恢复链） | 远端生成产物的「稳定本地地址」问题在桌面端的完整解法 |
| 节点扩展 | 开放 `CanvasNodeDefinition` 注册表：ports 可函数、Content/Panel/toolbar 可注入、动态端口 | 插件式节点模型与 React Flow custom node 的对照 |
| 生成 | Aitudou API 任务状态机（8 相位、批量 partial、attention、停止≠取消、journal 中断恢复、节点级锁防重复计费） | 与 LibTV Seedance 异步结果 ingress 语义高度可对照 |
| 扩展通道 | Agent（loopback HTTP+SSE 回传桥接 + stdio MCP）与插件共用 `CanvasAgentOp` 8 原语 | 「Agent 操作画布」的完整落地参考（含写操作二次确认、协议版本握手） |

## 3. 与 React Flow 惯例相反的输入语义（值得记录的设计分歧）

1. **wheel 永远缩放**（无 ctrl 区分，触控板双指滚动也缩放）；缩放范围 5%–500%。
2. **Space+拖拽被故意禁用**——空白处普通左键即平移，Space 只 preventDefault。
3. **框选 = ctrl/cmd+左键拖空白**（shift 为加选）；本项目 LibTV 语义是 Shift+drag marquee、blank-drag no-op（`AGENTS.md` Batch 77 语义），两者互为反例。
4. 缩放 UI 锚点分野：滚轮以鼠标为锚、滑杆以视口中心为锚。

> 结论（推断）：这些不是「没做」，而是面向纯消费级触控板用户的刻意取舍；对本项目的价值是确认 React Flow 默认语义并非唯一合理解，且 `data-canvas-no-zoom` 的弹层豁免清单与本项目的 overlay 命中问题是同一类课题。

## 4. 高价值机制清单（对本项目的可借鉴点）

按「证据强度 × 对 clone 主题相关性」排序，完整矩阵见 ADOPTION_DECISION_MATRIX.md：

1. **生成任务生命周期**（SOURCE_ANALYSIS §4.4）：phase 八态、`partial` 部分成功、`attention` 等补充参数、本地停止与远端继续解耦（停止轮询≠取消且明示计费）、提交即写 journal 用于刷新恢复、`hasUnresolvedAitudouTask` 防重复计费——与 clone `VR-007`/异步结果 ingress 合同直接可比。
2. **媒体资源生命周期**（§2.5/§2.7）：URL 哈希去重的稳定本地文件、manifest 原子写、hydrate 恢复链（本地路径→旧缓存迁移→重下载）、签名去重的 24 条版本历史 + pinned 版本引用——与 clone `VR-021` media ingress/resource lifecycle 合同直接可比。
3. **统一画布指令集**（§5.4/§6.2）：Agent 与插件共用 `CanvasAgentOp` 8 原语，写操作统一经网页侧二次确认——若 clone 未来做 Director/Agent 自动化，这是现成的协议形态参考。
4. **批量生成堆叠模型**（§4.6）：batch root/child、主图选举、堆叠动效、批量子图随拖动/删除联动——对照 LibTV 图片生成历史的节点表达。
5. **几何式分组**（§3.5）：`groupId` + 中心点包含判定，无显式成员列表——与 React Flow 无原生分组的现状互补的最轻方案。
6. **连线落点几何命中**（§1.7）：世界坐标距离 + 三级优先级而非 DOM hover——在 React Flow 里做「拖到空白自动建节点」时可借的算法。
7. **连线即上游引用**（§4.2）：`@mention` 标签序列化、`versionMode:"pinned"`、连线与 objectReferences 双模式互斥——对照 LibTV AutoLink/引用槽语义。
8. **封面数据推导**（§2.6）：项目封面取最新生成物而非截图，注释明示「用户可能正看旧版本，封面保持最新」。

## 5. 反面教材 / 风险（源码事实）

1. **无沙箱插件**：任意 URL JS 在主页面直接 `import()`，可读本地凭证；SECURITY.md 自认是「有意的扩展性取舍」。clone 若引入插件机制必须换 iframe/Worker 沙箱。
2. **巨型页面组件**：project.tsx 4242 行、48 useState；agent 可读性/可测性差。这与本项目「组件合同 + verifier」治理路线相反。
3. **无 schema 版本**：项目文档无 version 字段、persist 无 migrate；AGENTS.md（TDCanvas 的）明言「项目尚未上线不需要兼容旧数据」。不适合 clone 借鉴。
4. **死代码残留**：Aitudou 节点类型未注册、`importProject` 无 UI、mask-edit 对话框无引用、`transformAngleDataUrl` 无调用方。
5. **undo 边界粗**：全量快照不区分操作语义（无 per-command 标签），恢复时清空选择。

## 6. 证据边界

- 本文全部为**静态源码阅读**结论（锁定 `16b3127`），未运行应用、未采样 DOM/网络；手感类断言（动画/命中半径）未经实机复核。
- **未与上游 `basketikun/infinite-canvas` diff**：上游约 7k star（官网 canvas.best），本项目从未调研过；TDCanvas 的 canvas-agent、插件系统、画布内核大概率承自上游，Tauri 桌面化/Aitudou 管线/媒体缓存/主题/comfyui-local 大概率为 TDCanvas 新增——该归属判断目前只是**未证实的推断**，如需精确归属应补充上游对照（见 ITERATION_LOG 下一证据队列）。
- 本地工作副本 origin 是 fork（`wubuku/TDCanvas`）；研究基准= upstream 提交 `16b3127`，与 fork 无关。

## 7. 建议的后续动作（不执行，等待授权）

1. 如需精确区分继承/原创：clone `basketikun/infinite-canvas` 为 submodule 做一次 diff 审计（成本：一次调研批次）。
2. 若 LibTV 要补「拖线到空白建节点」「几何分组」「图片历史 pinned 引用」任一能力，先按项目协议走 `LIBTV_UIUX_PARITY_BACKLOG` 的 Par 编号与 verifier 流程，模式卡见 PATTERN_CARDS TD-03/06/08。
3. FrameOS/Jimeng 如需 Agent 化（无头操作画布），优先评估 TDCanvas 的「快照上报 + SSE 回传」桥接形态而非 MCP 直连（PATTERN_CARDS TD-11）。
