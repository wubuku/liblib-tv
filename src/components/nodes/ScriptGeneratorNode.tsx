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
import { useUIStore } from "@/store/uiStore";

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
// Batch 528: 2026-09-27 第五/八轮源站采样（liblib-source-exploration-2026-09-25
// NOTES §11/§140）——单击尝试入口仅选中/跟随节点（正在跟随/取消ESC），未展开子流程；
// clone 将跟随态与入口选择同步，再点同项或取消/ESC 退出。
// Batch 531: 2026-09-27 CDP 补采（同目录截图 38）修正 round-8 结论——
// 「自己编写分镜脚本」入口实际打开全屏分镜脚本编辑器；前两个入口保持跟随合同。
const attemptModes = [
  "剧本生成分镜脚本",
  "角色生成分镜脚本",
  "自己编写分镜脚本",
] as const;

const promptPlaceholder = "描述剧情片段、故事，为你生成分镜脚本";

function ScriptGeneratorNodeComponent({ id, data, selected }: NodeProps<ScriptGeneratorNodeType>) {
  const [attempt, setAttempt] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const isFollowingSession = useUIStore((state) => state.isFollowingSession);
  const setFollowingSession = useUIStore((state) => state.setFollowingSession);
  const openStoryboardEditor = useUIStore((state) => state.openStoryboardEditor);
  const storyboardSessionNodeId = useUIStore((state) => state.storyboardSessionNodeId);
  const setStoryboardSessionNode = useUIStore((state) => state.setStoryboardSessionNode);

  // Batch 534: 源站实测（截图 39）——自写会话后本卡转为进度卡
  // （①确认镜头—②准备资产—③合成提示词 + 打开脚本节点 →），持久不回退。
  const inStoryboardSession = storyboardSessionNodeId === id;

  // Batch 528: 入口高亮与跟随态同步——横幅取消/ESC 结束跟随即视为无选中入口。
  const activeAttempt = isFollowingSession ? attempt : null;

  const toggleAttempt = (mode: string) => {
    // Batch 531: 自写入口不进入跟随，直接打开全屏分镜脚本编辑器。
    if (mode === "自己编写分镜脚本") {
      setStoryboardSessionNode(id);
      openStoryboardEditor();
      return;
    }
    const next = activeAttempt === mode ? null : mode;
    setAttempt(next);
    setFollowingSession(next !== null);
  };

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

      {inStoryboardSession ? (
        <>
          <div className="flex flex-1 flex-col items-center justify-center">
            <div className="flex w-full items-start">
              {[
                { step: 1, label: "确认镜头", active: true },
                { step: 2, label: "准备资产", active: false },
                { step: 3, label: "合成提示词", active: false },
              ].map((item, index) => (
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
          <button
            type="button"
            data-script-generator-open-storyboard
            onClick={openStoryboardEditor}
            className="flex h-9 w-full items-center justify-center gap-1 rounded-lg bg-white/[0.06] text-xs text-[#d8d8d8] hover:bg-white/[0.1] hover:text-white"
          >
            打开脚本节点 <span aria-hidden="true">→</span>
          </button>
        </>
      ) : (
        <>
          <div className="pb-1 text-[11px] text-[#8c8c8c]">尝试：</div>
          <div className="space-y-1">
            {attemptModes.map((mode) => (
              <button
                key={mode}
                type="button"
                data-script-generator-attempt={mode}
                aria-pressed={activeAttempt === mode}
                onClick={() => toggleAttempt(mode)}
                className={cn(
                  "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs transition-colors",
                  activeAttempt === mode
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
        </>
      )}
    </div>
  );
}

export const ScriptGeneratorNode = memo(ScriptGeneratorNodeComponent);
