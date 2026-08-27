import assert from "node:assert/strict";
import {
  createDirectorProjectDocumentV1,
  normalizeDirectorProjectDocument,
} from "../src/lib/directorProjectDocument.ts";
import { planDirectorDelete } from "../src/lib/directorDeletePlanner.ts";

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

const cameraRelation = (lookAtObjectId = null, followTargetId = null) => ({
  fov: 45,
  target: [0, 1, 0],
  lookAtMode: lookAtObjectId ? "object" : "coordinate",
  lookAtObjectId,
  followTargetId,
  followOffset: [0, 1.2, 4.5],
  followView: "third-person",
});

function createPath(id, objectId) {
  const anchors = [
    {
      id: `${id}-a`,
      position: [0, 0, 0],
      type: "vertex",
      handleIn: [0, 0, 0],
      handleOut: [0, 0, 0],
    },
    {
      id: `${id}-b`,
      position: [1, 0, 1],
      type: "vertex",
      handleIn: [0, 0, 0],
      handleOut: [0, 0, 0],
    },
  ];
  return {
    id,
    objectId,
    name: id,
    preset: "line",
    enabled: true,
    orientToPath: false,
    closed: false,
    pivot: [0, 0, 0],
    transform: transform(),
    initialAnchors: anchors,
    anchors,
    points: anchors.map((anchor) => anchor.position),
  };
}

function createFixture() {
  const characterA = {
    id: "character-a",
    name: "Character A",
    kind: "character",
    primitive: "character",
    color: "#8899aa",
    visible: true,
    locked: false,
    transform: transform([-1, 0, 0]),
    characterRig: { posePresetId: "stand", controls: {} },
  };
  const characterB = {
    ...characterA,
    id: "character-b",
    name: "Character B",
    transform: transform([1, 0, 0]),
  };
  const localProp = {
    id: "prop-local",
    name: "Local prop",
    kind: "prop",
    primitive: "library",
    color: "#776655",
    visible: true,
    locked: false,
    transform: transform([0, 0, 1]),
    libraryAssetId: "resource-local-model",
    libraryCategoryId: "my-models",
    libraryVisual: "chair",
    librarySource: "local",
    libraryFileName: "chair.glb",
  };
  const cameraA = {
    id: "camera-a",
    name: "Camera A",
    kind: "camera",
    primitive: "camera",
    color: "#77ccff",
    visible: true,
    locked: false,
    transform: transform([4, 2, 6]),
    camera: cameraRelation(characterA.id, characterA.id),
  };
  const cameraB = {
    ...cameraA,
    id: "camera-b",
    name: "Camera B",
    transform: transform([-4, 2, 6]),
    camera: cameraRelation(),
  };
  const characterPath = createPath("path-character-a", characterA.id);
  const propPath = createPath("path-prop-local", localProp.id);
  const tracks = [
    {
      id: "track-character-a",
      kind: "transform",
      objectId: characterA.id,
      label: "Character A transform",
      motionPathId: characterPath.id,
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-character-a",
          time: 0,
          value: transform([-1, 0, 0]),
        },
      ],
    },
    {
      id: "track-character-a-pose",
      kind: "pose",
      objectId: characterA.id,
      label: "Character A pose",
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-character-a-pose",
          time: 0,
          value: { posePresetId: "stand", controls: {} },
        },
      ],
    },
    {
      id: "track-group",
      kind: "group",
      objectId: "group-cast",
      groupId: "group-cast",
      label: "Cast group",
      memberOffsets: {
        [characterA.id]: [0, 0, 0],
        [characterB.id]: [2, 0, 0],
      },
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-group",
          time: 0,
          value: transform(),
        },
      ],
    },
    {
      id: "track-prop",
      kind: "transform",
      objectId: localProp.id,
      label: "Prop transform",
      motionPathId: propPath.id,
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-prop",
          time: 0,
          value: transform([0, 0, 1]),
        },
      ],
    },
    ...[cameraA, cameraB].map((camera) => ({
      id: `track-${camera.id}`,
      kind: "camera",
      objectId: camera.id,
      label: camera.name,
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: `keyframe-${camera.id}`,
          time: 0,
          value: {
            transform: camera.transform,
            target: camera.camera.target,
            fov: camera.camera.fov,
          },
        },
      ],
    })),
  ];
  const document = createDirectorProjectDocumentV1({
    projectId: "batch72-project",
    owner: {
      route: "libtv",
      canvasId: "batch72-canvas",
      sourceNodeId: "batch72-source",
    },
    scene: {
      name: "Batch 72 fixture",
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [characterA, characterB, localProp, cameraA, cameraB],
    groups: [
      {
        id: "group-cast",
        label: "Cast",
        characterIds: [characterA.id, characterB.id],
      },
    ],
    activeCameraId: cameraA.id,
    aspectRatio: "16:9",
    resourceRefs: [
      {
        id: "resource-capture",
        kind: "media",
        source: "canvas",
        label: "Capture resource",
        locator: "capture://batch72",
        mimeType: "image/png",
      },
    ],
    captures: [
      {
        id: "capture-camera-a",
        dataUrl: "data:image/png;base64,QkFUQ0g3Mg==",
        cameraId: cameraA.id,
        cameraName: cameraA.name,
        aspectRatio: "16:9",
        width: 1280,
        height: 720,
        createdAt: "2026-08-27T12:00:00.000Z",
        sentNodeId: "ordinary-graph-node",
      },
    ],
    timeline: {
      duration: 8,
      currentTime: 2,
      isPlaying: false,
      loop: true,
      zoom: 1,
      autoKeyframe: true,
      tracks,
      motionPaths: [characterPath, propPath],
      selectedTrackId: tracks[0].id,
      selectedKeyframeId: tracks[0].keyframes[0].id,
      selectedMotionPathId: characterPath.id,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      editorMode: "timeline",
      cameraMotionPreset: { application: null, error: null },
    },
  });
  return normalizeDirectorProjectDocument({
    ...document,
    captureDescriptors: document.captureDescriptors.map((capture) => ({
      ...capture,
      resourceRefId: "resource-capture",
    })),
  });
}

function plan(document, command) {
  return planDirectorDelete(
    document,
    command,
    normalizeDirectorProjectDocument,
  );
}

const fixture = createFixture();
const fixtureFingerprint = JSON.stringify(fixture);

const characterDelete = plan(fixture, {
  kind: "DELETE_OBJECT",
  objectId: "character-a",
});
assert.equal(characterDelete.disposition, "READY");
assert.deepEqual(characterDelete.closure.deletedObjectIds, ["character-a"]);
assert.deepEqual(characterDelete.closure.deletedTrackIds, [
  "track-character-a",
  "track-character-a-pose",
]);
assert.deepEqual(characterDelete.closure.deletedPathIds, ["path-character-a"]);
assert.deepEqual(characterDelete.document.groups[0].characterIds, [
  "character-b",
]);
assert.deepEqual(
  characterDelete.document.timeline.tracks.find(
    (track) => track.id === "track-group",
  ).memberOffsets,
  { "character-b": [2, 0, 0] },
);
const repairedCamera = characterDelete.document.objects.find(
  (object) => object.id === "camera-a",
);
assert.equal(repairedCamera.camera.lookAtMode, "coordinate");
assert.equal(repairedCamera.camera.lookAtObjectId, null);
assert.equal(repairedCamera.camera.followTargetId, null);
assert.equal(JSON.stringify(fixture), fixtureFingerprint);

const activeCameraDelete = plan(fixture, {
  kind: "DELETE_OBJECT",
  objectId: "camera-a",
});
assert.equal(activeCameraDelete.disposition, "READY");
assert.equal(activeCameraDelete.document.activeCameraId, "camera-b");
assert.equal(
  activeCameraDelete.document.captureDescriptors[0].cameraId,
  null,
);

const oneCameraDocument = normalizeDirectorProjectDocument({
  ...fixture,
  objects: fixture.objects.filter((object) => object.id !== "camera-b"),
  timeline: {
    ...fixture.timeline,
    tracks: fixture.timeline.tracks.filter(
      (track) => track.objectId !== "camera-b",
    ),
  },
});
const lastCameraDelete = plan(oneCameraDocument, {
  kind: "DELETE_OBJECT",
  objectId: "camera-a",
});
assert.equal(lastCameraDelete.disposition, "REJECTED");
assert.equal(lastCameraDelete.reason, "DIRECTOR_LAST_CAMERA_REQUIRED");
assert.equal(lastCameraDelete.document, oneCameraDocument);

const ungroup = plan(fixture, {
  kind: "DELETE_GROUP",
  groupId: "group-cast",
  memberPolicy: "UNGROUP",
});
assert.equal(ungroup.disposition, "READY");
assert.equal(ungroup.document.groups.length, 0);
assert.equal(
  ungroup.document.objects.some((object) => object.id === "character-a"),
  true,
);
assert.equal(
  ungroup.document.timeline.tracks.some(
    (track) => track.id === "track-group",
  ),
  false,
);

const pathDelete = plan(fixture, {
  kind: "DELETE_MOTION_PATH",
  pathId: "path-character-a",
});
assert.equal(pathDelete.disposition, "READY");
assert.equal(
  pathDelete.document.timeline.tracks.find(
    (track) => track.id === "track-character-a",
  ).motionPathId,
  null,
);

const resourceBlocked = plan(fixture, {
  kind: "DELETE_RESOURCE",
  resourceId: "resource-local-model",
  instancePolicy: "BLOCK",
});
assert.equal(resourceBlocked.disposition, "REJECTED");
assert.equal(resourceBlocked.reason, "DIRECTOR_RESOURCE_IN_USE");
assert.equal(resourceBlocked.document, fixture);

const resourceCascade = plan(fixture, {
  kind: "DELETE_RESOURCE",
  resourceId: "resource-local-model",
  instancePolicy: "CASCADE",
});
assert.equal(resourceCascade.disposition, "READY");
assert.deepEqual(resourceCascade.closure.deletedObjectIds, ["prop-local"]);
assert.deepEqual(resourceCascade.closure.deletedPathIds, ["path-prop-local"]);
assert.equal(
  resourceCascade.document.resourceRefs.some(
    (resource) => resource.id === "resource-local-model",
  ),
  false,
);

const captureDelete = plan(fixture, {
  kind: "DELETE_CAPTURE",
  captureId: "capture-camera-a",
});
assert.equal(captureDelete.disposition, "READY");
assert.deepEqual(captureDelete.document.captureDescriptors, []);
assert.deepEqual(captureDelete.closure.deletedResourceIds, [
  "resource-capture",
]);

const result = {
  status: "PASS",
  batch: 72,
  scenarios: [
    "object closure",
    "camera fallback and capture repair",
    "last camera rejection",
    "group ungroup",
    "path detach",
    "resource block and cascade",
    "capture and resource closure",
    "input immutability",
  ],
};

console.log(JSON.stringify(result));
