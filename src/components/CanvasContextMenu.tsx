"use client";

import { useEffect } from "react";

export interface CanvasContextMenuPosition {
  x: number;
  y: number;
}

interface CanvasContextMenuProps {
  position: CanvasContextMenuPosition;
  canUndo: boolean;
  canRedo: boolean;
  hasSelection: boolean;
  onUpload: () => void;
  onSaveSelectionToAssets: () => void;
  onAddNode: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onPaste: () => void;
  onClose: () => void;
}

const itemClass =
  "flex h-8 w-full shrink-0 items-center justify-between rounded-lg px-2 text-[13px] text-[#eeeeee] transition-colors duration-100 disabled:cursor-default disabled:opacity-30 enabled:hover:bg-white/[0.07]";

const shortcutClass = "ml-6 whitespace-nowrap text-xs opacity-40";

const dividerClass = "mx-2 h-[0.5px] shrink-0 bg-[#363636]";

/**
 * Batch 172: 源站画布右键菜单（2026-09-07 CDP 采样）。
 * 结构：全屏透明点击层 + fixed 于点击点的菜单容器
 * `min-width: 196px; padding: 8px; gap: 4px; border-radius: 16px;
 * background: #262626; border: 0.5px solid #363636;`。
 * 空白画布下「保存到我的资产/撤销/重做」为 disabled（opacity 0.3）。
 */
export function CanvasContextMenu({
  position,
  canUndo,
  canRedo,
  hasSelection,
  onUpload,
  onSaveSelectionToAssets,
  onAddNode,
  onUndo,
  onRedo,
  onPaste,
  onClose,
}: CanvasContextMenuProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [onClose]);

  return (
    <>
      <div
        data-canvas-context-backdrop
        className="fixed inset-0 z-[62]"
        onMouseDown={onClose}
        onContextMenu={(event) => {
          event.preventDefault();
          onClose();
        }}
      />
      <div
        data-canvas-context-menu
        className="fixed z-[63] flex min-w-[196px] flex-col gap-1 rounded-2xl border-[0.5px] border-[#363636] bg-[#262626] p-2 shadow-[var(--canvas-shadow-menu)]"
        style={{ left: position.x, top: position.y }}
      >
        <button type="button" data-canvas-context-item="上传" className={itemClass} onClick={onUpload}>
          <span>上传</span>
        </button>
        <button
          type="button"
          data-canvas-context-item="保存到我的资产"
          className={itemClass}
          disabled={!hasSelection}
          onClick={onSaveSelectionToAssets}
        >
          <span>保存到我的资产</span>
        </button>
        <button type="button" data-canvas-context-item="添加节点" className={itemClass} onClick={onAddNode}>
          <span>添加节点</span>
        </button>
        <div className={dividerClass} />
        <button
          type="button"
          data-canvas-context-item="撤销"
          className={itemClass}
          disabled={!canUndo}
          onClick={onUndo}
        >
          <span>撤销</span>
          <span className={shortcutClass}>⌘Z</span>
        </button>
        <button
          type="button"
          data-canvas-context-item="重做"
          className={itemClass}
          disabled={!canRedo}
          onClick={onRedo}
        >
          <span>重做</span>
          <span className={shortcutClass}>⇧⌘Z</span>
        </button>
        <div className={dividerClass} />
        <button type="button" data-canvas-context-item="粘贴" className={itemClass} onClick={onPaste}>
          <span>粘贴</span>
          <span className={shortcutClass}>⌘V</span>
        </button>
      </div>
    </>
  );
}
