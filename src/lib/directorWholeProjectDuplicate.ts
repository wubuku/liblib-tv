import type { Edge, Node } from "@xyflow/react";
import {
  decodeDirectorProjectDocument,
  normalizeDirectorProjectDocument,
  type DirectorCaptureDescriptorV1,
  type DirectorGroupDocumentV1,
  type DirectorMotionPathAnchorDocumentV1,
  type DirectorMotionPathDocumentV1,
  type DirectorObjectDocumentV1,
  type DirectorProjectDocumentV1,
  type DirectorProjectOwnerV1,
  type DirectorResourceReferenceV1,
  type DirectorTimelineTrackDocumentV1,
} from "./directorProjectDocument.ts";
import {
  isSameDirectorProjectOwner,
  type DirectorProjectLifecycle,
} from "./directorProjectRegistry.ts";

export type DirectorWholeProjectEntityKind =
  | "graph-node"
  | "graph-edge"
  | "project"
  | "object"
  | "group"
  | "track"
  | "keyframe"
  | "path"
  | "anchor"
  | "resource"
  | "capture";

export interface DirectorWholeProjectIdFactoryInput {
  kind: DirectorWholeProjectEntityKind;
  sourceId: string;
  projectOrdinal: number;
  index: number;
}

export type DirectorWholeProjectIdFactory = (
  input: DirectorWholeProjectIdFactoryInput,
) => string;

export type DirectorDuplicatePersistenceDisposition =
  | "MISSING"
  | "RESTORED"
  | "REJECTED"
  | "UNAVAILABLE";

export interface DirectorWholeProjectSourceInput {
  sourceOwner: DirectorProjectOwnerV1;
  targetSourceNodeId?: string;
  sourceDocument: unknown | null;
  sourceLifecycle?: DirectorProjectLifecycle | null;
  sourcePersistenceDisposition?: DirectorDuplicatePersistenceDisposition;
}

export interface DirectorWholeProjectDuplicateInput {
  sourceCanvasId: string;
  targetCanvasId: string;
  sourceNodes: readonly Node[];
  sourceEdges: readonly Edge[];
  sourceViewport?: { x: number; y: number; zoom: number };
  projects: readonly DirectorWholeProjectSourceInput[];
  createProjectId: DirectorWholeProjectIdFactory;
  createEntityId: DirectorWholeProjectIdFactory;
  createGraphNodeId: DirectorWholeProjectIdFactory;
  createGraphEdgeId: DirectorWholeProjectIdFactory;
  createFreshDocument: (
    projectId: string,
    owner: DirectorProjectOwnerV1,
  ) => DirectorProjectDocumentV1;
}

export type DirectorWholeProjectDuplicateFailureReason =
  | "DUPLICATE_SOURCE_CANVAS_MISSING"
  | "DUPLICATE_SOURCE_DIRECTOR_MISSING"
  | "DUPLICATE_SOURCE_CANVAS_MISMATCH"
  | "DUPLICATE_SOURCE_TOMBSTONED"
  | "DUPLICATE_SOURCE_DOCUMENT_INVALID"
  | "DUPLICATE_REFERENCE_UNMODELED"
  | "DUPLICATE_GRAPH_REFERENCE_UNMODELED"
  | "DUPLICATE_NONPORTABLE_RESOURCE"
  | "DUPLICATE_RESOURCE_CONFLICT"
  | "DUPLICATE_IDENTITY_ALLOCATION_FAILED";

export interface DirectorWholeProjectIdMaps {
  objects: Record<string, string>;
  groups: Record<string, string>;
  tracks: Record<string, string>;
  keyframes: Record<string, string>;
  paths: Record<string, string>;
  anchors: Record<string, string>;
  resources: Record<string, string>;
  captures: Record<string, string>;
}

export interface DirectorWholeProjectCopyPlan {
  sourceOwner: DirectorProjectOwnerV1;
  targetOwner: DirectorProjectOwnerV1;
  projectId: string;
  generation: 1;
  document: DirectorProjectDocumentV1;
  idMaps: DirectorWholeProjectIdMaps;
  sourceWasFresh: boolean;
  aliasedResourceIds: string[];
  copiedCaptureIds: string[];
}

export interface DirectorWholeProjectDuplicatePlan {
  sourceCanvasId: string;
  targetCanvasId: string;
  targetViewport: { x: number; y: number; zoom: number };
  graphNodeIdMap: Record<string, string>;
  graphEdgeIdMap: Record<string, string>;
  targetNodes: Node[];
  targetEdges: Edge[];
  projects: DirectorWholeProjectCopyPlan[];
}

export type DirectorWholeProjectDuplicateResult =
  | {
      ok: true;
      plan: DirectorWholeProjectDuplicatePlan;
    }
  | {
      ok: false;
      reason: DirectorWholeProjectDuplicateFailureReason;
      sourceNodeId: string | null;
    };

type UnknownRecord = Record<string, unknown>;
type DirectorTuple3 = [number, number, number];

interface ProjectMaps {
  objectMap: Map<string, string>;
  groupMap: Map<string, string>;
  trackMap: Map<string, string>;
  keyframeMap: Map<string, string>;
  pathMap: Map<string, string>;
  anchorMap: Map<string, string>;
  resourceMap: Map<string, string>;
  captureMap: Map<string, string>;
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function cloneOwner(owner: DirectorProjectOwnerV1): DirectorProjectOwnerV1 {
  return {
    route: "libtv",
    canvasId: owner.canvasId,
    sourceNodeId: owner.sourceNodeId,
  };
}

function cloneTuple3(value: DirectorTuple3): DirectorTuple3 {
  return [...value];
}

function cloneNode(node: Node): Node {
  const cloned: Node = {
    ...node,
    position: { ...node.position },
    style: node.style ? { ...node.style } : node.style,
    data: isRecord(node.data) ? { ...node.data } : {},
  };
  delete cloned.selected;
  delete cloned.measured;
  delete cloned.dragging;
  delete cloned.resizing;
  return cloned;
}

function cloneEdge(edge: Edge): Edge {
  const cloned = { ...edge };
  delete cloned.selected;
  return cloned;
}

function recordFromMap(map: Map<string, string>): Record<string, string> {
  return Object.fromEntries([...map.entries()].sort(([left], [right]) =>
    left.localeCompare(right),
  ));
}

function isEphemeralLocator(resource: DirectorResourceReferenceV1): boolean {
  return /^(blob:|data:|objecturl:|memory:)/i.test(resource.locator);
}

function fail(
  reason: DirectorWholeProjectDuplicateFailureReason,
  sourceNodeId: string | null,
): DirectorWholeProjectDuplicateResult {
  return { ok: false, reason, sourceNodeId };
}

function allocateId(
  factory: DirectorWholeProjectIdFactory,
  input: DirectorWholeProjectIdFactoryInput,
  used: Set<string>,
): string | null {
  const value = factory(input);
  if (
    typeof value !== "string" ||
    value.trim().length === 0 ||
    used.has(value) ||
    value === input.sourceId
  ) {
    return null;
  }
  used.add(value);
  return value;
}

function mapNullable(
  map: Map<string, string>,
  value: string | null,
): string | null {
  return value === null ? null : map.get(value) ?? null;
}

function mapRequired(
  map: Map<string, string>,
  value: string,
): string | null {
  return map.get(value) ?? null;
}

function mapAnchor(
  anchor: DirectorMotionPathAnchorDocumentV1,
  map: Map<string, string>,
): DirectorMotionPathAnchorDocumentV1 | null {
  const id = mapRequired(map, anchor.id);
  if (!id) return null;
  return {
    ...anchor,
    id,
    position: cloneTuple3(anchor.position),
    handleIn: cloneTuple3(anchor.handleIn),
    handleOut: cloneTuple3(anchor.handleOut),
  };
}

function mapPath(
  path: DirectorMotionPathDocumentV1,
  maps: ProjectMaps,
): DirectorMotionPathDocumentV1 | null {
  const id = mapRequired(maps.pathMap, path.id);
  const objectId = mapRequired(maps.objectMap, path.objectId);
  if (!id || !objectId) return null;
  const initialAnchors = path.initialAnchors.map((anchor) =>
    mapAnchor(anchor, maps.anchorMap),
  );
  const anchors = path.anchors.map((anchor) =>
    mapAnchor(anchor, maps.anchorMap),
  );
  if (initialAnchors.some((anchor) => !anchor) || anchors.some((anchor) => !anchor)) {
    return null;
  }
  return {
    ...path,
    id,
    objectId,
    pivot: cloneTuple3(path.pivot),
    transform: {
      position: cloneTuple3(path.transform.position),
      rotation: cloneTuple3(path.transform.rotation),
      scale: cloneTuple3(path.transform.scale),
    },
    initialAnchors: initialAnchors as DirectorMotionPathAnchorDocumentV1[],
    anchors: anchors as DirectorMotionPathAnchorDocumentV1[],
  };
}

function mapObject(
  object: DirectorObjectDocumentV1,
  maps: ProjectMaps,
): DirectorObjectDocumentV1 | null {
  const id = mapRequired(maps.objectMap, object.id);
  if (!id) return null;
  const camera = object.camera
    ? {
        ...object.camera,
        target: cloneTuple3(object.camera.target),
        followOffset: cloneTuple3(object.camera.followOffset),
        lookAtObjectId: mapNullable(
          maps.objectMap,
          object.camera.lookAtObjectId,
        ),
        followTargetId: mapNullable(
          maps.objectMap,
          object.camera.followTargetId,
        ),
      }
    : null;
  if (
    object.camera &&
    ((object.camera.lookAtObjectId !== null && camera?.lookAtObjectId === null) ||
      (object.camera.followTargetId !== null &&
        camera?.followTargetId === null))
  ) {
    return null;
  }
  return {
    ...object,
    id,
    transform: {
      position: cloneTuple3(object.transform.position),
      rotation: cloneTuple3(object.transform.rotation),
      scale: cloneTuple3(object.transform.scale),
    },
    assetRefId: mapNullable(maps.resourceMap, object.assetRefId),
    characterRig: object.characterRig
      ? {
          posePresetId: object.characterRig.posePresetId,
          controls: { ...object.characterRig.controls },
        }
      : null,
    camera,
  };
}

function mapGroup(
  group: DirectorGroupDocumentV1,
  maps: ProjectMaps,
): DirectorGroupDocumentV1 | null {
  const id = mapRequired(maps.groupMap, group.id);
  if (!id) return null;
  const characterIds = group.characterIds.map((value) =>
    mapRequired(maps.objectMap, value),
  );
  if (characterIds.some((value) => !value)) return null;
  return {
    ...group,
    id,
    characterIds: characterIds as string[],
    crowd: group.crowd ? { ...group.crowd } : null,
  };
}

function mapTrack(
  track: DirectorTimelineTrackDocumentV1,
  maps: ProjectMaps,
): DirectorTimelineTrackDocumentV1 | null {
  const id = mapRequired(maps.trackMap, track.id);
  const objectId =
    track.kind === "group"
      ? mapRequired(maps.groupMap, track.objectId)
      : mapRequired(maps.objectMap, track.objectId);
  const motionPathId = mapNullable(maps.pathMap, track.motionPathId);
  if (!id || !objectId) return null;
  if (track.motionPathId !== null && motionPathId === null) return null;
  const keyframes = track.keyframes.map((keyframe) => {
    const keyframeId = mapRequired(maps.keyframeMap, keyframe.id);
    return keyframeId ? { ...keyframe, id: keyframeId } : null;
  });
  if (keyframes.some((keyframe) => !keyframe)) return null;
  const base = {
    ...track,
    id,
    objectId,
    motionPathId,
    speedCurve: {
      ...track.speedCurve,
      control1: [...track.speedCurve.control1] as [number, number],
      control2: [...track.speedCurve.control2] as [number, number],
    },
  };
  if (track.kind !== "group") {
    return {
      ...base,
      keyframes: keyframes as typeof track.keyframes,
    } as DirectorTimelineTrackDocumentV1;
  }
  const groupId = mapRequired(maps.groupMap, track.groupId);
  if (!groupId) return null;
  const memberOffsets: Record<string, DirectorTuple3> = {};
  for (const [memberId, offset] of Object.entries(track.memberOffsets)) {
    const mappedMemberId = mapRequired(maps.objectMap, memberId);
    if (!mappedMemberId) return null;
    memberOffsets[mappedMemberId] = cloneTuple3(offset);
  }
  return {
    ...base,
    kind: "group",
    groupId,
    memberOffsets,
    keyframes: keyframes as typeof track.keyframes,
  };
}

function mapCapture(
  capture: DirectorCaptureDescriptorV1,
  maps: ProjectMaps,
): DirectorCaptureDescriptorV1 | null {
  const id = mapRequired(maps.captureMap, capture.id);
  if (!id) return null;
  const cameraId = mapNullable(maps.objectMap, capture.cameraId);
  const resourceRefId = mapNullable(maps.resourceMap, capture.resourceRefId);
  if (
    (capture.cameraId !== null && cameraId === null) ||
    (capture.resourceRefId !== null && resourceRefId === null)
  ) {
    return null;
  }
  return { ...capture, id, cameraId, resourceRefId };
}

function rewriteDirectorLinkedData(
  data: Record<string, unknown>,
  targetNodeId: string,
  graphNodeMap: Map<string, string>,
  graphEdgeMap: Map<string, string>,
  projectBySourceNode: Map<string, ProjectMaps>,
): Record<string, unknown> | null {
  const next = { ...data };
  const rewriteCapture = next.directorCapture;
  if (isRecord(rewriteCapture)) {
    const sourceNodeId =
      typeof rewriteCapture.sourceNodeId === "string"
        ? rewriteCapture.sourceNodeId
        : null;
    const sourceProject = sourceNodeId
      ? projectBySourceNode.get(sourceNodeId)
      : undefined;
    if (!sourceNodeId || !sourceProject) return null;
    const mappedSourceNodeId = mapRequired(graphNodeMap, sourceNodeId);
    const mappedEdgeId =
      typeof rewriteCapture.edgeId === "string"
        ? mapRequired(graphEdgeMap, rewriteCapture.edgeId)
        : null;
    const captureId =
      typeof rewriteCapture.captureId === "string"
        ? mapRequired(sourceProject.captureMap, rewriteCapture.captureId)
        : null;
    const sourceCameraId =
      rewriteCapture.cameraId === null
        ? null
        : typeof rewriteCapture.cameraId === "string"
          ? mapRequired(sourceProject.objectMap, rewriteCapture.cameraId)
          : null;
    if (
      !mappedSourceNodeId ||
      !mappedEdgeId ||
      !captureId ||
      (rewriteCapture.cameraId !== null && !sourceCameraId)
    ) {
      return null;
    }
    next.directorCapture = {
      ...rewriteCapture,
      sourceNodeId: mappedSourceNodeId,
      edgeId: mappedEdgeId,
      captureId,
      cameraId: sourceCameraId,
    };
  }

  const rewriteExport = next.directorAnimationExport;
  if (isRecord(rewriteExport)) {
    const sourceNodeId =
      typeof rewriteExport.sourceNodeId === "string"
        ? rewriteExport.sourceNodeId
        : null;
    const sourceProject = sourceNodeId
      ? projectBySourceNode.get(sourceNodeId)
      : undefined;
    const mappedSourceNodeId = sourceNodeId
      ? mapRequired(graphNodeMap, sourceNodeId)
      : null;
    const mappedEdgeId =
      typeof rewriteExport.edgeId === "string"
        ? mapRequired(graphEdgeMap, rewriteExport.edgeId)
        : null;
    const sourceCameraId =
      rewriteExport.cameraId === null
        ? null
        : typeof rewriteExport.cameraId === "string" && sourceProject
          ? mapRequired(sourceProject.objectMap, rewriteExport.cameraId)
          : null;
    if (
      !sourceProject ||
      !mappedSourceNodeId ||
      !mappedEdgeId ||
      (rewriteExport.cameraId !== null && !sourceCameraId)
    ) {
      return null;
    }
    next.directorAnimationExport = {
      ...rewriteExport,
      exportId: `${targetNodeId}-export`,
      sourceNodeId: mappedSourceNodeId,
      edgeId: mappedEdgeId,
      cameraId: sourceCameraId,
    };
  }
  return next;
}

function rewriteProjectDocument(
  source: DirectorProjectDocumentV1,
  targetOwner: DirectorProjectOwnerV1,
  projectId: string,
  maps: ProjectMaps,
): DirectorProjectDocumentV1 | null {
  const objects = source.objects.map((object) => mapObject(object, maps));
  const groups = source.groups.map((group) => mapGroup(group, maps));
  const tracks = source.timeline.tracks.map((track) => mapTrack(track, maps));
  const motionPaths = source.timeline.motionPaths.map((path) =>
    mapPath(path, maps),
  );
  const captures = source.captureDescriptors
    .filter((capture) => capture.resourceRefId !== null)
    .map((capture) => mapCapture(capture, maps));
  if (
    objects.some((object) => !object) ||
    groups.some((group) => !group) ||
    tracks.some((track) => !track) ||
    motionPaths.some((path) => !path) ||
    captures.some((capture) => !capture)
  ) {
    return null;
  }
  const activeCameraId = mapRequired(maps.objectMap, source.activeCameraId);
  if (!activeCameraId) return null;
  const resources = source.resourceRefs.map((resource) => {
    const id = mapRequired(maps.resourceMap, resource.id);
    return id ? { ...resource, id } : null;
  });
  if (resources.some((resource) => !resource)) return null;
  return {
    schemaVersion: source.schemaVersion,
    projectId,
    owner: cloneOwner(targetOwner),
    scene: {
      ...source.scene,
    },
    objects: objects as DirectorObjectDocumentV1[],
    groups: groups as DirectorGroupDocumentV1[],
    activeCameraId,
    timeline: {
      ...source.timeline,
      tracks: tracks as DirectorTimelineTrackDocumentV1[],
      motionPaths: motionPaths as DirectorMotionPathDocumentV1[],
    },
    outputPreferences: { ...source.outputPreferences },
    resourceRefs: resources as DirectorResourceReferenceV1[],
    captureDescriptors: captures as DirectorCaptureDescriptorV1[],
  };
}

function createMaps(
  source: DirectorProjectDocumentV1,
  projectOrdinal: number,
  createEntityId: DirectorWholeProjectIdFactory,
): {
  maps: ProjectMaps | null;
  reason: DirectorWholeProjectDuplicateFailureReason | null;
} {
  const used = new Set<string>();
  const create = (
    kind: DirectorWholeProjectEntityKind,
    sourceId: string,
    index: number,
  ): string | null =>
    allocateId(createEntityId, { kind, sourceId, projectOrdinal, index }, used);
  const objectMap = new Map<string, string>();
  const groupMap = new Map<string, string>();
  const trackMap = new Map<string, string>();
  const keyframeMap = new Map<string, string>();
  const pathMap = new Map<string, string>();
  const anchorMap = new Map<string, string>();
  const resourceMap = new Map<string, string>();
  const captureMap = new Map<string, string>();

  source.resourceRefs.forEach((resource, index) => {
    if (resource.source === "local" || isEphemeralLocator(resource)) return;
    const id = create("resource", resource.id, index);
    if (id) resourceMap.set(resource.id, id);
  });
  if (source.resourceRefs.some((resource) => !resourceMap.has(resource.id))) {
    return { maps: null, reason: "DUPLICATE_NONPORTABLE_RESOURCE" };
  }

  source.objects.forEach((object, index) => {
    const id = create("object", object.id, index);
    if (id) objectMap.set(object.id, id);
  });
  source.groups.forEach((group, index) => {
    const id = create("group", group.id, index);
    if (id) groupMap.set(group.id, id);
  });
  source.timeline.tracks.forEach((track, index) => {
    const id = create("track", track.id, index);
    if (id) trackMap.set(track.id, id);
    track.keyframes.forEach((keyframe, keyframeIndex) => {
      const keyframeId = create("keyframe", keyframe.id, keyframeIndex);
      if (keyframeId) keyframeMap.set(keyframe.id, keyframeId);
    });
  });
  source.timeline.motionPaths.forEach((path, index) => {
    const id = create("path", path.id, index);
    if (id) pathMap.set(path.id, id);
    [...path.initialAnchors, ...path.anchors].forEach((anchor, anchorIndex) => {
      if (anchorMap.has(anchor.id)) return;
      const anchorId = create("anchor", anchor.id, anchorIndex);
      if (anchorId) anchorMap.set(anchor.id, anchorId);
    });
  });
  source.captureDescriptors.forEach((capture, index) => {
    if (capture.resourceRefId === null) return;
    const id = create("capture", capture.id, index);
    if (id) captureMap.set(capture.id, id);
  });

  const required = [
    [objectMap, source.objects.map((item) => item.id)],
    [groupMap, source.groups.map((item) => item.id)],
    [trackMap, source.timeline.tracks.map((item) => item.id)],
    [
      keyframeMap,
      source.timeline.tracks.flatMap((track) =>
        track.keyframes.map((item) => item.id),
      ),
    ],
    [pathMap, source.timeline.motionPaths.map((item) => item.id)],
    [
      anchorMap,
      source.timeline.motionPaths.flatMap((path) => [
        ...path.initialAnchors,
        ...path.anchors,
      ].map((item) => item.id)),
    ],
    [
      captureMap,
      source.captureDescriptors
        .filter((item) => item.resourceRefId !== null)
        .map((item) => item.id),
    ],
  ] as const;
  if (required.some(([map, ids]) => ids.some((id) => !map.has(id)))) {
    return { maps: null, reason: "DUPLICATE_IDENTITY_ALLOCATION_FAILED" };
  }

  return {
    maps: {
      objectMap,
      groupMap,
      trackMap,
      keyframeMap,
      pathMap,
      anchorMap,
      resourceMap,
      captureMap,
    },
    reason: null,
  };
}

export function planDirectorWholeProjectDuplicate(
  input: DirectorWholeProjectDuplicateInput,
): DirectorWholeProjectDuplicateResult {
  if (
    input.sourceCanvasId.trim().length === 0 ||
    input.targetCanvasId.trim().length === 0 ||
    input.sourceCanvasId === input.targetCanvasId
  ) {
    return fail("DUPLICATE_SOURCE_CANVAS_MISSING", null);
  }

  const sourceNodeIds = new Set(input.sourceNodes.map((node) => node.id));
  const graphNodeMap = new Map<string, string>();
  const graphEdgeMap = new Map<string, string>();
  const graphNodeIds = new Set<string>();
  const graphEdgeIds = new Set<string>();
  for (const [index, node] of input.sourceNodes.entries()) {
    const id = allocateId(
      input.createGraphNodeId,
      { kind: "graph-node", sourceId: node.id, projectOrdinal: -1, index },
      graphNodeIds,
    );
    if (!id) return fail("DUPLICATE_IDENTITY_ALLOCATION_FAILED", null);
    graphNodeMap.set(node.id, id);
  }
  for (const [index, edge] of input.sourceEdges.entries()) {
    if (
      !sourceNodeIds.has(edge.source) ||
      !sourceNodeIds.has(edge.target)
    ) {
      return fail("DUPLICATE_GRAPH_REFERENCE_UNMODELED", null);
    }
    const id = allocateId(
      input.createGraphEdgeId,
      { kind: "graph-edge", sourceId: edge.id, projectOrdinal: -1, index },
      graphEdgeIds,
    );
    if (!id) return fail("DUPLICATE_IDENTITY_ALLOCATION_FAILED", null);
    graphEdgeMap.set(edge.id, id);
  }

  const projectBySourceNodeInput = new Map(
    input.projects.map((project) => [project.sourceOwner.sourceNodeId, project]),
  );
  if (projectBySourceNodeInput.size !== input.projects.length) {
    return fail("DUPLICATE_IDENTITY_ALLOCATION_FAILED", null);
  }
  for (const node of input.sourceNodes) {
    if (node.type === "script-execution" && !projectBySourceNodeInput.has(node.id)) {
      return fail("DUPLICATE_SOURCE_DIRECTOR_MISSING", node.id);
    }
  }
  for (const project of input.projects) {
    if (
      project.sourceOwner.canvasId !== input.sourceCanvasId ||
      !sourceNodeIds.has(project.sourceOwner.sourceNodeId) ||
      input.sourceNodes.find(
        (node) => node.id === project.sourceOwner.sourceNodeId,
      )?.type !== "script-execution"
    ) {
      return fail("DUPLICATE_SOURCE_CANVAS_MISMATCH", project.sourceOwner.sourceNodeId);
    }
  }

  const usedProjectIds = new Set<string>();
  const projects: DirectorWholeProjectCopyPlan[] = [];
  const projectMaps = new Map<string, ProjectMaps>();
  for (const [projectOrdinal, sourceProject] of input.projects.entries()) {
    const sourceOwner = cloneOwner(sourceProject.sourceOwner);
    if (sourceProject.sourceLifecycle === "TOMBSTONED") {
      return fail("DUPLICATE_SOURCE_TOMBSTONED", sourceOwner.sourceNodeId);
    }
    const targetSourceNodeId =
      sourceProject.targetSourceNodeId ??
      graphNodeMap.get(sourceOwner.sourceNodeId);
    if (
      !targetSourceNodeId ||
      targetSourceNodeId !== graphNodeMap.get(sourceOwner.sourceNodeId)
    ) {
      return fail("DUPLICATE_SOURCE_DIRECTOR_MISSING", sourceOwner.sourceNodeId);
    }
    const targetOwner: DirectorProjectOwnerV1 = {
      route: "libtv",
      canvasId: input.targetCanvasId,
      sourceNodeId: targetSourceNodeId,
    };
    const projectId = input.createProjectId({
      kind: "project",
      sourceId: sourceProject.sourceDocument
        && isRecord(sourceProject.sourceDocument)
        && typeof sourceProject.sourceDocument.projectId === "string"
        ? sourceProject.sourceDocument.projectId
        : sourceOwner.sourceNodeId,
      projectOrdinal,
      index: projectOrdinal,
    });
    if (
      typeof projectId !== "string" ||
      projectId.trim().length === 0 ||
      usedProjectIds.has(projectId)
    ) {
      return fail("DUPLICATE_IDENTITY_ALLOCATION_FAILED", sourceOwner.sourceNodeId);
    }
    usedProjectIds.add(projectId);

    if (sourceProject.sourceDocument === null) {
      if (
        sourceProject.sourcePersistenceDisposition &&
        sourceProject.sourcePersistenceDisposition !== "MISSING"
      ) {
        return fail("DUPLICATE_SOURCE_DOCUMENT_INVALID", sourceOwner.sourceNodeId);
      }
      let document: DirectorProjectDocumentV1;
      try {
        document = normalizeDirectorProjectDocument(
          input.createFreshDocument(projectId, targetOwner),
        );
      } catch {
        return fail("DUPLICATE_SOURCE_DOCUMENT_INVALID", sourceOwner.sourceNodeId);
      }
      if (
        document.projectId !== projectId ||
        !isSameDirectorProjectOwner(document.owner, targetOwner)
      ) {
        return fail("DUPLICATE_SOURCE_DOCUMENT_INVALID", sourceOwner.sourceNodeId);
      }
      const copy: DirectorWholeProjectCopyPlan = {
        sourceOwner,
        targetOwner,
        projectId,
        generation: 1,
        document,
        idMaps: {
          objects: {},
          groups: {},
          tracks: {},
          keyframes: {},
          paths: {},
          anchors: {},
          resources: {},
          captures: {},
        },
        sourceWasFresh: true,
        aliasedResourceIds: [],
        copiedCaptureIds: [],
      };
      projects.push(copy);
      projectMaps.set(sourceOwner.sourceNodeId, {
        objectMap: new Map(),
        groupMap: new Map(),
        trackMap: new Map(),
        keyframeMap: new Map(),
        pathMap: new Map(),
        anchorMap: new Map(),
        resourceMap: new Map(),
        captureMap: new Map(),
      });
      continue;
    }

    const decoded = decodeDirectorProjectDocument(sourceProject.sourceDocument);
    if (
      !decoded.ok ||
      !isSameDirectorProjectOwner(decoded.document.owner, sourceOwner)
    ) {
      return fail("DUPLICATE_SOURCE_DOCUMENT_INVALID", sourceOwner.sourceNodeId);
    }
    const createdMaps = createMaps(
      decoded.document,
      projectOrdinal,
      input.createEntityId,
    );
    if (!createdMaps.maps || createdMaps.reason) {
      return fail(createdMaps.reason ?? "DUPLICATE_IDENTITY_ALLOCATION_FAILED", sourceOwner.sourceNodeId);
    }
    const copyShell = {
      sourceOwner,
      targetOwner,
      projectId,
      generation: 1 as const,
      document: decoded.document,
      idMaps: {
        objects: recordFromMap(createdMaps.maps.objectMap),
        groups: recordFromMap(createdMaps.maps.groupMap),
        tracks: recordFromMap(createdMaps.maps.trackMap),
        keyframes: recordFromMap(createdMaps.maps.keyframeMap),
        paths: recordFromMap(createdMaps.maps.pathMap),
        anchors: recordFromMap(createdMaps.maps.anchorMap),
        resources: recordFromMap(createdMaps.maps.resourceMap),
        captures: recordFromMap(createdMaps.maps.captureMap),
      },
      sourceWasFresh: false,
      aliasedResourceIds: decoded.document.resourceRefs.map(
        (resource) => resource.id,
      ),
      copiedCaptureIds: decoded.document.captureDescriptors
        .filter((capture) => capture.resourceRefId !== null)
        .map((capture) => capture.id),
    } satisfies DirectorWholeProjectCopyPlan;
    const maps = {
      ...createdMaps.maps,
    };
    const document = rewriteProjectDocument(
      decoded.document,
      targetOwner,
      projectId,
      maps,
    );
    if (!document) {
      return fail("DUPLICATE_REFERENCE_UNMODELED", sourceOwner.sourceNodeId);
    }
    const normalized = decodeDirectorProjectDocument(document);
    if (
      !normalized.ok ||
      normalized.document.projectId !== projectId ||
      !isSameDirectorProjectOwner(normalized.document.owner, targetOwner)
    ) {
      return fail("DUPLICATE_REFERENCE_UNMODELED", sourceOwner.sourceNodeId);
    }
    copyShell.document = normalized.document;
    projects.push(copyShell);
    projectMaps.set(sourceOwner.sourceNodeId, maps);
  }

  const targetNodes: Node[] = [];
  for (const sourceNode of input.sourceNodes) {
    const targetNode = cloneNode(sourceNode);
    const targetNodeId = graphNodeMap.get(sourceNode.id);
    if (!targetNodeId) return fail("DUPLICATE_IDENTITY_ALLOCATION_FAILED", null);
    targetNode.id = targetNodeId;
    if (sourceNode.parentId) {
      const parentId = graphNodeMap.get(sourceNode.parentId);
      if (parentId) targetNode.parentId = parentId;
      else delete targetNode.parentId;
    }
    if (isRecord(targetNode.data)) {
      const rewrittenData = rewriteDirectorLinkedData(
        targetNode.data,
        targetNodeId,
        graphNodeMap,
        graphEdgeMap,
        projectMaps,
      );
      if (!rewrittenData) {
        return fail("DUPLICATE_REFERENCE_UNMODELED", sourceNode.id);
      }
      targetNode.data = rewrittenData;
    }
    targetNodes.push(targetNode);
  }

  const targetEdges: Edge[] = input.sourceEdges.map((sourceEdge) => {
    const targetEdge = cloneEdge(sourceEdge);
    targetEdge.id = graphEdgeMap.get(sourceEdge.id) ?? sourceEdge.id;
    targetEdge.source = graphNodeMap.get(sourceEdge.source) ?? sourceEdge.source;
    targetEdge.target = graphNodeMap.get(sourceEdge.target) ?? sourceEdge.target;
    return targetEdge;
  });

  return {
    ok: true,
    plan: {
      sourceCanvasId: input.sourceCanvasId,
      targetCanvasId: input.targetCanvasId,
      targetViewport: { ...(input.sourceViewport ?? { x: 0, y: 0, zoom: 1 }) },
      graphNodeIdMap: recordFromMap(graphNodeMap),
      graphEdgeIdMap: recordFromMap(graphEdgeMap),
      targetNodes,
      targetEdges,
      projects,
    },
  };
}
