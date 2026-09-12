"use client";

import { useState } from "react";
import { ArrowUp, AtSign, ChevronDown, Maximize2, Plus } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";
import { VipDiamond } from "@/components/jimeng/icons";

/**
 * 空视频节点选中后下方弹出的视频生成面板 (Batch 3)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §7):
 * - 载体 xyflow <NodeToolbar> position=bottom；面板 680×208，节点下方 20px，居中
 * - 本体 form: rgb(32,32,32) r20 内边距 17
 * - 三行: 素材栏 h-12 (+ 按钮) / 提示词占位区 / 底部控制行 h-8
 * - 底部行左组: 即梦 Seedance 2.0 VIP ✦∨ · 16:9·720P ✦·1∨ · 全能参考∨ · 4s∨ · @
 * - 底部行右组: ✦56 积分 (white/60) + 32px 圆形发送钮 bg rgba(255,255,255,0.16)
 *   禁用态 (sr-only "请输入提示词")
 * - 右上角 40×40 展开钮 (icon 24, white/60)
 * mock: 提示词不可输入、下拉不开合 (Batch 5 接 store)。
 */
export function JimengGenPanel({ visible }: { visible: boolean }) {
  // Batch 40: 提示词可输入；发送后 pushToast (mock，不产生真实任务)
  const [prompt, setPrompt] = useState("");
  const pushToast = useJimengStore((s) => s.pushToast);
  const canSend = prompt.trim().length > 0;

  const send = () => {
    if (!canSend) return;
    setPrompt("");
    pushToast("生成任务已提交（mock）");
  };

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={20}>
      <div className="relative h-[208px] w-[680px]">
        {/* 右上角展开钮 (骑在面板顶边) */}
        <button
          type="button"
          aria-label="展开面板"
          className="absolute -top-1.5 right-0 z-[2] flex size-10 items-center justify-center"
        >
          <span className="flex size-6 items-center justify-center rounded-full text-white/60">
            <Maximize2 size={13} />
          </span>
        </button>

        <form
          className="flex h-full w-full flex-col justify-between rounded-[20px] bg-[#202020] p-[17px]"
          onSubmit={(e) => {
            e.preventDefault();
            if (canSend) {
              pushToast("生成任务已提交（mock）");
              setPrompt("");
            }
          }}
        >
          {/* 素材栏 */}
          <div className="flex h-12 w-full items-center">
            <button
              type="button"
              aria-label="上传参考图"
              className="flex size-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
            >
              <Plus size={20} />
            </button>
          </div>

          {/* 提示词输入区 (Batch 40: 可编辑) */}
          <div className="flex w-full items-start">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="上传参考图、输入文字或 @ 主体，描述你想生成的视频"
              rows={2}
              className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none placeholder:text-white/35"
            />
          </div>

          {/* 底部控制行 */}
          <div className="flex h-8 w-full items-center justify-between gap-1">
            <div className="flex min-w-0 items-center gap-1">
              <button
                type="button"
                className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                即梦 Seedance 2.0 VIP
                <VipDiamond size={12} />
                <ChevronDown size={12} className="text-white/60" />
              </button>
              <button
                type="button"
                className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                16:9 · 720P
                <VipDiamond size={12} />
                · 1
                <ChevronDown size={12} className="text-white/60" />
              </button>
              <button
                type="button"
                className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                全能参考
                <ChevronDown size={12} className="text-white/60" />
              </button>
              <button
                type="button"
                className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                4s
                <ChevronDown size={12} className="text-white/60" />
              </button>
              <button
                type="button"
                aria-label="提及主体"
                className="flex size-8 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
              >
                <AtSign size={15} />
              </button>
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              <span className="inline-flex items-center gap-1 text-dreamina-number text-[12px] font-medium text-white/60">
                <VipDiamond size={12} />
                56
              </span>
              <button
                type="submit"
                aria-label="生成"
                disabled={!canSend}
                className={`flex size-8 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-white text-black hover:bg-white/90"
                    : "bg-white/[0.16] text-white/20"
                }`}
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </NodeToolbar>
  );
}
