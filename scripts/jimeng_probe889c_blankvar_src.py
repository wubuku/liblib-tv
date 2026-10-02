#!/usr/bin/env python3
"""batch 889c 源站探针：只隔离**一个**变量 —— 按 Esc 之前那次 `blank()`。

## 为什么只测这一个变量

`Canvas` 那个落点是 **888 一跑**读到的，此后：

| 跑 | 前置态 | 落点 |
|---|---|---|
| 888 | `blank()` → 点节点中心 → Esc | **`Canvas`** |
| 889 `nofocus` | 程序化聚焦过芯片（**不等于** 888） | 节点本体 |
| 889b `pure_mouse` | 点节点中心 → Esc（**没有** `blank()`） | 节点本体 2/2 |

⇒ 两次复现**都落在节点本体**，唯一还没对齐的差异就是 888 按 Esc 前
**先点了一下画布空白**（`blank()`：在 `.react-flow__pane` 上找一个
`elementFromPoint` 验过、且不在任何节点里的坐标，点它，800ms）。

这跑**只**加这一个变量，其他照 889b 的 `pure_mouse` 原样。

## 结论口径

- 2 次；2/2 同一类才写「该前置态 ⇒ 该落点」
- 如果又是「节点本体」⇒ `Canvas` 那个读数**仍然解释不了**，
  如实记成「1 跑读到、3 跑复现不出」—— **不许**倒过来说 888 记错了，
  也**不许**说它是 flake（两件事都还没测）

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe889c_blankvar_src.py
"""

import json

OUT = "/tmp/b889c-src-blankvar.json"
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)', text: '',
                                   in_audio_node: false, in_listbox: false};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""

# 888 原样：点画布空白（坐标**先 elementFromPoint 验过**、且不在任何节点里）
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

NODE_CLASS_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  return n ? (n.className || '').toString() : null;
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def classify(f):
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("aria") == "Canvas":
        return "Canvas"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


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
    tid = None
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
        before = set(ev("() => [...document.querySelectorAll('.react-flow__node')]"
                        ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                   ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            tid = new[0]
            break
    out["audio_node"] = tid
    print(f"== 音频节点 {tid} ==")

    runs = []
    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    else:
        for rep in range(1, REPS + 1):
            rec = {"kind": "blank_then_center", "rep": rep}
            spot = ev(BLANK_JS)
            rec["blank_spot"] = spot
            if spot:
                page.mouse.click(spot[0], spot[1])
                page.wait_for_timeout(800)
            rec["toolbar_after_blank"] = ev(TOOLBAR_JS)
            rec["focus_after_blank"] = ev(FOCUS_JS)
            c = ev(CENTER_JS, tid)
            if not c:
                rec["verdict"] = "前置态没成立：算不出节点中心"
                runs.append(rec)
                print(f"  !! {rec['verdict']}")
                continue
            page.mouse.click(c[0], c[1])
            page.wait_for_timeout(1100)          # 与 888 同
            rec["toolbar_before"] = ev(TOOLBAR_JS)
            if not rec["toolbar_before"]:
                rec["verdict"] = "前置态没成立：blank+点中心没开出面板"
                runs.append(rec)
                print(f"  !! {rec['verdict']}")
                continue
            rec["class_before"] = ev(NODE_CLASS_JS, tid)
            rec["focus_before"] = ev(FOCUS_JS)

            page.keyboard.press("Escape")
            page.wait_for_timeout(1100)          # 与 888 同

            rec["focus_after"] = ev(FOCUS_JS)
            rec["landing"] = classify(rec["focus_after"])
            rec["toolbar_after"] = ev(TOOLBAR_JS)
            rec["class_after"] = ev(NODE_CLASS_JS, tid)
            rec["verdict"] = "sampled"
            runs.append(rec)
            print(f"\n[blank_then_center #{rep}] blank 落点={spot}"
                  f"  点空白后工具条={rec['toolbar_after_blank']}"
                  f" 焦点={rec['focus_after_blank']['aria']!r}")
            print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                  f"  在节点内={rec['focus_before']['in_audio_node']}"
                  f"  工具条={rec['toolbar_before']}")
            print(f"   按后：{rec['landing']}  焦点={rec['focus_after']['aria']!r}"
                  f"  工具条={rec['toolbar_after']}")
            print(f"   class：{rec['class_before']!r} → {rec['class_after']!r}")

        out["runs"] = runs
        ls = [r.get("landing") for r in runs if r.get("landing")]
        out["summary"] = {
            "landings": ls,
            "stable": len(ls) == REPS and len(set(ls)) == 1,
            "landing": ls[0] if ls and len(set(ls)) == 1 else None,
        }
        print(f"\n== 汇总：落点={ls} "
              f"{'稳定' if out['summary']['stable'] else '不稳定'} ==")
        if out["summary"]["stable"] and out["summary"]["landing"] == "节点本体":
            print("   ⇒ 加了 blank() **仍然**是节点本体 ⇒ "
                  "`Canvas` 那个读数**仍然解释不了**")
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
