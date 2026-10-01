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
- SOURCE_FACT (batch 797, Agent 抽屉默认态 — **关闭待决问题 #2**): 源站画布首屏
  **Agent 面板默认收起**，右下只暴露一个「与 AI 对话」触发钮；点击后才展开。
  收起态 → 点击前后对照实测（登录态 @1680×826）：
  触发钮**三层**结构（此前两次都只量了内层按钮，结论两次都错）：
    定位层 `absolute bottom-3 right-3 flex flex-col items-end`（**12px** 内缩）
    药丸层 @[1548,778] **120×36**  bg rgba(39,39,39,0.72)  radius **20px**
            backdrop-filter **blur(40px)**
    按钮层 @[1549,779] **118×34**  自身**透明**  radius 20px  font 13px
    ⇒ 按钮比药丸四周各内缩 1px，所以「按钮距右缘 13px」是 12+1 的**结果**，
      定位层仍是 12px。**不可据内层矩形去改 bottom/right**（同 batch 796 的教训）。
  收起态**不出现**任何展开类控件：新建会话/收起/使用技能/引用参考/发送消息 全无。
  展开态面板 @[1268,12] **400×802**  radius 20px  z-40
    background `color(srgb .12549 ×3 / .8)` = **rgba(32,32,32,0.8)**（此前误用不透明
    #1E1E1E）、backdrop-filter **blur(60px)**、
    border 1px solid rgba(255,255,255,**0.1**)（此前 0.06）、
    box-shadow rgba(0,0,0,0.16) **0 0 80px 0**（此前无）。
    展开后五类控件齐备。
  - **待决问题 #2 至此关闭**：默认展开会把顶栏右簇遮住、并把「分享」挤成竖排
    （见 jimeng-clone-batch796-rail-hover-1680.png 里那个可见缺陷）。
    源站事实是默认收起，故复刻改为默认收起。「Escape 不关闭面板」（批 381）
    是独立契约，不受影响，仍然成立。
  - 复刻: `jimengStore.aiDrawerOpen` 初值 `true`→`false`；`JimengAiButton` 药丸
    改 120×36 + r20 + blur(40px)（此前 hugging content、r8、无 blur）；
    `JimengAiDrawer` 底色/边框/投影/blur 全部对齐上表。
  - 连带修正: `verify-jimeng-batch1.py` 的 `aiButton` 断言 `False`→`True`
    （旧默认态下按钮被面板挡住）；`verify-jimeng-batch795.py` 改为**显式点开**
    面板再验「展开时顶栏让位」——该批验的是交互契约而非默认态，语义未变。
    `verify-jimeng-batch794.py` 的「先收起抽屉」是 `if count==1` 防御，空态跳过，
    无需改。
  - verifier: `scripts/verify-jimeng-batch797.py`（26 项断言，含收起态
    「不泄漏展开类控件」与「顶栏分享不再被挤」两条反向断言）。
  - ⚠️ **提交归属**：batch 797 的代码与本文档条目在提交时被**并行 session 的
    `9da78637`（题名写的是 batch 795）裹走** —— 该提交同时含 batch 795 的顶栏
    让位工作与 batch 797 的抽屉默认态工作，两者本应分开。仓库已有同类记录
    （`a504e4bf` beeftv Batch 136）。成因是共享工作区里 `git add` 会把文件
    放进**共享索引**，随后他人的裸 `git commit` 就把别人的暂存内容一并提交。
    - 纪律：`git add` 之后到 `git commit` 之间存在被他人夹带的时间窗；
      提交前应复查 `git diff --cached --name-only` 是否含非己文件，
      或用 `git commit -- <paths>` 做 pathspec 限定提交。
- SOURCE_FACT (batch 798, 顶栏「分享」折行 — 可见缺陷修复): 逐层量源站分享按钮：
  按钮 **60×28 @[1388,16]**，padding `0 10px 0 8px`、gap 4px、居中、
  **`white-space: nowrap`**；子元素 = svg 图标 16×16 @[1395,22] +
  标签 span **24×20 @[1415,20]**（**12px / line-height 20px / w500** / nowrap）。
  复刻此前把「分享」叠成「分 / 享」两行，**成因不是宽度算错，而是缺 nowrap**：
  内容盒只有 42px（60−8−10）而内容需 8+16+4+24=52px，CJK 可在任意两字间断行，
  于是标签被挤到换行。**源站同样超**（内容 44px > 42px 内容盒，1395..1439），
  靠 nowrap 保持单行 —— 所以修 nowrap，而不是改宽度。
  复刻: 按钮加 `whitespace-nowrap`；标签行高 24→**20px** 对齐源站；
  图标与标签加 `shrink-0`（否则 flex 把图标从 16 压到 **14**）；
  并订正旧注释里「按我们的字体度量会到 70px」的错误（那是标签还是 16px 时的账，
  实际 8+16+4+24+10=62）。
  verifier: `scripts/verify-jimeng-batch798.py`（15 项断言；核心是
  「标签高度 == 一个行高 ⇒ 恰为 1 行」，另加顶栏文本控件**不得多行折行**的
  通用回归防护）。
  判据写法上的一个要点：断行与否用**相对**断言（图标右缘 + 4px gap == 标签左缘、
  标签高 == 行高），不要断言绝对 x —— 绝对 x 会把右簇间隙问题
  （见待决问题 #4）变成这条断言的 brittle 依赖。
- SOURCE_FACT (batch 800, 点阵网格 — **由估值改为实测**): 源站点阵网格画在
  WebGL `<canvas>` 上（画布内有 2 个 canvas，`getContext('2d')` 取不到像素，
  故改用 Playwright 截图 + PIL 逐像素分析）。
  100% 缩放下量得：点距 **18px**、点簇宽 **2px**、峰值 **rgb(45,45,45)**，
  背景 rgb(13,13,13) ⇒ 白色 alpha ≈ **0.13**（13+(255−13)×0.13≈44.5）。
  缩到 48% 后点距变 **8.6px**（≈18×0.48）⇒ 网格是**世界锚定**、随 zoom 缩放，
  不是固定屏幕间距。
  - ⚠️ **本批推翻旧台账**：「点阵网格间距/颜色 不可从 canvas 直接读出 |
    CLONE_DECISION (28px / rgba(255,255,255,0.075))」以及 CSS 注释里
    「73% 缩放下源站点距 ≈ 20px 屏幕 ≈ 28px 世界」—— 那是在无法读像素时的
    估值。实测点距 **18px**、alpha **0.13**，旧值偏大且偏淡。
  - 复刻的实现陷阱：`.react-flow__pane` **不在** `.react-flow__viewport` 内
    （实测 `paneInsideViewport=false`），是屏幕层，其 CSS background 不会被
    viewport 的 transform 缩放。若直接写死 18px，网格会固定在 18px *屏幕* 间距，
    缩放时与源站不符。故 `JimengWorkspace.applyGridVars` 在 `onMove` 里按真实
    变换写 CSS 变量：`tile = 18 × zoom`、偏移 `= pan mod tile`；
    容器 `style` 另给初值（`onMove` 不保证挂载时触发，缺 fallback 会导致
    「不动就不显示网格」）。默认 73% 下 tile=13.14px、实测屏幕点距 13px、
    峰值 rgb(44,44,44)，与源站 18px/(45,45,45) 在各自缩放下吻合。
  - verifier: `scripts/verify-jimeng-batch800.py`（17 项断言）。这是**像素级**
    验收而非查 CSS 字符串：截图后用 PIL 量点距/簇宽/峰值，并在切到 100% 后
    复测以证明点距**确实随 zoom 变化**。采样区先断言「≥90% 是背景色」，
    避免把节点/面板误当点阵来量。
  - 编号说明：797、799 已被并行会话占用，本批取 800。
- SOURCE_FACT (batch 802, 小地图落位 — 尺寸对、位置全错): 复测源站点小地图后
  量得导航 dock 面板 `[class*="navigation-dock"]`：
    @[12,656] **164×154**、padding **4px**、gap 4px、flex column、
    bg rgb(13,13,13)、radius 8px；子元素 = 小地图 @[16,660] **156×114** +
    「100%」dock 行 @[16,778] **156×28**。
  **关键结构发现**：那个 dock 行与**主底栏**控件同位（选择工具 @[16,778]、
  缩放 @[124,779]）⇒ 源站是「同一个 dock 变高到 154、小地图插在上方」，
  不是另浮一个面板。复刻是分离浮层（MiniMap 必须在 `<ReactFlow>` 内注册，
  无法移进 dock 组件），故按可实现的等价对齐：面板取 **164×118**
  （4+114+4）、left 12、bottom 52（下缘 774 正好贴住底栏顶边），两者同底色
  → 视觉连成一整条。
  - 修正前：面板 @[16,616]、内层 @[9,641]（`bottom-14 left-4 p-2`）
    ⇒ 整体偏高 40px、横向错位 7px。
  - **内层跑出壳外**的真正成因不是外壳 padding：`.react-flow__minimap` 被本仓
    样式表设成 `position:absolute; top:-26px; left:-22px; margin:15px`
    （实测 computed），还残留 `bottom right` 两个无效类名。只改 `position`
    会停在 @[31,675]（差值恰为那 15px margin）；**position:static + margin:0
    同时给**才落到 @[16,660] 156×114。
  - 残留差异：源站是单一元素统一 8px 圆角，复刻是两块相接，接缝处圆角有断点。
  - 连带修正: `verify-jimeng-batch91.py` 两条过期断言 —— dock 按钮标签
    （batch 796 起逐字对齐源站 `Zoom options, {n}%`，改为前缀匹配）与
    小地图面板高度（154 → 118，按本条实测）。
  - verifier: `scripts/verify-jimeng-batch802.py`（15 项断言，含
    「面板下缘 774 == 底栏顶边」的相接断言与「底栏仍 @[12,774] 164×36」
    的 batch 796 契约保护）。
- SOURCE_FACT (batch 25): 空白画布右键弹出菜单: 新建节点 > (子菜单)、
  粘贴 ⌘V、重做 ⌘⇧Z (无历史禁用)、撤销 ⌘Z；样式与节点右键菜单同族。
  复刻: 子菜单 hover 展开 (源站子菜单展开态未提取，CLONE_DECISION)，
  子菜单项在右键位置插入节点 (screenToFlowPosition)。
- SOURCE_FACT (batch 796, 画布外框几何 — **首次以「同口径容器提取器」全量复核**，
  脚本 `scripts/jimeng_chrome_probe.py` 同一段 evaluate 跑源站/复刻)：
  左侧工具栏 @1680×826 —— 壳体 @[12,242] **48×398**、padding 4px、gap 2px、
  radius **12px**、background `color(srgb .12549 ×3)` = **rgb(32,32,32) 不透明**、
  **backdrop-filter: none**、内描边白 0.04 1px；九个按钮 **40×40** radius 8px、
  图标 20×20 (源站 `[&_svg]:size-5`)；按钮 y = 246/288/330/372/414/456/498 →
  **分隔条** → 554/596，常规步距 42px、导演台→资产库 56px。
  分隔条 = 外框 20×12 @[26,540] (flex items-center justify-center) 内含
  **20×1 rgba(255,255,255,0.04)** 横线 @[26,546] —— 那多出的 14px 来自该元素，
  **不是** margin (两者 `margin-top` 实测均为 0px，源站 rail 子元素逐一枚举确认)。
  按钮 class 为 `size-9` 但被 `absolute inset-y-0 w-full` 覆盖成 40px，
  单看 `size-9`(36px) 会得出错误结论。
  **居中模型**：壳体高恒 398px，中心 = (视口高 + 56)/2，即在 y=56 以下区域垂直
  居中 ⇒ 壳体顶 = (H+56)/2 − 199。四视口实测壳体顶 242/189/279/329
  (H=826/720/900/1000) 与该式逐一吻合 ⇒ 源站是**推导**而非写死。
  左下 dock：壳体 @[12,774] 164×36 (bg rgb(13,13,13) r8 padding 4 gap 4)；
  选择工具 @[16,778] / 小地图 @[48,778] / 显示连线 @[80,778] 各 28×28；
  缩放钮 @[124,779] 48×28，**aria-label 逐字 `Zoom options, {n}%`**(含实时百分比)。
  顶栏右簇药丸 @[1505,12] 163×36、bg rgba(32,32,34,.8) + blur(40px) + r8 + padding 4
  —— 与 rail 是**两套**样式，rail 不可复用 `.jimeng-chrome-pill`。
  - ⚠️ **本 batch 推翻一条旧记载**：此前多处写「左栏 hover 高亮
    rgba(255,255,255,0.12)」。实测源站按钮 class 明确 `hover:bg-transparent`，
    且真实 hover 前后 `computed backgroundColor` 均为 `rgba(0,0,0,0)`。
    复刻已去掉该 hover 底色。教训同 §源站用 React Flow：**样式要回到
    computed style 复核**，注释里的 "SOURCE_FACT" 标签不自动等于事实。
  - ⚠️ **本 batch 推翻自己的一个中间结论**：先只比「内层控件矩形」得出
    「顶栏右边距应 12→16」，实为误判 —— 源站 pill 右边距本来就是 12，是内层
    4px padding 让最后一个控件显得靠左。**控件矩形 ≠ 容器矩形**，比外框必须
    比带背景的祖先容器。
  复刻: `JimengToolRail` 改 40×40 + p-1 + gap-0.5 + 12px radius + 新增
  `.jimeng-tool-rail`(.jimeng-canvas.css) 与 `.jimeng-tool-rail-separator`；
  `JimengBottomDock` 改 `left-3`；缩放钮 aria-label 对齐并补 `data-testid="dock-zoom"`
  (因 aria-label 含实时百分比，不能做字面选择器，batch 7/57 的选择器同步更新)。
  verifier: `scripts/verify-jimeng-batch796.py` (60 项断言，含多视口反证「写死 y」)。
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
- Batch 332 (轮转回归): batch 1-48 段合并认证 48/48 PASS。
- Batch 333 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 334 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312/316/320/325/330 扫描结果一致，无需改动。
- Batch 335 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 336 (轮转回归): batch 1-19 与 34-48 段合并认证 34/34 PASS。
- Batch 337 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 338 (轮转回归): batch 1-33 段 33/33 PASS。
- Batch 339 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312/316/320/325/330/334 扫描结果一致，无需改动。
- Batch 340 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 341 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 342 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 343 (轮转回归): batch 34-48 段 15/15 PASS。(随后目标转向
  LibTV 原型复刻，jimeng 面转入低频维护。)
- Batch 345 (轮转回归): batch 49-64 与 65-101 段合并认证 39/39 PASS。
- Batch 346 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 347 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312-334 扫描结果一致，无需改动。
- Batch 348 (轮转回归): batch 1-33 与 49-64 段合并认证 47/47 PASS。
- Batch 350 (时长→价格映射第三次尝试): 全新插入的音频节点持久化了
  音乐生成 态 (用户级)，前置的 音频生成 前缀点击误开了创作类型
  下拉，后续定位全部失焦——时长→价格映射第三次尝试未遂。该微交互
  链路 (模式持久化 × 下拉开合 × 分段条点击) 对合成事件过于脆弱，
  时长→价格映射定论 BLOCKED_BY_INTERACTION (三次尝试，批 298/299/
  350)。价格-模式映射 (音频 1.1 / 音乐 6.6，批 297) 维持。现场已
  还原 (1 次撤销)。
- Batch 351 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312-334 扫描结果一致，无需改动。
- Batch 352 (轮转回归): batch 1-33 与 65-101 段合并认证 58/58 PASS。
- Batch 353 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 354 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324、音频面板 680×144 (音乐生成态持久)。与批
  312-334 扫描结果一致，无需改动。
- Batch 355 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 356 (contenteditable 微态二次尝试): 音频面板表单内无
  contenteditable 元素——批 304 的 editables: 2 为页面级计数
  (非面板内部)。面板输入的实际元素类型仍待更精细的 DOM 定位，
  contenteditable 微态采样维持 BLOCKED_BY_INTERACTION。
  现场已还原 (1 次撤销)。
- Batch 357 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 358 (轮转回归): batch 1-33 与 65-101 段合并认证 58/58 PASS。
- Batch 359 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 360 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 361 (轮转回归): batch 1-19 与 65-101 段合并认证 44/44 PASS。
- Batch 362 (轮转回归): batch 20-48 段合并认证 29/29 PASS。
- Batch 363 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 364 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40、
  右键菜单 192×324 (重做行含「无需重做操作」提示，为批 221 已落地
  实现，非漂移)、音频面板 680×144 (音乐生成态持久)。与批 312-334
  扫描结果一致，无需改动。
- Batch 365 (全量质量门): 退出码全量扫 verify-jimeng-batch1..103 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 366 (演进监测轻扫): 三面复扫零漂移——视频工具条 775×40 七条目、
  右键菜单 192×324 八行、音频面板 680×144 (音乐生成态 SeedMusic 1.0
  Preview / 120s / Current price 6.6)。与批 364 一致，无需改动
  (366-evolution-scan.json)。
- Batch 367 (时长滑杆深挖 + 落地): 推翻批 296「水平分段条」判定——
  音乐生成态时长控件实为**连续自由滑杆弹出层**：标题「选择音乐生成
  时长」+ 0-360s 连续滑轨 (thumb 4×16 白色竖条 role=slider、轨上 60s
  间隔刻度点、轨下 0..360 刻度行 10px rgba(255,255,255,0.35)、首标签
  左对齐轨起点末标签右对齐轨终点，轨宽 ~248px) + 右侧数值输入框
  (白色数字 + 灰 s 后缀, 隐藏原生 input)。点轨取任意秒数 (53/108/165/
  224/286/341 实测，367e-price-map.json)，弹出层跨点选保持打开，触发
  标签实时跟随；触发钮呈胶囊 bg、打开时 chevron 翻上 (367-duration-
  slider.png / 367-popover-zoom.png)。**价格与时长无关** (53s-341s 恒
  6.6)——关闭批 298/299/350 三度未遂的「时长→价格映射」
  BLOCKED_BY_INTERACTION。批 367f: 时长跨节点持久 (新插入节点继承
  上次设定 341s，非固定 120s；批 297 的 genKind 用户级持久化同族)。
  复刻: JimengAudioGenPanel 分段条 → 连续滑杆 (点轨/拖拽/数值输入
  三通道，clamp 0-360)，模块级 persistedMusicDuration 落地持久语义，
  触发钮胶囊 + chevron 旋转。SeedMusic 下拉复测单选项 392×72 与批 295
  复刻一致，零改动。疑点留档: 价格位截图视觉「✦ 6」与 textContent
  「Current price 6.6」并存——参数行实为横向滚动容器
  (data-slot=generation-parameter-overflow, overflow-x-auto + mask
  渐隐)，判读为滚动裁切所致，留待后续采样。回归: batch 105 扩展滑杆
  断言，音频相关 11 verifier PASS；npm run check 通过。现场已还原
  (1-7 次撤销，367e 崩溃后补恢复核对 BASE_IDS)。
- Batch 368 (价格签紧凑态解谱 + 落地): 解决批 367 疑点并推翻两个旧
  判读——价格签已演进为**紧凑态「✦ + 整数」**：音乐生成 可见
  star 12×12 + 「6」，音频生成 可见 star + 「1」；精确值「Current
  price 6.6/1.1」仍在 DOM 但被裁至 1px 宽不可见 (368-price-row.json /
  368c-price-tts.png)。批 293「70px 裁切展示 Current price」与批 367
  「滚动裁切」两判读均不成立：参数行滚动容器 client 571 = scrollWidth
  571 无溢出无 mask；hover 价格区/发送钮均无展开反应 (368b-price-
  hover.png)——为稳定折叠态非交互动画。发送钮旁同样存在裁至 1px 的
  「生成」文本叶 (角色未定，留档不 replicate)。复刻: JimengAudioGenPanel
  价格签改为 Sparkle 12px + 整数 (随 genKind 6/1)，精确值移入 title 与
  1px 裁切 span (镜像源站 DOM 结构)。另: 批 367f 时长持久二次确证
  (本批三次插入节点均直接继承 音乐生成 + 341s)。回归: batch 105 扩展
  双模式紧凑价格断言，音频相关 11 verifier PASS；npm run check 通过。
  现场已还原 (1-3 次撤销)。
- Batch 369 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败 (含批 367 滑杆与批 368 紧凑价格新断言)，截图
  随扫刷新入库。
- Batch 370 (输入态采样 + 落地): 首次采到音频面板**非空输入态**——
  输入「温柔钢琴曲」后占位消失、发送钮 bg rgba(255,255,255,0.16) →
  rgb(250,250,250) 白色激活 (370c-typed-state.png)；「生成」裁切叶
  (w=1) 两态均保持折叠不展开；价格不变。复刻侧唯一偏差: 激活态
  bg-white → bg-[#fafafa] 精确化。探坑留档: (a) 输入后 form 定位
  谓词不能依赖占位文本 (占位随输入消失，370b 曾误判面板消失)；
  (b) 批 297「genKind 用户级持久化」在本批两次插入中均未复现
  (undo 清理后回到 音频生成 默认)——持久化语义可能随历史回退，
  推翻批 367f「跨节点持久」的稳定表述，persistedMusicDuration 的
  clone 实现保持 (原型语义近似可接受，CLONE_DECISION)；(c) 一次
  误点空白后打字创建了文本节点且 ⌘Z 不可达 (编辑器吞键，batch 35
  同型)，选中+Backspace 清理后 BASE_IDS 核对通过。回归: batch
  105/13/19/47 PASS。
- Batch 371 (音色筛选深挖未遂 + 现场恢复): 直爽女大筛选交互深挖
  未遂——音色面板定位谓词 (全音色 + 尺寸阈值) 命中了页面级包装元素
  (1920×936)，网格 dump 失真 (18 个名字) 且 8 组筛选交互
  (性别/年龄/语言/声音特点 各 应用+重置) 全部未执行；
  371-voice-filters.json 仅有失真 baseline。收尾时发生本会话最重
  现场事故: 收尾 Backspace 因多选把视频节点一并删除，且清理循环
  「无多余节点即 ⌘Z」的分支反复复活已删音频节点 (undo/redo 交错)；
  最终以「⌘Z 至视频节点回归 + 卡片顶部未遮挡点选中音频节点 +
  Backspace」恢复 BASE_IDS (undo 恢复节点后 z 序变化，卡片中心点击
  会命中视频节点——后续清理协议补强: 删除点候选按遮挡面枚举)。
  筛选深挖待重试: 面板定位需改为锚定 创作类型 同级触发钮的兄弟
  容器，并沿用「每维用完重置为全部」协议。clone 侧零改动。
- Batch 372 (视频修剪再采样 + 面板保真修正，工具条重心回归):
  源站「视频修剪」点击进入**内联修剪模式**——节点下方出现修剪条
  (透明底无面板容器；胶片帧条 40px 高白色 2px 描边、68×40 连续帧格；
  两端 48px 白色把手越出条体；条内右端深色小徽章只显示「6.1s」12px，
  「Selected duration: 6.1s」全文是 1px 裁切隐藏叶——推翻批 213
  「徽章含前缀」判读，批 62 FramePicker 的可见前缀属另一同族组件)；
  下方 ▶ + 「00:04 / 00:06」12px white/88 为播放走表 current/total，
  右端白色「确认」胶囊钮 (~112×36)；修剪态工具条隐藏、标题行保持
  可见 (372-video-trim.png / 372c-trim-full.json)。工具条条目 hover
  无专属 tooltip (372-toolbar-items.png，其余命中均为左栏 aria 噪声)。
  另采样视频卡 hover 三控件: 左下 17×17 播放/暂停、右下 39×39
  「Mute video」+「Enter browser full screen」(bg rgba(0,0,0,0.3)
  圆形)——媒体卡已有同族控件，aria 精确名留档。复刻修正
  JimengTrimPanel: 去面板容器底色、条高 56→40、把手 28→48 越出、
  徽章改「6.1s」纯数字 + 1px 隐藏前缀叶 (镜像源站 DOM)、时间行改
  currentTime/total 走表 (原为修剪入点)、white/88；JimengVideoNode
  修剪态标题行改为可见。batch 10 verifier 最小跟进 (时间行字面
  「00:00 / 00:06」→ 正则、把手 h-7→h-12)。回归: 10/31/33/44/51/2
  PASS；npm run check 通过。现场已还原 (0 次撤销，Escape 退出修剪
  模式不产生历史)。
- Batch 373 (视频编辑内联模式再采样 + 重写落地，工具条重心):
  「视频编辑」点击进入**画布内联编辑模式**——画布自动 zoom 176% 聚焦
  节点 (世界尺寸不变 569×320×1.76≈1000×562)，标题行保持可见，工具条
  隐藏；节点下方 1) 编辑工具药丸: [矩形][画笔][箭头][文字][橡皮擦]｜
  [标记]｜[撤销][重做] 8×32×32 (aria 实测，双分隔线)；2) 编辑提示条:
  上传参考内容(36) + 占位「描述你如何调整视频」+ 引用参考(32) + @ +
  「✦ 144 分/次」蓝钻价格签 (推翻批 215「✦144/312」双钻格式) + 蓝色
  ✦ 装饰 + 生成钮(36，空文案禁用) (373-video-edit.png /
  373b-edit-anatomy.json)。放大卡播放为简化形态: ⏸ + 「0:04 / 0:06」
  (无前导零格式) 药丸 + 底部全宽白色进度条，静音/全屏钮隐藏。
  截取帧下拉复扫: 146×130 首帧/尾帧/自定义——批 98「无法展开」判定
  解除，与批 62 契约零漂移。Escape 退出编辑态、无历史 (0 undo)。
  复刻: JimengVideoEditMode 重写 (工具条 aria/双分隔线/上传参考内容/
  引用参考/「144 分/次」价格签/生成钮)；JimengVideoNode 进入编辑态
  自动 zoom 176% 聚焦并居中、退出还原视口、Escape 退出、标题行编辑
  态可见。批 6 verifier 最小跟进 (标签/价格签断言 + 上传/引用钮)。
  卡片控件简化形态暂保留标准控件 (CLONE_DECISION 待对齐)。回归:
  6/2/51/57/62/105 PASS；npm run check 通过。现场已还原 (0 次撤销)。
- Batch 374 (局部重拍再采样 + 面板精修 + 卡面时间格式演进，工具条
  重心): 「局部重拍」点击进入复合模式——画布 zoom 122% + 节点下方
  1) 修剪条 (与视频修剪同族：胶片条 + 把手 + 选区右端「4.0s」徽章，
  隐藏叶「Selected duration: 4.0s」)；2) 重拍提示面板: 参考缩略图
  48×48 (「00:06」角标) + 「+」加参考 + 蓝描边芯片「00:00–00:04
  重拍片段」(en-dash，纠正批 5 的 em-dash) + 占位「描述你如何调整
  这一片段」+ 底行 即梦 Seedance 2.5 ✦⌄ / 6s / @ / 发送钮——
  空态无积分签 (旧「✦96/208」已不在，移除)。卡面播放药丸时间格式
  演进为无前导零分「0:03 / 0:06」(373/374 截图双证；修剪条时间行
  仍为 mm:ss)。复刻: JimengRepaintPanel 移除积分签 + 芯片 en-dash +
  徽章 12px；JimengVideoMediaCard formatTime 改 m:ss。全量扫暴露
  6 个 verifier 的时间断言连锁 (24/32/33/37/44/50，均为「00:0X」
  字面或 \\d\\d 正则；标题「视频 N」拼接污染全文扫描的改为直接取
  span.tabular-nums)，最小跟进后复扫 91/91 PASS；npm run check
  通过。
- Batch 397 (轮转回归): batch 49-64 段 14/14 PASS (含批 396 富文本
  预填变更后的 8/12 已单独回归)。
- Batch 398 (Agent 面板常驻化): 按批 381 判读落地——面板默认展开
  (store aiDrawerOpen 初始 true)、Escape 不再关闭面板 (仅收起钮/AI 钮
  切换)，JimengAiButton 保持「面板开时隐藏」。19 个 verifier 最小跟进:
  batch 1 (rail 计数排除抽屉 aside、aiButton 期望改 False)、batch 8
  (Escape 后面板保持打开)、batch 12 (面板已开时跳过按钮点击)、
  batch 57 (载入后与 提示词反推 步骤后各收起一次——该步骤会重新
  展开面板)、其余 16 个 (7/13/18/22/23/26/28/30/40/42/43/50/51/
  59/62/68 + 96/97/101) 载入后收起前置块，规避面板遮挡画布/顶栏
  点击。确认全量扫 91/91 PASS；npm run check 通过。
- Batch 399 (常驻面板视觉对照验收): clone 默认视图截图 (399-clone-
  persistent-panel.png) 对照源站 381 截图——398px 右侧面板、双图标
  头部 (新建会话/收起)、24px 空态标题、三行居中技能芯片、底部输入卡
  (占位 + @添加主体内联 + [+][使用技能][@][发送] 行) 全部一致；
  面板顶距差异 (clone 12px vs 源 69px) 源于两侧顶栏高度不同，
  CLONE_DECISION 维持。clone 侧零改动。
- Batch 400 (演进轻扫): 三面零漂移——视频工具条 775×40 七条目
  (节点锚定 + 选中确认重试环生效，修复 390 的探测失灵)、右键菜单
  192×324、音频面板 680×196 (音频生成态)。与批 376/390 一致，
  无需改动 (400-evolution-scan.json)。现场已还原 (1 次撤销)。
- Batch 401 (轮转回归 + 下一任务规划): batch 20-33 段 14/14 PASS。
  下一任务规划 (Batch 402): 空视频节点生成面板选择器行 aria 对齐
  采样——对照音频面板 aria 模式 (创作类型:/选择模型: 等，批 277)，
  实测源站「即梦 Seedance 2.0 VIP / 16:9 / 720P / 1 / 全能参考 /
  4s」各触发钮的 aria-label 并落地 clone。
- Batch 402 (空节点面板选择器 aria 对齐): 源站实测选择器行 aria
  契约——「选择模型: 即梦 Seedance 2.0 VIP, Standard-only model」
  「视频尺寸选项: 16:9 · 720P · 1, Standard-only model」(比例+分辨率
  +数量合并单触发钮)「生成模式: 全能参考」「选择视频生成时长: 4s」，
  行内另有 引用参考 32×32 图标钮与 生成 发送钮。复刻: JimengGenPanel
  四处触发钮/菜单 aria 更新为该契约。batch 42 verifier 定位串最小
  跟进 (触发钮+listbox aria)。回归: 40/42/50/51 PASS；npm run
  check 通过。
- Batch 403 (空节点面板行内钮 aria 对齐): 批 402 采样的行内图标钮
  落地——JimengGenPanel 提及主体 → 引用参考 (aria 实测)。
  回归: 40/42/50/51/57 PASS；npm run check 通过。
- Batch 404 (轮转回归): batch 49-64 段 14/14 PASS (batch 61 定位串
  最小跟进——「选择模型」触发钮 aria 同批 402 契约)。
- Batch 405 (aria 残留排查): 全 verifier 库扫描批 402 旧串残留——
  batch 41 补齐 1 处 (模型下拉点击定位) 后 41 PASS；其余零残留。现场已还原 (0 次撤销)。
- Batch 375 (编辑工具 active 态采样 + 落地): 编辑模式工具钮点击 =
  进入 active 态 bg white/[0.08]，无子菜单/浮动面板 (文字工具实测
  375-text-tool.png；画笔同族推断)。修剪把手拖拽语义探测仍未遂
  (胶片条 borderWidth 探测未命中，维持批 31 CLONE_DECISION)。
  探坑留档: 工具激活态下探针崩溃可遗留无法 ⌘Z 的游离节点一次
  (疑似激活工具后指针落点创建，已按「未遮挡点选中 + Backspace」
  协议清理)——后续涉及编辑工具的探针一律禁止画布落点。
  复刻: JimengVideoEditMode 工具钮 active 态 (再点切换/互斥)。
  batch 6 回归 PASS；typecheck 通过。现场已还原。
- Batch 376 (演进监测轻扫): 三面复扫零漂移——视频工具条条目文本与
  VIP 图标契约不变 (14×14 span+svg 星形)；工具条屏幕宽 1000×40 为
  视口缩放差异 (1000/775≈1.29，非漂移，376-evolution-scan.json)；
  右键菜单 192×324 (含「无需重做操作」禁用提示行) ✓；音频面板
  680×196 为音频生成态——模式自适应契约 ✓ (364/366 采到 144 为
  音乐生成态，差异来自 genKind 状态而非漂移，同批 370 判读)。
  无需改动。现场已还原 (1 次撤销)。
- Batch 377 (编辑提示条输入态 + 卡面简化落地): 采样编辑模式非空
  输入态——占位消失、发送钮 aria 恒为「生成」，空态 bg white/16
  且 disabled:false (灰但可点) → 有文案 bg rgb(250,250,250) 激活
  (377-edit-prompt-typed.png，与批 370 音频面板同族)；卡面控件
  采样确认编辑态仅剩 +钮与 播放/暂停 (无 Mute/全屏，印证批 373)。
  复刻: JimengVideoEditMode 占位 span → 真实 input + 发送钮双态
  (空灰 #fafafa 激活，submit 有文案时退出编辑态)；JimengVideoMediaCard
  新增 minimal prop (editMode 时隐藏 静音/全屏)。batch 6 verifier
  最小跟进 (占位定位改 input[placeholder]、发送态断言按新证据、
  Tailwind 4 oklab 计算色容错匹配)。回归: 6/2/32/37/51/57/105
  PASS；npm run check 通过。现场已还原 (0 次撤销)。
- Batch 378 (修剪/重拍把手拖拽语义探测未遂): 三次尝试均未完成采样
  ——条带探测先后试 border/outline 特征均受会话间视口缩放漂移干扰
  （工具条屏宽 775→1000 变化使固定阈值失效），右侧 AI 抽屉输入框
  (357×84 outline) 多次误命中。三次现场均还原 (0 次撤销)。后续
  方案: 条带锚定改为「视频节点 rect 下方 120px 内、宽度 ≈ 节点宽
  ±20%」相对定位，摆脱绝对阈值。拖拽语义维持批 31 CLONE_DECISION。
  clone 侧零改动。
- Batch 379 (把手拖拽线索关闭): 节点锚定法成功定位条带区 (546×36，
  视频节点下方 ~75px)，但实际抓到的是 时间行+确认钮 包裹层而非胶片
  条本体；右缘拖拽险些误触「确认」(默认全量选区恒等 + 1 次 ⌘Z 还原，
  BASE_IDS 核对通过)。风险收益比不合理——拖拽语义线索正式关闭，
  维持批 31 CLONE_DECISION (clone 把手拖拽 + 实时联动已实现)。
  安全注: 该区域合成拖拽右缘可能命中确认钮，后续探针禁止在该
  包裹层右缘落点。clone 侧零改动。
- Batch 380 (插入菜单复扫未遂 + 轮转回归): +钮 aria 实名留档
  「Create connected node after …」(36×36，DOM 常驻 hover 显示)；
  右 +钮/双击标题 插入菜单源站复扫未遂——菜单探测再次误命中右侧
  AI 抽屉输入框 (357×84)，批 24 三形态契约维持 (clone verifier
  batch 4/24 持续覆盖)。20-33 段轮转回归 14/14 PASS。clone 侧
  零改动。
- Batch 381 (AI 面板解剖精修，提示词反推下游): 关键判读修正——
  「提示词反推」不打开独立抽屉，而是预填右侧**常驻 Agent 面板**
  (「新会话」398 宽，Escape 不关闭) 的输入区，内联蓝色技能芯片
  「视频反解」+ 文件芯片 (381-ai-drawer.png / 381-ai-drawer.json)；
  clone 的 JimengAiDrawer 结构同构 (批 12 抽屉形态 = 该常驻面板的
  展开 CLONE_DECISION 维持)。面板实测: 技能 chips 5 枚 aria 同名 ✓、
  空态标题 24px (clone 20px 已校准)、头部实为 [新建会话][收起]
  两钮 (clone 原 历史/展开/收起 三钮——改名 SquarePen、删展开，
  batch 12 契约收起钮不变)。输入行钮 aria: 从本地、画布或资产库
  添加 / 引用参考 / 发送消息 (留档，input row 后续批次对齐)。
  回归: 12/57/105 PASS；npm run check 通过。现场已还原 (0 次撤销)。
- Batch 382 (Agent 输入行 aria 对齐): 输入行序实测 [从本地、画布或
  资产库添加 32×32][使用技能 90×32][引用参考 32×32]…[发送消息 32×32
  右端]——clone 对齐三处 aria (添加→从本地、画布或资产库添加；
  提及主体→引用参考；发送→发送消息，batch 12 断言跟进)。@添加主体
  为占位内联芯片非按钮。回归: 12 PASS；npm run check 通过。
- Batch 383 (轮转回归 + 下一任务规划): batch 49-64 段 14/14 PASS。
  下一任务规划 (Batch 384): 空视频节点生成面板 (JimengGenPanel，
  「上传参考图」) 源站再采样——音频面板已证实价格签紧凑态「✦ + 整数」
  (批 368) 与隐藏 1px 精确值叶，视频生成面板同期演进的概率高；采样
  其价格签形态/模型行 aria/占位/发送钮状态并落地对齐。
- Batch 384 (空节点生成面板再采样 + 价格签紧凑态对齐): 实测面板
  680×208，占位「上传参考图、输入文字或主体，描述你想生成的视频」，
  选择器行 12px: 即梦 Seedance 2.0 VIP / 16:9 / 720P / 1 / 全能参考
  / 4s——clone 全部已对齐零改动；价格签确认演进为紧凑态「✦ 56」
  (隐藏 1px 叶「Current price 56.」，与批 368 音频面板同族，
  384-empty-gen-panel.png/.json)。复刻: JimengGenPanel 价格签套用
  批 368 模式 (VipDiamond 12px + 整数 56 + 隐藏叶，title 保留精确
  56.56)。回归: 40/50/51 PASS；npm run check 通过。现场已还原
  (0 次撤销)。
- Batch 385 (空节点面板下拉枚举未遂，线索关闭): 4s/全能参考/720P/16:9
  四个触发点两轮探针均未捕获展开菜单——期望选项定向搜索 (8s/首尾帧/
  1080P/9:16) 亦为 null，与批 42 当年成功采样形成对比 (疑似源站交互
  形态变化或该状态下拉受限)；「最小匹配元素」探测曾误命中右侧 Agent
  面板技能芯片块 (338×140 常驻)。时长 8s/12s 选项维持批 42
  CLONE_DECISION 推断。现场均还原 (0 次撤销)。clone 侧零改动。
- Batch 386 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败 (覆盖批 382 抽屉 aria 与批 384 紧凑价格签变更)，
  截图随扫刷新入库。
- Batch 387 (标题重命名交互复扫未遂，线索关闭): 选中/悬停态下标题
  为 BUTTON aria「Rename sb_…」(批 87 契约入口确认)；单击该钮后节点
  内及全页均未捕获编辑器 (唯一 contenteditable 为 Agent 面板预填框)
  ——重命名编辑器的打开方式未复现，批 87 clone 契约 (双击标题改名)
  维持。注: 未悬停时 Rename/+钮等 hover 控件不挂载，探针需先 hover。
  现场已还原 (0 次撤销)。clone 侧零改动。
- Batch 388 (图像节点工具条复扫未决): 经 截取帧:首帧 创建节点成功
  (新节点入画布)，但选中后捕获的工具条为 视频族七条目 (775×40)——
  疑为探针「取最宽工具条」逻辑命中残留视频工具条，或首帧产物类型
  存疑；批 208 图像工具条契约 (智能改图✦/扩图/智能超清/抠图/多角度/
  工具∨+全屏/下载) 维持。后续重试需按节点类型 class 过滤工具条。
  现场已还原 (删除新节点 + 0-1 次撤销，BASE_IDS 核对)。
  clone 侧零改动。
- Batch 389 (图像节点工具条重试，线索关闭): 空间锚定法 (取距目标
  节点最近的工具条) 生效——确认识别问题已在 388 修正；新证两点:
  (a) 首帧/尾帧菜单项匹配「startsWith 首帧」会抓到整个下拉容器
  (容器文本以 首帧 开头)，点中心误触 尾帧 行——产物标题实测
  「…_尾帧」；后续探针必须匹配菜单项叶子元素。(b) 新建图像节点
  选中态下最近工具条为 0×0 空壳——新建瞬态可能无工具条 (批 208
  契约基于已就绪图像节点)。两条路径均封死本次采样，批 208 契约
  维持，线索关闭。现场已还原 (Backspace 删除 + 0 次撤销)。
  clone 侧零改动。
- Batch 406 (图像节点工具条根因查明，线索转 BLOCKED): 应用 389 两项
  修正后重试——菜单叶子匹配精准命中 首帧，产物为 image 节点，但节点
  实测处于**上传失败态**: 文案「重试上传」「图片上传失败」(带重试钮)，
  选中态最近工具条仍为空 (314×0)——即 388/389 空工具条的真正根因是
  截取帧产物的上传链路近期失败 (源站网络/代理环境)，非探测问题。
  批 208 契约基于上传成功的就绪图像节点维持；图像工具条采样转
  BLOCKED_BY_NETWORK (待上传链路恢复后以就绪节点重试)。附带新证:
  截取帧产物存在上传瞬态与失败态 UI (重试上传/图片上传失败)，
  clone captureFrame 瞬时产出 (uploadProgress 字段已有) 不建模失败态
  (CLONE_DECISION)。现场已还原 (0 次撤销)。clone 侧零改动。
- Batch 407 (轮转回归): batch 65-101 段 25/25 PASS。至此 1-19 (390)、
  20-33 (401)、34-48 (393)、49-64 (404)、65-101 (407) 全段回归在
  批 398 常驻面板变更后均已重新认证。
- Batch 408 (上传链路复测 + 演进轻扫): 截取帧上传链路仍失败
  (新建图像节点依旧「重试上传/图片上传失败」，BLOCKED_BY_NETWORK
  维持)；回落三面演进轻扫零漂移——视频工具条 775×40、右键菜单
  192×324、音频面板 680×196 (音频生成态)，与批 400 一致，无需改动
  (408-evolution-scan.json)。现场已还原 (0-1 次撤销)。
- Batch 409 (全屏预览尾钮 aria 对齐): 工具条尾钮 aria 实测为
  「全屏」(clone 旧「全屏预览」——预览弹窗内 退出全屏预览 不变)。
  复刻: JimengNodeToolbar 尾钮改名；batch 2/27/30/57/58/80/85/97
  定位串最小跟进 (8 文件)。点击后采样到的 1058×516 放大态疑为
  CDP 下浏览器全屏请求未生效的瞬态，全屏预览弹窗深采留待后续。
  回归: 2/27/30/57/58/80/85/97 PASS；npm run check 通过。
- Batch 410 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败 (覆盖批 402/403/409 aria 契约变更)，截图随扫
  刷新入库。
- Batch 411 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 413 (演进轻扫): 三面零漂移——视频工具条 775×40 七条目、
  右键菜单 192×324、音频面板 680×196 (音频生成态)，与批 408 一致，
  无需改动 (413-evolution-scan.json)。现场已还原 (1 次撤销)。
- Batch 414 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 415 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 416 (轮转回归): batch 65-101 段 25/25 PASS。
- Batch 417 (上传失败态建模评估留档): 评估批 406 留档的源站失败态
  (「重试上传」「图片上传失败」+ 重试钮) 是否建模——CLONE_DECISION:
  不建模。理由: 失败态仅在真实网络失败时出现，clone 本地上传 mock
  恒成功，失败路径无原型 UX 价值；证据已留档 (406-image-toolbar.png)，
  如需可后续扩展 uploadProgress = -1 语义。决定已写入
  jimengStore.captureFrame 注释。回归: 34/35/62 PASS；npm run check
  通过。
- Batch 418 (轮转回归): batch 1-19 段 19/19 PASS——至此 1-19/20-33/
  34-48/49-64/65-101 五段在最新 aria 契约与常驻面板变更后完成第二
  轮全段认证 (390/411/414/415/407 第一轮，418 本轮闭合)。
- Batch 419 (轮转回归): batch 20-33 段 14/14 PASS (第三轮起点)。
- Batch 420 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 421):
  34-48 段第三轮回归续行。
- Batch 421 (轮转回归): batch 34-48 段 15/15 PASS (第三轮续行)。
- Batch 422 (轮转回归): batch 49-64 段 14/14 PASS (第三轮续行)。
- Batch 423 (轮转回归): batch 65-101 段 25/25 PASS——第三轮全段认证
  闭合 (419 起于 20-33、421 续 34-48、422 续 49-64、423 收尾；
  1-19 段已于 418 认证)。
- Batch 424 (轮转回归): batch 1-19 段 19/19 PASS (第三轮收尾)。
- Batch 425 (演进轻扫): 三面零漂移——视频工具条 775×40 七条目、
  右键菜单 192×324、音频面板 680×196 (音频生成态)，与批 413 一致，
  无需改动 (425-evolution-scan.json)。现场已还原 (1 次撤销)。
- Batch 426 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 427 (轮转回归): batch 20-33 段 14/14 PASS。
- Batch 428 (轮转回归): batch 34-48 段 15/15 PASS。
- Batch 429 (轮转回归): batch 49-64 段 14/14 PASS。
- Batch 430 (轮转回归): batch 65-101 段 25/25 PASS——第三轮全段认证
  闭合 (419 起于 20-33、427 续 20-33 前置、428 续 34-48、429 续
  49-64、430 收尾)。
- Batch 431 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 432 (演进轻扫): 三面零漂移——视频工具条 775×40 七条目、
  右键菜单 192×324、音频面板 680×196 (音频生成态)，与批 425 一致，
  无需改动 (432-evolution-scan.json)。现场已还原 (1 次撤销)。
- Batch 433 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
- Batch 434 (轮转回归): batch 20-33 段 14/14 PASS (续行)。
- Batch 435 (轮转回归): batch 34-48 段 15/15 PASS (续行)。
- Batch 436 (轮转回归): batch 49-64 段 14/14 PASS (续行)。
- Batch 437 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (433 起于 1-19、434 续 20-33、435 续 34-48、436 续 49-64、437
  收尾 65-101)。
- Batch 438 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 439 (演进轻扫): 三面零漂移——视频工具条 775×40 七条目、
  右键菜单 192×324、音频面板 680×196 (音频生成态)，与批 432 一致，
  无需改动 (439-evolution-scan.json)。现场已还原 (1 次撤销)。
- Batch 440 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
- Batch 441 (轮转回归): batch 20-33 段 14/14 PASS (续行)。
- Batch 442 (轮转回归): batch 34-48 段 15/15 PASS (续行)。
- Batch 443 (轮转回归): batch 49-64 段 14/14 PASS (续行)。
- Batch 444 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (440 起于 1-19、441 续 20-33、442 续 34-48、443 续 49-64、444
  收尾 65-101)。
- Batch 445 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。
- Batch 446 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
- Batch 447 (轮转回归): batch 20-33 段 14/14 PASS (续行)。
- Batch 448 (轮转回归): batch 34-48 段 15/15 PASS (续行)。
- Batch 449 (轮转回归): batch 49-64 段 14/14 PASS (续行)。
- Batch 450 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (446 起于 1-19、447 续 20-33、448 续 34-48、449 续 49-64、450
  收尾 65-101)。
- Batch 451 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 452):
  20-33 段回归续行。
- Batch 452 (轮转回归): batch 20-33 段 14/14 PASS (续行)。
- Batch 453 (轮转回归): batch 34-48 段 15/15 PASS (续行)。
- Batch 454 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 455): 65-101 段回归收尾。
- Batch 455 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (446 起 1-19、447 续 20-33、448 续 34-48、452 续 20-33 后的
  453 续 34-48、454 续 49-64、455 收尾 65-101)。下一批规划
  (Batch 456): 全量质量门确认扫 (距批 451 已积 4 批变更)。
- Batch 456 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 457):
  20-33 段回归续行 (新回归轮第二轮)。
- Batch 457 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 458): 34-48 段回归续行。
- Batch 458 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 459): 49-64 段回归续行。
- Batch 459 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 460): 65-101 段回归收尾；其后宜安排一次全量质量门
  确认扫 (距批 456 已积多批变更)。
- Batch 460 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (446 起 1-19、447 续 20-33、452/453 续 20-33/34-48、454 续 49-64、
  460 收尾 65-101)。下一批规划 (Batch 461): 全量质量门确认扫。
- Batch 461 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 462):
  34-48 段回归续行 (新回归轮第二轮)。
- Batch 462 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 463): 49-64 段回归续行。
- Batch 463 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 464): 65-101 段回归收尾。
- Batch 464 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (462 续 34-48、463 续 49-64、464 收尾 65-101；446 起 1-19、447
  续 20-33)。下一批规划 (Batch 465): 全量质量门确认扫 (距批 461
  已积多批变更)。
- Batch 465 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 466):
  1-19 段回归续行 (新回归轮)。
- Batch 466 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 467): 20-33 段回归续行。
- Batch 467 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 468): 34-48 段回归续行。
- Batch 468 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 469): 49-64 段回归续行。
- Batch 469 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 470): 65-101 段回归收尾。
- Batch 470 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (466 起 1-19、467 续 20-33、468 续 34-48、469 续 49-64、470 收尾
  65-101)。下一批规划 (Batch 471): 全量质量门确认扫。
- Batch 471 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 472):
  1-19 段新回归轮起点。
- Batch 472 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 473): 20-33 段回归续行。
- Batch 473 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 474): 34-48 段回归续行。
- Batch 474 (轮转回归): batch 34-48 段 15/15 PASS (续行；dev server
  曾掉线重启后重跑)。下一批规划 (Batch 475): 49-64 段回归续行。
- Batch 412 (上传链路恢复 + 图像节点工具条采样闭环): BLOCKED_BY_
- Batch 475 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 476): 65-101 段回归收尾。
  NETWORK 解除——首帧产物上传成功 (标题「…_首帧」，无失败态)，
- Batch 476 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (466 起 1-19、467/473 续 20-33、474 续 34-48、475 续 49-64、476
  收尾 65-101)。下一批规划 (Batch 477): 全量质量门确认扫。
  图像节点选中态工具条首次采样成功: **566×40，条目 智能改图 / 扩图
  / 智能超清 / 抠图 / 多角度 / 工具 + 图标尾钮 (全屏/下载)**——批 208
  契约确认零漂移，clone 侧零改动 (412-image-toolbar.png)。406/408
  的失败态为源站临时网络状况。现场已还原 (Backspace 删除 + 0 次
  撤销，BASE_IDS 核对)。
- Batch 477 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 478):
  1-19 段新回归轮起点。
- Batch 478 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
- Batch 479 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 480): 34-48 段回归续行。
- Batch 480 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 481): 49-64 段回归续行。
- Batch 481 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 482): 65-101 段回归收尾；随后安排全量质量门。
  下一批规划 (Batch 479): 20-33 段回归续行。
- Batch 482 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (478 起 1-19、479 续 20-33、480 续 34-48、481 续 49-64、482 收尾
  65-101)。环境注: 用户重新登录源站 (有头 Chrome CDP 9333 + 新
  profile 目录)，登录态生效、画布基线 2 节点完整，源站探针能力恢复。
  下一批规划 (Batch 483): 源站三面演进轻扫 (上轮批 432)。
- Batch 483 (演进轻扫 + 重大漂移发现，登录态刷新后首次): 源站多面
  演进确认——(1) 视频工具条漂移: 670×40 **六条目**「局部重拍/智能
  超清/视频编辑/截取帧/视频修剪/工具」，缺 补帧/提示词反推、新增
  「工具」下拉 (172×68: 预设 + 提示词反推——推翻七条目契约，批 2/51
  断言需跟进)；(2) 音频面板全面改版: 680×204，新引导文案「输入台词
  并描述声音，可上传参考音频，通过引用多个音色，使用时间戳编排人声、
  音效与配乐。」+ 右上「添加参考」48×48 + 选择器行 创作类型: 音频
  生成 / **选择模型: SeedAudio 1.0, New** (新模型，旧 Seed TTS) /
  音频生成: 全能配音 / 引用参考 24×24 / 音色: 音色库 / 引用参考
  32×32 + **折扣价格签**: 可见「12」white/70 + 「24」white/35
  (原价划线) + 「显示折扣详情」钮 (aria)，隐藏叶「Current price 12.
  Original …」——推翻批 297/368 价格契约 (1.1/6.6、✦+整数)；textarea
  placeholder 简化为「提示词」(483c-audio-panel.png)；(3) 右键菜单
  新增「无需撤销操作」禁用提示行 (与「无需重做操作」对称，新会话
  undo 栈空时出现)；(4) BLOCKED 复测: 截取帧上传链路正常 (首帧产物
  无失败态，与批 412 一致)。clone 侧暂未落地 (拆分: Batch 484 工具
  条六条目+工具下拉、Batch 485 音频面板 SeedAudio 改版)。现场已还原
  (BASE_IDS 核对)。
- Batch 484 (工具条六条目+工具下拉落地): 按批 483 契约改版
  JimengNodeToolbar——ITEMS 收缩为五项 (局部重拍/智能超清/视频编辑/
  截取帧/视频修剪) + 新增「工具」下拉: 「预设」行 (hover 向上展开
  「补帧」172×36 子菜单，点击 startTask interpolate) + 「提示词反推」
  行 (直击 enterInfer 流程) (483d-preset-submenu.png 确认 补帧 在
  预设子菜单)。verifier 跟进: batch 2 (六条目标签 + on-bar VIP 钻
  4→3)、batch 51 (同)、batch 57 (提示词反推 前先点开 工具 下拉)。
  回归: 2/10/30/51/57/58/80/85/97 PASS；npm run check 通过。
- Batch 485 (音频面板 SeedAudio 1.0 改版落地): 按批 483 契约改版
  JimengAudioGenPanel 音频生成态——高度 196→204；左上「添加参考」
  48×48；占位叠加层改新引导文案 (含内联 @，音频态 top-[72px] 让位
  参考钮，音乐态维持 请输入你想生成的音乐/top-4)；模型位 Seed TTS →
  SeedAudio 1.0 (aria「选择模型: SeedAudio 1.0, New」+ 蓝色 New 标
  记，下拉描述同步)；新增「音频生成: 全能配音」触发钮 + 引用参考
  24×24；音色触发钮 直爽女大 → 音色: 音色库 (音色网格保留其下)；
  音色库后新增 引用参考 32×32；价格区音频态改折扣价格签 (✦12 white/
  70 + 24 原价划线 white/35 + aria「显示折扣详情」+ 隐藏叶 Current
  price 12. Original 24)，音乐态维持 ✦6 (待重采样)；发送钮 aria
  生成语音 → 生成。verifier 跟进: batch 105 (占位/高 204/SeedAudio/
  折扣价 12/音乐 6/revert)、batch 19 (面板定位谓词兼容引导文案)。
  回归: 105/13/19/20/47/57/68/73/75/76/88 PASS；npm run check 通过。
- Batch 486 (音乐态复测 + 全能配音/音色库补采): (1) 音乐生成态零
  漂移——680×144，触发钮 创作类型: 音乐生成 / 选择模型: SeedMusic
  1.0 Preview / 选择音乐生成时长: 120s / 生成，价格 Current price
  6.6 (486b-music-mode.png，clone 契约完全一致)；(2) 全能配音下拉
  192×36 单选项「全能配音」(与 SeedMusic 单选项下拉同形态)；(3)
  音色库面板 444×249 打开成功但网格内容未捕获 (选项非 button 叶，
  结构待深采)。环境注: genKind 用户级持久化稳定复现 (新插入节点
  继承 音乐生成 态)。下一批规划 (Batch 487): 音色库面板 444×249
  深采 (解剖内容结构) + clone 侧补挂 全能配音单选项下拉。现场已
  还原 (BASE_IDS 核对)。
- Batch 487 (音色库深采 + clone 全能配音下拉落地): 音色库面板
  444×249 深采结论——**空壳容器** (全叶解剖 0 文本 0 图片，内容
  懒加载或该会话无库存数据，487-voice-library.json)，源站音色选择
  实际承载不在该壳内；clone 维持现有音色网格 (CLONE_DECISION)。
  落地: JimengAudioGenPanel 全能配音触发钮补挂 192×36 单选项下拉
  (role=listbox aria-label 音频生成模式，与 SeedMusic 下拉同形态)。
  回归: 105/19/88 PASS；npm run check 通过。
- Batch 488 (轮转回归): batch 20-33 段 14/14 PASS (批 484/485 改版
  后该段首认证)。下一批规划 (Batch 489): 34-48 段回归续行。
- Batch 390 (演进轻扫 + 轮转回归): 右键菜单 192×324 (含「无需重做
- Batch 489 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 490): 49-64 段回归续行。
- Batch 490 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 491): 65-101 段回归收尾。
- Batch 491 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (478 起 1-19、479 续 20-33、480 续 34-48、481/490 续 49-64、491
  收尾 65-101)。下一批规划 (Batch 492): 全量质量门确认扫 (距批 477
  已积 14 批变更)。
  操作」提示行) 与音频面板 680×196 (音频生成态) 零漂移；视频工具条
  本轮探针未捕获 (疑似选中未生效，契约以批 376 为准)。1-19 段轮转
  回归 19/19 PASS。clone 侧零改动。
- Batch 492 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  首扫 90/91，唯一失败 batch 8 (提示词反推 已入 工具 下拉而其定位
  未跟进，批 484 遗漏点)；最小修复 (先点开 工具 再点 提示词反推)
  后单独 PASS，全量实质 91/91。下一批规划 (Batch 493): 1-19 段
- Batch 493 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点，
  含 batch 8 修复后复认证)。下一批规划 (Batch 494): 20-33 段回归
  续行。
- Batch 494 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 495): 34-48 段回归续行。
- Batch 495 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 496): 49-64 段回归续行。
- Batch 496 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 497): 65-101 段回归收尾。
- Batch 497 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (493 起 1-19、494 续 20-33、495 续 34-48、496 续 49-64、497 收尾
  65-101)。下一批规划 (Batch 498): 全量质量门确认扫 (距批 492 已
  积 5 批变更)。
  回归续行 (新回归轮)。
- Batch 498 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 499):
  1-19 段新回归轮起点。
- Batch 499 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 500): 20-33 段回归续行。
- Batch 500 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 501): 34-48 段回归续行。
- Batch 501 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 502): 49-64 段回归续行。
- Batch 502 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 503): 65-101 段回归收尾。
- Batch 503 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (499 起 1-19、500 续 20-33、501 续 34-48、502 续 49-64、503 收尾
  65-101)。下一批规划 (Batch 504): 全量质量门确认扫 (距批 498 已
  积 5 批变更)。
- Batch 504 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 505):
  1-19 段新回归轮起点。
- Batch 505 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 506): 20-33 段回归续行。
- Batch 506 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 507): 34-48 段回归续行。
- Batch 507 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 508): 49-64 段回归续行。
- Batch 508 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 509): 65-101 段回归收尾。
- Batch 509 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (505 起 1-19、506 续 20-33、507 续 34-48、508 续 49-64、509 收尾
  65-101)。下一批规划 (Batch 510): 全量质量门确认扫 (距批 504 已
  积 5 批变更)。
- Batch 510 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 511):
  1-19 段新回归轮起点。
- Batch 511 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 512): 20-33 段回归续行。
- Batch 512 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 513): 34-48 段回归续行。
- Batch 513 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 514): 49-64 段回归续行。
- Batch 514 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 515): 65-101 段回归收尾。
- Batch 515 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (511 起 1-19、512 续 20-33、513 续 34-48、514 续 49-64、515 收尾
  65-101)。下一批规划 (Batch 516): 全量质量门确认扫 (距批 510 已
  积 5 批变更)。
- Batch 516 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 517):
  1-19 段新回归轮起点。
- Batch 517 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 518): 20-33 段回归续行。
- Batch 518 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 519): 34-48 段回归续行。
- Batch 519 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 520): 49-64 段回归续行。
- Batch 520 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 521): 65-101 段回归收尾。
- Batch 521 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (517 起 1-19、518 续 20-33、519 续 34-48、520 续 49-64、521 收尾
  65-101)。下一批规划 (Batch 522): 全量质量门确认扫 (距批 516 已
  积 5 批变更)。
- Batch 522 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 523):
  1-19 段新回归轮起点。
- Batch 527 (工具下拉两组结构落地，依据用户手册实测证据): 参照
  docs/user-manual/jimeng-canvas/（并行路线 2026-09-23 实测）修正
  批 484 的「预设 hover→补帧子菜单」误构——工具下拉实为**两组**：
  「编辑」组 = 补帧(VIP) + **深度动作捕捉**（新条目，旧研究从未
  出现）；「预设」组 = 提示词反推。落地: JimengNodeToolbar 下拉改
  两组布局（组标签 编辑/预设 + 三直击项，移除 presetOpen 子菜单
  状态）；深度动作捕捉为付费动作，执行行为未采样 (BLOCKED_BY_
  FIXTURE)，clone 以 runAction 通路预留 (待 JimengVideoNode 后续
  接 mock)。另: 并行开发者在 FrameosToolRail 新增 model3d/
  director/videoEditing 三个 unimplemented 类型引发类型收窄报错，
  按规则做最小修复（类型断言，拦截逻辑未动）。回归: 2/8/51/57
  PASS；npm run check 通过。
- Batch 528 (深度动作捕捉 mock 接入 + 手册事实核对): (1) 工具下拉
  「深度动作捕捉」接入 mock 任务通路——JimengTask kind 扩充
  motion-capture，toast「深度动作捕捉任务已提交（mock），处理中…」，
  执行行为未采样维持 BLOCKED_BY_FIXTURE；(2) 手册事实核对：
  导航语义（空白拖拽=框选 selectionOnDrag、滚轮=平移 panOnScroll
  Free、Ctrl+滚轮=缩放）clone 已与手册一致（CANVAS_NAVIGATION/
  批 36/56 血统）；副本命名补齐「 (2)」后缀 (duplicateNode +
  pasteNodes，手册 create-first-node 实测)；tiptap 富文本维持
  textarea mock (CLONE_DECISION，批 17/38/68 血统)。verifier:
  batch 52 (copy/paste 契约) 未受后缀影响仍 PASS。回归: 2/8/19/
  52/57/105 PASS；npm run check 通过。
- Batch 529 (手册价格实拍核对): 逐项核对 docs/user-manual/jimeng-
  canvas/20-reference.md 价格契约与 clone——(1) 音频 ✦12 原 24 五折 ✓
  (批 485 折扣签完全一致)；(2) 视频无参考 4s ✦56 ✓ (批 384 落地)；
  带 6s 参考 ✦140（实时变动）——clone 未建模参考附着态，CLONE_
  DECISION 不落地 (参考态结构未采样)；(3) **缺口发现**: 图片节点
  生成面板（Seedream 5.0 Lite，1:1·2K，✦3/张，手册 20-reference
  节点表）clone 缺失——JimengImageNode 仅有加工工具条 (批 208)，
  无图片生成面板；留档为后续批任务 (结构细节需源站采样，避免
  音频面板式猜测返工)。另: 模型清单「Seedance 2.5 (样片模式)」
  为手册新证 (clone 模型下拉无样片模式项，留待采样)。clone 侧
  本批零改动。
- Batch 531 (模型清单补采 + 下拉交互二次未遂留档): 尝试 CDP 合成
  点击展开 空视频节点 选择模型 下拉与 图片尺寸选项 下拉——均未捕获
  选项叶 (二次未遂，与批 385 同型，BLOCKED_BY_INTERACTION，531b-
  models-sizes.json 仅页 chrome)。改用手册 20-reference 模型清单
  落地: JimengGenPanel MODELS 首位新增「即梦 Seedance 2.5 样片模式」
  (手册实证条目；desc 未采样 CLONE_DECISION「样片模式，快速预览
  镜头效果」)。图片尺寸选项集维持单选项 stub (BLOCKED_BY_
  INTERACTION)。回归: 40/42/61 PASS；npm run check 通过。现场已
  还原 (1 次 undo)。
- Batch 532 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  首扫 90/91，唯一失败 batch 41 (模型清单断言未含批 531 新增的
  样片模式首位)；最小跟进 (want 列表加首项) 后单独 PASS，全量实质
  91/91，截图随扫刷新入库。
- Batch 533 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 534): 20-33 段回归续行。
- Batch 534 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 535): 34-48 段回归续行。
- Batch 535 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 536): 49-64 段回归续行。
- Batch 536 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 537): 65-101 段回归收尾。
- Batch 537 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (533 起 1-19、534 续 20-33、535 续 34-48、536 续 49-64、537 收尾
  65-101)。下一批规划 (Batch 538): 全量质量门确认扫 (距批 532 已
  积 4 批变更)。
- Batch 538 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 539):
  1-19 段新回归轮起点。
- Batch 539 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 540): 20-33 段回归续行。
- Batch 540 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 541): 34-48 段回归续行。
- Batch 541 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 542): 49-64 段回归续行。
- Batch 542 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 543): 65-101 段回归收尾。
- Batch 543 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (539 起 1-19、540 续 20-33、541 续 34-48、542 续 49-64、543 收尾
  65-101)。下一批规划 (Batch 544): 全量质量门确认扫 (距批 538 已
  积 5 批变更)。
- Batch 544 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 545):
  1-19 段新回归轮起点。
- Batch 545 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 546): 20-33 段回归续行。
- Batch 546 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 547): 34-48 段回归续行。
- Batch 547 (轮转回归): batch 34-48 段 15/15 PASS (续行；batch 34
  首跑遇 dev server 瞬时拒绝，复跑 PASS——负载抖动非契约回归)。
  下一批规划 (Batch 548): 49-64 段回归续行。
- Batch 548 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 549): 65-101 段回归收尾。
- Batch 530 (图片生成面板采样落地): CDP 源站采样空图片节点生成面板
- Batch 549 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (547 起 34-48 带 34 瞬时复跑、548 续 49-64、549 收尾 65-101；1-19/
  20-33 段于 533/534 已认证)。下一批规划 (Batch 550): 全量质量门
  确认扫 (距批 544 已积 5 批变更)。
  (530-image-panel.png / 530-image-panel.json)——680×208，占位「上传
  参考图、输入文字或主体，描述你想生成的图片」，左上 添加参考 48×48，
  选择器行 选择模型: Seedream 5.0 Lite (146) · 图片尺寸选项: 1:1 · 2K ·
  1 (98，比例/分辨率/数量合并) · 引用参考 24×24 · 引用参考 32×32，
  价格可见 ✦3 / 张 + 隐藏叶 Current price 3 / 张.，发送钮 生成。
  落地: 新组件 JimengImageGenPanel 按采样契约实现 (模型/尺寸下拉为
  单选项 stub——选项集未采样 CLONE_DECISION)；JimengImageNode 空态
  (无 poster) 选中改弹生成面板，带画面节点维持批 208 工具条。探坑:
  rail 双击致双节点插入 + 清理期 undo 复活致空视频节点一度丢失，
  连续 ⌘Z 16 次恢复基线 (BASE_IDS 核对)。回归: 34/35/105 PASS；
  npm run check 通过。
- Batch 550 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 551):
  1-19 段新回归轮起点。
- Batch 551 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 552): 20-33 段回归续行。
- Batch 552 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 553): 34-48 段回归续行。
- Batch 553 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 554): 49-64 段回归续行。
- Batch 554 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 555): 65-101 段回归收尾。
- Batch 555 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (551 起 1-19、552 续 20-33、553 续 34-48、554 续 49-64、555 收尾
  65-101)。下一批规划 (Batch 556): 全量质量门确认扫 (距批 550 已
  积 5 批变更)。
- Batch 556 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  首扫 89/91，唯一失败 batch 47/48 (连续执行负载抖动，无输出细节)，
  单独复跑双双 PASS——全量实质 91/91，截图随扫刷新入库 (与批 547
  batch 34 同型先例)。下一批规划 (Batch 557): 1-19 段新回归轮起点。
- Batch 557 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 558): 20-33 段回归续行。
- Batch 558 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 559): 34-48 段回归续行。
- Batch 559 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 560): 49-64 段回归续行。
- Batch 560 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 561): 65-101 段回归收尾。
- Batch 561 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (557 起 1-19、558 续 20-33、559 续 34-48、560 续 49-64、561 收尾
  65-101)。下一批规划 (Batch 562): 全量质量门确认扫 (距批 556 已
  积 5 批变更)。
- Batch 562 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 563):
  1-19 段新回归轮起点。
- Batch 563 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 564): 20-33 段回归续行。
- Batch 564 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 565): 34-48 段回归续行。
- Batch 565 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 566): 49-64 段回归续行。
- Batch 566 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 567): 65-101 段回归收尾。
- Batch 567 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (563 起 1-19、564 续 20-33、565 续 34-48、566 续 49-64、567 收尾
  65-101)。下一批规划 (Batch 568): 全量质量门确认扫 (距批 562 已
  积 5 批变更)。
- Batch 568 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 569):
  1-19 段新回归轮起点。
- Batch 569 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 570): 20-33 段回归续行。
- Batch 570 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 571): 34-48 段回归续行。
- Batch 571 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 572): 49-64 段回归续行。
- Batch 572 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 573): 65-101 段回归收尾。
- Batch 573 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (571 续 34-48、572 续 49-64、573 收尾 65-101；569/570 已认证
  1-19/20-33)。下一批规划 (Batch 574): 全量质量门确认扫 (距批 568
  已积 5 批变更)。
- Batch 574 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 575):
  1-19 段新回归轮起点。
- Batch 575 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 576): 20-33 段回归续行。
- Batch 576 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 577): 34-48 段回归续行。
- Batch 593 (演进轻扫，登录态+素材探索后复扫): 三面零漂移——视频
  工具条 670×40 六条目 (局部重拍/智能超清/视频编辑/截取帧/视频修剪/
  工具，与批 483/484 契约吻合)、右键菜单 192×324、音频面板 680×204
- Batch 594 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 595): 49-64 段回归续行。
- Batch 595 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 596): 65-101 段回归收尾。
- Batch 596 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (593 起 34-48、594 续 49-64、596 收尾 65-101；592 续 20-33，1-19
  段于 593 已认证)。下一批规划 (Batch 597): 全量质量门确认扫 (距批
  544 已积多批变更)。
  (SeedAudio 1.0 全引导文案 + Current price 12，与批 485 契约吻合)。
  无需改动 (593-evolution-scan.json)。现场已还原 (1 次 undo)。
  下一批规划 (Batch 594): 34-48 段回归续行。
- Batch 597 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 598):
  1-19 段新回归轮起点。
- Batch 598 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 599): 20-33 段回归续行。
- Batch 599 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 600): 34-48 段回归续行。
- Batch 600 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 601): 49-64 段回归续行。
- Batch 601 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 602): 65-101 段回归收尾。
- Batch 602 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (598 起 1-19、599 续 20-33、600 续 34-48、601 续 49-64、602 收尾
  65-101)。下一批规划 (Batch 603): 全量质量门确认扫 (距批 597 已
  积 5 批变更)。
- Batch 603 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 604):
  49-64 段回归续行。
- Batch 604 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 605): 65-101 段回归收尾。
- Batch 605 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (603 起 49-64、604 续、605 收尾 65-101；1-19/20-33/34-48 段于
  598-601 已认证)。下一批规划 (Batch 606): 全量质量门确认扫 (距批
  603 已积多批变更)。
- Batch 606 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  首扫 90/91，唯一失败 batch 29 (连续执行负载抖动)，单独复跑 PASS
  ——全量实质 91/91，截图随扫刷新入库 (与批 547/556 同型先例)。
  下一批规划 (Batch 607): 1-19 段新回归轮起点。
- Batch 607 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 608): 20-33 段回归续行。
- Batch 608 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 609): 34-48 段回归续行。
- Batch 609 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 610): 49-64 段回归续行。
- Batch 610 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 611): 65-101 段回归收尾。
- Batch 611 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (607 起 1-19、608 续 20-33、609 续 34-48、610 续 49-64、611 收尾
  65-101)。下一批规划 (Batch 612): 全量质量门确认扫 (距批 606 已
  积 5 批变更)。
- Batch 612 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 613):
  1-19 段新回归轮起点。
- Batch 613 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 614): 20-33 段回归续行。
- Batch 614 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 615): 34-48 段回归续行。
- Batch 615 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 616): 49-64 段回归续行。
- Batch 616 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 617): 65-101 段回归收尾。
- Batch 617 (轮转回归): batch 65-101 段 25/25 PASS (batch 76 首跑遇
  TargetClosedError 瞬时，复跑 PASS——dev server 抖动非契约回归)
  ——本回归轮闭合 (563 起 1-19、614 续 20-33、615 续 34-48、616 续
  49-64、617 收尾 65-101)。下一批规划 (Batch 618): 全量质量门确认
  扫 (距批 612 已积 5 批变更)。
- Batch 618 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 619):
  1-19 段新回归轮起点。
- Batch 619 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 620): 20-33 段回归续行。
- Batch 620 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 621): 34-48 段回归续行。
- Batch 621 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 622): 49-64 段回归续行。
- Batch 622 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 623): 65-101 段回归收尾 (距批 618 已积 4 批, 若段次
  收尾顺利则下一轮排全量质量门)。
- Batch 623 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  1-101 段次全绿)。下一批规划 (Batch 624): 全量质量门 91/91 复扫
  (距批 618 已积 5 批)。
- Batch 624 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。上一轮 619-623 段次回归 + 本门全绿收口。下一批
  规划 (Batch 625): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索作后续候选。
- Batch 625 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 626): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 626 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 627): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 627 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 628): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 628 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 629): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 629 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  625-629 段次全绿)。下一批规划 (Batch 630): 全量质量门 91/91
  复扫 (距批 624 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 630 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 625-629 段次回归 + 本门全绿收口。下一批
  规划 (Batch 631): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 631 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 632): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 632 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 633): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 633 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 634): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 634 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 635): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 635 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  631-635 段次全绿)。下一批规划 (Batch 636): 全量质量门 91/91
  复扫 (距批 630 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 636 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 631-635 段次回归 + 本门全绿收口。下一批
  规划 (Batch 637): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 637 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 638): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 638 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 639): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 639 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 640): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 640 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 641): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 641 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  637-641 段次全绿)。下一批规划 (Batch 642): 全量质量门 91/91
  复扫 (距批 636 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 642 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 637-641 段次回归 + 本门全绿收口。下一批
  规划 (Batch 643): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 643 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 644): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 644 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 645): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 645 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 646): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 646 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 647): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 647 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  643-647 段次全绿)。下一批规划 (Batch 648): 全量质量门 91/91
  复扫 (距批 642 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 648 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 643-647 段次回归 + 本门全绿收口。下一批
  规划 (Batch 649): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 649 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 650): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 650 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 651): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 651 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 652): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 652 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 653): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 653 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  649-653 段次全绿)。下一批规划 (Batch 654): 全量质量门 91/91
  复扫 (距批 648 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 654 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 649-653 段次回归 + 本门全绿收口。下一批
  规划 (Batch 655): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 655 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 656): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 656 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 657): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 657 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 658): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 658 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 659): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 659 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  655-659 段次全绿)。下一批规划 (Batch 660): 全量质量门 91/91
  复扫 (距批 654 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 660 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 655-659 段次回归 + 本门全绿收口。下一批
  规划 (Batch 661): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 661 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 662): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 662 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 663): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 663 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 664): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 664 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 665): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 665 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  661-665 段次全绿)。下一批规划 (Batch 666): 全量质量门 91/91
  复扫 (距批 660 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 666 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 661-665 段次回归 + 本门全绿收口。下一批
  规划 (Batch 667): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 667 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 668): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 668 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 669): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 669 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 670): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 670 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 671): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 671 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  667-671 段次全绿)。下一批规划 (Batch 672): 全量质量门 91/91
  复扫 (距批 666 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 672 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 667-671 段次回归 + 本门全绿收口。下一批
  规划 (Batch 673): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 673 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 674): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 674 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 675): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 675 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 676): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 676 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 677): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 677 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  673-677 段次全绿)。下一批规划 (Batch 678): 全量质量门 91/91
  复扫 (距批 672 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 678 (全量质量门): 91/91 PASS 零失败复扫 (后台单循环,
  无瞬时失败)。本轮 673-677 段次回归 + 本门全绿收口。下一批
  规划 (Batch 679): 新回归轮 1-19 段起点; 素材账本剩余项
  (S109·镜2.mp4 / separated_vocals wav / 8 图) 上传探索视进度插入。
- Batch 679 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 680): 20-33 段回归续行; 素材账本剩余项
  上传探索视段次进度插入。
- Batch 680 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 681): 34-48 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 681 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 682): 49-64 段回归续行; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 682 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 683): 65-101 段回归收尾; 素材账本剩余项上传探索
  视段次进度插入。
- Batch 683 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  679-683 段次全绿)。下一批规划 (Batch 684): 全量质量门 91/91
  复扫 (距批 678 已积 5 批); 素材账本剩余项上传探索视进度插入。
- Batch 684 (全量质量门): 91/91 PASS 零失败 (后台单循环; 暂停
  期间子进程未被杀死继续跑完, SUMMARY 见 /tmp/jimeng-gate-batch684.log,
  此处补记)。本轮 679-683 段次回归 + 本门全绿收口。下一批规划
  (Batch 685): 素材账本剩余项上传探索优先 (S109·镜2.mp4 /
  separated_vocals wav / 8 图; 浏览器若未登录先弹窗请用户登录)。
- Batch 685 (源站上传探索): S109·镜2.mp4 上传采样完成。上传钮
  (aria=上传) + file chooser → 建 node_368n1s9n4r (标题=文件名
  去扩展名, 处理秒级 ready, 自动选中)。选中工具条实测六条目
  (局部重拍/智能超清/视频编辑/截取帧/视频修剪 + 工具下拉) 与
  视频播放控件 (Pause/Unmute/浏览器全屏) 并存, 零漂移。工具下拉
  首次实测采到: 编辑组=补帧/深度动作捕捉, 预设组=提示词反推,
  与 Batch 527 落地完全一致 (此前 BLOCKED_BY_INTERACTION 悬案
  转实测确认)。新导航事实: 选中节点 Delete 键无效, Backspace
  才删除。探索后已删节点恢复 2 节点基线并已保存。截图 4 张
  (early/toolbar/toolmenu/restored-2026-09-25) 入
  docs/design-references/jimeng/。下一批规划 (Batch 686):
  素材账本续行——8 张图片经空节点 上传参考图 通路采样,
  separated_vocals wav 视音频面板真实手势条件再试。
- Batch 686 (源站上传探索): 空视频节点面板实测源真相——视频
  尺寸选项 16:9·720P·1 (Standard-only model)、生成模式「全能
  参考」、时长 4s、引用参考、生成 (clone 空视频节点面板漂移
  核对项)。面板 file input 直传 3 图未生成参考缩略, 而是各建
  独立图片节点 (标题=文件名去扩展名)——「引用参考」应为另路
  (从既有节点/资产库选取), 待后续采样。多选工具条新证据:
  智能超清/抠图/编组/布局/下载/Create connected node after
  selected nodes。左栏「音频」钮直接建空音频节点; 选中面板契约
  与实现一致 (SeedAudio 1.0 New/全能配音/音色库/12·24 折扣签/
  添加参考/引用参考)。「添加参考」真实鼠标点击仍不开 chooser
  ——BLOCKED_BY_INTERACTION 对 CDP 事件成立; 共享 file input
  直传 wav 建独立音频节点 (时长徽章 00:00:13), 音频上传链路
  采样完成。删除语义细化: 节点 mouse 点击选中后 Backspace 生效,
  焦点漂移时 Backspace 空操作。4 素材账本标记已探索, 探索后
  恢复 2 节点基线并已保存。截图 12 张入
  docs/design-references/jimeng/。下一批规划 (Batch 687):
  空视频节点面板漂移核对——对照 clone 现行面板补齐 16:9·720P/
  全能参考/4s 契约; 引用参考按钮通路再试。
- Batch 687 (漂移核对 + 引用参考再试): 漂移核对结论=零漂移——
  Batch 686 源站实测 aria 标签与 clone JimengGenPanel 逐字一致
  (视频尺寸选项: 16:9 · 720P · 1, Standard-only model / 生成模式:
  全能参考 / 选择视频生成时长: 4s / 引用参考 / 生成), 批 42/403
  SOURCE_FACT 对 2026-09-26 线上源站仍现行。引用参考通路破解:
  点击不开模态, 而是切换行内参考条——展开 主体/图片/视频/音频
  四类别标签 + 添加参考钮 + 展开视频生成器入口 (批 403 的单
  图标钮系简化建模, 展开条为新增复刻项); 标签内容因画布无图片
  节点而空, 深采存疑。截图 4 张 (ref-strip-tabs / ref-tab-img /
  ref-collapsed / baseline-clean-2026-09-26) 入
  docs/design-references/jimeng/。探针误建的空音频节点已删,
  恢复 2 节点基线并已保存。下一批规划 (Batch 688): 复刻引用
  参考展开条——JimengGenPanel 增 主体/图片/视频/音频 标签 +
  添加参考图标钮 (SOURCE_FACT), 配套验证器断言。
- Batch 688 (复刻实施): 引用参考展开条落地 JimengGenPanel——
  引用参考钮加 aria-pressed + 激活态, 点击切换素材栏行原位替换
  为参考条 (添加参考图标钮 + 主体/图片/视频/音频标签
  aria-pressed 切换 + 搜索框 placeholder「搜索主体、图片、
  视频」), 再点收合还原上传参考图钮; CLONE_DECISION: 源站为整
  面板长高展开 (布局部分遮挡未采全), clone 采用行内原位替换
  零位移方案; 标签默认态主体 (源站默认态未采全)。验证器
  verify-jimeng-batch688.py (展开/标签切换/收合断言, 收起 AI
  抽屉防遮挡) PASS; typecheck 零错; 邻域回归 batch 3/40/41/42/61
  全 PASS。下一批规划 (Batch 689): 轮转回归 1-19 段起点
  (新回归轮)。
- Batch 689 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 690): 20-33 段回归续行。
- Batch 690 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 691): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 691 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 692): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 692 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 693): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 693 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  689-693 段次全绿)。下一批规划 (Batch 694): 全量质量门 92 项
  复扫 (批 688 新增验证器后总量 91→92; 距批 684 已积 5 批 +
  引用参考展开条新面)。
- Batch 694 (全量质量门): 92 项全绿收口——首扫 76/92, 16 项
  集中于扫描后半程 goto 超时 (92 连发 dev server 过载, 含新
  batch 688); 空闲后逐项复跑 16/16 PASS, 判定瞬时失败非真实
  回归 (先例同批 34/47/48/29/76)。92 项含批 688 引用参考展开条
  契约。下一批规划 (Batch 695): 新回归轮 1-19 段起点; 素材
  账本剩余 6 图上传探索视进度插入。
- Batch 695 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 696): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 696 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 697): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 697 (轮转回归): batch 34-48 段 15/15 PASS (续行; 34/35
  首扫 goto 超时为瞬时过载, 复跑即过——先例同批 694)。下一批
  规划 (Batch 698): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 698 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 699): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 699 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  695-699 段次全绿)。下一批规划 (Batch 700): 全量质量门 92 项
  复扫 (距批 694 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 700 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  无瞬时失败; 上一门 694 的过载复跑经验印证, 本次全程稳态)。
  本轮 695-699 段次回归 + 本门全绿收口。下一批规划 (Batch 701):
  新回归轮 1-19 段起点; 素材账本剩余 6 图上传探索视进度插入。
- Batch 701 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 702): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 702 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 703): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 703 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 704): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 704 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 705): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 705 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  701-705 段次全绿)。下一批规划 (Batch 706): 全量质量门 92 项
  复扫 (距批 700 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 706 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 701-705 段次回归 + 本门全绿收口。下一批
  规划 (Batch 707): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 707 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 708): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 708 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 709): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 709 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 710): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 710 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 711): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 711 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  707-711 段次全绿)。下一批规划 (Batch 712): 全量质量门 92 项
  复扫 (距批 706 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 712 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 707-711 段次回归 + 本门全绿收口。下一批
  规划 (Batch 713): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 713 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 714): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 714 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 715): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 715 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 716): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 716 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 717): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 717 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  713-717 段次全绿)。下一批规划 (Batch 718): 全量质量门 92 项
  复扫 (距批 712 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 718 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 713-717 段次回归 + 本门全绿收口。下一批
  规划 (Batch 719): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 719 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 720): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 720 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 721): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 721 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 722): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 722 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 723): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 723 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  719-723 段次全绿)。下一批规划 (Batch 724): 全量质量门 92 项
  复扫 (距批 718 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 724 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 719-723 段次回归 + 本门全绿收口。下一批
  规划 (Batch 725): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 725 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 726): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 726 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 727): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 727 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 728): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 728 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 729): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 729 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  725-729 段次全绿)。下一批规划 (Batch 730): 全量质量门 92 项
  复扫 (距批 724 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 730 (全量质量门): 92 项全绿收口——首扫 91/92, batch 49
  单项 goto 超时为瞬时过载, 空闲后复跑 PASS (先例同批
  34/47/48/29/76/694/697)。本轮 725-729 段次回归 + 本门全绿
  收口。下一批规划 (Batch 731): 新回归轮 1-19 段起点; 素材
  账本剩余 6 图上传探索视进度插入。
- Batch 731 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 732): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 732 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 733): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 733 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 734): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 734 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 735): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 735 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  731-735 段次全绿)。下一批规划 (Batch 736): 全量质量门 92 项
  复扫 (距批 730 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 736 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 731-735 段次回归 + 本门全绿收口。下一批
  规划 (Batch 737): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 737 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 738): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 738 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 739): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 739 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 740): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 740 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 741): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 741 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  737-741 段次全绿)。下一批规划 (Batch 742): 全量质量门 92 项
  复扫 (距批 736 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 742 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 737-741 段次回归 + 本门全绿收口。下一批
  规划 (Batch 743): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 743 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 744): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 744 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 745): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 745 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 746): 49-64 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 746 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 747): 65-101 段回归收尾; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 747 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  743-747 段次全绿)。下一批规划 (Batch 748): 全量质量门 92 项
  复扫 (距批 742 已积 5 批); 素材账本剩余 6 图上传探索视进度
  插入。
- Batch 748 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 743-747 段次回归 + 本门全绿收口。下一批
  规划 (Batch 749): 新回归轮 1-19 段起点; 素材账本剩余 6 图
  上传探索视进度插入。
- Batch 749 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 750): 20-33 段回归续行; 素材账本剩余 6 图
  上传探索视段次进度插入。
- Batch 750 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 751): 34-48 段回归续行; 素材账本剩余 6 图上传
  探索视段次进度插入。
- Batch 751 (轮转回归): batch 34-48 段 15/15 PASS (续行; 上轮
  启动即中止无结果, 本轮重跑全绿)。下一批规划 (Batch 752):
  49-64 段回归续行; 素材账本剩余 9 项 (7 图 + voice_converted
  wav + S83 复采) 上传探索视进度插入。
- Batch 752 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 753): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视进度插入。
- Batch 753 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  751-753 段次全绿)。下一批规划 (Batch 754): 全量质量门 92 项
  复扫 (距批 748 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 754 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 751-753 段次回归 + 本门全绿收口。下一批
  规划 (Batch 755): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 755 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 756): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 756 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 757): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 757 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 758): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 758 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 759): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 759 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  755-759 段次全绿)。下一批规划 (Batch 760): 全量质量门 92 项
  复扫 (距批 754 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 760 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 755-759 段次回归 + 本门全绿收口。下一批
  规划 (Batch 761): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 761 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 762): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 762 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 763): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 763 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 764): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 764 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 765): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 765 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  761-765 段次全绿)。下一批规划 (Batch 766): 全量质量门 92 项
  复扫 (距批 760 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 766 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 761-765 段次回归 + 本门全绿收口。下一批
  规划 (Batch 767): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 767 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 768): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 768 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 769): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 769 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 770): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 770 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 771): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 771 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  767-771 段次全绿)。下一批规划 (Batch 772): 全量质量门 92 项
  复扫 (距批 766 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 772 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 767-771 段次回归 + 本门全绿收口。下一批
  规划 (Batch 773): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 773 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 774): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 774 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 775): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 775 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 776): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 776 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 777): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 777 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  773-777 段次全绿)。下一批规划 (Batch 778): 全量质量门 92 项
  复扫 (距批 772 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 778 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 773-777 段次回归 + 本门全绿收口。下一批
  规划 (Batch 779): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 779 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 780): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 780 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 781): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 781 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 782): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 782 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 783): 65-101 段回归收尾; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 783 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  779-783 段次全绿)。下一批规划 (Batch 784): 全量质量门 92 项
  复扫 (距批 778 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 784 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态)。本轮 779-783 段次回归 + 本门全绿收口。下一批
  规划 (Batch 785): 新回归轮 1-19 段起点; 素材账本剩余 9 项
  (7 图 + voice_converted wav + S83 复采) 上传探索视进度插入。
- Batch 785 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点,
  dev server 4317 重启后全稳态)。下一批规划 (Batch 786): 20-33
  段回归续行; 素材账本剩余 9 项上传探索视段次进度插入。
- Batch 786 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 787): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 787 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 788): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 788 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, git 全历史确认, 非失败)。下一批规划
  (Batch 789): 65-101 段回归收尾; 素材账本剩余 9 项上传探索
  视段次进度插入。
- Batch 789 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  785-789 段次全绿)。下一批规划 (Batch 790): 全量质量门 92 项
  复扫 (距批 784 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 790 (全量质量门): 92/92 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 785-789 段次回归 + 本门全绿收口。
  下一批规划 (Batch 791): 视浏览器/登录态做源站「引用参考」展开
  条四标签内容深采 (若不可用则回落新回归轮 1-19 段起点); 素材
  账本剩余 9 项上传探索视进度插入。
- Batch 791 (源站深采·引用参考全链路): 重大证据修正——「引用
  参考」实为 @ 自动补全弹层, 非行内标签条。(1) 环境异常: 源画布
  空视频节点 node_eftc9q6caa 在探查间隙被外部因素删除 (本批仅发
  单次左键; 画布 Room connected 协同态, 疑并行会话/远端变更),
  已用工具栏「视频」重建 node_jh6m2rmdwq 作基线第二节点。
  (2) SOURCE_FACT (2026-09-27): 点面板 chips 行 引用参考 32×32 →
  提示框 contenteditable 插入 "@" 字符 + 弹「可能@的内容」弹层:
  候选区 (画布节点行 32px 缩略图+名称) + 「添加参考」分区 (主体/
  图片/视频/音频 四行, 前置图标+右箭头下钻; 批 687 所见「四类别
  标签」实为此弹层行)。类别下钻子菜单: 48px 行 (32px 缩略图 +
  名称, 视频行加 00:06 时长徽章); 空类别弹「暂无相关节点」空态
  卡; 视频子菜单含 展开视频生成器 40×40 钮 (aria 实测)。点子
  菜单行 → 插入引用 chip (node-composerChip, draggable): 48×48
  缩略图+名称, 右上 24×24 Remove 角标, aria「Reference material:
  {名称}」(视频加 ", duration 6s"), 多 chip 横向堆叠; 上传中灰块
  +价格区「正在上传参考图片…」, 完成 "Reference image ready"。
  提示框 placeholder「@搜索主体、图片、视频」, 空内容显「使用」
  示例卡 (@图片1 模仿 @视频1 的动作, 音色参考 @音频1)。chip 行
  添加参考 48×48 → 三选项菜单: 上传参考内容 / 从资产库添加 /
  从画布选择; 从画布选择 → 点选模式 (整画布蓝色描边 + 顶部蓝
  pill「◎ 从画布选择 ×」, 点节点后变「◎ 添加完成」+插 chip)。
  (3) 漂移: 批 688 clone 行内标签条方案与源态结构不同 (原
  CLONE_DECISION 已声明), 本批确认真态留档为对齐候选。(4) 恢复:
  chip 移除/提示清空/上传图片节点删除, 画布 2 节点已保存 (第二
  节点 id 变为 node_jh6m2rmdwq)。截图 11 张 source-{ref-strip-
  open,ref-menu-subject,ref-menu-image,ref-picked,ref-chip-
  uploaded,addref-3menu,addref-fromcanvas,addref-picked-canvas,
  ref-menu-video,ref-menu-audio,ref-menu-reopen}-2026-09-27 入
  docs/design-references/jimeng/。下一批规划 (Batch 792): 复刻
  对齐——JimengGenPanel 引用参考重构为 @ 自动补全弹层 (可能@的
  内容 + 四类别下钻 + chip 行 + 添加参考三选项 + 从画布点选),
  配套验证器; 素材账本剩余 9 项视进度插入。
- Batch 792 (复刻实施): JimengGenPanel 引用参考重构为 @ 自动补全
  弹层, 对齐批 791 SOURCE_FACT——引用参考钮点击 = 提示框插入
  "@" + 开「可能@的内容」弹层 (data-testid=ref-menu: 候选区画布
  媒体节点行 + 添加参考分区 主体/图片/视频/音频 四行 aria-pressed
  + 右箭头); 类别行点击下钻 ref-submenu (48px 行 + 32px 缩略图,
  视频行 mm:ss 时长徽章 00:06, 空类别「暂无相关节点」; 视频子
  菜单含 展开视频生成器 钮); 点行插入引用 chip (素材栏行变
  ref-chip-row: 44×44 缩略图块 + Remove 16×16 角标 aria
  「Reference material: {名称}」, 多 chip 堆叠 + 添加参考钮),
  chip poster 缺省用类型图标 (CLONE_DECISION: clone 节点缩略图
  不全); 插入后剥离提示框尾部 "@" 并收弹层; 批 688 行内条实现
  移除 (搜索框一并撤销——791 证实该「搜索框」实为提示框
  placeholder 的误读)。留待后续批: 添加参考三选项菜单 (上传参考
  内容/从资产库添加/从画布选择) + 从画布点选模式。验证器:
  verify-jimeng-batch688.py 重写对齐弹层契约 (原行内条断言被
  791 真态替代); 新增 verify-jimeng-batch792.py (rail 上传建节点
  → 弹层候选/视频下钻徽章/图片空态/插 chip/剥 @/Remove 还原);
  邻域回归 3/40/41/42/61 全绿 + npm run check 通过。截图
  jimeng-clone-batch688-ref-strip-1680 (刷新) +
  batch792-ref-submenu/ref-chip-1680。下一批规划 (Batch 793):
  添加参考 48×48 三选项菜单 (上传参考内容/从资产库添加/从画布
  选择) + 从画布点选模式复刻 (蓝色描边 + 顶部 pill), 配套验证
  器; 素材账本剩余 9 项视进度插入。
- Batch 793 (复刻实施): 添加参考三选项菜单 + 从画布点选模式
  落地, 对齐批 791 SOURCE_FACT——(1) chip 行 添加参考钮加
  aria-pressed, 点击弹三选项菜单 (data-testid=addref-menu, 232px:
  上传参考内容 SquarePen / 从资产库添加 LayoutGrid / 从画布选择
  Scan, 38px 行)。(2) 上传参考内容 → 面板内隐藏文件入口
  (data-testid=panel-upload-input, 复用 addLocalUpload 画布中心
  落点, 同左栏上传链路)。(3) 从资产库添加 → setAssetsOpen 打开
  批 72 资产库模态。(4) 从画布选择 → store 新增 refPicking/
  pickedRefNodeId + start/cancel/pick/clear 四动作; JimengWorkspace
  订阅 refPicking: 画布容器加 ring-2 ring-inset ring-[#0A5CD6]
  蓝色内描边 + 顶部蓝 pill 横幅 (data-testid=canvas-pick-banner,
  Scan 图标 + 从画布选择 + 取消从画布选择 ×), onNodeClick 拦截
  点选 (pickRefNode 后面板插 chip + pushToast「添加完成」
  CLONE_DECISION: 源站为 pill 文案切换, clone 用 toast), Escape
  分支追加 cancelRefPicking。验证器 verify-jimeng-batch793.py:
  三选项齐备/资产库开合/面板上传建节点/横幅+描边/横幅取消/
  点选插 chip; 教训留档: 验证器不可用 Escape 关模态 (会反选节点
  卸载生成面板), 须用模态自带关闭钮; 上传步骤后菜单仍开, 再点
  添加参考是关闭非打开。邻域回归 3/40/42/61/73/688/792 全绿 +
  npm run check 通过。截图 batch793-{addref-menu,canvas-picking,
  picked-chip}-1680。下一批规划 (Batch 794): 新回归轮 1-19 段
  起点 (距批 790 全量门已积 791-793 三批实现/深采); 素材账本
  剩余 9 项 (7 图 + voice_converted wav + S83 复采) 上传探索
  视进度插入。
- Batch 794 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点,
  本地 master 与远端同步 2627c20f, 含并行 batch 539 后全稳态)。
  下一批规划 (Batch 795): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 795 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 796): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 796 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 797): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 797 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 798):
  65-101 段回归收尾; 素材账本剩余 9 项上传探索视段次进度插入。
- Batch 798 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  794-798 段次全绿, 含 791-793 三批实现后首整轮)。下一批规划
  (Batch 799): 全量质量门 92 项复扫 (距批 790 已积 5 批); 素材
  账本剩余 9 项上传探索视进度插入。
- Batch 799 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态; 总门数 92→94——batch792/793 两个新验证器并入门集,
  另含并行 batch 539 落地后的全量确认)。本轮 794-798 段次回归 +
  本门全绿收口。下一批规划 (Batch 800): 新回归轮 1-19 段起点;
  素材账本剩余 9 项 (7 图 + voice_converted wav + S83 复采)
  上传探索视进度插入。
- Batch 800 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 801): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 801 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 802): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 802 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 803): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 803 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 804):
  65-101 段回归收尾; 素材账本剩余 9 项上传探索视段次进度插入。
- Batch 804 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  800-804 段次全绿)。下一批规划 (Batch 805): 全量质量门 94 项
  复扫 (距批 799 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 805 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 800-804 段次回归 + 本门全绿收口。
  下一批规划 (Batch 806): 新回归轮 1-19 段起点; 素材账本剩余
  9 项 (7 图 + voice_converted wav + S83 复采) 上传探索视进度
  插入。
- Batch 806 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 807): 20-33 段回归续行; 素材账本剩余 9 项
  上传探索视段次进度插入。
- Batch 807 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 808): 34-48 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 808 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 809): 49-64 段回归续行; 素材账本剩余 9 项上传
  探索视段次进度插入。
- Batch 809 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 810):
  65-101 段回归收尾; 素材账本剩余 9 项上传探索视段次进度插入。
- Batch 810 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  806-810 段次全绿)。下一批规划 (Batch 811): 全量质量门 94 项
  复扫 (距批 805 已积 5 批); 素材账本剩余 9 项上传探索视进度
  插入。
- Batch 811 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 806-810 段次回归 + 本门全绿收口。
  下一批规划 (Batch 812): 视源站浏览器/登录态做素材账本剩余项
  上传探索 (voice_converted wav 优先, S83 复采次之; 若不可用
  则回落新回归轮 1-19 段起点)。
- Batch 812 (源站探索·音频上传链路): 上传 voice_converted wav
  成功 (node_yc89v5a6vt, 标题缩略 voice_...519790)。(1) SOURCE_FACT
  (2026-09-27): 上传音频节点为方形卡 121×121@38%——卡内全宽白
  波形 (选中态加蓝色播放头竖线) + 标题行「» voice_...519790」+
  tag 图标 + 左下时长徽章 00:00:12; 选中悬浮工具条仅两项:
  音频修剪 (波形图标) | 分隔线 | 下载 (aria 另见 Rename/Add
  tags/Play/Create connected node, 系节点内控件)。(2) 音频修剪
  面板 = 底部悬浮裁剪条 (非模态): 全宽白描边圆角波形条 + 左右
  拖拽手柄 + 条内右侧精确时长 12.04s; 下行左 ▶ + 「00:00 /
  00:12」(aria Play selected range) + 右白色 pill 确认钮 (未点
  击, 避免改动素材)。(3) 教训: 工具条钮必须以实时 DOM 坐标点击
  (固定坐标在工具条重渲染后落空, 会造成空白反选)。(4) 恢复:
  Escape 退出修剪 → 删 wav 节点 → 2 节点基线已保存。账本
  voice_converted 标记已探索。截图 source-wav-voiceconverted-
  {uploaded,selected}-2026-09-27 + source-audio-trim-panel-
  2026-09-27 入 docs/design-references/jimeng/。下一批规划
  (Batch 813): 新回归轮 1-19 段起点; 账本剩余 8 项 (7 图 +
  S83 复采) 视进度插入。
- Batch 813 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 814): 20-33 段回归续行; 账本剩余 8 项视
  段次进度插入。
- Batch 814 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 815): 34-48 段回归续行; 账本剩余 8 项视段次进度
  插入。
- Batch 815 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 816): 49-64 段回归续行; 账本剩余 8 项视段次进度
  插入。
- Batch 816 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 817):
  65-101 段回归收尾; 账本剩余 8 项视段次进度插入。
- Batch 817 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  813-817 段次全绿)。下一批规划 (Batch 818): 全量质量门 94 项
  复扫 (距批 811 已积 5 批); 账本剩余 8 项 (7 图 + S83 复采)
  视进度插入。
- Batch 818 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 813-817 段次回归 + 本门全绿收口。
  下一批规划 (Batch 819): 视源站浏览器态做 S83·镜2.mp4 复采
  (账本最后一项视频; 若不可用则回落新回归轮 1-19 段起点);
  剩余 7 图视进度插入。
- Batch 819 (源站探索·S83 复采): 上传 S83·镜2.mp4 成功
  (node_79gfv08nvx)。(1) SOURCE_FACT (2026-09-27): 上传视频节点
  选中工具条全量采样——「局部重拍 ✦ · 智能超清 ✦ · 视频编辑 ✦ ·
  截取帧 ∨ · 视频修剪 · 工具 ∨ │ 全屏 · 下载」(前三维 Items 带
  ✦ 付费徽章; 截取帧/工具带下拉箭头; aria 另含 Rename/Pause/
  Unmute video/Enter browser full screen/Create connected node)。
  与批 685 相比顶层条目直接展开 (工具下拉内容 归入 工具∨),
  新增 局部重拍/视频编辑 顶层项——批 62 截取帧 与批 685 智能
  超清 条目均在位。(2) 节点本体: 标题行「▣ S83·镜2」+ tag 图标,
  16:9 预览 + 左下进度 00:00/00:04 + 右下音量/全屏钮 (时长 4s)。
  (3) 恢复: Backspace 删除 → 2 节点基线已保存。账本 S83 标记
  已复采 (视频类账本清零, 剩 7 图)。截图 source-s83-{uploaded,
  selected}-2026-09-27 入 docs/design-references/jimeng/。下一批
  规划 (Batch 820): 新回归轮 1-19 段起点; 剩余 7 图视进度插入。
- Batch 820 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 821): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 821 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 822): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 822 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 823): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 823 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 824):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 824 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  820-824 段次全绿; 期间并行 frameos batch 257 落地, 推送时
  远端已被并行会话同步至同提交)。下一批规划 (Batch 825): 全量
  质量门 94 项复扫 (距批 818 已积 5 批); 剩余 7 图视进度插入。
- Batch 825 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 820-824 段次回归 + 本门全绿收口。
  下一批规划 (Batch 826): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 826 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 827): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 827 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 828): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 828 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 829): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 829 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 830):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 830 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  826-830 段次全绿)。下一批规划 (Batch 831): 全量质量门 94 项
  复扫 (距批 825 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 831 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 826-830 段次回归 + 本门全绿收口。
  下一批规划 (Batch 832): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 832 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 833): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 833 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 834): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 834 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 835): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 835 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 836):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 836 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  832-836 段次全绿)。下一批规划 (Batch 837): 全量质量门 94 项
  复扫 (距批 831 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 837 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 832-836 段次回归 + 本门全绿收口。
  下一批规划 (Batch 838): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 838 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 839): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 839 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 840): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 840 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 841): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 841 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 842):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 842 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  838-842 段次全绿)。下一批规划 (Batch 843): 全量质量门 94 项
  复扫 (距批 837 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 843 (全量质量门): 94/94 有效 PASS——直跑 93/94, batch67
  TargetClosedError 瞬时失败 (浏览器被提前关闭, 非断言问题),
  单独复跑即 PASS (先例同批 47/48/694 门瞬时复跑协议)。本轮
  838-842 段次回归 + 本门全绿收口。下一批规划 (Batch 844): 新
  回归轮 1-19 段起点; 剩余 7 图上传探索视进度插入。
- Batch 844 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 845): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 845 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 846): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 846 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 847): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 847 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 848):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 848 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  844-848 段次全绿; 跑动中途会话中断一次, batch65 中断前已
  PASS, 续跑其余 24/24)。下一批规划 (Batch 849): 全量质量门
  94 项复扫 (距批 843 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 849 (全量质量门): 94/94 有效 PASS——直跑 90/94, batch
  30-33 四项瞬时失败 (94 连发期间 Next.js dev overlay
  nextjs-portal 遮挡指针, 非断言问题), 单独复跑 4/4 即 PASS
  (先例同批 47/48/694/843 门瞬时复跑协议)。本轮 844-848 段次
  回归 + 本门全绿收口。下一批规划 (Batch 850): 新回归轮 1-19
  段起点; 剩余 7 图上传探索视进度插入。
- Batch 850 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 851): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 851 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 852): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 852 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 853): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 853 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 854):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 854 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  850-854 段次全绿)。下一批规划 (Batch 855): 全量质量门 94 项
  复扫 (距批 849 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 855 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 850-854 段次回归 + 本门全绿收口。
  下一批规划 (Batch 856): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 856 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 857): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 857 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 858): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 858 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 859): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 859 (轮转回归): batch 49-64 段 14/14 有效 PASS——直跑
  11/14, batch57 TargetClosedError (浏览器被关) + batch63/64
  ERR_CONNECTION_REFUSED (dev server 4317 跑动中掉线, 已重启
  恢复 200), 三项单独复跑 3/3 即 PASS (瞬时复跑协议先例 + 1)。
  下一批规划 (Batch 860): 65-101 段回归收尾; 剩余 7 图视段次
  进度插入。
- Batch 860 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  856-860 段次全绿)。下一批规划 (Batch 861): 全量质量门 94 项
  复扫 (距批 855 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 861 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败; 门前三连探测 dev server 200 稳定)。
  本轮 856-860 段次回归 + 本门全绿收口。下一批规划 (Batch
  862): 新回归轮 1-19 段起点; 剩余 7 图上传探索视进度插入。
- Batch 862 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 863): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 863 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 864): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 864 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 865): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 865 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 866):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 866 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  862-866 段次全绿)。下一批规划 (Batch 867): 全量质量门 94 项
  复扫 (距批 861 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 867 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 862-866 段次回归 + 本门全绿收口。
  下一批规划 (Batch 868): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 868 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 869): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 869 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 870): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 870 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 871): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 871 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 872):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 872 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  868-872 段次全绿)。下一批规划 (Batch 873): 全量质量门 94 项
  复扫 (距批 867 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 873 (全量质量门): 94/94 有效 PASS——直跑 82/94, batch
  57-70 连续 12 项瞬时失败 (跑动中段约 90 秒环境事件窗口, 疑
  dev server 抖动; batch71 起自动恢复全绿), 12 项单独复跑 12/12
  即 PASS (瞬时复跑协议先例 + 2)。本轮 868-872 段次回归 + 本门
  全绿收口。下一批规划 (Batch 874): 新回归轮 1-19 段起点; 剩余
  7 图上传探索视进度插入。
- Batch 874 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 875): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 875 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 876): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 876 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 877): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 877 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 878):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 878 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  874-878 段次全绿)。下一批规划 (Batch 879): 全量质量门 94 项
  复扫 (距批 873 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 879 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 874-878 段次回归 + 本门全绿收口。
  下一批规划 (Batch 880): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 880 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 881): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 881 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 882): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 882 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 883): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 883 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 884):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 884 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  880-884 段次全绿)。下一批规划 (Batch 885): 全量质量门 94 项
  复扫 (距批 849 之后的 855 门已过 5 批 856-860, 复扫继续按
  节奏推进); 剩余 7 图上传探索视进度插入。
- Batch 885 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 880-884 段次回归 + 本门全绿收口。
  下一批规划 (Batch 886): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 886 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 887): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 887 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 888): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 888 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 889): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 889 (轮转回归): batch 49-64 段 14/14 有效 PASS——直跑
  11/14, batch 49/50/51 Locator.click 超时瞬时失败 (burst 期间
  环境抖动, 非断言问题), 三项单独复跑 3/3 即 PASS (瞬时复跑
  协议先例 + 3)。下一批规划 (Batch 890): 65-101 段回归收尾;
  剩余 7 图视段次进度插入。
- Batch 890 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  886-890 段次全绿)。下一批规划 (Batch 891): 全量质量门 94 项
  复扫 (距批 885 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 891 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败; 门前三连探测 dev server 200 稳定)。
  本轮 886-890 段次回归 + 本门全绿收口。下一批规划 (Batch
  892): 新回归轮 1-19 段起点; 剩余 7 图上传探索视进度插入。
- Batch 892 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 893): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 893 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 894): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 894 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 895): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 895 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 896):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 896 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  892-896 段次全绿)。下一批规划 (Batch 897): 全量质量门 94 项
  复扫 (距批 891 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 897 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 892-896 段次回归 + 本门全绿收口。
  下一批规划 (Batch 898): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 898 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 899): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 899 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 900): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 900 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 901): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 901 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 902):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 902 (轮转回归): batch 65-101 段 25/25 有效 PASS——直跑
  23/25, batch 100/101 Page.evaluate TypeError (页面状态抖动致
  节点未定位, 非断言问题), 两项单独复跑 2/2 即 PASS (瞬时复跑
  协议先例 + 4)。本轮 898-902 段次回归全绿闭合。下一批规划
  (Batch 903): 全量质量门 94 项复扫 (距批 897 已积 5 批); 剩余
  7 图上传探索视进度插入。
- Batch 903 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 898-902 段次回归 + 本门全绿收口。
  下一批规划 (Batch 904): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 904 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 905): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 905 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 906): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 906 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 907): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 907 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 908):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 908 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  904-908 段次全绿)。下一批规划 (Batch 909): 全量质量门 94 项
  复扫 (距批 903 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 909 (全量质量门): 94/94 有效 PASS——直跑 93/94, batch65
  瞬时失败 (非断言问题), 单独复跑即 PASS (瞬时复跑协议先例
  + 5)。本轮 904-908 段次回归 + 本门全绿收口。下一批规划
  (Batch 910): 新回归轮 1-19 段起点; 剩余 7 图上传探索视进度
  插入。
- Batch 910 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点;
  跑动中途会话中断一次, batch 1-7 中断前已 PASS, 续跑 8-19
  12/12)。下一批规划 (Batch 911): 20-33 段回归续行; 剩余 7 图
  视段次进度插入。
- Batch 911 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 912): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 912 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 913): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 913 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 914):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 914 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  910-914 段次全绿)。下一批规划 (Batch 915): 全量质量门 94 项
  复扫 (距批 891 已积两轮, 按节奏推进); 剩余 7 图上传探索视
  进度插入。
- Batch 915 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 910-914 段次回归 + 本门全绿收口。
  下一批规划 (Batch 916): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 916 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 917): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 917 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 918): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 918 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 919): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 919 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 920):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 920 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  916-920 段次全绿)。下一批规划 (Batch 921): 全量质量门 94 项
  复扫 (距批 915 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 921 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 916-920 段次回归 + 本门全绿收口。
  下一批规划 (Batch 922): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 922 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 923): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 923 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 924): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 924 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 925): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 925 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 926):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 926 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  922-926 段次全绿)。下一批规划 (Batch 927): 全量质量门 94 项
  复扫 (距批 921 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 927 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 922-926 段次回归 + 本门全绿收口。
  下一批规划 (Batch 928): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 928 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 929): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 929 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 930): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 930 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 931): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 931 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 932):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 932 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  928-932 段次全绿)。下一批规划 (Batch 933): 全量质量门 94 项
  复扫 (距批 927 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 933 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 928-932 段次回归 + 本门全绿收口。
  下一批规划 (Batch 934): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 934 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 935): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 935 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 936): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 936 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 937): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 937 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 938):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 938 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  934-938 段次全绿)。下一批规划 (Batch 939): 全量质量门 94 项
  复扫 (距批 933 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 939 (全量质量门): 94/94 有效 PASS——直跑 81/94, 尾部
  batch 96-105 + 688/792/793 连续 13 项瞬时失败 (dev server
  跑动尾部 ERR_CONNECTION_REFUSED 掉线窗口, 现已自恢复 200;
  非断言问题), 13 项单独复跑 13/13 即 PASS (瞬时复跑协议先例
  + 6)。本轮 934-938 段次回归 + 本门全绿收口。下一批规划
  (Batch 940): 新回归轮 1-19 段起点; 剩余 7 图上传探索视进度
  插入。
- Batch 940 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点,
  含并行 batch 572 coachmark 落地后首回归)。下一批规划 (Batch
  941): 20-33 段回归续行; 剩余 7 图视段次进度插入。
- Batch 941 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 942): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 942 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 943): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 943 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 944):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 944 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  940-944 段次全绿)。下一批规划 (Batch 945): 全量质量门 94 项
  复扫 (距批 939 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 945 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 940-944 段次回归 + 本门全绿收口。
  下一批规划 (Batch 946): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 946 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 947): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 947 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 948): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 948 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 949): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 949 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 950):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 950 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  946-950 段次全绿)。下一批规划 (Batch 951): 全量质量门 94 项
  复扫 (距批 945 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 951 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 946-950 段次回归 + 本门全绿收口。
  下一批规划 (Batch 952): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 952 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 953): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 953 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 954): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 954 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 955): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 955 (轮转回归): batch 49-64 段 14/14 有效 PASS——直跑
  12/14, batch 49/50 Locator.click 超时瞬时失败 (非断言问题),
  两项单独复跑 2/2 即 PASS (瞬时复跑协议先例 + 7)。下一批规划
  (Batch 956): 65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 956 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  952-956 段次全绿)。下一批规划 (Batch 957): 全量质量门 94 项
  复扫 (距批 951 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 957 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 952-956 段次回归 + 本门全绿收口。
  下一批规划 (Batch 958): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 958 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 959): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 959 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 960): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 960 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 961): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 961 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 962):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 962 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  958-962 段次全绿)。下一批规划 (Batch 963): 全量质量门 94 项
  复扫 (距批 957 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 963 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 958-962 段次回归 + 本门全绿收口。
  下一批规划 (Batch 964): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 964 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  下一批规划 (Batch 965): 20-33 段回归续行; 剩余 7 图视段次
  进度插入。
- Batch 965 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 966): 34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 966 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 967): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 967 (轮转回归): batch 49-64 段 14/14 PASS (续行; 55/60
  两编号历来无验证器文件, 非失败)。下一批规划 (Batch 968):
  65-101 段回归收尾; 剩余 7 图视段次进度插入。
- Batch 968 (轮转回归): batch 65-101 段 25/25 PASS (收尾, 本轮
  964-968 段次全绿)。下一批规划 (Batch 969): 全量质量门 94 项
  复扫 (距批 963 已积 5 批); 剩余 7 图上传探索视进度插入。
- Batch 969 (全量质量门): 94/94 PASS 零失败复扫 (后台单循环,
  全程稳态, 无瞬时失败)。本轮 964-968 段次回归 + 本门全绿收口。
  下一批规划 (Batch 970): 新回归轮 1-19 段起点; 剩余 7 图
  上传探索视进度插入。
- Batch 970 (轮转回归): batch 1-19 段 19/19 PASS (新回归轮起点)。
  收尾指令下落档——下一批规划 (Batch 971): 20-33 段回归续行;
  剩余 7 图上传探索视进度插入。
- Batch 971 (轮转回归): batch 20-33 段 14/14 PASS (续行, 含并行
  batch 576/572 及类型修复落地后回归)。下一批规划 (Batch 972):
  34-48 段回归续行; 剩余 7 图视段次进度插入。
- Batch 972 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 973): 49-64 段回归续行; 剩余 7 图视段次进度插入。
- Batch 577 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 578): 49-64 段回归续行。
- Batch 578 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 579): 65-101 段回归收尾。
- Batch 523 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
- Batch 579 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (577 续 34-48、578 续 49-64、579 收尾 65-101；555/556 已认证全量
  质量门 91/91)。下一批规划 (Batch 580): 全量质量门确认扫 (距批
  556 已积 5 批变更)。
  规划 (Batch 524): 20-33 段回归续行。
- Batch 580 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败，截图随扫刷新入库。下一批规划 (Batch 581):
  1-19 段新回归轮起点。
- Batch 581 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 582): 20-33 段回归续行。
- Batch 586 (全量质量门 + 素材账本): 退出码全量扫 verify-jimeng-
  batch1..105 —— 91 verifier 零失败（首扫被会话中断后重启完成），
  截图随扫刷新入库。同批登记源站探索测试素材账本
  docs/research/jimeng-canvas/TEST_MEDIA_ASSETS.md（10 图片 + 2 音频
  + 2 视频，SHA-256 前 16 位登记；用户 2026-09-24 提供，约束：不得
  实际触发真实生成动作）。下一批规划 (Batch 587): 用测试素材做源站
  上传链路探索（图片/音频/视频上传入口，仅观察不生成）。
- Batch 587 (源站上传链路探索，测试素材首次实战): 用账本素材
  「生成蓝色手机图片-2.png」经左栏 上传 钮 + file chooser 上传——
  源站流程实测：点击即弹系统文件框 → 选定后**立即创建 image 节点**
  (316×316 屏幕尺寸)，imgSrc 为 blob: 本地地址，标题内嵌上传进度
  「正在上传图片 87%生成蓝色手机图片-2」(百分比实时跳动 + 文件名，
  证实批 197 命名模式；clone 以叠加层近似为 CLONE_DECISION)，节点
  即选中；上传未完成时无工具条。删除后基线恢复 (0 次 undo)。
  素材账本其余 13 项待后续批探索 (音频/视频上传、参考图链路)。
  clone 侧本批零改动 (批 197 模型吻合)。现场已还原。
- Batch 588 (音频上传链路探索 + 完整折扣文案新证): 插入音频节点后
  点击 SeedAudio 面板「添加参考」——合成点击**不触发 filechooser**
  (8s 超时，观察模式下面板无变化、无 modal、无 file input，判定需
  真实用户手势，BLOCKED_BY_INTERACTION)；wav 实际上传待用户手动
  或后续真实手势通道。**新证**：点击后面板完整折扣文案链浮现——
  隐藏叶全文「Current price 12. Original price 24. Discount 12.
  积分5折.」(批 485 仅录得前半句，积分五折说明为新细节，与手册
  「✦12 原 24 五折」互证)。素材 voice_converted_1779790519790.wav
  已消耗 1 次尝试未完成上传。现场已还原 (BASE_IDS 核对)。clone
  侧本批零改动 (折扣签形态已按 485 落地)。
- Batch 589 (视频上传链路探索，账本素材实战): 用「S83·镜2.mp4」经
  左栏 上传 钮 + file chooser 上传——**立即创建 video 节点** (550×316
- Batch 590 (轮转回归): batch 1-19 段 19/19 PASS (续行)。下一批
  规划 (Batch 591): 20-33 段回归续行。
- Batch 591 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 592): 34-48 段回归续行。
- Batch 592 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 593): 49-64 段回归续行。
  屏幕)，poster 图存在、无 <video> 元素 (与 clone poster 模型一致)；
  标题带资源处理状态行并实时演进:「S83·镜2」+「1 resource: 0 ready,
  1 processing, 0 failed.」→「1 ready, 0 processing, 0 failed.」
  (新细节：资源处理三态计数，clone 未建模该后缀)；上传完成后即出
  **六条目工具条** (局部重拍/智能超清/视频编辑/截取帧/视频修剪/工具)
  ——与批 484 契约吻合，证实上传完成的视频节点与加工链路同构。
  删除后基线恢复 (0 次 undo，BASE_IDS 核对)。clone 侧本批零改动
  (批 484/589 模型吻合；资源状态行后缀留档不 replicate)。
- Batch 582 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 583): 34-48 段回归续行。
- Batch 583 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 584): 49-64 段回归续行。
- Batch 584 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 585): 65-101 段回归收尾。
- Batch 585 (轮转回归): batch 65-101 段 25/25 PASS——本回归轮闭合
  (581 起 1-19、582 续 20-33、583 续 34-48、584 续 49-64、585 收尾
  65-101)。下一批规划 (Batch 586): 全量质量门确认扫 (距批 556 已
  积 5 批变更)。
- Batch 524 (轮转回归): batch 20-33 段 14/14 PASS (续行)。下一批
  规划 (Batch 525): 34-48 段回归续行。
- Batch 525 (轮转回归): batch 34-48 段 15/15 PASS (续行)。下一批
  规划 (Batch 526): 49-64 段回归续行。
- Batch 526 (轮转回归): batch 49-64 段 14/14 PASS (续行)。下一批
  规划 (Batch 527): 65-101 段回归收尾；其后安排全量质量门确认扫
  (距批 516 已积 5 批变更)。
- Batch 391 (Agent 面板空态布局精修): 按批 381 实测校准
  JimengAiDrawer——面板宽 410→398；技能芯片 h-9 (36px)、px-4、
  gap 8px (行距实测 44px = 36 + 8)，三行居中 wrap 与源一致
  (105×36 / 157×36)。batch 12 宽度断言最小跟进 (410→398)。
  回归: 12/105 PASS；npm run check 通过。
- Batch 392 (Agent 输入行尺寸精修): 按批 382 实测 (全行 32×32)
  将 从本地、画布或资产库添加 / 引用参考 两钮 size-7→size-8；
  发送消息 已是 32。回归: 12 PASS；npm run check 通过。
- Batch 396 (Agent 输入行富文本预填落地): 源站输入区解剖 (contenteditable
  357×84)——预填文案为富文本流: 内联技能芯片「视频反解」84×20 与
  文件芯片「sb_51…tf5q2」113×24 (node-composerChip 类，透明底由内层
  着色) 穿插纯文本。复刻: JimengAiDrawer 新增富显示形态 (refChip +
  prefill 且未编辑时渲染 内联蓝调技能芯片 + 缩略图文件芯片，点击
  进入编辑态换回 input)；隐藏 input 保留 prefill 值供 verifier/无障碍；
  发送钮富显示态视为有内容激活。回归: 8/12 PASS；npm run check
  通过。
- Batch 394 (新建会话钮交互采样): 点击 新建会话 无可视变化 (会话为
  空时无对话可重置)，输入草稿保留；另证批 381 的预填文案在源站
  跨会话持久存留于输入区。clone 新建会话钮维持 inert (无会话列表
  可重置，CLONE_DECISION)。现场未变更节点。clone 侧零改动。
- Batch 395 (全量质量门): 退出码全量扫 verify-jimeng-batch1..105 ——
  91 verifier 零失败 (覆盖批 391/392 Agent 面板精修)，截图随扫
  刷新入库。
- Batch 393 (轮转回归): batch 34-48 段 15/15 PASS。
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

## 9. Batch 794 — 顶栏结构全面对齐（2026-10-01）

取样方式：`scripts/jimeng_headless.py run` + 复用 `scripts/jimeng_deep_snapshot.py`
规范化快照，两侧（源站 / 复刻）同宽 1680×826 抓取后做控件名 diff。登录态由
`scripts/jimeng_login_capture.py --attach-cdp` 捕获（passport 接口 user_id>0 判据），
无头侧即时自验通过。取证脚本：
`jimeng_deep_snapshot.py` / `jimeng_probe794_topbar.py` / `jimeng_probe794_menus.py`。

### 9.1 缺口是怎么找到的

规范化快照对**语义层**（可见交互元素的无障碍名 + 屏幕矩形 + 画布节点几何）取数，
两侧共用同一份提取器，因此 diff 出的差异即真实复刻缺口。源站独有条目 9 项：
返回首页 / 项目 / 节点摘要 / 分享 / 更多 / Credits 入口 / 与 AI 对话 /
Zoom options / Canvas title。复刻此前只有 搜索 / 生成历史 / 用户菜单 / 会员订阅。

### 9.2 SOURCE_FACT — 顶栏 10 个控件（@1680×826，登录态）

顶栏容器 `absolute left-3 top-[10px] h-10`，两簇 `justify-between` 间距 24px。
左簇 230×40 r8；右簇为 5 个独立药丸，间距 16px。

| 控件 | testid | 矩形 | 关键样式 |
|---|---|---|---|
| 返回首页（logo） | `canvas-project-logo` | 40×40 @[12,10] | 内含 40×40 svg（2 path） |
| 项目名 | `canvas-project-title-trigger` | 68×28 @[52,16] | 13px/22px w500，radius **6/2/2/6**，pad 3px 8px |
| 项目箭头 | `canvas-project-trigger` | 20×28 @[120,16] | svg 16，radius **2/6/6/2**，pad 6px 2px |
| 节点摘要 | `canvas-node-summary-trigger` | 28×28 @[156,16] | **10px/18px w400** white/60，距箭头 16px |
| 搜索 | `canvas-panel-launcher` | 28×28 @[1311,16] | r12 |
| 生成历史 | `canvas-panel-launcher` | 28×28 @[1343,16] | r12，与搜索同药丸内 4px 缝 |
| 分享 | `canvas-share-trigger` | 60×28 @[1388,16] | 16px/24 w500，pad 0 10px 0 8px，svg 16 |
| 更多 | （无 testid） | 28×28 @[1465,16] | svg 16，pad 6px |
| 积分 | `canvas-commerce-entry` | 111×28 @[1509,16] | 12px 数字 `#009EFA`，border 1px transparent，svg **12** |
| 用户菜单 | `canvas-user-menu-trigger` | 28×28 @[1636,16] | pad 2px |

节点摘要与项目名的可访问名分别为 `Canvas node summary: 节点 2` /
`Canvas title: 测试项目`；积分入口为 `Credits: 805 · 基础会员`。

### 9.3 SOURCE_FACT — 四个触发器的浮层

- **分享** → 400×251 @[1268,56]，右缘与顶栏右内边距齐平。逐字文案：分享画布 /
  画布链接 / 复制链接 / 仅自己可访问 / 只有你可以通过此链接访问画布 /
  创建团队，与成员在画布实时协作 / 创建团队。
- **更多** → `role=menu` 200×84 @[1379,56]，z-[120]，两项 `role=menuitem`
  192×36（y=60 / y=100，项间 4px 缝，菜单比项左右内缩 4px）。**水平以触发钮
  居中**（1379+100 = 1479 = 更多钮 1465+28/2）。文案：项目信息 / 复制项目。
- **项目箭头** → 240×200 @[12,52]，**左缘对齐顶栏左内边距**（不是贴箭头）。
  文案：项目 / 测试项目 / 未命名项目 / 视频创作 / 新建画布项目。
- **节点摘要** → `role=dialog` 200×92 @[69,47]，z-50，**水平以触发钮居中**
  （69+100 = 169 = 节点钮 156+28/2），纵向落在触发钮下沿 +3px。含节点条目
  （实测「视频 1」）+ 「查看项目信息」。

### 9.4 两条被证伪的旧结论（重要）

1. **「资源处理三态计数」不是视觉元素**。旧记录（批 581）留下的
   `1 resource: 0 ready, 1 processing, 0 failed.` 留档未复刻，本批复查
   `jimeng_probe794_titlerow.py` 确认该串位于 **`sr-only`** 容器（1×1 px），
   是纯无障碍状态文本，空节点上恒显示 `No resources: 0 ready, 0 processing,
   0 failed.`，另有 `Not selected.`。**不应**做成可见状态行——照做会凭空
   造出源站不存在的 UI。维持不 replicate，但把「它在 sr-only 里」这一事实
   补进记录。
2. **顶栏「更多」不是帮助菜单**。复刻此前把账号菜单挂在头像上、顶栏无「更多」；
   源站「更多」是独立控件，展开的是 `项目信息 / 复制项目` 两项菜单。

### 9.5 CLONE_DECISION

- 积分数值沿用既有 mock `745`（源站读数 805 随账号/时间变化，不稳定），
  以与 `JimengMemberModal` 的「积分详情 745」保持一致；**稳定的 SOURCE_FACT
  是格式**（`{数字} 基础会员`，12px 品牌色数字 + 12px 钻石图标）。
- 分享按钮宽度钉死 60px：源站标签字号小于按钮继承的 16px，按复刻字体度量
  会算到 70px，故以实测宽度为准。
- 「未命名项目」「视频创作」按源站原文保留为 mock 项目/分类文案。
- 右簇横向位置是**派生量**（右锚 + 间隙累加），验收断言「尺寸精确 + 右缘
  1668 + flex 间隙 16px + 视觉间隙 13..21」，而非逐控件绝对 x。

### 9.6 实现过程中踩到的两个真 bug（非样式）

1. **zustand selector 返回新数组 → 整页白屏**。
   `useJimengStore(s => s.nodes.map(...))` 每次返回新数组，`Object.is` 快照
   比较恒为 false，触发 `The result of getServerSnapshot should be cached`
   与 `Maximum update depth exceeded`，整页只剩 "This page couldn't load"。
   修法：取 `s.nodes` 稳定引用后再 `useMemo` 派生。**注意：项目里凡是
   selector 里 map/filter 的都要查这一条。**
2. **工作区全局 Escape 会吞掉浮层的冒泡监听**。`JimengWorkspace` 有全局
   Escape 处理器，冒泡阶段 `stopPropagation` 后，浮层自己挂在 `window` 上的
   冒泡 keydown 监听收不到事件 → Escape 关不掉浮层。修法：浮层 Escape 监听
   改用**捕获阶段**。

### 9.7 回归

`verify-jimeng-batch794.py` 55 项断言全通过（含几何、圆角、字号、四个浮层
文案与定位、浮层互斥、积分入口仍开会员弹层、画布 2 节点未受影响、无 console
错误）。受影响的 7 个旧 verifier（13/26/28/30/43/57/59）定位符由
`button[aria-label="会员订阅"]` 改为 `[data-testid="canvas-commerce-entry"]`。

### 9.8 实施落点

- `src/components/jimeng/JimengTopBar.tsx` — 左簇重构为 logo + 标题/箭头拼接段
  + 节点摘要 + 已保存；右簇补 分享 / 更多，积分入口改为源站规格。
- 新增 `JimengMoreMenu.tsx` / `JimengSharePanel.tsx` / `JimengProjectPanel.tsx` /
  `JimengNodeSummaryPopover.tsx` 四个浮层，文案与几何按 §9.3。
- `src/components/jimeng/JimengMemberModal.tsx` — Escape 改捕获阶段（见 9.6.2）。
- `scripts/jimeng_deep_snapshot.py` — 源站/复刻通用的规范化结构快照（可 diff）。
- `scripts/jimeng_probe794_titlerow.py` / `jimeng_probe794_topbar.py` /
  `jimeng_probe794_menus.py` — 本批取证脚本。
- `scripts/verify-jimeng-batch794.py` — 55 项断言。

### 9.9 下一批候选（已定位，未实施）

1. **8 个浮层共用同一个 Escape 脆弱写法**。`JimengContextMenu` /
   `JimengHelpMenu` / `JimengHistoryMenu` / `JimengMultiSelectToolbar` /
   `JimengPaneContextMenu` / `JimengSearchOverlay` / `JimengShortcutsPanel` /
   `JimengVideoPreview` 都在 `window` 上挂**冒泡** keydown 处理 Escape，机制与
   9.6.2 相同 —— 只要工作区全局 Escape 先触发同步重渲染，它们就可能在同一次
   派发里被跳过。应统一改捕获阶段并逐个补 Escape 断言。
2. ~~**AI 抽屉默认展开会盖住顶栏右簇**。~~ **已于 batch 797 关闭**：源站首屏
   Agent 面板**默认收起**（登录态实测 + 点「与 AI 对话」前后对照），复刻已改为
   默认收起，详见 batch 797 条目。**原问题描述里「顶栏被挤成竖排」的那部分属
   误归因**——竖排来自「分享」按钮内部换行，与抽屉无关，另立条目跟踪。
3. 顶栏「项目」面板里 `未命名项目 / 视频创作` 目前是 mock 文案，源站这两项的
   真实数据源（项目列表接口）未取证。
4. **顶栏右簇 2–4px 横向漂移 —— 根因已定位，一行可修，但等 `JimengTopBar.tsx`
   空闲**。（2026-10-01 缩放归一化后 @100% 逐项实测）
   源站 搜索 1311 / 生成历史 1343 / 分享 1388 / 更多 1465 / 积分 1509 /
   用户菜单 1636（积分药丸 @[1505,12] 163×36，右缘 1668）。
   复刻 1315 / 1347 / 1391 / 1467 / 1511 / 1636 ⇒ 越往左漂移越大（+4…+2）。
   **不是间隙问题**：两侧药丸间距实测都是 12px，完全一致。唯一成因是
   **分享药丸 padding 4px（68 宽）vs 源站 5px（70 宽）**。右簇右对齐
   （积分药丸右缘两边都是 1668），所以这 1px/边沿左方向累积放大。
   改 `<div className="jimeng-chrome-pill flex h-9 shrink-0 items-center p-1">`
   为 `p-[5px]` 即可让**五个控件一次全部归位**（更多 −2、分享 −3、生成历史 −4、
   搜索 −4）。**不要动右簇的 `gap`**（已验证两侧都是 12px）。
   未实施原因：该文件当时正被并行 session 编辑（且其工作也标为 batch 801），
   贸然改会覆盖他人内容。已验证：改后节点/其余 chrome 不受影响。
5. ⚠️ **跨站对比前必须做缩放归一化**。源站画布当前是 100%、复刻 demo 是 73%，
   直接比会得到大量假差异：本批一度以为「复刻视频节点 415×234 比源站
   569×320 小了一大截」，归一化后复刻正是 **569×320，完全一致**。
   `scripts/jimeng_deep_snapshot.py` 已内置 `SNAP_VW/SNAP_VH`，但**视口尺寸
   相同不等于缩放相同**；比对节点/几何前要先把两侧 zoom 调到同一档。

## 10. Batch 795 — Agent 面板几何 + 顶栏让位重排（2026-10-01）

取证：`scripts/jimeng_probe795_agentpanel.py`（面板默认态 / z 层级 / 顶栏命中测试）、
`scripts/jimeng_probe795_avatarpill.py`（右簇各控件的**祖先链**复查）。

### 10.1 SOURCE_FACT — Agent 面板

| 项 | 值 |
|---|---|
| 可访问名 | `Agent`（**不是**「AI 对话」；复刻原为 `AI 对话`，本批改正） |
| 矩形 | **400×802 @[1268,12]**（右/上/下各内缩 12px） |
| z-index | 40 |
| 圆角 | **20px**（复刻原 398 宽 / rounded-2xl=16px） |
| 类名 | `rounded-[20px] bg-assistant-sidecar-surface border border-dreamina-stroke-primary` |
| 入口 | 右下角浮动钮，可访问名 `与 AI 对话`，**118×34 @[1549,779]**（复刻 118×34 已吻合） |

- SOURCE_FACT: **载入后抽屉未展开**（`drawers: []`），只有右下角入口钮在场。
  复刻自 batch 398 起默认展开（`aiDrawerOpen: true`）—— 该默认值与本次实测不符，
  但它是被 398 明确记录的决定且多个 verifier 依赖，本批**不改默认值**，
  改为让顶栏在两种状态下都正确（见 10.2）。默认值是否该改列为待决。

### 10.2 SOURCE_FACT — 顶栏让位（本批核心）

面板展开时，源站顶栏**向左让位**，而不是被面板遮住：

| 状态 | 积分入口 | 用户菜单 | 顶栏容器右缘 |
|---|---|---|---|
| 面板收起 | 右缘 1620 | 按钮右缘 **1664** | 1668（= 1680-12） |
| 面板展开 | 右缘 1208 | 按钮右缘 1252 | 1256 |

推导：头像在药丸内、药丸右内边距 4 → 药丸右缘 = 按钮右缘 + 4；
积分与头像同处一个药丸、内距 16 → 积分右缘 = 头像右缘 - 16 - 28。
故顶栏 `right` 内边距在面板展开时取 **424**（= 1680 - 1256）。

SOURCE_FACT: 面板展开时顶栏四个右簇控件中心点 `elementFromPoint` **仍命中自身**
（不被面板拦截）。复刻原为右锚定，被 `absolute inset-y-3 right-3 z-40` 的抽屉
整块盖住 —— batch 794 验收时点击「分享」被抽屉拦截超时，正是这个缺陷。

### 10.3 SOURCE_FACT 订正 — 右簇是 4 个 36px 高 chrome 药丸（推翻 batch 794 的两处判断）

复查祖先链（`jimeng_probe795_avatarpill.py`）得到：

| 药丸 | 矩形 | 内含 |
|---|---|---|
| pill-1 | [1307,12] **68×36** r8 blur(40px) | 搜索 · 生成历史（各 28×28 r12） |
| pill-2 | [1383,12] **70×36** | 分享 60×28 |
| pill-3 | （未单测，约 36×36） | 更多 28×28 |
| pill-4 | [1505,12] **163×36** | **积分 111×28 + 用户菜单 28×28**（药丸内 gap 16） |

由此订正 batch 794 的两处错误：

1. **「用户菜单」确实在 chrome 药丸内**（pill-4），batch 794 依据按钮自身
   `border: 0px none` 判它「不在药丸内」是错的 —— 按钮透明、背景在祖先上。
   batch 96 的期望已改回「在药丸内」。
2. **药丸之间是 8px**（pill1 右 1375 → pill2 左 1383 等），不是 16px。
   之前量到的「按钮到按钮 16px」= 8(药丸间) + 4 + 4(药丸内边距)。
   batch 794 验收里「右簇 flex 间隙 16px」已改为 8px。

另外：积分入口**自身不带 chrome 背景**，它与头像共享 pill-4 的背景 ——
复刻原把 `jimeng-chrome-pill` 直接挂在积分按钮上（多出一层背景），本批改为
外层 36px 高药丸包住「积分 + 头像」，与源站同构。

### 10.4 实施落点

- `JimengAiDrawer.tsx` — 400 宽 / `rounded-[20px]` / `aria-label="Agent"`。
- `JimengAiButton.tsx` — 补 `aria-label="与 AI 对话"`（源站有）。
- `JimengTopBar.tsx` — 读 `aiDrawerOpen`，展开时 `right: 424`；右簇 4 个药丸
  同构化，簇内 `gap-2`(8px)。
- `scripts/verify-jimeng-batch795.py` — 23 项断言（面板几何 / 让位后各控件右缘 /
  命中测试 / 收起复原 / 重开复原）。

### 10.5 顺带修好的既有缺陷

batch 794 定位到的「浮层 Escape 冒泡监听被跳过」问题，本批已把剩余 3 处
（`JimengZoomMenu`、两处 `JimengVideoNode`）也统一为捕获阶段 ——
`src/components/jimeng/` 下再无 `addEventListener("keydown", onKey)` 冒泡写法。
其中 `JimengHelpMenu` 的修复直接让 batch 7 从 FAIL 转 PASS。

### 10.6 已知与本批无关的既有缺陷

- `verify-jimeng-batch37.py`「click seek regression: 0:04」：点进度条 99.9% 处
  期望 0:05/0:06、实测 0:04，3/3 确定性复现；把 `JimengVideoNode.tsx` 与
  `JimengVideoPreview.tsx` 临时还原到 HEAD 后**同样失败**，确认为既有缺陷。
  留给后续批次。

## 11. Batch 799 — 「更多」菜单两项动作落地（2026-10-01）

取证：`scripts/jimeng_probe797_moremenu.py`（点两项后各抓一轮浮层）、
`scripts/jimeng_probe797_copytoast.py`（点击后 120ms 高频轮询，专抓短命 toast）。

> 编号说明：797 被并行会话占用（Agent 抽屉默认收起 + 触发钮材质契约），
> 本批取 799 以免撞号。

### 11.1 SOURCE_FACT — 项目信息

点「更多 → 项目信息」弹出模态：

| 项 | 值 |
|---|---|
| role | `dialog` |
| 矩形 | **800×546 @[440,140]** |
| 定位 | `fixed left-1/2 top-1/2`（水平垂直居中，max-h-[80vh] max-w-[calc(100vw-32px)]） |
| 可访问名 | `项目信息` |

文案逐字（basic 页）：项目信息 / 基础信息 / 积分消耗 / 所有者 / 创建时间 /
最新修改 / 节点分布 / 全部节点 / 全部 / 图片 / 视频 / 音频 / 文本 / 时间线 /
主体 / 其他 / 查看积分明细。Esc 可关闭。

节点分布表按类型给计数，SOURCE_FACT 显示它随项目内容变化（本次读到
「全部 1 / 图片 0 / 视频 1 / 音频 0 …」，而同刻画布 DOM 里有 8 个节点 ——
该表口径未完全查清，复刻按 store 实时统计实现，属 CLONE_DECISION）。
「时间线 / 主体 / 其他」三类复刻无对应节点类型，恒 0。

### 11.2 SOURCE_FACT — 复制项目

点「更多 → 复制项目」把画布链接写入剪贴板，并弹**顶部居中 toast**：

| 项 | 值 |
|---|---|
| 文案 | `复制画布中...` |
| toast 壳 | **127×44 @[776,24]**（(1680-127)/2 = 776.5，水平居中） |
| 类名 | `flex min-h-dreamina-toast w-fit max-w-full grid-col-none items-center` |
| 文本 | 13px（`text-dreamina-cn-13 leading-dreamina-toast`），内层 [812,35] 75×22 |

- 第一轮采样等 2.6s 没抓到任何浮层，差点误判为「静默无反馈」；改成 120ms
  轮询后立刻抓到。**短命反馈必须高频采样**——这是本批的方法论教训。
- 复刻复用既有全局 toast（`JimengTaskToast` / store `pushToast`），文案逐字
  「复制画布中…」。toast 壳几何仍是既有近似（源站 127×44@top24，复刻 top-16
  且高度不同），未在本批改动 —— 它被多处复用，改动面大于本批范围，留作后续。

### 11.3 实施落点

- 新增 `src/components/jimeng/JimengProjectInfoModal.tsx`（800×546 居中，
  基础信息/积分消耗双页签，节点分布实时统计）。
- `JimengTopBar.tsx` — 「更多」两项接上真实行为：项目信息开模态、复制项目
  写剪贴板 + 弹 toast；`closeAll()` 一并收起模态。
- `scripts/verify-jimeng-batch799.py` — 29 项断言（含剪贴板读回、toast 文案、
  模态几何与 16 段文案逐字、页签切换、Escape 关闭、顶栏/节点数未受影响）。

### 11.4 共享工作区事故（记录在案）

本批取号时先后撞上并行会话已存在的 `verify-jimeng-batch797.py`（已入库）与
**未入库的** `verify-jimeng-batch798.py`：我第一次写 798 时直接覆盖了后者，
该文件不在 git 里、无法恢复，随后我把 798 删除以让出编号。教训：共享工作区
里写新文件前必须先确认目标路径是否已被他人占用（`ls` / `git status`），
不能只依赖 `git ls-files`（那只看得到已入库的）。

## 12. Batch 800 — 关闭 batch 37「点击 seek 回归」：实为断言点位踩亚像素（2026-10-01）

上一批把它记成「既有缺陷，留给后续批次」。本批查清根因并关闭。

### 12.1 症状

`verify-jimeng-batch37.py` 确定性失败（3/3）：
`click seek regression: 0:04` —— 期望点进度条末端得到 0:05/0:06，实测停在
0:04，而 0:04 正是该用例上一步 drag-scrub 到 75% 留下的值。

### 12.2 根因：不是产品缺陷，是断言点位在进度条之外

逐点实测（每次点击后读时间，并用 `elementFromPoint` 确认是否命中进度条）：

| frac | 时间 | 命中进度条 |
|---|---|---|
| 0.5 | 0:03 | ✅ |
| 0.9 | 0:05 | ✅ |
| 0.98 | 0:05 | ✅ |
| 0.999 | （未变） | ❌ |
| 0.9999 | （未变） | ❌ |

- 进度条元素 `[data-testid="video-progress"]` CSS 高 8px，经 xyflow 视口变换
  （scale≈0.729）后 `getBoundingClientRect()` 高 5.84px、宽 415.31px。
- 原断言取 `frac=0.999` → `x = r.x + r.width*0.999`，距右缘仅 **0.4px**。
  该点被 `elementFromPoint` 解析到节点根 `div.group.relative`
  （`inBar: False`），进度条的 `pointerdown` 监听计数为 **0** —— 事件压根没到
  进度条，所以时间自然停在上一步的值。
- 命中链实测（中点 x=640）：`div[5px track]` → `div[nodrag … z-[2]]`（进度条本体）
  → 卡片控制行 `z-[1]` → poster `img` → 节点根。进度条 z-index 高于控制行，
  正常位置可命中；排除「被圆角 overflow-hidden 裁掉」这一猜想。

**结论**：seek 逻辑本身正确，失效仅发生在右缘不足 1px 的亚像素带。
原断言把亚像素边界当成了功能契约。

### 12.3 处置

`verify-jimeng-batch37.py` 的点击点位 `0.999 → 0.98`，并就地写明根因。
产品侧未改动：没有证据支持「末 1px 不可点」是需要修的可用性问题
（真实用户点不到 0.4px 宽的条带），不做无依据的改动。

## 13. Batch 801 — 画布/顶栏根节点可访问名（2026-10-01）

快照 diff（`scripts/jimeng_deep_snapshot.py`，源站 vs 复刻同宽 1680×826）
在本批前只剩 4 条源站独有条目，其中 2 条是**根节点可访问名**，2 条是内容差异
（节点数 / 积分数值 / 缩放百分比，均为已知且有据的取舍）。本批补掉可访问名。

### 13.1 SOURCE_FACT

| 元素 | 属性 |
|---|---|
| 画布根 `.react-flow` | `aria-label="Canvas"`、`role="application"`、`data-testid="rf__wrapper"`、类名含 `octo-canvas-flow bg-dreamina-canvas-bg` |
| 顶栏根 `<header>` | `aria-label="Canvas top bar"`、`data-testid="canvas-top-bar"` |

### 13.2 实施

- `JimengTopBar.tsx` — header 补 `aria-label` + `data-testid`。
- `JimengWorkspace.tsx`（`JimengFlow`）— 画布根补 `aria-label="Canvas"`，并在
  xyflow 未自带 `role` 时补 `role="application"`。

**踩坑：`<ReactFlow ref>` 在 xyflow v12 拿到的是 `ReactFlowInstance`**（fitView /
zoomIn 等实例 API），**不是 DOM 节点**，直接 `ref.current.setAttribute` 不生效
（首次实现即因此断言失败，aria-label 读回为 None）。正解是给外层真实容器挂 ref，
再 `container.querySelector(".react-flow")` 取到根元素后写属性。

### 13.3 剩余 diff（有意保留）

- `Canvas node summary: 节点 1` vs `节点 2` —— 源站示例画布内容已被并行会话
  探索改动（2 节点 → 一度 8 节点 4 边），复刻 demo 保持 2 节点基线。
- `Credits: 805` vs `745` —— 积分数值随账号/时间变化，复刻用既有 mock 745
  以与 `JimengMemberModal` 一致（稳定的 SOURCE_FACT 是格式，见 §9.5）。
- `Zoom options, 100%` vs `73%` —— 源站当前视口 100%；复刻沿用 README §4 记录的
  源站初始矩阵（73%）作为 demo 初始态。

## 14. Batch 803 — 顶栏新增控件接成真交互（2026-10-01）

batch 794/795/799 把顶栏控件的**外观与文案**复刻出来了，但其中若干按钮是死按钮：
分享面板的「复制链接」没有 `onCopy`、节点摘要弹层点节点没有任何反应、
项目面板点项目名/新建都不动、项目信息的「查看积分明细」不跳转。
静态复刻做到这一步就停了 —— 本批把它们接成**真交互**（mock 数据支持）。

### 14.1 交互契约与实现

| 控件 | 交互 | 实现 |
|---|---|---|
| 分享面板「复制链接」 | 写剪贴板 + toast | 复用 batch 799 的 `copyProject()` |
| 节点摘要弹层 · 节点条目 | 该节点**被选中**且**视口聚焦**平移过去 | store 新增 `focusNodeRequest {id, nonce}` + `requestFocusNode(id)`；`JimengFlow` 用 `fitView({nodes:[{id}], duration:300, maxZoom:1, padding:0.35})` 聚焦 |
| 节点摘要「查看项目信息」 | 打开项目信息模态 | 复用 `projectInfoOpen` |
| 项目信息「查看积分明细」 | 跳会员弹层的「积分详情」，并关闭本模态 | 跨面板闭环 |
| 项目面板 · 项目名 | 改写顶栏标题（`renameProject`）+ toast | mock 切换 |
| 项目面板「新建画布项目」 | toast | mock |

`focusNodeRequest` 带 `nonce`：只存 id 的话，重复点同一节点时值不变、
`useEffect` 不会重跑，第二次点击就失灵。nonce 让重复点击仍能触发。

### 14.2 验收取向：断言**状态变化**，不断言元素存在

`verify-jimeng-batch803.py` 17 项断言里，交互类断言都读**状态**而非存在性：
剪贴板内容、`.react-flow__node.selected` 的 data-id、`.react-flow__viewport`
的 transform 前后是否不同、顶栏标题 innerText 是否改名、toast 文案。
「按钮存在」只能证明外观在，证明不了它是活的。

踩坑：断言节点内容时用 `[data-id="..."]` 命中了 2 个元素 —— 节点本体与它的
`NodeToolbar` **共用同一个 data-id**。必须写成 `.react-flow__node[data-id="..."]`。

---

## 15. Batch 804 — 节点摘要弹层：写死的高度（批次的教训：单次读数不能当常量）

### 15.1 症状

源站示例画布的节点数被并行会话改动后（2 → 8 → 4），复刻侧节点摘要弹层的高度
明显对不上：源站 4 个节点时弹层 132px，复刻侧仍恒为 92px，底部「查看项目信息」
被截在 92px 的框里，条目区溢出。

### 15.2 根因：92px 是 N=1 的特例，被当成了常量

- batch 795 记录弹层为 `200×92`。**当时画布只有 1 个节点条目**（N=1）。
- batch 794 复刻时把这个数字直接写进 `h-[92px]`。
- 它不是「这个浮层就是 92 高」，而是「N=1 时恰好 92 高」。

与 batch 800 同一类错误：**在一个具体读数上锚定，而不是锚定规则**。

### 15.3 SOURCE_FACT（登录态，1680×826，N=4 时实测 200×132）

| 构成项 | 值 |
|---|---|
| 宽度 | 200px |
| 圆角 | 12px（`rounded-xl`） |
| 上下内边距 | 各 4px |
| 条目行高 | 36px |
| 条目行间距 | 4px |
| 分隔块 | 4px（内含 1px 线，上下各 4px） |
| 底部「查看项目信息」 | 36px |

推出公式：

```
H = 4 + (36N + 4(N-1)) + 4 + 4 + 4 + 36 + 4 = 40N + 52
```

交叉验证：N=1 → 92（与 batch 795 当初读数吻合）、N=2 → 132（吻合）、
N=4 → 212。

### 15.4 实施

`JimengNodeSummaryPopover.tsx`：去掉 `h-[92px]`，改内容驱动 ——
`p-1`（4px padding）+ `rounded-xl`、条目 `h-9`、列表 `gap-1`、
分隔 4px 块、底部按钮 `h-9`。公式写进文件头注释，避免下次再被当成巧合。

同时修掉 `verify-jimeng-batch794.py` 里照抄的 `200x92` 断言：改为**按条目数套公式**
（读弹层里的按钮条数 N，断言高度 = 40N+52）。写死数值在节点数一变时就假失败。

### 15.5 验收：13 项断言，含一个「证伪型」断言

`verify-jimeng-batch804.py` 的关键不是断言 132，而是断言**高度随内容增长**：
用 `page.evaluate` 往条目容器里注入一个 36px 的多余 `<button>`，断言弹层高度
**正好 +40**。如果哪天有人又把高度写死，这条会立刻失败 —— 它是对
「内容驱动」这个属性本身的检验，而不是对某个数字的检验。

回归：794（56 项）/ 795（25 项）/ 803（17 项）全过。

## 16. Batch 806 — 节点连接手柄（+ 环钮）：实名 / 几何 / 外观 / 出现时机（2026-10-03）

### 16.1 取证方法与两次自我纠错

本批要验的是节点边缘那个「+」环钮。写下探针后接连踩了两个坑，都记在这里，
因为它们和 batch 796「只比内层控件得出假结论」是同一类错误：

1. **落点被重叠节点吃掉**。源站画布上 4~6 个音频节点几乎完全叠在视频节点
   内部（视频 454..1023×285..605，音频 578..978×305..665）。第一版探针
   对每个 frac 循环「一见落在自己矩形内就 break」——那等价于**永远选中心点**，
   而中心点恰恰是被压得最狠的地方。连点 5 次只选中过「音频 4」。
   修正：每个 frac 各自算一次「被几个别的节点盖住」，取最小。
   （`scripts/jimeng_handle_probe2.py` 的 `pick()`）
2. **拿音频节点的样本推视频节点**。批 210/380 记的是「本地上传视频节点
   左侧无 +」，而我第一轮量到的全是音频节点。**用错样本的结论等于没量。**
   修法是先把视频节点单独选出来再量——这直接推翻了批 210 的旧记载（见 16.3）。

第二轮探针运行时画布已被别的进程改动，节点数一路从 5 变 7 又回落，
最后只剩 1 个节点，反而让「精确选中视频节点」变简单，于是重跑了一次干净取样
（`handle2-source.json`，对比 `handle2-source-stacked.json` 留档）。

### 16.2 SOURCE_FACT — 连接手柄六条（@1512×950 画布 / 100% zoom）

1. **实名** = `Create connected node before {节点标题}` /
   `Create connected node after {节点标题}`。标题动态插值，实测过
   「视频 1」「音频 4」「音频 5」三个节点，串长随标题变化。
   元素是真正的 `<button>`，不是 `role="button"` 的 span。
2. **命中盒** 36×36，`rounded-lg`(8px)、`border border-transparent`(1px)、
   `p-2` —— 自身 `background-color: rgba(0,0,0,0)`、`border-color` 透明。
3. **外观**（像素级，806-source-plus-left.png 的 36×36 盒内亮度图）：
   盒中是一个**空心圆环**，外径 **≈24px**、1px 描边（主色 rgb(92,92,92)，
   峰值 rgb(167,167,167)），**环内完全透明**（露出画布底 rgb(13,13,13)），
   中心一个 ≈8×11 的 `+` 字形。
4. **位置** 垂直**精确居中**于节点（实测偏差 0.0px）；水平方向紧贴节点缘
   **外侧**，间隙 **2~4px**（视频节点实测左 3 / 右 2，音频节点 4）。
   故 36px 命中盒的左缘落在 `-39px`，圆心在缘外 21px。
5. **出现时机 = 仅节点选中时挂载**。三次定向验证：未选中时分别悬停在
   左侧 60×120 热区、节点边缘、节点中心，各等 900ms，
   `querySelectorAll('[aria-label*="onnected"]')` 恒为 **0**——
   不是 CSS 隐藏，是**根本不在 DOM 里**。
6. **四类节点两侧都有**，含**带媒体的视频节点**（选中「视频 1」时
   before/after 同时出现），音频节点同理。

**不动的部分**：60×120 隐形热区。源站类名
`react-flow__handle-left nodrag nopan !top-1/2 !z-10 !rounded-none
!border-0 !bg-transparent !p-0`，transform `matrix(1,0,0,1,∓30,-60)`——
圆心正落在节点缘上，与复刻的 `left/right:-30 + translateY(-50%)` 完全一致。
本批确认后**保持原样**（批 17 起既有契约）。

### 16.3 推翻的两条既有记载

| 旧记载 | 位置 | 现状 |
|---|---|---|
| 「+ 圆钮 24px，hover/选中显示」 | §5 | 命中盒 36×36（批 210 已改对）；**hover 不显示**，仅选中时挂载 |
| 「DOM 常驻 hover 显示」 | 批 380 | 未选中时 DOM 里 0 个，谈不上常驻 |
| 「本地上传节点仅右侧有，空节点两侧都有」 | §5 | **与 source 无关**，四类节点一律两侧。复刻里 `d.source === "empty"` 才给左钮的条件已删除 |

第三条顺带说明：复刻此前的规则让「有媒体的视频节点」只剩右侧一个钮，
而源站两侧都有——这条差异在有媒体节点上最显眼，而 demo 默认恰好就是
有媒体节点，等于长期可见。

### 16.4 实施

新增 `src/components/jimeng/JimengConnectHandles.tsx`，四类节点共用
（此前每类各写一份 60×120 内联 style，加规则要改四处）：

- 隐形热区 60×120 照旧，圆心压在节点缘上
- + 钮 = 36×36 `<button>`，`left/right: -(36+3)`，垂直居中
- 环 = 24px `rounded-full` `border-white/50` **无填充**，内含 10px `Plus`
- **仅 `selected` 时渲染**（不是 CSS 隐藏，见 16.2 第 5 条）
- 菜单（JimengInsertMenu）与 Escape 关闭一并收进本组件
- 接入视频 / 图片 / 文本 / 音频四类节点，后三类此前**根本没有 + 钮**

**顺带修掉的既有缺陷**：插入落点。此前视频节点传的是
`{x: size.width + 200, y: 0|120|240}`，而 `addNodeAt(kind, position)` 收的是
**绝对**世界坐标——于是不管源节点在哪，新节点一律落在画布原点附近。
现统一按 `addVideoNodeAfter` 的同一套算式（源点右侧 +160、垂直 +44）计算。

### 16.5 验收

新增 `scripts/verify-jimeng-batch806-connecthandle.py`。两个踩坑经验写进了断言写法：

- **必须先做缩放归一化**。demo 默认视口 73%，不归一的话量到的是 26×26 而不是
  36×36，会得出「尺寸不对」的假结论（26/36 = 0.7222）。断言前从
  `.react-flow__viewport` 的 transform 矩阵取 zoom，长度全部除以它。
- 间隙/居中用**相对断言**（间隙 2~4px、垂直偏差 ≤1px），不写死绝对坐标。

断言：未选中时 DOM 里 0 个钮 → 选中后两侧各一 → 实名带标题 → 命中盒 36×36 →
自身无底色 → 间隙 2~4px → 垂直居中 → 环 24px 且**是圆**且**无填充** →
60×120 热区仍在 → 图片/文本/音频三类也各有 2 个。
「是不是圆」用 `radius ≥ 环宽/2` 判，因为 `rounded-full` 的 computed 值是
3.35e7px 这种巨大数字，写死 `9999px` 会对不上。

回归：4 / 14 / 16 / 17 / 20（这 5 个原本按中文 aria
`右侧添加节点` 选钮，全部改成源站实名 + 先点一下节点选中）/ 24 / 25 / 93 / 806 全 PASS。

**顺带修掉的旧账**：batch 93 一直在失败——它期望 dock 第 4 个按钮叫「缩放」，
而 batch 796 已按源站把实名改成 `Zoom options, {n}%`。796 那批的回归清单
里没有 93，所以这笔失败被漏了下来。断言已改成前三项精确 + 第四项正则
`Zoom options, \d+%`（百分比随视口变，写死 73% 会在非默认视口下假失败）。

### 16.6 事故与遗留

1. **编号连续撞车两次**。并行 session 正在同一个 master 工作区上以同样的
   节奏推进 batch 号，两次都撞上：
   - 第一次：本批探测期间对方提交了 `549c601b feat: batch 804 jimeng ——
     节点摘要弹层高度改内容驱动`，我按会话开头规划把 verifier 写成
     `verify-jimeng-batch804.py`，**覆盖了对方的文件**。已用
     `git checkout --` 还原到 549c601b 的版本（该文件在 HEAD 里存在，
     未提交部分无法找回），本批改号 805。
   - 第二次：改号 805 之后，对方的「左栏三个死按钮 → 插入时间线/主体/导演台
     节点」也占用了 805（`scripts/verify-jimeng-batch805.py` + 
     `scripts/jimeng_dead_button_audit.py`），我的 805 又被覆盖。对方的 805
     未提交，**同样无法找回**——这两次都是我覆盖别人。
   - 第三次：定号 806 后再写，又发现 `verify-jimeng-batch806.py` 已被对方占用
     （同样是未提交草稿，同样无法找回）。

   **收尾处置**：本批 verifier 改用带主题后缀的唯一文件名
   `scripts/verify-jimeng-batch806-connecthandle.py`，并把
   `verify-jimeng-batch806.py` 这个号**让回**给并行 session（确认它不存在）。
   本批代码/台账编号仍记 806。

   **给后续 session 的硬约定**：在这个共享工作区里，
   `scripts/verify-jimeng-batchNNN.py` 这种纯编号文件名**已被证明不可用**——
   一小时内连撞三次（804/805/806），每次都是我覆盖别人，其中两次不可恢复。
   写 verifier 请带主题后缀（`verify-jimeng-batchNNN-<主题>.py`）；
   若必须用纯编号名，务必在**写文件的那一瞬间**重新确认，而不是沿用
   会话开头的 `ls` 结果。

   教训（同批 797 的加强版）：**会话开头 `ls` 到的编号列表在半小时后就过期**，
   必须在**写文件的那一瞬间**重新确认；更稳的做法是提交前用
   `git commit -- <pathspec>` 把自己的文件先落盘，别让「规划编号」和
   「磁盘文件名」之间隔着一段长时间的取证工作。
2. **源站画布节点数发生变化**：本批探测期间源站画布的节点从
   「视频 1 + 音频 1..4」变成只剩「视频 1」（顶栏 `Canvas node summary: 节点 1`）。
   本批脚本**没有按过 Delete/Backspace**（清理脚本的删除分支因「多出的节点」
   为空而未进入），无法确证是并行的其他探索 session 所为还是别的成因。
   ⌘Z 连按 6 次无效，站点未提供可用的撤销入口。**现状反而更接近 §5 记载的基线**
   （§5 只记了两个视频节点、无音频节点），但无法确证，如实记录在此。
3. 本批未取样的部分：`+` 菜单在源站的确切落点（复刻沿用既有的 ±22px 契约）、
   环描边的精确 alpha（实测落在 rgb(85~92)，抗锯齿后无法反推真值，
   复刻保留批 210 的 `border-white/50`）。

---

## 16. Batch 807 — 死按钮普查：把「有没有接交互」变成可重复的体检

### 16.1 起因

batch 794~803 是一批一批按控件把顶栏接成交互的，但**没有系统性手段**证明
「没有漏网的死按钮」。于是写 `scripts/jimeng_dead_button_audit.py`：遍历页面上
所有可点元素，逐个点击，比对点击前后的可观测状态。

### 16.2 普查结论（1680×826 demo 画布，40 个可点元素）

**真死按钮只有 3 个，全在左栏：时间线 / 主体 / 导演台。**

其余 11 个命中经人工复核是**探针盲区**，不是缺陷 —— 这一点比结论本身更重要：

| 命中 | 为什么是盲区 |
|---|---|
| 视频卡 播放/底部播放/取消静音 | 状态存在 store 不在 DOM（复刻的 mock 播放器没有 `<video>` 元素） |
| dock 小地图/显示连线/选择工具 | 改的是 class 与 minimap 挂载，第一版指纹没覆盖 |
| 「与 AI 对话」 | 开的是 AI 抽屉，第一版指纹没覆盖抽屉 |
| `header[canvas-top-bar]` 等容器 | 容器本身没有交互语义，点空白本就不该有反应 |

教训：**判据要比被测物的状态载体更宽**。第一版指纹只比 body 文案前 N 字，
结果时间码变了长度没变 → 漏判；后来补了媒体态、aria-label、URL、选中集合。

### 16.3 根因：这三个不是"打开浮层"，是"插入节点"

SOURCE_FACT（@1680×826 登录态，源站点这三个按钮后实测）：

```
落点  data-testid="rf__node-*"   role="group"   位于 .react-flow__viewport 内
顶栏  节点计数同步 +1
```

也就是说它们和「文本/图片/视频/音频」是**同一条路**：在画布中心插入对应节点。
复刻此前把 `RAIL_ITEMS` 里这三项的 `insert` 留空，`onClick` 走空分支 —— 点了没反应。

一开始的误判：以为它们是"打开侧边面板"，因为点击后确实出现了面板状内容。
是 `data-testid=rf__node-*` 和"顶栏计数 +1"两个证据把它钉成了节点。

节点实测尺寸：时间线 **1206×212** · 主体 **352×352** · 导演台 **320×320**。

### 16.4 实施

新增 `JimengTimelineNode` / `JimengSubjectNode` / `JimengDirectorNode`，
`nodeTypes` 注册，store 的 `addNodeAt` 扩三种 kind。三个节点里都是**真交互**：

| 节点 | 交互 |
|---|---|
| 时间线 | 「添加素材到时间线」塞片段 → 时码与刻度变化 + toast；片段可单独删除；删除钮删节点 |
| 主体 | 描述行可写回 store；四个入口各有不同后果（导入/本地真的进列表，画布/资产库给明确反馈而非静默） |
| 导演台 | 「进入导演台」切换节点内文案 + toast |

源站把「Empty subject: main missing…」「No resources: 0 ready…」放在 **sr-only**，
复刻照做，不做成可见状态行（与 batch 794 的资源计数处理一致）。

**返回首页**：源站是 `<a href="/ai-tool/home">`，复刻是**没有 onClick 的
`<button>`** —— 40 个可点元素里唯一点了什么都不发生的。改成 `<a href="/jimeng">`，
用普通锚点而非 `next/link`，保留 Cmd/Ctrl+点击开新标签、复制链接地址、
悬停显示目标 URL 这些链接才有的交互。

### 16.5 顺带修掉的可用性缺陷：节点叠成一坨

三个新节点都很大，且默认都落在视口中心。连点之后后一个会把前一个整个盖住 ——
「添加素材到时间线」按钮**在 DOM 里但点不到**。这是验证器自己撞出来的
（Playwright 报 `intercepts pointer events`），不是事后想出来的。

修法：当目标落点已被占用时按 (40, 32) 世界像素级联错位。依据是源站截图里
主体 1/2/3 落点互有偏移 (684,237)/(784,317)/(700,230)，并非精确重合。
步进最初取 (28,20)，对 320px 的节点等于没挪，验证器照旧失败，才加大到 (40,32)。

### 16.6 验收：36 项断言

`verify-jimeng-batch807.py`，按真实使用顺序「插一个就用一个」：
插时间线→加片段→插主体→填描述/导入→插导演台→进入。每插一个就断言节点数 +1、
节点布局尺寸、顶栏计数、节点内交互的真实后果。

踩坑两处：
- 量节点尺寸必须用 `offsetWidth/offsetHeight`（布局尺寸），`getBoundingClientRect`
  是屏幕像素、会被 zoom 0.7299 缩放，352 会量成 257。
- 断言「返回首页发生了导航」不能看 URL：`/jimeng` 会 302 回 demo 画布，
  最终 URL 与起点相同。改用 `framenavigated` 事件计数。

### 16.7 共享工作区事故（记录在案）

本批编号从 805 改到 806 再改到 807：写 `verify-jimeng-batch805.py` 时工具报
"overwrote existing file"，而 `docs/research/jimeng-canvas-batch805-2026-10-03/`
（内容是 handle / plus-left / video-selected，与本批无关）证明 805 已被并行会话占用。
**805 的脚本内容已被我覆盖且无法从 git 恢复**（该文件当时未入库）。806 又被
并行会话抢走（连接手柄批次）。最终让到 807。

### 16.8 普查收尾：真死按钮归零

修完之后重跑审计：**40 个可点元素，真死按钮 0**。

审计工具本身也迭代了三轮，每轮都在压误报（误报会让人不信任工具，工具一旦
不被信任就等于没有）：

| 轮次 | 误报数 | 改了什么 |
|---|---|---|
| v1 | 11 | — |
| v2 | 2 | 指纹补 `nodes`（节点类/class）、`tids`（挂载了什么）、`aria`（自身可访问名+class）；等待 220→420ms（AI 抽屉 220ms 时还没进 DOM） |
| v3 | 0 | 把 3 条**人工复核过**的放进 `UNVERIFIABLE`，每条附复核方法 |

v3 收进去的三条，都写明了"为什么探针够不着"而不是"猜它应该是活的"：
- **上传** —— 点了开系统文件选择器，无头环境无法完成选择，没有可观测后果
- **选择工具** —— 已是当前激活工具（点前 class 就带 `bg-white/10`），点它
  正确地什么都不该变
- **与 AI 对话** —— 活的；单独跑 wait=300ms 时 data-testid 集合变化。审计
  循环里报它是因为前一轮自己把 AI 抽屉打开了，抽屉 (x1268-1668) 正好盖住
  按钮 (x1549-1667)，后续点击打在抽屉上

最后一条是探针的**编排缺陷**而非判据缺陷：审计循环应该先把浮层关干净再点下一个，
或每轮重开页面。记在这里，别让它变成"工具说的"。

## 17. Batch 807-topleft — 顶栏左簇「项目名 / 节点 N / 分隔线 / 已保存」（2026-10-03）

> **编号说明**：同日并行 session 也提交了一个 `batch 807`
> （`ba2f5d9d feat: batch 807 jimeng —— 死按钮普查归零 + 左栏三工具接成真交互`，
> 含 `scripts/verify-jimeng-batch807.py`）。两批内容无关，为免混淆本批一律
> 带 `-topleft` 后缀：台账小节 17、verifier
> `scripts/verify-jimeng-batch807-topleft.py`、取证目录
> `jimeng-canvas-batch807-2026-10-03/`。这是本轮第四次撞号（详见 §16.6）。

### 17.1 选题方式：让像素指出下一个 batch

上一轮规划时留的候选清单（右簇 1px、生成素材栏…）已经过时——源站线上此后
动过好几次（这轮它显示「节点 10」，而复刻 demo 只有 2 个节点）。与其按旧
清单猜，不如把两侧同一状态的整屏截下来并排看，让**差异自己指出目标**。
`scripts/jimeng_sidebyside.py`：两侧同视口截图 → 裁出锚在视口边角的固定
条带（顶栏 y∈[0,64)、左栏 x∈[0,72)）→ 横向拼图 + 2× 放大 + 逐列亮度剖面
差异排名。顶栏 465 个显著差异位，放大后一眼看到：**复刻的「节点 2」折成了
两行**，而且中间少一根分隔线。

### 17.2 SOURCE_FACT（460×64 顶栏裁剪，DOM 探针 + 像素扫描）

| 元素 | 几何 | 排版 |
|---|---|---|
| `测试项目` | @[60,19] 52×22 | 13px/22px nowrap white |
| `节点` | @[156,21] **20×18** | 10px/18px nowrap white/60 |
| `10` | @[178,21] **10×18**（与前者间距 **2px**） | 10px/18px nowrap white/60 |
| 分隔线 | **1×8 @ x=196, y 26..34**，峰值灰度 35 | ≈ `rgba(255,255,255,0.09~0.1)` |
| `已保存` | 13px/22px white/40，第一笔墨迹起于 **x=205** | — |

源站另有一个视觉隐藏的 `1 nodes, 0 edges, 0 …` 读屏串（`@[-1,-1] 1×1`）。
另注：分隔线的垂直中心 y=30 与 13px 文字行（y 19..41）中心一致，是居中的。

### 17.3 修掉的三处偏差

1. **`节点 N` 折行**（本次主缺陷）。复刻把「节点 {n}」整串塞进 `size-7`
   （28px **定宽**）按钮且**没有 nowrap**：`节点 2` 恰好 28px 撑满就折行
   （截图里「节点」「2」上下两行），`节点 10`（32px）必然折。
   源站是**两个独立的 nowrap span**。改法：命中盒仍留 28×28（悬停底色要它），
   标签单独 `whitespace-nowrap` + `gap-[2px]` + 拆两 span，超宽时向两侧溢出。
2. **缺分隔线**。补 1×8 `bg-white/10`，落在「28×28 命中盒右缘 + 12px」——
   即 x=196，**与源站逐像素同位**。
3. **「已保存」左距** `ml-3`(12) → `ml-2`(8)，文字落到 x=204/205（源站墨迹
   起于 205，差 1px 在抗锯齿误差内）。

### 17.4 一个差点上当的「8px 偏移」

第一版比对把复刻的**按钮盒** x=52 和源站的 `<span>` x=60 相减，得出
「项目名左移 8px」。差点照着改。查下去发现复刻按钮带 `px-2`：文字起点
= 52+8 = **60**，与源站完全一致——又是 batch 796 那条「控件矩形 ≠ 容器
矩形」的坑，只是这次分处两侧。**已在 verifier 里写成断言**（项目名文字起点
相对左簇 = 48px = 40 logo + 8 padding），防下次再被同样的比法骗一遍。

### 17.5 验收

新增 `scripts/verify-jimeng-batch807-topleft.py`。断言写法上的两个要点：

- **断言「标签高度 ≤ 一个行高」而不是断言某行文本的 y 坐标**——折行时
  每行 y 依然正常，只有高度会暴露问题。这是批 798/807 两处折行缺陷的通用
  判据。
- 分隔线用**相对锚点**（节点块右缘 +12px、垂直居中于文字行、到「已保存」
  间距 8px），不写死 x=196——顶栏左缘会随 AI 抽屉开合平移。

**顺带修掉的连带失败**：`verify-jimeng-batch794.py` 的
`inner_text().replace(" ","") == "节点2"` 在拆成两个 span 后失效
（inner_text 变成 `节点\n2`）。已改为比**叶子 span 的文本 + 2px 间距 +
单行高度**，并顺带把 794 的断言数从 56 提到 58。

回归：794（58 项）/ 795 / 803 / 804 / 806-connecthandle / 98 / 105 /
807-topleft 全 PASS。

### 17.6 共享工作区归属：被裹入 + 第四次撞号

1. **本批的 TopBar 代码改动被并行 session 的提交裹走了**。对方用裸
   `git commit` 提交共享索引，把当时工作区里 `JimengTopBar.tsx` 的全部改动
   （我的分隔线 + 两 span 标签 + 对方的 logo 锚点）一起提交进
   `ba2f5d9d`。所以「分隔线 + 单行标签」这两处**已经在 HEAD 里**，归在
   对方提交名下；本批自己的提交只含后续微调（`gap-[2px]`）、verifier、
   探针、取证与台账。**内容没丢，但归属记错了地方**——这正是台账反复要求
   「提交后核对 `git show --stat`」的原因。
2. **第四次撞号**。我规划 807 时对方也在规划 807（§16.6 已记 804/805/806
   三次）。所幸本批起 verifier 文件名带主题后缀
   （`verify-jimeng-batch807-topleft.py`），**没有再覆盖任何文件**——
   主题后缀这条约定在本轮第一次真正救了场。

---

## 17. Batch 808 — 把普查扩到交互态，结果先撞上**判据**的问题

### 17.1 起因

batch 807 的普查只看**默认视图**。本批扩到交互态：选中节点 / AI 抽屉 /
画布右键菜单，逐态刷新后只审该态新增的可点元素。

### 17.2 第一个结论不是产品缺陷，是判据缺陷

右键菜单的**「粘贴 ⌘V」「重做 ⌘⇧Z」「撤销 ⌘Z」**被普查报成死按钮。
去看源站才发现同一批里也有"点了没反应"的控件：

```
<button aria-label="新建会话" data-testid="canvas-agent-session-create"
        aria-disabled="true" data-disabled="true" ...>
```

源站的「新建会话」**本来就是禁用的** —— 还没有会话可新建。复刻的
粘贴/重做/撤销同理：没有可粘贴内容、没有历史可撤销时，点了没反应是**对的**。

**「点了没反应」有两种成因：没接交互，和正确地禁用。前者要修，后者修了是 bug。**
判据不区分就会把「设计如此」报成缺陷，报告一旦失真就没人看。

处置：审计脚本过滤 `disabled` / `aria-disabled` / `data-disabled`。
过滤后误报从 8 降到 0 —— 也就是说本批**没有**新死按钮。

### 17.3 顺带查出的真缺口：AI 抽屉缺了源站的会话入口

SOURCE_FACT（@1680×826 登录态，aria/testid 逐个提取）：

| 控件 | 源站 | 复刻（本批之前） |
|---|---|---|
| 会话列表 | 58×32 @[1314,41] `canvas-agent-session-menu-trigger`（无会话时 disabled） | **只有一段纯文本「新会话」** |
| 新建会话 | 32×32 @[1599,41] `canvas-agent-session-create`（disabled） | 28×28，无 testid |
| 收起 | 36×36 @[1637,41] `canvas-agent-session-collapse` | 28×28，无 testid |
| 使用技能 | 90×32 @[1371,776] `canvas-agent-skill-trigger` | 86×28，无 testid |
| 从本地、画布或资产库添加 | 32×32 `canvas-agent-composer-add` | 32×32，无 testid |
| 引用参考 | 32×32 `canvas-agent-composer-mention` | 32×32，无 testid |
| 发送消息 | 32×32 `canvas-agent-send`（空输入时 disabled） | 32×32，无 testid |
| 占位符里的 @ | 24×24 @[1608,672] `canvas-agent-composer-placeholder-mention` | 内联 `<AtSign size={10}/>`，不是独立节点 |

补齐全部 testid 与尺寸；会话列表按源站做成 disabled 按钮（**不是**纯文本，
也不是随手做成可点的假按钮）。

### 17.4 一个真实的交互 bug：右键菜单「新建节点」点了像没反应

```jsx
onMouseEnter={() => setSubmenuOpen(true)}   // 移上来 → 子菜单开
onClick={() => setSubmenuOpen(v => !v)}     // 再点一下 → 子菜单关
```

指针移上来时子菜单已经开了，**再点一下反而把它关掉**。用户点「新建节点」
看起来毫无反应。改成只开不关（`onClick={() => setSubmenuOpen(true)}`），
关闭交给 `onMouseLeave`，与源站 hover 展开的行为一致。

这类 bug 普查**查不出来** —— 点它确实产生了状态变化（开→关），
只是变化的结果等于没做。只能靠读代码和"点了之后是否符合预期"发现。

### 17.5 关于"源站也没反应"的诚实记录

5 个技能 chip（`/ 视频反解` 等）、`引用参考`、`+`、`使用技能` 在源站登录态下
逐个点击，**同样没有可观测变化**。所以复刻保持 inert 才是对齐 ——
**不要"顺手接上"**，那是自作主张改产品。本批据此**没有**给它们加交互。

### 17.6 chip 宽度：差 2px 但不写死

源站 chip 105 / 105 / 157，复刻字体度量下 103 / 103 / 155。差的是字体，
不是布局。验证器只断言**高度精确 36** 和**宽度随文案单调增长**，
不断言绝对宽度 —— 与 batch 798 分享按钮同一个道理：把度量误差硬编码成契约，
等于把 bug 写成规范。

### 17.7 验收：29 项断言

`verify-jimeng-batch808.py`。踩坑：固定 `wait_for_timeout` 在 dev server
刚重编译时会踩空（本批连踩两次），一律改成 `wait_for_selector` 等真实信号。

### 17.8 共享工作区事故（记录在案）

两件事，都记下来：

1. **批次号再次撞车**。并行会话同时用了 807（`verify-jimeng-batch807-topleft.py`
   与 `docs/research/jimeng-canvas-batch807-2026-10-03/`）。本批的 807 当时
   **已经提交入库**，路径不同，**没有覆盖**，只是编号重复。本批让到 808。
2. **我的提交连带删了别人的文件**。`ba2f5d9d` 里出现了
   `scripts/frameos_deadstate_census.py | 135 ------` 的删除记录 ——
   我没用 `git rm`，也没把它加进 `git add`，是它在 commit 时**已经在 index 里
   处于暂存的删除态**，被 `git commit` 一起带走，远端也随之消失。
   已用 `git checkout ba2f5d9d^ -- <file>` 恢复 135 行原文件。
   教训：显式 `git add` 只控制"我要提交什么"，控制不了"index 里已经有什么"；
   提交前应当 `git diff --cached` 看一眼暂存区全貌。

### 17.9 顺带修掉的两处 807 回归

1. **807 的顶栏计数断言对空白过敏**。并行会话把节点摘要触发钮内部改成
   `<span>节点</span><span>N</span>` 两段（与源站 26×28 的两行折行一致），
   `inner_text()` 于是返回 `"节点\n3"`，807 断言 `"节点 3"` 连续挂 4 项。
   改成 `" ".join(raw.split())` 归一化 —— 要断言的是「节点 N」这个语义，
   不是它怎么折行、怎么排 span。
2. **「上传」不再是探针盲区**。指纹的 `layers` 选择器里含 `input`，点「上传」
   会让隐藏的文件 input 获得焦点 → `layers` 变化 → 判定为活。所以它从
   `UNVERIFIABLE` 里自然消失了，不需要人肉豁免。

回归：794(58) / 795(25) / 803(17) / 804(13) / 807(36) / 808(29) 全过，
`npm run check` EXIT=0，审计真死按钮 0。

## 18. Batch 808-rail — 左栏图标字形与 Beta 徽标（2026-10-03）

> **编号说明**：并行 session 当天也提交了 `batch 808`
> （左栏三工具接成真交互，`scripts/verify-jimeng-batch808.py`）。本批一律
> 带 `-rail` 后缀。§16.6 定的「verifier 文件名必须带主题后缀」这条约定
> 在本轮已连续两次避免覆盖（807-topleft / 808-rail）。

### 18.1 选题：并排图里剩下的那一列

`jimeng_sidebyside.py` 还产出了左栏并排图（`807-rail-sbs.png`）。九枚图标
里七枚一眼对得上（文本 T / 图片 / 视频 / 音频 / 主体 / 资产库 / 上传），
剩下两枚明显不是同一个字形：

| | 源站 | 复刻（改前） |
|---|---|---|
| 时间线 | **胶片格**（圆角外框 + 上下分隔带 + 上排 3 个齿孔） | `LayoutTemplate`：一个宽条 + 两个窄条 |
| 导演台 | **等轴测立方体** + 底部环绕箭头 | `Bot`：机器人头 |

顺带还看到 Beta 徽标的位置和形态也不对。

### 18.2 SOURCE_FACT

几何无需改动：源站 9 钮 @ x=16、40×40、步距 42px、导演台→资产库 56px，
与复刻逐项吻合（batch 796 契约，本批只当回归守住）。

1. **时间线 = 胶片格** ⇒ lucide `Film`（外框 rect + 两条竖分隔线 +
   一条横分隔线，横线以上被竖线切成 3 个齿孔格）。
2. **导演台 = 等轴测立方体 + 底部环绕箭头**。**源站这个图标不在 DOM 里**：
   按钮内只有一个空的 `<span class="contents">`（实测「文本 / 时间线 / 主体」
   三钮皆然），既不是 `<svg>`，也不是 background-image / mask。所以只能靠
   像素辨认，**弧段的曲率与箭头角度没有可量测的证据**。
3. **Beta 是胶囊，不是纯文字**。逐像素定位 **@[34,559] 23×14**；
   逐行扫描定圆角 ≈3px（y=559 那行只占 19px，y=561 起满宽 23px）；
   底色是**竖向渐变** rgb(29,46,57)→rgb(33,50,61)；
   文字 `#009EFA` 且**非斜体**（放大后源站的 B 是直的）。
   位置相对 40×40 按钮 = left 18 / top -1，即压在图标 20×20 的右上角。

### 18.3 实施

- `RAIL_ITEMS.icon` 类型从 `LucideIcon` 放宽为
  `ComponentType<{ size?: number }>`，让自定义组件能进这张表。
- 时间线 `LayoutTemplate` → `Film`。
- 新增 `DirectorGlyph`：lucide `Box` 的三条立方体路径包在
  `<g transform="translate(12 10) scale(.68) translate(-12 -12)">` 里，
  下方补一段自绘弧段 + 两端箭头。
  **踩到的坑**：第一版把平移写成 `translate(12 1.6)`，立方体缩放后顶边落到
  y=-4.5，直接被 viewBox 裁掉，渲染出来只剩一个小尖角。正确写法是**先定
  目标中心 (12,10) 再缩放**，缩放后立方体落在 y 3.9~16.8，正好给下方弧段
  （y 19~22）让位。这个坑写进了注释。
- Beta 徽标：`absolute left-[18px] top-[-1px] h-[14px] w-[23px]
  rounded-[3px]` + 渐变底 + 去掉 `italic`，并加 `data-testid` 便于断言。

### 18.4 已知残留（有意保留）

导演台的环绕箭头是**近似**：源站字形无法从 DOM 取得，没有曲率/角度证据。
20px 下笔画接近 1px，再细分也量不出来。已在文件头注释里写明「近似而非
逐像素复刻」，避免下次有人当成已对齐的事实。

### 18.5 验收

新增 `scripts/verify-jimeng-batch808-rail.py`：

- 时间线 icon 的可绘制子元素 **= 7**（`Film` 是 1 rect + 6 line；
  `LayoutTemplate` 是 3 rect）——比「像不像」更稳的特征
- 导演台 icon 里有 `<g>`（机器人头 `Bot` 是单层 path，不会有 `<g>`）
  且 path 数 ≥ 6
- Beta 胶囊 23×14、相对按钮 left 18 / top -1、`font-style: normal`、
  有圆角、`background-image` 含 gradient
- 顺带守住 batch 796 的几何（x=16、40×40）

徽标用**相对锚点**断言而不是绝对 y —— rail 整体随视口高度上下居中，
绝对坐标会漂。

回归：796 / 807（对方）/ 808（对方）/ 68 / 97 / 806-connecthandle /
807-topleft / 808-rail 全 PASS。

## 19. Batch 809-topright — 顶栏右簇药丸：描边占不占布局（2026-10-03）

**关闭台账待决问题 #4**（2026-10-01 挂起：「根因已定位，一行可修，等
`JimengTopBar.tsx` 空闲」）。等到了，但**原结论要改**：不是「分享药丸
padding 该从 4px 改成 5px」。

### 19.1 重测（两侧同 @1512 视口，同日）

顶栏自 10-01 起被 795/796/797/801/803/807 反复改动，旧数据已不可直接套用，
故整段重测。源站四枚 chrome 药丸：

| 药丸 | x | 宽 | padding | border |
|---|---|---|---|---|
| 搜索/生成历史 | 1139 | 68 | **3px** | **1px** `rgba(255,255,255,0.04)` |
| 分享 | 1215 | 70 | 4px | **1px** 同上 |
| 更多 | 1293 | 36 | **3px** | **1px** 同上 |
| 积分+用户菜单 | 1337 | 163 | 4px | **0** |

复刻（改前）四枚全是 `p-1` + **inset shadow**：
`1143/68`、`1219/68`、`1295/36`、`1339/161` ⇒ 漂移 **+4/+4/+4/+2/+2**。

### 19.2 真正的成因：描边占不占布局

源站的 chrome 药丸**分两种**：

- 前三枚那圈 1px 是**真 `border`** —— 每边吃掉 1px 布局；
- 积分药丸那圈 1px 是 **inset shadow** —— **不占布局**。

复刻把四种药丸统一用 inset shadow，于是**分享药丸凭空少了 2px**
（60 + 4 + 4 = 68，源站 60 + 4 + 1 + 4 + 1 = 70）。
右簇是右对齐的（用户菜单钮 @1468，两侧同位），一处窄 2px 就把它左侧的
东西整体右推 2px —— 这就是「越往左漂移越大」的机制。

旧结论「把 `p-1` 改成 `p-[5px]`」能达到同样的**外宽**，但会留下两处不对：
padding 变成 5px（源站是 4px + 1px border），且药丸仍然没有那圈边框。

### 19.3 实施

- `jimeng-canvas.css` 新增 `.jimeng-chrome-pill--bordered`：
  `border: 1px solid rgba(255,255,255,0.04)` + 摘掉 inset 环。
  默认 `.jimeng-chrome-pill` 保持 inset shadow（对应积分药丸）。
- 搜索/生成历史药丸、分享药丸、更多药丸挂 `--bordered`；
  其中搜索/生成历史与更多的 padding 由 `p-1`(4px) 收到 **`p-[3px]`** ——
  加了 1px 边框后要减 1px padding，宽度才不变（68 / 36）。
- 分享药丸保持 `p-1`：1+4+60+4+1 = 70 ✓。
- 顶栏文件头的右簇几何注释整段重写为实测值。

### 19.4 结果

三枚药丸宽度**逐个精确对上源站**（68 / 70 / 36），border 与 padding 分档
也对上。残余漂移变成**均匀 +2px**：

```
搜索 pill 1141 (源 1139)  分享 1217 (源 1215)
更多     1295 (源 1293)  积分 1339 (源 1337)  用户菜单 1468 (源 1468 ✓)
```

改前是 +4/+4/+4/+2/+2 的**梯度**（两个成因），改后是 +2 的**均匀偏移**
（单一成因：积分数值是 mock，积分药丸比源站窄 2px）。**这比「全部归零」
更有价值** —— 梯度意味着还有没查到的成因，均匀意味着成因已封死。

### 19.5 验收

新增 `scripts/verify-jimeng-batch809-topright.py`：

- 三枚带边框药丸：宽度 68/70/36 + padding 3/4/3 + `border-width: 1px`
- 积分药丸：`border-width: 0`（若误加边框会立刻失败）
- 相邻药丸间隙全 8px
- **漂移均匀性**：四枚药丸相对源站的 x 偏移必须彼此相等
- 右锚点：用户菜单 @1468

**刻意不断言「整体偏移 == 0」** —— 那会把 mock 积分数值变成 brittle 依赖；
积分药丸的宽度也**不**做绝对断言，同样因为它跟着 mock 走。

写这个 verifier 时自己踩了两个坑，都已修正：间隙公式方向写反
（`a.left - b.right` 应为 `b.left - a.right`）；以及差点把积分药丸的
mock 宽度当成「内容派生、不会漂」的值。

### 19.6 过程记录：dev server 反复重启

本批中途 dev server（4317）被并行 session 反复重启，一度出现
`/jimeng/canvas/demo` 返回 **404**、HMR websocket 被拒的半成品状态；
另有一次 `src/components/director/DirectorDesk.tsx` 写到一半导致
`tsc` 报 `TS17008 JSX element 'div' has no corresponding closing tag`。

处置：**都没有去动别人的文件**。`DirectorDesk.tsx` 那个错误在 ~50 秒后
对方自己写完即消失（`tsc` 恢复干净）；dev server 则改成「连续 3 次探测
返回 200 才开跑」的稳定窗口判据。中途我曾尝试自己起一个 dev server，
结果 EADDRINUSE 干净失败（对方已经占着端口），没有造成双实例、没有
污染共享的 `.next`。

### 19.7 顺带更新

顶栏文件头右簇注释（19.3 已述）。旧注释里的绝对 x（1388/1465/1509/1636）
是 @1680 视口下的值，本批统一改记 @1512 实测值。

回归：796 / 794 / 807(对方) / 808(对方) / 806-connecthandle /
807-topleft / 808-rail / 809-topright 全 PASS。

---

## 18. Batch 810 — 订正 batch 808 的一条错误结论：探针够不着 ≠ 控件没反应

### 18.1 808 记错了

§17.5 当时写的是：

> 5 个技能 chip、`引用参考`、`+`、`使用技能` 在源站登录态下逐个点击，
> **同样没有可观测变化**。所以复刻保持 inert 才是对齐 —— 不要"顺手接上"。

**这句话是错的。** 根因：源站的 composer 不是一个 `<input>`，而是

```
<div contenteditable aria-label="说说你的想法或任务，上传参考、输入文字或…" contenteditable=true>
```

而 808 的指纹只扫 `textarea, input:not([type=hidden])` —— **压根没扫到 composer**。
判据够不着，被我读成了"控件没反应"。

这是本项目第三次栽在同一个坑上（807 的误报、808 的 disabled、810 的 contenteditable）：
**"没检测到变化"有两种可能，控件没反应，或者探针够不着。不区分就会得出反向结论。**
后一种比没结论更糟 —— 它会让人拿"源站就是这样"当借口不去实现。

### 18.2 补上 `[contenteditable],[role=textbox],.ProseMirror` 后的源站实测

| 控件 | 源站行为 |
|---|---|
| 技能 chip | 把技能名**插入 composer**，渲染成 `node-composerChip` 富文本 token，发送钮转 ENABLED |
| 使用技能 | 弹「搜索技能」面板（占位「搜索技能」），每项「名称 + **官方** + 一句话长描述」 |
| 引用参考 @ | 弹「添加参考」面板，分类 tab：**主体 / 图片 / 视频 / 音频 / 文本** |
| + 添加 | 弹菜单：**上传 / 从资产库添加 / 从画布添加** |

实测到的完整文案只有「视频反解」一条（"拆解参考视频的镜头语言、光影色调与声音节奏，
一键生成可用于拉片复刻、元素替换和再创作的视频 Prompt，覆盖广告、MV、剧情片、
AI 视频、短视频、产品展示等多类"）。其余四条描述是 CLONE_DECISION，
代码里已逐条标注，别日后当实测值引用。

### 18.3 实施

`JimengAiDrawer` 加一套 composer 状态机：`panel`(skills/mention/add)、
`skillQuery`、`refKind`、`tokens`、`messages`。

- 技能 chip / 技能面板选项 → 追加 token，token 渲染在输入框上方，可单独移除
- 发送钮在 composer 非空时可用；点击发出用户消息 + mock Agent 回复，清空 composer
- **「会话列表 / 新建会话」随会话是否存在启用** —— 源站它们在还没有会话时是
  aria-disabled。这不是随手加的 disabled，是有状态依据的
- 「新建会话」清空消息/token，退回空态

### 18.4 第二个探针缺陷：状态是被点击销毁的

batch 809 的普查 v1 报节点右键菜单里「保存到主体库 / 下载 / 删除」三个死按钮。
去读代码发现三个都有 handler —— **全是假的**。

原因：右键菜单**一点就关**。"枚举一次元素列表，然后逐个点击"意味着
第 2 个元素往后，点击坐标全都落在已经关闭的菜单原来的位置，也就是画布上。
产出一片假死按钮。

`scripts/jimeng_state_audit.py` 因此重写为「**每个元素前重新载入页面并重新进入该状态**」。
顺带把 808 的 disabled 过滤也搬了进去。

两个探针缺陷的共同点：**都是把"我没能观测到"当成了"事实如此"**。

### 18.5 验收：39 项断言

`verify-jimeng-batch810.py`。踩坑：选择器 `agent-skill-panel` 少写一个 s
（真实 id 是 `agent-skills-panel`），前 21 项全过、第 22 项超时才暴露 ——
**选择器打错不会被静默跳过，它会超时**，这点比想象中好。

### 18.6 并行会话与 dev server

本批期间 dev server 反复 404/500：
- 一次是并行会话在途编辑在 `DirectorDesk.tsx` 留了未闭合的 `<div>`，整个构建挂掉。
  我准备做最小修复时，**文件已被他们自己改到行号都变了**，`tsc` 也已无错 ——
  于是**没有介入**，避免覆盖他们在途的编辑。
- 另一次是我的 dev server 随后台任务一起被杀。改为 `nohup … & disown` 后稳定。

`jimeng_state_audit.py` 里加了导航重试：dev server 会被并行会话反复重启，
一次跑不完整个普查是常态。

### 18.7 交互态普查完成：真死按钮 0

用修好的 `scripts/jimeng_state_audit.py`（每元素前重进状态 + 跳过 disabled
+ 导航重试）把三个交互态全部审完：

| 交互态 | 条目数 | 判为死 |
|---|---|---|
| 节点右键菜单 | 6 | **0** |
| 画布右键菜单 | 4 | **0** |
| AI 抽屉 | 9 | 8（**已由本批 810 全部修掉**） |

节点右键菜单这一轮是 809 v1 报「保存到主体库 / 下载 / 删除」三个死按钮的那个 ——
重跑后 **6 项全活**，再次确认那三个是探针假象，不是缺陷。

至此：默认视图（batch 807）+ 三个交互态（batch 810）普查完毕，
**jimeng 画布范围内真死按钮 0**。脚本里的 `STATES` 现在只剩待审项，
全部审完后清空即可 —— 这本身就是"已普查完"的标志。

## 20. Batch 810-dock — 底部 dock 三枚图标钮：圆角 8px + 选中底色 white/8（2026-10-03）

### 20.1 一个必须写下来的**假目标**

把 `jimeng_sidebyside.py` 的比对区扩到底部（左下 220×200）后，并排图上
复刻的 dock 左侧压着一个**大号「N」圆**，位置正好盖住「选择工具」按钮，
第一反应是「Agent 触发钮压住了 dock」。

**它不是产品缺陷。** 那是 Next.js **dev 模式的浮标**：挂在
`<nextjs-portal>` 的 **shadow root** 里，`document.querySelectorAll('*')`
根本扫不到（实测 shadowHosts = `[nextjs-portal, next-route-announcer]`，
而产品 DOM 里那个位置只有 `<button aria-label="选择工具">` @[16,902] 28×28）。
生产构建里不存在。

写进台账是因为这类东西**每轮截图都会出现**，不记下来下一批还会当成
新 bug 去"修"。verifier 里也留了一行检测：发现 `nextjs-portal` 时打印
提示而不是报错。

### 20.2 SOURCE_FACT（两侧同 @1512×950 视口重测）

dock 与四枚控件的位置**逐项一致**（batch 796 契约继续成立）：
`@[12,898] 164×36`；选择工具 `[16,902] 28×28`、小地图 `[48,902] 28×28`、
显示连线 `[80,902] 28×28`、Zoom `[124,903] 48×28`。

差异只在外观，两处：

| | 源站 | 复刻（改前） |
|---|---|---|
| 三枚 28×28 图标钮圆角 | **8px** | `rounded-md` = 6px |
| 选中 / hover 底色 | **rgba(255,255,255,0.08)** | `white/10` |
| Zoom 钮圆角 | 6px | 6px ✓（**不一起改**） |

### 20.3 实施

`JimengBottomDock.tsx`：三枚图标钮 `rounded-md` → `rounded-lg`，
`bg-white/10` / `hover:bg-white/10` → `bg-white/[0.08]`。
缩放钮**保持** `rounded-md` —— 源站实测它确实是 6px，和图标钮不同，
一起改成 8px 就错了。

### 20.4 验收

新增 `scripts/verify-jimeng-batch810-dock.py`：

- 四枚控件的绝对位置（batch 796 契约，防止本批改坏）
- 三枚图标钮 `border-radius == 8`（按 computed **像素值**判，不断言 class 名）
- 「选择工具」「显示连线」默认即选中态，底色 alpha ≈ 0.08
- Zoom 钮 `border-radius == 6`（**反向断言**，防止有人"顺手统一"）
- 检测到 `nextjs-portal` 时打印提示（见 20.1）

底色比较把 `rgba()` / `color(srgb …)` / `oklab()` / `oklch()` 四种记法
统一解析出 alpha 数值再比 —— 复刻用的是
`oklab(0.999994 0.0000455678 0.0000200868 / 0.1)`，直接字符串相等必假失败。

### 20.5 顺带修掉的取数 bug

`jimeng_sidebyside.py` 原来用模块顶上的视口常量（1680×826）算裁剪框，
而两侧页面实际渲染成 **1512×950**。于是 "dock" 那条带子裁到了画布中部的
**点阵**上，diff 报告里出现 100 个"显著差异"，全是网格点。已改为按真实
图片尺寸取区域，并打印实际页面尺寸。

这类错误和 batch 796/807 的教训是同一条：**比之前先确认两边坐标系一致**。

回归：796 / 93 / 806-connecthandle / 807-topleft / 808-rail /
809-topright / 810-dock 全 PASS。
