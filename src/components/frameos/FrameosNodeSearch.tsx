"use client";

import { useEffect, useRef, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { SearchIcon, CloseIcon } from "./icons";

/**
 * FrameOS 节点搜索面板 (Cmd+K / Ctrl+K)
 * - 输入关键字过滤节点 (按 title)
 * - 上下方向键导航
 * - 回车选中并关闭 (xyflow 默认 fitView 选中的节点效果)
 */
export function FrameosNodeSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectNode = useFrameosStore((s) => s.selectNode);

  // Cmd+K / Ctrl+K 打开
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      const isInInput = tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement).isContentEditable;
      if (isInInput) return;
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // 打开时 focus 输入框 + 重置
  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const matches = query
    ? nodes.filter((n) => (n.data.title as string)?.toLowerCase().includes(query.toLowerCase()))
    : nodes;

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const target = matches[activeIdx];
      if (target) {
        selectNode(target.id);
        setOpen(false);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.5)",
          backdropFilter: "blur(4px)",
          zIndex: 5500,
        }}
        onClick={() => setOpen(false)}
      />
      <div
        style={{
          position: "fixed",
          top: 80,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 5501,
          width: 480,
          maxWidth: "calc(100vw - 48px)",
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 12,
          boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
          overflow: "hidden",
          animation: "frameos-pop-in 0.12s ease-out",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "12px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            gap: 10,
          }}
        >
          <SearchIcon size={16} color="#A3A3A3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="搜索节点 (按名称)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIdx(0);
            }}
            onKeyDown={handleKey}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
              fontSize: 14,
              fontFamily: "inherit",
            }}
          />
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="关闭搜索"
            style={{
              width: 24, height: 24, borderRadius: 6, border: "none",
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
            <CloseIcon size={12} />
          </button>
        </div>
        <div
          style={{
            maxHeight: 320,
            overflowY: "auto",
            padding: "4px 0",
          }}
        >
          {matches.length === 0 && (
            <div
              style={{
                color: "#7A7A7A",
                fontSize: 13,
                textAlign: "center",
                padding: "24px 16px",
              }}
            >
              没有匹配的节点
            </div>
          )}
          {matches.map((n, i) => {
            const isActive = i === activeIdx;
            return (
              <button
                key={n.id}
                type="button"
                onClick={() => {
                  selectNode(n.id);
                  setOpen(false);
                }}
                onMouseEnter={() => setActiveIdx(i)}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 16px",
                  background: isActive ? "rgba(59,130,246,0.16)" : "transparent",
                  border: "none",
                  color: "#FFFFFF",
                  fontSize: 13,
                  textAlign: "left",
                  cursor: "pointer",
                  transition: "background 0.1s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span>{n.data.title as string}</span>
                  <span style={{ color: "#7A7A7A", fontSize: 11, textTransform: "uppercase" }}>
                    {n.type}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
        <div
          style={{
            padding: "8px 16px",
            borderTop: "1px solid rgba(255,255,255,0.08)",
            color: "#7A7A7A",
            fontSize: 11,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>↑↓ 移动 · Enter 选择</span>
          <span>Esc 关闭</span>
        </div>
      </div>
    </>
  );
}
