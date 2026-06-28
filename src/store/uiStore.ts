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

  // Canvas settings
  showMinimap: boolean;
  showGrid: boolean;
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
  toggleMinimap: () => void;
  toggleGrid: () => void;
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

  showMinimap: true,
  showGrid: true,
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

  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),

  toggleGrid: () =>
    set((state) => ({ showGrid: !state.showGrid })),

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
    }),
}));
