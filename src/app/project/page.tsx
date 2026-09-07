"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, FolderPlus, Trash2 } from "lucide-react";
import { useCanvasStore } from "@/store/canvasStore";
import { cn } from "@/lib/utils";

// Batch 119: 2026-09-06 采样（liblib-projects-page-2026-09-06）——
// 「全部项目」页结构对齐；clone 单项目多画布，列表以画布为卡片映射（CLONE_DECISION）。
export default function ProjectListPage() {
  const router = useRouter();
  const {
    canvases,
    removedCanvases,
    activeCanvasId,
    setActiveCanvas,
    addCanvas,
    restoreCanvas,
  } = useCanvasStore();
  const [status, setStatus] = useState("");
  const [recycleOpen, setRecycleOpen] = useState(false);
  // Batch 136: 源站回收站「已选择 0 项」计数 —— clone 实现为逐项勾选 + 恢复。
  const [selectedRemoved, setSelectedRemoved] = useState<string[]>([]);
  const today = new Date().toISOString().slice(0, 10);

  // Batch 150: 源站 2026-09-07 实拍——/project 画布卡点击在新标签页打开画布。
  const openCanvas = (canvasId: string) => {
    setActiveCanvas(canvasId);
    window.open("/", "_blank");
  };

  return (
    <main
      data-project-list-page
      className="min-h-screen bg-[#141414] px-10 py-6 text-[#ededed]"
    >
      <div className="mb-6 flex items-center gap-4">
        <button
          type="button"
          data-project-back
          onClick={() => router.push("/")}
          className="flex h-8 items-center gap-1 rounded-lg px-2 text-sm text-[#d8d8d8] hover:bg-white/[0.06] hover:text-white"
        >
          <ArrowLeft size={15} />
          返回
        </button>
        <h1 className="text-lg font-medium">全部项目</h1>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            data-project-recycle
            aria-expanded={recycleOpen}
            onClick={() => setRecycleOpen((value) => !value)}
            className={cn(
              // Batch 167: 源站回收站为实心次级按钮（bg-btn-secondary，h-8）。
              "flex h-8 items-center gap-1.5 rounded-lg px-3 text-[13px] text-[#ededed] hover:bg-white/[0.12]",
              recycleOpen ? "bg-white/[0.16]" : "bg-white/[0.08]",
            )}
          >
            <Trash2 size={13} />
            回收站
          </button>
          <button
            type="button"
            data-project-new-folder
            onClick={() => setStatus("本地原型：新建文件夹未接入")}
            className="flex h-8 items-center gap-1.5 rounded-lg bg-white/[0.08] px-3 text-[13px] text-[#ededed] hover:bg-white/[0.12]"
          >
            <FolderPlus size={13} />
            新建文件夹
          </button>
        </div>
      </div>

      {recycleOpen && (
        <div data-recycle-panel className="mb-6 rounded-xl border border-white/[0.08] bg-[#1f1f1f] p-4">
          <p className="text-[11px] text-[#8c8c8c]">仅显示最近 30 天内删除的内容</p>
          {removedCanvases.length === 0 ? (
            <p data-recycle-empty className="py-4 text-xs text-[#666]">
              回收站为空
            </p>
          ) : (
            <>
              <p data-recycle-selection className="mt-1 text-[11px] text-[#9a9a9a]">
                已选择 {selectedRemoved.length} 项
              </p>
              <ul className="mt-2 space-y-2">
                {removedCanvases.map((canvas) => (
                  <li
                    key={canvas.id}
                    data-recycle-item={canvas.id}
                    className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <input
                        type="checkbox"
                        data-recycle-check={canvas.id}
                        checked={selectedRemoved.includes(canvas.id)}
                        onChange={(event) =>
                          setSelectedRemoved((current) =>
                            event.target.checked
                              ? [...current, canvas.id]
                              : current.filter((id) => id !== canvas.id),
                          )
                        }
                        className="size-3.5 shrink-0 accent-[#09caf5]"
                      />
                      <span className="min-w-0 truncate text-xs text-[#d8d8d8]">
                        {canvas.name}
                        <span className="ml-2 text-[10px] text-[#777]">
                          {canvas.removedAt} · 剩余 30 天
                        </span>
                      </span>
                    </span>
                    <button
                      type="button"
                      data-recycle-restore={canvas.id}
                      onClick={() => restoreCanvas(canvas.id)}
                      className="shrink-0 rounded border border-white/[0.14] px-2 py-1 text-[11px] text-[#d8d8d8] hover:border-white/[0.3] hover:text-white"
                    >
                      恢复
                    </button>
                  </li>
                ))}
              </ul>
              {selectedRemoved.length > 0 && (
                <button
                  type="button"
                  data-recycle-restore-selected
                  onClick={() => {
                    selectedRemoved.forEach((id) => restoreCanvas(id));
                    setSelectedRemoved([]);
                  }}
                  className="mt-2 rounded-lg border border-[#09caf5]/50 px-3 py-1.5 text-[11px] text-[#09caf5] hover:bg-[#09caf5]/10"
                >
                  恢复所选 {selectedRemoved.length} 项
                </button>
              )}
            </>
          )}
        </div>
      )}

      <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4">
        <button
          type="button"
          data-project-create-card
          onClick={() => {
            addCanvas();
            router.push("/");
          }}
          className="group flex flex-col overflow-hidden rounded-xl text-left transition-colors hover:opacity-90"
        >
          {/* Batch 167: 源站创建卡为 aspect-video 封面区 + 下方标题行（非虚线占位卡）。 */}
          <span className="flex aspect-video w-full shrink-0 items-center justify-center rounded-xl bg-white/[0.04] transition-colors group-hover:bg-white/[0.07]">
            <span className="text-[14px] font-medium text-[#ededed]">开始创作</span>
          </span>
          <span className="truncate px-0.5 py-2.5 text-sm font-medium text-[#9a9a9a]">创建新的视频项目</span>
        </button>
        {canvases.map((canvas) => (
          <button
            key={canvas.id}
            type="button"
            data-project-card={canvas.id}
            onClick={() => openCanvas(canvas.id)}
            className={cn(
              "group flex flex-col overflow-hidden rounded-xl border border-white/[0.08] bg-[#1f1f1f] text-left transition-all duration-200 hover:border-white/[0.24] hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)] hover:-translate-y-0.5",
              canvas.id === activeCanvasId && "border-[#09caf5]/50",
            )}
          >
            {/* Batch 148: 源站项目卡有封面图占位区（渐变色/缩略图）。 */}
            {/* Batch 167: 源站封面为 aspect-video（267 宽 → 149 高，卡总高 208）。 */}
            <div className="relative flex aspect-video w-full shrink-0 items-center justify-center bg-gradient-to-br from-[#2a3a4a] via-[#1e2e3e] to-[#1a2a3a] transition-transform duration-300 group-hover:scale-105">
              <svg viewBox="0 0 24 24" className="size-6 text-white/20 transition-transform duration-300 group-hover:scale-125" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="absolute bottom-1 right-2 rounded bg-black/50 px-1 py-0.5 text-[9px] text-white/60">
                {canvas.nodes.length} 个节点
              </span>
            </div>
            <div className="flex flex-1 flex-col justify-between p-3">
              <span className="truncate text-[14px] font-medium text-[#ededed]">{canvas.name}</span>
              {/* Batch 152: 源站卡副行仅日期（2026-09-07 实拍：未命名 + 2026-09-06），无工作区前缀。 */}
              <span className="text-[11px] text-[#777]">
                {today}
              </span>
            </div>
          </button>
        ))}
      </div>

      {status && (
        <p data-project-list-status className="mt-4 text-xs text-[#75d7e8]">
          {status}
        </p>
      )}
    </main>
  );
}
