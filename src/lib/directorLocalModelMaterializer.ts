import { FBXLoader } from "three/addons/loaders/FBXLoader.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import {
  Box3,
  type Material,
  Object3D,
  Vector3,
  type BufferGeometry,
} from "three";
import type { DirectorLocalModelLibraryItem } from "@/components/director/directorModelLibrary";
import { DIRECTOR_LOCAL_RESOURCE_MAX_BYTES } from "@/lib/directorLocalResourceLifecycle";

export class DirectorLocalModelAbortError extends Error {
  constructor() {
    super("模型解析已取消");
    this.name = "DirectorLocalModelAbortError";
  }
}

function throwIfAborted(signal?: AbortSignal): void {
  if (signal?.aborted) throw new DirectorLocalModelAbortError();
}

function decodeDataUrl(dataUrl: string): Uint8Array {
  const commaIndex = dataUrl.indexOf(",");
  if (!dataUrl.startsWith("data:") || commaIndex < 0) {
    throw new Error("本地模型资源定位符无效");
  }
  const metadata = dataUrl.slice(5, commaIndex);
  const payload = dataUrl.slice(commaIndex + 1);
  if (metadata.toLocaleLowerCase("en-US").includes(";base64")) {
    const binary = atob(payload);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes;
  }
  return new TextEncoder().encode(decodeURIComponent(payload));
}

function asArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(bytes);
  return copy.buffer;
}

function hasRenderableMesh(root: Object3D): boolean {
  let found = false;
  root.traverse((child) => {
    if ("isMesh" in child && child.isMesh === true) found = true;
  });
  return found;
}

function normalizeMaterializedObject(root: Object3D): Object3D {
  const bounds = new Box3().setFromObject(root);
  if (bounds.isEmpty()) throw new Error("模型没有可渲染的几何体");
  const size = bounds.getSize(new Vector3());
  const center = bounds.getCenter(new Vector3());
  const largestDimension = Math.max(size.x, size.y, size.z);
  if (!Number.isFinite(largestDimension) || largestDimension <= 0) {
    throw new Error("模型几何体尺寸无效");
  }
  root.position.sub(center);
  root.scale.multiplyScalar(2.2 / largestDimension);
  root.updateMatrixWorld(true);
  return root;
}

export async function materializeDirectorLocalModel(
  item: Pick<
    DirectorLocalModelLibraryItem,
    "fileName" | "dataUrl"
  >,
  signal?: AbortSignal,
): Promise<Object3D> {
  throwIfAborted(signal);
  const extension = /\.([^.]+)$/u.exec(item.fileName)?.[1]?.toLowerCase();
  if (extension !== "obj" && extension !== "fbx") {
    throw new Error("仅支持 OBJ 和 FBX 模型");
  }
  const bytes = decodeDataUrl(item.dataUrl);
  if (bytes.byteLength === 0) throw new Error("模型文件为空");
  if (bytes.byteLength > DIRECTOR_LOCAL_RESOURCE_MAX_BYTES) {
    throw new Error("本地模型资源超过 25 MiB 限制");
  }
  throwIfAborted(signal);

  const parsed =
    extension === "obj"
      ? new OBJLoader().parse(new TextDecoder().decode(bytes))
      : new FBXLoader().parse(asArrayBuffer(bytes), "");
  throwIfAborted(signal);
  if (!hasRenderableMesh(parsed)) throw new Error("模型没有可渲染的网格");
  return normalizeMaterializedObject(parsed);
}

export function disposeDirectorLocalModel(root: Object3D): void {
  root.traverse((child) => {
    const resource = child as unknown as {
      geometry?: BufferGeometry;
      material?: Material | Material[];
    };
    resource.geometry?.dispose();
    const materials = Array.isArray(resource.material)
      ? resource.material
      : resource.material
        ? [resource.material]
        : [];
    materials.forEach((material) => material.dispose());
  });
}
