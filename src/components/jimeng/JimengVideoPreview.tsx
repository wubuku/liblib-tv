"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 视频全屏播放器 (Batch 27/80)。
 *
 * 证据 (SOURCE_FACT batch 80, 80-preview.png + step32 dump):
 * - 全屏覆盖层 bg rgba(0,0,0,0.6) (画布透出)，进入即自动静音播放
 *   (aria: Play <节点标题>，Unmute video 可切)
 * - 底部控制条 36px：左 Play 16px + 当前时间/时长分列；右 Unmute 36×36
 *   + Exit browser full screen 36×36
 * CLONE_DECISION: 不进入浏览器 Fullscreen API (mock 无真实视频流)，
 * 以应用内覆盖层近似；关闭时暂停播放。
 */
function fmt(s: number) {
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(
    Math.floor(s % 60),
  ).padStart(2, "0")}`;
}

export function JimengVideoPreview({
  nodeId,
  data,
  onClose,
}: {
  nodeId: string;
  data: JimengVideoNodeData;
  onClose: () => void;
}) {
  const playing = data.playing === true;
  const muted = data.muted !== false;
  const togglePlay = useJimengStore((s) => s.togglePlay);
  const toggleMute = useJimengStore((s) => s.toggleMute);

  // Batch 80 (SOURCE_FACT): 进入全屏即自动静音播放，退出暂停
  // eslint-disable-next-line react-hooks/exhaustive-deps -- 仅进入/退出时执行
  useEffect(() => {
    if (!playing) togglePlay(nodeId);
    return () => {
      if (useJimengStore.getState().nodes.find((n) => n.id === nodeId)?.data.playing) {
        useJimengStore.getState().togglePlay(nodeId);
      }
    };
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return createPortal(
    <div
      className="fixed inset-0 z-[400] bg-black/60"
      role="dialog"
      aria-label="视频全屏预览"
    >
      {/* 媒体铺满 */}
      {data.poster ? (
        // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报
        <img
          src={data.poster}
          alt={data.title}
          className="absolute inset-0 h-full w-full object-contain"
        />
      ) : null}

      {/* 底部控制条 36px (SOURCE_FACT batch 80): 左 Play + 时间分列，
          右 Unmute + 退出全屏 */}
      <div className="absolute inset-x-0 bottom-0 flex h-9 items-center gap-3 px-6 text-white">
        <button
          type="button"
          aria-label={playing ? "全屏暂停" : "全屏播放"}
          onClick={() => togglePlay(nodeId)}
          className="flex size-9 items-center justify-center"
        >
          {playing ? (
            <Pause size={16} fill="currentColor" />
          ) : (
            <Play size={16} fill="currentColor" />
          )}
        </button>
        <span className="text-[13px] tabular-nums">{fmt(data.currentTime ?? 0)}</span>
        <span className="text-[13px] tabular-nums text-white/60">
          {fmt(data.duration ?? 0)}
        </span>
        <span className="flex-1" />
        <button
          type="button"
          aria-label={muted ? "取消静音" : "静音"}
          onClick={() => toggleMute(nodeId)}
          className="flex size-9 items-center justify-center"
        >
          {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
        <button
          type="button"
          aria-label="退出全屏预览"
          onClick={onClose}
          className="flex size-9 items-center justify-center"
        >
          <Maximize2 size={16} />
        </button>
      </div>
    </div>,
    document.body,
  );
}
