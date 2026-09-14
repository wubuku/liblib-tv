"use client";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 离线编辑冲突对话框 (Batch 82)。
 *
 * 证据 (SOURCE_FACT, docs/design-references/jimeng/81-after-reload-state.png
 * + 像素采样): 页面 reload 且存在未同步修改时弹出 — 居中模态
 * ~545×222, bg rgb(25,25,25), r16；标题「发现离线编辑」白色；
 * 正文「你在离线状态下对当前画布做了修改，这些修改尚未同步到服务器。」
 * 灰色两行；右下双钮: 丢弃修改 (灰底) / 保留并同步 (白底黑字主按钮)；
 * 背景遮罩与资产库模态同款 (black/55)。
 * CLONE_DECISION: 复刻侧无真实离线同步，经 store setOfflineDialog /
 * dev window hook 触发；丢弃/保留 均 mock toast 反馈后关闭。
 */
export function JimengOfflineDialog({ onClose }: { onClose: () => void }) {
  const pushToast = useJimengStore((s) => s.pushToast);

  const act = (discard: boolean) => {
    pushToast(discard ? "已丢弃离线修改（mock）" : "离线修改已同步（mock）");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[210] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/55"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-label="发现离线编辑"
        data-testid="jimeng-offline-dialog"
        className="relative w-[545px] rounded-2xl p-6"
        style={{ background: "rgb(25,25,25)" }}
      >
        <h3 className="text-[16px] font-medium leading-6 text-white">
          发现离线编辑
        </h3>
        <p className="mt-3 text-[14px] leading-6 text-white/55">
          你在离线状态下对当前画布做了修改，这些修改尚未同步到服务器。
        </p>
        <div className="mt-5 flex items-center justify-end gap-3">
          <button
            type="button"
            data-testid="offline-discard"
            onClick={() => act(true)}
            className="flex h-9 items-center rounded-lg bg-white/[0.1] px-4 text-[13px] font-medium text-white/85 hover:bg-white/[0.16]"
          >
            丢弃修改
          </button>
          <button
            type="button"
            data-testid="offline-keep"
            onClick={() => act(false)}
            className="flex h-9 items-center rounded-lg bg-white px-4 text-[13px] font-medium text-[#151515] hover:bg-white/90"
          >
            保留并同步
          </button>
        </div>
      </div>
    </div>
  );
}
