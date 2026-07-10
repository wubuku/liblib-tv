"use client";

import type { NodeProps } from "@xyflow/react";
import { useState } from "react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import {
  FilmNodeIcon,
  PlayFillIcon,
  PauseFillIcon,
  Upload2Icon,
  ErrorWarningIcon,
} from "../icons";
import type { FrameosNode } from "@/types/frameos";
import { useFrameosStore } from "@/store/frameosStore";

export function FrameosVideoNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const { title, imageUrl, reviewFailed } = data;
  const [isPlaying, setIsPlaying] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const videoUrl = imageUrl ? imageUrl.replace(/\?x-oss-process=.*$/, "") : undefined;

  const titleRight = reviewFailed ? (
    <span
      className="node-floating-title__binding-hint"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        color: "#F59E0B",
        fontSize: 12,
        fontWeight: 500,
        lineHeight: "20px",
      }}
    >
      <ErrorWarningIcon size={12} color="#F59E0B" />
      <span>审核未通过</span>
    </span>
  ) : undefined;

  return (
    <FrameosNodeShell
      kind="video"
      title={title}
      titleIcon={<FilmNodeIcon size={12} />}
      titleRight={titleRight}
      selected={selected}
      showLeftHandle
      showRightHandle
      showResizeHandle={false}
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={300}
      height={169}
    >
      <div
        className="card-body"
        style={{
          flex: 1,
          position: "relative",
          background: "#1C1C1C",
          borderRadius: 10,
          overflow: "hidden",
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {isPlaying && videoUrl && !videoError ? (
          <video
            src={videoUrl}
            autoPlay
            loop
            muted
            playsInline
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              display: "block",
              background: "#000",
            }}
            onClick={(e) => e.stopPropagation()}
            onDoubleClick={(e) => {
              e.stopPropagation();
              setIsPlaying(false);
            }}
            onError={() => {
              setVideoError(true);
              setIsPlaying(false);
            }}
          />
        ) : imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              display: "block",
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
            <FilmNodeIcon size={32} />
          </div>
        )}

        {/* 中心播放/暂停按钮 - hover 时显示 */}
        <button
          type="button"
          aria-label={isPlaying ? "暂停视频" : "播放视频"}
          className="vid-play-btn"
          onClick={(e) => {
            e.stopPropagation();
            setIsPlaying((v) => !v);
          }}
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 44,
            height: 44,
            background: isPlaying
              ? "rgba(0,0,0,0.7)"
              : "rgba(0,0,0,0.5)",
            backdropFilter: "blur(4px)",
            border: "1px solid rgba(255,255,255,0.2)",
            borderRadius: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#FFFFFF",
            cursor: "pointer",
            opacity: 1,
            transition: "all 0.15s",
            boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translate(-50%, -50%) scale(1.1)";
            e.currentTarget.style.background = "rgba(0,0,0,0.8)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translate(-50%, -50%) scale(1)";
            e.currentTarget.style.background = isPlaying
              ? "rgba(0,0,0,0.7)"
              : "rgba(0,0,0,0.5)";
          }}
        >
          {isPlaying ? <PauseFillIcon size={20} /> : <PlayFillIcon size={20} />}
        </button>

        {/* 右上角替换内容按钮 - 始终可见 (与原站 frameos.cn 一致) */}
        <div
          className="card-body-actions"
          style={{
            position: "absolute",
            top: 6,
            right: 6,
            zIndex: 1,
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
              input.accept = "video/*,image/*";
              input.onchange = () => {
                const file = input.files?.[0];
                if (!file) return;
                const url = URL.createObjectURL(file);
                useFrameosStore.getState().updateNodeData(id, {
                  imageUrl: url,
                  ...(file.type.startsWith("video/") ? {} : { reviewFailed: false }),
                });
              };
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
