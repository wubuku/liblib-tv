"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useViewport } from "@xyflow/react";
import { useState, useRef } from "react";

/**
 * FrameOS 节点 hover tooltip
 * - 显示节点标题 + 缩略图
 * - 跟随节点位置 + 画布缩放
 * - 仅在 hover 时显示，未选中节点
 */
export function FrameosNodeTooltip() {
  const [hoverInfo, setHoverInfo] = useState<{
    x: number;
    y: number;
    node: { id: string; title: string; imageUrl?: string };
  } | null>(null);
  const nodes = useFrameosStore((s) => s.nodes);
  const { x: panX, y: panY, zoom } = useViewport();

  // 监听节点 hover 状态 - 通过 event delegation
  if (typeof window !== "undefined" && !tooltipHookInstalled) {
    installTooltipHook(setHoverInfo, nodes, panX, panY, zoom);
    tooltipHookInstalled = true;
  }

  if (!hoverInfo) return null;

  return (
    <div
      style={{
        position: "fixed",
        left: hoverInfo.x,
        top: hoverInfo.y,
        zIndex: 2700,
        background: "rgba(20,20,20,0.95)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 8,
        padding: "6px 10px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        gap: 8,
        pointerEvents: "none",
        maxWidth: 280,
        animation: "frameos-pop-in 0.1s ease-out",
      }}
    >
      {hoverInfo.node.imageUrl && (
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 4,
            overflow: "hidden",
            background: "#0D0D0D",
            flexShrink: 0,
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <img
            src={hoverInfo.node.imageUrl}
            alt=""
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 12,
            fontWeight: 500,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {hoverInfo.node.title}
        </span>
      </div>
    </div>
  );
}

let tooltipHookInstalled = false;
let cleanupFn: (() => void) | null = null;

function installTooltipHook(
  setHoverInfo: (info: any) => void,
  nodes: any[],
  initialPanX: number,
  initialPanY: number,
  initialZoom: number
) {
  if (typeof window === "undefined") return;
  if (cleanupFn) cleanupFn();

  let currentHoverId: string | null = null;
  let hideTimer: ReturnType<typeof setTimeout> | null = null;

  const showFor = (id: string, clientX: number, clientY: number) => {
    if (hideTimer) {
      clearTimeout(hideTimer);
      hideTimer = null;
    }
    const node = nodes.find((n) => n.id === id);
    if (!node) return;
    // 计算节点在视口中的位置
    const nodeX = node.position.x * initialZoom + initialPanX;
    const nodeY = node.position.y * initialZoom + initialPanY;
    const nodeW = (node.style?.width as number) ?? 300;
    // tooltip 放在节点顶部上方
    const x = nodeX + (nodeW * initialZoom) / 2;
    const y = nodeY - 8;
    setHoverInfo({
      x,
      y,
      node: {
        id: node.id,
        title: node.data?.title as string,
        imageUrl: node.data?.imageUrl as string | undefined,
      },
    });
  };

  const hide = () => {
    hideTimer = setTimeout(() => setHoverInfo(null), 100);
  };

  const onMouseOver = (e: MouseEvent) => {
    const target = (e.target as HTMLElement)?.closest('[data-id]');
    if (!target) return;
    const id = target.getAttribute('data-id');
    if (!id) return;
    if (id !== currentHoverId) {
      currentHoverId = id;
      showFor(id, e.clientX, e.clientY);
    }
  };

  const onMouseOut = (e: MouseEvent) => {
    const target = e.relatedTarget as HTMLElement | null;
    if (target?.closest('[data-id]') === e.target) return;
    currentHoverId = null;
    hide();
  };

  // 使用 capture 以便在 ReactFlow 拦截前拿到事件
  document.addEventListener('mouseover', onMouseOver, true);
  document.addEventListener('mouseout', onMouseOut, true);

  cleanupFn = () => {
    document.removeEventListener('mouseover', onMouseOver, true);
    document.removeEventListener('mouseout', onMouseOut, true);
    if (hideTimer) clearTimeout(hideTimer);
  };
}
