#!/usr/bin/env python3
"""batch 899 源站探针：roving「**算下一个**」的规则是什么？到末尾**怎么绕**？

## 这一批要补的拼图

896 已经测清 roving 的**触发**（Tab/Shift+Tab 的 keydown）、**布什么**
（目标 `'0'` / 其余 `'-1'`，全画布重写）、**不** preventDefault、**此后不回撤**。

但**还差一条**：它在 keydown 里挑的「下一个节点」**是怎么算出来的**？
- 是**纯 DOM 序**（`.react-flow__node` 在 DOM 里的先后）？
- 还是跳过某些节点（没被渲染完的、被隐藏的、非画布内的）？
- **到末尾了怎么办** —— 停在最后一个？绕回第一个？还是把焦点交出画布？

⇒ **这三条不钉死就动手实现 = 照着猜的机制写代码。**（§77）

## 怎么量

复用 896 的仪器（**逐字**），从**点空白**起走（同 896 的起点），连按 Tab
**节点数 + 5** 次 —— 故意**走过一圈**，就是为了看末尾行为。每一步记：

- 这一步**被布上 `0` 的是哪个节点**（从变更流里取）
- 焦点**实际**落在哪（`focusin` 捕获阶段记的 `active_ident`）
- 全画布 `n_zero`（sanity：应该恒为 1）

然后把「**布 `0` 的顺序**」与「**节点的 DOM 顺序**」逐项比对。

## 判据纪律

- 仪器（`INSTALL_JS` / `STATE_JS`）**逐字复用 896**，不许改
- 节点总数是**易变量**（同 URL 逐轮 74→75→76→77）⇒ 按**身份**（testid）
  记 DOM 序，**不钉**绝对个数、**不钉**序号
- 每轮**重复 2 次**
- **诊断动作必须还原**（`finally` 里 disconnect + 摘监听）

## 计费边界

只按 Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe899_roving_next_rule_src.py
"""

import json

OUT = "/tmp/b899-src-roving-next-rule.json"
REPS = 2
# ⚠️ 第一版 OVERRUN=5 **不够**：81 次按压里只有 72 次真正推进了指针
# （其余 9 次是「指针没追上、原地重写同一个已有 '0' 的节点」），
# 指针只走到下标 72，**根本没走到末尾** ⇒ 「到末尾怎么绕」**没测到**。
# ⇒ 加到 25：101 次按压足以走过一圈并**真的绕回去**。
OVERRUN = 25
SETTLE_MS = 400        # Playwright 收**毫秒**（895 踩过秒/毫秒的坑）

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

DOM_ORDER_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""

# 每个节点的「身份名片」（用来**指名**被跳过/没被布过的那个是谁，而不是只报下标）
NODES_META_JS = """() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
  tid: n.getAttribute('data-testid') || '',
  kind: [...n.classList].find(c => c.startsWith('react-flow__node-')
        && c !== 'react-flow__node') || '?',
  aria: n.getAttribute('aria-label') || '',
  hidden: n.offsetParent === null,
}))"""

# ⚠️⚠️ 以下两段 **逐字来自 896 源站探针**，不许在这里「顺手优化」。
# 896 已经把 894 漏掉的**计数**（各有几个 0）补进 STATE_JS 了，别退回去。
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b899) { window.__b899.cleanup(); }
  const log = [];
  let seq = 0;
  const t0 = performance.now();

  const ident = (el) => {
    if (!el || el.nodeType !== 1) return String(el);
    const tid = el.getAttribute && el.getAttribute('data-testid');
    if (tid) return 'tid:' + tid;
    const tag = el.tagName;
    const cls = (el.className && el.className.baseVal !== undefined)
      ? el.className.baseVal : (el.className || '');
    const c = String(cls).split(/\\s+/).filter(Boolean).slice(0, 2).join('.');
    let i = 0, p = el;
    while ((p = p.previousElementSibling)) i++;
    return 'el:' + tag + (c ? '.' + c : '') + '#' + i;
  };

  const onFocusInCap = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'focusin@capture',
              target: ident(e.target),
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null,
              // ⚠️⚠️ 第一版这里写的是「target 是不是等于 activeElement」——
              // 那是**恒真**的（拿到焦点的元素按定义就成了 activeElement），
              // 看着像证据、其实**什么也没测**（896 那边 18/18 全 True 就是
              // 这个原因）。真正要问的是「落点**自己**是不是节点 wrapper」。
              target_is_node_wrapper: !!(e.target.classList
                && e.target.classList.contains('react-flow__node')),
              target_tag: e.target.tagName,
              target_aria: (e.target.getAttribute
                && e.target.getAttribute('aria-label')) || '',
              is_active: document.activeElement === e.target,
              active_ident: ident(document.activeElement)});
  };
  const onFocusOut = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'focusout',
              target: ident(e.target),
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null,
              active_ident: ident(document.activeElement)});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key,
              target: ident(e.target), ref: e});
  };
  // 派发**结束**后才读 defaultPrevented（890/892 的教训：只读捕获阶段恒为假）
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; delete rec.ref; }
  };
  document.addEventListener('focusin', onFocusInCap, true);
  document.addEventListener('focusout', onFocusOut, true);
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('keydown', onKeyEnd, false);

  const mo = new MutationObserver((recs) => {
    for (const r of recs) {
      log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
                kind: 'attr:' + r.attributeName,
                target: ident(r.target),
                oldValue: r.oldValue,
                value_at_flush: r.target.getAttribute(r.attributeName)});
    }
  });
  mo.observe(root, {attributes: true, attributeOldValue: true,
                    attributeFilter: ['tabindex'], subtree: true});

  window.__b899 = {
    log,
    dump: () => log.slice(),
    since: (seq_from) => log.filter(r => r.seq >= seq_from),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('focusout', onFocusOut, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b899;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {};
  const zeros = [];
  for (const n of nodes) {
    const ti = n.getAttribute('tabindex');
    const k = ti === null ? 'None' : ti;
    hist[k] = (hist[k] || 0) + 1;
    if (ti === '0') zeros.push(n.getAttribute('data-testid') || '(no-testid)');
  }
  const chain = [];
  let a = document.activeElement;
  for (let i = 0; a && i < 12; i++) {
    chain.push({tag: a.tagName,
                ti: a.getAttribute ? a.getAttribute('tabindex') : null,
                prop: a.tabIndex,
                aria: (a.getAttribute && a.getAttribute('aria-label')) || '',
                tid: (a.getAttribute && a.getAttribute('data-testid')) || null,
                is_node: !!(a.closest && a.closest('.react-flow__node'))});
    a = a.parentElement;
  }
  const an = document.activeElement
    && document.activeElement.closest
    && document.activeElement.closest('.react-flow__node');
  return {
    n_nodes: nodes.length,
    hist,
    zeros,
    n_zero: zeros.length,
    active: {
      aria: (document.activeElement
             && document.activeElement.getAttribute
             && document.activeElement.getAttribute('aria-label')) || '',
      tid: an ? an.getAttribute('data-testid') : null,
      node_ti: an ? an.getAttribute('tabindex') : null,
      self_ti: (document.activeElement
                && document.activeElement.getAttribute)
               ? document.activeElement.getAttribute('tabindex') : null,
    },
    chain,
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {}
page.goto(URL, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(3000)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    runs = []
    for rep in range(1, REPS + 1):
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)

        dom_order = ev(DOM_ORDER_JS)          # 按 testid 记 DOM 序
        meta = ev(NODES_META_JS)
        n = len(dom_order)
        presses = n + OVERRUN
        rec = {"rep": rep, "n_nodes_dom": n, "presses": presses,
               "dom_order": dom_order, "meta": meta, "steps": []}
        print(f"\n===== rep {rep}：DOM 序 {n} 个节点，按 {presses} 次 Tab =====")

        inst = ev(INSTALL_JS)
        rec["instrument"] = inst
        print(f"  仪器：{inst}")

        try:
            spot = ev(BLANK_JS)
            if spot:
                page.mouse.click(spot[0], spot[1])
                page.wait_for_timeout(1200)
            rec["blank_spot"] = spot
            print(f"  点空白 {spot} 后 active="
                  f"{ev(STATE_JS)['active']}")

            for i in range(1, presses + 1):
                cur = ev("() => window.__b899.cursor()")
                page.keyboard.press("Tab")
                page.wait_for_timeout(SETTLE_MS)
                st = ev(STATE_JS)
                # 这一步**新布上 0 的是谁**（只看 keydown 之后的属性变更）
                seg = ev("(f) => window.__b899.since(f)", cur)
                armed = [r for r in seg
                         if r["kind"].startswith("attr:")
                         and r["value_at_flush"] == '0'
                         and r["oldValue"] != '0']
                focusins = [r for r in seg if r["kind"] == "focusin@capture"]
                keydowns = [r for r in seg if r["kind"] == "keydown@capture"]
                dom_idx = {}
                for t in armed:
                    tid = (t["target"][4:] if t["target"].startswith("tid:")
                           else t["target"])
                    dom_idx[tid] = (dom_order.index(tid)
                                    if tid in dom_order else None)
                rec["steps"].append({
                    "i": i,
                    "zeros": st["zeros"],
                    "n_zero": st["n_zero"],
                    "n_nodes": st["n_nodes"],
                    "armed": [t["target"] for t in armed],
                    "armed_dom_idx": list(dom_idx.values()),
                    "focus_aria": st["active"]["aria"],
                    "focus_tid": st["active"]["tid"],
                    # ★ 用**真判据**：落点**自己**带不带 `react-flow__node` 类
                    "focus_lands_on_wrapper": bool(
                        focusins and focusins[-1].get("target_is_node_wrapper")),
                    "focus_lands_on_aria": (focusins[-1].get("target_aria")
                                            if focusins else None),
                    "focus_lands_on_tag": (focusins[-1].get("target_tag")
                                           if focusins else None),
                    "key_prevented": (keydowns[-1].get("default_prevented")
                                      if keydowns else None),
                })
                s = rec["steps"][-1]
                print(f"   Tab{i:<3d} 布0={str(s['armed'])[:30]:30s} "
                      f"DOM序={s['armed_dom_idx']} "
                      f"落点={str(s['focus_aria'])[:18]:18s}"
                      f"落点是wrapper?{s['focus_lands_on_wrapper']} "
                      f"n_zero={s['n_zero']}")

            # ── 汇总这一轮的「布 0 顺序」vs「DOM 序」──
            seq_armed = [a[4:] if a.startswith("tid:") else a
                         for s in rec["steps"] for a in s["armed"]]
            rec["armed_sequence"] = seq_armed
            rec["armed_sequence_dom_idx"] = [
                dom_order.index(t) if t in dom_order else None
                for t in seq_armed]
            rec["n_zero_all_one"] = all(s["n_zero"] == 1 for s in rec["steps"])
            rec["prevented_all_false"] = all(
                s["key_prevented"] is False for s in rec["steps"])
            # 末尾几步：节点数之后还按了 OVERRUN 次，看看发生了什么
            rec["tail"] = rec["steps"][n:]
            print(f"\n  布 0 顺序（DOM 序下标）：{rec['armed_sequence_dom_idx']}")
            print(f"  n_zero 恒为 1？{rec['n_zero_all_one']}")
            print(f"  keydown defaultPrevented 全 False？{rec['prevented_all_false']}")
            print(f"  末尾 {OVERRUN} 次（已走过一圈）：")
            for s in rec["tail"]:
                print(f"     Tab{s['i']} 布0={s['armed']} "
                      f"落点={s['focus_aria']!r} n_zero={s['n_zero']}")
        finally:
            try:
                ev("() => { if (window.__b899) { window.__b899.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败：{e}")
            print("  仪器已还原")

        runs.append(rec)

    out["runs"] = runs

    def dom_idx_seq(r):
        return r["armed_sequence_dom_idx"]

    # 纯 DOM 序 ⇒ 步 i（从 0 起）应布到 dom_order[i % n]
    verdict_rows = []
    from collections import Counter
    for r in runs:
        n = r["n_nodes_dom"]
        seq = dom_idx_seq(r)
        expect = [i % n for i in range(len(seq))]
        # ⚠️ `seq` 里可能有 `None`（被布 0 的目标**不在**本轮记录的 DOM 序里
        # —— 走查途中节点被 React 重建就会这样）。**不许**让它进排序/比较，
        # 否则整个汇总会崩（第一版就崩在这）。
        known = [x for x in seq if x is not None]
        unknown = [x for x in seq if x is None]
        ever = sorted(set(known))
        skipped = [i for i in range(n) if i not in ever]
        cnt = Counter(known)
        wrapped = {k: v for k, v in cnt.items() if v > 1}
        verdict_rows.append({
            "n_nodes_dom": n,
            "n_pressed": r["presses"],
            "n_arming_events": len(seq),
            "n_arming_unknown_target": len(unknown),
            "armed_dom_idx": known,
            "expect_if_pure_dom_order": expect[:len(known)],
            "matches_pure_dom_order": known == expect[:len(known)],
            "skipped_dom_indices": skipped,
            "skipped_nodes": [r["meta"][i] for i in skipped],
            "max_dom_idx_armed": max(known) if known else None,
            "revisited_dom_indices": wrapped,
            "wrapped_back": bool(wrapped),
            "n_zero_all_one": r["n_zero_all_one"],
            "prevented_all_false": r["prevented_all_false"],
            "n_press_without_arming": sum(1 for s in r["steps"]
                                          if not s["armed"]),
            "focus_on_wrapper_count": sum(1 for s in r["steps"]
                                          if s["focus_lands_on_wrapper"]),
        })
    out["verdict_rows"] = verdict_rows
    out["all_match_pure_dom_order"] = all(
        v["matches_pure_dom_order"] for v in verdict_rows)
    out["all_wrapped_back"] = all(v["wrapped_back"] for v in verdict_rows)

    print("\n== 判定 ==")
    for v in verdict_rows:
        print(f"  n={v['n_nodes_dom']} 按了 {v['n_pressed']} 次，"
              f"其中**真的布上 0** 的 {v['n_arming_events']} 次、"
              f"**原地没布**的 {v['n_press_without_arming']} 次")
        print(f"     布 0 的 DOM 序：{v['armed_dom_idx'][:16]} …")
        print(f"     若纯 DOM 序应为：{v['expect_if_pure_dom_order'][:16]} …")
        print(f"     **完全吻合纯 DOM 序？{v['matches_pure_dom_order']}**")
        print(f"     走到的最远下标：{v['max_dom_idx_armed']}（DOM 共 "
              f"{v['n_nodes_dom']} 个）；**目标不在 DOM 序里**的布 0 事件："
              f"{v['n_arming_unknown_target']} 次")
        print(f"     ⇒ 指针**停在**最远下标 = {v['max_dom_idx_armed']}，"
              f"而 DOM 最后一个下标 = {v['n_nodes_dom'] - 1}")
        print(f"     **从没被布过 0 的下标**：{v['skipped_dom_indices']}")
        for nd in v["skipped_nodes"]:
            print(f"        就是它：{nd}")
        print(f"     **有绕回去吗**（同一下标被布 ≥2 次）："
              f"{v['wrapped_back']} {v['revisited_dom_indices']}")
        print(f"     n_zero 恒 1：{v['n_zero_all_one']}；"
              f"prevented 全 False：{v['prevented_all_false']}")
        print(f"     落点**确实是节点 wrapper** 的次数："
              f"{v['focus_on_wrapper_count']}/{v['n_pressed']}")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
