import assert from "node:assert/strict";
import {
  collectLiveDirectorProjectOwners,
  createDirectorOwnerReachabilitySignature,
  planDirectorOwnerReachability,
} from "../src/lib/directorOwnerReconciliation.ts";
import {
  DirectorProjectRegistry,
  createDirectorProjectOwnerKey,
} from "../src/lib/directorProjectRegistry.ts";
import { DirectorAsyncAuthority } from "../src/lib/directorAsyncAuthority.ts";

const ownerA = {
  route: "libtv",
  canvasId: "canvas-a",
  sourceNodeId: "source-a",
};
const ownerB = {
  route: "libtv",
  canvasId: "canvas-a",
  sourceNodeId: "source-b",
};
const ownerC = {
  route: "libtv",
  canvasId: "canvas-b",
  sourceNodeId: "source-c",
};
const ownerDeleted = {
  route: "libtv",
  canvasId: "canvas-deleted",
  sourceNodeId: "source-deleted",
};

function createRecord(owner, lifecycle, generation = 1) {
  return {
    identity: {
      projectId: `project-${owner.sourceNodeId}`,
      owner,
      schemaVersion: 1,
      generation,
    },
    document: {
      projectId: `project-${owner.sourceNodeId}`,
      owner,
    },
    lifecycle,
    memory: { captures: [] },
  };
}

const canvases = [
  {
    id: "canvas-a",
    nodes: [{ id: "source-a" }, { id: "source-b" }, { id: "unrelated" }],
  },
  {
    id: "canvas-b",
    nodes: [{ id: "source-c" }],
  },
];
const collectedOwners = collectLiveDirectorProjectOwners(canvases);
assert.equal(collectedOwners.length, 4);
assert.equal(
  createDirectorOwnerReachabilitySignature(canvases),
  [
    createDirectorProjectOwnerKey(ownerA),
    createDirectorProjectOwnerKey(ownerB),
    createDirectorProjectOwnerKey({
      route: "libtv",
      canvasId: "canvas-a",
      sourceNodeId: "unrelated",
    }),
    createDirectorProjectOwnerKey(ownerC),
  ]
    .sort()
    .join("\n"),
);

const baseRegistry = {
  activeSession: {
    sessionId: "session-a",
    projectId: "project-source-a",
    owner: ownerA,
    generation: 1,
    openedAt: "2026-08-27T10:00:00.000Z",
  },
  records: [
    createRecord(ownerC, "CLOSED"),
    createRecord(ownerDeleted, "TOMBSTONED", 4),
    createRecord(ownerA, "ACTIVE"),
    createRecord(ownerB, "CLOSED"),
  ],
};

const preserveAll = planDirectorOwnerReachability({
  liveOwners: collectedOwners,
  registry: baseRegistry,
});
assert.deepEqual(preserveAll.tombstoneOwners, []);
assert.equal(preserveAll.activeOwnerInvalidated, false);
assert.deepEqual(
  preserveAll.preservedOwnerKeys,
  [
    createDirectorProjectOwnerKey(ownerA),
    createDirectorProjectOwnerKey(ownerB),
    createDirectorProjectOwnerKey(ownerC),
  ].sort(),
);
assert.deepEqual(preserveAll.alreadyTombstonedOwnerKeys, [
  createDirectorProjectOwnerKey(ownerDeleted),
]);

const inactiveSourceDelete = planDirectorOwnerReachability({
  liveOwners: collectedOwners.filter(
    (owner) => createDirectorProjectOwnerKey(owner) !== createDirectorProjectOwnerKey(ownerB),
  ),
  registry: baseRegistry,
});
assert.deepEqual(inactiveSourceDelete.tombstoneOwnerKeys, [
  createDirectorProjectOwnerKey(ownerB),
]);
assert.equal(inactiveSourceDelete.activeOwnerInvalidated, false);

const inactiveCanvasDelete = planDirectorOwnerReachability({
  liveOwners: collectedOwners.filter((owner) => owner.canvasId !== "canvas-b"),
  registry: baseRegistry,
});
assert.deepEqual(inactiveCanvasDelete.tombstoneOwnerKeys, [
  createDirectorProjectOwnerKey(ownerC),
]);
assert.equal(inactiveCanvasDelete.activeOwnerInvalidated, false);

const activeSourceDelete = planDirectorOwnerReachability({
  liveOwners: collectedOwners.filter(
    (owner) => createDirectorProjectOwnerKey(owner) !== createDirectorProjectOwnerKey(ownerA),
  ),
  registry: baseRegistry,
});
assert.deepEqual(activeSourceDelete.tombstoneOwnerKeys, [
  createDirectorProjectOwnerKey(ownerA),
]);
assert.equal(activeSourceDelete.activeOwnerInvalidated, true);

const invalidAndDuplicate = planDirectorOwnerReachability({
  liveOwners: [
    ownerA,
    ownerA,
    { ...ownerB, canvasId: " canvas-a" },
  ],
  registry: baseRegistry,
});
assert.equal(invalidAndDuplicate.invalidLiveOwnerCount, 1);
assert.equal(
  invalidAndDuplicate.liveOwnerKeys.filter(
    (key) => key === createDirectorProjectOwnerKey(ownerA),
  ).length,
  1,
);

const deterministic = planDirectorOwnerReachability({
  liveOwners: [...collectedOwners].reverse(),
  registry: {
    activeSession: baseRegistry.activeSession,
    records: [...baseRegistry.records].reverse(),
  },
});
assert.deepEqual(deterministic, preserveAll);

let projectSequence = 0;
let sessionSequence = 0;
const registry = new DirectorProjectRegistry({
  normalizeDocument: (document) => structuredClone(document),
  createProjectId: () => `batch76-project-${++projectSequence}`,
  createSessionId: (projectId, generation) =>
    `${projectId}-session-${generation}-${++sessionSequence}`,
  now: () => "2026-08-27T12:00:00.000Z",
});
const createDocument = (projectId, owner) => ({ projectId, owner });
for (const owner of [ownerA, ownerB, ownerC, ownerA]) {
  const result = registry.open({ owner, createDocument });
  assert.notEqual(result.disposition, "REJECTED");
}
const activeBeforeDelete = registry.getActiveSession();
assert.ok(activeBeforeDelete);

const runtimePlan = planDirectorOwnerReachability({
  liveOwners: [ownerA],
  registry: registry.getSnapshot(),
});
assert.deepEqual(runtimePlan.tombstoneOwnerKeys, [
  createDirectorProjectOwnerKey(ownerB),
  createDirectorProjectOwnerKey(ownerC),
]);
for (const owner of runtimePlan.tombstoneOwners) {
  assert.equal(registry.tombstone(owner).disposition, "CLOSED");
}
const generationB = registry.getRecord(ownerB).identity.generation;
const generationC = registry.getRecord(ownerC).identity.generation;
const repeatedPlan = planDirectorOwnerReachability({
  liveOwners: [ownerA],
  registry: registry.getSnapshot(),
});
assert.deepEqual(repeatedPlan.tombstoneOwners, []);
assert.equal(registry.getRecord(ownerB).identity.generation, generationB);
assert.equal(registry.getRecord(ownerC).identity.generation, generationC);
assert.equal(
  registry.open({ owner: ownerB, createDocument }).reason,
  "PROJECT_TOMBSTONED",
);

const asyncAuthority = new DirectorAsyncAuthority();
const asyncOwner = {
  owner: ownerA,
  projectId: activeBeforeDelete.projectId,
  sessionId: activeBeforeDelete.sessionId,
  generation: activeBeforeDelete.generation,
};
const descriptor = {
  operationId: "batch76-operation-a",
  kind: "capture",
  owner: asyncOwner,
  attemptId: "batch76-attempt-a",
  sourceFingerprint: "source-fingerprint-a",
  requestFingerprint: "request-fingerprint-a",
  acceptedAt: "2026-08-27T12:01:00.000Z",
  selectionPolicy: "select-result",
};
assert.equal(asyncAuthority.begin(descriptor).disposition, "accepted");

const activeDeletePlan = planDirectorOwnerReachability({
  liveOwners: [],
  registry: registry.getSnapshot(),
});
assert.equal(activeDeletePlan.activeOwnerInvalidated, true);
for (const owner of activeDeletePlan.tombstoneOwners) {
  assert.equal(registry.tombstone(owner).disposition, "CLOSED");
}
assert.equal(registry.getActiveSession(), null);
const tombstonedA = registry.getRecord(ownerA);
assert.equal(tombstonedA.lifecycle, "TOMBSTONED");
assert.equal(
  registry.open({ owner: ownerA, createDocument }).reason,
  "PROJECT_TOMBSTONED",
);
const staleEnvelope = {
  operationId: descriptor.operationId,
  kind: descriptor.kind,
  owner: descriptor.owner,
  attemptId: descriptor.attemptId,
  sourceFingerprint: descriptor.sourceFingerprint,
  resultId: "batch76-result-a",
  resultVersionId: "batch76-result-version-a",
  phase: "succeeded",
  payload: { captureId: "capture-a" },
};
const staleIngress = asyncAuthority.reconcile(staleEnvelope, {
  owner: {
    owner: ownerA,
    projectId: activeBeforeDelete.projectId,
    sessionId: "batch76-deleted-session",
    generation: tombstonedA.identity.generation,
  },
  sourceFingerprint: descriptor.sourceFingerprint,
});
assert.equal(staleIngress.disposition, "reject-stale");
assert.equal(staleIngress.reason, "DIRECTOR_ASYNC_OWNER_STALE");

const finalPlan = planDirectorOwnerReachability({
  liveOwners: [],
  registry: registry.getSnapshot(),
});
assert.deepEqual(finalPlan.tombstoneOwners, []);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      scenarios: {
        allCanvasCollection: "pass",
        inactiveSourceDelete: "pass",
        inactiveCanvasDelete: "pass",
        activeSourceDelete: "pass",
        invalidDuplicateNormalization: "pass",
        deterministicOrdering: "pass",
        registryIdempotency: "pass",
        tombstonedReopenRejected: "pass",
        delayedAsyncOwnerStale: "pass",
      },
      ownersObserved: 4,
      tombstonedProjects: registry
        .getSnapshot()
        .records.filter((record) => record.lifecycle === "TOMBSTONED").length,
      screenshots: 0,
    },
    null,
    2,
  ),
);
