import type { DirectorLocalModelLibraryItem } from "@/components/director/directorModelLibrary";

export const DIRECTOR_LOCAL_RESOURCE_SCHEMA_VERSION = 1 as const;

export type DirectorLocalModelExtension = "obj" | "fbx";
export type DirectorLocalResourceStatus =
  | "idle"
  | "loading"
  | "ready"
  | "failed"
  | "canceled"
  | "released";

export type DirectorLocalResourceFailureReason =
  | "INVALID_DESCRIPTOR"
  | "UNSUPPORTED_FORMAT"
  | "EMPTY_BYTES"
  | "PARSE_FAILED"
  | "ABORTED"
  | "STALE_ATTEMPT";

export interface DirectorLocalResourceDescriptorV1 {
  schemaVersion: typeof DIRECTOR_LOCAL_RESOURCE_SCHEMA_VERSION;
  resourceId: string;
  fileName: string;
  extension: DirectorLocalModelExtension;
  mimeType: string;
  sizeBytes: number;
  lastModified: number;
  locatorClass: "SESSION_DATA_URL";
  provenance: "LOCAL_FILE";
}

export interface DirectorLocalResourceStateV1 {
  descriptor: DirectorLocalResourceDescriptorV1;
  status: DirectorLocalResourceStatus;
  attempt: number;
  retryNonce: number;
  activeRequestId: string | null;
  error: DirectorLocalResourceFailureReason | null;
  errorMessage: string | null;
  leaseCount: number;
  updatedAt: string;
}

export type DirectorLocalResourceMap = Record<
  string,
  DirectorLocalResourceStateV1
>;

export interface DirectorLocalResourceTransition {
  state: DirectorLocalResourceStateV1 | null;
  accepted: boolean;
}

function extensionForFileName(
  fileName: string,
): DirectorLocalModelExtension | null {
  const match = /\.([^.]+)$/.exec(fileName.trim().toLocaleLowerCase("en-US"));
  if (match?.[1] === "obj" || match?.[1] === "fbx") return match[1];
  return null;
}

function nowIso(): string {
  return new Date().toISOString();
}

function validSize(sizeBytes: number): boolean {
  return Number.isFinite(sizeBytes) && sizeBytes > 0;
}

export function createDirectorLocalResourceDescriptor(
  item: Pick<
    DirectorLocalModelLibraryItem,
    "id" | "fileName" | "dataUrl"
  > & {
    mimeType?: string;
    sizeBytes?: number;
    lastModified?: number;
  },
): DirectorLocalResourceDescriptorV1 | null {
  const extension = extensionForFileName(item.fileName);
  if (
    !extension ||
    item.id.trim() !== item.id ||
    item.id.length === 0 ||
    item.fileName.trim() !== item.fileName ||
    item.fileName.length === 0 ||
    item.dataUrl.length === 0
  ) {
    return null;
  }
  const sizeBytes = item.sizeBytes ?? 0;
  const lastModified = item.lastModified ?? 0;
  if (!validSize(sizeBytes) && !item.dataUrl.startsWith("data:")) return null;
  return {
    schemaVersion: DIRECTOR_LOCAL_RESOURCE_SCHEMA_VERSION,
    resourceId: item.id,
    fileName: item.fileName,
    extension,
    mimeType:
      item.mimeType ??
      (extension === "obj" ? "text/plain" : "application/octet-stream"),
    sizeBytes: validSize(sizeBytes) ? sizeBytes : item.dataUrl.length,
    lastModified:
      Number.isFinite(lastModified) && lastModified >= 0 ? lastModified : 0,
    locatorClass: "SESSION_DATA_URL",
    provenance: "LOCAL_FILE",
  };
}

export function createDirectorLocalResourceState(
  descriptor: DirectorLocalResourceDescriptorV1,
  updatedAt = nowIso(),
): DirectorLocalResourceStateV1 {
  return {
    descriptor,
    status: "idle",
    attempt: 0,
    retryNonce: 0,
    activeRequestId: null,
    error: null,
    errorMessage: null,
    leaseCount: 0,
    updatedAt,
  };
}

export function addDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  descriptor: DirectorLocalResourceDescriptorV1,
): DirectorLocalResourceMap {
  const current = resources[descriptor.resourceId];
  return {
    ...resources,
    [descriptor.resourceId]: current
      ? {
          ...current,
          descriptor,
          status: current.status === "released" ? "idle" : current.status,
          updatedAt: nowIso(),
        }
      : createDirectorLocalResourceState(descriptor),
  };
}

export function createDirectorLocalResourceMap(
  items: readonly DirectorLocalModelLibraryItem[],
): DirectorLocalResourceMap {
  return items.reduce<DirectorLocalResourceMap>((resources, item) => {
    const descriptor = createDirectorLocalResourceDescriptor(item);
    return descriptor
      ? addDirectorLocalResource(resources, descriptor)
      : resources;
  }, {});
}

export function beginDirectorLocalResourceLoad(
  resources: DirectorLocalResourceMap,
  resourceId: string,
  requestId: string,
): DirectorLocalResourceTransition {
  const current = resources[resourceId];
  if (
    !current ||
    current.status === "released" ||
    current.status === "loading" ||
    requestId.length === 0
  ) {
    return {
      state: current ?? null,
      accepted: false,
    };
  }
  const next: DirectorLocalResourceStateV1 = {
    ...current,
    status: "loading",
    attempt: current.attempt + 1,
    activeRequestId: requestId,
    error: null,
    errorMessage: null,
    updatedAt: nowIso(),
  };
  return { state: next, accepted: true };
}

export function settleDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  input: {
    resourceId: string;
    requestId: string;
    status: "ready" | "failed" | "canceled";
    error?: DirectorLocalResourceFailureReason | null;
    errorMessage?: string | null;
  },
): DirectorLocalResourceTransition {
  const current = resources[input.resourceId];
  if (
    !current ||
    current.status !== "loading" ||
    current.activeRequestId !== input.requestId
  ) {
    return { state: current ?? null, accepted: false };
  }
  const next: DirectorLocalResourceStateV1 = {
    ...current,
    status: input.status,
    activeRequestId: null,
    error: input.error ?? null,
    errorMessage: input.errorMessage ?? null,
    updatedAt: nowIso(),
  };
  return { state: next, accepted: true };
}

export function retryDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (!current || current.status === "released") return resources;
  return {
    ...resources,
    [resourceId]: {
      ...current,
      status: "idle",
      retryNonce: current.retryNonce + 1,
      activeRequestId: null,
      error: null,
      errorMessage: null,
      updatedAt: nowIso(),
    },
  };
}

export function retainDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (!current || current.status === "released") return resources;
  return {
    ...resources,
    [resourceId]: {
      ...current,
      leaseCount: current.leaseCount + 1,
      updatedAt: nowIso(),
    },
  };
}

export function releaseDirectorLocalResourceLease(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (!current || current.leaseCount === 0) return resources;
  return {
    ...resources,
    [resourceId]: {
      ...current,
      leaseCount: current.leaseCount - 1,
      updatedAt: nowIso(),
    },
  };
}

export function markDirectorLocalResourceReleased(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (!current || current.leaseCount > 0) return resources;
  const next = { ...resources };
  next[resourceId] = {
    ...current,
    status: "released",
    activeRequestId: null,
    updatedAt: nowIso(),
  };
  return next;
}
