"use client";

import { useState, useRef, useEffect } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

export function CanvasTabDropdown() {
  const {
    canvases,
    activeCanvasId,
    setActiveCanvas,
    addCanvas,
    renameCanvas,
    removeCanvas,
    duplicateCanvas,
  } = useCanvasStore();
  const { isCanvasDropdownOpen, toggleCanvasDropdown } = useUIStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        toggleCanvasDropdown();
      }
    }
    if (isCanvasDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isCanvasDropdownOpen, toggleCanvasDropdown]);

  const handleRename = (id: string) => {
    if (editName.trim()) {
      renameCanvas(id, editName.trim());
    }
    setEditingId(null);
  };

  const activeCanvas = canvases.find((c) => c.id === activeCanvasId);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Tab Button */}
      <button
        onClick={toggleCanvasDropdown}
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
        <div className="absolute top-full left-0 mt-1 w-64 bg-[#1f1f1f] border border-[#363636] rounded-lg shadow-lg z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-[#363636]">
            <span className="text-sm font-medium text-[#f7f7f7]">画布</span>
            <button
              onClick={() => addCanvas()}
              className="flex items-center gap-1 text-xs text-[#09caf5] hover:text-[#5ddcff] transition-colors"
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
              新建画布
            </button>
          </div>

          {/* Canvas List */}
          <div className="max-h-60 overflow-y-auto">
            {canvases.map((canvas) => (
              <div
                key={canvas.id}
                className={cn(
                  "flex items-center justify-between px-3 py-2 hover:bg-[#353639] transition-colors group",
                  canvas.id === activeCanvasId && "bg-[#09caf5]/10"
                )}
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
                    onClick={() => setActiveCanvas(canvas.id)}
                    className={cn(
                      "flex-1 text-left text-sm",
                      canvas.id === activeCanvasId
                        ? "text-[#09caf5]"
                        : "text-[#f7f7f7]"
                    )}
                  >
                    {canvas.name}
                  </button>
                )}

                {/* More Actions */}
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(
                        menuOpenId === canvas.id ? null : canvas.id
                      );
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-[#525252] rounded transition-all"
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
                        onClick={() => {
                          duplicateCanvas(canvas.id);
                          setMenuOpenId(null);
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-[#f7f7f7] hover:bg-[#525252] transition-colors"
                      >
                        复制
                      </button>
                      {canvases.length > 1 && (
                        <button
                          onClick={() => {
                            removeCanvas(canvas.id);
                            setMenuOpenId(null);
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
