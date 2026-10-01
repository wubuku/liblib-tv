"""Jimeng clone batch 798 verifier — 顶栏「分享」标签不得折行 + 逐层几何对齐。

Contract (SOURCE_FACT 2026-10-01 登录态实测 @1680×826，源站逐层量得)：

  「分享」按钮 **60×28 @[1388,16]**，padding `0 10px 0 8px`、gap 4px、
  align-items/justify-content center、`white-space: **nowrap**`、按钮继承 16px/24。
    ├ svg 图标  16×16 @[1395,22]
    └ 标签 span **24×20 @[1415,20]**  font-size **12px** / line-height **20px** /
                 font-weight 500 / white-space nowrap  ← 文本是「分享」两字

  缺陷成因：按钮内容盒只有 42px（60 − 8 − 10），而内容需要
  8 + 16 + 4 + 24 = 52px。源站同样超（内容 44px > 42px 内容盒），
  **靠 `white-space: nowrap` 保持单行**；复刻此前漏了 nowrap，
  CJK 可在任意两字之间断行，于是「分享」被叠成「分 / 享」两行
  （见 jimeng-clone-batch797-collapsed-1680.png 顶栏）。
  ⇒ 这不是「宽度算错」，是**缺 nowrap**；修 nowrap 而非改宽度。

  另：图标与标签需 `shrink-0`，否则 flex 会把 16px 图标压到 14px。

  命中  标签 span 高度恰为 20px（单行）且宽度 24px；
        按钮 60×28；svg 16×16；标签 12px/20px/w500；图标→标签间距 4px。
  回归  顶栏其余含中文的控件同样不得折行（积分入口等）。

  判据写法：断行与否用**相对**断言，不断言绝对 x —— 绝对 x 会把右簇
  约 3–4px 的间隙偏移（台账待决问题 #4）变成本断言的 brittle 依赖。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

SHARE = '[data-testid="canvas-share-trigger"]'
CREDITS = '[data-testid="canvas-commerce-entry"]'


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

        # ── 分享按钮 ──
        print("— 分享按钮 —")
        share = page.locator(SHARE)
        check("分享按钮存在", share.count() == 1, f"count={share.count()}")
        if share.count() == 1:
            sb = share.bounding_box()
            # 只断言**尺寸**，不断言绝对 x：整簇右缘目前比源站右移约 3px
            # （源站 分享@1388 / 复刻 @1391），那是右簇各药丸之间的间隙问题，
            # 由台账待决问题 #4 跟踪；本批不碰簇布局。
            check("按钮 60×28",
                  near(sb["width"], 60) and near(sb["height"], 28),
                  f"{round(sb['width'])}x{round(sb['height'])}")
            ss = share.evaluate("el => getComputedStyle(el)")
            check("按钮 white-space nowrap", ss["whiteSpace"] == "nowrap", ss["whiteSpace"])
            check("按钮 padding 0 10px 0 8px",
                  ss["paddingRight"] == "10px" and ss["paddingLeft"] == "8px",
                  f"{ss['paddingLeft']}/{ss['paddingRight']}")
            check("按钮 gap 4px", ss["gap"] == "4px", ss["gap"])

            label = share.evaluate(
                """el => {
                  const s = [...el.querySelectorAll('span')]
                    .find((n) => (n.textContent || '').trim() === '分享');
                  if (!s) return null;
                  const b = s.getBoundingClientRect();
                  const c = getComputedStyle(s);
                  return { x: Math.round(b.x), y: Math.round(b.y),
                           w: Math.round(b.width), h: Math.round(b.height),
                           fontSize: c.fontSize, lineHeight: c.lineHeight,
                           fontWeight: c.fontWeight, whiteSpace: c.whiteSpace,
                           lines: Math.round(b.height / parseFloat(c.lineHeight)) };
                }"""
            )
            check("标签 span 存在", label is not None, "未找到「分享」span")
            if label:
                check("标签 24×20 @y=20",
                      near(label["w"], 24) and near(label["h"], 20) and near(label["y"], 20),
                      f"@x{label['x']},y{label['y']} {label['w']}x{label['h']}")
                check("标签字号 12px", label["fontSize"] == "12px", label["fontSize"])
                check("标签行高 20px", label["lineHeight"] == "20px", label["lineHeight"])
                check("标签字重 500", label["fontWeight"] == "500", label["fontWeight"])
                # 核心断言：单行。若折成两行，高度会变成 40。
                check("标签恰为 1 行（高 20 = 单行高）", label["lines"] == 1, f"lines={label['lines']}")

            icon = share.evaluate(
                """el => { const s = el.querySelector('svg');
                   if (!s) return null; const b = s.getBoundingClientRect();
                   return { x: Math.round(b.x), y: Math.round(b.y),
                            w: Math.round(b.width), h: Math.round(b.height) }; }"""
            )
            check("图标 16×16 @y=22",
                  bool(icon) and near(icon["w"], 16) and near(icon["h"], 16)
                  and near(icon["y"], 22),
                  str(icon))
            # 相对间距（对簇横向平移免疫）：源站 图标右缘 1411 → 标签左缘 1415 = gap 4
            if icon and label:
                check("图标→标签间距 4px",
                      near(icon["x"] + icon["w"] + 4, label["x"], 1.0),
                      f"图标右缘 {icon['x'] + icon['w']} → 标签 {label['x']}")

        # ── 回归：顶栏其他中文控件不得折行 ──
        print("— 顶栏其余控件折行回归 —")
        wrapped = page.evaluate(
            """(sels) => {
              const out = [];
              for (const sel of sels) {
                const el = document.querySelector(sel);
                if (!el) continue;
                const lh = parseFloat(getComputedStyle(el).lineHeight) || 0;
                const h = el.getBoundingClientRect().height;
                if (lh > 0 && h > lh * 1.6) {
                  out.push({ sel, h: Math.round(h), lh });
                }
              }
              return out;
            }""",
            [SHARE, CREDITS],
        )
        check("顶栏文本控件无多行折行", not wrapped, str(wrapped))

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch798-share-nowrap-1680.png"))
        check("无 console/page 错误", not errors, "; ".join(errors[:4]))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项不通过")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 798 分享标签 nowrap + 逐层几何契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
