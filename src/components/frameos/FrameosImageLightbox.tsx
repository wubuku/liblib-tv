"use client";

import { useEffect, useState } from "react";
import { CloseIcon, DownloadIcon } from "./icons";

/**
 * FrameOS 图片/视频灯箱 (Batch 227 图片 / Batch 230 视频扩展, 源站采样对齐):
 * 内容图片工具条 ⛶全屏查看 打开全屏灯箱 `.lightbox-chrome` 形态 —
 * 近黑背景 + 居中 contain 图片 + 顶部中央 [放大 缩小 重置 | 下载] + 右上 × 关闭;
 * Esc 关闭。源站按钮无 aria-label, 克隆补充供测试。
 * Batch 230: 视频节点 ⛶ 打开同族灯箱, 真视频源 (blob:/扩展名) 渲染
 * <video controls> 播放, 图片封面源渲染封面图。
 * 事件: window "frameos:image-lightbox" { title, imageUrl, videoUrl? }
 */
export function FrameosImageLightbox() {
  const [state, setState] = useState<{
    title: string;
    imageUrl: string;
    videoUrl?: string;
  } | null>(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const open = (e: Event) => {
      const detail = (
        e as CustomEvent<{ title: string; imageUrl: string; videoUrl?: string }>
      ).detail;
      if (!detail?.imageUrl) return;
      setZoom(1);
      setState(detail);
    };
    window.addEventListener("frameos:image-lightbox", open);
    return () => window.removeEventListener("frameos:image-lightbox", open);
  }, []);

  useEffect(() => {
    if (!state) return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setState(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state]);

  if (!state) return null;

  const onDownload = () => {
    const a = document.createElement("a");
    a.href = state.videoUrl ?? state.imageUrl;
    a.download = state.title || "media";
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const iconBtnStyle = {
    width: 32,
    height: 32,
    border: "none",
    borderRadius: 8,
    background: "transparent",
    color: "#E0E0E0",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "background 0.15s",
  } as const;

  return (
    <div
      data-frameos-image-lightbox
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 5000,
        background: "rgba(8,8,8,0.96)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={() => setState(null)}
    >
      {/* 顶部中央控制条: 图片 → 放大/缩小/重置 | 下载; 视频 → 下载 (Batch 230) */}
      <div
        data-frameos-lightbox-toolbar
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "absolute",
          top: 20,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: 2,
          padding: "0 4px",
          height: 40,
          borderRadius: 10,
          background: "rgba(28,28,28,0.85)",
          border: "1px solid rgba(255,255,255,0.08)",
          zIndex: 2,
        }}
      >
        {!state.videoUrl && (
          <>
        <button
          type="button"
          aria-label="放大"
          style={iconBtnStyle}
          onClick={() => setZoom((z) => Math.min(4, z + 0.25))}
        >
          <span style={{ fontSize: 15 }}>＋</span>
        </button>
        <button
          type="button"
          aria-label="缩小"
          style={iconBtnStyle}
          onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))}
        >
          <span style={{ fontSize: 15 }}>－</span>
        </button>
        <button
          type="button"
          aria-label="重置缩放"
          style={iconBtnStyle}
          onClick={() => setZoom(1)}
        >
          <span style={{ fontSize: 14 }}>↻</span>
        </button>
        <div
          style={{
            width: 1,
            height: 18,
            background: "rgba(255,255,255,0.15)",
            margin: "0 6px",
          }}
        />
          </>
        )}
        <button type="button" aria-label="下载" style={iconBtnStyle} onClick={onDownload}>
          <DownloadIcon size={15} />
        </button>
      </div>

      {/* 右上角关闭 */}
      <button
        type="button"
        aria-label="关闭灯箱"
        onClick={(e) => {
          e.stopPropagation();
          setState(null);
        }}
        style={{
          position: "absolute",
          top: 18,
          right: 22,
          width: 34,
          height: 34,
          border: "none",
          borderRadius: 9999,
          background: "rgba(28,28,28,0.85)",
          color: "#E0E0E0",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 2,
        }}
      >
        <CloseIcon size={15} />
      </button>

      {/* 居中媒体: 真视频源 → 播放器; 否则图片 (contain, 缩放) */}
      {state.videoUrl ? (
        <video
          src={state.videoUrl}
          controls
          autoPlay
          loop
          onClick={(e) => e.stopPropagation()}
          style={{
            maxWidth: "92vw",
            maxHeight: "88vh",
            display: "block",
          }}
        />
      ) : (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={state.imageUrl}
          alt={state.title}
          onClick={(e) => e.stopPropagation()}
          style={{
            maxWidth: "92vw",
            maxHeight: "88vh",
            objectFit: "contain",
            transform: `scale(${zoom})`,
            transition: "transform 0.15s ease-out",
          }}
        />
      )}
    </div>
  );
}
