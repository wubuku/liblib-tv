"use client";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 任务提交 toast (Batch 11, CLONE_DECISION)。
 * 源站提交智能超清/补帧后会显示任务反馈；未提取到确切样式 (副作用 BLOCKED)，
 * 按站点视觉语言做顶部居中深色药丸 toast。自动消失用 CSS 动画 (2.5s forwards)，
 * 避免 effect 内 setState (react-compiler lint 规则)。
 */
export function JimengTaskToast() {
  const tasks = useJimengStore((s) => s.tasks);
  const latest = tasks[tasks.length - 1];

  if (!latest) return null;

  return (
    <div
      key={latest.id}
      role="status"
      className="fixed left-1/2 top-16 z-[300] -translate-x-1/2 rounded-lg px-4 py-2 text-[13px] text-white"
      style={{
        background: "rgb(38,38,38)",
        boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
        animation: "jimeng-toast-hide 2.5s ease-in forwards",
      }}
    >
      {latest.kind === "upscale" ? "智能超清" : "补帧"}
      任务已提交（mock），处理中…
    </div>
  );
}
