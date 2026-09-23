"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useViewport } from "@xyflow/react";
import {
  TextNodeIcon,
  ImageNodeIcon,
  FilmNodeIcon,
  AudioIcon,
  LayoutGridIcon,
  UploadCloudIcon,
} from "./icons";

/**
 * FrameOS 空画布状态 (2026-09-23 源站实测, SOURCE_OBSERVATIONS §1.1 / 截图 01):
 * - 画布无节点时居中显示 标题「选择一种方式开始创作」+ 六个 CTA:
 *   文本 / 图片 / 视频 / 音频 / 3D导演台 / 上传文件
 * - 文本/图片/视频/音频 点击即创建对应节点; 3D导演台 在本原型未实现 → mock;
 *   上传文件 打开系统文件选择 (行为同左栏 本地上传)
 */

const CTAS: {
  label: string;
  icon: React.ReactNode;
  type?: "text" | "image" | "video" | "audio";
  mock?: boolean;
}[] = [
  { label: "文本", icon: <TextNodeIcon size={16} />, type: "text" },
  { label: "图片", icon: <ImageNodeIcon size={16} />, type: "image" },
  { label: "视频", icon: <FilmNodeIcon size={16} />, type: "video" },
  { label: "音频", icon: <AudioIcon size={16} />, type: "audio" },
  { label: "3D导演台", icon: <LayoutGridIcon size={16} />, mock: true },
  { label: "上传文件", icon: <UploadCloudIcon size={16} />, mock: true },
];

export function FrameosEmptyState() {
  const nodes = useFrameosStore((s) => s.nodes);
  const addNode = useFrameosStore((s) => s.addNode);
  const { x: panX, y: panY, zoom } = useViewport();

  if (nodes.length > 0) return null;

  return (
    <div
      data-frameos-empty-state
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2400,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 18,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          color: "#FFFFFF",
          fontSize: 20,
          fontWeight: 600,
          pointerEvents: "auto",
        }}
      >
        选择一种方式开始创作
      </div>
      <div
        style={{
          display: "flex",
          gap: 14,
          pointerEvents: "auto",
        }}
      >
        {CTAS.map((cta) => (
          <button
            key={cta.label}
            type="button"
            data-frameos-empty-cta={cta.label}
            onClick={() => {
              if (cta.mock) {
                window.alert(`${cta.label} (mock，本原型未实现)`);
                return;
              }
              addNode(cta.type!, {
                panX,
                panY,
                zoom,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
              });
            }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              height: 40,
              padding: "0 16px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.14)",
              background: "rgba(28,28,28,0.9)",
              color: "#E0E0E0",
              fontSize: 13,
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(40,40,40,0.95)";
              e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(28,28,28,0.9)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.14)";
            }}
          >
            {cta.icon}
            <span>{cta.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
