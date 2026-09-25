"use client";

import { useRef, useState } from "react";
import type { NodeProps } from "@xyflow/react";
import { useViewport } from "@xyflow/react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { AudioIcon, PlayFillIcon, PauseFillIcon, Upload2Icon } from "../icons";
import type { FrameosNode } from "@/types/frameos";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * FrameOS 音频节点 (Batch 213 空态 / Batch 222 内容态, 源站采样对齐):
 * - 空态: 居中音乐图标卡片 (260x160), 左右 handle, 选中显示音频面板 (BGM S6 等)
 * - 内容态 (2026-09-25 源站实测, 上传 wav 采样): `.audio-wrap` = 上部居中音乐
 *   图标 + 底部播放器行 [播放/暂停 | 当前时间 | 进度条 | 总时长] (源站用 plyr),
 *   右上角 替换内容 按钮; 仅右侧 handle; 选中工具条 [下载,收藏], 无面板
 */
function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function FrameosAudioNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const { title, audioUrl } = data;
  // Batch 236: 替换按钮随画布缩放 (源站 30px * canvas-zoom 实测)
  const { zoom } = useViewport();
  const btnSize = Math.max(14, Math.round(30 * zoom));
  const iconSize = Math.max(9, Math.round(12 * zoom));
  const inset = Math.max(3, Math.round(6 * zoom));
  const [, setIsHovered] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = () => {
    const el = audioRef.current;
    if (!el) return;
    if (playing) {
      el.pause();
    } else {
      void el.play();
    }
  };

  return (
    <FrameosNodeShell
      kind="audio"
      title={title}
      titleIcon={<AudioIcon size={12} />}
      selected={selected}
      showLeftHandle={!audioUrl}
      showRightHandle
      showResizeHandle={false}
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={260}
      height={160}
    >
      <div
        className="card-body"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#1C1C1C",
          borderRadius: 10,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {audioUrl ? (
          <div className="audio-wrap" style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column" }}>
            {/* 上部: 居中音乐图标 (源站 .audio-visual, aria-hidden) */}
            <div
              data-frameos-audio-visual
              aria-hidden
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AudioIcon size={24} color="#8C8C8C" />
            </div>
            {/* 底部: 播放器行 (源站 plyr: 播放/当前时间/进度/总时长) */}
            <div
              data-frameos-audio-player
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "0 10px 10px",
              }}
            >
              <button
                type="button"
                aria-label={playing ? "暂停" : "播放"}
                onClick={(e) => {
                  e.stopPropagation();
                  togglePlay();
                }}
                style={{
                  width: 24,
                  height: 24,
                  border: "none",
                  borderRadius: 9999,
                  background: "rgba(255,255,255,0.1)",
                  color: "#FFFFFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  flexShrink: 0,
                }}
              >
                {playing ? <PauseFillIcon size={12} /> : <PlayFillIcon size={12} />}
              </button>
              <span
                data-frameos-audio-current
                style={{ color: "#A3A3A3", fontSize: 11, fontVariantNumeric: "tabular-nums", flexShrink: 0 }}
              >
                {formatTime(current)}
              </span>
              <input
                type="range"
                aria-label="进度"
                min={0}
                max={duration || 0}
                step={0.01}
                value={current}
                onPointerDown={(e) => e.stopPropagation()}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setCurrent(next);
                  if (audioRef.current) audioRef.current.currentTime = next;
                }}
                style={{ flex: 1, minWidth: 0, accentColor: "#3B82F6", height: 4 }}
              />
              <span
                data-frameos-audio-duration
                style={{ color: "#A3A3A3", fontSize: 11, fontVariantNumeric: "tabular-nums", flexShrink: 0 }}
              >
                {formatTime(duration)}
              </span>
              <audio
                ref={audioRef}
                src={audioUrl}
                preload="metadata"
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onEnded={() => setPlaying(false)}
                onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
                onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
              />
            </div>
          </div>
        ) : (
          <AudioIcon size={24} color="#8C8C8C" />
        )}

        {/* 右上角替换内容按钮 - 与源站一致, 仅内容音频节点渲染 (同图片节点 Batch 172 门控) */}
        {audioUrl && (
          <div
            className="card-body-actions"
            style={{
              position: "absolute",
              top: inset,
              right: 6,
              zIndex: 2,
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
                input.accept = "audio/*";
                input.onchange = () => {
                  const file = input.files?.[0];
                  if (!file) return;
                  const url = URL.createObjectURL(file);
                  useFrameosStore.getState().updateNodeData(id, { audioUrl: url });
                };
                input.click();
              }}
              style={{
                width: btnSize,
                height: btnSize,
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
              <Upload2Icon size={iconSize} />
            </button>
          </div>
        )}
      </div>
    </FrameosNodeShell>
  );
}
