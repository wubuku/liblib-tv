#!/usr/bin/env python3
r"""batch 933 源站探针（**纯诊断**）：**`document.body` 那一站为什么偶发不出现？**

## 932（§142 四）留下的

**8 圈（2 轮 × 4 圈）里 7 圈是 28、1 圈是 27**（rep2 的第 3 圈），
**那一圈缺的恰好是 `document.body` 那一站**、其余 27 站逐条全等、owner 集合不变。

⚠️⚠️ **但要先把范围说准 —— 这 8 圈全是**臂 B**（越界尾巴）的**：
- **臂 A（中性态）**：两轮各 2 个完整圈，**`document.body` 每一圈都在**（2/2）
- **臂 B（越界尾巴）**：8 圈里 **1 圈缺**（7/8 在）
⇒ **臂 A 那个 2 个圈的样本根本不够谈「出现率」** ⇒ **933 必须把两个臂都测够。**

## 933 只问一件事：**那个 27 步闭环里，缺 `document.body` 的圈占多少、落在第几圈？**

⭐ **两臂各测 `CYCLES_PER_ARM` 个完整周期**（不是 2 个）：

- **臂 A（中性态）**：点空白 ⇒ 验 `any_ti ≡ 0` ⇒ 一路 `Shift+Tab` 到够 `CYCLES_PER_ARM` 个周期
- **臂 B（越界尾巴）**：点空白 ⇒ 正向到末尾、反向退到 `0`，再一路 `Shift+Tab` 到够那么多圈

## ⚠️⚠️ 切分口径：**按「画布根停靠点」切**（不是按周期 27 切）

⚠️ **周期本身就是要测的东西** ⇒ **不许拿「27」去切**
（否则「这一圈是 26 还是 27」就成了假设而不是读数）
⇒ 切分基准选 **`document.body` 之外的画布根停靠点**：932 已实测
**缺 `document.body` 那一圈，画布根照样命中**（rep2 的 `root_at = [1, 29, 57, 84]`）
⇒ **画布根停靠点是两个状态下都不会丢的锚点。**

⇒ 这是「切片边界」那条纪律的第四次应用：**切之前先钉死「以什么为界」，
而且要比的那两个集合必须同质。**

## 读什么（**只记录、不判机制**）

- 每个臂的每一圈：长度、**有没有 `document.body`**、它在圈内的第几位
- 缺 `document.body` 的圈落在**第几个**（⇒ 位置型还是分散型，**先不下结论**）
- 每圈的 `n_focusable` 序列（⇒ 缺它那一圈前后，可聚焦集合有没有变）

⚠️⚠️ **样本量纪律**：两臂各 2 轮 × `CYCLES_PER_ARM` 圈
⇒ 即使某个臂拿到 16 个圈，**也不足以区分「固定位置」与「随机」**
⇒ **基线只记出现率与落点分布，**「成因未查明、标未验证」**。
⚠️ **不许**先编一个机制再去找读数（926 那条）。

## 设计门（`design_ok`，**只判 setup，不判机制**）

1. `neutral_ok` —— 臂 A 起手 `any_ti == 0`
2. `neutral_never_armed_ok` —— 臂 A 全程 `moved` 全 False
3. `n_cycles_a_ok` / `n_cycles_b_ok` —— 两臂各自真的切出了 ≥ `CYCLES_PER_ARM` 个**完整**圈
4. `cap_ok` —— 两臂都没撞 `TAIL_CAP`（撞了只能报「读数不足」）

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe933_body_stop_rate_src.py
"""

import json

OUT = "/tmp/b933-src-body-stop-rate.json"
REPS = 2
SETTLE = 400
CYCLES_PER_ARM = 8        # ⭐ 每臂要的**完整**周期数
# ⚠️⚠️⚠️ **第一版这里踩了 §139/§140 那条纪律的同一个坑**：
#    预算按「保守下界 20」算 ⇒ 8 × 20 + 40 = 200 次
#    ⇒ **可实测的单圈是 27 次** ⇒ 8 圈要 **216 次** ⇒ **200 装不下、必然撞 cap**
#    ⇒ **「到边界（这里是「到够圈数」）之后」的预算必须 > 圈数 × 真实单圈长度，
#    而那个长度要先测出来** —— 932 已经测出 26/27 ⇒ 这里取 **30**（整数上界，不钉 27）
BUDGET_PER_CYCLE = 30
TAIL_CAP_A = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
TAIL_CAP_B = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
N_FWD = 100
PAST = 10
FWD_CAP = 130

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

# ⚠️⚠️ 尺子 = 932 那版，**一个字都不改**（同口径才有可比性）
CENSUS_JS = """(prev) => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [], idlIdx = [];
  const cur = {};
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
  const FOCUS_SEL = 'a[href], button, input, select, textarea,'
                    + ' [tabindex], [contenteditable]';
  const fset = [...document.querySelectorAll(FOCUS_SEL)];
  const domSig = (el) => {
    if (!el || el.nodeType !== 1) return null;
    const parts = [];
    let n = el, depth = 0;
    while (n && n.nodeType === 1 && depth < 8) {
      let nth = 1, p = n.previousElementSibling;
      while (p) { if (p.tagName === n.tagName) nth++; p = p.previousElementSibling; }
      parts.unshift(n.tagName.toLowerCase() + ':nth-of-type(' + nth + ')');
      n = n.parentElement; depth++;
    }
    return parts.join('/');
  };
  const ownerIdx = (el) => {
    if (!el || !el.closest) return -1;
    const host = el.closest('.react-flow__node');
    return host ? nodes.indexOf(host) : -1;
  };
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    n_wrapper_missing_ti: nodes.length - anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    zero_idx: zeroIdx,
    idl_idx: idlIdx,
    any_ti_idx: anyTiIdx,
    removed, added, changed,
    n_focusable: fset.length,
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      on_canvas_root: aOnCanvasRoot,
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
      fpos: a ? fset.indexOf(a) : -1,
      dom_sig: domSig(a),
      owner_node_idx: ownerIdx(a),
      // ⭐ 933 唯一的新增字段：**焦点是不是 `document.body` 本身**
      //   （`tag` 早就记了，但 933 要的是**一个能直接判的布尔**，
      //    而 `tag === 'BODY'` 还混着「`aria` 为空的其他元素」）
      is_body: !!(a && a.tagName === 'BODY'),
    },
  };
}"""

MAP_JS = """() => { const o = {};
  [...document.querySelectorAll('.react-flow__node')]
  .forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });
  return o; }"""

# ⚠️ **探针自己长防线**
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
# ⭐ 932 的两个与状态无关的身份必须留着（933 的读数要能和 932 比）
assert "dom_sig" in CENSUS_JS and "owner_node_idx" in CENSUS_JS, "932 的字段被弄丢了"
assert "is_body" in CENSUS_JS, "933 的新字段没写上"
assert REPS >= 2, "一次成功不叫可靠"
assert CYCLES_PER_ARM >= 6, "6 个圈太少了，频率会粗得没法比（§139 那条纪律）"
# ⚠️⚠️⚠️ **预算必须 > 圈数 × 真实单圈长度（932 实测 26/27）** ——
#    用「保守下界」当预算会**必然撞 cap**（第一版就是这么废掉的）
assert BUDGET_PER_CYCLE >= 28, \
    "单圈实测 26/27，预算系数必须高于它，否则 8 圈装不下（§139/§140 那条）"
assert TAIL_CAP_A >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
assert TAIL_CAP_B >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
# ⚠️⚠️ **不许拿 27 去切分**（周期本身是读数）—— 切分只能用画布根停靠点
assert "== 27" not in CENSUS_JS
assert "on_canvas_root" in CENSUS_JS, "切分锚点必须是画布根停靠"


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


def cut_cycles(press_list, min_len):
    """⭐ **按画布根停靠点切圈**（不许按周期切 —— 周期本身是读数）。
    返回每圈的 dict，含 `sig`（该圈整条 `dom_sig` 序列，供下面逐条比）。"""
    root_at = [i + 1 for i, p in enumerate(press_list)
               if p["post"]["active"]["on_canvas_root"]]
    out_cycles = []
    for j, s_k in enumerate(root_at):
        if j + 1 >= len(root_at):
            break                      # 最后一圈不完整 ⇒ 不要
        e_k = root_at[j + 1] - 1
        seg = press_list[s_k - 1: e_k]
        if len(seg) < min_len:
            continue                  # **不许拿残尾去和整圈比**（932 的教训）
        body_pos = [q + 1 for q, p in enumerate(seg)
                    if p["post"]["active"]["is_body"]]
        out_cycles.append({
            "start": s_k, "end": e_k, "len": e_k - s_k + 1,
            "has_body": bool(body_pos), "body_pos": body_pos,
            "owner_set": sorted({p["post"]["active"]["owner_node_idx"]
                                 for p in seg}),
            "n_focusable": sorted({p["post"]["n_focusable"] for p in seg}),
            # ⭐ 逐条比要用它（**不切**、**不采样**）
            "sig": [p["post"]["active"]["dom_sig"] for p in seg],
            "body_sig_idx": (body_pos[0] - 1) if body_pos else None,
        })
    return out_cycles


def short_cycle_vs_ref(cycles):
    """⭐⭐ **每一个「缺 `document.body` 的圈」是不是就等于
    「同臂某一个带 `BODY` 的整圈删掉 `BODY` 那一站」？**

    ⚠️ **参照圈必须带 `BODY` 且长度恰好多 1**，否则这个比较不成立
    ⇒ 找不到合格参照就返回 `None`（**不许**拿长度不对的圈硬比）。
    """
    refs = [c for c in cycles if c["has_body"]]
    out = []
    for c in cycles:
        if c["has_body"]:
            out.append({"start": c["start"], "len": c["len"],
                        "checked": False, "equal": None, "note": "带 BODY 圈"})
            continue
        ref = next((d for d in refs if d["len"] == c["len"] + 1), None)
        if ref is None or ref["body_sig_idx"] is None:
            out.append({"start": c["start"], "len": c["len"],
                        "checked": False, "equal": None,
                        "note": "**没有合格参照圈**（长度恰好多 1 且带 BODY）"})
            continue
        bidx = ref["body_sig_idx"]
        cand = ref["sig"][:bidx] + ref["sig"][bidx + 1:]
        first_diff = next(
            ({"pos": q, "ref": cand[q], "got": c["sig"][q]}
             for q in range(min(len(cand), len(c["sig"])))
             if cand[q] != c["sig"][q]), None)
        out.append({
            "start": c["start"], "len": c["len"], "checked": True,
            "ref_start": ref["start"], "ref_len": ref["len"],
            "ref_body_idx": bidx, "cand_len": len(cand),
            "equal": (cand == c["sig"]), "first_diff": first_diff,
        })
    return out


MIN_CYCLE_LEN = 20        # ⚠️ 保守下界（实测 26/27）—— 用来剔残尾


if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "cycles_per_arm": CYCLES_PER_ARM}

        presses = []
        arm_stream = []
        prev_map = tabindex_map()

        # ---------- 臂 A：中性态 ----------
        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["arm_a_blank_hit"] = sp
        rec["arm_a_any_ti_at_start"] = ev(CENSUS_JS, None)["n_wrapper_any_ti"]
        for k in range(1, TAIL_CAP_A + 1):
            prev_map = press_once("arm_a", k, KEY_REV, prev_map, presses,
                                  arm_stream)
            a_presses = [p for p in presses if p["phase"] == "arm_a"]
            if len(cut_cycles(a_presses, MIN_CYCLE_LEN)) >= CYCLES_PER_ARM:
                break
        cap_a = (k >= TAIL_CAP_A and
                 len(cut_cycles([p for p in presses if p["phase"] == "arm_a"],
                                MIN_CYCLE_LEN)) < CYCLES_PER_ARM)
        a_presses = [p for p in presses if p["phase"] == "arm_a"]
        rec["arm_a_presses"] = len(a_presses)
        rec["arm_a_cap_hit"] = cap_a
        rec["arm_a_cycles"] = cut_cycles(a_presses, MIN_CYCLE_LEN)
        # ⭐⭐ 「短圈 == 整圈删掉 BODY 那一站？」逐圈比
        rec["arm_a_short_vs_ref"] = short_cycle_vs_ref(rec["arm_a_cycles"])
        rec["arm_a_n_armed"] = sum(1 for p in a_presses if p["moved"])
        rec["arm_a_any_ti_set"] = sorted({p["post"]["n_wrapper_any_ti"]
                                          for p in a_presses})
        rec["arm_a_n_focusable_set"] = sorted({p["post"]["n_focusable"]
                                               for p in a_presses})

        # ⚠️⚠️ 落盘排在所有后处理与设计门之前（900/923 的教训）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 臂 B：越界尾巴（同一页、同一把尺子）----------
        sp2 = ev(BLANK_JS)
        if sp2:
            page.mouse.click(sp2[0], sp2[1])
            page.wait_for_timeout(900)
        rec["arm_b_blank_hit"] = sp2

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
        rec["n_nodes"] = presses[-1]["post"]["n_nodes"]

        zero_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if zero_at is None and p["moved"] and p["post"]["zero_idx"] \
                    and p["post"]["zero_idx"][0] == 0:
                zero_at = k
                break
        rec["zero_at"] = zero_at
        rec["armed_body_idx"] = presses[-1]["post"]["zero_idx"][0] \
            if presses[-1]["post"]["zero_idx"] else None

        tail_start = len(presses)
        for k in range(1, TAIL_CAP_B + 1):
            prev_map = press_once("arm_b", k, KEY_REV, prev_map, presses, arm_stream)
            b_presses = [p for p in presses if p["phase"] == "arm_b"]
            if len(cut_cycles(b_presses, MIN_CYCLE_LEN)) >= CYCLES_PER_ARM:
                break
        cap_b = (k >= TAIL_CAP_B and
                 len(cut_cycles([p for p in presses if p["phase"] == "arm_b"],
                                MIN_CYCLE_LEN)) < CYCLES_PER_ARM)
        b_presses = [p for p in presses if p["phase"] == "arm_b"]
        rec["arm_b_presses"] = len(b_presses)
        rec["arm_b_cap_hit"] = cap_b
        rec["arm_b_cycles"] = cut_cycles(b_presses, MIN_CYCLE_LEN)
        rec["arm_b_short_vs_ref"] = short_cycle_vs_ref(rec["arm_b_cycles"])
        rec["arm_b_n_armed"] = sum(1 for p in b_presses if p["moved"])
        rec["arm_b_n_focusable_set"] = sorted({p["post"]["n_focusable"]
                                               for p in b_presses})
        # ⭐ 臂 B 的圈里「被布本体」停靠了几次（= 圈长 − 1 的那个额外站）
        rec["arm_b_body_landings"] = [
            sum(1 for p in b_presses[c["start"] - 1: c["end"]]
                if p["post"]["active"]["is_wrapper"]
                and p["post"]["active"]["wrapper_idx"] == rec["armed_body_idx"])
            for c in rec["arm_b_cycles"]]
        rec["presses"] = presses
        rec["arm_stream"] = arm_stream

        def summarize(prefix):
            cs = rec[prefix + "_cycles"]
            sv = rec[prefix + "_short_vs_ref"]
            return {
                "n_cycles": len(cs),
                "lens": [c["len"] for c in cs],
                "has_body": [c["has_body"] for c in cs],
                "body_pos": [c["body_pos"] for c in cs],
                "n_missing_body": sum(1 for c in cs if not c["has_body"]),
                "missing_at": [i + 1 for i, c in enumerate(cs)
                               if not c["has_body"]],
                # ⭐ 短圈 vs 参照整圈删掉 BODY
                "short_checked": sum(1 for s in sv if s["checked"]),
                "short_equal": [s["equal"] for s in sv if s["checked"]],
                "short_notes": [s.get("note") for s in sv if not s["checked"]],
            }

        rec["sum_arm_a"] = summarize("arm_a")
        rec["sum_arm_b"] = summarize("arm_b")

        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        neutral_ok = (rec["arm_a_any_ti_at_start"] == 0)
        n_a_ok = len(rec["arm_a_cycles"]) >= CYCLES_PER_ARM
        n_b_ok = len(rec["arm_b_cycles"]) >= CYCLES_PER_ARM
        rec["design_ok"] = {
            "neutral_ok": bool(neutral_ok),
            "neutral_never_armed_ok": (rec["arm_a_n_armed"] == 0),
            "n_cycles_a_ok": bool(n_a_ok),
            "n_cycles_b_ok": bool(n_b_ok),
            "cap_ok": (not cap_a and not cap_b),
            "n_cycles_a": len(rec["arm_a_cycles"]),
            "n_cycles_b": len(rec["arm_b_cycles"]),
            "all_ok": bool(neutral_ok and rec["arm_a_n_armed"] == 0
                           and n_a_ok and n_b_ok and not cap_a and not cap_b),
        }
        sa, sb = rec["sum_arm_a"], rec["sum_arm_b"]
        print(f"  臂A：按了 {rec['arm_a_presses']} 次、圈长 {sa['lens']}、"
              f"缺 body {sa['n_missing_body']}/{sa['n_cycles']} "
              f"（落在第 {sa['missing_at']} 圈）")
        print(f"    ⭐ 短圈 == 参照整圈删掉 BODY？ 查了 {sa['short_checked']} 个 ⇒ "
              f"{sa['short_equal']}"
              + (f"（未查：{sa['short_notes']}）" if sa["short_notes"] else ""))
        print(f"  臂B：退到0@{zero_at}、按了 {rec['arm_b_presses']} 次、"
              f"圈长 {sb['lens']}、缺 body {sb['n_missing_body']}/{sb['n_cycles']} "
              f"（落在第 {sb['missing_at']} 圈）")
        print(f"    臂B 圈内被布本体停靠次数 = {rec['arm_b_body_landings']}")
        print(f"    n_focusable：臂A {rec['arm_a_n_focusable_set']} / "
              f"臂B {rec['arm_b_n_focusable_set']}")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    tot_a = tot_b = miss_a = miss_b = 0
    for r in runs:
        sa, sb = r["sum_arm_a"], r["sum_arm_b"]
        tot_a += sa["n_cycles"]; tot_b += sb["n_cycles"]
        miss_a += sa["n_missing_body"]; miss_b += sb["n_missing_body"]
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']}")
        print(f"    臂A {sa['n_cycles']} 圈、缺 body {sa['n_missing_body']}、"
              f"落点圈号 {sa['missing_at']}、圈长 {sa['lens']}")
        print(f"    臂B {sb['n_cycles']} 圈、缺 body {sb['n_missing_body']}、"
              f"落点圈号 {sb['missing_at']}、圈长 {sb['lens']}")
    print(f"\n== ⭐ 跨轮合计 ==")
    print(f"  臂A：{miss_a}/{tot_a} 圈缺 document.body")
    print(f"  臂B：{miss_b}/{tot_b} 圈缺 document.body")
    print("  ⚠️ **样本量就是这么多** ⇒ 「固定位置」还是「分散」"
          "**本批不判、标未验证**")
    print(f"\n== 已写 {OUT} ==")
