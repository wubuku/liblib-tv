import type {
  DirectorMotionPath,
  DirectorSpeedCurve,
  DirectorSpeedCurvePreset,
  DirectorTimelineTrack,
  DirectorTuple3,
} from "@/store/directorStore";

export interface DirectorMotionPathSample {
  position: DirectorTuple3;
  tangent: DirectorTuple3;
}

const speedCurvePresets: Record<
  Exclude<DirectorSpeedCurvePreset, "custom">,
  { control1: [number, number]; control2: [number, number] }
> = {
  linear: { control1: [0, 0], control2: [1, 1] },
  smooth: { control1: [0.33, 0], control2: [0.67, 1] },
  "ease-in": { control1: [0.42, 0], control2: [1, 1] },
  "ease-out": { control1: [0, 0], control2: [0.58, 1] },
  "ease-in-out": { control1: [0.42, 0], control2: [0.58, 1] },
};

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(Math.max(value, 0), 1);
}

function cubicBezierCoordinate(
  progress: number,
  control1: number,
  control2: number,
): number {
  const inverse = 1 - progress;
  return (
    3 * inverse * inverse * progress * control1 +
    3 * inverse * progress * progress * control2 +
    progress * progress * progress
  );
}

function cubicBezierDerivative(
  progress: number,
  control1: number,
  control2: number,
): number {
  const inverse = 1 - progress;
  return (
    3 * inverse * inverse * control1 +
    6 * inverse * progress * (control2 - control1) +
    3 * progress * progress * (1 - control2)
  );
}

function solveBezierParameter(
  targetX: number,
  control1X: number,
  control2X: number,
): number {
  let parameter = clampUnit(targetX);
  for (let iteration = 0; iteration < 8; iteration += 1) {
    const x =
      cubicBezierCoordinate(parameter, control1X, control2X) - targetX;
    if (Math.abs(x) < 0.00001) return clampUnit(parameter);
    const derivative = cubicBezierDerivative(
      parameter,
      control1X,
      control2X,
    );
    if (Math.abs(derivative) < 0.000001) break;
    parameter -= x / derivative;
    if (parameter < 0 || parameter > 1) break;
  }

  let lower = 0;
  let upper = 1;
  parameter = targetX;
  for (let iteration = 0; iteration < 18; iteration += 1) {
    const x = cubicBezierCoordinate(parameter, control1X, control2X);
    if (Math.abs(x - targetX) < 0.00001) break;
    if (x < targetX) lower = parameter;
    else upper = parameter;
    parameter = (lower + upper) / 2;
  }
  return clampUnit(parameter);
}

function tupleDistance(from: DirectorTuple3, to: DirectorTuple3): number {
  return Math.hypot(to[0] - from[0], to[1] - from[1], to[2] - from[2]);
}

function normalizeTuple(tuple: DirectorTuple3): DirectorTuple3 {
  const length = Math.hypot(tuple[0], tuple[1], tuple[2]);
  if (length < 0.000001) return [0, 0, 1];
  return [tuple[0] / length, tuple[1] / length, tuple[2] / length];
}

export function createDirectorSpeedCurve(
  preset: Exclude<DirectorSpeedCurvePreset, "custom"> = "linear",
): DirectorSpeedCurve {
  const values = speedCurvePresets[preset];
  return {
    preset,
    control1: [...values.control1],
    control2: [...values.control2],
  };
}

export function remapDirectorSpeedProgress(
  progress: number,
  curve: DirectorSpeedCurve,
): number {
  const targetX = clampUnit(progress);
  if (
    curve.control1[0] === curve.control1[1] &&
    curve.control2[0] === curve.control2[1]
  ) {
    return targetX;
  }
  const parameter = solveBezierParameter(
    targetX,
    clampUnit(curve.control1[0]),
    clampUnit(curve.control2[0]),
  );
  return clampUnit(
    cubicBezierCoordinate(
      parameter,
      clampUnit(curve.control1[1]),
      clampUnit(curve.control2[1]),
    ),
  );
}

export function getDirectorTrackProgress(
  track: DirectorTimelineTrack,
  time: number,
): number {
  const first = track.keyframes[0];
  const last = track.keyframes[track.keyframes.length - 1];
  if (!first || !last || last.time - first.time < 0.000001) return 0;
  const progress = (time - first.time) / (last.time - first.time);
  return remapDirectorSpeedProgress(progress, track.speedCurve);
}

export function remapDirectorTrackTime(
  track: DirectorTimelineTrack,
  time: number,
): number {
  const first = track.keyframes[0];
  const last = track.keyframes[track.keyframes.length - 1];
  if (!first || !last || time <= first.time || time >= last.time) return time;
  return (
    first.time +
    getDirectorTrackProgress(track, time) * (last.time - first.time)
  );
}

export function sampleDirectorMotionPath(
  path: DirectorMotionPath,
  progress: number,
): DirectorMotionPathSample | null {
  if (path.points.length < 2) return null;
  const segments: Array<{
    from: DirectorTuple3;
    to: DirectorTuple3;
    length: number;
  }> = [];
  const segmentCount = path.closed ? path.points.length : path.points.length - 1;
  for (let index = 0; index < segmentCount; index += 1) {
    const from = path.points[index];
    const to = path.points[(index + 1) % path.points.length];
    const length = tupleDistance(from, to);
    if (length > 0.000001) segments.push({ from, to, length });
  }
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0);
  if (totalLength < 0.000001) return null;

  let remaining = clampUnit(progress) * totalLength;
  const fallback = segments[segments.length - 1];
  for (const segment of segments) {
    if (remaining <= segment.length) {
      const localProgress = remaining / segment.length;
      return {
        position: [
          segment.from[0] +
            (segment.to[0] - segment.from[0]) * localProgress,
          segment.from[1] +
            (segment.to[1] - segment.from[1]) * localProgress,
          segment.from[2] +
            (segment.to[2] - segment.from[2]) * localProgress,
        ],
        tangent: normalizeTuple([
          segment.to[0] - segment.from[0],
          segment.to[1] - segment.from[1],
          segment.to[2] - segment.from[2],
        ]),
      };
    }
    remaining -= segment.length;
  }

  return {
    position: [...fallback.to],
    tangent: normalizeTuple([
      fallback.to[0] - fallback.from[0],
      fallback.to[1] - fallback.from[1],
      fallback.to[2] - fallback.from[2],
    ]),
  };
}

export function getDirectorPathYaw(tangent: DirectorTuple3): number {
  return (Math.atan2(tangent[0], tangent[2]) * 180) / Math.PI;
}
