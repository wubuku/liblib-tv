"use client";

import { useEffect } from "react";
import { ChevronRight, X } from "lucide-react";

import { VipDiamond } from "@/components/jimeng/icons";

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

export function JimengMemberModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[250] overflow-auto bg-[#0D0D0D]">
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
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="h-9 rounded-lg bg-white/[0.08] px-4 text-[13px] text-white hover:bg-white/[0.14]"
            >
              购买积分
            </button>
            <button
              type="button"
              className="h-9 rounded-lg bg-white/[0.08] px-4 text-[13px] text-white hover:bg-white/[0.14]"
            >
              订阅管理
            </button>
          </div>
        </div>

        {/* 促销横幅 (简化 CLONE_DECISION) */}
        <div className="mt-8 flex items-center justify-between rounded-2xl bg-gradient-to-r from-[#3D7BFF] via-[#69B6FF] to-[#F7B267] px-8 py-7">
          <div>
            <p className="text-[22px] font-semibold text-white">
              Seedance 2.5 720P 低至0.4元/秒
            </p>
            <p className="mt-1 text-[18px] font-semibold text-[#FFF3C2]">
              会员低至5折 + 积分消耗4.7折
            </p>
          </div>
          <span className="rounded-md bg-white/90 px-3 py-1 text-[13px] font-medium text-[#1A1A1A]">
            Seedance2.5 触底价
          </span>
        </div>

        <p className="mt-10 text-center text-[18px] text-white/90">
          订阅即梦，解锁更多Seedance2.5能力
        </p>

        {/* 计费 tabs */}
        <div className="mx-auto mt-5 flex w-fit items-center gap-1 rounded-full bg-white/[0.06] p-1">
          {TABS.map((t, i) => (
            <button
              key={t}
              type="button"
              className={`h-9 rounded-full px-5 text-[13px] ${
                i === 2 ? "bg-white/[0.14] text-white" : "text-white/60 hover:text-white/85"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* 价格卡 */}
        <div className="mt-8 grid grid-cols-4 gap-5">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className="flex flex-col rounded-2xl border border-white/[0.06] bg-white/[0.04] p-5"
            >
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
              <div className="mt-auto rounded-xl bg-white/[0.05] p-3">
                <p className="flex items-center gap-1 text-[13px] text-white/85">
                  <VipDiamond size={11} /> {plan.credits}积分每月
                </p>
                <p className="mt-1 text-[11px] text-white/40">
                  换算¥10={plan.rate}积分
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
