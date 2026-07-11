"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { DownloadIcon, StarIcon } from "./icons";

/**
 * FrameOS 节点浮动工具条 - 与 frameos.cn 完全对齐:
 * - 选中节点时浮动到节点正上方 + 居中
 * - 内容根据节点类型变化:
 *    - 文本: [下载]
 *    - 图片: [下载, 收藏, 超清, 720全景, 改图, 宫格切分]
 *    - 视频: [下载, 收藏, 查看历史, 超清, 去字幕]
 *    - 视频 (审核未通过): [下载, 收藏, 超清, 去字幕]
 * - 视觉: 圆角 8px, 背景 rgba(24,24,24,0.8), 1px hairline border, blur
 */
interface ToolbarAction {
  label: string;
  aria?: string;
  onClick?: () => void;
}

function getActionsForNode(node: { type?: string; data?: { reviewFailed?: boolean } } | undefined): ToolbarAction[] {
  if (!node) return [];
  switch (node.type) {
    case "text":
      return [{ label: "下载", aria: "下载" }];
    case "image":
      return [
        { label: "", aria: "下载" },
        { label: "", aria: "收藏" },
        { label: "超清" },
        { label: "720全景" },
        { label: "改图" },
        { label: "宫格切分" },
      ];
    case "video": {
      const base: ToolbarAction[] = [
        { label: "", aria: "下载" },
        { label: "", aria: "收藏" },
      ];
      if (!node.data?.reviewFailed) base.push({ label: "", aria: "查看历史" });
      base.push(
        { label: "超清" },
        { label: "去字幕" },
      );
      return base;
    }
    default:
      return [{ label: "", aria: "下载" }];
  }
}

export function FrameosNodeFloatingToolbar() {
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const [pos, setPos] = useState<{ left: number; top: number; width: number } | null>(null);

  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId)
    : undefined;

  useEffect(() => {
    if (!selectedNodeId) {
      setPos(null);
      return;
    }
    let raf = 0;
    const tick = () => {
      const el = document.querySelector(
        `.react-flow__node[data-id="${CSS.escape(selectedNodeId)}"]`
      );
      if (!el) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const r = el.getBoundingClientRect();
      // 视觉宽度根据动作数估算
      const actions = getActionsForNode(selectedNode);
      const w = Math.max(38, actions.length * 76);
      const left = r.left + r.width / 2 - w / 2;
      const top = r.top - 47;
      setPos((prev) => {
        if (prev && Math.abs(prev.left - left) < 0.5 && Math.abs(prev.top - top) < 0.5 && Math.abs(prev.width - w) < 0.5) {
          return prev;
        }
        return { left, top, width: w };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [selectedNodeId, selectedNode]);

  if (!selectedNode || !pos) return null;

  const actions = getActionsForNode(selectedNode);
  const onDownload = () => {
    const url = (selectedNode.data as { imageUrl?: string }).imageUrl ?? (selectedNode.data as { content?: string }).content;
    if (!url || !url.startsWith("http")) {
      window.alert("该节点没有可下载的源文件");
      return;
    }
    const a = document.createElement("a");
    a.href = url;
    a.download = selectedNode.id;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div
      className="frameos-floating-toolbar-new"
      style={{
        position: "fixed",
        left: pos.left,
        top: pos.top,
        width: pos.width,
        height: 38,
        background: "rgba(24,24,24,0.8)",
        backdropFilter: "blur(6px)",
        border: "1px solid rgba(255,255,255,0.04)",
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        padding: "0 4px",
        zIndex: 2800,
        animation: "frameos-pop-in 0.15s ease-out",
      }}
    >
      {actions.map((a, i) => {
        // 前两个为 icon-only (下载 / 收藏)
        const isIconOnly = !a.label;
        const aria = a.aria ?? a.label;
        // 文本节点只有下载, 不显示收藏/查看历史
        const isDownload = aria === "下载";
        const isFavorite = aria === "收藏";
        const onClick = isDownload ? onDownload : (a.onClick ?? (() => window.alert(`${a.label || aria} (mock)`)));
        return (
          <button
            key={i}
            type="button"
            aria-label={aria}
            title={aria}
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 4,
              minWidth: isIconOnly ? 32 : "auto",
              height: 30,
              padding: isIconOnly ? "0 6px" : "0 12px",
              border: "none",
              borderRadius: 6,
              background: "transparent",
              color: "#E0E0E0",
              fontSize: 12,
              fontWeight: 500,
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
            {isDownload && <DownloadIcon size={14} />}
            {isFavorite && <StarIcon size={14} />}
            {!isIconOnly && <span>{a.label}</span>}
          </button>
        );
      })}
    </div>
  );
}
