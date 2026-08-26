"use client";

import { create } from "zustand";
import {
  clampDirectorTimelineTime,
  sampleDirectorTimelineTrack,
} from "@/components/director/directorTimelineMath";
import {
  createDirectorSpeedCurve,
  getDirectorPathYaw,
  getDirectorTrackProgress,
  sampleDirectorMotionPath,
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

export type DirectorMotionPathPreset = "line" | "ring" | "rectangle";

export interface DirectorMotionPath {
  id: string;
  objectId: string;
  name: string;
  preset: DirectorMotionPathPreset;
  enabled: boolean;
  orientToPath: boolean;
  closed: boolean;
  points: DirectorTuple3[];
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

  openSession: (sourceNodeId: string) => void;
  selectObject: (objectId: string | null) => void;
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
  setCapturing: (capturing: boolean) => void;
  addCapture: (capture: DirectorCapture) => void;
  markCaptureSent: (captureId: string, nodeId: string) => void;
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
    preset: DirectorMotionPathPreset,
    trackId?: string,
  ) => void;
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

function createMotionPathForTrack(
  object: DirectorObject,
  preset: DirectorMotionPathPreset,
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

  return {
    id: `director-motion-path-${object.id}-${Date.now()}`,
    objectId: object.id,
    name: fallbackName,
    preset,
    enabled: true,
    orientToPath: false,
    closed,
    points,
  };
}

function applyTimelineAtTime(
  objects: DirectorObject[],
  timeline: DirectorTimelineState,
  time: number,
): DirectorObject[] {
  const tracksByObject = new Map(
    timeline.tracks.map((track) => [track.objectId, track]),
  );
  const pathsById = new Map(
    timeline.motionPaths.map((path) => [path.id, path]),
  );
  return objects.map((object) => {
    const track = tracksByObject.get(object.id);
    if (!track) return object;
    const sample = sampleDirectorTimelineTrack(track, time);
    if (!sample) return object;
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
    if (sample.kind === "camera" && object.camera) {
      return {
        ...object,
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
      ...object,
      transform,
    };
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

  const keyframes = [
    ...track.keyframes.filter((keyframe) => keyframe.id !== existing?.id),
    { id: keyframeId, time, value: cloneTransform(object.transform) },
  ].sort((a, b) => a.time - b.time);
  return { track: { ...track, keyframes }, keyframeId };
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

export const useDirectorStore = create<DirectorState>((set) => ({
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

  openSession: (sourceNodeId) =>
    set((state) => ({
      sourceNodeId,
      selectedObjectId: state.selectedObjectId ?? "director-character-lead",
      timeline: { ...state.timeline, isPlaying: false },
    })),

  selectObject: (objectId) => set({ selectedObjectId: objectId }),

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
                        track.kind === "camera" ? "机位" : "变换"
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
        (track) => track.objectId === object.id,
      );
      if (existing) {
        return {
          timeline: {
            ...state.timeline,
            selectedTrackId: existing.id,
            selectedKeyframeId: null,
            selectedMotionPathId: existing.motionPathId ?? null,
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
        (track) => track.objectId === objectId,
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
      if (!track || !object) return state;
      const path = createMotionPathForTrack(object, preset);
      const tracks = state.timeline.tracks.map((item) =>
        item.id === track.id ? { ...item, motionPathId: path.id } : item,
      ) as DirectorTimelineTrack[];
      const motionPaths = [
        ...state.timeline.motionPaths.filter(
          (item) => item.id !== track.motionPathId,
        ),
        path,
      ];
      const timeline: DirectorTimelineState = {
        ...state.timeline,
        tracks,
        motionPaths,
        selectedTrackId: track.id,
        selectedKeyframeId: null,
        selectedMotionPathId: path.id,
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
