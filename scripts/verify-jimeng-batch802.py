"""Jimeng clone batch 802 verifier — 小地图面板落位 + 与底栏相接。

Contract (SOURCE_FACT 2026-10-01 登录态实测，@1680×826，点「小地图」后量得)：

  源站导航 dock 面板 `[class*="navigation-dock"]`
      @[12,656] **164×154**  padding **4px**  gap 4px  flex column
      bg rgb(13,13,13)  radius 8px
    ├ 子元素1  @[16,660] **156×114**  = 小地图 (rgba(255,255,255,0.08) r6)
    └ 子元素2  @[16,778] **156×28**   = 「100%」等 dock 行
      注意 子元素2 与**主底栏**控件同位（选择工具 @[16,778]、缩放 @[124,779]）
      ⇒ 源站是「同一个 dock 变高、小地图插在上方」，不是另浮一个面板。

  复刻是分离浮层（无法把 MiniMap 移出 <ReactFlow>，它需要 flow store 注册），
  故按可实现的等价对齐：
    面板 @[12,656] **164×118**（= 4 padding + 114 + 4），下缘 774 正好贴住
    底栏顶边；两者同底色 rgb(13,13,13) → 视觉连成一整条。
    内层小地图落在 @[16,660] **156×114**。
  修正前：面板 @[16,616]、内层 @[9,641]（`bottom-14 left-4 p-2`）——
          整体偏高 40px、横向错位 7px，且内层跑到壳外左侧。

  命中  面板 @[12,656] 164×118、radius 8、bg rgb(13,13,13)、padding 4；
        内层小地图 @[16,660] 156×114、bg rgba(255,255,255,0.08)、radius 6；
        面板下缘 774 == 底栏顶边（相接无缝隙）；
        底栏本身仍是 @[12,774] 164×36（batch 796 契约，不得被本批破坏）；
        小地图可开关（收起后面板消失）。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

PANEL = '[data-testid="jimeng-minimap-panel"]'
DOCK = ".jimeng-bottom-dock"
MINIMAP = ".react-flow__minimap"


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def near(a, b, tol=1.0) -> bool:
        return a is not None and abs(a - b) <= tol

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2800)

        check("默认不显示小地图面板", page.locator(PANEL).count() == 0,
              f"count={page.locator(PANEL).count()}")

        page.locator('[data-testid="canvas-display-toggle-minimap"]').click()
        page.wait_for_timeout(1000)

        panel = page.locator(PANEL)
        check("点 dock 小地图后面板出现", panel.count() == 1, f"count={panel.count()}")

        if panel.count() == 1:
            pb = panel.bounding_box()
            # 面板：源站是 164×154 的单一 dock（内含小地图 + 原 dock 行），
            # 复刻为分离浮层，故取 164×118 并让下缘贴住底栏顶边 774。
            check("面板 @[12,656] 164×118",
                  near(pb["width"], 164) and near(pb["height"], 118)
                  and near(pb["x"], 12) and near(pb["y"], 656),
                  f"@{round(pb['x'])},{round(pb['y'])} {round(pb['width'])}x{round(pb['height'])}")
            check("面板下缘 774（贴住底栏）", near(pb["y"] + pb["height"], 774),
                  str(round(pb["y"] + pb["height"], 1)))
            ps = panel.evaluate("el => getComputedStyle(el)")
            check("面板 bg rgb(13,13,13)", ps["backgroundColor"] == "rgb(13, 13, 13)", ps["backgroundColor"])
            check("面板 radius 8px", ps["borderTopLeftRadius"] == "8px", ps["borderTopLeftRadius"])
            check("面板 padding 4px", ps["paddingTop"] == "4px" and ps["paddingLeft"] == "4px", ps["padding"])

            mm = page.locator(MINIMAP).first
            check("内层小地图存在", mm.count() == 1, f"count={mm.count()}")
            if mm.count() == 1:
                mb = mm.bounding_box()
                check("小地图 @[16,660] 156×114",
                      near(mb["width"], 156) and near(mb["height"], 114)
                      and near(mb["x"], 16) and near(mb["y"], 660),
                      f"@{round(mb['x'])},{round(mb['y'])} {round(mb['width'])}x{round(mb['height'])}")
                ms = mm.evaluate("el => getComputedStyle(el)")
                check("小地图 bg rgba(255,255,255,0.08)",
                      ms["backgroundColor"] == "rgba(255, 255, 255, 0.08)", ms["backgroundColor"])
                check("小地图 radius 6px", ms["borderTopLeftRadius"] == "6px", ms["borderTopLeftRadius"])

            # 底栏本身不得被本批改动（batch 796 契约）
            dock = page.locator(DOCK)
            if dock.count() == 1:
                db = dock.bounding_box()
                check("底栏仍 @[12,774] 164×36（batch 796 契约）",
                      near(db["width"], 164) and near(db["height"], 36)
                      and near(db["x"], 12) and near(db["y"], 774, 1.5),
                      f"@{round(db['x'])},{round(db['y'])} {round(db['width'])}x{round(db['height'])}")
                check("面板与底栏无缝隙（相接）",
                      near((pb["y"] + pb["height"]), db["y"], 1.0),
                      f"面板下缘 {round(pb['y'] + pb['height'])} vs 底栏顶 {round(db['y'])}")
            else:
                check("底栏存在", False, "未找到 .jimeng-bottom-dock")

            page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch802-minimap-1680.png"))

        # ── 收起 ──
        page.locator('[data-testid="canvas-display-toggle-minimap"]').click()
        page.wait_for_timeout(800)
        check("再点一次可收起", page.locator(PANEL).count() == 0,
              f"count={page.locator(PANEL).count()}")

        check("无 console/page 错误", not errors, "; ".join(errors[:4]))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项不通过")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 802 小地图面板落位 + 与底栏相接（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
