"use client";

import type { NodeProps } from "@xyflow/react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { LayoutGridIcon, ScissorsIcon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

/**
 * FrameOS 工作台节点 (Batch 221, 源站采样对齐 SOURCE_OBSERVATIONS §15):
 * - 3D导演台: 立方体图标居中 + 「进入导演台」胶囊按钮 (300x200)
 * - 视频剪辑台: 剪辑图标 + 「进入剪辑台」胶囊按钮 (同形态)
 * 按钮点击源站跳转工作台页面, 克隆 mock 提示 (未采样目标页)。
 */
export function FrameosWorkspaceNode({ id, data, selected, type }: NodeProps<FrameosNode>) {
  const { title } = data;
  const isDirector = type === "director3d";
  const actionLabel = isDirector ? "进入导演台" : "进入剪辑台";

  return (
    <FrameosNodeShell
      kind={isDirector ? "director3d" : "videoEdit"}
      title={title}
      titleIcon={
        isDirector ? <LayoutGridIcon size={12} /> : <ScissorsIcon size={12} />
      }
      selected={selected}
      showLeftHandle
      showRightHandle
      showResizeHandle={false}
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={300}
      height={200}
    >
      <div
        className="card-body"
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 14,
          background: "#1C1C1C",
          borderRadius: 10,
          overflow: "hidden",
        }}
      >
        {isDirector ? (
          <LayoutGridIcon size={28} color="#8C8C8C" />
        ) : (
          <ScissorsIcon size={28} color="#8C8C8C" />
        )}
        <button
          type="button"
          aria-label={actionLabel}
          onClick={(e) => {
            e.stopPropagation();
            window.alert(`${actionLabel} (mock，目标工作台页未实现)`);
          }}
          style={{
            height: 28,
            padding: "0 16px",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 9999,
            background: "rgba(255,255,255,0.08)",
            color: "#E0E0E0",
            fontSize: 12,
            fontWeight: 500,
            cursor: "pointer",
            transition: "background 0.15s, border-color 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.14)";
            e.currentTarget.style.borderColor = "rgba(96,165,250,0.5)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
          }}
        >
          {actionLabel}
        </button>
      </div>
    </FrameosNodeShell>
  );
}
