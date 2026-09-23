"use client";

import { useState } from "react";
import { ArrowUp, ChevronDown, Maximize2, Plus, Quote, Sparkle } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

/**
 * 空图片节点选中态下方弹出的图片生成面板 (Batch 530)。
 *
 * 证据 (SOURCE_FACT, 530-image-panel.png / 530-image-panel.json):
 * - 面板 680×208，与视频生成面板同族
 * - 左上「添加参考」48×48；占位「上传参考图、输入文字或主体，
 *   描述你想生成的图片」
 * - 选择器行: 选择模型: Seedream 5.0 Lite (146 宽) ·
 *   图片尺寸选项: 1:1 · 2K · 1 (98 宽，比例/分辨率/数量合并单触发钮)
 *   · 引用参考 24×24 · 引用参考 32×32
 * - 价格: 可见 ✦3 / 张，隐藏叶 Current price 3 / 张. (1px 裁切)
 * - 发送钮 生成 32×32 (空文案灰态)
 * mock: 生成流程未接入 (BLOCKED_BY_FIXTURE)。
 */
export function JimengImageGenPanel({ visible }: { visible: boolean }) {
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0;
  const [modelOpen, setModelOpen] = useState(false);
  const [sizeOpen, setSizeOpen] = useState(false);

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      <div className="relative w-[680px]">
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
          className="relative flex w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
          style={{ height: 208 }}
          onSubmit={(e) => e.preventDefault()}
        >
          {/* 批 530 SOURCE_FACT: 添加参考 48×48 (左上) */}
          <button
            type="button"
            aria-label="添加参考"
            className="mb-2 flex size-12 items-center justify-center rounded-xl bg-white/[0.06] text-white/80 hover:bg-white/10"
          >
            <Plus size={20} />
          </button>

          {!canSend ? (
            <div className="pointer-events-none absolute inset-x-4 top-[72px] flex items-start text-[13px] leading-[22px] text-white/35">
              上传参考图、输入文字或主体，描述你想生成的图片
            </div>
          ) : null}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="图片生成提示词"
            rows={2}
            className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none"
          />

          <div className="flex h-8 w-full items-center justify-between">
            <div className="flex min-w-0 items-center gap-1">
              {/* 批 530 SOURCE_FACT: 模型位 Seedream 5.0 Lite */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="选择模型: Seedream 5.0 Lite"
                  onClick={() => setModelOpen((v) => !v)}
                  className={`flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08] ${
                    modelOpen ? "bg-white/[0.08]" : ""
                  }`}
                >
                  Seedream 5.0 Lite
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {modelOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[260px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="图片模型"
                  >
                    <button
                      type="button"
                      role="option"
                      aria-selected
                      onClick={() => setModelOpen(false)}
                      className="flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] text-white bg-white/[0.10]"
                    >
                      Seedream 5.0 Lite
                    </button>
                  </div>
                ) : null}
              </div>
              {/* 批 530 SOURCE_FACT: 尺寸合并触发钮 (比例/分辨率/数量) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="图片尺寸选项: 1:1 · 2K · 1"
                  onClick={() => setSizeOpen((v) => !v)}
                  className={`flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08] ${
                    sizeOpen ? "bg-white/[0.08]" : ""
                  }`}
                >
                  1:1 · 2K · 1
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {sizeOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="图片尺寸"
                  >
                    <button
                      type="button"
                      role="option"
                      aria-selected
                      onClick={() => setSizeOpen(false)}
                      className="flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] text-white bg-white/[0.10]"
                    >
                      1:1 · 2K · 1
                    </button>
                  </div>
                ) : null}
              </div>
              {/* 批 530 SOURCE_FACT: 引用参考 24×24 */}
              <button
                type="button"
                aria-label="引用参考"
                className="flex size-6 items-center justify-center text-white/80 hover:bg-white/[0.08]"
              >
                <Quote size={13} />
              </button>
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              {/* 批 530 SOURCE_FACT: 价格 ✦3 / 张，隐藏叶 Current price 3 / 张. */}
              <span
                className="flex h-8 items-center gap-1 text-[13px] text-white/85"
                title="Current price 3 / 张."
              >
                <Sparkle size={12} className="fill-current text-white/70" />
                3
                <span className="text-[12px] text-white/[0.69]">/ 张</span>
                <span className="w-px overflow-hidden whitespace-nowrap text-[12px] text-white/[0.69]">
                  Current price 3 / 张.
                </span>
              </span>
              {/* 批 530 SOURCE_FACT: 引用参考 32×32 */}
              <button
                type="button"
                aria-label="引用参考"
                className="flex size-8 shrink-0 items-center justify-center text-white/80 hover:bg-white/[0.08]"
              >
                <Quote size={15} />
              </button>
              <button
                type="button"
                aria-label={canSend ? "生成" : "请输入提示词"}
                title={canSend ? undefined : "请输入提示词"}
                className={`flex size-8 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-[#fafafa] text-black hover:bg-white/90"
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
