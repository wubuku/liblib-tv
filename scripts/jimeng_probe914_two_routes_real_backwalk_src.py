#!/usr/bin/env python3
r"""batch 914 源站探针：**把 913 落空的证伪真正做成** —— 证伪臂的 `j` 必须**越过**目标终点

## 913 为什么落空

913 的 `B` 臂 `j` 填的**就是**直接落在目标终点上的那个 `j`（`49`→40、`60`→51）
⇒ 自适应停止条件一进去就满足、**一次都没往回按**
⇒ `A` 与 `B` **实际是同一条路线** ⇒ 对照根本没成立。

⇒ 钉成通用教训：**证伪臂的参数必须「越过」对照组**，
否则两条臂是同一条、**那一问根本没被问到**（与 899/901 同一条）。

## 这一批：三条「同终点、不同历史」

| 对 | `A` 臂（只往前走） | `B` 臂（往前**越过**，再往回走回来） |
|---|---|---|
| ① | `A-fwd44` ⇒ 终点 35 | `B-fwd45-back35`（`45` 落在 36 ⇒ 往回 1 次） |
| ② | `A-fwd49` ⇒ 终点 40 | `B-fwd55-back40`（`55` 落在 46 ⇒ 往回若干次） |
| ③ | `A-fwd60` ⇒ 终点 51 | `B-fwd65-back51`（`65` 落在 56 ⇒ 往回若干次） |

⚠️ 目标终点是**照着 910–912 实测的「`j` → 终点」表挑的**，不是拍脑袋；
⚠️ `B` 臂的 `j` **必须严格大于** `A` 臂、且**实测终点必须不等于**目标
（否则就是 913 那个错）。

## ⚠️ 探针**自己**拒绝再犯 913 的错（本次最关键的改动）

每条 `B` 臂跑完都记 `design_ok`，而 `design_ok` 同时要求三条：

1. 实测正走终点 **≠** `back_to`（真的越过了）
2. `n_back_presses >= 1`（**真的往回按了**）
3. 往回走之后实测终点 **==** `back_to`（真的走到了目标）

⚠️ 三条里任何一条不成立 ⇒ 该臂 `design_ok = False`、打印 `!! 设计违规`。
**基线不许把 `design_ok = False` 的臂当对照读。**
（这比「记得别写错参数」可靠：错参数会让探针**自己叫出来**，而不是静默产出一份
看起来没问题的同路线对比。）

## 判据纪律

- 仪器**逐字复用** 913/912（`__b914`）
- **每臂之间 reload**；每轮**重复 2 次**；终点**实测**
- ⚠️ **`moved` 是必需字段**（`armed` 会被 `oldValue != '0'` 过滤吞读数 ——
  **904 记过、909 又踩一次**）
- **全程不碰末尾** ⇒ 撞不上绕回（`j ≤ 65` < 实测末尾 75）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe914_two_routes_real_backwalk_src.py
"""

import json

OUT = "/tmp/b914-src-two-routes-real-backwalk.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909/910/913 逐字相同）
SETTLE = 300           # 毫秒

# ⚠️ `B` 臂的 `j` **必须越过**目标终点 —— 这正是 913 写错的地方
ARMS = [
    {"label": "A-fwd44",         "pair": 1, "j": 44, "back_to": None},
    {"label": "B-fwd45-back35",  "pair": 1, "j": 45, "back_to": 35},
    {"label": "A-fwd49",         "pair": 2, "j": 49, "back_to": None},
    {"label": "B-fwd55-back40",  "pair": 2, "j": 55, "back_to": 40},
    {"label": "A-fwd60",         "pair": 3, "j": 60, "back_to": None},
    {"label": "B-fwd65-back51",  "pair": 3, "j": 65, "back_to": 51},
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

# ⚠️ 仪器逐字来自 913 / 912
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b914) { window.__b914.cleanup(); }
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
  window.__b914 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b914;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 913 / 912
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
    cur = ev("() => window.__b914.cursor()")
    if mod:
        page.keyboard.down("Shift")
    page.keyboard.press("Tab")
    if mod:
        page.keyboard.up("Shift")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b914.since(f)", cur)
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


# ⚠️⚠️ **静态自检**：`B` 臂的 `j` 必须在同一对里**严格大于** `A` 臂，
# 否则又变成 913 的同一条路线（这一条是脚本层面的、不依赖实测，
# 所以先在开跑前就挡住）
for _p in (1, 2, 3):
    _a = [s for s in ARMS if s["pair"] == _p and s["back_to"] is None]
    _b = [s for s in ARMS if s["pair"] == _p and s["back_to"] is not None]
    assert len(_a) == 1 and len(_b) == 1, f"pair {_p} 必须恰好一 A 一 B"
    assert _b[0]["j"] > _a[0]["j"], (
        f"pair {_p}：**证伪臂的 j 必须越过对照组**"
        f"（A={_a[0]['j']} / B={_b[0]['j']}）—— 这正是 913 写错的地方")
print(f"== 静态自检过：{len(ARMS)} 臂，3 对，B 的 j 都严格大于 A ==")

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
            back_trace = []
            design = {}
            try:
                blank()
                pre = [tap(names) for _ in range(spec["j"])]
                # ⚠️ **正走结束时的终点要在往回走之前单独存一份** ——
                # 循环里 `cur_end` 会被往回走覆盖掉
                fwd_only_end = snap(names)
                cur_end = fwd_only_end
                # ⚠️ 往回走用**自适应停止条件**，**不是**拍脑袋给次数
                if spec["back_to"] is not None:
                    for _ in range(spec["j"] + 12):
                        if cur_end["zero_one"] == spec["back_to"]:
                            break
                        t = tap(names, mod=True)
                        back_presses.append(t)
                        cur_end = snap(names)
                        back_trace.append({
                            "k": len(back_presses),
                            "armed_idx": t["armed_idx"],
                            "pre_aria": t["pre_aria"],
                            "pre_is_wrapper": t["pre_is_wrapper"],
                            "moved": t["moved"],
                            "zero_after": cur_end["zeros"]})
                endpoint = snap(names)           # ← **实测终点**
                # ⚠️⚠️ **设计自检**：三条全中才算「同终点、不同路线」成立
                design = {
                    "back_to": spec["back_to"],
                    "fwd_end_zeros": fwd_only_end["zeros"],
                    "fwd_overshot": fwd_only_end["zero_one"],
                    "n_back_presses": len(back_presses),
                    "reached_target": None,
                    "design_ok": None,
                }
                if spec["back_to"] is not None:
                    # ① 正走终点 ≠ 目标（真的越过了）
                    # ② 真的往回按了（`n_back_presses >= 1`）
                    # ③ 真的走到了目标
                    design["reached_target"] = (endpoint["zero_one"]
                                                == spec["back_to"])
                    design["design_ok"] = bool(
                        (fwd_only_end["zero_one"] != spec["back_to"])
                        and len(back_presses) >= 1
                        and design["reached_target"])
                else:
                    design["design_ok"] = True     # `A` 臂是基线，不设门槛
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b914) { window.__b914.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            armed_idx = [i for s in after for i in s["armed_idx"]]
            first = next((s["armed_idx"][0] for s in after
                          if s["armed_idx"]), None)
            rec["arms"].append({
                "label": spec["label"], "pair": spec["pair"],
                "j": spec["j"], "back_to": spec["back_to"],
                "design": design,
                "n_back_presses": len(back_presses),
                "back_armed_count": sum(1 for s in back_presses if s["armed"]),
                "back_trace": back_trace,
                "fwd_end_zeros": design.get("fwd_end_zeros"),
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
                "pre_armed_idx_tail": [i for s in pre for i in s["armed_idx"]][-4:],
                "prevented_all_false": all(
                    s["prevented"] is False for s in pre + back_presses + after),
            })
            a = rec["arms"][-1]
            flag = "" if design.get("design_ok") is not False else "　**!! 设计违规**"
            print(f"  往前走 {spec['j']} 次 → 终点 {a['endpoint']['zeros']}"
                  f"，往回按了 **{a['n_back_presses']} 次**"
                  f" ⇒ 回来后 Tab×{N_PRESS} 布 {armed_idx}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**{flag}")
            if back_trace:
                print(f"    往回轨迹（'0' 的落点）："
                      f"{[t['zero_after'] for t in back_trace]}")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"], "pair": a["pair"], "j": a["j"],
                  "back_to": a["back_to"],
                  "design_ok": a["design"].get("design_ok"),
                  "fwd_overshot": a["design"].get("fwd_overshot"),
                  "reached_target": a["design"].get("reached_target"),
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
            ok = {True: "ok", False: "**设计违规**", None: "-"}[a["design_ok"]]
            print(f"    {a['label']:<18s} 设计{ok:<12s} 越到{str(a['fwd_overshot']):<5s}"
                  f" 往回{a['n_back_presses']}次 ⇒ 终点={str(ep):<5s}"
                  f" ⇒ 第一次布的下标 = {str(a['first_armed_idx']):<5s}"
                  f" 全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")
