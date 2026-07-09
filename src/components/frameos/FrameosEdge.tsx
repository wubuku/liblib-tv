"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * FrameOS 自定义边
 * - 默认：蓝色虚线
 * - 类型决定颜色 (default/generating/error)
 * - hover/selected：变粗 + flowing pulse + 剪刀删除按钮
 * - 中央有 label (可双击编辑)
 */

const COLORS = {
  default: { stroke: "rgba(59,130,246,0.42)", active: "rgba(96,165,250,0.9)" },
  generating: { stroke: "rgba(34,197,94,0.55)", active: "rgba(74,222,128,0.95)" },
  error: { stroke: "rgba(239,68,68,0.6)", active: "rgba(248,113,113,1)" },
} as const;

type EdgeKind = keyof typeof COLORS;

export function FrameosEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
  selected,
}: EdgeProps) {
  const [hovered, setHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const updateEdgeData = useFrameosStore((s) => s.updateEdgeData);
  const edges = useFrameosStore((s) => s.edges);

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

  const kind: EdgeKind = (data?.kind as EdgeKind) ?? "default";
  const colors = COLORS[kind] ?? COLORS.default;
  const label: string = (data?.label as string) ?? "";

  // 双击边进入编辑
  const onEdgeDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const onLabelBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const newLabel = e.currentTarget.value.trim();
    setIsEditing(false);
    if (newLabel !== label) {
      updateEdgeData(id, { label: newLabel });
    }
  };

  return (
    <>
      {/* Background base path - 按类型颜色 */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={20}
        style={{
          ...style,
          stroke: isActive ? colors.active : colors.stroke,
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
        onDoubleClick={onEdgeDoubleClick}
      />

      {/* Flowing pulse overlay (仅 hover/selected 时显示) */}
      {isActive && (
        <path
          d={edgePath}
          fill="none"
          stroke={colors.active}
          strokeWidth={3}
          strokeDasharray="8 200"
          strokeLinecap="round"
          pathLength={100}
          style={{
            pointerEvents: "none",
            animation: `frameos-edge-flow 1.5s linear infinite`,
            filter: "drop-shadow(0 0 4px rgba(150, 200, 255, 0.6))",
          }}
        />
      )}

      <EdgeLabelRenderer>
        {/* 边的中点 label (可编辑) */}
        {(label || isEditing || isActive) && (
          <div
            className="nodrag nopan"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
          >
            {isEditing ? (
              <input
                type="text"
                defaultValue={label}
                autoFocus
                onBlur={onLabelBlur}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === "Escape") {
                    (e.target as HTMLInputElement).blur();
                  }
                }}
                style={{
                  background: "#1C1C1C",
                  border: "1px solid #60A5FA",
                  borderRadius: 4,
                  padding: "2px 6px",
                  color: "#FFFFFF",
                  fontSize: 11,
                  outline: "none",
                  fontFamily: "inherit",
                  minWidth: 60,
                }}
                placeholder="边标签"
              />
            ) : (
              <span
                onDoubleClick={onEdgeDoubleClick}
                style={{
                  background: "rgba(20,20,20,0.9)",
                  border: `1px solid ${colors.stroke}`,
                  borderRadius: 4,
                  padding: "2px 6px",
                  color: "#E0E0E0",
                  fontSize: 11,
                  fontWeight: 500,
                  cursor: "text",
                  whiteSpace: "nowrap",
                  display: "inline-block",
                  pointerEvents: "all",
                }}
              >
                {label}
              </span>
            )}
          </div>
        )}

        {/* 删除按钮 (hover/selected 时显示) */}
        <div
          className="nodrag nopan"
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX + 60}px, ${labelY - 16}px)`,
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
