"use client";

import { BaseEdge, getBezierPath } from "@xyflow/react";
import type { EdgeProps } from "@xyflow/react";

/**
 * 即梦连线 (Batch 16)。
 *
 * SOURCE_FACT: 源站的边由 canvas 层绘制 (无 .react-flow__edge DOM)，确切视觉
 * 无法在不动用户画布的情况下提取 (BLOCKED_BY_FIXTURE)。
 * CLONE_DECISION: 用 xyflow bezier 边近似 — 常态 rgba(255,255,255,0.32) 1.5px，
 * 选中高亮白色 2px。
 */
export function JimengEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
}: EdgeProps) {
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{
        stroke: selected ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.32)",
        strokeWidth: selected ? 2 : 1.5,
      }}
    />
  );
}
