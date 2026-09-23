"use client";

import { useViewport } from "@xyflow/react";
import { useFrameosStore } from "@/store/frameosStore";
import { NODE_TYPES } from "./FrameosToolRail";
import { CloseIcon } from "./icons";

/**
 * 双击画布空白处的「选择节点类型」菜单 (2026-09-23 源站实测,
 * SOURCE_OBSERVATIONS §13.2 / 截图 19):
 * - 双击空白处 → 菜单锚定在双击位置, 标题「选择节点类型」
 * - 7 类条目与添加节点菜单一致 (无 添加资源 组)
 * - 音频 / 3D模型 / 3D导演台 / 视频剪辑台 在本原型未实现 → mock 提示
 * - 点击菜单外 / Esc / 完成创建 后关闭
 */
export function FrameosPaneAddMenu() {
  const paneMenuAt = useFrameosStore((s) => s.paneMenuAt);
  const setPaneMenuAt = useFrameosStore((s) => s.setPaneMenuAt);
  const addNode = useFrameosStore((s) => s.addNode);
  const { x: panX, y: panY, zoom } = useViewport();

  if (!paneMenuAt) return null;

  const addNodeOpts = {
    panX,
    panY,
    zoom,
    viewportWidth: typeof window !== "undefined" ? window.innerWidth : 1440,
    viewportHeight: typeof window !== "undefined" ? window.innerHeight : 900,
  };

  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 2890 }}
      onClick={() => setPaneMenuAt(null)}
    >
      <div
        data-frameos-pane-add-menu
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "fixed",
          left: paneMenuAt.x,
          top: paneMenuAt.y,
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 12,
          padding: 6,
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          minWidth: 180,
          zIndex: 2891,
        }}
      >
        <div
          style={{
            color: "#A3A3A3",
            fontSize: 12,
            padding: "6px 10px",
          }}
        >
          选择节点类型
        </div>
        {NODE_TYPES.map((nt) => (
          <div
            key={nt.title}
            onClick={() => {
              if ("unimplemented" in nt && nt.unimplemented) {
                window.alert(`${nt.title} 节点 (mock，本原型未实现)`);
                return;
              }
              if (nt.type) {
                addNode(nt.type, addNodeOpts);
              }
              setPaneMenuAt(null);
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "7px 10px",
              borderRadius: 8,
              cursor: "pointer",
              color: "#FFFFFF",
              fontSize: 13,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <span style={{ fontSize: 14 }}>{nt.icon}</span>
            <span>{nt.title}</span>
          </div>
        ))}
        <button
          type="button"
          aria-label="关闭节点类型菜单"
          onClick={() => setPaneMenuAt(null)}
          style={{
            position: "absolute",
            right: 6,
            top: 6,
            width: 20,
            height: 20,
            border: "none",
            background: "transparent",
            color: "#7A7A7A",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 0,
          }}
        >
          <CloseIcon size={12} />
        </button>
      </div>
    </div>
  );
}
