# Design References

> Dated screenshots from source sites and local clone verification. These are evidence artifacts, not the current UI source of truth.

## Naming

| Prefix | Meaning |
|---|---|
| `liblib-original-*` | LibTV source-site screenshot |
| `liblib-clone-*` | LibTV clone screenshot |
| `frameos-cn-*` / `original-*` | FrameOS source-site screenshot |
| `clone-*` | FrameOS clone screenshot |
| `*-batchN-*` | Batch-specific verification or diagnostic screenshot |

## Usage Rules

- Search `docs/research/` for a matching `SCREENSHOT_ANALYSIS.md` before visually reopening a screenshot.
- Use DOM/JSON measurements when exact geometry matters.
- Treat screenshots as dated observations with a viewport and interaction state.
- Do not call a screenshot “current” solely because its filename contains `final` or `after`.
- New screenshot states must be linked from the relevant research or component spec.

## Git Policy

- `docs/design-references/` is a versioned evidence directory, not an ignore
  target. Tracked source/clone screenshots must remain available for agent
  handoff and visual regression history.
- New batch screenshots should be named with their batch, viewport and date,
  and committed together with a `SCREENSHOT_ANALYSIS.md` ledger.
- Temporary screenshots outside the evidence directory use the existing
  root-level ignore patterns such as `verify-*.png` and `test-*.png`.

## Main Reference Groups

- [`liblib-live-2026-08-25/`](../research/liblib-live-2026-08-25/README.md) indexes LibTV source audits.
- [`liblib-seedance-2.5-2026-08-25/`](../research/liblib-seedance-2.5-2026-08-25/README.md) indexes Seedance evidence.
- [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](../research/open-canvas-2026-08-26/LIBTV_SOURCE_FRESHNESS_2026-08-27.md) interprets the 41% standard-image source screenshot and same-frame DOM geometry.
- [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](../research/open-canvas-2026-08-26/LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md) interprets the current 35-row video model catalog top/bottom screenshots and structured DOM audit.
- [`liblib-canvas-batch29-2026-08-25/`](../research/liblib-canvas-batch29-2026-08-25/SCREENSHOT_ANALYSIS.md) indexes the video frame-capture top menu, player camera, graph, selected output and mobile ledger.
- FrameOS-specific reference images are grouped under `frameos/`; their source research index is [`../research/frameos/`](../research/frameos/README.md).
- Batch screenshots are listed in each batch `IMPLEMENTATION.md` and, when visually inspected, its `SCREENSHOT_ANALYSIS.md`.
