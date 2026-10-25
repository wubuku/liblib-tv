"use client";

import { useEffect, useRef } from "react";
import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengTask } from "@/store/jimengStore";
import type { JimengVideoNodeData } from "@/types/jimeng";
import { useJimengStore } from "@/store/jimengStore";

function formatTime(s: number): string {
  // 批 373/374 SOURCE_FACT: 卡面播放药丸为无前导零分格式「0:04 / 0:06」
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

/**
 * 视频节点媒体卡片 (Batch 74 自 JimengVideoNode 拆分，无行为变更)。
 *
 * 结构 (SOURCE_FACT): 8px 圆角卡片、object-cover 海报、中央 44px 半透明
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
  minimal = false,
}: {
  id: string;
  d: JimengVideoNodeData;
  selected: boolean;
  playing: boolean;
  task?: JimengTask;
  /** 批 377 SOURCE_FACT: 编辑态卡面隐藏 静音/全屏 钮 (377 采样 cardBtns) */
  minimal?: boolean;
}) {
  const togglePlay = useJimengStore((s) => s.togglePlay);
  const restartPlay = useJimengStore((s) => s.restartPlay);
  const toggleMute = useJimengStore((s) => s.toggleMute);
  const setMediaError = useJimengStore((s) => s.setMediaError);
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const seek = useJimengStore((s) => s.seek);
  const openPreview = useJimengStore((s) => s.openPreview);

  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C11）：**真的 <video>**。
   *
   * 此前这张「媒体卡」是「背景图 + 模拟进度条」⇒ **播放时只有时间码在走**，
   * 屏幕上**没有任何视频**⇒ ⇒ 用户手册里写的「视频节点能播放」那句话当时是**假的**。
   *
   * 现在：真的有 `<video src>` 指向 `public/videos/` 下的 mp4 ⇒
   *  · 真的有画面（真的解码出来）；
   *  · 真的能播 / 停（`play()` / `pause()`）；
   *  · 真的能拖进度（`currentTime`）；
   *  · 真的有音量 / 静音（`muted`）。
   *
   * ⚠️ **store 仍是单一真源**：`playing` / `currentTime` 都在 store 里，
   *   而 `<video>` 元素**反过来听 store 的**（effect 里同步），
   *   而元素的真实进度**写回 store**（`onTimeUpdate`）——
   *   ⇒ ⇒ 两边不会各说各话（否则进度条会跟画面错位）。
   */
  const videoRef = useRef<HTMLVideoElement>(null);

  /* ⭐⭐⭐⭐⭐ 1032-⑫：**全屏预览打开时，卡面这个元素要让位**。
   *  理由：全屏层里也有一个真 `<video>`（此前全屏层只有一张海报 ⇒ 假播放）。
   *  ⇒ ⇒ 两个元素同时播 ⇒ 声音叠两遍、时间码互相追尾。
   *  ⇒ ⇒ 所以预览开着时**卡面这个暂停**（时间码由全屏层那个写回 store）。
   */
  const previewOpen = useJimengStore((s) => s.previewNodeId === id);

  /* store 的播放态 ⇒ 真的 play()/pause() */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (previewOpen) {
      /* 预览开着 ⇒ 播放权归全屏层那个元素。 */
      v.pause();
      return;
    }
    if (playing) {
      void v.play().catch(() => {
        /* 自动播放被浏览器拦下（有声/无用户手势）⇒ 忽略，
           用户点一下播放钮就会再试一次。 */
      });
    } else {
      v.pause();
    }
  }, [playing, d.src, previewOpen]);

  /* store 的当前时间 ⇒ 真的 seek（用户拖进度条时） */
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !d.src) return;
    const target = d.currentTime ?? 0;
    /* 只在**偏差明显**时才写回去 ⇒ 否则与 `onTimeUpdate` 互相追尾。 */
    if (Math.abs(v.currentTime - target) > 0.3) {
      v.currentTime = target;
    }
  }, [d.currentTime, d.src]);

  /* 静音态 ⇒ 真的 muted */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = d.muted ?? false;
  }, [d.muted]);

  /* ⭐⭐⭐⭐⭐ 1032-⑫：**音量** ⇒ 真的写到元素上。
   *  此前全屏播放器里那枚「音量滑杆」是**静态 span**（拖了没反应）⇒ 假交互。
   *  ⇒ ⇒ 现在音量是 store 里的真状态，拖动写回 store，再由这里写到 `<video>.volume`
   *  ⇒ ⇒ 拖完**听得见变化**。
   */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.volume = d.volume ?? 0.6;
  }, [d.volume, d.src]);

  return (
    <div
      className="group relative h-full w-full overflow-hidden rounded-lg"
      style={{
        background:
          "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
        boxShadow: nodeRingShadow(selected === true),
      }}
      onDoubleClick={() => {
        if (d.hasMedia) restartPlay(id);
      }}
    >
      {d.hasMedia && d.poster ? (
        <>
          {/* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C11）：**真的 <video>** ——
              此前这里是一张 `<img>`（海报）⇒ 屏幕上的画面**永远是静止的**，
              而进度条与时间码在动 ⇒ 用户看到的是「假播放」。
              ⇒ ⇒ 现在渲染真的 `<video>`：海报仍作 `poster`（未播时的第一帧），
                  播起来是**真的画面**。
              ⚠️ `muted` 由 store 的 `d.muted` 控制（effect 里同步），
                  这里先给初值避免首帧有声。 */}
          <video
            ref={videoRef}
            src={d.src}
            poster={d.poster}
            preload="metadata"
            playsInline
            muted={d.muted ?? false}
            data-testid="jimeng-video-element"
            className="absolute inset-0 h-full w-full object-cover"
            onTimeUpdate={(e) => {
              /* ⭐⭐⭐ 元素的真实进度**写回 store** ⇒ 进度条与画面永远一致。 */
              const t = e.currentTarget.currentTime;
              updateNodeData(id, { currentTime: t });
            }}
            onError={() => {
              /* 真解码失败 ⇒ 走既有的「视频播放失败 + 重试」态。 */
              setMediaError(id, true);
            }}
          />
          {/* ⭐⭐⭐⭐⭐ 1032-⑫：中央播放/暂停圆钮 —— **44×44**。
           *  此前这里是 `size-8`（32px）**并且注释写着 SOURCE_FACT** ⇒⇒
           *  那是**假源站标注**：源站那个大播放键实测是 **44×44**
           *  （testid `video-simple-player`，aria `Play <节点名>`；
           *    见手册 10-tasks/media-playback.md「三档状态表」，
           *    批次 101 / 195 实测，100% 档画布像素）。
           *  ⇒⇒ 现在改成 44×44 **对齐源站事实**，注释也改成真实出处。
           *  ⚠️ 复刻口径差异（CLONE_DECISION）：源站那枚只在「已选中未播」时挂载，
           *    复刻这边**三态都在**（静止态也给一个入口）—— 这是**多给**不是**少给**，
           *    已在手册「复刻口径与源站口径的差异」一节逐条写明。 */}
          <button
            type="button"
            aria-label={playing ? "暂停" : "播放"}
            onClick={(e) => {
              e.stopPropagation();
              togglePlay(id);
            }}
            className="absolute left-1/2 top-1/2 z-[1] flex size-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/75"
          >
            {playing ? (
              <Pause size={16} fill="currentColor" />
            ) : (
              <Play size={16} fill="currentColor" />
            )}
          </button>
          {/* 底部控制条 (批 208 SOURCE_FACT: 未选中静止卡仅中央播放钮可见，
              控制条悬停/选中/播放时显示) */}
          <div
            className={`absolute inset-x-0 bottom-0 z-[1] flex items-center gap-1.5 bg-gradient-to-t from-black/55 to-transparent px-2.5 pb-2 pt-5 text-white transition-opacity duration-150 ${
              playing || selected === true
                ? "opacity-100"
                : "opacity-0 group-hover:opacity-100"
            }`}
          >
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
            {!minimal ? (
            <>
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
            </>
            ) : null}
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
