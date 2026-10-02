"use client";

import { useEffect, useRef, useState } from "react";

import { useJimengStore } from "@/store/jimengStore";
import { useTakeFocusAtOpen } from "./jimengMenuChrome";

/**
 * 顶栏「更多」→「项目信息」模态 (Batch 799)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826，登录态，
 * scripts/jimeng_probe797_moremenu.py):
 *   role=dialog **800×546 @[440,140]**，定位 `fixed left-1/2 top-1/2`
 *   （即水平垂直居中：1680/2±400、826/2±273）。
 *   类名含 `max-h-[80vh] max-w-[calc(100vw-3...)]`。
 *   文案逐字：项目信息 / 基础信息 / 积分消耗 / 所有者 / 创建时间 / 最新修改 /
 *   节点分布 / 全部节点 / 全部 / 图片 / 视频 / 音频 / 文本 / 时间线 / 主体 / 其他 /
 *   查看积分明细。Esc 可关闭。
 *
 * 节点分布计数按 store 实时统计 (SOURCE_FACT 实测源站该表随之变化)；
 * 时间线/主体/其他 三类复刻无对应节点类型，恒为 0 (CLONE_DECISION)。
 */
const DIST = [
  { key: "image", label: "图片" },
  { key: "video", label: "视频" },
  { key: "audio", label: "音频" },
  { key: "text", label: "文本" },
  { key: null, label: "时间线" },
  { key: null, label: "主体" },
  { key: null, label: "其他" },
] as const;

export function JimengProjectInfoModal({
  onClose,
  onViewCredits,
}: {
  onClose: () => void;
  /** Batch 803: 「查看积分明细」跳到会员页的积分详情（跨面板闭环）。 */
  onViewCredits?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<"basic" | "credits">("basic");
  const project = useJimengStore((s) => s.project);
  const nodes = useJimengStore((s) => s.nodes);

  /* 批 864：开层即接管焦点。
     探针 864 实测（修之前）：`focus_at_open.state='body'` —— 焦点被丢给
     `document.body`，**连触发器都没保住**。对话框一开，键盘用户手上一个
     落点都没有。
     ⚠️ 这里**只接管焦点、不困 Tab**，和资产库那个不一样，理由要说准：
     本层是居中 800×546 的浮层，**没有全屏遮罩**（探针实测 `covered_n=0`
     —— 按 Tab 走出去的顶栏控件全都还看得见），页面上也没有 `aria-modal`
     ⇒ 它不是「挡着页面」的模态。困 Tab 会让用户凭空出不去，是过度。
     资产库有 `bg-black/55` 全屏遮罩、实测 11 个焦点位看不见，那边才该困。 */
  useTakeFocusAtOpen(ref, true);

  const counts = DIST.map((d) => ({
    label: d.label,
    n: d.key ? nodes.filter((x) => x.type === d.key).length : 0,
  }));
  const total = counts.reduce((a, c) => a + c.n, 0);

  useEffect(() => {
    // 捕获阶段：冒泡监听会被工作区先触发的同步重渲染跳过（见 batch 794 记录）
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="项目信息"
      data-testid="project-info-modal"
      className="fixed left-1/2 top-1/2 z-[250] flex h-[546px] w-[800px] max-h-[80vh] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl border border-white/[0.06]"
      style={{ background: "rgb(24,24,26)" }}
    >
      <div className="flex items-center justify-between px-6 pt-5">
        <p className="text-[16px] font-medium text-white/90">项目信息</p>
        <button
          type="button"
          aria-label="关闭项目信息"
          onClick={onClose}
          className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10"
        >
          ✕
        </button>
      </div>

      <div className="mt-4 flex items-center gap-6 border-b border-white/[0.06] px-6">
        {(
          [
            ["basic", "基础信息"],
            ["credits", "积分消耗"],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            aria-label={label}
            onClick={() => setTab(k)}
            className={`relative pb-2 text-[13px] ${
              tab === k ? "text-white" : "text-white/45 hover:text-white/70"
            }`}
          >
            {label}
            {tab === k ? (
              <span className="absolute inset-x-0 -bottom-px h-[2px] rounded bg-white" />
            ) : null}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {tab === "basic" ? (
          <>
            <dl className="grid grid-cols-[88px_1fr] gap-y-3 text-[13px]">
              <dt className="text-white/45">所有者</dt>
              <dd className="text-white/85">西卡文案馆</dd>
              <dt className="text-white/45">创建时间</dt>
              <dd className="text-white/85">2026年9月12日 01:34</dd>
              <dt className="text-white/45">最新修改</dt>
              <dd className="text-white/85">2026年10月1日 12:37</dd>
            </dl>

            <p className="mt-6 text-[13px] text-white/60">节点分布</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-white/10 px-2 py-1 text-[12px] text-white/80">
                全部节点 {total}
              </span>
              {counts.map((c) => (
                <span
                  key={c.label}
                  className="rounded-md bg-white/[0.06] px-2 py-1 text-[12px] text-white/60"
                >
                  {c.label} {c.n}
                </span>
              ))}
            </div>

            <button
              type="button"
              onClick={() => {
                onViewCredits?.();
                onClose();
              }}
              className="mt-6 text-[13px] text-[#009EFA] hover:underline"
            >
              查看积分明细
            </button>
          </>
        ) : (
          <p className="py-16 text-center text-[13px] text-white/35">
            本项目暂无积分消耗记录
          </p>
        )}
      </div>
    </div>
  );
}
