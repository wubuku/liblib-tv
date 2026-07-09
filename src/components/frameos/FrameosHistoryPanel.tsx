"use client";

import { useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { HistoryIcon, CloseIcon } from "./icons";

/**
 * FrameOS 历史记录面板 - 时光机侧栏
 * - 显示过去 20 步操作
 * - 点击某步跳转
 * - Figma / frameos.cn 风格
 */
export function FrameosHistoryPanel() {
  const past = useFrameosStore((s) => s.past);
  const future = useFrameosStore((s) => s.future);
  const [open, setOpen] = useState(false);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="打开历史记录"
        style={{
          position: "fixed",
          top: "50%",
          right: 0,
          transform: "translateY(-50%)",
          width: 32,
          height: 48,
          background: "rgba(20,20,20,0.85)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRight: "none",
          borderTopLeftRadius: 8,
          borderBottomLeftRadius: 8,
          color: "#A3A3A3",
          cursor: "pointer",
          zIndex: 2690,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(40,40,40,0.95)";
          e.currentTarget.style.color = "#FFFFFF";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(20,20,20,0.85)";
          e.currentTarget.style.color = "#A3A3A3";
        }}
      >
        <HistoryIcon size={16} />
      </button>
    );
  }

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
          right: 0,
          bottom: 0,
          width: 280,
          background: "#1C1C1C",
          borderLeft: "1px solid rgba(255,255,255,0.12)",
          zIndex: 2690,
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
            历史记录
          </h2>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="关闭"
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
            flex: 1,
            overflowY: "auto",
            padding: "8px 0",
          }}
        >
          {past.length === 0 && (
            <div
              style={{
                color: "#7A7A7A",
                fontSize: 13,
                textAlign: "center",
                padding: "32px 20px",
              }}
            >
              暂无历史记录
            </div>
          )}
          {past.map((_, i) => {
            // past 的 index 0 = 最早, 末 = 最近
            const isLast = i === past.length - 1;
            return (
              <button
                key={i}
                type="button"
                onClick={() => {
                  // 跳到该步 = 多次 undo 直到该索引成为"当前"
                  const remaining = past.length - 1 - i;
                  for (let k = 0; k < remaining; k++) {
                    useFrameosStore.getState().undo();
                  }
                  setOpen(false);
                }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 20px",
                  background: isLast ? "rgba(59,130,246,0.16)" : "transparent",
                  border: "none",
                  borderLeft: isLast ? "2px solid #60A5FA" : "2px solid transparent",
                  color: isLast ? "#FFFFFF" : "#A3A3A3",
                  fontSize: 13,
                  textAlign: "left",
                  cursor: "pointer",
                  transition: "background 0.15s, color 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isLast) {
                    e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                    e.currentTarget.style.color = "#FFFFFF";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isLast) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "#A3A3A3";
                  }
                }}
              >
                步骤 {i + 1}
                {isLast && <span style={{ marginLeft: 8, color: "#60A5FA", fontSize: 11 }}>当前</span>}
              </button>
            );
          })}
        </div>
        <div
          style={{
            padding: "12px 20px",
            borderTop: "1px solid rgba(255,255,255,0.08)",
            color: "#7A7A7A",
            fontSize: 11,
          }}
        >
          共 {past.length} 步历史 · {future.length} 步可重做
        </div>
      </div>
    </>
  );
}
