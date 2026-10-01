"use client";

import { useViewport } from "@xyflow/react";
import { useFrameosStore } from "@/store/frameosStore";
import { NODE_TYPES } from "./FrameosToolRail";

/**
 * 双击空白处弹出的「选择节点类型」菜单 (Batch 348 补完 Batch 168 的半成品接线)。
 *
 * 背景：`page.tsx` 里 Batch 168 早就把**事件半边**接好了 ——
 * 监听 `.react-flow__pane` 的 dblclick、跳过节点上的双击、记录坐标到
 * `paneMenuAt`。但 `paneMenuAt` **从没有任何组件读过**：状态被写进虚空，
 * 双击空白处**什么都不会出现**（实测 paneMenuAt={x:140,y:140} 而 DOM 里
 * 没有任何新增浮层，Esc 也清不掉这个状态）。
 * 本组件补上**渲染半边**，并让节点落在**双击的那一点**上。
 *
 * 节点类型列表直接复用工具条的 `NODE_TYPES`，避免两处各写一份类型表 ——
 * 同一个「有哪些节点类型」的事实只该有一个出处。
 */
export function FrameosPaneAddNodeMenu() {
  const paneMenuAt = useFrameosStore((s) => s.paneMenuAt);
  const setPaneMenuAt = useFrameosStore((s) => s.setPaneMenuAt);
  const addNode = useFrameosStore((s) => s.addNode);
  const { x: panX, y: panY, zoom } = useViewport();

  if (!paneMenuAt) return null;

  // 双击点从屏幕坐标换算到画布流坐标（与 addNode 的视口中央分支同一套换算）
  const flowPoint = {
    x: (paneMenuAt.x - panX) / zoom,
    y: (paneMenuAt.y - panY) / zoom,
  };

  return (
    <>
      <div
        data-frameos-pane-addnode-backdrop=""
        style={{ position: "fixed", inset: 0, zIndex: 2699 }}
        onClick={() => setPaneMenuAt(null)}
        onContextMenu={(e) => {
          e.preventDefault();
          setPaneMenuAt(null);
        }}
      />
      <div
        data-frameos-pane-addnode-menu=""
        style={{
          position: "fixed",
          left: paneMenuAt.x,
          top: paneMenuAt.y,
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 12,
          padding: 6,
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          minWidth: 200,
          zIndex: 2700,
        }}
      >
        <div
          style={{
            color: "#A3A3A3",
            fontSize: 12,
            padding: "8px 10px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            marginBottom: 4,
          }}
        >
          选择节点类型
        </div>
        {NODE_TYPES.map((nt) => (
          <button
            key={nt.type}
            type="button"
            data-frameos-pane-addnode-type={nt.type}
            onClick={() => {
              addNode(nt.type, {
                panX,
                panY,
                zoom,
                position: flowPoint,
                viewportWidth:
                  typeof window !== "undefined" ? window.innerWidth : 1440,
                viewportHeight:
                  typeof window !== "undefined" ? window.innerHeight : 900,
              });
              setPaneMenuAt(null);
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              width: "100%",
              padding: "8px 10px",
              borderRadius: 8,
              border: "none",
              background: "transparent",
              color: "#E0E0E0",
              fontSize: 13,
              textAlign: "left",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <span style={{ fontSize: 16 }}>{nt.icon}</span>
            <span>{nt.title}</span>
          </button>
        ))}
      </div>
    </>
  );
}
