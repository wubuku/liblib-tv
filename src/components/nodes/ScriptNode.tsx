import { memo } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { cn } from "@/lib/utils";

interface ScriptNodeData extends Record<string, unknown> {
  title?: string;
  content?: string;
}

type ScriptNodeType = Node<ScriptNodeData, "script">;

const defaultContent = `第一集：咖啡馆对峙
角色：陈默(男主,面容冷峻)、林小婉(女主,眼神忧郁)
场景1：咖啡馆
陈默坐在窗边，咖啡已凉。林小婉走进来，走到他对面坐下。
林小婉提高音量说："你到底还要躲我到什么时候？"
陈默不正眼看她，声音低沉："我没有躲你。"
林小婉眼眶红了，说："你知道我有多担心吗？"
陈默转过头，无声地冷笑了一下，说："当初你离开的时候，怎么没想过我会担心？"`;

function ScriptIcon({ className }: { className?: string }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M4 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1Z"
        stroke="currentColor"
        strokeWidth="1.2"
      />
      <path
        d="M6 5h4M6 8h4M6 11h2"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ScriptNode({ data, selected }: NodeProps<ScriptNodeType>) {
  const { title = "剧本", content = defaultContent } = data;

  return (
    <div
      className={cn(
        "w-[320px] rounded-lg border bg-[#1f1f1f] transition-shadow",
        selected ? "border-[#09caf5]" : "border-[#363636]",
        !selected && "hover:shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-[#363636] px-4 py-3">
        <ScriptIcon className="text-[#f7f7f7]" />
        <span className="text-sm font-semibold text-[#f7f7f7]">{title}</span>
      </div>

      {/* Content */}
      <div className="max-h-[300px] overflow-y-auto p-4">
        <p className="whitespace-pre-wrap text-sm font-normal leading-[1.6] text-[#f7f7f7]">
          {content}
        </p>
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-2 border-t border-[#363636] px-4 py-2">
        {/* Footer actions can be added here */}
      </div>

      {/* React Flow Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-[#525252]"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-[#525252]"
      />
    </div>
  );
}

export default memo(ScriptNode);
