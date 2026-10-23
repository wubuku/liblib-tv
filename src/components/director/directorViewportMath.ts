import type {
  DirectorAspectRatio,
  DirectorTuple3,
} from "@/store/directorStore";

export interface DirectorFrameRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface DirectorViewportSnapshot {
  fov: number;
  position: DirectorTuple3;
  target: DirectorTuple3;
}

export type DirectorViewportAxisId =
  | "x-positive"
  | "x-negative"
  | "y-positive"
  | "y-negative"
  | "z-positive"
  | "z-negative";

export function getDirectorViewportAxis(
  axis: DirectorViewportAxisId,
): DirectorTuple3 {
  if (axis === "x-positive") return [1, 0, 0];
  if (axis === "x-negative") return [-1, 0, 0];
  if (axis === "y-positive") return [0, 1, 0];
  if (axis === "y-negative") return [0, -1, 0];
  if (axis === "z-positive") return [0, 0, 1];
  return [0, 0, -1];
}

export function getDirectorViewportAxisSnapshot(
  snapshot: DirectorViewportSnapshot,
  axis: DirectorViewportAxisId,
): DirectorViewportSnapshot {
  const direction = getDirectorViewportAxis(axis);
  const dx = snapshot.position[0] - snapshot.target[0];
  const dy = snapshot.position[1] - snapshot.target[1];
  const dz = snapshot.position[2] - snapshot.target[2];
  const radius = Math.max(Math.hypot(dx, dy, dz), 0.001);

  return {
    fov: snapshot.fov,
    target: [...snapshot.target],
    position: [
      snapshot.target[0] + direction[0] * radius,
      snapshot.target[1] + direction[1] * radius,
      snapshot.target[2] + direction[2] * radius,
    ],
  };
}

/**
 * Batch 851：导演台的**视图类快捷键**。
 *
 * ★ 这里的每一个常量与分支都**逐字取自源站**的 chunk（`0fmehki05gkzw.js.js`），
 *   不是从行为反推的：
 *
 * - 视角预设（源站 `iK`）：
 *   `iK=(0,o.useCallback)((e,t)=>{ … let o={top:{x:0,y:1,z:.001},bottom:{x:0,y:-1,z:.001},
 *   front:{x:0,y:0,z:1},back:{x:0,y:0,z:-1},right:{x:1,y:0,z:0},left:{x:-1,y:0,z:0},
 *   default:C.y}[e], s=Math.hypot(o.x,o.y,o.z)||1; return{target:n,
 *   position:{x:n.x+o.x/s*i,y:n.y+o.y/s*i,z:n.z+o.z/s*i}}}, …)`
 *   ⟹ ⟹ **只改方向、不改视距**：距离 `i` 取当前 `|position − target|`。
 *   ⟹ ⟹ `top` 的 z 分量是 **0.001**（不是 0）⟹ ⟹ 避免 lookAt 退化。
 *
 * - 平移（源站 `oi` 的每帧回调 + `oo` 的登记 + keyup 的删除）：
 *   `hX=new Set(["w","a","s","d","q","e"])`；
 *   keydown：`if(hX.has(r)&&!(e.ctrlKey||e.metaKey)){e.preventDefault(),oo(r,e);return}`
 *   `oo` **只把键登记进 Set**；真正的位移在 rAF 回调里按「Set 里仍存在的键」算；
 *   keyup：`hX.has(t)&&(nK.current.delete(t), …)` ⟹ ⟹ **必须按住**，单击无效。
 *   每帧：`w→+forward, s→−forward, d→+right, a→−right, e→+up, q→−up`，
 *   `right = forward × up`（长度² < 1e-6 时兜底为 `(1,0,0)`），
 *   步长 `1.2 × max(|camera.position − controls.target|, 0.5) × (Shift ? 3 : 1)`，
 *   `dt` 钳制在 `[0, 0.05]`；**同时**平移 `camera.position` 与 `controls.target`。
 */

/** 源站的视角预设（`iK` 的第一个参数） */
export type DirectorViewPreset = "top" | "front";

/** 源站的 `hX`：可平移视口的裸键集合 */
export const DIRECTOR_VIEW_PAN_KEYS = [
  "w",
  "a",
  "s",
  "d",
  "q",
  "e",
] as const;

export type DirectorViewPanKey = (typeof DIRECTOR_VIEW_PAN_KEYS)[number];

/** 源站 `oi` 的步长系数 */
export const DIRECTOR_VIEW_PAN_SPEED = 1.2;
/** 源站 `oi` 的距离下限（`Math.max(dist, .5)`） */
export const DIRECTOR_VIEW_PAN_MIN_DISTANCE = 0.5;
/** 源站 `oi` 的 Shift 加速倍数（`nW.current?3:1`） */
export const DIRECTOR_VIEW_PAN_SHIFT_MULTIPLIER = 3;
/** 源站 `oi` 的 dt 上限（`Math.min(Math.max((e-a)/1e3,0),.05)`） */
export const DIRECTOR_VIEW_PAN_MAX_DELTA_SECONDS = 0.05;
/** 源站 `oi` 里 `right` 退化时的兜底长度平方阈值 */
export const DIRECTOR_VIEW_PAN_MIN_RIGHT_LENGTH_SQUARED = 1e-6;

/** 源站 `iK` 的方向向量表（**逐字**） */
const DIRECTOR_VIEW_PRESET_DIRECTIONS: Record<DirectorViewPreset, DirectorTuple3> =
  {
    top: [0, 1, 0.001],
    front: [0, 0, 1],
  };

function normalizeVector(
  vector: DirectorTuple3,
  fallback: DirectorTuple3,
): DirectorTuple3 {
  const length = Math.hypot(vector[0], vector[1], vector[2]);
  if (!Number.isFinite(length) || length === 0) return [...fallback];
  return [vector[0] / length, vector[1] / length, vector[2] / length];
}

function crossVectors(a: DirectorTuple3, b: DirectorTuple3): DirectorTuple3 {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

/**
 * 源站 `iK(preset)`：**只改方向、不改视距**。
 *
 * @param preset 视角预设（`top` 俯视 / `front` 正面）
 * @param snapshot 当前相机位姿（`position` / `target` / `fov`）
 * @returns 新的位姿：`target` 不变，`position` 沿预设方向、保持当前视距
 */
export function getDirectorViewPresetPose(
  preset: DirectorViewPreset,
  snapshot: DirectorViewportSnapshot,
): DirectorViewportSnapshot {
  const direction = DIRECTOR_VIEW_PRESET_DIRECTIONS[preset];
  const dx = snapshot.position[0] - snapshot.target[0];
  const dy = snapshot.position[1] - snapshot.target[1];
  const dz = snapshot.position[2] - snapshot.target[2];
  // 源站：`i = t?.distance ?? (Math.hypot(a.x-n.x,a.y-n.y,a.z-n.z) || h$)`
  const distance = Math.max(Math.hypot(dx, dy, dz), 0.000001);
  const length = Math.hypot(direction[0], direction[1], direction[2]) || 1;
  return {
    fov: snapshot.fov,
    target: [...snapshot.target],
    position: [
      snapshot.target[0] + (direction[0] / length) * distance,
      snapshot.target[1] + (direction[1] / length) * distance,
      snapshot.target[2] + (direction[2] / length) * distance,
    ],
  };
}

export type DirectorViewPanDeltaInput = {
  /** 当前**仍按住**的键（源站的 `nK.current`） */
  keys: Iterable<string>;
  /** 相机前向（源站的 `camera.getWorldDirection()`） */
  forward: DirectorTuple3;
  /** 上方向（源站的 `(0,1,0)`） */
  up: DirectorTuple3;
  /** `|camera.position − controls.target|` */
  distance: number;
  /** Shift 是否按下（源站的 `nW.current`） */
  shift: boolean;
  /** 这一帧的时间步长（秒） */
  deltaSeconds: number;
};

/**
 * 源站 `oi` 的一帧位移（逐字复刻）。
 *
 * @returns 这一帧要平移的向量（`[0,0,0]` 表示没有键被按住）
 */
export function computeDirectorViewPanDelta(
  input: DirectorViewPanDeltaInput,
): DirectorTuple3 {
  const pressed = new Set(input.keys);
  if (pressed.size === 0) return [0, 0, 0];

  const forward = normalizeVector(input.forward, [0, 0, -1]);
  const up = normalizeVector(input.up, [0, 1, 0]);

  // 源站：`c = new Vector3().crossVectors(o, s)`
  const rawRight = crossVectors(forward, up);
  const rightLengthSquared =
    rawRight[0] * rawRight[0] +
    rawRight[1] * rawRight[1] +
    rawRight[2] * rawRight[2];
  // 源站：`1e-6 > c.lengthSq() ? c.set(1,0,0) : c.normalize()`
  const right =
    rightLengthSquared < DIRECTOR_VIEW_PAN_MIN_RIGHT_LENGTH_SQUARED
      ? ([1, 0, 0] as DirectorTuple3)
      : normalizeVector(rawRight, [1, 0, 0]);

  let delta: DirectorTuple3 = [0, 0, 0];
  const add = (vector: DirectorTuple3, sign: 1 | -1): void => {
    delta = [
      delta[0] + vector[0] * sign,
      delta[1] + vector[1] * sign,
      delta[2] + vector[2] * sign,
    ];
  };
  // 源站的分支顺序：w / s / d / a / e / q
  if (pressed.has("w")) add(forward, 1);
  if (pressed.has("s")) add(forward, -1);
  if (pressed.has("d")) add(right, 1);
  if (pressed.has("a")) add(right, -1);
  if (pressed.has("e")) add(up, 1);
  if (pressed.has("q")) add(up, -1);

  if (delta[0] === 0 && delta[1] === 0 && delta[2] === 0) return [0, 0, 0];

  // 源站：`d.normalize().multiplyScalar(e * i)`
  const normalized = normalizeVector(delta, [0, 0, 0]);
  const step =
    DIRECTOR_VIEW_PAN_SPEED *
    Math.max(input.distance, DIRECTOR_VIEW_PAN_MIN_DISTANCE) *
    (input.shift ? DIRECTOR_VIEW_PAN_SHIFT_MULTIPLIER : 1);
  // 源站：`i = Math.min(Math.max((e-a)/1e3, 0), .05)`
  const deltaSeconds = Math.min(
    Math.max(input.deltaSeconds, 0),
    DIRECTOR_VIEW_PAN_MAX_DELTA_SECONDS,
  );
  const scale = step * deltaSeconds;
  return [normalized[0] * scale, normalized[1] * scale, normalized[2] * scale];
}

export function getDirectorAspectValue(ratio: DirectorAspectRatio): number {
  if (ratio === "9:16") return 9 / 16;
  if (ratio === "1:1") return 1;
  return 16 / 9;
}

export function getDirectorFrameRect(
  viewportWidth: number,
  viewportHeight: number,
  ratio: DirectorAspectRatio,
): DirectorFrameRect | null {
  if (viewportWidth <= 0 || viewportHeight <= 0) return null;

  const horizontalPadding = viewportWidth < 600 ? 16 : 40;
  const topPadding = viewportWidth < 600 ? 20 : 32;
  const bottomPadding = viewportWidth < 600 ? 92 : 88;
  const availableWidth = Math.max(1, viewportWidth - horizontalPadding * 2);
  const availableHeight = Math.max(1, viewportHeight - topPadding - bottomPadding);
  const aspect = getDirectorAspectValue(ratio);

  let width = availableWidth;
  let height = width / aspect;
  if (height > availableHeight) {
    height = availableHeight;
    width = height * aspect;
  }

  return {
    left: (viewportWidth - width) / 2,
    top: topPadding + (availableHeight - height) / 2,
    width,
    height,
  };
}
