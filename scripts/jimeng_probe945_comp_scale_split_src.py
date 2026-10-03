#!/usr/bin/env python3
r"""batch 945 源站探针（**纯诊断**）：**把 943 与 944 之间唯一的分歧拆成两个自变量**。

## 那个分歧是什么

- **943**：鼠标臂连点 **5** 次之后，键盘臂的**第一击**把删掉的
  **6** 个**一次性**写回（`added=[0,4,6,7,8,9]`、「不带 ti」6→1）。
- **944**：鼠标臂连点 **7** 次之后第 1 击补回 **7** 个（14→1）；
  但连点 **13** 次之后**连按 6 下** `added` 恒 **0**、「不带 ti」恒 **14**。

⇒ 两批的读数**互相冲突**，而 944 已经把它记成「两轮不一致、**不许**下结论」。
⇒ 本批就干一件事：**找出到底哪个自变量在决定结果**。

## ⭐ 关键：两个自变量在 944 里是**缠在一起**的

944 同时变了两样东西：

| 自变量 | 944 的取值 |
| --- | --- |
| **A：连点次数**（规模） | 7 / 13 |
| **B：那一击是不是**臂事件 | **不确定** —— `active_tag=BUTTON`，而按 §131/943 焦点落在节点**内部的按钮**上是**死按压** |

⇒ 「规模到 13 就不补了」与「那一击压根不是臂事件」**都能解释** 944 的读数
⇒ 承 930 的纪律：**两件事同时发生，只能归因到其中一件** —— 必须拆开。

## 本批的设计：一个 **2 × 3** 的格子表

- **自变量 A（规模）**：`scale ∈ {2, 6, 12}` 次本体点击
- **自变量 B（那一击是什么）**：`mode ∈ {"body", "asis"}`
  - `body` ⭐ **按 Tab 之前先程序化聚焦**带 `tabindex="0"` 的那个节点**本体**
    ⇒ 保证这一击**是**臂事件（这是**受控**的那一侧）
  - `asis` —— 不干预，让焦点停在点击留下的地方（944 实际遇到的情形）
- 每格：**独立 `boot()`**（状态不许串）、走初始化、等身份稳定、点 `scale` 次、
  按 1 下 `Tab` 记读数、再按 1 下记读数。
- **2 轮**，格子内读数**逐条相同**才算数。

⚠️ **`boot()` 每格都调**：940 记过「AI 侧栏 Esc 关不掉」，而选中态也会被带跑
⇒ 跨格复用状态就是**把上一格的结论带进这一格**。

## 判决点（关系式）

- **A 是主因？** ⇒ `mode="body"` 下「补回」与 `scale` **无关**，
  而 `mode="asis"` 下随 `scale` 变 ⇒ 那 944 的 `scale=13` 不补是因为 B 不是 A
- **B 是主因？** ⇒ `mode="body"` 下**任何** `scale` 都补 ⇒ 规模无关
- **两个都补** ⇒ 944 的读数另有原因（**那就如实说两个都不是**）
- **两个都不补** ⇒ 规模有关**且**与 B 无关

## ⭐ 顺带把 944 的 S 臂反向也答掉

944 的 S 臂第二对 `bit=False`、状态被前一带跑 ⇒ 反向没测到。
⚠️ 但**944 的 L 臂其实已经答了**：它连点 **13 个不同下标**、
每点一下都是一次臂事件（`bit=True`）⇒ **「点未选中的节点必然咬」**
在「本体落点、13 个不同下标」这个范围内 **2/2 成立**。
⇒ 本批把它作为**读数引用**，**不另设臂**（免得又做一臂、又多一串未测）。

## 探针自带的四道纪律（承 943/944）

1. ⭐ **防漂移**：普查 / 落点 / 焦点 / 空白点四段 JS **逐字 assert** 与 943 相同
   （940 的办法；936 栽过「同一判据写两套定义」）
2. ⭐ **尺子自证**：身份串必须先稳定（无交互双读 + 初始化已发生）
3. **不许拿陈旧普查当基线**：每一段退出前 `pre = cur`
4. ⭐ **派生键不许重名、原始键不许漏登记**（935 的两道免疫针）

## 计费边界

只点**节点本体**、只按 `Tab`。⛔ 守卫拦在 `mouse.click` **之前**，
契约是「**我正要点的这个元素**是什么」。**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe945_comp_scale_split_src.py
"""

import json
import pathlib

OUT = "/tmp/b945-comp-scale-split.json"
REPS = 2
P943 = pathlib.Path(__file__).with_name(
    "jimeng_probe943_arm_relation_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_REC = 2                 # 每格按几下 Tab（第一击是关键，第二击看是不是一次补完）
# ⭐ 两个自变量：`scale`（规模）× `mode`（那一击是不是臂事件）
CELLS = [{"scale": 2, "mode": "body"},
         {"scale": 6, "mode": "body"},
         {"scale": 12, "mode": "body"},
         {"scale": 12, "mode": "asis"}]

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti",
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "active_tag", "active_tid", "focus_in_node", "blank", "point", "i",
    "k", "arm", "hit_tag",
})
DERIVED_KEYS = frozenset({
    "scale", "mode", "n_settle", "ready_without_ti", "landable_found",
    "n_click", "click_bites", "w_after_clicks", "w_after_tabs", "recovered",
    "n_added_total", "focus_ok", "cell_ok", "reps_identical",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("scale", "mode", "recovered", "cell_ok", "reps_identical"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"

# ── 空白点 / 普查 / 落点 / 焦点：与 943 **逐字相同**（下面统一 assert）────
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

# ── ⭐ 程序化聚焦那个带 tabindex="0" 的**节点本体**（受控的那一侧）────
ARM_FOCUS_JS = """([nodeSel]) => {
  const el = document.querySelector(nodeSel + '[tabindex="0"]');
  if (!el) return {focus_ok: false, why: '找不到带 tabindex=0 的节点'};
  el.focus();
  return {focus_ok: document.activeElement === el,
          active_tag: (document.activeElement.tagName || '').toUpperCase()};
}"""

_p943src = P943.read_text(encoding="utf-8") if P943.exists() else ""
for _name in ("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS"):
    assert eval(_name) in _p943src, (      # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 943 那份**不一致** —— 两份定义开始分家了")
assert "ARM_FOCUS_JS" not in _p943src, "945 的新件别混进「逐字相同」那组"

SLICE_STR = "|| '').slice(0, "
for _name in ("CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"):
    _js = eval(_name)                         # noqa: S307
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


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "cells": CELLS, "n_rec": N_REC,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "question": "补偿的「规模阈值」与「那一击是不是臂事件」哪个是主因",
       "void_runs": [
           "944 v1：写下过「补偿没来」，**已撤回**"
           "（它的 is_arm 判据太松，焦点落在节点内部的按钮上是死按压）",
           "944 v3：scale=7 补 / scale=13 不补，**两轮不一致** ⇒ 本批拆自变量",
       ],
       "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, cell in enumerate(CELLS):
        scale, mode = cell["scale"], cell["mode"]
        print(f"  --- 格 {ci}：scale={scale} mode={mode} ---", flush=True)
        # ⭐ 每格**独立 boot**（940：状态会被带跑；AI 侧栏 Esc 关不掉）
        n_audio = boot_fn()
        c = {"ci": ci, "scale": scale, "mode": mode,
             "n_audio_rail_button": n_audio, "click_bites": 0,
             "n_click": 0, "tabs": []}
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
        # ⭐ 尺子自证：等「初始化已发生 **且** 身份稳定」，退出前 `pre = cur`
        n_settle = 0
        for _ in range(12):
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            n_settle += 1
            cur = ev(CENSUS_JS, [NODE_SEL])
            pre = cur                      # ⭐ 不许拿陈旧读数当基线
            if cur["n_without_ti"] <= 1:
                break
        c["n_settle"] = n_settle
        c["ready_without_ti"] = pre["n_without_ti"]
        print(f"      就绪：等稳定 {n_settle} 下、不带ti={pre['n_without_ti']}",
              flush=True)

        # 扫全表取**本体**可点的下标（943 的教训：固定挑会踩空）
        landable = []
        for i in range(pre["n_nodes"]):
            if ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)]):
                landable.append(i)
            if len(landable) >= scale + 2:
                break
        c["landable_found"] = len(landable)

        # 点 `scale` 次**不同**的节点（⭐ 顺带验「点未选中必然咬」）
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
            pre = post                      # ⭐ 每一击都换成新普查
            dump(out)
        c["w_after_clicks"] = pre["n_without_ti"]
        print(f"      点完 {c['n_click']} 次（咬到 {c['click_bites']}）"
              f" ⇒ 不带ti={c['w_after_clicks']}", flush=True)

        # ⭐⭐ **自变量 B**：按 Tab 之前焦点的落点
        if mode == "body":
            fa = ev(ARM_FOCUS_JS, [NODE_SEL])
            c["focus"] = fa
            print(f"      [B=body] 程序化聚焦节点本体：{fa}", flush=True)

        for k in range(1, N_REC + 1):
            f0 = ev(FOCUS_JS, [NODE_SEL])
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            cur = ev(CENSUS_JS, [NODE_SEL])
            d = delta(pre, cur)
            f1 = ev(FOCUS_JS, [NODE_SEL])
            # ⭐ 「是不是臂事件」判得比 944 更严：**按之前**焦点在不在节点本体上
            was_arm = bool(f0["focus_in_node"]) and f0["active_tag"] == "DIV"
            c["tabs"].append({"k": k, "was_arm": was_arm,
                              "active_before": f0["active_tag"],
                              "active_after": f1["active_tag"],
                              "bit": d["bit"],
                              "n_added": len(d["added"]),
                              "n_removed": len(d["removed"]),
                              "w_before": pre["n_without_ti"],
                              "w_after": cur["n_without_ti"],
                              "identity_stable": d["identity_stable"]})
            print(f"      [Tab {k}] 按前焦点={f0['active_tag']}"
                  f"{'/在节点内' if f0['focus_in_node'] else ''}"
                  f" was_arm={was_arm} added={len(d['added'])} "
                  f"不带ti {pre['n_without_ti']}→{cur['n_without_ti']}",
                  flush=True)
            pre = cur
            dump(out)
        c["w_after_tabs"] = pre["n_without_ti"]
        # 「补回」= 连点之后 > 1、连按之后回到 1（**关系式**，不钉绝对值）
        c["recovered"] = (c["w_after_clicks"] > 1 and pre["n_without_ti"] == 1)
        c["n_added_total"] = sum(t["n_added"] for t in c["tabs"])
        c["cell_ok"] = bool(c["n_click"] and c["n_click"] == c["click_bites"]
                            and c["landable_found"] >= scale)
        print(f"      ⇒ 补回={c['recovered']}（连点后 {c['w_after_clicks']} "
              f"→ 连按后 {c['w_after_tabs']}）、格可用={c['cell_ok']}", flush=True)
        dump(out)

print("\n读数已写入", OUT, flush=True)
