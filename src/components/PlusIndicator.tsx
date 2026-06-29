"use client";

import { cn } from "@/lib/utils";

/**
 * Replicates LibTV's connection indicator "+" icon:
 * - 42×42px rounded circle
 * - transparent background (no fill)
 * - light gray border
 * - "+" icon in center (same color as border)
 * - pointer-events: none (visible only)
 */
export function PlusIndicator({ side }: { side: "left" | "right" }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center",
        "w-[42px] h-[42px] rounded-full",
        "border border-[#525252]",
        "bg-transparent",
        "pointer-events-none",
        side === "left"
          ? "absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2"
          : "absolute right-0 top-1/2 translate-x-1/2 -translate-y-1/2"
      )}
      aria-hidden="true"
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 14 14"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M7 1V13M1 7H13"
          stroke="#525252"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}