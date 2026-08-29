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
import {
  useDirectorStore,
  type DirectorCameraLookAtMode,
  type DirectorCapture,
  type DirectorCharacterGroup,
  type DirectorMotionPath,
  type DirectorMotionPathAnchor,
  type DirectorMotionPathHandle,
  type DirectorObject,
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
}: {
  label: string;
  field: keyof DirectorTransform | "target" | "followOffset";
  values: DirectorTuple3;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
  disabledAxes?: Array<0 | 1 | 2>;
  disabled?: boolean;
  gestureTargetId?: string | null;
  gestureCommandKind?: string;
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
): string {
  return `${capture.cameraName}-截图${String(index + 1).padStart(2, "0")}`;
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
  const selectCapture = useDirectorStore((state) => state.selectCapture);
  const removeCapture = useDirectorStore((state) => state.removeCapture);
  const clearCaptures = useDirectorStore((state) => state.clearCaptures);
  const [viewerCaptureId, setViewerCaptureId] = useState<string | null>(null);
  const [viewerScale, setViewerScale] = useState(1);
  const [confirmClear, setConfirmClear] = useState(false);
  const viewerCapture =
    captures.find((capture) => capture.id === viewerCaptureId) ?? null;
  const cameraGroups = useMemo(() => {
    const groups = new Map<string, DirectorCapture[]>();
    captures.forEach((capture) => {
      const group = groups.get(capture.cameraName) ?? [];
      group.push(capture);
      groups.set(capture.cameraName, group);
    });
    return Array.from(groups.entries()).map(([cameraName, groupCaptures]) => {
      const chronological = [...groupCaptures].sort((left, right) =>
        left.createdAt.localeCompare(right.createdAt),
      );
      return {
        cameraName,
        captures: groupCaptures,
        labels: new Map(
          chronological.map((capture, index) => [
            capture.id,
            formatCaptureLabel(capture, index),
          ]),
        ),
      };
    });
  }, [captures]);

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
        {cameraGroups.length === 0 ? (
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
            {cameraGroups.map(({ cameraName, captures: groupCaptures, labels }) => (
              <section
                key={cameraName}
                data-director-capture-group={cameraName}
                aria-label={`${cameraName}截图`}
              >
                <h3 className="mb-2 text-[11px] text-[#bdbdbd]">
                  {cameraName}截图
                </h3>
                <div
                  className="grid grid-cols-3 gap-2"
                  aria-label={`${cameraName}截图列表`}
                >
                  {groupCaptures.map((capture) => {
                    const label = labels.get(capture.id) ?? `${cameraName}截图`;
                    const selected = activeCaptureId === capture.id;
                    return (
                      <article
                        key={capture.id}
                        data-director-capture-item={capture.id}
                        data-director-capture-item-selected={selected}
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
            ))}
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
    <label className="block">
      <span className="mb-1.5 flex items-center gap-1 text-[11px] text-[#777]">
        <Camera size={12} />
        视场角
      </span>
      <input
        type="range"
        min="20"
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
      <div className="mt-1 text-right text-[11px] tabular-nums text-[#a7a7a7]">
        {fov}°
      </div>
    </label>
  );
}

export function DirectorInspector({
  activeCapture,
  onSendCapture,
  onSendAllCaptures,
}: {
  activeCapture: DirectorCapture | null;
  onSendCapture: (capture: DirectorCapture) => void;
  onSendAllCaptures: () => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
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
  const [cameraTab, setCameraTab] = useState<"properties" | "captures">(
    "properties",
  );
  const timeline = useDirectorStore((state) => state.timeline);
  const selectedGroup =
    groups.find((group) => group.id === selectedGroupId) ?? null;
  const selected = objects.find((object) => object.id === selectedObjectId) ?? null;
  useEffect(() => {
    const input = sceneNameInputRef.current;
    if (input && document.activeElement !== input) input.value = scene.name;
  }, [scene.name]);
  useEffect(() => {
    const input = objectNameInputRef.current;
    if (input && document.activeElement !== input && selected) {
      input.value = selected.name;
    }
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
          className="grid h-9 shrink-0 grid-cols-2 border-b border-white/[0.07] bg-[#171717] p-1"
        >
          {(
            [
              ["properties", "属性"],
              ["captures", "摄像机截图"],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              data-director-camera-tab={tab}
              aria-pressed={cameraTab === tab}
              onClick={() => setCameraTab(tab)}
              className={cn(
                "rounded text-[11px] text-[#777] hover:text-white",
                cameraTab === tab && "bg-[#292929] text-[#d9d9d9]",
              )}
            >
              {label}
            </button>
          ))}
        </nav>
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto">
        {selectedGroup ? null : selected ? (
          selected.kind === "camera" && cameraTab === "captures" ? (
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
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "position", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
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
                <CameraFovField
                  objectId={selected.id}
                  fov={selected.camera.fov}
                  disabled={selected.locked}
                  updateCamera={updateCamera}
                  recordObjectKeyframe={recordObjectKeyframe}
                />
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
