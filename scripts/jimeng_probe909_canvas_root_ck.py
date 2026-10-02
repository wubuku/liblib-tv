#!/usr/bin/env python3
r"""batch 909 复刻侧验收：906/906②/908 那几格，改完到底对不对上？

## 这一批改了什么（**唯一的代码改动**）

`JimengWorkspace.tsx` 的模块级 `armRovingTabindex`：

| 位置 | 改前 | 改后 | 依据 |
|---|---|---|---|
| 找指针 `cur` | `n === active \|\| n.contains(active)` | **`n === active`** | 906：`closest` 口径会骗人，真判据是 `contains`（元素**本身就是**节点本体） |
| `cur === -1` 时 | 直接 `armAll(nodes, 0)` | **先判「焦点是否在某个节点的内层控件里」，是就 `return`** | 906 逐次证实：那几次「没布」的按压前焦点正是内层控件 |
| 越界 | `return` | **不动** | 908 复核：撒手那一格仍成立 |

## 判据**逐字复用**源站探针

- `STATE_JS` / `INSTALL_JS` **逐字来自 906**
- 臂**逐字对应** 906 的 `F8-fresh` / `F8` / `B8` 与 908 的 `W1` / `W2`

| 臂 | 对应源站 | 期望（源站实测） |
|---|---|---|
| `F8-fresh` | 906 `F8-fresh` | 从画布根按 `Tab`：**要布**，从 `0` 起 |
| `F8` | 906 `F8` | 走到末尾＋回走 ⇒ 按 `Tab` 要布 |
| `B8` | 906 `B8` | 画布根按 `Shift+Tab`：**一次都不布** |
| `W1` | 908 `W1` | 一路按到焦点走回画布根 ⇒ **会绕回布 `0`** |
| `W2` | 908 `W2` | 刚过末尾就点空白直接回画布根 ⇒ **也绕回布 `0`** |

⚠️ **不许**把「复刻侧读到几」当判据 —— 判据是**源站那条**，复刻侧只负责对上或对不上。

## 判据纪律

- 每臂之间 reload；每轮**重复 2 次**
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；诊断动作**必须还原**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  SNAP_URL=http://localhost:4317/jimeng/canvas/demo \
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe909_canvas_root_ck.py
"""

import json
import os
import time

from playwright.sync_api import sync_playwright

OUT = os.environ.get("SNAP_OUT", "/tmp/b909-ck-canvas-root.json")
REPS = 2
K_BACK = 30
N_PRESS = 8
SETTLE = 0.3            # **秒**（Python 端 time.sleep 收秒；Playwright 那边收毫秒）

ARMS = [
    {"label": "F8-fresh", "walk_end": False, "back": 0,      "mod": False},
    {"label": "F8",       "walk_end": True,  "back": K_BACK, "mod": False},
    {"label": "B8",       "walk_end": True,  "back": K_BACK, "mod": True},
    {"label": "W1",       "walk_end": True,  "back": 0,      "mod": False},
    {"label": "W2",       "walk_end": True,  "back": 0,      "mod": False},
]

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

NAMES_JS = """() => {
  const out = {};
  [...document.querySelectorAll('.react-flow__node')].forEach((n, i) => {
    out[n.getAttribute('data-testid') || ''] = {
      idx: i, aria: n.getAttribute('aria-label') || ''};
  });
  return out;
}"""

# ⚠️ 仪器逐字来自 906
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b909) { window.__b909.cleanup(); }
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
  window.__b909 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b909;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 906
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
  return {n_nodes: nodes.length, hist, zeros, n_zero: zeros.length,
    active: {tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      in_node_closest: !!(a && a.closest
        && a.closest('.react-flow__node')),
      is_wrapper: !!(a && a.classList
        && a.classList.contains('react-flow__node'))}};
}"""


def main() -> int:
    url = os.environ.get("SNAP_URL", "http://localhost:4317/jimeng/canvas/demo")
    out: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        # 视口与源站探针逐字相同（1512×1200）—— BLANK_JS 里的落点坐标按它挑的
        pg = b.new_context(viewport={"width": 1512, "height": 1200}).new_page()
        page = pg   # 下面那些辅助函数闭包用它

        def ev(js, arg=None):
            return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

        def snap(names):
            st = ev(STATE_JS)
            zs = [names.get(t, {}).get("idx") for t in st["zeros"]]
            return {"zeros": zs, "n_zero": st["n_zero"],
                    "active_aria": st["active"]["aria"][:22],
                    "in_node_closest": st["active"]["in_node_closest"],
                    "is_wrapper": st["active"]["is_wrapper"]}

        def press(names, mod=False):
            pre = snap(names)
            cur = ev("() => window.__b909.cursor()")
            if mod:
                pg.keyboard.down("Shift")
            pg.keyboard.press("Tab")
            if mod:
                pg.keyboard.up("Shift")
            time.sleep(SETTLE)
            seg = ev("(f) => window.__b909.since(f)", cur)
            armed = [r["target"] for r in seg
                     if r["kind"].startswith("attr:")
                     and r["value_at_flush"] == '0' and r["oldValue"] != '0']
            fi = [r for r in seg if r["kind"] == "focusin@capture"]
            kd = [r for r in seg if r["kind"] == "keydown@capture"]
            post = snap(names)
            return {"armed": armed,
                    "zero_before": pre["zeros"], "zero_after": post["zeros"],
                    "moved": pre["zeros"] != post["zeros"],
                    "armed_idx": [names.get(a[4:], {}).get("idx")
                                  for a in armed if a.startswith("tid:")],
                    "pre_aria": pre["active_aria"],
                    "pre_in_node_closest": pre["in_node_closest"],
                    "pre_is_wrapper": pre["is_wrapper"],
                    "land_aria": [f["target_aria"] for f in fi],
                    "land_is_wrapper": [f["target_is_node_wrapper"] for f in fi],
                    "prevented": (kd[-1].get("default_prevented") if kd else None)}

        def blank():
            sp = ev(BLANK_JS)
            if sp:
                pg.mouse.click(sp[0], sp[1])
                time.sleep(0.9)
            return sp

        def idx_of(names, a):
            return names.get(a[4:], {}).get("idx") if a.startswith("tid:") else None

        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_selector(".react-flow__node", timeout=30000)
        time.sleep(2.0)
        n0 = ev("() => document.querySelectorAll('.react-flow__node').length")
        out["ready"] = n0 > 0
        print(f"== 复刻就绪：{out['ready']}（{n0} 个节点）==")

        if not out["ready"]:
            out["verdict"] = "BLOCKED_BY_FIXTURE（复刻页面没起来）"
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"== 已写 {OUT}（被挡时也要落盘）==")
            return 1

        runs = []
        for rep in range(1, REPS + 1):
            rec = {"rep": rep, "arms": []}
            for spec in ARMS:
                # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_selector(".react-flow__node", timeout=30000)
                time.sleep(1.5)
                names = ev(NAMES_JS)
                n = len(names)
                inst = ev(INSTALL_JS)
                print(f"\n--- rep{rep} {spec['label']}（{n} 个节点，"
                      f"instrument={inst.get('ok')}）---")
                try:
                    blank()
                    fwd = []
                    if spec["walk_end"]:
                        for _ in range(n + 20):     # 走到末尾
                            fwd.append(press(names))
                    at_end = snap(names)
                    back = [press(names, mod=True) for _ in range(spec["back"])]
                    endpoint = snap(names)
                    if spec["label"] == "W2":
                        blank()                  # 刚过末尾就点空白：直接回画布根
                    blank()
                    after = [press(names, mod=spec["mod"])
                             for _ in range(N_PRESS)]
                finally:
                    try:
                        ev("() => { if (window.__b909) { window.__b909.cleanup(); "
                           "return 'cleaned'; } return 'none'; }")
                    except Exception as e:      # noqa: BLE001
                        print(f"  !! cleanup 失败：{e}")

                rec["arms"].append({
                    "label": spec["label"], "mod": spec["mod"],
                    "at_end": at_end, "endpoint": endpoint,
                    "fwd_armed_count": sum(1 for s in fwd if s["armed"]),
                    "back_armed_count": sum(1 for s in back if s["armed"]),
                    "after_per_press": [
                        {"armed_idx": s["armed_idx"],
                         "zero_before": s["zero_before"],
                         "zero_after": s["zero_after"],
                         "moved": s["moved"],
                         "pre_aria": s["pre_aria"],
                         "pre_in_node_closest": s["pre_in_node_closest"],
                         "pre_is_wrapper": s["pre_is_wrapper"],
                         "land_aria": s["land_aria"][:1],
                         "land_is_wrapper": s["land_is_wrapper"][:1],
                         "prevented": s["prevented"]}
                        for s in after],
                    "after_armed_idx": [i for s in after
                                        for i in s["armed_idx"]],
                    # ⚠️ `after_armed_idx` **会被 oldValue 过滤吞掉**（904 记过）⇒
                    # 另记一条「'0' 动过没有」的序列，两条一起看才不漏读
                    "after_moved": [s["moved"] for s in after],
                    "after_zero_after": [s["zero_after"] for s in after],
                    "prevented_all_false": all(
                        s["prevented"] is False for s in fwd + back + after),
                })
                a = rec["arms"][-1]
                print(f"  末尾{a['at_end']['zeros']} → 终点{a['endpoint']['zeros']}"
                      f" ⇒ 按 {N_PRESS} 次布 {a['after_armed_idx']}")
                for i, s in enumerate(a["after_per_press"]):
                    print(f"    press{i+1}: 按前={s['pre_aria']!r} "
                          f"closest={s['pre_in_node_closest']} "
                          f"本体={s['pre_is_wrapper']} ⇒ 布{s['armed_idx']} "
                          f"｜'0' {s['zero_before']}→{s['zero_after']} "
                          f"**动了={s['moved']}**")
            runs.append(rec)
            print("  仪器已还原")

        out["runs"] = runs
        out["summary"] = [{
            "rep": r["rep"],
            "arms": [{"label": a["label"], "mod": a["mod"],
                      "endpoint_zeros": a["endpoint"]["zeros"],
                      "after_armed_idx": a["after_armed_idx"],
                      "prevented_all_false": a["prevented_all_false"]}
                     for a in r["arms"]],
        } for r in runs]
        out["verdict"] = "sampled"

        # ⚠️ 落盘**必须**排在打印之前
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        print("\n== 汇总（只输出读数）==")
        for row in out["summary"]:
            print(f"  rep{row['rep']}")
            for a in row["arms"]:
                print(f"    {a['label']:<10s} mod={a['mod']} "
                      f"终点{a['endpoint_zeros']} ⇒ 布 {a['after_armed_idx']}"
                      f"｜'0' 末态 {a['after_zero_after']}")
        print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
