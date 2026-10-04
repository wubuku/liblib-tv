#!/usr/bin/env python3
r"""batch 951 源站探针（**纯诊断**）：⭐⭐⭐ 把 950 那条机制**从推断升级成实测**。

## 950 留下的是什么状态

950（**零点击**、2/2 逐条相同）测出了完整规则，并且发现：
**焦点一旦落在节点内部的 `BUTTON` 上，`Tab` 连按 5 下指针完全不动**
（指针冻在 `[2]`、那 5 下 `active_before = BUTTON`、`was_arm = False`、三元组全空）。

950 据此**推断**：「944 那次『连按 6 下 `added` 恒 0』不是没补偿，
而是**那 6 下压根没在臂窗口上按**」。

⚠️ 但 950 自己写明了：**这三条链接都是推断、不是实测** ——
**944 从没记过「无 `tabindex` 的下标」是哪几个**。
⇒ 950 的下一批写明：**「这才是把第四节从推断升级成实测的唯一一步」**。本批就是它。

## ⭐ 本批与 949/944 的**唯一**差别：按 Tab 之前**做不做**程序化聚焦

| | 949（测到补偿） | **944（没测到）** | 本批 |
| --- | --- | --- | --- |
| 就绪 | 显式按 2 下 ⇒ **1** | settle 10 下 ⇒ **1** | **显式按 2 下 ⇒ 1** |
| 连点 | 13 次 | 13 次 | **13 次** |
| 按 Tab | 6 下 | 6 下 | **6 下** |
| ⭐ 按 Tab 前**程序化聚焦节点本体** | **做了** | **没做** | ⭐ **两格各做一半** |
| ⭐ 记不记指针 `no_ti` | 没记 | 没记 | ⭐⭐ **每按都记** |

⇒ 本批把 949 与 944 之间**那一个**差别**单独做成自变量**，其余全固定：

| 格 | 按 Tab 前 | 身份 |
| --- | --- | --- |
| **格 0** | **不**程序化聚焦（焦点留在点击留下的样子） | ⭐ **照 944** |
| **格 1** | 程序化聚焦节点本体（`ARM_FOCUS_JS`） | ⭐ **照 949**（同一次跑里的对照） |

## 判决点（**关系式**）

- **格 0 指针冻住、格 1 指针每按都动？** ⇒ ⭐ **950 的机制被实测证实**，
  且「按 Tab 前焦点在哪」就是 944 与 949 的**那一个**差别
- **两格指针一样？** ⇒ ⭐⭐ **950 的机制被证伪** ⇒ 944 与 949 的差别在**别处**
  ⇒ **撤回** 950 那条推断（承 §77）
- **格 0 指针没冻、也没每按都动？** ⇒ 如实记，**不下结论**

## ⭐⭐ 反恒绿门

`focus_moved_the_pointer` —— 两格的 `no_ti` 序列**必须不一样**。
⚠️ 这道门**可红**：红了就说明「聚焦」这个操纵**没起作用**
（和 946 的 `warm_reached` 同一个病 —— 那边已撤回）。
⇒ ⭐ **「这个操纵到底动了没有」必须自己答，不能默认它动了。**

## 探针自带的纪律（承 943→950）

1. ⭐ **防漂移**：五段 JS **逐字 assert 与 950 相同**（940 的办法）；
   `NO_TI_JS` 也逐字相同（950 的新件，本批直接用）
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`；⚠️ **不许拿陈旧读数当基线**
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ **身份不稳的那一段三元组一律不许当读数**（946）
7. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配
   （`^\+\|\s*(\d+)[a-z]?\s*\|`）当成**新增批次**而挡下提交。948 栽过一次。

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」。**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe951_focus_gate_src.py
"""

import json
import pathlib

OUT = "/tmp/b951-focus-gate.json"
REPS = 2
P950 = pathlib.Path(__file__).with_name(
    "jimeng_probe950_coldwindow_src.py")

SETTLE = 350
BLANK_WAIT = 900
SCALE_FIXED = 13           # ⭐ 944 的数字
N_REC_FIXED = 6            # ⭐ 944 的数字
NSETTLE_FIXED = 2          # ⇒ 就绪 `不带 ti` = 1（948/949 已 2/2 验过）
NO_TI_CAP = 40
# ⭐ 唯一自变量：按 Tab 之前**做不做**程序化聚焦
CELLS = [{"arm_focus": False}, {"arm_focus": True}]

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
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
    "ci", "arm_focus", "n_rec", "n_settle", "scale", "n_audio_rail_button",
    "ready_without_ti", "settle_rows", "landable_found", "n_click",
    "click_bites", "w_after_clicks", "w_final", "tabs", "tab_rows",
    "pointer_frozen_presses", "pointer_moves", "added_total",
    "compensated", "cell_ok", "reps_identical", "design_gates",
    "focus_moved_the_pointer", "mechanism_confirmed_951",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("arm_focus", "pointer_frozen_presses", "focus_moved_the_pointer",
              "reps_identical", "mechanism_confirmed_951"):
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

# ⭐ 六段（含 950 的新件 `NO_TI_JS`）都与 950 **逐字相同**
_p950src = P950.read_text(encoding="utf-8") if P950.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL):
    assert _js in _p950src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 950 那份**不一致** —— 两份定义开始分家了")


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
    return {k: cell.get(k) for k in
            ("arm_focus", "ready_without_ti", "landable_found", "n_click",
             "click_bites", "w_after_clicks", "w_final", "added_total",
             "pointer_frozen_presses", "pointer_moves", "compensated",
             "tab_rows", "click_rows")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS,
       "scale_fixed": SCALE_FIXED, "n_rec_fixed": N_REC_FIXED,
       "n_settle_fixed": NSETTLE_FIXED, "no_ti_cap": NO_TI_CAP,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "950 那条机制（焦点在内部按钮上 ⇒ 指针冻住）能不能被实测证实",
       "void_runs": [
           "944 v1：「补偿没来」**已撤回**（is_arm 判据太松）",
           "944 v3：scale=7 补 / scale=13 不补，两轮不一致",
           "945：scale 与 mode 都拆了、都排除不了",
           "946：`warm` 压根没被操控 ⇒ `warm_reached` 恒真、已撤回",
           "947：`wait_stable` 被排除",
           "948：受控落点表 ⇒ **944 的矛盾结案（是个误读）**；就绪 = 1 是瞬态",
           "949：用 944 自己那组数字重跑 ⇒ **那次读数不可复现**",
           "950：零点击 14 下 ⇒ **铺窗口是一次性事件**；"
           "**指针会在内部 BUTTON 上冻住 5 下** ⇒ "
           "⚠️ **那三条解释 944 的链接全是推断、不是实测**",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        af = cell["arm_focus"]
        tag = "★ 照 944（不程序化聚焦）" if not af else "照 949（程序化聚焦）＝对照"
        print(f"  --- 格 {ci}（{tag}）：n_settle={NSETTLE_FIXED} "
              f"scale={SCALE_FIXED} n_rec={N_REC_FIXED} ---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "arm_focus": af, "n_rec": N_REC_FIXED,
             "n_settle": NSETTLE_FIXED, "scale": SCALE_FIXED,
             "n_audio_rail_button": n_audio, "click_bites": 0, "n_click": 0,
             "tabs": [], "settle_rows": [], "tab_rows": []}
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
        print(f"      就绪：显式按 {NSETTLE_FIXED} 下 ⇒ 不带ti={pre['n_without_ti']}",
              flush=True)

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
            pre = post
            dump(out)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点 {SCALE_FIXED} 次：落点成功 {c['n_click']}、"
              f"咬到 {c['click_bites']} ⇒ 不带ti={c['w_after_clicks']}", flush=True)

        # ⭐⭐ **唯一自变量**就在这一行：做不做程序化聚焦
        if af:
            fa = ev(ARM_FOCUS_JS, [NODE_SEL])
            c["focus"] = fa
            print(f"      程序化聚焦节点本体：{fa}", flush=True)
        else:
            fnow = ev(FOCUS_JS, [NODE_SEL])
            c["focus_skipped"] = fnow
            print(f"      ⭐ 不程序化聚焦，焦点留在点击留下的样子：{fnow}", flush=True)

        for k in range(1, N_REC_FIXED + 1):
            nt0 = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
            f0 = ev(FOCUS_JS, [NODE_SEL])
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            cur = ev(CENSUS_JS, [NODE_SEL])
            d = delta(pre, cur)
            nt1 = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
            f1 = ev(FOCUS_JS, [NODE_SEL])
            was_arm = bool(f0["focus_in_node"]) and f0["active_tag"] == "DIV"
            row = {"k": k, "was_arm": was_arm,
                   "active_before": f0["active_tag"],
                   "active_after": f1["active_tag"],
                   "focus_in_node": f1["focus_in_node"],
                   "no_ti_before": nt0["no_ti"], "no_ti_after": nt1["no_ti"],
                   "no_ti_capped": bool(nt0["no_ti_capped"]
                                        or nt1["no_ti_capped"]),
                   "pointer_moved": nt0["no_ti"] != nt1["no_ti"],
                   "bit": d["bit"], "n_added": len(d["added"]),
                   "n_removed": len(d["removed"]),
                   "w_before": pre["n_without_ti"],
                   "w_after": cur["n_without_ti"],
                   "identity_stable": d["identity_stable"]}
            c["tab_rows"].append(row)
            c["tabs"].append({"k": k, "n_added": len(d["added"]),
                              "w_after": cur["n_without_ti"]})
            print(f"      [Tab {k}/{N_REC_FIXED}] 前焦点={f0['active_tag']}"
                  f" 后焦点={f1['active_tag']} was_arm={was_arm}"
                  f" 指针 {nt0['no_ti'][:3]}→{nt1['no_ti'][:3]}"
                  f"（动了={row['pointer_moved']}）"
                  f" 不带ti {pre['n_without_ti']}→{cur['n_without_ti']}"
                  f" added={len(d['added'])}", flush=True)
            pre = cur
            dump(out)
        c["w_final"] = pre["n_without_ti"]
        c["added_total"] = sum(t["n_added"] for t in c["tab_rows"])
        c["pointer_moves"] = sum(1 for r in c["tab_rows"] if r["pointer_moved"])
        c["pointer_frozen_presses"] = sum(
            1 for r in c["tab_rows"] if not r["pointer_moved"])
        c["compensated"] = bool(c["click_bites"] > 0
                                and c["w_after_clicks"] > c["ready_without_ti"]
                                and c["tab_rows"]
                                and c["tab_rows"][0]["w_after"] == 1)
        c["cell_ok"] = bool(c["n_click"] == c["click_bites"])
        print(f"      ⇒ 指针动 {c['pointer_moves']}/{N_REC_FIXED}、"
              f"冻住 {c['pointer_frozen_presses']} 下、"
              f"added 合计 {c['added_total']}、补回={c['compensated']}", flush=True)
        dump(out)

_ident = []
for ci in range(len(CELLS)):
    got = [stable_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident

# ⭐⭐ 反恒绿门：两格的指针序列**必须不一样**（不然「聚焦」这个操纵没起作用）
_c0 = [run["cells"][0] for run in out["runs"] if "skipped" not in run["cells"][0]]
_c1 = [run["cells"][1] for run in out["runs"] if "skipped" not in run["cells"][1]]
_seq = lambda xs: [tuple(r["no_ti_after"][:3]) for r in xs[0].get("tab_rows", [])]  # noqa: E731
out["focus_moved_the_pointer"] = bool(
    _c0 and _c1 and _seq(_c0) != _seq(_c1))
# 机制被证实 = 「不聚焦那格冻住」且「聚焦那格动」
out["mechanism_confirmed_951"] = bool(
    _c0 and _c1
    and all(x.get("pointer_frozen_presses", 0) > 0 for x in _c0)
    and all(x.get("pointer_moves", 0) > 0 for x in _c1))

out["design_gates"] = {
    "pressed_exactly_ns": bool(all(
        len([r for r in cc.get("settle_rows", []) if r.get("press", 0) >= 1])
        == NSETTLE_FIXED
        for run in out["runs"] for cc in run["cells"]
        if "skipped" not in cc)),
    "grid_is_944_numbers": bool(CELLS and SCALE_FIXED == 13
                                and N_REC_FIXED == 6),
    "only_arm_focus_varies": bool(len({c["arm_focus"] for c in CELLS}) == 2),
    "reps_identical": bool(all(_ident)),
    "focus_moved_the_pointer": out["focus_moved_the_pointer"],
    "mechanism_confirmed_951": out["mechanism_confirmed_951"],
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                     "active_tag", "focus_in_node", "no_ti"))),
}
print("\n反恒绿门 focus_moved_the_pointer：", out["focus_moved_the_pointer"],
      flush=True)
print("机制被实测证实：", out["mechanism_confirmed_951"], flush=True)
print("设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
