# FrameOS 画布 — 实施总结

> 面向后续开发者/agents 的一份"我做了什么、为什么这样做、未来如何继续"的总览。
> 如果你想扩展功能、加新节点类型、或者调试问题，先读这份。

---

## 1. 一句话目标

把 `frameos.cn/#/canvas/...` 的画布编辑器复刻成 Next.js + React Flow 的 `/frameos/*` 路由，复用项目里**已经克隆好的 liblib-tv 画布**作为脚手架。

---

## 2. 关键设计决策

### 2.1 单独路由 + 单独 store（**而不是**多 mode 单 store）

| 决策 | 原因 |
|---|---|
| 路由 `/frameos/canvas/[id]` 与 `/` 完全分离 | 数据形状分歧大（frameos 有 breadcrumb 三级、prompt bar、history stack），强行统一 store 会产生 awkward union |
| 独立 `frameosStore`（不复用 `canvasStore`） | 即使同名字段（如 `nodes`、`edges`）在两个画布语义不同；改一个不影响另一个 |
| **共享**的：React Flow 库、`DeletableEdge` 自定义边、`cn()` utility | 这些是真正的"基础设施"，两边画布同型同构 |

**经验法则**：要做只在 FrameOS 用的功能就改 `frameosStore`，要做 liblib-tv 用的就改 `canvasStore`，要做两边都要的考虑抽成 lib（但先不要提前抽）。

### 2.2 节点不直接画 — 全部走 `FrameosNodeShell`

`FrameosNodeShell` 是 FrameOS 节点通用外壳，统一处理：
- `.node-floating-title` 绝对定位 top: -22px
- `.node-card` 容器（bg #1C1C1C, radius 10px）
- 左右 `<Handle>`（选中时变成 14×14 白色圆形 + 蓝边）
- 右下角 resize-handle（hover 显示，视频节点不显示）
- 选中态：`box-shadow: 0 0 0 4px rgba(59,130,246,0.18)` + 蓝色边框

**所有节点必须用这个 shell**。如果你要加新节点类型，先继承这个 shell。

### 2.3 浮动面板（floating-toolbar / PromptEditor / EditPanel）**跟随节点 + 画布缩放**

这是用户提的"节点拖动时 panel 跟随" UX。实现方式：

```tsx
// 在 floating 组件里用 useViewport() 拿 pan + zoom
const { x: panX, y: panY, zoom } = useViewport();
const nodeX = node.position.x * zoom + panX;
const nodeY = node.position.y * zoom + panY;
// 然后用 position: fixed 定位
```

**绝对不要** 用 `position: absolute` + 节点 position 算 — React Flow 用 `transform: translate(x, y)` 渲染节点，absolute 定位会无视画布的 pan/zoom，导致 panel 漂在视口中央。

### 2.4 PromptEditor 是**条件渲染**（仅在节点选中时显示）

不要让它一直固定在屏幕底部。原站的行为：
- 无选中 → 不显示
- 选中节点 → 出现在节点正下方 12px 处
- 全屏编辑 → 居中放大到顶部 80px

### 2.5 调试模式 (`isDebugMode`) — 隔离开发期产物

`FrameosNodeEditPanel`（节点 ID / 坐标 / 参数表单 / 快捷操作）**不是** FrameOS 原站有的功能。是我加的开发者调试便利。**默认隐藏**，通过右下角橙色 `DEBUG` 按钮开关。

**未来如果要删掉调试代码**：
- 删 `isDebugMode` / `toggleDebugMode` 字段
- 删 `<FrameosNodeEditPanel />` 挂载
- 删 `FrameosNodeEditPanel.tsx`

### 2.6 工具栏按钮（floating-toolbar）**按节点类型显示不同内容**

- 文本节点：下载、收藏、超清
- 视频节点：下载、收藏、超清、改图
- 图片节点：下载、收藏、超清、720全景、改图、宫格切分

按钮目前是 no-op（console.log），需要接入时改 `FrameosNodeFloatingToolbar.tsx` 里的 `onClick`。

---

## 3. 状态机（`frameosStore`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `breadcrumb` | `{project, scene, canvas}` | 三级面包屑 |
| `nodes` / `edges` | `FrameosNode[]` / `Edge[]` | 画布内容 |
| `past` / `future` | `[]` | history stack（最多 20 步） |
| `zoomPercent` | `number` | dock-bar 中间显示 |
| `showMinimap` | `boolean` | minimap 显隐 |
| `minimapPinActive` | `boolean` | 小地图钉按钮 active |
| `promptValue` | `string` | PromptEditor 输入（受控） |
| `selectedNodeId` | `string | null` | 当前选中节点 |
| `isAddNodeMenuOpen` | `boolean` | 左侧 + 号菜单 |
| `isOrganizeMenuOpen` | `boolean` | 整理方式菜单 |
| `organizeMode` | `'horizontal' | 'vertical' | 'grid'` | 当前整理方式 |
| `selectedModel` | `string` | "帧界 O2" / "帧界 G2" 等 |
| `isPromptFullscreen` | `boolean` | PromptEditor 全屏模式 |
| `isHelpOpen` | `boolean` | 快捷键帮助面板 |
| `isDebugMode` | `boolean` | 调试模式（**默认 false**） |

**actions**：`addNode` / `duplicateNode` / `removeNode` / `undo` / `redo` / `selectNode` / `setBreadcrumb` / `togglePromptFullscreen` / `toggleHelp` / `toggleDebugMode` / `setOrganizeMode` / `setSelectedModel` / `toggleMinimap` / `toggleAddNodeMenu` / `toggleOrganizeMenu` 等。

**history push 时机**：`addNode` / `removeNode` / `duplicateNode` / 改 `nodes` 的命令式操作。**`setNodes` 不入栈**（避免拖动 / undo 时回退错位置）。

---

## 4. 键盘快捷键完整列表

| 键 | 行为 |
|---|---|
| `Esc` | 多级退出：帮助面板 → 全屏 Prompt → 添加节点菜单 → 整理菜单 → 取消选中 |
| `Delete` / `Backspace` | 删除选中节点（输入框内不触发） |
| `Cmd/Ctrl + Z` | 撤销 |
| `Cmd/Ctrl + Shift + Z` | 重做 |
| `Cmd/Ctrl + D` | 复制选中节点 |
| `?` 或 `Shift + /` | 打开/关闭帮助面板 |
| `+` / `=` | 放大画布 |
| `-` / `_` | 缩小画布 |
| `0` | 适应画布 |

完整定义在 `src/app/frameos/canvas/[id]/page.tsx` 的 `useEffect` 键盘 handler。

---

## 5. 路由

```
/                          → liblib-tv 主页（已有，未改）
/frameos                   → 重定向到 /frameos/canvas/demo
/frameos/canvas/[id]       → FrameOS 画布（id 是任意字符串，目前只有 "demo"）
```

原 homepage 的 `TopNavBar` 加了一个 "FrameOS" 链接按钮（蓝色图标），从原画布可以一键跳到 frameos 画布。

---

## 6. 如何继续探索 / 扩展

### 添加新节点类型
1. 在 `src/types/frameos.ts` 加类型变体
2. 在 `src/store/frameosStore.ts` 的 `addNode()` 加上新 case
3. 创建 `src/components/frameos/nodes/FrameosMyNode.tsx`，用 `FrameosNodeShell` 包
4. 在 `src/app/frameos/canvas/[id]/page.tsx` 的 `nodeTypes` map 注册
5. 在 `FrameosToolRail.tsx` 的添加节点菜单里加选项
6. 在 `FrameosNodeFloatingToolbar.tsx` 添加该类型对应的工具按钮

### 修复 PromptEditor 跟丢节点
检查 `FrameosPromptEditor.tsx`：
- 必须用 `useViewport()` 拿 pan + zoom
- 必须用 `position: fixed` 而非 `absolute`
- 边界碰撞检测（左右下三向）必须用 `window.innerWidth/Height`

### 卸载调试代码
参见 2.5。

### 接入真实后端
- `setNodes` / `setEdges` / `addNode` 是 mutation points。包一层 API 调用即可。
- `frameosStore` 加 `persist` middleware (zustand/middleware) 可存 localStorage。

---

## 7. 与原站 FrameOS 的差异（明确承认的）

| 方面 | 原站 | 我做的 |
|---|---|---|
| 节点详情面板 | ❌ 没有 | ✅ 有，但**默认隐藏**，需开 DEBUG |
| PromptEditor | 条件显示在节点下方，跟随节点/缩放 | ✅ 一致（Batch 180 恢复跟随定位） |
| 节点 hover 时显示工具条 | ❌ 不显示（只有选中才显示 floating-toolbar） | ✅ 一致 |
| 视频内嵌播放 | ✅ | ✅（用 mp4 URL 推导出，可能因 cors 失败而 fallback） |
| 整理节点（网格/横向/纵向） | ✅，整理后视口适配、可撤销 | ✅ 一致（Batch 175） |
| 撤销/重做 | ✅（用 Vue history stack） | ✅（用 Zustand `past` / `future`；连线创建/删除 Batch 174 起入栈） |
| 节点替换内容 | ✅ 文件选择 | ✅ 文件选择（点 `replace-btn` 触发 `<input type="file">`） |
| 节点类型 | 7 类：文本/图片/视频/音频/3D模型/3D导演台/视频剪辑台 | 菜单 7 类逐字（Batch 167）；音频与 3D 类菜单项为 mock（无渲染器，Batch 167/182） |
| 模型选择器 | Seedream 5.0 Pro 等多个模型 | 6 模型（mock，默认 Seedream 5.0 Pro，Batch 160） |
| 提交 prompt | 调 API | no-op |
| 添加节点 | 左栏菜单 + 空态 CTA；~~双击空白~~（2026-09-24 新版本已移除） | 菜单 7 类逐字 + 空态 CTA（Batch 187）；双击空白入口已同步移除（Batch 182） |
| 文本/视频节点工具条 | 全屏查看 / 下载 两个 icon 按钮 | ✅ 一致（Batch 158/171） |
| 图片节点面板 | 聚焦/故事版/参考磁贴 + 引用芯片 + 删除连线/替换参考；聚焦模式（局部框选） | ✅ 一致（Batch 159/180/197；聚焦模式的真实局部框选未实现——需已生成图像） |
| 故事版模式 | ✅ 占位模板 + 模型/积分切换 | ✅ 一致（Batch 198） |
| 模板面板 | ✅ 公共/企业/我的模板 + 卡片 | ✅ 面板结构一致；卡片应用保持 mock |
| 项目资产面板 | ✅ 角色/物品/环境 | ✅ 一致 |
| 素材库/上传 | ✅ | 面板/对话框一致；实际上传未验证 |
| 搜索节点 | ✅ | ✅（Batch 163） |
| 小地图拖拽平移 | ✅ | ✅（Batch 179） |
| 参考选择模式 | ✅ 从画布选择参考 | ✅ 入口/顶栏/退出一致；真实框选未实现 |
| 多选/编组 | 源站行为未采样 | ❌ 未实现（无源站证据，不发明） |
