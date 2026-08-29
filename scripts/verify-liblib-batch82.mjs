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

let resources = createDirectorLocalResourceMap([validItem]);
assert.equal(resources[validItem.id]?.status, "idle");
resources = addDirectorLocalResource(resources, descriptor);

const first = beginDirectorLocalResourceLoad(resources, validItem.id, "request-1");
assert.equal(first.accepted, true);
assert.equal(first.state?.status, "loading");
resources = { ...resources, [validItem.id]: first.state };

const duplicate = beginDirectorLocalResourceLoad(
  resources,
  validItem.id,
  "request-duplicate",
);
assert.equal(duplicate.accepted, false);

const stale = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-duplicate",
  status: "ready",
});
assert.equal(stale.accepted, false);
assert.equal(stale.state?.status, "loading");

const ready = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-1",
  status: "ready",
});
assert.equal(ready.accepted, true);
assert.equal(ready.state?.status, "ready");
resources = { ...resources, [validItem.id]: ready.state };

resources = retryDirectorLocalResource(resources, validItem.id);
assert.equal(resources[validItem.id]?.status, "idle");
assert.equal(resources[validItem.id]?.retryNonce, 1);

const second = beginDirectorLocalResourceLoad(resources, validItem.id, "request-2");
assert.equal(second.accepted, true);
resources = { ...resources, [validItem.id]: second.state };
const failed = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-2",
  status: "failed",
  error: "PARSE_FAILED",
  errorMessage: "fixture parse failure",
});
assert.equal(failed.accepted, true);
assert.equal(failed.state?.error, "PARSE_FAILED");
resources = { ...resources, [validItem.id]: failed.state };

resources = retryDirectorLocalResource(resources, validItem.id);
const third = beginDirectorLocalResourceLoad(resources, validItem.id, "request-3");
assert.equal(third.accepted, true);
resources = { ...resources, [validItem.id]: third.state };
const canceled = settleDirectorLocalResource(resources, {
  resourceId: validItem.id,
  requestId: "request-3",
  status: "canceled",
  error: "ABORTED",
});
assert.equal(canceled.accepted, true);
assert.equal(canceled.state?.status, "canceled");
resources = { ...resources, [validItem.id]: canceled.state };

resources = retainDirectorLocalResource(resources, validItem.id);
assert.equal(resources[validItem.id]?.leaseCount, 1);
resources = markDirectorLocalResourceReleased(resources, validItem.id);
assert.equal(resources[validItem.id]?.status, "canceled");
resources = releaseDirectorLocalResourceLease(resources, validItem.id);
resources = markDirectorLocalResourceReleased(resources, validItem.id);
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
