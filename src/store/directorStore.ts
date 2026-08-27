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

interface DirectorState {
  sourceNodeId: string | null;
  projectOwner: DirectorProjectOwnerV1 | null;
  projectId: string | null;
  sessionId: string | null;
  generation: number | null;
  projectLifecycle: DirectorProjectLifecycle | null;
  scene: DirectorScene;
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

  openSession: (owner: DirectorProjectOwnerV1) => DirectorProjectOpenResult;
  closeSession: (
    expectedOwner?: DirectorProjectOwnerV1,
  ) => DirectorProjectCloseResult;
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
  removeLocalModelLibraryItem: (assetId: string) => void;
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
  ) => void;
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
  removeCapture: (captureId: string) => void;
  clearCaptures: () => void;
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
  removeTimelineTrack: (trackId?: string) => void;
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
  deleteMotionPath: (pathId?: string) => void;
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
  const object = state.objects.find(
    (item) => item.id === objectId && item.kind === "character",
  );
  if (!object) return state;
  const updatedObject: DirectorObject = {
    ...object,
    characterRig: cloneDirectorCharacterRig(rig),
  };
  const objects = state.objects.map((item) =>
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
  return {
    objects,
    timeline: {
      ...state.timeline,
      tracks,
      selectedTrackId: result.track.id,
      selectedKeyframeId: result.keyframeId,
      selectedMotionPathId: null,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      isPlaying: false,
    },
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
    objects: state.objects,
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
  const objects = applyTimelineAtTime(
    restored.objects,
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

  openSession: (owner) => {
    const currentState = get();
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
    }

    const result = directorProjectRegistry.open({
      owner,
      createDocument: createDefaultDirectorProjectDocument,
    });
    if (
      result.disposition !== "REJECTED" &&
      result.record &&
      result.session &&
      result.disposition !== "FOCUSED"
    ) {
      set(
        restoreDirectorProjectState(
          result.record,
          result.session,
          currentState.localModelLibrary,
        ),
      );
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
      }));
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

  ungroupSelectedCharacters: () =>
    set((state) => {
      const group = state.groups.find(
        (item) => item.id === state.selectedGroupId,
      );
      if (!group) return state;
      const tracks = state.timeline.tracks.filter(
        (track) => track.kind !== "group" || track.groupId !== group.id,
      );
      const selectedTrackRemoved = state.timeline.tracks.some(
        (track) =>
          track.id === state.timeline.selectedTrackId &&
          track.kind === "group" &&
          track.groupId === group.id,
      );
      return {
        groups: state.groups.filter((item) => item.id !== group.id),
        selectedObjectId:
          group.characterIds[group.characterIds.length - 1] ?? null,
        selectedObjectIds: [...group.characterIds],
        selectedGroupId: null,
        timeline: {
          ...state.timeline,
          tracks,
          selectedTrackId: selectedTrackRemoved
            ? tracks[0]?.id ?? null
            : state.timeline.selectedTrackId,
          selectedKeyframeId: null,
          isPlaying: false,
        },
      };
    }),

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
      return {
        objects: [...state.objects, ...characters],
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

  removeLocalModelLibraryItem: (assetId) =>
    set((state) => {
      const localModelLibrary = state.localModelLibrary.filter(
        (item) => item.id !== assetId,
      );
      writePersistedLocalModelLibrary(localModelLibrary);
      const removedObjectIds = new Set(
        state.objects
          .filter(
            (object) =>
              object.libraryAssetId === assetId &&
              object.libraryCategoryId === "my-models",
          )
          .map((object) => object.id),
      );
      if (removedObjectIds.size === 0) {
        return { localModelLibrary };
      }

      const tracks = state.timeline.tracks.filter(
        (track) => !removedObjectIds.has(track.objectId),
      );
      const removedTrackIds = new Set(
        state.timeline.tracks
          .filter((track) => removedObjectIds.has(track.objectId))
          .map((track) => track.id),
      );
      const motionPaths = state.timeline.motionPaths.filter(
        (path) => !removedObjectIds.has(path.objectId),
      );
      const removedMotionPathIds = new Set(
        state.timeline.motionPaths
          .filter((path) => removedObjectIds.has(path.objectId))
          .map((path) => path.id),
      );
      const selectedTrackRemoved =
        state.timeline.selectedTrackId !== null &&
        removedTrackIds.has(state.timeline.selectedTrackId);
      const selectedPathRemoved =
        state.timeline.selectedMotionPathId !== null &&
        removedMotionPathIds.has(state.timeline.selectedMotionPathId);
      return {
        localModelLibrary,
        objects: state.objects.filter(
          (object) => !removedObjectIds.has(object.id),
        ),
        selectedObjectId: removedObjectIds.has(state.selectedObjectId ?? "")
          ? null
          : state.selectedObjectId,
        selectedObjectIds: state.selectedObjectIds.filter(
          (objectId) => !removedObjectIds.has(objectId),
        ),
        timeline: {
          ...state.timeline,
          tracks,
          motionPaths,
          selectedTrackId: selectedTrackRemoved
            ? tracks[0]?.id ?? null
            : state.timeline.selectedTrackId,
          selectedKeyframeId: selectedTrackRemoved
            ? null
            : state.timeline.selectedKeyframeId,
          selectedMotionPathId: selectedPathRemoved
            ? null
            : state.timeline.selectedMotionPathId,
          selectedMotionPathAnchorId: selectedPathRemoved
            ? null
            : state.timeline.selectedMotionPathAnchorId,
          selectedMotionPathHandle: selectedPathRemoved
            ? null
            : state.timeline.selectedMotionPathHandle,
          motionPathDraft:
            state.timeline.motionPathDraft &&
            removedTrackIds.has(state.timeline.motionPathDraft.trackId)
              ? null
              : state.timeline.motionPathDraft,
          isPlaying: false,
        },
      };
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
      return {
        objects: [...state.objects, object],
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
      return {
        objects: resolveCameraRelations(
          applyDirectorGroupTransform(state.objects, group, transform),
        ),
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
      const objects = state.objects.map((object) =>
        object.id === objectId ? { ...object, ...patch } : object,
      );
      return {
        objects,
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

  updateObjectTransform: (objectId, field, axis, value) =>
    set((state) => {
      const objects = state.objects.map((object) =>
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
      return { objects: resolveCameraRelations(objects) };
    }),

  updateCamera: (objectId, patch) =>
    set((state) => {
      const current = state.objects.find((object) => object.id === objectId);
      const restoreOrdinaryCamera =
        Boolean(current?.camera?.followTargetId) &&
        patch.followTargetId === null;
      const sourceObjects = restoreOrdinaryCamera
        ? sampleTimelineObjectsAtTime(
            state.objects,
            state.timeline,
            state.timeline.currentTime,
            state.groups,
          )
        : state.objects;
      const objects = sourceObjects.map((object) =>
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
      return { objects: resolveCameraRelations(objects) };
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
    set((state) => {
      const captures = state.captures.filter(
        (capture) => capture.id !== captureId,
      );
      return {
        captures,
        activeCaptureId:
          state.activeCaptureId === captureId
            ? captures[0]?.id ?? null
            : state.activeCaptureId,
      };
    }),

  clearCaptures: () => set({ captures: [], activeCaptureId: null }),

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
        state.objects,
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
    const restoredObjects = state.objects.map((object) =>
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

    set((current) => ({
      objects: [...restoredObjects, camera],
      selectedObjectId: cameraId,
      activeCameraId: cameraId,
      viewMode: "camera",
      timeline: {
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
      },
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
    }));
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
          state.objects,
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
              state.objects,
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
          state.objects,
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
          state.objects,
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

  removeTimelineTrack: (requestedTrackId) =>
    set((state) => {
      const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
      if (!trackId) return state;
      const tracks = state.timeline.tracks.filter(
        (track) => track.id !== trackId,
      );
      const removedTrack = state.timeline.tracks.find(
        (track) => track.id === trackId,
      );
      const motionPaths = state.timeline.motionPaths.filter(
        (path) => path.id !== removedTrack?.motionPathId,
      );
      return {
        timeline: {
          ...state.timeline,
          tracks,
          motionPaths,
          selectedTrackId:
            state.timeline.selectedTrackId === trackId
              ? tracks[0]?.id ?? null
              : state.timeline.selectedTrackId,
          selectedKeyframeId: null,
          selectedMotionPathId:
            state.timeline.selectedMotionPathId === removedTrack?.motionPathId
              ? null
              : state.timeline.selectedMotionPathId,
          selectedMotionPathAnchorId:
            state.timeline.selectedMotionPathId === removedTrack?.motionPathId
              ? null
              : state.timeline.selectedMotionPathAnchorId,
          selectedMotionPathHandle:
            state.timeline.selectedMotionPathId === removedTrack?.motionPathId
              ? null
              : state.timeline.selectedMotionPathHandle,
          motionPathDraft:
            state.timeline.motionPathDraft?.trackId === trackId
              ? null
              : state.timeline.motionPathDraft,
          isPlaying: false,
        },
      };
    }),

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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
        state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
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
          state.objects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),

  deleteMotionPath: (requestedPathId) =>
    set((state) => {
      const pathId = requestedPathId ?? state.timeline.selectedMotionPathId;
      if (!pathId) return state;
      const tracks = state.timeline.tracks.map((track) =>
        track.motionPathId === pathId
          ? { ...track, motionPathId: undefined }
          : track,
      ) as DirectorTimelineTrack[];
      const motionPaths = state.timeline.motionPaths.filter(
        (path) => path.id !== pathId,
      );
      const timeline: DirectorTimelineState = {
        ...state.timeline,
        tracks,
        motionPaths,
        selectedMotionPathId: null,
        selectedMotionPathAnchorId: null,
        selectedMotionPathHandle: null,
        motionPathDraft:
          state.timeline.motionPathDraft?.trackId ===
          state.timeline.tracks.find((track) => track.motionPathId === pathId)?.id
            ? null
            : state.timeline.motionPathDraft,
        isPlaying: false,
      };
      return {
        objects: applyTimelineAtTime(
          state.objects,
          timeline,
          timeline.currentTime,
          state.groups,
        ),
        timeline,
      };
    }),
}));

if (typeof window !== "undefined") {
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
      __director_project_registry_snapshot:
        typeof getDirectorProjectRegistrySnapshot;
    }
  ).__director_store = useDirectorStore;
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
      __director_project_registry_snapshot:
        typeof getDirectorProjectRegistrySnapshot;
    }
  ).__director_project_registry_snapshot =
    getDirectorProjectRegistrySnapshot;
}
