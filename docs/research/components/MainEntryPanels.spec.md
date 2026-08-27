# Main Entry Panels Specification

## Scope

This specification covers the six panels opened from the LibTV primary bottom toolbar: toolbox, material library, character library, history, keyboard shortcuts, and tutorial/help.

The authoritative live extraction is `docs/research/liblib-live-2026-08-25/panel-audit.json`. These panels do not share one generic sidebar geometry.

## Desktop Geometry (`929x874`)

| Component | Geometry | Presentation |
|---|---|---|
| `ToolboxPanel` | `480x460`, bottom `73px`, center shifted `-64px` | Anchored floating panel; 3-column scrolling preset grid |
| `MaterialLibraryPanel` | `240x163`, bottom `73px`, center shifted `-24px` | Anchored floating menu; two 52px commands |
| `CharacterLibraryPanel` | `793x710`, centered near `y=82` | Backdrop modal with detail and carousel sections |
| `HistoryPanel` | `90vw x calc(100vh - 160px)`, `y=80` | Backdrop modal with toolbar, tabs, date groups and grid |
| `KeyboardShortcutsDialog` | left/right `12px`, height `447px`, bottom `73px` | Anchored panel without backdrop; four columns |
| Tutorial menu | `104x154`, bottom `73px`, center shifted `+92px` | Anchored command menu |

## Interaction Contract

- Only one primary toolbar content panel may be open at a time.
- Opening add-node or shortcuts closes a locally open content panel; opening a content panel closes add-node and shortcuts.
- Opening Add Node or a primary content panel preserves the Asset drawer as a
  layout surface; closing that transient surface also preserves the drawer.
- Backdrop modals close from their explicit close button or backdrop.
- Anchored panels close from the triggering button or their close control.
- Character “应用到画布” uses the page-owned actual-host placement path, creates
  one visible `512x288` graph image frame with the selected character media data,
  records one history step and selects it.
- History filters, zoom, batch selection and favorite state are local prototype interactions.
- On narrow screens, anchored panels move above the stacked bottom toolbars; large modals constrain width without shrinking text until it overflows.

## Assets

Panel assets live under `public/images/liblib-panels`. Run `node scripts/download-liblib-panel-assets.mjs` to rebuild them from the extracted source URLs.

## Files

- `src/components/LeftSidebar.tsx`
- `src/components/ToolboxPanel.tsx`
- `src/components/MaterialLibraryPanel.tsx`
- `src/components/CharacterLibraryPanel.tsx`
- `src/components/HistoryPanel.tsx`
- `src/components/KeyboardShortcutsDialog.tsx`
- `src/store/canvasStore.ts`
