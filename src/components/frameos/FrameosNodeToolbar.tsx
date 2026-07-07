"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useViewport } from "@xyflow/react";
import {
  DownloadIcon,
  StarIcon,
  HdIcon,
  GlobeIcon,
  BrushIcon,
  GridIcon,
} from "./icons";

/**
 * FrameOS 节点选中后浮动工具条
 * 位置：节点顶部上方居中，固定位置跟随节点移动 + 画布缩放
 */
export function FrameosNodeToolbar() {
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectNode = useFrameosStore((s) => s.selectNode);
  const { x: panX, y: panY, zoom } = useViewport();

  const node = nodes.find((n) => n.id === selectedNodeId);
  if (!node) return null;

  // 节点在视口中的位置 = (节点内部坐标 * zoom) + pan
  const nodeX = node.position.x * zoom + panX;
  const nodeY = node.position.y * zoom + panY;
  const nodeW = (node.style?.width as number) ?? 300;

  // toolbar 居中于节点顶部上方
  const left = nodeX + (nodeW * zoom) / 2;
  const top = Math.max(80, nodeY - 50); // 不超过顶部

  // 根据节点类型显示不同的按钮
  const isImage = node.type === "image";
  const isVideo = node.type === "video";
  const isText = node.type === "text";

  return (
    <div
      className="floating-toolbar"
      style={{
        position: "fixed",
        left: `${left}px`,
        top: `${top}px`,
        transform: "translateX(-50%)",
        zIndex: 2701,
        display: "flex",
        alignItems: "center",
        gap: 2,
        padding: "4px 6px",
        background: "#1C1C1C",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 10,
        boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
        animation: "frameos-pop-in 0.15s ease-out",
        transition: "left 0.15s ease, top 0.15s ease",
      }}
    >
      <ToolbarBtn label="下载" icon={<DownloadIcon size={14} />} onClick={() => {}} />
      <ToolbarBtn label="收藏" icon={<StarIcon size={14} />} onClick={() => {}} />

      {/* 图片节点的图像编辑工具 */}
      {isImage && (
        <>
          <ToolbarBtn label="超清" icon={<HdIcon size={14} />} onClick={() => {}} />
          <ToolbarBtn label="720全景" icon={<GlobeIcon size={14} />} onClick={() => {}} />
          <ToolbarBtn label="改图" icon={<BrushIcon size={14} />} onClick={() => {}} />
          <ToolbarBtn label="宫格切分" icon={<GridIcon size={14} />} onClick={() => {}} />
        </>
      )}

      {/* 视频节点 */}
      {isVideo && (
        <>
          <ToolbarBtn label="超清" icon={<HdIcon size={14} />} onClick={() => {}} />
          <ToolbarBtn label="改图" icon={<BrushIcon size={14} />} onClick={() => {}} />
        </>
      )}

      {/* 文本节点 */}
      {isText && (
        <>
          <ToolbarBtn label="超清" icon={<HdIcon size={14} />} onClick={() => {}} />
        </>
      )}

      {/* 关闭按钮 */}
      <div
        style={{
          width: 1,
          height: 18,
          background: "rgba(255,255,255,0.08)",
          margin: "0 4px",
        }}
      />
      <button
        type="button"
        aria-label="关闭"
        onClick={() => selectNode(null)}
        style={{
          width: 24,
          height: 24,
          borderRadius: 6,
          border: "none",
          background: "transparent",
          color: "#A3A3A3",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "background 0.15s, color 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255,255,255,0.05)";
          e.currentTarget.style.color = "#FFFFFF";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "#A3A3A3";
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

function ToolbarBtn({
  label,
  icon,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "5px 10px",
        borderRadius: 6,
        border: "none",
        background: "transparent",
        color: "#E0E0E0",
        fontSize: 12,
        cursor: "pointer",
        height: 28,
        transition: "background 0.15s, color 0.15s",
        whiteSpace: "nowrap",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.08)";
        e.currentTarget.style.color = "#FFFFFF";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "#E0E0E0";
      }}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
