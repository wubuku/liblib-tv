"use client";

import { useRef, useState } from "react";
import { ArrowUp, AtSign, ChevronDown, Plus } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";
import { useReactFlow } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import { useJimengStore } from "@/store/jimengStore";
import type { JimengVideoNodeData } from "@/types/jimeng";

/** ⭐⭐⭐ Batch 1032-②b-1：模型下拉的候选项。
 *  两个都是**源站真实出现过的模型名**（视频生成面板的「即梦 Seedance 2.0 VIP」
 *  与重拍面板自己的「即梦 Seedance 2.5」）⇒ ⇒ 不编造不存在的模型。 */
const REPAINT_MODELS = ["即梦 Seedance 2.5", "即梦 Seedance 2.0 VIP"] as const;
/** 时长候选项：与源站视频生成面板的时长档位同一组（4s / 6s / 10s）。 */
const REPAINT_DURATIONS = ["4s", "6s", "10s"] as const;

/**
 * 局部重拍编辑态面板 (Batch 5)。
 *
 * 证据 (SOURCE_FACT, /tmp extract 23-repaint-panel.png → docs batch5 截图):
 * 进入局部重拍后: 节点标题行隐藏；节点下方出现「帧条选区」(整段缩略图胶片 +
 * 白框选区窗口 + 时长标签 4.0s + 两侧拖拽把手)；再下方为生成面板变体:
 * 参考缩略图 chip (00:06) + "+"、提示词行含 chip「00:00—00:04 重拍片段」(蓝色描边)
 * + 占位「描述你如何调整这一片段」、底部 即梦 Seedance 2.5 ✦∨ / 6s / @ /
 * ✦ 96/208 积分 / 白色可用发送钮。
 * 批 214 SOURCE_FACT: 选区 aria「Selected duration: 4.0s」；提示词可输入，
 * 空提示时发送钮灰 (白/[0.16]) 带「Prompt is required」提示。
 * mock: 选区窗口为静态 4.0s；发送仅关闭编辑态 (无真实任务)。
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
  // 批 214 SOURCE_FACT: 提示词可输入，空提示时发送钮为禁用样式
  // (「Prompt is required」)；有提示词后白色可用
  const [prompt, setPrompt] = useState("");
  const canSend = prompt.trim().length > 0;
  /* ⭐⭐⭐ Batch 1032-②b-1：重拍面板此前有**四枚死按钮**：
     「添加参考图」「模型钮（即梦 Seedance 2.5，带 ChevronDown 像下拉）」「6s」「提及主体」。
     · 添加参考图 → 隐藏 file input → `addLocalUpload`（真落节点）
     · 模型钮     → 真的开下拉、真的换模型（候选取源站出现过的两个模型名）
     · 6s         → 真的开时长档位、真的换时长
     · 提及主体   → 要新增 store 侧的「主体选择」态 ⇒ **留到 ②b-2**，
                     **不拿一个假的 handler 去骗门**。
     ⚠️ 模型钮与时长钮此前**带 ChevronDown / 像下拉却点不动** ⇒ 「视觉在骗人」。 */
  const [model, setModel] = useState<string>(REPAINT_MODELS[0]);
  const [modelOpen, setModelOpen] = useState(false);
  const [duration, setDuration] = useState<string>(REPAINT_DURATIONS[1]);
  const [durationOpen, setDurationOpen] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const addLocalUpload = useJimengStore((s) => s.addLocalUpload);
  const { screenToFlowPosition } = useReactFlow();

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
          <div
            className="absolute inset-y-0 left-[2%] w-[52%] border-2 border-white/90 rounded-md"
            aria-label="Selected duration: 4.0s"
          >
            <span className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-black/60 px-1.5 py-0.5 text-[12px] text-white">
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
            if (!canSend) return;
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
              onClick={() => uploadInputRef.current?.click()}
              className="flex size-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
            >
              <Plus size={20} />
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[13px] leading-[22px]">
            <span className="inline-flex shrink-0 items-center gap-1 rounded border border-[#009EFA]/60 bg-[#009EFA]/10 px-1.5 py-0.5 text-white/80">
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
              00:00–00:04 重拍片段
            </span>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="描述你如何调整这一片段"
              className="w-full bg-transparent text-[13px] text-white outline-none placeholder:text-white/35"
            />
          </div>

          <div className="flex h-8 w-full items-center justify-between">
            <div className="flex items-center gap-1">
              {/* ⭐⭐⭐ 1032-②b-1：模型钮此前**带 ChevronDown 像下拉却点不动** ⇒ 视觉在骗人。
                  现在真的开层、真的换模型（候选取源站出现过的两个模型名）。 */}
              <div className="relative">
                <button
                  type="button"
                  aria-haspopup="listbox"
                  aria-expanded={modelOpen}
                  onClick={() => {
                    setModelOpen((v) => !v);
                    setDurationOpen(false);
                  }}
                  className="flex h-8 items-center gap-1 rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
                >
                  {model}
                  <VipDiamond size={12} />
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {modelOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[220px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="重拍模型"
                  >
                    {REPAINT_MODELS.map((m) => (
                      <button
                        key={m}
                        type="button"
                        role="option"
                        aria-selected={m === model}
                        onClick={() => {
                          setModel(m);
                          setModelOpen(false);
                        }}
                        className={`flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          m === model
                            ? "bg-white/[0.10] text-white"
                            : "text-white/80 hover:bg-white/[0.08]"
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* ⭐⭐⭐ 1032-②b-1：时长钮此前点不动 ⇒ 现在真的开档、真的换时长。 */}
              <div className="relative">
                <button
                  type="button"
                  aria-haspopup="listbox"
                  aria-expanded={durationOpen}
                  onClick={() => {
                    setDurationOpen((v) => !v);
                    setModelOpen(false);
                  }}
                  className="flex h-8 items-center rounded-lg px-2 text-[13px] text-white/90 hover:bg-white/[0.08]"
                >
                  {duration}
                </button>
                {durationOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[120px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="重拍时长"
                  >
                    {REPAINT_DURATIONS.map((d) => (
                      <button
                        key={d}
                        type="button"
                        role="option"
                        aria-selected={d === duration}
                        onClick={() => {
                          setDuration(d);
                          setDurationOpen(false);
                        }}
                        className={`flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          d === duration
                            ? "bg-white/[0.10] text-white"
                            : "text-white/80 hover:bg-white/[0.08]"
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* ⭐⭐⭐ 1032-②b-1：「提及主体」**本批不动** ——
                  它要新增 store 侧的「主体选择」态（主体节点点选 ⇒ 插 @主体），
                  留到 ②b-2。
                  ⚠️ **绝不用一个空 handler 去骗门** —— 那样它从「死按钮清单」里
                  消失了，用户点它却仍然什么都不会发生 ⇒ ⇒ 那比死按钮更坏。 */}
              <button
                type="button"
                aria-label="提及主体"
                className="flex size-8 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
              >
                <AtSign size={15} />
              </button>
            </div>
            <div className="flex items-center gap-2">
              {/* 批 374 SOURCE_FACT: 空态提示行无积分签 (旧 ✦96/208 已不在) */}
              <button
                type="submit"
                aria-label={canSend ? "生成" : "Prompt is required"}
                title={canSend ? undefined : "Prompt is required"}
                className={`flex size-9 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-white text-black hover:bg-white/90"
                    : "bg-white/[0.16] text-white/45"
                }`}
              >
                <ArrowUp size={16} />
              </button>
            </div>
          </div>
          {/* ⭐⭐⭐ 1032-②b-1：「添加参考图」的隐藏 file 入口
              （与生成面板同一套做法）。选中的文件**真的落成画布节点**。 */}
          <input
            ref={uploadInputRef}
            type="file"
            multiple
            accept="video/*,image/*,audio/*"
            className="hidden"
            data-testid="repaint-upload-input"
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              const el = document.querySelector(".jimeng-canvas");
              const center = screenToFlowPosition({
                x: el ? el.clientWidth / 2 : window.innerWidth / 2,
                y: el ? el.clientHeight / 2 : window.innerHeight / 2,
              });
              files.forEach((file, i) => {
                addLocalUpload(file.name, {
                  x: center.x - 284.5 + i * 40,
                  y: center.y - 160 + i * 40,
                });
              });
              e.target.value = "";
            }}
          />
        </form>
      </div>
    </NodeToolbar>
  );
}
