"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { useJimengStore } from "@/store/jimengStore";
import { useModalFocusTrap } from "./jimengMenuChrome";

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
  const seek = useJimengStore((s) => s.seek);
  const layerRef = useRef<HTMLDivElement>(null);

  /* 批 863：开层即接管焦点 + Tab 困在层内。
     判据在复刻上抓到实锤：此前焦点留在触发器上（`focus_at_open.state='other'`），
     按 Tab 会走过 22 个**被这个模态自己盖住**的控件（`covered_n=22`）——
     焦点环落在看不见的地方。⚠️ 源站这一层是 `BLOCKED_BY_FIXTURE`（NOT_SAMPLED，
     源站这一版画布没有全屏入口），所以这个修法**不声称**源站也这样；
     依据是「模态盖住了页面就不该把焦点漏给页面」这条模态自身的定义。 */
  useModalFocusTrap(layerRef, true);

  // Batch 80 (SOURCE_FACT): 进入全屏即自动静音播放，退出暂停
  // (仅进入/退出时执行，依赖保持为空)
  useEffect(() => {
    if (!playing) togglePlay(nodeId);
    return () => {
      if (useJimengStore.getState().nodes.find((n) => n.id === nodeId)?.data.playing) {
        useJimengStore.getState().togglePlay(nodeId);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
        // 捕获阶段（batch 794 实测踩坑）：JimengFlow 的全局 Escape 监听注册更早，
    // 会先触发同步重渲染；重渲染使本 effect 清理并重新注册监听，
    // removeEventListener 会把该 listener 标记为 removed，浏览器在**同一次
    // 事件派发中**跳过它 → 冒泡监听收不到 Escape，浮层关不掉。
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return createPortal(
    <div
      ref={layerRef}
      className="fixed inset-0 z-[400] bg-black/60"
      role="dialog"
      aria-label="视频全屏预览"
      /* 批 840：补锚点。这是批 832 role 型普查记下的那处「无锚点」——
         几何型普查（§54 第二通道）**结构上**看不见它：它 `fixed inset-0`
         = 1680×1050，正好撞上枚举里「≥1500×700 的巨型容器就跳过」那条规则。
         批 840 把那条规则换成按**身份**排除（见 jimeng_floating_layer_audit.py），
         它才浮出来。补锚点只是让它可指名，**不声称**源站有同名属性。 */
      data-testid="video-fullscreen-preview"
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

      {/* Batch 85 (SOURCE_FACT): 全宽 5px 进度条 (12px 命中区)，可点击 seek */}
      <div
        className="absolute inset-x-0 bottom-0 z-[1] flex h-3 cursor-pointer items-center"
        data-testid="preview-progress"
        onPointerDown={(e) => {
          (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
          const r = e.currentTarget.getBoundingClientRect();
          seek(nodeId, (e.clientX - r.left) / r.width);
        }}
        onPointerMove={(e) => {
          if (!(e.buttons & 1)) return;
          const r = e.currentTarget.getBoundingClientRect();
          seek(nodeId, (e.clientX - r.left) / r.width);
        }}
      >
        <div className="h-[5px] w-full rounded-[25px] bg-white/[0.16]">
          <div
            className="h-full rounded-[25px] bg-white/[0.96]"
            style={{
              width: `${Math.min(100, ((data.currentTime ?? 0) / (data.duration || 1)) * 100)}%`,
            }}
          />
        </div>
      </div>

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
        {/* 批 218 SOURCE_FACT: 音量滑杆 (细线 + 圆点)；静态 60% 为 CLONE_DECISION */}
        <span
          className="mr-1 flex h-4 w-16 items-center"
          role="slider"
          aria-label="音量"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={60}
        >
          <span className="h-px w-full bg-white/40">
            <span className="block h-px w-[60%] bg-white" />
          </span>
          <span className="-ml-1.5 size-2 rounded-full bg-white" />
        </span>
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
