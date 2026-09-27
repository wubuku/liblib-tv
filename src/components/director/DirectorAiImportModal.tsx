"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 539: 2026-09-27 已存截图转录（liblib-source-exploration-2026-09-25
// 44-director-rail-27.png）——rail「AI 识图导入」打开的居中模态：
// 标题栏 + 本地上传/历史记录 页签；虚线拖拽上传区（点击上传图片 或
// 拖拽本地图片至此上传；上传后画布将新连一个图片节点并自动替换当前图源）；
// 单选组「选择是否覆盖场景」：插入当前导演台（默认，作为站位参考层插入，
// 不覆盖当前全景、角色和机位）/ 覆盖当前导演台（…覆盖当前全景、角色和
// 机位）；底栏「关闭不会中断识图任务，生成站位参考后自动导入导演台」+
// 「生成站位参考」按钮（未上传时禁用态）。
// 真实识图/上传/生成均为云端 AI 动作——clone 仅本地可视交互，
// 「生成站位参考」永不触发（禁用态保持）。
const coverageOptions = [
  {
    id: "insert",
    label: "插入当前导演台",
    detail: "作为站位参考层插入，不覆盖当前全景、角色和机位",
    defaultChecked: true,
  },
  {
    id: "override",
    label: "覆盖当前导演台",
    detail: "作为站位参考层插入，覆盖当前全景、角色和机位",
    defaultChecked: false,
  },
] as const;

export function DirectorAiImportModal({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"upload" | "history">("upload");
  const [coverage, setCoverage] = useState<string>("insert");

  return (
    <div
      data-director-ai-import-backdrop
      className="fixed inset-0 z-[290] flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        data-director-ai-import-modal
        aria-label="AI 识图导入"
        onClick={(event) => event.stopPropagation()}
        className="w-[560px] rounded-xl border border-white/10 bg-[#202020] shadow-[0_24px_80px_rgba(0,0,0,0.6)]"
      >
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <h2 className="text-sm font-medium text-[#ededed]">AI 识图导入</h2>
          <button
            type="button"
            data-director-ai-import-close
            aria-label="关闭 AI 识图导入"
            onClick={onClose}
            className="rounded p-1 text-[#a5a5a5] hover:bg-white/[0.06] hover:text-white"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-5 py-4">
          <div className="flex items-center gap-4">
            {(
              [
                { id: "upload", label: "本地上传" },
                { id: "history", label: "历史记录" },
              ] as const
            ).map((item) => (
              <button
                key={item.id}
                type="button"
                data-director-ai-import-tab={item.id}
                aria-pressed={tab === item.id}
                onClick={() => setTab(item.id)}
                className={cn(
                  "pb-1 text-xs",
                  tab === item.id
                    ? "border-b border-white/60 text-white"
                    : "text-[#8c8c8c] hover:text-[#c0c0c0]",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === "upload" ? (
            <>
              <div
                data-director-ai-import-dropzone
                className="mt-4 flex h-[240px] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-white/[0.14] px-6 text-center"
              >
                <p className="text-sm text-[#c9c9c9]">
                  <span className="cursor-pointer text-[#ededed] underline underline-offset-2">点击上传图片</span>
                  {" 或 拖拽本地图片至此上传"}
                </p>
                <p className="text-[11px] text-[#777]">
                  上传后画布将新连一个图片节点并自动替换当前图源
                </p>
              </div>

              <p className="mt-4 text-xs text-[#b5b5b5]">选择是否覆盖场景</p>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {coverageOptions.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    data-director-coverage-option={option.id}
                    aria-pressed={coverage === option.id}
                    onClick={() => setCoverage(option.id)}
                    className={cn(
                      "rounded-lg border px-3 py-2.5 text-left",
                      coverage === option.id
                        ? "border-white/50 bg-white/[0.04]"
                        : "border-white/10 hover:border-white/25",
                    )}
                  >
                    <span className="flex items-center gap-1.5 text-xs text-[#ededed]">
                      <span
                        className={cn(
                          "flex size-3.5 items-center justify-center rounded-full border",
                          coverage === option.id ? "border-[#09caf5]" : "border-white/25",
                        )}
                      >
                        {coverage === option.id && (
                          <span className="size-1.5 rounded-full bg-[#09caf5]" />
                        )}
                      </span>
                      {option.label}
                    </span>
                    <span className="mt-1 block text-[10px] leading-4 text-[#8c8c8c]">
                      {option.detail}
                    </span>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div
              data-director-ai-import-history
              className="mt-4 flex h-[240px] items-center justify-center rounded-lg border border-dashed border-white/[0.14] text-xs text-[#777]"
            >
              暂无历史记录
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-white/[0.07] px-5 py-3.5">
          <p className="text-[11px] text-[#8c8c8c]">
            关闭不会中断识图任务，生成站位参考后自动导入导演台
          </p>
          <button
            type="button"
            data-director-ai-import-generate
            disabled
            title="生成站位参考（真实识图为云端 AI 动作，clone 不触发）"
            className="flex h-8 items-center rounded-lg bg-white/[0.08] px-3 text-xs text-[#777]"
          >
            生成站位参考
          </button>
        </div>
      </div>
    </div>
  );
}
