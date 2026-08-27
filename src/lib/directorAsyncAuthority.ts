import type { DirectorProjectOwnerV1 } from "@/lib/directorProjectDocument";

export type DirectorAsyncOperationKind =
  | "capture"
  | "video-export"
  | "phone-vcam";

export type DirectorAsyncPhase =
  | "progress"
  | "succeeded"
  | "failed"
  | "canceled";

export type DirectorAsyncOperationStatus =
  | "accepted"
  | "progress"
  | "succeeded"
  | "failed"
  | "canceled";

export type DirectorAsyncIngressDisposition =
  | "apply-current"
  | "duplicate-noop"
  | "reject-stale"
  | "reject-invalid";

export type DirectorAsyncIngressReason =
  | "DIRECTOR_ASYNC_INVALID_DESCRIPTOR"
  | "DIRECTOR_ASYNC_INVALID_ENVELOPE"
  | "DIRECTOR_ASYNC_OPERATION_MISSING"
  | "DIRECTOR_ASYNC_OWNER_STALE"
  | "DIRECTOR_ASYNC_SOURCE_STALE"
  | "DIRECTOR_ASYNC_ATTEMPT_STALE"
  | "DIRECTOR_ASYNC_OPERATION_TERMINAL"
  | "DIRECTOR_ASYNC_DUPLICATE_RESULT";

export interface DirectorAsyncOwnerSnapshotV1 {
  owner: DirectorProjectOwnerV1;
  projectId: string;
  sessionId: string;
  generation: number;
}

export interface DirectorAsyncOperationDescriptorV1 {
  operationId: string;
  kind: DirectorAsyncOperationKind;
  owner: DirectorAsyncOwnerSnapshotV1;
  attemptId: string;
  sourceFingerprint: string;
  requestFingerprint: string;
  acceptedAt: string;
  selectionPolicy: "preserve-current" | "select-result";
}

export interface DirectorAsyncResultEnvelopeV1<TPayload = unknown> {
  operationId: string;
  kind: DirectorAsyncOperationKind;
  owner: DirectorAsyncOwnerSnapshotV1;
  attemptId: string;
  sourceFingerprint: string;
  resultId: string;
  resultVersionId: string;
  phase: DirectorAsyncPhase;
  payload: TPayload;
}

export interface DirectorAsyncOperationRecordV1 {
  descriptor: DirectorAsyncOperationDescriptorV1;
  status: DirectorAsyncOperationStatus;
  seenResultKeys: string[];
  terminalResultVersionId: string | null;
}

export interface DirectorAsyncAuthoritySnapshotV1 {
  operations: DirectorAsyncOperationRecordV1[];
  resources: DirectorAsyncResourceRecordV1[];
}

export interface DirectorAsyncBeginResult {
  disposition: "accepted" | "duplicate-noop" | "reject-invalid";
  reason: DirectorAsyncIngressReason | null;
  operation: DirectorAsyncOperationRecordV1 | null;
  supersededAttemptId: string | null;
}

export interface DirectorAsyncIngressContextV1 {
  owner: DirectorAsyncOwnerSnapshotV1;
  sourceFingerprint: string;
}

export interface DirectorAsyncReconcileResult<TPayload = unknown> {
  disposition: DirectorAsyncIngressDisposition;
  reason: DirectorAsyncIngressReason | null;
  operation: DirectorAsyncOperationRecordV1 | null;
  envelope: DirectorAsyncResultEnvelopeV1<TPayload> | null;
}

export type DirectorAsyncResourceStatus =
  | "owned"
  | "transferred"
  | "released";

export interface DirectorAsyncResourceRecordV1 {
  resourceId: string;
  operationId: string;
  status: DirectorAsyncResourceStatus;
  resultVersionId: string | null;
  transferCount: number;
  releaseCount: number;
}

export interface DirectorAsyncResourceResult {
  disposition: "claimed" | "transferred" | "released" | "duplicate-noop" | "reject-invalid";
  resource: DirectorAsyncResourceRecordV1 | null;
}

function cloneOwner(
  owner: DirectorAsyncOwnerSnapshotV1,
): DirectorAsyncOwnerSnapshotV1 {
  return {
    owner: { ...owner.owner },
    projectId: owner.projectId,
    sessionId: owner.sessionId,
    generation: owner.generation,
  };
}

function cloneDescriptor(
  descriptor: DirectorAsyncOperationDescriptorV1,
): DirectorAsyncOperationDescriptorV1 {
  return {
    ...descriptor,
    owner: cloneOwner(descriptor.owner),
  };
}

function cloneOperation(
  operation: DirectorAsyncOperationRecordV1,
): DirectorAsyncOperationRecordV1 {
  return {
    descriptor: cloneDescriptor(operation.descriptor),
    status: operation.status,
    seenResultKeys: [...operation.seenResultKeys],
    terminalResultVersionId: operation.terminalResultVersionId,
  };
}

function cloneResource(
  resource: DirectorAsyncResourceRecordV1,
): DirectorAsyncResourceRecordV1 {
  return { ...resource };
}

function nonEmpty(value: string): boolean {
  return value.length > 0 && value.trim() === value;
}

function isValidOwnerSnapshot(
  owner: DirectorAsyncOwnerSnapshotV1,
): boolean {
  return (
    nonEmpty(owner.projectId) &&
    nonEmpty(owner.sessionId) &&
    Number.isInteger(owner.generation) &&
    owner.generation > 0 &&
    owner.owner.route === "libtv" &&
    nonEmpty(owner.owner.canvasId) &&
    nonEmpty(owner.owner.sourceNodeId)
  );
}

function isSameOwnerSnapshot(
  left: DirectorAsyncOwnerSnapshotV1,
  right: DirectorAsyncOwnerSnapshotV1,
): boolean {
  return (
    left.projectId === right.projectId &&
    left.sessionId === right.sessionId &&
    left.generation === right.generation &&
    left.owner.route === right.owner.route &&
    left.owner.canvasId === right.owner.canvasId &&
    left.owner.sourceNodeId === right.owner.sourceNodeId
  );
}

function isValidDescriptor(
  descriptor: DirectorAsyncOperationDescriptorV1,
): boolean {
  return (
    nonEmpty(descriptor.operationId) &&
    nonEmpty(descriptor.attemptId) &&
    nonEmpty(descriptor.sourceFingerprint) &&
    nonEmpty(descriptor.requestFingerprint) &&
    nonEmpty(descriptor.acceptedAt) &&
    isValidOwnerSnapshot(descriptor.owner) &&
    ["capture", "video-export", "phone-vcam"].includes(descriptor.kind) &&
    ["preserve-current", "select-result"].includes(descriptor.selectionPolicy)
  );
}

function isValidEnvelope<TPayload>(
  envelope: DirectorAsyncResultEnvelopeV1<TPayload>,
): boolean {
  return (
    nonEmpty(envelope.operationId) &&
    nonEmpty(envelope.attemptId) &&
    nonEmpty(envelope.sourceFingerprint) &&
    nonEmpty(envelope.resultId) &&
    nonEmpty(envelope.resultVersionId) &&
    isValidOwnerSnapshot(envelope.owner) &&
    ["capture", "video-export", "phone-vcam"].includes(envelope.kind) &&
    ["progress", "succeeded", "failed", "canceled"].includes(envelope.phase)
  );
}

function resultKey(
  envelope: Pick<
    DirectorAsyncResultEnvelopeV1,
    "attemptId" | "resultVersionId"
  >,
): string {
  return `${envelope.attemptId}:${envelope.resultVersionId}`;
}

function invalidBeginResult(
  reason: DirectorAsyncIngressReason,
): DirectorAsyncBeginResult {
  return {
    disposition: "reject-invalid",
    reason,
    operation: null,
    supersededAttemptId: null,
  };
}

export class DirectorAsyncAuthority {
  private readonly operations = new Map<
    string,
    DirectorAsyncOperationRecordV1
  >();

  private readonly resources = new Map<string, DirectorAsyncResourceRecordV1>();

  begin(
    descriptor: DirectorAsyncOperationDescriptorV1,
  ): DirectorAsyncBeginResult {
    if (!isValidDescriptor(descriptor)) {
      return invalidBeginResult("DIRECTOR_ASYNC_INVALID_DESCRIPTOR");
    }

    const existing = this.operations.get(descriptor.operationId);
    if (!existing) {
      const operation: DirectorAsyncOperationRecordV1 = {
        descriptor: cloneDescriptor(descriptor),
        status: "accepted",
        seenResultKeys: [],
        terminalResultVersionId: null,
      };
      this.operations.set(descriptor.operationId, operation);
      return {
        disposition: "accepted",
        reason: null,
        operation: cloneOperation(operation),
        supersededAttemptId: null,
      };
    }

    const sameOperation =
      existing.descriptor.kind === descriptor.kind &&
      isSameOwnerSnapshot(existing.descriptor.owner, descriptor.owner) &&
      existing.descriptor.sourceFingerprint === descriptor.sourceFingerprint &&
      existing.descriptor.requestFingerprint === descriptor.requestFingerprint;
    if (!sameOperation) {
      return invalidBeginResult("DIRECTOR_ASYNC_INVALID_DESCRIPTOR");
    }
    if (existing.descriptor.attemptId === descriptor.attemptId) {
      return {
        disposition: "duplicate-noop",
        reason: "DIRECTOR_ASYNC_DUPLICATE_RESULT",
        operation: cloneOperation(existing),
        supersededAttemptId: null,
      };
    }

    const supersededAttemptId = existing.descriptor.attemptId;
    const nextOperation: DirectorAsyncOperationRecordV1 = {
      ...existing,
      descriptor: cloneDescriptor(descriptor),
      status: "accepted",
      terminalResultVersionId: null,
    };
    this.operations.set(descriptor.operationId, nextOperation);
    return {
      disposition: "accepted",
      reason: null,
      operation: cloneOperation(nextOperation),
      supersededAttemptId,
    };
  }

  reconcile<TPayload>(
    envelope: DirectorAsyncResultEnvelopeV1<TPayload>,
    context: DirectorAsyncIngressContextV1,
  ): DirectorAsyncReconcileResult<TPayload> {
    if (!isValidEnvelope(envelope)) {
      return {
        disposition: "reject-invalid",
        reason: "DIRECTOR_ASYNC_INVALID_ENVELOPE",
        operation: null,
        envelope: null,
      };
    }

    const operation = this.operations.get(envelope.operationId);
    if (!operation) {
      return {
        disposition: "reject-stale",
        reason: "DIRECTOR_ASYNC_OPERATION_MISSING",
        operation: null,
        envelope: null,
      };
    }

    if (
      !isSameOwnerSnapshot(operation.descriptor.owner, context.owner) ||
      !isSameOwnerSnapshot(operation.descriptor.owner, envelope.owner)
    ) {
      return {
        disposition: "reject-stale",
        reason: "DIRECTOR_ASYNC_OWNER_STALE",
        operation: cloneOperation(operation),
        envelope: null,
      };
    }
    if (context.sourceFingerprint !== operation.descriptor.sourceFingerprint) {
      return {
        disposition: "reject-stale",
        reason: "DIRECTOR_ASYNC_SOURCE_STALE",
        operation: cloneOperation(operation),
        envelope: null,
      };
    }
    if (
      envelope.kind !== operation.descriptor.kind ||
      envelope.sourceFingerprint !== operation.descriptor.sourceFingerprint
    ) {
      return {
        disposition: "reject-invalid",
        reason: "DIRECTOR_ASYNC_INVALID_ENVELOPE",
        operation: cloneOperation(operation),
        envelope: null,
      };
    }
    if (envelope.attemptId !== operation.descriptor.attemptId) {
      return {
        disposition: "reject-stale",
        reason: "DIRECTOR_ASYNC_ATTEMPT_STALE",
        operation: cloneOperation(operation),
        envelope: null,
      };
    }

    const key = resultKey(envelope);
    if (operation.seenResultKeys.includes(key)) {
      return {
        disposition: "duplicate-noop",
        reason: "DIRECTOR_ASYNC_DUPLICATE_RESULT",
        operation: cloneOperation(operation),
        envelope: cloneEnvelope(envelope),
      };
    }
    if (
      operation.terminalResultVersionId !== null ||
      ["succeeded", "failed", "canceled"].includes(operation.status)
    ) {
      return {
        disposition: "reject-stale",
        reason: "DIRECTOR_ASYNC_OPERATION_TERMINAL",
        operation: cloneOperation(operation),
        envelope: null,
      };
    }

    const nextOperation: DirectorAsyncOperationRecordV1 = {
      ...operation,
      status:
        envelope.phase === "progress" ? "progress" : envelope.phase,
      seenResultKeys: [...operation.seenResultKeys, key],
      terminalResultVersionId:
        envelope.phase === "progress" ? null : envelope.resultVersionId,
    };
    this.operations.set(envelope.operationId, nextOperation);
    return {
      disposition: "apply-current",
      reason: null,
      operation: cloneOperation(nextOperation),
      envelope: cloneEnvelope(envelope),
    };
  }

  claimResource(
    resourceId: string,
    operationId: string,
  ): DirectorAsyncResourceResult {
    if (!nonEmpty(resourceId) || !nonEmpty(operationId)) {
      return { disposition: "reject-invalid", resource: null };
    }
    const existing = this.resources.get(resourceId);
    if (existing) {
      if (existing.operationId !== operationId) {
        return { disposition: "reject-invalid", resource: cloneResource(existing) };
      }
      return {
        disposition: "duplicate-noop",
        resource: cloneResource(existing),
      };
    }
    const resource: DirectorAsyncResourceRecordV1 = {
      resourceId,
      operationId,
      status: "owned",
      resultVersionId: null,
      transferCount: 0,
      releaseCount: 0,
    };
    this.resources.set(resourceId, resource);
    return { disposition: "claimed", resource: cloneResource(resource) };
  }

  transferResource(
    resourceId: string,
    operationId: string,
    resultVersionId: string,
  ): DirectorAsyncResourceResult {
    const resource = this.resources.get(resourceId);
    if (
      !resource ||
      resource.operationId !== operationId ||
      !nonEmpty(resultVersionId)
    ) {
      return { disposition: "reject-invalid", resource: resource ? cloneResource(resource) : null };
    }
    if (resource.status === "transferred") {
      return {
        disposition:
          resource.resultVersionId === resultVersionId
            ? "duplicate-noop"
            : "reject-invalid",
        resource: cloneResource(resource),
      };
    }
    if (resource.status === "released") {
      return { disposition: "reject-invalid", resource: cloneResource(resource) };
    }
    const nextResource: DirectorAsyncResourceRecordV1 = {
      ...resource,
      status: "transferred",
      resultVersionId,
      transferCount: resource.transferCount + 1,
    };
    this.resources.set(resourceId, nextResource);
    return { disposition: "transferred", resource: cloneResource(nextResource) };
  }

  releaseResource(
    resourceId: string,
    operationId: string,
  ): DirectorAsyncResourceResult {
    const resource = this.resources.get(resourceId);
    if (!resource || resource.operationId !== operationId) {
      return { disposition: "reject-invalid", resource: resource ? cloneResource(resource) : null };
    }
    if (resource.status === "released") {
      return {
        disposition: "duplicate-noop",
        resource: cloneResource(resource),
      };
    }
    if (resource.status === "transferred") {
      return { disposition: "reject-invalid", resource: cloneResource(resource) };
    }
    const nextResource: DirectorAsyncResourceRecordV1 = {
      ...resource,
      status: "released",
      releaseCount: resource.releaseCount + 1,
    };
    this.resources.set(resourceId, nextResource);
    return { disposition: "released", resource: cloneResource(nextResource) };
  }

  getSnapshot(): DirectorAsyncAuthoritySnapshotV1 {
    return {
      operations: [...this.operations.values()].map(cloneOperation),
      resources: [...this.resources.values()].map(cloneResource),
    };
  }
}

function cloneEnvelope<TPayload>(
  envelope: DirectorAsyncResultEnvelopeV1<TPayload>,
): DirectorAsyncResultEnvelopeV1<TPayload> {
  return {
    ...envelope,
    owner: cloneOwner(envelope.owner),
  };
}

export const directorAsyncAuthority = new DirectorAsyncAuthority();

let directorAsyncIdentitySequence = 0;

export function createDirectorAsyncIdentity(prefix: string): string {
  directorAsyncIdentitySequence += 1;
  return `${prefix}-${Date.now()}-${directorAsyncIdentitySequence}`;
}
