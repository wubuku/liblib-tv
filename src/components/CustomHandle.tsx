"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Handle, Position, type HandleProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

interface CustomHandleProps extends Omit<HandleProps, 'style'> {
  showOnHover?: boolean;
}

export function CustomHandle({ showOnHover = true, ...props }: CustomHandleProps) {
  const [isNear, setIsNear] = useState(false);
  const handleRef = useRef<HTMLDivElement>(null);
  const nodeRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Find the parent node element
    const handleEl = handleRef.current;
    if (!handleEl) return;

    const nodeEl = handleEl.closest('[data-testid*="rf__node"]');
    if (!nodeEl) return;
    nodeRef.current = nodeEl as HTMLElement;

    const handleMouseMove = (e: MouseEvent) => {
      if (!nodeRef.current) return;
      const rect = nodeRef.current.getBoundingClientRect();
      const mouseX = e.clientX;
      const mouseY = e.clientY;

      // Check if mouse is near the left or right edge
      const edgeThreshold = 30; // pixels from edge
      const isNearLeft = mouseX >= rect.left - edgeThreshold && mouseX <= rect.left + edgeThreshold;
      const isNearRight = mouseX >= rect.right - edgeThreshold && mouseX <= rect.right + edgeThreshold;
      const isInVerticalMiddle = mouseY >= rect.top + rect.height * 0.2 && mouseY <= rect.bottom - rect.height * 0.2;

      setIsNear((isNearLeft || isNearRight) && isInVerticalMiddle);
    };

    const handleMouseLeave = () => {
      setIsNear(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    nodeEl.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      nodeEl.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div ref={handleRef} className="relative">
      {/* Invisible handle for React Flow interaction */}
      <Handle
        {...props}
        style={{
          width: isNear ? 20 : 0,
          height: isNear ? 20 : 0,
          opacity: isNear ? 1 : 0,
          pointerEvents: 'auto',
        }}
      />

      {/* Visible "+" indicator */}
      {showOnHover && isNear && (
        <div
          className={cn(
            "absolute z-50 flex items-center justify-center",
            "w-5 h-5 rounded-full bg-[#09caf5] border-2 border-[#171717]",
            "transform -translate-x-1/2 -translate-y-1/2",
            "pointer-events-none",
            "transition-all duration-150 ease-in-out",
            "shadow-[0_0_8px_rgba(9,202,245,0.5)]"
          )}
          style={{
            left: props.position === Position.Left ? 0 : undefined,
            right: props.position === Position.Right ? 0 : undefined,
            top: '50%',
          }}
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M5 1V9M1 5H9" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
      )}
    </div>
  );
}
