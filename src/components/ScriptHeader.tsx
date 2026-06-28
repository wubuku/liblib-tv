"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export function ScriptHeader() {
  const [title] = useState("第一集：咖啡馆对峙");

  return (
    <div
      className="fixed top-[60px] left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-3 py-1.5 bg-[rgba(31,31,31,0.85)] backdrop-blur-md border border-[#363636] rounded-xl shadow-lg"
    >
      {/* Document/script icon */}
      <svg
        width="14"
        height="14"
        viewBox="0 0 14 14"
        fill="none"
        className="text-[#f7f7f7]"
      >
        <rect
          x="2"
          y="1"
          width="10"
          height="12"
          rx="1.5"
          stroke="currentColor"
          strokeWidth="1.2"
        />
        <path
          d="M4 4h6M4 7h6M4 10h3"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
        />
      </svg>

      {/* Title */}
      <span className="text-sm text-[#f7f7f7] font-medium">{title}</span>

      {/* Connection handles indicator (left + right dots) */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-[#363636]">
        <span
          className={cn(
            "w-2 h-2 rounded-full bg-[#09caf5] border border-[#171717]",
            "transition-all"
          )}
        />
        <span
          className={cn(
            "w-2 h-2 rounded-full bg-[#09caf5] border border-[#171717]",
            "transition-all"
          )}
        />
      </div>
    </div>
  );
}