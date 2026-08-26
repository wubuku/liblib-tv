import type {
  DirectorCameraKeyframeValue,
  DirectorTuple3,
} from "@/store/directorStore";

export interface DirectorPhoneVcamPose {
  yaw: number;
  pitch: number;
  roll: number;
}

export interface DirectorPhoneOrientation {
  alpha: number;
  beta: number;
  gamma: number;
}

const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(Number.isFinite(value) ? value : 0, minimum), maximum);
}

function cloneTuple(tuple: DirectorTuple3): DirectorTuple3 {
  return [...tuple];
}

function shortestAngleDelta(current: number, origin: number): number {
  return ((current - origin + 540) % 360) - 180;
}

function lerpTuple(
  from: DirectorTuple3,
  to: DirectorTuple3,
  amount: number,
): DirectorTuple3 {
  return from.map(
    (value, index) => value + (to[index] - value) * amount,
  ) as DirectorTuple3;
}

export function normalizeDirectorPhoneOrientation(
  orientation: DirectorPhoneOrientation,
  origin: DirectorPhoneOrientation,
): DirectorPhoneVcamPose {
  return {
    yaw: clamp(shortestAngleDelta(orientation.alpha, origin.alpha), -90, 90),
    pitch: clamp(orientation.beta - origin.beta, -60, 60),
    roll: clamp(orientation.gamma - origin.gamma, -45, 45),
  };
}

export function mapDirectorPhonePoseToCamera({
  baseline,
  previous,
  pose,
  stability,
  keepLevel,
  elevation,
}: {
  baseline: DirectorCameraKeyframeValue;
  previous: DirectorCameraKeyframeValue;
  pose: DirectorPhoneVcamPose;
  stability: number;
  keepLevel: boolean;
  elevation: number;
}): DirectorCameraKeyframeValue {
  const basePosition = baseline.transform.position;
  const baseTarget = baseline.target;
  const offsetX = basePosition[0] - baseTarget[0];
  const offsetY = basePosition[1] - baseTarget[1];
  const offsetZ = basePosition[2] - baseTarget[2];
  const radius = Math.max(Math.hypot(offsetX, offsetY, offsetZ), 0.1);
  const horizontalRadius = Math.max(Math.hypot(offsetX, offsetZ), 0.001);
  const baseYaw = Math.atan2(offsetX, offsetZ);
  const basePitch = Math.atan2(offsetY, horizontalRadius);
  const yaw = baseYaw + clamp(pose.yaw, -90, 90) * 0.72 * DEG_TO_RAD;
  const pitch = clamp(
    basePitch + clamp(pose.pitch, -60, 60) * 0.42 * DEG_TO_RAD,
    -72 * DEG_TO_RAD,
    72 * DEG_TO_RAD,
  );
  const target: DirectorTuple3 = [
    baseTarget[0],
    baseTarget[1] + clamp(elevation, -4, 4),
    baseTarget[2],
  ];
  const targetPosition: DirectorTuple3 = [
    target[0] + Math.sin(yaw) * Math.cos(pitch) * radius,
    target[1] + Math.sin(pitch) * radius,
    target[2] + Math.cos(yaw) * Math.cos(pitch) * radius,
  ];
  const targetRotation: DirectorTuple3 = [
    clamp(pose.pitch, -60, 60),
    yaw * RAD_TO_DEG,
    keepLevel ? 0 : clamp(pose.roll, -45, 45),
  ];
  const smoothing = clamp(stability, 0, 100) / 100;
  const response = 1 - smoothing * 0.82;

  return {
    transform: {
      position: lerpTuple(
        previous.transform.position,
        targetPosition,
        response,
      ),
      rotation: lerpTuple(
        previous.transform.rotation,
        targetRotation,
        response,
      ),
      scale: cloneTuple(baseline.transform.scale),
    },
    target: lerpTuple(previous.target, target, response),
    fov: baseline.fov,
  };
}

export function isFiniteDirectorCameraValue(
  value: DirectorCameraKeyframeValue,
): boolean {
  return [
    ...value.transform.position,
    ...value.transform.rotation,
    ...value.transform.scale,
    ...value.target,
    value.fov,
  ].every(Number.isFinite);
}
