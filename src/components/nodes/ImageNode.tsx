"use client";

import Image from "next/image";
import { ImageIcon } from "lucide-react";
import { Handle, Position, useViewport, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { ImageEditPanel } from "@/components/ImageEditPanel";
import { ImageToolbar, type ImageToolbarAction } from "@/components/ImageToolbar";
import { useCanvasStore } from "@/store/canvasStore";

export interface ImageNodeData extends Record<string, unknown> {
  filename: string;
  width: number;
  height: number;
  imageUrl: string;
  watermarkUrl?: string;
  editorVariant?: "empty" | "prompt" | "referenced" | "tool";
  prompt?: string;
  references?: string[];
  generationSettings?: string;
  portraitEnhanced?: boolean;
}

export type ImageNodeType = Node<ImageNodeData, "image">;

const derivedImageActions: Record<Exclude<ImageToolbarAction, "人像质感调节">, { filename: string; prompt: string }> = {
  "全景": { filename: "720°全景图", prompt: "以当前画面为中心，向左右自然延展为 720° 全景图，保持人物、光线和空间结构连续。" },
  "多角度": { filename: "多角度展示图", prompt: "保持主体造型一致，生成正面、侧面、背面和三分之二视角的多角度展示。" },
  "打光": { filename: "智能打光", prompt: "保持主体与构图不变，增强电影级侧逆光、轮廓光与自然环境反射。" },
  "九宫格": { filename: "九宫格分镜", prompt: "保持角色和场景连续，生成九宫格镜头探索图，覆盖景别与机位变化。" },
  "高清": { filename: "高清放大", prompt: "对当前图片进行高清修复与细节增强，保持原始构图和人物一致性。" },
  "宫格切分": { filename: "宫格切分结果", prompt: "将当前宫格图拆分为可独立引用的镜头素材。" },
};

export function ImageNode({ id, data, selected }: NodeProps<ImageNodeType>) {
  const { filename, width, height, imageUrl, watermarkUrl } = data;
  const { zoom } = useViewport();
  const addDerivedNode = useCanvasStore((state) => state.addDerivedNode);
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);
  const selectedNodeCount = useCanvasStore((state) => state.selectedNodeIds.length);
  const showSingleNodeEditor = selected && selectedNodeCount <= 1;

  const runAction = (action: ImageToolbarAction) => {
    if (action === "人像质感调节") {
      updateNodeData(id, { portraitEnhanced: !data.portraitEnhanced });
      return;
    }

    const derived = derivedImageActions[action];
    addDerivedNode(id, "image", {
      filename: derived.filename,
      width,
      height,
      imageUrl,
      watermarkUrl,
      editorVariant: "tool",
      prompt: derived.prompt,
      references: [imageUrl],
      generationSettings: data.generationSettings ?? "16:9 · 标准画质 · 2K · 1张",
    });
  };

  return (
    <div
      className={cn(
        "group relative h-full w-full overflow-visible rounded-[4px] border bg-[#202020]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      {showSingleNodeEditor && <ImageToolbar portraitEnhanced={Boolean(data.portraitEnhanced)} onAction={runAction} />}
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-7 left-0 flex h-6 w-full items-center gap-1.5 text-[12px] text-[#828282]">
        <ImageIcon size={13} />
        <span className="min-w-0 flex-1 truncate">{filename}</span>
        <span className="shrink-0 tabular-nums">{width} × {height}</span>
      </div>

      <div className="relative h-full w-full overflow-hidden rounded-[3px]">
        <Image
          src={imageUrl}
          alt={filename}
          fill
          sizes="700px"
          className={cn("object-cover transition-[filter] duration-300", data.portraitEnhanced && "contrast-[1.06] saturate-[1.08] brightness-[1.03]")}
          loading="eager"
          unoptimized
        />
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

      {showSingleNodeEditor && (
        <ImageEditPanel
          zoom={zoom}
          variant={data.editorVariant ?? "empty"}
          initialPrompt={data.prompt}
          initialReferences={data.references}
          generationSettings={data.generationSettings}
        />
      )}
    </div>
  );
}
