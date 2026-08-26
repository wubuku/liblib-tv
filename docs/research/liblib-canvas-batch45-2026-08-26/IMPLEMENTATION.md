# Batch 45 Implementation Log

> Status: source evidence and implementation plan protected. Code work pending.

## Protected Context

- current locale proves group/ungroup, crowd-array fields, expansion and group
  keyframes;
- current Director chunk proves explicit `characterGroups`, `groupTracks` and
  `memberOffsets`;
- current import logic de-duplicates group members and rejects groups smaller
  than two;
- fixed upstream proves a workable derived-anchor/fan-out R3F pattern;
- fixed upstream has no timeline, so group animation is clone-owned but
  source-required.

## Progress

- [x] current locale extraction
- [x] current business-chunk archaeology
- [x] fixed upstream archaeology
- [x] plan and component specification
- [ ] pure group math
- [ ] store and timeline model
- [ ] tree, viewport and inspector UI
- [ ] focused browser verification
- [ ] screenshot analysis
- [ ] cross-batch regression and stable documentation

## Worktree Safety

Historical regression PNGs are already modified in the shared worktree.
Batch 45 commits must stage exact source, script, documentation and new Batch
45 screenshot paths only. Do not revert or absorb unrelated changes.

## Interruption Handoff

Continue from [`PLAN.md`](PLAN.md), beginning with pure group math and the store
model. Preserve the evidence distinctions in
[`DIRECTOR_GROUPS.spec.md`](DIRECTOR_GROUPS.spec.md).
