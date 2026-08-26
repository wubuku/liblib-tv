import type { DirectorAspectRatio } from "@/store/directorStore";

export interface DirectorFrameRect {
  left: number;
  top: number;
  width: number;
  height: number;
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
