import assert from "node:assert/strict";
import fs from "node:fs";
import {
  DIRECTOR_LOCAL_RESOURCE_MAX_BYTES,
  addDirectorLocalResource,
  beginDirectorLocalResourceLoad,
  createDirectorLocalResourceDescriptor,
  createDirectorLocalResourceMap,
  markDirectorLocalResourceReleased,
  releaseDirectorLocalResourceLease,
  retainDirectorLocalResource,
  retryDirectorLocalResource,
  settleDirectorLocalResource,
} from "../src/lib/directorLocalResourceLifecycle.ts";

const root = new URL("..", import.meta.url);
const lifecycleSource = fs.readFileSync(
  new URL("./src/lib/directorLocalResourceLifecycle.ts", root),
  "utf8",
);
const materializerSource = fs.readFileSync(
  new URL("./src/lib/directorLocalModelMaterializer.ts", root),
  "utf8",
);

const dataUrl = "data:text/plain;base64,dGVzdA==";
const validItem = {
  id: "batch92-resource",
  fileName: "batch92.obj",
  dataUrl,
  mimeType: "text/plain",
  sizeBytes: 4,
  lastModified: 1,
  categoryId: "my-models",
  name: "Batch 92",
  visual: "box",
  color: "#8899aa",
};
const ownerA = {
  ownerKey: "libtv:batch92-canvas:batch92-source",
  projectId: "batch92-project",
  sessionId: "batch92-session-a",
  generation: 1,
};
const ownerB = {
  ...ownerA,
  sessionId: "batch92-session-b",
  generation: 2,
};

const descriptor = createDirectorLocalResourceDescriptor(validItem);
assert.ok(descriptor);
assert.equal(descriptor.sizeBytes, 4);
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    sizeBytes: 5,
  }),
  null,
);
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    dataUrl: "data:text/plain;base64,%%%%",
  }),
  null,
);
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    sizeBytes: DIRECTOR_LOCAL_RESOURCE_MAX_BYTES + 1,
  }),
  null,
);
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    mimeType: "",
  }),
  null,
);
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    lastModified: Number.NaN,
  }),
  null,
);

let resources = createDirectorLocalResourceMap([validItem]);
const first = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-a",
  ownerA,
);
assert.equal(first.accepted, true);
resources = { ...resources, [validItem.id]: first.state };
resources = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "lease-a",
  owner: ownerA,
});
assert.equal(resources[validItem.id]?.leaseCount, 1);
assert.equal(resources[validItem.id]?.activeRequestOwner?.sessionId, ownerA.sessionId);

const wrongOwnerSettle = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-a",
  owner: ownerB,
  status: "ready",
});
assert.equal(wrongOwnerSettle.accepted, false);
assert.equal(wrongOwnerSettle.state?.status, "loading");

const wrongOwnerCancel = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-a",
  owner: ownerB,
  status: "canceled",
  error: "ABORTED",
  errorMessage: "wrong owner",
});
assert.equal(wrongOwnerCancel.accepted, false);

const wrongOwnerRelease = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "lease-a",
  ownerB,
);
assert.equal(wrongOwnerRelease[validItem.id]?.leaseCount, 1);

const ready = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-a",
  owner: ownerA,
  status: "ready",
});
assert.equal(ready.accepted, true);
assert.equal(ready.state?.error, null);
resources = { ...resources, [validItem.id]: ready.state };

const duplicateLease = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "lease-a",
  owner: ownerA,
});
assert.equal(duplicateLease[validItem.id]?.leaseCount, 1);

resources = markDirectorLocalResourceReleased(resources, validItem.id);
assert.equal(resources[validItem.id]?.status, "ready");
assert.equal(resources[validItem.id]?.releaseRequested, true);
const blockedRetry = retryDirectorLocalResource(resources, validItem.id);
assert.equal(blockedRetry[validItem.id]?.retryNonce, 0);
resources = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "lease-a",
  ownerA,
);
assert.equal(resources[validItem.id]?.status, "released");
assert.equal(resources[validItem.id]?.leaseCount, 0);
assert.equal(resources[validItem.id]?.releaseRequested, true);

resources = addDirectorLocalResource(resources, descriptor);
assert.equal(resources[validItem.id]?.status, "idle");
assert.equal(resources[validItem.id]?.releaseRequested, false);
assert.equal(resources[validItem.id]?.leaseCount, 0);

const second = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-b",
  ownerA,
);
assert.equal(second.accepted, true);
resources = { ...resources, [validItem.id]: second.state };
const invalidReady = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-b",
  owner: ownerA,
  status: "ready",
  error: "PARSE_FAILED",
});
assert.equal(invalidReady.accepted, false);
assert.equal(invalidReady.state?.status, "loading");
const failed = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-b",
  owner: ownerA,
  status: "failed",
  error: "PARSE_FAILED",
  errorMessage: "fixture parse failure",
});
assert.equal(failed.accepted, true);
resources = { ...resources, [validItem.id]: failed.state };
resources = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "lease-b",
  owner: ownerA,
});
resources = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "lease-b",
  ownerA,
);
resources = retryDirectorLocalResource(resources, validItem.id);
assert.equal(resources[validItem.id]?.status, "idle");

assert.match(lifecycleSource, /releaseRequested: boolean/);
assert.match(lifecycleSource, /sameLeaseOwner/);
assert.match(lifecycleSource, /DIRECTOR_LOCAL_RESOURCE_MAX_BYTES/);
assert.match(materializerSource, /bytes\.byteLength > DIRECTOR_LOCAL_RESOURCE_MAX_BYTES/);

console.log(
  JSON.stringify({
    batch: 92,
    status: "PASS",
    cases: {
      strictDescriptorAndByteBudget: true,
      ownerScopedRequestAndLease: true,
      wrongOwnerZeroMutation: true,
      terminalInvariant: true,
      deferredRelease: true,
      finalLeaseRelease: true,
      releasedResourceReactivation: true,
      retryAfterFailure: true,
      materializerBudgetGuard: true,
    },
  }),
);
