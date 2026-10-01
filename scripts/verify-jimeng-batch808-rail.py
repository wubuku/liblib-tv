"""Jimeng clone batch 808-rail verifier — 左栏图标字形与 Beta 徽标。

Contract (SOURCE_FACT 2026-10-03 登录态实测)：

  源站左栏 9 钮 @ x=16，40×40，纵向步距 42px，导演台→资产库 56px
  （含 20×12 分隔条）—— 与复刻一致，batch 796 契约，本批不动几何。

  本批只管**字形**与**徽标**，依据是 7× 放大后的像素辨认
  （docs/research/jimeng-canvas-batch807-2026-10-03/807-rail-sbs.png）：

  1. 时间线 = **胶片格**（外框圆角矩形 + 上下两条分隔带，带上排 3 个齿孔）
     ⇒ lucide `Film`。复刻此前用 `LayoutTemplate`（一个宽条 + 两个窄条），
     放大后与源站毫无相似之处。
  2. 导演台 = **等轴测立方体 + 底部环绕箭头**。复刻此前用 `Bot`（机器人头），
     与源站毫无相似之处。源站该图标**不在 DOM 里**（按钮内只有空的
     `<span class="contents">`，实测文本/时间线/主体三钮皆然），既不是 svg
     也不是背景图/遮罩，所以弧段的曲率与箭头角度**没有可量测的证据**，
     复刻用 lucide `Box` 的立方体路径 + 一段自绘弧段近似，标注为近似。
  3. Beta 徽标是一枚**胶囊**，不是纯文字：
     @[34,559] **23×14**、圆角 ≈3px、底色竖向渐变
     rgb(29,46,57)→rgb(33,50,61)、文字 #009EFA 且**非斜体**。
     复刻此前是 `-top-0.5 left-1/2` 居中的 7px **斜体**纯蓝文字（无底色），
     位置 @[28,557] 16×5。

验收取向：徽标用**相对锚点**（相对 40×40 按钮 left 18 / top -1）而不是
绝对 x —— rail 整体随视口高度上下居中，绝对 y 会漂。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

PROBE = """() => {
  const out = {};
  for (const lb of ['时间线', '导演台']) {
    const b = [...document.querySelectorAll('button')]
      .find(x => (x.getAttribute('aria-label') || '') === lb);
    if (!b) { out[lb] = { missing: true }; continue; }
    const r = b.getBoundingClientRect();
    const svg = b.querySelector('svg');
    const sr = svg ? svg.getBoundingClientRect() : null;
    const badge = b.querySelector('[data-testid="rail-beta-badge"]');
    const br = badge ? badge.getBoundingClientRect() : null;
    const bs = badge ? getComputedStyle(badge) : null;
    out[lb] = {
      btn: [r.x, r.y, r.width, r.height],
      icon: sr ? [sr.x, sr.y, sr.width, sr.height] : null,
      // 立方体的等轴测特征：内部有「三条棱交于中心」的 path
      pathCount: svg ? svg.querySelectorAll('path').length : 0,
      hasGroup: !!b.querySelector('svg g'),
      badge: br ? [br.x - r.x, br.y - r.y, br.width, br.height] : null,
      badgeRadius: bs ? bs.borderTopLeftRadius : null,
      badgeBg: bs ? bs.backgroundImage : null,
      badgeItalic: bs ? bs.fontStyle : null,
      badgeColor: bs ? bs.color : null,
    };
  }
  return out;
}"""


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            pg.goto(CANVAS_URL, wait_until="domcontentloaded")
            pg.wait_for_timeout(3000)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            d = pg.evaluate(PROBE)

            # ── 时间线：胶片格（lucide Film = 7 条 path）──
            tl = d.get("时间线") or {}
            if tl.get("missing"):
                failures.append("时间线 button not found")
            else:
                # lucide Film 有 7 个子元素（rect×1 + line×6）；LayoutTemplate
                # 是 3 个 rect。子元素总数是能区分两者的稳定特征。
                if tl["pathCount"] != 7:
                    failures.append(
                        f"时间线 icon has {tl['pathCount']} drawable children, want 7 "
                        "(lucide Film; LayoutTemplate has 3 rects)"
                    )
                if tl["icon"] and round(tl["icon"][2]) != 20:
                    failures.append(f"时间线 icon {tl['icon'][2]:.0f}px, want 20")

            # ── 导演台：立方体（svg 内有 <g> 包裹的等轴测立方体 + 弧段）──
                #   —— 机器人头 Bot 是单层 path，不会有 <g>
            dr = d.get("导演台") or {}
            if dr.get("missing"):
                failures.append("导演台 button not found")
            else:
                if not dr["hasGroup"]:
                    failures.append(
                        "导演台 icon has no <g> — expected the scaled isometric cube group"
                    )
                if dr["pathCount"] < 6:
                    failures.append(
                        f"导演台 icon has {dr['pathCount']} paths, want ≥6 (cube 3 + arc 3)"
                    )
                if dr["icon"] and round(dr["icon"][2]) != 20:
                    failures.append(f"导演台 icon {dr['icon'][2]:.0f}px, want 20")

            # ── Beta 胶囊：23×14 @ 按钮内 left 18 / top -1，圆角 ≈3，非斜体 ──
                bd = dr.get("badge")
            if not bd:
                failures.append("Beta badge missing (source: 23x14 pill, not bare text)")
            else:
                if round(bd[2]) != 23 or round(bd[3]) != 14:
                    failures.append(
                        f"Beta badge {bd[2]:.0f}x{bd[3]:.0f}, want 23x14 (source @[34,559])"
                    )
                if abs(bd[0] - 18) > 1.0 or abs(bd[1] + 1) > 1.0:
                    failures.append(
                        f"Beta badge at left {bd[0]:.0f} / top {bd[1]:.0f} relative to the "
                        "40x40 button, want left 18 / top -1"
                    )
                if dr["badgeItalic"] != "normal":
                    failures.append(
                        f"Beta badge font-style = {dr['badgeItalic']!r}, want normal "
                        "(source is upright; the clone had italic)"
                    )
                if dr["badgeRadius"] in ("0px", None):
                    failures.append(f"Beta badge has no rounded corners ({dr['badgeRadius']})")
                if not dr["badgeBg"] or "gradient" not in dr["badgeBg"]:
                    failures.append(
                        f"Beta badge has no gradient fill (source rgb(29,46,57)->rgb(33,50,61))"
                    )

            # ── 几何未被本批破坏（batch 796 契约）──
            for lb, want_y in (("时间线", None), ("导演台", None)):
                node = d.get(lb) or {}
                if node.get("btn") and round(node["btn"][0]) != 16:
                    failures.append(f"{lb} left edge {node['btn'][0]:.0f}, want 16 (batch 796)")
                if node.get("btn") and (
                    round(node["btn"][2]) != 40 or round(node["btn"][3]) != 40
                ):
                    failures.append(f"{lb} is not 40x40 (batch 796)")

            pg.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch808-rail.png"))
        finally:
            b.close()

    if failures:
        print("FAIL batch808-rail")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch808-rail — 左栏字形：时间线 Film / 导演台 立方体+弧 / Beta 胶囊 23×14 非斜体")
    return 0


if __name__ == "__main__":
    sys.exit(main())
