import { create } from "zustand";

export type PrimaryPanel =
  | "move"
  | "toolbox"
  | "material"
  | "character"
  | "history"
  | "tutorial";

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
  toggleMinimap: () => void;
  toggleGrid: () => void;
  toggleEdges: () => void;
  toggleSnapToGrid: () => void;
  setZoomLevel: (zoom: number) => void;

  // Close all panels
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
};

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

  showMinimap: false,
  showGrid: true,
  showEdges: true,
  snapToGrid: false,
  zoomLevel: 54,

  toggleAddNodePanel: () =>
    set((state) => ({
      ...closedOverlayState,
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
      ...closedOverlayState,
      activePrimaryPanel: state.activePrimaryPanel === panel ? null : panel,
    })),

  setPrimaryPanel: (panel) =>
    set({
      ...closedOverlayState,
      activePrimaryPanel: panel,
    }),

  setEditorMode: (mode) =>
    set({
      ...closedOverlayState,
      editorMode: mode,
      isAgentOpen: mode === "storyboard",
    }),

  setCanvasTool: (tool) => set({ canvasTool: tool }),

  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),

  toggleGrid: () =>
    set((state) => ({ showGrid: !state.showGrid })),

  toggleEdges: () =>
    set((state) => ({ showEdges: !state.showEdges })),

  toggleSnapToGrid: () =>
    set((state) => ({ snapToGrid: !state.snapToGrid })),

  setZoomLevel: (zoom: number) => set({ zoomLevel: zoom }),

  closeAllPanels: () =>
    set(closedOverlayState),
}));
