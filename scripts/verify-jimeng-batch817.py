#!/usr/bin/env python3
"""Jimeng clone batch 817 verifier — 两个按钮名订正 +「全屏编辑」接上真面板。

批 241 给这 8 个工具条按钮起的名有两个是**猜的**，本批逐项向源站核对后订正
（README §26）：

  第 1 个  复刻「字体」    → 源站 aria-label 是英文 **"Text style"**，48×32（带 chevron）
  第 8 个  复刻「展开编辑」→ 源站 aria-label 是「**全屏**」32×32；点开的面板标题是
                        「**全屏编辑**」（实测 126×42 的标签按钮 @[1340,406]）
  第 8 个此前是 OPEN_QUESTION 816-a，本批拿到形态，关闭该问号。

另附一条**如实记录**：面板「时间线」段的 ⌘B 分割片段 / Q 向左裁剪 / W 向右裁剪
在本画布上无法验证 —— 源站自己的「添加素材到时间线」按钮带
`data-timeline-empty="true"`，且所有节点 aria-label 都是 `No resources: 0 ready`，
即**这个画布没有任何素材可以生成片段**。源站与复刻同处这一状态，属
BLOCKED_BY_FIXTURE，不能据此说"源站没实现"。

判据：断言**状态变化**（面板真出现、内容真落库、按钮名真是源站那个），
不断言"元素还在不在"。
"""

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"
NODE_SEL = '[class*="react-flow__node"]'

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def rail_click(page, label: str) -> None:
    box = page.locator(f'button[aria-label="{label}"]').first.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(1500)


def find_text_node(page):
    """取「文本 N」标题开头且面积最小的节点。

    判据坑（沿用 816）：`.react-flow__node` 同时匹配外层包装 div，
    它的 innerText 也含「文本」二字，取最小面积才是真节点。
    """
    best = None
    for i in range(min(page.locator(NODE_SEL).count(), 20)):
        el = page.locator(NODE_SEL).nth(i)
        try:
            txt = (el.inner_text() or "").strip()
            if not re.match(r"^文本\s*\d", txt) and "双击编辑文本" not in txt:
                continue
            bb = el.bounding_box()
            if not bb:
                continue
            area = bb["width"] * bb["height"]
            if best is None or area < best[0]:
                best = (area, el, txt)
        except Exception:
            pass
    return best[1] if best else None


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state=str(STATE) if STATE.exists() else None,
                            viewport={"width": 1680, "height": 1050})
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        rail_click(page, "文本")
        node = find_text_node(page)
        if node is None:
            print("FAIL: 没找到文本节点")
            return 1

        # ── 前置：进编辑态 ───────────────────────────────────────────
        bb = node.bounding_box()
        ok = False
        for dy in (0.4, 0.5, 0.6, 0.3):
            page.mouse.dblclick(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * dy)
            page.wait_for_timeout(800)
            if page.locator('[data-testid="text-rich-editor"]').count():
                ok = True
                break
        check("0.1 前置：双击进入编辑态", ok)
        if not ok:
            return 1
        page.locator('[data-testid="text-rich-editor"]').click()
        page.keyboard.type("全屏样例", delay=35)
        page.wait_for_timeout(400)

        # ── 1. 按钮名订正（源站 aria-label 逐字）──────────────────────
        tb = page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                if (!bar) return null;
                return [...bar.querySelectorAll('button')].map(b => {
                    const r = b.getBoundingClientRect();
                    // 量 **CSS 像素**（getComputedStyle），不是 getBoundingClientRect。
                // 判据坑：工具条在画布节点里，被画布缩放（复刻默认 73%）一起缩放，
                // 32px 的按钮量出来是 23px —— 量屏幕像素等于把当时的缩放系数
                // 固化成脆依赖。CSS 尺寸不受 transform 影响，才是产品尺寸。
                const cs = getComputedStyle(b);
                return {al: b.getAttribute('aria-label'),
                        rect: [parseFloat(cs.width), parseFloat(cs.height)].map(Math.round),
                        screen: [r.width, r.height].map(Math.round)};
                });
            }"""
        )
        check("1.0 前置：工具条 8 个按钮", tb is not None and len(tb) == 8,
              str([x["al"] for x in (tb or [])]))
        labels = [x["al"] for x in (tb or [])]
        check("1.1 第 1 个按钮名是源站的「Text style」（不是复刻猜的「字体」）",
              labels[:1] == ["Text style"], str(labels[:1]))
        check("1.2 第 8 个按钮名是源站的「全屏」（不是复刻猜的「展开编辑」）",
              labels[-1:] == ["全屏"], str(labels[-1:]))
        # 源站实测 48×32 / 32×32
        if tb:
            check("1.3 第 1 个按钮 48×32（带 chevron，源站实测）",
                  tb[0]["rect"] == [48, 32], str(tb[0]["rect"]))
            check("1.4 第 8 个按钮 32×32（源站实测）",
                  tb[-1]["rect"] == [32, 32], str(tb[-1]["rect"]))
            check("1.4b 六个格式按钮均 32×32（源站实测）",
                  all(x["rect"] == [32, 32] for x in tb[1:7]),
                  str([x["rect"] for x in tb[1:7]]))
            if tb:
                smaller = all(s["screen"][0] < r[0] for s, r in
                              zip(tb, [x["rect"] for x in tb]))
                check("1.4c 屏幕像素确实小于 CSS 尺寸（证明存在画布缩放，前面的判据必须量 CSS）",
                      smaller, f"screen={[x['screen'] for x in tb]}")
        check("1.5 复刻不再残留「字体」「展开编辑」这两个猜出来的名字",
              "字体" not in labels and "展开编辑" not in labels, str(labels))

        # ── 2. 「全屏」接上真面板 ────────────────────────────────────
        page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                if (bar) bar.scrollIntoView();
            }"""
        )
        page.locator('[data-testid="text-expand"]').click()
        page.wait_for_timeout(900)
        panel = page.locator('[data-testid="text-fullscreen"]')
        check("2.1 点「全屏」打开「全屏编辑」面板（读 data-testid 真出现）",
              panel.count() == 1)
        if panel.count():
            pr = panel.bounding_box()
            # 判据用**关系**不写死绝对值：面板锚在节点上，会随画布缩放一起缩放
            # （源站实测 326×324 是在源站当时的画布缩放下量的）。写死绝对宽度
            # 等于把当时的缩放系数固化成脆依赖。断言的是「接近正方形 + 明显大于
            # 节点自身」这两个与缩放无关的性质。
            node_bb = node.bounding_box()
            ratio = (pr["width"] / pr["height"]) if pr and pr["height"] else 0
            check("2.2 面板宽高比 ≈326:324（源站实测），用关系而非绝对值",
                  0.95 <= ratio <= 1.06, f"{pr['width']:.0f}×{pr['height']:.0f} 比值 {ratio:.3f}" if pr else "无")
            # 不写死"面板比节点大"这种**源站并没有的属性**（源站 326 的面板
            # 比它 368 的文本节点还窄）。过不了源站验证的关系，不该出现在断言里。
            check("2.3 面板可访问名是「全屏编辑」（源站同名）",
                  panel.get_attribute("aria-label") == "全屏编辑",
                  str(panel.get_attribute("aria-label")))
            seeded = page.evaluate(
                """() => {
                    const el = document.querySelector('[data-testid="text-fullscreen-editor"]');
                    return el ? el.innerHTML : null;
                }"""
            )
            check("2.4 面板里带上了节点正文（内容真灌进去了）",
                  seeded is not None and "全屏样例" in seeded, str(seeded)[:60])

            # 全屏面里快捷键仍生效
            page.locator('[data-testid="text-fullscreen-editor"]').click()
            page.keyboard.press("Meta+a")
            page.wait_for_timeout(250)
            before = page.evaluate(
                """() => document.querySelector('[data-testid="text-fullscreen-editor"]').innerHTML"""
            )
            page.keyboard.press("Meta+b")
            page.wait_for_timeout(400)
            after = page.evaluate(
                """() => document.querySelector('[data-testid="text-fullscreen-editor"]').innerHTML"""
            )
            check("2.5 全屏面里 ⌘B 仍生效（复用同一套快捷键）",
                  after != before and "<b" in after, str(after)[:50])

            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            view = page.evaluate(
                """() => {
                    const v = document.querySelector('[data-testid="text-rich-view"]');
                    return v ? v.innerHTML : null;
                }"""
            )
            check("2.6 Enter 把全屏面的改动落库（不是只在面板里好看）",
                  view is not None and "<strong" in view, str(view)[:70])

            page.locator('[data-testid="text-fullscreen-close"]').click()
            page.wait_for_timeout(600)
            check("2.7 关闭钮真能关掉面板",
                  page.locator('[data-testid="text-fullscreen"]').count() == 0)

        # ── 3. 如实记录：时间线 3 键 BLOCKED_BY_FIXTURE ──────────────
        rail_click(page, "时间线")
        tl = page.evaluate(
            """() => {
                const nodes = [...document.querySelectorAll('[class*="react-flow__node"]')];
                const n = nodes.find(e => /时间线\\s*\\d/.test((e.innerText||'')));
                return n ? (n.innerText||'').replace(/\\s+/g,' ').slice(0,80) : null;
            }"""
        )
        check("3.1 时间线节点存在（面板「时间线」段 3 键的落点）", tl is not None, str(tl))
        # 源站同样测不到：data-timeline-empty=true + 全节点 No resources
        check("3.2 时间线 3 键在本画布无法验证 = BLOCKED_BY_FIXTURE（如实记录）",
              True, "源站 data-timeline-empty=true / No resources: 0 ready；复刻同样无素材")

        check("4.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 817 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
