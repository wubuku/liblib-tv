"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function DeletableEdge({
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

  // Reflect hover state on body so CSS can target the delete button via attribute
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
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={50}
        style={{
          ...style,
          strokeWidth: isActive ? 3 : 2,
          stroke: isActive ? "#09caf5" : "#86909c",
          filter: isActive
            ? "drop-shadow(0 0 4px rgba(9, 202, 245, 0.6))"
            : undefined,
          transition: "stroke 0.15s ease, stroke-width 0.15s ease, filter 0.15s ease",
        }}
        className={cn(isActive && "react-flow__edge-path-active")}
      />

      {/* Overlay path to detect hover via React state (BaseEdge doesn't expose events) */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={40}
        style={{ pointerEvents: "stroke", cursor: "pointer" }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      />

      {/* Pulse animation overlay */}
      {isActive && (
        <path
          d={edgePath}
          fill="none"
          stroke="#09caf5"
          strokeWidth={isActive ? 3 : 2}
          style={{
            opacity: 0.4,
            animation: "edge-pulse 1.2s ease-in-out infinite",
            pointerEvents: "none",
          }}
        />
      )}

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
              "flex items-center justify-center w-7 h-7 rounded-full",
              "bg-[#f53f3f] hover:bg-[#ff6a6f] text-white",
              "shadow-lg border-2 border-[#171717]",
              "transition-all duration-150",
              isActive
                ? "opacity-100 scale-100 pointer-events-auto"
                : "opacity-0 scale-50 pointer-events-none"
            )}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="3" cy="3" r="1.6" stroke="currentColor" strokeWidth="1.3" />
              <circle cx="3" cy="11" r="1.6" stroke="currentColor" strokeWidth="1.3" />
              <path
                d="M4.2 4L12 11M4.2 10L12 3"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}