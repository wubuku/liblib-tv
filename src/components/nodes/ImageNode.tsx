"use client";

import Image from "next/image";
import { useState } from "react";
import { ImageIcon } from "lucide-react";
import { Handle, Position, useViewport, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { ImageEditPanel, type ImageEditorHeight } from "@/components/ImageEditPanel";
import { ImageToolbar, type ImageToolbarAction } from "@/components/ImageToolbar";
import { ImageAnnotateSurface } from "@/components/ImageAnnotateSurface";
import { ImageElementEditMode } from "@/components/ImageElementEditMode";
import {
  ImageAnnotateToolbar,
  type ImageAnnotateTool,
} from "@/components/ImageAnnotateToolbar";
import {
  useCanvasStore,
  type DirectorCaptureMetadata,
  type VideoFrameCaptureMetadata,
} from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";

export interface ImageNodeData extends Record<string, unknown> {
  filename: string;
  width: number;
  height: number;
  imageUrl: string | null;
  watermarkUrl?: string;
  placeholderKind?: "panorama";
  editorVariant?: "empty" | "prompt" | "referenced" | "tool" | "panorama";
  editorHeight?: ImageEditorHeight;
  prompt?: string;
  references?: string[];
  generationSettings?: string;
  portraitEnhanced?: boolean;
  frameCapture?: VideoFrameCaptureMetadata;
  directorCapture?: DirectorCaptureMetadata;
}

export type ImageNodeType = Node<ImageNodeData, "image">;

const derivedImageActions: Partial<Record<ImageToolbarAction, { filename: string; prompt: string }>> = {
  "多角度": { filename: "多角度展示图", prompt: "保持主体造型一致，生成正面、侧面、背面和三分之二视角的多角度展示。" },
  "打光": { filename: "智能打光", prompt: "保持主体与构图不变，增强电影级侧逆光、轮廓光与自然环境反射。" },
  "九宫格": { filename: "九宫格分镜", prompt: "保持角色和场景连续，生成九宫格镜头探索图，覆盖景别与机位变化。" },
  "高清": { filename: "高清放大", prompt: "对当前图片进行高清修复与细节增强，保持原始构图和人物一致性。" },
  "宫格切分": { filename: "宫格切分结果", prompt: "将当前宫格图拆分为可独立引用的镜头素材。" },
};

export function ImageNode({ id, data, selected }: NodeProps<ImageNodeType>) {
  const { filename, width, height, imageUrl, watermarkUrl, frameCapture, directorCapture } = data;
  const { zoom } = useViewport();
  const addDerivedNode = useCanvasStore((state) => state.addDerivedNode);
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);
  const selectedNodeCount = useCanvasStore((state) => state.selectedNodeIds.length);
  const openImagePreview = useUIStore((state) => state.openImagePreview);
  const openImageAnnotate = useUIStore((state) => state.openImageAnnotate);
  const imageAnnotate = useUIStore((state) => state.imageAnnotate);
  const closeImageAnnotate = useUIStore((state) => state.closeImageAnnotate);
  const openImageElementEdit = useUIStore((state) => state.openImageElementEdit);
  const imageElementEdit = useUIStore((state) => state.imageElementEdit);
  const closeImageElementEdit = useUIStore((state) => state.closeImageElementEdit);
  const isAnnotating = selected && imageAnnotate?.nodeId === id && Boolean(imageUrl);
  const isElementEditing = selected && imageElementEdit?.nodeId === id && Boolean(imageUrl);
  const [activeAnnotateTool, setActiveAnnotateTool] = useState<ImageAnnotateTool>("pencil");
  const [annotateColor, setAnnotateColor] = useState("#ff0000");
  const [annotateStrokeWidth, setAnnotateStrokeWidth] = useState(4);
  const showSingleNodeEditor = selected && selectedNodeCount <= 1 && !isAnnotating && !isElementEditing;

  const runAction = (action: ImageToolbarAction) => {
    if (action === "人像质感调节") {
      updateNodeData(id, { portraitEnhanced: !data.portraitEnhanced });
      return;
    }

    if (!imageUrl) return;

    if (action === "预览") {
      openImagePreview({
        nodeId: id,
        filename,
        imageUrl,
        watermarkUrl,
        width,
        height,
      });
      return;
    }

    if (action === "标注") {
      openImageAnnotate({
        nodeId: id,
        filename,
        imageUrl,
        width,
        height,
      });
      return;
    }

    if (action === "元素编辑") {
      openImageElementEdit({
        nodeId: id,
        filename,
        imageUrl,
        width,
        height,
      });
      return;
    }

    if (action === "全景") {
      addDerivedNode(
        id,
        "image",
        {
          filename: "720°全景图",
          width: 700,
          height: 350,
          imageUrl: null,
          watermarkUrl: undefined,
          placeholderKind: "panorama",
          editorVariant: "panorama",
          editorHeight: 252,
          references: [imageUrl],
          generationSettings: "2:1 · 标准画质 · 2K · 1张",
        },
        {
          dimensions: { width: 700, height: 350 },
          offset: { x: 120, y: -110 },
        },
      );
      return;
    }

    const derived = derivedImageActions[action];
    if (!derived) return;
    addDerivedNode(id, "image", {
      filename: derived.filename,
      width,
      height,
      imageUrl,
      watermarkUrl,
      editorVariant: "tool",
      editorHeight: 274,
      prompt: derived.prompt,
      references: [imageUrl],
      generationSettings: data.generationSettings ?? "16:9 · 标准画质 · 2K · 1张",
    });
  };

  return (
    <div
      {...(frameCapture
        ? {
            "data-video-frame-capture": true,
            "data-video-frame-capture-kind": frameCapture.kind,
            "data-video-frame-source-id": frameCapture.sourceNodeId,
            "data-video-frame-capture-seconds": frameCapture.captureSeconds,
            "data-video-frame-edge-id": frameCapture.edgeId,
            "data-video-frame-name": frameCapture.name,
            "data-video-frame-alt": frameCapture.alt,
          }
        : {})}
      {...(directorCapture
        ? {
            "data-director-capture-node": true,
            "data-director-capture-id": directorCapture.captureId,
            "data-director-capture-source-id": directorCapture.sourceNodeId,
            "data-director-capture-camera-id": directorCapture.cameraId ?? "",
            "data-director-capture-aspect": directorCapture.aspectRatio,
            "data-director-capture-edge-id": directorCapture.edgeId,
          }
        : {})}
      className={cn(
        "group relative h-full w-full overflow-visible rounded-[4px] border bg-[#202020]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      {showSingleNodeEditor && (
        <ImageToolbar
          zoom={zoom}
          portraitEnhanced={Boolean(data.portraitEnhanced)}
          onAction={runAction}
        />
      )}
      {isAnnotating && (
        <ImageAnnotateToolbar
          activeTool={activeAnnotateTool}
          color={annotateColor}
          strokeWidth={annotateStrokeWidth}
          onToolChange={setActiveAnnotateTool}
          onColorChange={setAnnotateColor}
          onStrokeWidthChange={setAnnotateStrokeWidth}
          onClose={closeImageAnnotate}
        />
      )}
      {isElementEditing && (
        <ImageElementEditMode zoom={zoom} onClose={closeImageElementEdit} />
      )}
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-7 left-0 flex h-6 w-full items-center gap-1.5 text-[12px] text-[#828282]">
        <ImageIcon size={13} />
        <span className="min-w-0 flex-1 truncate">{filename}</span>
        <span className="shrink-0 tabular-nums">{width} × {height}</span>
      </div>

      <div data-image-node-media className="relative h-full w-full overflow-hidden rounded-[3px]">
        {data.placeholderKind === "panorama" || !imageUrl ? (
          <div
            data-image-placeholder={data.placeholderKind ?? "empty"}
            className="flex h-full w-full items-center justify-center bg-[#212121] text-[#666]"
          >
            <ImageIcon size={38} strokeWidth={1.2} />
          </div>
        ) : (
          <Image
            src={imageUrl}
            alt={frameCapture?.alt ?? filename}
            fill
            sizes="700px"
            className={cn("object-cover transition-[filter] duration-300", data.portraitEnhanced && "contrast-[1.06] saturate-[1.08] brightness-[1.03]")}
            loading="eager"
            unoptimized
          />
        )}
        {imageUrl && watermarkUrl && (
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

      {isAnnotating && <ImageAnnotateSurface activeTool={activeAnnotateTool} />}

      {showSingleNodeEditor && (
        <ImageEditPanel
          zoom={zoom}
          variant={data.editorVariant ?? "empty"}
          panelHeight={data.editorHeight}
          initialPrompt={data.prompt}
          initialReferences={data.references}
          generationSettings={data.generationSettings}
        />
      )}
    </div>
  );
}
