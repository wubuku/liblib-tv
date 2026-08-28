import assert from "node:assert/strict";
import {
  createDirectorProjectDocumentV1,
} from "../src/lib/directorProjectDocument.ts";
import { planDirectorWholeProjectDuplicate } from "../src/lib/directorWholeProjectDuplicate.ts";

const sourceCanvasId = "canvas-source";
const targetCanvasId = "canvas-target";
const ownerA = {
  route: "libtv",
  canvasId: sourceCanvasId,
  sourceNodeId: "director-a",
};
const ownerB = {
  route: "libtv",
  canvasId: sourceCanvasId,
  sourceNodeId: "director-b",
};

let sequence = 0;
const deterministicFactory = ({ kind, sourceId, projectOrdinal, index }) =>
  `batch79-${kind}-${sourceId}-${projectOrdinal}-${index}-${++sequence}`;
const transform = (x, y, z) => ({
  position: [x, y, z],
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
});
const makeDocument = (projectId, owner) =>
  createDirectorProjectDocumentV1({
    projectId,
    owner,
    scene: {
      name: "Batch 79 scene",
      backgroundColor: "#20252b",
      groundColor: "#30343a",
      showGround: true,
      showGrid: true,
    },
    objects: [
      {
        id: "character-source",
        name: "Character",
        kind: "character",
        primitive: "character",
        color: "#7f91a5",
        visible: true,
        locked: false,
        transform: transform(0, 0, 0),
        characterRig: { posePresetId: "stand", controls: { shoulder: 0.2 } },
      },
      {
        id: "prop-source",
        name: "Catalog mug",
        kind: "prop",
        primitive: "mug",
        color: "#d2a679",
        visible: true,
        locked: false,
        transform: transform(1, 0, 0),
        libraryAssetId: "resource-catalog",
        librarySource: "catalog",
        libraryFileName: "catalog-mug.glb",
      },
      {
        id: "camera-source",
        name: "Main Camera",
        kind: "camera",
        primitive: "camera",
        color: "#ffffff",
        visible: true,
        locked: false,
        transform: transform(0, 2, 6),
        camera: {
          fov: 45,
          target: [0, 0, 0],
          lookAtMode: "object",
          lookAtObjectId: "character-source",
          followTargetId: "character-source",
          followOffset: [0, 1, 4],
          followView: "third-person",
        },
      },
    ],
    groups: [
      {
        id: "group-source",
        label: "Lead group",
        characterIds: ["character-source"],
        crowd: null,
      },
    ],
    activeCameraId: "camera-source",
    aspectRatio: "16:9",
    timeline: {
      duration: 10,
      currentTime: 3,
      isPlaying: false,
      loop: true,
      zoom: 1,
      autoKeyframe: true,
      selectedTrackId: null,
      selectedKeyframeId: null,
      selectedMotionPathId: null,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      editorMode: "timeline",
      cameraMotionPreset: { application: null, error: null },
      tracks: [
        {
          id: "transform-track-source",
          kind: "transform",
          objectId: "character-source",
          label: "Character transform",
          motionPathId: "path-source",
          speedCurve: {
            preset: "linear",
            control1: [0, 0],
            control2: [1, 1],
          },
          keyframes: [
            { id: "transform-keyframe-0", time: 0, value: transform(0, 0, 0) },
            { id: "transform-keyframe-1", time: 10, value: transform(2, 0, 0) },
          ],
        },
        {
          id: "camera-track-source",
          kind: "camera",
          objectId: "camera-source",
          label: "Camera transform",
          motionPathId: null,
          speedCurve: {
            preset: "smooth",
            control1: [0.2, 0],
            control2: [0.8, 1],
          },
          keyframes: [
            {
              id: "camera-keyframe-0",
              time: 0,
              value: {
                transform: transform(0, 2, 6),
                target: [0, 0, 0],
                fov: 45,
              },
            },
          ],
        },
        {
          id: "pose-track-source",
          kind: "pose",
          objectId: "character-source",
          label: "Character pose",
          motionPathId: null,
          speedCurve: {
            preset: "linear",
            control1: [0, 0],
            control2: [1, 1],
          },
          keyframes: [
            {
              id: "pose-keyframe-0",
              time: 0,
              value: { posePresetId: "stand", controls: { shoulder: 0.2 } },
            },
          ],
        },
        {
          id: "group-track-source",
          kind: "group",
          objectId: "group-source",
          groupId: "group-source",
          label: "Group transform",
          motionPathId: null,
          memberOffsets: { "character-source": [0, 0, 0] },
          speedCurve: {
            preset: "linear",
            control1: [0, 0],
            control2: [1, 1],
          },
          keyframes: [
            { id: "group-keyframe-0", time: 0, value: transform(0, 0, 0) },
          ],
        },
      ],
      motionPaths: [
        {
          id: "path-source",
          objectId: "character-source",
          name: "Lead path",
          preset: "line",
          enabled: true,
          orientToPath: true,
          closed: false,
          pivot: [0, 0, 0],
          transform: transform(0, 0, 0),
          initialAnchors: [
            {
              id: "anchor-source-0",
              position: [0, 0, 0],
              type: "vertex",
              handleIn: [0, 0, 0],
              handleOut: [0, 0, 0],
            },
            {
              id: "anchor-source-1",
              position: [2, 0, 0],
              type: "vertex",
              handleIn: [0, 0, 0],
              handleOut: [0, 0, 0],
            },
          ],
          anchors: [
            {
              id: "anchor-source-0",
              position: [0, 0, 0],
              type: "vertex",
              handleIn: [0, 0, 0],
              handleOut: [0, 0, 0],
            },
            {
              id: "anchor-source-1",
              position: [2, 0, 0],
              type: "vertex",
              handleIn: [0, 0, 0],
              handleOut: [0, 0, 0],
            },
          ],
        },
      ],
    },
    captures: [],
    resourceRefs: [
      {
        id: "resource-catalog",
        kind: "model",
        source: "catalog",
        label: "Catalog mug",
        locator: "catalog://mug",
        mimeType: "model/gltf-binary",
      },
    ],
  });

const sourceDocument = makeDocument("project-a", ownerA);
sourceDocument.resourceRefs = [
  {
    id: "resource-catalog",
    kind: "model",
    source: "catalog",
    label: "Catalog mug",
    locator: "catalog://mug",
    mimeType: "model/gltf-binary",
  },
];
sourceDocument.objects = sourceDocument.objects.map((object) =>
  object.id === "director-prop-mug"
    ? { ...object, assetRefId: "resource-catalog" }
    : object,
);
sourceDocument.captureDescriptors = [
  {
    id: "capture-source",
    cameraId: "camera-source",
    cameraName: "Main Camera",
    aspectRatio: "16:9",
    width: 1280,
    height: 720,
    createdAt: "2026-08-28T10:00:00.000Z",
    resourceRefId: "resource-catalog",
  },
];

const sourceNodes = [
  { id: "director-a", type: "script-execution", position: { x: 0, y: 0 }, data: {} },
  { id: "director-b", type: "script-execution", position: { x: 500, y: 0 }, data: {} },
  {
    id: "capture-result",
    type: "image",
    position: { x: 300, y: 300 },
    data: {
      directorCapture: {
        sourceNodeId: "director-a",
        captureId: "capture-source",
        cameraId: "camera-source",
        aspectRatio: "16:9",
        edgeId: "edge-a-result",
      },
    },
  },
];
const sourceEdges = [
  {
    id: "edge-a-result",
    source: "director-a",
    target: "capture-result",
    sourceHandle: "source",
    targetHandle: "target",
  },
];

const beforeSource = structuredClone({
  sourceDocument,
  sourceNodes,
  sourceEdges,
});
const planned = planDirectorWholeProjectDuplicate({
  sourceCanvasId,
  targetCanvasId,
  sourceNodes,
  sourceEdges,
  sourceViewport: { x: 42, y: -18, zoom: 0.8 },
  projects: [
    {
      sourceOwner: ownerA,
      sourceDocument,
      sourceLifecycle: "ACTIVE",
      sourcePersistenceDisposition: "RESTORED",
    },
    {
      sourceOwner: ownerB,
      sourceDocument: null,
      sourceLifecycle: null,
      sourcePersistenceDisposition: "MISSING",
    },
  ],
  createProjectId: deterministicFactory,
  createEntityId: deterministicFactory,
  createGraphNodeId: deterministicFactory,
  createGraphEdgeId: deterministicFactory,
  createFreshDocument: makeDocument,
});

assert.equal(planned.ok, true);
if (!planned.ok) throw new Error(planned.reason);
const plan = planned.plan;
assert.equal(plan.projects.length, 2);
assert.equal(plan.projects[0].sourceWasFresh, false);
assert.equal(plan.projects[1].sourceWasFresh, true);
assert.equal(plan.targetViewport.zoom, 0.8);
assert.notEqual(plan.projects[0].projectId, sourceDocument.projectId);
assert.notEqual(plan.projects[0].targetOwner.sourceNodeId, ownerA.sourceNodeId);
assert.equal(
  plan.projects[0].document.owner.canvasId,
  targetCanvasId,
);
assert.equal(plan.projects[0].document.objects.length, sourceDocument.objects.length);
assert.equal(plan.projects[0].document.timeline.tracks.length, sourceDocument.timeline.tracks.length);
assert.equal(plan.projects[0].document.captureDescriptors.length, 1);
assert.notEqual(
  plan.projects[0].document.captureDescriptors[0].id,
  sourceDocument.captureDescriptors[0].id,
);
assert.equal(
  plan.projects[0].document.captureDescriptors[0].resourceRefId,
  plan.projects[0].idMaps.resources["resource-catalog"],
);
assert.equal(
  plan.projects[0].document.activeCameraId,
  plan.projects[0].idMaps.objects[sourceDocument.activeCameraId],
);

const mappedResult = plan.targetNodes.find((node) => node.id === plan.graphNodeIdMap["capture-result"]);
assert.ok(mappedResult);
assert.equal(
  mappedResult.data.directorCapture.sourceNodeId,
  plan.graphNodeIdMap["director-a"],
);
assert.equal(
  mappedResult.data.directorCapture.edgeId,
  plan.graphEdgeIdMap["edge-a-result"],
);
assert.equal(
  mappedResult.data.directorCapture.captureId,
  plan.projects[0].idMaps.captures["capture-source"],
);

assert.deepEqual({ sourceDocument, sourceNodes, sourceEdges }, beforeSource);

const nonPortableDocument = structuredClone(sourceDocument);
nonPortableDocument.resourceRefs[0] = {
  ...nonPortableDocument.resourceRefs[0],
  source: "local",
  locator: "local://session-only",
};
const nonPortable = planDirectorWholeProjectDuplicate({
  sourceCanvasId,
  targetCanvasId,
  sourceNodes: sourceNodes.slice(0, 1),
  sourceEdges: [],
  projects: [
    {
      sourceOwner: ownerA,
      sourceDocument: nonPortableDocument,
      sourceLifecycle: "CLOSED",
      sourcePersistenceDisposition: "RESTORED",
    },
  ],
  createProjectId: deterministicFactory,
  createEntityId: deterministicFactory,
  createGraphNodeId: deterministicFactory,
  createGraphEdgeId: deterministicFactory,
  createFreshDocument: makeDocument,
});
assert.equal(nonPortable.ok, false);
if (nonPortable.ok) throw new Error("non-portable resource unexpectedly accepted");
assert.equal(nonPortable.reason, "DUPLICATE_NONPORTABLE_RESOURCE");

const rejectedMissing = planDirectorWholeProjectDuplicate({
  sourceCanvasId,
  targetCanvasId,
  sourceNodes: sourceNodes.slice(0, 1),
  sourceEdges: [],
  projects: [
    {
      sourceOwner: ownerA,
      sourceDocument: null,
      sourceLifecycle: null,
      sourcePersistenceDisposition: "REJECTED",
    },
  ],
  createProjectId: deterministicFactory,
  createEntityId: deterministicFactory,
  createGraphNodeId: deterministicFactory,
  createGraphEdgeId: deterministicFactory,
  createFreshDocument: makeDocument,
});
assert.equal(rejectedMissing.ok, false);
if (rejectedMissing.ok) throw new Error("rejected source unexpectedly accepted");
assert.equal(rejectedMissing.reason, "DUPLICATE_SOURCE_DOCUMENT_INVALID");

console.log(
  JSON.stringify({
    batch: 79,
    status: "PASS",
    scenarios: {
      fullDocumentTwoPassMap: true,
      multipleOwners: true,
      graphProvenanceRewrite: true,
      freshMissingDocument: true,
      nonPortableResourceReject: true,
      rejectedSourceZeroPlan: true,
      inputIsolation: true,
    },
    targetProjectCount: plan.projects.length,
    mappedObjectCount: Object.keys(plan.projects[0].idMaps.objects).length,
    mappedTrackCount: Object.keys(plan.projects[0].idMaps.tracks).length,
    mappedCaptureCount: Object.keys(plan.projects[0].idMaps.captures).length,
  }),
);
