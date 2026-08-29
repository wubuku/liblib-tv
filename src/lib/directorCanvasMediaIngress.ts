import type { CanvasData } from "@/store/canvasStore";

export interface DirectorCanvasMediaInputV1 {
  sourceNodeId: string;
  sourceKind: "panorama" | "image";
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}

export type DirectorPanoramaRuntimeState =
  | "empty"
  | "loading"
  | "ready"
  | "error";

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord | null {
  return value && typeof value === "object"
    ? (value as UnknownRecord)
    : null;
}

function readPositiveDimension(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? Math.round(value)
    : 1;
}

function readFilename(value: unknown): string {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : "未命名图片";
}

function readImageUrl(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null;
}

/**
 * Only direct image inputs of the active Director graph node are eligible.
 * This keeps the host handoff deterministic and avoids reaching through
 * unrelated graph branches.
 */
export function collectDirectorCanvasMediaInputs(
  canvas: CanvasData | undefined,
  directorNodeId: string,
): DirectorCanvasMediaInputV1[] {
  if (!canvas || canvas.id.length === 0 || directorNodeId.length === 0) {
    return [];
  }

  const directSourceIds: string[] = [];
  const seenSourceIds = new Set<string>();
  canvas.edges.forEach((edge) => {
    if (edge.target !== directorNodeId || seenSourceIds.has(edge.source)) {
      return;
    }
    seenSourceIds.add(edge.source);
    directSourceIds.push(edge.source);
  });

  const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
  return directSourceIds.flatMap((sourceNodeId) => {
    const node = nodesById.get(sourceNodeId);
    if (!node || node.type !== "image") return [];
    const data = asRecord(node.data);
    const imageUrl = readImageUrl(data?.imageUrl);
    if (!data || !imageUrl) return [];
    const editorVariant = data.editorVariant;
    const placeholderKind = data.placeholderKind;
    return [
      {
        sourceNodeId,
        sourceKind:
          editorVariant === "panorama" || placeholderKind === "panorama"
            ? "panorama"
            : "image",
        filename: readFilename(data.filename),
        imageUrl,
        width: readPositiveDimension(data.width),
        height: readPositiveDimension(data.height),
      },
    ];
  });
}
