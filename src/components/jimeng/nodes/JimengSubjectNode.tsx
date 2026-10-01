"use client";

import { useState } from "react";
import {
  FolderOpen,
  Images,
  Pencil,
  SquareUser,
  Upload,
  UserPlus,
} from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengSubjectNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

/**
 * 主体节点 (Batch 805 SOURCE_FACT @1680×826 实测 352×352)。
 *
 * 左栏「主体」按钮点下去之后出现的东西（源站落点 `rf__node-*` role=group，
 * 在 viewport 内，顶栏节点计数 +1）—— 此前复刻当成"打开浮层"，所以是死按钮。
 *
 * 结构：
 *   标题行  「主体 N」+ 右上编辑笔
 *   副行    「添加描述...」占位（可编辑）
 *   内卡    四个入口 导入主体 / 从画布选择 / 从资产库选择 / 本地添加
 *   空态    源站放在 sr-only（"Empty subject: main missing, 0 auxiliaries,
 *           voice missing."）—— 不做成可见状态行（与 batch 794 资源计数同理）
 *
 * 真交互：四个入口各自有不同后果，描述行可写回 store。
 */
const ENTRIES = [
  { key: "import", label: "导入主体", icon: UserPlus },
  { key: "canvas", label: "从画布选择", icon: Images },
  { key: "assets", label: "从资产库选择", icon: FolderOpen },
  { key: "local", label: "本地添加", icon: Upload },
] as const;

export function JimengSubjectNode({ id, data, selected }: NodeProps) {
  const d = data as JimengSubjectNodeData;
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const pushToast = useJimengStore((s) => s.pushToast);
  const [draft, setDraft] = useState(d.description ?? "");
  const imported = d.imported ?? [];

  const runEntry = (key: (typeof ENTRIES)[number]["key"], label: string) => {
    if (key === "import" || key === "local") {
      const name = `主体素材 ${imported.length + 1}`;
      updateNodeData(id, { imported: [...imported, name] });
      pushToast(FEEDBACK.importSubject(name));
      return;
    }
    // 画布/资产库选择在源站是带上下文的选择器；复刻给出明确反馈而不是静默
    pushToast(
        key === "canvas" ? FEEDBACK.needCanvasNodeFirst(label) : FEEDBACK.needAssetsFirst(label),
      );
  };

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-testid="subject-node"
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start text-left">
        <SquareUser size={16} />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      <div
        className="flex h-full w-full flex-col overflow-hidden rounded-lg p-3"
        style={{
          background: "rgb(24,24,26)",
          boxShadow: nodeRingShadow(selected === true),
        }}
      >
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[13px]/[20px] text-white/85">
            <SquareUser size={15} />
            {d.title}
          </span>
          <button
            type="button"
            aria-label="编辑主体"
            className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10"
          >
            <Pencil size={14} />
          </button>
        </div>

        <input
          value={draft}
          aria-label="主体描述"
          placeholder="添加描述..."
          onChange={(e) => setDraft(e.target.value)}
          onBlur={() => updateNodeData(id, { description: draft })}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
          className="mt-2 h-8 w-full rounded-md bg-transparent px-1 text-[13px]/[20px] text-white/85 outline-none placeholder:text-white/35"
          data-testid="subject-description"
        />

        <div className="mt-2 flex min-h-0 flex-1 flex-col justify-center gap-1 rounded-md bg-white/[0.04] px-3">
          {ENTRIES.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              aria-label={label}
              onClick={() => runEntry(key, label)}
              className="flex h-9 items-center gap-2 rounded-md text-left text-[13px] text-white/80 hover:bg-white/10"
            >
              <Icon size={15} className="text-white/60" />
              {label}
            </button>
          ))}
        </div>

        {imported.length > 0 ? (
          <ul className="mt-2 shrink-0" data-testid="subject-imported">
            {imported.map((n) => (
              <li key={n} className="truncate text-[12px] leading-5 text-white/55">
                · {n}
              </li>
            ))}
          </ul>
        ) : null}

        <span className="sr-only">
          {imported.length === 0
            ? "Empty subject: main missing, 0 auxiliaries, voice missing."
            : `Subject with ${imported.length} imported asset(s).`}
        </span>
      </div>

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
    </div>
  );
}
