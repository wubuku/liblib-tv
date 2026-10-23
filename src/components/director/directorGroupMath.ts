import type {
  DirectorCharacterGroup,
  DirectorObject,
  DirectorObjectKind,
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

/**
 * ★★ Batch 855：组成员引用（`{kind, id}`）。
 *
 * ★ 源站逐字（chunk `0fmehki05gkzw.js.js`，机器提取见
 *   `docs/research/liblib-canvas-batch855-2026-10-01/raw/source-855-contract.json`）：
 *   `function N(e){return`${e.kind}:${e.id}`}` —— 成员的键是 **`kind:id`**。
 */
export interface DirectorGroupMemberRef {
  kind: DirectorObjectKind;
  id: string;
}

/**
 * ★★ Batch 855：取一个组的**权威成员列表**（运行时层的**唯一**实现）。
 *
 * ★ 逐字对齐源站 `function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);
 *   r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),
 *   (e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}`：
 * ★ **`members` 优先、`characterIds` 兜底**（老组／群众组只有 `characterIds`），
 * ★ 并按源站的 `N(e)`＝`kind:id` 去重。
 *
 * ★ ★ **本函数是运行时层（store ＋ 组数学）的唯一来源** —— 854 之后
 *   `src/store/directorStore.ts` 的 `resolveGroupMemberRefs` 直接转出本函数，
 *   避免同一份「权威列表」规则在仓库里出现第二份实现。
 * ★ （`src/lib/directorProjectDocument.ts` 里的 `resolveDirectorGroupMembers`
 *   是**故意保留的独立实现** —— 那是文档层的第二套实现，用来交叉验证。）
 */
export function resolveDirectorGroupMemberRefs(group: {
  characterIds: string[];
  members?: DirectorGroupMemberRef[] | null;
}): DirectorGroupMemberRef[] {
  const out: DirectorGroupMemberRef[] = [];
  const seen = new Set<string>();
  const push = (kind: DirectorObjectKind, id: string) => {
    if (!id) return;
    const key = `${kind}:${id}`;
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ kind, id });
  };
  (group.members ?? []).forEach((member) => push(member.kind, member.id));
  group.characterIds.forEach((id) => push("character", id));
  return out;
}

/**
 * ★★ Batch 855：组 rig **会驱动**的成员类别。
 *
 * ★ 源站逐字（组轨道 rig 的应用块 `A.forEach`）：分支只有
 *   `"character"===o` ／ `"prop"===o` ／ `"emptyObject"===o`
 *   —— **没有 `"camera"===o` 分支**。
 * ⟹ ⟹ **机位入组后不会被组轨道带动**（机位在源站靠 `followTargetId` 跟组锚点）。
 * ⟹ ⟹ clone 没有 emptyObject ⟹ ⟹ 落点只有 character ＋ prop。
 *
 * ★ 登记表见 `docs/research/liblib-canvas-batch855-2026-10-01/README.md`
 *   的「差异登记 D2」：解析器认 camera、但应用块没有 camera 分支 ⟹ 疑似源站漏分支，
 *   本批**按源站逐字复刻**（机位不动），并把「源站是否有意如此」登记为待查。
 */
export const DIRECTOR_GROUP_RIG_DRIVEN_KINDS: readonly DirectorObjectKind[] = [
  "character",
  "prop",
];

/**
 * ★★ Batch 855：取一个组的**全部成员对象**（任意类别，源站 `O(e)` 的顺序）。
 *
 * ★★ Batch 854 之前这里是 `object.kind === "character" && memberIds.has(object.id)`
 *   ⟹ ⟹ **只认角色** ⟹ ⟹ 机位入组后**锚点／成员偏移／整体变换全都漏掉机位**。
 * ★ ★ 源站逐字 `H(e,t)`／`V(e,t,r)` 都遍历 `O(e)`（权威成员列表，任意类别）⟹ ⟹ 本批对齐。
 */
export function getDirectorGroupMembers(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
): DirectorObject[] {
  const byKey = new Map(
    objects.map((object) => [`${object.kind}:${object.id}`, object]),
  );
  const out: DirectorObject[] = [];
  resolveDirectorGroupMemberRefs(group).forEach((member) => {
    const object = byKey.get(`${member.kind}:${member.id}`);
    if (object) out.push(object);
  });
  return out;
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
  // ★★ Batch 855：成员集合从「只认角色」改成「**全部非机位成员**」
  //   （源站 rig 的应用分支只有 character／prop／emptyObject ⟹ 机位不在内）。
  const memberIds = new Set(
    resolveDirectorGroupMemberRefs(group)
      .filter((member) => DIRECTOR_GROUP_RIG_DRIVEN_KINDS.includes(member.kind))
      .map((member) => member.id),
  );
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
    if (!memberIds.has(object.id)) {
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

/**
 * ★★ Batch 855：**组轨道（groupTracks）rig** —— 按源站逐字实现。
 *
 * ## ★ 源站逐字依据
 *
 * ```js
 * // 组轨道 rig：memberOffsets 缺失时现算 ＋ 遍历 O(r) ＝ 全部成员
 * let i=t.memberOffsets??V(r,a,f);
 * O(r).forEach(t=>{let r=i[N(t)];
 *   r&&A.set(N(t),{position:{x:e.position.x+r.x,y:e.position.y+r.y,z:e.position.z+r.z},
 *                  yaw:n?.orientToPath?e.rotation.y:void 0,moving:v.has(e.id)})});
 *
 * // 应用块：分支只有 character ／ prop ／ emptyObject ——**没有 camera**
 * A.forEach((e,t)=>{ … if("character"===o){…} if("prop"===o){…} if("emptyObject"===o){…} });
 * ```
 *
 * ## ★★ 三个语义要点
 *
 * 1. **成员位置 ＝ 组的采样位置 ＋ 成员偏移** ⟹ ⟹ **纯平移**：
 *    偏移向量**不参与旋转／缩放**，成员的 rotation／scale **保持自己的**。
 * 2. **机位不动**：应用块没有 `"camera"===o` 分支 ⟹ ⟹ 机位入组后不会被组轨道带动。
 * 3. 成员的 `rotation.y` 只有在**路径 orientToPath** 时才被组的 yaw 覆盖
 *    ⟹ ⟹ clone 的组轨道**没有路径**（`createTrackForGroup` 不写 `motionPathId`）
 *    ⟹ ⟹ 该分支对 clone **不适用**，登记为「不适用」而非差异。
 *
 * ## ★ 与 `applyDirectorGroupTransform` 的分工
 *
 * - **本函数** ＝ 时间轴 rig（组轨道回放）⟹ ⟹ 源站逐字（纯平移）。
 * - `applyDirectorGroupTransform` ＝ **交互路径**（组检查器的变换输入）
 *   ⟹ ⟹ 源站的组**根本没有 transform 字段**（`{id,label,characterIds,members}`），
 *   交互路径的旋转／缩放语义**未取证** ⟹ ⟹ 本批**保持现状**并登记为独立批次。
 */
export function applyDirectorGroupRig(
  objects: DirectorObject[],
  group: DirectorCharacterGroup,
  sampledTransform: DirectorTransform,
  memberOffsets: Record<string, DirectorTuple3>,
): DirectorObject[] {
  const drivenIds = new Set(
    resolveDirectorGroupMemberRefs(group)
      .filter((member) => DIRECTOR_GROUP_RIG_DRIVEN_KINDS.includes(member.kind))
      .map((member) => member.id),
  );
  return objects.map((object) => {
    if (!drivenIds.has(object.id)) return object;
    const offset = memberOffsets[object.id];
    if (!offset) return object;
    return {
      ...object,
      transform: {
        ...object.transform,
        // ★ 源站逐字：`position:{x:e.position.x+r.x, y:e.position.y+r.y, z:e.position.z+r.z}`
        position: roundTuple([
          sampledTransform.position[0] + offset[0],
          sampledTransform.position[1] + offset[1],
          sampledTransform.position[2] + offset[2],
        ]),
        // ★ 源站逐字：成员保留**自己的** rotation／scale
        //   （`rotation:void 0===e.yaw?t.rotation:{...t.rotation,y:e.yaw}` ／ `scale:r.scale`）
        rotation: [...object.transform.rotation],
        scale: [...object.transform.scale],
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
