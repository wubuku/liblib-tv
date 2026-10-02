#!/usr/bin/env python3
"""batch 901 复刻探针：验刚实现的 roving 是否**与源站同规则**。

## 改了什么

`JimengWorkspace.tsx`：`nodesFocusable={false}`（中性态无 `tabindex` 属性）
＋ 模块级 `armRovingTabindex`（keydown 捕获阶段布 `'0'`/`'-1'`、**不**
preventDefault、到末尾撒手、此后不回撤）。

## 判据必须**逐字复用源站探针**

判据全部来自 896/899/900 的**源站**探针（`INSTALL_JS`、`STATE_JS`、
`DOM_ORDER_JS`、空白点候选）。**不许**在这里改写成「复刻版」——
判据不同就量出了「不同」，而那只是判据不同（890c 的教训）。

## 逐条对照源站的哪一条

| 源站事实（出处） | 复刻侧该怎么读到 |
|---|---|
| 中性态**无 `tabindex` 属性**（896 ①） | `hist == {'None': n}` |
| 第一次 Tab 布「目标 `0` / 其余 `-1`」全画布重写（896 ②） | `n_zero == 1` 且 `hist == {'0':1, '-1':n-1}` |
| **不** preventDefault（896 ③） | keydown `default_prevented` 全 `False` |
| **先布 `0` 再移焦点**（896 ④） | `focusin@capture` 时落点 `ti` 已是 `'0'` |
| **此后不回撤**（896 ⑤） | 点空白之后那个 `'0'` 仍在 |
| 顺序**≈DOM 序**（899 ①） | 布 `0` 的下标连成 `[0,1,2,…]` |
| **到末尾撒手、绝不绕回**（899 ②） | 越界后**不再**有任何布 `0` 动作 |
| ⚠️ 源站有 **2 个节点整轮没被布上 `0`**（900，原因不可从 DOM 查明） | 复刻**按纯 DOM 序** ⇒ 预期**没有**这个例外 ⇒ **这是刻意记下的差异** |

## 纪律

- 每轮**重复 2 次**；每轮**从刚载完**开始
- 仪器**必须还原**（`finally` 里 disconnect + 摘监听）
- 节点总数是**易变量**（复刻 demo 自带 2 个 video，探针再插 5 个）⇒
  按**身份**记 DOM 序，**不钉**个数
- **落盘必须排在打印之前**（900 的教训），长输出别进管道

## 计费边界

只点左栏**插入**入口、点画布空白、点节点本体、按 Tab/Shift+Tab。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe901_roving_impl_ck.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b901-ck-roving-impl.json")
REPS = 2
KINDS = ["文本", "图片", "时间线", "主体", "导演台"]
OVERRUN = 20           # ⚠️ 第一版 OVERRUN=6 **不够**：走查里有一堆按压被节点的
                       # **内层控件**吃掉（复刻 video 节点有 5 个内层按钮），
                       # 13 次按压只把指针推到下标 5（DOM 共 7 个）⇒
                       # **根本没走到末尾** ⇒ 「899② 到末尾撒手」**没验到**。
                       # 加到 20 才是**故意走过一圈**。
SETTLE = 0.4            # ← **秒**（895 踩过毫秒/秒的坑）

# ⚠️⚠️ 以下 JS **逐字来自 899/900 的源站探针**，不许改。
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

STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {};            // tabindex 值 → **有几个**
  const zeros = [];           // 所有 tabindex='0' 的节点身份
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

# ⚠️ 仪器也逐字来自 900（只把 window 上的名字从 __b900 换成 __b901）
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b901) { window.__b901.cleanup(); }
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
                && e.target.getAttribute('aria-label')) || '',
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key,
              target: ident(e.target), ref: e});
  };
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; delete rec.ref; }
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
  window.__b901 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b901;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url, "runs": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        for rep in range(1, REPS + 1):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4.0)
            rec: dict = {"rep": rep, "steps": []}

            def ev(js, arg=None):
                return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

            print(f"\n===== rep {rep} =====")

            def read(cond, note=""):
                st = ev(STATE_JS)
                d = {"cond": cond, "note": note, "hist": st["hist"],
                     "n_zero": st["n_zero"], "n_nodes": st["n_nodes"],
                     "zeros": st["zeros"], "active": st["active"]}
                rec["steps"].append(d)
                print(f"  [{cond}] hist={d['hist']} n_zero={d['n_zero']} "
                      f"落点aria={d['active']['aria']!r}")
                return d

            # ① 中性态（刚载完、什么都不插、什么都不点）
            read("neutral_fresh_load", "刚载完什么都不做（只自带 2 个 video）")

            # 插 5 个类型，让走查有点长度（插一个量一个，避免 897 的重叠问题）
            for label in KINDS:
                loc = pg.locator(f'button[aria-label="{label}"]')
                if loc.count():
                    loc.first.click(timeout=8000)
                    time.sleep(1.4)
            read("after_insert_all", f"插完 {KINDS}")
            dom = ev(DOM_ORDER_JS)
            rec["dom_order"] = dom
            n = len(dom)
            print(f"  DOM 序 {n} 个节点")

            # ② 装仪器（**点空白之前**就装）
            rec["instrument"] = ev(INSTALL_JS)
            try:
                spot = ev(BLANK_JS)
                if spot:
                    pg.mouse.click(spot[0], spot[1])
                    time.sleep(1.0)
                rec["blank_spot"] = spot
                read("after_blank", f"点空白 {spot}")

                # ③ 走 Tab：节点数 + OVERRUN 次（要看「到末尾撒手」）
                walk = []
                for i in range(1, n + OVERRUN + 1):
                    cur = ev("() => window.__b901.cursor()")
                    pg.keyboard.press("Tab")
                    time.sleep(SETTLE)
                    seg = ev("(f) => window.__b901.since(f)", cur)
                    st = ev(STATE_JS)
                    armed = [r["target"] for r in seg
                             if r["kind"].startswith("attr:")
                             and r["value_at_flush"] == '0'
                             and r["oldValue"] != '0']
                    kd = [r for r in seg if r["kind"] == "keydown@capture"]
                    fi = [r for r in seg if r["kind"] == "focusin@capture"]
                    walk.append({
                        "i": i,
                        "armed": armed,
                        "armed_idx": [(dom.index(a[4:])
                                       if a.startswith("tid:") and a[4:] in dom
                                       else None) for a in armed],
                        "n_zero": st["n_zero"], "hist": st["hist"],
                        "focus_aria": st["active"]["aria"],
                        "focus_ti_at_focusin": (fi[-1]["target_tabindex"]
                                               if fi else None),
                        "focus_is_wrapper": (fi[-1]["target_is_node_wrapper"]
                                             if fi else None),
                        "prevented": (kd[-1].get("default_prevented")
                                      if kd else None),
                    })
                    w = walk[-1]
                    print(f"   Tab{i:<3d} 布0={w['armed_idx']} "
                          f"n_zero={w['n_zero']} "
                          f"落点={w['focus_aria'][:18]!r} "
                          f"focusin时落点ti={w['focus_ti_at_focusin']!r} "
                          f"prevented={w['prevented']}")
                rec["walk"] = walk
                armed_idx = [x for w in walk for x in w["armed_idx"]]
                rec["armed_idx"] = armed_idx

                # ④ 「此后不回撤」：再点空白，那个 0 还在吗
                spot2 = ev(BLANK_JS)
                if spot2:
                    pg.mouse.click(spot2[0], spot2[1])
                    time.sleep(1.0)
                read("after_blank_again", f"走完之后再点空白 {spot2}")
                rec["blank_spot_2"] = spot2

                # ⑤ Shift+Tab 一次（看反向）
                cur = ev("() => window.__b901.cursor()")
                pg.keyboard.press("Shift+Tab")
                time.sleep(SETTLE)
                seg = ev("(f) => window.__b901.since(f)", cur)
                st = ev(STATE_JS)
                rec["one_shift_tab"] = {
                    "armed": [r["target"] for r in seg
                              if r["kind"].startswith("attr:")
                              and r["value_at_flush"] == '0'
                              and r["oldValue"] != '0'],
                    "n_zero": st["n_zero"], "hist": st["hist"],
                    "focus_aria": st["active"]["aria"],
                }
                print(f"  [Shift+Tab 一次] {rec['one_shift_tab']}")
            finally:
                try:
                    ev("() => { if (window.__b901) { window.__b901.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:      # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")
                print("  仪器已还原")

            res["runs"].append(rec)

        b.close()

    # ── 汇总：逐条对照源站 ──
    summ = []
    for r in res["runs"]:
        neutral = next(s for s in r["steps"] if s["cond"] == "neutral_fresh_load")
        after_ins = next(s for s in r["steps"] if s["cond"] == "after_insert_all")
        after_blank = next(s for s in r["steps"] if s["cond"] == "after_blank")
        again = next(s for s in r["steps"] if s["cond"] == "after_blank_again")
        walk = r["walk"]
        armed = r["armed_idx"]
        n = len(r["dom_order"])
        last_arm = max((i for i, x in enumerate(armed) if x is not None),
                       default=None)
        reached_end = last_arm == n - 1
        # ⚠️ 只有**真的走到最后一个节点**，「越界后有没有再布」这一问才成立。
        # 走到一半就下结论 = 拿没测到的数据说事（899 第一版的坑）。
        past = walk[n:] if len(walk) > n else []
        beyond = [w["armed_idx"] for w in walk[n:] if w["armed_idx"]]
        # 「越界」= 指针已经到最后一个、之后**还有**按压
        after_last = []
        if reached_end:
            seen_last = False
            for w in walk:
                if w["armed_idx"] and max(
                        x for x in w["armed_idx"] if x is not None) == n - 1:
                    seen_last = True
                    continue
                if seen_last and w["armed_idx"]:
                    after_last.append(w["armed_idx"])

        summ.append({
            "rep": r["rep"],
            "n_nodes": n,
            # 896 ①
            "neutral_has_no_tabindex":
                set(neutral["hist"]) <= {"None"},
            "after_insert_has_no_tabindex":
                set(after_ins["hist"]) <= {"None"},
            "after_blank_has_no_tabindex":
                set(after_blank["hist"]) <= {"None"},
            # 896 ②
            "n_zero_is_1_everywhere": all(w["n_zero"] == 1 for w in walk),
            "hist_shape_ok": all(
                w["hist"].get("0") == 1 and w["hist"].get("-1", 0) == n - 1
                for w in walk),
            # 896 ③
            "prevented_all_false": all(w["prevented"] is False for w in walk),
            # 896 ④
            "zero_set_before_focus_moves": all(
                w["focus_ti_at_focusin"] == "0"
                for w in walk if w["focus_is_wrapper"]),
            # 899 ①
            "armed_idx_sequence": armed,
            "armed_is_dom_order": armed == list(range(len(armed))),
            # 899 ②
            "last_armed_idx": last_arm,
            "reached_last_node": reached_end,
            "arms_after_reaching_last": after_last,
            "no_wrap_confirmed": reached_end and not after_last,
            # 896 ⑤
            "zero_persists_after_blank": again["n_zero"] == 1,
            "zero_holder_after_blank": again["zeros"],
            "one_shift_tab": r["one_shift_tab"],
        })
    res["summary"] = summ
    res["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    print("\n== 逐条对照源站（各 2/2）==")
    for s in summ:
        print(f"  rep{s['rep']}（{s['n_nodes']} 个节点）")
        print(f"    896① 中性态无 tabindex："
              f"{s['neutral_has_no_tabindex']} / "
              f"插完仍无：{s['after_insert_has_no_tabindex']} / "
              f"点空白后仍无：{s['after_blank_has_no_tabindex']}")
        print(f"    896② n_zero 恒 1：{s['n_zero_is_1_everywhere']}；"
              f"直方图形状对：{s['hist_shape_ok']}")
        print(f"    896③ preventDefault 全 False：{s['prevented_all_false']}")
        print(f"    896④ 先布 0 再移焦点：{s['zero_set_before_focus_moves']}")
        print(f"    899① 布 0 顺序：{s['armed_idx_sequence']} "
              f"⇒ 纯 DOM 序？{s['armed_is_dom_order']}")
        print(f"    899② 走到的最远下标：{s['last_armed_idx']}"
              f"（DOM 共 {s['n_nodes']} 个）")
        if s["reached_last_node"]:
            print(f"        走到了最后一个 ⇒ 越界后还有布 0 吗："
                  f"{s['arms_after_reaching_last'] or '（无 ⇒ 撒手 ✓）'}"
                  f"；**不绕回**已确认：{s['no_wrap_confirmed']}")
        else:
            print(f"        ⚠️ **没走到最后一个** ⇒ 「到末尾撒手 / 不绕回」"
                  f"**这一问本轮不成立**（不许拿没测到的数据下结论）")
        print(f"    896⑤ 点空白后那个 0 仍在：{s['zero_persists_after_blank']}"
              f"（在 {s['zero_holder_after_blank']} 上）")
        print(f"    Shift+Tab 一次：{s['one_shift_tab']}")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
