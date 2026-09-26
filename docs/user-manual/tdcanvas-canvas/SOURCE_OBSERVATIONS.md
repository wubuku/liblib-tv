# TDCanvas 源站观察台账（SOURCE_OBSERVATIONS）

> 版本锁定：TDCanvas `v0.14.0`，提交 `16b31273633f983cdbd8de05694ec36d471b2650`（本地工作副本
> `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`，origin 为 fork `wubuku/TDCanvas`；
> 上游 HEAD 已于 2026-09-26 前移至 `d05cf612`，增量见调研包 UPSTREAM_DIFF_AUDIT §7）。
> 运行环境：TDCanvas `web/` 的 `npm run dev`（Vite 7.3.6，localhost:3000；需 nvm node 24）。
> 证据分级：`[运行时]` 本地真实浏览器交互取证；`[静态]` 源码 file:line（对齐 `16b3127`，
> 详见调研包 `docs/research/tdcanvas-2026-09-26/SOURCE_ANALYSIS.md`）；`[官方文档]`
> TDCanvas 仓内 mdx（**可能滞后于 UI，冲突时以运行时为准**）。

## 1. 全局壳与导航

- 顶部导航：TDCanvas logo、我的画布、ComfyUI 本地、提示词库、我的资产、配置；右侧 Agent、配置、中/EN、明暗主题、`v0.14.0` 版本徽标。[运行时]
- 画布编辑页顶栏：主页、画布菜单（汉堡）、项目标题（双击改名）、本地 Codex 面板、配置、中/EN、主题、版本、快捷键、Agent。[运行时]

## 2. 项目生命周期

- 首页空态：hero「从一张画布开始」+ 新建画布按钮 + 最近画布区；`?mode=new` 自动创建并跳转 `/canvas/:id`。[运行时]
- 新项目默认标题「TDCanvas 2」（0 画布时新建即为 2，编号规则待查）。[运行时]
- 项目列表按 `updatedAt` 倒序；封面取最新生成物（数据推导）；删除走确认弹窗；导出 zip（fflate，`projects.json` v3 + 引用媒体）；`importProject` API 存在但无 UI 入口。[静态]

## 3. 画布视口与手势（与常见画布不同的语义）

- wheel 永远缩放（5%–500%，鼠标锚）；缩放滑杆 5–500%（视口中心锚）。[运行时+静态]
- 空白左键拖拽 = 平移；**Space+拖拽被禁用**（只 preventDefault）。[运行时+静态]
- Ctrl/Cmd+拖空白 = 框选（Shift 加选）。[静态；运行时部分]
- 重置视图：fit 动画，缩放 clamp ≤100%（运行时实测 100%→77%）。[运行时+静态]
- 小地图（纯 div，240×160，点击/拖拽导航）开关在缩放 Dock。[静态]

## 4. 节点体系

- 类型：文本/图片/视频/音频/组/ComfyUI 工作流（双击空白菜单逐字）；Config/Aitudou 为遗留未注册类型。[运行时+静态]
- 默认尺寸：图 620×350、文 520×300、视 660×371、音 540×160、组 760×480；缩放限制 220×160–1600×1200；图片(未开自由缩放)/视频锁定宽高比。[静态]
- 空图片节点创建即选中并**自动打开下方 Aitudou 原生面板**（文生图/自动识别/参数 1k/2k/参考素材区「从画布连线后会自动带入参考素材」）。[运行时]
- 文本节点：双击编辑文字、悬浮工具条「编辑文字/生图/缩小/放大」、占位「双击编辑文字」+ 右上「生图」入口；下方面板「文本创作」。空态文案「双击编辑文字」。[运行时]
- 悬浮工具条（图片有内容后展开全集）：信息/删除/存资产/下载/编辑/复制提示词/反推提示词/替换图片/裁剪/切图/放大/查看大图/更多（含 角度、自由缩放，默认隐藏可自定义，`tdcanvas:image-quick-tools-v6`）。[运行时+静态]
- 节点信息 Modal：ID/类型/尺寸/位置/状态/路径/批量数/提示词/错误/原始 JSON。[静态]

## 5. 素材上传与媒体

- 全局隐藏多选 file input，accept 白名单：`image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,.mp4,.mov,.avi,.mkv,audio/mpeg,audio/wav,audio/x-wav,audio/flac,audio/x-flac,.mp3,.wav,.flac`；单文件 ≤50MB。[运行时取 accept 原文+静态]
- **空图片节点 + 真实图片**：原地替换节点（replaceNodeWithMaterialFile），标题=文件名，按自然比例重设尺寸（居中补偿）。[运行时]
- **非空节点 + 新图片**：新建节点 + 视口聚焦动画。[运行时]
- 拖放上传：同白名单，落点 40px 阶梯错位建节点，`sourceOrigin:"upload"`。[静态]
- 图片历史：每节点 ≤24 条版本（FNV-1a 签名去重），历史面板切换回写 metadata；引用可 pinned。[静态]
- 本地 Canvas2D 操作：裁剪/切图/放大（1K/2K/4K，非 AI）——产物建子节点并连线；角度重渲染走 AI（付费，手册只描述）。[静态]

## 6. 连线与引用（数据流语义）

- 端口拖拽建立连线：贝塞尔曲线即时生成，两端节点 related 高亮。[运行时]
- 连线校验：禁自连/禁组、方向相对、类型兼容（any 通配）、非 multiple 输入口限一条入边。[静态]
- **拖线到空白处弹创建菜单**（文本/图片/视频/音频）→ 建节点+反向端口连线+选中+开面板。[静态]
- 双模式：connections（连线模式）/ objects（无线引用）互斥——objects 模式不渲染连线、添加引用清空既有连线；引用支持 latest/pinned 版本。[静态]
- @mention：contentEditable 输入 `@` 弹候选插缩略图 chip，序列化「图片 N / 视频 N / 文本 N」标签。[静态+官方文档]

## 7. 生成工作流（**付费动作，手册只描述不回走**）

- 入口：原生面板运行按钮/回车、文本节点「生图」按钮（右侧 +96px 新建图片节点并连线）、错误卡重试、反推提示词（建 midjourney.describe 文本节点）。[静态]
- 任务状态机：queued→running→succeeded/partial/failed/attention/stopped；本地停止≠远端取消（明示「远端任务仍可能继续执行并计费」）；提交即写 journal（localStorage），刷新恢复；节点级守卫防重复计费。[静态]
- 模型：静态目录 `AITUDOU_MODEL_PROFILES`（123 文档条目：Seedance/Seedream/Qwen/Wan/Kling/Hailuo/Flux/Vidu/Doubao Audio/Kimi/Whisper/Suno 等）；inputKind 自动匹配变体；价格目录实时拉取并逐模型报价。[静态]
- 未配置 API Key 时生成不可用（配置页需填 Key）——运行时探索全程未配置，生成入口未点击。[运行时边界]

## 8. 撤销/持久化/多项目

- undo/redo：页面级全量快照双栈（180ms 防抖合并、拖拽合并为一条、上限 50）；快捷键 Cmd/Ctrl+Z / +Shift / Ctrl+Y。[静态]
- 持久化：全自动三级漏斗（页面 effect → 400ms 防抖 → localforage IndexedDB），无手动保存；viewport 属项目文档（500ms 防抖）。[静态]
- 快捷键全集（project.tsx:1735-1807）：Cmd/Ctrl+Z(+Shift)/Y、A、C、V、Delete/Backspace、Escape（清 13 项状态）；无缩放类键盘快捷键；官方快捷键文档与源码一致。[静态+官方文档]

## 9. 官方文档与实际 UI 的差异（重要）

TDCanvas 仓内 `docs/content/docs/canvas/canvas-node-manual.zh-CN.mdx` 描述的生成流为**旧版语义**：

| 官方文档说法 | 基线 `16b3127` 实际行为 |
|---|---|
| 「生图」创建**生成配置节点**（Config）并连线 | Aitudou 原生面板直接挂在媒体节点下方（Config 节点已迁移为遗留类型） |
| 视频生成走 OpenAI `/v1/videos`、火山方舟 Agent Plan | 实际主通道为 Aitudou API（aitudou.ts 1003 行任务状态机） |
| 「画布节点右上角不再显示资源角标」 | 与当前实现一致（mention chip 序列化） |
| 撤销范围含「助手会话变化」 | chatSessions 为无 UI 遗留子系统（数据链在、无聊天 UI） |

手册成稿以**运行时行为为准**，官方文档仅作术语与历史参考；上表差异写入 troubleshooting 候选。

## 10. 自动化方法备忘（复跑手册回走用）

- Playwright locator 点击会被画布覆盖层拦截（含 force）→ **必须走 CUA 坐标路径**（截图定位）。
- `page.evaluate` 桥接不稳定（返回空对象/参数不传递）→ 页侧脚本用 `locator("body").evaluate`。
- IAB 无文件选择器 → 真实素材注入：复制到 `web/public/__rt__/`（ASCII 名，用后删）→ 页内 fetch → File → input.files → change（详见 TEST_MEDIA_ASSETS.md）。
- dev server 启动：`nvm use 24 && cd web && npm run dev`（Vite @3000）；停机后 IndexedDB 数据保留在浏览器 profile。
