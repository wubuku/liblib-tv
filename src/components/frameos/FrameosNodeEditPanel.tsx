"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useMemo, useState } from "react";
import {
  TextNodeIcon,
  ImageNodeIcon,
  FilmNodeIcon,
  CloseIcon,
} from "./icons";

const PARAMS_BY_KIND = {
  text: [
    { key: "content", label: "文本内容", type: "textarea" },
    { key: "title", label: "节点名称", type: "text" },
  ],
  image: [
    { key: "title", label: "节点名称", type: "text" },
    { key: "imageUrl", label: "图片 URL", type: "text" },
    { key: "alt", label: "替代文本", type: "text" },
    { key: "width", label: "宽度 (px)", type: "number" },
    { key: "height", label: "高度 (px)", type: "number" },
  ],
  video: [
    { key: "title", label: "节点名称", type: "text" },
    { key: "imageUrl", label: "视频封面 URL", type: "text" },
    { key: "duration", label: "时长 (秒)", type: "number" },
    { key: "aspectRatio", label: "画面比例", type: "select", options: ["16:9", "9:16", "1:1", "4:3"] },
  ],
} as const;

/**
 * Frameos 节点编辑面板
 * 选中节点时浮在画布右侧
 */
export function FrameosNodeEditPanel() {
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const setNodes = useFrameosStore((s) => s.setNodes);
  const selectNode = useFrameosStore((s) => s.selectNode);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId),
    [nodes, selectedNodeId]
  );

  if (!selectedNode) return null;

  const updateField = (key: string, value: unknown) => {
    setNodes(
      nodes.map((n) =>
        n.id === selectedNode.id
          ? { ...n, data: { ...n.data, [key]: value } }
          : n
      )
    );
  };

  const params = PARAMS_BY_KIND[selectedNode.type as keyof typeof PARAMS_BY_KIND] ?? [];

  return (
    <div
      className="node-edit-panel"
      style={{
        position: "absolute",
        top: 80,
        right: 12,
        width: 320,
        maxHeight: "calc(100vh - 200px)",
        background: "#1C1C1C",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 12,
        boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
        zIndex: 2700,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        animation: "slideIn 0.2s ease",
      }}
    >
      {/* 顶部 header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 14px",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: "rgba(59,130,246,0.16)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#60A5FA",
            }}
          >
            {selectedNode.type === "text" ? (
              <TextNodeIcon size={14} />
            ) : selectedNode.type === "image" ? (
              <ImageNodeIcon size={14} />
            ) : (
              <FilmNodeIcon size={14} />
            )}
          </div>
          <div>
            <div style={{ color: "#FFFFFF", fontSize: 13, fontWeight: 500 }}>节点详情</div>
            <div style={{ color: "#7A7A7A", fontSize: 11 }}>{selectedNode.data.title}</div>
          </div>
        </div>
        <button
          type="button"
          aria-label="关闭面板"
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
          <CloseIcon size={14} />
        </button>
      </div>

      {/* 内容 */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "14px",
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        {/* 节点 ID */}
        <div>
          <div style={{ color: "#A3A3A3", fontSize: 11, marginBottom: 4 }}>节点 ID</div>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: "#7A7A7A",
              padding: "6px 10px",
              background: "#0D0D0D",
              borderRadius: 6,
              border: "1px solid rgba(255,255,255,0.04)",
              wordBreak: "break-all",
            }}
          >
            {selectedNode.id}
          </div>
        </div>

        {/* 位置信息 */}
        <div style={{ display: "flex", gap: 8 }}>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#A3A3A3", fontSize: 11, marginBottom: 4 }}>X 坐标</div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: 12,
                color: "#E0E0E0",
                padding: "6px 10px",
                background: "#0D0D0D",
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.04)",
              }}
            >
              {Math.round(selectedNode.position.x)}
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#A3A3A3", fontSize: 11, marginBottom: 4 }}>Y 坐标</div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: 12,
                color: "#E0E0E0",
                padding: "6px 10px",
                background: "#0D0D0D",
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.04)",
              }}
            >
              {Math.round(selectedNode.position.y)}
            </div>
          </div>
        </div>

        {/* 节点参数 */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 14 }}>
          <div style={{ color: "#A3A3A3", fontSize: 11, marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>
            节点参数
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {params.map((p) => (
              <ParamField
                key={p.key}
                param={p}
                value={(selectedNode.data as Record<string, unknown>)[p.key]}
                onChange={(v) => updateField(p.key, v)}
              />
            ))}
          </div>
        </div>

        {/* 快捷操作 */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 14 }}>
          <div style={{ color: "#A3A3A3", fontSize: 11, marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>
            快捷操作
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <ActionButton label="复制节点" />
            <ActionButton label="锁定位置" />
            <ActionButton
              label="删除节点"
              variant="danger"
              onClick={() => {
                if (confirm(`确认删除「${selectedNode.data.title}」？`)) {
                  setNodes(nodes.filter((n) => n.id !== selectedNode.id));
                  selectNode(null);
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

interface ParamFieldProps {
  param: {
    key: string;
    label: string;
    type: string;
    options?: readonly string[];
  };
  value: unknown;
  onChange: (v: unknown) => void;
}

function ParamField({ param, value, onChange }: ParamFieldProps) {
  if (param.type === "textarea") {
    return (
      <div>
        <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 4 }}>{param.label}</div>
        <textarea
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          style={{
            width: "100%",
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 6,
            padding: "8px 10px",
            color: "#FFFFFF",
            fontSize: 12,
            outline: "none",
            resize: "vertical",
            minHeight: 60,
            fontFamily: "inherit",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)")}
        />
      </div>
    );
  }

  if (param.type === "number") {
    return (
      <div>
        <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 4 }}>{param.label}</div>
        <input
          type="number"
          value={(value as number) ?? ""}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{
            width: "100%",
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 6,
            padding: "8px 10px",
            color: "#FFFFFF",
            fontSize: 12,
            outline: "none",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)")}
        />
      </div>
    );
  }

  if (param.type === "select" && param.options) {
    return (
      <div>
        <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 4 }}>{param.label}</div>
        <select
          value={(value as string) ?? param.options[0]}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: "100%",
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 6,
            padding: "8px 10px",
            color: "#FFFFFF",
            fontSize: 12,
            outline: "none",
            cursor: "pointer",
          }}
        >
          {param.options.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div>
      <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 4 }}>{param.label}</div>
      <input
        type="text"
        value={(value as string) ?? ""}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          background: "#0D0D0D",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 6,
          padding: "8px 10px",
          color: "#FFFFFF",
          fontSize: 12,
          outline: "none",
          transition: "border-color 0.15s",
        }}
        onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)")}
        onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)")}
      />
    </div>
  );
}

function ActionButton({
  label,
  variant,
  onClick,
}: {
  label: string;
  variant?: "danger";
  onClick?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const isDanger = variant === "danger";

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: "100%",
        padding: "8px 12px",
        background: hovered
          ? isDanger
            ? "rgba(239,68,68,0.16)"
            : "rgba(255,255,255,0.05)"
          : "transparent",
        border: `1px solid ${hovered && isDanger ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.06)"}`,
        borderRadius: 6,
        color: isDanger ? "#EF4444" : "#E0E0E0",
        fontSize: 12,
        textAlign: "left",
        cursor: "pointer",
        transition: "all 0.15s",
      }}
    >
      {label}
    </button>
  );
}
