#!/usr/bin/env python3
r"""batch 927 源站探针（**纯诊断**）：**「写回早了一步」是只发生一次、还是每个整页循环一次**？

## §136 撞出的那条异常

926 实测（2/2）：在「退到下界 `0` → 冻结 30 次 `Shift+Tab` → 翻回正向」这个序列里，
**冻结之后的第 2 次正向按压**（`'0'` **停在 `[0]` 没动**、`moved = False`）
却做了 **`added = [1]`**（给下标 `1` **写回**了 `tabindex`）。

⚠️ **只有 1 次读数 ⇒ 按纪律不足以立机制。**
⚠️ 而且它**推翻了 §131** 那条「死按压 ⇒ 应用完全没碰 `tabindex`」
（在 921/922/924 的 8/8、4/4、47/47 都成立）⇒ §131 已收窄成「绝大多数」。

## 三个候选解释，本批**不预设**哪个对

① **只发生一次**：那是「从冻结状态**回到**画布内」这**一件事**带来的，
   冻结多长都一样
② **每个整页循环一次**：那它和**循环次数**成正比
③ **和冻结长度无关、和「翻回正向后的第几次按压」有关**：
   固定发生在翻向后的第 2 次，和冻结多长无关

## ⭐ 这就是**专为证伪它设计的最小复现**：把冻结长度分档

在同一轮里，对 **4 档冻结长度**各跑一遍
`L ∈ {1, 5, 29, 57}`（`1` 和 `5` **不足一个循环**、`29`/`57` 是**一到两个循环**），
每档都记：**翻回正向之后、第一次臂事件之前**那几次按压的**逐次 delta**。

- 若「`delta` 不空的死按压」**在每一档都恰好 1 次** ⇒ 倾向 ① 或 ③
- 若它**随循环次数增长** ⇒ 倾向 ②
- 若 `L = 1`（连一步循环都没走完）**就已经发生** ⇒ 更倾向 ③

⚠️ **本探针只输出读数，不判机制**；上面只是**要问什么**。
⚠️ **节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ 只记**最后那个下标**。
⚠️ **不许**拿死按压的**总次数**当判据（§135 实测它会抖 1 步）
⇒ 判据钉「**翻向之后、第一次臂事件之前**」这一小段的**逐次 delta**。

## 设计门（`design_ok`，每轮每档判一次）

1. `entered_ok` —— 第一个**反向**臂事件的 `pre` 焦点在**节点本体**上
2. `reached_0_ok` —— 反向**真的**退到了下标 `0`（否则没有「冻结」可言）
3. `post_arm_ok` —— 这一档翻回正向之后**真的又布了**（至少 1 次臂事件）

⚠️ 前两档 `L = 1` / `L = 5` 时，**前一档的臂事件已经把焦点带进画布了** ——
所以 `entered_ok` / `reached_0_ok` **只对第 1 档有约束**；
第 2–4 档的门是「**这一档自己也真的退到了 0、也真的又布了**」。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe927_early_writeback_repro_src.py
"""

import json

OUT = "/tmp/b927-src-early-writeback-repro.json"
REPS = 2
SETTLE = 400
# ⭐ 分档：1 和 5 **不足一个 28 步循环**、29/57 是**一到两个循环**
FREEZE_LADDER = (1, 5, 29, 57)
N_FWD = 12            # 只需把焦点推进画布、给反向留退路（不必走到末尾）
REV_CAP = 60          # 反向封顶
POST_CAP = 40         # 翻回正向后的封顶
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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 921–926 同一套）
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
# ⭐ 分档必须**同时覆盖「不足一个循环」和「一到两个循环」**
#    ⇒ 否则「只发生一次」和「每个循环一次」这两个候选**分不开**
assert min(FREEZE_LADDER) < 28, "必须有一档**不足**一个 28 步循环"
assert max(FREEZE_LADDER) > 28, "必须有一档**超过**一个 28 步循环"
assert len(set(FREEZE_LADDER)) >= 3, "至少 3 档才谈得上「一次 vs 每循环一次」"
assert MIN_ARM >= 3 and N_FWD >= MIN_ARM, "窗口深 2，正向步数要够"
assert (KEY_FWD, KEY_REV) == ("Tab", "Shift+Tab"), "两个方向都要测"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed", "active")

URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d3399f"
       "?enter_from=project_list&from_page=create")
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
    """按一次、记整张表 + delta；返回 (新的 prev_map, 该次是否臂事件)。"""
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
    return tabindex_map(), moved_c


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
        rec = {"rep": rep, "ladder": list(FREEZE_LADDER),
               "n_fwd": N_FWD, "rev_cap": REV_CAP, "post_cap": POST_CAP}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        arm_stream = []
        prev_map = tabindex_map()

        # ---------- 阶段 1：正向推进（不必走到末尾，只要有退路）----------
        for k in range(1, N_FWD + 1):
            prev_map, _ = press_once("fwd", k, KEY_FWD, prev_map, presses, arm_stream)
        rec["n_armed_after_fwd"] = sum(1 for ph, _ in arm_stream if ph == "fwd")

        # ---------- 阶段 2：反向退到 0 ----------
        zero_at = None
        for k in range(1, REV_CAP + 1):
            prev_map, mv = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if p["moved"] and "first_rev_pre_on_body" not in rec:
                rec["first_rev_k"] = k
                rec["first_rev_pre_on_body"] = bool(p["pre"]["active"]["is_wrapper"])
            if mv and p["post"]["zero_idx"] and p["post"]["zero_idx"][0] == 0:
                zero_at = k
                break
        rec["hit_zero_at"] = zero_at
        rec["n_nodes"] = presses[-1]["post"]["n_nodes"]

        # ---------- 阶段 3：⭐ 逐档跑「冻结 L 次 → 翻回正向」 ----------
        ladder = []
        for L in FREEZE_LADDER:
            last_armed_before = (arm_stream[-1][1] if arm_stream else None)
            base = prev_map
            t0 = len(presses)
            for k in range(1, L + 1):
                prev_map, _ = press_once(
                    "frz%d" % L, k, KEY_REV, prev_map, presses, arm_stream)
            n_frz_armed = sum(1 for p in presses[t0:] if p["moved"])
            any_ti_frz = [p["post"]["n_wrapper_any_ti"] for p in presses[t0:]]

            # 翻回正向：按到**真的又布了一次**为止
            t1 = len(presses)
            post_moved_at = None
            for k in range(1, POST_CAP + 1):
                prev_map, mv = press_once(
                    "post%d" % L, k, KEY_FWD, prev_map, presses, arm_stream)
                if mv and post_moved_at is None:
                    post_moved_at = k
                    break
            post_presses = presses[t1:]
            first_arm = next((p for p in post_presses if p["moved"]), None)
            ladder.append({
                "L": L,
                "last_armed_before": last_armed_before,
                "n_frz_armed": n_frz_armed,
                "any_ti_frz_min": min(any_ti_frz) if any_ti_frz else None,
                "any_ti_frz_max": max(any_ti_frz) if any_ti_frz else None,
                "post_moved_at": post_moved_at,
                "first_post_armed": (first_arm["post"]["zero_idx"][0]
                                     if first_arm
                                     and first_arm["post"]["zero_idx"] else None),
                "first_post_removed": first_arm["post"]["removed"] if first_arm else None,
                "first_post_added": first_arm["post"]["added"] if first_arm else None,
                "first_post_changed": first_arm["post"]["changed"] if first_arm else None,
                # ⭐ 判读用的那一小段：**翻向之后、第一次臂事件之前**
                "post_prefix": [{
                    "k": p["k"], "moved": p["moved"],
                    "zero_idx": p["post"]["zero_idx"],
                    "removed": p["post"]["removed"],
                    "added": p["post"]["added"],
                    "changed": p["post"]["changed"],
                    "pre_on_body": p["pre"]["active"]["is_wrapper"],
                } for p in post_presses
                    if first_arm is None or p["k"] <= first_arm["k"]],
            })
        rec["ladder_runs"] = ladder

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["design_ok"] = {
            "entered_ok": bool(rec.get("first_rev_pre_on_body")),
            "reached_0_ok": bool(zero_at is not None),
            "frz_clean_ok": all(x["n_frz_armed"] == 0 for x in ladder),
            "post_arm_ok": all(x["post_moved_at"] is not None for x in ladder),
            "all_ok": bool(rec.get("first_rev_pre_on_body")
                           and zero_at is not None
                           and all(x["n_frz_armed"] == 0 for x in ladder)
                           and all(x["post_moved_at"] is not None for x in ladder)),
        }

        # ⚠️⚠️ **落盘必须排在打印之前**（923 的教训：后处理崩掉
        #    不该带走已经采到的读数）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        print(f"  n_nodes={rec['n_nodes']} | 正向臂事件 "
              f"{rec['n_armed_after_fwd']}、反向退到 0@{zero_at}")
        for x in ladder:
            pre_nc = [p for p in x["post_prefix"]
                      if not p["moved"] and (p["removed"] or p["added"] or p["changed"])]
            print("    L=%-3d 冻结零臂事件=%-5s 翻向后第%s次才布 | "
                  "第一次臂 removed=%s added=%s changed=%s | "
                  "★ 臂事件之前 delta 不空的死按压 %d 次 %s"
                  % (x["L"], x["n_frz_armed"] == 0, x["post_moved_at"],
                     x["first_post_removed"], x["first_post_added"],
                     x["first_post_changed"], len(pre_nc),
                     [p["added"] for p in pre_nc]))
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']}")
        for x in r["ladder_runs"]:
            pre_nc = [p for p in x["post_prefix"]
                      if not p["moved"] and (p["removed"] or p["added"] or p["changed"])]
            print("    L=%-3d 臂事件前 delta 不空的死按压 %d 次 %s | "
                  "第一次 removed=%s added=%s"
                  % (x["L"], len(pre_nc), [p["added"] for p in pre_nc],
                     x["first_post_removed"], x["first_post_added"]))
    print(f"\n== 已写 {OUT} ==")
