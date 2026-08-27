import assert from "node:assert/strict";
import {
  buildDirectorClipboardPacket,
  planDirectorClipboardPaste,
  validateDirectorClipboardPacket,
} from "../src/lib/directorClipboard.ts";
import { createDirectorProjectDocumentV1 } from "../src/lib/directorProjectDocument.ts";

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

const emptyRuntimeTimeline = (tracks, motionPaths) => ({
  duration: 8,
  currentTime: 4,
  isPlaying: true,
  loop: true,
  zoom: 1.5,
  autoKeyframe: true,
  tracks,
  motionPaths,
  selectedTrackId: tracks[0]?.id ?? null,
  selectedKeyframeId: tracks[0]?.keyframes[0]?.id ?? null,
  selectedMotionPathId: motionPaths[0]?.id ?? null,
  selectedMotionPathAnchorId: motionPaths[0]?.anchors[0]?.id ?? null,
  selectedMotionPathHandle: "out",
  motionPathDraft: null,
  editorMode: "curve",
  cameraMotionPreset: {
    application: null,
    error: null,
  },
});

function createDocument(projectId = "batch75-project-a") {
  const characterA = {
    id: "character-a",
    name: "Lead",
    kind: "character",
    primitive: "character",
    color: "#8899aa",
    visible: true,
    locked: false,
    transform: transform([-1, 0, 0]),
    characterRig: {
      posePresetId: "stand",
      controls: { "head.yaw": 12 },
    },
  };
  const characterD = {
    id: "character-d",
    name: "Partner",
    kind: "character",
    primitive: "character",
    color: "#aa9988",
    visible: true,
    locked: false,
    transform: transform([0.5, 0, 0.3]),
    characterRig: {
      posePresetId: "stand",
      controls: {},
    },
  };
  const propB = {
    id: "prop-b",
    name: "Local chair",
    kind: "prop",
    primitive: "library",
    color: "#776655",
    visible: true,
    locked: false,
    transform: transform([1.4, 0, 0.2]),
    libraryAssetId: "resource-chair",
    libraryCategoryId: "my-models",
    libraryVisual: "chair",
    librarySource: "local",
    libraryFileName: "chair.obj",
  };
  const cameraC = {
    id: "camera-c",
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
      lookAtObjectId: characterA.id,
      followTargetId: propB.id,
      followOffset: [0, 1.2, 4.5],
      followView: "third-person",
    },
  };
  const pathA = {
    id: "path-a",
    objectId: characterA.id,
    name: "Lead path",
    preset: "pen",
    enabled: true,
    orientToPath: true,
    closed: false,
    pivot: [0, 0, 0],
    transform: transform([0.2, 0, 0.1]),
    initialAnchors: [
      {
        id: "anchor-a-0",
        position: [-1, 0, 0],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
      {
        id: "anchor-a-1",
        position: [1, 0, 1],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
    ],
    anchors: [
      {
        id: "anchor-a-0",
        position: [-1, 0, 0],
        type: "vertex",
        handleIn: [0, 0, 0],
        handleOut: [0, 0, 0],
      },
      {
        id: "anchor-a-mid",
        position: [0, 0, 0.6],
        type: "symmetric",
        handleIn: [-0.2, 0, 0],
        handleOut: [0.2, 0, 0],
      },
      {
        id: "anchor-a-1",
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
  const tracks = [
    {
      id: "track-a-transform",
      kind: "transform",
      objectId: characterA.id,
      label: "Lead transform",
      motionPathId: pathA.id,
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-a-transform-0",
          time: 0,
          value: transform([-1, 0, 0]),
        },
        {
          id: "keyframe-a-transform-8",
          time: 8,
          value: transform([1, 0, 1]),
        },
      ],
    },
    {
      id: "track-a-pose",
      kind: "pose",
      objectId: characterA.id,
      label: "Lead pose",
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-a-pose-0",
          time: 0,
          value: { posePresetId: "stand", controls: {} },
        },
        {
          id: "keyframe-a-pose-8",
          time: 8,
          value: { posePresetId: null, controls: { "head.yaw": 24 } },
        },
      ],
    },
    {
      id: "track-d-transform",
      kind: "transform",
      objectId: characterD.id,
      label: "Partner transform",
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-d-transform-0",
          time: 0,
          value: transform([0.5, 0, 0.3]),
        },
      ],
    },
    {
      id: "track-b-transform",
      kind: "transform",
      objectId: propB.id,
      label: "Chair transform",
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-b-transform-0",
          time: 0,
          value: transform([1.4, 0, 0.2]),
        },
      ],
    },
    {
      id: "track-c-camera",
      kind: "camera",
      objectId: cameraC.id,
      label: "Main camera",
      speedCurve: speedCurve(),
      keyframes: [
        {
          id: "keyframe-c-camera-0",
          time: 0,
          value: {
            transform: transform([4, 2, 6]),
            target: [0, 1, 0],
            fov: 45,
          },
        },
        {
          id: "keyframe-c-camera-8",
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
      id: "track-group",
      kind: "group",
      objectId: "group-cast",
      groupId: "group-cast",
      label: "Cast group",
      memberOffsets: {
        [characterA.id]: [-1, 0, 0],
        [characterD.id]: [0.5, 0, 0.3],
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
          value: transform([0.5, 0, 0.2]),
        },
      ],
    },
  ];
  return createDirectorProjectDocumentV1({
    projectId,
    owner: {
      route: "libtv",
      canvasId: "batch75-canvas-a",
      sourceNodeId: "batch75-director-a",
    },
    scene: {
      name: "Batch 75 fixture",
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [characterA, characterD, propB, cameraC],
    groups: [
      {
        id: "group-cast",
        label: "Cast",
        characterIds: [characterA.id, characterD.id],
      },
    ],
    activeCameraId: cameraC.id,
    aspectRatio: "16:9",
    captures: [
      {
        id: "capture-x",
        dataUrl: "data:image/png;base64,NOT_PORTABLE",
        cameraId: cameraC.id,
        cameraName: cameraC.name,
        aspectRatio: "16:9",
        width: 1280,
        height: 720,
        createdAt: "2026-08-27T18:00:00.000Z",
        sentNodeId: "ordinary-graph-result",
      },
    ],
    timeline: emptyRuntimeTimeline(tracks, [pathA]),
  });
}

const deterministicId = ({
  kind,
  sourceId,
  pasteOrdinal,
  attempt,
}) => `${kind}-paste-${pasteOrdinal}-${sourceId}-${attempt}`;

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

const document = createDocument();

const singleObject = buildDirectorClipboardPacket({
  document,
  selection: {
    selectedObjectIds: ["character-a"],
    selectedGroupId: null,
  },
});
assert.equal(singleObject.ok, true);
assert.deepEqual(
  singleObject.packet.objects.map((object) => object.id),
  ["character-a"],
);
assert.deepEqual(
  singleObject.packet.timeline.tracks.map((track) => track.id),
  ["track-a-transform", "track-a-pose"],
);
assert.deepEqual(
  singleObject.packet.timeline.motionPaths.map((path) => path.id),
  ["path-a"],
);
assert.deepEqual(singleObject.packet.groups, []);

const groupClosure = buildDirectorClipboardPacket({
  document,
  selection: {
    selectedObjectIds: ["character-a"],
    selectedGroupId: "group-cast",
  },
});
assert.equal(groupClosure.ok, true);
assert.deepEqual(groupClosure.packet.selection.selectedObjectIds, [
  "character-a",
  "character-d",
]);
assert.deepEqual(
  groupClosure.packet.timeline.tracks.map((track) => track.id),
  [
    "track-a-transform",
    "track-a-pose",
    "track-d-transform",
    "track-group",
  ],
);
assert.equal(groupClosure.packet.groups.length, 1);
assert.equal(JSON.stringify(groupClosure.packet).includes("capture-x"), false);
assert.equal(
  JSON.stringify(groupClosure.packet).includes("ordinary-graph-result"),
  false,
);
assert.equal(
  JSON.stringify(groupClosure.packet).includes("NOT_PORTABLE"),
  false,
);

const externalCamera = buildDirectorClipboardPacket({
  document,
  selection: {
    selectedObjectIds: ["camera-c"],
    selectedGroupId: null,
  },
});
assert.equal(externalCamera.ok, true);
assert.equal(externalCamera.packet.objects[0].camera.lookAtMode, "coordinate");
assert.equal(externalCamera.packet.objects[0].camera.lookAtObjectId, null);
assert.equal(externalCamera.packet.objects[0].camera.followTargetId, null);

const internalCamera = buildDirectorClipboardPacket({
  document,
  selection: {
    selectedObjectIds: ["character-a", "camera-c"],
    selectedGroupId: null,
  },
});
assert.equal(internalCamera.ok, true);
const packetCamera = internalCamera.packet.objects.find(
  (object) => object.id === "camera-c",
);
assert.equal(packetCamera.camera.lookAtObjectId, "character-a");
assert.equal(packetCamera.camera.followTargetId, null);

const internalPaste = planDirectorClipboardPaste({
  document,
  packet: internalCamera.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.equal(internalPaste.ok, true);
const copiedCharacterId =
  internalPaste.plan.idMaps.objects["character-a"];
const copiedCameraId = internalPaste.plan.idMaps.objects["camera-c"];
const copiedCamera = internalPaste.plan.document.objects.find(
  (object) => object.id === copiedCameraId,
);
assert.equal(copiedCamera.camera.lookAtObjectId, copiedCharacterId);
assert.equal(copiedCamera.camera.followTargetId, null);
assert.deepEqual(copiedCamera.camera.target, [0.6, 1, 0.6]);
assert.equal(internalPaste.plan.document.activeCameraId, "camera-c");

const groupPaste = planDirectorClipboardPaste({
  document,
  packet: groupClosure.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.equal(groupPaste.ok, true);
assert.equal(groupPaste.plan.offset, 0.6);
assert.equal(groupPaste.plan.selection.selectedGroupId, "group-paste-1-group-cast-0");
assert.deepEqual(groupPaste.plan.selection.selectedObjectIds, [
  "object-paste-1-character-a-0",
  "object-paste-1-character-d-0",
]);
const pastedGroup = groupPaste.plan.document.groups.find(
  (group) => group.id === groupPaste.plan.selection.selectedGroupId,
);
assert.deepEqual(pastedGroup.characterIds, groupPaste.plan.selection.selectedObjectIds);
const pastedGroupTrack = groupPaste.plan.document.timeline.tracks.find(
  (track) =>
    track.kind === "group" &&
    track.groupId === groupPaste.plan.selection.selectedGroupId,
);
assert.equal(pastedGroupTrack.objectId, pastedGroup.id);
assert.deepEqual(
  Object.keys(pastedGroupTrack.memberOffsets),
  pastedGroup.characterIds,
);
const pastedLead = groupPaste.plan.document.objects.find(
  (object) => object.id === groupPaste.plan.selection.selectedObjectIds[0],
);
assert.deepEqual(pastedLead.transform.position, [-0.4, 0, 0.6]);
const pastedTransformTrack = groupPaste.plan.document.timeline.tracks.find(
  (track) =>
    track.kind === "transform" && track.objectId === pastedLead.id,
);
assert.deepEqual(
  pastedTransformTrack.keyframes[0].value.position,
  [-0.4, 0, 0.6],
);
const pastedPath = groupPaste.plan.document.timeline.motionPaths.find(
  (path) => path.objectId === pastedLead.id,
);
assert.deepEqual(pastedPath.transform.position, [0.8, 0, 0.7]);
assert.notEqual(pastedPath.id, "path-a");
assert.notEqual(pastedPath.anchors[0].id, "anchor-a-0");
assert.equal(pastedPath.initialAnchors[0].id, pastedPath.anchors[0].id);
assert.equal(
  groupPaste.plan.document.timeline.tracks.some((track) =>
    track.keyframes.some((keyframe) => keyframe.id.startsWith("keyframe-a-")),
  ),
  true,
  "source keyframes should remain in the destination document",
);
assert.equal(
  groupPaste.plan.document.timeline.tracks
    .filter((track) => groupPaste.plan.pastedTrackIds.includes(track.id))
    .some((track) =>
      track.keyframes.some((keyframe) => keyframe.id.startsWith("keyframe-a-")),
    ),
  false,
  "pasted keyframes must all receive new identities",
);

const secondGroupPaste = planDirectorClipboardPaste({
  document: groupPaste.plan.document,
  packet: groupClosure.packet,
  pasteOrdinal: 2,
  createId: deterministicId,
});
assert.equal(secondGroupPaste.ok, true);
assert.equal(secondGroupPaste.plan.offset, 1.2);
const secondLead = secondGroupPaste.plan.document.objects.find(
  (object) => object.id === secondGroupPaste.plan.selection.selectedObjectIds[0],
);
assert.deepEqual(secondLead.transform.position, [0.2, 0, 1.2]);
assert.equal(
  groupPaste.plan.selection.selectedObjectIds.some((id) =>
    secondGroupPaste.plan.selection.selectedObjectIds.includes(id),
  ),
  false,
);

const resourcePacket = buildDirectorClipboardPacket({
  document,
  selection: {
    selectedObjectIds: ["prop-b"],
    selectedGroupId: null,
  },
});
assert.equal(resourcePacket.ok, true);
assert.deepEqual(resourcePacket.packet.resourceRefs.map((item) => item.id), [
  "resource-chair",
]);
const resourcePaste = planDirectorClipboardPaste({
  document,
  packet: resourcePacket.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.equal(resourcePaste.ok, true);
assert.deepEqual(resourcePaste.plan.aliasedResourceIds, ["resource-chair"]);
assert.equal(
  resourcePaste.plan.document.resourceRefs.filter(
    (resource) => resource.id === "resource-chair",
  ).length,
  1,
);

const destinationWithoutResource = cloneJson(document);
destinationWithoutResource.objects = destinationWithoutResource.objects.filter(
  (object) => object.id !== "prop-b",
);
destinationWithoutResource.timeline.tracks =
  destinationWithoutResource.timeline.tracks.filter(
    (track) => track.objectId !== "prop-b",
  );
destinationWithoutResource.resourceRefs = [];
const destinationCamera = destinationWithoutResource.objects.find(
  (object) => object.id === "camera-c",
);
destinationCamera.camera.followTargetId = null;
const missingResource = planDirectorClipboardPaste({
  document: destinationWithoutResource,
  packet: resourcePacket.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.deepEqual(missingResource, {
  ok: false,
  reason: "RESOURCE_MISSING",
});

const conflictingDocument = cloneJson(document);
conflictingDocument.resourceRefs[0].label = "Conflicting chair";
const conflictingResource = planDirectorClipboardPaste({
  document: conflictingDocument,
  packet: resourcePacket.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.deepEqual(conflictingResource, {
  ok: false,
  reason: "RESOURCE_CONFLICT",
});

const stalePacket = planDirectorClipboardPaste({
  document: createDocument("batch75-project-b"),
  packet: singleObject.packet,
  pasteOrdinal: 1,
  createId: deterministicId,
});
assert.deepEqual(stalePacket, {
  ok: false,
  reason: "PROJECT_MISMATCH",
});

const malformedPacket = cloneJson(singleObject.packet);
malformedPacket.runtime = { selected: true };
assert.deepEqual(validateDirectorClipboardPacket(malformedPacket), {
  ok: false,
  reason: "INVALID_PACKET",
});
assert.deepEqual(
  buildDirectorClipboardPacket({
    document,
    selection: {
      selectedObjectIds: [],
      selectedGroupId: null,
    },
  }),
  {
    ok: false,
    reason: "EMPTY_SELECTION",
  },
);

const allocationFailure = planDirectorClipboardPaste({
  document,
  packet: singleObject.packet,
  pasteOrdinal: 1,
  createId: () => "character-a",
});
assert.deepEqual(allocationFailure, {
  ok: false,
  reason: "IDENTITY_ALLOCATION_FAILED",
});

console.log(
  JSON.stringify(
    {
      status: "PASS",
      batch: 75,
      scenarios: [
        "single-object typed closure",
        "selected-group full closure",
        "external camera detach and coordinate freeze",
        "internal camera relation remap",
        "object/group/track/path/keyframe/anchor identity remap",
        "deterministic repeated paste offset",
        "stable resource alias",
        "missing and conflicting resource rejection",
        "cross-project stale rejection",
        "strict packet shape and empty selection",
        "identity allocation failure",
        "capture/runtime/graph projection exclusion",
      ],
      counts: {
        groupObjects: groupClosure.packet.objects.length,
        groupTracks: groupClosure.packet.timeline.tracks.length,
        groupPaths: groupClosure.packet.timeline.motionPaths.length,
        remappedKeyframes: Object.keys(groupPaste.plan.idMaps.keyframes).length,
        remappedAnchors: Object.keys(groupPaste.plan.idMaps.anchors).length,
      },
      errors: [],
    },
    null,
    2,
  ),
);
