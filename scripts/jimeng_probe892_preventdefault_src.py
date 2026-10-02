#!/usr/bin/env python3
"""batch 892 源站探针：**派发结束后**再读 `defaultPrevented` —— 钉死 891 收窄出的唯一候选。

## 891 把候选收窄到一个

891 的最小复现（六格各 2/2）证明：
- 「焦点在落点的可聚焦祖先内 ⇒ 浏览器不移动焦点」—— **证伪**
- **只有 `preventDefault()`** 能阻止浏览器移动焦点；`stopPropagation()` 挡不住

而 890b 把监听挂在 `document` 的**冒泡阶段**，读数是**空数组**（事件**没冒泡
到 document**）⇒ 有人在**中途**处理了它。⇒ 源站很可能
**`preventDefault()` + `stopPropagation()` 两件都做了**。

## 为什么之前读不到

不是「没有」，是**读的时候太早**：

| 阶段 | 读到的是什么 |
|---|---|
| 捕获阶段（`document`） | 此刻**还没有任何 handler 跑过** ⇒ **恒真为假**（890 的错） |
| 冒泡阶段（`document`） | 事件**根本没到** `document` ⇒ **读不到**（890b） |

## 这批的取法：保存**事件对象引用**，事后读

事件对象在派发**结束之后仍然存在**，且它的 `defaultPrevented` 保留**最终
值**。所以：

1. 在 `document` 的**捕获阶段**只做一件事：`w.saved = e`（存引用）
2. 点完、等事件派发**彻底结束**（`setTimeout` + 一帧）
3. 再读 `w.saved.defaultPrevented`

⇒ 这样**与 handler 跑没跑完无关**，读到的是**最终**状态。

⚠️ 同时保留三个**互相独立**的读数，免得只靠一个：
- `defaultPrevented`（捕获阶段存引用、事后读）← **本批的主角**
- `document` 冒泡阶段**有没有收到**事件（`stopPropagation` 的证据）
- `focusin` 次数（焦点到底动不动）—— 与 889/890 的读数**对齐**

## 每段序列都从**干净起点**建立

序列 B 必须在 reload 之后做，否则量到的不是「直接点」。

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe892_preventdefault_src.py
"""

import json

OUT = "/tmp/b892-src-preventdefault.json"
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

# ⚠️ 主角：捕获阶段**只存引用**，不读值
INSTALL_JS = """() => {
  const w = window.__b892 = {saved: null, savedAt: null,
                             bubble_at_doc: [], focusins: [],
                             node_saw_mousedown: 0};
  w.onCap = (e) => { if (!w.saved) { w.saved = e; w.savedAt = Date.now(); } };
  w.onBub = (e) => { w.bubble_at_doc.push({
      id: e.target.id || e.target.tagName,
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { w.focusins.push(
      e.target.getAttribute('aria-label') || e.target.tagName); };
  w.onNode = () => { w.node_saw_mousedown += 1; };
  document.addEventListener('mousedown', w.onCap, true);
  document.addEventListener('mousedown', w.onBub, false);
  document.addEventListener('focusin', w.onFi, true);
  return true;
}"""

# 派发**结束之后**才读 —— 这才是本批与 890/890b 的区别
READ_JS = """() => {
  const w = window.__b892;
  if (!w) return null;
  const s = w.saved;
  return {
    saved_exists: !!s,
    saved_type: s ? s.type : null,
    saved_target: s ? (s.target.id || s.target.tagName
                       || (s.target.className || '').toString().slice(0, 40))
                    : null,
    // ↓↓↓ 本批的主角：事后读，拿到的是**最终**值 ↓↓↓
    defaultPrevented_final: s ? s.defaultPrevented : null,
    bubbles: s ? s.bubbles : null,
    cancelBubble_final: s ? s.cancelBubble : null,
    // 独立读数：document 冒泡阶段有没有收到（= stopPropagation 的证据）
    bubble_at_doc: w.bubble_at_doc,
    focusins: w.focusins,
    node_saw_mousedown: w.node_saw_mousedown,
  };
}"""

RESTORE_JS = """() => { const w = window.__b892;
  if (!w) return false;
  document.removeEventListener('mousedown', w.onCap, true);
  document.removeEventListener('mousedown', w.onBub, false);
  document.removeEventListener('focusin', w.onFi, true);
  delete window.__b892; return true; }"""

CLEAR_JS = """() => { const w = window.__b892;
  if (!w) return false;
  w.saved = null; w.savedAt = null; w.bubble_at_doc = [];
  w.focusins = []; w.node_saw_mousedown = 0; return true; }"""


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


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")


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
                    if seq == "A_blank_then_node":
                        spot = ev(BLANK_JS)
                        rec["blank_spot"] = spot
                        if spot:
                            page.mouse.click(spot[0], spot[1])
                            page.wait_for_timeout(900)
                        rec["focus_after_blank"] = ev(FOCUS_JS)
                        ev(CLEAR_JS)
                    c = ev(CENTER_JS, tid)
                    if not c:
                        rec["verdict"] = "前置态没成立：算不出节点中心"
                        runs.append(rec)
                        print(f"  !! [{seq} #{rep}] {rec['verdict']}")
                        continue
                    rec["focus_before_node_click"] = ev(FOCUS_JS)
                    page.mouse.click(c[0], c[1])
                    # ⚠️ 等事件派发**彻底结束**再读：多给几帧
                    page.wait_for_timeout(1500)
                    rec["focus_after_node_click"] = ev(FOCUS_JS)
                    rec["landing"] = classify(rec["focus_after_node_click"])
                    rec["toolbar_after"] = ev(TOOLBAR_JS)
                    rec["read"] = ev(READ_JS)
                    rec["verdict"] = "sampled"
                finally:
                    ev(RESTORE_JS)
                runs.append(rec)

                r = rec.get("read") or {}
                print(f"\n[{seq} #{rep}]")
                print(f"   点节点前焦点={rec['focus_before_node_click']['aria']!r}"
                      f"  点后落点={rec['landing']}")
                print(f"   ⭐ defaultPrevented（**事后读**）="
                      f"{r.get('defaultPrevented_final')}"
                      f"   bubbles={r.get('bubbles')}"
                      f"   cancelBubble={r.get('cancelBubble_final')}")
                print(f"   存到的事件：{r.get('saved_type')!r}  target="
                      f"{r.get('saved_target')!r}")
                print(f"   document 冒泡阶段收到={r.get('bubble_at_doc')}")
                print(f"   focusin={r.get('focusins')}")
    finally:
        ev(RESTORE_JS)

    out["runs"] = runs
    summ = {}
    for seq in ("A_blank_then_node", "B_node_directly"):
        rs = [r for r in runs if r["seq"] == seq and r.get("read")]
        summ[seq] = {
            "defaultPrevented_final": [(r.get("read") or {}).get(
                "defaultPrevented_final") for r in rs],
            "bubble_at_doc_n": [len((r.get("read") or {}).get(
                "bubble_at_doc", [])) for r in rs],
            "focusin_n": [len((r.get("read") or {}).get("focusins", []))
                          for r in rs],
            "landings": [r.get("landing") for r in rs],
        }
    out["summary"] = summ
    print("\n== 汇总 ==")
    for seq, s in summ.items():
        print(f"  {seq}")
        print(f"    ⭐ defaultPrevented（事后读）={s['defaultPrevented_final']}")
        print(f"    document 冒泡收到次数={s['bubble_at_doc_n']}")
        print(f"    focusin 次数={s['focusin_n']}")
        print(f"    落点={s['landings']}")
    dp = summ["A_blank_then_node"]["defaultPrevented_final"]
    out["verdict"] = ("892 结论：A 序列 defaultPrevented="
                      f"{dp} ⇒ 源站"
                      + ("**确实 preventDefault 了**" if dp and all(x is True for x in dp)
                         else ("**没** preventDefault" if dp and all(x is False for x in dp)
                               else "读数不齐/为空，**不能下结论**")))
    print(f"\n== {out['verdict']} ==")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
