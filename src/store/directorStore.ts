"use client";

import { create } from "zustand";

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

  openSession: (sourceNodeId) =>
    set((state) => ({
      sourceNodeId,
      selectedObjectId: state.selectedObjectId ?? "director-character-lead",
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
    set((state) => ({
      objects: state.objects.map((object) =>
        object.id === objectId ? { ...object, ...patch } : object,
      ),
    })),

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
}));

if (typeof window !== "undefined") {
  (
    window as unknown as {
      __director_store: typeof useDirectorStore;
    }
  ).__director_store = useDirectorStore;
}

