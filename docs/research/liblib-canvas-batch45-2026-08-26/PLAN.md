# Batch 45 Plan

## Goal

Complete a source-backed Director Desk group-authoring loop:

```text
multi-select characters or add crowd array
  -> create/select explicit group
  -> inspect and transform the whole group
  -> add/update a group timeline track
  -> scrub/play deterministic member motion
  -> ungroup without deleting members
```

## Scope

### In scope

- explicit serializable character groups;
- single selection, Shift multi-selection and selected-group state;
- generic group and ungroup actions;
- rows/columns/spacing crowd creation;
- expandable group rows with member previews;
- group inspector name and transform controls;
- R3F group selection and transform gizmo;
- typed group tracks/keyframes and interpolation;
- focused desktop/mobile Playwright verification;
- screenshot ledger, cross-batch regression and stable docs.

### Out of scope

- source-exact crowd limits or placement math;
- persistence, clipboard and undo;
- group visibility/lock aggregation;
- group pose/color batch editing;
- group motion paths;
- arbitrary mixed prop/camera groups;
- backend or collaboration behavior.

## Ordered Work

1. Protect current source evidence and fixed-upstream archaeology.
2. Add pure group math:
   - derived anchor;
   - finite fan-out transform;
   - centered crowd positions.
3. Extend the store:
   - `groups`, `selectedObjectIds`, `selectedGroupId`;
   - selection/group/crowd actions;
   - group transform and auto-keyframe;
   - `group` timeline-track variant.
4. Extend the object tree:
   - Shift selection;
   - group aggregation;
   - expand/collapse;
   - group/ungroup commands.
5. Extend the viewport:
   - crowd entry and compact panel;
   - click-to-select group members;
   - group transform rig.
6. Extend the inspector with group name/transform editing.
7. Extend timeline labels, selection, add-track and add-keyframe routing.
8. Add `scripts/verify-liblib-batch45.py`.
9. Run one focused visual inspection and immediately record
   `SCREENSHOT_ANALYSIS.md`.
10. Run Batch 35-45 regression, docs check, full check and diff check.
11. Update maturity/stable docs, commit and push.

## Acceptance Gates

- a `2x3` crowd creates six finite, unique character objects and one group;
- group row selects all members and expands/collapses;
- Shift selection plus `打组` creates a valid group with at least two members;
- `解组` preserves members and removes the group/its group track;
- inspector and R3F gizmo move the whole group without collapsing offsets;
- group track uses `kind: "group"` and stable group target ID;
- group keyframes scrub/play to visibly different R3F pixels;
- desktop and `390x844` crowd panels remain inside the document;
- no runtime console/page/request errors;
- previous Director batches and repository gates remain green.

## Protection Commits

- [x] plan/evidence
- [x] implementation
- [x] focused verification
- [x] final documentation/regression

## Closeout

Focused browser verification, Batch 35-45 serial regression,
`npm run docs:check`, `npm run check` and `git diff --check` all passed on
2026-08-26. The implementation and repository history are recorded in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md).
