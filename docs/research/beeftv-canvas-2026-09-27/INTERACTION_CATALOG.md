# BeefTV 交互目录（INTERACTION_CATALOG）

> 锁定提交 `85c9686`（v1.5.7）。每项：触发 → 行为 → 证据（file:line，路径相对 `web/src/`）→ 对 clone 的相关性。
> 相关性分级：`对照`（与本 clone 语义互为样本）/ `候选`（可评估吸收，需走 Par/verifier 流程）/ `无关`。

## 1. 视口手势

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| 鼠标滚轮 | 以鼠标为锚缩放，`factor=1.1^(-deltaY/72)`，范围 0.05–2 | `components/canvas/infinite-canvas.tsx:214-228,493-495` | 对照（与 LibTV 源站 wheel 语义需按 `CANVAS_NAVIGATION.md` 权威，不受此影响） |
| 触控板双指滚动 / Shift+滚轮 | 平移（按 delta 整除性区分鼠标滚轮） | `infinite-canvas.tsx:201-212` | 对照 |
| Ctrl/Cmd+滚轮（捏合） | 缩放，delta 档位 24（触控板）vs 72（鼠标）；浮层区域也被画布接管 | `infinite-canvas.tsx:189,196-197,218` | 对照 |
| 中键拖空白 | 平移 | `lib/canvas/canvas-selection.ts:28` | 对照 |
| Space 按住+拖 | 平移（Space 仅修饰平移，输入元素不生效） | `infinite-canvas.tsx:151-180`、`canvas-selection.ts:30` | 对照 |
| 触控板单指拖背景 | 平移 | `infinite-canvas.tsx:283-300` | 对照 |
| 双指 pinch | 以两指中点为锚缩放 | `infinite-canvas.tsx:259-281,326-345` | 对照 |
| 双击空白 | 打开画布右键菜单并展开「添加节点」子菜单；同时清空当前节点/连线选择与打开的面板 | `use-canvas-viewport-controller.ts:119-127`、`canvas-context-menu.tsx:150-153`（v21 复核补充） | 候选（对照 LibTV「双击打开添加节点面板」batch115） |
| 滚轮/平移停止后 120ms | 才提交 React state（交互期只写 DOM） | `infinite-canvas.tsx:140-146` | 对照（性能方法） |

## 2. 工具模式

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| `V` | 切到框选工具（**默认工具**，空白左键拖=框选） | `canvas-toolbar.tsx:153-166`、`project.tsx:362,3066` | 对照（LibTV 源站是 Shift+drag marquee、blank-drag no-op） |
| `H` | 切到抓手工具（拖动=平移） | `canvas-toolbar.tsx:153-166` | 对照 |
| `?` | 打开快捷键中心 | `use-canvas-keyboard.ts:145-149` | 候选（clone 已有快捷键帮助面板） |
| `Ctrl/Cmd+F`（+Shift） | 节点搜索 modal；+Shift 进入/退出专注模式 | `use-canvas-keyboard.ts:121-130` | 候选 |

注意：`lib/canvas/canvas-shortcuts.ts:117-123` 的文案与代码相反（文案说「按 V 切换到移动工具」），以代码为准（源码事实，已是上游自身文案 bug）。

## 3. 选择与拖拽

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| 点击节点 | 清空后单选；松手未移动且单选→打开面板 | `use-canvas-selection-controller.ts:159-181,269-272` | 对照 |
| Shift/Ctrl/Meta+点击 | toggle 加减选；Alt+点击=减选 | `canvas-selection-controller.ts:169-177` | 对照 |
| 框选（默认工具拖空白） | 策略：默认 replace、Shift=add、Ctrl=toggle、Alt=subtract；阈值 4/k；hitMode 恒 intersect | `canvas-selection.ts:63-72`、`canvas-selection-controller.ts:138-157,307` | 对照 |
| 框选预览 | 完全绕过 React 直写 DOM，pointer-up 才进 state | `canvas-selection-controller.ts:313-333` | 对照（性能方法） |
| 拖动节点 | rAF 节流；智能对齐 7/k、网格吸附 16px；拖拽期间暂停历史记录 | `canvas-selection-controller.ts:239-290,214` | 对照 |
| 拖动集合 | 自动带上 batch 子节点与 frame 子节点 | `canvas-selection-controller.ts:197-206` | 候选（分组联动语义） |
| 拖到素材库文件夹 | 只归档不变更子节点 | `canvas-selection-controller.ts:259-262` | 无关 |
| 触控轻点背景 | 清空选择 | `infinite-canvas.tsx:381-383` | 对照 |
| `Ctrl/Cmd+A` | 全选节点 | `use-canvas-keyboard.ts:168-175` | 对照 |
| `Esc` | 取消选择/关浮层；专注模式下退出 | `use-canvas-keyboard.ts:208-221` | 对照 |

## 4. 连线交互

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| hover/选中节点边缘 | 出现左右「+」侧栏轨道（80px 圆形热区）；script/batch-table 无输入侧，script/config 无输出侧 | `canvas-node.tsx:583-584,859-949` | 对照（LibTV 源站 `+` Handle 是权威形态） |
| 从 rail 拖出 | 进入连线预览（rAF 每帧）；预览=三次贝塞尔 | `use-canvas-connection-controller.ts:686-716,783-789`、`canvas-connections.tsx:161-173` | 对照 |
| 拖近目标节点 | 56px 屏幕像素圆形吸附（除以 k）；命中但策略不过=靠近不吸附；目标节点 3D tilt 反馈（进入点 latch） | `use-canvas-connection-controller.ts:61,458-497`、`canvas-connection-tilt.ts:6-18` | 对照 |
| 松手在合法目标 | 建线（方向归一化：Config 恒为 target、同端点重复只更新 anchorRatio） | `use-canvas-connection-controller.ts:607-684,264-266` | 对照 |
| **松手在空白** | 弹「引用该节点生成」快速创建菜单（位置按源节点锚点 Y 排布） | `use-canvas-connection-controller.ts:678-683,274-437` | **候选**（同 TDCanvas TD-03；走 Par/verifier） |
| **点 pin（位移≤5px）** | 不画线，直接弹快速创建菜单 | `use-canvas-connection-controller.ts:818-827` | **候选** |
| 拖线到提示词面板参考 chip | 换参考（elementFromPoint DOM 命中，就近 chip） | `use-canvas-connection-controller.ts:618-667` | 对照（LibTV 引用槽有自己的交互） |
| 多选 ≥2 后 `Alt+L` / 从选区 pin 拖出 | 批量连线：规划 valid/partial/invalid，commit 汇总跳过数 | `use-canvas-keyboard.ts:140-144`、`use-canvas-connection-controller.ts:216-245,540-556` | 对照 |
| 点击连线 | 选中（16px 透明命中 stroke） | `canvas-connections.tsx:73-93` | 对照 |
| 右键连线 | 菜单仅「删除连接」 | `canvas-context-menu.tsx:289-293` | 对照 |
| `Delete`（连线选中时） | **优先删选中连线**（防止误删节点） | `use-canvas-keyboard.ts:193-207` | **候选**（语义歧义消解，可吸收进 clone 快捷键合同） |
| 拖既有连线端点 | 不支持重连（改接=删旧建新或换参考） | 全仓无 reconnect 实现（静态复核） | 对照 |

## 5. 节点生命周期

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| 创建入口（5 处） | 空白右键→添加节点 / 双击空白 / 底部工具栏添加面板 / 连线快速创建菜单 / `Ctrl/Cmd+F` 搜索 modal | `canvas-context-menu.tsx:320-399`、`canvas-toolbar.tsx`、`canvas-workspace-overlays.tsx:161-235`、`canvas-node-search-modal.tsx` | 对照 |
| 创建菜单布局 | grid（底部面板）与 list（右键子菜单，带搜索）；list 默认隐藏绘图/文件夹/批量表三个高级项，搜索可见 | `canvas-create-menu.tsx:20-105`（注释「隐藏不删能力」:29-37） | 候选 |
| 重命名 | 节点外置标题头：点击标题（hover 铅笔）进入 input；frame/folder 双击标题；空值回滚 | `canvas-node.tsx:710-806,288-296`、`canvas-frame-node.tsx:260-268` | 对照（BeefTV 约定：铅笔入口必须可发现，`AGENTS.md` §6） |
| 复制/粘贴/副本 | `Ctrl/Cmd+C/V`（画布文本选区让位；keydown 兜底浏览器不发 paste）；`Ctrl/Cmd+D` 创建参数变体 | `use-canvas-keyboard.ts:176-192,224-236`、`canvas-context-menu.tsx:281-287` | 对照 |
| 删除 | Delete/Backspace：先连线后节点；阻止 Backspace 浏览器后退 | `use-canvas-keyboard.ts:193-207` | **候选** |
| 调整尺寸 | 四角手柄（偏移 14px、热区 28px）；媒体默认锁比例；`freeResize` 解锁 | `canvas-node.tsx:575-580,213-254` | 对照 |
| 图片自适应 | 解码后 fitNodeSize 夹 [420×236, 720×520]；`manualSize` 用户手动定过则让位 | `canvas-node-size.ts:4-15`、`canvas-node-content.tsx:660-683` | 对照 |
| 锁定 | 锁定节点只响应 click；锁定节点不动几何（生成回填时） | `canvas-selection-controller.ts:190-195`、`canvas-generation-task-sync.ts:190` | 对照 |
| frame/folder | 拖节点进 frame 几何判定→显式 parentId；折叠隐藏子节点+连线改道；folder 折叠=封面卡 | `canvas-frame.ts:31-33,79-92,138-184` | 对照（显式成员 vs LibTV 几何分组对照样本） |
| 双击节点 | 分发：批次根开合/图片看大图/director/绘图/文本编辑 | `canvas-node.tsx:390-419` | 对照 |

## 6. 右键菜单（单组件按 type 四分支）

| type | 项目 | 证据 |
|---|---|---|
| 画布空白 | 自适应整理画布（多选时）/ 添加节点（子菜单）/ 上传到这里 / 从素材库插入 / 撤销 / 重做 / 粘贴 | `canvas-context-menu.tsx:204-221` |
| 节点多选 | 整理画布 / 复制 N 个节点 / 发送到 Agent / 删除 N 个节点（danger） | `canvas-context-menu.tsx:222-231` |
| 节点单选（角色卡） | 查看角色详情 / 发送到 Agent / 复制引用 / 创建引用副本 / 删除 | `canvas-context-menu.tsx:234-245` |
| 节点单选（媒体） | 全景预览 / 资产分类（二级页）/ 复制节点 | `canvas-context-menu.tsx:246-261` |
| 节点单选（其他） | 保存到我的素材 / 放大编辑(文本) / 打开绘图 / 用文本生图 / 发送到 Agent / 复制 / 创建参数变体(⌘D) / 粘贴 / 删除；Frame/文件夹=折叠展开+复制及内容 | `canvas-context-menu.tsx:262-288` |
| 连线 | 删除连接 | `canvas-context-menu.tsx:289-293` |

菜单位置统一避让 Agent 面板与视口边缘（:491-508）；自制浮层自管 Esc 与外点关闭（:131-148）。相关性：对照。

## 7. 生成工作流交互

| 交互 | 行为 | 证据 | 相关性 |
|---|---|---|---|
| 上游连线 | 上游资源自动成为生成参考；上游文本自动拼 prompt；连线顺序=引用编号 | `canvas-node-generation.ts:59-137`、`canvas-resource-references.ts:429-433` | 对照（LibTV AutoLink/引用槽对照样本） |
| `@mention` | 提示词 `@图片1/@[node:xxx]` 命中→composer 模式（只按 mention 取素材）；不可解析直接报错 | `canvas-node-generation.ts:84-101` | 对照 |
| 提交 | 节点级互斥锁；同指纹再提交弹「可能再次消耗积分」确认 | `canvas-generation-submission.ts:37-87`、`use-canvas-generation-executor.ts:84-98` | **候选**（对照 VR-007） |
| 进行中 | 徽章+spinner+阶段文案+已耗时；图片占位按请求比例预创建 | `canvas-node.tsx:817-853`、`canvas-node-content.tsx:197-205` | 对照 |
| 结果回填 | 媒体就地替换+几何居中调整；文本多余份数右侧兄弟阵列；图片 count>1=root+N 子节点；视频再生成入版本族 | `canvas-generation-task-sync.ts:151-242`、`canvas-text-generation-executor.ts:36-58`、`canvas-image-generation-executor.ts:81-83` | 对照 |
| 失败 | 旧结果不清空；审核类失败（输入未变指纹）阻止自动重试；524 提交不确定相位 | `canvas-generation-failure.ts:26-59` | **候选** |
| 重试 | 从 generatedFromNodeId 重建上下文；引用丢失拒绝；retry clientOperationId 哈希幂等 | `use-canvas-generation-retry.ts:83-89,176-201,414-416` | **候选** |
| 刷新恢复 | 按 taskId 对账任务列表；孤立 loading 标记本地中断 | `use-canvas-generation.ts:384-546` | **候选**（对照 VR-007/VR-015） |
| 撤销 | 画布撤销不取消已提交任务（批准警告文案明示） | `canvas-operation-contract.ts:305` | 对照 |

## 8. 周边表面

| 表面 | 要点 | 证据 | 相关性 |
|---|---|---|---|
| 顶栏 | 保存/导入 LibTV/TapNow 入口/短剧导引/版本记录/`?libtvChrome` 品牌化与只读复刻条 | `canvas-project-top-bar.tsx:42-43,101-157,351` | 无关（`?libtvChrome` 三件套见 PATTERN_CARDS BF-37） |
| 底部工具栏 | 添加面板（grid）、V/H 工具切换 | `canvas-toolbar.tsx` | 对照 |
| 选区浮动工具栏 | 随视口 MutationObserver 重定位 | `canvas-workspace-overlays.tsx:21-80` | 候选 |
| 小地图 | 纯 DOM、按需挂载、拖地图 preview/commit 两段 | `canvas-mini-map.tsx` | 候选 |
| 节点工具栏 | 选中节点上方动作条，定位避开 Agent 面板；工具项 tool-registry 解析（applicable 过滤+用户偏好排序） | `canvas-node-toolbar.tsx:139-213`、`tool-registry.ts:93-105` | 候选 |
| 右上任务浮层 | activeOnly、2s/10s 自适应轮询+窗口事件即时刷新 | `use-canvas-active-tasks.ts:15-46` | 候选 |
| 专注模式 | Ctrl/Cmd+F+Shift 进入；无选中无浮层时 Esc 退出 | `use-canvas-keyboard.ts:121-130,208-221` | 候选 |
| 版本历史 | 云端/本地草稿双 tab、只读整画布预览、恢复前自动备份 | `canvas-version-history.tsx` | 候选（对照 VR-017） |
| 回收站 | 项目软删除（最近 200 条完整快照）、恢复/彻底删除 | `use-canvas-history-store.ts`、`recycle-bin-dialog.tsx:12-136` | 对照（LibTV batch124 已有画布回收站） |

## 9. 快捷键全表（实现：`use-canvas-keyboard.ts`；展示文案：`canvas-shortcuts.ts:27-220`）

| 键 | 行为 | 证据（keyboard.ts） |
|---|---|---|
| Ctrl/Cmd + `+`/`=` / `-`/`_` | 步进缩放 ±0.1 | 99-108 |
| Ctrl/Cmd + `0` | 适应整个画布 | 109-113 |
| Ctrl/Cmd + `1` / `2` / `3` | 100% / 适应画布 / 适应选区（maxScale 1.25） | 150-156 |
| Ctrl/Cmd + `S` | 保存画布 | 115-120 |
| Ctrl/Cmd + `F`（+Shift） | 搜索节点（+Shift 专注模式） | 121-130 |
| Alt + Shift + `F` | 自动整理画布 | 134-139 |
| Alt + `L` | 批量连线（>1 选中） | 140-144 |
| `?` | 快捷键中心 | 145-149 |
| Ctrl/Cmd + `Z` / `Shift+Z` / `Y` | 撤销 / 重做 / 重做 | 157-167 |
| Ctrl/Cmd + `A` | 全选 | 168-175 |
| Ctrl/Cmd + `C` / `V` | 复制 / 粘贴节点 | 176-192 |
| `Delete` / `Backspace` | 删除（先连线后节点） | 193-207 |
| `Esc` | 取消选择/关浮层/退专注 | 208-221 |
| `V` / `H` | 框选工具 / 抓手工具 | `canvas-toolbar.tsx:153-166` |
| `Space` + 拖 | 平移 | `infinite-canvas.tsx:151-180` |
| 粘贴系统事件 | 节点标记文本→还原节点；否则系统图片优先 | 224-236 |

保护条件：文本编辑目标放行（97,131）；节点工具条内按键忽略（94）；`[data-canvas-no-zoom]` 控件上只放行 C/V（132-133）。

## 10. 与 LibTV clone 导航语义的对照声明

- BeefTV 的「默认空白左键拖=框选（工具化 V/H）」「wheel 语义拆分（滚轮缩放/触控板平移）」「Delete 先连线」与本项目 LibTV 源站权威（`docs/CANVAS_NAVIGATION.md`：blank-drag no-op、Shift+drag marquee、Batch 77 运行时证据）**多处相反**。
- 结论：互为「React Flow 默认并非唯一解」的对照样本，**均不构成**改动 `CANVAS_NAVIGATION.md` 权威的证据；任何吸收走 ADOPTION_DECISION_MATRIX 的 ADAPT 闸门（需 Par 编号 + verifier）。
