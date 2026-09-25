"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import {
  AudioIcon,
  DownloadIcon,
  FilmNodeIcon,
  FullscreenExitIcon,
  HdIcon,
  ScissorsIcon,
  StarIcon,
  SubtractIcon,
  TextNodeIcon,
} from "./icons";

/**
 * FrameOS 节点浮动工具条 - 与 frameos.cn 完全对齐:
 * - 选中节点时浮动到节点正上方 + 居中
 * - 内容按节点类型与内容状态区分 (Batch 220/222/225):
 *    - 文本: [全屏查看, 下载] (两个 icon 按钮)
 *    - 空图片: 无工具条; 内容图片: 十项富工具条
 *    - 空视频: [全屏查看, 下载]; 内容视频: 九项 (2026-09-25 源站实测)
 *    - 内容音频: [下载, 收藏]; 空音频: [下载]
 * - 视觉: 圆角 8px, 背景 rgba(24,24,24,0.8), 1px hairline border, blur
 */
interface ToolbarAction {
  label: string;
  aria?: string;
  icon?: ReactNode;
  onClick?: () => void;
}

function getActionsForNode(
  node: { type?: string; data?: { reviewFailed?: boolean; imageUrl?: string; audioUrl?: string } } | undefined
): ToolbarAction[] {
  if (!node) return [];
  switch (node.type) {
    case "text":
      // 2026-09-23 源站实测: 选中文本节点只有 全屏查看 / 下载 两个 icon 按钮
      return [
        { label: "", aria: "全屏查看" },
        { label: "", aria: "下载" },
      ];
    case "image":
      // 2026-09-24 源站实测: 有内容的图片节点选中显示富工具条
      // (⛶全屏 / 下载 / ⭐收藏 / 超清 / 720全景 / 打光 / 改图 / 裁剪 / 标注 / 宫格切分∨);
      // 空图片节点无工具条 (Batch 172/225 空态复测)
      if (!node.data?.imageUrl) return [];
      return [
        { label: "", aria: "全屏查看" },
        { label: "", aria: "下载" },
        { label: "", aria: "收藏" },
        { label: "超清" },
        { label: "720全景" },
        { label: "打光" },
        { label: "改图" },
        { label: "裁剪" },
        { label: "标注" },
        { label: "宫格切分 ∨" },
      ];
    case "video":
      // 2026-09-25 源站实测 (Batch 225, 新版本): 内容视频节点工具条 = 全屏查看/
      // 下载/收藏/剪辑/裁剪/音视频分离/超清/去字幕/片段重拍 九项;
      // 空视频节点保留 2026-09-23 采样的 全屏查看/下载 两项
      if (!node.data?.imageUrl) {
        return [
          { label: "", aria: "全屏查看" },
          { label: "", aria: "下载" },
        ];
      }
      return [
        { label: "", aria: "全屏查看" },
        { label: "", aria: "下载" },
        { label: "", aria: "收藏" },
        { label: "剪辑", icon: <ScissorsIcon size={12} /> },
        { label: "裁剪", icon: <SubtractIcon size={12} /> },
        { label: "音视频分离", icon: <AudioIcon size={12} /> },
        { label: "超清", icon: <HdIcon size={12} /> },
        { label: "去字幕", icon: <TextNodeIcon size={12} /> },
        { label: "片段重拍", icon: <FilmNodeIcon size={12} /> },
      ];
    case "audio":
      // 2026-09-25 源站实测 (Batch 222): 内容音频节点工具条 = 下载/收藏 两个
      // icon 按钮 (无全屏查看); 空音频节点同 default
      if (!node.data?.audioUrl) return [{ label: "", aria: "下载" }];
      return [
        { label: "", aria: "下载" },
        { label: "", aria: "收藏" },
      ];
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

  // 选中变化时立即重置 pos, 避免旧节点位置短暂闪到新节点
  const [prevSelectedId, setPrevSelectedId] = useState<string | null>(selectedNodeId);
  if (selectedNodeId !== prevSelectedId) {
    setPrevSelectedId(selectedNodeId);
    setPos(null);
  }

  useEffect(() => {
    if (!selectedNodeId) {
      return undefined;
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
      // 视觉宽度按动作逐项估算 (icon ≈40px, 文本项 ≈ 字数*12 + 内边距)
      const actions = getActionsForNode(selectedNode);
      const w = Math.max(
        38,
        actions.reduce(
          (acc, a) => acc + (a.label ? a.label.length * 12 + 26 : 40) + 4,
          8
        )
      );
      const left = r.left + r.width / 2 - w / 2;
      // frameos.cn 测得 toolbar 高度 38 + 与节点垂直 gap 19 = 节点上方 57px
      const TOOLBAR_HEIGHT = 38;
      const VERTICAL_GAP = 19;
      const top = r.top - (TOOLBAR_HEIGHT + VERTICAL_GAP);
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
  // 空图片节点等无动作场景不渲染工具条 (源站: 空图片节点选中无工具条)
  if (actions.length === 0) return null;
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
        // 前两个为 icon-only (下载 / 收藏 / 全屏查看)
        const isIconOnly = !a.label;
        const aria = a.aria ?? a.label;
        // 文本节点只有 全屏查看/下载, 不显示收藏/查看历史
        const isDownload = aria === "下载";
        const isFavorite = aria === "收藏";
        const isFullscreenView = aria === "全屏查看";
        const onClick = isDownload
          ? onDownload
          : isFullscreenView && selectedNode.type === "image"
          ? () => {
              // Batch 227: 图片 ⛶全屏查看 = 灯箱浮层 (源站 .lightbox-chrome 采样)
              const imageUrl = (selectedNode?.data as { imageUrl?: string })?.imageUrl;
              if (!imageUrl) return;
              window.dispatchEvent(
                new CustomEvent("frameos:image-lightbox", {
                  detail: {
                    title: (selectedNode?.data as { title?: string })?.title ?? "",
                    imageUrl,
                  },
                })
              );
            }
          : isFullscreenView && selectedNode.type !== "image"
          ? () => {
              // Batch 205: 全屏查看 = 文本内容全屏阅读浮层 (推断实现);
              // 图片节点的 ⛶ 全屏查看源站行为未细采样, 走 mock 提示
              const content =
                (selectedNode?.data as { content?: string })?.content ??
                (selectedNode?.data as { title?: string })?.title ??
                "";
              window.dispatchEvent(
                new CustomEvent("frameos:fullscreen-text", {
                  detail: {
                    title:
                      (selectedNode?.data as { title?: string })?.title ?? "",
                    content,
                  },
                })
              );
            }
          : (a.onClick ?? (() => window.alert(`${a.label || aria} (mock)`)));
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
            {isFullscreenView && <FullscreenExitIcon size={14} />}
            {!isIconOnly && a.icon}
            {!isIconOnly && <span>{a.label}</span>}
          </button>
        );
      })}
    </div>
  );
}
