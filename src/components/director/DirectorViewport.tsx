"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  Camera,
  Check,
  Grid3X3,
  ImagePlus,
  Move3D,
  PanelLeftOpen,
  PanelRightOpen,
  Rotate3D,
  Scaling,
  X,
} from "lucide-react";
import { Line, OrbitControls, TransformControls } from "@react-three/drei";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import {
  DoubleSide,
  MathUtils,
  PerspectiveCamera,
  type Group,
  type MeshStandardMaterialParameters,
} from "three";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorCapture,
  type DirectorMotionPath,
  type DirectorMotionPathAnchor,
  type DirectorMotionPathHandle,
  type DirectorObject,
  type DirectorTransformMode,
  type DirectorTuple3,
} from "@/store/directorStore";
import {
  buildDirectorMotionPathPoints,
  buildDirectorMotionPathWorldAnchors,
} from "@/components/director/directorMotionMath";
import {
  getDirectorFrameRect,
  type DirectorFrameRect,
} from "@/components/director/directorViewportMath";
import {
  DirectorVideoExportError,
  recordDirectorCanvasVideo,
  type DirectorVideoExportRequest,
  type DirectorVideoExportResult,
} from "@/components/director/directorVideoExport";

/* eslint-disable react-hooks/immutability -- Three.js cameras are mutable runtime objects managed by R3F. */
function CameraController() {
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

  useEffect(() => {
    const perspective = camera as PerspectiveCamera;
    if (!perspective.isPerspectiveCamera) return;

    if (viewMode === "camera" && activeCamera?.camera) {
      perspective.position.set(...activeCamera.transform.position);
      perspective.fov = activeCamera.camera.fov;
      perspective.lookAt(...activeCamera.camera.target);
      perspective.updateProjectionMatrix();
      perspective.updateMatrixWorld();
      invalidate();
    } else if (previousMode.current === "camera") {
      perspective.position.set(6.2, 4.25, 7.4);
      perspective.fov = 45;
      perspective.lookAt(0, 1, 0);
      perspective.updateProjectionMatrix();
      perspective.updateMatrixWorld();
      invalidate();
    }
    previousMode.current = viewMode;
  }, [activeCamera, camera, invalidate, viewMode]);

  if (viewMode !== "director") return null;

  return (
    <OrbitControls
      makeDefault
      enabled={!isCapturing && motionPathDraft === null}
      enableDamping
      dampingFactor={0.08}
      minDistance={2.5}
      maxDistance={20}
      maxPolarAngle={Math.PI / 2.02}
      target={[0, 1, 0]}
    />
  );
}
/* eslint-enable react-hooks/immutability */

function CharacterPrimitive({
  color,
  material,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
}) {
  return (
    <group>
      <mesh castShadow position={[0, 2.02, 0]}>
        <sphereGeometry args={[0.25, 24, 18]} />
        <meshStandardMaterial color="#c9aa94" {...material} />
      </mesh>
      <mesh castShadow position={[0, 1.35, 0]}>
        <capsuleGeometry args={[0.34, 0.72, 8, 16]} />
        <meshStandardMaterial color={color} roughness={0.72} {...material} />
      </mesh>
      <mesh castShadow position={[-0.2, 0.48, 0]}>
        <capsuleGeometry args={[0.11, 0.7, 6, 12]} />
        <meshStandardMaterial color="#25282e" roughness={0.8} {...material} />
      </mesh>
      <mesh castShadow position={[0.2, 0.48, 0]}>
        <capsuleGeometry args={[0.11, 0.7, 6, 12]} />
        <meshStandardMaterial color="#25282e" roughness={0.8} {...material} />
      </mesh>
      <mesh castShadow position={[-0.46, 1.38, 0]} rotation={[0, 0, -0.13]}>
        <capsuleGeometry args={[0.09, 0.66, 6, 12]} />
        <meshStandardMaterial color={color} roughness={0.72} {...material} />
      </mesh>
      <mesh castShadow position={[0.46, 1.38, 0]} rotation={[0, 0, 0.13]}>
        <capsuleGeometry args={[0.09, 0.66, 6, 12]} />
        <meshStandardMaterial color={color} roughness={0.72} {...material} />
      </mesh>
    </group>
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

function SceneObject({ object }: { object: DirectorObject }) {
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
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
  const selectedMotionPathAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const groupRef = useRef<Group>(null);
  const selected = selectedObjectId === object.id;

  const hideCameraRig =
    object.kind === "camera" &&
    (isCapturing || (viewMode === "camera" && object.id === activeCameraId));
  if (!object.visible || hideCameraRig) return null;

  const material: MeshStandardMaterialParameters = selected
    ? {
        emissive: "#075e71",
        emissiveIntensity: 0.36,
      }
    : {};
  const rotation = object.transform.rotation.map((value) =>
    MathUtils.degToRad(value),
  ) as [number, number, number];

  const commitTransform = () => {
    const group = groupRef.current;
    if (!group) return;
    const values = {
      position: [group.position.x, group.position.y, group.position.z],
      rotation: [
        MathUtils.radToDeg(group.rotation.x),
        MathUtils.radToDeg(group.rotation.y),
        MathUtils.radToDeg(group.rotation.z),
      ],
      scale: [group.scale.x, group.scale.y, group.scale.z],
    } as const;
    (["position", "rotation", "scale"] as const).forEach((field) => {
      values[field].forEach((value, axis) => {
        updateObjectTransform(
          object.id,
          field,
          axis as 0 | 1 | 2,
          Number(value.toFixed(3)),
        );
      });
    });
    recordObjectKeyframe(object.id);
  };

  const content = (
    <group
      ref={groupRef}
      position={object.transform.position}
      rotation={rotation}
      scale={object.transform.scale}
      onClick={(event: ThreeEvent<MouseEvent>) => {
        event.stopPropagation();
        if (motionPathDraft || selectedMotionPathAnchorId) return;
        selectObject(object.id, "viewport");
      }}
    >
      {object.primitive === "character" ? (
        <CharacterPrimitive color={object.color} material={material} />
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
    <TransformControls
      mode={transformMode}
      size={0.72}
      onMouseUp={commitTransform}
    >
      {content}
    </TransformControls>
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
  const selectedAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const selectedHandle = useDirectorStore(
    (state) => state.timeline.selectedMotionPathHandle,
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
  const groupRef = useRef<Group>(null);
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

  const commit = () => {
    const group = groupRef.current;
    if (!group) return;
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
      return;
    }
    updateMotionPathAnchorWorldPosition(
      path.id,
      anchor.id,
      worldPosition,
    );
  };

  const content = (
    <group
      ref={groupRef}
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

  if (!selected) return content;
  return (
    <TransformControls mode="translate" size={0.62} onMouseUp={commit}>
      {content}
    </TransformControls>
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
  const finishMotionPathDrawing = useDirectorStore(
    (state) => state.finishMotionPathDrawing,
  );
  const pointerActive = useRef(false);

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
          if (draft.tool === "pencil") finishMotionPathDrawing();
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

function DirectorScene() {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const isCapturing = useDirectorStore((state) => state.isCapturing);

  return (
    <>
      <color attach="background" args={[scene.backgroundColor]} />
      <fog attach="fog" args={[scene.backgroundColor, 9, 24]} />
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
        <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
          <planeGeometry args={[32, 32]} />
          <meshStandardMaterial color={scene.groundColor} roughness={0.94} />
        </mesh>
      ) : null}
      {scene.showGrid && !isCapturing ? (
        <gridHelper args={[24, 24, "#59636c", "#3d454c"]} position={[0, 0.006, 0]} />
      ) : null}
      {objects.map((object) => (
        <SceneObject key={object.id} object={object} />
      ))}
      <DirectorMotionPaths />
      <DirectorMotionPathDrawingSurface />
    </>
  );
}

function CaptureController({
  request,
  frameRect,
  onCaptured,
}: {
  request: number;
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
  const handledRequest = useRef(0);

  useEffect(() => {
    if (request <= 0 || request === handledRequest.current) return;
    handledRequest.current = request;
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
          const context = output.getContext("2d");
          if (!context) throw new Error("Director capture canvas is unavailable");
          context.drawImage(
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
          onCaptured({
            id: `director-capture-${Date.now()}`,
            dataUrl: output.toDataURL("image/png"),
            cameraId: activeCamera?.id ?? null,
            cameraName: activeCamera?.name ?? "导演视角",
            aspectRatio,
            width: output.width,
            height: output.height,
            createdAt,
          });
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

function AspectFrame({ frameRect }: { frameRect: DirectorFrameRect | null }) {
  const aspectRatio = useDirectorStore((state) => state.aspectRatio);
  const showThirds = useDirectorStore((state) => state.showThirds);
  const isCapturing = useDirectorStore((state) => state.isCapturing);

  if (!frameRect || isCapturing) return null;

  return (
    <div
      data-director-aspect-frame
      data-director-aspect-ratio={aspectRatio}
      className="pointer-events-none absolute border border-white/75 shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]"
      style={{
        left: frameRect.left,
        top: frameRect.top,
        width: frameRect.width,
        height: frameRect.height,
      }}
    >
      {showThirds ? (
        <div data-director-thirds className="absolute inset-0">
          <span className="absolute bottom-0 left-1/3 top-0 w-px bg-white/35" />
          <span className="absolute bottom-0 left-2/3 top-0 w-px bg-white/35" />
          <span className="absolute left-0 right-0 top-1/3 h-px bg-white/35" />
          <span className="absolute left-0 right-0 top-2/3 h-px bg-white/35" />
        </div>
      ) : null}
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

export function DirectorViewport({
  onOpenTree,
  onOpenInspector,
  videoExportRequest,
  onVideoExportProgress,
  onVideoExportCompleted,
  onVideoExportFailed,
}: {
  onOpenTree: () => void;
  onOpenInspector: () => void;
  videoExportRequest: DirectorVideoExportRequest | null;
  onVideoExportProgress: (progress: number) => void;
  onVideoExportCompleted: (result: DirectorVideoExportResult) => void;
  onVideoExportFailed: (message: string) => void;
}) {
  const viewMode = useDirectorStore((state) => state.viewMode);
  const transformMode = useDirectorStore((state) => state.transformMode);
  const aspectRatio = useDirectorStore((state) => state.aspectRatio);
  const showThirds = useDirectorStore((state) => state.showThirds);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const timeline = useDirectorStore((state) => state.timeline);
  const setTransformMode = useDirectorStore((state) => state.setTransformMode);
  const setAspectRatio = useDirectorStore((state) => state.setAspectRatio);
  const toggleThirds = useDirectorStore((state) => state.toggleThirds);
  const setCapturing = useDirectorStore((state) => state.setCapturing);
  const addCapture = useDirectorStore((state) => state.addCapture);
  const selectObject = useDirectorStore((state) => state.selectObject);
  const finishMotionPathDrawing = useDirectorStore(
    (state) => state.finishMotionPathDrawing,
  );
  const cancelMotionPathDrawing = useDirectorStore(
    (state) => state.cancelMotionPathDrawing,
  );
  const viewportRef = useRef<HTMLDivElement>(null);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const [captureRequest, setCaptureRequest] = useState(0);

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
      if (event.key === "Escape") cancelMotionPathDrawing();
      else finishMotionPathDrawing();
    };
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [
    cancelMotionPathDrawing,
    finishMotionPathDrawing,
    timeline.motionPathDraft,
  ]);

  const frameRect = useMemo(
    () =>
      getDirectorFrameRect(
        viewportSize.width,
        viewportSize.height,
        aspectRatio,
      ),
    [aspectRatio, viewportSize.height, viewportSize.width],
  );

  const requestCapture = () => {
    if (isCapturing) return;
    setCapturing(true);
    setCaptureRequest((value) => value + 1);
  };

  return (
    <section
      ref={viewportRef}
      data-director-viewport
      data-director-view={viewMode}
      className="relative h-full min-h-0 min-w-0 overflow-hidden bg-[#20252b]"
      aria-label="3D导演视口"
    >
      <div data-director-webgl-canvas className="absolute inset-0">
        <Canvas
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
          <CameraController />
          <DirectorScene />
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
        </Canvas>
      </div>

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
              onClick={finishMotionPathDrawing}
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
            onClick={cancelMotionPathDrawing}
            className="flex h-7 w-7 items-center justify-center rounded text-[#b8a09a] hover:bg-white/[0.07] hover:text-white"
          >
            <X size={14} />
          </button>
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

      <div
        data-director-viewport-toolbar
        className="absolute bottom-5 left-1/2 z-10 flex h-11 max-w-[calc(100%-24px)] -translate-x-1/2 items-center gap-1 rounded-md border border-white/10 bg-[#222]/95 px-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.34)]"
      >
        <div className="flex items-center">
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
                "flex h-8 w-8 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
                transformMode === mode && "bg-white/10 text-[#5ddcff]",
              )}
            >
              <Icon size={15} />
            </button>
          ))}
        </div>
        <span className="mx-0.5 h-5 w-px bg-white/10" />
        <div className="flex items-center" role="group" aria-label="画幅比例">
          {(["16:9", "9:16", "1:1"] as const).map((ratio) => (
            <button
              key={ratio}
              type="button"
              data-director-aspect={ratio}
              aria-pressed={aspectRatio === ratio}
              onClick={() => setAspectRatio(ratio)}
              className={cn(
                "h-8 min-w-10 rounded px-1.5 text-[10px] tabular-nums text-[#8d8d8d] hover:text-white",
                aspectRatio === ratio && "bg-white/10 text-white",
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
            "flex h-8 w-8 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
            showThirds && "bg-white/10 text-[#5ddcff]",
          )}
        >
          <Grid3X3 size={15} />
        </button>
        <span className="mx-0.5 h-5 w-px bg-white/10" />
        <button
          type="button"
          data-director-capture
          disabled={isCapturing || timeline.motionPathDraft !== null}
          onClick={requestCapture}
          className="flex h-8 items-center gap-1.5 rounded bg-[#e7e7e7] px-2.5 text-[11px] text-[#202020] hover:bg-white disabled:bg-[#555] disabled:text-[#999]"
        >
          {viewMode === "camera" ? <Camera size={14} /> : <ImagePlus size={14} />}
          <span className="max-[520px]:hidden">
            {isCapturing ? "截图中" : "保存构图"}
          </span>
        </button>
      </div>
    </section>
  );
}
