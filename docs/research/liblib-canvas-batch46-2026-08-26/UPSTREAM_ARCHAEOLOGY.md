# Batch 46 Upstream Archaeology

## Fixed Revision

```text
research/upstream/storyai-3d-director-desk
8c8bd361790be4d37158a7430365e65546e358fe
```

## Relevant Files

| File | Borrowable fact |
|---|---|
| `src/editor/panels/CameraPanel.tsx` | properties/captures tabs, camera-grouped captures, card actions, viewer, clear-all and send-all |
| `src/editor/store/directorStore.ts` | sequential per-camera capture naming and capture arrays |
| `src/styles/index.css` | gallery/grid/footer/viewer layout contracts |
| `src/editor/panels/CameraPanel.test.tsx` | empty state, action labels, viewer and footer behavior |

## Upstream Capture Model

The upstream camera stores:

```text
camera.captures[]
camera.lastCaptureUrl
```

Each capture receives a stable sequential name:

```text
{cameraName}-截图01
{cameraName}-截图02
...
```

The panel groups captures by camera and supports:

- camera properties / camera screenshots tabs;
- three-column thumbnail grid;
- per-card delete, send-to-canvas and view actions;
- full-screen preview dialog;
- zoom in/out, wheel zoom, drag when zoomed and download;
- Escape/backdrop/close-button viewer dismissal;
- empty state `暂无摄像机截图`;
- footer `清空全部` and `发送到画布`.

The upstream CSS tests also establish that the gallery is a scrollable right
Inspector surface with a fixed footer, and that the viewer is a full-screen
black overlay. Those dimensions and colors are upstream facts, not current
LibTV runtime measurements.

## Borrowing Decision

Borrow the interaction hierarchy and naming pattern. Keep the existing clone's
`DirectorCapture` payload and `canvasStore.createDirectorCapture` transaction,
because changing the clone to the upstream's camera-document schema would
unnecessarily cross the established `directorStore` boundary.

The clone will implement a bounded single-session gallery, not upstream host
bridge, download persistence or camera-document serialization.
