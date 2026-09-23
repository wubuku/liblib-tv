"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * FrameOS 聚焦模式 (2026-09-23 源站实测, SOURCE_OBSERVATIONS §13.4):
 * - 图片节点面板点「聚焦」进入; 节点上覆盖 聚焦模式 说明浮层
 * - 顶部条: 请在图片上框选聚焦区域 / 返回节点 / 退出
 * - 按 ESC 或 退出 可离开; 返回节点 仅关闭浮层回到节点
 *
 * 本原型未实现真实局部框选 (需要已生成图像), 只复刻入口与退出链路。
 */
export function FrameosFocusMode() {
  const focusModeNodeId = useFrameosStore((s) => s.focusModeNodeId);
  const setFocusModeNodeId = useFrameosStore((s) => s.setFocusModeNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const [pos, setPos] = useState<{ left: number; top: number; width: number; height: number } | null>(
    null,
  );

  const targetNode = focusModeNodeId
    ? nodes.find((n) => n.id === focusModeNodeId)
    : undefined;

  useEffect(() => {
    if (!focusModeNodeId) {
      // 无 id 时组件返回 null, 陈旧的 pos 无需清理 (避免 effect 内同步 setState)
      return undefined;
    }
    let raf = 0;
    const tick = () => {
      const el = document.querySelector(
        `.react-flow__node[data-id="${CSS.escape(focusModeNodeId)}"]`,
      );
      if (!el) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const r = el.getBoundingClientRect();
      setPos((prev) => {
        if (
          prev &&
          Math.abs(prev.left - r.left) < 0.5 &&
          Math.abs(prev.top - r.top) < 0.5 &&
          Math.abs(prev.width - r.width) < 0.5 &&
          Math.abs(prev.height - r.height) < 0.5
        ) {
          return prev;
        }
        return { left: r.left, top: r.top, width: r.width, height: r.height };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [focusModeNodeId]);

  if (!focusModeNodeId || !targetNode || !pos) return null;

  return (
    <>
      {/* 节点上的聚焦模式说明浮层 */}
      <div
        data-frameos-focus-mode
        style={{
          position: "fixed",
          left: pos.left,
          top: pos.top,
          width: pos.width,
          height: pos.height,
          zIndex: 2900,
          background: "rgba(13,13,13,0.92)",
          borderRadius: 10,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          textAlign: "center",
          padding: 16,
        }}
      >
        <div style={{ color: "#FFFFFF", fontSize: 18, fontWeight: 600 }}>聚焦模式</div>
        <div style={{ color: "#C2C2C2", fontSize: 13 }}>
          请选择一张图像进行「局部框选」操作
        </div>
        <div style={{ color: "#7A7A7A", fontSize: 12 }}>
          按 ESC 键可退出当前模式
        </div>
      </div>

      {/* 顶部条: 提示 + 返回节点 / 退出 */}
      <div
        data-frameos-focus-topbar
        style={{
          position: "fixed",
          top: 8,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 2901,
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 10px",
          background: "rgba(24,24,24,0.9)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 10,
          color: "#E0E0E0",
          fontSize: 13,
        }}
      >
        <span>请在图片上框选聚焦区域</span>
        <button
          type="button"
          data-frameos-focus-back
          onClick={() => setFocusModeNodeId(null)}
          style={{
            height: 28,
            padding: "0 10px",
            borderRadius: 6,
            border: "1px solid rgba(255,255,255,0.14)",
            background: "transparent",
            color: "#E0E0E0",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          返回节点
        </button>
        <button
          type="button"
          data-frameos-focus-exit
          onClick={() => setFocusModeNodeId(null)}
          style={{
            height: 28,
            padding: "0 10px",
            borderRadius: 6,
            border: "none",
            background: "rgba(255,255,255,0.10)",
            color: "#FFFFFF",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          退出
        </button>
      </div>
    </>
  );
}
