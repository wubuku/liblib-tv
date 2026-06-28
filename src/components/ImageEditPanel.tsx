"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { CameraConfigDialog } from "./CameraConfigDialog";
import { CameraMovementDialog } from "./CameraMovementDialog";

interface ImageEditPanelProps {
  onClose: () => void;
}

export function ImageEditPanel({ onClose }: ImageEditPanelProps) {
  const [activeTab, setActiveTab] = useState<"style" | "mark">("style");
  const [prompt, setPrompt] = useState("");
  const [isCameraConfigOpen, setIsCameraConfigOpen] = useState(false);
  const [isCameraMovementOpen, setIsCameraMovementOpen] = useState(false);

  return (
    <>
      <div className="absolute left-0 right-0 top-full mt-2 z-50 bg-[#1f1f1f] border border-[#363636] rounded-xl shadow-xl overflow-hidden">
        {/* Top tabs */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-[#363636]">
          <button
            onClick={() => setActiveTab("style")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors",
              activeTab === "style"
                ? "bg-[#363636] text-[#f7f7f7]"
                : "text-[#919191] hover:text-[#f7f7f7] hover:bg-[#353639]"
            )}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1L13 7L7 13L1 7L7 1Z" stroke="currentColor" strokeWidth="1.2" />
            </svg>
            风格
          </button>
          <button
            onClick={() => setActiveTab("mark")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors",
              activeTab === "mark"
                ? "bg-[#363636] text-[#f7f7f7]"
                : "text-[#919191] hover:text-[#f7f7f7] hover:bg-[#353639]"
            )}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.2" />
              <path d="M4 7H10M7 4V10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
            标记
          </button>
        </div>

        {/* Prompt section */}
        <div className="px-4 py-3">
          <p className="text-xs text-[#919191] mb-2">
            可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜
          </p>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="输入提示词..."
            className="w-full bg-[#363636] text-[#f7f7f7] text-sm p-2.5 rounded-lg border border-[#525252] focus:border-[#09caf5] outline-none resize-none h-16 placeholder:text-[#86909c]"
          />
        </div>

        {/* Bottom controls */}
        <div className="px-4 py-3 border-t border-[#363636]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Model selector */}
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M7 4V10M4 7H10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                Lib Image
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M3 4L5 6L7 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {/* Quality selector */}
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors">
                自适应 · 标准画质 · 2K
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M3 4L5 6L7 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {/* Preset button */}
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <rect x="2" y="2" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
                  <rect x="8" y="2" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
                  <rect x="2" y="8" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
                  <rect x="8" y="8" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
                </svg>
                预设
              </button>

              {/* Camera button */}
              <button
                onClick={() => setIsCameraConfigOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 4H12V11H2V4Z" stroke="currentColor" strokeWidth="1.2" />
                  <circle cx="7" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M5 4V3H9V4" stroke="currentColor" strokeWidth="1.2" />
                </svg>
                摄像机
              </button>

              {/* Camera Movement button */}
              <button
                onClick={() => setIsCameraMovementOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#363636] text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <rect x="2" y="4" width="10" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M12 7H13M1 7H2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                运镜
              </button>
            </div>

            <div className="flex items-center gap-3">
              {/* Quantity selector */}
              <div className="flex items-center gap-1.5">
                <button className="w-6 h-6 flex items-center justify-center rounded bg-[#363636] text-[#f7f7f7] hover:bg-[#525252] transition-colors">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M2 5H8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                </button>
                <span className="text-sm text-[#f7f7f7] min-w-[24px] text-center">1张</span>
                <button className="w-6 h-6 flex items-center justify-center rounded bg-[#363636] text-[#f7f7f7] hover:bg-[#525252] transition-colors">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M5 2V8M2 5H8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                </button>
              </div>

              {/* Credits display */}
              <div className="flex items-center gap-1 text-sm text-[#919191]">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M6 3V9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <span>18</span>
              </div>

              {/* Generate button */}
              <button className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#09caf5] text-white hover:bg-[#5ddcff] transition-colors">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M3 7H11M8 4L11 7L8 10" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Config Dialog */}
      <CameraConfigDialog
        isOpen={isCameraConfigOpen}
        onClose={() => setIsCameraConfigOpen(false)}
        onApply={(config) => {
          console.log("Camera config applied:", config);
          // TODO: Apply camera config to the image generation
        }}
      />

      {/* Camera Movement Dialog */}
      <CameraMovementDialog
        isOpen={isCameraMovementOpen}
        onClose={() => setIsCameraMovementOpen(false)}
        onApply={(config) => {
          console.log("Camera movement applied:", config);
          // TODO: Apply camera movement to the video generation
        }}
      />
    </>
  );
}
