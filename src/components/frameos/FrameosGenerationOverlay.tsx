"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useEffect, useRef, useState } from "react";

/**
 * FrameOS 生成动画覆盖层
 * - 当 currentGeneration 存在时显示进度浮窗
 * - 进度条 0% → 100% (30 秒 mock)
 * - 显示 "生成中 1 节点 / 1 边" + prompt 摘要
 * - 完成后自动消失并 toast 成功
 */
export function FrameosGenerationOverlay() {
  const currentGeneration = useFrameosStore((s) => s.currentGeneration);
  const cancelGeneration = useFrameosStore((s) => s.cancelGeneration);
  const [progress, setProgress] = useState(0);
  const [now, setNow] = useState<number | null>(null);

  // currentGeneration 变化时重置 progress/now — 文档推荐的"派生 state 而非 effect"模式
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  // eslint-disable-next-line react-hooks/refs
  const prevGenRef = useRef(currentGeneration);
  // eslint-disable-next-line react-hooks/refs
  if (prevGenRef.current !== currentGeneration) {
    // eslint-disable-next-line react-hooks/refs
    prevGenRef.current = currentGeneration;
    setProgress(0);
    setNow(null);
  }

  useEffect(() => {
    if (!currentGeneration) {
      return undefined;
    }
    const startedAt = currentGeneration.startedAt;
    const durationMs = currentGeneration.durationMs;
    const tick = () => {
      const elapsed = Date.now() - startedAt;
      const p = Math.min(100, (elapsed / durationMs) * 100);
      setProgress(p);
      setNow(Date.now());
      if (p >= 100) {
        // 完成
        setTimeout(() => {
          useFrameosStore.setState({ currentGeneration: null });
          // toast
          const ev = new CustomEvent("frameos-toast", {
            detail: { message: "生成完成 ✓", variant: "success" },
          });
          window.dispatchEvent(ev);
        }, 500);
      }
    };
    tick();
    const id = setInterval(tick, 50);
    return () => clearInterval(id);
  }, [currentGeneration]);

  if (!currentGeneration) return null;

  const elapsedSec = Math.floor(((now ?? currentGeneration.startedAt) - currentGeneration.startedAt) / 1000);
  const totalSec = Math.floor(currentGeneration.durationMs / 1000);
  const remaining = Math.max(0, totalSec - elapsedSec);

  return (
    <div
      style={{
        position: "fixed",
        bottom: 200,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 5500,
        width: 360,
        background: "rgba(20,20,20,0.95)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(59,130,246,0.4)",
        borderRadius: 12,
        padding: 16,
        boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
        animation: "frameos-pop-in 0.2s ease-out",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: 4,
              background: "#60A5FA",
              boxShadow: "0 0 8px rgba(96,165,250,0.6)",
              animation: "frameos-gen-pulse 1s ease-in-out infinite",
            }}
          />
          <span style={{ color: "#FFFFFF", fontSize: 13, fontWeight: 500 }}>
            生成中...
          </span>
        </div>
        <span style={{ color: "#A3A3A3", fontSize: 12, fontFamily: "monospace" }}>
          {remaining}s
        </span>
      </div>

      {/* 进度条 */}
      <div
        style={{
          height: 6,
          background: "rgba(255,255,255,0.08)",
          borderRadius: 3,
          overflow: "hidden",
          marginBottom: 10,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: "linear-gradient(90deg, #3B82F6, #60A5FA)",
            transition: "width 0.05s linear",
            boxShadow: "0 0 8px rgba(96,165,250,0.5)",
          }}
        />
      </div>

      {/* 摘要 */}
      <div
        style={{
          color: "#A3A3A3",
          fontSize: 11,
          marginBottom: 4,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {currentGeneration.prompt || "（无 prompt）"}
      </div>
      <div style={{ color: "#7A7A7A", fontSize: 11 }}>
        {currentGeneration.nodeIds.length} 节点 · {currentGeneration.edgeIds.length} 边
      </div>

      {/* 取消按钮 */}
      <button
        type="button"
        onClick={cancelGeneration}
        style={{
          marginTop: 10,
          width: "100%",
          padding: "6px 12px",
          background: "transparent",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 6,
          color: "#A3A3A3",
          fontSize: 12,
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
        取消
      </button>
    </div>
  );
}
