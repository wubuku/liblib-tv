# Component Specifications

> Component-level contracts for the LibTV clone. Read the matching spec before changing a component or node.

## Coverage First

Use [`COVERAGE_MATRIX.md`](COVERAGE_MATRIX.md) to map a source component to its
spec, batch evidence, verifier and current documentation gap. The matrix also
marks components covered by a parent/domain contract, legacy helpers, debug-only
surfaces and parallel WIP. Do not infer `SPEC_COMPLETE` merely because a file is
listed in `COMPONENT_INVENTORY.md`.

## How To Find A Spec

| Area | Specs |
|---|---|
| Shell and navigation | `TopNavBar`, `CanvasTabDropdown`, `LeftSidebar`, `BottomToolbar`, `AssetManagerPanel`, `StoryboardBoard`, `AgentDrawer` |
| Panels and dialogs | `AddNodePanel`, `MainEntryPanels`, `ToolboxPanel`, `CharacterLibraryPanel`, `HistoryPanel`, `SmartMattingPanel`, `VideoClipEditPanel`, `CameraConfigDialog`, `CameraMovementDialog`, `KeyboardShortcutsDialog` |
| Image workflow | `ImageNode`, `ImageEditPanel`, [`LibTVOverlayPositioning.contract.md`](LibTVOverlayPositioning.contract.md), [`LibTVAutoLink.contract.md`](LibTVAutoLink.contract.md) |
| Video workflow | `VideoNode`, `VideoGenerationPanel`, `VideoProcessingToolbar`, `SegmentReshootPanel`, `VideoContinuationSelector`, `SubtitleErasePanel`, `PictureEditPanel`, `DepthMotionCapturePanel` |
| Graph behavior | `DeletableEdge`, `StoryboardGroupNode` |
| Specialized nodes | `ScriptNode`, `ScriptExecutionNode`, `TextNode`, `AudioNode`, `ShotBreakdownNode`, `ShotBreakdownResultNode`, `VideoClipNode` |

The `PictureEditPanel` contract is also recorded in
[`PictureEditPanel.spec.md`](PictureEditPanel.spec.md).

Files are named `<Component>.spec.md`. Batch-specific contracts live in the corresponding `docs/research/liblib-canvas-batchN-*` directory.
