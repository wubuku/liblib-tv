#!/usr/bin/env python3
r"""batch 910 源站探针：**重扫**「终点 → 起点」的映射（907 作废后的重做）

## 907 为什么作废（908 已查清）

907 想扫「终点 → 起点」，结果 6 条臂的终点**全都是下标 `0`** ——
正序走查**每条都绕回了** ⇒ 一个能区分的终点都没扫到。
成因：**走查按了 `节点数 + 25` 次，而 908 实测绕回恰好在第 103 次**（78 节点）
⇒ `+25` 正好撞上绕回点。

## 这一批**换掉那个设计**，不是只改停止条件

907 的做法是「先走到末尾、再往回按 `k` 次」⇒ 终点被走查预算绑架。
910 改成**直接扫「从画布根按几次 `Tab`」** `j`：

| | 907（作废） | 910（这一批） |
|---|---|---|
| 变量 | 往回按 `k` 次 | **从画布根按 `j` 次** |
| 怎么到那个终点 | 先走到末尾（**预算 `n+25` 会撞上绕回**），再往回 | **直接按 `j` 次**，全程不碰末尾 |
| 终点 | **推算/撞出来** | **实测**（`j` 会被内层控件吃掉一部分，按压数 ≠ 步数） |

⇒ `j ∈ {0,3,8,15,25,40,55,65}`。`j=0` 覆盖「从未 Tab 过」那一格，
`j=55/65` 用来够到 906/908 关心的 **56 / 58 / 59** 附近。
**`j` 最大 65 < 末尾（实测 75）⇒ 结构上不可能绕回。**

## 判据纪律（把 909 踩的坑一并修掉）

- 仪器**逐字复用** 908（`__b910`）
- **每臂之间 reload**；每轮**重复 2 次**
- ⚠️ **两条序列一起记**：`armed_idx` **和** `'0'` 动没动
  （`oldValue != '0'` 的过滤会把「本来就是 `'0'`、又被重写一次」的那次算漏 ——
  **904 记过、909 又踩一次**）⇒ `moved` 是**必需字段**，不是可选
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**；
  终点**实测**、**不拿公式当读数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe910_endpoint_to_start_rescan_src.py
"""

import json

OUT = "/tmp/b910-src-endpoint-start-rescan.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909 逐字相同）
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

JS = [0, 3, 8, 15, 25, 40, 55, 65]   # 扫的变量：从画布根按几次
                                    # ⚠️ 最大 65 < 实测末尾 75 ⇒ 撞不上绕回

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

# ⚠️ 仪器逐字来自 908
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b910) { window.__b910.cleanup(); }
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
  window.__b910 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b910;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 908
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
      is_wrapper: !!(a && a.classList
                  && a.classList.contains('react-flow__node'))}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def snap(names):
    st = ev(STATE_JS)
    zs = [names.get(t, {}).get("idx") for t in st["zeros"]]
    return {"zeros": zs, "zero_one": (zs[0] if len(zs) == 1 else zs),
            "active_aria": st["active"]["aria"][:22],
            "active_is_wrapper": st["active"]["is_wrapper"]}


def tap(names):
    """一次按压：按前焦点 + 布了什么 + 按后落点 + 按后 `'0'`（**带 moved**）。"""
    before = snap(names)
    cur = ev("() => window.__b910.cursor()")
    page.keyboard.press("Tab")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b910.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    after = snap(names)
    return {"armed": armed,
            "armed_idx": [names.get(a[4:], {}).get("idx")
                          for a in armed if a.startswith("tid:")],
            "pre_aria": before["active_aria"],
            "pre_is_wrapper": before["active_is_wrapper"],
            "zero_before": before["zeros"], "zero_after": after["zeros"],
            # ⚠️ 909 踩过的坑：`armed` 会被 oldValue 过滤吞读数 ⇒ moved 是必需的
            "moved": before["zeros"] != after["zeros"],
            "land_aria": [f["target_aria"] for f in fi],
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


def blank():
    sp = ev(BLANK_JS)
    if sp:
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)
    return sp


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
print(f"== 登录态 {out['logged_in']} ==")

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
        for j in JS:
            # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(9000)
            page.set_viewport_size({"width": 1512, "height": 1200})
            page.wait_for_timeout(2500)
            names = ev(NAMES_JS)
            n = len(names)
            rec.setdefault("n_nodes", n)
            inst = ev(INSTALL_JS)
            print(f"\n--- rep{rep} j={j}（{n} 个节点，"
                  f"instrument={inst.get('ok')}）---")
            try:
                blank()
                pre = []
                for _ in range(j):               # **直接按 j 次**，不碰末尾
                    pre.append(tap(names))
                endpoint = snap(names)           # ← **实测终点**
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b910) { window.__b910.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            armed_idx = [i for s in after for i in s["armed_idx"]]
            first = next((s["armed_idx"][0] for s in after
                          if s["armed_idx"]), None)
            rec["arms"].append({
                "j": j, "endpoint": endpoint,
                "pre_armed_count": sum(1 for s in pre if s["armed"]),
                "pre_moved": [s["moved"] for s in pre],
                "after_per_press": [
                    {"armed_idx": s["armed_idx"],
                     "pre_aria": s["pre_aria"],
                     "pre_is_wrapper": s["pre_is_wrapper"],
                     "zero_before": s["zero_before"],
                     "zero_after": s["zero_after"],
                     "moved": s["moved"],
                     "land_aria": s["land_aria"][:1],
                     "prevented": s["prevented"]}
                    for s in after],
                "after_armed_idx": armed_idx,
                "after_moved": [s["moved"] for s in after],
                "first_armed_idx": first,
                "prevented_all_false": all(
                    s["prevented"] is False for s in pre + after),
            })
            a = rec["arms"][-1]
            print(f"  实测终点 **{a['endpoint']['zeros']}**（按了 {j} 次）"
                  f" ⇒ 回来后 Tab×{N_PRESS} 布 {armed_idx}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"j": a["j"],
                  "endpoint_zeros": a["endpoint"]["zeros"],
                  "first_armed_idx": a["first_armed_idx"],
                  "after_armed_idx": a["after_armed_idx"],
                  "after_moved": a["after_moved"],
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
            print(f"    j={a['j']:<3d} 实测终点={str(ep):<5s} ⇒ "
                  f"第一次布的下标 = {str(a['first_armed_idx']):<5s} "
                  f"全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")
