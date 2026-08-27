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
| Media ingress | A named user intent that introduces local bytes or attaches an existing media result/asset before graph projection | `LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md` |
| Temporary resource lease | Instance-scoped ownership of `File`/`Blob`/object URL used for probe or preview, with explicit transfer/release | `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`, `LIBTV-VR-021` |
| Stable asset | Reusable media identity whose lifetime is independent from one canvas node reference | Asset Manager research, `DEC-037` |
| Node media reference | A graph-owned reference to a stable asset/result/locator, not the bytes or asset registry record itself | node data contract, media ingress contract |
| Provisional projection | Operation-owned progress/error UI shown before a semantic graph plan is accepted; excluded from graph history/document | `OC-PATTERN-11`, `LIBTV-UIX-21` |
| Resource reachability | The set of graph/history/clipboard/editor/operation/asset/export owners that must be empty before release | media ingress contract, delete/async contracts |
| Editor session | One foreground editing lifetime bound to route/canvas generation, target/source baseline and one declared profile | `LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`, `DEC-038` |
| Editor baseline | Immutable, field/source-scoped semantic value captured when an editor session opens | editor session contract |
| Working draft | Session-owned mutable authoring state that has not yet been accepted into graph or async operation authority | `LIBTV-FIX-LOCAL-EDITOR-SESSION-01` |
| Local editor history | Undo/redo state owned by a custom foreground editor and excluded from semantic graph history until acceptance | `LIBTV-VR-022`, `OC-PATTERN-12` |
| Commit intent | A frozen, normalized request to accept one editor draft synchronously or hand it to async authority | editor session contract, async ingress contract |
| Baseline drift | A scoped owner/source change after editor open that requires explicit rebase, conflict or invalidation instead of silent draft overwrite | `DEC-038`, `LIBTV-EDS-I-019/020` |
| Media intrinsic dimensions | Decoded dimensions of one exact image/video output, with explicit provenance and validity; not request settings or node size | `LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md` |
| Selected output | The current candidate/version identity and its own metadata, distinct from a node's source collection or request aspect | `OC-PATTERN-13`, `DEC-039` |
| Semantic node frame | Graph-owned width/height policy for a media node's canvas frame; changes only through a declared semantic command | `LIBTV-MRG-I-013..018`, `LIBTV-VR-023` |
| Passive measured rect | Runtime observation of the rendered node shell used for selection and anchors; never evidence of user resize intent | React Flow `measured`, media geometry contract |
| Rendition profile | A named surface policy that binds media/output identity, frame role, fit, object position, clipping and fallback | `CANVAS_PRIMARY`, `DETAIL_INSPECTOR`, `EDITOR_FULL_MEDIA` |
| Frame policy | The declared authority that shapes a node frame: source media, request aspect, fixed type or explicit semantic frame | `SOURCE_MEDIA_SHAPED`, `REQUEST_ASPECT_SHAPED`, `TYPE_FIXED`, `EXPLICIT_SEMANTIC_FRAME` |
| Measurement epoch | Owner/generation/frame/rendition revision tuple used to reject stale DOM measurements and anchors | `DEC-039`, `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` |
