import assert from "node:assert/strict";
import {
  createDirectorProjectDocumentV1,
  decodeDirectorProjectDocument,
  encodeDirectorProjectDocument,
  rebindDirectorProjectDocumentV1,
} from "../src/lib/directorProjectDocument.ts";

const transform = (position = [0, 0, 0]) => ({
  position,
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});

function createFixture() {
  const character = {
    id: "batch81-character",
    name: "导入角色",
    kind: "character",
    primitive: "character",
    color: "#7890a8",
    visible: true,
    locked: false,
    transform: transform([-1, 0, 0]),
    characterRig: { posePresetId: "stand", controls: { "head.yaw": 12 } },
  };
  const camera = {
    id: "batch81-camera",
    name: "导入机位",
    kind: "camera",
    primitive: "camera",
    color: "#99ddff",
    visible: true,
    locked: false,
    transform: transform([3, 2, 5]),
    camera: {
      fov: 45,
      target: [0, 1, 0],
      lookAtMode: "object",
      lookAtObjectId: character.id,
      followTargetId: null,
      followOffset: [0, 1, 4],
      followView: "third-person",
    },
  };
  return createDirectorProjectDocumentV1({
    projectId: "batch81-source-project",
    owner: {
      route: "libtv",
      canvasId: "batch81-source-canvas",
      sourceNodeId: "batch81-source-node",
    },
    scene: {
      name: "Batch 81 imported scene",
      backgroundColor: "#182028",
      groundColor: "#29343d",
      showGround: true,
      showGrid: false,
    },
    objects: [character, camera],
    groups: [],
    activeCameraId: camera.id,
    aspectRatio: "9:16",
    timeline: {
      duration: 8,
      currentTime: 4,
      isPlaying: true,
      loop: true,
      zoom: 2,
      autoKeyframe: true,
      tracks: [
        {
          id: "batch81-track",
          kind: "transform",
          objectId: character.id,
          label: "导入轨道",
          motionPathId: undefined,
          speedCurve: {
            preset: "linear",
            control1: [0, 0],
            control2: [1, 1],
          },
          keyframes: [
            { id: "batch81-key-0", time: 0, value: transform([-1, 0, 0]) },
            { id: "batch81-key-8", time: 8, value: transform([1, 0, 0]) },
          ],
        },
      ],
      motionPaths: [],
    },
    captures: [
      {
        id: "batch81-capture",
        dataUrl: "data:image/png;base64,SHOULD_NOT_BE_EXPORTED",
        cameraId: camera.id,
        cameraName: camera.name,
        aspectRatio: "9:16",
        width: 720,
        height: 1280,
        createdAt: "2026-08-29T00:00:00.000Z",
      },
    ],
  });
}

const source = createFixture();
const encoded = encodeDirectorProjectDocument(source);
assert.equal(encoded.includes("SHOULD_NOT_BE_EXPORTED"), false);
assert.equal(encoded.includes("data:"), false);
assert.equal(encoded.includes("blob:"), false);

const decoded = decodeDirectorProjectDocument(JSON.parse(encoded));
assert.equal(decoded.ok, true);
if (!decoded.ok) throw new Error(decoded.error.message);

const rebound = rebindDirectorProjectDocumentV1(decoded.document, {
  projectId: "batch81-target-project",
  owner: {
    route: "libtv",
    canvasId: "batch81-target-canvas",
    sourceNodeId: "batch81-target-node",
  },
});
assert.equal(rebound.projectId, "batch81-target-project");
assert.deepEqual(rebound.owner, {
  route: "libtv",
  canvasId: "batch81-target-canvas",
  sourceNodeId: "batch81-target-node",
});
assert.deepEqual(rebound.objects.map((object) => object.id), [
  "batch81-character",
  "batch81-camera",
]);
assert.equal(rebound.objects[1].camera?.lookAtObjectId, "batch81-character");
assert.equal(rebound.timeline.tracks[0].objectId, "batch81-character");
assert.equal(rebound.captureDescriptors.length, 1);

const unknown = JSON.parse(encoded);
unknown.unmodeled = true;
const unknownResult = decodeDirectorProjectDocument(unknown);
assert.equal(unknownResult.ok, false);
if (unknownResult.ok) throw new Error("unknown field accepted");
assert.equal(unknownResult.error.code, "UNKNOWN_FIELD");

const future = JSON.parse(encoded);
future.schemaVersion = 99;
const futureResult = decodeDirectorProjectDocument(future);
assert.equal(futureResult.ok, false);
if (futureResult.ok) throw new Error("future schema accepted");
assert.equal(futureResult.error.code, "FUTURE_SCHEMA_VERSION");

const dangling = JSON.parse(encoded);
dangling.objects[1].camera.lookAtObjectId = "missing-object";
const danglingResult = decodeDirectorProjectDocument(dangling);
assert.equal(danglingResult.ok, false);
if (danglingResult.ok) throw new Error("dangling reference accepted");
assert.equal(danglingResult.error.code, "DANGLING_REFERENCE");

const nonFinite = JSON.parse(encoded);
nonFinite.scene.backgroundColor = "ok";
nonFinite.objects[0].transform.position[0] = "not-a-number";
const nonFiniteResult = decodeDirectorProjectDocument(nonFinite);
assert.equal(nonFiniteResult.ok, false);
if (nonFiniteResult.ok) throw new Error("invalid numeric field accepted");
assert.equal(nonFiniteResult.error.code, "INVALID_FIELD");

console.log(
  JSON.stringify({
    batch: 81,
    status: "PASS",
    scenarios: [
      "strict V1 export excludes capture bytes and blob/data URLs",
      "owner/project identity rebind preserves internal entity references",
      "unknown field rejected",
      "future schema rejected",
      "dangling reference rejected",
      "invalid numeric field rejected",
    ],
    errors: [],
  }),
);
