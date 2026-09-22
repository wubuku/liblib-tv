# FrameOS 源站观察台账

> Read this file before reopening a screenshot. 本文件区分 DOM 事实、交互观察、截图事实和待验证事项。

## 2026-09-22 Readiness Smoke

### DOM 事实

- 源站 URL：`https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`。
- 桌面视口：`1280x720`；locale：`zh-CN`。
- 空画布初始为 0 个 `.react-flow__node`、0 个 `.react-flow__edge`。
- 空态提示逐字为“选择一种方式开始创作”，六个可见 CTA 为“文本”“图片”“视频”“音频”“3D导演台”“上传文件”。
- 可见导航包括“展开菜单”、breadcrumb “测试作品 / 测试项目 / 画布 1”、“使用教程”、“撤销”“重做”，左栏“添加节点”“查看项目资产”“从素材库选择”“本地上传”“帮助”，左下“画布小地图”“缩小”“100%”“放大”“适应画布”“搜索节点”“一键整理 · 网格整理”“选择整理方式”。
- 初始“撤销”“重做”为 disabled；隐藏弹层存在按钮不作为用户可见事实。

### 交互观察

- 点击空态“文本”后，空态消失，DOM 仍使用 React Flow 节点类；可见内容出现“文本节点1 （双击编辑文本）”。
- 点击后出现一个 `contenteditable=true` 编辑面，以及“参考”“CO 5”“全屏编辑”“高级设置”和 disabled 的图片提交按钮。
- 点击后“撤销”变为 enabled，“重做”仍为 disabled。未点击提交，未触发付费图片或视频生成。
- 该操作只是 readiness smoke，不等于 `create-first-node` 或 `edit-selected-node` 已完成 Gate A/Gate B。

### 截图事实

![空画布高亮“文本”入口](screenshots/01-create-first-node-empty-state.png)

![左栏高亮“添加节点”入口](screenshots/02-canvas-context-left-rail.png)

![左下工具条高亮“缩小”按钮](screenshots/03-navigate-canvas-toolbar.png)

- 三张图均使用 `1280x720` 页面、裁掉 y=0-60 的账户区域后输出；高亮由实时 DOM bounding box 注入，截图后已清除。
- `01-create-first-node-empty-state.png` 证明空态入口位置与可见上下文，不证明点击后的持久化结果。
- `02-canvas-context-left-rail.png` 证明“添加节点”入口位于左栏，不证明菜单项目集合。
- `03-navigate-canvas-toolbar.png` 证明左下缩放工具条位置和“缩小”入口，不证明鼠标、触摸板或快捷键语义。

### 待验证事项

- 图片、视频、音频、3D导演台、上传文件各入口的创建结果。
- 节点拖动、连接、右键菜单、历史、搜索、整理和 breadcrumb 下拉。
- 鼠标滚轮、macOS 触摸板和快捷键的准确画布导航语义。
- 上传图片、音频、视频后的节点状态、网络证据和恢复路径。
