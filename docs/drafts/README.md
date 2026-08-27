# Draft Documents

> Active plans and designs that are still being iterated.

Lifecycle status and promotion/supersession rules are defined in
[`DOCUMENT_LIFECYCLE.md`](../DOCUMENT_LIFECYCLE.md).

## Rules

- Use a descriptive topic name; do not use `NOTES`, `TEMP` or `TASK_PROGRESS`.
- Put implementation plans here before code changes when no existing batch directory is appropriate.
- Include status, scope, evidence, decisions, acceptance criteria and next action.
- When a plan is completed, keep the implementation result with its batch history or promote stable guidance into `docs/`.

## Current Drafts

| Draft | Scope | Status |
|---|---|---|
| [`LIBTV_MEDIA_RENDITION_GEOMETRY_RESEARCH_PLAN_2026-08-27.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_RESEARCH_PLAN_2026-08-27.md) | Open Canvas/LibTV intrinsic media、selected output、generation aspect、node frame、measured geometry 与 per-surface crop/fit 权威 | `ACTIVE` / documentation only |

Completed Open Canvas research plans, including media ingress/resource lifecycle and editor session/commit/history, are retained with their evidence and handoff history under [`../research/open-canvas-2026-08-26/`](../research/open-canvas-2026-08-26/README.md). The active media-rendition plan will be promoted there after its dated audit, stable contract and governance chain are complete.

Active research/implementation batches under `docs/research/liblib-canvas-batchN-*` carry their own `PLAN.md` and are indexed from [`../research/README.md`](../research/README.md).
