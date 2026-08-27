# PictureEditPanel

## Purpose

`src/components/PictureEditPanel.tsx` is the shared ready-video lower editor for
`主体消除`、`主体修改` and `主体替换`. It owns normalized mark editing and local
history; graph mutation belongs to `canvasStore.createPictureEdit`.

## Evidence Boundary

The source bundle confirms the three modes, four active tools, mark fields, limits,
mode-specific requirements and visible copy. It does not provide a complete saved
editor screenshot in the current research bundle. Panel geometry, marker appearance,
candidate labels and local replacement feedback are therefore explicitly clone
calibration.

## Structure

```text
PictureEditPanel
├── normalized mark overlay in source video body
├── lower node-anchored editor
│   ├── mode/counter header
│   ├── point/box/brush/eraser tools
│   ├── undo/redo/reset
│   ├── selected mark candidate/details
│   ├── modify description or replace source
│   └── submit/reason/status
└── local editor history
```

## Mode Rules

| Mode | Max | Required |
|---|---:|---|
| subjectRemove | 4 | one or more marks |
| subjectModify | 4 | description for every mark |
| subjectReplace | 2 | replacement for every mark |

## Prototype Boundary

- normalized marks are UI state, not segmentation masks;
- candidates are local labels;
- upload/history buttons do not access files or account data;
- submit creates a pending graph placeholder only;
- no real video, task ID, power calculation or polling.

## Editor Session Boundary

[`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)
classifies this surface as `RECORD_EDITOR`:

- pointermove mutates the working draft and one completed pointer interaction
  creates at most one local history entry;
- local history is capped at 30 entries and never writes graph history before
  submit;
- submit deep-clones marks and `canvasStore.createPictureEdit` owns the eventual
  one-step graph transaction;
- current description and replacement updates use `replaceMarks` rather than
  `commitMarks`, so not every semantic detail edit is represented in local undo;
- the 520ms component timer is a local simulation, not a durable operation ID.

The missing detail-history ownership and production async handoff remain
implementation work; the current visual/geometry contract is unchanged.

## Verification

See [`../liblib-canvas-batch31-2026-08-26/PICTURE_EDIT_WORKFLOW.spec.md`](../liblib-canvas-batch31-2026-08-26/PICTURE_EDIT_WORKFLOW.spec.md)
and `scripts/verify-liblib-batch31.py`.

## Stable Selectors

- `[data-picture-edit-panel]`
- `[data-picture-edit-close]`
- `[data-picture-edit-mode]`
- `[data-picture-edit-count]`
- `button[data-picture-edit-tool]`
- `[data-picture-edit-mark-overlay]`
- `[data-picture-edit-mark]`
- `[data-picture-edit-mark-tool]`
- `[data-picture-edit-mark-frame]`
- `[data-picture-edit-mark-handle]`
- `[data-picture-edit-description]`
- `[data-picture-edit-replacement]`
- `[data-picture-edit-replacement-selected]`
- `[data-picture-edit-history="undo"]`
- `[data-picture-edit-history="redo"]`
- `[data-picture-edit-reset]`
- `[data-picture-edit-submit]`
- `[data-picture-edit-spinner]`
- `[data-picture-edit-submit-reason]`
- `[data-picture-edit-output]`
