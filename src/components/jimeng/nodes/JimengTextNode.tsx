"use client";

import { useEffect, useRef, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengTextNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";

/**
 * 文字节点 (Batch 17/38)。结构与视频节点同族 (SOURCE_FACT §5 的视频节点骨架)，
 * 尺寸/样式为 CLONE_DECISION (源站文字节点未提取)。
 * Batch 38: 双击卡片进入行内编辑，Enter/失焦提交。
 */
export function JimengTextNode({ id, data, selected }: NodeProps) {
  const d = data as JimengTextNodeData;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(d.text);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing) taRef.current?.focus();
  }, [editing]);

  const commit = () => {
    setEditing(false);
    // mock: 编辑内容仅存于节点本地状态，未写回全局 store (CLONE_DECISION)
  };

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center gap-1.5 text-left text-white/70">
        <FileBadgeIcon size={16} />
        <span className="max-w-full truncate whitespace-nowrap text-[13px] leading-[22px]">
          {d.title}
        </span>
      </div>

      <div
        className="h-full w-full overflow-hidden rounded-lg p-4"
        style={{
          background: "linear-gradient(to right bottom, rgb(30,30,32), rgb(22,22,24))",
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
          <p className="text-[13px] leading-[22px] whitespace-pre-wrap text-white/85">
            {draft || d.text}
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
