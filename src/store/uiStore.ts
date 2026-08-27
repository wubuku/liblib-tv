import { create } from "zustand";
import {
  resolveLibTVBlockingForegroundSurface,
  type LibTVBlockingForegroundSurface,
} from "@/lib/libtvSelectionCommandContext";

export type PrimaryPanel =
  | "move"
  | "toolbox"
  | "material"
  | "character"
  | "history"
  | "tutorial";

export interface ImagePreviewState {
  canvasId: string;
  nodeId: string;
  filename: string;
  imageUrl: string;
  watermarkUrl?: string;
  width: number;
  height: number;
}

export interface ImageAnnotateState {
  canvasId: string;
  nodeId: string;
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}

export interface ImageElementEditState {
  canvasId: string;
  nodeId: string;
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}

interface UIState {
  // Panel visibility
  isAddNodePanelOpen: boolean;
  isCanvasDropdownOpen: boolean;
  isAssetPanelOpen: boolean;
  isToolboxPanelOpen: boolean;
  isMaterialPanelOpen: boolean;
  isCharacterPanelOpen: boolean;
  isHistoryPanelOpen: boolean;
  isShortcutsPanelOpen: boolean;
  isTutorialPanelOpen: boolean;
  isNotificationOpen: boolean;
  isUserMenuOpen: boolean;
  isSharePanelOpen: boolean;
  isAgentOpen: boolean;
  isZoomMenuOpen: boolean;
  activePrimaryPanel: PrimaryPanel | null;
  editorMode: "workbench" | "storyboard";
  canvasTool: "select" | "pan";
  activeDirectorNodeId: string | null;
  activeDirectorCanvasId: string | null;
  imagePreview: ImagePreviewState | null;
  imageAnnotate: ImageAnnotateState | null;
  imageElementEdit: ImageElementEditState | null;

  // Canvas settings
  showMinimap: boolean;
  showGrid: boolean;
  showEdges: boolean;
  snapToGrid: boolean;
  zoomLevel: number;

  // Actions
  toggleAddNodePanel: () => void;
  toggleCanvasDropdown: () => void;
  closeCanvasDropdown: () => void;
  toggleAssetPanel: () => void;
  toggleToolboxPanel: () => void;
  toggleMaterialPanel: () => void;
  toggleCharacterPanel: () => void;
  toggleHistoryPanel: () => void;
  toggleShortcutsPanel: () => void;
  toggleTutorialPanel: () => void;
  toggleNotification: () => void;
  toggleUserMenu: () => void;
  toggleSharePanel: () => void;
  toggleAgent: () => void;
  toggleZoomMenu: () => void;
  closeZoomMenu: () => void;
  togglePrimaryPanel: (panel: PrimaryPanel) => void;
  setPrimaryPanel: (panel: PrimaryPanel | null) => void;
  setEditorMode: (mode: "workbench" | "storyboard") => void;
  setCanvasTool: (tool: "select" | "pan") => void;
  openDirectorDesk: (nodeId: string, canvasId: string) => void;
  closeDirectorDesk: () => void;
  openImagePreview: (preview: ImagePreviewState) => void;
  closeImagePreview: () => void;
  openImageAnnotate: (annotate: ImageAnnotateState) => void;
  closeImageAnnotate: () => void;
  openImageElementEdit: (elementEdit: ImageElementEditState) => void;
  closeImageElementEdit: () => void;
  toggleMinimap: () => void;
  toggleGrid: () => void;
  toggleEdges: () => void;
  toggleSnapToGrid: () => void;
  setZoomLevel: (zoom: number) => void;

  // Close all panels
  closeTopForegroundSurface: () => LibTVBlockingForegroundSurface | null;
  closeAllPanels: () => void;
}

type OverlayState = Pick<
  UIState,
  | "isAddNodePanelOpen"
  | "isCanvasDropdownOpen"
  | "isAssetPanelOpen"
  | "isToolboxPanelOpen"
  | "isMaterialPanelOpen"
  | "isCharacterPanelOpen"
  | "isHistoryPanelOpen"
  | "isShortcutsPanelOpen"
  | "isTutorialPanelOpen"
  | "isNotificationOpen"
  | "isUserMenuOpen"
  | "isSharePanelOpen"
  | "isAgentOpen"
  | "isZoomMenuOpen"
  | "activePrimaryPanel"
  | "imagePreview"
  | "imageAnnotate"
  | "imageElementEdit"
>;

const closedOverlayState: OverlayState = {
  isAddNodePanelOpen: false,
  isCanvasDropdownOpen: false,
  isAssetPanelOpen: false,
  isToolboxPanelOpen: false,
  isMaterialPanelOpen: false,
  isCharacterPanelOpen: false,
  isHistoryPanelOpen: false,
  isShortcutsPanelOpen: false,
  isTutorialPanelOpen: false,
  isNotificationOpen: false,
  isUserMenuOpen: false,
  isSharePanelOpen: false,
  isAgentOpen: false,
  isZoomMenuOpen: false,
  activePrimaryPanel: null,
  imagePreview: null,
  imageAnnotate: null,
  imageElementEdit: null,
};

function closeTransientOverlays(
  state: Pick<UIState, "isAssetPanelOpen">,
): OverlayState {
  return {
    ...closedOverlayState,
    isAssetPanelOpen: state.isAssetPanelOpen,
  };
}

export const useUIStore = create<UIState>((set) => ({
  isAddNodePanelOpen: false,
  isCanvasDropdownOpen: false,
  isAssetPanelOpen: false,
  isToolboxPanelOpen: false,
  isMaterialPanelOpen: false,
  isCharacterPanelOpen: false,
  isHistoryPanelOpen: false,
  isShortcutsPanelOpen: false,
  isTutorialPanelOpen: false,
  isNotificationOpen: false,
  isUserMenuOpen: false,
  isSharePanelOpen: false,
  isAgentOpen: false,
  isZoomMenuOpen: false,
  activePrimaryPanel: null,
  editorMode: "workbench",
  canvasTool: "select",
  activeDirectorNodeId: null,
  activeDirectorCanvasId: null,
  imagePreview: null,
  imageAnnotate: null,
  imageElementEdit: null,

  showMinimap: false,
  showGrid: true,
  showEdges: true,
  snapToGrid: false,
  zoomLevel: 54,

  toggleAddNodePanel: () =>
    set((state) => ({
      ...closeTransientOverlays(state),
      isAddNodePanelOpen: !state.isAddNodePanelOpen,
    })),

  toggleCanvasDropdown: () =>
    set((state) => ({
      ...closedOverlayState,
      isCanvasDropdownOpen: !state.isCanvasDropdownOpen,
    })),

  closeCanvasDropdown: () => set({ isCanvasDropdownOpen: false }),

  toggleAssetPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isAssetPanelOpen: !state.isAssetPanelOpen,
    })),

  toggleToolboxPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isToolboxPanelOpen: !state.isToolboxPanelOpen,
      activePrimaryPanel: state.activePrimaryPanel === "toolbox" ? null : "toolbox",
    })),

  toggleMaterialPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isMaterialPanelOpen: !state.isMaterialPanelOpen,
      activePrimaryPanel: state.activePrimaryPanel === "material" ? null : "material",
    })),

  toggleCharacterPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isCharacterPanelOpen: !state.isCharacterPanelOpen,
      activePrimaryPanel: state.activePrimaryPanel === "character" ? null : "character",
    })),

  toggleHistoryPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isHistoryPanelOpen: !state.isHistoryPanelOpen,
      activePrimaryPanel: state.activePrimaryPanel === "history" ? null : "history",
    })),

  toggleShortcutsPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isShortcutsPanelOpen: !state.isShortcutsPanelOpen,
    })),

  toggleTutorialPanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isTutorialPanelOpen: !state.isTutorialPanelOpen,
      activePrimaryPanel: state.activePrimaryPanel === "tutorial" ? null : "tutorial",
    })),

  toggleNotification: () =>
    set((state) => ({
      ...closedOverlayState,
      isNotificationOpen: !state.isNotificationOpen,
    })),

  toggleUserMenu: () =>
    set((state) => ({
      ...closedOverlayState,
      isUserMenuOpen: !state.isUserMenuOpen,
    })),

  toggleSharePanel: () =>
    set((state) => ({
      ...closedOverlayState,
      isSharePanelOpen: !state.isSharePanelOpen,
    })),

  toggleAgent: () =>
    set((state) => ({
      ...closedOverlayState,
      isAgentOpen: !state.isAgentOpen,
    })),

  toggleZoomMenu: () =>
    set((state) => ({
      ...closedOverlayState,
      isZoomMenuOpen: !state.isZoomMenuOpen,
    })),

  closeZoomMenu: () => set({ isZoomMenuOpen: false }),

  togglePrimaryPanel: (panel) =>
    set((state) => ({
      ...closeTransientOverlays(state),
      activePrimaryPanel: state.activePrimaryPanel === panel ? null : panel,
    })),

  setPrimaryPanel: (panel) =>
    set((state) => ({
      ...closeTransientOverlays(state),
      activePrimaryPanel: panel,
    })),

  setEditorMode: (mode) =>
    set({
      ...closedOverlayState,
      editorMode: mode,
      isAgentOpen: mode === "storyboard",
    }),

  setCanvasTool: (tool) => set({ canvasTool: tool }),

  openDirectorDesk: (nodeId, canvasId) =>
    set({
      ...closedOverlayState,
      activeDirectorNodeId: nodeId,
      activeDirectorCanvasId: canvasId,
    }),

  closeDirectorDesk: () =>
    set({ activeDirectorNodeId: null, activeDirectorCanvasId: null }),

  openImagePreview: (preview) =>
    set({
      ...closedOverlayState,
      imagePreview: preview,
    }),

  closeImagePreview: () => set({ imagePreview: null }),

  openImageAnnotate: (annotate) =>
    set({
      ...closedOverlayState,
      imageAnnotate: annotate,
    }),

  closeImageAnnotate: () => set({ imageAnnotate: null }),

  openImageElementEdit: (elementEdit) =>
    set({
      ...closedOverlayState,
      imageElementEdit: elementEdit,
    }),

  closeImageElementEdit: () => set({ imageElementEdit: null }),

  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),

  toggleGrid: () =>
    set((state) => ({ showGrid: !state.showGrid })),

  toggleEdges: () =>
    set((state) => ({ showEdges: !state.showEdges })),

  toggleSnapToGrid: () =>
    set((state) => ({ snapToGrid: !state.snapToGrid })),

  setZoomLevel: (zoom: number) => set({ zoomLevel: zoom }),

  closeTopForegroundSurface: () => {
    let closedSurface: LibTVBlockingForegroundSurface | null = null;
    set((state) => {
      closedSurface = resolveLibTVBlockingForegroundSurface(state);
      switch (closedSurface) {
        case "shortcuts":
          return { isShortcutsPanelOpen: false };
        case "canvas-dropdown":
          return { isCanvasDropdownOpen: false };
        case "add-node":
          return { isAddNodePanelOpen: false };
        case "zoom-menu":
          return { isZoomMenuOpen: false };
        case "share":
          return { isSharePanelOpen: false };
        case "notification":
          return { isNotificationOpen: false };
        case "user-menu":
          return { isUserMenuOpen: false };
        case "primary-panel":
          return {
            activePrimaryPanel: null,
            isToolboxPanelOpen: false,
            isMaterialPanelOpen: false,
            isCharacterPanelOpen: false,
            isHistoryPanelOpen: false,
            isTutorialPanelOpen: false,
          };
        default:
          return state;
      }
    });
    return closedSurface;
  },

  closeAllPanels: () =>
    set({
      ...closedOverlayState,
      activeDirectorNodeId: null,
      activeDirectorCanvasId: null,
    }),
}));

declare global {
  interface Window {
    __libtv_ui_store: typeof useUIStore;
  }
}

if (typeof window !== "undefined") {
  window.__libtv_ui_store = useUIStore;
}
