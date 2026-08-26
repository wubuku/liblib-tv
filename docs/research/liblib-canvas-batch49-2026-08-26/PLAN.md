# Batch 49 计划：导演台视口原生坐标控件

## 1. 决策

本批选择“视口原生坐标控件”作为一个窄切片。它的价值高于继续扩展
Batch 48 的模型资产边界，因为它直接改善 3D 场景的空间定向，同时不引入
新的资产格式、远端状态或普通画布事务。

## 2. 证据等级

| 结论 | Provenance | 等级 |
|---|---|---|
| 上游有独立 R3F `GizmoViewport` | fixed checkout `8c8bd36` | `UPSTREAM_FACT` |
| 上游使用六个 DOM 命中按钮将轴向点击映射为相机快照 | `DirectorCanvas.tsx` | `UPSTREAM_FACT` |
| 上游控件位于视口右上角，默认 80×80px、距边 20px | `index.css` / `DirectorCanvas.tsx` | `UPSTREAM_FACT` |
| 当前 LibTV 有 3D 导演台、相机与视口能力 | current source bundle / Batch 34 | `SOURCE_CONTRACT` |
| 当前 clone 没有 orientation gizmo | current clone source audit | `CLONE_FACT` |
| 当前 LibTV 的确切控件几何 | 未取得 authenticated DOM contract | `UNKNOWN` |

本批允许借鉴上游实现，但不把上游 clone 的 CSS 自动升级为 LibTV
生产事实。

## 3. 实施范围

### 包含

- 在现有 Director R3F 视口上层渲染独立的小型透明 R3F gizmo canvas；
- 使用 `GizmoHelper` + `GizmoViewport` 生成 X/Y/Z 轴视觉；
- 为六个正/反方向提供无装饰、可访问的 DOM 命中按钮；
- 命中按钮根据当前 Director 相机快照计算位置和 z-index；
- 点击方向后切换到 Director 视角，并将主视口相机切到该方向；
- 在 capture、path drawing、phone recording 等不适合变更视角的状态中禁用；
- 记录 desktop/mobile 布局、R3F 非空、相机状态和浏览器错误。

### 不包含

- GizmoViewport 的拖动、自由 orbit 或面/角点命中；
- 相机快照写入 Director timeline keyframe；
- 修改 active camera 的对象 transform/target；
- source-side 精确实现、LibTV backend、远端项目持久化；
- 真实 FBX/OBJ/GLB 加载、环境库和普通画布任务。

## 4. 最小代码切片

| 文件 | 变化 |
|---|---|
| `src/components/director/DirectorViewport.tsx` | gizmo snapshot、独立 R3F overlay、轴向命中与主相机同步 |
| `scripts/verify-liblib-batch49.py` | 专项 Playwright、像素和几何验证 |
| `docs/design-references/` | 本批 desktop/mobile/contact sheet 截图 |
| 本目录 | 计划、证据、合同、实施、截图分析、成熟度 |

如确实需要新增纯数学模块，必须先证明它能减少
`DirectorViewport.tsx` 的复杂度；否则保持本批局部化。

## 5. 验收门

### 行为

- 默认导演视角显示 gizmo 视觉和六个方向按钮；
- 六个按钮都有稳定 `aria-label` 和 `data-director-viewport-gizmo-button`；
- 点击 `X 正向` 后主相机切到 target 的正 X 方向，view mode 为 `director`；
- 在 camera mode 点击轴向会回到 director mode，而不修改 active camera 对象；
- 空白点击、普通对象选择、timeline/path/phone 状态不被 gizmo 命中层破坏；
- capture 时 gizmo 不进入截图，录制/路径状态不产生额外 mutation。

### 几何和视觉

- gizmo 是独立 overlay，不改变 viewport、aspect frame、toolbar 或 timeline 的尺寸；
- desktop 距视口右上边缘有稳定间距；
- mobile 仍在 viewport 内，不造成水平溢出，也不遮挡紧邻 toolbar；
- main WebGL canvas 与 gizmo canvas 都非空；
- 新增截图只做一次视觉识别，识别结果写入 `SCREENSHOT_ANALYSIS.md`。

### 工程

- 无 `any`、无 Three.js runtime reference 进入 Zustand；
- focused verifier、Batch 35-49 serial regression、`npm run docs:check`、
  `npm run check`、`git diff --check` 全部通过；
- 只提交本批路径，不吸收历史 `docs/design-references/` 修改。

## 6. 后续队列

本批完成后重新评估：

1. 桌面侧栏折叠/全屏工作区；
2. gizmo 与相机轨道/关键帧的关系；
3. Director shell 精确几何与键盘/focus；
4. 只有 Director 的高价值能力成熟或被证据阻断后，才回到普通画布。
