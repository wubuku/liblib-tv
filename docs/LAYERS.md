# Layer Model

This is a frontend-specific dependency model. It describes ownership and allowed direction, not a runtime framework feature.

## Layer Definitions

| Layer | Content | Example paths |
|---|---|---|
| L0 Types | data contracts and route-specific types | `src/types/` |
| L1 Pure | pure helpers, transforms and class utilities | `src/lib/` |
| L2 State | Zustand stores and graph transactions | `src/store/` |
| L3 UI | reusable visual components, nodes, panels and dialogs | `src/components/` |
| L4 Route | Next.js pages/layouts and React Flow orchestration | `src/app/` |
| L5 Evidence | research, specs, screenshots and implementation records | `docs/` |

## Dependency Rules

```text
L4 Route -> L3 UI -> L2 State -> L1 Pure -> L0 Types
L4 Route -> L0 Types
L3 UI -> L1 Pure / L0 Types
L2 State -> L1 Pure / L0 Types
L5 Evidence describes and constrains all code layers
```

- L0 must not import UI, stores or route code.
- L1 must remain browser-independent unless the helper explicitly belongs to a browser boundary.
- L2 owns mutations to graph state; components call actions rather than duplicating transactions.
- L3 may use route-specific stores but LibTV components must not import `frameosStore`, and FrameOS components must not import `canvasStore`.
- L4 wires route behavior and registers node/edge types; it should not become a second store.
- L5 is not imported by runtime code. It is the source-of-truth record for evidence and decisions.

## Route Isolation Matrix

| From \ To | LibTV route | FrameOS route | Shared |
|---|---:|---:|---:|
| LibTV store/components | ✅ | ❌ | only generic primitives |
| FrameOS store/components | ❌ | ✅ | only generic primitives |
| React Flow / `cn` / types | ✅ | ✅ | ✅ |
| Route-specific CSS | ❌ | ❌ | only through explicit shared tokens |

## Cross-Cutting Rules

- `src/app/globals.css` affects both routes; any React Flow selector change requires checking both routes.
- `DeletableEdge` and `FrameosEdge` are separate renderers even when their visual techniques overlap.
- `canvasStore` and `frameosStore` are intentionally not unified with a mode flag.
- `docs/research/` may reference source-site structure, but source-site implementation assumptions must not leak into runtime code without an explicit clone decision.
