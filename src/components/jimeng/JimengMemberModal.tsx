"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight, X } from "lucide-react";

import { VipDiamond } from "@/components/jimeng/icons";
import { mockMsg } from "@/components/jimeng/jimengFeedback";

/**
 * 会员 pill → 订阅页全屏浮层 (Batch 13)。
 *
 * 证据 (SOURCE_FACT): 点击会员药丸打开全屏订阅页:
 * 账户头 (头像 + 租户名 + 基础会员 + 到期时间 + 积分详情 ✦745 >) +
 * 购买积分/订阅管理 按钮 + 右上关闭 ×；
 * 计费 tabs 连续包年(限时5折)/连续包月/连续包季(7折)/单月购买，
 * 四档价格卡: 基础 ¥188/季、标准 ¥568、高级 ¥1959 (划线 ¥2798, 首季7.1折)、
 * 超级 ¥8189 (划线 ¥16999)；卡底 ✦积分每月 + 换算行。
 * CLONE_DECISION: 促销倒计时横幅简化为静态渐变条；文案 mock。
 */
const PLANS = [
  {
    name: "基础会员",
    price: "188",
    sub: "每月¥62.66 · 自动续订，可随时取消",
    credits: "725",
    rate: "116",
  },
  {
    name: "标准会员",
    price: "568",
    sub: "每月¥189.33 · 自动续订，可随时取消",
    credits: "2210",
    rate: "117",
  },
  {
    name: "高级会员",
    price: "1959",
    sub: "首季7.1折¥1,959 · 下季续费金额¥2,798 · 包季套餐可随时取消",
    credits: "12320",
    rate: "189",
  },
  {
    name: "超级会员",
    price: "8189",
    sub: "首季5.1折¥8,189 · 下季续费金额¥16,999 · 包季套餐可随时取消",
    credits: "54600",
    rate: "200",
  },
] as const;

const TABS = ["连续包年 限时5折", "连续包月", "连续包季 7折", "单月购买"] as const;

/** ⭐⭐⭐ Batch 1032-②b-1：横幅折扣行**按计费档位**取值。
 *  · 档 0 = 源站取证的横幅原文（「会员低至5折 + 积分消耗4.7折」，对应「连续包年 限时5折」）。
 *  · 档 2 = 「连续包季 7折」—— 7 折来自 tab 自身文案（源站事实），**不外推 4.7 折**。
 *  · 其余档位源站未取证 ⇒ ⇒ 明说「待源站取证（mock）」，**不编数字**。 */
const BANNER_DISCOUNT = [
  "会员低至5折 + 积分消耗4.7折",
  `会员折扣${mockMsg("待源站取证")}`,
  "连续包季 7折",
  `会员折扣${mockMsg("待源站取证")}`,
] as const;

/** 促销倒计时：源站提取时显示 02天00时27分11秒 (SOURCE_FACT screenshot 34)，
 * 复刻以该剩余量起跳实时递减 (CLONE_DECISION：真实截止时间不可知)。 */
const PROMO_INITIAL_SECONDS = 2 * 86400 + 0 * 3600 + 27 * 60 + 11;

function useCountdown() {
  const [remaining, setRemaining] = useState(PROMO_INITIAL_SECONDS);
  useEffect(() => {
    const timer = window.setInterval(
      () => setRemaining((r) => (r > 0 ? r - 1 : 0)),
      1000,
    );
    return () => window.clearInterval(timer);
  }, []);
  const d = Math.floor(remaining / 86400);
  const h = Math.floor((remaining % 86400) / 3600);
  const m = Math.floor((remaining % 3600) / 60);
  const s = remaining % 60;
  return [
    { value: String(d).padStart(2, "0"), unit: "天" },
    { value: String(h).padStart(2, "0"), unit: "小时" },
    { value: String(m).padStart(2, "0"), unit: "分钟" },
    { value: String(s).padStart(2, "0"), unit: "秒" },
  ];
}

export function JimengMemberModal({ onClose }: { onClose: () => void }) {
  const countdown = useCountdown();
  // ⭐⭐⭐ Batch 1032-②b-1：计费 tab 的当前档位。此前写死 `i === 2` 常亮
  // ⇒ ⇒ 四个 tab 看着像能切、切不动。默认仍是 2（源站取证的那一档：连续包季）。
  const [activeTab, setActiveTab] = useState(2);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    // 必须用**捕获阶段**（batch 794 实测踩坑）：JimengFlow 的全局 Escape 监听
    // 注册得更早，会先触发一次同步重渲染；重渲染使本组件 effect 清理并重新
    // 注册监听，而 removeEventListener 会把该 listener 标记为 removed —— 于是
    // 浏览器在**同一次事件派发中**跳过它，冒泡监听收不到 Escape，弹层关不掉。
    // 捕获阶段先于任何冒泡处理器执行，不受此影响。
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    /* 批 827：只加**自动化锚点**，不加 role / aria-label。
       源站实测（@1680×1050，点 `canvas-commerce-entry`）这层同样是全屏
       `fixed` 遮罩（z-index 1001, 1680×1050）且 **role / aria-label /
       data-testid 全都没有** —— 也就是说"普查按 role 枚举看不见它"这件事
       **源站也一样**，是源站自带的性质，不是复刻的缺陷。
       所以这里刻意**不补 role**：补了就等于擅自改进源站语义，偏离源站。
       但 data-testid 对用户不可见、只是自动化锚点，本项目的 816/823/826
       三轮都把它立成了常备契约，所以补上，让普查能看见并如实记录它。 */
    <div
      data-testid="jimeng-member-modal"
      className="fixed inset-0 z-[250] overflow-auto bg-[#0D0D0D]"
    >
      <button
        type="button"
        aria-label="关闭订阅页"
        onClick={onClose}
        className="absolute right-6 top-6 flex size-10 items-center justify-center rounded-full bg-white/[0.08] text-white/80 hover:bg-white/[0.16]"
      >
        <X size={18} />
      </button>

      <div className="mx-auto max-w-[1280px] px-10 py-10">
        {/* 账户头 */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <span className="flex size-14 items-center justify-center rounded-full bg-gradient-to-br from-[#2A2A2E] to-[#1A1A1C] text-[15px] text-white/80">
              文案
            </span>
            <div>
              <p className="flex items-center gap-1.5 text-[20px] text-white">
                个人空间 <VipDiamond size={14} />
              </p>
              <p className="mt-1 flex items-center gap-3 text-[13px] text-white/55">
                <span>基础会员 2026.10.12 01:31</span>
                <span className="inline-flex items-center gap-1">
                  积分详情 <VipDiamond size={11} /> 745
                  <ChevronRight size={12} />
                </span>
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
              {/* ⭐⭐⭐ Batch 1032-②b-1：这两个 CTA **不接线**，而且**必须不接线** ——
                计费动作绝不能真做 ⇒ 正确的处置是「**明确禁用 + 看得见的说明**」，
                而不是「能点、点了什么都不会发生」（那是 1032 审计里最坏的一类）。
                ⚠️ **说明文字放在旁边而不是 `title`** —— disabled 元素不派发鼠标事件，
                ⇒ ⇒ 原生 tooltip 在它身上常常根本不显示 ⇒ ⇒ 只写 title 等于没说。
                ⚠️ 按钮文案保持源站原样（`购买积分` / `订阅管理`），不改写源站文案。 */}
              <button
                type="button"
                disabled
                className="h-9 cursor-not-allowed rounded-lg bg-white/[0.08] px-4 text-[13px] text-white/40"
              >
                购买积分
              </button>
              <button
                type="button"
                disabled
                className="h-9 cursor-not-allowed rounded-lg bg-white/[0.08] px-4 text-[13px] text-white/40"
              >
                订阅管理
              </button>
            </div>
            {/* ⭐ 可见的说明（不是 tooltip）—— 见上：disabled 元素不派发鼠标事件。 */}
            <p className="text-[11px] text-white/40">
              计费入口：原型不提供购买与订阅（不做真实交易）
            </p>
          </div>
        </div>

        {/* 促销横幅 (倒计时卡为 SOURCE_FACT batch 13/26；起跳值 CLONE_DECISION)
            ⭐⭐⭐ Batch 1032-②b-1：横幅第二行**跟着计费 tab 走**。
            源站取证的横幅原文是「会员低至5折 + 积分消耗4.7折」—— 那是**连续包年**
            那一档的文案（tab 自己写着「限时5折」）。
            ⇒ ⇒ 切到别的档位时**不沿用 5折**，而是明说「待源站取证」。
            第三行始终显示当前周期 ⇒ ⇒ 切 tab 一定看得见变化。 */}
        <div className="mt-8 flex items-center justify-between rounded-2xl bg-gradient-to-r from-[#3D7BFF] via-[#69B6FF] to-[#F7B267] px-8 py-7">
          <div>
            <p className="text-[22px] font-semibold text-white">
              Seedance 2.5 720P 低至0.4元/秒
            </p>
            <p className="mt-1 text-[18px] font-semibold text-[#FFF3C2]">
              {BANNER_DISCOUNT[activeTab]}
            </p>
            <p className="mt-1 text-[13px] text-white/70">
              当前周期：{TABS[activeTab]}
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            {countdown.map(({ value, unit }) => (
              <div
                key={unit}
                className="flex w-[62px] flex-col items-center rounded-xl bg-white/95 py-2"
              >
                <span className="text-[26px] font-semibold leading-7 text-[#1A1A1A] tabular-nums">
                  {value}
                </span>
                <span className="text-[11px] text-[#4A4A4A]">{unit}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="mt-10 text-center text-[18px] text-white/90">
          订阅即梦，解锁更多Seedance2.5能力
        </p>

        {/* 计费 tabs
            ⭐⭐⭐ Batch 1032-②b-1：此前四个 tab **没有 onClick**，只有 `i === 2` 常亮
            ⇒ ⇒ **看着像能切、切不动**（1032-① 登记为 BILLING 类糊弄）。
            现在切 tab **真的改**：选中态移动 + 促销横幅文案随周期变 +
            下方出现一行「本档金额为 mock」说明。
            ⚠️ **不编造其它周期的金额**：源站只取证了「连续包季」这一档的价格，
            ⇒ ⇒ 切到别的档时，价格卡保持源站那份，**并显式声明**金额未取证。 */}
        <div
          className="mx-auto mt-5 flex w-fit items-center gap-1 rounded-full bg-white/[0.06] p-1"
          role="tablist"
          aria-label="计费周期"
        >
          {TABS.map((t, i) => (
            <button
              key={t}
              type="button"
              role="tab"
              aria-selected={i === activeTab}
              aria-label={t}
              onClick={() => setActiveTab(i)}
              className={`h-9 rounded-full px-5 text-[13px] ${
                i === activeTab ? "bg-white/[0.14] text-white" : "text-white/60 hover:text-white/85"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        {activeTab !== 2 ? (
          <p className="mt-3 text-center text-[12px] text-white/45">
            当前周期「{TABS[activeTab]}」：下方价格卡仍是源站取证的「连续包季」金额，
            本档金额{mockMsg("待源站取证")}。
          </p>
        ) : null}

        {/* 价格卡 */}
        <div className="mt-8 grid grid-cols-4 gap-5">
          {PLANS.map((plan, idx) => (
            <PlanCard key={plan.name} plan={plan} isPremium={idx === 2} />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 高级会员卡积分滑块 (Batch 28)。
 *
 * 证据 (SOURCE_FACT): 高级会员卡有四档滑块，刻度 6.2K/12.3K/18.5K/27.7K，
 * 默认选中 12.3K (=12320积分每月)。其余档位的积分数值未提取
 * (CLONE_DECISION: 按刻度推算 6160/12320/18480/27690)，价格不随档位变化。
 */
const SLIDER_STOPS = [
  { label: "6.2K", credits: 6160 },
  { label: "12.3K", credits: 12320 },
  { label: "18.5K", credits: 18480 },
  { label: "27.7K", credits: 27690 },
];

function PlanCard({
  plan,
  isPremium,
}: {
  plan: (typeof PLANS)[number];
  isPremium: boolean;
}) {
  const [stop, setStop] = useState(1);
  const trackRef = useRef<HTMLDivElement>(null);
  const credits = isPremium ? SLIDER_STOPS[stop].credits : plan.credits;

  // 拖动跟随: 指针按住/滑过轨道时吸附最近档位 (Batch 30)
  const dragTo = (clientX: number) => {
    const r = trackRef.current?.getBoundingClientRect();
    if (!r || r.width === 0) return;
    const ratio = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
    setStop(Math.round(ratio * (SLIDER_STOPS.length - 1)));
  };

  return (
    <div className="flex flex-col rounded-2xl border border-white/[0.06] bg-white/[0.04] p-5">
      <p className="text-[15px] text-white/90">{plan.name}</p>
      <p className="mt-3 text-white">
        <span className="text-[15px]">¥</span>
        <span className="text-[34px] font-semibold leading-none">
          {plan.price}
        </span>
        <span className="ml-1 text-[12px] text-white/55">每季</span>
      </p>
      <p className="mt-2 min-h-[40px] text-[12px] leading-[18px] text-white/45">
        {plan.sub}
      </p>

      {isPremium ? (
        <div className="mb-3">
          <div
            ref={trackRef}
            className="relative h-4 cursor-pointer"
            onPointerDown={(e) => {
              // 点在档位按钮上时交给按钮自身 onClick，不启动拖拽
              if ((e.target as HTMLElement).closest("button")) return;
              e.currentTarget.setPointerCapture(e.pointerId);
              dragTo(e.clientX);
            }}
            onPointerMove={(e) => {
              if (e.buttons & 1) dragTo(e.clientX);
            }}
          >
            <div className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-white/[0.12]">
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-white/80 transition-all"
                style={{ width: `${(stop / (SLIDER_STOPS.length - 1)) * 100}%` }}
              />
            </div>
            {SLIDER_STOPS.map((s, i) => (
              <button
                key={s.label}
                type="button"
                aria-label={`积分档位 ${s.label}`}
                onClick={() => setStop(i)}
                className={`absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 transition-colors ${
                  i === stop
                    ? "border-white bg-white"
                    : "border-white/50 bg-[#202020] hover:border-white/80"
                }`}
                style={{ left: `${(i / (SLIDER_STOPS.length - 1)) * 100}%` }}
              />
            ))}
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-white/40">
            {SLIDER_STOPS.map((s, i) => (
              <span key={s.label} className={i === stop ? "text-white/80" : ""}>
                {s.label}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="mb-3" />
      )}

      <div className="mt-auto rounded-xl bg-white/[0.05] p-3">
        <p
          className="flex items-center gap-1 text-[13px] text-white/85"
          data-testid="plan-credits"
        >
          <VipDiamond size={11} /> {credits}积分每月
        </p>
        <p className="mt-1 text-[11px] text-white/40">
          换算¥10={plan.rate}积分
        </p>
      </div>
    </div>
  );
}
