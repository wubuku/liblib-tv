import { memo, useState, useRef } from "react";
import { Handle, Position, type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { PlusIndicator } from "../PlusIndicator";

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

function PlusIcon() {
  return null;
}

export function ScriptNode({ id, data, selected }: NodeProps<ScriptNodeType>) {
  const { title = "剧本", content = defaultContent } = data;
  const { deleteElements } = useReactFlow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const [showLeftHandle, setShowLeftHandle] = useState(false);
  const [showRightHandle, setShowRightHandle] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteElements({ nodes: [{ id }] });
  };

  // Show handles when hovering over the node
  const handleMouseEnter = () => {
    setShowLeftHandle(true);
    setShowRightHandle(true);
  };

  const handleMouseLeave = () => {
    setShowLeftHandle(false);
    setShowRightHandle(false);
  };

  return (
    <div
      ref={nodeRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "w-[320px] overflow-visible rounded-xl border bg-[#212121] flex flex-col transition-shadow group",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.3)]" : "border-[#363636]",
        !selected && "hover:shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
      )}
    >
      {/* Delete button - visible when selected */}
      {selected && (
        <button
          onClick={handleDelete}
          className="absolute -top-2 -right-2 z-10 w-5 h-5 bg-[#f53f3f] rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[#ff6a6f]"
          aria-label="Delete node"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M2 2L8 8M8 2L2 8" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}

      {/* Left Handle - Target */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        className="!opacity-0 !pointer-events-auto"
      />
      {/* Left "+" indicator (42x42 transparent circle) */}
      <div
        className={cn(
          "transition-opacity duration-150",
          showLeftHandle ? "opacity-100" : "opacity-0"
        )}
      >
        <PlusIndicator side="left" />
      </div>

      {/* Right Handle - Source */}
      <Handle
        type="source"
        position={Position.Right}
        id="source"
        className="!opacity-0 !pointer-events-auto"
      />
      {/* Right "+" indicator (42x42 transparent circle) */}
      <div
        className={cn(
          "transition-opacity duration-150",
          showRightHandle ? "opacity-100" : "opacity-0"
        )}
      >
        <PlusIndicator side="right" />
      </div>

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
    </div>
  );
}

export default memo(ScriptNode);
