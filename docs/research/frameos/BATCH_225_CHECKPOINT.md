# FrameOS Clone Loop Checkpoint — Batch 225 收尾 (2026-09-25)

> **全量回归三 (2026-09-28, Batch 280)**：`run-frameos-verifiers.sh` 69/69 PASS
> （套件新增 batch279 裁剪态）。

> **裁剪态已实现 (2026-09-28, Batch 279)**：内容图工具条 裁剪 → 进入裁剪态
> （控制条 退出裁剪/宽高比自由/480×480 输入/确认裁剪 + 8 手柄 + 三分格参考线，
> 按源站 cico-root 采样）。确认=mock alert 并退出；验证器 batch279 14/14 PASS。

> **故事版模式复核 (2026-09-28, Batch 276)**：源站空节点面板点故事版 =
> 模式切换（按钮高亮 + 占位文案 10-15 秒剧情→4-8 分镜逐字一致 + 模型帧界 O2.5
> + 规格 2K·16:9 + 积分 100）——克隆 storyboardMode 实现逐项吻合，无需改动。
> 采样后测试节点已删除，画布 5 节点基准位完好。

> **会话收尾留档 (2026-09-29)**：本会话 Batch 250-321+ 共 70+ 批全部完成推送。
> 源站画布节点渲染故障与框选失效持续（两问题独立，realtime 通道/热更新），
> 顺延项（双分组小地图判定、剪辑台编辑器采样、规格宽高比完整清单、
> 载荷级节点清单验证）等源站恢复后按文档化清单执行。克隆侧 70/70 多次认证、
> 全部文档/手册/矩阵对齐、我的范围工作区干净、无未推送提交。

> **Batch 288 (2026-09-28 深夜续)**：缩放范围实测 15%–500%，克隆 minZoom/
> maxZoom 修正为 0.15/5。**Batch 262 丢失节点全部服务端回归**（同步掩蔽非删除），
> 画布对账完成：删重建副本、原生节点保留并归位（≤30px），现存 7 节点
> （含 153bc6 文本节点1 / 2981fd 图片节点1 两个历史遗留）。框选仍失效（延续）。

> **提交完整性审计 (2026-09-28 深夜, Batch 286)**：当日 250-285 全部 35 个
> 批次提交均在 origin/master（含并行 sweep 交织提交，内容逐一核对）。

> **全量回归四 (2026-09-28, Batch 303)**：`run-frameos-verifiers.sh` 70/70 PASS
> （套件新增 batch300 规格二维弹层；涵盖缩放边界/空节点语义/模型清单/裁剪态
> 全部当日变更的最终认证）。

> **规格二维弹层已实现 (2026-09-28, Batch 300)**：源站规格控件为 分辨率
> [1K,2K] + 宽高比 [16:9,9:16,21:9,4:3,3:4,1:1] 二维弹层，值显示「2K · 16:9」。
> 克隆替换原单一合并列表为二维弹层（选完不自动收起，外部点击关闭）；
> 模型下拉 14 项同批落地（Batch 299）。verifier batch300 12/12 PASS。

> **收尾扫描 (2026-09-28 深夜, Batch 283)**：交互探针 + 结构标记全部与基线
> 一致（内容图工具条十项、侧栏/dock 钮数、5 节点），无新漂移。当日闭环批次：
> 250-282（分组全链路/⌥复制/裁剪态/漂移跟踪/文档手册/三次全量 69-69 绿）。

> **帮助面板复核 (2026-09-28, Batch 275)**：源站帮助面板仍为快捷键四组
> （创作/缩放/移动画布/其他），无操作指南/成组内容——克隆 FrameosHelpPanel
> 结构逐字一致，无漂移。

> **全量回归二 (2026-09-28, Batch 264)**：`run-frameos-verifiers.sh` 68/68 PASS
> （套件含新增 batch257 ⌥拖拽复制；batch169 重试后通过——既知瞬态）。

> **分组右键菜单 + 重命名已对齐 (2026-09-28, Batch 262)**：源站分组右键 =
> 复制⌘C/创建副本⌘D/删除⌫（点击效果未采样→mock）；双击标签内联重命名
> （实测 组1→探测组A）。克隆实现 renameGroup + 内联 input + 分组 contextmenu；
> verifier batch251 扩至 55/55 PASS。

> **批量连线端口已对齐 (2026-09-28, Batch 261)**：`.canvas-batch-selection-chrome`
> (批量选区层, 同矩形/淡边框/pointer-events:none) 右缘带 24px 圆形「批量连线」
> 端口 (right:-12 垂直居中)。点击进连线态但提交语义未采样到（未产生边）——克隆
> 渲染端口 + mock toast，不发明行为。滚轮=平移再获佐证。verifier batch251 扩至
> 49/49 PASS。

> **分组角点手柄=装饰 (2026-09-28, Batch 258)**：源站实测 NW 手柄（真实拖拽 +
> 合成事件双路径）拖 30px 零变化——`.canvas-group__handle--*` 无行为语义，
> 克隆装饰性实现即正确。采样后已解组复原。

> **⌥拖拽复制已采样并实现 (2026-09-28, Batch 257)**：源站实测（合成 alt+drag）=
> 原节点留在拖拽落点 + 同题副本偏移 (+20,+15) 自动选中。此前"不可采样"结论推翻。
> 克隆：store.duplicateNodeAt + onNodeDragStop altKey 分支；verifier batch257
> 10/10 PASS（副本/偏移/选中/两级撤销）。手册 duplicate-delete-history 与
> help-and-shortcuts 已更新为实测。

> **全量回归 (2026-09-28, Batch 256)**：`run-frameos-verifiers.sh` 67/67 PASS
> （Batch 251-253 分组功能与共享辅助重构后全量无回归）。

> **源站新鲜度扫描 (2026-09-28, Batch 255)**：无结构变化。侧栏六钮（添加节点/
> 项目资产/素材库/本地上传/模板/帮助）、底部 dock 七钮、头部（下载桌面端/积分/
> 项目切换）均与克隆基线一致；内容图工具条仍为十项（全屏/下载/收藏 纯图标 +
> 超清/720全景/打光/改图/裁剪/标注/宫格切分）；帮助快捷键表四组逐字一致，
> 已知历史陈旧声明（左键拖动=平移、滚轮=平移）无变化。测试画布 5 节点完好。

> **状态更新 (2026-09-27 晚, Batch 252 收尾)**：宫格/垂直排列补采完成
> （`docs/research/liblib-frameos-batch252-2026-09-27/ARRANGE_OBSERVATIONS.md`）：
> 宫格=按原Y排序 ceil(√n) 列行优先 2×2 确认（与克隆一致）；**垂直=同样按 Y 排序**
> （推翻克隆按 X 推断，已改 `arrangeGroup`）；间距 40/对齐盒+28 规则全面确认。
> ⚠️ 源站同步 bug：对同一分组连续两次排列 ops（<10s）会**永久丢节点**（服务端不再
> 返回，撤销不可用）；已按记录修复测试画布（补建两节点+拖回基准 ≤9px）。后续采样
> 禁止对同一分组连续快速排列。素材库「添加参考素材」确认为新建内容节点（iframe
> 弹层需真实坐标点击，资产在「画布素材」目录）。verifier batch251 扩至 44/44 PASS。

> **状态更新 (2026-09-27, Batch 251 收尾)**：**成组阻塞项已解除**——合成 pointer
> 事件恢复框选后 `el.click()` 采样到完整成组行为（详见
> `docs/research/liblib-frameos-batch251-2026-09-27/GROUP_OBSERVATIONS.md`）：
> 分组覆盖层 `.canvas-group`（成员 bbox+28、rgba(c,.16)/rgba(c,.9)/r12、组N 标签、
> 四角手柄）、展开工具栏六键（切换背景色/排列方式│整组执行/存为模板/解组/批量下载）、
> 10 色板弹层（is-current 蓝环）、排列菜单（水平=按原 Y 一行、间距40、对齐盒左上+28）、
> 分组拖拽全员跟随、解组保持成员位置（源站解组后工具栏残留=bug，克隆正确隐藏）。
> 克隆实现：store groups/selectedGroupId + FrameosGroupCanvas（viewport 首子层）+
> FrameosGroupToolbar 双模式（多选成组真实现；多选工具条几何修正为 bbox 居中）。
> verifier batch251 37/37 PASS，回归 229/232/234 全绿。采样后源站画布已复原
> （解组+逐节点拖回，≤3px，刷新确认持久化）。
> **历史状态 (2026-09-26 深夜, Batch 250 收尾)**：226-249 已全部完成推送。

## Batch 252 已完成（本段为计划存档）

**主题：源站「宫格/垂直排列」参数补采**——已在同日完成（见顶部状态更新与
`docs/research/liblib-frameos-batch252-2026-09-27/ARRANGE_OBSERVATIONS.md`）。
采样在画布 1 直接进行（Batch 251 的解组+拖回复原手法），未新建画布；
画布切换弹层 toggle 不稳定的问题因此绕过。

## Batch 253 候选

- verifier 框选辅助函数去重（batch226/229/232/234/251 重复的
  elementFromPoint 扫描逻辑抽到共享 python 模块）。
> 本日新增：241 手册同步(4866c588)、242 成组工具条换行修复+克隆渲染记录5张(ff2803ff)、
> 243 手册PROGRESS刷新(adf06372)、244 验证器90s goto加固(经归档)、246 证据注记(35bef7d1)、
> 245 帮助面板复检无漂移(acf9debd)、247 移除发明行为方向键/Tab(5ca726f5)、
> 248 ⌘±/⌘0 缩放快捷键(经归档)、249 键盘表文档(a016cef8)。验证基线 66/66 PASS。
> **源站新鲜度（Batch 250 扫描）**：无更新提示，6 节点基线稳定，内容图右 handle
> 语义不变。**遗留阻塞项**：①成组点击效果——源站拖拽输入路径不稳定无法复现框选，
> 克隆保持 mock；②宫格切分/打光/改图等付费动作——按纪律永不点击；③⌥拖拽复制——
> 源站帮助声明但交互细节不可采样，未实现（避免发明行为）。
> Batch 233 源站新鲜度扫描：结构稳定无新版本。**Batch 226 的"剩余计划"已完成**
> （内容视频菜单=三行极简，见 Batch 228）。下方 Batch 226 计划段落仅作历史记录。

## 本轮完成（均已提交推送）

| Batch | 内容 | Commit |
|---|---|---|
| 220 | 内容图片富工具条（十项、按 imageUrl 门控、空图片无工具条）+ 验证器 | 9b073755 |
| 221 | 3D导演台/视频剪辑台工作台节点渲染器（图标+胶囊按钮）+ 验证器 | e4f276cd |
| 222 | 内容音频节点 plyr 形态播放器（wav 探针采样）+ 验证器 | 7483852c |
| 223 | 本地上传真实接线（按 MIME 建带内容节点、标题=文件名去扩展名）+ 验证器 | 600009fa |
| 224 | 素材库二轮对齐 + 添加参考素材接线（0 选中禁用、建节点后关闭）+ 验证器 | 1057ebf1 |
| 225 | **内容媒体统一语义**：内容媒体选中=富工具条+无面板+仅右 handle；空节点=面板+双 handle；内容视频九项工具条+时长徽章+右下替换按钮；12 个旧验证器同步更新 | 88ee6ff3 |

验证基线：`scripts/run-frameos-verifiers.sh` 53/53 PASS；`npm run check` 0 error。

## Batch 225 关键结论（推翻旧采样的部分）

- 内容媒体节点（图片有图/视频/音频有料）选中**无 PromptEditor 面板**——
  Batch 159/160/161/171/172/180/183/190/196/197/198/200/220 中相关断言已全部
  更新为"清空内容后验面板"或"内容态无面板"。
- 内容视频工具条为九项（全屏查看/下载/收藏/剪辑/裁剪/音视频分离/超清/去字幕/
  片段重拍），覆盖 Batch 171 的旧两项采样。
- handle 语义：内容媒体仅右 handle；空节点/文本/工作台节点左右双 handle。
  batch174 连线验证器改为先清空图片内容再连线。
- 无头 Chromium（Playwright）无 H.264 解码器：视频时长徽章验证用
  `/tmp/frameos-probe-video.webm`（ffmpeg 生成，命令在 batch225 验证器头部注释）。

## Batch 226 进行中（下一棒从这里接手）

**主题：右键菜单内容感知行**。已采样：内容图片节点菜单 =
复制⌘C / 复制图片 / 创建副本⌘D / （线）/ **设置为资产图** / （线）/ 删除⌫
（详见 SOURCE_OBSERVATIONS.md「内容图片右键菜单」条目）。

剩余：①补采 空图片/文本/内容视频 菜单行与禁用态；②克隆 FrameosContextMenu
按类型/内容态差异化（至少补「设置为资产图」mock）；③验证器；④复核 batch170/178
旧菜单验证器。

## 后续候选

- 内容图片工具条 ⛶全屏查看 行为采样（当前克隆为 mock alert）
- 空节点右键菜单新版复核
- 剩余 ⚪ 项需真实生成事件（付费，禁止）

## 环境注意

- dev server: 端口 4317（`npm run dev`）；node 需 `nvm use 24`
  （本轮 shell 出现 node 不在 PATH 的情况）。
- 源站探针遗留：素材库 上传素材 目录留有 clone-probe-tone.wav 与
  clone-probe-shot.mp4 两个库内资产（画布节点均已删除，库资产无入口删除或未采样到）。
- 测试媒体（用户授权，仅上传探索、严禁真实生成）：见 goal 附件清单
  （10 图 + 2 wav + 2 mp4），已记录于 TEST_MEDIA_ASSETS.md。


## Batch 326（2026-09-29）：源站恢复确认 + 过期账本行修正

**源站恢复（重大）**：batch 301-308 记录的源站故障结束——7 节点对账态完整回归
（3D导演台/视频剪辑台/图片节点1/2/3/生成蓝色手机图片-2×2），蓝色参考虚线完好，
「进入剪辑台」入口在位。batch 301-308 的"0 节点"实为 500% 缩放停留误判。
**源站依赖采样队列解冻**：剪辑台编辑器采样、内容图片工具条 ⛶全屏查看采样、
裁剪确认行为采样、分组端口提交语义采样——均可恢复（保持不触发真实生成）。

**过期账本行修正（4 处，引证在案）**：
- IMPLEMENTATION §7「模型选择器 6 模型（mock）」→ Batch 299 已更新为源站
  14 模型清单（Seedream 5.0 Pro/帧界 O2.5 系/O2/G2/G Pro/Lite/M8.2 等）。
- IMPLEMENTATION §7「参考选择模式 真实框选未实现」→ 源站实测为**点击节点加参考**
  （Batch 197 采样，非框选）；克隆 Batch 197 已同款实现，行删除。
- BEHAVIORS「多选管道已通，工具条未实现」→ FrameosGroupToolbar 双模式工具条
  已全链路实现（Batch 251-262，verifier batch251 59 项），行更新。
- BEHAVIORS「拖动时节点对齐辅助线 ❌」→ FrameosAlignmentGuides 已实现并在
  canvas/page.tsx:725 接线，行更新为 ✅。

验证基线：`scripts/run-frameos-verifiers.sh` **70/70 PASS**（Batch 326 复跑）。
证据：recovery-batch326-nodelist.png / recovery-batch326-fit.png。

## Batch 327-328（2026-10-01）：源站阻塞期 — 两个克隆侧数据一致性缺陷

**源站阻塞**：`frameos.cn` 对自动化启动的浏览器一律弹「确定你不是机器人」，
**人工点击亦判失败**（与 profile 新旧无关：已持有 liblib.tv 登录态的 :9222 profile
同样被拦）。人机验证属站点反自动化访问控制，**不尝试绕过**；本轮全部源站采样顺延。
详见 [`SOURCE_ACCESS_BLOCKED_2026-10-01.md`](SOURCE_ACCESS_BLOCKED_2026-10-01.md)。
源站阻塞不构成停工理由，以下两批改做**克隆侧运行时缺陷挖掘**（探针驱动，不依赖源站）。

**Batch 327 — 节点克隆 id 碰撞（静默丢节点）**：`duplicateNode` /
`duplicateNodeAt` / `pasteNodeFromClipboard` 用裸 `Date.now()` 生成节点 id，
同毫秒连按两次 ⌘D / ⌘V 产生**相同 id**，React Flow 按 `data-id` 索引 →
后写入者覆盖前者，**按两次只多一个节点**。实测：duplicate 10/11 唯一、
paste 10/13 唯一；对照组 `addNode`（Batch 223 已有计数器）9/9 唯一，
据此把缺陷隔离到这三条路径。修复 = 追加 `nodeCloneIdCounter`，
与 addNode/createGroup 既有解法一致。verifier batch327 **14/14 PASS**。

**Batch 328 — 分组完整性（悬空成员 + 陈旧分组盒）**：`removeNode` 只过滤
`nodes`/`edges` 不维护 `groups` → 被删节点仍留在 `memberIds`（悬空引用），
分组盒 `x/y/w/h` 从不重算。实测删除 1 个成员后 `dangling:["text-1"]`、
盒仍为删除前的 737×319。而 `arrangeGroup` 以 `memberIds` 为唯一事实来源，
悬空 id 不报错、只让成员集静默偏小。修复 = 新增 `reconcileGroups()`：
剪悬空成员 + 按存活成员 bbox+28 重算盒 + 成员删空则分组消失 + 同步清
`selectedGroupId`。修复后 `dangling:[]`、盒 737×319 → 356×256。
verifier batch328 **17/17 PASS**；batch251（分组 59 项）回归 PASS。

**顺延（需已登录源站会话）**：剪辑台编辑器采样、内容图片 ⛶ 全屏查看采样、
裁剪确认行为采样、分组端口提交语义采样、双分组小地图判定、规格宽高比完整清单、
载荷级节点清单验证。

**候选（Batch 329）**：`undo`/`redo` 历史快照只存 `{nodes, edges}` 不含 `groups`，
且 `createGroup` 未入历史栈 → 撤销成组动作不恢复分组。改动会影响 batch251 断言，
需单独批次评估。

**环境坑（已修）**：`/tmp/frameos-probe-video.webm` 会被 macOS 清理，导致
batch225/230 报 `ENOENT`。重建后两者均 PASS —— 见到 ENOENT 先重建素材再判回归。

## Batch 329（2026-10-01）：分组进入撤销历史

**Batch 328 的直接后续**。328 让 `removeNode` 开始改写 `groups`，而历史快照只存
`{nodes, edges}` → 同一动作正向被完整记录、撤销只回滚一半。核心症状：
撤销「删除分组成员」时**节点回来了但成员集没回来**，被恢复的节点被静默踢出分组，
且不产生悬空引用、不报错（用户表现为「撤销后节点飘在组外面」）。
另两条：`createGroup` / `ungroup` 完全不入栈，撤销无效。

修复：快照类型纳入可选 `groups`；新增 `pushHistorySnapshot(state)` 统一入口，
**13 处**入栈路径全部改用它（根因是 13 处各自手写、漏带只是迟早）；成组/解组
入栈；undo/redo 还原 groups 并过 `reconcileGroups` 兜底。
verifier batch329 **23/23 PASS**（含伪造旧格式快照的兜底断言）。
详见 [`liblib-frameos-batch329-2026-10-01/README.md`](../liblib-frameos-batch329-2026-10-01/README.md)。

**候选 Batch 330**：`arrangeGroup` / `moveGroup` / `setGroupColor` / `renameGroup`
仍不入历史栈。需先确认源站是否视其为可撤销动作 —— 源站不可访问时**不得凭空发明**，
若按克隆一致性补齐必须显式标注为 clone-only 决策。

## Batch 330（2026-10-01）：分组重命名 / 改色 的撤销覆盖

Batch 329 之后 `createGroup` / `ungroup` / `arrangeGroup` 可撤销，但
`renameGroup` / `setGroupColor` 仍只改 state 不入栈 → **重命名、改色不可撤销**
（探针实测 `pushed:false, undoRestores:false`）。已改用 `pushHistorySnapshot`。

**顺带修掉一个新问题**：简单加快照后发现 `renameGroup(gid, '   ')` 状态虽不变
却照样入栈 —— 用户按一次撤销被消耗掉、什么也没发生。已加**无净变化不入栈**守卫
（空名/同名/同色 → 直接 return）。入栈从此与「状态确实变了」严格等价。

**`moveGroup` 故意不改**：它每帧调用，入栈会灌爆 20 格栈（Batch 189/232
节点拖拽的老问题）。整组拖拽的撤销由 UI 层在手势开始时调一次 `pushHistory()`
保证（`FrameosGroupCanvas.tsx:70`）。验证器把这条当**不变式**测：
一次 push + 6 次 moveGroup → 深度只 +1，一次撤销精确回原位（盒 + 全部成员）。

⚠️ **CLONE_DECISION**：源站是否视分组重命名/改色/拖拽为可撤销动作**未采样**
（源站阻塞）。本批是**克隆内部一致性**决策，**不是源站对齐声明**；恢复访问后需复核。

verifier batch330 **22/22 PASS**；batch251/232/177/159/174/328/329 回归 8/8 PASS。
详见 [`liblib-frameos-batch330-2026-10-01/README.md`](../liblib-frameos-batch330-2026-10-01/README.md)。

**候选 Batch 331**：反向问题 —— 是否存在**不该入栈却入了**的 action
（纯 UI 状态如 minimap 显隐/面板开关入历史，导致撤销「无事可做」）。
需先用探针枚举全部 action 的入栈行为再决定立项。

## Batch 331（2026-10-01）：撤销栈按画布隔离

审计 Batch 329/330 后枚举全部 48 个 store action 的入栈行为（16 入栈 / 32 不入栈），
在不入栈的一批里发现 `setBreadcrumb` 的问题：换画布时**只**清 `groups`/选中态，
**不重置** `past`/`future`，而快照也不记录来自哪张画布 → 在画布 A 上做的动作
可以在画布 B 上「撤销」，把 A 的 nodes/edges/groups **整份灌进 B**。

实测：画布 B 从 0 节点变成画布 A 的 7 个节点（`afterUndoOnB`）。
`reconcileGroups` 在此并不算错 —— 它拿 A 的节点收敛 A 的分组完全自洽；
缺陷在于**根本不该把 A 的快照应用到 B**。

修复：`HistoryEntry` 带 `canvasKey`；`setBreadcrumb` 换画布清空 past/future；
`undo`/`redo` 遇异画布快照拒绝并清栈（兜底）。旧快照无 `canvasKey` 按同源处理。
verifier batch331 **19/19 PASS**（含同画布逐步 undo1/undo2/redo1/redo2 断言）。

⚠️ **首版探针漏判的教训**：直接在空 `past` 上切画布再撤销会得到 `B-clean`，
但那只是因为 `undo` 是 no-op —— 必须先 `addNode` 制造快照才能复现。
「先造前置状态」已写进探针与验证器，避免后人重蹈。

**顺带记录（非本批缺陷）**：`canvasData` 只在切换时从 `MOCK_CANVASES` 写入、
不回写实时编辑 → 切走再切回会丢失本地新增节点与分组。这是原型既有的 mock 边界
（不实现持久化），验证器已按此正确的不变式书写断言。

**候选 Batch 332**：`canvasData` 回写实时编辑。需先确认源站是否持久化画布内编辑
（源站不可访问时不得凭空发明）；若按克隆一致性补齐须标注 clone-only。

## Batch 332（2026-10-01）：canvasData 回写实时编辑

`setBreadcrumb` 换画布时用 `MOCK_CANVASES` 覆盖目标画布，**从不把离开画布的
实时 nodes/edges/groups 写回 canvasData** → 本地新增/移动/删除的节点、分组、
连线，在切走再切回后**全部丢失**。

实测：画布 A 加 1 个节点 7→8 → 切到画布 B（0 节点）→ 切回 A 变回 **7**。
用户表现为「编辑内容凭空消失，无任何提示」。

修复：切走前把实时 nodes/edges/groups 写入 `canvasData[prevKey]`；目标画布
优先读已保存数据，未编辑过的画布仍回落 fixture；`canvasData` 类型新增可选
`groups`（分组属于画布）。
verifier batch332 **17/17 PASS**（含面包屑计数口径一致性）。

⚠️ **连带更新 Batch 331 验证器**：331 第 4 项断言「切回 A 后节点数 == 7」，
在 332 修好后必然失败 —— 因为新增节点现在**正确地存活**了。
这不是回归，而是**旧断言描述的正是缺陷本身**。已改为它真正关心的不变式
「不混入 B 的节点」（跨画布污染判据）。
**教训：断言要绑定真实性质，不要绑定缺陷的副作用。**

⚠️ **CLONE_DECISION**：源站是否持久化画布内编辑**未采样**（源站阻塞）。
本批修的是原型内部的**数据丢失洞**，任何交互式原型都不应有；
但**不是源站对齐声明**，恢复访问后仍需复核。

**候选 Batch 333**：`canvasData` 只存内存，**刷新页面仍丢失全部编辑**。
Batch 208 已覆盖画布内的刷新持久化，但跨画布编辑的刷新持久化尚无覆盖。
需先确认源站刷新语义（不得凭空发明）；若补齐须标注 clone-only。

## Batch 333（2026-10-01）：画布内容跨刷新持久化

**本批有源站证据**（与 331/332 的 clone-only 不同）：手册 20-reference.md
「刷新后内容保留；撤销/重做历史清空」；Batch 251 采样「刷新确认持久化」。
克隆此前只把内容放内存，刷新即回 fixture → 编辑全部丢失，属**真实对齐缺口**。

修复：localStorage 持久化（沿用 directorStore 的 SSR 安全 + try/catch 降级模式），
写入用**单一 store 订阅**（不在 13 个写入点各加一行 —— 反用 Batch 329 的教训），
**只持久化内容、不持久化 past/future**，与源站「内容保留、历史清空」一致。

⚠️ **SSR hydration 坑**：第一版把持久化内容灌进 store 初值 → 控制台报
hydration mismatch（服务端读不到 localStorage，客户端能读到，两边树不同）。
改为初值一律用 fixture、持久化内容在**挂载后**由 `restorePersistedCanvas()`
应用。**任何读浏览器存储的初始化都不能放进渲染路径。**

🔴 **本批最重要的发现：Batch 208 的断言方向是反的。**
它声称验证「刷新后内容保留」，断言却是
`nodes_after == nodes_before`（上下文为删掉一个节点后刷新，节点数**回到删除前**）
—— 把**内容丢失**当成了持久化的成功条件。克隆把内容放内存时它 PASS，
一旦真持久化它反而 FAIL。已改为 `nodes_after == nodes_before - 1`。

**教训：一个「通过」的绿色断言，可能正锁着一个缺陷。** Batch 208 五项全 PASS，
却从未真正验证过持久化。

verifier batch333 **19/19 PASS**（含损坏 localStorage、非法结构、清空回落、
各画布独立、**hydration 不再复发**）。

**候选 Batch 334**：审计其余「声称验证但断言方向可能相反」的验证器 ——
grep 形如 `== nodes_before` / `== initial` 的断言，逐个核对该等于操作前还是操作后。

## Batch 334（2026-10-01）：持久化落地后的验证器隔离修复

Batch 333 让内容**真的**跨刷新持久化后，三个验证器的「刷新 = 干净起点」假设
同时失效 —— batch327 刷新后节点重叠、click 被 intercept 而超时失败。
内容不持久时「刷新」天然等于回到初值，很多验证器（注释里明写的）都悄悄依赖
这一点；持久化变真后这些假设全部失效。

新增共享助手 `goto_clean_canvas()`（放在既有共享模块 frameos_verify_common.py）：

| 验证器 | 失效的假设 | 处理 |
|---|---|---|
| batch327 | reload 后回到初值再测键盘路径 | 改用 goto_clean_canvas |
| batch208 | 同上（本批已修其断言方向） | 改用 goto_clean_canvas |
| batch183 | 注释明写「刷新获得干净状态」 | 改用 goto_clean_canvas + 更新注释 |
| batch333 | 自己是唯一写入方 | 结束时 clear() 并复验（+2 断言） |

⚠️ **batch327 的失败不是 id 碰撞回归**。它是修 id 碰撞的验证器，一失败很容易
误判成「修复坏了」。实际堆栈是 `Locator.click: Timeout 30000ms exceeded` +
`subtree intercepts pointer events` —— 失败在**点击**这一步，不在任何 check 断言。
> 教训：验证器失败先看**失败在哪一步**（断言 vs 交互超时），
> 再判断是功能回归还是测试环境问题，两者修法完全不同。

**候选 Batch 335**：Batch 333 提出的「断言方向可能相反」全仓审计 ——
grep 形如 `== nodes_before` / `== initial` 的断言，逐个核对方向。
batch208 已证明绿色断言可能锁着缺陷。

## Batch 335（2026-10-01）：全仓验证器「空断言 / 恒真断言」审计

Batch 208 证明**绿色断言可能锁着缺陷**。本批推广到全仓：扫描所有
`scripts/verify-*.py` 的恒真模式，**共 5 处，全部修正**。

| 文件 | 原断言 | 修正为 |
|---|---|---|
| verify-frameos-batch221 | `toolbar.count() >= 0` | `== 1` + 补 `node.selected == 1` |
| verify-liblib-batch200 | `... .count() >= 0 or True` | `== 1` |
| verify-liblib-batch528 | `node.count() >= 0 and is_visible()` | `== 1 and ...` |
| verify-liblib-batch562 | `... .count() >= 0`（or 短路分支） | `== 1` |
| verify-liblib-batch586 | `gallery.count() >= 0` | `== 1` |

`== []` 那一类（30+ 处）经抽查**全部合法**（确实在断言空态），不动。

⚠️ **空断言比「没有断言」更危险**：`check("card:selected", X >= 0 or True)`
在覆盖矩阵里显示为「✅ 已覆盖」，读账本的人会认为该行为已验证；
实际上它对任何实现都通过，包括功能完全损坏的实现。
不写断言至少在矩阵里是空缺，会引人去补。

**与 Batch 208 的关系**：208 是断言**方向反了**（锁定缺陷）；
335 是断言**恒真**（制造虚假覆盖感）。两者都是「绿色但无意义」。

修正后复跑：frameos221 13/13；liblib200/528/562 PASS；liblib586 18/18。

**候选 Batch 336**：把恒真断言检查做成**门禁脚本**（类似 verify-docs.py），
对 `scripts/verify-*.py` 扫描 `>= 0` / `or True` 并在 runner 前置运行，
避免同类问题再次混入。

## Batch 336（2026-10-01）：断言质量门禁

Batch 335 清了 5 处恒真断言，但**没有防复发机制**。本批固化为门禁脚本
`scripts/verify-assertions.py`，接入 `npm run assertions:check`。

| 规则 | 匹配 | 说明 |
|---|---|---|
| VACUOUS_COUNT | `.count() >= 0` | 计数不可能为负 |
| OR_TRUE | `... or True` | 显式或真，整条失效 |
| COMPARE_TO_NONE | `x == None` | 应写 `is None`（smell） |

**刻意不查 `== []`** —— Batch 335 已确认那 30+ 处都是真实断言「集合为空」，
误报会消耗信任，门禁必须精准。

🔴 **门禁上线当场又抓出 2 处此前漏掉的**（这正是一次性清理总会漏的证据）：

| 文件 | 原断言 | 修正为 |
|---|---|---|
| verify-liblib-batch437 | `after_target["nodeCount"] == 0 or True  # canvas-2 has fixture nodes` | `set(before).isdisjoint(after)` 断言**集合不重叠**（并给 canvas_state 补 nodeIds） |
| verify-liblib-batch448 | `"请选择字幕擦除区域" in ... or True` | 去掉 `or True` |

两处都不是随手写错：作者当时大概遇到断言失败，用 `or True`「解决」了 ——
那个断言从此永不再失败，**它要检查的东西变成无人看管**。437 尤其隐蔽：
注释说明了为什么 `count()==0` 不成立，但正确做法是断言集合不重叠，而非放弃断言。

**门禁有效性自检**（不验证门禁的门禁等于没有门禁）：注入 `.count() >= 0`
→ Found 1 / EXIT=1；还原 → 0 vacuous in 452 scripts / EXIT=0。

复跑：liblib437 PASS、liblib448 PASS。

## Batch 337（2026-10-01）：断言门禁接入 CI

`.github/workflows/ci.yml` 新增 `Assertion quality gate`（Type check 之后、
Build 之前，早失败省时间）。CI 现状：Checkout → Node → npm ci → Lint →
Type check → **Assertion gate** → Build。

**门禁在 CI 环境下的可用性已实测**：用 `git archive HEAD | tar -x` 还原出与 CI
等价的干净副本 → `0 vacuous assertions in 451 verifier scripts, EXIT=0`；
门禁只依赖 Python 标准库，无第三方依赖。✅

🔴 **顺带实测：`verify-docs.py` 目前不能进 CI**（干净 checkout 必失败）：
  - `research/upstream/*` 下的 `.ts` → **submodule 未初始化**；
  - `docs/user-manual/*/screenshots/*.png` → **被 gitignore**。
即它**只在本地工作区能过**（那里有 submodule 内容和被忽略的产物）。
接进 CI 会让每次 push 都红 → 本批**刻意不接**，并在 workflow 注释里写明原因
与前置条件（需先让脚本区分「产物缺失」与「链接写错」）。

> 教训：加 CI 步骤前先在**干净 checkout** 上验一次。本地能跑 ≠ CI 能跑。
> 与 Batch 329「13 处各自手写快照」同源 —— 分散的隐式假设总会在某刻集中爆发。

⚠️ **CI 改动未提交（凭据限制）**：`.github/workflows/ci.yml` 的门禁步骤仍留在
工作区未提交 —— 当前 git 凭据缺 `workflow` scope，push 被远端拒绝
（"refusing to allow an OAuth App to create or update workflow
.github/workflows/ci.yml without workflow scope"）。
这是凭据权限限制，**不做绕过**；需由有 `workflow` 权限者提交该文件。
在提交之前，门禁只能靠人工跑 `npm run assertions:check`。

## Batch 338（2026-10-01）：verify-docs.py 区分「产物缺失」与「链接写错」

Batch 337 发现 `verify-docs.py` 在干净 checkout 上必失败，因而无法进 CI。
本批新增 `is_expected_missing()`：submodule（`research/upstream/`）与 gitignore
截图（`screenshots/*.{png,jpg,...}`）**降级为 note**，真断链仍 `return 1`。

干净 checkout 实测（`git archive HEAD | tar -x`，与 CI 等价）：
`passed: 1197 files, 5169 targets, 302 expected-missing`，**EXIT=0** ✅

⚠️ **前提须说清**：干净副本里仍有 4 条指向 `10-tasks/use-agent.md` 的报错 ——
该文件目前是**未跟踪**状态（`??`），属**其他开发者的在途 WIP**。
按纪律本批**没有** `git add` 它。已实测：一旦其作者提交，干净 checkout 立刻 EXIT=0。
**这不是 verify-docs 的缺陷，而是工作区状态的真实反映。**

**一次自我纠正**：排查中我一度把 `90-troubleshooting.md` 的
指向 `10-tasks/use-agent.md` 的链接改成 `../10-tasks/...`，以为解析失败；
改完本地检查反而失败 → 说明**原路径本来就对**（链接以手册根为基准）。
已 `git checkout` 还原。
> 教训：在「文件未跟踪」与「链接写错」之间，先确认文件是否存在再改链接。

## Batch 339（2026-10-01）：「断言方向」门禁尝试 —— 否定结论（未上线）

尝试加 `UNANNOTATED_DIRECTION` 规则拦截 Batch 208 那类**方向反了**的断言。
**结论：不可行，已放弃，`scripts/verify-assertions.py` 保持 Batch 336 原状。**

原因：
1. **误报压倒性**：全仓报 129 条，含把 `page.evaluate` 的**多行 JS 字符串**
   误当 Python 扫到（`"(after) => window.__director_store..."`）；
   过滤后仍有 **83 条**真实 Python 断言命中。
2. **真实命中里绝大多数是对的**，且**检查名已自明**：
   `undo:node-removed` / `paste:node-added` / `alt:count-plus-one` ——
   再要求注释说明方向，是为已自明处强加噪声。
3. **真正的缺陷（208）靠的不是这条规则**：208 的问题是
   **检查名与断言互相矛盾**（名说「保留」、断言验「丢失」）。
   能抓它的是「名 vs 断言」的语义交叉核对，不是「有无注释」。

> 门禁的价值在于**零误报**。Batch 336 建立时已定标准「刻意不查 `== []`」，
> 理由是误报比漏报更消耗信任。129 条误报的门禁会被习惯性忽略，等于没有门禁。

本批是一次**有价值的否定结论**：花一轮确认这条路走不通，比留噪声规则强。

## Batch 340（2026-10-01）：组内复制副本的分组归属（含 reconcileGroups 两处镜像缺陷）

`duplicateNode` 的副本落在源节点 +40/+40，**常常在分组盒内**，但此前
**不加入该分组** —— 视觉「在组里」、实际不是成员。删掉原成员后盒塌缩（Batch 328），
副本被留在组外却仍处于原组盒区域，视觉错位。

实测：`INCONSISTENT: true`（`dupJoinedGroup:false` 而 `dupInsideBoxBefore:true`）。

修 1：`duplicateNode` 让**落在所属分组盒内**的副本自动入组并重算盒。

🔴 修 1 时 `dup:box-recomputed` 断言失败（盒 737、应 777），逐层挖出
`reconcileGroups` 的**两个独立缺陷**：

- **A「永远没变」**：原判定拿 `g.memberIds` 与**它自己**比 → 恒为「未变」
  → 永远保留陈旧盒、永远不剪枝。修法：新增 `previousMemberIds` 参数，
  由调用方传入**变更前**的成员集合。
- **B「变了也当没变」**：长度相同即判未变，漏判「删一个又加一个」的等长场景。
  补 `g.memberIds.every(id => nodes.some(n => n.id === id))`。

> 这两处是**同一函数里互为镜像的错误**。Batch 328 引入时只测了「删成员」
> 一条路径；Batch 340 第一次走「加成员」路径才暴露。
> **同一函数的不同分支往往藏着镜像缺陷，只测一条路径等于没测。**

⚠️ CLONE_DECISION：源站对「复制组内节点」的归属**未采样**（源站阻塞）。
本批修的是克隆自身一致性，非源站对齐声明。

verifier batch340 **14/14 PASS**；batch328/329/330/331/332/333/251/133/327 回归全绿。

**候选 Batch 341**：`reconcileGroups` 的教训适用于其它操作分组成员的路径 ——
`arrangeGroup` / `moveGroup` / `pasteNodeFromClipboard` 各自是否也只被单路径测过？

## Batch 341（2026-10-01）：分组盒几何不变式提升为 store 写入口的强制约束

Batch 340 修好了 `reconcileGroups` **函数内部**的两处缺陷，但那个函数只挂在
`removeNode` / `duplicateNode` / `undo` / `redo` 四条 action 上 —— **别的路径
根本不调用它**。本批回答 Batch 340 留下的候选问题：还有哪些路径只测了一条。

代码审计直接找出三条（都不是猜的）：

| 场景 | 入口 | 可达性 | 修复前实测 |
|---|---|---|---|
| 一键整理 | `FrameosMapDock` → `organizeNodes` | ✅ 真实按钮 | drift x/y/w/h |
| 拖拽成员 | `page.tsx onNodesChange` → `setNodes` | ✅ 拖动画布 | drift x/w/h |
| 面板删除 | `FrameosNodeEditPanel` → `setNodes(filter)` | ⚠️ 仅 debug 模式 | 悬空成员 `['text-1']` + 盒不收缩 |

第三条是重点：它与 Batch 328 修过的 `removeNode` 是**同一处缺陷的两条路径**
（右侧面板直接 `setNodes(nodes.filter(...))` 绕开了 action）。
**修一条漏一条 —— 正是 Batch 340 写下的教训本身。**

🔴 修 1 后 S1/S2 仍 STALE，挖出**更浅一层的缺陷**：`reconcileGroups` 的
`unchanged` 短路**只看 memberIds**，把「成员集合没变」当成「盒不用动」。
而**成员整体移动**时 `memberIds` 一个字都不变 → 盒永远不重算。整理和拖拽
栽的正是这个。改为**无条件重算**（前提已逐个核对：`createGroup`/`arrangeGroup`
的盒就是 bbox+28；`moveGroup` 盒与成员同量平移，平移不改变该关系），
`previousMemberIds` 参数随之**变得多余并被删除** —— 它当初只为喂那条错误短路。

修 2：把不变式收敛到 **store 的唯一写入口**。包住 `set`，写完 nodes/groups
后统一 `enforceGroupGeometry` 一次 —— 将来新加的 action 也不可能再漏。
与 Batch 329（13 处手写快照 → 单一出口）、Batch 333（多处写 localStorage
→ 单一订阅）同一判断。细节：重入守卫防无限递归；**无净变化返回同一对象**，
否则 Batch 333 按引用判断的持久化订阅会把同样内容反复写进 localStorage。

⚠️ CLONE_DECISION：源站是否允许把成员拖出分组、是否自动退组，**未采样**（源站阻塞）。
「拖动成员时盒跟随成员」是按克隆自身不变式推的，**未**发明「拖出即退组」。

verifier batch341 **22/22 PASS**，且做过**变异测试**：临时注释掉
`enforceGroupGeometry(...)` 后验证器如期失败于 `organize:box-recomputed`
（`box={x:33,y:5,w:737,h:319}` vs `expected={x:32,y:32,w:676,h:256}`）。
**改绿色断言前先证它会红** —— Batch 208 的教训。
回归 328/329/330/331/332/333/340 七批全绿。

**遗留观察**（不在本批范围）：`toggleDebugMode` 全仓**无任何 UI 入口**，
`FrameosNodeEditPanel` 整块是死代码；`moveGroup` 每帧调用会让 Batch 333 的
持久化订阅每帧写 localStorage（既有行为）。

**候选 Batch 342**：`FrameosNodeEditPanel` 的「复制节点 / 锁定位置」是否也是
空壳？debug UI 无入口是否意味着整块该删或该接线。

## Batch 342（2026-10-01）：节点搜索「点击结果聚焦」用错坐标系（+ 一个否定结论）

`FrameosNodeSearch.focusNode()` 把 `getBoundingClientRect()` 的**屏幕坐标**喂给
`useReactFlow().setCenter()`，后者要的是**画布流坐标**。

实测（视口改成 `translate(400,260) scale(0.5)` 模拟用户缩放/平移）：
点结果后目标节点 `video-1` 落在屏幕 **(1272, −66)** —— 中心比视口顶边还高
66px，**节点被推出屏幕**，与组件注释声明的「把视野缩放聚焦到它」正好相反。
**选中对了、缩放 2.73 也对了，只有聚焦是错的。**

修：用 `position + 尺寸/2` 调 setCenter。修复后同一场景 (800, 475)，dx=dy=0。

🔑 为什么之前没发现：**默认视图下几乎不可见**（屏幕坐标与流坐标只差一个画布
内边距，量出来「差不多居中」就过去了）。所以验证器**先用真实手势把视口弄成
非默认状态**（点 3 次缩小 + 空白处拖拽平移），并把「前置已扭曲」本身作为一条
断言 —— 没有它，居中断言会在旧代码上**假通过**。

变异测试：改回屏幕坐标后失败于 `focus:centered`
（`node center=(547,-38)`，又一次出屏）。

同批**否定结论**：Batch 333 持久化订阅**每帧**写 localStorage（拖分组时
`moveGroup` 每帧触发）——结构问题属实，但实测 7 节点 0.025 ms/帧、
287 节点（载荷 3 KB→111 KB）也只 0.11 ms/帧，**远低于 16 ms 帧预算，不修**。
「每帧写 localStorage 听起来很糟」在没有实测前不能当缺陷来修。
探针与数字留档，供画布体量增长时重新评估。

写验证器时踩的坑：点搜索结果**不会**关闭面板（组件注释即声明「× / Esc 关闭」），
我在第二段又点了一次 toggle 把面板关掉了 → `fill` 超时，一度误判成应用缺陷。
**验证器失败先看失败在哪一步。**

verifier batch342 **10/10 PASS**。

**候选 Batch 343**：`FrameosNodeEditPanel` 的「复制节点」「锁定位置」两个
ActionButton 无 onClick（空壳），且整面板只在 `isDebugMode` 下渲染而
`toggleDebugMode` 全仓无 UI 入口 —— 属源站对齐问题，先记录；
另有 `generations` 死状态字段可清理。

## Batch 343（2026-10-01）：边完整性不变式（与 341 同构）+ 持久损坏的放大

边有一条和分组完全同构的不变式 ——「每条边的两端都指向存活节点」—— 而剪边
**只存在于 `removeNode` 一处**。`setNodes` 是公开 action，面板删除正是
`setNodes(nodes.filter(...))`。

实测（修复前）：
```
[对照组 removeNode] edges 5 → 3, dangling=[]            ← 剪了
[路径   setNodes]   edges 3 → 3, dangling=[2 条]        ← 没剪
  .react-flow__edge 渲染数: 0                            ← 渲染不出来
持久化里的悬空边: 2 条    刷新后 dangling: 仍在
```

🔴 **关键放大效应**：Batch 333 的持久化订阅把这些悬空边写进了 localStorage 且
**跨刷新存活** —— 内存里的潜在缺陷被**固化成了持久损坏**。React Flow 一条都
渲染不出来，所以用户看不见；**看不见的损坏比看得见的错更危险**，它会累积且
没有自愈路径。

同一路径还有第三个问题：`setNodes` 是 `set({ nodes })`，**不 pushHistory** →
面板删除**不可撤销**。也就是说面板把手写了一遍 `removeNode` 已有的一切语义
（剪边/入栈/清选中），还少了三样。

修 1：`enforceGroupGeometry` → **`enforceGraphInvariants`**，同��出口再收一条
不变式。副产品：**已写坏的存档会被治愈**（`restorePersistedCanvas` 也经过这里）。
修 2：面板改用 `removeNode` —— **删代码而不是加代码**，与 328/341 同方向。

变异测试：注释掉边收敛后验证器失败于 `setNodes:no-dangling`。
写验证器时把 `reload:nodes-restored` 的基准从「初始 7 个节点」改成「刷新前快照」
—— 断言要绑**真实性质**，不绑一个会过期的常数（Batch 208 教训，第二次用上）。

verifier batch343 **13/13 PASS**。

**候选 Batch 344**：`generations` 是死状态字段（从未写入也从未读取）；
`FrameosNodeEditPanel` 两个空壳按钮 + 整面板无入口（属源站对齐，阻塞）。

## Batch 344（2026-10-01）：分组右键菜单「删除」弹绿色成功提示却什么都没删

`FrameosGroupCanvas` 的分组右键菜单，「删除」项此前只是
`showToast("已删除分组 (mock)", "success")`。

实测（修复前）：
```
菜单项: ['复制\n⌘C', '创建副本\n⌘D', '删除\n⌫']
[点「删除」] groupCount=1 hasGroup=True DOM 分组盒=1   ← 组还在原地
[按 ⌫]      hasGroup=True groupCount=1 pastDepth=1     ← 毫无反应
```

第二个缺陷：菜单把 ⌫ 标成快捷键，但 `page.tsx` 的 Delete/Backspace 分支
只认 `selectedNodeId` —— 纯选中分组时按 ⌫ 什么都不发生。**菜单上写着的
快捷键必须能用。**

🔑 为什么这条比「两个死按钮」严重：死按钮点了没反应，用户一眼就知道不对；
这一条是**主动撒谎** —— 绿色对勾 +「已删除分组」+ 组仍在原地，用户会以为
删掉了、继续操作，直到某天发现它还在，而中间的判断已基于错误前提。
**一个会撒谎的 UI 比一个明显坏掉的 UI 更危险**：坏掉的让人停下，撒谎的让人
继续往下走。

修 1：「删除」改用 store 已有的 `ungroup`（工具条「解组」同一个 action，
自带入栈 + 清理 selectedGroupId），并且**不发 toast** —— 组从画布消失本身
就是反馈，比一条可能不兑现的文案诚实。
修 2：Delete/Backspace 补 selectedGroupId 分支（节点优先，Batch 177 语义不变）。

⚠️ CLONE_DECISION：「删除分组」也可能读作「连成员一起删」。那是破坏性操作、
需二次确认，源站**未采样**（阻塞）→ **不擅自发明**，本次取非破坏可撤销的读法，
注释里写明日后若源站确认是另一种读法只需改这一处。
`复制`/`创建副本` 仍是 mock：源站确认了**条目存在**（SOURCE_FACT）但没采样
**做什么**，要实现就得发明语义（如副本组是否与原组共享成员 → 会打破
「一节点一组」模型）→ 不动，记录在案。

变异测试：改回 `showToast("已删除分组 (mock)")` 后验证器失败于
`delete:group-gone-from-store (hasGroup=True)`。

verifier batch344 **15/15 PASS**。

**候选 Batch 345**：`FrameosGroupCanvas.tsx:236`「批量连线 (mock)」同类未实现；
`generations` 死状态字段；`FrameosNodeEditPanel` 两个空壳按钮（后者属源站对齐，阻塞）。

## Batch 345（2026-10-01）：⌘Z/⌘⇧Z 谎报成功（+ 一个让它「无法被测」的元缺陷）

`page.tsx` 的 ⌘Z 分支此前是 `undo(); showToast("已撤销", "info");`，而 `undo()`
在 `past.length === 0` 时**直接 return，什么都没做**。

比 344 更容易撞上：Batch 333 刻意**只持久化内容不持久化历史** → **每次刷新后
撤销栈必然为空** → 刷新后的第一次 ⌘Z 必然撒谎。

修复后实测：空栈 ⌘Z →「没有可撤销的操作」；真撤销 →「已撤销」且 nodes 8→7。

🔑 **元缺陷：这条谎此前根本无法被测出来**。第一次跑探针 toast 数组恒为 `[]`
—— 不是缺陷不存在，是**抓不到**：`FrameosToast` 的元素只有内联样式、**没有任何
标识属性**，而 toast 文案正是「UI 是否谎报」的**唯一证据**。
也就是说在补标识之前，即使有人想写验证器也只能写成空断言 —— 而空断言正是
Batch 336 门禁要清理的东西。**可测性和缺陷同等重要：测不了的东西，坏了也
没人知道。** 修：加 `data-frameos-toast` / `-variant`，与仓库既有
`data-frameos-*` 约定一致。

修：`undo()`/`redo()` 由 `() => void` 改 `() => boolean` **如实报告是否真的执行**；
调用方据此选诚实文案。tsc 全绿证明**无其它地方依赖旧 void 返回**。
顺带修掉更隐蔽的一条：Batch 331 的跨画布拒绝会 `set({past:[],future:[]})`
却**什么都没撤销** —— 此前那条路径也照样弹「已撤销」，而它同时**清空了整条
撤销历史**。现在返回 `false`，不再谎报。

验证器把**文案**与**数据变化**绑在一起断言（只验文案仍可能是一句空话）：
「已撤销」必须伴随节点数真的减少。**断言要绑真实性质。**

变异测试直接复现缺陷原文：`toasts=['已撤销']`（空栈时）。

verifier batch345 **15/15 PASS**。

**全仓同类扫描**：frameos 目录剩余 `showToast` 全部带 `(mock)` 字样（已复制分组/
已创建分组副本/批量连线/已存为模板/已设置为资产图），性质与 344 的「假装成功」
不同 —— 它们自认是占位符。**真正的假成功已全部处理。**

**候选 Batch 346**：`generations` 死状态字段；`FrameosNodeEditPanel` 空壳按钮
（源站对齐，阻塞）。

> 插曲: 写「toast 可寻址」断言时我图省事写了 `count() >= 0`，被 **Batch 336 的
> 恒真断言门禁当场抓出**（`[VACUOUS_COUNT] count() >= 0 恒真`）。这是本会话门禁
> **第一次抓到我自己新写的代码** —— 门禁对自己人一样有效，这正是它值得存在的原因：
> 写断言的人和审断言的人不是同一个视角。已改为真实性质（count>=1 + 文案一致 +
> variant 暴露）。

## Batch 346（2026-10-01）：兑现「双击节点聚焦填满视口」+ 一次被我推翻的错误修复

🔴 **本批最重要的一条：我一开始做错了，而且做错的方式很典型。**

初版修复：把帮助面板那两行改写成三行精确描述，并**删掉**「双击空白处添加节点」，
理由是「帮助面板不该承诺 app 做不到的事」。全量套件跑完报
**batch183 FAILED: help:verbatim-rows**。

翻 batch183 源码，它锁的是 `HELP_ROWS = ["双击空白处添加节点", …,
"双击节点聚焦填满视口", …]`，docstring 明写「**new-source-version drift lock**
… help panel **26 verbatim shortcut rows**」。

**这些字符串是源站帮助面板的逐字转录**（2026-09-24 源站新版本重新采样），
即 **SOURCE_FACT**，不是克隆自己的措辞。

所以我当时的「优化」等于：**为了让克隆的内部一致性论证好看，去改写源站事实的
转录**。克隆的职责是复现源站；做不到时正确动作是**如实记录差距**，不是把差距
从证据里抹掉 —— 删掉一条逐字源站原文来赢一场内部一致性争论，是**最坏的一种
「修复」**：它让文档不再能被用来发现差距。

已全部回退：帮助面板文本**逐字不动**（`data-frameos-help-*` 属性保留，纯增量）。
保留的只有 `onNodeDoubleClick` 实现。

> 这次能抓回来，靠的正是 batch183 那个漂移锁。**断言的价值不在于它今天通过，
> 而在于它能在你「顺手优化」的时候把你拦下来。**

其余发现（仍然成立）：

- 「双击节点聚焦填满视口」在克隆里**从未实现**（页面无任何双击 handler）。
  已实现 `onNodeDoubleClick` → `fitView`。**必须显式给 min/maxZoom** ——
  `fitViewOptions` 把缩放钉死在 1，不覆盖就退化成「什么都不动」。
- 逐节点类型实测才发现：文本节点双击**进编辑**(`FrameosTextNode:34` +
  stopPropagation)、视频节点双击**预览**(`FrameosVideoNode:119`)，双击**到不了**
  聚焦；只有图片等冒泡。源站是否如此**需采样确认**（已记为待核）。
- 「双击空白添加节点」：源站逐字承诺、克隆未实现。承诺没说添加**哪一种**，而
  工具条是带类型选择的菜单，选默认类型就是发明 → 记为**保真度差距**
  （原文留着、差距记着），不发明、不删。

🔑 元缺陷第二次重演：帮助面板行也无可寻址属性（与 Batch 345 toast 同款）。
已加 `data-frameos-help-row/-label/-desc`，**纯增量不碰文本**。
**同一个坑两个批次连踩两次** —— 「补可测性」该是新增 UI 元素时的默认动作。

变异测试：撤掉 `onNodeDoubleClick` → 失败于 `image:dblclick-focuses`。
写探针时踩自己的坑：循环会移动视口，后续步骤沿用旧坐标会点到空气
（误报 enters_edit=false）。**验证失败先看失败在哪一步**。

verifier batch346 **24/24 PASS**；batch183 恢复 PASS。

**候选 Batch 347**：`generations` 死状态字段；`FrameosNodeEditPanel` 空壳按钮
（源站对齐，阻塞）；「双击空白添加节点」与「双击节点聚焦」对文本/视频是否成立
—— 均待源站可采样。

## Batch 347（2026-10-01）：交互盲区清零 + 变成门禁

Batch 345（toast 无标识）与 Batch 346（帮助面板行无标识）是**同一个元缺陷踩了两次**。
两次就是模式：「记得加测试钩子」不是可靠流程。

运行时普查（修复前）：
```
[default] 可点元素 38  有稳定钩子 34  盲区 4  (11%)
盲区样本: '下载桌面端' / '测试作品' / '测试项目' / '画布 1'
```
**三个核心导航控件 + 一个头部按钮，恰恰是测试最需要寻址却唯一没法寻址的东西。**

🔑 **方法论纠正**：静态扫源码时我数出「7 组件 81 个交互元素零 data 属性」，看着像
笔大账。**运行时测量才是真的** —— 那些按钮大多有 `aria-label`（342/346 我正是用
`button[aria-label="搜索节点"]` 选中的），盲区只有 4 个。
**差点按错误量级去改一片代码。** 静态扫描会高估欠账。

修：`Crumb` 共用渲染函数加 `data-frameos-crumb={label}`（一次覆盖三个面包屑）；
「下载桌面端」加 `data-frameos-download-client`。后者**仍是 mock**（源站外部下载
地址未采样 → 不发明），但**可寻址必须做到** —— 正因为将来可能出问题才要能抓到。

**本批真正的产出是门禁**：验证器在三种 UI 态（默认/帮助面板/选中节点）枚举所有
可点元素，任何缺稳定钩子（无 data-*/aria-label/id/title）者**失败并指名**。
以后新增 UI 忘加钩子，套件当场指出，而不是等某个验证器写不出来才发现。

门禁自带防假绿断言 `scan:not-empty`（要求扫到 ≥20 个元素）——
**「扫到 0 个元素」和「0 个盲区」在断言里长得一样**，必须分开断言。

verifier batch347 **12/12 PASS**；变异测试撤掉 crumb 钩子 → 门禁 FAIL。

**三条方法论沉淀**：
1. 元缺陷踩两次就该变成门禁（一次是意外，两次是流程缺陷）；
2. 静态扫描会高估欠账，运行时测量才是真的；
3. 门禁必须防假绿。

**候选 Batch 348**：`generations` 死状态字段；`FrameosNodeEditPanel` 空壳按钮
（源站对齐，阻塞）；盲区门禁若需豁免机制则加显式白名单。

## Batch 348（2026-10-01）：「双击空白添加节点」是半成品接线 —— 事件接了，菜单没渲染

`page.tsx:188` 的注释就是证据：「双击空白处打开「选择节点类型」菜单 (Batch 168)」。
事件半边**早就接好了**（pane 的 dblclick、跳过节点、记录坐标到 `paneMenuAt`），
但 **`paneMenuAt` store 外零引用** → 双击空白处什么都不会出现，**Esc 还关不掉**。

实测（修复前）：
```
[双击后] paneMenuAt={'x':140,'y':140}  出现「选择节点类型」=False
[Esc 后] paneMenuAt={'x':200,'y':180}  ← 关不掉
HALF_WIRED: true
```

🔑 **本批修正了 Batch 346 的判断错误**：346 把这条记为「保真度差距」，理由是
「承诺没说添加哪一种，选默认类型就是发明 → 不发明」。**这个推理是错的** ——
Batch 168 的设计**已经回答了**（要一个「选择节点类型」**菜单**，用户自己选）。
所以不是「无法实现」，而是**「做了一半」**。

> **教训**：把功能记为「没证据、无法实现」之前，先查是不是**已经有半成品实现
> 把答案写好了**。半成品的存在本身就是强证据。「我不能发明」和「我不能凭空
> 发明」是两回事。

修：① 新增 `FrameosPaneAddNodeMenu`（缺失的渲染半边），类型列表**复用工具条
导出的 `NODE_TYPES`**（同一事实只该有一个出处）；② `AddNodeOpts` 加可选
`position`（**流坐标**）—— 此前 `addNode` 只能放视口中央或随机，用户在哪儿双击
就必须在哪儿出现；③ Esc 链补 `paneMenuAt`。

verifier batch348 **24/24 PASS**；变异测试摘掉组件 → FAIL。
实测节点屏幕中心 (140,142) vs 双击点 (140,140)，**误差 2px**。

写探针时踩了两个坑(都是探针自己的问题): ① 遮罩点击超时 —— 因为上一步刚在那个
坐标加了节点, 第二次双击落在**节点**上(双击节点不弹菜单是**正确行为**);
② Playwright `position` 字典误写成 `{"height":700}`。
**验证失败先看失败在哪一步** —— 这条纪律本会话第三次派上用场。

**死状态普查副产品**（`FrameosCanvasState` 78 个成员，store 外零引用只有 3 个）：
`paneMenuAt`（本批修好）/ `generations`（从未写从未读）/ `toggleDebugMode`
（store 外零调用）。
> 先前我用粗糙正则数出「16 个死成员」——**错的**（`selectedNodeId`/`setNodes`
> 明明在用）。换成直接计数才是真实的 3 个。**测量方法本身要先验证**，
> 否则会拿着错误的量级去改代码。

**候选 Batch 349**：`generations` 死状态清理；「双击空白添加节点」菜单视觉与源站
一致性（采样阻塞）；用死状态普查法审 jimeng/director 各自的 store。

---

## Batch 349 — 生成完成提示重复派发 11 次 + 删死状态字段

commit: (本批)
性质: **CLONE_DECISION**（克隆侧；源站人机验证仍被拦，无一条源站采样）

### 缺陷一（用户可见）：一次生成弹出 11 条一模一样的「生成完成 ✓」

`FrameosGenerationOverlay` 的 tick 由 `setInterval(tick, 50)` 驱动，而收尾
`setTimeout(..., 500)` 写在 tick 里、**且 `p>=100` 之后 interval 不停** ——
于是收尾窗口内**每个 tick 都排一个收尾 timeout**。第一个 timeout 把
`currentGeneration` 置 null 触发清理，但它之前排下的那些仍会陆续触发，
**每个都 dispatch 一次 `frameos-toast`**；`showToast` 不去重、逐条堆叠。

静态推算 500ms/50ms ≈ 11；**探针在真实 30 秒 mock 下实测 11 条**（`dom_done_toast_count=11`），
推算与实测逐一对上。

修：effect 体内加 `finished` 闩锁 + 进入收尾即 `clearInterval`。
闩锁是局部变量而 effect 依赖 `currentGeneration`，所以**每次新生成天然拿到新闩锁**
—— 验证器专为此断言了「第二次生成也要提示」。

> 顺带：进度跑满后不再每 50ms 触发一次 setProgress/setNow（每秒 20 次渲染）。

### 缺陷二：`generations` 死状态字段已删

普查（`scripts/_deadstate_census.py`，临时工具未入库）扫 `FrameosCanvasState` 的
**33 个数据字段**的 store 外读取点 —— **只有 `generations` 是 0**，
且 store 内只有「声明 + 初值 `[]`」两处，从无任何读写。`src/` 与 `scripts/` 均零引用。

留着它等于用注释承诺一个「生成任务列表」功能，对下一个维护者是**文档性谎言**。
要不要「生成历史」是产品决定，源站未采样，**不发明**。

### 验证

verifier batch349 **9/9 PASS**、0 诊断。**两次变异测试都确认验证器会红**：
① 去掉闩锁+停表 → `r1:one-done-event got=11`（数字等于缺陷原文）；
② 加回 `generations` → `store:generations-field-removed has=True`。

**mock 时钟压到 2s**：机制与时长无关（重复次数只取决于 p>=100 后的 500ms 窗口），
变异测试在 2s 下同样复现 11 条，反过来印证；真实 30s 证据留在探针。

### 两次「变异测试自身的坑」

① 第一次变异只去闩锁、**却保留了 `clearInterval`** —— interval 照样停、缺陷没恢复，
**验证器照常通过**。
> **一次「变异测试通过」毫无意义，除非先确认变异真的移除了被测性质**；
> 变异不到位比不做变异更危险，因为它给的是虚假信心。
> 这次靠「报错里的数字必须等于缺陷原文的 11」才看穿 —— 只看到 PASS 就会把
> 这批的验证证据当成废纸。

② 第二轮数出 2 条，排查确认是**测量脚手架造的缺陷**：`INSTALL_SPY` 每轮都
`addEventListener` 且不清旧的，一次派发被两个监听器各推一遍。
修法：监听器只装一次 + 游标切分。
> 这是本会话**第四次**「先看失败在哪一步」救下误改应用代码
> （前三次：346 探针坐标失效、348 探针复用已有节点、Playwright `position` 笔误）。

### 顺带记录（未修，非缺陷）

- **生成流程在 demo 首屏完全不可达**：7 个 fixture 节点全是 text 或带 `imageUrl` 的
  image/video，`FrameosPromptEditor` 对它们一律 return null。必须先加一个
  「无媒体内容的生成节点」才够得着生成按钮。
- **Batch 347 的可寻址性门禁普查不到生成按钮**：`FrameosGenerationOverlay`
  整个没有任何 `data-frameos-*` 钩子，门禁在三种 UI 态里都没触达过它。
  门禁的边界是「**普查所及范围内**零盲区」，不是「全 app 零盲区」。

**候选 Batch 350**：`toggleDebugMode` 零调用（batch348 普查发现，本轮普查
只覆盖数据字段未覆盖 action）；用同一普查法审 jimeng/director 各自的 store；
「双击空白添加节点」菜单视觉与源站一致性（采样阻塞）。

---

## Batch 350 — 裁剪表单静默丢弃用户输入 + batch333 偶发失败真因(门禁缺陷)

性质: **CLONE_DECISION**（克隆侧；裁剪的**提交语义**源站未采样）

### 缺陷一: 裁剪是「接受输入并静默丢弃」的表单

`FrameosNodeFloatingToolbar` 裁剪态(Batch 279 采样的是 UI 外观)里:
宽高是 `<input defaultValue={480}>` 的**非受控**输入, 全仓**没人读过**;
「✓ 确认裁剪」只 `alert("已确认裁剪 (mock)")` + 退出裁剪态;
裁剪框恒等于节点当前矩形, 8 手柄全是 `pointerEvents: none`(拖不动)。

→ 用户填的数字被整个丢弃, **节点一点没变**, UI 却弹了确认。
比普通 mock 更坏: mock 是「本来没做」, 这里是**收了输入、给了确认、再扔掉**。

修(不新增 store API, 不发明裁剪语义):
① 宽高受控, 进入裁剪时用**节点当前尺寸**初始化(不是写死 480);
② 裁剪框跟随输入, 锚在节点左上角;
③ 确认时复用**拖拽手柄用的同一对** action —— `beginResize`(入历史) + `resizeNode`(落尺寸)
   → 不新增 API、自动可撤销、与全 app 历史语义一致;
④ 最小值沿用手柄同一对下限 200×120;
⑤ 解析不出数字就**不落也不谎报成功**;
⑥ `nodeRect` 是屏幕坐标而宽高是流坐标 —— 显式换算(Batch 342 同源陷阱)。

实测: 300×169 → 确认 420×260 → ⌘Z 精确还原 300×169。

verifier batch350 **14/14 PASS**、0 诊断。**两处变异都确认会红**且数字即缺陷原文:
① 去掉 `resizeNode` → `confirm:applies-size style=(300,169) expect=(420,260)`;
② 退回 `defaultValue=480` → `input:initialized-from-node input=(480,480) style=(300,169)`。

**探针自身的坑(第五次)**：`undo:restores-size` 曾报 `(None,None)`, 像是「撤销把节点删了」。
实测撤销**精确还原了** 300×169, 只是 `selectedNodeId` 变 null —— 而 `undo()` 里
`selectedNodeId: null` 是**有意的显式设计**(快照恢复丢选中), 不是缺陷。
探针改为**按 node id 读**(稳定身份), 并把「还原尺寸」与「节点还在」拆成两条断言。
> 本会话累计五次因「先看失败在哪一步」避免误改应用代码
> (346 坐标失效 / 348 复用已有节点 / Playwright position 笔误 / 349 监听器重复注册 / 350 按选中态取节点)。

### 顺带查清: batch333 反复偶发失败的真因是**门禁缺陷**

`diagnostics:zero` 连续三轮在全量套件里失败、重试也失败, 但**隔离 5+ 次、
6 路并发 3 次、重编译扰动 3 次全过**。前两次抓诊断失败是因为 runner 对失败输出
做 `tail -5` 把诊断截掉了; 改成**写文件**才抓到原文:

    requestfailed:GET:.../_next/static/chunks/[turbopack]...hmr-client...js:net::ERR_ABORTED
    requestfailed:GET:.../images/frameos/node-vid-cover-2.jpg:net::ERR_ABORTED

**全是 `net::ERR_ABORTED`** = 浏览器**主动取消**的请求, 不是服务器/应用失败:
① Turbopack HMR chunk(别的 session 改源文件触发重编译, 旧 hash 失效);
② `/images/frameos/*`(batch333 密集 `page.reload()` 测跨刷新持久化, 图片请求随导航被取消)。

`attach_errors` 把浏览器 `requestfailed` 一律当应用错误 → `diagnostics:zero`
在长跑/并发下必然误报, 还会淹没真实错误。
**batch333 本身无功能回归**(11 次隔离/压力跑全过); 问题在门禁分不清
「应用抛错」与「HMR chunk 被取消」。门禁必须零误报 → 要修。

**候选 Batch 351**: 改共享 `attach_errors`, 不把 `net::ERR_ABORTED` 计为应用错误,
并配「门禁没被削弱」的反向测试(注入真 console.error / pageerror / 404 仍须失败);
影响 86 个验证器, 故单独成批。

---

## Batch 351 — 门禁分不清「应用抛错」与「浏览器中止的请求」

性质: 验证基础设施修正(不涉及产品行为)。**CLONE_DECISION**

`batch333 diagnostics:zero` 连续三轮在全量套件里失败、重试也失败, 但同一份代码
**隔离 5+ 次 / 6 路并发 3 次 / 重编译扰动 3 次全部通过**。三轮套件首轮挂的批次还
各不相同(171/172/221/327/333、208/209/333、216/220/221/327/333), 但 batch333
三次都在、失败点始终是 `diagnostics:zero`。

**抓证据失败两次, 这条经验值得单独记**:
① 第一次在失败前 `print` 诊断 → 被 runner 的 `echo "$out" | tail -5` **截掉**;
② 改成**写文件**才拿到原文。
> 门禁失败时能看到的信息恰恰最少。**诊断必须写到不会被截断的地方**。

原文**全是 `net::ERR_ABORTED`**(浏览器**主动取消**, 不是服务器/应用失败):
Turbopack HMR chunk(别的 session 改源文件触发重编译) + `/images/frameos/*`
(batch333 密集 reload 测跨刷新持久化)。

**一个必须先查清的细节**: 抓到的条目**没有 `console:error:` 前缀** → 它们不来自
共享的 `attach_errors`, 而是 batch333 **自己内联**的 `requestfailed` 监听器
(第 99-102 行)。所以要收口**两处**, 只改共享函数不够。

修: `is_dev_server_noise()` 放共享模块作**单一出处**, 两处监听器都用它。
判据用「**中止**」而非路径白名单 —— 被中止的请求不携带任何服务端/应用健康信息
(应用自己 AbortController 取消的同理); 404/500/连接失败**不是** ERR_ABORTED, 照旧计入。

**这是反向测试**: 重点是证明门禁**没被削弱**。verifier 15 项、0 诊断, 逐条断言
真 `console.error` / 未捕获异常 / 404 **必须仍被抓到**。
另有两条防假绿自检: 干净起点错误列表为空; 且**另挂不经过滤的原始监听器**做对照,
确认 ERR_ABORTED 事件真的发生过。

**双向变异测试**(门禁改动必须两个方向都测):
| 变异 | 结果 |
|---|---|
| A 撤销过滤(`return False`,=修复前) | 红 `pure:hmr_chunk_aborted is_noise=False want=True` |
| B **过滤过头**(`return True`,真错误也吞) | 红 `pure:not_found is_noise=True want=False` |
> 只做 A 只能证明「测试抓得住没修」, 抓不住「修过头把门禁掏空」。

**防假绿自检自己也写错过**: `anti-false-green:abort-really-happened` 首跑 saw=0 ——
我试图用页内 `console.error` 猴补丁抓原始事件做对照, 但 `requestfailed` 是
**浏览器**发出的、不经过页面 `console.error`, 对照恒为空, 于是「被过滤」成了空断言。
改用独立的原始 `requestfailed` 监听器(同一事件、两个收集器)后才有真对照。
> **防假绿自检失败时要先怀疑自检**, 而不是相信「那大概是个 bug」。

影响面: `attach_errors` 被 86 个 frameos 验证器共用; 收窄的只是「浏览器中止的请求」,
其余全部照旧, 由反向测试逐条兜住。

**候选 Batch 352**: Batch 347 的可寻址性门禁只普查了三种 UI 态, 没触达
`FrameosGenerationOverlay`(整个组件零 `data-frameos-*`) —— 把门禁的 UI 态覆盖面
扩到「主面板/裁剪态/分组态/空画布」, 或给覆盖层补钩子; 死状态普查推广到
canvasStore/directorStore(8709 行, 本轮只扫了 frameos 与 jimeng)。

---

## Batch 352 — 死状态普查改用真 AST; 5 个 store 全扫; 记录一处跨线发现

性质: 工具质量(不动产品行为)。**CLONE_DECISION**

**为什么要重写工具**: Batch 349 的普查工具是正则实现, 推广到别的 store 时先后暴露
**5 类误报**, 每一类都差点让人把活字段当死状态:
1. 多行函数签名的**参数**被当字段(jimengStore `applyTrim` 的 `trimmedDuration`);
2. **解构**读取被漏(`const { groupNames } = useJimengStore.getState()`; 且 hook 真名
   `useJimengStore` 与文件名 `jimengStore` 之间**没有词边界**, `\bjimengStore\b` 永远匹配不到);
3. 多行 action 的**首行** `foo: (` 像字段(canvasStore `addNodeAtFlowCenter` 等 3 个);
4. 多行**解构**里字段单独占行(canvasStore `removedCanvases` / `historyByCanvas`);
5. 用「第一个 `\n}`」切接口 body 太天真(canvasStore `cohortId` 等 —— 扫进了邻近接口)。

> 继续打补丁是错的方向: 误报率这么高的工具留在仓库里, 每次都会产出
> **看起来很确凿的假线索**。改用 TypeScript 自己的 AST(仓库已有 5.9.3), 5 类归零。
> **测量方法本身要先验证** —— 这次是用真实编译器 AST 验证的。

**全量扫描**: frameosStore(33 字段)/canvasStore/jimengStore **均无死状态**;
`uiStore` 30 字段里有 **4 个真候选**; directorStore(8709 行)本轮未扫。

**跨线发现(只记录, 未改)**: `uiStore` 的
`isToolboxPanelOpen`/`isMaterialPanelOpen`/`isCharacterPanelOpen`/`isHistoryPanelOpen`
及各自 `toggleXxxPanel` **都零调用**; 而 `LeftSidebar.tsx:128-141` 是用
`activePrimaryPanel === "toolbox"` 驱动这些面板的 —— 那 4 个 boolean 是
`activePrimaryPanel` 重构前的**遗留旧机制**, 不可达且是陷阱(谁调用 toggle 都不会有反应)。
**不改**的理由: `uiStore` 属 liblib/jimeng 主应用, 不在帧界画布这条线上, 而那条线
此刻有并行 session 作业; 按「不干扰他人工作」+「不擅自跨线改动」, 只记录。
要清由该线作者连同其验证器一起清。

**未完成**: directorStore 未扫; 普查**仍不宜门禁化** —— 层 B 判据是
「initializer 提到 store 名」, 理论上仍可能漏间接引用(把整个 store 传给别的函数再解构),
真要门禁化需先为这些形态各造「已知活着」的样本做反向测试。

**候选 Batch 353**: Batch 347 的可寻址性门禁只普查三种 UI 态, 没触达
`FrameosGenerationOverlay`(整个组件零 `data-frameos-*`) —— 扩门禁覆盖面或补钩子;
继续找「UI 撒谎」类缺陷(裁剪那一条挖完后, 还剩 FrameosTemplatePanel 模板应用、
FrameosWorkspaceNode 目标工作台页等 mock)。

---

## Batch 352 续 — 「480×480」不是源站常数: 查一手采样定案

全量回归跑出 batch279 失败: `crop:size-inputs-480` —— 正是 Batch 350 改掉的那处。
**先查一手源站记录再决定**, 找到 `docs/research/liblib-frameos-batch278-2026-09-28/CROP_OBSERVATIONS.md:11`:

> - [480] x [480]（两个 42px 宽的数字输入框，**裁剪区当前尺寸**）

→ **480 是采样当时那个裁剪区的「当前尺寸」，不是源站写死的常数**;
观测者自己标注的就是「裁剪区当前尺寸」。

于是定案:
- 克隆侧此前把**观测值当常数**抄成 `defaultValue={480}`, 并用 batch279 的
  `crop:size-inputs-480` 把这个字面化**钉死** —— 输入框永远显示 480、与节点实际
  尺寸无关、改了也不生效(Batch 350 修的就是这个);
- Batch 350 的改法(用节点当前尺寸初始化)**正是源站行为**, 不是发明;
- batch279 的断言钉的是**克隆的缺陷**, 已改为 `crop:size-inputs-are-current-size`
  (校验输入框 === 节点流坐标尺寸), 并在断言处引用一手采样出处。

**这正是 Batch 346 的镜像情形, 但结论相反**:
346 我删了源站逐字原文去换内部一致(错, 被全量套件抓出);
352 我手里有**一手源站观测**, 证明「480」是克隆对观测值的**字面化**而非源站性质,
所以是让克隆去匹配源站的**事实**(当前尺寸), 而不是匹配克隆的**字面化**。
> **纪律**: 遇到「我的改动撞上了旧断言」, 第一动作是**去找一手证据**,
> 而不是直接改断言 —— 也不 reflexively 改断言。证据在手, 才有资格说谁对。

同时给 `BEHAVIORS.md:141` 与 `IMPLEMENTATION.md:201` 两处记着 `480×480` 的地方
**加注**(不是删除采样记录): 说明 480 是采样当时尺寸、现已按当前尺寸初始化。

`CROP_OBSERVATIONS.md:15`「确认裁剪未点击(避免任何应用/生成消耗)」也再次确认:
确认语义**源站未采样** → Batch 350 复用 `beginResize`+`resizeNode` 而非自造裁剪
语义, 标 CLONE_DECISION 是对的。

变异测试: 宽高退回 `defaultValue={480}` → batch279 红 `crop:size-inputs-are-current-size`。

---

## Batch 353 — 可寻址门禁的覆盖面从 3 态扩到 8 态

性质: 可测性基础设施(不改任何交互行为)。**CLONE_DECISION**

Batch 347 把「交互盲区清零」做成了门禁(运行时枚举所有可点元素, 缺钩子就红),
但**门禁自身有边界而没人把它当约束**: 它只普查 3 态(默认/帮助开/选中节点),
于是这 3 态碰不到的东西全部逃过检查 —— 裁剪态、分组态、节点搜索面板、模板面板,
以及 `FrameosGenerationOverlay`(**整个组件零 `data-frameos-*`**)。
Batch 349/350 的记录里都写了「门禁没触达生成浮窗」, 但没变成约束。

探针先量欠账(与门禁同一把尺子): group 态 **3 个盲区**(整组执行/存为模板/解组)、
generation 态 **2 个**(取消按钮 + 一个 prompt textarea); crop/node_search/template 全 0。

补 8 个钩子(分组工具条 3、生成浮窗 2、PromptEditor 4 个 textarea 全部),
5 个新态归零, 并把 5 个新态**并入门禁**: batch347 从 9 项检查扩到 **21 项**,
每个新态都带 `scan:not-empty:<态>` 防假绿自检。
变异测试: 摘掉「解组」钩子 → 红 `blind:group-zero 盲区 1/45: [{'tag':'button','text':'解组'}]`,
报错精确指名元素。

**过程中的三个坑(都值得记)**:

1. **JSX 开始标签的属性区里不能写 `//` 注释** —— 会让整页编译失败、节点一个不渲染,
   而 `tsc` 报错全在 `.next/dev/types/routes.d.ts` 这个生成文件里, **看不出是自己写的**。
   注释必须放在开始标签**外面**。
   > 页面突然 404/500 先怀疑最近的 JSX; `tsc` 报的生成文件错误是噪音, **要过滤 `.next/` 再看**。

2. **一次 grep 的输出被我自己的 `head -30` 截断** —— 只看到 3 个 textarea 就以为补齐了,
   实际有 **4** 个, 漏的正是**用户看到的常态面板**那个; 而且两个 placeholder 完全相同,
   靠 grep 上下文分不出来, 最后靠运行时枚举每个元素的 `data-*` 才定位。
   > **别截断自己正在用来做判断的证据。** 需要「全都看到」时就要真的全都看到。

3. **dev server 反复 404/崩溃, 把排查带偏两次** —— 500 的真凶是**另一个 session
   正在改的** `DirectorDesk.tsx`(JSX 未闭合), 等 ~90s 后他自己修好了。
   处置: 属他人进行中的重构就**不猜他的结构意图、不抢同一文件**, 等他收尾;
   路由全 404(含 `/`)说明 `.next` 缓存不一致 —— `rm -rf` 被安全策略拦, 改用
   `mv` 挪到 `/tmp`(挪出仓库、**未删除**)。
   > `.next` 被 git 忽略**不代表** `.next.corrupt-xxxx` 也被忽略(实测会冒进 git status)。

**遗留边界**: 门禁覆盖 8 态但仍是**枚举式**的 —— 未覆盖的态(全屏编辑态/资产面板/多选态)
仍可能藏盲区。根治是让「缺钩子」在 lint/类型层面就报错(自定义 ESLint 规则), 另一量级。

**候选 Batch 354**: 把可寻址门禁推广到 **jimeng / liblib 画布**(同一套约定已在
frameos 落地, 另两条线尚未普查); 或用同样「先探针量欠账再改」的方法去审
全屏编辑态与资产面板这两个尚未进门的态。

---

## Batch 354 — 门禁的「贫瘠环境」假设 + 同一颗哑弹的 8 处漏网

性质: 验证基础设施(不改产品行为)。**CLONE_DECISION**

**问题一: 我的门禁依赖「我 shell 里恰好有 node」**
Batch 353 收尾的全量回归里 `batch352` 挂于
`FileNotFoundError: No such file or directory: 'node'` —— 单独手跑能过、**进门禁就挂**,
因为 `run-frameos-verifiers.sh` 只用 pyenv 的 python、**不导出 nvm 的 node 路径**。
> **门禁必须在最贫瘠的环境里也能跑**; 把可靠性绑在调用者 `PATH` 上,
> 等于留了一个「在我这儿好好的」型故障。
修 `find_node()`: `LIBLIB_NODE` → `PATH` → `~/.nvm/versions/node/*/bin/node` → homebrew
→ `/usr/local/bin` 逐级探测。验证刻意做「**贫瘠环境演练**」:
`env PATH="/usr/bin:/bin:...:$HOME/.pyenv/versions/3.10.6/bin"` 实跑通过。

**问题二: 同一颗哑弹还有 8 处漏网**
全量回归里 **batch327 又以 `diagnostics:zero` 失败** → 查得 frameos 套件里
**10 个验证器各自带一份内联 `requestfailed` 监听器**(133/134/327/328/329/330/
331/332/333/351), 其中 **8 个**(除已修的 333/351)仍在把 `net::ERR_ABORTED` 当应用错误。
> **Batch 351 的教训被放大: 修了「一处漏网」不等于修了「这类问题」。**
> 判据要放**单一出处**并让所有副本引用它, 而不是逐个打补丁。
8 个已全部接入 `is_dev_server_noise`, 并**逐个实跑**确认(10/7/14/17/23/22/19/17 checks PASS)。

**过程中的一个自伤**: 批量注入时我加的 `sys.path.insert` 用了**没导入的 `sys`**;
`py_compile` **抓不到**运行时 `NameError`(编译过、实跑炸: `batch328: NameError: sys`)。
7 个文件全缺 `import sys`, 补齐后逐个实跑。
> **`py_compile` 只保证语法, 不保证名字存在**; 批量改动后必须实跑,
> 尤其给别人的文件注入代码时。

**遗留**: 同样的内联监听器在 liblib / jimeng / director 套件里可能也存在(本批只清 frameos);
门禁的**运行环境约定**目前靠各验证器自己兜底, 更彻底的做法是 runner 统一注入环境。

**候选 Batch 355**: 把 `is_dev_server_noise` 与「贫瘠环境」约定推广到 liblib/jimeng 套件;
或把可寻址门禁推广到那两条线(见 Batch 353 候选)。

---

## Batch 355 — 「启用着、收下输入、什么都不做」的表单控件: 普查 + 清零 + 门禁

性质: 克隆侧缺陷。**CLONE_DECISION**（不改任何源站已采样的文案与外观）

`FrameosProjectAssetsPanel` 的搜索框是**启用着、无 `value` 绑定、无 `onChange`** 的
裸 `<input>`。实测: 输入「角色」后面板文本**一字不变**, 输入框自己还留着字,
而 **console errors 为空** —— 即不是报错、是**纯惰性**, 所以任何「页面有没有报错」
类检查都发现不了它。与 Batch 350 裁剪宽高同族(看起来能用的表单静默丢弃输入),
区别是这条连反馈都没有。

普查探针在 4 种 UI 态枚举所有 input/textarea, 判据用 React 挂在 DOM 上的
`__reactProps$*` 读 `onChange`(即「这个控件有没有被 React 接上事件处理」,
而不是看源码里有没有写):

| UI 态 | 控件 | 静默丢弃 |
|---|---|---|
| default | 0 | 0 |
| **assets_panel** | 1 | **1** |
| crop | 2 | 0(350 已修) |
| generative_panel | 1 | 0 |

**全 frameos 只剩这 1 个。**

修: **不是「让它能用」, 是「别假装它能用」**。面板是硬编码空态「暂无已生成的资产图」
—— 克隆侧没有资产数据, 而「设为资产图」的源站点击效果**未采样**(226),
所以「图片节点该归角色/物品/环境哪一类」**没有依据**, 凭空虚构分类学比留个
诚实禁用态更糟。加 `disabled` + `title="暂无资产可搜索"` + 视觉区分, 空态文案不动。
> 与 Batch 344「分组删除」同构: 没有真 action 可接时, **让 UI 停止撒谎,
> 而不是发明一个假 action**。

verifier 13 项/0 诊断, 把普查变成**门禁**(每态带 `scan:not-empty` 防假绿 +
「总数 ≥ 4」防普查整体失效), 并钉住三条性质: 确实 disabled / 带说明 / 空态没被误删。
变异: 去掉 `disabled` → 红 `no-silent-discard:assets_panel 静默丢弃输入的控件:
[{'tag':'input','ph':'搜索资产名称...','data':['data-frameos-assets-search']}]`。

**未改的保真度差距**: 「设为资产图」弹绿色成功提示(Batch 226 mock)与资产面板恒为空
**两者互不连通** —— 用户点了看到成功, 打开面板却什么都没有。要连通就得先有资产数据
与分类学, 属产品决定。本批只消除了「搜索框假装能用」这一处更硬的谎言。

**自伤**: 普查探针第一版在 Python 里写了 `hasattr(window...)` —— `window` 是 JS 名字,
直接 NameError; **`py_compile` 抓不到, 必须实跑**(与 354 的 `import sys` 同类)。

**候选 Batch 356**: 同一套普查推广到 jimeng / liblib 画布(它们的输入控件更多、
盲区大概率更多); 或用同样的「普查 → 清零 → 门禁」三段式审其它交互族
(如「启用但无 handler 的按钮」—— 347 审的是**缺钩子**, 不是**缺行为**)。

---

## Batch 356 — 7 个「呈现为可点、实则毫无反应」的按钮

性质: 克隆侧缺陷(几何/尺寸/圆角/位置/文案一律不动)。**CLONE_DECISION**

Batch 347 审的是「**缺钩子**」(能否被测试寻址); 本批审它的行为孪生 —
「**点了有没有反应**」。普查 frameos 全部 `<button>` 找无 `onClick` 的,
逐个人工核实后确认 **7 个**是真缺陷:

素材库的 收藏筛选/创建者筛选/创建时间排序(灰底 pointer)、批量操作(描边 pointer)、
**+ 本地上传(蓝色主按钮)**、以及 FrameosPromptEditor 的
**生成音频(¥100)/生成视频(¥300)(实心蓝圆形主按钮)**。

> **越像「主行动」的越糟**: 两个「生成」是各自面板里最醒目的实心蓝圆钮,
> 「+ 本地上传」是素材库那一行里唯一的蓝色按钮 —— 点了全都毫无反应, 连提示都没有。

**普查本身有误报**: 初版报 8 个, 其中 `FrameosGroupToolbar` 的排列菜单项是**误报**
(它有 `onClick: arrangeGroup`, 只是落在我的正则窗口外)。
> 普查的假阳性会把**真按钮**标成「该修的」, 诱导改动正常代码 ——
> 352 的死状态普查已吃过 5 类误报, 这里再次印证: **普查结果必须逐个核实**。

修: 源站这些交互**未采样**, 而「生成」是**付费动作**(¥100/¥300)按纪律**绝不触发**
→ 不发明行为, 按仓库既有「惰性控件」约定(见「整组执行」: cursor default + 暗色)
改为 `disabled` + `title` 说明 + 降饱和, **几何/文案一律不动**。

verifier 34 项/0 诊断, 变成门禁: 判据 = **计算样式 `cursor: pointer` 且未 disabled
且 React props 无 onClick**。另钉住 7 个目标确实 disabled、带说明、
**付费按钮未被接线**(回归防护)、**几何未动**(32×32)。
变异: 「+ 本地上传」恢复蓝色 pointer → 红 `no-fake-clickable:material_library
呈现可点却无 handler: [{'aria':'','text':'+ 本地上传'}]`。

**写验证器时踩的四个坑(全是探针自己的问题)**:
① **同名按钮张冠李戴** —— 「本地上传」有两个: 素材库里那个是假按钮(该修),
   工具条上那个是 `onClick={openFilePicker}` 的**真**按钮(不能动);
   早期只按 `aria||text` 匹配, 结果把**真按钮**当成目标、报「又变回可点」
   → 目标识别必须带**所在对话框作用域**;
② 装饰前缀(「**+** 本地上传」), 匹配前需归一化;
③ fixture 的 `video-1` 带 `imageUrl`, 按 Batch 225「内容媒体节点无面板」被早退分支
   排除, **进不去视频面板** → 必须注入无内容的视频节点;
④ **自己污染 `diagnostics:zero`** —— 多次注入固定 id 造成 React 重复 key 报错;
   且我第一次把 `id` 拼成 `Date.now()` 而 `selectNode` 用了 `nodes.length`, 两者对不上。
> ④ 是本会话**第六次**因「先看失败在哪一步」避免误改应用代码。

**保真度差距**: 素材库三颗筛选芯片在源站是真能筛的; 「+ 本地上传」「生成音频」
「生成视频」在源站都是真功能, 克隆未实现 —— 本批只处理外观, 真实行为依赖
源站采样或产品决定, 不在本批内发明。

**候选 Batch 357**: 把「假可点按钮」与「静默丢弃输入」两套普查推广到
jimeng / liblib 画布; 或继续在 frameos 挖第三类交互谎言
(如「有 handler 但 handler 只弹 toast 而状态没变」—— Batch 344/345/349 挖到的都是这类)。

---

## Batch 357 (2026-10-01) — 第三类交互谎言: 「点了有反应、但状态没变」

**不是继续做测试基建, 是真的找到 5 条产品缺陷。**

第三类交互谎言(前两类: 350/355 静默丢弃输入、344/356 假可点按钮):
有 handler、点了确实弹出一条**绿色 ✓「已xxx」成功提示**、但底层状态一点没变。
它在每一层单看都是「正常的」—— 有函数、有反馈、零 console 错误、截图还挺好看。
只有「点完去看结果」那一步才露馅。

普查 `scripts/toast_lie_census.mjs`(AST, 36 个源文件) 找到 6 条 TOAST-ONLY,
**逐个人工核实**后 5 条为谎报、1 条为真:

| 位置 | 文案 | 核实 |
|---|---|---|
| `page.tsx` 设置为资产图 | 已设置为资产图 (mock) | 谎报: 资产面板是**写死的空态**, 无数据源 |
| `GroupCanvas.tsx:121` 复制 | 已复制分组 (mock) | 谎报: 无 action, 且**语义未定义**(见下) |
| `GroupCanvas.tsx:126` 创建副本 | 已创建分组副本 (mock) | 谎报: 同上 |
| `GroupCanvas.tsx:250` 批量连线 | 批量连线 (mock) | 谎报: 多步交互的起点, 非可补 action |
| `GroupToolbar.tsx:264` 存为模板 | 已存为模板 (mock) | 谎报: **面板另一头是硬编码常量表** |
| `page.tsx:357` ⌘S | 已保存当前画布 | **非谎报**, 保持原样 |

最值得记的是**存为模板**: 要**翻到面板的另一头**才看穿 ——
`FrameosTemplatePanel` 渲染的卡片来自常量 `TEMPLATE_CARDS`, store 里没有
`template` 字段。菜单项的反馈和它声称写入的那个目的地是两套互不相干的东西。
(而 Batch 355 禁用资产搜索框时写下的注释其实已经点破了「设置为资产图」的根因:
*「面板内容是硬编码空态……克隆侧没有资产数据」* —— 同一件事的两头, 一头已诚实、
一头还在撒谎。)

「复制分组」卡住的地方是**语义**而非缺代码: 分组是由存活成员算出来的盒子
(Batch 341 不变式), 复制的是盒子还是成员? 成员副本归不归入新组? 两个组引用
同一批成员合不合法? 源站未采样, 全是编造。对照组: 节点级「创建副本」是**真的**
(`duplicateNode`, Batch 170) —— 同名不同命, 反而更让人误以为分组那档也能用。

⌘S 判为**非谎报**并写进门禁白名单常量 `BENIGN_TOAST`: 画布每次 nodes/groups/edges
变动都由 mount 订阅自动写 localStorage, 那句话在事实上为真, 只是把功劳记在一次
并不存在的动作上。门禁注明「若日后画布不再自动保存, 这条应改判并移出白名单」——
**绑真实性质, 不绑缺陷副作用**。

修: **先被自己的修法推翻一次**(见下), 最终形态 = 保持启用 + 实话提示。

**⚠️ 修法改过一次: 被 batch170 打回, 而它是对的**
第一版把 5 项统统 `disabled` + title。门禁 30 项全绿、3 项变异全红, 看着很稳——
但全量回归里 **batch170 红了**: `node:item:设为��资产图:disabled=false`。
按「撞上旧断言先去查一手源站证据」: `BEHAVIORS.md:33`(2026-09-25 源站实测,
Batch 226/228) 记着内容图片态的「设置为资产图」是**启用**的, 禁用的只有空图片态
的复制图片/重新生成。**我改 enabled 是在改源站事实。**
更要紧的是第二层: 缺陷本来就不在「能不能点」, 而在**谎称成功**; 拿 disabled 当
修复, 等于用改源站事实去盖住文案不诚实。
最终 5 条统一为: **保持启用 + toast 从 success 改成 warning 说清「暂不可用」+ title**。
一个谎报都没被藏起来, 只是反馈终于说实话。判据随之从「只弹 toast」收紧为
「**只弹 toast 且声称成功**」—— 一条 warning 说「暂不可用」是诚实的, 不是谎报。
另四项虽无门禁钉启用态, 但也无任何证据说它该禁用; 同一条修法在有证据的那项上
已被证伪, 就不该只对它网开一面。

**普查工具自己假绿了三次**(都是「扫不全」伪装成「没问题」, 全是同一个家族):
① `.tsx` 里 `(e)=>{}` 外层是 `JsxExpression`, 没解包 → **全部 JSX handler 一条没扫到**;
② 紧凑箭头 `() => showToast(...)` 的 body 是**表达式**不是块, `forEachChild` 起步
   恰好跳过顶层那个 CallExpression —— 而快捷键 handler 都是块体, **侥幸命中**,
   让扫不全的工具看起来像没问题;
③ 同文件两个同名 `const handler`, 按名字取第一个 → ⌘Z/⌘S 整段解析成另一个函数而消失。
外加一条**构造性假阳性**(`const finish = () => showToast(...)` 外面才 writeText)
和一条**有意的假阳性**(FrameosToast 自己监听 toast 事件, 显式排除并报出排除数)。
> 第四次因「先怀疑测量方法本身」避免把「零命中」当成「没问题」。

**粒度**: 判定单位是**单条 toast** 不是整个 handler —— keydown handler 里有 6 条
toast, ⌘Z 调了 `undo()`、⌘S 什么都没调, 按 handler 整体判定会**放过后者**。

verifier 40 项/0 诊断, 变成门禁: 只允许剩 1 条「声称成功」且必须是白名单的 ⌘S;
5 条谎报文案逐条钉死; 5 条「暂不可用」必须在场且**都不是 success 变体**(抓「话说对了
颜色还在撒谎」的半修); `scanned>=30`+`toastSites>=8` 防假绿; 运行时逐个点下去验
variant 与文案; 5 处**仍启用**(batch170 回归防护); 并钉住 Batch 344 的「删除」没被带走。
变异 3 项全红: 撤销修复 / 半修(仍用 success 变体) / 改源站事实(又 disabled)。

**探针自己踩的三个坑(都不是应用缺陷)**:
① **菜单开着就右键 = 菜单被关掉** —— 上下文菜单有一层 `position:fixed; inset:0` 遮罩,
   其 onContextMenu 只做 closeContextMenu。实测 items 序列 3 → 3 → **0**。
   `open_group_menu()` 因此做成幂等(先 Esc 再右键);
② **别删 React 管的 DOM** —— 曾用 `.forEach(e => e.remove())` 给 toast「清场」,
   结果 fiber 与 DOM 对不上, 下一次重渲染把右键菜单一起拖没了; 改成**前后取差集**;
③ 点完菜单项菜单会关, 每点一项前都要重新打开。

**同一次回归里另一条断言「该」改 —— 区别在于断的是不是源站事实**:
`verify-frameos-batch251.py` 的 `port:click-mock-toast` 断的是文本
`批量连线 (mock)`。它**不是**源站事实(源站点击效果从未采样, 断言名里就写着 mock),
所以该跟着改; 而 batch170 断的启用态**是** `BEHAVIORS.md:33` 采样到的源站事实,
所以该改我的代码。**同一个回归、两种相反的处置, 分野就在这一条。**
batch251 周围那几条(24px 圆 / `48, 54, 66` 底 / 贴右边中点)全是采样到的几何,
一根没动; 只把 mock 文案断言换成两条不钉死具体文案的性质断言:
`port:click-gives-feedback` + `port:click-not-success-claim`。

**环境噪音(非本批)**: 同一次回归里 batch279/300 失败于
`WebSocket is already in CLOSING or CLOSED state` / `ERR_CONNECTION_REFUSED`
(dev server 当时掉线), 隔离跑均通过。`is_dev_server_noise` 目前只挡
`requestfailed:...net::ERR_ABORTED`, 这两类要不要补进去**留作单独一批** ——
门禁过滤器必须双向验证, 不能顺手放宽。

---

## Batch 358 (2026-10-01) — 「启用却点了没反应」普查推广到 liblib 画布线

frameos 三类交互谎言的门禁(350/355/344/356/357)都齐了, **liblib 这条线一个都没有**:
302 个 `verify-liblib-batch*.py` 里没有一条查「可点外观却没有 handler」。

普查(运行时, 16 个 UI 态)找到 **95 个**「启用、无 handler」的控件: 教程四项 /
生成历史卡片 查看·使用·下载×3 / 时间倒序 / 卡片收藏×40+ / 筛选 /
工具箱模板说明与模板选择 / Agent 历史对话·设置·CLI / 开通会员 / 积分余额。
逐组读过源码确认, 非静态推断。几处值得单说:
- `HistoryPanel` 同一行的「收藏」**有** `toggleFavorite` —— 同组控件不能靠位置猜;
- `AgentDrawer` 里紧挨着的「新对话无法分享」是**正确写法**(disabled+title+opacity-40),
  同一个抽屉里, 正确示范和四个谎言并排;
- 「开通会员」是付费入口, 按纪律**绝不接线**。

**修法: 保持启用 + 去掉悬停骗人的反馈 + title 说明, 不落 `disabled`。**
理由同 batch357 的分野: `verify-liblib-batch97.py` 依据 2026-09-05 源站审计断言
Agent header 三项 `is_disabled() == False`, `batch106/121` 断言教程四项可见 ——
断的都是**已采样的源站形态**, 所以不能靠禁用来「修」。

**⚠️ `aria-disabled` 也踩了同一个坑**: 第一版给惰性控件加 `aria-disabled="true"`
(语义上比 data-* 更妥), 结果 batch97 直接红 —— **Playwright 的 `is_disabled()`
把 `aria-disabled` 也算作禁用**。于是全部 14 处改用 `data-inert="true"`:
语义标注不能变成「改掉已采样源站形态」的暗门。

**门禁的例外规则: 不按名字开白名单, 要求例外自证**(同时带 `data-inert` 与非空 `title`)。
白名单只会在下次重构里悄悄失效 —— 新增一个死按钮不会被列进去, 门禁仍绿, 而用户多点了一次。
属性判据不会: 任何新死按钮都得自己写清「我不可用」和一句给用户看的理由。

**扫描器自己假绿了五次**(全是「扫不全」伪装成「没问题」):
① 只用 `cursor:pointer` 判可点 → liblib 不用内联 cursor(36 个按钮 35 个 default),
   扫出「0 个假可点」—— **那个结论是无效的, 差点当体检报告交出去**;
② 只扫 button → workspace/canvas 两态元素数完全相同(36/36), 可画布态明明多了 10 个节点;
③ 把**继承了父元素 cursor** 的 `<path>`/`<svg>`(34+1 个)算成独立控件;
④ 特征集只取 data/aria/role → 把「面板开了但控件是纯文本 div」的 4 个态误判成「没打开」;
⑤ **只收 pointer 或已接线** → 正好滤掉了要找的缺陷: TutorialMenu 那四个按钮既没有
   onClick 也没有 cursor, 而「启用却无 handler 的按钮」按定义就是这类缺陷本身。
> ⑤ 不是漏掉某一个缺陷, 而是**系统性地对最纯的那一类缺陷失明**。

外加两条构造性假阳性的正确处理(不是开白名单): `onChange`/`onInput` 同样算已接线
(range 天生没有 onClick); `<label>` 的接线看**后代控件**(点 label 等于点它包的 checkbox)。

**防假绿**: 每个态必须与默认态元素集合不同, 否则「零违规」只是把默认态数了 16 遍。
**防过滤过头**: 扫描器先后加五层过滤, 所以专门有一条**反向变异** —— 从本来是活的
控件(「关闭工具箱」的 onClose)上摘掉 handler; 若扫描器过宽, 这个变异会看不见。
实测 4 项变异全红(撤销修复 / 抹掉 title / 只降饱和不声明 / 反向), 判据没被放宽。

**顺带修掉一处他人的恒真断言**(解除仓库级门禁阻塞, 已提交文件非 WIP):
`verify-liblib-batch612.py` 的 `panel:添加节点-opens` 写的是
`page.locator("text=基础节点").count() >= 0`。查证后发现**「基础节点」这个文案在
src/ 里根本不存在**, 那个定位器恒为 0, `>= 0` 永远成立 —— 恒真断言比没有断言更危险。
改用面板常驻的 `data-add-node-entry`, 112/112 仍全过。
> 这里我连错两次: 第一次直接改 `>= 1`, 结果 batch612 失败, 才意识到定位器本身是错的
> —— **恒真断言的修法要连定位器一起修**。第二次换成 `data-add-node-search` 又失败
> (它只在 searchOpen 时渲染), 第三次才用对。

**顺带查到、只记录不动的两处死状态**: uiStore 的
`isToolboxPanelOpen`/`isMaterialPanelOpen`/`isCharacterPanelOpen`/`isHistoryPanelOpen`/
`isTutorialPanelOpen` **零读取**(面板早已改由 `activePrimaryPanel` 单一槽位驱动);
`toggleUserMenu` **全项目无人调用**, `isUserMenuOpen` 只被
`libtvSelectionCommandContext` 读来抑制快捷键 —— 用户菜单没有触发器也没有渲染器。

**覆盖缺口(如实记录)**: liblib 没有 runner, 302 个验证器串行约 4 小时, 本批未全量跑;
跑的是与本次 6 个改动组件相关的 17 个定向验证器。

---

## Batch 359 (2026-10-01) — 普查扩到节点编辑面: 39 个死控件, 以及三次假零

358 查的是**画布外框**的 16 态。节点一选中, 浮出来的是另一整片界面(图片节点浮动
工具条、图片编辑面板、标注模式工具条、视频片段编辑面板)—— **从没普查过**,
而 frameos batch 350 那个「裁剪宽高静默丢弃输入」正是在节点级编辑态里。

**「静默丢弃输入」: 0 命中**, 且做过功能抽检(风格库搜索 16→0、特效库 24→0、
工作区改名生效) —— 有 onChange 只是必要条件, batch 350 的裁剪框就是「有 handler、
值进了 store、但没有任何代码读它」。

**「点了没反应」: 39 个**, 集中在两个文件:
`ImageEditPanel`(展开编辑器 / 参考·标记·风格 / 比例·画质·分辨率 / 高级设置×2 /
翻译 / 撤销)与 `VideoGenerationPanel`(doc-sparkle / 翻译视频提示词 / settings2)。
整个图片编辑器**只有「生成图片」和模型菜单是真接线的**(全文件 6 处 onClick)。
对照组很说明问题: 视频片段面板的「展开智能剪辑编辑器」**早已诚实报告**
「本地原型：展开编辑器未连接」—— 同类问题在那边解决过了, 这边却一直挂着悬停反馈。

修法同 358: 保持启用 + 去悬停反馈 + cursor default + title + `data-inert`。
文案与几何一律不动(既有门禁 batch10 断的正是 54×26 / 32×32 与文案)。

**本批真正的收获是三次假零**(普查工具最危险的失败模式不是报错, 是**安静地
什么都没测然后报「无问题」**):
① **画布没 hydration 完** —— 一轮 `wait_for_timeout(1500)` 没等到, `node_ids`
   拿到空数组, 探针「跑完」并报 0 问题。假零。现在显式 wait_for_selector,
   节点为空直接抛错。
② **标注模式没打开** —— 工具条带 scale transform, 页面内 el.click() 点不动它。
   第一版该态 testid 集合为空、控件数反而从 ~50 掉到 39, 却照样显示「无问题」;
   三连跑里还**间歇性**失败。现在 click(force) → 退回派发 → **有界重试**,
   仍打不开就红(那一态等于没测, 不能算「干净」)。
③ **⚠️ 扫描器把要找的缺陷预先滤掉了** —— 这个最讽刺, 是我在 358 批评过别人的
   同一个错误自己又犯一遍: node 探针写了「有 handler **或** cursor:pointer 才收」,
   而 Tailwind 下 `<button>` 的 computed cursor 是 `default` 不是 `pointer` ——
   **没有 handler 的按钮在判定之前就被丢掉**, 死控件判据根本没机会触发。
   变异测试红在了下游的 `annotate:opened` 而不是死控件断言上, 这才暴露出来。
   一改就是 39 个。顺带修掉一条**不成立的豁免**: 原先「祖先有 handler 就放过」对
   ImageToolbar 是错的 —— 工具条容器上是 `onClick={(e) => e.stopPropagation()}`,
   阻止冒泡, 什么也不做。现在自称控件的元素必须**自己**有 handler。

变异 2 项全红且**红在正确的断言上**: 摘 onChange → `no-silent-discard`;
整个摘 onClick → `no-dead-control`。
> 第二项第一版写成 `onClick={() => undefined}` —— 函数还在, 普查认为「已接线」。
> **要让判据生效, 必须让 handler 真的不存在。**

**顺带修掉一处别人批次引入的回归**: `verify-liblib-batch25` 红了, 但与本批零交集
(它只用 data-video-clip-*), 引入点是 `612689b1`(batch 477 把 `status` 从 string
改成 `{text, tone}` 对象)—— `{status && ...}` 对对象**恒真**, 于是状态行永远渲染,
在提示词下**永久占一行空白**。改成 `{status.text && (` 既保留 477 的
`data-status-tone` 与对象模型, 又恢复原意, batch25 随即通过。
> 与本会话早先修的 batch612 恒真断言同类: 仓库门禁会因别的批次而红。
> **先查是谁、什么时候引入的**, 别默认是自己造成的, 也别因为「不是我弄的」就不管。

覆盖下界: 节点数≥8 / 节点面≥8 / 控件≥300 / 输入≥10 / ≥3 个节点进到标注模式。
实测 16 画布态 + 15 节点面(5 标注态)、**709 控件**、29 输入。

---

## Batch 360 (2026-10-01) — 补上两块从未普查的面: 3 个死控件 + 一条漏掉的门禁

358/359 覆盖: 画布外框 16 态 + fixture 里 10 个节点的编辑面。剩两块没测:
① **能新建但默认画布没有的节点类型**(音频/智能剪辑/逐帧拉片)—— 编辑面板一次没进过;
② **浮层**(预览大图 / 标注画布 / 标注颜色菜单)—— 标注态进去之后画布控件是另一层,
而 frameos batch 350 的裁剪框正是这种「浮在上面的编辑层」。

**跳过「导演台」**: 它打开 DirectorDesk, 那是另一条线且有并行 session 正在改
(`src/components/director/*` 有未提交 WIP) —— 现在普查会把人家的在途改动混进结果。
**跨线不碰。**

结果: 浮层三面 0 问题; 节点类型里 **3 个死控件**:
`AudioNode:59` 播放音频(白色圆形主按钮, 最像能点的那个)、
`VideoClipEditPanel:73` 默认模式、`:83` 输出设置 16:9·720P·30s。
三个都无 onClick 也没 disabled, 却各带悬停反馈。修法同 358/359, 文案几何不动
(batch25 读的正是文案, 改后仍过)。

**探针踩坑但没变成假零**: 第一版把 CSS 类名当成 `data-add-node-entry` 的值
(正确是 AddNodePanel 的 `entry.type`: audio/video-clip/shot-breakdown), 三个类型
全被跳过。关键是探针**如实报「跳过」而不是「0 问题」** —— 输出里是三行
「面板里没有该类型」。若当时报 0 问题, 这三个面就会以「已覆盖」的名义混过去。
**探针宁可说自己没测到, 也不谎报干净。**

**门禁补上一条漏掉的断言(本批最重要的产出之一)**: 变异里有一项**没被抓到** ——
把「默认模式」的 hover 底色加回去, 门禁是绿的。判据只管「有没有 handler」,
没管「看起来能不能点」; 而 **hover 变色恰恰是这类缺陷最核心的视觉特征**, 用户就是
被它骗的。补成 `no-lying-affordance`: 声明了惰性的控件若还带 `hover:` 暗示,
就还是在骗人。补完 4 项变异全红。
> 属「元缺陷踩到即变门禁」: 不是某个控件的问题, 是判据少了一个维度。
变异第 4 项第一版挑错了目标: 选了标注「重做」, 但它本来就 disabled ——
禁用的控件本来就不该被判成死控件, 那样测不到任何东西。改摘标注工具切换的 onClick,
红在 `overlay:annotate:no-dead-control`。

防假零: 三种新节点**必须真的被创建出来**, 每个浮层**必须真的打开**(各有独立标志),
每个面至少扫到 30 个控件。

**顺带记录(只记录不修)**: `CameraConfigDialog` / `CameraMovementDialog`
**全项目无人渲染** —— 死组件。与 359 记的 uiStore 五个零读取开关、
`toggleUserMenu` 无人调用同类。

覆盖 6 个面。verifier 31 项; 共享探针加了 `lyingAffordance` 字段后,
359 门禁 52 项复跑仍全过。
