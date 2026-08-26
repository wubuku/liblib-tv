"use client";

import Image from "next/image";
import {
  Camera,
  Check,
  Eye,
  EyeOff,
  Plus,
  RotateCcw,
  Route,
  Send,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorCapture,
  type DirectorMotionPath,
  type DirectorMotionPathAnchor,
  type DirectorMotionPathHandle,
  type DirectorTransform,
  type DirectorTuple3,
} from "@/store/directorStore";

const axisLabels = ["X", "Y", "Z"] as const;

function AxisFields({
  label,
  field,
  values,
  onChange,
  disabledAxes = [],
}: {
  label: string;
  field: keyof DirectorTransform | "target";
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

export function DirectorInspector({
  activeCapture,
  onSendCapture,
}: {
  activeCapture: DirectorCapture | null;
  onSendCapture: (capture: DirectorCapture) => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const objects = useDirectorStore((state) => state.objects);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const updateScene = useDirectorStore((state) => state.updateScene);
  const updateObject = useDirectorStore((state) => state.updateObject);
  const updateObjectTransform = useDirectorStore(
    (state) => state.updateObjectTransform,
  );
  const updateCamera = useDirectorStore((state) => state.updateCamera);
  const recordObjectKeyframe = useDirectorStore(
    (state) => state.recordObjectKeyframe,
  );
  const timeline = useDirectorStore((state) => state.timeline);
  const selected = objects.find((object) => object.id === selectedObjectId) ?? null;
  const selectedTrack = timeline.tracks.find(
    (track) => track.objectId === selected?.id,
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

  return (
    <section
      data-director-inspector
      data-director-inspector-kind={selected?.kind ?? "scene"}
      className="flex h-full min-h-0 flex-col bg-[#191919]"
    >
      <header className="flex h-12 shrink-0 items-center border-b border-white/[0.07] px-3">
        <h2 className="text-xs font-medium text-[#dedede]">
          {selected ? "对象属性" : "场景属性"}
        </h2>
        <span className="ml-auto text-[10px] text-[#666]">
          {selected?.kind === "camera"
            ? "摄像机"
            : selected?.kind === "character"
              ? "角色"
              : selected
                ? "场景物体"
                : "Scene"}
        </span>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {selected ? (
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
                <AxisFields
                  label="注视点"
                  field="target"
                  values={selected.camera.target}
                  onChange={(axis, value) => {
                    const target: DirectorTuple3 = [...selected.camera!.target];
                    target[axis] = value;
                    updateCamera(selected.id, { target });
                    recordObjectKeyframe(selected.id);
                  }}
                />
              </div>
            ) : null}

            {selectedPath ? (
              <MotionPathInspector path={selectedPath} />
            ) : null}
          </div>
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
