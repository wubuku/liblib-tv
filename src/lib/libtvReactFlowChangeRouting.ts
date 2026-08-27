import type { Edge, Node } from "@xyflow/react";

export type LibTVReactFlowChangeRoutingCode =
  | "APPLIED_SELECTION"
  | "APPLIED_TRANSPORT"
  | "APPLIED_MIXED_RUNTIME"
  | "STALE_ELEMENT_ID"
  | "INVALID_NUMERIC_PAYLOAD"
  | "SEMANTIC_CHANGE_REQUIRES_COMMAND"
  | "ATTRIBUTE_RESIZE_REQUIRES_COMMAND"
  | "UNSUPPORTED_CHANGE_VARIANT"
  | "ACTIVE_CANVAS_CHANGED";

export type LibTVReactFlowRejectedCode = Exclude<
  LibTVReactFlowChangeRoutingCode,
  | "APPLIED_SELECTION"
  | "APPLIED_TRANSPORT"
  | "APPLIED_MIXED_RUNTIME"
  | "ACTIVE_CANVAS_CHANGED"
>;

export interface LibTVReactFlowChangeRoutingRequest {
  expectedActiveCanvasId: string;
  nodeChanges?: readonly unknown[];
  edgeChanges?: readonly unknown[];
}

export interface LibTVReactFlowChangeRoutingResult {
  status: "applied" | "rejected";
  code: LibTVReactFlowChangeRoutingCode;
  expectedActiveCanvasId: string;
  activeCanvasId: string;
  nodeChangeCount: number;
  edgeChangeCount: number;
  changeIndex?: number;
  elementId?: string;
}

export interface LibTVReactFlowChangeRoutingSnapshot {
  activeCanvasId: string;
  nodes: readonly Node[];
  edges: readonly Edge[];
  selectedNodeIds: readonly string[];
  selectedEdgeIds: readonly string[];
}

export type LibTVReactFlowChangeRoutingPlan =
  | {
      status: "accept";
      code:
        | "APPLIED_SELECTION"
        | "APPLIED_TRANSPORT"
        | "APPLIED_MIXED_RUNTIME";
      nextNodes: Node[];
      nextSelectedNodeIds: string[];
      nextSelectedEdgeIds: string[];
      hasSelection: boolean;
      hasTransport: boolean;
    }
  | {
      status: "reject";
      code: LibTVReactFlowRejectedCode;
      changeIndex: number;
      elementId?: string;
    };

type NodeSelectionDelta = {
  elementId: string;
  selected: boolean;
};

type EdgeSelectionDelta = NodeSelectionDelta;

type NodePositionDelta = {
  elementId: string;
  position?: { x: number; y: number };
  dragging?: boolean;
};

type NodeDimensionsDelta = {
  elementId: string;
  dimensions?: { width: number; height: number };
  resizing?: boolean;
};

const nodeChangeKeys = {
  select: new Set(["id", "type", "selected"]),
  position: new Set(["id", "type", "position", "positionAbsolute", "dragging"]),
  dimensions: new Set(["id", "type", "dimensions", "resizing", "setAttributes"]),
  remove: new Set(["id", "type"]),
  add: new Set(["item", "type", "index"]),
  replace: new Set(["id", "item", "type"]),
} as const;

const edgeChangeKeys = {
  select: nodeChangeKeys.select,
  remove: nodeChangeKeys.remove,
  add: nodeChangeKeys.add,
  replace: nodeChangeKeys.replace,
} as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function hasOnlyKeys(
  value: Record<string, unknown>,
  allowedKeys: ReadonlySet<string>,
): boolean {
  return Object.keys(value).every((key) => allowedKeys.has(key));
}

function isFinitePosition(value: unknown): value is { x: number; y: number } {
  if (!isRecord(value)) return false;
  return (
    typeof value.x === "number" &&
    Number.isFinite(value.x) &&
    typeof value.y === "number" &&
    Number.isFinite(value.y)
  );
}

function isFiniteDimensions(
  value: unknown,
): value is { width: number; height: number } {
  if (!isRecord(value)) return false;
  return (
    typeof value.width === "number" &&
    Number.isFinite(value.width) &&
    value.width >= 0 &&
    typeof value.height === "number" &&
    Number.isFinite(value.height) &&
    value.height >= 0
  );
}

function orderedSelection(
  initialIds: readonly string[],
  availableIds: ReadonlySet<string>,
  deltas: readonly NodeSelectionDelta[],
): string[] {
  const selectedIds = initialIds.filter((id) => availableIds.has(id));
  for (const delta of deltas) {
    const existingIndex = selectedIds.indexOf(delta.elementId);
    if (delta.selected) {
      if (existingIndex === -1) selectedIds.push(delta.elementId);
    } else if (existingIndex !== -1) {
      selectedIds.splice(existingIndex, 1);
    }
  }
  return selectedIds;
}

function rejected(
  code: LibTVReactFlowRejectedCode,
  changeIndex: number,
  elementId?: string,
): Extract<LibTVReactFlowChangeRoutingPlan, { status: "reject" }> {
  return { status: "reject", code, changeIndex, elementId };
}

export function planLibTVReactFlowChanges(
  snapshot: LibTVReactFlowChangeRoutingSnapshot,
  request: LibTVReactFlowChangeRoutingRequest,
): LibTVReactFlowChangeRoutingPlan {
  const nodeChanges = request.nodeChanges ?? [];
  const edgeChanges = request.edgeChanges ?? [];
  const nodeIds = new Set(snapshot.nodes.map((node) => node.id));
  const edgeIds = new Set(snapshot.edges.map((edge) => edge.id));
  const nodeSelections: NodeSelectionDelta[] = [];
  const edgeSelections: EdgeSelectionDelta[] = [];
  const positions: NodePositionDelta[] = [];
  const dimensions: NodeDimensionsDelta[] = [];

  for (const [changeIndex, rawChange] of nodeChanges.entries()) {
    if (!isRecord(rawChange) || typeof rawChange.type !== "string") {
      return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
    }

    switch (rawChange.type) {
      case "add":
      case "remove":
      case "replace": {
        if (!hasOnlyKeys(rawChange, nodeChangeKeys[rawChange.type])) {
          return rejected(
            "UNSUPPORTED_CHANGE_VARIANT",
            changeIndex,
            typeof rawChange.id === "string" ? rawChange.id : undefined,
          );
        }
        return rejected(
          "SEMANTIC_CHANGE_REQUIRES_COMMAND",
          changeIndex,
          typeof rawChange.id === "string" ? rawChange.id : undefined,
        );
      }
      case "select": {
        if (
          !hasOnlyKeys(rawChange, nodeChangeKeys.select) ||
          typeof rawChange.id !== "string" ||
          typeof rawChange.selected !== "boolean"
        ) {
          return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
        }
        if (!nodeIds.has(rawChange.id)) {
          return rejected("STALE_ELEMENT_ID", changeIndex, rawChange.id);
        }
        nodeSelections.push({
          elementId: rawChange.id,
          selected: rawChange.selected,
        });
        break;
      }
      case "position": {
        if (
          !hasOnlyKeys(rawChange, nodeChangeKeys.position) ||
          typeof rawChange.id !== "string" ||
          (rawChange.dragging !== undefined &&
            typeof rawChange.dragging !== "boolean")
        ) {
          return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
        }
        if (!nodeIds.has(rawChange.id)) {
          return rejected("STALE_ELEMENT_ID", changeIndex, rawChange.id);
        }
        if (
          (rawChange.position !== undefined &&
            !isFinitePosition(rawChange.position)) ||
          (rawChange.positionAbsolute !== undefined &&
            !isFinitePosition(rawChange.positionAbsolute))
        ) {
          return rejected(
            "INVALID_NUMERIC_PAYLOAD",
            changeIndex,
            rawChange.id,
          );
        }
        positions.push({
          elementId: rawChange.id,
          position: rawChange.position,
          dragging: rawChange.dragging,
        });
        break;
      }
      case "dimensions": {
        if (
          !hasOnlyKeys(rawChange, nodeChangeKeys.dimensions) ||
          typeof rawChange.id !== "string" ||
          (rawChange.resizing !== undefined &&
            typeof rawChange.resizing !== "boolean")
        ) {
          return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
        }
        if (!nodeIds.has(rawChange.id)) {
          return rejected("STALE_ELEMENT_ID", changeIndex, rawChange.id);
        }
        if (
          rawChange.setAttributes !== undefined &&
          rawChange.setAttributes !== false
        ) {
          if (
            rawChange.setAttributes === true ||
            rawChange.setAttributes === "width" ||
            rawChange.setAttributes === "height"
          ) {
            return rejected(
              "ATTRIBUTE_RESIZE_REQUIRES_COMMAND",
              changeIndex,
              rawChange.id,
            );
          }
          return rejected(
            "UNSUPPORTED_CHANGE_VARIANT",
            changeIndex,
            rawChange.id,
          );
        }
        if (
          rawChange.dimensions !== undefined &&
          !isFiniteDimensions(rawChange.dimensions)
        ) {
          return rejected(
            "INVALID_NUMERIC_PAYLOAD",
            changeIndex,
            rawChange.id,
          );
        }
        dimensions.push({
          elementId: rawChange.id,
          dimensions: rawChange.dimensions,
          resizing: rawChange.resizing,
        });
        break;
      }
      default:
        return rejected(
          "UNSUPPORTED_CHANGE_VARIANT",
          changeIndex,
          typeof rawChange.id === "string" ? rawChange.id : undefined,
        );
    }
  }

  for (const [edgeIndex, rawChange] of edgeChanges.entries()) {
    const changeIndex = nodeChanges.length + edgeIndex;
    if (!isRecord(rawChange) || typeof rawChange.type !== "string") {
      return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
    }

    switch (rawChange.type) {
      case "add":
      case "remove":
      case "replace": {
        if (!hasOnlyKeys(rawChange, edgeChangeKeys[rawChange.type])) {
          return rejected(
            "UNSUPPORTED_CHANGE_VARIANT",
            changeIndex,
            typeof rawChange.id === "string" ? rawChange.id : undefined,
          );
        }
        return rejected(
          "SEMANTIC_CHANGE_REQUIRES_COMMAND",
          changeIndex,
          typeof rawChange.id === "string" ? rawChange.id : undefined,
        );
      }
      case "select": {
        if (
          !hasOnlyKeys(rawChange, edgeChangeKeys.select) ||
          typeof rawChange.id !== "string" ||
          typeof rawChange.selected !== "boolean"
        ) {
          return rejected("UNSUPPORTED_CHANGE_VARIANT", changeIndex);
        }
        if (!edgeIds.has(rawChange.id)) {
          return rejected("STALE_ELEMENT_ID", changeIndex, rawChange.id);
        }
        edgeSelections.push({
          elementId: rawChange.id,
          selected: rawChange.selected,
        });
        break;
      }
      default:
        return rejected(
          "UNSUPPORTED_CHANGE_VARIANT",
          changeIndex,
          typeof rawChange.id === "string" ? rawChange.id : undefined,
        );
    }
  }

  const hasSelection = nodeSelections.length > 0 || edgeSelections.length > 0;
  const hasTransport = positions.length > 0 || dimensions.length > 0;
  if (!hasSelection && !hasTransport) {
    return rejected("UNSUPPORTED_CHANGE_VARIANT", -1);
  }

  const positionsByNodeId = new Map<string, NodePositionDelta[]>();
  for (const position of positions) {
    const existing = positionsByNodeId.get(position.elementId) ?? [];
    existing.push(position);
    positionsByNodeId.set(position.elementId, existing);
  }
  const dimensionsByNodeId = new Map<string, NodeDimensionsDelta[]>();
  for (const dimension of dimensions) {
    const existing = dimensionsByNodeId.get(dimension.elementId) ?? [];
    existing.push(dimension);
    dimensionsByNodeId.set(dimension.elementId, existing);
  }

  const nextNodes = hasTransport
    ? snapshot.nodes.map((node) => {
        const positionDeltas = positionsByNodeId.get(node.id);
        const dimensionDeltas = dimensionsByNodeId.get(node.id);
        if (!positionDeltas && !dimensionDeltas) return node;

        const nextNode = { ...node };
        for (const delta of positionDeltas ?? []) {
          if (delta.position) nextNode.position = { ...delta.position };
          if (delta.dragging !== undefined) nextNode.dragging = delta.dragging;
        }
        for (const delta of dimensionDeltas ?? []) {
          if (delta.dimensions) nextNode.measured = { ...delta.dimensions };
          if (delta.resizing !== undefined) nextNode.resizing = delta.resizing;
        }
        delete nextNode.selected;
        return nextNode;
      })
    : [...snapshot.nodes];

  return {
    status: "accept",
    code:
      hasSelection && hasTransport
        ? "APPLIED_MIXED_RUNTIME"
        : hasSelection
          ? "APPLIED_SELECTION"
          : "APPLIED_TRANSPORT",
    nextNodes,
    nextSelectedNodeIds: orderedSelection(
      snapshot.selectedNodeIds,
      nodeIds,
      nodeSelections,
    ),
    nextSelectedEdgeIds: orderedSelection(
      snapshot.selectedEdgeIds,
      edgeIds,
      edgeSelections,
    ),
    hasSelection,
    hasTransport,
  };
}
