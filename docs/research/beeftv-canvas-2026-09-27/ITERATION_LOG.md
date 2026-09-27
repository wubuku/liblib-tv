# beeftv-canvas 调研包 ITERATION_LOG

> 本目录调研包的版本史、覆盖面缺口与下一证据队列。自检：`python3 scripts/check-beeftv-research.py`（只读）。

## 版本史

### v35（2026-09-28）：第十四轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十四轮检查）。
- **第十四轮抽查**：8 处新断言（§3.4/§8.3/§9.2/§10.2/§10.4/§11.2/§12.1/§16）→ §32.13；8/8 吻合。**增补 2 处**：outcome 归一额外容忍 pending/processing/canceled 拼写；表情编辑 provider-mask/local-composite 双模式降级文案。Windows 保留名正则经直接阅读证实（首次 grep 关键词未命中教训记录）。
- **累计 125 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.13 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v34 队列 1（上游增量检查）✅、队列 2（第十四轮抽查）✅。

### v34（2026-09-28）：第十三轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十三轮检查）。
- **第十三轮抽查**：6 处新断言（§10.2/§25.2/§22.6/§12.2/§14）→ §32.12；6/6 吻合（蒙版前缀逐字、宫格钳制公式、creation 事务重读、8 槽权限表逐字、composer 拼装、导出媒体递归收集）。
- **累计 117 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.12 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v33 队列 1（上游增量检查）✅、队列 2（第十三轮抽查）✅。

### v33（2026-09-28）：第十二轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十二轮检查）。
- **第十二轮抽查**：6 处新断言（§4.3/§5.3/§8.1/§10.3/§14/§25.2）→ §32.11；6/6 吻合（四角 ResizeHandle 门控、光晕 strokeWidth 8+blur 3px+opacity 0.18、历史 180ms 防抖、MP4 moov 逐盒扫描、导出 version:4、CreationSubmissionID uniqueIndex gorm tag）。
- **累计 111 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.11 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v32 队列 1（上游增量检查）✅、队列 2（第十二轮抽查）✅。

### v32（2026-09-28）：第十一轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十一轮检查）。
- **第十一轮抽查**：8 处新断言（§2.4/§4.1/§5.1/§7.x/§8.4/§10.1/§12.2/§19/§28.2/§28.4）→ §32.10；8/8 吻合（nodeToAsset 文本须带正文注释逐字、容量中文报错、草稿双锁嵌套、封面串行队列注释、进度五态标签、snap 8px 两处、minimap 24、主题 store 37 行）。
- **累计 105 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.10 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v31 队列 1（上游增量检查）✅、队列 2（第十一轮抽查）✅。

### v31（2026-09-28）：第十轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十轮检查）。
- **第十轮抽查**：8 处新断言（§4.6/§12.1/§13.1/§20/§26.3/§28.3/§10.2/§4.6）→ §32.9；8/8 吻合（z 层级逐档注释、paint order 不持久化注释、模式纯映射注释、4s 兜底、$divide 除零报错、XML 转义、gap=48 常量、workspaceProjectId 继承）。
- **累计 97 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.9 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v30 队列 1（上游增量检查）✅、队列 2（第十轮抽查）✅。

### v30（2026-09-28）：第九轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第九轮检查）。
- **第九轮抽查**：8 处新断言（§4.5/§5.1/§8.4/§9.6/§10.1/§23.4/§26.4）→ §32.8；8/8 吻合（含 frame 连线拒绝、folder 折叠 ≤3 列公式、maxInputCount 中文报错、`@[node:id]` token 构造、prepareClose 三态逐行）。
- **累计 89 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.8 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v29 队列 1（上游增量检查）✅、队列 2（第九轮抽查）✅。

### v29（2026-09-28）：第八轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第八轮检查）。
- **第八轮抽查**：8 处新断言（§2.2/§4.3/§6.x/§7.x/§8.2/§9.4/§10.3/§11.3/§19/§29.3）→ §32.7；8/8 吻合（含 1 处升级为具名常量 NODE_EXTERNAL_HEADER_MIN_SCALE）。
- **累计 81 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.7 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v28 队列 1（上游增量检查）✅、队列 2（第八轮抽查）✅。

### v28（2026-09-28）：第七轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第七轮检查）。
- **第七轮抽查**：8 处新断言（§3.4/§6.1/§8.4/§10.2/§11.1/§11.2/§12.2/§25.3）→ §32.6；8/8 吻合（6 处逐行、1 处域确认、1 处增补）。**增补**：CreateAgentRunInput 实际字段比 §11.1 记录更丰富（reasoningMode/profileRevision/渠道四件套/contextScope），§32.6 已记录。
- **累计 73 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.6 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v27 队列 1（上游增量检查）✅、队列 2（第七轮抽查）✅。

### v27（2026-09-28）：第六轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第六轮检查）。
- **第六轮抽查**：8 处新断言（§4.1/§6.3/§7.6/§9.5/§22.1/§26.2/§28.4/§28.6）→ §32.5；8/8 吻合。
- **累计 65 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.5 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v26 队列 1（上游增量检查）✅、队列 2（第六轮抽查）✅。

### v26（2026-09-28）：第五轮定点抽查 + REPORT 一致性快检

- **上游增量**：v1.5.9 之后仍无新提交（第五轮检查）。
- **第五轮抽查**：6 处（§4.2/§6.2/§9.3/§10.2/§11.1/§13.1）→ §32.4，6/6 域确认。
- **REPORT.md 一致性快检**：机制清单/反面教材/证据边界与现行 34 章正文无冲突、无过期断言。
- **包结构变化**：仅 §32.4 追加；卡/矩阵计数不变（45/44）。**累计 57 处断言抽查全部吻合**。
- **队列清算**：v25 队列 1（上游增量检查）✅、队列 2（第五轮抽查 + REPORT 快检）✅。

### v25（2026-09-28）：第四轮定点抽查 + 上游增量检查

- **上游增量**：再次 fetch —— v1.5.9 之后仍无新提交。
- **第四轮抽查**：8 处新断言（§4.4/§7.1/§9.1/§9.6/§12.2/§13.1/§13.3/§23.3）→ §32.3；8/8 吻合。**累计 51 处断言抽查 100% 吻合**。**BF-39 扩至第六处 LibTV 对齐证据**：默认尺寸层注释「文本节点 350×350 作为首屏复刻基准」「LibTV renders an empty audio node as a square media card」（constant/canvas.ts:14,26-28）。
- **包结构变化**：仅 §32.3 追加 + BF-39 扩充；卡/矩阵计数不变（45/44）。
- **队列清算**：v24 队列 1（上游增量检查）✅、队列 2（第四轮定点抽查）✅。

### v24（2026-09-28）：第三轮定点抽查 + 上游增量检查

- **上游增量**：再次 fetch —— v1.5.9 之后仍无新提交。
- **第三轮抽查**：8 处新断言（§3.2/§5.1/§5.3/§8.5/§10.2/§11.1/§12.3/§16）→ §32.2；8/8 吻合。**累计 43 处断言抽查 100% 吻合**；精确化第 2 处：版本标签首值为 "B"（根媒体隐含 "A"）。
- **包结构变化**：仅 §32.2 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v23 队列 1（上游增量检查）✅、队列 2（第三轮定点抽查）✅。

### v23（2026-09-28）：上游增量检查 + 交互目录一致性核验

- **上游增量**：再次 `git fetch` —— v1.5.9 之后**无新提交**（log 为空），最新 tag 仍为 v1.5.9；§35 审计结论继续有效，无需增量。
- **一致性核验**（INTERACTION_CATALOG × SOURCE_ANALYSIS §6/§31）：3 处目录独有断言定点复核——①双击空白 handler（:119-127，除开菜单外**还清空节点/连线选择与打开的面板**，此细节已补进目录 §1）；②SelectionToolbar 起始行 :21 ✓；③`useCanvasCreateCommands` 共用命令解析且 enabledPluginIds 来自 pluginStates.effectiveEnabled（与 §16 启停传播一致）✓。目录与 §6/§31 无漂移。
- **包结构变化**：无章节增减；INTERACTION_CATALOG §1 一行增补。
- **队列清算**：v22 队列 1（上游增量检查）✅、队列 2（交互目录一致性通读）✅。

### v22（2026-09-28）：上游前移差异审计（v1.5.7 → v1.5.9）

- **方法**：`git fetch origin --tags` 后比对锁定提交 `85c9686` 与新 tag `v1.5.9`（恰好 2 个提交：e8cf506 浅色模式 / e2fd1d3 视频素材限制对齐；42 文件 +1590/-477，后端无 diff）→ SOURCE_ANALYSIS **§35**。
- **审计结论**：
  1. v1.5.8 画布支持浅色模式（appearance 模式三态化、默认外观回落全局主题）+ **恢复主工具栏「画布外观」入口**——撤销了锁定提交中「外观入口已按产品要求移除」的决策，§31.3 已加双向标注（仅对 v1.5.7 成立）。
  2. v1.5.9 视频参考素材校验与错误提示增强（video-validation/generation-error/model-capabilities 增强、seedance provider 简化）——方向与 §9.3 错误码体系一致，未发现与本包断言冲突。
  3. **本包锚点不移动**（README 锚点表新增「上游最新已知 v1.5.9」行）；后续对齐走增量差异审计。
- **包结构变化**：SOURCE_ANALYSIS 34→35 章；卡/矩阵计数不变（45/44）。
- **队列清算**：v21 队列 1（上游前移差异审计）✅。

### v21（2026-09-28）：第二轮断言抽查扩样

- **方法**：对代理章节再抽 10 处此前未抽查过的新断言（§4.3/§4.5/§6.1/§6.2/§6.4/§7.6/§8.1/§9.4/§10.3/§12.1/§13.1）→ §32.1 第二轮台账。
- **结果**：10/10 吻合；**累计 35 处断言抽查全部吻合**。精确化 1 处：导演台默认演员 URL 锁定 `three.js@r185` 官方示例 Xbot.glb（jsdelivr CDN，director-scene.ts:6）。
- **包结构变化**：仅 §32 扩充；卡/矩阵计数不变（45/44）。
- **队列清算**：v20 按需补强（断言抽查扩样）✅。

### v20（2026-09-28）：45 卡 × 44 行全文一致性通读

- **方法**：对 PATTERN_CARDS（45 卡）、ADOPTION_DECISION_MATRIX（43→44 行）、README/REPORT/INTERACTION_CATALOG 的交叉引用与计数声明做全文一致性通读；机械排查「未被矩阵引用的卡」与「仅出现一次的卡号」。
- **发现与修复**：
  1. **BF-02（CSS 变量世界变换 + 交互期降负）是唯一未被矩阵引用的卡**——v3 扩卡时的遗漏。修复：补矩阵第 44 行（ADAPT，理由「通用低风险手法，吸收前实测节点卡开销」）；分桶 ADAPT 7→8、合计 43→44；check 脚本 EXPECTED_ROWS 同步。
  2. 「仅出现一次的卡号」共 44 处为正常形态（卡号只出现在自身标题），非缺口。
  3. 其余交叉引用（§ 引用、VR 对照、tdcanvas 互证标注）通读无发现漂移。
- **一致性设施增强建议（未实施，留档）**：check 脚本可加「每张卡必须被矩阵至少引用一次」的强制项——本次靠人工通读发现，机械化后可在扩卡时自动拦截。
- **包结构变化**：矩阵 43→44 行（BF-02 补行）；卡计数不变（45）；分桶 15/8/16/3/2；README/索引/自检脚本计数同步。
- **队列清算**：v19 按需补强（模式卡与矩阵一致性通读）✅。

### v19（2026-09-28）：viewport 二次核读与渲染细节增补

- **全读**：director-viewport.tsx（1199 行，包作者全文第二遍）→ SOURCE_ANALYSIS **§34**。
- **核读结论**：§23 的全部机制断言经独立阅读**全部成立，无一处需修正**；导演台主文件（workbench 942 行 + viewport 1199 行）至此均经包作者全文精读。
- **渲染细节增补**：模型展示身份 render 阶段屏蔽旧资源；GLTF 采纳整体 try/catch 防半采纳资源 + SkeletonUtils.clone 共享资源「采纳后绝不 dispose source」；**rig 推断正则模式表**（约 40 人形骨骼位 ×4 命名惯例，映射 ≥8 根才 ready）；模型自动归一化（最大边=2、落地 y=0）；演员共享引用材质（被顶材质立即 dispose 防「每次加载泄漏一份」）；BoneController 屏幕恒定尺寸换算（透视/正交两分支）与手指组 dimmed；占位人偶火柴人（14 关节）；录制循环渲染错误立即中止 + 时长 ≥50% 校验；`data-renderer-ready` E2E 信号。
- **包结构变化**：SOURCE_ANALYSIS 33→34 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v18 队列 1（viewport 未逐行段）✅。**至此静态阅读面全量覆盖：包作者全文精读的文件累计约 12,000 行，代理精读覆盖其余主要域。**

### v18（2026-09-28）：导演台 workbench 编排层精读

- **全读**：canvas-director-workbench.tsx（942 行，包作者全文）→ SOURCE_ANALYSIS **§33**（编排层视角，与 §23 机制视角互补）。
- **核心产出**：
  1. canonical 提交 vs 仅镜像的二元纪律（mirrorDraft 用于取消预览/pagehide/卸载兜底，「这些都不是新的用户改动」）；卸载三层分工（pagehide active→commit/idle→mirror + controller 独占落盘；beforeunload 仅声明未确认改动；卸载 effect cancel+mirror）。
  2. 提交粒度纪律：commit 前终结暂存手势；replaceWithoutHistory 分离历史边界与持久化边界；删除关键帧「未命中返回同引用则不 commit」；placement intent 在 commit 内读（异步路径不过时坐标）。
  3. 双 playhead 纪律注释（raw 取值/snapped 写入，防 AutoKey OFF 增量漂移起点错误）。
  4. applyToCanvas/exportClayVideo 的快照时效校验（exportClay 两次校验）+ 输出失败 draft 保留可重试。
  5. **姿势数字精确化**：DirectorPose union 21 值（含 neutral），UI 姿势按钮 20 个（§23 表述精确化）；BoneRotationFields 四元数 q/-q 双距离防回环；运镜 10 种位移偏移表。
  6. 全文件「焦点释放」防误触网（所有按钮点完 releaseDirectorFocusAfterPointer）。
- **包结构变化**：SOURCE_ANALYSIS 32→33 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v17 队列 1（workbench 精读）✅。viewport 主文件主要机制已由 §23 代理覆盖，其余未逐行段降为可选。

### v17（2026-09-28）：交叉校验台账（断言抽查扩样）

- **方法**：对子代理产出章节均匀抽取 12 处承重断言（§4.2/§5.2/§6.1/§7.2/§9.2/§10.1/§11.1/§12.2/§16/§22.2/§25.1/§28.1），逐条回源码复核 → SOURCE_ANALYSIS **§32**（12 行台账 + 累计统计 + 残余边界声明）。
- **结果**：12/12 吻合；连同此前 v1（5 处）/v9（4 处）/v13（3 处）/v16（间接 1 处），**累计 25 处抽查 100% 吻合，未发现断言错误**。ITERATION_LOG 覆盖面登记的「file:line（子代理）」证据强度评级经此轮抽查维持有效。
- **包结构变化**：SOURCE_ANALYSIS 31→32 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v16 队列 1（交叉校验/抽查扩样）✅。静态阅读面主要域已全部覆盖；后续迭代转为按需补强。

### v16（2026-09-28）：画布周边边角（选区浮层/节点面板浮层/主工具栏）

- **全读**：canvas-workspace-overlays.tsx（288 行）、canvas-toolbar.tsx（375 行）→ SOURCE_ANALYSIS **§31**。
- **核心产出**：
  1. 选区浮层定位是命令式直写（ref 优先、无 ref 才走 React state），五路重算触发源（双 Observer + viewport 事件 + resize）。
  2. 节点面板浮层：宽度随节点屏宽 clamp(660,920)、双事件订阅（无节流 graphics 预览 + 拖拽预览）维持贴附、贴附优先查真实节点 DOM；连线快速菜单的 safe width 实时避让 Agent 抽屉。
  3. 主工具栏：tool-registry + 用户偏好（设置弹窗调排序/显隐）；`ToolbarHandlers` 全量接口 no-op 占位模式；外点关闭豁免 antd 颜色选择器；Agent 抽屉打开时 dock 避让 340px。
  4. **BF-39 扩至第五处命名级 LibTV 对齐证据**：工具栏注释「Match LibTV's tool shortcuts」、`libtvChrome`「兼容 LibTV 视觉基线」prop、面板底部间隙注释「LibTV reserves only a small gap above the bottom controls」；并核实 V/H 菜单文案错位（box-select 显示名「移动」）是上游文案混乱的第二处。
- **包结构变化**：SOURCE_ANALYSIS 30→31 章；卡计数不变但 BF-39 内容扩充；矩阵不变（45/43）。
- **队列清算**：v15 队列 2（画布周边边角）✅。

### v15（2026-09-28）：字幕高亮与 SRT 重分段（时间线域收官）

- **全读**：subtitle-highlights.ts（91 行）、subtitle-highlight-service.ts（50 行）、subtitle-highlight-runner.ts（113 行）、srt-parser.ts（67 行）、srt-resegment.ts（131 行）→ SOURCE_ANALYSIS **§30**。
- **核心产出**：高亮「文本自证」有效性模型（highlightText===sourceText.slice 即有效、文本一变即 expired、重分段重映射找不到显式 dropped）；LLM 输出双重校验；无模型回退按终止标点取首句「保证功能不中断」；批处理 worker 池（batch 30/并发 3/共享游标/首错短路）；SRT 容错解析与序号归一；重分段断点优先级（中文标点>英文标点>空格>硬切）+ 300ms 最小时长的「接受违规不崩溃」策略。**时间线域至此全量覆盖**。
- **包结构变化**：SOURCE_ANALYSIS 29→30 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v14 队列 2（subtitle-highlight/srt-resegment）✅。

### v14（2026-09-28）：provider 域深补（水合/鉴权/出站边界）

- **方法**：只读代理聚焦深读三处（provider.go 水合段、provider_protocol.go:517-743 鉴权段、internal/outbound/outbound.go）→ SOURCE_ANALYSIS **§29**。
- **核心产出**：
  1. 水合两级策略 {requireURL, preferURL}：interfaceType 白名单 + Mask 强制内嵌 + 插件 RequiresPublicMediaURLs 强制 URL；本地模式 requireURL 直接拒绝（「loopback URL 外部模型不可达，不能伪造」）；HMAC 签名 URL TTL 4h；方舟可信素材 asset:// 改写特例；视频槽位排序=首帧/尾帧/普通参考。
  2. 鉴权驱动实为 **12 种变体**（含 aws-sigv4 region 从 hostname 推断+四轮 HMAC、tc3 规范头仅 content-type;host、volcengine-v4 官方 SDK、未知显式报错）；凭证 AES-256-GCM 落盘（enc:v1: + 0600 settings-key）、任务落库前递归加密；日志脱敏（query 不入库/敏感键 REDACTED/data: 摘要/128KB 上限）。
  3. 出站边界：**防 DNS rebinding 的「校验与拨号同源解析」设计**（消除 TOCTOU）；重定向逐跳复检；header 封禁表防覆盖鉴权头；响应大小三重强制；熔断+渠道槽位租约；如实观察 isPublicMediaURL 仅查 scheme、内网拦截依赖出站层。
  4. **定位修正**：鉴权驱动在 provider_protocol.go:517-743（v9 曾引 provider_http_client.go:517-593，该段实为 URL 拼接；8 种→12 种变体）。
- **包结构变化**：SOURCE_ANALYSIS 28→29 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v13 队列 1（provider 域余下）✅。

### v13（2026-09-28）：时间线编辑器八插槽面板 + editor store

- **方法**：只读代理深读 editor/ 八面板（约 2800 行）+ editor-store.ts + editor-slot-registry.ts + 宿主 editor.tsx 接线；包作者抽查 3 处承重断言全部吻合（store dispatch fail-closed、panel preview-then-commit、AI ≤3 阈值）→ SOURCE_ANALYSIS **§28**。
- **核心产出**：
  1. editor store：命令唯一入口（inPreview 拒绝 dispatch）+ 手势三分（previewGesture/commitGesture/cancelGesture，「手势不逐帧污染撤销栈」）+ 1.5s 防抖串行保存链 + 纯 UI 字段（selectedClipId/transportMs）不入历史。
  2. timeline-panel：preview-then-commit 拖拽、手势状态 useRef 防每帧重渲染、「手势数学与渲染同源 pxPerMs」、trim-start 同步 sourceStartMs、吸附比较陷阱处理。
  3. preview-monitor：rAF 本地时钟 80ms 节流回写、单一 video 元素（非池）从动时钟（0.35s 容差）、H.265 转码副本终态护栏。
  4. asset-ingest：nodeId 引用 vs directMedia 直连双形态；**画布选材是自动同步**（产物 ready 即并入项目素材）；文件名+kind 去重。
  5. ai-assistant：完整调用链（显式覆写 text 模型→同源 system prompt→流式→parse→整批校验→≤3 直执行/>3 命令清单预览卡→applyPlan 整卡替换汇报）。
  6. export/transcription/subtitle-tools/inspector：失去媒体的片段跳过不阻断导出；渲染计划「无源片段不补黑场由 gap 统一覆盖」（线上黑场翻倍实锤注释）；转写/SRT 单条 rebuildSubtitleClips 原子替换；字幕=节点只读快照语义；inspector 提交粒度与控件类型匹配（onBlur vs onChange）。
  7. slot-registry：渲染期 fail-closed 权限表（被拒插槽渲染诊断条）+ 命令代发运行期断言；**五个入口全收敛到同一 dispatch 通道**——「同一注册表约束三方」在面板层的完整体现。
- **包结构变化**：SOURCE_ANALYSIS 27→28 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v12 队列 1（editor 面板与 store 接线）✅。

### v12（2026-09-28）：导演台 UI 边角

- **全读**：director-onboarding.ts（245 行）、canvas-director-onboarding.tsx（253 行）、director-sequencer.tsx（281 行）、director-viewport-dock.tsx（79 行）、canvas-director-node-panel.tsx（78 行）、director-view-toolbar.tsx（55 行）、canvas-director-template-modal.tsx（34 行）→ SOURCE_ANALYSIS **§27**。
- **核心产出**：
  1. 引导状态机：「引导是提示不是场景内容」（绝不入 DirectorScene/undo）+ schema 版本化防卡死 + 「宁可再引导一次」解析哲学 + 注释记录的 `??` 短路 scope 校验 bug 教训。
  2. 引导浮层：非阻塞设计（region 非 dialog、无遮罩不抢焦点——「任何模态化都会把照着做变成先关掉」）；**并发写锁换代语义**（换代整体替换实例而非 release 共享实例；run() 拿锁时刻同步捕获，绝不在 finally 重读 ref）；IndexedDB 失败时宁可隐藏不骚扰。
  3. Sequencer：关键帧从惰性 span 改真实 button（「之前关键帧一旦记录就无法删除」）；Camera Cut 概览轨保持只读避免双删除入口；选择失效守卫；fps 帧格吸附。
  4. 工具面：「改内容 vs 换眼睛」二分（取景切换不进 undo）；文字标签优于图标（3D/CAM 含义相反）；节点面板诚实空态（不画伪 3D）+ failedUrl 记 URL 非布尔；模板显式选择（呼应「绝不在用户没选过时塞演员」）。
- **导演台域至此全量覆盖**（6432 行中除 workbench/viewport 主文件的未逐行段外均已读或由 §23 覆盖）。
- **包结构变化**：SOURCE_ANALYSIS 26→27 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v11 队列 1（导演台 UI 边角）✅。

### v11（2026-09-28）：官方应用清单 + 技能域

- **全读**：official-applications.ts（27 行）、skill-runtime.ts（298 行）、api/skills.ts（245 行）、skill-drafting.ts（58 行）、canvas-skill-mentions.ts（7 行）、skill-catalog.ts（30 行）→ SOURCE_ANALYSIS **§26**。
- **核心产出**：
  1. 官方应用清单唯一来源收敛（5 个应用型插件 ID）+ 三处清单漂移 bug 的整改注释——与本项目「唯一源规则」同构。
  2. Skill 数据模型：GitHub 安装（ref/subdir/autoUpdate）+ 自动同步状态机（syncStatus/lastSyncedAt）；listAddedSkills 的 scope 缓存 + 15s TTL + in-flight 合流 + 三级退避重试 + `canvas-skills-changed` 失效广播。
  3. **Skill Runtime 单一所有权**：canvas-skill-mentions.ts 仅是兼容 shim（「canvas code must not load files or expand skill prompts independently」）；4 profile 注册表（值统一、留分化位）；linked-context 投递的预算均分 + SKILL.md 优先 + 链接文件「required 短语正则 > 术语重合度（中文二元组）> 位置」排序 + 截断明示；`<skill-context>` XML 包裹 + 安全前言；**provenance（ids/versions/files+sha256）可审计**。
  4. AI 技能草稿走服务端提示词模板占位符（印证 features.mdx「平台级 LLM 任务只走后端提示词目录」）。
- **包结构变化**：SOURCE_ANALYSIS 25→26 章；卡/矩阵计数不变（45/43）。
- **队列清算**：v10 队列 1（官方应用与 skills）✅。
- **验证记录**：`check-beeftv-research.py` OK（45/45、43/43）；`verify-docs.py` 仍仅报 user-manual 并行会话在途断链（增至 2 处，均为 `docs/user-manual/tdcanvas-canvas/10-tasks/` 未提交 stub，非本包），过滤后无其他断链。

### v10（2026-09-28）：时间线几何 + 后端任务域（双队列项）

- **时间线几何（§24，包作者全读）**：timeline-build/tracks/placement/snap/view 五文件（567 行）。要点：四文件头注释「移植自 lingji-cut」——BeefTV 自身第三方代码移植的 provenance 数据点；画布→时间线单向快照（重建不覆盖、字幕相对视频片段偏移、只处理已入轨节点）；放置与吸附分离（重叠即拒绝 vs 最近目标吸附，阈值屏幕像素换算与 BF-14 同思路）；视图数学（96px/s、zoom 0.02–4、标尺 12 档 ≥64px）。
- **后端任务域（§25，只读代理深读约 4900 行）**：
  1. 任务生命周期：创建即服务端冻结选型；状态迁移全部 CAS；三层租约（任务 45s/15s 续租、worker 槽位、creation 会话 epoch）；**上游轮询=同步循环+defer 回池再领取**，非常驻定时器；取消对账（仅 Veo/火山支持上游取消）；失败任务人工恢复口「只查询不重建」。
  2. **幂等修正（对 §9.2）**：clientOperationId/attemptGroupId/retryOf 后端 0 命中——普通任务无请求级幂等；真正幂等在 creation（ItemKey+uniqueIndex）与 Cloud Agent（幂等键即主键）；后端防重复上游调用靠「冻结选型+派发 CAS+provider Idempotency-Key+恢复只读」。§9.2 第 4 层已改写并交叉引用。
  3. **未发现积分扣费/退款实现**——开源后端「防重复计费」实为防重复上游调用，计费在 hosted 侧。
  4. 回传通道全景：普通任务完成无推送（webhook 0 命中），前端 2s 轮询唯一；例外 Cloud Agent 媒体任务后端同事务直建画布节点；画布 revision SSE（250ms 查库推信号）；ApiCallLog 每上游 HTTP 一行并承担 provider_request_id 恢复职责。
- **包结构变化**：SOURCE_ANALYSIS 23→25 章；README 章节枚举改为分组式；卡/矩阵计数不变（45/43）。
- **队列清算**：v9 队列 1（backend task/generation）✅、队列 2（时间线几何 5 文件）✅。
- **验证记录**：`check-beeftv-research.py` OK（45/45、43/43）；`verify-docs.py` 报 1 个缺失链接 `docs/user-manual/tdcanvas-canvas/10-tasks/generate-images.md → 90-troubleshooting.md`——经查该文件为**并行用户手册会话的在途修改**（mtime 01:59、未提交 ` M`、引用了尚未创建的页面），不属本调研包、本会话未触碰 user-manual，按仓库纪律不回滚他人变更；本包自身链接在 v9 轮 verify-docs（1102 文件）已全绿。

### v9（2026-09-28）：导演台 three.js 内部机制

- **方法**：只读代理精读 director 域约 6400 行（director-viewport.tsx 1199 行、director-save.ts 443 行、director-view-modes.ts 362 行、director-animation-semantics/gesture-transaction/recovery/repro-* 等）；包作者抽查 4 处承重断言全部吻合（Canvas 稳定引用与 frameloop="demand"、gizmo 冻结声明式 prop、历史 50 上限 `slice(-49)/slice(0,50)`、草稿键+300ms+baseUpdatedAt）→ SOURCE_ANALYSIS **§23**（9 节）。
- **核心产出**：
  1. R3F 渲染管线：Canvas 配置必须模块级稳定引用（context lost 重建陷阱）、`frameloop="demand"`+全量手动 invalidate、DPR 封顶 1.5、三相机指针切换互不污染。
  2. **TransformControls 冻结式手势事务**（BF-43 新卡）：显式 attach + 手势期冻结声明式 prop + 从同一 Object3D 读回 + begin/end 恰好一个终态（pointerup/blur/hidden=commit、Escape/pointercancel=cancel）——本项目 Director 硬约束的成熟参照实现。
  3. 关键帧/动画：手写插值（rotation 走四元数 slerp）、骨骼四层分层合成（rest×poseDelta/motion→override→keyframe）、AnimationMixer 只管 motion clips 且 `setTime` 声明式求值、21 姿势=纯数据四元数增量表、**Auto Key 双语义**（关=增量搬全轨道保渲染不变）。
  4. **保存管线**（BF-44 新卡）：立即同步草稿 + 300ms 防抖排空循环 + revision 确认 + baseUpdatedAt 基线恢复（陈旧残留不弹恢复）+ prepareClose 三态 + localStorage 不可用显式抛错。
  5. **白名单诊断 + 复现基建**（BF-45 新卡）：11 稳定码/常量 message/字段白名单；确定性离线复现场景 + 15 条手工复现矩阵 + 注入变体（手写 glTF、确定性 404）。
  6. 取景 7 模式（viewMode 绝不入场景不产历史）、荷兰角先 up 后 lookAt、正交双跨度包围盒；预览出图 overrideMaterial+手动 render+toBlob、录制 vp9→vp8 降级 + webm 时长校验。
- **包结构变化**：SOURCE_ANALYSIS 22→23 章；卡 42→45（BF-43/44/45）；矩阵 40→43 行（均 ADOPT_METHOD；分桶 15/7/16/3/2）；README/索引/自检脚本计数同步。
- **队列清算**：v8 队列 1（导演台内部）✅ 完成。

### v8（2026-09-28）：六个内置插件逐个深读

- **全读**：eagle.ts（371 行）、prompt-optimizer.ts（352 行）、workflows.ts（44 行）、ai-art-critique.ts（45 行）、media-conversion.ts（37 行）、editor/editor-shell.tsx（92 行）+ editor/index.ts → SOURCE_ANALYSIS **§22**（六插件逐个档案 + 跨插件模式归纳）。editor/ 八个插槽面板实现（约 2800 行）未逐行读，其产品语义已在 §18.2.7/§21 覆盖。
- **核心产出**：
  1. 六种声明贡献面 + 两类指令式钩子全景；「manifest 声明能力目录、指令式代码只做接线」双轨。
  2. eagle：后端代理架构（浏览器不直连）、导入映射表（视频 1280×720 展示兜底不改原文件、文本明确报错）、「自动写回失败不得误报为已保存」诚实边界。
  3. prompt-optimizer：strict tool-call 契约 + **14 个模型族适配 profile**（含 Seedream/即梦、Seedance——直接对应 LibTV 生态模型，与 open-canvas 包模型能力矩阵同题）；失败回退原提示词；权限声明比实际使用宽（观察）。
  4. ai-art-critique：唯一贡献画布节点的内置插件 + agentActions/readAgentNode 双 Agent 钩子 + sourceFingerprint stale 检测（与 media-conversion 节点同构）。
  5. editor-shell：唯一 v2 manifest，一个插件声明 8 个 editorSlots、渲染器经 registerEditorSlot 指令式注册。
  6. 「documentation 即边界声明」模式：每插件内嵌文档明确「不做什么」。
- **包结构变化**：SOURCE_ANALYSIS 21→22 章；卡/矩阵计数不变（42/40）。
- **队列清算**：v7 队列 1（内置插件逐个深读）✅ 完成。

### v7（2026-09-28）：时间线域深读（命令状态机 / 200 层历史 / AI 命令契约）

- **全读**：`web/src/lib/timeline/` 四个核心文件（editor-commands.ts 364 行、editor-history.ts 57 行、ai-command-schema.ts 220 行、timeline-summary.ts 72 行）→ SOURCE_ANALYSIS **§21**。
- **核心产出**：
  1. ADR-0002 命令协议：`{op,payload}` 可序列化 + 纯函数 handler + fail-closed 校验；12 内置 op 全枚举；逐条校验纪律（trim 源时长上界、setClipProperty 白名单、确定性 id 派生、removeTrack 保底轨道）；插件经宿主 API 与内建命令共用同一注册表。
  2. **200 层结构共享快照栈**：全量快照但免深拷贝（依赖命令层不可变更新）——在同一产品内化解了画布本体 §8.1「补丁栈 vs 快照栈」两难。
  3. ADR-0007 AI 命令契约：**同一注册表约束宿主/AI/插件三方**；`commands:[]` 合法终态语义；整批 dry-run 任一失败整批拒绝；`AI_EDITING_MAX_COMMANDS=8`（schema 硬上限）与 features.mdx「≤3 直执行」分界并存；`AI_COMMAND_SCHEMA_VERSION` 供 golden 对齐。
  4. 确定性中文摘要（60 行折叠/24 字截断/无随机）——AI 上下文与诊断共用。
  5. **三种历史粒度对照表**（时间线 vs 画布本体 50 条补丁栈 vs Agent 整批快照栈，10 个维度）+ 核心洞察：结构共享使快照栈成本趋近补丁栈且保住命令语义；画布本体未跟进的原因是编辑入口分散（推断）。
- **证据边界补充**：ADR-0002/0007 编号在代码注释中被引用，但 ADR 文档不在公共快照（docs/content/docs 仅 backend/overview/plugins）。
- **包结构变化**：SOURCE_ANALYSIS 20→21 章；卡/矩阵计数不变（42/40）。
- **队列清算**：v6 队列 1（时间线域）✅ 完成。

### v6（2026-09-28）：声明式协议引擎深读

- **全读**：`backend/internal/protocol/expression.go`（665 行全读）+ `manifest.go` 适配器执行段（:412-561）+ 函数清单 → SOURCE_ANALYSIS **§20**。
- **核心产出**：36 个 `$` 算子全集与语义（含 `$indexObject` 编号键适配、`$eq` canonical-JSON 比较）；「miss 静默 nil」路径语义与 `"false"/"0"/"no"/"null"` 真值规则（与前端 hasAudio 解析跨端一致）；适配器 create/poll/cancel/result/agent 生命周期与 fail-closed 请求校验；多候选响应路径容错 + sha256 合成 tool-call ID；同步二进制「空响应必须失败」；`newapi-channel-1` 双投影兼容 shim（引擎保持纯声明、个别兼容以 ID 特判收容）。
- **包结构变化**：SOURCE_ANALYSIS 19→20 章；卡/矩阵计数不变（42/40）。
- **队列清算**：v5 队列 1（协议引擎模板表达式）✅ 完成。

### v5（2026-09-28）：测试套件全景 + 4 件抽读

- **规模发现**：`web/test/` 共 292 个测试文件，**111 个 canvas 前缀**——测试命名清单本身构成上游画布机制的自我索引 → SOURCE_ANALYSIS **§19**。
- **抽读 4 件**（与包内承重断言互证）：①连线快速创建菜单测试钉死「引用该节点生成」+7 命令（smart-edit/director/script 置灰），且测试名显式 **"LibTV-style compact list layout"**（BF-39 第四处命名级 LibTV 对齐证据，卡已更新）；②键盘删除文本合同（BF-18 互证）；③刷新对账 effect 断言无 `localMode` 分支（BF-27 互证）；④LibTV 夹具契约精确数字（dense=61 节点：38 图/17 视频/6 音频——BF-37 补充）。
- **包结构变化**：SOURCE_ANALYSIS 18→19 章；卡/矩阵计数不变（42/40）。
- **队列清算**：v4 队列 1（local-* 边界测试所属的测试套件面）以「全景+抽读」方式完成——111 个画布测试未逐个全读，按名索引 + 4 件抽读已满足调研深度；逐个精读仅在对照实现具体机制时按需进行。

### v4（2026-09-28）：features.mdx 产品功能清单逐条对照

- **方法**：全读 `docs/content/docs/overview/features.mdx`（359 行）18 个功能节，与已采源码证据逐节对照，三态标注（一致/新增细节/超出范围）→ SOURCE_ANALYSIS **§18**。
- **对照结果**：
  1. **零冲突**：7 组数值/语义断言抽样（5 分钟备份间隔/20 份/350ms/3s/5×5 宫格/单悬停解码器/整理泳道规则）全部与静态阅读吻合；产品文档明示「不提供多人实时协同」与 §14 后端语义吻合。
  2. **新增细节 8 项**（§18.2）：智能引用 AutoLink 匹配器（候选仅限已连接激活素材、`图1/image 1`/独立序号、跳过歧义，`canvas-resource-mention-textarea.tsx`——与 LibTV AutoLink 同题第三样本）；强制覆盖保存的素材重绑与「素材先于画布」顺序（`canvas-asset-repair.ts`）；提示词放大编辑窗口参数；多角度 3D 编辑器贴节点形态；批量创作表交互面（全局提示词/跨行交换/`canvas_edit_batch_table`）；自由起点起始框交互；时间线编辑器（**200 层命令历史**对照画布本体 50 条补丁栈、fail-closed `timeline.command` 权限、whisper.cpp 转写、AI 助手 ≤3 命令直执行）；云端 Agent 记忆体系（remember_lesson 待审/用户压缩/recall_lessons 索引注入）与插话/终态冻结。
  3. **表述修正**：§11.1「服务端工具全集」改为「展示层清单（非全集）」——分镜域与 `canvas_edit_batch_table` 等域工具在能力 registry 中（features.mdx:43），v1 表述过强。
- **包结构变化**：SOURCE_ANALYSIS 17→18 章；卡/矩阵计数不变（42/40）。
- **队列清算**：v3 队列 1（features.mdx 对照）✅ 完成；队列 2-5 顺延。

### v3（2026-09-28）：插件运行时 + 本地伴随进程

- **新增证据**（静态阅读，锁定 `85c9686`）：
  1. 前端插件运行时（`lib/plugins/` 全目录 + `use-plugin-store` + 抽样 `plugin-packages` manifest）→ SOURCE_ANALYSIS **§16**：双插件体系（6 个编译期内置 TS 插件 × 84 个后端纯声明式协议包，前端 import 图与 plugin-packages 零交集）；manifest v1/v2、`entry` 遗留字段、`worker` runtime 无引用；sandbox renderer **纯占位**（「等待隔离运行时」）；安全模型=「前端零第三方代码执行 + 声明式权限 fail-closed + 后端上传物纯数据」，与 TDCanvas 无沙箱直执行构成两极。
  2. 本地伴随进程 → SOURCE_ANALYSIS **§17**：`framefield-local-runtime`（默认 127.0.0.1:17371，强制精确 loopback origin）；模块 canvas-agent/dreamina/portrait-clearance/depth·lineart·pose-estimation 各持独立 scope；浏览器 CryptoKey 注册 + scope 会话（idb）；响应 64KB/32MB 上界、重定向判无效；估计请求三重响应校验、CPU device、模型缓存自管。**观察**：与 TDCanvas canvas-agent 同构且端口同为 17371（巧合或惯例未考证，仅记录）。
  3. 新卡 **BF-41**（双插件体系）、**BF-42**（本地伴随进程）；矩阵 38→40 行（39/40 均 RESEARCH_ONLY；分桶 12/7/16/3/2）；SOURCE_ANALYSIS 15→17 章。
- **v2 缺口队列清算**：队列 1（插件运行时）✅；队列 2（本地推理运行时）✅（§17 已覆盖 estimation 三模块与 media-conversion 的接入点）；队列 3（features.mdx）部分——已定位章节结构（359 行，「画布保存保护与版本记录/画布智能引用/批量创作表/画布抓手与框选」等章节与已采证据对应），完整产品面对照顺延 v4。

### v2（2026-09-28）：后端画布历史 + 上游测试套件 + LibTV 对齐证据

- **新增证据**（均静态阅读，仍锁定 `85c9686`）：
  1. Go 后端 `backend/internal/repository/canvas_history.go`（165 行全读）+ `docs/content/docs/backend/backend-database.mdx` 画布章节 → SOURCE_ANALYSIS **§14**：`canvas_projects` revision CAS、`canvas_snapshots` 摘要列与 (canvas_id,revision) 唯一、保存单事务（采样判定=revision 前进且过 5 分钟 cutoff 或 force、引用保护须全部 ready、20 份保留清理）、「素材+画布」联合发布事务、同物理对象别名引用保护、恢复形成新版本不回写 revision、旧客户端缺 revision 保存 428、schema v13/v23 迁移线、「画布 metadata 不作为生产完成度真相源」立场。
  2. `web/test/` 画布四测试（canvas-grid-viewport / canvas-spatial-index / canvas-media-performance / canvas-node-title-interaction，共 546 行全读）→ SOURCE_ANALYSIS **§15**：双轨视口精确回归钉（translate3d 公式/CSS 变量/事件频率/网格零写入）、50k 节点空间索引夹具、媒体激活单激活与「InactiveVideoPreview 不得含 video 元素」、音频自绘播放器与手势隔离、Vidstack 控制面 CSS 合同、hasAudio 推导链、标题拖拽/重命名 aria 分工。
  3. **LibTV 对齐证据（BF-39 新卡）**：测试名显式命名「LibTV 800% precision zoom ceiling」（`viewportAtScale` clamp 8，与滚轮 clamp 0.05–2 双轨）、「does not eagerly load or resize LibTV thumbnails」（`importedFromLibTV` 早退）、libtv-res 快照首帧推导——BeefTV 把 LibTV 行为当作用例钉进回归，与本项目源站采样互证。
  4. **源码文本断言测试（BF-40 新卡）**：readFileSync+toContain 把实现细节钉成文本合同（pretest 门禁），与本 verifier 体系互证。
- **包结构变化**：PATTERN_CARDS 38→40（BF-39/40）；ADOPTION 矩阵 36→38 行（行 37=RESEARCH_ONLY、行 38=ADOPT_METHOD；分桶 12/7/14/3/2）；SOURCE_ANALYSIS 13→15 章；README/索引计数声明同步；`check-beeftv-research.py` 期望值同步。
- **v1 缺口队列清算**：队列 1（canvas_history.go + web/test 画布测试）✅ 完成；队列 2 部分完成（backend-database.mdx 画布/资源章节已读；http-api.mdx 确认为高层索引文档 36 行，无逐路由清单，无进一步挖掘价值）。队列 3/4 顺延。

### v1（2026-09-27）：首版落档

- **基线**：上游 `glanderness/BeefTV` 锁定 `85c9686c87a4c176449e29292beba8b96dc430bb`（tag v1.5.7，2026-09-27），工作树干净，origin 即 upstream（非 fork）。
- **包内容**：README / REPORT / SOURCE_ANALYSIS（13 章）/ INTERACTION_CATALOG（10 节 + 快捷键全表）/ PATTERN_CARDS（BF-01..38）/ ADOPTION_DECISION_MATRIX（36 行）/ 本日志；自检脚本 `scripts/check-beeftv-research.py`。
- **方法**：
  1. 结构勘察（目录/依赖/体量/AGENTS.md 架构约定）+ 版本锚定（git log/tag/VERSION）。
  2. **7 路并行静态精读**（只读子代理）：①交互控制器（connection/selection/keyboard/viewport/菜单）②渲染性能体系（render model/虚拟化/空间索引/Leafer/小地图/媒体预览）③历史与持久化（undo/operation contract/storageRevision/版本历史/导出）④节点体系（类型/注册表/DOM/尺寸/分组/连线渲染）⑤生成管线（生命周期/幂等/重试/批量/布局/引用/同步）⑥上传与媒体工具（上传管线/图片工具/ffmpeg 视频/人脸检测/缓存）⑦Agent 与集成（协议/导演台/分镜/工作流/工作区/LibTV 导入）。
  3. 包作者人工核读承重文件全文：`components/canvas/infinite-canvas.tsx`（495 行）、`stores/canvas/use-canvas-store.ts`（621 行）。
  4. **抽查**：对子代理结论中 5 处承重断言（指针意图路由、storage-revision 文档结构、性能模式阈值、CanvasOperation 枚举、Delete-先连线）直接对源码复核，全部吻合。
- **一致性设施**：`check-beeftv-research.py` 校验 § 交叉引用、BF 卡号解析、矩阵行号连续性与分桶汇总一致、README/docs 索引计数声明一致。
- **与既有包的关系**：沿用 tdcanvas-2026-09-26 的包结构与分桶语义；与 tdcanvas 包的三处结论互证（统一画布指令集、拖线建下游、媒体版本/历史两极）；与 open-canvas 包的引用语义合同（AUTOLINK/VR-015/VR-017/VR-021）做对照标注。
- **覆盖面缺口（v1 已知未读）**：
  - Go 后端：`backend/internal/repository/canvas_history.go`（项目版本历史的后端权威）、task/asset/generation 域内部、`api_test.go` 中 hosted-only 路由清单全貌。
  - `web/test/` 测试套件（预提交测试 5 个：local-only-source-boundary、local-workspace-bootstrap、local-asset-repository-boundary、local-task-events、channel-model-catalog + canvas-grid-viewport）与 `test/` 其余测试（canvas-media-performance、canvas-node-title-interaction、canvas-spatial-index 等）——上游自己的回归断言尚未读。
  - `docs/content/docs/`（features.mdx、backend/http-api.mdx、backend-database.mdx、code-map.mdx）站点内容。
  - `plugin-packages/`（89 个插件）与 `lib/plugins` 插件运行时细节；`services/` 中 media-conversion/local-runtime（本地推理）域。
  - 时间线（timeline）域与导演台 three.js 内部（仅读了与画布的边界）。
- **下一证据队列（按价值排序）**：
  1. `canvas_history.go` + `web/test/canvas-*` 测试：补全版本历史后端语义与上游回归断言清单（纯静态，无安全边界问题）。
  2. `docs/content/docs/backend/http-api.mdx` + `backend-database.mdx`：任务/资源/画布项目的后端数据模型总表。
  3. media-conversion 本地推理运行时（estimation services）与插件运行时沙箱现状。
  4. （需运行/浏览器授权，暂缓）真实启动桌面或 web 形态做运行时审计——按 tdcanvas 包 RUNTIME_AUDIT 的「真实素材非付费路径」红线执行，且不得触发真实生成（BeefTV 接真实模型渠道，成本红线同样适用）。

## 覆盖面登记（v2 更新）

| 域 | 覆盖 | 证据强度 |
|---|---|---|
| 画布内核/视口/输入 | 全 | file:line + 人工核读 + 上游回归测试钉（§15） |
| 状态/持久化/rebase/生成事务 | 全 | file:line + 人工核读 |
| 节点/连线/交互 | 全 | file:line（子代理） |
| 渲染性能/虚拟化/Leafer/媒体预览 | 全 | file:line（子代理）+ 上游测试钉 |
| 历史/版本/导出/回收站 | 全（含后端权威语义 §14） | file:line（子代理）+ Go 仓储全读 |
| 生成管线/防重计费/批量 | 全 | file:line（子代理） |
| 上传/图片/视频工具/人脸/缓存 | 全 | file:line（子代理） |
| Agent/导演台/分镜/工作流/工作区/LibTV 导入 | 全（边界级） | file:line（子代理）；three.js 内部未读 |
| Go 后端 | 画布历史/数据模型/资源生命周期（database.mdx + canvas_history.go）；任务/Agent 执行域未读 | file:line |
| 测试套件 | 全景：292 文件/111 canvas 前缀按名索引（§19）；8 个测试全读（画布四件 §15 + 抽读四件 §19）；其余按需 | file:line |
| 文档站 | backend-database.mdx 画布/资源章节；http-api.mdx（36 行高层索引）；**features.mdx 全文逐节对照（§18）** | file:line |
| 插件包 / 插件运行时 / 本地推理 | 插件运行时与双体系全（§16）；本地伴随进程与 estimation 三模块全（§17）；89 个 plugin-packages 仅抽样 3 个 manifest | file:line |
| 运行时行为 | 未执行 | 静态阅读边界声明见 REPORT §6 |

## 覆盖面登记（v9 更新）

| 域 | 覆盖 | 证据强度 |
|---|---|---|
| 画布内核/视口/输入 | 全 | file:line + 人工核读 + 上游回归测试钉（§15） |
| 状态/持久化/rebase/生成事务 | 全 | file:line + 人工核读 |
| 节点/连线/交互 | 全 | file:line（子代理） |
| 渲染性能/虚拟化/Leafer/媒体预览 | 全 | file:line（子代理）+ 上游测试钉 |
| 历史/版本/导出/回收站 | 全（含后端权威语义 §14） | file:line（子代理）+ Go 仓储全读 |
| 生成管线/防重计费/批量 | 全 | file:line（子代理） |
| 上传/图片/视频工具/人脸/缓存 | 全 | file:line（子代理） |
| Agent/分镜/工作流/工作区/LibTV 导入 | 全（边界级） | file:line（子代理） |
| 导演台 | **内部机制全（§23：渲染管线/手势事务/关键帧/保存/恢复/取景/出图）** | file:line（子代理）+ 4 处抽查吻合 |
| Go 后端 | 画布历史/数据模型/资源生命周期（§14）+ 协议引擎（§20）；task/generation 域未读 | file:line |
| 测试套件 | 全景 292/111 按名索引（§19）；8 个测试全读 | file:line |
| 文档站 | backend-database.mdx 画布章节；http-api.mdx 定性；features.mdx 全文对照（§18） | file:line |
| 插件 | 机制面（§16）+ 六内置插件能力面（§22）+ 协议包抽样 | file:line |
| 本地伴随进程 | 全（§17） | file:line |
| 时间线 | 命令/历史/AI/摘要四核心面全（§21）；5 个几何文件与 editor 面板未读 | file:line |
| 运行时行为 | 未执行 | 静态阅读边界声明见 REPORT §6 |

## 下一证据队列（v35 后剩余）

1. （需运行/浏览器授权，暂缓）运行时审计——按 tdcanvas 包 RUNTIME_AUDIT「真实素材非付费路径」红线，且不得触发真实生成。
2. 静态阅读面已全量覆盖（**125 处断言抽查 100% 吻合** + 卡/矩阵机械校验 + 十四轮上游增量检查 + 目录/章节一致性核验 + REPORT 快检）；后续迭代转为按需补强：用户点名的域、上游再次前移时的增量差异审计（v1.5.9 之后）、实现对照时的定点深读。
