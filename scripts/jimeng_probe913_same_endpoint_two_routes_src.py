#!/usr/bin/env python3
r"""batch 913 源站探针：**换方法** —— 同一个终点、不同的历史，起点跟不跟终点走？

## 910–912 夹到 1 宽就停手了

| 实测终点 | 起点 | 边界 |
|---|---|---|
| `≤ 35` | 0 | `35 \| 36` |
| `36…40` | 11 | |
| `≥ 41` | 12 | `40 \| 41` |

⚠️ 912 已经钉死：**收窄的是「经验边界」、不是「理解」**；
**为什么是 0/11/12、为什么分界在那两处，全部未查明** ⇒
**继续夹已经到方法极限了** ⇒ 这一批**换方法**。

## 这一批的问题：**起点是「终点的函数」吗？**

910–912 每条臂的路线都是**同一条**：从画布根连按 `j` 次 `Tab` ⇒ 点空白 ⇒ 回来按 `Tab`。
⇒ **「终点」和「历史」是共变的** ⇒ 那张映射表**分不清**
起点到底跟着**终点**走、还是跟着**某段别的历史**走。

**证伪设计：同一个终点、两条不同的路线。**

| 臂 | 路线 | 终点 |
|---|---|---|
| `A-fwd49` | 只往前走 49 次 | 40（912 已测 ⇒ 起点 **11**） |
| `B-fwd49-back` | 往前走 49 次，**再往回走到终点 40** | 40 |
| `A-fwd60` | 只往前走 60 次 | 51（按映射 ⇒ 起点 **12**） |
| `B-fwd60-back` | 往前走 60 次，**再往回走到终点 51** | 51 |

⚠️ 往回走用**自适应停止条件**（「`'0'` 到目标就停」），**不是**拍脑袋给次数
（907/908 的教训）⇒ 并**记下实际往回按了几次**。

⇒ 若起点**只**跟着终点走 ⇒ `A` 与 `B` **逐条相同** ⇒ 那张映射表可信。
⇒ 若 `A` 与 `B` 不同 ⇒ **终点不是唯一自变量** ⇒ **910–912 的映射要重画**。

## 判据纪律

- 仪器**逐字复用** 912（`__b913`）
- **每臂之间 reload**；每轮**重复 2 次**；终点**实测**
- ⚠️ **`moved` 是必需字段**（`armed` 会被 `oldValue != '0'` 过滤吞读数 ——
  **904 记过、909 又踩一次**）
- **全程不碰末尾** ⇒ 撞不上绕回（`j ≤ 60` < 实测末尾 75）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe913_same_endpoint_two_routes_src.py
"""

import json

OUT = "/tmp/b913-src-same-endpoint-two-routes.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909/910 逐字相同）
SETTLE = 300           # 毫秒

# 目标终点是**照着 910–912 那张表挑的**，不是拍脑袋：
#   终点 40 ⇒ 映射说起点 11；终点 51 ⇒ 映射说起点 12
ARMS = [
    {"label": "A-fwd49",       "j": 49, "back_to": None},
    {"label": "B-fwd49-back",  "j": 49, "back_to": 40},
    {"label": "A-fwd60",       "j": 60, "back_to": None},
    {"label": "B-fwd60-back",  "j": 60, "back_to": 51},
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

# ⚠️ 仪器逐字来自 912
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b913) { window.__b913.cleanup(); }
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
  window.__b913 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b913;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 912
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


def tap(names, mod=False):
    """一次按压：按前焦点 + 布了什么 + 按后落点 + 按后 `'0'`（**带 moved**）。"""
    before = snap(names)
    cur = ev("() => window.__b913.cursor()")
    if mod:
        page.keyboard.down("Shift")
    page.keyboard.press("Tab")
    if mod:
        page.keyboard.up("Shift")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b913.since(f)", cur)
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
        for spec in ARMS:
            # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(9000)
            page.set_viewport_size({"width": 1512, "height": 1200})
            page.wait_for_timeout(2500)
            names = ev(NAMES_JS)
            n = len(names)
            rec.setdefault("n_nodes", n)
            inst = ev(INSTALL_JS)
            print(f"\n--- rep{rep} {spec['label']}（{n} 个节点，"
                  f"instrument={inst.get('ok')}）---")
            back_presses = []
            try:
                blank()
                pre = [tap(names) for _ in range(spec["j"])]
                at_fwd_end = snap(names)
                # ⚠️ 往回走用**自适应停止条件**，**不是**拍脑袋给次数
                if spec["back_to"] is not None:
                    for _ in range(spec["j"] + 10):
                        if at_fwd_end["zero_one"] == spec["back_to"]:
                            break
                        back_presses.append(tap(names, mod=True))
                        at_fwd_end = snap(names)
                endpoint = snap(names)           # ← **实测终点**
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b913) { window.__b913.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            armed_idx = [i for s in after for i in s["armed_idx"]]
            first = next((s["armed_idx"][0] for s in after
                          if s["armed_idx"]), None)
            rec["arms"].append({
                "label": spec["label"], "j": spec["j"],
                "back_to": spec["back_to"],
                "n_back_presses": len(back_presses),
                "back_armed_count": sum(1 for s in back_presses if s["armed"]),
                "endpoint": endpoint,
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
                    s["prevented"] is False for s in pre + back_presses + after),
            })
            a = rec["arms"][-1]
            print(f"  往前走 {spec['j']} 次 → {a['endpoint']['zeros']}"
                  f"，再往回按了 **{a['n_back_presses']} 次**"
                  f" ⇒ 回来后 Tab×{N_PRESS} 布 {armed_idx}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"], "j": a["j"],
                  "back_to": a["back_to"],
                  "n_back_presses": a["n_back_presses"],
                  "endpoint_zeros": a["endpoint"]["zeros"],
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
            ep = (a["endpoint_zeros"][0]
                  if len(a["endpoint_zeros"]) == 1 else (a["endpoint_zeros"] or "∅"))
            print(f"    {a['label']:<15s} 往回{a['n_back_presses']}次 "
                  f"⇒ 终点={str(ep):<5s} ⇒ 第一次布的下标 = "
                  f"{str(a['first_armed_idx']):<5s} 全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")
