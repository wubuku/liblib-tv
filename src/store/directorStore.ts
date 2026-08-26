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

export type DirectorTuple3 = [number, number, number];
export type DirectorViewMode = "director" | "camera";
export type DirectorTransformMode = "translate" | "rotate" | "scale";
export type DirectorAspectRatio = "16:9" | "9:16" | "1:1";
export type DirectorObjectKind = "character" | "prop" | "camera";
export type DirectorPrimitive = "character" | "table" | "mug" | "wall" | "camera";

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
  characterRig?: DirectorCharacterRig;
  camera?: {
    fov: number;
    target: DirectorTuple3;
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
}

interface DirectorState {
  sourceNodeId: string | null;
  scene: DirectorScene;
  objects: DirectorObject[];
  selectedObjectId: string | null;
  activeCameraId: string;
  viewMode: DirectorViewMode;
  transformMode: DirectorTransformMode;
  aspectRatio: DirectorAspectRatio;
  showThirds: boolean;
  isCapturing: boolean;
  captures: DirectorCapture[];
  activeCaptureId: string | null;
  timeline: DirectorTimelineState;
  phoneVcam: DirectorPhoneVcamState;

  openSession: (sourceNodeId: string) => void;
  selectObject: (
    objectId: string | null,
    source?: "explicit" | "viewport",
  ) => void;
  setViewMode: (mode: DirectorViewMode) => void;
  setTransformMode: (mode: DirectorTransformMode) => void;
  setAspectRatio: (ratio: DirectorAspectRatio) => void;
  toggleThirds: () => void;
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
      ? { ...object.camera, target: [...object.camera.target] }
      : undefined,
    characterRig: object.characterRig
      ? cloneDirectorCharacterRig(object.characterRig)
      : undefined,
  }));
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

function applyTimelineAtTime(
  objects: DirectorObject[],
  timeline: DirectorTimelineState,
  time: number,
): DirectorObject[] {
  const tracksByObject = new Map<string, DirectorTimelineTrack[]>();
  timeline.tracks.forEach((track) => {
    const tracks = tracksByObject.get(track.objectId) ?? [];
    tracks.push(track);
    tracksByObject.set(track.objectId, tracks);
  });
  const pathsById = new Map(
    timeline.motionPaths.map((path) => [path.id, path]),
  );
  return objects.map((object) => {
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

export const useDirectorStore = create<DirectorState>((set, get) => ({
  sourceNodeId: null,
  scene: {
    name: "第一集：咖啡馆对峙",
    backgroundColor: "#20252b",
    groundColor: "#30343a",
    showGround: true,
    showGrid: true,
  },
  objects: cloneObjects(),
  selectedObjectId: "director-character-lead",
  activeCameraId: "director-camera-main",
  viewMode: "director",
  transformMode: "translate",
  aspectRatio: "16:9",
  showThirds: false,
  isCapturing: false,
  captures: [],
  activeCaptureId: null,
  timeline: createDefaultTimeline(),
  phoneVcam: createDefaultPhoneVcamState(),

  openSession: (sourceNodeId) =>
    set((state) => ({
      sourceNodeId,
      selectedObjectId: state.selectedObjectId ?? "director-character-lead",
      timeline: { ...state.timeline, isPlaying: false },
      phoneVcam:
        state.phoneVcam.status === "recording"
          ? {
              ...state.phoneVcam,
              status: "local-ready",
              recordingStartTime: null,
              sampleCount: 0,
              error: null,
            }
          : state.phoneVcam,
    })),

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
        timeline: {
          ...state.timeline,
          selectedMotionPathAnchorId: null,
          selectedMotionPathHandle: null,
        },
      };
    }),

  setViewMode: (mode) =>
    set((state) => ({
      viewMode: mode,
      selectedObjectId: mode === "camera" ? state.activeCameraId : state.selectedObjectId,
    })),

  setTransformMode: (mode) => set({ transformMode: mode }),

  setAspectRatio: (ratio) => set({ aspectRatio: ratio }),

  toggleThirds: () => set((state) => ({ showThirds: !state.showThirds })),

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
    set((state) => ({
      objects: state.objects.map((object) =>
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
    })),

  updateCamera: (objectId, patch) =>
    set((state) => ({
      objects: state.objects.map((object) =>
        object.id === objectId && object.camera
          ? {
              ...object,
              camera: {
                ...object.camera,
                ...patch,
                target: patch.target
                  ? [...patch.target]
                  : [...object.camera.target],
              },
            }
          : object,
      ),
    })),

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
      return {
        selectedObjectId: track.objectId,
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
      return {
        selectedObjectId: track.objectId,
        objects: applyTimelineAtTime(
          state.objects,
          state.timeline,
          keyframe.time,
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
        ),
        timeline,
      };
    }),

  createMotionPath: (preset, requestedTrackId) =>
    set((state) => {
      const trackId = requestedTrackId ?? state.timeline.selectedTrackId;
      const track = state.timeline.tracks.find((item) => item.id === trackId);
      const object = state.objects.find(
        (item) => item.id === track?.objectId,
      );
      if (!track || !object || track.kind === "pose") return state;
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
      if (!track || !object || track.kind === "pose") return state;
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
        ),
        timeline,
      };
    }),
}));

if (typeof window !== "undefined") {
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
    }
  ).__director_store = useDirectorStore;
}
