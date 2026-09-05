# LibTV Live Audit — 2026-09-05

> 状态:`READ_ONLY_AUDIT`(仅观察,无 graph mutation、无输入提交、无新建画布/节点)。
>
> 采样环境:登录态,内嵌浏览器,viewport `1440x900`,macOS。
> 采样项目:共享项目「未命名工作区 / 画布 1」(`?spaceId=7546884&projectId=874d99b76f434c16ae0c2183454370ca`),**空画布**。
>
> 与 [`liblib-live-2026-08-25/`](../liblib-live-2026-08-25/README.md) 的关系:上一轮基线以 10 节点 demo 项目为主;本轮是**空画布项目**的 shell/入口审计,记录 2026-08-29(Batch 96)之后可复核的新表面。两轮项目状态不同,节点级对比不在本轮范围内。

## 证据标签

| 标签 | 含义 |
|---|---|
| `SOURCE_FACT` | 本轮 DOM / computed style / 截图直接观察 |
| `INFERENCE` | 由观察推导的解释,未逐项验证 |
| `CLONE_GAP` | 与当前 clone 基线(Batch 96 后)对比的差异判断 |
| `SOURCE_UNKNOWN` | 本轮未采样,需要后续 fixture/授权 |

## 1. 画布 shell(工作流模式,空画布)

`SOURCE_FACT`(`original-canvas-empty-workflow-1440x900.png`):

- 顶栏左:logo 下拉、可编辑「项目名称」textbox(值=未命名工作区)、「画布 1」按钮、两个 icon 按钮(整理/布局,32x32,位于 `x≈265/297`)。
- 顶栏右:分享入口、「开通会员 限时 45 折」、积分「100」、avatar、「打开 Agent」按钮(`87x32 @ x=1337`)。
- 底部中央工具条 8 项:添加节点 / 移动 / 打开工具箱 / 素材库 / 角色库 / 生成历史 / 快捷键 / 教程;主按钮「添加节点」`32x32 @ (560,848)`。
- 底部左侧控制组:资产管理(文字按钮)、整理画布 `Option+Shift+F`、切换小地图、隐藏节点连线、网格吸附、缩放选项(100%)。
- 空画布中央提示「双击画布 自由生成节点」,下方一排 4 个快捷芯片:
  - 故事脚本生成
  - 角色三视图
  - 全能参考生视频(`SD 2.5` 角标)
  - 音频生视频(`SD 2.5` 角标)

`CLONE_GAP`:「音频生视频」是 clone 完全没有的能力入口;4 个空画布快捷芯片与「双击画布」空态提示未建模(clone 仅 boot demo 项目,无空画布状态)。

## 2. 协作跟随状态条(新)

`SOURCE_FACT`:DOM 存在 `fixed left-1/2 top-0 z-[305]` 容器(`opacity:0` 淡出态),内含「正在跟随」文本、`取消 ESC` 按钮、`按 ESC 退出` tooltip。容器 class 含 `motion-safe:transition-opacity motion-safe:duration-20`,子元素为 `rounded-b-xl border px-3 py-1.5 shadow-md`。

`INFERENCE`:这是**实时协作跟随模式**(跟随其他成员视口)的顶部落出横幅,跟随中显示、超时/退出淡出。本轮无第二成员在线,未能采样可见态。

`CLONE_GAP`:clone 无任何协作/跟随建模。

## 3. 添加节点面板

`SOURCE_FACT`(`original-add-node-panel.png`,面板 `196x481 @ (477,350)`,fixed `z-(--z-panel)`):

- 头部「添加节点」+ 搜索(placeholder 搜索画布节点)。
- 节点区 9 项:文本 / 图片 / 视频 / 智能剪辑(`Beta`)/ **导演台(`NEW` 角标)** / 逐帧拉片(`SD 2.5` 角标)/ 音频 / 脚本(子菜单箭头)/ 素材库(子菜单箭头)。
- **「添加资源」分区(新)**:上传 / 从生成历史选择。

脚本子菜单(`original-add-panel-script-flyout.png`):**脚本(`NEW`)** 与 **脚本(旧版)(`Beta`)** 并存——原站正在以新脚本节点替换旧剧本文本节点,旧入口保留。素材库子菜单:风格库 / 特效库(与 clone 现有记录一致)。

`CLONE_GAP`:clone AddNodePanel 无「添加资源」分区;导演台无 `NEW` 角标;逐帧拉片无 `SD 2.5` 角标;脚本无双入口(新脚本节点能力未研究,`SOURCE_UNKNOWN`)。

## 4. 画布切换下拉

`SOURCE_FACT`(`original-canvas-dropdown.png`):「画布 1」按钮点击后展开自绘菜单(无 ARIA 角色,ARIA 快照不可见),内容为「画布 +」头部行与「画布 1 ✓」当前项。菜单约 `210x80`,锚定按钮下方。

`INFERENCE`:`+` 为新建画布(本轮未点击,避免项目 mutation)。菜单结构与 clone 的 CanvasTabDropdown(编辑草稿 + 行级更多菜单)存在差异,需后续在多画布项目里复核(`SOURCE_UNKNOWN`)。

## 5. 故事板模式 + Agent 抽屉

`SOURCE_FACT`(`original-storyboard-mode-agent.png`):

- 顶栏「工作流 / 故事板」为 `aria-pressed` 双态按钮;切到故事板后 Agent 抽屉自动打开,顶部「打开 Agent」按钮消失(drawer 打开时顶栏避让)。
- 故事板面板分**文本 / 图片 / 视频**三组 banner,空态为「暂无文本 / 暂无图片 / 暂无视频」;图片、视频组带「放大图片 / 放大视频」按钮。

Agent 抽屉(`original-agent-drawer-workflow.png`)为 dialog 形态:

- 头部:新对话 / 历史对话 / 分享(新对话时 disabled,文案「新对话无法分享」)/ Agent 设置 / **CLI & Skill** / 关闭;下沿有「调整 AI 助手面板宽度」separator(可拖宽)。
- Skill 推荐区:「选一个 Skill,让创作更快一步」+ 换一批,4 张卡片带 handle:皮克斯动画广告 `/pixar-animated-ad-creator`、爆款拉片复刻 `/viral-video-replicator`、新中式美学TVC `/neo-chinese-aesthetic-tvc`、古典武侠电影全流程导演 `/hujinquanwuxia`。
- composer:placeholder「开始你的创作,或者 @ 引用工作流/节点/资源」,底部控件:添加附件 / **选择模型** / Skill / **生成模式** / Send(disabled)。

`CLONE_GAP`:clone Agent 抽屉无 选择模型 / 生成模式 / CLI & Skill;Skill 推荐名称与 handle 是旧集合;故事板空态分组为「文本/图片/视频」三组(clone 现为关键元素栏 + 图片/视频列,需复核)。

### 5.1 选择模型菜单(新)

`SOURCE_FACT`(补采样 2026-09-05:菜单为**单滚动列表内「图片 / 视频」两个分区**,tabs 为分区锚点;列表可滚动,已滚到底确认完整目录;`original-agent-model-menu-image.png` / `-video.png` 为首屏局部):

- 图片分区(7 项,均无 premium 角标):
  - `Lib Image` — 最新图片模型,长文本能力突出
  - `General image Pro` — 最强图片编辑模型,一致性好
  - `General image V2` — 支持联网搜索、文字准确、速度更快
  - `Seedream 5.0 Pro` — 精准交互式编辑,支持原生多语言排版
  - `Style Image V8.2` — 电影感全面升级,精准还原光影、人物与真实材质
  - `Style Image V8.1` — 生图更连贯、细节更丰富、美学水准大幅提升
  - `Style Image V7` — 最佳美学、电影质感、创意能力强
- 视频分区(8 项;💎 为 premium 角标):
  - `Seedance 2.5` 💎 — 最强视频模型,全能参考,30s音画同步
  - `Seedance 2.0 VIP` 💎 — 最强视频模型,会员专属通道,15s音画同步
  - `Minimax H3` 💎 — 全模态输入,多参数控制,多场景商用级生成
  - `Seedance 2.0 Fast VIP` 💎 — 最强视频模型极速快速版,会员专属通道,15s音画同步
  - `Wan 3.0 Prime` — 超快生成,全模态参考,超写实高一致性
  - `Wan 3.0` — 全模态参考,支持文档与网页输入,超写实高一致性生成
  - `Kling O3` 💎 — 视频编辑模型、参考一致性、首尾同出、多镜头
  - `Kling 3.0` 💎 — 视频生成模型,高质感、支持多镜头
- 每项右侧有 `+` 按钮;菜单标题「选择模型」。

### 5.2 生成模式菜单(新)

`SOURCE_FACT`(`original-agent-generation-mode.png`):手动模式(Agent 在每次生成前询问)/ 自动模式(Agent 完全自动生成,默认勾选)。

## 6. 生成历史(模态)

`SOURCE_FACT`(`original-generation-history-modal.png`):大模态(带背景模糊遮罩),头部「生成历史」+ 缩略图尺寸 slider + 关闭;筛选行:「本画布」chip(选中)、图片 `0`、视频 `0`、**音频 `0`**;右侧:所有评级 下拉、时间倒序、批量操作;空态「暂无历史记录」。

`CLONE_GAP`:clone 生成历史无 音频 分类、无评级/排序/批量操作、非模态形态。

## 7. 资产管理(左抽屉)

`SOURCE_FACT`(`original-asset-drawer-left.png`):左抽屉与右 Agent 抽屉**可同时打开**;内容为 dialog:项目名称 textbox、画布 1 按钮、**画布 / 资产** 双 tab、搜索节点、筛选:全部、**所有评级**、**展示设置**;空态「画布暂无节点」;底部「共 0 节点」+ 收起节点侧栏。打开时画布区右移,底部画布控制组避让。

`CLONE_GAP`:clone 资产抽屉无 画布/资产 双 tab、无 所有评级/展示设置;「共 N 节点」计数未建模。

## 8. 我的工具箱

`SOURCE_FACT`(`original-toolbox-presets.png`):底部「打开工具箱」弹出「我的工具箱」浮层(带 `?` 帮助与关闭),2 列以上【预设】卡片网格:左弧滑行 / 电商手机弹出效果 / 咖啡杯出场 / 360旋转展示 / 机械臂视角 / Live 2D 等(可滚动,完整集合未采样)。

`INFERENCE`:预设是命名运镜/运效模板,点击预期生成对应节点或运镜(`SOURCE_UNKNOWN`,未点击)。

## 9. 快捷键弹窗(全量)

`SOURCE_FACT`(`original-shortcuts-dialog.png`,4 栏,标题栏有「关闭快捷键面板」):

- 创作:成组 `⌘ G`;合并分镜组 `⌘ ⌥ G`;解组 `⌘ ⇧ G`;连线 `⌘ L`;复制节点和连线 `⌘ D`;生成 `⌘ Enter`;新建节点 `Tab`;节点复制 `Option + 拖动节点`;创建副本 `⌘ Option + 拖动`。
- 缩放:放大 `⌘ +`;缩小 `⌘ −`;适应画布 `⌘ 0`;触控板(手势图);鼠标 `⌘ 滚轮`。
- 移动画布:键盘 `Space`;触控板;鼠标(中键);移动 `V`;抓手工具 `H`;整理画布 `⌥ ⇧ F`。
- 其他:撤销 `⌘ Z`;重做 `⌘ ⇧ Z`;**画布节点搜索 `⌘ F`**;删除。

`CLONE_GAP`:`合并分镜组`、`连线 ⌘L`、`生成 ⌘Enter`、`Tab 新建节点`、`⌘F 画布节点搜索`、`⌘D 复制节点和连线` 与 clone 键位表需要逐项 crosswalk(见 [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](../LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md));clone 帮助面板内容预计已漂移。

## 10. 发布与分享

`SOURCE_FACT`(`original-publish-share.png`):顶栏 popover 两项:在LibTV上发布(发布你的作品和创作过程,让更多创作者看到。)/ 分享链接(拥有此链接的人可以查看并复制你的画布。)。与 clone Batch 14 记录一致,未发现漂移。

## 11. 交互环境备注(研究方法)

`SOURCE_FACT`:该站点在自动化下不稳定——多次交互后 guest 页面整体卸载为 `about:blank`(本轮发生 3 次,重载即恢复);Playwright locator click 的 actionability 探针经常取不到点击点(CUA 坐标点击可用);添加面板对本轮的 Escape / 外点关闭均无响应(可能是面板自身行为,也可能与自动化事件派发有关,`SOURCE_UNKNOWN`);画布下拉、Agent 选择模型/生成模式等弹层为自绘组件,不进 ARIA 快照,必须截图读取。

## 12. 未采样 / 后续队列

- 空画布 4 个快捷芯片的点击流(会创建节点,需可丢弃 fixture 授权);
- 新「脚本」节点与「脚本(旧版)」的能力差异;
- 导演台在空项目中的入口行为(带 `NEW` 角标);
- 多画布项目的画布下拉完整结构、重命名/删除入口;
- ~~素材库/角色库本轮未重新打开~~ **2026-09-05 补采样已复核**(见 §13);
- 跟随模式可见态、Agent 对话运行态、生成历史非空态;
- demo 10 节点项目与 2026-08-25 基线的节点级 diff。

## 13. 补采样（2026-09-05 晚间,只读）

`SOURCE_FACT`(`original-project-menu.png` / `original-material-flyout.png` / `original-character-library-modal.png`):

- **logo 项目菜单**:回到主页 / 全部项目 /(分隔线)创建新项目 / 删除项目;Escape 不关闭(观察)。已由 Batch 106 对齐(clone 各项为本地 status)。
- **素材库工具条 flyout**:素材库标题 + 风格库(`NEW`)/ 特效库(`NEW`)。clone MaterialLibraryPanel 两行条目与 NEW 角标一致,无漂移。
- **角色库模态**:详情区(甜妹/清新少女 + 标签 女主/现代/青年/温柔 + 四张预览图 + 说明文案 + `应用至画布`)+ 底部 角色筛选 / 最近使用 / 横向角色条(甜妹、霸总、温柔熟男、清冷千金、古风男主/女主、恶毒女配、正派长辈父/母、反派长辈…)。clone CharacterLibraryPanel 名单与结构一致,无漂移;详情区标签/说明文案的 clone 覆盖度待后续批次核对。
- **角色筛选面板**（补采样）：`清空筛选` + 分组芯片 `性别（男/女/中性）、年龄段（儿童/少年/青年/中年/老年）、种族（人类/精灵/兽人/机械/其他）、时代（先秦/古代/近代/现代/未来）、文化区域（选项被卡片条遮挡,选项 SOURCE_UNKNOWN）`;面板向上展开。已由 Batch 112 对齐(clone 过滤语义为 CLONE_DECISION)。
- **Agent Skill 标题第三变体**:「一个 Skill,慢慢打磨你的故事」再次观察到,已由 Batch 107 建模为轮换。

## 截图索引

viewport `1440x900`,除注明外为全屏截图:

| 文件 | 状态 |
|---|---|
| `original-canvas-empty-workflow-1440x900.png` | 工作流空画布首屏 |
| `original-add-node-panel.png` | 添加节点面板展开 |
| `original-add-panel-script-flyout.png` | 脚本子菜单展开 |
| `original-canvas-dropdown.png` | 画布下拉(左上局部) |
| `original-storyboard-mode-agent.png` | 故事板模式 + Agent 抽屉 |
| `original-agent-drawer-workflow.png` | 工作流模式 Agent 抽屉(重载后保持打开) |
| `original-agent-model-menu-image.png` | Agent 选择模型·图片(局部) |
| `original-agent-model-menu-video.png` | Agent 选择模型·视频(局部) |
| `original-agent-generation-mode.png` | Agent 生成模式菜单(局部) |
| `original-generation-history-modal.png` | 生成历史模态 |
| `original-asset-drawer-left.png` | 资产管理左抽屉 + Agent 双开 |
| `original-toolbox-presets.png` | 我的工具箱预设 |
| `original-shortcuts-dialog.png` | 快捷键弹窗 |
| `original-publish-share.png` | 发布与分享 popover |
| `original-project-menu.png` | logo 项目菜单(补采样) |
| `original-material-flyout.png` | 素材库 flyout(补采样) |
| `original-character-library-modal.png` | 角色库模态(补采样) |
| `original-character-filter-panel.png` | 角色筛选面板(补采样) |
