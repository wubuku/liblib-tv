#!/usr/bin/env python3
"""batch 890 源站探针：点节点**抢不抢焦点**，为什么**取决于有没有点过空白**？

⛔⛔⛔ **批 890b 判定：本探针的 `defaultPrevented` 读数作废，不许当证据。**

本探针把它挂在 `document` 的**捕获阶段**读，而捕获阶段是最早跑的 ——
那一刻**还没有任何 handler 执行过**（除了更早的捕获监听器），所以
`defaultPrevented` **必然**是 `false`：**恒真为假**，它**不是**
「源站没 preventDefault」的证据。890b 已把它改到**冒泡阶段**。

⚠️ 但要留意：**890b 也没读到**（`document` 冒泡监听**没收到该事件**，
读数是空数组，疑似被 `stopPropagation()`）⇒「源站有没有 preventDefault」
**至今没测到**，890 和 890b 的这一格都**不能**用来下结论。

**这个探针仍然有效的读数**（它们不依赖那条坏判据）：
- 序列 A 的 `focusin` 次数 **0**、序列 B 次数 **2**
- 源站代码（栈里的 `r5`）在两条序列里都调 `focus()`，目标**都是画布根**
- 节点 `tabindex='0'`

## 889 留下的那条差异（两边各 2/2，机制未查明）

| | 点空白 → 再点节点中心之后，焦点在哪 |
|---|---|
| 源站（889c） | **留在画布**（`aria='Canvas'`） |
| 复刻（889b_ck） | **被节点抢走** |

而且源站有个反直觉的补充（889b `pure_mouse` 2/2）：**不**点空白、
**直接**点节点时，焦点**会**到节点上。

⇒ 「点节点抢不抢焦点」在源站**取决于之前有没有点过空白**。这批查**为什么**。

## 两个候选机制，各有各的判据

**候选 ①：节点上的 `mousedown` 被 `preventDefault()` 了。**
浏览器的规则是：mousedown 的默认行为包含「把焦点移到目标最近的可聚焦
祖先」。一旦被 `preventDefault()`，**默认的焦点移动就不会发生** ⇒
焦点留在原处。
⇒ 判据：在 `document` 上用**捕获阶段**监听 `mousedown`，读
`e.defaultPrevented`。序列 A（先点空白）若为 `true` 而序列 B（直接点）为
`false`，就**证成**候选 ①。

**候选 ②：有人主动调了 `focus()` / `blur()`。**
⇒ 判据：劫持 `HTMLElement.prototype.focus` 与 `blur`，记下调用栈
（882 用过这招），看是谁在动焦点。**没有栈**就说明焦点是**浏览器原生**
移动的（回到候选 ① 那侧）。

⚠️ 两个候选**可能同时成立**，也可能**都不成立**（第三种：节点上的
`tabindex` 在两条序列里不一样）。所以**每条读数都单独记**，
不许先有结论再找证据。

## 诊断动作不许留痕（882 的规矩）

- 劫持的 prototype **每段测完自己还原**（`finally` 里恢复）
- 事件监听用一次性函数、测完 `removeEventListener`
- 中途 reload 也算恢复手段

## 每段序列都要**从干净起点**建立

序列 B（直接点节点）必须在 **reload 之后**做 —— 否则序列 A 已经把状态
改过了，量到的就不是「直接点」。

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe890_nodefocus_why_src.py
"""

import json

OUT = "/tmp/b890-src-nodefocus-why.json"
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

# 装监听：捕获阶段读 mousedown 有没有被 preventDefault；记录 focusin 目标
INSTALL_JS = """() => {
  const w = window.__b890 = {mousedowns: [], focusins: [], focuses: [], blurs: []};
  w.onMd = (e) => { w.mousedowns.push({
      target_in_node: !!(e.target.closest && e.target.closest(
        '.react-flow__node-audio')),
      target_cls: (e.target.className || '').toString().slice(0, 60),
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { w.focusins.push({
      tag: e.target.tagName,
      aria: e.target.getAttribute('aria-label') || '',
      in_node: !!(e.target.closest && e.target.closest(
        '.react-flow__node-audio'))}); };
  document.addEventListener('mousedown', w.onMd, true);
  document.addEventListener('focusin', w.onFi, true);
  // 劫持 focus / blur 记调用栈（候选 ②）
  w.origFocus = HTMLElement.prototype.focus;
  w.origBlur = HTMLElement.prototype.blur;
  HTMLElement.prototype.focus = function (...a) {
    try { w.focuses.push({who: (new Error()).stack.split('\\n').slice(1, 5)
        .map(s => s.trim()).join(' | ').slice(0, 300),
        on_in_node: !!(this.closest && this.closest(
          '.react-flow__node-audio')),
        aria: this.getAttribute('aria-label') || ''}); } catch (x) {}
    return w.origFocus.apply(this, a);
  };
  HTMLElement.prototype.blur = function (...a) {
    try { w.blurs.push({who: (new Error()).stack.split('\\n').slice(1, 5)
        .map(s => s.trim()).join(' | ').slice(0, 300),
        on_in_node: !!(this.closest && this.closest(
          '.react-flow__node-audio'))}); } catch (x) {}
    return w.origBlur.apply(this, a);
  };
  return true;
}"""

READ_JS = """() => {
  const w = window.__b890;
  if (!w) return null;
  return {mousedowns: w.mousedowns, focusins: w.focusins,
          focuses: w.focuses, blurs: w.blurs};
}"""

# 还原：诊断动作不许留痕
RESTORE_JS = """() => {
  const w = window.__b890;
  if (!w) return false;
  document.removeEventListener('mousedown', w.onMd, true);
  document.removeEventListener('focusin', w.onFi, true);
  if (w.origFocus) HTMLElement.prototype.focus = w.origFocus;
  if (w.origBlur) HTMLElement.prototype.blur = w.origBlur;
  delete window.__b890;
  return true;
}"""

# 清空缓冲（序列之间互不污染）
CLEAR_JS = """() => { const w = window.__b890;
  if (!w) return false;
  w.mousedowns = []; w.focusins = []; w.focuses = []; w.blurs = [];
  return true; }"""

NODE_TABINDEX_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  return {tag: n.tagName, tabindex: n.getAttribute('tabindex'),
          tabIndexProp: n.tabIndex,
          cls: (n.className || '').toString().slice(0, 80)};
}"""


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
    """插一个音频节点并返回它的 data-testid（判集合差分，CC.2 的教训）。"""
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
    runs = []
    tid = None
    try:
        for rep in range(1, REPS + 1):
            for seq in ("A_blank_then_node", "B_node_directly"):
                rec = {"rep": rep, "seq": seq}
                # ⚠️ 每段序列都**从干净起点**建立：B 必须在 reload 之后，
                # 否则 A 已经把状态改过了，量到的不是「直接点」。
                page.goto(
                    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
                    "64b58cd5-7b04-4312-890a-09f2d1d3399f"
                    "?enter_from=project_list&from_page=create",
                    wait_until="domcontentloaded", timeout=90000)
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
                        ev(CLEAR_JS)      # 空白那一下的读数不算进「点节点」这段
                    c = ev(CENTER_JS, tid)
                    if not c:
                        rec["verdict"] = "前置态没成立：算不出节点中心"
                        runs.append(rec)
                        print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                        continue
                    rec["focus_before_node_click"] = ev(FOCUS_JS)
                    page.mouse.click(c[0], c[1])
                    page.wait_for_timeout(1200)
                    rec["focus_after_node_click"] = ev(FOCUS_JS)
                    rec["landing"] = classify(rec["focus_after_node_click"])
                    rec["toolbar_after"] = ev(TOOLBAR_JS)
                    rec["events"] = ev(READ_JS)
                    rec["verdict"] = "sampled"
                finally:
                    ev(RESTORE_JS)     # 诊断动作不许留痕
                runs.append(rec)

                ev_ = rec.get("events") or {}
                mds = [m for m in ev_.get("mousedowns", []) if m["target_in_node"]]
                rec["node_mousedown_default_prevented"] = (
                    mds[0]["defaultPrevented"] if mds else None)
                print(f"\n[{seq} #{rep}] 节点 tabindex="
                      f"{(rec.get('node_tabindex') or {}).get('tabindex')!r}")
                print(f"   点节点前焦点：{rec['focus_before_node_click']['aria']!r}"
                      f"（落点 {classify(rec['focus_before_node_click'])}）")
                print(f"   点节点后落点：{rec['landing']}  焦点="
                      f"{rec['focus_after_node_click']['aria']!r}"
                      f"  工具条={rec['toolbar_after']}")
                print(f"   候选① 节点 mousedown 被 preventDefault = "
                      f"{rec['node_mousedown_default_prevented']}")
                fis = ev_.get("focusins", [])
                print(f"   focusin 次数={len(fis)}"
                      f"  目标={[ (f['tag'], f['in_node']) for f in fis ]}")
                print(f"   候选② focus() 调用={len(ev_.get('focuses', []))}"
                      f"  blur() 调用={len(ev_.get('blurs', []))}")
                for f in ev_.get("focuses", [])[:2]:
                    print(f"      focus ← {f['who'][:150]}")
                for b in ev_.get("blurs", [])[:2]:
                    print(f"      blur  ← {b['who'][:150]}")
    finally:
        ev(RESTORE_JS)

    out["runs"] = runs
    # 汇总：A/B 两条序列的**落点**与**mousedown 是否被 preventDefault** 各是什么
    summ = {}
    for seq in ("A_blank_then_node", "B_node_directly"):
        rs = [r for r in runs if r["seq"] == seq and r.get("landing")]
        summ[seq] = {
            "landings": [r["landing"] for r in rs],
            "default_prevented": [r.get("node_mousedown_default_prevented")
                                  for r in rs],
            "focus_before": [r["focus_before_node_click"]["aria"] for r in rs],
            "focus_calls": [len((r.get("events") or {}).get("focuses", []))
                            for r in rs],
            "blur_calls": [len((r.get("events") or {}).get("blurs", []))
                           for r in rs],
        }
    out["summary"] = summ
    print("\n== 汇总 ==")
    for seq, s in summ.items():
        print(f"  {seq:20s} 落点={s['landings']}")
        print(f"  {'':20s} 点节点前焦点={s['focus_before']}")
        print(f"  {'':20s} mousedown 被 preventDefault={s['default_prevented']}"
              f"  focus()={s['focus_calls']}  blur()={s['blur_calls']}")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
