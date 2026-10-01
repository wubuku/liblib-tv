#!/usr/bin/env python
"""batch 837-dock verifier —— 底部 dock 四枚钮的 aria 信号，以及「两条路不能漂」。

批 835 普查 dock 时实测到源站三枚 28×28 图标钮都带 `aria-pressed`：
选择工具 **false**（点一下变 **true**）、小地图 false、显示连线 **true**，
而 zoom 钮带的是 `aria-expanded="false"`、**没有** aria-pressed。
复刻此前**一枚信号都没发**，且「选择工具」钮的 onClick 是
`setToolActive("select")` —— 强制置位，于是「已经是 select 时点它」什么都不会
发生（本地普查把它记进 UNVERIFIABLE，理由是复刻自己写的）。

本批三件事：
1. 三枚图标钮补 `aria-pressed`，小地图/连线的初值与源站实测**本就一致**
   （store 的 minimapOpen=false、edgesVisible=true）
2. zoom 钮补 `aria-expanded`（且**不给** aria-pressed —— 源站就没有）
3. 「选择工具」改成 toggle，并与 V 快捷键**共用 store 里那一条**实现

⚠ 取值方向故意与源站相反（记在台账 §52 的 837-a）：源站默认 false、点一下 true，
语义从 aria 推不出来；复刻按自己的状态模型发 `toolActive === "select"`，
宁可让序列反一次，也不发语义颠倒的 aria-pressed。所以本脚本断言的是
「**翻转**」与「与 V 键同步」，**不是**「等于 false/true」。
"""

from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1680, "height": 826}

DOCK = {
    "tool": '[data-testid="canvas-pointer-tool-toggle"]',
    "minimap": '[data-testid="canvas-display-toggle-minimap"]',
    "edges": '[data-testid="canvas-display-toggle-connections"]',
    "zoom": '[data-testid="canvas-zoom-percent"]',
}
MINIMAP_PANEL = '[data-testid="jimeng-minimap-panel"]'


def clear_dev_portal(page) -> None:
    """摘掉 Next.js dev 指示器（dev-only 的量具遮挡，不是产品缺陷）。

    事实：dock 最左那枚钮 @[16,778,28,28]，其中心点的命中元素是 NEXTJS-PORTAL。
    `force=True` 救不了 —— force 只跳过可点性检查，事件仍投给最上层的 portal，
    React 的 onClick 不会触发。摘掉 portal 之后点击恢复正常命中判定。
    """
    page.evaluate("() => document.querySelector('nextjs-portal')?.remove()")


def main() -> int:
    failures: list[str] = []
    passed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        if ok:
            passed += 1
        else:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def attr(page, sel: str, name: str) -> str | None:
        loc = page.locator(sel)
        return loc.first.get_attribute(name) if loc.count() else None

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        try:
            page.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if page.evaluate("() => !!document.querySelector('.react-flow__node')"):
                    break
                page.wait_for_timeout(1000)

            print("— ① 三枚图标钮都有 aria-pressed，两枚初值与源站实测一致 —")
            for key in ("tool", "minimap", "edges"):
                v = attr(page, DOCK[key], "aria-pressed")
                check(f"{key} 有 aria-pressed（此前一枚都没有）", v is not None, str(v))
            check("小地图初值 false（源站实测 false，store minimapOpen=false）",
                  attr(page, DOCK["minimap"], "aria-pressed") == "false",
                  str(attr(page, DOCK["minimap"], "aria-pressed")))
            check("连线初值 true（源站实测 true，store edgesVisible=true）",
                  attr(page, DOCK["edges"], "aria-pressed") == "true",
                  str(attr(page, DOCK["edges"], "aria-pressed")))
            check("zoom 钮有 aria-expanded=false（源站实测）",
                  attr(page, DOCK["zoom"], "aria-expanded") == "false",
                  str(attr(page, DOCK["zoom"], "aria-expanded")))
            check("zoom 钮**没有** aria-pressed（源站实测 None，别给错信号）",
                  attr(page, DOCK["zoom"], "aria-pressed") is None,
                  str(attr(page, DOCK["zoom"], "aria-pressed")))

            print("— ② 点它真有**后果**（判据落在后果，不是属性）—")
            before_map = page.locator(MINIMAP_PANEL).count()
            page.locator(DOCK["minimap"]).first.click()
            page.wait_for_timeout(450)
            after_map = page.locator(MINIMAP_PANEL).count()
            check("点小地图 ⇒ 浮层出现，且 aria-pressed 翻成 true",
                  after_map > before_map and attr(page, DOCK["minimap"], "aria-pressed") == "true",
                  f"panel {before_map}→{after_map} pressed={attr(page, DOCK['minimap'], 'aria-pressed')}")
            page.locator(DOCK["minimap"]).first.click()
            page.wait_for_timeout(450)
            check("再点 ⇒ 浮层消失、aria-pressed 回 false（两向都验）",
                  page.locator(MINIMAP_PANEL).count() == before_map
                  and attr(page, DOCK["minimap"], "aria-pressed") == "false",
                  f"panel={page.locator(MINIMAP_PANEL).count()}")

            # ⚠ BLOCKED_BY_FIXTURE：demo 的 store 是 `edges: []` —— **零条边**，
            #   所以「切换后边数变化」这条判据在本 fixture 下**无从断言**
            #   （0 → 0 恒成立）。试过用真实拖拽造一条：从 node0 右侧热区
            #   （批 828 实测 [-30,44,60,120]）拖到 node1 左侧，未生成边。
            #   因此本批只钉**信号**（aria-pressed 两向翻转），可见后果留作
            #   OPEN_QUESTION 837-b，不拿恒真断言充数。
            page.locator(DOCK["edges"]).first.click()
            page.wait_for_timeout(450)
            check("点连线 ⇒ aria-pressed 翻成 false（信号；可见后果见 BLOCKED_BY_FIXTURE）",
                  attr(page, DOCK["edges"], "aria-pressed") == "false",
                  str(attr(page, DOCK["edges"], "aria-pressed")))
            check("fixture 确实零条边（所以后果判据不可断言，不是判据写错）",
                  page.locator(".react-flow__edge").count() == 0,
                  f"edges={page.locator('.react-flow__edge').count()}")
            page.locator(DOCK["edges"]).first.click()
            page.wait_for_timeout(450)
            check("再点 ⇒ 翻回 true（两向都验）",
                  attr(page, DOCK["edges"], "aria-pressed") == "true",
                  str(attr(page, DOCK["edges"], "aria-pressed")))

            page.locator(DOCK["zoom"]).first.click()
            page.wait_for_timeout(400)
            check("点 zoom ⇒ 菜单出现且 aria-expanded 变 true",
                  page.locator('[data-testid="canvas-zoom-menu"]').count() == 1
                  and attr(page, DOCK["zoom"], "aria-expanded") == "true",
                  f'pressed/expanded={attr(page, DOCK["zoom"], "aria-expanded")}')
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

            print("— ③ 「选择工具」是**二态**（此前点它等于没反应）—")
            # ⚠ 这枚钮在 dock 最左端，而 **Next.js dev 指示器**恰好浮在视口左下角：
            #   命中测试实测 `document.elementFromPoint(钮中心)` 返回 NEXTJS-PORTAL
            #   （该 portal 自身 rect 是 0×0，但它 shadow 里的指示器盖住了那个点），
            #   普通 click 会 retry 到 30s 超时。
            #   ⚠ **试过 force=True，不行**：force 只跳过可点性**检查**，事件仍投在
            #   最上层的 portal 上，onClick 根本不触发（aria-pressed 纹丝不动）。
            #   所以改成**把 portal 从测试页里摘掉** —— 修的是量具，不是产品。
            #   生产构建里没有这个 portal；将来谁遇到同一个超时，别去「修」dock。
            t0 = attr(page, DOCK["tool"], "aria-pressed")
            clear_dev_portal(page)
            page.locator(DOCK["tool"]).first.click()
            page.wait_for_timeout(400)
            t1 = attr(page, DOCK["tool"], "aria-pressed")
            check("点它 ⇒ aria-pressed 翻转（本批核心：此前恒为 select 什么都不会变）",
                  t0 is not None and t1 is not None and t0 != t1, f"{t0} → {t1}")
            clear_dev_portal(page)
            page.locator(DOCK["tool"]).first.click()
            page.wait_for_timeout(400)
            check("再点 ⇒ 翻回原值（是开关，不是单向置位）",
                  attr(page, DOCK["tool"], "aria-pressed") == t0,
                  f'{attr(page, DOCK["tool"], "aria-pressed")} vs {t0}')

            print("— ④ 按钮与 V 键走**同一条**实现（两路不许漂）—")
            by_btn = attr(page, DOCK["tool"], "aria-pressed")
            page.locator("body").first.click(position={"x": 700, "y": 700})
            page.keyboard.press("v")
            page.wait_for_timeout(400)
            by_key = attr(page, DOCK["tool"], "aria-pressed")
            check("按 V ⇒ 也翻转", by_key is not None and by_key != by_btn, f"{by_btn} → {by_key}")
            clear_dev_portal(page)
            page.locator(DOCK["tool"]).first.click()
            page.wait_for_timeout(400)
            check("再点按钮 ⇒ 回到按 V 之前的状态（同一状态机，不是两套）",
                  attr(page, DOCK["tool"], "aria-pressed") == by_btn,
                  f'{attr(page, DOCK["tool"], "aria-pressed")} vs {by_btn}')

            print("— ⑤ 反向自检 —")
            check("三条 toggle 的 aria-pressed 此刻都能读到（信号没被卸载）",
                  all(attr(page, DOCK[k], "aria-pressed") is not None for k in ("tool", "minimap", "edges")))
            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — batch 837 dock "
          f"{passed}/{passed + len(failures)}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
