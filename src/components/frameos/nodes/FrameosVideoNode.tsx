"use client";

import type { NodeProps } from "@xyflow/react";
import { useEffect, useState } from "react";
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
  const [, setIsHovered] = useState(false); // 占位, 保留 onMouseEnter/Leave 用于未来 hover-only UI
  const [videoError, setVideoError] = useState(false);
  // Batch 225: 内容视频节点左下角时长徽章 (源站 00:04 样式, 读 metadata);
  // 仅真视频源 (blob:/扩展名) 可读时长, jpg 封面 mock 不显示徽章。
  // 用 detached <video> 拉元数据 — display:none 元素在 Chromium 里不触发加载
  const [durationLabel, setDurationLabel] = useState<string | null>(null);
  const videoUrl = imageUrl ? imageUrl.replace(/\?x-oss-process=.*$/, "") : undefined;
  const isVideoSource =
    !!videoUrl &&
    (videoUrl.startsWith("blob:") ||
      /\.(mp4|webm|mov|m4v)(\?|$)/i.test(videoUrl));

  const formatDuration = (seconds: number): string => {
    if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  useEffect(() => {
    if (!isVideoSource || !videoUrl) return undefined;
    const probe = document.createElement("video");
    probe.preload = "metadata";
    probe.muted = true;
    probe.onloadedmetadata = () =>
      setDurationLabel(formatDuration(probe.duration));
    probe.src = videoUrl;
    return () => {
      probe.onloadedmetadata = null;
      probe.removeAttribute("src");
    };
  }, [isVideoSource, videoUrl]);

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
      // Batch 225: 内容视频节点仅右侧 handle (2026-09-25 源站实测);
      // 空视频节点保留左右 handle
      showLeftHandle={!imageUrl}
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
          // Batch 345: 画布节点位图按节点尺寸动态缩放，保留 img（FrameOS 路线）。
          // eslint-disable-next-line @next/next/no-img-element
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
              color: "#8C8C8C",
            }}
          >
            <FilmNodeIcon size={24} />
          </div>
        )}

        {/* 左下角时长徽章 (Batch 225 源站 00:04 样式; 元数据经上方 effect 读取) */}
        {imageUrl && !isPlaying && isVideoSource && durationLabel && (
          <span
            data-frameos-video-duration
            style={{
              position: "absolute",
              left: 8,
              bottom: 8,
              padding: "1px 6px",
              borderRadius: 4,
              background: "rgba(0,0,0,0.65)",
              color: "#E0E0E0",
              fontSize: 11,
              fontVariantNumeric: "tabular-nums",
              zIndex: 1,
            }}
          >
            {durationLabel}
          </span>
        )}

        {/* 中心播放/暂停按钮 - 仅对有内容的视频节点渲染
            (2026-09-23 源站实测: 空视频节点为纯图标, 无播放按钮/徽章) */}
        {videoUrl ? (
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
        ) : null}

        {/* 右下角替换内容按钮 - 仅对有内容的视频节点渲染
            (Batch 225 源站截图: 视频节点替换按钮位于右下角, 与图片节点右上角不同) */}
        {imageUrl ? (
        <div
          className="card-body-actions"
          style={{
            position: "absolute",
            bottom: 6,
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
        ) : null}
      </div>
    </FrameosNodeShell>
  );
}
