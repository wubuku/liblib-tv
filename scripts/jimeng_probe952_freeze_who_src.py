#!/usr/bin/env python3
r"""batch 952 源站探针（**纯诊断 / 零节点点击**）：⭐⭐⭐ 把 950 那个**仍然成立**的冻结拆开。

## 950 留下的、**仍然成立**的现象

950（零点击、2/2 逐条相同）从刚 `boot()` 完连按 14 下 `Tab`，其中**第 5~8 按指针不动**
（`no_ti` 冻在 `[2]`）。逐按看：

| 按 | 指针 | 按前焦点 | 按后焦点 | `was_arm` |
| --- | --- | --- | --- | --- |
| 4 | `[2]` | `DIV` | **`BUTTON`** | True |
| 5 | `[2]` | `BUTTON` | **`BUTTON`** | False |
| 6 | `[2]` | `BUTTON` | **`BUTTON`** | False |
| 7 | `[2]` | `BUTTON` | **`BUTTON`** | False |
| 8 | `[2]` | `BUTTON` | **`DIV`** | False |
| 9 | **`[3]`** | `DIV` | `DIV` | True |

⇒ 读出三件**950 没点名**的事：
1. 按 5/6/7 **焦点完全不动** ⇒ 不是「指针卡住」，是**那个元素把 `Tab` 吞了**
2. 按 8 **焦点离开了按钮、而指针仍不动** ⇒ **有一按滞后**
3. 按 9 指针才动 ⇒ 滞后恰好 **1 下**

⇒ 951 已经证明：在**「13 连点之后」**这条路径上**完全不会冻结** ⇒
**冻结只属于「冷启动直接 `Tab`」那条路径** ⇒ 复刻侧**必须**分开实现。

## 本批要答的四个问题（**全是「仍然成立」那个现象的**）

- **Q1 是哪个元素在吞？** ⇒ 记 `tag` / `testid` / `aria-label` / `class` / 在第几个节点 /
  `type` / `disabled`（`WHOAMI_JS`，本批**新件**）
- **Q2 `Shift+Tab` 能不能把它弄出来？**（反向臂 —— 940/943 的成对办法）
- **Q3 方向键有没有反应？**
- **Q4 `Escape` 能不能释放？**
- **Q5 那一按滞后是不是真的？**（指针在「焦点离开」那一按不动、下一按才动）

## 本批的设计

| 格 | 做什么 |
| --- | --- |
| **格 0** | `Tab` × **14**（**照 950 的基线**，2/2 对照），每按都记 `WHOAMI` |
| **格 1** | `Tab` × **4** 到达冻结点，然后**依次**试 `Shift+Tab` → `Tab` → `ArrowDown` → `Escape` → `Tab`×3，**每步全量记录** |

每格**独立 `boot()`**；**2 轮**。

## ⭐ 三道门（**全部可红**）

1. `reached_the_freeze` —— 格 1 必须**真的**走进冻结点（某按指针不动）。
   ⚠️ 可红：红了就说明**这次冻结没出现**，那一格**如实记、不下结论**。
2. `lag_is_one_press` —— 「焦点离开按钮的那一按指针不动、**下一按才动**」。
   ⚠️ 可红：红了就说明 950 那个「一按滞后」是**我看图说话**。
3. `escape_releases` / `shift_tab_moves` / `arrow_moves` —— 三条**各判各的**，
   ⚠️ **都不许**预设方向（红了就记红）。

## 探针自带的纪律（承 943→951）

1. ⭐ **防漂移**：六段 JS **逐字 assert 与 951 相同**（940 的办法）；
   `WHOAMI_JS` 是本批**新件**、显式 assert **不许混进**「逐字相同」那组
2. ⭐ **尺子自证**：每一段退出前 `pre = cur`；⚠️ **不许拿陈旧读数当基线**
3. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
4. ⭐ **派生键不许与原始键重叠、不许重名、原始键不许漏登记**（935 的两道免疫针）
5. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版栽过：漏一个逗号 ⇒ 门恒绿）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ **身份不稳的那一段三元组一律不许当读数**（946）
7. ⚠️ **写推断之前先查基线里有没有反例**（951 栽过：那条读数 945 早就写进去了）
8. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配
   （`^\+\|\s*(\d+)[a-z]?\s*\|`）当成**新增批次**而挡下提交。948 栽过一次。

## 计费边界

**本批零节点点击。** 只发一次画布空白点击去焦点（943 起的标准前置），
⛔ 守卫拦在 `mouse.click` **之前**，契约是「**我正要点的这个元素**是什么」。
**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe952_freeze_who_src.py
"""

import json
import pathlib

OUT = "/tmp/b952-freeze-who.json"
REPS = 2
P951 = pathlib.Path(__file__).with_name(
    "jimeng_probe951_focus_gate_src.py")

SETTLE = 350
BLANK_WAIT = 900
NO_TI_CAP = 40
N_PRESS_BASE = 14          # 格 0：照 950
N_PRESS_LEAD = 4           # 格 1：先按 4 下到达冻结点
# ⭐ 判别组：每一步都全量记录，**不许**预设方向
PROBE_STEPS = [("Shift+Tab", 1), ("Tab", 1), ("ArrowDown", 1),
               ("Escape", 1), ("Tab", 3)]

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
    # WHOAMI_JS（950/951 那批焦点读数里**没有**的字段）
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who",
})
DERIVED_KEYS = frozenset({
    "ci", "mode", "n_press", "n_audio_rail_button", "cold_without_ti",
    "rows", "frozen_presses", "swallowed_presses", "left_button_press",
    "lag_is_one_press", "reached_the_freeze", "escape_releases",
    "shift_tab_moves", "arrow_moves", "step_rows", "cell_ok",
    "reps_identical", "design_gates", "curve_reproducible",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "frozen_presses", "lag_is_one_press",
              "reached_the_freeze", "reps_identical", "curve_reproducible"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index"):
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

# ⭐⭐ 本批的新件：**「现在焦点在谁身上」** —— 950/951 那份焦点读数**没有**这些字段，
#    所以它答不了 Q1（是哪个元素在吞 `Tab`）。
WHOAMI_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {who: null, tag: null, tid: null, aria: null, cls: null,
                  node_index: null, in_node_list: false, disabled: null,
                  type_attr: null, rect: null};
  const all = Array.from(document.querySelectorAll(nodeSel));
  const node = a.closest(nodeSel);
  const host = a.closest('[data-testid]');
  const r = a.getBoundingClientRect();
  return {who: 1, tag: (a.tagName || '').toUpperCase(),
          tid: host ? host.getAttribute('data-testid') : null,
          aria: a.getAttribute('aria-label') || a.getAttribute('title')
                || (a.innerText || '').slice(0, 30) || null,
          cls: (a.className && a.className.baseVal !== undefined)
                 ? a.className.baseVal : String(a.className || ''),
          node_index: node ? all.indexOf(node) : null,
          in_node_list: !!node,
          disabled: a.disabled === true,
          type_attr: a.getAttribute('type'),
          rect: [Math.round(r.left), Math.round(r.top),
                 Math.round(r.width), Math.round(r.height)]};
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

# ⭐ 六段（950 新件 `NO_TI_JS` 也算）都与 951 **逐字相同**
_p951src = P951.read_text(encoding="utf-8") if P951.exists() else ""
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL):
    assert _js in _p951src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 951 那份**不一致** —— 两份定义开始分家了")
# ⭐ `WHOAMI_JS` 是本批**新件** ⇒ 必须**不在** 951 里（不然两份定义会分家）
assert "WHOAMI_JS" not in _p951src, "952 的新件别混进「逐字相同」那组"


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
            ("mode", "n_press", "cold_without_ti", "rows", "step_rows",
             "frozen_presses", "swallowed_presses", "left_button_press",
             "lag_is_one_press", "reached_the_freeze", "escape_releases",
             "shift_tab_moves", "arrow_moves")}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS,
       "n_press_base": N_PRESS_BASE, "n_press_lead": N_PRESS_LEAD,
       "probe_steps": PROBE_STEPS, "no_ti_cap": NO_TI_CAP,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "950 那个仍然成立的冻结：是「焦点困住」还是「按钮自己吞了 Tab」",
       "void_runs": [
           "944 v1：「补偿没来」**已撤回**（is_arm 判据太松）",
           "946：`warm` 压根没被操控 ⇒ `warm_reached` 恒真、已撤回",
           "948：**944 的矛盾结案（是个误读）**；就绪 = 1 是瞬态",
           "949：944 那次读数**不可复现**（同一组数字 2/2 测到补偿）",
           "950：零点击 14 下 ⇒ 铺窗口是**一次性事件**；"
           "**指针会在内部 BUTTON 上冻住 5 下**（**这条仍然成立**）",
           "951：⚠️ **950 那条「拿它解释 944」的推断已撤回** —— "
           "`arm_focus` 在 944 条件下是 **no-op**（点击后焦点本来就在 DIV 上）；"
           "⇒ **冻结只属于「冷启动直接 Tab」那条路径**",
           "⚠️ 951 还留了一条：**写推断之前要先查基线里有没有反例**"
           "（那条读数 945 早就写进基线了）",
       ],
       "runs": []}


def press_row(page, pre, key, k, phase, step):
    """按一次键，记全量。**所有**读数都在这里取，顺序固定。"""
    nt0 = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
    f0 = ev(FOCUS_JS, [NODE_SEL])
    w0 = ev(WHOAMI_JS, [NODE_SEL])
    page.keyboard.press(key)
    page.wait_for_timeout(SETTLE)
    cur = ev(CENSUS_JS, [NODE_SEL])
    d = delta(pre, cur)
    nt1 = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
    f1 = ev(FOCUS_JS, [NODE_SEL])
    w1 = ev(WHOAMI_JS, [NODE_SEL])
    row = {"phase": phase, "step": step, "k": k, "key": key,
           "no_ti_before": nt0["no_ti"], "no_ti_after": nt1["no_ti"],
           "no_ti_capped": bool(nt0["no_ti_capped"] or nt1["no_ti_capped"]),
           "pointer_moved": nt0["no_ti"] != nt1["no_ti"],
           "active_before": f0["active_tag"], "active_after": f1["active_tag"],
           "focus_in_node_after": f1["focus_in_node"],
           "was_arm": bool(f0["focus_in_node"]) and f0["active_tag"] == "DIV",
           "focus_moved": (f0["active_tag"], f0["active_tid"])
                          != (f1["active_tag"], f1["active_tid"]),
           "bit": d["bit"], "n_added": len(d["added"]),
           "n_removed": len(d["removed"]),
           "w_before": pre["n_without_ti"], "w_after": cur["n_without_ti"],
           "identity_stable": d["identity_stable"],
           "who_before": w0, "who_after": w1}
    return row, cur


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, mode in enumerate(("base", "probe")):
        n_press = N_PRESS_BASE if mode == "base" else N_PRESS_LEAD
        tag = ("照 950 的基线" if mode == "base"
               else f"先按 {N_PRESS_LEAD} 下到达冻结点，再跑判别组")
        print(f"  --- 格 {ci}（{tag}）---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "mode": mode, "n_press": n_press,
             "n_audio_rail_button": n_audio, "rows": [], "step_rows": []}
        rec["cells"].append(c)
        dump(out)
        if n_audio == 0:
            c["skipped"] = "登录态没命中，本轮不测"
            continue

        sp = ev(BLANK_JS)
        c["blank"] = sp
        if sp:
            guard_point(sp[0], sp[1])      # ⭐ 只点**画布空白**去焦点
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(BLANK_WAIT)
        pre = ev(CENSUS_JS, [NODE_SEL])
        nt = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
        c["cold_without_ti"] = nt["n_without_ti"]
        c["rows"].append({"phase": "cold", "step": 0, "k": 0, "key": None,
                          "no_ti_before": nt["no_ti"],
                          "no_ti_after": nt["no_ti"],
                          "no_ti_capped": nt["no_ti_capped"],
                          "pointer_moved": False,
                          "active_before": None, "active_after": None,
                          "was_arm": None, "bit": None, "n_added": None,
                          "w_before": pre["n_without_ti"],
                          "w_after": pre["n_without_ti"],
                          "identity_stable": None,
                          "who_before": None,
                          "who_after": ev(WHOAMI_JS, [NODE_SEL])})
        print(f"      冷启动：nodes={pre['n_nodes']}、不带ti={nt['n_without_ti']}",
              flush=True)

        for k in range(1, n_press + 1):
            row, pre = press_row(page, pre, "Tab", k, "base", 0)
            c["rows"].append(row)
            print(f"      [Tab {k:>2}] 前={row['active_before']}"
                  f" 后={row['active_after']} 焦点动了={row['focus_moved']}"
                  f" 指针 {row['no_ti_before'][:3]}→{row['no_ti_after'][:3]}"
                  f"（动={row['pointer_moved']}）"
                  f" 不带ti {row['w_before']}→{row['w_after']}"
                  f" 按后焦点在节点#{row['who_after'].get('node_index')}"
                  f" aria={str(row['who_after'].get('aria'))[:22]!r}", flush=True)
            dump(out)

        if mode == "probe":
            step = 0
            for key, times in PROBE_STEPS:
                for _ in range(times):
                    step += 1
                    row, pre = press_row(page, pre, key, step, "probe", step)
                    c["step_rows"].append(row)
                    c["rows"].append(row)
                    print(f"      [{key} #{step}] 前={row['active_before']}"
                          f" 后={row['active_after']}"
                          f" 焦点动了={row['focus_moved']}"
                          f" 指针 {row['no_ti_before'][:3]}→"
                          f"{row['no_ti_after'][:3]}"
                          f"（动={row['pointer_moved']}）"
                          f" 不带ti {row['w_before']}→{row['w_after']}"
                          f" 按后 aria={str(row['who_after'].get('aria'))[:22]!r}"
                          f" type={row['who_after'].get('type_attr')!r}"
                          f" disabled={row['who_after'].get('disabled')}",
                          flush=True)
                    dump(out)

        # ── 派生量（**关系式**，不钉绝对值）────────────────────────────
        main_rows = [r for r in c["rows"] if r["phase"] in ("base", "cold")]
        c["frozen_presses"] = sum(1 for r in main_rows
                                  if r["k"] >= 1 and not r["pointer_moved"])
        c["swallowed_presses"] = sum(
            1 for r in main_rows
            if r["k"] >= 1 and not r["pointer_moved"] and not r["focus_moved"])
        # 「焦点离开按钮的那一按」= `active_before=BUTTON` 且 `active_after≠BUTTON`
        c["left_button_press"] = next(
            (r["k"] for r in main_rows
             if r["k"] >= 1 and r["active_before"] == "BUTTON"
             and r["active_after"] != "BUTTON"), None)
        # ⭐ 门：滞后恰好 1 下 —— 「离开」那一按指针不动、**下一按**才动
        lb = c["left_button_press"]
        c["lag_is_one_press"] = bool(
            lb is not None
            and not next(r for r in main_rows if r["k"] == lb)["pointer_moved"]
            and next((r["pointer_moved"] for r in main_rows
                      if r["k"] == lb + 1), False))
        c["reached_the_freeze"] = bool(c["frozen_presses"] > 0)
        st = c["step_rows"]
        _mv = lambda key, times: [          # noqa: E731
            r for r in st if r["key"] == key][:times]
        c["shift_tab_moves"] = any(
            r["focus_moved"] for r in _mv("Shift+Tab", 1))
        c["arrow_moves"] = any(r["focus_moved"] for r in _mv("ArrowDown", 1))
        c["escape_releases"] = any(r["focus_moved"] for r in _mv("Escape", 1))
        c["cell_ok"] = bool(len(main_rows) == n_press + 1)
        print(f"      ⇒ 冻住 {c['frozen_presses']} 下、"
              f"其中**焦点也没动**的 {c['swallowed_presses']} 下、"
              f"离开按钮的那一按 k={lb}、滞后 1 下={c['lag_is_one_press']}"
              + (f"｜Shift+Tab 动了={c['shift_tab_moves']}、"
                 f"方向键动了={c['arrow_moves']}、"
                 f"Esc 动了={c['escape_releases']}" if st else ""),
              flush=True)
        dump(out)

_ident = []
for ci in range(2):
    got = [curve_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["curve_reproducible"] = bool(all(_ident))

out["design_gates"] = {
    "zero_node_clicks": bool(all(
        not run["cells"][ci].get("click_rows")
        and run["cells"][ci].get("n_click", 0) == 0
        for run in out["runs"] for ci in range(2)
        if "skipped" not in run["cells"][ci])),
    "pressed_exactly_n": bool(all(
        len([r for r in run["cells"][ci].get("rows", [])
             if r.get("phase") == "base" and r.get("k", 0) >= 1]) == n_press
        for run in out["runs"] for ci, n_press in ((0, N_PRESS_BASE),
                                                   (1, N_PRESS_LEAD))
        if "skipped" not in run["cells"][ci])),
    "curve_reproducible": out["curve_reproducible"],
    "reached_the_freeze": bool(all(
        run["cells"][0].get("reached_the_freeze")
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "lag_is_one_press": bool(all(
        run["cells"][0].get("lag_is_one_press")
        for run in out["runs"] if "skipped" not in run["cells"][0])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                     "active_tag", "focus_in_node", "no_ti",
                                     "aria", "node_index"))),
}
print("\n设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
