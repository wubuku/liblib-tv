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
  + 播完自停。
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
- BLOCKED_BY_FIXTURE: 智能超清、补帧（会提交生成任务消耗积分）；
  下载（真实文件）、保存到主体库（写库）→ 工具条上保留按钮但无功能面板。

## 8. 复刻侧实现映射（CLONE_DECISION）

- 路由: `/jimeng` → redirect `/jimeng/canvas/demo`（同构 `/frameos`）。
- Store: `src/store/jimengStore.ts`（与 canvasStore/frameosStore 隔离；
  选中态以 `selectedNodeId` 单一来源回填，规避 applyNodeChanges 重置问题）。
- 样式: `src/app/jimeng-canvas.css`（token 表见 §3）；组件 `src/components/jimeng/`。
- 验证: `scripts/verify-jimeng-batch1.py`（dev server 4317；截图入
  `docs/design-references/jimeng/`）。
