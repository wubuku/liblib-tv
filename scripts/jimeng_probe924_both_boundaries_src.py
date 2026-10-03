#!/usr/bin/env python3
r"""batch 924 源站探针（**纯诊断**）：**把两个边界在同一次运行里都穿过去** —— 到边界是**停手**，还是**绕回**？

## §133 已经查清的

923 实测（2/2）：滚动窗口是**一条不分方向的全局臂事件流**
（`removed` = 上一个臂事件、**34/34 全中**）⇒ **方向对称**。
但它只把反向退到 **3** ⇒ **两个边界都没被反向测到**。

## 这一批只问一件事：**穿过头之后会怎样**

896（MM.1）早已在**正向**测到：走到末尾（`max_dom_idx_armed=75`）**就停手、
绝不绕回**。⚠️ **反向那条边界从来没被测过** ——
「到下界 0 之后是停手、还是绕回到 75」**未验证**。

⇒ 所以本批**在同一次运行里把两个边界都穿过去**：

- **正向阶段**：`Tab` 连按，**一直按到布上下标 75**，然后**继续按 `PAST` 次**
- **反向阶段**：`Shift+Tab` 连按，**一直按到布上下标 0**，然后**继续按 `PAST` 次**

⇒ 两向**互相是对照**，而不是「正向有证据、反向靠推测」。

## ⚠️ 停止条件不许拍脑袋给次数

- 正向的停止条件 = **真的布到了最后一个下标**，**且**之后又按了 `PAST` 次
- 反向的停止条件 = **真的布到了 0**，**且**之后又按了 `PAST` 次
- `FWD_CAP` / `REV_CAP` **只是封顶**，不是判据

## 设计门（`design_ok`，每轮判一次）

1. `focus_on_body_ok` —— 翻向那一刻焦点真的落在**节点本体**上
2. `fwd_reached_end_ok` —— 正向**真的布到了最后一个下标**（不是猜的）
3. `rev_reached_start_ok` —— 反向**真的布到了 0**
4. `n_past_ok` —— 两向在**越界之后**各自都至少按了 `PAST` 次
   （**不然「没绕回」这个结论就没有样本**）

⚠️ **`moved` 是必需字段**；`armed` 会在非 `.react-flow__node` 的元素上触发
⇒ 「有没有咬到」**只能用 `moved`** 判。
⚠️ 探针**只输出读数**，判读留给基线（`design_ok` 只判 setup、不判机制）。
⚠️ **节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ 只记**最后那个下标**，
**不许**把它当常量钉进判据。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe924_both_boundaries_src.py
"""

import json

OUT = "/tmp/b924-src-both-boundaries.json"
REPS = 2
SETTLE = 400
PAST = 10            # 越界之后**继续按**的次数（不然「没绕回」就没有样本）
FWD_CAP = 110        # ⚠️ 只是封顶
REV_CAP = 110        # ⚠️ 只是封顶

KEY_FWD = "Tab"
KEY_REV = "Shift+Tab"

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 921/922/923 同一套）
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
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    zero_idx: zeroIdx,          // ⚠️ **完整**列表（一个都不切）
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
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
assert PAST >= 5, "越界后至少要再按几次，否则「没绕回」没有样本"
assert (KEY_FWD, KEY_REV) == ("Tab", "Shift+Tab"), "两个方向都要测"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
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
print(f"== 登录态 {out['logged_in']} ==")


def run_phase(phase, key, cap, boundary_test, prev_map, presses, arm_stream):
    """按一个方向，直到**真的**布到边界下标、之后再按 `PAST` 次。

    `boundary_test`: 给定布到的下标，返回「是否算到达边界」。
    返回 (是否到达边界, 到达边界的第几次按压(1-based) 或 None)
    """
    hit_at = None
    for k in range(cap):
        pre_c = ev(CENSUS_JS, prev_map)      # 按之前普查（带 delta）
        page.keyboard.press(key)
        page.wait_for_timeout(SETTLE)
        post_c = ev(CENSUS_JS, prev_map)     # 按之后普查（带 delta）
        moved_c = pre_c["zero_idx"] != post_c["zero_idx"]
        if moved_c:
            idx = post_c["zero_idx"][0]
            arm_stream.append((phase, idx))
            if hit_at is None and boundary_test(idx, post_c["n_nodes"]):
                hit_at = k + 1
        presses.append({
            "phase": phase, "k": k + 1,
            "pre": {kk: pre_c[kk] for kk in KEEP},
            "post": {kk: post_c[kk] for kk in KEEP},
            "moved": moved_c,
        })
        prev_map = tabindex_map()
        # ⚠️ 停止条件：**真的到达了边界** 且 **之后又按了 PAST 次**
        if hit_at is not None and (k + 1) - hit_at >= PAST:
            return True, hit_at, prev_map
    return (hit_at is not None), hit_at, prev_map


if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ **被挡时也要落盘**（906 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        # ⚠️ **每轮之间 reload**（906 已证明这是必须的）
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "past": PAST,
               "fwd_cap": FWD_CAP, "rev_cap": REV_CAP}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        arm_stream = []          # (phase, 被布的下标)，跨方向、按时间序
        prev_map = tabindex_map()

        # ---------- 正向：走到最后一个下标，再多按 PAST 次 ----------
        # ⚠️ 节点总数是易变量 ⇒ 边界用**当下那一刻的 n_nodes** 算
        hit_fwd, at_fwd, prev_map = run_phase(
            "fwd", KEY_FWD, FWD_CAP,
            lambda idx, nn: idx == nn - 1,
            prev_map, presses, arm_stream)

        # 翻向那一刻的快照
        fwd_presses = [p for p in presses if p["phase"] == "fwd"]
        # ⚠️⚠️ 924 第一版**把门放错了位置**（自己踩的，记在这里）：
        #    第一版拿「**正向阶段最后一次**按压之后焦点在不在本体上」当门。
        #    但正向阶段**故意**在越界之后又按了 PAST 次 ⇒ 那 10 次已经把焦点
        #    带出了画布、绕了半圈页面 ⇒ 这道门必然 FAIL，**可它并不是
        #    「反向臂事件起手时焦点在不在本体上」**（实测反向第 1–8 次都是死按压，
        #    **第 9 次**焦点才回到布在 75 的那个本体上、**第 10 次**才真的布）。
        # ⇒ 门改成问它本来该问的那个问题（见下面 `first_rev_arm_pre_*`），
        #    **不是把门删掉、更不是放宽**。
        rec["focus_on_body_at_flip"] = bool(
            fwd_presses and fwd_presses[-1]["post"]["active"]["is_wrapper"])
        rec["armed_idx_at_flip"] = (fwd_presses[-1]["post"]["zero_idx"][0]
                                    if fwd_presses
                                    and fwd_presses[-1]["post"]["zero_idx"]
                                    else None)

        # ---------- 反向：一路退到 0，再多按 PAST 次 ----------
        hit_rev, at_rev, prev_map = run_phase(
            "rev", KEY_REV, REV_CAP,
            lambda idx, nn: idx == 0,
            prev_map, presses, arm_stream)

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["n_nodes"] = presses[-1]["post"]["n_nodes"] if presses else None
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]
        rec["hit_fwd_boundary"] = hit_fwd
        rec["hit_fwd_at_press"] = at_fwd
        rec["hit_rev_boundary"] = hit_rev
        rec["hit_rev_at_press"] = at_rev

        # ---------- 越界之后的每一次按压（**判「停手 vs 绕回」的关键**）----------
        rec["after_fwd_boundary"] = [p["k"] for p in fwd_presses
                                     if at_fwd and p["k"] > at_fwd]
        rec["after_rev_boundary"] = [p["k"] for p in
                                     [q for q in presses if q["phase"] == "rev"]
                                     if at_rev and p["k"] > at_rev]
        rev_presses = [p for p in presses if p["phase"] == "rev"]
        rec["after_rev_arm_idx"] = [
            p["post"]["zero_idx"][0] for p in rev_presses
            if at_rev and p["k"] > at_rev and p["moved"]
            and p["post"]["zero_idx"]]
        rec["after_fwd_arm_idx"] = [
            p["post"]["zero_idx"][0] for p in fwd_presses
            if at_fwd and p["k"] > at_fwd and p["moved"]
            and p["post"]["zero_idx"]]

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 的教训：后处理崩掉
        #    不该带走已经采到的读数）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup，不判机制 ----------
        n_past_fwd = len(rec["after_fwd_boundary"])
        n_past_rev = len(rec["after_rev_boundary"])
        n_past_ok = (n_past_fwd >= PAST and n_past_rev >= PAST)
        # ⭐ 门问的是「**第一个反向臂事件起手时**焦点在不在本体上」
        #    （用 `pre`、也就是按压**之前**那一侧 —— 923 已钉：
        #    `post` 焦点是按压的**结果**、不能当 keydown 那刻的落点）
        first_rev_arm = next((p for p in rev_presses if p["moved"]), None)
        rec["first_rev_arm_k"] = first_rev_arm["k"] if first_rev_arm else None
        rec["first_rev_arm_pre_focus_on_body"] = bool(
            first_rev_arm and first_rev_arm["pre"]["active"]["is_wrapper"])
        rec["first_rev_arm_pre_wrapper_idx"] = (
            first_rev_arm["pre"]["active"]["wrapper_idx"]
            if first_rev_arm else None)
        focus_gate_ok = rec["first_rev_arm_pre_focus_on_body"]
        rec["design_ok"] = {
            "focus_on_body_at_first_rev_arm_ok": bool(focus_gate_ok),
            "fwd_reached_end_ok": bool(hit_fwd),
            "rev_reached_start_ok": bool(hit_rev),
            "n_past_ok": bool(n_past_ok),
            "n_past_fwd": n_past_fwd,
            "n_past_rev": n_past_rev,
            "all_ok": bool(focus_gate_ok and hit_fwd
                           and hit_rev and n_past_ok),
        }
        print(f"  首个反向臂事件在反向第 {rec['first_rev_arm_k']} 次、"
              f"其 pre 焦点在本体={rec['first_rev_arm_pre_focus_on_body']}"
              f"（本体下标 {rec['first_rev_arm_pre_wrapper_idx']}）")
        print(f"  n_nodes={rec['n_nodes']} | 正向到末尾={hit_fwd}@第{at_fwd}次、"
              f"其后按了 {n_past_fwd} 次（其中布了 {rec['after_fwd_arm_idx']}）")
        print(f"  反向退到 0={hit_rev}@第{at_rev}次、其后按了 {n_past_rev} 次"
              f"（其中布了 {rec['after_rev_arm_idx']}）")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']} "
              f"n_nodes={r['n_nodes']}")
        print(f"    fwd 臂事件 {len(r['arm_seq_fwd'])} 次，"
              f"最大值={max(r['arm_seq_fwd']) if r['arm_seq_fwd'] else None} "
              f"（n_nodes-1={r['n_nodes'] - 1 if r['n_nodes'] else None}）")
        print(f"    rev 臂事件 {len(r['arm_seq_rev'])} 次，"
              f"最小值={min(r['arm_seq_rev']) if r['arm_seq_rev'] else None}")
        print(f"    越界后正向还布过：{r['after_fwd_arm_idx']}")
        print(f"    越界后反向还布过：{r['after_rev_arm_idx']}")
    print(f"\n== 已写 {OUT} ==")
