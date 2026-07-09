"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useState } from "react";
import { ArrowLeftIcon, CloseIcon, ArrowRightIcon } from "./icons";

/**
 * FrameOS 侧边面板 (展开菜单按钮控制)
 * - 默认收起, canvas 占满整个视口
 * - 点击 "展开菜单" 按钮展开, 显示项目/场景/画布导航 + 节点列表
 * - 与原站 frameos.cn 一致 (左侧滑出)
 */
export function FrameosSidePanel() {
  const [open, setOpen] = useState(false);
  const breadcrumb = useFrameosStore((s) => s.breadcrumb);
  const setBreadcrumb = useFrameosStore((s) => s.setBreadcrumb);
  const canvasData = useFrameosStore((s) => s.canvasData);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectNode = useFrameosStore((s) => s.selectNode);

  const currentKey = `${breadcrumb.project}/${breadcrumb.scene}/${breadcrumb.canvas}`;

  return (
    <>
      {/* 展开按钮 (顶部最左, 与原站一致) */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "收起菜单" : "展开菜单"}
        title={open ? "收起菜单" : "展开菜单"}
        style={{
          position: "absolute",
          top: 70,
          left: open ? 288 : 12,
          zIndex: 2700,
          width: 28,
          height: 28,
          borderRadius: 6,
          background: "rgba(20,20,20,0.85)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(255,255,255,0.12)",
          color: "#C2C2C2",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "left 0.2s ease, background 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(40,40,40,0.95)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(20,20,20,0.85)";
        }}
      >
        {open ? <ArrowLeftIcon size={14} /> : <ArrowRightIcon size={14} />}
      </button>

      {/* 侧边面板 */}
      {open && (
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
              top: 60,
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
                    style={{
                      padding: "10px 16px",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      background: isActive ? "rgba(59,130,246,0.12)" : "transparent",
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
      )}
    </>
  );
}
