import { create } from "zustand";

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
  editorMode: "workbench",
  canvasTool: "select",

  showMinimap: false,
  showGrid: true,
  showEdges: true,
  snapToGrid: false,
  zoomLevel: 54,

  toggleAddNodePanel: () =>
    set((state) => ({
      isAddNodePanelOpen: !state.isAddNodePanelOpen,
      isCanvasDropdownOpen: false,
    })),

  toggleCanvasDropdown: () =>
    set((state) => ({
      isCanvasDropdownOpen: !state.isCanvasDropdownOpen,
      isAddNodePanelOpen: false,
    })),

  toggleAssetPanel: () =>
    set((state) => ({ isAssetPanelOpen: !state.isAssetPanelOpen })),

  toggleToolboxPanel: () =>
    set((state) => ({ isToolboxPanelOpen: !state.isToolboxPanelOpen })),

  toggleMaterialPanel: () =>
    set((state) => ({ isMaterialPanelOpen: !state.isMaterialPanelOpen })),

  toggleCharacterPanel: () =>
    set((state) => ({ isCharacterPanelOpen: !state.isCharacterPanelOpen })),

  toggleHistoryPanel: () =>
    set((state) => ({ isHistoryPanelOpen: !state.isHistoryPanelOpen })),

  toggleShortcutsPanel: () =>
    set((state) => ({ isShortcutsPanelOpen: !state.isShortcutsPanelOpen })),

  toggleTutorialPanel: () =>
    set((state) => ({ isTutorialPanelOpen: !state.isTutorialPanelOpen })),

  toggleNotification: () =>
    set((state) => ({ isNotificationOpen: !state.isNotificationOpen })),

  toggleUserMenu: () =>
    set((state) => ({ isUserMenuOpen: !state.isUserMenuOpen })),

  toggleSharePanel: () =>
    set((state) => ({
      isSharePanelOpen: !state.isSharePanelOpen,
      isCanvasDropdownOpen: false,
    })),

  toggleAgent: () =>
    set((state) => ({ isAgentOpen: !state.isAgentOpen })),

  setEditorMode: (mode) =>
    set({
      editorMode: mode,
      isAgentOpen: mode === "storyboard",
      isSharePanelOpen: false,
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
    set({
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
    }),
}));
