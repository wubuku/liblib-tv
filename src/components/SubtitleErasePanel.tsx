"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Gem,
  HelpCircle,
  Redo2,
  RefreshCw,
  Scan,
  Undo2,
  X,
} from "lucide-react";
import {
  type SubtitleEraseMode,
  type SubtitleEraseRegion,
} from "@/store/canvasStore";
import { cn } from "@/lib/utils";

interface SubtitleErasePanelProps {
  zoom: number;
  mode: SubtitleEraseMode;
  onCancel: () => void;
  onConfirm: (
    mode: SubtitleEraseMode,
    regions: SubtitleEraseRegion[],
  ) => void;
}

interface RegionHistory {
  past: SubtitleEraseRegion[][];
  present: SubtitleEraseRegion[];
  future: SubtitleEraseRegion[][];
}

type ResizeHandle = "nw" | "ne" | "se" | "sw";

type RegionInteraction =
  | {
      type: "draw";
      pointerId: number;
      startX: number;
      startY: number;
      regionId: string;
      initialRegions: SubtitleEraseRegion[];
    }
  | {
      type: "move";
      pointerId: number;
      startX: number;
      startY: number;
      regionId: string;
      initialRegions: SubtitleEraseRegion[];
    }
  | {
      type: "resize";
      pointerId: number;
      startX: number;
      startY: number;
      regionId: string;
      handle: ResizeHandle;
      initialRegions: SubtitleEraseRegion[];
    };

const MIN_REGION_SIZE = 0.02;
const MAX_REGION_HISTORY = 30;

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(maximum, Math.max(minimum, value));
}

function cloneRegions(regions: SubtitleEraseRegion[]) {
  return regions.map((region) => ({ ...region }));
}

function regionsEqual(
  left: SubtitleEraseRegion[],
  right: SubtitleEraseRegion[],
) {
  if (left.length !== right.length) return false;
  return left.every((region, index) => {
    const other = right[index];
    return (
      other !== undefined &&
      region.id === other.id &&
      region.relX === other.relX &&
      region.relY === other.relY &&
      region.width === other.width &&
      region.height === other.height
    );
  });
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

export function SubtitleErasePanel({
  zoom,
  mode,
  onCancel,
  onConfirm,
}: SubtitleErasePanelProps) {
  const [history, setHistory] = useState<RegionHistory>({
    past: [],
    present: [],
    future: [],
  });
  const regions = history.present;
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [drawingEnabled, setDrawingEnabled] = useState(mode === "region");
  const regionsRef = useRef(regions);
  const overlayRef = useRef<HTMLDivElement>(null);
  const interactionRef = useRef<RegionInteraction | null>(null);
  const regionCounterRef = useRef(0);

  const replaceRegions = useCallback((nextRegions: SubtitleEraseRegion[]) => {
    regionsRef.current = nextRegions;
    setHistory((current) => ({ ...current, present: nextRegions }));
  }, []);

  const commitSnapshot = useCallback(
    (
      previousRegions: SubtitleEraseRegion[],
      nextRegions: SubtitleEraseRegion[],
    ) => {
      if (regionsEqual(previousRegions, nextRegions)) return;
      regionsRef.current = nextRegions;
      setHistory((current) => ({
        past: [...current.past, cloneRegions(previousRegions)].slice(
          -MAX_REGION_HISTORY,
        ),
        present: cloneRegions(nextRegions),
        future: [],
      }));
    },
    [],
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
      const point = pointInOverlay(overlay, event.clientX, event.clientY);
      const start = pointInOverlay(
        overlay,
        interaction.startX,
        interaction.startY,
      );

      if (interaction.type === "draw") {
        const relX = Math.min(start.x, point.x);
        const relY = Math.min(start.y, point.y);
        const width = Math.abs(point.x - start.x);
        const height = Math.abs(point.y - start.y);
        replaceRegions([
          ...cloneRegions(interaction.initialRegions),
          {
            id: interaction.regionId,
            relX,
            relY,
            width,
            height,
          },
        ]);
        return;
      }

      const source = interaction.initialRegions.find(
        (region) => region.id === interaction.regionId,
      );
      if (!source) return;

      if (interaction.type === "move") {
        const deltaX = point.x - start.x;
        const deltaY = point.y - start.y;
        const relX = clamp(source.relX + deltaX, 0, 1 - source.width);
        const relY = clamp(source.relY + deltaY, 0, 1 - source.height);
        replaceRegions(
          interaction.initialRegions.map((region) =>
            region.id === source.id ? { ...region, relX, relY } : { ...region },
          ),
        );
        return;
      }

      let left = source.relX;
      let top = source.relY;
      let right = source.relX + source.width;
      let bottom = source.relY + source.height;
      if (interaction.handle.includes("w")) {
        left = clamp(point.x, 0, right - MIN_REGION_SIZE);
      }
      if (interaction.handle.includes("e")) {
        right = clamp(point.x, left + MIN_REGION_SIZE, 1);
      }
      if (interaction.handle.includes("n")) {
        top = clamp(point.y, 0, bottom - MIN_REGION_SIZE);
      }
      if (interaction.handle.includes("s")) {
        bottom = clamp(point.y, top + MIN_REGION_SIZE, 1);
      }
      replaceRegions(
        interaction.initialRegions.map((region) =>
          region.id === source.id
            ? {
                ...region,
                relX: left,
                relY: top,
                width: right - left,
                height: bottom - top,
              }
            : { ...region },
        ),
      );
    };

    const finishInteraction = (event: PointerEvent) => {
      const interaction = interactionRef.current;
      if (!interaction || event.pointerId !== interaction.pointerId) return;
      interactionRef.current = null;

      const currentRegions = regionsRef.current;
      const drawnRegion =
        interaction.type === "draw"
          ? currentRegions.find(
              (region) => region.id === interaction.regionId,
            )
          : undefined;
      if (
        interaction.type === "draw" &&
        (!drawnRegion ||
          drawnRegion.width < MIN_REGION_SIZE ||
          drawnRegion.height < MIN_REGION_SIZE)
      ) {
        replaceRegions(cloneRegions(interaction.initialRegions));
        setSelectedRegionId(null);
        return;
      }

      commitSnapshot(interaction.initialRegions, currentRegions);
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
  }, [commitSnapshot, replaceRegions]);

  const beginDraw = (event: React.PointerEvent<HTMLDivElement>) => {
    if (mode !== "region" || !drawingEnabled) return;
    event.preventDefault();
    event.stopPropagation();
    const regionId = `subtitle-region-${++regionCounterRef.current}`;
    interactionRef.current = {
      type: "draw",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      regionId,
      initialRegions: cloneRegions(regionsRef.current),
    };
    setSelectedRegionId(regionId);
  };

  const beginMove = (
    regionId: string,
    event: React.PointerEvent<HTMLDivElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    interactionRef.current = {
      type: "move",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      regionId,
      initialRegions: cloneRegions(regionsRef.current),
    };
    setSelectedRegionId(regionId);
  };

  const beginResize = (
    regionId: string,
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
      regionId,
      handle,
      initialRegions: cloneRegions(regionsRef.current),
    };
    setSelectedRegionId(regionId);
  };

  const undo = () => {
    setHistory((current) => {
      const previous = current.past.at(-1);
      if (!previous) return current;
      const present = cloneRegions(previous);
      regionsRef.current = present;
      setSelectedRegionId(null);
      return {
        past: current.past.slice(0, -1),
        present,
        future: [cloneRegions(current.present), ...current.future],
      };
    });
  };

  const redo = () => {
    setHistory((current) => {
      const next = current.future[0];
      if (!next) return current;
      const present = cloneRegions(next);
      regionsRef.current = present;
      setSelectedRegionId(null);
      return {
        past: [...current.past, cloneRegions(current.present)].slice(
          -MAX_REGION_HISTORY,
        ),
        present,
        future: current.future.slice(1),
      };
    });
  };

  const reset = () => {
    if (regionsRef.current.length === 0) return;
    const previous = cloneRegions(regionsRef.current);
    replaceRegions([]);
    setSelectedRegionId(null);
    commitSnapshot(previous, []);
  };

  const canSubmit = mode === "smart" || regions.length > 0;

  return (
    <>
      {mode === "region" && (
        <div
          ref={overlayRef}
          data-subtitle-region-overlay
          data-drawing-enabled={drawingEnabled}
          className={cn(
            "nodrag nowheel nopan absolute inset-0 z-30 overflow-hidden rounded-[2px]",
            drawingEnabled ? "cursor-crosshair" : "cursor-default",
          )}
          onPointerDown={beginDraw}
          onClick={(event) => event.stopPropagation()}
        >
          {regions.map((region) => {
            const selected = selectedRegionId === region.id;
            return (
              <div
                key={region.id}
                data-subtitle-region
                data-subtitle-region-selected={selected}
                data-rel-x={region.relX.toFixed(4)}
                data-rel-y={region.relY.toFixed(4)}
                data-rel-width={region.width.toFixed(4)}
                data-rel-height={region.height.toFixed(4)}
                onPointerDown={(event) => beginMove(region.id, event)}
                className={cn(
                  "absolute box-border cursor-grab bg-[rgba(7,184,221,0.15)] active:cursor-grabbing",
                  selected
                    ? "border-2 border-[#09caf5]"
                    : "border-[1.5px] border-[#0690ae]",
                )}
                style={{
                  left: `${region.relX * 100}%`,
                  top: `${region.relY * 100}%`,
                  width: `${region.width * 100}%`,
                  height: `${region.height * 100}%`,
                }}
              >
                {selected &&
                  (["nw", "ne", "se", "sw"] as const).map((handle) => (
                    <button
                      key={handle}
                      type="button"
                      data-subtitle-region-handle={handle}
                      aria-label={`调整区域 ${handle}`}
                      onPointerDown={(event) =>
                        beginResize(region.id, handle, event)
                      }
                      className={cn(
                        "absolute z-10 size-2 rounded-[1px] border border-white bg-[#0690ae]",
                        handle === "nw" &&
                          "-left-1 -top-1 cursor-nwse-resize",
                        handle === "ne" &&
                          "-right-1 -top-1 cursor-nesw-resize",
                        handle === "se" &&
                          "-bottom-1 -right-1 cursor-nwse-resize",
                        handle === "sw" &&
                          "-bottom-1 -left-1 cursor-nesw-resize",
                      )}
                    />
                  ))}
              </div>
            );
          })}
        </div>
      )}

      <div
        data-subtitle-erase-panel
        className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-40 h-12 w-max -translate-x-1/2 translate-y-full origin-top"
        // The bordered node is the containing block, so 17 flow units preserve the source's -bottom-4 outer offset.
        style={{ transform: `scale(${1 / zoom})` }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
      >
        <section className="flex h-12 w-max items-center gap-3 rounded-xl border border-[#3a3a3a] bg-[#262626]/95 px-2 py-2 shadow-[0_4px_10px_rgba(0,0,0,0.3)] backdrop-blur-xl">
          <button
            data-subtitle-erase-close
            type="button"
            onClick={onCancel}
            title="关闭"
            aria-label="关闭去字幕"
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#8d8d8d] transition-colors hover:bg-white/[0.07] hover:text-white"
          >
            <X size={14} />
          </button>
          <span className="h-6 w-px shrink-0 bg-white/10" />
          <div
            data-subtitle-erase-mode={mode}
            className="flex h-8 shrink-0 items-center gap-1 px-2 text-[13px] text-[#e8e8e8]"
          >
            <span className="whitespace-nowrap">
              {mode === "smart" ? "智能去字幕" : "框选去字幕"}
            </span>
            {mode === "region" && (
              <span className="group relative flex size-4 items-center justify-center">
                <button
                  data-subtitle-erase-help
                  type="button"
                  aria-label="查看框选去字幕说明"
                  className="flex size-4 items-center justify-center text-[#8b8b8b] hover:text-white"
                >
                  <HelpCircle size={14} />
                </button>
                <span className="pointer-events-none invisible absolute bottom-[calc(100%+10px)] left-1/2 z-50 w-72 -translate-x-1/2 rounded-lg border border-white/10 bg-[#202020] p-3 text-left text-xs leading-5 text-[#d8d8d8] opacity-0 shadow-xl transition-opacity group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100">
                  <span className="mb-1 block text-white">使用说明</span>
                  <span className="block">• 在画面上拖拽鼠标,框选要擦除的区域</span>
                  <span className="block">• 支持框选多个区域,所有框内文字将被擦除</span>
                  <span className="block">• 擦除作用于整段视频,不仅是当前帧</span>
                </span>
              </span>
            )}
          </div>

          {mode === "region" && (
            <>
              <span className="h-6 w-px shrink-0 bg-white/10" />
              <div className="flex items-center gap-1">
                <ToolButton
                  dataAttribute="data-subtitle-region-toggle"
                  label="选择区域"
                  active={drawingEnabled}
                  onClick={() => setDrawingEnabled((value) => !value)}
                >
                  <Scan size={16} />
                </ToolButton>
                <ToolButton
                  dataAttribute="data-subtitle-region-undo"
                  label="撤销"
                  disabled={history.past.length === 0}
                  onClick={undo}
                >
                  <Undo2 size={16} />
                </ToolButton>
                <ToolButton
                  dataAttribute="data-subtitle-region-redo"
                  label="重做"
                  disabled={history.future.length === 0}
                  onClick={redo}
                >
                  <Redo2 size={16} />
                </ToolButton>
                <ToolButton
                  dataAttribute="data-subtitle-region-reset"
                  label="重置"
                  disabled={regions.length === 0}
                  onClick={reset}
                >
                  <RefreshCw size={15} />
                </ToolButton>
              </div>
            </>
          )}

          <span
            data-subtitle-erase-cost
            className="flex h-8 shrink-0 items-center gap-1 text-xs text-[#8b8b8b]"
          >
            <Gem size={14} />
            <span>-</span>
          </span>
          <button
            data-subtitle-erase-submit
            type="button"
            disabled={!canSubmit}
            onClick={() => onConfirm(mode, cloneRegions(regions))}
            title={
              canSubmit ? "生成去字幕视频" : "请选择字幕擦除区域"
            }
            aria-label="生成去字幕视频"
            className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-white text-[#202020] transition-[filter,opacity] hover:brightness-110 active:brightness-95 disabled:cursor-not-allowed disabled:opacity-35"
          >
            <ArrowUp size={13} />
          </button>
        </section>
      </div>
    </>
  );
}

function ToolButton({
  dataAttribute,
  label,
  active = false,
  disabled = false,
  onClick,
  children,
}: {
  dataAttribute:
    | "data-subtitle-region-toggle"
    | "data-subtitle-region-undo"
    | "data-subtitle-region-redo"
    | "data-subtitle-region-reset";
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      {...{ [dataAttribute]: true }}
      type="button"
      disabled={disabled}
      onClick={onClick}
      title={label}
      aria-label={label}
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors",
        active
          ? "bg-white/[0.08] text-white"
          : disabled
            ? "cursor-not-allowed text-[#555]"
            : "text-[#8d8d8d] hover:bg-white/[0.07] hover:text-white",
      )}
    >
      {children}
    </button>
  );
}
