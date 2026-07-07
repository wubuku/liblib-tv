"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";

interface MenuItem {
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  danger?: boolean;
  separator?: boolean;
  onClick?: () => void;
}

interface ContextMenuState {
  x: number;
  y: number;
  items: MenuItem[];
}

let globalState: ContextMenuState | null = null;
let setter: ((s: ContextMenuState | null) => void) | null = null;

export function openContextMenu(state: ContextMenuState) {
  globalState = state;
  setter?.(state);
}

export function closeContextMenu() {
  globalState = null;
  setter?.(null);
}

export function FrameosContextMenu() {
  const [state, setState] = useState<ContextMenuState | null>(globalState);

  useEffect(() => {
    setter = setState;
    return () => {
      setter = null;
    };
  }, []);

  // 监听 Esc 关闭
  useEffect(() => {
    if (!state) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeContextMenu();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state]);

  if (!state) return null;

  return (
    <>
      <div
        style={{ position: "fixed", inset: 0, zIndex: 5000 }}
        onClick={closeContextMenu}
        onContextMenu={(e) => {
          e.preventDefault();
          closeContextMenu();
        }}
      />
      <div
        style={{
          position: "fixed",
          left: state.x,
          top: state.y,
          zIndex: 5001,
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 10,
          padding: 6,
          boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
          minWidth: 200,
          animation: "frameos-pop-in 0.12s ease-out",
        }}
      >
        {state.items.map((item, i) =>
          item.separator ? (
            <div
              key={i}
              style={{
                height: 1,
                background: "rgba(255,255,255,0.08)",
                margin: "4px 0",
              }}
            />
          ) : (
            <button
              key={i}
              type="button"
              onClick={() => {
                item.onClick?.();
                closeContextMenu();
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                padding: "8px 10px",
                borderRadius: 6,
                border: "none",
                background: "transparent",
                color: item.danger ? "#EF4444" : "#E0E0E0",
                fontSize: 13,
                cursor: "pointer",
                textAlign: "left",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = item.danger
                  ? "rgba(239,68,68,0.12)"
                  : "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              {item.icon && (
                <span
                  style={{
                    width: 16,
                    height: 16,
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {item.icon}
                </span>
              )}
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.shortcut && (
                <span
                  style={{
                    color: "#7A7A7A",
                    fontSize: 11,
                    fontFamily: "monospace",
                  }}
                >
                  {item.shortcut}
                </span>
              )}
            </button>
          )
        )}
      </div>
    </>
  );
}
