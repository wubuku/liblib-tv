"use client";

import { useUIStore } from "@/store/uiStore";

// Batch 105: 2026-09-05 源站 computed style——容器 fixed top-0 居中 z-[305]、
// opacity 过渡淡入淡出；子元素 rounded-b-xl 胶囊含「正在跟随/取消/按 ESC 退出」。
// 跟随的触发来自协作事件（源站采样为淡出态），clone 仅暴露状态与单层 ESC 退出。
export function FollowBanner() {
  const isFollowingSession = useUIStore((state) => state.isFollowingSession);
  const setFollowingSession = useUIStore((state) => state.setFollowingSession);

  return (
    <div
      data-follow-banner
      aria-hidden={!isFollowingSession}
      className="pointer-events-none fixed left-1/2 top-0 z-[305] -translate-x-1/2 motion-safe:transition-opacity motion-safe:duration-200"
      style={{ opacity: isFollowingSession ? 1 : 0 }}
    >
      <div
        className={cnBannerPill(isFollowingSession)}
      >
        <span className="text-sm">正在跟随</span>
        <button
          type="button"
          data-follow-cancel
          tabIndex={isFollowingSession ? 0 : -1}
          onClick={() => setFollowingSession(false)}
          className="rounded px-1 text-xs underline-offset-2 hover:underline"
        >
          取消<i className="not-italic text-[10px] opacity-70"> ESC</i>
        </button>
      </div>
      {isFollowingSession && (
        <div className="mt-1 flex justify-center">
          <span className="rounded-md bg-black/60 px-2 py-0.5 text-[11px] text-[#d0d0d0]">
            按 ESC 退出
          </span>
        </div>
      )}
    </div>
  );
}

function cnBannerPill(active: boolean) {
  return [
    "pointer-events-auto flex items-center gap-2 rounded-b-xl border border-white/10 bg-[#262626] px-3 py-1.5 text-white shadow-md",
    active ? "" : "pointer-events-none",
  ].join(" ");
}
