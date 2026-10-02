#!/usr/bin/env python3
"""batch 907 源站探针：**终点 → 起点**的映射到底长什么样？

## 906 留下的唯一硬缺口

906 证了两件事、也留了一个洞：

**已证**：落点**跟着终点走**（终点 58 ⇒ 布 `[2,3,4,5]`；终点 59 ⇒ 布 `[0,1,2,3]`），
**904 那个 `[2,3]` 不是异常值**。

**已知但没刻画**：终点 → 起点 的映射长什么样。到目前为止只攒下几个点：

| 终点 | 回来后第一次布的下标 |
|---|---|
| ∅（从未 Tab 过） | 0 |
| 0 | 1 |
| **56** | **12** |
| **58** | **2** |
| 59 | 0 |
| 60 | 0 |
| 75 | 0 |

⇒ **看不出单调、也看不出线性**；0 / 56 / 58 给出非 0，其余给 0。
⚠️ **不许**据此编规则（那是 §899「不许编判据去凑」）。

## 这一批只做一件事：**连续扫终点**

`k` = 往回按几次。904 已证终点 `= 88 − k`（在 k∈{28,30,32} 上）⇒
**扫 `k` 就是扫终点**。每臂之间 reload（906 已证明这是必须的），
每臂都记**实际落到的终点**（不拿公式当读数用，节点总数是易变量）。

`k ∈ {0, 3, 8, 15, 25, 40}` —— 刻意在已知的 0 / 56 / 58 / 59 附近取点，
也覆盖大跨度，看那个分界到底在哪。

## 判据纪律

- 仪器**逐字复用** 906（`__b907`）
- **每臂之间 reload**（906 已证明）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**；终点**实测**、不套公式
- 每轮**重复 2 次**；臂序固定
- **落盘排在打印之前**；**被挡时也要落盘**
- 登录判据**未命中就重试**（906 第一版把偶发加载失败报成 BLOCKED 的教训）
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe907_endpoint_to_start_map_src.py
"""

import json

OUT = "/tmp/b907-src-endpoint-start-map.json"
REPS = 2
N_PRESS = 8            # 回来之后按几次（与 906 逐字相同，好比）
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

KS = [0, 3, 8, 15, 25, 40]     # 扫的变量：往回按几次 ⇒ 等价于扫终点

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
  if (window.__b907) { window.__b907.cleanup(); }
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
  window.__b907 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b907;
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
    """一次按压：**按压前**的焦点 + 布了什么 + 按压后的落点（逐字来自 906）。"""
    pre = ev(STATE_JS)["active"]
    cur = ev("() => window.__b907.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b907.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    return {"armed": armed,
            "pre_aria": pre["aria"][:20], "pre_in_node": pre["in_node"],
            "pre_tid": pre["tid"],
            "focus_aria": [f["target_aria"] for f in fi],
            "focus_is_node": [f["target_is_node_wrapper"] for f in fi],
            "focus_tid": [f["target"] for f in fi],
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {}
page.goto(URL, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(3000)
# ⚠️ 906 的教训：**一次没命中不等于没登录** ⇒ 未命中就再等 8s 复判一次
out["login_check_attempts"] = []
for attempt in (1, 2):
    n = page.locator('button[aria-label="音频"]').count()
    out["login_check_attempts"].append(
        {"attempt": attempt, "n_audio_rail_button": n,
         "n_react_flow": page.locator(".react-flow").count(),
         "n_nodes": page.locator(".react-flow__node").count()})
    if n > 0:
        break
    if attempt == 1:
        page.wait_for_timeout(8000)
        n2 = page.locator('button[aria-label="音频"]').count()
        out["login_check_attempts"].append(
            {"attempt": "1b-再等8s", "n_audio_rail_button": n2,
             "n_react_flow": page.locator(".react-flow").count(),
             "n_nodes": page.locator(".react-flow__node").count()})
        if n2 > 0:
            break

out["logged_in"] = any(a["n_audio_rail_button"] > 0
                       for a in out["login_check_attempts"])
print(f"== 登录态 {out['logged_in']}（尝试 {out['login_check_attempts']}）==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ **被挡时也要落盘** —— 被挡恰恰是最该留痕的一次（906 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        rec = {"rep": rep, "arms": []}
        for k in KS:
            # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(9000)
            page.set_viewport_size({"width": 1512, "height": 1200})
            page.wait_for_timeout(2500)
            names = ev(NAMES_JS)
            n = len(names)
            rec.setdefault("n_nodes", n)
            inst = ev(INSTALL_JS)
            print(f"\n--- rep{rep} k={k}（{n} 个节点，"
                  f"instrument={inst.get('ok')}）---")

            def blank():
                sp = ev(BLANK_JS)
                if sp:
                    page.mouse.click(sp[0], sp[1])
                    page.wait_for_timeout(900)
                return sp

            def snap():
                st = ev(STATE_JS)
                return {"zeros": [names.get(t, {}).get("idx") for t in st["zeros"]],
                        "n_zero": st["n_zero"],
                        "active_in_node": st["active"]["in_node"],
                        "active_aria": st["active"]["aria"][:20]}

            try:
                blank()
                entry = snap()
                fwd = []
                for _ in range(n + 25):        # 与 902–906 同：走到末尾
                    fwd.append(press(page))
                at_end = snap()
                back = [press(page, mod=True) for _ in range(k)]
                endpoint = snap()              # ← **实测终点**，不套公式
                blank()
                after = [press(page) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b907) { window.__b907.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            def idx_of(a):
                return names.get(a[4:], {}).get("idx") if a.startswith("tid:") else None

            armed_idx = [idx_of(a) for s in after for a in s["armed"]]
            first = next((i for i in armed_idx if i is not None), None)
            rec["arms"].append({
                "k": k,
                "entry": entry, "at_end": at_end, "endpoint": endpoint,
                "fwd_armed_count": sum(1 for s in fwd if s["armed"]),
                "back_armed_count": sum(1 for s in back if s["armed"]),
                "after_per_press": [
                    {"armed_idx": [idx_of(a) for a in s["armed"]],
                     "pre_aria": s["pre_aria"], "pre_in_node": s["pre_in_node"],
                     "pre_idx": idx_of(s["pre_tid"]) if s["pre_tid"] else None,
                     "focus_aria": s["focus_aria"],
                     "focus_is_node": s["focus_is_node"],
                     "focus_idx": [idx_of(t) for t in s["focus_tid"]],
                     "prevented": s["prevented"]}
                    for s in after],
                "after_armed_idx": armed_idx,
                "first_armed_idx": first,     # ← **这一批要的那个数**
                "prevented_all_false": all(
                    s["prevented"] is False for s in fwd + back + after),
            })
            a = rec["arms"][-1]
            print(f"  入场{a['entry']['zeros']} → 末尾{a['at_end']['zeros']} "
                  f"→ 终点**{a['endpoint']['zeros']}**"
                  f"（back布了{a['back_armed_count']} 次）")
            print(f"  ⇒ 回来后 Tab×{N_PRESS} 布 {a['after_armed_idx']}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"k": a["k"],
                  "endpoint_zeros": a["endpoint"]["zeros"],
                  "back_armed_count": a["back_armed_count"],
                  "first_armed_idx": a["first_armed_idx"],
                  "after_armed_idx": a["after_armed_idx"],
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
            ep = a["endpoint_zeros"][0] if len(a["endpoint_zeros"]) == 1 else (
                a["endpoint_zeros"] or "∅")
            print(f"    k={a['k']:<3d} 终点={str(ep):<5s} ⇒ "
                  f"第一次布的下标 = {str(a['first_armed_idx']):<5s} "
                  f"全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")
