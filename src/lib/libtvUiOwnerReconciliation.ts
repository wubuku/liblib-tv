export type LibTVUiOwnerKind =
  | "imagePreview"
  | "imageAnnotate"
  | "imageElementEdit"
  | "director";

export interface LibTVUiOwnerIdentity {
  canvasId: string;
  nodeId: string;
}

export type LibTVUiOwnerSnapshot = Partial<
  Record<LibTVUiOwnerKind, LibTVUiOwnerIdentity | null>
>;

export interface LibTVUiOwnerReconciliationInput {
  activeCanvasId: string;
  activeNodeIds: readonly string[];
  owners: LibTVUiOwnerSnapshot;
}

export interface LibTVUiOwnerReconciliationResult {
  validOwners: LibTVUiOwnerKind[];
  invalidOwners: LibTVUiOwnerKind[];
}

const ownerKinds: LibTVUiOwnerKind[] = [
  "imagePreview",
  "imageAnnotate",
  "imageElementEdit",
  "director",
];

export function reconcileLibTVUiOwners(
  input: LibTVUiOwnerReconciliationInput,
): LibTVUiOwnerReconciliationResult {
  const activeNodeIds = new Set(input.activeNodeIds);
  const validOwners: LibTVUiOwnerKind[] = [];
  const invalidOwners: LibTVUiOwnerKind[] = [];

  for (const kind of ownerKinds) {
    const owner = input.owners[kind];
    if (!owner) continue;

    const isValid =
      owner.canvasId === input.activeCanvasId && activeNodeIds.has(owner.nodeId);
    if (isValid) validOwners.push(kind);
    else invalidOwners.push(kind);
  }

  return { validOwners, invalidOwners };
}

declare global {
  interface Window {
    __libtv_reconcile_ui_owners: (
      input: LibTVUiOwnerReconciliationInput,
    ) => LibTVUiOwnerReconciliationResult;
  }
}

if (typeof window !== "undefined") {
  window.__libtv_reconcile_ui_owners = reconcileLibTVUiOwners;
}
