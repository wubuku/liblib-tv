"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent, ReactNode } from "react";
import {
  Camera,
  ChartSpline,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Circle,
  DiamondPlus,
  Minus,
  Move3D,
  Pause,
  Plus,
  PenTool,
  Pencil,
  Play,
  RectangleHorizontal,
  Repeat2,
  Route,
  Timer,
  Trash2,
  Waypoints,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DIRECTOR_TIMELINE_DEFAULT_HEIGHT,
  useDirectorStore,
} from "@/store/directorStore";
import type { DirectorTimelineTrack } from "@/store/directorStore";
import { DirectorCurveEditor } from "@/components/director/DirectorCurveEditor";
import {
  DIRECTOR_CAMERA_MOTION_PRESETS,
  type DirectorCameraMotionPresetMode,
} from "@/components/director/directorCameraPresets";

function formatTimelineTime(seconds: number): string {
  const safeSeconds = Math.max(0, seconds);
  const minutes = Math.floor(safeSeconds / 60);
  const remaining = safeSeconds - minutes * 60;
  return `${minutes.toString().padStart(2, "0")}:${remaining
    .toFixed(2)
    .padStart(5, "0")}`;
}

type DirectorTimeUnit = "s" | "ms";

// Batch 593（源站 2026-10-01 实测，1920×1150，导演视角）：
// 轨道行第 3 列是三个 24×24 按钮，可及名与禁用规则逐字如下——
//   ‹ `上一关键帧`  本轨道在播放头之前没有关键帧时 disabled
//   ◆ `当前帧有关键帧`（aria-pressed=true）/ `当前帧无关键帧`（false）
//   › `下一关键帧`  本轨道在播放头之后没有关键帧时 disabled
// 关键帧在播放头 0 时：‹› 双禁用、◆ pressed；播放头移到 977ms 时 ‹ 可用、
// › 仍禁用、◆ 变为「当前帧无关键帧」——证明源站的 seek 范围是**本轨道**
// 而非全局时间轴。
const DIRECTOR_KEYFRAME_EPSILON = 1e-3;

// Batch 595（源站 2026-10-01 逐像素实测，见 directorTrackKeyframeState 上方）：
const DIRECTOR_RULER_TICK_SECONDS = 0.1;
const DIRECTOR_RULER_MAJOR_EVERY = 10;
const DIRECTOR_RULER_MAJOR_PX = "8.5px";
const DIRECTOR_RULER_MINOR_PX = "3.5px";
const DIRECTOR_RULER_MAJOR_COLOR = "#878787";
const DIRECTOR_RULER_MINOR_COLOR = "#686868";

// Batch 595 实测的刻度是**底对齐**在 36px 裁切窗口的底部往上 5px 处
// （主刻度 y 22.5–31.0、次刻度 y 27.5–31.0，窗口底 36）——标尺区因此是
// 36px 而不是 clone 原先的 28px，这也是车道与左列行能对齐的前提。
const DIRECTOR_RULER_HEIGHT_PX = 36;
const DIRECTOR_RULER_TICK_BOTTOM_PX = 5;

// Batch 598（源站 2026-10-01 逐像素实测，/tmp/src593/probe35–probe42）：
// 车道区是**一块自绘 canvas**（2124×115，父容器
// `relative shrink-0 overflow-hidden rounded-r-md bg-black/15`），里面同时画
// 标尺、车道色带、播放头和关键帧菱形，右列没有任何 DOM 覆盖层。clone 用 DOM
// 复刻这层，实测值：
//   车道格节奏  32px = 31px 色带 + 1px #212121 底边（色带 [37,67)、[68,99)，
//               间隙 [67,68) 是 #212121）
//   对象行车道  #28464c = #212121 叠 rgba(60,181,204,0.25)；顶边多一条 1px
//               #355359 亮线；四角 4px 圆角（左右两端 3.5px 的渐变实测）
//   轨道车道    #243032 = #212121 叠 rgba(60,181,204,0.1)
//   播放头      2px 宽、#05a3c5，**只覆盖对象行车道**（不画进标尺、不画进轨道
//               车道），无三角头、无辉光
//   关键帧菱形  外接 11×11 的空心菱形 = 7.8px 见方旋转 45°、1px #13879f 描边、
//               #2f2f2f 填充，垂直居中于所属车道
// 与左列同一套 alpha 阶梯：对象行 0.25 / white-10，轨道行 0.1 / 透明。
// 车道底色 #212121（不是 clone 原先的 #2a2a2a——batch 595 读到的是间隙色）。
const DIRECTOR_LANE_BASE_COLOR = "#212121";
const DIRECTOR_LANE_EDGE_COLOR = "#212121";
const DIRECTOR_OBJECT_LANE_TOP_EDGE = "#355359";
const DIRECTOR_PLAYHEAD_COLOR = "#05a3c5";
const DIRECTOR_KEYFRAME_EDGE_COLOR = "#13879f";
const DIRECTOR_KEYFRAME_FILL_COLOR = "#2f2f2f";
// 11px 外接方 ÷ √2 = 7.78px，取 7.8px 让实测外接回到 11px。
const DIRECTOR_KEYFRAME_BOX_PX = "7.8px";

// Batch 601（源站 2026-10-01 实测，/tmp/src593/probe47 + 4x 截图）：源站打开
// 导演台时时间单位是 **ms**——单位钮文字 `ms`、aria `切换时间单位为 s`，
// 播放头位置读数 `0`、总时长读数 `10000`（该项目时长 10s × 1000）。
// batch 591 把 clone 的默认单位定成 `s`，但那不是源站事实（源站两次观测都在
// ms 态），本批按实测翻转。
const DIRECTOR_DEFAULT_TIME_UNIT: DirectorTimeUnit = "ms";

function directorTrackKeyframeState(
  track: DirectorTimelineTrack,
  currentTime: number,
) {
  const times = track.keyframes
    .map((keyframe) => keyframe.time)
    .sort((a, b) => a - b);
  const exact = times.find(
    (time) => Math.abs(time - currentTime) <= DIRECTOR_KEYFRAME_EPSILON,
  );
  return {
    exact,
    earlier: [...times]
      .reverse()
      .find((time) => time < currentTime - DIRECTOR_KEYFRAME_EPSILON),
    later: times.find((time) => time > currentTime + DIRECTOR_KEYFRAME_EPSILON),
  };
}

// 轨道行第 4 列读数（源站实测 `3.3,2.2,10`）：显示本轨道在播放头处生效的
// 关键帧的位置三元组。格式不是定长小数——源站 z=10 印作 `10` 而非 `10.0`，
// 所以按「四舍五入到 3 位后交给默认数字转字符串」处理。
// 源站轨道名是**属性**名（位置 / 旋转 / 缩放，逐字实测），因为源站一个属性
// 一条轨道。clone 一条轨道同时驱动位置+旋转+缩放（机位轨道另含 target/fov），
// 无法一一对应，故第 2 列按 kind 取两字短名，完整 label 留在 title 上。
// —— 源站 36px 的名字列放不下 clone 的 `${对象名} · 变换` 这类长标签。
function directorTrackShortName(track: DirectorTimelineTrack): string {
  if (track.kind === "camera") return "机位";
  if (track.kind === "pose") return "姿势";
  if (track.kind === "group") return "分组";
  return "变换";
}

function directorTrackValueText(
  track: DirectorTimelineTrack,
  currentTime: number,
): string {
  const activeTime = track.keyframes
    .map((keyframe) => keyframe.time)
    .filter((time) => time <= currentTime + DIRECTOR_KEYFRAME_EPSILON)
    .sort((a, b) => b - a)[0];
  if (activeTime === undefined) return "";
  const atPlayhead = (time: number) =>
    Math.abs(time - activeTime) <= DIRECTOR_KEYFRAME_EPSILON;
  const position =
    track.kind === "transform"
      ? track.keyframes.find((keyframe) => atPlayhead(keyframe.time))?.value
          .position
      : track.kind === "camera"
        ? track.keyframes.find((keyframe) => atPlayhead(keyframe.time))?.value
            .transform.position
        : null;
  if (!position) return "";
  return position
    .map((value: number) => String(Number(value.toFixed(3))))
    .join(",");
}

// Batch 591（源站 2026-10-01 实测）：播放头位置 / 总时长都是可编辑文本框，
// 46×24、12px 居中、无描边（border-width 0），值随单位切换格式——
//   s  模式：两位小数（0.00 / 10.00）
//   ms 模式：整数毫秒（0 / 10000）
// 两框连体：左框 radius 8px 0 0 8px、右框全 0。回车或失焦提交，无法解析
// 时回滚到上一个合法值（沿用 batch 588 读数行已在源站实测通过的同一模式）。
function TimelineTimeField({
  testId,
  ariaLabel,
  className,
  value,
  unit,
  onCommit,
}: {
  testId: "time" | "duration";
  ariaLabel: string;
  className: string;
  value: number;
  unit: DirectorTimeUnit;
  onCommit: (seconds: number) => void;
}) {
  const format = (seconds: number) =>
    unit === "s" ? seconds.toFixed(2) : String(Math.round(seconds * 1000));
  const parse = (raw: string) =>
    unit === "s" ? Number(raw) : Number(raw) / 1000;
  const [draft, setDraft] = useState(() => format(value));
  useEffect(() => {
    setDraft(format(value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, unit]);
  const commit = (raw: string) => {
    const parsed = parse(raw.trim());
    if (Number.isFinite(parsed)) {
      onCommit(parsed);
    } else {
      setDraft(format(value));
    }
  };
  return (
    <input
      type="text"
      inputMode="decimal"
      data-director-timeline-time={testId === "time" ? value.toFixed(3) : undefined}
      data-director-timeline-duration={testId === "duration" ? value.toFixed(3) : undefined}
      data-director-time-field={testId}
      data-director-time-field-unit={unit}
      aria-label={ariaLabel}
      value={draft}
      spellCheck={false}
      onChange={(event) => {
        setDraft(event.target.value);
        commit(event.target.value);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") commit(event.currentTarget.value);
      }}
      onBlur={() => setDraft(format(value))}
      className={cn(
        // Batch 601（源站实测 class 逐字）：
        // `h-6 border-0 bg-white/10 px-0 text-center text-[12px] tabular-nums
        //  leading-none text-[#F7F7F7] outline-none transition-colors
        //  placeholder:text-white/30 hover:bg-white/[0.16]
        //  focus:bg-white/[0.18] focus:ring-1 focus:ring-[#5DDCFF]/70 w-[46px]`
        "h-6 w-[46px] shrink-0 border-0 bg-white/10 px-0 text-center text-[12px] tabular-nums leading-none",
        "text-[#F7F7F7] outline-none transition-colors placeholder:text-white/30",
        "hover:bg-white/[0.16] focus:bg-white/[0.18] focus:ring-1 focus:ring-[#5DDCFF]/70",
        className,
      )}
    />
  );
}

export function DirectorTimeline({
  trailing,
}: {
  /** Batch 596: 源站时间轴工具条右端除了缩放簇还挂着「导出视频到画布」
   *  ((1804,1025) 108x28)，clone 原来把它放在顶栏。用这个插槽把归属组件
   *  传进来，避免 DirectorTimeline 反向依赖 DirectorDesk 的状态。 */
  trailing?: ReactNode;
}) {
  const timeline = useDirectorStore((state) => state.timeline);
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const setTimelineTime = useDirectorStore((state) => state.setTimelineTime);
  // Batch 591: 源站时间单位切换（s <-> ms）
  const setTimelineDuration = useDirectorStore(
    (state) => state.setTimelineDuration,
  );
  const [timeUnit, setTimeUnit] = useState<DirectorTimeUnit>(
    DIRECTOR_DEFAULT_TIME_UNIT,
  );
  // Batch 591/592: 源站时间轴高 182px；「时间线最小化」把它收成 88px
  // ——工具栏整条保留，只有轨道区收起，按钮同时变成「展开时间线」。
  const [timelineCollapsed, setTimelineCollapsed] = useState(false);
  // Batch 607（源站 2026-10-01 实测）：面板顶边有一条 1920x8 @(0,1021) 的
  // 拖拽把手 `absolute inset-x-0 top-0 z-40 h-2 cursor-ns-resize`，实测
  // elementFromPoint 落在把手中心命中的就是把手本身（z-40 在头行 z-30 之上，
  // 所以它盖住整条 36px 头行的上沿 8px）。拖它调时间轴总高。
  //
  // 高度是**视图态**：按 batch 599 的结论（文档 schema 故意不含视图态
  // 字段，zoom 走同一条路）它不进持久化 schema，因此就放在组件本地，
  // 与 `timelineCollapsed` 同级。量程 88（收起档）..420 是 clone 自定的
  // ——源站的拖拽量程**未取证**（拖它会改用户真实工程里的面板高度）。
  // Batch 608：高度从组件本地 state 上提到 directorStore（视图态，不进持久化
  // schema），好让「动画时间轴」开关与拖拽把手操作同一份状态。
  const timelinePanelOpen = useDirectorStore((state) => state.timelinePanelOpen);
  const timelineHeight = useDirectorStore((state) => state.timelineHeight);
  const setTimelineHeight = useDirectorStore((state) => state.setTimelineHeight);
  const resizeDragRef = useRef<{ pointerId: number; startY: number; startHeight: number } | null>(
    null,
  );
  const beginHeightResize = (event: React.PointerEvent<HTMLDivElement>) => {
    if (timelineCollapsed) return;
    event.preventDefault();
    event.stopPropagation();
    (event.target as HTMLElement).setPointerCapture?.(event.pointerId);
    resizeDragRef.current = {
      pointerId: event.pointerId,
      startY: event.clientY,
      startHeight: timelineHeight,
    };
  };
  const moveHeightResize = (event: React.PointerEvent<HTMLDivElement>) => {
    const drag = resizeDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    // 往上拖（clientY 变小）面板变高，所以取负号
    const next = drag.startHeight - (event.clientY - drag.startY);
    setTimelineHeight(next);
  };
  const endHeightResize = (event: React.PointerEvent<HTMLDivElement>) => {
    if (resizeDragRef.current?.pointerId !== event.pointerId) return;
    resizeDragRef.current = null;
    (event.target as HTMLElement).releasePointerCapture?.(event.pointerId);
  };
  // Batch 593: 源站对象行首列的「收起属性 / 展开属性」只收起**该对象的轨道
  // 行**，对象行本身保留，时间轴总高不变（实测收起前后面板都是 130px）。
  // 与右列的「时间线最小化」（整条收起）是两个独立控件。
  const [collapsedObjects, setCollapsedObjects] = useState<
    Record<string, boolean>
  >({});
  const setTimelinePlaying = useDirectorStore(
    (state) => state.setTimelinePlaying,
  );
  // Batch 552/553: 源站「+ 新建轨道」（截图 48）——为选中的角色/摄像机
  // 创建变换轨道；无合格选中时禁用（源站 onboarding 提示需先选择）。
  const selectedObjectKind = useDirectorStore((state) =>
    state.selectedObjectId
      ? state.objects.find((o) => o.id === state.selectedObjectId)?.kind
      : undefined,
  );
  const createTrackForSelectedObject = useDirectorStore(
    (state) => state.createTrackForSelectedObject,
  );
  const trackCreatable =
    selectedObjectKind === "character" || selectedObjectKind === "camera";
  // Batch 556: 源站截图 48——时间线打开时的 1/5 引导气泡（请选择一个
  // 角色或者摄像机后，可新建轨道 + 跳过/下一步）；步骤 2-5 未采样，
  // 跳过/下一步均收起气泡（CLONE_DECISION）。
  // Batch 572: 源站实测（截图 58，batch 571）——气泡收起状态跨重载持久
  // （浏览器重启后仍收起）；clone 以 localStorage 对齐该持久化语义。
  const [coachDismissed, setCoachDismissed] = useState(() => {
    try {
      return window.localStorage.getItem("director-timeline-coach-dismissed") === "1";
    } catch {
      return false;
    }
  });
  const dismissCoach = () => {
    setCoachDismissed(true);
    try {
      window.localStorage.setItem("director-timeline-coach-dismissed", "1");
    } catch {
      /* storage 不可用时仅会话内收起 */
    }
  };
  const advanceTimeline = useDirectorStore((state) => state.advanceTimeline);
  const toggleTimelineLoop = useDirectorStore(
    (state) => state.toggleTimelineLoop,
  );
  const toggleAutoKeyframe = useDirectorStore(
    (state) => state.toggleAutoKeyframe,
  );
  const setTimelineZoom = useDirectorStore((state) => state.setTimelineZoom);
  const selectTimelineTrack = useDirectorStore(
    (state) => state.selectTimelineTrack,
  );
  const selectTimelineKeyframe = useDirectorStore(
    (state) => state.selectTimelineKeyframe,
  );
  const addTimelineTrack = useDirectorStore(
    (state) => state.addTimelineTrack,
  );
  const removeTimelineTrack = useDirectorStore(
    (state) => state.removeTimelineTrack,
  );
  const addTimelineKeyframe = useDirectorStore(
    (state) => state.addTimelineKeyframe,
  );
  const deleteTimelineKeyframe = useDirectorStore(
    (state) => state.deleteTimelineKeyframe,
  );
  const setTimelineEditorMode = useDirectorStore(
    (state) => state.setTimelineEditorMode,
  );
  const createMotionPath = useDirectorStore(
    (state) => state.createMotionPath,
  );
  const applyCameraMotionPreset = useDirectorStore(
    (state) => state.applyCameraMotionPreset,
  );
  const startMotionPathDrawing = useDirectorStore(
    (state) => state.startMotionPathDrawing,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const toggleMotionPathEnabled = useDirectorStore(
    (state) => state.toggleMotionPathEnabled,
  );
  const toggleMotionPathOrient = useDirectorStore(
    (state) => state.toggleMotionPathOrient,
  );
  const deleteMotionPath = useDirectorStore(
    (state) => state.deleteMotionPath,
  );
  const timelineRootRef = useRef<HTMLElement>(null);
  const timelineCanvasRef = useRef<HTMLDivElement>(null);
  const scrubCleanupRef = useRef<(() => void) | null>(null);
  const pathTriggerRef = useRef<HTMLButtonElement>(null);
  const pathMenuRef = useRef<HTMLDivElement>(null);
  const presetTriggerRef = useRef<HTMLButtonElement>(null);
  const presetPanelRef = useRef<HTMLDivElement>(null);
  const [pathMenuLeft, setPathMenuLeft] = useState<number | null>(null);
  const [presetPanelLeft, setPresetPanelLeft] = useState<number | null>(null);
  const [presetMode, setPresetMode] =
    useState<DirectorCameraMotionPresetMode>("replace");

  useEffect(() => {
    return () => {
      scrubCleanupRef.current?.();
    };
  }, []);

  useEffect(() => {
    if (!timeline.isPlaying) return;
    let frame = 0;
    let previous = performance.now();
    const tick = (now: number) => {
      const deltaSeconds = Math.min((now - previous) / 1000, 0.1);
      previous = now;
      advanceTimeline(deltaSeconds);
      if (useDirectorStore.getState().timeline.isPlaying) {
        frame = window.requestAnimationFrame(tick);
      }
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [advanceTimeline, timeline.isPlaying]);

  // Batch 595（源站 2026-10-01 逐像素实测标尺 canvas）：
  // 细分**恒为 0.1s**，不随缩放改变——zoom 42 与 zoom 100 下都是 100 条刻度
  // （总时长 10s），只是间距随 zoom 线性放大（实测主刻度间距 211px @42、
  // 500px @100）。每第 10 条是主刻度（1s），带 `{n}s` 标签。
  // 竖直方向（canvas 顶为 0，2x DPR 折算回 CSS）：
  //   标签带  y 5.0 – 13.5，字色 #9d9d9d，字号约 12px（该带高 8.5px）
  //   主刻度  y 22.5 – 31.0（高 8.5px），色 #878787
  //   次刻度  y 27.5 – 31.0（高 3.5px），色 #686868
  //   标尺底 #212121，刻度带下方是轨道道底 #2a2a2a
  const ticks = useMemo(() => {
    const step = DIRECTOR_RULER_TICK_SECONDS;
    const count = Math.round(timeline.duration / step);
    return Array.from({ length: count + 1 }, (_, index) => index * step);
  }, [timeline.duration]);
  const selectedTrack =
    timeline.tracks.find((track) => track.id === timeline.selectedTrackId) ??
    null;
  const selectedPath = selectedTrack?.motionPathId
    ? timeline.motionPaths.find(
        (path) => path.id === selectedTrack.motionPathId,
      ) ?? null
    : null;
  const selectedTrackObject =
    selectedTrack?.kind === "group"
      ? undefined
      : objects.find((object) => object.id === selectedTrack?.objectId);
  const selectedTrackLocked =
    selectedTrack?.kind === "group"
      ? Boolean(
          groups
            .find((group) => group.id === selectedTrack.groupId)
            ?.characterIds.some((objectId) =>
              objects.some((object) => object.id === objectId && object.locked),
            ),
        )
      : Boolean(selectedTrackObject?.locked);
  const cameraFollowActive = Boolean(
    selectedTrackObject?.camera?.followTargetId,
  );
  const selectedPresetApplication =
    timeline.cameraMotionPreset.application?.trackId === selectedTrack?.id
      ? timeline.cameraMotionPreset.application
      : null;
  const presetError = timeline.cameraMotionPreset.error;
  const selectedPresetError =
    presetError &&
    presetError.trackId === selectedTrack?.id &&
    presetError.mode === presetMode
      ? presetError
      : null;
  const hasSelectedObjectTrack = timeline.tracks.some(
    (track) =>
      selectedGroupId
        ? track.kind === "group" && track.groupId === selectedGroupId
        : track.objectId === selectedObjectId && track.kind !== "pose",
  );
  // Batch 594（源站 2026-10-01 实测，总时长 = 10000ms 时逐点采样）：
  //   zoom   0  16  31   49   64   82  100
  //   标尺宽 1598 1598 1598 2473 3220 4116 5012
  // 49/64/82/100 四点严格共线，斜率 49.78 px/zoom、截距 ≈33.6px；zoom ≤ 31 时
  // 宽度等于容器宽（1598），即源站把内容宽度夹在容器宽上。换成「每秒像素」
  // 就是 3.36 + 4.978*zoom px/s，按总时长线性外推（**外推是推断**：源站只有
  // 10s 这一个采样点，改总时长要写用户项目，没测）。
  // 640px 的下限是 clone 自己的（源站是夹到容器宽，容器宽是动态的）。
  const timelineWidth = Math.max(
    640,
    timeline.duration * (3.36 + 4.978 * timeline.zoom),
  );
  const playheadPosition =
    timeline.duration > 0
      ? (timeline.currentTime / timeline.duration) * 100
      : 0;

  // Batch 593: 源站轨道区左列是**两级**的——每个「拥有轨道的对象」一行对象行，
  // 其下挂该对象的若干轨道行。源站当前只有一个对象（主机位）且只有一条
  // 轨道（位置），所以「按对象分组」这一步是从 DOM 结构 + 栅格列宽推断的
  // （对象行 16px/1fr/220px，轨道行 40px/36px/78px/1fr，两者不可能同层）。
  const timelineTrackGroups = useMemo(() => {
    const grouped = new Map<
      string,
      {
        key: string;
        objectId: string;
        tracks: DirectorTimelineTrack[];
        objectName: string;
      }
    >();
    for (const track of timeline.tracks) {
      const key =
        track.kind === "group"
          ? `group:${track.groupId}`
          : `object:${track.objectId}`;
      const existing = grouped.get(key);
      if (existing) {
        existing.tracks.push(track);
        continue;
      }
      const object = objects.find((item) => item.id === track.objectId);
      const group =
        track.kind === "group"
          ? groups.find((item) => item.id === track.groupId)
          : undefined;
      grouped.set(key, {
        key,
        objectId: track.objectId,
        tracks: [track],
        objectName: object?.name ?? group?.label ?? "对象",
      });
    }
    return [...grouped.values()];
  }, [timeline.tracks, objects, groups]);

  // Batch 598: 源站的播放头只画在**对象行车道**里，且该项目只有一个对象，
  // 测不出多对象时它落在哪一条。clone 选「当前选中轨道所属对象」那条车道，
  // 没有任何轨道被选中时退回第一个对象（clone-only 决策，见上方常量注释）。
  const playheadGroupKey = useMemo(() => {
    const owning = timelineTrackGroups.find((group) =>
      group.tracks.some((track) => track.id === timeline.selectedTrackId),
    );
    return (owning ?? timelineTrackGroups[0])?.key ?? null;
  }, [timelineTrackGroups, timeline.selectedTrackId]);

  useEffect(() => {
    if (pathMenuLeft === null) return;
    const close = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        (pathMenuRef.current?.contains(target) ||
          pathTriggerRef.current?.contains(target))
      ) {
        return;
      }
      setPathMenuLeft(null);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPathMenuLeft(null);
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [pathMenuLeft]);

  useEffect(() => {
    if (presetPanelLeft === null) return;
    const close = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        (presetPanelRef.current?.contains(target) ||
          presetTriggerRef.current?.contains(target))
      ) {
        return;
      }
      setPresetPanelLeft(null);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPresetPanelLeft(null);
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [presetPanelLeft]);

  const togglePathMenu = () => {
    if (cameraFollowActive) return;
    setPresetPanelLeft(null);
    if (pathMenuLeft !== null) {
      setPathMenuLeft(null);
      return;
    }
    const root = timelineRootRef.current?.getBoundingClientRect();
    const trigger = pathTriggerRef.current?.getBoundingClientRect();
    if (!root || !trigger) return;
    setPathMenuLeft(
      Math.max(8, Math.min(trigger.left - root.left, root.width - 176)),
    );
  };

  const togglePresetPanel = () => {
    if (selectedTrack?.kind !== "camera" || cameraFollowActive) return;
    if (presetPanelLeft !== null) {
      setPresetPanelLeft(null);
      return;
    }
    const root = timelineRootRef.current?.getBoundingClientRect();
    const trigger = presetTriggerRef.current?.getBoundingClientRect();
    if (!root || !trigger) return;
    setPathMenuLeft(null);
    setPresetPanelLeft(
      Math.max(8, Math.min(trigger.left - root.left, root.width - 312)),
    );
  };

  const seekFromClientX = (clientX: number) => {
    const element = timelineCanvasRef.current;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    const progress = Math.min(
      Math.max((clientX - rect.left) / rect.width, 0),
      1,
    );
    setTimelineTime(progress * timeline.duration);
  };

  const beginScrub = (event: ReactPointerEvent<HTMLElement>) => {
    if (
      event.target instanceof Element &&
      event.target.closest("[data-director-keyframe-id]")
    ) {
      return;
    }
    event.preventDefault();
    setTimelinePlaying(false);
    seekFromClientX(event.clientX);

    const target = event.currentTarget;
    const pointerId = event.pointerId;
    let active = true;
    const handleMove = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId !== pointerId) return;
      seekFromClientX(pointerEvent.clientX);
    };
    const cleanup = () => {
      if (!active) return;
      active = false;
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
      window.removeEventListener("pointercancel", handleCancel);
      window.removeEventListener("blur", handleBlur);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      target.removeEventListener("lostpointercapture", handleLostPointerCapture);
      if (target.hasPointerCapture(pointerId)) {
        target.releasePointerCapture(pointerId);
      }
      if (scrubCleanupRef.current === cleanup) {
        scrubCleanupRef.current = null;
      }
    };
    const handleUp = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId === pointerId) cleanup();
    };
    const handleCancel = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId === pointerId) cleanup();
    };
    const handleBlur = () => cleanup();
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") cleanup();
    };
    const handleLostPointerCapture = () => cleanup();

    scrubCleanupRef.current?.();
    scrubCleanupRef.current = cleanup;
    target.setPointerCapture(pointerId);
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
    window.addEventListener("pointercancel", handleCancel);
    window.addEventListener("blur", handleBlur);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    target.addEventListener("lostpointercapture", handleLostPointerCapture);
  };

  // Batch 608：源站底部胶囊里那枚「动画时间轴」是 `aria-pressed=true` 的开关
  // （源站实测），时间轴面板当前可见。clone 原先时间轴常驻、无整条开关。
  // 语义取「开关整条时间轴面板的可见性」——这是按钮名 + aria-pressed 开态 +
  // 面板可见三者共同支持的读法，**属推断**：源站那枚按钮的点击行为没有取证
  // （点它可能改用户真实工程），所以不声称其确切结果。这里落成一个真实可用
  // 的开关，而不是一个不工作的按钮。
  //
  // 与「时间线最小化」（182 -> 88，面板仍在）是两个独立语义，互不影响。
  if (!timelinePanelOpen) return null;

  return (
    <section
      ref={timelineRootRef}
      data-director-timeline
      data-director-timeline-mode={timeline.editorMode}
      data-director-timeline-collapsed={timelineCollapsed ? "true" : "false"}
      data-director-timeline-height={timelineCollapsed ? 88 : timelineHeight}
      className={cn(
        // Batch 607（源站实测 1920x130 @(0,1020)）：
        //   pointer-events-auto.relative.flex.w-full.min-w-0.flex-col
        //   .overflow-hidden.rounded-tl-none.rounded-tr-none
        //   .border-t.border-white/10.bg-[#1f1f1f].text-white
        //   .shadow-[0_-18px_48px_rgba(0,0,0,0.24)].backdrop-blur-xl
        // 一处有意保留：源站是 `overflow-hidden`，clone 仍是 `overflow-visible`
        // ——时间轴上有若干绝对定位的下拉/浮层（轨道右键菜单、曲线编辑器等）
        // 依赖不被裁切；改 hidden 要连带把这些浮层 portal 出去，超出本批范围。
        // 记录在案，不假装一致。
        //
        // Batch 611 修：这一层需要压过属性面板列（`z-30`）。原因是本 section
        // 带 `backdrop-blur-xl` —— **backdrop-filter 会创建层叠上下文**，于是
        // 导出面板的 `z-50` 被关在这个上下文里、再也够不到外面的列；而本
        // section 自身 `z-index: auto`，输给了列的 z-30。症状是导出面板向上
        // 弹出后，其「比例」三枚按钮被属性面板的字段行盖住点不动
        // （batch 40 的 `9:16` 点击超时即此）。
        // 布局上时间轴与属性面板列并不重叠（各自占一格），所以抬到 z-40
        // 不改变版面，只让面板/菜单类浮层能盖住右列。
        "z-40 pointer-events-auto relative flex w-full min-w-0 shrink-0 flex-col overflow-visible rounded-tl-none rounded-tr-none border-t border-white/10 bg-[#1f1f1f] text-white shadow-[0_-18px_48px_rgba(0,0,0,0.24)] backdrop-blur-xl max-[899px]:h-[176px]",
        // 源站实测：展开 1920x182 @(0,968)；收起 1920x88 @(0,1062)
        timelineCollapsed
          ? "h-[88px]"
          : cn(
              "h-[182px]",
              timelineHeight !== DIRECTOR_TIMELINE_DEFAULT_HEIGHT && "h-auto",
            ),
      )}
      style={
        timelineCollapsed || timelineHeight === DIRECTOR_TIMELINE_DEFAULT_HEIGHT
          ? undefined
          : { height: timelineHeight }
      }
    >
      {/* 源站顶边 8px 拖拽把手（见 beginHeightResize 处的实测记录）。
          z-40 压在头行 z-30 之上，与源站一致。把手本身透明、无子节点，
          拖拽全靠 pointer 事件（pointer capture 在把手自身上）。 */}
      <div
        data-director-timeline-resize-handle
        aria-label="拖动调整时间轴高度"
        role="separator"
        aria-orientation="horizontal"
        onPointerDown={beginHeightResize}
        onPointerMove={moveHeightResize}
        onPointerUp={endHeightResize}
        onPointerCancel={endHeightResize}
        className="absolute inset-x-0 top-0 z-40 h-2 cursor-ns-resize"
      />
      {/* Batch 593（源站 2026-10-01 CDP 实测重做）：引导气泡在源站是
          **fixed** 定位的独立浮层，不在时间轴内部——
            260 x 114 @ (163, 920) @1920x1150
            style="left: 163px; top: 920px; width: 260px"
            rounded-xl(12) / border-white/[0.08] / bg-[#242424] / p-4(16)
            shadow-[0_4px_16px_rgba(0,0,0,0.18)] / z-[1]
            正文 h-10 overflow-hidden text-[12px] leading-[19.2px] text-white/90
            页脚 mt-3 flex justify-between gap-1
              1/5  : min-w-0 flex-1 text-[14px] leading-3 text-white/55
              跳过  : h-7 rounded-lg bg-transparent px-3 text-[13px] text-white/70
              下一步: h-7 rounded-lg bg-white/10 px-3 text-[13px] text-white/85
          top 用 `calc(100vh - 230px)` 表达（1150-230=920），这样换视口高度时
          仍然贴在时间轴上方而不是压在轨道行上——clone 之前的
          `absolute bottom-3 left-3` 落在 182px 时间轴内部、宽 300px，会盖住
          320px 宽轨道列的第二行。
          一处有意偏离：源站气泡是 `pointer-events-auto`，clone 改成
          `pointer-events-none` + 两个按钮 `pointer-events-auto`。源站工具条
          左格只有 320px，气泡只压住「新建轨道」顶端 7px；clone 的工具条是
          一整行（多了预设运镜/曲线编辑器/缓入等 clone 能力），同一块屏幕会被
          压住一整排控件，文字区吞点击会让工具条在引导期间不可用。外观与
          几何完全按实测。步骤 2-5 仍未采样，跳过/下一步都只收起
          （沿用 batch 556 的 clone 决策）。收起状态跨重载持久沿用 batch 572。 */}
      {!coachDismissed ? (
        <div
          data-director-timeline-coachmark
          role="status"
          className="pointer-events-none fixed left-[163px] z-[1] w-[260px] overflow-hidden rounded-xl border border-white/[0.08] bg-[#242424] p-4 text-white shadow-[0_4px_16px_rgba(0,0,0,0.18)]"
          style={{ top: "calc(100vh - 230px)" }}
        >
          <div className="h-10 overflow-hidden text-[12px] font-normal leading-[19.2px] text-white/90">
            请选择一个角色或者摄像机后，可新建轨道
          </div>
          <div className="mt-3 flex items-center justify-between gap-1">
            <span className="min-w-0 flex-1 text-[14px] font-normal leading-3 text-white/55">
              1/5
            </span>
            <button
              type="button"
              data-director-coachmark-skip
              onClick={dismissCoach}
              className="pointer-events-auto h-7 rounded-lg bg-transparent px-3 text-[13px] font-normal leading-none text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              跳过
            </button>
            <button
              type="button"
              data-director-coachmark-next
              onClick={dismissCoach}
              className="pointer-events-auto h-7 rounded-lg bg-white/10 px-3 text-[13px] font-normal leading-none text-white/85 transition-colors hover:bg-white/15 hover:text-white"
            >
              下一步
            </button>
          </div>
        </div>
      ) : null}
      {/* Batch 593（源站 2026-10-01 实测）：工具条是 z-30 覆盖层，高 36px
          （`h-[36px]` + `px-2 py-1`），**没有**任何标题——之前 clone 自造的
          「动画时间轴」h2 已删除。左格 320px 放播放/自动帧/循环/读数/单位/
          新建轨道，右格放标尺缩放与导出。
          Batch 601（源站实测 /tmp/src593/probe47）：左格前七项的**逐项间隙**
          不是统一的 4px——播放/自动帧/循环三者 gap 0，之后 4px 跳到读数组，
          读数组内 1px 连体，再 15px 才到「新建轨道」。宽度 26/24/26/46/46/33/82。
          所以这里把 header 的 gap 归零，各段自己带边距。 */}
      <header
        data-director-timeline-controls
        className="flex h-9 shrink-0 items-center gap-0 border-b border-white/[0.07] px-2 py-1 pr-[260px]"
      >
        {/* Batch 618（移动端命中普查）：左格内容**不得渗进** `pr-[260px]`
            这块给右格预留的区域。
            之前的读法是「header 自己 overflow-x-auto + pr-260」，但 CSS 里
            padding-right 属于**滚动溢出区**——内容溢出 content box 之后会一直
            画到 padding box 边缘为止。桌面 1920 下左格内容 1044px 远小于
            1392px 的窗口，根本不溢出，于是看不出问题；390 下窗口只有
            390-8-260=122px，内容 1044px 溢出 922px，全都画进了预留区，而
            右格是不透明的 `bg-[#212121]`（`absolute right-0` 244px 宽）——
            于是「总时长」「时间单位」「新建轨道」「预设运镜」四枚控件**画在
            不透明块底下**：命中测试打到的是右格本身，点不动，也看不出还有
            内容（无滚动条提示）。1024 下同样溢出，但溢出部分落在视口之外，
            只被算作 clipped，所以此前两轮普查（batch 617 的 1920/1024 腿）
            都没报出来。
            修法：把滚动容器下沉到内层 div，header 自身不再滚动，于是裁切线
            落在 content box 右缘（x=130），内容滚过去也不会画进预留区——
            与 1024 的表现一致（clipped，横向滚一下就到）。
            桌面几何一字未动：内层 div 在 1920 下宽 1392 > 1044，不产生滚动条，
            子节点各自的 ml/gap 都在内层 flex 里，位置逐像素不变。 */}
        <div
          data-director-timeline-controls-scroll
          className="flex min-w-0 flex-1 items-center gap-0 overflow-x-auto"
          >
          <button
            type="button"
            data-director-playback
            aria-label={timeline.isPlaying ? "暂停" : "播放"}
            title={timeline.isPlaying ? "暂停" : "播放"}
            aria-pressed={timeline.isPlaying}
            onClick={() => setTimelinePlaying(!timeline.isPlaying)}
            className="flex h-6 w-[26px] shrink-0 items-center justify-center rounded-md text-white/80 transition-colors hover:bg-white/10 hover:text-white"
          >
            {timeline.isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>
          {/* Batch 591（源站 2026-10-01 实测，工具栏自左至右）：播放 /
              自动帧 / 循环播放 / 播放头位置 / 总时长 / 时间单位 / 新建轨道。
              自动帧此前排在循环播放之后，与源站顺序不符，本批前移。 */}
          {/* Batch 573: 源站 CDP 枚举（截图 55，24px 图标钮 aria-label 自动帧，
              无文字）——自动帧 toggle 对齐为图标钮；batch 36 的 data 属性与
              aria-pressed 合同保留。 */}
          <button
            type="button"
            data-director-auto-keyframe
            aria-label="自动帧"
            title="自动帧"
            aria-pressed={timeline.autoKeyframe}
            onClick={toggleAutoKeyframe}
            className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/10 hover:text-white",
              timeline.autoKeyframe && "bg-white/10 text-white",
            )}
          >
            {/* Batch 601（源站 4x 截图实测）：源站「自动帧」里是一个 14px
                （`svg.h-3.5.w-3.5`）的**秒表**图标，不是圆点。 */}
            <Timer size={14} />
          </button>
          <button
            type="button"
            data-director-loop
            aria-label="循环播放"
            title="循环播放"
            aria-pressed={timeline.loop}
            onClick={toggleTimelineLoop}
            className={cn(
              "flex h-6 w-[26px] shrink-0 items-center justify-center rounded-md text-[12px] leading-none transition-colors",
              timeline.loop
                ? "bg-white/10 text-neutral-50"
                : "text-white/80 hover:bg-white/10 hover:text-white",
            )}
          >
            <Repeat2 size={14} />
          </button>
          {/* Batch 591：源站两个读数是**连体**的可编辑文本框（各 46×24、
              12px 居中）。Batch 601 精测补齐：左框 radius 8px 0 0 8px、
              **中框 radius 0**、单位钮 radius 0 8px 8px 0，三者 gap 1px；
              底色是 `bg-white/10`（不是 clone 的 `#222`），内边距 0，
              文字 12px `#F7F7F7`，带 hover `bg-white/[0.16]` 与
              focus `bg-white/[0.18] + ring-1 ring-[#5DDCFF]/70`。
              值随单位切换：ms 模式整数毫秒（0 / 10000，源站默认），
              s 模式两位小数（0.00 / 10.00）。aria 逐字为 播放头位置 / 总时长。 */}
          <div className="ml-1 flex shrink-0 items-center gap-px">
          <TimelineTimeField
            testId="time"
            ariaLabel="播放头位置"
            className="rounded-l-lg"
            value={timeline.currentTime}
            unit={timeUnit}
            onCommit={(seconds) =>
              setTimelineTime(Math.min(Math.max(seconds, 0), timeline.duration))
            }
          />
          <TimelineTimeField
            testId="duration"
            ariaLabel="总时长"
            className=""
            value={timeline.duration}
            unit={timeUnit}
            onCommit={setTimelineDuration}
          />
          <button
            type="button"
            data-director-time-unit
            aria-label={timeUnit === "s" ? "切换时间单位为 ms" : "切换时间单位为 s"}
            title={timeUnit === "s" ? "切换时间单位为 ms" : "切换时间单位为 s"}
            onClick={() => setTimeUnit((unit) => (unit === "s" ? "ms" : "s"))}
            className="flex h-6 w-[33px] shrink-0 items-center justify-center rounded-r-lg bg-white/10 px-2 text-[12px] tabular-nums leading-none text-[#F7F7F7] transition-colors hover:bg-white/[0.16] hover:text-white"
          >
            {timeUnit}
          </button>
          </div>
          <button
            type="button"
            data-director-add-track
            // Batch 591: 源站该按钮的可及名逐字是这句（描述「先选中再建立」
            // 的前置条件），不是「新建轨道」；clone 的 title 仍保留更完整的
            // 禁用提示（含 coachmark 指引），二者并存。
            // Batch 601（源站实测）：按钮**显示文字**是「新建轨道」（82×24，
            // 13px），可及名才是那句前置条件提示——两者并存，不是二选一。
            aria-label="选中角色、道具或分组后建立轨道"
            title={
              trackCreatable
                ? "新建轨道"
                : "请选择一个角色或者摄像机后，可新建轨道"
            }
            disabled={!trackCreatable}
            onClick={() => createTrackForSelectedObject()}
            className={cn(
              "ml-[15px] flex h-6 w-[82px] shrink-0 items-center justify-center gap-1 rounded-lg px-2 text-[13px] leading-none transition-colors",
              trackCreatable
                ? "text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
                : "text-[#525252]",
            )}
          >
            <Plus size={13} />
            新建轨道
          </button>
          {/* Batch 593：源站工具条只有七项（播放/自动帧/循环播放/播放头位置/
              总时长/时间单位/新建轨道），**没有**「上一/下一关键帧」——它们在
              源站位于每条轨道行内（见下方轨道行）。本批把这两个按钮从工具条
              移到轨道行，工具条顺序与源站逐位一致。 */}
          <button
            ref={presetTriggerRef}
            type="button"
            data-director-camera-preset-trigger
            disabled={selectedTrack?.kind !== "camera" || cameraFollowActive}
            title={
              cameraFollowActive
                ? "跟随目标时不可使用预设运镜"
                : undefined
            }
            aria-expanded={presetPanelLeft !== null}
            onClick={togglePresetPanel}
            className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
          >
            <Camera size={13} />
            预设运镜
          </button>
          {cameraFollowActive && selectedTrack?.kind === "camera" ? (
            <span
              data-director-camera-preset-error
              className="shrink-0 text-[10px] text-[#c9a36c]"
            >
              跟随目标时不可使用预设运镜
            </span>
          ) : null}
          <button
            ref={pathTriggerRef}
            type="button"
            data-director-create-motion-path
            disabled={
              !selectedTrack ||
              selectedTrack.kind === "pose" ||
              selectedTrack.kind === "group" ||
              cameraFollowActive ||
              selectedTrackLocked
            }
            title={
              cameraFollowActive
                ? "请先关闭机位跟随，再绘制轨迹"
                : undefined
            }
            aria-expanded={pathMenuLeft !== null}
            onClick={togglePathMenu}
            className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
          >
            <Route size={13} />
            创建运动轨迹
          </button>
          {cameraFollowActive ? (
            <span
              data-director-camera-follow-conflict
              className="shrink-0 text-[10px] text-[#c9a36c]"
            >
              请先关闭机位跟随，再绘制轨迹
            </span>
          ) : null}
          <button
            type="button"
            data-director-open-curve-editor
            disabled={!selectedTrack || selectedTrackLocked}
            aria-pressed={timeline.editorMode === "curve"}
            onClick={() => setTimelineEditorMode("curve")}
            className={cn(
              "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]",
              timeline.editorMode === "curve" &&
                "bg-white/[0.07] text-[#5ddcff]",
            )}
          >
            <ChartSpline size={13} />
            曲线编辑器
          </button>
          {selectedPath ? (
            <>
              <button
                type="button"
                data-director-motion-path-enabled={selectedPath.id}
                aria-label="启用曲线"
                title="启用曲线"
                aria-pressed={selectedPath.enabled}
                disabled={selectedTrackLocked}
                onClick={() => toggleMotionPathEnabled(selectedPath.id)}
                className={cn(
                  "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#777] hover:bg-white/[0.06] hover:text-white",
                  selectedPath.enabled && "bg-white/[0.07] text-[#5ddcff]",
                )}
              >
                <Route size={13} />
                启用曲线
              </button>
              {selectedTrack?.kind === "transform" ? (
                <button
                  type="button"
                  data-director-motion-path-orient={selectedPath.id}
                  aria-label="绑定对象沿路径朝向"
                  title="绑定对象沿路径朝向"
                  aria-pressed={selectedPath.orientToPath}
                  disabled={selectedTrackLocked}
                  onClick={() => toggleMotionPathOrient(selectedPath.id)}
                  className={cn(
                    "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#777] hover:bg-white/[0.06] hover:text-white",
                    selectedPath.orientToPath &&
                      "bg-white/[0.07] text-[#5ddcff]",
                  )}
                >
                  <Waypoints size={13} />
                  沿路径朝向
                </button>
              ) : null}
              <button
                type="button"
                data-director-delete-motion-path={selectedPath.id}
                aria-label="删除曲线"
                title="删除曲线"
                disabled={selectedTrackLocked}
                onClick={() => deleteMotionPath(selectedPath.id)}
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d]"
              >
                <Trash2 size={13} />
              </button>
            </>
          ) : null}
          {/* Batch 593: 这个「轨道」按钮原先和工具条里的「+ 新建轨道」共用
              data-director-add-track，按该属性定位会命中两个元素（batch 45 的
              strict mode violation）。源站工具条只有「新建轨道」一个建轨入口，
              这个是 clone 的手动补建入口，属性独立命名。 */}
          <button
            type="button"
            data-director-add-track-manual
            disabled={
              (!selectedObjectId && !selectedGroupId) ||
              hasSelectedObjectTrack ||
              selectedTrackLocked
            }
            onClick={() => addTimelineTrack()}
            className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
          >
            <Plus size={13} />
            轨道
          </button>
          {/* Batch 593: 源站轨道行的四列栅格里没有删除位，删除轨道改挂在工具条
              「轨道」按钮之后（clone-only 能力的落位调整，aria 保持不变）。 */}
          <button
            type="button"
            data-director-remove-track
            aria-label={`移除${selectedTrack?.label ?? ""}轨道`}
            title="移除轨道"
            disabled={!selectedTrack || selectedTrackLocked}
            onClick={() => removeTimelineTrack()}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d] disabled:text-[#3f3f3f]"
          >
            <Trash2 size={13} />
          </button>
          <button
            type="button"
            data-director-add-keyframe
            disabled={!selectedTrack || selectedTrackLocked}
            onClick={() => addTimelineKeyframe()}
            className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
          >
            <DiamondPlus size={13} />
            添加关键帧
          </button>
          <button
            type="button"
            data-director-delete-keyframe
            aria-label="删除关键帧"
            title="删除关键帧"
            disabled={!timeline.selectedKeyframeId || selectedTrackLocked}
            onClick={() => deleteTimelineKeyframe()}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d] disabled:text-[#3f3f3f]"
          >
            <Trash2 size={13} />
          </button>
          <span className="mx-1 h-5 w-px shrink-0 bg-white/10" />
        </div>
      </header>

      {/* Batch 596（源站 2026-10-01 实测）：工具条是**两格**结构——左格可横向
          滚动（clone 工具条比源站长很多），右格 `absolute right-0 top-0`
          浮在上面装缩放簇 + 导出按钮，源站右格实测
          `absolute right-0 top-0 z-20 flex h-9 items-center gap-2 bg-[#212121] pr-2`
          244x36 @(1676,1021)。
          右格必须**在 header 之外**：header 是 `overflow-x-auto`，按 CSS 规范它
          的 overflow-y 会从 visible 变成 auto，于是向上弹出的导出面板会被裁掉
          （实测面板中心点命中的是 WebGL canvas 而不是面板）。 */}
      <div
        data-director-timeline-strip-right
        className="absolute right-0 top-0 z-30 flex h-9 items-center gap-2 bg-[#212121] pr-2"
      >
        {/* Batch 594（源站 2026-10-01 实测）：缩放簇是 120x36 的独立块
            `flex h-9 w-[120px] items-center gap-2 border-l border-white/[0.08]
            bg-[#212121] px-2`，里面**没有**放大镜图标——只有自绘轨道 + 最小化钮。
            轨道 71x16 容器 / 71x4 `rounded-full` `bg-white/40` / 12x12
            `rounded-full` `border-[#F7F7F7] bg-[#F7F7F7]` 圆钮，上面盖一层
            透明的原生 range（71x24）。量程 0-100，无 step 属性。 */}
        <div
          data-director-timeline-zoom-cluster
          className="flex h-9 w-[120px] shrink-0 items-center gap-2 border-l border-white/[0.08] bg-[#212121] px-2"
        >
          <div className="relative h-4 min-w-0 flex-1">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 overflow-hidden rounded-full bg-white/40"
            >
              <div
                className="h-full rounded-full bg-[#F7F7F7]"
                style={{ width: `${timeline.zoom}%` }}
              />
            </div>
            <div
              aria-hidden="true"
              className="pointer-events-none absolute top-1/2 h-3 w-3 rounded-full border border-[#F7F7F7] bg-[#F7F7F7]"
              style={{
                left: `${timeline.zoom}%`,
                transform: `translate(${timeline.zoom === 0 ? "0%" : "-50%"}, -50%)`,
              }}
            />
            <input
              type="range"
              aria-label="时间轴缩放"
              title="时间轴缩放"
              data-director-timeline-zoom
              min="0"
              max="100"
              value={timeline.zoom}
              onChange={(event) =>
                setTimelineZoom(Number(event.currentTarget.value))
              }
              className="absolute inset-x-0 top-1/2 m-0 h-6 w-full -translate-y-1/2 cursor-pointer appearance-none bg-transparent opacity-0"
            />
          </div>
          {/* Batch 592（源站实测）：收起按钮的可及名随状态翻转——
              展开时 `时间线最小化` @(1764,1027) 24×24，收起后同一位置变成
              `展开时间线` @(1764,1121)。收起只收轨道区，工具条整条保留。
              Batch 594 把它收进缩放簇（源站它就在簇内 `w-[120px]` 里）。 */}
          <button
            type="button"
            data-director-timeline-collapse
            aria-label={timelineCollapsed ? "展开时间线" : "时间线最小化"}
            title={timelineCollapsed ? "展开时间线" : "时间线最小化"}
            aria-pressed={timelineCollapsed}
            onClick={() => setTimelineCollapsed((collapsed) => !collapsed)}
            className="group relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-white/65 transition-colors hover:bg-white/10 hover:text-white"
          >
            {timelineCollapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            <span className="hidden" aria-hidden="true" />
          </button>
        </div>
        {trailing}
      </div>

      {presetPanelLeft !== null ? (
        <div
          ref={presetPanelRef}
          data-director-camera-preset-panel
          data-director-camera-preset-panel-mode={presetMode}
          className="absolute bottom-full z-50 max-h-[calc(100vh-88px)] w-[304px] max-w-[calc(100%-16px)] overflow-hidden rounded border border-white/[0.1] bg-[#202020] shadow-[0_16px_38px_rgba(0,0,0,0.48)]"
          style={{ left: presetPanelLeft }}
        >
          <header className="flex h-10 items-center border-b border-white/[0.07] px-3">
            <Camera size={14} className="text-[#66d9f4]" />
            <h3 className="ml-2 text-[11px] font-medium text-[#dedede]">
              预设运镜
            </h3>
            <span className="ml-auto text-[9px] text-[#5f5f5f]">预设</span>
            <button
              type="button"
              aria-label="关闭预设运镜"
              title="关闭"
              onClick={() => setPresetPanelLeft(null)}
              className="ml-1 flex h-7 w-7 items-center justify-center rounded text-[#727272] hover:bg-white/[0.06] hover:text-white"
            >
              <X size={13} />
            </button>
          </header>

          <div className="max-h-[calc(100vh-136px)] overflow-y-auto p-3">
            <div
              data-director-camera-preset-mode={presetMode}
              className="grid h-8 grid-cols-2 gap-1 rounded border border-white/[0.08] bg-[#181818] p-0.5"
            >
              {(
                [
                  ["replace", "替换运镜"],
                  ["append", "追加运镜"],
                ] as const
              ).map(([mode, label]) => (
                <button
                  key={mode}
                  type="button"
                  data-director-camera-preset-mode-option={mode}
                  aria-pressed={presetMode === mode}
                  onClick={() => setPresetMode(mode)}
                  className={cn(
                    "rounded text-[10px] text-[#818181] hover:text-white",
                    presetMode === mode &&
                      "bg-[#303030] text-[#6eddf6]",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="mt-2 grid grid-cols-2 gap-1.5">
              {DIRECTOR_CAMERA_MOTION_PRESETS.map((preset) => {
                const active =
                  selectedPresetApplication?.preset === preset.id &&
                  selectedPresetApplication.mode === presetMode;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    data-director-camera-preset-option={preset.id}
                    aria-pressed={active}
                    onClick={() =>
                      applyCameraMotionPreset(
                        preset.id,
                        presetMode,
                        selectedTrack?.id,
                      )
                    }
                    className={cn(
                      "flex h-8 min-w-0 items-center justify-center gap-1.5 rounded border border-white/[0.07] bg-[#252525] px-2 text-[10px] text-[#9b9b9b] hover:border-white/[0.14] hover:text-white",
                      active &&
                        "border-[#65d9f4]/35 bg-[#0c6579]/20 text-[#78e0f7]",
                    )}
                  >
                    {preset.id === "orbit" ? (
                      <Circle size={12} />
                    ) : preset.id === "half-arc" ? (
                      <Waypoints size={12} />
                    ) : preset.id === "spiral-up" ? (
                      <Route size={12} />
                    ) : (
                      <Move3D size={12} />
                    )}
                    <span className="truncate">{preset.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="mt-2 min-h-8 border-t border-white/[0.07] pt-2">
              {selectedPresetError ? (
                <p
                  data-director-camera-preset-error
                  className="text-[9px] leading-4 text-[#d5a86d]"
                >
                  {selectedPresetError.message}
                </p>
              ) : selectedPresetApplication ? (
                <p
                  data-director-camera-preset-status
                  data-preset={selectedPresetApplication.preset}
                  data-mode={selectedPresetApplication.mode}
                  data-start-time={selectedPresetApplication.startTime}
                  data-end-time={selectedPresetApplication.endTime}
                  data-keyframe-count={
                    selectedPresetApplication.generatedKeyframeIds.length
                  }
                  className="text-[9px] leading-4 text-[#72d995]"
                >
                  {selectedPresetApplication.mode === "replace"
                    ? "替换运镜"
                    : "追加运镜"}
                  {" · "}
                  {
                    DIRECTOR_CAMERA_MOTION_PRESETS.find(
                      (item) =>
                        item.id === selectedPresetApplication.preset,
                    )?.label
                  }
                </p>
              ) : (
                <p className="text-[9px] leading-4 text-[#5f5f5f]">预设</p>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {pathMenuLeft !== null ? (
        <div
          ref={pathMenuRef}
          data-director-motion-path-menu
          className="absolute top-10 z-50 w-44 border border-white/[0.1] bg-[#232323] p-1 shadow-[0_12px_30px_rgba(0,0,0,0.42)]"
          style={{ left: pathMenuLeft }}
        >
          <div
            data-director-motion-path-free-draw
            className="px-2 pb-1 pt-1.5 text-[10px] text-[#626262]"
          >
            自由绘制
          </div>
          {[
            {
              tool: "pencil" as const,
              label: "铅笔路径",
              Icon: Pencil,
            },
            {
              tool: "pen" as const,
              label: "钢笔路径",
              Icon: PenTool,
            },
          ].map(({ tool, label, Icon }) => (
            <button
              key={tool}
              type="button"
              data-director-motion-path-draw-tool={tool}
              disabled={selectedTrackLocked}
              onClick={() => {
                startMotionPathDrawing(tool);
                const draft =
                  useDirectorStore.getState().timeline.motionPathDraft;
                if (draft) {
                  beginDirectorGesture({
                    commandKind: "path-draw",
                    targetId: draft.trackId,
                    fieldScope: draft.tool,
                  });
                }
                setPathMenuLeft(null);
              }}
              className="flex h-8 w-full items-center gap-2 px-2 text-left text-[11px] text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
            >
              <Icon size={13} className="text-[#777]" />
              {label}
            </button>
          ))}
          <div className="mx-2 my-1 h-px bg-white/[0.07]" />
          {[
            {
              preset: "line" as const,
              label: "直线路径",
              Icon: Minus,
            },
            {
              preset: "ring" as const,
              label: "圆环路径",
              Icon: Circle,
            },
            {
              preset: "rectangle" as const,
              label: "矩形路径",
              Icon: RectangleHorizontal,
            },
          ].map(({ preset, label, Icon }) => (
            <button
              key={preset}
              type="button"
              data-director-motion-path-preset={preset}
              disabled={selectedTrackLocked}
              onClick={() => {
                createMotionPath(preset);
                setPathMenuLeft(null);
              }}
              className="flex h-8 w-full items-center gap-2 px-2 text-left text-[11px] text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
            >
              <Icon size={13} className="text-[#777]" />
              {label}
            </button>
          ))}
        </div>
      ) : null}

      {timeline.editorMode === "curve" ? (
        <DirectorCurveEditor />
      ) : (
      <div className="flex min-h-0 min-w-0 flex-1 gap-[2px]">
        {/* Batch 600（源站实测）：两列之间是 2px 的 `gap-[2px]` **间隙**，不是
            边框——源站左列 `z-10 shrink-0 bg-[#1f1f1f]` 的 borderRight 实测 0px。
            clone 原先给左列加了 `border-r border-white/[0.07]`，把右列推前了 1px。 */}
        {/* Batch 593（源站实测）：左列 320px（不再随视口收窄），顶部有一条
            36px 空占位给覆盖在它上面的工具条，对象行与轨道行各 32px。 */}
        <div
          data-director-timeline-track-list
          className="w-[320px] shrink-0 overflow-y-auto bg-[#1f1f1f] max-[899px]:w-[220px]"
        >
          {/* 源站左列第一格是一个 320x36 的空 div（`bg-[#1f1f1f]`，实测
              innerHTML 长度为 0），专门给覆盖在上面的工具条让位；它让对象行
              落在 y=1057 而不是 y=1021。 */}
          <div className="h-9 shrink-0 bg-[#1f1f1f]" aria-hidden="true" />
          {timeline.tracks.length === 0 ? (
            <div className="px-3 py-6 text-center text-[11px] text-[#555]">
              选择对象后新建轨道
            </div>
          ) : (
            timelineTrackGroups.map((group) => {
              const collapsed = collapsedObjects[group.key] === true;
              const cameraTrack = group.tracks.find(
                (track) => track.kind === "camera",
              );
              const groupSelected = group.tracks.some(
                (track) => track.id === timeline.selectedTrackId,
              );
              return (
                <div key={group.key} data-director-object-group={group.key}>
                  {/* 对象行：源站 320×32，栅格 16px / 1fr / 220px。第 1 列是
                      收起开关（20×20，chevron 展开时 rotate-90、收起时 rotate-0，
                      可及名 收起属性/展开属性 + aria-expanded，无 title）；
                      第 3 列的「绘制轨迹」在源站是**真 button** 86×24 带
                      aria-pressed，不是 clone 之前用的 span role=button。 */}
                  <div
                    data-director-timeline-object-row={group.objectId}
                    data-director-timeline-object-selected={groupSelected ? "true" : "false"}
                    className="group relative grid h-8 items-center gap-1 px-2 text-[12px] text-[#F7F7F7] transition-colors"
                    style={{
                      gridTemplateColumns: "16px minmax(0,1fr) 220px",
                    }}
                  >
                    {/* Batch 597（源站 2026-10-01 实测）：对象行常驻一条
                        `span[aria-hidden].absolute.inset-0` 覆盖层，颜色随「该对象
                        的轨道是否被选中」在 rgba(60,181,204,0.25) 与 white/10 之间
                        切换；行文字色恒为 #F7F7F7，**不随选中变化**。 */}
                    <span
                      aria-hidden="true"
                      className={cn(
                        "pointer-events-none absolute inset-x-0 inset-y-0",
                        groupSelected ? "bg-[rgba(60,181,204,0.25)]" : "bg-white/10",
                      )}
                    />
                    <button
                      type="button"
                      aria-label={collapsed ? "展开属性" : "收起属性"}
                      aria-expanded={!collapsed}
                      onClick={() =>
                        setCollapsedObjects((current) => ({
                          ...current,
                          [group.key]: !collapsed,
                        }))
                      }
                      className="group relative z-[1] flex h-5 w-5 items-center justify-center rounded-md text-white/45 transition-colors hover:bg-white/10 hover:text-white"
                    >
                      <ChevronRight
                        className={cn(
                          "h-[5px] w-[5px] transition-transform",
                          !collapsed && "rotate-90",
                        )}
                      />
                      <span className="hidden" aria-hidden="true" />
                    </button>
                    <div
                      role="button"
                      tabIndex={0}
                      title={group.objectName}
                      data-director-timeline-object-name={group.objectId}
                      onClick={() => selectTimelineTrack(group.tracks[0].id)}
                      className="relative z-[1] min-w-0 cursor-pointer truncate text-left font-medium text-[#F7F7F7] transition-colors hover:text-white"
                    >
                      <span className="truncate">{group.objectName}</span>
                    </div>
                    <div className="relative z-[1] flex min-w-0 items-center justify-end gap-1">
                      {cameraTrack ? (
                        <button
                          type="button"
                          data-director-track-draw-trail={cameraTrack.id}
                          aria-label="绘制轨迹"
                          aria-pressed={Boolean(cameraTrack.motionPathId)}
                          onClick={() => {
                            selectTimelineTrack(cameraTrack.id);
                            togglePathMenu();
                          }}
                          className={cn(
                            "flex h-6 w-fit min-w-0 cursor-pointer items-center justify-center gap-1 rounded-lg px-2 text-[13px] leading-none transition-colors",
                            cameraTrack.motionPathId
                              ? "bg-[#23393D] text-[#5ddcff]"
                              : "text-[#5ddcff] hover:bg-[#23393D]",
                          )}
                        >
                          <Route size={14} className="shrink-0" />
                          <span className="min-w-0 truncate">绘制轨迹</span>
                        </button>
                      ) : null}
                    </div>
                  </div>
                  {collapsed
                    ? null
                    : group.tracks.map((track) => {
                        const selected =
                          track.id === timeline.selectedTrackId;
                        const keyframeState =
                          directorTrackKeyframeState(
                            track,
                            timeline.currentTime,
                          );
                        return (
                          <div
                            key={track.id}
                            data-director-track-label={track.id}
                            data-director-track-row={track.id}
                            data-director-track-row-kind={track.kind}
                            data-director-track-row-selected={selected ? "true" : "false"}
                            // Batch 597: 源站轨道行的选中态是**背景**
                            // `rgba(60,181,204,0.1)`，未选中是 `bg-transparent`
                            // + `hover:bg-white/[0.04]`；文字色恒为 #A8A8A8，
                            // 轨道名另加 font-medium + #F7F7F7。clone 原先靠改
                            // 文字色表达选中，与源站不符。
                            className={cn(
                              "group relative grid h-8 items-center gap-1 px-2 text-[12px] text-[#A8A8A8] transition-colors hover:bg-white/[0.04] max-[899px]:[grid-template-columns:32px_36px_78px_minmax(0,1fr)]",
                              selected ? "bg-[rgba(60,181,204,0.1)]" : "bg-transparent",
                            )}
                            style={{
                              gridTemplateColumns: "40px 36px 78px minmax(0,1fr)",
                            }}
                          >
                            {/* 源站第 1 列 40px 是**纯装饰**的加号（aria-hidden）：
                                竖线只画到行中点、横线落在行中点，色值 #363636。 */}
                            <span
                              aria-hidden="true"
                              className="relative h-full w-10"
                            >
                              <span
                                className="absolute left-5 top-0 w-px"
                                style={{
                                  bottom: "50%",
                                  background: selected
                                    ? "rgba(7,184,221,0.4)"
                                    : "#363636",
                                }}
                              />
                              <span
                                className="absolute left-5 top-1/2 h-px w-4"
                                style={{
                                  background: selected
                                    ? "rgba(7,184,221,0.4)"
                                    : "#363636",
                                }}
                              />
                            </span>
                            <div
                              role="button"
                              tabIndex={0}
                              title={track.label}
                              onClick={() => selectTimelineTrack(track.id)}
                              className="relative z-[1] min-w-0 cursor-pointer truncate text-left font-medium text-[#F7F7F7] transition-colors hover:text-white"
                            >
                              <span className="truncate">
                                {directorTrackShortName(track)}
                              </span>
                            </div>
                            <div className="flex h-6 shrink-0 items-center justify-center gap-0.5">
                              <button
                                type="button"
                                aria-label="上一关键帧"
                                disabled={keyframeState.earlier === undefined}
                                onClick={() => {
                                  selectTimelineTrack(track.id);
                                  if (keyframeState.earlier !== undefined) {
                                    setTimelineTime(keyframeState.earlier);
                                  }
                                }}
                                className="group relative flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-white/60 transition-colors hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:text-white/25 disabled:hover:bg-transparent"
                              >
                                <ChevronLeft className="h-[5px] w-[5px]" />
                                <span className="hidden" aria-hidden="true" />
                              </button>
                              <button
                                type="button"
                                aria-label={
                                  keyframeState.exact === undefined
                                    ? "当前帧无关键帧"
                                    : "当前帧有关键帧"
                                }
                                aria-pressed={keyframeState.exact !== undefined}
                                onClick={() => {
                                  selectTimelineTrack(track.id);
                                  const keyframe = track.keyframes.find(
                                    (item) =>
                                      Math.abs(
                                        item.time - timeline.currentTime,
                                      ) <= DIRECTOR_KEYFRAME_EPSILON,
                                  );
                                  if (keyframe) {
                                    deleteTimelineKeyframe(keyframe.id);
                                  } else {
                                    addTimelineKeyframe(track.id);
                                  }
                                }}
                                className="group relative flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-colors hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:text-white/25 disabled:hover:bg-transparent"
                              >
                                <span
                                  aria-hidden="true"
                                  className={cn(
                                    "h-[9px] w-[9px] rotate-45 rounded-[2px] border transition-colors",
                                    keyframeState.exact === undefined
                                      ? "border-white/30"
                                      : "border-[#A8A8A8] bg-[#A8A8A8]",
                                  )}
                                />
                                <span className="hidden" aria-hidden="true" />
                              </button>
                              <button
                                type="button"
                                aria-label="下一关键帧"
                                disabled={keyframeState.later === undefined}
                                onClick={() => {
                                  selectTimelineTrack(track.id);
                                  if (keyframeState.later !== undefined) {
                                    setTimelineTime(keyframeState.later);
                                  }
                                }}
                                className="group relative flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-white/60 transition-colors hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:text-white/25 disabled:hover:bg-transparent"
                              >
                                <ChevronRight className="h-[5px] w-[5px]" />
                                <span className="hidden" aria-hidden="true" />
                              </button>
                            </div>
                            <span
                              data-director-track-value={track.id}
                              className="relative z-[1] truncate text-right text-[13px] tabular-nums"
                            >
                              {directorTrackValueText(
                                track,
                                timeline.currentTime,
                              )}
                            </span>
                          </div>
                        );
                      })}
                </div>
              );
            })
          )}
        </div>

        {!timelineCollapsed ? (
        /* Batch 600（源站实测）：右列是**三层**——
             pane  `relative min-w-0 flex-1 bg-[#1f1f1f]`
             scroller `tiny-scrollbar h-full min-w-0 overflow-x-auto overflow-y-hidden`
             内容  `relative shrink-0 overflow-hidden rounded-r-md bg-black/15`
           内容按内容宽高排布（源站实测 2124×115，而 pane 1598×129），所以
           `rounded-r-md` 的圆角落在**内容右端**而不是视口右缘，内容下方露出
           的是 pane 的 #1f1f1f。clone 原先只有一层 scroller，且内容被
           `min-h-full` 拉满，右缘圆角和底部露底都没有。 */
        <div className="relative min-w-0 flex-1 bg-[#1f1f1f]">
          <div className="tiny-scrollbar h-full min-w-0 overflow-x-auto overflow-y-hidden">
          <div
            ref={timelineCanvasRef}
            data-director-timeline-canvas
            className="relative min-w-full shrink-0 overflow-hidden rounded-r-md"
            // 源站这层是 `bg-black/15`，但它**观察不到**：包裹层与 canvas 同为
            // 2124×115，canvas 逐像素不透明地铺满（底色就是实测的 #212121）。
            // 所以这里保留可观测的 #212121，不去追一个永远被盖住的底色。
            style={{
              width: timelineWidth,
              background: DIRECTOR_LANE_BASE_COLOR,
            }}
          >
            <div
              data-director-timeline-ruler
              data-director-timeline-tick-count={ticks.length}
              onPointerDown={beginScrub}
              style={{ height: DIRECTOR_RULER_HEIGHT_PX }}
              className="relative shrink-0 cursor-ew-resize bg-[#212121]"
            >
              {ticks.map((tick, index) => {
                const major = index % DIRECTOR_RULER_MAJOR_EVERY === 0;
                return (
                  <span key={tick}>
                    <span
                      data-director-ruler-tick={major ? "major" : "minor"}
                      className="absolute w-px"
                      style={{
                        left: `${(tick / timeline.duration) * 100}%`,
                        bottom: `${DIRECTOR_RULER_TICK_BOTTOM_PX}px`,
                        height: major
                          ? DIRECTOR_RULER_MAJOR_PX
                          : DIRECTOR_RULER_MINOR_PX,
                        background: major
                          ? DIRECTOR_RULER_MAJOR_COLOR
                          : DIRECTOR_RULER_MINOR_COLOR,
                      }}
                    />
                    {major ? (
                      <span
                        className="absolute top-[5px] -translate-x-1/2 text-[12px] tabular-nums text-[#9d9d9d]"
                        style={{ left: `${(tick / timeline.duration) * 100}%` }}
                      >
                        {tick}s
                      </span>
                    ) : null}
                  </span>
                );
              })}
            </div>

            {/* Batch 598（源站逐像素实测）：车道区与左列是**同一套两级行**——
                每个对象一条对象行车道，其下挂该对象的轨道车道；对象行收起时
                轨道车道整条消失（实测收起后 canvas 只剩一条 [37,67) 的色带）。
                clone 原先直接 map timeline.tracks（一条 track 一条道、且不看
                收起状态），导致车道比左列少一半行、整体错位 8px。对象行车道
                用独立属性名 data-director-timeline-object-lane，**不占**
                data-director-track-id，以免改动既有按轨道计数的合同。 */}
            {timelineTrackGroups.map((group) => {
              const groupCollapsed = collapsedObjects[group.key] === true;
              const groupSelected = group.tracks.some(
                (track) => track.id === timeline.selectedTrackId,
              );
              return (
                <div key={`lane:${group.key}`} data-director-lane-group={group.key}>
                  <div
                    data-director-timeline-object-lane={group.objectId}
                    data-director-timeline-object-lane-selected={
                      groupSelected ? "true" : "false"
                    }
                    onPointerDown={beginScrub}
                    // 实测：#212121 叠 rgba(60,181,204,0.25) = #28464c（选中），
                    // 顶边一条 1px #355359 亮线，四角 4px 圆角；每格 32px =
                    // 31px 色带 + 1px #212121 底边。
                    className={cn(
                      "relative h-8 cursor-ew-resize rounded-[4px] border-y",
                      groupSelected
                        ? "bg-[rgba(60,181,204,0.25)]"
                        : "bg-white/10",
                    )}
                    style={{
                      borderTopColor: DIRECTOR_OBJECT_LANE_TOP_EDGE,
                      borderBottomColor: DIRECTOR_LANE_EDGE_COLOR,
                    }}
                  >
                    {/* 实测播放头 2px 宽、#05a3c5、无三角头无辉光，且**只画在
                        对象行车道里**（轨道车道那一条整段都是车道底色）。源站只
                        有一个对象，测不出多个对象时播放头落在哪一条——clone 选
                        「当前选中轨道所属对象」那条（clone-only 决策）。 */}
                    {playheadGroupKey === group.key ? (
                      <div
                        data-director-playhead
                        data-director-playhead-time={timeline.currentTime.toFixed(3)}
                        className="pointer-events-none absolute bottom-0 top-0 z-20 w-[2px]"
                        style={{
                          left: `${playheadPosition}%`,
                          background: DIRECTOR_PLAYHEAD_COLOR,
                        }}
                      />
                    ) : null}
                  </div>
                  {groupCollapsed
                    ? null
                    : group.tracks.map((track) => (
                        <div
                          key={track.id}
                          data-director-track-id={track.id}
                          data-director-track-kind={track.kind}
                          data-director-track-object-id={track.objectId}
                          data-director-track-group-id={
                            track.kind === "group" ? track.groupId : undefined
                          }
                          data-director-track-selected={
                            track.id === timeline.selectedTrackId
                          }
                          onPointerDown={beginScrub}
                          // Batch 595/598（源站逐像素实测）：轨道车道是**纯色**，
                          // 没有竖向网格线也没有行内分隔线；底色 = #212121 叠
                          // rgba(60,181,204,0.1) = #243032（选中），未选中透明
                          // 落回 #212121。每格同样是 31px 色带 + 1px #212121 底边。
                          className={cn(
                            "relative h-8 cursor-ew-resize border-b",
                            track.id === timeline.selectedTrackId &&
                              "bg-[rgba(60,181,204,0.1)]",
                          )}
                          style={{ borderBottomColor: DIRECTOR_LANE_EDGE_COLOR }}
                        >
                          {track.keyframes.map((keyframe) => {
                            const selected =
                              keyframe.id === timeline.selectedKeyframeId;
                            return (
                              <button
                                key={keyframe.id}
                                type="button"
                                data-director-keyframe-id={keyframe.id}
                                data-director-keyframe-time={keyframe.time}
                                aria-label={`${track.label} ${formatTimelineTime(keyframe.time)} 关键帧`}
                                title={`${formatTimelineTime(keyframe.time)} 关键帧`}
                                onPointerDown={(event) => event.stopPropagation()}
                                onClick={() => {
                                  // Batch 579: 源站实测（截图 63）——点击关键帧菱形
                                  // 同时选中并把播头 seek 到关键帧时间。
                                  selectTimelineKeyframe(track.id, keyframe.id);
                                  setTimelineTime(keyframe.time);
                                }}
                                // 实测：外接 11×11 的**空心**菱形（7.8px 见方
                                // 旋转 45°）、1px #13879f 描边、#2f2f2f 填充。
                                // 选中的实心 #05a3c5 是 clone-only（源站只测到
                                // 未选中态，再点一次可能删关键帧，没敢试）。
                                className={cn(
                                  "absolute top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rotate-45 border",
                                  selected
                                    ? "border-[#05a3c5] bg-[#05a3c5]"
                                    : "border-[#13879f] bg-[#2f2f2f] hover:bg-[#3a3a3a]",
                                )}
                                style={{
                                  width: DIRECTOR_KEYFRAME_BOX_PX,
                                  height: DIRECTOR_KEYFRAME_BOX_PX,
                                  borderColor: selected
                                    ? DIRECTOR_PLAYHEAD_COLOR
                                    : DIRECTOR_KEYFRAME_EDGE_COLOR,
                                  background: selected
                                    ? DIRECTOR_PLAYHEAD_COLOR
                                    : DIRECTOR_KEYFRAME_FILL_COLOR,
                                  left: `clamp(9px, ${
                                    (keyframe.time / timeline.duration) * 100
                                  }%, calc(100% - 9px))`,
                                }}
                              />
                            );
                          })}
                        </div>
                      ))}
                </div>
              );
            })}
          </div>
          </div>
        </div>
        ) : null}
      </div>
      )}
    </section>
  );
}
