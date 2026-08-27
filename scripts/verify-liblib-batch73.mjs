import assert from "node:assert/strict";
import {
  DirectorAsyncAuthority,
  createDirectorAsyncIdentity,
} from "../src/lib/directorAsyncAuthority.ts";

const owner = {
  owner: {
    route: "libtv",
    canvasId: "batch73-canvas",
    sourceNodeId: "batch73-source",
  },
  projectId: "batch73-project",
  sessionId: "batch73-session",
  generation: 7,
};

const context = (sourceFingerprint = "source@v1") => ({
  owner,
  sourceFingerprint,
});

const descriptor = (attemptId, sourceFingerprint = "source@v1") => ({
  operationId: "batch73-export",
  kind: "video-export",
  owner,
  attemptId,
  sourceFingerprint,
  requestFingerprint: "duration=4;aspect=16:9",
  acceptedAt: "2026-08-27T12:00:00.000Z",
  selectionPolicy: "select-result",
});

const envelope = (attemptId, resultVersionId, phase = "succeeded") => ({
  operationId: "batch73-export",
  kind: "video-export",
  owner,
  attemptId,
  sourceFingerprint: "source@v1",
  resultId: resultVersionId,
  resultVersionId,
  phase,
  payload: { resultVersionId },
});

const authority = new DirectorAsyncAuthority();
const first = authority.begin(descriptor("attempt-1"));
assert.equal(first.disposition, "accepted");
assert.equal(first.operation?.status, "accepted");

const progress = authority.reconcile(
  envelope("attempt-1", "result-1-progress", "progress"),
  context(),
);
assert.equal(progress.disposition, "apply-current");
assert.equal(progress.operation?.status, "progress");

const current = authority.reconcile(
  envelope("attempt-1", "result-1"),
  context(),
);
assert.equal(current.disposition, "apply-current");
assert.equal(current.operation?.status, "succeeded");

const duplicate = authority.reconcile(
  envelope("attempt-1", "result-1"),
  context(),
);
assert.equal(duplicate.disposition, "duplicate-noop");
assert.equal(duplicate.reason, "DIRECTOR_ASYNC_DUPLICATE_RESULT");

const terminalConflict = authority.reconcile(
  envelope("attempt-1", "result-2"),
  context(),
);
assert.equal(terminalConflict.disposition, "reject-stale");
assert.equal(terminalConflict.reason, "DIRECTOR_ASYNC_OPERATION_TERMINAL");

const staleOwner = authority.reconcile(
  envelope("attempt-1", "result-owner-stale"),
  {
    owner: {
      ...owner,
      sessionId: "batch73-session-reopened",
      generation: 8,
    },
    sourceFingerprint: "source@v1",
  },
);
assert.equal(staleOwner.disposition, "reject-stale");
assert.equal(staleOwner.reason, "DIRECTOR_ASYNC_OWNER_STALE");

const retry = authority.begin(descriptor("attempt-2"));
assert.equal(retry.disposition, "accepted");
assert.equal(retry.supersededAttemptId, "attempt-1");

const oldAttempt = authority.reconcile(
  envelope("attempt-1", "result-old-attempt"),
  context(),
);
assert.equal(oldAttempt.disposition, "reject-stale");
assert.equal(oldAttempt.reason, "DIRECTOR_ASYNC_ATTEMPT_STALE");

const sourceDrift = authority.reconcile(
  envelope("attempt-2", "result-source-stale"),
  context("source@v2"),
);
assert.equal(sourceDrift.disposition, "reject-stale");
assert.equal(sourceDrift.reason, "DIRECTOR_ASYNC_SOURCE_STALE");

const retryCurrent = authority.reconcile(
  envelope("attempt-2", "result-retry"),
  context(),
);
assert.equal(retryCurrent.disposition, "apply-current");

const invalidBegin = authority.begin({
  ...descriptor(""),
  operationId: "",
});
assert.equal(invalidBegin.disposition, "reject-invalid");
assert.equal(invalidBegin.reason, "DIRECTOR_ASYNC_INVALID_DESCRIPTOR");

const invalidEnvelope = authority.reconcile(
  {
    ...envelope("attempt-2", "result-invalid"),
    resultVersionId: "",
  },
  context(),
);
assert.equal(invalidEnvelope.disposition, "reject-invalid");
assert.equal(invalidEnvelope.reason, "DIRECTOR_ASYNC_INVALID_ENVELOPE");

const resourceAuthority = new DirectorAsyncAuthority();
const resourceOperationId = createDirectorAsyncIdentity("batch73-resource");
assert.equal(
  resourceAuthority.claimResource("blob:batch73", resourceOperationId)
    .disposition,
  "claimed",
);
assert.equal(
  resourceAuthority.transferResource(
    "blob:batch73",
    resourceOperationId,
    "result-resource-v1",
  ).disposition,
  "transferred",
);
assert.equal(
  resourceAuthority.transferResource(
    "blob:batch73",
    resourceOperationId,
    "result-resource-v1",
  ).disposition,
  "duplicate-noop",
);
assert.equal(
  resourceAuthority.releaseResource("blob:batch73", resourceOperationId)
    .disposition,
  "reject-invalid",
);

const releaseOperationId = createDirectorAsyncIdentity("batch73-release");
assert.equal(
  resourceAuthority.claimResource("blob:batch73-release", releaseOperationId)
    .disposition,
  "claimed",
);
assert.equal(
  resourceAuthority.releaseResource("blob:batch73-release", releaseOperationId)
    .disposition,
  "released",
);
assert.equal(
  resourceAuthority.releaseResource("blob:batch73-release", releaseOperationId)
    .disposition,
  "duplicate-noop",
);

const snapshot = authority.getSnapshot();
assert.equal(snapshot.operations.length, 1);
assert.equal(snapshot.operations[0].descriptor.attemptId, "attempt-2");
assert.equal(snapshot.operations[0].status, "succeeded");
assert.deepEqual(snapshot.operations[0].seenResultKeys, [
  "attempt-1:result-1-progress",
  "attempt-1:result-1",
  "attempt-2:result-retry",
]);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      batch: 73,
      scenarios: [
        "current progress and terminal apply",
        "owner/session/generation stale",
        "source fingerprint drift",
        "retry attempt supersession",
        "duplicate terminal delivery",
        "terminal conflict",
        "invalid descriptor and envelope",
        "resource transfer exactly once",
        "resource release exactly once",
      ],
      snapshot: {
        operationStatus: snapshot.operations[0].status,
        currentAttemptId: snapshot.operations[0].descriptor.attemptId,
        seenResultKeys: snapshot.operations[0].seenResultKeys,
      },
      errors: [],
    },
    null,
    2,
  ),
);
