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

## Main Reference Groups

- [`liblib-live-2026-08-25/`](../research/liblib-live-2026-08-25/README.md) indexes LibTV source audits.
- [`liblib-seedance-2.5-2026-08-25/`](../research/liblib-seedance-2.5-2026-08-25/README.md) indexes Seedance evidence.
- FrameOS-specific reference images are grouped under `frameos/`; their source research index is [`../research/frameos/`](../research/frameos/README.md).
- Batch screenshots are listed in each batch `IMPLEMENTATION.md` and, when visually inspected, its `SCREENSHOT_ANALYSIS.md`.
