"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Camera,
  Check,
  ChevronDown,
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
  type DirectorPoseControlGroup,
} from "@/components/director/directorPose";
import { getDirectorGroupAnchorTransform } from "@/components/director/directorGroupMath";
import { useDirectorGestureBoundary } from "@/components/director/useDirectorGestureBoundary";
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
}) {
  const gesture = useDirectorGestureBoundary({
    commandKind: gestureCommandKind,
    targetId: gestureTargetId,
    fieldScope: field,
  });
  const isAxisDisabled = (index: number) =>
    disabled || disabledAxes.includes(index as 0 | 1 | 2);
  return (
    <fieldset className="border-0 p-0">
      <legend className="mb-1.5 text-[11px] text-[#777]">{label}</legend>
      <div className="grid grid-cols-3 gap-1.5">
        {values.map((value, index) => (
          <label
            key={axisLabels[index]}
            className={`flex h-8 min-w-0 items-center rounded border border-white/[0.08] bg-[#222] px-1.5 focus-within:border-[#09caf5]/60 ${
              isAxisDisabled(index) ? "opacity-45" : ""
            }`}
          >
            <span className="mr-1 text-[10px] text-[#666]">{axisLabels[index]}</span>
            {keyframedAxes.includes(index as 0 | 1 | 2) ? (
              /* Batch 575: 源站截图 60——该轴存在关键帧时输入右侧的青色菱形标记 */
              <span
                data-director-keyframed-axis={field}
                data-director-keyframed-axis-index={index}
                aria-label={`${axisLabels[index]} 轴已有关键帧`}
                className="mr-0.5 size-1.5 shrink-0 rotate-45 rounded-[1px] bg-[#09caf5]"
              />
            ) : null}
            <input
              type="number"
              step={field === "rotation" ? 1 : 0.1}
              data-director-transform-field={field}
              data-director-transform-axis={axisLabels[index].toLowerCase()}
              value={Number(value.toFixed(2))}
              disabled={isAxisDisabled(index)}
              {...(isAxisDisabled(index) ? {} : gesture)}
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
      className="space-y-4 px-3 py-3"
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
  const [expanded, setExpanded] = useState(
    group.id === "body" || group.id === "head-neck",
  );
  const updateCharacterPoseControl = useDirectorStore(
    (state) => state.updateCharacterPoseControl,
  );
  const controls =
    character.characterRig?.controls ?? createDirectorCharacterRig().controls;

  return (
    <section
      data-director-pose-group={group.id}
      className="border-t border-white/[0.06]"
    >
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
        className="flex min-h-10 w-full items-center gap-2 py-2 text-left"
      >
        <span className="text-[11px] font-medium text-[#c8c8c8]">
          {group.label}
        </span>
        <span className="min-w-0 flex-1 truncate text-[9px] text-[#626262]">
          {group.bones.join(" / ")}
        </span>
        <ChevronDown
          size={12}
          className={cn(
            "shrink-0 text-[#666] transition-transform",
            expanded && "rotate-180",
          )}
        />
      </button>
      {expanded ? (
        <div className="space-y-2 pb-3">
          {group.controls.map((control) => {
            return (
              <PoseControl
                key={control.key}
                characterId={character.id}
                groupLabel={group.label}
                control={control}
                value={controls[control.key] ?? 0}
                disabled={character.locked}
                updateCharacterPoseControl={updateCharacterPoseControl}
              />
            );
          })}
        </div>
      ) : null}
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
  control: DirectorPoseControlGroup["controls"][number];
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

  return (
    <label className="grid grid-cols-[minmax(0,1fr)_42px] items-center gap-x-2 gap-y-1">
      <span className="truncate text-[10px] text-[#8b8b8b]">
        {control.label}
      </span>
      <output className="text-right text-[10px] tabular-nums text-[#b8b8b8]">
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
      className="space-y-4 px-3 py-3"
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

function CameraFovField({
  objectId,
  fov,
  disabled,
  updateCamera,
  recordObjectKeyframe,
}: {
  objectId: string;
  fov: number;
  disabled: boolean;
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

  return (
    // Batch 581（源站 2026-10-01 CDP 实测）：FOV 行紧贴页签栏下方（y=134），
    // 早于「名称」（y=289），形态为 `FOV 50°` 单行——标签与度数读数同行、
    // 滑杆在下。原生 range 属性实测 min=15 / max=90 / step=1（此前 clone
    // 写死 min=20，量程比源站窄）。
    <div className="block" data-director-camera-fov-field>
      <div className="mb-1.5 flex items-center justify-between text-[11px] text-[#777]">
        <span className="flex items-center gap-1">
          <Camera size={12} />
          FOV
        </span>
        <span
          data-director-camera-fov-readout
          className="tabular-nums text-[#a7a7a7]"
        >
          {fov}°
        </span>
      </div>
      <input
        type="range"
        min="15"
        max="90"
        step="1"
        data-director-camera-fov
        value={fov}
        disabled={disabled}
        {...(disabled ? {} : gesture)}
        onChange={(event) => {
          updateCamera(objectId, {
            fov: Number(event.target.value),
          });
          recordObjectKeyframe(objectId);
        }}
        className="w-full accent-[#09caf5]"
      />
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
}: {
  axis: string;
  value: number;
  step: number;
  onChange: (next: number) => void;
  testId: string;
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
      className="h-7 w-6 shrink-0 cursor-ew-resize select-none rounded border border-white/[0.08] bg-[#222] text-[10px] font-medium uppercase text-[#8c8c8c] hover:border-[#09caf5]/40 hover:text-white"
    >
      {axis}
    </button>
  );
}

function CameraFovHelp() {
  // Batch 582: 源站实测该说明**默认展开**（innerText 直接含文案，? 开关在
  // 其前），此前 clone 默认收起，现对齐为默认展开。
  const [open, setOpen] = useState(true);
  return (
    <div
      data-director-camera-fov-help
      data-open={open ? "true" : "false"}
      className="space-y-1.5"
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] text-[#777]">视野角度 (FOV)</span>
        <button
          type="button"
          aria-label="视野角度说明"
          aria-expanded={open}
          data-director-camera-fov-help-toggle
          onClick={() => setOpen((value) => !value)}
          className="grid h-3.5 w-3.5 place-items-center rounded-full border border-white/20 text-[8px] leading-none text-[#8c8c8c] hover:border-white/40 hover:text-white"
        >
          ?
        </button>
      </div>
      {open ? (
        <p className="text-[10px] leading-4 text-[#6f6f6f]">
          控制镜头视野范围。数值越小，画面越近、越聚焦；数值越大，画面越广、能看到更多环境。
        </p>
      ) : null}
    </div>
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
        // keyframe.value 即 DirectorTransform。
        const values = (keyframe.value as unknown as Record<string, unknown>)
          ?.transform as unknown as Record<string, unknown> | undefined;
        return (
          Math.abs(keyframe.time - timeline.currentTime) < 0.001 &&
          Array.isArray(values?.[field])
        );
      });
      if (hasKey) axes.push(fieldIndex as 0 | 1 | 2);
    });
    return axes;
  }, [selected, timeline]);
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
          className="grid h-9 shrink-0 grid-cols-2 border-b border-white/[0.07] bg-[#171717] p-1"
        >
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
                "rounded text-[11px] text-[#777] hover:text-white",
                characterTab === tab &&
                  "bg-[#292929] text-[#d9d9d9]",
              )}
            >
              {label}
            </button>
          ))}
        </nav>
      ) : selected?.kind === "camera" ? (
        <nav
          data-director-camera-tabs
          aria-label="摄像机编辑"
          // Batch 581: 三个页签（属性 / 运动轨迹 / 截图）此前挤在
          // grid-cols-2 里，第三个换行导致页签栏占两行（实测 属性 y=136 /
          // 截图 y=153）。源站页签为单行等宽胶囊，按页签数分列。
          className="grid h-9 shrink-0 grid-cols-3 border-b border-white/[0.07] bg-[#171717] p-1"
        >
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
              className={cn(
                "relative rounded text-[11px] text-[#777] hover:text-white",
                cameraTab === tab && "bg-[#292929] text-[#d9d9d9]",
              )}
            >
              {label}
              {tab === "motion" ? (
                <span
                  data-director-camera-motion-new
                  className="absolute -top-2 right-0 rounded-full bg-[#09caf5] px-1 text-[8px] font-medium text-[#0d2c33]"
                >
                  NEW
                </span>
              ) : null}
            </button>
          ))}
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
          <div className="space-y-4 px-3 py-3">
            {selected.locked ? (
              <p
                data-director-locked-hint
                className="flex items-center gap-1.5 rounded border border-[#f0c776]/20 bg-[#7b5521]/10 px-2 py-1.5 text-[10px] leading-4 text-[#d5b879]"
              >
                <Lock size={12} aria-hidden="true" />
                对象已锁定，属性与变换编辑已停用
              </p>
            ) : null}
            {/* Batch 581（源站实测 y=134，紧贴页签栏下方、早于「名称」
                y=289）：FOV 行提到面板顶部。摄像机属性页才有。 */}
            {selected.camera ? (
              <CameraFovField
                objectId={selected.id}
                fov={selected.camera.fov}
                disabled={selected.locked}
                updateCamera={updateCamera}
                recordObjectKeyframe={recordObjectKeyframe}
              />
            ) : null}
            <label className="block">
              <span className="mb-1.5 block text-[11px] text-[#777]">名称</span>
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
                className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
              />
            </label>

            {selected.kind === "camera" ? (
              <label className="mt-3 block">
                <span className="mb-1.5 block text-[11px] text-[#777]">切换机位</span>
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
                  className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
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
              <label className="relative flex h-8 flex-1 items-center gap-2 rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#bdbdbd]">
                <span
                  className="h-4 w-4 rounded-sm border border-white/20"
                  style={{ backgroundColor: selected.color }}
                />
                <span>颜色</span>
                <input
                  type="color"
                  aria-label="对象颜色"
                  value={selected.color}
                  disabled={selected.locked}
                  onChange={(event) =>
                    updateObject(selected.id, { color: event.target.value })
                  }
                  className="absolute h-0 w-0 opacity-0"
                />
              </label>
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
                  <span className="mb-1.5 block text-[11px] text-[#777]">
                    跟随目标
                  </span>
                  <select
                    data-director-camera-follow-target
                    value={selected.camera.followTargetId ?? ""}
                    disabled={selected.locked}
                    onChange={(event) =>
                      updateCamera(selected.id, {
                        followTargetId: event.currentTarget.value || null,
                      })
                    }
                    className="h-8 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#d2d2d2] outline-none focus:border-[#09caf5]/60"
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
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "scale", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
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
                <CameraFovHelp />
                <label className="block">
                  <span className="mb-1.5 block text-[11px] text-[#777]">
                    注视目标
                  </span>
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
                    className="h-8 w-full min-w-0 rounded border border-white/[0.08] bg-[#222] px-2 text-[11px] text-[#d2d2d2] outline-none focus:border-[#09caf5]/60"
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
          <div data-director-scene-settings className="space-y-4 px-3 py-3">
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
                  <span className="w-10 text-right text-[10px] tabular-nums text-[#8c8c8c]">
                    {Math.round((scene.sceneScale ?? 1) * 100)}%
                  </span>
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
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>天空颜色</span>
                {/* Batch 582（源站实测 y=452/457）：源站天空颜色除取色器外
                    还有 hex 文本框 + `#` 前缀读数。 */}
                <span className="flex items-center gap-1.5">
                  <span className="text-[10px] tabular-nums text-[#8c8c8c]">
                    #{(scene.skyColor ?? "#060608").replace("#", "")}
                  </span>
                  <input
                    data-director-scene-sky-color
                    type="color"
                    aria-label="天空颜色"
                    value={scene.skyColor ?? "#060608"}
                    onChange={(event) =>
                      updateScene({ skyColor: event.target.value })
                    }
                    className="h-6 w-9 rounded border-0 bg-transparent"
                  />
                </span>
              </label>
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
                  <span className="w-8 text-right text-[10px] tabular-nums text-[#8c8c8c]">
                    {scene.panoramaRotation ?? 0}°
                  </span>
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
                  <span className="w-8 text-right text-[10px] tabular-nums text-[#8c8c8c]">
                    {scene.panoramaSphereRadius ?? 30}
                  </span>
                </span>
              </label>
              <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
                <span>角色标签</span>
                <input
                  data-director-scene-character-labels
                  type="checkbox"
                  checked={scene.showCharacterLabels ?? true}
                  onChange={(event) =>
                    updateScene({ showCharacterLabels: event.target.checked })
                  }
                  className="accent-[#09caf5]"
                />
              </label>
              <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
                <span>网格吸附</span>
                <input
                  data-director-scene-snap-to-grid
                  type="checkbox"
                  checked={scene.snapToGrid ?? false}
                  onChange={(event) =>
                    updateScene({ snapToGrid: event.target.checked })
                  }
                  className="accent-[#09caf5]"
                />
              </label>
              <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
                <span>高斯地面吸附</span>
                <input
                  data-director-scene-gaussian-snap
                  type="checkbox"
                  checked={scene.gaussianGroundSnap ?? true}
                  onChange={(event) =>
                    updateScene({ gaussianGroundSnap: event.target.checked })
                  }
                  className="accent-[#09caf5]"
                />
              </label>
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
                  <span className="w-8 text-right text-[10px] tabular-nums text-[#8c8c8c]">
                    {(scene.groundOpacity ?? 0.4).toFixed(2)}
                  </span>
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
                  <span className="w-8 text-right text-[10px] tabular-nums text-[#8c8c8c]">
                    {(scene.groundHeight ?? 0).toFixed(1)}
                  </span>
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
