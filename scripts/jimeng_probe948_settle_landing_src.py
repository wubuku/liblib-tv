#!/usr/bin/env python3
r"""batch 948 源站探针（**纯诊断**）：⭐⭐⭐⭐ 把 947 那张**关系式**对照表变成**受控对照**。

## 947 留下的口子

947 排除了「等不等身份稳定」，于是 944 那个矛盾只剩一张**跨批对照表**：

⚠️ **表格第一格不写裸数字**：`| 944 |` 那种行会被 pre-commit 钩子的批次行匹配
（`^\+\|\s*(\d+)[a-z]?\s*\|`，见 `docs/user-manual/beeftv-canvas/scripts/buildrecord.py`）
当成**新增批次**，而本树的绿构建只走到 Batch 258 ⇒ 提交被挡下。
⇒ 这是**内容撞了格式**：改内容，**不动门**。

| 批次 | settle | 就绪 `不带 ti` | 矛盾？ |
| --- | --- | --- | --- |
| 批 945 / 批 947 | 1 下 | **0** | **无** |
| 批 944 | 10 下 | **1** | **有** |
| 批 946 | 0 下 | **76** | **有** |

⇒ **矛盾只在「就绪 ≠ 0」那侧** —— ⚠️ 但 947 自己写明了：
**「这仍然是关系式推断、不是受控对照」**（那三批的 `scale`/落点/咬到数**都不同**）
⇒ ⭐ **下一步该测什么已经唯一了**：让 settle **显式停在 0 和停在 1**，
**其它一切固定**。本批就干这件事。

## 本批的设计：**单变量** `n_settle`（**显式按固定下数**，不是「按到满足为止」）

⚠️ 946 栽过的坑**不许再栽**：它用「按到 `n_without_ti >= warm` 为止」，
而 boot 后的自然值就是 76 ⇒ 任何目标都 ≤ 76 ⇒ 循环**一次都没进** ⇒ 门恒真、已撤回。
⇒ 本批**不用条件循环**，改成**显式按 `n_settle` 下**，并**把每一按的落点记下来**。

- `n_settle ∈ {0, 1, 2}` ⇒ 预期落点 **76 / 0 / 1**（946 的 sham 走过 76→0→1）
- 固定 `scale = 8`、固定 `mode = body`、固定 `wait_stable = False`
  （947 已证明 `wait_stable` 对结果**没有影响**，取便宜的那一侧）
- 每格**独立 `boot()`**；**2 轮**

## ⭐⭐ 本批的两道门（都承 946/947 的教训）

1. `landed_differently` —— ⭐ **「三个格真的落在三个不同的值上吗」必须自己答**。
   如果 `n_settle=2` 也落在 `0`（即 76→0→0 而不是 76→0→1），
   **那就如实记下来**，并且**下一批不能再按「1 = 1」去设计**。
   ⇒ 这道门**不是**判 `warm_reached` 那种恒真门：它比的是**格与格之间**，
   操纵不动它就会红。
2. `settle_stable_ok` —— 记录**每一按的 `identity_stable`**。
   ⚠️ 947 只记了 `不带 ti` 轨迹、**没记每按的身份稳不稳**；
   而 946 的 sham 那一侧 `identity_stable` **全程 False** ⇒
   `76 → 0 → 1` 这条路径**本身可能就是瞬态而不是状态**。
   ⇒ ⭐ **一个数「看起来像状态」不够，得知道它稳不稳。**

## 读什么

- `settle_rows`：每一按的 `不带 ti` + `identity_stable` + 按前焦点
- `click_rows` / `tabs`（与 945/947 同口径）
- `w_after_clicks` / `w_after_tab1` / `w_final` / `compensated`
- `n_added_total`、第 1 击的 `added`

## 探针自带的纪律（承 943→947）

1. ⭐ **防漂移**：五段 JS **逐字 assert 与 947 相同**（940 的办法）
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`；⚠️ **不许拿陈旧读数当基线**
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131）
7. ⚠️ **身份不稳的那一段三元组一律不许当读数**（946）

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」。**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe948_settle_landing_src.py
"""

import json
import pathlib

OUT = "/tmp/b948-settle-landing.json"
REPS = 2
P947 = pathlib.Path(__file__).with_name(
    "jimeng_probe947_stablewait_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_REC = 3
SCALE_FIXED = 8
POLL_MAX = 6
POLL_GAP = 250
# ⭐ 唯一自变量：**显式**按固定下数（不是「按到满足为止」—— 946 栽过）
NSETTLE_CELLS = [0, 1, 2]
CELLS = [{"n_settle": n} for n in NSETTLE_CELLS]

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
    "ci", "n_settle", "n_audio_rail_button", "ready_without_ti",
    "settle_rows", "landable_found", "n_click", "click_bites",
    "w_after_clicks", "w_after_tab1", "w_final", "compensated",
    "n_added_total", "cell_ok", "reps_identical", "design_gates",
    "landed_differently", "settle_stable_ok",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("n_settle", "ready_without_ti", "compensated", "cell_ok",
              "reps_identical", "landed_differently", "settle_stable_ok"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "removed", "added", "n_without_ti",
             "active_tag", "focus_in_node"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"

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

_p947src = P947.read_text(encoding="utf-8") if P947.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS",
                       "ARM_FOCUS_JS"),
                      (BLANK_JS,) + _JS_ALL):
    assert _js in _p947src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 947 那份**不一致** —— 两份定义开始分家了")


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


def stable_key(cell):
    """两轮逐条比较用的键。⚠️ 排除 `settle_rows` 里的路径类读数。"""
    return {k: cell.get(k) for k in
            ("n_settle", "ready_without_ti", "landable_found", "n_click",
             "click_bites", "w_after_clicks", "w_after_tab1", "w_final",
             "compensated", "n_added_total", "click_rows", "tabs")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS, "n_rec": N_REC,
       "scale_fixed": SCALE_FIXED, "wait_stable_fixed": False,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "让 settle 显式停在 0 / 1 / 76 三个点上，看矛盾跟不跟着就绪值走",
       "void_runs": [
           "944 v1：「补偿没来」**已撤回**（is_arm 判据太松）",
           "944 v3：scale=7 补 / scale=13 不补，两轮不一致",
           "945：scale 与 mode 都拆了、都排除不了",
           "946：`warm` **压根没被操控过**（自然值 76 ≥ 任何目标）"
           "⇒ `warm_reached` 恒真 = 恒绿 = **没有门，已撤回**",
           "946：sham 证明「第一击 Tab 压下去」不需要连点 ⇒ 那不是补偿",
           "946：格 0 两轮一个 75→1、一个 75→8 ⇒ **944 矛盾原样重现**",
           "947：`wait_stable` 被排除（poll 0→5 而读数逐条不变）",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        ns = cell["n_settle"]
        print(f"  --- 格 {ci}：n_settle={ns} ---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "n_settle": ns, "n_audio_rail_button": n_audio,
             "click_bites": 0, "n_click": 0, "tabs": [], "settle_rows": []}
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
        c["settle_rows"].append(
            {"press": 0, "n_without_ti": pre["n_without_ti"],
             "identity_stable": None, "active_tag": None})

        # ⭐⭐ **显式**按 `ns` 下 —— 不用「按到满足为止」（946 栽过：恒真门）
        for k in range(1, ns + 1):
            before = pre
            f0 = ev(FOCUS_JS, [NODE_SEL])
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            cur = ev(CENSUS_JS, [NODE_SEL])
            d = delta(before, cur)
            # ⭐ 记下**每一按**的身份稳不稳（947 缺这条）
            c["settle_rows"].append(
                {"press": k, "n_without_ti": cur["n_without_ti"],
                 "identity_stable": d["identity_stable"],
                 "active_tag": f0["active_tag"]})
            pre = cur                      # ⭐ 不许拿陈旧读数当基线
            dump(out)
        c["ready_without_ti"] = pre["n_without_ti"]
        print(f"      settle：显式按 {ns} 下，逐按落点="
              f"{[(r['press'], r['n_without_ti'], r['identity_stable']) for r in c['settle_rows']]}"
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
            page.wait_for_timeout(SETTLE)      # wait_stable=False（947 已证无影响）
            post = ev(CENSUS_JS, [NODE_SEL])
            d = delta(before, post)
            c["n_click"] += 1
            if d["bit"]:
                c["click_bites"] += 1
            c.setdefault("click_rows", []).append(
                {"k": k + 1, "i": landable[k], "bit": d["bit"],
                 "removed": d["removed"], "added": d["added"],
                 "identity_stable": d["identity_stable"]})
            pre = post                      # ⭐ 每一击都换成新普查
            dump(out)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点完 {c['n_click']} 次（咬到 {c['click_bites']}）"
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

# ⭐⭐ 门 1：三个格**真的落在不同的值上**吗？比的是**格与格之间** ⇒ 操纵不动就红
_land = []
for ci in range(len(CELLS)):
    for run in out["runs"]:
        if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]:
            _land.append((run["cells"][ci].get("n_settle"),
                          run["cells"][ci].get("ready_without_ti")))
out["landing_pairs"] = sorted(set(_land))
out["landed_differently"] = bool(
    len({v for _, v in _land}) >= 2 and len(_land) == REPS * len(CELLS))

# ⭐⭐ 门 2：settle 那几按的身份稳不稳（`None` = 没按，不算不稳）
_st = []
for run in out["runs"]:
    for cc in run["cells"]:
        if "skipped" in cc:
            continue
        for r in cc.get("settle_rows", []):
            if r.get("identity_stable") is not None:
                _st.append(bool(r["identity_stable"]))
out["settle_stable_ok"] = bool(_st and all(_st))

out["design_gates"] = {
    # ⭐⭐ **按压次数必须真的等于 `ns`** —— 行为检查，不是源码字符串检查。
    #    （第一版这里写的是 `... or True`，那正是 946/947 一路在打的**恒真门**。）
    "pressed_exactly_ns": bool(all(
        len([r for r in cc.get("settle_rows", []) if r.get("press", 0) >= 1])
        == cc.get("n_settle")
        for run in out["runs"] for cc in run["cells"]
        if "skipped" not in cc)),
    "n_settle_varies": bool(len({x["n_settle"] for x in CELLS}) == 3),
    "reps_identical": bool(all(_ident)),
    "landed_differently": out["landed_differently"],
    "settle_stable_ok": out["settle_stable_ok"],
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "removed",
                                     "added", "n_without_ti", "active_tag",
                                     "focus_in_node"))),
}
print("\n落点对照（n_settle → 就绪不带ti）：", out["landing_pairs"], flush=True)
print("反恒绿门 landed_differently：", out["landed_differently"], flush=True)
print("settle 身份全稳：", out["settle_stable_ok"], flush=True)
print("设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
