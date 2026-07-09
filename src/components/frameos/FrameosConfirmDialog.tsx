"use client";

import { CloseIcon } from "./icons";

/**
 * FrameOS 确认对话框 - 用于删除节点/边的二次确认
 * - 与原站 frameos.cn 一致: 模态居中, 半透明遮罩, 取消/确定按钮
 */
export function FrameosConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "确定",
  cancelLabel = "取消",
  danger,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(4px)",
          zIndex: 6000,
        }}
        onClick={onCancel}
      />
      <div
        role="dialog"
        aria-label={title}
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 6001,
          width: 360,
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 12,
          padding: 20,
          boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
          animation: "frameos-pop-in 0.15s ease-out",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <h2 style={{ color: "#FFFFFF", fontSize: 16, fontWeight: 600, margin: 0 }}>
            {title}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="关闭"
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
            <CloseIcon size={14} />
          </button>
        </div>
        {message && (
          <p style={{ color: "#A3A3A3", fontSize: 13, margin: "0 0 16px", lineHeight: 1.5 }}>
            {message}
          </p>
        )}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: "8px 16px",
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 6,
              color: "#E0E0E0",
              fontSize: 13,
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            style={{
              padding: "8px 16px",
              background: danger ? "#DC2626" : "#3B82F6",
              border: "none",
              borderRadius: 6,
              color: "#FFFFFF",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </>
  );
}
