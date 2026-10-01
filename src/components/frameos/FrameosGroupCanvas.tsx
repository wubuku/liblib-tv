"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useViewport } from "@xyflow/react";
import { useFrameosStore, type FrameosGroup } from "@/store/frameosStore";
import { showToast } from "./FrameosToast";
import { openContextMenu } from "./FrameosContextMenu";

/**
 * FrameOS 画布分组覆盖层 (Batch 251, 源站采样 2026-09-27):
 * `.canvas-groups-layer` 以 flow 坐标渲染在节点层之前 (分组在节点后方)。
 * 容器: bg rgba(c,0.16) / border 1.5px rgba(c,0.9) / radius 12;
 * 标签 top:-24 含文件夹图标 + 「组N」(12px rgb(163,163,163));
 * 选中态四角手柄 12×12 外偏 -6px。
 * 交互: pointerdown 选中分组; 拖拽带动全部成员同步位移 (非成员不动)。
 * Batch 261: 选中态右缘出现「批量连线」端口 (24px 圆, right:-12, 垂直居中,
 * bg rgba(48,54,66,0.96) / border 1.5px rgba(255,255,255,0.88)) — 源站点击后
 * 进入连线态但完整提交语义未采样到, 克隆以 mock toast 呈现。
 */

function hexToRgba(hex: string, alpha: number): string {
  const v = hex.replace("#", "");
  const r = parseInt(v.slice(0, 2), 16);
  const g = parseInt(v.slice(2, 4), 16);
  const b = parseInt(v.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 分组标签文件夹图标 (源站 ri-folder-2-line, 12px 线性)
function FolderIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden style={{ display: "block" }}>
      <path
        d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2.5h9A1.5 1.5 0 0 1 21 9v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18V6.5Z"
        stroke="rgb(163,163,163)"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const HANDLES = ["nw", "ne", "sw", "se"] as const;

function GroupDiv({ group, selected }: { group: FrameosGroup; selected: boolean }) {
  const selectGroup = useFrameosStore((s) => s.selectGroup);
  const moveGroup = useFrameosStore((s) => s.moveGroup);
  const renameGroup = useFrameosStore((s) => s.renameGroup);
  const ungroup = useFrameosStore((s) => s.ungroup);
  const { zoom } = useViewport();
  const [renaming, setRenaming] = useState(false);
  const dragRef = useRef<{ sx: number; sy: number; lastX: number; lastY: number; pushed: boolean } | null>(null);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    // 阻断冒泡, 避免被 pane 起成框选 (源站分组区域拖拽 = 移动分组)
    e.stopPropagation();
    selectGroup(group.id);
    dragRef.current = {
      sx: e.clientX,
      sy: e.clientY,
      lastX: e.clientX,
      lastY: e.clientY,
      pushed: false,
    };
    const onMove = (ev: PointerEvent) => {
      const d = dragRef.current;
      if (!d) return;
      if (!d.pushed && Math.hypot(ev.clientX - d.sx, ev.clientY - d.sy) > 2) {
        useFrameosStore.getState().pushHistory();
        d.pushed = true;
      }
      const dx = (ev.clientX - d.lastX) / zoom;
      const dy = (ev.clientY - d.lastY) / zoom;
      if (dx !== 0 || dy !== 0) {
        moveGroup(group.id, dx, dy);
        d.lastX = ev.clientX;
        d.lastY = ev.clientY;
      }
    };
    const onUp = () => {
      dragRef.current = null;
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  return (
    <div
      data-frameos-group={group.id}
      className={"frameos-canvas-group" + (selected ? " is-selected" : "")}
      style={{
        position: "absolute",
        left: group.x,
        top: group.y,
        width: group.w,
        height: group.h,
        background: hexToRgba(group.color, 0.16),
        border: `1.5px solid ${hexToRgba(group.color, 0.9)}`,
        borderRadius: 12,
        pointerEvents: "auto",
        cursor: "default",
      }}
      onPointerDown={onPointerDown}
      onMouseDown={(e) => e.stopPropagation()}
      onContextMenu={(e) => {
        // Batch 262: 分组右键菜单 (源站: 复制⌘C / 创建副本⌘D / 删除⌫; 点击效果未采样)
        e.preventDefault();
        e.stopPropagation();
        selectGroup(group.id);
        openContextMenu({
          x: e.clientX,
          y: e.clientY,
          items: [
            {
              label: "复制",
              shortcut: "⌘C",
              onClick: () => showToast("已复制分组 (mock)", "success"),
            },
            {
              label: "创建副本",
              shortcut: "⌘D",
              onClick: () => showToast("已创建分组副本 (mock)", "success"),
            },
            { separator: true, label: "" },
            {
              label: "删除",
              danger: true,
              shortcut: "⌫",
              // Batch 344: 此前是 `showToast("已删除分组 (mock)", "success")` ——
              // 弹一条绿色成功提示说「已删除分组」，但**组根本没有被删**。
              // 实测 (probe-frameos-batch344-group-menu.py): 点击后
              // groupCount 仍为 1、hasGroup 仍为 true、DOM 里分组盒还在。
              //
              // 改为直接复用 store 已有的 `ungroup`（工具条「解组」用的同一个
              // action：移除分组、成员位置保持），并且**不发 toast** ——
              // 组从画布上消失本身就是反馈，比一条可能不兑现的文案诚实
              // （与 FrameosGroupToolbar 的解组保持一致）。
              //
              // CLONE_DECISION: 「删除分组」也可能指「连成员一起删」。那是破坏性
              // 操作、且需要二次确认，源站行为未采样（被人机验证阻塞，见
              // SOURCE_ACCESS_BLOCKED_2026-10-01.md），**不擅自发明**。这里取的是
              // 非破坏、可撤销的那一种读法。若日后源站可采样且确认是另一种，
              // 只需改这一处。
              onClick: () => ungroup(group.id),
            },
          ],
        });
      }}
    >
      <div
        className="frameos-canvas-group-label"
        style={{
          position: "absolute",
          top: -24,
          left: 0,
          height: 20,
          display: "flex",
          alignItems: "center",
          gap: 4,
          fontSize: 12,
          lineHeight: "20px",
          color: "rgb(163,163,163)",
        }}
        onPointerDown={(e) => e.stopPropagation()}
        onDoubleClick={(e) => {
          // Batch 262: 双击标签进入内联重命名 (源站: input.canvas-group__rename-input)
          e.stopPropagation();
          setRenaming(true);
        }}
      >
        <FolderIcon />
        {renaming ? (
          <input
            className="frameos-group-rename-input"
            defaultValue={group.name}
            autoFocus
            style={{
              width: 90,
              height: 20,
              fontSize: 12,
              color: "rgb(163,163,163)",
              background: "rgba(24,24,24,0.9)",
              border: "1px solid rgba(255,255,255,0.16)",
              borderRadius: 4,
              padding: "0 4px",
              outline: "none",
            }}
            onPointerDown={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
            onDoubleClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              e.stopPropagation();
              if (e.key === "Enter") {
                renameGroup(group.id, e.currentTarget.value);
                setRenaming(false);
              } else if (e.key === "Escape") {
                setRenaming(false);
              }
            }}
            onBlur={(e) => {
              renameGroup(group.id, e.currentTarget.value);
              setRenaming(false);
            }}
          />
        ) : (
          <span className="frameos-canvas-group-name">{group.name}</span>
        )}
      </div>
      {selected &&
        HANDLES.map((pos) => (
          <div
            key={pos}
            aria-hidden
            className={`frameos-canvas-group-handle frameos-canvas-group-handle--${pos}`}
            style={{
              position: "absolute",
              width: 12,
              height: 12,
              border: `1.5px solid ${group.color}`,
              borderRadius: 3,
              ...(pos.includes("n") ? { top: -6 } : { bottom: -6 }),
              ...(pos.includes("w") ? { left: -6 } : { right: -6 }),
            }}
          />
        ))}
      {selected && (
        <button
          type="button"
          aria-label="批量连线"
          className="frameos-group-batch-connect-port"
          style={{
            position: "absolute",
            width: 24,
            height: 24,
            right: -12,
            top: "50%",
            marginTop: -12,
            borderRadius: "50%",
            background: "rgba(48,54,66,0.96)",
            border: "1.5px solid rgba(255,255,255,0.88)",
            cursor: "pointer",
            padding: 0,
          }}
          onPointerDown={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            showToast("批量连线 (mock)", "success");
          }}
        />
      )}
    </div>
  );
}

export function FrameosGroupCanvas() {
  const groups = useFrameosStore((s) => s.groups);
  const selectedGroupId = useFrameosStore((s) => s.selectedGroupId);
  const [host, setHost] = useState<HTMLElement | null>(null);

  // 挂载到 .react-flow__viewport 的第一个子层 (源站: 分组层在节点层之前)
  useEffect(() => {
    let tries = 0;
    let raf = 0;
    const tryMount = () => {
      const vp = document.querySelector(".react-flow__viewport");
      if (vp) {
        const layer = document.createElement("div");
        layer.setAttribute("data-frameos-groups-layer", "");
        layer.style.position = "absolute";
        layer.style.left = "0";
        layer.style.top = "0";
        layer.style.width = "0";
        layer.style.height = "0";
        layer.style.pointerEvents = "none";
        vp.insertBefore(layer, vp.firstChild);
        setHost(layer);
        return;
      }
      if (tries++ < 60) raf = requestAnimationFrame(tryMount);
    };
    tryMount();
    return () => {
      cancelAnimationFrame(raf);
      document.querySelector("[data-frameos-groups-layer]")?.remove();
    };
  }, []);

  if (!host) return null;
  return createPortal(
    <>
      {groups.map((g) => (
        <GroupDiv key={g.id} group={g} selected={g.id === selectedGroupId} />
      ))}
    </>,
    host
  );
}
