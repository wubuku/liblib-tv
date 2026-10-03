#!/usr/bin/env python3
r"""batch 937 源站探针（**纯诊断**）：**源站能不能同时开出两个浮层？**
—— 把 H936「浮层互斥」从「与读数相容」做成**可证伪的实验**。

## 937 的由来（936 留下的）

936 测出：目标形态「**非全屏浮层盖住层内**控件」**两侧 0 观测** ⇒ 判据一个字不动。
⚠️ 但 H936（**「这一类不会出现，因为浮层互斥：开一层会关掉另一层」**）
只被标成「**未验证、只是与两侧读数相容**」——
936 当时同时观测到「最多 2 层」，而**那第 2 层是常驻的 `.react-flow__node-toolbar`**，
**不是**第二个浮层 ⇒ **936 没有测过「开一层会不会关掉另一层」这件正事。**

⇒ 937 就问这一件：**开 A 层，再开 B 层，A 还在不在？**

⚠️ **可证伪的方向是双向的**：
- A 被 B 关掉 ⇒ 与 H936 相容（互斥成立）⇒ 但**仍不等于** H936 成立
  （还需要「被关掉的层里那些控件因此才没被盖住」这后半截）
- **A 活下来** ⇒ H936 **被证伪** ⇒ 「这一类 0 观测」就有了别的解释，
  档位问题要重开

## ⭐⭐ 关键口径：「层」有两个数，混了就会读反（936 已经吃过一次）

`LAYER_SEL`（判据自己的选择器）命中的顶层元素里，
**`.react-flow__node-toolbar` / `.react-flow__node-panel` 是节点的一部分，不是浮层**
—— 936 实测「同时 2 层」里那第 2 层正是它。

⇒ 所以**两个数分开记**：
- `n_layer_roots` ＝ 全部顶层 `LAYER_SEL` 匹配（判据眼里的「层」）
- `n_overlay_roots` ＝ **扣掉**上面那两类（互斥问题真正关心的「浮层」）

⚠️ 只报前者、把它读成「两个浮层并存」，就是 936 明确警告过的那类误读。

## 身份必须用不随插入移位的键（936 的第二个坑）

`dom_sig` 是 `tag:nth-of-type` 路径，**下标会因插入而移位** ⇒
「A 还在不在」**不能**按 `dom_sig` 跨状态比（936 因此整轮作废过一次）。

⇒ 跨状态认层只用 **`data-testid` → `role` + 矩形就近**；
`dom_sig` **只**用于**同一快照内**的顶层去重（那里它是稳的）。

## 阳性对照：先证明「普查看得见第二个浮层」

⚠️ 0 观测本身不是证据（§62）。⇒ 在真实普查**之后**注入一个
**合成浮层**（`<div role="menu">` + 不透明底），确认 `n_overlay_roots` **真的 +1**；
加不上就说明普查是瞎的、本批读数作废。⚠️ 夹具**不设 `pointer-events: none`**
（`querySelectorAll` 不受它影响，但保持一致；真会被它影响的是
`elementsFromPoint`，本夹具不参与那条）。
⚠️ 注入的元素用完立刻移除并断言已移除。

## 计费边界（**结构上禁止**，不只靠自觉）

`FORBIDDEN_TIDS` 里是源站实测存在的**计费入口**：
`canvas-commerce-entry`（积分/会员入口，aria-label `Credits: 805 · 基础会员`）
—— **绝不点**。守卫按 `data-testid` 拦，**拦在 `mouse.click` 之前**。
其余只点：顶栏 launcher、缩放、侧栏、画布**空白**处右键。
**绝不**点生成/发送/购买/充值；**不点任何节点**（本批不需要节点工具栏）。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload`。
唯一的 DOM 改动是 C 段那个合成浮层，**当场删掉并断言删干净**。

## 派生键免疫针（935 踩过 `KeyError`）

`CENSUS_KEYS`（JS 原始读数）与 `DERIVED_KEYS`（Python 派生）分开列、
断言**不许重叠**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe937_layer_exclusivity_src.py
"""

import json

OUT = "/tmp/b937-src-layer-exclusivity.json"
REPS = 2

OPEN_WAIT = 1400
RESET_WAIT = 500

# ⚠️⚠️ 计费入口（源站实测存在）：**结构上禁止点击**，守卫拦在 click 之前
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger", "canvas-recharge")

# ⚠️ 逐字承判据（`jimeng_unclickable_audit.py` 的模块级单一来源）。
#    本批问的仍是「判据眼里的层」，尺子必须与判据同一份定义。
LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')
# ⭐ 这两类是**节点的一部分**，不是浮层（936 撞过：误把它读成第二个浮层）
NODE_PART_SEL = ".react-flow__node-toolbar, .react-flow__node-panel"

BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

CENSUS_KEYS = frozenset({
    "dom_sig", "tag", "tid", "role", "al", "x", "y", "w", "h",
    "is_node_part", "n_layer_roots", "n_overlay_roots", "boxes", "roots",
})
DERIVED_KEYS = frozenset({
    "a_opened", "b_opened", "a_survived", "both_overlays_coexist",
    "n_overlays_after_b", "new_overlay_tids_b", "b_blocked_a",
    "a_opened_by", "b_opened_by",
})
assert not (CENSUS_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了"
assert "a_survived" not in CENSUS_KEYS, "a_survived 必须是派生量"

# ⭐ `LAYER_SEL` 必须与判据那份**逐字相同**（本批问的就是判据眼里的「层」）。
#    936 因为「同一判据写两套定义」整轮作废过一次（把源站搜索层漏掉、
#    把常驻 Agent 侧栏当成了浮层）⇒ 这条**结构性地**钉住，不靠自觉。
#    ⚠️ 改这里之前先去改判据那个常量，两边必须一起动。
assert LAYER_SEL == (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')

# ⚠️ `__sig` **只**在这一段 JS 里出现一次（937 只有这一个块用它）⇒
# 没有第二份副本，也就没有「两份漂移」的问题。
# 935 教训（派生键不许与原始键重叠）在这里对应的就是下面的 assert。
# ── 层普查（判据自己的 `LAYER_SEL`；零尺寸的不算层）────────────────────
CENSUS_JS = """(args) => {
  const [sel, nodeSel] = args;
  const __sig = (e) => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      let i = 1;
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === n.tagName) i++;
      }
      parts.unshift(n.tagName + ':nth-of-type(' + i + ')');
    }
    return parts.join('/');
  };
  const boxes = [];
  for (const e of document.querySelectorAll(sel)) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    boxes.push({dom_sig: __sig(e), tag: e.tagName,
                tid: e.getAttribute('data-testid') || '',
                role: e.getAttribute('role') || '',
                al: (e.getAttribute('aria-label') || '').slice(0, 40),
                x: Math.round(r.x), y: Math.round(r.y),
                w: Math.round(r.width), h: Math.round(r.height),
                is_node_part: !!e.matches(nodeSel)});
  }
  // 顶层去重：互为祖先的只算一层（⚠️ 只在**同一快照内**用前缀）
  const roots = [];
  for (const b of boxes) {
    const pre = b.dom_sig + '/';
    if (boxes.some(o => o.dom_sig !== b.dom_sig
                        && pre.startsWith(o.dom_sig + '/'))) continue;
    roots.push(b);
  }
  return {boxes, roots,
          n_layer_roots: roots.length,
          n_overlay_roots: roots.filter(r => !r.is_node_part).length};
}"""

# ── 阳性对照用的合成浮层（**不是**探针的身份工具）──────────────────────
FIXTURE_ADD_JS = """() => {
  const d = document.createElement('div');
  d.setAttribute('data-b937-fixture', '1');
  d.setAttribute('role', 'menu');
  d.style.position = 'fixed';
  d.style.left = '120px';
  d.style.top = '160px';
  d.style.width = '240px';
  d.style.height = '180px';
  d.style.background = 'rgb(2, 3, 4)';
  d.style.zIndex = '2147483647';
  document.body.appendChild(d);
  return {ok: true};
}"""

FIXTURE_DEL_JS = """() => {
  const n = document.querySelectorAll('[data-b937-fixture]');
  n.forEach(e => e.remove());
  return document.querySelectorAll('[data-b937-fixture]').length;
}"""


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def topmost(boxes):
    out = []
    for b in boxes:
        pre = b["dom_sig"] + "/"
        if any(o["dom_sig"] != b["dom_sig"] and pre.startswith(o["dom_sig"] + "/")
               for o in boxes):
            continue
        out.append(b)
    out.sort(key=lambda b: -(b["w"] * b["h"]))
    return out


def census(tag):
    r = ev(CENSUS_JS, [LAYER_SEL, NODE_PART_SEL])
    roots = topmost(r["boxes"])
    # ⭐ Python 与 JS **各算了一遍**顶层去重 ⇒ 在这里**互相印证**。
    #    这不是重复实现：一致性不一致就说明其中一边的「互为祖先」判法坏了
    #    （936 栽在同一种「两个实现各算一遍、却不比对」上）。
    assert len(roots) == r["n_layer_roots"], (
        f"顶层去重两个实现对不上：JS {r['n_layer_roots']} vs Python {len(roots)}")
    overlays = [x for x in roots if not x["is_node_part"]]
    assert len(overlays) == r["n_overlay_roots"], (
        f"「浮层」数两个实现对不上：JS {r['n_overlay_roots']} vs Python {len(overlays)}")
    unknown = set(r) - CENSUS_KEYS
    assert not unknown, f"普查冒出未登记的原始键: {unknown}"
    return {"tag": tag, "n_layer_roots": len(roots),
            "n_overlay_roots": len(overlays),
            "roots": roots[:10], "overlays": overlays[:10]}


def guard(al, tid):
    """计费护栏：**先按 testid 硬拦**（结构上），再按文案等值拦。"""
    if tid in FORBIDDEN_TIDS:
        return f"护栏拦下计费入口 testid={tid!r}"
    t = (al or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        return f"护栏拦下付费动作 {t!r}"
    return None


def reset():
    for _ in range(2):
        page.keyboard.press("Escape")
        page.wait_for_timeout(RESET_WAIT)


def click_trigger(tid, idx=0, name=""):
    """按 `data-testid` 点触发器（源站实测这些 testid 稳定）。"""
    pt = page.evaluate("""(args) => {
      const [tid, i] = args;
      const es = [...document.querySelectorAll(`[data-testid="${tid}"]`)];
      if (es.length <= i) return null;
      const e = es[i];
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return null;
      return {n: es.length, al: (e.getAttribute('aria-label') || '').slice(0, 40),
              x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""", [tid, idx])
    if not pt:
        return {"ok": False, "why": f"没有可点的 {tid}[{idx}]"}
    blocked = guard(pt.get("al"), tid)
    if blocked:
        return {"ok": False, "why": blocked}
    page.mouse.click(pt["x"], pt["y"])
    return {"ok": True, "trigger": {"tid": tid, "idx": idx, "al": pt.get("al")}}


def open_context_menu():
    spot = page.evaluate("""() => {
      for (const [x, y] of [[430, 620], [420, 660], [450, 700], [400, 580],
                            [470, 640], [440, 680]]) {
        const e = document.elementFromPoint(x, y);
        if (!e) continue;
        if (e.closest('[data-id]')) continue;
        if (!e.closest('.react-flow__pane, .react-flow__renderer, '
                     + '[class*=pane], [class*=canvas]')) continue;
        return {x, y};
      }
      return null;
    }""")
    if not spot:
        return {"ok": False, "why": "找不到空画布落点"}
    page.mouse.click(spot["x"], spot["y"], button="right")
    return {"ok": True, "trigger": {"tid": "(空画布右键)", "idx": -1,
                                    "al": f"@{spot['x']},{spot['y']}"}}


# ⚠️ 只用**非计费**触发器；`canvas-commerce-entry` 故意列在注释里当反面例子
OPENERS = [
    ("顶栏·搜索", lambda: click_trigger("canvas-panel-launcher", 0)),
    ("顶栏·生成历史", lambda: click_trigger("canvas-panel-launcher", 1)),
    ("缩放菜单", lambda: click_trigger("canvas-zoom-percent", 0)),
    ("与 AI 对话侧栏", lambda: click_trigger("canvas-sidecar-launcher", 0)),
    ("画布右键菜单", open_context_menu),
    # ⛔ 反面例子（**绝不点**，守卫会拦）：canvas-commerce-entry = 积分/会员入口
]


def keys_of(c):
    """一层普查里的**全部**浮层身份（只取不随插入移位的键）。"""
    out = set()
    for o in c["overlays"]:
        if o["tid"]:
            out.add("tid:" + o["tid"])
        elif o["role"]:
            out.add("role:%s@%dx%d" % (o["role"], o["w"], o["h"]))
    return out


def pair_test(a_name, a_open, b_name, b_open):
    """开 A → 记 → 开 B → 记，看 **A 还在不在**。"""
    reset()
    c0 = census("before")
    ra = a_open()
    page.wait_for_timeout(OPEN_WAIT)
    ca = census("after_a")
    rb = b_open()
    page.wait_for_timeout(OPEN_WAIT)
    cb = census("after_b")

    # ⚠️⚠️⚠️ 937 第一版在这里写的是 `if k and k != base_ids:`
    #    —— `k` 是**字符串**、`base_ids` 是**集合**，`!=` **恒为真**
    #    ⇒ 每个浮层都「通过」⇒ 循环把**最后一个**浮层当成 A
    #    ⇒ 而那最后一个实测正是**常驻的 `canvas-editor-menu`**
    #    ⇒ `a_survived` 测的是「常驻层还在不在」⇒ **恒为 true**。
    # ⭐ 后果有多严重：探针自己打的汇总是「**32/32 全部并存、H936 被证伪**」，
    #    而从原始读数重算的真相是「**24/28 里开 B 会关掉 A**」——
    #    **结论正好相反**。⇒ 身份必须用**集合差**算，不是逐个 `!=`。
    base = keys_of(c0)
    a_new = keys_of(ca) - base
    a_opened = bool(a_new)
    a_survived = bool(a_new & keys_of(cb)) if a_opened else None
    b_new = keys_of(cb) - base - a_new
    b_opened = bool(b_new)
    rec = {
        "a": a_name, "b": b_name, "a_open_result": ra, "b_open_result": rb,
        "base_keys": sorted(base),
        "a_new_keys": sorted(a_new), "b_new_keys": sorted(b_new),
        "cb_keys": sorted(keys_of(cb)),
        "c0_n_overlay_roots": c0["n_overlay_roots"],
        "ca_n_overlay_roots": ca["n_overlay_roots"],
        "cb_n_overlay_roots": cb["n_overlay_roots"],
        "ca_n_layer_roots": ca["n_layer_roots"],
        "cb_n_layer_roots": cb["n_layer_roots"],
        "raw": {"c0": c0, "ca": ca, "cb": cb},
    }
    d = {"a_opened": a_opened, "b_opened": b_opened,
         "a_survived": bool(a_survived) if a_opened else False,
         "both_overlays_coexist": bool(a_opened and b_opened and a_survived),
         "n_overlays_after_b": cb["n_overlay_roots"],
         "new_overlay_tids_b": sorted(b_new),
         "b_blocked_a": bool(a_opened and b_opened and not a_survived),
         "a_opened_by": a_name, "b_opened_by": b_name}
    # ⚠️⚠️ 仪器自身的免疫针：`a_opened` 为真时 **A 到底是谁**必须被记下来。
    #    第一版之所以能一路错到底，正是因为「A 是谁」没进读数 ⇒
    #    读的人无从发现它测的是常驻层。
    assert a_opened or not a_new, "a_opened 与 a_new_keys 自相矛盾"
    assert (not a_opened) or rec["a_new_keys"], "a_opened=True 却没有 A 的身份"
    bad = set(d) - DERIVED_KEYS
    assert not bad, f"派生量冒出未登记的键: {bad}"
    rec["der"] = d
    reset()
    return rec


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "forbidden_tids": list(FORBIDDEN_TIDS),
       "openers": [n for n, _ in OPENERS], "design_ok": {}, "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n_audio = page.locator('button[aria-label="音频"]').count()
    if n_audio == 0:
        page.wait_for_timeout(8000)
        n_audio = page.locator('button[aria-label="音频"]').count()
    rec = {"rep": rep, "n_audio_rail_button": n_audio,
           "n_nodes": page.locator(".react-flow__node").count(), "pairs": []}
    out["runs"].append(rec)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    # 先单独量一遍「每个开层器自己能不能开出来」（开层器坏掉就别测它的配对）
    solo = []
    for nm, op in OPENERS:
        reset()
        c0 = census(f"solo/{nm}/before")
        r = op()
        page.wait_for_timeout(OPEN_WAIT)
        c1 = census(f"solo/{nm}/after")
        solo.append({"name": nm, "open": r, "n_overlay_roots": c1["n_overlay_roots"],
                     "n_layer_roots": c1["n_layer_roots"],
                     "overlay_ids": [o["tid"] or o["role"] or o["tag"]
                                     for o in c1["overlays"]]})
        print(f"  solo [{nm}] 开={bool(r.get('ok'))} "
              f"浮层 {c0['n_overlay_roots']}->{c1['n_overlay_roots']} "
              f"{[o['tid'] or o['role'] for o in c1['overlays']]}", flush=True)
        reset()
    rec["solo"] = solo
    dump(out)
    openable = [nm for nm, s in zip([n for n, _ in OPENERS], solo)
                if s["open"].get("ok") and s["n_overlay_roots"] > 0]
    print(f"  可用开层器: {openable}", flush=True)

    by_name = dict(OPENERS)
    for a in openable:
        for b in openable:
            if a == b:
                continue
            pr = pair_test(a, by_name[a], b, by_name[b])
            rec["pairs"].append(pr)
            dump(out)   # ⚠️ 每个配对落一次盘
            d = pr["der"]
            print(f"  [{a} → {b}] A开={d['a_opened']} B开={d['b_opened']} "
                  f"A还活着={d['a_survived']} 浮层数={pr['cb_n_overlay_roots']} "
                  f"A={pr['a_new_keys']} B={pr['b_new_keys']} "
                  f"cb={pr['cb_keys']}", flush=True)

    # ── 阳性对照：注入一个合成浮层，`n_overlay_roots` 必须真的 +1 ────────
    reset()
    cb = census("pc/before")
    ev(FIXTURE_ADD_JS)
    ca = census("pc/after")
    ev(FIXTURE_DEL_JS)
    rec["positive_control"] = {
        "n_before": cb["n_overlay_roots"], "n_after": ca["n_overlay_roots"],
        "delta": ca["n_overlay_roots"] - cb["n_overlay_roots"],
        "leak_check": ev(FIXTURE_DEL_JS)}
    dump(out)
    print(f"  阳性对照 浮层 {cb['n_overlay_roots']}->{ca['n_overlay_roots']} "
          f"(Δ{rec['positive_control']['delta']}) "
          f"残留={rec['positive_control']['leak_check']}", flush=True)
    reset()

# ── 汇总（派生层：与上面的原始记录分开）────────────────────────────────
runs_ok = [r for r in out["runs"] if not r.get("skipped")]
all_pairs = [p for r in runs_ok for p in r["pairs"]]
pcs = [r.get("positive_control", {}) for r in runs_ok]
both = [p for p in all_pairs if p["der"]["both_overlays_coexist"]]
blocked = [p for p in all_pairs if p["der"]["b_blocked_a"]]
both_opened = [p for p in all_pairs if p["der"]["a_opened"] and p["der"]["b_opened"]]

out["summary"] = {
    "reps": len(out["runs"]), "runs_ok": len(runs_ok),
    "n_openers": len(OPENERS), "n_pairs_tested": len(all_pairs),
    "n_pairs_both_opened": len(both_opened),
    "n_pairs_BOTH_OVERLAYS_COEXIST": len(both),
    "n_pairs_b_blocked_a": len(blocked),
    "n_pairs_a_not_survived": sum(1 for p in all_pairs
                                  if p["der"]["a_opened"] and not p["der"]["a_survived"]),
    # ⭐ 仪器自身的阴阳两面分别有多少 —— 全是同一面就说明它在恒真
    "n_survived_true": sum(1 for p in all_pairs if p["der"]["a_survived"]),
    "n_survived_false": sum(1 for p in both_opened
                            if not p["der"]["a_survived"]),
    "surviving_a_ids": sorted({k for p in all_pairs
                               if p["der"]["a_survived"]
                               for k in p["a_new_keys"]}),
    "max_n_overlay_roots_seen": max(
        [p["der"]["n_overlays_after_b"] for p in all_pairs] or [0]),
    "coexisting_pairs": [f"{p['a']}→{p['b']}" for p in both],
    "positive_control_delta": [pc.get("delta") for pc in pcs],
    "fixture_leak_gone": [pc.get("leak_check") for pc in pcs],
}
out["design_ok"] = {
    "pairs_ok": len(both_opened) >= 4,   # 至少 4 个配对两段都开得出来
    # ⭐ 阳性对照必须真的 +1，否则「没并存」是瞎的
    "positive_control_ok": all((pc.get("delta") or 0) >= 1 for pc in pcs) and bool(pcs),
    "no_fixture_leak_ok": all(pc.get("leak_check") == 0 for pc in pcs) and bool(pcs),
    # ⭐⭐ 仪器自身的**阴阳对照**：`a_survived` 必须**两个答案都出现过**。
    #    937 第一版它恒为 True（把常驻层当成了 A）⇒ 一门都没有 ⇒
    #    探针打出「32/32 全部并存」这种与真相相反的汇总还没人拦。
    #    ⇒ 这道门是**冲着「结论看起来整齐」去的**：越整齐越要验。
    "instrument_discriminates_ok": (
        out["summary"]["n_survived_true"] > 0
        and out["summary"]["n_survived_false"] > 0),
}
dump(out)

print("\n===== 937 汇总 =====", flush=True)
for k, v in out["summary"].items():
    print(f"  {k}: {v}")
print(f"  design_ok: {out['design_ok']}")
