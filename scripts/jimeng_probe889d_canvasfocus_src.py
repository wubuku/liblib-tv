#!/usr/bin/env python3
"""batch 889d 源站探针：点画布空白之后，焦点到底落在**哪个元素**上？

## 为什么单独测这个

889b（复刻侧）查到一条**已成立的真差异**（两边各 2/2）：

| | 点画布空白之后的焦点 |
|---|---|
| 源站 | 某个 `aria-label='Canvas'` 的元素 |
| 复刻 | `body`（`.react-flow__pane` 等**四个**容器 `tabindex` 全是 `None`） |

但「某个 `aria-label='Canvas'` 的元素」**太粗** —— 不知道它是
React Flow 的 pane、还是外层包一个 `role=application` 的容器、还是
`contenteditable`，更不知道它**能不能被 Tab 到**。

⇒ 这跑把那个元素的**身份一次钉死**：`tagName` / `className` /
`data-testid` / `role` / `tabindex` / `contenteditable`，以及
**Tab 能不能走到它**（`tabindex=None` ≠ 键盘不可达：默认的
`<div>` 也不可 Tab，但**有些实现**会在 keydown 时自己接管焦点）。

## 结论口径

- 只报**读到的**，不许推断「所以源站画布是可访问的」
- Tab 能不能到它是**独立**一条读数，不许用「它有焦点」推出来

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键（Tab）。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe889d_canvasfocus_src.py
"""

import json

OUT = "/tmp/b889d-src-canvasfocus.json"

IDENT_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', is_body: true};
  const chain = [];
  let e = a;
  for (let i = 0; i < 5 && e; i++) {
    chain.push({tag: e.tagName,
                cls: (e.className || '').toString().slice(0, 90),
                testid: e.getAttribute('data-testid'),
                role: e.getAttribute('role'),
                tabindex: e.getAttribute('tabindex'),
                contenteditable: e.getAttribute('contenteditable'),
                aria: e.getAttribute('aria-label')});
    e = e.parentElement;
  }
  return {tag: a.tagName,
          cls: (a.className || '').toString().slice(0, 90),
          testid: a.getAttribute('data-testid'),
          role: a.getAttribute('role'),
          tabindex: a.getAttribute('tabindex'),
          contenteditable: a.getAttribute('contenteditable'),
          aria: a.getAttribute('aria-label'),
          rect: (() => { const r = a.getBoundingClientRect();
            return [Math.round(r.x), Math.round(r.y),
                    Math.round(r.width), Math.round(r.height)]; })(),
          chain};
}"""

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

PANE_INFO_JS = """() => {
  const out = [];
  for (const s of ['.react-flow__pane', '.react-flow__renderer',
                   '.react-flow', '.react-flow__viewport']) {
    for (const e of document.querySelectorAll(s)) {
      out.push({sel: s, tag: e.tagName,
                cls: (e.className || '').toString().slice(0, 90),
                role: e.getAttribute('role'),
                tabindex: e.getAttribute('tabindex'),
                contenteditable: e.getAttribute('contenteditable'),
                aria: e.getAttribute('aria-label')});
    }
  }
  return out;
}"""

# Tab 能不能走到画布：从 body 连按 N 次 Tab，记每次落点里有没有画布元素
# ⚠️ 用 `IDENT_JS` 逐次读（**独立**读数），不写一个「预判型」的 JS ——
# 预判会把「没到」和「到了但没认出来」混成同一个结果。


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    rec = {}
    out["pane_info"] = ev(PANE_INFO_JS)
    print("\n== 画布容器们 ==")
    for e in out["pane_info"]:
        print(f"   {e['sel']:24s} {e['tag']} role={e['role']!r} "
              f"tabindex={e['tabindex']!r} aria={e['aria']!r} "
              f"cls={e['cls']!r}")

    # 点画布空白 → 焦点落谁
    spot = ev(BLANK_JS)
    rec["blank_spot"] = spot
    if spot:
        page.mouse.click(spot[0], spot[1])
        page.wait_for_timeout(900)
    rec["focus_after_blank"] = ev(IDENT_JS)
    fb = rec["focus_after_blank"]
    print(f"\n== 点空白 {spot} 之后的焦点 ==")
    print(f"   tag={fb.get('tag')!r} role={fb.get('role')!r} "
          f"tabindex={fb.get('tabindex')!r} "
          f"contenteditable={fb.get('contenteditable')!r}")
    print(f"   aria={fb.get('aria')!r} cls={fb.get('cls')!r}")
    print(f"   rect={fb.get('rect')}")
    for i, c in enumerate(fb.get("chain", [])[:4]):
        print(f"   往上 {i}: {c['tag']} role={c['role']!r} "
              f"tabindex={c['tabindex']!r} aria={c['aria']!r}")

    # Tab 能不能走到画布（**独立**读数，不许用「它有焦点」推出来）
    page.evaluate("() => document.body.focus()")
    page.mouse.click(spot[0], spot[1]) if spot else None
    walk = []
    for i in range(24):
        page.keyboard.press("Tab")
        page.wait_for_timeout(120)
        walk.append(ev(IDENT_JS))
    rec["tab_walk"] = [
        {"tag": w.get("tag"), "aria": w.get("aria"),
         "cls": w.get("cls"), "tabindex": w.get("tabindex")}
        for w in walk]
    in_pane = [i for i, w in enumerate(rec["tab_walk"])
               if "react-flow__pane" in (w.get("cls") or "")]
    rec["tab_reached_pane"] = in_pane
    print(f"\n== Tab 24 次，落在画布容器上的步数 ==")
    print(f"   {in_pane if in_pane else '一次都没到（Tab 走不到画布）'}")
    for i, w in enumerate(rec["tab_walk"][:12]):
        print(f"   Tab{i+1:<2d} {w.get('tag')}/tabindex={w.get('tabindex')!r}"
              f"/{w.get('aria')!r}")

    rec["verdict"] = "sampled"
    out["result"] = rec
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
