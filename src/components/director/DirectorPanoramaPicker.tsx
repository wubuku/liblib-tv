"use client";

// ★★★ Batch 861（源站实测）：导演台左侧「全景图」面板里
//   **「历史记录」与「AI生成」两行在源站都不是死按钮** ——
//   它们都会打开一个**资产库选择器**对话框。
//
// ★ 源站实测（`probes/source861_panorama_diff.py` ⟹ `raw/source-861-panorama-diff.json`）：
//   点「历史记录」⟹ ⟹ 新增按钮：生成历史／我保存的／我上传的／本项目／全部项目／
//                            图片0／取消／确认选择（按钮数 86 → 95）
//   点「AI生成」  ⟹ ⟹ 在上面那批之外**再多**「上传图片」「生成」「关闭」
//                            （按钮数 86 → 98）
//   ⇒ ⟹ 两行打开的是**同一个**资产库选择器，AI 那一行多一个「生成」入口。
//   ⇒ ⟹ 源站那个对话框是**全屏**的（rect 1920×1080）。
//
// ★ ★★ **clone 与源站的差异（如实登记，不假装一致）**：
//   · 源站的列表内容是**资产库**（五个筛选标签：生成历史／我保存的／我上传的／
//     本项目／全部项目；实测该账号下「图片 0 ／ 暂无历史记录」）；
//   · clone 的全景图来源是**画布图片节点的直接上游** ⟹ ⟹ 本对话框列的是
//     **当前可作全景图的图片输入**（含本地上传的那张）⟹ ⟹
//     **界面形态不同、内容语义等价**（都是「挑一张已有图片当全景图」）。
//   · 「生成」在 clone **不接真实生成**（真实生图会产生费用）⟹ ⟹
//     点它只给一句明确说明 ⟹ ⟹ 不假装能生成。
//
// ★ 源站逐字（`aU` 的 panorama 段）：
//   历史记录：`onClick:T` ⟹ `oB` ⟹ `eu?.((e,t)=>{…r6({panoramaUrl:e})})`
//   AI生成  ：`onClick:P` ＋ `disabled:E` ⟹ `oX` ⟹ `td(!0)`（打开对话框）
//   本地上传：`onClick:()=>{I?.(), et.current?.click()}`
import { useState } from "react";
import { Image as ImageIcon, Sparkles, Upload, X } from "lucide-react";

import type { DirectorCanvasMediaInputV1 } from "@/lib/directorCanvasMediaIngress";

export type DirectorPanoramaPickerMode = "history" | "ai";

export function DirectorPanoramaPicker({
  mode,
  inputs,
  onClose,
  onConfirm,
  onUploadImage,
}: {
  mode: DirectorPanoramaPickerMode;
  inputs: DirectorCanvasMediaInputV1[];
  onClose: () => void;
  onConfirm: (sourceNodeId: string) => void;
  onUploadImage: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generateNotice, setGenerateNotice] = useState<string | null>(null);

  return (
    <div
      data-director-panorama-picker
      data-director-panorama-picker-mode={mode}
      role="dialog"
      aria-modal="true"
      aria-label="选择全景图"
      className="fixed inset-0 z-[2200] flex flex-col bg-black/72 backdrop-blur-[2px]"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 p-6">
        <div className="flex w-[880px] max-w-full flex-col overflow-hidden rounded-xl border border-white/10 bg-[#1a1a1a]">
          {/* ★ 标题条 */}
          <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/8 px-4">
            <span className="text-[13px] text-white/90">全景图</span>
            <button
              type="button"
              data-director-panorama-picker-close
              aria-label="关闭"
              title="关闭"
              onClick={onClose}
              className="flex size-7 items-center justify-center rounded text-white/70 hover:bg-white/8 hover:text-white"
            >
              <X size={15} />
            </button>
          </div>

          {/* ★ AI 模式多一行入口（源站实测：AI 那行多「上传图片」「生成」）*/}
          {mode === "ai" ? (
            <div className="flex shrink-0 items-center gap-2 border-b border-white/8 px-4 py-3">
              <button
                type="button"
                data-director-panorama-generate
                onClick={() =>
                  setGenerateNotice(
                    "本原型不接入真实全景图生成（真实生图会产生费用），此处只作入口占位。",
                  )
                }
                className="flex h-8 items-center gap-1.5 rounded-lg border border-white/15 px-3 text-[12px] text-white/90 hover:bg-white/8"
              >
                <Sparkles size={14} aria-hidden="true" />
                生成
              </button>
              <button
                type="button"
                data-director-panorama-picker-upload
                onClick={onUploadImage}
                className="flex h-8 items-center gap-1.5 rounded-lg border border-white/15 px-3 text-[12px] text-white/90 hover:bg-white/8"
              >
                <Upload size={14} aria-hidden="true" />
                上传图片
              </button>
              {generateNotice ? (
                <span
                  data-director-panorama-generate-notice
                  className="min-w-0 flex-1 truncate text-[11px] text-[#f0c776]"
                >
                  {generateNotice}
                </span>
              ) : null}
            </div>
          ) : null}

          {/* ★ 列表 */}
          <div className="min-h-[220px] flex-1 overflow-y-auto p-4">
            {inputs.length === 0 ? (
              <p
                data-director-panorama-picker-empty
                className="flex h-[180px] items-center justify-center text-[12px] text-white/45"
              >
                暂无可用图片（把画布上的图片节点连到导演台，或用「本地上传」选一张）
              </p>
            ) : (
              <ul className="grid grid-cols-4 gap-3">
                {inputs.map((input) => (
                  <li key={input.sourceNodeId}>
                    <button
                      type="button"
                      data-director-panorama-picker-option={input.sourceNodeId}
                      data-director-panorama-picker-kind={input.sourceKind}
                      aria-pressed={selectedId === input.sourceNodeId}
                      onClick={() => setSelectedId(input.sourceNodeId)}
                      className={
                        selectedId === input.sourceNodeId
                          ? "flex w-full flex-col gap-1.5 rounded-lg border border-white/85 p-1.5 text-left"
                          : "flex w-full flex-col gap-1.5 rounded-lg border border-white/10 p-1.5 text-left hover:bg-white/6"
                      }
                    >
                      <span className="flex h-[88px] w-full items-center justify-center overflow-hidden rounded bg-black/40">
                        {/* ★ blob URL ／ 画布图片 URL 都是**运行时地址**，
                            next/image 的优化器处理不了 ⟹ ⟹ 用原生 img。 */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={input.imageUrl}
                          alt={input.filename}
                          className="max-h-full max-w-full object-contain"
                        />
                      </span>
                      <span className="flex min-w-0 items-center gap-1 text-[11px] text-white/80">
                        <ImageIcon size={11} aria-hidden="true" />
                        <span className="min-w-0 truncate">{input.filename}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* ★ 底部动作（源站逐字：取消／确认选择）*/}
          <div className="flex h-14 shrink-0 items-center justify-end gap-2 border-t border-white/8 px-4">
            <button
              type="button"
              data-director-panorama-picker-cancel
              onClick={onClose}
              className="h-8 rounded-lg px-3 text-[12px] text-white/75 hover:bg-white/8"
            >
              取消
            </button>
            <button
              type="button"
              data-director-panorama-picker-confirm
              disabled={selectedId === null}
              onClick={() => {
                if (selectedId !== null) onConfirm(selectedId);
              }}
              className="h-8 rounded-lg bg-white/90 px-3 text-[12px] text-black disabled:cursor-not-allowed disabled:opacity-35"
            >
              确认选择
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
