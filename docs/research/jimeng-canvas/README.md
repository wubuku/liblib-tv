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
- SOURCE_FACT (batch 195 复测): 截取帧下拉恢复可展开（首帧/尾帧/自定义三项不变，
  可见菜单 73×65 @ 按钮下方 6px、行距 21px、13px 白字；146×130 为其外层缩放
  容器）。视频工具条 7 条目几何复测一致（局部重拍 106 / 智能超清 106 /
  视频编辑 106 / 截取帧 91 / 补帧 80 / 视频修剪 88 / 提示词反推 101，panel
  775×40，条目间距 2px）。
- SOURCE_FACT (batch 195, 图片节点工具条): 截取帧产出的图片节点（569×320，
  同视频卡尺寸；标题「{视频标题}_{首帧|尾帧}」下划线连接）选中后上方弹出自有
  工具条——面板与节点同宽（569×40）、同深色药丸；条目 智能改图✦ / 扩图 /
  智能超清 / 抠图 / 多角度 / 工具∨（仅智能改图带 14×14 VIP 菱标；智能超清
  此处无 VIP 标，区别于视频工具条；工具带 12×12 下拉箭头）；无分隔线、
  无全屏/下载尾钮。产出图片节点带血缘连线（video→image 1 条）且落点为行内
  右移避让后的空位（+80 间距）。工具∨ 菜单项未捕获（单击未展开，
  BLOCKED_BY_EXTRACTION）。
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
- Batch 110 (维护轮): 退出码全量回归 1..96 —— 82 verifier 零失败；
  源站复探无变化（截取帧下拉仍关闭、视频空闲），维持既有受阻判定。
- Batch 114 (AI 抽屉演进复查): 源站「与 AI 对话」抽屉重新提取
  (114-ai-drawer.png / 114-ai-drawer.json)——右侧 400px 抽屉
  (rgba(32,32,32,0.8))、「新会话」头部+历史/展开图标、居中空态
  「探索更多专业创作模式」+ 5 技能 chips、底部输入卡片 (占位含
  "/"使用技能/@添加主体/Agent 协作 + @ 行内 chip + 底行
  +/使用技能/@/白色圆形发送钮)——与我方 JimengAiDrawer (batch 12)
  结构一致，无实现差距；batch 12 verifier 回归通过。
- Batch 195 (图片节点工具条复刻, 阻塞解除): 源站 截取帧 下拉恢复展开
  （batch 84/90/100 受阻判定解除），补齐等待多轮的图片节点工具条提取
  （195-toolbar.json / 195-dropdown.json / 195-image-toolbar-full.json /
  195-census-after-frame.json，几何级证据；源站截图受页面持续渲染影响
  未获取，BLOCKED_BY_EXTRACTION 备注）并复刻:
  新增 `JimengImageNodeToolbar`（6 条目契约见 §6 batch 195 SOURCE_FACT，
  VIP/下拉箭头/无下载尾钮差异全部落地）；`captureFrame` 产出标题改为
  源站下划线约定 `「{视频标题}_{首帧|尾帧}」`；图片节点选中显示自有工具条
  (JimengImageNode 接线, soloSelected 门控, 各项 pushToast mock)。
  验证: verify-jimeng-batch97.py 新增（首帧→图片节点→工具条契约→撤销还原），
  受影响面回归 batch 2/34/62/66/70/82 全 PASS，npm run check 通过。
  工具∨ 菜单项与源站截图仍缺，后续轮次补提。
- Batch 196 (工具∨ 菜单补提失败 + 轮转): 图片工具条「工具∨」以三种触发路径
  （真实坐标 click / hover 1.5s / JS pointer+mouse 事件分派）均未展开菜单——
  在当前源站状态（上传视频空闲 + 断线重连恢复后）判定 BLOCKED_BY_EXTRACTION，
  clone 维持箭头视觉 + toast mock。另: 该页面状态下截图捕获必挂
  （playwright 高层 Page.screenshot 与 raw CDP Page.captureScreenshot 均超时，
  疑似视频元素持续解码占用合成器），源站截图留待页面空闲态再取。
  两轮变异周期均完整还原（画布回到 2 视频节点基线）。
  回归: batch 49-64 段 14/14 PASS（今日改动未覆盖面），零失败。
- Batch 197 (上传瞬态复刻): 批 195 提取的 census 曾捕获产出瞬间节点文本
  「正在上传图片 0%」(195-census-after-frame.json 上一轮现场)——源站截取帧
  产出先经历 1-2s 上传进度态再转常规图片节点。复刻: `uploadProgress`
  瞬态字段 (0 → 46 @0.5s → 100 @1.0s, mock setTimeout + setState,
  不产生脏态/撤销步；节点被删则定时器空转)，JimengImageNode 上传遮罩
  「正在上传图片 N%」(bg black/45 + 13px 白字, 布局为 CLONE_DECISION——
  源站仅文本级证据)，按 <100 判定显隐。
  验证: verify-jimeng-batch98.py (0% 起步 → ≤2.3s 消隐 → 标题保持
  「…_首帧」→ 撤销还原)；batch 97/62 回归 PASS。
- Batch 198 (全量质量门): 退出码全量扫 verify-jimeng-batch1..98 ——
  84 verifier 零失败 (含新增 97/98)，截图随扫刷新入库；
  并行 heartbeat 自动化 (batch 637-639) 与本轮提交交错合入，
  jimeng 面无冲突。npm run check 于 batch 197 已过 (此后 jimeng
  树无代码变化，不重复执行)。
- Batch 199 (截图阻塞定论 + docs 门禁): 源站页面截图第三种路径
  (raw CDP + clip 小区域 + captureBeyondViewport=false, 子进程 20s
  硬超时) 仍必挂——连同 playwright 高层与 raw CDP 全帧共三种路径
  均超时，当前页面态 (视频持续解码) 下源站截图正式定论
  BLOCKED_BY_EXTRACTION，后续仅在页面空闲态复测。图片工具条源站
  截图缺口随之维持几何级 JSON 证据。
  环境: 本轮 `npm run dev` 绑定 4317 (verifier 依赖端口)，由本循环
  持有；verify-docs.py 通过 (1003 files / 4398 links)。
- Batch 200 (§10 留档修复): 修复 cf1848c 引入的 §10 逐字符竖排损坏
  (656-1592 行 937 行重组为 26 行可读文本，无良好历史副本可还原)，
  快照内容刷新至 batch-200 状态 (84 verifier、图片工具条/上传瞬态
  已落地、受阻面重列)；全库扫描确认无其他文件同类损坏。
- Batch 201 (探针环境诊断 + 自定义帧选择器复验未遂):
  当日点击/截图间歇失效的根因定位——探针 Chrome 窗口曾退化为
  960×90 的 fullscreen 条带 (innerWidth/innerHeight 即 960/90，
  y>90 的所有坐标 elementFromPoint 返回 null)，Browser.setWindowBounds
  恢复 1680×960 后点击命中恢复；窗口恢复后 raw CDP 截图仍挂
  (合成器 wedged，疑视频解码占用)，截图 BLOCKED 判定不变。
  另: reload 后 workspace-preparing-state 遮罩期间点击全部无效，
  须轮询待其消失。截取帧下拉可打开，但点「自定义」行未展开
  帧选择器 (源站行为待复验；batch 9/10 提取证据与我方
  JimengFramePicker 实现维持有效)。两轮变异周期均完整还原
  (2 视频节点基线)。
- Batch 202 (自定义帧选择器复验 + 几何对齐): 下拉「自定义」行此前
  未展开系探针点击坐标落在相邻行 (y+53 误触截帧产出图片节点，已清理
  还原)；改用 JS 精确点击「自定义」元素后面板正常展开——旧 dump 过滤器
  排除了节点容器是「未见面板」的误判。完整几何提取 (202-custom-picker.json):
  面板与节点同宽 564×116、帧条 540×54 (64×36 缩略图平铺)、底行 ▶
  00:00/00:06 (12px) ｜ 截取帧 89×36 ｜ 提示「请至少截取 1 帧」(12px,
  batch 9 未记载的新文案) + 确认 82×36 r8 (禁用态 bg 白/16 + 字 白/20)。
  复刻: JimengFramePicker 面板宽度改为节点宽 (原固定 640)、新增未截取
  提示、确认禁用态修正为 bg 白/16 + 字 白/20、帧条高 54px。
  验证: verify-jimeng-batch99.py 新增 (面板宽/提示/禁用样式/截取门控/
  确认关闭)；batch 9/10/34 回归 PASS；npm run check 通过。
- Batch 203 (确认行为采样 + 语义修正): 源站帧选择器完整交互链采样
  (203-picker-interaction.json / 203-picker-confirm.json)——初始
  readout 00:00/00:06 + 提示 + 确认样式门控 (白/20, 无 disabled 属性)；
  帧条点击 → readout 00:03/00:06 (60%→3.6s 取整)；截取帧 → 提示消失 +
  确认变白底深字 rgb(26,26,26)；确认 → 选择器关闭 + **直出该帧图片
  节点** (非写回 currentTime——batch 34 旧「写回」语义系误采样，修正)。
  复刻: captureFrame 扩展 custom 分支 (标题「{视频}_自定义」，该标题
  后缀源站未采样为 CLONE_DECISION)，JimengFramePicker onConfirm 改为
  产出图片节点 (原 capturedFrame/currentTime 写回移除，媒体卡
  capturedFrame 徽标暂留待更清晰证据)；帧条补 data-testid=frame-strip
  (verifier 稳定定位——旧 .relative 选择器命中全屏外壳导致点击反选)。
  验证: verify-jimeng-batch100.py 新增 (全链路: 下拉→自定义→帧条→截取→
  确认→图片节点+连线→撤销)；batch 9/10/34/62/97/98/99 回归 7/7 PASS。
  探针备注: 源站视口持续向上漂移致工具栏滑出屏幕，操作前先 Shift+1
  适配画布 (batch 7 快捷键)；多次「下拉未展开」实为该漂移下的点击落空。
- Batch 204 (自定义产出标题采样): 源站确认产出的图片节点标题为
  「{视频}_截帧_1」(204-custom-title.json，aria 与节点文本一致)——
  后缀为 截帧_N 序号计数器。复刻对齐: captureFrame custom 分支产出
  「{视频}_截帧_{N}」，N = 同源已有截帧节点数 + 1 (重复截取的计数口径
  为 CLONE_DECISION，源站仅采样到首例 _1)。batch 34/100 verifier 断言
  同步更新，均 PASS。
- Batch 205 (全量质量门 + 误采样 UI 清除): 全量扫首轮 84/86——
  batch 35/36 失败均系 batch 203 语义修正的遗留：媒体卡「截取帧徽章」
  (跳转/清除) 以旧误采样行为为前提，确认直出图片节点后 capturedFrame
  已无写入方。清除: 移除 JimengVideoMediaCard 徽章块与 capturedFrame
  字段 (batch 35/36 旧 UI 系误采样产物，204-custom-title 佐证源站
  直出图片节点)；batch 35/36 verifier 改写为新契约 (确认→图片节点
  「_截帧_1」/选择器关闭/无徽章/撤销还原)。复扫 86/86 零失败，
  npm run check 通过，截图随扫刷新。
- Batch 206 (生成视频节点选中态采样 + 面板细节对齐): 源站「视频 1」
  (无资源生成视频节点) 选中 → 无视频式工具条，下方为生成面板
  (206-empty-video-selected.json / 206-genpanel-detail.json)。面板
  细节复测: 内边距 16 (原提取 17)、占位 14px 且「@主体」为行内
  白/[0.08] chip、底部行控件 12px、右侧价格签为「Current price」标签 +
  ✦56.56 (白/[0.69]，70px 裁切容器——源站自身即截断显示，原提取仅 ✦56)。
  复刻: JimengGenPanel 四项对齐 (pad16/占位叠加层含 chip/控件 12px/
  Current price 价格签；placeholder 属性保留置透明供 a11y 与验证器)。
  回归: batch 3/5/13/28/30/40/41/43/57/61 共 10/10 PASS。
- Batch 207 (视频工具条 svg 级复验): 与图片工具条同规格的 svg 级证据
  (207-video-toolbar-svg.json)——panel 775×40；局部重拍/智能超清/视频编辑/
  补帧 各 2 svg (16×16 图标 + 14×14 VIP 菱标 rgb(0,158,250))；截取帧
  2 svg (16×16 + 12×12 下拉箭头)；视频修剪/提示词反推 各 1 svg 无菱标；
  按钮宽 106/106/106/91/80/88/101 与 batch 195 提取一致。复刻侧
  JimengNodeToolbar 零漂移，无需改动。
- Batch 208 (截图解封 + 两处证据反转): 合成器恢复后源站截图重新可用
  (208-source-image-toolbar.png)。截图揭示两处批 195 误判并修正:
  ① 图片工具条实际带 分隔线+全屏预览+下载 32×32 尾钮 (无文字图标钮
  被 rawText 漏采)，JimengImageNodeToolbar 补齐尾钮 (下载沿用保存门控
  为 CLONE_DECISION)；② 画布出现真实边 DOM——未选中边 stroke
  rgb(0,142,229) 1px 实线 (208-edges.json，原「无 edge DOM」受阻判定
  解除)，JimengEdge 常态由 rgba(255,255,255,0.32)/1.5px 修正为
  rgb(0,142,229)/1px；截图另见端点小 + 圆 (悬停态推断，未 DOM 采样)。
  媒体卡细节采样入库 (208-video-card-detail.json)。batch 97 断言改写，
  97/62 回归 PASS。
- Batch 209 (工具∨ 菜单解封 + 视频卡悬停门控): 截图能力恢复后重试
  「工具」点击即成功展开菜单 (此前全部失败系视口漂移导致的点击落空，
  BLOCKED_BY_EXTRACTION 解除)。菜单采样 (209-tools-click.png /
  209-menu-crop2.png): 232px 面板两组——「编辑」消除笔/构图/宫格切分(›)/
  提示词反推，「预设」场景俯视图/连续分镜图/多机位九宫格/人物三视图/
  面部三视图/产品三视图；分组标签 12px white/40，行 38px 图标+13px 白字，
  展开时工具箭头朝上。复刻: JimengImageNodeToolbar 工具下拉落地 (10 项
  mock toast)。另: 未选中视频卡的 controls 条悬停/选中/播放时才显示
  (208-video-card.png——静止卡仅中央播放钮)，媒体卡补 group-hover 门控；
  batch 16 断言随批 208 连线证据更新 (rgb(0,142,229)/1px)。
  验证: verify-jimeng-batch101.py 新增；batch 15/16/97 回归 PASS。
- Batch 210 (视觉比对 + +钮尺寸对齐): 源站视频工具条/截取帧下拉最新
  截图 (210-source-video-toolbar.png / 210-source-capture-dropdown.png)
  与 clone 并排比对——工具条条目/VIP 菱标/尾钮、卡片控制条
  (Pause/时间/Mute video/Enter browser full screen, 210-card-buttons.json)
  全部一致，无漂移。微调: 源站「Create connected node」+ 圆钮 36×36
  (clone 原 24px)，左右两侧 + 钮放大至 size-9、图标 16。batch
  14/16/17/20/24 回归 PASS。
- Batch 211 (外壳件条目级复验): 源站左栏 9 项 (文本/图片/视频/音频/
  时间线/主体/导演台+Beta/资产库/上传，211-rail-dock.json) 与底部 dock
  (选择工具/小地图/显示连线 ｜ 缩放块 ｜ 与 AI 对话) 与 clone 逐项一致
  ——零漂移，无需改动。
- Batch 212 (全量质量门): 退出码全量扫 verify-jimeng-batch1..101 ——
  87 verifier 零失败 (含新增 99/100/101)，截图随扫刷新入库。
- Batch 213 (修剪态复验 + 标签对齐): 源站视频修剪条最新采样
  (213-source-trim.png / 213-trim-bar.json): 562×100，布局与 clone
  batch 10 结构一致；新细节——时长标签含「Selected duration: 」前缀
  (Selected duration: 6.1s)。JimengTrimPanel 标签对齐；batch 31/33
  verifier 的时长解析改为剥离前缀后比较，31/33/10/44 回归 PASS。
- Batch 214 (重拍态复验 + 提示词门控): 源站局部重拍态最新采样
  (214-source-repaint.png / 214-repaint.json): 面板 680×264，帧条选区
  aria「Selected duration: 4.0s」，发送钮空提示时灰 (白/[0.16]) 带
  「Prompt is required」，布局与 clone batch 5 一致。复刻:
  JimengRepaintPanel 提示词可输入 (原静态占位)、发送钮按提示词门控
  (空=灰+Prompt is required，有提示词=白色)、选区补 aria。
  batch 5 verifier 更新为批 214 契约，5/23 回归 PASS。
- Batch 215 (编辑态复验): 源站视频编辑态最新采样 (215-source-edit.png)——
  8 图标工具药丸 (框选/套索/箭头/文字/橡皮擦/定位/撤销/重做) 与节点放大
  自动播放均与 batch 6 一致；两处演进——提示条左端图标由铅笔改为**回形针**，
  积分数值 120/260 → **144/312** (随配置变动的动态值)。复刻对齐
  JimengVideoEditMode；batch 6 verifier 断言同步更新，6/12 回归 PASS。
- Batch 216 (提示词反推行为演进复刻): 源站提示词反推已不再是 mock 面板
  (216-source-infer.png)——点击后节点放大暂停，右侧打开 AI 抽屉并预填
  「用 视频反解 反推出 {视频标题} 的提示词，并创建文本节点，方便我拉片
  复刻」。复刻: store 新增 aiDrawerPrefill/openAiDrawer；JimengAiDrawer
  以 prefill 为 key 重挂载带入初始值；JimengVideoNode 提示词反推 →
  enterInfer + openAiDrawer(预填)；JimengInferPanel 渲染移除 (组件保留)；
  工作区 Escape 分支补抽屉关闭。batch 8 verifier 改写为新契约
  (抽屉打开+预填+无旧面板+Escape 关闭)，8/12/30/40/97/101 回归 PASS。
- Batch 218 (全屏预览复验 + 音量滑杆): 源站全屏预览最新采样
  (218-source-fullscreen.png)——控制条为 ⏸ + 0:01/0:06 ｜ 音量滑杆
  (细线+圆点) + 🔊 + 退出全屏，右上角 X 关闭钮；视频 cover 铺满、
  底部细进度线。新增细节: 静音钮旁的**音量滑杆** (batch 80 未记载)。
  复刻: JimengVideoPreview 控制条补静态音量滑杆 (60%，
  CLONE_DECISION)；batch 80/32 回归 PASS。
- Batch 219 (多选工具条复验 + 抽屉草稿持久化): 源站 shift+双选未编组
  节点 → 多选条「2 节点｜编组｜布局∨｜下载图标钮」(219-multiselect-toolbar.json
  / 219-source-multiselect.png)——与 clone 完全一致 (背景色钮仅编组态出现，
  batch 63 契约，非漂移)，零改动。对齐的小差距: AI 抽屉草稿在源站跨
  关闭保留 (重开仍见上次反推预填)——store 新增 aiDrawerDraft，
  JimengAiDrawer 输入即写草稿、初始化优先取草稿。batch 8/12 回归 PASS。
- Batch 220 (全量质量门): 退出码全量扫 verify-jimeng-batch1..101 ——
  87 verifier 零失败，截图随扫刷新入库。
- Batch 221 (右键菜单复验 + 细节对齐): 源站节点右键菜单最新采样
  (221-context-menu.json): 面板 192×324、行高 36px、快捷键 white/60、
  重做禁用行 (white/20) 附「无需重做操作」提示；分组与条目与 clone
  契约一致。复刻微调: 面板 w-44→w-48 (192px)、行 h-11→h-9 (36px)、
  重做禁用行补提示。batch 62/64 回归 PASS。
- Batch 222 (空白右键菜单复验 + 子菜单补全): 源站空白画布右键菜单
  (222-pane-menu.json): 232px、行 36px、重做禁用行附「无需重做操作」；
  「新建节点」子菜单共 10 项——「添加节点」表头 (white/35) + 文本/图片/
  视频/音频/时间线/主体/导演台/从资产库添加/本地上传 (后 5 项仅展示
  mock，CLONE_DECISION)。复刻: JimengPaneContextMenu 子菜单由 4 项扩至
  10 项并补表头，面板/行尺寸对齐，重做提示补齐。batch 25 verifier
  更新 (子菜单 9 menuitem 项)，25/26 回归 PASS。
- Batch 223 (缩放菜单复验): 源站底栏缩放菜单最新采样
  (223-zoom-menu.json): 200×292，放大视图⌘+/缩小视图⌘-/适配画布⇧1/
  缩放至选中项⇧2 (无选中禁用)/缩放至50%/100%⌘1/200%——与 clone
  batch 7 契约一致，零漂移，无需改动。
- Batch 224 (生成历史/用户菜单复验): 源站两菜单最新采样——生成历史
  288×91 空态「暂无生成历史」(224-history-menu.json)；用户菜单 240×272:
  租户名头 (西卡文案馆) + 帮助中心/使用手册/快捷键/AI生成水印设置/即梦CLI
  (224-user-menu.json)——均与 clone 契约一致，零漂移，无需改动。
- Batch 225 (资产库模态复验): 源站资产库模态最新采样
  (225-source-assets-modal.png): 834×672 居中模态——资产(active 药丸)/
  主体 tab、图片(下划线 active)/视频/音频/文档筛选 + 搜索框 + 日历/筛选
  双图标、空态「暂无图片素材」、底部「已选择 0 个素材」+ 禁用确认钮——
  与 clone batch 55 契约一致，零漂移，无需改动。
- Batch 227 (搜索浮层复验 + 对齐): 源站顶栏搜索浮层采样
  (227-search.json / 227-source-search.png): 输入框 placeholder
  「搜索节点...」(clone 原「搜索」)、面板 242px 宽 (clone 原 380px)、
  输入行更紧凑 (~26px)。JimengSearchOverlay 三项对齐；batch 96 verifier
  断言同步更新 (占位符按属性断言)，96 回归 PASS。
- Batch 228 (+ 钮行为复验): 源站选中节点「Create connected node」+ 圆钮
  点击 → 打开「添加节点」子菜单 (228-plus-menu.json / 228-source-plus-menu.png:
  添加节点表头 + 文本/图片/视频/音频/时间线/… 项)——与 clone
  JimengInsertMenu (表头 + 9 项) 同族一致，无需改动。
- Batch 229 (轮转回归): batch 34-48 段 15/15 PASS。文本节点插入采样
  两次未遂 (+ 菜单展开时序边际)，batch 68 既有源站证据维持有效，
  后续轮次再试。
- Batch 230 (+ 钮子菜单上下文态采样): 230-source-text-node.png——+ 钮的
  添加节点子菜单项存在上下文禁用态 (合成事件触发「无法连接这些节点」
  toast；文本/图片/音频呈灰态、视频高亮)。合成点击未真正插入节点，
  文本节点插入采样仍未遂 (batch 68 证据维持)；无效连接 toast 文案
  已留档。clone 插入菜单保持「总是可插入 + 建边」语义 (CLONE_DECISION)。
- Batch 231 (无效连接 toast 落地): 批 230 采样的「无法连接这些节点」
  toast 接入 clone——JimengWorkspace 新增 onConnectEnd，连接拖拽以
  invalid 结束时 pushToast。batch 57 交互审计回归 PASS。
- Batch 232 (全量质量门): 退出码全量扫 verify-jimeng-batch1..101 ——
  87 verifier 零失败，截图随扫刷新入库。
- Batch 233 (悬停门控验证器): verify-jimeng-batch102.py 新增——视频卡
  控制条在静止未选中时 opacity 0，悬停/选中时 opacity 1 (批 209 门控
  的行为级断言：idle→hover→unhover→selected 四态)。
- Batch 234 (文本节点插入第三次采样): 真实鼠标点击子菜单「文本」仍未
  产出节点——源站 + 钮的插入语义为**拖拽建立连接**，纯点击等于无效连接
  尝试 (批 230 toast)。文本节点视觉采样维持 batch 68 证据；clone 的
  「点击菜单项即插入 + 建边」保持 CLONE_DECISION 不变。
- Batch 235 (编组态复验): 源站多选 → 编组 → 工具条切为「解除编组/布局/
  背景色」+ 编组框出现「编组 1」标签 (235-grouped.json /
  235-source-grouped.png)——与 clone batch 63 契约一致；解除编组后完整
  还原为「2 节点/编组/布局」。多选家族两态全部新鲜验证，零漂移。
- Batch 236 (音频节点插入采样 + 对齐): 源站左栏「音频」插入 →
  音频节点 368×368 方形 (clone 原 400×120 横条)、aria「音频 node:
  音频 1」、**插入即处于选中态** (236-audio-node.json /
  236-source-audio-node.png)。复刻: addNodeAt 音频分支尺寸改为
  368×368；插入节点统一 selected: true (源站行为)。注意: 源站撤销栈
  不覆盖左栏插入 (⌘Z 无效)，还原需手动删除——clone 的插入接撤销栈
  为既有增强，保留。batch 17/19/20/68/73 回归 PASS。
- Batch 237 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 238 (文本节点插入采样 + 对齐): 源站左栏「文本」插入 →
  文本节点 368×368 方形 (clone 原 328×340，批 68 旧证据)、空态
  「双击编辑文本」+ 标题「文本 1」、插入即选中——与批 236 音频节点
  同规则。store 文本分支尺寸改为 368×368；batch 68 verifier 屏幕尺寸
  断言同步更新 (0.7299 缩放下 ~269×269)，68/17/65 回归 PASS。
  还原方式: 源站左栏插入不可撤销，手动选中+删除 (同批 236)。
- Batch 239 (音频卡内部 + 生成面板落地): 源站音频卡内部仅居中 5 柱
  波形图标 (无常驻播放控件，236-source-audio-node.png)——clone 旧横条
  播放器 (播放钮 + 44 柱波形 + 时长) 系误复刻，移除。新增
  JimengAudioGenPanel: 选中态下方 680×176 面板，占位「请输入你想生成
  的说话内容」+ 展开钮 + 底行 音频生成∨/Seed TTS∨/直爽女大∨ + ✦1 +
  灰色发送 (输入后白色)。batch 19/47 verifier 改写为新契约，均 PASS。
- Batch 240 (全量质量门): 退出码全量扫 verify-jimeng-batch1..101 ——
  88 verifier 零失败 (含新增 102)，截图随扫刷新入库。
- Batch 241 (文本编辑态复验 + 工具条落地): 源站文本节点双击进入
  编辑态——卡上方出现富文本工具条 (241-source-text-edit.png):
  字体 T∨/无序列表/有序列表/加粗 B/删除线 S/斜体 I/下划线 U/展开钮，
  8 个 mock 按钮；编辑时「双击编辑文本」空态隐藏。复刻:
  JimengTextNode 编辑态新增 text-format-toolbar (纯视觉 mock，
  onMouseDown 防失焦)。verify-jimeng-batch103.py 新增 (8 按钮契约 +
  Escape 退出)，38/68 回归 PASS。
- Batch 242 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 243 (文本节点选中工具条落地): 源站最新截图
  (243-source-font-menu.png) 显示文本节点选中(非编辑)态自有工具条
  「背景色｜展开钮｜下载」——批 68「选中无工具条」已被源站演进推翻；
  背景色打开六格调色板 (无+青绿/靛蓝/紫/橙/黄，色值为 CLONE_DECISION)。
  复刻: JimengTextNode 选中态 NodeToolbar + bgColor 字段
  (选色写回卡片背景、无=默认深色渐变)。字体∨下拉列表仍未采样
  (定位落在背景色钮，BLOCKED_BY_EXTRACTION 遗留)。
  verify-jimeng-batch104.py 新增 (工具条/调色板/选色写回/无复位)，
  68 回归 PASS。
- Batch 244 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败 (含新增 103/104)，截图随扫刷新入库。
- Batch 245 (音频生成下拉部分采样 + 还原协议修正): 「音频生成」下拉
  两项 音频生成/音乐生成 (192×76，245-audio-selectors.json)；Seed TTS/
  直爽女大 下拉未捕获。重要修正: 批 236 的「源站撤销栈不覆盖左栏插入」
  结论有误——⌘Z 在画布焦点下有效 (本轮 3 次 ⌘Z 完整还原了插入与误删)，
  此前失效系标题编辑输入框吞焦点所致。协议收紧: 源站画布上禁止
  右键-删除清理 (上下文菜单可能作用于其他节点)，一律 ⌘Z 恢复后核对
  节点 id 集合。本次误删已完整还原 (两原始视频节点 id 核对一致)。
- Batch 246 (音频生成下拉落地): JimengAudioGenPanel「音频生成」选择器
  接入批 245 采样的两项下拉 (音频生成/音乐生成，192×76 36px 行，
  可切换)；Seed TTS/直爽女大 维持 chevron mock。batch 19 回归 PASS。
- Batch 247 (轮转回归): batch 1-33 段 33/33 PASS。
- Batch 248 (Seed TTS 下拉采样落地): 源站「Seed TTS」下拉为两行式
  菜单项——标题 Seed TTS + 描述「上百个预设音色，让你玩转人声配音」
  (392×72，248-audio-selectors2.json / 248-source-Seed TTS.png)。
  JimengAudioGenPanel Seed TTS 选择器接入该下拉 (单选项，点击收起)；
  直爽女大 (音色) 下拉仍未采样。⌘Z 还原协议执行良好 (1 次还原，
  id 核对通过)。batch 19 回归 PASS。
- Batch 249 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 250 (音色下拉采样落地): 源站「直爽女大」(音色) 下拉完整采样
  (250-source-voice-menu.png): 「全音色」头 + 性别/年龄/语言/声音特点
  4 筛选 + 3 列音色网格 (可见 15 项: 直爽女大✓/低音炮/英气飒姐/阳光
  小男孩/纯净女声/温柔软妹/黛玉/明媚女声/含蓄女声/紫薇/猴哥/蜡笔小新/
  八戒Pro/动漫海绵/聪慧群仔，每项 ▶+名称，选中带勾)。复刻:
  JimengAudioGenPanel 音色下拉 700px 面板同构落地 (选色写回按钮标签)。
  ⌘Z 还原协议执行良好 (1 次还原)。
- Batch 251 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 252 (字体下拉定论): 三次双击均无法使源站文本节点保持编辑态
  (「双击编辑文本」占位未消失)——批 241 的富文本工具条截图为短暂瞬态，
  自动化下编辑态不再可稳定进入，字体∨列表定论 BLOCKED_BY_INTERACTION。
  clone 维持批 241 的编辑态工具条视觉 mock (textarea + 8 按钮)。
- Batch 253 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 254 (音色筛选采样): 「性别」筛选下拉选项 = 全部 性别 / 男 / 女
  (254-filters.json / 254-filter-性别.png)；年龄/语言/声音特点 三筛选
  未及采样 (选中态因 Escape 退出需逐个重开，后续轮次补)。
  clone 的筛选钮维持视觉 stub (筛选逻辑为 CLONE_DECISION)。
  ⌘Z 还原协议执行良好 (1 次还原，节点基线核对通过)。
- Batch 255 (筛选下拉落地): 年龄筛选 = 全部 年龄/幼儿/少年/青年/中年/
  老年；声音特点筛选 = 全部 声音特点/适合旁白/情景演绎/多情感/适合口播/
  知名 IP (255-filters.json + 255 截图)；语言筛选仍未采样 (stub)。
  复刻: JimengAudioGenPanel 四筛选改为可选下拉 (性别沿用批 254 三项，
  选项写回按钮标签；实际过滤音色列表为 CLONE_DECISION)。
  ⌘Z 还原协议执行良好。
- Batch 256 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 257 (语言筛选补采样落地): 「语言」筛选下拉 = 全部 语言/
  普通话/中文方言/英文 (257-lang-filter.json / 257-source-lang-filter.png)。
  JimengAudioGenPanel 语言筛选由 stub 升级为可选项下拉——至此音色
  筛选四项 (性别/年龄/语言/声音特点) 全部完成源站采样与落地。
  ⌘Z 还原协议执行良好 (1 次还原)。
- Batch 258 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 259 (轮转回归): batch 1-33 与 49-64 段合并认证 47/47 PASS。
- Batch 260 (左栏视频插入复验): 源站左栏「视频」插入 → 空生成视频
  节点「视频 2」(序号递增，260-video-insert.json)：屏幕 654×368 =
  世界 569×320 × 115% 缩放——与 clone addNodeAt (569×320) 一致，
  插入即选中 ✓。零漂移，无需改动。⌘Z 还原协议执行良好 (1 次还原)。
- Batch 261 (左栏图片插入采样 + 对齐): 源站左栏「图片」插入 →
  图片节点「图片 1」世界 320×320 方形 (屏幕 368×368 × 115%，
  261-image-insert.json / 261-source-image-insert.png)，插入即选中，
  cls 同为 node-image (与截取帧图片同族)。clone addNodeAt image
  尺寸由 480×360 修正为 320×320；插入即选中 (批 236) 已覆盖。
  batch 17/65 回归 PASS。⌘Z 还原协议执行良好 (1 次还原)。
  至此左栏插入家族四节点 (文本/图片/视频/音频) 全部新鲜采样对齐。
- Batch 262 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 263 (音频悬停交互采样): 源站音频卡悬停 (未选中) 仅标题行出现
  「Add tags」按钮，无播放控件——确认批 239 移除播放钮正确。
  音频节点标题行的 Add tags (标签选择器) 为 clone 未覆盖项 (视频节点
  batch 31 已有)，待后续批次补齐。⌘Z 还原协议执行良好 (1 次还原)。
- Batch 264 (音频 Add tags 落地): 音频节点标题行补齐颜色标记选色盘
  (悬停出现 Tag 钮，禁止+五色，复用 batch 31 TAG_COLORS；选色写回
  tagColor)——对应批 263 采样的「Add tags」悬停钮。bgColor/tagColor
  字段入 JimengAudioNodeData。batch 19/47 回归 PASS。
- Batch 265 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 266 (抽屉预填 chip 采样未遂): 反推打开抽屉后页面 evaluate
  超时 (drawer 渲染阻塞采样)，行内 chip (视频反解 skill chip/视频引用
  chip) 的精确样式未取得——219 截图已示其存在，clone 以纯文本预填
  近似维持。现场已完整还原 (2 节点/抽屉关闭/无选中)。
- Batch 267 (轮转回归): batch 1-33 段 33/33 PASS。
- Batch 268 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 269 (抽屉引用 chip 落地): 基于 219 已有截图裁剪分析
  (269-drawer-chips-crop.png，无需触碰源站)——预填文本中嵌入视频引用
  chip (缩略图 + 截断标题 sb_51...tf5q2)，出现两次；抽屉发送钮为白色
  可用态 (预填存在)。复刻: store 新增 aiDrawerRefChip (poster+label)，
  openAiDrawer 支持携带，JimengAiDrawer 输入区上方渲染引用 chip。
  batch 8/12 回归 PASS。零源站触碰 (纯截图离线分析)。
- Batch 270 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 271 (docs 门禁 + 轮转): verify-docs.py 通过 (1003 files /
  4398 links)；轮转 34-48 与 65-101 段合并认证 40/40 PASS。
- Batch 272 (多选右键菜单复验): 源站多选右键菜单最新采样
  (272-multiselect-menu.json): 192×332 八项 复制⌘C/复制副本⌘D/粘贴⌘V/
  编组/下载/重做⌘⇧Z/撤销⌘Z/删除⌫——无 保存到主体库，与 clone
  batch 64 契约一致，零漂移，无需改动。尺寸与批 221 节点右键菜单
  精修一致 (192px/36px 行)。
- Batch 274 (使用技能 flyout 采样未遂): 抽屉打开后页面 evaluate 与
  截图均持续阻塞 (渲染器 wedged，与批 266 同因)——「使用技能」flyout
  的条目级采样定论 BLOCKED_BY_RENDERER。clone 抽屉保留 5 技能 chips
  (batch 12/114 契约) 作为近似。现场已还原 (2 节点/抽屉关闭/无选中)。
- Batch 275 (轮转回归): batch 1-33 与 49-64 段合并认证 47/47 PASS。
- Batch 276 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 277 (选择器 hover/aria 微态采样 + 对齐): 源站音频生成面板
  三选择器 hover 无 tooltip/title，但 aria 前缀各异——创作类型: 音频
  生成 / 选择模型: Seed TTS / 音色: 直爽女大。clone aria-label 对齐
  (原 选择生成类型/选择音色模型/选择音色)。batch 19 回归 PASS。
  ⌘Z 还原协议执行良好 (1 次还原)。
- Batch 278 (筛选交互深挖定论): 应用「性别=男」观察音色列表变化的
  尝试两度触发渲染器阻塞 (与批 266/274 同因)——筛选交互深挖定论
  BLOCKED_BY_RENDERER。clone 的筛选实现基于静态采样证据
  (批 250 音色网格 / 254 性别选项 / 255 年龄与声音特点选项)，
  选项切换与网格过滤逻辑为 CLONE_DECISION。现场已还原 (1 次撤销)。
- Batch 279 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 280 (渲染器恢复 + hover 截图补采): 渲染器 wedged 状态解除，
  截图能力恢复。音频生成面板三选择器 hover 截图补采
  (280-hover-genkind/model/voice.png)——无 tooltip 弹出，选择器样式与
  clone hover 态一致；音频卡/生成面板/抽屉预填 (引用 chip 已更新为
  🎧音频 1) 视觉全部与 clone 对齐。零漂移，无需改动。
  ⌘Z 还原协议执行良好 (1 次还原)。
- Batch 281 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 282 (筛选交互深挖成功 + 性别映射落地): 渲染器恢复后筛选
  交互采样成功——性别=男 过滤出 18 个男声 (低音炮/阳光小男孩/猴哥/
  蜡笔小新/八戒Pro/动漫海绵/聪慧胖仔/憨萌福娃/爽快小哥/低沉大叔/
  飒爽少侠/权威精英男/呆萌小男孩/威严老爷子/深夜博客/成熟总裁/皇上/
  老实小哥)，性别=女 过滤出 18 个女声 (直爽女大/英气飒姐/纯净女声/
  温柔软妹/黛玉/明媚女声/含蓄女声/紫薇/糯音女孩/TVB女声Pro/优雅女声/
  狐媚姐姐/将门女将/成熟御姐/灵动甜妹/慈祥奶奶/妩媚熟女/正气女声)。
  复刻: JimengAudioGenPanel VOICES 扩展为 36 项带性别结构，
  性别筛选真实过滤音色网格 (推翻批 278 的 BLOCKED 判定——渲染器
  恢复后采样即成功)。batch 19 回归 PASS。⌘Z 协议两次执行良好。
- Batch 283 (年龄维度过滤结果采样): 年龄=老年 → 4 音色: 威严老爷子/
  慈祥奶奶/慈祥爷爷/和蔼奶奶 (283-filter-results.json)——其中
  慈祥爷爷/和蔼奶奶 不在性别采样的 36 项内，证实音色全目录大于
  已采样清单 (clone VOICES 维持 36 项 + CLONE_DECISION 截止)。
  语言=英文 与 声音特点=适合口播 的 dump 受累积筛选污染 (老年未重置)
  结果为空，单维结论待后续。clone 筛选下拉选项已落地、过滤逻辑
  (性别) 已实现，年龄/语言/声音特点的音色映射为部分采样。
  现场已还原 (1 次撤销)。
- Batch 284 (轮转回归): batch 1-19 与 49-64 段合并认证 33/33 PASS。
- Batch 285 (语言=英文 单维结论澄清 + 落地): 全新插入无累积筛选下，
  语言=英文 单维过滤出 8 个英文音色 (Bill/Sarah/Liam/George/Lily/
  Callum/Chris/Daniel，285-voices-english.json / 285-source-lang-en.png)
  ——此前空结果确系老年累积筛选污染。复刻: VOICES 扩至 44 项
  (36 中文 + 8 英文，英文项带 lang 标记)，语言=英文 真实过滤英文音色，
  普通话/中文方言 映射中文集合 (CLONE_DECISION)。音色全目录 ≥44 项。
- Batch 286 (适合口播单维采样 + 目录增长): 声音特点=适合口播 单维
  (清洁状态) → 8 新音色: 灵动女声/温柔女声/知性熟女/Vlog配音/活泼女声/
  清醒语录/磁性男主播/清晰语录 (286-filter-results.json)——音色全目录
  增长至 ≥52 项 (286-source-filters.png)。语言=普通话 dump 受未重置的
  适合口播污染 (推断映射维持)；中文方言选项在滚动区外点击未中 (待续)。
  复刻: 8 新音色入 VOICES (性别推断)。batch 19 回归 PASS。
  现场已还原 (1 次撤销)。
- Batch 287 (中文方言下拉采样落地): 滚动语言下拉后「中文方言」点击
  生效 → 8 方言音色: 真人播客男/磁性男主播(双属)/台湾腔甜妹/天津小哥/
  台湾男生/春日部姐姐/蜡笔小妮/桃花庵主 (287-dialect-voices.json /
  287-source-dialect.png)。复刻: 7 新音色入 VOICES (lang=中文方言)，
  语言筛选三分支 (英文/中文方言/普通话) 各自真实过滤；磁性男主播
  双属保留单条目。音色全目录 ≥59 项。至此音频生成面板全维度
  (生成类型/模型/音色/四筛选) 采样与落地闭环。batch 19 回归 PASS。
  现场已还原 (1 次撤销)。
- Batch 288 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  90 verifier 零失败，截图随扫刷新入库。
- Batch 289 (音色网格滚动分页复验): 全音色网格滚动到底无新音色
  (289-full-catalog.json)——ALL 视图可见 17 项 (直爽女大/低音炮/英气
  飒姐/阳光小男孩/纯净女声/温柔软妹/黛玉/明媚女声/含蓄女声/紫薇/猴哥/
  蜡笔小新/八戒Pro/动漫海绵/聪慧胖仔/糯音女孩/憨萌福娃/TVB女声Pro)
  全部 ⊆ 已采样 44 项目录，无分页页脚。零漂移，无需改动。
  现场已还原 (1 次撤销)。
- Batch 290 (轮转回归): batch 49-64 与 65-101 段合并认证 39/39 PASS。
- Batch 291 (轮转 + 演进轻扫): batch 34-48 段 15/15 PASS；源站视频
  工具条演进轻扫零漂移 (775×40 七条目一致，只读探测)。
- Batch 292 (轮转回归): batch 1-19 与 20-33 段合并认证 32/33——batch 15
  播放定位超时为负载抖动 (单独复跑 PASS，与批 247/281 历史一致)。
  复跑后该批全绿。
- Batch 293 (演进轻扫 + 两处演进落地): 右键菜单零漂移 (192×324 八项
  一致)；音频生成面板两处演进——高度 176→196、价格区 ✦1 →
  「Current price 1.1」(70px 裁切，同批 206 形态) + 空提示发送钮
  aria「请输入提示词」。复刻: JimengAudioGenPanel 高度与价格签对齐。
  batch 19/47 回归 PASS。现场已还原 (1 次撤销)。
- Batch 294 (音乐生成态选择器组切换落地): 批 294 采样确认切换
  音乐生成 后选择器整组变化——模型位 SeedMusic 1.0 Preview、音色位
  变 120s 时长 (294-price-dynamics.json：价格区在两种态下均为
  Current price 形态)。复刻: JimengAudioGenPanel 按 genKind 条件
  渲染两组选择器 (音频生成=Seed TTS 两行式+音色下拉；音乐生成=
  SeedMusic 1.0 Preview+120s chevron stub)。面板整体重写消除
  先前 patch 的 JSX 结构损伤。batch 19/47 回归 PASS。
  现场已还原 (3 次撤销)。
- Batch 295 (SeedMusic 下拉采样落地): 音乐生成态模型下拉为两行式
  菜单项——标题 SeedMusic 1.0 Preview + 描述「细腻风格控制与多语种
  演唱，人声表现更自然」(392×72，295-music-selectors.json /
  295-source-seedmusic-menu.png)。JimengAudioGenPanel 音乐生成态
  模型位接入该下拉；120s 时长下拉未采样 (chevron stub，面板在
  SeedMusic 菜单 Escape 后失焦)。batch 19/47 回归 PASS。
  现场已还原 (2 次撤销)。
- Batch 296 (120s 时长下拉采样落地): 音乐生成态时长选择为**水平
  分段条**——60/120/180/240/300/360 六段 (368×44，当前值高亮；
  296-duration-menu.json / 296-source-duration-menu.png)。复刻:
  JimengAudioGenPanel 音乐生成态时长位改为分段条 (点击选值回写
  按钮标签)。至此音乐生成态全部选择器采样闭环。batch 19/47 回归
  PASS。现场已还原 (1 次撤销)。
- Batch 297 (双模式价格差异确认 + 动态价格落地): 完整文本读取——
  音乐生成态价格 **6.6** (vs 音频生成态 1.1)，价格随模式动态变化
  (297-price-diff.json)。另发现全新插入的音频节点继承了上次的
  音乐生成 态 (用户级持久化，CLONE_DECISION: clone 维持默认
  音频生成)。复刻: JimengAudioGenPanel 价格值按 genKind 动态
  (1.1/6.6)。batch 19 回归 PASS。现场已还原 (1 次撤销)。
- Batch 298 (时长切换价格采样不确定): 选择 360s 后价格持平 6.6 且
  时长标签未变——合成点击未在分段条生效 (JS 分派与真实指针事件差异)，
  时长→价格 映射采样不确定。价格-模式映射 (音频生成 1.1 / 音乐生成
  6.6，批 297) 维持；时长维度映射留待真实指针事件采样。clone 的
  分段条已实现选值回写 (交互模型与源一致)。现场已还原 (1 次撤销)。
- Batch 299 (时长→价格映射定论): 真实指针事件重试仍无法稳定展开
  时长分段条 (批 296 曾成功一次，交互时序敏感)——时长→价格映射定论
  BLOCKED_BY_INTERACTION。价格-模式映射 (音频生成 1.1 / 音乐生成 6.6，
  批 297) 维持有效。clone 分段条交互模型与源一致，选值回写已实现。
  现场已还原 (1 次撤销)。
- Batch 300 (里程碑 + 全量质量门): 退出码全量扫 verify-jimeng-batch1..103
  ——90 verifier 零失败，截图随扫刷新入库；§10 留档快照刷新至
  batch-300 状态（本轮快照含探针协议沉淀与全受阻面定性）。
- Batch 301 (新监测周期首扫 + 两处模式适配落地): 三面复扫——视频
  工具条 775×40 与右键菜单 192×324 零漂移；音频面板两处模式适配
  演进——占位符随模式变化 (音乐生成→「请输入你想生成的音乐」/
  音频生成→「请输入你想生成的说话内容」)、面板高度随模式变化
  (音乐生成 144 / 音频生成 196)。复刻: JimengAudioGenPanel 占位与
  高度按 genKind 适配。batch 19/47 回归 PASS。现场已还原 (1 次撤销)。
- Batch 302 (双模式渲染验证器): verify-jimeng-batch105.py 新增——
  音频生成态 (占位 说话内容/高度 196/Seed TTS+音色) 与 音乐生成态
  (占位 音乐/高度 144/SeedMusic+120s) 双向切换断言，含回退校验。
  verifier 修正: 面板定位改用 textarea[placeholder] 选择器
  (占位符非 textContent)。
- Batch 303 (演进监测轻扫): 视频工具条零漂移 (775×40 七条目一致)。
  音频面板 dump 未命中 (探针时序，非源站漂移——批 301 契约仍新，
  后续轮次重试)。
- Batch 304 (输入元素演进确认 + 叠加层占位落地): 页面级 dump 确认
  源站音频面板输入已从 textarea+placeholder 切换为 contenteditable
  (editables: 2 / textareas: 0，占位以真实元素渲染)——批 301→303 之间
  的演进。复刻: JimengAudioGenPanel 占位改叠加层渲染 (textarea 保持
  可用，placeholder 属性移除)，batch 19 定位改用 textContent。
  batch 19 回归 PASS。现场已还原 (1 次撤销)。
- Batch 305 (双模式验证器适配): verify-jimeng-batch105 断言更新至
  叠加层占位机制 (占位文本从 overlay div 读取，面板定位改用
  textarea[aria-label=音频生成提示词])——双模式 (音频 196/说话内容、
  音乐 144/音乐) 断言双向 PASS。batch 19/47 回归 PASS。
- Batch 306 (轮转回归): batch 49-64 与 65-101 段合并再认证 39/39
  PASS (音频面板叠加层占位改动后的覆盖认证)。
- Batch 307 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败 (含新增 105)，截图随扫刷新入库。
- Batch 308 (contenteditable 微态采样未遂 + 意外节点清理): 点击
  contenteditable 后键入触发意外第二音频节点插入 (节点 3，点击落点
  误触)，且 ⌘Z 因编辑器焦点吞键失效——手动选中+Backspace 清理还原
  (基线 2 节点核对通过)。contenteditable 深交互微态采样维持
  BLOCKED_BY_INTERACTION (合成交互的副作用不可控)。
- Batch 309 (音频面板重采样): 零漂移——680×144、音乐生成态持久
  (309-audio-panel.json，contenteditable 1 个，文本与批 304 采样一致)。
  clone 双模式契约 (占位叠加/高度/选择器组) 维持有效。
- Batch 310 (轮转回归): batch 34-48 与 65-101 段合并认证 40/40 PASS。
- Batch 311 (轮转回归): batch 1-33 与 49-64 段合并认证 47/47 PASS。
- Batch 312 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40 七
  条目、右键菜单 192×324 八行、音频面板 680×144 (音乐生成态持久、
  contenteditable 结构确认)。无需改动。
- Batch 313 (轮转回归): batch 1-33 与 65-101 段合并认证 58/58 PASS。
- Batch 314 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 315 (轮转回归): batch 1-19 与 65-101 段合并认证 44/44 PASS。
- Batch 316 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批 312
  扫描结果一致，无需改动。
- Batch 317 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 318 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 319 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 320 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批 312/316
  扫描结果一致，无需改动。
- Batch 321 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 322 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 323 (轮转回归): batch 1-33 段 33/33 PASS。
- Batch 324 (轮转回归): batch 34-64 段合并认证 29/29 PASS。
- Batch 325 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312/316/320 扫描结果一致，无需改动。
- Batch 326 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 327 (轮转回归): batch 34-64 段合并认证 29/29 PASS。
- Batch 328 (轮转回归): batch 1-33 与 65-101 段合并认证 58/58 PASS。
- Batch 329 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 330 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312/316/320/325 扫描结果一致，无需改动。
- Batch 331 (轮转回归): batch 49-64 段 14/14 PASS。
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
## 10. 留档快照（batch 200 后 · 2026-09-15）
- 完成度: batch 1-200 全部闭环（提取→实现→verifier→npm run check→回归→push）。
  84 个独立 verifier（退出码判定）真实全绿，覆盖全部有代码批次
  （55/60/74/77/79/81/83/84/90/94 为观察/重构批，无独立 verifier；
  97 图片节点工具条、98 上传瞬态为 batch 195/197 新增）。
- 复刻重心状态: 「本地上传视频节点」选中工具栏 9 项 UX 全部落地——
  局部重拍帧条、视频编辑工具药丸、截取帧（首帧/尾帧直出图片节点 +
  自定义帧选择器）、补帧/智能超清 mock 任务闭环、视频修剪、提示词反推、
  全屏播放器（black/60 + 自动静音播放 + 5px seek 进度条）、下载（保存
  状态门控）。图片节点自有工具条（智能改图✦/扩图/智能超清/抠图/多角度/
  工具∨，batch 195）与截取帧产出上传瞬态「正在上传图片 N%」（batch 197）
  均已落地；截取帧产出标题为下划线约定「{视频}_{首帧|尾帧}」。
- 家族扩展: 多选组合工具条（N 节点/编组/解除编组/布局 宫格·智能/背景色
  调色板/禁用下载）、编组卡片视觉层、多选右键菜单变体、节点行内重命名
  （全节点类型）、资产库模态、小地图（pan/zoom）、离线编辑冲突对话框、
  顶栏演进对齐（搜索/生成历史双钮 + 用户菜单）、媒体失效态、连线显隐
  开关、进度条 5px 药丸演进、退出码全量回归方法。
- 受阻面（外部依赖, 均已定性入档）: 连线真实视觉（源站无 edge DOM）；
  智能超清/补帧真实流程（积分类副作用，按用户决策除牌）；订阅管理页
  （按用户决策除牌）；工具∨ 菜单项（三种触发路径均未展开，
  BLOCKED_BY_EXTRACTION）；源站截图（三种捕获路径在该页面态下均超时，
  待页面空闲复测）。
- 质量门: npm run check（lint + typecheck + build）全绿；全量回归
  1..98 退出码判定 84/84 零失败（batch 198 最近一轮全量扫）。
- 协作记录: 并行开发者的 liblib 在途文件全程未触碰；jimeng README 曾被
  ed2ae39 误覆盖为 LibTV runbook，已从 git 历史完整恢复（b1864ba）。
- 维护循环: 111-113 及 115-199 低频维护轮（轮空复查/抽样回归/全量扫），
  截取帧下拉于 batch 195 恢复展开，图片节点工具条/上传瞬态已复刻
  （batch 195/197）；工具∨ 菜单与源站截图维持 BLOCKED_BY_EXTRACTION。
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
