"use client";

import { Maximize2, Pause, Play, Plus, Tag, VolumeX } from "lucide-react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { JimengNodeToolbar } from "@/components/jimeng/JimengNodeToolbar";

/**
 * 即梦视频节点 — 复刻重点 (本地上传视频)。
 *
 * 结构证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md):
 * - 标题行在卡片上方 32px：文件徽标 16×16 + 13px/22px rgba(255,255,255,0.7) 标题 + 右侧 Tag 图标
 * - 卡片 569×320 世界尺寸、8px 圆角；媒体 object-cover
 * - 有内容: 中央 32px 半透明播放圆钮 + 底部 播放/时间/静音/全屏 控制 + 底边 2px 进度条
 * - 空节点: 对角渐变占位 + 中央小图标
 * - 左右连接热区 60×120 (隐形)；"+ " 圆钮 24px：本地上传节点仅右侧，空节点两侧 (hover/选中显示)
 */
function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

const HANDLE_BASE = {
  width: 60,
  height: 120,
  background: "transparent",
  border: "none",
  borderRadius: 0,
} as const;

export function JimengVideoNode({ data, selected }: NodeProps) {
  const d = data as JimengVideoNodeData;
  // 播放态由 data.playing 显式驱动 (mock 初始为暂停，与源站提取时一致)
  const playing = d.hasMedia && d.playing === true;

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      {/* 选中后弹出的操作工具条 (仅有内容的视频节点；空节点走生成面板) */}
      {d.hasMedia ? <JimengNodeToolbar visible={selected === true} /> : null}
      {/* 标题行 (卡片上方 32px)：文件徽标 + 标题 + 右侧图标 */}
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center justify-between text-left">
        <div className="flex min-w-0 items-center gap-1.5 text-white/70">
          <FileBadgeIcon size={16} />
          <span className="max-w-full truncate whitespace-nowrap text-[13px] leading-[22px]">
            {d.title}
          </span>
        </div>
        {d.hasMedia ? (
          <Tag size={16} className="shrink-0 text-white/40" />
        ) : null}
      </div>

      {/* 卡片主体 */}
      <div
        className="relative h-full w-full overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : undefined,
        }}
      >
        {d.hasMedia && d.poster ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报 */}
            <img
              src={d.poster}
              alt={d.title}
              className="absolute inset-0 h-full w-full object-cover"
            />
            {/* 中央播放/暂停圆钮 32px rgba(0,0,0,0.6) SOURCE_FACT */}
            <span className="absolute left-1/2 top-1/2 z-[1] flex size-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white">
              {playing ? (
                <Pause size={14} fill="currentColor" />
              ) : (
                <Play size={14} fill="currentColor" />
              )}
            </span>
            {/* 底部控制条 */}
            <div className="absolute inset-x-0 bottom-0 z-[1] flex items-center gap-1.5 bg-gradient-to-t from-black/55 to-transparent px-2.5 pb-2 pt-5 text-white">
              {playing ? (
                <Pause size={12} fill="currentColor" />
              ) : (
                <Play size={12} fill="currentColor" />
              )}
              <span className="text-[11px] leading-none tabular-nums">
                {formatTime(d.currentTime ?? 0)} / {formatTime(d.duration ?? 0)}
              </span>
              <span className="flex-1" />
              <VolumeX size={13} />
              <Maximize2 size={13} />
            </div>
            {/* 底边进度条 2px */}
            <div className="absolute inset-x-0 bottom-0 z-[2] h-[2px] bg-white/25">
              <div
                className="h-full bg-white/90"
                style={{
                  width: `${Math.min(100, ((d.currentTime ?? 0) / (d.duration || 1)) * 100)}%`,
                }}
              />
            </div>
          </>
        ) : (
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/45">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
              <rect
                x="2"
                y="2"
                width="14"
                height="14"
                rx="3"
                stroke="currentColor"
                strokeWidth="1.3"
              />
              <rect x="6.5" y="6.5" width="5" height="5" rx="1" fill="currentColor" />
            </svg>
          </span>
        )}
      </div>

      {/* 连接热区 (隐形) + "+" 圆钮 (hover/选中显示) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{ ...HANDLE_BASE, left: -30, top: "50%", transform: "translateY(-50%)" }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{ ...HANDLE_BASE, right: -30, top: "50%", transform: "translateY(-50%)" }}
      />
      {d.source !== "empty" ? null : (
        <span className="pointer-events-none absolute -left-3 top-1/2 z-20 hidden size-6 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex">
          <Plus size={14} />
        </span>
      )}
      <span className="pointer-events-none absolute -right-3 top-1/2 z-20 hidden size-6 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex">
        <Plus size={14} />
      </span>
    </div>
  );
}
