# Batch 45 Implementation Log

> Status: focused implementation and browser verification complete on
> 2026-08-26. Repository-wide regression and final documentation closeout are
> tracked separately below.

## Protected Context

- current LibTV locale proves group/ungroup, crowd-array fields, expansion and
  group keyframes;
- current Director chunk proves explicit `characterGroups`, `groupTracks` and
  `memberOffsets`;
- current import logic de-duplicates group members and rejects groups smaller
  than two;
- fixed upstream proves a workable derived-anchor/fan-out R3F pattern;
- fixed upstream has no timeline, so group animation is clone-owned but
  source-required.

## Implementation

- [x] current locale extraction
- [x] current business-chunk archaeology
- [x] fixed upstream archaeology
- [x] plan and component specification
- [x] pure group math
- [x] store and timeline model
- [x] tree, viewport and Inspector UI
- [x] focused browser verification
- [x] screenshot analysis
- [ ] cross-batch regression and stable documentation closeout

### Code Surface

- `src/components/director/directorGroupMath.ts`
  - derived group anchor;
  - finite member offsets;
  - translation/rotation/scale fan-out;
  - centered X/Z crowd positions.
- `src/store/directorStore.ts`
  - serializable `groups`, multi-selection and selected-group state;
  - group/ungroup and crowd-array actions;
  - group transform updates and auto-keyframes;
  - typed `kind: "group"` tracks with independent keyframes;
  - group sampling applied after ordinary object tracks.
- `src/components/director/DirectorObjectTree.tsx`
  - Shift character selection;
  - group rows, member previews, expand/collapse and group commands.
- `src/components/director/DirectorViewport.tsx`
  - crowd panel and bounded inputs;
  - grouped-character viewport selection;
  - R3F group TransformControls.
- `src/components/director/DirectorInspector.tsx`
  - group name, member count/crowd metadata and transform fields.
- `src/components/director/DirectorTimeline.tsx`
  - group track icon, target metadata and keyframe rendering.

## Focused Verification

Command:

```bash
LIBLIB_BASE_URL=http://localhost:3000 \
  python3 scripts/verify-liblib-batch45.py
```

Result:

```text
Batch 45 director group/crowd verification passed.
```

The verifier covers:

- 2×3 crowd creation with six unique finite character objects;
- crowd panel bounds on desktop and mobile;
- group selection, expansion and member previews;
- group Inspector selection and anchor transform editing;
- `kind: "group"` timeline track with stable group target and member offsets;
- keyframe creation at a second time and deterministic scrub pixel change;
- playback advancing the group timeline;
- ungroup preserving members and removing the group track;
- Shift multi-select followed by group/ungroup;
- zero console, page and request errors.

## Screenshot Ledger

The first visual pass is recorded in
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md). It covers the six focused
screenshots and the generated contact sheet. Do not reopen the full contact
sheet unless a new question is not answered by that ledger.

## Worktree Safety

Historical regression PNGs were already modified in the shared worktree before
Batch 45. The Batch 45 commit must stage only:

- Batch 45 source files;
- `scripts/verify-liblib-batch45.py`;
- Batch 45 research documents;
- the seven Batch 45 screenshots and contact sheet;
- the required stable documentation edits.

Do not revert or absorb unrelated historical PNG changes.

## Commits

- Plan/evidence protection: `56e822f`
- Focused implementation and verification: pending
- Repository-wide closeout: pending

## Interruption Handoff

After repository-wide closeout, read
[`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md) before selecting the next
Director batch. Keep source facts, fixed-upstream facts and clone calibration
separate.
