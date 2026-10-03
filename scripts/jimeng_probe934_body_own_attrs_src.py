#!/usr/bin/env python3
r"""batch 934 源站探针（**纯诊断**）：`document.body` 那一站的缺席，
**与 `document.body` 自己那一下的任何可测属性相关吗？**

## 933（§143）留下的

**32 圈里 3 圈缺 `document.body`（9.4%）**、落点第 4/2/7 圈，
而 **3/3 处短圈都精确等于「同臂参照整圈删掉 `BODY` 那一站」** ⇒ 唯一差异就是那一站。
⚠️ 三个假设已排除：越界状态、可聚焦集合大小、少了被布本体。

## 934 ⭐ 不去堆圈数硬凑「随机」，而是换一个**能被证伪**的假设

⚠️ **「落点分散」既不支持「固定位置」、也证不了「随机」**（§143 五）
⇒ **堆更多圈数只能把频率估得更准，判不了性质。**
⇒ 934 换一个**具体、可测、可证伪**的假设：

> **H：「那一站出不出现，取决于 `document.body` 自己那一下是不是当时可被顺序聚焦」**
> —— 即 `document.body` 的 `tabindex` 属性 / IDL `tabIndex` / 子节点数在缺席圈里**变了**。

⭐ 逐次按压记录四个**与焦点走线无关的**页面量：
`body_tabindex`（属性原文）、`body_tabIndex`（IDL）、`body_n_children`、
`body_scroll_top`，外加 933 已有的 `n_focusable`。

⇒ **若缺席圈与完整圈的这些量逐次全同 ⇒ H 被证伪**（914 那套「把候选逐个消掉」的路子）
⇒ **若真的变了 ⇒ 拿到了唯一的可测相关量**，而「为什么变」仍要另问。

⚠️⚠️ **不许**因为「找到相关量」就宣称「这就是成因」——
**相关 ≠ 成因**，何况 9.4% 的基率下随便一个量都容易撞出相关。

## 圈数为什么要加

⚠️ 9.4% 的基率下，**16 个圈只能期望 1.5 次缺席** ⇒ 要估频率至少得 40+ 圈
⇒ 934 取 **15 圈/臂/轮 × 2 臂 × 2 轮 = 60 圈**（期望 ≈ 5.6 次缺席）
⇒ **仍然只报频率与落点分布，不判「随机/固定」**（§143 五那条纪律继续有效）

## 设计门（`design_ok`，**只判 setup，不判机制**）

1. `neutral_ok` / `neutral_never_armed_ok` —— 臂 A 起手 `any_ti ≡ 0` 且全程不布
2. `n_cycles_a_ok` / `n_cycles_b_ok` —— 两臂各切出 ≥ `CYCLES_PER_ARM` 个**完整**圈
3. `cap_ok` —— 两臂都没撞 cap（撞了只能报「读数不足」）

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe934_body_own_attrs_src.py
"""

import json

OUT = "/tmp/b934-src-body-own-attrs.json"
REPS = 2
SETTLE = 400
CYCLES_PER_ARM = 15
# ⚠️⚠️ 预算系数必须**高于实测单圈长度**（26–28）—— §139/§140 那条纪律
#    （933 第一版就是按 20 算、结果 8 圈 × 27 = 216 装不进 200）
BUDGET_PER_CYCLE = 32
TAIL_CAP_A = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
TAIL_CAP_B = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
N_FWD = 100
PAST = 10
FWD_CAP = 130
MIN_CYCLE_LEN = 20

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

# ⚠️⚠️ 尺子 = 933 那版，**一个字都不改**，只**加**四个与焦点走线无关的页面量
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
  const B = document.body;
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
    // ⭐⭐⭐ 934 新增：**与焦点走线无关的四个页面量**。
    //   假设 H = 「那一站的出没取决于 `document.body` 自己那一下可不可顺序聚焦」
    //   ⇒ 逐次记下这四个量，缺席圈与完整圈逐次全同 ⇒ **H 被证伪**。
    body_tabindex: B ? B.getAttribute('tabindex') : null,
    body_tab_index: B ? B.tabIndex : null,
    body_n_children: B ? B.childElementCount : null,
    body_scroll_top: B ? Math.round(B.scrollTop) : null,
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
      is_body: !!(a && a.tagName === 'BODY'),
    },
  };
}"""

MAP_JS = """() => { const o = {};
  [...document.querySelectorAll('.react-flow__node')]
  .forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });
  return o; }"""

BODY_ATTRS = ("body_tabindex", "body_tab_index", "body_n_children",
              "body_scroll_top")

# ⚠️ **探针自己长防线**
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
# ⭐ 932/933 的字段不许被弄丢（读数要能和前两批比）
for fld in ("dom_sig", "owner_node_idx", "is_body", "fpos"):
    assert fld in CENSUS_JS, f"前批的字段 {fld} 被弄丢了"
# ⭐⭐ 934 的四个新字段必须都在
for fld in BODY_ATTRS:
    assert fld in CENSUS_JS, f"934 的新字段 {fld} 没写上"
assert REPS >= 2, "一次成功不叫可靠"
assert CYCLES_PER_ARM >= 10, \
    "9.4% 的基率下圈数太少 ⇒ 频率估不准（§139 那条：预算要先够）"
assert BUDGET_PER_CYCLE >= 30, \
    "单圈实测 26–28，预算系数必须高于它，否则必然撞 cap（§139/§140）"
assert TAIL_CAP_A >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
assert TAIL_CAP_B >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
# ⚠️⚠️ **不许拿 27/28 去切分**（周期本身是读数）—— 只能用画布根停靠点
assert "== 27" not in CENSUS_JS and "== 28" not in CENSUS_JS
assert "on_canvas_root" in CENSUS_JS, "切分锚点必须是画布根停靠"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed", "n_focusable") + BODY_ATTRS + ("active",)

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


def count_full_cycles(press_list):
    """⭐ **便宜的停止条件**：只数「画布根停靠点」个数（O(n)），
    免得每次按压都重建整圈序列。≥ N+1 个画布根 ⇒ 至少 N 个**完整**圈。"""
    roots = sum(1 for p in press_list if p["post"]["active"]["on_canvas_root"])
    return max(0, roots - 1)


def cut_cycles(press_list, min_len):
    """⭐ **按画布根停靠点切圈**（不许按周期切 —— 周期本身是读数）。
    末圈不完整 ⇒ 丢弃；短于 `min_len` ⇒ 丢弃（**不许拿残尾和整圈比**）。"""
    root_at = [i + 1 for i, p in enumerate(press_list)
               if p["post"]["active"]["on_canvas_root"]]
    out_cycles = []
    for j, s_k in enumerate(root_at):
        if j + 1 >= len(root_at):
            break
        e_k = root_at[j + 1] - 1
        seg = press_list[s_k - 1: e_k]
        if len(seg) < min_len:
            continue
        body_pos = [q + 1 for q, p in enumerate(seg)
                    if p["post"]["active"]["is_body"]]
        out_cycles.append({
            "start": s_k, "end": e_k, "len": e_k - s_k + 1,
            "has_body": bool(body_pos), "body_pos": body_pos,
            "owner_set": sorted({p["post"]["active"]["owner_node_idx"]
                                 for p in seg}),
            "n_focusable": sorted({p["post"]["n_focusable"] for p in seg}),
            "sig": [p["post"]["active"]["dom_sig"] for p in seg],
            "body_sig_idx": (body_pos[0] - 1) if body_pos else None,
            # ⭐⭐ 934 核心：把四个页面量**逐次**记下来（不取集合、后面要逐次比）
            "body_attr_seq": [[p["post"][f] for f in BODY_ATTRS] for p in seg],
        })
    return out_cycles


def short_cycle_vs_ref(cycles):
    """每个「缺 `document.body` 的圈」是不是就等于「同臂某个带 `BODY` 的整圈
    删掉 `BODY` 那一站」？**参照圈必须带 `BODY` 且长度恰好多 1**，
    找不到就记 `None`（**不许**拿长度不对的圈硬比）。"""
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
        out.append({
            "start": c["start"], "len": c["len"], "checked": True,
            "ref_start": ref["start"], "ref_len": ref["len"],
            "ref_body_idx": bidx, "cand_len": len(cand),
            "equal": (cand == c["sig"]), "first_diff": next(
                ({"pos": q, "ref": cand[q], "got": c["sig"][q]}
                 for q in range(min(len(cand), len(c["sig"])))
                 if cand[q] != c["sig"][q]), None),
        })
    return out


def body_attrs_unchanged(cycles):
    """⭐⭐⭐ **假设 H 的判决**：`document.body` 自己那一下的可测属性，
    在「缺 `BODY` 的圈」里变没变。

    ⚠️⚠️⚠️ **第一版这里踩了「切片会把规律读反」那条纪律的**第四种形式**：
    ⚠️⚠️ **「缺席圈比参照圈少一行」⇒ 按行号对齐就是**整体错位一格****
    ⇒ 读出来的「它变了」**全是错位**，不是真相关。
    ⭐ **证据（可复算）**：完整圈的 `body_n_children` 跳变行号是
    `[…15, 17, 20, 24, 25]`，缺席圈是 `[…14, 16, 19, 23, 24]` —— **每个都恰好少 1**，
    而前 13 行**完全相同**。

    ⇒ 所以这里**两种对齐都算、都记**：
    - `naive_row_align` —— 按行号硬对（**保留当历史记录**：它是那处错位的现场）
    - `time_aligned` —— ⭐ **把参照圈在 `BODY` 那一行切开再拼**（正确的时间对齐）
    ⇒ **判决看 `time_aligned`**。
    """
    full = [c for c in cycles if c["has_body"]]
    miss = [c for c in cycles if not c["has_body"]]
    if not full or not miss:
        return {"comparable": False, "n_full": len(full), "n_missing": len(miss)}
    ref_cycle = full[0]
    ref = ref_cycle["body_attr_seq"]
    bidx = ref_cycle["body_sig_idx"]
    # ⭐ **正确的时间对齐**：参照圈删掉 `BODY` 那一行
    ref_cut = ref[:bidx] + ref[bidx + 1:]

    def cmp_seq(rows):
        n = min(len(rows), len(ref))
        return n, all(ref[i] == rows[i] for i in range(n)), next(
            ({"pos": i, "ref": ref[i], "got": rows[i]}
             for i in range(n) if ref[i] != rows[i]), None)

    def cmp_cut(rows):
        n = min(len(rows), len(ref_cut))
        return n, all(ref_cut[i] == rows[i] for i in range(n)), next(
            ({"pos": i, "ref": ref_cut[i], "got": rows[i]}
             for i in range(n) if ref_cut[i] != rows[i]), None)

    per_missing = []
    for c in miss:
        rows = c["body_attr_seq"]
        n_naive, same_naive, diff_naive = cmp_seq(rows)
        n_cut, same_cut, diff_cut = cmp_cut(rows)
        per_missing.append({
            "start": c["start"], "len": c["len"],
            "naive_row_align": {"cmp_len": n_naive, "all_same": same_naive,
                                "first_diff": diff_naive},
            "time_aligned": {"cmp_len": n_cut, "all_same": same_cut,
                             "first_diff": diff_cut},
        })
    # 反向：所有**完整**圈之间是否全同（若连完整圈都在变 ⇒ 参照本身不稳）
    full_pairwise = all(ref == c["body_attr_seq"] for c in full)
    return {
        "comparable": True, "n_full": len(full), "n_missing": len(miss),
        "ref_start": ref_cycle["start"], "ref_len": ref_cycle["len"],
        "ref_body_idx": bidx, "ref_first_row": ref[0] if ref else None,
        "ref_cut_len": len(ref_cut),
        "per_missing": per_missing,
        # ⭐ **判决**（两处必须同时给出：naive 是错位的现场，time_aligned 才是判决）
        "naive_all_same": all(p["naive_row_align"]["all_same"]
                              for p in per_missing),
        "all_same": all(p["time_aligned"]["all_same"] for p in per_missing),
        "full_cycles_identical": full_pairwise,
    }


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
            ap = [p for p in presses if p["phase"] == "arm_a"]
            if count_full_cycles(ap) >= CYCLES_PER_ARM:
                break
        cap_a = (k >= TAIL_CAP_A
                 and count_full_cycles([p for p in presses
                                        if p["phase"] == "arm_a"])
                 < CYCLES_PER_ARM)
        a_presses = [p for p in presses if p["phase"] == "arm_a"]
        rec["arm_a_presses"] = len(a_presses)
        rec["arm_a_cap_hit"] = cap_a
        rec["arm_a_cycles"] = cut_cycles(a_presses, MIN_CYCLE_LEN)
        rec["arm_a_short_vs_ref"] = short_cycle_vs_ref(rec["arm_a_cycles"])
        rec["arm_a_body_attrs"] = body_attrs_unchanged(rec["arm_a_cycles"])
        rec["arm_a_n_armed"] = sum(1 for p in a_presses if p["moved"])
        rec["arm_a_any_ti_set"] = sorted({p["post"]["n_wrapper_any_ti"]
                                          for p in a_presses})
        rec["arm_a_body_attr_global"] = {
            f: sorted({json.dumps(p["post"][f], ensure_ascii=False)
                       for p in a_presses}) for f in BODY_ATTRS}

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

        for k in range(1, TAIL_CAP_B + 1):
            prev_map = press_once("arm_b", k, KEY_REV, prev_map, presses, arm_stream)
            bp = [p for p in presses if p["phase"] == "arm_b"]
            if count_full_cycles(bp) >= CYCLES_PER_ARM:
                break
        cap_b = (k >= TAIL_CAP_B
                 and count_full_cycles([p for p in presses
                                        if p["phase"] == "arm_b"])
                 < CYCLES_PER_ARM)
        b_presses = [p for p in presses if p["phase"] == "arm_b"]
        rec["arm_b_presses"] = len(b_presses)
        rec["arm_b_cap_hit"] = cap_b
        rec["arm_b_cycles"] = cut_cycles(b_presses, MIN_CYCLE_LEN)
        rec["arm_b_short_vs_ref"] = short_cycle_vs_ref(rec["arm_b_cycles"])
        rec["arm_b_body_attrs"] = body_attrs_unchanged(rec["arm_b_cycles"])
        rec["arm_b_n_armed"] = sum(1 for p in b_presses if p["moved"])
        rec["arm_b_body_attr_global"] = {
            f: sorted({json.dumps(p["post"][f], ensure_ascii=False)
                       for p in b_presses}) for f in BODY_ATTRS}
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
            ba = rec[prefix + "_body_attrs"]
            return {
                "n_cycles": len(cs),
                "lens": [c["len"] for c in cs],
                "n_missing_body": sum(1 for c in cs if not c["has_body"]),
                "missing_at": [i + 1 for i, c in enumerate(cs)
                               if not c["has_body"]],
                "short_checked": sum(1 for s in sv if s["checked"]),
                "short_equal": [s["equal"] for s in sv if s["checked"]],
                "body_attrs_comparable": ba.get("comparable"),
                # ⚠️ naive 是**错位的现场**（保留当历史记录），判决看 time_aligned
                "body_attrs_naive_all_same": ba.get("naive_all_same"),
                "body_attrs_all_same": ba.get("all_same"),
                "body_attrs_full_identical": ba.get("full_cycles_identical"),
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
        print(f"  臂A：按了 {rec['arm_a_presses']} 次、{sa['n_cycles']} 圈、"
              f"缺 body {sa['n_missing_body']}（落第 {sa['missing_at']} 圈）、"
              f"短圈==整圈删BODY {sa['short_equal']}")
        print(f"    ⭐ H 判决：body 自身四量 缺席圈 vs 完整圈 —— "
              f"**按行号硬对（错位现场）={sa['body_attrs_naive_all_same']}**、"
              f"**按时间对齐（判决）={sa['body_attrs_all_same']}**、"
              f"完整圈之间全同={sa['body_attrs_full_identical']}")
        print(f"  臂B：退到0@{zero_at}、按了 {rec['arm_b_presses']} 次、"
              f"{sb['n_cycles']} 圈、缺 body {sb['n_missing_body']}"
              f"（落第 {sb['missing_at']} 圈）、"
              f"短圈==整圈删BODY {sb['short_equal']}")
        print(f"    ⭐ H 判决：按行号硬对={sb['body_attrs_naive_all_same']}、"
              f"**按时间对齐（判决）={sb['body_attrs_all_same']}**、"
              f"完整圈之间全同={sb['body_attrs_full_identical']}")
        print(f"    body 自身四量全臂取值：臂A {rec['arm_a_body_attr_global']}")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    t = m = 0
    hs = []
    for r in runs:
        sa, sb = r["sum_arm_a"], r["sum_arm_b"]
        t += sa["n_cycles"] + sb["n_cycles"]
        m += sa["n_missing_body"] + sb["n_missing_body"]
        for v in (sa["body_attrs_all_same"], sb["body_attrs_all_same"]):
            if v is not None:
                hs.append(v)
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']}")
        print(f"    臂A {sa['n_cycles']} 圈、缺 {sa['n_missing_body']}、"
              f"落点 {sa['missing_at']}")
        print(f"    臂B {sb['n_cycles']} 圈、缺 {sb['n_missing_body']}、"
              f"落点 {sb['missing_at']}")
    print(f"\n== ⭐ 跨轮合计 ==")
    print(f"  {m}/{t} 圈缺 document.body（{m * 100.0 / max(t, 1):.1f}%）")
    print(f"  ⭐ 假设 H（body 自身四量在缺席圈里变了）判决："
          f"all_same 全为 True 的臂数 = {sum(1 for x in hs if x)}/{len(hs)}")
    print("  ⚠️ **本批仍不判「随机 / 固定」**（§143 五那条纪律继续有效）")
    print(f"\n== 已写 {OUT} ==")
