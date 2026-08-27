export type LibTVSelectionKind = "none" | "node" | "edge" | "mixed";

export type LibTVSelectionRef =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string };

export interface LibTVSelectionSnapshot {
  canvasId: string;
  nodeIds: string[];
  edgeIds: string[];
  kind: LibTVSelectionKind;
  primary: LibTVSelectionRef | null;
}

export interface LibTVSelectionSnapshotInput {
  canvasId: string;
  availableNodeIds: readonly string[];
  availableEdgeIds: readonly string[];
  selectedNodeIds: readonly string[];
  selectedNodeId: string | null;
  selectedEdgeIds: readonly string[];
}

export type LibTVBlockingForegroundSurface =
  | "shortcuts"
  | "canvas-dropdown"
  | "add-node"
  | "zoom-menu"
  | "share"
  | "notification"
  | "user-menu"
  | "primary-panel";

export interface LibTVForegroundSurfaceSnapshot {
  isShortcutsPanelOpen: boolean;
  isCanvasDropdownOpen: boolean;
  isAddNodePanelOpen: boolean;
  isZoomMenuOpen: boolean;
  isSharePanelOpen: boolean;
  isNotificationOpen: boolean;
  isUserMenuOpen: boolean;
  activePrimaryPanel: string | null;
}

function uniqueAvailableIds(
  selectedIds: readonly string[],
  availableIds: ReadonlySet<string>,
): string[] {
  return Array.from(new Set(selectedIds)).filter((id) => availableIds.has(id));
}

export function captureLibTVSelectionSnapshot(
  input: LibTVSelectionSnapshotInput,
): LibTVSelectionSnapshot {
  const availableNodeIds = new Set(input.availableNodeIds);
  const availableEdgeIds = new Set(input.availableEdgeIds);
  const nodeIds = uniqueAvailableIds(input.selectedNodeIds, availableNodeIds);
  const edgeIds = uniqueAvailableIds(input.selectedEdgeIds, availableEdgeIds);
  const selectedNodeId =
    input.selectedNodeId && nodeIds.includes(input.selectedNodeId)
      ? input.selectedNodeId
      : nodeIds.at(-1) ?? null;

  const kind: LibTVSelectionKind =
    nodeIds.length > 0 && edgeIds.length > 0
      ? "mixed"
      : nodeIds.length > 0
        ? "node"
        : edgeIds.length > 0
          ? "edge"
          : "none";

  return {
    canvasId: input.canvasId,
    nodeIds,
    edgeIds,
    kind,
    primary: selectedNodeId
      ? { kind: "node", id: selectedNodeId }
      : edgeIds.length > 0
        ? { kind: "edge", id: edgeIds.at(-1) as string }
        : null,
  };
}

export function isLibTVEditableCommandTarget(
  target: EventTarget | null,
): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(
    target.closest(
      [
        "textarea",
        "select",
        "input:not([type='button']):not([type='submit']):not([type='reset']):not([type='checkbox']):not([type='radio']):not([type='range']):not([type='color']):not([type='file'])",
        "[contenteditable]:not([contenteditable='false'])",
        "[role='textbox']",
        "[role='searchbox']",
        "[role='combobox']",
        "[data-libtv-editor-root]",
      ].join(", "),
    ),
  );
}

export function resolveLibTVBlockingForegroundSurface(
  snapshot: LibTVForegroundSurfaceSnapshot,
): LibTVBlockingForegroundSurface | null {
  if (snapshot.isShortcutsPanelOpen) return "shortcuts";
  if (snapshot.isCanvasDropdownOpen) return "canvas-dropdown";
  if (snapshot.isAddNodePanelOpen) return "add-node";
  if (snapshot.isZoomMenuOpen) return "zoom-menu";
  if (snapshot.isSharePanelOpen) return "share";
  if (snapshot.isNotificationOpen) return "notification";
  if (snapshot.isUserMenuOpen) return "user-menu";
  if (snapshot.activePrimaryPanel) return "primary-panel";
  return null;
}

export function isLibTVCanvasCommandKey(event: KeyboardEvent): boolean {
  const modifier = event.metaKey || event.ctrlKey;
  return (
    event.key === "Delete" ||
    event.key === "Backspace" ||
    (modifier &&
      ["z", "y", "d", "0", "+", "=", "-"].includes(event.key.toLowerCase())) ||
    (!modifier &&
      !event.altKey &&
      ["g", "v", "h"].includes(event.key.toLowerCase())) ||
    (event.altKey && event.shiftKey && event.key.toLowerCase() === "f")
  );
}
