"""Jimeng clone batch 809-topright verifier — 顶栏右簇药丸的边框/padding 与横向漂移。

Contract (SOURCE_FACT 2026-10-03 登录态重测，@1512 视口，两侧同一页面宽度)：

  源站 chrome 药丸分**两种**，不是一种：
    搜索/生成历史 pill @[1139] 68 宽  padding **3px**  border **1px** rgba(255,255,255,.04)
    分享          pill @[1215] 70 宽  padding  4px     border **1px**
    更多          pill @[1293] 36 宽  padding **3px**  border **1px**
    积分+用户菜单  pill @[1337] 163 宽 padding  4px     border **0**

  关键在于**占不占布局**：前三枚的描边是真 border（每边吃掉 1px），
  积分药丸那圈 1px 是 inset shadow（不占布局）。

  改前复刻四枚全是 `p-1` + inset shadow ⇒ 分享药丸 68（源站 70）、
  积分药丸 161（源站 163），右簇整体右漂 +4/+4/+4/+2/+2。
  改后：三枚加 `--bordered`（真 1px border）并把 搜索/历史·更多 的
  padding 收到 3px，三枚药丸宽度**逐个精确对上** 68/70/36；
  残余漂移变成**均匀 +2px**，成因单一 —— 积分数值是 mock，
  积分药丸比源站窄 2px（161 vs 163），右对齐下把它左侧所有东西右推 2px。

验收取向：
  - 断言**相邻药丸间距都是 8px**（源站与复刻一致），这是横向排布的不变量；
  - 断言药丸**宽度绝对值** 68/70/36 —— 这三个数由内容（28+4+28 / 60 / 28）
    推导，与 mock 数值无关，不会漂。**积分药丸不在此列**：它的宽度跟着
    mock 积分数值走（复刻 161 / 源站 163），只能断言 border/padding 分档，
    宽度留给「漂移均匀性」那条断言去管；
  - 断言 border-width / padding 的**分档**（前三枚 1px、积分药丸 0px），
    这才是本批真正修的东西；
  - **不断言**「整体偏移 == 0」：那会把 mock 积分数值变成 brittle 依赖。
    改判「四枚药丸的 x 偏移彼此相同」—— 即漂移是均匀的、单一成因的。
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

# 源站实测值（见 docstring）
SOURCE_PILL = {
    "search": {"x": 1139, "w": 68, "pad": 3, "bw": 1},
    "share": {"x": 1215, "w": 70, "pad": 4, "bw": 1},
    "more": {"x": 1293, "w": 36, "pad": 3, "bw": 1},
    "credits": {"x": 1337, "w": 163, "pad": 4, "bw": 0},
}

PROBE = """() => {
  const pick = (lb) => [...document.querySelectorAll('button,a')]
    .find(b => (b.getAttribute('aria-label') || '') === lb);
  const pillOf = (el) => {
    if (!el) return null;
    let n = el;
    for (let i = 0; i < 6 && n; i++) {
      const bg = getComputedStyle(n).backgroundColor;
      const m = /^rgba?\\(([^)]+)\\)$/.exec(bg) || /^color\\(srgb\\s+([^)]+)\\)$/.exec(bg);
      const a = m ? (m[1].trim().split(/[\\s,/]+/)[3] || '1').trim() : '1';
      if (m && parseFloat(a) > 0.02) return n;
      n = n.parentElement;
    }
    return null;
  };
  const info = (el) => {
    const p = pillOf(el);
    if (!p) return null;
    const r = p.getBoundingClientRect(); const s = getComputedStyle(p);
    return { x: Math.round(r.x), w: Math.round(r.width),
             padX: Math.round(parseFloat(s.paddingLeft)),
             bw: Math.round(parseFloat(s.borderTopWidth)),
             bcol: s.borderTopColor, radius: s.borderTopLeftRadius,
             cls: (p.className || '').toString() };
  };
  const sBtn = pick('搜索'), hBtn = pick('生成历史');
  const user = pick('用户菜单');
  const cr = [...document.querySelectorAll('button,a')]
    .find(b => (b.getAttribute('aria-label') || '').startsWith('Credits'));
  return {
    search: info(sBtn), share: info(pick('分享')), more: info(pick('更多')),
    credits: info(cr),
    // 搜索与生成历史共处同一枚药丸
    samePill: !!(sBtn && hBtn && pillOf(sBtn) === pillOf(hBtn)),
    userBtnX: user ? Math.round(user.getBoundingClientRect().x) : null,
    innerGap: (() => {
      if (!sBtn || !hBtn) return null;
      const a = sBtn.getBoundingClientRect(), b = hBtn.getBoundingClientRect();
      return Math.round(b.x - (a.x + a.width));
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
            # dev server 刚重启时首屏编译慢，等右簇真的出现再断言
            pg.wait_for_selector('[aria-label="搜索"]', timeout=45000)
            pg.wait_for_timeout(1200)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(700)
            d = pg.evaluate(PROBE)

            for key in ("search", "share", "more", "credits"):
                got, want = d.get(key), SOURCE_PILL[key]
                if not got:
                    failures.append(f"{key} pill not found")
                    continue
                # 积分药丸的宽度跟着 mock 积分数值走，不做绝对断言
                if key != "credits" and got["w"] != want["w"]:
                    failures.append(
                        f"{key} pill width {got['w']}, want {want['w']} (source @{want['x']})"
                    )
                if got["padX"] != want["pad"]:
                    failures.append(
                        f"{key} pill padding-x {got['padX']}px, want {want['pad']}px"
                    )
                if got["bw"] != want["bw"]:
                    failures.append(
                        f"{key} pill border-width {got['bw']}px, want {want['bw']}px"
                        + ("  (前三枚必须是**真 border**才占布局)"
                           if want["bw"] else "  (积分药丸的描边是 inset shadow，不占布局)")
                    )

            # 搜索/生成历史必须仍在同一枚药丸内，且内缝 4px
            if not d["samePill"]:
                failures.append("搜索 / 生成历史 no longer share one pill")
            if d["innerGap"] not in (None, 4):
                failures.append(f"搜索→生成历史 inner gap {d['innerGap']}px, want 4")

            # 相邻药丸间距 8px（两侧一致，横向排布的不变量）
            # 注意方向：a 在左、b 在右，间隙 = b.left − a.right
            for a, bn in (("search", "share"), ("share", "more"), ("more", "credits")):
                pa, pb = d.get(a), d.get(bn)
                if pa and pb:
                    gap = pb["x"] - (pa["x"] + pa["w"])
                    if gap != 8:
                        failures.append(f"{a} → {bn} gap = {gap}px, want 8")

            # 漂移必须**均匀**：四枚药丸的 x 偏移彼此相同（单一成因）
            offs = [d[k]["x"] - SOURCE_PILL[k]["x"] for k in ("search", "share", "more", "credits") if d.get(k)]
            if len(offs) == 4 and len(set(offs)) != 1:
                failures.append(
                    f"right-cluster drift is not uniform: {offs} "
                    "(source x offsets — should all be equal, i.e. one root cause)"
                )
            elif offs:
                print(f"  右簇整体偏移 {offs[0]:+d}px（残余成因：mock 积分数值窄 2px）")

            # 右锚点：用户菜单必须与源站同位
            if d["userBtnX"] != 1468:
                failures.append(f"用户菜单 x={d['userBtnX']}, want 1468 (right anchor)")

            pg.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch809-topright.png"))
        finally:
            b.close()

    if failures:
        print("FAIL batch809-topright")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch809-topright — 右簇药丸 68/70/36 精确、border 1px/0px 分档正确、漂移均匀")
    return 0


if __name__ == "__main__":
    sys.exit(main())
