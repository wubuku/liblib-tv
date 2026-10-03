#!/usr/bin/env python3
r"""batch 926 源站探针（**纯诊断**）：**越界冻结之后窗口还指着上一个臂事件吗** —— §135 四(1) 那个「未回答的问题」

## §135 明确留下的未回答问题

925 实测：退到下界 `0` 之后，**80 次 `Shift+Tab` 里应用一次都没布**
（焦点每 28 步落回下标 0 的本体、**带 `tabindex="0"`**，但 `cur+dir` 越界 ⇒ 不布）
⇒ **压根没有新的臂事件**
⇒ ⇒ 「**滚动窗口跨整页循环还成立吗**」**本批没有被问到**。

## 926 换一条路把它问掉：冻结之后**正向再布一次**

阶段：
1. **正向**走到最后一个下标（再多按 `PAST` 次）
2. **反向**退到下界 `0`
3. ⭐ **冻结**：继续按 `TAIL` 次 `Shift+Tab`（盖过 §132/§135 那个 28 步整页循环）
   —— 预期**零臂事件**、`n_wrapper_any_ti` 全程 75
4. ⭐⭐ **翻回正向再布一次**（自适应：按 `Tab` 直到真的布了一次，再多按几次）

**判别点 = 第 4 阶段第一次臂事件的 `removed`**：

- 若 `removed` **仍然是冻结前的最后一个臂事件那个下标** ⇒
  **越界那 28 步没有结束窗口** ⇒ 窗口确实「跨整页循环」
- 若 `removed` 是**空的**（或指向别的东西）⇒ **冻结期间窗口被清掉了**

⚠️ **预期会被「巧合」干扰，先写下来免得被当成例外**：冻结结束时状态是
「下标 `0` 带着 `'0'`、下标 `1` **没有** `tabindex`、其余 `'-1'`」；
而正向再布的下一个目标是下标 `1` ⇒ 于是这一次的
`removed = [0]`、**`added = [1]`**、**`changed = []`**
（因为 `1` 本来就**没有**属性，`null → '0'` 会被记成 `added`）
⇒ 这和 §133 翻向那一次是**同一类巧合**，**不是规则被破坏**。

## 设计门（`design_ok`，每轮判一次）

1. `entered_ok` —— 第一个**反向**臂事件的 `pre` 焦点在**节点本体**上
2. `reached_0_ok` —— 反向**真的**退到了下标 `0`
3. ⭐ `freeze_clean_ok` —— **冻结阶段真的冻结了**（零臂事件 且 `any_ti` 全程 75）
   ⇒ **这是第 4 阶段那个问题的前提**；冻结没发生，那个问题就**没有意义**
4. `post_freeze_arm_ok` —— 冻结之后**真的又布了**（至少 1 次）

⚠️ **「冻结之后窗口指哪儿」是读数、不是门** —— 门只管 setup，判读留给基线。
⚠️ **节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ 只记**最后那个下标**。
⚠️ **不许**拿死按压的**次数**当判据（§135 实测它会抖 1 步）。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe926_window_survives_freeze_src.py
"""

import json

OUT = "/tmp/b926-src-window-survives-freeze.json"
REPS = 2
SETTLE = 400
PAST = 10             # 到达末尾之后又按几次
TAIL = 30             # 冻结阶段：⚠️ 必须 > 28（§135 实测闭环周期 28）
POST_CAP = 60         # 翻回正向后的封顶
POST_PAST = 6         # 再布到之后又按几次（要能看出窗口继续滚动）
FWD_CAP = 130         # 正向阶段封顶
MIN_ARM = 3           # 窗口深 2

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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 921–925 同一套）
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
# ⚠️ 冻结必须**盖过** §135 实测的那个 28 步闭环，否则「跨循环」没被覆盖
assert TAIL > 28, "冻结次数必须大于 §135 实测的闭环周期 28"
assert PAST >= 5 and MIN_ARM >= 3 and POST_PAST >= 3, "样本量门"
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
               "post_cap": POST_CAP, "post_past": POST_PAST}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        arm_stream = []
        prev_map = tabindex_map()

        # ---------- 阶段 1：正向走到最后一个下标，再多按 PAST 次 ----------
        hit_end_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("fwd", k, KEY_FWD, prev_map, presses, arm_stream)
            p = presses[-1]
            if (hit_end_at is None and p["moved"] and p["post"]["zero_idx"]
                    and p["post"]["zero_idx"][0] == p["post"]["n_nodes"] - 1):
                hit_end_at = k
            if hit_end_at is not None and k - hit_end_at >= PAST:
                break
        rec["hit_end_at"] = hit_end_at
        n_nodes = presses[-1]["post"]["n_nodes"]
        rec["n_nodes"] = n_nodes

        # ---------- 阶段 2：反向退到 0 ----------
        zero_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if p["phase"] == "rev" and "first_rev_pre_on_body" not in rec \
                    and p["moved"]:
                rec["first_rev_k"] = k
                rec["first_rev_pre_on_body"] = bool(
                    p["pre"]["active"]["is_wrapper"])
                rec["first_rev_pre_idx"] = p["pre"]["active"]["wrapper_idx"]
            if (zero_at is None and p["moved"] and p["post"]["zero_idx"]
                    and p["post"]["zero_idx"][0] == 0):
                zero_at = k
                break
        rec["hit_zero_at"] = zero_at

        # ---------- 阶段 3：⭐ 冻结（继续按 Shift+Tab TAIL 次）----------
        any_ti_at_freeze_start = presses[-1]["post"]["n_wrapper_any_ti"]
        last_armed_before_freeze = (arm_stream[-1][1] if arm_stream else None)
        base = zero_at if zero_at else 0
        for k in range(base + 1, base + TAIL + 1):
            prev_map = press_once("freeze", k, KEY_REV, prev_map, presses, arm_stream)
        any_ti_at_freeze_end = presses[-1]["post"]["n_wrapper_any_ti"]
        rec["any_ti_at_freeze_start"] = any_ti_at_freeze_start
        rec["any_ti_at_freeze_end"] = any_ti_at_freeze_end
        rec["last_armed_before_freeze"] = last_armed_before_freeze

        # ---------- 阶段 4：⭐⭐ 翻回正向，再布一次（**判别点**）----------
        first_post_k = None
        for k in range(1, POST_CAP + 1):
            prev_map = press_once("post", k, KEY_FWD, prev_map, presses, arm_stream)
            p = presses[-1]
            if first_post_k is None and p["moved"]:
                first_post_k = k
                rec["first_post_removed"] = p["post"]["removed"]
                rec["first_post_added"] = p["post"]["added"]
                rec["first_post_changed"] = p["post"]["changed"]
                rec["first_post_armed"] = p["post"]["zero_idx"][0] \
                    if p["post"]["zero_idx"] else None
                rec["first_post_pre_on_body"] = bool(
                    p["pre"]["active"]["is_wrapper"])
            if first_post_k is not None and k - first_post_k >= POST_PAST:
                break
        rec["first_post_k"] = first_post_k

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]
        rec["arm_seq_post"] = [i for ph, i in arm_stream if ph == "post"]
        rec["n_armed_rev"] = len(rec["arm_seq_rev"])

        # ---------- 冻结阶段：真的冻结了吗（**第 4 阶段的前提**）----------
        frz = [p for p in presses if p["phase"] == "freeze"]
        rec["freeze"] = {
            "n_presses": len(frz),
            "n_armed": sum(1 for p in frz if p["moved"]),
            "any_ti_min": min([p["post"]["n_wrapper_any_ti"] for p in frz] or [None]),
            "any_ti_max": max([p["post"]["n_wrapper_any_ti"] for p in frz] or [None]),
            "delta_all_empty": sum(
                1 for p in frz
                if p["post"]["removed"] == [] and p["post"]["added"] == []
                and p["post"]["changed"] == []),
            "zero_idx_frozen": frz[-1]["post"]["zero_idx"] if frz else None,
        }

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 的教训：后处理崩掉
        #    不该带走已经采到的读数）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup，不判机制 ----------
        entered_ok = bool(rec.get("first_rev_pre_on_body"))
        reached_0_ok = (zero_at is not None)
        freeze_clean_ok = (rec["freeze"]["n_armed"] == 0
                           and rec["freeze"]["n_presses"] >= 1
                           and rec["freeze"]["any_ti_min"]
                           == rec["freeze"]["any_ti_max"]
                           == any_ti_at_freeze_end)
        post_arm_ok = (first_post_k is not None)
        rec["design_ok"] = {
            "entered_ok": entered_ok,
            "reached_0_ok": bool(reached_0_ok),
            "freeze_clean_ok": bool(freeze_clean_ok),
            "post_freeze_arm_ok": bool(post_arm_ok),
            "all_ok": bool(entered_ok and reached_0_ok
                           and freeze_clean_ok and post_arm_ok),
        }
        print(f"  n_nodes={n_nodes} | 正向到末尾@{hit_end_at}、反向退到 0@{zero_at}")
        print(f"  冻结 {rec['freeze']['n_presses']} 次：布了 {rec['freeze']['n_armed']} 次、"
              f"any_ti {rec['freeze']['any_ti_min']}–{rec['freeze']['any_ti_max']}、"
              f"冻结前最后布的下标={last_armed_before_freeze}")
        print(f"  ⭐ 冻结后第一次正向臂事件（正向第 {rec.get('first_post_k')} 次）："
              f"布了 {rec.get('first_post_armed')}、"
              f"removed={rec.get('first_post_removed')} "
              f"added={rec.get('first_post_added')} "
              f"changed={rec.get('first_post_changed')}")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']} "
              f"n_nodes={r['n_nodes']}")
        print(f"    冻结 {r['freeze']['n_presses']} 次零臂事件；"
              f"冻结前最后布={r['last_armed_before_freeze']}")
        print(f"    ⭐ 冻结后第一次臂事件：removed={r.get('first_post_removed')} "
              f"added={r.get('first_post_added')} "
              f"changed={r.get('first_post_changed')}")
        print(f"    冻结后臂事件序列={r['arm_seq_post']}")
    print(f"\n== 已写 {OUT} ==")
