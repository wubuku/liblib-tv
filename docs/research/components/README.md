# Component Specifications

> Component-level contracts for the LibTV clone. Read the matching spec before changing a component or node.

## How To Find A Spec

| Area | Specs |
|---|---|
| Shell and navigation | `TopNavBar`, `CanvasTabDropdown`, `LeftSidebar`, `BottomToolbar`, `AssetManagerPanel`, `StoryboardBoard`, `AgentDrawer` |
| Panels and dialogs | `AddNodePanel`, `MainEntryPanels`, `CameraConfigDialog`, `CameraMovementDialog`, `KeyboardShortcutsDialog` |
| Image workflow | `ImageNode`, `ImageEditPanel` |
| Video workflow | `VideoNode`, `VideoGenerationPanel`, `VideoProcessingToolbar`, `SegmentReshootPanel` |
| Graph behavior | `DeletableEdge`, `StoryboardGroupNode` |
| Specialized nodes | `ScriptNode`, `ScriptExecutionNode`, `TextNode`, `AudioNode`, `ShotBreakdownNode`, `VideoClipNode` |

Files are named `<Component>.spec.md`. Batch-specific contracts live in the corresponding `docs/research/liblib-canvas-batchN-*` directory.
