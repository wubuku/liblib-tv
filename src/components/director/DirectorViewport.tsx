"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type CSSProperties,
} from "react";
import {
  Camera,
  Check,
  Boxes,
  Eye,
  Expand,
  Grid3X3,
  ImagePlus,
  Minimize2,
  Move3D,
  PanelLeftOpen,
  PanelRightOpen,
  Plus,
  Rotate3D,
  Search,
  Scaling,
  Smartphone,
  Users,
  X,
} from "lucide-react";
import {
  GizmoHelper,
  GizmoViewport,
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
  Matrix4,
  MathUtils,
  PerspectiveCamera,
  Quaternion,
  Vector3,
  type Group,
  type MeshStandardMaterialParameters,
} from "three";
import { cn } from "@/lib/utils";
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
  getDirectorProjectRegistrySnapshot,
  useDirectorStore,
  type DirectorCapture,
  type DirectorCharacterGroup,
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
  getDirectorViewportAxis,
  getDirectorViewportAxisSnapshot,
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

/* eslint-disable react-hooks/immutability -- Three.js cameras are mutable runtime objects managed by R3F. */
const DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT: DirectorViewportSnapshot = {
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

function CameraController({
  directorCameraCommand,
}: {
  directorCameraCommand: DirectorViewportSnapshot | null;
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
        invalidate();
      } else if (previousMode.current === "camera") {
        applyDirectorViewportSnapshot(
          perspective,
          DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT,
        );
        invalidate();
      }
    }
    previousMode.current = viewMode;
  }, [activeCamera, camera, directorCameraCommand, invalidate, viewMode]);

  if (viewMode !== "director") return null;

  return (
    <OrbitControls
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
      target={[0, 1, 0]}
    />
  );
}
/* eslint-enable react-hooks/immutability */

function DirectorCameraSnapshotBridge({
  cameraTarget,
  onSnapshot,
  viewMode,
}: {
  cameraTarget: DirectorViewportSnapshot["target"];
  onSnapshot: (snapshot: DirectorViewportSnapshot) => void;
  viewMode: "director" | "camera";
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

    const target: DirectorViewportSnapshot["target"] =
      viewMode === "director" ? [0, 1, 0] : [...cameraTarget];
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
  snapshot,
}: {
  disabled: boolean;
  onAxisSelect: (axis: DirectorViewportAxisId) => void;
  snapshot: DirectorViewportSnapshot;
}) {
  return (
    <div
      data-director-viewport-gizmo
      aria-label="3D视口原生坐标控件"
      data-director-viewport-gizmo-position={snapshot.position.join(",")}
      data-director-viewport-gizmo-target={snapshot.target.join(",")}
      className="absolute right-5 top-5 z-20 h-20 w-20"
    >
      <div
        className="pointer-events-none absolute inset-0 drop-shadow-[0_2px_5px_rgba(0,0,0,0.48)]"
        data-director-gizmo-webgl-canvas-wrapper
      >
        <Canvas
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
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const selectedMotionPathAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const groupRef = useRef<Group>(null);
  const selected = selectedObjectId === object.id && selectedGroupId === null;
  const owningGroup = groups.find((group) =>
    group.characterIds.includes(object.id),
  );

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
    commitDirectorGesture();
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
        if (owningGroup) {
          useDirectorStore.getState().selectGroup(owningGroup.id);
          return;
        }
        selectObject(object.id, "viewport");
      }}
    >
      {object.primitive === "character" ? (
        <DirectorMannequin
          color={object.color}
          material={material}
          rig={object.characterRig ?? createDirectorCharacterRig()}
        />
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
      {object.primitive === "library" && object.libraryVisual ? (
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
    <TransformControls
      mode={transformMode}
      size={0.72}
      onMouseDown={() =>
        beginDirectorGesture({
          commandKind: "object-transform",
          targetId: object.id,
          fieldScope: transformMode,
        })
      }
      onMouseUp={commitTransform}
    >
      {content}
    </TransformControls>
  );
}

function DirectorGroupTransformRig({
  group,
}: {
  group: DirectorCharacterGroup;
}) {
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const objects = useDirectorStore((state) => state.objects);
  const transformMode = useDirectorStore((state) => state.transformMode);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const motionPathDraft = useDirectorStore(
    (state) => state.timeline.motionPathDraft,
  );
  const selectedMotionPathAnchorId = useDirectorStore(
    (state) => state.timeline.selectedMotionPathAnchorId,
  );
  const updateGroupTransform = useDirectorStore(
    (state) => state.updateGroupTransform,
  );
  const recordGroupKeyframe = useDirectorStore(
    (state) => state.recordGroupKeyframe,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const groupRef = useRef<Group>(null);
  const anchor = getDirectorGroupAnchorTransform(objects, group);
  if (
    !anchor ||
    selectedGroupId !== group.id ||
    isCapturing ||
    motionPathDraft !== null ||
    selectedMotionPathAnchorId !== null
  ) {
    return null;
  }

  const commitTransform = () => {
    const current = groupRef.current;
    if (!current) return;
    const nextTransform = {
      position: [
        current.position.x,
        current.position.y,
        current.position.z,
      ] as DirectorTuple3,
      rotation: [
        MathUtils.radToDeg(current.rotation.x),
        MathUtils.radToDeg(current.rotation.y),
        MathUtils.radToDeg(current.rotation.z),
      ] as DirectorTuple3,
      scale: [current.scale.x, current.scale.y, current.scale.z] as DirectorTuple3,
    };
    updateGroupTransform(group.id, nextTransform);
    recordGroupKeyframe(group.id);
    commitDirectorGesture();
  };

  return (
    <group data-director-group-rig={group.id}>
      <TransformControls
        mode={transformMode}
        size={0.82}
        onMouseDown={() =>
          beginDirectorGesture({
            commandKind: "group-transform",
            targetId: group.id,
            fieldScope: transformMode,
          })
        }
        onMouseUp={commitTransform}
      >
        <group
          ref={groupRef}
          position={anchor.position}
          rotation={anchor.rotation.map((value) =>
            MathUtils.degToRad(value),
          ) as [number, number, number]}
          scale={anchor.scale}
        />
      </TransformControls>
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

  const commit = () => {
    const group = groupRef.current;
    if (!group) {
      transformActiveRef.current = false;
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
      transformActiveRef.current = false;
      commitDirectorGesture();
      return;
    }
    updateMotionPathAnchorWorldPosition(
      path.id,
      anchor.id,
      worldPosition,
    );
    transformActiveRef.current = false;
    commitDirectorGesture();
  };

  useEffect(() => {
    const handlePointerCancel = () => {
      if (!transformActiveRef.current) return;
      transformActiveRef.current = false;
      cancelDirectorGesture();
    };
    window.addEventListener("pointercancel", handlePointerCancel);
    return () =>
      window.removeEventListener("pointercancel", handlePointerCancel);
  }, [cancelDirectorGesture]);

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
    <TransformControls
      mode="translate"
      size={0.62}
      onMouseDown={() => {
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
      onPointerCancel={() => {
        if (!transformActiveRef.current) return;
        transformActiveRef.current = false;
        cancelDirectorGesture();
      }}
    >
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

function DirectorScene() {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const groups = useDirectorStore((state) => state.groups);

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
      {groups.map((group) => (
        <DirectorGroupTransformRig key={group.id} group={group} />
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
}: {
  item: DirectorModelLibraryCardItem;
  onAdd: (item: DirectorModelLibraryCardItem) => void;
  onPreview: (item: DirectorModelLibraryCardItem) => void;
  selected: boolean;
  onDelete?: (item: DirectorLocalModelLibraryItem) => void;
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
    </div>
  );
}

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
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const activeCamera = useDirectorStore((state) =>
    state.objects.find((object) => object.id === activeCameraId),
  );
  const phoneVcamStatus = useDirectorStore(
    (state) => state.phoneVcam.status,
  );
  const timeline = useDirectorStore((state) => state.timeline);
  const setTransformMode = useDirectorStore((state) => state.setTransformMode);
  const setAspectRatio = useDirectorStore((state) => state.setAspectRatio);
  const toggleThirds = useDirectorStore((state) => state.toggleThirds);
  const viewportPanelsCollapsed = useDirectorStore(
    (state) => state.viewportPanelsCollapsed,
  );
  const toggleViewportPanelsCollapsed = useDirectorStore(
    (state) => state.toggleViewportPanelsCollapsed,
  );
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  const setCapturing = useDirectorStore((state) => state.setCapturing);
  const addCapture = useDirectorStore((state) => state.addCapture);
  const addCrowdArray = useDirectorStore((state) => state.addCrowdArray);
  const addModelLibraryObject = useDirectorStore(
    (state) => state.addModelLibraryObject,
  );
  const localModelLibrary = useDirectorStore(
    (state) => state.localModelLibrary,
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
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const [viewportSnapshot, setViewportSnapshot] =
    useState<DirectorViewportSnapshot>(
      DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT,
    );
  const viewportSnapshotRef = useRef(viewportSnapshot);
  const [directorCameraCommand, setDirectorCameraCommand] =
    useState<DirectorViewportSnapshot | null>(null);
  const [captureRequest, setCaptureRequest] =
    useState<DirectorAsyncOperationDescriptorV1 | null>(null);
  const captureRequestSequence = useRef(0);
  const [phoneVcamOpen, setPhoneVcamOpen] = useState(false);
  const [crowdPanelOpen, setCrowdPanelOpen] = useState(false);
  const [crowdRows, setCrowdRows] = useState("3");
  const [crowdColumns, setCrowdColumns] = useState("3");
  const [crowdSpacing, setCrowdSpacing] = useState("1.2");
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
        aspectRatio,
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

  const crowdTotal = Math.min(
    Math.max(Number(crowdRows) || 1, 1),
    6,
  ) * Math.min(Math.max(Number(crowdColumns) || 1, 1), 8);

  const addCrowd = () => {
    addCrowdArray({
      rows: Number(crowdRows),
      columns: Number(crowdColumns),
      spacing: Number(crowdSpacing),
    });
    setCrowdPanelOpen(false);
  };

  const toggleModelLibrary = () => {
    setPhoneVcamOpen(false);
    setCrowdPanelOpen(false);
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
          <CameraController
            directorCameraCommand={directorCameraCommand}
          />
          <DirectorCameraSnapshotBridge
            cameraTarget={activeCamera?.camera?.target ?? [0, 1, 0]}
            onSnapshot={handleViewportSnapshot}
            viewMode={viewMode}
          />
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

      {!isCapturing ? (
        <DirectorViewportGizmo
          disabled={viewportGizmoDisabled}
          onAxisSelect={handleViewportAxisSelect}
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

      {crowdPanelOpen ? (
        <div
          data-director-crowd-panel
          role="dialog"
          aria-label="添加群众阵列"
          className="absolute bottom-[72px] left-1/2 z-20 w-[272px] -translate-x-1/2 rounded border border-white/10 bg-[#242424]/[.98] p-3 shadow-[0_12px_28px_rgba(0,0,0,0.38)]"
        >
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs text-[#dedede]">添加群众阵列</h2>
            <span
              data-director-crowd-count={crowdTotal}
              className="text-[10px] tabular-nums text-[#777]"
            >
              共{crowdTotal}人
            </span>
          </div>
          <div className="grid grid-cols-[1fr_auto_1fr] gap-2">
            <label className="block">
              <span className="mb-1 block text-[10px] text-[#777]">行数</span>
              <input
                data-director-crowd-rows
                type="number"
                min="1"
                max="6"
                value={crowdRows}
                onChange={(event) => setCrowdRows(event.target.value)}
                className="h-8 w-full rounded border border-white/[0.08] bg-[#1b1b1b] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
              />
            </label>
            <span className="self-end pb-2 text-xs text-[#666]">×</span>
            <label className="block">
              <span className="mb-1 block text-[10px] text-[#777]">列数</span>
              <input
                data-director-crowd-columns
                type="number"
                min="1"
                max="8"
                value={crowdColumns}
                onChange={(event) => setCrowdColumns(event.target.value)}
                className="h-8 w-full rounded border border-white/[0.08] bg-[#1b1b1b] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
              />
            </label>
          </div>
          <label className="mt-2 block">
            <span className="mb-1 block text-[10px] text-[#777]">间距</span>
            <input
              data-director-crowd-spacing
              type="number"
              min="0.6"
              max="3"
              step="0.1"
              value={crowdSpacing}
              onChange={(event) => setCrowdSpacing(event.target.value)}
              className="h-8 w-full rounded border border-white/[0.08] bg-[#1b1b1b] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
            />
          </label>
          <div className="mt-3 flex justify-end gap-1.5">
            <button
              type="button"
              data-director-crowd-action="cancel"
              onClick={() => setCrowdPanelOpen(false)}
              className="h-8 rounded px-3 text-[11px] text-[#888] hover:bg-white/[0.06] hover:text-white"
            >
              取消
            </button>
            <button
              type="button"
              data-director-crowd-action="add"
              onClick={addCrowd}
              className="h-8 rounded bg-[#e7e7e7] px-3 text-[11px] text-[#202020] hover:bg-white"
            >
              添加
            </button>
          </div>
        </div>
      ) : null}

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

      <div
        data-director-viewport-toolbar
        className="absolute bottom-5 left-1/2 z-10 flex h-11 max-w-[calc(100%-24px)] -translate-x-1/2 items-center gap-1 overflow-x-auto rounded-md border border-white/10 bg-[#222]/95 px-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.34)]"
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
          data-director-panels-toggle
          aria-label={viewportPanelsCollapsed ? "恢复侧栏" : "全屏"}
          title={viewportPanelsCollapsed ? "恢复侧栏" : "全屏"}
          aria-pressed={viewportPanelsCollapsed}
          onClick={toggleViewportPanelsCollapsed}
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
            viewportPanelsCollapsed && "bg-white/10 text-[#5ddcff]",
          )}
        >
          {viewportPanelsCollapsed ? <Minimize2 size={15} /> : <Expand size={15} />}
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
            setCrowdPanelOpen(false);
            setPhoneVcamOpen((value) => !value);
          }}
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
            phoneVcamOpen && "bg-white/10 text-[#5ddcff]",
            phoneVcamRecording && "text-[#ed7a7d]",
          )}
        >
          <Smartphone size={15} />
        </button>
        <button
          type="button"
          data-director-crowd-trigger
          aria-label="添加群众阵列"
          title="添加群众阵列"
          aria-expanded={crowdPanelOpen}
          onClick={() => {
            setModelLibraryOpen(false);
            setPhoneVcamOpen(false);
            setCrowdPanelOpen((value) => !value);
          }}
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
            crowdPanelOpen && "bg-white/10 text-[#5ddcff]",
          )}
        >
          <Users size={15} />
        </button>
        <button
          ref={modelLibraryTriggerRef}
          type="button"
          data-director-model-library-trigger
          aria-label="模型库"
          title="模型库"
          aria-expanded={modelLibraryOpen}
          onClick={toggleModelLibrary}
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#8d8d8d] hover:text-white",
            modelLibraryOpen && "bg-white/10 text-[#5ddcff]",
          )}
        >
          <Boxes size={15} />
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
