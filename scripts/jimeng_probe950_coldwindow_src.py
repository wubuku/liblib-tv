#!/usr/bin/env python3
r"""batch 950 源站探针（**纯诊断 / 零点击**）：⭐⭐⭐ 把「冷启动铺窗口」从**现象**测成**规则**。

## 为什么要测这条

948 证明「944 那个矛盾是一个误读」—— 矛盾只在**就绪 = 76** 那一侧（**一按 `Tab`
都还没按过**）出现；946 的 **sham**（零点击）又证明那一侧第 1 击 `Tab` 就是 `76 → 0`。
⇒ 「冷启动铺窗口」这条规则是**判别两个 regime 的那把尺子**，而复刻侧要照抄的
**正是这条规则本身**。

⚠️ 但到今天为止，关于它我们只有**三个孤立读数**：

| 来源 | 按了几下 | `不带 ti` |
| --- | --- | --- |
| 刚 `boot()` 完（**一按都没有**） | 0 | **76** |
| 946 sham | 1 / 2 / 3 | **0 / 1 / 1** |
| 948 settle | 1 / 2 | **0 / 1** |

⇒ **只到第 3 下**。第 4 下之后会怎样、`不带 ti` 会不会一直是 1、
**那个「当前」节点是不是每按一次就往前挪一格** —— 全都没测过。

## 本批的设计：**零点击**，一条曲线压到底

- **零点击**（一个 `mouse.click` 都不发；只点一次画布空白**去焦点**，那是 943 起的
  标准前置、不是节点点击）
- 从刚 `boot()` 完开始，**连按 `N_PRESS = 14` 下 `Tab`**，**每按都记全量**：
  `不带 ti` / **哪些下标没有 `tabindex`** / 按前焦点 / `focus_in_node` / 身份稳不稳
- 每格**独立 `boot()``；**2 轮** ⇒ 曲线必须 **2/2 逐条相同**
- 固定：`N_PRESS = 14`（覆盖 943/944 记过的「Tab 周期 101/104」之外的一段，
  至少把 `不带 ti` 的稳态看清）

## ⭐ 本批自己设计的门

1. `press1_is_the_big_drop` —— **第 1 按与第 2 按之后必须是两种不同的量级**。
   ⚠️ 这道门**不是恒真门**：它比的是**同一条曲线的前后两段**，
   而源站完全可能给出「每按都只动 1 个」⇒ 那就**红**，红了就说明
   「铺窗口是一次性事件」这个说法**错了**。
2. `steady_at_one` —— 第 2 按之后 `不带 ti` **恒为 1**（§131 那条不变式）。
   ⚠️ 同样是可红的：红了就说明不变式有别的成立条件。
3. `pointer_walks` —— **「没有 `tabindex` 的那个下标每按一次就变」**。
   ⚠️ 可红：红了就说明那个下标不动（指针不游走），那 940 的「单指针」结论要重看。

## 探针自带的纪律（承 943→949）

1. ⭐ **防漂移**：五段 JS **逐字 assert 与 949 相同**（940 的办法）
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`；⚠️ **不许拿陈旧读数当基线**
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ **身份不稳的那一段三元组一律不许当读数**（946）
7. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配
   （`^\+\|\s*(\d+)[a-z]?\s*\|`）当成**新增批次**而挡下提交。948 栽过一次。

## 计费边界

**本批零节点点击。** 只发一次画布空白点击去焦点（943 起的标准前置），
⛔ 守卫拦在 `mouse.click` **之前**，契约是「**我正要点的这个元素**是什么」。
**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe950_coldwindow_src.py
"""

import json
import pathlib

OUT = "/tmp/b950-coldwindow.json"
REPS = 2
P949 = pathlib.Path(__file__).with_name(
    "jimeng_probe949_replay944_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_PRESS = 14               # ⭐ 压到底：把稳态看清
NO_TI_CAP = 40             # 「没有 tabindex 的下标」最多记这么多条

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "充值")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "no_ti",
    "no_ti_capped", "active_tag", "active_tid", "focus_in_node", "blank",
    "point", "i", "k", "hit_tag", "focus_ok",
})
DERIVED_KEYS = frozenset({
    "ci", "n_press", "n_audio_rail_button", "cold_without_ti",
    "press_rows", "drop_p1", "max_drop_after", "steady_at_one",
    "pointer_moves", "pointer_walks", "press1_is_the_big_drop",
    "reps_identical", "design_gates", "curve_reproducible",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("n_press", "cold_without_ti", "steady_at_one", "pointer_walks",
              "press1_is_the_big_drop", "reps_identical", "curve_reproducible"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti"):
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

# ⭐⭐ 本批的新件：**「哪些下标没有 tabindex」** —— 这是「指针在哪」的正面读数。
#    截断到 `cap` 条，**并如实记下 `capped`**（不许让人以为那就是全部）。
NO_TI_JS = """([nodeSel, cap]) => {
  const nodes = Array.from(document.querySelectorAll(nodeSel));
  const out = [];
  for (let i = 0; i < nodes.length; i++) {
    if (!nodes[i].hasAttribute('tabindex')) out.push(i);
  }
  return {no_ti: out.slice(0, cap), no_ti_capped: out.length > cap,
          n_without_ti: out.length};
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

# ⭐ 947/948/949 那五段必须与 949 **逐字相同**；`NO_TI_JS` 是本批**新件**、不许混进去
_p949src = P949.read_text(encoding="utf-8") if P949.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS",
                       "ARM_FOCUS_JS"),
                      (BLANK_JS,) + _JS_ALL):
    assert _js in _p949src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 949 那份**不一致** —— 两份定义开始分家了")
assert "NO_TI_JS" not in _p949src, "950 的新件别混进「逐字相同」那组"


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


def curve_key(cell):
    """两轮逐条比较用的键。"""
    return {k: cell.get(k) for k in
            ("n_press", "cold_without_ti", "press_rows", "drop_p1",
             "max_drop_after", "steady_at_one", "pointer_moves",
             "pointer_walks", "press1_is_the_big_drop")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "n_press": N_PRESS,
       "no_ti_cap": NO_TI_CAP, "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "「冷启动铺窗口」这条规则本身长什么样（零点击、14 下 Tab 的全曲线）",
       "void_runs": [
           "944 v1：「补偿没来」**已撤回**（is_arm 判据太松）",
           "946：`warm` 压根没被操控 ⇒ `warm_reached` 恒真、已撤回",
           "946：sham（**零点击**）76→0→1→1 ⇒ 「第一击 Tab 压下去」不是补偿",
           "947：`wait_stable` 被排除（poll 0→5 而读数逐条不变）",
           "948：受控落点表 76/0/1 ⇒ **944 的矛盾结案（是个误读）**；"
           "**就绪 = 1 是瞬态**",
           "949：用 944 自己那组数字重跑 ⇒ **那次读数不可复现**",
           "⚠️ 上面关于「铺窗口」只有**三个孤立读数**（下 0/1/2/3 下），"
           "**第 4 下之后从没测过** ⇒ 本批补上",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    n_audio = boot_fn()
    c = {"ci": 0, "n_press": N_PRESS, "n_audio_rail_button": n_audio,
         "press_rows": []}
    rec["cells"].append(c)
    dump(out)
    if n_audio == 0:
        c["skipped"] = "登录态没命中，本轮不测"
        continue

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])          # ⭐ 只点**画布空白**去焦点，不是节点点击
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    pre = ev(CENSUS_JS, [NODE_SEL])
    nt = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
    c["cold_without_ti"] = nt["n_without_ti"]
    c["press_rows"].append(
        {"press": 0, "n_without_ti": nt["n_without_ti"],
         "no_ti": nt["no_ti"], "no_ti_capped": nt["no_ti_capped"],
         "active_tag": None, "focus_in_node": None,
         "identity_stable": None})
    print(f"      冷启动：nodes={pre['n_nodes']}、不带ti={nt['n_without_ti']}"
          f"（截断={nt['no_ti_capped']}）", flush=True)

    for k in range(1, N_PRESS + 1):
        before = pre
        f0 = ev(FOCUS_JS, [NODE_SEL])
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        d = delta(before, cur)
        nt = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
        f1 = ev(FOCUS_JS, [NODE_SEL])
        was_arm = bool(f0["focus_in_node"]) and f0["active_tag"] == "DIV"
        c["press_rows"].append(
            {"press": k, "n_without_ti": nt["n_without_ti"],
             "no_ti": nt["no_ti"], "no_ti_capped": nt["no_ti_capped"],
             "active_before": f0["active_tag"], "active_after": f1["active_tag"],
             "focus_in_node": f1["focus_in_node"], "was_arm": was_arm,
             "bit": d["bit"], "n_added": len(d["added"]),
             "n_removed": len(d["removed"]),
             "identity_stable": d["identity_stable"]})
        print(f"      [Tab {k:>2}/{N_PRESS}] 前焦点={f0['active_tag']}"
              f"{'/在节点内' if f0['focus_in_node'] else ''}"
              f" 后焦点={f1['active_tag']} was_arm={was_arm}"
              f" 不带ti={nt['n_without_ti']} 无ti下标={nt['no_ti'][:6]}"
              f" added={len(d['added'])} stable={d['identity_stable']}",
              flush=True)
        pre = cur
        dump(out)

    rows = c["press_rows"]
    vals = [r["n_without_ti"] for r in rows]
    c["drop_p1"] = abs(vals[0] - vals[1])
    c["max_drop_after"] = max(abs(vals[i] - vals[i - 1])
                              for i in range(2, len(vals)))
    # 「稳态恒 1」= 第 2 按之后**每一按**都读到 1
    c["steady_at_one"] = all(v == 1 for v in vals[2:])
    # 「指针游走」= 第 2 按之后那个「无 ti 下标」每按都变过
    seq = [tuple(r["no_ti"]) for r in rows[2:]]
    c["pointer_moves"] = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
    c["pointer_walks"] = bool(len(seq) > 1 and len(set(seq)) == len(seq))
    # ⭐ 门 1：第 1 按与第 2 按之后**必须是两种量级**（**可红**！）
    c["press1_is_the_big_drop"] = bool(c["drop_p1"] > max(c["max_drop_after"], 1))
    print(f"      ⇒ 曲线={vals}")
    print(f"      ⇒ 第1按落差={c['drop_p1']}、其后最大落差={c['max_drop_after']}"
          f"、稳态恒1={c['steady_at_one']}、指针游走={c['pointer_walks']}"
          f"（变了 {c['pointer_moves']} 次）、第1按是大跳="
          f"{c['press1_is_the_big_drop']}", flush=True)
    dump(out)

_ident = []
for ci in range(1):
    got = [curve_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["curve_reproducible"] = bool(all(_ident))

out["design_gates"] = {
    "zero_node_clicks": bool(all(
        not run["cells"][0].get("click_rows")
        and run["cells"][0].get("n_click", 0) == 0
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "pressed_exactly_n": bool(all(
        len([r for r in run["cells"][0].get("press_rows", [])
             if r.get("press", 0) >= 1]) == N_PRESS
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "curve_reproducible": out["curve_reproducible"],
    "press1_is_the_big_drop": bool(all(
        run["cells"][0].get("press1_is_the_big_drop")
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "steady_at_one": bool(all(
        run["cells"][0].get("steady_at_one")
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "pointer_walks": bool(all(
        run["cells"][0].get("pointer_walks")
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                     "active_tag", "focus_in_node", "no_ti"))),
}
print("\n曲线 2/2 可复现：", out["curve_reproducible"], flush=True)
print("设计门：", out["design_gates"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
