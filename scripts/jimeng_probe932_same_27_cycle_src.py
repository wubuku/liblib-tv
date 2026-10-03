#!/usr/bin/env python3
r"""batch 932 源站探针（**纯诊断**）：**「那 27 步整页闭环」是不是同一个闭环？**

## 931 留下的两件事

**① 「两侧用的是同一个 27」这句话，到 931 为止只验了「个数相同」。**
931 在收尾时重读了 §132 的落盘（`/tmp/b922-src-reverse-arm-window.json`
那个 60 站 `entry` 序列），发现 §132 那个 27 步闭环的真实构成是
`用户菜单…文本`（17 站）＋ 9 个内层控件 ＋ `Canvas` = **27**，
而 931 反向那一圈去掉被布本体后**逐条全等**（只是整体转了一格）
⇒ **「同一个 27」可以从「个数相同」升级为「逐条全等」。**

**② ⚠️ 但顺手撞出 §132 的一处错**：§132 基线写
「`添加素材到时间线`/`静音`/`全屏编辑`/`导出时间线`/`替换媒体`，**各出现 2 次**」
⇒ 逐条数下来是 **4 个 ×2、而 `替换媒体` 只有 1 次**（2/2 一致）。

## ⭐ 932 为什么必须换一把新尺子

⚠️⚠️ **931 的 `fpos`（焦点在「可聚焦元素序列」里的序号）跨状态不可比**：
`fpos` 的分母是**当前可聚焦集合的大小**
⇒ 中性态（`any_ti = 0`，本体都没有 `tabindex`）与越界尾巴（`any_ti = 75`）
**两个状态的可聚焦集合大小不同 ⇒ 同一个元素的 `fpos` 数值不同**
⇒ **拿 `fpos` 去跨状态对齐两段走线是错的。**

⇒ 932 加两个**与状态无关**的身份：
- ⭐ `active.dom_sig` —— **结构路径**（`tag:nth-of-type(...)` 逐级上溯，深度封顶）
  ⇒ 与「哪些元素可聚焦」**完全无关** ⇒ 跨状态可比。
- ⭐ `active.owner_node_idx` —— **最近那个 `.react-flow__node` 祖先的 DOM 下标**
  （没有就 -1）⇒ 直接回答 §141 九(1) 那个没答的问题：
  **「那 9 个节点邻近槽位里坐的控件，属于哪个节点？」**

## 设计：⭐ **同一次运行里跑两臂、共用同一把尺子**

- **臂 A（中性态）**：点画布空白 ⇒ 验 `any_ti == 0` ⇒ 连按 `N_NEUTRAL` 次 `Shift+Tab`
- **臂 B（越界尾巴）**：再点一次空白（把焦点放回画布根）⇒ 正向走到末尾、
  反向退到 `0`，然后**自适应**连按到第 `MIN_RETURNS` 次落回被布本体

⚠️ **臂 A 一次都不布**（§132 已查清：中性态从画布根反向按压不布）
⇒ **臂 A 跑完的 `tabindex` 状态与跑之前完全一样**
⇒ 两臂之间**不需要 reload**，却在**同一页、同一把尺子**下测到。

## 判别点（**只输出读数、不判机制**）

1. 臂 A 的站表周期是多少？（§132 当年记 27）
2. 臂 A 的 27 站与臂 B 尾巴里那 27 站（去掉被布本体）**按 `dom_sig` 逐条对齐**
   是不是全等？
3. 那 9 个节点邻近槽位里的元素，`owner_node_idx` 是多少？
   ⇒ **它跟「被布的那个本体」是同一个节点吗？**

## 设计门（`design_ok`，**只判 setup，不判机制**）

1. `neutral_ok` —— 臂 A 起手时 `any_ti == 0`（真的是中性态）
2. `n_neutral_ok` —— 臂 A 真的按了 `N_NEUTRAL` 次（覆盖 ≥2 个周期）
3. `neutral_never_armed_ok` —— 臂 A 全程 `moved` 全 False
   （⚠️ 这是**门**不是读数：它一旦为真就说明臂 A 确实没干扰状态）
4. `reached_0_ok` —— 臂 B 反向真的退到了 `0`
5. `n_returns_ok` —— 臂 B 尾巴落回被布本体 ≥ `MIN_RETURNS` 次
6. `cap_ok` —— 没有撞 `TAIL_CAP`（撞了只能报「读数不足」）

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe932_same_27_cycle_src.py
"""

import json

OUT = "/tmp/b932-src-same-27-cycle.json"
REPS = 2
SETTLE = 400
N_NEUTRAL = 60        # ⚠️ §132 当年是 60（覆盖 2 个周期），这里逐字沿用
N_FWD = 100
PAST = 10
MIN_ARM = 3
FWD_CAP = 130
MIN_RETURNS = 4       # ⇒ 至少 3 个间隔
TAIL_CAP = 200

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

# ⚠️⚠️ **尺子 = 931 那版 + 932 的两个「与状态无关」的新增字段**。
#    **已有字段的算法一个字都不改**（只加不改，928 起的纪律）。
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
  // ⭐⭐ 932 新增 ①：**与状态无关**的结构路径。
  //    只用 tag + nth-of-type 逐级上溯 —— **不掺 aria / class / tabindex**
  //    ⇒ 与「哪些元素可聚焦」无关 ⇒ 中性态与越界尾巴之间可比。
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
  // ⭐⭐ 932 新增 ②：最近那个 `.react-flow__node` 祖先的 DOM 下标
  //    ⇒ 回答「那 9 个节点邻近槽位里的控件属于哪个节点」
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
      fpos: a ? fset.indexOf(a) : -1,     // ⚠️ **跨状态不可比**，只作同状态参考
      dom_sig: domSig(a),                 // ⭐⭐ 932 新增：可比
      owner_node_idx: ownerIdx(a),        // ⭐⭐ 932 新增
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
assert "dom_sig" in CENSUS_JS and "owner_node_idx" in CENSUS_JS, "932 的新字段没写上"
assert "fpos" in CENSUS_JS, "931 的字段要留着（同状态内仍有用）"
assert REPS >= 2, "一次成功不叫可靠"
assert MIN_RETURNS >= 4, "少于 4 次落回 ⇒ 间隔不足 3 个"
assert TAIL_CAP >= MIN_RETURNS * 30, "cap 要够宽，窄了会把「读数不足」误当读数"
# ⚠️⚠️ **不许把 §132/§931 那个 27 钉成期望值** —— 932 要问的就是「是不是同一个」
assert "== 27" not in CENSUS_JS
# ⚠️ **不许把 dom_sig 写成掺了 aria 的**（掺了就不再「与状态无关」）
assert "getAttribute" not in CENSUS_JS.split("const domSig")[1].split(
    "const ownerIdx")[0], "dom_sig 里不许掺任何属性（会重新绑回 aria）"


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


def gaps_of(positions):
    return [positions[i + 1] - positions[i]
            for i in range(len(positions) - 1)]


def sig_of(rec_press):
    return rec_press["post"]["active"]["dom_sig"]


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
        rec = {"rep": rep, "n_neutral": N_NEUTRAL, "tail_cap": TAIL_CAP,
               "min_returns": MIN_RETURNS}

        presses = []
        arm_stream = []
        prev_map = tabindex_map()

        # ================= 臂 A：中性态下从画布根反向走整页 =================
        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["arm_a_blank_hit"] = sp
        rec["census_at_blank"] = ev(CENSUS_JS, None)
        rec["arm_a_any_ti_at_start"] = rec["census_at_blank"]["n_wrapper_any_ti"]

        for k in range(1, N_NEUTRAL + 1):
            prev_map = press_once("neutral", k, KEY_REV, prev_map, presses,
                                  arm_stream)

        # ⚠️⚠️ **落盘必须排在所有后处理与设计门之前**（900/923 的教训）
        runs.append(rec)
        out["runs"] = runs
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ================= 臂 B：越界尾巴（同一页、同一把尺子）=================
        sp2 = ev(BLANK_JS)
        if sp2:
            page.mouse.click(sp2[0], sp2[1])
            page.wait_for_timeout(900)
        rec["arm_b_blank_hit"] = sp2
        rec["arm_b_any_ti_at_start"] = ev(CENSUS_JS, None)["n_wrapper_any_ti"]

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

        zero_at = None
        for k in range(1, FWD_CAP + 1):
            prev_map = press_once("rev", k, KEY_REV, prev_map, presses, arm_stream)
            p = presses[-1]
            if zero_at is None and p["moved"] and p["post"]["zero_idx"] \
                    and p["post"]["zero_idx"][0] == 0:
                zero_at = k
                break
        rec["zero_at"] = zero_at
        armed_body = presses[-1]["post"]["zero_idx"][0] \
            if presses[-1]["post"]["zero_idx"] else None
        rec["armed_body_idx"] = armed_body

        ret_armed_at = []
        cap_hit = False
        for k in range(1, TAIL_CAP + 1):
            prev_map = press_once("tail", k, KEY_REV, prev_map, presses, arm_stream)
            act = presses[-1]["post"]["active"]
            if act["is_wrapper"] and act["wrapper_idx"] == armed_body \
                    and act["ti_attr"] == "0":
                ret_armed_at.append(k)
            if len(ret_armed_at) >= MIN_RETURNS:
                break
        else:
            cap_hit = (len(ret_armed_at) < MIN_RETURNS)
        rec["cap_hit"] = cap_hit
        rec["ret_armed_at"] = ret_armed_at
        rec["gaps_armed"] = gaps_of(ret_armed_at)

        rec["presses"] = presses
        rec["arm_stream"] = arm_stream
        rec["arm_seq_neutral"] = [i for ph, i in arm_stream if ph == "neutral"]
        rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
        rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]

        neut = [p for p in presses if p["phase"] == "neutral"]
        tail = [p for p in presses if p["phase"] == "tail"]
        rec["arm_a"] = {
            "n_presses": len(neut),
            "n_armed": sum(1 for p in neut if p["moved"]),
            "aria_seq": [p["post"]["active"]["aria"] for p in neut],
            "sig_seq": [sig_of(p) for p in neut],
            "owner_seq": [p["post"]["active"]["owner_node_idx"] for p in neut],
            "any_ti_series": [p["post"]["n_wrapper_any_ti"] for p in neut],
        }
        rec["arm_b_tail"] = {
            "n_presses": len(tail),
            "n_armed": sum(1 for p in tail if p["moved"]),
            "aria_seq": [p["post"]["active"]["aria"] for p in tail],
            "sig_seq": [sig_of(p) for p in tail],
            "owner_seq": [p["post"]["active"]["owner_node_idx"] for p in tail],
        }

        # ---- 臂 A 的周期（**原样记录、不与 27 比**）----
        a_sig = rec["arm_a"]["sig_seq"]
        a_root = [i + 1 for i, p in enumerate(neut)
                  if p["post"]["active"]["on_canvas_root"]]
        rec["arm_a_root_at"] = a_root
        rec["arm_a_root_gaps"] = gaps_of(a_root)

        # ---- ⭐ 两臂按 `dom_sig` 对齐：臂 A 的一个周期 vs 臂 B 尾巴里那一圈 ----
        # 臂 B 的一圈 = 从「画布根」到「下一次画布根之前」
        b_root = [i + 1 for i, p in enumerate(tail)
                  if p["post"]["active"]["on_canvas_root"]]
        rec["arm_b_root_at"] = b_root
        b_sig = rec["arm_b_tail"]["sig_seq"]
        b_laps = []
        for j, s_k in enumerate(b_root):
            e_k = (b_root[j + 1] - 1) if (j + 1 < len(b_root)) else len(tail)
            b_laps.append((s_k, e_k, b_sig[s_k - 1: e_k]))
        rec["arm_b_lap_bounds"] = [(s, e) for s, e, _ in b_laps]
        rec["arm_b_lap_lens"] = [len(sig) for _, _, sig in b_laps]
        rec["arm_b_laps_identical"] = (
            len(b_laps) >= 2 and all(sig == b_laps[0][2] for _, _, sig in b_laps))

        # 臂 A 的一个周期：从画布根到下一次画布根之前
        a_laps = []
        for j, s_k in enumerate(a_root):
            e_k = (a_root[j + 1] - 1) if (j + 1 < len(a_root)) else len(neut)
            a_laps.append((s_k, e_k, a_sig[s_k - 1: e_k]))
        rec["arm_a_lap_bounds"] = [(s, e) for s, e, _ in a_laps]
        rec["arm_a_lap_lens"] = [len(sig) for _, _, sig in a_laps]
        rec["arm_a_laps_identical"] = (
            len(a_laps) >= 2 and all(sig == a_laps[0][2] for _, _, sig in a_laps))

        # ⭐⭐ 对齐：把臂 A 第一圈与臂 B 第一圈**按 dom_sig 找共同子序列**
        #    （环是循环的 ⇒ 允许 A 从任意一站起转）
        def align(lap_a, lap_b):
            if not lap_a or not lap_b:
                return {"a_len": len(lap_a), "b_len": len(lap_b),
                        "offset": None, "equal": False}
            best = None
            for off in range(len(lap_a)):
                rot = lap_a[off:] + lap_a[:off]
                n = min(len(rot), len(lap_b))
                same = sum(1 for q in range(n) if rot[q] == lap_b[q])
                if best is None or same > best[1]:
                    best = (off, same)
            off, same = best
            rot = lap_a[off:] + lap_a[:off]
            n = min(len(rot), len(lap_b))
            first_diff = next(
                ({"pos": q, "a": rot[q], "b": lap_b[q]}
                 for q in range(n) if rot[q] != lap_b[q]), None)
            return {"a_len": len(lap_a), "b_len": len(lap_b),
                    "offset": off, "matched": same, "cmp_len": n,
                    "equal": same == n and len(lap_a) == len(lap_b),
                    "first_diff": first_diff}

        rec["align_a0_b0"] = align(
            a_laps[0][2] if a_laps else [], b_laps[0][2] if b_laps else [])
        rec["align_a0_b0_aria"] = align(
            [x["post"]["active"]["aria"]
             for x in neut[(a_laps[0][0] - 1 if a_laps else 0):
                           (a_laps[0][1] if a_laps else 0)]],
            [x["post"]["active"]["aria"]
             for x in tail[(b_laps[0][0] - 1 if b_laps else 0):
                           (b_laps[0][1] if b_laps else 0)]]) \
            if a_laps and b_laps else None

        # ⭐ 那 9 个「节点邻近槽位」的 owner：在臂 A 与臂 B 里各是什么
        rec["owner_at_a"] = [
            {"k": q + 1, "aria": (neut[q]["post"]["active"]["aria"] or "")[:18],
             "owner": neut[q]["post"]["active"]["owner_node_idx"]}
            for q in range(len(neut))
            if neut[q]["post"]["active"]["owner_node_idx"] >= 0]
        rec["owner_at_b"] = [
            {"k": q + 1, "aria": (tail[q]["post"]["active"]["aria"] or "")[:18],
             "owner": tail[q]["post"]["active"]["owner_node_idx"]}
            for q in range(len(tail))
            if tail[q]["post"]["active"]["owner_node_idx"] >= 0]

        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        # ---------- 设计门：只判 setup ----------
        neutral_ok = (rec["arm_a_any_ti_at_start"] == 0)
        n_neutral_ok = (rec["arm_a"]["n_presses"] >= N_NEUTRAL)
        neutral_never_armed_ok = (rec["arm_a"]["n_armed"] == 0)
        reached_0_ok = (zero_at is not None)
        n_returns_ok = (len(ret_armed_at) >= MIN_RETURNS)
        rec["design_ok"] = {
            "neutral_ok": bool(neutral_ok),
            "n_neutral_ok": bool(n_neutral_ok),
            "neutral_never_armed_ok": bool(neutral_never_armed_ok),
            "reached_0_ok": bool(reached_0_ok),
            "n_returns_ok": bool(n_returns_ok),
            "cap_ok": (not cap_hit),
            "n_returns": len(ret_armed_at),
            "arm_a_lap_lens": rec["arm_a_lap_lens"],
            "arm_b_lap_lens": rec["arm_b_lap_lens"],
            "all_ok": bool(neutral_ok and n_neutral_ok
                           and neutral_never_armed_ok and reached_0_ok
                           and n_returns_ok and not cap_hit),
        }
        print(f"  n_nodes={n_nodes} | 中性态 any_ti@起手="
              f"{rec['arm_a_any_ti_at_start']}、臂A 按了 {rec['arm_a']['n_presses']} 次、"
              f"布了 {rec['arm_a']['n_armed']} 次")
        print(f"    臂A 各圈长度 {rec['arm_a_lap_lens']}、圈间一致="
              f"{rec['arm_a_laps_identical']}")
        print(f"    臂B 退到0@{zero_at}（被布本体={armed_body}）、尾巴 "
              f"{rec['arm_b_tail']['n_presses']} 次、各圈长度 {rec['arm_b_lap_lens']}、"
              f"圈间一致={rec['arm_b_laps_identical']}")
        al = rec["align_a0_b0"]
        print(f"    ⭐ 按 dom_sig 对齐（允许转动）：A 圈长 {al['a_len']} vs B 圈长 "
              f"{al['b_len']}、offset={al['offset']}、逐条全等={al['equal']}"
              f"（相同 {al['matched']}/{al['cmp_len']}）")
        if al.get("first_diff"):
            print(f"       首处不同：{al['first_diff']}")
        print(f"    臂A 里带 owner 的停靠 {len(rec['owner_at_a'])} 个；"
              f"臂B 里 {len(rec['owner_at_b'])} 个")
        print(f"  => design_ok={rec['design_ok']['all_ok']}")

    out["verdict"] = "sampled"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        al = r["align_a0_b0"]
        print(f"  rep{r['rep']} design_ok={r['design_ok']['all_ok']} "
              f"cap_hit={r['cap_hit']}")
        print(f"    臂A 各圈 {r['arm_a_lap_lens']}、圈间一致="
              f"{r['arm_a_laps_identical']}")
        print(f"    臂B 各圈 {r['arm_b_lap_lens']}、圈间一致="
              f"{r['arm_b_laps_identical']}")
        print(f"    ⭐ 对齐：A {al['a_len']} vs B {al['b_len']}、offset "
              f"{al['offset']}、全等={al['equal']}、"
              f"匹配 {al['matched']}/{al['cmp_len']}")
        print(f"    臂A owner：{[(o['aria'], o['owner']) for o in r['owner_at_a']]}")
        print(f"    臂B owner：{[(o['aria'], o['owner']) for o in r['owner_at_b']]}")
    print("\n== ⭐ 跨轮对照 ==")
    if len(runs) >= 2:
        a, b = runs
        print(f"  臂A 圈长 {a['arm_a_lap_lens']} → {b['arm_a_lap_lens']}；"
              f"臂B 圈长 {a['arm_b_lap_lens']} → {b['arm_b_lap_lens']}")
        print(f"  对齐结果：{a['align_a0_b0']['equal']} → "
              f"{b['align_a0_b0']['equal']}（offset "
              f"{a['align_a0_b0']['offset']} → {b['align_a0_b0']['offset']}）")
    print(f"\n== 已写 {OUT} ==")
