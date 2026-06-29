"use client";

import { cn } from "@/lib/utils";

/**
 * Replicates LibTV's "+" visual indicator that appears on node hover.
 *
 * Important design points (matching the original site):
 * - Purely decorative visual — the React Flow `<Handle>` (which is 0×0 and
 *   sits on the node border) is what accepts drag/click for connections.
 * - This component does NOT block pointer events, so the handle stays clickable.
 * - Sits ~8px outside the node border so the icon is clearly visible without
 *   making the node hard to click/drag.
 * - Circle has fill #1f1f1f + stroke #86909c, with a "+" glyph in #c0c8d0.
 */
export function PlusIndicator({ side }: { side: "left" | "right" }) {
  const isLeft = side === "left";
  return (
    <div
      className={cn(
        "absolute top-1/2 -translate-y-1/2",
        "pointer-events-none", // do NOT block the handle hit-area on the border
        "flex items-center justify-center",
        "w-[24px] h-[24px] rounded-full",
        "bg-[#1f1f1f]",
        "border border-[#86909c]",
        isLeft ? "left-0 -translate-x-[calc(100%+10px)]" : "right-0 translate-x-[calc(100%+10px)]"
      )}
      aria-hidden="true"
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10 6.5v7M6.5 10h7"
          stroke="#c0c8d0"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}