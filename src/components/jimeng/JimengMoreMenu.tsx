"use client";

import { useEffect, useRef } from "react";

/**
 * 顶栏「更多」→ 菜单 (Batch 794)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826): 点击后弹出 role=menu
 * 200×84 @[1379,56]，z-[120]，两项菜单项 192×36 @ x=1383、y=60 / y=100
 * （项间 4px 缝，菜单比项左右各内缩 4px）。菜单水平**以触发钮居中**
 * (1379+100=1479 = 更多钮 1465+28/2)，纵向落在顶栏下沿 +2px。
 * 文案逐字：项目信息 / 复制项目。
 */
const ITEMS = ["项目信息", "复制项目"] as const;

export function JimengMoreMenu({
  onClose,
  onOpenProjectInfo,
  onCopyProject,
}: {
  onClose: () => void;
  onOpenProjectInfo?: () => void;
  onCopyProject?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    // 捕获阶段：工作区有全局 Escape 处理器会在冒泡阶段 stopPropagation，
    // 冒泡监听收不到事件，浮层就关不掉。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="menu"
      aria-label="更多"
      data-testid="topbar-more-menu"
      // 以触发钮水平居中 (SOURCE_FACT)，纵向 +2px 落在顶栏下沿
      className="absolute left-1/2 top-[40px] z-[120] flex w-[200px] -translate-x-1/2 flex-col gap-1 overflow-x-hidden overflow-y-auto overscroll-contain rounded-lg p-1"
      style={{ background: "rgb(38,38,38)" }}
    >
      {ITEMS.map((label) => (
        <button
          key={label}
          type="button"
          role="menuitem"
          onClick={() => {
            if (label === "项目信息") onOpenProjectInfo?.();
            if (label === "复制项目") onCopyProject?.();
            onClose();
          }}
          className="flex h-9 w-full cursor-pointer select-none items-center rounded-md px-3 text-left text-[13px] text-white/90 outline-none hover:bg-white/10"
        >
          {label}
        </button>
      ))}
    </div>
  );
}
