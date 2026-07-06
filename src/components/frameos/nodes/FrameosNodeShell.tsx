"use client";

import type { ReactNode } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

/**
 * Frameos 节点统一外壳：
 * - node-card-wrap (相对定位 容器)
 *   - node-floating-title (绝对 top:-22px, color #A3A3A3, font 500 12px)
 *   - node-card (bg #1C1C1C, radius 10px, column flex)
 *     - 左右 handle
 *     - card-body (children)
 *     - resize-handle (右下角 18×18, opacity 0 → hover 1)
 */
export interface FrameosNodeShellProps {
  title: string;
  titleIcon: ReactNode;
  titleRight?: ReactNode;
  selected?: boolean;
  children: ReactNode;
  showLeftHandle?: boolean;
  showRightHandle?: boolean;
  // 是否显示缩放手柄（图片节点有，视频节点没有）
  showResizeHandle?: boolean;
  // 节点类型（用于 className 标记 is-text/is-video/is-image）
  kind: "text" | "image" | "video";
  width?: number;
  height?: number;
  nodeProps: NodeProps;
}

export function FrameosNodeShell({
  title,
  titleIcon,
  titleRight,
  selected,
  children,
  showLeftHandle = true,
  showRightHandle = true,
  showResizeHandle = true,
  kind,
  width,
  height,
  nodeProps,
}: FrameosNodeShellProps) {
  const { id } = nodeProps;
  return (
    <div
      className={`node-card-wrap is-${kind}${selected ? " is-selected" : ""}`}
      style={{
        width: width ?? undefined,
        height: height ?? undefined,
        position: "relative",
      }}
    >
      {/* Floating title - 绝对定位到节点顶部上方 */}
      <div className="node-floating-title">
        <div className="node-floating-title__left">
          <i className="node-floating-title__icon">{titleIcon}</i>
          <span className="node-floating-title__name">{title}</span>
        </div>
        {titleRight && (
          <div className="node-floating-title__right">{titleRight}</div>
        )}
      </div>

      {/* 节点卡片 */}
      <div
        className={`node-card ${selected ? "is-selected" : ""}`}
        style={{
          backgroundColor: "#1C1C1C",
          borderRadius: "10px",
          width: width ?? "100%",
          height: height ?? "100%",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          overflow: "visible",
          transition: "box-shadow 0.15s, border-color 0.15s",
          border: selected
            ? "1px solid rgba(96,165,250,0.6)"
            : "1px solid transparent",
          boxShadow: selected
            ? "0 0 0 4px rgba(59,130,246,0.18), 0 8px 24px rgba(0,0,0,0.4)"
            : "0 2px 8px rgba(0,0,0,0.2)",
        }}
      >
        {/* XYFlow handles - 单边连接端口 (选中时显示为白色圆形 + 蓝边) */}
        {showLeftHandle && (
          <Handle
            type="target"
            position={Position.Left}
            id="left"
            className="frameos-handle"
            style={{
              width: selected ? 16 : 8,
              height: selected ? 16 : 8,
              background: selected ? "#FFFFFF" : "#3B82F6",
              border: selected ? "2px solid #3B82F6" : "none",
              opacity: selected ? 1 : 0,
              transition: "all 0.15s",
              cursor: "crosshair",
            }}
          />
        )}
        {showRightHandle && (
          <Handle
            type="source"
            position={Position.Right}
            id="right"
            className="frameos-handle"
            style={{
              width: selected ? 16 : 8,
              height: selected ? 16 : 8,
              background: selected ? "#FFFFFF" : "#3B82F6",
              border: selected ? "2px solid #3B82F6" : "none",
              opacity: selected ? 1 : 0,
              transition: "all 0.15s",
              cursor: "crosshair",
            }}
          />
        )}

        {/* 内容区 */}
        <div style={{ overflow: "hidden", borderRadius: 9, flex: 1, display: "flex", flexDirection: "column" }}>
          {children}
        </div>

        {/* resize handle - 右下角 (hover 节点时显示) */}
        {showResizeHandle && (
          <div
            className="resize-handle"
            aria-label="拖拽调整大小"
            data-node-id={id}
            style={{
              position: "absolute",
              right: 0,
              bottom: 0,
              width: 18,
              height: 18,
              cursor: "nwse-resize",
              opacity: 0,
              transition: "opacity 0.15s",
              backgroundImage:
                "linear-gradient(135deg, transparent 0%, transparent 50%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0.5) 55%, transparent 55%, transparent 65%, rgba(255,255,255,0.5) 65%, rgba(255,255,255,0.5) 70%, transparent 70%, transparent 80%, rgba(255,255,255,0.5) 80%, rgba(255,255,255,0.5) 85%, transparent 85%)",
              pointerEvents: "all",
            }}
          />
        )}
      </div>
    </div>
  );
}
