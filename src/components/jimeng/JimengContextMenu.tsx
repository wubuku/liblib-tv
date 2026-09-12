"use client";

import { useEffect, useRef } from "react";

/**
 * 节点右键菜单 (Batch 4)。
 *
 * 证据 (SOURCE_FACT, docs/design-references/jimeng/jimeng-source-node-context-menu-*.png):
 * bg rgb(38,38,38) r12；分组: 复制⌘C / 复制副本⌘D / 粘贴⌘V ｜ 保存到主体库 / 下载 ｜
 * 重做⌘⇧Z(禁用) / 撤销⌘Z / 删除⌫；行高约 44px，13px 文本，快捷键右对齐 white/45。
 * 功能: 复制/复制副本/粘贴/删除接 store；保存到主体库/下载/撤销/重做 mock no-op。
 */
export interface JimengContextMenuState {
  x: number;
  y: number;
  nodeId: string;
}

export function JimengContextMenu({
  state,
  canUndo = false,
  canRedo = false,
  onClose,
  onAction,
}: {
  state: JimengContextMenuState;
  canUndo?: boolean;
  canRedo?: boolean;
  onClose: () => void;
  onAction: (action: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  const rows: {
    label: string;
    shortcut?: string;
    disabled?: boolean;
    action?: string;
    danger?: boolean;
  }[] = [
    { label: "复制", shortcut: "⌘ C", action: "copy" },
    { label: "复制副本", shortcut: "⌘ D", action: "duplicate" },
    { label: "粘贴", shortcut: "⌘ V", action: "paste" },
    { label: "保存到主体库", action: "save-to-library" },
    { label: "下载", action: "download" },
    { label: "重做", shortcut: "⌘ ⇧ Z", disabled: !canRedo, action: "redo" },
    { label: "撤销", shortcut: "⌘ Z", disabled: !canUndo, action: "undo" },
    { label: "删除", shortcut: "⌫", action: "delete", danger: true },
  ];

  return (
    <div
      ref={ref}
      role="menu"
      className="fixed z-[200] w-44 rounded-xl p-2"
      style={{
        left: state.x,
        top: state.y,
        background: "rgb(38,38,38)",
      }}
    >
      {rows.map((row, i) => {
        const needsDivider =
          i === 3 || i === 5; /* 保存到主体库 前 / 重做 前 */
        return (
          <div key={row.label}>
            {needsDivider ? <div className="mx-2 my-1 h-px bg-white/[0.08]" /> : null}
            <button
              type="button"
              role="menuitem"
              disabled={row.disabled}
              onClick={() => {
                if (row.disabled) return;
                if (row.action) onAction(row.action);
                onClose();
              }}
              className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
                row.disabled
                  ? "cursor-default text-white/30"
                  : row.danger
                    ? "text-white/85 hover:bg-white/10"
                    : "text-white/85 hover:bg-white/10"
              }`}
            >
              {row.label}
              {row.shortcut ? (
                <span className="text-[12px] text-white/45">{row.shortcut}</span>
              ) : null}
            </button>
          </div>
        );
      })}
    </div>
  );
}
