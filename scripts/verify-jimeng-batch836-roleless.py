#!/usr/bin/env python3
"""Jimeng clone batch 836-verifier — 一个 role 型普查**结构上就看不见**的浮层。

## 这批的起点是一句「测不到」

§47 记下：复刻侧 `JimengNodeToolbar` 的两个下拉（截取帧 / 工具）是**裸 div，
一个 role 都没有** ⇒ 任何 `role ∈ dialog/menu/listbox/popover` 型普查都看不见它们。

想去源站问「源站的节点工具条下拉带不带 role」，两条路都堵死：

| 路径 | 结果 |
|---|---|
| 视频节点工具条 | 源站示例画布的视频节点**全是「暂无视频」**，选中弹的是**生成表单**不是工具条 ⇒「截取帧」「工具」根本没出现（`picked_label=None`） |
| 文本节点工具条 | `node-toolbar` 在（`data-testid`），「背景色」按钮实测 `aria-haspopup="menu"` 75×32，但无头环境下**点不开** —— 点了之后 `aria-expanded` 仍是 `false`，无新块出现 |

⇒ **BLOCKED_BY_FIXTURE**。没有证据，所以**不补 role**：源站有没有、是什么，
都不知道，凭空写一个 `role="menu"` 就是"复刻自有"。

## 但"测不到"不能等于"什么都不做"

能确证的有两件，都做了：

1. **补锚点**（用户不可见）—— 至少可指名、可定位。
2. **把盲区本身变成可断言的** —— 这才是关键：以前"普查看不见它们"是个
   **沉默的事实**，没人知道普查有洞；现在 §C 正面断言「role 型普查枚举到 0 个，
   而锚点存在」，**普查工具的这个洞被写在判据里**，谁都能看到。

顺带一条源站观察：源站那枚「背景色」按钮**没有 aria-label**，名字来自
`innerText`。复刻侧有 `aria-label="背景色"`。按"有对应物就照抄"的规矩，
这条记为**复刻多给的**（不冲突，aria-label 与可见文案一致），不在本批处理。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

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


# 与 `jimeng_role_layer_scan` / 批 832 普查**同一个**选择器 —— 必须是同一个，
# 否则「普查看不见它」这句话就没有意义（换了更宽的选择器当然看得见）
ROLE_LAYER_JS = """() => {
  const SEL = '[role=dialog],[role=menu],[role=listbox],[role=popover]';
  return [...document.querySelectorAll(SEL)].filter(e => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4;
  }).map(e => ({role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
                name: e.getAttribute('aria-label')}));
}"""


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        def clear_selection() -> None:
            pt = page.evaluate("""() => {
              const pane = document.querySelector('.react-flow__pane');
              if (!pane) return null;
              const r = pane.getBoundingClientRect();
              for (const [fx, fy] of [[0.02,0.95],[0.98,0.95],[0.02,0.05],[0.98,0.05]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && pane.contains(h)) return {x, y};
              }
              return null;
            }""")
            if pt:
                page.mouse.click(pt["x"], pt["y"])
                page.wait_for_timeout(450)

        def select_video() -> bool:
            """选中带媒体的视频节点（它的工具条里才有截取帧/工具）。"""
            clear_selection()
            pt = page.evaluate("""() => {
              const n = document.querySelector(
                '.react-flow__node[data-testid="rf__node-video-local-1"]');
              if (!n) return null;
              const r = n.getBoundingClientRect();
              // 不能落在控件上：中心是 32px 播放/暂停键，它 stopPropagation
              const CTRL = 'button,[role=button],a,input';
              for (const [fx, fy] of [[0.5,0.25],[0.25,0.5],[0.75,0.5],[0.5,0.75],
                                      [0.2,0.2],[0.8,0.8]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && n.contains(h) && !h.closest(CTRL)) return {x, y};
              }
              return null;
            }""")
            if pt is None:
                return False
            page.mouse.click(pt["x"], pt["y"])
            page.wait_for_timeout(900)
            return page.evaluate(
                "() => document.querySelectorAll('.react-flow__node-toolbar').length >= 1")

        def open_toolbar_dropdown(label: str, tid: str | None = None) -> bool:
            """把工具条上的某个下拉**打开**（幂等）。

            ⚠️ 必须幂等：这些触发器是 toggle。上一段 A 打开后没关，这里再点一次
            就是「关上」，于是 B 段去找元素时 count=0 —— 看起来像"元素不见了"，
            实际是我自己把它关的。
            """
            if tid and page.locator(f'[data-testid="{tid}"]').count():
                return True
            loc = page.locator(f'.react-flow__node-toolbar button:text-is("{label}")')
            if not loc.count():
                return False
            loc.first.click()
            page.wait_for_timeout(650)
            return True

        # ── A. 两个下拉：能指名可定位 ─────────────────────────────
        print("— A. 视频工具条两个下拉：补了锚点（源站测不到 ⇒ 不补 role）—")
        sel = select_video()
        check("A.0 前置：带媒体的视频节点被单独选中（工具条挂上）", sel,
              f"toolbars={page.evaluate('() => document.querySelectorAll(' + repr('.react-flow__node-toolbar') + ').length')}")

        for label, tid, want_items in [("截取帧", "video-toolbar-capture-menu", 3),
                                       ("工具", "video-toolbar-tools-menu", 3)]:
            if not sel:
                break
            ok = open_toolbar_dropdown(label, tid)
            el = page.locator(f'[data-testid="{tid}"]')
            check(f"A.{tid} 「{label}」下拉能打开且有锚点", ok and el.count() == 1,
                  f"opened={ok} count={el.count()}")
            if el.count():
                check(f"A.{tid} 内含 {want_items} 枚项（截取帧=首帧/尾帧/自定义；"
                      f"工具=补帧/深度动作捕捉/提示词反推）",
                      el.locator("button").count() == want_items,
                      f"buttons={el.locator('button').count()}")

        # ── B. 刻意不给 role：锁住"测不到"而不是"忘了加" ──────────
        print("\n— B. 刻意不给 role —— 源站 BLOCKED_BY_FIXTURE，没有证据不编 —")
        if sel:
            open_toolbar_dropdown("截取帧", "video-toolbar-capture-menu")
            cap = page.locator('[data-testid="video-toolbar-capture-menu"]')
            check("B.1 截取帧下拉**没有** role 属性",
                  cap.count() == 1 and cap.get_attribute("role") is None,
                  repr(cap.get_attribute("role")) if cap.count() else "N/A")
            # 收起截取帧、改开「工具」（两枚可以并存，B.2 要单独确认后者）
            if page.locator('[data-testid="video-toolbar-capture-menu"]').count():
                open_toolbar_dropdown("截取帧")
            open_toolbar_dropdown("工具", "video-toolbar-tools-menu")
            tl = page.locator('[data-testid="video-toolbar-tools-menu"]')
            check("B.2 工具下拉**没有** role 属性",
                  tl.count() == 1 and tl.get_attribute("role") is None,
                  repr(tl.get_attribute("role")) if tl.count() else "N/A")
        src = Path(__file__).resolve().parent.parent / "src/components/jimeng/JimengNodeToolbar.tsx"
        text = src.read_text(encoding="utf-8")
        check("B.3 「不补 role」的理由写进了源码（防后人'顺手补上'）",
              "BLOCKED_BY_FIXTURE" in text and "不补 role" in text,
              f"BLOCKED_BY_FIXTURE={'BLOCKED_BY_FIXTURE' in text} "
              f"不补 role={'不补 role' in text}")

        # ── C. 把普查的洞正面写进判据 ─────────────────────────────
        print("\n— C. 普查盲区：role 型普查枚举到 0 个，而锚点确实存在 —")
        if sel:
            # 两个都打开 —— B 段把截取帧收起来了，只开一个的话 C.1 的前置态
            # 不成立（这次就栽在这：断言写"两个都在"，实际只开了一个）。
            # 顺带说明：视频工具条这两个下拉是**各自独立**的 state，能同时开；
            # 批 835 证过"源站生成面板的下拉互斥"，但源站这两处**测不到**
            # （无带媒体的视频节点），所以**没有改**它们的互斥性，只记录。
            open_toolbar_dropdown("截取帧", "video-toolbar-capture-menu")
            open_toolbar_dropdown("工具", "video-toolbar-tools-menu")
            tids_present = page.evaluate(
                """() => ['video-toolbar-capture-menu','video-toolbar-tools-menu']
                    .filter(t => document.querySelector(`[data-testid="${t}"]`))""")
            role_rows = page.evaluate(ROLE_LAYER_JS)
            mine = [r for r in role_rows
                    if r["tid"] in ("video-toolbar-capture-menu", "video-toolbar-tools-menu")]
            check(
                "C.1 两个下拉此刻确实在 DOM 里（前置态成立）",
                set(tids_present) == {"video-toolbar-capture-menu", "video-toolbar-tools-menu"},
                f"在={tids_present}",
            )
            check(
                "C.2 **用与普查同一个选择器**枚举它们 ⇒ 0 个 —— "
                "这就是普查的洞，现在写在判据里而不是沉默着",
                not mine, f"枚举到={mine}",
            )
            # 反向自检：同一个选择器对**别的**浮层是能命中的（否则 C.2 恒真）
            other = page.locator('[data-testid="canvas-zoom-menu"]')
            probe_role = page.evaluate(
                """() => { const d = document.createElement('div');
                     d.setAttribute('role','menu');
                     d.setAttribute('data-testid','__probe__');
                     d.style.cssText='position:fixed;left:10px;top:10px;width:60px;height:30px';
                     document.body.appendChild(d); return true; }""")
            probe_rows = page.evaluate(ROLE_LAYER_JS)
            check(
                "C.3 反向自检：同一选择器对带 role 的元素**能**命中（证明 C.2 不是恒空）",
                any(r["tid"] == "__probe__" for r in probe_rows),
                f"探针被枚举到={[r['tid'] for r in probe_rows if r['tid'] == '__probe__']}")
            page.evaluate("""() => { const d = document.querySelector('[data-testid="__probe__"]');
                              if (d) d.remove(); }""")
            check("C.4 探针已清理（别把测试残留留给下一次运行）",
                  page.evaluate("() => !document.querySelector('[data-testid=\"__probe__\"]')"))

        check("Z.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 836-verifier OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
