"use client";

import type { ImageElementEditTool } from "@/components/ImageElementEditToolbar";

interface ImageElementEditSurfaceProps {
  activeTool: ImageElementEditTool;
  zoom: number;
}

export function ImageElementEditSurface({
  activeTool,
  zoom,
}: ImageElementEditSurfaceProps) {
  const safeZoom = Math.max(0.1, zoom);
  const recordHeight = 50 / safeZoom;
  const screenGap = 12 / safeZoom;
  const extraHeight = recordHeight + screenGap;

  return (
    <div
      data-image-element-edit-mode
      className="nodrag nowheel nopan pointer-events-none absolute left-0 top-0 z-30 w-full overflow-visible"
      style={{ height: `calc(100% + ${extraHeight}px)` }}
    >
      <div
        data-image-element-edit-stage
        data-image-element-edit-tool={activeTool}
        className="nodrag nowheel nopan pointer-events-auto absolute left-0 top-0 w-full overflow-hidden rounded-[3px] border border-white/20"
        style={{ height: `calc(100% - ${extraHeight}px)` }}
        onPointerDown={(event) => event.stopPropagation()}
        onPointerMove={(event) => event.stopPropagation()}
        onPointerUp={(event) => event.stopPropagation()}
      >
        <div
          data-image-element-edit-mask
          className="absolute inset-0 flex items-center justify-center bg-black/45"
        >
          <span
            data-image-element-edit-guide
            className="rounded-md bg-black/45 px-3 py-1.5 text-center text-[12px] text-white/90"
          >
            标记你想要修改的对象
          </span>
        </div>
      </div>

      <div
        data-image-element-edit-record-panel
        className="pointer-events-auto absolute left-1/2 top-[calc(100%_-_var(--element-edit-extra-height))] w-[400px] origin-top rounded-xl border border-[#363636] bg-[#262626] shadow-[0_12px_32px_rgba(0,0,0,0.42)]"
        style={{
          "--element-edit-extra-height": `${extraHeight}px`,
          marginTop: `${screenGap}px`,
          transform: `translateX(-50%) scale(${1 / safeZoom})`,
        } as React.CSSProperties}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
      >
        <div
          data-image-element-edit-empty
          className="flex h-[50px] items-center justify-center text-[13px] text-[#8e8e8e]"
        >
          编辑内容待添加
        </div>
        <button
          type="button"
          data-image-element-edit-generate
          disabled
          aria-label="生成元素编辑结果"
          className="sr-only"
        >
          生成
        </button>
      </div>
    </div>
  );
}

