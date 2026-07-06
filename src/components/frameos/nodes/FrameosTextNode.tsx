"use client";

import type { NodeProps } from "@xyflow/react";
import { useState } from "react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { TextNodeIcon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

export function FrameosTextNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const [content, setContent] = useState(data.content ?? "");
  const { title } = data;

  return (
    <FrameosNodeShell
      kind="text"
      title={title}
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
          padding: "12px",
          display: "flex",
        }}
      >
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          spellCheck={false}
          className="text-display"
          style={{
            flex: 1,
            width: "100%",
            height: "100%",
            background: "transparent",
            color: "#C2C2C2",
            fontSize: 13,
            lineHeight: "20.15px",
            border: "none",
            outline: "none",
            resize: "none",
            fontFamily: "inherit",
            padding: 0,
          }}
        />
      </div>
    </FrameosNodeShell>
  );
}
