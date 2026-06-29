"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Replicates LibTV's edge hover/select effect:
 * - Hovered/selected edge has thicker stroke (4) with light gray-blue color
 * - A "flowing pulse" effect: multiple light segments animate along the path,
 *   each using a transparent-to-blue linear gradient + a Gaussian-blur filter
 *   for a glowing effect
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
  const animRef = useRef<number | null>(null);

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

  // Generate 3 flow segments that travel along the path
  const flowSegments = [];
  if (isActive) {
    const numSegments = 3;
    const segmentLength = 0.18; // 18% of path
    const cycleDuration = 1800; // ms
    for (let i = 0; i < numSegments; i++) {
      const delay = (i * cycleDuration) / numSegments;
      flowSegments.push(
        <FlowSegment
          key={i}
          edgePath={edgePath}
          edgeId={id}
          delay={delay}
          duration={cycleDuration}
          segmentLength={segmentLength}
        />
      );
    }
  }

  return (
    <>
      <defs>
        <filter
          id={`edge-flow-filter-${id}`}
          filterUnits="userSpaceOnUse"
          x={Math.min(sourceX, targetX) - 20}
          y={Math.min(sourceY, targetY) - 20}
          width={Math.abs(targetX - sourceX) + 40}
          height={Math.abs(targetY - sourceY) + 40}
          colorInterpolationFilters="sRGB"
        >
          <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blurOuter" />
          <feFlood floodColor="rgba(100, 180, 255, 0.45)" result="floodOuter" />
          <feComposite in="blurOuter" in2="floodOuter" operator="in" result="glowOuter" />
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blurInner" />
          <feFlood floodColor="rgba(150, 210, 255, 0.7)" result="floodInner" />
          <feComposite in="blurInner" in2="floodInner" operator="in" result="glowInner" />
          <feMerge>
            <feMergeNode in="glowOuter" />
            <feMergeNode in="glowInner" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={20}
        style={{
          ...style,
          strokeWidth: isActive ? 4 : 2,
          stroke: isActive ? "#c0c8d0" : "#86909c",
          filter: isActive ? `drop-shadow(0 0 4px rgba(100,180,255,0.5))` : undefined,
          transition: "stroke 200ms, stroke-width 200ms",
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

      {/* Flowing pulse segments */}
      {isActive && (
        <g style={{ pointerEvents: "none" }}>{flowSegments}</g>
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
 * A light segment that travels along the bezier path.
 * Uses a transparent-to-blue gradient with the edge-flow-filter for a glowing effect.
 */
function FlowSegment({
  edgePath,
  edgeId,
  delay,
  duration,
  segmentLength,
}: {
  edgePath: string;
  edgeId: string;
  delay: number;
  duration: number;
  segmentLength: number;
}) {
  const pathRef = useRef<SVGPathElement>(null);
  const offsetRef = useRef(0);

  // Use SVG `pathLength` to normalize, then animate stroke-dashoffset
  // by manipulating the dash array to create the "traveling segment" effect
  useEffect(() => {
    let raf: number;
    const start = performance.now();

    const animate = (now: number) => {
      const elapsed = ((now - start) % duration) / duration; // 0..1
      offsetRef.current = elapsed;
      if (pathRef.current) {
        // We use dash array trick: long gap + short visible segment
        const pathLength = pathRef.current.getTotalLength();
        const visibleLen = pathLength * segmentLength;
        const gapLen = pathLength - visibleLen;
        // The visible segment starts at offset = -visibleLen + (pathLength * elapsed)
        // but easier: dashoffset = pathLength * elapsed
        const offset = pathLength * elapsed;
        pathRef.current.setAttribute(
          "stroke-dasharray",
          `${visibleLen} ${gapLen}`
        );
        pathRef.current.setAttribute("stroke-dashoffset", `${-offset}`);
      }
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [duration, segmentLength]);

  // Initial visible/dash values; updated in animation loop
  return (
    <>
      <defs>
        <linearGradient
          id={`edge-flow-grad-${edgeId}-${delay}`}
          x1="0"
          y1="0"
          x2="1"
          y2="0"
        >
          <stop offset="0%" stopColor="rgba(100, 180, 255, 0)" />
          <stop offset="100%" stopColor="rgba(100, 180, 255, 0.9)" />
        </linearGradient>
      </defs>
      <path
        ref={pathRef}
        d={edgePath}
        fill="none"
        stroke={`url(#edge-flow-grad-${edgeId}-${delay})`}
        strokeWidth={4}
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={`url(#edge-flow-filter-${edgeId})`}
        style={{
          strokeDasharray: "0 1000",
          strokeDashoffset: 0,
        }}
      />
    </>
  );
}