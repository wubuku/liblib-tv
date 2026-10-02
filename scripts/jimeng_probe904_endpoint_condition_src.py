#!/usr/bin/env python3
"""batch 904 源站探针：那个**落点条件**是什么？

## 903 留下的未解格子

903 的四条对照 8/8 都给 `[0,1,2]`，而 902 给 `[2,3]`。差别是**可测**的：

| 跑次 | 往回走结束时 `'0'` 在 | 回来后按 `Tab` ×3 |
|---|---|---|
| 902（2/2） | 下标 **58** | `[2, 3]` |
| 903 的 `D`（2/2） | 下标 **59** | `[0, 1, 2]` |

⇒ **两个都是真实读数**；「从 0 开始不是无条件的」；**触发条件仍未查明**。

## 这一批的思路：**扫两个变量 + 记入场状态**

不知道是哪条因果链在动，所以**能测的都记下来**：

- **扫的变量 1：进场前的 `Shift+Tab` 次数 `pre`**（902 开头有 5 次格 A，903 的 D 没有）
- **扫的变量 2：往回按 `Shift+Tab` 的次数 `k`**
- **入场状态**：每条臂**开始时** `'0'` 在谁身上

## 为什么光扫 `k` 不够

902 与 903 的 `k` **相同**（都是 30）却落在 58 / 59 ⇒ **按的次数解释不了**。
最可疑的差别是 902 开头那 5 次 `Shift+Tab`（它把焦点带出了画布），
所以 `pre` 必须也当变量扫进来。

## 判据纪律

- 仪器**逐字复用** 900
- 节点总数**易变量** ⇒ 按**身份**记 DOM 序
- 每轮**重复 2 次**；所有臂**每轮都跑**、顺序固定
- **落盘必须排在打印之前**；诊断动作**必须还原**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe904_endpoint_condition_src.py
"""

import json

OUT = "/tmp/b904-src-endpoint-condition.json"
REPS = 2
# 扫的变量有两个，都可测：
#   pre —— 进场前先按几次 Shift+Tab（902 开头有 5 次格 A，903 的 D 没有）
#   k   —— 往回按几次
# 902 与 903 的 **k 相同（都 30）**却落在 58 / 59 ⇒ 光扫 k 不够，
# 所以必须把 pre 也当变量扫进来。
ARMS = [
    {"label": "base-k30",   "pre": 0, "k": 30},
    {"label": "base-k28",   "pre": 0, "k": 28},
    {"label": "base-k32",   "pre": 0, "k": 32},
    {"label": "shift5-k30", "pre": 5, "k": 30},
]
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

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
      idx: i, aria: n.getAttribute('aria-label') || ''};
  });
  return out;
}"""

# ⚠️ 仪器逐字来自 900
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b904) { window.__b904.cleanup(); }
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
  window.__b904 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b904;
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
    active: {tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      in_node: !!an,
      node_tid: an ? an.getAttribute('data-testid') : null}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def press(pg, mod=False):
    cur = ev("() => window.__b904.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b904.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    return {"armed": armed,
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


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
        rec = {"rep": rep, "n_nodes": n, "arms": []}
        print(f"\n===== rep {rep}（{n} 个节点）=====")
        inst = ev(INSTALL_JS)
        rec["instrument"] = inst

        def blank():
            sp = ev(BLANK_JS)
            if sp:
                page.mouse.click(sp[0], sp[1])
                page.wait_for_timeout(900)
            return sp

        def zero_idx():
            st = ev(STATE_JS)
            return {"n_zero": st["n_zero"],
                    "zeros": [names.get(t, {}).get("idx")
                              for t in st["zeros"]],
                    "aria": [names.get(t, {}).get("aria")
                             for t in st["zeros"]],
                    "active_in_node": st["active"]["in_node"],
                    "active_aria": st["active"]["aria"][:18]}

        try:
            for spec in ARMS:
                pre, k = spec["pre"], spec["k"]
                blank()
                pre_presses = [press(page, mod=True) for _ in range(pre)]
                pre_end = zero_idx()
                entry = zero_idx()              # ← **入场状态**
                fwd = []
                for _ in range(n + 25):        # 走到末尾（与 902/903 同）
                    fwd.append(press(page))
                at_end = zero_idx()
                back = []
                for _ in range(k):
                    back.append(press(page, mod=True))
                endpoint = zero_idx()           # ← **终点**
                blank()
                after = [press(page) for _ in range(3)]
                after_state = zero_idx()
                armed_idx = [names.get(a[4:], {}).get("idx")
                             for s in after for a in s["armed"] if a.startswith("tid:")]
                arm = {"label": spec["label"], "pre": pre, "k": k,
                       "pre_state": pre_end, "entry": entry, "at_end": at_end,
                       "endpoint": endpoint, "after_armed_idx": armed_idx,
                       "after_state": after_state,
                       "after_armed_aria": [
                           names.get(a[4:], {}).get("aria")
                           for s in after for a in s["armed"] if a.startswith("tid:")],
                       "pre_armed_count": sum(1 for s in pre_presses if s["armed"]),
                       "fwd_armed_count": sum(1 for s in fwd if s["armed"]),
                       "back_armed_count": sum(1 for s in back if s["armed"]),
                       "prevented_all_false": all(
                           s["prevented"] is False
                           for s in pre_presses + fwd + back + after)}
                rec["arms"].append(arm)
                print(f"  [{spec['label']}] pre={pre} 入场 0 在 {entry['zeros']}"
                      f" → 走到末尾 0 在 {at_end['zeros']}"
                      f" → 往回 {k} 次后 0 在 {endpoint['zeros']}"
                      f"（布了 {arm['back_armed_count']} 次）"
                      f" ⇒ 回来后 Tab×3 布 {armed_idx}")
        finally:
            try:
                ev("() => { if (window.__b904) { window.__b904.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败：{e}")
            print("  仪器已还原")
        runs.append(rec)

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"], "pre": a["pre"], "k": a["k"],
                  "pre_zeros": a["pre_state"]["zeros"],
                  "pre_armed_count": a["pre_armed_count"],
                  "entry_zeros": a["entry"]["zeros"],
                  "at_end_zeros": a["at_end"]["zeros"],
                  "endpoint_zeros": a["endpoint"]["zeros"],
                  "back_armed_count": a["back_armed_count"],
                  "after_armed_idx": a["after_armed_idx"],
                  "after_zeros": a["after_state"]["zeros"],
                  "prevented_all_false": a["prevented_all_false"]}
                 for a in r["arms"]],
    } for r in runs]
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for row in out["summary"]:
        print(f"  rep{row['rep']}")
        for a in row["arms"]:
            print(f"    {a['label']:<12s} pre={a['pre']}(布了{a['pre_armed_count']}) "
                  f"入场{a['entry_zeros']} → 末尾{a['at_end_zeros']} "
                  f"→ 终点{a['endpoint_zeros']}"
                  f"（往回布了 {a['back_armed_count']} 次）"
                  f" ⇒ Tab×3 得 {a['after_armed_idx']} 末态{a['after_zeros']}")
    print(f"\n== 已写 {OUT} ==")
