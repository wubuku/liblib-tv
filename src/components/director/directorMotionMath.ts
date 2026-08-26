import type {
  DirectorMotionPath,
  DirectorMotionPathAnchor,
  DirectorMotionPathAnchorType,
  DirectorSpeedCurve,
  DirectorSpeedCurvePreset,
  DirectorTimelineTrack,
  DirectorTransform,
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

function subtractTuple(
  left: DirectorTuple3,
  right: DirectorTuple3,
): DirectorTuple3 {
  return [
    left[0] - right[0],
    left[1] - right[1],
    left[2] - right[2],
  ];
}

function scaleTuple(tuple: DirectorTuple3, scale: number): DirectorTuple3 {
  return [tuple[0] * scale, tuple[1] * scale, tuple[2] * scale];
}

function rotateTupleX(tuple: DirectorTuple3, radians: number): DirectorTuple3 {
  const cosine = Math.cos(radians);
  const sine = Math.sin(radians);
  return [
    tuple[0],
    tuple[1] * cosine - tuple[2] * sine,
    tuple[1] * sine + tuple[2] * cosine,
  ];
}

function rotateTupleY(tuple: DirectorTuple3, radians: number): DirectorTuple3 {
  const cosine = Math.cos(radians);
  const sine = Math.sin(radians);
  return [
    tuple[0] * cosine + tuple[2] * sine,
    tuple[1],
    -tuple[0] * sine + tuple[2] * cosine,
  ];
}

function rotateTupleZ(tuple: DirectorTuple3, radians: number): DirectorTuple3 {
  const cosine = Math.cos(radians);
  const sine = Math.sin(radians);
  return [
    tuple[0] * cosine - tuple[1] * sine,
    tuple[0] * sine + tuple[1] * cosine,
    tuple[2],
  ];
}

function degreesToRadians(value: number): number {
  return (value * Math.PI) / 180;
}

function safeScale(value: number): number {
  return Number.isFinite(value) && Math.abs(value) > 0.000001 ? value : 1;
}

function hasHandle(tuple: DirectorTuple3): boolean {
  return Math.hypot(tuple[0], tuple[1], tuple[2]) > 0.000001;
}

function cubicBezierPoint(
  from: DirectorTuple3,
  control1: DirectorTuple3,
  control2: DirectorTuple3,
  to: DirectorTuple3,
  progress: number,
): DirectorTuple3 {
  const inverse = 1 - progress;
  const fromWeight = inverse * inverse * inverse;
  const control1Weight = 3 * inverse * inverse * progress;
  const control2Weight = 3 * inverse * progress * progress;
  const toWeight = progress * progress * progress;
  return [
    from[0] * fromWeight +
      control1[0] * control1Weight +
      control2[0] * control2Weight +
      to[0] * toWeight,
    from[1] * fromWeight +
      control1[1] * control1Weight +
      control2[1] * control2Weight +
      to[1] * toWeight,
    from[2] * fromWeight +
      control1[2] * control1Weight +
      control2[2] * control2Weight +
      to[2] * toWeight,
  ];
}

export function createDirectorMotionPathAnchor(
  id: string,
  position: DirectorTuple3,
  type: DirectorMotionPathAnchorType = "vertex",
): DirectorMotionPathAnchor {
  return {
    id,
    position: [...position],
    type,
    handleIn: [0, 0, 0],
    handleOut: [0, 0, 0],
  };
}

export function cloneDirectorMotionPathAnchors(
  anchors: DirectorMotionPathAnchor[],
): DirectorMotionPathAnchor[] {
  return anchors.map((anchor) => ({
    ...anchor,
    position: [...anchor.position],
    handleIn: [...anchor.handleIn],
    handleOut: [...anchor.handleOut],
  }));
}

export function createDirectorMotionPathTransform(): DirectorTransform {
  return {
    position: [0, 0, 0],
    rotation: [0, 0, 0],
    scale: [1, 1, 1],
  };
}

export function getDirectorMotionPathPivot(
  anchors: DirectorMotionPathAnchor[],
): DirectorTuple3 {
  if (anchors.length === 0) return [0, 0, 0];
  const total = anchors.reduce<DirectorTuple3>(
    (sum, anchor) => [
      sum[0] + anchor.position[0],
      sum[1] + anchor.position[1],
      sum[2] + anchor.position[2],
    ],
    [0, 0, 0],
  );
  return [
    total[0] / anchors.length,
    total[1] / anchors.length,
    total[2] / anchors.length,
  ];
}

export function transformDirectorMotionPathVector(
  vector: DirectorTuple3,
  transform: DirectorTransform,
): DirectorTuple3 {
  let result: DirectorTuple3 = [
    vector[0] * safeScale(transform.scale[0]),
    vector[1] * safeScale(transform.scale[1]),
    vector[2] * safeScale(transform.scale[2]),
  ];
  result = rotateTupleX(result, degreesToRadians(transform.rotation[0]));
  result = rotateTupleY(result, degreesToRadians(transform.rotation[1]));
  return rotateTupleZ(result, degreesToRadians(transform.rotation[2]));
}

export function inverseTransformDirectorMotionPathVector(
  vector: DirectorTuple3,
  transform: DirectorTransform,
): DirectorTuple3 {
  let result = rotateTupleZ(
    vector,
    -degreesToRadians(transform.rotation[2]),
  );
  result = rotateTupleY(
    result,
    -degreesToRadians(transform.rotation[1]),
  );
  result = rotateTupleX(
    result,
    -degreesToRadians(transform.rotation[0]),
  );
  return [
    result[0] / safeScale(transform.scale[0]),
    result[1] / safeScale(transform.scale[1]),
    result[2] / safeScale(transform.scale[2]),
  ];
}

export function transformDirectorMotionPathPoint(
  point: DirectorTuple3,
  pivot: DirectorTuple3,
  transform: DirectorTransform,
): DirectorTuple3 {
  const offset = transformDirectorMotionPathVector(
    subtractTuple(point, pivot),
    transform,
  );
  return addTuple(
    addTuple(pivot, transform.position),
    offset,
  );
}

export function inverseTransformDirectorMotionPathPoint(
  point: DirectorTuple3,
  pivot: DirectorTuple3,
  transform: DirectorTransform,
): DirectorTuple3 {
  const translated = subtractTuple(
    point,
    addTuple(pivot, transform.position),
  );
  return addTuple(
    pivot,
    inverseTransformDirectorMotionPathVector(translated, transform),
  );
}

export function buildDirectorMotionPathWorldAnchors(
  anchors: DirectorMotionPathAnchor[],
  pivot: DirectorTuple3,
  transform: DirectorTransform,
): DirectorMotionPathAnchor[] {
  return anchors.map((anchor) => ({
    ...anchor,
    position: transformDirectorMotionPathPoint(
      anchor.position,
      pivot,
      transform,
    ),
    handleIn: transformDirectorMotionPathVector(
      anchor.handleIn,
      transform,
    ),
    handleOut: transformDirectorMotionPathVector(
      anchor.handleOut,
      transform,
    ),
  }));
}

export function buildDirectorMotionPathPoints(
  anchors: DirectorMotionPathAnchor[],
  closed: boolean,
  subdivisions = 12,
): DirectorTuple3[] {
  if (anchors.length === 0) return [];
  if (anchors.length === 1) return [[...anchors[0].position]];

  const points: DirectorTuple3[] = [[...anchors[0].position]];
  const segmentCount = closed ? anchors.length : anchors.length - 1;
  const steps = Math.max(2, Math.round(subdivisions));

  for (let index = 0; index < segmentCount; index += 1) {
    const from = anchors[index];
    const to = anchors[(index + 1) % anchors.length];
    const isClosingSegment = closed && index === segmentCount - 1;
    if (!hasHandle(from.handleOut) && !hasHandle(to.handleIn)) {
      if (!isClosingSegment) points.push([...to.position]);
      continue;
    }

    const control1 = addTuple(from.position, from.handleOut);
    const control2 = addTuple(to.position, to.handleIn);
    for (let step = 1; step <= steps; step += 1) {
      if (isClosingSegment && step === steps) continue;
      points.push(
        cubicBezierPoint(
          from.position,
          control1,
          control2,
          to.position,
          step / steps,
        ),
      );
    }
  }

  return points;
}

function defaultAnchorHandles(
  anchors: DirectorMotionPathAnchor[],
  index: number,
  closed: boolean,
): { handleIn: DirectorTuple3; handleOut: DirectorTuple3 } {
  const anchor = anchors[index];
  const previous =
    anchors[index - 1] ?? (closed ? anchors[anchors.length - 1] : anchor);
  const next =
    anchors[index + 1] ?? (closed ? anchors[0] : anchor);
  const direction = normalizeTuple(
    subtractTuple(next.position, previous.position),
  );
  const previousDistance = tupleDistance(anchor.position, previous.position);
  const nextDistance = tupleDistance(anchor.position, next.position);
  const availableDistances = [previousDistance, nextDistance].filter(
    (distance) => distance > 0.000001,
  );
  const handleLength =
    (availableDistances.length > 0
      ? Math.min(...availableDistances)
      : 1) * 0.28;
  const handleOut = scaleTuple(direction, handleLength);
  return {
    handleIn: scaleTuple(handleOut, -1),
    handleOut,
  };
}

export function setDirectorMotionPathAnchorType(
  anchors: DirectorMotionPathAnchor[],
  anchorId: string,
  type: DirectorMotionPathAnchorType,
  closed: boolean,
): DirectorMotionPathAnchor[] {
  const index = anchors.findIndex((anchor) => anchor.id === anchorId);
  if (index < 0) return anchors;
  const current = anchors[index];
  let handleIn: DirectorTuple3 = [...current.handleIn];
  let handleOut: DirectorTuple3 = [...current.handleOut];

  if (type === "vertex") {
    handleIn = [0, 0, 0];
    handleOut = [0, 0, 0];
  } else if (!hasHandle(handleIn) && !hasHandle(handleOut)) {
    ({ handleIn, handleOut } = defaultAnchorHandles(anchors, index, closed));
  } else if (type === "symmetric") {
    const source = hasHandle(handleOut)
      ? handleOut
      : scaleTuple(handleIn, -1);
    handleOut = [...source];
    handleIn = scaleTuple(source, -1);
  }

  return anchors.map((anchor) =>
    anchor.id === anchorId
      ? { ...anchor, type, handleIn, handleOut }
      : anchor,
  );
}

export function isDirectorMotionPathValid(
  anchors: DirectorMotionPathAnchor[],
): boolean {
  if (anchors.length < 2) return false;
  const first = anchors[0].position;
  return anchors.some(
    (anchor) => tupleDistance(first, anchor.position) > 0.0001,
  );
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
