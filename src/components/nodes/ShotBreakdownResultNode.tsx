"use client";

import Image from "next/image";
import { memo, useState } from "react";
import { ImageIcon, Music2, Play, Share2, Video } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import type {
  ShotBreakdownDimension,
  ShotBreakdownResultItem,
} from "@/lib/shotBreakdownResults";

export interface ShotBreakdownResultNodeData extends Record<string, unknown> {
  resultKey: string;
  category: ShotBreakdownDimension;
  title: string;
  items: ShotBreakdownResultItem[];
  sourceBreakdownId: string;
}

export type ShotBreakdownResultNodeType = Node<
  ShotBreakdownResultNodeData,
  "shot-breakdown-result"
>;

function ResultAction({
  itemId,
  active,
  onActivate,
}: {
  itemId: string;
  active: boolean;
  onActivate: () => void;
}) {
  return (
    <button
      type="button"
      data-shot-breakdown-item-action={itemId}
      aria-label={`将 ${itemId} 用作参考`}
      aria-pressed={active}
      title="用作参考"
      onClick={(event) => {
        event.stopPropagation();
        onActivate();
      }}
      className={cn(
        "nodrag nopan absolute right-3 top-3 flex size-8 items-center justify-center rounded-[8px] border text-white transition-colors",
        active
          ? "border-[#24cbed]/70 bg-[#0b6b80]"
          : "border-white/20 bg-black/55 hover:bg-black/75",
      )}
    >
      <Share2 size={16} />
    </button>
  );
}

function VisualResultCard({
  item,
  active,
  onActivate,
}: {
  item: ShotBreakdownResultItem;
  active: boolean;
  onActivate: () => void;
}) {
  const KindIcon = item.kind === "video" ? Video : ImageIcon;

  return (
    <article
      data-shot-breakdown-item={item.id}
      className="min-w-0 overflow-hidden rounded-[10px] bg-[#2b2b2b]"
    >
      <div className="flex h-[42px] items-center gap-2.5 px-4 text-[17px] text-[#aaa]">
        {item.kind === "video" ? (
          <Play size={17} fill="currentColor" />
        ) : (
          <KindIcon size={17} />
        )}
        <span className="min-w-0 flex-1 truncate">
          {item.id}｜{item.summary}
        </span>
        {item.resolution && (
          <span className="shrink-0 tabular-nums text-[#888]">{item.resolution}</span>
        )}
      </div>
      <div className="relative mx-4 mb-4 aspect-video overflow-hidden rounded-[8px] bg-[#1d1d1d]">
        {item.imageUrl && (
          <Image
            src={item.imageUrl}
            alt={`${item.id} ${item.summary}`}
            fill
            sizes="500px"
            className="object-cover"
            unoptimized
          />
        )}
        <ResultAction itemId={item.id} active={active} onActivate={onActivate} />
      </div>
    </article>
  );
}

function MusicResult({
  item,
  active,
  onActivate,
}: {
  item: ShotBreakdownResultItem;
  active: boolean;
  onActivate: () => void;
}) {
  return (
    <article
      data-shot-breakdown-item={item.id}
      className="relative flex h-full flex-col rounded-[10px] bg-[#2b2b2b] p-4"
    >
      <div className="flex h-8 items-center gap-2 pr-9 text-[16px] text-[#aaa]">
        <Music2 size={17} />
        <span className="truncate">
          {item.id}｜{item.summary}
        </span>
      </div>
      <ResultAction itemId={item.id} active={active} onActivate={onActivate} />
      <div
        data-shot-breakdown-waveform
        className="mt-3 flex min-h-0 flex-1 items-center gap-[3px] overflow-hidden rounded-[8px] border border-white/10 bg-[#242424] px-3"
      >
        {Array.from({ length: 45 }, (_, index) => (
          <span
            key={index}
            className="w-[2px] shrink-0 rounded-full bg-[#656565]"
            style={{ height: `${12 + ((index * 17) % 44)}px` }}
          />
        ))}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[12px] tabular-nums text-[#aaa]">
        <span>00:00 / 00:14</span>
        <button
          type="button"
          aria-label="播放 BGM"
          className="nodrag nopan flex size-6 items-center justify-center rounded-full border border-white/15 bg-[#303030] text-white"
        >
          <Play size={11} fill="currentColor" />
        </button>
      </div>
    </article>
  );
}

function ShotBreakdownResultNodeComponent({
  data,
  selected,
}: NodeProps<ShotBreakdownResultNodeType>) {
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const isMusic = data.category === "music";

  return (
    <div
      data-shot-breakdown-result={data.resultKey}
      data-shot-breakdown-category={data.category}
      className={cn(
        "relative h-full w-full overflow-visible rounded-[14px] border bg-[#292929] p-3",
        selected
          ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]"
          : "border-white/[0.08]",
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        style={{ width: 20, height: 20 }}
      />
      <div className="pointer-events-none absolute -top-[38px] left-0 flex h-[30px] items-center gap-2 whitespace-nowrap text-[18px] text-[#969696]">
        {isMusic ? <Music2 size={18} /> : <ImageIcon size={18} />}
        <span>{data.title}</span>
      </div>

      {isMusic ? (
        <MusicResult
          item={data.items[0]}
          active={activeItemId === data.items[0].id}
          onActivate={() => setActiveItemId(data.items[0].id)}
        />
      ) : (
        <div className="grid h-full grid-cols-2 content-start gap-4">
          {data.items.map((item) => (
            <VisualResultCard
              key={item.id}
              item={item}
              active={activeItemId === item.id}
              onActivate={() => setActiveItemId(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export const ShotBreakdownResultNode = memo(ShotBreakdownResultNodeComponent);
