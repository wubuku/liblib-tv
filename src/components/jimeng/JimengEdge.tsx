"use client";

import { BaseEdge, getBezierPath, useInternalNode } from "@xyflow/react";
import type { EdgeProps } from "@xyflow/react";

/**
 * 即梦连线 (Batch 16/62)。
 *
 * SOURCE_FACT: 源站的边由 canvas 层绘制 (无 .react-flow__edge DOM)，确切视觉
 * 无法在不动用户画布的情况下提取 (BLOCKED_BY_FIXTURE)。
 * SOURCE_FACT (batch 62, 截图像素采样): 多选相邻节点时，两卡片间隙出现
 * 1px 蓝色连接段 (合成后 ≈ rgb(35,108,172))；单选/无选状态同位置无连线。
 * CLONE_DECISION: 用 xyflow bezier 边近似 — 常态 rgba(255,255,255,0.32) 1.5px，
 * 双端节点同时选中时蓝色 rgb(35,108,172) 1px，边自身选中白色 2px。
 */
export function JimengEdge({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
}: EdgeProps) {
  const sourceInternal = useInternalNode(source);
  const targetInternal = useInternalNode(target);
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const bothEndsSelected =
    sourceInternal?.selected === true && targetInternal?.selected === true;
  const stroke = selected
    ? "rgba(255,255,255,0.9)"
    : bothEndsSelected
      ? "rgb(35,108,172)"
      : "rgba(255,255,255,0.32)";

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{
        stroke,
        strokeWidth: selected ? 2 : bothEndsSelected ? 1 : 1.5,
      }}
    />
  );
}
