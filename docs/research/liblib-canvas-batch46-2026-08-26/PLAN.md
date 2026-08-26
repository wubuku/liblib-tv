# Batch 46 Plan

## Goal

Complete a source-backed Director screenshot-management loop:

```text
capture several compositions
  -> open the camera screenshot tab
  -> inspect grouped thumbnails and empty state
  -> open/close a full-screen preview
  -> send one or all captures to the canvas
  -> confirm and clear local screenshot records
```

## Value Choice

| Candidate | Current evidence | Existing foundation | Decision |
|---|---|---|---|
| camera screenshot gallery | exact current locale keys + fixed upstream panel | capture records, PNG preview, graph return | implement |
| model/environment library | source vocabulary + upstream breadth | no asset persistence | defer |
| ordinary canvas overlays | strong old source contracts | existing clone has later gap work | defer until Director capture slice closes |

## In Scope

- camera Inspector `属性 / 摄像机截图` tabs;
- empty state `暂无摄像机截图`;
- camera-labeled capture groups and sequential display names;
- compact thumbnail grid with selected/current state;
- single-item send and existing sent-state preservation;
- full-screen image viewer with close, Escape and bounded zoom controls;
- `全部清空` confirmation and local record clearing;
- `发送到画布` bulk return for unsent captures;
- desktop/mobile panel bounds and no-overflow verification.

## Out Of Scope

- remote persistence, upload, host bridge or download history;
- deleting already returned React Flow nodes when local records are cleared;
- exact LibTV panel pixels or unobserved camera-document schema;
- multi-camera authoring beyond grouping records by the existing `cameraName`;
- capture generation presets such as four-view/twelve-view;
- undo/redo for local Director gallery state.

## Ordered Work

1. Protect current locale and fixed-upstream evidence.
2. Extend `directorStore` with capture selection and clear actions.
3. Replace the single preview with a camera screenshot gallery.
4. Add a source-shaped viewer and bulk return/clear flows.
5. Add stable selectors and focused Batch 46 Playwright.
6. Inspect the generated contact sheet once and write the screenshot ledger.
7. Run Batch 35-46 regression, docs check, `npm run check` and diff check.
8. Update maturity/stable docs, commit and push.

## Acceptance Gates

- no-capture camera state visibly exposes the source-backed empty state;
- two captures render as camera-labeled gallery cards;
- selecting a card changes the active preview;
- viewer opens, closes by button/Escape/backdrop and remains in document bounds;
- zoom controls change viewer scale without page overflow;
- single send marks only the selected capture and creates one graph node/edge;
- bulk send creates one graph node/edge per unsent capture and does not duplicate sent records;
- clear-all requires confirmation, clears local records and leaves returned graph nodes;
- desktop/mobile camera gallery has no runtime errors or horizontal overflow.

## Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-camera-tabs]` | camera Inspector tabs |
| `[data-director-camera-tab="captures"]` | screenshot tab |
| `[data-director-capture-gallery]` | gallery root |
| `[data-director-capture-empty]` | no-capture state |
| `[data-director-capture-group]` | camera-labeled group |
| `[data-director-capture-item]` | thumbnail card |
| `[data-director-capture-item-selected]` | active card state |
| `[data-director-capture-viewer]` | full-screen viewer |
| `[data-director-capture-viewer-close]` | viewer close |
| `[data-director-capture-clear-all]` | clear-all command |
| `[data-director-capture-clear-confirm]` | clear confirmation |
| `[data-director-capture-send-all]` | bulk canvas return |
