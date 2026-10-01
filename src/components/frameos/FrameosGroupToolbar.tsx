"use client";

import { useEffect, useState } from "react";
import { useViewport } from "@xyflow/react";
import {
  useFrameosStore,
  FRAMEOS_GROUP_COLORS,
  type FrameosGroup,
} from "@/store/frameosStore";
import type { FrameosNode } from "@/types/frameos";
import { DownloadIcon } from "./icons";
import { showToast } from "./FrameosToast";

/**
 * FrameOS 成组工具条 — 双模式 (Batch 251, 源站采样 2026-09-27):
 * 1) 多选模式: 框选 ≥2 节点 → [成组 | 批量下载], 锚定选中集合包围盒上方 15px、
 *    水平居中 (源站实测: 工具条中心 = bbox 中心)。成组 → createGroup (源站静默)。
 * 2) 分组模式: 选中分组 → [切换背景色(色点) | 排列方式 │ 整组执行 存为模板 解组 批量下载],
 *    同样居中锚定分组盒。切换背景色 → 10 色板弹层 (is-current 蓝环);
 *    排列方式 → 宫格/水平/垂直菜单; 解组移除分组 (成员位置保持);
 *    批量下载 title「打包下载 N 个文件」= 有媒体成员数; 整组执行为付费功能 no-op;
 *    存为模板 mock toast。源站解组后工具栏残留是 bug, 克隆正确隐藏。
 */

type ToolbarPos = { cx: number; top: number };

function downloadNodesMedia(nodesList: FrameosNode[]) {
  let count = 0;
  for (const node of nodesList) {
    const url =
      (node.data as { imageUrl?: string }).imageUrl ??
      (node.data as { audioUrl?: string }).audioUrl;
    if (!url) continue;
    const a = document.createElement("a");
    a.href = url;
    a.download = (node.data as { title?: string }).title || node.id;
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
}

function nodeHasMedia(n: FrameosNode): boolean {
  return !!(
    (n.data as { imageUrl?: string }).imageUrl ||
    (n.data as { audioUrl?: string }).audioUrl
  );
}

// ── 小图标 (源站 remixicon 对应物) ──
const iconSvg = (d: string, size = 13) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden style={{ display: "block" }}>
    <path d={d} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
const GridIcon = () => iconSvg("M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z");
const RowLayoutIcon = () => iconSvg("M4 5.5h16M4 12h16M4 18.5h16");
const ColLayoutIcon = () => iconSvg("M5.5 4v16M12 4v16M18.5 4v16");
const PlayIcon = () => iconSvg("M8 5.5v13l11-6.5-11-6.5Z");
const TemplateIcon = () => iconSvg("M4 4h16v16H4V4Zm0 5.5h16M9.5 9.5V20");
const CollageIcon = () => iconSvg("M8 4h12v12H8V4Zm-4 4v12h12");

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
  whiteSpace: "nowrap",
} as const;

const iconBtnStyle = {
  ...btnStyle,
  width: 29,
  padding: 0,
  justifyContent: "center",
} as const;

const popStyle = {
  background: "rgba(24,24,24,0.95)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10,
  boxShadow: "0 25px 50px -12px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
  padding: 6,
} as const;

export function FrameosGroupToolbar() {
  const groups = useFrameosStore((s) => s.groups);
  const selectedGroupId = useFrameosStore((s) => s.selectedGroupId);
  const { x: panX, y: panY, zoom } = useViewport();
  const [multiPos, setMultiPos] = useState<ToolbarPos | null>(null);
  const [openPop, setOpenPop] = useState<"color" | "arrange" | null>(null);

  const selectedGroup: FrameosGroup | null =
    groups.find((g) => g.id === selectedGroupId) ?? null;
  const allNodes = useFrameosStore((s) => s.nodes);

  // 多选模式: rAF 跟踪选中集合包围盒 (分组选中时隐藏, 由 tick 内读取 store 判断)
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      if (useFrameosStore.getState().selectedGroupId) {
        setMultiPos((prev) => (prev === null ? prev : null));
        raf = requestAnimationFrame(tick);
        return;
      }
      const selectedEls = [
        ...document.querySelectorAll(".react-flow__node.selected"),
      ];
      if (selectedEls.length < 2) {
        setMultiPos((prev) => (prev === null ? prev : null));
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
      const TOOLBAR_HEIGHT = 36;
      const GAP = 15;
      setMultiPos((prev) => {
        const next = {
          cx: (minX + maxX) / 2,
          top: minY - (TOOLBAR_HEIGHT + GAP),
        };
        if (prev && Math.abs(prev.cx - next.cx) < 0.5 && Math.abs(prev.top - next.top) < 0.5) {
          return prev;
        }
        return next;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // 弹层打开时: 点击外部关闭 + Esc 关闭
  useEffect(() => {
    if (!openPop) return;
    const close = () => setOpenPop(null);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", onKey);
    };
  }, [openPop]);

  // ── 分组模式 ──
  if (selectedGroup) {
    const g = selectedGroup;
    const cx = (g.x + g.w / 2) * zoom + panX;
    const top = g.y * zoom + panY - (36 + 15);
    const members = allNodes.filter((n) => g.memberIds.includes(n.id));
    const mediaCount = members.filter(nodeHasMedia).length;

    return (
      <>
        <div
          className="frameos-group-toolbar frameos-group-toolbar--group"
          style={{
            position: "fixed",
            left: cx,
            top,
            transform: "translateX(-50%)",
            height: 36,
            background: "rgba(24,24,24,0.85)",
            backdropFilter: "blur(6px)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 8,
            display: "flex",
            alignItems: "center",
            gap: 2,
            padding: "0 4px",
            zIndex: 2700,
            animation: "frameos-pop-in 0.15s ease-out",
          }}
          onPointerDown={(e) => e.stopPropagation()}
        >
          <button
            type="button"
            aria-label="切换背景色"
            style={iconBtnStyle}
            onClick={(e) => {
              e.stopPropagation();
              setOpenPop((p) => (p === "color" ? null : "color"));
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <span
              className="gt-color-dot"
              style={{
                width: 16,
                height: 16,
                borderRadius: "50%",
                background: g.color,
                display: "block",
              }}
            />
          </button>
          <button
            type="button"
            aria-label="排列方式"
            style={iconBtnStyle}
            onClick={(e) => {
              e.stopPropagation();
              setOpenPop((p) => (p === "arrange" ? null : "arrange"));
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <GridIcon />
          </button>
          <span
            aria-hidden
            style={{ width: 1, height: 18, background: "rgba(255,255,255,0.08)", margin: "0 4px" }}
          />
          {/* 整组执行 = 源站付费生成入口, 不 mock 触发 */}
          {/* Batch 353: 补钩子 —— Batch 347 的可寻址门禁只普查默认/帮助/选中节点
              三种 UI 态, 分组态从未被扫到, 这三个按钮因此一直是无钩子盲区 */}
          <button
            type="button"
            data-frameos-group-action="run-all"
            style={{ ...btnStyle, cursor: "default", color: "#9CA3AF" }}
          >
            <PlayIcon />
            <span>整组执行</span>
          </button>
          <button
            type="button"
            data-frameos-group-action="save-template"
            style={btnStyle}
            onClick={(e) => {
              e.stopPropagation();
              showToast("已存为模板 (mock)", "success");
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <TemplateIcon />
            <span>存为模板</span>
          </button>
          <button
            type="button"
            data-frameos-group-action="ungroup"
            style={btnStyle}
            onClick={(e) => {
              e.stopPropagation();
              useFrameosStore.getState().ungroup(g.id);
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <CollageIcon />
            <span>解组</span>
          </button>
          <button
            type="button"
            aria-label="批量下载"
            title={`打包下载 ${mediaCount} 个文件`}
            style={btnStyle}
            onClick={(e) => {
              e.stopPropagation();
              downloadNodesMedia(members);
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

          {openPop === "color" && (
            <div
              className="frameos-group-color-pop"
              style={{
                ...popStyle,
                position: "absolute",
                left: -60,
                top: 40,
                display: "grid",
                gridTemplateColumns: "repeat(5, 22px)",
                gap: 6,
                zIndex: 2710,
              }}
              onPointerDown={(e) => e.stopPropagation()}
            >
              {FRAMEOS_GROUP_COLORS.map((c, i) => (
                <button
                  key={c}
                  type="button"
                  aria-label={i === 0 ? "默认色" : `背景色 ${c}`}
                  className={"gt-color-swatch" + (g.color === c ? " is-current" : "")}
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: "9999px",
                    background: c,
                    border: `2px solid ${g.color === c ? "rgb(59,130,246)" : "transparent"}`,
                    cursor: "pointer",
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    useFrameosStore.getState().setGroupColor(g.id, c);
                    setOpenPop(null);
                  }}
                />
              ))}
            </div>
          )}
          {openPop === "arrange" && (
            <div
              className="frameos-group-arrange-pop"
              style={{
                ...popStyle,
                position: "absolute",
                left: -30,
                top: 40,
                display: "flex",
                flexDirection: "column",
                width: 140,
                zIndex: 2710,
              }}
              onPointerDown={(e) => e.stopPropagation()}
            >
              {(
                [
                  ["grid", "宫格排列", GridIcon],
                  ["horizontal", "水平排列", RowLayoutIcon],
                  ["vertical", "垂直排列", ColLayoutIcon],
                ] as const
              ).map(([mode, label, Icon]) => (
                <button
                  key={mode}
                  type="button"
                  className="gt-menu-item"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    height: 32,
                    padding: "0 8px",
                    border: "none",
                    borderRadius: 6,
                    background: "transparent",
                    color: "#E0E0E0",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(255,255,255,0.08)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    useFrameosStore.getState().arrangeGroup(g.id, mode);
                    setOpenPop(null);
                  }}
                >
                  <Icon />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </>
    );
  }

  // ── 多选模式 ──
  if (!multiPos) return null;

  return (
    <div
      className="frameos-group-toolbar"
      style={{
        position: "fixed",
        left: multiPos.cx,
        top: multiPos.top,
        transform: "translateX(-50%)",
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
          // Batch 251: 真实成组 (源站静默无 toast)
          const ids = [
            ...document.querySelectorAll(".react-flow__node.selected"),
          ]
            .map((el) => el.getAttribute("data-id"))
            .filter((v): v is string => !!v);
          useFrameosStore.getState().createGroup(ids);
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
          const selected = [
            ...document.querySelectorAll(".react-flow__node.selected"),
          ];
          const store = useFrameosStore.getState();
          const nodesList = selected
            .map((el) => store.nodes.find((n) => n.id === el.getAttribute("data-id")))
            .filter((n): n is FrameosNode => !!n);
          downloadNodesMedia(nodesList);
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
