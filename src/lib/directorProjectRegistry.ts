import type {
  DirectorProjectDocumentV1,
  DirectorProjectOwnerV1,
} from "@/lib/directorProjectDocument";
import type { DirectorCapture } from "@/store/directorStore";

export type DirectorProjectLifecycle = "ACTIVE" | "CLOSED" | "TOMBSTONED";

export interface DirectorProjectIdentityV1 {
  projectId: string;
  owner: DirectorProjectOwnerV1;
  schemaVersion: 1;
  generation: number;
}

export interface DirectorProjectMemorySidecarV1 {
  captures: DirectorCapture[];
}

export interface DirectorProjectRecordV1 {
  identity: DirectorProjectIdentityV1;
  document: DirectorProjectDocumentV1;
  lifecycle: DirectorProjectLifecycle;
  memory: DirectorProjectMemorySidecarV1;
}

export interface DirectorProjectCopyRegistrationV1 {
  owner: DirectorProjectOwnerV1;
  projectId: string;
  generation: number;
  document: DirectorProjectDocumentV1;
  captures: DirectorCapture[];
}

export type DirectorProjectCopyRegistrationResult =
  | {
      disposition: "COMMITTED";
      records: DirectorProjectRecordV1[];
    }
  | {
      disposition: "REJECTED";
      reason:
        | "INVALID_OWNER"
        | "INVALID_DOCUMENT"
        | "IDENTITY_CONFLICT";
      records: [];
    };

export interface DirectorSessionV1 {
  sessionId: string;
  projectId: string;
  owner: DirectorProjectOwnerV1;
  generation: number;
  openedAt: string;
}

export type DirectorProjectRegistryReason =
  | "INVALID_OWNER"
  | "INVALID_DOCUMENT"
  | "PROJECT_TOMBSTONED"
  | "NO_ACTIVE_SESSION"
  | "OWNER_STALE";

export type DirectorProjectOpenDisposition =
  | "CREATED"
  | "RESTORED"
  | "FOCUSED"
  | "REJECTED";

export interface DirectorProjectOpenResult {
  disposition: DirectorProjectOpenDisposition;
  reason: DirectorProjectRegistryReason | null;
  record: DirectorProjectRecordV1 | null;
  session: DirectorSessionV1 | null;
  previousOwnerKey: string | null;
}

export type DirectorProjectCloseDisposition =
  | "CLOSED"
  | "NOOP"
  | "STALE"
  | "REJECTED";

export interface DirectorProjectCloseResult {
  disposition: DirectorProjectCloseDisposition;
  reason: DirectorProjectRegistryReason | null;
  record: DirectorProjectRecordV1 | null;
}

export type DirectorProjectUpdateDisposition =
  | "COMMITTED"
  | "STALE"
  | "REJECTED";

export interface DirectorProjectUpdateResult {
  disposition: DirectorProjectUpdateDisposition;
  reason: DirectorProjectRegistryReason | null;
  record: DirectorProjectRecordV1 | null;
}

export interface DirectorProjectRegistrySnapshot {
  activeSession: DirectorSessionV1 | null;
  records: DirectorProjectRecordV1[];
}

interface DirectorProjectRegistryDependencies {
  normalizeDocument: (
    document: DirectorProjectDocumentV1,
  ) => DirectorProjectDocumentV1;
  createProjectId: (ownerKey: string) => string;
  createSessionId: (projectId: string, generation: number) => string;
  now: () => string;
}

interface OpenDirectorProjectInput {
  owner: DirectorProjectOwnerV1;
  createDocument: (
    projectId: string,
    owner: DirectorProjectOwnerV1,
  ) => DirectorProjectDocumentV1;
  persistedDocument?: DirectorProjectDocumentV1 | null;
  persistedGeneration?: number | null;
}

interface CommitDirectorProjectInput {
  owner: DirectorProjectOwnerV1;
  projectId: string;
  generation: number;
  document: DirectorProjectDocumentV1;
  captures: DirectorCapture[];
}

let directorProjectIdentitySequence = 0;

function nextDirectorIdentity(prefix: string): string {
  directorProjectIdentitySequence += 1;
  return `${prefix}-${Date.now()}-${directorProjectIdentitySequence}`;
}

const defaultDependencies: Omit<
  DirectorProjectRegistryDependencies,
  "normalizeDocument"
> = {
  createProjectId: () => nextDirectorIdentity("director-project"),
  createSessionId: () => nextDirectorIdentity("director-session"),
  now: () => new Date().toISOString(),
};

function cloneOwner(owner: DirectorProjectOwnerV1): DirectorProjectOwnerV1 {
  return {
    route: "libtv",
    canvasId: owner.canvasId,
    sourceNodeId: owner.sourceNodeId,
  };
}

function cloneCapture(capture: DirectorCapture): DirectorCapture {
  return { ...capture };
}

function cloneSession(session: DirectorSessionV1): DirectorSessionV1 {
  return {
    ...session,
    owner: cloneOwner(session.owner),
  };
}

function cloneRecord(
  record: DirectorProjectRecordV1,
  normalizeDocument: DirectorProjectRegistryDependencies["normalizeDocument"],
): DirectorProjectRecordV1 {
  return {
    identity: {
      ...record.identity,
      owner: cloneOwner(record.identity.owner),
    },
    document: normalizeDocument(record.document),
    lifecycle: record.lifecycle,
    memory: {
      captures: record.memory.captures.map(cloneCapture),
    },
  };
}

function isValidOwner(owner: DirectorProjectOwnerV1): boolean {
  return (
    owner.route === "libtv" &&
    owner.canvasId.length > 0 &&
    owner.canvasId.trim() === owner.canvasId &&
    owner.sourceNodeId.length > 0 &&
    owner.sourceNodeId.trim() === owner.sourceNodeId
  );
}

export function createDirectorProjectOwnerKey(
  owner: DirectorProjectOwnerV1,
): string {
  return JSON.stringify([owner.route, owner.canvasId, owner.sourceNodeId]);
}

export function isSameDirectorProjectOwner(
  left: DirectorProjectOwnerV1,
  right: DirectorProjectOwnerV1,
): boolean {
  return (
    left.route === right.route &&
    left.canvasId === right.canvasId &&
    left.sourceNodeId === right.sourceNodeId
  );
}

function hasMatchingDocumentIdentity(
  document: DirectorProjectDocumentV1,
  projectId: string,
  owner: DirectorProjectOwnerV1,
): boolean {
  return (
    document.projectId === projectId &&
    isSameDirectorProjectOwner(document.owner, owner)
  );
}

export class DirectorProjectRegistry {
  private readonly records = new Map<string, DirectorProjectRecordV1>();
  private activeSession: DirectorSessionV1 | null = null;
  private readonly dependencies: DirectorProjectRegistryDependencies;

  constructor(
    dependencies: Pick<
      DirectorProjectRegistryDependencies,
      "normalizeDocument"
    > &
      Partial<
        Omit<DirectorProjectRegistryDependencies, "normalizeDocument">
      >,
  ) {
    this.dependencies = { ...defaultDependencies, ...dependencies };
  }

  getActiveSession(): DirectorSessionV1 | null {
    return this.activeSession ? cloneSession(this.activeSession) : null;
  }

  getRecord(owner: DirectorProjectOwnerV1): DirectorProjectRecordV1 | null {
    const record = this.records.get(createDirectorProjectOwnerKey(owner));
    return record
      ? cloneRecord(record, this.dependencies.normalizeDocument)
      : null;
  }

  getSnapshot(): DirectorProjectRegistrySnapshot {
    return {
      activeSession: this.getActiveSession(),
      records: [...this.records.values()].map((record) =>
        cloneRecord(record, this.dependencies.normalizeDocument),
      ),
    };
  }

  open(input: OpenDirectorProjectInput): DirectorProjectOpenResult {
    const { owner } = input;
    if (!isValidOwner(owner)) {
      return {
        disposition: "REJECTED",
        reason: "INVALID_OWNER",
        record: null,
        session: null,
        previousOwnerKey: null,
      };
    }

    const ownerKey = createDirectorProjectOwnerKey(owner);
    const previousOwnerKey = this.activeSession
      ? createDirectorProjectOwnerKey(this.activeSession.owner)
      : null;
    if (this.activeSession && previousOwnerKey === ownerKey) {
      const record = this.records.get(ownerKey);
      return {
        disposition: "FOCUSED",
        reason: null,
        record: record
          ? cloneRecord(record, this.dependencies.normalizeDocument)
          : null,
        session: cloneSession(this.activeSession),
        previousOwnerKey,
      };
    }

    const existing = this.records.get(ownerKey);
    if (existing?.lifecycle === "TOMBSTONED") {
      return {
        disposition: "REJECTED",
        reason: "PROJECT_TOMBSTONED",
        record: null,
        session: null,
        previousOwnerKey,
      };
    }

    let nextDocument: DirectorProjectDocumentV1;
    let projectId: string;
    let disposition: DirectorProjectOpenDisposition;
    if (existing) {
      projectId = existing.identity.projectId;
      nextDocument = this.dependencies.normalizeDocument(existing.document);
      disposition = "RESTORED";
    } else if (input.persistedDocument) {
      projectId = input.persistedDocument.projectId;
      try {
        nextDocument = this.dependencies.normalizeDocument(
          input.persistedDocument,
        );
      } catch {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          record: null,
          session: null,
          previousOwnerKey,
        };
      }
      if (!hasMatchingDocumentIdentity(nextDocument, projectId, owner)) {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          record: null,
          session: null,
          previousOwnerKey,
        };
      }
      disposition = "RESTORED";
    } else {
      projectId = this.dependencies.createProjectId(ownerKey);
      try {
        nextDocument = this.dependencies.normalizeDocument(
          input.createDocument(projectId, cloneOwner(owner)),
        );
      } catch {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          record: null,
          session: null,
          previousOwnerKey,
        };
      }
      if (!hasMatchingDocumentIdentity(nextDocument, projectId, owner)) {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          record: null,
          session: null,
          previousOwnerKey,
        };
      }
      disposition = "CREATED";
    }

    const generation = existing
      ? existing.identity.generation + 1
      : (input.persistedGeneration ?? 0) + 1;
    const nextRecord: DirectorProjectRecordV1 = {
      identity: {
        projectId,
        owner: cloneOwner(owner),
        schemaVersion: 1,
        generation,
      },
      document: nextDocument,
      lifecycle: "ACTIVE",
      memory: existing
        ? {
            captures: existing.memory.captures.map(cloneCapture),
          }
        : { captures: [] },
    };
    const nextSession: DirectorSessionV1 = {
      sessionId: this.dependencies.createSessionId(projectId, generation),
      projectId,
      owner: cloneOwner(owner),
      generation,
      openedAt: this.dependencies.now(),
    };

    if (this.activeSession && previousOwnerKey) {
      const previousRecord = this.records.get(previousOwnerKey);
      if (previousRecord) {
        this.records.set(previousOwnerKey, {
          ...previousRecord,
          lifecycle: "CLOSED",
        });
      }
    }
    this.records.set(ownerKey, nextRecord);
    this.activeSession = nextSession;

    return {
      disposition,
      reason: null,
      record: cloneRecord(nextRecord, this.dependencies.normalizeDocument),
      session: cloneSession(nextSession),
      previousOwnerKey,
    };
  }

  updateActive(input: CommitDirectorProjectInput): DirectorProjectUpdateResult {
    const activeSession = this.activeSession;
    if (!activeSession) {
      return {
        disposition: "STALE",
        reason: "NO_ACTIVE_SESSION",
        record: null,
      };
    }
    if (
      !isSameDirectorProjectOwner(activeSession.owner, input.owner) ||
      activeSession.projectId !== input.projectId ||
      activeSession.generation !== input.generation
    ) {
      return {
        disposition: "STALE",
        reason: "OWNER_STALE",
        record: null,
      };
    }

    let document: DirectorProjectDocumentV1;
    try {
      document = this.dependencies.normalizeDocument(input.document);
    } catch {
      return {
        disposition: "REJECTED",
        reason: "INVALID_DOCUMENT",
        record: null,
      };
    }
    if (
      !hasMatchingDocumentIdentity(document, input.projectId, input.owner)
    ) {
      return {
        disposition: "REJECTED",
        reason: "INVALID_DOCUMENT",
        record: null,
      };
    }

    const ownerKey = createDirectorProjectOwnerKey(input.owner);
    const currentRecord = this.records.get(ownerKey);
    if (!currentRecord || currentRecord.lifecycle === "TOMBSTONED") {
      return {
        disposition: "STALE",
        reason: "OWNER_STALE",
        record: null,
      };
    }
    const nextRecord: DirectorProjectRecordV1 = {
      ...currentRecord,
      document,
      memory: {
        captures: input.captures.map(cloneCapture),
      },
    };
    this.records.set(ownerKey, nextRecord);
    return {
      disposition: "COMMITTED",
      reason: null,
      record: cloneRecord(nextRecord, this.dependencies.normalizeDocument),
    };
  }

  close(input: CommitDirectorProjectInput): DirectorProjectCloseResult {
    if (!this.activeSession) {
      return {
        disposition: "NOOP",
        reason: "NO_ACTIVE_SESSION",
        record: null,
      };
    }
    const update = this.updateActive(input);
    if (update.disposition !== "COMMITTED" || !update.record) {
      return {
        disposition:
          update.disposition === "STALE" ? "STALE" : "REJECTED",
        reason: update.reason,
        record: null,
      };
    }

    const ownerKey = createDirectorProjectOwnerKey(input.owner);
    const nextRecord: DirectorProjectRecordV1 = {
      ...update.record,
      lifecycle: "CLOSED",
    };
    this.records.set(ownerKey, nextRecord);
    this.activeSession = null;
    return {
      disposition: "CLOSED",
      reason: null,
      record: cloneRecord(nextRecord, this.dependencies.normalizeDocument),
    };
  }

  tombstone(owner: DirectorProjectOwnerV1): DirectorProjectCloseResult {
    if (!isValidOwner(owner)) {
      return {
        disposition: "REJECTED",
        reason: "INVALID_OWNER",
        record: null,
      };
    }
    const ownerKey = createDirectorProjectOwnerKey(owner);
    const record = this.records.get(ownerKey);
    if (!record) {
      return {
        disposition: "NOOP",
        reason: null,
        record: null,
      };
    }
    const nextRecord: DirectorProjectRecordV1 = {
      ...record,
      identity: {
        ...record.identity,
        generation: record.identity.generation + 1,
      },
      lifecycle: "TOMBSTONED",
    };
    this.records.set(ownerKey, nextRecord);
    if (
      this.activeSession &&
      createDirectorProjectOwnerKey(this.activeSession.owner) === ownerKey
    ) {
      this.activeSession = null;
    }
    return {
      disposition: "CLOSED",
      reason: null,
      record: cloneRecord(nextRecord, this.dependencies.normalizeDocument),
    };
  }

  registerCopies(
    inputs: readonly DirectorProjectCopyRegistrationV1[],
  ): DirectorProjectCopyRegistrationResult {
    const stagedRecords: DirectorProjectRecordV1[] = [];
    const ownerKeys = new Set<string>();
    const projectIds = new Set<string>();

    for (const input of inputs) {
      if (
        !isValidOwner(input.owner) ||
        typeof input.projectId !== "string" ||
        input.projectId.trim().length === 0 ||
        !Number.isInteger(input.generation) ||
        input.generation <= 0
      ) {
        return {
          disposition: "REJECTED",
          reason: "INVALID_OWNER",
          records: [],
        };
      }
      const ownerKey = createDirectorProjectOwnerKey(input.owner);
      if (
        ownerKeys.has(ownerKey) ||
        this.records.has(ownerKey) ||
        projectIds.has(input.projectId) ||
        [...this.records.values()].some(
          (record) => record.identity.projectId === input.projectId,
        )
      ) {
        return {
          disposition: "REJECTED",
          reason: "IDENTITY_CONFLICT",
          records: [],
        };
      }
      let document: DirectorProjectDocumentV1;
      try {
        document = this.dependencies.normalizeDocument(input.document);
      } catch {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          records: [],
        };
      }
      if (!hasMatchingDocumentIdentity(document, input.projectId, input.owner)) {
        return {
          disposition: "REJECTED",
          reason: "INVALID_DOCUMENT",
          records: [],
        };
      }
      ownerKeys.add(ownerKey);
      projectIds.add(input.projectId);
      stagedRecords.push({
        identity: {
          projectId: input.projectId,
          owner: cloneOwner(input.owner),
          schemaVersion: 1,
          generation: input.generation,
        },
        document,
        lifecycle: "CLOSED",
        memory: {
          captures: input.captures.map(cloneCapture),
        },
      });
    }

    stagedRecords.forEach((record) => {
      this.records.set(
        createDirectorProjectOwnerKey(record.identity.owner),
        record,
      );
    });
    return {
      disposition: "COMMITTED",
      records: stagedRecords.map((record) =>
        cloneRecord(record, this.dependencies.normalizeDocument),
      ),
    };
  }
}
