export type DirectorCameraPresetTuple3 = [number, number, number];

export type DirectorCameraMotionPresetId =
  | "orbit"
  | "half-arc"
  | "push-in"
  | "pull-out"
  | "pedestal-up"
  | "truck-right"
  | "spiral-up";

export type DirectorCameraMotionPresetMode = "replace" | "append";

export interface DirectorCameraPresetValue {
  transform: {
    position: DirectorCameraPresetTuple3;
    rotation: DirectorCameraPresetTuple3;
    scale: DirectorCameraPresetTuple3;
  };
  target: DirectorCameraPresetTuple3;
  fov: number;
}

export const DIRECTOR_CAMERA_MOTION_PRESETS: ReadonlyArray<{
  id: DirectorCameraMotionPresetId;
  label: string;
}> = [
  { id: "orbit", label: "环绕" },
  { id: "half-arc", label: "半弧" },
  { id: "push-in", label: "推近" },
  { id: "pull-out", label: "拉远" },
  { id: "pedestal-up", label: "升降" },
  { id: "truck-right", label: "横移" },
  { id: "spiral-up", label: "螺旋上升" },
];

function finite(value: number, fallback: number): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.round(value * 1_000_000) / 1_000_000;
}

function tuple(
  values: DirectorCameraPresetTuple3,
  fallback: DirectorCameraPresetTuple3,
): DirectorCameraPresetTuple3 {
  return [
    finite(values[0], fallback[0]),
    finite(values[1], fallback[1]),
    finite(values[2], fallback[2]),
  ];
}

function cloneValue(value: DirectorCameraPresetValue): DirectorCameraPresetValue {
  return {
    transform: {
      position: [...value.transform.position],
      rotation: [...value.transform.rotation],
      scale: [...value.transform.scale],
    },
    target: [...value.target],
    fov: finite(value.fov, 45),
  };
}

function interpolateTuple(
  from: DirectorCameraPresetTuple3,
  to: DirectorCameraPresetTuple3,
  progress: number,
): DirectorCameraPresetTuple3 {
  return tuple(
    [
      from[0] + (to[0] - from[0]) * progress,
      from[1] + (to[1] - from[1]) * progress,
      from[2] + (to[2] - from[2]) * progress,
    ],
    from,
  );
}

function createSamples(
  count: number,
  createValue: (progress: number) => DirectorCameraPresetValue,
): DirectorCameraPresetValue[] {
  return Array.from({ length: count }, (_, index) =>
    createValue(index / Math.max(count - 1, 1)),
  );
}

export function createDirectorCameraMotionPresetValues(
  preset: DirectorCameraMotionPresetId,
  startValue: DirectorCameraPresetValue,
): DirectorCameraPresetValue[] {
  const start = cloneValue(startValue);
  const position = start.transform.position;
  const target = start.target;
  const offset: DirectorCameraPresetTuple3 = [
    position[0] - target[0],
    position[1] - target[1],
    position[2] - target[2],
  ];
  const horizontalRadius = Math.max(Math.hypot(offset[0], offset[2]), 0.1);
  const startAngle = Math.atan2(offset[0], offset[2]);

  const withPosition = (
    nextPosition: DirectorCameraPresetTuple3,
    nextTarget = target,
  ): DirectorCameraPresetValue => ({
    transform: {
      position: tuple(nextPosition, position),
      rotation: [...start.transform.rotation],
      scale: [...start.transform.scale],
    },
    target: tuple(nextTarget, target),
    fov: start.fov,
  });

  if (preset === "orbit" || preset === "half-arc" || preset === "spiral-up") {
    const count = preset === "half-arc" ? 7 : 9;
    const turn = preset === "half-arc" ? Math.PI : Math.PI * 2;
    return createSamples(count, (progress) => {
      const angle = startAngle + turn * progress;
      const rise = preset === "spiral-up" ? 2.6 * progress : 0;
      return withPosition([
        target[0] + Math.sin(angle) * horizontalRadius,
        target[1] + offset[1] + rise,
        target[2] + Math.cos(angle) * horizontalRadius,
      ]);
    });
  }

  if (preset === "push-in" || preset === "pull-out") {
    const finalScale = preset === "push-in" ? 0.45 : 1.65;
    return createSamples(3, (progress) => {
      const radiusScale = 1 + (finalScale - 1) * progress;
      return withPosition([
        target[0] + offset[0] * radiusScale,
        target[1] + offset[1] * radiusScale,
        target[2] + offset[2] * radiusScale,
      ]);
    });
  }

  if (preset === "pedestal-up") {
    return createSamples(3, (progress) =>
      withPosition([
        position[0],
        position[1] + 2.4 * progress,
        position[2],
      ]),
    );
  }

  const lookDirection: DirectorCameraPresetTuple3 = [
    target[0] - position[0],
    0,
    target[2] - position[2],
  ];
  const lookLength = Math.max(
    Math.hypot(lookDirection[0], lookDirection[2]),
    0.001,
  );
  const right: DirectorCameraPresetTuple3 = [
    -lookDirection[2] / lookLength,
    0,
    lookDirection[0] / lookLength,
  ];
  const translatedPosition: DirectorCameraPresetTuple3 = [
    position[0] + right[0] * 3,
    position[1],
    position[2] + right[2] * 3,
  ];
  const translatedTarget: DirectorCameraPresetTuple3 = [
    target[0] + right[0] * 3,
    target[1],
    target[2] + right[2] * 3,
  ];
  return createSamples(3, (progress) =>
    withPosition(
      interpolateTuple(position, translatedPosition, progress),
      interpolateTuple(target, translatedTarget, progress),
    ),
  );
}

export function isFiniteDirectorCameraPresetValue(
  value: DirectorCameraPresetValue,
): boolean {
  return [
    ...value.transform.position,
    ...value.transform.rotation,
    ...value.transform.scale,
    ...value.target,
    value.fov,
  ].every(Number.isFinite);
}
