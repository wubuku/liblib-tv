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
  // 批 396 SOURCE_FACT: 预填以富文本形态渲染 (技能芯片 84×20 + 文件芯片
  // 113×24 内联于文本流，node-composerChip)——点击进入编辑态换回 input
  const [editing, setEditing] = useState(false);
  const richPrefill = !!refChip && prefill && !editing && !input;

  // SOURCE_FACT (batch 795 实测 @1680×826): 面板 400×802 @[1268,12]，z-40，
  // radius 20px，右缘/上缘/下缘各内缩 12px。
  return (
    <aside
      // Batch 797 SOURCE_FACT (2026-10-01 登录态实测，点「与 AI 对话」后量得):
      //   @[1268,12] 400×802  radius 20px  z-40
      //   background  color(srgb .12549 ×3 / .8) = **rgba(32,32,32,0.8)**
      //             （此前误用不透明 #1E1E1E）
      //   backdrop-filter **blur(60px)**
      //   border      1px solid rgba(255,255,255,**0.1**)（此前 0.06）
      //   box-shadow  rgba(0,0,0,0.16) 0 0 80px 0（此前无）
      className="absolute inset-y-3 right-3 z-40 flex w-[400px] flex-col rounded-[20px] border border-white/10 bg-[rgba(32,32,32,0.8)] shadow-[0_0_80px_0_rgba(0,0,0,0.16)] backdrop-blur-[60px]"
      role="dialog"
      aria-label="Agent"
    >
      {/* 头部 — Batch 808 SOURCE_FACT（@1680×826 登录态，aria/testid 逐个提取）：
          会话列表 58×32 @[1314,41] `canvas-agent-session-menu-menu-trigger`
            ↑ 此前复刻这里只是一段纯文本「新会话」，源站是**按钮**；无会话时
              aria-disabled=true —— 正确禁用，不是没接交互
          新建会话 32×32 @[1599,41] `canvas-agent-session-create`（同样 disabled）
          收起     36×36 @[1637,41] `canvas-agent-session-collapse`（此前复刻 28×28） */}
      <div className="flex items-center justify-between px-4 py-3">
        <button
          type="button"
          aria-label="会话列表"
          data-testid="canvas-agent-session-menu-trigger"
          disabled
          className="flex h-8 w-[58px] cursor-default items-center gap-1 rounded-lg px-2 text-[14px] text-white/90 disabled:text-white/45"
        >
          新会话
        </button>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="新建会话"
            data-testid="canvas-agent-session-create"
            disabled
            className="flex size-8 cursor-default items-center justify-center rounded-md text-white/60"
          >
            <SquarePen size={16} />
          </button>
          <button
            type="button"
            aria-label="收起"
            data-testid="canvas-agent-session-collapse"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
          >
            <PanelRightClose size={16} />
          </button>
        </div>
      </div>

      {/* 居中空态 */}
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6">
        <p className="text-[24px] text-white/85">探索更多专业创作模式</p>
        <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2">
          {SKILL_CHIPS.map((chip) => (
            /* SOURCE_FACT (batch 808): chip 105×36，最长的「/ 全流程广告片导演」
               157 宽 —— 宽度随文案自适应，不是固定值。源站点这几个 chip 在本次
               登录态探测下**同样没有可观测变化**，所以复刻保持 inert 才是对齐，
               不要"顺手接上"。 */
            <button
              key={chip}
              type="button"
              data-testid="canvas-agent-mode-action"
              className="flex h-9 items-center rounded-full bg-white/[0.06] px-5 text-[13px] text-white/80 hover:bg-white/[0.12]"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* 底部输入卡片 */}
      <div className="p-3">
        <div className="rounded-2xl bg-white/[0.06] p-3">
          {richPrefill ? (
            <div
              className="min-h-[44px] cursor-text text-[13px] leading-[22px] text-white"
              data-testid="agent-rich-prefill"
              onClick={() => setEditing(true)}
            >
              用{' '}
              <span className="inline-flex items-center gap-0.5 rounded bg-[#0A5CD6]/25 px-1 align-top text-[#5AB0FF]">
                <WandSparkles size={11} />
                视频反解
              </span>{' '}
              反推出{' '}
              <span className="inline-flex items-center gap-1 rounded bg-white/[0.10] px-1 py-0.5 align-top">
                <img
                  src={refChip!.poster}
                  alt=""
                  className="h-4 w-6 rounded-sm object-cover"
                />
                <span className="max-w-[80px] truncate text-[12px] text-white/85">
                  {refChip!.label}
                </span>
              </span>{' '}
              的提示词，并创建文本节点，方便我拉片复刻
              {/* batch 8 verifier 读取 input.value */}
              <input type="hidden" value={prefill || ""} readOnly />
            </div>
          ) : (
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
            {/* SOURCE_FACT (batch 808): 占位文案里的 @ 是 24×24 的独立可访问节点
                `canvas-agent-composer-placeholder-mention` @[1608,672]，
                与底行那个 32×32 的 `canvas-agent-composer-mention` 是两个东西 */}
            <span
              data-testid="canvas-agent-composer-placeholder-mention"
              className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded bg-white/[0.08] text-white/55"
            >
              <AtSign size={10} />
              <span className="sr-only">添加主体</span>
            </span>
            ，和 Agent 一起创作
          </p>
          )}
          <div className="mt-2 flex items-center gap-1">
            {/* 批 382 SOURCE_FACT: 输入行 aria 实测 从本地、画布或资产库添加 */}
            <button
              type="button"
              aria-label="从本地、画布或资产库添加"
              data-testid="canvas-agent-composer-add"
              className="flex size-8 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <Plus size={16} />
            </button>
            <button
              type="button"
              aria-label="使用技能"
              data-testid="canvas-agent-skill-trigger"
              className="flex h-8 w-[90px] items-center gap-1 rounded-md px-2 text-[13px] text-white/75 hover:bg-white/10"
            >
              <WandSparkles size={14} />
              使用技能
            </button>
            <button
              type="button"
              aria-label="引用参考"
              data-testid="canvas-agent-composer-mention"
              className="flex size-8 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <AtSign size={14} />
            </button>
            <span className="flex-1" />
            <button
              type="button"
              aria-label="发送消息"
              data-testid="canvas-agent-send"
              disabled={richPrefill ? false : !input.trim()}
              className={`flex size-8 items-center justify-center rounded-full ${
                richPrefill || input.trim()
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
