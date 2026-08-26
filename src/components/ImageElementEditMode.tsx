"use client";

import { useState } from "react";
import {
  ImageElementEditSurface,
} from "@/components/ImageElementEditSurface";
import {
  ImageElementEditToolbar,
  type ImageElementEditTool,
} from "@/components/ImageElementEditToolbar";

interface ImageElementEditModeProps {
  zoom: number;
  onClose: () => void;
}

export function ImageElementEditMode({
  zoom,
  onClose,
}: ImageElementEditModeProps) {
  const [activeTool, setActiveTool] = useState<ImageElementEditTool>("point");
  const [brushSize, setBrushSize] = useState(4);

  return (
    <>
      <ImageElementEditToolbar
        activeTool={activeTool}
        brushSize={brushSize}
        onToolChange={setActiveTool}
        onBrushSizeChange={setBrushSize}
        onClose={onClose}
      />
      <ImageElementEditSurface activeTool={activeTool} zoom={zoom} />
    </>
  );
}

