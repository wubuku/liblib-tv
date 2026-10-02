#!/usr/bin/env python3
"""batch 890c 复刻探针：把 890b 那套**同一判据**用在复刻侧，比对机制。

## 源站那边已经查清的机制（890b，两条序列各 2/2，完全一致）

- 节点 `tabindex='0'`；但**点击坐标落点是节点里的 `svg`**（tabIndex=-1）
- 源站代码（栈里的 `r5`）在两条序列里都调 `focus()`，目标**都是画布根**：
  - **A**（先点空白再点节点）：`当时已是焦点=True` ⇒ 那次 `focus()` **空操作**
  - **B**（直接点节点）：`当时已是焦点=False` ⇒ 它**真的**把焦点搬到画布根
    （= focusin #1）
- B 的 focusin #2 才是**浏览器原生**把焦点移到节点；A 的 focusin **0 次**

⇒ 源站 A/B 的差别**不是应用逻辑不同**，而是**焦点起点**不同引发的
浏览器默认行为（mousedown 落点若在当前焦点元素的**子树内**，浏览器
不移动焦点）。节点本身够不够聚焦是另一回事。

## 这里只量复刻侧，判据逐字复用 890b 的 JS

不重写判据（免得两边各量各的、量出「不同」其实只是判据不同）。

## 顺带回答一个 889 留下的问题

889 补了 `tabindex='0'` 之后，复刻「点空白 ⇒ 焦点 `Canvas`」已经和源站
一致；但「点空白后再点节点」，源站**不**被节点抢焦点、复刻**被抢走**
（2/2）。这跑看**复刻这边是谁在 focus 节点**：
- 若是**浏览器原生**（`focusin` 有、但 `focus()` 调用里**没有**节点）
  ⇒ 两条序列在浏览器层就该一样，差异只可能来自「当前焦点不在画布根」
- 若是**有 JS 主动 focus 节点** ⇒ 那就是复刻侧**多了一步**源站没有的动作

## 诊断动作不许留痕

劫持的 prototype 与监听都在 `finally` 里还原/摘除（882 的规矩）。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe890c_nodefocus_why_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b890c-ck-nodefocus-why.json")
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          is_canvas_root: !!(a.closest && a.closest(
            '.react-flow') && !a.closest('.react-flow__node'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
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
        && !t.closest('.react-flow__node')) return [x, y];
  }
  const p = document.querySelector('.react-flow__pane');
  if (!p) return null;
  const r = p.getBoundingClientRect();
  const x = Math.round(r.x + r.width - 30);
  const y = Math.round(r.y + r.height - 30);
  const t = document.elementFromPoint(x, y);
  if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
    return [x, y];
  return null;
}"""
HIT_JS = """(xy) => {
  const e = document.elementFromPoint(xy[0], xy[1]);
  if (!e) return {none: true};
  const chain = [];
  let n = e;
  for (let i = 0; i < 6 && n; i++) {
    chain.push({tag: n.tagName,
                cls: (n.className && n.className.toString
                      ? n.className.toString()
                      : String(n.className)).slice(0, 60),
                tabindex: n.getAttribute('tabindex'),
                tabIndexProp: n.tabIndex,
                testid: n.getAttribute('data-testid')});
    n = n.parentElement;
  }
  return {tag: e.tagName, tabIndexProp: e.tabIndex, chain};
}"""

# ⚠️ 与 890b **逐字同款**：`defaultPrevented` 在**冒泡阶段**读
INSTALL_JS = """() => {
  const w = window.__b890c = {md_bubble: [], focusins: [],
                              focuses: [], blurs: []};
  w.onMdBubble = (e) => { w.md_bubble.push({
      target_in_node: !!(e.target.closest && e.target.closest(
        '.react-flow__node-audio')),
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { const t = e.target;
    w.focusins.push({tag: t.tagName,
                     aria: t.getAttribute('aria-label') || '',
                     in_node: !!(t.closest && t.closest(
                       '.react-flow__node-audio')),
                     is_canvas_root: !!(t.closest && t.closest(
                       '.react-flow') && !t.closest('.react-flow__node'))}); };
  document.addEventListener('mousedown', w.onMdBubble, false);
  document.addEventListener('focusin', w.onFi, true);
  w.origFocus = HTMLElement.prototype.focus;
  w.origBlur = HTMLElement.prototype.blur;
  w.who = () => { try { return (new Error()).stack.split('\\n').slice(2, 5)
      .map(s => s.trim()).join(' | ').slice(0, 240); } catch (x) { return '?'; } };
  w.ident = (el) => ({tag: el.tagName,
      aria: el.getAttribute('aria-label') || '',
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 16),
      in_node: !!(el.closest && el.closest('.react-flow__node-audio')),
      is_canvas_root: !!(el.closest && el.closest(
        '.react-flow') && !el.closest('.react-flow__node')),
      already_active: document.activeElement === el});
  HTMLElement.prototype.focus = function (...a) {
    try { w.focuses.push({target: w.ident(this), who: w.who()}); } catch (x) {}
    return w.origFocus.apply(this, a);
  };
  HTMLElement.prototype.blur = function (...a) {
    try { w.blurs.push({target: w.ident(this), who: w.who()}); } catch (x) {}
    return w.origBlur.apply(this, a);
  };
  return true;
}"""

READ_JS = """() => { const w = window.__b890c;
  if (!w) return null;
  return {md_bubble: w.md_bubble, focusins: w.focusins,
          focuses: w.focuses, blurs: w.blurs}; }"""
CLEAR_JS = """() => { const w = window.__b890c;
  if (!w) return false;
  w.md_bubble = []; w.focusins = []; w.focuses = []; w.blurs = [];
  return true; }"""
RESTORE_JS = """() => { const w = window.__b890c;
  if (!w) return false;
  document.removeEventListener('mousedown', w.onMdBubble, false);
  document.removeEventListener('focusin', w.onFi, true);
  if (w.origFocus) HTMLElement.prototype.focus = w.origFocus;
  if (w.origBlur) HTMLElement.prototype.blur = w.origBlur;
  delete window.__b890c; return true; }"""
NODE_TABINDEX_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  return {tabindex: n.getAttribute('tabindex'), tabIndexProp: n.tabIndex}; }"""


def classify(f: dict) -> str:
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("is_canvas_root"):
        return "画布"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        res["runs"] = []
        for rep in range(1, REPS + 1):
            for seq in ("A_blank_then_node", "B_node_directly"):
                rec: dict = {"rep": rep, "seq": seq}
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3.5)
                before = set(pg.evaluate(
                    "() => [...document.querySelectorAll('.react-flow__node')]"
                    ".map(n => n.getAttribute('data-testid'))"))
                t = pg.locator('button[aria-label="音频"]').first
                if not t.count():
                    rec["verdict"] = "前置态没成立：没有音频入口"
                    res["runs"].append(rec)
                    print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                    continue
                t.click(timeout=8000)
                time.sleep(1.8)
                new = [x for x in pg.evaluate(
                    "() => [...document.querySelectorAll('.react-flow__node')]"
                    ".map(n => n.getAttribute('data-testid'))") if x not in before]
                if not new:
                    rec["verdict"] = "前置态没成立：集合差分是空"
                    res["runs"].append(rec)
                    print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                    continue
                nid = new[0]
                pg.keyboard.press("Escape")
                time.sleep(0.4)

                def ev(js, arg=None):
                    return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

                ev(INSTALL_JS)
                try:
                    rec["node_tabindex"] = ev(NODE_TABINDEX_JS, nid)
                    if seq == "A_blank_then_node":
                        spot = ev(BLANK_JS)
                        rec["blank_spot"] = spot
                        if spot:
                            pg.mouse.click(spot[0], spot[1])
                            time.sleep(0.9)
                        rec["focus_after_blank"] = ev(FOCUS_JS)
                        ev(CLEAR_JS)
                    c = ev(CENTER_JS, nid)
                    if not c:
                        rec["verdict"] = "前置态没成立：算不出节点中心"
                        res["runs"].append(rec)
                        print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                        continue
                    rec["hit"] = ev(HIT_JS, c)
                    rec["focus_before_node_click"] = ev(FOCUS_JS)
                    pg.mouse.click(c[0], c[1])
                    time.sleep(1.2)
                    rec["focus_after_node_click"] = ev(FOCUS_JS)
                    rec["landing"] = classify(rec["focus_after_node_click"])
                    rec["toolbar_after"] = ev(TOOLBAR_JS)
                    rec["events"] = ev(READ_JS)
                    rec["verdict"] = "sampled"
                finally:
                    ev(RESTORE_JS)
                res["runs"].append(rec)

                e = rec.get("events") or {}
                node_mds = [m for m in e.get("md_bubble", [])
                            if m["target_in_node"]]
                hit = rec.get("hit") or {}
                print(f"\n[{seq} #{rep}] 节点 tabindex="
                      f"{(rec.get('node_tabindex') or {}).get('tabindex')!r}"
                      f"  坐标落点 tag={hit.get('tag')!r}"
                      f" tabIndexProp={hit.get('tabIndexProp')!r}")
                print(f"   点节点前焦点="
                      f"{rec['focus_before_node_click']['aria']!r}"
                      f"/{rec['focus_before_node_click']['text']!r}")
                print(f"   点节点后落点：{rec['landing']}  焦点="
                      f"{rec['focus_after_node_click']['aria']!r}"
                      f"/{rec['focus_after_node_click']['text']!r}")
                print(f"   mousedown 冒泡阶段被 preventDefault="
                      f"{[m['defaultPrevented'] for m in node_mds]}")
                print(f"   focusin 次数={len(e.get('focusins', []))}")
                for f in e.get("focusins", []):
                    print(f"      focusin → {f['tag']}/aria={f['aria']!r}"
                          f" 在节点内={f['in_node']} 是画布根={f['is_canvas_root']}")
                for f in e.get("focuses", []):
                    tg = f["target"]
                    print(f"      focus() 目标={tg['tag']}/aria={tg['aria']!r}"
                          f"/{tg['text']!r} 在节点内={tg['in_node']}"
                          f" 是画布根={tg['is_canvas_root']}"
                          f" 当时已是焦点={tg['already_active']}")
                for bb in e.get("blurs", []):
                    tg = bb["target"]
                    print(f"      blur() 目标={tg['tag']}/aria={tg['aria']!r}"
                          f" 在节点内={tg['in_node']}")
        summ = {}
        for seq in ("A_blank_then_node", "B_node_directly"):
            rs = [r for r in res["runs"] if r["seq"] == seq and r.get("landing")]
            summ[seq] = {
                "landings": [r["landing"] for r in rs],
                "focusin_n": [len((r.get("events") or {}).get("focusins", []))
                              for r in rs],
                "focus_targets": [[
                    (f["target"]["aria"] or f["target"]["text"]
                     or f["target"]["tag"])
                    + ("(已是焦点)" if f["target"]["already_active"] else "")
                    for f in (r.get("events") or {}).get("focuses", [])]
                    for r in rs],
            }
        res["summary"] = summ
        print("\n== 汇总（复刻侧）==")
        for seq, s in summ.items():
            print(f"  {seq}")
            print(f"    落点={s['landings']}")
            print(f"    focusin 次数={s['focusin_n']}")
            print(f"    focus() 调用的目标={s['focus_targets']}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
