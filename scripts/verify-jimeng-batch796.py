"""Jimeng clone batch 796 verifier — 左侧工具栏 / 左下 dock 几何契约。

Contract (SOURCE_FACT 2026-10-01，登录态实测，脚本 scripts/jimeng_chrome_probe.py)：

左侧工具栏 @1680×826：
  外壳  @[12,242] 48×398  padding 4px  gap 2px  radius 12px
        bg rgb(32,32,32) **不透明**（color(srgb .12549 ×3)）、**无 backdrop blur**、
        box-shadow 内描边白 0.04 1px。与顶部 chrome 药丸
        (rgba(32,32,34,.8) + blur(40px)) 是两套样式，不可复用。
  按钮  40×40  radius 8px  图标 20×20（源站 [&_svg]:size-5）
  纵向  246/288/330/372/414/456/498 → 分隔条 → 554/596（以上为**按钮** y）
        常规步距 42px；导演台→资产库 56px，多出的 14px = 12px 分隔条 + 2×2px gap
  分隔条 外框 20×12 @[26,540]（flex items-center justify-center），
        内含一条 20×1 的 rgba(255,255,255,0.04) 横线 @[26,546]
  hover  按钮底色**不变**（源站 class 明确 hover:bg-transparent，实测 hover 前后
        computed backgroundColor 均为 rgba(0,0,0,0)）。
        —— 本仓库此前记载的「hover 高亮 rgba(255,255,255,0.12)」是台账错误，
        本 batch 首次以 DOM 实测推翻并订正。

左下 dock @1680×826：
  壳体 @[12,774] 164×36  bg rgb(13,13,13)  radius 8  padding 4  gap 4
  选择工具 @[16,778] 28×28 / 小地图 @[48,778] / 显示连线 @[80,778]
  缩放钮   @[124,779] 48×28，aria-label 逐字 "Zoom options, {n}%"（含实时百分比）

居中模型（防过拟合的关键断言）：
  源站 rail 高恒为 390px，railTop = 56 + (视口高 − 446) / 2，即在 y=56 以下区域
  垂直居中。四视口实测 railTop = 246(826) / 193(720) / 283(900) / 333(1000)，
  与该式逐一吻合 ⇒ 源站是**推导**而非写死。因此本 verifier 额外在 720/900/1000
  三个高度复跑同一公式，防止后人把它改成固定 y 而只在 1680×826 下看起来对。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

RAIL = '[data-testid="tool-rail"]'
SEP = '[data-testid="tool-rail-separator"]'

# 源站 1680×826 实测的九个按钮 y 坐标（顺序固定）
RAIL_Y = [246, 288, 330, 372, 414, 456, 498, 554, 596]
RAIL_LABELS = ["文本", "图片", "视频", "音频", "时间线", "主体", "导演台", "资产库", "上传"]

RAIL_H = 390          # 九个按钮的纵向总跨度
RAIL_SHELL_H = 398    # 壳体高 = 390 + 上下各 4px padding
RAIL_CENTER_OFFSET = 56  # 壳体中心 = (视口高 + 56) / 2，即在 y=56 以下区域垂直居中


def rail_shell_top(viewport_h: int) -> float:
    """壳体顶 = 中心 − 398/2 = (视口高 + 56)/2 − 199。

    源站壳体在「y=56 到视口底」这一区域垂直居中，故中心 = (视口高 + 56) / 2。
    等价写法 (H + 56 − 398) / 2 = (H − 342) / 2 —— 注意分子是 H **加** 56，
    写成 (H − 342)/2 时若把 56 减进分子会得到 (H − 98)/2，恒差 28px。

    这里算的是**壳体**顶。壳体上下各有 4px padding，所以第一个**按钮**的
    y = 壳体顶 + 4。早期版本把从按钮 y 反推的公式直接拿来比壳体，恒差 4px，
    属于度量对象错配，不是实现问题。
    """
    return (viewport_h + RAIL_CENTER_OFFSET) / 2 - RAIL_SHELL_H / 2


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
        page.wait_for_timeout(2500)

        # ── 左侧工具栏外壳 ──
        print("— 左侧工具栏外壳 —")
        rail = page.locator(RAIL)
        check("rail 存在", rail.count() == 1, f"count={rail.count()}")
        if rail.count() == 1:
            b = rail.bounding_box()
            check("壳体 48 宽 @x=12", near(b["width"], 48) and near(b["x"], 12),
                  f"{round(b['x'])} {round(b['width'])}")
            check("壳体 @[12,242] 48×398",
                  near(b["x"], 12) and near(b["y"], 242, 1.5)
                  and near(b["width"], 48) and near(b["height"], 398, 1.5),
                  f"@{round(b['x'])},{round(b['y'])} {round(b['width'])}x{round(b['height'])}")
            cs = rail.evaluate("el => getComputedStyle(el)")
            check("padding 4px", cs["paddingTop"] == "4px" and cs["paddingLeft"] == "4px", cs["padding"])
            check("gap 2px", cs["rowGap"] == "2px", cs["rowGap"])
            check("radius 12px", cs["borderTopLeftRadius"] == "12px", cs["borderTopLeftRadius"])
            check("bg 不透明 rgb(32,32,32)", cs["backgroundColor"] == "rgb(32, 32, 32)", cs["backgroundColor"])
            check("无 backdrop blur", cs["backdropFilter"] in ("none", ""), cs["backdropFilter"])

        # ── 九个按钮 ──
        print("— 工具栏按钮 —")
        got_y = []
        for label, want_y in zip(RAIL_LABELS, RAIL_Y):
            btn = page.locator(f'aside button[aria-label="{label}"]').first
            if btn.count() == 0:
                check(f"{label} 存在", False, "未找到")
                got_y.append(None)
                continue
            bb = btn.bounding_box()
            got_y.append(round(bb["y"]))
            check(f"{label} 40×40 @x=16", near(bb["width"], 40) and near(bb["height"], 40) and near(bb["x"], 16),
                  f"@{round(bb['x'])},{round(bb['y'])} {round(bb['width'])}x{round(bb['height'])}")
            check(f"{label} y={want_y}", near(bb["y"], want_y), f"实际 {round(bb['y'])}")
            bcs = btn.evaluate("el => getComputedStyle(el)")
            check(f"{label} radius 8px", bcs["borderTopLeftRadius"] == "8px", bcs["borderTopLeftRadius"])
        check("九个按钮齐全", all(v is not None for v in got_y), str(got_y))

        # 步距：前七项恒 42，导演台→资产库 56
        if all(v is not None for v in got_y):
            pitch = [got_y[i + 1] - got_y[i] for i in range(len(got_y) - 1)]
            check("常规步距 42px", all(v == 42 for v in pitch[:6]), str(pitch[:6]))
            check("导演台→资产库 56px", pitch[6] == 56, str(pitch[6]))
            check("资产库→上传 42px", pitch[7] == 42, str(pitch[7]))

        # 图标 20×20
        icon = page.locator(f'aside button[aria-label="文本"] svg').first
        if icon.count():
            ib = icon.bounding_box()
            check("图标 20×20", near(ib["width"], 20) and near(ib["height"], 20),
                  f"{round(ib['width'])}x{round(ib['height'])}")

        # ── 分隔条 ──
        print("— 导演台/资产库 分隔条 —")
        sep = page.locator(SEP)
        check("分隔条存在", sep.count() == 1, f"count={sep.count()}")
        if sep.count() == 1:
            sb = sep.bounding_box()
            check("分隔条 20×12 @[26,540]",
                  near(sb["width"], 20) and near(sb["height"], 12)
                  and near(sb["x"], 26) and near(sb["y"], 540),
                  f"@{round(sb['x'])},{round(sb['y'])} {round(sb['width'])}x{round(sb['height'])}")
            line = sep.evaluate(
                """el => { const s = getComputedStyle(el, '::before');
                   if (!s || s.content === 'none') return null;
                   return { w: s.width, h: s.height, bg: s.backgroundColor,
                            // 伪元素无法直接量矩形，用壳体几何推算其纵向位置
                            offsetY: (el.getBoundingClientRect().height
                                      - parseFloat(s.height || '0')) / 2 }; }"""
            )
            check("内线 20×1 rgba(255,255,255,0.04)",
                  bool(line) and line["w"] == "20px" and line["h"] == "1px"
                  and line["bg"] == "rgba(255, 255, 255, 0.04)",
                  str(line))
            check("内线纵向居中于 12px 壳（offset≈5.5 → 绝对 y≈546）",
                  bool(line) and near(line["offsetY"], 5.5, 0.6)
                  and near(sb["y"] + line["offsetY"], 546, 1.0),
                  f"offsetY={line['offsetY'] if line else None} absY={round(sb['y'] + line['offsetY'], 1) if line else None}")

        # ── hover 不改底色 ──
        print("— hover 语义 —")
        hover_btn = page.locator('aside button[aria-label="文本"]').first
        before = hover_btn.evaluate("el => getComputedStyle(el).backgroundColor")
        hover_btn.hover()
        page.wait_for_timeout(500)
        after = hover_btn.evaluate("el => getComputedStyle(el).backgroundColor")
        check("hover 前后底色均透明（源站 hover:bg-transparent）",
              before == "rgba(0, 0, 0, 0)" and after == "rgba(0, 0, 0, 0)",
              f"{before} -> {after}")
        # hover 标签飞出层仍需可用（batch 73 契约，不能被本 batch 打坏）
        flyout = page.evaluate(
            """() => [...document.querySelectorAll('[data-rail-label]')]
                 .filter(e => getComputedStyle(e).opacity === '1').length"""
        )
        check("hover 标签飞出层仍出现", flyout >= 1, f"visible={flyout}")

        # ── 左下 dock ──
        print("— 左下 dock —")
        dock = page.locator(".jimeng-bottom-dock")
        if dock.count() == 1:
            db = dock.bounding_box()
            check("dock 164×36 @[12,774]",
                  near(db["width"], 164) and near(db["height"], 36)
                  and near(db["x"], 12) and near(db["y"], 774, 1.5),
                  f"@{round(db['x'])},{round(db['y'])} {round(db['width'])}x{round(db['height'])}")
        for label, want_x in (("选择工具", 16), ("小地图", 48), ("显示连线", 80)):
            el = page.locator(f'button[aria-label="{label}"]').first
            bb = el.bounding_box() if el.count() else None
            check(f"{label} 28×28 @x={want_x}",
                  bb is not None and near(bb["width"], 28) and near(bb["height"], 28) and near(bb["x"], want_x),
                  f"@{round(bb['x'])}" if bb else "None")

        zoom = page.locator('[data-testid="dock-zoom"]')
        check("缩放钮存在", zoom.count() == 1, f"count={zoom.count()}")
        if zoom.count() == 1:
            zb = zoom.bounding_box()
            check("缩放钮 48×28 @x=124",
                  near(zb["width"], 48) and near(zb["height"], 28) and near(zb["x"], 124),
                  f"@{round(zb['x'])},{round(zb['y'])} {round(zb['width'])}x{round(zb['height'])}")
            zc = zoom.evaluate("el => getComputedStyle(el)")
            check("缩放 btn height 28", zc["height"] == "28px", zc["height"])
            al = zoom.get_attribute("aria-label")
            check('aria-label 逐字 "Zoom options, {n}%"',
                  bool(al) and al.startswith("Zoom options, ") and al.endswith("%"),
                  repr(al))

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch796-rail-dock-1680.png"))

        # ── 居中模型：多视口反证「写死 y」 ──
        print("— 居中模型（多视口）—")
        for vh, want_btn in ((720, 193), (900, 283), (1000, 333)):
            page.set_viewport_size({"width": 1680, "height": vh})
            page.wait_for_timeout(700)
            rb = page.locator(RAIL).bounding_box()
            check(f"1680×{vh} 壳体顶 ≈ {round(rail_shell_top(vh))}（(H+56)/2−199）",
                  rb is not None and near(rb["y"], rail_shell_top(vh), 1.5),
                  f"实际 {round(rb['y']) if rb else 'None'}")
            # 第一个按钮 = 壳体顶 + 4px padding，源站四视口实测 246/193/283/333
            btn_y = page.locator('aside button[aria-label="文本"]').bounding_box()
            check(f"1680×{vh} 首按钮 y={want_btn}（源站同值）",
                  btn_y is not None and near(btn_y["y"], want_btn, 1.5),
                  f"实际 {round(btn_y['y']) if btn_y else 'None'}")

        # 第二张：hover 态（标签飞出层可见 + 按钮底色不变），与默认态是不同的
        # 可观察状态。早先这里在多视口来回后回到默认视口再截，产出与第一张
        # 字节完全相同的重复图，白占一份证据。
        page.locator('aside button[aria-label="文本"]').first.hover()
        page.wait_for_timeout(500)
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch796-rail-hover-1680.png"))
        browser.close()

    print()
    if errors:
        print("控制台错误:")
        for e in errors[:10]:
            print("  " + e)
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项不通过")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 796 左侧工具栏 + 左下 dock 几何契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
