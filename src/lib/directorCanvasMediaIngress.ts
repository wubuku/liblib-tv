import type { CanvasData } from "@/store/canvasStore";

export interface DirectorCanvasMediaInputV1 {
  sourceNodeId: string;
  sourceKind: "panorama" | "image";
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}

/**
 * Batch 861（源站实测）：导演台左侧「全景图 → 本地上传」在源站是
 *   `onClick:()=>{I?.(), et.current?.click()}`（逐字，`aU` 的 panorama 段）
 *   ⟹ ⟹ 真正的动作是**触发一个隐藏的 file input**。
 * 源站选中文件后走 `onUploadPanoramaFile`（逐字 `oz`）⟹ ⟹ 落成
 *   `panoramaUrl` ⟹ ⟹ 全景图在源站是**一个 URL**，不依赖画布节点。
 *
 * ★ clone 的全景图来源是**画布图片节点的直接上游**（`sourceNodeId` ＝ 节点 id）
 *   ⟹ ⟹ 本地文件**没有**节点 id ⟹ ⟹ 本模块把本地图片包成
 *   **同构的虚拟输入**（`sourceNodeId` ＝ `local-panorama:<id>`）
 *   ⟹ ⟹ 于是 3D 层、检查器、选择器**一条通路**照常工作，不必新增渲染分支。
 */
export interface DirectorLocalPanoramaAsset {
  id: string;
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}

/** ★ 本地全景图输入的 id 前缀（区别于真实画布节点 id）。 */
export const DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX = "local-panorama:";

export function directorLocalPanoramaSourceNodeId(id: string): string {
  return `${DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX}${id}`;
}

/**
 * 把「本地上传」的本地图片并进画布媒体输入列表。
 * ★ 没有本地资产时**原样返回**（不做拷贝）⟹ ⟹ 旧调用点的引用稳定性不变。
 */
export function mergeDirectorLocalPanoramaInput(
  inputs: DirectorCanvasMediaInputV1[],
  local: DirectorLocalPanoramaAsset | null,
): DirectorCanvasMediaInputV1[] {
  if (!local || local.imageUrl.trim().length === 0) return inputs;
  return [
    ...inputs,
    {
      sourceNodeId: directorLocalPanoramaSourceNodeId(local.id),
      sourceKind: "panorama",
      filename: local.filename,
      imageUrl: local.imageUrl,
      width: local.width,
      height: local.height,
    },
  ];
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
