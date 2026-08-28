# LibTV 画布操作指南

> 这是普通 LibTV React Flow 画布的当前操作权威。开发者或 agent 修改
> `src/app/page.tsx` 的 viewport、滚轮、拖动、工具快捷键或节点拖动前，先读本页，
> 再读 [`NAVIGATION_GESTURES.spec.md`](research/liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md)
> 和 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)。
>
> 本页记录的是 2026-08-28 对已登录 LibTV 原站和当前 clone 的行为核对结果。
> 它只覆盖普通画布，不覆盖 FrameOS，也不覆盖 Director 的 R3F 场景操作。

## 快速结论

| 目的 | 当前 clone 操作 | 结果 |
|---|---|---|
| 平移画布 | 未按修饰键滚动；或按住鼠标中键拖动 | 平移，不改变 graph/history |
| 临时平移 | 按住 `Space`，同时用左键拖动画布空白处 | 松开 `Space` 后恢复原工具 |
| 持久平移 | 按 `H`，再用左键拖动画布空白处 | 进入抓手工具，按 `V` 返回 |
| 选择/移动节点 | 按 `V`，点击或拖动节点本体 | 节点位置改变；空白左键拖动不产生框选 |
| 缩放画布 | macOS 触摸板双指捏合；或 `Command`/`Control` + 滚轮 | 以指针位置为缩放参考 |
| 恢复视图 | 点击底部百分比菜单中的“适合屏幕”，或 `Command+0` | 只改变 viewport |

## macOS 鼠标

### 平移

1. **鼠标滚轮**：在画布上滚动，垂直滚轮改变纵向 viewport，横向滚轮改变横向
   viewport。普通滚轮不是缩放入口。
2. **鼠标中键**：按住滚轮并拖动。该入口不要求先切换到 `H`，在 `V` 模式也可用。
3. **Space + 左键**：按住 `Space`，再按住左键拖动空白画布。`Space` 只在按住期间
   生效，不会改变持久工具。
4. **H + 左键**：按 `H` 进入抓手工具，再用左键拖动空白画布。此状态会保持，
   直到按 `V` 或从底部工具菜单选择“移动”。

### 缩放

- 按住 `Command` 的同时滚动鼠标滚轮。
- 在 Chromium 自动化中，macOS 触摸板 pinch 通常以 `Control` 修饰的 wheel
  事件进入页面；不要要求真实用户在触摸板 pinch 时按住 `Control`。
- 缩放围绕当前指针位置进行；缩放不会创建 graph history entry。

### 节点拖动和空白拖动的区别

- `V` 是节点选择/移动工具。拖动节点本体会修改节点的 flow position，并由节点
  拖动事务记录一次 graph history。
- `V` 下拖动空白处不是画布平移，也不是当前源站已核实的框选入口；它是 no-op。
- `H` 或按住 `Space` 后，左键拖动空白处才是画布平移。
- 鼠标中键平移独立于 `V/H/Space`，不能被节点拖动或空白点击取消选择逻辑吞掉。

## macOS 触摸板

| 触摸板动作 | 页面语义 | 注意 |
|---|---|---|
| 双指上下/左右滚动 | 平移画布 | 不改变 zoom |
| 双指捏合 | 缩放画布 | Chromium 通常把 pinch 暴露为 `ctrlKey` wheel |
| `Space` + 单指按住拖动 | 临时平移 | 松开 `Space` 后恢复 `V` 或 `H` |
| 触摸板无法提供中键 | 使用 `Space` + 左键拖动代替 | 这是同一平移语义，不新增工具状态 |

触摸板的物理手势由操作系统和浏览器转换为 pointer/wheel 事件。clone 不手写
设备识别算法，而是通过 React Flow 的 `panOnScroll`、`panOnScrollSpeed=1`、
`zoomOnScroll` 和显式 modifier 事件路径复刻结果。不要把触摸板的 `Control`
事件模拟方式写成用户必须按键的操作步骤。

## 工具状态

### `V`：移动

- 持久工具状态：`canvasTool = "select"`。
- 节点可拖动。
- 空白左键拖动保持原位，不产生 selection rectangle。
- 选择状态仍由点击、修饰键点击和节点/edge 的既有 selection owner 管理。

### `H`：抓手工具

- 持久工具状态：`canvasTool = "pan"`。
- 左键空白拖动平移。
- 节点不可通过普通左键拖动移动。
- 中键拖动仍然是平移入口。

### `Space`：临时抓手

- 只在非 `input`、`textarea`、`contenteditable` 编辑目标中接管。
- `keydown` 后 `data-temporary-pan="true"`，pane 使用 grab cursor。
- `keyup`、window blur 和 document hidden 会清除临时状态。
- 不改变持久 `canvasTool`，不进入 graph history。

## 缩放菜单和键盘

底部画布控制中的百分比按钮打开 `data-liblib-overlay="zoom-menu"`。当前 clone
提供：

- `放大`：`Command/Ctrl +`；
- `缩小`：`Command/Ctrl -`；
- `适合屏幕`：`Command/Ctrl + 0`；
- `缩放至 50%`、`100%`、`800%`。

源站在 2026-08-28 的两个 UI surface 存在文案差异：缩放菜单显示 `⌘0`，快捷键
面板的文本快照显示 `0`。运行时核对表明普通 `0` 不会适合屏幕，`Command+0`
会适合屏幕；clone 采用运行时有效的 `Command/Ctrl+0`。见
[`SOURCE_NAVIGATION_AUDIT_2026-08-28.md`](research/liblib-canvas-batch77-2026-08-28/SOURCE_NAVIGATION_AUDIT_2026-08-28.md)。

## 实现边界

普通画布导航由 [`src/app/page.tsx`](../src/app/page.tsx) 统一仲裁：

```text
canvasTool === "pan" || isSpacePressed
  -> effectivePan
  -> panOnDrag / nodesDraggable / cursor
```

当前关键 React Flow 配置：

```tsx
panOnScroll
panOnScrollSpeed={1}
zoomOnScroll
panOnDrag={effectivePan ? [0, 1] : [1]}
panActivationKeyCode={null}
selectionOnDrag={false}
nodesDraggable={canvasTool === "select" && !effectivePan}
```

`panOnDrag` 的数字是鼠标按钮：`0` 左键，`1` 中键。中键必须在普通选择模式
下也保留，因此不能只把它写成 `effectivePan` 布尔值。

不要把下列三类操作混淆：

1. **普通画布平移/缩放**：改变 React Flow viewport，不改变 graph document；
2. **普通节点拖动**：改变 `canvasStore` 中节点 flow position，进入节点拖动事务；
3. **Director 物体移动**：在 `DirectorViewport` 的 Three.js/R3F 场景中通过
   `TransformControls` 改变 authored object transform，与 React Flow pane 操作
   是两个独立的领域和 history owner。

## 验证

本页对应的 focused gate：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch77.py
```

该 gate 使用真实 Playwright pointer/wheel 输入检查普通滚轮、中键、`Space`、`H`、
`V`、modifier wheel、空白 no-op、zoom menu、mobile overflow 和 console/page/request
错误。Director gizmo drag 也在同一批保留独立断言。

源站只读证据和测试基线：

- [`SOURCE_NAVIGATION_AUDIT_2026-08-28.md`](research/liblib-canvas-batch77-2026-08-28/SOURCE_NAVIGATION_AUDIT_2026-08-28.md)
- [`NAVIGATION_GESTURES.spec.md`](research/liblib-canvas-batch6-2026-08-25/NAVIGATION_GESTURES.spec.md)
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)
