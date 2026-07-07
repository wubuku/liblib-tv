"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeProps } from "@xyflow/react";
import { useFrameosStore } from "@/store/frameosStore";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { TextNodeIcon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

export function FrameosTextNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const initialContent = (data.content as string) ?? "";
  const [content, setContent] = useState(initialContent);
  const [isEditing, setIsEditing] = useState(false);
  const updateNodeData = useFrameosStore((s) => s.updateNodeData);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // 同步外部 data.content 变化（例如撤销/重做）
  useEffect(() => {
    if (!isEditing) setContent((data.content as string) ?? "");
  }, [data.content, isEditing]);

  // 进入编辑模式时自动 focus
  useEffect(() => {
    if (isEditing && taRef.current) {
      taRef.current.focus();
      taRef.current.select();
    }
  }, [isEditing]);

  // 双击节点进入编辑
  const onDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  // 失焦保存并退出
  const onBlur = () => {
    setIsEditing(false);
    if (content !== initialContent) {
      updateNodeData(id, { content, title: content.slice(0, 20) || "文本节点" });
    }
  };

  return (
    <FrameosNodeShell
      kind="text"
      title={data.title as string}
      titleIcon={<TextNodeIcon size={12} />}
      selected={selected}
      showLeftHandle
      showRightHandle
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={300}
      height={200}
    >
      <div
        className="card-body"
        style={{
          flex: 1,
          padding: 12,
          display: "flex",
          cursor: isEditing ? "text" : "pointer",
        }}
        onDoubleClick={onDoubleClick}
      >
        {isEditing ? (
          <textarea
            ref={taRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={onBlur}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                (e.target as HTMLTextAreaElement).blur();
              }
            }}
            spellCheck={false}
            style={{
              flex: 1,
              width: "100%",
              height: "100%",
              background: "transparent",
              color: "#C2C2C2",
              fontSize: 13,
              lineHeight: "20.15px",
              border: "1px solid rgba(96,165,250,0.5)",
              borderRadius: 6,
              padding: 6,
              outline: "none",
              resize: "none",
              fontFamily: "inherit",
            }}
          />
        ) : (
          <div
            className="text-display"
            style={{
              flex: 1,
              color: "#C2C2C2",
              fontSize: 13,
              lineHeight: "20.15px",
              whiteSpace: "pre-wrap",
              overflow: "auto",
            }}
          >
            {content || (
              <span style={{ color: "#5A5A5A", fontStyle: "italic" }}>
                （双击编辑文本）
              </span>
            )}
          </div>
        )}
      </div>
    </FrameosNodeShell>
  );
}
