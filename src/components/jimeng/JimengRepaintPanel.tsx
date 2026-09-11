"use client";

import { ArrowUp, AtSign, ChevronDown, Plus } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 局部重拍编辑态面板 (Batch 5)。
 *
 * 证据 (SOURCE_FACT, /tmp extract 23-repaint-panel.png → docs batch5 截图):
 * 进入局部重拍后: 节点标题行隐藏；节点下方出现「帧条选区」(整段缩略图胶片 +
 * 白框选区窗口 + 时长标签 4.0s + 两侧拖拽把手)；再下方为生成面板变体:
 * 参考缩略图 chip (00:06) + "+"、提示词行含 chip「00:00—00:04 重拍片段」(蓝色描边)
 * + 占位「描述你如何调整这一片段」、底部 即梦 Seedance 2.5 ✦∨ / 6s / @ /
 * ✦ 96/208 积分 / 白色可用发送钮。
 * mock: 选区窗口为静态 4.0s；发送钮可点但仅关闭编辑态 (无真实任务)。
 */
export function JimengRepaintPanel({
  visible,
  data,
  onSubmit,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  onSubmit: () => void;
}) {
  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={20}>
      <div className="flex w-[680px] flex-col gap-3">
        {/* 帧条选区 */}
        <div className="relative h-16 overflow-hidden rounded-lg border border-white/10">
          <div
            className="absolute inset-0 opacity-80"
            style={
              data.poster
                ? {
                    backgroundImage: `url(${data.poster})`,
                    backgroundRepeat: "repeat-x",
                    backgroundSize: "auto 100%",
                  }
                : { background: "linear-gradient(to right, #222, #141414)" }
            }
          />
          {/* 白框选区窗口 (静态 4.0s) */}
          <div className="absolute inset-y-0 left-[2%] w-[52%] border-2 border-white/90 rounded-md">
            <span className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-black/60 px-1.5 py-0.5 text-[11px] text-white">
              4.0s
            </span>
            <span className="absolute -left-1 top-1/2 h-6 w-1.5 -translate-y-1/2 rounded-full bg-white" />
            <span className="absolute -right-1 top-1/2 h-6 w-1.5 -translate-y-1/2 rounded-full bg-white" />
          </div>
        </div>

        {/* 重拍生成面板 */}
        <form
          className="flex h-[150px] w-full flex-col justify-between rounded-[20px] bg-[#202020] p-[17px]"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          <div className="flex h-11 items-center gap-2">
            <span className="relative size-11 overflow-hidden rounded-xl border border-white/15">
              {data.poster ? (
                // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报
                <img
                  src={data.poster}
                  alt="参考帧"
                  className="h-full w-full object-cover"
                />
              ) : null}
              <span className="absolute bottom-0 left-0 right-0 bg-black/60 text-center text-[9px] leading-4 text-white">
                00:06
              </span>
            </span>
            <button
              type="button"
              aria-label="添加参考图"
              className="flex size-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
            >
              <Plus size={20} />
            </button>
          </div>

          <p className="flex items-center gap-1.5 text-[13px] leading-[22px] text-white/35">
            <span className="inline-flex items-center gap-1 rounded border border-[#009EFA]/60 bg-[#009EFA]/10 px-1.5 py-0.5 text-white/80">
              <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
                <rect
                  x="1"
                  y="2"
                  width="10"
                  height="8"
                  rx="1.5"
                  stroke="currentColor"
                  fill="none"
                />
                <path d="M3 1v10M9 1v10" stroke="currentColor" />
              </svg>
              00:00—00:04 重拍片段
            </span>
            描述你如何调整这一片段
          </p>

          <div className="flex h-8 w-full items-center justify-between">
            <div className="flex items-center gap-1">
              <button
                type="button"
                className="flex h-8 items-center gap-1 rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                即梦 Seedance 2.5
                <VipDiamond size={12} />
                <ChevronDown size={12} className="text-white/60" />
              </button>
              <button
                type="button"
                className="flex h-8 items-center rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
              >
                6s
              </button>
              <button
                type="button"
                aria-label="提及主体"
                className="flex size-8 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
              >
                <AtSign size={15} />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 text-[12px] font-medium text-white/60">
                <VipDiamond size={12} />
                96<span className="text-white/40">/208</span>
              </span>
              <button
                type="submit"
                aria-label="生成"
                className="flex size-9 items-center justify-center rounded-full bg-white text-black"
              >
                <ArrowUp size={16} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </NodeToolbar>
  );
}
