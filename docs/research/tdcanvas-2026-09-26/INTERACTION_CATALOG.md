# TDCanvas 交互目录

> 覆盖用户可达交互的触发 → 行为 → 证据（file:line，对齐 `16b3127`）→ 对 clone 的相关性。
> 引用质量：全部 6 表 + 快捷键全表已完成逐条抽检（本文件 79/79 命中；包内累计引用台账以 ITERATION_LOG 维护记录为准，不在此处硬编码以免过时）。
> 机制细节见 [SOURCE_ANALYSIS.md](SOURCE_ANALYSIS.md)；归属（继承/原创）见 [UPSTREAM_DIFF_AUDIT.md](UPSTREAM_DIFF_AUDIT.md)；采纳判断见 [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)。
> 相关性图例：`高`=LibTV/Jimeng 已有对应面或 parity backlog 方向；`中`=FrameOS/未来能力；`低`=对照研究。

## 1. 视口手势

| 交互 | 触发 | 行为 | 证据 | 相关性 |
|---|---|---|---|---|
| 缩放 | wheel（任意修饰键） | 以鼠标为锚，`pow(1.1,-dy/100)`，clamp 5%–500% | `td-canvas-surface.tsx:69-89` | 低（语义相反，clone=React Flow 默认） |
| 缩放（UI） | 左下滑杆 | 以视口中心为锚，5%–500% | `project.tsx:1207-1218`；`canvas-zoom-controls.tsx:84-95` | 低 |
| 平移 | 中键拖拽 或 左键拖空白 | rAF 合帧平移；`data-canvas-panning` + grabbing 光标 | `td-canvas-surface.tsx:104-118, 169-178` | 中（空白拖拽平移 vs clone blank-drag no-op） |
| Space+拖拽 | 按住 Space 左键拖 | **故意禁用**：只 preventDefault 不平移 | `td-canvas-surface.tsx:120-122` | 低（与 clone Space=平移相反） |
| 框选 | ctrl/cmd+左键拖空白 | 世界矩形相交选择；shift=加选 | `project.tsx:1270-1302, 1485-1517` | 中（clone=Shift+drag marquee） |
| 适配视图 | 重置视图按钮 | 可见节点包围盒算 k（≤1），280ms 动画 | `project.tsx:1136-1174` | 中 |
| 聚焦节点 | 侧栏单击节点 | 450ms 动画定位，k clamp 0.05–1.5 | `project.tsx:1176-1203` | 中 |
| 小地图导航 | 点击/拖拽小地图 | 视口中心移至点击世界点 | `canvas-mini-map.tsx:86-113` | 中 |
| 弹层豁免 | antd 弹层/`[data-canvas-no-zoom]` 内滚轮 | 不缩放、不阻止默认滚动 | `td-canvas-surface.tsx:71, 93, 200-212` | 高（同 clone overlay 命中课题） |
| 背景模式 | 外观 flyout | dots/lines/blank 三种屏幕空间背景 | `canvas-toolbar.tsx:298-385` | 低 |

## 2. 节点生命周期

| 交互 | 触发 | 行为 | 证据 | 相关性 |
|---|---|---|---|---|
| 建节点（工具栏） | 左侧 Dock「+」flyout | 文本/图片/视频/音频/primary 插件/分组/上传素材/扩展分组；带 localStorage 记忆的上次配置 | `canvas-toolbar.tsx:269-296`；`canvas-node-preferences.ts:36-69` | 高 |
| 建节点（双击空白） | 双击画布 | 该位置弹 NodeCreateMenu（注册表驱动） | `td-canvas-surface.tsx:125-129`；`project.tsx:3692-3698` | 高（clone Batch 115 双击开面板） |
| 建节点（右键） | 空白右键→添加节点 | 同创建菜单 | `canvas-context-menu.tsx:71-81` | 高 |
| 拖文件入画布 | drop | 白名单校验（图/视频/音频 ≤50MB），落点 40px 阶梯错位建节点 | `canvas-upload-material.ts:13-60`；`project.tsx:2772-2791` | 高 |
| 上传到空节点 | 文件选择器 | **原地替换**节点类型 | `project.tsx:1634-1694` | 中 |
| 重命名 | 双击标题 | input（≤64），Enter 提交/Escape 还原 | `canvas-node.tsx:336-352` | 高 |
| 移动 | 左键拖节点 | 选中集+批量子图+组成员联动；对齐辅助线（7px 阈值）+可选网格吸附 | `project.tsx:1337-1365, 1442-1472` | 高 |
| 缩放 | 四角手柄 | min 220×160 / max 1600×1200；图片(未开 freeResize)/视频锁比；居中补偿 | `canvas-node.tsx:249-306`；`canvas-node-size.ts` | 高 |
| 自由比例开关 | hover 工具栏 | 开=自由；关=按自然比例回弹高度保持垂直中心 | `project.tsx:1827-1838` | 高 |
| 选择 | 单击 | shift/meta/ctrl 皆 toggle；capture 阶段先选中 | `project.tsx:1306-1335` | 高 |
| 复制/粘贴 | Cmd+C/V | 内存剪贴板；粘贴中心对齐画布中心、groupId 重映射、标题 " Copy" | `project.tsx:1043-1134` | 高 |
| 粘贴兜底 | 内部剪贴板空 | 系统剪贴板：图→图片节点、文→文本节点 | `project.tsx:1716-1733` | 中 |
| 制作副本 | 节点右键 | 偏移 +36,+36 | `project.tsx:1025-1041` | 中 |
| 删除 | Delete/Backspace | 引用清理链（批量子图/停生成/objectReferences/groupId/主图重选/13 项悬空 UI/文件） | `project.tsx:841-893` | 高（对照 VR-013） |
| 拖入分组 | 拖到 Group 上 | 中心点包含判定，pad=24 收进并写 groupId；实时高亮 | `canvas-node-geometry.ts:16-47` | 中 |
| hover 工具条 | hover/唯一选中 | info/retry/存资产/下载/编辑/字号±/上传替换/图片快捷工具（可自定义）/插件注入；节点顶上方定位 | `canvas-node-hover-toolbar.tsx:145-196`；`canvas-node-toolbar-position.ts:3-10` | 高 |
| 节点信息 | info 按钮 | Modal：ID/类型/尺寸/位置/状态/路径/批量数/提示词/错误/原始 JSON（脱敏） | `canvas-node-hover-toolbar.tsx:274-367` | 中 |
| 图片历史 | 节点右上历史按钮（≥2 条） | 版本面板；切换回写节点 metadata | `canvas-node.tsx:916-1037`；`canvas-image-history.ts:34-48` | 高（候选 ADAPT） |
| 大图预览 | 双击图片/侧栏 Eye | antd Modal 纯 img contain（无缩放平移） | `project.tsx:3953-3963` | 低 |

## 3. 连线与引用

| 交互 | 触发 | 行为 | 证据 | 相关性 |
|---|---|---|---|---|
| 建连线 | port 按下拖拽 | 几何命中（口 40/scale、节点 32/scale、三级优先级）；贝塞尔虚线跟随 | `project.tsx:573-615, 1809-1818` | 高 |
| 拖线到空白 | 松手未命中 | 弹 文本/图片/视频/音频 菜单 → 建节点+反向连线+选中+开面板 | `canvas-create-menus.tsx:16-43`；`project.tsx:547-566` | 高（候选 ADAPT） |
| 连线校验 | connectNodes | 禁自连/禁 Group/方向相对/类型兼容（any 通配）/非 multiple 口限一条 | `canvas-node-ports.ts:63-85` | 高（对照 VR-009） |
| 删连线 | 连线右键/Delete | 删连接并清悬空态 | `project.tsx:895-899` | 高 |
| 无线引用 | objects 模式添加 | 写 objectReferences 并**清掉已有连线**；latest/pinned 版本 | `project.tsx:905-923`；`canvas-resource-references.ts:174-190` | 高（AutoLink 对照） |
| @mention | 输入 @ | 候选菜单插缩略图 chip；序列化「图片 N」标签 | `canvas-prompt-chip-input.tsx:86-328` | 高 |
| 运行态光效 | 节点生成中 | 该节点相关连线流动虚线 | `canvas-connections.tsx:67-72` | 中 |

## 4. 生成工作流

| 交互 | 触发 | 行为 | 证据 | 相关性 |
|---|---|---|---|---|
| 运行生成 | 原生面板圆形按钮/回车 | 任务提交→queued→轮询（4s/60min/退避）→写回 | `aitudou-native-generation-panel.tsx:489-500`；`aitudou.ts:567-591` | 高 |
| 文本生图 | Text 节点右上按钮 | 右侧 +96px 建 Image 节点+连线+开面板（不直接生成） | `project.tsx:3425-3451` | 高 |
| 重试 | error 卡/hover 工具栏 | `handleRetryNode` 重建任务 | `project.tsx:3244-3423` | 高 |
| 停止轮询 | 停止按钮+确认 | 仅本地停止；明示「远端仍可能计费」；phase=stopped | `project.tsx:2196-2214, 2353-2365` | 高 |
| 断点恢复 | 刷新后打开项目 | journal 合回在途任务；不确定中断标 polling_interrupted | `aitudou-task-journal.ts:71-123` | 高 |
| 批量展开/设主图 | 双击 batch 根/卡片按钮 | 堆叠帧展开收起；primaryImageId 切换 | `project.tsx:1870-1921` | 高（候选 ADAPT） |
| 多输出建节点 | Aitudou 多 outputs | 非 content 输出各建节点（6 个一列）+连线+防重复 | `project.tsx:4081-4123, 2096-2103` | 高 |
| 历史版本切换 | 历史面板选择 | 回写 metadata；pinned 引用锁定版本 | `canvas-image-history.ts:34-48` | 高 |
| 反推提示词 | hover 工具栏 | 建 `midjourney.describe` Text 节点+连线运行 | `project.tsx:2462-2495` | 中 |
| 裁剪/分割/放大 | hover 工具栏 | 本地 Canvas2D；产物建子节点+连线（split 建 N 个） | `canvas-node-crop/split/upscale-dialog.tsx` | 中 |
| 角度重渲染 | hover 工具栏 | CSS3D 预览→AI image-to-image 生成 | `canvas-node-angle-dialog.tsx:20-93` | 中 |

## 5. 周边表面

| 交互 | 触发 | 行为 | 证据 | 相关性 |
|---|---|---|---|---|
| 项目 CRUD | 首页卡片 | 打开/重命名/删除（确认框）/多选批量导出删除；`?mode=new/recent` 直达 | `pages/canvas/index.tsx:30-197` | 高 |
| 项目封面 | 数据推导 | 最新生成物（imageHistory>outputs>content），非截图 | `canvas-home.ts:23-56` | 高 |
| 导出 zip | 首页多选/卡片 | fflate zip：projects.json(v3)+引用媒体 | `canvas-export.ts:11-32` | 中（导入无 UI） |
| 资产插入 | 资产选择器 | text/video/image 三分支在视口中心建节点 | `project.tsx:3494-3520` | 中 |
| 提示词插入 | 面板书本按钮 | PromptSelectDialog 选词回填 | `canvas-prompt-library.tsx:10-30` | 中 |
| 侧栏节点列表 | canvas tab | 类型过滤+搜索+聚焦+预览+多选批量导出+状态点 | `canvas-side-panel.tsx:157-296` | 中 |
| Agent 写画布 | agent 工具调用 | SSE 下发→网页确认→applyOps→result 回传；单次 undo 快照 | `local-agent-panel.tsx:782-855`；`use-agent-bridge.ts:43-90` | 高（Director 参考） |
| 插件安装 | 管理器 | 注册表/本地/URL/dev 四来源；启用即注册+css+setup | `plugin-loader.ts:31-170` | 中 |
| 快捷键帮助 | 缩放 dock 按钮 | 键位弹窗 | `canvas-zoom-controls.tsx:105-106` | 高（对照 clone 快捷键面板） |

## 6. 键盘快捷键全表（`project.tsx:1735-1807`）

| 键 | 行为 | 备注 |
|---|---|---|
| Cmd/Ctrl+Z | 撤销 | +Shift 重做 |
| Cmd/Ctrl+Y | 重做 | |
| Cmd/Ctrl+A | 全选节点 | 清连线选中/菜单/框选 |
| Cmd/Ctrl+C | 复制选中 | 有文字选区时让位浏览器 |
| Cmd/Ctrl+V | 粘贴 | 内部剪贴板优先，系统兜底 |
| Delete/Backspace | 删节点（含批量/组员），无选中删连接 | 等价 |
| Escape | 清 13 项状态（选择/连线/菜单/框选/连线中/hover/工具条/面板/编辑态/info/crop/待建菜单） | 单层 Escape |
| Space | 无操作（只 preventDefault） | 故意禁用 |
| — | 无缩放/适配键盘快捷键 | 仅滚轮/滑杆/按钮 |

> 守卫：焦点在 input/textarea/select/contenteditable/`[data-canvas-no-zoom]`/`[data-canvas-shortcuts-ignore]` 时全部跳过（`:1737-1739`）。
