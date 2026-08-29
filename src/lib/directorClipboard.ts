import {
  decodeDirectorProjectDocument,
  normalizeDirectorProjectDocument,
  type DirectorCameraKeyframeDocumentV1,
  type DirectorGroupKeyframeDocumentV1,
  type DirectorMotionPathAnchorDocumentV1,
  type DirectorMotionPathDocumentV1,
  type DirectorObjectDocumentV1,
  type DirectorPoseKeyframeDocumentV1,
  type DirectorProjectDocumentV1,
  type DirectorResourceReferenceV1,
  type DirectorShotRecordV1,
  type DirectorTimelineTrackDocumentV1,
  type DirectorTransformDocumentV1,
  type DirectorTransformKeyframeDocumentV1,
} from "./directorProjectDocument.ts";

export const DIRECTOR_CLIPBOARD_SCHEMA_VERSION = 1 as const;
export const DIRECTOR_CLIPBOARD_PASTE_OFFSET = 0.6;

export interface DirectorClipboardSelectionV1 {
  selectedObjectIds: string[];
  selectedGroupId: string | null;
}

export interface DirectorClipboardPacketV1 {
  schemaVersion: typeof DIRECTOR_CLIPBOARD_SCHEMA_VERSION;
  sourceProjectId: string;
  selection: DirectorClipboardSelectionV1;
  objects: DirectorObjectDocumentV1[];
  groups: DirectorProjectDocumentV1["groups"];
  shots: DirectorShotRecordV1[];
  timeline: {
    tracks: DirectorTimelineTrackDocumentV1[];
    motionPaths: DirectorMotionPathDocumentV1[];
  };
  resourceRefs: DirectorResourceReferenceV1[];
}

export type DirectorClipboardFailureReason =
  | "EMPTY_SELECTION"
  | "INVALID_SELECTION"
  | "INVALID_PACKET"
  | "PROJECT_MISMATCH"
  | "RESOURCE_MISSING"
  | "RESOURCE_CONFLICT"
  | "IDENTITY_ALLOCATION_FAILED";

export type DirectorClipboardBuildResult =
  | {
      ok: true;
      packet: DirectorClipboardPacketV1;
    }
  | {
      ok: false;
      reason: DirectorClipboardFailureReason;
    };

export type DirectorClipboardEntityKind =
  | "object"
  | "group"
  | "track"
  | "path"
  | "keyframe"
  | "anchor"
  | "shot";

export type DirectorClipboardIdFactory = (input: {
  kind: DirectorClipboardEntityKind;
  sourceId: string;
  pasteOrdinal: number;
  index: number;
  attempt: number;
}) => string;

export interface DirectorClipboardPastePlan {
  document: DirectorProjectDocumentV1;
  selection: {
    selectedObjectId: string | null;
    selectedObjectIds: string[];
    selectedGroupId: string | null;
  };
  pastedTrackIds: string[];
  pastedMotionPathIds: string[];
  offset: number;
  idMaps: {
    objects: Record<string, string>;
    groups: Record<string, string>;
    tracks: Record<string, string>;
    paths: Record<string, string>;
    keyframes: Record<string, string>;
    anchors: Record<string, string>;
    shots: Record<string, string>;
  };
  aliasedResourceIds: string[];
}

export type DirectorClipboardPasteResult =
  | {
      ok: true;
      plan: DirectorClipboardPastePlan;
    }
  | {
      ok: false;
      reason: DirectorClipboardFailureReason;
    };

type UnknownRecord = Record<string, unknown>;

let directorClipboardIdentitySequence = 0;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(record: UnknownRecord, keys: string[]): boolean {
  const actual = Object.keys(record).sort();
  const expected = [...keys].sort();
  return (
    actual.length === expected.length &&
    actual.every((key, index) => key === expected[index])
  );
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string" && item.length > 0)
  );
}

function hasSameStringSet(left: string[], right: string[]): boolean {
  if (left.length !== right.length) return false;
  const rightSet = new Set(right);
  return rightSet.size === right.length && left.every((item) => rightSet.has(item));
}

function cloneTuple3(value: [number, number, number]): [number, number, number] {
  return [...value];
}

function offsetTuple3(
  value: [number, number, number],
  offset: number,
): [number, number, number] {
  return [
    Number((value[0] + offset).toFixed(6)),
    value[1],
    Number((value[2] + offset).toFixed(6)),
  ];
}

function cloneTransform(
  transform: DirectorTransformDocumentV1,
): DirectorTransformDocumentV1 {
  return {
    position: cloneTuple3(transform.position),
    rotation: cloneTuple3(transform.rotation),
    scale: cloneTuple3(transform.scale),
  };
}

function offsetTransform(
  transform: DirectorTransformDocumentV1,
  offset: number,
): DirectorTransformDocumentV1 {
  return {
    ...cloneTransform(transform),
    position: offsetTuple3(transform.position, offset),
  };
}

function defaultDirectorClipboardIdFactory(input: {
  kind: DirectorClipboardEntityKind;
  sourceId: string;
  pasteOrdinal: number;
  index: number;
  attempt: number;
}): string {
  directorClipboardIdentitySequence += 1;
  const sourceToken =
    input.sourceId.replace(/[^a-zA-Z0-9_-]+/g, "-").slice(-32) || "entity";
  return [
    "director",
    input.kind,
    "copy",
    sourceToken,
    Date.now(),
    input.pasteOrdinal,
    input.index,
    input.attempt,
    directorClipboardIdentitySequence,
  ].join("-");
}

function createValidationCamera(id: string): DirectorObjectDocumentV1 {
  return {
    id,
    name: "Clipboard validation camera",
    kind: "camera",
    primitive: "camera",
    color: "#000000",
    visible: false,
    locked: true,
    transform: {
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      scale: [1, 1, 1],
    },
    assetRefId: null,
    libraryCategoryId: null,
    libraryVisual: null,
    characterRig: null,
    camera: {
      fov: 45,
      target: [0, 0, 0],
      lookAtMode: "coordinate",
      lookAtObjectId: null,
      followTargetId: null,
      followOffset: [0, 0, 0],
      followView: "third-person",
    },
  };
}

export function validateDirectorClipboardPacket(
  input: unknown,
): DirectorClipboardBuildResult {
  if (!isRecord(input)) {
    return { ok: false, reason: "INVALID_PACKET" };
  }
  if (
    !hasExactKeys(input, [
      "schemaVersion",
      "sourceProjectId",
      "selection",
      "objects",
      "groups",
      "shots",
      "timeline",
      "resourceRefs",
    ]) ||
    input.schemaVersion !== DIRECTOR_CLIPBOARD_SCHEMA_VERSION ||
    typeof input.sourceProjectId !== "string" ||
    input.sourceProjectId.length === 0 ||
    !isRecord(input.selection) ||
    !hasExactKeys(input.selection, [
      "selectedObjectIds",
      "selectedGroupId",
    ]) ||
    !isStringArray(input.selection.selectedObjectIds) ||
    !(
      input.selection.selectedGroupId === null ||
      (typeof input.selection.selectedGroupId === "string" &&
        input.selection.selectedGroupId.length > 0)
    ) ||
    !Array.isArray(input.objects) ||
    !Array.isArray(input.groups) ||
    !Array.isArray(input.shots) ||
    !isRecord(input.timeline) ||
    !hasExactKeys(input.timeline, ["tracks", "motionPaths"]) ||
    !Array.isArray(input.timeline.tracks) ||
    !Array.isArray(input.timeline.motionPaths) ||
    !Array.isArray(input.resourceRefs)
  ) {
    return { ok: false, reason: "INVALID_PACKET" };
  }

  const rawObjectIds = new Set(
    input.objects.flatMap((value) => {
      if (!isRecord(value) || typeof value.id !== "string") return [];
      return [value.id];
    }),
  );
  let validationCameraId = "__director_clipboard_validation_camera__";
  while (rawObjectIds.has(validationCameraId)) {
    validationCameraId = `${validationCameraId}_`;
  }
  const rawCamera = input.objects.find(
    (value) =>
      isRecord(value) &&
      value.kind === "camera" &&
      typeof value.id === "string",
  );
  const activeCameraId =
    isRecord(rawCamera) && typeof rawCamera.id === "string"
      ? rawCamera.id
      : validationCameraId;
  const includesValidationCamera = activeCameraId === validationCameraId;
  const validationShot: DirectorShotRecordV1 = {
    id: "__director_clipboard_validation_shot__",
    name: "Clipboard validation shot",
    cameraId: validationCameraId,
    startTime: 0,
    endTime: 1_000_000_000,
    captureIds: [],
  };
  const decoded = decodeDirectorProjectDocument({
    schemaVersion: 1,
    projectId: input.sourceProjectId,
    owner: {
      route: "libtv",
      canvasId: "__director_clipboard_validation_canvas__",
      sourceNodeId: "__director_clipboard_validation_source__",
    },
    scene: {
      name: "Clipboard validation",
      backgroundColor: "#000000",
      groundColor: "#000000",
      showGround: false,
      showGrid: false,
    },
    objects: includesValidationCamera
      ? [...input.objects, createValidationCamera(validationCameraId)]
      : input.objects,
    groups: input.groups,
    shots: includesValidationCamera
      ? [...input.shots, validationShot]
      : input.shots,
    activeCameraId,
    timeline: {
      duration: 1_000_000_000,
      loop: false,
      autoKeyframe: false,
      tracks: input.timeline.tracks,
      motionPaths: input.timeline.motionPaths,
    },
    outputPreferences: {
      aspectRatio: "16:9",
    },
    resourceRefs: input.resourceRefs,
    captureDescriptors: [],
  });
  if (!decoded.ok) {
    return { ok: false, reason: "INVALID_PACKET" };
  }

  const selectedObjectIds = [...input.selection.selectedObjectIds];
  const selectedObjectSet = new Set(selectedObjectIds);
  if (
    selectedObjectSet.size !== selectedObjectIds.length ||
    selectedObjectIds.length === 0
  ) {
    return { ok: false, reason: "INVALID_SELECTION" };
  }
  const objects = decoded.document.objects.filter(
    (object) => object.id !== validationCameraId,
  );
  if (
    !hasSameStringSet(
      objects.map((object) => object.id),
      selectedObjectIds,
    )
  ) {
    return { ok: false, reason: "INVALID_SELECTION" };
  }

  const selectedGroupId = input.selection.selectedGroupId;
  if (selectedGroupId) {
    if (
      decoded.document.groups.length !== 1 ||
      decoded.document.groups[0].id !== selectedGroupId ||
      !hasSameStringSet(
        decoded.document.groups[0].characterIds,
        selectedObjectIds,
      )
    ) {
      return { ok: false, reason: "INVALID_SELECTION" };
    }
  } else if (decoded.document.groups.length > 0) {
    return { ok: false, reason: "INVALID_SELECTION" };
  }

  const resourceIds = new Set(
    objects.flatMap((object) =>
      object.assetRefId === null ? [] : [object.assetRefId],
    ),
  );
  if (
    !hasSameStringSet(
      decoded.document.resourceRefs.map((resource) => resource.id),
      [...resourceIds],
    )
  ) {
    return { ok: false, reason: "INVALID_PACKET" };
  }

  const packet: DirectorClipboardPacketV1 = {
    schemaVersion: DIRECTOR_CLIPBOARD_SCHEMA_VERSION,
    sourceProjectId: input.sourceProjectId,
    selection: {
      selectedObjectIds,
      selectedGroupId,
    },
    objects,
    groups: decoded.document.groups,
    shots: decoded.document.shots.filter(
      (shot) => shot.cameraId !== validationCameraId,
    ),
    timeline: {
      tracks: decoded.document.timeline.tracks,
      motionPaths: decoded.document.timeline.motionPaths,
    },
    resourceRefs: decoded.document.resourceRefs,
  };
  return { ok: true, packet };
}

export function buildDirectorClipboardPacket(input: {
  document: DirectorProjectDocumentV1;
  selection: DirectorClipboardSelectionV1;
}): DirectorClipboardBuildResult {
  let document: DirectorProjectDocumentV1;
  try {
    document = normalizeDirectorProjectDocument(input.document);
  } catch {
    return { ok: false, reason: "INVALID_PACKET" };
  }

  const selectedGroup = input.selection.selectedGroupId
    ? document.groups.find(
        (group) => group.id === input.selection.selectedGroupId,
      )
    : null;
  if (input.selection.selectedGroupId && !selectedGroup) {
    return { ok: false, reason: "INVALID_SELECTION" };
  }
  const requestedObjectIds = selectedGroup
    ? selectedGroup.characterIds
    : input.selection.selectedObjectIds;
  const selectedObjectIds = [
    ...new Set(
      requestedObjectIds.filter((objectId) =>
        document.objects.some((object) => object.id === objectId),
      ),
    ),
  ];
  if (selectedObjectIds.length === 0) {
    return { ok: false, reason: "EMPTY_SELECTION" };
  }

  const selectedObjectSet = new Set(selectedObjectIds);
  const objects = document.objects
    .filter((object) => selectedObjectSet.has(object.id))
    .map((object) => {
      if (!object.camera) return object;
      const lookAtObjectId =
        object.camera.lookAtObjectId &&
        selectedObjectSet.has(object.camera.lookAtObjectId)
          ? object.camera.lookAtObjectId
          : null;
      const followTargetId =
        object.camera.followTargetId &&
        selectedObjectSet.has(object.camera.followTargetId)
          ? object.camera.followTargetId
          : null;
      return {
        ...object,
        camera: {
          ...object.camera,
          target: cloneTuple3(object.camera.target),
          lookAtMode:
            object.camera.lookAtMode === "object" && lookAtObjectId === null
              ? ("coordinate" as const)
              : object.camera.lookAtMode,
          lookAtObjectId,
          followTargetId,
          followOffset: cloneTuple3(object.camera.followOffset),
        },
      };
    });
  const groups = selectedGroup ? [selectedGroup] : [];
  const tracks = document.timeline.tracks.filter((track) =>
    track.kind === "group"
      ? selectedGroup?.id === track.groupId
      : selectedObjectSet.has(track.objectId),
  );
  const motionPaths = document.timeline.motionPaths.filter((path) =>
    selectedObjectSet.has(path.objectId),
  );
  const shots = document.shots
    .filter((shot) => selectedObjectSet.has(shot.cameraId))
    .map((shot) => ({ ...shot, captureIds: [] }));
  const selectedResourceIds = new Set(
    objects.flatMap((object) =>
      object.assetRefId === null ? [] : [object.assetRefId],
    ),
  );
  const resourceRefs = document.resourceRefs.filter((resource) =>
    selectedResourceIds.has(resource.id),
  );

  return validateDirectorClipboardPacket({
    schemaVersion: DIRECTOR_CLIPBOARD_SCHEMA_VERSION,
    sourceProjectId: document.projectId,
    selection: {
      selectedObjectIds,
      selectedGroupId: selectedGroup?.id ?? null,
    },
    objects,
    groups,
    shots,
    timeline: {
      tracks,
      motionPaths,
    },
    resourceRefs,
  });
}

function allocateDirectorClipboardId(input: {
  kind: DirectorClipboardEntityKind;
  sourceId: string;
  pasteOrdinal: number;
  index: number;
  usedIds: Set<string>;
  factory: DirectorClipboardIdFactory;
}): string | null {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    const candidate = input.factory({
      kind: input.kind,
      sourceId: input.sourceId,
      pasteOrdinal: input.pasteOrdinal,
      index: input.index,
      attempt,
    });
    if (candidate.length > 0 && !input.usedIds.has(candidate)) {
      input.usedIds.add(candidate);
      return candidate;
    }
  }
  return null;
}

function allocateMap(input: {
  kind: DirectorClipboardEntityKind;
  sourceIds: string[];
  pasteOrdinal: number;
  usedIds: Set<string>;
  factory: DirectorClipboardIdFactory;
}): Map<string, string> | null {
  const map = new Map<string, string>();
  for (const [index, sourceId] of input.sourceIds.entries()) {
    const allocated = allocateDirectorClipboardId({
      ...input,
      sourceId,
      index,
    });
    if (!allocated) return null;
    map.set(sourceId, allocated);
  }
  return map;
}

function mapToRecord(map: Map<string, string>): Record<string, string> {
  return Object.fromEntries(map.entries());
}

function requireMappedId(map: Map<string, string>, sourceId: string): string {
  const mapped = map.get(sourceId);
  if (!mapped) {
    throw new Error(`Missing Director clipboard identity for ${sourceId}`);
  }
  return mapped;
}

function mapOptionalId(
  map: Map<string, string>,
  sourceId: string | null,
): string | null {
  return sourceId === null ? null : requireMappedId(map, sourceId);
}

function descriptorFingerprint(resource: DirectorResourceReferenceV1): string {
  return JSON.stringify(resource);
}

function remapObject(
  object: DirectorObjectDocumentV1,
  objectIds: Map<string, string>,
  offset: number,
): DirectorObjectDocumentV1 {
  return {
    ...object,
    id: requireMappedId(objectIds, object.id),
    transform: offsetTransform(object.transform, offset),
    characterRig: object.characterRig
      ? {
          posePresetId: object.characterRig.posePresetId,
          controls: { ...object.characterRig.controls },
        }
      : null,
    camera: object.camera
      ? {
          ...object.camera,
          target: offsetTuple3(object.camera.target, offset),
          lookAtObjectId: mapOptionalId(
            objectIds,
            object.camera.lookAtObjectId,
          ),
          followTargetId: mapOptionalId(
            objectIds,
            object.camera.followTargetId,
          ),
          followOffset: cloneTuple3(object.camera.followOffset),
        }
      : null,
  };
}

function remapTransformKeyframe(
  keyframe: DirectorTransformKeyframeDocumentV1,
  keyframeIds: Map<string, string>,
  offset: number,
): DirectorTransformKeyframeDocumentV1 {
  return {
    ...keyframe,
    id: requireMappedId(keyframeIds, keyframe.id),
    value: offsetTransform(keyframe.value, offset),
  };
}

function remapCameraKeyframe(
  keyframe: DirectorCameraKeyframeDocumentV1,
  keyframeIds: Map<string, string>,
  offset: number,
): DirectorCameraKeyframeDocumentV1 {
  return {
    ...keyframe,
    id: requireMappedId(keyframeIds, keyframe.id),
    value: {
      transform: offsetTransform(keyframe.value.transform, offset),
      target: offsetTuple3(keyframe.value.target, offset),
      fov: keyframe.value.fov,
    },
  };
}

function remapPoseKeyframe(
  keyframe: DirectorPoseKeyframeDocumentV1,
  keyframeIds: Map<string, string>,
): DirectorPoseKeyframeDocumentV1 {
  return {
    ...keyframe,
    id: requireMappedId(keyframeIds, keyframe.id),
    value: {
      posePresetId: keyframe.value.posePresetId,
      controls: { ...keyframe.value.controls },
    },
  };
}

function remapGroupKeyframe(
  keyframe: DirectorGroupKeyframeDocumentV1,
  keyframeIds: Map<string, string>,
  offset: number,
): DirectorGroupKeyframeDocumentV1 {
  return {
    ...keyframe,
    id: requireMappedId(keyframeIds, keyframe.id),
    value: offsetTransform(keyframe.value, offset),
  };
}

function remapTrack(input: {
  track: DirectorTimelineTrackDocumentV1;
  objectIds: Map<string, string>;
  groupIds: Map<string, string>;
  trackIds: Map<string, string>;
  pathIds: Map<string, string>;
  keyframeIds: Map<string, string>;
  offset: number;
}): DirectorTimelineTrackDocumentV1 {
  const motionPathId = input.track.motionPathId
    ? requireMappedId(input.pathIds, input.track.motionPathId)
    : null;
  const base = {
    id: requireMappedId(input.trackIds, input.track.id),
    objectId:
      input.track.kind === "group"
        ? requireMappedId(input.groupIds, input.track.objectId)
        : requireMappedId(input.objectIds, input.track.objectId),
    label: input.track.label,
    motionPathId,
    speedCurve: {
      preset: input.track.speedCurve.preset,
      control1: [...input.track.speedCurve.control1] as [number, number],
      control2: [...input.track.speedCurve.control2] as [number, number],
    },
  };
  if (input.track.kind === "group") {
    return {
      ...base,
      kind: "group",
      groupId: requireMappedId(input.groupIds, input.track.groupId),
      memberOffsets: Object.fromEntries(
        Object.entries(input.track.memberOffsets).map(([objectId, value]) => [
          requireMappedId(input.objectIds, objectId),
          cloneTuple3(value),
        ]),
      ),
      keyframes: input.track.keyframes.map((keyframe) =>
        remapGroupKeyframe(keyframe, input.keyframeIds, input.offset),
      ),
    };
  }
  if (input.track.kind === "camera") {
    return {
      ...base,
      kind: "camera",
      keyframes: input.track.keyframes.map((keyframe) =>
        remapCameraKeyframe(keyframe, input.keyframeIds, input.offset),
      ),
    };
  }
  if (input.track.kind === "pose") {
    return {
      ...base,
      kind: "pose",
      keyframes: input.track.keyframes.map((keyframe) =>
        remapPoseKeyframe(keyframe, input.keyframeIds),
      ),
    };
  }
  return {
    ...base,
    kind: "transform",
    keyframes: input.track.keyframes.map((keyframe) =>
      remapTransformKeyframe(keyframe, input.keyframeIds, input.offset),
    ),
  };
}

function anchorMapKey(pathId: string, anchorId: string): string {
  return `${pathId}\u0000${anchorId}`;
}

function remapAnchor(
  pathId: string,
  anchor: DirectorMotionPathAnchorDocumentV1,
  anchorIds: Map<string, string>,
): DirectorMotionPathAnchorDocumentV1 {
  return {
    ...anchor,
    id: requireMappedId(anchorIds, anchorMapKey(pathId, anchor.id)),
    position: cloneTuple3(anchor.position),
    handleIn: cloneTuple3(anchor.handleIn),
    handleOut: cloneTuple3(anchor.handleOut),
  };
}

function remapPath(input: {
  path: DirectorMotionPathDocumentV1;
  objectIds: Map<string, string>;
  pathIds: Map<string, string>;
  anchorIds: Map<string, string>;
  offset: number;
}): DirectorMotionPathDocumentV1 {
  return {
    ...input.path,
    id: requireMappedId(input.pathIds, input.path.id),
    objectId: requireMappedId(input.objectIds, input.path.objectId),
    pivot: cloneTuple3(input.path.pivot),
    transform: offsetTransform(input.path.transform, input.offset),
    initialAnchors: input.path.initialAnchors.map((anchor) =>
      remapAnchor(input.path.id, anchor, input.anchorIds),
    ),
    anchors: input.path.anchors.map((anchor) =>
      remapAnchor(input.path.id, anchor, input.anchorIds),
    ),
  };
}

function remapShot(
  shot: DirectorShotRecordV1,
  shotIds: Map<string, string>,
  objectIds: Map<string, string>,
): DirectorShotRecordV1 {
  return {
    ...shot,
    id: requireMappedId(shotIds, shot.id),
    cameraId: requireMappedId(objectIds, shot.cameraId),
    // Captures are session sidecars and are intentionally not copied by object clipboard.
    captureIds: [],
  };
}

export function planDirectorClipboardPaste(input: {
  document: DirectorProjectDocumentV1;
  packet: unknown;
  pasteOrdinal: number;
  createId?: DirectorClipboardIdFactory;
}): DirectorClipboardPasteResult {
  let document: DirectorProjectDocumentV1;
  try {
    document = normalizeDirectorProjectDocument(input.document);
  } catch {
    return { ok: false, reason: "INVALID_PACKET" };
  }
  if (!Number.isInteger(input.pasteOrdinal) || input.pasteOrdinal < 1) {
    return { ok: false, reason: "INVALID_PACKET" };
  }
  const validated = validateDirectorClipboardPacket(input.packet);
  if (!validated.ok) return validated;
  const packet = validated.packet;
  if (packet.sourceProjectId !== document.projectId) {
    return { ok: false, reason: "PROJECT_MISMATCH" };
  }

  const resourcesById = new Map(
    document.resourceRefs.map((resource) => [resource.id, resource]),
  );
  for (const resource of packet.resourceRefs) {
    const current = resourcesById.get(resource.id);
    if (!current) return { ok: false, reason: "RESOURCE_MISSING" };
    if (descriptorFingerprint(current) !== descriptorFingerprint(resource)) {
      return { ok: false, reason: "RESOURCE_CONFLICT" };
    }
  }

  const factory = input.createId ?? defaultDirectorClipboardIdFactory;
  const objectIds = allocateMap({
    kind: "object",
    sourceIds: packet.objects.map((object) => object.id),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(document.objects.map((object) => object.id)),
    factory,
  });
  const groupIds = allocateMap({
    kind: "group",
    sourceIds: packet.groups.map((group) => group.id),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(document.groups.map((group) => group.id)),
    factory,
  });
  const trackIds = allocateMap({
    kind: "track",
    sourceIds: packet.timeline.tracks.map((track) => track.id),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(document.timeline.tracks.map((track) => track.id)),
    factory,
  });
  const pathIds = allocateMap({
    kind: "path",
    sourceIds: packet.timeline.motionPaths.map((path) => path.id),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(document.timeline.motionPaths.map((path) => path.id)),
    factory,
  });
  const keyframeIds = allocateMap({
    kind: "keyframe",
    sourceIds: packet.timeline.tracks.flatMap((track) =>
      track.keyframes.map((keyframe) => keyframe.id),
    ),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(
      document.timeline.tracks.flatMap((track) =>
        track.keyframes.map((keyframe) => keyframe.id),
      ),
    ),
    factory,
  });
  const anchorSourceIds = packet.timeline.motionPaths.flatMap((path) => [
    ...new Set(
      [...path.initialAnchors, ...path.anchors].map((anchor) =>
        anchorMapKey(path.id, anchor.id),
      ),
    ),
  ]);
  const anchorIds = allocateMap({
    kind: "anchor",
    sourceIds: anchorSourceIds,
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(
      document.timeline.motionPaths.flatMap((path) =>
        [...path.initialAnchors, ...path.anchors].map((anchor) => anchor.id),
      ),
    ),
    factory,
  });
  const shotIds = allocateMap({
    kind: "shot",
    sourceIds: packet.shots.map((shot) => shot.id),
    pasteOrdinal: input.pasteOrdinal,
    usedIds: new Set(document.shots.map((shot) => shot.id)),
    factory,
  });
  if (
    !objectIds ||
    !groupIds ||
    !trackIds ||
    !pathIds ||
    !keyframeIds ||
    !anchorIds ||
    !shotIds
  ) {
    return { ok: false, reason: "IDENTITY_ALLOCATION_FAILED" };
  }

  const offset = DIRECTOR_CLIPBOARD_PASTE_OFFSET * input.pasteOrdinal;
  try {
    const pastedObjects = packet.objects.map((object) =>
      remapObject(object, objectIds, offset),
    );
    const pastedGroups = packet.groups.map((group) => ({
      ...group,
      id: requireMappedId(groupIds, group.id),
      characterIds: group.characterIds.map((objectId) =>
        requireMappedId(objectIds, objectId),
      ),
      crowd: group.crowd ? { ...group.crowd } : null,
    }));
    const pastedTracks = packet.timeline.tracks.map((track) =>
      remapTrack({
        track,
        objectIds,
        groupIds,
        trackIds,
        pathIds,
        keyframeIds,
        offset,
      }),
    );
    const pastedPaths = packet.timeline.motionPaths.map((path) =>
      remapPath({
        path,
        objectIds,
        pathIds,
        anchorIds,
        offset,
      }),
    );
    const pastedShots = packet.shots.map((shot) =>
      remapShot(shot, shotIds, objectIds),
    );
    const nextDocument = normalizeDirectorProjectDocument({
      ...document,
      objects: [...document.objects, ...pastedObjects],
      groups: [...document.groups, ...pastedGroups],
      shots: [...document.shots, ...pastedShots],
      activeCameraId: document.activeCameraId,
      timeline: {
        ...document.timeline,
        tracks: [...document.timeline.tracks, ...pastedTracks],
        motionPaths: [...document.timeline.motionPaths, ...pastedPaths],
      },
      resourceRefs: document.resourceRefs,
      captureDescriptors: document.captureDescriptors,
    });
    const selectedObjectIds = packet.selection.selectedObjectIds.map(
      (objectId) => requireMappedId(objectIds, objectId),
    );
    return {
      ok: true,
      plan: {
        document: nextDocument,
        selection: {
          selectedObjectId: selectedObjectIds.at(-1) ?? null,
          selectedObjectIds,
          selectedGroupId: packet.selection.selectedGroupId
            ? requireMappedId(groupIds, packet.selection.selectedGroupId)
            : null,
        },
        pastedTrackIds: pastedTracks.map((track) => track.id),
        pastedMotionPathIds: pastedPaths.map((path) => path.id),
        offset,
        idMaps: {
          objects: mapToRecord(objectIds),
          groups: mapToRecord(groupIds),
          tracks: mapToRecord(trackIds),
          paths: mapToRecord(pathIds),
          keyframes: mapToRecord(keyframeIds),
          anchors: mapToRecord(anchorIds),
          shots: mapToRecord(shotIds),
        },
        aliasedResourceIds: packet.resourceRefs.map((resource) => resource.id),
      },
    };
  } catch {
    return { ok: false, reason: "INVALID_PACKET" };
  }
}
