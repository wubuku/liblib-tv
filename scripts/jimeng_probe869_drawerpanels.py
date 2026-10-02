#!/usr/bin/env python3
"""batch 869 诊断：AI 抽屉里那 3 个 `role="dialog"` —— 浮层套浮层时，
审计的 `open_layer()` 认到的是**哪一个**？

## 为什么要探这个（先探再判，§77）

867 把 `JimengAiDrawer` 里另外 3 个 `role="dialog"` 记成「本批没逐个探」。
本批要探它们，但先撞上一个**判据本身**的疑问：

这 3 个浮层（会话列表 / 搜索技能 / 添加参考）都渲染在**抽屉内部**
（`mx-3 mb-2`），而抽屉自己也是 `role="dialog"`（`canvas-agent-drawer`）。
`open_layer()` 那段 JS 遍历 `document.querySelectorAll(LAYER)`、**返回第一个
命中的** —— DOM 顺序上**祖先在子孙之前**，所以它多半会返回**外层的抽屉**，
而不是刚打开的那个内层面板。

若真如此：`measure()` 会把三个状态**全测成同一个抽屉**。那不是「抽屉有缺陷」，
而是**量错了对象** —— 正是 840/849 记的「后面每个状态都在报同一层」那个坑。

⚠️ 所以本探针**只测量、不改判据**：先把「它到底返回哪个」探死，
再决定改不改、怎么改。机制没验死就动判据 = §77 那条老毛病。

## 判据同款，不复制一份

`open_layer()` 的 JS 与 `MODALISH_JS` 都**直接从审计源码里取**
（`jimeng_unclickable_audit.py`），不在这份探针里抄第二份 ——
抄一份就是让同一判据分叉的起点（866 定的规矩）。

## 只诊断，不改产品

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe869_drawerpanels.py`
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b869-drawerpanels.json")
AUDIT = ROOT / "scripts" / "jimeng_unclickable_audit.py"

# 这三个就是 867 记的「没逐个探」的那三个（复刻侧 testid）
PANELS = [
    ("会话列表", '[data-testid="canvas-agent-session-menu-trigger"]',
     "canvas-agent-session-menu"),
    ("搜索技能", '[data-testid="canvas-agent-skill-trigger"]',
     "agent-skills-panel"),
    ("添加参考", '[data-testid="canvas-agent-composer-mention"]',
     "agent-mention-panel"),
]


def _extract_js(src: str, anchor: str) -> str:
    """从审计源码里取出 `anchor` 之后第一段 `page.evaluate(\"\"\"…\"\"\")`。

    ⚠️ 只做这一件事，不做通用解析 —— 通用解析器一旦跟不上审计的写法，
    就会静默取空串，然后探针「量了个空」还照样报通过。
    取不到就**抛**，不返回空串。

    ⚠️⚠️ 下面那两个定界符是**拼出来的**，不是直接写出来的。把
    `page.evaluate(` 后面那三个引号直接写在源码里的话（哪怕只是写在注释里），
    `jimeng_probe_js_syntax_check.py` 会把它当成本探针的一段内联 JS 拿去解析，
    然后报一句莫名其妙的语法错（869 第一版就被它带偏过一轮，以为是自己探针里
    的 JS 写错了）。**检查器认的是形态，不是意图** —— 自己别去撞它的形态。

    顺带一提：本文件第一版的另一个 bug 就是在 docstring 里直接写出了三个连续
    引号，**当场把自己的 docstring 提前闭合**（§65 早记着这条，第一版还是踩了）。
    """
    i = src.index(anchor)
    open_kw = "page.evaluate(" + '"' * 3
    close_kw = '"' * 3 + ")"
    j = src.index(open_kw, i) + len(open_kw)
    k = src.index(close_kw, j)
    return src[j:k]


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    if not AUDIT.exists():
        print(f"❌ 审计脚本不在：{AUDIT}")
        return 1
    asrc = AUDIT.read_text(encoding="utf-8")
    open_layer_js = _extract_js(asrc, "def open_layer()")
    # MODALISH_JS 是模块级常量，形如 `MODALISH_JS = """…"""`
    m = re.search(r'MODALISH_JS\s*=\s*"""(.*?)"""', asrc, re.S)
    if not m:
        print("❌ 审计里取不到 MODALISH_JS（模块级常量被改名了？）")
        return 1
    modalish_js = m.group(1)
    print(f"已从审计源码取到 open_layer 的 JS {len(open_layer_js)} 字符、"
          f"MODALISH_JS {len(modalish_js)} 字符（不抄第二份）")

    res: dict = {"panels": {}}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # ── 先把抽屉打开 ────────────────────────────────────────────
        dr = pg.locator('[data-testid="canvas-agent-drawer"]')
        if not dr.count():
            t = pg.locator('button[aria-label="与 AI 对话"]').first
            if not t.count():
                print("❌ 抽屉入口都不在 DOM 里 ⇒ 前置态没成立，**不是**"
                      "「入口没有」")
                b.close()
                return 1
            # ⚠️ 验落点再点（843 的教训）
            bb = t.bounding_box()
            if bb:
                cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
                hit = pg.evaluate(
                    "([x,y])=>{const e=document.elementFromPoint(x,y);"
                    "return e?e.tagName+'/'+(e.getAttribute('data-testid')"
                    "||e.getAttribute('aria-label')||''):null;}", [cx, cy])
                print(f"  抽屉入口落点 = {hit}")
            t.click(timeout=8000)
            time.sleep(1.5)
        print("抽屉开着：%d" % pg.locator(
            '[data-testid="canvas-agent-drawer"]').count())

        for name, trig, tid in PANELS:
            print(f"\n=== {name}（{tid}）===")
            rec: dict = {}
            t = pg.locator(trig)
            rec["trigger_n"] = t.count()
            if not t.count():
                rec["verdict"] = "入口按钮**不在 DOM 里** ⇒ 前置态没成立"
                print("  ❌ 入口不在 DOM")
                res["panels"][name] = rec
                continue
            # ⚠️⚠️ 「入口在 DOM 里」和「入口能点」是**两件事**。
            #   869 第一版直接 `t.first.click()`，结果 8s 超时把**整个探针**
            #   带走（后面两个面板一个都没量到）。这里改成先问 enabled：
            #   disabled 是**第三种「没结果」** —— 不是「按钮不存在」，
            #   也不是「前置态没成立」，而是「入口在、看得见、但此刻按不动」。
            #   不分开记账，就会有人把 disabled 读成「没接交互」。
            rec["disabled"] = t.first.is_disabled()
            rec["aria_disabled"] = t.first.get_attribute("aria-disabled")
            print(f"  入口在 DOM，disabled={rec['disabled']} "
                  f"aria-disabled={rec['aria_disabled']!r}")
            if rec["disabled"]:
                rec["verdict"] = ("入口**在 DOM 但 disabled** ⇒ 冷启动前置态"
                                  "不成立（不是「入口没有」，也不是「没接交互」）")
                print(f"  ⛔ {rec['verdict']}")
                res["panels"][name] = rec
                continue
            # 验落点
            bb = t.first.bounding_box()
            if bb:
                cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
                rec["hit"] = pg.evaluate(
                    "([x,y])=>{const e=document.elementFromPoint(x,y);"
                    "return e?e.tagName+'/'+(e.getAttribute('data-testid')"
                    "||e.getAttribute('aria-label')||''):null;}", [cx, cy])
                print(f"  入口落点 = {rec['hit']}")
            try:
                t.first.click(timeout=8000)
            except Exception as e:
                rec["verdict"] = f"点了但点不动：{str(e).splitlines()[0][:60]}"
                print(f"  ❌ {rec['verdict']}")
                res["panels"][name] = rec
                continue
            time.sleep(1.2)

            rec["layer_n"] = pg.locator(f'[data-testid="{tid}"]').count()
            # ⭐ 本探针要回答的那个问题
            rec["open_layer_says"] = pg.evaluate(open_layer_js)
            print(f"  层计数 = {rec['layer_n']}  "
                  f"审计 open_layer() 认到 = {rec['open_layer_says']!r}")
            print(f"  ⇒ {'**认对了**' if rec['open_layer_says'] == tid else '**认错了（认成外层）**'}")

            if rec["layer_n"]:
                rec["geometry"] = pg.evaluate("""(tid) => {
                  const e = document.querySelector(`[data-testid="${tid}"]`);
                  const r = e.getBoundingClientRect();
                  const q = (s) => e.querySelectorAll(s).length;
                  return {rect: [Math.round(r.x), Math.round(r.y),
                                 Math.round(r.width), Math.round(r.height)],
                          role: e.getAttribute('role') || '',
                          in_drawer: !!e.closest('[data-testid="canvas-agent-drawer"]'),
                          focusables: q('button,[href],input,select,textarea,'
                            + '[tabindex]:not([tabindex="-1"]),[role=menuitem]'),
                          text: (e.innerText || '').trim().slice(0, 60)};
                }""", tid)
                # ⚠️ MODALISH_JS 是 `(tid) => …`，**必须把层的 testid 传进去**。
                #   869 第一版忘了传参，于是三个面板的 modalish 全是
                #   「层不存在」—— 而那不是结论，是**量法错了**
                #   （把「没量到」写成「不是模态」）。
                rec["modalish"] = pg.evaluate(modalish_js, tid)
                g = rec["geometry"]
                print(f"  几何 {g['rect']} role={g['role']!r} "
                      f"在抽屉内={g['in_drawer']} 可聚焦={g['focusables']}")
                print(f"  文案：{g['text']!r}")
                print(f"  modalish = {json.dumps(rec['modalish'], ensure_ascii=False)}")

            # 收掉：Escape（批 839 给抽屉接的）
            pg.keyboard.press("Escape")
            time.sleep(0.8)
            rec["closed_by_escape"] = (
                pg.locator(f'[data-testid="{tid}"]').count() == 0)
            print(f"  Escape 收层 = {rec['closed_by_escape']}")
            res["panels"][name] = rec

        # 收抽屉
        pg.keyboard.press("Escape")
        time.sleep(0.8)
        res["drawer_left_open"] = pg.locator(
            '[data-testid="canvas-agent-drawer"]').count() > 0
        print(f"\n最后抽屉还开着？{res['drawer_left_open']}")

        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
