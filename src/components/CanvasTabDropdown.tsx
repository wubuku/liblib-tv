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
  const dropdownRef = useRef<HTMLDivElement>(null);

  const closeDropdown = useCallback(() => {
    setEditingId(null);
    setEditName("");
    setEditingProjectName(false);
    setProjectNameDraft("");
    setMenuOpenId(null);
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
  const orderedCanvases = activeCanvas
    ? [activeCanvas, ...canvases.filter((canvas) => canvas.id !== activeCanvasId)]
    : canvases;

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
                className="group flex items-center justify-between px-3 py-2 transition-colors hover:bg-[#353639]"
              >
                {editingId === canvas.id ? (
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => handleRename(canvas.id)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && handleRename(canvas.id)
                    }
                    className="flex-1 bg-[#363636] text-[#f7f7f7] text-sm px-2 py-1 rounded border border-[#525252] focus:border-[#09caf5] outline-none"
                    autoFocus
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setActiveCanvas(canvas.id);
                      closeDropdown();
                    }}
                    className="min-w-0 flex-1 truncate text-left text-sm text-[#f7f7f7]"
                  >
                    {canvas.name}
                  </button>
                )}

                {/* More Actions */}
                <div className="relative flex h-6 w-6 items-center justify-center">
                  {canvas.id === activeCanvasId && (
                    <svg
                      data-canvas-active-check
                      className="h-4 w-4 text-[#f7f7f7] transition-opacity group-hover:opacity-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                  <button
                    type="button"
                    data-canvas-row-menu={canvas.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(
                        menuOpenId === canvas.id ? null : canvas.id
                      );
                    }}
                    className="absolute inset-0 p-1 opacity-0 transition-all hover:bg-[#525252] group-hover:opacity-100"
                  >
                    <svg
                      className="w-4 h-4 text-[#919191]"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                      />
                    </svg>
                  </button>

                  {menuOpenId === canvas.id && (
                    <div className="absolute right-0 top-full mt-1 w-36 bg-[#363636] border border-[#525252] rounded-lg shadow-lg overflow-hidden z-50">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(canvas.id);
                          setEditName(canvas.name);
                          setMenuOpenId(null);
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                      >
                        重命名
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          duplicateCanvas(canvas.id);
                          closeDropdown();
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                      >
                        复制
                      </button>
                      {canvases.length > 1 && (
                        <button
                          type="button"
                          onClick={() => {
                            removeCanvas(canvas.id);
                            closeDropdown();
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-[#f53f3f] hover:bg-[#525252] transition-colors"
                        >
                          删除
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
