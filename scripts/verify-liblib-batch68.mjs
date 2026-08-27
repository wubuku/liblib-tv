import assert from "node:assert/strict";
import {
  createDirectorProjectDocumentV1,
  normalizeDirectorProjectDocument,
} from "../src/lib/directorProjectDocument.ts";
import {
  DirectorProjectRegistry,
  createDirectorProjectOwnerKey,
} from "../src/lib/directorProjectRegistry.ts";

const transform = (position = [0, 0, 0]) => ({
  position,
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});

function createDocument(projectId, owner, sceneName) {
  const character = {
    id: "character-main",
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
    id: "camera-main",
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
    projectId,
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
    captures: [],
    timeline: {
      duration: 8,
      currentTime: 0,
      isPlaying: false,
      loop: true,
      zoom: 1,
      autoKeyframe: true,
      tracks: [
        {
          id: "track-character",
          kind: "transform",
          objectId: character.id,
          label: "Lead transform",
          speedCurve: {
            preset: "smooth",
            control1: [0.33, 0],
            control2: [0.67, 1],
          },
          keyframes: [
            {
              id: "keyframe-character-0",
              time: 0,
              value: transform([-1, 0, 0]),
            },
            {
              id: "keyframe-character-8",
              time: 8,
              value: transform([1, 0, 0]),
            },
          ],
        },
        {
          id: "track-camera",
          kind: "camera",
          objectId: camera.id,
          label: "Main camera",
          speedCurve: {
            preset: "smooth",
            control1: [0.33, 0],
            control2: [0.67, 1],
          },
          keyframes: [
            {
              id: "keyframe-camera-0",
              time: 0,
              value: {
                transform: transform([4, 2, 6]),
                target: [0, 1, 0],
                fov: 45,
              },
            },
            {
              id: "keyframe-camera-8",
              time: 8,
              value: {
                transform: transform([3, 2, 4]),
                target: [0.2, 1, 0],
                fov: 50,
              },
            },
          ],
        },
      ],
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

let projectSequence = 0;
let sessionSequence = 0;
let clockSequence = 0;
const registry = new DirectorProjectRegistry({
  normalizeDocument: normalizeDirectorProjectDocument,
  createProjectId: () => `project-${++projectSequence}`,
  createSessionId: (projectId, generation) =>
    `${projectId}-session-${generation}-${++sessionSequence}`,
  now: () =>
    `2026-08-27T10:00:${String(clockSequence++).padStart(2, "0")}.000Z`,
});

const ownerA = {
  route: "libtv",
  canvasId: "canvas-a",
  sourceNodeId: "director-node-a",
};
const ownerB = {
  route: "libtv",
  canvasId: "canvas-a",
  sourceNodeId: "director-node-b",
};
const ownerC = {
  route: "libtv",
  canvasId: "canvas-b",
  sourceNodeId: "director-node-a",
};

assert.notEqual(
  createDirectorProjectOwnerKey({
    route: "libtv",
    canvasId: "canvas|a",
    sourceNodeId: "node",
  }),
  createDirectorProjectOwnerKey({
    route: "libtv",
    canvasId: "canvas",
    sourceNodeId: "a|node",
  }),
);

const openA1 = registry.open({
  owner: ownerA,
  createDocument: (projectId, owner) =>
    createDocument(projectId, owner, "A default"),
});
assert.equal(openA1.disposition, "CREATED");
assert.equal(openA1.record?.identity.generation, 1);
assert.equal(openA1.session?.generation, 1);

const beforeFocus = JSON.stringify(registry.getSnapshot());
const focusA = registry.open({
  owner: ownerA,
  createDocument: () => {
    throw new Error("same-owner focus must not create a document");
  },
});
assert.equal(focusA.disposition, "FOCUSED");
assert.equal(JSON.stringify(registry.getSnapshot()), beforeFocus);

const documentA = structuredClone(openA1.record.document);
documentA.scene.name = "A edited";
const updateA = registry.updateActive({
  owner: ownerA,
  projectId: openA1.session.projectId,
  generation: openA1.session.generation,
  document: documentA,
  captures: [
    {
      id: "capture-a",
      dataUrl: "data:image/png;base64,QQ==",
      cameraId: "camera-main",
      cameraName: "Main camera",
      aspectRatio: "16:9",
      width: 1280,
      height: 720,
      createdAt: "2026-08-27T10:01:00.000Z",
      sentNodeId: "graph-result-a",
    },
  ],
});
assert.equal(updateA.disposition, "COMMITTED");

const openB = registry.open({
  owner: ownerB,
  createDocument: (projectId, owner) =>
    createDocument(projectId, owner, "B default"),
});
assert.equal(openB.disposition, "CREATED");
assert.notEqual(openB.session.projectId, openA1.session.projectId);
assert.equal(openB.record.document.scene.name, "B default");
assert.equal(openB.record.memory.captures.length, 0);

const documentB = structuredClone(openB.record.document);
documentB.scene.name = "B edited";
assert.equal(
  registry.updateActive({
    owner: ownerB,
    projectId: openB.session.projectId,
    generation: openB.session.generation,
    document: documentB,
    captures: [],
  }).disposition,
  "COMMITTED",
);

const openA2 = registry.open({
  owner: ownerA,
  createDocument: () => {
    throw new Error("existing project must restore");
  },
});
assert.equal(openA2.disposition, "RESTORED");
assert.equal(openA2.session.projectId, openA1.session.projectId);
assert.equal(openA2.session.generation, 2);
assert.notEqual(openA2.session.sessionId, openA1.session.sessionId);
assert.equal(openA2.record.document.scene.name, "A edited");
assert.equal(openA2.record.memory.captures[0].dataUrl, "data:image/png;base64,QQ==");
assert.equal(openA2.record.memory.captures[0].sentNodeId, "graph-result-a");

const detachedA = registry.getRecord(ownerA);
detachedA.document.scene.name = "external mutation";
detachedA.memory.captures[0].dataUrl = "mutated";
assert.equal(registry.getRecord(ownerA).document.scene.name, "A edited");
assert.equal(
  registry.getRecord(ownerA).memory.captures[0].dataUrl,
  "data:image/png;base64,QQ==",
);

const beforeStale = JSON.stringify(registry.getSnapshot());
const staleUpdate = registry.updateActive({
  owner: ownerA,
  projectId: openA1.session.projectId,
  generation: openA1.session.generation,
  document: documentA,
  captures: [],
});
assert.equal(staleUpdate.disposition, "STALE");
assert.equal(staleUpdate.reason, "OWNER_STALE");
assert.equal(JSON.stringify(registry.getSnapshot()), beforeStale);

const invalidOwner = {
  route: "libtv",
  canvasId: " canvas-invalid",
  sourceNodeId: "node-invalid",
};
const beforeInvalid = JSON.stringify(registry.getSnapshot());
const invalidOpen = registry.open({
  owner: invalidOwner,
  createDocument: (projectId, owner) =>
    createDocument(projectId, owner, "invalid"),
});
assert.equal(invalidOpen.disposition, "REJECTED");
assert.equal(invalidOpen.reason, "INVALID_OWNER");
assert.equal(JSON.stringify(registry.getSnapshot()), beforeInvalid);

const openC = registry.open({
  owner: ownerC,
  createDocument: (projectId, owner) =>
    createDocument(projectId, owner, "C default"),
});
assert.equal(openC.disposition, "CREATED");
assert.notEqual(openC.session.projectId, openA1.session.projectId);
assert.notEqual(
  createDirectorProjectOwnerKey(ownerC),
  createDirectorProjectOwnerKey(ownerA),
);

const closeC = registry.close({
  owner: ownerC,
  projectId: openC.session.projectId,
  generation: openC.session.generation,
  document: openC.record.document,
  captures: [],
});
assert.equal(closeC.disposition, "CLOSED");
assert.equal(registry.getActiveSession(), null);

const openC2 = registry.open({
  owner: ownerC,
  createDocument: () => {
    throw new Error("closed project must restore");
  },
});
assert.equal(openC2.disposition, "RESTORED");
assert.equal(openC2.session.projectId, openC.session.projectId);
assert.equal(openC2.session.generation, 2);

assert.equal(registry.tombstone(ownerB).disposition, "CLOSED");
const beforeTombstoneOpen = JSON.stringify(registry.getSnapshot());
const tombstonedOpen = registry.open({
  owner: ownerB,
  createDocument: (projectId, owner) =>
    createDocument(projectId, owner, "must not replace tombstone"),
});
assert.equal(tombstonedOpen.disposition, "REJECTED");
assert.equal(tombstonedOpen.reason, "PROJECT_TOMBSTONED");
assert.equal(JSON.stringify(registry.getSnapshot()), beforeTombstoneOpen);

const snapshot = registry.getSnapshot();
assert.equal(snapshot.records.length, 3);
assert.equal(
  snapshot.records.find(
    (record) =>
      createDirectorProjectOwnerKey(record.identity.owner) ===
      createDirectorProjectOwnerKey(ownerB),
  ).lifecycle,
  "TOMBSTONED",
);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      ownerKeys: 3,
      projects: snapshot.records.length,
      activeProjectId: snapshot.activeSession.projectId,
      activeGeneration: snapshot.activeSession.generation,
      dispositions: {
        create: openA1.disposition,
        focus: focusA.disposition,
        restore: openA2.disposition,
        stale: staleUpdate.disposition,
        tombstone: tombstonedOpen.disposition,
      },
      documentIsolation: true,
      memorySidecarIsolation: true,
      zeroPartialRejection: true,
    },
    null,
    2,
  ),
);
