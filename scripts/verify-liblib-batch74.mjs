import assert from "node:assert/strict";
import { createDirectorProjectDocumentV1 } from "../src/lib/directorProjectDocument.ts";
import {
  createDirectorProjectStorageKey,
  DirectorProjectPersistenceAuthority,
} from "../src/lib/directorProjectPersistence.ts";

class MemoryBackend {
  values = new Map();
  shouldFailWrites = false;

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    if (this.shouldFailWrites) throw new Error("quota");
    this.values.set(key, value);
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

const owner = {
  route: "libtv",
  canvasId: "batch74-canvas-a",
  sourceNodeId: "batch74-director-a",
};

const transform = (position = [0, 0, 0]) => ({
  position,
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});

function createDocument(sceneName = "Batch 74 scene") {
  const character = {
    id: "batch74-character",
    name: "Lead",
    kind: "character",
    primitive: "character",
    color: "#8899aa",
    visible: true,
    locked: false,
    transform: transform([-1, 0, 0]),
    characterRig: {
      posePresetId: "stand",
      controls: {},
    },
  };
  const camera = {
    id: "batch74-camera",
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
      lookAtMode: "object",
      lookAtObjectId: character.id,
      followTargetId: null,
      followOffset: [0, 1.2, 4.5],
      followView: "third-person",
    },
  };
  return createDirectorProjectDocumentV1({
    projectId: "batch74-project-a",
    owner,
    scene: {
      name: sceneName,
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [character, camera],
    groups: [],
    activeCameraId: camera.id,
    aspectRatio: "16:9",
    captures: [
      {
        id: "batch74-capture",
        dataUrl: "data:image/png;base64,NOT_PORTABLE",
        cameraId: camera.id,
        cameraName: camera.name,
        aspectRatio: "16:9",
        width: 1280,
        height: 720,
        createdAt: "2026-08-27T12:00:00.000Z",
        sentNodeId: null,
      },
    ],
    timeline: {
      duration: 8,
      currentTime: 6,
      isPlaying: true,
      loop: true,
      zoom: 1.5,
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
      cameraMotionPreset: {
        application: null,
        error: null,
      },
    },
  });
}

function rawEnvelope(backend, key) {
  const raw = backend.getItem(key);
  assert.ok(raw);
  return JSON.parse(raw);
}

const backend = new MemoryBackend();
const authority = new DirectorProjectPersistenceAuthority(backend);
const key = createDirectorProjectStorageKey(owner);
const document = createDocument();

const missing = authority.load(owner);
assert.deepEqual(missing, {
  disposition: "MISSING",
  reason: null,
  key,
  document: null,
  projectId: null,
  generation: null,
  fingerprint: null,
});

const saved = authority.save({
  owner,
  projectId: document.projectId,
  generation: 3,
  document,
  savedAt: "2026-08-27T12:01:00.000Z",
});
assert.equal(saved.disposition, "SAVED");
assert.equal(saved.envelope?.document.captureDescriptors.length, 0);
assert.equal(
  JSON.stringify(saved.envelope).includes("NOT_PORTABLE"),
  false,
);

const restored = authority.load(owner);
assert.equal(restored.disposition, "RESTORED");
assert.deepEqual(restored.document, saved.envelope?.document);
assert.equal(restored.generation, 3);

const firstRequest = authority.beginSave({
  owner,
  projectId: document.projectId,
  generation: 3,
  document: createDocument("older"),
});
const secondRequest = authority.beginSave({
  owner,
  projectId: document.projectId,
  generation: 3,
  document: createDocument("newer"),
});
assert.equal(authority.completeSave(secondRequest).disposition, "SAVED");
assert.equal(
  authority.completeSave(firstRequest).disposition,
  "STALE_IGNORED",
);
assert.equal(authority.load(owner).document?.scene.name, "newer");

const corruptBefore = backend.getItem(key);
backend.setItem(key, "{not-json");
const corrupt = authority.load(owner);
assert.equal(corrupt.disposition, "REJECTED");
assert.equal(corrupt.reason, "CORRUPT_PAYLOAD");
assert.equal(backend.getItem(key), "{not-json");
backend.setItem(key, corruptBefore);

const future = rawEnvelope(backend, key);
future.storageSchemaVersion = 2;
backend.setItem(key, JSON.stringify(future));
const futureResult = authority.load(owner);
assert.equal(futureResult.disposition, "REJECTED");
assert.equal(futureResult.reason, "FUTURE_STORAGE_SCHEMA");
backend.setItem(key, corruptBefore);

const ownerMismatch = rawEnvelope(backend, key);
ownerMismatch.owner = { ...owner, sourceNodeId: "other-source" };
backend.setItem(key, JSON.stringify(ownerMismatch));
const ownerResult = authority.load(owner);
assert.equal(ownerResult.disposition, "REJECTED");
assert.equal(ownerResult.reason, "OWNER_MISMATCH");
backend.setItem(key, corruptBefore);

const projectMismatch = rawEnvelope(backend, key);
projectMismatch.projectId = "other-project";
backend.setItem(key, JSON.stringify(projectMismatch));
const projectResult = authority.load(owner);
assert.equal(projectResult.disposition, "REJECTED");
assert.equal(projectResult.reason, "PROJECT_MISMATCH");
backend.setItem(key, corruptBefore);

backend.shouldFailWrites = true;
const failedWrite = authority.save({
  owner,
  projectId: document.projectId,
  generation: 4,
  document: createDocument("write failure"),
});
assert.equal(failedWrite.disposition, "REJECTED");
assert.equal(failedWrite.reason, "WRITE_FAILED");
assert.equal(authority.getRecord(owner).status, "SESSION_ONLY");
backend.shouldFailWrites = false;

const unavailable = new DirectorProjectPersistenceAuthority(null);
assert.equal(unavailable.load(owner).reason, "STORAGE_UNAVAILABLE");
assert.equal(
  unavailable.save({
    owner,
    projectId: document.projectId,
    generation: 1,
    document,
  }).reason,
  "STORAGE_UNAVAILABLE",
);

const snapshot = authority.getSnapshot();
assert.equal(snapshot.storageSchemaVersion, 1);
assert.equal(snapshot.available, true);
assert.equal(snapshot.records.length, 1);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      batch: 74,
      scenarios: [
        "missing storage",
        "strict envelope round-trip",
        "capture byte exclusion",
        "stale save completion",
        "corrupt payload zero replacement",
        "future schema rejection",
        "owner mismatch rejection",
        "project mismatch rejection",
        "write failure preserves session-only status",
        "storage unavailable",
      ],
      snapshot: {
        status: snapshot.records[0].status,
        generation: snapshot.records[0].generation,
        savedFingerprint: snapshot.records[0].fingerprint,
      },
      errors: [],
    },
    null,
    2,
  ),
);
