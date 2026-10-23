"use client";

import { useEffect, useRef } from "react";

/**
 * 顶栏项目名右侧箭头「项目」→ 项目面板 (Batch 794)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826): 240×200 @[12,52] —— **左缘与顶栏
 * 左内边距齐平**（不是贴着箭头），纵向 +2px 落在顶栏下沿。面板内
 * max-h 限高、纵向 flex。文案逐字：项目 / 测试项目 / 未命名项目 /
 * 视频创作 / 新建画布项目。
 * 「未命名项目」与「视频创作」是源站真实存在的另一条项目/分类文案，
 * 此处按 mock 数据渲染 (CLONE_DECISION)。
 *
 * ⭐⭐⭐ Batch 1032-④-B（C02）：**项目列表改成真的**。
 * 此前这里写死两枚按钮（「测试项目」「未命名项目」），点「新建画布项目」只弹
 * 一句复述按钮名的话 ⇒ **什么也没建**。
 * ⇒ 现在列表来自 store 的 `projects`，`onCreate` 真建一条，`onSwitch` 真切回去。
 */
export function JimengProjectPanel({
  projectName,
  projects,
  onClose,
  onOpenProject,
  onSwitchProject,
  onCreate,
}: {
  projectName: string;
  /** ⭐⭐⭐ 真实项目列表（来自 store） */
  projects?: { id: string; name: string }[];
  onClose: () => void;
  onOpenProject?: (name: string) => void;
  onSwitchProject?: (id: string) => void;
  onCreate?: () => void;
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

  /* 列表优先用 store 的真实项目；拿不到时退回旧的两条（保持组件可独立使用）。 */
  const list =
    projects && projects.length > 0
      ? projects
      : [
          { id: "p1", name: "测试项目" },
          { id: "p2", name: "未命名项目" },
        ];

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="项目"
      data-testid="topbar-project-panel"
      // SOURCE_FACT: 左缘对齐顶栏左内边距 (x=12)，非贴箭头
      className="absolute left-0 top-[42px] z-[120] flex h-[200px] w-[240px] max-h-[200px] shrink-0 flex-col overflow-hidden rounded-xl p-2"
      style={{ background: "rgb(38,38,38)" }}
    >
      <p className="px-2 py-1.5 text-[13px] text-white/45">项目</p>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {list.map((p) => (
          <button
            key={p.id}
            type="button"
            data-testid={`topbar-project-item-${p.id}`}
            onClick={() => {
              /* ⭐⭐⭐ 真的切回去：切的是 store 里的项目，不是改个显示名。 */
              onSwitchProject?.(p.id);
              onOpenProject?.(p.name);
            }}
            className={`flex h-9 w-full items-center justify-between rounded-md px-2 text-left text-[13px] ${
              p.name === projectName ? "bg-white/[0.08] text-white" : "text-white/70 hover:bg-white/10"
            }`}
          >
            <span>{p.name}</span>
            {p.name === projectName ? (
              <span className="text-[11px] text-white/40">当前</span>
            ) : null}
          </button>
        ))}
      </div>
      <div className="my-1 h-px bg-white/[0.06]" />
      <p className="px-2 py-1 text-[12px] text-white/40">视频创作</p>
      <button
        type="button"
        data-testid="topbar-project-create"
        onClick={onCreate}
        className="flex h-9 items-center rounded-md px-2 text-left text-[13px] text-white/90 hover:bg-white/10"
      >
        新建画布项目
      </button>
    </div>
  );
}
