"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useEffect, useState } from "react";
import { CloseIcon } from "./icons";

/**
 * FrameOS 侧边面板 — 由 AppHeader 的"展开菜单" 按钮 (dispatchEvent frameos:toggle-side) 控制
 * 显示项目/场景/画布列表. 默认收起, canvas 占满整个视口.
 */
export function FrameosSidePanel() {
  const [open, setOpen] = useState(false);
  const breadcrumb = useFrameosStore((s) => s.breadcrumb);
  const setBreadcrumb = useFrameosStore((s) => s.setBreadcrumb);
  const canvasData = useFrameosStore((s) => s.canvasData);
  const nodes = useFrameosStore((s) => s.nodes);

  useEffect(() => {
    const toggle = () => setOpen((o) => !o);
    window.addEventListener("frameos:toggle-side", toggle);
    return () => window.removeEventListener("frameos:toggle-side", toggle);
  }, []);

  const currentKey = `${breadcrumb.project}/${breadcrumb.scene}/${breadcrumb.canvas}`;

  if (!open) return null;

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          zIndex: 2680,
        }}
        onClick={() => setOpen(false)}
      />
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          bottom: 0,
          width: 280,
          background: "#1C1C1C",
          borderRight: "1px solid rgba(255,255,255,0.12)",
          zIndex: 2690,
          display: "flex",
          flexDirection: "column",
          animation: "frameos-slide-in-left 0.2s ease-out",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <h2 style={{ color: "#FFFFFF", fontSize: 14, fontWeight: 600, margin: 0 }}>
            项目
          </h2>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="关闭侧栏"
            style={{
              width: 24, height: 24, borderRadius: 6, border: "none",
              background: "transparent", color: "#A3A3A3",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer",
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
            <CloseIcon size={14} />
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          {Object.entries(canvasData).map(([key, data]) => {
            const [project, scene, canvas] = key.split("/");
            const isActive = key === currentKey;
            return (
              <div
                key={key}
                role="button"
                tabIndex={0}
                onClick={() => {
                  setBreadcrumb({ project, scene, canvas });
                  setOpen(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    setBreadcrumb({ project, scene, canvas });
                    setOpen(false);
                  }
                }}
                style={{
                  padding: "10px 16px",
                  borderBottom: "1px solid rgba(255,255,255,0.04)",
                  background: isActive ? "rgba(59,130,246,0.12)" : "transparent",
                  cursor: "pointer",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = "transparent";
                }}
              >
                <div style={{ color: isActive ? "#FFFFFF" : "#C2C2C2", fontSize: 13, fontWeight: 500 }}>
                  {project}
                </div>
                <div style={{ color: "#A3A3A3", fontSize: 12, marginTop: 2 }}>
                  {scene} / {canvas}
                </div>
                <div style={{ marginTop: 6, color: "#7A7A7A", fontSize: 11 }}>
                  {data.nodes.length} 节点 · {data.edges.length} 边
                </div>
              </div>
            );
          })}
        </div>
        <div
          style={{
            padding: "12px 16px",
            borderTop: "1px solid rgba(255,255,255,0.08)",
            color: "#7A7A7A",
            fontSize: 11,
          }}
        >
          {nodes.length} 当前节点 · 共 {Object.keys(canvasData).length} 个画布
        </div>
      </div>
    </>
  );
}
