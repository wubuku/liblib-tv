"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import {
  ArrowDown,
  ArrowUp,
  Crosshair,
  Gauge,
  Lock,
  RotateCcw,
  Smartphone,
  Unlock,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  normalizeDirectorPhoneOrientation,
  type DirectorPhoneOrientation,
  type DirectorPhoneVcamPose,
} from "@/components/director/directorPhoneVcamMath";
import {
  useDirectorStore,
  type DirectorCameraKeyframeValue,
  type DirectorPhoneVcamSample,
} from "@/store/directorStore";

interface PermissionAwareDeviceOrientationEvent {
  requestPermission?: () => Promise<"granted" | "denied">;
}

const pairingPattern = Array.from({ length: 13 * 13 }, (_, index) => {
  const x = index % 13;
  const y = Math.floor(index / 13);
  const finder = (originX: number, originY: number) => {
    const localX = x - originX;
    const localY = y - originY;
    if (localX < 0 || localX > 4 || localY < 0 || localY > 4) return false;
    return (
      localX === 0 ||
      localX === 4 ||
      localY === 0 ||
      localY === 4 ||
      (localX >= 2 && localX <= 2 && localY >= 2 && localY <= 2)
    );
  };
  return (
    finder(0, 0) ||
    finder(8, 0) ||
    finder(0, 8) ||
    ((x * 7 + y * 5 + x * y) % 11 < 4 && x > 4 && y > 4)
  );
});

function cloneCameraValue(
  value: DirectorCameraKeyframeValue,
): DirectorCameraKeyframeValue {
  return {
    transform: {
      position: [...value.transform.position],
      rotation: [...value.transform.rotation],
      scale: [...value.transform.scale],
    },
    target: [...value.target],
    fov: value.fov,
  };
}

function getActiveCameraSample(time: number): DirectorPhoneVcamSample | null {
  const state = useDirectorStore.getState();
  const camera = state.objects.find(
    (object) => object.id === state.activeCameraId,
  );
  if (!camera?.camera) return null;
  return {
    time,
    value: cloneCameraValue({
      transform: camera.transform,
      target: camera.camera.target,
      fov: camera.camera.fov,
    }),
  };
}

function formatSeconds(value: number): string {
  return `${Math.max(value, 0).toFixed(1)}s`;
}

export function DirectorPhoneVcamPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const phoneVcam = useDirectorStore((state) => state.phoneVcam);
  const currentTime = useDirectorStore(
    (state) => state.timeline.currentTime,
  );
  const duration = useDirectorStore((state) => state.timeline.duration);
  const setStatus = useDirectorStore((state) => state.setPhoneVcamStatus);
  const connectLocal = useDirectorStore(
    (state) => state.connectPhoneVcamLocal,
  );
  const setGyroEnabled = useDirectorStore(
    (state) => state.setPhoneVcamGyroEnabled,
  );
  const setStability = useDirectorStore(
    (state) => state.setPhoneVcamStability,
  );
  const toggleKeepLevel = useDirectorStore(
    (state) => state.togglePhoneVcamKeepLevel,
  );
  const setHold = useDirectorStore((state) => state.setPhoneVcamHold);
  const calibrate = useDirectorStore(
    (state) => state.calibratePhoneVcam,
  );
  const applyPose = useDirectorStore(
    (state) => state.applyPhoneVcamPose,
  );
  const elevate = useDirectorStore((state) => state.elevatePhoneVcam);
  const startRecording = useDirectorStore(
    (state) => state.startPhoneVcamRecording,
  );
  const setRecordingTime = useDirectorStore(
    (state) => state.setPhoneVcamRecordingTime,
  );
  const setSampleCount = useDirectorStore(
    (state) => state.setPhoneVcamSampleCount,
  );
  const importTake = useDirectorStore(
    (state) => state.importPhoneVcamTake,
  );
  const pointerId = useRef<number | null>(null);
  const orientationOrigin = useRef<DirectorPhoneOrientation | null>(null);
  const samples = useRef<DirectorPhoneVcamSample[]>([]);
  const [gyroMessage, setGyroMessage] = useState<string | null>(null);
  const connected = ["local-ready", "recording", "imported"].includes(
    phoneVcam.status,
  );
  const recording = phoneVcam.status === "recording";
  const remaining = Math.max(duration - currentTime, 0);

  useEffect(() => {
    if (!open || phoneVcam.status !== "idle") return;
    setStatus("preparing");
  }, [open, phoneVcam.status, setStatus]);

  useEffect(() => {
    if (!open || phoneVcam.status !== "preparing") return;
    const timer = window.setTimeout(() => setStatus("waiting"), 320);
    return () => window.clearTimeout(timer);
  }, [open, phoneVcam.status, setStatus]);

  useEffect(() => {
    if (!open || !phoneVcam.gyroEnabled) return;
    orientationOrigin.current = null;
    const handleOrientation = (event: DeviceOrientationEvent) => {
      if (
        event.alpha === null ||
        event.beta === null ||
        event.gamma === null
      ) {
        return;
      }
      const orientation = {
        alpha: event.alpha,
        beta: event.beta,
        gamma: event.gamma,
      };
      if (!orientationOrigin.current) {
        orientationOrigin.current = orientation;
      }
      applyPose(
        normalizeDirectorPhoneOrientation(
          orientation,
          orientationOrigin.current,
        ),
      );
    };
    window.addEventListener("deviceorientation", handleOrientation);
    return () =>
      window.removeEventListener("deviceorientation", handleOrientation);
  }, [applyPose, open, phoneVcam.gyroEnabled]);

  useEffect(() => {
    if (!open || !recording) return;
    const state = useDirectorStore.getState();
    const startTime = state.phoneVcam.recordingStartTime;
    if (startTime === null) return;
    const startedAt = performance.now();
    let animationFrame = 0;
    let lastSampleAt = -Infinity;
    let active = true;
    const initial = getActiveCameraSample(startTime);
    samples.current = initial ? [initial] : [];
    setSampleCount(samples.current.length);

    const finish = (time: number) => {
      const finalSample = getActiveCameraSample(time);
      const previous = samples.current[samples.current.length - 1];
      if (
        finalSample &&
        (!previous || Math.abs(previous.time - finalSample.time) >= 0.001)
      ) {
        samples.current.push(finalSample);
      }
      setSampleCount(samples.current.length);
      importTake(samples.current);
    };

    const tick = (now: number) => {
      if (!active) return;
      const elapsed = Math.max((now - startedAt) / 1000, 0);
      const nextTime = Math.min(startTime + elapsed, duration);
      setRecordingTime(nextTime);
      if (now - lastSampleAt >= 96 || nextTime >= duration - 0.001) {
        const sample = getActiveCameraSample(nextTime);
        if (sample) samples.current.push(sample);
        lastSampleAt = now;
        setSampleCount(samples.current.length);
      }
      if (nextTime >= duration - 0.001) {
        finish(nextTime);
        return;
      }
      animationFrame = window.requestAnimationFrame(tick);
    };

    animationFrame = window.requestAnimationFrame(tick);
    return () => {
      active = false;
      window.cancelAnimationFrame(animationFrame);
    };
  }, [
    duration,
    importTake,
    open,
    recording,
    setRecordingTime,
    setSampleCount,
  ]);

  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if (!recording) onClose();
    };
    window.addEventListener("keydown", closeOnEscape, true);
    return () =>
      window.removeEventListener("keydown", closeOnEscape, true);
  }, [onClose, open, recording]);

  const statusCopy = useMemo(() => {
    if (phoneVcam.status === "preparing") return "正在准备本机环境";
    if (phoneVcam.status === "waiting") {
      return "请保持手机和电脑在同一 wifi 下，用手机扫码连接";
    }
    if (phoneVcam.status === "local-ready") return "本机预演已连接";
    if (phoneVcam.status === "recording") return "录制中";
    if (phoneVcam.status === "imported") {
      return "手机运镜已导入机位时间轴";
    }
    if (phoneVcam.status === "error") {
      return phoneVcam.error ?? "手机运镜启动失败";
    }
    return "点击重试启动手机运镜";
  }, [phoneVcam.error, phoneVcam.status]);

  const requestGyro = async () => {
    setGyroMessage(null);
    if (typeof window.DeviceOrientationEvent === "undefined") {
      setGyroMessage("当前环境不支持手机运镜");
      setGyroEnabled(false);
      return;
    }
    const orientationConstructor =
      window.DeviceOrientationEvent as unknown as PermissionAwareDeviceOrientationEvent;
    try {
      const permission = orientationConstructor.requestPermission
        ? await orientationConstructor.requestPermission()
        : "granted";
      if (permission !== "granted") {
        setGyroMessage("请在 Safari 设置中允许运动与方向访问后重试");
        setGyroEnabled(false);
        return;
      }
      orientationOrigin.current = null;
      setGyroEnabled(true);
      setGyroMessage("陀螺仪已启用");
    } catch {
      setGyroEnabled(false);
      setGyroMessage("请在 Safari 设置中允许运动与方向访问后重试");
    }
  };

  const updatePoseFromPointer = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (
        pointerId.current !== null &&
        pointerId.current !== event.pointerId
      ) {
        return;
      }
      const rect = event.currentTarget.getBoundingClientRect();
      const normalizedX = Math.min(
        Math.max((event.clientX - rect.left) / rect.width, 0),
        1,
      );
      const normalizedY = Math.min(
        Math.max((event.clientY - rect.top) / rect.height, 0),
        1,
      );
      const pose: DirectorPhoneVcamPose = {
        yaw: (normalizedX - 0.5) * 90,
        pitch: (0.5 - normalizedY) * 60,
        roll: phoneVcam.keepLevel
          ? 0
          : (normalizedX - 0.5) * 24,
      };
      applyPose(pose);
    },
    [applyPose, phoneVcam.keepLevel],
  );

  const stopRecording = () => {
    if (!recording) return;
    const state = useDirectorStore.getState();
    const finalSample = getActiveCameraSample(state.timeline.currentTime);
    const previous = samples.current[samples.current.length - 1];
    if (
      finalSample &&
      (!previous || Math.abs(previous.time - finalSample.time) >= 0.001)
    ) {
      samples.current.push(finalSample);
    }
    setSampleCount(samples.current.length);
    importTake(samples.current);
  };

  const beginOrStopRecording = () => {
    if (recording) {
      stopRecording();
      return;
    }
    samples.current = [];
    startRecording();
  };

  if (!open) return null;

  return (
    <section
      data-director-phone-vcam-panel
      data-director-phone-vcam-status={phoneVcam.status}
      data-director-phone-vcam-mode="local-preview"
      className="absolute bottom-[72px] right-3 z-30 flex max-h-[calc(100%-88px)] w-[340px] flex-col overflow-hidden rounded-md border border-white/10 bg-[#1c1c1c]/98 text-[#d7d7d7] shadow-[0_18px_45px_rgba(0,0,0,0.46)] max-[520px]:left-3 max-[520px]:right-3 max-[520px]:w-auto"
    >
      <header className="flex h-11 shrink-0 items-center gap-2 border-b border-white/[0.07] px-3">
        <Smartphone size={15} className="text-[#69d9f6]" />
        <h2 className="min-w-0 flex-1 truncate text-xs font-medium text-[#eeeeee]">
          虚拟相机
        </h2>
        <span
          data-director-phone-vcam-local-preview
          className="rounded-sm border border-[#6bd8f5]/25 bg-[#0b5363]/35 px-1.5 py-0.5 text-[9px] text-[#83dff5]"
        >
          本机预演
        </span>
        <button
          type="button"
          aria-label="关闭虚拟相机"
          title="关闭"
          disabled={recording}
          onClick={onClose}
          className="flex h-7 w-7 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-white disabled:text-[#444]"
        >
          <X size={14} />
        </button>
      </header>

      <div className="min-h-0 overflow-y-auto">
        <div className="flex min-h-11 items-center gap-2 border-b border-white/[0.07] px-3 py-2">
          <span
            className={cn(
              "h-2 w-2 shrink-0 rounded-full bg-[#717171]",
              phoneVcam.status === "preparing" && "animate-pulse bg-[#e0b45d]",
              phoneVcam.status === "waiting" && "animate-pulse bg-[#69d9f6]",
              connected && "bg-[#64d58a]",
              phoneVcam.status === "recording" &&
                "animate-pulse bg-[#f25d61]",
              phoneVcam.status === "error" && "bg-[#ef7777]",
            )}
          />
          <span className="min-w-0 flex-1 text-[10px] leading-4 text-[#969696]">
            {statusCopy}
          </span>
          {phoneVcam.status === "error" ? (
            <button
              type="button"
              onClick={() => setStatus("preparing")}
              className="h-7 shrink-0 rounded px-2 text-[10px] text-[#b8b8b8] hover:bg-white/[0.06] hover:text-white"
            >
              重试
            </button>
          ) : null}
        </div>

        {!connected ? (
          <div className="flex flex-col items-center px-4 py-4">
            <div
              aria-hidden="true"
              className="relative grid h-28 w-28 grid-cols-[repeat(13,minmax(0,1fr))] gap-px overflow-hidden rounded-sm border-4 border-white bg-white p-1"
            >
              {pairingPattern.map((filled, index) => (
                <span
                  key={index}
                  className={filled ? "bg-[#161616]" : "bg-white"}
                />
              ))}
              <span className="absolute inset-x-3 top-1/2 -translate-y-1/2 bg-white/95 py-1 text-center text-[9px] font-medium text-[#303030]">
                本机预演
              </span>
            </div>
            <p className="mt-3 max-w-[270px] text-center text-[10px] leading-4 text-[#777]">
              如果手机提示证书风险，请在同一 Wi-Fi 下继续访问并信任本机证书。
            </p>
            <button
              type="button"
              data-director-phone-vcam-connect
              disabled={phoneVcam.status === "preparing"}
              onClick={connectLocal}
              className="mt-3 flex h-8 items-center gap-1.5 rounded bg-[#e9e9e9] px-3 text-[11px] text-[#202020] hover:bg-white disabled:bg-[#444] disabled:text-[#777]"
            >
              <Smartphone size={13} />
              启动本机预演
            </button>
          </div>
        ) : (
          <>
            <div className="border-b border-white/[0.07] px-3 py-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[10px] text-[#777]">GYRO</span>
                <span
                  data-director-phone-vcam-pose
                  data-yaw={phoneVcam.pose.yaw.toFixed(2)}
                  data-pitch={phoneVcam.pose.pitch.toFixed(2)}
                  data-roll={phoneVcam.pose.roll.toFixed(2)}
                  className="text-[9px] tabular-nums text-[#686868]"
                >
                  {phoneVcam.pose.yaw.toFixed(0)} /{" "}
                  {phoneVcam.pose.pitch.toFixed(0)} /{" "}
                  {phoneVcam.pose.roll.toFixed(0)}
                </span>
              </div>
              <div
                data-director-phone-vcam-pose-pad
                role="slider"
                aria-label="手机运镜姿态"
                aria-valuemin={-90}
                aria-valuemax={90}
                aria-valuenow={Math.round(phoneVcam.pose.yaw)}
                aria-valuetext={`yaw ${phoneVcam.pose.yaw.toFixed(0)}, pitch ${phoneVcam.pose.pitch.toFixed(0)}`}
                tabIndex={0}
                onPointerDown={(event) => {
                  pointerId.current = event.pointerId;
                  event.currentTarget.setPointerCapture(event.pointerId);
                  updatePoseFromPointer(event);
                }}
                onPointerMove={(event) => {
                  if (pointerId.current === event.pointerId) {
                    updatePoseFromPointer(event);
                  }
                }}
                onPointerUp={(event) => {
                  if (pointerId.current !== event.pointerId) return;
                  pointerId.current = null;
                  if (event.currentTarget.hasPointerCapture(event.pointerId)) {
                    event.currentTarget.releasePointerCapture(event.pointerId);
                  }
                }}
                className={cn(
                  "relative h-24 touch-none overflow-hidden rounded border border-white/[0.08] bg-[#171717]",
                  phoneVcam.hold && "opacity-55",
                )}
              >
                <span className="absolute left-1/2 top-0 h-full w-px bg-white/[0.06]" />
                <span className="absolute left-0 top-1/2 h-px w-full bg-white/[0.06]" />
                <span
                  className="pointer-events-none absolute h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#75def7] bg-[#0a7288]/45 shadow-[0_0_12px_rgba(72,210,242,0.34)]"
                  style={{
                    left: `${50 + (phoneVcam.pose.yaw / 90) * 100}%`,
                    top: `${50 - (phoneVcam.pose.pitch / 60) * 100}%`,
                  }}
                >
                  <Crosshair size={12} className="m-[3px] text-[#a8ecfb]" />
                </span>
              </div>

              <div className="mt-2 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  data-director-phone-vcam-enable-gyro
                  aria-pressed={phoneVcam.gyroEnabled}
                  onClick={() => void requestGyro()}
                  className={cn(
                    "flex h-8 items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-[10px] text-[#9c9c9c] hover:text-white",
                    phoneVcam.gyroEnabled &&
                      "border-[#64d58a]/30 text-[#7ee49b]",
                  )}
                >
                  <Gauge size={13} />
                  {phoneVcam.gyroEnabled ? "陀螺仪已启用" : "启用陀螺仪"}
                </button>
                <button
                  type="button"
                  data-director-phone-vcam-calibrate
                  onClick={() => {
                    orientationOrigin.current = null;
                    calibrate();
                  }}
                  className="flex h-8 items-center justify-center gap-1.5 rounded border border-white/[0.08] bg-[#222] text-[10px] text-[#9c9c9c] hover:text-white"
                >
                  <RotateCcw size={13} />
                  松开校准
                </button>
              </div>
              {gyroMessage ? (
                <p className="mt-2 text-[9px] leading-4 text-[#8b8b8b]">
                  {gyroMessage}
                </p>
              ) : null}
            </div>

            <div className="border-b border-white/[0.07] px-3 py-3">
              <label className="block">
                <span className="flex items-center justify-between text-[10px] text-[#818181]">
                  <span>稳定度</span>
                  <span className="tabular-nums">
                    稳定度：{Math.round(phoneVcam.stability)}
                  </span>
                </span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={phoneVcam.stability}
                  data-director-phone-vcam-stability
                  onChange={(event) =>
                    setStability(Number(event.currentTarget.value))
                  }
                  className="mt-2 h-1 w-full accent-[#62d6f3]"
                />
              </label>
              <div className="mt-3 grid grid-cols-[1fr_1fr_auto_auto] gap-1.5">
                <button
                  type="button"
                  data-director-phone-vcam-keep-level
                  aria-pressed={phoneVcam.keepLevel}
                  onClick={toggleKeepLevel}
                  className={cn(
                    "h-8 rounded border border-white/[0.08] bg-[#222] px-2 text-[10px] text-[#929292] hover:text-white",
                    phoneVcam.keepLevel &&
                      "border-[#63d7f4]/30 text-[#72dcf6]",
                  )}
                >
                  保持水平
                </button>
                <button
                  type="button"
                  data-director-phone-vcam-hold
                  aria-pressed={phoneVcam.hold}
                  onClick={() => setHold(!phoneVcam.hold)}
                  className={cn(
                    "flex h-8 items-center justify-center gap-1 rounded border border-white/[0.08] bg-[#222] px-2 text-[10px] text-[#929292] hover:text-white",
                    phoneVcam.hold &&
                      "border-[#e6b764]/30 text-[#efc77f]",
                  )}
                >
                  {phoneVcam.hold ? <Unlock size={12} /> : <Lock size={12} />}
                  {phoneVcam.hold ? "解锁机位" : "临时锁定机位"}
                </button>
                <button
                  type="button"
                  data-director-phone-vcam-elevate="up"
                  aria-label="上升"
                  title="上升"
                  onClick={() => elevate(0.18)}
                  className="flex h-8 w-8 items-center justify-center rounded border border-white/[0.08] bg-[#222] text-[#929292] hover:text-white"
                >
                  <ArrowUp size={13} />
                </button>
                <button
                  type="button"
                  data-director-phone-vcam-elevate="down"
                  aria-label="下降"
                  title="下降"
                  onClick={() => elevate(-0.18)}
                  className="flex h-8 w-8 items-center justify-center rounded border border-white/[0.08] bg-[#222] text-[#929292] hover:text-white"
                >
                  <ArrowDown size={13} />
                </button>
              </div>
            </div>

            <div className="px-3 py-3">
              <div className="flex items-center justify-between text-[10px] text-[#757575]">
                <span>
                  {formatSeconds(currentTime)} / {formatSeconds(duration)}
                </span>
                <span
                  data-director-phone-vcam-sample-count={
                    phoneVcam.sampleCount
                  }
                  className="tabular-nums"
                >
                  {recording
                    ? `${phoneVcam.sampleCount} samples`
                    : `剩余 ${formatSeconds(remaining)}`}
                </span>
              </div>
              <button
                type="button"
                data-director-phone-vcam-record
                aria-pressed={recording}
                onClick={beginOrStopRecording}
                className={cn(
                  "mt-2 flex h-9 w-full items-center justify-center gap-2 rounded bg-[#e9e9e9] text-[11px] font-medium text-[#202020] hover:bg-white",
                  recording && "bg-[#d85256] text-white hover:bg-[#e05f63]",
                )}
              >
                <span
                  className={cn(
                    "h-2 w-2 rounded-full bg-[#d85256]",
                    recording && "animate-pulse bg-white",
                  )}
                />
                {recording ? "停止录制" : "录制"}
              </button>
              {phoneVcam.error ? (
                <p
                  data-director-phone-vcam-error
                  className="mt-2 text-[9px] leading-4 text-[#d48484]"
                >
                  {phoneVcam.error}
                </p>
              ) : null}
              {phoneVcam.importedCameraId && phoneVcam.importedTrackId ? (
                <p
                  data-director-phone-vcam-take
                  data-camera-id={phoneVcam.importedCameraId}
                  data-track-id={phoneVcam.importedTrackId}
                  className="mt-2 truncate text-[9px] text-[#6fdc91]"
                >
                  手机运镜已导入机位时间轴
                </p>
              ) : null}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
