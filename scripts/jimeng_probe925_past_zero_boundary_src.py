#!/usr/bin/env python3
r"""batch 925 源站探针（**纯诊断**）：**退到下界 0 之后**继续按 `Shift+Tab` —— 焦点会走去哪？滚动窗口还成立吗？

## §133/§134 已经查清的

- **§133**：滚动窗口是**一条不分方向的全局臂事件流**
  （`removed` = 上一个臂事件，144 次臂事件**零偏差**）⇒ **方向对称**。
- **§134**：**两个边界都是「到头停手、绝不绕回」** ——
  正向到 `n_nodes-1` 停手、反向退到 **0** 停手，越界后各按 10 次**一次都没布**。
- **§132**：**反向从画布根出发会走整页、构成一个周期恰为 27 的「闭环」**，
  `moved` 60/60 全 False ⇒ 永远进不了画布。

## 925 只问一件事：**过了 0 之后呢？**

⚠️ §134 只在 0 之后又按了 **10 次**就停了 ⇒ **那 10 次够不够走完 §132 那个
27 步闭环、焦点有没有绕回画布、绕回来之后还 arm 不 arm、窗口还算不算数**
—— **一个都没测到**。

本批把尾巴拉长：退到 0 之后**继续按到 `TAIL_CAP` 次**（封顶），
全程记**整张表 + 逐次 delta + 焦点落点**。

⭐ 真正想拿到的那个读数：
**如果焦点绕回某个本体、应用又布了一次，那么这一次臂事件的
`removed` 是不是仍然是「上一个臂事件」？**
—— §132 那 27 步整页循环夹在两次臂事件**中间**，
这正是「滚动窗口跨整页循环还成立吗」的唯一判别点。

## 设计门（`design_ok`，每轮判一次）

1. `reached_0_ok` —— 反向**真的**退到了下标 0
2. `n_armed_before_0_ok` —— 退到 0 **之前**至少 3 次臂事件
   （⭐ 窗口深 2 ⇒ 窗口得先被填上，才有「还成立」可问）
3. `n_tail_ok` —— 0 之后真的按了至少 `PAST` 次（不然「没反应」没有样本）
4. `entered_ok` —— 翻向那一刻焦点落在**节点本体**上

⚠️ **「0 之后一直没布」是读数、不是门** —— 门只管 setup，判读留给基线。
⚠️ **节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ 只记**最后那个下标**，
**不许**把它当常量钉进判据。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe925_past_zero_boundary_src.py
"""

import json

OUT = "/tmp/b925-src-past-zero-boundary.json"
REPS = 2
SETTLE = 400
N_FWD = 100           # 正向连按（自适应在到达末尾后停）
PAST = 10             # 到达末尾之后又按几次（给「停手」留样本）
TAIL = 80             # ⚠️ 退到 0 之后**继续按**多少次（§132 那个闭环是 27 步）
MIN_ARM = 3           # ⭐ 窗口深 2 ⇒ 退到 0 之前至少要有这么多次臂事件
FWD_CAP = 130         # ⚠️ 只是封顶

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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 921–924 同一套）
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
# ⚠️ 尾巴必须比 §132 那个 27 步闭环**长**，否则「绕回整页」这个情形没被覆盖
assert TAIL >= 30, "尾巴要盖过 §132 那个 27 步闭环，否则「绕回整页」没被覆盖"
assert PAST >= 5 and MIN_ARM >= 3, "样本量门"
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


def press_once(phase, k, key, prev_map, presses, arm_stream):
    """按一次、记整张表 + delta；返回新的 prev_map。"""
    pre_c = ev(CENSUS_JS, prev_map)
    page.keyboard.press(key)
    page.wait_for_timeout(SETTLE)
    post_c = ev(CENSUS_JS, prev_map)
    moved_c = pre_c["zero_idx"] != post_c["zero_idx"]
    if moved_c:
        arm_stream.append((phase, post_c["zero_idx"][0]))
    presses.append({
        "phase": phase, "k": k,
        "pre": {kk: pre_c[kk] for kk in KEEP},
        "post": {kk: post_c[kk] for kk in KEEP},
        "moved": moved_c,
    })
    return tabindex_map()


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
        rec = {"rep": rep, "past": PAST, "tail": TAIL,
               "fwd_cap": FWD_CAP, "min_arm": MIN_ARM}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        arm_stream = []          # (phase, 被布的下标)，跨方向、按时间序
        prev_map = tabindex_map()

        # ---------- 阶段 1：正向走到最后一个下标，再多按 PAST 次 ----------
        hit_end_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("fwd", k, KEY_FWD, prev_map, presses, arm_stream)
            idx = presses[-1]["post"]["zero_idx"]
            if (hit_end_at is None and presses[-1]["moved"] and idx
                    and idx[0] == presses[-1]["post"]["n_nodes"] - 1):
                hit_end_at = k
            if hit_end_at is not None and k - hit_end_at >= PAST:
                break
        rec["hit_end_at"] = hit_end_at
        n_nodes = presses[-1]["post"]["n_nodes"]
        rec["n_nodes"] = n_nodes

        # ---------- 阶段 2：反向退到 0（顺带记录第一个反向臂事件的 pre 焦点）----------
        zero_at = None
        rev_start_k = None
        for k in range(1, FWD_CAP + 1):
            before_n = len(presses)
            prev_map = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if rev_start_k is None and p["moved"]:
                rev_start_k = k
                rec["first_rev_arm_k"] = k
                rec["first_rev_arm_pre_focus_on_body"] = bool(
                    p["pre"]["active"]["is_wrapper"])
                rec["first_rev_arm_pre_wrapper_idx"] = p["pre"]["active"]["wrapper_idx"]
            idx = p["post"]["zero_idx"]
            if (zero_at is None and p["moved"] and idx and idx[0] == 0):
                zero_at = k
                break
        rec["hit_zero_at"] = zero_at

        # ---------- 阶段 3：⭐ 过了 0 之后**继续按 TAIL 次** ----------
        for k in range(zero_at + 1 if zero_at else 1, (zero_at or 0) + TAIL + 1):
            prev_map = press_once("tail", k, KEY_REV, prev_map, presses, arm_stream)

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]
        rec["n_armed_before_zero"] = len(rec["arm_seq_rev"])

        # ---------- 尾巴：0 之后的每一次按压（**判读留给基线**）----------
        tail_presses = [p for p in presses if p["phase"] == "tail"]
        rec["tail"] = {
            "n_presses": len(tail_presses),
            "n_armed": sum(1 for p in tail_presses if p["moved"]),
            "arm_idx": [p["post"]["zero_idx"][0] for p in tail_presses
                        if p["moved"] and p["post"]["zero_idx"]],
            "delta_all_empty": sum(
                1 for p in tail_presses
                if p["post"]["removed"] == [] and p["post"]["added"] == []
                and p["post"]["changed"] == []),
            # ⭐ 焦点落点整条轨迹（要看 §132 那个 27 步闭环有没有出现）
            "focus_aria_seq": [p["post"]["active"]["aria"] for p in tail_presses],
            "focus_is_wrapper_seq": [p["post"]["active"]["is_wrapper"]
                                     for p in tail_presses],
        }
        rec["any_ti_at_tail_end"] = presses[-1]["post"]["n_wrapper_any_ti"]
        rec["any_ti_tail_min"] = min(
            [p["post"]["n_wrapper_any_ti"] for p in tail_presses] or [None])

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 的教训：后处理崩掉
        #    不该带走已经采到的读数）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup，不判机制 ----------
        entered_ok = bool(rec.get("first_rev_arm_pre_focus_on_body"))
        reached_0_ok = (zero_at is not None)
        n_armed_ok = (rec["n_armed_before_zero"] >= MIN_ARM)
        n_tail_ok = (rec["tail"]["n_presses"] >= PAST)
        rec["design_ok"] = {
            "entered_ok": entered_ok,
            "reached_0_ok": bool(reached_0_ok),
            "n_armed_before_0_ok": bool(n_armed_ok),
            "n_tail_ok": bool(n_tail_ok),
            "n_armed_before_zero": rec["n_armed_before_zero"],
            "n_tail": rec["tail"]["n_presses"],
            "all_ok": bool(entered_ok and reached_0_ok
                           and n_armed_ok and n_tail_ok),
        }
        print(f"  n_nodes={n_nodes} | 正向到末尾@{hit_end_at}次、"
              f"反向退到 0@{zero_at}次 | 首个反向臂事件@{rec.get('first_rev_arm_k')}次"
              f"其 pre 焦点在本体={rec.get('first_rev_arm_pre_focus_on_body')}")
        print(f"  0 之后又按了 {rec['tail']['n_presses']} 次："
              f"其中布了 {rec['tail']['n_armed']} 次 {rec['tail']['arm_idx']}、"
              f"delta 全空 {rec['tail']['delta_all_empty']} 次 | "
              f"any_ti 尾部 {rec['any_ti_tail_min']}→{rec['any_ti_at_tail_end']}")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']} "
              f"n_nodes={r['n_nodes']}")
        print(f"    0 之后：按了 {r['tail']['n_presses']} 次、"
              f"布了 {r['tail']['n_armed']} 次 {r['tail']['arm_idx']}、"
              f"delta 全空 {r['tail']['delta_all_empty']} 次")
        print(f"    any_ti 尾部最小={r['any_ti_tail_min']} "
              f"结束={r['any_ti_at_tail_end']}")
    print(f"\n== 已写 {OUT} ==")
