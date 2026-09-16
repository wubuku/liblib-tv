"use client";

import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import type { JimengTask } from "@/store/jimengStore";
import type { JimengVideoNodeData } from "@/types/jimeng";
import { useJimengStore } from "@/store/jimengStore";

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

/**
 * 视频节点媒体卡片 (Batch 74 自 JimengVideoNode 拆分，无行为变更)。
 *
 * 结构 (SOURCE_FACT): 8px 圆角卡片、object-cover 海报、中央 32px 半透明
 * 播放圆钮、底部 播放/时间/静音/全屏 控制条、底边 2px 进度条；
 * 截取帧徽章 (batch 35/36)、进度条 seek/scrub (batch 32/37)、
 * 任务/生成中遮罩 (batch 11/50)、媒体失效态 (batch 67)。
 */
export function JimengVideoMediaCard({
  id,
  d,
  selected,
  playing,
  task,
}: {
  id: string;
  d: JimengVideoNodeData;
  selected: boolean;
  playing: boolean;
  task?: JimengTask;
}) {
  const togglePlay = useJimengStore((s) => s.togglePlay);
  const restartPlay = useJimengStore((s) => s.restartPlay);
  const toggleMute = useJimengStore((s) => s.toggleMute);
  const setMediaError = useJimengStore((s) => s.setMediaError);
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const seek = useJimengStore((s) => s.seek);
  const openPreview = useJimengStore((s) => s.openPreview);

  return (
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
      onDoubleClick={() => {
        if (d.hasMedia) restartPlay(id);
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
          {/* 中央播放/暂停圆钮 32px rgba(0,0,0,0.6) SOURCE_FACT；点击切换播放 */}
          <button
            type="button"
            aria-label={playing ? "暂停" : "播放"}
            onClick={(e) => {
              e.stopPropagation();
              togglePlay(id);
            }}
            className="absolute left-1/2 top-1/2 z-[1] flex size-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/75"
          >
            {playing ? (
              <Pause size={14} fill="currentColor" />
            ) : (
              <Play size={14} fill="currentColor" />
            )}
          </button>
          {/* 底部控制条 */}
          <div className="absolute inset-x-0 bottom-0 z-[1] flex items-center gap-1.5 bg-gradient-to-t from-black/55 to-transparent px-2.5 pb-2 pt-5 text-white">
            <button
              type="button"
              aria-label={playing ? "底部暂停" : "底部播放"}
              onClick={(e) => {
                e.stopPropagation();
                togglePlay(id);
              }}
              className="flex items-center"
            >
              {playing ? (
                <Pause size={12} fill="currentColor" />
              ) : (
                <Play size={12} fill="currentColor" />
              )}
            </button>
            <span className="text-[11px] leading-none tabular-nums">
              {formatTime(d.currentTime ?? 0)} / {formatTime(d.duration ?? 0)}
            </span>
            <span className="flex-1" />
            <button
              type="button"
              aria-label={d.muted ? "取消静音" : "静音"}
              title={d.muted ? "取消静音" : "静音"}
              onClick={(e) => {
                e.stopPropagation();
                toggleMute(id);
              }}
              className="flex items-center"
            >
              {d.muted ? <VolumeX size={13} /> : <Volume2 size={13} />}
            </button>
            <button
              type="button"
              aria-label="全屏预览"
              title="全屏"
              onClick={(e) => {
                e.stopPropagation();
                openPreview(id);
              }}
              className="flex items-center"
            >
              <Maximize2 size={13} />
            </button>
          </div>
          {/* 底边进度条 2px；点击 seek (Batch 32)、按住拖拽 scrub (Batch 37)。
              nodrag: 阻止 xyflow 节点拖拽抢占指针 (否则 scrub 中途失效) */}
          <div
            className="nodrag absolute inset-x-0 bottom-0 z-[2] h-[8px] cursor-pointer bg-transparent"
            data-testid="video-progress"
            onPointerDown={(e) => {
              e.stopPropagation();
              (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
              const r = e.currentTarget.getBoundingClientRect();
              seek(id, (e.clientX - r.left) / r.width);
            }}
            onPointerMove={(e) => {
              if (!(e.buttons & 1)) return;
              e.stopPropagation();
              const r = e.currentTarget.getBoundingClientRect();
              seek(id, (e.clientX - r.left) / r.width);
            }}
          >
            {/* Batch 85 (SOURCE_FACT 85-seek.json): track 5px white/16 r25,
                fill white/96 */}
            <div className="absolute inset-x-0 bottom-0 h-[5px] rounded-[25px] bg-white/[0.16]">
              <div
                className="h-full rounded-[25px] bg-white/[0.96]"
                style={{
                  width: `${Math.min(100, ((d.currentTime ?? 0) / (d.duration || 1)) * 100)}%`,
                }}
              />
            </div>
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

      {/* mock 任务处理中遮罩 (Batch 11, CLONE_DECISION)；生成中遮罩 (Batch 50) */}
      {task ? (
        <div className="absolute inset-0 z-[3] flex flex-col items-center justify-center gap-2 rounded-lg bg-black/55">
          <span className="size-6 animate-spin rounded-full border-2 border-white/25 border-t-white" />
          <span className="text-[12px] text-white/85">
            {task.kind === "upscale" ? "智能超清" : "补帧"}处理中…
          </span>
        </div>
      ) : null}
      {d.generating ? (
        <div className="absolute inset-0 z-[3] flex flex-col items-center justify-center gap-2 rounded-lg bg-black/55">
          <span className="size-6 animate-spin rounded-full border-2 border-white/25 border-t-white" />
          <span className="text-[12px] text-white/85">生成中…</span>
        </div>
      ) : null}
      {/* 媒体失效态 (Batch 67, SOURCE_FACT 67-cap-state.png): 视频播放失败
          + 白底 重试播放视频 药丸钮；点击重试清除错误并从头重播 */}
      {d.mediaError && !task && !d.generating ? (
        <div className="absolute inset-0 z-[3] flex flex-col items-center justify-center gap-2.5 rounded-lg">
          <span className="text-[12px] text-white/85" data-testid="media-error-text">
            视频播放失败
          </span>
          <button
            type="button"
            data-testid="media-error-retry"
            onClick={(e) => {
              e.stopPropagation();
              setMediaError(id, false);
              restartPlay(id);
            }}
            className="nodrag rounded-lg bg-white px-3 py-1.5 text-[12px] font-medium text-[#151515] hover:bg-white/90"
          >
            重试播放视频
          </button>
        </div>
      ) : null}
    </div>
  );
}
