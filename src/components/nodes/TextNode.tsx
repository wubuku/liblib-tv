"use client";

import { memo, useState } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface TextNodeData extends Record<string, unknown> {
  content: string;
}

export type TextNodeType = Node<TextNodeData>;

/* 源站 text 节点文档图标（0 0 20 20 四行文档，Batch 218 采样）。 */
function DocGlyph() {
  return (
    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 20 20" fill="none">
      <path
        d="M17.4 0A2.6 2.6 0 0 1 20 2.6v14.8a2.6 2.6 0 0 1-2.6 2.6H2.6A2.6 2.6 0 0 1 0 17.4V2.6A2.6 2.6 0 0 1 2.6 0zM4 16.26h8v-1.8H4zm0-3.57h12V7.3H4zm0-3.57h12v-1.8H4z"
        fill="currentColor"
      />
    </svg>
  );
}

/* Batch 218 采样的 5 操作按钮（源站直采）。 */
const actionButtons = [
  "自己编写内容",
  "文生视频",
  "图片反推提示词",
  "文字生音乐",
  "GVLM 3.1",
] as const;

/* Batch 218: 源站 text 节点重采——markdown 展示块 + 尝试按钮组（非 textarea
   编辑器）。759×759，悬浮标题条在 -28px，shell rounded-xl #171717。
   内容渲染为 markdown（无 textarea——编辑入口未采样）。 */
function TextNodeComponent({ data }: NodeProps<TextNodeType>) {
  const [activeAction, setActiveAction] = useState<string | null>(null);

  return (
    <div className="relative" style={{ width: 350 }}>
      {/* 悬浮标题条（源站：文档图标 + 节点标题） */}
      <div className="absolute left-0 top-[-28px] flex w-full items-center gap-1 text-[#8f8f8f]">
        <DocGlyph />
        <span className="truncate text-[13px]">文本节点</span>
      </div>
      {/* 卡壳 */}
      <div className="node-shell relative flex h-[350px] w-full flex-col overflow-hidden rounded-xl border border-[#363636] bg-[#171717] p-3">
        <span className="mb-2 text-[11px] text-[#777]">尝试:</span>
        <div className="flex flex-wrap gap-1.5">
          {actionButtons.map((label) => (
            <button
              key={label}
              type="button"
              data-text-action={label}
              onClick={() => setActiveAction(label)}
              className={cn(
                "flex h-7 items-center rounded-full px-2.5 text-xs transition-colors",
                activeAction === label
                  ? "bg-white/[0.1] text-[#f7f7f7]"
                  : "bg-white/[0.05] text-[#aaa] hover:bg-white/[0.09] hover:text-white",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        {/* markdown 展示区（源站为 markdown 渲染，无 textarea） */}
        <div className="mt-2 min-h-0 flex-1 overflow-y-auto rounded-lg bg-white/[0.03] p-2">
          <p className="text-xs leading-5 text-[#a5a5a5]">
            {data.content || "写下你想讲的故事、场景或角色设定。"}
          </p>
        </div>
      </div>
      {/* Batch 355: 与其余节点类型对齐补具名把手（data-handleid 可寻址，
          batch 57 连接合同依赖 source/target 命名）。 */}
      <Handle type="target" position={Position.Left} id="target" isConnectable />
      <Handle type="source" position={Position.Right} id="source" isConnectable />
    </div>
  );
}

export const TextNode = memo(TextNodeComponent);
