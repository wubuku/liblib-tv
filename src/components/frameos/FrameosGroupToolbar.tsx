"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { DownloadIcon } from "./icons";
import { showToast } from "./FrameosToast";

/**
 * FrameOS 多选成组工具条 (Batch 229, 源站采样对齐 2026-09-25):
 * 空白拖拽框选 ≥2 节点时, 在选中集合包围盒上方 15px 处显示 `.group-toolbar`
 * 形态工具条 — [成组 (ri-group-line) | 批量下载 (ri-download-2-line)]，高 36。
 * 成组点击效果源站未采样到 (采样时工具条滚出视口), 克隆 mock 提示。
 * 批量下载 (Batch 234): 逐个下载选中节点的媒体 (imageUrl/audioUrl)。
 * 单选时不显示 (单选走 FrameosNodeFloatingToolbar)。
 */
export function FrameosGroupToolbar() {
  const [pos, setPos] = useState<{ left: number; top: number; width: number } | null>(
    null
  );

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const selectedEls = [
        ...document.querySelectorAll(".react-flow__node.selected"),
      ];
      if (selectedEls.length < 2) {
        setPos((prev) => (prev === null ? prev : null));
        raf = requestAnimationFrame(tick);
        return;
      }
      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      for (const el of selectedEls) {
        const r = el.getBoundingClientRect();
        minX = Math.min(minX, r.left);
        maxX = Math.max(maxX, r.right);
        minY = Math.min(minY, r.top);
      }
      const width = 163;
      const left = (minX + maxX) / 2 - width / 2;
      const TOOLBAR_HEIGHT = 36;
      const GAP = 15;
      const top = minY - (TOOLBAR_HEIGHT + GAP);
      setPos((prev) => {
        if (
          prev &&
          Math.abs(prev.left - left) < 0.5 &&
          Math.abs(prev.top - top) < 0.5
        ) {
          return prev;
        }
        return { left, top, width };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  if (!pos) return null;

  const batchDownload = () => {
    // Batch 234: 批量下载 = 逐个下载选中节点的媒体 (标签语义直译;
    // 源站点击效果未采样)。跳过无媒体节点。
    const selected = [
      ...document.querySelectorAll(".react-flow__node.selected"),
    ];
    const store = useFrameosStore.getState();
    let count = 0;
    for (const el of selected) {
      const id = el.getAttribute("data-id");
      const node = store.nodes.find((n) => n.id === id);
      if (!node) continue;
      const url =
        (node.data as { imageUrl?: string }).imageUrl ??
        (node.data as { audioUrl?: string }).audioUrl;
      if (!url) continue;
      const a = document.createElement("a");
      a.href = url;
      a.download =
        (node.data as { title?: string }).title || node.id;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      a.remove();
      count += 1;
    }
    showToast(
      count > 0 ? `已开始下载 ${count} 个素材` : "选中节点没有可下载的素材",
      count > 0 ? "success" : "danger"
    );
  };

  const btnStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    height: 28,
    padding: "0 12px",
    border: "none",
    borderRadius: 6,
    background: "transparent",
    color: "#E0E0E0",
    fontSize: 12,
    fontWeight: 500,
    cursor: "pointer",
    transition: "background 0.15s",
  } as const;

  return (
    <div
      className="frameos-group-toolbar"
      style={{
        position: "fixed",
        left: pos.left,
        top: pos.top,
        width: pos.width,
        height: 36,
        background: "rgba(24,24,24,0.85)",
        backdropFilter: "blur(6px)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        padding: "0 4px",
        zIndex: 2700,
        animation: "frameos-pop-in 0.15s ease-out",
      }}
    >
      <button
        type="button"
        aria-label="成组"
        style={btnStyle}
        onClick={(e) => {
          e.stopPropagation();
          showToast("成组 (mock，源站行为未采样)", "success");
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255,255,255,0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
        }}
      >
        <span aria-hidden style={{ fontSize: 13 }}>⧉</span>
        <span>成组</span>
      </button>
      <button
        type="button"
        aria-label="批量下载"
        style={btnStyle}
        onClick={(e) => {
          e.stopPropagation();
          batchDownload();
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255,255,255,0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
        }}
      >
        <DownloadIcon size={13} />
        <span>批量下载</span>
      </button>
    </div>
  );
}
