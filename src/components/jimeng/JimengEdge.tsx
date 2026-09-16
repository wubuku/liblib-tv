"use client";

import { BaseEdge, getBezierPath, useInternalNode } from "@xyflow/react";
import type { EdgeProps } from "@xyflow/react";

/**
 * 即梦连线 (Batch 16/62；Batch 208 真实视觉采样)。
 *
 * SOURCE_FACT (batch 208, 208-edges.json): 画布出现真实边 DOM——未选中边
 * stroke rgb(0,142,229) 1px 直线无虚线；截图 (208-source-image-toolbar.png)
 * 显示为细蓝线 + 端点小 + 圆 (悬停态推断，未 DOM 采样)。
 * SOURCE_FACT (batch 62): 双端节点同时选中时 ≈ rgb(35,108,172)。
 * CLONE_DECISION: 常态 rgb(0,142,229) 1px (批 208 实测)，双端选中
 * rgb(35,108,172) 1px (批 62)，边自身选中白色 2px。
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
      : "rgb(0,142,229)";

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{
        stroke,
        strokeWidth: selected ? 2 : 1,
      }}
    />
  );
}
