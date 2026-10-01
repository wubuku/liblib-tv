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
// Batch 532: 2026-09-27 CDP 补采（截图 40/41）——第 2 步为 角色/场景/道具
// 三组新增虚线卡 + 「资产已生成，如再次生成将会覆盖…」提示；第 3 步为
// 同表格「最终提示词」列高亮 + 一键合成全部提示词；无上一步按钮；
// 下一步推进为本地导航；一键合成不触发真实生成（付费 AI 动作）。

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
  // Batch 532: 2026-09-27 CDP 补采（截图 40/41）——下一步可推进到
  // 准备资产（角色/场景/道具 新增卡 + 覆盖提示）与合成提示词
  // （最终提示词列高亮 + 一键合成全部提示词）；源站无上一步按钮。
  const [step, setStep] = useState(1);

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
          { step: 1, title: "确认镜头", subtitle: `${rows.length}个镜头待核对` },
          { step: 2, title: "准备资产", subtitle: "暂无资产" },
          { step: 3, title: "合成提示词", subtitle: `0/${rows.length} 已合成` },
        ].map((item, index) => (
          <div key={item.step} className="flex items-center gap-16">
            {index > 0 && <span className="h-px w-28 bg-white/10" />}
            <div
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-1.5",
                item.step === step && "bg-white/[0.07]",
              )}
            >
              <span
                className={cn(
                  "flex size-7 items-center justify-center rounded-full text-sm",
                  item.step === step ? "bg-[#e8e8e8] text-[#1a1a1a]" : "border border-white/15 text-[#8c8c8c]",
                )}
              >
                {item.step}
              </span>
              <span className="leading-tight">
                <span className={cn("block text-sm", item.step === step ? "text-[#ededed]" : "text-[#8c8c8c]")}>
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

      {step === 2 ? (
        <div className="mt-5 flex-1 overflow-auto px-6 pb-16">
          {["角色", "场景", "道具"].map((group) => (
            <div key={group} data-storyboard-asset-group={group} className="mb-6">
              <h3 className="text-sm text-[#d8d8d8]">{group}</h3>
              {/* Batch 367: 「新增{分组}资产」无 onClick 也无 disabled, 却带
                  hover:border-white/[0.28] + hover:text-[#c0c0c0] —— 一个
                  195×190 的大虚线卡, 视觉上强烈暗示「点这里能加资产」, 点了
                  什么都不发生。资产新增的源站形态未采样(人机验证阻塞), 不发明;
                  按 batch 358/359/360/364/366 同策让 UI 停止撒谎: 去掉悬停
                  骗人反馈 + cursor: default + title 说明 + data-inert 自证惰性。
                  几何与文案不动。 */}
              <button
                type="button"
                data-storyboard-asset-add
                data-inert="true"
                title="资产新增暂不可用"
                aria-label={`新增${group}资产`}
                className="mt-2 flex h-[190px] w-[195px] cursor-default flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-white/[0.14] text-[#8c8c8c]"
              >
                <span className="text-2xl leading-none">+</span>
                <span className="text-xs">新增</span>
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-5 flex-1 overflow-auto px-6 pb-16">
          <div className="min-w-[1180px] rounded-md border border-white/[0.06]">
            <div className="flex bg-[#1a1a1a] text-xs text-[#a5a5a5]">
              <span className="w-[4%] px-2 py-2.5 text-center">镜号</span>
              <span className="w-[4%] px-2 py-2.5 text-center">时长</span>
              {textColumns.map((column) => (
                <span key={column.key} className={cn("border-l border-white/[0.06] px-2 py-2.5", column.width)}>{column.label}</span>
              ))}
              <span className={cn("w-[8%] border-l border-white/[0.06] px-2 py-2.5", step === 3 && "bg-white/[0.08] text-[#ededed]")}>
                最终提示词
              </span>
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
                {/* Batch 366: 原来无 onClick 也无 disabled, 却带 hover:bg-white/[0.06]
                    —— 每行最右端的「···」操作入口, 视觉上明确在邀请点击, 点了却
                    什么都不发生。源站行操作菜单(复制/删除/重排)的具体项未采样
                    (人机验证阻塞), 不擅自发明, 按 358/359/360/364 同策让 UI 停止
                    撒谎: 去掉悬停骗人反馈 + cursor:default + title 说明 +
                    data-inert 自证惰性。几何与文案不动。 */}
                <button type="button" data-storyboard-row-menu data-inert="true" aria-label={`镜头${row.shot}操作`} title="行操作菜单暂不可用" className="cursor-default rounded px-1.5 py-0.5 text-[#8c8c8c]">···</button>
              </span>
            </div>
          ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between px-6 py-4">
        {step === 2 ? (
          <span data-storyboard-asset-notice className="flex items-center gap-1.5 text-xs text-[#8c8c8c]">
            <span className="text-[#3fbf7f]">✓</span> 资产已生成，如再次生成将会覆盖之前的图片/场景/道具等资产
          </span>
        ) : (
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
        )}
        {step === 1 && (
          <button
            type="button"
            data-storyboard-next-step
            data-storyboard-next="assets"
            onClick={() => setStep(2)}
            className="flex items-center gap-1.5 rounded-full bg-[#e8e8e8] px-4 py-2 text-sm text-[#1a1a1a] hover:bg-white"
          >
            → 下一步：准备资产
          </button>
        )}
        {step === 2 && (
          <button
            type="button"
            data-storyboard-next-step
            data-storyboard-next="prompts"
            onClick={() => setStep(3)}
            className="flex items-center gap-1.5 rounded-full bg-[#e8e8e8] px-4 py-2 text-sm text-[#1a1a1a] hover:bg-white"
          >
            → 下一步：合成提示词
          </button>
        )}
        {step === 3 && (
          /* Batch 368: 这颗**早就有 title 说明**「clone 不触发」, 说明当初
             知道它不干活 —— 但处置只做了一半: 缺 `data-inert` 自证, 而且
             `hover:bg-white` 还在, 白底亮起的 hover 仍在邀请点击。
             「有 title 就算自证」是不成立的 —— title 要悬停才看得见,
             视觉承诺已经先给出去了。付费合成**永不接线**, 按 358/359/360/
             364/366/367 同策补齐 data-inert + cursor:default + 去 hover。
             文案与几何不动。 */
          <button
            type="button"
            data-storyboard-synthesize-all
            data-inert="true"
            title="一键合成全部提示词（真实合成为付费 AI 动作，clone 不触发）"
            className="flex cursor-default items-center gap-1.5 rounded-full bg-[#e8e8e8] px-4 py-2 text-sm text-[#1a1a1a]"
          >
            一键合成全部提示词
          </button>
        )}
      </div>
    </div>
  );
}
