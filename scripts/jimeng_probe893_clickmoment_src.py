#!/usr/bin/env python3
"""batch 893 源站探针：**点击那一刻**节点发生了什么？（§103 那个矛盾的下一个假设）

## 矛盾（原样摆着）

1. 891 的 C1（空白页最小复现 2/2）：焦点在落点的**可聚焦祖先**上、点一个
   **不可聚焦后代** ⇒ 浏览器**会**把焦点移到可聚焦子元素。
2. 源站结构与 C1 **完全一样**（焦点=画布根 `tabindex='0'`、落点=节点里的
   `svg`/tabIndex=-1、节点 `tabindex='0'`），A 序列却 `focusin` **0** 次。
3. 892 又证明源站**没有** `preventDefault`。

⇒ 「会移动」与「没移动且没被阻止」**不可能同时成立**。

## §103 猜的是「tabindex 被移除」。这批加一个**更具体**的候选

浏览器的默认动作是「把焦点移到 **mousedown 目标**的最近可聚焦祖先」。**如果
那个 target 在默认动作发生时已经不在文档里了，就没有任何可聚焦祖先可移动**
—— 这会**同时**满足上面三条，而且**不需要** `preventDefault`。

⇒ 候选：**mousedown 期间 React 重渲染，把节点（或落点）从 DOM 上换掉了。**

## 这批测的（每样都独立，别只靠一个）

1. **落点 target 与节点在派发结束后还 `isConnected` 吗** —— 直接测「浏览器
   面对的 target 还在不在文档里」
2. **`MutationObserver`** 挂在节点上，记 `attributes`（尤其 `tabindex`）与
   `childList` 的变化，并带**相对 mousedown 的时间差**
3. **节点的 `tabindex` 在点击前 / 点击后各是多少**（§103 的原假设）
4. **`focusin` 次数**（与 889/890/892 对齐，三跑以上交叉验证）
5. **`document` 冒泡阶段有没有收到**（stopPropagation 的间接读数）

⚠️ 890/892 的教训：**读数取不到时要先怀疑自己的判据**。所以每项都独立记，
并且**打印出来**，不靠单个读数下结论。

## 序列定义（与 889/890/892 **同款**，便于交叉对齐）

- **A**：点空白（焦点落画布）→ 点节点中心 → 读数
- **B**：直接点节点中心 → 读数

B 必须在 **reload 之后**做。

## 诊断动作不许留痕

监听与 `MutationObserver` 都在 `finally` 里断开。

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe893_clickmoment_src.py
"""

import json

OUT = "/tmp/b893-src-clickmoment.json"
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

NODE_TABINDEX_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {no_node: true};
  return {tabindex: n.getAttribute('tabindex'), tabIndexProp: n.tabIndex,
          is_connected: n.isConnected};
}"""

# ⚠️ 捕获阶段：只**存引用**（落点 target + 它最近的节点 + 节点的 tabindex），
# 一律**不读值**当结论 —— 值留到派发结束后再读
INSTALL_JS = """(tid) => {
  const w = window.__b893 = {savedTarget: null, savedNode: null,
                             tabindex_at_mousedown: null, t0: 0,
                             mutations: [], bubble_at_doc: [], focusins: []};
  const node = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  w.savedNodeRef = node;
  if (node) {
    w.mo = new MutationObserver((list) => {
      for (const m of list) {
        w.mutations.push({
          dt: Date.now() - w.t0,
          type: m.type,
          attr: m.attributeName,
          old: m.oldValue,
          now: node.getAttribute(m.attributeName || ''),
          added: m.addedNodes ? m.addedNodes.length : 0,
          removed: m.removedNodes ? m.removedNodes.length : 0});
      }
    });
    w.mo.observe(node, {attributes: true, attributeOldValue: true,
                        childList: true, subtree: true});
  }
  w.onCap = (e) => {
    if (w.savedTarget) return;              // 只记第一次
    w.t0 = Date.now();
    w.savedTarget = e.target;
    const n = e.target.closest && e.target.closest('.react-flow__node-audio');
    w.savedNode = n;
    w.node_tabindex_attr = n ? n.getAttribute('tabindex') : null;
    w.node_tabIndexProp = n ? n.tabIndex : null;
    w.target_id = e.target.id || e.target.tagName;
  };
  w.onBub = (e) => { w.bubble_at_doc.push({
      id: e.target.id || e.target.tagName,
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { w.focusins.push(
      e.target.getAttribute('aria-label') || e.target.tagName); };
  document.addEventListener('mousedown', w.onCap, true);
  document.addEventListener('mousedown', w.onBub, false);
  document.addEventListener('focusin', w.onFi, true);
  return true;
}"""

# 派发**结束之后**才读 —— 与 892 同款取法
READ_JS = """(tid) => {
  const w = window.__b893;
  if (!w) return null;
  const t = w.savedTarget, n = w.savedNode;
  const cur = document.querySelector(
    `.react-flow__node[data-testid="${tid}"]`);
  return {
    target: w.target_id || null,
    // ↓↓↓ 主角：默认动作发生时，浏览器面对的 target / 节点还在文档里吗
    target_is_connected: t ? t.isConnected : null,
    node_is_connected: n ? n.isConnected : null,
    same_node_still_in_dom: !!(n && cur && n === cur),
    // 节点 tabindex：mousedown 时 vs 派发结束后
    tabindex_at_mousedown: w.node_tabindex_attr,
    tabIndexProp_at_mousedown: w.node_tabIndexProp,
    tabindex_now: cur ? cur.getAttribute('tabindex') : '(节点不在 DOM)',
    tabIndexProp_now: cur ? cur.tabIndex : null,
    mutations: w.mutations,
    bubble_at_doc: w.bubble_at_doc,
    focusins: w.focusins,
  };
}"""

RESTORE_JS = """() => { const w = window.__b893;
  if (!w) return false;
  document.removeEventListener('mousedown', w.onCap, true);
  document.removeEventListener('mousedown', w.onBub, false);
  document.removeEventListener('focusin', w.onFi, true);
  if (w.mo) w.mo.disconnect();
  delete window.__b893; return true; }"""

CLEAR_JS = """() => { const w = window.__b893;
  if (!w) return false;
  w.savedTarget = null; w.savedNode = null; w.mutations = [];
  w.bubble_at_doc = []; w.focusins = []; w.t0 = 0; return true; }"""


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

                ev(INSTALL_JS, tid)
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
                    rec["tabindex_before_click"] = ev(NODE_TABINDEX_JS, tid)
                    rec["focus_before_node_click"] = ev(FOCUS_JS)
                    page.mouse.click(c[0], c[1])
                    page.wait_for_timeout(1500)   # 等派发彻底结束
                    rec["focus_after_node_click"] = ev(FOCUS_JS)
                    rec["landing"] = classify(rec["focus_after_node_click"])
                    rec["toolbar_after"] = ev(TOOLBAR_JS)
                    rec["read"] = ev(READ_JS, tid)
                    rec["verdict"] = "sampled"
                finally:
                    ev(RESTORE_JS)
                runs.append(rec)

                r = rec.get("read") or {}
                print(f"\n[{seq} #{rep}] 点前 tabindex="
                      f"{(rec.get('tabindex_before_click') or {}).get('tabindex')!r}"
                      f"  点后落点={rec['landing']}")
                print(f"   ⭐ 落点 target={r.get('target')!r} "
                      f"**isConnected**={r.get('target_is_connected')}")
                print(f"   ⭐ 节点 **isConnected**={r.get('node_is_connected')}"
                      f"  同一个节点还在 DOM={r.get('same_node_still_in_dom')}")
                print(f"   tabindex: mousedown 时="
                      f"{r.get('tabindex_at_mousedown')!r}"
                      f"/tabIndexProp={r.get('tabIndexProp_at_mousedown')}"
                      f"  → 派发后={r.get('tabindex_now')!r}"
                      f"/tabIndexProp={r.get('tabIndexProp_now')}")
                muts = r.get("mutations") or []
                print(f"   MutationObserver 记到 {len(muts)} 条：")
                for m in muts[:6]:
                    print(f"      dt={m['dt']}ms {m['type']} "
                          f"attr={m['attr']!r} old={m['old']!r} "
                          f"now={m['now']!r} +{m['added']}/-{m['removed']}")
                print(f"   document 冒泡收到={r.get('bubble_at_doc')}")
                print(f"   focusin={r.get('focusins')}")
    finally:
        ev(RESTORE_JS)

    out["runs"] = runs
    summ = {}
    for seq in ("A_blank_then_node", "B_node_directly"):
        rs = [r for r in runs if r["seq"] == seq and r.get("read")]
        summ[seq] = {
            "target_is_connected": [(r["read"] or {}).get(
                "target_is_connected") for r in rs],
            "node_is_connected": [(r["read"] or {}).get(
                "node_is_connected") for r in rs],
            "same_node": [(r["read"] or {}).get(
                "same_node_still_in_dom") for r in rs],
            "tabindex_mousedown": [(r["read"] or {}).get(
                "tabindex_at_mousedown") for r in rs],
            "tabindex_after": [(r["read"] or {}).get(
                "tabindex_now") for r in rs],
            "n_mutations": [len((r["read"] or {}).get("mutations", []))
                            for r in rs],
            "focusin_n": [len((r["read"] or {}).get("focusins", []))
                          for r in rs],
            "landings": [r.get("landing") for r in rs],
        }
    out["summary"] = summ
    print("\n== 汇总 ==")
    for seq, s in summ.items():
        print(f"  {seq}")
        for k, v in s.items():
            print(f"    {k} = {v}")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
