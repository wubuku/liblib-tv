# ScriptHeader Legacy Contract

## Current Status

`src/components/ScriptHeader.tsx` exists in the repository but is not imported or mounted anywhere under `src/`. It has no current runtime behavior or verification contract and must be treated as `LEGACY`, not as a visible LibTV component.

This status was confirmed by repository-wide source search on 2026-08-26. If the file is later mounted, this document must be replaced by current source evidence and a focused component contract.

## What The File Contains

The unused prototype renders a fixed top-center chip:

```text
document icon
第一集：咖啡馆对峙
two decorative cyan dots
```

Implementation facts:

- fixed `top: 60px`, centered horizontally, `z-index: 30`;
- title is constant component-local state rather than active canvas/script data;
- document icon is a hand-authored inline SVG;
- cyan dots are plain `<span>` elements, not React Flow `<Handle>` components;
- there are no props, commands, selectors, store reads or interaction states.

These are facts about dormant clone code, not LibTV source facts.

## Source Evidence Boundary

- The dated live audit confirms a script node titled `第一集：咖啡馆对峙` in the canvas graph.
- The same audit identifies the old clone's always-visible purple follow banner as visually dominant while the relevant source overlay is normally transparent/non-dominant.
- No current evidence requires a global fixed title chip above the canvas.
- The historical `PAGE_TOPOLOGY.md` description of `<ScriptHeader>` represented an earlier clone structure and has been corrected to mark it unmounted.

Do not infer a global script-follow feature from the script node title, and do not reintroduce an always-visible follow banner from old screenshots.

## Hard Boundaries

- Decorative dots must never substitute for real React Flow connection handles.
- Do not mount this component to “complete” the page topology without current source evidence.
- Do not read FrameOS breadcrumb or Director title state to populate a LibTV header.
- If a current source title/follow overlay is verified, define its owner, visibility state, Escape lifecycle, z-index and relationship to the script node before implementation.

## Verification Status

- No focused verifier references `ScriptHeader`.
- No current route screenshot requires it.
- `rg -n 'ScriptHeader' src` currently returns only its own declaration.

The absence of a mount is the current contract. Deleting the file would still require explicit code authorization and a separate usage/build check; this documentation-only batch does not modify it.
