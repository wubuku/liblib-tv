"use client";

import { useEffect, useRef, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { NodeToolbar, Position as TBPosition } from "@xyflow/react";
import {
  Bold,
  ChevronDown,
  Download,
  Italic,
  List,
  ListOrdered,
  Maximize2,
  Square,
  Strikethrough,
  Type,
  Underline,
} from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import type { JimengTextNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 文字节点 (Batch 17/38/68)。结构与视频节点同族 (SOURCE_FACT §5 骨架)。
 * Batch 68 (SOURCE_FACT): 标题图标 T 字形、选中无工具条、占位
 * 「双击编辑文本」、默认 328×340 (68-newnode-selected.png 实测)。
 * Batch 38: 双击卡片进入行内编辑，Enter/失焦提交。
 * Batch 241 (SOURCE_FACT, 241-source-text-edit.png): 编辑态卡上方出现
 * 富文本工具条——字体 T∨ / 无序列表 / 有序列表 / 加粗 B / 删除线 S /
 * 斜体 I / 下划线 U / 展开钮 (按钮为视觉 mock，未接真实格式化)。
 * Batch 241b (SOURCE_FACT, 243-source-font-menu.png): 选中(非编辑)态
 * 另有工具条 背景色(调色板: 无+青绿/靛蓝/紫/橙/黄 六格) / 展开钮 /
 * 下载——「选中无工具条」的批 68 观察已被源站演进推翻。
 */
export function JimengTextNode({ id, data, selected }: NodeProps) {
  const d = data as JimengTextNodeData;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(d.text);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // 批 241b SOURCE_FACT: 调色板 无 + 青绿/靛蓝/紫/橙/黄 (色值为 CLONE_DECISION)
  const BG_COLORS: { label: string; value: string | null }[] = [
    { label: "无", value: null },
    { label: "青绿", value: "#4ECDE6" },
    { label: "靛蓝", value: "#6B7CFF" },
    { label: "紫", value: "#A46BFF" },
    { label: "橙", value: "#FF9A4D" },
    { label: "黄", value: "#FFD44D" },
  ];

  useEffect(() => {
    if (editing) taRef.current?.focus();
  }, [editing]);

  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  // Batch 48: 提交写回 store (mock 文字节点真实联动)
  const commit = () => {
    setEditing(false);
    updateNodeData(id, { text: draft });
  };

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center gap-1.5 text-left text-white/70">
        <Type size={16} />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      {/* 批 241b SOURCE_FACT: 选中(非编辑)态工具条 背景色/展开/下载 */}
      <NodeToolbar isVisible={selected === true && !editing} position={TBPosition.Top} offset={36}>
        <div className="jimeng-node-toolbar relative flex h-10 select-none items-center gap-1 px-1.5">
          <div className="relative">
            <button
              type="button"
              aria-label="背景色"
              onClick={() => setPaletteOpen((v) => !v)}
              className="jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] text-white"
            >
              <Square size={13} />
              背景色
            </button>
            {paletteOpen ? (
              <div
                className="absolute right-0 top-full z-[140] mt-2 flex items-center gap-1.5 rounded-xl px-2.5 py-2"
                style={{ background: "rgb(38,38,38)" }}
                role="menu"
                aria-label="背景色调色板"
              >
                {BG_COLORS.map(({ label, value }) => (
                  <button
                    key={label}
                    type="button"
                    role="menuitem"
                    aria-label={`背景色 ${label}`}
                    onClick={() => {
                      updateNodeData(id, { bgColor: value });
                      setPaletteOpen(false);
                    }}
                    className="flex size-5 items-center justify-center rounded-full"
                    style={{
                      background: value ?? "transparent",
                      border: value ? "none" : "1.5px solid rgba(255,255,255,0.5)",
                    }}
                  >
                    {value === null ? <span className="text-[10px] leading-none text-white/60">∅</span> : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <button
            type="button"
            aria-label="展开文本面板"
            onClick={() => setPaletteOpen(false)}
            className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
          >
            <Maximize2 size={15} />
          </button>
          <button
            type="button"
            aria-label="下载"
            className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
          >
            <Download size={15} />
          </button>
        </div>
      </NodeToolbar>

      <div
        className="h-full w-full overflow-hidden rounded-lg p-4"
        style={{
          background:
            d.bgColor ??
            "linear-gradient(to right bottom, rgb(30,30,32), rgb(22,22,24))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : "0 0 0 1px rgba(255,255,255,0.06) inset",
        }}
        onDoubleClick={(e) => {
          e.stopPropagation();
          setEditing(true);
        }}
      >
        {/* 批 241 SOURCE_FACT: 编辑态富文本工具条 (视觉 mock) */}
        {editing ? (
          <div
            className="absolute bottom-full left-1/2 z-[130] mb-2 flex -translate-x-1/2 items-center gap-0.5 rounded-xl bg-[#262626] p-1"
            role="toolbar"
            aria-label="文本格式"
            data-testid="text-format-toolbar"
          >
            {[
              { label: "字体", node: <Type size={14} />, chevron: true },
              { label: "无序列表", node: <List size={14} /> },
              { label: "有序列表", node: <ListOrdered size={14} /> },
              { label: "加粗", node: <Bold size={14} /> },
              { label: "删除线", node: <Strikethrough size={14} /> },
              { label: "斜体", node: <Italic size={14} /> },
              { label: "下划线", node: <Underline size={14} /> },
              { label: "展开编辑", node: <Maximize2 size={12} /> },
            ].map(({ label, node: icon, chevron }) => (
              <button
                key={label}
                type="button"
                aria-label={label}
                onMouseDown={(e) => e.preventDefault()}
                className="flex h-7 items-center gap-0.5 rounded-md px-1.5 text-white/85 hover:bg-white/10"
              >
                {icon}
                {chevron ? <ChevronDown size={10} className="text-white/60" /> : null}
              </button>
            ))}
          </div>
        ) : null}
        {editing ? (
          <textarea
            ref={taRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                setEditing(false);
              }
              if (e.key === "Escape") {
                setDraft(d.text);
                setEditing(false);
              }
            }}
            className="h-full w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none"
          />
        ) : (
          <p
            className={`text-[13px] leading-[22px] whitespace-pre-wrap ${
              draft || d.text ? "text-white/85" : "text-white/40"
            }`}
          >
            {draft || d.text || "双击编辑文本"}
          </p>
        )}
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{
          width: 60,
          height: 120,
          background: "transparent",
          border: "none",
          borderRadius: 0,
          left: -30,
          top: "50%",
          transform: "translateY(-50%)",
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{
          width: 60,
          height: 120,
          background: "transparent",
          border: "none",
          borderRadius: 0,
          right: -30,
          top: "50%",
          transform: "translateY(-50%)",
        }}
      />
    </div>
  );
}
