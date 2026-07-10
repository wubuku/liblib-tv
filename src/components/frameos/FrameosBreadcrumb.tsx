"use client";

import { useState, useRef } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { ArrowLeftIcon, ArrowDownIcon } from "./icons";

const MOCK_PROJECTS = [
  { id: "p1", name: "默认作品", scenes: ["咖啡馆对峙", "海边告白", "办公室对话"] },
  { id: "p2", name: "短剧项目A", scenes: ["开场", "高潮", "结尾"] },
  { id: "p3", name: "电商demo", scenes: ["产品展示", "模特出镜"] },
  { id: "p4", name: "广告片系列", scenes: ["钩子版", "场景版"] },
];

const MOCK_CANVASES = ["画布 1", "画布 2", "分镜图", "流程图"];

/**
 * FrameOS 顶部 breadcrumb 栏 (位于 AppHeader 下方居中)
 * 展开菜单 / 默认作品 / 咖啡馆对峙 / 画布 1 — 每个都支持下拉
 */
export function FrameosBreadcrumb() {
  const breadcrumb = useFrameosStore((s) => s.breadcrumb);
  const setBreadcrumb = useFrameosStore((s) => s.setBreadcrumb);

  const [projectOpen, setProjectOpen] = useState(false);
  const [sceneOpen, setSceneOpen] = useState(false);
  const [canvasOpen, setCanvasOpen] = useState(false);

  return (
    <div
      className="canvas-breadcrumb-bar"
      style={{
        // 嵌入 AppHeader 第二条 (60px logo + 40px 面包屑); 该 div 现在在 AppHeader 内部渲染
        display: "flex",
        alignItems: "center",
        gap: 2,
        padding: "4px 6px",
        background: "transparent",
        backdropFilter: "none",
        borderRadius: 0,
        border: "none",
        pointerEvents: "auto",
      }}
    >
      {/* 展开菜单 */}
      <button
        type="button"
        aria-label="展开菜单"
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          border: "none",
          background: "transparent",
          color: "#C2C2C2",
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
          e.currentTarget.style.color = "#C2C2C2";
        }}
      >
        <ArrowLeftIcon size={16} />
      </button>

      <Crumb
        label={breadcrumb.project}
        open={projectOpen}
        onToggle={() => {
          setProjectOpen((v) => !v);
          setSceneOpen(false);
          setCanvasOpen(false);
        }}
        onClose={() => setProjectOpen(false)}
      >
        {MOCK_PROJECTS.map((p) => (
          <DropdownItem
            key={p.id}
            label={p.name}
            selected={p.name === breadcrumb.project}
            onClick={() => {
              setBreadcrumb({ project: p.name, scene: p.scenes[0] });
              setProjectOpen(false);
            }}
          />
        ))}
        <Divider />
        <DropdownItem label="+ 新建项目" onClick={() => setProjectOpen(false)} />
      </Crumb>

      <Slash />
      <Crumb
        label={breadcrumb.scene}
        open={sceneOpen}
        onToggle={() => {
          setSceneOpen((v) => !v);
          setProjectOpen(false);
          setCanvasOpen(false);
        }}
        onClose={() => setSceneOpen(false)}
      >
        {MOCK_PROJECTS.find((p) => p.name === breadcrumb.project)?.scenes.map((s) => (
          <DropdownItem
            key={s}
            label={s}
            selected={s === breadcrumb.scene}
            onClick={() => {
              setBreadcrumb({ scene: s });
              setSceneOpen(false);
            }}
          />
        ))}
        <Divider />
        <DropdownItem label="+ 新建场景" onClick={() => setSceneOpen(false)} />
      </Crumb>

      <Slash />
      <Crumb
        label={breadcrumb.canvas}
        open={canvasOpen}
        onToggle={() => {
          setCanvasOpen((v) => !v);
          setProjectOpen(false);
          setSceneOpen(false);
        }}
        onClose={() => setCanvasOpen(false)}
      >
        {MOCK_CANVASES.map((c) => (
          <DropdownItem
            key={c}
            label={c}
            selected={c === breadcrumb.canvas}
            onClick={() => {
              setBreadcrumb({ canvas: c });
              setCanvasOpen(false);
            }}
          />
        ))}
        <Divider />
        <DropdownItem label="+ 新建画布" onClick={() => setCanvasOpen(false)} />
      </Crumb>
    </div>
  );
}

function Crumb({
  label,
  open,
  onToggle,
  onClose,
  children,
}: {
  label: string;
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="breadcrumb-switcher"
        onClick={onToggle}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 2,
          padding: "5px 8px 5px 10px",
          borderRadius: 8,
          border: `1px solid ${open ? "rgba(96,165,250,0.4)" : "transparent"}`,
          background: open ? "rgba(59,130,246,0.16)" : "transparent",
          color: open ? "#60A5FA" : "#FFFFFF",
          fontSize: 13,
          fontWeight: 500,
          cursor: "pointer",
          height: 27,
          transition: "background 0.15s, border-color 0.15s, color 0.15s",
        }}
        onMouseEnter={(e) => {
          if (!open) {
            e.currentTarget.style.background = "rgba(255,255,255,0.05)";
            e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
          }
        }}
        onMouseLeave={(e) => {
          if (!open) {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.borderColor = "transparent";
          }
        }}
      >
        <span>{label}</span>
        <ArrowDownIcon size={12} />
      </button>
      {open && (
        <>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 2699 }}
            onClick={onClose}
          />
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 6px)",
              left: 0,
              minWidth: 180,
              background: "#1C1C1C",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 10,
              padding: 6,
              boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
              zIndex: 2700,
            }}
          >
            {children}
          </div>
        </>
      )}
    </div>
  );
}

function DropdownItem({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
        padding: "8px 10px",
        borderRadius: 6,
        background: selected ? "rgba(59,130,246,0.16)" : "transparent",
        color: selected ? "#60A5FA" : "#FFFFFF",
        fontSize: 13,
        cursor: "pointer",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!selected) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
      }}
      onMouseLeave={(e) => {
        if (!selected) e.currentTarget.style.background = "transparent";
      }}
    >
      <span>{label}</span>
      {selected && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M5 12l5 5L20 7"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </div>
  );
}

function Divider() {
  return (
    <div
      style={{
        height: 1,
        background: "rgba(255,255,255,0.08)",
        margin: "4px 0",
      }}
    />
  );
}

function Slash() {
  return (
    <span
      style={{
        color: "#5A5A5A",
        fontSize: 13,
        userSelect: "none",
        padding: "0 2px",
      }}
    >
      /
    </span>
  );
}
