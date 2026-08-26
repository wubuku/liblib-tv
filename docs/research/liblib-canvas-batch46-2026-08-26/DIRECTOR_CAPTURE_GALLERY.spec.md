# Director Capture Gallery Specification

## Evidence Classification

| Contract | Basis |
|---|---|
| camera-labeled screenshot records | current LibTV locale |
| empty screenshot state | current LibTV locale |
| clear-all and confirmation | current LibTV locale |
| bulk send to canvas | current LibTV locale |
| preview close command | current LibTV locale |
| tabs, grouped cards and full-screen viewer | fixed upstream implementation |
| exact dimensions and colors | clone calibration |

## Domain Contract

The current clone keeps:

```ts
interface DirectorCapture {
  id: string;
  dataUrl: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: DirectorAspectRatio;
  width: number;
  height: number;
  createdAt: string;
  sentNodeId?: string;
}
```

The gallery derives a display label from `cameraName` and the capture's
position within that camera group. It does not change the established graph
metadata schema.

## Interaction Contract

- camera selection exposes `属性` and `摄像机截图` tabs;
- an empty gallery says `暂无摄像机截图`;
- thumbnails are grouped by camera label;
- clicking a card selects it and updates the current preview;
- clicking view opens a full-screen viewer;
- viewer supports close button, backdrop and Escape;
- clear-all opens a confirmation surface, then removes local capture records;
- clearing does not delete already returned React Flow nodes;
- single send reuses the existing one-capture graph transaction;
- bulk send creates one transaction per unsent capture and marks each sent;
- sent cards remain visible and are disabled for duplicate send.

## Visual Boundary

Borrow the upstream hierarchy: scrollable Inspector content, compact
thumbnail grid, fixed action footer and black full-screen viewer. Do not state
the upstream pixel values as LibTV source facts until the authenticated source
runtime is measured.
