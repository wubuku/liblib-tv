"use client";

import { Ban, Tag } from "lucide-react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { useJimengStore } from "@/store/jimengStore";

/** 节点颜色标记五色 (SOURCE_FACT batch 31: 禁止 + 青/蓝/紫/橙/黄) */
export const TAG_COLORS = ["#3BE8E8", "#3D7BFF", "#9C5BFF", "#F79022", "#FFE14D"];

/**
 * 视频节点标题行 (Batch 74 自 JimengVideoNode 拆分，无行为变更)。
 *
 * 结构 (SOURCE_FACT): 卡片上方 32px — 文件徽标 16×16 + 13px/22px
 * rgba(255,255,255,0.7) 标题 (原生 title 悬停提示, batch 45) + 右侧
 * 颜色标记钮 (点击弹 禁止+五色 选色盘, batch 31)。
 * 双击标题行 = 「添加节点」菜单 extended 版 (SOURCE_FACT batch 24)。
 */
export function JimengVideoTitleRow({
  id,
  d,
  tagPickerOpen,
  onToggleTagPicker,
  onDblClick,
}: {
  id: string;
  d: JimengVideoNodeData;
  tagPickerOpen: boolean;
  onToggleTagPicker: () => void;
  onDblClick: () => void;
}) {
  const updateNodeData = useJimengStore((s) => s.updateNodeData);

  return (
    <div
      // Batch 812 SOURCE_FACT: 源站标题行盒 32 高但内容**顶对齐**在 -31，
      // 不是"在 32px 里居中"（居中会把 24 高的文字放到 -27，低 4px）。
      // justify-between + pr-px 保留：源站标签钮贴着卡片右缘**内侧 1px**
      // （实测 24 宽 @x=544、卡片宽 569 → 右缘 568）。
      className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start justify-between pr-px text-left"
      onDoubleClick={(e) => {
        e.stopPropagation();
        onDblClick();
      }}
    >
      <div className="flex h-6 min-w-0 items-center gap-1 text-white/70">
        <FileBadgeIcon size={16} />
        <JimengNodeTitle id={id} title={d.title} />
      </div>
      {d.hasMedia ? (
        <span className="relative">
          <button
            type="button"
            // Batch 812 SOURCE_FACT: 源站实名是 `Add tags`（此前复刻自造
            // 「节点颜色标记」）。行为不变 —— 仍是源站的 禁止+五色 选色盘 (batch 31)。
            aria-label="Add tags"
            onClick={(e) => {
              e.stopPropagation();
              onToggleTagPicker();
            }}
            // 源站实测 24×24、圆角 8、padding 0 4px；复刻此前是 16×16 无圆角。
            className="nodrag flex size-6 items-center justify-center rounded-lg px-1"
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
                  onToggleTagPicker();
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
                    onToggleTagPicker();
                  }}
                  className="size-4 rounded-full"
                  style={{ background: color }}
                />
              ))}
            </span>
          ) : null}
        </span>
      ) : null}
    </div>
  );
}
