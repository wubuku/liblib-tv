#!/usr/bin/env python3
r"""batch 929 源站探针（**纯诊断**）：**用足够长的尾巴**把「正向到末尾之后到底绕不绕回」判死

## 这一批要判死的那一对矛盾（**都是源站实测、方向相反**）

- **§124/896**：「到末尾就停手、**绝不绕回**」（`max_dom_idx_armed = 75`、
  `revisited = {}`）
- **§130/908**：「**源站会绕回**，但**只在「焦点回到画布根」的那一按**」
  （4/4，两条臂都布到了 `0`；`W1` 在**第 103 次**按压、`W2` 在第 85/84 次）

⇒ 两条**并存但不矛盾**的候选规则是 §908 那条（两分支）：
· 末尾 ＋ **按前焦点是节点本体** ＋ `Tab` ⇒ **撒手**
· 末尾 ＋ **按前焦点是画布根** ＋ `Tab` ⇒ **布 `'0'`、绕回**

⚠️⚠️ **而 §134（我自己在 924 记的那条）把两分支一刀切成「绝不绕回」** ——
它越界后**只按了 `10` 次**，**而 §134 自己就实测过那个整页循环是 28 步**
⇒ **10 次预算根本不够** ⇒ §928 已把那半个判成**回归**（899 踩过的同一个取样假象）。

## 本批就是那一跑

正向走到**最后一个下标**之后 ⭐ **继续按 `TAIL = 90` 次**（≥ 3 个整页循环）
⇒ 记每一次的 `zero_idx` **和按前焦点落在哪个元素上**。

- 若 `'0'` 在越界之后**回到了更小的下标** ⇒ **绕回**成立
- **判别用的那一格**：绕回那一按的**按前焦点是不是画布根**（§908 的条件）

## ⚠️ 判据纪律

- **纯读**：普查**纯读**、**不劫持 prototype、不装 MutationObserver**
- **重复 2 轮**；**每轮之间 reload**
- ⚠️ **`TAIL` 必须静态大于 28**（§134/§135 实测的整页循环周期）
  ⇒ **不然就又是一次「预算不够就下结论」的取样假象**
- ⚠️ **节点总数是易变量** ⇒ 边界用**当下那一刻的 `n_nodes`** 算，**不钉绝对值**
- ⚠️ **不许**用「越界后有没有布」这种**布尔**当唯一证据 ——
  要**记下标序列**（§131 的教训：**切片会把规律读反**、布尔会把「哪一个」抹平）
- ⚠️ 落盘排在打印之前；**探针只输出读数**，判读留给基线

## 计费边界

只按 `Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe929_long_tail_wrap_or_not_src.py
"""

import json

OUT = "/tmp/b929-src-long-tail-wrap.json"
REPS = 2
SETTLE = 400
N_FWD_CAP = 200        # 正向走到末尾的封顶
TAIL = 90              # ⚠️ **必须 > 28**（越界之后继续按多少次）
LOOP_PERIOD = 28       # §134/§135 实测的整页循环周期

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

# ⚠️⚠️ **核心读数**：**整张表** + **逐次 delta**（与 919–928 同一把尺子）
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
      // ⭐ 判别用的那一格：**按前焦点是不是画布根**（§908 的绕回条件）
      on_canvas_root: aOnCanvasRoot,
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
# ⭐⭐ **本批最要紧的一道静态门**：尾巴必须**远超**那个整页循环
#    ⇒ **不然就又是一次「预算不够就下结论」的取样假象**（899/§134 栽过两次）
assert TAIL >= 3 * LOOP_PERIOD, "尾巴必须 >= 3 个整页循环，否则又是取样假象"
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
        rec = {"rep": rep, "tail": TAIL, "loop_period": LOOP_PERIOD,
               "n_fwd_cap": N_FWD_CAP}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)

        presses = []
        arm_stream = []
        prev_map = tabindex_map()

        def press_once(phase, k, prev_map):
            pre = ev(CENSUS_JS, prev_map)
            page.keyboard.press(KEY_FWD)
            page.wait_for_timeout(SETTLE)
            post = ev(CENSUS_JS, prev_map)
            moved = pre["zero_idx"] != post["zero_idx"]
            if moved:
                arm_stream.append((phase, post["zero_idx"][0]))
            presses.append({
                "phase": phase, "k": k,
                "pre": {kk: pre[kk] for kk in KEEP},
                "post": {kk: post[kk] for kk in KEEP},
                "moved": moved,
            })
            return tabindex_map()

        # ---------- 阶段 1：正向走到最后一个下标（自适应）----------
        end_at = None
        for k in range(1, N_FWD_CAP + 1):
            prev_map = press_once("fwd", k, prev_map)
            p = presses[-1]
            if (end_at is None and p["moved"] and p["post"]["zero_idx"]
                    and p["post"]["zero_idx"][0] == p["post"]["n_nodes"] - 1):
                end_at = k
                break
        rec["hit_end_at"] = end_at
        n_nodes = presses[-1]["post"]["n_nodes"]
        rec["n_nodes"] = n_nodes
        armed_at_end = presses[-1]["post"]["zero_idx"][0] \
            if presses[-1]["post"]["zero_idx"] else None

        # ---------- 阶段 2：⭐ 越界之后**继续按 TAIL 次** ----------
        base = end_at if end_at else 0
        for k in range(base + 1, base + TAIL + 1):
            prev_map = press_once("tail", k, prev_map)

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["armed_at_end"] = armed_at_end
        rec["tail_presses"] = [p for p in presses if p["phase"] == "tail"]

        # ---------- 尾巴里每一次的「布到哪个下标 + 按前焦点在哪」----------
        # ⚠️ **不切片**：每一次都记全（§131 的教训）
        rec["tail_seq"] = [{
            "k": p["k"], "moved": p["moved"],
            "armed": p["post"]["zero_idx"][0] if p["post"]["zero_idx"] else None,
            "pre_on_canvas_root": p["pre"]["active"]["on_canvas_root"],
            "pre_on_wrapper": p["pre"]["active"]["is_wrapper"],
            "pre_aria": p["pre"]["active"]["aria"],
            "removed": p["post"]["removed"], "added": p["post"]["added"],
            "changed": p["post"]["changed"],
        } for p in rec["tail_presses"]]
        rec["tail_armed_idx"] = [t["armed"] for t in rec["tail_seq"]
                                 if t["moved"]]
        # ⭐ 判别点：越界之后第一次**布到比末尾更小的下标**
        revisit = next((t for t in rec["tail_seq"]
                        if t["moved"] and armed_at_end is not None
                        and t["armed"] < armed_at_end), None)
        rec["first_revisit"] = revisit
        rec["any_ti_tail_min"] = min(
            [p["post"]["n_wrapper_any_ti"] for p in rec["tail_presses"]] or [None])

        # ⚠️⚠️ **落盘必须排在设计门之前**（923 的教训：后处理崩掉
        #    不该带走已经采到的读数）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup ----------
        reached_end_ok = (end_at is not None)
        n_tail_ok = len(rec["tail_presses"]) >= TAIL
        entered_ok = bool(presses and presses[0]["moved"])
        rec["design_ok"] = {
            "entered_ok": entered_ok,
            "reached_end_ok": bool(reached_end_ok),
            "n_tail_ok": bool(n_tail_ok),
            "n_tail": len(rec["tail_presses"]),
            "all_ok": bool(entered_ok and reached_end_ok and n_tail_ok),
        }
        print(f"  n_nodes={n_nodes} | 正向到末尾@{end_at}次、布在下标 {armed_at_end}")
        print(f"  越界之后又按了 {len(rec['tail_presses'])} 次；"
              f"其中布了 {len(rec['tail_armed_idx'])} 次 "
              f"{rec['tail_armed_idx'][:12]}")
        if revisit:
            print(f"  ⭐ 第一次「布到比末尾更小的下标」在第 {revisit['k']} 次："
                  f"布到 {revisit['armed']}、"
                  f"按前焦点在画布根={revisit['pre_on_canvas_root']}、"
                  f"在本体={revisit['pre_on_wrapper']}")
        else:
            print("  ⭐ 越界之后**一次都没布到更小的下标**（尾巴 "
                  f"{len(rec['tail_presses'])} 次）")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        rv = r["first_revisit"]
        # ⚠️⚠️ **929 第一版自己踩的坑**：这里原来写成**跨行的 f-string 表达式**，
        #    而 **f-string 表达式里不许换行**（那是 Python 3.12 / PEP 701 才放宽的）
        #    ⇒ `/opt/miniconda3` 的 **3.12** 语法门**放行了**它，
        #    可 harness 跑的是 **3.11** ⇒ **一跑就 SyntaxError、整轮读数全丢**。
        #    ⇒ 教训见提交信息：**语法门必须用「真跑那个」解释器**。
        #    这里改成**先算好再打印**，不再把表达式塞进 f-string。
        rv_text = ("第%s次→%s（按前焦点在画布根=%s）"
                   % (rv["k"], rv["armed"], rv["pre_on_canvas_root"])) \
            if rv else "**无**"
        print("  rep%s design_ok=%s n_nodes=%s 末尾下标=%s 尾巴 %s 次"
              % (r["rep"], r["design_ok"]["all_ok"], r["n_nodes"],
                 r["armed_at_end"], r["design_ok"]["n_tail"]))
        print("    尾巴里布过的下标=%s" % r["tail_armed_idx"][:20])
        print("    第一次绕回=%s" % rv_text)
    print(f"\n== 已写 {OUT} ==")
