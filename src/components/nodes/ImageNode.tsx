"use client";

import Image from "next/image";
import { ImageIcon } from "lucide-react";
import { Handle, Position, useViewport, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { ImageEditPanel } from "@/components/ImageEditPanel";
import { ImageToolbar } from "@/components/ImageToolbar";

export interface ImageNodeData extends Record<string, unknown> {
  filename: string;
  width: number;
  height: number;
  imageUrl: string;
  watermarkUrl?: string;
}

export type ImageNodeType = Node<ImageNodeData, "image">;

export function ImageNode({ data, selected }: NodeProps<ImageNodeType>) {
  const { filename, width, height, imageUrl, watermarkUrl } = data;
  const { zoom } = useViewport();

  return (
    <div
      className={cn(
        "group relative h-full w-full overflow-visible rounded-[4px] border bg-[#202020]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      {selected && <ImageToolbar />}
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-7 left-0 flex h-6 w-full items-center gap-1.5 text-[12px] text-[#828282]">
        <ImageIcon size={13} />
        <span className="min-w-0 flex-1 truncate">{filename}</span>
        <span className="shrink-0 tabular-nums">{width} × {height}</span>
      </div>

      <div className="relative h-full w-full overflow-hidden rounded-[3px]">
        <Image src={imageUrl} alt={filename} fill sizes="700px" className="object-cover" loading="eager" unoptimized />
        {watermarkUrl && (
          <Image
            src={watermarkUrl}
            alt=""
            width={48}
            height={23}
            className="pointer-events-none absolute left-1 top-1 h-[23px] w-12 object-contain opacity-90"
            unoptimized
          />
        )}
      </div>

      {selected && <ImageEditPanel zoom={zoom} />}
    </div>
  );
}
