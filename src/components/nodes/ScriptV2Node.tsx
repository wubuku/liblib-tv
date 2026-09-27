"use client";

import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

export interface ScriptV2NodeData extends Record<string, unknown> {
  title?: string;
}

export type ScriptV2NodeType = Node<ScriptV2NodeData, "script-v2">;

/* 源站节点头部文档图标（0 0 20 20，四行文档，Batch 208 采样）。 */
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

// Batch 207/208: 源站 script-v2 节点（350×350，标题「脚本生成器」）——
// 卡壳 rounded-xl / #171717（Surface-Panel-background）/ 选中描边
// canvas-node-border-selected；标题条悬浮于卡片上方 -28px（随流缩放）。
// Batch 533: 2026-09-27 CDP 补采（liblib-source-exploration-2026-09-25
// 截图 39 + 节点 DOM 文本）——分镜会话后卡内为进度卡形态：
// ①确认镜头—②准备资产—③合成提示词（圆圈+连线+下方标签）+
// 底部「打开脚本节点 →」按钮（重新打开全屏编辑器）。
// 新建态内部从未采样（207 占位合同）；进度卡为唯一实证内部形态，
// clone 以其为卡体；标题保持 207 的「脚本生成器」默认。
const progressSteps = [
  { step: 1, label: "确认镜头", active: true },
  { step: 2, label: "准备资产", active: false },
  { step: 3, label: "合成提示词", active: false },
] as const;

function ScriptV2NodeInner({ data }: NodeProps<ScriptV2NodeType>) {
  const openStoryboardEditor = useUIStore((state) => state.openStoryboardEditor);

  return (
    <div className="relative" style={{ width: 350 }}>
      <div className="absolute left-0 top-[-28px] flex w-full items-center gap-1 text-[#8f8f8f]">
        <DocGlyph />
        <span className="truncate text-[13px]">{data.title ?? "脚本生成器"}</span>
      </div>
      <div
        className={cn(
          "node-shell relative flex h-[350px] w-full flex-col overflow-hidden rounded-xl border border-[#363636] bg-[#171717]",
        )}
      >
        <Handle type="target" position={Position.Left} isConnectable />
        <Handle type="source" position={Position.Right} isConnectable />
        <div className="flex flex-1 flex-col items-center justify-center gap-6 px-5">
          <div className="flex w-full items-start justify-between">
            {progressSteps.map((item, index) => (
              <div key={item.step} className="flex flex-1 items-start">
                {index > 0 && <span className="mt-[13px] h-px flex-1 bg-white/10" />}
                <div className="flex flex-col items-center gap-1.5">
                  <span
                    className={cn(
                      "flex size-[26px] items-center justify-center rounded-full text-xs",
                      item.active ? "bg-[#e8e8e8] text-[#1a1a1a]" : "border border-white/15 text-[#8c8c8c]",
                    )}
                  >
                    {item.step}
                  </span>
                  <span className={cn("whitespace-nowrap text-[11px]", item.active ? "text-[#d8d8d8]" : "text-[#777]")}>
                    {item.label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="p-4">
          <button
            type="button"
            data-script-v2-open
            onClick={openStoryboardEditor}
            className="flex h-9 w-full items-center justify-center gap-1 rounded-lg bg-white/[0.06] text-xs text-[#d8d8d8] hover:bg-white/[0.1] hover:text-white"
          >
            打开脚本节点 <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export const ScriptV2Node = memo(ScriptV2NodeInner);
