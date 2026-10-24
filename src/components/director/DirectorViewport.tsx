"use client";

import type { ElementRef, ReactNode } from "react";

import {
  createContext,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  useContext,
  type ChangeEvent,
  type CSSProperties,
} from "react";
import {
  Camera,
  Check,
  Boxes,
  Eye,
  Film,
  Grid3X3,
  ImagePlus,
  Move3D,
  PanelLeftOpen,
  PanelRightOpen,
  Plus,
  Rotate3D,
  RotateCcw,
  Search,
  Scaling,
  Smartphone,
  Users,
  X,
} from "lucide-react";
import {
  GizmoHelper,
  GizmoViewport,
  Html,
  Line,
  OrbitControls,
  TransformControls,
} from "@react-three/drei";
import {
  Canvas,
  useFrame,
  useThree,
  type ThreeEvent,
} from "@react-three/fiber";
import {
  DoubleSide,
  BackSide,
  Matrix4,
  MathUtils,
  Object3D,
  PerspectiveCamera,
  Quaternion,
  Texture,
  TextureLoader,
  Vector3,
  type Group,
  type MeshStandardMaterialParameters,
} from "three";
import { cn } from "@/lib/utils";
import {
  buildDirectorCameraUpdateEvent,
  resolveDirectorTelemetryCameraId,
} from "@/lib/directorTelemetry";
import {
  createDirectorAsyncIdentity,
  directorAsyncAuthority,
  type DirectorAsyncIngressContextV1,
  type DirectorAsyncOperationDescriptorV1,
  type DirectorAsyncOwnerSnapshotV1,
  type DirectorAsyncResultEnvelopeV1,
} from "@/lib/directorAsyncAuthority";
import { directorDocumentFingerprint } from "@/lib/directorCommandKernel";
import {
  DirectorLocalModelAbortError,
  disposeDirectorLocalModel,
  materializeDirectorLocalModel,
} from "@/lib/directorLocalModelMaterializer";
import type { DirectorLocalResourceStatus } from "@/lib/directorLocalResourceLifecycle";
import {
  getDirectorProjectRegistrySnapshot,
  resolveGroupMemberRefs,
  useDirectorStore,
  DIRECTOR_FRAME_ASPECT_VALUES,
  type DirectorCapture,
  type DirectorCharacterGroup,
  type DirectorMotionPath,
  type DirectorMotionPathAnchor,
  type DirectorMotionPathHandle,
  type DirectorObject,
  type DirectorTransform,
  type DirectorTransformMode,
  type DirectorTuple3,
} from "@/store/directorStore";
import {
  buildDirectorMotionPathPoints,
  buildDirectorMotionPathWorldAnchors,
} from "@/components/director/directorMotionMath";
import {
  DIRECTOR_GRID_SNAP_STEP,
  DIRECTOR_TRANSFORM_SHORTCUT_MODES,
  DIRECTOR_VIEW_PAN_KEYS,
  computeDirectorViewPanDelta,
  getDirectorFrameRect,
  getDirectorViewportAxis,
  getDirectorViewportAxisSnapshot,
  getDirectorViewPresetPose,
  resolveDirectorTransformShortcutMode,
  type DirectorTransformShortcutCategory,
  type DirectorTransformShortcutKey,
  type DirectorViewPreset,
  type DirectorViewportAxisId,
  type DirectorFrameRect,
  type DirectorViewportSnapshot,
} from "@/components/director/directorViewportMath";
import {
  DIRECTOR_MODEL_LIBRARY_CATEGORIES,
  filterDirectorModelLibraryItems,
  getDirectorModelLibraryCategoryLabel,
  getDirectorModelLibraryItems,
  type DirectorModelLibraryCategoryId,
  type DirectorLocalModelLibraryItem,
  type DirectorModelLibraryCardItem,
  type DirectorModelLibraryItem,
} from "@/components/director/directorModelLibrary";
import { readDirectorLocalModelFiles } from "@/components/director/directorLocalModelImport";
import {
  composeDirectorCameraPreviewCamera,
  hasDirectorCameraPreviewCanvas,
  renderDirectorCameraPreview,
} from "@/components/director/directorCameraPreview";
import {
  DirectorVideoExportError,
  recordDirectorCanvasVideo,
  type DirectorVideoExportRequest,
  type DirectorVideoExportResult,
} from "@/components/director/directorVideoExport";
import { DirectorPhoneVcamPanel } from "@/components/director/DirectorPhoneVcamPanel";
import { DirectorMannequin } from "@/components/director/DirectorMannequin";
import { createDirectorCharacterRig } from "@/components/director/directorPose";
import {
  getDirectorGroupAnchorTransform,
} from "@/components/director/directorGroupMath";
import { isMalformedBase64DataImageUrl } from "@/lib/mediaUrl";
import type {
  DirectorCanvasMediaInputV1,
  DirectorPanoramaRuntimeState,
} from "@/lib/directorCanvasMediaIngress";

/* eslint-disable react-hooks/immutability -- Three.js cameras are mutable runtime objects managed by R3F. */
export const DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT: DirectorViewportSnapshot = {
  fov: 45,
  position: [6.2, 4.25, 7.4],
  target: [0, 1, 0],
};

const DIRECTOR_VIEWPORT_GIZMO_AXIS_COLORS: [string, string, string] = [
  "#E56C5B",
  "#6CDB7A",
  "#7AA7FF",
] as const;

const DIRECTOR_VIEWPORT_GIZMO_TARGETS: Array<{
  id: DirectorViewportAxisId;
  label: string;
}> = [
  { id: "x-positive", label: "X 正向" },
  { id: "x-negative", label: "X 反向" },
  { id: "y-positive", label: "Y 正向" },
  { id: "y-negative", label: "Y 反向" },
  { id: "z-positive", label: "Z 正向" },
  { id: "z-negative", label: "Z 反向" },
];

function useDirectorCanvasEventSource() {
  const [fallbackEventSource] = useState<HTMLElement | null>(
    () =>
      typeof document === "undefined" ? null : document.createElement("div"),
  );
  const eventSourceRef = useMemo(
    () => ({ current: fallbackEventSource as HTMLElement }),
    [fallbackEventSource],
  );
  const setEventSource = useCallback(
    (element: HTMLDivElement | null) => {
      eventSourceRef.current = element ?? (fallbackEventSource as HTMLElement);
    },
    [eventSourceRef, fallbackEventSource],
  );

  return { eventSourceRef, setEventSource };
}

function applyDirectorViewportSnapshot(
  perspective: PerspectiveCamera,
  snapshot: DirectorViewportSnapshot,
) {
  perspective.position.set(...snapshot.position);
  perspective.fov = snapshot.fov;
  perspective.lookAt(...snapshot.target);
  perspective.updateProjectionMatrix();
  perspective.updateMatrixWorld();
}

/**
 * Batch 851：导演台的**视图类快捷键**。
 *
 * ★ 键位与语义**逐字取自源站 chunk**（`0fmehki05gkzw.js.js`），不是照抄快捷键面板：
 *
 * ```js
 * else if("t"===n)n0.setEditorCameraPose(iK("top"));
 * else if("y"===n)n0.setEditorCameraPose(iK("front"));
 * else if("h"===n)eJ("director"),n0.setEditorCameraPose(iK("default"));
 * ```
 *
 * ★ WASDQE 是**按住连续平移**，不是「按一下走一步」：
 * keydown 只把键**登记进一个 Set**，真正的位移在 `requestAnimationFrame` 回调里
 * 按「Set 里仍然存在的键」算；**keyup 会把键删掉** ⟹ ⟹ 单击（按下即松开）不会有任何位移。
 * ★ 步长 `1.2 × max(|camera.position − controls.target|, 0.5) × (Shift ? 3 : 1)`，
 * 方向按**相机朝向**（forward / forward×up / up），**同时**平移相机与 orbit 中心。
 */
/**
 * ★ 用 **ref 直取实例**，不走 R3F 的 `state.controls` ⟹ ⟹
 * 1) 免掉「订阅拿到 null」的风险；
 * 2) rAF 回调里读 `ref.current` 永远是最新实例 ⟹ ⟹ 不会因为 re-render 而失效。
 *
 * ★ 实例类型用 `ElementRef<typeof OrbitControls>` 从 drei 取 ⟹ ⟹
 * 不需要直接 import `three-stdlib`（★ 它不是本仓库声明的依赖）。
 */
type DirectorOrbitControlsRef = React.MutableRefObject<
  ElementRef<typeof OrbitControls> | null
>;

const DIRECTOR_VIEW_PAN_KEY_SET: ReadonlySet<string> = new Set(
  DIRECTOR_VIEW_PAN_KEYS,
);

function DirectorViewShortcutController({
  onOrbitTargetChange,
  controlsRef,
}: {
  onOrbitTargetChange: (target: DirectorTuple3) => void;
  controlsRef: DirectorOrbitControlsRef;
}) {
  const camera = useThree((state) => state.camera);
  const invalidate = useThree((state) => state.invalidate);
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  /* ★ Batch 852：变换类快捷键（V／R／F）与网格吸附（X） */
  const setTransformMode = useDirectorStore((state) => state.setTransformMode);
  const updateScene = useDirectorStore((state) => state.updateScene);
  const snapToGrid = useDirectorStore((state) => state.scene.snapToGrid ?? false);
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const finishMotionPathDrawing = useDirectorStore(
    (state) => state.finishMotionPathDrawing,
  );
  /**
   * ★ 源站 `nf.current.selectedCategory` 的 clone 对应物。
   *
   * ★ clone 的对象种类只有 `character`／`prop`／`camera`（`DirectorObjectKind`），
   * **没有** `emptyObject` ⟹ 源站那条「空对象不许旋转／缩放」的守卫在 clone 里
   * 永远不降级；★ 但规则照样实现（见 `resolveDirectorTransformShortcutMode`），
   * 等 clone 长出空对象时直接生效。
   */
  const selectedTransformCategory = useDirectorStore(
    (state): DirectorTransformShortcutCategory => {
      const id = state.selectedObjectId;
      if (!id) return null;
      const object = state.objects.find((item) => item.id === id);
      return (object?.kind as DirectorTransformShortcutCategory) ?? null;
    },
  );
  /** 当前**仍按住**的平移键（源站的 `nK.current`） */
  const pressedKeys = useRef(new Set<string>());
  /** Shift 是否按住（源站的 `nW.current`，按住时步长 ×3） */
  const shiftPressed = useRef(false);
  const frameHandle = useRef<number | null>(null);
  const lastFrameTime = useRef(0);

  /** 当前相机位姿（源站 `iK` 里的 `getEditorCameraPose()`） */
  const readSnapshot = useCallback((): DirectorViewportSnapshot => {
    const perspective = camera as PerspectiveCamera;
    const controls = controlsRef.current;
    const target = controls ? controls.target : new Vector3(0, 1, 0);
    return {
      fov: perspective.fov,
      position: [
        perspective.position.x,
        perspective.position.y,
        perspective.position.z,
      ],
      target: [target.x, target.y, target.z],
    };
  }, [camera, controlsRef]);

  /** 把位姿写回相机**并**同步 orbit 中心（源站的 `setEditorCameraPose`） */
  const applySnapshot = useCallback(
    (snapshot: DirectorViewportSnapshot) => {
      const perspective = camera as PerspectiveCamera;
      perspective.position.set(...snapshot.position);
      perspective.fov = snapshot.fov;
      perspective.lookAt(...snapshot.target);
      perspective.updateProjectionMatrix();
      perspective.updateMatrixWorld();
      const controls = controlsRef.current;
      if (controls) {
        controls.target.set(...snapshot.target);
        controls.update();
        onOrbitTargetChange([
          controls.target.x,
          controls.target.y,
          controls.target.z,
        ]);
      }
      invalidate();
    },
    [camera, controlsRef, invalidate, onOrbitTargetChange],
  );

  /** 源站 `iK(preset)`：**只改方向、不改视距** */
  const applyPreset = useCallback(
    (preset: DirectorViewPreset) => {
      applySnapshot(getDirectorViewPresetPose(preset, readSnapshot()));
    },
    [applySnapshot, readSnapshot],
  );

  /** 源站 `eJ("director")` ＋ `iK("default")` */
  const resetView = useCallback(() => {
    setViewMode("director");
    applySnapshot(DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT);
  }, [applySnapshot, setViewMode]);

  /**
   * ★ Batch 852：源站 `iW(mode)` —— **切变换模式**。
   *
   * ```js
   * let iW=(0,o.useCallback)(e=>{
   *   if(t4&&im(),
   *      "emptyObject"===nf.current.selectedCategory&&"translate"!==e){
   *     tl("translate"),af.setMode("translate");return}
   *   tl(e),af.setMode(e)},[im,t4,af]);
   * ```
   *
   * ★ 两段语义都照抄：
   * ① `t4&&im()` ⟹ **正在编辑运动路径时，先把路径提交掉**再切模式；
   * ② `emptyObject` 守卫 ⟹ 选中空对象时，旋转／缩放降级成移动。
   *
   * ★ clone 的 `tl`/`af` 是**同一个 state**（`transformMode` ＋ drei 的
   * `<TransformControls mode={transformMode}>`）⟹ 一次 `setTransformMode` 即两处生效。
   */
  const applyTransformShortcut = useCallback(
    (requested: DirectorTransformMode) => {
      if (motionPathDraft) finishMotionPathDrawing();
      setTransformMode(
        resolveDirectorTransformShortcutMode(requested, selectedTransformCategory),
      );
    },
    [
      finishMotionPathDrawing,
      motionPathDraft,
      selectedTransformCategory,
      setTransformMode,
    ],
  );

  const stopPanLoop = useCallback(() => {
    if (frameHandle.current !== null) {
      cancelAnimationFrame(frameHandle.current);
      frameHandle.current = null;
    }
    lastFrameTime.current = 0;
  }, []);

  /** 源站 `oi`：一帧的平移 */
  const stepPan = useCallback(() => {
    frameHandle.current = null;
    if (pressedKeys.current.size === 0) {
      lastFrameTime.current = 0;
      return;
    }
    const now = performance.now();
    const deltaSeconds = lastFrameTime.current
      ? (now - lastFrameTime.current) / 1000
      : 0;
    lastFrameTime.current = now;
    const perspective = camera as PerspectiveCamera;
    const forward = new Vector3();
    perspective.getWorldDirection(forward);
    const controls = controlsRef.current;
    const orbitTarget = controls ? controls.target : new Vector3(0, 1, 0);
    const delta = computeDirectorViewPanDelta({
      keys: pressedKeys.current,
      forward: [forward.x, forward.y, forward.z],
      up: [0, 1, 0],
      distance: perspective.position.distanceTo(orbitTarget),
      shift: shiftPressed.current,
      deltaSeconds,
    });
    if (delta[0] !== 0 || delta[1] !== 0 || delta[2] !== 0) {
      const step = new Vector3(delta[0], delta[1], delta[2]);
      perspective.position.add(step);
      // ★ 源站：`r.position.add(d); n.target.add(d); n.update();`
      //   ⟹ ⟹ **相机与 orbit 中心同步平移** ⟹ ⟹ 视距不变 ⟹ ⟹ 只是平移不旋转。
      if (controls) {
        controls.target.add(step);
        controls.update();
      }
      invalidate();
    }
    frameHandle.current = requestAnimationFrame(stepPan);
  }, [camera, controlsRef, invalidate]);

  useEffect(() => {
    /** 源站 `h5`：可编辑元素里**所有**快捷键都不生效 */
    const isEditableTarget = (target: EventTarget | null) => {
      if (!(target instanceof Element)) return false;
      return Boolean(
        target.closest('input, textarea, select, [contenteditable="true"]'),
      );
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.isComposing) return;
      if (isEditableTarget(event.target)) return;
      const key = event.key.toLowerCase();
      /* ★ Batch 852：变换类快捷键。源站 chunk 的四条分支（机器提取见
       *   raw/source-852-contract.json）：
       *   else if("v"===n)iW("translate");
       *   else if("r"===n)iW("rotate");
       *   else if("f"===n)iW("scale");
       *   else if("x"===n)eT(e=>!e);
       *
       * ★ 修饰键条件照抄源站 `hY` 块的 `&&` 链：
       *   `z`/`g`/`c` 要 ⌘、`d` 要 ⌘⇧、`h` 要**无** ⌘⌥；
       *   ★ **`v`/`r`/`f`/`x` 没有任何修饰键限制** ⟹ Shift+V 照样生效。
       *   ★ 唯一例外是 `v`：源站里 ⌘V 走的是**粘贴**分支
       *   （`if("v"===n&&(e.ctrlKey||e.metaKey)){…paste…;return}`）⟹
       *   ⌘V 永远到不了 iW ⟹ clone 同样让开（粘贴归 DirectorDesk 的 ⌘V）。
       */
      if (
        key === "v" ||
        key === "r" ||
        key === "f" ||
        key === "x"
      ) {
        if (key === "v" && (event.ctrlKey || event.metaKey)) return;
        event.preventDefault();
        if (key === "x") {
          // 源站 `eT(e=>!e)` ⟹ **翻转**网格吸附（不是置位）
          updateScene({ snapToGrid: !snapToGrid });
          return;
        }
        const requested = DIRECTOR_TRANSFORM_SHORTCUT_MODES[
          key as DirectorTransformShortcutKey
        ];
        applyTransformShortcut(requested);
        return;
      }
      if (key === "t" || key === "y" || key === "h") {
        // 源站：`("h"!==n||!e.ctrlKey&&!e.metaKey&&!e.altKey)`
        if (event.ctrlKey || event.metaKey || event.altKey) return;
        event.preventDefault();
        if (key === "t") applyPreset("top");
        else if (key === "y") applyPreset("front");
        else resetView();
        return;
      }
      if (!DIRECTOR_VIEW_PAN_KEY_SET.has(key)) return;
      // 源站的裸键组条件：`hX.has(r)&&!(e.ctrlKey||e.metaKey)`
      if (event.ctrlKey || event.metaKey) return;
      event.preventDefault();
      pressedKeys.current.add(key);
      shiftPressed.current = event.shiftKey;
      if (frameHandle.current === null) {
        lastFrameTime.current = 0;
        frameHandle.current = requestAnimationFrame(stepPan);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (!DIRECTOR_VIEW_PAN_KEY_SET.has(key)) return;
      pressedKeys.current.delete(key);
      shiftPressed.current = event.shiftKey;
      if (pressedKeys.current.size === 0) {
        stopPanLoop();
        // ★ 平移期间 orbit 中心只在内存里动 ⟹ ⟹ 收手时同步一次 state，
        //   否则下一次 re-render 会用旧引用把它打回默认。
        const controls = controlsRef.current;
        if (controls) {
          onOrbitTargetChange([
            controls.target.x,
            controls.target.y,
            controls.target.z,
          ]);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown, true);
    window.addEventListener("keyup", handleKeyUp, true);
    return () => {
      window.removeEventListener("keydown", handleKeyDown, true);
      window.removeEventListener("keyup", handleKeyUp, true);
      stopPanLoop();
    };
  }, [
    applyPreset,
    applyTransformShortcut,
    controlsRef,
    onOrbitTargetChange,
    resetView,
    snapToGrid,
    stepPan,
    stopPanLoop,
    updateScene,
  ]);

  return null;
}

function CameraController({
  directorCameraCommand,
  directorOrbitTarget,
  onOrbitTargetChange,
  controlsRef,
}: {
  directorCameraCommand: DirectorViewportSnapshot | null;
  /** ★ Batch 851：orbit 中心的**引用稳定**值 ⟹ ⟹ 否则 drei 会每次 re-render 都把它打回默认 */
  directorOrbitTarget: DirectorTuple3;
  onOrbitTargetChange: (target: DirectorTuple3) => void;
  controlsRef: DirectorOrbitControlsRef;
}) {
  const viewMode = useDirectorStore((state) => state.viewMode);
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const activeCamera = useDirectorStore((state) =>
    state.objects.find((object) => object.id === activeCameraId),
  );
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const camera = useThree((state) => state.camera);
  const invalidate = useThree((state) => state.invalidate);
  const previousMode = useRef(viewMode);
  const lastAppliedDirectorCommand = useRef<DirectorViewportSnapshot | null>(
    null,
  );

  /** ★ 同步 orbit 中心 ⟹ ⟹ 相机看向哪，orbit 中心就在哪（两者必须一致） */
  const syncOrbitTarget = useCallback(
    (target: DirectorTuple3) => {
      const controls = controlsRef.current;
      if (!controls) return;
      controls.target.set(...target);
      controls.update();
      onOrbitTargetChange([target[0], target[1], target[2]]);
    },
    [controlsRef, onOrbitTargetChange],
  );

  useEffect(() => {
    const perspective = camera as PerspectiveCamera;
    if (!perspective.isPerspectiveCamera) return;

    if (viewMode === "camera" && activeCamera?.camera) {
      perspective.position.set(...activeCamera.transform.position);
      perspective.fov = activeCamera.camera.fov;
      if (
        activeCamera.camera.lookAtMode === "rotation" &&
        !activeCamera.camera.followTargetId
      ) {
        perspective.rotation.set(
          MathUtils.degToRad(activeCamera.transform.rotation[0]),
          MathUtils.degToRad(activeCamera.transform.rotation[1]),
          MathUtils.degToRad(activeCamera.transform.rotation[2]),
        );
      } else {
        perspective.lookAt(...activeCamera.camera.target);
      }
      perspective.updateProjectionMatrix();
      perspective.updateMatrixWorld();
      invalidate();
    } else if (viewMode === "director") {
      const hasNewDirectorCommand =
        directorCameraCommand !== null &&
        directorCameraCommand !== lastAppliedDirectorCommand.current;
      if (hasNewDirectorCommand && directorCameraCommand) {
        applyDirectorViewportSnapshot(perspective, directorCameraCommand);
        lastAppliedDirectorCommand.current = directorCameraCommand;
        syncOrbitTarget(directorCameraCommand.target);
        invalidate();
      } else if (previousMode.current === "camera") {
        applyDirectorViewportSnapshot(
          perspective,
          DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT,
        );
        // ★ Batch 851：切回导演视角时 orbit 中心必须跟着复位 ⟹ ⟹
        //   否则「相机看向 [0,1,0]」而「orbit 中心停在别处」，两者会打架。
        syncOrbitTarget(DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT.target);
        invalidate();
      }
    }
    previousMode.current = viewMode;
  }, [
    activeCamera,
    camera,
    directorCameraCommand,
    invalidate,
    onOrbitTargetChange,
    syncOrbitTarget,
    viewMode,
  ]);

  if (viewMode !== "director") return null;

  return (
    <OrbitControls
      ref={controlsRef}
      key={
        directorCameraCommand
          ? directorCameraCommand.position.join(":")
          : "director-default"
      }
      makeDefault
      enabled={!isCapturing && motionPathDraft === null}
      enableDamping
      dampingFactor={0.08}
      minDistance={2.5}
      maxDistance={20}
      maxPolarAngle={Math.PI}
      target={directorOrbitTarget}
    />
  );
}
/* eslint-enable react-hooks/immutability */

function DirectorCameraSnapshotBridge({
  cameraTarget,
  onSnapshot,
  viewMode,
  controlsRef,
}: {
  cameraTarget: DirectorViewportSnapshot["target"];
  onSnapshot: (snapshot: DirectorViewportSnapshot) => void;
  viewMode: "director" | "camera";
  controlsRef: DirectorOrbitControlsRef;
}) {
  const camera = useThree((state) => state.camera);
  const elapsed = useRef(0);
  const lastSnapshot = useRef<DirectorViewportSnapshot | null>(null);

  useFrame((_, delta) => {
    elapsed.current += delta;
    if (elapsed.current < 0.08) return;
    elapsed.current = 0;

    const perspective = camera as PerspectiveCamera;
    if (!perspective.isPerspectiveCamera) return;

    // ★ Batch 851：导演视角下要回读**真实的 orbit 中心** ⟹ ⟹
    //   之前这里硬编码 [0,1,0] ⟹ ⟹ 而 WASDQE 会把 orbit 中心一起平移
    //   ⟹ ⟹ 硬编码会让回读出的位姿与真实相机脱节（gizmo 的轴向移动会算错）。
    //   ★ 默认态下 orbit 中心就是 [0,1,0] ⟹ ⟹ 对既有行为**零影响**。
    const controls = controlsRef.current;
    const target: DirectorViewportSnapshot["target"] =
      viewMode === "director"
        ? controls
          ? [controls.target.x, controls.target.y, controls.target.z]
          : [0, 1, 0]
        : [...cameraTarget];
    const snapshot: DirectorViewportSnapshot = {
      fov: perspective.fov,
      position: [
        perspective.position.x,
        perspective.position.y,
        perspective.position.z,
      ],
      target: [...target],
    };
    const previous = lastSnapshot.current;
    if (
      previous &&
      previous.fov === snapshot.fov &&
      previous.position.every(
        (value, index) => value === snapshot.position[index],
      ) &&
      previous.target.every((value, index) => value === snapshot.target[index])
    ) {
      return;
    }
    lastSnapshot.current = snapshot;
    onSnapshot(snapshot);
  });

  return null;
}

function getDirectorViewportGizmoButtonStyle(
  snapshot: DirectorViewportSnapshot,
  axis: DirectorViewportAxisId,
): CSSProperties {
  const relativePosition = new Vector3(
    snapshot.position[0] - snapshot.target[0],
    snapshot.position[1] - snapshot.target[1],
    snapshot.position[2] - snapshot.target[2],
  );
  if (relativePosition.lengthSq() === 0) relativePosition.set(0, 0, 1);

  const gizmoCamera = new PerspectiveCamera(snapshot.fov, 1, 0.1, 100);
  gizmoCamera.position.copy(relativePosition);
  gizmoCamera.lookAt(0, 0, 0);
  gizmoCamera.updateMatrixWorld();

  const gizmoQuaternion = new Quaternion().setFromRotationMatrix(
    new Matrix4().copy(gizmoCamera.matrix).invert(),
  );
  const projectedDirection = new Vector3(...getDirectorViewportAxis(axis)).applyQuaternion(
    gizmoQuaternion,
  );
  const hitRadius = 7.5;
  const left = Math.min(
    Math.max(40 + projectedDirection.x * 29, hitRadius),
    80 - hitRadius,
  );
  const top = Math.min(
    Math.max(40 - projectedDirection.y * 29, hitRadius),
    80 - hitRadius,
  );
  const depth = Math.round((projectedDirection.z + 1) * 100);

  return {
    left,
    top,
    zIndex: 10 + depth,
  };
}

function DirectorViewportGizmo({
  disabled,
  onAxisSelect,
  onResetView,
  snapshot,
}: {
  disabled: boolean;
  onAxisSelect: (axis: DirectorViewportAxisId) => void;
  onResetView: () => void;
  snapshot: DirectorViewportSnapshot;
}) {
  const { eventSourceRef, setEventSource } = useDirectorCanvasEventSource();

  return (
    <div
      data-director-viewport-gizmo
      aria-label="3D视口原生坐标控件"
      data-director-viewport-gizmo-position={snapshot.position.join(",")}
      data-director-viewport-gizmo-target={snapshot.target.join(",")}
      // ★★★ Batch 864（★ 修 batch 863 带出来的一个**真缺陷**）：
      //   这枚坐标控件原先是 `z-20` ⟹ ⟹ 它**盖住**了取景框右上角那枚
      //   「构图参考线」开关 ⟹ ⟹ **开关点不到**。
      //   ★ 根因：batch 863 给取景框加了**遮罩容器**（源站逐字 `z-10`）
      //   ⟹ ⟹ 那个容器**创建了层叠上下文** ⟹ ⟹ 容器里那枚开关的 `z-20`
      //   被**困在 z-10 里** ⟹ ⟹ 与同为 `z-20` 的这枚控件**平级打架** ⟹ ⟹ 输了。
      //   ★ ★ 修法（**不动源站逐字结构**）：把**这枚 clone 自有控件**降到 `z-10`
      //   ⟹ ⟹ 遮罩容器（DOM 上**更靠后**）盖过它 ⟹ ⟹ 开关恢复可点；
      //   ⟹ ⟹ 而且这枚控件会**跟着视口里除取景框外的一切一起被压暗**，
      //   ⟹ ⟹ 与源站「取景框外整片都压暗＋模糊」的模型**一致**。
      //   ★ 为什么源站没这个问题：源站的取景框是**全屏**容器里算的
      //   （框右边缘 ≤1591），而这枚控件在**视口右上角** ⟹ ⟹ 两者不重叠；
      //   ⟹ ⟹ clone 的视口**更窄**（1358 vs 1920）⟹ ⟹ 才会撞上
      //   ⟹ ⟹ 根因仍是 **D18（布局级）**，本条只是把交互修回来。
      className="absolute right-5 top-5 z-10 h-20 w-20"
    >
      {/* Batch 543: 源站截图 18——gizmo 正下方「重置视角」按钮，恢复导演台默认机位。 */}
      <button
        type="button"
        data-director-reset-view
        onClick={onResetView}
        className="absolute right-0 top-[calc(100%+8px)] whitespace-nowrap rounded border border-white/10 bg-[#262626]/90 px-2 py-1 text-[11px] text-[#c9c9c9] hover:text-white"
      >
        重置视角
      </button>
      <div
        ref={setEventSource}
        className="pointer-events-none absolute inset-0 drop-shadow-[0_2px_5px_rgba(0,0,0,0.48)]"
        data-director-gizmo-webgl-canvas-wrapper
      >
        <Canvas
          eventSource={eventSourceRef}
          frameloop="always"
          camera={{ fov: snapshot.fov, position: [0, 0, 1] }}
          gl={{ alpha: true, antialias: true }}
          onCreated={({ gl }) => {
            gl.domElement.dataset.directorGizmoWebglCanvas = "true";
            gl.domElement.setAttribute("aria-label", "视口方向轴");
          }}
        >
          <DirectorViewportGizmoScene snapshot={snapshot} />
        </Canvas>
      </div>
      <div
        data-director-viewport-gizmo-hit-layer
        aria-label="3D视口坐标切换按钮"
        data-director-viewport-gizmo-disabled={disabled}
        className={cn(
          "absolute inset-0",
          disabled ? "pointer-events-none opacity-60" : "pointer-events-auto",
        )}
      >
        {DIRECTOR_VIEWPORT_GIZMO_TARGETS.map((target) => (
          <button
            key={target.id}
            type="button"
            data-director-viewport-gizmo-button={target.id}
            aria-label={target.label}
            title={target.label}
            disabled={disabled}
            onClick={() => onAxisSelect(target.id)}
            style={getDirectorViewportGizmoButtonStyle(snapshot, target.id)}
            className="absolute h-[15px] w-[15px] -translate-x-1/2 -translate-y-1/2 rounded-full border-0 bg-transparent p-0 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/80"
          />
        ))}
      </div>
    </div>
  );
}

/* eslint-disable react-hooks/immutability -- R3F owns this mutable gizmo camera. */
function DirectorViewportGizmoScene({
  snapshot,
}: {
  snapshot: DirectorViewportSnapshot;
}) {
  const camera = useThree((state) => state.camera);
  const relativePosition = useMemo(
    () =>
      new Vector3(
        snapshot.position[0] - snapshot.target[0],
        snapshot.position[1] - snapshot.target[1],
        snapshot.position[2] - snapshot.target[2],
      ),
    [snapshot.position, snapshot.target],
  );

  useLayoutEffect(() => {
    const perspective = camera as PerspectiveCamera;
    if (!perspective.isPerspectiveCamera) return;
    perspective.position.copy(
      relativePosition.lengthSq() === 0
        ? new Vector3(0, 0, 1)
        : relativePosition,
    );
    perspective.fov = snapshot.fov;
    perspective.lookAt(0, 0, 0);
    perspective.updateProjectionMatrix();
    perspective.updateMatrixWorld();
  }, [camera, relativePosition, snapshot.fov]);

  return (
    <GizmoHelper alignment="center-center" margin={[0, 0]}>
      <GizmoViewport
        axisColors={DIRECTOR_VIEWPORT_GIZMO_AXIS_COLORS}
        disabled
        scale={25}
      />
    </GizmoHelper>
  );
}
/* eslint-enable react-hooks/immutability */

function hasDirectorTransformChanged(
  current: DirectorTransform,
  next: DirectorTransform,
): boolean {
  return (["position", "rotation", "scale"] as const).some((field) =>
    current[field].some(
      (value, axis) => Math.abs(value - next[field][axis]) > 0.0005,
    ),
  );
}

function TablePrimitive({
  color,
  material,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
}) {
  return (
    <group>
      <mesh castShadow receiveShadow position={[0, 0.94, 0]}>
        <boxGeometry args={[2.3, 0.16, 1.25]} />
        <meshStandardMaterial color={color} roughness={0.68} {...material} />
      </mesh>
      {[
        [-0.92, 0.45, -0.42],
        [0.92, 0.45, -0.42],
        [-0.92, 0.45, 0.42],
        [0.92, 0.45, 0.42],
      ].map((position) => (
        <mesh
          key={position.join("-")}
          castShadow
          position={position as [number, number, number]}
        >
          <boxGeometry args={[0.12, 0.9, 0.12]} />
          <meshStandardMaterial color="#34312e" roughness={0.82} {...material} />
        </mesh>
      ))}
    </group>
  );
}

function CameraPrimitive({
  color,
  material,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
}) {
  return (
    <group scale={0.38}>
      <mesh castShadow>
        <boxGeometry args={[0.8, 0.5, 1.15]} />
        <meshStandardMaterial color="#2d3338" metalness={0.32} roughness={0.54} {...material} />
      </mesh>
      <mesh castShadow position={[0, 0, -0.76]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.24, 0.34, 0.48, 20]} />
        <meshStandardMaterial color={color} metalness={0.42} roughness={0.38} {...material} />
      </mesh>
      <mesh castShadow position={[-0.24, 0.42, 0.12]}>
        <cylinderGeometry args={[0.24, 0.24, 0.2, 20]} />
        <meshStandardMaterial color="#22272c" metalness={0.45} roughness={0.44} {...material} />
      </mesh>
      <mesh castShadow position={[0.24, 0.42, 0.12]}>
        <cylinderGeometry args={[0.2, 0.2, 0.2, 20]} />
        <meshStandardMaterial color="#22272c" metalness={0.45} roughness={0.44} {...material} />
      </mesh>
    </group>
  );
}

function LibraryPropPrimitive({
  visual,
  color,
  material,
}: {
  visual: NonNullable<DirectorObject["libraryVisual"]>;
  color: string;
  material: MeshStandardMaterialParameters;
}) {
  if (visual === "bottle") {
    return (
      <group position={[0, 0.45, 0]} scale={0.82}>
        <mesh castShadow>
          <cylinderGeometry args={[0.22, 0.27, 0.78, 20]} />
          <meshStandardMaterial color={color} roughness={0.3} {...material} />
        </mesh>
        <mesh castShadow position={[0, 0.52, 0]}>
          <cylinderGeometry args={[0.13, 0.16, 0.22, 20]} />
          <meshStandardMaterial color={color} roughness={0.28} {...material} />
        </mesh>
        <mesh castShadow position={[0, 0.68, 0]}>
          <cylinderGeometry args={[0.14, 0.14, 0.08, 20]} />
          <meshStandardMaterial color="#27333a" roughness={0.42} {...material} />
        </mesh>
      </group>
    );
  }

  if (visual === "chair") {
    return (
      <group position={[0, 0.02, 0]} scale={0.9}>
        <mesh castShadow position={[0, 0.62, 0]}>
          <boxGeometry args={[0.9, 0.16, 0.82]} />
          <meshStandardMaterial color={color} roughness={0.58} {...material} />
        </mesh>
        <mesh castShadow position={[0, 1.18, -0.3]}>
          <boxGeometry args={[0.9, 1.1, 0.14]} />
          <meshStandardMaterial color={color} roughness={0.58} {...material} />
        </mesh>
        {[
          [-0.34, 0.3, -0.27],
          [0.34, 0.3, -0.27],
          [-0.34, 0.3, 0.27],
          [0.34, 0.3, 0.27],
        ].map((position) => (
          <mesh
            key={position.join("-")}
            castShadow
            position={position as [number, number, number]}
          >
            <boxGeometry args={[0.12, 0.58, 0.12]} />
            <meshStandardMaterial color="#34312e" roughness={0.82} {...material} />
          </mesh>
        ))}
      </group>
    );
  }

  if (visual === "lamp") {
    return (
      <group position={[0, 0.02, 0]} scale={0.88}>
        <mesh castShadow position={[0, 0.08, 0]}>
          <cylinderGeometry args={[0.3, 0.34, 0.16, 24]} />
          <meshStandardMaterial color="#34383d" metalness={0.24} roughness={0.5} {...material} />
        </mesh>
        <mesh castShadow position={[0, 0.62, 0]}>
          <cylinderGeometry args={[0.055, 0.055, 1.05, 16]} />
          <meshStandardMaterial color="#7f858a" metalness={0.32} roughness={0.44} {...material} />
        </mesh>
        <mesh castShadow position={[0, 1.12, 0]}>
          <coneGeometry args={[0.38, 0.36, 24, 1, false]} />
          <meshStandardMaterial color={color} roughness={0.48} {...material} />
        </mesh>
        <pointLight
          color={color}
          intensity={0.7}
          distance={2.2}
          position={[0, 1.02, 0.08]}
        />
      </group>
    );
  }

  if (visual === "plant") {
    return (
      <group position={[0, 0.02, 0]} scale={0.92}>
        <mesh castShadow position={[0, 0.28, 0]}>
          <cylinderGeometry args={[0.3, 0.23, 0.5, 20]} />
          <meshStandardMaterial color="#9b694d" roughness={0.72} {...material} />
        </mesh>
        {[
          [0, 0.92, 0],
          [-0.2, 0.78, 0.03],
          [0.2, 0.78, -0.04],
        ].map((position, index) => (
          <mesh
            key={index}
            castShadow
            position={position as [number, number, number]}
            scale={index === 0 ? [0.28, 0.52, 0.16] : [0.2, 0.38, 0.13]}
          >
            <sphereGeometry args={[0.6, 16, 12]} />
            <meshStandardMaterial color={color} roughness={0.66} {...material} />
          </mesh>
        ))}
      </group>
    );
  }

  return (
    <group position={[0, 0.38, 0]} scale={0.9}>
      <mesh castShadow>
        <boxGeometry args={[0.86, 0.72, 0.72]} />
        <meshStandardMaterial color={color} roughness={0.62} {...material} />
      </mesh>
      <mesh castShadow position={[0, 0.42, 0]}>
        <boxGeometry args={[0.72, 0.08, 0.58]} />
        <meshStandardMaterial color="#d1b184" roughness={0.55} {...material} />
      </mesh>
    </group>
  );
}

const DirectorLocalModelRuntimeContext = createContext<
  Readonly<Record<string, Object3D>>
>({});

function DirectorLocalModelResourceLoader({
  item,
  onModel,
}: {
  item: DirectorLocalModelLibraryItem;
  onModel: (resourceId: string, model: Object3D | null) => void;
}) {
  const resource = useDirectorStore(
    (state) => state.localModelResources[item.id],
  );
  const resourceRef = useRef(resource);
  const projectId = useDirectorStore((state) => state.projectId);
  const sessionId = useDirectorStore((state) => state.sessionId);
  const generation = useDirectorStore((state) => state.generation);
  const startLoad = useDirectorStore(
    (state) => state.startLocalModelResourceLoad,
  );
  const settleLoad = useDirectorStore(
    (state) => state.settleLocalModelResource,
  );
  const releaseResourceLease = useDirectorStore(
    (state) => state.releaseLocalModelResourceLease,
  );
  const cancelLoad = useDirectorStore(
    (state) => state.cancelLocalModelResourceLoad,
  );
  const retryNonce = resource?.retryNonce ?? 0;
  const [model, setModel] = useState<Object3D | null>(null);
  const modelRef = useRef<Object3D | null>(null);
  useEffect(() => {
    resourceRef.current = resource;
    modelRef.current = model;
  }, [model, resource]);

  useEffect(() => {
    const current = resourceRef.current;
    if (!current || current.status === "released") return;
    if (current.status === "ready" && modelRef.current === null) {
      useDirectorStore.getState().retryLocalModelResource(item.id);
      return;
    }
    if (current.status === "loading") return;

    const requestId = startLoad(item.id);
    if (!requestId) return;
    const leaseOwner = useDirectorStore
      .getState()
      .localModelResources[item.id]?.leases.find(
        (lease) => lease.leaseId === requestId,
      )?.owner;
    if (!leaseOwner) {
      cancelLoad(item.id, requestId);
      return;
    }
    const controller = new AbortController();
    let active = true;

    void materializeDirectorLocalModel(item, controller.signal)
      .then((nextModel) => {
        if (!active) {
          disposeDirectorLocalModel(nextModel);
          return;
        }
        const accepted = settleLoad({
          resourceId: item.id,
          requestId,
          status: "ready",
        });
        if (!accepted) {
          releaseResourceLease(item.id, requestId, leaseOwner);
          disposeDirectorLocalModel(nextModel);
          return;
        }
        setModel(nextModel);
        onModel(item.id, nextModel);
      })
      .catch((error: unknown) => {
        if (!active) return;
        const canceled = error instanceof DirectorLocalModelAbortError;
        settleLoad({
          resourceId: item.id,
          requestId,
          status: canceled ? "canceled" : "failed",
          error: canceled ? "ABORTED" : "PARSE_FAILED",
          errorMessage:
            error instanceof Error ? error.message : "模型解析失败",
        });
        releaseResourceLease(item.id, requestId, leaseOwner);
      });

    return () => {
      active = false;
      controller.abort();
      cancelLoad(item.id, requestId, leaseOwner);
      releaseResourceLease(item.id, requestId, leaseOwner);
      if (modelRef.current) {
        onModel(item.id, null);
        disposeDirectorLocalModel(modelRef.current);
        setModel(null);
      }
    };
  }, [
    cancelLoad,
    generation,
    item,
    onModel,
    projectId,
    retryNonce,
    releaseResourceLease,
    sessionId,
    settleLoad,
    startLoad,
  ]);

  return null;
}

function DirectorLocalModelRuntime({
  children,
}: {
  children: React.ReactNode;
}) {
  const objects = useDirectorStore((state) => state.objects);
  const localModelLibrary = useDirectorStore(
    (state) => state.localModelLibrary,
  );
  const [models, setModels] = useState<Record<string, Object3D>>({});
  const localItems = useMemo(() => {
    const ids = new Set(
      objects
        .filter(
          (object) =>
            object.primitive === "library" &&
            object.librarySource === "local" &&
            object.libraryAssetId,
        )
        .map((object) => object.libraryAssetId as string),
    );
    return localModelLibrary.filter((item) => ids.has(item.id));
  }, [localModelLibrary, objects]);
  const onModel = useCallback(
    (resourceId: string, model: Object3D | null) => {
      setModels((current) => {
        if (model) return { ...current, [resourceId]: model };
        if (!(resourceId in current)) return current;
        const next = { ...current };
        delete next[resourceId];
        return next;
      });
    },
    [],
  );

  return (
    <DirectorLocalModelRuntimeContext.Provider value={models}>
      {localItems.map((item) => (
        <DirectorLocalModelResourceLoader
          key={item.id}
          item={item}
          onModel={onModel}
        />
      ))}
      {children}
    </DirectorLocalModelRuntimeContext.Provider>
  );
}

function SceneObject({ object }: { object: DirectorObject }) {
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const groups = useDirectorStore((state) => state.groups);
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const viewMode = useDirectorStore((state) => state.viewMode);
  const transformMode = useDirectorStore((state) => state.transformMode);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const selectObject = useDirectorStore((state) => state.selectObject);
  const updateObjectTransform = useDirectorStore(
    (state) => state.updateObjectTransform,
  );
  const recordObjectKeyframe = useDirectorStore(
    (state) => state.recordObjectKeyframe,
  );
  // Batch 549: 源站「角色标签」开关控制角色头顶名称浮标（截图 18 角色A）。
  const showCharacterLabels = useDirectorStore(
    (state) => state.scene.showCharacterLabels ?? true,
  );
  const snapToGrid = useDirectorStore((state) => state.scene.snapToGrid ?? false);
  // Batch 558: 源站「高斯地面吸附」开——角色渲染位置 Y 不低于地面（与
  // authored 层夹紧合同一致，修复 runtime 投影覆盖导致的视觉偏差）。
  const gaussianGroundSnap = useDirectorStore(
    (state) => state.scene.gaussianGroundSnap ?? true,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const selectedMotionPathAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const localModels = useContext(DirectorLocalModelRuntimeContext);
  const localModel =
    object.librarySource === "local" && object.libraryAssetId
      ? localModels[object.libraryAssetId] ?? null
      : null;
  const localModelInstance = useMemo(
    () => localModel?.clone(true) ?? null,
    [localModel],
  );
  const groupRef = useRef<Group>(null);
  const [transformTarget, setTransformTarget] = useState<Group | null>(null);
  const transformEngagedRef = useRef(false);
  const transformActiveRef = useRef(false);
  const selected = selectedObjectId === object.id && selectedGroupId === null;
  const owningGroup = groups.find((group) =>
    group.characterIds.includes(object.id),
  );

  const hideCameraRig =
    object.kind === "camera" &&
    (isCapturing || (viewMode === "camera" && object.id === activeCameraId));

  const material: MeshStandardMaterialParameters = selected
    ? {
        emissive: "#075e71",
        emissiveIntensity: 0.36,
      }
    : {};
  const rotation = object.transform.rotation.map((value) =>
    MathUtils.degToRad(value),
  ) as [number, number, number];
  const assignGroupRef = useCallback((group: Group | null) => {
    groupRef.current = group;
    setTransformTarget(group);
  }, []);

  const restoreTransform = useCallback(() => {
    const group = groupRef.current;
    if (!group) return;
    group.position.set(...object.transform.position);
    group.rotation.set(...rotation);
    group.scale.set(...object.transform.scale);
    group.updateMatrixWorld();
  }, [object.transform.position, object.transform.scale, rotation]);

  const commitTransform = useCallback(() => {
    if (!transformEngagedRef.current) return;
    transformEngagedRef.current = false;
    if (!transformActiveRef.current) {
      restoreTransform();
      return;
    }
    transformActiveRef.current = false;
    const group = groupRef.current;
    if (!group) {
      cancelDirectorGesture();
      return;
    }
    const nextTransform: DirectorTransform = {
      position: [group.position.x, group.position.y, group.position.z],
      rotation: [
        MathUtils.radToDeg(group.rotation.x),
        MathUtils.radToDeg(group.rotation.y),
        MathUtils.radToDeg(group.rotation.z),
      ],
      scale: [group.scale.x, group.scale.y, group.scale.z],
    };
    if (!hasDirectorTransformChanged(object.transform, nextTransform)) {
      restoreTransform();
      commitDirectorGesture();
      return;
    }
    (["position", "rotation", "scale"] as const).forEach((field) => {
      nextTransform[field].forEach((value, axis) => {
        updateObjectTransform(
          object.id,
          field,
          axis as 0 | 1 | 2,
          Number(value.toFixed(3)),
        );
      });
    });
    recordObjectKeyframe(object.id);
    commitDirectorGesture();
  }, [
    cancelDirectorGesture,
    commitDirectorGesture,
    object.id,
    object.transform,
    recordObjectKeyframe,
    restoreTransform,
    updateObjectTransform,
  ]);

  const cancelTransform = useCallback(() => {
    if (!transformEngagedRef.current) return;
    transformEngagedRef.current = false;
    const wasActive = transformActiveRef.current;
    transformActiveRef.current = false;
    restoreTransform();
    if (wasActive) cancelDirectorGesture();
  }, [cancelDirectorGesture, restoreTransform]);

  useEffect(() => {
    const handlePointerUp = () => commitTransform();
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", cancelTransform);
    return () => {
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", cancelTransform);
    };
  }, [cancelTransform, commitTransform]);

  if (!object.visible || hideCameraRig) return null;

  const renderPosition =
    gaussianGroundSnap && object.kind === "character"
      ? ([object.transform.position[0], Math.max(object.transform.position[1], 0), object.transform.position[2]] as typeof object.transform.position)
      : object.transform.position;
  const content = (
    <group
      ref={assignGroupRef}
      position={renderPosition}
      rotation={rotation}
      scale={object.transform.scale}
      onClick={(event: ThreeEvent<MouseEvent>) => {
        event.stopPropagation();
        if (motionPathDraft || selectedMotionPathAnchorId) return;
        if (owningGroup) {
          useDirectorStore.getState().selectGroup(owningGroup.id);
          return;
        }
        selectObject(object.id, "viewport");
      }}
    >
      {object.primitive === "character" ? (
        <>
          <DirectorMannequin
            color={object.color}
            material={material}
            rig={object.characterRig ?? createDirectorCharacterRig()}
          />
          {showCharacterLabels ? (
            <Html
              position={[0, 2.35, 0]}
              center
              distanceFactor={8}
              style={{ pointerEvents: "none" }}
              zIndexRange={[40, 0]}
            >
              <span
                data-director-character-label={object.name}
                className="whitespace-nowrap rounded bg-black/60 px-1.5 py-0.5 text-sm font-medium text-white"
              >
                {object.name}
              </span>
            </Html>
          ) : null}
        </>
      ) : null}
      {object.primitive === "table" ? (
        <TablePrimitive color={object.color} material={material} />
      ) : null}
      {object.primitive === "mug" ? (
        <mesh castShadow>
          <cylinderGeometry args={[0.13, 0.11, 0.24, 24]} />
          <meshStandardMaterial color={object.color} roughness={0.38} {...material} />
        </mesh>
      ) : null}
      {object.primitive === "wall" ? (
        <group>
          <mesh receiveShadow>
            <boxGeometry args={[7, 3, 0.18]} />
            <meshStandardMaterial color={object.color} roughness={0.92} {...material} />
          </mesh>
          <mesh position={[-2.15, 0.25, 0.12]}>
            <boxGeometry args={[1.5, 1.6, 0.08]} />
            <meshStandardMaterial color="#b98254" emissive="#5a321b" emissiveIntensity={0.16} />
          </mesh>
          <mesh position={[1.85, 0.45, 0.12]}>
            <boxGeometry args={[1.8, 1.25, 0.08]} />
            <meshStandardMaterial color="#667988" emissive="#243c4c" emissiveIntensity={0.2} />
          </mesh>
        </group>
      ) : null}
      {object.primitive === "camera" ? (
        <CameraPrimitive color={object.color} material={material} />
      ) : null}
      {object.primitive === "library" && localModelInstance ? (
        <primitive object={localModelInstance} />
      ) : null}
      {object.primitive === "library" &&
      object.libraryVisual &&
      !localModelInstance ? (
        <LibraryPropPrimitive
          color={object.color}
          material={material}
          visual={object.libraryVisual}
        />
      ) : null}
    </group>
  );

  if (
    !selected ||
    object.locked ||
    isCapturing ||
    selectedMotionPathAnchorId !== null ||
    motionPathDraft !== null
  ) {
    return content;
  }

  return (
    <>
      {transformTarget ? (
        <TransformControls
          object={transformTarget}
          mode={transformMode}
          translationSnap={snapToGrid ? DIRECTOR_GRID_SNAP_STEP : null}
          size={0.72}
          onMouseDown={() => {
            transformEngagedRef.current = true;
            const result = beginDirectorGesture({
              commandKind: "object-transform",
              targetId: object.id,
              fieldScope: transformMode,
            });
            transformActiveRef.current = result.disposition === "COMMITTED";
          }}
          onMouseUp={commitTransform}
          onPointerCancel={cancelTransform}
          onLostPointerCapture={cancelTransform}
        />
      ) : null}
      {content}
    </>
  );
}

/**
 * ★★★ Batch 856：组的**画布锚点**（**没有 gizmo**）。
 *
 * ★ 源站逐字：建组 `a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}`
 *   ⟹ ⟹ 组**没有 transform 字段**（机器提取见
 *   `docs/research/liblib-canvas-batch856-2026-10-01/raw/source-856-contract.json`）。
 * ★ 源站实测（`raw/source-856-groupinspector.json`）：
 *   选中**角色** ⟹ 检查器 **13 个字段**；选中**组** ⟹ **1 个字段**（只有「名称」）。
 * ★ 源站实测（`raw/source-856-groupgizmo.json`）：
 *   选中组后**画布上没有任何 gizmo** ⟹ ⟹ 像素差只落在左侧树面板；
 *   阳性对照＝选中角色时画布右下角出现**红色箭头**（包围盒一直延伸到 x=896），
 *   而选中组时包围盒**只到 x=271**（＝树面板右缘）。
 * ★ 源站里 gizmo 只注册**具体对象**（character／prop／camera／emptyObject），
 *   **没有「组」这一类** ⟹ ⟹ 组**不能**在画布上被拖动。
 * ⟹ ⟹ **组只能通过「组轨道」（时间轴）移动**。
 *
 * ★ 所以本组件现在**只保留一个空的锚点 group**（保留
 *   `data-director-group-rig` 这个语义锚点 ＋ 给将来「组空间」留位置），
 *   **TransformControls（gizmo）已移除** ⟹ ⟹ 之前那条
 *   `updateGroupTransform` 的「旋转增量 ＋ 缩放比」交互路径
 *   在源站**根本不存在**。
 */
function DirectorGroupTransformRig({
  group,
}: {
  group: DirectorCharacterGroup;
}) {
  const objects = useDirectorStore((state) => state.objects);
  const anchor = getDirectorGroupAnchorTransform(objects, group);
  if (!anchor) return null;
  return (
    <group data-director-group-rig={group.id}>
      <group
        position={anchor.position}
        rotation={anchor.rotation.map((value) =>
          MathUtils.degToRad(value),
        ) as [number, number, number]}
        scale={anchor.scale}
      />
    </group>
  );
}

function addTuple(
  left: DirectorTuple3,
  right: DirectorTuple3,
): DirectorTuple3 {
  return [
    left[0] + right[0],
    left[1] + right[1],
    left[2] + right[2],
  ];
}

function PathControlPoint({
  path,
  anchor,
  worldAnchor,
  handle,
}: {
  path: DirectorMotionPath;
  anchor: DirectorMotionPathAnchor;
  worldAnchor: DirectorMotionPathAnchor;
  handle: DirectorMotionPathHandle | null;
}) {
  const snapToGrid = useDirectorStore(
    (state) => state.scene.snapToGrid ?? false,
  );
  const selectedAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const selectedHandle = useDirectorStore(
    (state) => state.timeline.selectedMotionPathHandle,
  );
  const objectLocked = useDirectorStore((state) =>
    state.objects.some(
      (object) => object.id === path.objectId && object.locked,
    ),
  );
  const selectMotionPathAnchor = useDirectorStore(
    (state) => state.selectMotionPathAnchor,
  );
  const updateMotionPathAnchorWorldPosition = useDirectorStore(
    (state) => state.updateMotionPathAnchorWorldPosition,
  );
  const updateMotionPathAnchorWorldHandle = useDirectorStore(
    (state) => state.updateMotionPathAnchorWorldHandle,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const groupRef = useRef<Group>(null);
  const [transformTarget, setTransformTarget] = useState<Group | null>(null);
  const transformEngagedRef = useRef(false);
  const transformActiveRef = useRef(false);
  const selected =
    selectedAnchorId === anchor.id && selectedHandle === handle;
  const relative =
    handle === "in"
      ? worldAnchor.handleIn
      : handle === "out"
        ? worldAnchor.handleOut
        : null;
  const position = relative
    ? addTuple(worldAnchor.position, relative)
    : worldAnchor.position;
  const assignGroupRef = useCallback((group: Group | null) => {
    groupRef.current = group;
    setTransformTarget(group);
  }, []);

  const restoreTransform = useCallback(() => {
    const group = groupRef.current;
    if (!group) return;
    group.position.set(...position);
    group.updateMatrixWorld();
  }, [position]);

  const commit = useCallback(() => {
    if (!transformEngagedRef.current) return;
    transformEngagedRef.current = false;
    if (!transformActiveRef.current) {
      restoreTransform();
      return;
    }
    transformActiveRef.current = false;
    const group = groupRef.current;
    if (!group) {
      cancelDirectorGesture();
      return;
    }
    const worldPosition: DirectorTuple3 = [
      Number(group.position.x.toFixed(3)),
      Number(group.position.y.toFixed(3)),
      Number(group.position.z.toFixed(3)),
    ];
    if (handle) {
      updateMotionPathAnchorWorldHandle(
        path.id,
        anchor.id,
        handle,
        worldPosition,
      );
      commitDirectorGesture();
      return;
    }
    updateMotionPathAnchorWorldPosition(
      path.id,
      anchor.id,
      worldPosition,
    );
    commitDirectorGesture();
  }, [
    anchor.id,
    cancelDirectorGesture,
    commitDirectorGesture,
    handle,
    path.id,
    restoreTransform,
    updateMotionPathAnchorWorldHandle,
    updateMotionPathAnchorWorldPosition,
  ]);

  const cancelTransform = useCallback(() => {
    if (!transformEngagedRef.current) return;
    transformEngagedRef.current = false;
    const wasActive = transformActiveRef.current;
    transformActiveRef.current = false;
    restoreTransform();
    if (wasActive) cancelDirectorGesture();
  }, [cancelDirectorGesture, restoreTransform]);

  useEffect(() => {
    const handlePointerUp = () => commit();
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", cancelTransform);
    return () => {
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", cancelTransform);
    };
  }, [cancelTransform, commit]);

  const content = (
    <group
      ref={assignGroupRef}
      position={position}
      onClick={(event: ThreeEvent<MouseEvent>) => {
        event.stopPropagation();
        selectMotionPathAnchor(path.id, anchor.id, handle);
      }}
    >
      <mesh renderOrder={5}>
        {handle ? (
          <boxGeometry args={[0.095, 0.095, 0.095]} />
        ) : (
          <sphereGeometry args={[selected ? 0.09 : 0.068, 14, 10]} />
        )}
        <meshBasicMaterial
          color={
            selected
              ? "#ffffff"
              : handle
                ? "#f6b85f"
                : "#09caf5"
          }
          depthTest={false}
        />
      </mesh>
    </group>
  );

  if (!selected || objectLocked) return content;
  return (
    <>
      {transformTarget ? (
        <TransformControls
          object={transformTarget}
          mode="translate"
          translationSnap={snapToGrid ? DIRECTOR_GRID_SNAP_STEP : null}
          size={0.62}
          onMouseDown={() => {
            transformEngagedRef.current = true;
            const result = beginDirectorGesture({
              commandKind: handle
                ? "path-anchor-handle-transform"
                : "path-anchor-transform",
              targetId: anchor.id,
              fieldScope: handle ?? "position",
            });
            transformActiveRef.current = result.disposition === "COMMITTED";
          }}
          onMouseUp={commit}
          onPointerCancel={cancelTransform}
        />
      ) : null}
      {content}
    </>
  );
}

function DirectorMotionPathControls({
  path,
}: {
  path: DirectorMotionPath;
}) {
  const selectedAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const worldAnchors = buildDirectorMotionPathWorldAnchors(
    path.anchors,
    path.pivot,
    path.transform,
  );

  return (
    <>
      {path.anchors.map((anchor, index) => {
        const worldAnchor = worldAnchors[index];
        const anchorSelected = anchor.id === selectedAnchorId;
        const showHandles =
          anchorSelected && anchor.type !== "vertex";
        const handleIn = addTuple(
          worldAnchor.position,
          worldAnchor.handleIn,
        );
        const handleOut = addTuple(
          worldAnchor.position,
          worldAnchor.handleOut,
        );
        return (
          <group key={anchor.id}>
            {showHandles ? (
              <>
                <Line
                  points={[handleIn, worldAnchor.position, handleOut]}
                  color="#b88a51"
                  lineWidth={1}
                  transparent
                  opacity={0.85}
                  depthTest={false}
                />
                <PathControlPoint
                  path={path}
                  anchor={anchor}
                  worldAnchor={worldAnchor}
                  handle="in"
                />
                <PathControlPoint
                  path={path}
                  anchor={anchor}
                  worldAnchor={worldAnchor}
                  handle="out"
                />
              </>
            ) : null}
            <PathControlPoint
              path={path}
              anchor={anchor}
              worldAnchor={worldAnchor}
              handle={null}
            />
          </group>
        );
      })}
    </>
  );
}

function DirectorMotionPaths() {
  const timeline = useDirectorStore((state) => state.timeline);
  const viewMode = useDirectorStore((state) => state.viewMode);
  const isCapturing = useDirectorStore((state) => state.isCapturing);

  if (viewMode !== "director" || isCapturing) return null;

  return (
    <group>
      {timeline.motionPaths
        .filter((path) => path.enabled)
        .map((path) => {
          const selected = path.id === timeline.selectedMotionPathId;
          const points = path.closed
            ? [...path.points, path.points[0]]
            : path.points;
          return (
            <group key={path.id}>
              <Line
                points={points}
                color={selected ? "#09caf5" : "#6c7d86"}
                lineWidth={selected ? 2.2 : 1.2}
                transparent
                opacity={selected ? 0.95 : 0.52}
                depthTest={false}
              />
              {selected ? <DirectorMotionPathControls path={path} /> : null}
            </group>
          );
        })}
    </group>
  );
}

function DirectorMotionPathDrawingSurface() {
  const draft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const appendMotionPathDraftAnchor = useDirectorStore(
    (state) => state.appendMotionPathDraftAnchor,
  );
  const updateMotionPathDraftLastHandle = useDirectorStore(
    (state) => state.updateMotionPathDraftLastHandle,
  );
  const cancelMotionPathDrawing = useDirectorStore(
    (state) => state.cancelMotionPathDrawing,
  );
  const finishMotionPathDrawing = useDirectorStore(
    (state) => state.finishMotionPathDrawing,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const pointerActive = useRef(false);

  useEffect(() => {
    const handlePointerCancel = () => {
      if (!pointerActive.current) return;
      pointerActive.current = false;
      cancelMotionPathDrawing();
      cancelDirectorGesture();
    };
    window.addEventListener("pointercancel", handlePointerCancel);
    return () =>
      window.removeEventListener("pointercancel", handlePointerCancel);
  }, [cancelDirectorGesture, cancelMotionPathDrawing]);

  if (!draft) return null;
  const draftPoints = buildDirectorMotionPathPoints(draft.anchors, false);
  const pointFromEvent = (
    event: ThreeEvent<PointerEvent>,
  ): DirectorTuple3 => [
    Number(event.point.x.toFixed(3)),
    draft.planeY,
    Number(event.point.z.toFixed(3)),
  ];

  return (
    <group>
      {draftPoints.length >= 2 ? (
        <Line
          points={draftPoints}
          color="#f6b85f"
          lineWidth={2}
          transparent
          opacity={0.96}
          depthTest={false}
        />
      ) : null}
      {draft.anchors.map((anchor) => (
        <mesh
          key={anchor.id}
          position={anchor.position}
          renderOrder={6}
        >
          <sphereGeometry args={[0.06, 12, 8]} />
          <meshBasicMaterial color="#f6b85f" depthTest={false} />
        </mesh>
      ))}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, draft.planeY + 0.018, 0]}
        onPointerDown={(event) => {
          if (event.nativeEvent.button !== 0) return;
          event.stopPropagation();
          pointerActive.current = true;
          const target = event.nativeEvent.currentTarget;
          if (target instanceof Element) {
            target.setPointerCapture(event.pointerId);
          }
          appendMotionPathDraftAnchor(pointFromEvent(event));
        }}
        onPointerMove={(event) => {
          if (!pointerActive.current) return;
          event.stopPropagation();
          if (draft.tool === "pencil") {
            appendMotionPathDraftAnchor(pointFromEvent(event));
          } else {
            updateMotionPathDraftLastHandle(pointFromEvent(event));
          }
        }}
        onPointerUp={(event) => {
          if (!pointerActive.current) return;
          event.stopPropagation();
          pointerActive.current = false;
          const target = event.nativeEvent.currentTarget;
          if (
            target instanceof Element &&
            target.hasPointerCapture(event.pointerId)
          ) {
            target.releasePointerCapture(event.pointerId);
          }
          if (draft.tool === "pencil") {
            finishMotionPathDrawing();
            commitDirectorGesture();
          }
        }}
        onPointerCancel={(event) => {
          if (!pointerActive.current) return;
          event.stopPropagation();
          pointerActive.current = false;
          const target = event.nativeEvent.currentTarget;
          if (
            target instanceof Element &&
            target.hasPointerCapture(event.pointerId)
          ) {
            target.releasePointerCapture(event.pointerId);
          }
          cancelMotionPathDrawing();
          cancelDirectorGesture();
        }}
      >
        <planeGeometry args={[40, 40]} />
        <meshBasicMaterial
          transparent
          opacity={0}
          depthWrite={false}
          side={DoubleSide}
        />
      </mesh>
    </group>
  );
}

function DirectorPanoramaRuntime({
  input,
  onStatusChange,
  panoramaRotation,
  panoramaSphereRadius,
}: {
  input: DirectorCanvasMediaInputV1;
  onStatusChange: (status: Exclude<DirectorPanoramaRuntimeState, "empty">) => void;
  panoramaRotation: number;
  panoramaSphereRadius: number;
}) {
  const [texture, setTexture] = useState<Texture | null>(null);
  const textureRef = useRef<Texture | null>(null);

  useEffect(() => {
    let active = true;
    if (isMalformedBase64DataImageUrl(input.imageUrl)) {
      onStatusChange("error");
      return () => {
        active = false;
      };
    }

    const loader = new TextureLoader();
    onStatusChange("loading");
    const loadedTexture = loader.load(
      input.imageUrl,
      (nextTexture) => {
        if (!active) {
          nextTexture.dispose();
          return;
        }
        textureRef.current = nextTexture;
        setTexture(nextTexture);
        onStatusChange("ready");
      },
      undefined,
      () => {
        if (active) onStatusChange("error");
      },
    );

    return () => {
      active = false;
      loadedTexture.dispose();
      if (textureRef.current === loadedTexture) {
        textureRef.current = null;
        setTexture(null);
      }
    };
  }, [input.imageUrl, onStatusChange]);

  if (!texture) return null;

  // Batch 555: 源站「全景球 水平旋转/球形半径」（截图 45/48）接入渲染；
  // 半径默认 30 保持 clone 现渲染（源站示值 60，SOURCE_DIFF）。
  const rotationRadians = panoramaRotation * (Math.PI / 180);
  const sphereRadius = panoramaSphereRadius;
  return (
    <mesh
      scale={[-1, 1, 1]}
      rotation={[0, rotationRadians, 0]}
      frustumCulled={false}
      raycast={() => undefined}
    >
      <sphereGeometry args={[sphereRadius, 64, 32]} />
      <meshBasicMaterial
        map={texture}
        side={BackSide}
        depthWrite={false}
        toneMapped={false}
      />
    </mesh>
  );
}

function DirectorScene({
  panoramaInput,
  onPanoramaStatusChange,
}: {
  panoramaInput: DirectorCanvasMediaInputV1 | null;
  onPanoramaStatusChange: (
    status: Exclude<DirectorPanoramaRuntimeState, "empty">,
  ) => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const groups = useDirectorStore((state) => state.groups);

  return (
    <>
      {/* Batch 549: 源站「天空颜色」为全景缺席时的天幕底色；全景存在时仍以
          场景背景色兜底（全景球覆盖其上）。 */}
      <color
        attach="background"
        args={[
          panoramaInput ? scene.backgroundColor : (scene.skyColor ?? scene.backgroundColor),
        ]}
      />
      <fog attach="fog" args={[scene.backgroundColor, 9, 24]} />
      {panoramaInput ? (
        <DirectorPanoramaRuntime
          input={panoramaInput}
          onStatusChange={onPanoramaStatusChange}
          panoramaRotation={scene.panoramaRotation ?? 0}
          panoramaSphereRadius={scene.panoramaSphereRadius ?? 30}
        />
      ) : null}
      <ambientLight intensity={1.15} />
      <directionalLight
        castShadow
        position={[4.5, 8, 4]}
        intensity={2.3}
        color="#ffe3c2"
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-5, 3, 2]} intensity={1.2} color="#95c8ff" />
      {scene.showGround ? (
        <mesh
          receiveShadow
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, (scene.groundHeight ?? 0) - 0.01, 0]}
        >
          <planeGeometry args={[32, 32]} />
          <meshStandardMaterial
            color={scene.groundColor}
            roughness={0.94}
            transparent
            opacity={scene.groundOpacity ?? 0.4}
          />
        </mesh>
      ) : null}
      {scene.showGrid && !isCapturing ? (
        <gridHelper args={[24, 24, "#59636c", "#3d454c"]} position={[0, 0.006, 0]} />
      ) : null}
      {/* Batch 559: 源站「场景变换」——缩放/平移/旋转作用于场景内容
          （对象与分组；地面/网格/灯光为辅助不参与）。 */}
      <group
        scale={scene.sceneScale ?? 1}
        position={[...(scene.sceneTranslate ?? [0, 0, 0])]}
        rotation={[
          (scene.sceneRotate?.[0] ?? 0) * (Math.PI / 180),
          (scene.sceneRotate?.[1] ?? 0) * (Math.PI / 180),
          (scene.sceneRotate?.[2] ?? 0) * (Math.PI / 180),
        ]}
      >
      <DirectorLocalModelRuntime>
        {objects.map((object) => (
          <SceneObject key={object.id} object={object} />
        ))}
        {groups.map((group) => (
          <DirectorGroupTransformRig key={group.id} group={group} />
        ))}
      </DirectorLocalModelRuntime>
      </group>
      <DirectorMotionPaths />
      <DirectorMotionPathDrawingSurface />
    </>
  );
}

/**
 * Batch 611：把当前 scene 按「属性面板选中的那台机位」离屏渲进
 * WebGLRenderTarget，再回读进面板里的 2D canvas。复用同一个 WebGL
 * 上下文，不新增 context，主画布与导出路径不受影响。
 *
 * readRenderTargetPixels 是同步回读（会 stall 管线），所以只在**签名变化**
 * 时才渲：签名含机位变换/FOV、场景里所有对象与分组的变换、以及播放头时间。
 * 播放时播放头每帧变，于是退化成每帧一次小尺寸（240×135）回读；静止时
 * 完全不触发。
 */
function CameraPreviewRenderer() {
  const gl = useThree((state) => state.gl);
  const scene = useThree((state) => state.scene);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectIds[0] ?? null);
  const previewCamera = useMemo(() => new PerspectiveCamera(), []);
  const lastSignature = useRef<string | null>(null);
  const frame = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      if (cancelled) return;
      frame.current = window.requestAnimationFrame(tick);
      if (!hasDirectorCameraPreviewCanvas()) return;
      const state = useDirectorStore.getState();
      const selected = state.objects.find(
        (object) => object.id === selectedObjectId && object.camera,
      );
      if (!selected?.camera) {
        lastSignature.current = null;
        return;
      }
      const signature = [
        selected.id,
        selected.transform.position.join(","),
        selected.transform.rotation.join(","),
        selected.camera.fov,
        selected.camera.target.join(","),
        selected.camera.lookAtMode,
        selected.camera.followTargetId ?? "",
        state.timeline.currentTime,
        state.timeline.isPlaying ? "1" : "0",
        state.objects
          .map((object) =>
            [
              object.id,
              object.visible === false ? "h" : "v",
              object.transform.position.join(","),
              object.transform.rotation.join(","),
            ].join(":"),
          )
          .join("|"),
      ].join("#");
      if (signature === lastSignature.current) return;
      lastSignature.current = signature;
      composeDirectorCameraPreviewCamera(previewCamera, {
        position: selected.transform.position,
        fov: selected.camera.fov,
        target: selected.camera.target,
        useRotation:
          selected.camera.lookAtMode === "rotation" &&
          !selected.camera.followTargetId,
        rotation: selected.transform.rotation,
      });
      renderDirectorCameraPreview(gl, scene, previewCamera);
    };
    frame.current = window.requestAnimationFrame(tick);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame.current);
    };
  }, [gl, previewCamera, scene, selectedObjectId]);

  return null;
}

function CaptureController({
  request,
  frameRect,
  onCaptured,
}: {
  request: DirectorAsyncOperationDescriptorV1 | null;
  frameRect: DirectorFrameRect | null;
  onCaptured: (capture: DirectorCapture) => void;
}) {
  const aspectRatio = useDirectorStore((state) => state.aspectRatio);
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const activeCamera = useDirectorStore((state) =>
    state.objects.find((object) => object.id === activeCameraId),
  );
  const setCapturing = useDirectorStore((state) => state.setCapturing);
  const gl = useThree((state) => state.gl);
  const scene = useThree((state) => state.scene);
  const camera = useThree((state) => state.camera);
  const handledRequest = useRef<string | null>(null);

  useEffect(() => {
    if (!request || request.operationId === handledRequest.current) return;
    handledRequest.current = request.operationId;
    let firstFrame = 0;
    let secondFrame = 0;

    firstFrame = window.requestAnimationFrame(() => {
      secondFrame = window.requestAnimationFrame(() => {
        try {
          gl.render(scene, camera);
          const source = gl.domElement;
          const cssWidth = source.clientWidth || 1;
          const cssHeight = source.clientHeight || 1;
          const rect = frameRect ?? {
            left: 0,
            top: 0,
            width: cssWidth,
            height: cssHeight,
          };
          const scaleX = source.width / cssWidth;
          const scaleY = source.height / cssHeight;
          const output = document.createElement("canvas");
          output.width = Math.max(1, Math.round(rect.width * scaleX));
          output.height = Math.max(1, Math.round(rect.height * scaleY));
          const canvasContext = output.getContext("2d");
          if (!canvasContext)
            throw new Error("Director capture canvas is unavailable");
          canvasContext.drawImage(
            source,
            Math.round(rect.left * scaleX),
            Math.round(rect.top * scaleY),
            output.width,
            output.height,
            0,
            0,
            output.width,
            output.height,
          );
          const createdAt = new Date().toISOString();
          const capture: DirectorCapture = {
            id: `director-capture-${Date.now()}`,
            dataUrl: output.toDataURL("image/png"),
            cameraId: activeCamera?.id ?? null,
            shotId: useDirectorStore.getState().activeShotId,
            cameraName: activeCamera?.name ?? "导演视角",
            aspectRatio,
            width: output.width,
            height: output.height,
            createdAt,
          };
          const currentState = useDirectorStore.getState();
          const record = currentState.projectId
            ? getDirectorProjectRegistrySnapshot().records.find(
                (candidate) =>
                  candidate.identity.projectId === currentState.projectId,
              )
            : null;
          const currentOwner =
            currentState.projectOwner &&
            currentState.projectId &&
            currentState.sessionId &&
            currentState.generation !== null &&
              ({
                owner: { ...currentState.projectOwner },
                projectId: currentState.projectId,
                sessionId: currentState.sessionId,
                generation: currentState.generation,
              } satisfies DirectorAsyncOwnerSnapshotV1);
          const ingressContext: DirectorAsyncIngressContextV1 | null =
            currentOwner && record
              ? {
                  owner: currentOwner,
                  sourceFingerprint: directorDocumentFingerprint(
                    record.document,
                  ),
                }
              : null;
          const envelope: DirectorAsyncResultEnvelopeV1<DirectorCapture> = {
            operationId: request.operationId,
            kind: request.kind,
            owner: request.owner,
            attemptId: request.attemptId,
            sourceFingerprint: request.sourceFingerprint,
            resultId: capture.id,
            resultVersionId: capture.id,
            phase: "succeeded",
            payload: capture,
          };
          if (
            ingressContext &&
            directorAsyncAuthority.reconcile(envelope, ingressContext)
              .disposition ===
              "apply-current"
          ) {
            onCaptured(capture);
          }
        } finally {
          setCapturing(false);
        }
      });
    });

    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.cancelAnimationFrame(secondFrame);
    };
  }, [
    activeCamera,
    aspectRatio,
    camera,
    frameRect,
    gl,
    onCaptured,
    request,
    scene,
    setCapturing,
  ]);

  return null;
}

function VideoExportController({
  request,
  frameRect,
  onProgress,
  onCompleted,
  onFailed,
}: {
  request: DirectorVideoExportRequest | null;
  frameRect: DirectorFrameRect | null;
  onProgress: (progress: number) => void;
  onCompleted: (result: DirectorVideoExportResult) => void;
  onFailed: (message: string) => void;
}) {
  const gl = useThree((state) => state.gl);
  const setCapturing = useDirectorStore((state) => state.setCapturing);
  const setTimelineTime = useDirectorStore((state) => state.setTimelineTime);
  const setTimelinePlaying = useDirectorStore(
    (state) => state.setTimelinePlaying,
  );
  const handledRequest = useRef(0);

  useEffect(() => {
    if (!request || request.id === handledRequest.current) return;
    handledRequest.current = request.id;
    const previousTimeline = useDirectorStore.getState().timeline;
    const sourceCanvas = gl.domElement;
    const crop = frameRect ?? {
      left: 0,
      top: 0,
      width: Math.max(sourceCanvas.clientWidth, 1),
      height: Math.max(sourceCanvas.clientHeight, 1),
    };
    let active = true;

    setTimelinePlaying(false);
    setCapturing(true);
    onProgress(0);

    void recordDirectorCanvasVideo({
      sourceCanvas,
      frameRect: crop,
      request,
      timelineDuration: previousTimeline.duration,
      onTimelineTime: setTimelineTime,
      onProgress: (progress) => {
        if (active) onProgress(progress);
      },
    })
      .then((result) => {
        if (active) onCompleted(result);
        else URL.revokeObjectURL(result.videoUrl);
      })
      .catch((error: unknown) => {
        if (!active) return;
        onFailed(
          error instanceof DirectorVideoExportError
            ? error.userMessage
            : "动画视频录制失败",
        );
      })
      .finally(() => {
        if (!active) return;
        setTimelineTime(previousTimeline.currentTime);
        if (previousTimeline.isPlaying) setTimelinePlaying(true);
        setCapturing(false);
      });

    return () => {
      active = false;
    };
  }, [
    frameRect,
    gl,
    onCompleted,
    onFailed,
    onProgress,
    request,
    setCapturing,
    setTimelinePlaying,
    setTimelineTime,
  ]);

  return null;
}

/**
 * ★★★ Batch 862（源站逐字）：取景框上的**构图参考线**开关。
 *
 * ★ 源站逐字（chunk 的 `mP` 组件）：
 * ```js
 * a?(0,i.jsx)("button",{
 *   type:"button",
 *   title:s("canvas:directorAspectFrameOverlay"),
 *   className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8
 *     items-center justify-center rounded-lg transition-colors
 *     ${n?"bg-(--btn-secondary-bg) text-btn-primary"
 *        :"text-white/50 hover:bg-white/10 hover:text-white/80"}`,
 *   style:{left:u.left+u.width-40, top:u.top+8},
 *   onClick:a,
 *   children:(0,i.jsx)(d.f,{className:"h-4 w-4 shrink-0","aria-hidden":!0})
 * }):null
 * ```
 * ★ 调用点（逐字）：`onToggleCompositionGrid:null!==tr?()=>{…}:void 0`
 *   ⟹ ⟹ **这枚按钮只在「选了具体比例」时存在**（`tr===null` 时 `a` 是 `undefined`）
 *   ⟹ ⟹ 与「取景框不在场」是**同一个条件** ⟹ ⟹ clone 让它跟框同生共死。
 * ★ 位置公式（逐字）：`left = 框左 + 框宽 − 40`、`top = 框上 + 8`
 *   ⟹ ⟹ 相对框就是「右边内缩 8px」（按钮宽 32）、上边内缩 8px。
 * ★ 源站运行时实测（`raw/source-862-frame-thirds.json`）：
 *   框 @(329,185) 1262×710 ⟹ 按钮 @(1551,193) 32×32
 *   （329 + 1262 − 40 = 1551 ✔、185 + 8 = 193 ✔）⟹ ⟹ 公式实测命中。
 * ★ 开启态的类名 `bg-(--btn-secondary-bg) text-btn-primary` 在 clone 里**没有**
 *   对应变量（`--btn-secondary-bg`／`btn-primary` 全仓 0 命中）⟹ ⟹ 这里用
 *   **inline style** 给等效实测值（源站实测：bg `rgba(255,255,255,0.1)`、
 *   前景 `rgb(9,202,245)`），关闭态的类名逐字照抄（那几个类 clone 已在用）。
 */
function DirectorFrameThirdsToggle({
  frameWidth,
  showThirds,
  onToggle,
}: {
  frameWidth: number;
  showThirds: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      data-director-frame-thirds-toggle
      aria-label="构图参考线"
      title="构图参考线"
      aria-pressed={showThirds}
      onClick={onToggle}
      // ★ 源站逐字（关闭态）：`nodrag nopan nowheel pointer-events-auto absolute
      //   z-20 flex h-8 w-8 items-center justify-center rounded-lg transition-colors
      //   text-white/50 hover:bg-white/10 hover:text-white/80`
      className="nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 items-center justify-center rounded-lg transition-colors text-white/50 hover:bg-white/10 hover:text-white/80"
      style={{
        // ★ 源站逐字：`left: u.left + u.width - 40`、`top: u.top + 8`
        //   （按钮是遮罩容器的绝对定位子节点 ⟹ ⟹ 换算成「相对框」＝ 右边内缩 8px）
        left: frameWidth - 40,
        top: 8,
        // ★ 源站开启态的类名 `bg-(--btn-secondary-bg) text-btn-primary`
        //   ⟹ ⟹ clone 无这两个变量 ⟹ ⟹ 用源站实测值兜底。
        ...(showThirds
          ? { backgroundColor: "rgba(255,255,255,0.1)", color: "rgb(9,202,245)" }
          : null),
      }}
    >
      {/* ★ 源站逐字（`d.f` 图标的 svg，16×16，单 path，fill=currentColor） */}
      <svg
        width={16}
        height={16}
        fill="none"
        viewBox="0 0 16 16"
        className="h-4 w-4 shrink-0"
        aria-hidden="true"
      >
        <path
          fill="currentColor"
          d="M12.266 1.4a.6.6 0 0 1 .6.6v1.134h1.133a.6.6 0 1 1 0 1.199h-1.134v3.066H14a.601.601 0 0 1 0 1.202h-1.134v3.066H14a.6.6 0 1 1 0 1.2h-1.134V14a.6.6 0 1 1-1.199 0v-1.134H8.6V14a.601.601 0 0 1-1.202 0v-1.134H4.332V14a.6.6 0 1 1-1.2 0v-1.134H2a.6.6 0 1 1 0-1.199h1.134V8.601H1.999a.601.601 0 0 1 0-1.202h1.134V4.333H1.999a.6.6 0 1 1 0-1.2h1.134V2a.6.6 0 1 1 1.199 0v1.134h3.066V2A.601.601 0 0 1 8.6 2v1.134h3.066V2a.6.6 0 0 1 .6-.6M4.332 11.666h3.066V8.601H4.332zm4.268 0h3.066V8.601H8.6zM4.332 7.399h3.066V4.333H4.332zm4.268 0h3.066V4.333H8.6z"
        />
      </svg>
    </button>
  );
}

function AspectFrame({ frameRect }: { frameRect: DirectorFrameRect | null }) {
  // ★ Batch 860：取景框读的是**取景比例**（七档 ＋ 自适应），
  //   不是导出用的 `aspectRatio`（三值）⟹ ⟹ 两者语义不同（见 store 的注释）。
  const frameAspectRatio = useDirectorStore((state) => state.frameAspectRatio);
  const showThirds = useDirectorStore((state) => state.showThirds);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  // ★ Batch 862：框上那枚「构图参考线」开关（源站逐字）。
  const toggleThirds = useDirectorStore((state) => state.toggleThirds);
  // ★ Batch 864：源站逐字 `n4(t, "reference_line", (0,nZ.p)(e), "right_panel")`
  //   ⟹ ⟹ 切参考线时记一条**本地**的同构事件（★ **不触网**）。
  //   ★ 机位 ＝ **选中机位**，否则**第一个机位**（源站逐字 `e1 || rL.cameras[0]?.id`）。
  const objects = useDirectorStore((state) => state.objects);
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const recordTelemetry = useDirectorStore((state) => state.recordTelemetry);
  const handleToggleThirds = () => {
    const cameras = objects.filter((object) => object.kind === "camera");
    const cameraId = resolveDirectorTelemetryCameraId(cameras, activeCameraId);
    if (cameraId) {
      recordTelemetry(
        buildDirectorCameraUpdateEvent({
          cameraId,
          settingName: "reference_line",
          // ★ 源站逐字：`(0,nZ.p)(e)` ⟹ 布尔被转成 **数字**（实测 `setting_value: 1`）。
          settingValue: showThirds ? 0 : 1,
        }),
      );
    }
    toggleThirds();
  };

  // ★ 「自适应」⟹ ⟹ `frameRect` 已经是 `null` ⟹ ⟹ 框**不在场**（源站实测）。
  if (!frameRect || isCapturing) return null;

  return (
    // ★★★ Batch 863（源站逐字）：**框外遮罩**改成源站那套。
    //
    // ★ 源站逐字（chunk 的 `mP` 组件）：外层容器
    //   `pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10`，
    //   里面**第一个**子元素就是**铺满的遮罩层**：
    //   ```js
    //   (0,i.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",
    //     style:{WebkitMaskImage:"linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
    //            WebkitMaskPosition:`0 0, ${u.left}px ${u.top}px`,
    //            WebkitMaskRepeat:"no-repeat, no-repeat",
    //            WebkitMaskSize:`100% 100%, ${u.width}px ${u.height}px`,
    //            WebkitMaskComposite:"xor", maskComposite:"exclude"}})
    //   ```
    //   ⟹ ⟹ **框外**＝ 黑 20% ＋ **背景模糊**；**框内**被 mask **挖空**
    //   （`mask-composite: exclude`）⟹ ⟹ 不压暗、不模糊。
    //
    // ★ ★ clone 在本批之前**没有遮罩层** ⟹ ⟹ 框外是框自己的
    //   `shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`（**黑 24%、没有模糊**）⟹ ⟹ D20。
    // ★ 本批把那层 box-shadow **删掉**，改由遮罩层承担（与源站同构）。
    <div
      data-director-aspect-mask-container
      className="pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10"
    >
      {/* ★ 源站逐字：`absolute inset-0 bg-black/20 backdrop-blur-md` ＋ CSS mask 挖空
          （★ `bg-black/20` 与 `backdrop-blur-md` 这两个类 clone **已在别处使用**
          ⟹ ⟹ Tailwind 扫描已覆盖 ⟹ ⟹ 可以直接照抄类名）。 */}
      <div
        data-director-aspect-mask
        className="absolute inset-0 bg-black/20 backdrop-blur-md"
        style={{
          // ★ 源站逐字（`u` ＝ 框在同一个坐标系里的位置与尺寸）
          WebkitMaskImage:
            "linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
          WebkitMaskPosition: `0 0, ${frameRect.left}px ${frameRect.top}px`,
          WebkitMaskRepeat: "no-repeat, no-repeat",
          WebkitMaskSize: `100% 100%, ${frameRect.width}px ${frameRect.height}px`,
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
        }}
      />
      <div
        data-director-aspect-frame
        data-director-aspect-ratio={frameAspectRatio ?? "auto"}
        // ★ Batch 862（源站逐字）：框的描边是 **outline**（不是 border）＋ 圆角 12px。
        //   源站：`outline-white/18 absolute rounded-xl outline -outline-offset-1`
        //   ⟹ ⟹ `outline-white/18` 是**任意值类** ⟹ ⟹ 4317 的 Tailwind 扫描是冻结的
        //   （新增类不生成）⟹ ⟹ 这里用 inline style 给等效实测值。
        //   ★ ★ Batch 863：**删掉**原先那层 `shadow-[0_0_0_9999px_…]`（框外遮罩
        //   改由上面的遮罩层承担 ⟹ ⟹ 源站那个框上**没有** box-shadow）。
        className="pointer-events-none absolute"
        style={{
          left: frameRect.left,
          top: frameRect.top,
          width: frameRect.width,
          height: frameRect.height,
          // ★ 源站实测（`raw/source-862-frame-thirds.json`）：
          //   outline 1px / offset −1px / 白 18% / radius 12px
          borderRadius: "12px",
          outline: "1px solid rgba(255,255,255,0.18)",
          outlineOffset: "-1px",
        }}
      >
        {showThirds ? (
          <div data-director-thirds className="absolute inset-0">
            {/* ★ 源站逐字：`bg-(--color-white-alpha-50)`（＝ 白 50%）
              ⟹ ⟹ 任意值类未生成 ⟹ ⟹ inline style 给实测等效值。 */}
            <span
              className="absolute bottom-0 left-1/3 top-0 w-px"
              style={{ backgroundColor: "rgba(255,255,255,0.5)" }}
            />
            <span
              className="absolute bottom-0 left-2/3 top-0 w-px"
              style={{ backgroundColor: "rgba(255,255,255,0.5)" }}
            />
            <span
              className="absolute left-0 right-0 top-1/3 h-px"
              style={{ backgroundColor: "rgba(255,255,255,0.5)" }}
            />
            <span
              className="absolute left-0 right-0 top-2/3 h-px"
              style={{ backgroundColor: "rgba(255,255,255,0.5)" }}
            />
          </div>
        ) : null}
        {/* ★★ Batch 862：源站的构图参考线开关**长在取景框右上角**
            （源站逐字：`onToggleCompositionGrid:null!==tr?…:void 0`
            ⟹ ⟹ 「自适应」时连按钮一起不在场）。 */}
        <DirectorFrameThirdsToggle
          frameWidth={frameRect.width}
          showThirds={showThirds}
          onToggle={handleToggleThirds}
        />
      </div>
    </div>
  );
}

const transformTools: Array<{
  mode: DirectorTransformMode;
  label: string;
  Icon: typeof Move3D;
}> = [
  { mode: "translate", label: "移动", Icon: Move3D },
  { mode: "rotate", label: "旋转", Icon: Rotate3D },
  { mode: "scale", label: "缩放", Icon: Scaling },
];

type DirectorTransformContext = {
  kind: "none" | "object" | "group" | "path-anchor" | "path-drawing" | "busy";
  state: "idle" | "editable" | "locked" | "blocked";
  label: string;
  detail: string;
};

function ModelLibraryThumbnail({
  item,
}: {
  item: DirectorModelLibraryCardItem;
}) {
  return (
    <span
      className="relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-lg border border-white/[0.05] bg-[#1b1b1b] transition-colors group-hover:bg-[#2c3236]"
      style={{ color: item.color }}
      aria-hidden="true"
    >
      <span className="absolute inset-0 bg-[radial-gradient(circle_at_50%_28%,rgba(255,255,255,0.12),transparent_52%)]" />
      <span
        className={cn(
          "relative block border border-current/60 bg-current/45 shadow-[0_4px_8px_rgba(0,0,0,0.25)]",
          item.visual === "bottle" &&
            "h-9 w-5 rounded-[40%_40%_34%_34%]",
          item.visual === "chair" &&
            "h-7 w-9 rounded-sm border-b-4",
          item.visual === "lamp" &&
            "h-7 w-10 rounded-[60%_60%_35%_35%]",
          item.visual === "plant" &&
            "h-8 w-8 rounded-[50%_50%_35%_35%]",
          item.visual === "box" && "h-9 w-9 rounded-sm",
        )}
      >
        {item.visual === "bottle" ? (
          <span className="absolute -top-2 left-1/2 h-2 w-2 -translate-x-1/2 rounded-t-sm border border-current/60 bg-current/45" />
        ) : null}
        {item.visual === "chair" ? (
          <span className="absolute -bottom-3 left-1/2 h-3 w-6 -translate-x-1/2 border-x border-current/60" />
        ) : null}
        {item.visual === "lamp" ? (
          <span className="absolute -bottom-4 left-1/2 h-4 w-px -translate-x-1/2 bg-current/80" />
        ) : null}
        {item.visual === "plant" ? (
          <span className="absolute -bottom-2 left-1/2 h-3 w-5 -translate-x-1/2 rounded-b-md bg-[#9b694d]" />
        ) : null}
      </span>
    </span>
  );
}

function ModelLibraryCard({
  item,
  onAdd,
  onPreview,
  selected,
  onDelete,
  resourceStatus,
  onRetry,
}: {
  item: DirectorModelLibraryCardItem;
  onAdd: (item: DirectorModelLibraryCardItem) => void;
  onPreview: (item: DirectorModelLibraryCardItem) => void;
  selected: boolean;
  onDelete?: (item: DirectorLocalModelLibraryItem) => void;
  resourceStatus?: DirectorLocalResourceStatus;
  onRetry?: (resourceId: string) => void;
}) {
  const local = item.categoryId === "my-models";
  const localItem = local ? item : null;
  const card = (
    <article
      role="group"
      tabIndex={0}
      data-director-model-library-card
      data-director-model-library-add
      data-director-model-library-asset-id={item.id}
      {...(local ? { "data-director-model-library-local-card": "" } : {})}
      aria-label={`添加模型 ${item.name}`}
      onClick={() => onAdd(item)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onAdd(item);
        }
      }}
      className={cn(
        "group relative flex min-w-0 cursor-pointer flex-col items-center gap-1.5 rounded p-1 text-center text-[11px] text-[#8f8f8f] hover:bg-white/[0.04] hover:text-white focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#09caf5]",
        selected && "bg-[#09caf5]/10 text-[#dffaff]",
      )}
    >
      <span
        data-director-model-library-preview
        data-director-model-library-preview-asset-id={item.id}
        aria-hidden="true"
        className={cn("relative block rounded-lg", selected && "ring-1 ring-[#09caf5]")}
      >
        <ModelLibraryThumbnail item={item} />
      </span>
      <button
        type="button"
        data-director-model-library-preview-trigger
        data-director-model-library-preview-asset-id={item.id}
        aria-label={`预览模型 ${item.name}`}
        title="预览"
        onClick={(event) => {
          event.stopPropagation();
          onPreview(item);
        }}
        className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-black/55 text-white/80 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#09caf5]"
      >
        <Eye size={11} />
      </button>
      <span className="w-full truncate">{item.name}</span>
      {localItem && resourceStatus ? (
        <span
          data-director-model-library-local-status={resourceStatus}
          className={cn(
            "max-w-full truncate text-[9px]",
            resourceStatus === "ready" && "text-[#8fd4a8]",
            resourceStatus === "loading" && "text-[#f0c776]",
            (resourceStatus === "failed" || resourceStatus === "canceled") &&
              "text-[#e59a8c]",
            resourceStatus === "idle" && "text-[#777]",
          )}
        >
          {resourceStatus === "ready"
            ? "已加载"
            : resourceStatus === "loading"
              ? "加载中"
              : resourceStatus === "failed"
                ? "加载失败"
                : resourceStatus === "canceled"
                  ? "已取消"
                  : "待加载"}
        </span>
      ) : null}
      {localItem ? (
        <span
          data-director-model-library-local-file-name
          className="sr-only"
        >
          {localItem.fileName}
        </span>
      ) : null}
    </article>
  );

  if (!localItem || !onDelete) return card;

  return (
    <div className="group relative min-w-0">
      {card}
      <button
        type="button"
        data-director-model-library-local-delete
        data-director-model-library-local-asset-id={localItem.id}
        aria-label={`删除模型及场景实例 ${localItem.name}`}
        title="删除模型及场景实例"
        onClick={() => onDelete(localItem)}
        className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-black/55 text-[#bdbdbd] opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#09caf5] hover:bg-black/75 hover:text-white"
      >
        <X size={12} />
      </button>
      {resourceStatus === "failed" || resourceStatus === "canceled" ? (
        <button
          type="button"
          data-director-model-library-local-retry
          data-director-model-library-local-asset-id={localItem.id}
          aria-label={`重试加载模型 ${localItem.name}`}
          title="重试加载"
          onClick={(event) => {
            event.stopPropagation();
            onRetry?.(localItem.id);
          }}
          className="absolute bottom-1 right-1 flex h-5 w-5 items-center justify-center rounded-full bg-black/55 text-[#f0c776] opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#09caf5] hover:bg-black/75 hover:text-white"
        >
          <RotateCcw size={11} />
        </button>
      ) : null}
    </div>
  );
}

export function DirectorViewport({
  onOpenTree,
  onOpenInspector,
  panoramaInput,
  onPanoramaStatusChange,
  videoExportRequest,
  onVideoExportProgress,
  onVideoExportCompleted,
  onVideoExportFailed,
  bottomBarExtra,
}: {
  onOpenTree: () => void;
  onOpenInspector: () => void;
  panoramaInput: DirectorCanvasMediaInputV1 | null;
  onPanoramaStatusChange: (status: DirectorPanoramaRuntimeState) => void;
  videoExportRequest: DirectorVideoExportRequest | null;
  onVideoExportProgress: (progress: number) => void;
  onVideoExportCompleted: (result: DirectorVideoExportResult) => void;
  onVideoExportFailed: (message: string) => void;
  // Batch 604（源站实测）：视口底部浮动条是 `flex items-center gap-2` 的
  // **一行**，工具胶囊（nav）与 prompt 胶囊（grid）并排居中。prompt 胶囊由
  // DirectorDesk 构造并经此插槽放进同一行——这样既对齐源站结构，也顺带
  // 消掉 clone 此前「工具条 z-10 @(651,904) 与 prompt 条 z-20 @(266,908)
  // 几乎完全重叠、后者 pointer-events-auto 吞掉前者点击」的问题。
  bottomBarExtra?: ReactNode;
}) {
  // Batch 608：底部胶囊那枚「动画时间轴」开关
  const timelinePanelOpen = useDirectorStore((state) => state.timelinePanelOpen);
  const toggleTimelinePanel = useDirectorStore((state) => state.toggleTimelinePanel);
  const viewMode = useDirectorStore((state) => state.viewMode);
  const transformMode = useDirectorStore((state) => state.transformMode);
  // ★ Batch 860：取景比例（七档 ＋ 自适应）⟹ ⟹ 驱动机位取景框；
  //   导出比例 `aspectRatio`（三值）仍另有一路（截图/导出），两者分开。
  const frameAspectRatio = useDirectorStore((state) => state.frameAspectRatio);
  const setFrameAspectRatio = useDirectorStore((state) => state.setFrameAspectRatio);
  // ★ 导出/截图用的比例（三值）⟹ ⟹ 与上面的**取景比例**是两件事。
  const captureAspectRatio = useDirectorStore((state) => state.aspectRatio);
  const showThirds = useDirectorStore((state) => state.showThirds);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const selectedObjectIds = useDirectorStore(
    (state) => state.selectedObjectIds,
  );
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const activeCamera = useDirectorStore((state) =>
    state.objects.find((object) => object.id === activeCameraId),
  );
  const phoneVcamStatus = useDirectorStore(
    (state) => state.phoneVcam.status,
  );
  const timeline = useDirectorStore((state) => state.timeline);
  const setTransformMode = useDirectorStore((state) => state.setTransformMode);
  const toggleThirds = useDirectorStore((state) => state.toggleThirds);
  const viewportPanelsCollapsed = useDirectorStore(
    (state) => state.viewportPanelsCollapsed,
  );
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  const setCapturing = useDirectorStore((state) => state.setCapturing);
  const addCapture = useDirectorStore((state) => state.addCapture);
  const addModelLibraryObject = useDirectorStore(
    (state) => state.addModelLibraryObject,
  );
  const localModelLibrary = useDirectorStore(
    (state) => state.localModelLibrary,
  );
  const localModelResources = useDirectorStore(
    (state) => state.localModelResources,
  );
  const hydrateLocalModelLibrary = useDirectorStore(
    (state) => state.hydrateLocalModelLibrary,
  );
  const addLocalModelLibraryItem = useDirectorStore(
    (state) => state.addLocalModelLibraryItem,
  );
  const removeLocalModelLibraryItem = useDirectorStore(
    (state) => state.removeLocalModelLibraryItem,
  );
  const retryLocalModelResource = useDirectorStore(
    (state) => state.retryLocalModelResource,
  );
  const selectObject = useDirectorStore((state) => state.selectObject);
  const finishMotionPathDrawing = useDirectorStore(
    (state) => state.finishMotionPathDrawing,
  );
  const cancelMotionPathDrawing = useDirectorStore(
    (state) => state.cancelMotionPathDrawing,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const viewportRef = useRef<HTMLDivElement>(null);
  const { eventSourceRef, setEventSource } = useDirectorCanvasEventSource();
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const [viewportSnapshot, setViewportSnapshot] =
    useState<DirectorViewportSnapshot>(
      DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT,
    );
  const [panoramaRuntimeState, setPanoramaRuntimeState] =
    useState<DirectorPanoramaRuntimeState>(
      panoramaInput ? "loading" : "empty",
    );
  const viewportSnapshotRef = useRef(viewportSnapshot);
  const [directorCameraCommand, setDirectorCameraCommand] =
    useState<DirectorViewportSnapshot | null>(null);
  // ★ Batch 851：orbit 中心必须是**引用稳定**的 state ⟹ ⟹ 之前是字面量 [0,1,0]，
  //   drei 把它透传给 <primitive object={controls}> ⟹ ⟹ R3F 每次 re-render 都会 apply
  //   ⟹ ⟹ WASDQE 平移出来的 orbit 中心会被下一次 re-render 打回默认。
  const [directorOrbitTarget, setDirectorOrbitTarget] =
    useState<DirectorTuple3>([0, 1, 0]);
  // ★ Batch 851：OrbitControls 实例的 ref ⟹ ⟹ 快捷键直接改它（与源站同一条路径）
  const directorOrbitControlsRef = useRef<ElementRef<typeof OrbitControls> | null>(
    null,
  );
  // Batch 543: 源站截图 18——重置视角恢复导演台默认机位（新对象触发
  // CameraController 重新应用快照）。
  const handleResetDirectorView = () => {
    setDirectorCameraCommand({ ...DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT });
  };
  const [captureRequest, setCaptureRequest] =
    useState<DirectorAsyncOperationDescriptorV1 | null>(null);
  const captureRequestSequence = useRef(0);
  const [phoneVcamOpen, setPhoneVcamOpen] = useState(false);
  // ★★★ Batch 857：**删掉**视口里的 legacy 群众阵列面板（`crowdPanelOpen` 等）。
  //   ★ 理由：源站**只有一个**「添加群众阵列」入口（rail 的「添加角色 → 群众 (3x3)」）
  //   ⟹ ⟹ 源站实测（自指判据）：全页「aria-label 等于对话框那个」的元素**只有 1 个**
  //   ⟹ ⟹ 视口工具栏这枚按钮是**clone 多出来的入口**。
  //   ⟹ ⟹ 而且它那套面板的量程也是 clone 自己发明的（行≤6／列≤8／间距 0.6–3），
  //   ⟹ ⟹ 源站是 1–10／1–10／0.1–10 ⟹ ⟹ 两处都对不上。
  const [modelLibraryOpen, setModelLibraryOpen] = useState(false);
  const [activeModelLibraryCategoryId, setActiveModelLibraryCategoryId] =
    useState<DirectorModelLibraryCategoryId>("convenience");
  const [modelLibrarySearch, setModelLibrarySearch] = useState("");
  const [selectedModelLibraryAssetId, setSelectedModelLibraryAssetId] =
    useState<string | null>(null);
  const modelLibraryTriggerRef = useRef<HTMLButtonElement>(null);
  const modelLibraryPanelRef = useRef<HTMLDivElement>(null);
  const localModelLibraryInputRef = useRef<HTMLInputElement>(null);
  const phoneVcamRecording = phoneVcamStatus === "recording";
  const viewportGizmoDisabled =
    timeline.motionPathDraft !== null || phoneVcamRecording;
  const handlePanoramaStatusChange = useCallback(
    (status: Exclude<DirectorPanoramaRuntimeState, "empty">) => {
      setPanoramaRuntimeState(status);
      onPanoramaStatusChange(status);
    },
    [onPanoramaStatusChange],
  );
  const transformContext = useMemo<DirectorTransformContext>(() => {
    if (phoneVcamRecording) {
      return {
        kind: "busy",
        state: "blocked",
        label: "虚拟相机录制中",
        detail: "录制结束后可变换",
      };
    }
    if (isCapturing) {
      return {
        kind: "busy",
        state: "blocked",
        label: "正在保存构图",
        detail: "完成后可变换",
      };
    }
    if (timeline.motionPathDraft) {
      return {
        kind: "path-drawing",
        state: "blocked",
        label: "正在绘制路径",
        detail: "完成或取消后可变换",
      };
    }

    const selectedAnchorId = timeline.selectedMotionPathAnchorId;
    if (selectedAnchorId) {
      const selectedPath = timeline.motionPaths.find((path) =>
        path.anchors.some((anchor) => anchor.id === selectedAnchorId),
      );
      const pathObject = selectedPath
        ? objects.find((object) => object.id === selectedPath.objectId)
        : null;
      const locked = Boolean(pathObject?.locked);
      return {
        kind: "path-anchor",
        state: locked ? "locked" : "editable",
        label: pathObject ? `${pathObject.name} · 路径锚点` : "路径锚点",
        detail: locked ? "对象已锁定" : "可拖动控制点",
      };
    }

    if (selectedGroupId) {
      const selectedGroup = groups.find((group) => group.id === selectedGroupId);
      // ★★ Batch 855：锁定守卫按**全部成员**（源站 `O(e)`）。
      const locked = Boolean(
        selectedGroup &&
        resolveGroupMemberRefs(selectedGroup).some((member) =>
          objects.some((object) => object.id === member.id && object.locked),
        ),
      );
      return {
        kind: "group",
        state: locked ? "locked" : "editable",
        label: selectedGroup?.label ?? "分组",
        detail: locked ? "含锁定成员" : "可变换分组",
      };
    }

    const selectedObject = objects.find((object) => object.id === selectedObjectId);
    if (selectedObject) {
      return {
        kind: "object",
        state: selectedObject.locked ? "locked" : "editable",
        label: selectedObject.name,
        detail: selectedObject.locked ? "对象已锁定" : "可拖动三轴控件",
      };
    }

    if (selectedObjectIds.length > 1) {
      return {
        kind: "none",
        state: "idle",
        label: `${selectedObjectIds.length} 个对象`,
        detail: "多选暂不显示三轴控件",
      };
    }

    return {
      kind: "none",
      state: "idle",
      label: "未选择对象",
      detail: "选择对象后可变换",
    };
  }, [
    groups,
    isCapturing,
    objects,
    phoneVcamRecording,
    selectedGroupId,
    selectedObjectId,
    selectedObjectIds.length,
    timeline.motionPathDraft,
    timeline.motionPaths,
    timeline.selectedMotionPathAnchorId,
  ]);

  const handleViewportSnapshot = useCallback(
    (snapshot: DirectorViewportSnapshot) => {
      viewportSnapshotRef.current = snapshot;
      setViewportSnapshot(snapshot);
    },
    [],
  );

  const handleViewportAxisSelect = useCallback(
    (axis: DirectorViewportAxisId) => {
      const nextSnapshot = getDirectorViewportAxisSnapshot(
        viewportSnapshotRef.current,
        axis,
      );
      viewportSnapshotRef.current = nextSnapshot;
      setViewportSnapshot(nextSnapshot);
      setDirectorCameraCommand(nextSnapshot);
      setViewMode("director");
    },
    [setViewMode],
  );

  useLayoutEffect(() => {
    const element = viewportRef.current;
    if (!element) return;
    const updateSize = () =>
      setViewportSize({ width: element.clientWidth, height: element.clientHeight });
    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!timeline.motionPathDraft) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" && event.key !== "Enter") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if (event.key === "Escape") {
        cancelMotionPathDrawing();
        cancelDirectorGesture();
      } else {
        finishMotionPathDrawing();
        commitDirectorGesture();
      }
    };
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [
    cancelDirectorGesture,
    cancelMotionPathDrawing,
    commitDirectorGesture,
    finishMotionPathDrawing,
    timeline.motionPathDraft,
  ]);

  useEffect(() => {
    hydrateLocalModelLibrary();
  }, [hydrateLocalModelLibrary]);

  useEffect(() => {
    const nextState: DirectorPanoramaRuntimeState = panoramaInput
      ? "loading"
      : "empty";
    setPanoramaRuntimeState(nextState);
    onPanoramaStatusChange(nextState);
  }, [onPanoramaStatusChange, panoramaInput]);

  useEffect(() => {
    if (!modelLibraryOpen) return;
    const closeOnOutsidePointerDown = (event: PointerEvent) => {
      if (!(event.target instanceof Node)) return;
      if (modelLibraryTriggerRef.current?.contains(event.target)) return;
      if (modelLibraryPanelRef.current?.contains(event.target)) return;
      setModelLibraryOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      setModelLibraryOpen(false);
    };
    document.addEventListener("pointerdown", closeOnOutsidePointerDown);
    window.addEventListener("keydown", closeOnEscape, true);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointerDown);
      window.removeEventListener("keydown", closeOnEscape, true);
    };
  }, [modelLibraryOpen]);

  // ★ Batch 860：取景框按**取景比例**算 ⟹ ⟹ 七档数值比例（源站实测六档全对），
  //   「自适应」＝ `null` ⟹ ⟹ `getDirectorFrameRect` 直接返回 `null` ⟹ ⟹ 框不在场。
  const frameRatio = useDirectorStore((state) => state.frameAspectRatio);
  const frameAspectValue =
    frameRatio === null ? null : DIRECTOR_FRAME_ASPECT_VALUES[frameRatio];

  const frameRect = useMemo(
    () =>
      getDirectorFrameRect(
        viewportSize.width,
        viewportSize.height,
        frameAspectValue,
      ),
    [frameAspectValue, viewportSize.height, viewportSize.width],
  );

  const requestCapture = () => {
    if (isCapturing) return;
    const currentState = useDirectorStore.getState();
    const record = currentState.projectId
      ? getDirectorProjectRegistrySnapshot().records.find(
          (candidate) => candidate.identity.projectId === currentState.projectId,
        )
      : null;
    if (
      !currentState.projectOwner ||
      !currentState.projectId ||
      !currentState.sessionId ||
      currentState.generation === null ||
      !record
    ) {
      return;
    }
    const owner: DirectorAsyncOwnerSnapshotV1 = {
      owner: { ...currentState.projectOwner },
      projectId: currentState.projectId,
      sessionId: currentState.sessionId,
      generation: currentState.generation,
    };
    captureRequestSequence.current += 1;
    const descriptor: DirectorAsyncOperationDescriptorV1 = {
      operationId: createDirectorAsyncIdentity("director-capture"),
      kind: "capture",
      owner,
      attemptId: createDirectorAsyncIdentity("director-capture-attempt"),
      sourceFingerprint: directorDocumentFingerprint(record.document),
      requestFingerprint: JSON.stringify({
        aspectRatio: captureAspectRatio,
        frameRect,
        activeCameraId: currentState.activeCameraId,
        sequence: captureRequestSequence.current,
      }),
      acceptedAt: new Date().toISOString(),
      selectionPolicy: "preserve-current",
    };
    if (directorAsyncAuthority.begin(descriptor).disposition !== "accepted") {
      return;
    }
    setCapturing(true);
    setCaptureRequest(descriptor);
  };

  const toggleModelLibrary = () => {
    setPhoneVcamOpen(false);
    setModelLibraryOpen((value) => !value);
  };

  const selectModelLibraryItem = (item: DirectorModelLibraryCardItem) => {
    setSelectedModelLibraryAssetId(item.id);
  };

  const addModelLibraryItem = (item: DirectorModelLibraryItem) => {
    addModelLibraryObject(item);
    setModelLibraryOpen(false);
  };

  const addLocalModelLibraryItemToScene = (
    item: DirectorLocalModelLibraryItem,
  ) => {
    addModelLibraryObject(item);
    setModelLibraryOpen(false);
  };

  const handleLocalModelLibraryChange = async (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const input = event.currentTarget;
    try {
      const items = await readDirectorLocalModelFiles(input.files ?? []);
      items.forEach(addLocalModelLibraryItem);
    } finally {
      input.value = "";
    }
  };

  const openLocalModelLibraryImport = () => {
    localModelLibraryInputRef.current?.click();
  };

  const activeModelLibraryItems =
    activeModelLibraryCategoryId === "my-models"
      ? localModelLibrary
      : getDirectorModelLibraryItems(activeModelLibraryCategoryId);
  const visibleModelLibraryItems = filterDirectorModelLibraryItems(
    activeModelLibraryItems,
    modelLibrarySearch,
  );
  const previewModelLibraryItem =
    visibleModelLibraryItems.find(
      (item) => item.id === selectedModelLibraryAssetId,
    ) ??
    visibleModelLibraryItems[0] ??
    null;

  useEffect(() => {
    if (
      previewModelLibraryItem &&
      previewModelLibraryItem.id !== selectedModelLibraryAssetId
    ) {
      setSelectedModelLibraryAssetId(previewModelLibraryItem.id);
    }
    if (!previewModelLibraryItem && selectedModelLibraryAssetId !== null) {
      setSelectedModelLibraryAssetId(null);
    }
  }, [previewModelLibraryItem, selectedModelLibraryAssetId]);

  return (
    <section
      ref={viewportRef}
      data-director-viewport
      data-director-view={viewMode}
      data-director-panels-collapsed={viewportPanelsCollapsed}
      // ★ Batch 851：把**当前相机位姿**暴露成 DOM 属性 ⟹ ⟹ 门禁才能断言
      //   「按 T 之后相机到底变成了哪个坐标」，而不只是「画面变了」。
      data-director-view-position={viewportSnapshot.position.join(",")}
      data-director-view-target={viewportSnapshot.target.join(",")}
      data-director-view-fov={viewportSnapshot.fov}
      className="relative h-full min-h-0 min-w-0 overflow-hidden bg-[#20252b]"
      aria-label="3D导演视口"
    >
      <div
        ref={setEventSource}
        data-director-webgl-canvas
        className="absolute inset-0"
      >
        <Canvas
          eventSource={eventSourceRef}
          shadows
          frameloop="always"
          dpr={[1, 2]}
          camera={{ position: [6.2, 4.25, 7.4], fov: 45, near: 0.1, far: 100 }}
          gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
          onPointerMissed={() => {
            if (
              !timeline.motionPathDraft &&
              !timeline.selectedMotionPathAnchorId
            ) {
              selectObject(null, "viewport");
            }
          }}
          onCreated={({ gl }) => {
            gl.domElement.dataset.directorWebglCanvas = "true";
            gl.domElement.setAttribute("aria-label", "导演台 WebGL 场景");
          }}
        >
          <CameraController
            directorCameraCommand={directorCameraCommand}
            directorOrbitTarget={directorOrbitTarget}
            onOrbitTargetChange={setDirectorOrbitTarget}
            controlsRef={directorOrbitControlsRef}
          />
          <DirectorViewShortcutController
            onOrbitTargetChange={setDirectorOrbitTarget}
            controlsRef={directorOrbitControlsRef}
          />
          <DirectorCameraSnapshotBridge
            cameraTarget={activeCamera?.camera?.target ?? [0, 1, 0]}
            onSnapshot={handleViewportSnapshot}
            viewMode={viewMode}
            controlsRef={directorOrbitControlsRef}
          />
          <DirectorScene
            panoramaInput={panoramaInput}
            onPanoramaStatusChange={handlePanoramaStatusChange}
          />
          <CaptureController
            request={captureRequest}
            frameRect={frameRect}
            onCaptured={addCapture}
          />
          <VideoExportController
            request={videoExportRequest}
            frameRect={frameRect}
            onProgress={onVideoExportProgress}
            onCompleted={onVideoExportCompleted}
            onFailed={onVideoExportFailed}
          />
          <CameraPreviewRenderer />
        </Canvas>
      </div>

      <div
        data-director-local-model-resource-statuses
        className="sr-only"
      >
        {Object.values(localModelResources).map((resource) => (
          <span
            key={resource.descriptor.resourceId}
            data-director-local-model-resource-status={
              resource.descriptor.resourceId
            }
            data-director-local-model-resource-state={resource.status}
            data-director-local-model-resource-attempt={resource.attempt}
            data-director-local-model-resource-error={resource.error ?? ""}
          >
            {resource.errorMessage ?? resource.status}
          </span>
        ))}
      </div>
      <div
        data-director-panorama-runtime
        data-director-panorama-state={panoramaRuntimeState}
        data-director-panorama-source-id={panoramaInput?.sourceNodeId ?? ""}
        className="sr-only"
      >
        {panoramaRuntimeState === "error" ? (
          <span data-director-panorama-error>
            画布环境图片加载失败，已保留其他场景对象
          </span>
        ) : (
          panoramaRuntimeState
        )}
      </div>

      {!isCapturing ? (
        <DirectorViewportGizmo
          disabled={viewportGizmoDisabled}
          onAxisSelect={handleViewportAxisSelect}
          onResetView={handleResetDirectorView}
          snapshot={viewportSnapshot}
        />
      ) : null}

      <div
        data-director-motion-path-layer
        data-director-motion-path-count={timeline.motionPaths.length}
        className="sr-only"
      >
        {timeline.motionPaths.map((path) => (
          <span
            key={path.id}
            data-director-motion-path-id={path.id}
            data-director-motion-path-preset={path.preset}
            data-director-motion-path-visible={
              path.enabled && viewMode === "director" && !isCapturing
            }
            data-director-motion-path-pivot={path.pivot.join(",")}
          >
            {path.name}
            {path.anchors.map((anchor, index) => (
              <span
                key={anchor.id}
                data-director-motion-path-anchor={index}
                data-director-motion-path-anchor-id={anchor.id}
                data-director-motion-path-anchor-type={anchor.type}
                data-director-motion-path-anchor-selected={
                  anchor.id === timeline.selectedMotionPathAnchorId
                }
                data-director-motion-path-world-anchor={buildDirectorMotionPathWorldAnchors(
                  [anchor],
                  path.pivot,
                  path.transform,
                )[0].position.join(",")}
              >
                {anchor.type !== "vertex" ? (
                  <>
                    <span data-director-motion-path-handle="in" />
                    <span data-director-motion-path-handle="out" />
                  </>
                ) : null}
              </span>
            ))}
          </span>
        ))}
      </div>

      <AspectFrame frameRect={frameRect} />

      {timeline.motionPathDraft ? (
        <div
          data-director-path-drawing
          data-director-path-drawing-tool={timeline.motionPathDraft.tool}
          className="absolute bottom-[76px] left-1/2 z-20 flex h-9 -translate-x-1/2 items-center gap-1 rounded border border-[#f6b85f]/35 bg-[#24211d]/95 px-2 shadow-[0_8px_20px_rgba(0,0,0,0.3)]"
        >
          <span className="px-1 text-[11px] text-[#f2c781]">
            正在绘制曲线
          </span>
          {timeline.motionPathDraft.tool === "pen" ? (
            <button
              type="button"
              data-director-path-drawing-complete
              aria-label="完成钢笔路径"
              title="完成"
              onClick={() => {
                finishMotionPathDrawing();
                commitDirectorGesture();
              }}
              className="flex h-7 w-7 items-center justify-center rounded text-[#a9d8bf] hover:bg-white/[0.07] hover:text-white"
            >
              <Check size={14} />
            </button>
          ) : null}
          <button
            type="button"
            data-director-path-drawing-cancel
            aria-label="取消路径绘制"
            title="取消"
            onClick={() => {
              cancelMotionPathDrawing();
              cancelDirectorGesture();
            }}
            className="flex h-7 w-7 items-center justify-center rounded text-[#b8a09a] hover:bg-white/[0.07] hover:text-white"
          >
            <X size={14} />
          </button>
        </div>
      ) : null}

      <DirectorPhoneVcamPanel
        open={phoneVcamOpen}
        onClose={() => setPhoneVcamOpen(false)}
      />

      {/* ★★★ Batch 857：视口里的 legacy 群众阵列面板**已删**（源站没有这个入口）。
          唯一的「添加群众阵列」入口在 **rail 的「添加角色 → 群众 (3x3)」**。 */}

      {modelLibraryOpen ? (
        <div
          ref={modelLibraryPanelRef}
          data-director-model-library-panel
          role="dialog"
          aria-label="模型库"
          className="absolute bottom-[72px] left-1/2 z-30 h-[360px] max-h-[calc(100%-120px)] w-[500px] max-w-[calc(100%-24px)] -translate-x-1/2 overflow-hidden rounded-lg border border-white/10 bg-[#242424]/[.98] text-[#dedede] shadow-[0_12px_32px_rgba(0,0,0,0.42)]"
        >
          <input
            ref={localModelLibraryInputRef}
            data-director-model-library-local-input
            type="file"
            accept=".fbx,.obj"
            multiple
            onChange={(event) => void handleLocalModelLibraryChange(event)}
            className="sr-only"
          />
          <div className="flex h-10 items-center justify-between border-b border-white/[0.06] px-3">
            <h2 className="text-xs font-medium text-[#eeeeee]">模型库</h2>
            <button
              type="button"
              aria-label="关闭模型库"
              title="关闭模型库"
              onClick={() => setModelLibraryOpen(false)}
              className="flex h-7 w-7 items-center justify-center rounded text-[#858585] hover:bg-white/[0.06] hover:text-white"
            >
              <X size={15} />
            </button>
          </div>
          <div
            className="grid h-10 grid-cols-5 border-b border-white/[0.06]"
            role="tablist"
            aria-label="模型分类"
          >
            {DIRECTOR_MODEL_LIBRARY_CATEGORIES.map((category) => {
              const active = category.id === activeModelLibraryCategoryId;
              return (
                <button
                  key={category.id}
                  type="button"
                  data-director-model-library-tab={category.id}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setActiveModelLibraryCategoryId(category.id)}
                  className={cn(
                    "relative min-w-0 px-1 text-[11px] text-[#777] hover:text-white",
                    active && "text-[#5ddcff]",
                  )}
                >
                  {category.label}
                  {active ? (
                    <span className="absolute bottom-0 left-1/2 h-[2px] w-7 -translate-x-1/2 bg-[#09caf5]" />
                  ) : null}
                </button>
              );
            })}
          </div>
          <label className="flex h-9 items-center gap-2 border-b border-white/[0.06] px-3 text-[#777] focus-within:text-[#bdbdbd]">
            <Search size={13} />
            <input
              data-director-model-library-search
              aria-label="搜索模型"
              value={modelLibrarySearch}
              onChange={(event) => setModelLibrarySearch(event.target.value)}
              placeholder="搜索模型"
              className="min-w-0 flex-1 bg-transparent text-[11px] text-[#dedede] outline-none placeholder:text-[#666]"
            />
          </label>
          {previewModelLibraryItem ? (
            <div
              data-director-model-library-preview-panel
              data-director-model-library-preview-asset-id={
                previewModelLibraryItem.id
              }
              className="flex h-[72px] items-center gap-2 border-b border-white/[0.06] px-3"
            >
              <ModelLibraryThumbnail item={previewModelLibraryItem} />
              <div className="min-w-0 flex-1">
                <p
                  data-director-model-library-preview-name
                  data-director-model-library-preview-name-value={
                    previewModelLibraryItem.name
                  }
                  aria-label={`已选资源 ${previewModelLibraryItem.name}`}
                  className="truncate text-[11px] text-[#e2e2e2]"
                >
                  已选资源
                </p>
                <p className="mt-1 truncate text-[10px] text-[#6f6f6f]">
                  {getDirectorModelLibraryCategoryLabel(
                    previewModelLibraryItem.categoryId,
                  )}
                  {"fileName" in previewModelLibraryItem
                    ? ` · ${previewModelLibraryItem.fileName}`
                    : " · 场景代理模型"}
                </p>
              </div>
              <button
                type="button"
                data-director-model-library-preview-add
                aria-label={`加入场景 ${previewModelLibraryItem.name}`}
                onClick={() => {
                  if (previewModelLibraryItem.categoryId === "my-models") {
                    addLocalModelLibraryItemToScene(previewModelLibraryItem);
                  } else {
                    addModelLibraryItem(previewModelLibraryItem);
                  }
                }}
                className="flex h-7 shrink-0 items-center gap-1 rounded bg-[#e7e7e7] px-2 text-[10px] text-[#202020] hover:bg-white"
              >
                <Plus size={12} />
                加入场景
              </button>
            </div>
          ) : null}
          {activeModelLibraryCategoryId === "my-models" &&
          activeModelLibraryItems.length === 0 &&
          modelLibrarySearch.trim() === "" ? (
            <div
              data-director-model-library-empty
              className="flex h-[calc(100%-157px)] flex-col items-center justify-center gap-3 text-xs text-[#777]"
              role="status"
              aria-label="暂无任何模型"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/[0.04] text-[#666]">
                <Boxes size={19} />
              </span>
              <span>暂无任何模型</span>
              <button
                type="button"
                data-director-model-library-import
                onClick={openLocalModelLibraryImport}
                className="h-7 rounded border border-white/[0.08] bg-white/[0.05] px-3 text-[11px] text-[#b5b5b5] hover:bg-white/[0.09] hover:text-white"
              >
                本地导入
              </button>
            </div>
          ) : (
            <div
              className="grid h-[calc(100%-157px)] auto-rows-max grid-cols-3 gap-x-3 gap-y-4 overflow-y-auto p-3 min-[480px]:grid-cols-4 min-[680px]:grid-cols-5"
              role="list"
              aria-label="模型列表"
            >
              {visibleModelLibraryItems.length === 0 ? (
                <div
                  data-director-model-library-no-results
                  role="status"
                  aria-label="未搜索到模型"
                  className="col-span-full flex min-h-[120px] items-center justify-center text-center text-[11px] text-[#686868]"
                >
                  未搜索到模型
                </div>
              ) : (
                visibleModelLibraryItems.map((item) => (
                  <ModelLibraryCard
                    key={item.id}
                    item={item}
                    selected={selectedModelLibraryAssetId === item.id}
                    onPreview={selectModelLibraryItem}
                    onAdd={(nextItem) => {
                      if (nextItem.categoryId === "my-models") {
                        addLocalModelLibraryItemToScene(nextItem);
                        return;
                      }
                      addModelLibraryItem(nextItem);
                    }}
                    onDelete={
                      item.categoryId === "my-models"
                        ? (localItem) =>
                            removeLocalModelLibraryItem(
                              localItem.id,
                              "CASCADE",
                            )
                        : undefined
                    }
                    resourceStatus={
                      item.categoryId === "my-models"
                        ? localModelResources[item.id]?.status
                        : undefined
                    }
                    onRetry={retryLocalModelResource}
                  />
                ))
              )}
              {activeModelLibraryCategoryId === "my-models" &&
              modelLibrarySearch.trim() === "" ? (
                <button
                  type="button"
                  data-director-model-library-import
                  aria-label="本地导入"
                  onClick={openLocalModelLibraryImport}
                  className="group flex min-w-0 flex-col items-center gap-1.5 rounded p-1 text-center text-[11px] text-[#777] hover:bg-white/[0.04] hover:text-white focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#09caf5]"
                >
                  <span className="flex h-16 w-16 items-center justify-center rounded-lg border border-dashed border-white/15 bg-transparent text-[#777] group-hover:bg-white/[0.04] group-hover:text-white">
                    <span className="text-2xl leading-none">+</span>
                  </span>
                  <span className="w-full truncate">本地导入</span>
                </button>
              ) : null}
            </div>
          )}
        </div>
      ) : null}

      <div className="absolute left-3 top-3 z-10 hidden gap-1 max-[899px]:flex">
        <button
          type="button"
          aria-label="打开场景对象"
          title="场景对象"
          onClick={onOpenTree}
          className="flex h-8 w-8 items-center justify-center rounded border border-white/10 bg-[#222]/95 text-[#bcbcbc]"
        >
          <PanelLeftOpen size={15} />
        </button>
        <button
          type="button"
          aria-label="打开属性面板"
          title="属性"
          onClick={onOpenInspector}
          className="flex h-8 w-8 items-center justify-center rounded border border-white/10 bg-[#222]/95 text-[#bcbcbc]"
        >
          <PanelRightOpen size={15} />
        </button>
      </div>

      {/* Batch 604（源站 2026-10-01 实测 1920x1150）：视口底部浮动条的外壳
          逐字是 `z-(--z-sticky) pointer-events-none absolute inset-x-0
          bottom-0 flex flex-col items-center gap-1`（1920x182 @(0,968)
          z=200，内容 = 48 工具行 + 4 gap-1 + 130 导演台），其下 `pointer-
          events-auto flex items-center gap-2` 把两枚胶囊并排居中（源站实测
          360 宽 @(780,968)）。clone 的 main 不含导演台，所以这一层只承载
          胶囊行；z 取源站解析值 200。`px-3` 是 clone 侧新增的窄屏留白
          （源站此处无内边距，它靠整屏居中）。 */}
      <div
        data-director-bottom-bar
        className="pointer-events-none absolute inset-x-0 bottom-0 z-[200] flex flex-col items-center gap-1 px-3"
      >
        <div className="pointer-events-auto flex w-full overflow-x-auto">
          {/* `mx-auto` + `shrink-0`：内容比容器宽时 auto 外边距解析为 0，
              左侧不会被 justify-center 顶出裁切区（窄屏仍可横向滚动）。 */}
          <div className="mx-auto flex shrink-0 items-center gap-2">
      <div
        data-director-viewport-toolbar
        // 源站逐字：relative flex h-12 shrink-0 items-center gap-2 rounded-full
        // border border-white/10 bg-[rgba(33,33,33,0.94)] text-white
        // shadow-[0_1px_2px_rgba(0,0,0,0.18)] backdrop-blur-xl w-32 p-2
        // ——`w-32`(128px) 恰好装满源站那三项(3x32+2x8+2x8)，clone 的控件集
        // 更大，故去掉定宽让内容撑开；`max-w-[calc(100vw-48px)] overflow-x-
        // auto` 是 clone 窄屏保护（batch41 断言工具条 390 宽下 x>=12 且右缘
        // <=378）。其余逐字照抄。
        className="relative flex h-12 max-w-[calc(100vw-48px)] shrink-0 items-center gap-2 overflow-x-auto rounded-full border border-white/10 bg-[rgba(33,33,33,0.94)] p-2 text-white shadow-[0_1px_2px_rgba(0,0,0,0.18)] backdrop-blur-xl"
      >
        <div
          data-director-transform-context
          data-director-transform-context-kind={transformContext.kind}
          data-director-transform-context-state={transformContext.state}
          data-director-transform-context-target={transformContext.label}
          aria-label={`${transformContext.label}，${transformContext.detail}`}
          title={transformContext.detail}
          className="flex min-w-0 max-w-[154px] shrink-0 items-center gap-1.5 border-r border-white/10 px-1.5 pr-2 text-[10px] max-[520px]:max-w-[112px]"
        >
          <Move3D
            size={14}
            aria-hidden="true"
            className={cn(
              "shrink-0",
              transformContext.state === "editable" && "text-[#5ddcff]",
              transformContext.state === "locked" && "text-[#f0c776]",
              transformContext.state === "blocked" && "text-[#e59a8c]",
              transformContext.state === "idle" && "text-[#777]",
            )}
          />
          <span className="min-w-0 truncate">
            <span
              data-director-transform-context-label
              className={cn(
                "block truncate",
                transformContext.state === "editable" && "text-[#d9f8ff]",
                transformContext.state === "locked" && "text-[#f0c776]",
                transformContext.state === "blocked" && "text-[#e59a8c]",
                transformContext.state === "idle" && "text-[#a0a0a0]",
              )}
            >
              {transformContext.label}
            </span>
            <span
              data-director-transform-context-detail
              className="block truncate text-[9px] text-[#6f6f6f]"
            >
              {transformContext.detail}
            </span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          {transformTools.map(({ mode, label, Icon }) => (
            <button
              key={mode}
              type="button"
              aria-label={label}
              title={label}
              aria-pressed={transformMode === mode}
              data-director-transform-mode={mode}
              onClick={() => setTransformMode(mode)}
              className={cn(
                "group relative flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
                transformMode === mode && "bg-white/8",
              )}
            >
              <Icon size={20} aria-hidden="true" />
            </button>
          ))}
        </div>
        {/* 源站底部第一枚胶囊只有三项：移动 / 截图 / 动画时间轴
            （各 32x32，icon 20px，`aria-pressed=true` 选中态追加 `bg-white/8`，
            实测 @(869,976)）。clone 这枚胶囊控件更多（变换模式/画幅/九宫格/
            虚拟相机/群众/模型库/保存构图），本批把源站有而 clone 无的
            「动画时间轴」补进来，位置放在变换模式之后、画幅比例之前。
            语义是「开关整条时间轴面板」，与面板内的「时间线最小化」
            （182 -> 88，面板仍在）互不影响。
            注意：源站这枚按钮的点击行为**未取证**（点它可能改用户真实工程），
            aria-pressed 的语义取自「按钮名 + 开态 + 面板可见」的联合读法，
            属 clone 侧推断，不声称源站的确切结果。 */}
        <button
          type="button"
          data-director-timeline-toggle
          aria-label="动画时间轴"
          title="动画时间轴"
          aria-pressed={timelinePanelOpen}
          onClick={toggleTimelinePanel}
          className={cn(
            "group relative flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
            timelinePanelOpen && "bg-white/8",
          )}
        >
          <Film size={20} aria-hidden="true" />
        </button>
        <span className="mx-0.5 h-5 w-px bg-white/10" />
        <div className="flex items-center gap-2" role="group" aria-label="画幅比例">
          {(["16:9", "9:16", "1:1"] as const).map((ratio) => (
            <button
              key={ratio}
              type="button"
              data-director-aspect={ratio}
              // ★ Batch 860：这两组是 **clone 自己的扩展**（源站实测：底部
              //   27 枚控件里**没有**比例按钮，源站的画幅比例只在左侧面板七格）。
              //   ⟹ ⟹ 保留它们（不擅自删用户可见功能），但让它们与左侧面板
              //   **共享同一个取景比例状态** ⟹ ⟹ 两处不会打架。
              aria-pressed={frameAspectRatio === ratio}
              onClick={() => setFrameAspectRatio(ratio)}
              className={cn(
                "flex h-8 min-w-10 shrink-0 items-center justify-center rounded-lg text-[10px] tabular-nums text-white transition-colors hover:bg-white/8",
                frameAspectRatio === ratio && "bg-white/8",
              )}
            >
              {ratio}
            </button>
          ))}
        </div>
        <button
          type="button"
          aria-label={showThirds ? "关闭九宫格辅助线" : "开启九宫格辅助线"}
          title="九宫格辅助线"
          aria-pressed={showThirds}
          onClick={toggleThirds}
          className={cn(
            "group relative flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
            showThirds && "bg-white/8",
          )}
        >
          <Grid3X3 size={20} aria-hidden="true" />
        </button>
        <span className="mx-0.5 h-5 w-px bg-white/10" />
        <button
          type="button"
          data-director-phone-vcam-trigger
          aria-label="虚拟相机"
          title="虚拟相机"
          aria-expanded={phoneVcamOpen}
          aria-pressed={phoneVcamOpen}
          onClick={() => {
            if (phoneVcamRecording) return;
            setModelLibraryOpen(false);
            setPhoneVcamOpen((value) => !value);
          }}
          className={cn(
            "group relative flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
            phoneVcamOpen && "bg-white/8",
            phoneVcamRecording && "text-[#ed7a7d]",
          )}
        >
          <Smartphone size={20} aria-hidden="true" />
        </button>
        {/* ★★★ Batch 857：**移动端**唯一的一枚「添加群众阵列」入口。
            ★ 源站**没有移动端布局**：实测 390×844 下源站渲染的仍是桌面
              画布（页面宽于视口、导演台根本没开，见
              docs/research/liblib-canvas-batch857-2026-10-01/raw/source-857-mobile.json）
              ⟹ ⟹ 「源站的移动端入口」**不存在**，也就无从对齐。
            ★ 但 clone **有自己的**移动端适配 ⟹ ⟹ 不能因为对齐桌面就把
              **移动端的能力**删掉（那不是对齐，是制造缺口）。
            ★ 所以：**桌面隐藏、只有移动端出现** ⟹ ⟹ 桌面端可见的 crowd
              入口仍然**只有 rail 那一枚**（与源站一致），移动端也**只有
              这一枚**（clone 自己的扩展，已如实登记）。
            ★ 它开的是**同一个**对话框（源站逐字那套量程／默认值／落点规则）。 */}
        <button
          type="button"
          data-director-crowd-mobile-trigger
          aria-label="添加群众阵列"
          title="添加群众阵列"
          className={cn(
            "group relative hidden size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
            "max-[899px]:flex",
          )}
          onClick={(event) => {
            setModelLibraryOpen(false);
            setPhoneVcamOpen(false);
            const rect = event.currentTarget.getBoundingClientRect();
            window.dispatchEvent(
              new CustomEvent("director:open-crowd-dialog", {
                detail: {
                  rect: {
                    left: rect.left,
                    top: rect.top,
                    right: rect.right,
                    bottom: rect.bottom,
                  },
                },
              }),
            );
          }}
        >
          <Users size={20} aria-hidden="true" />
        </button>
        {/* ★★★ Batch 857：桌面的「添加群众阵列」入口**只有 rail 那一枚**
            （源站逐字：`"aria-haspopup":"dialog","aria-expanded":"crowd"===L`
            ⟹ ⟹ 全页同 aria-label 的元素只有 1 个，见
            raw/source-857-crowd.json 的「⑤同aria元素」）。 */}
        <button
          ref={modelLibraryTriggerRef}
          type="button"
          data-director-model-library-trigger
          aria-label="模型库"
          title="模型库"
          aria-expanded={modelLibraryOpen}
          onClick={toggleModelLibrary}
          className={cn(
            "group relative flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-colors hover:bg-white/8",
            modelLibraryOpen && "bg-white/8",
          )}
        >
          <Boxes size={20} aria-hidden="true" />
        </button>
        <span className="mx-0.5 h-5 w-px bg-white/10" />
        <button
          type="button"
          data-director-capture
          disabled={
            isCapturing ||
            timeline.motionPathDraft !== null ||
            phoneVcamRecording
          }
          onClick={requestCapture}
          className="flex h-8 items-center gap-1.5 rounded-lg bg-[#e7e7e7] px-2.5 text-[11px] text-[#202020] hover:bg-white disabled:bg-[#555] disabled:text-[#999]"
        >
          {viewMode === "camera" ? <Camera size={14} /> : <ImagePlus size={14} />}
          <span className="max-[520px]:hidden">
            {isCapturing ? "截图中" : "保存构图"}
          </span>
        </button>
      </div>
            {bottomBarExtra}
          </div>
        </div>
      </div>
    </section>
  );
}
