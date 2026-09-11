"use client";

import { useState } from "react";
import { Copy, X } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 提示词反推面板 (Batch 8)。
 *
 * CLONE_DECISION: 源站点击「提示词反推」会提交推理任务消耗积分
 * (BLOCKED_BY_FIXTURE，未提取源站面板)。本面板为复刻侧 mock：
 * 结构沿用源站生成面板的视觉语言 (rgb(32,32,32) r20 底板 + NodeToolbar bottom)，
 * 展示 mock 反推文本 + 复制按钮。
 */
export function JimengInferPanel({
  visible,
  data,
  onClose,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const copyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(MOCK_INFERRED_PROMPT);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // 剪贴板不可用时静默 (mock)
    }
  };

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={20}>
      <div className="relative w-[680px] rounded-[20px] bg-[#202020] p-[17px]">
        <button
          type="button"
          aria-label="关闭反推面板"
          onClick={onClose}
          className="absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg text-white/50 hover:bg-white/10 hover:text-white"
        >
          <X size={15} />
        </button>

        <div className="mb-2 flex items-center gap-2">
          <span className="text-[13px] font-medium text-white">提示词反推</span>
          <VipDiamond size={12} />
          <span className="text-[12px] text-white/45">{data.title}</span>
        </div>

        <p className="mb-3 rounded-xl bg-white/[0.05] p-3 text-[13px] leading-[22px] text-white/85">
          {MOCK_INFERRED_PROMPT}
          <span className="ml-1 text-[11px] text-white/35">（mock 反推结果）</span>
        </p>

        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={copyPrompt}
            className="flex h-8 items-center gap-1.5 rounded-lg bg-white/[0.08] px-3 text-[13px] text-white/85 hover:bg-white/[0.14]"
          >
            <Copy size={14} />
            {copied ? "已复制" : "复制提示词"}
          </button>
        </div>
      </div>
    </NodeToolbar>
  );
}

const MOCK_INFERRED_PROMPT =
  "黑白影调，咖啡馆内，一位长发女子与一位男子隔桌对坐交谈，桌上两杯咖啡，背景有窗户与桌椅，浅景深，电影感构图";
