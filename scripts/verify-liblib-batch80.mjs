import assert from "node:assert/strict";
import { createDirectorProjectDocumentV1 } from "../src/lib/directorProjectDocument.ts";
import {
  createDirectorProjectStorageKey,
  DirectorProjectPersistenceAuthority,
} from "../src/lib/directorProjectPersistence.ts";

class MemoryBackend {
  values = new Map();
  failWrites = false;

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    if (this.failWrites) throw new Error("quota");
    this.values.set(key, value);
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

const owner = {
  route: "libtv",
  canvasId: "batch80-canvas-a",
  sourceNodeId: "batch80-director-a",
};

const transform = (position = [0, 0, 0]) => ({
  position,
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});

function createDocument(name = "Batch 80 scene") {
  const camera = {
    id: "batch80-camera",
    name: "Main camera",
    kind: "camera",
    primitive: "camera",
    color: "#99ddff",
    visible: true,
    locked: false,
    transform: transform([4, 2, 6]),
    camera: {
      fov: 45,
      target: [0, 1, 0],
      lookAtMode: "coordinate",
      lookAtObjectId: null,
      followTargetId: null,
      followOffset: [0, 1.2, 4.5],
      followView: "third-person",
    },
  };
  return createDirectorProjectDocumentV1({
    projectId: "batch80-project-a",
    owner,
    scene: {
      name,
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [camera],
    groups: [],
    activeCameraId: camera.id,
    aspectRatio: "16:9",
    timeline: {
      duration: 8,
      currentTime: 4,
      isPlaying: true,
      loop: true,
      zoom: 1,
      autoKeyframe: true,
      tracks: [],
      motionPaths: [],
      selectedTrackId: null,
      selectedKeyframeId: null,
      selectedMotionPathId: null,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      editorMode: "timeline",
      cameraMotionPreset: { application: null, error: null },
    },
    captures: [
      {
        id: "batch80-capture",
        dataUrl: "data:image/png;base64,TRANSIENT_BYTES",
        cameraId: camera.id,
        cameraName: camera.name,
        aspectRatio: "16:9",
        width: 1280,
        height: 720,
        createdAt: "2026-08-28T12:00:00.000Z",
        sentNodeId: null,
      },
    ],
  });
}

function rawValue(backend, key) {
  const raw = backend.getItem(key);
  assert.ok(raw);
  return JSON.parse(raw);
}

const backend = new MemoryBackend();
const authority = new DirectorProjectPersistenceAuthority(backend);
const document = createDocument();
const key = createDirectorProjectStorageKey(owner);
const saved = authority.save({
  owner,
  projectId: document.projectId,
  generation: 3,
  document,
  savedAt: "2026-08-28T12:01:00.000Z",
});
assert.equal(saved.disposition, "SAVED");
assert.equal(saved.envelope?.document.captureDescriptors.length, 0);

const tombstoned = authority.tombstone({
  owner,
  projectId: document.projectId,
  generation: 3,
  tombstonedAt: "2026-08-28T12:02:00.000Z",
});
assert.equal(tombstoned.disposition, "TOMBSTONED");
assert.deepEqual(rawValue(backend, key), {
  storageSchemaVersion: 1,
  lifecycle: "TOMBSTONED",
  projectId: document.projectId,
  owner,
  generation: 3,
  tombstonedAt: "2026-08-28T12:02:00.000Z",
});
assert.equal(authority.load(owner).reason, "PROJECT_TOMBSTONED");

const repeated = authority.tombstone({
  owner,
  projectId: document.projectId,
  generation: 3,
});
assert.equal(repeated.disposition, "ALREADY_TOMBSTONED");
assert.equal(repeated.envelope?.tombstonedAt, "2026-08-28T12:02:00.000Z");

const saveAfterTombstone = authority.save({
  owner,
  projectId: document.projectId,
  generation: 4,
  document: createDocument("must not resurrect"),
});
assert.equal(saveAfterTombstone.disposition, "STALE_IGNORED");
assert.equal(saveAfterTombstone.reason, "PROJECT_TOMBSTONED");
assert.equal(rawValue(backend, key).lifecycle, "TOMBSTONED");

const malformed = {
  ...rawValue(backend, key),
  unexpected: true,
};
backend.setItem(key, JSON.stringify(malformed));
const malformedResult = authority.load(owner);
assert.equal(malformedResult.disposition, "REJECTED");
assert.equal(malformedResult.reason, "INVALID_ENVELOPE");

const staleBackend = new MemoryBackend();
const staleAuthority = new DirectorProjectPersistenceAuthority(staleBackend);
staleAuthority.save({
  owner,
  projectId: document.projectId,
  generation: 9,
  document,
});
const staleTombstone = staleAuthority.tombstone({
  owner,
  projectId: document.projectId,
  generation: 8,
});
assert.equal(staleTombstone.disposition, "REJECTED");
assert.equal(staleTombstone.reason, "STALE_REQUEST");
assert.equal(staleAuthority.load(owner).disposition, "RESTORED");

const failedBackend = new MemoryBackend();
const failedAuthority = new DirectorProjectPersistenceAuthority(failedBackend);
failedAuthority.save({
  owner,
  projectId: document.projectId,
  generation: 1,
  document,
});
failedBackend.failWrites = true;
const failedTombstone = failedAuthority.tombstone({
  owner,
  projectId: document.projectId,
  generation: 1,
});
assert.equal(failedTombstone.disposition, "REJECTED");
assert.equal(failedTombstone.reason, "WRITE_FAILED");
assert.equal(failedAuthority.getRecord(owner).status, "SESSION_ONLY");
assert.equal(failedAuthority.load(owner).disposition, "RESTORED");

const unavailable = new DirectorProjectPersistenceAuthority(null);
assert.equal(
  unavailable.tombstone({
    owner,
    projectId: document.projectId,
    generation: 1,
  }).reason,
  "STORAGE_UNAVAILABLE",
);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      batch: 80,
      scenarios: [
        "strict tombstone envelope round-trip",
        "durable tombstone blocks load",
        "tombstone is idempotent",
        "save cannot resurrect tombstoned project",
        "malformed tombstone is rejected",
        "stale tombstone cannot replace newer document",
        "write failure preserves session-only continuity",
        "storage unavailable",
      ],
      errors: [],
    },
    null,
    2,
  ),
);
