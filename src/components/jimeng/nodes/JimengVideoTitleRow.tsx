"use client";

import { Ban, Tag } from "lucide-react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
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
      className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center justify-between text-left"
      onDoubleClick={(e) => {
        e.stopPropagation();
        onDblClick();
      }}
    >
      <div className="flex min-w-0 items-center gap-1.5 text-white/70">
        <FileBadgeIcon size={16} />
        <span
          className="max-w-full truncate whitespace-nowrap text-[13px] leading-[22px]"
          title={d.title}
        >
          {d.title}
        </span>
      </div>
      {d.hasMedia ? (
        <span className="relative">
          <button
            type="button"
            aria-label="节点颜色标记"
            onClick={(e) => {
              e.stopPropagation();
              onToggleTagPicker();
            }}
            className="flex size-4 items-center justify-center"
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
