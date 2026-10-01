"""Jimeng clone batch 810-dock verifier — 底部 dock 三枚图标钮的圆角与选中底色。

Contract (SOURCE_FACT 2026-10-03 重测，两侧同 @1512×950 视口)：

  源站 dock @[12,898] 164×36，四枚控件位置与复刻**逐项一致**：
    选择工具 @[16,902] 28×28   小地图 @[48,902] 28×28
    显示连线 @[80,902] 28×28   Zoom @[124,903] 48×28
  差异只在外观：
    三枚 28×28 图标钮  border-radius **8px**（缩放钮同为 6px，两侧一致）
    选中/hover 底色     **rgba(255, 255, 255, 0.08)**（此前复刻 white/10）

⚠️ 取证时踩到并**排除**的一个假目标：并排图里复刻的 dock 左侧压着一个
大号「N」圆，位置正好盖住「选择工具」。它**不是产品缺陷**——
是 Next.js dev 模式的浮标，挂在 `<nextjs-portal>` 的 **shadow root** 里，
`document.querySelectorAll('*')` 根本看不见（已实测：shadowHosts =
[nextjs-portal, next-route-announcer]）。生产构建里不存在，不要去"修"它。

验收取向：圆角用 computed `border-radius` 的**像素值**判（8px vs 6px），
不断言 class 名；底色把 oklab/rgba 两种记法都归一到 alpha 数值再比 ——
复刻用的是 `oklab(0.999994 … / 0.1)`，直接字符串相等会假失败。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1512, "height": 950}

WANT_POS = {
    "选择工具": (16, 902, 28, 28),
    "小地图": (48, 902, 28, 28),
    "显示连线": (80, 902, 28, 28),
}
ICON_RADIUS = 8
SEL_ALPHA = 0.08

PROBE = """() => {
  const alpha = (bg) => {
    const m = /^rgba?\\(([^)]+)\\)$/.exec(bg) || /^color\\(srgb\\s+([^)]+)\\)$/.exec(bg)
           || /^oklab\\(([^)]+)\\)$/.exec(bg) || /^oklch\\(([^)]+)\\)$/.exec(bg);
    if (!m) return null;
    const parts = m[1].trim().split(/[\\s,/]+/);
    return parseFloat(parts[3] ?? '1');
  };
  const out = {};
  for (const lb of ['选择工具', '小地图', '显示连线']) {
    const el = [...document.querySelectorAll('button')]
      .find(b => (b.getAttribute('aria-label') || '') === lb);
    if (!el) { out[lb] = null; continue; }
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    out[lb] = { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                radius: parseFloat(s.borderTopLeftRadius) || 0,
                bgAlpha: alpha(s.backgroundColor), rawBg: s.backgroundColor };
  }
  const z = document.querySelector('[data-testid="dock-zoom"]');
  out['zoom'] = z ? { radius: parseFloat(getComputedStyle(z).borderTopLeftRadius) || 0,
                      rect: (() => { const r = z.getBoundingClientRect();
                        return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null;
  // 记录 Next.js dev 浮标的存在（取证说明用，断言它**不该**进产品 DOM）
  out['_devPortal'] = !!document.querySelector('nextjs-portal');
  return out;
}"""


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            pg.goto(CANVAS_URL, wait_until="domcontentloaded")
            pg.wait_for_selector('[aria-label="选择工具"]', timeout=60000)
            pg.wait_for_timeout(1200)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            d = pg.evaluate(PROBE)

            for lb, want in WANT_POS.items():
                got = d.get(lb)
                if not got:
                    failures.append(f"{lb} button not found")
                    continue
                if tuple(got["rect"]) != want:
                    failures.append(f"{lb} {got['rect']}, want {list(want)} (batch 796 契约)")
                if got["radius"] != ICON_RADIUS:
                    failures.append(
                        f"{lb} border-radius {got['radius']}px, want {ICON_RADIUS}px "
                        "(source; the clone had rounded-md = 6px)"
                    )
                # 「选择工具」与「显示连线」默认即选中态，底色应是 white/8
                if lb in ("选择工具", "显示连线"):
                    a = got["bgAlpha"]
                    if a is None or abs(a - SEL_ALPHA) > 0.006:
                        failures.append(
                            f"{lb} active background alpha {a} ({got['rawBg']}), "
                            f"want {SEL_ALPHA} (source rgba(255,255,255,0.08))"
                        )

            z = d.get("zoom")
            if not z:
                failures.append("zoom button not found")
            elif z["radius"] != 6:
                failures.append(
                    f"zoom border-radius {z['radius']}px, want 6px "
                    "(source measures 6px here — 与图标钮不同，别一起改成 8)"
                )

            if d.get("_devPortal"):
                print("  注：检测到 <nextjs-portal>（Next.js dev 浮标，shadow DOM）。"
                      "并排图里那个压住 dock 的『N』圆就是它，非产品缺陷。")

            pg.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch810-dock.png"))
        finally:
            b.close()

    if failures:
        print("FAIL batch810-dock")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch810-dock — dock 三钮 8px 圆角 + white/8 选中底色，缩放钮保持 6px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
