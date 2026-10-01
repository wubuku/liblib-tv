"""Jimeng clone batch 797 verifier — Agent 抽屉默认收起 + 触发钮/面板材质契约。

Contract (SOURCE_FACT 2026-10-01，登录态实测 @1680×826；取证脚本
scripts/jimeng_chrome_probe.py + 「点『与 AI 对话』前后对照」)：

本批关闭台账遗留的待决问题 #2「AI 抽屉默认展开会盖住顶栏右簇」。源站事实是
**默认收起**，此前复刻的「默认展开」是批 398 的约定，取样中从未在源站出现过。
默认展开还导致顶栏「分享」被挤成竖排文字（见 jimeng-clone-batch797 开态截图）。

收起态（首屏）：
  面板           不存在（`aside[aria-label="Agent"]` count = 0）
  触发钮结构     **三层**，逐层实测：
    定位层  `absolute bottom-3 right-3 flex flex-col items-end`（12px 内缩）
    药丸层  @[1548,778] 120×36  bg rgba(39,39,39,0.72)  radius **20px**
            backdrop-filter **blur(40px)**
    按钮层  @[1549,779] 118×34  自身**透明**  radius 20px  font 13px
  展开类控件     新建会话/收起/使用技能/引用参考/发送消息 **一个都不出现**
  四视口内缩     按钮距右缘恒 13px = 定位 12px + 按钮内缩 1px（勿据此外推 13px）

展开态（点触发钮后）：
  面板  @[1268,12] 400×802  radius 20px  z-index 40
        background color(srgb .12549 ×3 / .8) = **rgba(32,32,32,0.8)**
        backdrop-filter **blur(60px)**
        border 1px solid rgba(255,255,255,**0.1**)
        box-shadow rgba(0,0,0,0.16) 0 0 80px 0
  控件  新建会话 / 收起 / 使用技能 / 引用参考 / 发送消息 出现
  收起  点「收起」后面板消失、触发钮复现
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
TRIGGER_PILL = '[data-testid="ai-trigger-pill"]'
TRIGGER_BTN = 'button[aria-label="与 AI 对话"]'
OPEN_CUES = ["新建会话", "收起", "使用技能", "引用参考", "发送消息"]


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

    def visible_cues(page) -> dict:
        return page.evaluate(
            """(cues) => {
              const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              const vis = (el) => { const b = el.getBoundingClientRect();
                if (b.width < 1 || b.height < 1) return false;
                for (let p = el; p; p = p.parentElement) {
                  const s = getComputedStyle(p);
                  if (s.visibility === 'hidden' || s.display === 'none') return false;
                } return true; };
              const all = [...document.querySelectorAll('button,[role="button"],[aria-label]')].filter(vis);
              const out = {};
              for (const c of cues) {
                // 源站这五类控件都带 aria-label；复刻里「使用技能」是纯可见文本
                // （无 aria-label），只按 aria-label 匹配会误判为缺失。
                out[c] = all.filter((b) => norm(b.getAttribute('aria-label')) === c
                                        || norm(b.innerText) === c).length;
              }
              return out;
            }""",
            OPEN_CUES,
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # ── 收起态 ──
        print("— 收起态（默认）—")
        drawer = page.locator(DRAWER)
        check("首屏无 Agent 面板", drawer.count() == 0, f"count={drawer.count()}")

        cues = visible_cues(page)
        leaked = [c for c, n in cues.items() if n > 0]
        check("收起态不泄漏任何展开类控件", not leaked, f"出现: {leaked}")

        pill = page.locator(TRIGGER_PILL)
        check("触发药丸存在", pill.count() == 1, f"count={pill.count()}")
        if pill.count() == 1:
            pb = pill.bounding_box()
            check("药丸 120×36 @[1548,778]",
                  near(pb["width"], 120) and near(pb["height"], 36)
                  and near(pb["x"], 1548) and near(pb["y"], 778, 1.5),
                  f"@{round(pb['x'])},{round(pb['y'])} {round(pb['width'])}x{round(pb['height'])}")
            ps = pill.evaluate("el => getComputedStyle(el)")
            check("药丸 bg rgba(39,39,39,0.72)", ps["backgroundColor"] == "rgba(39, 39, 39, 0.72)", ps["backgroundColor"])
            check("药丸 radius 20px", ps["borderTopLeftRadius"] == "20px", ps["borderTopLeftRadius"])
            check("药丸 backdrop blur(40px)", "blur(40px)" in (ps["backdropFilter"] or ""), ps["backdropFilter"])

        btn = page.locator(TRIGGER_BTN)
        check("触发按钮存在", btn.count() == 1, f"count={btn.count()}")
        if btn.count() == 1:
            bb = btn.bounding_box()
            check("按钮 118×34 @[1549,779]",
                  near(bb["width"], 118) and near(bb["height"], 34)
                  and near(bb["x"], 1549) and near(bb["y"], 779, 1.5),
                  f"@{round(bb['x'])},{round(bb['y'])} {round(bb['width'])}x{round(bb['height'])}")
            bs = btn.evaluate("el => getComputedStyle(el)")
            check("按钮自身透明", bs["backgroundColor"] == "rgba(0, 0, 0, 0)", bs["backgroundColor"])
            check("按钮 radius 20px", bs["borderTopLeftRadius"] == "20px", bs["borderTopLeftRadius"])
            check("按钮 13px 文字", bs["fontSize"] == "13px", bs["fontSize"])

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch797-collapsed-1680.png"))

        # 收起态下顶栏不应被挤压（这是默认展开留下的可见缺陷）
        share = page.locator('[data-testid="canvas-share-trigger"]')
        if share.count() == 1:
            sb = share.bounding_box()
            check("顶栏「分享」不再被挤成竖排（高 28）", near(sb["height"], 28), f"h={round(sb['height'])}")

        # ── 展开态 ──
        print("— 展开态（点触发钮）—")
        btn.click()
        page.wait_for_timeout(900)
        check("面板已展开", drawer.count() == 1, f"count={drawer.count()}")
        if drawer.count() == 1:
            d = drawer.bounding_box()
            check("面板 400×802 @[1268,12]",
                  near(d["width"], 400) and near(d["height"], 802)
                  and near(d["x"], 1268) and near(d["y"], 12),
                  f"@{round(d['x'])},{round(d['y'])} {round(d['width'])}x{round(d['height'])}")
            check("面板右缘 1668", near(d["x"] + d["width"], 1668), str(round(d["x"] + d["width"], 1)))
            ds = drawer.evaluate("el => getComputedStyle(el)")
            check("面板 bg rgba(32,32,32,0.8)", ds["backgroundColor"] == "rgba(32, 32, 32, 0.8)", ds["backgroundColor"])
            check("面板 backdrop blur(60px)", "blur(60px)" in (ds["backdropFilter"] or ""), ds["backdropFilter"])
            check("面板 radius 20px", ds["borderTopLeftRadius"] == "20px", ds["borderTopLeftRadius"])
            check("面板 z-index 40", ds["zIndex"] == "40", ds["zIndex"])
            check("面板边框白 10%", "0.1" in ds["borderTopColor"] or "0.1" in ds["borderTopWidth"],
                  f"{ds['borderTopWidth']} {ds['borderTopColor']}")
            check("面板 80px 投影", "80px" in ds["boxShadow"], ds["boxShadow"][:80])

            cues2 = visible_cues(page)
            missing = [c for c in OPEN_CUES if cues2.get(c, 0) == 0]
            check("五类展开控件齐备", not missing, f"缺: {missing}")

            page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch797-expanded-1680.png"))

            # ── 收起 ──
            print("— 收起 —")
            page.locator('button[aria-label="收起"]').first.click()
            page.wait_for_timeout(700)
            check("面板已收起", drawer.count() == 0, f"count={drawer.count()}")
            check("触发钮复现", page.locator(TRIGGER_PILL).count() == 1,
                  f"count={page.locator(TRIGGER_PILL).count()}")

        check("无 console/page 错误", not errors, "; ".join(errors[:4]))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项不通过")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 797 Agent 抽屉默认收起 + 触发钮/面板材质契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
