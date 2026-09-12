"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 视频全屏播放器 (Batch 27)。
 *
 * 证据 (SOURCE_FACT): 点击卡片右下角全屏图标后进入全屏播放器 —
 * 全屏黑底、媒体铺满、左下 播放/暂停 + 时长、右下 静音 + 退出全屏；无画布 chrome。
 * mock: 媒体为海报铺满 (无真实视频流)，播放态沿用节点数据。
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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return createPortal(
    <div className="fixed inset-0 z-[400] bg-black" role="dialog" aria-label="视频全屏预览">
      {/* 媒体铺满 */}
      {data.poster ? (
        // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报
        <img
          src={data.poster}
          alt={data.title}
          className="absolute inset-0 h-full w-full object-contain"
        />
      ) : null}

      {/* 左下: 播放/暂停 + 时长 */}
      <div className="absolute bottom-5 left-6 flex items-center gap-3 text-white">
        <button
          type="button"
          aria-label={playing ? "全屏暂停" : "全屏播放"}
          onClick={() => togglePlay(nodeId)}
          className="flex items-center"
        >
          {playing ? (
            <Pause size={18} fill="currentColor" />
          ) : (
            <Play size={18} fill="currentColor" />
          )}
        </button>
        <span className="text-[13px] tabular-nums">
          {fmt(data.currentTime ?? 0)} / {fmt(data.duration ?? 0)}
        </span>
      </div>

      {/* 右下: 静音 + 退出全屏 */}
      <div className="absolute bottom-5 right-6 flex items-center gap-4 text-white">
        <button
          type="button"
          aria-label={muted ? "取消静音" : "静音"}
          onClick={() => toggleMute(nodeId)}
          className="flex items-center"
        >
          {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
        </button>
        <button
          type="button"
          aria-label="退出全屏预览"
          onClick={onClose}
          className="flex items-center"
        >
          <Maximize2 size={18} />
        </button>
      </div>
    </div>,
    document.body,
  );
}
