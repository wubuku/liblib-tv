"use client";

import { Waves } from "lucide-react";

/**
 * 右下角「与 AI 对话」按钮 — 1548,778 120×36 (SOURCE_FACT)。
 * bg rgba(39,39,39,0.72) + 顶部高光渐变叠加 (渐变色值截断，CLONE_DECISION 近似)。
 */
export function JimengAiButton() {
  return (
    <div className="absolute bottom-3 right-3 z-30 flex flex-col items-end">
      <div className="relative inline-flex h-9 items-center justify-center overflow-hidden rounded-lg bg-[rgba(39,39,39,0.72)]">
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(138,196,220,0.18) 0%, rgba(138,196,220,0.02) 100%)",
          }}
        />
        <button
          type="button"
          className="relative z-[1] inline-flex h-[34px] w-[118px] items-center justify-center gap-1 whitespace-nowrap text-[13px] font-medium text-white"
        >
          <Waves size={16} className="text-[#7FD8C9]" />
          与 AI 对话
        </button>
      </div>
    </div>
  );
}
