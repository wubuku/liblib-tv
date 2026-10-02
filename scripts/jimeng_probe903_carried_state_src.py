#!/usr/bin/env python3
"""batch 903 源站探针：902 那个「带过来的状态」到底是什么？

## 902 留下的未解格子

902 格 B：正向走到最后一个 → 往回 30 次（走出画布）→ **再点空白** → 按 `Tab` ×3
⇒ 布 `'0'` 的下标是 **`[2, 3]`**、**不是 0**。

⇒ 只够**否掉**「指针每次都从当前焦点现算」这一个假设 ⇒ **确实有**被带过来的
状态。**但那是什么、为什么是 2 —— 902 没解释。**

## 这一批的思路：**不猜机制，只量能约束住任何解释的事实**

关键是把两件被 902 混在一起的事**分开**：

- (i) 指针**停在末尾**（走完一圈、正向到最后一个）
- (ii) 焦点**真的走出过画布**（往回走出、落进顶栏/外围 chrome）

902 两件**同时**发生了，所以分不清是**哪一个**带出来的。所以这批做**四条对照**，
每条只动一个变量：

| 代号 | 序列 | 问的是 |
|---|---|---|
| `A` | 点空白 → `Tab` ×3 | **干净基线**：是不是 `0,1,2` |
| `B` | 点空白 → `Tab` ×3 → **点空白** → `Tab` ×3 | 只加「**中途离开过**」，指针**没**走到末尾 |
| `C` | 点空白 → `Tab` ×(n+25)（**走到末尾**）→ 点空白 → `Tab` ×3 | 只加「**指针到末尾**」，**没**走出过画布 |
| `D` | 点空白 → `Tab` ×(n+25) → `Shift+Tab` ×30（**走出画布**）→ 点空白 → `Tab` ×3 | 两件都加（= 902 那一格，**用来复现**） |

⇒ **C 与 D 的差别**就是答案的形状：
- 若 C 给 `0,1,2` 而 D 给别的 ⇒ **带出来的状态是「焦点出画布」这件事**
- 若 C、D 都给别的 ⇒ **带出来的是「指针停在末尾」这件事**
- 若 B 就已经给别的 ⇒ **只要中途离开过就带状态**（与末尾无关）

## 每一步都记

- 被布 `'0'` 的下标 + 身份（`data-testid` / `aria`）
- 按之前一刻的 `document.activeElement`（tag / testid / **在不在节点上**）
- 按之后那一刻的 `n_zero` / 持 `'0'` 的那个是谁
- `defaultPrevented`

## 纪律

- 仪器**逐字复用** 900
- 节点总数**易变量** ⇒ 按**身份**记 DOM 序
- 每轮**重复 2 次**；四条对照**每轮都跑**（顺序固定：A→B→C→D）
- **落盘必须排在打印之前**；诊断动作**必须还原**
- ⚠️ **不许**在探针里写「所以机制是 X」—— 只输出**读数**，
  判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe903_carried_state_src.py
"""

import json

OUT = "/tmp/b903-src-carried-state.json"
REPS = 2
OVERRUN = 25          # 和 902 同值：够走过一圈
BACK_OUT = 30         # 和 902 同值
SETTLE = 400          # 毫秒（Playwright）

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

NAMES_JS = """() => {
  const out = {};
  [...document.querySelectorAll('.react-flow__node')].forEach((n, i) => {
    out[n.getAttribute('data-testid') || ''] = {
      idx: i, aria: n.getAttribute('aria-label') || '',
      kind: [...n.classList].find(c => c.startsWith('react-flow__node-')
            && c !== 'react-flow__node') || '?'};
  });
  return out;
}"""

# ⚠️ 仪器逐字来自 900
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b903) { window.__b903.cleanup(); }
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
              kind: 'focusin@capture', target: ident(e.target),
              target_is_node_wrapper: !!(e.target.classList
                && e.target.classList.contains('react-flow__node')),
              target_aria: (e.target.getAttribute
                && e.target.getAttribute('aria-label')) || ''});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key, shift: e.shiftKey,
              target: ident(e.target), ref: e});
  };
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; rec.shift = e.shiftKey; delete rec.ref; }
  };
  document.addEventListener('focusin', onFocusInCap, true);
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('keydown', onKeyEnd, false);
  const mo = new MutationObserver((recs) => {
    for (const r of recs) {
      log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
                kind: 'attr:' + r.attributeName,
                target: ident(r.target), oldValue: r.oldValue,
                value_at_flush: r.target.getAttribute(r.attributeName)});
    }
  });
  mo.observe(root, {attributes: true, attributeOldValue: true,
                    attributeFilter: ['tabindex'], subtree: true});
  window.__b903 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b903;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {}; const zeros = [];
  for (const n of nodes) {
    const ti = n.getAttribute('tabindex');
    const k = ti === null ? 'None' : ti;
    hist[k] = (hist[k] || 0) + 1;
    if (ti === '0') zeros.push(n.getAttribute('data-testid') || '(no-testid)');
  }
  const a = document.activeElement;
  const an = a && a.closest && a.closest('.react-flow__node');
  return {n_nodes: nodes.length, hist, zeros, n_zero: zeros.length,
    active: {
      tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      self_ti: (a && a.getAttribute) ? a.getAttribute('tabindex') : null,
      in_node: !!an,
      node_tid: an ? an.getAttribute('data-testid') : null}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def press(pg, mod=False):
    """按一次键。**先记按之前一刻的 activeElement**，再按，再记变更流。"""
    before = ev(STATE_JS)["active"]
    cur = ev("() => window.__b903.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b903.since(f)", cur)
    st = ev(STATE_JS)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    return {"before": before, "armed": armed,
            "n_zero": st["n_zero"], "zeros": st["zeros"],
            "after": st["active"],
            "prevented": (kd[-1].get("default_prevented") if kd else None),
            "focus_aria": (fi[-1]["target_aria"] if fi else None),
            "focus_is_wrapper": (fi[-1]["target_is_node_wrapper"] if fi else None)}


def idx_of(armed, dom, names):
    out = []
    for a in armed:
        tid = a[4:] if a.startswith("tid:") else a
        if tid in dom:
            i = dom.index(tid)
            out.append({"idx": i, "tid": tid,
                        "aria": (names.get(tid) or {}).get("aria"),
                        "kind": (names.get(tid) or {}).get("kind")})
        else:
            out.append({"idx": None, "tid": tid})
    return out


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
        dom = ev(DOM_ORDER_JS)
        names = ev(NAMES_JS)
        n = len(dom)
        rec = {"rep": rep, "n_nodes": n, "arms": {}}
        print(f"\n===== rep {rep}（{n} 个节点）=====")
        print(f"  DOM 前 6 个："
              f"{[(i, names[d].get('aria')) for i, d in enumerate(dom[:6])]}")
        inst = ev(INSTALL_JS)
        rec["instrument"] = inst

        def blank():
            sp = ev(BLANK_JS)
            if sp:
                page.mouse.click(sp[0], sp[1])
                page.wait_for_timeout(1000)
            return sp

        def record(code, s):
            rec["arms"].setdefault(code, []).append({
                "before_in_node": s["before"]["in_node"],
                "before_tid": s["before"]["tid"],
                "before_aria": s["before"]["aria"][:20],
                "armed": idx_of(s["armed"], dom, names),
                "n_zero": s["n_zero"],
                "zero_holder": idx_of([t for t in s["zeros"]], dom, names),
                "after_in_node": s["after"]["in_node"],
                "after_tid": s["after"]["tid"],
                "after_aria": s["after"]["aria"][:20],
                "prevented": s["prevented"],
            })

        try:
            # ── A：干净基线 ──
            blank()
            for _ in range(3):
                record("A", press(page))
            print("  [A] 干净基线 Tab×3 ⇒ 布0下标："
                  f"{[a['idx'] for st in rec['arms']['A'] for a in st['armed']]}")

            # ── B：中途离开过（指针没到末尾）──
            blank()
            for _ in range(3):
                press(page)
            blank()                      # ← 只加这一个变量
            for _ in range(3):
                record("B", press(page))
            print("  [B] 中途点空白后 Tab×3 ⇒ 布0下标："
                  f"{[a['idx'] for st in rec['arms']['B'] for a in st['armed']]}")

            # ── C：指针到末尾（但**没**走出过画布）──
            blank()
            for _ in range(n + OVERRUN):
                press(page)
            c_state = ev(STATE_JS)
            rec["C_state_at_end"] = {"n_zero": c_state["n_zero"],
                                     "zeros": idx_of(c_state["zeros"], dom, names),
                                     "active": c_state["active"]}
            print(f"  [C 走到末尾] n_zero={c_state['n_zero']} "
                  f"0 在 {[z['idx'] for z in rec['C_state_at_end']['zeros']]}；"
                  f"此刻焦点在节点内={c_state['active']['in_node']}")
            blank()                      # ← 只加这一个变量
            for _ in range(3):
                record("C", press(page))
            print("  [C] 点空白后 Tab×3 ⇒ 布0下标："
                  f"{[a['idx'] for st in rec['arms']['C'] for a in st['armed']]}")

            # ── D：两件都加（复现 902 那一格）──
            blank()
            for _ in range(n + OVERRUN):
                press(page)
            for _ in range(BACK_OUT):
                press(page, mod=True)
            d_state = ev(STATE_JS)
            rec["D_state_before_reblank"] = {
                "n_zero": d_state["n_zero"],
                "zeros": idx_of(d_state["zeros"], dom, names),
                "active": d_state["active"]}
            print(f"  [D 往回 {BACK_OUT} 次后] n_zero={d_state['n_zero']} "
                  f"0 在 {[z['idx'] for z in rec['D_state_before_reblank']['zeros']]}；"
                  f"焦点 tag={d_state['active']['tag']} "
                  f"aria={d_state['active']['aria'][:18]!r} "
                  f"在节点内={d_state['active']['in_node']}")
            blank()
            for _ in range(3):
                record("D", press(page))
            print("  [D] 点空白后 Tab×3 ⇒ 布0下标："
                  f"{[a['idx'] for st in rec['arms']['D'] for a in st['armed']]}")
        finally:
            try:
                ev("() => { if (window.__b903) { window.__b903.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败：{e}")
            print("  仪器已还原")
        runs.append(rec)

    out["runs"] = runs
    out["summary"] = []
    for r in runs:
        row = {"rep": r["rep"], "n_nodes": r["n_nodes"]}
        for code in ("A", "B", "C", "D"):
            st = r["arms"].get(code) or []
            row[code] = {
                "armed_idx": [a["idx"] for s in st for a in s["armed"]],
                "armed_nodes": [a for s in st for a in s["armed"]],
                "before_in_node": [s["before_in_node"] for s in st],
                "before_aria": [s["before_aria"] for s in st],
                "zero_holder_idx": [z["idx"] for s in st
                                    for z in s["zero_holder"]],
                "prevented_all_false": all(s["prevented"] is False for s in st),
            }
        row["C_state_at_end_zeros"] = [
            z["idx"] for z in r["C_state_at_end"]["zeros"]]
        row["D_state_before_reblank_zeros"] = [
            z["idx"] for z in r["D_state_before_reblank"]["zeros"]]
        out["summary"].append(row)
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总：四条对照（只输出读数，**不判机制**）==")
    for row in out["summary"]:
        print(f"  rep{row['rep']}（{row['n_nodes']} 个节点）")
        for code, desc in (("A", "干净基线"),
                           ("B", "中途点空白（指针没到末尾）"),
                           ("C", "指针到末尾（没走出画布）"),
                           ("D", "到末尾 ＋ 走出画布（= 902 那格）")):
            d = row[code]
            print(f"    {code} {desc:26s} 布0下标={d['armed_idx']} "
                  f"持0者={d['zero_holder_idx']} "
                  f"按前在节点内={d['before_in_node']}")
        print(f"    C 走到末尾时持 0 者 = {row['C_state_at_end_zeros']}")
        print(f"    D 往回走完时持 0 者 = {row['D_state_before_reblank_zeros']}")
    print(f"\n== 已写 {OUT} ==")
