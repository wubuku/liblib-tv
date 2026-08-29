import type { DirectorLocalModelLibraryItem } from "@/components/director/directorModelLibrary";

export const DIRECTOR_LOCAL_RESOURCE_SCHEMA_VERSION = 1 as const;
export const DIRECTOR_LOCAL_RESOURCE_MAX_BYTES = 25 * 1024 * 1024;

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

export interface DirectorLocalResourceLeaseOwnerV1 {
  ownerKey: string;
  projectId: string;
  sessionId: string;
  generation: number;
}

export interface DirectorLocalResourceLeaseV1 {
  leaseId: string;
  owner: DirectorLocalResourceLeaseOwnerV1;
}

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
  activeRequestOwner: DirectorLocalResourceLeaseOwnerV1 | null;
  error: DirectorLocalResourceFailureReason | null;
  errorMessage: string | null;
  leaseCount: number;
  leases: DirectorLocalResourceLeaseV1[];
  releaseRequested: boolean;
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
  return (
    Number.isSafeInteger(sizeBytes) &&
    sizeBytes > 0 &&
    sizeBytes <= DIRECTOR_LOCAL_RESOURCE_MAX_BYTES
  );
}

function nonEmpty(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.trim() === value;
}

function validLeaseOwner(
  owner: unknown,
): owner is DirectorLocalResourceLeaseOwnerV1 {
  if (!owner || typeof owner !== "object") return false;
  const candidate = owner as Partial<DirectorLocalResourceLeaseOwnerV1>;
  return (
    nonEmpty(candidate.ownerKey) &&
    nonEmpty(candidate.projectId) &&
    nonEmpty(candidate.sessionId) &&
    typeof candidate.generation === "number" &&
    Number.isSafeInteger(candidate.generation) &&
    candidate.generation > 0
  );
}

function sameLeaseOwner(
  left: DirectorLocalResourceLeaseOwnerV1,
  right: DirectorLocalResourceLeaseOwnerV1,
): boolean {
  return (
    left.ownerKey === right.ownerKey &&
    left.projectId === right.projectId &&
    left.sessionId === right.sessionId &&
    left.generation === right.generation
  );
}

function cloneLeaseOwner(
  owner: DirectorLocalResourceLeaseOwnerV1,
): DirectorLocalResourceLeaseOwnerV1 {
  return { ...owner };
}

function estimateDataUrlBytes(dataUrl: string): number | null {
  if (!dataUrl.startsWith("data:")) return null;
  const commaIndex = dataUrl.indexOf(",");
  if (commaIndex <= 5) return null;
  const metadata = dataUrl.slice(5, commaIndex);
  const payload = dataUrl.slice(commaIndex + 1);
  if (payload.length === 0) return null;
  if (metadata.toLocaleLowerCase("en-US").includes(";base64")) {
    const normalized = payload.replace(/\s/g, "");
    if (
      normalized.length === 0 ||
      normalized.length % 4 === 1 ||
      !/^[A-Za-z0-9+/]*={0,2}$/u.test(normalized)
    ) {
      return null;
    }
    const padding = normalized.endsWith("==")
      ? 2
      : normalized.endsWith("=")
        ? 1
        : 0;
    return Math.floor((normalized.length * 3) / 4) - padding;
  }
  try {
    return new TextEncoder().encode(decodeURIComponent(payload)).byteLength;
  } catch {
    return null;
  }
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
  if (
    typeof item !== "object" ||
    item === null ||
    !nonEmpty(item.id) ||
    !nonEmpty(item.fileName) ||
    typeof item.dataUrl !== "string"
  ) {
    return null;
  }
  const extension = extensionForFileName(item.fileName);
  if (
    !extension ||
    item.dataUrl.length === 0 ||
    estimateDataUrlBytes(item.dataUrl) === null
  ) {
    return null;
  }
  const sizeBytes = item.sizeBytes ?? 0;
  const lastModified = item.lastModified ?? 0;
  const estimatedBytes = estimateDataUrlBytes(item.dataUrl);
  if (
    estimatedBytes === null ||
    !validSize(estimatedBytes) ||
    (item.sizeBytes !== undefined &&
      (!validSize(sizeBytes) || sizeBytes !== estimatedBytes)) ||
    (item.lastModified !== undefined &&
      (!Number.isSafeInteger(lastModified) || lastModified < 0)) ||
    (item.mimeType !== undefined && !nonEmpty(item.mimeType))
  ) {
    return null;
  }
  return {
    schemaVersion: DIRECTOR_LOCAL_RESOURCE_SCHEMA_VERSION,
    resourceId: item.id,
    fileName: item.fileName,
    extension,
    mimeType:
      item.mimeType ??
      (extension === "obj" ? "text/plain" : "application/octet-stream"),
    sizeBytes: item.sizeBytes === undefined ? estimatedBytes : sizeBytes,
    lastModified:
      item.lastModified === undefined ? 0 : lastModified,
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
    activeRequestOwner: null,
    error: null,
    errorMessage: null,
    leaseCount: 0,
    leases: [],
    releaseRequested: false,
    updatedAt,
  };
}

export function addDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  descriptor: DirectorLocalResourceDescriptorV1,
): DirectorLocalResourceMap {
  const current = resources[descriptor.resourceId];
  if (current?.releaseRequested && current.leaseCount > 0) {
    return resources;
  }
  return {
    ...resources,
    [descriptor.resourceId]: current
      ? {
          ...current,
          descriptor,
          ...(current.status === "released" || current.releaseRequested
            ? {
                status: "idle" as const,
                attempt: 0,
                retryNonce: 0,
                activeRequestId: null,
                activeRequestOwner: null,
                error: null,
                errorMessage: null,
                leaseCount: 0,
                leases: [],
                releaseRequested: false,
              }
            : {}),
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
  owner: DirectorLocalResourceLeaseOwnerV1,
): DirectorLocalResourceTransition {
  const current = resources[resourceId];
  if (
    !current ||
    current.status === "released" ||
    current.status === "loading" ||
    current.releaseRequested ||
    !nonEmpty(requestId) ||
    !validLeaseOwner(owner)
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
    activeRequestOwner: cloneLeaseOwner(owner),
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
    owner: DirectorLocalResourceLeaseOwnerV1;
    status: "ready" | "failed" | "canceled";
    error?: DirectorLocalResourceFailureReason | null;
    errorMessage?: string | null;
  },
): DirectorLocalResourceTransition {
  const current = resources[input.resourceId];
  if (
    !current ||
    current.status !== "loading" ||
    current.activeRequestId !== input.requestId ||
    !current.activeRequestOwner ||
    !validLeaseOwner(input.owner) ||
    !sameLeaseOwner(current.activeRequestOwner, input.owner)
  ) {
    return { state: current ?? null, accepted: false };
  }
  const error = input.error ?? null;
  const errorMessage = input.errorMessage ?? null;
  const validTerminal =
    input.status === "ready"
      ? error === null && errorMessage === null
      : error !== null && errorMessage !== "";
  if (!validTerminal) return { state: current, accepted: false };
  const next: DirectorLocalResourceStateV1 = {
    ...current,
    status: input.status,
    activeRequestId: null,
    activeRequestOwner: null,
    error: input.status === "ready" ? null : error,
    errorMessage: input.status === "ready" ? null : errorMessage,
    updatedAt: nowIso(),
  };
  return { state: next, accepted: true };
}

export function retryDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (
    !current ||
    current.status === "released" ||
    current.releaseRequested ||
    current.leaseCount > 0
  ) {
    return resources;
  }
  return {
    ...resources,
    [resourceId]: {
      ...current,
      status: "idle",
      retryNonce: current.retryNonce + 1,
      activeRequestId: null,
      activeRequestOwner: null,
      error: null,
      errorMessage: null,
      updatedAt: nowIso(),
    },
  };
}

export function retainDirectorLocalResource(
  resources: DirectorLocalResourceMap,
  resourceId: string,
  lease: DirectorLocalResourceLeaseV1,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (
    !current ||
    current.status === "released" ||
    current.releaseRequested ||
    !nonEmpty(lease.leaseId) ||
    !validLeaseOwner(lease.owner) ||
    current.leases.some((item) => item.leaseId === lease.leaseId)
  ) {
    return resources;
  }
  const leases = [
    ...current.leases,
    { leaseId: lease.leaseId, owner: cloneLeaseOwner(lease.owner) },
  ];
  return {
    ...resources,
    [resourceId]: {
      ...current,
      leaseCount: leases.length,
      leases,
      updatedAt: nowIso(),
    },
  };
}

export function releaseDirectorLocalResourceLease(
  resources: DirectorLocalResourceMap,
  resourceId: string,
  leaseId: string,
  owner: DirectorLocalResourceLeaseOwnerV1,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (
    !current ||
    !nonEmpty(leaseId) ||
    !validLeaseOwner(owner) ||
    !current.leases.some(
      (lease) =>
        lease.leaseId === leaseId && sameLeaseOwner(lease.owner, owner),
    )
  ) {
    return resources;
  }
  const leases = current.leases.filter((lease) => lease.leaseId !== leaseId);
  const lastLease = leases.length === 0;
  const shouldRelease = current.releaseRequested && lastLease;
  const cancelActiveRequest =
    lastLease && current.activeRequestId === leaseId;
  return {
    ...resources,
    [resourceId]: {
      ...current,
      status: shouldRelease
        ? "released"
        : cancelActiveRequest
          ? "canceled"
          : current.status,
      activeRequestId:
        shouldRelease || cancelActiveRequest ? null : current.activeRequestId,
      activeRequestOwner:
        shouldRelease || cancelActiveRequest ? null : current.activeRequestOwner,
      error:
        shouldRelease
          ? null
          : cancelActiveRequest
            ? "ABORTED"
            : current.error,
      errorMessage:
        shouldRelease
          ? null
          : cancelActiveRequest
            ? "资源 lease 已释放"
            : current.errorMessage,
      leaseCount: leases.length,
      leases,
      updatedAt: nowIso(),
    },
  };
}

export function markDirectorLocalResourceReleased(
  resources: DirectorLocalResourceMap,
  resourceId: string,
): DirectorLocalResourceMap {
  const current = resources[resourceId];
  if (!current) return resources;
  if (current.leaseCount > 0) {
    const loading = current.status === "loading";
    return {
      ...resources,
      [resourceId]: {
        ...current,
        status: loading ? "canceled" : current.status,
        activeRequestId: null,
        activeRequestOwner: null,
        error: loading ? "ABORTED" : current.error,
        errorMessage: loading ? "资源已请求释放" : current.errorMessage,
        releaseRequested: true,
        updatedAt: nowIso(),
      },
    };
  }
  const next = { ...resources };
  next[resourceId] = {
    ...current,
    status: "released",
    activeRequestId: null,
    activeRequestOwner: null,
    error: null,
    errorMessage: null,
    releaseRequested: true,
    updatedAt: nowIso(),
  };
  return next;
}
