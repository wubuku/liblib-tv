"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

// Batch 531: 2026-09-27 源站 CDP 补采（liblib-source-exploration-2026-09-25
// 截图 38-script-selfwrite-clicked.png + 抽屉 DOM 采样）——脚本生成器
// 「自己编写分镜脚本」入口打开的全屏分镜脚本编辑器：
// 顶部 3 步 stepper（确认镜头/准备资产/合成提示词）+ 右上 0/3 进度与关闭；
// 10 列分镜表格（镜号/时长/画面描述/景别/光影氛围/对白旁白/音效/运镜/
// 最终提示词/操作），首行 1/5s，空单元格左上角 + 号；最终提示词列显示
// 「待生成提示词」；底部 + 添加镜头 与 → 下一步：准备资产。
// 「下一步」的目标步骤未采样（SOURCE_UNCERTAIN），按钮仅为可视态；
// 全部编辑为本地草稿，不触发任何 AI 生成。

interface StoryboardRow {
  shot: number;
  duration: string;
  description: string;
  shotSize: string;
  lighting: string;
  dialogue: string;
  soundEffect: string;
  cameraMove: string;
}

const initialRows: StoryboardRow[] = [
  { shot: 1, duration: "5s", description: "", shotSize: "", lighting: "", dialogue: "", soundEffect: "", cameraMove: "" },
];

const textColumns = [
  { key: "description", label: "画面描述", width: "w-[26%]" },
  { key: "shotSize", label: "景别", width: "w-[6%]" },
  { key: "lighting", label: "光影氛围", width: "w-[11%]" },
  { key: "dialogue", label: "对白/旁白", width: "w-[15%]" },
  { key: "soundEffect", label: "音效", width: "w-[11%]" },
  { key: "cameraMove", label: "运镜", width: "w-[9%]" },
] as const;

function EditableCell({
  value,
  onChange,
  label,
}: {
  value: string;
  onChange: (next: string) => void;
  label: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);

  if (editing) {
    return (
      <input
        data-storyboard-cell-input
        value={draft}
        autoFocus
        aria-label={label}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={() => {
          onChange(draft);
          setEditing(false);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            onChange(draft);
            setEditing(false);
          }
        }}
        className="h-full w-full bg-transparent px-2 text-xs text-[#e6e6e6] outline-none"
      />
    );
  }
  return (
    <button
      type="button"
      data-storyboard-cell
      aria-label={label}
      onClick={() => {
        setDraft(value);
        setEditing(true);
      }}
      className="group/cell relative h-full w-full px-2 py-1.5 text-left text-xs text-[#e6e6e6]"
    >
      {value ? (
        <span className="line-clamp-2">{value}</span>
      ) : (
        <span className="absolute left-1.5 top-1 text-[11px] leading-none text-[#5e5e5e] group-hover/cell:text-[#9a9a9a]">+</span>
      )}
    </button>
  );
}

export function StoryboardScriptEditor() {
  const isOpen = useUIStore((state) => state.isStoryboardEditorOpen);
  const close = useUIStore((state) => state.closeStoryboardEditor);
  const [rows, setRows] = useState<StoryboardRow[]>(initialRows);

  if (!isOpen) return null;

  const updateRow = (shot: number, key: keyof StoryboardRow, value: string) => {
    setRows((current) =>
      current.map((row) => (row.shot === shot ? { ...row, [key]: value } : row)),
    );
  };

  return (
    <div
      data-storyboard-editor
      aria-label="分镜脚本编辑器"
      className="fixed inset-0 z-[280] flex flex-col bg-[#0d0d0d]/[0.97]"
    >
      <div className="flex items-start justify-center gap-16 pt-5">
        {[
          { step: 1, title: "确认镜头", subtitle: `${rows.length}个镜头待核对`, active: true },
          { step: 2, title: "准备资产", subtitle: "暂无资产", active: false },
          { step: 3, title: "合成提示词", subtitle: `0/${rows.length} 已合成`, active: false },
        ].map((item, index) => (
          <div key={item.step} className="flex items-center gap-16">
            {index > 0 && <span className="h-px w-28 bg-white/10" />}
            <div className="flex items-center gap-2.5">
              <span
                className={cn(
                  "flex size-7 items-center justify-center rounded-full text-sm",
                  item.active ? "bg-[#e8e8e8] text-[#1a1a1a]" : "border border-white/15 text-[#8c8c8c]",
                )}
              >
                {item.step}
              </span>
              <span className="leading-tight">
                <span className={cn("block text-sm", item.active ? "text-[#ededed]" : "text-[#8c8c8c]")}>
                  {item.title}
                </span>
                <span className="block text-[11px] text-[#6e6e6e]">{item.subtitle}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
      <div className="absolute right-5 top-5 flex items-center gap-3">
        <span className="text-xs text-[#8c8c8c]">0/3 完成后可批量生成视频</span>
        <button
          type="button"
          data-storyboard-close
          aria-label="关闭分镜脚本编辑器"
          onClick={close}
          className="rounded-lg p-1.5 text-[#a5a5a5] hover:bg-white/[0.07] hover:text-white"
        >
          <X size={18} />
        </button>
      </div>

      <div className="mt-5 flex-1 overflow-auto px-6 pb-16">
        <div className="min-w-[1180px] rounded-md border border-white/[0.06]">
          <div className="flex bg-[#1a1a1a] text-xs text-[#a5a5a5]">
            <span className="w-[4%] px-2 py-2.5 text-center">镜号</span>
            <span className="w-[4%] px-2 py-2.5 text-center">时长</span>
            {textColumns.map((column) => (
              <span key={column.key} className={cn("border-l border-white/[0.06] px-2 py-2.5", column.width)}>{column.label}</span>
            ))}
            <span className="w-[8%] border-l border-white/[0.06] px-2 py-2.5">最终提示词</span>
            <span className="w-[5%] border-l border-white/[0.06] px-2 py-2.5 text-center">操作</span>
          </div>
          {rows.map((row) => (
            <div key={row.shot} data-storyboard-row={row.shot} className="flex border-t border-white/[0.06]">
              <span className="w-[4%] py-3 text-center text-xs text-[#d0d0d0]">{row.shot}</span>
              <span className="w-[4%] py-3 text-center text-xs text-[#d0d0d0]">{row.duration}</span>
              {textColumns.map((column) => (
                <span key={column.key} className={cn("min-h-[52px] border-l border-white/[0.06]", column.width)}>
                  <EditableCell
                    label={column.label}
                    value={row[column.key]}
                    onChange={(next) => updateRow(row.shot, column.key, next)}
                  />
                </span>
              ))}
              <span className="w-[8%] border-l border-white/[0.06] px-2 py-3 text-center text-xs text-[#6e6e6e]">
                待生成提示词
              </span>
              <span className="flex w-[5%] items-center justify-center border-l border-white/[0.06]">
                <button type="button" data-storyboard-row-menu aria-label={`镜头${row.shot}操作`} className="rounded px-1.5 py-0.5 text-[#8c8c8c] hover:bg-white/[0.06]">···</button>
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between px-6 py-4">
        <button
          type="button"
          data-storyboard-add-shot
          onClick={() =>
            setRows((current) => [
              ...current,
              {
                shot: current.length + 1,
                duration: "5s",
                description: "",
                shotSize: "",
                lighting: "",
                dialogue: "",
                soundEffect: "",
                cameraMove: "",
              },
            ])
          }
          className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-[#d8d8d8] hover:bg-white/[0.06]"
        >
          <span className="text-base leading-none">+</span> 添加镜头
        </button>
        <button
          type="button"
          data-storyboard-next-step
          title="下一步：准备资产（源站后续步骤未采样）"
          className="flex items-center gap-1.5 rounded-full bg-[#e8e8e8] px-4 py-2 text-sm text-[#1a1a1a] hover:bg-white"
        >
          → 下一步：准备资产
        </button>
      </div>
    </div>
  );
}
