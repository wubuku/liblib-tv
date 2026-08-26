"use client";

import Image from "next/image";
import { useState } from "react";
import {
  Camera,
  Check,
  ChevronDown,
  Eye,
  EyeOff,
  Plus,
  RotateCcw,
  Route,
  Send,
  Trash2,
  Users,
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
}: {
  label: string;
  field: keyof DirectorTransform | "target" | "followOffset";
  values: DirectorTuple3;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
  disabledAxes?: Array<0 | 1 | 2>;
}) {
  return (
    <fieldset className="border-0 p-0">
      <legend className="mb-1.5 text-[11px] text-[#777]">{label}</legend>
      <div className="grid grid-cols-3 gap-1.5">
        {values.map((value, index) => (
          <label
            key={axisLabels[index]}
            className={`flex h-8 min-w-0 items-center rounded border border-white/[0.08] bg-[#222] px-1.5 focus-within:border-[#09caf5]/60 ${
              disabledAxes.includes(index as 0 | 1 | 2) ? "opacity-45" : ""
            }`}
          >
            <span className="mr-1 text-[10px] text-[#666]">{axisLabels[index]}</span>
            <input
              type="number"
              step={field === "rotation" ? 1 : 0.1}
              data-director-transform-field={field}
              data-director-transform-axis={axisLabels[index].toLowerCase()}
              value={Number(value.toFixed(2))}
              disabled={disabledAxes.includes(index as 0 | 1 | 2)}
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
      <label className="block">
        <span className="mb-1.5 block text-[11px] text-[#777]">名称</span>
        <input
          data-director-group-name
          value={group.label}
          onChange={(event) =>
            updateGroup(group.id, { label: event.target.value })
          }
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
  onChange,
}: {
  label: string;
  values: DirectorTuple3;
  kind: "position" | "handle";
  handle?: DirectorMotionPathHandle;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
}) {
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
  onChange,
}: {
  label: string;
  field: keyof DirectorTransform;
  values: DirectorTuple3;
  onChange: (axis: 0 | 1 | 2, value: number) => void;
}) {
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
      className="space-y-3 border-t border-white/[0.07] pt-4"
    >
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
            onChange={() => toggleMotionPathEnabled(path.id)}
            className="accent-[#09caf5]"
          />
        </label>
        <button
          type="button"
          data-director-toggle-path-closed
          aria-pressed={path.closed}
          disabled={!path.closed && path.anchors.length < 3}
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
          onChange={(axis, value) =>
            updateMotionPathTransform(path.id, "scale", axis, value)
          }
        />
        <div className="grid grid-cols-2 gap-1.5">
          <button
            type="button"
            data-director-path-reset-offset
            onClick={() => resetMotionPathOffset(path.id)}
            className="flex h-8 items-center justify-center gap-1 rounded border border-white/[0.08] bg-[#222] text-[11px] text-[#a7a7a7] hover:text-white"
          >
            <RotateCcw size={12} />
            重置偏移
          </button>
          <button
            type="button"
            data-director-path-reset
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
              disabled={path.anchors.length <= 2}
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
            const value = controls[control.key] ?? 0;
            return (
              <label
                key={control.key}
                className="grid grid-cols-[minmax(0,1fr)_42px] items-center gap-x-2 gap-y-1"
              >
                <span className="truncate text-[10px] text-[#8b8b8b]">
                  {control.label}
                </span>
                <output className="text-right text-[10px] tabular-nums text-[#b8b8b8]">
                  {control.unit === "meter"
                    ? value.toFixed(2)
                    : `${Math.round(value)}°`}
                </output>
                <input
                  type="range"
                  min={control.min}
                  max={control.max}
                  step={control.step}
                  value={value}
                  aria-label={`${group.label} ${control.label}`}
                  data-director-pose-control={control.key}
                  onChange={(event) =>
                    updateCharacterPoseControl(
                      character.id,
                      control.key,
                      Number(event.currentTarget.value),
                    )
                  }
                  className="col-span-2 w-full accent-[#09caf5]"
                />
              </label>
            );
          })}
        </div>
      ) : null}
    </section>
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

export function DirectorInspector({
  activeCapture,
  onSendCapture,
}: {
  activeCapture: DirectorCapture | null;
  onSendCapture: (capture: DirectorCapture) => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const updateScene = useDirectorStore((state) => state.updateScene);
  const updateObject = useDirectorStore((state) => state.updateObject);
  const updateObjectTransform = useDirectorStore(
    (state) => state.updateObjectTransform,
  );
  const updateCamera = useDirectorStore((state) => state.updateCamera);
  const recordObjectKeyframe = useDirectorStore(
    (state) => state.recordObjectKeyframe,
  );
  const [poseObjectId, setPoseObjectId] = useState<string | null>(null);
  const timeline = useDirectorStore((state) => state.timeline);
  const selectedGroup =
    groups.find((group) => group.id === selectedGroupId) ?? null;
  const selected = objects.find((object) => object.id === selectedObjectId) ?? null;
  const selectedTrack = timeline.tracks.find(
    (track) =>
      selectedGroup
        ? track.kind === "group" && track.groupId === selectedGroup.id
        : track.objectId === selected?.id && track.kind !== "pose",
  );
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
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto">
        {selectedGroup ? null : selected ? (
          selected.kind === "character" && characterTab === "pose" ? (
            <CharacterPoseInspector character={selected} />
          ) : (
          <div className="space-y-4 px-3 py-3">
            <label className="block">
              <span className="mb-1.5 block text-[11px] text-[#777]">名称</span>
              <input
                value={selected.name}
                onChange={(event) =>
                  updateObject(selected.id, { name: event.target.value })
                }
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
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "position", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
              <AxisFields
                label="旋转"
                field="rotation"
                values={selected.transform.rotation}
                disabledAxes={pathControlsRotationY ? [1] : []}
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
                onChange={(axis, value) => {
                  updateObjectTransform(selected.id, "scale", axis, value);
                  recordObjectKeyframe(selected.id);
                }}
              />
            </div>

            {selected.camera ? (
              <div className="space-y-3 border-t border-white/[0.07] pt-4">
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
                    value={selected.camera.fov}
                    onChange={(event) => {
                      updateCamera(selected.id, {
                        fov: Number(event.target.value),
                      });
                      recordObjectKeyframe(selected.id);
                    }}
                    className="w-full accent-[#09caf5]"
                  />
                  <div className="mt-1 text-right text-[11px] tabular-nums text-[#a7a7a7]">
                    {selected.camera.fov}°
                  </div>
                </label>
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
          <div className="space-y-4 px-3 py-3">
            <label className="block">
              <span className="mb-1.5 block text-[11px] text-[#777]">场景名称</span>
              <input
                value={scene.name}
                onChange={(event) => updateScene({ name: event.target.value })}
                className="h-8 w-full rounded border border-white/[0.08] bg-[#222] px-2 text-xs text-[#dedede] outline-none focus:border-[#09caf5]/60"
              />
            </label>
            <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
              <span>显示地面</span>
              <input
                type="checkbox"
                checked={scene.showGround}
                onChange={(event) => updateScene({ showGround: event.target.checked })}
                className="accent-[#09caf5]"
              />
            </label>
            <label className="flex h-9 items-center justify-between border-b border-white/[0.06] text-xs text-[#bcbcbc]">
              <span>显示网格</span>
              <input
                type="checkbox"
                checked={scene.showGrid}
                onChange={(event) => updateScene({ showGrid: event.target.checked })}
                className="accent-[#09caf5]"
              />
            </label>
            <label className="flex h-9 items-center justify-between text-xs text-[#bcbcbc]">
              <span>背景颜色</span>
              <input
                type="color"
                aria-label="场景背景颜色"
                value={scene.backgroundColor}
                onChange={(event) =>
                  updateScene({ backgroundColor: event.target.value })
                }
                className="h-6 w-9 rounded border-0 bg-transparent"
              />
            </label>
          </div>
        )}
      </div>

      {activeCapture ? (
        <CapturePreview capture={activeCapture} onSend={onSendCapture} />
      ) : null}
    </section>
  );
}
