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
