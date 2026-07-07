"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

/**
 * FrameOS 自定义边
 * - 默认：蓝色虚线 (rgba(59,130,246,0.42), 2px, dasharray 7,5)
 * - hover/selected：变粗 + flowing pulse + 剪刀删除按钮
 *
 * 视觉行为与 liblib-tv 的 DeletableEdge 一致（共享删除按钮 + 脉冲），
 * 但默认 stroke 是蓝色虚线而不是灰色实线。
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
  selected,
}: EdgeProps) {
  const [hovered, setHovered] = useState(false);

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  useEffect(() => {
    if (hovered) {
      document.body.dataset.hoverEdge = id;
    } else if (document.body.dataset.hoverEdge === id) {
      delete document.body.dataset.hoverEdge;
    }
    return () => {
      if (document.body.dataset.hoverEdge === id) {
        delete document.body.dataset.hoverEdge;
      }
    };
  }, [hovered, id]);

  const onDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.dispatchEvent(new CustomEvent("delete-edge", { detail: { id } }));
  };

  const isActive = hovered || selected;

  return (
    <>
      {/* Background base path - 蓝色虚线 */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={20}
        style={{
          ...style,
          stroke: isActive ? "rgba(96,165,250,0.9)" : "rgba(59,130,246,0.42)",
          strokeWidth: isActive ? 3 : 2,
          strokeDasharray: isActive ? "none" : "7,5",
          transition: "stroke 200ms, stroke-width 200ms, stroke-dasharray 200ms",
          pointerEvents: "none",
        }}
      />

      {/* Invisible hit path for hover detection */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
        style={{ pointerEvents: "stroke", cursor: "pointer" }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      />

      <EdgeLabelRenderer>
        <div
          className="nodrag nopan"
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: "none",
          }}
        >
          <button
            data-edge-delete={id}
            onClick={onDelete}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            aria-label="删除连线"
            className={cn(
              "flex items-center justify-center w-8 h-8 rounded-full",
              "bg-[#1c1d29] hover:bg-[#262833] text-[#f7f7f7]",
              "shadow-lg border border-[#3a3d4a]",
              "transition-all duration-150",
              isActive
                ? "opacity-100 scale-100 pointer-events-auto"
                : "opacity-0 scale-50 pointer-events-none"
            )}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="3.5" cy="3.5" r="1.8" stroke="currentColor" strokeWidth="1.4" />
              <circle cx="3.5" cy="12.5" r="1.8" stroke="currentColor" strokeWidth="1.4" />
              <path
                d="M4.8 4.8L14 13M4.8 11.2L14 3"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
