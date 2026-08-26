# Batch 32 Screenshot Analysis Ledger

> 状态：实施前台账。当前没有新增原站深度动作捕捉截图；先登记已有字符串
> 证据和 clone 截图计划，避免把未识别画面写成事实。

## Reused Evidence

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch28-2026-08-25/SOURCE_EVIDENCE.md`](../liblib-canvas-batch28-2026-08-25/SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch29-2026-08-25/PLAN.md`](../liblib-canvas-batch29-2026-08-25/PLAN.md)
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)

## Recognition Policy

2026-08-26 已对本批新增 clone contact sheet 做一次识别，后续先读本节，
不要重复打开同一张 contact sheet：

- viewport、duration state、resolution state 和截图路径；
- toolbar trigger、node-anchored panel、source summary 和 pending output 层级；
- default guard、busy、submit、graph undo/redo 和 mobile clipping；
- source fact、inference、clone calibration 和 clone-only decision；
- 未取得的原站 geometry 不通过 clone 截图补写。

## Planned Screenshots

| State | Planned path | Status |
|---|---|---|
| default 30s guard | `docs/design-references/liblib-clone-batch32-depth-guard-929-2026-08-26.png` | captured |
| 10s panel 720P | `docs/design-references/liblib-clone-batch32-depth-panel-720p-929-2026-08-26.png` | captured |
| 10s panel 1080P | `docs/design-references/liblib-clone-batch32-depth-panel-1080p-929-2026-08-26.png` | captured |
| pending graph | `docs/design-references/liblib-clone-batch32-depth-graph-929-2026-08-26.png` | captured |
| mobile clipping | `docs/design-references/liblib-clone-batch32-depth-mobile-390-2026-08-26.png` | captured |

## Recognition Result

Contact sheet：
`docs/design-references/liblib-clone-batch32-depth-motion-contact-sheet-2026-08-26.png`

| State | Direct screenshot observation | Classification |
|---|---|---|
| 30s guard | ready video remains selected; top processing toolbar includes the new depth action; a compact dark feedback chip appears over the media near the top; no lower depth panel or new graph node is visible | clone behavior implemented from source-backed duration-limit semantics |
| 10s / 720P | the ready video keeps its top toolbar; a node-centered dark panel is visibly attached below the video; title, cyan depth icon, intro copy, source summary and a two-option resolution control are visible; `720P` is selected | clone calibration; intro/title are source-backed strings |
| 10s / 1080P | same lower panel geometry and hierarchy as 720P; selection moves to `1080P` without changing the source node or the top toolbar | clone-only local parameter state |
| pending graph | source video remains selected with the lower generation editor visible; pending depth reference cards appear to the right and are connected by direct edges; outputs use dark placeholder bodies rather than the source poster | clone-only pending graph and media placeholder |
| mobile | the 390px viewport naturally clips the wide top toolbar and lower node panel at the canvas edge; the panel stays node-centered and no document-level horizontal overflow is introduced | clone calibration consistent with existing selected-node overlay contract |

### Layer And Geometry Notes

- The top toolbar is one horizontal layer above the selected video.
- The depth panel is a separate lower `NodeToolbar`, centered on the same node.
- The panel is narrower than the processing toolbar and contains a source summary
  row followed by the resolution control row.
- The pending graph image is a fit-view capture; the lower generation editor remains
  attached to the source while the derived pending nodes sit to the right.
- The mobile capture intentionally preserves natural clipping instead of recentering
  overlays into the browser viewport.

### Evidence Limits

These screenshots verify the clone's current behavior only. They do not add
original-site evidence for exact panel width, toolbar order, animation timing,
resolution option completeness, result media or unresolved source duration limits.
