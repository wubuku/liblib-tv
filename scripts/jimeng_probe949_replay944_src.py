#!/usr/bin/env python3
r"""batch 949 源站探针（**纯诊断**）：⭐⭐⭐ **把 944 自己那组数字原样重跑一遍**。

## 948 结案之后，唯一还挂着的因果问题

948 已经证明「944 那个矛盾是一个误读」—— 矛盾只在**就绪 = 76** 那一侧（**一按 `Tab`
都还没按过**）出现，而 946 的 sham 证明那一侧第 1 击 `Tab` 在干的是**冷启动铺窗口**。

⇒ 但 948 **没有解释 944 自己那次读数**（就绪 1、13 连点、连按 6 下 `added` 恒 0），
而且明明白白写了「**成因仍未查明**」。
⇒ 本批就干这一件事：**同一段代码、同一组数字**（就绪 = 显式按 2 下 ⇒ 1、13 连点、
连按 6 下 `Tab`），看那次「`added` 恒 0」**能不能复现**。

## ⭐⭐ 本批的设计关键：**同一次跑里带对照格**

⚠️ 947 栽过一次的坑：它把**不同批次**的读数摆成一张表当对照，
结果被自己判成「**关系式推断、不是受控对照**」。
⇒ 本批**不许**再犯：对照格**就在同一次跑里**，别的参数与 944 那格**只差 `scale` 与
按压下数**，其余逐字相同 ⇒ 任何差别都**只能**归因到那两个数字上。

| 格 | `n_settle` | `scale` | 按几下 `Tab` | 身份 |
| --- | --- | --- | --- | --- |
| 格 0 | **2**（就绪 1） | **13** | **6** | ⭐ **944 的那组数字** |
| 格 1 | **2**（就绪 1） | 8 | 3 | ⭐ **同一次跑里的对照**（= 948 格 2） |

## 判决点

- **格 0 复现「`added` 恒 0」？** ⇒ 那个矛盾是真的，且成因在 13/6 这两个数字上
- **格 0 补偿照常（与格 1 同形）？** ⇒ ⭐ **944 那次读数不可复现**
  ⇒ 它是一次**读数事故**（多半是它自己那格 `cell_ok` 不满足、
  身份不稳那一段的读数按 946 **一律不作数**），**不是**机制
- **两格形状一样？** ⇒ `scale=13` 与 `6` 下 `Tab` **都不是**变量（与 945 的排除一致）

## 探针自带的纪律（承 943→948）

1. ⭐ **防漂移**：五段 JS **逐字 assert 与 948 相同**（940 的办法）
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`；⚠️ **不许拿陈旧读数当基线**
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131）
7. ⚠️ **身份不稳的那一段三元组一律不许当读数**（946）
8. ⚠️ **表格第一格不写裸数字** —— `| 13 |` 会被 pre-commit 钩子的批次行匹配
   （`^\+\|\s*(\d+)[a-z]?\s*\|`）当成**新增批次**而挡下提交。948 栽过一次。

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」。**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe949_replay944_src.py
"""

import json
import pathlib

OUT = "/tmp/b949-replay944.json"
REPS = 2
P948 = pathlib.Path(__file__).with_name(
    "jimeng_probe948_settle_landing_src.py")

SETTLE = 350
BLANK_WAIT = 900
SCALE_FIXED = 8
NSETTLE_FIXED = 2           # ⭐ 显式按 2 下 ⇒ 就绪 `不带 ti` = 1（948 已 2/2 验过）
# ⭐ 格 0 = 944 的那组数字；格 1 = 同一次跑里的对照（= 948 格 2）
CELLS = [{"scale": 13, "n_rec": 6}, {"scale": SCALE_FIXED, "n_rec": 3}]

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
    "ci", "scale", "n_rec", "n_settle", "n_audio_rail_button",
    "ready_without_ti", "settle_rows", "landable_found", "n_click",
    "click_bites", "w_after_clicks", "w_after_tab1", "w_final",
    "compensated", "n_added_total", "tabs_with_added", "added_all_zero",
    "first_click_bites", "cell_ok", "reps_identical", "design_gates",
    "reproduced_944", "control_present",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("scale", "n_rec", "ready_without_ti", "compensated", "cell_ok",
              "reps_identical", "reproduced_944", "added_all_zero"):
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

_p948src = P948.read_text(encoding="utf-8") if P948.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS",
                       "ARM_FOCUS_JS"),
                      (BLANK_JS,) + _JS_ALL):
    assert _js in _p948src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 948 那份**不一致** —— 两份定义开始分家了")


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
    """两轮逐条比较用的键。"""
    return {k: cell.get(k) for k in
            ("scale", "n_rec", "n_settle", "ready_without_ti", "landable_found",
             "n_click", "click_bites", "w_after_clicks", "w_after_tab1",
             "w_final", "compensated", "n_added_total", "tabs_with_added",
             "added_all_zero", "first_click_bites", "click_rows", "tabs")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS,
       "n_settle_fixed": NSETTLE_FIXED, "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "944 自己那次（就绪 1、13 连点、连按 6 下）能不能原样复现",
       "void_runs": [
           "944 v1：「补偿没来」**已撤回**（is_arm 判据太松）",
           "944 v3：scale=7 补 / scale=13 不补，两轮不一致",
           "945：scale 与 mode 都拆了、都排除不了",
           "946：`warm` **压根没被操控过** ⇒ `warm_reached` 恒真、已撤回",
           "946：sham 证明「第一击 Tab 压下去」不需要连点 ⇒ 那不是补偿",
           "947：`wait_stable` 被排除（poll 0→5 而读数逐条不变）",
           "948：受控落点表 76/0/1 ⇒ **矛盾结案（是个误读）**；"
           "但「944 自己那次为何不补」**成因仍未查明**",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        scale, n_rec = cell["scale"], cell["n_rec"]
        tag = "★ 944 的那组数字" if ci == 0 else "同一次跑里的对照"
        print(f"  --- 格 {ci}（{tag}）：n_settle={NSETTLE_FIXED} "
              f"scale={scale} n_rec={n_rec} ---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "scale": scale, "n_rec": n_rec,
             "n_settle": NSETTLE_FIXED, "n_audio_rail_button": n_audio,
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
             "identity_stable": None})

        for k in range(1, NSETTLE_FIXED + 1):
            before = pre
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            cur = ev(CENSUS_JS, [NODE_SEL])
            d = delta(before, cur)
            c["settle_rows"].append(
                {"press": k, "n_without_ti": cur["n_without_ti"],
                 "identity_stable": d["identity_stable"]})
            pre = cur
            dump(out)
        c["ready_without_ti"] = pre["n_without_ti"]
        print(f"      前置态：显式按 {NSETTLE_FIXED} 下，逐按落点="
              f"{[(r['press'], r['n_without_ti'], r['identity_stable']) for r in c['settle_rows']]}"
              f" ⇒ 就绪 {pre['n_without_ti']}", flush=True)
        dump(out)

        landable = []
        for i in range(pre["n_nodes"]):
            if ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)]):
                landable.append(i)
            if len(landable) >= scale + 2:
                break
        c["landable_found"] = len(landable)

        for k in range(scale):
            if k >= len(landable):
                break
            pt = ev(POINT_JS, [NODE_SEL, landable[k], list(HIT_FORBIDDEN)])
            if not pt:
                continue
            before = pre
            guard_point(pt[0], pt[1])
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(SETTLE)
            post = ev(CENSUS_JS, [NODE_SEL])
            d = delta(before, post)
            c["n_click"] += 1
            if d["bit"]:
                c["click_bites"] += 1
            row = {"k": k + 1, "i": landable[k], "bit": d["bit"],
                   "removed": d["removed"], "added": d["added"],
                   "identity_stable": d["identity_stable"]}
            if k == 0:
                c["first_click_bites"] = int(bool(d["bit"]))
            c.setdefault("click_rows", []).append(row)
            pre = post
            dump(out)
        c.setdefault("first_click_bites", 0)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点 {scale} 次：落点成功 {c['n_click']}、咬到 {c['click_bites']}"
              f"（landable={len(landable)}）⇒ 不带ti={c['w_after_clicks']}",
              flush=True)

        fa = ev(ARM_FOCUS_JS, [NODE_SEL])
        c["focus"] = fa

        for k in range(1, n_rec + 1):
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
            print(f"      [Tab {k}/{n_rec}] 按前焦点={f0['active_tag']}"
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
        c["tabs_with_added"] = sum(1 for t in c["tabs"] if t["n_added"] > 0)
        # ⭐ 944 的判别式就是这一条：**连按 6 下 `added` 恒 0**
        c["added_all_zero"] = (c["n_added_total"] == 0)
        c["cell_ok"] = bool(c["n_click"] == c["click_bites"])
        print(f"      ⇒ 补回={c['compensated']}、有 added 的按压数="
              f"{c['tabs_with_added']}/{n_rec}、added 全 0={c['added_all_zero']}"
              f"、格可用={c['cell_ok']}", flush=True)
        dump(out)

_ident = []
for ci in range(len(CELLS)):
    got = [stable_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident

_c0 = [run["cells"][0] for run in out["runs"] if "skipped" not in run["cells"][0]]
_c1 = [run["cells"][1] for run in out["runs"] if "skipped" not in run["cells"][1]]
# ⭐ 「944 那次有没有被复现」= 格 0 两轮**都**出现 `added` 恒 0
out["reproduced_944"] = bool(_c0 and all(x.get("added_all_zero") for x in _c0))
# ⭐ 对照格**必须真的在**（不许拿一个不存在的对照说「两格一样」）
out["control_present"] = bool(_c1 and all(x.get("n_click", 0) > 0 for x in _c1))

out["design_gates"] = {
    # ⭐⭐ 按压次数必须真的等于 `n_settle`（行为检查，不是源码字符串检查）
    "pressed_exactly_ns": bool(all(
        len([r for r in cc.get("settle_rows", []) if r.get("press", 0) >= 1])
        == NSETTLE_FIXED
        for run in out["runs"] for cc in run["cells"]
        if "skipped" not in cc)),
    "grid_is_944_numbers": bool(CELLS[0]["scale"] == 13 and CELLS[0]["n_rec"] == 6),
    "same_settle_both_cells": bool(
        all(cc.get("n_settle") == NSETTLE_FIXED
            for run in out["runs"] for cc in run["cells"] if "skipped" not in cc)),
    "reps_identical": bool(all(_ident)),
    "reproduced_944": out["reproduced_944"],
    "control_present": out["control_present"],
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "removed",
                                     "added", "n_without_ti", "active_tag",
                                     "focus_in_node"))),
}
print("\n944 那次有没有被复现（格 0 两轮都 added 恒 0）：",
      out["reproduced_944"], flush=True)
print("对照格在不在：", out["control_present"], flush=True)
print("设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
