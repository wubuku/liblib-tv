#!/usr/bin/env python3
r"""batch 922 源站探针（**纯诊断**）：**把 921 的「臂事件三动作 + 滚动窗口」在反向也做一遍** —— 是同一条规则，还是**方向不对称**？

## 921 已查清（正向 `Tab`）

- **① 初始化**（第一次布，只有一次）：给**所有**节点写上 `tabindex`（1×'0' + 75×'-1'）
- **② 之后每次「臂事件」恰好三件事**：
  `removed` = **上一个**臂事件的下标（属性**整个移除**）、`added` = **上上个**的
  （**写回** `'-1'`）、`changed` = **本次**被布的（`'-1'`→`'0'`）⇒ 24/24
- **不变式**：任何时刻**恰好 1 个**本体没有 `tabindex` 属性 ⇒ `n_wrapper_any_ti` 恒 75

⚠️ **那个滚动窗口深 2**（要看「上一个」和「上上个」）⇒ **至少要 3 次臂事件**
才能把它和任何别的规律分开 ⇒ 这就是本探针**最关键的一道设计门**。

## 922 只问一件事：**反向是同一条规则，还是方向不对称？**

⚠️ 不能直接对空白处按 `Shift+Tab` 就开始测 —— 917/921 实测：**反向从画布根出发
先把焦点带出画布、把整页反向走一遍**（约 28 次死按压）⇒ 那些按压**一次都不布**，
拿来当「反向臂事件」测会**得到完全虚假的读数**。
⇒ 所以分两段：
- **A 段（setup，不算臂事件读数）**：点空白后连按 `Shift+Tab`，
  **自适应停止条件 = 焦点真的落到某个节点本体上**（不是拍脑袋给次数；上限只封顶）
- **B 段（真正被测的）**：从那个本体开始，每次按压都记**整张表 + 逐次 delta**

## ⭐ 同一次运行里**正反两向都测**（对照）

921 是在**另一次运行**里测的正向。跨 run 比 ⇒ 混了「机制会不会在两次运行之间变」。
所以本探针每轮 **reload 两次**：一次跑 `rev`、一次跑 `fwd`（`fwd` 从画布根直接开始，
第一次按压就布 ⇒ 天然有干净的臂历史）⇒ **同 run、同节点集、同一份探针代码路径**。

## 设计门（`design_ok`，每轮每臂各判一次）

1. `entered_ok` —— 真的进到画布内、反向起点确实落在**节点本体**上
   （否则 B 段量的根本不是「反向臂事件」）
2. `n_armed_ok` —— **B 段至少 3 次臂事件**（⭐ 滚动窗口深 2 的硬要求）
3. 另有静态 assert：不许再出现 920 那种 `slice(0, 12)`（**切片会把规律读反**）

⚠️ **`moved` 是必需字段**（904 记过、909 又踩一次）；`armed` 会在非 `.react-flow__node`
的元素上触发 ⇒ **停止条件只能用 `moved`**。
⚠️ 探针**只输出读数**，判读留给基线（`design_ok` 只判 setup、不判机制）。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe922_reverse_arm_window_src.py
"""

import json

OUT = "/tmp/b922-src-reverse-arm-window.json"
REPS = 2
TRIALS = ("rev", "fwd")
SETTLE = 400
N_MEASURE = 14            # 与 921 同量级，够攒出 ≥3 次臂事件
ENTRY_CAP = 60            # ⚠️ **只是封顶**，停止条件是自适应的（见 A 段）

# ⚠️ 键名提到模块级复用（A 段和 B 段都要用）
KEY_FWD = "Tab"
KEY_REV = "Shift+Tab"

# ⚠️ 臂 → 键的映射提到模块级（断言和真跑共用一份 ⇒ 断言才不是摆设）
TRIAL_KEYS = (("rev", KEY_REV), ("fwd", KEY_FWD))

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️ A 段用**轻量**读数（只判「进没进画布」）—— 全表留给 B 段，省时间
LIGHT_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [];
  for (let i = 0; i < nodes.length; i++)
    if (nodes[i].getAttribute('tabindex') === '0') zeroIdx.push(i);
  const a = document.activeElement;
  const isW = !!(a && a.classList && a.classList.contains('react-flow__node'));
  return {zero_idx: zeroIdx, n_nodes: nodes.length, is_wrapper: isW,
          wrapper_idx: isW ? nodes.indexOf(a) : null,
          aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null};
}"""

# ⚠️⚠️ **本批的核心读数**：**整张表** + **逐次 delta**（与 921 同一套）
# ⚠️ 920 最大的问题就是 `slice(0, 12)` ⇒ 这里**一个字都不切**
CENSUS_JS = """(prev) => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [], idlIdx = [];
  const cur = {};                       // idx -> tabindex 值（null 表示没这个属性）
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const ti = n.getAttribute('tabindex');
    cur[i] = ti;
    if (ti === '0') zeroIdx.push(i);
    if (n.tabIndex >= 0) idlIdx.push(i);
  }
  const added = [], removed = [], changed = [];
  const anyTiIdx = [];
  for (let i = 0; i < nodes.length; i++) if (cur[i] !== null) anyTiIdx.push(i);
  if (prev) {
    for (let i = 0; i < nodes.length; i++) {
      const was = (i in prev) ? prev[i] : null;
      if (was === null && cur[i] !== null) added.push(i);
      else if (was !== null && cur[i] === null) removed.push(i);
      else if (was !== cur[i]) changed.push([i, was, cur[i]]);
    }
  }
  const a = document.activeElement;
  const aIsWrapper = !!(a && a.classList
                    && a.classList.contains('react-flow__node'));
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    zero_idx: zeroIdx,          // ⚠️ **完整**列表（920 的教训：一个都不切）
    idl_idx: idlIdx,
    any_ti_idx: anyTiIdx,
    removed, added, changed,
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
    },
  };
}"""

MAP_JS = """() => { const o = {};
  [...document.querySelectorAll('.react-flow__node')]
  .forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });
  return o; }"""

# ⚠️ **探针自己长防线**（912 起的纪律：设计错误要当场自己叫出来）
# ⚠️ 920 用 `slice(0, 12)` 把规律读反了 ⇒ 这里直接静态 forbid
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（920 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "B 段必须用整张表 + 逐次 delta"
# ⚠️ 两个方向都必须真的被跑到（不许只测一向就下「对称/不对称」的结论）
assert {t for t, _ in TRIAL_KEYS} == set(TRIALS), "两个方向都要测"
assert len({k for _, k in TRIAL_KEYS}) == 2, "两个方向必须是两个不同的键"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed", "active")


def load():
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(9000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2500)


out = {}
load()
# ⚠️ 906 的教训：**一次没命中不等于没登录** ⇒ 未命中就再等 8s 复判一次
out["login_check_attempts"] = []
for attempt in (1, 2):
    n = page.locator('button[aria-label="音频"]').count()
    out["login_check_attempts"].append(
        {"attempt": attempt, "n_audio_rail_button": n,
         "n_nodes": page.locator(".react-flow__node").count()})
    if n > 0:
        break
    if attempt == 1:
        page.wait_for_timeout(8000)
        n2 = page.locator('button[aria-label="音频"]').count()
        out["login_check_attempts"].append(
            {"attempt": "1b-再等8s", "n_audio_rail_button": n2,
             "n_nodes": page.locator(".react-flow__node").count()})
        if n2 > 0:
            break

out["logged_in"] = any(a["n_audio_rail_button"] > 0
                       for a in out["login_check_attempts"])
print(f"== 登录态 {out['logged_in']} ==")


def run_trial(trial, key):
    """跑一臂：reload → 点空白 → A 段（rev 才有）→ B 段被测 N 次。"""
    load()
    rec = {"trial": trial, "key": key, "n_measure": N_MEASURE,
           "entry_cap": ENTRY_CAP}

    sp = ev(BLANK_JS)
    if sp:
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)
    rec["blank_hit"] = sp
    rec["census_at_blank"] = ev(CENSUS_JS, None)

    # ---------- A 段（setup）：rev 要先走进画布 ----------
    entry = []
    if trial == "rev":
        for i in range(ENTRY_CAP):
            pre_l = ev(LIGHT_JS)
            page.keyboard.press(key)
            page.wait_for_timeout(SETTLE)
            post_l = ev(LIGHT_JS)
            moved_l = pre_l["zero_idx"] != post_l["zero_idx"]
            entry.append({"k": i + 1, "moved": moved_l,
                          "is_wrapper": post_l["is_wrapper"],
                          "wrapper_idx": post_l["wrapper_idx"],
                          "zero_idx": post_l["zero_idx"],
                          "aria": post_l["aria"]})
            # ⚠️ 自适应停止：**焦点真的落到节点本体上**才算进到画布内
            if post_l["is_wrapper"]:
                break
    rec["entry"] = entry
    rec["n_entry_used"] = len(entry)
    rec["focus_on_body_at_entry"] = bool(
        entry and entry[-1]["is_wrapper"]) if trial == "rev" else None
    # ⚠️ 916 记过：`armed` 会在非 `.react-flow__node` 的元素上触发
    #    ⇒ 「有没有咬到」只能用 `moved` 判
    rec["entry_moved_at_end"] = bool(entry and entry[-1]["moved"]) \
        if trial == "rev" else None

    # ---------- B 段（真正被测的）----------
    prev_map = tabindex_map()
    presses = []
    arm_seq = []          # ⚠️ 每次臂事件后被布的下标，**按时间顺序**
    for k in range(N_MEASURE):
        pre_c = ev(CENSUS_JS, prev_map)      # 按之前普查（带 delta）
        page.keyboard.press(key)
        page.wait_for_timeout(SETTLE)
        post_c = ev(CENSUS_JS, prev_map)     # 按之后普查（带 delta）
        moved_c = pre_c["zero_idx"] != post_c["zero_idx"]
        if moved_c:
            arm_seq.append(post_c["zero_idx"])
        presses.append({
            "k": k + 1,
            "pre": {kk: pre_c[kk] for kk in KEEP},
            "post": {kk: post_c[kk] for kk in KEEP},
            "moved": moved_c,
        })
        prev_map = tabindex_map()
    rec["presses"] = presses
    rec["arm_seq"] = arm_seq
    rec["n_armed"] = len(arm_seq)

    # ---------- 设计门：只判 setup，不判机制 ----------
    if trial == "rev":
        entered_ok = (rec["n_entry_used"] < ENTRY_CAP
                      and rec["focus_on_body_at_entry"])
    else:
        # fwd 从画布根直接开始：第一次按压就布 ⇒ 有臂事件即算进到画布内
        entered_ok = rec["n_armed"] >= 1
    n_armed_ok = rec["n_armed"] >= 3      # ⭐ 滚动窗口深 2 的硬要求
    rec["design_ok"] = {
        "entered_ok": bool(entered_ok),
        "n_armed_ok": bool(n_armed_ok),
        "n_armed": rec["n_armed"],
        "all_ok": bool(entered_ok and n_armed_ok),
    }
    print(f"  [{trial}] A 段 {rec['n_entry_used']} 次 "
          f"(落本体={rec['focus_on_body_at_entry']}) → "
          f"B 段 {N_MEASURE} 次、臂事件 {rec['n_armed']} 次 "
          f"arm_seq={arm_seq} ⇒ design_ok={rec['design_ok']['all_ok']}")
    return rec


if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ **被挡时也要落盘**（906 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        # ⚠️ ⚠️ 每个臂都 **reload**（906 已证明必须）⇒ 两向各有干净的臂历史
        for trial, key in TRIAL_KEYS:
            rec = run_trial(trial, key)
            rec["rep"] = rep
            runs.append(rec)
            out["runs"] = runs
            # ⚠️ 每臂都先落盘（防中途崩了读数全丢）
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} [{r['trial']}] "
              f"design_ok={r['design_ok']['all_ok']} "
              f"n_armed={r['n_armed']} n_entry={r['n_entry_used']}")
        for p in r["presses"]:
            a, b = p["post"], p["pre"]
            print(f"    第{p['k']:>2d}次 any_ti {b['n_wrapper_any_ti']}→"
                  f"{a['n_wrapper_any_ti']} | removed={a['removed']} "
                  f"added={a['added']} changed={a['changed']} "
                  f"| ti0 {b['zero_idx']}→{a['zero_idx']} "
                  f"| 焦点idx={a['active']['wrapper_idx']}")
    print(f"\n== 已写 {OUT} ==")
