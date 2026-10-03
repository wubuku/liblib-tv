#!/usr/bin/env python3
r"""batch 947 源站探针（**纯诊断**）：⭐⭐⭐ 拆 944 矛盾**剩下的**那个可疑变量。

## 944 那个矛盾现在被逼到一个墙角了

945 排除了 **规模**（`scale`）与 **那一击是不是臂事件**（`mode`）；
946 的 `warm` **压根没被操控过**（见 946 §零）⇒ 三个都不成立。
而 946 ⭐⭐⭐⭐⭐ **原样重现**了那个矛盾：同一段代码，rep1 第 1 击 `Tab` **75 → 1**、
rep2 **75 → 8**。

⇒ 剩下唯一还没被人**当自变量操控过**的差别，是这个：

| | 每次点击后 | `identity_stable` |
| --- | --- | --- |
| **945** | 只等 `350ms` 就普查 | 大段 **True** |
| **946** | 只等 `350ms` 就普查 | 大段 **False**（第 3 击起） |

⭐ 而 946 已经证明这件事**有后果**：`delta()` 在 `identity_stable=False` 时
**按构造**返回空三元组 ⇒ 那一段的所有 `added/removed/changed` **全都不作数**。

⇒ 本批就测它：**每次点击后等身份稳定**（受控侧）vs **不等**（对照侧）。

## 本批的设计：**单变量**、**短**、**带 sham 级对照**

- **唯一自变量 `wait_stable ∈ {False, True}`**
- 固定：settle 循环**照抄 945**（按 `Tab` 到 `n_without_ti <= 1` 为止、上限 14 下）
  ⇒ **前置态与 945 同侧**（这一侧 945 测到 `added=8`，读数可与 945 对照）
- 固定 `scale = 8`、固定 `mode = body`
- 每格**独立 `boot()`**；**2 轮**

## ⭐⭐ 本批自己设计的「反恒绿」门

`wait_stable=True` 那一格如果**测不出任何差别**，那这道门就是恒绿的
（和 946 的 `warm_reached` 同一个病，**已撤回**）⇒
所以加 `manip_moved_something`：两格的 `n_poll` 最大值或 `settled` 计数
**必须不一样**，否则**本批作废**。
⇒ ⭐ **「这个操纵到底动了没有」必须自己答，不能默认它动了。**

## 读什么

- 每击的 `n_poll`（轮了几次才等到身份稳定）与 `settled`（等到了没有）
- `click_rows`（三元组 + `identity_stable`）与 `tabs`（逐击）
- `w_after_clicks` / `w_after_tab1` / `w_final` 与 `compensated`
- `settle_traj`：settle 循环里 `不带 ti` 的**整条轨迹**（946 只知道两个端点 76 / 0）

## 探针自带的纪律（承 943/944/945/946）

1. ⭐ **防漂移**：五段 JS **逐字 assert 与 946 相同**（940 的办法）
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131：切片会把规律读反）
7. ⚠️ **不许拿陈旧普查当基线**；⚠️ **身份不稳的那一段三元组一律不许当读数**（946）

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」。**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe947_stablewait_src.py
"""

import json
import pathlib

OUT = "/tmp/b947-stablewait.json"
REPS = 2
P946 = pathlib.Path(__file__).with_name(
    "jimeng_probe946_prestate_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_REC = 3                 # 连点后按几下 Tab（第 1 击是关键）
SETTLE_MAX = 14           # settle 循环上限（照抄 945）
SCALE_FIXED = 8           # ⭐ 固定规模
POLL_MAX = 6              # 每次点击后最多轮询几次
POLL_GAP = 250
# ⭐ 唯一自变量
CELLS = [{"wait_stable": False}, {"wait_stable": True}]

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti",
    "active_tag", "active_tid", "focus_in_node", "blank", "point", "i",
    "k", "hit_tag", "focus_ok",
})
DERIVED_KEYS = frozenset({
    "ci", "wait_stable", "n_audio_rail_button", "settle_presses",
    "ready_without_ti", "settle_traj", "landable_found", "n_click",
    "click_bites", "n_poll_max", "n_poll_total", "n_settled",
    "w_after_clicks", "w_after_tab1", "w_final", "compensated",
    "n_added_total", "cell_ok", "reps_identical", "design_gates",
    "manip_moved_something",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("wait_stable", "compensated", "cell_ok", "reps_identical",
              "manip_moved_something"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "removed", "added", "n_without_ti",
             "active_tag", "focus_in_node"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"

# ── 五段 JS：与 946 **逐字相同**（下面统一 assert）
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

CENSUS_JS = """([nodeSel]) => {
  const nodes = Array.from(document.querySelectorAll(nodeSel));
  const ti = {}, ids = {}, cls = {};
  let n_with_ti = 0;
  nodes.forEach((el, i) => {
    const has = el.hasAttribute('tabindex');
    if (has) n_with_ti += 1;
    ti[i] = has ? el.getAttribute('tabindex') : null;
    ids[i] = (el.getAttribute('data-testid') || '')
      + '|' + (el.getAttribute('aria-label') || '')
      + '|' + (el.innerText || '').slice(0, 24);
    cls[i] = el.className;
  });
  return {n_nodes: nodes.length, n_with_ti: n_with_ti,
          n_without_ti: nodes.length - n_with_ti,
          ti: ti, ids: ids, cls: cls};
}"""

POINT_JS = """([nodeSel, i, forbidden]) => {
  const el = document.querySelectorAll(nodeSel)[i];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const f = [0.5, 0.35, 0.65, 0.2, 0.8];
  for (const y0 of f) {
    for (const x0 of f) {
      const x = Math.round(r.left + r.width * x0);
      const y = Math.round(r.top + r.height * y0);
      if (x < 0 || y < 0) continue;
      const at = document.elementFromPoint(x, y);
      if (!at) continue;
      const tag = (at.tagName || '').toUpperCase();
      if (forbidden.indexOf(tag) >= 0) continue;
      if (!el.contains(at)) continue;
      return [x, y, tag];
    }
  }
  return null;
}"""

FOCUS_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {active_tag: null, active_tid: null, focus_in_node: false};
  const host = a.closest('[data-testid]');
  const node = a.closest(nodeSel);
  return {active_tag: (a.tagName || '').toUpperCase(),
          active_tid: host ? host.getAttribute('data-testid') : null,
          focus_in_node: !!node};
}"""

ARM_FOCUS_JS = """([nodeSel]) => {
  const el = document.querySelector(nodeSel + '[tabindex="0"]');
  if (!el) return {focus_ok: false, why: '找不到带 tabindex=0 的节点'};
  el.focus();
  return {focus_ok: document.activeElement === el,
          active_tag: (document.activeElement.tagName || '').toUpperCase()};
}"""

_JS_ALL = (CENSUS_JS, POINT_JS, FOCUS_JS, ARM_FOCUS_JS)
SLICE_STR = "|| '').slice(0, "
# ⭐⭐ 守卫常量自己必须能匹配上东西（946 第一版漏一个逗号 ⇒ 这道门恒绿）
assert any(SLICE_STR in _js for _js in _JS_ALL), (
    "SLICE_STR 自己就匹配不上任何一段 JS —— 这道门恒绿，等于没有门")
for _name, _js in zip(("CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"),
                      _JS_ALL):
    assert _js.count("slice(") == _js.count(SLICE_STR), (
        f"{_name} 里有**非字符串**切片（§131：切片会把规律读反）")

_p946src = P946.read_text(encoding="utf-8") if P946.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS",
                       "ARM_FOCUS_JS"),
                      (BLANK_JS,) + _JS_ALL):
    assert _js in _p946src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 946 那份**不一致** —— 两份定义开始分家了")


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def guard(al, tid):
    """⛔ 计费守卫：契约是「**我正要点的这个元素**是什么」。"""
    if tid in FORBIDDEN_TIDS:
        raise AssertionError(f"拒绝点击计费入口 testid={tid!r}")
    t = (al or "").strip()
    if t in BILLED_EXACT or t.split(":")[0].strip() in BILLED_EXACT:
        raise AssertionError(f"拒绝点击计费文案 {t!r}")
    for b in BILLED_PREFIX:
        if t.startswith(b):
            raise AssertionError(f"拒绝点击计费文案 {t!r}")


def guard_point(x, y):
    at = ev("""([x, y]) => {
      const el = document.elementFromPoint(x, y);
      if (!el) return null;
      const host = el.closest('[data-testid]');
      return {tid: host ? host.getAttribute('data-testid') : null,
              al: (el.innerText || el.textContent || '').slice(0, 40)};
    }""", [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


def boot_fn():
    """重新 goto 并等登录态（940：AI 侧栏 Esc 关不掉 ⇒ 每格都得重开）。"""
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    return n


def delta(pre, post):
    """逐**身份**对齐的两张表之差；身份对不上**如实记下**（943 的教训）。
    ⚠️ **身份对不上时三元组是空的是构造性产物，不是现象**（946）。"""
    a, b = pre["ids"], post["ids"]
    if a != b:
        diff = sorted({int(k) for k in set(a) | set(b)
                       if a.get(k) != b.get(k)})
        return {"identity_stable": False, "removed": [], "added": [],
                "changed": [], "n_without_ti": post["n_without_ti"],
                "bit": False, "diff_ids": diff}
    removed, added, changed = [], [], []
    ta, tb = pre["ti"], post["ti"]
    for i in sorted(a, key=lambda x: int(x)):
        was, cur = ta[i], tb[i]
        if was is None and cur is not None:
            added.append(int(i))
        elif was is not None and cur is None:
            removed.append(int(i))
        elif was != cur:
            changed.append([int(i), was, cur])
    return {"identity_stable": True, "removed": removed, "added": added,
            "changed": changed, "n_without_ti": post["n_without_ti"],
            "bit": bool(removed or added or changed), "diff_ids": []}


def settle_census(max_poll=POLL_MAX, gap=POLL_GAP):
    """⭐ **本批的新件**：轮询普查直到**连续两次的身份表相同**。

    ⚠️ 判据是「**两次读数彼此相同**」，不是「与点击前相同」——
    点击本来就该改东西，拿「与点击前相同」当稳定条件是**问错了问题**。
    返回 `(读数, 轮了几次, 等到了没有)`。
    """
    n = 0
    prev = ev(CENSUS_JS, [NODE_SEL])
    while n < max_poll:
        page.wait_for_timeout(gap)
        cur = ev(CENSUS_JS, [NODE_SEL])
        n += 1
        if cur["ids"] == prev["ids"]:
            return cur, n, True
        prev = cur
    return prev, n, False


def stable_key(cell):
    """两轮逐条比较用的键。⚠️ `settle_traj` 排除外：长度可变。"""
    return {k: cell.get(k) for k in
            ("wait_stable", "settle_presses", "ready_without_ti",
             "landable_found", "n_click", "click_bites", "n_poll_max",
             "n_poll_total", "n_settled", "w_after_clicks", "w_after_tab1",
             "w_final", "compensated", "n_added_total", "click_rows", "tabs")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS, "n_rec": N_REC,
       "scale_fixed": SCALE_FIXED, "poll_max": POLL_MAX, "poll_gap": POLL_GAP,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "944 矛盾剩下的可疑变量：连点期间身份在不在动（等不等它稳定）",
       "void_runs": [
           "944 v1：写下过「补偿没来」，**已撤回**（is_arm 判据太松）",
           "944 v3：scale=7 补 / scale=13 不补，**两轮不一致**",
           "945：scale 与 mode 都拆了、都排除不了",
           "946：`warm` **压根没被操控过**（自然值 76 ≥ 任何目标）"
           "⇒ **`warm_reached` 恒真 = 恒绿 = 没有门，已撤回**",
           "946：sham 证明「第一击 Tab 压下去」**不需要连点** ⇒ 那不是补偿",
           "946：格 0 两轮一个 75→1、一个 75→8 ⇒ **944 矛盾原样重现**",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        ws = cell["wait_stable"]
        print(f"  --- 格 {ci}：wait_stable={ws} ---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "wait_stable": ws, "n_audio_rail_button": n_audio,
             "click_bites": 0, "n_click": 0, "n_poll_total": 0,
             "n_settled": 0, "tabs": [], "settle_traj": []}
        rec["cells"].append(c)
        dump(out)
        if n_audio == 0:
            c["skipped"] = "登录态没命中，本轮不测"
            continue

        sp = ev(BLANK_JS)
        c["blank"] = sp
        if sp:
            guard_point(sp[0], sp[1])
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(BLANK_WAIT)
        pre = ev(CENSUS_JS, [NODE_SEL])

        # ⭐ settle **照抄 945**：按 Tab 到 `n_without_ti <= 1` 为止、上限 14 下
        # ⇒ **前置态与 945 同侧**，读数可与 945 对照
        n_press = 0
        c["settle_traj"].append(
            {"press": 0, "n_without_ti": pre["n_without_ti"]})
        for _ in range(SETTLE_MAX):
            if pre["n_without_ti"] <= 1:
                break
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            n_press += 1
            cur = ev(CENSUS_JS, [NODE_SEL])
            pre = cur                      # ⭐ 不许拿陈旧读数当基线
            c["settle_traj"].append(
                {"press": n_press, "n_without_ti": cur["n_without_ti"]})
        c["settle_presses"] = n_press
        c["ready_without_ti"] = pre["n_without_ti"]
        print(f"      settle：按 {n_press} 下，不带ti 轨迹="
              f"{[t['n_without_ti'] for t in c['settle_traj']]}"
              f" ⇒ 就绪 {pre['n_without_ti']}", flush=True)
        dump(out)

        landable = []
        for i in range(pre["n_nodes"]):
            if ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)]):
                landable.append(i)
            if len(landable) >= SCALE_FIXED + 2:
                break
        c["landable_found"] = len(landable)

        for k in range(SCALE_FIXED):
            if k >= len(landable):
                break
            pt = ev(POINT_JS, [NODE_SEL, landable[k], list(HIT_FORBIDDEN)])
            if not pt:
                continue
            before = pre
            guard_point(pt[0], pt[1])
            page.mouse.click(pt[0], pt[1])
            if ws:
                # ⭐ 受控侧：等**连续两次身份表相同**再普查
                post, n_poll, settled = settle_census()
                c["n_poll_total"] += n_poll
                c["n_settled"] += int(bool(settled))
                c["n_poll_max"] = max(c.get("n_poll_max", 0), n_poll)
            else:
                page.wait_for_timeout(SETTLE)
                post = ev(CENSUS_JS, [NODE_SEL])
                c["n_poll_max"] = c.get("n_poll_max", 0)
            d = delta(before, post)
            c["n_click"] += 1
            if d["bit"]:
                c["click_bites"] += 1
            row = {"k": k + 1, "i": landable[k], "bit": d["bit"],
                   "removed": d["removed"], "added": d["added"],
                   "identity_stable": d["identity_stable"]}
            if ws:
                row["n_poll"] = n_poll
                row["settled"] = bool(settled)
            c.setdefault("click_rows", []).append(row)
            pre = post                      # ⭐ 每一击都换成新普查
            dump(out)
        c.setdefault("n_poll_max", 0)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点完 {c['n_click']} 次（咬到 {c['click_bites']}）"
              f"，轮询总计 {c['n_poll_total']}、等到稳定 {c['n_settled']}"
              f" ⇒ 不带ti={c['w_after_clicks']}", flush=True)

        fa = ev(ARM_FOCUS_JS, [NODE_SEL])
        c["focus"] = fa

        for k in range(1, N_REC + 1):
            f0 = ev(FOCUS_JS, [NODE_SEL])
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            cur = ev(CENSUS_JS, [NODE_SEL])
            d = delta(pre, cur)
            f1 = ev(FOCUS_JS, [NODE_SEL])
            was_arm = bool(f0["focus_in_node"]) and f0["active_tag"] == "DIV"
            c["tabs"].append({"k": k, "was_arm": was_arm,
                              "active_before": f0["active_tag"],
                              "active_after": f1["active_tag"],
                              "bit": d["bit"], "n_added": len(d["added"]),
                              "n_removed": len(d["removed"]),
                              "w_before": pre["n_without_ti"],
                              "w_after": cur["n_without_ti"],
                              "identity_stable": d["identity_stable"]})
            print(f"      [Tab {k}] 按前焦点={f0['active_tag']}"
                  f"{'/在节点内' if f0['focus_in_node'] else ''}"
                  f" was_arm={was_arm} added={len(d['added'])}"
                  f" 不带ti {pre['n_without_ti']}→{cur['n_without_ti']}"
                  f" stable={d['identity_stable']}", flush=True)
            pre = cur
            dump(out)
            if k == 1:
                c["w_after_tab1"] = cur["n_without_ti"]
        c.setdefault("w_after_tab1", pre["n_without_ti"])
        c["w_final"] = pre["n_without_ti"]
        c["compensated"] = bool(c["click_bites"] > 0
                                and c["w_after_clicks"] > c["ready_without_ti"]
                                and c["w_after_tab1"] == 1)
        c["n_added_total"] = sum(t["n_added"] for t in c["tabs"])
        c["cell_ok"] = bool(c["n_click"] == c["click_bites"])
        print(f"      ⇒ 补回={c['compensated']}（连点后 {c['w_after_clicks']}"
              f" → 第1击后 {c['w_after_tab1']}、终值 {c['w_final']}）、"
              f"格可用={c['cell_ok']}", flush=True)
        dump(out)

# ⭐ `reps_identical` 真算
_ident = []
for ci in range(len(CELLS)):
    got = [stable_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident

# ⭐⭐ **反恒绿门**：这个操纵到底动了没有？两格必须**测得出差别**
_wa = [run["cells"][0] for run in out["runs"] if "skipped" not in run["cells"][0]]
_wb = [run["cells"][1] for run in out["runs"] if "skipped" not in run["cells"][1]]
_wa_t = [(x.get("n_poll_max", 0), x.get("n_settled", 0)) for x in _wa]
_wb_t = [(x.get("n_poll_max", 0), x.get("n_settled", 0)) for x in _wb]
out["manip_moved_something"] = bool(_wa_t and _wb_t and _wa_t != _wb_t)

out["design_gates"] = {
    "single_var": bool(len({x["wait_stable"] for x in CELLS}) == 2),
    "scale_fixed": bool(SCALE_FIXED == 8),
    "reps_identical": bool(all(_ident)),
    "manip_moved_something": out["manip_moved_something"],
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "removed",
                                     "added", "n_without_ti", "active_tag",
                                     "focus_in_node"))),
    "settle_side_matches_945": bool(
        all(run["cells"][ci].get("ready_without_ti") is not None
            for run in out["runs"] for ci in range(len(CELLS))
            if "skipped" not in run["cells"][ci])),
}
print("\n反恒绿门（操纵动了没有）：", out["manip_moved_something"], flush=True)
print("设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
