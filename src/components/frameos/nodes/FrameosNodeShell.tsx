"use client";

import type { ReactNode } from "react";
import { Handle, Position, NodeResizer, type NodeProps } from "@xyflow/react";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * Frameos 节点统一外壳（参考原站 frameos.cn 的精确 DOM）
 * - node-card-wrap (相对定位, 容器 class `is-{kind} is-embedded` + 可选 `is-selected`)
 *   - node-floating-title (绝对 top:-22px, color #A3A3A3, font 500 12px)
 *   - node-card (透明 background, 由子内容决定颜色)
 *     - 左右 handle (默认 opacity 0, 选中时 1 + transform 偏移)
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
      className={`node-card-wrap is-${kind} is-embedded${selected ? " is-selected" : ""}`}
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

      {/* 节点卡片 - 原站是 transparent background，颜色由 card-body 决定 */}
      <div
        className={`node-card ${selected ? "is-selected" : ""}`}
        style={{
          backgroundColor: "transparent",
          borderRadius: "10px",
          width: width ?? "100%",
          height: height ?? "100%",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          overflow: "visible",
        }}
      >
        {/* XYFlow handles - 默认 opacity 0 (在 CSS .frameos-canvas .react-flow__handle 中),
           选中/hover 时 CSS 改 opacity 1 + transform 偏移 */}
        {showLeftHandle && (
          <Handle
            type="target"
            position={Position.Left}
            id="left"
            className="frameos-handle"
          />
        )}
        {showRightHandle && (
          <Handle
            type="source"
            position={Position.Right}
            id="right"
            className="frameos-handle"
          />
        )}

        {/* XYFlow NodeResizer (右下角缩放手柄) - 仅图片/文本节点有 */}
        {showResizeHandle && selected && (
          <NodeResizer
            color="#60A5FA"
            isVisible={selected}
            minWidth={150}
            minHeight={100}
            maxWidth={800}
            maxHeight={600}
            lineClassName="frameos-resize-line"
            handleClassName="frameos-resize-handle"
            onResize={(_, params) => {
              // 实时同步尺寸到 store
              const setNodes = useFrameosStore.getState().setNodes;
              const { nodes } = useFrameosStore.getState();
              setNodes(
                nodes.map((n) =>
                  n.id === nodeProps.id
                    ? { ...n, style: { ...n.style, width: params.width, height: params.height } }
                    : n
                )
              );
            }}
            onResizeEnd={(_, params) => {
              // 持久化尺寸到 store (带 history)
              const updateNodeData = useFrameosStore.getState().updateNodeData;
              const { past, nodes, edges } = useFrameosStore.getState();
              useFrameosStore.setState({
                past: [...past.slice(-19), { nodes, edges }],
                future: [],
              });
              updateNodeData(nodeProps.id, {
                width: params.width,
                height: params.height,
              });
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
