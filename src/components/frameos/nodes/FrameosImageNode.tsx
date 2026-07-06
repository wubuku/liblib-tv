"use client";

import type { NodeProps } from "@xyflow/react";
import { useState } from "react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { ImageNodeIcon, Upload2Icon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

export function FrameosImageNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const { title, imageUrl } = data;
  const [isHovered, setIsHovered] = useState(false);
  const isPortrait = (data as { orientation?: string }).orientation === "portrait";

  return (
    <FrameosNodeShell
      kind="image"
      title={title}
      titleIcon={<ImageNodeIcon size={12} />}
      selected={selected}
      showLeftHandle
      showRightHandle
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={isPortrait ? 225 : 300}
      height={isPortrait ? 300 : 169}
    >
      <div
        className="card-body"
        style={{
          flex: 1,
          position: "relative",
          background: "rgba(0,0,0,0.3)",
          borderRadius: 9,
          overflow: "hidden",
          minHeight: 0,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              display: "block",
              transition: "transform 0.3s",
              transform: isHovered ? "scale(1.02)" : "scale(1)",
            }}
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#5A5A5A",
            }}
          >
            <ImageNodeIcon size={32} />
          </div>
        )}

        {/* hover 时的暗罩 + 编辑提示 */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            opacity: isHovered && !selected ? 1 : 0,
            transition: "opacity 0.15s",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            pointerEvents: isHovered ? "auto" : "none",
          }}
        >
          <button
            type="button"
            style={{
              padding: "6px 12px",
              background: "rgba(0,0,0,0.7)",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRadius: 8,
              color: "#FFFFFF",
              fontSize: 12,
              cursor: "pointer",
              backdropFilter: "blur(4px)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            预览
          </button>
          <button
            type="button"
            style={{
              padding: "6px 12px",
              background: "rgba(59,130,246,0.9)",
              border: "1px solid rgba(96,165,250,0.5)",
              borderRadius: 8,
              color: "#FFFFFF",
              fontSize: 12,
              cursor: "pointer",
              backdropFilter: "blur(4px)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            编辑
          </button>
        </div>

        {/* 右上角替换内容按钮 - 仅 hover 或选中时显示 */}
        <div
          className="card-body-actions"
          style={{
            position: "absolute",
            top: 6,
            right: 6,
            zIndex: 2,
            opacity: isHovered || selected ? 1 : 0,
            transition: "opacity 0.15s",
          }}
        >
          <button
            type="button"
            aria-label="替换内容"
            className="node-content-replace"
            onClick={(e) => {
              e.stopPropagation();
              const input = document.createElement("input");
              input.type = "file";
              input.accept = "image/*";
              input.click();
            }}
            style={{
              width: 22,
              height: 22,
              borderRadius: 6,
              background: "rgba(0,0,0,0.7)",
              border: "1px solid rgba(255,255,255,0.12)",
              boxShadow: "rgba(0,0,0,0.3) 0 4px 12px 0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#FFFFFF",
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s, transform 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(0,0,0,0.9)";
              e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)";
              e.currentTarget.style.transform = "scale(1.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(0,0,0,0.7)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
              e.currentTarget.style.transform = "scale(1)";
            }}
          >
            <Upload2Icon size={12} />
          </button>
        </div>
      </div>
    </FrameosNodeShell>
  );
}
