# Glossary

| Term | Definition | Related code/docs |
|---|---|---|
| LibTV | The `liblib.tv/canvas` source product being reverse-engineered | `/`, `canvasStore`, `docs/research/liblib-live-*` |
| FrameOS | The `frameos.cn` source product being reverse-engineered | `/frameos/*`, `frameosStore`, `docs/research/frameos/` |
| Canvas | The infinite React Flow workspace containing nodes and edges | `src/app/page.tsx`, FrameOS page |
| Node | A graph item such as image, video, script or text | `src/components/nodes/` |
| Edge | A connection between two nodes | `DeletableEdge`, `FrameosEdge` |
| Handle | React Flow connection endpoint; in LibTV it visually renders the `+` affordance | `Handle`, `globals.css` |
| Parent-child | A node hierarchy represented by `parentId` and relative position | video group, `canvasStore` |
| Floating UI | Toolbar or editor anchored to a selected node or viewport | `ImageToolbar`, `ImageEditPanel`, FrameOS overlays |
| NodeToolbar | React Flow overlay rendered outside the zoomed node layer | `src/components/ImageToolbar.tsx` |
| Prompt | Text instruction used by a generation/editor panel | image/video panels, FrameOS prompt editor |
| AutoLink | Smart reference suggestion that maps canvas assets into Prompt references | image/video research and local prototype |
| Organize | Source-like command that repositions current graph topology | `liblibOrganize`, Batch 7 |
| Batch | A bounded research/implementation/verification unit with durable handoff docs | `docs/research/liblib-canvas-batch*` |
| Source fact | Directly observed source-site DOM, JSON, screenshot or interaction | `docs/research/` |
| Inference | A behavior model derived from multiple source facts | specs and implementation records |
| Clone decision | A local prototype choice made where source evidence is incomplete | component specs |
| Screenshot ledger | Written record of a screenshot's state, geometry, evidence and uncertainty | `SCREENSHOT_ANALYSIS.md` |
| React Flow | `@xyflow/react` graph/canvas primitive used by both routes | `src/app/`, `src/components/` |
| `canvasStore` | LibTV Zustand store for canvases, graph, selection, viewport and history | `src/store/canvasStore.ts` |
| `uiStore` | LibTV Zustand store for panels, tools, modes, toggles and zoom | `src/store/uiStore.ts` |
| `frameosStore` | Independent FrameOS Zustand store for graph, prompt, history and menus | `src/store/frameosStore.ts` |
| DEBUG-only | A developer convenience intentionally excluded from source-site claims | `FrameosNodeEditPanel` |
| Prototype boundary | A feature is visually/interactionally mocked without a real backend | README, Architecture |
