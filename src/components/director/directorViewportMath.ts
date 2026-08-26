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
