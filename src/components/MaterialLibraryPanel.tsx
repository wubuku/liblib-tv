"use client";

import { Aperture, Box } from "lucide-react";

interface MaterialLibraryPanelProps {
  onClose: () => void;
}

const entries = [
  { label: "风格库", description: "新增风格节点", icon: Box },
  { label: "特效库", description: "新增特效节点", icon: Aperture },
] as const;

export function MaterialLibraryPanel({ onClose }: MaterialLibraryPanelProps) {
  return (
    <section
      aria-label="素材库"
      className="fixed bottom-[73px] left-[calc(50%-24px)] z-[62] h-[163px] w-[240px] -translate-x-1/2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-1/2"
    >
      <h2 className="px-2 py-1 text-sm font-medium text-[#929292]">素材库</h2>
      <div className="mt-[9px] space-y-1">
        {entries.map((entry) => {
          const Icon = entry.icon;
          return (
            <button
              key={entry.label}
              type="button"
              onClick={onClose}
              className="flex h-[52px] w-full items-center gap-2 rounded-xl px-2 text-left hover:bg-white/[0.06]"
            >
              <span className="flex size-8 shrink-0 items-center justify-center text-[#ededed]">
                <Icon size={20} strokeWidth={1.6} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm text-[#eeeeee]">{entry.label}</span>
                <span className="block text-[11px] text-[#777]">{entry.description}</span>
              </span>
              <span className="rounded-full bg-white/[0.06] px-2 py-1 text-[10px] text-[#777]">NEW</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
