"use client";

import { useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { ArrowDownIcon } from "./icons";

const MOCK_WORKS = [
  { id: "w1", name: "测试作品", projects: ["测试项目", "备用项目"] },
  { id: "w2", name: "短剧作品A", projects: ["开场项目", "高潮项目"] },
  { id: "w3", name: "电商作品B", projects: ["产品展示"] },
];

/**
 * FrameOS 顶部 breadcrumb 栏 (2026-09-23 源站实测对齐, Batch 164):
 * - 测试作品 / 测试项目 / 画布 1 三级, 各自下拉
 * - 画布下拉: 标题"画布" + 「+」新建入口 + 画布列表 (当前项高亮带勾, 右侧节点数)
 *   + 底部 重命名 / 删除 操作行 (源站形态; 操作结果未验证 → mock)
 * - 作品/项目下拉: 列表 + 当前项高亮
 */
export function FrameosBreadcrumb() {
  const breadcrumb = useFrameosStore((s) => s.breadcrumb);
  const setBreadcrumb = useFrameosStore((s) => s.setBreadcrumb);
  const canvasData = useFrameosStore((s) => s.canvasData);
  const nodes = useFrameosStore((s) => s.nodes);

  const [workOpen, setWorkOpen] = useState(false);
  const [projectOpen, setProjectOpen] = useState(false);
  const [canvasOpen, setCanvasOpen] = useState(false);

  const work = MOCK_WORKS.find((w) => w.name === breadcrumb.project) ?? MOCK_WORKS[0];

  const canvasNames = Array.from(
    new Set([
      ...Object.keys(canvasData)
        .filter((k) =>
          k.startsWith(`${breadcrumb.project}/${breadcrumb.scene}/`)
        )
        .map((k) => k.split("/")[2]),
      breadcrumb.canvas,
    ]),
  );

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
      {/* 展开菜单 + 作品 */}
      <Crumb
        label={breadcrumb.project}
        open={workOpen}
        onToggle={() => {
          setWorkOpen((v) => !v);
          setProjectOpen(false);
          setCanvasOpen(false);
        }}
        onClose={() => setWorkOpen(false)}
      >
        <DropdownHeader label="作品" />
        {MOCK_WORKS.map((w) => (
          <DropdownItem
            key={w.id}
            label={w.name}
            count={`${w.projects.length} 项目`}
            selected={w.name === breadcrumb.project}
            onClick={() => {
              setBreadcrumb({ project: w.name, scene: w.projects[0], canvas: "画布 1" });
              setWorkOpen(false);
            }}
          />
        ))}
      </Crumb>

      <Slash />
      <Crumb
        label={breadcrumb.scene}
        open={projectOpen}
        onToggle={() => {
          setProjectOpen((v) => !v);
          setWorkOpen(false);
          setCanvasOpen(false);
        }}
        onClose={() => setProjectOpen(false)}
      >
        <DropdownHeader label="项目" />
        {work.projects.map((s) => (
          <DropdownItem
            key={s}
            label={s}
            selected={s === breadcrumb.scene}
            onClick={() => {
              setBreadcrumb({ scene: s, canvas: "画布 1" });
              setProjectOpen(false);
            }}
          />
        ))}
      </Crumb>

      <Slash />
      <Crumb
        label={breadcrumb.canvas}
        open={canvasOpen}
        onToggle={() => {
          setCanvasOpen((v) => !v);
          setWorkOpen(false);
          setProjectOpen(false);
        }}
        onClose={() => setCanvasOpen(false)}
      >
        <div
          data-frameos-canvas-dropdown
          style={{ minWidth: 220 }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "6px 10px",
              color: "#A3A3A3",
              fontSize: 12,
            }}
          >
            <span>画布</span>
            <span
              title="新建画布"
              style={{ cursor: "pointer", fontSize: 14, color: "#C2C2C2" }}
            >
              +
            </span>
          </div>
          {MOCK_WORKS.find((w) => w.name === breadcrumb.project)?.projects.map(
            () => null,
          )}
          {canvasNames.map((name) => (
            <CanvasOption
              key={name}
              label={name}
              nodeCount={
                name === breadcrumb.canvas
                  ? nodes.length
                  : canvasData[
                      `${breadcrumb.project}/${breadcrumb.scene}/${name}`
                    ]?.nodes.length ?? 0
              }
              selected={name === breadcrumb.canvas}
              onClick={() => {
                setBreadcrumb({ canvas: name });
                setCanvasOpen(false);
              }}
            />
          ))}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 10,
              padding: "8px 10px",
              color: "#C2C2C2",
              fontSize: 13,
            }}
          >
            <span
              style={{ cursor: "pointer" }}
              onClick={() => window.alert("重命名画布 (mock，未验证)")}
            >
              重命名
            </span>
            <span style={{ color: "#3A3A3A" }}>|</span>
            <span
              style={{ cursor: "pointer" }}
              onClick={() => window.alert("删除画布 (mock，未验证)")}
            >
              删除
            </span>
          </div>
        </div>
      </Crumb>
    </div>
  );
}

function CanvasOption({
  label,
  nodeCount,
  selected,
  onClick,
}: {
  label: string;
  nodeCount: number;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <div
      data-frameos-canvas-option={label}
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
      }}
    >
      <span>{label}</span>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: selected ? "#60A5FA" : "#A3A3A3", fontSize: 12 }}>
        {nodeCount} 节点
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
      </span>
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

function DropdownHeader({ label }: { label: string }) {
  return (
    <div
      style={{
        padding: "6px 10px",
        color: "#A3A3A3",
        fontSize: 12,
      }}
    >
      {label}
    </div>
  );
}

function DropdownItem({
  label,
  count,
  selected,
  onClick,
}: {
  label: string;
  count?: string;
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
      {count && (
        <span
          style={{ color: selected ? "#60A5FA" : "#A3A3A3", fontSize: 12, marginLeft: "auto" }}
        >
          {count}
        </span>
      )}
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
