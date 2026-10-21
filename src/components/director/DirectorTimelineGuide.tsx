"use client";

// Batch 834（源站 2026-10-21 活体 ＋ 源站 chunk 原文）：
// 导演台**时间轴引导气泡**的 **5 步**完整实现。
//
// ★ 源站原文（chunk `0fmehki05gkzw.js.js` 的组件 `cC`）的 5 步数据：
//   步 1  target=add-track        count=1/5 width=260 bubbleOffsetX=-80  bubbleHeight=112
//   步 2  target=draw-trajectory  count=2/5 width=300 bubbleOffsetX=-64  bubbleHeight=112
//   步 3  target=motion-preset-ring count=3/5 width=360 bubbleOffsetX=-48 bubbleHeight=136
//   步 4  target=play             count=4/5 width=300 bubbleOffsetX=12   bubbleHeight=112
//   步 5  target=export-to-canvas count=5/5 width=360 bubbleOffsetX=-268 bubbleHeight=112
//   ⟹ raw/source-834-timeline-guide.json（活体 ＋ 原文两路交叉核对）
//
// ★ 定位算法（源站原文照抄）：
//   target = 「export-to-canvas」用导出按钮的 ref
//          ?? document.querySelector('[data-director-timeline-guide-target="<target>"]')
//          ?? （target==="motion-preset-ring" 时退回 draw-trajectory）
//          ?? document.querySelector('[data-director-timeline-guide-target="add-track"]')
//   icon   = target.querySelector('[data-director-timeline-guide-icon="true"]') ?? target
//   width  = Math.min(步宽, innerWidth - 24)
//   left   = clamp(icon 中心 x ＋ bubbleOffsetX, 12, innerWidth - width - 12)
//   top    = target.top - bubbleHeight - 2；不足 12 则改成 target.bottom + 14（再夹一次）
//   ring   = 以 icon 中心为心的 60×60 盒子（里一枚 24×24 的涟漪圆）
//
// ★ ★ 与源站**有意**的两处偏离（CLONE_DECISION，勿当��缺陷）：
//   ① 气泡本体是 `pointer-events-none`、只有两枚按钮是 `pointer-events-auto`
//      （源站气泡本体是 `pointer-events-auto`）——沿用 batch 556 的既定做法：
//      clone 的时间轴工具条是**一整行**（多了预设运镜／曲线编辑器等 clone 能力），
//      气泡若吞掉整块的点击，引导期间工具条会不可用。
//   ② 涟漪圆的 `border-[1.2px] border-[#07B8DD]` 与气泡的 `font-['PingFang_SC',sans-serif]`
//      走 **inline style** 而不是 Tailwind 任意值类 —— 4317 的 Tailwind 扫描是**冻结**的
//      （batch 824 实测）⟹ 新增任意值类在 dev 上不生成。
//
// ★ 收起标记沿用 clone 自己的 localStorage 键 `director-timeline-coach-dismissed`
//   （源站的键是 `libtv.director.timeline-guide.dismissed.v1`）——
//   ★ 键名**不能**跟着改：门禁 36／575 直接断言这个键名。

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

export type DirectorTimelineGuideStep = {
  /** 源站用 `data-director-timeline-guide-target` 标记的目标 */
  target: string;
  text: string;
  count: string;
  width: number;
  bubbleOffsetX: number;
  bubbleHeight: number;
};

/** 5 步的**文案逐字取自源站活体读数**（raw/source-834-timeline-guide.json）。 */
export const DIRECTOR_TIMELINE_GUIDE_STEPS: ReadonlyArray<DirectorTimelineGuideStep> = [
  {
    target: "add-track",
    text: "请选择一个角色或者摄像机后，可新建轨道",
    count: "1/5",
    width: 260,
    bubbleOffsetX: -80,
    bubbleHeight: 112,
  },
  {
    target: "draw-trajectory",
    text: "点击创建路径，弹出选项面板",
    count: "2/5",
    width: 300,
    bubbleOffsetX: -64,
    bubbleHeight: 112,
  },
  {
    target: "motion-preset-ring",
    text: "点击圆环/直线/矩形创建路径，或用铅笔/钢笔工具绘制想要路径",
    count: "3/5",
    width: 360,
    bubbleOffsetX: -48,
    bubbleHeight: 136,
  },
  {
    target: "play",
    text: "路径绘制后点击播放，可预览动画",
    count: "4/5",
    width: 300,
    bubbleOffsetX: 12,
    bubbleHeight: 112,
  },
  {
    target: "export-to-canvas",
    text: "预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑",
    count: "5/5",
    width: 360,
    bubbleOffsetX: -268,
    bubbleHeight: 112,
  },
];

const RIPPLE_CSS = `@keyframes director-timeline-guide-ripple {
  0% { transform: scale(1); opacity: 0; }
  12% { transform: scale(1.05); opacity: 0.9; }
  100% { transform: scale(2.5); opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .director-timeline-guide-ripple { animation: none !important; opacity: 0.6 !important; }
}`;

type GuideGeometry = {
  bubble: { left: number; top: number; width: number };
  ring: { left: number; top: number; size: number; rippleSize: number };
};

function clamp(value: number, low: number, high: number) {
  return Math.min(Math.max(value, low), high);
}

/** 源站的「同值就不重渲染」比较（0.5px 容差，六个数全比）。 */
function sameGeometry(a: GuideGeometry | null, b: GuideGeometry) {
  if (!a) return false;
  const near = (x: number, y: number) => Math.abs(x - y) < 0.5;
  return (
    near(a.bubble.left, b.bubble.left) &&
    near(a.bubble.top, b.bubble.top) &&
    near(a.bubble.width, b.bubble.width) &&
    near(a.ring.left, b.ring.left) &&
    near(a.ring.top, b.ring.top) &&
    near(a.ring.size, b.ring.size) &&
    near(a.ring.rippleSize, b.ring.rippleSize)
  );
}

export function DirectorTimelineGuide({
  step,
  onNext,
  onSkip,
}: {
  /** 0–4；null ＝ 不显示 */
  step: number | null;
  onNext: () => void;
  onSkip: () => void;
}) {
  const spec = useMemo(
    () =>
      step === null ? null : (DIRECTOR_TIMELINE_GUIDE_STEPS[step] ?? null),
    [step],
  );
  const [geometry, setGeometry] = useState<GuideGeometry | null>(null);
  const geometryRef = useRef<GuideGeometry | null>(null);

  useLayoutEffect(() => {
    if (!spec) return;
    const compute = () => {
      const byTarget = (name: string) =>
        document.querySelector<HTMLElement>(
          `[data-director-timeline-guide-target="${name}"]`,
        );
      const target =
        byTarget(spec.target) ??
        (spec.target === "motion-preset-ring"
          ? byTarget("draw-trajectory")
          : null) ??
        byTarget("add-track");
      if (!target) return;
      const targetBox = target.getBoundingClientRect();
      const iconEl =
        target.querySelector<HTMLElement>(
          '[data-director-timeline-guide-icon="true"]',
        ) ?? target;
      const iconBox = iconEl.getBoundingClientRect();
      const width = Math.min(spec.width, window.innerWidth - 24);
      const centerX = iconBox.left + iconBox.width / 2;
      const left = clamp(
        centerX + spec.bubbleOffsetX,
        12,
        window.innerWidth - width - 12,
      );
      const above = targetBox.top - spec.bubbleHeight - 2;
      const top =
        above >= 12
          ? above
          : clamp(
              targetBox.bottom + 14,
              12,
              window.innerHeight - 120,
            );
      const next: GuideGeometry = {
        bubble: { left, top, width },
        ring: {
          left: centerX - 30,
          top: iconBox.top + iconBox.height / 2 - 30,
          size: 60,
          rippleSize: 24,
        },
      };
      if (sameGeometry(geometryRef.current, next)) return;
      geometryRef.current = next;
      setGeometry(next);
    };
    compute();
    window.addEventListener("resize", compute);
    window.addEventListener("scroll", compute, true);
    const timer = window.setInterval(compute, 250);
    return () => {
      window.removeEventListener("resize", compute);
      window.removeEventListener("scroll", compute, true);
      window.clearInterval(timer);
    };
  }, [spec]);

  useEffect(() => {
    if (!spec) {
      geometryRef.current = null;
      setGeometry(null);
    }
  }, [spec]);

  if (!spec || !geometry || typeof document === "undefined") return null;

  const isLast = step === DIRECTOR_TIMELINE_GUIDE_STEPS.length - 1;
  return createPortal(
    <div
      className="pointer-events-none fixed inset-0"
      data-director-timeline-guide-overlay="true"
      // ★★ z-index 必须走 **inline style**：源站写的是 `z-[1900]`（Tailwind 任意值类），
      //   但 **4317 的 Tailwind 扫描是冻结的**（batch 824 实测）⟹ 新增的任意值类
      //   在 dev 上**根本不生成** ⟹ z-index 落回 auto ⟹ 整块引导被时间轴的
      //   z-30 盖住 ⟹ ★ **「下一步」按钮点不动**（本批实测到的真缺陷）。
      //   同一坑：气泡的 `z-[1]` 与光环的 `z-[2]` 也一并改成 inline style。
      style={{ zIndex: 1900 }}
    >
      <style>{RIPPLE_CSS}</style>
      {/* 气泡本体（源站 class 逐字照抄；pointer-events 的偏离见文件头 ①） */}
      <div
        data-director-timeline-guide-bubble
        // ★ 旧名 `data-director-timeline-coachmark` **保留**（别名）：
        //   门禁 556／557 直接按它定位气泡与两枚按钮 ⟹ 改名会让它们失效。
        data-director-timeline-coachmark
        role="status"
        className="pointer-events-none fixed overflow-hidden rounded-xl border border-white/[0.08] bg-[#242424] p-4 font-normal text-white shadow-[0_4px_16px_rgba(0,0,0,0.18)]"
        style={{
          left: geometry.bubble.left,
          top: geometry.bubble.top,
          width: geometry.bubble.width,
          zIndex: 1,
          fontFamily: "'PingFang_SC', sans-serif",
        }}
      >
        <div className="h-10 overflow-hidden text-[12px] font-normal leading-[19.2px] tracking-normal text-white/90">
          {spec.text}
        </div>
        <div className="mt-3 flex items-center justify-between gap-1">
          <span
            data-director-timeline-guide-count
            className="min-w-0 flex-1 text-[14px] font-normal leading-3 tracking-normal text-white/55"
          >
            {spec.count}
          </span>
          <button
            type="button"
            data-director-timeline-guide-skip
            // ★ 旧名保留（门禁 556／557 按它定位）
            data-director-coachmark-skip
            onClick={onSkip}
            className="pointer-events-auto h-7 rounded-lg bg-transparent px-3 text-[13px] font-normal leading-none tracking-normal text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            跳过
          </button>
          <button
            type="button"
            data-director-timeline-guide-next
            // ★ 旧名保留（门禁 556／557 按它定位）
            data-director-coachmark-next
            onClick={onNext}
            className="pointer-events-auto h-7 rounded-lg bg-white/10 px-3 text-[13px] font-normal leading-none tracking-normal text-white/85 transition-colors hover:bg-white/15 hover:text-white"
          >
            {isLast ? "完成" : "下一步"}
          </button>
        </div>
      </div>
      {/* 目标光环：60×60 的盒子里一枚 24×24 的涟漪圆（源站原文） */}
      <div
        data-director-timeline-guide-ring
        className="fixed"
        style={{
          left: geometry.ring.left,
          top: geometry.ring.top,
          width: geometry.ring.size,
          height: geometry.ring.size,
          zIndex: 2,
        }}
      >
        <span
          className="director-timeline-guide-ripple pointer-events-none absolute left-1/2 top-1/2 rounded-full opacity-0"
          style={{
            width: geometry.ring.rippleSize,
            height: geometry.ring.rippleSize,
            marginLeft: -geometry.ring.rippleSize / 2,
            marginTop: -geometry.ring.rippleSize / 2,
            transformOrigin: "center",
            border: "1.2px solid #07B8DD",
            animation:
              "director-timeline-guide-ripple 1400ms cubic-bezier(0.22, 0.61, 0.36, 1) infinite",
            willChange: "transform, opacity",
          }}
        />
      </div>
    </div>,
    document.body,
  );
}
