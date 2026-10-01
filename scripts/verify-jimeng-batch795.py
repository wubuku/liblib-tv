"""Jimeng clone batch 795 verifier — Agent 面板几何 + 顶栏让位重排。

Contract (SOURCE_FACT 2026-10-01，登录态，1680×826)：
  面板  aria-label="Agent"，400×802 @[1268,12]，z-40，radius 20px，
        右缘 1668 / 上缘 12 / 下缘 814（inset-y-3 + right-3）。
  重排  面板展开时**顶栏右簇向左让位**，不被面板遮挡且保持可点：
        积分入口右缘 1208（= 1668 - 12(base) - 400(面板) - 16(缝) - 28(用户菜单) - 16(缝)），
        即顶栏 right 内边距由 12 变为 428；面板左缘 1268 与用户菜单右缘 1252 相距 16。
        收起面板后顶栏右缘回到 1668。
  命中  面板展开时，顶栏 分享/更多/积分/用户菜单 四个控件的中心点
        elementFromPoint 必须命中自身子树（不被面板拦截）。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

DRAWER = 'aside[aria-label="Agent"]'
RIGHT_CLUSTER = [
    '[data-testid="canvas-share-trigger"]',
    '[data-testid="canvas-more-trigger"]',
    '[data-testid="canvas-commerce-entry"]',
    '[data-testid="canvas-user-menu-trigger"]',
]


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

    def near(a, b, tol=2.0) -> bool:
        return a is not None and abs(a - b) <= tol

    def hit_test(page, selector: str) -> dict:
        """中心点最上层元素是否属于该控件自身。"""
        return page.evaluate(
            """(sel) => {
              const el = document.querySelector(sel);
              if (!el) return { missing: true };
              const r = el.getBoundingClientRect();
              const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
              return {
                rect: { x: r.x, y: r.y, w: r.width, h: r.height },
                selfHit: !!(top && top.closest(sel)),
                topAria: top ? (top.getAttribute('aria-label')
                            || (top.closest('[aria-label]') || {}).getAttribute?.('aria-label') || '') : '',
              };
            }""",
            selector,
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # ── 面板：Batch 797 起默认**收起**（源站实测），故先显式点开 ──
        # 本批要验的是「面板展开时顶栏让位」这条交互契约，而不是默认态；
        # 默认态本身由 batch 797 断言。源站收起态只有右下角一个 118×34 触发钮。
        drawer = page.locator(DRAWER)
        check("默认收起（batch 797 契约）", drawer.count() == 0, f"count={drawer.count()}")
        trigger = page.locator('[data-testid="ai-trigger-pill"]')
        check("收起态暴露「与 AI 对话」触发钮", trigger.count() == 1, f"count={trigger.count()}")
        if trigger.count() == 1:
            trigger.click()
            page.wait_for_timeout(700)
        check("点击后面板展开", drawer.count() == 1, f"count={drawer.count()}")
        if drawer.count() == 1:
            d = drawer.bounding_box()
            check("面板 400x802 @[1268,12]",
                  near(d["width"], 400) and near(d["height"], 802)
                  and near(d["x"], 1268) and near(d["y"], 12),
                  f"实际 {round(d['x'])},{round(d['y'])} {round(d['width'])}x{round(d['height'])}")
            check("面板右缘 1668", near(d["x"] + d["width"], 1668, 1.0), str(round(d["x"] + d["width"], 2)))
            ds = drawer.evaluate("el => getComputedStyle(el)")
            check("面板 radius 20px", ds["borderTopLeftRadius"] == "20px", ds["borderTopLeftRadius"])
            check("面板 z-index 40", ds["zIndex"] == "40", ds["zIndex"])

        print("— 顶栏让位（面板展开时）—")
        credits = page.locator('[data-testid="canvas-commerce-entry"]').bounding_box()
        check("积分入口右缘 1208", credits is not None and near(credits["x"] + credits["width"], 1208),
              str(round(credits["x"] + credits["width"], 2)) if credits else "None")
        menu = page.locator('[data-testid="canvas-user-menu-trigger"]').bounding_box()
        check("用户菜单右缘 1252", menu is not None and near(menu["x"] + menu["width"], 1252),
              str(round(menu["x"] + menu["width"], 2)) if menu else "None")
        check("用户菜单与面板左缘相距 16",
              menu is not None and drawer.count() == 1 and near(drawer.bounding_box()["x"] - (menu["x"] + menu["width"]), 16),
              str(round(drawer.bounding_box()["x"] - (menu["x"] + menu["width"]), 2)) if menu and drawer.count() else "n/a")
        for sel in RIGHT_CLUSTER:
            ht = hit_test(page, sel)
            check(f"{sel} 未被面板遮挡", ht.get("selfHit") is True,
                  f"top={ht.get('topAria')!r}")
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch795-drawer-open-1680.png"))

        print("— 收起面板后顶栏复原 —")
        collapse = page.locator('button[aria-label="收起"]')
        if collapse.count() == 1:
            collapse.click()
            page.wait_for_timeout(600)
        check("面板已收起", page.locator(DRAWER).count() == 0, f"count={page.locator(DRAWER).count()}")
        menu2 = page.locator('[data-testid="canvas-user-menu-trigger"]').bounding_box()
        check("用户菜单右缘回到 1664（药丸内缩 4）", menu2 is not None and near(menu2["x"] + menu2["width"], 1664, 1.0),
              str(round(menu2["x"] + menu2["width"], 2)) if menu2 else "None")
        pill_right = page.evaluate(
            """() => {
              const el = document.querySelector('[data-testid="canvas-user-menu-trigger"]')
                .closest('.jimeng-chrome-pill');
              return el ? el.getBoundingClientRect().right : null;
            }"""
        )
        check("积分/头像药丸右缘回到 1668", pill_right is not None and near(pill_right, 1668, 1.0), repr(pill_right))
        credits2 = page.locator('[data-testid="canvas-commerce-entry"]').bounding_box()
        check("积分入口右缘回到 1620", credits2 is not None and near(credits2["x"] + credits2["width"], 1620, 1.0),
              str(round(credits2["x"] + credits2["width"], 2)) if credits2 else "None")
        for sel in RIGHT_CLUSTER:
            check(f"收起后 {sel} 可点", hit_test(page, sel).get("selfHit") is True, "covered")

        print("— 重新展开 —")
        page.evaluate(
            """() => {
              // 走真实入口：右下角「与 AI 对话」浮动钮（SOURCE_FACT 118x34 @右下）
              const b = [...document.querySelectorAll('button,[role="button"]')]
                .find((e) => e.getAttribute('aria-label') === '与 AI 对话');
              if (b) b.click();
            }"""
        )
        page.wait_for_timeout(900)
        check("点浮动钮可重新展开面板", page.locator(DRAWER).count() == 1,
              f"count={page.locator(DRAWER).count()}")
        credits3 = page.locator('[data-testid="canvas-commerce-entry"]').bounding_box()
        check("重开后积分入口右缘 1208", credits3 is not None and near(credits3["x"] + credits3["width"], 1208),
              str(round(credits3["x"] + credits3["width"], 2)) if credits3 else "None")

        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 795 Agent 面板几何 + 顶栏让位契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
