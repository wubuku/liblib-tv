import type { Node, Viewport } from "@xyflow/react";

const SOURCE_ORGANIZE_POSITIONS: Record<string, { x: number; y: number }> = {
  "i-lBzmo67AHv": { x: 0, y: 0 },
  "i-vxeeCnxySa": { x: -85, y: 450 },
  "i-1FQ9tErTcC": { x: 0, y: 900 },
  "i-dnwoZQ7jsG": { x: -85, y: 1350 },
  "b-bTLLuU4w5q": { x: 910, y: 470 },
  "i-YDfWhFlthe": { x: 820, y: 1040 },
  "g-245IDFh8sB": { x: 1640, y: 370 },
  "g-EFbbHpwq5w": { x: 1640, y: 940 },
  "v-UGQZzZOpbv": { x: 1710, y: 1010 },
  "t-9j2MoccxBj": { x: 2500, y: 0 },
};

const FALLBACK_COLUMNS = [-85, 820, 1640];
const FALLBACK_START_Y = 1820;
const FALLBACK_GUTTER_Y = 100;
const ORGANIZE_HORIZONTAL_MARGIN = 48;
const ORGANIZE_TOP_MARGIN = 49;
const ORGANIZE_MIN_ZOOM = 0.1;
const ORGANIZE_MAX_ZOOM = 0.526;

function dimension(value: number | string | undefined, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function nodeWidth(node: Node): number {
  return node.width ?? dimension(node.style?.width, 350);
}

function nodeHeight(node: Node): number {
  return node.height ?? dimension(node.style?.height, 180);
}

export function organizeLiblibNodes(nodes: Node[]): Node[] {
  const fallbackY = FALLBACK_COLUMNS.map(() => FALLBACK_START_Y);

  return nodes.map((node) => {
    if (node.parentId) return node;

    const sourcePosition = SOURCE_ORGANIZE_POSITIONS[node.id];
    if (sourcePosition) {
      return {
        ...node,
        position: { ...sourcePosition },
      };
    }

    const columnIndex = fallbackY.indexOf(Math.min(...fallbackY));
    const position = {
      x: FALLBACK_COLUMNS[columnIndex],
      y: fallbackY[columnIndex],
    };
    fallbackY[columnIndex] += nodeHeight(node) + FALLBACK_GUTTER_Y;
    return {
      ...node,
      position,
    };
  });
}

function getAbsolutePosition(node: Node, nodesById: Map<string, Node>): { x: number; y: number } {
  let x = node.position.x;
  let y = node.position.y;
  let parentId = node.parentId;
  const visited = new Set<string>([node.id]);

  while (parentId && !visited.has(parentId)) {
    visited.add(parentId);
    const parent = nodesById.get(parentId);
    if (!parent) break;
    x += parent.position.x;
    y += parent.position.y;
    parentId = parent.parentId;
  }

  return { x, y };
}

export function getLiblibOrganizeViewport(nodes: Node[], viewportWidth: number): Viewport {
  if (nodes.length === 0) return { x: 0, y: 0, zoom: 1 };

  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;

  for (const node of nodes) {
    const position = getAbsolutePosition(node, nodesById);
    minX = Math.min(minX, position.x);
    minY = Math.min(minY, position.y);
    maxX = Math.max(maxX, position.x + nodeWidth(node));
  }

  const boundsWidth = Math.max(1, maxX - minX);
  const availableWidth = Math.max(1, viewportWidth - ORGANIZE_HORIZONTAL_MARGIN * 2);
  const zoom = Math.min(
    ORGANIZE_MAX_ZOOM,
    Math.max(ORGANIZE_MIN_ZOOM, availableWidth / boundsWidth),
  );

  return {
    x: ORGANIZE_HORIZONTAL_MARGIN - minX * zoom,
    y: ORGANIZE_TOP_MARGIN - minY * zoom,
    zoom,
  };
}

