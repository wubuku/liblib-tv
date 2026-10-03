#!/usr/bin/env python3
r"""batch 935 源站探针（**纯诊断**）：把 `document.body` 那一站的出没，
在 **DOM 可观测层面**系统地扫一遍 —— 目标是**测出「查不出来」**，而不是猜。

## 934（§144）留下的

- ⭐ **H 已被整个证伪**：`body_tabindex`/`body_tab_index`/`body_scroll_top` **全臂恒定**；
  `body_n_children` 会跳，但**按正确时间对齐后缺席圈与完整圈逐次全同（5/5）**
- ⚠️ 代价：934 第一版**按行号**比两个**行数不同**的序列 ⇒ **整体错位一格**
  ⇒ 读到的「它变了」是假的（**「切片会把规律读反」第四种形式**）

## ⭐ 935 的两个方法论要点（都是被 934 的坑逼出来的）

**① 对齐必须按 `dom_sig`、不许按行号。**
935 **不在整圈上比**，而是**先在每一圈里定位「那一 press 本身」**
（`post.active.dom_sig` 等于参照圈 `BODY` 那一站 `dom_sig` 的那次按压），
**再只比那一次** ⇒ **单点比较、错位根本无从发生。**
⚠️ 顺带还多测一个可证伪的读数：**缺席圈里到底有没有那么一次按压**
（若**找不到**，那 5/5「短圈 = 整圈删 BODY」就得重看）。

**② 目标不是找一个原因，而是把「查不出来」变成一条读数。**
⚠️ 934 已把 `document.body` 自己能测的全测了、全恒定 ⇒ **不许**接着在它身上找。
⇒ 935 在**同一时刻**系统地扫一批**互不相关的** DOM 可观测量，
**若没有任何一个在两类圈之间有差别** ⇒ ⇒ **「原理上不可从 DOM 查明」就是一条测出来的结论**
（不是假设）⇒ 复刻侧由此拿到一条**可以写进基线的边界**（§122 那条精神）。

## 扫的量（**都取在「那一 press」上，逐个单点比**）

- `body_*` 四项（承 934）、`n_focusable`
- `documentElement` 的 `scrollTop` / `clientHeight` / `scrollHeight`
- `window` 的 `scrollX` / `scrollY` / `innerHeight`
- **`document.hasFocus()`** ⭐（无头下焦点状态可能与真浏览器不同）
- **「那一 press」的 `pre.active` 落点**（`dom_sig` / `is_body` / `on_canvas_root`）
- `active_scroll_x/y`（焦点元素自己在不在视口内）

⚠️⚠️ **不许**因为「某个量有差别」就宣称它就是成因（934 已经吃过一次亏）：
**差别的个数如实报，成因标「未验证」**。

## 设计门（`design_ok`，**只判 setup，不判机制**）

1. `neutral_ok` / `neutral_never_armed_ok` —— 臂 A 起手 `any_ti ≡ 0` 且全程不布
2. `n_cycles_a_ok` / `n_cycles_b_ok` —— 两臂各 ≥ `CYCLES_PER_ARM` 个**完整**圈
3. `n_missing_ok` —— 两臂合计至少 **3** 个缺 `BODY` 的圈
   （⚠️ 不够就**照实报不足**、**不许**据此说什么；9% 的基率下圈数要先够）
4. `cap_ok` —— 没撞 cap

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe935_body_stop_sweep_src.py
"""

import json

OUT = "/tmp/b935-src-body-stop-sweep.json"
REPS = 2
SETTLE = 400
CYCLES_PER_ARM = 15
# ⚠️⚠️ 预算系数必须**高于实测单圈长度**（26–28）—— §139/§140 那条纪律
BUDGET_PER_CYCLE = 32
TAIL_CAP_A = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
TAIL_CAP_B = CYCLES_PER_ARM * BUDGET_PER_CYCLE + 40
N_FWD = 100
PAST = 10
FWD_CAP = 130
MIN_CYCLE_LEN = 20
MIN_MISSING_TOTAL = 3

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

# ⚠️ 尺子 = 934 那版 + ⭐ 935 的扫测量（**已有字段一个字都不改**）
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
  const DE = document.documentElement;
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
    body_tabindex: B ? B.getAttribute('tabindex') : null,
    body_tab_index: B ? B.tabIndex : null,
    body_n_children: B ? B.childElementCount : null,
    body_scroll_top: B ? Math.round(B.scrollTop) : null,
    // ⭐⭐ 935 新增：互不相关的 DOM 可观测量，**目标是把「查不出来」测成读数**
    de_scroll_top: DE ? Math.round(DE.scrollTop) : null,
    de_client_height: DE ? DE.clientHeight : null,
    de_scroll_height: DE ? DE.scrollHeight : null,
    win_scroll_x: Math.round(window.scrollX),
    win_scroll_y: Math.round(window.scrollY),
    win_inner_height: window.innerHeight,
    has_focus: document.hasFocus(),
    vis_state: document.visibilityState,
    active_rect: a && a.getBoundingClientRect
      ? [Math.round(a.getBoundingClientRect().top),
         Math.round(a.getBoundingClientRect().left)] : null,
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
# ⭐ 935 要扫的**全部**量（承 934 的四个 + 新增十个）
SWEEP_FIELDS = BODY_ATTRS + (
    "n_focusable", "de_scroll_top", "de_client_height", "de_scroll_height",
    "win_scroll_x", "win_scroll_y", "win_inner_height", "has_focus",
    "vis_state", "active_rect",
)
# ⚠️⚠️ **`pre_*` 那三个是「派生」字段、不是 census 里的原始键** ——
#    ⭐ 第一版把两类混在一个元组里、再按原始键去取 ⇒ **`KeyError: 'pre_dom_sig'`**
#    ⇒ **一次异常读数不足以立机制，两件事只能归因到其中一件：**
#    ① 这处崩溃是**取键方式**错；② **整轮读数全丢**是**落盘排得太晚**（下面已修）
DERIVED_PRE = ("pre_dom_sig", "pre_is_body", "pre_on_canvas_root")
DERIVED_POST = ("post_dom_sig", "post_is_body")
# ⭐⭐ 单点比较用的字段表（原始 + 派生，**比较时两类都在**）
POINT_FIELDS = SWEEP_FIELDS + DERIVED_PRE
# ⚠️⚠️⚠️ **这两条就是第一版那个 `KeyError` 的免疫针**：
#    ⭐ 第一版把「原始键」与「派生键」混在一个元组里、再按原始键去取
#    ⇒ 派生键必然取不到 ⇒ **`KeyError: 'pre_dom_sig'`**
#    ⇒ **「原始键」与「派生键」不许重叠**（重叠就说明**取法错了**）
assert not ((set(DERIVED_PRE) | set(DERIVED_POST)) & set(SWEEP_FIELDS)), \
    "派生键与 census 原始键**不许重叠**（第一版就是重叠 ⇒ KeyError）"
assert not (set(DERIVED_PRE) & set(DERIVED_POST)), \
    "pre/post 的派生键**不许重名**（否则单点比较会两边串味）"
assert all(f in SWEEP_FIELDS for f in BODY_ATTRS), \
    "934 的四个键必须原样留在扫测量里（不然两批不可比）"

# ⚠️ **探针自己长防线**
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
for fld in ("dom_sig", "owner_node_idx", "is_body", "fpos"):
    assert fld in CENSUS_JS, f"前批的字段 {fld} 被弄丢了"
for fld in BODY_ATTRS:
    assert fld in CENSUS_JS, f"934 的字段 {fld} 被弄丢了"
for fld in SWEEP_FIELDS:
    assert fld in CENSUS_JS, f"935 的扫测量 {fld} 没写上"
assert REPS >= 2, "一次成功不叫可靠"
assert CYCLES_PER_ARM >= 10, "9% 的基率下圈数太少 ⇒ 频率估不准（§139 那条）"
assert BUDGET_PER_CYCLE >= 30, "单圈实测 26–28，预算系数必须高于它（§139/§140）"
assert TAIL_CAP_A >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
assert TAIL_CAP_B >= CYCLES_PER_ARM * BUDGET_PER_CYCLE
# ⚠️⚠️ **不许拿 27/28 去切分**（周期本身是读数）
assert "== 27" not in CENSUS_JS and "== 28" not in CENSUS_JS
assert "on_canvas_root" in CENSUS_JS, "切分锚点必须是画布根停靠"
# ⚠️⚠️ 935 的核心纪律：**「那一 press」必须按 `dom_sig` 定位、不许按行号**
#    （934 第一版就是按行号比两个行数不同的序列 ⇒ 整体错位一格 ⇒ 读出假相关）
# ⚠️ **这条实现本身由 `scripts/jimeng_check_verifier_anchors.py` 去钉**
#    （它把探针源码当文本读）—— ⭐ **所以本探针不读自己的源码**：
#    harness 是 exec 进来的、`__file__` 未必可用，而「门跑在不可靠的前提下」
#    正是 §929 那条教训。**宁可把钉子交给那道能钉住它的门。**
assert MIN_CYCLE_LEN >= 20, "剔残尾的下限（实测单圈 26–28）"
assert len(POINT_FIELDS) >= 12, "单点比较的字段太少 ⇒ 扫不出东西"
assert len(SWEEP_FIELDS) >= 10, "扫测量太少 ⇒ 「查不出来」这个结论就不成立"


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def tabindex_map():
    return ev(MAP_JS)


KEEP = ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
        "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
        "removed", "added", "changed") + SWEEP_FIELDS + ("active",)

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
    roots = sum(1 for p in press_list if p["post"]["active"]["on_canvas_root"])
    return max(0, roots - 1)


def cut_cycles(press_list, min_len):
    """⭐ **按画布根停靠点切圈**（不许按周期切）；末圈与短于 `min_len` 的丢弃。"""
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
            "sig": [p["post"]["active"]["dom_sig"] for p in seg],
            "body_sig_idx": (body_pos[0] - 1) if body_pos else None,
        })
    return out_cycles


def locate_body_press(cycles, press_list):
    """⭐⭐ **按落点定位「那一 press 本身」** —— **不许按行号**（934 的坑）。

    ⚠️⚠️⚠️ **第一版的定位轴选错了、而且错得「看起来能跑」**：
    原本想找「`post.dom_sig` == 参照圈 `BODY` 那一站 `dom_sig`」的那一次按压。
    ⭐ **但 933/934 已经测出：缺席圈 == 整圈删掉 `BODY` 那一站**
    ⇒ **缺席圈的 `sig` 里压根没有 `BODY` 那个 `dom_sig`**
    ⇒ 那样定位的话，**缺席圈必然 `found=False`**，
    **而那恰恰是唯一要看的那些圈** ⇒ **整批会落空。**

    ⭐ **正确的轴是「离开 `BODY` 之前那一站的落点」**（即参照圈那一 press 的
    `pre.active.dom_sig`，全圈里是 `返回首页`）：缺席圈里**同样有一次按压从
    `返回首页` 出发**（只不过它的 `post` 落到了下一站 `与 AI 对话` 而不是 `BODY`）
    ⇒ **两类圈都能定位到唯一一次** ⇒ **单点比较、行号无关**。
    """
    full = [c for c in cycles if c["has_body"]]
    if not full:
        return {"ref_pre_sig": None, "points": [],
                "note": "**这一臂没有带 BODY 的圈** ⇒ 无参照可用"}
    ref = full[0]
    bidx = ref["body_sig_idx"]
    ref_press = press_list[ref["start"] + bidx - 1]
    ref_pre_sig = ref_press["pre"]["active"]["dom_sig"]
    ref_post_sig = ref_press["post"]["active"]["dom_sig"]
    points = []
    for c in cycles:
        hit = None
        for q in range(c["start"] - 1, c["end"]):
            if press_list[q]["pre"]["active"]["dom_sig"] == ref_pre_sig:
                hit = q + 1          # 1 基
                break
        if hit is None:
            points.append({"start": c["start"], "len": c["len"],
                           "has_body": c["has_body"], "found": False,
                           "note": "**这一圈里找不到「从那一站出发」的那次按压**"})
            continue
        points.append({
            "start": c["start"], "len": c["len"], "has_body": c["has_body"],
            "found": True, "row_press": hit,
            "row_in_cycle": hit - c["start"] + 1,
            "post_is_body": press_list[hit - 1]["post"]["active"]["is_body"],
        })
    return {"ref_pre_sig": ref_pre_sig, "ref_post_sig": ref_post_sig,
            "ref_start": ref["start"], "ref_body_row_in_cycle": bidx + 1,
            "ref_press": ref["start"] + bidx, "points": points}


def point_rows(press_list, cycles, loc):
    """把 `locate_body_press` 的定位**取成真实读数**（`pre` 与 `post` 各一份）。"""
    rows = []
    for pt in loc["points"]:
        if not pt.get("found"):
            rows.append(pt)
            continue
        p = press_list[pt["row_press"] - 1]
        # ⚠️ 原始键与派生键**分开取**（第一版混在一起 ⇒ KeyError）
        pre_raw = {f: p["pre"][f] for f in SWEEP_FIELDS}
        pre_der = {
            "pre_dom_sig": p["pre"]["active"]["dom_sig"],
            "pre_is_body": p["pre"]["active"]["is_body"],
            "pre_on_canvas_root": p["pre"]["active"]["on_canvas_root"],
        }
        post_raw = {f: p["post"][f] for f in SWEEP_FIELDS}
        post_der = {
            "post_dom_sig": p["post"]["active"]["dom_sig"],
            "post_is_body": p["post"]["active"]["is_body"],
        }
        rows.append({
            "start": pt["start"], "len": pt["len"],
            "has_body": pt["has_body"], "found": True,
            "row_press": pt["row_press"], "row_in_cycle": pt["row_in_cycle"],
            "post_is_body": pt["post_is_body"],
            "pre": {**pre_raw, **pre_der},
            "post": {**post_raw, **post_der},
        })
    return rows


def sweep_compare(rows):
    """⭐⭐⭐ **单点比较**：缺席圈 vs 带 BODY 圈，逐个字段比。
    ⇒ **一个字段都没差 ⇒ 「原理上不可从 DOM 查明」就是一条测出来的结论。**"""
    with_body = [r for r in rows if r.get("found") and r["has_body"]]
    without = [r for r in rows if r.get("found") and not r["has_body"]]
    if not with_body or not without:
        return {"comparable": False, "n_with": len(with_body),
                "n_without": len(without)}
    pre_diff, post_diff = {}, {}
    for f in POINT_FIELDS:
        if any(r["pre"][f] != with_body[0]["pre"][f] for r in without):
            pre_diff[f] = sorted({json.dumps(r["pre"][f], ensure_ascii=False)
                                  for r in without})
    for f in SWEEP_FIELDS:
        if any(r["post"][f] != with_body[0]["post"][f] for r in without):
            post_diff[f] = sorted({json.dumps(r["post"][f],
                                              ensure_ascii=False)
                                   for r in without})
    return {
        "comparable": True, "n_with": len(with_body), "n_without": len(without),
        "ref_row_press": with_body[0]["row_press"],
        "n_pre_fields_compared": len(POINT_FIELDS),
        "n_post_fields_compared": len(SWEEP_FIELDS),
        "pre_diff": pre_diff, "post_diff": post_diff,
        "pre_all_same": not pre_diff, "post_all_same": not post_diff,
        "any_diff": bool(pre_diff or post_diff),
        "with_body_pre": with_body[0]["pre"],
        "without_pre": [r["pre"] for r in without],
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
        rec["arm_a_n_armed"] = sum(1 for p in a_presses if p["moved"])
        rec["arm_a_any_ti_set"] = sorted({p["post"]["n_wrapper_any_ti"]
                                          for p in a_presses})
        # ⚠️⚠️⚠️ **落盘必须排在**所有**后处理之前**（900/923 那条纪律）：
        #    ⭐ **第一版把落盘排在 `point_rows` 之后** ⇒ 后处理一崩
        #    **整轮 9 分钟的原始读数全丢**（实测：KeyError ⇒ 进程退出、连文件都没有）
        #    ⇒ **原始读数一旦采到就先落盘，派生量算错了也还能重算。**
        if len(runs) < rep:      # ⚠️ 每轮只 append 一次（落盘要早、runs 不能重计）
            runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        loc_a = locate_body_press(rec["arm_a_cycles"], a_presses)
        rec["arm_a_loc"] = loc_a
        rec["arm_a_point_rows"] = point_rows(a_presses, rec["arm_a_cycles"],
                                             loc_a)
        rec["arm_a_sweep"] = sweep_compare(rec["arm_a_point_rows"])
        if len(runs) < rep:      # ⚠️ 每轮只 append 一次（落盘要早、runs 不能重计）
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
        rec["arm_b_n_armed"] = sum(1 for p in b_presses if p["moved"])
        loc_b = locate_body_press(rec["arm_b_cycles"], b_presses)
        rec["arm_b_loc"] = loc_b
        rec["arm_b_point_rows"] = point_rows(b_presses, rec["arm_b_cycles"],
                                             loc_b)
        rec["arm_b_sweep"] = sweep_compare(rec["arm_b_point_rows"])
        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        # ⚠️ 同上：**臂 B 的原始读数也先落盘**，派生量后算
        if len(runs) < rep:      # ⚠️ 每轮只 append 一次（落盘要早、runs 不能重计）
            runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        def summarize(prefix):
            cs = rec[prefix + "_cycles"]
            rows = rec[prefix + "_point_rows"]
            sw = rec[prefix + "_sweep"]
            return {
                "n_cycles": len(cs),
                "lens": [c["len"] for c in cs],
                "n_missing_body": sum(1 for c in cs if not c["has_body"]),
                "missing_at": [i + 1 for i, c in enumerate(cs)
                               if not c["has_body"]],
                # ⭐ 「缺席圈里找不找得到那一 press」
                "n_not_found": sum(1 for r in rows if not r.get("found")),
                "n_found": sum(1 for r in rows if r.get("found")),
                "sweep_comparable": sw.get("comparable"),
                "sweep_pre_all_same": sw.get("pre_all_same"),
                "sweep_post_all_same": sw.get("post_all_same"),
                "sweep_pre_diff": sorted(sw.get("pre_diff", {}).keys()),
                "sweep_post_diff": sorted(sw.get("post_diff", {}).keys()),
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
        print(f"  臂A：{sa['n_cycles']} 圈、缺 body {sa['n_missing_body']}"
              f"（落第 {sa['missing_at']} 圈）、"
              f"「那一 press」找到 {sa['n_found']} / 找不到 {sa['n_not_found']}")
        print(f"    ⭐ 单点扫：pre 全同={sa['sweep_pre_all_same']}"
              f"（{sa['sweep_pre_diff']}）、post 全同={sa['sweep_post_all_same']}"
              f"（{sa['sweep_post_diff']}）")
        print(f"  臂B：{sb['n_cycles']} 圈、缺 body {sb['n_missing_body']}"
              f"（落第 {sb['missing_at']} 圈）、"
              f"「那一 press」找到 {sb['n_found']} / 找不到 {sb['n_not_found']}")
        print(f"    ⭐ 单点扫：pre 全同={sb['sweep_pre_all_same']}"
              f"（{sb['sweep_pre_diff']}）、post 全同={sb['sweep_post_all_same']}"
              f"（{sb['sweep_post_diff']}）")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    t = m = nf = 0
    any_diff_arms = 0
    n_arms = 0
    for r in runs:
        sa, sb = r["sum_arm_a"], r["sum_arm_b"]
        t += sa["n_cycles"] + sb["n_cycles"]
        m += sa["n_missing_body"] + sb["n_missing_body"]
        nf += sa["n_not_found"] + sb["n_not_found"]
        for s in (sa, sb):
            n_arms += 1
            if s["sweep_pre_all_same"] is False or s["sweep_post_all_same"] is False:
                any_diff_arms += 1
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']}")
        print(f"    臂A {sa['n_cycles']} 圈、缺 {sa['n_missing_body']}、"
              f"找不到那一 press {sa['n_not_found']}")
        print(f"    臂B {sb['n_cycles']} 圈、缺 {sb['n_missing_body']}、"
              f"找不到那一 press {sb['n_not_found']}")
    print(f"\n== ⭐ 跨轮合计 ==")
    print(f"  {m}/{t} 圈缺 document.body（{m * 100.0 / max(t, 1):.1f}%）")
    print(f"  「那一 press」找不到的圈数 = {nf}（0 ⇒ 935 那条定位在缺席圈里也成立）")
    print(f"  ⭐ 单点扫**发现差别**的臂数 = {any_diff_arms}/{n_arms}")
    print("  ⚠️ **差别的个数如实报、成因标「未验证」**"
          "（934 已经吃过一次「相关是错位造出来的」的亏）")
    print(f"\n== 已写 {OUT} ==")
