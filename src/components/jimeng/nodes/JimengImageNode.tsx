"use client";

import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengImageNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { JimengImageNodeToolbar } from "@/components/jimeng/JimengImageNodeToolbar";
import { JimengImageGenPanel } from "@/components/jimeng/JimengImageGenPanel";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 图片节点 (Batch 17)。结构与视频节点同族 (SOURCE_FACT §5 的视频节点骨架)；
 * 批 195 补源站图片节点提取: 569×320 同视频卡、选中工具条见
 * JimengImageNodeToolbar。
 */
export function JimengImageNode({ id, data, selected }: NodeProps) {
  const d = data as JimengImageNodeData;
  const pushToast = useJimengStore((s) => s.pushToast);
  const soloSelected =
    useJimengStore((s) => s.nodes.filter((n) => n.selected).length) === 1;

  return (
    <>
      {/* 批 530 SOURCE_FACT: 空图片节点 (无 poster) 选中弹图片生成面板；
          带画面节点维持批 208 加工工具条 */}
      {d.poster ? (
        <JimengImageNodeToolbar
          visible={selected === true && soloSelected}
          onAction={(label) => pushToast(`${label}（mock）`)}
        />
      ) : (
        <JimengImageGenPanel visible={selected === true && soloSelected} />
      )}
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center gap-1.5 text-left text-white/70">
        <FileBadgeIcon size={16} />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      <div
        className="relative h-full w-full overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : undefined,
        }}
      >
        {d.poster ? (
          // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报
          <img
            src={d.poster}
            alt={d.title}
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/40">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
              <rect x="2" y="2" width="16" height="16" rx="3" stroke="currentColor" strokeWidth="1.3" />
              <circle cx="7" cy="7.5" r="1.6" fill="currentColor" />
              <path d="m4 15 4.5-5 3 3.4L14 10.5l2.5 3" stroke="currentColor" strokeWidth="1.3" fill="none" />
            </svg>
          </span>
        )}
        {/* 截取帧产出瞬态 (Batch 197 SOURCE_FACT「正在上传图片 0%」)；
            布局为 CLONE_DECISION (源站仅文本级证据) */}
        {typeof d.uploadProgress === "number" && d.uploadProgress < 100 ? (
          <div
            className="absolute inset-0 flex items-center justify-center bg-black/45"
            data-jimeng-image-uploading=""
          >
            <span className="text-[13px] text-white/90">
              正在上传图片 {d.uploadProgress}%
            </span>
          </div>
        ) : null}
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
    </>
  );
}
