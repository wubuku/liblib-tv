#!/usr/bin/env python3
"""batch 890b 源站探针：修 890 的**判据缺陷**，并把「谁把焦点 focus 到哪」记全。

## 890 的判据缺陷（自己抓到的）

890 在 `document` 上用**捕获阶段**监听 `mousedown` 然后读
`e.defaultPrevented`，两条序列都读到 `False`。**这个读法是坏的**：

捕获阶段是最早跑的，此刻**还没有任何 handler 执行过**（除了更早的捕获
监听器），所以 `defaultPrevented` **必然**是 `false` —— 它**恒真为假**，
不是「源站没 preventDefault」的证据。

⇒ 要读「有没有被 preventDefault」，必须挂在**冒泡阶段**（`capture=false`）
的 `document` 上：那时所有节点的 handler 都跑完了，读数才有意义。这与 876c「错判据不许悄悄改掉」同族：**判据坏了要修判据并留痕，
不许把坏判据的读数当结论。**

## 890 那批**有效**的读数（focusin 是被动观察，没有这个缺陷）

| 序列 | 点节点前焦点 | 点节点后落点 | `focusin` 次数 |
|---|---|---|---|
| A 先点空白再点节点 | `Canvas`（画布） | **画布** | **0** |
| B 直接点节点 | `音频`（那个按钮） | **节点本体** | **2** |

⇒ A 里点击节点**整个过程焦点一次都没动过**；B 里移动了两次。
而 890 记到源站代码（栈里的 `r5`）在两条序列里都调了**恰好 1 次**
`focus()`，栈**完全相同** ⇒ 「谁调 focus」**不能**解释这个差异。

## 这批要补的三样

1. `defaultPrevented` 改在**冒泡阶段**读（修判据）
2. `focus()` 调用记录**目标元素身份**（tag/class/testid/在不在节点里）——
   890 只记了「在节点里吗」和栈，**不足以**说清 focus 到了哪
3. `focusin` 目标记**完整身份**，不只记 `in_node` 布尔

## 诊断动作不许留痕

劫持的 prototype 与事件监听都在 `finally` 里还原/摘除（882 的规矩）。

## 每段序列都从**干净起点**建立

序列 B 必须在 reload 之后做，否则量到的不是「直接点」。

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe890b_nodefocus_why2_src.py
"""

import json

OUT = "/tmp/b890b-src-nodefocus-why2.json"
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
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
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️ 那个坐标**落点是谁** —— 决定「浏览器会把焦点移到哪」。
# 890 没记这条，而它很可能就是答案的一半（点中的也许不是 tabindex=0 的
# 那个元素本身，而是某个不可聚焦的后代）。
HIT_JS = """(xy) => {
  const e = document.elementFromPoint(xy[0], xy[1]);
  if (!e) return {none: true};
  const chain = [];
  let n = e;
  for (let i = 0; i < 6 && n; i++) {
    chain.push({tag: n.tagName, cls: (n.className || '').toString().slice(0, 60),
                tabindex: n.getAttribute('tabindex'),
                tabIndexProp: n.tabIndex,
                contenteditable: n.getAttribute('contenteditable'),
                testid: n.getAttribute('data-testid')});
    n = n.parentElement;
  }
  return {tag: e.tagName, cls: (e.className || '').toString().slice(0, 80),
          tabindex: e.getAttribute('tabindex'),
          tabIndexProp: e.tabIndex, chain};
}"""

# ⚠️⚠️ `defaultPrevented` 必须在**冒泡阶段**读（890 的判据缺陷）
INSTALL_JS = """() => {
  const w = window.__b890b = {md_bubble: [], md_capture: [],
                              focusins: [], focuses: [], blurs: []};
  w.onMdBubble = (e) => { w.md_bubble.push({
      target_in_node: !!(e.target.closest && e.target.closest(
        '.react-flow__node-audio')),
      target_cls: (e.target.className || '').toString().slice(0, 60),
      // 冒泡到 document 时，所有 handler 都跑完了 —— 这才是有意义的读数
      defaultPrevented: e.defaultPrevented}); };
  w.onMdCapture = (e) => { w.md_capture.push({
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { const t = e.target;
    w.focusins.push({tag: t.tagName,
                     cls: (t.className || '').toString().slice(0, 60),
                     aria: t.getAttribute('aria-label') || '',
                     testid: t.getAttribute('data-testid'),
                     in_node: !!(t.closest && t.closest(
                       '.react-flow__node-audio')),
                     is_canvas_root: !!(t.closest && t.closest(
                       '.react-flow') && !t.closest('.react-flow__node'))}); };
  document.addEventListener('mousedown', w.onMdCapture, true);
  document.addEventListener('mousedown', w.onMdBubble, false);
  document.addEventListener('focusin', w.onFi, true);
  w.origFocus = HTMLElement.prototype.focus;
  w.origBlur = HTMLElement.prototype.blur;
  w.who = (el) => { try { return (new Error()).stack.split('\\n').slice(2, 5)
      .map(s => s.trim()).join(' | ').slice(0, 260); } catch (x) { return '?'; } };
  w.ident = (el) => ({tag: el.tagName,
      cls: (el.className || '').toString().slice(0, 60),
      aria: el.getAttribute('aria-label') || '',
      testid: el.getAttribute('data-testid'),
      in_node: !!(el.closest && el.closest('.react-flow__node-audio')),
      is_canvas_root: !!(el.closest && el.closest(
        '.react-flow') && !el.closest('.react-flow__node')),
      already_active: document.activeElement === el});
  HTMLElement.prototype.focus = function (...a) {
    try { w.focuses.push({target: w.ident(this), who: w.who(this)}); } catch (x) {}
    return w.origFocus.apply(this, a);
  };
  HTMLElement.prototype.blur = function (...a) {
    try { w.blurs.push({target: w.ident(this), who: w.who(this)}); } catch (x) {}
    return w.origBlur.apply(this, a);
  };
  return true;
}"""

READ_JS = """() => { const w = window.__b890b;
  if (!w) return null;
  return {md_bubble: w.md_bubble, md_capture: w.md_capture,
          focusins: w.focusins, focuses: w.focuses, blurs: w.blurs}; }"""

CLEAR_JS = """() => { const w = window.__b890b;
  if (!w) return false;
  w.md_bubble = []; w.md_capture = []; w.focusins = [];
  w.focuses = []; w.blurs = []; return true; }"""

RESTORE_JS = """() => { const w = window.__b890b;
  if (!w) return false;
  document.removeEventListener('mousedown', w.onMdCapture, true);
  document.removeEventListener('mousedown', w.onMdBubble, false);
  document.removeEventListener('focusin', w.onFi, true);
  if (w.origFocus) HTMLElement.prototype.focus = w.origFocus;
  if (w.origBlur) HTMLElement.prototype.blur = w.origBlur;
  delete window.__b890b; return true; }"""

NODE_TABINDEX_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  return {tag: n.tagName, tabindex: n.getAttribute('tabindex'),
          tabIndexProp: n.tabIndex,
          cls: (n.className || '').toString().slice(0, 80)}; }"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def classify(f):
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("is_canvas_root"):
        return "画布"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


def find_audio_node():
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
            return new[0]
    return None


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {}
page.goto(URL, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    runs = []
    try:
        for rep in range(1, REPS + 1):
            for seq in ("A_blank_then_node", "B_node_directly"):
                rec = {"rep": rep, "seq": seq}
                page.goto(URL, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(9000)
                page.set_viewport_size({"width": 1512, "height": 1200})
                page.wait_for_timeout(2000)
                tid = find_audio_node()
                if not tid:
                    rec["verdict"] = "前置态没成立：插不进音频节点"
                    runs.append(rec)
                    print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                    continue

                ev(INSTALL_JS)
                try:
                    rec["node_tabindex"] = ev(NODE_TABINDEX_JS, tid)
                    if seq == "A_blank_then_node":
                        spot = ev(BLANK_JS)
                        rec["blank_spot"] = spot
                        if spot:
                            page.mouse.click(spot[0], spot[1])
                            page.wait_for_timeout(900)
                        rec["focus_after_blank"] = ev(FOCUS_JS)
                        ev(CLEAR_JS)   # 空白那一下的读数不算进「点节点」这段
                    c = ev(CENTER_JS, tid)
                    if not c:
                        rec["verdict"] = "前置态没成立：算不出节点中心"
                        runs.append(rec)
                        print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                        continue
                    # ⚠️ 新增：那个坐标**点中的到底是谁**
                    rec["hit"] = ev(HIT_JS, c)
                    rec["focus_before_node_click"] = ev(FOCUS_JS)
                    page.mouse.click(c[0], c[1])
                    page.wait_for_timeout(1200)
                    rec["focus_after_node_click"] = ev(FOCUS_JS)
                    rec["landing"] = classify(rec["focus_after_node_click"])
                    rec["toolbar_after"] = ev(TOOLBAR_JS)
                    rec["events"] = ev(READ_JS)
                    rec["verdict"] = "sampled"
                finally:
                    ev(RESTORE_JS)
                runs.append(rec)

                e = rec.get("events") or {}
                node_mds = [m for m in e.get("md_bubble", [])
                            if m["target_in_node"]]
                rec["md_bubble_prevented"] = (
                    [m["defaultPrevented"] for m in node_mds] or None)
                rec["md_capture_prevented"] = [
                    m["defaultPrevented"] for m in e.get("md_capture", [])]
                hit = rec.get("hit") or {}
                print(f"\n[{seq} #{rep}] 节点 tabindex="
                      f"{(rec.get('node_tabindex') or {}).get('tabindex')!r}"
                      f"  坐标落点 tag={hit.get('tag')!r}"
                      f" tabIndexProp={hit.get('tabIndexProp')!r}")
                if hit.get("chain"):
                    for i, cch in enumerate(hit["chain"][:3]):
                        print(f"    落点往上 {i}: {cch['tag']}"
                              f" tabindex={cch['tabindex']!r}"
                              f" tabIndexProp={cch['tabIndexProp']!r}"
                              f" cls={cch['cls']!r}")
                print(f"   点节点前焦点："
                      f"{rec['focus_before_node_click']['aria']!r}")
                print(f"   点节点后落点：{rec['landing']}  焦点="
                      f"{rec['focus_after_node_click']['aria']!r}")
                print(f"   ⚠️ mousedown 冒泡阶段 defaultPrevented="
                      f"{rec['md_bubble_prevented']}"
                      f"  （捕获阶段={rec['md_capture_prevented']}，恒假）")
                print(f"   focusin 次数={len(e.get('focusins', []))}")
                for f in e.get("focusins", []):
                    print(f"      focusin → {f['tag']}"
                          f"/aria={f['aria']!r} 在节点内={f['in_node']}"
                          f" 是画布根={f['is_canvas_root']}")
                for f in e.get("focuses", []):
                    t = f["target"]
                    print(f"      focus() 目标={t['tag']}/aria={t['aria']!r}"
                          f" 在节点内={t['in_node']} 是画布根={t['is_canvas_root']}"
                          f" 当时已是焦点={t['already_active']}")
                for b in e.get("blurs", []):
                    t = b["target"]
                    print(f"      blur() 目标={t['tag']}/aria={t['aria']!r}"
                          f" 在节点内={t['in_node']}")
    finally:
        ev(RESTORE_JS)

    out["runs"] = runs
    summ = {}
    for seq in ("A_blank_then_node", "B_node_directly"):
        rs = [r for r in runs if r["seq"] == seq and r.get("landing")]
        summ[seq] = {
            "landings": [r["landing"] for r in rs],
            "md_bubble_prevented": [r.get("md_bubble_prevented") for r in rs],
            "focusin_n": [len((r.get("events") or {}).get("focusins", []))
                          for r in rs],
            "focus_targets": [[f["target"]["aria"] or f["target"]["tag"]
                               for f in (r.get("events") or {}).get("focuses", [])]
                              for r in rs],
        }
    out["summary"] = summ
    print("\n== 汇总 ==")
    for seq, s in summ.items():
        print(f"  {seq}")
        print(f"    落点={s['landings']}")
        print(f"    mousedown 冒泡阶段被 preventDefault={s['md_bubble_prevented']}")
        print(f"    focusin 次数={s['focusin_n']}")
        print(f"    focus() 调用的目标={s['focus_targets']}")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
