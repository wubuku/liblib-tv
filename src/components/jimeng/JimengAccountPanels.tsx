"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { MOCK_MARK } from "@/components/jimeng/jimengFeedback";

/**
 * 账号菜单派生浮层 (Batch 820)。
 *
 * 这两个浮层此前不存在 —— 账号菜单里除「快捷键」外的四项点了只关菜单，
 * 是**真死按钮**（见 JimengHelpMenu 文件头）。本批按源站逐项实测接上
 * （README §27），几何与文案均取自实测，不清楚的���方标 (mock)。
 */

/** 批 820 SOURCE_FACT：AI 生成水印设置弹窗的法条文案，逐字取自源站 */
const WATERMARK_LEGAL =
  '根据法律法规要求，即梦AI平台（"平台"）提供AI生成合成服务，可能导致公众混淆或者误认的，' +
  '平台应当在AI生成合成内容上添加显式标识（即“AI生成”明水印），向公众进行提示。 ' +
  "经过您的申请，平台可以向您提供未添加显式标识的AI生成合成内容。" +
  "如您后续使用网络信息内容传播服务发布AI生成合成内容，请注意您还需主动声明并使用传播平台提供的标识功能进行标识。" +
  "您理解并承诺，如您未按照法律法规要求在AI生成合成内容上添加显式标识，导致公众混淆或者误认，" +
  "因此所发生的后果和责任均由您自行承担。";

/** 批 820 SOURCE_FACT：帮助中心浮层，源站 360×648 @[1304,60]（视口 1680 宽） */
export function JimengHelpCenterPanel({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    };
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-label="Help center"
      data-testid="account-help-center"
      className="fixed right-3 top-[60px] z-[240] flex h-[648px] w-[360px] flex-col overflow-hidden rounded-2xl border border-white/10"
      style={{ background: "rgb(34,34,34)" }}
    >
      <div className="flex h-14 shrink-0 items-center justify-between px-4">
        <p className="text-[15px] text-white">帮助中心</p>
        <button
          type="button"
          aria-label="关闭帮助中心"
          data-testid="account-help-center-close"
          onClick={onClose}
          className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
        >
          <X size={14} />
        </button>
      </div>
      {/* (mock) 源站这个浮层在实测时**加载失败**（正文是「帮助中心加载失败，请重试」
          与一个「重试」钮），所以加载成功后的长什么样我没有证据，不编。 */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 text-[13px] leading-[22px] text-white/45">
        <p>{`帮助内容${MOCK_MARK}：源站在本次实测中该浮层加载失败，此处内容未取证。`}</p>
      </div>
    </div>
  );
}

/** 批 820 SOURCE_FACT：水印设置弹窗 —— 全屏遮罩 + 居中 616×492
 *  （(1680-616)/2=532, (1050-492)/2=279，与源站实测 @[532,279] 吻合）；
 *  控件实测：关闭 36×36 aria-label "Close watermark settings" @[1080,311]、
 *  水印开关 24×24 @[564,609]、保存 84×36「保存设置」@[1032,703]。 */
export function JimengWatermarkDialog({ onClose }: { onClose: () => void }) {
  const [noWatermark, setNoWatermark] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    <>
      <div
        className="fixed inset-0 z-[280]"
        style={{ background: "rgba(0,0,0,0.8)" }}
        data-dialog-overlay="true"
        data-testid="watermark-overlay"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-label="AI生成水印设置"
        data-testid="account-watermark-dialog"
        className="fixed left-1/2 top-1/2 z-[290] flex h-[492px] w-[616px] max-h-[80vh] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl"
        style={{ background: "rgb(34,34,34)" }}
      >
        <div className="flex h-[68px] shrink-0 items-start justify-between px-5 pt-4">
          <h2 className="text-[16px] text-white">AI生成水印设置</h2>
          <button
            type="button"
            aria-label="Close watermark settings"
            data-testid="watermark-close"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-lg text-white/60 hover:bg-white/10 hover:text-white"
          >
            <X size={16} />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5">
          <p className="text-[13px] leading-[22px] text-white/80">{WATERMARK_LEGAL}</p>
          <p className="mt-3 text-[13px] leading-[22px] text-white/80">
            打开去除水印开关后，您使用即梦前述账号所创作、生成的AI生成合成内容在导出后将不再添加
            “AI生成”明水印，但仍将保留“即梦AI”品牌水印。
          </p>
          <button
            type="button"
            role="switch"
            aria-label="导出内容去除AI生成水印"
            aria-checked={noWatermark}
            data-testid="watermark-toggle"
            onClick={() => {
              setNoWatermark((v) => !v);
              setSaved(false);
            }}
            className={`mt-4 flex size-6 items-center justify-center rounded-md border ${
              noWatermark
                ? "border-[#0A5CD6] bg-[#0A5CD6]"
                : "border-white/30 bg-transparent"
            }`}
          >
            {noWatermark ? <span className="text-[11px] leading-none text-white">✓</span> : null}
          </button>
          <p className="mt-4 text-[12px] leading-[20px] text-white/55">
            打开开关并点击保存设置，代表您已确认充分了解上述情况并同意
          </p>
          <p className="mt-2 text-[12px] leading-[20px] text-white/55">
            后续可在右上角头像处的「AI生成水印设置」中修改水印设置
          </p>
        </div>
        <div className="flex h-[68px] shrink-0 items-center justify-end px-5">
          <button
            type="button"
            aria-label="保存设置"
            data-testid="watermark-save"
            onClick={() => setSaved(true)}
            className="flex h-9 w-[84px] items-center justify-center rounded-lg bg-[#0A5CD6] text-[13px] text-white hover:bg-[#0A5CD6]/85"
          >
            {saved ? "已保存" : "保存设置"}
          </button>
        </div>
      </div>
    </>
  );
}
