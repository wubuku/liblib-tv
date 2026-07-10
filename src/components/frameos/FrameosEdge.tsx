"use client";

import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

/**
 * FrameOS 边 - 与 frameos.cn 完全对齐:
 * - 始终蓝色虚线 (rgba(59,130,246,0.42) 7px-5px), 持续流动动画
 * - 没有文字标签 (原站边不带 label)
 * - 没有删除按钮 (用户通过 FrameosConfirmDialog / DELETE 键删)
 * - 没有按 kind 的不同颜色 (原站统一蓝)
 */
export function FrameosEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
}: EdgeProps) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={20}
        style={{
          ...style,
          stroke: "rgba(59, 130, 246, 0.42)",
          strokeWidth: 2,
          strokeDasharray: "7 5",
          animation: "frameos-edge-flow 0.6s linear infinite",
          pointerEvents: "none",
        }}
      />
    </>
  );
}
