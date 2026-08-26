"use client";

import Image from "next/image";
import { Camera, Check, Eye, EyeOff, Send } from "lucide-react";
import {
  useDirectorStore,
  type DirectorCapture,
  type DirectorTransform,
  type DirectorTuple3,
} from "@/store/directorStore";

const axisLabels = ["X", "Y", "Z"] as const;

function AxisFields({
  label,
  field,
  values,
  onChange,
}: {
  label: string;
  field: keyof DirectorTransform | "target";
  values: DirectorTuple3;
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
            <span className="mr-1 text-[10px] text-[#666]">{axisLabels[index]}</span>
            <input
              type="number"
              step={field === "rotation" ? 1 : 0.1}
              data-director-transform-field={field}
              data-director-transform-axis={axisLabels[index].toLowerCase()}
              value={Number(value.toFixed(2))}
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
  const selected = objects.find((object) => object.id === selectedObjectId) ?? null;

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
                onChange={(axis, value) =>
                  updateObjectTransform(selected.id, "position", axis, value)
                }
              />
              <AxisFields
                label="旋转"
                field="rotation"
                values={selected.transform.rotation}
                onChange={(axis, value) =>
                  updateObjectTransform(selected.id, "rotation", axis, value)
                }
              />
              <AxisFields
                label="缩放"
                field="scale"
                values={selected.transform.scale}
                onChange={(axis, value) =>
                  updateObjectTransform(selected.id, "scale", axis, value)
                }
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
                    onChange={(event) =>
                      updateCamera(selected.id, {
                        fov: Number(event.target.value),
                      })
                    }
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
                  }}
                />
              </div>
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
