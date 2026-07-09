"use client";

import { useEffect, useState } from "react";

interface ToastItem {
  id: number;
  message: string;
  variant: "success" | "info" | "warning" | "danger";
}

let nextId = 1;
let setter: ((t: ToastItem[] | ((p: ToastItem[]) => ToastItem[])) => void) | null = null;
let currentToasts: ToastItem[] = [];

export function showToast(
  message: string,
  variant: ToastItem["variant"] = "info"
) {
  const id = nextId++;
  currentToasts = [...currentToasts, { id, message, variant }];
  setter?.([...currentToasts]);
  // 3 秒后自动消失
  setTimeout(() => {
    currentToasts = currentToasts.filter((t) => t.id !== id);
    setter?.([...currentToasts]);
  }, 3000);
}

// 全局事件: 允许跨组件触发 toast
if (typeof window !== "undefined" && !(window as any).__frameosToastListenerInstalled) {
  window.addEventListener("frameos-toast", (e: Event) => {
    const detail = (e as CustomEvent).detail;
    if (detail?.message) {
      showToast(detail.message, detail.variant);
    }
  });
  (window as any).__frameosToastListenerInstalled = true;
}

export function FrameosToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    setter = setToasts;
    return () => {
      setter = null;
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 80,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 6000,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        pointerEvents: "none",
      }}
    >
      {toasts.map((t) => {
        const colors = {
          success: { bg: "rgba(34,197,94,0.16)", border: "rgba(34,197,94,0.4)", text: "#22C55E" },
          info: { bg: "rgba(59,130,246,0.16)", border: "rgba(59,130,246,0.4)", text: "#60A5FA" },
          warning: { bg: "rgba(245,158,11,0.16)", border: "rgba(245,158,11,0.4)", text: "#F59E0B" },
          danger: { bg: "rgba(239,68,68,0.16)", border: "rgba(239,68,68,0.4)", text: "#EF4444" },
        }[t.variant];
        return (
          <div
            key={t.id}
            style={{
              background: "rgba(20,20,20,0.95)",
              backdropFilter: "blur(8px)",
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: "8px 14px",
              color: colors.text,
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              gap: 8,
              boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
              pointerEvents: "auto",
              animation: "frameos-toast-in 0.2s ease-out",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: 3,
                background: colors.text,
              }}
            />
            <span style={{ color: "#FFFFFF" }}>{t.message}</span>
          </div>
        );
      })}
    </div>
  );
}
