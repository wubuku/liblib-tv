# Batch 35 计划：真实 R3F 导演台第一条纵切

## 1. 缺口与价值排序

| 候选 | 当前 clone | 证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 真实 3D 导演工作区 | 无行为“脚本执行”卡片 | 原站 3D 合同 + 已有 R3F 复刻 | 5 | 本批实施 |
| 截图回到画布 | 无 | 原站节点描述 + bundle 输出合同 + 上游桥接 | 5 | 本批实施 |
| 树/视口/Inspector 同步 | 无 | 上游运行时与测试 | 5 | 本批实施 |
| 导演/机位视角与画幅 | 无 | 原站机位合同 + 上游运行时 | 4 | 本批实施 |
| 动画时间轴与关键帧 | 无 | 原站 bundle 明确，上游缺失 | 5 | 下一批优先 |
| 运动路径与曲线 | 无 | 原站 bundle 明确，上游缺失 | 5 | 时间轴后实施 |
| 手机虚拟机位 | 无 | 原站 bundle 明确 | 3 | 机位轨道稳定后实施 |

现有节点最严重的问题不是视觉误差，而是交互模型错误：它把导演台脑补成
“确认镜头/准备资产/合成提示词”的脚本步骤卡，点击按钮没有任何行为。本批先
修复产品边界，再做更细的视觉校准。

## 2. Source Fact / Replication Fact / Clone Decision

### LibTV source fact

- 画布存在名为“导演台”的 3D 节点入口；
- 节点产品描述是“搭建3D场景，截图作为构图参考”；
- 当前源 bundle 定义了场景对象、角色姿态、机位、时间轴、路径和输出回画布；
- 精确壳层尺寸、视口 toolbar 几何和当前账号的能力门控仍需运行时复核。

### Existing replication fact

- `research/upstream/storyai-3d-director-desk` 是已有 LibTV 导演台复刻参考；
- 使用 Three.js、React Three Fiber 和 Drei；
- 实现三栏工作区、语义对象树、选择驱动 Inspector、导演/机位视角、
  画幅/九宫格和 helper-free 截图；
- 没有当前 LibTV bundle 已证明的动画时间轴、路径和手机运镜。

### Clone decision

- 当前 React Flow 页面保留挂载，导演台作为 fixed full-screen island 覆盖其上；
- 使用 `next/dynamic(..., { ssr: false })` 只在打开时载入 3D 客户端代码；
- 新建独立 `directorStore`，不向 `canvasStore` 或 `frameosStore` 加 mode；
- 初始场景只使用代码生成的几何体和灯光，不复制上游模型/贴图；
- 使用一名程序化角色代理、桌/道具、地面和一台可见机位形成可辨识构图；
- 截图从 WebGL canvas 读取，按当前画幅裁剪；截图期间隐藏 grid、gizmo、
  机位 helper、selection outline 和 DOM guide；
- 一次“发送到画布”原子创建一个 image node、一条 edge 和一份 capture metadata；
- 关闭工作区不重置 React Flow nodes、edges、selection 或 viewport。

## 3. 状态与组件边界

```text
uiStore
  activeDirectorNodeId / openDirectorDesk / closeDirectorDesk

directorStore
  project(scene, objects, cameras)
  selectedObjectId
  viewMode / transformMode / aspectRatio / showThirds
  captures / activeCaptureId
  scene editing actions

canvasStore
  createDirectorCapture(sourceDirectorNodeId, capture)
  atomic image node + edge + undo snapshot

page.tsx
  dynamic DirectorDesk mount
```

`directorStore` 只保存可序列化的编辑状态。R3F 的 `Object3D`、camera、renderer
和 canvas refs 保持在组件层，不能进入 Zustand。

## 4. 实施步骤

1. 安装与 React 19.2.4 兼容的 `three`、`@react-three/fiber`、
   `@react-three/drei` 和 `@types/three`。
2. 新增导演台 schema/store、默认场景和纯函数 selectors。
3. 修正画布节点的名称、说明和 CTA，接入 open/close lifecycle。
4. 实现 topbar、对象树、R3F viewport、viewport toolbar 和 Inspector。
5. 实现树/视口选择同步、物体 visibility、transform 字段、场景和机位属性。
6. 实现导演/机位视角、16:9/9:16/1:1 画幅与九宫格。
7. 实现截图、预览、发送到画布和关闭后上下文恢复。
8. 新增 Batch 35 静态 verifier 和专项 Playwright。
9. 运行跨批回归、`npm run docs:check`、`npm run check` 和 `git diff --check`。

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-node]` | React Flow 导演台节点 |
| `[data-open-director]` | 打开工作区命令 |
| `[data-director-workspace]` | 全屏导演台根 |
| `[data-director-tree]` | 左侧对象树 |
| `[data-director-viewport]` | 中央 R3F 视口 |
| `[data-director-webgl-canvas]` | WebGL canvas 容器 |
| `[data-director-object-id]` | 对象树行 |
| `[data-director-inspector]` | 右侧上下文 Inspector |
| `[data-director-view-mode]` | 导演/机位视角命令 |
| `[data-director-aspect]` | 画幅选择命令 |
| `[data-director-capture]` | 截图命令 |
| `[data-director-capture-preview]` | 当前截图预览 |
| `[data-director-send-capture]` | 发送到画布命令 |
| `[data-close-director]` | 返回画布命令 |
| `[data-director-capture-node]` | React Flow 回流图片节点 |

## 6. 验收标准

- 点击现有或新建导演台节点 CTA 后出现全屏工作区，React Flow DOM 仍挂载。
- WebGL canvas 在桌面和移动 viewport 上存在且像素采样不是空白/单色。
- 默认场景能辨识地面、角色代理、桌/道具和机位，不依赖外部模型资产。
- 树、3D 点击和 Inspector 使用同一个 `selectedObjectId`。
- visibility、位置、旋转、缩放和 FOV 控件能改变场景。
- 导演视角与机位视角切换后 WebGL canvas 仍非空。
- 画幅比例改变 frame 几何；九宫格开关不改变 R3F canvas 尺寸。
- 截图尺寸符合选中比例，且截图不包含 grid、gizmo、机位 helper 或 DOM guide。
- 发送后新增一个 image node 和一条 director -> image edge；一次 undo/redo
  移除/恢复二者。
- 关闭后原 nodes、edges、selection 和 viewport 不丢失。
- `390x844` 使用抽屉式左右 panel，不产生 document 横向 overflow。
- 专项浏览器测试无 page error、console error 或 WebGL context failure。

## 7. 不在本批

- 把上游 Vite app 作为 iframe 或独立路由直接嵌入；
- 复制上游 mannequin、模型库、截图或其他许可证未明确的资产；
- 真实 GLTF/FBX 导入、全景投影和资源持久化；
- 多选、TransformControls 拖拽、undo stack 或项目 JSON 导入导出；
- 时间轴、关键帧、运动路径、动画录制、手机运镜；
- 把本批 prototype calibration 写成 LibTV 精确视觉事实。

## 8. 实施状态

- [x] Batch 34 证据与代码考古已复核
- [x] Next.js 16 client/lazy-loading 约束已复核
- [x] Batch 35 计划、规格、selectors 和验收矩阵已落档
- [x] 依赖、schema/store 和 canvas return transaction
- [x] 导演台 shell、R3F viewport、tree 和 Inspector
- [x] 机位、画幅、截图和回流
- [ ] Playwright、像素检查、跨批回归和实施收口
