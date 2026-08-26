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

## Verification

See [`../liblib-canvas-batch31-2026-08-26/PICTURE_EDIT_WORKFLOW.spec.md`](../liblib-canvas-batch31-2026-08-26/PICTURE_EDIT_WORKFLOW.spec.md)
and `scripts/verify-liblib-batch31.py`.
