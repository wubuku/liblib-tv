# Director Workspace Specification

## 1. Purpose

导演台是 LibTV React Flow 的一个专用 3D authoring surface，不是普通节点的
下方参数面板。用户从导演台节点进入工作区，搭建构图、选择机位、保存截图，
再把截图作为 image node 放回原画布。

## 2. Entry And Lifecycle

### Entry node

- 节点显示 `3D导演台`、`搭建3D场景，截图作为构图参考` 和当前对象/机位数量；
- 主命令为 `进入导演台`；
- 事件必须 stop propagation，不能同时触发节点拖动；
- 打开时记录 source director node id，关闭时只清理 UI session id。

### Workspace mount

- `position: fixed; inset: 0`，位于所有 React Flow、导航和面板之上；
- workspace 打开时主画布继续挂载但不可接收 pointer/keyboard input；
- `Escape` 优先关闭 director 内部菜单/移动抽屉；无内部 overlay 时返回画布；
- 关闭后选中原 director node，原 viewport 不发生 fit/zoom/reset。

## 3. Information Architecture

### Top bar

- 左：返回图标、`3D导演台`、当前场景名；
- 中：`导演视角 / 机位视角` segmented control；
- 右：capture status、关闭图标。

### Left object tree

- 搜索框；
- `角色`、`场景物体`、`摄像机` 三组；
- row：kind icon、名称、visibility 命令；
- 选中 row 与 R3F 物体和 Inspector 同步；
- 空白 viewport click 回到 scene inspector。

### Central viewport

- 真实 R3F `<Canvas>`，`preserveDrawingBuffer: true`；
- 环境色、主光、补光、地面和 grid；
- 初始可辨识场景：角色代理、桌、道具、背景体块和 camera rig；
- director mode 使用 OrbitControls；
- camera mode 使用 active shot position/target/FOV；
- selected object 使用轻量高亮和 axis helper；capture 时临时隐藏。

### Viewport toolbar

- transform mode：移动 / 旋转 / 缩放；
- aspect ratio：`16:9 / 9:16 / 1:1`；
- thirds guide toggle；
- capture；
- 移动端 left/right panel toggle。

### Right inspector

- 无对象：scene background、ground、grid；
- character/prop：名称、颜色、visible、position/rotation/scale；
- camera：名称、active state、position、target 和 FOV；
- numeric fields 使用固定三列 axis grid，不因数值长度改变布局。

## 4. Director Domain

```ts
type DirectorObjectKind = "character" | "prop" | "camera";
type DirectorViewMode = "director" | "camera";
type DirectorTransformMode = "translate" | "rotate" | "scale";
type DirectorAspectRatio = "16:9" | "9:16" | "1:1";

interface DirectorTransform {
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
}
```

Camera shot 同时具有 tree object 和 authoring record 语义，但第一纵切可以由
一个 camera object 持有 `target` 与 `fov`，后续时间轴批次再拆 typed track。

## 5. Selection Contract

| Action | Result |
|---|---|
| click tree row | select matching object; route Inspector |
| click R3F mesh | select matching object; route Inspector |
| click empty viewport | clear object selection; show scene Inspector |
| click camera row | select camera and make it active |
| hide selected object | keep row selected, hide mesh, show hidden state in Inspector |
| switch camera mode | activate camera Inspector and render through active shot |

## 6. Capture Contract

1. Determine the visible frame rectangle from viewport size and selected aspect.
2. Set capture mode before the next render.
3. Hide grid, selection indicator, axis helper and camera rig.
4. Render one frame.
5. Crop the WebGL backing store using CSS-to-device-pixel scale.
6. Export PNG data URL.
7. Restore helpers and render normally.
8. Store capture metadata in `directorStore`.
9. On send, call one `canvasStore.createDirectorCapture` transaction.

Capture metadata:

```ts
interface DirectorCaptureMetadata {
  sourceNodeId: string;
  captureId: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: DirectorAspectRatio;
  width: number;
  height: number;
  createdAt: string;
  edgeId: string;
}
```

The returned image node:

- uses the PNG data URL as `imageUrl`;
- uses captured pixel dimensions;
- displays filename `导演台截图-<camera name>`;
- stores `directorCapture` metadata and `data-director-capture-node`;
- is placed in the first free slot to the right of the source director node;
- is connected by one default edge;
- can be undone/redone atomically.

## 7. Responsive Contract

### Desktop `>= 900px`

- topbar 48px;
- left rail 220px;
- right rail 288px;
- central viewport fills remaining width and height;
- rails are not cards and do not float over the viewport.

### Compact `< 900px`

- central viewport remains full-screen;
- tree and Inspector become mutually exclusive fixed drawers;
- viewport toolbar exposes icon buttons for both drawers;
- topbar title may truncate but view-mode control and close command remain reachable;
- no horizontal document overflow.

## 8. Visual Boundary

The visual language follows the current LibTV clone: neutral charcoal surfaces,
thin white-alpha dividers, cyan active state, compact 12-14px labels and 4-6px
control radii. Exact original Director Desk measurements are unresolved; these
values are clone calibration and must remain easy to replace after source runtime
inspection.

## 9. Accessibility And Testability

- icon-only commands have `aria-label` and `title`;
- segmented controls expose `aria-pressed`;
- tree rows expose selected/hidden state through data attributes;
- viewport has an accessible label independent of WebGL content;
- all stable selectors are defined in [`PLAN.md`](PLAN.md);
- the verifier must inspect WebGL pixels, not only canvas dimensions or DOM.

