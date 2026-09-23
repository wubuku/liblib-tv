"use client";

import { useEffect, useState } from "react";

/**
 * FrameOS 全屏文本查看浮层 (Batch 205, 推断实现):
 * 文本节点浮动工具条的「全屏查看」触发——全屏显示文本内容便于阅读。
 * 事件: window "frameos:fullscreen-text" { title, content }
 * 关闭: × 或 Esc
 */
export function FrameosFullscreenText() {
  const [view, setView] = useState<{ title: string; content: string } | null>(
    null,
  );

  useEffect(() => {
    const open = (e: Event) => {
      const detail = (e as CustomEvent<{ title: string; content: string }>)
        .detail;
      setView(detail);
    };
    window.addEventListener("frameos:fullscreen-text", open);
    return () => window.removeEventListener("frameos:fullscreen-text", open);
  }, []);

  useEffect(() => {
    if (!view) return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setView(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [view]);

  if (!view) return null;

  return (
    <div
      data-frameos-fullscreen-text
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 3000,
        background: "rgba(13,13,13,0.97)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "48px 24px",
        overflow: "auto",
      }}
    >
      <button
        type="button"
        aria-label="关闭全屏查看"
        onClick={() => setView(null)}
        style={{
          position: "absolute",
          top: 24,
          right: 32,
          width: 32,
          height: 32,
          borderRadius: 8,
          border: "none",
          background: "transparent",
          color: "#A3A3A3",
          fontSize: 18,
          cursor: "pointer",
        }}
      >
        ×
      </button>
      <h2
        style={{
          color: "#FFFFFF",
          fontSize: 20,
          fontWeight: 600,
          margin: "0 0 24px",
        }}
      >
        {view.title}
      </h2>
      <div
        style={{
          color: "#E0E0E0",
          fontSize: 16,
          lineHeight: 1.8,
          maxWidth: 720,
          whiteSpace: "pre-wrap",
        }}
      >
        {view.content || "（无内容）"}
      </div>
    </div>
  );
}
