"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Download, Group, LayoutGrid, Sparkles } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 多选组合工具条 (Batch 62/63)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §6 batch 62/63):
 * - ≥2 节点选中时出现在选区包围盒上方 36px 居中：rgb(32,32,32) r12 h40
 *   (与单选工具条同族载体)
 * - 常规: 「N 节点」标签 rgba(255,255,255,0.5) 13px ｜分隔线｜ 编组 (图标+文字)
 *   布局 (图标+文字+下拉箭头) ｜分隔线｜ 下载图标钮 32×32 禁用态
 *   rgba(255,255,255,0.2)，隐藏提示文案「导出前请保存画布」
 * - 布局下拉 (SOURCE_FACT batch 63): 宫格布局 / 智能布局 两项
 * - 选中集为同一编组时 (SOURCE_FACT batch 63, 63-after-group.png):
 *   编组 → 解除编组，并出现 背景色 钮；调色板 rgb(38,38,38) 横排 6 格
 *   (无颜色 + 青绿 #25C3D9 / 靛蓝 #656FF8 / 紫 #B55CF8 / 橙 #FB883A /
 *   黄 #FDD135，截图像素采样)
 * CLONE_DECISION: 宫格/智能布局的具体排列算法未运行提取——复刻为
 * 网格 (ceil(√n) 列) 与单行；下载禁用原因为导出需先保存画布。
 */

const GROUP_BG_COLORS = ["#25C3D9", "#656FF8", "#B55CF8", "#FB883A", "#FDD135"];

export function JimengMultiSelectToolbar() {
  const selectedCount = useJimengStore(
    (s) => s.nodes.filter((n) => n.selected).length,
  );
  const editingActive = useJimengStore((s) =>
    Boolean(
      s.repaintNodeId ||
        s.editNodeId ||
        s.inferNodeId ||
        s.framePickerNodeId ||
        s.trimNodeId ||
        s.previewNodeId,
    ),
  );
  const groupSelected = useJimengStore((s) => s.groupSelected);
  const ungroupSelected = useJimengStore((s) => s.ungroupSelected);
  const arrangeSelected = useJimengStore((s) => s.arrangeSelected);
  const arrangeSelectedGrid = useJimengStore((s) => s.arrangeSelectedGrid);
  const setGroupColor = useJimengStore((s) => s.setGroupColor);
  // 选中集是否已属同一编组 (≥2 且 groupId 一致)
  const groupedId = useJimengStore((s) => {
    const sel = s.nodes.filter((n) => n.selected);
    if (sel.length < 2) return null;
    const gid = sel[0]?.groupId;
    return gid && sel.every((n) => n.groupId === gid) ? gid : null;
  });

  const [center, setCenter] = useState<{ x: number; top: number } | null>(null);
  const [layoutOpen, setLayoutOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const lastRef = useRef("");
  // Batch 66: 下载受保存状态门控 (保存中… 禁用 + 提示)
  const saved = useJimengStore((s) => s.project.saved);

  const visible = selectedCount >= 2 && !editingActive;

  // 选区包围盒跟随: rAF 轮测选中节点的屏幕矩形 (视口平移/缩放/拖拽均适用)，
  // 仅在多选可见期间运行
  useEffect(() => {
    if (!visible) {
      // 隐藏时复位下拉/坐标 (异步调度，避免 effect 内同步 setState)
      const id = window.setTimeout(() => {
        setLayoutOpen(false);
        setPaletteOpen(false);
        setCenter(null);
        lastRef.current = "";
      }, 0);
      return () => window.clearTimeout(id);
    }
    let raf = 0;
    const tick = () => {
      const rects = [
        ...document.querySelectorAll(".react-flow__node.selected"),
      ].map((n) => n.getBoundingClientRect());
      if (rects.length >= 2) {
        const left = Math.min(...rects.map((r) => r.x));
        const right = Math.max(...rects.map((r) => r.x + r.width));
        const top = Math.min(...rects.map((r) => r.y));
        const key = `${Math.round(left)}:${Math.round(right)}:${Math.round(top)}`;
        if (key !== lastRef.current) {
          lastRef.current = key;
          setCenter({ x: (left + right) / 2, top });
        }
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [visible]);

  // 下拉菜单 Escape 关闭
  useEffect(() => {
    if (!layoutOpen && !paletteOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setLayoutOpen(false);
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [layoutOpen, paletteOpen]);

  if (!visible || !center) return null;

  return (
    <div
      data-testid="jimeng-multi-toolbar"
      className="jimeng-node-toolbar fixed z-[60] flex h-10 select-none items-center gap-0.5 px-1.5"
      style={{
        left: center.x,
        top: center.top - 36,
        transform: "translate(-50%, -100%)",
      }}
    >
      <span
        data-testid="multi-count"
        className="whitespace-nowrap px-1.5 text-[13px] leading-none text-white/50"
      >
        {selectedCount} 节点
      </span>
      <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />
      {groupedId ? (
        <button
          type="button"
          data-testid="multi-ungroup"
          onClick={() => ungroupSelected()}
          className="jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white"
        >
          <Group size={16} className="shrink-0" />
          解除编组
        </button>
      ) : (
        <button
          type="button"
          data-testid="multi-group"
          onClick={() => groupSelected()}
          className="jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white"
        >
          <Group size={16} className="shrink-0" />
          编组
        </button>
      )}
      <div className="relative">
        <button
          type="button"
          data-testid="multi-layout"
          onClick={() => {
            setPaletteOpen(false);
            setLayoutOpen((v) => !v);
          }}
          className={`jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
            layoutOpen ? "bg-white/10" : ""
          }`}
        >
          <LayoutGrid size={16} className="shrink-0" />
          布局
          <ChevronDown size={12} className="ml-0.5 shrink-0 text-white/70" />
        </button>
        {layoutOpen ? (
          <div
            className="absolute left-1/2 top-full z-[120] mt-2 -translate-x-1/2 rounded-xl p-1"
            style={{ background: "rgb(38,38,38)" }}
            data-testid="multi-layout-menu"
          >
            <button
              type="button"
              data-testid="multi-arrange-grid"
              onClick={() => {
                arrangeSelectedGrid();
                setLayoutOpen(false);
              }}
              className="flex h-10 w-full items-center gap-2 whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
            >
              <LayoutGrid size={16} className="shrink-0 text-white/85" />
              宫格布局
            </button>
            <button
              type="button"
              data-testid="multi-arrange-smart"
              onClick={() => {
                arrangeSelected();
                setLayoutOpen(false);
              }}
              className="flex h-10 w-full items-center gap-2 whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
            >
              <Sparkles size={16} className="shrink-0 text-white/85" />
              智能布局
            </button>
          </div>
        ) : null}
      </div>
      {groupedId ? (
        <div className="relative">
          <button
            type="button"
            data-testid="multi-bgcolor"
            onClick={() => {
              setLayoutOpen(false);
              setPaletteOpen((v) => !v);
            }}
            className={`jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
              paletteOpen ? "bg-white/10" : ""
            }`}
          >
            <span
              className={`size-3.5 shrink-0 rounded-[4px] border ${
                paletteOpen ? "border-white" : "border-white/60"
              }`}
            />
            背景色
          </button>
          {paletteOpen ? (
            <div
              className="absolute left-1/2 top-full z-[120] mt-2 flex -translate-x-1/2 items-center gap-2 rounded-xl px-2.5 py-2"
              style={{ background: "rgb(38,38,38)" }}
              data-testid="multi-bgcolor-palette"
            >
              <button
                type="button"
                aria-label="无颜色"
                data-testid="swatch-none"
                onClick={() => {
                  setGroupColor(groupedId, null);
                  setPaletteOpen(false);
                }}
                className="size-[22px] rounded-md border border-white/40 bg-[#0E0E0E] hover:border-white"
              />
              {GROUP_BG_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  aria-label={`背景色 ${color}`}
                  data-testid={`swatch-${color}`}
                  onClick={() => {
                    setGroupColor(groupedId, color);
                    setPaletteOpen(false);
                  }}
                  className="size-[22px] rounded-md hover:ring-1 hover:ring-white/70"
                  style={{ background: color }}
                />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />
      <button
        type="button"
        data-testid="multi-download"
        disabled={!saved}
        aria-label="下载"
        title={saved ? undefined : "导出前请保存画布"}
        onClick={() => {
          if (saved) useJimengStore.getState().pushToast("视频下载已开始（mock）");
        }}
        className={`jimeng-node-toolbar-item flex size-8 items-center justify-center ${
          saved ? "text-white" : "cursor-not-allowed text-white/20"
        }`}
      >
        <Download size={16} />
      </button>
    </div>
  );
}
