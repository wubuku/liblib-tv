"use client";

import { ArrowGoBackIcon, ArrowGoForwardIcon } from "./icons";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * FrameOS 顶部右侧撤销/重做 Dock (位于 AppHeader 下方, z=2700)
 */
export function FrameosHistoryDock() {
  const undo = useFrameosStore((s) => s.undo);
  const redo = useFrameosStore((s) => s.redo);
  const canUndo = useFrameosStore((s) => s.past.length > 0);
  const canRedo = useFrameosStore((s) => s.future.length > 0);

  return (
    <div
      className="canvas-history-dock"
      style={{
        position: "absolute",
        top: 70,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 2700,
      }}
    >
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
        <button
          type="button"
          aria-label="撤销 (Ctrl+Z)"
          className="dock-btn"
          onClick={undo}
          disabled={!canUndo}
          title="撤销 (Ctrl+Z)"
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            border: "none",
            background: "transparent",
            color: canUndo ? "#C2C2C2" : "#5A5A5A",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: canUndo ? "pointer" : "not-allowed",
            padding: "0 8px",
            transition: "background 0.15s, color 0.15s",
          }}
          onMouseEnter={(e) => {
            if (canUndo) {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              e.currentTarget.style.color = "#FFFFFF";
            }
          }}
          onMouseLeave={(e) => {
            if (canUndo) {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#C2C2C2";
            }
          }}
        >
          <ArrowGoBackIcon size={16} />
        </button>
        <button
          type="button"
          aria-label="重做 (Ctrl+Shift+Z)"
          className="dock-btn"
          disabled={!canRedo}
          onClick={redo}
          title="重做 (Ctrl+Shift+Z)"
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            border: "none",
            background: "transparent",
            color: canRedo ? "#C2C2C2" : "#5A5A5A",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: canRedo ? "pointer" : "not-allowed",
            padding: "0 8px",
            transition: "background 0.15s, color 0.15s",
          }}
          onMouseEnter={(e) => {
            if (canRedo) {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              e.currentTarget.style.color = "#FFFFFF";
            }
          }}
          onMouseLeave={(e) => {
            if (canRedo) {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#C2C2C2";
            }
          }}
        >
          <ArrowGoForwardIcon size={16} />
        </button>
      </div>
    </div>
  );
}
