"use client";

import { useEffect } from "react";

export interface CanvasContextMenuTarget {
  x: number;
  y: number;
  variant: "pane" | "node";
}

interface CanvasContextMenuProps {
  target: CanvasContextMenuTarget;
  canUndo: boolean;
  canRedo: boolean;
  onUpload: () => void;
  onSaveSelectionToAssets: () => void;
  onAddNode: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onPaste: () => void;
  onCopyNode: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onCopyToClipboard: () => void;
  onClose: () => void;
}

const itemClass =
  "flex h-8 w-full shrink-0 items-center justify-between rounded-lg px-2 text-[13px] text-[#eeeeee] transition-colors duration-100 disabled:cursor-default disabled:opacity-30 enabled:hover:bg-white/[0.07]";

const shortcutClass = "ml-6 whitespace-nowrap text-xs opacity-40";

const dividerClass = "mx-2 h-[0.5px] shrink-0 bg-[#363636]";

/* 源站节点菜单「复制节点/创建副本」标签后的 14px 问号提示图标（2026-09-07 采样）。 */
const infoGlyph = (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="ml-1 opacity-35">
    <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" />
    <text x="7" y="10.5" textAnchor="middle" fill="currentColor" fontSize="9" fontWeight="500" fontFamily="sans-serif">
      ?
    </text>
  </svg>
);

/**
 * Batch 172/173: 源站画布右键菜单（2026-09-07 CDP 采样）。
 * 结构：全屏透明点击层 + fixed 于点击点的菜单容器
 * `min-width: 196px; padding: 8px; gap: 4px; border-radius: 16px;
 * background: #262626; border: 0.5px solid #363636`。
 * pane 变体六项：上传/保存到我的资产/添加节点/撤销⌘Z/重做⇧⌘Z/粘贴⌘V；
 * node 变体七项：保存到我的资产/创建主体/复制节点⌘C/创建副本⌘D/粘贴⌘V/
 * 删除⌘⌫/复制到剪贴板（两组 0.5px 分隔线）。
 */
export function CanvasContextMenu({
  target,
  canUndo,
  canRedo,
  onUpload,
  onSaveSelectionToAssets,
  onAddNode,
  onUndo,
  onRedo,
  onPaste,
  onCopyNode,
  onDuplicate,
  onDelete,
  onCopyToClipboard,
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
        data-canvas-context-variant={target.variant}
        className="fixed z-[63] flex min-w-[196px] flex-col gap-1 rounded-2xl border-[0.5px] border-[#363636] bg-[#262626] p-2 shadow-[var(--canvas-shadow-menu)]"
        style={{ left: target.x, top: target.y }}
      >
        {target.variant === "pane" ? (
          <>
            <button type="button" data-canvas-context-item="上传" className={itemClass} onClick={onUpload}>
              <span>上传</span>
            </button>
            <button
              type="button"
              data-canvas-context-item="保存到我的资产"
              className={itemClass}
              disabled
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
          </>
        ) : (
          <>
            <button
              type="button"
              data-canvas-context-item="保存到我的资产"
              className={itemClass}
              disabled
              onClick={onSaveSelectionToAssets}
            >
              <span>保存到我的资产</span>
            </button>
            <button
              type="button"
              data-canvas-context-item="创建主体"
              className={itemClass}
              disabled
              onClick={onSaveSelectionToAssets}
            >
              <span>创建主体</span>
            </button>
            <div className={dividerClass} />
            <button type="button" data-canvas-context-item="复制节点" className={itemClass} onClick={onCopyNode}>
              <span className="flex items-center">
                复制节点
                {infoGlyph}
              </span>
              <span className={shortcutClass}>⌘C</span>
            </button>
            <button type="button" data-canvas-context-item="创建副本" className={itemClass} onClick={onDuplicate}>
              <span className="flex items-center">
                创建副本
                {infoGlyph}
              </span>
              <span className={shortcutClass}>⌘D</span>
            </button>
            <button type="button" data-canvas-context-item="粘贴" className={itemClass} onClick={onPaste}>
              <span>粘贴</span>
              <span className={shortcutClass}>⌘V</span>
            </button>
            <button type="button" data-canvas-context-item="删除" className={itemClass} onClick={onDelete}>
              <span>删除</span>
              <span className={shortcutClass}>⌘⌫</span>
            </button>
            <div className={dividerClass} />
            <button
              type="button"
              data-canvas-context-item="复制到剪贴板"
              className={itemClass}
              onClick={onCopyToClipboard}
            >
              <span>复制到剪贴板</span>
            </button>
          </>
        )}
      </div>
    </>
  );
}
