"use client";

import { memo, useState } from "react";
import { Clapperboard, FileUp, Sparkles } from "lucide-react";
import {
  Handle,
  Position,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface ScriptGeneratorNodeData extends Record<string, unknown> {
  title?: string;
}

export type ScriptGeneratorNodeType = Node<
  ScriptGeneratorNodeData,
  "script-generator"
>;

// Batch 116: 2026-09-06 丢弃式采样（liblib-canvas-sampling-2026-09-06 §3）——
// 三种尝试模式、参考图入口、提示词与 GVLM 3.1 模型为源站观察；
// 生成服务不存在，本地仅维护选择与草稿。
const attemptModes = [
  "剧本生成分镜脚本",
  "角色生成分镜脚本",
  "自己编写分镜脚本",
] as const;

const promptPlaceholder = "描述剧情片段、故事，为你生成分镜脚本";

function ScriptGeneratorNodeComponent({
  data,
  selected,
}: NodeProps<ScriptGeneratorNodeType>) {
  const [attempt, setAttempt] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");

  return (
    <div
      data-script-generator-node
      className={cn(
        "relative flex h-[350px] w-[350px] flex-col overflow-hidden rounded-[10px] border bg-[#242424] px-4 py-3",
        selected
          ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]"
          : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="flex items-center gap-2 pb-2">
        <Clapperboard size={14} className="text-[#d8d8d8]" />
        <span className="text-sm font-medium text-[#ededed]">{data.title ?? "脚本生成器"}</span>
      </div>

      <div className="pb-1 text-[11px] text-[#8c8c8c]">尝试：</div>
      <div className="space-y-1">
        {attemptModes.map((mode) => (
          <button
            key={mode}
            type="button"
            data-script-generator-attempt={mode}
            aria-pressed={attempt === mode}
            onClick={() => setAttempt(attempt === mode ? null : mode)}
            className={cn(
              "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs transition-colors",
              attempt === mode
                ? "bg-[#09caf5]/15 text-[#09caf5]"
                : "bg-white/[0.04] text-[#d8d8d8] hover:bg-white/[0.08]",
            )}
          >
            <Sparkles size={12} className="shrink-0" />
            <span className="min-w-0 flex-1 truncate">{mode}</span>
          </button>
        ))}
      </div>

      <button
        type="button"
        data-script-generator-reference
        className="mt-2 flex h-8 items-center gap-2 rounded-lg border border-dashed border-white/[0.12] px-2 text-[11px] text-[#9a9a9a] hover:border-white/[0.24] hover:text-white"
      >
        <FileUp size={12} />
        参考图
      </button>

      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        placeholder={promptPlaceholder}
        aria-label="脚本生成器提示词"
        className="mt-2 min-h-[52px] w-full flex-1 resize-none rounded-lg bg-white/[0.04] px-2 py-1.5 text-xs leading-5 text-[#e0e0e0] outline-none placeholder:text-[#666]"
      />

      <div className="mt-2 flex items-center justify-between">
        <span className="flex items-center gap-1 rounded bg-white/[0.06] px-1.5 py-0.5 text-[10px] text-[#9a9a9a]">
          <Sparkles size={10} />
          GVLM 3.1
        </span>
        <span className="rounded bg-white/[0.06] px-1.5 py-0.5 text-[10px] text-[#9a9a9a]">6</span>
      </div>
    </div>
  );
}

export const ScriptGeneratorNode = memo(ScriptGeneratorNodeComponent);
