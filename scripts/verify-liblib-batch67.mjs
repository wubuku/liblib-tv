import assert from "node:assert/strict";
import {
  createDirectorProjectDocumentV1,
  decodeDirectorProjectDocument,
  encodeDirectorProjectDocument,
} from "../src/lib/directorProjectDocument.ts";

const transform = (position = [0, 0, 0]) => ({
  position,
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});

const speedCurve = () => ({
  preset: "smooth",
  control1: [0.33, 0],
  control2: [0.67, 1],
});

function createSnapshot() {
  const character = {
    id: "character-1",
    name: "Lead",
    kind: "character",
    primitive: "character",
    color: "#8899aa",
    visible: true,
    locked: false,
    transform: transform([-1, 0, 0]),
    characterRig: {
      posePresetId: "stand",
      controls: {
        "head.yaw": 12,
        "body.offsetY": 0.04,
      },
    },
  };
  const prop = {
    id: "prop-1",
    name: "Imported chair",
    kind: "prop",
    primitive: "library",
    color: "#776655",
    visible: true,
    locked: false,
    transform: transform([1, 0, 0]),
    libraryAssetId: "asset-chair-1",
    libraryCategoryId: "my-models",
    libraryVisual: "chair",
    librarySource: "local",
    libraryFileName: "chair.obj",
  };
  const camera = {
    id: "camera-1",
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
  const path = {
    id: "path-1",
    objectId: character.id,
    name: "Lead path",
    preset: "pen",
    enabled: true,
    orientToPath: true,
    closed: false,
    pivot: [0, 0, 0],
    transform: transform(),
    initialAnchors: [
      {
        id: "anchor-a",
        position: [-1, 0, 0],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
      {
        id: "anchor-b",
        position: [1, 0, 1],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
    ],
    anchors: [
      {
        id: "anchor-a",
        position: [-1, 0, 0],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
      {
        id: "anchor-inserted",
        position: [0, 0, 0.6],
        type: "symmetric",
        handleIn: [-0.2, 0, 0],
        handleOut: [0.2, 0, 0],
      },
      {
        id: "anchor-b",
        position: [1, 0, 1],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
    ],
    points: [
      [-1, 0, 0],
      [0, 0, 0.6],
      [1, 0, 1],
    ],
  };
  return {
    projectId: "director-project-1",
    owner: {
      route: "libtv",
      canvasId: "canvas-a",
      sourceNodeId: "director-node-a",
    },
    scene: {
      name: "Codec fixture",
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [character, prop, camera],
    groups: [
      {
        id: "group-1",
        label: "Cast",
        characterIds: [character.id],
        crowd: null,
      },
    ],
    activeCameraId: camera.id,
    aspectRatio: "16:9",
    captures: [
      {
        id: "capture-1",
        dataUrl: "data:image/png;base64,SHOULD_NOT_BE_PORTABLE",
        cameraId: camera.id,
        cameraName: camera.name,
        aspectRatio: "16:9",
        width: 1280,
        height: 720,
        createdAt: "2026-08-27T09:30:00.000Z",
        sentNodeId: "graph-node-result",
      },
    ],
    timeline: {
      duration: 8,
      currentTime: 4,
      isPlaying: true,
      loop: true,
      zoom: 1.5,
      autoKeyframe: true,
      tracks: [
        {
          id: "track-transform",
          kind: "transform",
          objectId: character.id,
          label: "Lead transform",
          motionPathId: path.id,
          speedCurve: speedCurve(),
          keyframes: [
            {
              id: "keyframe-transform-0",
              time: 0,
              value: transform([-1, 0, 0]),
            },
            {
              id: "keyframe-transform-8",
              time: 8,
              value: transform([1, 0, 1]),
            },
          ],
        },
        {
          id: "track-camera",
          kind: "camera",
          objectId: camera.id,
          label: "Main camera",
          speedCurve: speedCurve(),
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
                target: [0.4, 1, 0],
                fov: 50,
              },
            },
          ],
        },
        {
          id: "track-pose",
          kind: "pose",
          objectId: character.id,
          label: "Lead pose",
          speedCurve: speedCurve(),
          keyframes: [
            {
              id: "keyframe-pose-0",
              time: 0,
              value: {
                posePresetId: "stand",
                controls: {},
              },
            },
            {
              id: "keyframe-pose-8",
              time: 8,
              value: {
                posePresetId: null,
                controls: { "head.yaw": 24 },
              },
            },
          ],
        },
        {
          id: "track-group",
          kind: "group",
          objectId: "group-1",
          groupId: "group-1",
          label: "Cast group",
          memberOffsets: {
            [character.id]: [-1, 0, 0],
          },
          speedCurve: speedCurve(),
          keyframes: [
            {
              id: "keyframe-group-0",
              time: 0,
              value: transform(),
            },
            {
              id: "keyframe-group-8",
              time: 8,
              value: transform([0.5, 0, 0]),
            },
          ],
        },
      ],
      motionPaths: [path],
      selectedTrackId: "track-transform",
      selectedKeyframeId: "keyframe-transform-0",
      selectedMotionPathId: path.id,
      selectedMotionPathAnchorId: "anchor-inserted",
      selectedMotionPathHandle: "out",
      motionPathDraft: {
        tool: "pencil",
        trackId: "track-transform",
        objectId: character.id,
        planeY: 0,
        anchors: [],
      },
      editorMode: "curve",
      cameraMotionPreset: {
        application: null,
        error: null,
      },
    },
    selectedObjectId: character.id,
    selectedObjectIds: [character.id],
    selectedGroupId: "group-1",
    viewMode: "camera",
    transformMode: "rotate",
    showThirds: true,
    viewportPanelsCollapsed: true,
    isCapturing: true,
    activeCaptureId: "capture-1",
    phoneVcam: {
      status: "recording",
    },
  };
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function rejectCase(name, base, mutate, expectedCode) {
  const candidate = cloneJson(base);
  mutate(candidate);
  const result = decodeDirectorProjectDocument(candidate);
  assert.equal(result.ok, false, `${name}: expected rejection`);
  assert.equal(
    result.error.code,
    expectedCode,
    `${name}: wrong error code at ${result.error.path}`,
  );
  assert.equal(
    Object.hasOwn(result, "document"),
    false,
    `${name}: rejected result leaked a partial document`,
  );
  return result.error.path;
}

const snapshot = createSnapshot();
const snapshotBefore = cloneJson(snapshot);
const document = createDirectorProjectDocumentV1(snapshot);
const encoded = encodeDirectorProjectDocument(document);
const decoded = decodeDirectorProjectDocument(JSON.parse(encoded));

assert.equal(decoded.ok, true, "valid V1 document must decode");
assert.equal(
  encodeDirectorProjectDocument(decoded.document),
  encoded,
  "encode/decode/encode must be deterministic",
);
assert.deepEqual(snapshot, snapshotBefore, "snapshot adapter mutated its input");
assert.deepEqual(
  document.objects.map((object) => object.id),
  ["character-1", "prop-1", "camera-1"],
  "object authoring order must be preserved",
);
assert.deepEqual(
  document.timeline.motionPaths[0].anchors.map((anchor) => anchor.id),
  ["anchor-a", "anchor-inserted", "anchor-b"],
  "motion path geometry order must be preserved",
);
assert.equal(
  document.resourceRefs[0].id,
  "asset-chair-1",
  "library asset should become a stable resource reference",
);
assert.equal(
  document.objects[1].assetRefId,
  "asset-chair-1",
  "library object should reference the generated resource descriptor",
);

for (const excluded of [
  "dataUrl",
  "sentNodeId",
  "selectedObjectId",
  "selectedTrackId",
  "currentTime",
  "isPlaying",
  "zoom",
  "motionPathDraft",
  "editorMode",
  "cameraMotionPreset",
  "phoneVcam",
]) {
  assert.equal(
    encoded.includes(excluded),
    false,
    `portable document leaked excluded field: ${excluded}`,
  );
}

const sourceDocument = JSON.parse(encoded);
const isolated = decodeDirectorProjectDocument(sourceDocument);
assert.equal(isolated.ok, true);
sourceDocument.scene.name = "mutated after decode";
sourceDocument.objects[0].transform.position[0] = 999;
assert.equal(isolated.document.scene.name, "Codec fixture");
assert.equal(isolated.document.objects[0].transform.position[0], -1);

const cases = [
  [
    "malformed root",
    () => decodeDirectorProjectDocument(null),
    "INVALID_DOCUMENT",
  ],
  [
    "future schema",
    (base) => rejectCase(
      "future schema",
      base,
      (candidate) => {
        candidate.schemaVersion = 2;
      },
      "FUTURE_SCHEMA_VERSION",
    ),
  ],
  [
    "unknown top-level field",
    (base) => rejectCase(
      "unknown top-level field",
      base,
      (candidate) => {
        candidate.selection = {};
      },
      "UNKNOWN_FIELD",
    ),
  ],
  [
    "unknown nested field",
    (base) => rejectCase(
      "unknown nested field",
      base,
      (candidate) => {
        candidate.scene.currentTime = 4;
      },
      "UNKNOWN_FIELD",
    ),
  ],
  [
    "duplicate object ID",
    (base) => rejectCase(
      "duplicate object ID",
      base,
      (candidate) => {
        candidate.objects[1].id = candidate.objects[0].id;
      },
      "DUPLICATE_ID",
    ),
  ],
  [
    "dangling active camera",
    (base) => rejectCase(
      "dangling active camera",
      base,
      (candidate) => {
        candidate.activeCameraId = "camera-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "dangling camera relation",
    (base) => rejectCase(
      "dangling camera relation",
      base,
      (candidate) => {
        candidate.objects[2].camera.lookAtObjectId = "object-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "dangling group member",
    (base) => rejectCase(
      "dangling group member",
      base,
      (candidate) => {
        candidate.groups[0].characterIds[0] = "character-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "dangling track target",
    (base) => rejectCase(
      "dangling track target",
      base,
      (candidate) => {
        candidate.timeline.tracks[0].objectId = "object-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "dangling path target",
    (base) => rejectCase(
      "dangling path target",
      base,
      (candidate) => {
        candidate.timeline.tracks[0].motionPathId = null;
        candidate.timeline.motionPaths[0].objectId = "object-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "track/path owner mismatch",
    (base) => rejectCase(
      "track/path owner mismatch",
      base,
      (candidate) => {
        candidate.timeline.motionPaths[0].objectId = "prop-1";
      },
      "INVALID_FIELD",
    ),
  ],
  [
    "duplicate keyframe ID",
    (base) => rejectCase(
      "duplicate keyframe ID",
      base,
      (candidate) => {
        candidate.timeline.tracks[1].keyframes[0].id =
          candidate.timeline.tracks[0].keyframes[0].id;
      },
      "DUPLICATE_ID",
    ),
  ],
  [
    "non-increasing keyframe time",
    (base) => rejectCase(
      "non-increasing keyframe time",
      base,
      (candidate) => {
        candidate.timeline.tracks[0].keyframes[1].time = 0;
      },
      "INVALID_FIELD",
    ),
  ],
  [
    "non-finite value",
    (base) => {
      const candidate = cloneJson(base);
      candidate.objects[0].transform.position[0] = Number.NaN;
      const result = decodeDirectorProjectDocument(candidate);
      assert.equal(result.ok, false);
      assert.equal(result.error.code, "NON_FINITE_NUMBER");
      assert.equal(Object.hasOwn(result, "document"), false);
      return result.error.path;
    },
  ],
  [
    "blob resource locator",
    (base) => rejectCase(
      "blob resource locator",
      base,
      (candidate) => {
        candidate.resourceRefs[0].locator = "blob:http://localhost/asset";
      },
      "INVALID_FIELD",
    ),
  ],
  [
    "dangling capture resource",
    (base) => rejectCase(
      "dangling capture resource",
      base,
      (candidate) => {
        candidate.captureDescriptors[0].resourceRefId = "resource-missing";
      },
      "DANGLING_REFERENCE",
    ),
  ],
  [
    "camera track targets prop",
    (base) => rejectCase(
      "camera track targets prop",
      base,
      (candidate) => {
        candidate.timeline.tracks[1].objectId = "prop-1";
      },
      "INVALID_FIELD",
    ),
  ],
];

const rejectionPaths = {};
for (const [name, run, expectedCode] of cases) {
  if (name === "malformed root") {
    const result = run();
    assert.equal(result.ok, false);
    assert.equal(result.error.code, expectedCode);
    assert.equal(Object.hasOwn(result, "document"), false);
    rejectionPaths[name] = result.error.path;
  } else {
    rejectionPaths[name] = run(sourceDocument);
  }
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      schemaVersion: document.schemaVersion,
      roundTripBytes: encoded.length,
      accepted: {
        objects: document.objects.length,
        groups: document.groups.length,
        tracks: document.timeline.tracks.length,
        motionPaths: document.timeline.motionPaths.length,
        resources: document.resourceRefs.length,
        captures: document.captureDescriptors.length,
      },
      rejectedCases: cases.length,
      rejectionPaths,
      excludedRuntimeFieldsVerified: true,
      inputIsolationVerified: true,
      orderPreservationVerified: true,
    },
    null,
    2,
  ),
);
