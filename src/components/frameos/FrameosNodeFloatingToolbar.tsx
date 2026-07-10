"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { DownloadIcon } from "./icons";

/**
 * 选中节点的浮动工具条 (与原站 frameos.cn 一致).
 * 位置: 选中节点的正上方 47px 处
 * 视觉: 38x38, rgba(24,24,24,0.8), 8px 圆角, 1px 边框 rgba(255,255,255,0.04)
 * 内容: 下载按钮 (mock 下载该节点的源图/视频)
 */
export function FrameosNodeFloatingToolbar() {
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);

  useEffect(() => {
    if (!selectedNodeId) {
      setPos(null);
      return;
    }
    // 用 RAF + getBoundingClientRect 跟随节点 (节点 xyflow 在 transform 内,
    // 但 .getBoundingClientRect() 已返回屏幕坐标, 适合 floating toolbar 用)
    let raf = 0;
    const tick = () => {
      const el = document.querySelector(
        `.react-flow__node[data-id="${CSS.escape(selectedNodeId)}"]`
      );
      if (!el) {
        setPos(null);
        raf = requestAnimationFrame(tick);
        return;
      }
      const r = el.getBoundingClientRect();
      // 节点水平居中, 顶部上移 47px (含节点上方 22px 浮标题 + 25px 间距 + 38 工具条)
      const left = r.left + r.width / 2 - 19;
      const top = r.top - 47;
      setPos((prev) => {
        if (prev && Math.abs(prev.left - left) < 0.5 && Math.abs(prev.top - top) < 0.5) {
          return prev;
        }
        return { left, top };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [selectedNodeId]);

  if (!selectedNodeId || !pos) return null;

  // 找一下节点类型 (decide 下载 mvp 行为)
  const node = nodes.find((n) => n.id === selectedNodeId);
  if (!node) return null;

  const handleDownload = () => {
    const url = (node.data as { imageUrl?: string }).imageUrl;
    if (!url) {
      window.alert("该节点没有可下载的源文件");
      return;
    }
    const a = document.createElement("a");
    a.href = url;
    a.download = `${node.id}`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div
      className="frameos-floating-toolbar"
      style={{
        position: "fixed",
        left: pos.left,
        top: pos.top,
        width: 38,
        height: 38,
        background: "rgba(24,24,24,0.8)",
        backdropFilter: "blur(6px)",
        border: "1px solid rgba(255,255,255,0.04)",
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        zIndex: 2800,
        animation: "frameos-pop-in 0.15s ease-out",
      }}
    >
      <button
        type="button"
        aria-label="下载"
        title="下载"
        onClick={(e) => {
          e.stopPropagation();
          handleDownload();
        }}
        style={{
          width: 32,
          height: 32,
          border: "none",
          background: "transparent",
          color: "#E0E0E0",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 6,
          cursor: "pointer",
          transition: "background 0.15s, color 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255,255,255,0.08)";
          e.currentTarget.style.color = "#FFFFFF";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "#E0E0E0";
        }}
      >
        <DownloadIcon size={14} />
      </button>
    </div>
  );
}
