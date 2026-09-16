"use client";

import { useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { Ban, Tag } from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import type { JimengAudioNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { TAG_COLORS } from "@/components/jimeng/nodes/JimengVideoTitleRow";
import { JimengAudioGenPanel } from "@/components/jimeng/JimengAudioGenPanel";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 音频节点 (Batch 19；批 236/239 源站采样对齐)。
 *
 * 证据 (SOURCE_FACT 236-audio-node.json / 236-source-audio-node.png):
 * 卡片 368×368 方形，内部仅居中的 5 柱波形图标 (white/40)，
 * 无常驻播放控件；选中态下方弹出音频生成面板
 * (JimengAudioGenPanel: 占位「请输入你想生成的说话内容」+
 * 音频生成/Seed TTS/直爽女大 三选择器 + ✦1 + 禁用发送)。
 * 标题行 FileBadgeIcon + 「音频 1」；插入即选中 (批 236)。
 * 批 19/47 的横条播放器为旧视觉，已按源站实测移除。
 */
export function JimengAudioNode({ id, data, selected }: NodeProps) {
  const d = data as JimengAudioNodeData;
  // 批 263 SOURCE_FACT: 音频标题行悬停出现 Add tags (颜色标记选色盘)
  const [tagPickerOpen, setTagPickerOpen] = useState(false);
  const updateNodeData = useJimengStore((s) => s.updateNodeData);

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center justify-between gap-1.5 text-left text-white/70">
        <div className="flex min-w-0 items-center gap-1.5">
          <FileBadgeIcon size={16} />
          <JimengNodeTitle id={id} title={d.title} />
        </div>
        <span className="relative">
          <button
            type="button"
            aria-label="节点颜色标记"
            onClick={(e) => {
              e.stopPropagation();
              setTagPickerOpen((v) => !v);
            }}
            className="flex size-4 items-center justify-center opacity-0 group-hover:opacity-100"
          >
            {d.tagColor ? (
              <span
                className="size-3 rounded-full"
                style={{ background: d.tagColor }}
              />
            ) : (
              <Tag size={16} className="text-white/40" />
            )}
          </button>
          {tagPickerOpen ? (
            <span
              className="nodrag absolute right-0 top-[calc(100%+6px)] z-[130] flex items-center gap-2 rounded-full border border-white/10 bg-[#262626] px-2.5 py-1.5"
              role="menu"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <button
                type="button"
                aria-label="清除颜色标记"
                onClick={(e) => {
                  e.stopPropagation();
                  updateNodeData(id, { tagColor: null });
                  setTagPickerOpen(false);
                }}
                className="flex size-4 items-center justify-center rounded-full border border-white/40 text-white/70"
              >
                <Ban size={10} />
              </button>
              {TAG_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  aria-label={`颜色标记 ${color}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    updateNodeData(id, { tagColor: color });
                    setTagPickerOpen(false);
                  }}
                  className="size-4 rounded-full"
                  style={{ background: color }}
                />
              ))}
            </span>
          ) : null}
        </span>
      </div>

      <div
        className="relative flex h-full w-full items-center justify-center overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(30,30,32), rgb(22,22,24))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : "0 0 0 1px rgba(255,255,255,0.06) inset",
        }}
      >
        {/* 批 236 SOURCE_FACT: 居中 5 柱波形图标 */}
        <span className="flex items-center gap-1 text-white/40" aria-hidden>
          {[12, 20, 28, 20, 12].map((h, i) => (
            <span
              key={i}
              className="w-[3px] rounded-full bg-current"
              style={{ height: h }}
            />
          ))}
        </span>
      </div>

      <JimengAudioGenPanel visible={selected === true} />

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
