"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUp,
  Circle,
  Eraser,
  Gem,
  HelpCircle,
  Library,
  LoaderCircle,
  MousePointer2,
  Pencil,
  Redo2,
  RotateCcw,
  SquareDashed,
  Undo2,
  Upload,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  PictureEditAction,
  PictureEditMark,
  PictureEditReplacement,
  PictureEditTool,
} from "@/store/canvasStore";

interface PictureEditPanelProps {
  zoom: number;
  mode: PictureEditAction;
  currentTime: number;
  submitting?: boolean;
  onCancel: () => void;
  onConfirm: (marks: PictureEditMark[]) => void;
}

interface MarkHistory {
  past: PictureEditMark[][];
  present: PictureEditMark[];
  future: PictureEditMark[][];
}

type ResizeHandle = "nw" | "ne" | "se" | "sw";

type MarkInteraction =
  | {
      type: "box" | "brush";
      pointerId: number;
      startX: number;
      startY: number;
      markId: string;
      initialMarks: PictureEditMark[];
    }
  | {
      type: "move";
      pointerId: number;
      startX: number;
      startY: number;
      markId: string;
      initialMarks: PictureEditMark[];
    }
  | {
      type: "resize";
      pointerId: number;
      startX: number;
      startY: number;
      markId: string;
      handle: ResizeHandle;
      initialMarks: PictureEditMark[];
    };

const MIN_MARK_SIZE = 0.02;
const POINT_MARK_SIZE = 0.08;
const MAX_HISTORY = 30;

const modeLabels: Record<PictureEditAction, string> = {
  subjectRemove: "主体消除",
  subjectModify: "主体修改",
  subjectReplace: "主体替换",
};

const modeLimits: Record<PictureEditAction, number> = {
  subjectRemove: 4,
  subjectModify: 4,
  subjectReplace: 2,
};

const toolLabels: Record<Exclude<PictureEditTool, "eraser"> | "eraser", string> =
  {
    point: "点选",
    box: "框选",
    brush: "画笔",
    eraser: "橡皮",
  };

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(maximum, Math.max(minimum, value));
}

function cloneMarks(marks: PictureEditMark[]) {
  return marks.map((mark) => ({
    ...mark,
    points: mark.points?.map((point) => ({ ...point })),
    replacement: mark.replacement ? { ...mark.replacement } : undefined,
  }));
}

function marksEqual(left: PictureEditMark[], right: PictureEditMark[]) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function pointInOverlay(
  overlay: HTMLDivElement,
  clientX: number,
  clientY: number,
) {
  const box = overlay.getBoundingClientRect();
  return {
    x: clamp((clientX - box.left) / box.width, 0, 1),
    y: clamp((clientY - box.top) / box.height, 0, 1),
  };
}

function markBounds(mark: PictureEditMark) {
  const points = mark.points ?? [];
  if (points.length === 0) return mark;
  const left = Math.min(...points.map((point) => point.x));
  const top = Math.min(...points.map((point) => point.y));
  const right = Math.max(...points.map((point) => point.x));
  const bottom = Math.max(...points.map((point) => point.y));
  return {
    ...mark,
    relX: left,
    relY: top,
    width: Math.max(MIN_MARK_SIZE, right - left),
    height: Math.max(MIN_MARK_SIZE, bottom - top),
  };
}

function isPointInsideMark(mark: PictureEditMark, point: { x: number; y: number }) {
  return (
    point.x >= mark.relX &&
    point.x <= mark.relX + mark.width &&
    point.y >= mark.relY &&
    point.y <= mark.relY + mark.height
  );
}

function getModePrompt(mode: PictureEditAction) {
  if (mode === "subjectModify") return "描述想要如何更改画面";
  if (mode === "subjectReplace") return "为主体选择替换图";
  return "拖拽或点击视频画面标记需要处理的主体";
}

export function PictureEditPanel({
  zoom,
  mode,
  currentTime,
  submitting = false,
  onCancel,
  onConfirm,
}: PictureEditPanelProps) {
  const limit = modeLimits[mode];
  const [tool, setTool] = useState<PictureEditTool>("point");
  const [history, setHistory] = useState<MarkHistory>({
    past: [],
    present: [],
    future: [],
  });
  const [selectedMarkId, setSelectedMarkId] = useState<string | null>(null);
  const [limitNotice, setLimitNotice] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const interactionRef = useRef<MarkInteraction | null>(null);
  const marksRef = useRef<PictureEditMark[]>([]);
  const markCounterRef = useRef(0);
  const marks = history.present;
  const selectedMark = marks.find((mark) => mark.id === selectedMarkId) ?? null;

  const replaceMarks = useCallback((nextMarks: PictureEditMark[]) => {
    const cloned = cloneMarks(nextMarks);
    marksRef.current = cloned;
    setHistory((current) => ({ ...current, present: cloned }));
  }, []);

  const commitMarks = useCallback(
    (previousMarks: PictureEditMark[], nextMarks: PictureEditMark[]) => {
      if (marksEqual(previousMarks, nextMarks)) return;
      const next = cloneMarks(nextMarks);
      marksRef.current = next;
      setHistory((current) => ({
        past: [...current.past, cloneMarks(previousMarks)].slice(-MAX_HISTORY),
        present: next,
        future: [],
      }));
    },
    [],
  );

  const createMark = useCallback(
    (
      markTool: Exclude<PictureEditTool, "eraser">,
      relX: number,
      relY: number,
      width: number,
      height: number,
      points?: Array<{ x: number; y: number }>,
    ): PictureEditMark => {
      const nextId = ++markCounterRef.current;
      return {
        id: `picture-edit-mark-${nextId}`,
        tool: markTool,
        frameSeconds: Number(currentTime.toFixed(2)),
        relX: clamp(relX, 0, 1),
        relY: clamp(relY, 0, 1),
        width: clamp(width, MIN_MARK_SIZE, 1),
        height: clamp(height, MIN_MARK_SIZE, 1),
        points,
        candidate: `主体 ${nextId}`,
      };
    },
    [currentTime],
  );

  const removeMark = useCallback(
    (markId: string) => {
      const previous = cloneMarks(marksRef.current);
      const next = previous.filter((mark) => mark.id !== markId);
      if (next.length === previous.length) return;
      commitMarks(previous, next);
      setSelectedMarkId(next.at(-1)?.id ?? null);
    },
    [commitMarks],
  );

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      onCancel();
    };

    window.addEventListener("keydown", handleEscape, true);
    return () => window.removeEventListener("keydown", handleEscape, true);
  }, [onCancel]);

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      const interaction = interactionRef.current;
      const overlay = overlayRef.current;
      if (!interaction || !overlay || event.pointerId !== interaction.pointerId) {
        return;
      }

      event.preventDefault();
      const currentPoint = pointInOverlay(overlay, event.clientX, event.clientY);
      const startPoint = pointInOverlay(
        overlay,
        interaction.startX,
        interaction.startY,
      );
      const source = interaction.initialMarks.find(
        (mark) => mark.id === interaction.markId,
      );
      if (!source) return;

      if (interaction.type === "box") {
        const relX = Math.min(startPoint.x, currentPoint.x);
        const relY = Math.min(startPoint.y, currentPoint.y);
        replaceMarks([
          ...cloneMarks(interaction.initialMarks).filter(
            (mark) => mark.id !== source.id,
          ),
          {
            ...source,
            relX,
            relY,
            width: Math.max(MIN_MARK_SIZE, Math.abs(currentPoint.x - startPoint.x)),
            height: Math.max(
              MIN_MARK_SIZE,
              Math.abs(currentPoint.y - startPoint.y),
            ),
          },
        ]);
        return;
      }

      if (interaction.type === "brush") {
        const points = [
          ...(source.points ?? []),
          {
            x: currentPoint.x,
            y: currentPoint.y,
          },
        ];
        replaceMarks([
          ...cloneMarks(interaction.initialMarks).filter(
            (mark) => mark.id !== source.id,
          ),
          markBounds({
            ...source,
            points,
          }),
        ]);
        return;
      }

      if (interaction.type === "move") {
        const deltaX = currentPoint.x - startPoint.x;
        const deltaY = currentPoint.y - startPoint.y;
        const relX = clamp(source.relX + deltaX, 0, 1 - source.width);
        const relY = clamp(source.relY + deltaY, 0, 1 - source.height);
        const movedPoints = source.points?.map((point) => ({
          x: clamp(point.x + deltaX, 0, 1),
          y: clamp(point.y + deltaY, 0, 1),
        }));
        replaceMarks(
          interaction.initialMarks.map((mark) =>
            mark.id === source.id
              ? { ...mark, relX, relY, points: movedPoints }
              : { ...mark },
          ),
        );
        return;
      }

      if (interaction.type !== "resize") return;
      let left = source.relX;
      let top = source.relY;
      let right = source.relX + source.width;
      let bottom = source.relY + source.height;
      if (interaction.handle.includes("w")) {
        left = clamp(currentPoint.x, 0, right - MIN_MARK_SIZE);
      }
      if (interaction.handle.includes("e")) {
        right = clamp(currentPoint.x, left + MIN_MARK_SIZE, 1);
      }
      if (interaction.handle.includes("n")) {
        top = clamp(currentPoint.y, 0, bottom - MIN_MARK_SIZE);
      }
      if (interaction.handle.includes("s")) {
        bottom = clamp(currentPoint.y, top + MIN_MARK_SIZE, 1);
      }
      replaceMarks(
        interaction.initialMarks.map((mark) =>
          mark.id === source.id
            ? {
                ...mark,
                relX: left,
                relY: top,
                width: right - left,
                height: bottom - top,
              }
            : { ...mark },
        ),
      );
    };

    const finishInteraction = (event: PointerEvent) => {
      const interaction = interactionRef.current;
      if (!interaction || event.pointerId !== interaction.pointerId) return;
      interactionRef.current = null;
      commitMarks(interaction.initialMarks, marksRef.current);
    };

    window.addEventListener("pointermove", handlePointerMove, {
      passive: false,
    });
    window.addEventListener("pointerup", finishInteraction);
    window.addEventListener("pointercancel", finishInteraction);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", finishInteraction);
      window.removeEventListener("pointercancel", finishInteraction);
    };
  }, [commitMarks, replaceMarks]);

  const beginDraw = (event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const point = overlayRef.current
      ? pointInOverlay(overlayRef.current, event.clientX, event.clientY)
      : { x: 0.5, y: 0.5 };

    if (tool === "eraser") {
      const target = [...marksRef.current]
        .reverse()
        .find((mark) => isPointInsideMark(mark, point));
      if (target) removeMark(target.id);
      return;
    }

    if (marksRef.current.length >= limit) {
      setLimitNotice(true);
      return;
    }
    setLimitNotice(false);

    const previous = cloneMarks(marksRef.current);
    if (tool === "point") {
      const size = POINT_MARK_SIZE;
      const mark = createMark(
        "point",
        point.x - size / 2,
        point.y - size / 2,
        size,
        size,
      );
      commitMarks(previous, [...previous, mark]);
      setSelectedMarkId(mark.id);
      return;
    }

    const markId = `picture-edit-mark-${++markCounterRef.current}`;
    const mark =
      tool === "box"
        ? {
            ...createMark("box", point.x, point.y, MIN_MARK_SIZE, MIN_MARK_SIZE),
            id: markId,
          }
        : {
            ...createMark("brush", point.x, point.y, MIN_MARK_SIZE, MIN_MARK_SIZE, [
              point,
            ]),
            id: markId,
          };
    interactionRef.current = {
      type: tool,
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      markId,
      initialMarks: previous,
    };
    replaceMarks([...previous, mark]);
    setSelectedMarkId(mark.id);
  };

  const beginMove = (
    mark: PictureEditMark,
    event: React.PointerEvent<HTMLDivElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    if (tool === "eraser") {
      removeMark(mark.id);
      return;
    }
    interactionRef.current = {
      type: "move",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      markId: mark.id,
      initialMarks: cloneMarks(marksRef.current),
    };
    setSelectedMarkId(mark.id);
  };

  const beginResize = (
    mark: PictureEditMark,
    handle: ResizeHandle,
    event: React.PointerEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    interactionRef.current = {
      type: "resize",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      markId: mark.id,
      handle,
      initialMarks: cloneMarks(marksRef.current),
    };
    setSelectedMarkId(mark.id);
  };

  const updateSelectedMark = (
    patch: Partial<Pick<PictureEditMark, "description" | "replacement">>,
  ) => {
    if (!selectedMarkId) return;
    replaceMarks(
      marksRef.current.map((mark) =>
        mark.id === selectedMarkId ? { ...mark, ...patch } : { ...mark },
      ),
    );
  };

  const setReplacement = (replacement: PictureEditReplacement) => {
    updateSelectedMark({ replacement });
  };

  const undo = () => {
    setHistory((current) => {
      const previous = current.past.at(-1);
      if (!previous) return current;
      const present = cloneMarks(previous);
      marksRef.current = present;
      setSelectedMarkId(present.at(-1)?.id ?? null);
      return {
        past: current.past.slice(0, -1),
        present,
        future: [cloneMarks(current.present), ...current.future],
      };
    });
  };

  const redo = () => {
    setHistory((current) => {
      const next = current.future[0];
      if (!next) return current;
      const present = cloneMarks(next);
      marksRef.current = present;
      setSelectedMarkId(present.at(-1)?.id ?? null);
      return {
        past: [...current.past, cloneMarks(current.present)].slice(-MAX_HISTORY),
        present,
        future: current.future.slice(1),
      };
    });
  };

  const reset = () => {
    const previous = cloneMarks(marksRef.current);
    if (previous.length === 0) return;
    commitMarks(previous, []);
    setSelectedMarkId(null);
    setLimitNotice(false);
  };

  const reason = useMemo(() => {
    if (marks.length === 0) return "请先标记主体";
    if (
      mode === "subjectModify" &&
      marks.some((mark) => !mark.description?.trim())
    ) {
      return "请补充每个主体的修改描述";
    }
    if (
      mode === "subjectReplace" &&
      marks.some((mark) => !mark.replacement)
    ) {
      return "请为每个主体选择替换图";
    }
    return null;
  }, [marks, mode]);

  const canSubmit = !reason && !submitting;
  const toolItems: Array<{
    id: PictureEditTool;
    icon: React.ReactNode;
  }> = [
    { id: "point", icon: <MousePointer2 size={14} /> },
    { id: "box", icon: <SquareDashed size={14} /> },
    { id: "brush", icon: <Pencil size={14} /> },
    { id: "eraser", icon: <Eraser size={14} /> },
  ];

  return (
    <>
      <div
        ref={overlayRef}
        data-picture-edit-mark-overlay
        data-picture-edit-tool={tool}
        className={cn(
          "nodrag nowheel nopan absolute inset-0 z-30 overflow-hidden rounded-[2px]",
          tool === "eraser" ? "cursor-cell" : "cursor-crosshair",
        )}
        onPointerDown={beginDraw}
        onClick={(event) => event.stopPropagation()}
      >
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 size-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {marks
            .filter((mark) => mark.tool === "brush" && mark.points)
            .map((mark) => (
              <polyline
                key={mark.id}
                data-picture-edit-mark-path={mark.id}
                points={mark.points
                  ?.map((point) => `${point.x * 100},${point.y * 100}`)
                  .join(" ")}
                fill="none"
                stroke={mark.id === selectedMarkId ? "#09caf5" : "#65d9ed"}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
              />
            ))}
        </svg>
        {marks.map((mark) => {
          const selected = mark.id === selectedMarkId;
          return (
            <div
              key={mark.id}
              data-picture-edit-mark
              data-picture-edit-mark-id={mark.id}
              data-picture-edit-mark-tool={mark.tool}
              data-picture-edit-mark-selected={selected}
              data-picture-edit-mark-frame={mark.frameSeconds}
              className={cn(
                "absolute box-border min-w-2 min-h-2 cursor-grab bg-[#09caf5]/10 active:cursor-grabbing",
                mark.tool === "point" && "rounded-full",
                mark.tool === "brush" && "border border-dashed border-[#65d9ed]/80",
                selected
                  ? "border-2 border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.25)]"
                  : "border border-[#08a2bf]/80",
              )}
              style={{
                left: `${mark.relX * 100}%`,
                top: `${mark.relY * 100}%`,
                width: `${mark.width * 100}%`,
                height: `${mark.height * 100}%`,
              }}
              onPointerDown={(event) => beginMove(mark, event)}
              onClick={(event) => {
                event.stopPropagation();
                setSelectedMarkId(mark.id);
              }}
            >
              <span className="pointer-events-none absolute -top-5 left-0 whitespace-nowrap rounded bg-black/75 px-1.5 py-0.5 text-[10px] text-white">
                {mark.candidate}
              </span>
              {selected && mark.tool !== "point" &&
                (["nw", "ne", "se", "sw"] as const).map((handle) => (
                  <button
                    key={handle}
                    type="button"
                    data-picture-edit-mark-handle={handle}
                    aria-label={`调整${mark.candidate} ${handle}`}
                    onPointerDown={(event) => beginResize(mark, handle, event)}
                    className={cn(
                      "absolute z-10 size-2 rounded-[1px] border border-white bg-[#0690ae]",
                      handle === "nw" && "-left-1 -top-1 cursor-nwse-resize",
                      handle === "ne" && "-right-1 -top-1 cursor-nesw-resize",
                      handle === "se" && "-bottom-1 -right-1 cursor-nwse-resize",
                      handle === "sw" && "-bottom-1 -left-1 cursor-nesw-resize",
                    )}
                  />
                ))}
            </div>
          );
        })}
      </div>

      <div
        data-picture-edit-panel
        className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-40 w-[660px] -translate-x-1/2 translate-y-full origin-top"
        style={{ transform: `scale(${1 / zoom})` }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
      >
        <section className="flex min-h-[176px] flex-col gap-2 rounded-2xl border border-[#363636] bg-[#262626]/[0.98] p-2 shadow-[0_22px_60px_rgba(0,0,0,0.52)] backdrop-blur-xl">
          <header className="flex h-8 shrink-0 items-center gap-2">
            <button
              data-picture-edit-close
              type="button"
              onClick={onCancel}
              disabled={submitting}
              aria-label={`关闭${modeLabels[mode]}`}
              className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#8d8d8d] hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <X size={14} />
            </button>
            <span className="h-6 w-px bg-white/10" />
            <span
              data-picture-edit-mode={mode}
              className="text-[13px] font-medium text-[#ededed]"
            >
              {modeLabels[mode]}
            </span>
            <span
              data-picture-edit-count={`${marks.length}/${limit}`}
              className="rounded-md bg-white/[0.06] px-2 py-1 text-[11px] tabular-nums text-[#aaa]"
            >
              {marks.length}/{limit}
            </span>
            <span className="group relative ml-auto flex size-5 items-center justify-center text-[#777]">
              <HelpCircle size={14} />
              <span className="pointer-events-none invisible absolute bottom-[calc(100%+8px)] right-0 z-50 w-64 rounded-lg border border-white/10 bg-[#202020] p-2.5 text-[11px] leading-5 text-[#d8d8d8] opacity-0 shadow-xl transition-opacity group-hover:visible group-hover:opacity-100">
                {getModePrompt(mode)}
              </span>
            </span>
          </header>

          <div className="flex min-h-8 items-center gap-1">
            {toolItems.map((item) => (
              <button
                key={item.id}
                data-picture-edit-tool={item.id}
                type="button"
                aria-label={toolLabels[item.id]}
                aria-pressed={tool === item.id}
                onClick={() => {
                  setTool(item.id);
                  setLimitNotice(false);
                }}
                className={cn(
                  "flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-xs transition-colors",
                  tool === item.id
                    ? "bg-[#09caf5]/[0.14] text-[#dffbff]"
                    : "text-[#999] hover:bg-white/[0.07] hover:text-white",
                )}
              >
                {item.icon}
                {toolLabels[item.id]}
              </button>
            ))}
            <span className="mx-1 h-6 w-px bg-white/10" />
            <button
              data-picture-edit-history="undo"
              type="button"
              title="撤销"
              aria-label="撤销标记"
              disabled={history.past.length === 0 || submitting}
              onClick={undo}
              className="flex size-8 items-center justify-center rounded-lg text-[#999] hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:text-[#555]"
            >
              <Undo2 size={15} />
            </button>
            <button
              data-picture-edit-history="redo"
              type="button"
              title="重做"
              aria-label="重做标记"
              disabled={history.future.length === 0 || submitting}
              onClick={redo}
              className="flex size-8 items-center justify-center rounded-lg text-[#999] hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:text-[#555]"
            >
              <Redo2 size={15} />
            </button>
            <button
              data-picture-edit-reset
              type="button"
              title="重置"
              aria-label="重置标记"
              disabled={marks.length === 0 || submitting}
              onClick={reset}
              className="flex size-8 items-center justify-center rounded-lg text-[#999] hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:text-[#555]"
            >
              <RotateCcw size={14} />
            </button>
            {limitNotice && (
              <span className="ml-auto text-[11px] text-[#e4a44b]">
                最多标记 {limit} 处
              </span>
            )}
          </div>

          <div className="flex min-h-[52px] min-w-0 flex-1 items-center gap-2 rounded-xl bg-[#1d1d1d] px-2.5 py-2">
            {selectedMark ? (
              <>
                <button
                  type="button"
                  data-picture-edit-mark-selected
                  onClick={() => setSelectedMarkId(null)}
                  className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg bg-[#09caf5]/[0.12] px-2 text-xs text-[#dffbff]"
                >
                  <Circle size={11} fill="currentColor" />
                  {selectedMark.candidate}
                </button>
                <span
                  data-picture-edit-mark-time={selectedMark.frameSeconds}
                  className="shrink-0 text-[10px] tabular-nums text-[#777]"
                >
                  {selectedMark.frameSeconds.toFixed(2)}s
                </span>
                {mode === "subjectModify" && (
                  <textarea
                    data-picture-edit-description
                    value={selectedMark.description ?? ""}
                    onChange={(event) =>
                      updateSelectedMark({ description: event.target.value })
                    }
                    placeholder="描述想要如何更改画面"
                    rows={2}
                    className="nodrag nowheel min-h-9 min-w-0 flex-1 resize-none rounded-lg border border-white/10 bg-[#282828] px-2.5 py-2 text-xs leading-4 text-[#ededed] outline-none placeholder:text-[#666] focus:border-[#09caf5]/60"
                  />
                )}
                {mode === "subjectReplace" && (
                  <div className="flex min-w-0 flex-1 items-center gap-1.5">
                    <button
                      data-picture-edit-replacement="upload"
                      type="button"
                      onClick={() =>
                        setReplacement({
                          source: "upload",
                          label: "本地上传图片",
                        })
                      }
                      className="flex h-8 items-center gap-1.5 rounded-lg border border-white/10 px-2.5 text-xs text-[#cfcfcf] hover:border-[#09caf5]/60 hover:text-white"
                    >
                      <Upload size={13} />
                      本地上传
                    </button>
                    <button
                      data-picture-edit-replacement="history"
                      type="button"
                      onClick={() =>
                        setReplacement({
                          source: "history",
                          label: "历史图库图片",
                        })
                      }
                      className="flex h-8 items-center gap-1.5 rounded-lg border border-white/10 px-2.5 text-xs text-[#cfcfcf] hover:border-[#09caf5]/60 hover:text-white"
                    >
                      <Library size={13} />
                      历史图库
                    </button>
                    {selectedMark.replacement && (
                      <span
                        data-picture-edit-replacement-selected={
                          selectedMark.replacement.source
                        }
                        className="min-w-0 truncate text-[11px] text-[#8eddea]"
                      >
                        已选择 {selectedMark.replacement.label}
                      </span>
                    )}
                  </div>
                )}
                {mode === "subjectRemove" && (
                  <span className="min-w-0 flex-1 truncate text-xs text-[#777]">
                    已标记此主体，提交后将移除并融合背景
                  </span>
                )}
              </>
            ) : (
              <span className="flex min-w-0 items-center gap-2 text-xs text-[#777]">
                <MousePointer2 size={14} />
                {getModePrompt(mode)}
              </span>
            )}
            {marks.length > 0 && (
              <div className="ml-auto flex shrink-0 items-center gap-1">
                {marks.map((mark) => (
                  <button
                    key={mark.id}
                    type="button"
                    aria-label={`选择${mark.candidate}`}
                    aria-pressed={selectedMarkId === mark.id}
                    onClick={() => setSelectedMarkId(mark.id)}
                    className={cn(
                      "flex size-6 items-center justify-center rounded-md text-[10px] tabular-nums",
                      selectedMarkId === mark.id
                        ? "bg-[#09caf5]/20 text-[#dffbff]"
                        : "bg-white/[0.05] text-[#888] hover:bg-white/[0.1] hover:text-white",
                    )}
                  >
                    {mark.id.split("-").at(-1)}
                  </button>
                ))}
              </div>
            )}
          </div>

          <footer className="flex h-8 shrink-0 items-center gap-2">
            <span
              data-picture-edit-submit-reason={reason ?? undefined}
              className={cn(
                "min-w-0 flex-1 truncate text-[11px]",
                reason ? "text-[#bd8c55]" : "text-[#777]",
              )}
            >
              {submitting
                ? "分析中"
                : reason ?? `当前帧 ${currentTime.toFixed(2)}s · 标记将用于整段视频`}
            </span>
            <span className="flex h-7 items-center gap-1 text-xs text-[#777]">
              <Gem size={13} />
              <span>--</span>
            </span>
            <button
              data-picture-edit-submit
              data-picture-edit-submit-status={submitting ? "analyzing" : "idle"}
              type="button"
              disabled={!canSubmit}
              onClick={() => onConfirm(cloneMarks(marksRef.current))}
              aria-label={`提交${modeLabels[mode]}`}
              className="flex h-8 items-center gap-1.5 rounded-lg bg-[#ededed] px-3 text-xs font-medium text-[#242424] transition-[filter,opacity] hover:brightness-110 active:brightness-95 disabled:cursor-not-allowed disabled:opacity-35"
            >
              {submitting ? (
                <LoaderCircle
                  data-picture-edit-spinner
                  size={14}
                  className="animate-spin"
                />
              ) : (
                <ArrowUp size={14} />
              )}
              {submitting ? "分析中" : "提交"}
            </button>
          </footer>
        </section>
      </div>
    </>
  );
}
