"""Jimeng clone batch 794 verifier — 顶栏结构对齐源站实测。

Contract (SOURCE_FACT 2026-10-01，登录态，1680×826):
  左簇 230×40 r8 —
    返回首页 logo 40×40 @[12,10] · 项目名 68×28 @[52,16] 13px/22 w500
    radius 6/2/2/6 · 项目箭头 20×28 @[120,16] svg16 radius 2/6/6/2
    节点摘要 28×28 @[156,16] 10px/18 white/60 · 距箭头 16px
  右簇 间距 16px —
    搜索 28×28 @[1311,16] r12 · 生成历史 28×28 @[1343,16] r12 · 药丸内 4px 缝
    分享 60×28 @[1388,16] · 更多 28×28 @[1465,16]
    积分 111×28 @[1509,16] 12px 品牌色数字 + 基础会员
    用户菜单 28×28 @[1636,16]
  四个触发器的浮层 —
    分享   400×251 右缘对齐顶栏右内边距
    更多   role=menu 200×84，两项 192×36，水平以触发钮居中
    项目   240×200 **左缘**对齐顶栏左内边距
    节点 N role=dialog 200 宽，高度内容驱动 40N+52（N=条目数），水平以触发钮居中
"""

import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def box(page, selector: str):
    el = page.locator(selector).first
    if el.count() == 0:
        return None
    return el.bounding_box()


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

    def box_matches(name, sel, x, y, w, h, tol=2.0) -> None:
        b = box(page, sel)
        if b is None:
            check(name, False, f"selector 未命中 {sel}")
            return
        ok = near(b["x"], x, tol) and near(b["y"], y, tol) and near(b["width"], w, tol) and near(b["height"], h, tol)
        check(
            name,
            ok,
            f"期望 [{x},{y} {w}x{h}] 实际 [{round(b['x'])},{round(b['y'])} {round(b['width'])}x{round(b['height'])}]",
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # AI 抽屉默认展开且 inset-y-3，会盖住顶栏右簇（既有惯例同 batch 793：
        # 验顶栏前先收起抽屉）。抽屉本身契约不在本批范围。
        collapse = page.locator('button[aria-label="收起"]')
        if collapse.count() == 1:
            collapse.click()
            page.wait_for_timeout(400)

        print("— 左簇 —")
        box_matches("logo 返回首页 40x40@12,10", '[data-testid="canvas-project-logo"]', 12, 10, 40, 40)
        box_matches("项目名 68x28@52,16", '[data-testid="canvas-project-title-trigger"]', 52, 16, 68, 28)
        box_matches("项目箭头 20x28@120,16", '[data-testid="canvas-project-trigger"]', 120, 16, 20, 28)
        box_matches("节点摘要 28x28@156,16", '[data-testid="canvas-node-summary-trigger"]', 156, 16, 28, 28)

        title = page.locator('[data-testid="canvas-project-title-trigger"]')
        ts = title.evaluate("el => getComputedStyle(el)")
        check("项目名字号 13px/22 w500", ts["fontSize"] == "13px" and ts["lineHeight"] == "22px" and ts["fontWeight"] == "500",
              f"{ts['fontSize']}/{ts['lineHeight']} w{ts['fontWeight']}")
        check("项目名左圆角 6/2/2/6", ts["borderTopLeftRadius"] == "6px" and ts["borderBottomRightRadius"] == "2px",
              f"{ts['borderTopLeftRadius']} .. {ts['borderBottomRightRadius']}")

        arrow = page.locator('[data-testid="canvas-project-trigger"]')
        ast = arrow.evaluate("el => getComputedStyle(el)")
        check("箭头右圆角 2/6/6/2", ast["borderTopRightRadius"] == "6px" and ast["borderTopLeftRadius"] == "2px",
              f"{ast['borderTopLeftRadius']} .. {ast['borderTopRightRadius']}")

        ns = page.locator('[data-testid="canvas-node-summary-trigger"]')
        nst = ns.evaluate("el => getComputedStyle(el)")
        check("节点摘要 10px/18 常规字重", nst["fontSize"] == "10px" and nst["lineHeight"] == "18px" and nst["fontWeight"] == "400",
              f"{nst['fontSize']}/{nst['lineHeight']} w{nst['fontWeight']}")
        check("节点摘要文案「节点 2」", ns.inner_text().replace(" ", "") == "节点2", repr(ns.inner_text()))

        # 节点计数随画布变化 (batch 70/71 契约，batch 794 保留)
        check("节点摘要 aria 含计数",
              ns.get_attribute("aria-label") == "Canvas node summary: 节点 2",
              repr(ns.get_attribute("aria-label")))

        print("— 右簇（尺寸精确；横向按右缘 + 间隙断言，右锚簇的绝对 x 是派生量）—")
        RIGHT = [
            ('[data-testid="topbar-search"]', 28, "搜索"),
            ('button[aria-label="生成历史"]', 28, "生成历史"),
            ('[data-testid="canvas-share-trigger"]', 60, "分享"),
            ('[data-testid="canvas-more-trigger"]', 28, "更多"),
            ('[data-testid="canvas-commerce-entry"]', 111, "积分"),
            ('[data-testid="canvas-user-menu-trigger"]', 28, "用户菜单"),
        ]
        boxes = []
        for sel, w, label in RIGHT:
            b = box(page, sel)
            if b is None:
                check(f"{label} 命中", False, f"未命中 {sel}")
                continue
            check(f"{label} {w}x28@y16", near(b["width"], w) and near(b["height"], 28) and near(b["y"], 16),
                  f"实际 {round(b['width'])}x{round(b['height'])}@y{round(b['y'])}")
            boxes.append((label, b))
        if len(boxes) == len(RIGHT):
            order = [x[0] for x in boxes]
            check("右簇顺序与源站一致",
                  order == ["搜索", "生成历史", "分享", "更多", "积分", "用户菜单"], str(order))
            # SOURCE_FACT (batch 795 复查): 头像在 163×36 药丸内、药丸右内边距 4，
            # 故**药丸**右缘 1668 而头像按钮右缘 1664。
            last_right = boxes[-1][1]["x"] + boxes[-1][1]["width"]
            check("头像按钮右缘 1664（药丸内缩 4）", near(last_right, 1664, 1.0), f"实际 {round(last_right, 2)}")
            pill_right = page.evaluate(
                """() => {
              const el = document.querySelector('[data-testid="canvas-user-menu-trigger"]')
                .closest('.jimeng-chrome-pill');
              return el ? el.getBoundingClientRect().right : null;
            }"""
            )
            check("积分/头像药丸右缘 1668", pill_right is not None and near(pill_right, 1668, 1.0), repr(pill_right))
            # 药丸内 4px 缝；药丸之间 16px（源站实测 13/17/16/16，取 16±3）
            check("搜索→生成历史 4px 缝",
                  near(boxes[1][1]["x"] - (boxes[0][1]["x"] + boxes[0][1]["width"]), 4, 1.0),
                  f"实际 {round(boxes[1][1]['x'] - boxes[0][1]['x'] - boxes[0][1]['width'], 2)}")
            # SOURCE_FACT (batch 795 复查): 药丸之间 8px；按钮到按钮 8+4+4=16。
            # batch 795 把药丸从「按钮自带背景」改成「外层 36px 高药丸」后，
            # 簇内 flex gap 由 16 修正为 8。
            cluster_gap = page.evaluate(
                """() => {
              const el = document.querySelector('[data-testid="topbar-search"]')
                .closest('div.pointer-events-auto.flex.h-10');
              return el ? getComputedStyle(el).gap : null;
            }"""
            )
            check("右簇药丸间隙 8px", cluster_gap == "8px", repr(cluster_gap))
            # 控件到控件的实际视觉间距：首个跨药丸边界，含药丸 4px 内缩，
            # 源站实测 17、其余 16/16/16，故统一放宽到 13..21。
            for i in range(1, len(boxes) - 1):
                gap = boxes[i + 1][1]["x"] - (boxes[i][1]["x"] + boxes[i][1]["width"])
                check(f"{boxes[i][0]}→{boxes[i + 1][0]} 视觉间隙 13..21", 13.0 <= gap <= 21.0, f"实际 {round(gap, 2)}")

        credits = page.locator('[data-testid="canvas-commerce-entry"]')
        ctext = re.sub(r"\s+", "", credits.inner_text())
        check("积分文案「745 基础会员」", ctext == "745基础会员", repr(credits.inner_text()))
        check("积分 aria 为 Credits 契约",
              credits.get_attribute("aria-label") == "Credits: 745 · 基础会员",
              repr(credits.get_attribute("aria-label")))

        share_t = page.locator('[data-testid="canvas-share-trigger"]')
        sst = share_t.evaluate("el => getComputedStyle(el)")
        check("分享字号 16px/24 w500", sst["fontSize"] == "16px" and sst["lineHeight"] == "24px" and sst["fontWeight"] == "500",
              f"{sst['fontSize']}/{sst['lineHeight']} w{sst['fontWeight']}")

        print("— 分享浮层 —")
        share_t.click()
        page.wait_for_timeout(400)
        sp = box(page, '[data-testid="topbar-share-panel"]')
        check("分享面板 400x251", sp is not None and near(sp["width"], 400) and near(sp["height"], 251), str(sp))
        check("分享面板右缘对齐 1668", sp is not None and near(sp["x"] + sp["width"], 1668), str(sp))
        sp_txt = page.locator('[data-testid="topbar-share-panel"]').inner_text()
        for frag in ["分享画布", "复制链接", "仅自己可访问", "只有你可以通过此链接访问画布",
                     "创建团队，与成员在画布实时协作", "创建团队"]:
            check(f"分享面板含「{frag}」", frag in sp_txt, repr(sp_txt[:120]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch794-share-panel-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        check("Escape 关闭分享面板", box(page, '[data-testid="topbar-share-panel"]') is None, "still open")

        print("— 更多菜单 —")
        page.locator('[data-testid="canvas-more-trigger"]').click()
        page.wait_for_timeout(400)
        mm = box(page, '[data-testid="topbar-more-menu"]')
        check("更多菜单 200x84", mm is not None and near(mm["width"], 200) and near(mm["height"], 84), str(mm))
        items = page.locator('[data-testid="topbar-more-menu"] [role="menuitem"]')
        check("更多菜单两项", items.count() == 2, f"count={items.count()}")
        if items.count() == 2:
            i0 = items.nth(0).bounding_box()
            check("菜单项 192x36", near(i0["width"], 192) and near(i0["height"], 36), str(i0))
            check("菜单文案 项目信息/复制项目",
                  items.nth(0).inner_text().strip() == "项目信息" and items.nth(1).inner_text().strip() == "复制项目",
                  f"{items.nth(0).inner_text()!r}/{items.nth(1).inner_text()!r}")
            # SOURCE_FACT: 菜单以触发钮水平居中
            trig = page.locator('[data-testid="canvas-more-trigger"]').bounding_box()
            check("菜单以触发钮居中",
                  near(mm["x"] + mm["width"] / 2, trig["x"] + trig["width"] / 2),
                  f"menu_cx={round(mm['x'] + mm['width'] / 2)} trig_cx={round(trig['x'] + trig['width'] / 2)}")
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch794-more-menu-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 项目面板 —")
        page.locator('[data-testid="canvas-project-trigger"]').click()
        page.wait_for_timeout(400)
        pp = box(page, '[data-testid="topbar-project-panel"]')
        check("项目面板 240x200", pp is not None and near(pp["width"], 240) and near(pp["height"], 200), str(pp))
        # SOURCE_FACT: 左缘对齐顶栏左内边距 (x=12)
        check("项目面板左缘 x=12", pp is not None and near(pp["x"], 12), str(pp))
        pp_txt = page.locator('[data-testid="topbar-project-panel"]').inner_text()
        for frag in ["项目", "未命名项目", "视频创作", "新建画布项目"]:
            check(f"项目面板含「{frag}」", frag in pp_txt, repr(pp_txt[:120]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch794-project-panel-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 节点摘要浮层 —")
        page.locator('[data-testid="canvas-node-summary-trigger"]').click()
        page.wait_for_timeout(400)
        np_ = box(page, '[data-testid="topbar-node-summary"]')
        # batch 804 修正：高度是内容驱动的 H=40N+52（794 当初只看到 1 个条目才读成 92）。
        # 写死数值会在节点数一变时就假失败，改为按条目数套公式。
        ns_rows = page.locator('[data-testid="topbar-node-summary"] > div > button').count()
        expect_h = 40 * ns_rows + 52
        check(f"节点摘要弹层 200x(40N+52)，N={ns_rows} → {expect_h}",
              np_ is not None and near(np_["width"], 200) and near(np_["height"], expect_h), str(np_))
        ntrig = page.locator('[data-testid="canvas-node-summary-trigger"]').bounding_box()
        check("节点摘要弹层以触发钮居中",
              np_ is not None and near(np_["x"] + np_["width"] / 2, ntrig["x"] + ntrig["width"] / 2),
              str(np_))
        np_txt = page.locator('[data-testid="topbar-node-summary"]').inner_text()
        check("节点摘要弹层含「查看项目信息」", "查看项目信息" in np_txt, repr(np_txt[:120]))
        check("节点摘要弹层含节点标题", "视频 1" in np_txt, repr(np_txt[:120]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch794-node-summary-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 互斥与回归 —")
        page.locator('[data-testid="canvas-more-trigger"]').click()
        page.wait_for_timeout(250)
        page.locator('[data-testid="canvas-project-trigger"]').click()
        page.wait_for_timeout(250)
        check("浮层互斥：开项目关更多", box(page, '[data-testid="topbar-more-menu"]') is None
              and box(page, '[data-testid="topbar-project-panel"]') is not None, "both/neither open")
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)

        # 积分入口仍打开会员弹层 (batch 13/26/28/30/43/57/59 契约)
        page.locator('[data-testid="canvas-commerce-entry"]').click()
        page.wait_for_timeout(500)
        body = page.locator("body").inner_text()
        check("积分入口打开会员弹层", "积分详情" in body and "745" in body, body[:160])
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # 画布本体未被顶栏改动影响
        check("画布仍有 2 节点", page.locator(".react-flow__node").count() == 2,
              f"count={page.locator('.react-flow__node').count()}")

        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch794-topbar-1680.png"))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 794 顶栏结构对齐契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
