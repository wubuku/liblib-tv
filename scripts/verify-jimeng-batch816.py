#!/usr/bin/env python3
"""Jimeng clone batch 816 verifier — 文本节点的富文本工具条与 10 个快捷键。

出发点：批 815 把源站快捷键面板补齐到 28 行，其中「文本编辑」整段 10 行是**新加的**
—— 加进来就得兑现。批 241 早已把这 8 个工具条按钮标为「视觉 mock，未接真实格式化」，
于是面板承诺的 10 个键在复刻里一个都不通。

源站依据（README §25，全部带 contenteditable 前置态门禁，activeElement.ce=true）：
    ⌘B 加粗    <p>文字</p> → <p><strong>文字</strong></p>      响应
    ⌘I 倾斜    → <strong><em>文字</em></strong>              响应
    ⌘U 下划线  → …<u>文字</u>…                                响应
    ⌘⇧X 删除线 → …<s><u>文字</u></s>…                         响应
    ⌘⌥1/2/3    p → h1 → h2 → h3                              响应
    ⌘⌥0        h1 → p                                        响应
    ⌘⇧8/7      → ul+li / ol+li                              响应

判据纪律：**断言 innerHTML 的状态变化**，不断言「元素还在不在」。每次按键前都
重新全选（选区没了 execCommand 就作用在光标上，会误判为「没反应」）。
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

EDITOR_JS = """() => {
  const ed = document.querySelector('[data-testid="text-rich-editor"]');
  const vw = document.querySelector('[data-testid="text-rich-view"]');
  const ae = document.activeElement;
  return {
    editing: !!ed,
    inner: ed ? ed.innerHTML : null,
    view: vw ? vw.innerHTML : null,
    ce: !!(ae && ae.isContentEditable),
    sel: window.getSelection() ? String(window.getSelection()) : '',
  };
}"""


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
    """取「文本」开头且**面积最小**的节点。

    判据坑：`.react-flow__node` 同时匹配到外层包装 div（1226×766），它的 innerText
    也含「文本」二字。初版探针就匹配到包装层，双击落空，编辑态永远进不去。
    """
    best = None
    for i in range(min(page.locator(NODE_SEL).count(), 20)):
        el = page.locator(NODE_SEL).nth(i)
        try:
            txt = (el.inner_text() or "").strip()
            if not re.match(r"^文本", txt):
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


def enter_edit(page, node) -> bool:
    bb = node.bounding_box()
    for dy in (0.4, 0.5, 0.6, 0.3):
        page.mouse.dblclick(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * dy)
        page.wait_for_timeout(800)
        f = page.evaluate(EDITOR_JS)
        if f["editing"] and f["ce"]:
            return True
    return False


def select_all(page) -> None:
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(250)


def reset_editor(page) -> None:
    """把编辑面内容重置成干净的 `<p>测试文字样例</p>` 并全选。

    判据坑 1：格式化按钮是 **toggle**。前面 1.x 已经用键盘把文字加粗/倾斜/下划线/
    删除线全套上了，此时再点「加粗」是**取消加粗** —— innerHTML 变了，但断言
    "结果里含 <b>" 就成了假失败。测按钮前必须先清干净。

    判据坑 2：不能用 `el.innerHTML = ...` 直接改 DOM。实测那样改完再点一下
    工具条按钮，内容会被清空 —— React 的 dangerouslySetInnerHTML 与外部 DOM
    改写打架。改走键盘：⌘A 全选后直接打字覆盖，是用户真实路径。
    """
    page.locator('[data-testid="text-rich-editor"]').click()
    page.wait_for_timeout(200)
    # 收敛式重置：用**产品自己的 toggle 键**把还开着的行内格式关掉。
    # 不能盲按一串：这些键是 toggle，对没开的格式再按一次就变成打开。
    # 也不能「删掉重打」：实测 Chromium 里删掉再打字会**继承**原格式，
    # 结果还是 <b><i><u><strike>，行内 toggle 继续互相抵消。
    cur = page.evaluate(EDITOR_JS)["inner"] or ""
    for keys, tag in [("Meta+b", "<b"), ("Meta+i", "<i"), ("Meta+u", "<u"),
                      ("Meta+Shift+x", "<strike")]:
        if tag in cur:
            select_all(page)
            page.keyboard.press(keys)
            page.wait_for_timeout(250)
    # 块级归一成 <p>（列表会被摊平）
    select_all(page)
    page.keyboard.press("Meta+Alt+0")
    page.wait_for_timeout(300)
    select_all(page)


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

        # ── 前置态门禁：进编辑 + 打字 + 选区非空，否则本文件全部作废 ──
        ok = enter_edit(page, node)
        check("0.1 前置：双击进入编辑态且编辑面是 contenteditable", ok)
        if not ok:
            return 1
        page.keyboard.type("测试文字样例", delay=40)
        page.wait_for_timeout(500)
        select_all(page)
        f = page.evaluate(EDITOR_JS)
        check("0.2 前置：打字后选区非空（空选区下格式化本就不该有反应）",
              bool(f["sel"].strip()), f"sel={f['sel']!r}")

        # ── 1. 十个快捷键：断言 innerHTML 结构变化 ──────────────────
        def press_keys(keys: str, want: str, label: str):
            select_all(page)
            before = page.evaluate(EDITOR_JS)["inner"]
            page.keyboard.press(keys)
            page.wait_for_timeout(400)
            after = page.evaluate(EDITOR_JS)["inner"]
            check(label, after != before and want in (after or ""),
                  f"{str(before)[:46]} -> {str(after)[:46]}")

        # 行内四键：先清成纯 <p>，再逐个加，避免 toggle 互相抵消
        press_keys("Meta+Alt+0", "<p>", "1.1 ⌘⌥0 普通文本")
        for keys, want, label in [
            ("Meta+b", "<b", "1.2 ⌘B 加粗"),
            ("Meta+i", "<i", "1.3 ⌘I 倾斜"),
            ("Meta+u", "<u", "1.4 ⌘U 下划线"),
            ("Meta+Shift+x", "<strike", "1.5 ⌘⇧X 删除线"),
        ]:
            press_keys(keys, want, label)
        press_keys("Meta+Alt+1", "<h1>", "1.6 ⌘⌥1 一级标题")
        press_keys("Meta+Alt+2", "<h2>", "1.7 ⌘⌥2 二级标题")
        press_keys("Meta+Alt+3", "<h3>", "1.8 ⌘⌥3 三级标题")
        press_keys("Meta+Alt+0", "<p>", "1.9 ⌘⌥0 从 h3 退回普通文本")
        press_keys("Meta+Shift+8", "<ul", "1.10 ⌘⇧8 无序列表")
        press_keys("Meta+Shift+7", "<ol", "1.11 ⌘⇧7 有序列表")

        # ── 2. 工具条 7 个按钮：与快捷键同一套行为 ──────────────────
        tb = page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                return bar ? [...bar.querySelectorAll('button')].map(b => b.getAttribute('aria-label')) : null;
            }"""
        )
        check("2.0 前置：编辑态工具条 8 个按钮齐全",
              tb is not None and len(tb) == 8, str(tb))

        for label, want in [("加粗", "<b"), ("斜体", "<i"), ("下划线", "<u"), ("删除线", "<strike")]:
            reset_editor(page)
            before = page.evaluate(EDITOR_JS)["inner"]
            page.locator(f'[data-testid="text-fmt-{label}"]').click()
            page.wait_for_timeout(400)
            st = page.evaluate(EDITOR_JS)
            check(f"2.1 工具条「{label}」真改 innerHTML",
                  st["inner"] != before and want in (st["inner"] or "") and st["editing"],
                  f"{str(before)[:30]} -> {str(st['inner'])[:40]}")

        for label, want in [("无序列表", "<ul"), ("有序列表", "<ol")]:
            reset_editor(page)
            before = page.evaluate(EDITOR_JS)["inner"]
            page.locator(f'[data-testid="text-fmt-{label}"]').click()
            page.wait_for_timeout(400)
            st = page.evaluate(EDITOR_JS)
            check(f"2.2 工具条「{label}」真改 innerHTML",
                  st["inner"] != before and want in (st["inner"] or "") and st["editing"],
                  str(st["inner"])[:50])

        # 连续点按钮不得把编辑面卸载（onBlur 误触发 commit 的回归守卫）
        check("2.3 回归：连点工具条按钮后编辑面仍在（onBlur 不得误提交）",
              page.evaluate(EDITOR_JS)["editing"])

        # ── 3. 字体菜单 ─────────────────────────────────────────────
        # 先重置再开菜单：反过来的话 reset 里的点击会走到已经打开的菜单上。
        reset_editor(page)
        page.locator('[data-testid="text-format-toolbar"] button[aria-label="Text style"]').click()
        page.wait_for_timeout(400)
        fm = page.locator('[data-testid="text-font-menu"]')
        items = fm.locator('[role="menuitem"]').all_inner_texts() if fm.count() else []
        check("3.1 字体菜单四项齐全（对应面板 ⌘⌥0~3）",
              items == ["普通文本", "一级标题", "二级标题", "三级标题"], str(items))
        if items:
            before = page.evaluate(EDITOR_JS)["inner"]
            page.locator('[data-testid="text-font-menu"] [aria-label="字体 一级标题"]').click()
            page.wait_for_timeout(400)
            st = page.evaluate(EDITOR_JS)
            check("3.2 字体菜单「一级标题」真改 innerHTML",
                  st["inner"] != before and "<h1" in (st["inner"] or "") and st["editing"],
                  f"{str(before)[:30]} -> {str(st['inner'])[:40]}")

        # ── 4. 第 8 个按钮 ──────────────────────────────────────────
        # 批 816 写这条时它是 OPEN_QUESTION 816-a（源站形态未取证，断言"点了没变化"）。
        # 批 817 拿到源站实名并接成真面板：aria-label 是「**全屏**」，
        # 点开的面板叫「**全屏编辑**」。故本条改为守源站实名，
        # 面板行为断言挪到 verify-jimeng-batch817.py。
        eighth = page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                if (!bar) return null;
                const b = [...bar.querySelectorAll('button')].pop();
                return b ? b.getAttribute('aria-label') : null;
            }"""
        )
        check("4.1 第 8 个按钮名是源站的「全屏」（批 816 写的是猜的「展开编辑」）",
              eighth == "全屏", str(eighth))

        # ── 5. 落库：Enter 提交 / Escape 取消 ────────────────────────
        # 判据坑：点完「展开编辑」焦点在按钮上，Enter 会被按钮吃掉，到不了编辑面。
        # 真实用户也得先把光标放回文字里，所以这里先点回编辑面（不是绕过，是还原
        # 用户必经的一步）。提交前先造出**块级 + 行内都有**的内容，5.3 才有东西可断言。
        reset_editor(page)
        page.keyboard.press("Meta+b")
        page.wait_for_timeout(300)
        select_all(page)
        page.keyboard.press("Meta+Alt+1")
        page.wait_for_timeout(400)
        pre_commit = page.evaluate(EDITOR_JS)["inner"]
        check("5.0 前置：提交前内容是 <h1> + <b>",
              "<h1" in (pre_commit or "") and "<b" in (pre_commit or ""), str(pre_commit)[:60])
        page.keyboard.press("Enter")
        page.wait_for_timeout(900)
        st = page.evaluate(EDITOR_JS)
        check("5.1 Enter 提交并退出编辑", st["editing"] is False)
        # 落库的标签按源站形态归一（b→strong、i→em、strike→s）
        view = (st["view"] or "")
        check("5.2 落库视图渲染富文本（不是纯文本回退）", "<h1" in view, view[:70])
        check("5.3 落库标签按源站归一（strong/em/s，不是 b/i/strike）",
              "<strong" in view and "<b>" not in view and "<strike" not in view,
              view[:90])

        page.mouse.dblclick(node.bounding_box()["x"] + node.bounding_box()["width"] / 2,
                            node.bounding_box()["y"] + node.bounding_box()["height"] * 0.4)
        page.wait_for_timeout(900)
        if page.evaluate(EDITOR_JS)["editing"]:
            page.keyboard.type("临时垃圾", delay=30)
            page.wait_for_timeout(400)
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            st2 = page.evaluate(EDITOR_JS)
            check("5.4 Escape = 取消：临时输入不落库（沿用批 38 原语义）",
                  "临时垃圾" not in (st2["view"] or "") and st2["editing"] is False,
                  str(st2["view"])[:70])

        check("6.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 816 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
