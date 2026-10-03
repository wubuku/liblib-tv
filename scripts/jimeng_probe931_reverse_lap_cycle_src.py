#!/usr/bin/env python3
r"""batch 931 源站探针（**纯诊断**）：**反向那一侧有没有和正向一样的「常数周期」？**

## 930（§140）刚刚在**正向**测到的

- 绕回发生在按压 **102 / 203 / 304**，两次间隔 **101 / 101** ⇒ **「那一圈」是常数**；
- **每一圈逐条完全相同**（各：按压 101、臂事件 74、死按压 27、下标 `1…75`）。
  ⚠️ 930 的基线原文写的是「73 臂 + 28 死」，**那个 28 是按模式填的、已被 931 订正为 27**
  ⇒ 详见 `source_wrap_cycle_is_constant_930` 里的【931 订正】批注。

## 931 只问一件事：**反向那个圈是不是也是常数？**

⚠️ §135（925）只在**退到 `0` 之后又按了 80 次**就停了，量到的是
「**每 28 步**落回下标 `0` 的本体、应用一次都不布、闭环周期 28」
⇒ **28 只覆盖了不到 3 圈，而且只比了「落回本体」这一个事件**。

⭐ 931 做两件 §135 没做的事：

1. **按到「落回本体」出现 `MIN_RETURNS` 次为止**（**自适应停手**，不是拍脑袋给次数）
   ⇒ 于是「间隔是不是恒定」才是一个**真主张**（至少 3 个间隔）。
2. **比的是「焦点走线的整条序列」，不是单个事件** ——
   930 那边「每一圈逐条完全相同」比的是臂事件；
   反向尾巴**零臂事件**（§135）⇒ **能比的只有焦点落点序列**。
   ⭐ 为此**新增一个字段** `active.fpos` = 焦点在**当前可聚焦元素序列**里的序号
   （§132 已记过闭环里有**成对出现**的同名元素如 `静音`
   ⇒ 只比 `aria` 会撞车，序号不会）。

## ⭐ 对照臂：抖动到底出在哪一段？

⚠️⚠️ §135 五、如实记过一笔：**两轮不是逐条一致** ——
死按压总数 **117 / 118**、反向退到 `0` 的次数 **88 / 89**（差 1），
而**臂事件读数 144/144 完全一致**。

⇒ 那**多走/少走的一步，到底落在「接近段」还是「尾巴」**？—— §135 **分不出来**。
⇒ ⭐ **931 不需要额外的臂就能分辨**：每轮**同时**记
`hit_end_at` / `zero_at`（**接近段**）**和**尾巴的间隔序列。
两轮一比：**哪一段的数字在动，抖动就在哪一段** ——
这正是「两件事同时发生只能归因到其中一件」。

## 设计门（`design_ok`，每轮判一次；**只判 setup，不判机制**）

1. `entered_ok` —— 首个反向臂事件的**按前焦点**在节点本体上
2. `reached_0_ok` —— 反向**真的**退到了下标 `0`
3. `n_armed_before_0_ok` —— 退到 `0` **之前**至少 `MIN_ARM` 次臂事件（窗口深 2）
4. `n_returns_ok` —— ⭐ 尾巴里**落回被布本体**至少 `MIN_RETURNS` 次
   （⇒ 至少 3 个间隔，「常数」才站得住）
5. `cap_ok` —— **没有**因为撞到 `TAIL_CAP` 而提前收工
   （⚠️ 撞到 cap ⇒ **读数不足**、**必须**照实报 FAIL，**不许**据此下结论
    —— 这正是 §139 那条硬纪律：预算不足就下结论 = 假读数）

⚠️ **「间隔是不是全相等」「每圈序列是不是一样」是读数、不是门** ——
门只管 setup，判读留给基线。
⚠️ **节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ 不许钉成常量。
⚠️ **不许把 §135 那个 28 钉成期望值** —— 931 要问的就是「它是不是常数」，
**预设 28 就等于把答案写进判据**。间隔**原样记录**，不做任何比较判断。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**
（尾巴里焦点会路过节点的**内层控件** —— §132 已记过闭环里有
`添加素材到时间线`/`静音`/`全屏编辑`/`导出时间线`/`替换媒体`。
**按下去的是 `Tab` 键本身，不是点击** ⇒ 不产生任何点击副作用。）

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe931_reverse_lap_cycle_src.py
"""

import json

OUT = "/tmp/b931-src-reverse-lap.json"
REPS = 2
SETTLE = 400
N_FWD = 100           # 正向连按（自适应在到达末尾后停）
PAST = 10             # 到达末尾之后又按几次（与 925 逐字一致，好直接比）
MIN_ARM = 3           # ⭐ 窗口深 2 ⇒ 退到 0 之前至少要有这么多次臂事件
FWD_CAP = 130         # ⚠️ 只是封顶
MIN_RETURNS = 4       # ⭐ 至少 4 次「落回被布本体」⇒ 至少 3 个间隔
TAIL_CAP = 200        # ⚠️ 只是封顶；**自适应停手**才是真正的停止条件

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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 919–930 同一把尺子）
# ⚠️ §131 的教训：920 用 `slice(0, 12)` 把规律读反了 ⇒ 这里**一个字都不切**
# ⭐ **931 只在 930 那版上「加」字段、不改任何一个已有字段的算法** ——
#    新增 `n_focusable` 与 `active.fpos`（焦点在可聚焦序列里的序号）
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
  // ⭐ 931 新增：焦点在「可聚焦元素序列」里的序号。
  //   §132 已记过闭环里有**成对出现**的同名元素（如 静音）
  //   ⇒ 只比 aria 会撞车，序号不会。set 变了由 n_focusable 暴露。
  const FOCUS_SEL = 'a[href], button, input, select, textarea,'
                    + ' [tabindex], [contenteditable]';
  const fset = [...document.querySelectorAll(FOCUS_SEL)];
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
    n_focusable: fset.length,             // ⭐ 931 新增
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      on_canvas_root: aOnCanvasRoot,      // ⭐ §908 的绕回触发条件
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
      fpos: a ? fset.indexOf(a) : -1,     // ⭐ 931 新增
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
# ⭐ 931 的两个新字段必须在（少一个这批就白跑了）
assert "fpos" in CENSUS_JS and "n_focusable" in CENSUS_JS, "931 的新字段没写上"
assert REPS >= 2, "一次成功不叫可靠"
# ⭐⭐ 「间隔是不是恒定」要成立，至少得 3 个间隔 ⇒ 至少 4 次落回
assert MIN_RETURNS >= 4, "少于 4 次落回 ⇒ 间隔不足 3 个，「常数」是个空主张"
# ⚠️⚠️ §139 的硬纪律：撞到 cap 只能报「读数不足」，不能拿来下结论
#    ⇒ cap 必须**宽到撞它本身就是信号**，且**不许**把它当成停止条件
assert TAIL_CAP >= MIN_RETURNS * 30, \
    "cap 要够宽（每圈按 30 保守下界算），窄了就会把「读数不足」误当读数"
assert (KEY_FWD, KEY_REV) == ("Tab", "Shift+Tab"), "两个方向都要测"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed", "n_focusable", "active")

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
    """按一次、记整张表 + delta；返回新的 prev_map。（与 925/930 逐字同口径）"""
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


def gaps_of(positions):
    """相邻位置之差；**原样返回、不做任何判断**（不预设是不是常数）。"""
    return [positions[i + 1] - positions[i]
            for i in range(len(positions) - 1)]


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
        rec = {"rep": rep, "past": PAST, "tail_cap": TAIL_CAP,
               "min_arm": MIN_ARM, "min_returns": MIN_RETURNS}

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
        # （与 925 **逐字一致** ⇒ 两批的接近段读数可直接比）
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

        # ---------- 阶段 2：反向退到 0（顺带记首个反向臂事件的 pre 焦点）----------
        zero_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if zero_at is None and p["moved"] and p["post"]["zero_idx"] \
                    and p["post"]["zero_idx"][0] == 0:
                rec["first_rev_arm_k"] = k
                rec["first_rev_arm_pre_focus_on_body"] = bool(
                    p["pre"]["active"]["is_wrapper"])
                rec["first_rev_arm_pre_wrapper_idx"] = p["pre"]["active"]["wrapper_idx"]
                zero_at = k
                break
        rec["zero_at"] = zero_at
        rec["armed_body_idx"] = (presses[-1]["post"]["zero_idx"][0]
                                 if presses[-1]["post"]["zero_idx"] else None)

        # ---------- 阶段 3：⭐ 过了 0 之后**自适应连按** ----------
        #   停止条件 = 「观测到第 MIN_RETURNS 次落回被布本体」（不是拍脑袋给次数）
        #   TAIL_CAP 只封顶；**撞到 cap 一律记 cap_hit=True**（⇒ 设计门 FAIL）
        armed_body = rec["armed_body_idx"]
        tail_presses_start = len(presses)
        ret_armed_at = []       # 落回**被布那个本体**的按压序号（尾巴内，1 基）
        ret_any_at = []         # 落到**任意**节点本体的按压序号
        cap_hit = False
        for k in range(1, TAIL_CAP + 1):
            prev_map = press_once("tail", k, KEY_REV, prev_map, presses, arm_stream)
            act = presses[-1]["post"]["active"]
            if act["is_wrapper"]:
                ret_any_at.append(k)
                if act["wrapper_idx"] == armed_body and act["ti_attr"] == "0":
                    ret_armed_at.append(k)
            if len(ret_armed_at) >= MIN_RETURNS:
                break
        else:
            cap_hit = (len(ret_armed_at) < MIN_RETURNS)
        rec["cap_hit"] = cap_hit
        rec["ret_armed_at"] = ret_armed_at
        rec["ret_any_at"] = ret_any_at
        rec["armed_body_idx_observed"] = [
            presses[tail_presses_start + k - 1]["post"]["active"]["wrapper_idx"]
            for k in ret_any_at]
        rec["gaps_armed"] = gaps_of(ret_armed_at)

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]
        rec["n_armed_before_zero"] = len(rec["arm_seq_rev"])

        # ---------- 尾巴派生读数（**只记录、不判机制**）----------
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
            "focus_aria_seq": [p["post"]["active"]["aria"] for p in tail_presses],
            "focus_is_wrapper_seq": [p["post"]["active"]["is_wrapper"]
                                     for p in tail_presses],
            # ⭐ 931 的核心读数：焦点走线（序号）与画布根停靠点
            "fpos_seq": [p["post"]["active"]["fpos"] for p in tail_presses],
            "root_at": [k for k, p in enumerate(tail_presses, 1)
                        if p["post"]["active"]["on_canvas_root"]],
            "n_focusable_series": [p["post"]["n_focusable"] for p in tail_presses],
        }
        rec["root_gaps"] = gaps_of(rec["tail"]["root_at"])
        rec["any_ti_at_tail_end"] = presses[-1]["post"]["n_wrapper_any_ti"]
        rec["any_ti_tail_min"] = min(
            [p["post"]["n_wrapper_any_ti"] for p in tail_presses] or [None])
        rec["focusable_set_first"] = rec["tail"]["n_focusable_series"][0]
        rec["focusable_set_last"] = rec["tail"]["n_focusable_series"][-1]

        # ⚠️⚠️⚠️ **第一版这段犯过一个错、把记录留在代码里**（README §141）：
        #    原来以「落回被布本体」切圈，**第 0 圈从「尾巴第 1 次按压」起、
        #    第 1..3 圈从「上一次的落回本体」起** ⇒ **首尾边界不一致**
        #    ⇒ 打出 `lap_lens = [28, 29, 29, 29]`、`laps_identical = False`
        #    ⇒ **那不是源站事实、是我自己的切片把规律读反**：
        #    画布根是每圈第 1 站、被布本体是最后一站，
        #    而「第 0 圈」和「第 1..3 圈」量的是**两种不同的区间**。
        #    ⇒ 现在**统一边界：以「画布根停靠点」为每圈起点**。
        #    教训：「切片会把规律读反」这条纪律**在分析层同样成立** ——
        #    **连「以什么为界切一整圈」都得先钉死。**
        walk_seq = rec["tail"]["fpos_seq"]
        root_pos = rec["tail"]["root_at"]
        lap_starts, lap_ends = [], []
        for j, s_k in enumerate(root_pos):
            # 最后一圈止于尾巴末尾；其余止于「下一次画布根停靠」的前一次按压
            e_k = (root_pos[j + 1] - 1) if (j + 1 < len(root_pos)) \
                else len(tail_presses)
            lap_starts.append(s_k)
            lap_ends.append(e_k)
        lap_segs = [walk_seq[s_k - 1: e_k]
                    for s_k, e_k in zip(lap_starts, lap_ends)]
        rec["lap_starts"] = lap_starts
        rec["lap_ends"] = lap_ends
        rec["lap_lens"] = [len(s) for s in lap_segs]
        rec["laps_identical"] = (len(lap_segs) >= 2
                                 and all(s == lap_segs[0] for s in lap_segs))
        rec["first_lap_diff"] = next(
            ({"lap": j, "pos": q,
              "ref": lap_segs[0][q] if q < len(lap_segs[0]) else None,
              "got": s[q]}
             for j, s in enumerate(lap_segs)
             for q in range(min(len(s), len(lap_segs[0])))
             if s[q] != lap_segs[0][q]),
            None)

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
        n_returns_ok = (len(ret_armed_at) >= MIN_RETURNS)
        rec["design_ok"] = {
            "entered_ok": entered_ok,
            "reached_0_ok": bool(reached_0_ok),
            "n_armed_before_0_ok": bool(n_armed_ok),
            "n_returns_ok": bool(n_returns_ok),
            "cap_ok": (not cap_hit),
            "n_armed_before_zero": rec["n_armed_before_zero"],
            "n_returns": len(ret_armed_at),
            "tail_presses": rec["tail"]["n_presses"],
            "all_ok": bool(entered_ok and reached_0_ok and n_armed_ok
                           and n_returns_ok and not cap_hit),
        }
        print(f"  n_nodes={n_nodes} | 正向到末尾@{hit_end_at}次、"
              f"反向退到 0@{zero_at}次（被布本体下标={armed_body}）")
        print(f"  尾巴按了 {rec['tail']['n_presses']} 次（cap={TAIL_CAP}，"
              f"撞 cap={cap_hit}）：落回被布本体 {len(ret_armed_at)} 次 "
              f"{ret_armed_at}；间隔 {rec['gaps_armed']}")
        print(f"    画布根停靠 {rec['tail']['root_at']}；"
              f"臂事件 {rec['tail']['n_armed']} 次 {rec['tail']['arm_idx']}；"
              f"delta 全空 {rec['tail']['delta_all_empty']}/{rec['tail']['n_presses']}")
        print(f"    各圈长度 {rec['lap_lens']}；逐圈完全相同="
              f"{rec['laps_identical']}；any_ti {rec['any_ti_tail_min']}"
              f"→{rec['any_ti_at_tail_end']}")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']} "
              f"n_nodes={r['n_nodes']} cap_hit={r['cap_hit']}")
        print(f"    接近段：到末尾@{r['hit_end_at']} 退到0@{r['zero_at']}")
        print(f"    尾巴 {r['tail']['n_presses']} 次："
              f"落回 {r['ret_armed_at']}")
        print(f"    间隔 {r['gaps_armed']}")
        print(f"    画布根停靠 {r['tail']['root_at']} / 间隔 {r['root_gaps']}")
        print(f"    各圈长度 {r['lap_lens']}、逐圈完全相同={r['laps_identical']}、"
              f"首处不同={r['first_lap_diff']}")
    print("\n== ⭐ 跨轮对照：接近段 vs 尾巴，哪一段在动 ==")
    if len(runs) >= 2:
        for a, b in zip(runs, runs[1:]):
            print(f"  rep{a['rep']}→rep{b['rep']}："
                  f"到末尾 {a['hit_end_at']}→{b['hit_end_at']}、"
                  f"退到0 {a['zero_at']}→{b['zero_at']}、"
                  f"尾巴间隔 {a['gaps_armed']}→{b['gaps_armed']}")
    print(f"\n== 已写 {OUT} ==")
