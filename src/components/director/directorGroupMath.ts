import type {
  DirectorCharacterGroup,
  DirectorObject,
  DirectorTransform,
  DirectorTuple3,
} from "@/store/directorStore";

function roundTuple(tuple: DirectorTuple3): DirectorTuple3 {
  return tuple.map((value) => Number(value.toFixed(3))) as DirectorTuple3;
}

function rotateTuple(
  tuple: DirectorTuple3,
  rotationDegrees: DirectorTuple3,
): DirectorTuple3 {
  const rotation = rotationDegrees.map(
    (value) => (value * Math.PI) / 180,
  ) as DirectorTuple3;
  const cosX = Math.cos(rotation[0]);
  const sinX = Math.sin(rotation[0]);
  const cosY = Math.cos(rotation[1]);
  const sinY = Math.sin(rotation[1]);
  const cosZ = Math.cos(rotation[2]);
  const sinZ = Math.sin(rotation[2]);

  const x1 = tuple[0];
  const y1 = tuple[1] * cosX - tuple[2] * sinX;
  const z1 = tuple[1] * sinX + tuple[2] * cosX;
  const x2 = x1 * cosY + z1 * sinY;
  const y2 = y1;
  const z2 = -x1 * sinY + z1 * cosY;

  return [
    x2 * cosZ - y2 * sinZ,
    x2 * sinZ + y2 * cosZ,
    z2,
  ];
}

export function getDirectorGroupMembers(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
): DirectorObject[] {
  const memberIds = new Set(group.characterIds);
  return objects.filter(
    (object) => object.kind === "character" && memberIds.has(object.id),
  );
}

export function getDirectorGroupAnchorTransform(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
): DirectorTransform | null {
  const members = getDirectorGroupMembers(objects, group);
  if (members.length === 0) return null;
  const position = members.reduce<DirectorTuple3>(
    (sum, member) => [
      sum[0] + member.transform.position[0],
      sum[1] + member.transform.position[1],
      sum[2] + member.transform.position[2],
    ],
    [0, 0, 0],
  );
  const reference = members[0].transform;
  return {
    position: roundTuple([
      position[0] / members.length,
      position[1] / members.length,
      position[2] / members.length,
    ]),
    rotation: [...reference.rotation],
    scale: [...reference.scale],
  };
}

export function getDirectorGroupMemberOffsets(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
): Record<string, DirectorTuple3> {
  const anchor = getDirectorGroupAnchorTransform(objects, group);
  if (!anchor) return {};
  return Object.fromEntries(
    getDirectorGroupMembers(objects, group).map((member) => [
      member.id,
      roundTuple([
        member.transform.position[0] - anchor.position[0],
        member.transform.position[1] - anchor.position[1],
        member.transform.position[2] - anchor.position[2],
      ]),
    ]),
  );
}

export function applyDirectorGroupTransform(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
  nextTransform: DirectorTransform,
): DirectorObject[] {
  const anchor = getDirectorGroupAnchorTransform(objects, group);
  if (!anchor) return objects;
  const memberIds = new Set(group.characterIds);
  const rotationDelta: DirectorTuple3 = [
    nextTransform.rotation[0] - anchor.rotation[0],
    nextTransform.rotation[1] - anchor.rotation[1],
    nextTransform.rotation[2] - anchor.rotation[2],
  ];
  const scaleRatio: DirectorTuple3 = [
    Math.abs(anchor.scale[0]) < Number.EPSILON
      ? 1
      : nextTransform.scale[0] / anchor.scale[0],
    Math.abs(anchor.scale[1]) < Number.EPSILON
      ? 1
      : nextTransform.scale[1] / anchor.scale[1],
    Math.abs(anchor.scale[2]) < Number.EPSILON
      ? 1
      : nextTransform.scale[2] / anchor.scale[2],
  ];

  return objects.map((object) => {
    if (!memberIds.has(object.id) || object.kind !== "character") {
      return object;
    }
    const scaledOffset: DirectorTuple3 = [
      (object.transform.position[0] - anchor.position[0]) * scaleRatio[0],
      (object.transform.position[1] - anchor.position[1]) * scaleRatio[1],
      (object.transform.position[2] - anchor.position[2]) * scaleRatio[2],
    ];
    const rotatedOffset = rotateTuple(scaledOffset, rotationDelta);
    return {
      ...object,
      transform: {
        position: roundTuple([
          nextTransform.position[0] + rotatedOffset[0],
          nextTransform.position[1] + rotatedOffset[1],
          nextTransform.position[2] + rotatedOffset[2],
        ]),
        rotation: roundTuple([
          object.transform.rotation[0] + rotationDelta[0],
          object.transform.rotation[1] + rotationDelta[1],
          object.transform.rotation[2] + rotationDelta[2],
        ]),
        scale: roundTuple([
          object.transform.scale[0] * scaleRatio[0],
          object.transform.scale[1] * scaleRatio[1],
          object.transform.scale[2] * scaleRatio[2],
        ]),
      },
    };
  });
}

export function createDirectorCrowdPositions(
  rows: number,
  columns: number,
  spacing: number,
  origin: DirectorTuple3,
): DirectorTuple3[] {
  const safeRows = Math.max(1, Math.round(rows));
  const safeColumns = Math.max(1, Math.round(columns));
  const safeSpacing = Math.max(0.1, spacing);
  const xOffset = ((safeColumns - 1) * safeSpacing) / 2;
  const zOffset = ((safeRows - 1) * safeSpacing) / 2;
  const positions: DirectorTuple3[] = [];

  for (let row = 0; row < safeRows; row += 1) {
    for (let column = 0; column < safeColumns; column += 1) {
      positions.push(
        roundTuple([
          origin[0] + column * safeSpacing - xOffset,
          origin[1],
          origin[2] + row * safeSpacing - zOffset,
        ]),
      );
    }
  }

  return positions;
}
