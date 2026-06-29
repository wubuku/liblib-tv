"use client";

import { cn } from "@/lib/utils";

/**
 * Replicates LibTV's connection indicator "+" icon exactly:
 *
 * - 42×42px wrapper, positioned at horizontal distance ~21px from the node border
 * - Inside: a 20×20 SVG circle with "+" inside
 * - For LEFT indicator: SVG is translated +25px from wrapper center
 *   (i.e. the "+" icon sits to the RIGHT side of the wrapper, near the node)
 * - For RIGHT indicator: SVG is translated -25px from wrapper center
 *   (i.e. the "+" icon sits to the LEFT side of the wrapper, near the node)
 *
 * Color: SVG uses --canvas-handle-bg for fill and --canvas-handle-icon for
 * stroke / "+" path. We approximate these with our local palette.
 */
export function PlusIndicator({ side }: { side: "left" | "right" }) {
  const isLeft = side === "left";
  return (
    <div
      className={cn(
        "flex items-center justify-center",
        "w-[42px] h-[42px] rounded-full",
        "bg-transparent",
        "pointer-events-none",
        "absolute top-1/2 -translate-y-1/2",
        isLeft
          ? // Wrapper center sits ~21px to the LEFT of the node border
            "left-0 -translate-x-[calc(100%+0px)]"
          : "right-0 translate-x-[calc(100%+0px)]"
      )}
      // The wrapper's left/right edge is exactly 21px from the node border,
      // so the wrapper CENTER is 0px from the node edge (half a wrapper width).
      // Re-anchor via a precise transform so the wrapper appears ~21px out.
      style={{
        // Wrapper's center should be 21px away from node edge
        // i.e. wrapper left/right edge is at distance 0 (touching offset),
        // wrapper center 21px out → translate(±100%, 0) places edge at 0,
        // then translate ±21px more puts center at ±21px.
        transform: isLeft
          ? "translate(calc(-100% - 21px), -50%)"
          : "translate(calc(100% + 21px), -50%)",
      }}
      aria-hidden="true"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          // Inner "+" icon translated toward the node: ±25px
          transform: isLeft ? "translate(25px, 0)" : "translate(-25px, 0)",
        }}
      >
        <circle
          cx="10"
          cy="10"
          r="9.35"
          fill="#1f1f1f"
          stroke="#86909c"
          strokeWidth="1.2"
        />
        <path
          d="M10 6.5v7M6.5 10h7"
          stroke="#c0c8d0"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}