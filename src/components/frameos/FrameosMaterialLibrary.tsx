"use client";

import { useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { CloseIcon } from "./icons";

/**
 * FrameOS 素材库面板 - 替代 mock console.log
 * - 显示 mock 素材列表 (3 类: 图片/视频/角色)
 * - 点击素材 → 加到画布中央 + 自动选中新节点
 * - 右侧抽屉滑出
 */
const MOCK_ASSETS = [
  { id: "a1", name: "咖啡馆外景", kind: "image", emoji: "🖼" },
  { id: "a2", name: "街道夜景", kind: "image", emoji: "🖼" },
  { id: "a3", name: "室内特写", kind: "image", emoji: "🖼" },
  { id: "a4", name: "对白镜头", kind: "video", emoji: "🎬" },
  { id: "a5", name: "人物动作", kind: "video", emoji: "🎬" },
  { id: "a6", name: "场景过渡", kind: "video", emoji: "🎬" },
  { id: "a7", name: "陈默 (男主)", kind: "character", emoji: "👤" },
  { id: "a8", name: "林小婉 (女主)", kind: "character", emoji: "👤" },
  { id: "a9", name: "服务员", kind: "character", emoji: "👤" },
];

const KIND_LABELS: Record<string, string> = {
  image: "图片",
  video: "视频",
  character: "角色",
};

export function FrameosMaterialLibrary() {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<"all" | "image" | "video" | "character">("all");
  const addNode = useFrameosStore((s) => s.addNode);

  const list = filter === "all" ? MOCK_ASSETS : MOCK_ASSETS.filter((a) => a.kind === filter);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="打开素材库"
        title="从素材库选择"
        style={{
          position: "absolute",
          top: 50,
          left: 50,
          width: 40,
          height: 40,
          borderRadius: 8,
          background: "rgba(20,20,20,0.9)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(96,165,250,0.4)",
          color: "#60A5FA",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
          fontWeight: 500,
          cursor: "pointer",
          zIndex: 100,
          boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
        }}
      >
        素材库
      </button>

      {open && (
        <>
          <div
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.5)",
              zIndex: 5500,
            }}
            onClick={() => setOpen(false)}
          />
          <div
            style={{
              position: "fixed",
              top: 0,
              right: 0,
              bottom: 0,
              width: 360,
              background: "#1C1C1C",
              borderLeft: "1px solid rgba(255,255,255,0.12)",
              zIndex: 5501,
              display: "flex",
              flexDirection: "column",
              animation: "frameos-slide-in-right 0.2s ease-out",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px 20px",
                borderBottom: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <h2 style={{ color: "#FFFFFF", fontSize: 16, fontWeight: 600, margin: 0 }}>
                素材库
              </h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="关闭素材库"
                style={{
                  width: 28, height: 28, borderRadius: 6, border: "none",
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
            <div
              style={{
                display: "flex",
                gap: 4,
                padding: "10px 16px",
                borderBottom: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              {(["all", "image", "video", "character"] as const).map((k) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setFilter(k)}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: "none",
                    background: filter === k ? "rgba(59,130,246,0.2)" : "transparent",
                    color: filter === k ? "#FFFFFF" : "#A3A3A3",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  {k === "all" ? "全部" : KIND_LABELS[k]}
                </button>
              ))}
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: 8,
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              {list.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => {
                    addNode(a.kind === "image" ? "image" : a.kind === "video" ? "video" : "character");
                    setOpen(false);
                  }}
                  style={{
                    padding: 12,
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 6,
                    color: "#E0E0E0",
                    fontSize: 12,
                    cursor: "pointer",
                    textAlign: "center",
                    transition: "background 0.15s, border-color 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(59,130,246,0.15)";
                    e.currentTarget.style.borderColor = "rgba(59,130,246,0.4)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                    e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                  }}
                >
                  <div style={{ fontSize: 28, marginBottom: 4 }}>{a.emoji}</div>
                  <div>{a.name}</div>
                  <div style={{ color: "#7A7A7A", fontSize: 10, marginTop: 2 }}>
                    {KIND_LABELS[a.kind]}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}
