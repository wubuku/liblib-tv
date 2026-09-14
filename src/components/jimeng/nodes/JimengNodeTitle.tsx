"use client";

import { useEffect, useRef, useState } from "react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 节点标题文本 (Batch 88)。
 *
 * SOURCE_FACT (batch 87/88): 各类节点的标题行均支持点击行内重命名
 * (源站 aria "Rename <标题>"，视频/文本节点实证)，Enter 提交、可撤销。
 * 共享组件：非编辑态渲染纯文本 (含原生 title 悬停提示, batch 45)，
 * 点击进入 input，Enter/失焦提交 (renameNode, 单条历史)，Escape 取消。
 */
export function JimengNodeTitle({ id, title }: { id: string; title: string }) {
  const renameNode = useJimengStore((s) => s.renameNode);
  const [renaming, setRenaming] = useState(false);
  const [draft, setDraft] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (renaming) inputRef.current?.select();
  }, [renaming]);

  const commit = () => {
    const next = draft.trim();
    if (renaming && next && next !== title) renameNode(id, next);
    setRenaming(false);
  };

  if (renaming) {
    return (
      <input
        ref={inputRef}
        value={draft}
        data-testid="node-rename-input"
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(title);
            setRenaming(false);
          }
        }}
        onMouseDown={(e) => e.stopPropagation()}
        className="max-w-full truncate whitespace-nowrap rounded border border-white/30 bg-transparent px-1 text-[13px] leading-[22px] text-white/70 outline-none"
      />
    );
  }

  return (
    <span
      className="max-w-full cursor-text truncate whitespace-nowrap text-[13px] leading-[22px]"
      title={title}
      data-testid="node-title-text"
      onClick={(e) => {
        e.stopPropagation();
        setDraft(title);
        setRenaming(true);
      }}
    >
      {title}
    </span>
  );
}
