"""Jimeng clone batch 807 verifier — 顶栏左簇「项目名 / 节点 N / 分隔线 / 已保存」。

Contract (SOURCE_FACT 2026-10-03 登录态实测，460×64 顶栏裁剪 + DOM 探针，
docs/research/jimeng-canvas-batch807-2026-10-03/)：

  源站  `测试项目`   span @[60,19] 52×22  13px/22px nowrap
        `节点`      span @[156,21] 20×18  10px/18px nowrap  white/60
        `10`        span @[178,21] 10×18  10px/18px nowrap  white/60   ← 间距 2px
        分隔线       1×8 @ x=196, y 26..34（逐列扫描定位，峰值灰度 35 ≈ white/10）
        `已保存`     13px/22px white/40，第一笔墨迹起于 x=205

  三处修掉的偏差：
    1. `节点 {n}` 整串塞进 `size-7`(28px) 定宽按钮且无 nowrap → 折成两行
       （「节点」和「2」上下排）。源站是单行两个 span。
    2. 完全没有分隔线。
    3. 「已保存」左距 ml-3(12) → ml-2(8)，落到源站的 x=204/205。

验收取向：
  - 断言**标签高度**（一个行高 = 18px ⇒ 必然单行），而不是断言「某行文本
    的 y 坐标」——后者在换行时仍然成立，抓不到本次的缺陷。
  - 分隔线用**相对锚点**断言：它必须在「节点块右缘 +12px」且垂直居中于
    13px 文字行，不写死 x=196（顶栏左缘在 AI 抽屉展开时会平移）。
  - 顺带守一条容易被误判的契约：项目名**文字**起点 60px = 按钮盒 52 + px-2(8)。
    拿按钮盒的 x 去比源站的 span x 会得出「差 8px」的假结论（batch 796 同款坑）。
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
  const r = (el) => { const b = el.getBoundingClientRect();
    return [b.x, b.y, b.width, b.height]; };
  const vis = (el) => { if (!el) return false; const b = el.getBoundingClientRect();
    if (b.width < 0.5 || b.height < 0.5) return false;
    for (let p = el; p; p = p.parentElement) { const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false; } return true; };
  const cs = (el, k) => (el ? getComputedStyle(el)[k] : null);

  // 节点摘要标签：按钮内**叶子** span（外层那个 flex 容器 span 也匹配
  // querySelectorAll('span')，不滤掉的话 spans[0] 拿到的是 "节点2" 整串）
  const btn = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
  const label = btn && btn.querySelector('span');
  const labelSpans = btn
    ? [...btn.querySelectorAll('span')].filter((s) => s.children.length === 0)
    : [];
  const div = document.querySelector('[data-testid="topbar-left-divider"]');
  const saved = document.querySelector('[data-testid="topbar-saved-status"]');
  const title = document.querySelector('[data-testid="canvas-project-title-trigger"]');
  const titleSpan = title && title.firstElementChild;

  // 项目名文字起点要用**文字盒**量，不能用按钮盒（按钮有 px-2 内边距）
  const titleInk = (() => {
    if (!title) return null;
    const b = title.getBoundingClientRect();
    return b.x + parseFloat(getComputedStyle(title).paddingLeft || '0');
  })();

  return {
    btn: btn ? r(btn) : null,
    label: label ? r(label) : null,
    labelWs: cs(label, 'whiteSpace'),
    labelFs: cs(label, 'fontSize'),
    labelLh: cs(label, 'lineHeight'),
    labelColor: cs(label, 'color'),
    spans: labelSpans.map((s) => ({ text: (s.textContent || '').trim(), rect: r(s) })),
    divider: div ? r(div) : null,
    dividerBg: cs(div, 'backgroundColor'),
    saved: saved ? r(saved) : null,
    savedWs: cs(saved, 'whiteSpace'),
    titleInk,
    titlePad: title ? parseFloat(getComputedStyle(title).paddingLeft || '0') : null,
    leftCluster: (() => {
      const l = document.querySelector('[data-testid="topbar-left"]');
      return l ? r(l) : null;
    })(),
  };
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

            # ── 1. 标签必须单行：一个行高 ──
            if not d["label"]:
                failures.append("node summary label not found")
            else:
                lh = float((d["labelLh"] or "0").replace("px", "") or 0)
                h = d["label"][3]
                if lh and h > lh + 1.0:
                    failures.append(
                        f"node summary label wraps: height {h:.0f}px > one line "
                        f"{lh:.0f}px (source is a single 18px line)"
                    )
                if d["labelWs"] != "nowrap":
                    failures.append(f"node summary label white-space = {d['labelWs']!r}, want nowrap")
                if d["labelFs"] != "10px" or d["labelLh"] != "18px":
                    failures.append(
                        f"node summary label typography {d['labelFs']}/{d['labelLh']}, want 10px/18px"
                    )
                # 源站是「节点」与数字两个 span，间距 2px
                if len(d["spans"]) < 2:
                    failures.append(
                        f"node summary label has {len(d['spans'])} span(s); "
                        "source splits 节点 / N into two"
                    )
                elif d["spans"][0]["text"] != "节点":
                    failures.append(f"first label span = {d['spans'][0]['text']!r}, want '节点'")
                else:
                    gap = d["spans"][1]["rect"][0] - (
                        d["spans"][0]["rect"][0] + d["spans"][0]["rect"][2]
                    )
                    if not (1.0 <= gap <= 3.0):
                        failures.append(
                            f"gap between 节点 and count = {gap:.1f}px, want 2 (source @156..176 / @178)"
                        )

            # ── 2. 分隔线：1×8，挂在节点块右缘 +12px，垂直居中于文字行 ──
            if not d["divider"]:
                failures.append("topbar-left divider missing (source: 1x8 @ x=196)")
            else:
                dx, dy, dw, dh = d["divider"]
                if (round(dw), round(dh)) != (1, 8):
                    failures.append(f"divider {dw:.0f}x{dh:.0f}, want 1x8")
                if d["btn"]:
                    want_x = d["btn"][0] + d["btn"][2] + 12
                    if abs(dx - want_x) > 1.0:
                        failures.append(
                            f"divider x={dx:.0f}, want {want_x:.0f} (node block right + 12)"
                        )
                if d["saved"]:
                    scy = d["saved"][1] + d["saved"][3] / 2
                    if abs((dy + dh / 2) - scy) > 1.5:
                        failures.append(
                            f"divider not vertically centred on the text line "
                            f"({dy + dh / 2:.1f} vs {scy:.1f})"
                        )
                if d["saved"] and d["divider"]:
                    gap = d["saved"][0] - (d["divider"][0] + d["divider"][2])
                    if not (7.0 <= gap <= 9.0):
                        failures.append(
                            f"divider → 已保存 gap = {gap:.0f}px, want 8 (source ink @205)"
                        )

            # ── 3. 已保存单行 nowrap ──
            if d["saved"] and d["savedWs"] != "nowrap":
                failures.append(f"saved status white-space = {d['savedWs']!r}, want nowrap")

            # ── 4. 项目名文字起点 = 盒起点 + 内边距（防 batch 796 同款误判）──
            if d["titleInk"] is not None and d["leftCluster"]:
                ink = d["titleInk"] - d["leftCluster"][0]
                if abs(ink - 48) > 1.0:
                    failures.append(
                        f"project title ink offset from left cluster = {ink:.0f}px, "
                        f"want 48 (40 logo + 8 padding); source 60 - 12 = 48"
                    )

            pg.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch807-topleft.png"))
        finally:
            b.close()

    if failures:
        print("FAIL batch807")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch807 — 顶栏左簇：节点 N 单行/两 span/2px 间距 + 分隔线 1×8@+12 + 已保存 nowrap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
