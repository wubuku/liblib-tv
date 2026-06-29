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
 * Inject a unique @keyframes + className rule into document.head for a given
 * edge/phase. The animation moves stroke-dashoffset from 100 -> 0, so a
 * 20/80 dasharray segment travels along the normalized (pathLength=100) path.
 */
function useEdgePulseKeyframe(edgeId: string, phase: number) {
  useEffect(() => {
    if (typeof document === "undefined") return;
    const styleId = `edge-flow-kf-${edgeId}-${phase}`;
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    const className = `edge-flow-kf-${edgeId}-${phase}`;
    style.textContent = `
      @keyframes ${className} {
        from { stroke-dashoffset: 100; }
        to { stroke-dashoffset: 0; }
      }
      .${className} {
        animation: ${className} 1.6s linear infinite;
      }
    `;
    document.head.appendChild(style);
    return () => {
      const el = document.getElementById(styleId);
      if (el) el.remove();
    };
  }, [edgeId, phase]);
}

/**
 * Replicates LibTV's edge hover/select effect:
 * - Hovered/selected edge has thicker stroke (4) with light gray-blue color
 * - A "flowing pulse" effect: 3 light segments animate along the path using
 *   stroke-dasharray + stroke-dashoffset CSS animation (per-segment phase offset)
 * - A scissors delete button appears at the midpoint
 */
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
      <defs>
        {/* Strong glow filter for the flowing pulse segments */}
        <filter
          id={`edge-flow-filter-${id}`}
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
          colorInterpolationFilters="sRGB"
        >
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Background base path - dimmed when active so the flow stands out */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={20}
        style={{
          ...style,
          strokeWidth: isActive ? 4 : 2,
          stroke: isActive ? "#c0c8d0" : "#86909c",
          opacity: isActive ? 0.45 : 1,
          transition: "stroke 200ms, stroke-width 200ms, opacity 200ms",
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

      {/* Flowing pulse: 3 segments with CSS keyframe animation, different phase */}
      {isActive && (
        <g style={{ pointerEvents: "none" }} filter={`url(#edge-flow-filter-${id})`}>
          <PulsePath d={edgePath} edgeId={id} phase={0} />
          <PulsePath d={edgePath} edgeId={id} phase={1} />
          <PulsePath d={edgePath} edgeId={id} phase={2} />
        </g>
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

/**
 * A pulse segment using a CSS keyframe injected via useEdgePulseKeyframe.
 * The animation moves stroke-dashoffset 100 -> 0, so a 20/80 dasharray
 * travels along the pathLength=100 normalized path. Each phase is offset
 * by animation-delay so 3 segments appear evenly spaced.
 */
function PulsePath({
  d,
  edgeId,
  phase,
}: {
  d: string;
  edgeId: string;
  phase: number;
}) {
  useEdgePulseKeyframe(edgeId, phase);
  const animName = `edge-flow-kf-${edgeId}-${phase}`;

  return (
    <>
      <defs>
        <linearGradient id={`edge-flow-grad-${edgeId}-${phase}`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(180, 220, 255, 0)" />
          <stop offset="50%" stopColor="rgba(200, 235, 255, 1)" />
          <stop offset="100%" stopColor="rgba(180, 220, 255, 0)" />
        </linearGradient>
      </defs>
      <path
        d={d}
        fill="none"
        stroke={`url(#edge-flow-grad-${edgeId}-${phase})`}
        strokeWidth={6}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={animName}
        style={{
          pathLength: 100,
          strokeDasharray: "20 80",
          animationDelay: `${-phase * 0.53}s`,
        } as React.CSSProperties}
      />
    </>
  );
}