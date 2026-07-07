"use client";

import { useFrameosStore } from "@/store/frameosStore";

/**
 * 调试模式开关（仅开发者使用）
 * 激活后，点击节点会弹出右侧"节点详情"面板
 * 默认隐藏，点击右下角小三角展开
 */
export function FrameosDebugToggle() {
  const isDebugMode = useFrameosStore((s) => s.isDebugMode);
  const toggleDebugMode = useFrameosStore((s) => s.toggleDebugMode);

  return (
    <div
      className="debug-toggle"
      style={{
        position: "fixed",
        right: 12,
        bottom: 12,
        zIndex: 2700,
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 10px",
        background: isDebugMode
          ? "rgba(245,158,11,0.16)"
          : "rgba(20,20,20,0.85)",
        backdropFilter: "blur(12px)",
        border: `1px solid ${isDebugMode ? "rgba(245,158,11,0.4)" : "rgba(255,255,255,0.06)"}`,
        borderRadius: 8,
        fontSize: 11,
        fontFamily: "monospace",
        color: isDebugMode ? "#F59E0B" : "#7A7A7A",
        cursor: "pointer",
        userSelect: "none",
        transition: "all 0.15s",
      }}
      onClick={toggleDebugMode}
      title="切换调试模式 (开启后点击节点显示详情面板)"
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: 3,
          background: isDebugMode ? "#F59E0B" : "#5A5A5A",
        }}
      />
      <span>{isDebugMode ? "DEBUG ON" : "DEBUG"}</span>
    </div>
  );
}
