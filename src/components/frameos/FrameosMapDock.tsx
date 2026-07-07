"use client";

import { useRef } from "react";
import {
  MapPinIcon,
  SubtractIcon,
  AddLineIcon,
  FullscreenExitIcon,
  LayoutGridIcon,
  ArrowDownIcon,
} from "./icons";
import { useFrameosStore } from "@/store/frameosStore";
import { useReactFlow, useViewport } from "@xyflow/react";

// 节点类型对应的 minimap 颜色
const NODE_TYPE_COLORS: Record<string, string> = {
  text: "rgba(96,165,250,0.65)",      // 蓝
  image: "rgba(34,197,94,0.65)",      // 绿
  video: "rgba(239,68,68,0.65)",      // 红
  character: "rgba(168,85,247,0.65)", // 紫
  scene: "rgba(245,158,11,0.65)",     // 黄
  audio: "rgba(236,72,153,0.65)",     // 粉
  style: "rgba(20,184,166,0.65)",     // 青
  batch: "rgba(251,191,36,0.65)",     // 琥珀
};
const DEFAULT_NODE_COLOR = "rgba(255,255,255,0.18)";

interface DockBtnProps {
  label: string;
  icon: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}

function DockBtn({ label, icon, active, onClick }: DockBtnProps) {
  return (
    <button
      type="button"
      aria-label={label}
      className={`dock-btn${active ? " is-active" : ""}`}
      onClick={onClick}
      style={{
        width: 32,
        height: 32,
        borderRadius: 8,
        border: "none",
        background: active ? "rgba(59,130,246,0.16)" : "transparent",
        color: active ? "#60A5FA" : "#C2C2C2",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        padding: "0 8px",
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.background = "rgba(255,255,255,0.05)";
          e.currentTarget.style.color = "#FFFFFF";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "#C2C2C2";
        }
      }}
    >
      {icon}
    </button>
  );
}

function Divider() {
  return (
    <span
      className="dock-divider"
      style={{
        display: "block",
        width: 1,
        height: 18,
        background: "rgba(255,255,255,0.08)",
      }}
    />
  );
}

/**
 * FrameOS 左下 dock (minimap + 缩放控件)
 */
export function FrameosMapDock() {
  const showMinimap = useFrameosStore((s) => s.showMinimap);
  const minimapPinActive = useFrameosStore((s) => s.minimapPinActive);
  const toggleMinimap = useFrameosStore((s) => s.toggleMinimap);
  const zoomPercent = useFrameosStore((s) => s.zoomPercent);
  const setZoomPercent = useFrameosStore((s) => s.setZoomPercent);
  const isOrganizeMenuOpen = useFrameosStore((s) => s.isOrganizeMenuOpen);
  const toggleOrganizeMenu = useFrameosStore((s) => s.toggleOrganizeMenu);
  const closeOrganizeMenu = useFrameosStore((s) => s.closeOrganizeMenu);
  const organizeMode = useFrameosStore((s) => s.organizeMode);
  const setOrganizeMode = useFrameosStore((s) => s.setOrganizeMode);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  // 画布视口 (用于 minimap viewport 框)
  const { x: vpX, y: vpY, zoom: vpZoom } = useViewport();
  const setNodes = useFrameosStore((s) => s.setNodes);
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const organizeRef = useRef<HTMLDivElement>(null);

  // 实际执行节点整理
  const runOrganize = (mode: typeof organizeMode) => {
    setOrganizeMode(mode);
    // 计算布局
    const sorted = [...nodes];
    const cols = Math.ceil(Math.sqrt(sorted.length));
    const cellW = 320;
    const cellH = 220;
    const offsetX = 60;
    const offsetY = 60;
    let laid: typeof sorted = [];
    if (mode === "grid") {
      laid = sorted.map((n, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        return {
          ...n,
          position: { x: offsetX + col * cellW, y: offsetY + row * cellH },
        };
      });
    } else if (mode === "horizontal") {
      laid = sorted.map((n, i) => ({
        ...n,
        position: { x: offsetX + i * cellW, y: offsetY },
      }));
    } else {
      laid = sorted.map((n, i) => ({
        ...n,
        position: { x: offsetX, y: offsetY + i * cellH },
      }));
    }
    setNodes(laid);
  };

  return (
    <div
      className="canvas-map-dock"
      style={{
        position: "absolute",
        left: 12,
        bottom: 12,
        zIndex: 2700,
      }}
    >
      {showMinimap && (
        <div
          className="minimap-panel"
          style={{
            marginBottom: 8,
            background: "rgba(20,20,20,0.85)",
            backdropFilter: "blur(12px)",
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.06)",
            padding: 8,
          }}
        >
          <div
            className="minimap"
            style={{
              width: 160,
              height: 100,
              position: "relative",
              background: "#0D0D0D",
              borderRadius: 6,
              overflow: "hidden",
            }}
          >
            {/* 装饰性背景点阵 */}
            <div
              className="minimap-bg"
              style={{
                position: "absolute",
                inset: 0,
                backgroundImage:
                  "radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px)",
                backgroundSize: "12px 12px",
              }}
            />
            {/* 节点缩略 - 根据真实 nodes 数据计算位置和大小 + 按类型着色 */}
            {nodes.map((n) => {
              const w = (n.style?.width as number) ?? 300;
              const h = (n.style?.height as number) ?? 169;
              const left = n.position.x * 0.06;
              const top = n.position.y * 0.06;
              const width = w * 0.06;
              const height = h * 0.06;
              const isSelected = n.id === selectedNodeId;
              const typeColor = NODE_TYPE_COLORS[n.type] ?? DEFAULT_NODE_COLOR;
              return (
                <div
                  key={n.id}
                  className="mini-node"
                  title={n.data.title}
                  style={{
                    position: "absolute",
                    left: `${left}px`,
                    top: `${top}px`,
                    width: `${width}px`,
                    height: `${height}px`,
                    borderRadius: 2,
                    background: isSelected
                      ? "rgba(96,165,250,0.85)"
                      : typeColor,
                    border: isSelected
                      ? "1px solid rgba(96,165,250,1)"
                      : "1px solid rgba(255,255,255,0.12)",
                    transition: "all 0.15s",
                  }}
                />
              );
            })}

            {/* 视口框 (跟随画布 zoom/pan 实时更新) */}
            <div
              className="viewport-rect"
              style={{
                position: "absolute",
                // 视口中心 = (-vpX, -vpY) / vpZoom, 视口尺寸 = (160/vpZoom, 100/vpZoom)
                left: `${-vpX / vpZoom * 0.06}px`,
                top: `${-vpY / vpZoom * 0.06}px`,
                width: `${(160 / vpZoom) * 0.06}px`,
                height: `${(100 / vpZoom) * 0.06}px`,
                border: "1px solid rgba(96,165,250,0.8)",
                background: "rgba(96,165,250,0.1)",
                borderRadius: 2,
                pointerEvents: "none",
                transition: "all 0.15s",
              }}
            />
          </div>
        </div>
      )}

      {/* 工具栏 */}
      <div
        className="dock-bar"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          padding: 3,
          background: "rgba(20,20,20,0.85)",
          backdropFilter: "blur(12px)",
          borderRadius: 10,
          border: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <DockBtn
          label="画布小地图"
          icon={<MapPinIcon size={16} />}
          active={minimapPinActive}
          onClick={toggleMinimap}
        />
        <Divider />
        <DockBtn
          label="缩小"
          icon={<SubtractIcon size={16} />}
          onClick={() => {
            zoomOut({ duration: 200 });
            setZoomPercent(Math.max(10, zoomPercent - 10));
          }}
        />
        <span
          className="dock-scale"
          style={{
            color: "#C2C2C2",
            fontSize: 12,
            minWidth: 40,
            textAlign: "center",
            userSelect: "none",
          }}
        >
          {zoomPercent}%
        </span>
        <DockBtn
          label="放大"
          icon={<AddLineIcon size={16} />}
          onClick={() => {
            zoomIn({ duration: 200 });
            setZoomPercent(Math.min(200, zoomPercent + 10));
          }}
        />
        <DockBtn
          label="适应画布"
          icon={<FullscreenExitIcon size={16} />}
          onClick={() => {
            fitView({ duration: 200, padding: 0.1 });
            setZoomPercent(100);
          }}
        />
        <Divider />
        <DockBtn
          label="一键整理 · 网格整理"
          icon={<LayoutGridIcon size={16} />}
          onClick={() => runOrganize("grid")}
        />
        <div ref={organizeRef} style={{ position: "relative" }}>
          <DockBtn
            label="选择整理方式"
            icon={<ArrowDownIcon size={14} />}
            active={isOrganizeMenuOpen}
            onClick={toggleOrganizeMenu}
          />

          {/* 整理方式菜单 */}
          {isOrganizeMenuOpen && (
            <>
              <div
                style={{ position: "fixed", inset: 0, zIndex: 2699 }}
                onClick={closeOrganizeMenu}
              />
              <div
                style={{
                  position: "absolute",
                  left: "calc(100% + 6px)",
                  bottom: 0,
                  background: "#1C1C1C",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 12,
                  padding: 6,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
                  width: 220,
                  zIndex: 2700,
                }}
              >
                <OrganizeItem
                  title="按连线横向"
                  desc="沿连线从左到右分层"
                  selected={organizeMode === "horizontal"}
                  onClick={() => runOrganize("horizontal")}
                />
                <OrganizeItem
                  title="按连线纵向"
                  desc="沿连线从上到下分层"
                  selected={organizeMode === "vertical"}
                  onClick={() => runOrganize("vertical")}
                />
                <OrganizeItem
                  title="网格整理"
                  desc="保持相对位置去重叠对齐"
                  selected={organizeMode === "grid"}
                  onClick={() => runOrganize("grid")}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function OrganizeItem({
  title,
  desc,
  selected,
  onClick,
}: {
  title: string;
  desc: string;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "10px 12px",
        borderRadius: 8,
        cursor: "pointer",
        background: selected ? "rgba(59,130,246,0.16)" : "transparent",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!selected) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
      }}
      onMouseLeave={(e) => {
        if (!selected) e.currentTarget.style.background = "transparent";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
        <span
          style={{
            color: selected ? "#60A5FA" : "#FFFFFF",
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          {title}
        </span>
        {selected && (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path
              d="M5 12l5 5L20 7"
              stroke="#60A5FA"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </div>
      <div style={{ color: "#7A7A7A", fontSize: 12, marginTop: 2 }}>{desc}</div>
    </div>
  );
}
