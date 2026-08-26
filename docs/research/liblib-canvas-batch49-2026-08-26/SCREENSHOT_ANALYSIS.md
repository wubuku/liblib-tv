# Batch 49 截图识别台账

> 本文件记录本批截图的唯一一次视觉识别结果。截图是当前 clone 的验证产物，
> 不是 LibTV authenticated source screenshot；上游尺寸和颜色只用于校准。
> 后续复核先读本文件，不重复打开同一 contact sheet。

## Capture Metadata

| 项目 | 值 |
|---|---|
| source | current LibTV clone, local dev server |
| capture date | 2026-08-26 batch naming convention |
| desktop viewport | `1440×900` |
| mobile viewport | `390×844` |
| zoom | browser default, device scale factor `1` |
| visual artifact | [`liblib-clone-batch49-director-gizmo-contact-sheet-2026-08-26.png`](../../design-references/liblib-clone-batch49-director-gizmo-contact-sheet-2026-08-26.png) |
| individual artifacts | default / X positive / camera mode / capture hidden / mobile，均在 `docs/design-references/` |
| evidence companions | Batch 49 专项 Playwright、DOM bounding boxes、R3F canvas pixel checks |

## Visual Read

| State | 识图结果 | 证据性质 |
|---|---|---|
| DEFAULT | 深色三列导演台工作区中，坐标控件位于中央 R3F 视口的右上角；构图框、地面网格、场景对象、对象树、Inspector 和时间轴仍保持原有层级。控件视觉由红/绿/蓝三轴组成，未出现额外不透明面板。 | screenshot fact + DOM-backed placement |
| X POSITIVE | 场景切换到沿 X 轴的侧向构图，人物、桌子和墙面关系明显改变；构图框、底部工具条、对象树、Inspector 和时间轴未因切换而重排。右上角控件仍存在，轴向视觉随相机方向改变。 | screenshot fact + camera-command verifier |
| CAMERA MODE | 顶部“机位视角”处于选中状态，中央画面由 active camera 构图控制；坐标控件仍可见，说明它是 viewport orientation feedback，不是 Director-only object overlay。Inspector 保持相机相关内容。 | screenshot fact + view-mode DOM |
| CAPTURE HIDES GIZMO | 截图过程中右上角坐标控件消失；capture viewer 在右下方出现，主工作区和时间轴仍在后方。该状态没有看到 gizmo 进入 capture 输出路径的证据。 | screenshot fact + capture state DOM |
| MOBILE | `390px` 宽视口下，顶部导演台 header、左/右面板入口、右上角坐标控件、中央构图框和底部工具条均在 viewport 内；时间轴位于底部，未出现水平滚动或控件压出边界。 | screenshot fact + mobile bounds verifier |

## Geometry Read

- DOM `[data-director-viewport-gizmo]` measured `80×80px` on desktop and
  remains wholly inside `[data-director-viewport]`.
- Desktop overlay is `20px` from the viewport top/right calibration edge.
- Six DOM buttons are `15×15px`; their projected centers move with the current
  camera snapshot and their `z-index` follows gizmo-local depth.
- The screenshot inspection shows the axis heads remain compact enough not to
  cover the bottom toolbar or the right Inspector.
- The mobile screenshot confirms the overlay remains inside the narrow viewport;
  the verifier also checks each hit button's bounding box against the overlay.

## Behavior Read

- A real mouse click on `X 正向` changes the main WebGL composition to the
  positive X direction.
- DOM dispatch checks cover all six semantic directions. Back-facing axes can
  be visually occluded by the front-facing axis at an exact cardinal view,
  matching the depth-ordered gizmo model; this is not treated as a second
  toolbar.
- Axis changes leave Director object state, selection state and timeline state
  unchanged.
- In `camera` mode, an axis command switches back to `director` mode before
  applying the clone-local Director snapshot; it does not mutate the active
  camera object.
- During path drawing and phone-camera recording, the gizmo remains visual but
  its six buttons are disabled. During capture/export, the gizmo overlay is
  unmounted.

## Uncertainty and Non-Claims

- These screenshots do not prove current LibTV production CSS, renderer choice
  or source-side gizmo DOM.
- They do not prove drag-to-orbit, face/corner selection, camera persistence or
  timeline keyframe integration.
- The capture-hidden screenshot proves clone overlay lifecycle only; it is
  paired with the separate WebGL capture path and does not independently prove
  pixel-level absence from a remote source capture.
