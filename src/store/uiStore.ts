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
  | "tutorial"
  | "style-library"
  | "effects-library";

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
  /** Batch 443 (VR-023 Slice C): declared full-media plane baseline. */
  mediaRevision: number;
  fit: "cover" | "contain";
  /** Batch 474 (VR-022 Slice E): frozen editor session baseline —
   * media identity + declared plane + revision at open time. */
  sessionBaseline: {
    mediaId: string;
    width: number;
    height: number;
    mediaRevision: number;
    fit: "cover" | "contain";
  };
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
  isFollowingSession: boolean;
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
  isStoryboardEditorOpen: boolean;
  storyboardSessionNodeId: string | null;
  isZoomMenuOpen: boolean;
  activePrimaryPanel: PrimaryPanel | null;
  /** ★★ Batch 839：角色造型室里的「角色资产视图」当前打开的角色 id（关掉时 null）。
   *  ★ 它是 primary-panel 的**下一层** ⟹ 登记成**前台阻塞面**，
   *    Esc 才只会关掉资产视图、而不是把整个面板关掉。 */
  characterAssetsId: string | null;
  /** ★★ Batch 840：「角色大编辑器」当前打开的角色 id（关掉时 null）。
   *  ★ 它比**资产视图**还高一层（源站：资产视图底栏的「编辑角色」⟹ 大编辑器盖住整个模态）
   *  ⟹ ⟹ 登记成**前台阻塞面** `character-editor`，Esc 才先关它、再关资产视图、最后关面板。 */
  characterEditorId: string | null;
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
  /** ★★ Batch 839：开/关「角色资产视图」（角色造型室里的下一层）。 */
  setCharacterAssetsId: (id: string | null) => void;
  /** ★★ Batch 840：开/关**角色大编辑器**（null = 关闭）。 */
  setCharacterEditorId: (id: string | null) => void;
  openStoryboardEditor: () => void;
  closeStoryboardEditor: () => void;
  setStoryboardSessionNode: (nodeId: string | null) => void;
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
  setFollowingSession: (value: boolean) => void;

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
  | "isStoryboardEditorOpen"
  | "isZoomMenuOpen"
  | "activePrimaryPanel"
  | "characterAssetsId"
  | "characterEditorId"
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
  isStoryboardEditorOpen: false,
  // storyboardSessionNodeId 有意不在 closedOverlayState 重置——
  // 会话转换是节点持久形态（batch 534），不随其他面板开关回退。
  isZoomMenuOpen: false,
  activePrimaryPanel: null,
  characterAssetsId: null,
  characterEditorId: null,
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
  isFollowingSession: false,
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
  isStoryboardEditorOpen: false,
  storyboardSessionNodeId: null,
  isZoomMenuOpen: false,
  activePrimaryPanel: null,
  characterAssetsId: null,
  characterEditorId: null,
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
      // ★★ Batch 839：换/关面板 ⟹ 顺手关掉角色资产视图 ⟹
      //   否则它会**残留**成一个「谁也关不掉、Esc 也只关它」的死状态。
      characterAssetsId: null,
      // ★★ Batch 840：大编辑器比资产视图还高一层 ⟹ 换/关面板时也要顺手清掉它。
      characterEditorId: null,
    })),

  // ★★ Batch 839：开/关角色资产视图（角色造型室里的下一层）。
  setCharacterAssetsId: (id) => set({ characterAssetsId: id }),

  // ★★ Batch 840：开/关**角色大编辑器**（源站：资产视图底栏「编辑角色」⟹ 大编辑器）。
  //   ★ 开编辑器 ⟹ 顺手关掉资产视图 ⟹ 否则它会**残留**成一层看不见、却还在挡 Esc 的状态。
  setCharacterEditorId: (id: string | null) =>
    set((state) => ({
      characterEditorId: id,
      characterAssetsId: id ? null : state.characterAssetsId,
    })),

  openStoryboardEditor: () =>
    set((state) => ({
      ...closeTransientOverlays(state),
      isStoryboardEditorOpen: true,
    })),

  // Batch 534: 源站实测（截图 39）——自写会话后脚本生成器卡转为进度卡；
  // clone 以会话节点 id 记录该转换（持久，不随编辑器关闭回退）。
  setStoryboardSessionNode: (nodeId) => set({ storyboardSessionNodeId: nodeId }),

  closeStoryboardEditor: () => set({ isStoryboardEditorOpen: false }),

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

  // Batch 105: 协作跟随会话（源站顶部落出横幅）；触发来自协作事件，clone 仅暴露状态。
  setFollowingSession: (value: boolean) => set({ isFollowingSession: value }),

  closeTopForegroundSurface: () => {
    let closedSurface: LibTVBlockingForegroundSurface | null = null;
    set((state) => {
      closedSurface = resolveLibTVBlockingForegroundSurface(state);
      switch (closedSurface) {
        case "follow-banner":
          return { isFollowingSession: false };
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
        case "storyboard-editor":
          return { isStoryboardEditorOpen: false };
        case "character-assets":
          return { characterAssetsId: null };
        case "character-editor":
          return { characterEditorId: null };
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
