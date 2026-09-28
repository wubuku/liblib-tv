# beeftv-canvas 调研包 ITERATION_LOG

> 本目录调研包的版本史、覆盖面缺口与下一证据队列。自检：`python3 scripts/check-beeftv-research.py`（只读）。

## 版本史
### v129（2026-09-29）：§2/§7/§10/§12/§24 补样（live 写入体/时间线构建体/首帧水合去重/CanvasProject 21 字段/TapNow 端点体/dark 主题值）+ depth-action 分叉记录 + 上游增量检查

- **上游增量**：main 无 v1.6.6 后新提交；**depth-action 分支与 main 分叉并行**（尖端 5806524 备发布 v1.6.0，163 文件 +10466/-2941 差异）——该分支未死，合流时需双向差异审计。
- **v129 抽查**：6 处新断言 → §32.111；6/6 吻合（live 视口 translate3d 写入体逐字、buildTimelineFromNodes content/storageKey 过滤 + 游标排列、首帧水合 requestKey 在途去重 + 失败可重试、CanvasProject 类型体恰 21 字段与 row 598 互证、TapNow { shareId } 端点体、dark 主题三值）。
- **台账勘定延续**：台账 **695 行** + pre-ledger 13 = **708 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.111 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v128 后队列（未锚定实现体抽样）✅。

### v128（2026-09-28）：§30/§7/§23/§8/§16 补样（高亮 system prompt 契约/prompts 五函数/dark accent/H 键显隐语义/restoreProject 消费面/declarative runtime）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v128 轮增量检查）。
- **v128 抽查**：6 处新断言 → §32.110；6/6 吻合（「请输出严格 JSON」系统提示逐字、prompts catalog 恰 5 函数、dark #f5f5f5 与 light #171717 互镜、导演台 H=toggle-visibility 与画布 H=pan 语义分歧、restoreProject 第二次互证、media-conversion declarative runtime 与 sandbox 占位两面）。
- **台账勘定延续**：台账 **689 行** + pre-ledger 13 = **702 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.110 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v127 后队列（depth-action 监控）进行中。

### v127（2026-09-28）：§8/§30/§23/§9/§17 补样（项目三操作体/高亮消息契约/帧格累积体/导出白膜按钮/快捷键四分类/密钥库命名）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v127 轮增量检查）。
- **v127 抽查**：6 处新断言 → §32.109；6/6 吻合（deleteProjects/restoreProject 去重前插/replaceProjects、entryIndex|startMs|endMs|text 逐条 + 返回 JSON 中文指令、Math.floor 帧格累积 + advanceDirectorPlayhead、exportClayVideo :665 + 导出白膜 :738、快捷键 common/navigation/selection/editing 四分类、framefield-local-runtime 密钥库）。
- **台账勘定延续**：台账 **683 行** + pre-ledger 13 = **696 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.109 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v126 后队列（depth-action 监控）进行中。

### v126（2026-09-28）：§12/§10/§22/§17/§23 补样（双导入弹窗落点/音频 error 相/eagle 管理员流+排障矩阵/revokeLocalSession/resolveDirectorKeyframeRecord 双时间写入）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v126 轮增量检查）。
- **v126 抽查**：6 处新断言 → §32.108；6/6 吻合（LibTV/TapNow 同落点文案、音频 error 相 + 快照错误字段、管理员 Base URL 配置流、插件排障矩阵行、revokeLocalSession 吊销入口、resolveDirectorKeyframeRecord raw/snapped 双时间 + 骨骼 snapped 写入）。
- **台账勘定延续**：台账 **677 行** + pre-ledger 13 = **690 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.108 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v125 后队列（depth-action 监控）进行中。

### v125（2026-09-28）：§23/§30/§12/§22/§17 补样（键位输入契约/共享游标池全貌/构造器消费侧/eagle 第四端点/jsonFetch 安全头/challenge 重试）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v125 轮增量检查）。
- **v125 抽查**：6 处新断言 → §32.107；6/6 吻合（DirectorKeyEvent {key,metaKey?,shiftKey?}、游标抢占 + 双退出 + 中文节点标记 + mode text、video→SourceUrl/image→ImagePreviewUrl 消费映射、eagle file 端点「下载并导入站点资源存储」、credentials omit + redirect error + no-store + allowError 尾参、challenge publicKeyJwk 重试）。
- **台账勘定延续**：台账 **671 行** + pre-ledger 13 = **684 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.107 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v124 后队列（depth-action 监控）进行中。

### v124（2026-09-28）：§23/§30/§12/§22/§8/§17 补样（导演台快捷键 7 动作/runner AbortSignal 贯穿/导入 loading 防重入/eagle 三读取端点/任务浮层 slice 5/challenge 过期重建）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v124 轮增量检查）。
- **v124 抽查**：6 处新断言 → §32.106；6/6 吻合（DirectorShortcutAction 7 kind + resolveDirectorShortcut、AbortSignal 参数/退出/透传三贯穿、loading 防重入、eagle library/items/thumbnail 三代理端点、slice(0,5) 直锚、challenge expiresAt 过期重建）。
- **台账勘定延续**：台账 **665 行** + pre-ledger 13 = **678 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.106 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v123 后队列（depth-action 监控）进行中。

### v123（2026-09-28）：§24/§30/§12/§10/§26 补样（trim 实参向量/重分段优先级注释/预览 URL 三构造器/UUID 宽容解析/ResourceKind 四值/记忆面板 UI）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v123 轮增量检查）。
- **v123 抽查**：6 处新断言 → §32.105；6/6 吻合（ffmpeg trim 全实参 libx264/veryfast/crf20、断点优先级「中文标点 > 英文标点 > 空格 > 硬切」逐字、三个 buildLibTV*Url 构造器、parseLibTVProjectUUID 链接/裸 UUID 双收、ResourceKind 四值含分片同枚举、记忆面板 antd+图标操作面）。
- **台账勘定延续**：台账 **659 行** + pre-ledger 13 = **672 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.105 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v122 后队列（depth-action 监控）进行中。

### v122（2026-09-28）：§7/§10/§12/§23/§25 深化补样（hover 销毁链全貌/8MB 分片会话/导入落点说明/播放 fps clamp/按运镜轨迹实现/审计查询面）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v122 轮增量检查）。
- **v122 抽查**：6 处新断言 → §32.104；6/6 吻合（hover 租约销毁七步链 + 让位显式播放、分片会话三段协议每片 8MB、导入落点「保留相对位置放到可视区中心」+ 无效节点逐条披露、fps clamp ≤120、resolveDirectorCameraMoveKeyframes 首尾关键帧对实现 + 按钮接线、审计日志 APICallLog/AnalyticsAPICallLogs 查询面）。
- **台账勘定延续**：台账 **653 行** + pre-ledger 13 = **666 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.104 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v121 后队列（depth-action 监控）进行中。

### v121（2026-09-28）：§21-§25 补样（动画插值应用点/渐变 id 消毒/快捷键中心消费面/messages 端点/审计先查后补/渠道能力归一化）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v121 轮增量检查）。
- **v121 抽查**：6 处新断言 → §32.103；6/6 吻合（interpolateDirectorTransform 于 rendered/resolved 双应用点、gradientId 正则消毒、shortcuts modal 消费 filterCanvasShortcuts、POST messages 多轮续聊、HasAPICallLogForTask 先查后补、normalizeCapabilityString 容错）。路径厘正：model-capabilities.ts 实在 lib/。
- **台账勘定延续**：台账 **647 行** + pre-ledger 13 = **660 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.103 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v120 后队列（depth-action 监控）进行中。

### v120（2026-09-28）：§24/§30/§22/§7/§5/§8 补样（ffmpeg GOP 理由块/SRT round-trip/eagle 后端代理/light accent/updateProject 盖戳/deleteProjects）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v120 轮增量检查）。
- **v120 抽查**：6 处新断言 → §32.102；6/6 吻合（ffmpeg 输出 seek GOP 理由块逐字、parseSrt/serializeSrtEntries 对称、eagle「浏览器不会直接访问 Eagle」后端代理架构 + 写入端点、light accent #171717 三值、updatedAt: now 盖戳、deleteProjects 接口+实现）。
- **台账勘定延续**：台账 **641 行** + pre-ledger 13 = **654 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.102 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v119 后队列（depth-action 监控）进行中。

### v119（2026-09-28）：§5/§8/§10/§17/§25 补样（上传无哈希反验二层/challenge-signature 交换/回收站 localOnly 恢复/元数据宽松抽取/音频六相单例/Seedance 单入口）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v119 轮增量检查）。
- **v119 抽查**：6 处新断言 → §32.101；6/6 吻合（sha256/md5/contentHash 反验二层 0 计数、/runtime/session/exchange 挑战-签名协议、restoreProject localOnly 分支、元数据宽松抽取「继续上传原文件」warn、CanvasAudioPlaybackPhase 六相 + 单例 Controller、Seedance 唯一导出判定）。
- **台账勘定延续**：台账 **635 行** + pre-ledger 13 = **648 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.101 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v118 后队列（depth-action 监控）进行中。

### v118（2026-09-28）：§3/§6/§15-§17/§25 补样（commitTitle 体/focus-visible 双点/isSeedanceConfig/会话刷新重试体/golden 夹具对/mini-map live 桥）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v118 轮增量检查）。
- **v118 抽查**：6 处新断言 → §32.100；6/6 吻合（commitTitle 空回滚 + 变更才回调完整体、focus-visible outline-2 + motion-reduce 双点、isSeedanceConfig、refreshed 单次重试纪律、ai-commands/commands 双 golden + 拖拽 harness 夹具、mini-map 订阅 canvas 预览事件桥）。
- **台账勘定延续**：台账 **629 行** + pre-ledger 13 = **642 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.100 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v117 后队列（depth-action 监控）进行中。

### v117（2026-09-28）：§26/§10/§14/§12 补样（记忆压缩端点/播放按钮双用点/tasks 路由/音频卸载停止/导入 UUID 解析/上传 accept 白名单）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v117 轮增量检查）。
- **v117 抽查**：6 处新断言 → §32.99；6/6 吻合（CompactInterval/CompactStatus 类型面 + compactAgentMemories 30s 端点、VideoPreviewPlayButton :584/589、GET /tasks → TasksWithOptions、卸载即停 stopCanvasAudio、parseLibTVProjectUUID + 中文错误、accept 十类白名单 multiple）。路径厘正：routes.go 实在 backend/internal/handler/。
- **台账勘定延续**：台账 **623 行** + pre-ledger 13 = **636 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.99 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v116 后队列（depth-action 监控）进行中。

### v116（2026-09-28）：§4-§11 混合补样（frame 改道/400ms 队列/video_options 渠道判定/interjections 插话端点/全景内容/回收站按需门）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 be89ee3 未合入（v116 轮增量检查）。
- **v116 抽查**：6 处新断言 → §32.98；6/6 吻合（resolveFrameConnection 折叠改道、store 400ms 队列直接落锚〔BF-23 基础频率〕、provider_video_options 三判定函数、interjections 插话端点 20s + getAgentRun、PanoramaNodeContent、回收站 open 门按需加载）。
- **台账勘定延续**：台账 **617 行** + pre-ledger 13 = **630 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.98 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v115 后队列（depth-action 监控）进行中。

### v115（2026-09-28）：depth-action 第三次强推 be89ee3（140 文件反弹调整）+ 快捷键/选择域补样（Ctrl+F/Alt+L/undo-redo 键族/加减选三分支/双 rAF+双击分发）+ 上游增量检查

- **上游增量**：main 仍 v1.5.9；depth-action 第三次强推 **be89ee3**（同题 merge 重做），tree vs v1.5.9 为 140 文件 +4643/-3650（较 135 反弹，内容仍在调整），未合入。
- **v115 抽查**：6 处新断言 → §32.97；6/6 吻合（Ctrl+F 搜索入口、Alt+L >1 选中门槛 + !event.repeat、mod+Z/shift+Z/Y 键族、Alt 减选 + shift/meta/ctrl toggle 三分支逐字、拖拽与框选双 rAF 节流 + 双击四类分发）。
- **台账勘定延续**：台账 **611 行** + pre-ledger 13 = **624 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.97 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v114 后队列（depth-action 监控）进行中。

### v114（2026-09-28）：depth-action re-merge aca8e16（树差收窄 135 文件）+ 六项补样（Ctrl+S/折叠背板 aria/starterMode/快照哈希契约/grid 四测试名）+ 上游增量检查

- **上游增量**：main 仍 v1.5.9 无新提交、无新 tag；depth-action 强推 **aca8e16**（同题 merge 重做），tree vs v1.5.9 缩至 **135 文件 +4454/-2398**（174→137→135 持续收窄），仍未合入。
- **v114 抽查**：6 处新断言 → §32.96；6/6 吻合（Ctrl+S !event.repeat 保存、折叠背板 aria-label + 封面 lazy 渲染〔row 536 渲染侧补齐〕、starterMode guided/freeform 归一、agent hash/callHash 内容快照哈希契约、grid-viewport 四测试名含 800% 上限）。
- **台账勘定延续**：台账 **605 行** + pre-ledger 13 = **618 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.96 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v113 后队列（depth-action 合入监控）进行中——re-merge 后树差持续收窄。

### v113（2026-09-28）：depth-action 分支 merge 同步 main（19e80fc，合并前置动作）+ 六项补样（plan_updated/SVG 强调层/首张回填/文档内嵌全键/历史双入口）+ 上游增量检查

- **上游增量（重要）**：main 仍 v1.5.9；depth-action 分支新增 **19e80fc「merge: 同步 main v1.5.9 并保留深度捕捉改动」**——把 v1.5.9 合入分支，为合回 main 做准备；仍未反向合入。tree vs v1.5.9 复测：137 files changed, 4533 insertions(+), 3275 deletions(-)（回卷性删除消失，纯增量特征，合入概率显著升高）。锚点纪律不变，合入 main 后触发 §35 增量审计。
- **v113 抽查**：6 处新断言 → §32.95；6/6 吻合（plan_updated 待办事件、SVG 强调层 + Leafer 双层渲染闭合、首张回填 root 执行侧三行、updateProject Pick 全键「文档内嵌一切」闭合、SaveDocumentWithHistory 双入口 + canvasRevisionConflict）。
- **台账勘定延续**：台账 **599 行** + pre-ledger 13 = **612 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.95 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v112 后队列（depth-action 监控）进行中——出现 merge 同步前置动作，合入概率升高。

### v112（2026-09-28）：§11/§6/§2/§5/§10/§16 补样（审批七态中文/空白菜单三键/背景 token/canonical 去重体/音频单例/插件双版本契约）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 da6820e 未合入（v112 轮增量检查）。
- **v112 抽查**：6 处新断言 → §32.94；6/6 吻合（statusLabel 七态中文映射 + 审批失败文案、撤销/重做/粘贴三键 disabled 门、CanvasBackgroundMode + grid token、sameCanvasContent canonicalize every-key 比较体、ensureAudio 惰性单例、**新发现** PLUGIN_API_VERSION v1/v2 双契约并存——editor-shell 直书 v2、media-conversion 等经常量走 v1）。
- **台账勘定延续**：台账 **593 行** + pre-ledger 13 = **606 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.94 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v111 后队列（depth-action 监控）进行中。

### v111（2026-09-28）：§11-§13 与 BF-10/15 补锚（审批七操作/任务取消闭环/remoteContentHash/pagehide 撤销/快速创建过滤链/顶栏 props）+ 上游增量检查

- **上游增量**：main 无新提交；depth-action 分支尖端仍 da6820e 未合入（v111 轮增量检查）。
- **v111 抽查**：6 处新断言 → §32.93；6/6 吻合（审批预览操作枚举恰七值、cancelGenerationTask + task-cancelled 事件闭环、remoteContentHash 托管标记、pagehide 统一 revokeObjectURL、快速创建候选过滤链〔「虚拟节点」措辞未复现如实记〕、顶栏 libtvChrome 双 props 链）。路径厘正：canvas-project-top-bar.tsx 实在 pages/canvas/。
- **里程碑**：台账+pre-ledger 合计突破 **600 处断言抽查全部吻合**。
- **台账勘定延续**：台账 **587 行** + pre-ledger 13 = **600 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.93 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v110 后队列（depth-action 监控）进行中。

### v110（2026-09-28）：depth-action 新提交 da6820e（纯 CI 重跑零内容）+ §6-§10 补样（版本双 tab/anchorRatio 反验/autoArrange 体/524 不确定相位/音频服务+双粘贴）+ 上游增量检查

- **上游增量**：main 仍 v1.5.9；depth-action 新增 da6820e「ci: 重新运行 PR 检查」，树差为空、未合入（v110 轮增量检查）。
- **v110 抽查**：6 处新断言 → §32.92；6/6 吻合（版本历史 cloud/draft 双 tab、anchorRatio 渲染不消费反向验证、autoArrange 选择感知算法体 + 中文兜底、524 归入 submission_uncertain、全局音频播放服务 useSyncExternalStore、pasteCopiedNodes/pasteSystemClipboard 双粘贴路径）。
- **台账勘定延续**：台账 **581 行** + pre-ledger 13 = **594 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.92 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v109 后队列（depth-action 合入监控）进行中——新提交为纯 CI，继续监控。

### v109（2026-09-28）：depth-action 分支跟进（未合入）+ v108 分诊修正（desktopupdate 实为删改非新域）+ depth-capture 预研 + main 补样 + 上游增量检查

- **上游增量**：main 仍 v1.5.9 无新提交；depth-action 分支尖端仍 7fadefd（未合入）。
- **v108 分诊修正（诚实记录）**：desktopupdate 并非「新域」——v1.5.9 已有 27 文件，分支**删除**其中 5 个 proxy_*（代理层移除，属 -7403 删除主体）；确证新域仅 tools/depth-capture（Video Depth Anything Small 深度视频 CLI）。锚点纪律不变。
- **v109 抽查**：6 处新断言 → §32.91；6/6 吻合（分支状态+分诊修正、depth-capture README 逐字、回收站恢复/彻底删除双动作、Agent 七态 union + cancelAgentRun 15s、主题 accent 双主题定义、插件 apiVersion v2 契约）。路径厘正：canvas-theme.ts 实在 web/src/lib/。
- **台账勘定延续**：台账 **575 行** + pre-ledger 13 = **588 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.91 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v108 后队列（depth-action 合入监控）进行中——仍未合入，继续监控。

### v108（2026-09-28）：**首个上游分支强推事件**（codex/depth-action-video-preview 174 文件分诊，锚点不动）+ §6-§13 补样 + 上游增量检查

- **上游增量（重要）**：main v1.5.9 之后仍无新提交；但远端分支 `codex/depth-action-video-preview` 被 **force-update**（a9c421e→7fadefd）——单提交「深度动作捕捉与视频预览稳定性」聚合本地改动，vs v1.5.9 计 **174 文件 +5232/-7403**，**未合入 main**。首分诊：新域 desktopupdate（桌面更新）与 tools/depth-capture；CHANGELOG 回卷删除 v1.5.9 段；包锚点核心文件 infinite-canvas/expression 零 diff、store 仅 1+/2-。处置：锚点维持 `85c9686` 不动，待合入 main/打 tag 后按 §35 流程做增量差异审计。
- **v108 抽查**：6 处新断言 → §32.90；6/6 吻合（分支事件+影响面双记录、createAgentRun :140、importTapNowCanvas :55、Ctrl+1/2/3 三段缩放、hydrateCanvasVideoPreview :10、云 Agent 设置页集成记忆面板）。
- **台账勘定延续**：台账 **569 行** + pre-ledger 13 = **582 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.90 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v107 后队列（§35 分支再监控）✅（捕获强推事件并分诊）；新增队列：depth-action 分支合入 main 后的 §35 增量审计。

### v107（2026-09-28）：§15-§19 上游回归/文档站对照抽样（InactiveVideoPreview 文本断言/标题交互三测试/LibTV 菜单双证/local-only 边界/渠道目录/features.mdx）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v107 轮增量检查）。
- **v107 抽查**：6 处新断言 → §32.89；6/6 吻合（正则提取函数源码做断言的 BF-40 技术实证、标题交互三测试名逐字、LibTV 风格菜单源+测试双证 w-[232px]/grid-cols-4、local-only 边界 existsSync false + session 云端词正则、渠道模型目录 audio 序列断言、features.mdx 实路径 overview/ 子目录 + Agent 能力长清单同向）。
- **台账勘定延续**：台账 **563 行** + pre-ledger 13 = **576 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.89 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v106 后队列（§15-§19 抽样）✅。

### v106（2026-09-28）：REPORT §5 反面教材清单收尾 + §17 剩余细节（双字段警告/sandbox 占位/无去重反验/depth 错误归一/CryptoKey/idb）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v106 轮增量检查）。
- **v106 抽查**：6 处新断言 → §32.88；6/6 吻合（「两者不能互相覆盖……富引用会退化」注释逐字、「插件节点等待隔离运行时」占位逐字、dedupe 反向计数 0、depth requestJson 错误归一 + 会话刷新单次重试、CryptoKey privateKey/registered、openDB(KEY_DATABASE,1) idb 持久化）。至此 REPORT §5 六条反面教材全部有回源锚。
- **台账勘定延续**：台账 **557 行** + pre-ledger 13 = **570 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.88 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v105 后队列（REPORT §4-§5 清单锚定、§17 剩余）✅——REPORT §4 九项与 §5 六项全部有回源锚。

### v105（2026-09-28）：§22 六内置插件能力面深读（eagle 41595/ai-art-critique 560×420/optimizer 五字段输出/media-conversion transforms/runninghub 三 capability/editor-shell 汇总）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v105 轮增量检查）。
- **v105 抽查**：6 处新断言 → §32.87；6/6 吻合（eagle Eagle Local API 默认 41595 + 必填 url、critique 560×420 accepts image 二轮互证、optimizer required 五字段与 strict 面互补、media-conversion「不加载 SD 重绘管线」+ contributes.transforms 第三种贡献类型、runninghub image/video/audio 三贡献项 + 状态门、editor-shell 三轮覆盖汇总）。
- **台账勘定延续**：台账 **551 行** + pre-ledger 13 = **564 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.87 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v104 后队列（§22 内置插件能力面深读）✅。

### v104（2026-09-28）：目录 §6-§7 右键分支与 §13 导入披露复验（多选/角色卡/媒体/空白三分支 + multiResult 取首个 + 文本份数规划）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v104 轮增量检查）。
- **v104 抽查**：6 处新断言 → §32.86；6/6 吻合（多选三动作含 danger、角色卡 MenuHeader/Section 分支头、全景预览+资产分类二级、空白菜单「自适应整理画布/上传到这里/从素材库插入」、multiResult「N 个多结果节点已使用首个结果」披露逐字 + 七计数聚合、textCount 独立份数「对齐上游 v0.16 语义」注释 + planTextGenerationTargets）。路径厘正：canvas-text-generation-executor.ts 实在 pages/canvas/。
- **台账勘定延续**：台账 **545 行** + pre-ledger 13 = **558 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.86 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v103 后队列（目录 §6-§7 剩余、§13 导入细节）✅。

### v103（2026-09-28）：目录 §4-§9 剩余未锚交互项复验（触控轻点/无重连静态复核/folder 折叠语义/菜单自管 Esc/专注模式/缩放步进）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v103 轮增量检查）。
- **v103 抽查**：6 处新断言 → §32.85；6/6 吻合（触控 pointerup 未移动才清空、reconnect 双文件计数 0 的无重连静态复核、getCollapsedParentFrame/isNodeHiddenByCollapsedFrame 折叠隐藏 + folder/frame 分歧门、closeOnEscape window 监听、专注模式 Shift 进入 + Esc 退出三条件、+/-/0/小键盘全族缩放快捷键）。
- **台账勘定延续**：台账 **539 行** + pre-ledger 13 = **552 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.85 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v102 后队列（目录 §4-§9 剩余项）✅。

### v102（2026-09-28）：§5-§13 未抽样交互细节复验（双击空白菜单/拖动集合联动/视频 URL 不返回/回收站 200/耗时徽章/Alt+Shift+F）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v102 轮增量检查）。
- **v102 抽查**：6 处新断言 → §32.84；6/6 吻合（双击空白四处清空 + createOpen 菜单、batchChildIds+frame 子级链式展开 + locked 排除、「original video URL deliberately never returned」注释逐字、回收站 slice(0,200) 软删除、useTaskElapsed 耗时徽章 + shortTaskId、Alt+Shift+F autoArrangeCanvasNodes + 弹层守卫 + !event.repeat）。
- **台账勘定延续**：台账 **533 行** + pre-ledger 13 = **546 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.84 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v101 后队列（§5-§13 未抽样交互细节）✅。

### v101（2026-09-28）：§4-§13 画布本体抽样复验（? 快捷键/世界层/版本恢复备份/孤立对账/50MB 分片/审批呈现）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v101 轮增量检查）。
- **v101 抽查**：6 处新断言 → §32.83；6/6 吻合（`?` nonce 触发快捷键中心、`data-canvas-world-layer` + Leafer 双 host、版本恢复「恢复前会备份当前云端内容」文案逐字 + before_restore 标签、孤立 loading 快照中断注释逐字、50MB 分片阈值「与后端单请求 multipart 上限一致」+ http.MaxBytesError 中文错误、AgentApprovalPresentation server/fallback 双源 + 参数 JSON 重建）。
- **台账勘定延续**：台账 **527 行** + pre-ledger 13 = **540 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.83 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v100 后队列（§4-§13 画布本体抽样）✅。

### v100（2026-09-28）：REPORT §2 架构定性表逐行抽样 + §16-§19 补样（18 节点类型/无箭头连线/sameCanvasContent/测试计数勘误/http-api 36 行/权限 fail-closed）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v100 轮增量检查）。
- **§19 测试计数勘误**：原记「292 文件」→ 实测 `*.test.*` **290** 个、web/test 全部 **294** 文件（4 个 fixtures/helpers）；canvas 前缀 111 精确不变；覆盖表两处已回写勘误口径。
- **v100 抽查**：6 处新断言 → §32.82；6/6 吻合（CanvasNodeType enum 恰 18 项 + PluginCanvasNodeType 开放扩展、marker 计数 0 + 渐变 pathD、sameCanvasContent :603、290/294+111 口径、http-api.mdx 恰 36 行、permission-check 判别联合 + throw fail-closed）。
- **台账勘定延续**：台账 **521 行** + pre-ledger 13 = **534 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：§19 口径勘误回写（ITERATION_LOG 覆盖表两处）、§32.82 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v99 后队列（REPORT §2 逐行抽样、§16-§19 补样）✅——REPORT §2 表 11 行全部有回源锚。

### v99（2026-09-28）：§27-§31 剩余细节抽样复验（ShotInspector 四域/editor-shell 注册/高亮 expired/provider 错误分类/视口错误边界/tool-registry 管线）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v99 轮增量检查）。
- **v99 抽查**：6 处新断言 → §32.81；6/6 吻合（ShotInspector 时长/焦距/光圈/焦点距离逐值吻合 + 双按钮锚、registerPlugin+registerEditorSlot 双通道、expired「文本自证」:25、provider 三类具名错误含 Unwrap 与熔断开路、错误边界「本地失败隔离」+「retryKey 真正重建」注释逐字、tool-registry applicable 过滤管线注释逐字 + defaultOrder 去重）。路径厘正：tool-registry.ts 实在 lib/canvas/tool-registry/ 子目录。
- **台账勘定延续**：台账 **515 行** + pre-ledger 13 = **528 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.81 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v98 后队列（§27-§31 剩余细节）✅。

### v98（2026-09-28）：§21-§24 时间线/几何域抽样复验（12 op 目录/200 层历史/view 常量/默认三轨/碰撞三函数/双向同步）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v98 轮增量检查）。
- **v98 抽查**：6 处新断言 → §32.80；6/6 吻合（AI_EDITING_OP_CATALOG 物理计数恰 12 与「12 个黄金 op」互证〔初查误计 13 系类型声明行干扰〕、HISTORY_LIMIT 200 + ADR-0002 注释逐字、view 常量 96px/s·960·0.02-4·1.25、默认三轨 video-1/audio-1/subtitle-1、placement clipsOverlap/canPlaceAt/findCollidingItems 三函数、buildTimelineFromNodes + 字幕双向同步）。
- **台账勘定延续**：台账 **509 行** + pre-ledger 13 = **522 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.80 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v97 后队列（§21-§24 时间线/几何剩余细节）✅。

### v97（2026-09-28）：§14/§20-§25 抽样复验 + §20 算子计数勘误（36→45）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v97 轮增量检查）。
- **§20 算子全集勘误（本轮核心）**：原记「36 个」，多名单 case 全量展开实测 **45 唯一算子名**——`case "$coalesce", "$default"`、`case "$map", "$filter"`、`case "$eq", "$ne", …, "$and", "$or"` 等共享分支是漏计主因（expression.go:79/:124/:435）；§20 标题已回写勘误。这是继 §35 两处后第 3 处实质勘误。
- **v97 抽查**：6 处新断言 → §32.79；6/6 吻合（算子勘误 + `AI_EDITING_MAX_COMMANDS = 8` 与 12 黄金 op 目录、revision 乐观并发 `current.Revision != *revision` :95、worker 15s tick 与 45s lease 节拍、确定性中文摘要注释逐字、creation epoch 三重守卫 :91）。
- **台账勘定延续**：台账 **503 行** + pre-ledger 13 = **516 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：§20 算子计数勘误回写、§32.79 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v96 后队列（§14/§20-§25 抽样）✅。

### v96（2026-09-28）：§26-§31 跨章抽样复验（skills 缓存退避/官方插件 5 项/runner 并发/onboarding 6 步/浮层双观察器/outbound 超时链）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交；codex 分支树差仍为空（v96 轮增量检查）。
- **v96 抽查**：6 处新断言 → §32.78；6/6 吻合（skills 15s TTL + [300,900,1800] 退避、官方应用清单恰 5 项、runner 并发 3 + 共享游标 + firstError 短路、onboarding VERSION 2 + 恰 6 步、浮动工具栏 ResizeObserver+MutationObserver 双观察器〔目录记载成立且补锚更全〕、outbound requestTimeout 四点链）。行号初排误用 486-491（与 §32.77 碰撞），防重校验即时拦截后改排 **492-497**——v82 新增校验第二次实时生效。
- **台账勘定延续**：台账 **497 行** + pre-ledger 13 = **510 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.78 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v95 后队列（§26-§31 抽样）✅。

### v95（2026-09-28）：REPORT/目录 §10 结论面复核 + codex 分支树差监控 + 定点抽查（fit 上限/巨石定量/50k 夹具）+ 上游增量检查

- **上游增量**：v1.5.9 之后 main 仍无新提交（v95 轮增量检查）；**codex/video-alignment-20260927 分支监控闭环**——远端分支含 2 个 pre-squash 提交（e2fd1d3 的 PR 源），`git diff v1.5.9 分支` 为空，树内容完全一致，零新增内容。
- **v95 抽查**：6 处新断言 → §32.77；6/6 吻合（fit maxScale 1/选区 1.25 三锚、project.tsx 213,805 字节 + 27 处 use-canvas 引用、50k 空间索引夹具 :70、codex 分支树差为空、目录 §10 三支判定全部有锚、REPORT 结论面无陈旧计数 + §3 七项分歧全锚 + 引用卡号全存在）。
- **台账勘定延续**：台账 **491 行** + pre-ledger 13 = **504 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.77 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v94 后队列（REPORT/§10 复核、codex 分支监控）✅；至本轮 REPORT §3 七项输入语义分歧逐项有回源锚。

### v94（2026-09-28）：余量卡面收尾（BF-07/18/30/31/32/33）——卡面二轮回源 45/45 完成 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v94 轮增量检查）。
- **v94 抽查**：6 处新断言 → §32.76；6/6 吻合（hittable:false ×2 + [0.85,1.25] rebase 阈值 + connectionSceneSignature **恰 20 字段**物理计数、BF-18 paint-order 注释与 row 427 逐字同源、versionOfNodeId + prepareInPlaceMediaVersion 全仓无调用点、BF-31 与 row 361 一致 + composerContent 独立字段、batch-table 1280×560 + 并发 10 + batchRowId、pendingRemoteUpload + X-Idempotency-Key 三处）。路径厘正一处：canvas-leafer-graphics-layer.tsx 实在 components/canvas/。
- **里程碑**：PATTERN_CARDS 45 张卡**全部完成二轮回源**（累计 39 + 本轮 6；BF-18/31 经「历史行 + 卡面」双验证）。
- **台账勘定延续**：台账 **485 行** + pre-ledger 13 = **498 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.76 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v93 队列（余量卡面收尾）✅。

### v93（2026-09-28）：PATTERN_CARDS 最后一批卡面抽样回源（BF-22/24/26/27/29/36）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v93 轮增量检查）。
- **v93 抽查**：6 处新断言 → §32.75；6/6 吻合（快照撤销容量 10 + 结构逐字、generation stamp 专用 commit 注释逐字、8 原语 union 恰 8 项逐字 + verifyCanvasOperations + resourceReady 物化门、「历史 taskId 不是锁」注释逐字、batchRootId 退休/解除四锚、192KB 预算 + 384KB/96k 硬失败文案逐字）。路径厘正：canvas-image-generation-executor.ts 实际在 pages/canvas/（卡面引文件名省目录，非断言错误）。
- **台账勘定延续**：台账 **479 行** + pre-ledger 13 = **492 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.75 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v92 队列（最后一批卡面）✅；卡面二轮回源累计 **39 张**（新增 BF-22/24/26/27/29/36）；余 BF-07（REJECT 域）/BF-18/31（历史行 427/361 覆盖）/BF-30/32/33 共 6 张未做二轮回源，按需再议。

### v92（2026-09-28）：PATTERN_CARDS 剩余卡面抽样回源·四批（BF-12/13/16/21/25/35）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v92 轮增量检查）。
- **v92 抽查**：6 处新断言 → §32.74；6/6 吻合（默认 `box-select` + H/V 切换三元、railSize 80 + LibTV 80px 注释 + anchorRatio 0.5 回退、elementFromPoint 两处、EntityChange/beforeOrder/180ms debounce、Web Locks fail-closed 抛错逐字 + promise tail 转 void「不毒化保存队列」注释逐字、patch 冲突抛错逐字 + terminal 三态守卫「Never turn its terminal result back into a pending task」+ `{before: current, after: current}` 无操作保护）。
- **台账勘定延续**：台账 **473 行** + pre-ledger 13 = **486 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.74 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v91 队列（剩余卡面·四批）✅；卡面二轮回源累计 **33 张**（新增 BF-12/13/16/21/25/35；BF-18/31 经历史行覆盖）。

### v91（2026-09-28）：PATTERN_CARDS 剩余卡面抽样回源·三批（BF-11/15/17/20/23/28）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v91 轮增量检查）。
- **v91 抽查**：6 处新断言 → §32.73；6/6 吻合（指针意图路由七支逐字、拖线空白 quick 分支 + pin ≤5px、tilt ±10deg latch、媒体 fit 420×236/720×520 + freeResize/locked 门 + 占位比例串、storageRevision/tombstones 字段 + generationEffectKeys 并集 `[...new Set([...durable,...local])]` 逐字、防重复计费四层全锚〔互斥 locks Map + 指纹 canonicalize + 确认文案逐字 + clientOperationId〕）。
- **台账勘定延续**：台账 **467 行** + pre-ledger 13 = **480 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.73 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v90 队列（剩余卡面抽样·三批）✅；卡面二轮回源累计 **27 张**（新增 BF-11/15/17/20/23/28）。

### v90（2026-09-28）：PATTERN_CARDS 剩余卡面抽样回源·二批（BF-01/02/05/08/19/34）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v90 轮增量检查）。
- **v90 抽查**：6 处新断言 → §32.72；6/6 吻合（三频率 120ms/32ms/64ms 全落锚〔含 caller :35 行 notify 门与 render-sync :3 常量〕、CSS 四 live 变量 + globals.css 交互期降负带、auto 阈值 80/32、小地图 240×160/≤24 缩略图/preview-commit 双回调、标题头 0.35 隐藏 + 逆倍率同帧抵消、ffmpeg 同源发布 + ISO-BMFF 手工容器结构校验注释逐字 + rVFC 抽帧）。方法注记：32ms/64ms 初查未在卡面所引次级文件现形，追至 caller 后回核确认卡面 file:line 区间均覆盖实际常量，无需勘误。
- **台账勘定延续**：台账 **461 行** + pre-ledger 13 = **474 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.72 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v89 队列（剩余卡面抽样）✅；卡面二轮回源累计 **21 张**（BF-01/02/03/04/05/06/08/09/10/14/19/34/37-45）。

### v89（2026-09-28）：PATTERN_CARDS BF-01..36 卡面抽样回源（BF-03/04/06/09/10/14）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v89 轮增量检查）。
- **v89 抽查**：6 处新断言 → §32.71；6/6 吻合（空间索引 cell 1024/跨格 256 兜底、虚拟化 720/5000 + 双边距 128/192·384/640 + 分档 280/420/720、拖拽期 `sameNodeSemanticData` 逐位语义短路、hover 租约 350ms/3s/8s deadline + removeAttribute 销毁、Blob LRU 2GB/64MB/500 条/并发 16/quota×0.2、吸附 56px + isNearNode 建模 + :58 注释比卡面更细〔LibTV 80px 世界坐标 ≈ 屏幕 110px〕）。
- **台账勘定延续**：台账 **455 行** + pre-ledger 13 = **468 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.71 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v88 队列（BF-01..36 抽样）✅；卡面已二轮回源累计 15 张（BF-03/04/06/09/10/11 部分/14/37/38/39/40/41/42/43/44/45）。

### v88（2026-09-28）：BF-42 32MB 锚补验（depth-runtime）+ BF-37/38/43 卡面回源复验 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v88 轮增量检查）。
- **v88 抽查**：6 处新断言 → §32.70；6/6 吻合（BF-42 卡面 32MB 上限锚定 depth-runtime.ts:6 + 12MB 输入图「深度转换图片不能超过 12MB」+ boundedText 双检；BF-37 opt-in 注释逐字 :68 + libtvChrome 只读保存跳转 project.tsx:675/2978；BF-38 五统计计数器 :48-52 + 两段式双错误文案 + importSource :43；TapNowImportResult 同构 tapnow.ts:38 + 十个 createLibTv*Fixture 注入面；BF-43 `frozen || resolved` :557 + readObject3DTransform 读回 :638-640 + 终态映射注释逐字 :89-91/:18/:49）。
- **台账勘定延续**：台账 **449 行** + pre-ledger 13 = **462 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.70 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v87 队列 1（BF-42 32MB 补验）✅、队列 2（BF-37/38/43 卡面抽样）✅。

### v87（2026-09-28）：§35 差异审计重跑（端点恒等 + 两处误记勘误回写）+ PATTERN_CARDS 卡锚复验（BF-40/41/42）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v87 轮增量检查）。
- **§35 差异审计机械重跑（本轮核心）**：端点全哈希恒等（`v1.5.9^{commit}`==`e2fd1d3f78fa…`、`v1.5.7^{commit}`==`85c9686c87a4…`）证明 diff 确定性、上游无漂移；但抓出 §35 两处**审计时点误记**并已回写（带 v87 勘误标记）：①总量原记 42 文件 +1590/-477，实测 **62 文件 +2057/-849**（v1.5.8 段 23 文件 +234/-177 后端 0；v1.5.9 段 41 文件 +1824/-673）；②「backend/internal 无 diff/纯前端发布」不成立，实测 **16 文件 +1106/-165**（model_capability/provider×5/video_reference_constraints 新增/resource/generation 三件/repository + 6 测试），性质 = 素材限制与错误提示的服务端对应实现。包断言锚定 `85c9686` 不受影响；§35.2 逐文件行数经核为「插入+删除总数」口径，与 numstat 一致。
- **卡锚复验**：BF-40（readFileSync ×8 + pretest/test:canvas 分级门禁）、BF-41（六副作用 import + manifest.go:75-77 注释逐字 + isPluginEffectivelyEnabled 门禁 :327）、BF-42（精确 loopback 校验逐字 + MAX_RESPONSE_BYTES=64KB）——3/3 吻合；BF-42 卡面 32MB 上限本轮未复核，入下轮队列。
- **v87 抽查**：6 处新断言（§35 勘误 ×3 + 卡锚 ×3）→ §32.69；6/6 吻合。
- **台账勘定延续**：台账 **443 行** + pre-ledger 13 = **456 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：§35 头注与 §35.2 勘误回写、§32.69 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v86 后队列（§35 文件清单重跑、PATTERN_CARDS 剩余卡面抽样）✅。

### v86（2026-09-28）：§33-34 编排层抽样复验（镜像注释/快捷键 preventDefault/双 playhead/姿势 21+20/运镜表 10 项/录制健壮性）+ 结论面计数同步核验 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v86 轮增量检查）。
- **结论面计数同步核验**：REPORT.md 与 README.md 均不携带累计抽查总数（仅 REPORT.md:65 / README.md:20 的 v1 历史表述「5 处承重断言抽查/关键断言抽查」），累计口径 444→450 仅存于 §32 勘定行与 ITERATION_LOG 队列——无陈旧漂移，无需改写结论面。
- **v86 抽查**：6 处新断言（§33.1/§33.2×2/§33.4×2/§34.3）→ §32.68；6/6 吻合（mirrorDraft「这些都不是新的用户改动」注释逐字 :126、runShortcut 返回值语义「执行了才 preventDefault」:519-525、双 playhead 纪律注释逐字 + snappedPlayhead :200-203、DirectorPose 恰 21 值 + poseOptions 恰 20 钮 + 景别 6/运镜 10、cameraMoveTransform offsets 恰 10 键全量数值、录制首错即停 + `Math.max(0.25, duration*0.5)` 时长探针）。
- **台账勘定延续**：台账 **437 行** + pre-ledger 13 = **450 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.68 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v85 后队列（REPORT/README 计数同步核验、§33-34 抽样）✅。

### v85（2026-09-28）：交互目录剩余章节抽样复验（§2 文案 bug/§5 删除优先级+重命名回滚/§6 菜单避让/§8 自适应轮询/§9 保护条件）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v85 轮增量检查）。
- **v85 抽查**：6 处新断言（交互目录 §2/§5×2/§6/§8/§9）→ §32.67；6/6 吻合（快捷键文案 bug「切换移动工具」vs `box-select-tool` 逐字、删除先连线后节点 + Backspace 拦截注释逐字、重命名 Enter/Escape/空值回滚 `commitTitle` :288-292、菜单避让 `.canvas-agent-panel` + clamp 12px、任务浮层 `2_000:10_000` 自适应轮询 + 三窗口事件 + cloud_agent 过滤〔比目录记载更细〕、按键保护条件三条）。
- **台账勘定延续**：台账 **431 行** + pre-ledger 13 = **444 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.67 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v84 后队列（交互目录剩余章节复验）✅；INTERACTION_CATALOG 十章节中 §1/§2/§3/§4/§5/§6/§7/§8/§9 均已有回源复验样本。

### v84（2026-09-28）：交互目录抽样复验（pinch 中点锚/四角手柄+freeResize/连线 16px 命中/@mention 报错）+ 卡↔矩阵交叉核对（BF-39↔37、BF-44↔42、BF-45↔43）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v84 轮增量检查）。
- **交互目录抽样复验**：INTERACTION_CATALOG 抽 4 项回源，4/4 吻合——§1 双指 pinch 中点锚 `(first.x+second.x)/2`（infinite-canvas.tsx:268-269）、§3 四角手柄 14px 外偏 + `freeResize` 锁比例让位（canvas-node.tsx:575-580,699-702 + types/canvas.ts:270 + canvas-image-toolbar-tools.tsx:71）、§4 连线 16px 透明命中（canvas-connections.tsx:77-78）、§7 `assertResolvableGenerationMentions` 不可解析抛错 + composer 分支（canvas-node-generation.ts:88-97）。
- **卡↔矩阵交叉核对**：3 对全部一致——BF-39↔行 37（卡面六项子证据 ⊃ 矩阵标题三项，RESEARCH_ONLY 与卡面「仅作对照证据」门槛一致）；BF-44↔行 42（逐项一致，源码锚 director-save.ts:130/136/98）；BF-45↔行 43（诊断码恰 11 项、复现矩阵物理计数恰 15 条，与双方表述吻合）。
- **v84 抽查**：6 处新断言（交互 4 + 交叉 2）→ §32.66；6/6 吻合。
- **台账勘定延续**：台账 **425 行** + pre-ledger 13 = **438 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.66 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v83 后队列（INTERACTION_CATALOG 抽样复验、PATTERN_CARDS↔矩阵交叉核对）✅。

### v83（2026-09-28）：补录复验清算（误报澄清：零丢失）+ 定点抽查（技能预算分摊/截断后缀/linked 白名单/引导非阻塞播报/SSE content-type 守卫/八插槽全枚举）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v83 轮增量检查）。
- **v82 遗留项清算（误报澄清）**：逐项回源 + 台账比对确认 v79/v80（第四十八、四十九轮）条目所述断言**全部已有落档行**：collectObject3DResources→390、HasAPICallLogForTask→344、snap 距离排序+同毫秒→346、preview 门控注释→347、directorCaptureUsable→349、failedLoads 角标重试→351、shouldUseTaskTextEvents→352、SRT 序号归一→253/353、flushSave 实现→387、导出常量 62min/3s→269——v82 轮「疑丢失」判断有误，零补录需要；清算注记已写入 §32.65 节首。
- **v83 抽查**：6 处新断言（§26/§27/§25.3/§16）→ §32.65；6/6 吻合（技能预算 `max(1, floor(32k/选中数))` 均摊 + SKILL.md 二进制抛错、截断后缀逐字且预留后缀长度、linked 文本八扩展白名单 + scripts//assets/ 前缀与四 binary kind 排除、引导 role="region" 非 dialog + aria-live 播报 + 进度文本承担、SSE content-type 守卫 + Accept/Last-Event-ID 双头、编辑器壳八插槽全枚举 priority 0）。
- **台账勘定延续**：台账 **419 行** + pre-ledger 13 = **432 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.65 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v82 队列 1（补录复验）✅（清算为零丢失）。

### v82（2026-09-28）：定点抽查（高亮解析空回退/编辑器壳声明面/SSE 拨号守卫/终态适配器注入/引导并发锁/技能预算与提及）+ 台账编号修复 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（v82 轮增量检查）。
- **台账编号修复（本轮先行的结构勘误）**：SOURCE_ANALYSIS 末两节原误用 §32.60/§32.61 编号（与 v77/v78 两节撞号），重编号为 **§32.62/§32.63** 并补 v79/v80 轮标签；两节台账行号原误从 262 重新起算（与既有 262-273 行碰撞），物理清点后接续改排 **396-401 / 402-407**；v80（批量批准节）勘定随之修正为 **台账 407 行 + pre-ledger 13 = 420 处**。自检脚本新增第 6 项校验（编号标题与台账行号防重复），以当前缺陷为负向测试样例验证拦截有效（修复前 14 项报错 → 修复后清零）。
- **v82 抽查**：6 处新断言（§30/§16/§25.3/§25.2/§27/§26）→ §32.64；6/6 吻合（高亮解析非 object/非法项双空回退 + 五字段守卫、编辑器壳 `surfaces:["fullscreen"]` + permissions 三值 + 八插槽描述、SSE 120s idle watchdog + retry-after>300s 终止 + 4xx 除 408/429 不重试 + reconnecting 态、终态适配器三函数注入、导演台引导 gate 同刻捕获 + 换代整体替换 + reset 失败补读、技能四 profile 统一 4/32k/3 预算 + `@[skill:id]` 与边界符自然提及 + required 正则优先）。
- **台账勘定延续**：台账 **413 行** + pre-ledger 13 = **426 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：§32.62/§32.63 重编号、§32.64 追加；卡/矩阵计数不变（45/44）。
- **历史条目指针勘误**：v78（第四十七轮）→ §32.61（原误写 §32.55）、v81（第五十轮）→ §32.55（原误写 §32.58）、v80（批量批准轮）→ §32.63（原误写 §32.61）——均按内容逐行比对后纠正。
- **遗留勘误入队**：v79（第四十八轮）与 v80（第四十九轮）条目所述断言（collectObject3DResources 逐 mesh、HasAPICallLogForTask、directorCaptureUsable、shouldUseTaskTextEvents、failedLoads 角标重试、SRT 序号 idx+1 归一、snap 同毫秒全量、preview 门控注释）在台账中仅部分能对应既有行（如 383/387/269），无独立落档行（疑上会话编辑冲突丢失）→ 下一轮逐条回源复验后补录。（v83 轮清算：该判断为**误报**——全部已有落档行 390/344/346/347/349/351/352/253+353，见 §32.65 节首注记。）

### v80（2026-09-28）：新一轮定点抽查（批量批准 1-20 上限/指纹复验/undo 同守卫/环境强度/递归 back/存储注入）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（新一轮检查）。
- **新一轮抽查**：6 处新断言（§25.2/§28.x/§23.x/§16/§30）→ §32.63（v82 轮勘误：原误写 §32.61，该号属 v78 节）；6/6 吻合（批量批准 1-20 项上限、批准前置指纹复验、undo/redo 与 dispatch 同 inPreview 守卫、环境强度 0.7×0.35、SRT 递归切分 back 条目、插件宿主 pluginStorageFor 注入）。
- **台账勘定延续**：台账 407 行 + pre-ledger 13 = **420 处断言抽查全部吻合**（v82 轮勘误：原误记 401/414，系撞号期行号重排前口径）。
- **包结构变化**：仅 §32.61 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：上一轮队列（backend task 域/时间线接线/viewport 余项定点抽查）✅。

### v81（2026-09-28）：第五十轮定点抽查（worker draining/saveChain 尾/双主题/strict 工具/五态枚举/技能文件端点）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第五十轮检查）。
- **第五十轮抽查**：6 处新断言（§2.4/§9.3/§16/§22.2/§25.1/§26.3/§28.x）→ §32.55（v82 轮勘误：原误写 §32.58，该号属 v75 节）；6/6 吻合（worker draining 双检 :50,64、saveChain 尾段失败保留 isDirty、canvasThemes 仅 light/dark 双键〔皮肤在后端〕、优化器 strict 工具 additionalProperties:false、不可重试默认 true 兜底、技能文件端点 GET /skills/:id/files）。
- **台账勘定延续**：台账 367 行 + pre-ledger 13 = **380 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.58 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v80 队列 1（backend task/generation 域定点抽查）✅、队列 2（时间线 editor store 接线剩余）✅。

### v80（2026-09-28）：第四十九轮定点抽查（directorCaptureUsable/flushSave 实现/failed notice retryLoad/shouldUseTaskTextEvents/SRT 序号归一）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十九轮检查）。
- **第四十九轮抽查**：5 处新断言（§2.x/§23.2/§25.3/§28.x/§30）→ §32.57；5/5 吻合（directorCaptureUsable registered && !contextLost、flushSave 清定时器 + isDirty 门控、failedLoads 角标重试循环 :191、shouldUseTaskTextEvents onTextDelta/useTextEvents、SRT 序号非法 idx+1 归一）。
- **台账勘定延续**：台账 361 行 + pre-ledger 13 = **374 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.57 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v79 队列 1（时间线 subtitle-highlight/导演台 viewport 剩余定点抽查）✅。

### v79（2026-09-28）：第四十八轮定点抽查（collectObject3D/审计补行/导出常量/snap 同毫秒/preview 门控/finalizeReplay 定义）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十八轮检查）。
- **第四十八轮抽查**：6 处新断言（§23.2/§25.3/§28.6/§30）→ §32.56；6/6 吻合（collectObject3DResources 逐 mesh 收集 + dispose 守卫、HasAPICallLogForTask 先查、导出常量 62min/3s、snap 距离排序 + 同毫秒全量、preview 门控语义注释逐字、finalizeReplay 定义定位）。
- **台账勘定延续**：台账 355 行 + pre-ledger 13 = **368 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.56 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v79 队列（viewport 剩余渲染细节/终态协调定点抽查）✅。

### v78（2026-09-28）：第四十七轮定点抽查（disposeObject3D/卸载 flush/路由回退三支/恢复序列/SRT 多行/插槽权限三值）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十七轮检查）。
- **第四十七轮抽查**：6 处新断言（§23.2/§28.x/§25.2/§30/§16）→ §32.61（v82 轮勘误：原误写 §32.55，该号属 v81 节）；6/6 吻合（disposeDirectorObject3D 三类资源 Set 去重 + owner 显式调用注释、卸载 flushSave 双注释〔错误证据不假装已保存〕、路由回退三支路 + RouteID 对齐、恢复序列三步、SRT 多行文本保留、EditorPluginPermission 三值 + Omit 技巧）。
- **台账勘定延续**：台账 405 行 + pre-ledger 13 = **418 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.55 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v77 队列（viewport 渲染细节/任务域定点抽查）✅。

### v77（2026-09-28）：第四十六轮定点抽查（viewport 渲染细节/editor 接线/Agent SSE 路由勘定）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十六轮检查）。
- **第四十六轮抽查**：6 处新断言（§23.2/§25.3/§26.x/§28.x/§2.3）→ §32.54；6/6 吻合（useEditorSlots 8 槽消费、Agent SSE 路由在 cloud agent handler 注册的域说明、normalizeModel 二轮确认、flushSave 实现、草稿恢复弹窗文案逐字、wheel preventDefault）。
- **台账勘定延续**：台账 386 行 + pre-ledger 13 = **399 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.54 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v76 队列（viewport 剩余渲染细节/时间线 editor 接线定点抽查）✅。

### v76（2026-09-28）：第四十五轮定点抽查（手势三函数/ApproveProposalVersion/末段时长/exLocalMp4 错误态/text_to_video/finalizeReplay）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第七十六轮检查）。
- **第四十五轮抽查**：6 处新断言（§12.2/§25.2/§28.1/§28.6/§30）→ §32.53；6/6 吻合（手势三函数守卫与入历史、ApprovedProposalVersion 单调 + 同 hash 幂等、递归切分 front/back、exportLocalMp4 错误态透出、text_to_video 节点构造全字段、finalizeReplay 通道字段与调用）。
- **台账勘定延续**：台账 367 行 + pre-ledger 13 = **380 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.53 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v75 队列（backend task/generation 域余下定点抽查）✅。

### v75（2026-09-28）：第四十八轮定点抽查（记忆端点/复现夹具/TaskID 复用/firstValidDate/背景默认/重映射索引）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十八轮检查）。
- **第四十八轮抽查**：6 处新断言（§2.4/§4.1/§23.2/§25.2/§26.2/§30）→ §32.56；6/6 吻合（记忆六端点 15s/30s 分级超时、复现夹具字面量确定性、TaskID 复用 return nil 分支、firstValidDate 链、背景默认 dots、重映射 indexOf/dropped）。
- **台账勘定延续**：台账 361 行 + pre-ledger 13 = **374 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.56 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v74 队列（剩余未抽样断言定点抽查）✅。

### v74（2026-09-28）：第四十六轮定点抽查（agent-memories/useEditorSlots/租约支路/素材 URL/批切片/wheel shift）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十六轮检查）。
- **第四十六轮抽查**：6 处新断言（§2.3/§4.1/§22.6/§25.1/§26.2/§30）→ §32.54；6/6 吻合（agent-memories 144 行全貌含压缩档位、useEditorSlots 消费方 editor.tsx:231、RenewTaskLease 45s 失败支 leaseLost、resolveMediaUrl 三处素材 URL、批切片默认 30、shift 横滚降级）。
- **台账勘定延续**：台账 354 行 + pre-ledger 13 = **367 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.54 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v73 队列（agent-memories 深读/useEditorSlots 消费方）✅。

### v73（2026-09-28）：第四十五轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第七十三轮检查）。
- **第四十五轮抽查**：6 处新断言（§4.1/§9.6/§25.1/§25.3/§30/§34）→ §32.53；6/6 吻合（渠道并发上限平台桥接、素材输入边顺序唯一源注释逐字、高亮 LLM 形状守卫、reconcileImageBatchRoot 定位、错误文本截断 500、素材挂载负载形状）。
- **台账勘定延续**：台账 348 行 + pre-ledger 13 = **361 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.53 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v72 队列（subtitle-highlight 剩余/生成域定点抽查）✅。

### v72（2026-09-28）：第四十四轮定点抽查（运镜偏移表/merge 进度/重置绑定/上传网格/local 态机）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第七十二轮检查——上游增量检查每轮均执行，本轮为第四十四次记录）。
- **第四十四轮抽查**：5 处新断言（§12.1/§10.3/§9.2/§10.1/§28.6）→ §32.52；5/5 吻合（cameraMoveTransform 十运镜偏移表全表、merge 三段进度 + concat.txt 清单、resetGenerationTaskMetadata 清旧绑定注释、批量上传网格居中坐标、local 导出 done/error 态机）。
- **台账勘定延续**：台账 342 行 + pre-ledger 13 = **355 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.52 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v71 队列（导演台 viewport 剩余/时间线 editor 接线定点抽查）✅。

### v71（2026-09-28）：第四十三轮定点抽查（provider 域/SRT 域/插槽接线/锁定期勘定）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十三轮检查）。
- **第四十三轮抽查**：5 处新断言（§25.2/§30/§22.6/§16/§35）→ §32.51；5/5 吻合（AttemptNumber 防重复创建门禁含中文错误逐字、重分段 CJK/拉丁标点集、emitChange 接线、渠道目录 capability 可选过滤、v1.5.7 锁定期无 light 模式勘定〔与 §35 一致〕）。
- **台账勘定延续**：台账 **337 行** + pre-ledger 13 = **350 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.51 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v70 队列 1（provider 域余下/SRT 域定点抽查）✅。

### v70（2026-09-28）：第四十二轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十二轮检查）。
- **第四十二轮抽查**：6 处新断言（§23.2/§25.1/§23.4/§30）→ §32.50；6/6 吻合（失败登记表 error-only 语义、渠道并发信号量、safeReproText 脱敏、runner 双守卫、重试回调接线、派发 CAS RowsAffected 检查）。
- **台账勘定延续**：台账 319 行 + pre-ledger 13 = **334 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.50 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v69 队列 1（剩余未逐行域定点抽查）✅。

### v69（2026-09-28）：第四十一轮定点抽查（capture 状态机/angle-scene/终态协调/runner 游标池/corner notice/scope 守卫）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十一轮检查）。
- **第四十一轮抽查**：6 处新断言（§23.2/§10.2/§25.2/§27.1/§30）→ §32.49；6/6 吻合（capture 四事件归一状态机、angle-scene 双模式 + 半径常量、终态协调全链、runner 共享游标池 + firstError 短路、失败模型角标通知、requireScope 归一守卫）。
- **台账勘定延续**：台账 309 行 + pre-ledger 13 = **322 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.49 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v68 队列（viewport 未逐行段/终态协调定点抽查）✅。

### v68（2026-09-28）：第四十轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第四十轮检查）。
- **第四十轮抽查**：6 处新断言（§23.2/§25.3/§4.3/§25.1/§23.4/§9.2）→ §32.48；6/6 吻合（disposeDirectorMaterials textures→materials 释放、EstimatedCostMicros 无写入点二轮确认、双击分发批次根优先、租约续期 15s ticker + 5s 超时、保存状态投影 Omit scene、结果几何居中 locked 跳过二轮确认）。
- **台账勘定延续**：台账 303 行 + pre-ledger 13 = **316 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.48 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v67 队列 1（backend provider/worker 域余下定点抽查）✅。

### v67（2026-09-28）：第三十九轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十九轮检查）。
- **第三十九轮抽查**：6 处新断言（§8.2/§10.4/§25.3/§8.3/§4.1）→ §32.45；6/6 吻合（opLabel 余段、agent-debug-export 递归脱敏深读〔位置勘定 lib/canvas〕、requestKind 四分类、FNV-1a 快照哈希、SSE watchdog 逐事件重置、时间戳多级兜底链）。
- **台账勘定延续**：台账 298 行 + pre-ledger 13 = **316 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.45 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v66 队列（viewport/provider 余下定点抽查）✅。

### v66（2026-09-28）：第三十七轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十七轮检查）。
- **第三十七轮抽查**：5 处新断言（§23.x/§28.1/§29.3/§30）→ §32.46；5/5 吻合（手势三分 inPreview 门控、出站禁用头清单 17 项 + 双前缀、GLTF 加载所有权 adopt/disposeSource 注释逐字、高亮 runner 进度字段、草稿键 scope 化）。
- **台账勘定延续**：台账 260 行 + pre-ledger 13 = **273 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.46 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v65 队列 1（新一轮定点抽查）✅。

### v65（2026-09-28）：第三十六轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十六轮检查）。
- **第三十六轮抽查**：6 处新断言（§25.3/§26.3/§28.2/§30）→ §32.45；6/6 吻合（waitForGenerationTask 文本事件/轮询双路 + 连续失败计数、characterAssetId 匹配引用集合、插槽注册 HMR 幂等 + 返回卸载闭包、日志载荷 128KB 上限、SRT 序号非法归一、skillRuntime 单例 + 适配器注册表现状）。
- **台账勘定延续**：台账 249 行 + pre-ledger 13 = **262 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.45 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v64 队列 1（上游增量检查）✅、队列 2（第三十六轮抽查）✅。

### v67（2026-09-28）：第三十八轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十八轮检查）。
- **第三十八轮抽查**：6 处新断言（§23.2/§25.3/§26.3/§28.1/§12.2）→ §32.44；6/6 吻合（saveChain 串行保存、safeProviderLogError 状态码化、rig ready ≥8 阈值、交付适配器注册表现状、空 rows 中文错误逐字、readCameraTransform 空安全）。
- **台账勘定延续**：台账 249 行 + pre-ledger 13 = **262 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.44 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v66 队列（viewport/provider 余下定点抽查）✅。

### v66（2026-09-28）：第三十七轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十七轮检查）。
- **第三十七轮抽查**：6 处新断言（§9.1/§11.1/§12.1/§12.2/§25.1/§28.2）→ §32.43；6/6 吻合（运镜首尾双 upsert、取消不确定三态文案、分镜模板元数据展开、标签列 sticky、localSeq 字段、NODE_STATUS_ERROR 具名常量）。
- **台账勘定延续**：台账 298 行 + pre-ledger 13 = **311 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.43 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v65 队列 1（上游增量检查）✅、队列 2（第三十七轮抽查）✅。

### v65（2026-09-28）：第三十六轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十六轮检查）。
- **第三十六轮抽查**：6 处新断言（§4.3/§9.3/§9.4/§13.1/§16/§23.3）→ §32.42；6/6 吻合（标题空值回滚、workflows 三能力中文标签、poseQuaternion 欧拉转换、费用确认弹窗、不可重试类别枚举、删除后兄弟画布导航 + 草稿清理）。
- **台账勘定延续**：台账 285 行 + pre-ledger 13 = **298 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.42 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v64 队列 1（新一轮定点抽查）✅。

### v64（2026-09-28）：第三十五轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十五轮检查）。
- **第三十五轮抽查**：6 处新断言（§2.4/§4.x/§10.x/§11.1/§23.2/§25.2）→ §32.41；6/6 吻合（protectTaskSecrets 递归加密、agent-debug-export 位置勘定〔lib/canvas 而非 services/diagnostics〕、命名皮肤在 Go 后端 appearance_skins.go、Agent 记忆前端双文件、批量表行构建函数、共享 clay 材质销毁注释）。
- **台账勘定延续**：台账 279 行 + pre-ledger 13 = **292 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.41 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v63 队列 1（新一轮定点抽查）✅。

### v63（2026-09-28）：第三十四轮定点抽查（editor 接线/后端任务路由）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十四轮检查）。
- **第三十四轮抽查**：6 处新断言（§25.x/§27.1/§28.1/§28.6）→ §32.40；6/6 吻合（saveTimeline scoped 键、text-deltas 双路由〔前端 text-events 命名差异已记录〕、nextRouteAttemptAfterFailure、exportLocalMp4 wasm 兜底、引导 tryEnter/release、requiresLibass 双落点）。
- **台账勘定延续**：台账 273 行 + pre-ledger 13 = **286 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.40 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v62 队列 1（backend 任务路由定点抽查）✅。

### v62（2026-09-28）：第三十三轮定点抽查（导出链/CreationRun/视频工具）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十三轮检查）。
- **第三十三轮抽查**：6 处新断言（§10.3/§25.2/§28.6/§9.4/§2.x）→ §32.39；6/6 吻合（collectRenderSources nodeId 去重、renderRemote 内联预览+下载、渲染计划前 8 步展示、ProposalVersion 单调锁、merge concat 回退与 finally 清理、activeTaskLimit 来源）。
- **台账勘定延续**：台账 267 行 + pre-ledger 13 = **280 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.39 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v61 队列 1（导出链/CreationRun/视频工具定点抽查）✅。

### v61（2026-09-28）：第三十二轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十二轮检查）。
- **第三十二轮抽查**：6 处新断言（§29.3/§23.x/§25.2/§2.1/§4.1）→ §32.38；6/6 域确认（outbound 头 32 个/16KB 限额、姿势标签 21 项映射、SkeletonHelper 卸载清理、ItemKey 去重冲突、双 ignore 选择器清单、素材下载回退位置勘定）。
- **台账勘定延续**：台账 261 行 + pre-ledger 13 = **274 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.38 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v60 队列 1（backend provider 余下）✅、队列 2（第三十二轮抽查）✅。

### v60（2026-09-28）：第三十一轮定点抽查（worker/CloudAgent/导出/迁移/角度）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十一轮检查）。
- **第三十一轮抽查**：6 处新断言（§25.1/§25.2/§28.6/§3.x/§10.2/§4.5）→ §32.37；6/6 吻合（worker 2s tick 两处、CloudAgent 幂等主键 ag+sha256[:16]、导出轮询 62min/3s、normalizeLocalCanvasProject 剥离 hosted 标记、角度节点走后端、LANE_ORDER 二轮确认）。
- **台账勘定延续**：台账 255 行 + pre-ledger 13 = **268 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.37 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v59+队列 1（上游增量检查）✅、队列 2（第三十一轮抽查）✅。

### v59（2026-09-28）：第三十轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十轮检查）。
- **第三十轮抽查**：6 处新断言（§4.1/§9.4/§12.2/§25.3/§30 + 未读文件 chapter-asset-breakdown.ts）→ §32.36；6/6 吻合（readiness 阻塞原因/styleReady、素材分类三级回退、活跃批次去重、SanitizeAPICallPayload 落点、chapter-asset-breakdown fail-closed 校验、SRT 容错解析二轮确认）。
- **台账勘定延续**：台账 243 行 + pre-ledger 13 = **256 处断言抽查全部吻合**（§32.36 6 行为台账内新增）。
- **包结构变化**：仅 §32.36 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v48 队列 1（上游增量检查）✅、队列 2（第三十轮抽查）✅。

### v58（2026-09-28）：行号重排 + 第二十八轮定点抽查（未抽样分支）+ 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十八轮检查）。
- **台账行号重排**：以脚本将 §32 全部台账行顺序重编号（消除多轮追加造成的编号空洞），重排前后物理行数核对一致（237 行）。
- **第二十八轮抽查（未抽样分支）**：6 处新断言 → §32.35；6/6 吻合（分镜首帧门禁双文案、快速创建虚拟节点禁用原因、媒体直传永久失败当场抛出、重试 submission_unknown 门禁、画布外观默认键 v2、图片批量子任务 count 强制 "1"）。
- **累计（勘定）**：台账 **243 行** + pre-ledger 13 处 = **256 处断言抽查全部吻合**；精确化累计 3 处。
- **包结构变化**：仅 §32.35 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v47 队列（上游增量检查）✅、本轮定点抽查 ✅。

### v57（2026-09-28）：第三十五轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十五轮检查）。
- **第三十五轮抽查**：6 处新断言（§6.2/§9.4/§10.2/§25.2/§28.2）→ §32.34；6/6 吻合（快速菜单视口订阅重算、蒙版 count 钳制、CreationGuard 先于重读、trim 左右吸附交替、并发 1-10 钳制、maskSupported 双处检查）。
- **台账勘定延续**：台账 250 行 + pre-ledger 13 = **250 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.34 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v56 队列 1（上游增量检查）✅、队列 2（第三十五轮抽查）✅。

### v56（2026-09-28）：第三十四轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十四轮检查）。
- **第三十四轮抽查**：6 处新断言（§9.3/§10.2/§12.1/§16/§19/§25.3/§28.2）→ §32.33；6/6 域确认（孤儿中断文案逐字、declarative 只读列表、任务列表游标域确认、标签列 192px、标注两次 drawImage、导演提示词分段结构与防换人颜色指令）。
- **台账勘定延续**：台账 244 行 + pre-ledger 13 = **244 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.33 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v55 队列 1（上游增量检查）✅、队列 2（第三十四轮抽查）✅。

### v55（2026-09-28）：第三十三轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十三轮检查）。
- **第三十三轮抽查**：6 处新断言（§4.x/§8.2/§9.1/§10.1/§12.1/§23.3/§25.2）→ §32.32；6/6 吻合（opLabel 中文标签、CreationRun epoch 45s 租约、35mm 全画幅换算公式逐字、bindGenerationTask、批量上传网格常量 3/380/300、drawStepUpscale 倍增循环）。
- **台账勘定延续**：台账 238 行 + pre-ledger 13 = **238 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.32 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v54 队列 1（上游增量检查）✅、队列 2（第三十三轮抽查）✅。

### v54（2026-09-28）：第三十二轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十二轮检查）。
- **第三十二轮抽查**：6 处新断言（§4.2/§8.2/§10.1/§10.2/§13.3/§26.3）→ §32.31；6/6 吻合（重叠两两检测、上传进度按文件字节归一、表情双位图 + 钳制、maxInputCount 透传、技能搜索端点、两步导入按钮）。
- **台账勘定延续**：台账 219 行 + pre-ledger 13 = **232 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.31 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v53 队列 1（上游增量检查）✅、队列 2（第三十二轮抽查）✅。

### v53（2026-09-28）：第三十一轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第三十一轮检查）。
- **第三十一轮抽查**：6 处新断言（§2.4/§4.5/§6.2/§9.1/§25.1/§28.2）→ §32.30；6/6 吻合（批量连线规划 + 逐源资格过滤、路由失败切换 for 循环、SlotStack 诊断条 title 逐字、spread 可选项、结果回填 fallback 链 + effectKey、CanvasTheme 浅/深双主题 :6/:73）。
- **台账勘定延续**：台账 213 行 + pre-ledger 13 = **226 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.30 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v52 队列 1（上游增量检查）✅、队列 2（第三十一轮抽查）✅。

### v52（2026-09-28）：第三十轮定点抽查（视频工具/AI 助手链/技能运行时）

- **上游增量**：v1.5.9 之后仍无新提交（第三十轮检查）。
- **第三十轮抽查**：6 处新断言（§10.3/§28.5）→ §32.29；6/6 吻合（输出健全性按 kind 校验 + 整段去音注释增补、mergeVideos 至少 2 个 + Blob 双源、applyPlan 逐条 dispatch + 汇报替换、failTurn 重试回喂「请只输出修正后的命令 JSON」、空 commands 纯问答早返回、提音首选 aac copy 注释）。
- **台账勘定延续**：台账 207 行 + pre-ledger 13 = **220 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.29 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v51 队列 1（上游增量检查）✅、队列 2（第三十轮抽查）✅。

### v51（2026-09-28）：第二十九轮定点抽查（骨骼分层/asset-ingest/图片工具）

- **上游增量**：v1.5.9 之后仍无新提交（第二十九轮检查）。
- **第二十九轮抽查**：6 处新断言（§10.2/§12.1/§23.2/§23.3/§28.4）→ §32.28；6/6 吻合（骨骼分层优先级头注释逐字、probeMediaDurationMs、upscale high 逐倍 step-upscale + 4096 钳制、导演台 5 模板含中文描述、裁切中心方裁二轮确认、白膜材质跳过集）。
- **台账勘定延续**：台账 201 行 + pre-ledger 13 = **214 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.28 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v50 队列 1（上游增量检查）✅、队列 2（第二十九轮抽查）✅。

### v50（2026-09-28）：第二十八轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十八轮检查）。
- **第二十八轮抽查**：6 处新断言（§2.4/§4.5/§9.2/§9.4/§11.1/§16）→ §32.27；6/6 吻合（批量入队活跃 nodeId 过滤、插件上传仅进后端、插话端点 + 面板失败文案、LANE_ORDER 四泳道、任务反查节点双源、画布外观默认读取）。
- **台账勘定延续**：台账 195 行 + pre-ledger 13 = **208 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.27 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v49 队列 1（上游增量检查）✅、队列 2（第二十八轮抽查）✅。

### v49（2026-09-28）：第二十七轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十七轮检查）。
- **第二十七轮抽查**：5 处新断言（§3.1/§8.2/§9.6/§16/§28.6）→ §32.26；5/5 吻合（Agent 摘要 op.type 归约、folders 键二轮确认、SRT 导入固定 nodeId、权限去重抛错、video promptOnly 判定含 @文本展开注释）。
- **台账勘定延续**：台账 189 行 + pre-ledger 13 = **202 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.26 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v48 队列 1（上游增量检查）✅、队列 2（第二十七轮抽查）✅。

### v48（2026-09-28）：第二十六轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十六轮检查）。
- **第二十六轮抽查**：6 处新断言（§2.3/§12.2/§16/§22.2/§26.3/§28.1）→ §32.25；6/6 吻合（本地目录回落 capability 过滤、优化器系统提示边界逐字、provenance 三键映射、load 全量复位、双击三选择器守卫、分镜物化五态）。
- **台账勘定延续**：台账 184 行 + pre-ledger 13 = **197 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.25 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v47 队列 1（上游增量检查）✅、队列 2（第二十六轮抽查）✅。

### v47（2026-09-28）：第二十五轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十五轮检查）。
- **第二十五轮抽查**：6 处新断言（§2.4/§4.2/§10.2/§12.2/§16/§25.3）→ §32.24；6/6 吻合（标注撤销纯函数三元组、分镜 100 行双重执法、内置插件注册顺序即优先级、SSE after/Last-Event-ID 双路游标、背景模式枚举、NODE_SPECS metadata 默认）。
- **台账勘定延续**：台账 178 行 + pre-ledger 13 = **191 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.24 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v46 队列 1（上游增量检查）✅、队列 2（第二十五轮抽查）✅。

### v46（2026-09-28）：第二十四轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十四轮检查）。
- **第二十四轮抽查**：6 处新断言（§2.3/§4.5/§16/§22.6/§23.3/§28.1/§28.2）→ §32.23；6/6 吻合（自动布局排除项与泳道/拓扑分支、scheduleSave isDirty 门控、gestureRef useRef、八插槽 priority 全 0、mixer LoopRepeat/LoopOnce、触控板启发式）。
- **台账勘定延续**：台账 172 行 + pre-ledger 13 = **185 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.23 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v45 队列 1（上游增量检查）✅、队列 2（第二十四轮抽查）✅。

### v45（2026-09-28）：第二十三轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十三轮检查）。
- **第二十三轮抽查**：6 处新断言（§4.1/§4.3/§12.1/§25.1/§26.2/§28.4）→ §32.22；6/6 吻合（素材批量插入 Promise.all、取消对账 41 次常量、素材分类推断两级函数、标题按钮 aria-label、导演台输出 ensureCanvasNodeAsset、canvas-skills-changed 广播）。
- **台账勘定延续**：台账 166 行 + pre-ledger 13 = **179 处断言抽查全部吻合**。
- **包结构变化**：仅 §32.22 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v44 队列 1（上游增量检查）✅、队列 2（第二十三轮抽查）✅。

### v44（2026-09-28）：第二十二轮定点抽查 + 抽查总量勘定

- **上游增量**：v1.5.9 之后仍无新提交（第二十二轮检查）。
- **第二十二轮抽查**：6 处新断言（§4.5/§5.1/§6.x/§8.x/§9.x/§16/§22.6/§28.6/§29.x）→ §32.21；6/6 吻合（canFolderContain 除 frame 全收、folder 折叠 ≤3 列公式、maxInputCount 中文报错、`@[node:id]`/`@[skill:id]` token 构造、prepareClose 三态、技能名上限 80、版本恢复链、素材入库重试）。
- **抽查总量勘定（重要修正）**：以 awk 逐节物理清点为准——§32 台账行 **160 行** + pre-ledger 13 处 = **173 处断言抽查全部吻合**。此前轮次转写的「累计 187」系加法错误（误将本轮前 direct 计为 174），现已修正；行号因多轮追加存在空洞，以物理行数为准。
- **包结构变化**：章节计数不变（35 章，§32.21 为台账扩样行）；卡/矩阵计数不变（45/44）。
- **队列清算**：v43 队列 1（上游增量检查）✅、队列 2（第二十二轮抽查）✅。

### v43（2026-09-28）：第二十一轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十一轮检查）。
- **第二十一轮抽查**：6 处新断言（§4.5/§6.2/§8.4/§10.1）→ §32.20；6/6 吻合（Kahn 拓扑注释逐字、不重叠摆位 gap 36、远程导入幂等键、版本预览空动作表、媒体泳道 LANE_ORDER、导入幂等键）。
- **累计 167 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.20 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v42 队列 1（上游增量检查）✅、队列 2（第二十一轮抽查）✅。

### v42（2026-09-28）：第二十轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第二十轮检查）。
- **第二十轮抽查**：6 处新断言（§4.5/§5.x/§10.x/§12.1/§16/§28.4/§29.1）→ §32.19；6/6 吻合（canFolderContain、Mask 强制内嵌注释、插件注册四项校验、-ss/-map 注释〔增补：空 mdat 风险与 attached pic 细节〕、摆场能力收窄、素材分类默认）。
- **累计 161 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.19 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v41 队列 1（上游增量检查）✅、队列 2（第二十轮抽查）✅。

### v41（2026-09-28）：第十九轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十九轮检查）。
- **第十九轮抽查**：6 处新断言（§4.x/§8.4/§9.4/§10.2/§12.1/§16/§22.6）→ §32.18；6/6 吻合（批量表行连线同步 + JSON 相同跳过、裁切 0-1 归一化钳制、unregister 三段清理、插槽 priority/order 排序、version-preview 前缀、导演台孤儿修复注释逐字）。
- **累计 155 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.18 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v40 队列 1（上游增量检查）✅、队列 2（第十九轮抽查）✅。

### v40（2026-09-28）：第十八轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十八轮检查）。
- **第十八轮抽查**：6 处新断言（§4.2/§5.1/§6.2/§9.2/§10.3/§16）→ §32.17；6/6 吻合。**精确化第 3 处**：重试 clientOperationId 哈希实际输入含 `generation-retry\0` 前缀（SHA-256 三段拼接），本包此前转写略去该前缀。
- **累计 149 处断言抽查全部吻合**；无断言错误。
- **包结构变化**：仅 §32.17 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v39 队列 1（上游增量检查）✅、队列 2（第十八轮抽查）✅。

### v39（2026-09-28）：第十七轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十七轮检查）。
- **第十七轮抽查**：6 处新断言（§9.3/§10.2/§12.2/§16/§25.3/§28.5）→ §32.16；6/6 吻合（中心方裁、本地回落 4 协议、UpstreamURL 剥 query、96 字符截断、孤立 loading 五条件、分镜物化 120px）。
- **累计 143 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.16 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v38 队列 1（上游增量检查）✅、队列 2（第十七轮抽查）✅。

### v38（2026-09-28）：上游增量检查 + 自检脚本负向测试

- **上游增量**：v1.5.9 之后仍无新提交（第十七轮检查）。
- **自检脚本负向测试（元验证）**：故意篡改矩阵分桶汇总（ADOPT_METHOD 15→14）后，`check-beeftv-research.py` 正确报出两处问题（分桶计数不符 + 合计不符）并以退出码 1 失败；从备份恢复后重新全绿。**自检脚本自身能捕获篡改/漂移，验证器有效性成立。**（过程记录：首次用 BSD sed 做篡改时因 `-i ''` 在 sh 下解析异常未生效，文件经 diff 确认未变，改用 Python 完成篡改注入——负向测试的注入方式本身也经核对。）
- **包结构变化**：无。
- **队列清算**：v37 队列 1（上游增量检查）✅。

### v37（2026-09-28）：第十六轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十六轮检查）。
- **第十六轮抽查**：6 处新断言（§12.2/§13.1/§16/§19/§22.6/§25.1）→ §32.15；6/6 吻合（sandbox 占位逐字、分镜就绪门禁含角色卡版本错误文案、worker 槽位租约、Agent 刷新合并注释、小地图两段拖拽、版本导出排除笔画注释）。
- **累计 137 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.15 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v36 队列 1（上游增量检查）✅、队列 2（第十六轮抽查）✅。

### v36（2026-09-28）：第十五轮定点抽查 + 上游增量检查

- **上游增量**：v1.5.9 之后仍无新提交（第十五轮检查）。
- **第十五轮抽查**：6 处新断言（§4.3/§9.2/§19/§23.3/§28.1/§29.3）→ §32.14；6/6 吻合（手柄 14/28px、epsilon 0.001 具名常量、小地图空场景兜底、load 清定时器、directResourceURL 三重守卫、locked 几何跳过）。
- **累计 131 处断言抽查全部吻合**；无新增精确化。
- **包结构变化**：仅 §32.14 追加；卡/矩阵计数不变（45/44）。
- **队列清算**：v35 队列 1（上游增量检查）✅、队列 2（第十五轮抽查）✅。

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
| 测试套件 | 全景：290 个 *.test.* 文件（web/test 全部 294，含 4 夹具/助手；v100 勘误，原记 292）/111 canvas 前缀按名索引（§19）；8 个测试全读（画布四件 §15 + 抽读四件 §19）；其余按需 | file:line |
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
| 测试套件 | 全景 290 *.test.*（v100 勘误，原记 292）/111 按名索引（§19）；8 个测试全读 | file:line |
| 文档站 | backend-database.mdx 画布章节；http-api.mdx 定性；features.mdx 全文对照（§18） | file:line |
| 插件 | 机制面（§16）+ 六内置插件能力面（§22）+ 协议包抽样 | file:line |
| 本地伴随进程 | 全（§17） | file:line |
| 时间线 | 命令/历史/AI/摘要四核心面全（§21）；5 个几何文件与 editor 面板未读 | file:line |
| 运行时行为 | 未执行 | 静态阅读边界声明见 REPORT §6 |

## 下一证据队列（截至本日志最新轮次）

1. ✅（v83 轮清算）补录复验：回源比对确认 v79/v80-四十九轮条目所述断言全部已有落档行（390/344/346/347/349/351/352/253+353/387/269），零丢失，未补录新行。
1. （需运行/浏览器授权，暂缓）运行时审计——按 tdcanvas 包 RUNTIME_AUDIT「真实素材非付费路径」红线，且不得触发真实生成。
2. 静态阅读面已全量覆盖：**708 处断言抽查 100% 吻合〔3 处精确化〕**（§32 台账 695 行 + pre-ledger 13）+ 卡/矩阵/台账行号/标题编号机械校验（含负向测试验证）+ 交互目录九章节回源复验 + 目录 §10 三支判定有锚 + 卡↔矩阵交叉核对（3/3）+ **PATTERN_CARDS 45/45 卡面二轮回源完成** + REPORT 结论面复核（§3 七项分歧全锚）+ codex 分支树差监控闭环 + §35 差异审计机械重跑（两处误记勘误）+ §20 算子计数勘误（45 唯一名）+ §14/§16-§31 跨章抽样 + 时间线域 17 文件 API 面抽样 + REPORT §2 表 11 行全锚 + 画布本体 §4-§13 抽样 + 历轮上游增量检查 + 目录/章节一致性核验；后续迭代转为按需补强：用户点名的域、上游再次前移时的增量差异审计、实现对照时的定点深读。
