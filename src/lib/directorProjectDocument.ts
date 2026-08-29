import type {
  DirectorCameraKeyframe,
  DirectorCapture,
  DirectorCharacterGroup,
  DirectorGroupKeyframe,
  DirectorMotionPath,
  DirectorObject,
  DirectorPoseKeyframe,
  DirectorScene,
  DirectorTimelineState,
  DirectorTimelineTrack,
  DirectorTransform,
  DirectorTransformKeyframe,
  DirectorTuple3,
} from "@/store/directorStore";
import type {
  DirectorModelLibraryCategoryId,
  DirectorModelLibraryVisual,
} from "@/components/director/directorModelLibrary";
import type {
  DirectorCameraFollowView,
  DirectorCameraLookAtMode,
} from "@/components/director/directorCameraFollow";
import type {
  DirectorCharacterRig,
  DirectorPoseKeyframeValue,
  DirectorPosePresetId,
} from "@/components/director/directorPose";
import type {
  DirectorMotionPathAnchorType,
  DirectorMotionPathPreset,
  DirectorSpeedCurvePreset,
} from "@/store/directorStore";

export const DIRECTOR_PROJECT_SCHEMA_VERSION = 1 as const;

export interface DirectorProjectOwnerV1 {
  route: "libtv";
  canvasId: string;
  sourceNodeId: string;
}

export type DirectorResourceKindV1 = "model" | "panorama" | "media";
export type DirectorResourceSourceV1 =
  | "catalog"
  | "local"
  | "remote"
  | "canvas";

export interface DirectorResourceReferenceV1 {
  id: string;
  kind: DirectorResourceKindV1;
  source: DirectorResourceSourceV1;
  label: string;
  locator: string;
  mimeType: string | null;
}

export interface DirectorTransformDocumentV1 {
  position: DirectorTuple3;
  rotation: DirectorTuple3;
  scale: DirectorTuple3;
}

export interface DirectorCharacterRigDocumentV1 {
  posePresetId: DirectorPosePresetId | null;
  controls: Record<string, number>;
}

export interface DirectorCameraDocumentV1 {
  fov: number;
  target: DirectorTuple3;
  lookAtMode: DirectorCameraLookAtMode;
  lookAtObjectId: string | null;
  followTargetId: string | null;
  followOffset: DirectorTuple3;
  followView: DirectorCameraFollowView;
}

export interface DirectorObjectDocumentV1 {
  id: string;
  name: string;
  kind: DirectorObject["kind"];
  primitive: DirectorObject["primitive"];
  color: string;
  visible: boolean;
  locked: boolean;
  transform: DirectorTransformDocumentV1;
  assetRefId: string | null;
  libraryCategoryId: DirectorModelLibraryCategoryId | null;
  libraryVisual: DirectorModelLibraryVisual | null;
  characterRig: DirectorCharacterRigDocumentV1 | null;
  camera: DirectorCameraDocumentV1 | null;
}

export interface DirectorGroupDocumentV1 {
  id: string;
  label: string;
  characterIds: string[];
  crowd: {
    rows: number;
    columns: number;
    spacing: number;
  } | null;
}

export interface DirectorSceneDocumentV1 {
  name: string;
  backgroundColor: string;
  groundColor: string;
  showGround: boolean;
  showGrid: boolean;
}

export type DirectorAspectRatioV1 = "16:9" | "9:16" | "1:1";

export interface DirectorCaptureDescriptorV1 {
  id: string;
  cameraId: string | null;
  shotId: string | null;
  cameraName: string;
  aspectRatio: DirectorAspectRatioV1;
  width: number;
  height: number;
  createdAt: string;
  resourceRefId: string | null;
}

export interface DirectorShotRecordV1 {
  id: string;
  name: string;
  cameraId: string;
  startTime: number;
  endTime: number;
  captureIds: string[];
}

export interface DirectorSpeedCurveDocumentV1 {
  preset: DirectorSpeedCurvePreset;
  control1: [number, number];
  control2: [number, number];
}

export interface DirectorTransformKeyframeDocumentV1 {
  id: string;
  time: number;
  value: DirectorTransformDocumentV1;
}

export interface DirectorCameraKeyframeValueDocumentV1 {
  transform: DirectorTransformDocumentV1;
  target: DirectorTuple3;
  fov: number;
}

export interface DirectorCameraKeyframeDocumentV1 {
  id: string;
  time: number;
  value: DirectorCameraKeyframeValueDocumentV1;
}

export interface DirectorPoseKeyframeValueDocumentV1 {
  posePresetId: DirectorPosePresetId | null;
  controls: Record<string, number>;
}

export interface DirectorPoseKeyframeDocumentV1 {
  id: string;
  time: number;
  value: DirectorPoseKeyframeValueDocumentV1;
}

export interface DirectorGroupKeyframeDocumentV1 {
  id: string;
  time: number;
  value: DirectorTransformDocumentV1;
}

interface DirectorTimelineTrackDocumentBaseV1 {
  id: string;
  objectId: string;
  label: string;
  motionPathId: string | null;
  speedCurve: DirectorSpeedCurveDocumentV1;
}

export type DirectorTimelineTrackDocumentV1 =
  | (DirectorTimelineTrackDocumentBaseV1 & {
      kind: "transform";
      keyframes: DirectorTransformKeyframeDocumentV1[];
    })
  | (DirectorTimelineTrackDocumentBaseV1 & {
      kind: "camera";
      keyframes: DirectorCameraKeyframeDocumentV1[];
    })
  | (DirectorTimelineTrackDocumentBaseV1 & {
      kind: "pose";
      keyframes: DirectorPoseKeyframeDocumentV1[];
    })
  | (DirectorTimelineTrackDocumentBaseV1 & {
      kind: "group";
      groupId: string;
      memberOffsets: Record<string, DirectorTuple3>;
      keyframes: DirectorGroupKeyframeDocumentV1[];
    });

export interface DirectorMotionPathAnchorDocumentV1 {
  id: string;
  position: DirectorTuple3;
  type: DirectorMotionPathAnchorType;
  handleIn: DirectorTuple3;
  handleOut: DirectorTuple3;
}

export interface DirectorMotionPathDocumentV1 {
  id: string;
  objectId: string;
  name: string;
  preset: DirectorMotionPathPreset;
  enabled: boolean;
  orientToPath: boolean;
  closed: boolean;
  pivot: DirectorTuple3;
  transform: DirectorTransformDocumentV1;
  initialAnchors: DirectorMotionPathAnchorDocumentV1[];
  anchors: DirectorMotionPathAnchorDocumentV1[];
}

export interface DirectorTimelineDocumentV1 {
  duration: number;
  loop: boolean;
  autoKeyframe: boolean;
  tracks: DirectorTimelineTrackDocumentV1[];
  motionPaths: DirectorMotionPathDocumentV1[];
}

export interface DirectorProjectDocumentV1 {
  schemaVersion: typeof DIRECTOR_PROJECT_SCHEMA_VERSION;
  projectId: string;
  owner: DirectorProjectOwnerV1;
  scene: DirectorSceneDocumentV1;
  objects: DirectorObjectDocumentV1[];
  groups: DirectorGroupDocumentV1[];
  shots: DirectorShotRecordV1[];
  activeCameraId: string;
  timeline: DirectorTimelineDocumentV1;
  outputPreferences: {
    aspectRatio: DirectorAspectRatioV1;
  };
  resourceRefs: DirectorResourceReferenceV1[];
  captureDescriptors: DirectorCaptureDescriptorV1[];
}

export interface DirectorProjectSnapshotInput {
  projectId: string;
  owner: DirectorProjectOwnerV1;
  scene: DirectorScene;
  objects: DirectorObject[];
  groups: DirectorCharacterGroup[];
  activeCameraId: string;
  aspectRatio: DirectorAspectRatioV1;
  timeline: DirectorTimelineState;
  captures?: DirectorCapture[];
  shots?: DirectorShotRecordV1[];
  resourceRefs?: DirectorResourceReferenceV1[];
}

export type DirectorProjectDocumentErrorCode =
  | "INVALID_DOCUMENT"
  | "FUTURE_SCHEMA_VERSION"
  | "UNKNOWN_FIELD"
  | "INVALID_FIELD"
  | "DUPLICATE_ID"
  | "DANGLING_REFERENCE"
  | "NON_FINITE_NUMBER";

export interface DirectorProjectDocumentError {
  code: DirectorProjectDocumentErrorCode;
  path: string;
  message: string;
}

export type DirectorProjectDocumentDecodeResult =
  | {
      ok: true;
      document: DirectorProjectDocumentV1;
    }
  | {
      ok: false;
      error: DirectorProjectDocumentError;
    };

class DocumentDecodeFailure extends Error {
  readonly error: DirectorProjectDocumentError;

  constructor(error: DirectorProjectDocumentError) {
    super(error.message);
    this.name = "DocumentDecodeFailure";
    this.error = error;
  }
}

type UnknownRecord = Record<string, unknown>;

const DIRECTOR_OBJECT_KINDS = ["character", "prop", "camera"] as const;
const DIRECTOR_PRIMITIVES = [
  "character",
  "table",
  "mug",
  "wall",
  "camera",
  "library",
] as const;
const DIRECTOR_LIBRARY_CATEGORIES = [
  "convenience",
  "home",
  "outdoor",
  "tools",
  "my-models",
] as const;
const DIRECTOR_LIBRARY_VISUALS = [
  "bottle",
  "chair",
  "lamp",
  "plant",
  "box",
] as const;
const DIRECTOR_CAMERA_LOOK_AT_MODES = [
  "coordinate",
  "rotation",
  "object",
] as const;
const DIRECTOR_CAMERA_FOLLOW_VIEWS = ["third-person", "first-person"] as const;
const DIRECTOR_SPEED_CURVE_PRESETS = [
  "linear",
  "smooth",
  "ease-in",
  "ease-out",
  "ease-in-out",
  "custom",
] as const;
const DIRECTOR_MOTION_PATH_PRESETS = [
  "line",
  "ring",
  "rectangle",
  "pencil",
  "pen",
] as const;
const DIRECTOR_ANCHOR_TYPES = [
  "vertex",
  "symmetric",
  "asymmetric",
] as const;
const DIRECTOR_TRACK_KINDS = [
  "transform",
  "camera",
  "pose",
  "group",
] as const;
const DIRECTOR_RESOURCE_KINDS = ["model", "panorama", "media"] as const;
const DIRECTOR_RESOURCE_SOURCES = [
  "catalog",
  "local",
  "remote",
  "canvas",
] as const;
const DIRECTOR_ASPECT_RATIOS = ["16:9", "9:16", "1:1"] as const;
const DIRECTOR_POSE_PRESET_IDS_V1 = [
  "stand",
  "t-pose",
  "walk",
  "run",
  "sit",
  "crouch",
  "kneel-one",
  "kneel-two",
  "hands-on-hips",
  "lean",
  "bow",
  "think",
  "fight",
  "kick",
  "throw",
  "push",
  "wave",
  "reach",
  "cross-arms",
  "phone",
] as const satisfies readonly DirectorPosePresetId[];

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function fail(
  code: DirectorProjectDocumentErrorCode,
  path: string,
  message: string,
): never {
  throw new DocumentDecodeFailure({ code, path, message });
}

function expectRecord(value: unknown, path: string): UnknownRecord {
  if (!isRecord(value)) {
    fail("INVALID_DOCUMENT", path, "expected an object");
  }
  return value;
}

function expectArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) {
    fail("INVALID_FIELD", path, "expected an array");
  }
  return value;
}

function expectString(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    fail("INVALID_FIELD", path, "expected a non-empty string");
  }
  return value;
}

function expectNullableString(
  value: unknown,
  path: string,
): string | null {
  if (value === null) return null;
  return expectString(value, path);
}

function expectFiniteNumber(value: unknown, path: string): number {
  if (typeof value !== "number") {
    fail("INVALID_FIELD", path, "expected a number");
  }
  if (!Number.isFinite(value)) {
    fail("NON_FINITE_NUMBER", path, "number must be finite");
  }
  return value;
}

function expectBoolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    fail("INVALID_FIELD", path, "expected a boolean");
  }
  return value;
}

function expectEnum<T extends string>(
  value: unknown,
  values: readonly T[],
  path: string,
): T {
  if (typeof value !== "string" || !values.includes(value as T)) {
    fail("INVALID_FIELD", path, `expected one of: ${values.join(", ")}`);
  }
  return value as T;
}

function expectExactKeys(
  value: UnknownRecord,
  keys: readonly string[],
  path: string,
): void {
  const expected = new Set(keys);
  for (const key of Object.keys(value)) {
    if (!expected.has(key)) {
      fail(
        "UNKNOWN_FIELD",
        `${path}.${key}`,
        `unknown field "${key}"`,
      );
    }
  }
  for (const key of keys) {
    if (!(key in value)) {
      fail("INVALID_FIELD", `${path}.${key}`, "required field is missing");
    }
  }
}

function expectExactKeysWithOptional(
  value: UnknownRecord,
  requiredKeys: readonly string[],
  optionalKeys: readonly string[],
  path: string,
): void {
  const allowed = new Set([...requiredKeys, ...optionalKeys]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      fail(
        "UNKNOWN_FIELD",
        `${path}.${key}`,
        `unknown field "${key}"`,
      );
    }
  }
  for (const key of requiredKeys) {
    if (!(key in value)) {
      fail("INVALID_FIELD", `${path}.${key}`, "required field is missing");
    }
  }
}

function expectTuple3(value: unknown, path: string): DirectorTuple3 {
  const tuple = expectArray(value, path);
  if (tuple.length !== 3) {
    fail("INVALID_FIELD", path, "expected a tuple with exactly 3 values");
  }
  return [
    expectFiniteNumber(tuple[0], `${path}[0]`),
    expectFiniteNumber(tuple[1], `${path}[1]`),
    expectFiniteNumber(tuple[2], `${path}[2]`),
  ];
}

function expectTuple2(value: unknown, path: string): [number, number] {
  const tuple = expectArray(value, path);
  if (tuple.length !== 2) {
    fail("INVALID_FIELD", path, "expected a tuple with exactly 2 values");
  }
  const first = expectFiniteNumber(tuple[0], `${path}[0]`);
  const second = expectFiniteNumber(tuple[1], `${path}[1]`);
  if (first < 0 || first > 1 || second < 0 || second > 1) {
    fail("INVALID_FIELD", path, "speed curve coordinates must be in [0, 1]");
  }
  return [first, second];
}

function expectIdArray(value: unknown, path: string): string[] {
  const ids = expectArray(value, path).map((item, index) =>
    expectString(item, `${path}[${index}]`),
  );
  const seen = new Set<string>();
  ids.forEach((id, index) => {
    if (seen.has(id)) {
      fail("DUPLICATE_ID", `${path}[${index}]`, `duplicate ID "${id}"`);
    }
    seen.add(id);
  });
  return ids;
}

function expectNumberMap(
  value: unknown,
  path: string,
): Record<string, number> {
  const record = expectRecord(value, path);
  const result: Record<string, number> = {};
  Object.entries(record)
    .sort(([left], [right]) => left.localeCompare(right))
    .forEach(([key, item]) => {
    if (key.trim().length === 0) {
      fail("INVALID_FIELD", `${path}.${key}`, "map key must be non-empty");
    }
    result[key] = expectFiniteNumber(item, `${path}.${key}`);
    });
  return result;
}

function expectTuple3Map(
  value: unknown,
  path: string,
): Record<string, DirectorTuple3> {
  const record = expectRecord(value, path);
  const result: Record<string, DirectorTuple3> = {};
  Object.entries(record)
    .sort(([left], [right]) => left.localeCompare(right))
    .forEach(([key, item]) => {
    if (key.trim().length === 0) {
      fail("INVALID_FIELD", `${path}.${key}`, "map key must be non-empty");
    }
    result[key] = expectTuple3(item, `${path}.${key}`);
    });
  return result;
}

function expectTransform(
  value: unknown,
  path: string,
): DirectorTransformDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["position", "rotation", "scale"], path);
  return {
    position: expectTuple3(record.position, `${path}.position`),
    rotation: expectTuple3(record.rotation, `${path}.rotation`),
    scale: expectTuple3(record.scale, `${path}.scale`),
  };
}

function expectPoseValue(
  value: unknown,
  path: string,
): DirectorPoseKeyframeValueDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["posePresetId", "controls"], path);
  return {
    posePresetId: expectNullableEnum(
      record.posePresetId,
      DIRECTOR_POSE_PRESET_IDS_V1,
      `${path}.posePresetId`,
    ),
    controls: expectNumberMap(record.controls, `${path}.controls`),
  };
}

function expectNullableEnum<T extends string>(
  value: unknown,
  values: readonly T[],
  path: string,
): T | null {
  if (value === null) return null;
  return expectEnum(value, values, path);
}

function expectCameraValue(
  value: unknown,
  path: string,
): DirectorCameraKeyframeValueDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["transform", "target", "fov"], path);
  return {
    transform: expectTransform(record.transform, `${path}.transform`),
    target: expectTuple3(record.target, `${path}.target`),
    fov: expectFov(record.fov, `${path}.fov`),
  };
}

function expectFov(value: unknown, path: string): number {
  const fov = expectFiniteNumber(value, path);
  if (fov <= 0 || fov >= 180) {
    fail("INVALID_FIELD", path, "field of view must be between 0 and 180");
  }
  return fov;
}

function expectTimelineKeyframeTime(
  value: unknown,
  path: string,
  duration: number,
): number {
  const time = expectFiniteNumber(value, path);
  if (time < 0 || time > duration) {
    fail("INVALID_FIELD", path, "keyframe time must be within timeline duration");
  }
  return time;
}

function expectSpeedCurve(
  value: unknown,
  path: string,
): DirectorSpeedCurveDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["preset", "control1", "control2"], path);
  return {
    preset: expectEnum(
      record.preset,
      DIRECTOR_SPEED_CURVE_PRESETS,
      `${path}.preset`,
    ),
    control1: expectTuple2(record.control1, `${path}.control1`),
    control2: expectTuple2(record.control2, `${path}.control2`),
  };
}

function expectAnchors(
  value: unknown,
  path: string,
): DirectorMotionPathAnchorDocumentV1[] {
  const anchors = expectArray(value, path).map((item, index) => {
    const anchorPath = `${path}[${index}]`;
    const record = expectRecord(item, anchorPath);
    expectExactKeys(
      record,
      ["id", "position", "type", "handleIn", "handleOut"],
      anchorPath,
    );
    return {
      id: expectString(record.id, `${anchorPath}.id`),
      position: expectTuple3(record.position, `${anchorPath}.position`),
      type: expectEnum(record.type, DIRECTOR_ANCHOR_TYPES, `${anchorPath}.type`),
      handleIn: expectTuple3(record.handleIn, `${anchorPath}.handleIn`),
      handleOut: expectTuple3(record.handleOut, `${anchorPath}.handleOut`),
    };
  });
  const seen = new Set<string>();
  anchors.forEach((anchor, index) => {
    if (seen.has(anchor.id)) {
      fail(
        "DUPLICATE_ID",
        `${path}[${index}].id`,
        `duplicate anchor ID "${anchor.id}"`,
      );
    }
    seen.add(anchor.id);
  });
  if (anchors.length < 2) {
    fail("INVALID_FIELD", path, "a motion path needs at least two anchors");
  }
  return anchors;
}

function expectTransformKeyframes(
  value: unknown,
  path: string,
  duration: number,
): DirectorTransformKeyframeDocumentV1[] {
  return expectArray(value, path).map((item, index) => {
    const keyframePath = `${path}[${index}]`;
    const record = expectRecord(item, keyframePath);
    expectExactKeys(record, ["id", "time", "value"], keyframePath);
    return {
      id: expectString(record.id, `${keyframePath}.id`),
      time: expectTimelineKeyframeTime(
        record.time,
        `${keyframePath}.time`,
        duration,
      ),
      value: expectTransform(record.value, `${keyframePath}.value`),
    };
  });
}

function expectCameraKeyframes(
  value: unknown,
  path: string,
  duration: number,
): DirectorCameraKeyframeDocumentV1[] {
  return expectArray(value, path).map((item, index) => {
    const keyframePath = `${path}[${index}]`;
    const record = expectRecord(item, keyframePath);
    expectExactKeys(record, ["id", "time", "value"], keyframePath);
    return {
      id: expectString(record.id, `${keyframePath}.id`),
      time: expectTimelineKeyframeTime(
        record.time,
        `${keyframePath}.time`,
        duration,
      ),
      value: expectCameraValue(record.value, `${keyframePath}.value`),
    };
  });
}

function expectPoseKeyframes(
  value: unknown,
  path: string,
  duration: number,
): DirectorPoseKeyframeDocumentV1[] {
  return expectArray(value, path).map((item, index) => {
    const keyframePath = `${path}[${index}]`;
    const record = expectRecord(item, keyframePath);
    expectExactKeys(record, ["id", "time", "value"], keyframePath);
    return {
      id: expectString(record.id, `${keyframePath}.id`),
      time: expectTimelineKeyframeTime(
        record.time,
        `${keyframePath}.time`,
        duration,
      ),
      value: expectPoseValue(record.value, `${keyframePath}.value`),
    };
  });
}

function expectGroupKeyframes(
  value: unknown,
  path: string,
  duration: number,
): DirectorGroupKeyframeDocumentV1[] {
  return expectArray(value, path).map((item, index) => {
    const keyframePath = `${path}[${index}]`;
    const record = expectRecord(item, keyframePath);
    expectExactKeys(record, ["id", "time", "value"], keyframePath);
    return {
      id: expectString(record.id, `${keyframePath}.id`),
      time: expectTimelineKeyframeTime(
        record.time,
        `${keyframePath}.time`,
        duration,
      ),
      value: expectTransform(record.value, `${keyframePath}.value`),
    };
  });
}

function expectTrack(
  value: unknown,
  path: string,
  duration: number,
): DirectorTimelineTrackDocumentV1 {
  const record = expectRecord(value, path);
  const kind = expectEnum(record.kind, DIRECTOR_TRACK_KINDS, `${path}.kind`);
  const commonKeys = [
    "id",
    "kind",
    "objectId",
    "label",
    "motionPathId",
    "speedCurve",
  ];
  const keyframeKeys = ["keyframes"];
  const base = {
    id: expectString(record.id, `${path}.id`),
    objectId: expectString(record.objectId, `${path}.objectId`),
    label: expectString(record.label, `${path}.label`),
    motionPathId: expectNullableString(
      record.motionPathId,
      `${path}.motionPathId`,
    ),
    speedCurve: expectSpeedCurve(record.speedCurve, `${path}.speedCurve`),
  };
  if (kind === "group") {
    expectExactKeys(record, [...commonKeys, "groupId", "memberOffsets", ...keyframeKeys], path);
    return {
      ...base,
      kind,
      groupId: expectString(record.groupId, `${path}.groupId`),
      memberOffsets: expectTuple3Map(
        record.memberOffsets,
        `${path}.memberOffsets`,
      ),
      keyframes: expectGroupKeyframes(
        record.keyframes,
        `${path}.keyframes`,
        duration,
      ),
    };
  }
  expectExactKeys(record, [...commonKeys, ...keyframeKeys], path);
  if (kind === "camera") {
    return {
      ...base,
      kind,
      keyframes: expectCameraKeyframes(
        record.keyframes,
        `${path}.keyframes`,
        duration,
      ),
    };
  }
  if (kind === "pose") {
    return {
      ...base,
      kind,
      keyframes: expectPoseKeyframes(
        record.keyframes,
        `${path}.keyframes`,
        duration,
      ),
    };
  }
  return {
    ...base,
    kind,
    keyframes: expectTransformKeyframes(
      record.keyframes,
      `${path}.keyframes`,
      duration,
    ),
  };
}

function expectPath(
  value: unknown,
  path: string,
): DirectorMotionPathDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    [
      "id",
      "objectId",
      "name",
      "preset",
      "enabled",
      "orientToPath",
      "closed",
      "pivot",
      "transform",
      "initialAnchors",
      "anchors",
    ],
    path,
  );
  return {
    id: expectString(record.id, `${path}.id`),
    objectId: expectString(record.objectId, `${path}.objectId`),
    name: expectString(record.name, `${path}.name`),
    preset: expectEnum(
      record.preset,
      DIRECTOR_MOTION_PATH_PRESETS,
      `${path}.preset`,
    ),
    enabled: expectBoolean(record.enabled, `${path}.enabled`),
    orientToPath: expectBoolean(
      record.orientToPath,
      `${path}.orientToPath`,
    ),
    closed: expectBoolean(record.closed, `${path}.closed`),
    pivot: expectTuple3(record.pivot, `${path}.pivot`),
    transform: expectTransform(record.transform, `${path}.transform`),
    initialAnchors: expectAnchors(
      record.initialAnchors,
      `${path}.initialAnchors`,
    ),
    anchors: expectAnchors(record.anchors, `${path}.anchors`),
  };
}

function expectCameraDocument(
  value: unknown,
  path: string,
): DirectorCameraDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    [
      "fov",
      "target",
      "lookAtMode",
      "lookAtObjectId",
      "followTargetId",
      "followOffset",
      "followView",
    ],
    path,
  );
  return {
    fov: expectFov(record.fov, `${path}.fov`),
    target: expectTuple3(record.target, `${path}.target`),
    lookAtMode: expectEnum(
      record.lookAtMode,
      DIRECTOR_CAMERA_LOOK_AT_MODES,
      `${path}.lookAtMode`,
    ),
    lookAtObjectId: expectNullableString(
      record.lookAtObjectId,
      `${path}.lookAtObjectId`,
    ),
    followTargetId: expectNullableString(
      record.followTargetId,
      `${path}.followTargetId`,
    ),
    followOffset: expectTuple3(
      record.followOffset,
      `${path}.followOffset`,
    ),
    followView: expectEnum(
      record.followView,
      DIRECTOR_CAMERA_FOLLOW_VIEWS,
      `${path}.followView`,
    ),
  };
}

function expectObject(
  value: unknown,
  path: string,
): DirectorObjectDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    [
      "id",
      "name",
      "kind",
      "primitive",
      "color",
      "visible",
      "locked",
      "transform",
      "assetRefId",
      "libraryCategoryId",
      "libraryVisual",
      "characterRig",
      "camera",
    ],
    path,
  );
  const kind = expectEnum(
    record.kind,
    DIRECTOR_OBJECT_KINDS,
    `${path}.kind`,
  );
  const camera = record.camera === null
    ? null
    : expectCameraDocument(record.camera, `${path}.camera`);
  const characterRig = record.characterRig === null
    ? null
    : expectCharacterRig(record.characterRig, `${path}.characterRig`);
  if (kind === "camera" && camera === null) {
    fail("INVALID_FIELD", `${path}.camera`, "camera objects need camera data");
  }
  if (kind !== "camera" && camera !== null) {
    fail(
      "INVALID_FIELD",
      `${path}.camera`,
      "only camera objects may contain camera data",
    );
  }
  if (kind === "character" && characterRig === null) {
    fail(
      "INVALID_FIELD",
      `${path}.characterRig`,
      "character objects need character rig data",
    );
  }
  if (kind !== "character" && characterRig !== null) {
    fail(
      "INVALID_FIELD",
      `${path}.characterRig`,
      "only character objects may contain character rig data",
    );
  }
  return {
    id: expectString(record.id, `${path}.id`),
    name: expectString(record.name, `${path}.name`),
    kind,
    primitive: expectEnum(
      record.primitive,
      DIRECTOR_PRIMITIVES,
      `${path}.primitive`,
    ),
    color: expectString(record.color, `${path}.color`),
    visible: expectBoolean(record.visible, `${path}.visible`),
    locked: expectBoolean(record.locked, `${path}.locked`),
    transform: expectTransform(record.transform, `${path}.transform`),
    assetRefId: expectNullableString(
      record.assetRefId,
      `${path}.assetRefId`,
    ),
    libraryCategoryId: expectNullableEnum(
      record.libraryCategoryId,
      DIRECTOR_LIBRARY_CATEGORIES,
      `${path}.libraryCategoryId`,
    ),
    libraryVisual: expectNullableEnum(
      record.libraryVisual,
      DIRECTOR_LIBRARY_VISUALS,
      `${path}.libraryVisual`,
    ),
    characterRig,
    camera,
  };
}

function expectCharacterRig(
  value: unknown,
  path: string,
): DirectorCharacterRigDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["posePresetId", "controls"], path);
  return {
    posePresetId: expectNullableEnum(
      record.posePresetId,
      DIRECTOR_POSE_PRESET_IDS_V1,
      `${path}.posePresetId`,
    ),
    controls: expectNumberMap(record.controls, `${path}.controls`),
  };
}

function expectGroup(
  value: unknown,
  path: string,
): DirectorGroupDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["id", "label", "characterIds", "crowd"], path);
  const crowd = record.crowd === null
    ? null
    : expectCrowd(record.crowd, `${path}.crowd`);
  return {
    id: expectString(record.id, `${path}.id`),
    label: expectString(record.label, `${path}.label`),
    characterIds: expectIdArray(record.characterIds, `${path}.characterIds`),
    crowd,
  };
}

function expectCrowd(
  value: unknown,
  path: string,
): DirectorGroupDocumentV1["crowd"] {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["rows", "columns", "spacing"], path);
  const rows = expectFiniteNumber(record.rows, `${path}.rows`);
  const columns = expectFiniteNumber(record.columns, `${path}.columns`);
  const spacing = expectFiniteNumber(record.spacing, `${path}.spacing`);
  if (!Number.isInteger(rows) || rows < 1) {
    fail("INVALID_FIELD", `${path}.rows`, "rows must be a positive integer");
  }
  if (!Number.isInteger(columns) || columns < 1) {
    fail(
      "INVALID_FIELD",
      `${path}.columns`,
      "columns must be a positive integer",
    );
  }
  if (spacing < 0) {
    fail("INVALID_FIELD", `${path}.spacing`, "spacing cannot be negative");
  }
  return { rows, columns, spacing };
}

function expectScene(
  value: unknown,
  path: string,
): DirectorSceneDocumentV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    ["name", "backgroundColor", "groundColor", "showGround", "showGrid"],
    path,
  );
  return {
    name: expectString(record.name, `${path}.name`),
    backgroundColor: expectString(
      record.backgroundColor,
      `${path}.backgroundColor`,
    ),
    groundColor: expectString(record.groundColor, `${path}.groundColor`),
    showGround: expectBoolean(record.showGround, `${path}.showGround`),
    showGrid: expectBoolean(record.showGrid, `${path}.showGrid`),
  };
}

function expectResourceReference(
  value: unknown,
  path: string,
): DirectorResourceReferenceV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    ["id", "kind", "source", "label", "locator", "mimeType"],
    path,
  );
  const locator = expectString(record.locator, `${path}.locator`);
  if (locator.startsWith("data:") || locator.startsWith("blob:")) {
    fail(
      "INVALID_FIELD",
      `${path}.locator`,
      "portable resource references cannot contain data or blob URLs",
    );
  }
  return {
    id: expectString(record.id, `${path}.id`),
    kind: expectEnum(record.kind, DIRECTOR_RESOURCE_KINDS, `${path}.kind`),
    source: expectEnum(
      record.source,
      DIRECTOR_RESOURCE_SOURCES,
      `${path}.source`,
    ),
    label: expectString(record.label, `${path}.label`),
    locator,
    mimeType: expectNullableString(record.mimeType, `${path}.mimeType`),
  };
}

function expectCaptureDescriptor(
  value: unknown,
  path: string,
): DirectorCaptureDescriptorV1 {
  const record = expectRecord(value, path);
  expectExactKeysWithOptional(
    record,
    [
      "id",
      "cameraId",
      "cameraName",
      "aspectRatio",
      "width",
      "height",
      "createdAt",
      "resourceRefId",
    ],
    ["shotId"],
    path,
  );
  const width = expectFiniteNumber(record.width, `${path}.width`);
  const height = expectFiniteNumber(record.height, `${path}.height`);
  if (!Number.isInteger(width) || width <= 0) {
    fail("INVALID_FIELD", `${path}.width`, "width must be a positive integer");
  }
  if (!Number.isInteger(height) || height <= 0) {
    fail(
      "INVALID_FIELD",
      `${path}.height`,
      "height must be a positive integer",
    );
  }
  return {
    id: expectString(record.id, `${path}.id`),
    cameraId: expectNullableString(record.cameraId, `${path}.cameraId`),
    shotId:
      record.shotId === undefined
        ? null
        : expectNullableString(record.shotId, `${path}.shotId`),
    cameraName: expectString(record.cameraName, `${path}.cameraName`),
    aspectRatio: expectEnum(
      record.aspectRatio,
      DIRECTOR_ASPECT_RATIOS,
      `${path}.aspectRatio`,
    ),
    width,
    height,
    createdAt: expectString(record.createdAt, `${path}.createdAt`),
    resourceRefId: expectNullableString(
      record.resourceRefId,
      `${path}.resourceRefId`,
    ),
  };
}

function deriveDefaultShots(
  objects: DirectorObjectDocumentV1[],
  duration: number,
  captures: DirectorCaptureDescriptorV1[],
): DirectorShotRecordV1[] {
  return objects
    .filter((object) => object.kind === "camera")
    .map((camera) => ({
      id: `director-shot-${camera.id}`,
      name: `${camera.name} · 镜头`,
      cameraId: camera.id,
      startTime: 0,
      endTime: duration,
      captureIds: captures
        .filter((capture) => capture.cameraId === camera.id)
        .map((capture) => capture.id),
    }));
}

function expectShot(
  value: unknown,
  path: string,
  duration: number,
): DirectorShotRecordV1 {
  const record = expectRecord(value, path);
  expectExactKeys(
    record,
    ["id", "name", "cameraId", "startTime", "endTime", "captureIds"],
    path,
  );
  const startTime = expectFiniteNumber(record.startTime, `${path}.startTime`);
  const endTime = expectFiniteNumber(record.endTime, `${path}.endTime`);
  if (startTime < 0 || startTime >= endTime || endTime > duration) {
    fail(
      "INVALID_FIELD",
      path,
      "shot range must satisfy 0 <= startTime < endTime <= timeline duration",
    );
  }
  return {
    id: expectString(record.id, `${path}.id`),
    name: expectString(record.name, `${path}.name`),
    cameraId: expectString(record.cameraId, `${path}.cameraId`),
    startTime,
    endTime,
    captureIds: expectIdArray(record.captureIds, `${path}.captureIds`),
  };
}

function expectOwner(
  value: unknown,
  path: string,
): DirectorProjectOwnerV1 {
  const record = expectRecord(value, path);
  expectExactKeys(record, ["route", "canvasId", "sourceNodeId"], path);
  return {
    route: expectEnum(record.route, ["libtv"], `${path}.route`),
    canvasId: expectString(record.canvasId, `${path}.canvasId`),
    sourceNodeId: expectString(record.sourceNodeId, `${path}.sourceNodeId`),
  };
}

function expectDocument(value: unknown): DirectorProjectDocumentV1 {
  const record = expectRecord(value, "$");
  expectExactKeysWithOptional(
    record,
    [
      "schemaVersion",
      "projectId",
      "owner",
      "scene",
      "objects",
      "groups",
      "activeCameraId",
      "timeline",
      "outputPreferences",
      "resourceRefs",
      "captureDescriptors",
    ],
    ["shots"],
    "$",
  );
  if (record.schemaVersion !== DIRECTOR_PROJECT_SCHEMA_VERSION) {
    if (
      typeof record.schemaVersion === "number" &&
      Number.isFinite(record.schemaVersion) &&
      record.schemaVersion > DIRECTOR_PROJECT_SCHEMA_VERSION
    ) {
      fail(
        "FUTURE_SCHEMA_VERSION",
        "$.schemaVersion",
        `schema version ${String(record.schemaVersion)} is newer than supported version ${String(DIRECTOR_PROJECT_SCHEMA_VERSION)}`,
      );
    }
    fail(
      "INVALID_FIELD",
      "$.schemaVersion",
      `only schema version ${String(DIRECTOR_PROJECT_SCHEMA_VERSION)} is supported`,
    );
  }

  const durationRecord = expectRecord(record.timeline, "$.timeline");
  expectExactKeys(
    durationRecord,
    ["duration", "loop", "autoKeyframe", "tracks", "motionPaths"],
    "$.timeline",
  );
  const duration = expectFiniteNumber(
    durationRecord.duration,
    "$.timeline.duration",
  );
  if (duration <= 0) {
    fail("INVALID_FIELD", "$.timeline.duration", "duration must be positive");
  }

  const objects = expectArray(record.objects, "$.objects").map((item, index) =>
    expectObject(item, `$.objects[${index}]`),
  );
  ensureUniqueIds(objects.map((object) => object.id), "$.objects");
  const groups = expectArray(record.groups, "$.groups").map((item, index) =>
    expectGroup(item, `$.groups[${index}]`),
  );
  ensureUniqueIds(groups.map((group) => group.id), "$.groups");
  const resourceRefs = expectArray(
    record.resourceRefs,
    "$.resourceRefs",
  ).map((item, index) =>
    expectResourceReference(item, `$.resourceRefs[${index}]`),
  );
  ensureUniqueIds(resourceRefs.map((resource) => resource.id), "$.resourceRefs");
  const parsedCaptureDescriptors = expectArray(
    record.captureDescriptors,
    "$.captureDescriptors",
  ).map((item, index) =>
    expectCaptureDescriptor(item, `$.captureDescriptors[${index}]`),
  );
  ensureUniqueIds(
    parsedCaptureDescriptors.map((capture) => capture.id),
    "$.captureDescriptors",
  );
  const legacyDocument = record.shots === undefined;
  const shots =
    legacyDocument
      ? deriveDefaultShots(objects, duration, parsedCaptureDescriptors)
      : expectArray(record.shots, "$.shots").map((item, index) =>
          expectShot(item, `$.shots[${index}]`, duration),
        );
  ensureUniqueIds(
    shots.map((shot) => shot.id),
    "$.shots",
  );
  const shotByCameraId = new Map(
    shots.map((shot) => [shot.cameraId, shot]),
  );
  const captureMembership = new Map(
    shots.flatMap((shot) =>
      shot.captureIds.map((captureId) => [captureId, shot.id] as const),
    ),
  );
  const captureDescriptors = parsedCaptureDescriptors.map((capture) => ({
    ...capture,
    shotId:
      capture.shotId ??
      captureMembership.get(capture.id) ??
      (legacyDocument
        ? shotByCameraId.get(capture.cameraId ?? "")?.id ?? null
        : null),
  }));
  const motionPaths = expectArray(
    durationRecord.motionPaths,
    "$.timeline.motionPaths",
  ).map((item, index) =>
    expectPath(item, `$.timeline.motionPaths[${index}]`),
  );
  ensureUniqueIds(
    motionPaths.map((path) => path.id),
    "$.timeline.motionPaths",
  );
  const tracks = expectArray(
    durationRecord.tracks,
    "$.timeline.tracks",
  ).map((item, index) =>
    expectTrack(item, `$.timeline.tracks[${index}]`, duration),
  );
  ensureUniqueIds(
    tracks.map((track) => track.id),
    "$.timeline.tracks",
  );

  const document: DirectorProjectDocumentV1 = {
    schemaVersion: DIRECTOR_PROJECT_SCHEMA_VERSION,
    projectId: expectString(record.projectId, "$.projectId"),
    owner: expectOwner(record.owner, "$.owner"),
    scene: expectScene(record.scene, "$.scene"),
    objects,
    groups,
    shots,
    activeCameraId: expectString(record.activeCameraId, "$.activeCameraId"),
    timeline: {
      duration,
      loop: expectBoolean(durationRecord.loop, "$.timeline.loop"),
      autoKeyframe: expectBoolean(
        durationRecord.autoKeyframe,
        "$.timeline.autoKeyframe",
      ),
      tracks,
      motionPaths,
    },
    outputPreferences: expectOutputPreferences(record.outputPreferences),
    resourceRefs,
    captureDescriptors,
  };
  validateReferences(document);
  return document;
}

function expectOutputPreferences(
  value: unknown,
): DirectorProjectDocumentV1["outputPreferences"] {
  const record = expectRecord(value, "$.outputPreferences");
  expectExactKeys(record, ["aspectRatio"], "$.outputPreferences");
  return {
    aspectRatio: expectEnum(
      record.aspectRatio,
      DIRECTOR_ASPECT_RATIOS,
      "$.outputPreferences.aspectRatio",
    ),
  };
}

function ensureUniqueIds(ids: string[], path: string): void {
  const seen = new Set<string>();
  ids.forEach((id, index) => {
    if (seen.has(id)) {
      fail("DUPLICATE_ID", `${path}[${index}]`, `duplicate ID "${id}"`);
    }
    seen.add(id);
  });
}

function requireReference(
  ids: Set<string>,
  id: string | null,
  path: string,
  kind: string,
): void {
  if (id !== null && !ids.has(id)) {
    fail(
      "DANGLING_REFERENCE",
      path,
      `${kind} reference "${id}" does not exist`,
    );
  }
}

function validateReferences(document: DirectorProjectDocumentV1): void {
  const objectById = new Map(document.objects.map((object) => [object.id, object]));
  const objectIds = new Set(objectById.keys());
  const characterIds = new Set(
    document.objects
      .filter((object) => object.kind === "character")
      .map((object) => object.id),
  );
  const cameraIds = new Set(
    document.objects
      .filter((object) => object.kind === "camera")
      .map((object) => object.id),
  );
  const groupById = new Map(document.groups.map((group) => [group.id, group]));
  const groupIds = new Set(groupById.keys());
  const pathIds = new Set(document.timeline.motionPaths.map((path) => path.id));
  const resourceIds = new Set(document.resourceRefs.map((resource) => resource.id));

  if (document.objects.length === 0) {
    fail("INVALID_FIELD", "$.objects", "a project needs at least one object");
  }
  if (!cameraIds.has(document.activeCameraId)) {
    fail(
      "DANGLING_REFERENCE",
      "$.activeCameraId",
      `active camera "${document.activeCameraId}" does not exist`,
    );
  }

  const membersAcrossGroups = new Set<string>();
  document.groups.forEach((group, groupIndex) => {
    group.characterIds.forEach((characterId, memberIndex) => {
      if (!characterIds.has(characterId)) {
        fail(
          "DANGLING_REFERENCE",
          `$.groups[${groupIndex}].characterIds[${memberIndex}]`,
          `character reference "${characterId}" does not exist`,
        );
      }
      if (membersAcrossGroups.has(characterId)) {
        fail(
          "INVALID_FIELD",
          `$.groups[${groupIndex}].characterIds[${memberIndex}]`,
          `character "${characterId}" cannot belong to multiple groups`,
        );
      }
      membersAcrossGroups.add(characterId);
    });
    if (group.characterIds.length === 0) {
      fail(
        "INVALID_FIELD",
        `$.groups[${groupIndex}].characterIds`,
        "groups need at least one character",
      );
    }
  });

  document.objects.forEach((object, objectIndex) => {
    requireReference(
      resourceIds,
      object.assetRefId,
      `$.objects[${objectIndex}].assetRefId`,
      "resource",
    );
    if (object.kind === "camera" && object.primitive !== "camera") {
      fail(
        "INVALID_FIELD",
        `$.objects[${objectIndex}].primitive`,
        "camera objects must use the camera primitive",
      );
    }
    if (object.kind === "character" && object.primitive !== "character") {
      fail(
        "INVALID_FIELD",
        `$.objects[${objectIndex}].primitive`,
        "character objects must use the character primitive",
      );
    }
    if (object.camera) {
      requireReference(
        objectIds,
        object.camera.lookAtObjectId,
        `$.objects[${objectIndex}].camera.lookAtObjectId`,
        "look-at object",
      );
      requireReference(
        objectIds,
        object.camera.followTargetId,
        `$.objects[${objectIndex}].camera.followTargetId`,
        "follow target",
      );
    }
  });

  document.captureDescriptors.forEach((capture, captureIndex) => {
    requireReference(
      cameraIds,
      capture.cameraId,
      `$.captureDescriptors[${captureIndex}].cameraId`,
      "capture camera",
    );
    requireReference(
      resourceIds,
      capture.resourceRefId,
      `$.captureDescriptors[${captureIndex}].resourceRefId`,
      "capture resource",
    );
  });

  const shotIds = new Set(document.shots.map((shot) => shot.id));
  const captureIds = new Set(
    document.captureDescriptors.map((capture) => capture.id),
  );
  const shotCameraIds = new Set<string>();
  const capturesByShot = new Map<string, string>();
  document.shots.forEach((shot, shotIndex) => {
    requireReference(
      cameraIds,
      shot.cameraId,
      `$.shots[${shotIndex}].cameraId`,
      "shot camera",
    );
    if (shotCameraIds.has(shot.cameraId)) {
      fail(
        "INVALID_FIELD",
        `$.shots[${shotIndex}].cameraId`,
        `camera "${shot.cameraId}" cannot own multiple shots`,
      );
    }
    shotCameraIds.add(shot.cameraId);
    shot.captureIds.forEach((captureId, captureIndex) => {
      requireReference(
        captureIds,
        captureId,
        `$.shots[${shotIndex}].captureIds[${captureIndex}]`,
        "shot capture",
      );
      if (capturesByShot.has(captureId)) {
        fail(
          "INVALID_FIELD",
          `$.shots[${shotIndex}].captureIds[${captureIndex}]`,
          `capture "${captureId}" cannot belong to multiple shots`,
        );
      }
      capturesByShot.set(captureId, shot.id);
    });
  });
  cameraIds.forEach((cameraId) => {
    if (!shotCameraIds.has(cameraId)) {
      fail(
        "INVALID_FIELD",
        "$.shots",
        `camera "${cameraId}" must have a shot`,
      );
    }
  });
  document.captureDescriptors.forEach((capture, captureIndex) => {
    const shotId = capture.shotId;
    if (shotId !== null && !shotIds.has(shotId)) {
      fail(
        "DANGLING_REFERENCE",
        `$.captureDescriptors[${captureIndex}].shotId`,
        `capture shot "${shotId}" does not exist`,
      );
    }
    const membership = capturesByShot.get(capture.id) ?? null;
    if (shotId !== null && membership !== null && shotId !== membership) {
      fail(
        "INVALID_FIELD",
        `$.captureDescriptors[${captureIndex}].shotId`,
        "capture shot provenance must match shot membership",
      );
    }
    if (membership !== null && capture.shotId === null) {
      fail(
        "INVALID_FIELD",
        `$.captureDescriptors[${captureIndex}].shotId`,
        "shot captures must carry matching shot provenance",
      );
    }
    if (
      capture.cameraId !== null &&
      capture.shotId !== null &&
      document.shots.find((shot) => shot.id === capture.shotId)?.cameraId !==
        capture.cameraId
    ) {
      fail(
        "INVALID_FIELD",
        `$.captureDescriptors[${captureIndex}].shotId`,
        "capture shot must belong to the capture camera",
      );
    }
  });

  const keyframeIds = new Set<string>();
  document.timeline.tracks.forEach((track, trackIndex) => {
    if (track.kind === "group") {
      if (track.objectId !== track.groupId) {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].objectId`,
          "group track objectId must equal groupId",
        );
      }
      if (!groupIds.has(track.groupId)) {
        fail(
          "DANGLING_REFERENCE",
          `$.timeline.tracks[${trackIndex}].groupId`,
          `group "${track.groupId}" does not exist`,
        );
      }
      const group = groupById.get(track.groupId);
      if (!group) {
        fail(
          "DANGLING_REFERENCE",
          `$.timeline.tracks[${trackIndex}].groupId`,
          `group "${track.groupId}" does not exist`,
        );
      }
      const memberIds = new Set(group.characterIds);
      Object.keys(track.memberOffsets).forEach((memberId) => {
        if (!memberIds.has(memberId)) {
          fail(
            "DANGLING_REFERENCE",
            `$.timeline.tracks[${trackIndex}].memberOffsets.${memberId}`,
            `group member "${memberId}" does not exist in group`,
          );
        }
      });
      if (Object.keys(track.memberOffsets).length !== memberIds.size) {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].memberOffsets`,
          "group track offsets must cover every group member",
        );
      }
    } else {
      const object = objectById.get(track.objectId);
      if (!object) {
        fail(
          "DANGLING_REFERENCE",
          `$.timeline.tracks[${trackIndex}].objectId`,
          `object "${track.objectId}" does not exist`,
        );
      }
      if (track.kind === "camera" && object.kind !== "camera") {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].kind`,
          "camera tracks must target camera objects",
        );
      }
      if (track.kind === "pose" && object.kind !== "character") {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].kind`,
          "pose tracks must target character objects",
        );
      }
      if (track.kind === "transform" && object.kind === "camera") {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].kind`,
          "camera objects need camera tracks",
        );
      }
    }
    requireReference(
      pathIds,
      track.motionPathId,
      `$.timeline.tracks[${trackIndex}].motionPathId`,
      "motion path",
    );
    if (track.motionPathId) {
      const path = document.timeline.motionPaths.find(
        (candidate) => candidate.id === track.motionPathId,
      );
      if (!path || path.objectId !== track.objectId) {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].motionPathId`,
          "motion path must target the same object as its track",
        );
      }
    }
    track.keyframes.forEach((keyframe, keyframeIndex) => {
      if (keyframeIds.has(keyframe.id)) {
        fail(
          "DUPLICATE_ID",
          `$.timeline.tracks[${trackIndex}].keyframes[${keyframeIndex}].id`,
          `duplicate keyframe ID "${keyframe.id}"`,
        );
      }
      keyframeIds.add(keyframe.id);
      if (
        keyframeIndex > 0 &&
        keyframe.time <= track.keyframes[keyframeIndex - 1].time
      ) {
        fail(
          "INVALID_FIELD",
          `$.timeline.tracks[${trackIndex}].keyframes[${keyframeIndex}].time`,
          "keyframe times must be strictly increasing",
        );
      }
    });
  });

  document.timeline.motionPaths.forEach((path, pathIndex) => {
    if (!objectIds.has(path.objectId)) {
      fail(
        "DANGLING_REFERENCE",
        `$.timeline.motionPaths[${pathIndex}].objectId`,
        `object "${path.objectId}" does not exist`,
      );
    }
  });
}

function sortTuple3Map(
  values: Record<string, DirectorTuple3>,
): Record<string, DirectorTuple3> {
  return Object.fromEntries(
    Object.keys(values)
      .sort()
      .map((key) => [key, [...values[key]] as DirectorTuple3]),
  );
}

function cloneTransform(
  transform: DirectorTransform,
): DirectorTransformDocumentV1 {
  return {
    position: [...transform.position],
    rotation: [...transform.rotation],
    scale: [...transform.scale],
  };
}

function cloneControls(
  controls: Record<string, number>,
): Record<string, number> {
  return Object.fromEntries(
    Object.keys(controls)
      .sort()
      .map((key) => [key, controls[key]]),
  );
}

function mapRig(
  rig: DirectorCharacterRig | DirectorPoseKeyframeValue,
): DirectorCharacterRigDocumentV1 {
  return {
    posePresetId: rig.posePresetId,
    controls: cloneControls(rig.controls),
  };
}

function mapCamera(
  camera: NonNullable<DirectorObject["camera"]>,
): DirectorCameraDocumentV1 {
  return {
    fov: camera.fov,
    target: [...camera.target],
    lookAtMode: camera.lookAtMode,
    lookAtObjectId: camera.lookAtObjectId,
    followTargetId: camera.followTargetId,
    followOffset: [...camera.followOffset],
    followView: camera.followView,
  };
}

function mapObject(
  object: DirectorObject,
  resourceRefs: DirectorResourceReferenceV1[],
): DirectorObjectDocumentV1 {
  const matchingResource = object.libraryAssetId
    ? resourceRefs.find((resource) => resource.id === object.libraryAssetId)
    : undefined;
  return {
    id: object.id,
    name: object.name,
    kind: object.kind,
    primitive: object.primitive,
    color: object.color,
    visible: object.visible,
    locked: object.locked,
    transform: cloneTransform(object.transform),
    assetRefId: matchingResource?.id ?? null,
    libraryCategoryId: object.libraryCategoryId ?? null,
    libraryVisual: object.libraryVisual ?? null,
    characterRig: object.characterRig ? mapRig(object.characterRig) : null,
    camera: object.camera ? mapCamera(object.camera) : null,
  };
}

function mapGroup(group: DirectorCharacterGroup): DirectorGroupDocumentV1 {
  return {
    id: group.id,
    label: group.label,
    characterIds: [...group.characterIds],
    crowd: group.crowd
      ? {
          rows: group.crowd.rows,
          columns: group.crowd.columns,
          spacing: group.crowd.spacing,
        }
      : null,
  };
}

function mapKeyframe(
  keyframe:
    | DirectorTransformKeyframe
    | DirectorCameraKeyframe
    | DirectorPoseKeyframe
    | DirectorGroupKeyframe,
): DirectorTransformKeyframeDocumentV1 | DirectorCameraKeyframeDocumentV1 | DirectorPoseKeyframeDocumentV1 | DirectorGroupKeyframeDocumentV1 {
  if ("fov" in keyframe.value) {
    return {
      id: keyframe.id,
      time: keyframe.time,
      value: {
        transform: cloneTransform(keyframe.value.transform),
        target: [...keyframe.value.target],
        fov: keyframe.value.fov,
      },
    };
  }
  if ("posePresetId" in keyframe.value) {
    return {
      id: keyframe.id,
      time: keyframe.time,
      value: mapRig(keyframe.value),
    };
  }
  return {
    id: keyframe.id,
    time: keyframe.time,
    value: cloneTransform(keyframe.value),
  };
}

function mapTrack(
  track: DirectorTimelineTrack,
): DirectorTimelineTrackDocumentV1 {
  const base = {
    id: track.id,
    objectId: track.objectId,
    label: track.label,
    motionPathId: track.motionPathId ?? null,
    speedCurve: {
      preset: track.speedCurve.preset,
      control1: [...track.speedCurve.control1] as [number, number],
      control2: [...track.speedCurve.control2] as [number, number],
    },
  };
  if (track.kind === "group") {
    return {
      ...base,
      kind: "group",
      groupId: track.groupId,
      memberOffsets: sortTuple3Map(track.memberOffsets),
      keyframes: track.keyframes.map(mapKeyframe) as DirectorGroupKeyframeDocumentV1[],
    };
  }
  if (track.kind === "camera") {
    return {
      ...base,
      kind: "camera",
      keyframes: track.keyframes.map(mapKeyframe) as DirectorCameraKeyframeDocumentV1[],
    };
  }
  if (track.kind === "pose") {
    return {
      ...base,
      kind: "pose",
      keyframes: track.keyframes.map(mapKeyframe) as DirectorPoseKeyframeDocumentV1[],
    };
  }
  return {
    ...base,
    kind: "transform",
    keyframes: track.keyframes.map(mapKeyframe) as DirectorTransformKeyframeDocumentV1[],
  };
}

function mapAnchor(
  anchor: DirectorMotionPath["anchors"][number],
): DirectorMotionPathAnchorDocumentV1 {
  return {
    id: anchor.id,
    position: [...anchor.position],
    type: anchor.type,
    handleIn: [...anchor.handleIn],
    handleOut: [...anchor.handleOut],
  };
}

function mapPath(path: DirectorMotionPath): DirectorMotionPathDocumentV1 {
  return {
    id: path.id,
    objectId: path.objectId,
    name: path.name,
    preset: path.preset,
    enabled: path.enabled,
    orientToPath: path.orientToPath,
    closed: path.closed,
    pivot: [...path.pivot],
    transform: cloneTransform(path.transform),
    initialAnchors: path.initialAnchors.map(mapAnchor),
    anchors: path.anchors.map(mapAnchor),
  };
}

function createResourceReferences(
  objects: DirectorObject[],
  explicit: DirectorResourceReferenceV1[],
): DirectorResourceReferenceV1[] {
  const refs = new Map(explicit.map((resource) => [resource.id, resource]));
  objects.forEach((object) => {
    if (!object.libraryAssetId || refs.has(object.libraryAssetId)) return;
    refs.set(object.libraryAssetId, {
      id: object.libraryAssetId,
      kind: "model",
      source: object.librarySource === "local" ? "local" : "catalog",
      label: object.libraryFileName ?? object.name,
      locator: object.libraryAssetId,
      mimeType: null,
    });
  });
  return [...refs.values()];
}

function mapCapture(capture: DirectorCapture): DirectorCaptureDescriptorV1 {
  return {
    id: capture.id,
    cameraId: capture.cameraId,
    shotId: capture.shotId ?? null,
    cameraName: capture.cameraName,
    aspectRatio: capture.aspectRatio,
    width: capture.width,
    height: capture.height,
    createdAt: capture.createdAt,
    resourceRefId: null,
  };
}

export function createDirectorProjectDocumentV1(
  input: DirectorProjectSnapshotInput,
): DirectorProjectDocumentV1 {
  const resourceRefs = createResourceReferences(
    input.objects,
    input.resourceRefs ?? [],
  );
  const captureDescriptors = (input.captures ?? []).map(mapCapture);
  const document: DirectorProjectDocumentV1 = {
    schemaVersion: DIRECTOR_PROJECT_SCHEMA_VERSION,
    projectId: input.projectId,
    owner: {
      route: "libtv",
      canvasId: input.owner.canvasId,
      sourceNodeId: input.owner.sourceNodeId,
    },
    scene: {
      name: input.scene.name,
      backgroundColor: input.scene.backgroundColor,
      groundColor: input.scene.groundColor,
      showGround: input.scene.showGround,
      showGrid: input.scene.showGrid,
    },
    objects: input.objects.map((object) => mapObject(object, resourceRefs)),
    groups: input.groups.map(mapGroup),
    shots:
      input.shots?.map((shot) => ({
        id: shot.id,
        name: shot.name,
        cameraId: shot.cameraId,
        startTime: shot.startTime,
        endTime: shot.endTime,
        captureIds: [...shot.captureIds],
      })) ??
      deriveDefaultShots(
        input.objects.map((object) => mapObject(object, resourceRefs)),
        input.timeline.duration,
        captureDescriptors,
      ),
    activeCameraId: input.activeCameraId,
    timeline: {
      duration: input.timeline.duration,
      loop: input.timeline.loop,
      autoKeyframe: input.timeline.autoKeyframe,
      tracks: input.timeline.tracks.map(mapTrack),
      motionPaths: input.timeline.motionPaths.map(mapPath),
    },
    outputPreferences: {
      aspectRatio: input.aspectRatio,
    },
    resourceRefs,
    captureDescriptors,
  };
  return normalizeDirectorProjectDocument(document);
}

export function normalizeDirectorProjectDocument(
  document: DirectorProjectDocumentV1,
): DirectorProjectDocumentV1 {
  const result = decodeDirectorProjectDocument(document);
  if (!result.ok) {
    throw new Error(
      `${result.error.code} at ${result.error.path}: ${result.error.message}`,
    );
  }
  return result.document;
}

export function decodeDirectorProjectDocument(
  input: unknown,
): DirectorProjectDocumentDecodeResult {
  try {
    return { ok: true, document: expectDocument(input) };
  } catch (error) {
    if (error instanceof DocumentDecodeFailure) {
      return { ok: false, error: error.error };
    }
    throw error;
  }
}

export function encodeDirectorProjectDocument(
  document: DirectorProjectDocumentV1,
): string {
  return JSON.stringify(normalizeDirectorProjectDocument(document));
}

export function rebindDirectorProjectDocumentV1(
  document: DirectorProjectDocumentV1,
  target: {
    projectId: string;
    owner: DirectorProjectOwnerV1;
  },
): DirectorProjectDocumentV1 {
  const normalized = normalizeDirectorProjectDocument(document);
  return normalizeDirectorProjectDocument({
    ...normalized,
    projectId: target.projectId,
    owner: {
      route: "libtv",
      canvasId: target.owner.canvasId,
      sourceNodeId: target.owner.sourceNodeId,
    },
  });
}
