#!/usr/bin/env python3
"""batch 889b 复刻探针：把「焦点真在**画布**上、面板开着」这个前置态**立起来**。

## 889 第一跑的洞

889 复刻侧的 `canvas` 那一档**前置态没成立**：

```
[canvas #1] 按前：焦点=''/'音频 1'  在节点内=True   ← 焦点被节点抢走了
[canvas #1] 按后：body
```

复刻侧「点空白 → 再点节点中心」这串操作，**点节点那一下把焦点抢到了
节点上**；而源站 889c 同样这串操作之后焦点**留在画布**：

```
[blank_then_center #1] 按前：焦点='Canvas'  在节点内=False
```

⇒ 两条都 2/2 稳定，但**量的不是同一个前置态**，`body` vs `Canvas`
**不能**判成差异。这正是「我没检测到 ⇒ 先确认我够得着」那条。

⇒ 这跑**只**解决前置态：**先开面板、再程序化把焦点放到画布上**，
并且**验到焦点确实不在节点里**才按 Esc。

## 顺带量一条**已成立的真差异**候选

「点节点中心**会不会**把焦点给节点」：
源站 = **不会**（889c 焦点留在 `Canvas`）、复刻 = **会**（889 焦点在节点）。
本跑把两边的读数都**显式记下来**，因为它决定了上面那个前置态能不能用
鼠标达成 —— 是**独立**于 Esc 落点的一条行为。

## 怎么把焦点放到画布上

React Flow 的 pane 有没有 `tabindex` **先量再决定**：
- 有 ⇒ 程序化 `focus()`，干净
- 没有 ⇒ 记下来，并明确说「这个前置态在复刻侧**用键盘达不到**」，
  不许硬凑一个近似状态当它

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe889b_esclanding_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b889b-ck-esclanding.json")
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', aria: '(body)', text: '',
    in_audio_node: false, in_listbox: false};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => !!document.querySelector(
  '[data-testid="audio-all-voices-listbox"]')"""
CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080], [1500, 1000]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return {xy: [x, y], from: 'list'};
  }
  const p = document.querySelector('.react-flow__pane');
  if (!p) return null;
  const r = p.getBoundingClientRect();
  const x = Math.round(r.x + r.width - 30);
  const y = Math.round(r.y + r.height - 30);
  const t = document.elementFromPoint(x, y);
  if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
    return {xy: [x, y], from: 'pane_rect'};
  return null;
}"""
# 画布上**哪些元素可聚焦** —— 先量再决定能不能程序化放焦点
# ⚠️⚠️ 889b 第一版这个 JS **只取 `tabindex`**，我据此在结论里写了
# 「复刻 role=None/aria=None」—— 而它**压根没取那两个属性**，那句是我
# 从一个没测过的读数上推出来的（现场用一条临时脚本复核：复刻其实是
# `role='application'` + `aria-label='Canvas'`，**和源站一样**）。
# ⇒ 教训同 884：**探针没取的属性，不许出现在结论里**。这里把
# role / aria / testid 一并取回，读数才够下结论。
FOCUSABLE_JS = """() => {
  const sels = ['.react-flow__pane', '.react-flow__renderer',
                '.react-flow', '.react-flow__viewport', '.react-flow__node-pane'];
  const out = [];
  for (const s of sels) {
    for (const e of document.querySelectorAll(s)) {
      out.push({sel: s, tag: e.tagName,
                role: e.getAttribute('role'),
                aria: e.getAttribute('aria-label'),
                testid: e.getAttribute('data-testid'),
                tabindex: e.getAttribute('tabindex'),
                has_tabindex: e.hasAttribute('tabindex')});
    }
  }
  return out;
}"""
FOCUS_PANE_JS = """() => {
  // ⚠️ 源站点空白时焦点落在 **`.react-flow` 根容器**（role=application +
  // aria=Canvas + tabindex=0，889d 实测），**不是** `.react-flow__pane`
  // —— pane 的 tabindex 是 None，点了也没焦点。所以这里也**先试根容器**。
  const p = document.querySelector('.react-flow')
    || document.querySelector('.react-flow__pane')
    || document.querySelector('.react-flow__renderer')
    || document.querySelector('.react-flow__viewport');
  if (!p) return {no_pane: true};
  p.focus();
  return {focused: document.activeElement === p,
          tag: p.tagName, cls: (p.className || '').toString().slice(0, 60),
          role: p.getAttribute('role'),
          tabindex: p.getAttribute('tabindex'),
          aria: p.getAttribute('aria-label') || ''};
}"""
NODE_TABBABLE_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  return {tag: n.tagName, tabindex: n.getAttribute('tabindex'),
          has_tabindex: n.hasAttribute('tabindex')};
}"""


def classify(f: dict) -> str:
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("aria") == "Canvas":
        return "Canvas"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        before = set(pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))"))
        t = pg.locator('button[aria-label="音频"]').first
        if not t.count():
            print("❌ 插不进音频节点 ⇒ 前置态没成立")
            b.close()
            return 1
        t.click(timeout=8000)
        time.sleep(2.0)
        new = [x for x in pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))") if x not in before]
        if not new:
            print("❌ 集合差分是空 ⇒ 插节点没生效")
            b.close()
            return 1
        nid = new[0]
        res["audio_node"] = nid
        pg.keyboard.press("Escape")
        time.sleep(0.4)

        def ev(js, arg=None):
            return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

        # ── 第一段：**点节点会不会把焦点抢走**（独立于 Esc 的一条行为）──
        click_focus = []
        for rep in range(1, REPS + 1):
            if ev(TOOLBAR_JS):
                pg.keyboard.press("Escape")
                time.sleep(0.8)
            sp = ev(BLANK_JS)
            if sp:
                pg.mouse.click(sp["xy"][0], sp["xy"][1])
                time.sleep(0.8)
            rec = {"rep": rep, "blank_spot": sp,
                   "focus_after_blank": ev(FOCUS_JS)}
            c = ev(CENTER_JS, nid)
            if c:
                pg.mouse.click(c[0], c[1])
                time.sleep(1.1)
            rec["toolbar_after_center"] = ev(TOOLBAR_JS)
            rec["focus_after_center"] = ev(FOCUS_JS)
            rec["node_took_focus"] = bool(
                rec["focus_after_center"].get("in_audio_node"))
            click_focus.append(rec)
            print(f"\n[click_focus #{rep}] 点空白后焦点="
                  f"{rec['focus_after_blank']['aria']!r}"
                  f" → 点节点后焦点={rec['focus_after_center']['aria']!r}"
                  f"/{rec['focus_after_center']['text']!r}"
                  f"  节点抢到焦点={rec['node_took_focus']}"
                  f"  工具条={rec['toolbar_after_center']}")
        res["click_focus"] = click_focus
        res["node_tabbable"] = ev(NODE_TABBABLE_JS, nid)

        # ── 第二段：可聚焦元素普查（**先量再决定**能不能程序化放焦点）──
        res["focusable"] = ev(FOCUSABLE_JS)
        print(f"\n== 画布上可聚焦元素 ==")
        for e in res["focusable"]:
            print(f"   {e['sel']:26s} {e['tag']} role={e['role']!r} "
                  f"aria={e['aria']!r} tabindex={e['tabindex']!r}")
        focusable = [e for e in res["focusable"] if e["has_tabindex"]]
        res["any_focusable"] = bool(focusable)

        # ── 第三段：面板开着 + 焦点真在画布上 → Esc ────────────────
        runs = []
        if not focusable:
            res["verdict"] = ("前置态没成立：复刻侧画布上**没有**任何带 "
                              "tabindex 的元素 ⇒ 「焦点在画布上」这个前置态"
                              "**用键盘达不到** ⇒ 本轮不测（**不是**"
                              "「落点没差异」）")
            print(f"\n  !! {res['verdict']}")
        else:
            for rep in range(1, REPS + 1):
                rec = {"kind": "canvas_prog", "rep": rep}
                if not ev(TOOLBAR_JS):
                    c = ev(CENTER_JS, nid)
                    if not c:
                        rec["verdict"] = "算不出节点中心"
                        runs.append(rec)
                        continue
                    pg.mouse.click(c[0], c[1])
                    time.sleep(1.1)
                if not ev(TOOLBAR_JS):
                    rec["verdict"] = "前置态没成立：面板没开"
                    runs.append(rec)
                    print(f"  !! [canvas_prog #{rep}] {rec['verdict']}")
                    continue
                fp = ev(FOCUS_PANE_JS)
                rec["focus_pane"] = fp
                time.sleep(0.3)
                rec["focus_before"] = ev(FOCUS_JS)
                if not fp.get("focused") or rec["focus_before"].get("in_audio_node"):
                    rec["verdict"] = (
                        f"前置态没成立：焦点没能放到画布上 {fp}"
                        f"（焦点在节点内="
                        f"{rec['focus_before'].get('in_audio_node')}）⇒ 本轮不测")
                    runs.append(rec)
                    print(f"  !! [canvas_prog #{rep}] {rec['verdict']}")
                    continue
                rec["toolbar_before"] = ev(TOOLBAR_JS)

                pg.keyboard.press("Escape")
                time.sleep(1.0)

                rec["focus_after"] = ev(FOCUS_JS)
                rec["landing"] = classify(rec["focus_after"])
                rec["toolbar_after"] = ev(TOOLBAR_JS)
                rec["verdict"] = "sampled"
                runs.append(rec)
                print(f"\n[canvas_prog #{rep}] 面板开 + 焦点程序化放画布"
                      f"（{fp.get('cls')}）")
                print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                      f"  在节点内={rec['focus_before']['in_audio_node']}"
                      f"  工具条={rec['toolbar_before']}")
                print(f"   按后：{rec['landing']}"
                      f"  焦点={rec['focus_after']['aria']!r}"
                      f"  工具条={rec['toolbar_after']}")

            res["runs"] = runs
            ls = [r.get("landing") for r in runs if r.get("landing")]
            res["summary"] = {
                "landings": ls,
                "stable": len(ls) == REPS and len(set(ls)) == 1,
                "landing": ls[0] if ls and len(set(ls)) == 1 else None,
            }
            print(f"\n== 汇总：焦点在画布上按 Esc ⇒ 落点={ls} "
                  f"{'稳定' if res['summary']['stable'] else '不稳定'} ==")
            res["verdict"] = "sampled"

        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
