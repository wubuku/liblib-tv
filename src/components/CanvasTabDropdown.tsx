"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

export function CanvasTabDropdown() {
  const {
    projectName,
    canvases,
    activeCanvasId,
    setProjectName,
    setActiveCanvas,
    addCanvas,
    renameCanvas,
    removeCanvas,
    duplicateCanvas,
  } = useCanvasStore();
  const {
    isCanvasDropdownOpen,
    toggleCanvasDropdown,
    closeCanvasDropdown,
  } = useUIStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editingProjectName, setEditingProjectName] = useState(false);
  const [projectNameDraft, setProjectNameDraft] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  // Batch 114: 删除画布确认框（源站文案：此操作不可恢复）。
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const closeDropdown = useCallback(() => {
    setEditingId(null);
    setEditName("");
    setEditingProjectName(false);
    setProjectNameDraft("");
    setMenuOpenId(null);
    setPendingDelete(null);
    closeCanvasDropdown();
  }, [closeCanvasDropdown]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        closeDropdown();
      }
    }
    if (isCanvasDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [closeDropdown, isCanvasDropdownOpen]);

  useEffect(() => {
    if (!isCanvasDropdownOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeDropdown();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [closeDropdown, isCanvasDropdownOpen]);

  const handleRename = (id: string) => {
    if (editName.trim()) {
      renameCanvas(id, editName.trim());
    }
    closeDropdown();
  };

  const handleProjectNameCommit = () => {
    setProjectName(projectNameDraft);
    setEditingProjectName(false);
    setProjectNameDraft("");
  };

  const handleToggle = () => {
    if (isCanvasDropdownOpen) {
      closeDropdown();
      return;
    }
    setEditingId(null);
    setEditName("");
    setEditingProjectName(false);
    setProjectNameDraft("");
    setMenuOpenId(null);
    toggleCanvasDropdown();
  };

  const activeCanvas = canvases.find((c) => c.id === activeCanvasId);
  // Batch 114: 源站下拉按创建时间倒序（最新在前）。
  const orderedCanvases = [...canvases].reverse();

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Tab Button */}
      <button
        data-canvas-trigger
        onClick={handleToggle}
        className={cn(
          "flex items-center gap-2 px-2 h-8 rounded-lg text-[#f7f7f7] hover:bg-[#353639] transition-colors",
          isCanvasDropdownOpen && "bg-[#353639]"
        )}
      >
        <span className="text-sm">{activeCanvas?.name || "画布"}</span>
        <svg
          className={cn(
            "w-3 h-3 transition-transform",
            isCanvasDropdownOpen && "rotate-180"
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown */}
      {isCanvasDropdownOpen && (
        <div data-liblib-overlay="canvas-dropdown" className="absolute top-full left-0 mt-1 w-56 overflow-hidden rounded-xl border border-[#363636] bg-[#1f1f1f] shadow-lg z-50">
          <div data-canvas-project className="border-b border-[#363636] px-3 pb-3 pt-3">
            <span className="block text-[11px] text-[#8c8c8c]">当前项目</span>
            {editingProjectName ? (
              <input
                data-canvas-project-input
                type="text"
                autoFocus
                value={projectNameDraft}
                onChange={(event) => setProjectNameDraft(event.target.value)}
                onBlur={handleProjectNameCommit}
                onKeyDown={(event) => {
                  if (event.key === "Enter") handleProjectNameCommit();
                  if (event.key === "Escape") {
                    setEditingProjectName(false);
                    setProjectNameDraft("");
                  }
                }}
                className="mt-1 w-full bg-transparent text-sm text-[#f7f7f7] outline-none"
              />
            ) : (
              <button
                type="button"
                onClick={() => {
                  setProjectNameDraft(projectName);
                  setEditingProjectName(true);
                }}
                className="mt-1 max-w-full truncate text-left text-sm text-[#f7f7f7] hover:text-white"
              >
                {projectName}
              </button>
            )}
          </div>

          {/* Canvas list header */}
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-sm font-medium text-[#f7f7f7]">画布</span>
            <button
              type="button"
              data-canvas-new
              aria-label="新建画布"
              title="新建画布"
              onClick={() => {
                addCanvas();
                closeDropdown();
              }}
              className="flex h-7 w-7 items-center justify-center rounded-md text-[#f7f7f7] transition-colors hover:bg-white/[0.07]"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>
          </div>

          {/* Canvas List */}
          <div className="max-h-60 overflow-y-auto border-t border-[#363636]">
            {orderedCanvases.map((canvas) => (
              <div
                key={canvas.id}
                data-canvas-row={canvas.id}
                data-canvas-active={canvas.id === activeCanvasId ? "true" : "false"}
                className="group/canvas-row relative flex items-center justify-between px-3 py-2 transition-colors hover:bg-[#353639]"
              >
                {editingId === canvas.id ? (
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => handleRename(canvas.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleRename(canvas.id);
                      if (e.key === "Escape") {
                        setEditingId(null);
                        setEditName("");
                      }
                    }}
                    className="min-w-0 flex-1 rounded border border-[#525252] bg-[#363636] px-2 py-1 text-sm text-[#f7f7f7] outline-none focus:border-[#09caf5]"
                    autoFocus
                  />
                ) : (
                  <button
                    type="button"
                    aria-label={`切换到画布 ${canvas.name}`}
                    title={canvas.name}
                    onClick={() => {
                      setActiveCanvas(canvas.id);
                      closeDropdown();
                    }}
                    className="flex min-w-0 flex-1 items-center gap-2 text-left text-sm text-[#f7f7f7]"
                  >
                    <span className="min-w-0 flex-1 truncate">{canvas.name}</span>
                    {canvas.id === activeCanvasId && (
                      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                )}
                <button
                  type="button"
                  aria-label="更多操作"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpenId(menuOpenId === canvas.id ? null : canvas.id);
                  }}
                  className="ml-1 flex size-6 shrink-0 items-center justify-center rounded-lg text-[#919191] opacity-0 transition-opacity hover:bg-[#525252] hover:text-white group-hover/canvas-row:opacity-100 focus-visible:opacity-100"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01" />
                  </svg>
                </button>

                {menuOpenId === canvas.id && (
                  <div className="absolute right-2 top-full z-50 w-36 overflow-hidden rounded-lg border border-[#525252] bg-[#363636] shadow-lg">
                    <button
                      type="button"
                      onClick={() => {
                        closeDropdown();
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                    >
                      在新窗口打开
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(canvas.id);
                        setEditName(canvas.name);
                        setMenuOpenId(null);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                    >
                      重命名画布
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        duplicateCanvas(canvas.id);
                        closeDropdown();
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                    >
                      复制画布
                    </button>
                    {canvases.length > 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          setMenuOpenId(null);
                          setPendingDelete({ id: canvas.id, name: canvas.name });
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-[#f55353] hover:bg-[#525252] transition-colors"
                      >
                        删除画布
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {pendingDelete && (
        <div
          data-canvas-delete-confirm
          className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 backdrop-blur-[3px]"
          onMouseDown={() => setPendingDelete(null)}
        >
          <div
            role="dialog"
            aria-label="删除画布"
            className="w-[360px] rounded-xl border border-white/[0.08] bg-[#262626] p-4 shadow-[0_28px_80px_rgba(0,0,0,0.6)]"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <h3 className="text-sm font-medium text-[#f0f0f0]">删除画布</h3>
            <p className="mt-2 text-xs leading-5 text-[#a8a8a8]">
              确定要删除画布「{pendingDelete.name}」吗？此操作不可恢复。
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPendingDelete(null)}
                className="rounded-lg border border-white/[0.1] px-3 py-1.5 text-xs text-[#d8d8d8] hover:bg-white/[0.06]"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => {
                  removeCanvas(pendingDelete.id);
                  setPendingDelete(null);
                  closeDropdown();
                }}
                className="rounded-lg bg-[#f55353] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#e04545]"
              >
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}