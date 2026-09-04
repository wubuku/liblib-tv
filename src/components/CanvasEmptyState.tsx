"use client";

import { MousePointerClick } from "lucide-react";
import { useState } from "react";

// Batch 100: 芯片命名/角标来自 2026-09-05 源站空画布审计；点击流未采样，
// clone 只提供诚实本地反馈，不伪造生成。
const quickChips = [
  { id: "story-script", label: "故事脚本生成", badge: "" },
  { id: "character-turnaround", label: "角色三视图", badge: "" },
  { id: "reference-to-video", label: "全能参考生视频", badge: "SD 2.5" },
  { id: "audio-to-video", label: "音频生视频", badge: "SD 2.5" },
];

export function CanvasEmptyState() {
  const [status, setStatus] = useState("");

  return (
    <div
      data-canvas-empty-state
      className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center gap-9"
    >
      <div className="flex items-center gap-1.5 text-sm text-[#8f8f8f]">
        <MousePointerClick size={16} className="text-[#bdbdbd]" />
        <span>双击画布</span>
        <span>自由生成节点</span>
      </div>
      <div className="pointer-events-auto flex max-w-[92vw] flex-wrap items-center justify-center gap-3">
        {quickChips.map((chip) => (
          <button
            key={chip.id}
            type="button"
            data-canvas-empty-chip={chip.id}
            onClick={() => setStatus("本地原型：快速生成入口未接入")}
            className="flex h-12 items-center gap-2.5 rounded-xl border border-white/[0.08] bg-[#1d1d1d]/90 px-5 text-sm text-[#ededed] shadow-[0_10px_28px_rgba(0,0,0,0.45)] transition-colors hover:border-white/[0.16] hover:bg-[#232323]"
          >
            <span>{chip.label}</span>
            {chip.badge && (
              <span className="rounded bg-[#223038] px-1.5 py-0.5 text-[10px] leading-none text-[#6ecbe8]">
                {chip.badge}
              </span>
            )}
          </button>
        ))}
      </div>
      {status && (
        <p data-canvas-empty-status className="pointer-events-auto text-xs text-[#75d7e8]">
          {status}
        </p>
      )}
    </div>
  );
}
