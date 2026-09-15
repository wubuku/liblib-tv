# 即梦 AI 画布复刻 — 源站证据与研究记录

> 源站: `https://jimeng.jianying.com` AI 画布 (`/ai-tool/ai-canvas/<project-id>`)。
> 提取日期: 2026-09-12，viewport 1680×826 @dpr2，登录态，Chrome for Testing 147 (裸启动、走系统代理)。
> 复刻路由: `/jimeng` (master 工作区，与 LibTV / FrameOS 隔离)。
>
> 提取方式: CDP attach 到用户已登录的隔离 Chrome (端口 9333)，DOM/computed style
> 读取 + 只读交互截图。提取脚本存于 `/tmp/jimeng-clone/`（会话产物，不入库）。

## 1. 证据分类约定

- `SOURCE_FACT` — 源站 DOM / computed style / 截图直接读出的事实。
- `CLONE_DECISION` — 复刻侧自主决策（近似、命名、mock）。
- `BLOCKED_BY_FIXTURE` — 需要源站副作用才能继续的观察。

## 2. 技术栈事实

- SOURCE_FACT: 源站画布即 **React Flow (xyflow v12)** —
  `react-flow octo-canvas-flow`、`react-flow__viewport xyflow__viewport`、
  `react-flow__node react-flow__node-video`、`react-flow__node-toolbar`。
  复刻沿用 `@xyflow/react` 12（本仓库已有依赖）。
- SOURCE_FACT: 源站 UI 为 Tailwind + 内部设计 token（`bg-dreamina-canvas-bg`、
  `z-canvas-chrome`、`rounded-dreamina-tooltip` 等；"dreamina" 为即梦内部代号）。
- SOURCE_FACT: 边不在 DOM（`.react-flow__edge` 数量为 0），由全屏 `<canvas>`
  层绘制（`z-canvas-connection-flow-surface`）；点阵网格同样是 canvas 绘制
  （`absolute inset-0 z-[-1]`）。
- CLONE_DECISION: 复刻用 CSS radial-gradient 点阵 + xyflow 默认 SVG 边。

## 3. 关键样式 token（computed style）

| Token | 值 | 分类 |
|---|---|---|
| app 背景 | `rgb(15,15,18)` | SOURCE_FACT |
| 画布背景 | `rgb(13,13,13)` (`bg-dreamina-canvas-bg`) | SOURCE_FACT |
| body 字体 | PingFang SC, Hiragino Sans GB, Microsoft YaHei | SOURCE_FACT |
| 顶部药丸 | `rgba(32,32,34,0.8)` + `blur(40px)` + inset `rgba(255,255,255,0.06)` + `0 1px 2px rgba(0,0,0,0.24)`，r8 | SOURCE_FACT |
| 底部 dock | `rgb(13,13,13)` + inset `rgba(255,255,255,0.04)`，r8，p4，164×36 | SOURCE_FACT |
| 节点工具条 | `rgb(32,32,32)`，r12，h40（`react-flow__node-toolbar`） | SOURCE_FACT |
| 工具条分隔线 | hr 5×16 含 p2，bg `rgba(204,221,255,0.1)` | SOURCE_FACT |
| VIP 钻石色 | `rgb(0,158,250)`（`text-dreamina-brand-bright-default`，14×14 svg） | SOURCE_FACT |
| 节点标题 | 13px/22px `rgba(255,255,255,0.698)` | SOURCE_FACT |
| 节点占位渐变 | `linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))` | SOURCE_FACT |
| 节点圆角 | 8px (`rounded-canvas-media-node-preview`) | SOURCE_FACT |
| AI 按钮 | `rgba(39,39,39,0.72)` 120×36 + 顶部渐变叠加（渐变值提取截断） | SOURCE_FACT/CLONE_DECISION |
| 点阵网格间距/颜色 | 不可从 canvas 直接读出 | CLONE_DECISION (28px / rgba(255,255,255,0.075)) |
| 选中环 | 白色 1.5px 视觉（具体 token 未读出） | CLONE_DECISION |

## 4. 布局骨架（screen rect @1680×826, zoom 73%）

- 顶栏 header: `absolute left-3 top-[10px] h-10 z-30`，全宽（右端 inset 12px）。
- 顶栏右药丸: 搜索/帮助 68×36；会员 161×36；头像 36。
- 左栏 aside: `absolute bottom-4 left-4 top-[72px]` 垂直居中；9 个 20×20 图标，
  垂直步进 42px；第 7 个（智能体）挂 Beta 徽标。
- 底部 dock: `16,774` 164×36：选择/布局/同步 3×28px 图标钮 + 分隔线 + 缩放 48×28。
- AI 按钮: `bottom-3 right-3` 120×36。
- 初始视口: `matrix(0.729858,0,0,0.729858,-60.6,1.3)`（底栏显示 73%）。

## 5. 视频节点（本 batch 复刻重点）

- SOURCE_FACT: 世界尺寸 ≈ 569×320（16:9）；节点 1 世界坐标 (675.6, 280.5)，
  节点 2 "视频 1" (1442.1, 323.2)。
- SOURCE_FACT: 标题行在卡片上方 32px（h-8，absolute bottom-full）：
  文件徽标 16×16 + 13px 标题（`min-w-canvas-zero` 截断）+ 右侧 Tag/Link 图标。
- SOURCE_FACT: 左右 Handle 为 60×120 隐形热区（`!rounded-none !border-0 !bg-transparent`，
  `top-1/2` 平移 ±30px）。
- SOURCE_FACT: "+" 圆钮 24px 出现在节点边缘中点，hover/选中显示；
  本地上传节点仅右侧有，空节点两侧都有（提取截图 05/06/07 对比）。
- SOURCE_FACT: 有内容的节点选中 → 上方弹出工具条（见 §6）；
  空节点选中 → 下方弹出视频生成面板（见 §7）+ 白色选中环。
- SOURCE_FACT: 有媒体时卡片含：中央 32px `rgba(0,0,0,0.6)` 播放/暂停圆钮、
  底部 播放|时间 00:02/00:06|静音|全屏 控制、底边 2px 播放进度条。
- CLONE_DECISION: mock 海报为合成 SVG 渐变（不含源站用户内容）；`playing`
  初始 false 对齐提取时的暂停态。

## 6. 选中节点浮动工具条（当前开发重心）

- SOURCE_FACT: 触发 = 节点选中（鼠标移开后仍在）；载体为 xyflow `<NodeToolbar>`
  （`react-flow__node-toolbar`），位于节点上方（toolbar 775×40 @ [253,130]）。
- SOURCE_FACT: 条目（视频节点）: 局部重拍✦ / 智能超清✦ / 视频编辑✦ / 截取帧∨ /
  补帧✦ / 视频修剪 / 提示词反推 ｜ 分隔线 ｜ 全屏图标钮 / 下载图标钮。
  ✦=VIP 标记（14×14, rgb(0,158,250)）；∨=下拉。
- SOURCE_FACT: 条目文本 13px/400 白色；条目内 icon 16×16（`size-4`）；
  尾部图标钮 32×32 r8 gap4；条目 hover 有浅色底（近似 rgba(255,255,255,0.08)）。
- SOURCE_FACT: 截取帧下拉菜单: `rgb(38,38,38)` r12，146×130，菜单项
  首帧 / 尾帧 / 自定义（16px 图标 + 13px 文本，行高约 44px），锚在按钮下方 8px
  （`top-[calc(100%+8px)]`），z-[120]。
- 截图: `docs/design-references/jimeng/jimeng-source-video-node-selected-toolbar-1680-2026-09-12.png`、
  `jimeng-source-capture-frame-dropdown-1680-2026-09-12.png`。

## 7. 编辑态与其他状态（后续 batch 素材）

- 空节点选中生成面板: 见
  `jimeng-source-empty-node-selected-genpanel-1680-2026-09-12.png`。
  面板含 "+" 按钮、占位文案 "上传参考图、输入文字或 @ 主体，描述你想生成的视频"、
  底部模型行（即梦 Seedance 2.0 VIP ✦ ∨ / 16:9 · 720P ✦ · 1 ∨ / 全能参考 ∨ / 4s ∨ /
  @ / ✦56 / 圆形发送钮）。
  SOURCE_FACT (batch 3 精确提取): 面板本体 form 680×208、rgb(32,32,32)、r20、
  内边距 17、居中于节点下方 20px；载体同样是 `react-flow__node-toolbar`
  (position=bottom)；右上角 40×40 展开钮 (icon 24, white/60)。
- 节点右键菜单: 复制⌘C / 复制副本⌘D / 粘贴⌘V ｜ 保存到主体库 / 下载 ｜
  重做⌘⇧Z(禁用) / 撤销⌘Z / 删除⌫。
- SOURCE_FACT (batch 5): 局部重拍进入编辑态 — 节点标题行隐藏、节点放大 (zoom 101%)、
  帧条选区 (胶片缩略图 + 白框 4.0s + 两侧拖拽把手)；下方重拍面板变体:
  参考缩略图 chip (00:06) + "+"、提示词行 chip「00:00—00:04 重拍片段」(蓝色描边) +
  占位「描述你如何调整这一片段」、即梦 Seedance 2.5 ✦∨ / 6s / @ / ✦ 96/208 /
  白色可用发送钮。
- SOURCE_FACT (batch 6): 视频编辑进入局部编辑态 — 标题行与工具条隐藏、节点放大
  (zoom 145%)、视频自动播放；下方 8 图标工具药丸 (框选/套索/箭头/文字/橡皮擦/定位/
  分隔/撤销/重做) + 编辑提示条 (铅笔 + 「描述你如何调整视频」+ @ + ✦120/260 +
  禁用发送钮)。
- SOURCE_FACT (batch 7): 点击底栏缩放块弹出上方菜单 200×292 rgb(38,38,38) r12:
  放大视图⌘+ / 缩小视图⌘− / 适配画布⇧1 / 缩放至选中项⇧2 (无选中禁用) ｜
  缩放至50% / 缩放至100%⌘1 / 缩放至200%；底栏缩放值为可编辑输入框 (复刻只读,
  CLONE_DECISION)。
- SOURCE_FACT (batch 7): 顶栏 ? 弹出 240×272 rgb(34,34,34) r12 菜单:
  帮助中心 / 使用手册 / 快捷键 / AI生成水印设置 / 即梦CLI（顶部含租户名）。
- SOURCE_FACT (batch 7): 左栏按钮 hover 无 tooltip，仅按钮高亮 rgba(255,255,255,0.12) r8。
- SOURCE_FACT (batch 9): 截取帧下拉「自定义」→ 节点下方帧选择条: 胶片帧条 (左侧
  播放头竖线) + 底部行 ▶ 00:00 / 00:06 ｜ 📷 截取帧 ｜ 确认 (未截取禁用，
  截取后确认可用)。
- CLONE_DECISION (batch 8): 提示词反推为 mock 面板 (标题 + mock 反推文本 +
  复制提示词 + 关闭)；源站点击会提交付费推理任务 (BLOCKED_BY_FIXTURE)。
- SOURCE_FACT (batch 10): 视频修剪 → 节点下方修剪条: 全宽帧条 + 两端白色拖拽
  把手 (整段选中，条内右侧时长标签 6.1s) + ▶ 00:00/00:06 + 白色可用确认钮
  (区别于帧选择器的置灰确认)。
- CLONE_DECISION (batch 10): 截取帧下拉 首帧/尾帧 → 帧选择器预选播放头
  (00:00 / 00:06)，确认直接可用 (源站未提取该两项目录行为)。
- CLONE_DECISION (batch 11): 智能超清/补帧 → mock 任务流: toast「任务已提交
  (mock)」+ 节点处理中遮罩 (spinner + 处理中，持续)；源站会真实提交付费任务
  (BLOCKED_BY_FIXTURE)。
- SOURCE_FACT (batch 12): 「与 AI 对话」按钮 → 全高右侧抽屉 (宽 ≈410px):
  头部「新会话」+ 历史/展开/收起图标；居中空态「探索更多专业创作模式」+
  技能 chips (/ 视频反解 / 创作分镜 / 全流程广告片导演 / 剧本开发 / 剧情短片)；
  底部输入卡片 (占位「输入想法、剧本或上传参考，支持" / "使用技能，@ 添加主体，
  和 Agent 一起创作」+ 底行 +/使用技能/@/禁用发送)。展开时原按钮隐藏。
- SOURCE_FACT (batch 13): 顶栏 ⌕ 按钮实为「生成历史」下拉 (≈380px 面板):
  标题 生成历史 + tabs 全部(选中下划线)/图片/视频/音频 + 空态 暂无生成历史。
- SOURCE_FACT (batch 13): 会员药丸点击 → 全屏订阅页: 账户头 (租户名 + 基础会员
  + 到期时间 + 积分详情 ✦745 >) + 购买积分/订阅管理 + 促销横幅 (Seedance 2.5
  渐变 + 倒计时) + 计费 tabs 连续包年(限时5折)/连续包月/连续包季(7折)/单月购买 +
  四档价格卡 基础¥188 / 标准¥568 / 高级¥1959(划线¥2798, 首季7.1折) /
  超级¥8189(划线¥16999)，卡底 ✦积分每月 (725/2210/12320/54600) + 换算行。
  CLONE_DECISION: 促销倒计时简化为静态渐变条。
- SOURCE_FACT (batch 18): 帮助菜单「快捷键」打开右侧快捷键面板 (≈242px 宽):
  通用操作 — 打开/关闭 Agent ⌘/ · 撤销 ⌘Z · 还原 ⌘⇧Z|⌘Y · 移动工具 V ·
  全屏 F · 创建编组 ⌘G · 取消编组 ⌘⇧G；视图 — 放大 ⌘+ · 缩小 ⌘− ·
  适配画布 ⇧1|⌘0 · 缩放至100% ⌘1 · 缩放至选中项 ⇧2 · 缩放画布 ⌘ scroll；
  另有时间线分区 (被截断，BLOCKED_BY_FIXTURE)。
- SOURCE_FACT (batch 21, 导航语义): 空白左键拖拽**不平移**；普通滚轮 = 垂直平移
  (free)；ctrl+滚轮 = 缩放 (scale 1→1.2 实测)。中键拖拽平移为 CLONE_DECISION。
- SOURCE_FACT (batch 22): 点击头像展开与帮助菜单同构的账号菜单 (租户名头 +
  帮助中心/使用手册/快捷键/AI生成水印设置/即梦CLI)。
- CLONE_DECISION (batch 14): 撤销/重做历史栈 (past/future 快照，图结构变更时
  入栈) + 键盘 ⌘Z/⌘⇧Z/⌘C/⌘D/⌘V/Delete。
- CLONE_DECISION (batch 15): 视频播放 mock — 播放/暂停切换 + 0.25s tick 走动
  + 播完自停。（batch 32 起「播完自停」被「播完重放」取代，见下。）
- CLONE_DECISION (batch 16): 连线视觉 — bezier rgba(255,255,255,0.32) 1.5px，
  选中白色 2px；源站 canvas 边的确切视觉 BLOCKED_BY_FIXTURE。
  多选 = Shift+点击 (multiSelectionKeyCode)。
- CLONE_DECISION (batch 17/19): 图片节点 480×360 占位 / 文字节点 320×200 mock
  文本 / 音频节点 400×120 波形 (伪随机 44 条 + 00:15)；左栏 文字/图片/视频/音频
  点击在画布中央插入对应节点；+ 菜单 图片/文本/音频 在源节点旁创建。
- CLONE_DECISION (batch 20): V 切换 select/move 工具态 (dock 按钮高亮同步)；
  F = 浏览器全屏 (源站全屏语义未验证)。
- CLONE_DECISION (batch 22 实现): 帮助/? 与头像共用单一账号菜单实例，
  锚定头像下方 (源站两处菜单同构)。
- SOURCE_FACT (batch 24, 双击行为): 双击视频卡片中心 = **从头重播**
  (时间重置 00:00、进入播放态)；双击节点标题行 = 打开「添加节点」菜单的
  **extended 版** — 在 + 手柄菜单的 7 项之后追加「从资产库添加」「本地上传」。
  复刻: restartPlay + JimengInsertMenu extended；Escape 关闭菜单。
- SOURCE_FACT (batch 25): 空白画布右键弹出菜单: 新建节点 > (子菜单)、
  粘贴 ⌘V、重做 ⌘⇧Z (无历史禁用)、撤销 ⌘Z；样式与节点右键菜单同族。
  复刻: 子菜单 hover 展开 (源站子菜单展开态未提取，CLONE_DECISION)，
  子菜单项在右键位置插入节点 (screenToFlowPosition)。
- SOURCE_FACT (batch 27, 全屏播放器): 点击卡片右下角全屏图标 (或工具条 ⤢) 进入
  全屏播放器 — 全屏黑底、媒体铺满、左下 播放/暂停 + 时长、右下 静音 + 退出全屏，
  无画布 chrome；Esc 退出。复刻经 portal 挂 body (React Flow 视口 transform
  会劫持 fixed 定位)。
- SOURCE_FACT (batch 28, 订阅页高级卡): 4 停点积分滑杆 tick 标签
  6.2K/12.3K/18.5K/27.7K，默认 12.3K ↔ 12320积分每月（与 batch 13 订阅页
  高级卡 ✦12320 交叉一致）。CLONE_DECISION: 点击停点更新积分读数，其余
  停点积分为外推值；价格跨停点不变（未提取）。
- SOURCE_FACT (batch 29): 单击顶栏项目名 = 行内重命名编辑器（Enter 提交 /
  Esc 取消）；视频卡片静音按钮切换 muted（源站卡片默认静音，按钮标签
  描述动作）。
- CLONE_DECISION (batch 30): 高级卡滑杆轨道支持指针拖拽 snap-to-stop
  （停点按钮保留自身点击，capture 在按钮上跳过）；全屏预览静音图标联动
  节点 muted 态（源站语义已验证：默认静音、Unmute video ↔ Mute video）。
- SOURCE_FACT (batch 31): 视频节点标题 Tag 图标点击弹出颜色标记选择器
  （禁止/清除 + 青/蓝/紫/橙/黄 五色），选中即标记节点。
  CLONE_DECISION: 修剪面板手柄可拖拽 + 实时时长标签（源站拖拽几何未
  逐帧提取）。
- CLONE_DECISION (batch 32): 控件语义完善 — 播放到结尾后再点播放 = 从头
  重播（0.05s 容差），与 batch 24 双击重播语义一致，取代 batch 15
  「播完自停」；进度条可点击 seek（6px 热区、2px 视觉条不变；源站是否
  支持点击 seek 未采样）。
- CLONE_DECISION (batch 33): 修剪面板 确认 将拖拽范围的时长写回节点
  （store `applyTrim`：currentTime 重置 + 历史栈入栈，⌘Z 可还原，
  扩展 batch 14 历史栈）；面板确认后关闭，节点时间行反映裁剪后时长
  （源站确认后的节点态未采样，控件语义复刻）。
- CLONE_DECISION (batch 34): 帧选择器写回节点 — 胶片条点击移动播放头
  （时间读数跟随）；自定义模式 截取帧 预挂 确认，确认后节点 seek 到
  所截帧时间（`updateNodeData` currentTime）；首帧/尾帧预设即时可用，
  确认 seek 到 0/时长。深化 batch 9 帧选择器（预选播放头 → 写回节点）
  与 batch 10 截取帧下拉语义（源站确认后的节点 seek 态未采样）。
- CLONE_DECISION (batch 35): 自定义帧捕获确认后将 `capturedFrame` 写入
  节点数据，卡片左上显示 相机+时间 badge；帧选择器确认传递帧时间
  （batch 34 链路延续）。
- CLONE_DECISION (batch 36): badge 交互 — 点击 badge seek 区将节点
  currentTime 跳到所截帧；badge × 清除所截帧；两者 stopPropagation
  避免节点选中/拖拽副作用（源站 badge 交互未采样）。
- CLONE_DECISION (batch 37): 进度条指针拖拽 scrub — 按下即进入拖拽，
  连续跟随更新 currentTime；nodrag 类防止 xyflow 节点拖拽劫持指针
  （scrub 中途失效的根因）；普通点击 seek 回归保持。
- CLONE_DECISION (batch 38): Shift+点击多选；右键菜单 删除 一条历史
  批量移除全部选中节点（`removeNodes`）；文字节点双击进入行内 textarea
  编辑（Enter/Esc 处理；local-only mock）；`updateNodeData` 泛化为
  任意节点类型。
- SOURCE_FACT (batch 39, 交叉一致): 快捷键面板已记载 创建编组 ⌘G /
  取消编组 ⌘⇧G（与 §7 batch 18 面板条目一致）。复刻: groupSelected
  给 ≥2 选中节点分配共享 groupId，拖拽组内节点整组联动（onNodesChange
  按 groupId delta 展开 position）；⌘⇧G 清除全部 groupId
  （CLONE_DECISION: 原型级全局解组）；节点包装器暴露 data-group-id。
- CLONE_DECISION (batch 40): 生成面板提示词为真实 textarea，有文字时
  send 可用并提交 mock toast「生成任务已提交」（全局 toast store，
  JimengTaskToast 2.5s 自动清除）；startTask 同时推送 mock toast
  （batch 11 回归保持）。
- 记录说明（batch 433 对照批）: batch 28–32 由并行开发者实现（commits
  66094ad / e20b453 / 97c3ce3 / 77f0a6c / 0e18d9a），以上条目自其提交
  消息与代码审读转录；§7 原有直采条目止于 batch 27。batch 33 条目同法
  补录（commit 58edecb，batch 434 对照批）。batch 34 条目同法补录
  （commit 5422c94，batch 434 对照批）。batch 35/36 条目同法补录
  （commits 31a954e / 2c39b4b，batch 436 对照批）。batch 37 条目同法
  补录（commit 5f6da13，batch 437 对照批）。batch 38 条目同法补录
  （commit d4d69b5，batch 438 对照批）。batch 39/40 条目同法补录
  （commits 8c03eef / 9454fd8，batch 444 对照批）。batch 41–43/46/47
  条目同法补录（batch 452 对照批）。batch 49/50/51 条目同法补录
  （commits 215c86b / db2f1f5 / 622563e，batch 457 对照批）。
  batch 52 条目同法补录（commit ee6d1c5，batch 458 对照批）。
  batch 53 条目同法补录（batch 460 对照批）。batch 56 条目同法补录
  （commit ddfbb9e，batch 465 对照批）。batch 57 审计 + Escape 修复
  条目同法补录（commits b23f4dd / 9cde67f，batch 469 对照批）。
  batch 59 测试条目同法补录（commit 6c23ef9，batch 472 对照批）。
  batch 67 条目同法补录（commit a069c8e，batch 495 对照批）。
  batch 66 条目同法补录（commit b6df166 的前置提交，batch 492 对照批）。
  batch 61 加固/63/64/65 条目同法补录（commits 3089788 / 11dc070 /
  0ae72ca / 1b98d79，batch 488 对照批）。
- 复刻/加固 (batch 61): workspace Escape 分支统一调用全部退出动作
  （repaint/edit/infer/framePicker/trim）；多选重试等待 800ms 加固。
- 测试 (batch 59, 无新行为): 订阅滑杆刻度标签验证——6.2K/12.3K/
  18.5K/27.7K 刻度与 27690 端点值断言（batch 28/30/43 合同的复核）。
- SOURCE_FACT (batch 67, 媒体错误状态): 源视频资源完全过期后完整错误
  态可见——海报上 视频播放失败 文案 + 白色 重试播放视频 pill。复刻:
  mediaError 旗标 + setMediaError 动作（不污染文档脏状态）；蒙层渲染
  于海报上方（task/generating 蒙层优先）；重试清除错误并重启播放。
  clone 无自然失败路径——测试直接驱动状态。
- SOURCE_FACT (batch 66, 保存态门控下载): 跨截图证据——顶栏显示 已保存
  时下载可用，保存中… 时下载禁用（白/20 样式）且隐藏提示
  导出前请保存画布；统一规则覆盖单选工具条/多选工具条/右键菜单。
- SOURCE_FACT (batch 62, 截取帧 首帧/尾帧 直出图片节点): 源站选中视频
  节点 → 工具条 截取帧 → 首帧 后不打开帧选择器，而是直接异步产出
  带画面的 image 节点（截图 62-frame-menu.png / 62-first-frame-result.png /
  62-multiselect.png；点击后约 2-5s 节点出现，位于同行下一空位——
  实测落点 x=1708 即源节点右侧避让同行节点后的空位；标题为源资产名
  + 数字后缀）。复刻: captureFrame(id, 'first'|'last') 同步产出 image
  节点（poster=视频海报、标题「<源标题> 首帧/尾帧」、右侧 80 间距起
  逐节点右移避让、lineage 连线、入撤销栈）；自定义 仍走帧选择器。
- SOURCE_FACT (batch 63, 布局菜单实项): 布局 dropdown 实际项为
  宫格布局 / 智能布局（batch 62 的 auto-arrange 猜测被源站证据取代；
  算法 CLONE_DECISION: grid ceil(√n) 列 / 行）。编组在源站创建真实
  编组卡片（「编组 N」标题 + 面板 + 白边框 + 角点手柄，取消选中后
  可见）；编组选中工具条切换为 解除编组 ｜ 布局∨ ｜ 背景色 ｜
  下载(disabled)。复刻: JimengGroupFrames 视觉层叠加 groupId 模型
  （batch 39 架构保留）+ 工具条变体切换 + groupNames 入 store。
- SOURCE_FACT (batch 64, 多选右键菜单变体): ≥2 选中时右键菜单切换为
  多选变体（含 解除编组/编组 等多选项）。复刻: JimengContextMenu
  变体分支。
- 测试 (batch 65, 语义锁定): 编组交互语义锁定——成员单选、间隙拖拽
  惰性、编组 N 编号连续性（member solo-select / inert gap drag /
  编组 N numbering）。
- SOURCE_FACT (batch 62, 多选组合工具条): ≥2 节点选中时，选区包围盒
  上方 36px 居中出现组合工具条——rgb(32,32,32) r12 h40（与单选工具条
  同族载体），内容「N 节点」标签 rgba(255,255,255,0.5) 13px ｜分隔线｜
  编组（16 图标+文字）布局（16 图标+文字+下拉箭头，按钮宽 78 vs 编组
  62）｜分隔线｜ 下载图标钮 32×32 禁用态 rgba(255,255,255,0.2) + 视觉
  隐藏提示「导出前请保存画布」（62b-multiselect-styles.json 精确
  computed style）。同截图证实多选时不渲染空节点生成面板。
- SOURCE_FACT (batch 62, 选区包围盒与连接线): 多选包围盒样式 =
  bg rgba(255,255,255,0.04) + 1px dashed rgba(255,255,255,0.2) +
  border-radius 40px，几何为选中卡片包围盒四周外扩 40px
  （62b-multiselect-styles.json computed style + 截图几何）。
  CLONE_DECISION: xyflow v12 原生 nodesselection-rect 仅 marquee 结束后
  渲染，shift+click 多选无（源站两种方式均显示）——复刻侧 CSS 覆写
  原生路径 + JimengSelectionOutline 组件补齐 shift+click 路径；
  outline 仅视觉 (pointer-events:none)，源站包围盒可拖拽整体移动未复刻。
  两卡片间隙在双端节点同时选中时出现 1px 蓝色连接段（截图像素采样
  合成值 ≈ rgb(35,108,172)；单选/无选同位置无连线；源站无
  .react-flow__edge DOM，连线宿主元素未定位）。复刻: JimengEdge
  双端 selected 时 stroke rgb(35,108,172) 1px。多选工具条
  编组=groupSelected；布局 下拉内容源站未提取（CLONE_DECISION: 复刻
  提供「自动排列」——选中节点按 x 排成一行，y 对齐选区最小值，单条历史）。
- 观测 (batch 62, 未复刻): 源站视频节点在媒体 URL 失效后呈现
  「视频播放失败」+ 重试按钮错误态（62-first-frame-result.png 中央
  文案与 hover 提示）；复刻侧 media 为本地 data URI 无失效路径，
  留档待 mock 触发器批次再实现。
- SOURCE_FACT (batch 63, 布局菜单): 多选工具条「布局」下拉为两项——
  宫格布局 / 智能布局（63-layout-menu.png，项 172×38 白字 13px）。
  CLONE_DECISION: 排列算法未运行提取（运行会改动用户画布内容位置），
  复刻语义为 宫格=ceil(√n) 列网格、智能=单行 (y 对齐、间距 80)。
- SOURCE_FACT (batch 63, 编组卡片与解除编组): 源站 编组 创建真实
  group 父节点（react-flow__node-group，aria-label「组 node: 编组 N」，
  顶栏节点计数 +1）：卡片含「编组 N」标题（图标+文字，卡片左上方），
  面板比成员包围盒大一圈（~64px 边距）bg 略亮于画布，失焦仍可见；
  选中时白描边 + 四角圆形手柄。编组选中后多选工具条切换为
  「解除编组 ｜ 布局∨ ｜ 背景色 ｜ ↓(禁用)」（63-after-group.png /
  63-group-selected-toolbar）。复刻: 保留 groupId 标记模型 (batch 39
  架构 CLONE_DECISION)，以 JimengGroupFrames 视觉层近似卡片
  (标题+面板+描边+四角手柄，pointer-events:none，面板绘制于画布上方
  — 成员卡片上的着色极浅)；工具条按选中集是否同组切换 编组/解除编组
  + 背景色；groupSelected 记录 groupNames「编组 N」。
- SOURCE_FACT (batch 63, 背色调色板): 背景色 钮弹出 rgb(38,38,38)
  横排 6 格圆角面板——无颜色 + 青绿 #25C3D9 / 靛蓝 #656FF8 /
  紫 #B55CF8 / 橙 #FB883A / 黄 #FDD135（63-palette-zoom.png 像素采样；
  与 batch 31 节点标记五色同族但色值不同）。复刻: setGroupColor
  (无颜色=清除)，tint 以 16% 透明度混合进组卡片面板 (实色混合比例
  未提取，CLONE_DECISION)。
- SOURCE_FACT (batch 65, 编组交互语义, 只读验证): 源站点击编组成员卡片
  仅选中该成员节点（非整组，与我方 groupId 模型一致）；拖拽组面板空白
  区（两卡片间隙）不移动任何节点（65-group-interactions.json）。
  复刻: 语义一致，无需改动；batch 65 验证器锁定合同——组标题编号
  「编组 1」→ 解除编组 → 重建为「编组 2」（groupNames 序号跨解组
  持久，CLONE_DECISION 同源站「视频 N」计数习惯）。
- 测试 (batch 65): 组交互语义锁定验证器（成员单选/间隙拖拽不动/
  编组编号递增）。
- SOURCE_FACT (batch 64, 多选右键菜单): ≥2 选中时右键节点弹多选变体菜单
  (rgb(38,38,38) 200×340)——复制⌘C / 复制副本⌘D / 粘贴⌘V ｜ 编组 ｜
  下载(禁用，隐藏提示「导出前请保存画布」) ｜ 重做⌘⇧Z / 撤销⌘Z /
  删除⌫；无 保存到主体库 项 (64-multiselect-contextmenu.png)。
  复刻: JimengContextMenu multi 变体；多选 复制副本 = 剪贴板中转
  copyNodes+pasteNodes (相对布局 +60 偏移，单条历史)；编组 接
  groupSelected。提取备注: 源站多选时右键被 nodesselection-rect 拦截
  (其悬浮于节点之上、可拖拽移动整个选区——源站选择容器是交互层，
  我方 outline 为 pointer-events:none CLONE_DECISION)，需原生鼠标
  事件绕过 actionability 检查。
- SOURCE_FACT (batch 66, 保存状态门控下载): 三张对照截图揭示统一规律 —
  顶栏 已保存 时单选工具条下载可用（62-first-frame-result.png 图标亮色、
  62-frame-menu-status.png「节点 2 ｜ 已保存」）；顶栏 保存中… 时多选
  工具条下载禁用 rgba(255,255,255,0.2)（62-multiselect.png）且带隐藏
  提示「导出前请保存画布」。CLONE_DECISION: 单选工具条在 保存中… 的
  状态未被源站捕获（自动保存太快），统一规则为 下载受保存状态门控，
  应用于 单选工具条 / 多选工具条 / 右键菜单 三处下载钮。复刻: store
  markDirty（内容变更 → project.saved=false，mock 自动保存 2s → true；
  选中/播放/静音不脏化），JimengTopBar 已有 已保存/保存中… 渲染。
  测试注: 拖拽 2px 低于 xyflow 阈值不触发 position 变更，验证器以
  30px 往返拖拽制造脏态（净位移 0，容差放宽至 2.5px）。
- SOURCE_FACT (batch 67, 媒体失效态实现): 源站视频资源彻底失效后
  完整错误态可见（67-cap-state.png）——海报上方居中「视频播放失败」
  12px white/85 + 白底药丸钮「重试播放视频」（黑字 12px，hover 变暗）。
  复刻: mediaError data 旗标 + setMediaError action（不脏化画布），
  覆盖层渲染于海报上方（任务/生成中遮罩优先）；重试点击清除错误并
  从头重播。触发途径: 复刻侧无自然失效路径，测试经 dev-only
  window.__jimengStore hook 驱动（生产构建不挂载）。
- CLONE_DECISION (batch 67, 已编组选中右键菜单变体): 选中集为同一编组
  时右键菜单 编组→解除编组。源站提取两次被 nodesselection-rect 拦截
  （67-image-grouped.json grouped_contextmenu 为空），语义与多选工具条
  的 编组/解除编组 切换保持一致。提取备注: 源站 截取帧 下拉在视频
  失效后不再弹出（资源依赖），媒体相关提取通道自此受限。
  图片节点工具条提取（经 首帧 造图后选中）同因受阻，留档待源视频
  可播放窗口再试。
- SOURCE_FACT (batch 68, 左栏 aria-label + 文本节点默认): 左栏按钮
  aria-label 依次为 文本/图片/视频/音频/时间线/主体/导演台(Beta)/
  资产库/上传（68-rail.json）——修正此前 文字/分镜/数字人/智能体/
  素材库 的近似标签。点击 文本 在视口中心创建文本节点（标题 文本 1、
  选中无工具条、占位 双击编辑文本 (white/40)、T 字形标题图标、
  实测 ~328×340 (68-newnode-selected.png)）。复刻: 标签对齐、
  insertAtCenter 按各节点默认尺寸的一半回退（原硬编码 -280/-160 使
  非视频节点偏心）、文本节点默认尺寸/占位/图标/空态色对齐。
  测试注: batch 38 的多选首击落在视频中央播放圆钮上
  (stopPropagation 吞掉点击)，验证器改点 (中心-120,+40)；撤销恢复的
  选中节点 z 升高会遮挡后续交互，补空白点击清除选择。

- SOURCE_FACT (batch 41, 生成面板模型选择): 源站模型选择下拉已提取——
  8 个模型（Seedance 2.5 / 2.0 mini / 2.0 Fast VIP / 2.0 VIP / 1.0 Fast、
  MiniMax H3、HappyHorse 1.1、Wan 3.0）各带 name + description；点击开
  listbox，选中更新文案并关闭。
- SOURCE_FACT (batch 42, 组合菜单): 比例按钮打开组合菜单——选择比例
  21:9/16:9/4:3/1:1/3:4/9:16、选择分辨率 720P/1080P/4K、选择生成数量
  1-4；全能参考切换 首尾帧/全能参考。CLONE_DECISION: 时长选项 4s 为
  提取值、8s/12s 为外推。三个选择器可点且状态更新。
- 测试 (batch 43, 无新行为): 高级滑杆拖拽端到端覆盖——拖到端点
  27690 / 起始 6160 并在释放后保持（batch 28 拖拽跟随实现的验证批）。
- CLONE_DECISION (batch 46 语义演进, 见 §9): ⌘A 全选 + Escape 取消
  选择并关闭全屏预览（previewNodeId 提升到 store 修复 Escape 竞态）。
- 复刻 (batch 47, mock): 音频节点播放交互——播放切换波形点亮推进、
  暂停冻结、播完自停归零。
- SOURCE_FACT (batch 56, 框选语义): 空白左键拖拽绘制 marquee 框选，
  释放选中框内节点——即梦空白拖拽是框选而非平移（与 LibTV 画布的
  空白拖拽 no-op + Shift+拖拽框选语义相反，跨站点差异记录）。复刻:
  selectionOnDrag 启用、panOnDrag 保持中键；onNodesChange 重构为
  xyflow 持有 selected 旗标、store 仅镜像 selectedNodeId（修复
  marquee/store 选中竞态）；batch 56 验证器断言 marquee 选中 ≥2 且
  中键拖拽仍平移。
- 复刻 (batch 49, 诚实反馈补全): 工具条 下载 / 保存到主体库 补 mock
  toast 反馈（真实下载/写库维持 BLOCKED_BY_FIXTURE）——工具条 9 项
  自此全部有 UX 反馈。决策记录（用户指正）: 订阅页 tab 切换半成品
  回退——当前登录用户已是会员，订阅计费非复刻重心。
- 复刻 (batch 50, 生成流程闭环): 生成面板 生成 提交 generateInto(id,
  prompt)——节点进入 generating（spinner 蒙层 + 生成中），3s mock
  完成出 poster + 00:00/00:06（source: 'generated'）。
- 测试 (batch 51): 生成完成后新节点工具条行为验证——7 项 + 分隔线、
  title tag、时间行、gen panel 消失；NodeToolbar portal 作用域入档。
- 复刻 (batch 53, mock 任务生命周期收口): startTask 任务 4s 后自动
  完成——处理中蒙层（spinner + 处理中）清除，mock 任务生命周期闭合
  （验证器含任务中/完成后两态断言）。
- 复刻 (batch 57, 全交互审计): 零控制台错误的完整交互审计；审计发现
  的 Escape 修复——workspace Escape 分支统一清除 repaint/edit/infer/
  framePicker/trim 编辑态（SOURCE_FACT-verified UX：源站 Esc 退出编辑
  态；此前 editNodeId 残留会阻塞 视频编辑 后的工具条恢复）。
- 复刻 (batch 52): 多选复制/粘贴——右键菜单 复制 复制全部选中节点
  （单个走原路径）；剪贴板泛化为 {nodes, edges} 并保留内部连线；
  粘贴经 id 重映射恢复相对布局；pasteNode 更名 pasteNodes（单条
  历史入栈）。
- SOURCE_FACT (batch 44): 修剪面板起点把手向右拖动 → 左侧时间读数前进、
  选区时长缩短 —— 与我方实现语义一致 (只读验证，源站把手几何未逐帧提取)。
- CLONE_DECISION (batch 44 实现): applyTrim 接受起点偏移，确认修剪后节点
  currentTime 落在新起点并入撤销栈。
- CLONE_DECISION (batch 45): 标题 span 带原生 title 属性 (完整文件名，
  悬停显示浏览器原生提示) —— 源站只读提取证实同构。
- SOURCE_FACT (batch 48 提取/验证): 文字节点行内编辑提交写回 store
  (updateNodeData 泛化为任意节点类型)；编辑内容在选择切换后保持。
- SOURCE_FACT (batch 55, 框选语义): 源站 Shift+左键拖拽空白画布绘制白色细线
  框选矩形 (marquee)；释放后选区内节点选中。复刻: xyflow v12 默认
  selectionKeyCode=Shift 绘制相同矩形 ✓；但释放后的节点选中应用在复刻侧
  未生效 (已知偏差，待排查 onNodesChange select 路径与 xyflow 内部同步)。
- BLOCKED_BY_FIXTURE: 智能超清、补帧（会提交生成任务消耗积分）；
  下载（真实文件）、保存到主体库（写库）→ 工具条上保留按钮但无功能面板。

## 9. 阶段性留档 (batch 44-48)

- Batch 44: 修剪起点把手拖动 + 起点偏移语义 (applyTrim 三参)。
- Batch 45: 节点标题原生悬停提示 (title 属性)。
- Batch 46: ⌘A 全选 + Escape 取消选择；修复全屏预览 Escape 竞态
  (previewNodeId 提升到 store —— workspace 取消选择处理先于预览自身
  监听器运行，本地状态驱动会导致预览无法用 Escape 关闭)。
- Batch 47: 音频节点播放交互 (波形点亮推进/暂停冻结/播完自停归零)。
- Batch 48: 文字节点行内编辑提交写回 store (updateNodeData 泛化)。
- Batch 62: 截取帧 首帧/尾帧 直出图片节点 (captureFrame 避让落位)；
  多选组合工具条 (N 节点/编组/布局∨/禁用下载) + nodesselection-rect
  覆写 (dashed white/20 r40) + 双端选中蓝色连线；gen panel 多选隐藏。
  证据: docs/design-references/jimeng/62-*.png / 62*.json。
- Batch 63: 布局菜单 宫格布局/智能布局；编组卡片视觉层 (编组 N 标题+
  面板+描边+四角手柄) + 工具条 解除编组/背景色 变体 + 调色板
  (无颜色+5 色) + groupNames/groupColors store。
  证据: docs/design-references/jimeng/63-*.png / 63-*.json。
- Batch 64: 多选右键菜单变体 (复制/复制副本/粘贴｜编组｜下载禁｜
  重做/撤销/删除，无 保存到主体库)；多选 复制副本=copyNodes+pasteNodes。
  证据: docs/design-references/jimeng/64-*.png / 64-*.json。
- Batch 66: 下载按钮保存状态门控 (保存中… 禁用+提示 / 已保存 可用)；
  markDirty + 2s mock 自动保存；覆盖 单选工具条/多选工具条/右键菜单。
  证据: docs/design-references/jimeng/62-frame-menu-status.png 等 +
  verify-jimeng-batch66.py。
- Batch 67: 视频播放失败错误态 (mediaError + 重试播放视频 药丸) +
  已编组选中右键菜单 解除编组 变体 + dev-only store window hook。
  证据: docs/design-references/jimeng/67-*.png + 67-image-grouped.json。
- Batch 68: 左栏标签对齐 aria-label (文本/时间线/主体/导演台/资产库) +
  文本节点默认值 (328×340、双击编辑文本、Type 图标、视口中心插入)。
  证据: docs/design-references/jimeng/68-*.png / 68-rail.json。
- Batch 69: 全量质量门 — verify 1..68 全绿 (60 verifier + 老式 1/2/3/5/6)，
  截图刷新入库 (commit 3306154)。
- BLOCKED_BY_FIXTURE 再确认 (batch 90): 离线同步完成 + 播放激活后
  复探 截取帧 下拉——仍不展开；且播放交互后视频再次进入
  「视频播放失败」态，形成「重试→可播一次→再失效」循环。
  图片节点工具条与首帧/尾帧源站行为提取持续受阻，直到资源被
  平台恢复或重新上传。我方截取帧/进度条/播放器实现维持既有
  batch 62-85 合同不变。
- Batch 100 (复探): 截取帧下拉仍不展开、卡片无时间读数——与 batch 84/90
  判定一致，无新提取面。回归部分由 batch 99 全量扫覆盖 (此后零代码
  变化，不重复执行)。
- Batch 101/102/104 轮空复查: 低频维护循环持续——退出码全量扫描
  (batch 101, 82 ok) 与源站复探 (batch 102/104) 均无变化；并行开发
  者提交 (batch 510-517 focused fixtures) 不触及 jimeng 文件
  (git diff 7eea3c5..HEAD -- src/components/jimeng 为空)。
- Batch 98 (收尾): 订阅管理页与促销弹窗已关闭 (再想想/页面×)，
  画布基线保持 2 节点、缩放 100%；视口平移残留为视图状态非内容
  变化，不再扰动。截取帧下拉复探仍未展开 (维持 batch 84 判定)。
- SOURCE_FACT (batch 91, 小地图): 底部 dock 演进为 [选择工具][小地图]
  ｜缩放百分比 (91-minimap.json——布局 已并入多选工具条、同步 由自动
  保存取代)；小地图 点击切换左下 164×154 rgb(13,13,13) r8 面板
  (内 156×114 white/8% r6 地图区)。
- Batch 91 (复刻): dock 重构为上述布局 + xyflow <MiniMap> 面板
  (pannable、nodeColor 灰、mask 黑/45) + 验证器 (布局/尺寸/开关)。
  21 批旧 布局/同步 dock 钮移除记录在案 (站点演进)。
- Batch 92 (小地图语义实证 + 对齐): 源站小地图 拖拽平移画布 ✓、
  滚轮缩放画布 ✓ (92-minimap-sem.json viewport transform 前后对比)；
  地图区即 portal 目标 canvas-minimap-portal-target 156×114。
  复刻: MiniMap zoomable 由 false 修正为开启 (pannable 原本一致) +
  验证器 (拖拽/滚轮 viewport 变化断言)。
- SOURCE_FACT (batch 93, dock 连线开关): dock 实为四钮——选择工具
  (canvas-dock-pointer)/小地图 (canvas-dock-minimap)/显示连线
  (canvas-dock-lines)/Zoom options；显示连线 为连线显隐开关。
  复刻: store edgesVisible + dock Spline 图标钮 + JimengFlow
  edges 条件渲染；图标用 lucide Spline 近似 (CLONE_DECISION)。
- Batch 94 (缩放菜单一致性): 源站缩放菜单为 5 项 — 适配画布⇧1/
  缩放至选中项⇧2/缩放至50%/缩放至100%⌘1/缩放至200% (94-zoom-menu.png
  / 94-zoom-menu.json)，早期记录的 放大视图⌘+/缩小视图⌘− 菜单项已
  从源站菜单移除 (⌘± 快捷键仍在)。复刻: JimengZoomMenu 移除这两项
  (batch 7 verifier 同步)，源站画布缩放已还原 100%。
- Batch 96 (顶栏演进对齐): 源站顶栏现为 [搜索(canvas-search)][生成历史
  (canvas-history)]｜[Credits 基础会员][用户菜单]——帮助/? 钮已移除，
  用户菜单 展开个人资料弹层 (西卡文案馆/基础会员/到期 2026.10.12/
  积分详情 725，96-user-menu.png)。复刻: 顶栏 pill 改为 搜索+生成历史
  双钮 (History 图标)、帮助 钮移除 (JimengHelpMenu 暂留组件文件，
  由头像共用实例继续承载)、账号菜单 aria 改 用户菜单、新增最小
  JimengSearchOverlay (输入框+暂无搜索结果，内容 BLOCKED_BY_FIXTURE——
- 观测 (batch 97, 用户菜单去向 + 订阅管理页): 点击 用户菜单 打开的是
  订阅管理页 (账号头 西卡文案馆✦/基础会员/到期 2026.10.12 01:31/积分
  详情 725/购买积分/订阅管理 + Seedance 2.5 触底价促销弹窗 + 四档
  会员卡 188/56?/…/8189 每月积分 725/2210/12320/54600)，97-profile-
  open.png。按用户既定决策 (batch 49: 订阅计费非复刻重心) 除牌，
  不复刻；已关闭弹窗与页面，源站画布还原基线。
- 证伪 (batch 97, 卡片时间格式): step35 textContent 读到 00:06/00:06
  无空格曾疑格式差异，但 77-video-state.png 截图证实视觉为
  「00:00 / 00:06」带空格 (textContent 拼接假信号)——我方格式正确，
  无需改动。
  33-search-overlay.png 实为生成历史面板，搜索覆盖层从未被捕获)。
- Batch 93: 显示连线开关 + 验证器 (经 + 手柄插视频建边 → 隐/显断言)。
- SOURCE_FACT (batch 70, 顶栏节点计数): 顶栏 节点{N} 随画布实时变化 —
  源站截图链: 基线 节点 2 (62-frame-menu-status.png) → 建 image 节点后
  节点 3 (62-multiselect.png 顶栏) → 编组后 节点 3 (63-after-group.png,
  组节点计数 +1)。复刻: JimengTopBar 节点数改为 store nodes.length
  实时映射。CLONE_DECISION: 我方编组为 groupId 标记模型 (无组节点)，
  编组不使计数 +1 (源站 +1)。
- Batch 70: 顶栏 节点{N} 实时映射 + 验证器 (插入/撤销/截取帧 计数断言)。
  证据: verify-jimeng-batch70.py + jimeng-clone-batch70-node-count.png。
- Batch 71: 编组计数语义补齐 — 每个编组使顶栏 节点{N} +1
  (nodes.length + groupId 去重数，SOURCE_FACT 63-after-group.png
  节点 3 = 2 卡片 + 1 组)；解除编组回落。verify-jimeng-batch71.py。
- Batch 72: 资产库模态 (双 tab/筛选/搜索/骨架网格/空态/禁用确认) +
  Escape 统一关闭。证据: docs/design-references/jimeng/72-*.png +
  72-assets.json。
- Batch 74 (重构, 无行为变更): JimengVideoNode (556 行) 拆分为
  JimengVideoTitleRow (标题行+颜色标记) + JimengVideoMediaCard
  (海报/控制条/进度/遮罩/错误态) + 编排器；门: tsc/lint/build +
  视频节点相关 20 个 verifier 全绿。
- SOURCE_FACT (batch 75, 资产库筛选空态): 资产 tab 内切换筛选改变空态
  文案 — 视频→暂无视频素材、音频→暂无音频素材 (75-assets-deep.json
  实证；文档 未捕获按同模式外推)；主体 tab 固定 暂无主体素材。
  复刻: 空态文案改为 暂无{当前筛选}素材 (batch 72 的 tab-only 映射
  修正)。时间/筛选 图标钮的弹出层未捕获 (点击无可见变化，留档)。
- Batch 75: 资产库筛选空态跟随 + 验证器 (四种筛选切换断言 +
  主体 tab 固定文案)。
- SOURCE_FACT (batch 76, 主体 tab 实际内容): 主体 tab 用单个「全部」
  筛选替换 图片/视频/音频/文档 行 (白色 active + 下划线)；空态为
  「没有可用主体」 white/35 (76-subject-deep.json / 76-subject-tab.png，
  修正 batch 75 的「暂无主体素材」外推)；确认钮保持禁用；资产 tab
  转为 inactive white/70。文档筛选空态实证「暂无文档素材」
  (batch 75 外推正确)。复刻: 主体 tab 渲染 全部 单筛选 + 独立空态，
  切回资产 tab 恢复四筛选。
- Batch 76: 主体 tab 全部筛选 + 没有可用主体 空态 + 验证器
  (75 verifier 同步更新合同)。
- Batch 77: 全量回归 1..76 全绿（72 verifier），截图刷新 (commit 5add09c)。
- SOURCE_FACT (batch 78, 资产库骨架格与图标 tooltip): 空态骨架格
  124×124、5 列、间距 2px、bg white/4%、r2 (右对齐 630px 网格区)；
  时间/筛选 图标钮 hover 显示 radix 式 tooltip 药丸 (56×36, 按钮下方,
  文本即 时间/筛选) (78-skeleton-hover.json)。复刻: 骨架网格参数对齐
  (630px 右对齐 grid、aspect-square、gap 2px)、图标钮 group-hover
  tooltip 药丸 (此前仅原生 title)。
- Batch 86 (观察, 只读验证): 卡片 Seek 滑杆无 thumb (纯 track+fill
  药丸，拖拽中亦无)，拖到中点时间正确变 00:03/00:06 (与我方 scrub
  一致)；全屏播放器静音钮语义 Unmute video ↔ Mute video toggle
  (与我方 取消静音/静音 一致，aria 文案差异为 CLONE_DECISION 中文
- SOURCE_FACT (batch 87, 节点重命名): 标题行即 Rename 按钮 (aria
  "Rename <标题>")——点击打开行内 input (300px、预填现名、white/70)，
  Enter 提交并全局生效 (Seek aria 同步)，⌘Z 可撤销 (87-rename-open.png)。
  主体: Add tags 24×24 (batch 31 颜色标记同位)。
- Batch 87 (复刻): JimengVideoTitleRow 点击标题进入行内重命名
  (renameNode 单条历史入撤销栈、Enter/失焦提交、Escape 取消、
  双击仍开插入菜单并退出重命名态) + 验证器。
- Batch 88 (重命名全节点扩展): 源站文本节点标题同为 Rename 按钮
  ("Rename 文本 1" + Add tags 实证)——复刻将行内重命名抽为共享
  JimengNodeTitle 组件，应用于 视频/文本/音频/图片 全部节点标题行；
  验证器覆盖 文本/音频 重命名 + 撤销链 (重命名与插入各占一条历史)。
  证据: 88 文本重命名截图。
  对照: 源站卡片控制条按钮集 播放(Pause)/Mute video/Enter browser
  full screen 与我方 播放/静音/全屏 结构一致 (aria 文案英文 vs
  中文为 CLONE_DECISION)。
  界面)。退出全屏后卡片控制条未发现 静音 aria (源站卡片控件再度
  变化，留档)。证据: 86-seek-hover/drag.png、86-thumb-mute.json。
- Batch 79 (遮罩实证): 资产库模态背景遮罩采样 — 画布 rgb(13,13,13) 处
  开模态后四点均 (6,6,6)，反推 alpha ≈ 0.54，复刻由 bg-black/50 修正为
  bg-black/55。
- SOURCE_FACT (batch 82, 离线编辑冲突对话框复刻): 81-after-reload-state.png
  的对话框落地 — 居中 545px 模态 rgb(25,25,25) r16：标题 发现离线编辑、
  正文 你在离线状态下对当前画布做了修改，这些修改尚未同步到服务器。、
  右下 丢弃修改 (灰底 white/10)/保留并同步 (白底黑字主按钮)，遮罩
  black/55。复刻: JimengOfflineDialog + store offlineDialogOpen；
  触发经 dev window hook (复刻侧无真实离线态)；两按钮均 mock toast
- SOURCE_FACT (batch 85, 进度条演进): 视频卡片进度条由 2px 演进为
  5px 药丸 (track white/16% r25、fill white/96%，全卡宽)；全屏播放
  器底部有全宽 5px 可 seek 进度条 (12px 命中区) (85-seek.json)。
  复刻: 卡片进度条参数对齐；JimengVideoPreview 新增可 seek 进度条
- Batch 106 (回归方法修正 + 隐藏失败清零): 发现早期轮转/全量扫描用
「末行文本匹配」判定，locator 超时失败的末行是 call log 而被误报
  ok——batch 99/101 两轮「全绿」各掩盖了 1-2 个超时失败。改用
  退出码判定重跑 1..96，暴露并修复 batch 22 (账号菜单→用户菜单)
  与 batch 57 (帮助→用户菜单头像路径) 两处 stale 引用；82 verifier
  现为真实的全绿。
  (此前缺失)。
- Batch 85: 进度条对齐 + 验证器 (卡片样式断言 + 预览 50% seek)。
  反馈后关闭；Escape 统一分支关闭。
- SOURCE_FACT (batch 80, 全屏播放器): 点全屏进入浏览器 Fullscreen API
  (aria Exit browser full screen)，覆盖层 bg rgba(0,0,0,0.6) 透出画布，
  进入即自动静音播放 (aria Play <节点标题> / Unmute video)；底部
  36px 控制条：Play 16px + 当前/时长时间分列 + Unmute/Exit 36×36
  (80-preview.png)。复刻: JimengVideoPreview 背景改 black/60、
  进入自动播放/退出暂停、控制条 36px + 16px 图标 + 时间分列；
  浏览器 Fullscreen API 以应用内覆盖层近似 (CLONE_DECISION)。
- Batch 81 (观察 + 提取受阻更新): 源站视频经 重试播放 完全恢复
  （浏览器全屏播放 00:02/00:06 可见），但随后的页面 reload 触发
  「发现离线编辑」冲突对话框（你在离线状态下对当前画布做了修改，
  这些修改尚未同步到服务器 + 丢弃修改/保留并同步 双按钮）——选
  保留并同步 后会话恢复。图片节点工具条提取仍受阻：截取帧 下拉
  （radix menu, aria-haspopup=menu）在离线同步后的会话中点击/hover/
  键盘均不展开 (81-diag4.png)，疑似房间权限或站点 A/B 变化。
  旧行为对照: batch 62 时同坐标同视频可正常展开。
  离线编辑冲突对话框为新 surface，已截图 (81-after-reload-state.png)
- BLOCKED_BY_FIXTURE 更新 (batch 84): 完全新加载会话 + 播放中
  (00:01/00:06) 两条件下，源站 截取帧 下拉均不展开 (aria-haspopup=menu、
  data-state 恒 closed、无新元素挂载)——判定为源站侧变化/缺陷，
  非会话降级。我方 截取帧 行为维持 batch 62 时代源站证据实现的
  合同不变 (首帧/尾帧直出图片节点、自定义帧选择器)。
  留档，待后续批次复刻。
- Batch 80: 全屏播放器对齐 (black/60 背景、自动静音播放、36px 控制条、时间分列) + 验证器 (27 verifier 合同同步)。
- 观测 (batch 77, 重试播放行为): 源站 重试播放视频 点击后错误横幅清除，
  但资源已死时视频进入「00:00 / 00:00」无时长空载态（中央播放圆钮
  消失、截取帧 下拉不再弹出）——媒体类提取（图片节点工具条）继续
  受阻 (BLOCKED_BY_FIXTURE，待资源真正恢复)。我方重试语义（清除
  错误 + 从头重播，时长保留 6s）与此一致仅时长差异 (CLONE_DECISION)。
- SOURCE_FACT (batch 73, 左栏标签飞出 + 本地上传): 悬停左栏时图标右侧
  显示标签飞出层 (73-upload-panel.png: 文本/图片/…/上传 与图标逐行
  对齐)。上传 点击打开系统多选文件选择器 (filechooser multiple 实证)，
  选中文件即为本地上传视频节点 (现有节点标题 sb_... 即文件名形态)。
  复刻: rail group-hover 标签飞出层；隐藏 file input (multiple,
  accept video/image) → addLocalUpload —— 文件名为标题、mock 海报、
  6s、本地上传视频节点落于视口中心 (多文件斜向错开)，入撤销栈。
- Batch 73: 左栏飞出标签 + 本地上传闭环验证器
  (filechooser set_files → 节点创建 → 撤销)。
- Batch 69b: 全量回归 1..68 二次全绿（含 62/64 合同更新后），截图刷新
  (commit 3306154)。
- SOURCE_FACT (batch 72, 资产库模态): 左栏 资产库 点击打开居中模态 —
  801×620, bg rgb(26,26,26), r20；顶部 资产(active white/8%)/主体 双 tab +
  右上 ×；筛选 图片(active 下划线)/视频/音频/文档 (58×36, inactive
  white/70) + 搜索输入 200×36 + 时间/筛选 图标钮 28×28；空态
  「暂无图片素材」 white/35 叠骨架网格；底栏 已选择 0 个素材 white/60 +
  确认钮 80×36 (bg white/16% text white/20 禁用)（72-assets-panel.png /
  72-assets.json）。隐藏英文 aria「Import assets / Choose assets from
  Dreamina」入档未渲染。复刻: JimengAssetsModal + store assetsOpen；
  主体/其它筛选空态文案外推 (CLONE_DECISION)。实现注: 模态自身
  window Escape 监听在真实按键下失效（合成事件可触发，原因未定），
  改由 workspace 统一 Escape 分支关闭 (batch 57 先例)。
- 回归状态: verify-jimeng-batch1..48 共 48 个 verifier 全部 PASS；
  npm run check (lint + typecheck + build) 通过。
- 环境备注: dev server Fast Refresh 会在文件编辑后重置页面 store 状态，
  verifier 需在无并发编辑窗口内运行；GitHub 推送在本地代理 (127.0.0.1
  :1234/1235) 离线时可用 `git -c http.proxy= -c https.proxy=
  -c http.version=HTTP/1.1 push` 直连重试。
- SOURCE_FACT (batch 55, 框选语义): 源站 Shift+左键拖拽空白画布绘制白色细线
  框选矩形 (marquee)；释放后选区内节点选中。复刻: xyflow v12 默认
  selectionKeyCode=Shift 绘制相同矩形 ✓；但释放后的节点选中应用在复刻侧
  未生效 (已知偏差，待排查 onNodesChange select 路径与 xyflow 内部同步)。
- BLOCKED_BY_FIXTURE: 智能超清、补帧（会提交生成任务消耗积分）；
  下载（真实文件）、保存到主体库（写库）→ 工具条上保留按钮但无功能面板。

## 8. 复刻侧实现映射（CLONE_DECISION）

- 路由: `/jimeng` → redirect `/jimeng/canvas/demo`（同构 `/frameos`）。
- Store: `src/store/jimengStore.ts`（与 canvasStore/frameosStore 隔离；
  选中态以 `selectedNodeId` 单一来源回填，规避 applyNodeChanges 重置问题）。
- 样式: `src/app/jimeng-canvas.css`（token 表见 §3）；组件 `src/components/jimeng/`。
- 验证: `scripts/verify-jimeng-batch1.py` … `verify-jimeng-batch48.py`
  （每批一个验证器；dev server 4317；截图入 `docs/design-references/jimeng/`。
  batch 1 在 LibTV 维护集内；batch 2+ 验证器由并行路线开发者维护）。
