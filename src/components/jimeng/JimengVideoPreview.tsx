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
  const setVolume = useJimengStore((s) => s.setVolume);
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const layerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const volume = data.volume ?? 0.6;

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

  /* ⭐⭐⭐⭐⭐ 1032-⑫：**全屏层里是真的 `<video>`**。
   *  此前这里只渲染一张**海报 `<img>`** ⇒ ⇒ 全屏里画面**永远是静止的**，
   *  而时间码在往前走 ⇒ ⇒ **假播放**（与卡面 C11 那次整改同族，但全屏层漏了）。
   *  ⇒ ⇒ 现在渲染真 `<video src>`：海报仍作 `poster`（未播时的第一帧）。
   *
   *  ⚠️ 与卡面那个元素的关系：**卡面那个在本层打开时暂停**
   *    （见 JimengVideoMediaCard 的 previewOpen 分支）⇒
   *    ⇒ 两个元素不会同时播 ⇒ 声音不叠、时间码不互相追尾。
   */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (playing) {
      void v.play().catch(() => {
        /* 自动播放被浏览器拦下 ⇒ 忽略；用户点一下播放钮会再试。 */
      });
    } else {
      v.pause();
    }
  }, [playing, data.src]);

  /* store 的当前时间 ⇒ 真的 seek */
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !data.src) return;
    const target = data.currentTime ?? 0;
    if (Math.abs(v.currentTime - target) > 0.3) {
      v.currentTime = target;
    }
  }, [data.currentTime, data.src]);

  /* 静音 / 音量 ⇒ 真的写到元素上 */
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = muted;
  }, [muted, data.src]);
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.volume = volume;
  }, [volume, data.src]);

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
      {/* 媒体铺满 —— ⭐⭐⭐⭐⭐ 1032-⑫：真 `<video>`（此前是海报 `<img>` ⇒ 假播放）。
          没有 `src` 的空节点才回落成海报图。 */}
      {data.src ? (
        <video
          ref={videoRef}
          src={data.src}
          poster={data.poster}
          preload="metadata"
          playsInline
          muted={muted}
          data-testid="jimeng-video-preview-element"
          className="absolute inset-0 h-full w-full object-contain"
          onTimeUpdate={(e) => {
            /* 元素的真实进度写回 store ⇒ 进度条与画面永远一致。 */
            updateNodeData(nodeId, { currentTime: e.currentTarget.currentTime });
          }}
        />
      ) : data.poster ? (
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
        {/* ⭐⭐⭐⭐⭐ 1032-⑫：音量滑杆 —— **真能拖**（此前是**静态 span**）。
         *  旧形态：`role="slider"` + `aria-valuenow={60}` 写死、**零事件处理器**
         *  ⇒ ⇒ 拖它没反应、读数永远 60 ⇒ ⇒ **假交互**
         *  （也正是 1034 假交互普查扫不到它的那一类：
         *    那道门只扫**带事件属性**的元素 ⇒ 零处理器的元素压根不在候选集里）。
         *
         *  现在：拖动 ⇒ 写 store 的 `volume` ⇒ ⇒ 真的写到 `<video>.volume`
         *  ⇒ ⇒ 拖完**听得见**；读数 `aria-valuenow` 随动。
         *  键盘：←/→/↑/↓ 调 0.05，Home/End 到两端（`role="slider"` 语义要求可聚焦）。
         *
         *  口径 (SOURCE_FACT, 手册 10-tasks/media-playback.md「音量滑杆」节，
         *  2026-10-02 源站实测)：音量 `aria-valuemin=0` / `aria-valuemax=1`
         *  ⇒ ⇒ 复刻对齐（进度条那条的 `aria-valuemax` 是**素材总时长**，两者不混）。 */}
        <span
          className="mr-1 flex h-4 w-[52px] items-center"
          role="slider"
          tabIndex={0}
          aria-label="音量"
          aria-valuemin={0}
          aria-valuemax={1}
          aria-valuenow={Number(volume.toFixed(2))}
          data-testid="preview-volume-slider"
          onPointerDown={(e) => {
            (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
            const r = e.currentTarget.getBoundingClientRect();
            setVolume(nodeId, (e.clientX - r.left) / r.width);
          }}
          onPointerMove={(e) => {
            if (!(e.buttons & 1)) return;
            const r = e.currentTarget.getBoundingClientRect();
            setVolume(nodeId, (e.clientX - r.left) / r.width);
          }}
          onKeyDown={(e) => {
            const cur = volume;
            let next: number | null = null;
            if (e.key === "ArrowRight" || e.key === "ArrowUp") next = cur + 0.05;
            if (e.key === "ArrowLeft" || e.key === "ArrowDown") next = cur - 0.05;
            if (e.key === "Home") next = 0;
            if (e.key === "End") next = 1;
            if (next === null) return;
            e.preventDefault();
            setVolume(nodeId, next);
          }}
        >
          {/* 轨道 52×2 + 8×8 圆点 thumb（贴住分位）——
              源站口径见上方注释。 */}
          <span className="relative h-px w-full bg-white/40">
            <span
              className="block h-px bg-white"
              style={{ width: `${Math.round(volume * 100)}%` }}
            />
            <span
              className="absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white"
              style={{ left: `${Math.round(volume * 100)}%` }}
            />
          </span>
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
