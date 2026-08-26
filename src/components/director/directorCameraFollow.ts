export type DirectorCameraTuple3 = [number, number, number];
export type DirectorCameraLookAtMode = "coordinate" | "rotation" | "object";
export type DirectorCameraFollowView = "third-person" | "first-person";

export interface DirectorCameraRelation {
  lookAtMode: DirectorCameraLookAtMode;
  lookAtObjectId: string | null;
  followTargetId: string | null;
  followOffset: DirectorCameraTuple3;
  followView: DirectorCameraFollowView;
}

export interface DirectorCameraTargetObject {
  id: string;
  kind: "character" | "prop" | "camera";
  primitive:
    | "character"
    | "table"
    | "mug"
    | "wall"
    | "camera"
    | "library";
  transform: {
    position: DirectorCameraTuple3;
    rotation: DirectorCameraTuple3;
    scale: DirectorCameraTuple3;
  };
}

export interface DirectorCameraResolution {
  position: DirectorCameraTuple3;
  target: DirectorCameraTuple3;
}

const DEG_TO_RAD = Math.PI / 180;

function finite(value: number, fallback: number): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.round(value * 1_000_000) / 1_000_000;
}

function finiteTuple(
  value: DirectorCameraTuple3,
  fallback: DirectorCameraTuple3,
): DirectorCameraTuple3 {
  return [
    finite(value[0], fallback[0]),
    finite(value[1], fallback[1]),
    finite(value[2], fallback[2]),
  ];
}

function rotateOffsetAroundY(
  offset: DirectorCameraTuple3,
  rotationY: number,
): DirectorCameraTuple3 {
  const radians = finite(rotationY, 0) * DEG_TO_RAD;
  const cosine = Math.cos(radians);
  const sine = Math.sin(radians);
  return finiteTuple(
    [
      offset[0] * cosine + offset[2] * sine,
      offset[1],
      -offset[0] * sine + offset[2] * cosine,
    ],
    offset,
  );
}

export function createDirectorCameraRelation(): DirectorCameraRelation {
  return {
    lookAtMode: "coordinate",
    lookAtObjectId: null,
    followTargetId: null,
    followOffset: [0, 1.2, 4.5],
    followView: "third-person",
  };
}

export function getDirectorCameraTargetFocus(
  object: DirectorCameraTargetObject,
): DirectorCameraTuple3 {
  const scaleY = Math.max(Math.abs(object.transform.scale[1]), 0.05);
  const focusHeight =
    object.primitive === "character"
      ? 1.48 * scaleY
      : object.primitive === "table"
        ? 0.94 * scaleY
        : object.primitive === "mug"
          ? 0.12 * scaleY
          : object.primitive === "library"
            ? 0.6 * scaleY
          : 0;
  return finiteTuple(
    [
      object.transform.position[0],
      object.transform.position[1] + focusHeight,
      object.transform.position[2],
    ],
    object.transform.position,
  );
}

export function resolveDirectorCameraRelation({
  position,
  target,
  relation,
  objects,
}: {
  position: DirectorCameraTuple3;
  target: DirectorCameraTuple3;
  relation: DirectorCameraRelation;
  objects: DirectorCameraTargetObject[];
}): DirectorCameraResolution {
  let resolvedPosition = finiteTuple(position, [0, 0, 0]);
  let resolvedTarget = finiteTuple(target, [0, 0, -1]);

  if (relation.lookAtMode === "object" && relation.lookAtObjectId) {
    const lookAtObject = objects.find(
      (object) => object.id === relation.lookAtObjectId,
    );
    if (lookAtObject) {
      resolvedTarget = getDirectorCameraTargetFocus(lookAtObject);
    }
  }

  if (!relation.followTargetId) {
    return { position: resolvedPosition, target: resolvedTarget };
  }

  const followTarget = objects.find(
    (object) => object.id === relation.followTargetId,
  );
  if (!followTarget) {
    return { position: resolvedPosition, target: resolvedTarget };
  }

  const focus = getDirectorCameraTargetFocus(followTarget);
  const offset = rotateOffsetAroundY(
    finiteTuple(relation.followOffset, [0, 1.2, 4.5]),
    followTarget.transform.rotation[1],
  );
  resolvedPosition = finiteTuple(
    [
      focus[0] + offset[0],
      focus[1] + offset[1],
      focus[2] + offset[2],
    ],
    position,
  );

  if (relation.followView === "first-person") {
    const yaw = finite(followTarget.transform.rotation[1], 0) * DEG_TO_RAD;
    const forwardDistance = 3;
    resolvedTarget = finiteTuple(
      [
        resolvedPosition[0] + Math.sin(yaw) * forwardDistance,
        resolvedPosition[1],
        resolvedPosition[2] - Math.cos(yaw) * forwardDistance,
      ],
      target,
    );
  } else {
    resolvedTarget = focus;
  }

  return { position: resolvedPosition, target: resolvedTarget };
}
