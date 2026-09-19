"use client";

import { useState } from "react";
import { useJimengStore } from "@/store/jimengStore";
import {
  ArrowUp,
  AtSign,
  PanelRightClose,
  Plus,
  SquarePen,
  WandSparkles,
} from "lucide-react";

/**
 * 「与 AI 对话」右侧抽屉 (Batch 12)。
 *
 * 证据 (SOURCE_FACT): 点击右下角按钮展开全高右侧抽屉 (宽 ≈410px, 圆角,
 * assistant-sidecar 深色表面): 头部「新会话」+ 历史/展开图标；居中空态
 * 「探索更多专业创作模式」+ 技能 chips (/ 视频反解 / 创作分镜 / 全流程广告片导演 /
 * 剧本开发 / 剧情短片)；底部输入卡片: 占位「输入想法、剧本或上传参考，支持" / "
 * 使用技能，@ 添加主体，和 Agent 一起创作」+ @ chip + 底行 +/使用技能/@/禁用发送钮。
 * mock: 输入不可用，chips 点击无操作。
 */
const SKILL_CHIPS = [
  "/ 视频反解",
  "/ 创作分镜",
  "/ 全流程广告片导演",
  "/ 剧本开发",
  "/ 剧情短片",
];

export function JimengAiDrawer({ onClose }: { onClose: () => void }) {
  // 批 216: 预填提示词 (提示词反推 → 视频反解)；由工作区以 prefill 为
  // key 重挂载本组件带入初始值。批 219: 草稿跨关闭保留——优先取已存草稿
  const prefill = useJimengStore((s) => s.aiDrawerPrefill);
  const refChip = useJimengStore((s) => s.aiDrawerRefChip);
  const draft = useJimengStore((s) => s.aiDrawerDraft);
  const setAiDrawerDraft = useJimengStore((s) => s.setAiDrawerDraft);
  const [input, setInput] = useState(draft || prefill || "");

  return (
    <aside
      className="absolute inset-y-3 right-3 z-40 flex w-[398px] flex-col rounded-2xl border border-white/[0.06] bg-[#1E1E1E]"
      role="dialog"
      aria-label="AI 对话"
    >
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-[14px] text-white/90">新会话</span>
        <div className="flex items-center gap-1">
          {/* 批 381 SOURCE_FACT: 头部实为 [新建会话][收起] 两钮 (aria 实测) */}
          <button
            type="button"
            aria-label="新建会话"
            className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
          >
            <SquarePen size={15} />
          </button>
          <button
            type="button"
            aria-label="收起"
            onClick={onClose}
            className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
          >
            <PanelRightClose size={15} />
          </button>
        </div>
      </div>

      {/* 居中空态 */}
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6">
        <p className="text-[24px] text-white/85">探索更多专业创作模式</p>
        <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2">
          {SKILL_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              className="flex h-9 items-center rounded-full bg-white/[0.06] px-4 text-[13px] text-white/80 hover:bg-white/[0.12]"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* 底部输入卡片 */}
      <div className="p-3">
        <div className="rounded-2xl bg-white/[0.06] p-3">
          <p className="min-h-[44px] text-[13px] leading-[22px] text-white/35">
            <input
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setAiDrawerDraft(e.target.value);
              }}
              placeholder="输入想法、剧本或上传参考，支持 “ / ” 使用技能，"
              className="w-full bg-transparent text-[13px] text-white outline-none placeholder:text-white/35"
            />
            {refChip ? (
              <span className="mr-1 inline-flex items-center gap-1 rounded bg-white/[0.10] px-1 py-0.5 align-middle">
                <img
                  src={refChip.poster}
                  alt=""
                  className="h-4 w-6 rounded-sm object-cover"
                />
                <span className="max-w-[80px] truncate text-[12px] text-white/85">
                  {refChip.label}
                </span>
              </span>
            ) : null}
            <span className="mt-1 inline-flex items-center gap-1 rounded bg-white/[0.08] px-1 text-white/55">
              <AtSign size={10} />
              添加主体
            </span>
            ，和 Agent 一起创作
          </p>
          <div className="mt-2 flex items-center gap-1">
            {/* 批 382 SOURCE_FACT: 输入行 aria 实测 从本地、画布或资产库添加 */}
            <button
              type="button"
              aria-label="从本地、画布或资产库添加"
              className="flex size-7 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <Plus size={16} />
            </button>
            <button
              type="button"
              className="flex h-7 items-center gap-1 rounded-md px-2 text-[13px] text-white/75 hover:bg-white/10"
            >
              <WandSparkles size={14} />
              使用技能
            </button>
            <button
              type="button"
              aria-label="引用参考"
              className="flex size-7 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <AtSign size={14} />
            </button>
            <span className="flex-1" />
            <button
              type="button"
              aria-label="发送消息"
              disabled={!input.trim()}
              className={`flex size-8 items-center justify-center rounded-full ${
                input.trim()
                  ? "bg-white text-black"
                  : "bg-white/[0.14] text-white/30"
              }`}
            >
              <ArrowUp size={15} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
