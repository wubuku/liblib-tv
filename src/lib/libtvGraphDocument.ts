// Batch 513 (VR-010 Slice A): pure graph-document codec, strict V1 reader,
// runtime-field writer whitelist and the §9.2 pure corpus runner.
// Pure only: no React, no DOM, no store access; migration is an explicit
// Vn→Vn+1 chain (V1 ships with none), and edge-policy/media-budget/limit
// policies are injected by the caller so no product number is invented here.
// Contract: docs/research/components/LibTVGraphDocument.contract.md §4-§10.

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export interface LibTVGraphDocumentV1 {
  kind: "libtv-canvas-graph";
  schemaVersion: 1;
  canvas: { name: string; viewport: { x: number; y: number; zoom: number } };
  nodes: SerializedLibTVNodeV1[];
  edges: SerializedLibTVEdgeV1[];
}

export interface SerializedLibTVNodeV1 {
  id: string;
  nodeType: string;
  dataVersion: 1;
  position: { x: number; y: number };
  parentId?: string;
  extent?: "parent";
  width?: number;
  height?: number;
  zIndex?: number;
  data: { [key: string]: JsonValue };
}

export interface SerializedLibTVEdgeV1 {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  edgeType: "default";
  data?: { [key: string]: JsonValue };
}

export type GraphDocumentRejectionReason =
  | "MALFORMED_JSON"
  | "INVALID_ENVELOPE"
  | "INVALID_NUMBER"
  | "DUPLICATE_NODE_ID"
  | "DUPLICATE_EDGE_ID"
  | "DANGLING_EDGE"
  | "MISSING_PARENT"
  | "PARENT_CYCLE"
  | "UNSUPPORTED_NODE_TYPE"
  | "INVALID_NODE_DATA"
  | "CONNECTION_POLICY_UNRESOLVED"
  | "NON_PORTABLE_MEDIA_REFERENCE"
  | "EMBEDDED_MEDIA_TOO_LARGE"
  | "DOCUMENT_LIMIT_EXCEEDED";

export type GraphDocumentWarning = string;

export type GraphDocumentLoadResult =
  | { status: "ready"; document: LibTVGraphDocumentV1 }
  | {
      status: "migrated";
      document: LibTVGraphDocumentV1;
      fromVersion: number;
      warnings: GraphDocumentWarning[];
    }
  | { status: "reject"; reason: GraphDocumentRejectionReason }
  | { status: "unsupported"; reason: "UNSUPPORTED_FUTURE_VERSION" | "UNMODELED_NODE_DATA" };

// §5.2 runtime/session fields excluded by the declared writer.
const RUNTIME_NODE_KEYS = new Set([
  "selected",
  "dragging",
  "resizing",
  "hover",
  "focus",
  "measured",
  "style",
  "internals",
]);

export interface GraphDocumentPolicies {
  // Per-type data validators: known type with failing data → INVALID_NODE_DATA.
  nodeDataValidators?: Record<string, (data: { [key: string]: JsonValue }) => boolean>;
  // Edge policy delegated to the graph-connection contract.
  isKnownEdgePolicy?: (edge: SerializedLibTVEdgeV1) => boolean;
  // data: URL byte budget; absent policy rejects every embedded data URL.
  embeddedMediaBudgetBytes?: number;
  // Document limits; absent policy disables DOCUMENT_LIMIT_EXCEEDED.
  limits?: { maxNodes?: number; maxEdges?: number; maxDepth?: number };
}

const MAX_DATA_URL_DEFAULT = 5 * 1024 * 1024;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function dataUrlByteLength(value: string): number {
  const comma = value.indexOf(",");
  return comma === -1 ? 0 : value.length - comma - 1;
}

// Media-reference diagnostics over node/edge data (§5.3).
function mediaDiagnostics(
  value: JsonValue,
  budgetBytes: number,
): GraphDocumentRejectionReason | null {
  if (typeof value === "string") {
    if (value.startsWith("blob:")) return "NON_PORTABLE_MEDIA_REFERENCE";
    if (value.startsWith("data:") && dataUrlByteLength(value) > budgetBytes) {
      return "EMBEDDED_MEDIA_TOO_LARGE";
    }
    return null;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = mediaDiagnostics(item, budgetBytes);
      if (found) return found;
    }
    return null;
  }
  if (value && typeof value === "object") {
    for (const key of Object.keys(value)) {
      const found = mediaDiagnostics((value as { [k: string]: JsonValue })[key], budgetBytes);
      if (found) return found;
    }
  }
  return null;
}

function isJsonValue(value: unknown): value is JsonValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return true;
  }
  if (Array.isArray(value)) return value.every(isJsonValue);
  if (typeof value === "object") {
    return Object.values(value as Record<string, unknown>).every(isJsonValue);
  }
  return false;
}

// §9.2 "runtime stripping": the declared writer excludes runtime/session
// fields and non-JSON values; semantic data is never silently dropped.
export function serializeLibTVGraphDocument(input: {
  canvasName: string;
  viewport: { x: number; y: number; zoom: number };
  nodes: {
    id: string;
    nodeType: string;
    dataVersion?: number;
    position: { x: number; y: number };
    parentId?: string;
    width?: number;
    height?: number;
    zIndex?: number;
    data: Record<string, unknown>;
    [runtimeKey: string]: unknown;
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
    data?: Record<string, unknown>;
  }[];
}): { status: "ready"; document: LibTVGraphDocumentV1 } | { status: "reject"; reason: GraphDocumentRejectionReason } {
  const nodes: SerializedLibTVNodeV1[] = [];
  for (const node of input.nodes) {
    const data: { [key: string]: JsonValue } = {};
    for (const key of Object.keys(node.data ?? {})) {
      if (RUNTIME_NODE_KEYS.has(key)) continue;
      const value = node.data[key];
      if (!isJsonValue(value)) continue;
      data[key] = value;
    }
    const media = mediaDiagnostics(data, MAX_DATA_URL_DEFAULT);
    if (media) return { status: "reject", reason: media };
    nodes.push({
      id: node.id,
      nodeType: node.nodeType,
      dataVersion: 1,
      position: { x: node.position.x, y: node.position.y },
      ...(node.parentId ? { parentId: node.parentId, extent: "parent" as const } : {}),
      ...(node.width !== undefined ? { width: node.width } : {}),
      ...(node.height !== undefined ? { height: node.height } : {}),
      ...(node.zIndex !== undefined ? { zIndex: node.zIndex } : {}),
      data,
    });
  }
  const edges: SerializedLibTVEdgeV1[] = input.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    ...(edge.sourceHandle ? { sourceHandle: edge.sourceHandle } : {}),
    ...(edge.targetHandle ? { targetHandle: edge.targetHandle } : {}),
    edgeType: "default" as const,
    ...(edge.data && isJsonValue(edge.data)
      ? { data: edge.data as { [key: string]: JsonValue } }
      : {}),
  }));
  return {
    status: "ready",
    document: {
      kind: "libtv-canvas-graph",
      schemaVersion: 1,
      canvas: { name: input.canvasName, viewport: { ...input.viewport } },
      nodes,
      edges,
    },
  };
}

// §7 parse/migration/validation pipeline. V1 ships no migrations; anything
// above 1 is UNSUPPORTED_FUTURE_VERSION with zero mutation and no downgrade.
export function parseLibTVGraphDocument(
  input: string | unknown,
  policies: GraphDocumentPolicies = {},
): GraphDocumentLoadResult {
  let value: unknown;
  if (typeof input === "string") {
    try {
      value = JSON.parse(input);
    } catch {
      return { status: "reject", reason: "MALFORMED_JSON" };
    }
  } else {
    value = input;
  }
  if (
    !value ||
    typeof value !== "object" ||
    (value as Record<string, unknown>).kind !== "libtv-canvas-graph" ||
    typeof (value as Record<string, unknown>).schemaVersion !== "number"
  ) {
    return { status: "reject", reason: "INVALID_ENVELOPE" };
  }
  const envelope = value as Record<string, unknown>;
  const version = envelope.schemaVersion as number;
  if (version > 1) {
    return { status: "unsupported", reason: "UNSUPPORTED_FUTURE_VERSION" };
  }
  if (version < 1 || !Array.isArray(envelope.nodes) || !Array.isArray(envelope.edges)) {
    return { status: "reject", reason: "INVALID_ENVELOPE" };
  }
  const canvas = envelope.canvas as Record<string, unknown> | undefined;
  const viewport = canvas?.viewport as Record<string, unknown> | undefined;
  if (
    !canvas ||
    typeof canvas.name !== "string" ||
    !viewport ||
    !isFiniteNumber(viewport.x) ||
    !isFiniteNumber(viewport.y) ||
    !isFiniteNumber(viewport.zoom) ||
    viewport.zoom <= 0
  ) {
    return { status: "reject", reason: "INVALID_ENVELOPE" };
  }

  const nodes: SerializedLibTVNodeV1[] = [];
  const seenNodes = new Set<string>();
  for (const raw of envelope.nodes as Record<string, unknown>[]) {
    if (
      !raw ||
      typeof raw.id !== "string" ||
      typeof raw.nodeType !== "string" ||
      typeof raw.dataVersion !== "number"
    ) {
      return { status: "reject", reason: "INVALID_ENVELOPE" };
    }
    if (raw.dataVersion !== 1) {
      return { status: "unsupported", reason: "UNMODELED_NODE_DATA" };
    }
    if (seenNodes.has(raw.id)) {
      return { status: "reject", reason: "DUPLICATE_NODE_ID" };
    }
    seenNodes.add(raw.id);
    const position = raw.position as Record<string, unknown> | undefined;
    if (
      !position ||
      !isFiniteNumber(position.x) ||
      !isFiniteNumber(position.y) ||
      (raw.width !== undefined && !isFiniteNumber(raw.width)) ||
      (raw.height !== undefined && !isFiniteNumber(raw.height))
    ) {
      return { status: "reject", reason: "INVALID_NUMBER" };
    }
    if (
      raw.data === undefined ||
      raw.data === null ||
      typeof raw.data !== "object" ||
      Array.isArray(raw.data)
    ) {
      return { status: "reject", reason: "INVALID_ENVELOPE" };
    }
    const data = raw.data as { [key: string]: JsonValue };
    const media = mediaDiagnostics(
      data,
      policies.embeddedMediaBudgetBytes ?? MAX_DATA_URL_DEFAULT,
    );
    if (media) return { status: "reject", reason: media };
    nodes.push({
      id: raw.id,
      nodeType: raw.nodeType,
      dataVersion: 1,
      position: { x: position.x as number, y: position.y as number },
      ...(typeof raw.parentId === "string"
        ? { parentId: raw.parentId, extent: "parent" as const }
        : {}),
      ...(raw.width !== undefined ? { width: raw.width as number } : {}),
      ...(raw.height !== undefined ? { height: raw.height as number } : {}),
      ...(raw.zIndex !== undefined ? { zIndex: raw.zIndex as number } : {}),
      data,
    });
  }

  // Structural: parents, cycles, node-type registry, data validators.
  for (const node of nodes) {
    if (policies.nodeDataValidators) {
      const validator = policies.nodeDataValidators[node.nodeType];
      if (!validator) {
        return { status: "reject", reason: "UNSUPPORTED_NODE_TYPE" };
      }
      if (!validator(node.data)) {
        return { status: "reject", reason: "INVALID_NODE_DATA" };
      }
    }
  }
  for (const node of nodes) {
    if (node.parentId && !seenNodes.has(node.parentId)) {
      return { status: "reject", reason: "MISSING_PARENT" };
    }
  }
  for (const node of nodes) {
    let current = node;
    const walked = new Set<string>();
    while (current.parentId) {
      if (walked.has(current.id)) {
        return { status: "reject", reason: "PARENT_CYCLE" };
      }
      walked.add(current.id);
      const parent = nodes.find((candidate) => candidate.id === current.parentId);
      if (!parent) return { status: "reject", reason: "MISSING_PARENT" };
      current = parent;
    }
  }

  // Edges: duplicates, dangling endpoints, number health, delegated policy.
  const edges: SerializedLibTVEdgeV1[] = [];
  const seenEdges = new Set<string>();
  for (const raw of envelope.edges as Record<string, unknown>[]) {
    if (
      !raw ||
      typeof raw.id !== "string" ||
      typeof raw.source !== "string" ||
      typeof raw.target !== "string"
    ) {
      return { status: "reject", reason: "INVALID_ENVELOPE" };
    }
    if (seenEdges.has(raw.id)) {
      return { status: "reject", reason: "DUPLICATE_EDGE_ID" };
    }
    seenEdges.add(raw.id);
    if (!seenNodes.has(raw.source) || !seenNodes.has(raw.target)) {
      return { status: "reject", reason: "DANGLING_EDGE" };
    }
    const edge: SerializedLibTVEdgeV1 = {
      id: raw.id,
      source: raw.source,
      target: raw.target,
      edgeType: "default",
      ...(typeof raw.sourceHandle === "string" ? { sourceHandle: raw.sourceHandle } : {}),
      ...(typeof raw.targetHandle === "string" ? { targetHandle: raw.targetHandle } : {}),
    };
    if (policies.isKnownEdgePolicy && !policies.isKnownEdgePolicy(edge)) {
      return { status: "reject", reason: "CONNECTION_POLICY_UNRESOLVED" };
    }
    edges.push(edge);
  }

  // §7.2 document limits: injected policy only — no borrowed product number.
  const limits = policies.limits;
  if (limits) {
    if (
      (limits.maxNodes !== undefined && nodes.length > limits.maxNodes) ||
      (limits.maxEdges !== undefined && edges.length > limits.maxEdges)
    ) {
      return { status: "reject", reason: "DOCUMENT_LIMIT_EXCEEDED" };
    }
    if (limits.maxDepth !== undefined) {
      const depthOf = (node: SerializedLibTVNodeV1): number => {
        let depth = 1;
        let current = node;
        while (current.parentId) {
          const parent = nodes.find((candidate) => candidate.id === current.parentId);
          if (!parent) break;
          current = parent;
          depth += 1;
        }
        return depth;
      };
      if (nodes.some((node) => depthOf(node) > limits.maxDepth!)) {
        return { status: "reject", reason: "DOCUMENT_LIMIT_EXCEEDED" };
      }
    }
  }

  return {
    status: "ready",
    document: {
      kind: "libtv-canvas-graph",
      schemaVersion: 1,
      canvas: {
        name: canvas.name as string,
        viewport: {
          x: viewport.x as number,
          y: viewport.y as number,
          zoom: viewport.zoom as number,
        },
      },
      nodes,
      edges,
    },
  };
}

// §9.2 pure corpus: every case is input + expectation over the codec.
export function runLibTVGraphDocumentPureCorpus(): Record<
  string,
  { ok: boolean; detail?: unknown }
> {
  const results: Record<string, { ok: boolean; detail?: unknown }> = {};
  const record = (name: string, ok: boolean, detail?: unknown) => {
    results[name] = ok ? { ok } : { ok, detail };
  };
  const policies: GraphDocumentPolicies = {
    nodeDataValidators: {
      text: (data) => typeof data.content === "string",
      video: (data) => typeof data.title === "string",
    },
    isKnownEdgePolicy: (edge) =>
      edge.sourceHandle === undefined || edge.sourceHandle.startsWith("out-"),
    limits: { maxNodes: 200, maxEdges: 400, maxDepth: 8 },
  };

  // empty V1: exact ready round-trip.
  {
    const doc: LibTVGraphDocumentV1 = {
      kind: "libtv-canvas-graph",
      schemaVersion: 1,
      canvas: { name: "empty", viewport: { x: 0, y: 0, zoom: 1 } },
      nodes: [],
      edges: [],
    };
    const parsed = parseLibTVGraphDocument(JSON.parse(JSON.stringify(doc)), policies);
    const roundTripped = parseLibTVGraphDocument(
      JSON.stringify(doc),
      policies,
    );
    record(
      "empty_v1_ready_round_trip",
      parsed.status === "ready" &&
        roundTripped.status === "ready" &&
        JSON.stringify((parsed as { document: LibTVGraphDocumentV1 }).document) ===
          JSON.stringify(doc),
      { parsed: parsed.status },
    );
  }

  // demo V1: order/IDs/layout/data retained.
  {
    const serialized = serializeLibTVGraphDocument({
      canvasName: "demo",
      viewport: { x: 10, y: 20, zoom: 0.8 },
      nodes: [
        {
          id: "text-1",
          nodeType: "text",
          position: { x: 1, y: 2 },
          width: 328,
          height: 340,
          data: { content: "剧本", selected: true, measured: { w: 1 } },
        },
        {
          id: "video-1",
          nodeType: "video",
          position: { x: 3, y: 4 },
          data: { title: "片段" },
        },
      ],
      edges: [{ id: "e-1", source: "text-1", target: "video-1" }],
    });
    const okWrite = serialized.status === "ready";
    const doc = okWrite ? serialized.document : null;
    const parsed = doc
      ? parseLibTVGraphDocument(JSON.parse(JSON.stringify(doc)), policies)
      : null;
    const parsedDoc =
      parsed && parsed.status === "ready" ? parsed.document : null;
    record(
      "demo_v1_semantics_retained",
      okWrite &&
        parsedDoc !== null &&
        JSON.stringify(parsedDoc) === JSON.stringify(doc) &&
        parsedDoc.nodes[0].id === "text-1" &&
        parsedDoc.nodes[0].data.content === "剧本" &&
        parsedDoc.nodes[0].data.selected === undefined &&
        parsedDoc.nodes[1].id === "video-1",
      { okWrite },
    );
  }

  // group V1: parent resolves; relative positions retained.
  {
    const doc: LibTVGraphDocumentV1 = {
      kind: "libtv-canvas-graph",
      schemaVersion: 1,
      canvas: { name: "group", viewport: { x: 0, y: 0, zoom: 1 } },
      nodes: [
        {
          id: "group-1",
          nodeType: "text",
          dataVersion: 1,
          position: { x: 0, y: 0 },
          data: { content: "父" },
        },
        {
          id: "child-1",
          nodeType: "text",
          dataVersion: 1,
          position: { x: 30, y: 30 },
          parentId: "group-1",
          extent: "parent",
          data: { content: "子" },
        },
      ],
      edges: [{ id: "e-inner", source: "group-1", target: "child-1", edgeType: "default" as const }],
    };
    const parsed = parseLibTVGraphDocument(doc, policies);
    record(
      "group_v1_parent_resolved",
      parsed.status === "ready" &&
        (parsed as { document: LibTVGraphDocumentV1 }).document.nodes[1]
          .parentId === "group-1",
      { parsed: parsed.status },
    );
  }

  // future version: unsupported; no fallback, zero mutation semantics.
  {
    const parsed = parseLibTVGraphDocument({
      kind: "libtv-canvas-graph",
      schemaVersion: 999,
      canvas: { name: "x", viewport: { x: 0, y: 0, zoom: 1 } },
      nodes: [],
      edges: [],
    });
    record(
      "future_version_unsupported",
      parsed.status === "unsupported" &&
        parsed.reason === "UNSUPPORTED_FUTURE_VERSION",
      { parsed },
    );
  }

  // duplicate / dangling.
  {
    const base = (nodes: unknown[], edges: unknown[]) => ({
      kind: "libtv-canvas-graph",
      schemaVersion: 1,
      canvas: { name: "d", viewport: { x: 0, y: 0, zoom: 1 } },
      nodes,
      edges,
    });
    const node = (id: string) => ({
      id,
      nodeType: "text",
      dataVersion: 1,
      position: { x: 0, y: 0 },
      data: { content: "" },
    });
    const dup = parseLibTVGraphDocument(
      base([node("a"), node("a")], []),
      policies,
    );
    const edge = (id: string, source: string, target: string) => ({
      id,
      source,
      target,
      edgeType: "default",
    });
    const dangling = parseLibTVGraphDocument(
      base([node("a")], [edge("e", "a", "ghost")]),
      policies,
    );
    record(
      "duplicate_and_dangling_reasons",
      dup.status === "reject" &&
        dup.reason === "DUPLICATE_NODE_ID" &&
        dangling.status === "reject" &&
        dangling.reason === "DANGLING_EDGE",
      { dup: dup.status, dangling: dangling.status },
    );
  }

  // invalid parent / parent cycle.
  {
    const node = (id: string, parentId?: string) => ({
      id,
      nodeType: "text",
      dataVersion: 1,
      position: { x: 0, y: 0 },
      parentId,
      data: { content: "" },
    });
    const missing = parseLibTVGraphDocument(
      {
        kind: "libtv-canvas-graph",
        schemaVersion: 1,
        canvas: { name: "m", viewport: { x: 0, y: 0, zoom: 1 } },
        nodes: [node("a", "ghost")],
        edges: [],
      },
      policies,
    );
    const cycle = parseLibTVGraphDocument(
      {
        kind: "libtv-canvas-graph",
        schemaVersion: 1,
        canvas: { name: "c", viewport: { x: 0, y: 0, zoom: 1 } },
        nodes: [node("a", "b"), node("b", "a")],
        edges: [],
      },
      policies,
    );
    record(
      "invalid_parent_cycle_reasons",
      missing.status === "reject" &&
        missing.reason === "MISSING_PARENT" &&
        cycle.status === "reject" &&
        cycle.reason === "PARENT_CYCLE",
      {
        missing: missing.status,
        cycle: cycle.status,
      },
    );
  }

  // blob media: non-portable diagnostics; no fake success.
  {
    const serialized = serializeLibTVGraphDocument({
      canvasName: "blob",
      viewport: { x: 0, y: 0, zoom: 1 },
      nodes: [
        {
          id: "v",
          nodeType: "video",
          position: { x: 0, y: 0 },
          data: { src: "blob:https://example.test/uuid" },
        },
      ],
      edges: [],
    });
    record(
      "blob_media_non_portable",
      serialized.status === "reject" &&
        serialized.reason === "NON_PORTABLE_MEDIA_REFERENCE",
      { serialized: serialized.status },
    );
  }

  // oversized embedded media: explicit size rejection (policy-injected).
  {
    const parsed = parseLibTVGraphDocument(
      {
        kind: "libtv-canvas-graph",
        schemaVersion: 1,
        canvas: { name: "big", viewport: { x: 0, y: 0, zoom: 1 } },
        nodes: [
          {
            id: "i",
            nodeType: "text",
            dataVersion: 1,
            position: { x: 0, y: 0 },
            data: { poster: `data:image/png;base64,${"A".repeat(64)}` },
          },
        ],
        edges: [],
      },
      { ...policies, embeddedMediaBudgetBytes: 16 },
    );
    record(
      "oversized_embedded_media_rejected",
      parsed.status === "reject" && parsed.reason === "EMBEDDED_MEDIA_TOO_LARGE",
      { parsed: parsed.status },
    );
  }

  // edge policy unknown → delegated connection contract.
  {
    const parsed = parseLibTVGraphDocument(
      {
        kind: "libtv-canvas-graph",
        schemaVersion: 1,
        canvas: { name: "p", viewport: { x: 0, y: 0, zoom: 1 } },
        nodes: [
          {
            id: "a",
            nodeType: "text",
            dataVersion: 1,
            position: { x: 0, y: 0 },
            data: { content: "" },
          },
          {
            id: "b",
            nodeType: "text",
            dataVersion: 1,
            position: { x: 1, y: 1 },
            data: { content: "" },
          },
        ],
        edges: [
          { id: "e", source: "a", target: "b", sourceHandle: "mystery", edgeType: "default" },
        ],
      },
      policies,
    );
    record(
      "edge_policy_unresolved",
      parsed.status === "reject" && parsed.reason === "CONNECTION_POLICY_UNRESOLVED",
      { parsed: parsed.status },
    );
  }

  // document limit exceeded (injected policy).
  {
    const node = (id: string) => ({
      id,
      nodeType: "text",
      dataVersion: 1,
      position: { x: 0, y: 0 },
      data: { content: "" },
    });
    const nodes = Array.from({ length: 5 }, (_, i) => node(`n${i}`));
    const parsed = parseLibTVGraphDocument(
      {
        kind: "libtv-canvas-graph",
        schemaVersion: 1,
        canvas: { name: "l", viewport: { x: 0, y: 0, zoom: 1 } },
        nodes,
        edges: [],
      },
      { ...policies, limits: { maxNodes: 4 } },
    );
    record(
      "document_limit_exceeded",
      parsed.status === "reject" && parsed.reason === "DOCUMENT_LIMIT_EXCEEDED",
      { parsed: parsed.status },
    );
  }

  return results;
}
