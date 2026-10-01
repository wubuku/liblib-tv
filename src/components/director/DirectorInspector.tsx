"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Camera,
  Check,
  Download,
  Eye,
  EyeOff,
  Images,
  Lock,
  Plus,
  RotateCcw,
  Route,
  Send,
  Trash2,
  Users,
  X,
  ZoomIn,
  ZoomOut,
  Unlock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DirectorCameraMotionTab } from "@/components/director/DirectorCameraMotionTab";
import {
  DIRECTOR_CAMERA_FOV_MAX,
  DIRECTOR_CAMERA_FOV_MIN,
  useDirectorStore,
  type DirectorCameraLookAtMode,
  type DirectorCapture,
  type DirectorCharacterGroup,
  type DirectorMotionPath,
  type DirectorMotionPathAnchor,
  type DirectorMotionPathHandle,
  type DirectorObject,
  type DirectorShotRecord,
  type DirectorTransform,
  type DirectorTuple3,
} from "@/store/directorStore";
import {
  createDirectorCharacterRig,
  DIRECTOR_POSE_CONTROL_GROUPS,
  DIRECTOR_POSE_PRESETS,
  type DirectorPoseControlDefinition,
  type DirectorPoseControlGroup,
} from "@/components/director/directorPose";
import { getDirectorGroupAnchorTransform } from "@/components/director/directorGroupMath";
import { useDirectorGestureBoundary } from "@/components/director/useDirectorGestureBoundary";
import {
  attachDirectorCameraPreviewCanvas,
  DIRECTOR_CAMERA_PREVIEW_HEIGHT,
  DIRECTOR_CAMERA_PREVIEW_WIDTH,
} from "@/components/director/directorCameraPreview";
import type {
  DirectorCanvasMediaInputV1,
  DirectorPanoramaRuntimeState,
} from "@/lib/directorCanvasMediaIngress";

function cloneDirectorTransform(transform: DirectorTransform): DirectorTransform {
  return {
    position: [...transform.position],
    rotation: [...transform.rotation],
    scale: [...transform.scale],
  };
}

const axisLabels = ["X", "Y", "Z"] as const;

/* Batch 610（源站 2026-10-01 实测 probe68）：字段标签统一是
   `mb-1 flex h-7 items-center text-[13px] font-normal leading-none
   text-white/45`（28 高 + mb-1 + 28 高控件 = 组高 60）；下拉是
   `h-7 w-full rounded-lg border-0 bg-white/10 px-2 text-[12px]
   text-neutral-50 outline-none placeholder:text-white/30
   focus:bg-white/13 appearance-none`。抽成一对组件，三枚 select 共用。 */
function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="mb-1 flex h-7 items-center text-[13px] font-normal leading-none text-white/45">
      {children}
    </span>
  );
}

const FIELD_CONTROL =
  "h-7 w-full rounded-lg border-0 bg-white/10 px-2 text-[12px] text-neutral-50 outline-none placeholder:text-white/30 focus:bg-white/13 appearance-none";

// Batch 610：源站 range 实测 min=15 / max=90 / step=1（probe68 直接读到
// DOM 属性），填充比 (50-15)/(90-15)=46.6% 与实测 fill 宽 79.3/170 吻合。
// 常量在 store 模块（与 updateCamera 的守卫同源），这里只是别名。
const FOV_MIN = DIRECTOR_CAMERA_FOV_MIN;
const FOV_MAX = DIRECTOR_CAMERA_FOV_MAX;

function AxisFields({
  label,
  field,
  values,
  onChange,
  disabledAxes = [],
  disabled = false,
  gestureTargetId = null,
  gestureCommandKind = "inspector-transform",
  keyframedAxes = [],
  onToggleKeyframe,
}: {
  label: string;
  field: keyof DirectorTransform | "target" | "followOffset";
  values: DirectorTuple3;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
  disabledAxes?: Array<0 | 1 | 2>;
  disabled?: boolean;
  gestureTargetId?: string | null;
  gestureCommandKind?: string;
  keyframedAxes?: Array<0 | 1 | 2>;
  onToggleKeyframe?: () => void;
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: gestureCommandKind,
    targetId: gestureTargetId,
    fieldScope: field,
  });
  const isAxisDisabled = (index: number) =>
    disabled || disabledAxes.includes(index as 0 | 1 | 2);
  // Batch 583（源站 2026-10-01 实测）：对象变换三行（位置/旋转/缩放）每轴
  // 都是「可横向拖动的轴片 + 数值框」，aria 逐字为「左右拖动调整 X 轴」。
  // 步进取数值框 step 的 1/4 像素当量（源站未暴露，记为 CLONE_DECISION）。
  const stepFor = () => (field === "rotation" ? 1 : field === "scale" ? 0.05 : 0.1);
  return (
    <fieldset className="border-0 p-0">
      {/* Batch 609（源站 2026-10-01 实测 probe66）：源站字段组标签是
          `mb-1 flex h-7 items-center text-[13px] font-normal leading-none
          text-white/45`（标签盒 28 高 + mb-1 4 + 控件 28 = 组高 60），
          不是 clone 原来的 11px 灰字。 */}
      <legend className="mb-1 flex h-7 items-center text-[13px] font-normal leading-none text-white/45">
        {label}
      </legend>
      {/* Batch 609：源站三轴行 gap-1（实测 80+4+80+4+80 = 248）。 */}
      <div className="grid grid-cols-3 gap-1">
        {values.map((value, index) => {
          const axis = index as 0 | 1 | 2;
          const keyframed = keyframedAxes.includes(axis);
          return (
          <label
            key={axisLabels[index]}
            /* Batch 609：源站单元格 80×28 `relative flex h-7 min-w-0
                overflow-hidden rounded-lg bg-white/10`，
                focus 态提亮到 bg-white/13（无描边）。 */
            className={cn(
              "focus-within:bg-white/13 relative flex h-7 min-w-0 overflow-hidden rounded-lg bg-white/10 transition-colors",
              isAxisDisabled(index) && "opacity-45",
            )}
          >
            {isAxisDisabled(index) ? (
              <span className="flex h-full w-5 shrink-0 items-center justify-center text-[12px] uppercase text-white/45">
                {axisLabels[index].toLowerCase()}
              </span>
            ) : (
              /* Batch 609：源站轴片 20×28 且 `absolute left-0 top-0 z-10`
                  （实测 x=1656 而数值框同起点，轴片压在其上），不是流内 24 宽。 */
              <SceneAxisScrub
                className="absolute left-0 top-0 z-10 flex h-7 w-5 touch-none select-none items-center justify-center rounded-[8px_0px_0px_8px] border-0 bg-transparent text-[12px] font-normal uppercase text-white/45 hover:bg-white/8 hover:text-white/45"
                /* 源站 aria 是大写 `左右拖动调整 X 轴`，而 DOM 文本是小写
                   `x`、靠 CSS `uppercase` 显示成 X。batch 609 一度把轴名
                   一并小写传下去，aria 就变成了 `… x 轴`，与源站不符；
                   字形大小写由 SceneAxisScrub 内部负责。 */
                axis={axisLabels[index]}
                value={value}
                step={stepFor()}
                testId={`${field}-${axisLabels[index]}`}
                onChange={(next) => onChange(index as 0 | 1 | 2, next)}
              />
            )}
            {/* Batch 609：源站数值框 `h-full min-w-0 flex-1 pl-6 pr-0
                text-[12px] tabular-nums`（左对齐，pl-6 让开轴片），
                并用 appearance:textfield 藏掉 number 步进箭头。 */}
            <input
              type="number"
              step={field === "rotation" ? 1 : field === "scale" ? 0.05 : 0.1}
              data-director-transform-field={field}
              data-director-transform-axis={axisLabels[index].toLowerCase()}
              value={Number(value.toFixed(2))}
              disabled={isAxisDisabled(index)}
              {...(isAxisDisabled(index) ? {} : gesture)}
              onChange={(event) =>
                onChange(index as 0 | 1 | 2, Number(event.target.value))
              }
              className="h-full min-w-0 flex-1 appearance-none border-0 bg-transparent pl-6 pr-0 text-[12px] tabular-nums text-neutral-50 outline-none [&::-webkit-inner-spin-button]:m-0 [&::-webkit-outer-spin-button]:appearance-none"
            />
            {/* Batch 609：源站每个格子右端挂一枚 20×28 关键帧开关
                （`当前帧无关键帧` ↔ `当前帧有关键帧` 两态互斥）。 */}
            {onToggleKeyframe ? (
              <KeyframeToggleButton
                on={keyframed}
                testId={`${field}-${axisLabels[index]}`}
                field={field}
                axisIndex={axis}
                disabled={isAxisDisabled(index)}
                onClick={onToggleKeyframe}
              />
            ) : null}
          </label>
          );
        })}
      </div>
    </fieldset>
  );
}

/* Batch 609（源站 2026-10-01 实测 probe67）：关键帧开关两态逐字照抄——
     有：`bg-[#263E43] text-[#5DDCFF]`（实算 rgb(38,62,67) / rgb(93,220,255)）
       菱形 rect `fill=currentColor`；
     无：`bg-white/[0.04] text-white/75 hover:bg-white/[0.07] hover:text-[#5DDCFF]`
       菱形 rect `fill=none stroke=currentColor stroke-width=1.2`。
     两态都带 `ml-px border-l border-black/20`，9×9 svg viewBox 0 0 10 10。 */
const KEYFRAME_TOGGLE_BASE =
  "ml-px flex h-full w-[20px] cursor-pointer shrink-0 items-center justify-center border-l border-black/20 transition-colors";

function KeyframeToggleButton({
  on,
  testId,
  field,
  axisIndex,
  disabled,
  onClick,
}: {
  on: boolean;
  testId: string;
  field: string;
  axisIndex: 0 | 1 | 2;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-director-keyframe-toggle={testId}
      data-director-keyframe-toggle-state={on ? "on" : "off"}
      /* Batch 575 的 `data-director-keyframed-axis` 合同迁到「有」态按钮上，
         取证脚本与既有 verifier 的选择器不变。 */
      {...(on
        ? {
            "data-director-keyframed-axis": field,
            "data-director-keyframed-axis-index": axisIndex,
          }
        : {})}
      aria-label={on ? "当前帧有关键帧" : "当前帧无关键帧"}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        KEYFRAME_TOGGLE_BASE,
        on
          ? "bg-[#263E43] text-[#5DDCFF]"
          : "bg-white/[0.04] text-white/75 hover:bg-white/[0.07] hover:text-[#5DDCFF]",
      )}
    >
      <svg
        width="9"
        height="9"
        viewBox="0 0 10 10"
        aria-hidden="true"
        focusable="false"
        className="shrink-0"
      >
        <rect
          x="1.95"
          y="1.95"
          width="6.1"
          height="6.1"
          rx="1"
          transform="rotate(45 5 5)"
          fill={on ? "currentColor" : "none"}
          stroke="currentColor"
          strokeWidth="1.2"
        />
      </svg>
    </button>
  );
}

function CapturePreview({
  capture,
  onSend,
}: {
  capture: DirectorCapture;
  onSend: (capture: DirectorCapture) => void;
}) {
  return (
    <section data-director-capture-preview className="border-t border-white/[0.07] px-3 py-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs text-[#d7d7d7]">当前截图</h3>
        <span className="text-[10px] tabular-nums text-[#707070]">
          {capture.width} × {capture.height}
        </span>
      </div>
      <div className="relative aspect-video overflow-hidden rounded border border-white/[0.08] bg-black">
        <Image
          src={capture.dataUrl}
          alt={`${capture.cameraName}构图截图`}
          fill
          sizes="288px"
          className="object-contain"
          unoptimized
        />
      </div>
      <button
        type="button"
        data-director-send-capture
        disabled={Boolean(capture.sentNodeId)}
        onClick={() => onSend(capture)}
        className="mt-2 flex h-8 w-full items-center justify-center gap-1.5 rounded bg-[#e8e8e8] text-xs text-[#202020] hover:bg-white disabled:bg-[#363636] disabled:text-[#858585]"
      >
        {capture.sentNodeId ? <Check size={13} /> : <Send size={13} />}
        {capture.sentNodeId ? "已发送到画布" : "发送到画布"}
      </button>
    </section>
  );
}

function formatCaptureLabel(
  capture: DirectorCapture,
  index: number,
  prefix = capture.cameraName,
): string {
  return `${prefix}-截图${String(index + 1).padStart(2, "0")}`;
}

function DirectorCaptureGallery({
  captures,
  onSendCapture,
  onSendAllCaptures,
}: {
  captures: DirectorCapture[];
  onSendCapture: (capture: DirectorCapture) => void;
  onSendAllCaptures: () => void;
}) {
  const activeCaptureId = useDirectorStore((state) => state.activeCaptureId);
  const shots = useDirectorStore((state) => state.shots);
  const objects = useDirectorStore((state) => state.objects);
  const selectCapture = useDirectorStore((state) => state.selectCapture);
  const removeCapture = useDirectorStore((state) => state.removeCapture);
  const clearCaptures = useDirectorStore((state) => state.clearCaptures);
  const [viewerCaptureId, setViewerCaptureId] = useState<string | null>(null);
  const [viewerScale, setViewerScale] = useState(1);
  const [confirmClear, setConfirmClear] = useState(false);
  const viewerCapture =
    captures.find((capture) => capture.id === viewerCaptureId) ?? null;
  const shotGroups = useMemo(() => {
    const shotById = new Map(shots.map((shot) => [shot.id, shot]));
    const cameraById = new Map(
      objects
        .filter((object) => object.kind === "camera")
        .map((object) => [object.id, object]),
    );
    const groups = new Map<
      string,
      {
        shotId: string | null;
        shotName: string;
        cameraName: string;
        captures: DirectorCapture[];
      }
    >();
    captures.forEach((capture) => {
      const shot =
        (capture.shotId ? shotById.get(capture.shotId) : undefined) ??
        (capture.cameraId
          ? shots.find((candidate) => candidate.cameraId === capture.cameraId)
          : undefined);
      const cameraName =
        (capture.cameraId
          ? cameraById.get(capture.cameraId)?.name
          : undefined) ?? capture.cameraName;
      const key =
        shot?.id ?? `camera:${capture.cameraId ?? "unassigned"}`;
      const group = groups.get(key) ?? {
        shotId: shot?.id ?? null,
        shotName: shot?.name ?? "未分配镜头",
        cameraName,
        captures: [],
      };
      group.captures.push(capture);
      groups.set(key, group);
    });
    return Array.from(groups.entries()).map(([key, group]) => {
      const chronological = [...group.captures].sort((left, right) =>
        left.createdAt.localeCompare(right.createdAt),
      );
      return {
        key,
        ...group,
        labels: new Map(
          chronological.map((capture, index) => [
            capture.id,
            formatCaptureLabel(capture, index, group.shotName),
          ]),
        ),
      };
    });
  }, [captures, objects, shots]);

  useEffect(() => {
    if (!viewerCaptureId) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setViewerCaptureId(null);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [viewerCaptureId]);

  const closeViewer = () => setViewerCaptureId(null);
  const changeViewerScale = (delta: number) => {
    setViewerScale((scale) =>
      Math.min(4, Math.max(0.5, Number((scale + delta).toFixed(2)))),
    );
  };

  const viewerLayer = viewerCapture ? (
    <div
      data-director-capture-viewer
      role="dialog"
      aria-label="截图预览"
      className="fixed inset-0 z-[220] flex items-center justify-center bg-black/90 p-5 backdrop-blur-[4px]"
      onClick={closeViewer}
    >
      <div
        className="absolute right-4 top-4 z-10 flex gap-1.5"
        role="toolbar"
        aria-label="截图预览工具栏"
        onClick={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          aria-label="缩小图片"
          title="缩小"
          onClick={() => changeViewerScale(-0.25)}
          className="flex h-9 w-9 items-center justify-center rounded border border-white/10 bg-white/10 text-white/90 hover:bg-white/20"
        >
          <ZoomOut size={16} />
        </button>
        <button
          type="button"
          aria-label="放大图片"
          title="放大"
          onClick={() => changeViewerScale(0.25)}
          className="flex h-9 w-9 items-center justify-center rounded border border-white/10 bg-white/10 text-white/90 hover:bg-white/20"
        >
          <ZoomIn size={16} />
        </button>
        <a
          href={viewerCapture.dataUrl}
          download={`${viewerCapture.cameraName}-截图.png`}
          aria-label="下载图片"
          title="下载"
          onClick={(event) => event.stopPropagation()}
          className="flex h-9 w-9 items-center justify-center rounded border border-white/10 bg-white/10 text-white/90 hover:bg-white/20"
        >
          <Download size={16} />
        </a>
        <button
          type="button"
          data-director-capture-viewer-close
          aria-label="关闭截图预览"
          title="关闭"
          onClick={closeViewer}
          className="flex h-9 w-9 items-center justify-center rounded border border-white/10 bg-white/10 text-white/90 hover:bg-white/20"
        >
          <X size={16} />
        </button>
      </div>
      <div
        className="grid h-full w-full place-items-center overflow-hidden"
        onClick={(event) => event.stopPropagation()}
      >
        <Image
          src={viewerCapture.dataUrl}
          alt={`${viewerCapture.cameraName}截图预览`}
          width={viewerCapture.width}
          height={viewerCapture.height}
          unoptimized
          draggable={false}
          className="max-h-[80vh] max-w-[80vw] select-none rounded object-contain transition-transform duration-200"
          style={{ transform: `scale(${viewerScale})` }}
        />
      </div>
    </div>
  ) : null;

  return (
    <>
      <section
        data-director-capture-gallery
        className="flex min-h-0 flex-1 flex-col"
      >
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {shotGroups.length === 0 ? (
          <div
            data-director-capture-empty
            role="status"
            aria-label="暂无摄像机截图"
            className="flex min-h-[180px] flex-col items-center justify-center gap-2 text-center text-[11px] text-[#686868]"
          >
            <Images size={22} strokeWidth={1.4} />
            <span>暂无摄像机截图</span>
          </div>
        ) : (
          <div className="space-y-4">
            {shotGroups.map(
              ({
                key,
                shotId,
                shotName,
                cameraName,
                captures: groupCaptures,
                labels,
              }) => (
              <section
                key={key}
                data-director-capture-group={cameraName}
                data-director-capture-group-shot={shotId ?? ""}
                aria-label={`${shotName} · ${cameraName}截图`}
              >
                <h3 className="mb-2 text-[11px] text-[#bdbdbd]">
                  {shotName} · {cameraName}
                </h3>
                <div
                  className="grid grid-cols-3 gap-2"
                  aria-label={`${shotName}截图列表`}
                >
                  {groupCaptures.map((capture) => {
                    const label =
                      labels.get(capture.id) ?? `${shotName}截图`;
                    const selected = activeCaptureId === capture.id;
                    return (
                      <article
                        key={capture.id}
                        data-director-capture-item={capture.id}
                        data-director-capture-item-selected={selected}
                        data-director-capture-shot-id={capture.shotId ?? ""}
                        className="min-w-0"
                      >
                        <button
                          type="button"
                          aria-label={`选择截图 ${label}`}
                          aria-pressed={selected}
                          onClick={() => selectCapture(capture.id)}
                          className={cn(
                            "block w-full min-w-0 text-left",
                            selected && "text-[#dffaff]",
                          )}
                        >
                          <span
                            className={cn(
                              "relative block aspect-square overflow-hidden rounded border bg-black",
                              selected
                                ? "border-[#09caf5] shadow-[0_0_0_1px_rgba(9,202,245,0.32)]"
                                : "border-white/[0.1]",
                            )}
                          >
                            <Image
                              src={capture.dataUrl}
                              alt={`${label}缩略图`}
                              fill
                              sizes="84px"
                              className="object-cover"
                              unoptimized
                            />
                          </span>
                          <span className="mt-1 block truncate text-[10px] text-[#858585]">
                            {label}
                          </span>
                        </button>
                        <div className="mt-1 grid grid-cols-3 border border-white/[0.08] bg-[#202020]">
                          <button
                            type="button"
                            data-director-capture-view={capture.id}
                            aria-label={`查看截图 ${label}`}
                            title="查看截图"
                            onClick={() => {
                              selectCapture(capture.id);
                              setViewerCaptureId(capture.id);
                              setViewerScale(1);
                            }}
                            className="flex h-6 items-center justify-center text-[#777] hover:bg-white/[0.06] hover:text-white"
                          >
                            <Eye size={12} />
                          </button>
                          <button
                            type="button"
                            data-director-capture-send={capture.id}
                            aria-label={`发送到画布 ${label}`}
                            title="发送到画布"
                            disabled={Boolean(capture.sentNodeId)}
                            onClick={() => onSendCapture(capture)}
                            className="flex h-6 items-center justify-center text-[#777] hover:bg-white/[0.06] hover:text-white disabled:text-[#3f3f3f]"
                          >
                            {capture.sentNodeId ? (
                              <Check size={12} />
                            ) : (
                              <Send size={12} />
                            )}
                          </button>
                          <button
                            type="button"
                            data-director-capture-remove={capture.id}
                            aria-label={`删除截图 ${label}`}
                            title="删除截图"
                            onClick={() => removeCapture(capture.id)}
                            className="flex h-6 items-center justify-center text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d]"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            ),
            )}
          </div>
        )}
        </div>

        <footer className="grid shrink-0 grid-cols-2 gap-2 border-t border-white/[0.07] px-3 py-3">
        <button
          type="button"
          data-director-capture-clear-all
          disabled={captures.length === 0}
          onClick={() => setConfirmClear(true)}
          className="flex h-8 items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-[11px] text-[#999] hover:text-white disabled:text-[#484848]"
        >
          <Trash2 size={13} />
          全部清空
        </button>
        <button
          type="button"
          data-director-capture-send-all
          disabled={!captures.some((capture) => !capture.sentNodeId)}
          onClick={onSendAllCaptures}
          className="flex h-8 items-center justify-center gap-1.5 rounded bg-[#0aa8cf] text-[11px] text-white hover:bg-[#13b9df] disabled:bg-[#303030] disabled:text-[#555]"
        >
          <Send size={13} />
          发送到画布
        </button>
        </footer>

      {confirmClear ? (
        <div
          data-director-capture-clear-confirm
          role="dialog"
          aria-label="确认清空所有截图"
          className="absolute inset-x-3 bottom-[68px] z-20 rounded border border-white/[0.1] bg-[#262626] p-3 shadow-[0_12px_30px_rgba(0,0,0,0.48)]"
        >
          <p className="text-xs text-[#dedede]">确认清空所有截图？</p>
          <p className="mt-1 text-[10px] leading-4 text-[#777]">
            已发送到画布的图片节点不会被删除。
          </p>
          <div className="mt-3 flex justify-end gap-1.5">
            <button
              type="button"
              data-director-capture-clear-cancel
              onClick={() => setConfirmClear(false)}
              className="h-7 rounded px-2.5 text-[11px] text-[#888] hover:bg-white/[0.06] hover:text-white"
            >
              取消
            </button>
            <button
              type="button"
              data-director-capture-clear-confirm-submit
              onClick={() => {
                clearCaptures();
                setConfirmClear(false);
                closeViewer();
              }}
              className="h-7 rounded bg-[#d76767] px-2.5 text-[11px] text-white hover:bg-[#e57979]"
            >
              确认
            </button>
          </div>
        </div>
      ) : null}

      </section>
      {typeof document !== "undefined" && viewerLayer
        ? createPortal(viewerLayer, document.body)
        : null}
    </>
  );
}

function GroupInspector({ group }: { group: DirectorCharacterGroup }) {
  const objects = useDirectorStore((state) => state.objects);
  const updateGroup = useDirectorStore((state) => state.updateGroup);
  const updateGroupTransform = useDirectorStore(
    (state) => state.updateGroupTransform,
  );
  const recordGroupKeyframe = useDirectorStore(
    (state) => state.recordGroupKeyframe,
  );
  const anchor = getDirectorGroupAnchorTransform(objects, group);
  const hasLockedMember = group.characterIds.some((objectId) =>
    objects.some((object) => object.id === objectId && object.locked),
  );
  const groupNameInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const input = groupNameInputRef.current;
    if (input && document.activeElement !== input) input.value = group.label;
  }, [group.label]);
  if (!anchor) return null;

  const updateField = (
    field: keyof DirectorTransform,
    axis: 0 | 1 | 2,
    value: number,
  ) => {
    const next = cloneDirectorTransform(anchor);
    next[field][axis] = value;
    updateGroupTransform(group.id, next);
    recordGroupKeyframe(group.id);
  };

  return (
    <div
      data-director-group-inspector
      className="space-y-4 px-4 py-3"
    >
      {hasLockedMember ? (
        <p
          data-director-locked-hint
          className="flex items-center gap-1.5 rounded border border-[#f0c776]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#d5b879]"
        >
          <Lock size={12} aria-hidden="true" />
          分组包含已锁定成员，分组变换已停用
        </p>
      ) : null}
      <label className="block">
        <span className="mb-1.5 block text-[11px] text-[#777]">名称</span>
        <input
          data-director-group-name
          ref={groupNameInputRef}
          defaultValue={group.label}
          onBlur={(event) =>
            updateGroup(group.id, { label: event.currentTarget.value })
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") event.currentTarget.blur();
          }}
          className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
        />
      </label>
      <div className="flex items-center gap-2 rounded border border-white/[0.07] bg-[#202020] px-2 py-2 text-[11px] text-[#aaa]">
        <Users size={13} className="text-[#5ddcff]" />
        <span>{group.crowd ? "群众阵列" : "角色组"}</span>
        <span className="ml-auto tabular-nums text-[#777]">
          {group.characterIds.length} 个成员
        </span>
      </div>
      {group.crowd ? (
        <div className="grid grid-cols-3 gap-1.5 text-center text-[10px] text-[#777]">
          <span>行 {group.crowd.rows}</span>
          <span>列 {group.crowd.columns}</span>
          <span>间距 {group.crowd.spacing}</span>
        </div>
      ) : null}
      <div className="space-y-3 border-t border-white/[0.07] pt-4">
        {(
          [
            ["position", "位置"],
            ["rotation", "旋转"],
            ["scale", "缩放"],
          ] as const
        ).map(([field, label]) => (
          <div key={field} data-director-group-transform-field={field}>
            <AxisFields
              label={label}
              field={field}
              values={anchor[field]}
              disabled={hasLockedMember}
              gestureTargetId={group.id}
              gestureCommandKind="group-transform"
              onChange={(axis, value) => updateField(field, axis, value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function PathTupleFields({
  label,
  values,
  kind,
  handle,
  gestureTargetId,
  disabled = false,
  onChange,
}: {
  label: string;
  values: DirectorTuple3;
  kind: "position" | "handle";
  handle?: DirectorMotionPathHandle;
  gestureTargetId: string;
  disabled?: boolean;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: kind === "position" ? "path-anchor-position" : "path-anchor-handle",
    targetId: gestureTargetId,
    fieldScope: kind === "handle" ? `${handle}` : "position",
  });
  return (
    <fieldset className="border-0 p-0">
      <legend className="mb-1.5 text-[11px] text-[#777]">{label}</legend>
      <div className="grid grid-cols-3 gap-1.5">
        {values.map((value, index) => (
          <label
            key={axisLabels[index]}
            className="flex h-8 min-w-0 items-center rounded border border-white/[0.08] bg-[#222] px-1.5 focus-within:border-[#09caf5]/60"
          >
            <span className="mr-1 text-[10px] text-[#666]">
              {axisLabels[index]}
            </span>
            <input
              type="number"
              step="0.1"
              data-director-path-anchor-position={
                kind === "position" ? axisLabels[index].toLowerCase() : undefined
              }
              data-director-path-anchor-handle={
                kind === "handle" ? handle : undefined
              }
              data-director-path-anchor-handle-axis={
                kind === "handle" ? axisLabels[index].toLowerCase() : undefined
              }
              value={Number(value.toFixed(3))}
              disabled={disabled}
              {...(disabled ? {} : gesture)}
              onChange={(event) =>
                onChange(index as 0 | 1 | 2, Number(event.target.value))
              }
              className="min-w-0 flex-1 bg-transparent text-right text-[11px] tabular-nums text-[#d5d5d5] outline-none"
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function PathTransformFields({
  label,
  field,
  values,
  gestureTargetId,
  disabled = false,
  onChange,
}: {
  label: string;
  field: keyof DirectorTransform;
  values: DirectorTuple3;
  gestureTargetId: string;
  disabled?: boolean;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: "path-transform",
    targetId: gestureTargetId,
    fieldScope: field,
  });
  return (
    <fieldset
      data-director-path-transform-field={field}
      className="border-0 p-0"
    >
      <legend className="mb-1.5 text-[11px] text-[#777]">{label}</legend>
      <div className="grid grid-cols-3 gap-1.5">
        {values.map((value, index) => (
          <label
            key={axisLabels[index]}
            className="flex h-8 min-w-0 items-center rounded border border-white/[0.08] bg-[#222] px-1.5 focus-within:border-[#09caf5]/60"
          >
            <span className="mr-1 text-[10px] text-[#666]">
              {axisLabels[index]}
            </span>
            <input
              type="number"
              step={field === "rotation" ? "1" : "0.1"}
              data-director-path-transform-axis={axisLabels[
                index
              ].toLowerCase()}
              value={Number(value.toFixed(3))}
              disabled={disabled}
              {...(disabled ? {} : gesture)}
              onChange={(event) =>
                onChange(index as 0 | 1 | 2, Number(event.target.value))
              }
              className="min-w-0 flex-1 bg-transparent text-right text-[11px] tabular-nums text-[#d5d5d5] outline-none"
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function MotionPathInspector({
  path,
}: {
  path: DirectorMotionPath;
}) {
  const timeline = useDirectorStore((state) => state.timeline);
  const objects = useDirectorStore((state) => state.objects);
  const renameMotionPath = useDirectorStore(
    (state) => state.renameMotionPath,
  );
  const toggleMotionPathEnabled = useDirectorStore(
    (state) => state.toggleMotionPathEnabled,
  );
  const selectMotionPathAnchor = useDirectorStore(
    (state) => state.selectMotionPathAnchor,
  );
  const updateMotionPathAnchorPosition = useDirectorStore(
    (state) => state.updateMotionPathAnchorPosition,
  );
  const updateMotionPathAnchorHandle = useDirectorStore(
    (state) => state.updateMotionPathAnchorHandle,
  );
  const setMotionPathAnchorType = useDirectorStore(
    (state) => state.setMotionPathAnchorType,
  );
  const insertMotionPathAnchor = useDirectorStore(
    (state) => state.insertMotionPathAnchor,
  );
  const deleteMotionPathAnchor = useDirectorStore(
    (state) => state.deleteMotionPathAnchor,
  );
  const toggleMotionPathClosed = useDirectorStore(
    (state) => state.toggleMotionPathClosed,
  );
  const updateMotionPathTransform = useDirectorStore(
    (state) => state.updateMotionPathTransform,
  );
  const resetMotionPathOffset = useDirectorStore(
    (state) => state.resetMotionPathOffset,
  );
  const resetMotionPath = useDirectorStore(
    (state) => state.resetMotionPath,
  );
  const selectedAnchor =
    path.anchors.find(
      (anchor) => anchor.id === timeline.selectedMotionPathAnchorId,
    ) ?? null;
  const objectLocked = objects.some(
    (object) => object.id === path.objectId && object.locked,
  );

  const updateAnchorTuple = (
    anchor: DirectorMotionPathAnchor,
    field: "position" | "handleIn" | "handleOut",
    axis: 0 | 1 | 2,
    value: number,
  ) => {
    const tuple: DirectorTuple3 = [...anchor[field]];
    tuple[axis] = value;
    if (field === "position") {
      updateMotionPathAnchorPosition(path.id, anchor.id, tuple);
      return;
    }
    updateMotionPathAnchorHandle(
      path.id,
      anchor.id,
      field === "handleIn" ? "in" : "out",
      tuple,
    );
  };

  return (
    <section
      data-director-motion-path-inspector={path.id}
      data-director-motion-path-locked={objectLocked}
      className="space-y-3 border-t border-white/[0.07] pt-4"
    >
      {objectLocked ? (
        <p
          data-director-locked-hint
          className="flex items-center gap-1.5 rounded border border-[#f0c776]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#d5b879]"
        >
          <Lock size={12} aria-hidden="true" />
          所属对象已锁定，轨迹编辑已停用
        </p>
      ) : null}
      <div className="flex items-center gap-1.5 text-[11px] text-[#a9a9a9]">
        <Route size={12} className="text-[#5ddcff]" />
        <span>运动轨迹</span>
        <span className="ml-auto text-[10px] uppercase text-[#5d5d5d]">
          {path.preset}
        </span>
      </div>

      <label className="block">
        <span className="mb-1.5 block text-[11px] text-[#777]">名称</span>
        <input
          data-director-path-name
          value={path.name}
          disabled={objectLocked}
          onChange={(event) =>
            renameMotionPath(path.id, event.target.value)
          }
          className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
        />
      </label>

      <div className="grid grid-cols-2 gap-1.5">
        <label className="flex h-8 items-center justify-between rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#bdbdbd]">
          <span>启用曲线</span>
          <input
            type="checkbox"
            checked={path.enabled}
            disabled={objectLocked}
            onChange={() => toggleMotionPathEnabled(path.id)}
            className="accent-[#09caf5]"
          />
        </label>
        <button
          type="button"
          data-director-toggle-path-closed
          aria-pressed={path.closed}
          disabled={objectLocked || (!path.closed && path.anchors.length < 3)}
          onClick={() => toggleMotionPathClosed(path.id)}
          className={cn(
            "h-8 rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#888] hover:text-white disabled:text-[#454545]",
            path.closed && "border-[#09caf5]/35 text-[#5ddcff]",
          )}
        >
          {path.closed ? "闭合路径" : "开放路径"}
        </button>
      </div>

      <div className="space-y-3 border-t border-white/[0.06] pt-3">
        <PathTransformFields
          label="位置"
          field="position"
          values={path.transform.position}
          disabled={objectLocked}
          gestureTargetId={path.id}
          onChange={(axis, value) =>
            updateMotionPathTransform(
              path.id,
              "position",
              axis,
              value,
            )
          }
        />
        <PathTransformFields
          label="旋转"
          field="rotation"
          values={path.transform.rotation}
          disabled={objectLocked}
          gestureTargetId={path.id}
          onChange={(axis, value) =>
            updateMotionPathTransform(
              path.id,
              "rotation",
              axis,
              value,
            )
          }
        />
        <PathTransformFields
          label="缩放"
          field="scale"
          values={path.transform.scale}
          disabled={objectLocked}
          gestureTargetId={path.id}
          onChange={(axis, value) =>
            updateMotionPathTransform(path.id, "scale", axis, value)
          }
        />
        <div className="grid grid-cols-2 gap-1.5">
          <button
            type="button"
            data-director-path-reset-offset
            disabled={objectLocked}
            onClick={() => resetMotionPathOffset(path.id)}
            className="flex h-8 items-center justify-center gap-1 rounded border border-white/[0.08] bg-[#222] text-[11px] text-[#a7a7a7] hover:text-white"
          >
            <RotateCcw size={12} />
            重置偏移
          </button>
          <button
            type="button"
            data-director-path-reset
            disabled={objectLocked}
            onClick={() => resetMotionPath(path.id)}
            className="h-8 rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#777] hover:text-white"
          >
            重置
          </button>
        </div>
      </div>

      <div>
        <div className="mb-1.5 flex items-center justify-between text-[11px] text-[#777]">
          <span>锚点</span>
          <span className="tabular-nums">{path.anchors.length}</span>
        </div>
        <div
          data-director-path-anchor-list
          className="grid grid-cols-6 gap-1"
        >
          {path.anchors.map((anchor, index) => (
            <button
              key={anchor.id}
              type="button"
              data-director-path-anchor-option={anchor.id}
              aria-pressed={anchor.id === selectedAnchor?.id}
              onClick={() =>
                selectMotionPathAnchor(path.id, anchor.id)
              }
              className={cn(
                "flex h-7 min-w-0 items-center justify-center rounded border border-white/[0.07] bg-[#222] text-[10px] tabular-nums text-[#777] hover:text-white",
                anchor.id === selectedAnchor?.id &&
                  "border-[#09caf5]/45 bg-[#09caf5]/10 text-[#5ddcff]",
              )}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      {selectedAnchor ? (
        <div className="space-y-3 border-t border-white/[0.06] pt-3">
          <fieldset className="border-0 p-0">
            <legend className="mb-1.5 text-[11px] text-[#777]">
              锚点类型
            </legend>
            <div className="grid grid-cols-3 rounded bg-[#222] p-0.5">
              {(
                [
                  ["vertex", "顶点"],
                  ["symmetric", "对称"],
                  ["asymmetric", "非对称"],
                ] as const
              ).map(([type, label]) => (
                <button
                  key={type}
                  type="button"
                  data-director-path-anchor-type-option={type}
                  aria-pressed={selectedAnchor.type === type}
                  disabled={objectLocked}
                  onClick={() =>
                    setMotionPathAnchorType(
                      path.id,
                      selectedAnchor.id,
                      type,
                    )
                  }
                  className={cn(
                    "h-7 rounded text-[10px] text-[#777] hover:text-white",
                    selectedAnchor.type === type &&
                      "bg-[#3a3a3a] text-[#5ddcff]",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </fieldset>

          <PathTupleFields
            label="位置"
            kind="position"
            gestureTargetId={selectedAnchor.id}
            disabled={objectLocked}
            values={selectedAnchor.position}
            onChange={(axis, value) =>
              updateAnchorTuple(
                selectedAnchor,
                "position",
                axis,
                value,
              )
            }
          />

          {selectedAnchor.type !== "vertex" ? (
            <>
              <PathTupleFields
                label="入控制柄"
                kind="handle"
                handle="in"
                gestureTargetId={selectedAnchor.id}
                disabled={objectLocked}
                values={selectedAnchor.handleIn}
                onChange={(axis, value) =>
                  updateAnchorTuple(
                    selectedAnchor,
                    "handleIn",
                    axis,
                    value,
                  )
                }
              />
              <PathTupleFields
                label="出控制柄"
                kind="handle"
                handle="out"
                gestureTargetId={selectedAnchor.id}
                disabled={objectLocked}
                values={selectedAnchor.handleOut}
                onChange={(axis, value) =>
                  updateAnchorTuple(
                    selectedAnchor,
                    "handleOut",
                    axis,
                    value,
                  )
                }
              />
            </>
          ) : null}

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              data-director-insert-path-anchor
              disabled={objectLocked}
              onClick={() =>
                insertMotionPathAnchor(path.id, selectedAnchor.id)
              }
              className="flex h-8 flex-1 items-center justify-center gap-1 rounded border border-white/[0.08] bg-[#222] text-[11px] text-[#a7a7a7] hover:text-white"
            >
              <Plus size={12} />
              新增锚点
            </button>
            <button
              type="button"
              data-director-delete-path-anchor
              aria-label="删除锚点"
              title="删除锚点"
              disabled={objectLocked || path.anchors.length <= 2}
              onClick={() =>
                deleteMotionPathAnchor(path.id, selectedAnchor.id)
              }
              className="flex h-8 w-8 items-center justify-center rounded border border-white/[0.08] bg-[#222] text-[#777] hover:text-[#f08d8d] disabled:text-[#3f3f3f]"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function PoseControlGroup({
  character,
  group,
}: {
  character: DirectorObject;
  group: DirectorPoseControlGroup;
}) {
  const updateCharacterPoseControl = useDirectorStore(
    (state) => state.updateCharacterPoseControl,
  );
  const controls =
    character.characterRig?.controls ?? createDirectorCharacterRig().controls;

  // Batch 584（源站实测）：姿势调节七组**全部常驻展开**、无折叠手风琴，
  // 四肢组内先出「左 / 右」子行标题再出各关节滑杆。
  return (
    <section
      data-director-pose-group={group.id}
      data-expanded="true"
      className="border-t border-white/[0.06] pt-2"
    >
      <h4 className="mb-1.5 text-[11px] font-medium text-[#c8c8c8]">
        {group.label}
      </h4>
      <div className="space-y-2">
        {group.rows.map((row, rowIndex) => (
          <div key={row.side ?? `row-${rowIndex}`} className="space-y-2">
            {row.label ? (
              <p
                data-director-pose-side={row.side}
                className="text-[10px] text-[#8b8b8b]"
              >
                {row.label}
              </p>
            ) : null}
            {row.controls.map((control) => (
              <PoseControl
                key={control.key}
                characterId={character.id}
                groupLabel={group.label}
                control={control}
                value={controls[control.key] ?? 0}
                disabled={character.locked}
                updateCharacterPoseControl={updateCharacterPoseControl}
              />
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

function PoseControl({
  characterId,
  groupLabel,
  control,
  value,
  disabled,
  updateCharacterPoseControl,
}: {
  characterId: string;
  groupLabel: string;
  control: DirectorPoseControlDefinition;
  value: number;
  disabled: boolean;
  updateCharacterPoseControl: (
    objectId: string,
    key: string,
    value: number,
  ) => void;
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: "pose-control",
    targetId: characterId,
    fieldScope: control.key,
  });

  // Batch 584: 源站为「标签在上、整宽滑杆在下」，且关节角**不显示数字
  // 读数**（仅滑杆 + aria「{label}角度」）。此处对齐，角度值移入 output
  // 的 aria/value 供辅助技术与 verifier 读取。
  return (
    <label className="block">
      <span className="mb-1 block text-[10px] text-[#8b8b8b]">
        {control.label}
      </span>
      <output
        data-director-pose-value={control.key}
        className="sr-only"
        aria-label={`${control.label}角度`}
      >
        {control.unit === "meter" ? value.toFixed(2) : `${Math.round(value)}°`}
      </output>
      <input
        type="range"
        min={control.min}
        max={control.max}
        step={control.step}
        value={value}
        aria-label={`${groupLabel} ${control.label}`}
        data-director-pose-control={control.key}
        disabled={disabled}
        {...(disabled ? {} : gesture)}
        onChange={(event) =>
          updateCharacterPoseControl(
            characterId,
            control.key,
            Number(event.currentTarget.value),
          )
        }
        className="col-span-2 w-full accent-[#09caf5]"
      />
    </label>
  );
}

function CharacterPoseInspector({
  character,
}: {
  character: DirectorObject;
}) {
  const applyCharacterPosePreset = useDirectorStore(
    (state) => state.applyCharacterPosePreset,
  );
  const rig = character.characterRig ?? createDirectorCharacterRig();

  return (
    <div
      data-director-pose-panel
      className="space-y-4 px-4 py-3"
    >
      {character.locked ? (
        <p
          data-director-locked-hint
          className="flex items-center gap-1.5 rounded border border-[#f0c776]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#d5b879]"
        >
          <Lock size={12} aria-hidden="true" />
          对象已锁定，姿势编辑已停用
        </p>
      ) : null}
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-[11px] font-medium text-[#cfcfcf]">姿势预设</h3>
          <span
            data-director-pose-state
            data-pose-preset={rig.posePresetId ?? "custom"}
            data-pose-control-count={Object.keys(rig.controls).length}
            className="text-[9px] text-[#686868]"
          >
            {rig.posePresetId
              ? DIRECTOR_POSE_PRESETS.find(
                  (preset) => preset.id === rig.posePresetId,
                )?.label ?? "站立"
              : "自定义"}
          </span>
        </div>
        <div className="grid grid-cols-4 gap-1">
          {DIRECTOR_POSE_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              data-director-pose-preset={preset.id}
              aria-pressed={rig.posePresetId === preset.id}
              disabled={character.locked}
              onClick={() =>
                applyCharacterPosePreset(character.id, preset.id)
              }
              className={cn(
                "flex h-8 min-w-0 items-center justify-center rounded border border-white/[0.07] bg-[#222] px-1 text-[10px] text-[#898989] hover:border-white/[0.14] hover:text-white",
                rig.posePresetId === preset.id &&
                  "border-[#09caf5]/45 bg-[#09caf5]/10 text-[#62ddf7]",
              )}
            >
              <span className="min-w-0 truncate">{preset.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-[11px] font-medium text-[#cfcfcf]">姿势调节</h3>
        <p className="mt-1 text-[10px] text-[#686868]">SAM 骨骼姿势</p>
        <div className="mt-2">
          {DIRECTOR_POSE_CONTROL_GROUPS.map((group) => (
              <PoseControlGroup
                key={group.id}
              character={character}
              group={group}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

/**
 * Batch 611（源站 2026-10-01 实测 probe66，裁图二次确认）：属性面板顶部是
 * 一块 sticky 预览缩略图。几何逐字照抄：
 *   section  `sticky top-0 z-20 border-b border-white/8
 *             bg-[rgba(33,33,33,0.98)] px-4 py-4
 *             shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md`  280×168
 *     div    `relative overflow-hidden rounded-xl border`  240×135
 *            （源站底色 rgba(8,8,16,0.95)）
 *     canvas 240×135 —— **真 3D 渲染**，不是示意图
 *     div    `pointer-events-none absolute left-3 top-3 text-[13px]
 *              leading-none text-white/55` → `FOV 50°`
 *     button `hover:bg-white/16 absolute bottom-3 right-3 flex size-6
 *              items-center justify-center rounded-lg bg-white/10
 *              text-white/85` 24×24 + 14px 对角双箭头
 *
 * 渲染由 `CameraPreviewRenderer`（在视口那个 WebGL 上下文里）把 scene 按
 * 本机位离屏渲好后回读进来，这里只负责挂载 2D canvas 与两个角标。
 */
function CameraPreviewSection({
  objectId,
  fov,
}: {
  objectId: string;
  fov: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const viewMode = useDirectorStore((state) => state.viewMode);
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  const selectShot = useDirectorStore((state) => state.selectShot);
  const shot = useDirectorStore((state) =>
    state.shots.find((candidate) => candidate.cameraId === objectId),
  );
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = DIRECTOR_CAMERA_PREVIEW_WIDTH;
    canvas.height = DIRECTOR_CAMERA_PREVIEW_HEIGHT;
    attachDirectorCameraPreviewCanvas(canvas);
    // 只摘自己那块；组件卸载时 canvasRef 已无意义，直接置空即可——
    // 同一时刻面板里只可能有一块预览 canvas。
    return () => attachDirectorCameraPreviewCanvas(null);
  }, []);

  // 源站这枚 24×24 钮的图标是对角双箭头（放大 / 进入），可访问名在
  // 控件全集差集里读作「切换到机位视角」；但它的**点击行为没有取证**
  // （点源站控件会写真实工程）。这里取「切到该机位的机位视角」——复用既有
  // 已验证的 selectShot + setViewMode，不新增 store 动作。记为 INFERENCE。
  const alreadyFraming = viewMode === "camera" && activeCameraId === objectId;

  return (
    <section
      data-director-camera-preview
      className="sticky top-0 z-20 -mx-4 -mt-3 border-b border-white/8 bg-[rgba(33,33,33,0.98)] px-4 py-4 shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md"
    >
      {/* 源站盒实测 240×135（16:9），canvas 也是 240×135 且从 +1 开始——
          源站是 border 压在 canvas 上、由 overflow-hidden 裁掉的。照抄：
          盒 240×135，canvas absolute inset-0 铺满，section 高
          16+135+16+1 = 168 与源站一致。 */}
      <div className="relative h-[135px] w-[240px] overflow-hidden rounded-xl border border-white/10 bg-[rgba(8,8,16,0.95)]">
        <canvas
          ref={canvasRef}
          data-director-camera-preview-canvas
          aria-label="机位取景预览"
          /* absolute 的 left/top 以 padding box 为准，即边框内侧 +1——
             与源站 canvas 起点 [1657,122] 相对盒 [1656,121] 的 +1 一致。 */
          className="absolute left-0 top-0 block h-[135px] w-[240px]"
        />
        <div
          data-director-camera-preview-fov
          className="pointer-events-none absolute left-3 top-3 text-[13px] leading-none text-white/55"
        >
          FOV {fov}°
        </div>
        <button
          type="button"
          data-director-camera-preview-expand
          aria-label="切换到机位视角"
          title="切换到机位视角"
          onClick={() => {
            if (shot) selectShot(shot.id);
            setViewMode("camera");
          }}
          className="absolute bottom-3 right-3 flex size-6 items-center justify-center rounded-lg bg-white/10 text-white/85 transition-colors hover:bg-white/16 hover:text-white"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               aria-hidden="true" focusable="false" className="shrink-0">
            <path d="M7 17 17 7" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" />
            <path d="M17 8.5V7h-1.5" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round" />
            <path d="M7 15.5V17h1.5" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span className="sr-only" data-director-camera-preview-state>
          {alreadyFraming ? "framing" : "idle"}
        </span>
      </div>
    </section>
  );
}

function CameraFovField({
  objectId,
  fov,
  disabled,
  fovKeyframed,
  onToggleKeyframe,
  updateCamera,
  recordObjectKeyframe,
}: {
  objectId: string;
  fov: number;
  disabled: boolean;
  fovKeyframed: boolean;
  onToggleKeyframe: () => void;
  updateCamera: (
    objectId: string,
    patch: Partial<NonNullable<DirectorObject["camera"]>>,
  ) => void;
  recordObjectKeyframe: (objectId: string, force?: boolean) => void;
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: "camera-fov",
    targetId: objectId,
    fieldScope: "fov",
  });

  // Batch 610（源站 2026-10-01 实测 probe68）：FOV 控件**不在面板顶部**。
  // 源站 y=134 那个 `FOV 50°` 是 sticky 预览缩略图
  // （`div.pointer-events-none.absolute.left-3.top-3`）里的角标，不是控件；
  // 真正的控件在 y=842 的「视野角度 (FOV)」段里，位于「注视坐标」之后。
  // batch 581 据历史截图把它读成「FOV 行紧贴页签栏下方」，本批按 live
  // 读数更正（见 README 的读数矛盾记录）。
  const [draft, setDraft] = useState(String(fov));
  useEffect(() => {
    setDraft(String(fov));
  }, [fov]);
  const min = FOV_MIN;
  const max = FOV_MAX;
  const ratio = max > min ? (fov - min) / (max - min) : 0;
  const commit = (next: number) => {
    const clamped = Math.min(max, Math.max(min, next));
    updateCamera(objectId, { fov: clamped });
    recordObjectKeyframe(objectId);
  };
  return (
    <div className="block" data-director-camera-fov-field>
      {/* 标题行：标签 + 16x16 的 ? 徽标，徽标是 tooltip 的 group 宿主 */}
      <div className="mb-3 flex items-center gap-1">
        <span className="text-[13px] font-medium leading-none text-white/45">
          视野角度 (FOV)
        </span>
        <span className="group relative" data-director-camera-fov-help>
          <span
            aria-label="视野角度说明"
            data-director-camera-fov-help-badge
            className="flex h-4 w-4 cursor-default items-center justify-center rounded-full border border-white/20 text-[10px] text-white/45"
          >
            ?
          </span>
          {/* 源站是 hover 浮层（opacity-0 + group-hover:opacity-100 +
              transition-opacity），不是可点开的展开块。 */}
          <span
            data-director-camera-fov-help-tooltip
            className="z-1700 pointer-events-none absolute bottom-[calc(100%+8px)] left-1/2 w-52 -translate-x-1/2 rounded-lg bg-[#2b2b2b] px-2 py-1 text-xs leading-5 text-white/85 opacity-0 shadow-[0_8px_20px_rgba(0,0,0,0.35)] transition-opacity group-hover:opacity-100"
          >
            控制镜头视野范围。数值越小，画面越近、越聚焦；数值越大，画面越广、能看到更多环境。
          </span>
        </span>
      </div>
      {/* 控件行：170px 自绘滑块 + 8px 间隙 + 70px 数值框（170+8+70=248） */}
      <div className="flex items-center justify-center gap-2">
        <div
          data-director-camera-fov-slider
          className="relative h-5 w-[170px] shrink-0"
        >
          <div className="absolute left-0 top-1/2 h-1 w-full -translate-y-1/2 rounded-full bg-[#5c5c5c]">
            <div
              data-director-camera-fov-fill
              className="h-full rounded-full bg-[#09caf5]"
              style={{ width: `${ratio * 100}%` }}
            />
          </div>
          <div
            data-director-camera-fov-knob
            className="pointer-events-none absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#262626] bg-white"
            style={{ left: `${ratio * 100}%` }}
          />
          <input
            type="range"
            min={min}
            max={max}
            step={1}
            aria-label="视野角度 (FOV)"
            data-director-camera-fov
            value={fov}
            disabled={disabled}
            {...(disabled ? {} : gesture)}
            onChange={(event) => commit(Number(event.target.value))}
            className="absolute inset-x-0 top-1/2 h-5 w-full -translate-y-1/2 cursor-pointer touch-none opacity-0 disabled:cursor-default"
          />
        </div>
        <div className="focus-within:bg-white/13 flex h-7 min-w-px flex-1 overflow-hidden rounded-lg bg-white/10 transition-colors">
          <input
            type="number"
            min={min}
            max={max}
            step={1}
            aria-label="视野角度 (FOV) 数值"
            data-director-camera-fov-number
            data-director-camera-fov-readout
            value={draft}
            disabled={disabled}
            onChange={(event) => {
              const raw = event.target.value;
              setDraft(raw);
              if (raw.trim() === "" || !Number.isFinite(Number(raw))) return;
              commit(Number(raw));
            }}
            onBlur={() => setDraft(String(fov))}
            className="h-full min-w-0 flex-1 border-0 bg-transparent px-2 text-center text-[13px] tabular-nums text-neutral-50 outline-none [appearance:textfield] disabled:opacity-45 [&::-webkit-inner-spin-button]:m-0 [&::-webkit-outer-spin-button]:appearance-none"
          />
          <KeyframeToggleButton
            on={fovKeyframed}
            testId="fov"
            field="camera"
            axisIndex={0}
            disabled={disabled}
            onClick={onToggleKeyframe}
          />
        </div>
      </div>
    </div>
  );
}

// Batch 582（源站 2026-10-01 实测）：场景平移 / 场景旋转 的三轴行不是
// 「标签 + 数值框」，而是每轴一个**可横向拖动的轴片**（源站实测
// `<button aria-label="左右拖动调整 X 轴">`）紧贴数值框左侧——按住左右拖
// 即可连续调整该轴。源站未暴露步进量，clone 取数值框 step 的 1/4 像素当量
// 作为拖动灵敏度（CLONE_DECISION）。
function SceneAxisScrub({
  axis,
  value,
  step,
  onChange,
  testId,
  className,
}: {
  axis: string;
  value: number;
  step: number;
  onChange: (next: number) => void;
  testId: string;
  className?: string;
}) {
  const dragRef = useRef<{ x: number; value: number } | null>(null);
  return (
    <button
      type="button"
      data-director-scene-axis-scrub={testId}
      aria-label={`左右拖动调整 ${axis} 轴`}
      onPointerDown={(event) => {
        dragRef.current = { x: event.clientX, value };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        const origin = dragRef.current;
        if (!origin) return;
        const delta = (event.clientX - origin.x) * step * 0.25;
        onChange(Number((origin.value + delta).toFixed(4)));
      }}
      onPointerUp={(event) => {
        dragRef.current = null;
        event.currentTarget.releasePointerCapture(event.pointerId);
      }}
      onPointerCancel={() => {
        dragRef.current = null;
      }}
      className={cn(
        "h-7 w-6 shrink-0 cursor-ew-resize select-none rounded border border-white/[0.08] bg-[#222] text-[10px] font-medium uppercase text-[#8c8c8c] hover:border-[#09caf5]/40 hover:text-white",
        className,
      )}
    >
      {/* 源站实测：aria-label 用大写轴名，DOM 文本是小写，靠 class 里的
          `uppercase` 把字形显示成大写。两件事分开，才与源站逐字一致。 */}
      {axis.toLowerCase()}
    </button>
  );
}

// Batch 585（源站 2026-10-01 实测）：颜色类行的形态是
// `#` 前缀 + **可编辑 hex 文本框** + 取色器，三者同排
// （角色 颜色 y=481/513/518：color #4f8ef7 + text 4F8EF7 + `#`；
//   场景 天空颜色 y=452/457：color #060608 + text 060608 + `#`）。
// 583/582 只把 hex 做成了只读读数，本批补上文本框与提交。
// hex 允许省略 `#`；非法值不提交（保留上一次合法值），大小写归一为小写。
function HexColorRow({
  label,
  value,
  disabled,
  onCommit,
  testId,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onCommit: (hex: string) => void;
  testId: string;
}) {
  const [draft, setDraft] = useState(value.replace("#", ""));
  useEffect(() => {
    setDraft(value.replace("#", ""));
  }, [value]);
  return (
    <label className="flex items-center justify-between text-[11px] text-[#777]">
      <span>{label}</span>
      <span className="flex items-center gap-1.5">
        <span className="text-[10px] text-[#8c8c8c]">#</span>
        <input
          type="text"
          data-director-hex-input={testId}
          aria-label={`${label} hex 值`}
          value={draft}
          disabled={disabled}
          spellCheck={false}
          // Batch 588（源站实测）：hex 文本框 maxLength=6，且 `uppercase` 是
          // **CSS text-transform**（源站 computed textTransform=uppercase，
          // 底层值仍按输入原样保留），不是把值转大写——按值转换会与 585
          // 已固化的 store 小写约定互相打架。
          maxLength={6}
          onChange={(event) => {
            const next = event.target.value.trim();
            setDraft(next);
            if (/^#?[0-9a-fA-F]{6}$/.test(next)) {
              onCommit(next.startsWith("#") ? next.toLowerCase() : `#${next.toLowerCase()}`);
            }
          }}
          onBlur={() => setDraft(value.replace("#", ""))}
          className="h-6 w-[68px] rounded border border-white/[0.08] bg-[#222] px-1.5 text-[10px] uppercase tabular-nums text-[#c8c8c8] outline-none focus:border-[#09caf5]/60 disabled:opacity-45"
        />
        <input
          type="color"
          aria-label={label}
          data-director-color-picker={testId}
          value={value}
          disabled={disabled}
          onChange={(event) => onCommit(event.target.value)}
          className="h-6 w-9 rounded border-0 bg-transparent"
        />
      </span>
    </label>
  );
}

function SceneToggleRow({
  label,
  checked,
  testId,
  dataAttr = "data-director-scene-toggle",
  onToggle,
  compact = false,
}: {
  label: string;
  checked: boolean;
  testId: string;
  /** 沿用既有行的属性名（batch 550 断言 data-director-scene-snap-to-grid）。 */
  dataAttr?: string;
  onToggle: (next: boolean) => void;
  /** 地面行实测为 240×15（嵌套行），其余三行为整宽 280×56。 */
  compact?: boolean;
}) {
  // Batch 588（源站 2026-10-01 实测）：场景面板的开关行不是原生 checkbox，
  // 而是整宽 button（280×56，透明底、space-between、items-center）内含
  // 标签 span + 24×14 全圆角轨道 + 10×10 旋钮：
  //   开 = 轨道纯白 rgb(255,255,255)、旋钮 rgb(31,31,31) 居右（轨道 x+12）
  //   关 = 轨道 rgba(255,255,255,0.18)、旋钮居左（轨道 x+2）
  return (
    <button
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={checked}
      {...{ [dataAttr]: testId }}
      data-director-scene-toggle-on={checked ? "true" : "false"}
      onClick={() => onToggle(!checked)}
      className={cn(
        "flex w-full items-center justify-between border-0 bg-transparent px-4 text-left text-xs text-[#bcbcbc]",
        compact ? "h-[15px]" : "h-14",
      )}
    >
      <span className="truncate">{label}</span>
      <span
        aria-hidden="true"
        data-director-scene-toggle-track
        className={cn(
          "relative block h-[14px] w-6 shrink-0 rounded-full transition-colors",
          checked ? "bg-white" : "bg-white/[0.18]",
        )}
      >
        <span
          data-director-scene-toggle-knob
          className={cn(
            "absolute top-[2px] block size-[10px] rounded-full transition-all",
            checked
              ? "left-[12px] bg-[#1f1f1f]"
              : "left-[2px] bg-white/[0.18]",
          )}
        />
      </span>
    </button>
  );
}

function NumericReadoutInput({
  text,
  ariaLabel,
  testId,
  width = "w-[70px]",
  onCommit,
}: {
  text: string;
  ariaLabel: string;
  testId: string;
  width?: string;
  onCommit: (next: number) => void;
}) {
  // Batch 588（源站 2026-10-01 实测）：滑杆同排的读数是可编辑
  // `input[type=text]`（readOnly=false、disabled=false），不是只读文本，
  // 五处共用同一套样式 `focus:bg-white/13 h-7 min-w-px flex-1 rounded-lg
  // border-0`。提交语义沿用 batch 585 已验证的天空颜色 hex 行模式：
  // 失焦提交、无法解析则回滚到上一个合法值。
  const [draft, setDraft] = useState(text);
  useEffect(() => {
    setDraft(text);
  }, [text]);
  const commit = (next: string) => {
    const parsed = Number.parseFloat(next.replace(/[%°]/g, "").trim());
    if (Number.isFinite(parsed)) {
      onCommit(parsed);
    }
  };
  return (
    <input
      type="text"
      inputMode="decimal"
      data-director-scene-readout={testId}
      aria-label={ariaLabel}
      value={draft}
      spellCheck={false}
      onChange={(event) => {
        setDraft(event.target.value);
        commit(event.target.value);
      }}
      onBlur={() => setDraft(text)}
      className={cn(
        "h-7 min-w-px rounded-lg border-0 bg-white/[0.06] px-2 text-right text-[11px]",
        "tabular-nums text-[#c8c8c8] outline-none focus:bg-white/[0.13]",
        width,
      )}
    />
  );
}

function formatDirectorShotRange(startTime: number, endTime: number): string {
  return `${startTime.toFixed(1)}-${endTime.toFixed(1)}s`;
}

function DirectorShotInspector({
  shot,
  duration,
}: {
  shot: DirectorShotRecord;
  duration: number;
}) {
  const updateShot = useDirectorStore((state) => state.updateShot);
  const [name, setName] = useState(shot.name);
  const [startTime, setStartTime] = useState(String(shot.startTime));
  const [endTime, setEndTime] = useState(String(shot.endTime));

  const resetFromStore = () => {
    const current = useDirectorStore
      .getState()
      .shots.find((candidate) => candidate.id === shot.id);
    setName(current?.name ?? shot.name);
    setStartTime(String(current?.startTime ?? shot.startTime));
    setEndTime(String(current?.endTime ?? shot.endTime));
  };

  const commitName = () => {
    const result = updateShot(shot.id, { name });
    if (result.disposition !== "COMMITTED") resetFromStore();
  };

  const commitStartTime = () => {
    const result = updateShot(shot.id, { startTime: Number(startTime) });
    if (result.disposition !== "COMMITTED") resetFromStore();
  };

  const commitEndTime = () => {
    const result = updateShot(shot.id, { endTime: Number(endTime) });
    if (result.disposition !== "COMMITTED") resetFromStore();
  };

  return (
    <section
      data-director-shot-inspector
      className="space-y-3 border-b border-white/[0.07] px-3 py-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-[11px] font-medium text-[#cfcfcf]">当前镜头</h3>
        <span
          data-director-shot-range
          data-director-shot-id={shot.id}
          className="text-[10px] tabular-nums text-[#777]"
        >
          {formatDirectorShotRange(shot.startTime, shot.endTime)}
        </span>
      </div>
      <label className="block">
        <span className="mb-1.5 block text-[11px] text-[#777]">镜头名称</span>
        <input
          data-director-shot-name
          value={name}
          onChange={(event) => setName(event.currentTarget.value)}
          onBlur={commitName}
          onKeyDown={(event) => {
            if (event.key === "Enter") event.currentTarget.blur();
          }}
          className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
        />
      </label>
      <div className="grid grid-cols-2 gap-1.5">
        <label className="block">
          <span className="mb-1.5 block text-[11px] text-[#777]">开始</span>
          <input
            data-director-shot-start
            type="number"
            min="0"
            max={duration}
            step="0.1"
            value={startTime}
            onChange={(event) => setStartTime(event.currentTarget.value)}
            onBlur={commitStartTime}
            className="h-8 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-2 text-right text-[11px] tabular-nums text-[#d5d5d5] outline-none focus:border-[#09caf5]/60"
          />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[11px] text-[#777]">结束</span>
          <input
            data-director-shot-end
            type="number"
            min="0"
            max={duration}
            step="0.1"
            value={endTime}
            onChange={(event) => setEndTime(event.currentTarget.value)}
            onBlur={commitEndTime}
            className="h-8 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-2 text-right text-[11px] tabular-nums text-[#d5d5d5] outline-none focus:border-[#09caf5]/60"
          />
        </label>
      </div>
    </section>
  );
}

export function DirectorInspector({
  activeCapture,
  onSendCapture,
  onSendAllCaptures,
  panoramaInputs,
  selectedPanoramaSourceId,
  panoramaRuntimeState,
  onPanoramaSourceChange,
}: {
  activeCapture: DirectorCapture | null;
  onSendCapture: (capture: DirectorCapture) => void;
  onSendAllCaptures: () => void;
  panoramaInputs: DirectorCanvasMediaInputV1[];
  selectedPanoramaSourceId: string | null;
  panoramaRuntimeState: DirectorPanoramaRuntimeState;
  onPanoramaSourceChange: (sourceNodeId: string | null) => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
  const shots = useDirectorStore((state) => state.shots);
  const captures = useDirectorStore((state) => state.captures);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const updateScene = useDirectorStore((state) => state.updateScene);
  const addDirectorCamera = useDirectorStore(
    (state) => state.addDirectorCamera,
  );
  const updateObject = useDirectorStore((state) => state.updateObject);
  const updateObjectTransform = useDirectorStore(
    (state) => state.updateObjectTransform,
  );
  const updateCamera = useDirectorStore((state) => state.updateCamera);
  const recordObjectKeyframe = useDirectorStore(
    (state) => state.recordObjectKeyframe,
  );
  const [poseObjectId, setPoseObjectId] = useState<string | null>(null);
  const sceneNameInputRef = useRef<HTMLInputElement>(null);
  const objectNameInputRef = useRef<HTMLInputElement>(null);
  const selectShot = useDirectorStore((state) => state.selectShot);
  // Batch 563: 源站截图 50/51——摄像机面板三页签 属性 | 运动轨迹(NEW) | 截图；
  // 运动轨迹页签承载 虚拟相机（扫码连接 + 录制/重试）与 预设运镜/创建运动轨迹。
  const [cameraTab, setCameraTab] = useState<
    "properties" | "motion" | "captures"
  >("properties");
  const timeline = useDirectorStore((state) => state.timeline);
  const selectedGroup =
    groups.find((group) => group.id === selectedGroupId) ?? null;
  const selected = objects.find((object) => object.id === selectedObjectId) ?? null;
  const selectedShot =
    selected?.kind === "camera"
      ? shots.find((shot) => shot.cameraId === selected.id) ?? null
      : null;
  // Batch 575: 源站截图 60——摄像机面板 位置 X/Y/Z 输入右侧的青色菱形
  // 轴标记（该轴在当前播放头时间存在关键帧）。autoKeyframe 提交后
  // recordObjectKeyframe 落轨道，此处从变换轨道反查三轴。
  const keyframedAxes = useMemo(() => {
    if (!selected) return [];
    const track = timeline.tracks.find(
      (candidate) =>
        candidate.objectId === selected.id &&
        (candidate.kind === "transform" || candidate.kind === "camera"),
    );
    if (!track) return [];
    const axes: Array<0 | 1 | 2> = [];
    (["position", "rotation", "scale"] as const).forEach((field, fieldIndex) => {
      const hasKey = track.keyframes.some((keyframe) => {
        // 相机轨道关键帧 value 形如 { transform, target, fov }；变换轨道
        // keyframe.value 即 DirectorTransform。Batch 609 修：此前只读
        // `value.transform`，于是**角色/道具这类 transform 轨道恒为 false**
        // （batch 575 只测过相机，掩盖了它）——两种形态都要认。
        const raw = keyframe.value as unknown as Record<string, unknown>;
        const values = (raw?.transform ?? raw) as
          | Record<string, unknown>
          | undefined;
        return (
          Math.abs(keyframe.time - timeline.currentTime) < 0.001 &&
          Array.isArray(values?.[field])
        );
      });
      if (hasKey) axes.push(fieldIndex as 0 | 1 | 2);
    });
    return axes;
  }, [selected, timeline]);
  // Batch 609：关键帧开关要能「删掉当前帧这一枚」，所以这里除了字段粒度的
  // 布尔判定，还要拿到播放头处那一枚关键帧的 id（同一时刻的多枚取最后一枚，
  // 与 upsertTrackKeyframe 的覆盖写入顺序一致）。
  const keyframeAtPlayheadId = useMemo(() => {
    if (!selected) return null;
    const track = timeline.tracks.find(
      (candidate) =>
        candidate.objectId === selected.id &&
        (candidate.kind === "transform" || candidate.kind === "camera"),
    );
    if (!track) return null;
    let hit: string | null = null;
    for (const keyframe of track.keyframes) {
      if (Math.abs(keyframe.time - timeline.currentTime) < 0.001) {
        hit = keyframe.id;
      }
    }
    return hit;
  }, [selected, timeline]);
  const deleteTimelineKeyframe = useDirectorStore(
    (state) => state.deleteTimelineKeyframe,
  );
  // 有则删、无则按当前变换补一枚（force=true 绕开 autoKeyframe 开关——
  // 显式打点不该被「自动关键帧」这个全局开关拦掉）。
  const toggleKeyframeAtPlayhead = () => {
    if (!selected) return;
    if (keyframeAtPlayheadId) {
      deleteTimelineKeyframe(keyframeAtPlayheadId);
    } else {
      recordObjectKeyframe(selected.id, true);
    }
  };
  // Batch 610：FOV 数值框尾部的关键帧开关。源站把 fov 存在**相机轨道**
  // 关键帧里（{ transform, target, fov }），与变换行读的是同一枚关键帧，
  // 所以这里直接复用播放头那一枚的 id——按钮管的是「这一帧」，不是「这一
  // 个字段」，与源站「每个数值框右端都挂同一枚开关」的结构一致。
  const cameraFovKeyframed = keyframeAtPlayheadId !== null;
  const toggleCameraFovKeyframe = toggleKeyframeAtPlayhead;
  useEffect(() => {
    const input = sceneNameInputRef.current;
    if (input && document.activeElement !== input) input.value = scene.name;
  }, [scene.name]);
  // Batch 345: DOM 回填只按 id/name 变化触发（activeElement 守卫防打字覆盖），
  // 故意收窄依赖，不随 selected 其余字段重跑。
  useEffect(() => {
    const input = objectNameInputRef.current;
    if (input && document.activeElement !== input && selected) {
      input.value = selected.name;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id, selected?.name]);
  const selectedTrack = timeline.tracks.find((track) => {
    if (track.id !== timeline.selectedTrackId) return false;
    return selectedGroup
      ? track.kind === "group" && track.groupId === selectedGroup.id
      : Boolean(selected && track.objectId === selected.id);
  }) ?? null;
  const selectedPath = selectedTrack?.motionPathId
    ? timeline.motionPaths.find(
        (path) => path.id === selectedTrack.motionPathId,
      )
    : undefined;
  const pathControlsRotationY =
    selectedTrack?.kind === "transform" &&
    selectedPath?.enabled === true &&
    selectedPath.orientToPath;
  const characterTab =
    selected?.kind === "character" && poseObjectId === selected.id
      ? "pose"
      : "properties";
  const cameraTargets = objects.filter(
    (object) =>
      object.visible &&
      (object.kind === "character" || object.kind === "prop"),
  );

  return (
    <section
      data-director-inspector
      data-director-inspector-kind={
        selectedGroup ? "group" : selected?.kind ?? "scene"
      }
      data-director-inspector-track-id={selectedTrack?.id ?? ""}
      className="flex h-full min-h-0 flex-col bg-[#191919]"
    >
      <header className="flex h-12 shrink-0 items-center border-b border-white/[0.07] px-3">
        <h2 className="text-xs font-medium text-[#dedede]">
          {selectedGroup ? "分组属性" : selected ? "对象属性" : "场景属性"}
        </h2>
        <span className="ml-auto text-[10px] text-[#666]">
          {selectedGroup
            ? selectedGroup.crowd
              ? "群众"
              : "角色组"
            : selected?.kind === "camera"
            ? "摄像机"
            : selected?.kind === "character"
              ? "角色"
              : selected
                ? "场景物体"
                : "Scene"}
        </span>
      </header>

      {selectedGroup ? (
        <GroupInspector group={selectedGroup} />
      ) : selected?.kind === "character" ? (
        <nav
          data-director-character-tabs
          aria-label="角色编辑"
          // Batch 603：与摄像机页签共用同一套外壳（源站是同一个 `<section>` +
          // `scrollbar-hide` 页签条）。**页签集合本身未取证**——源站当前工程只
          // 采样到机位（属性/运动轨迹/截图），角色是否也是这三项没测，所以
          // clone 的 属性/姿势 保留，只对齐外壳与胶囊样式。
          className="relative w-full min-w-0 max-w-full shrink-0 overflow-hidden border-b border-white/8 px-4 pb-3"
        >
          <div className="scrollbar-hide flex w-full min-w-0 max-w-full gap-2 overflow-x-auto overflow-y-hidden pt-4">
          {(
            [
              ["properties", "属性"],
              ["pose", "姿势"],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              data-director-character-tab={tab}
              aria-pressed={characterTab === tab}
              onClick={() =>
                setPoseObjectId(tab === "pose" ? selected.id : null)
              }
              className={cn(
                "relative flex h-7 min-w-12 shrink-0 items-center justify-center rounded-lg px-3 text-[13px] font-normal transition-colors",
                characterTab === tab
                  ? "bg-white/10 text-neutral-50"
                  : "text-white/45 hover:bg-white/6 hover:text-white/75",
              )}
            >
              <span className="shrink-0">{label}</span>
            </button>
          ))}
          </div>
        </nav>
      ) : selected?.kind === "camera" ? (
        <nav
          data-director-camera-tabs
          aria-label="摄像机编辑"
          // Batch 603（源站 2026-10-01 实测，/tmp/src593/probe49）：源站这层是
          // `<section class="border-white/8 relative w-full min-w-0 max-w-full
          //  overflow-hidden border-b px-4 pb-3">`（280×57 @(1640,48)），
          // 里面再套一条横向滚动但隐藏滚动条的页签条
          // `scrollbar-hide flex w-full min-w-0 max-w-full gap-2
          //  overflow-x-auto overflow-y-hidden pt-4`（248×44）。
          // 16(上) + 28(页签) + 12(下) + 1(下边框) = 57px。
          // clone 原先是 `grid h-9 grid-cols-3 p-1`：等宽分列、固定 36px 高。
          className="relative w-full min-w-0 max-w-full shrink-0 overflow-hidden border-b border-white/8 px-4 pb-3"
        >
          <div className="scrollbar-hide flex w-full min-w-0 max-w-full gap-2 overflow-x-auto overflow-y-hidden pt-4">
          {(
            [
              ["properties", "属性"],
              ["motion", "运动轨迹"],
              ["captures", "截图"],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              data-director-camera-tab={tab}
              aria-pressed={cameraTab === tab}
              onClick={() => setCameraTab(tab)}
              // 源站逐字：`relative flex h-7 min-w-12 shrink-0 items-center
              // justify-center rounded-lg px-3 text-[13px] font-normal
              // transition-colors`，选中叠 `bg-white/10 text-neutral-50`，
              // 未选中 `hover:bg-white/6 text-white/45 hover:text-white/75`。
              // 宽度是**内容自适应 + 48px 下限**（实测 50/76/50），不是等分列。
              className={cn(
                "relative flex h-7 min-w-12 shrink-0 items-center justify-center rounded-lg px-3 text-[13px] font-normal transition-colors",
                cameraTab === tab
                  ? "bg-white/10 text-neutral-50"
                  : "text-white/45 hover:bg-white/6 hover:text-white/75",
              )}
            >
              <span className="shrink-0">{label}</span>
              {tab === "motion" ? (
                // 源站的 NEW 角标逐字：
                // `pointer-events-none absolute right-0 top-0 z-10 flex h-5
                //  -translate-y-[70%] items-center justify-center rounded-t-lg
                //  rounded-bl-sm rounded-br-lg bg-[#5DDCFF] px-1.5 text-[11px]
                //  font-medium leading-3 text-black`
                <span
                  aria-hidden="true"
                  data-director-camera-motion-new
                  className="pointer-events-none absolute right-0 top-0 z-10 flex h-5 -translate-y-[70%] items-center justify-center rounded-t-lg rounded-bl-sm rounded-br-lg bg-[#5DDCFF] px-1.5 text-[11px] font-medium leading-3 text-black"
                >
                  NEW
                </span>
              ) : null}
            </button>
          ))}
          </div>
        </nav>
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto">
        {selectedGroup ? null : selected ? (
          selected.kind === "camera" && cameraTab === "motion" ? (
            <DirectorCameraMotionTab cameraName={selected.name} />
          ) : selected.kind === "camera" && cameraTab === "captures" ? (
            <DirectorCaptureGallery
              captures={captures}
              onSendCapture={onSendCapture}
              onSendAllCaptures={onSendAllCaptures}
            />
          ) : selected.kind === "character" && characterTab === "pose" ? (
            <CharacterPoseInspector character={selected} />
          ) : (
          <div className="space-y-4 px-4 py-3">
            {selected.locked ? (
              <p
                data-director-locked-hint
                className="flex items-center gap-1.5 rounded border border-[#f0c776]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#d5b879]"
              >
                <Lock size={12} aria-hidden="true" />
                对象已锁定，属性与变换编辑已停用
              </p>
            ) : null}
            {/* Batch 610：FOV 控件已从面板顶部移到这里（源站实测 FOV 段
                y=798，在「注视坐标」之后、「相机截图」之前）。 */}
            {selected.camera ? (
              <CameraPreviewSection
                objectId={selected.id}
                fov={selected.camera.fov}
              />
            ) : null}
            <label className="block">
              {/* Batch 609（源站 probe67 实测）：名称标签同样是 h-7 / 13px /
                  text-white/45，输入框 `h-7 w-full rounded-lg border-0
                  bg-white/10 px-2 text-[12px] text-neutral-50
                  placeholder:text-white/30 focus:bg-white/13`。 */}
              <span className="mb-1 flex h-7 items-center text-[13px] font-normal leading-none text-white/45">
                名称
              </span>
              <input
                ref={objectNameInputRef}
                data-director-object-name
                defaultValue={selected.name}
                disabled={selected.locked}
                onBlur={(event) =>
                  updateObject(selected.id, { name: event.currentTarget.value })
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") event.currentTarget.blur();
                }}
                className="h-7 w-full rounded-lg border-0 bg-white/10 px-2 text-[12px] text-neutral-50 outline-none placeholder:text-white/30 focus:bg-white/13 disabled:opacity-45"
              />
            </label>

            {selected.kind === "camera" ? (
              <label className="mt-3 block">
                <FieldLabel>切换机位</FieldLabel>
                <select
                  data-director-camera-switch
                  value={
                    shots.find((shot) => shot.cameraId === selected.id)?.id ?? ""
                  }
                  onChange={(event) => {
                    if (event.currentTarget.value) {
                      selectShot(event.currentTarget.value);
                    }
                  }}
                  className={cn(FIELD_CONTROL, "disabled:opacity-45")}
                >
                  {objects
                    .filter((object) => object.kind === "camera")
                    .map((camera) => {
                      const shot = shots.find(
                        (candidate) => candidate.cameraId === camera.id,
                      );
                      return (
                        <option
                          key={camera.id}
                          value={shot?.id ?? ""}
                          disabled={!shot}
                        >
                          {camera.name}
                        </option>
                      );
                    })}
                </select>
              </label>
            ) : null}

            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label={selected.visible ? "隐藏对象" : "显示对象"}
                onClick={() =>
                  updateObject(selected.id, { visible: !selected.visible })
                }
                className="flex h-8 flex-1 items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-xs text-[#bdbdbd] hover:text-white"
              >
                {selected.visible ? <Eye size={13} /> : <EyeOff size={13} />}
                {selected.visible ? "可见" : "已隐藏"}
              </button>
              <button
                type="button"
                data-director-inspector-lock
                aria-label={selected.locked ? "解锁对象" : "锁定对象"}
                title={selected.locked ? "解锁对象" : "锁定对象"}
                onClick={() =>
                  updateObject(selected.id, { locked: !selected.locked })
                }
                className={cn(
                  "flex h-8 flex-1 items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-xs text-[#bdbdbd] hover:text-white",
                  selected.locked && "border-[#f0c776]/35 text-[#f0c776]",
                )}
              >
                {selected.locked ? <Lock size={13} /> : <Unlock size={13} />}
                {selected.locked ? "已锁定" : "未锁定"}
              </button>
            </div>

            <div className="space-y-3 border-t border-white/[0.07] pt-4">
              <AxisFields
                label="位置"
                field="position"
                values={selected.transform.position}
                disabled={selected.locked}
                gestureTargetId={selected.id}
                gestureCommandKind="object-transform"
                keyframedAxes={keyframedAxes}
                onToggleKeyframe={toggleKeyframeAtPlayhead}
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "position", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
              {/* Batch 581（源站实测 y=505 位于「位置」465 与「旋转」609
                  之间）：跟随目标选择器上提到变换组内、位置之后。跟随偏移 /
                  跟随视角仍留在下方摄像机分组（源站同屏未见，clone 保留）。 */}
              {selected.camera ? (
                <label className="block">
                  <FieldLabel>跟随目标</FieldLabel>
                  <select
                    data-director-camera-follow-target
                    value={selected.camera.followTargetId ?? ""}
                    disabled={selected.locked}
                    onChange={(event) =>
                      updateCamera(selected.id, {
                        followTargetId: event.currentTarget.value || null,
                      })
                    }
                    className={cn(FIELD_CONTROL, "min-w-0 disabled:opacity-45")}
                  >
                    <option value="">不跟随</option>
                    {cameraTargets.map((object) => (
                      <option key={object.id} value={object.id}>
                        {object.name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              <AxisFields
                label="旋转"
                field="rotation"
                values={selected.transform.rotation}
                disabled={selected.locked}
                disabledAxes={pathControlsRotationY ? [1] : []}
                gestureTargetId={selected.id}
                gestureCommandKind="object-transform"
                keyframedAxes={keyframedAxes}
                onToggleKeyframe={toggleKeyframeAtPlayhead}
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "rotation", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
              {pathControlsRotationY ? (
                <p
                  data-director-motion-path-rotation-hint
                  className="text-[10px] leading-4 text-[#7298a2]"
                >
                  已开启沿路径朝向，Y 轴旋转由运动轨迹控制
                </p>
              ) : null}
              <AxisFields
                label="缩放"
                field="scale"
                values={selected.transform.scale}
                disabled={selected.locked}
                gestureTargetId={selected.id}
                gestureCommandKind="object-transform"
                keyframedAxes={keyframedAxes}
                onToggleKeyframe={toggleKeyframeAtPlayhead}
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "scale", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
              {/* Batch 583（源站 2026-10-01 实测，角色A 属性页 y=409）：
                  缩放之后是「统一缩放」——range 0.1–10 step 0.05 + 一位小数
                  读数（实测 1.0），三轴同值同源。 */}
              <label className="flex items-center justify-between text-[11px] text-[#777]">
                <span>统一缩放</span>
                <span className="flex items-center gap-2">
                  <input
                    type="range"
                    min={0.1}
                    max={10}
                    step={0.05}
                    aria-label="统一缩放"
                    data-director-uniform-scale
                    value={selected.transform.scale[0]}
                    disabled={selected.locked}
                    onChange={(event) => {
                      const next = Number(event.target.value);
                      ([0, 1, 2] as const).forEach((axis) => {
                        updateObjectTransform(selected.id, "scale", axis, next);
                      });
                      recordObjectKeyframe(selected.id);
                    }}
                    className="w-24 accent-[#09caf5]"
                  />
                  <span
                    data-director-uniform-scale-readout
                    className="w-8 text-right text-[10px] tabular-nums text-[#8c8c8c]"
                  >
                    {selected.transform.scale[0].toFixed(1)}
                  </span>
                </span>
              </label>
              {/* Batch 583: 颜色行按源站行序（y=481，紧随统一缩放）从上方
                  按钮行移出。Batch 585: hex 改为源站的可编辑文本框。 */}
              <HexColorRow
                label="颜色"
                testId="object"
                value={selected.color}
                disabled={selected.locked}
                onCommit={(hex) => updateObject(selected.id, { color: hex })}
              />
            </div>

            {selected.camera ? (
              <div className="space-y-3 border-t border-white/[0.07] pt-4">
                {selectedShot ? (
                  <DirectorShotInspector
                    key={`${selectedShot.id}:${selectedShot.name}:${selectedShot.startTime}:${selectedShot.endTime}`}
                    shot={selectedShot}
                    duration={timeline.duration}
                  />
                ) : null}
                {/* Batch 581: FOV 控件已提到面板顶部（源站实测），此处保留
                    源站底部的说明块（y=816 `视野角度 (FOV)` + `?` 开关 +
                    文案），文案逐字取自源站。 */}
                {selected.camera ? (
                  <CameraFovField
                    objectId={selected.id}
                    fov={selected.camera.fov}
                    disabled={selected.locked}
                    fovKeyframed={cameraFovKeyframed}
                    onToggleKeyframe={toggleCameraFovKeyframe}
                    updateCamera={updateCamera}
                    recordObjectKeyframe={recordObjectKeyframe}
                  />
                ) : null}
                <label className="block">
                  <FieldLabel>注视目标</FieldLabel>
                  <select
                    data-director-camera-look-at-mode={
                      selected.camera.lookAtMode
                    }
                    data-director-camera-look-at-object={
                      selected.camera.lookAtObjectId ?? ""
                    }
                    value={
                      selected.camera.lookAtMode === "object" &&
                      selected.camera.lookAtObjectId
                        ? `object:${selected.camera.lookAtObjectId}`
                        : selected.camera.lookAtMode
                    }
                    disabled={selected.locked}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      if (value.startsWith("object:")) {
                        updateCamera(selected.id, {
                          lookAtMode: "object",
                          lookAtObjectId: value.slice("object:".length),
                        });
                        return;
                      }
                      updateCamera(selected.id, {
                        lookAtMode: value as Exclude<
                          DirectorCameraLookAtMode,
                          "object"
                        >,
                        lookAtObjectId: null,
                      });
                    }}
                    className={cn(FIELD_CONTROL, "min-w-0 disabled:opacity-45")}
                  >
                    <option value="coordinate">手动坐标</option>
                    <option value="rotation">手动旋转</option>
                    {cameraTargets.map((object) => (
                      <option key={object.id} value={`object:${object.id}`}>
                        {object.name}
                      </option>
                    ))}
                  </select>
                </label>

                {selected.camera.lookAtMode !== "rotation" ? (
                  <div
                    data-director-camera-target-coordinates
                    data-director-camera-target-derived={
                      selected.camera.lookAtMode === "object"
                    }
                  >
                    <AxisFields
                      label="注视坐标"
                      field="target"
                      values={selected.camera.target}
                      disabled={selected.locked}
                      disabledAxes={
                        selected.camera.lookAtMode === "object"
                          ? [0, 1, 2]
                          : []
                      }
                      onChange={(axis, value) => {
                        const target: DirectorTuple3 = [
                          ...selected.camera!.target,
                        ];
                        target[axis] = value;
                        updateCamera(selected.id, { target });
                        recordObjectKeyframe(selected.id);
                      }}
                      gestureTargetId={selected.id}
                      gestureCommandKind="camera-target"
                    />
                  </div>
                ) : (
                  <p className="text-[10px] leading-4 text-[#7298a2]">
                    使用上方旋转参数控制机位方向
                  </p>
                )}

                <span
                  data-director-camera-follow-state={
                    selected.camera.followTargetId ? "active" : "none"
                  }
                  data-follow-target-id={
                    selected.camera.followTargetId ?? ""
                  }
                  data-look-at-mode={selected.camera.lookAtMode}
                  data-follow-view={selected.camera.followView}
                  className="sr-only"
                />

                {selected.camera.followTargetId ? (
                  <>
                    <div data-director-camera-follow-offset>
                      <AxisFields
                        label="跟随偏移"
                        field="followOffset"
                        values={selected.camera.followOffset}
                        disabled={selected.locked}
                        gestureTargetId={selected.id}
                        gestureCommandKind="camera-follow-offset"
                        onChange={(axis, value) => {
                          const followOffset: DirectorTuple3 = [
                            ...selected.camera!.followOffset,
                          ];
                          followOffset[axis] = value;
                          updateCamera(selected.id, { followOffset });
                        }}
                      />
                    </div>
                    <fieldset className="border-0 p-0">
                      <legend className="mb-1.5 text-[11px] text-[#777]">
                        跟随视角
                      </legend>
                      <div
                        data-director-camera-follow-view
                        className="grid h-8 grid-cols-2 gap-1 rounded border border-white/[0.08] bg-[#1d1d1d] p-0.5"
                      >
                        {(
                          [
                            ["third-person", "第三人称"],
                            ["first-person", "第一人称"],
                          ] as const
                        ).map(([mode, label]) => (
                          <button
                            key={mode}
                            type="button"
                            data-director-camera-follow-view-option={mode}
                            aria-pressed={selected.camera!.followView === mode}
                            disabled={selected.locked}
                            onClick={() =>
                              updateCamera(selected.id, {
                                followView: mode,
                              })
                            }
                            className={cn(
                              "min-w-0 rounded text-[10px] text-[#858585] hover:text-white",
                              selected.camera!.followView === mode &&
                                "bg-[#303030] text-[#70def6]",
                            )}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </fieldset>
                    <p
                      data-director-camera-follow-conflict
                      className="rounded border border-[#d6a35a]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#caa66f]"
                    >
                      请先关闭机位跟随，再绘制轨迹
                    </p>
                  </>
                ) : null}
              </div>
            ) : null}

            {selectedPath ? (
              <MotionPathInspector path={selectedPath} />
            ) : null}
          </div>
          )
        ) : (
          <div data-director-scene-settings className="space-y-4 px-4 py-3">
            <section data-director-scene-settings-section>
            <section
              data-director-scene-transform
              className="space-y-2 border-b border-white/[0.07] pb-3"
            >
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>场景缩放</span>
                <span className="flex items-center gap-2">
                  <input
                    data-director-scene-scale
                    type="range"
                    min={0.1}
                    max={10}
                    step={0.1}
                    aria-label="场景缩放"
                    value={scene.sceneScale ?? 1}
                    onChange={(event) =>
                      updateScene({ sceneScale: Number(event.target.value) })
                    }
                    className="w-24 accent-[#09caf5]"
                  />
                  <NumericReadoutInput
                    testId="scale"
                    ariaLabel="场景缩放读数"
                    text={`${Math.round((scene.sceneScale ?? 1) * 100)}%`}
                    // 源站读数是百分比（值 3 -> `300%`），store 存的是倍数。
                    onCommit={(next) =>
                      updateScene({
                        sceneScale: Math.min(10, Math.max(0.1, next / 100)),
                      })
                    }
                  />
                </span>
              </label>
              <div className="space-y-1 text-xs text-[#bcbcbc]">
                <span className="block">场景平移</span>
                <div className="grid grid-cols-3 gap-1.5">
                  {(["X", "Y", "Z"] as const).map((axisLabel, axisIndex) => {
                    const translate = scene.sceneTranslate ?? [0, 0, 0];
                    const commit = (next: number) => {
                      const tuple = [...translate] as [number, number, number];
                      tuple[axisIndex] = next;
                      updateScene({ sceneTranslate: tuple });
                    };
                    return (
                      <div key={axisLabel} className="flex items-center gap-1">
                        <SceneAxisScrub
                          axis={axisLabel}
                          value={translate[axisIndex]}
                          step={0.1}
                          testId={`translate-${axisLabel}`}
                          onChange={commit}
                        />
                        <input
                          data-director-scene-translate={axisIndex}
                          type="number"
                          step={0.1}
                          aria-label={`场景平移 ${axisLabel}`}
                          value={translate[axisIndex]}
                          onChange={(event) =>
                            commit(Number(event.target.value))
                          }
                          className="h-7 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-1.5 text-[11px] text-[#dedede] outline-none focus:border-[#09caf5]/60"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="space-y-1 text-xs text-[#bcbcbc]">
                <span className="block">场景旋转</span>
                <div className="grid grid-cols-3 gap-1.5">
                  {(["X", "Y", "Z"] as const).map((axisLabel, axisIndex) => {
                    const rotate = scene.sceneRotate ?? [0, 0, 0];
                    const commit = (next: number) => {
                      const tuple = [...rotate] as [number, number, number];
                      tuple[axisIndex] = next;
                      updateScene({ sceneRotate: tuple });
                    };
                    return (
                      <div key={axisLabel} className="flex items-center gap-1">
                        <SceneAxisScrub
                          axis={axisLabel}
                          value={rotate[axisIndex]}
                          step={1}
                          testId={`rotate-${axisLabel}`}
                          onChange={commit}
                        />
                        <input
                          data-director-scene-rotate={axisIndex}
                          type="number"
                          step={1}
                          aria-label={`场景旋转 ${axisLabel}`}
                          value={rotate[axisIndex]}
                          onChange={(event) =>
                            commit(Number(event.target.value))
                          }
                          className="h-7 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-1.5 text-[11px] text-[#dedede] outline-none focus:border-[#09caf5]/60"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-[11px] font-medium text-[#cfcfcf]">
                  场景设置
                </h3>
                <span className="text-[9px] text-[#686868]">Scene</span>
              </div>
              <label className="block">
                <span className="mb-1.5 block text-[11px] text-[#777]">
                  场景名称
                </span>
                <input
                  ref={sceneNameInputRef}
                  data-director-scene-name
                  defaultValue={scene.name}
                  onBlur={(event) => {
                    const nextName = event.currentTarget.value.trim();
                    if (!nextName) {
                      event.currentTarget.value = scene.name;
                      updateScene({ name: "" });
                      return;
                    }
                    event.currentTarget.value = nextName;
                    updateScene({ name: nextName });
                  }}
                  onKeyDown={(event) => {
                    if (event.key !== "Enter") return;
                    event.preventDefault();
                    event.currentTarget.blur();
                  }}
                  className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
                />
              </label>
            </section>
            <section
              data-director-scene-display-settings
              className="space-y-1 border-t border-white/[0.07] pt-3"
            >
              <h3 className="text-[11px] font-medium text-[#cfcfcf]">
                显示
              </h3>
              <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
                <span>显示地面</span>
                <input
                  data-director-scene-show-ground
                  type="checkbox"
                  checked={scene.showGround}
                  onChange={(event) =>
                    updateScene({ showGround: event.target.checked })
                  }
                  className="accent-[#09caf5]"
                />
              </label>
              <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
                <span>显示网格</span>
                <input
                  data-director-scene-show-grid
                  type="checkbox"
                  checked={scene.showGrid}
                  onChange={(event) =>
                    updateScene({ showGrid: event.target.checked })
                  }
                  className="accent-[#09caf5]"
                />
              </label>
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>背景颜色</span>
                <input
                  data-director-scene-background-color
                  type="color"
                  aria-label="场景背景颜色"
                  value={scene.backgroundColor}
                  onChange={(event) =>
                    updateScene({ backgroundColor: event.target.value })
                  }
                  className="h-6 w-9 rounded border-0 bg-transparent"
                />
              </label>
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>地面颜色</span>
                <input
                  data-director-scene-ground-color
                  type="color"
                  aria-label="场景地面颜色"
                  value={scene.groundColor}
                  onChange={(event) =>
                    updateScene({ groundColor: event.target.value })
                  }
                  className="h-6 w-9 rounded border-0 bg-transparent"
                />
              </label>
              {/* Batch 582/585（源站实测 y=452/457）：天空颜色为
                  `#` + hex 文本框 + 取色器；582 先做成只读读数，本批
                  换成源站的可编辑文本框。 */}
              <HexColorRow
                label="天空颜色"
                testId="sky"
                value={scene.skyColor ?? "#060608"}
                disabled={false}
                onCommit={(hex) => updateScene({ skyColor: hex })}
              />
              <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
                <span>全景球 水平旋转</span>
                <span className="flex items-center gap-2">
                  <input
                    data-director-scene-panorama-rotation
                    type="range"
                    min={0}
                    max={360}
                    step={1}
                    aria-label="全景球水平旋转"
                    value={scene.panoramaRotation ?? 0}
                    onChange={(event) =>
                      updateScene({
                        panoramaRotation: Number(event.target.value),
                      })
                    }
                    className="w-24 accent-[#09caf5]"
                  />
                  <NumericReadoutInput
                    testId="panorama-rotation"
                    ariaLabel="全景球水平旋转读数"
                    text={`${scene.panoramaRotation ?? 0}°`}
                    onCommit={(next) =>
                      updateScene({
                        panoramaRotation: Math.min(360, Math.max(0, next)),
                      })
                    }
                  />
                </span>
              </label>
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>全景球 球形半径</span>
                <span className="flex items-center gap-2">
                  <input
                    data-director-scene-panorama-radius
                    type="range"
                    min={10}
                    max={500}
                    step={10}
                    aria-label="全景球球形半径"
                    value={scene.panoramaSphereRadius ?? 30}
                    onChange={(event) =>
                      updateScene({
                        panoramaSphereRadius: Number(event.target.value),
                      })
                    }
                    className="w-24 accent-[#09caf5]"
                  />
                  <NumericReadoutInput
                    testId="sphere-radius"
                    ariaLabel="全景球球形半径读数"
                    text={`${scene.panoramaSphereRadius ?? 30}`}
                    onCommit={(next) =>
                      updateScene({
                        panoramaSphereRadius: Math.min(500, Math.max(10, next)),
                      })
                    }
                  />
                </span>
              </label>
              <SceneToggleRow
                label="角色标签"
                testId="character-labels"
                dataAttr="data-director-scene-character-labels"
                checked={scene.showCharacterLabels ?? true}
                onToggle={(next) => updateScene({ showCharacterLabels: next })}
              />
              <SceneToggleRow
                label="网格吸附"
                testId="snap-to-grid"
                dataAttr="data-director-scene-snap-to-grid"
                checked={scene.snapToGrid ?? false}
                onToggle={(next) => updateScene({ snapToGrid: next })}
              />
              <SceneToggleRow
                label="高斯地面吸附"
                testId="gaussian-snap"
                dataAttr="data-director-scene-gaussian-snap"
                checked={scene.gaussianGroundSnap ?? true}
                onToggle={(next) => updateScene({ gaussianGroundSnap: next })}
              />
              {/* Batch 582（源站实测 y 序：透明度 920 在前、高度 992 在后，
                  且透明度带 `0.40` 两位小数读数、高度步进 0.05）：顺序与
                  读数对齐源站。 */}
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>地面透明度</span>
                <span className="flex items-center gap-2">
                  <input
                    data-director-scene-ground-opacity
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    aria-label="地面透明度"
                    value={scene.groundOpacity ?? 0.4}
                    onChange={(event) =>
                      updateScene({
                        groundOpacity: Number(event.target.value),
                      })
                    }
                    className="w-24 accent-[#09caf5]"
                  />
                  <NumericReadoutInput
                    testId="ground-opacity"
                    ariaLabel="地面透明度读数"
                    width="w-[62px]"
                    text={(scene.groundOpacity ?? 0.4).toFixed(2)}
                    onCommit={(next) =>
                      updateScene({
                        groundOpacity: Math.min(1, Math.max(0, next)),
                      })
                    }
                  />
                </span>
              </label>
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>地面高度</span>
                <span className="flex items-center gap-2">
                  <input
                    data-director-scene-ground-height
                    type="range"
                    min={-2}
                    max={2}
                    step={0.05}
                    aria-label="地面高度"
                    value={scene.groundHeight ?? 0}
                    onChange={(event) =>
                      updateScene({ groundHeight: Number(event.target.value) })
                    }
                    className="w-24 accent-[#09caf5]"
                  />
                  <NumericReadoutInput
                    testId="ground-height"
                    ariaLabel="地面高度读数"
                    width="w-[62px]"
                    text={(scene.groundHeight ?? 0).toFixed(1)}
                    onCommit={(next) =>
                      updateScene({
                        groundHeight: Math.min(2, Math.max(-2, next)),
                      })
                    }
                  />
                </span>
              </label>
            </section>
            <section
              data-director-panorama-input
              className="space-y-2 border-t border-white/[0.07] pt-3"
            >
              {/* Batch 561: 源站截图 45/48——全景背景区：已连接全景图 状态
                  与「请将图片节点连接到导演台左侧输入口」提示框。 */}
              <h3 className="text-[11px] font-medium text-[#cfcfcf]">
                全景背景
              </h3>
              {panoramaRuntimeState === "ready" && (
                <p
                  data-director-panorama-connected
                  className="text-[10px] text-[#9ddbb9]"
                >
                  已连接全景图
                </p>
              )}
              {panoramaInputs.length === 0 && (
                <div
                  data-director-panorama-hint
                  className="flex items-center gap-1.5 rounded-lg border border-dashed border-white/[0.12] px-3 py-2.5 text-[10px] leading-4 text-[#686868]"
                >
                  <span
                    className={cn(
                      "flex size-3.5 shrink-0 items-center justify-center rounded-full border border-current text-[8px]",
                    )}
                  >
                    !
                  </span>
                  请将图片节点连接到导演台左侧输入口
                </div>
              )}
              <div className="flex items-center justify-between">
                <h3 className="text-[11px] font-medium text-[#cfcfcf]">
                  画布环境
                </h3>
                <span className="text-[9px] text-[#686868]">Session</span>
              </div>
              <p className="text-[10px] leading-4 text-[#686868]">
                使用当前导演台节点的直接上游图片作为临时全景参考。
              </p>
              <select
                data-director-panorama-source
                aria-label="画布环境图片"
                value={selectedPanoramaSourceId ?? ""}
                onChange={(event) =>
                  onPanoramaSourceChange(event.currentTarget.value || null)
                }
                className="h-8 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#d2d2d2] outline-none focus:border-[#09caf5]/60"
              >
                <option value="">不使用画布图片</option>
                {panoramaInputs.map((input) => (
                  <option
                    key={input.sourceNodeId}
                    value={input.sourceNodeId}
                    data-director-panorama-source-option={input.sourceNodeId}
                  >
                    {input.filename}
                    {input.sourceKind === "panorama" ? " · 全景" : " · 图片"}
                  </option>
                ))}
              </select>
              <div
                data-director-panorama-selection
                data-director-panorama-source-id={selectedPanoramaSourceId ?? ""}
                className="flex min-h-7 items-center gap-2 text-[10px] text-[#777]"
              >
                <Images size={13} className="shrink-0 text-[#5ddcff]" />
                <span className="min-w-0 flex-1 truncate">
                  {selectedPanoramaSourceId
                    ? panoramaInputs.find(
                        (input) =>
                          input.sourceNodeId === selectedPanoramaSourceId,
                      )?.filename ?? "输入已失效"
                    : panoramaInputs.length > 0
                      ? "未选择环境图片"
                      : "没有可用的直接上游图片"}
                </span>
                {selectedPanoramaSourceId ? (
                  <button
                    type="button"
                    data-director-panorama-clear
                    aria-label="清除画布环境图片"
                    title="清除环境图片"
                    onClick={() => onPanoramaSourceChange(null)}
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-white"
                  >
                    <X size={13} />
                  </button>
                ) : null}
              </div>
              <div
                data-director-panorama-status
                data-director-panorama-state={panoramaRuntimeState}
                className={cn(
                  "flex items-center gap-1.5 text-[10px]",
                  panoramaRuntimeState === "error"
                    ? "text-[#ef9292]"
                    : panoramaRuntimeState === "ready"
                      ? "text-[#9ddbb9]"
                      : "text-[#777]",
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    panoramaRuntimeState === "error"
                      ? "bg-[#d76767]"
                      : panoramaRuntimeState === "ready"
                        ? "bg-[#70c99a]"
                        : panoramaRuntimeState === "loading"
                          ? "animate-pulse bg-[#09caf5]"
                          : "bg-[#555]",
                  )}
                />
                <span>
                  {panoramaRuntimeState === "ready"
                    ? "环境预览已加载"
                    : panoramaRuntimeState === "loading"
                      ? "正在加载环境预览"
                      : panoramaRuntimeState === "error"
                        ? "环境图片加载失败，其他场景对象仍可用"
                        : "未设置环境预览"}
                </span>
              </div>
            </section>
            <section
              data-director-scene-camera-actions
              className="border-t border-white/[0.07] pt-3"
            >
              <div className="mb-2">
                <h3 className="text-[11px] font-medium text-[#cfcfcf]">
                  场景机位
                </h3>
                <p className="mt-1 text-[10px] leading-4 text-[#686868]">
                  从当前活动机位复制构图，创建一个可独立编辑的新机位
                </p>
              </div>
              <button
                type="button"
                data-director-add-camera
                onClick={addDirectorCamera}
                className="flex h-8 w-full items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-[11px] text-[#bdbdbd] hover:border-[#09caf5]/40 hover:text-white"
              >
                <Camera size={13} />
                新增机位
              </button>
            </section>
          </div>
        )}
      </div>

      {activeCapture &&
      !(selected?.kind === "camera" && cameraTab === "captures") ? (
        <CapturePreview capture={activeCapture} onSend={onSendCapture} />
      ) : null}
    </section>
  );
}
