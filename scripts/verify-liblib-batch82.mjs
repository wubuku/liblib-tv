import assert from "node:assert/strict";
import {
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

const dataUrl = "data:text/plain;base64,dGVzdA==";
const validItem = {
  id: "batch82-resource",
  fileName: "batch82.obj",
  dataUrl,
  mimeType: "text/plain",
  sizeBytes: 4,
  lastModified: 1,
  categoryId: "my-models",
  name: "Batch 82",
  visual: "box",
  color: "#8899aa",
};

const descriptor = createDirectorLocalResourceDescriptor(validItem);
assert.ok(descriptor);
assert.equal(descriptor.extension, "obj");
assert.equal(descriptor.locatorClass, "SESSION_DATA_URL");
assert.equal(descriptor.provenance, "LOCAL_FILE");
assert.equal(
  createDirectorLocalResourceDescriptor({
    ...validItem,
    fileName: "batch82.gltf",
  }),
  null,
);

const owner = {
  ownerKey: "libtv:batch82-canvas:batch82-source",
  projectId: "batch82-project",
  sessionId: "batch82-session",
  generation: 1,
};

let resources = createDirectorLocalResourceMap([validItem]);
assert.equal(resources[validItem.id]?.status, "idle");
resources = addDirectorLocalResource(resources, descriptor);

const first = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-1",
  owner,
);
assert.equal(first.accepted, true);
assert.equal(first.state?.status, "loading");
resources = { ...resources, [validItem.id]: first.state };
resources = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "request-1",
  owner,
});

const duplicate = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-duplicate",
  owner,
);
assert.equal(duplicate.accepted, false);

const stale = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-duplicate",
  owner,
  status: "ready",
});
assert.equal(stale.accepted, false);
assert.equal(stale.state?.status, "loading");

const ready = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-1",
  owner,
  status: "ready",
});
assert.equal(ready.accepted, true);
assert.equal(ready.state?.status, "ready");
resources = { ...resources, [validItem.id]: ready.state };
resources = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "request-1",
  owner,
);

resources = retryDirectorLocalResource(resources, validItem.id);
assert.equal(resources[validItem.id]?.status, "idle");
assert.equal(resources[validItem.id]?.retryNonce, 1);

const second = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-2",
  owner,
);
assert.equal(second.accepted, true);
resources = { ...resources, [validItem.id]: second.state };
resources = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "request-2",
  owner,
});
const failed = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-2",
  owner,
  status: "failed",
  error: "PARSE_FAILED",
  errorMessage: "fixture parse failure",
});
assert.equal(failed.accepted, true);
assert.equal(failed.state?.error, "PARSE_FAILED");
resources = { ...resources, [validItem.id]: failed.state };
resources = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "request-2",
  owner,
);

resources = retryDirectorLocalResource(resources, validItem.id);
const third = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-3",
  owner,
);
assert.equal(third.accepted, true);
resources = { ...resources, [validItem.id]: third.state };
resources = retainDirectorLocalResource(resources, validItem.id, {
  leaseId: "request-3",
  owner,
});
const canceled = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-3",
  owner,
  status: "canceled",
  error: "ABORTED",
});
assert.equal(canceled.accepted, true);
assert.equal(canceled.state?.status, "canceled");
resources = { ...resources, [validItem.id]: canceled.state };
assert.equal(resources[validItem.id]?.leaseCount, 1);
resources = markDirectorLocalResourceReleased(resources, validItem.id);
assert.equal(resources[validItem.id]?.releaseRequested, true);
assert.equal(resources[validItem.id]?.status, "canceled");
resources = releaseDirectorLocalResourceLease(
  resources,
  validItem.id,
  "request-3",
  owner,
);
assert.equal(resources[validItem.id]?.status, "released");

console.log(
  JSON.stringify({
    batch: 82,
    status: "PASS",
    cases: {
      descriptor: true,
      unsupportedExtension: true,
      loadingDuplicateGuard: true,
      staleAttemptIgnored: true,
      ready: true,
      parseFailure: true,
      retry: true,
      cancel: true,
      leaseRelease: true,
    },
  }),
);
