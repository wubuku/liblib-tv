"use client";

import { useEffect, useRef } from "react";
import type { ImageAnnotateTool } from "@/components/ImageAnnotateToolbar";

interface ImageAnnotateSurfaceProps {
  activeTool: ImageAnnotateTool;
}

export function ImageAnnotateSurface({ activeTool }: ImageAnnotateSurfaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateBackingSize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(1, Math.round(rect.width * 2));
      canvas.height = Math.max(1, Math.round(rect.height * 2));
    };

    updateBackingSize();
    const observer = new ResizeObserver(updateBackingSize);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      data-image-annotate-surface
      data-image-annotate-tool={activeTool}
      className="nodrag nowheel nopan absolute inset-0 z-10 cursor-crosshair"
      onPointerDown={(event) => event.stopPropagation()}
      onPointerMove={(event) => event.stopPropagation()}
      onPointerUp={(event) => event.stopPropagation()}
    >
      <canvas
        ref={canvasRef}
        data-image-annotate-canvas
        data-image-annotate-dpr="2"
        aria-label="图片标注画布"
        className="block size-full"
      />
    </div>
  );
}

