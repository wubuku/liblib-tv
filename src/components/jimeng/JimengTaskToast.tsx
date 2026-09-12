"use client";

import { useEffect } from "react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 全局 toast (Batch 40)。
 * 源站提交生成任务后会显示任务反馈；未提取到确切样式 (副作用 BLOCKED)，
 * 按站点视觉语言做顶部居中深色药丸 toast，2.5s 后由调用方清除。
 */
export function JimengTaskToast() {
  const toast = useJimengStore((s) => s.toast);
  const clearToast = useJimengStore((s) => s.clearToast);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => clearToast(), 2500);
    return () => window.clearTimeout(timer);
  }, [toast, clearToast]);

  if (!toast) return null;

  return (
    <div
      role="status"
      className="fixed left-1/2 top-16 z-[300] -translate-x-1/2 rounded-lg px-4 py-2 text-[13px] text-white"
      style={{
        background: "rgb(38,38,38)",
        boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
      }}
    >
      {toast}
    </div>
  );
}
