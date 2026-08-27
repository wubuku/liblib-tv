"use client";

import { create } from "zustand";
import {
  clampDirectorTimelineTime,
  sampleDirectorTimelineTrack,
} from "@/components/director/directorTimelineMath";
import {
  isFiniteDirectorCameraValue,
  mapDirectorPhonePoseToCamera,
  type DirectorPhoneVcamPose,
} from "@/components/director/directorPhoneVcamMath";
import {
  applyDirectorPosePreset,
  cloneDirectorCharacterRig,
  cloneDirectorPoseValue,
  createDirectorCharacterRig,
  updateDirectorPoseControl,
  type DirectorCharacterRig,
  type DirectorPoseKeyframeValue,
  type DirectorPosePresetId,
} from "@/components/director/directorPose";
import {
  buildDirectorMotionPathWorldAnchors,
  buildDirectorMotionPathPoints,
  cloneDirectorMotionPathAnchors,
  createDirectorMotionPathAnchor,
  createDirectorMotionPathTransform,
  createDirectorSpeedCurve,
  getDirectorMotionPathPivot,
  getDirectorPathYaw,
  getDirectorTrackProgress,
  inverseTransformDirectorMotionPathPoint,
  inverseTransformDirectorMotionPathVector,
  isDirectorMotionPathValid,
  sampleDirectorMotionPath,
  setDirectorMotionPathAnchorType,
  transformDirectorMotionPathPoint,
} from "@/components/director/directorMotionMath";
import {
  createDirectorCameraRelation,
  resolveDirectorCameraRelation,
  type DirectorCameraFollowView,
  type DirectorCameraLookAtMode,
} from "@/components/director/directorCameraFollow";
import {
  createDirectorCameraMotionPresetValues,
  type DirectorCameraMotionPresetId,
  type DirectorCameraMotionPresetMode,
} from "@/components/director/directorCameraPresets";
import {
  applyDirectorGroupTransform,
  createDirectorCrowdPositions,
  getDirectorGroupAnchorTransform,
  getDirectorGroupMemberOffsets,
} from "@/components/director/directorGroupMath";
import type {
  DirectorModelLibraryCategoryId,
  DirectorLocalModelLibraryItem,
  DirectorModelLibraryCardItem,
  DirectorModelLibraryVisual,
} from "@/components/director/directorModelLibrary";
import {
  createDirectorProjectDocumentV1,
  normalizeDirectorProjectDocument,
  type DirectorProjectOwnerV1,
} from "@/lib/directorProjectDocument";
import {
  DirectorProjectRegistry,
  isSameDirectorProjectOwner,
  type DirectorProjectCloseResult,
  type DirectorProjectLifecycle,
  type DirectorProjectOpenResult,
  type DirectorProjectRegistrySnapshot,
  type DirectorSessionV1,
} from "@/lib/directorProjectRegistry";
import { restoreDirectorProjectRuntimeSnapshotV1 } from "@/lib/directorProjectRuntimeAdapter";
import {
  directorProjectPersistence,
  getDirectorProjectPersistenceSnapshot,
} from "@/lib/directorProjectPersistence";
import {
  cloneDirectorHistoryState,
  createDirectorCommandResult,
  createDirectorGesture,
  createDirectorHistoryEntry,
  createDirectorHistoryState,
  directorDocumentFingerprint,
  pushDirectorHistory,
  type DirectorCommandResult,
  type DirectorHistoryState,
} from "@/lib/directorCommandKernel";
import {
  createDirectorAsyncIdentity,
  directorAsyncAuthority,
  type DirectorAsyncIngressContextV1,
  type DirectorAsyncOwnerSnapshotV1,
  type DirectorAsyncResultEnvelopeV1,
} from "@/lib/directorAsyncAuthority";
import type { DirectorProjectDocumentV1 } from "@/lib/directorProjectDocument";
import {
  buildDirectorClipboardPacket,
  planDirectorClipboardPaste,
  type DirectorClipboardPacketV1,
  type DirectorClipboardPastePlan,
} from "@/lib/directorClipboard";
import {
  planDirectorDelete,
  type DirectorDeleteCommand,
  type DirectorDeletePlan,
  type DirectorResourceDeletePolicy,
} from "@/lib/directorDeletePlanner";

export type DirectorTuple3 = [number, number, number];
export type DirectorViewMode = "director" | "camera";
export type DirectorTransformMode = "translate" | "rotate" | "scale";
export type DirectorAspectRatio = "16:9" | "9:16" | "1:1";
export type DirectorObjectKind = "character" | "prop" | "camera";
export type DirectorPrimitive =
  | "character"
  | "table"
  | "mug"
  | "wall"
  | "camera"
  | "library";
export type { DirectorCameraFollowView, DirectorCameraLookAtMode };
export type {
  DirectorCameraMotionPresetId,
  DirectorCameraMotionPresetMode,
};

export interface DirectorTransform {
  position: DirectorTuple3;
  rotation: DirectorTuple3;
  scale: DirectorTuple3;
}

export interface DirectorObject {
  id: string;
  name: string;
  kind: DirectorObjectKind;
  primitive: DirectorPrimitive;
  color: string;
  visible: boolean;
  locked: boolean;
  transform: DirectorTransform;
  libraryAssetId?: string;
  libraryCategoryId?: DirectorModelLibraryCategoryId;
  libraryVisual?: DirectorModelLibraryVisual;
  librarySource?: "catalog" | "local";
  libraryFileName?: string;
  characterRig?: DirectorCharacterRig;
  camera?: {
    fov: number;
    target: DirectorTuple3;
    lookAtMode: DirectorCameraLookAtMode;
    lookAtObjectId: string | null;
    followTargetId: string | null;
    followOffset: DirectorTuple3;
    followView: DirectorCameraFollowView;
  };
}

export interface DirectorCharacterGroup {
  id: string;
  label: string;
  characterIds: string[];
  crowd?: {
    rows: number;
    columns: number;
    spacing: number;
  };
}

export interface DirectorScene {
  name: string;
  backgroundColor: string;
  groundColor: string;
  showGround: boolean;
  showGrid: boolean;
}

export interface DirectorCapture {
  id: string;
  dataUrl: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: DirectorAspectRatio;
  width: number;
  height: number;
  createdAt: string;
  sentNodeId?: string;
}

export interface DirectorTransformKeyframe {
  id: string;
  time: number;
  value: DirectorTransform;
}

export interface DirectorCameraKeyframeValue {
  transform: DirectorTransform;
  target: DirectorTuple3;
  fov: number;
}

export interface DirectorCameraKeyframe {
  id: string;
  time: number;
  value: DirectorCameraKeyframeValue;
}

export interface DirectorPoseKeyframe {
  id: string;
  time: number;
  value: DirectorPoseKeyframeValue;
}

export interface DirectorGroupKeyframe {
  id: string;
  time: number;
  value: DirectorTransform;
}

export type DirectorPhoneVcamStatus =
  | "idle"
  | "preparing"
  | "waiting"
  | "local-ready"
  | "recording"
  | "imported"
  | "error";

export interface DirectorPhoneVcamSample {
  time: number;
  value: DirectorCameraKeyframeValue;
}

export interface DirectorPhoneVcamState {
  status: DirectorPhoneVcamStatus;
  gyroEnabled: boolean;
  stability: number;
  keepLevel: boolean;
  hold: boolean;
  elevation: number;
  pose: DirectorPhoneVcamPose;
  baselineCamera: DirectorCameraKeyframeValue | null;
  recordingStartTime: number | null;
  sampleCount: number;
  takeCount: number;
  importedCameraId: string | null;
  importedTrackId: string | null;
  error: string | null;
}

export interface DirectorPhoneVcamImportResult {
  cameraId: string;
  trackId: string;
}

export type DirectorSpeedCurvePreset =
  | "linear"
  | "smooth"
  | "ease-in"
  | "ease-out"
  | "ease-in-out"
  | "custom";

export interface DirectorSpeedCurve {
  preset: DirectorSpeedCurvePreset;
  control1: [number, number];
  control2: [number, number];
}

export type DirectorMotionPathPreset =
  | "line"
  | "ring"
  | "rectangle"
  | "pencil"
  | "pen";
export type DirectorMotionPathGeometryPreset = Exclude<
  DirectorMotionPathPreset,
  "pencil" | "pen"
>;
export type DirectorMotionPathDrawTool = "pencil" | "pen";
export type DirectorMotionPathAnchorType =
  | "vertex"
  | "symmetric"
  | "asymmetric";
export type DirectorMotionPathHandle = "in" | "out";

export interface DirectorMotionPathAnchor {
  id: string;
  position: DirectorTuple3;
  type: DirectorMotionPathAnchorType;
  handleIn: DirectorTuple3;
  handleOut: DirectorTuple3;
}

export interface DirectorMotionPath {
  id: string;
  objectId: string;
  name: string;
  preset: DirectorMotionPathPreset;
  enabled: boolean;
  orientToPath: boolean;
  closed: boolean;
  pivot: DirectorTuple3;
  transform: DirectorTransform;
  initialAnchors: DirectorMotionPathAnchor[];
  anchors: DirectorMotionPathAnchor[];
  points: DirectorTuple3[];
}

export interface DirectorMotionPathDraft {
  tool: DirectorMotionPathDrawTool;
  trackId: string;
  objectId: string;
  planeY: number;
  anchors: DirectorMotionPathAnchor[];
}

interface DirectorTimelineTrackBase {
  id: string;
  objectId: string;
  label: string;
  motionPathId?: string;
  speedCurve: DirectorSpeedCurve;
}

export type DirectorTimelineTrack =
  | (DirectorTimelineTrackBase & {
      kind: "transform";
      keyframes: DirectorTransformKeyframe[];
    })
  | (DirectorTimelineTrackBase & {
      kind: "camera";
      keyframes: DirectorCameraKeyframe[];
    })
  | (DirectorTimelineTrackBase & {
      kind: "pose";
      keyframes: DirectorPoseKeyframe[];
    })
  | (DirectorTimelineTrackBase & {
      kind: "group";
      groupId: string;
      memberOffsets: Record<string, DirectorTuple3>;
      keyframes: DirectorGroupKeyframe[];
    });

export interface DirectorTimelineState {
  duration: number;
  currentTime: number;
  isPlaying: boolean;
  loop: boolean;
  zoom: number;
  autoKeyframe: boolean;
  tracks: DirectorTimelineTrack[];
  motionPaths: DirectorMotionPath[];
  selectedTrackId: string | null;
  selectedKeyframeId: string | null;
  selectedMotionPathId: string | null;
  selectedMotionPathAnchorId: string | null;
  selectedMotionPathHandle: DirectorMotionPathHandle | null;
  motionPathDraft: DirectorMotionPathDraft | null;
  editorMode: "timeline" | "curve";
  cameraMotionPreset: {
    application: {
      trackId: string;
      preset: DirectorCameraMotionPresetId;
      mode: DirectorCameraMotionPresetMode;
      startTime: number;
      endTime: number;
      generatedKeyframeIds: string[];
    } | null;
    error: {
      trackId: string;
      preset: DirectorCameraMotionPresetId;
      mode: DirectorCameraMotionPresetMode;
      message: string;
    } | null;
  };
}

function createDefaultScene(): DirectorScene {
  return {
    name: "第一集：咖啡馆对峙",
    backgroundColor: "#20252b",
    groundColor: "#30343a",
    showGround: true,
    showGrid: true,
  };
}

export interface DirectorGestureInput {
  commandKind: string;
  targetId?: string | null;
  fieldScope?: string | null;
}

interface DirectorState {
  sourceNodeId: string | null;
  projectOwner: DirectorProjectOwnerV1 | null;
  projectId: string | null;
  sessionId: string | null;
  generation: number | null;
  projectLifecycle: DirectorProjectLifecycle | null;
  scene: DirectorScene;
  authoredObjects: DirectorObject[];
  objects: DirectorObject[];
  groups: DirectorCharacterGroup[];
  selectedObjectId: string | null;
  selectedObjectIds: string[];
  selectedGroupId: string | null;
  activeCameraId: string;
  viewMode: DirectorViewMode;
  transformMode: DirectorTransformMode;
  aspectRatio: DirectorAspectRatio;
  showThirds: boolean;
  viewportPanelsCollapsed: boolean;
  isCapturing: boolean;
  captures: DirectorCapture[];
  activeCaptureId: string | null;
  localModelLibrary: DirectorLocalModelLibraryItem[];
  timeline: DirectorTimelineState;
  phoneVcam: DirectorPhoneVcamState;
  history: DirectorHistoryState;
  clipboard: DirectorClipboardPacketV1 | null;
  clipboardPasteCount: number;
  lastCommandResult: DirectorCommandResult | null;

  openSession: (owner: DirectorProjectOwnerV1) => DirectorProjectOpenResult;
  closeSession: (
    expectedOwner?: DirectorProjectOwnerV1,
  ) => DirectorProjectCloseResult;
  beginDirectorGesture: (
    input: DirectorGestureInput,
  ) => DirectorCommandResult;
  commitDirectorGesture: () => DirectorCommandResult;
  cancelDirectorGesture: () => DirectorCommandResult;
  undoDirector: () => DirectorCommandResult;
  redoDirector: () => DirectorCommandResult;
  copyDirectorSelection: () => DirectorCommandResult;
  pasteDirectorClipboard: () => DirectorCommandResult;
  deleteDirectorEntity: (
    command: DirectorDeleteCommand,
  ) => DirectorCommandResult;
  selectObject: (
    objectId: string | null,
    source?: "explicit" | "viewport",
  ) => void;
  toggleObjectSelection: (objectId: string) => void;
  selectGroup: (groupId: string | null) => void;
  groupSelectedCharacters: () => string | null;
  ungroupSelectedCharacters: () => void;
  addCrowdArray: (input: {
    rows: number;
    columns: number;
    spacing: number;
  }) => string | null;
  hydrateLocalModelLibrary: () => void;
  addLocalModelLibraryItem: (item: DirectorLocalModelLibraryItem) => void;
  removeLocalModelLibraryItem: (
    assetId: string,
    policy?: DirectorResourceDeletePolicy,
  ) => DirectorCommandResult;
  addModelLibraryObject: (item: DirectorModelLibraryCardItem) => string;
  updateGroup: (
    groupId: string,
    patch: Partial<Pick<DirectorCharacterGroup, "label">>,
  ) => void;
  updateGroupTransform: (
    groupId: string,
    transform: DirectorTransform,
  ) => void;
  setViewMode: (mode: DirectorViewMode) => void;
  setTransformMode: (mode: DirectorTransformMode) => void;
  setAspectRatio: (ratio: DirectorAspectRatio) => void;
  toggleThirds: () => void;
  toggleViewportPanelsCollapsed: () => void;
  setViewportPanelsCollapsed: (collapsed: boolean) => void;
  updateScene: (patch: Partial<DirectorScene>) => void;
  updateObject: (objectId: string, patch: Partial<Pick<DirectorObject, "name" | "color" | "visible" | "locked">>) => void;
  updateObjectTransform: (
    objectId: string,
    field: keyof DirectorTransform,
    axis: 0 | 1 | 2,
    value: number,
  ) => DirectorCommandResult;
  updateCamera: (
    objectId: string,
    patch: Partial<NonNullable<DirectorObject["camera"]>>,
  ) => void;
  applyCharacterPosePreset: (
    objectId: string,
    presetId: DirectorPosePresetId,
  ) => void;
  updateCharacterPoseControl: (
    objectId: string,
    key: string,
    value: number,
  ) => void;
  setCapturing: (capturing: boolean) => void;
  addCapture: (capture: DirectorCapture) => void;
  selectCapture: (captureId: string | null) => void;
  removeCapture: (captureId: string) => DirectorCommandResult;
  clearCaptures: () => DirectorCommandResult;
  markCaptureSent: (captureId: string, nodeId: string) => void;
  setPhoneVcamStatus: (
    status: DirectorPhoneVcamStatus,
    error?: string | null,
  ) => void;
  connectPhoneVcamLocal: () => boolean;
  setPhoneVcamGyroEnabled: (enabled: boolean) => void;
  setPhoneVcamStability: (stability: number) => void;
  togglePhoneVcamKeepLevel: () => void;
  setPhoneVcamHold: (hold: boolean) => void;
  calibratePhoneVcam: () => void;
  applyPhoneVcamPose: (pose: DirectorPhoneVcamPose) => void;
  elevatePhoneVcam: (delta: number) => void;
  startPhoneVcamRecording: () => boolean;
  setPhoneVcamRecordingTime: (time: number) => void;
  setPhoneVcamSampleCount: (count: number) => void;
  importPhoneVcamTake: (
    samples: DirectorPhoneVcamSample[],
  ) => DirectorPhoneVcamImportResult | null;
  setTimelineTime: (time: number) => void;
  setTimelinePlaying: (playing: boolean) => void;
  advanceTimeline: (deltaSeconds: number) => void;
  toggleTimelineLoop: () => void;
  toggleAutoKeyframe: () => void;
  setTimelineZoom: (zoom: number) => void;
  selectTimelineTrack: (trackId: string) => void;
  selectTimelineKeyframe: (trackId: string, keyframeId: string) => void;
  addTimelineTrack: (objectId?: string) => void;
  removeTimelineTrack: (trackId?: string) => DirectorCommandResult;
  addTimelineKeyframe: (trackId?: string) => void;
  deleteTimelineKeyframe: (keyframeId?: string) => void;
  seekTimelineKeyframe: (direction: -1 | 1) => void;
  recordObjectKeyframe: (objectId: string, force?: boolean) => void;
  recordGroupKeyframe: (groupId: string, force?: boolean) => void;
  setTimelineEditorMode: (mode: "timeline" | "curve") => void;
  setTrackSpeedCurvePreset: (
    trackId: string,
    preset: Exclude<DirectorSpeedCurvePreset, "custom">,
  ) => void;
  setTrackSpeedCurveControl: (
    trackId: string,
    handle: 1 | 2,
    point: [number, number],
  ) => void;
  applyCameraMotionPreset: (
    preset: DirectorCameraMotionPresetId,
    mode: DirectorCameraMotionPresetMode,
    trackId?: string,
  ) => boolean;
  createMotionPath: (
    preset: DirectorMotionPathGeometryPreset,
    trackId?: string,
  ) => void;
  startMotionPathDrawing: (
    tool: DirectorMotionPathDrawTool,
    trackId?: string,
  ) => void;
  appendMotionPathDraftAnchor: (position: DirectorTuple3) => void;
  updateMotionPathDraftLastHandle: (worldPosition: DirectorTuple3) => void;
  finishMotionPathDrawing: () => void;
  cancelMotionPathDrawing: () => void;
  selectMotionPathAnchor: (
    pathId: string,
    anchorId: string,
    handle?: DirectorMotionPathHandle | null,
  ) => void;
  updateMotionPathAnchorPosition: (
    pathId: string,
    anchorId: string,
    position: DirectorTuple3,
  ) => void;
  updateMotionPathAnchorWorldPosition: (
    pathId: string,
    anchorId: string,
    position: DirectorTuple3,
  ) => void;
  updateMotionPathAnchorHandle: (
    pathId: string,
    anchorId: string,
    handle: DirectorMotionPathHandle,
    value: DirectorTuple3,
  ) => void;
  updateMotionPathAnchorWorldHandle: (
    pathId: string,
    anchorId: string,
    handle: DirectorMotionPathHandle,
    position: DirectorTuple3,
  ) => void;
  setMotionPathAnchorType: (
    pathId: string,
    anchorId: string,
    type: DirectorMotionPathAnchorType,
  ) => void;
  insertMotionPathAnchor: (pathId?: string, anchorId?: string) => void;
  deleteMotionPathAnchor: (pathId?: string, anchorId?: string) => void;
  toggleMotionPathClosed: (pathId?: string) => void;
  renameMotionPath: (pathId: string, name: string) => void;
  updateMotionPathTransform: (
    pathId: string,
    field: keyof DirectorTransform,
    axis: 0 | 1 | 2,
    value: number,
  ) => void;
  resetMotionPathOffset: (pathId?: string) => void;
  resetMotionPath: (pathId?: string) => void;
  toggleMotionPathEnabled: (pathId?: string) => void;
  toggleMotionPathOrient: (pathId?: string) => void;
  deleteMotionPath: (pathId?: string) => DirectorCommandResult;
}

const defaultObjects: DirectorObject[] = [
  {
    id: "director-character-lead",
    name: "角色01 · 陈默",
    kind: "character",
    primitive: "character",
    color: "#8696a8",
    visible: true,
    locked: false,
    transform: {
      position: [-1.25, 0, 0.2],
      rotation: [0, 18, 0],
      scale: [1, 1, 1],
    },
    characterRig: createDirectorCharacterRig(),
  },
  {
    id: "director-prop-table",
    name: "咖啡桌",
    kind: "prop",
    primitive: "table",
    color: "#7b6959",
    visible: true,
    locked: false,
    transform: {
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      scale: [1, 1, 1],
    },
  },
  {
    id: "director-prop-mug",
    name: "冷掉的咖啡",
    kind: "prop",
    primitive: "mug",
    color: "#ece7de",
    visible: true,
    locked: false,
    transform: {
      position: [0.25, 1.08, 0.05],
      rotation: [0, -18, 0],
      scale: [1, 1, 1],
    },
  },
  {
    id: "director-prop-wall",
    name: "咖啡馆背景",
    kind: "prop",
    primitive: "wall",
    color: "#394450",
    visible: true,
    locked: false,
    transform: {
      position: [0, 1.5, -2.6],
      rotation: [0, 0, 0],
      scale: [1, 1, 1],
    },
  },
  {
    id: "director-camera-main",
    name: "机位01 · 对峙中景",
    kind: "camera",
    primitive: "camera",
    color: "#9bdcf2",
    visible: true,
    locked: false,
    transform: {
      position: [4.8, 2.65, 6.9],
      rotation: [0, 0, 0],
      scale: [1, 1, 1],
    },
    camera: {
      fov: 43,
      target: [-0.3, 1.15, 0],
      ...createDirectorCameraRelation(),
    },
  },
];

function cloneObjects(): DirectorObject[] {
  return defaultObjects.map((object) => ({
    ...object,
    transform: {
      position: [...object.transform.position],
      rotation: [...object.transform.rotation],
      scale: [...object.transform.scale],
    },
    camera: object.camera
      ? {
          ...object.camera,
          target: [...object.camera.target],
          followOffset: [...object.camera.followOffset],
        }
      : undefined,
    characterRig: object.characterRig
      ? cloneDirectorCharacterRig(object.characterRig)
      : undefined,
  }));
}

const DIRECTOR_LOCAL_MODEL_LIBRARY_STORAGE_KEY =
  "liblib-tv-director-local-model-library-v1";

function isDirectorModelLibraryVisual(
  value: unknown,
): value is DirectorModelLibraryVisual {
  return (
    value === "bottle" ||
    value === "chair" ||
    value === "lamp" ||
    value === "plant" ||
    value === "box"
  );
}

function isLocalModelLibraryItem(
  value: unknown,
): value is DirectorLocalModelLibraryItem {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<DirectorLocalModelLibraryItem>;
  return (
    typeof candidate.id === "string" &&
    candidate.categoryId === "my-models" &&
    typeof candidate.name === "string" &&
    typeof candidate.fileName === "string" &&
    typeof candidate.dataUrl === "string" &&
    isDirectorModelLibraryVisual(candidate.visual) &&
    typeof candidate.color === "string"
  );
}

function readPersistedLocalModelLibrary(): DirectorLocalModelLibraryItem[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(DIRECTOR_LOCAL_MODEL_LIBRARY_STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(isLocalModelLibraryItem) : [];
  } catch {
    return [];
  }
}

function writePersistedLocalModelLibrary(
  items: DirectorLocalModelLibraryItem[],
) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(
      DIRECTOR_LOCAL_MODEL_LIBRARY_STORAGE_KEY,
      JSON.stringify(items),
    );
  } catch {
    // Keep the current session usable when browser storage quota is exceeded.
  }
}

function cloneTransform(transform: DirectorTransform): DirectorTransform {
  return {
    position: [...transform.position],
    rotation: [...transform.rotation],
    scale: [...transform.scale],
  };
}

function cloneCameraValue(
  object: DirectorObject,
): DirectorCameraKeyframeValue | null {
  if (!object.camera) return null;
  return {
    transform: cloneTransform(object.transform),
    target: [...object.camera.target],
    fov: object.camera.fov,
  };
}

function cloneCameraKeyframeValue(
  value: DirectorCameraKeyframeValue,
): DirectorCameraKeyframeValue {
  return {
    transform: cloneTransform(value.transform),
    target: [...value.target],
    fov: value.fov,
  };
}

function createDefaultPhoneVcamState(): DirectorPhoneVcamState {
  return {
    status: "idle",
    gyroEnabled: false,
    stability: 58,
    keepLevel: true,
    hold: false,
    elevation: 0,
    pose: { yaw: 0, pitch: 0, roll: 0 },
    baselineCamera: null,
    recordingStartTime: null,
    sampleCount: 0,
    takeCount: 0,
    importedCameraId: null,
    importedTrackId: null,
    error: null,
  };
}

function createDefaultTimeline(): DirectorTimelineState {
  const objects = cloneObjects();
  const character = objects.find(
    (object) => object.id === "director-character-lead",
  );
  const camera = objects.find((object) => object.id === "director-camera-main");
  if (!character || !camera?.camera) {
    throw new Error("Director timeline fixtures require character and camera");
  }

  return {
    duration: 8,
    currentTime: 0,
    isPlaying: false,
    loop: true,
    zoom: 1,
    autoKeyframe: true,
    tracks: [
      {
        id: "director-track-character-lead-transform",
        kind: "transform",
        objectId: character.id,
        label: `${character.name} · 变换`,
        speedCurve: createDirectorSpeedCurve(),
        keyframes: [
          {
            id: "director-keyframe-character-0",
            time: 0,
            value: cloneTransform(character.transform),
          },
          {
            id: "director-keyframe-character-4",
            time: 4,
            value: {
              position: [0.65, 0, 0.35],
              rotation: [0, -12, 0],
              scale: [1, 1, 1],
            },
          },
          {
            id: "director-keyframe-character-8",
            time: 8,
            value: {
              position: [-0.4, 0, 0.8],
              rotation: [0, -42, 0],
              scale: [1, 1, 1],
            },
          },
        ],
      },
      {
        id: "director-track-camera-main",
        kind: "camera",
        objectId: camera.id,
        label: `${camera.name} · 机位`,
        speedCurve: createDirectorSpeedCurve(),
        keyframes: [
          {
            id: "director-keyframe-camera-0",
            time: 0,
            value: cloneCameraValue(camera)!,
          },
          {
            id: "director-keyframe-camera-4",
            time: 4,
            value: {
              transform: {
                position: [4.1, 2.3, 5.4],
                rotation: [0, 0, 0],
                scale: [1, 1, 1],
              },
              target: [0.2, 1.2, 0],
              fov: 47,
            },
          },
          {
            id: "director-keyframe-camera-8",
            time: 8,
            value: {
              transform: {
                position: [2.9, 1.85, 4.3],
                rotation: [0, 0, 0],
                scale: [1, 1, 1],
              },
              target: [0.1, 1.15, 0.15],
              fov: 52,
            },
          },
        ],
      },
    ],
    motionPaths: [],
    selectedTrackId: "director-track-character-lead-transform",
    selectedKeyframeId: "director-keyframe-character-0",
    selectedMotionPathId: null,
    selectedMotionPathAnchorId: null,
    selectedMotionPathHandle: null,
    motionPathDraft: null,
    editorMode: "timeline",
    cameraMotionPreset: {
      application: null,
      error: null,
    },
  };
}

function createTrackForObject(
  object: DirectorObject,
  time: number,
): DirectorTimelineTrack {
  const id = `director-track-${object.id}`;
  if (object.kind === "camera" && object.camera) {
    return {
      id,
      kind: "camera",
      objectId: object.id,
      label: `${object.name} · 机位`,
      speedCurve: createDirectorSpeedCurve(),
      keyframes: [
        {
          id: `${id}-keyframe-${Math.round(time * 1000)}`,
          time,
          value: cloneCameraValue(object)!,
        },
      ],
    };
  }
  return {
    id,
    kind: "transform",
    objectId: object.id,
    label: `${object.name} · 变换`,
    speedCurve: createDirectorSpeedCurve(),
    keyframes: [
      {
        id: `${id}-keyframe-${Math.round(time * 1000)}`,
        time,
        value: cloneTransform(object.transform),
      },
    ],
  };
}

function createTrackForGroup(
  group: DirectorCharacterGroup,
  objects: DirectorObject[],
  time: number,
): DirectorTimelineTrack | null {
  const transform = getDirectorGroupAnchorTransform(objects, group);
  if (!transform) return null;
  const id = `director-track-${group.id}`;
  return {
    id,
    kind: "group",
    objectId: group.id,
    groupId: group.id,
    label: `${group.label} · 分组`,
    memberOffsets: getDirectorGroupMemberOffsets(objects, group),
    speedCurve: createDirectorSpeedCurve(),
    keyframes: [
      {
        id: `${id}-keyframe-${Math.round(time * 1000)}`,
        time,
        value: cloneTransform(transform),
      },
    ],
  };
}

function createPoseTrackForObject(
  object: DirectorObject,
  time: number,
): DirectorTimelineTrack {
  const id = `director-track-${object.id}-pose`;
  const rig = object.characterRig ?? createDirectorCharacterRig();
  return {
    id,
    kind: "pose",
    objectId: object.id,
    label: `${object.name} · 姿态`,
    speedCurve: createDirectorSpeedCurve(),
    keyframes: [
      {
        id: `${id}-keyframe-${Math.round(time * 1000)}`,
        time,
        value: cloneDirectorPoseValue(rig),
      },
    ],
  };
}

function createMotionPathForTrack(
  object: DirectorObject,
  preset: DirectorMotionPathGeometryPreset,
): DirectorMotionPath {
  const origin: DirectorTuple3 = [...object.transform.position];
  let points: DirectorTuple3[];
  let closed = false;

  if (preset === "ring") {
    const radius = 1.4;
    const centerX = origin[0] - radius;
    points = Array.from({ length: 16 }, (_, index) => {
      const angle = (index / 16) * Math.PI * 2;
      return [
        centerX + Math.cos(angle) * radius,
        origin[1],
        origin[2] + Math.sin(angle) * radius,
      ];
    });
    closed = true;
  } else if (preset === "rectangle") {
    points = [
      origin,
      [origin[0] + 2.6, origin[1], origin[2]],
      [origin[0] + 2.6, origin[1], origin[2] + 1.8],
      [origin[0], origin[1], origin[2] + 1.8],
    ];
    closed = true;
  } else {
    points = [
      origin,
      [origin[0] + 3.2, origin[1], origin[2] + 1.1],
    ];
  }

  const fallbackName =
    object.kind === "camera"
      ? "机位自动帧轨迹"
      : object.kind === "character"
        ? "角色自动帧轨迹"
        : "道具自动帧轨迹";
  const pathId = `director-motion-path-${object.id}-${Date.now()}`;
  const anchors = points.map((point, index) =>
    createDirectorMotionPathAnchor(
      `${pathId}-anchor-${index}`,
      point,
    ),
  );
  const pivot = getDirectorMotionPathPivot(anchors);
  const transform = createDirectorMotionPathTransform();

  return {
    id: pathId,
    objectId: object.id,
    name: fallbackName,
    preset,
    enabled: true,
    orientToPath: false,
    closed,
    pivot,
    transform,
    initialAnchors: cloneDirectorMotionPathAnchors(anchors),
    anchors,
    points: buildDirectorMotionPathPoints(
      buildDirectorMotionPathWorldAnchors(anchors, pivot, transform),
      closed,
    ),
  };
}

function finiteTuple(
  value: DirectorTuple3,
  fallback: DirectorTuple3,
): DirectorTuple3 {
  return value.map((item, index) =>
    Number.isFinite(item) ? item : fallback[index],
  ) as DirectorTuple3;
}

function rebuildMotionPath(
  path: DirectorMotionPath,
  anchors: DirectorMotionPathAnchor[],
  closed = path.closed,
  transform = path.transform,
  pivot = path.pivot,
): DirectorMotionPath {
  return {
    ...path,
    closed,
    transform,
    pivot,
    anchors,
    points: buildDirectorMotionPathPoints(
      buildDirectorMotionPathWorldAnchors(anchors, pivot, transform),
      closed,
    ),
  };
}

function replaceTrackMotionPath(
  timeline: DirectorTimelineState,
  track: DirectorTimelineTrack,
  path: DirectorMotionPath,
): DirectorTimelineState {
  return {
    ...timeline,
    tracks: timeline.tracks.map((item) =>
      item.id === track.id ? { ...item, motionPathId: path.id } : item,
    ) as DirectorTimelineTrack[],
    motionPaths: [
      ...timeline.motionPaths.filter(
        (item) => item.id !== track.motionPathId,
      ),
      path,
    ],
    selectedTrackId: track.id,
    selectedKeyframeId: null,
    selectedMotionPathId: path.id,
    isPlaying: false,
  };
}

function sampleTimelineObjectsAtTime(
  objects: DirectorObject[],
  timeline: DirectorTimelineState,
  time: number,
  groups: DirectorCharacterGroup[] = [],
): DirectorObject[] {
  const tracksByObject = new Map<string, DirectorTimelineTrack[]>();
  timeline.tracks
    .filter((track) => track.kind !== "group")
    .forEach((track) => {
    const tracks = tracksByObject.get(track.objectId) ?? [];
    tracks.push(track);
    tracksByObject.set(track.objectId, tracks);
  });
  const pathsById = new Map(
    timeline.motionPaths.map((path) => [path.id, path]),
  );
  const sampledObjects = objects.map((object) => {
    const tracks = tracksByObject.get(object.id);
    if (!tracks) return object;
    return tracks.reduce<DirectorObject>((sampledObject, track) => {
      const sample = sampleDirectorTimelineTrack(track, time);
      if (!sample) return sampledObject;
      if (sample.kind === "pose") {
        if (sampledObject.kind !== "character") return sampledObject;
        return {
          ...sampledObject,
          characterRig: cloneDirectorPoseValue(sample.pose),
        };
      }
      const path = track.motionPathId
        ? pathsById.get(track.motionPathId)
        : undefined;
      const pathSample =
        path?.enabled === true
          ? sampleDirectorMotionPath(
              path,
              getDirectorTrackProgress(track, time),
            )
          : null;
      if (sample.kind === "camera" && sampledObject.camera) {
        return {
          ...sampledObject,
          transform: {
            ...cloneTransform(sample.transform),
            position: pathSample
              ? [...pathSample.position]
              : [...sample.transform.position],
          },
          camera: {
            ...sampledObject.camera,
            fov: sample.fov,
            target: [...sample.target],
          },
        };
      }
      const transform = cloneTransform(sample.transform);
      if (pathSample) {
        transform.position = [...pathSample.position];
        if (path?.orientToPath) {
          transform.rotation[1] = getDirectorPathYaw(pathSample.tangent);
        }
      }
      return {
        ...sampledObject,
        transform,
      };
    }, object);
  });
  return timeline.tracks
    .filter((track) => track.kind === "group")
    .reduce((currentObjects, track) => {
      const group = groups.find((item) => item.id === track.groupId);
      const sample = sampleDirectorTimelineTrack(track, time);
      if (!group || sample?.kind !== "group") return currentObjects;
      return applyDirectorGroupTransform(
        currentObjects,
        group,
        sample.transform,
      );
    }, sampledObjects);
}

function resolveCameraRelations(objects: DirectorObject[]): DirectorObject[] {
  return objects.map((object) => {
    if (!object.camera) return object;
    const resolution = resolveDirectorCameraRelation({
      position: object.transform.position,
      target: object.camera.target,
      relation: object.camera,
      objects,
    });
    return {
      ...object,
      transform: {
        ...object.transform,
        position: [...resolution.position],
      },
      camera: {
        ...object.camera,
        target: [...resolution.target],
      },
    };
  });
}

function applyTimelineAtTime(
  objects: DirectorObject[],
  timeline: DirectorTimelineState,
  time: number,
  groups: DirectorCharacterGroup[] = [],
): DirectorObject[] {
  return resolveCameraRelations(
    sampleTimelineObjectsAtTime(objects, timeline, time, groups),
  );
}

function projectDirectorRuntimeObjects(
  authoredObjects: DirectorObject[],
  timeline: DirectorTimelineState,
  groups: DirectorCharacterGroup[],
): DirectorObject[] {
  return applyTimelineAtTime(
    authoredObjects,
    timeline,
    timeline.currentTime,
    groups,
  );
}

function upsertTrackKeyframe(
  track: DirectorTimelineTrack,
  object: DirectorObject,
  time: number,
): { track: DirectorTimelineTrack; keyframeId: string } {
  const existing = track.keyframes.find(
    (keyframe) => Math.abs(keyframe.time - time) < 0.001,
  );
  const keyframeId =
    existing?.id ??
    `${track.id}-keyframe-${Math.round(time * 1000)}-${Date.now()}`;

  if (track.kind === "camera") {
    const value = cloneCameraValue(object);
    if (!value) return { track, keyframeId };
    const keyframes = [
      ...track.keyframes.filter((keyframe) => keyframe.id !== existing?.id),
      { id: keyframeId, time, value },
    ].sort((a, b) => a.time - b.time);
    return { track: { ...track, keyframes }, keyframeId };
  }

  if (track.kind === "pose") {
    const value = cloneDirectorPoseValue(
      object.characterRig ?? createDirectorCharacterRig(),
    );
    const keyframes = [
      ...track.keyframes.filter((keyframe) => keyframe.id !== existing?.id),
      { id: keyframeId, time, value },
    ].sort((a, b) => a.time - b.time);
    return { track: { ...track, keyframes }, keyframeId };
  }

  const keyframes = [
    ...track.keyframes.filter((keyframe) => keyframe.id !== existing?.id),
    { id: keyframeId, time, value: cloneTransform(object.transform) },
  ].sort((a, b) => a.time - b.time);
  return { track: { ...track, keyframes }, keyframeId };
}

function upsertGroupTrackKeyframe(
  track: Extract<DirectorTimelineTrack, { kind: "group" }>,
  transform: DirectorTransform,
  time: number,
): {
  track: Extract<DirectorTimelineTrack, { kind: "group" }>;
  keyframeId: string;
} {
  const existing = track.keyframes.find(
    (keyframe) => Math.abs(keyframe.time - time) < 0.001,
  );
  const keyframeId =
    existing?.id ??
    `${track.id}-keyframe-${Math.round(time * 1000)}-${Date.now()}`;
  const keyframes = [
    ...track.keyframes.filter((keyframe) => keyframe.id !== existing?.id),
    { id: keyframeId, time, value: cloneTransform(transform) },
  ].sort((left, right) => left.time - right.time);
  return { track: { ...track, keyframes }, keyframeId };
}

function updateCharacterRigAndTimeline(
  state: DirectorState,
  objectId: string,
  rig: DirectorCharacterRig,
): Partial<DirectorState> {
  const object = state.authoredObjects.find(
    (item) => item.id === objectId && item.kind === "character",
  );
  if (!object) return state;
  const updatedObject: DirectorObject = {
    ...object,
    characterRig: cloneDirectorCharacterRig(rig),
  };
  const authoredObjects = state.authoredObjects.map((item) =>
    item.id === object.id ? updatedObject : item,
  );
  const existing = state.timeline.tracks.find(
    (track) => track.objectId === object.id && track.kind === "pose",
  );
  const baseTrack =
    existing ??
    createPoseTrackForObject(updatedObject, state.timeline.currentTime);
  const result = upsertTrackKeyframe(
    baseTrack,
    updatedObject,
    state.timeline.currentTime,
  );
  const tracks = existing
    ? state.timeline.tracks.map((track) =>
        track.id === existing.id ? result.track : track,
      )
    : [...state.timeline.tracks, result.track];
  const timeline = {
    ...state.timeline,
    tracks,
    selectedTrackId: result.track.id,
    selectedKeyframeId: result.keyframeId,
    selectedMotionPathId: null,
    selectedMotionPathAnchorId: null,
    selectedMotionPathHandle: null,
    motionPathDraft: null,
    isPlaying: false,
  };
  return {
    authoredObjects,
    objects: projectDirectorRuntimeObjects(
      authoredObjects,
      timeline,
      state.groups,
    ),
    timeline,
  };
}

function updateTuple(
  tuple: DirectorTuple3,
  axis: 0 | 1 | 2,
  value: number,
): DirectorTuple3 {
  const next: DirectorTuple3 = [...tuple];
  next[axis] = Number.isFinite(value) ? value : tuple[axis];
  return next;
}

const DIRECTOR_CROWD_COLORS = [
  "#7f91a5",
  "#9c7f75",
  "#728b7f",
  "#9a8b68",
  "#7e7897",
  "#8f7588",
];

const directorProjectRegistry = new DirectorProjectRegistry({
  normalizeDocument: normalizeDirectorProjectDocument,
});

const directorHistoryByProject = new Map<string, DirectorHistoryState>();
const directorCaptureArchives = new Map<
  string,
  Map<string, DirectorCapture>
>();
let directorHistorySyncSuspended = false;

interface DirectorDocumentSnapshot {
  document: DirectorProjectDocumentV1;
  fingerprint: string;
  projectId: string;
  generation: number;
}

function getDirectorSelectionResult(
  state: DirectorState,
): {
  selectedObjectId: string | null;
  selectedObjectIds: string[];
  selectedGroupId: string | null;
} {
  return {
    selectedObjectId: state.selectedObjectId,
    selectedObjectIds: [...state.selectedObjectIds],
    selectedGroupId: state.selectedGroupId,
  };
}

function getDirectorDocumentSnapshot(
  state: DirectorState,
): DirectorDocumentSnapshot | null {
  const session = directorProjectRegistry.getActiveSession();
  if (
    !session ||
    !state.projectOwner ||
    state.projectId !== session.projectId ||
    state.generation !== session.generation ||
    !isSameDirectorProjectOwner(state.projectOwner, session.owner)
  ) {
    return null;
  }
  try {
    const document = snapshotCurrentDirectorProject(state, session);
    return {
      document,
      fingerprint: directorDocumentFingerprint(document),
      projectId: session.projectId,
      generation: session.generation,
    };
  } catch {
    return null;
  }
}

function getDirectorAsyncContext(
  state: DirectorState,
): DirectorAsyncIngressContextV1 | null {
  if (
    !state.projectOwner ||
    !state.projectId ||
    !state.sessionId ||
    state.generation === null
  ) {
    return null;
  }
  const record = directorProjectRegistry
    .getSnapshot()
    .records.find(
      (candidate) => candidate.identity.projectId === state.projectId,
    );
  if (!record) return null;
  const owner: DirectorAsyncOwnerSnapshotV1 = {
    owner: { ...state.projectOwner },
    projectId: state.projectId,
    sessionId: state.sessionId,
    generation: state.generation,
  };
  return {
    owner,
    sourceFingerprint: directorDocumentFingerprint(record.document),
  };
}

function rememberDirectorCaptures(
  projectId: string,
  captures: DirectorCapture[],
): void {
  const archive =
    directorCaptureArchives.get(projectId) ??
    new Map<string, DirectorCapture>();
  captures.forEach((capture) => archive.set(capture.id, { ...capture }));
  directorCaptureArchives.set(projectId, archive);
}

function capturesForDirectorDocument(
  projectId: string,
  document: DirectorProjectDocumentV1,
  fallback: DirectorCapture[],
): DirectorCapture[] {
  rememberDirectorCaptures(projectId, fallback);
  const archive = directorCaptureArchives.get(projectId);
  if (!archive) return [];
  return document.captureDescriptors
    .map((descriptor) => {
      const capture = archive.get(descriptor.id);
      if (!capture) return null;
      return {
        ...capture,
        cameraId: descriptor.cameraId,
        cameraName: descriptor.cameraName,
        aspectRatio: descriptor.aspectRatio,
        width: descriptor.width,
        height: descriptor.height,
        createdAt: descriptor.createdAt,
      };
    })
    .filter((capture): capture is DirectorCapture => Boolean(capture));
}

function historyForDirectorProject(projectId: string): DirectorHistoryState {
  const history = directorHistoryByProject.get(projectId);
  if (!history) return createDirectorHistoryState();
  const cloned = cloneDirectorHistoryState(history);
  cloned.activeGesture = null;
  return cloned;
}

function rememberDirectorHistory(
  projectId: string,
  history: DirectorHistoryState,
): void {
  const cloned = cloneDirectorHistoryState(history);
  cloned.activeGesture = null;
  directorHistoryByProject.set(projectId, cloned);
}

function updateActiveDirectorDocument(
  state: DirectorState,
  document: DirectorProjectDocumentV1,
  captures: DirectorCapture[],
): boolean {
  const session = directorProjectRegistry.getActiveSession();
  if (
    !session ||
    !state.projectOwner ||
    state.projectId !== session.projectId ||
    state.generation !== session.generation ||
    !isSameDirectorProjectOwner(state.projectOwner, session.owner)
  ) {
    return false;
  }
  rememberDirectorCaptures(session.projectId, captures);
  const result = directorProjectRegistry.updateActive({
    owner: session.owner,
    projectId: session.projectId,
    generation: session.generation,
    document,
    captures,
  });
  if (result.disposition !== "COMMITTED") return false;
  directorProjectPersistence.save({
    owner: session.owner,
    projectId: session.projectId,
    generation: session.generation,
    document,
  });
  return true;
}

function restoreDirectorDocumentState(
  state: DirectorState,
  document: DirectorProjectDocumentV1,
): Partial<DirectorState> | null {
  const session = directorProjectRegistry.getActiveSession();
  if (
    !session ||
    !state.projectOwner ||
    state.projectId !== session.projectId ||
    state.generation !== session.generation ||
    !isSameDirectorProjectOwner(state.projectOwner, session.owner)
  ) {
    return null;
  }
  const record = directorProjectRegistry.getRecord(session.owner);
  if (!record) return null;
  const captures = capturesForDirectorDocument(
    session.projectId,
    document,
    record.memory.captures,
  );
  return restoreDirectorProjectState(
    {
      ...record,
      document,
      memory: { captures },
    },
    session,
    state.localModelLibrary,
  );
}

function makeDirectorCommandResult(
  state: DirectorState,
  input: Omit<
    Parameters<typeof createDirectorCommandResult>[0],
    "projectId" | "generation"
  > & {
    projectId?: string | null;
    generation?: number | null;
  },
): DirectorCommandResult {
  return createDirectorCommandResult({
    ...input,
    projectId: input.projectId ?? state.projectId,
    generation: input.generation ?? state.generation,
    selectionResult:
      input.selectionResult === undefined
        ? getDirectorSelectionResult(state)
        : input.selectionResult,
  });
}

function createDefaultDirectorProjectDocument(
  projectId: string,
  owner: DirectorProjectOwnerV1,
) {
  return createDirectorProjectDocumentV1({
    projectId,
    owner,
    scene: createDefaultScene(),
    objects: cloneObjects(),
    groups: [],
    activeCameraId: "director-camera-main",
    aspectRatio: "16:9",
    timeline: createDefaultTimeline(),
    captures: [],
  });
}

function snapshotCurrentDirectorProject(
  state: DirectorState,
  session: DirectorSessionV1,
) {
  return createDirectorProjectDocumentV1({
    projectId: session.projectId,
    owner: session.owner,
    scene: state.scene,
    objects: state.authoredObjects,
    groups: state.groups,
    activeCameraId: state.activeCameraId,
    aspectRatio: state.aspectRatio,
    timeline: state.timeline,
    captures: state.captures,
  });
}

function restoreDirectorProjectState(
  record: NonNullable<DirectorProjectOpenResult["record"]>,
  session: NonNullable<DirectorProjectOpenResult["session"]>,
  localModelLibrary: DirectorLocalModelLibraryItem[],
): Partial<DirectorState> {
  const restored = restoreDirectorProjectRuntimeSnapshotV1(record.document);
  const authoredObjects = restored.objects;
  const objects = applyTimelineAtTime(
    authoredObjects,
    restored.timeline,
    restored.timeline.currentTime,
    restored.groups,
  );
  const selectedObjectId =
    objects.find((object) => object.kind === "character")?.id ??
    objects[0]?.id ??
    null;
  return {
    sourceNodeId: session.owner.sourceNodeId,
    projectOwner: { ...session.owner },
    projectId: session.projectId,
    sessionId: session.sessionId,
    generation: session.generation,
    projectLifecycle: "ACTIVE",
    scene: restored.scene,
    authoredObjects,
    objects,
    groups: restored.groups,
    selectedObjectId,
    selectedObjectIds: selectedObjectId ? [selectedObjectId] : [],
    selectedGroupId: null,
    activeCameraId: restored.activeCameraId,
    viewMode: "director",
    transformMode: "translate",
    aspectRatio: restored.aspectRatio,
    showThirds: false,
    viewportPanelsCollapsed: false,
    isCapturing: false,
    captures: record.memory.captures.map((capture) => ({ ...capture })),
    activeCaptureId: null,
    localModelLibrary,
    timeline: restored.timeline,
    phoneVcam: createDefaultPhoneVcamState(),
  };
}

interface DirectorDeleteStateProjection {
  state: Partial<DirectorState>;
  captures: DirectorCapture[];
  localModelLibrary: DirectorLocalModelLibraryItem[];
  selectionResult: {
    selectedObjectId: string | null;
    selectedObjectIds: string[];
    selectedGroupId: string | null;
  };
}

function projectDirectorDeleteState(
  state: DirectorState,
  plan: DirectorDeletePlan,
  command: DirectorDeleteCommand,
): DirectorDeleteStateProjection {
  const restored = restoreDirectorProjectRuntimeSnapshotV1(plan.document);
  const objectIds = new Set(restored.objects.map((object) => object.id));
  const groupById = new Map(
    restored.groups.map((group) => [group.id, group]),
  );
  const trackById = new Map(
    restored.timeline.tracks.map((track) => [track.id, track]),
  );
  const pathById = new Map(
    restored.timeline.motionPaths.map((path) => [path.id, path]),
  );
  const selectedTrack =
    (state.timeline.selectedTrackId
      ? trackById.get(state.timeline.selectedTrackId)
      : null) ??
    restored.timeline.tracks[0] ??
    null;
  const selectedKeyframeId =
    selectedTrack?.keyframes.some(
      (keyframe) => keyframe.id === state.timeline.selectedKeyframeId,
    )
      ? state.timeline.selectedKeyframeId
      : null;
  const selectedPath =
    (state.timeline.selectedMotionPathId
      ? pathById.get(state.timeline.selectedMotionPathId)
      : null) ??
    (selectedTrack?.motionPathId
      ? pathById.get(selectedTrack.motionPathId)
      : null) ??
    null;
  const selectedAnchorId =
    selectedPath?.anchors.some(
      (anchor) => anchor.id === state.timeline.selectedMotionPathAnchorId,
    )
      ? state.timeline.selectedMotionPathAnchorId
      : null;
  const deletedTrackIds = new Set(plan.closure.deletedTrackIds);
  const deletedObjectIds = new Set(plan.closure.deletedObjectIds);
  const deletedPathIds = new Set(plan.closure.deletedPathIds);
  const draft = state.timeline.motionPathDraft;
  const motionPathDraft =
    draft &&
    !deletedTrackIds.has(draft.trackId) &&
    !deletedObjectIds.has(draft.objectId) &&
    deletedPathIds.size === 0
      ? draft
      : null;
  const presetApplication = state.timeline.cameraMotionPreset.application;
  const presetTrack = presetApplication
    ? trackById.get(presetApplication.trackId)
    : null;
  const cameraMotionPresetApplication =
    presetApplication &&
    presetTrack &&
    presetApplication.generatedKeyframeIds.every((keyframeId) =>
      presetTrack.keyframes.some((keyframe) => keyframe.id === keyframeId),
    )
      ? presetApplication
      : null;
  const presetError = state.timeline.cameraMotionPreset.error;
  const cameraMotionPresetError =
    presetError && trackById.has(presetError.trackId) ? presetError : null;
  const currentTime = clampDirectorTimelineTime(
    state.timeline.currentTime,
    restored.timeline.duration,
  );
  const timeline: DirectorTimelineState = {
    ...restored.timeline,
    currentTime,
    isPlaying: false,
    zoom: state.timeline.zoom,
    selectedTrackId: selectedTrack?.id ?? null,
    selectedKeyframeId,
    selectedMotionPathId: selectedPath?.id ?? null,
    selectedMotionPathAnchorId: selectedAnchorId,
    selectedMotionPathHandle: selectedAnchorId
      ? state.timeline.selectedMotionPathHandle
      : null,
    motionPathDraft,
    editorMode: state.timeline.editorMode,
    cameraMotionPreset: {
      application: cameraMotionPresetApplication,
      error: cameraMotionPresetError,
    },
  };
  const authoredObjects = restored.objects;
  const objects = projectDirectorRuntimeObjects(
    authoredObjects,
    timeline,
    restored.groups,
  );

  const survivingGroup = state.selectedGroupId
    ? groupById.get(state.selectedGroupId)
    : null;
  let selectedGroupId = survivingGroup?.id ?? null;
  let selectedObjectIds = survivingGroup
    ? [...survivingGroup.characterIds]
    : state.selectedObjectIds.filter((objectId) => objectIds.has(objectId));
  let selectedObjectId =
    state.selectedObjectId && objectIds.has(state.selectedObjectId)
      ? state.selectedObjectId
      : selectedObjectIds.at(-1) ?? null;
  if (state.viewMode === "camera") {
    selectedGroupId = null;
    selectedObjectId = restored.activeCameraId;
    selectedObjectIds = [restored.activeCameraId];
  }

  const activeCameraChanged =
    state.activeCameraId !== restored.activeCameraId;
  const phoneVcamInvalidated =
    activeCameraChanged ||
    (state.phoneVcam.importedCameraId !== null &&
      deletedObjectIds.has(state.phoneVcam.importedCameraId)) ||
    (state.phoneVcam.importedTrackId !== null &&
      deletedTrackIds.has(state.phoneVcam.importedTrackId));
  const captures = capturesForDirectorDocument(
    plan.document.projectId,
    plan.document,
    state.captures,
  );
  const activeCaptureId =
    state.activeCaptureId &&
    captures.some((capture) => capture.id === state.activeCaptureId)
      ? state.activeCaptureId
      : captures[0]?.id ?? null;
  const removesLocalLibraryDescriptor =
    command.kind === "DELETE_RESOURCE" &&
    plan.closure.deletedResourceIds.includes(command.resourceId);
  const localModelLibrary = removesLocalLibraryDescriptor
    ? state.localModelLibrary.filter(
        (item) => item.id !== command.resourceId,
      )
    : state.localModelLibrary;

  const selectionResult = {
    selectedObjectId,
    selectedObjectIds,
    selectedGroupId,
  };
  return {
    state: {
      scene: restored.scene,
      authoredObjects,
      objects,
      groups: restored.groups,
      activeCameraId: restored.activeCameraId,
      aspectRatio: restored.aspectRatio,
      selectedObjectId,
      selectedObjectIds,
      selectedGroupId,
      captures,
      activeCaptureId,
      localModelLibrary,
      timeline,
      phoneVcam: phoneVcamInvalidated
        ? createDefaultPhoneVcamState()
        : state.phoneVcam,
      isCapturing: activeCameraChanged ? false : state.isCapturing,
    },
    captures,
    localModelLibrary,
    selectionResult,
  };
}

function projectDirectorClipboardPasteState(
  state: DirectorState,
  plan: DirectorClipboardPastePlan,
): Partial<DirectorState> {
  const restored = restoreDirectorProjectRuntimeSnapshotV1(plan.document);
  const pastedTrackIds = new Set(plan.pastedTrackIds);
  const pastedPathIds = new Set(plan.pastedMotionPathIds);
  const selectedTrack =
    restored.timeline.tracks.find((track) => pastedTrackIds.has(track.id)) ??
    (state.timeline.selectedTrackId
      ? restored.timeline.tracks.find(
          (track) => track.id === state.timeline.selectedTrackId,
        )
      : null) ??
    restored.timeline.tracks[0] ??
    null;
  const selectedPath =
    restored.timeline.motionPaths.find((path) => pastedPathIds.has(path.id)) ??
    (selectedTrack?.motionPathId
      ? restored.timeline.motionPaths.find(
          (path) => path.id === selectedTrack.motionPathId,
        )
      : null) ??
    null;
  const timeline: DirectorTimelineState = {
    ...restored.timeline,
    currentTime: clampDirectorTimelineTime(
      state.timeline.currentTime,
      restored.timeline.duration,
    ),
    isPlaying: false,
    zoom: state.timeline.zoom,
    selectedTrackId: selectedTrack?.id ?? null,
    selectedKeyframeId: selectedTrack?.keyframes[0]?.id ?? null,
    selectedMotionPathId: selectedPath?.id ?? null,
    selectedMotionPathAnchorId: null,
    selectedMotionPathHandle: null,
    motionPathDraft: null,
    editorMode: state.timeline.editorMode,
    cameraMotionPreset: state.timeline.cameraMotionPreset,
  };
  const authoredObjects = restored.objects;
  return {
    authoredObjects,
    objects: projectDirectorRuntimeObjects(
      authoredObjects,
      timeline,
      restored.groups,
    ),
    groups: restored.groups,
    selectedObjectId: plan.selection.selectedObjectId,
    selectedObjectIds: [...plan.selection.selectedObjectIds],
    selectedGroupId: plan.selection.selectedGroupId,
    activeCameraId: restored.activeCameraId,
    timeline,
  };
}

function createRejectedOpenResult(
  reason: NonNullable<DirectorProjectOpenResult["reason"]>,
  previousOwnerKey: string | null,
): DirectorProjectOpenResult {
  return {
    disposition: "REJECTED",
    reason,
    record: null,
    session: null,
    previousOwnerKey,
  };
}

export function getDirectorProjectRegistrySnapshot():
  DirectorProjectRegistrySnapshot {
  return directorProjectRegistry.getSnapshot();
}

export const useDirectorStore = create<DirectorState>((set, get) => ({
  sourceNodeId: null,
  projectOwner: null,
  projectId: null,
  sessionId: null,
  generation: null,
  projectLifecycle: null,
  scene: createDefaultScene(),
  authoredObjects: cloneObjects(),
  objects: cloneObjects(),
  groups: [],
  selectedObjectId: "director-character-lead",
  selectedObjectIds: ["director-character-lead"],
  selectedGroupId: null,
  activeCameraId: "director-camera-main",
  viewMode: "director",
  transformMode: "translate",
  aspectRatio: "16:9",
  showThirds: false,
  viewportPanelsCollapsed: false,
  isCapturing: false,
  captures: [],
  activeCaptureId: null,
  localModelLibrary: [],
  timeline: createDefaultTimeline(),
  phoneVcam: createDefaultPhoneVcamState(),
  history: createDirectorHistoryState(),
  clipboard: null,
  clipboardPasteCount: 0,
  lastCommandResult: null,

  openSession: (owner) => {
    const currentState = get();
    const persisted = directorProjectPersistence.load(owner);
    const activeSession = directorProjectRegistry.getActiveSession();
    if (
      activeSession &&
      !isSameDirectorProjectOwner(activeSession.owner, owner)
    ) {
      let document;
      try {
        document = snapshotCurrentDirectorProject(
          currentState,
          activeSession,
        );
      } catch {
        return createRejectedOpenResult(
          "INVALID_DOCUMENT",
          JSON.stringify([
            activeSession.owner.route,
            activeSession.owner.canvasId,
            activeSession.owner.sourceNodeId,
          ]),
        );
      }
      const update = directorProjectRegistry.updateActive({
        owner: activeSession.owner,
        projectId: activeSession.projectId,
        generation: activeSession.generation,
        document,
        captures: currentState.captures,
      });
      if (update.disposition !== "COMMITTED") {
        return createRejectedOpenResult(
          update.reason ?? "OWNER_STALE",
          JSON.stringify([
            activeSession.owner.route,
            activeSession.owner.canvasId,
            activeSession.owner.sourceNodeId,
          ]),
        );
      }
      directorProjectPersistence.save({
        owner: activeSession.owner,
        projectId: activeSession.projectId,
        generation: activeSession.generation,
        document,
      });
    }

    const result = directorProjectRegistry.open({
      owner,
      createDocument: createDefaultDirectorProjectDocument,
      persistedDocument: persisted.document,
      persistedGeneration: persisted.generation,
    });
    if (
      result.disposition !== "REJECTED" &&
      result.record &&
      result.session &&
      result.disposition !== "FOCUSED"
    ) {
      set(
        {
          ...restoreDirectorProjectState(
            result.record,
            result.session,
            currentState.localModelLibrary,
          ),
          history: historyForDirectorProject(result.session.projectId),
          lastCommandResult: null,
        },
      );
      if (persisted.disposition !== "REJECTED") {
        directorProjectPersistence.save({
          owner: result.session.owner,
          projectId: result.session.projectId,
          generation: result.session.generation,
          document: result.record.document,
        });
      }
    }
    return result;
  },

  closeSession: (expectedOwner) => {
    const activeSession = directorProjectRegistry.getActiveSession();
    if (!activeSession) {
      return {
        disposition: "NOOP",
        reason: "NO_ACTIVE_SESSION",
        record: null,
      };
    }
    if (
      expectedOwner &&
      !isSameDirectorProjectOwner(activeSession.owner, expectedOwner)
    ) {
      return {
        disposition: "STALE",
        reason: "OWNER_STALE",
        record: null,
      };
    }
    const currentState = get();
    rememberDirectorHistory(activeSession.projectId, currentState.history);
    let document;
    try {
      document = snapshotCurrentDirectorProject(
        currentState,
        activeSession,
      );
    } catch {
      return {
        disposition: "REJECTED",
        reason: "INVALID_DOCUMENT",
        record: null,
      };
    }
    const result = directorProjectRegistry.close({
      owner: activeSession.owner,
      projectId: activeSession.projectId,
      generation: activeSession.generation,
      document,
      captures: currentState.captures,
    });
    if (result.disposition === "CLOSED") {
      if (result.record) {
        directorProjectPersistence.save({
          owner: result.record.identity.owner,
          projectId: result.record.identity.projectId,
          generation: result.record.identity.generation,
          document: result.record.document,
        });
      }
      set((state) => ({
        sourceNodeId: null,
        projectOwner: null,
        projectId: null,
        sessionId: null,
        generation: null,
        projectLifecycle: null,
        isCapturing: false,
        timeline: {
          ...state.timeline,
          isPlaying: false,
          motionPathDraft: null,
        },
        phoneVcam: createDefaultPhoneVcamState(),
        history: createDirectorHistoryState(),
        lastCommandResult: null,
      }));
    }
    return result;
  },

  beginDirectorGesture: (input) => {
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_BEGIN",
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (!input.commandKind.trim()) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_BEGIN",
        disposition: "REJECTED",
        reason: "DIRECTOR_INVALID_VALUE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (state.history.activeGesture) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_BEGIN",
        disposition: "CONFLICT",
        reason: "DIRECTOR_HISTORY_CONFLICT",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (!snapshot) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_BEGIN",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const gesture = createDirectorGesture({
      projectId: snapshot.projectId,
      generation: snapshot.generation,
      commandKind: input.commandKind,
      targetId: input.targetId ?? null,
      fieldScope: input.fieldScope ?? null,
      baselineFingerprint: snapshot.fingerprint,
      baseline: snapshot.document,
    });
    const result = makeDirectorCommandResult(state, {
      commandKind: "GESTURE_BEGIN",
      disposition: "COMMITTED",
      projectChanged: false,
      historyEntries: 0,
    });
    set({
      history: {
        ...state.history,
        activeGesture: gesture,
      },
      lastCommandResult: result,
    });
    return result;
  },

  commitDirectorGesture: () => {
    const state = get();
    const gesture = state.history.activeGesture;
    if (!gesture) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_COMMIT",
        disposition: "NOOP",
        reason: "DIRECTOR_GESTURE_NOT_ACTIVE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (
      !snapshot ||
      snapshot.projectId !== gesture.projectId ||
      snapshot.generation !== gesture.generation
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_COMMIT",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({
        history: { ...state.history, activeGesture: null },
        lastCommandResult: result,
      });
      return result;
    }
    if (snapshot.fingerprint === gesture.baselineFingerprint) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_COMMIT",
        disposition: "NOOP",
        reason: "DIRECTOR_COMMAND_NO_CHANGE",
      });
      set({
        history: { ...state.history, activeGesture: null },
        lastCommandResult: result,
      });
      return result;
    }
    if (
      !updateActiveDirectorDocument(
        state,
        snapshot.document,
        state.captures,
      )
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_COMMIT",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const result = makeDirectorCommandResult(state, {
      commandKind: "GESTURE_COMMIT",
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 1,
    });
    const entry = createDirectorHistoryEntry({
      commandId: result.commandId,
      commandKind: gesture.commandKind,
      projectId: gesture.projectId,
      generation: gesture.generation,
      before: gesture.baseline,
      after: snapshot.document,
    });
    const history = pushDirectorHistory(state.history, entry);
    rememberDirectorHistory(gesture.projectId, history);
    set({ history, lastCommandResult: result });
    return result;
  },

  cancelDirectorGesture: () => {
    const state = get();
    const gesture = state.history.activeGesture;
    if (!gesture) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_CANCEL",
        disposition: "NOOP",
        reason: "DIRECTOR_GESTURE_NOT_ACTIVE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (
      !snapshot ||
      snapshot.projectId !== gesture.projectId ||
      snapshot.generation !== gesture.generation
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_CANCEL",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({
        history: { ...state.history, activeGesture: null },
        lastCommandResult: result,
      });
      return result;
    }
    const result = makeDirectorCommandResult(state, {
      commandKind: "GESTURE_CANCEL",
      disposition: "NOOP",
      projectChanged: false,
      historyEntries: 0,
    });
    if (snapshot.fingerprint === gesture.baselineFingerprint) {
      set({
        history: { ...state.history, activeGesture: null },
        lastCommandResult: result,
      });
      return result;
    }
    const restored = restoreDirectorDocumentState(state, gesture.baseline);
    const captures = capturesForDirectorDocument(
      gesture.projectId,
      gesture.baseline,
      state.captures,
    );
    if (!restored || !updateActiveDirectorDocument(state, gesture.baseline, captures)) {
      const staleResult = makeDirectorCommandResult(state, {
        commandKind: "GESTURE_CANCEL",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: staleResult });
      return staleResult;
    }
    directorHistorySyncSuspended = true;
    try {
      set({
        ...restored,
        history: { ...state.history, activeGesture: null },
        lastCommandResult: result,
      });
    } finally {
      directorHistorySyncSuspended = false;
    }
    rememberDirectorHistory(gesture.projectId, state.history);
    return result;
  },

  undoDirector: () => {
    if (get().history.activeGesture) get().cancelDirectorGesture();
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UNDO",
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const entry = state.history.past.at(-1);
    if (!entry) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UNDO",
        disposition: "NOOP",
        reason: "DIRECTOR_HISTORY_EMPTY",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const current = getDirectorDocumentSnapshot(state);
    if (
      !current ||
      entry.projectId !== current.projectId ||
      directorDocumentFingerprint(entry.after) !== current.fingerprint
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UNDO",
        disposition: "CONFLICT",
        reason: "DIRECTOR_HISTORY_CONFLICT",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const restored = restoreDirectorDocumentState(state, entry.before);
    const captures = capturesForDirectorDocument(
      entry.projectId,
      entry.before,
      state.captures,
    );
    if (!restored || !updateActiveDirectorDocument(state, entry.before, captures)) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UNDO",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const history: DirectorHistoryState = {
      ...state.history,
      past: state.history.past.slice(0, -1),
      future: [entry, ...state.history.future].slice(0, state.history.limit),
      activeGesture: null,
    };
    const result = makeDirectorCommandResult(state, {
      commandKind: "UNDO",
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 0,
    });
    directorHistorySyncSuspended = true;
    try {
      set({ ...restored, history, lastCommandResult: result });
    } finally {
      directorHistorySyncSuspended = false;
    }
    rememberDirectorHistory(entry.projectId, history);
    return result;
  },

  redoDirector: () => {
    if (get().history.activeGesture) get().cancelDirectorGesture();
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "REDO",
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const entry = state.history.future[0];
    if (!entry) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "REDO",
        disposition: "NOOP",
        reason: "DIRECTOR_HISTORY_EMPTY",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const current = getDirectorDocumentSnapshot(state);
    if (
      !current ||
      entry.projectId !== current.projectId ||
      directorDocumentFingerprint(entry.before) !== current.fingerprint
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "REDO",
        disposition: "CONFLICT",
        reason: "DIRECTOR_HISTORY_CONFLICT",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const restored = restoreDirectorDocumentState(state, entry.after);
    const captures = capturesForDirectorDocument(
      entry.projectId,
      entry.after,
      state.captures,
    );
    if (!restored || !updateActiveDirectorDocument(state, entry.after, captures)) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "REDO",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const history: DirectorHistoryState = {
      ...state.history,
      past: [...state.history.past, entry].slice(-state.history.limit),
      future: state.history.future.slice(1),
      activeGesture: null,
    };
    const result = makeDirectorCommandResult(state, {
      commandKind: "REDO",
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 0,
    });
    directorHistorySyncSuspended = true;
    try {
      set({ ...restored, history, lastCommandResult: result });
    } finally {
      directorHistorySyncSuspended = false;
    }
    rememberDirectorHistory(entry.projectId, history);
    return result;
  },

  copyDirectorSelection: () => {
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "COPY_SELECTION",
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (!snapshot) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "COPY_SELECTION",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const built = buildDirectorClipboardPacket({
      document: snapshot.document,
      selection: {
        selectedObjectIds:
          state.selectedObjectIds.length > 0
            ? state.selectedObjectIds
            : state.selectedObjectId
              ? [state.selectedObjectId]
              : [],
        selectedGroupId: state.selectedGroupId,
      },
    });
    if (!built.ok) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "COPY_SELECTION",
        disposition:
          built.reason === "EMPTY_SELECTION" ? "NOOP" : "REJECTED",
        reason:
          built.reason === "EMPTY_SELECTION"
            ? "DIRECTOR_CLIPBOARD_EMPTY"
            : "DIRECTOR_CLIPBOARD_INVALID",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const result = makeDirectorCommandResult(state, {
      commandKind: "COPY_SELECTION",
      disposition: "COMMITTED",
      projectChanged: false,
      historyEntries: 0,
    });
    set({
      clipboard: built.packet,
      clipboardPasteCount: 0,
      lastCommandResult: result,
    });
    return result;
  },

  pasteDirectorClipboard: () => {
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (!state.clipboard) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: "NOOP",
        reason: "DIRECTOR_CLIPBOARD_EMPTY",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (
      state.history.activeGesture ||
      state.timeline.motionPathDraft ||
      state.isCapturing ||
      state.phoneVcam.status === "recording"
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: "CONFLICT",
        reason: "DIRECTOR_HISTORY_CONFLICT",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (!snapshot) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const planned = planDirectorClipboardPaste({
      document: snapshot.document,
      packet: state.clipboard,
      pasteOrdinal: state.clipboardPasteCount + 1,
    });
    if (!planned.ok) {
      const stale = planned.reason === "PROJECT_MISMATCH";
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: stale ? "STALE" : "REJECTED",
        reason: stale
          ? "DIRECTOR_CLIPBOARD_STALE"
          : "DIRECTOR_CLIPBOARD_INVALID",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (
      !updateActiveDirectorDocument(
        state,
        planned.plan.document,
        state.captures,
      )
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "PASTE_CLIPBOARD",
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const result = makeDirectorCommandResult(state, {
      commandKind: "PASTE_CLIPBOARD",
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 1,
      selectionResult: planned.plan.selection,
    });
    const entry = createDirectorHistoryEntry({
      commandId: result.commandId,
      commandKind: "PASTE_CLIPBOARD",
      projectId: snapshot.projectId,
      generation: snapshot.generation,
      before: snapshot.document,
      after: planned.plan.document,
    });
    const history = pushDirectorHistory(state.history, entry);
    rememberDirectorHistory(snapshot.projectId, history);
    directorHistorySyncSuspended = true;
    try {
      set({
        ...projectDirectorClipboardPasteState(state, planned.plan),
        clipboardPasteCount: state.clipboardPasteCount + 1,
        history,
        lastCommandResult: result,
      });
    } finally {
      directorHistorySyncSuspended = false;
    }
    return result;
  },

  deleteDirectorEntity: (command) => {
    if (get().history.activeGesture) get().cancelDirectorGesture();
    const state = get();
    if (!state.projectId || state.generation === null) {
      const result = makeDirectorCommandResult(state, {
        commandKind: command.kind,
        disposition: "REJECTED",
        reason: "DIRECTOR_PROJECT_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    const snapshot = getDirectorDocumentSnapshot(state);
    if (!snapshot) {
      const result = makeDirectorCommandResult(state, {
        commandKind: command.kind,
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (
      command.kind === "DELETE_RESOURCE" &&
      state.localModelLibrary.some(
        (item) => item.id === command.resourceId,
      ) &&
      !snapshot.document.resourceRefs.some(
        (resource) => resource.id === command.resourceId,
      )
    ) {
      const localModelLibrary = state.localModelLibrary.filter(
        (item) => item.id !== command.resourceId,
      );
      writePersistedLocalModelLibrary(localModelLibrary);
      const result = makeDirectorCommandResult(state, {
        commandKind: command.kind,
        disposition: "COMMITTED",
        projectChanged: false,
        historyEntries: 0,
        resourceEffects: [
          {
            kind: "descriptor-deleted",
            resourceId: command.resourceId,
          },
        ],
      });
      set({ localModelLibrary, lastCommandResult: result });
      return result;
    }
    const plan = planDirectorDelete(
      snapshot.document,
      command,
      normalizeDirectorProjectDocument,
    );
    if (plan.disposition !== "READY") {
      const result = makeDirectorCommandResult(state, {
        commandKind: plan.commandKind,
        disposition:
          plan.disposition === "NOOP" ? "NOOP" : "REJECTED",
        reason: plan.reason,
      });
      set({ lastCommandResult: result });
      return result;
    }

    const projection = projectDirectorDeleteState(state, plan, command);
    if (
      !updateActiveDirectorDocument(
        state,
        plan.document,
        projection.captures,
      )
    ) {
      const result = makeDirectorCommandResult(state, {
        commandKind: plan.commandKind,
        disposition: "STALE",
        reason: "DIRECTOR_OWNER_STALE",
      });
      set({ lastCommandResult: result });
      return result;
    }

    if (
      projection.localModelLibrary !== state.localModelLibrary
    ) {
      writePersistedLocalModelLibrary(projection.localModelLibrary);
    }
    const result = makeDirectorCommandResult(state, {
      commandKind: plan.commandKind,
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 1,
      selectionResult: projection.selectionResult,
      resourceEffects: plan.closure.deletedResourceIds.map(
        (resourceId) => ({
          kind:
            command.kind === "DELETE_RESOURCE" &&
            command.resourceId === resourceId
              ? ("descriptor-deleted" as const)
              : ("release-candidate" as const),
          resourceId,
        }),
      ),
    });
    const entry = createDirectorHistoryEntry({
      commandId: result.commandId,
      commandKind: plan.commandKind,
      projectId: snapshot.projectId,
      generation: snapshot.generation,
      before: snapshot.document,
      after: plan.document,
    });
    const history = pushDirectorHistory(state.history, entry);
    rememberDirectorHistory(snapshot.projectId, history);
    directorHistorySyncSuspended = true;
    try {
      set({
        ...projection.state,
        history,
        lastCommandResult: result,
      });
    } finally {
      directorHistorySyncSuspended = false;
    }
    return result;
  },

  selectObject: (objectId, source = "explicit") =>
    set((state) => {
      if (
        source === "viewport" &&
        (state.timeline.motionPathDraft ||
          state.timeline.selectedMotionPathAnchorId)
      ) {
        return state;
      }
      return {
        selectedObjectId: objectId,
        selectedObjectIds: objectId ? [objectId] : [],
        selectedGroupId: null,
        timeline: {
          ...state.timeline,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
        },
      };
    }),

  toggleObjectSelection: (objectId) =>
    set((state) => {
      const object = state.objects.find(
        (item) => item.id === objectId && item.kind === "character",
      );
      if (!object) return state;
      const currentIds = state.selectedGroupId
        ? []
        : state.selectedObjectIds;
      const selectedObjectIds = currentIds.includes(objectId)
        ? currentIds.filter((id) => id !== objectId)
        : [...currentIds, objectId];
      return {
        selectedObjectId:
          selectedObjectIds[selectedObjectIds.length - 1] ?? null,
        selectedObjectIds,
        selectedGroupId: null,
        timeline: {
          ...state.timeline,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  selectGroup: (groupId) =>
    set((state) => {
      if (!groupId) {
        return {
          selectedObjectId: null,
          selectedObjectIds: [],
          selectedGroupId: null,
        };
      }
      const group = state.groups.find((item) => item.id === groupId);
      if (!group) return state;
      const selectedObjectIds = group.characterIds.filter((id) =>
        state.objects.some((object) => object.id === id),
      );
      if (selectedObjectIds.length === 0) return state;
      return {
        selectedObjectId:
          selectedObjectIds[selectedObjectIds.length - 1] ?? null,
        selectedObjectIds,
        selectedGroupId: group.id,
        timeline: {
          ...state.timeline,
          selectedMotionPathId: null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          motionPathDraft: null,
          isPlaying: false,
        },
      };
    }),

  groupSelectedCharacters: () => {
    let createdGroupId: string | null = null;
    set((state) => {
      const assignedIds = new Set(
        state.groups.flatMap((group) => group.characterIds),
      );
      const characterIds = state.selectedObjectIds.filter(
        (id) =>
          !assignedIds.has(id) &&
          state.objects.some(
            (object) => object.id === id && object.kind === "character",
          ),
      );
      if (characterIds.length < 2) return state;
      const groupIndex = state.groups.length + 1;
      const group: DirectorCharacterGroup = {
        id: `director-character-group-${Date.now()}-${groupIndex}`,
        label: `角色组${groupIndex}`,
        characterIds,
      };
      createdGroupId = group.id;
      return {
        groups: [...state.groups, group],
        selectedObjectId: characterIds[characterIds.length - 1] ?? null,
        selectedObjectIds: characterIds,
        selectedGroupId: group.id,
        timeline: {
          ...state.timeline,
          selectedMotionPathId: null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          motionPathDraft: null,
          isPlaying: false,
        },
      };
    });
    return createdGroupId;
  },

  ungroupSelectedCharacters: () => {
    const groupId = get().selectedGroupId;
    if (!groupId) return;
    get().deleteDirectorEntity({
      kind: "DELETE_GROUP",
      groupId,
      memberPolicy: "UNGROUP",
    });
  },

  addCrowdArray: ({ rows, columns, spacing }) => {
    let createdGroupId: string | null = null;
    set((state) => {
      const safeRows = Math.min(Math.max(Math.round(rows), 1), 6);
      const requestedColumns = Math.min(
        Math.max(Math.round(columns), 1),
        8,
      );
      const safeColumns = Math.max(
        1,
        Math.min(requestedColumns, Math.floor(24 / safeRows)),
      );
      const safeSpacing = Number(
        Math.min(Math.max(spacing, 0.6), 3).toFixed(2),
      );
      const characterObjects = state.objects.filter(
        (object) => object.kind === "character",
      );
      const maxCharacterX =
        characterObjects.length > 0
          ? Math.max(
              ...characterObjects.map(
                (object) => object.transform.position[0],
              ),
            )
          : 0;
      const positions = createDirectorCrowdPositions(
        safeRows,
        safeColumns,
        safeSpacing,
        [maxCharacterX + safeSpacing * 2, 0, 0.8],
      );
      const groupIndex = state.groups.length + 1;
      const stamp = Date.now();
      const startIndex = characterObjects.length + 1;
      const characters = positions.map<DirectorObject>((position, index) => ({
        id: `director-crowd-${stamp}-${index + 1}`,
        name: `角色${String(startIndex + index).padStart(2, "0")}`,
        kind: "character",
        primitive: "character",
        color:
          DIRECTOR_CROWD_COLORS[
            (startIndex + index - 1) % DIRECTOR_CROWD_COLORS.length
          ],
        visible: true,
        locked: false,
        transform: {
          position,
          rotation: [0, 0, 0],
          scale: [0.92, 0.92, 0.92],
        },
        characterRig: createDirectorCharacterRig(),
      }));
      const group: DirectorCharacterGroup = {
        id: `director-crowd-group-${stamp}-${groupIndex}`,
        label: `群众 (${safeRows}x${safeColumns})`,
        characterIds: characters.map((character) => character.id),
        crowd: {
          rows: safeRows,
          columns: safeColumns,
          spacing: safeSpacing,
        },
      };
      createdGroupId = group.id;
      const authoredObjects = [...state.authoredObjects, ...characters];
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          state.timeline,
          state.groups.concat(group),
        ),
        groups: [...state.groups, group],
        selectedObjectId:
          group.characterIds[group.characterIds.length - 1] ?? null,
        selectedObjectIds: [...group.characterIds],
        selectedGroupId: group.id,
        timeline: {
          ...state.timeline,
          isPlaying: false,
        },
      };
    });
    return createdGroupId;
  },

  hydrateLocalModelLibrary: () =>
    set({ localModelLibrary: readPersistedLocalModelLibrary() }),

  addLocalModelLibraryItem: (item) =>
    set((state) => {
      const items = [
        ...state.localModelLibrary.filter(
          (current) => current.id !== item.id,
        ),
        item,
      ];
      writePersistedLocalModelLibrary(items);
      return { localModelLibrary: items };
    }),

  removeLocalModelLibraryItem: (assetId, policy = "BLOCK") =>
    get().deleteDirectorEntity({
      kind: "DELETE_RESOURCE",
      resourceId: assetId,
      instancePolicy: policy,
    }),

  addModelLibraryObject: (item) => {
    let createdObjectId = "";
    set((state) => {
      const libraryObjectCount = state.objects.filter(
        (object) => object.primitive === "library",
      ).length;
      const column = libraryObjectCount % 3;
      const row = Math.floor(libraryObjectCount / 3);
      const objectId = `director-library-${item.id}-${Date.now()}`;
      const object: DirectorObject = {
        id: objectId,
        name: item.name,
        kind: "prop",
        primitive: "library",
        color: item.color,
        visible: true,
        locked: false,
        transform: {
          position: [1.65 + column * 0.85, 0, 0.8 + row * 0.9],
          rotation: [0, 0, 0],
          scale: [1, 1, 1],
        },
        libraryAssetId: item.id,
        libraryCategoryId: item.categoryId,
        libraryVisual: item.visual,
        librarySource:
          item.categoryId === "my-models" ? "local" : "catalog",
        libraryFileName: "fileName" in item ? item.fileName : undefined,
      };
      createdObjectId = objectId;
      const authoredObjects = [...state.authoredObjects, object];
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          state.timeline,
          state.groups,
        ),
        selectedObjectId: objectId,
        selectedObjectIds: [objectId],
        selectedGroupId: null,
        timeline: {
          ...state.timeline,
          selectedMotionPathId: null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          motionPathDraft: null,
          isPlaying: false,
        },
      };
    });
    return createdObjectId;
  },

  updateGroup: (groupId, patch) =>
    set((state) => ({
      groups: state.groups.map((group) =>
        group.id === groupId ? { ...group, ...patch } : group,
      ),
      timeline: patch.label
        ? {
            ...state.timeline,
            tracks: state.timeline.tracks.map((track) =>
              track.kind === "group" && track.groupId === groupId
                ? { ...track, label: `${patch.label} · 分组` }
                : track,
            ),
          }
        : state.timeline,
    })),

  updateGroupTransform: (groupId, transform) =>
    set((state) => {
      const group = state.groups.find((item) => item.id === groupId);
      if (!group) return state;
      const authoredObjects = resolveCameraRelations(
        applyDirectorGroupTransform(state.authoredObjects, group, transform),
      );
      const existing = state.timeline.tracks.find(
        (track): track is Extract<DirectorTimelineTrack, { kind: "group" }> =>
          track.kind === "group" && track.groupId === groupId,
      );
      const timeline = existing && state.timeline.autoKeyframe
        ? {
            ...state.timeline,
            tracks: state.timeline.tracks.map((track) =>
              track.id === existing.id
                ? upsertGroupTrackKeyframe(
                    existing,
                    transform,
                    state.timeline.currentTime,
                  ).track
                : track,
            ),
            isPlaying: false,
          }
        : state.timeline;
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          timeline,
          state.groups,
        ),
        timeline,
      };
    }),

  setViewMode: (mode) =>
    set((state) => ({
      viewMode: mode,
      selectedObjectId: mode === "camera" ? state.activeCameraId : state.selectedObjectId,
      selectedObjectIds:
        mode === "camera" ? [state.activeCameraId] : state.selectedObjectIds,
      selectedGroupId: mode === "camera" ? null : state.selectedGroupId,
    })),

  setTransformMode: (mode) => set({ transformMode: mode }),

  setAspectRatio: (ratio) => set({ aspectRatio: ratio }),

  toggleThirds: () => set((state) => ({ showThirds: !state.showThirds })),

  toggleViewportPanelsCollapsed: () =>
    set((state) => ({
      viewportPanelsCollapsed: !state.viewportPanelsCollapsed,
    })),

  setViewportPanelsCollapsed: (collapsed) =>
    set({ viewportPanelsCollapsed: collapsed }),

  updateScene: (patch) =>
    set((state) => ({ scene: { ...state.scene, ...patch } })),

  updateObject: (objectId, patch) =>
    set((state) => {
      const authoredObjects = state.authoredObjects.map((object) =>
        object.id === objectId ? { ...object, ...patch } : object,
      );
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          state.timeline,
          state.groups,
        ),
        timeline: patch.name
          ? {
              ...state.timeline,
              tracks: state.timeline.tracks.map((track) =>
                track.objectId === objectId
                  ? {
                      ...track,
                      label: `${patch.name} · ${
                        track.kind === "camera"
                          ? "机位"
                          : track.kind === "group"
                            ? "分组"
                          : track.kind === "pose"
                            ? "姿态"
                            : "变换"
                      }`,
                    }
                  : track,
              ),
            }
          : state.timeline,
      };
    }),

  updateObjectTransform: (objectId, field, axis, value) => {
    const state = get();
    const authoredObject = state.authoredObjects.find(
      (object) => object.id === objectId,
    );
    const runtimeObject = state.objects.find(
      (object) => object.id === objectId,
    );
    if (!authoredObject || !runtimeObject) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UPDATE_OBJECT_TRANSFORM",
        disposition: "REJECTED",
        reason: "DIRECTOR_TARGET_MISSING",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (!Number.isFinite(value)) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UPDATE_OBJECT_TRANSFORM",
        disposition: "REJECTED",
        reason: "DIRECTOR_INVALID_VALUE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    if (authoredObject.transform[field][axis] === value) {
      const result = makeDirectorCommandResult(state, {
        commandKind: "UPDATE_OBJECT_TRANSFORM",
        disposition: "NOOP",
        reason: "DIRECTOR_COMMAND_NO_CHANGE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    set((state) => {
      const authoredObjects = state.authoredObjects.map((object) =>
        object.id === objectId
          ? {
              ...object,
              transform: {
                ...object.transform,
                [field]: updateTuple(object.transform[field], axis, value),
              },
            }
          : object,
      );
      const nextRuntimeObjects = resolveCameraRelations(
        state.objects.map((object) =>
          object.id === objectId
            ? {
                ...object,
                transform: {
                  ...object.transform,
                  [field]: updateTuple(object.transform[field], axis, value),
                },
              }
            : object,
        ),
      );
      const existing = state.timeline.tracks.find(
        (track) =>
          track.objectId === objectId &&
          (track.kind === "transform" || track.kind === "camera"),
      );
      let timeline = state.timeline;
      if (existing && state.timeline.autoKeyframe) {
        const nextRuntimeObject = nextRuntimeObjects.find(
          (object) => object.id === objectId,
        );
        if (nextRuntimeObject) {
          const result = upsertTrackKeyframe(
            existing,
            nextRuntimeObject,
            state.timeline.currentTime,
          );
          timeline = {
            ...state.timeline,
            tracks: state.timeline.tracks.map((track) =>
              track.id === existing.id ? result.track : track,
            ),
            selectedTrackId: result.track.id,
            selectedKeyframeId: result.keyframeId,
            isPlaying: false,
          };
        }
      }
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          timeline,
          state.groups,
        ),
        timeline,
      };
    });
    return makeDirectorCommandResult(state, {
      commandKind: "UPDATE_OBJECT_TRANSFORM",
      disposition: "COMMITTED",
      projectChanged: true,
      historyEntries: 1,
    });
  },

  updateCamera: (objectId, patch) =>
    set((state) => {
      const authoredCamera = state.authoredObjects.find(
        (object) => object.id === objectId && object.camera,
      );
      const runtimeCamera = state.objects.find(
        (object) => object.id === objectId && object.camera,
      );
      if (!authoredCamera?.camera || !runtimeCamera?.camera) return state;
      const authoredObjects = state.authoredObjects.map((object) =>
        object.id === objectId && object.camera
          ? {
              ...object,
              camera: {
                ...object.camera,
                ...patch,
                target: patch.target
                  ? ([...patch.target] as DirectorTuple3)
                  : ([...object.camera.target] as DirectorTuple3),
                followOffset: patch.followOffset
                  ? ([...patch.followOffset] as DirectorTuple3)
                  : ([...object.camera.followOffset] as DirectorTuple3),
              },
            }
          : object,
      );
      const nextRuntimeObjects = resolveCameraRelations(
        state.objects.map((object) =>
          object.id === objectId && object.camera
            ? {
                ...object,
                camera: {
                  ...object.camera,
                  ...patch,
                  target: patch.target
                    ? ([...patch.target] as DirectorTuple3)
                    : ([...object.camera.target] as DirectorTuple3),
                  followOffset: patch.followOffset
                    ? ([...patch.followOffset] as DirectorTuple3)
                    : ([...object.camera.followOffset] as DirectorTuple3),
                },
              }
            : object,
        ),
      );
      const existing = state.timeline.tracks.find(
        (track) => track.objectId === objectId && track.kind === "camera",
      );
      let timeline = state.timeline;
      if (existing && state.timeline.autoKeyframe) {
        const nextRuntimeObject = nextRuntimeObjects.find(
          (object) => object.id === objectId,
        );
        if (nextRuntimeObject) {
          const result = upsertTrackKeyframe(
            existing,
            nextRuntimeObject,
            state.timeline.currentTime,
          );
          timeline = {
            ...state.timeline,
            tracks: state.timeline.tracks.map((track) =>
              track.id === existing.id ? result.track : track,
            ),
            selectedTrackId: result.track.id,
            selectedKeyframeId: result.keyframeId,
            isPlaying: false,
          };
        }
      }
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          timeline,
          state.groups,
        ),
        timeline,
      };
    }),

  applyCharacterPosePreset: (objectId, presetId) =>
    set((state) =>
      updateCharacterRigAndTimeline(
        state,
        objectId,
        applyDirectorPosePreset(presetId),
      ),
    ),

  updateCharacterPoseControl: (objectId, key, value) =>
    set((state) => {
      const object = state.objects.find(
        (item) => item.id === objectId && item.kind === "character",
      );
      if (!object) return state;
      return updateCharacterRigAndTimeline(
        state,
        objectId,
        updateDirectorPoseControl(
          object.characterRig ?? createDirectorCharacterRig(),
          key,
          value,
        ),
      );
    }),

  setCapturing: (capturing) => set({ isCapturing: capturing }),

  addCapture: (capture) =>
    set((state) => ({
      captures: [capture, ...state.captures].slice(0, 12),
      activeCaptureId: capture.id,
    })),

  selectCapture: (captureId) =>
    set((state) => ({
      activeCaptureId:
        captureId && state.captures.some((capture) => capture.id === captureId)
          ? captureId
          : null,
    })),

  removeCapture: (captureId) =>
    get().deleteDirectorEntity({
      kind: "DELETE_CAPTURE",
      captureId,
    }),

  clearCaptures: () =>
    get().deleteDirectorEntity({
      kind: "DELETE_CAPTURES",
      captureIds: get().captures.map((capture) => capture.id),
    }),

  markCaptureSent: (captureId, nodeId) =>
    set((state) => ({
      captures: state.captures.map((capture) =>
        capture.id === captureId ? { ...capture, sentNodeId: nodeId } : capture,
      ),
    })),

  setPhoneVcamStatus: (status, error = null) =>
    set((state) => ({
      phoneVcam: {
        ...state.phoneVcam,
        status,
        error,
        recordingStartTime:
          status === "recording"
            ? state.phoneVcam.recordingStartTime
            : null,
      },
    })),

  connectPhoneVcamLocal: () => {
    const state = get();
    const camera = state.objects.find(
      (object) => object.id === state.activeCameraId,
    );
    const baselineCamera = camera ? cloneCameraValue(camera) : null;
    if (!camera || !baselineCamera) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status: "error",
          error: "导演台视口还未准备好",
        },
      }));
      return false;
    }
    if (camera.camera?.followTargetId) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status: "error",
          error: "请先关闭机位跟随，再使用手机运镜",
        },
      }));
      return false;
    }
    set((current) => ({
      viewMode: "camera",
      selectedObjectId: camera.id,
      timeline: { ...current.timeline, isPlaying: false },
      phoneVcam: {
        ...current.phoneVcam,
        status: "local-ready",
        hold: false,
        elevation: 0,
        pose: { yaw: 0, pitch: 0, roll: 0 },
        baselineCamera,
        recordingStartTime: null,
        sampleCount: 0,
        error: null,
      },
    }));
    return true;
  },

  setPhoneVcamGyroEnabled: (enabled) =>
    set((state) => ({
      phoneVcam: { ...state.phoneVcam, gyroEnabled: enabled },
    })),

  setPhoneVcamStability: (stability) =>
    set((state) => ({
      phoneVcam: {
        ...state.phoneVcam,
        stability: Math.min(
          Math.max(Number.isFinite(stability) ? stability : 0, 0),
          100,
        ),
      },
    })),

  togglePhoneVcamKeepLevel: () =>
    set((state) => ({
      phoneVcam: {
        ...state.phoneVcam,
        keepLevel: !state.phoneVcam.keepLevel,
      },
    })),

  setPhoneVcamHold: (hold) =>
    set((state) => ({
      phoneVcam: { ...state.phoneVcam, hold },
    })),

  calibratePhoneVcam: () =>
    set((state) => {
      const camera = state.objects.find(
        (object) => object.id === state.activeCameraId,
      );
      const baselineCamera = camera ? cloneCameraValue(camera) : null;
      if (!baselineCamera) return state;
      return {
        phoneVcam: {
          ...state.phoneVcam,
          baselineCamera,
          elevation: 0,
          pose: { yaw: 0, pitch: 0, roll: 0 },
          hold: false,
          error: null,
        },
      };
    }),

  applyPhoneVcamPose: (pose) =>
    set((state) => {
      const camera = state.objects.find(
        (object) => object.id === state.activeCameraId,
      );
      const baselineCamera =
        state.phoneVcam.baselineCamera ??
        (camera ? cloneCameraValue(camera) : null);
      const normalizedPose: DirectorPhoneVcamPose = {
        yaw: Number.isFinite(pose.yaw) ? pose.yaw : 0,
        pitch: Number.isFinite(pose.pitch) ? pose.pitch : 0,
        roll: Number.isFinite(pose.roll) ? pose.roll : 0,
      };
      if (
        !camera?.camera ||
        !baselineCamera ||
        camera.camera.followTargetId !== null ||
        state.phoneVcam.hold ||
        !["local-ready", "recording", "imported"].includes(
          state.phoneVcam.status,
        )
      ) {
        return {
          phoneVcam: {
            ...state.phoneVcam,
            pose: normalizedPose,
          },
        };
      }
      const previous = cloneCameraValue(camera);
      if (!previous) return state;
      const nextCamera = mapDirectorPhonePoseToCamera({
        baseline: baselineCamera,
        previous,
        pose: normalizedPose,
        stability: state.phoneVcam.stability,
        keepLevel: state.phoneVcam.keepLevel,
        elevation: state.phoneVcam.elevation,
      });
      return {
        objects: state.objects.map((object) =>
          object.id === camera.id
            ? {
                ...object,
                transform: cloneTransform(nextCamera.transform),
                camera: {
                  ...object.camera!,
                  target: [...nextCamera.target],
                  fov: nextCamera.fov,
                },
              }
            : object,
        ),
        phoneVcam: {
          ...state.phoneVcam,
          pose: normalizedPose,
          baselineCamera,
          error: null,
        },
      };
    }),

  elevatePhoneVcam: (delta) =>
    set((state) => {
      const camera = state.objects.find(
        (object) => object.id === state.activeCameraId,
      );
      const baselineCamera =
        state.phoneVcam.baselineCamera ??
        (camera ? cloneCameraValue(camera) : null);
      if (
        !camera?.camera ||
        !baselineCamera ||
        camera.camera.followTargetId !== null ||
        state.phoneVcam.hold ||
        !Number.isFinite(delta)
      ) {
        return state;
      }
      const elevation = Math.min(
        Math.max(state.phoneVcam.elevation + delta, -4),
        4,
      );
      const previous = cloneCameraValue(camera);
      if (!previous) return state;
      const nextCamera = mapDirectorPhonePoseToCamera({
        baseline: baselineCamera,
        previous,
        pose: state.phoneVcam.pose,
        stability: state.phoneVcam.stability,
        keepLevel: state.phoneVcam.keepLevel,
        elevation,
      });
      return {
        objects: state.objects.map((object) =>
          object.id === camera.id
            ? {
                ...object,
                transform: cloneTransform(nextCamera.transform),
                camera: {
                  ...object.camera!,
                  target: [...nextCamera.target],
                  fov: nextCamera.fov,
                },
              }
            : object,
        ),
        phoneVcam: {
          ...state.phoneVcam,
          elevation,
          baselineCamera,
          error: null,
        },
      };
    }),

  startPhoneVcamRecording: () => {
    const state = get();
    const camera = state.objects.find(
      (object) => object.id === state.activeCameraId,
    );
    if (!camera?.camera) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          error: "导演台视口还未准备好",
        },
      }));
      return false;
    }
    if (camera.camera.followTargetId) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          error: "请先关闭机位跟随，再使用手机运镜",
        },
      }));
      return false;
    }
    if (
      !["local-ready", "imported"].includes(state.phoneVcam.status)
    ) {
      return false;
    }
    if (state.timeline.currentTime >= state.timeline.duration - 0.001) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          error: "当前播放头后没有可录制时长",
        },
      }));
      return false;
    }
    set((current) => ({
      timeline: { ...current.timeline, isPlaying: false },
      phoneVcam: {
        ...current.phoneVcam,
        status: "recording",
        baselineCamera:
          cloneCameraValue(camera) ?? current.phoneVcam.baselineCamera,
        recordingStartTime: current.timeline.currentTime,
        sampleCount: 0,
        importedCameraId: null,
        importedTrackId: null,
        error: null,
      },
    }));
    return true;
  },

  setPhoneVcamRecordingTime: (time) =>
    set((state) => {
      if (state.phoneVcam.status !== "recording") return state;
      const currentTime = clampDirectorTimelineTime(
        time,
        state.timeline.duration,
      );
      const activeCamera = state.objects.find(
        (object) => object.id === state.activeCameraId,
      );
      const sampledObjects = applyTimelineAtTime(
        state.authoredObjects,
        state.timeline,
        currentTime,
        state.groups,
      );
      return {
        objects: activeCamera
          ? sampledObjects.map((object) =>
              object.id === activeCamera.id ? activeCamera : object,
            )
          : sampledObjects,
        timeline: {
          ...state.timeline,
          currentTime,
          isPlaying: false,
        },
      };
    }),

  setPhoneVcamSampleCount: (count) =>
    set((state) => ({
      phoneVcam: {
        ...state.phoneVcam,
        sampleCount: Math.max(
          0,
          Math.round(Number.isFinite(count) ? count : 0),
        ),
      },
    })),

  importPhoneVcamTake: (samples) => {
    const state = get();
    const activeCamera = state.objects.find(
      (object) => object.id === state.activeCameraId,
    );
    const startTime = state.phoneVcam.recordingStartTime;
    const validSamples = samples
      .filter(
        (sample) =>
          Number.isFinite(sample.time) &&
          sample.time >= 0 &&
          sample.time <= state.timeline.duration &&
          isFiniteDirectorCameraValue(sample.value),
      )
      .sort((left, right) => left.time - right.time)
      .filter(
        (sample, index, all) =>
          index === 0 ||
          Math.abs(sample.time - all[index - 1].time) >= 0.001,
      );
    if (
      state.phoneVcam.status !== "recording" ||
      startTime === null ||
      !activeCamera?.camera ||
      validSamples.length < 2
    ) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status:
            current.phoneVcam.status === "recording"
              ? "local-ready"
              : current.phoneVcam.status,
          recordingStartTime: null,
          error: "本次手机运镜没有有效录制内容",
        },
      }));
      return null;
    }

    const context = getDirectorAsyncContext(state);
    if (!context) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status: "local-ready",
          recordingStartTime: null,
          error: "导演台会话已失效，请重新录制",
        },
      }));
      return null;
    }
    const operationId = createDirectorAsyncIdentity(
      "director-phone-vcam-import",
    );
    const descriptor = {
      operationId,
      kind: "phone-vcam" as const,
      owner: context.owner,
      attemptId: createDirectorAsyncIdentity(
        "director-phone-vcam-import-attempt",
      ),
      sourceFingerprint: context.sourceFingerprint,
      requestFingerprint: JSON.stringify({
        sampleCount: validSamples.length,
        firstTime: validSamples[0]?.time ?? null,
        lastTime: validSamples.at(-1)?.time ?? null,
      }),
      acceptedAt: new Date().toISOString(),
      selectionPolicy: "select-result" as const,
    };
    if (directorAsyncAuthority.begin(descriptor).disposition !== "accepted") {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status: "local-ready",
          recordingStartTime: null,
          error: "手机运镜结果未被接受，请重新录制",
        },
      }));
      return null;
    }
    const resultId = `${operationId}-take`;
    const envelope: DirectorAsyncResultEnvelopeV1<{
      sampleCount: number;
    }> = {
      operationId,
      kind: descriptor.kind,
      owner: descriptor.owner,
      attemptId: descriptor.attemptId,
      sourceFingerprint: descriptor.sourceFingerprint,
      resultId,
      resultVersionId: resultId,
      phase: "succeeded",
      payload: { sampleCount: validSamples.length },
    };
    if (
      directorAsyncAuthority.reconcile(envelope, context).disposition !==
      "apply-current"
    ) {
      set((current) => ({
        phoneVcam: {
          ...current.phoneVcam,
          status: "local-ready",
          recordingStartTime: null,
          error: "手机运镜结果已失效，请重新录制",
        },
      }));
      return null;
    }

    const takeIndex = state.phoneVcam.takeCount + 1;
    const createdAt = Date.now();
    const cameraId = `director-phone-vcam-${takeIndex}-${createdAt}`;
    const trackId = `director-track-phone-vcam-${takeIndex}-${createdAt}`;
    const name = `手机运镜 ${takeIndex}`;
    const lastSample = validSamples[validSamples.length - 1];
    const lastValue = cloneCameraKeyframeValue(lastSample.value);
    const camera: DirectorObject = {
      id: cameraId,
      name,
      kind: "camera",
      primitive: "camera",
      color: "#6ed9f5",
      visible: true,
      locked: false,
      transform: cloneTransform(lastValue.transform),
      camera: {
        target: [...lastValue.target],
        fov: lastValue.fov,
        ...createDirectorCameraRelation(),
      },
    };
    const track: DirectorTimelineTrack = {
      id: trackId,
      kind: "camera",
      objectId: cameraId,
      label: name,
      speedCurve: createDirectorSpeedCurve(),
      keyframes: validSamples.map((sample, index) => ({
        id: `${trackId}-keyframe-${index}`,
        time: clampDirectorTimelineTime(
          Math.max(sample.time, startTime),
          state.timeline.duration,
        ),
        value: cloneCameraKeyframeValue(sample.value),
      })),
    };
    const baseline = state.phoneVcam.baselineCamera;
    const restoredObjects = state.authoredObjects.map((object) =>
      object.id === activeCamera.id && baseline
        ? {
            ...object,
            transform: cloneTransform(baseline.transform),
            camera: {
              ...object.camera!,
              target: [...baseline.target] as DirectorTuple3,
              fov: baseline.fov,
            },
          }
        : object,
    );

    set((current) => {
      const authoredObjects = [...restoredObjects, camera];
      const timeline: DirectorTimelineState = {
        ...current.timeline,
        currentTime: lastSample.time,
        isPlaying: false,
        tracks: [...current.timeline.tracks, track],
        selectedTrackId: trackId,
        selectedKeyframeId:
          track.keyframes[track.keyframes.length - 1]?.id ?? null,
        selectedMotionPathId: null,
        selectedMotionPathAnchorId: null,
        selectedMotionPathHandle: null,
        motionPathDraft: null,
        editorMode: "timeline",
      };
      return {
        authoredObjects,
        objects: projectDirectorRuntimeObjects(
          authoredObjects,
          timeline,
          current.groups,
        ),
        selectedObjectId: cameraId,
        activeCameraId: cameraId,
        viewMode: "camera",
        timeline,
        phoneVcam: {
          ...current.phoneVcam,
          status: "imported",
          baselineCamera: cloneCameraKeyframeValue(lastValue),
          recordingStartTime: null,
          sampleCount: validSamples.length,
          takeCount: takeIndex,
          importedCameraId: cameraId,
          importedTrackId: trackId,
          error: null,
        },
      };
    });
    return { cameraId, trackId };
  },

  setTimelineTime: (time) =>
    set((state) => {
      const currentTime = clampDirectorTimelineTime(
        time,
        state.timeline.duration,
      );
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          state.timeline,
          currentTime,
          state.groups,
        ),
        timeline: {
          ...state.timeline,
          currentTime,
          isPlaying: false,
        },
      };
    }),

  setTimelinePlaying: (playing) =>
    set((state) => {
      if (!playing) {
        return { timeline: { ...state.timeline, isPlaying: false } };
      }
      const restart =
        state.timeline.currentTime >= state.timeline.duration - 0.001;
      const currentTime = restart ? 0 : state.timeline.currentTime;
      return {
        objects: restart
          ? applyTimelineAtTime(
              state.authoredObjects,
              state.timeline,
              currentTime,
              state.groups,
            )
          : state.objects,
        timeline: {
          ...state.timeline,
          currentTime,
          isPlaying: true,
        },
      };
    }),

  advanceTimeline: (deltaSeconds) =>
    set((state) => {
      if (!state.timeline.isPlaying || deltaSeconds <= 0) return state;
      const duration = state.timeline.duration;
      const requested = state.timeline.currentTime + deltaSeconds;
      const reachedEnd = requested >= duration;
      const currentTime = reachedEnd
        ? state.timeline.loop
          ? requested % duration
          : duration
        : requested;
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          state.timeline,
          currentTime,
          state.groups,
        ),
        timeline: {
          ...state.timeline,
          currentTime,
          isPlaying: reachedEnd ? state.timeline.loop : true,
        },
      };
    }),

  toggleTimelineLoop: () =>
    set((state) => ({
      timeline: { ...state.timeline, loop: !state.timeline.loop },
    })),

  toggleAutoKeyframe: () =>
    set((state) => ({
      timeline: {
        ...state.timeline,
        autoKeyframe: !state.timeline.autoKeyframe,
      },
    })),

  setTimelineZoom: (zoom) =>
    set((state) => ({
      timeline: {
        ...state.timeline,
        zoom: Math.min(Math.max(zoom, 0.75), 2.5),
      },
    })),

  selectTimelineTrack: (trackId) =>
    set((state) => {
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      if (!track) return state;
      const group =
        track.kind === "group"
          ? state.groups.find((item) => item.id === track.groupId)
          : null;
      const selectedObjectIds = group
        ? [...group.characterIds]
        : [track.objectId];
      return {
        selectedObjectId:
          selectedObjectIds[selectedObjectIds.length - 1] ?? null,
        selectedObjectIds,
        selectedGroupId: group?.id ?? null,
        timeline: {
          ...state.timeline,
          selectedTrackId: track.id,
          selectedKeyframeId: null,
          selectedMotionPathId: track.motionPathId ?? null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  selectTimelineKeyframe: (trackId, keyframeId) =>
    set((state) => {
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      const keyframe = track?.keyframes.find((item) => item.id === keyframeId);
      if (!track || !keyframe) return state;
      const group =
        track.kind === "group"
          ? state.groups.find((item) => item.id === track.groupId)
          : null;
      const selectedObjectIds = group
        ? [...group.characterIds]
        : [track.objectId];
      return {
        selectedObjectId:
          selectedObjectIds[selectedObjectIds.length - 1] ?? null,
        selectedObjectIds,
        selectedGroupId: group?.id ?? null,
        objects: applyTimelineAtTime(
          state.authoredObjects,
          state.timeline,
          keyframe.time,
          state.groups,
        ),
        timeline: {
          ...state.timeline,
          currentTime: keyframe.time,
          selectedTrackId: track.id,
          selectedKeyframeId: keyframe.id,
          selectedMotionPathId: track.motionPathId ?? null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  addTimelineTrack: (requestedObjectId) =>
    set((state) => {
      const requestedGroup = state.groups.find(
        (group) =>
          group.id === requestedObjectId ||
          (!requestedObjectId && group.id === state.selectedGroupId),
      );
      if (requestedGroup) {
        const existing = state.timeline.tracks.find(
          (track) =>
            track.kind === "group" &&
            track.groupId === requestedGroup.id,
        );
        if (existing) {
          return {
            timeline: {
              ...state.timeline,
              selectedTrackId: existing.id,
              selectedKeyframeId: null,
              selectedMotionPathId: null,
              selectedMotionPathAnchorId: null,
              selectedMotionPathHandle: null,
              isPlaying: false,
            },
          };
        }
        const track = createTrackForGroup(
          requestedGroup,
          state.objects,
          state.timeline.currentTime,
        );
        if (!track) return state;
        return {
          timeline: {
            ...state.timeline,
            tracks: [...state.timeline.tracks, track],
            selectedTrackId: track.id,
            selectedKeyframeId: track.keyframes[0]?.id ?? null,
            selectedMotionPathId: null,
            selectedMotionPathAnchorId: null,
            selectedMotionPathHandle: null,
            isPlaying: false,
          },
        };
      }
      const objectId = requestedObjectId ?? state.selectedObjectId;
      const object = state.objects.find((item) => item.id === objectId);
      if (!object) return state;
      const existing = state.timeline.tracks.find(
        (track) =>
          track.objectId === object.id && track.kind !== "pose",
      );
      if (existing) {
        return {
          timeline: {
            ...state.timeline,
            selectedTrackId: existing.id,
            selectedKeyframeId: null,
            selectedMotionPathId: existing.motionPathId ?? null,
            selectedMotionPathAnchorId: null,
            selectedMotionPathHandle: null,
          },
        };
      }
      const track = createTrackForObject(
        object,
        state.timeline.currentTime,
      );
      return {
        timeline: {
          ...state.timeline,
          tracks: [...state.timeline.tracks, track],
          selectedTrackId: track.id,
          selectedKeyframeId: track.keyframes[0]?.id ?? null,
          selectedMotionPathId: null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  removeTimelineTrack: (requestedTrackId) => {
    const trackId = requestedTrackId ?? get().timeline.selectedTrackId;
    if (!trackId) {
      const state = get();
      const result = makeDirectorCommandResult(state, {
        commandKind: "DELETE_TRACK",
        disposition: "NOOP",
        reason: "DIRECTOR_COMMAND_NO_CHANGE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    return get().deleteDirectorEntity({
      kind: "DELETE_TRACK",
      trackId,
    });
  },

  addTimelineKeyframe: (requestedTrackId) =>
    set((state) => {
      const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      if (track?.kind === "group") {
        const group = state.groups.find(
          (item) => item.id === track.groupId,
        );
        const transform = group
          ? getDirectorGroupAnchorTransform(state.objects, group)
          : null;
        if (!group || !transform) return state;
        const result = upsertGroupTrackKeyframe(
          track,
          transform,
          state.timeline.currentTime,
        );
        return {
          timeline: {
            ...state.timeline,
            tracks: state.timeline.tracks.map((item) =>
              item.id === track.id ? result.track : item,
            ),
            selectedTrackId: track.id,
            selectedKeyframeId: result.keyframeId,
            isPlaying: false,
          },
        };
      }
      const object = state.objects.find(
        (item) => item.id === track?.objectId,
      );
      if (!track || !object) return state;
      const result = upsertTrackKeyframe(
        track,
        object,
        state.timeline.currentTime,
      );
      return {
        timeline: {
          ...state.timeline,
          tracks: state.timeline.tracks.map((item) =>
            item.id === track.id ? result.track : item,
          ),
          selectedTrackId: track.id,
          selectedKeyframeId: result.keyframeId,
          isPlaying: false,
        },
      };
    }),

  deleteTimelineKeyframe: (requestedKeyframeId) =>
    set((state) => {
      const keyframeId =
        requestedKeyframeId ?? state.timeline.selectedKeyframeId;
      if (!keyframeId) return state;
      const tracks = state.timeline.tracks.map((track) => ({
        ...track,
        keyframes: track.keyframes.filter(
          (keyframe) => keyframe.id !== keyframeId,
        ),
      })) as DirectorTimelineTrack[];
      const timeline = { ...state.timeline, tracks };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          state.timeline.currentTime,
          state.groups,
        ),
        timeline: {
          ...timeline,
          selectedKeyframeId: null,
          isPlaying: false,
        },
      };
    }),

  seekTimelineKeyframe: (direction) =>
    set((state) => {
      const times = Array.from(
        new Set(
          state.timeline.tracks.flatMap((track) =>
            track.keyframes.map((keyframe) => keyframe.time),
          ),
        ),
      ).sort((a, b) => a - b);
      const current = state.timeline.currentTime;
      const nextTime =
        direction > 0
          ? times.find((time) => time > current + 0.001)
          : [...times].reverse().find((time) => time < current - 0.001);
      if (nextTime === undefined) return state;
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          state.timeline,
          nextTime,
          state.groups,
        ),
        timeline: {
          ...state.timeline,
          currentTime: nextTime,
          selectedKeyframeId: null,
          isPlaying: false,
        },
      };
    }),

  recordObjectKeyframe: (objectId, force = false) =>
    set((state) => {
      if (!force && !state.timeline.autoKeyframe) return state;
      const object = state.objects.find((item) => item.id === objectId);
      if (!object) return state;
      const existing = state.timeline.tracks.find(
        (track) => track.objectId === objectId && track.kind !== "pose",
      );
      const baseTrack =
        existing ??
        createTrackForObject(object, state.timeline.currentTime);
      const result = upsertTrackKeyframe(
        baseTrack,
        object,
        state.timeline.currentTime,
      );
      const tracks = existing
        ? state.timeline.tracks.map((track) =>
            track.id === existing.id ? result.track : track,
          )
        : [...state.timeline.tracks, result.track];
      return {
        timeline: {
          ...state.timeline,
          tracks,
          selectedTrackId: result.track.id,
          selectedKeyframeId: result.keyframeId,
          selectedMotionPathId: result.track.motionPathId ?? null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  recordGroupKeyframe: (groupId, force = false) =>
    set((state) => {
      if (!force && !state.timeline.autoKeyframe) return state;
      const group = state.groups.find((item) => item.id === groupId);
      const transform = group
        ? getDirectorGroupAnchorTransform(state.objects, group)
        : null;
      if (!group || !transform) return state;
      const existing = state.timeline.tracks.find(
        (
          track,
        ): track is Extract<DirectorTimelineTrack, { kind: "group" }> =>
          track.kind === "group" && track.groupId === group.id,
      );
      const baseTrack =
        existing ??
        createTrackForGroup(group, state.objects, state.timeline.currentTime);
      if (!baseTrack || baseTrack.kind !== "group") return state;
      const result = upsertGroupTrackKeyframe(
        baseTrack,
        transform,
        state.timeline.currentTime,
      );
      const tracks = existing
        ? state.timeline.tracks.map((track) =>
            track.id === existing.id ? result.track : track,
          )
        : [...state.timeline.tracks, result.track];
      return {
        timeline: {
          ...state.timeline,
          tracks,
          selectedTrackId: result.track.id,
          selectedKeyframeId: result.keyframeId,
          selectedMotionPathId: null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          isPlaying: false,
        },
      };
    }),

  setTimelineEditorMode: (mode) =>
    set((state) => ({
      timeline: {
        ...state.timeline,
        editorMode: mode,
        isPlaying: false,
      },
    })),

  setTrackSpeedCurvePreset: (trackId, preset) =>
    set((state) => {
      const tracks = state.timeline.tracks.map((track) =>
        track.id === trackId
          ? { ...track, speedCurve: createDirectorSpeedCurve(preset) }
          : track,
      ) as DirectorTimelineTrack[];
      const timeline = { ...state.timeline, tracks, isPlaying: false };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  setTrackSpeedCurveControl: (trackId, handle, point) =>
    set((state) => {
      const controlPoint: [number, number] = [
        Math.min(Math.max(Number.isFinite(point[0]) ? point[0] : 0, 0), 1),
        Math.min(Math.max(Number.isFinite(point[1]) ? point[1] : 0, 0), 1),
      ];
      const tracks = state.timeline.tracks.map((track) =>
        track.id === trackId
          ? {
              ...track,
              speedCurve: {
                ...track.speedCurve,
                preset: "custom" as const,
                [handle === 1 ? "control1" : "control2"]: controlPoint,
              },
            }
          : track,
      ) as DirectorTimelineTrack[];
      const timeline = { ...state.timeline, tracks, isPlaying: false };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  applyCameraMotionPreset: (preset, mode, requestedTrackId) => {
    const state = get();
    const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
    const track = state.timeline.tracks.find(
      (item) => item.id === trackId && item.kind === "camera",
    );
    const camera = state.objects.find(
      (object) => object.id === track?.objectId && object.camera,
    );
    if (!track || track.kind !== "camera" || !camera?.camera) return false;

    if (camera.camera.followTargetId) {
      set((current) => ({
        timeline: {
          ...current.timeline,
          cameraMotionPreset: {
            ...current.timeline.cameraMotionPreset,
            error: {
              trackId: track.id,
              preset,
              mode,
              message: "跟随目标时不可使用预设运镜",
            },
          },
        },
      }));
      return false;
    }

    const lastKeyframe = track.keyframes[track.keyframes.length - 1];
    if (
      mode === "append" &&
      (!lastKeyframe ||
        lastKeyframe.time >= state.timeline.duration - 0.001)
    ) {
      set((current) => ({
        timeline: {
          ...current.timeline,
          cameraMotionPreset: {
            ...current.timeline.cameraMotionPreset,
            error: {
              trackId: track.id,
              preset,
              mode,
              message: "当前时间轴没有可追加的时长",
            },
          },
        },
      }));
      return false;
    }

    const startTime = mode === "replace" ? 0 : lastKeyframe.time;
    const endTime = state.timeline.duration;
    const startValue =
      mode === "replace"
        ? cloneCameraValue(camera)
        : cloneCameraKeyframeValue(lastKeyframe.value);
    if (!startValue) return false;
    const values = createDirectorCameraMotionPresetValues(preset, startValue);
    const createdAt = Date.now();
    const generated = values.map((value, index) => ({
      id: `${track.id}-preset-${preset}-${createdAt}-${index}`,
      time:
        startTime +
        (endTime - startTime) * (index / Math.max(values.length - 1, 1)),
      value: cloneCameraKeyframeValue(value),
    }));
    const keyframes =
      mode === "replace"
        ? generated
        : [...track.keyframes, ...generated.slice(1)];
    const tracks = state.timeline.tracks.map((item) =>
      item.id === track.id ? { ...track, keyframes } : item,
    ) as DirectorTimelineTrack[];
    const motionPaths = state.timeline.motionPaths.map((path) =>
      path.id === track.motionPathId ? { ...path, enabled: false } : path,
    );
    const timeline: DirectorTimelineState = {
      ...state.timeline,
      tracks,
      motionPaths,
      selectedTrackId: track.id,
      selectedKeyframeId: null,
      selectedMotionPathId: null,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      editorMode: "timeline",
      isPlaying: false,
      cameraMotionPreset: {
        application: {
          trackId: track.id,
          preset,
          mode,
          startTime,
          endTime,
          generatedKeyframeIds: generated.map((keyframe) => keyframe.id),
        },
        error: null,
      },
    };
    set({
      objects: applyTimelineAtTime(
        state.authoredObjects,
        timeline,
        timeline.currentTime,
        state.groups,
      ),
      timeline,
    });
    return true;
  },

  createMotionPath: (preset, requestedTrackId) =>
    set((state) => {
      const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      const object = state.objects.find(
        (item) => item.id === track?.objectId,
      );
      if (
        !track ||
        !object ||
        track.kind === "pose" ||
        track.kind === "group" ||
        object.camera?.followTargetId
      ) {
        return state;
      }
      const path = createMotionPathForTrack(object, preset);
      const timeline = {
        ...replaceTrackMotionPath(state.timeline, track, path),
        selectedMotionPathAnchorId: null,
        selectedMotionPathHandle: null,
        motionPathDraft: null,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  startMotionPathDrawing: (tool, requestedTrackId) =>
    set((state) => {
      const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      const object = state.objects.find(
        (item) => item.id === track?.objectId,
      );
      if (
        !track ||
        !object ||
        track.kind === "pose" ||
        track.kind === "group" ||
        object.camera?.followTargetId
      ) {
        return state;
      }
      return {
        viewMode: "director",
        selectedObjectId: object.id,
        timeline: {
          ...state.timeline,
          selectedTrackId: track.id,
          selectedKeyframeId: null,
          selectedMotionPathId: track.motionPathId ?? null,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
          motionPathDraft: {
            tool,
            trackId: track.id,
            objectId: object.id,
            planeY: object.transform.position[1],
            anchors: [],
          },
          isPlaying: false,
        },
      };
    }),

  appendMotionPathDraftAnchor: (position) =>
    set((state) => {
      const draft = state.timeline.motionPathDraft;
      if (!draft) return state;
      const safePosition = finiteTuple(position, [
        0,
        draft.planeY,
        0,
      ]);
      safePosition[1] = draft.planeY;
      const previous = draft.anchors[draft.anchors.length - 1];
      const minimumDistance = draft.tool === "pencil" ? 0.12 : 0.04;
      if (
        previous &&
        Math.hypot(
          safePosition[0] - previous.position[0],
          safePosition[1] - previous.position[1],
          safePosition[2] - previous.position[2],
        ) < minimumDistance
      ) {
        return state;
      }
      const anchor = createDirectorMotionPathAnchor(
        `director-motion-draft-${Date.now()}-${draft.anchors.length}`,
        safePosition,
      );
      return {
        timeline: {
          ...state.timeline,
          motionPathDraft: {
            ...draft,
            anchors: [...draft.anchors, anchor],
          },
        },
      };
    }),

  updateMotionPathDraftLastHandle: (worldPosition) =>
    set((state) => {
      const draft = state.timeline.motionPathDraft;
      const anchor = draft?.anchors[draft.anchors.length - 1];
      if (!draft || draft.tool !== "pen" || !anchor) return state;
      const safePosition = finiteTuple(worldPosition, anchor.position);
      safePosition[1] = draft.planeY;
      const handleOut: DirectorTuple3 = [
        safePosition[0] - anchor.position[0],
        safePosition[1] - anchor.position[1],
        safePosition[2] - anchor.position[2],
      ];
      const hasHandle =
        Math.hypot(handleOut[0], handleOut[1], handleOut[2]) >= 0.04;
      const anchors = draft.anchors.map((item) =>
        item.id === anchor.id
          ? {
              ...item,
              type: hasHandle ? ("symmetric" as const) : ("vertex" as const),
              handleIn: hasHandle
                ? (handleOut.map((value) => -value) as DirectorTuple3)
                : ([0, 0, 0] as DirectorTuple3),
              handleOut: hasHandle
                ? handleOut
                : ([0, 0, 0] as DirectorTuple3),
            }
          : item,
      );
      return {
        timeline: {
          ...state.timeline,
          motionPathDraft: { ...draft, anchors },
        },
      };
    }),

  finishMotionPathDrawing: () =>
    set((state) => {
      const draft = state.timeline.motionPathDraft;
      const track = state.timeline.tracks.find(
        (item) => item.id === draft?.trackId,
      );
      if (!draft || !track || !isDirectorMotionPathValid(draft.anchors)) {
        return {
          timeline: {
            ...state.timeline,
            motionPathDraft: null,
            selectedMotionPathAnchorId: null,
            selectedMotionPathHandle: null,
          },
        };
      }
      const pathId = `director-motion-path-${draft.objectId}-${Date.now()}`;
      const anchors = draft.anchors.map((anchor, index) => ({
        ...anchor,
        id: `${pathId}-anchor-${index}`,
        position: [...anchor.position] as DirectorTuple3,
        handleIn: [...anchor.handleIn] as DirectorTuple3,
        handleOut: [...anchor.handleOut] as DirectorTuple3,
      }));
      const toolLabel = draft.tool === "pencil" ? "铅笔路径" : "钢笔路径";
      const toolCount =
        state.timeline.motionPaths.filter((path) => path.preset === draft.tool)
          .length + 1;
      const path: DirectorMotionPath = {
        id: pathId,
        objectId: draft.objectId,
        name: `${toolLabel}${toolCount}`,
        preset: draft.tool,
        enabled: true,
        orientToPath: false,
        closed: false,
        pivot: getDirectorMotionPathPivot(anchors),
        transform: createDirectorMotionPathTransform(),
        initialAnchors: cloneDirectorMotionPathAnchors(anchors),
        anchors,
        points: buildDirectorMotionPathPoints(anchors, false),
      };
      const timeline = {
        ...replaceTrackMotionPath(state.timeline, track, path),
        selectedMotionPathAnchorId: anchors[0]?.id ?? null,
        selectedMotionPathHandle: null,
        motionPathDraft: null,
      };
      return {
        selectedObjectId: draft.objectId,
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  cancelMotionPathDrawing: () =>
    set((state) => ({
      timeline: {
        ...state.timeline,
        motionPathDraft: null,
        selectedMotionPathAnchorId: null,
        selectedMotionPathHandle: null,
        isPlaying: false,
      },
    })),

  selectMotionPathAnchor: (pathId, anchorId, handle = null) =>
    set((state) => {
      const path = state.timeline.motionPaths.find(
        (item) => item.id === pathId,
      );
      const anchor = path?.anchors.find((item) => item.id === anchorId);
      const track = state.timeline.tracks.find(
        (item) => item.motionPathId === pathId,
      );
      if (!path || !anchor || !track) return state;
      return {
        selectedObjectId: track.objectId,
        viewMode: "director",
        timeline: {
          ...state.timeline,
          selectedTrackId: track.id,
          selectedKeyframeId: null,
          selectedMotionPathId: path.id,
          selectedMotionPathAnchorId: anchor.id,
          selectedMotionPathHandle: handle,
          motionPathDraft: null,
          isPlaying: false,
        },
      };
    }),

  updateMotionPathAnchorPosition: (pathId, anchorId, position) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      const currentAnchor = currentPath?.anchors.find(
        (anchor) => anchor.id === anchorId,
      );
      if (!currentPath || !currentAnchor) return state;
      const anchors = currentPath.anchors.map((anchor) =>
        anchor.id === anchorId
          ? {
              ...anchor,
              position: finiteTuple(position, anchor.position),
            }
          : anchor,
      );
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? rebuildMotionPath(path, anchors) : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        selectedMotionPathAnchorId: anchorId,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  updateMotionPathAnchorWorldPosition: (pathId, anchorId, position) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      const currentAnchor = currentPath?.anchors.find(
        (anchor) => anchor.id === anchorId,
      );
      if (!currentPath || !currentAnchor) return state;
      const localPosition = inverseTransformDirectorMotionPathPoint(
        finiteTuple(
          position,
          transformDirectorMotionPathPoint(
            currentAnchor.position,
            currentPath.pivot,
            currentPath.transform,
          ),
        ),
        currentPath.pivot,
        currentPath.transform,
      );
      const anchors = currentPath.anchors.map((anchor) =>
        anchor.id === anchorId
          ? { ...anchor, position: localPosition }
          : anchor,
      );
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? rebuildMotionPath(path, anchors) : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        selectedMotionPathAnchorId: anchorId,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  updateMotionPathAnchorHandle: (pathId, anchorId, handle, value) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      const currentAnchor = currentPath?.anchors.find(
        (anchor) => anchor.id === anchorId,
      );
      if (!currentPath || !currentAnchor || currentAnchor.type === "vertex") {
        return state;
      }
      const safeValue = finiteTuple(
        value,
        handle === "in"
          ? currentAnchor.handleIn
          : currentAnchor.handleOut,
      );
      const opposite = safeValue.map(
        (item) => -item,
      ) as DirectorTuple3;
      const anchors = currentPath.anchors.map((anchor) => {
        if (anchor.id !== anchorId) return anchor;
        if (handle === "in") {
          return {
            ...anchor,
            handleIn: safeValue,
            handleOut:
              anchor.type === "symmetric" ? opposite : anchor.handleOut,
          };
        }
        return {
          ...anchor,
          handleOut: safeValue,
          handleIn:
            anchor.type === "symmetric" ? opposite : anchor.handleIn,
        };
      });
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? rebuildMotionPath(path, anchors) : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        selectedMotionPathAnchorId: anchorId,
        selectedMotionPathHandle: handle,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  updateMotionPathAnchorWorldHandle: (
    pathId,
    anchorId,
    handle,
    position,
  ) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      const currentAnchor = currentPath?.anchors.find(
        (anchor) => anchor.id === anchorId,
      );
      if (!currentPath || !currentAnchor || currentAnchor.type === "vertex") {
        return state;
      }
      const worldAnchorPosition = transformDirectorMotionPathPoint(
        currentAnchor.position,
        currentPath.pivot,
        currentPath.transform,
      );
      const safePosition = finiteTuple(position, worldAnchorPosition);
      const localValue = inverseTransformDirectorMotionPathVector(
        [
          safePosition[0] - worldAnchorPosition[0],
          safePosition[1] - worldAnchorPosition[1],
          safePosition[2] - worldAnchorPosition[2],
        ],
        currentPath.transform,
      );
      const opposite = localValue.map(
        (item) => -item,
      ) as DirectorTuple3;
      const anchors = currentPath.anchors.map((anchor) => {
        if (anchor.id !== anchorId) return anchor;
        if (handle === "in") {
          return {
            ...anchor,
            handleIn: localValue,
            handleOut:
              anchor.type === "symmetric" ? opposite : anchor.handleOut,
          };
        }
        return {
          ...anchor,
          handleOut: localValue,
          handleIn:
            anchor.type === "symmetric" ? opposite : anchor.handleIn,
        };
      });
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? rebuildMotionPath(path, anchors) : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        selectedMotionPathAnchorId: anchorId,
        selectedMotionPathHandle: handle,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  setMotionPathAnchorType: (pathId, anchorId, type) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath) return state;
      const anchors = setDirectorMotionPathAnchorType(
        currentPath.anchors,
        anchorId,
        type,
        currentPath.closed,
      );
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? rebuildMotionPath(path, anchors) : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        selectedMotionPathAnchorId: anchorId,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  insertMotionPathAnchor: (requestedPathId, requestedAnchorId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      const anchorId =
        requestedAnchorId ?? state.timeline.selectedMotionPathAnchorId;
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      const index = currentPath?.anchors.findIndex(
        (anchor) => anchor.id === anchorId,
      );
      if (!currentPath || index === undefined || index < 0) return state;
      const current = currentPath.anchors[index];
      const next =
        currentPath.anchors[index + 1] ??
        (currentPath.closed ? currentPath.anchors[0] : null);
      const position: DirectorTuple3 = next
        ? [
            (current.position[0] + next.position[0]) / 2,
            (current.position[1] + next.position[1]) / 2,
            (current.position[2] + next.position[2]) / 2,
          ]
        : [
            current.position[0] + 0.8,
            current.position[1],
            current.position[2],
          ];
      const anchor = createDirectorMotionPathAnchor(
        `${currentPath.id}-anchor-${Date.now()}`,
        position,
      );
      const anchors = [
        ...currentPath.anchors.slice(0, index + 1),
        anchor,
        ...currentPath.anchors.slice(index + 1),
      ];
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === currentPath.id
          ? rebuildMotionPath(path, anchors)
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: currentPath.id,
        selectedMotionPathAnchorId: anchor.id,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  deleteMotionPathAnchor: (requestedPathId, requestedAnchorId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      const anchorId =
        requestedAnchorId ?? state.timeline.selectedMotionPathAnchorId;
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath || !anchorId || currentPath.anchors.length <= 2) {
        return state;
      }
      const index = currentPath.anchors.findIndex(
        (anchor) => anchor.id === anchorId,
      );
      if (index < 0) return state;
      const anchors = currentPath.anchors.filter(
        (anchor) => anchor.id !== anchorId,
      );
      const closed = currentPath.closed && anchors.length >= 3;
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === currentPath.id
          ? rebuildMotionPath(path, anchors, closed)
          : path,
      );
      const nextAnchor = anchors[Math.min(index, anchors.length - 1)];
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: currentPath.id,
        selectedMotionPathAnchorId: nextAnchor?.id ?? null,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  toggleMotionPathClosed: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath || (!currentPath.closed && currentPath.anchors.length < 3)) {
        return state;
      }
      const closed = !currentPath.closed;
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === currentPath.id
          ? rebuildMotionPath(path, path.anchors, closed)
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: currentPath.id,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  renameMotionPath: (pathId, name) =>
    set((state) => ({
      timeline: {
        ...state.timeline,
        motionPaths: state.timeline.motionPaths.map((path) =>
          path.id === pathId ? { ...path, name } : path,
        ),
      },
    })),

  updateMotionPathTransform: (pathId, field, axis, value) =>
    set((state) => {
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath) return state;
      const fallback = currentPath.transform[field][axis];
      const finiteValue = Number.isFinite(value) ? value : fallback;
      const nextValue =
        field === "scale"
          ? Math.min(Math.max(finiteValue, 0.05), 20)
          : finiteValue;
      const tuple: DirectorTuple3 = [...currentPath.transform[field]];
      tuple[axis] = nextValue;
      const transform: DirectorTransform = {
        ...currentPath.transform,
        [field]: tuple,
      };
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId
          ? rebuildMotionPath(path, path.anchors, path.closed, transform)
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  resetMotionPathOffset: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath) return state;
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === currentPath.id
          ? rebuildMotionPath(
              path,
              path.anchors,
              path.closed,
              createDirectorMotionPathTransform(),
            )
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: currentPath.id,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  resetMotionPath: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      const currentPath = state.timeline.motionPaths.find(
        (path) => path.id === pathId,
      );
      if (!currentPath) return state;
      const anchors = cloneDirectorMotionPathAnchors(
        currentPath.initialAnchors,
      );
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === currentPath.id
          ? rebuildMotionPath(
              path,
              anchors,
              path.closed,
              createDirectorMotionPathTransform(),
              getDirectorMotionPathPivot(anchors),
            )
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: currentPath.id,
        selectedMotionPathAnchorId: anchors[0]?.id ?? null,
        selectedMotionPathHandle: null,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  toggleMotionPathEnabled: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      if (!pathId) return state;
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId ? { ...path, enabled: !path.enabled } : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  toggleMotionPathOrient: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      if (!pathId) return state;
      const track = state.timeline.tracks.find(
        (item) => item.motionPathId === pathId,
      );
      if (track?.kind !== "transform") return state;
      const motionPaths = state.timeline.motionPaths.map((path) =>
        path.id === pathId
          ? { ...path, orientToPath: !path.orientToPath }
          : path,
      );
      const timeline = {
        ...state.timeline,
        motionPaths,
        selectedMotionPathId: pathId,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.authoredObjects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  deleteMotionPath: (requestedPathId) => {
    const pathId = requestedPathId ?? get().timeline.selectedMotionPathId;
    if (!pathId) {
      const state = get();
      const result = makeDirectorCommandResult(state, {
        commandKind: "DELETE_MOTION_PATH",
        disposition: "NOOP",
        reason: "DIRECTOR_COMMAND_NO_CHANGE",
      });
      set({ lastCommandResult: result });
      return result;
    }
    return get().deleteDirectorEntity({
      kind: "DELETE_MOTION_PATH",
      pathId,
    });
  },
}));

useDirectorStore.subscribe((state, previousState) => {
  if (state.projectId) {
    rememberDirectorCaptures(state.projectId, state.captures);
    rememberDirectorHistory(state.projectId, state.history);
  }

  const current = getDirectorDocumentSnapshot(state);
  const previous = getDirectorDocumentSnapshot(previousState);
  if (
    !current ||
    !previous ||
    current.projectId !== previous.projectId ||
    current.generation !== previous.generation ||
    !isSameDirectorProjectOwner(
      state.projectOwner ?? { route: "libtv", canvasId: "", sourceNodeId: "" },
      previousState.projectOwner ?? {
        route: "libtv",
        canvasId: "",
        sourceNodeId: "",
      },
    ) ||
    current.fingerprint === previous.fingerprint ||
    directorHistorySyncSuspended ||
    state.history.activeGesture
  ) {
    return;
  }

  if (
    !updateActiveDirectorDocument(
      state,
      current.document,
      state.captures,
    )
  ) {
    const result = makeDirectorCommandResult(state, {
      commandKind: "PROJECT_MUTATION",
      disposition: "STALE",
      reason: "DIRECTOR_OWNER_STALE",
    });
    directorHistorySyncSuspended = true;
    try {
      useDirectorStore.setState({ lastCommandResult: result });
    } finally {
      directorHistorySyncSuspended = false;
    }
    return;
  }

  const result = makeDirectorCommandResult(state, {
    commandKind: "PROJECT_MUTATION",
    disposition: "COMMITTED",
    projectChanged: true,
    historyEntries: 1,
  });
  const entry = createDirectorHistoryEntry({
    commandId: result.commandId,
    commandKind: "PROJECT_MUTATION",
    projectId: current.projectId,
    generation: current.generation,
    before: previous.document,
    after: current.document,
  });
  const history = pushDirectorHistory(state.history, entry);
  rememberDirectorHistory(current.projectId, history);
  directorHistorySyncSuspended = true;
  try {
    useDirectorStore.setState({
      history,
      lastCommandResult: result,
    });
  } finally {
    directorHistorySyncSuspended = false;
  }
});

if (typeof window !== "undefined") {
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
      __director_project_registry_snapshot:
        typeof getDirectorProjectRegistrySnapshot;
      __director_project_persistence_snapshot:
        typeof getDirectorProjectPersistenceSnapshot;
      __director_async_authority_snapshot: () => ReturnType<
        typeof directorAsyncAuthority.getSnapshot
      >;
    }
  ).__director_store = useDirectorStore;
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
      __director_project_registry_snapshot:
        typeof getDirectorProjectRegistrySnapshot;
      __director_project_persistence_snapshot:
        typeof getDirectorProjectPersistenceSnapshot;
      __director_async_authority_snapshot: () => ReturnType<
        typeof directorAsyncAuthority.getSnapshot
      >;
    }
  ).__director_project_registry_snapshot =
    getDirectorProjectRegistrySnapshot;
  (
    window as unknown as {
      __director_project_persistence_snapshot:
        typeof getDirectorProjectPersistenceSnapshot;
    }
  ).__director_project_persistence_snapshot =
    getDirectorProjectPersistenceSnapshot;
  (
    window as unknown as {
      __director_async_authority_snapshot: () => ReturnType<
        typeof directorAsyncAuthority.getSnapshot
      >;
    }
  ).__director_async_authority_snapshot = () =>
    directorAsyncAuthority.getSnapshot();
}
