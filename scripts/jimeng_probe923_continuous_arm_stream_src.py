#!/usr/bin/env python3
r"""batch 923 源站探针（**纯诊断**）：**一条连续的臂事件流，正向走到位后直接翻向** —— §131 那条滚动窗口规则在**反向**是不是同一条？

## 922 留下的确切缺口

922 想测「反向的臂事件三动作是不是同一条规则」，但**反向臂 2/2 都被设计门挡住**
（`design_ok = False`、`n_armed = 0`）⇒ 作废。922 顺手查清的真事实：

- **反向从画布根出发、永远进不了画布**（60 次 `Shift+Tab` 构成**周期 27 的闭环**，
  `moved` 60/60 全 False、`is_wrapper` 60/60 全 False）
- ⇒ **反向臂必须先正向布一个**才有本体可退

## 923 的设计：**一条连续的臂事件流，中途翻向**（而不是分两段各测一遍）

`Tab` 连按到离起点足够远（给反向留出退路）→ **不停顿，直接翻成 `Shift+Tab`** 继续按
⇒ **每一次按压都记整张表 + 逐次 delta**，并给每条标上 `phase`（`fwd` / `rev`）。

⭐ **这样「方向翻转的那一次」就是最锋利的判别点** ——
窗口到底是
- **A：跨方向的全局臂事件流**（`removed` = 上一次臂事件，**不分方向**）⇒ 对称
- **B：分方向**（反向另起一套）⇒ **方向不对称**

只要把**正向的 `arm_seq`** 也记下来，就能直接问：
**翻向后的第一次臂事件，它的 `removed` 是不是正向最后布的那个？**

## 为什么不分两段

分两段（A 段只测正向、B 段只测反向）会**丢掉「翻向」这个最关键的样本** ——
而 923 要回答的恰恰是「翻向时窗口会不会断」。

## 设计门（`design_ok`，每轮判一次）

1. `entered_ok` —— **翻向那一刻焦点真的落在节点本体上**
   （否则反向量的不是「本体上的反向臂事件」）
2. `room_ok` —— 翻向时被布的下标 **≥ `N_REV`** ⇒ 反向有足够退路
   （否则会先撞下界，后面全是越界空操作）
3. `n_armed_ok` —— 正向、反向**各**至少 3 次臂事件
   （⭐ 滚动窗口深 2 的硬要求）
4. 静态 assert：不许再出现 `slice(0, 12)`（**切片会把规律读反**，§131 教训）

⚠️ **`moved` 是必需字段**；`armed` 会在非 `.react-flow__node` 的元素上触发
⇒ 「有没有咬到」**只能用 `moved`** 判。
⚠️ 探针**只输出读数**，判读留给基线（`design_ok` 只判 setup、不判机制）。

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe923_continuous_arm_stream_src.py
"""

import json

OUT = "/tmp/b923-src-continuous-arm-stream.json"
REPS = 2
SETTLE = 400
N_FWD = 24              # 正向按压次数 ⇒ 大致把 `'0'` 布到下标 20 上下
N_REV = 16              # 反向按压次数
MIN_ARM = 3             # ⭐ 滚动窗口深 2 ⇒ 正反两向各至少 3 次臂事件
FWD_CAP = 45            # 正向的封顶（⚠️ 只是封顶，够用即可）

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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 921/922 同一套）
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
# ⚠️ 两个方向都要真的按到（不许只测一向就下「对称/不对称」的结论）
assert (KEY_FWD, KEY_REV) == ("Tab", "Shift+Tab"), "两个方向都要测"
assert N_FWD >= MIN_ARM and N_REV >= MIN_ARM, "两向按压数都要够攒出臂事件"


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
        rec = {"rep": rep, "n_fwd": N_FWD, "n_rev": N_REV}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        # ---------- 一条连续的臂事件流：fwd → **不停顿** → rev ----------
        prev_map = tabindex_map()
        presses = []
        # ⚠️ 臂事件流：(phase, 被布的下标) —— 跨方向、**按时间顺序**
        arm_stream = []
        for phase, key, cnt in (("fwd", KEY_FWD, N_FWD), ("rev", KEY_REV, N_REV)):
            for k in range(cnt):
                pre_c = ev(CENSUS_JS, prev_map)     # 按之前普查（带 delta）
                page.keyboard.press(key)
                page.wait_for_timeout(SETTLE)
                post_c = ev(CENSUS_JS, prev_map)    # 按之后普查（带 delta）
                moved_c = pre_c["zero_idx"] != post_c["zero_idx"]
                if moved_c:
                    arm_stream.append((phase, post_c["zero_idx"][0]))
                presses.append({
                    "phase": phase, "k": k + 1,
                    "pre": {kk: pre_c[kk] for kk in KEEP},
                    "post": {kk: post_c[kk] for kk in KEEP},
                    "moved": moved_c,
                })
                prev_map = tabindex_map()
            print(f"  [{phase}] 走完 {cnt} 次")
        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]
        rec["n_armed_fwd"] = len(rec["arm_seq_fwd"])
        rec["n_armed_rev"] = len(rec["arm_seq_rev"])

        # ---------- 翻向那一刻的快照（判别「窗口会不会断」的关键）----------
        fwd_presses = [p for p in presses if p["phase"] == "fwd"]
        rev_presses = [p for p in presses if p["phase"] == "rev"]
        # ⚠️⚠️ 923 第一版踩的坑：`zero_idx` 是**列表**，第一版把它直接拿去
        #    和整数比 ⇒ `TypeError: '>=' not supported between 'list' and 'int'`
        #    ⇒ **崩在设计门那一行、整轮读数全丢**。这里拆成两个字段：
        #    列表原样留（不切片、不加工），**另**存一个取首项的整数。
        zf = fwd_presses[-1]["post"]["zero_idx"] if fwd_presses else []
        rec["flip"] = {
            # 翻向前最后一次正向按压之后：焦点在不在本体上
            "focus_on_body_at_flip": bool(
                fwd_presses and fwd_presses[-1]["post"]["active"]["is_wrapper"]),
            "zero_idx_at_flip": zf,
            "armed_idx_at_flip": (zf[0] if zf else None),   # ⚠️ 整数
            # 翻向后第一次反向按压的 delta（**判别点**）
            "first_rev_removed": rev_presses[0]["post"]["removed"] if rev_presses else None,
            "first_rev_added": rev_presses[0]["post"]["added"] if rev_presses else None,
            "first_rev_changed": rev_presses[0]["post"]["changed"] if rev_presses else None,
            "last_fwd_armed": rec["arm_seq_fwd"][-1] if rec["arm_seq_fwd"] else None,
            "prev_prev_fwd_armed": (rec["arm_seq_fwd"][-2]
                                    if len(rec["arm_seq_fwd"]) >= 2 else None),
        }

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 第一版把写文件排在门后面，
        #    门一崩整轮读数全丢 ⇒ 这是 §900 那条教训的推广：
        #    **任何后处理崩掉都不该带走已经采到的读数**）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup，不判机制 ----------
        entered_ok = rec["flip"]["focus_on_body_at_flip"]
        room_ok = (rec["flip"]["armed_idx_at_flip"] is not None
                   and rec["flip"]["armed_idx_at_flip"] >= N_REV)
        n_armed_ok = (rec["n_armed_fwd"] >= MIN_ARM
                      and rec["n_armed_rev"] >= MIN_ARM)
        rec["design_ok"] = {
            "entered_ok": bool(entered_ok),
            "room_ok": bool(room_ok),
            "n_armed_ok": bool(n_armed_ok),
            "n_armed_fwd": rec["n_armed_fwd"],
            "n_armed_rev": rec["n_armed_rev"],
            "all_ok": bool(entered_ok and room_ok and n_armed_ok),
        }
        print(f"  翻向时 armed_idx={rec['flip']['armed_idx_at_flip']} "
              f"焦点在本体={rec['flip']['focus_on_body_at_flip']} | "
              f"臂事件 fwd={rec['n_armed_fwd']} rev={rec['n_armed_rev']} | "
              f"rev arm_seq={rec['arm_seq_rev']} "
              f"=> design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']}")
        print(f"    arm_stream（phase, idx）= {r['arm_stream']}")
        print(f"    翻向判别点：removed={r['flip']['first_rev_removed']} "
              f"added={r['flip']['first_rev_added']} "
              f"changed={r['flip']['first_rev_changed']} | "
              f"正向最后布={r['flip']['last_fwd_armed']} "
              f"上上={r['flip']['prev_prev_fwd_armed']}")
    print(f"\n== 已写 {OUT} ==")
