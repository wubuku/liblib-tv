#!/usr/bin/env python3
r"""batch 930 源站探针（**纯诊断**）：**绕回之后还能不能再来一轮**？两次绕回的间隔是同一个数吗？

## §139 刚拿到的硬纪律

> **「到边界之后的行为」这类问题，预算必须 > 「从边界走回触发点」所需的那一圈**
> —— **而那一圈的长度本身就是要先测出来的东西**，
> **不许拿「按了 N 次没看到」当机制。**

§139 实测（2/2）：正向到末尾 = **第 83 次**；**第 102 次**按前焦点 = `Canvas`（画布根）
⇒ 布 `0`、**绕回** ⇒ **从末尾走回触发点恰好 19 次**。

⚠️ **但 §139 的尾巴只够走完「绕回之后的第一次」** ——
它布到下标 **63** 就用完了预算 ⇒ 所以
**「绕回是不是只此一次」「两次绕回的间隔是不是同一个 19」都还没测到。**

## 930 只问这一件事：**把尾巴拉到能看出第二次绕回**

- 记录**每一个臂事件**（按压序号 + 被布的下标 + **按前焦点是不是画布根**）
- ⭐ 由此能直接算出**每一次绕回发生在第几次按压**、**两次绕回间隔多少**
- 并看**绕回后的那一圈**：有没有再到末尾？**下标 12 还跳不跳**？

## ⚠️ 判据纪律（**929 的教训直接变成静态门**）

- ⚠️⚠️ **929 第一版就是被「3.12 放行、3.11 崩」干掉的** ⇒
  **f-string 表达式里一律不许换行**（`%` 格式化或先算好再打印）
- ⭐ **`TAIL` 必须够走完两圈** —— 静态 assert 用
  **`MIN_TAIL_NODE_PASSES`（圈数）× 一个保守的节点数下界**来表达，
  **不是**去钉实测的节点总数（**节点总数是易变量**）
- **纯读**：普查**纯读**、**不劫持 prototype、不装 MutationObserver**
- **重复 2 轮**；**每轮之间 reload**
- ⚠️ **不许**用「有没有布过」这种**布尔**当唯一证据 ⇒ **记下标序列**
- ⚠️ 落盘排在打印之前；**探针只输出读数**，判读留给基线

## 计费边界

只按 `Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe930_second_wrap_src.py
"""

import json

OUT = "/tmp/b930-src-second-wrap.json"
REPS = 2
SETTLE = 400
N_FWD_CAP = 220        # 正向走到末尾的封顶
MIN_TAIL_NODE_PASSES = 3   # ⭐ 尾巴至少要够走 **3 个节点数**（= 绕回后两圈有余）
TAIL_MIN = 180         # ⚠️ **保守下界**（实测节点数在 74–77 之间，这里只当下界用）
LOOP_FROM_END = 19     # §139 实测：末尾 → 画布根

KEY_FWD = "Tab"

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 919–929 同一把尺子）
# ⚠️ §131 的教训：920 用 `slice(0, 12)` 把规律读反了 ⇒ 这里**一个字都不切**
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
  const aOnCanvasRoot = !!(a && a.closest && a.closest('.react-flow')
                    && !aIsWrapper
                    && (a.getAttribute('aria-label') || '') === 'Canvas');
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    n_wrapper_missing_ti: nodes.length - anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    zero_idx: zeroIdx,          // ⚠️ **完整**列表（一个都不切）
    idl_idx: idlIdx,
    any_ti_idx: anyTiIdx,
    removed, added, changed,
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      on_canvas_root: aOnCanvasRoot,      // ⭐ §908 的绕回触发条件
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
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
# ⭐⭐ **§139 那条硬纪律的机械化**：尾巴必须**够走完两圈**，
#    而「够」要按**节点数**表达（节点数是易变量 ⇒ 只用**保守下界**当下界，
#    **不钉实测值**）
assert MIN_TAIL_NODE_PASSES >= 2, "至少要能看到第二次绕回 ⇒ 圈数下限 2"
assert TAIL_MIN >= MIN_TAIL_NODE_PASSES * 60, \
    "尾巴必须 >= 圈数 × 保守节点数下界，否则又是一次「预算不够就下结论」"
assert LOOP_FROM_END == 19, "§139 实测的「末尾 → 画布根」是 19；改了要连带改基线"
assert REPS >= 2, "一次成功不叫可靠"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti", "n_wrapper_missing_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed", "active")

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
print("== 登录态 %s ==" % out["logged_in"])

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("== 已写 %s（被挡时也要落盘）==" % OUT)
else:
    runs = []
    for rep in range(1, REPS + 1):
        # ⚠️ **每轮之间 reload**（906 已证明这是必须的）
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "tail_min": TAIL_MIN,
               "min_tail_node_passes": MIN_TAIL_NODE_PASSES,
               "loop_from_end": LOOP_FROM_END, "n_fwd_cap": N_FWD_CAP}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        prev_map = tabindex_map()

        def press_once(phase, k, prev_map):
            pre = ev(CENSUS_JS, prev_map)
            page.keyboard.press(KEY_FWD)
            page.wait_for_timeout(SETTLE)
            post = ev(CENSUS_JS, prev_map)
            moved = pre["zero_idx"] != post["zero_idx"]
            presses.append({
                "phase": phase, "k": k,
                "pre": {kk: pre[kk] for kk in KEEP},
                "post": {kk: post[kk] for kk in KEEP},
                "moved": moved,
            })
            return tabindex_map(), moved

        # ---------- 阶段 1：正向走到最后一个下标（自适应）----------
        end_at = None
        for k in range(1, N_FWD_CAP + 1):
            prev_map, _mv = press_once("fwd", k, prev_map)
            p = presses[-1]
            if (end_at is None and p["moved"] and p["post"]["zero_idx"]
                    and p["post"]["zero_idx"][0] == p["post"]["n_nodes"] - 1):
                end_at = k
                break
        n_nodes = presses[-1]["post"]["n_nodes"]
        rec["n_nodes"] = n_nodes
        rec["hit_end_at"] = end_at

        # ---------- 阶段 2：⭐ 尾巴拉到「够看出第二次绕回」 ----------
        # ⚠️ 尾巴长度按**实测节点数**定（**用关系、不钉常量**）：
        #    「至少 MIN_TAIL_NODE_PASSES 个节点数」
        tail_len = max(TAIL_MIN, MIN_TAIL_NODE_PASSES * n_nodes)
        rec["tail_len"] = tail_len
        base = end_at if end_at else 0
        for k in range(base + 1, base + tail_len + 1):
            prev_map, _mv = press_once("tail", k, prev_map)

        rec["presses"] = presses
        rec["tail_presses"] = [p for p in presses if p["phase"] == "tail"]

        # ---------- ⭐ 每一个臂事件：(按压序号, 下标, 按前焦点在不在画布根) ----------
        arms = []
        for p in presses:
            if p["moved"] and p["post"]["zero_idx"]:
                arms.append({
                    "k": p["k"], "phase": p["phase"],
                    "idx": p["post"]["zero_idx"][0],
                    "pre_on_canvas_root": p["pre"]["active"]["on_canvas_root"],
                    "pre_on_wrapper": p["pre"]["active"]["is_wrapper"],
                })
        rec["arms"] = arms
        rec["arm_idx_seq"] = [a["idx"] for a in arms]
        rec["arm_k_seq"] = [a["k"] for a in arms]

        # ---------- 绕回：每一次「布到比上一个臂事件更小的下标」 ----------
        wraps = []
        for i in range(1, len(arms)):
            if arms[i]["idx"] < arms[i - 1]["idx"]:
                wraps.append({
                    "k": arms[i]["k"], "idx": arms[i]["idx"],
                    "prev_idx": arms[i - 1]["idx"],
                    "pre_on_canvas_root": arms[i]["pre_on_canvas_root"],
                    # 两次绕回之间的按压间隔（**「那一圈」的长度**）
                    "gap_presses": arms[i]["k"] - arms[i - 1]["k"],
                })
        rec["wraps"] = wraps
        rec["n_wraps"] = len(wraps)
        rec["wrap_gaps"] = [w["gap_presses"] for w in wraps]
        # 两次**绕回之间**的间隔（跨一整圈）
        rec["wrap_to_wrap"] = [wraps[i]["k"] - wraps[i - 1]["k"]
                               for i in range(1, len(wraps))]
        rec["all_wraps_on_canvas_root"] = all(
            w["pre_on_canvas_root"] for w in wraps) if wraps else None

        # ---------- 绕回后的那一圈：还跳不跳下标 12？到不到末尾？----------
        if wraps:
            k0 = wraps[0]["k"]
            after = [a["idx"] for a in arms if a["k"] > k0]
            rec["after_first_wrap_idx_seq"] = after
            rec["after_first_wrap_max"] = max(after) if after else None
            rec["after_first_wrap_min"] = min(after) if after else None
        else:
            rec["after_first_wrap_idx_seq"] = []
            rec["after_first_wrap_max"] = None
            rec["after_first_wrap_min"] = None
        rec["any_ti_tail_min"] = min(
            [p["post"]["n_wrapper_any_ti"] for p in rec["tail_presses"]] or [None])
        rec["missing_ti_tail_min"] = min(
            [p["post"]["n_wrapper_missing_ti"] for p in rec["tail_presses"]]
            or [None])

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 的教训）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup ----------
        reached_end_ok = (end_at is not None)
        n_tail_ok = len(rec["tail_presses"]) >= MIN_TAIL_NODE_PASSES * n_nodes
        first_wrap_ok = bool(wraps)
        rec["design_ok"] = {
            "reached_end_ok": bool(reached_end_ok),
            "n_tail_ok": bool(n_tail_ok),
            "first_wrap_ok": first_wrap_ok,
            "n_tail": len(rec["tail_presses"]),
            "all_ok": bool(reached_end_ok and n_tail_ok and first_wrap_ok),
        }
        print("  n_nodes=%d | 到末尾@%s次 | 尾巴 %d 次"
              % (n_nodes, end_at, len(rec["tail_presses"])))
        print("  臂事件 %d 次；绕回 %d 次：%s"
              % (len(arms), rec["n_wraps"],
                 [(w["k"], w["idx"], w["pre_on_canvas_root"],
                   w["gap_presses"]) for w in wraps]))
        if rec["wrap_to_wrap"]:
            print("  两次绕回之间的按压间隔 = %s" % rec["wrap_to_wrap"])
        print("  绕回后那一圈：min=%s max=%s（前 14 个 %s）"
              % (rec["after_first_wrap_min"], rec["after_first_wrap_max"],
                 rec["after_first_wrap_idx_seq"][:14]))
        print("  => design_ok=%s" % rec["design_ok"]["all_ok"])

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print("  rep%s design_ok=%s n_nodes=%s 尾巴 %s 次"
              % (r["rep"], r["design_ok"]["all_ok"], r["n_nodes"],
                 r["design_ok"]["n_tail"]))
        print("    绕回 %d 次，发生在按压 %s"
              % (r["n_wraps"], [w["k"] for w in r["wraps"]]))
        print("    全部绕回的按前焦点都在画布根 = %s"
              % r["all_wraps_on_canvas_root"])
        print("    两次绕回间隔 = %s" % r["wrap_to_wrap"])
    print("\n== 已写 %s ==" % OUT)
