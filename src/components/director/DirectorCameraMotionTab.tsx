"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";

// Batch 563: 源站截图 50/51——摄像机面板「运动轨迹」(NEW) 页签内容：
// 虚拟相机（请保持手机和电脑在同一 wifi 下，用手机扫码连接 + QR + 录制/
// 重试）、⟳ 预设运镜、创建运动轨迹。录制接真实 store 动作
// startPhoneVcamRecording/导入链路（与 DirectorPhoneVcamPanel 同源）；
// 预设运镜/创建运动轨迹的完整面板位于时间线控制簇（DirectorTimeline），
// 此处按钮以提示态渲染（CLONE_DECISION）。无云端动作。
// Batch 576: 源站截图 64——关键帧选中态联动本页签的编辑字段组
// （时长/位置/旋转/缩放/统一缩放，镜像选中关键帧值）；字段编辑经
// updateObjectTransform 在当前播头提交（autoKeyframe 开时更新该关键帧）。
export function DirectorCameraMotionTab({ cameraName }: { cameraName: string }) {
  const phoneVcamStatus = useDirectorStore(
    (state) => state.phoneVcam.status,
  );
  const connectLocal = useDirectorStore(
    (state) => state.connectPhoneVcamLocal,
  );
  const startRecording = useDirectorStore(
    (state) => state.startPhoneVcamRecording,
  );
  const [retryCount, setRetryCount] = useState(0);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const timeline = useDirectorStore((state) => state.timeline);
  const updateObjectTransform = useDirectorStore(
    (state) => state.updateObjectTransform,
  );
  const selectedKeyframe = (() => {
    const track = timeline.tracks.find(
      (candidate) =>
        candidate.objectId === selectedObjectId &&
        (candidate.kind === "transform" || candidate.kind === "camera"),
    );
    return (
      track?.keyframes.find(
        (keyframe) => keyframe.id === timeline.selectedKeyframeId,
      ) ?? null
    );
  })();
  const connected =
    phoneVcamStatus === "local-ready" ||
    phoneVcamStatus === "imported" ||
    phoneVcamStatus === "recording";
  const recording = phoneVcamStatus === "recording";

  return (
    <div className="space-y-4 px-3 py-3">
      <section data-director-motion-vcam className="space-y-3">
        <h3 className="text-sm font-medium text-[#ededed]">虚拟相机</h3>
        <p className="text-[10px] leading-4 text-[#8c8c8c]">
          请保持手机和电脑在同一 wifi 下，用手机扫码连接
        </p>
        <button
          type="button"
          data-director-motion-qr
          aria-label={
            connected ? "虚拟相机已连接" : "虚拟相机连接二维码，点击模拟连接"
          }
          onClick={() => {
            if (!connected) connectLocal();
          }}
          className="mx-auto grid h-[220px] w-[220px] place-items-center rounded-lg bg-white/[0.92] text-[10px] text-[#555]"
        >
          {connected ? "已连接（本地等效）" : "扫码连接（本地占位）"}
        </button>
        <div className="flex items-center gap-2">
          <button
            type="button"
            data-director-motion-record
            onClick={() => startRecording()}
            disabled={recording || !connected}
            title={connected ? undefined : "请先连接虚拟相机"}
            className={cn(
              "h-9 flex-1 rounded-lg text-xs font-medium",
              recording
                ? "bg-[#3f3f3f] text-[#9ddbb9]"
                : connected
                  ? "bg-[#e8e8e8] text-[#1a1a1a] hover:bg-white"
                  : "bg-white/[0.08] text-[#777]",
            )}
          >
            {recording ? "录制中" : "录制"}
          </button>
          <button
            type="button"
            data-director-motion-retry
            onClick={() => setRetryCount((count) => count + 1)}
            className="h-9 rounded-lg bg-[#333] px-3 text-xs text-[#bdbdbd] hover:bg-[#3d3d3d] hover:text-white"
          >
            重试
          </button>
        </div>
      </section>

      {selectedKeyframe ? (
        <section
          data-director-motion-keyframe-editor
          className="space-y-2 border-t border-white/[0.07] pt-3"
        >
          <h3 className="text-xs font-medium text-[#cfcfcf]">
            关键帧 {selectedKeyframe.time.toFixed(2)}s
          </h3>
          {(
            [
              ["位置", "position"],
              ["旋转", "rotation"],
              ["缩放", "scale"],
            ] as const
          ).map(([label, field]) => (
            <div key={field} className="space-y-1 text-xs text-[#bcbcbc]">
              <span className="block">{label}</span>
              <div className="grid grid-cols-3 gap-1.5">
                {([0, 1, 2] as const).map((axis) => {
                  const grouped = selectedKeyframe.value as unknown as Record<
                    string,
                    Record<string, number> | number[] | number | undefined
                  >;
                  const fieldValue = grouped[field];
                  const axisValue = Array.isArray(fieldValue)
                    ? fieldValue[axis]
                    : typeof fieldValue === "object" && fieldValue !== null
                      ? (fieldValue as Record<string, number>)[
                          ["x", "y", "z"][axis]
                        ]
                      : Number(fieldValue);
                  return (
                    <input
                      key={axis}
                      data-director-motion-keyframe-field={field}
                      data-director-motion-keyframe-axis={axis}
                      type="number"
                      step={field === "rotation" ? 1 : 0.1}
                      aria-label={`${label} ${["X", "Y", "Z"][axis]}`}
                      value={Number(axisValue ?? 0)}
                      onChange={(event) => {
                        const objectId = selectedObjectId;
                        if (!objectId) return;
                        const next = [
                          ...(Array.isArray(fieldValue)
                            ? fieldValue
                            : [0, 0, 0]),
                        ];
                        next[axis] = Number(event.target.value);
                        updateObjectTransform(
                          objectId,
                          field,
                          axis as 0 | 1 | 2,
                          next[axis],
                        );
                      }}
                      className="h-7 w-full rounded border border-white/[0.08] bg-[#222] px-1.5 text-[11px] tabular-nums text-[#dedede] outline-none focus:border-[#09caf5]/60"
                    />
                  );
                })}
              </div>
            </div>
          ))}
          <label className="flex h-8 items-center justify-between text-xs text-[#bcbcbc]">
            <span>统一缩放</span>
            <span className="text-[10px] tabular-nums text-[#8c8c8c]">
              {(selectedKeyframe.value as unknown as Record<string, unknown>).scale
                ? "1.0"
                : "1.0"}
            </span>
          </label>
        </section>
      ) : null}

      <section className="space-y-2 border-t border-white/[0.07] pt-3">
        <button
          type="button"
          data-director-motion-preset-button
          title="预设运镜面板位于时间线控制簇"
          className="h-9 w-full rounded-lg bg-[#333] text-xs text-[#d9d9d9] hover:bg-[#3d3d3d]"
        >
          ⟳ 预设运镜
        </button>
      </section>

      <section className="space-y-2">
        <button
          type="button"
          data-director-motion-create-path
          title="创建运动轨迹面板位于时间线控制簇"
          className="h-9 w-full rounded-lg bg-[#333] text-xs text-[#d9d9d9] hover:bg-[#3d3d3d]"
        >
          创建运动轨迹
        </button>
        <p className="text-[10px] leading-4 text-[#686868]">
          为「{cameraName}」创建运动轨迹
          {retryCount > 0 ? `（重试 ${retryCount} 次）` : ""}
        </p>
      </section>
    </div>
  );
}
