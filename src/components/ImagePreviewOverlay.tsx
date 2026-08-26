"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { ImagePreviewState } from "@/store/uiStore";

export function ImagePreviewOverlay({
  preview,
  onClose,
}: {
  preview: ImagePreviewState;
  onClose: () => void;
}) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const ratio = preview.width / preview.height;

  useEffect(() => {
    closeButtonRef.current?.focus({ preventScroll: true });
  }, []);

  return (
    <div
      data-image-preview-overlay
      role="dialog"
      aria-modal="true"
      aria-label={`${preview.filename}预览`}
      tabIndex={-1}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          onClose();
          return;
        }
        if (event.key === "Tab") {
          event.preventDefault();
          closeButtonRef.current?.focus();
        }
      }}
    >
      <div
        data-image-preview-content
        className="relative flex h-[80vh] w-[85vw] items-center justify-center"
      >
        <button
          ref={closeButtonRef}
          type="button"
          data-image-preview-close
          onClick={onClose}
          aria-label="关闭预览"
          title="关闭"
          className="absolute -right-3 -top-3 z-10 flex size-8 items-center justify-center rounded-lg bg-[#2a2a2a] text-[#ededed] shadow-[0_8px_28px_rgba(0,0,0,0.48)] hover:bg-[#383838]"
        >
          <X size={18} />
        </button>

        <div
          data-image-preview-media
          className="relative max-h-full max-w-full overflow-hidden"
          // The source constrains media by an 85vw x 80vh viewport while
          // preserving each image's intrinsic aspect ratio.
          style={{
            width: `min(100%, calc(80vh * ${ratio}))`,
            aspectRatio: `${preview.width} / ${preview.height}`,
          }}
        >
          <Image
            src={preview.imageUrl}
            alt={preview.filename}
            fill
            sizes="85vw"
            className="object-contain"
            loading="eager"
            unoptimized
          />
          {preview.watermarkUrl && (
            <Image
              data-image-preview-watermark
              src={preview.watermarkUrl}
              alt=""
              width={48}
              height={23}
              className="pointer-events-none absolute left-2.5 top-2.5 h-[23px] w-12 object-contain"
              unoptimized
            />
          )}
        </div>
      </div>
    </div>
  );
}
