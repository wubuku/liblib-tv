"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorTransform,
} from "@/store/directorStore";
import type { DirectorTimelineTrack } from "@/store/directorStore";

// Batch 563: 源站截图 50/51——摄像机面板「运动轨迹」(NEW) 页签内容：
// 虚拟相机（请保持手机和电脑在同一 wifi 下，用手机扫码连接 + QR + 录制/
// 重试）、⟳ 预设运镜、创建运动轨迹。录制接真实 store 动作
// startPhoneVcamRecording/导入链路（与 DirectorPhoneVcamPanel 同源）；
// 预设运镜/创建运动轨迹的完整面板位于时间线控制簇（DirectorTimeline），
// 此处按钮以提示态渲染（CLONE_DECISION）。无云端动作。
// Batch 576: 源站截图 64——关键帧选中态联动本页签的编辑字段组
// （时长/位置/旋转/缩放/统一缩放，镜像选中关键帧值）；字段编辑经
// updateObjectTransform 在当前播头提交（autoKeyframe 开时更新该关键帧）。
// Batch 580（源站截图 64 放大复核，docs/research/liblib-source-exploration-
// 2026-09-25/64-director-diamond-dragged.png 右栏 3180-3840 × 1140-1960 区域）：
// 1) 「时长」与「统一缩放」在源站是 **滑杆 + 数值框** 同一行（青色已填充
//    轨道 + 白色圆形滑块）；576 的 clone 完全没有时长，统一缩放还是恒为
//    "1.0" 的死三元，本批按源站几何补齐并接上真实读写。
// 2) 修正 576 遗留缺陷：摄像机轨道关键帧 value 形如
//    { transform, target, fov }，而旧代码直接读 value[field]，导致本页签
//    （正是摄像机上下文）位置/旋转/缩放三组输入恒显 NaN。取值改为
//    相机轨道走 value.transform[field]，变换轨道走 value[field]。
// 3) 字段提交对齐到「选中关键帧」：updateObjectTransform 落在当前播头，
//    播头不在选中关键帧时间时会静默写到另一个关键帧；提交前先把播头
//    对齐（setTimelineTime），保证编辑与镜像字段互为同一目标。
// Batch 580: 源站截图 64 的「时长」「统一缩放」为 滑杆 + 数值框 同行布局，
// 轨道深灰、已填充段青色 #09caf5、滑块白色圆形（截图实测）。
// Batch 583: 统一缩放的**真实量程**由源站角色属性页实测确定——
// min=0.1 max=10 step=0.05（`/tmp` 采样：角色A 属性页 y=409 的
// `range value=1` + 文本 `1.0`），与场景缩放同为 0.1–10 的倍率滑杆。
// 580 当时按截图量滑块位置推断的 0–10 已据此更正。「时长」滑杆量程仍无
// 源站交互证据，保留 0–10 并标注为待复核。
const MOTION_SLIDER_MAX = 10;
const MOTION_SLIDER_MIN = 0;
const UNIFORM_SCALE_MIN = 0.1;
const UNIFORM_SCALE_STEP = 0.05;

type MotionKeyframeTrack = Extract<
  DirectorTimelineTrack,
  { kind: "transform" | "camera" }
>;

// 摄像机轨道关键帧 value = { transform, target, fov }；变换/群组轨道
// value = DirectorTransform。Batch 580 修复：旧实现只按 value[field] 读取，
// 摄像机上下文（本页签的唯一场景）恒得 undefined → Number(undefined) = NaN。
function readKeyframeTransform(
  keyframe: MotionKeyframeTrack["keyframes"][number] | null,
): DirectorTransform | null {
  if (!keyframe) return null;
  const value = keyframe.value as unknown as Record<string, unknown>;
  if (
    value.transform &&
    typeof value.transform === "object" &&
    !Array.isArray(value.transform)
  ) {
    return value.transform as DirectorTransform;
  }
  if (value.position && value.rotation && value.scale) {
    return value as unknown as DirectorTransform;
  }
  return null;
}

function MotionSliderField({
  label,
  value,
  step,
  decimals,
  min = MOTION_SLIDER_MIN,
  onCommit,
  testId,
}: {
  label: string;
  value: number;
  step: number;
  decimals: number;
  min?: number;
  onCommit: (next: number) => void;
  testId: string;
}) {
  const clamped = Math.min(MOTION_SLIDER_MAX, Math.max(min, value));
  const span = MOTION_SLIDER_MAX - min || 1;
  const ratio = (clamped - min) / span;
  return (
    <div className="space-y-1 text-xs text-[#bcbcbc]">
      <span className="block">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={min}
          max={MOTION_SLIDER_MAX}
          step={step}
          value={clamped}
          aria-label={label}
          data-director-motion-slider={testId}
          onChange={(event) => onCommit(Number(event.currentTarget.value))}
          // 源站轨道为深灰、已填充段青色、滑块白色；accent-color 无法分开
          // 填充与滑块配色，故用内联渐变 + 滑块伪元素（AGENTS.md 要求记录
          // 动态内联样式，理由：复刻源站滑杆几何）。
          style={{
            background: `linear-gradient(to right, #09caf5 0%, #09caf5 ${
              ratio * 100
            }%, #4a4a4a ${ratio * 100}%, #4a4a4a 100%)`,
          }}
          className="h-1 flex-1 cursor-pointer appearance-none rounded-full [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0a0a0a] [&::-webkit-slider-thumb]:bg-white"
        />
        <input
          type="number"
          step={step}
          aria-label={`${label} 数值`}
          data-director-motion-slider-value={testId}
          value={Number(clamped.toFixed(decimals))}
          onChange={(event) => {
            const next = Number(event.currentTarget.value);
            if (Number.isFinite(next)) onCommit(next);
          }}
          className="h-7 w-[68px] shrink-0 rounded bg-[#2a2a2a] px-2 text-[11px] tabular-nums text-[#dedede] outline-none focus:ring-1 focus:ring-[#09caf5]/60"
        />
      </div>
    </div>
  );
}

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
  const setTimelineTime = useDirectorStore((state) => state.setTimelineTime);
  const selectedKeyframe = (() => {
    const track = timeline.tracks.find(
      (candidate): candidate is MotionKeyframeTrack =>
        candidate.objectId === selectedObjectId &&
        (candidate.kind === "transform" || candidate.kind === "camera"),
    );
    return (
      track?.keyframes.find(
        (keyframe) => keyframe.id === timeline.selectedKeyframeId,
      ) ?? null
    );
  })();
  const selectedTransform = readKeyframeTransform(selectedKeyframe);
  // Batch 580: updateObjectTransform 提交在当前播头。播头不在选中关键帧
  // 时间上时，编辑会静默写到另一个关键帧，与镜像字段显示的选中关键帧
  // 脱节。提交前先把播头对齐到选中关键帧（batch 579 起菱形点击已 seek，
  // 此处覆盖程序化选中等其余路径）。
  const commitTransformValue = (
    field: "position" | "rotation" | "scale",
    axis: 0 | 1 | 2,
    value: number,
  ) => {
    const objectId = selectedObjectId;
    if (!objectId || !Number.isFinite(value)) return;
    if (selectedKeyframe && timeline.currentTime !== selectedKeyframe.time) {
      setTimelineTime(selectedKeyframe.time);
    }
    updateObjectTransform(objectId, field, axis, value);
  };
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

      {selectedKeyframe && selectedTransform ? (
        <section
          data-director-motion-keyframe-editor
          className="space-y-2 border-t border-white/[0.07] pt-3"
        >
          <h3 className="text-xs font-medium text-[#cfcfcf]">
            关键帧 {selectedKeyframe.time.toFixed(2)}s
          </h3>
          {/* Batch 580: 源站字段组自上而下为 时长 → 位置 → 旋转 → 缩放 →
              统一缩放（截图 64）。时长在 clone 中映射为播头时间（运动轨迹
              面板所处的时长位置）；源站 0.1 的取值语义未经交互复核。 */}
          <MotionSliderField
            label="时长"
            testId="duration"
            value={timeline.currentTime}
            step={0.01}
            decimals={2}
            onCommit={(next) =>
              setTimelineTime(
                Math.min(MOTION_SLIDER_MAX, Math.max(0, next)),
              )
            }
          />
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
                {([0, 1, 2] as const).map((axis) => (
                  <input
                    key={axis}
                    data-director-motion-keyframe-field={field}
                    data-director-motion-keyframe-axis={axis}
                    type="number"
                    step={field === "rotation" ? 1 : 0.1}
                    aria-label={`${label} ${["X", "Y", "Z"][axis]}`}
                    value={Number(
                      selectedTransform[field][[0, 1, 2][axis]].toFixed(3),
                    )}
                    onChange={(event) =>
                      commitTransformValue(
                        field,
                        axis,
                        Number(event.currentTarget.value),
                      )
                    }
                    className="h-7 w-full rounded border border-white/[0.08] bg-[#222] px-1.5 text-[11px] tabular-nums text-[#dedede] outline-none focus:border-[#09caf5]/60"
                  />
                ))}
              </div>
            </div>
          ))}
          <MotionSliderField
            label="统一缩放"
            testId="uniform-scale"
            value={selectedTransform.scale[0]}
            step={UNIFORM_SCALE_STEP}
            decimals={1}
            min={UNIFORM_SCALE_MIN}
            onCommit={(next) => {
              // 统一缩放 = 三轴同值（源站截图 64 缩放 X/Y/Z 同为 1 时
              // 统一缩放显示 1.0）。三轴经 commitTransformValue 逐轴提交。
              ([0, 1, 2] as const).forEach((axis) =>
                commitTransformValue("scale", axis, next),
              );
            }}
          />
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
