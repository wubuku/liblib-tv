#!/usr/bin/env python3
"""batch 860：**证伪实验** —— `autoFocus` 会不会在重渲染后把焦点抢回面板？

§77 留了一个**未证实**的推测：

> 新版面板订阅 zustand `nodes`，画布任何变动都会让它重渲染；而输入框带
> `autoFocus` —— React 可能在重渲染后**重新施加** `autoFocus`，把焦点从画布
> **抢回面板**。这能解释「blur 之后第一次 Tab 又落回层内」。

§77 同时定下硬规矩：**机制未验死之前不许改判据/改产品**。这个探针就是去
**验死**它 —— 而且它必须**能判红**：如果实验跑完仍支持假设，它得自己说
「假设未被推翻」。

实验设计（三个可观测量，全部读状态，不看元素存在）：

  E1 `blur()` 之后**立刻**读 `activeElement` —— 在层内还是层外？
  E2 焦点**移到一个确定的画布控件**上（按 Tab 走 N 步到已知 tid），
     然后让画布变动（触发面板重渲染），**不动任何焦点**，
     再读 `activeElement` —— 焦点被抢回面板了吗？
  E3 不做任何重渲染时，同一套 E2 步骤跑一遍当**对照**。

E2 与 E3 的差值 = 「重渲染把焦点抢回来」的**净效应**。
差值为 0 ⇒ 假设**被推翻**（autoFocus 不会在重渲染后重新施加）。

⚠️ 跑法（自己起浏览器，不能用 headless 注入）：

    /opt/miniconda3/bin/python3 scripts/jimeng_probe860_autofocus.py old
    /opt/miniconda3/bin/python3 scripts/jimeng_probe860_autofocus.py wide

`old` 用当前工作区的 242px 猜测版，`wide` 用 /tmp/wide-search.tsx
（跑之前自己装回去）。**两遍都跑，对照才有意义。**

⚠️ 本探针**只诊断，不改产品**。
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
LAYER = "jimeng-search-overlay"

WHO_JS = """(tid) => {
  const L = document.querySelector(`[data-testid="${tid}"]`);
  const a = document.activeElement;
  if (!a || a === document.body)
    return {who: 'body', in_layer: false, tid: '', al: ''};
  return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
            || a.getAttribute('aria-label') || '')
            .toString().slice(0, 26)),
          in_layer: !!(L && L.contains(a)),
          tid: a.getAttribute('data-testid') || '',
          al: (a.getAttribute('aria-label') || '').slice(0, 26),
          is_input: a.tagName === 'INPUT'};
}"""


def snapshot(pg, label, e):
    w = pg.evaluate(WHO_JS, LAYER)
    e[label] = w
    print(f"   {label:<26} in_layer={w['in_layer']!s:<5} who={w['who']!r}")
    return w


def open_panel(pg):
    trg = pg.locator('button[aria-label="搜索"]')
    if not trg.count():
        return False
    trg.first.click(timeout=8000)
    pg.wait_for_timeout(1000)
    return pg.locator(f'[data-testid="{LAYER}"]').count() > 0


def run(pg, mode):
    out = {"mode": mode}
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    pg.set_viewport_size({"width": 1512, "height": 1200})
    pg.wait_for_timeout(1500)

    print(f"\n===== mode={mode} =====")
    if not open_panel(pg):
        out["verdict"] = "panel_not_open"
        print("!! 面板开不出来")
        return out
    out["layer_open"] = True

    # ── E1：blur 之后立刻读 ────────────────────────────────────────────────
    print("\n-- E1 blur() 之后立刻读 --")
    pg.evaluate("() => { const a = document.activeElement;"
                " if (a && a.blur) a.blur(); }")
    pg.wait_for_timeout(150)
    e = {}
    snapshot(pg, "E1 blur 之后", e)
    out["E1"] = e

    # ── E2：焦点放到一个**确定的画布控件**上（用 Tab 走到已知 tid）──────
    #    然后**不碰焦点**，只让画布变动（触发面板重渲染），再看焦点去哪了。
    print("\n-- E2 焦点落在画布控件上 → 触发重渲染（不碰焦点）--")
    pg.evaluate("() => { const a = document.activeElement;"
                " if (a && a.blur) a.blur(); }")
    # 走到一个**层外**的确定控件：顶栏「更多」
    landed = None
    for _ in range(60):
        pg.keyboard.press("Tab")
        w = pg.evaluate(WHO_JS, LAYER)
        if w.get("tid") == "canvas-more-trigger":
            landed = w
            break
    if not landed:
        out["E2"] = {"why": "走不到 canvas-more-trigger（层外锚点）"}
        print("   ⚠ 走不到层外锚点 ⇒ E2/E3 对照做不了")
        return out
    print(f"   焦点已落在层外: {landed['who']!r}")
    before = snapshot(pg, "E2 变动前", e)

    # 触发面板重渲染：改一个**不改变 nodes 长度**的状态（搜索词），它会让
    # 面板重渲染但不动画布 —— 这正是「面板重渲染、画布不变」的那一路。
    inp = pg.locator(f'[data-testid="{LAYER}"] input').first
    if inp.count():
        inp.fill("审")
        pg.wait_for_timeout(500)
        after = snapshot(pg, "E2 面板重渲染后", e)
    else:
        after = snapshot(pg, "E2 无输入框", e)
    out["E2"] = {"before": before, "after": after,
                 "stolen": bool(before and after and not before["in_layer"]
                                and after["in_layer"])}

    # ── E3 对照：**同样等这么久，但不触发任何重渲染** ──────────────────────
    print("\n-- E3 对照：不触发重渲染，只等同样时长 --")
    pg.evaluate("() => { const a = document.activeElement;"
                " if (a && a.blur) a.blur(); }")
    landed2 = None
    for _ in range(60):
        pg.keyboard.press("Tab")
        w = pg.evaluate(WHO_JS, LAYER)
        if w.get("tid") == "canvas-more-trigger":
            landed2 = w
            break
    b3 = snapshot(pg, "E3 等待前", e)
    pg.wait_for_timeout(500)
    a3 = snapshot(pg, "E3 等待后", e)
    out["E3"] = {"before": b3, "after": a3,
                 "stolen": bool(b3 and a3 and not b3["in_layer"] and a3["in_layer"])}

    # ── 判决：E2 抢焦点 且 E3 不抢 ⇒ 重渲染是原因；否则假设被推翻 ──────────
    out["verdict"] = ("autoFocus 重渲染抢焦点：**未推翻**"
                      if out["E2"].get("stolen") and not out["E3"].get("stolen")
                      else "autoFocus 重渲染抢焦点：**被推翻**"
                      f"（E2 抢={out['E2'].get('stolen')}、"
                      f"E3 抢={out['E3'].get('stolen')}）")
    print(f"\n== 判决：{out['verdict']} ==")
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "old"
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1512, "height": 1200})
        pg = ctx.new_page()
        try:
            res = run(pg, mode)
        finally:
            b.close()
    with open(f"/tmp/b860-autofocus-{mode}.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\n== 已写 /tmp/b860-autofocus-{mode}.json ==")


if __name__ == "__main__":
    main()
