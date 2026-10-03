#!/usr/bin/env python3
r"""batch 946 源站探针（**纯诊断**）：⭐⭐⭐ 拆**第三个**自变量「前置态」。

## 945 留下的那个口子

945 把 944 的矛盾拆成了两个自变量并都测了：规模（`scale`）、那一击是不是臂事件（`mode`）。
结论是两条都排除不了 944 那次读数，于是**显式留下**：

- 本批每格 settle 只按 **1** 下、`就绪不带 ti = 0`
- 而 944 settle 了 **10** 下、`就绪不带 ti = 1`

⇒ **剩下唯一没被对照过的变量是「前置态」** —— 连点开始之前那个 `tabindex` 窗口
处在一个什么状态。945 自己写下：**「你以为只有两个，其实有三个」**。

## ⭐ 为什么这个变量有可能是主因

按 §131/943，`不带 ti`（`n_without_ti`）的**不变式是恒 1**：有且只有一个节点是「当前」节点
（没有 `tabindex`）。于是：

- `就绪不带 ti = 0` ⇒ **还没有 current 节点**（初始化刚发生，窗口还没被走）
- `就绪不带 ti = 1` ⇒ **已经有 current 节点**（指针已经走过它了）

⇒ 945 的整批读数（连点 12 次、8 次咬、1 击补回 8 个）**全部发生在「窗口里还没有 current 节点」**
这一侧；944 那次不补**发生在已经有 current 节点**那一侧。
⇒ 这两条读数**可能压根不是同一个实验**，而它们被当成了同一个。

## 本批的设计：**单变量**格子表（承 945 的教训，只动一样）

- **唯一自变量 `warm`**：就绪时要把 `不带 ti` 顶到几（`{0, 1, 2, 6}`）
  —— 靠**连按 Tab 直到 `n_without_ti >= warm`**（最多 14 下），并**把整条轨迹记下来**
- **固定 `scale = 8`** 次本体点击（945 证明规模无关，这里钉住不动）
- **固定 `mode = body`**（945 证明 `asis` 与 `body` 逐字相同）
- 每格：**独立 `boot()`**（940：状态会被带跑；AI 侧栏 Esc 关不掉）
- **2 轮**，格内读数**逐条相同**才算数

### ⭐ 第五格是 **sham**（专为证伪本批的仪器而设计）

`{"warm": 6, "scale": 0}`：6 下预热、**零点击**、只按 Tab。
⇒ 如果连点都没发生过而第 1 击 Tab 仍然有大幅 `added`，
那么前面几格的「补偿」就可能是**开机瞬态**，不是补偿 ⇒ 仪器恒绿。
⇒ **一个恒绿的仪器比没有仪器更坏**（942 的教训），所以这一格不许省。

## 判决点（**关系式**，不钉绝对值）

- **`warm` 是主因？** ⇒ `warm=0` 一侧补回、`warm>=1` 一侧不补（或反过来）
- **`warm` 不是主因？** ⇒ 两侧都补回 ⇒ 944 那次读数另有原因，**如实说「三个都不是」**
- **sham 有大幅 `added`？** ⇒ 仪器在测瞬态 ⇒ **本批全部作废**

## 探针自带的纪律（承 943/944/945）

1. ⭐ **防漂移**：普查 / 落点 / 焦点 / 空白点 / 程序化聚焦五段 JS
   **逐字 assert 与 945 相同**（940 的办法；936 栽过「同一判据写两套定义」）
2. ⭐ **尺子自证**：预热循环退出前 `pre = cur`；每一段退出前 `pre = cur`
3. ⭐ **`reps_identical` 这次真算** —— 945 只把它**声明**进 `DERIVED_KEYS`
   却**从没赋值**（一个悬空键，等于没有这道门）⇒ 本批补上
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⚠️ **不许拿陈旧普查当基线**（每段退出前 `pre = cur`）
6. ⭐ **非字符串不许切片**（§131：切片会把规律读反）

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」，不是「页面上有没有」。
**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe946_prestate_src.py
"""

import json
import pathlib

OUT = "/tmp/b946-prestate.json"
REPS = 2
P945 = pathlib.Path(__file__).with_name(
    "jimeng_probe945_comp_scale_split_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_REC = 3                 # 预热完成后按几下 Tab（第 1 击是关键）
WARM_MAX = 14             # 预热循环的上限
SCALE_FIXED = 8           # ⭐ 固定规模（945：规模不是主因）
# ⭐ 唯一自变量 `warm`；第五格是 **sham**（零点击，专为证伪本批仪器）
CELLS = [{"warm": 0, "scale": SCALE_FIXED},
         {"warm": 1, "scale": SCALE_FIXED},
         {"warm": 2, "scale": SCALE_FIXED},
         {"warm": 6, "scale": SCALE_FIXED},
         {"warm": 6, "scale": 0}]          # ⭐ sham

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    # delta()
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    # census
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti",
    # focus / point / blank
    "active_tag", "active_tid", "focus_in_node", "blank", "point", "i",
    "k", "hit_tag", "focus_ok",
})
DERIVED_KEYS = frozenset({
    "ci", "warm", "scale", "is_sham", "n_audio_rail_button",
    "warm_presses", "ready_without_ti", "warm_traj", "warm_reached",
    "landable_found", "n_click", "click_bites", "first_click_bites",
    "first_click_stable",
    "w_after_clicks", "w_after_tab1", "w_final", "compensated",
    "n_added_total", "cell_ok", "reps_identical", "design_gates",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("warm", "compensated", "cell_ok", "reps_identical", "is_sham"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
# ⭐ 原始键不许漏登记：凡是从 delta/census 直接读出来的名字都得登记
for _raw in ("bit", "identity_stable", "removed", "added", "n_without_ti",
             "active_tag", "focus_in_node"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"

# ── 空白点 / 普查 / 落点 / 焦点 / 程序化聚焦：与 945 **逐字相同**（下面统一 assert）
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

_p945src = P945.read_text(encoding="utf-8") if P945.exists() else ""
for _name in ("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"):
    assert eval(_name) in _p945src, (      # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 945 那份**不一致** —— 两份定义开始分家了")

SLICE_STR = "|| '').slice(0, "
_JS_ALL = (CENSUS_JS, POINT_JS, FOCUS_JS, ARM_FOCUS_JS)
# ⭐⭐ **守卫常量自己必须能匹配上东西**：本文件第一版把这里写成了
# `"|| '').slice(0 "`（**漏了一个逗号**）⇒ `count(SLICE_STR)` 恒为 0
# ⇒ 上面那道「非字符串切片」的门**永远不会红** = 恒绿 = 没有门。
# ⇒ **一个恒真的判据比没有判据更坏**（942 的教训）⇒ 这里给门加一道自证：
assert any(SLICE_STR in _js for _js in _JS_ALL), (
    "SLICE_STR 自己就匹配不上任何一段 JS —— 这道门恒绿，等于没有门")
for _name, _js in zip(("CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"),
                      _JS_ALL):
    assert _js.count("slice(") == _js.count(SLICE_STR), (
        f"{_name} 里有**非字符串**切片（§131：切片会把规律读反）")


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
    """逐**身份**对齐的两张表之差；身份对不上**如实记下**（943 的教训）。"""
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
    """⭐ 两轮逐条比较用的键：只取**读数**，不含与轮次无关会漂的元信息。
    ⚠️ `warm_traj` 排除在外：它是**长度可变**的轨迹，长度不同不代表读数不同
    （那是「按到几才够」的差别，由 `warm_presses` 单独承载）。"""
    return {k: cell.get(k) for k in
            ("warm", "scale", "is_sham", "ready_without_ti", "warm_presses",
             "warm_reached", "landable_found", "n_click", "click_bites",
             "first_click_bites", "w_after_clicks", "w_after_tab1",
             "w_final", "compensated", "n_added_total", "click_rows", "tabs")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS, "n_rec": N_REC,
       "scale_fixed": SCALE_FIXED, "warm_max": WARM_MAX,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "第三个自变量「前置态」（就绪时不带ti 停在哪）是不是主因",
       "void_runs": [
           "944 v1：写下过「补偿没来」，**已撤回**"
           "（is_arm 判据太松，焦点落在节点内部的按钮上是死按压）",
           "944 v3：scale=7 补 / scale=13 不补，**两轮不一致** ⇒ 945 拆自变量",
           "945：把 scale 与 mode 都拆了、都排除不了 ⇒ 本批拆**第三个**「前置态」",
           "945 只把 reps_identical **声明**进 DERIVED_KEYS 却**从没赋值**"
           " ⇒ 那道门等于没有 ⇒ 本批真算",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        warm, scale = cell["warm"], cell["scale"]
        sham = (scale == 0)
        print(f"  --- 格 {ci}：warm={warm} scale={scale}"
              f"{'（sham）' if sham else ''} ---", flush=True)
        # ⭐ 每格**独立 boot**（940：状态会被带跑；AI 侧栏 Esc 关不掉）
        n_audio = boot_fn()
        c = {"ci": ci, "warm": warm, "scale": scale, "is_sham": sham,
             "n_audio_rail_button": n_audio, "click_bites": 0, "n_click": 0,
             "tabs": [], "warm_traj": []}
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

        # ⭐⭐ **唯一自变量**：把「不带 ti」顶到 `warm`，并把**整条轨迹**记下来
        n_press = 0
        c["warm_traj"].append({"press": 0, "n_without_ti": pre["n_without_ti"]})
        for _ in range(WARM_MAX):
            if pre["n_without_ti"] >= warm:
                break
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            n_press += 1
            cur = ev(CENSUS_JS, [NODE_SEL])
            pre = cur                      # ⭐ 不许拿陈旧读数当基线
            c["warm_traj"].append(
                {"press": n_press, "n_without_ti": cur["n_without_ti"]})
        c["warm_presses"] = n_press
        c["ready_without_ti"] = pre["n_without_ti"]
        c["warm_reached"] = bool(pre["n_without_ti"] >= warm)
        print(f"      前置态：按 {n_press} 下到 不带ti={pre['n_without_ti']}"
              f"（目标 {warm}、达到={c['warm_reached']}）", flush=True)
        dump(out)

        # 扫全表取**本体**可点的下标（943 的教训：固定挑会踩空）
        landable = []
        for i in range(pre["n_nodes"]):
            if ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)]):
                landable.append(i)
            if len(landable) >= scale + 2:
                break
        c["landable_found"] = len(landable)

        # 点 `scale` 次**不同**的节点
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
            c.setdefault("click_rows", []).append(
                {"k": k + 1, "i": landable[k], "bit": d["bit"],
                 "removed": d["removed"], "added": d["added"],
                 "identity_stable": d["identity_stable"]})
            if k == 0:
                # ⭐ 「boot/预热之后第一击咬不咬」——945 的 8 个格次全都是
                # `i=0 / bit=False / identity_stable=False`（2/2），值得单独立读数
                c["first_click_bites"] = int(bool(d["bit"]))
                c["first_click_stable"] = bool(d["identity_stable"])
            pre = post                      # ⭐ 每一击都换成新普查
            dump(out)
        c.setdefault("first_click_bites", 0)
        c.setdefault("first_click_stable", False)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点完 {c['n_click']} 次（咬到 {c['click_bites']}）"
              f" ⇒ 不带ti={c['w_after_clicks']}", flush=True)

        # ⭐ 固定受控的那一侧：程序化聚焦带 tabindex=0 的节点**本体**
        fa = ev(ARM_FOCUS_JS, [NODE_SEL])
        c["focus"] = fa
        print(f"      程序化聚焦节点本体：{fa}", flush=True)

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
                  f" 不带ti {pre['n_without_ti']}→{cur['n_without_ti']}",
                  flush=True)
            pre = cur
            dump(out)
            if k == 1:
                c["w_after_tab1"] = cur["n_without_ti"]
        c.setdefault("w_after_tab1", pre["n_without_ti"])
        c["w_final"] = pre["n_without_ti"]
        # ⭐ 「补回」= **关系式**：连点把「不带 ti」推高了、第 1 击 Tab 又压回 1
        c["compensated"] = bool(c["click_bites"] > 0
                                and c["w_after_clicks"] > c["ready_without_ti"]
                                and c["w_after_tab1"] == 1)
        c["n_added_total"] = sum(t["n_added"] for t in c["tabs"])
        c["cell_ok"] = bool(c["n_click"] == c["click_bites"]
                            and c["warm_reached"] and c["landable_found"] >= scale)
        print(f"      ⇒ 补回={c['compensated']}（连点后 {c['w_after_clicks']}"
              f" → 第1击后 {c['w_after_tab1']}、终值 {c['w_final']}）、"
              f"格可用={c['cell_ok']}", flush=True)
        dump(out)

# ⭐ `reps_identical` 这次**真算**（945 只声明没赋值 ⇒ 那道门等于没有）
_ident = []
for ci in range(len(CELLS)):
    got = [stable_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["design_gates"] = {
    # 格子数对得上，且**末格是 sham**（专为证伪本批仪器而设计，不许省）
    "sham_present": bool(CELLS[-1]["scale"] == 0),
    "sham_is_only_scale0": bool(sum(1 for x in CELLS if x["scale"] == 0) == 1),
    # 规模与 mode 都**钉死**了 ⇒ 本批只动一个自变量
    "scale_fixed": bool(len({x["scale"] for x in CELLS if x["scale"]}) == 1),
    "warm_varies": bool(len({x["warm"] for x in CELLS}) > 1),
    # sham 那一格：**零点击** ⇒ 不许有 click_rows
    "sham_zero_clicks": bool(all(
        not run["cells"][-1].get("click_rows")
        and run["cells"][-1].get("n_click") == 0
        for run in out["runs"] if "skipped" not in run["cells"][-1])),
    # ⭐ sham 必须在**每一轮**都真的没点过（仪器不是只在某一轮是 sham）
    "sham_ran_every_rep": bool(all(
        "skipped" not in run["cells"][-1] for run in out["runs"])),
    # 逐格 2/2 相同
    "reps_identical": bool(all(_ident)),
    # 派生键不许与原始键重叠（第二道，跑完再查一次）
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "removed",
                                     "added", "n_without_ti", "active_tag",
                                     "focus_in_node"))),
}
print("\n设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
