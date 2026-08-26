import type { Edge, Node } from "@xyflow/react";

export type LibTVConnectionOrigin = "react-flow" | "programmatic";
export type LibTVConnectionStartHandleType = "source" | "target";

export interface ProposedLibTVConnection {
  origin: LibTVConnectionOrigin;
  sourceNodeId: string | null | undefined;
  sourceHandleId: string | null | undefined;
  targetNodeId: string | null | undefined;
  targetHandleId: string | null | undefined;
  /**
   * React Flow already normalizes its final Connection payload. Set this only
   * when validating a raw gesture whose first endpoint was a target handle.
   */
  startedFromHandleType?: LibTVConnectionStartHandleType;
}

export interface NormalizedLibTVConnection {
  sourceNodeId: string;
  sourceHandleId: "source";
  targetNodeId: string;
  targetHandleId: "target";
}

export type LibTVConnectionRejectionReason =
  | "MISSING_ENDPOINT"
  | "INVALID_HANDLE_DIRECTION"
  | "DANGLING_ENDPOINT"
  | "DUPLICATE_NODE_PAIR"
  | "SELF_LOOP"
  | "DIRECTED_CYCLE";

export type LibTVConnectionValidationResult =
  | {
      status: "allow";
      connection: NormalizedLibTVConnection;
      domainStatus: "not-evaluated";
    }
  | {
      status: "reject";
      reason: LibTVConnectionRejectionReason;
    };

type NodeIdentity = Pick<Node, "id">;
type EdgeEndpoints = Pick<Edge, "source" | "target">;

function hasEndpoint(value: string | null | undefined): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function normalizeLibTVConnection(
  proposal: ProposedLibTVConnection,
): LibTVConnectionValidationResult {
  if (
    !hasEndpoint(proposal.sourceNodeId) ||
    !hasEndpoint(proposal.targetNodeId)
  ) {
    return { status: "reject", reason: "MISSING_ENDPOINT" };
  }

  const targetStarted = proposal.startedFromHandleType === "target";
  const sourceNodeId = targetStarted
    ? proposal.targetNodeId
    : proposal.sourceNodeId;
  const sourceHandleId = targetStarted
    ? proposal.targetHandleId
    : proposal.sourceHandleId;
  const targetNodeId = targetStarted
    ? proposal.sourceNodeId
    : proposal.targetNodeId;
  const targetHandleId = targetStarted
    ? proposal.sourceHandleId
    : proposal.targetHandleId;

  if (sourceHandleId !== "source" || targetHandleId !== "target") {
    return { status: "reject", reason: "INVALID_HANDLE_DIRECTION" };
  }

  return {
    status: "allow",
    connection: {
      sourceNodeId,
      sourceHandleId,
      targetNodeId,
      targetHandleId,
    },
    domainStatus: "not-evaluated",
  };
}

function hasUnorderedNodePair(
  edges: readonly EdgeEndpoints[],
  sourceNodeId: string,
  targetNodeId: string,
): boolean {
  return edges.some(
    (edge) =>
      (edge.source === sourceNodeId && edge.target === targetNodeId) ||
      (edge.source === targetNodeId && edge.target === sourceNodeId),
  );
}

function hasDirectedPath(
  edges: readonly EdgeEndpoints[],
  startNodeId: string,
  goalNodeId: string,
  availableNodeIds: ReadonlySet<string>,
): boolean {
  const adjacency = new Map<string, string[]>();
  for (const edge of edges) {
    if (
      !availableNodeIds.has(edge.source) ||
      !availableNodeIds.has(edge.target)
    ) {
      continue;
    }
    const targets = adjacency.get(edge.source) ?? [];
    targets.push(edge.target);
    adjacency.set(edge.source, targets);
  }

  const pending = [startNodeId];
  const visited = new Set<string>();
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    if (current === goalNodeId) return true;
    visited.add(current);
    pending.push(...(adjacency.get(current) ?? []));
  }
  return false;
}

export function validateLibTVGraphConnection(
  proposal: ProposedLibTVConnection,
  nodes: readonly NodeIdentity[],
  edges: readonly EdgeEndpoints[],
): LibTVConnectionValidationResult {
  const normalized = normalizeLibTVConnection(proposal);
  if (normalized.status === "reject") return normalized;

  const { sourceNodeId, targetNodeId } = normalized.connection;
  const nodeIds = new Set(nodes.map((node) => node.id));
  if (!nodeIds.has(sourceNodeId) || !nodeIds.has(targetNodeId)) {
    return { status: "reject", reason: "DANGLING_ENDPOINT" };
  }

  if (hasUnorderedNodePair(edges, sourceNodeId, targetNodeId)) {
    return { status: "reject", reason: "DUPLICATE_NODE_PAIR" };
  }

  if (sourceNodeId === targetNodeId) {
    return { status: "reject", reason: "SELF_LOOP" };
  }

  if (hasDirectedPath(edges, targetNodeId, sourceNodeId, nodeIds)) {
    return { status: "reject", reason: "DIRECTED_CYCLE" };
  }

  return normalized;
}

export function proposedLibTVConnectionFromEdge(
  edge: Pick<Edge, "source" | "sourceHandle" | "target" | "targetHandle">,
  origin: LibTVConnectionOrigin,
): ProposedLibTVConnection {
  return {
    origin,
    sourceNodeId: edge.source,
    sourceHandleId: edge.sourceHandle,
    targetNodeId: edge.target,
    targetHandleId: edge.targetHandle,
  };
}
