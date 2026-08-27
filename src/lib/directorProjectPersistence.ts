import {
  decodeDirectorProjectDocument,
  normalizeDirectorProjectDocument,
  type DirectorProjectDocumentV1,
  type DirectorProjectOwnerV1,
} from "./directorProjectDocument.ts";
import {
  createDirectorProjectOwnerKey,
  isSameDirectorProjectOwner,
  type DirectorProjectIdentityV1,
} from "./directorProjectRegistry.ts";
import { directorDocumentFingerprint } from "./directorCommandKernel.ts";

export const DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION = 1 as const;

export interface DirectorProjectStorageEnvelopeV1 {
  storageSchemaVersion: typeof DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION;
  projectId: string;
  owner: DirectorProjectOwnerV1;
  generation: number;
  savedAt: string;
  documentFingerprint: string;
  document: DirectorProjectDocumentV1;
}

export interface DirectorProjectStorageBackend {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export type DirectorProjectPersistenceLoadReason =
  | "STORAGE_UNAVAILABLE"
  | "CORRUPT_PAYLOAD"
  | "FUTURE_STORAGE_SCHEMA"
  | "INVALID_ENVELOPE"
  | "INVALID_DOCUMENT"
  | "OWNER_MISMATCH"
  | "PROJECT_MISMATCH"
  | "FINGERPRINT_MISMATCH";

export type DirectorProjectPersistenceSaveReason =
  | "STORAGE_UNAVAILABLE"
  | "WRITE_FAILED"
  | "STALE_REQUEST"
  | "PROJECT_MISMATCH"
  | "OWNER_MISMATCH"
  | "INVALID_DOCUMENT";

export type DirectorProjectPersistenceStatus =
  | "UNAVAILABLE"
  | "MISSING"
  | "RESTORED"
  | "SAVED"
  | "SESSION_ONLY"
  | "REJECTED"
  | "STALE_IGNORED";

export interface DirectorProjectPersistenceLoadResult {
  disposition: "MISSING" | "RESTORED" | "REJECTED";
  reason: DirectorProjectPersistenceLoadReason | null;
  key: string;
  document: DirectorProjectDocumentV1 | null;
  projectId: string | null;
  generation: number | null;
  fingerprint: string | null;
}

export interface DirectorProjectPersistenceSaveInput {
  owner: DirectorProjectOwnerV1;
  projectId: string;
  generation: number;
  document: DirectorProjectDocumentV1;
  savedAt?: string;
}

export interface DirectorProjectPersistenceSaveRequest {
  requestId: number;
  key: string;
  input: DirectorProjectPersistenceSaveInput;
}

export interface DirectorProjectPersistenceSaveResult {
  disposition: "SAVED" | "STALE_IGNORED" | "REJECTED";
  reason: DirectorProjectPersistenceSaveReason | null;
  key: string;
  requestId: number;
  envelope: DirectorProjectStorageEnvelopeV1 | null;
}

export interface DirectorProjectPersistenceRecord {
  key: string;
  owner: DirectorProjectOwnerV1;
  status: DirectorProjectPersistenceStatus;
  reason:
    | DirectorProjectPersistenceLoadReason
    | DirectorProjectPersistenceSaveReason
    | null;
  projectId: string | null;
  generation: number | null;
  fingerprint: string | null;
  savedAt: string | null;
  lastRequestId: number | null;
}

export interface DirectorProjectPersistenceSnapshot {
  storageSchemaVersion: typeof DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION;
  available: boolean;
  records: DirectorProjectPersistenceRecord[];
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function cloneOwner(owner: DirectorProjectOwnerV1): DirectorProjectOwnerV1 {
  return {
    route: "libtv",
    canvasId: owner.canvasId,
    sourceNodeId: owner.sourceNodeId,
  };
}

function isValidOwner(value: unknown): value is DirectorProjectOwnerV1 {
  return (
    isRecord(value) &&
    value.route === "libtv" &&
    isNonEmptyString(value.canvasId) &&
    value.canvasId.trim() === value.canvasId &&
    isNonEmptyString(value.sourceNodeId) &&
    value.sourceNodeId.trim() === value.sourceNodeId
  );
}

function isFinitePositiveInteger(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    Number.isInteger(value) &&
    value > 0
  );
}

function isCurrentStorageSchema(
  value: unknown,
): value is typeof DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION {
  return value === DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION;
}

function cloneDocument(
  document: DirectorProjectDocumentV1,
): DirectorProjectDocumentV1 {
  return normalizeDirectorProjectDocument(document);
}

function documentForPersistence(
  document: DirectorProjectDocumentV1,
): DirectorProjectDocumentV1 {
  const normalized = cloneDocument(document);
  const stableCaptureIds = new Set(
    normalized.captureDescriptors
      .filter((capture) => capture.resourceRefId !== null)
      .map((capture) => capture.id),
  );
  return {
    ...normalized,
    captureDescriptors: normalized.captureDescriptors.filter((capture) =>
      stableCaptureIds.has(capture.id),
    ),
  };
}

function createBrowserStorageBackend(): DirectorProjectStorageBackend | null {
  if (typeof window === "undefined") return null;
  try {
    const storage = window.localStorage;
    const probeKey = "__liblib_tv_director_storage_probe__";
    storage.setItem(probeKey, "1");
    storage.removeItem(probeKey);
    return storage;
  } catch {
    return null;
  }
}

export function createDirectorProjectStorageKey(
  owner: DirectorProjectOwnerV1,
): string {
  return `liblib-tv-director-project-v1:${encodeURIComponent(
    createDirectorProjectOwnerKey(owner),
  )}`;
}

function rejectLoad(
  key: string,
  reason: DirectorProjectPersistenceLoadReason,
): DirectorProjectPersistenceLoadResult {
  return {
    disposition: "REJECTED",
    reason,
    key,
    document: null,
    projectId: null,
    generation: null,
    fingerprint: null,
  };
}

function decodeEnvelope(
  raw: string,
  key: string,
): DirectorProjectPersistenceLoadResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw) as unknown;
  } catch {
    return rejectLoad(key, "CORRUPT_PAYLOAD");
  }
  if (!isRecord(parsed)) return rejectLoad(key, "INVALID_ENVELOPE");
  const expectedKeys = [
    "storageSchemaVersion",
    "projectId",
    "owner",
    "generation",
    "savedAt",
    "documentFingerprint",
    "document",
  ] as const;
  const actualKeys = Object.keys(parsed);
  if (
    actualKeys.length !== expectedKeys.length ||
    actualKeys.some(
      (candidate) => !(expectedKeys as readonly string[]).includes(candidate),
    )
  ) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  if (
    parsed.storageSchemaVersion !== undefined &&
    typeof parsed.storageSchemaVersion === "number" &&
    Number.isFinite(parsed.storageSchemaVersion) &&
    parsed.storageSchemaVersion >
      DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION
  ) {
    return rejectLoad(key, "FUTURE_STORAGE_SCHEMA");
  }
  if (!isCurrentStorageSchema(parsed.storageSchemaVersion)) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  if (!isNonEmptyString(parsed.projectId)) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  if (!isValidOwner(parsed.owner)) return rejectLoad(key, "INVALID_ENVELOPE");
  if (!isFinitePositiveInteger(parsed.generation)) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  if (!isNonEmptyString(parsed.savedAt)) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  if (!isNonEmptyString(parsed.documentFingerprint)) {
    return rejectLoad(key, "INVALID_ENVELOPE");
  }
  const documentResult = decodeDirectorProjectDocument(parsed.document);
  if (!documentResult.ok) return rejectLoad(key, "INVALID_DOCUMENT");
  const document = documentResult.document;
  if (document.projectId !== parsed.projectId) {
    return rejectLoad(key, "PROJECT_MISMATCH");
  }
  if (!isSameDirectorProjectOwner(document.owner, parsed.owner)) {
    return rejectLoad(key, "OWNER_MISMATCH");
  }
  if (directorDocumentFingerprint(document) !== parsed.documentFingerprint) {
    return rejectLoad(key, "FINGERPRINT_MISMATCH");
  }
  return {
    disposition: "RESTORED",
    reason: null,
    key,
    document,
    projectId: document.projectId,
    generation: parsed.generation,
    fingerprint: parsed.documentFingerprint,
  };
}

function createEnvelope(
  input: DirectorProjectPersistenceSaveInput,
): DirectorProjectStorageEnvelopeV1 | null {
  if (!isValidOwner(input.owner)) return null;
  if (!isNonEmptyString(input.projectId)) return null;
  if (!isFinitePositiveInteger(input.generation)) return null;
  const document = documentForPersistence(input.document);
  if (
    document.projectId !== input.projectId ||
    !isSameDirectorProjectOwner(document.owner, input.owner)
  ) {
    return null;
  }
  return {
    storageSchemaVersion: DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION,
    projectId: input.projectId,
    owner: cloneOwner(input.owner),
    generation: input.generation,
    savedAt: input.savedAt ?? new Date().toISOString(),
    documentFingerprint: directorDocumentFingerprint(document),
    document,
  };
}

export class DirectorProjectPersistenceAuthority {
  private readonly backend: DirectorProjectStorageBackend | null;
  private readonly records = new Map<
    string,
    DirectorProjectPersistenceRecord
  >();
  private readonly latestRequestIds = new Map<string, number>();
  private nextRequestId = 0;

  constructor(backend?: DirectorProjectStorageBackend | null) {
    this.backend =
      backend === undefined ? createBrowserStorageBackend() : backend;
  }

  isAvailable(): boolean {
    return this.backend !== null;
  }

  load(owner: DirectorProjectOwnerV1): DirectorProjectPersistenceLoadResult {
    const key = createDirectorProjectStorageKey(owner);
    if (!this.backend) {
      this.remember(owner, {
        status: "UNAVAILABLE",
        reason: "STORAGE_UNAVAILABLE",
        projectId: null,
        generation: null,
        fingerprint: null,
        savedAt: null,
        lastRequestId: null,
      });
      return rejectLoad(key, "STORAGE_UNAVAILABLE");
    }
    let raw: string | null;
    try {
      raw = this.backend.getItem(key);
    } catch {
      this.remember(owner, {
        status: "UNAVAILABLE",
        reason: "STORAGE_UNAVAILABLE",
        projectId: null,
        generation: null,
        fingerprint: null,
        savedAt: null,
        lastRequestId: null,
      });
      return rejectLoad(key, "STORAGE_UNAVAILABLE");
    }
    if (raw === null) {
      this.remember(owner, {
        status: "MISSING",
        reason: null,
        projectId: null,
        generation: null,
        fingerprint: null,
        savedAt: null,
        lastRequestId: null,
      });
      return {
        disposition: "MISSING",
        reason: null,
        key,
        document: null,
        projectId: null,
        generation: null,
        fingerprint: null,
      };
    }
    const result = decodeEnvelope(raw, key);
    if (result.disposition === "RESTORED" && result.document) {
      this.remember(owner, {
        status: "RESTORED",
        reason: null,
        projectId: result.projectId,
        generation: result.generation,
        fingerprint: result.fingerprint,
        savedAt: this.readSavedAt(raw),
        lastRequestId: null,
      });
    } else {
      this.remember(owner, {
        status: "REJECTED",
        reason: result.reason,
        projectId: null,
        generation: null,
        fingerprint: null,
        savedAt: null,
        lastRequestId: null,
      });
    }
    return result;
  }

  beginSave(
    input: DirectorProjectPersistenceSaveInput,
  ): DirectorProjectPersistenceSaveRequest {
    this.nextRequestId += 1;
    const key = createDirectorProjectStorageKey(input.owner);
    return {
      requestId: this.nextRequestId,
      key,
      input: {
        ...input,
        owner: cloneOwner(input.owner),
        document: cloneDocument(input.document),
      },
    };
  }

  completeSave(
    request: DirectorProjectPersistenceSaveRequest,
  ): DirectorProjectPersistenceSaveResult {
    const { input, key, requestId } = request;
    const latestRequestId = this.latestRequestIds.get(key);
    if (latestRequestId !== undefined && requestId < latestRequestId) {
      this.remember(input.owner, {
        status: "STALE_IGNORED",
        reason: "STALE_REQUEST",
        projectId: input.projectId,
        generation: input.generation,
        fingerprint: null,
        savedAt: null,
        lastRequestId: requestId,
      });
      return {
        disposition: "STALE_IGNORED",
        reason: "STALE_REQUEST",
        key,
        requestId,
        envelope: null,
      };
    }
    this.latestRequestIds.set(key, requestId);
    const envelope = createEnvelope(input);
    if (!envelope) {
      this.remember(input.owner, {
        status: "SESSION_ONLY",
        reason: "INVALID_DOCUMENT",
        projectId: input.projectId,
        generation: input.generation,
        fingerprint: null,
        savedAt: null,
        lastRequestId: requestId,
      });
      return {
        disposition: "REJECTED",
        reason: "INVALID_DOCUMENT",
        key,
        requestId,
        envelope: null,
      };
    }
    if (!this.backend) {
      this.remember(input.owner, {
        status: "SESSION_ONLY",
        reason: "STORAGE_UNAVAILABLE",
        projectId: input.projectId,
        generation: input.generation,
        fingerprint: envelope.documentFingerprint,
        savedAt: envelope.savedAt,
        lastRequestId: requestId,
      });
      return {
        disposition: "REJECTED",
        reason: "STORAGE_UNAVAILABLE",
        key,
        requestId,
        envelope: null,
      };
    }
    try {
      const currentRaw = this.backend.getItem(key);
      if (currentRaw !== null) {
        const current = decodeEnvelope(currentRaw, key);
        if (
          current.disposition === "RESTORED" &&
          current.generation !== null &&
          current.generation > envelope.generation
        ) {
          this.remember(input.owner, {
            status: "STALE_IGNORED",
            reason: "STALE_REQUEST",
            projectId: current.projectId,
            generation: current.generation,
            fingerprint: current.fingerprint,
            savedAt: this.readSavedAt(currentRaw),
            lastRequestId: requestId,
          });
          return {
            disposition: "STALE_IGNORED",
            reason: "STALE_REQUEST",
            key,
            requestId,
            envelope: null,
          };
        }
      }
      this.backend.setItem(key, JSON.stringify(envelope));
    } catch {
      this.remember(input.owner, {
        status: "SESSION_ONLY",
        reason: "WRITE_FAILED",
        projectId: input.projectId,
        generation: input.generation,
        fingerprint: envelope.documentFingerprint,
        savedAt: envelope.savedAt,
        lastRequestId: requestId,
      });
      return {
        disposition: "REJECTED",
        reason: "WRITE_FAILED",
        key,
        requestId,
        envelope: null,
      };
    }
    this.remember(input.owner, {
      status: "SAVED",
      reason: null,
      projectId: envelope.projectId,
      generation: envelope.generation,
      fingerprint: envelope.documentFingerprint,
      savedAt: envelope.savedAt,
      lastRequestId: requestId,
    });
    return {
      disposition: "SAVED",
      reason: null,
      key,
      requestId,
      envelope,
    };
  }

  save(
    input: DirectorProjectPersistenceSaveInput,
  ): DirectorProjectPersistenceSaveResult {
    const request = this.beginSave(input);
    return this.completeSave(request);
  }

  getRecord(owner: DirectorProjectOwnerV1): DirectorProjectPersistenceRecord {
    const key = createDirectorProjectStorageKey(owner);
    const existing = this.records.get(key);
    if (existing) {
      return {
        ...existing,
        owner: cloneOwner(existing.owner),
      };
    }
    return {
      key,
      owner: cloneOwner(owner),
      status: this.backend ? "MISSING" : "UNAVAILABLE",
      reason: this.backend ? null : "STORAGE_UNAVAILABLE",
      projectId: null,
      generation: null,
      fingerprint: null,
      savedAt: null,
      lastRequestId: null,
    };
  }

  getSnapshot(): DirectorProjectPersistenceSnapshot {
    return {
      storageSchemaVersion: DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION,
      available: this.backend !== null,
      records: [...this.records.values()].map((record) => ({
        ...record,
        owner: cloneOwner(record.owner),
      })),
    };
  }

  private remember(
    owner: DirectorProjectOwnerV1,
    patch: Omit<DirectorProjectPersistenceRecord, "key" | "owner">,
  ): void {
    const key = createDirectorProjectStorageKey(owner);
    this.records.set(key, {
      key,
      owner: cloneOwner(owner),
      ...patch,
    });
  }

  private readSavedAt(raw: string): string | null {
    try {
      const parsed: unknown = JSON.parse(raw);
      return isRecord(parsed) && isNonEmptyString(parsed.savedAt)
        ? parsed.savedAt
        : null;
    } catch {
      return null;
    }
  }
}

export const directorProjectPersistence =
  new DirectorProjectPersistenceAuthority();

export function getDirectorProjectPersistenceSnapshot(): DirectorProjectPersistenceSnapshot {
  return directorProjectPersistence.getSnapshot();
}

export function directorProjectPersistenceIdentity(
  owner: DirectorProjectOwnerV1,
  projectId: string,
  generation: number,
): DirectorProjectIdentityV1 {
  return {
    projectId,
    owner: cloneOwner(owner),
    schemaVersion: 1,
    generation,
  };
}
