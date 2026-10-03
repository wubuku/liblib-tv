#!/usr/bin/env python3
r"""batch 941 源站探针（**纯诊断 / 自我证伪**）：**940 那两条「冷启动不可达」是真的吗？**

## 941 的由来：940 的结论可能是**我自己判据的缺陷**

940 对源站 5 个层各量了两列：开层那一瞬间焦点在哪 / 冷启动 Tab 第几步进层。
其中**三行**是 `wrapped = True`（走满 160 步、落点标记第二次出现 = 绕了一圈仍未到）
⇒ 940 据此写下「搜索层 / 缩放菜单 / 右键菜单**冷启动不可达**」。

⚠️⚠️ **复查 940 的源码，发现它的「进层」判据有个真缺陷**：

```python
# 940 的 STEP_JS：只记**最近**的那个 LAYER_SEL 祖先，找到就 break
layerTid = p.getAttribute('data-testid') || ('role:' + ...);
...
# 940 的判定
if target_layer_tid and st["layer_tid"] == target_layer_tid and first_in is None:
```

⚠️ `target_layer_tid` 取自**开层焦点**的最近祖先。实测搜索层开层后新增**两个**层
（`canvas-feature-panel` + `canvas-search-panel`），开层焦点（ASIDE 本体）的最近
祖先是 `canvas-feature-panel` ⇒ `target = canvas-feature-panel`。

⇒ ⚠️ **而冷启动后落在 `canvas-search-panel` 内部**的输入框 / 分类钮 / 结果钮，
它们**最近**的 `LAYER_SEL` 祖先是 `canvas-search-panel`，**不是** `canvas-feature-panel`
⇒ `layer_tid != target` ⇒ **被判成「没进」** ⇒ 假阴性。

⇒ ⭐⭐ **941 就是去证伪它的**：同一份游走，**三个判据并排**。

## ⭐ 三判据并排（这一批的正题）

| 判据 | 定义 | 它能分出什么 |
| --- | --- | --- |
| **A（940 用的）** | `最近 LAYER_SEL 祖先的 testid === target` | 940 的原判据 |
| **B（祖先包含）** | `!!el.closest('[data-testid="TARGET"]')` | 「落点在**这一层子树内**」 |
| **C（936 的口径）** | `!!el.closest('[data-b941-seed]')` | 936 的 `in_seed`（**打标记**） |

⚠️ **A 与 B 的差别就是本批要量的东西**：
A 要求「最近祖先**恰好**是它」，B 只要求「祖先链里**有**它」。

⇒ ⭐ **判决**：若 B 或 C 有命中而 A 没有 ⇒ **940 的 `wrapped` 被证伪**。

### ⭐⭐ 同时把「落点到底在哪一层」变成**读数**而不是推断

每一步记**完整的 `LAYER_SEL` 祖先链**（所有匹配的祖先，**不只最近那个**，
按由近到远排序）⇒ 事后能从读数直接看出焦点落在哪几层里，
**不必**再回头猜「为什么 A 没命中」。

⚠️ 这一条是 937 的教训（`a_survived` 恒真 ⇒ 汇将与真相相反）：
**「A 到底是谁」必须进读数**，否则读的人无从发现它测错了对象。

## ⚠️⚠️ 顺带订正 940 基线里的一处**措辞错误**

940 的基线写「936 的 `in_seed` 判据用的是 `LAYER_SEL` 的 `closest` 形式」⇒ **错**。
936 的源码里是**两个分开的**判据：

| 936 的字段 | 定义 |
| --- | --- |
| `focus_in_layer` | `!!a.closest(LAYER_SEL)`（**宽泛**） |
| `in_seed` | `!!a.closest('[data-b936-seed]')`（**精确标记**） |

⇒ 而 936 报的「层内步 20/轮」用的是 **`in_seed`**（精确那个）
⇒ ⚠️ 也就是说：**936 与 940 的矛盾不能用「口径宽窄」解释** ——
两个口径都精确，只是 A 这个判据本身写错了。
⇒ 941 会把这一点一起钉死（并排跑 A/B/C 三列）。

## 只测两个层（940 报 `wrapped` 且**读数稳定**的那两个）

- `canvas-feature-panel`（顶栏·搜索）—— 940 说 `wrapped=True`
- `canvas-context-menu`（画布右键菜单）—— 940 说 `wrapped=True`
- 顺带带一个 **940 说「第 1 次可达」**的层当**阳性对照**：
  `generation-history-panel`（顶栏·生成历史）
  ⇒ ⚠️ **阳性对照必须有**：只有一个判别器时，三个判据的读数都可能是恒真的。

## 游走预算

`B_TAB_CAP = 160`，**走满**（不因进层就停，845 栽过）。
结局三分（承 940）：`reached` / `wrapped`（落点标记第二次出现）/ `capped`（按满）。

## ⚠️ 阴阳对照门（940 刚踩了四版，所以这次先设计对）

**两个答案必须来自两个不同的集合**（940 的教训）：
- 判据 A 必须在**至少一个层**上给出与 B/C **不同**的答案
  （若三个判据在所有层上答案都相同 ⇒ 本批**测不出差别** ⇒ 如实记 `False`）
- 阳性对照层必须 `reached`（否则「三判据一致」是恒真的）

## 计费边界

只按 `Tab` + 各开层器那一次点击；`FORBIDDEN_TIDS` 守卫拦在 `mouse.click` 之前。
**绝不**点生成/发送/购买/充值；**不点任何节点**。
⚠️ 游走**一定会路过**计费入口（940 实测第 9 站），但**路过 ≠ 点击** ⇒ 记进读数。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload`。
唯一 DOM 改动：打/清 `data-b941-i`（身份标记）与 `data-b941-seed`（种子标记）。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe941_layer_identity_probe_src.py
"""

import json

OUT = "/tmp/b941-src-layer-identity.json"
REPS = 2

OPEN_WAIT = 1400
RESET_WAIT = 500
SETTLE = 200
B_TAB_CAP = 160

# ⛔ 计费入口（承 937/939/940）：**结构上禁止点击**
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger", "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')
assert LAYER_SEL == (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]'
), "LAYER_SEL 与判据那份漂移了（936 栽过：同一判据写两套定义）"

MARK_ATTR = "data-b941-i"
SEED_ATTR = "data-b941-seed"
B939_SEL = ("a[href], area[href], button, input, select, textarea, "
            "iframe, object, embed, summary, audio[controls], video[controls], "
            "[contenteditable], [tabindex]")

# 940 报 `wrapped` 的两个（读数稳定），+ 一个 940 说「第 1 次可达」的正对照
TARGETS = [
    ("顶栏·搜索", "canvas-panel-launcher", 0, "canvas-feature-panel"),
    ("画布右键菜单", "(空画布右键)", -1, "canvas-context-menu"),
    ("顶栏·生成历史", "canvas-panel-launcher", 1, "generation-history-panel"),
    # ⚠️⚠️ 第一版**漏了这个层**（940 报它 `wrapped=True`，却没被证伪）
    #    ⇒ 那是**取样缺口**，不是「它大概也一样」—— 补上。
    ("缩放菜单", "canvas-zoom-percent", 0, "canvas-zoom-menu"),
]

RAW_KEYS = frozenset({
    "k", "ti_before", "mark", "tag", "tid", "in_node", "is_billing",
    "nearest_ancestor_tid", "ancestor_chain", "in_target_closest",
    "in_seed_closest", "step", "n_new_layers", "new_layers", "target_tid",
    "target_src", "focus_at_open", "open_result", "tab_log",
})
DERIVED_KEYS = frozenset({
    "k_stable", "a_first_hit", "b_first_hit", "c_first_hit",
    "a_reached", "b_reached", "c_reached", "a_wrapped", "b_wrapped",
    "c_wrapped", "a_b_differ", "criteria_disagree", "positive_control_ok",
    "yin_yang_ok", "n_steps", "billing_steps", "a_false_negative",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"

# ── 枚举（只为打身份标记；不过滤，见 940 的教训）──
INDEX_JS = """([sel, markAttr, seedAttr]) => {
  for (const old of document.querySelectorAll('[' + markAttr + ']')) {
    old.removeAttribute(markAttr);
  }
  for (const old of document.querySelectorAll('[' + seedAttr + ']')) {
    old.removeAttribute(seedAttr);
  }
  const live = [];
  for (const e of document.querySelectorAll(sel)) {
    if (e.disabled) continue;
    const ti = e.getAttribute('tabindex');
    if (ti !== null && Number(ti) < 0) continue;
    if (e.getClientRects().length === 0) continue;
    live.push(e);
  }
  for (let i = 0; i < live.length; i++) live[i].setAttribute(markAttr, String(i));
  return {k: live.length, ti_before: Object.create(null)};
}"""

# ⭐⭐ 本批的核心读数：**完整的 LAYER_SEL 祖先链**（不只最近那个）
STEP_JS = """([markAttr, layerSel, targetTid, seedAttr, forbiddenTids]) => {
  const a = document.activeElement;
  if (!a || a === document.body) {
    return {mark: -1, tag: 'BODY', tid: '', in_node: false, is_billing: false,
            nearest_ancestor_tid: null, ancestor_chain: [],
            in_target_closest: false, in_seed_closest: false};
  }
  // ⭐ 祖先链：**所有**匹配的 LAYER_SEL 祖先，由近到远（不是只取最近那个）
  const chain = [];
  let inNode = false, isBilling = false;
  for (let p = a; p && p !== document.body; p = p.parentElement) {
    if (p.matches && p.matches(layerSel)) {
      chain.push(p.getAttribute('data-testid')
                 || ('role:' + (p.getAttribute('role') || p.tagName)));
    }
    if (!inNode && p.classList && p.classList.contains('react-flow__node')) inNode = true;
    for (const b of forbiddenTids) {
      if (p.getAttribute && p.getAttribute('data-testid') === b) isBilling = true;
    }
  }
  const tSel = '[data-testid="' + targetTid + '"]';
  return {
    mark: a.hasAttribute(markAttr) ? Number(a.getAttribute(markAttr)) : null,
    tag: a.tagName, tid: a.getAttribute('data-testid') || '',
    in_node: inNode, is_billing: isBilling,
    nearest_ancestor_tid: chain.length ? chain[0] : null,
    ancestor_chain: chain,
    // B 判据：祖先链里**有** target（用 closest，与 940 的「恰好等于」不同）
    in_target_closest: !!a.closest(tSel),
    // C 判据：936 的口径（打标记）
    in_seed_closest: !!a.closest('[' + seedAttr + ']'),
  };
}"""

MARK_SEED_JS = """([targetTid, seedAttr]) => {
  const e = document.querySelector('[data-testid="' + targetTid + '"]');
  if (!e) return {ok: false, why: 'DOM 里没有 ' + targetTid};
  e.setAttribute(seedAttr, '1');
  return {ok: document.querySelectorAll('[' + seedAttr + ']').length === 1,
          tag: e.tagName};
}"""

BLUR_ALL_JS = """() => {
  const a = document.activeElement;
  if (a && a.blur) a.blur();
  return document.activeElement === document.body;
}"""


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def guard(al, tid):
    if tid in FORBIDDEN_TIDS:
        return f"护栏拦下计费入口 testid={tid!r}"
    t = (al or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        return f"护栏拦下付费动作 {t!r}"
    return None


def click_trigger(tid, idx=0):
    pt = page.evaluate("""([tid, idx]) => {
      const c = [...document.querySelectorAll('[data-testid="' + tid + '"]')];
      const e = c[idx];
      if (!e) return null;
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return null;
      return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
              al: e.getAttribute('aria-label') || ''};
    }""", [tid, idx])
    if not pt:
        return {"ok": False, "why": f"触发器 {tid}[{idx}] 不可点"}
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
    hit = page.evaluate("""([x, y]) => {
      const e = document.elementFromPoint(x, y);
      if (!e) return null;
      const b = e.closest('[data-testid]');
      return {tid: b ? b.getAttribute('data-testid') : '',
              al: e.getAttribute('aria-label') || ''};
    }""", [spot["x"], spot["y"]])
    blocked = guard((hit or {}).get("al"), (hit or {}).get("tid"))
    if blocked:
        return {"ok": False, "why": blocked}
    page.mouse.click(spot["x"], spot["y"], button="right")
    return {"ok": True, "trigger": {"tid": "(空画布右键)",
                                    "al": f"@{spot['x']},{spot['y']}"}}


def open_layer(trigger_tid, idx):
    if trigger_tid == "(空画布右键)":
        return open_context_menu()
    return click_trigger(trigger_tid, idx)


def walk(target_tid):
    """冷启动 + 按 Tab 走满预算，**三判据并排**记录。"""
    ev(BLUR_ALL_JS)
    log, seen = [], set()
    billing, first = [], {"A": None, "B": None, "C": None}
    wrapped = False
    for i in range(1, B_TAB_CAP + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        st = ev(STEP_JS, [MARK_ATTR, LAYER_SEL, target_tid, SEED_ATTR,
                          list(FORBIDDEN_TIDS)])
        unknown = set(st) - RAW_KEYS
        assert not unknown, f"轨迹读数冒出未登记的原始键: {unknown}"
        log.append(dict(st, step=i))
        if st["is_billing"]:
            billing.append(i)
        # ⭐ 三判据分别记「第一次命中」
        if first["A"] is None and st["nearest_ancestor_tid"] == target_tid:
            first["A"] = i
        if first["B"] is None and st["in_target_closest"]:
            first["B"] = i
        if first["C"] is None and st["in_seed_closest"]:
            first["C"] = i
        if first["A"] is not None and first["B"] is not None and first["C"] is not None:
            break
        m = st["mark"]
        if m is None:
            continue
        if m in seen:
            wrapped = True
            break
        seen.add(m)
    capped = all(v is None for v in first.values()) and not wrapped
    d = {"a_first_hit": first["A"], "b_first_hit": first["B"],
         "c_first_hit": first["C"],
         "a_reached": first["A"] is not None, "b_reached": first["B"] is not None,
         "c_reached": first["C"] is not None, "a_wrapped": wrapped,
         "b_wrapped": wrapped, "c_wrapped": wrapped,
         "n_steps": len(log), "billing_steps": billing[:6]}
    # ⭐⭐ 本批正题：**A 与 B 给出不同答案** ⇒ 940 的 `wrapped` 是假阴性
    d["a_b_differ"] = (first["A"] is None) != (first["B"] is None)
    d["a_false_negative"] = (first["A"] is None and first["B"] is not None)
    bad = set(d) - DERIVED_KEYS
    assert not bad, f"派生量冒出未登记的键: {bad}"
    return log, d


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "b939_sel": B939_SEL, "target_list": TARGETS,
       "b_tab_cap": B_TAB_CAP, "forbidden_tids": list(FORBIDDEN_TIDS),
       "design_ok": {}, "runs": []}


def boot():
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    return n


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep}
    out["runs"].append(rec)
    for name, trig, idx, target in TARGETS:
        n = boot()
        if n == 0:
            rec.setdefault("layers", []).append(
                {"name": name, "skipped": "登录态没命中"})
            continue
        ev(INDEX_JS, [B939_SEL, MARK_ATTR, SEED_ATTR])
        ro = open_layer(trig, idx)
        page.wait_for_timeout(OPEN_WAIT)
        seed = ev(MARK_SEED_JS, [target, SEED_ATTR])
        f_open = ev(STEP_JS, [MARK_ATTR, LAYER_SEL, target, SEED_ATTR,
                              list(FORBIDDEN_TIDS)])
        log, d = walk(target)
        rec.setdefault("layers", []).append({
            "name": name, "target_tid": target, "target_src": "探针指定的层",
            "open_result": ro, "seed_mark": seed, "focus_at_open": f_open,
            "tab_log": log[:220], "der": d})
        print(f"  [{name}] target={target} seed={seed.get('ok')} "
              f"开层焦点 mark={f_open['mark']} chain={f_open['ancestor_chain']}")
        print(f"       A(最近祖先==target)={d['a_first_hit']} "
              f"B(closest 含 target)={d['b_first_hit']} "
              f"C(seed 标记)={d['c_first_hit']} "
              f"⇒ A 是假阴性? {d['a_false_negative']}  步数={d['n_steps']}", flush=True)
        dump(out)

runs = [r for r in out["runs"] if r.get("layers")]
out["summary"] = {
    "n_reps_measured": len(runs),
    "layers": [[{"name": l["name"], "target": l.get("target_tid"),
                 "a": l["der"]["a_first_hit"], "b": l["der"]["b_first_hit"],
                 "c": l["der"]["c_first_hit"],
                 "a_false_negative": l["der"]["a_false_negative"],
                 "n_steps": l["der"]["n_steps"],
                 "focus_at_open_chain": (l.get("focus_at_open") or {}).get("ancestor_chain")}
                for l in r["layers"] if l.get("der")] for r in runs],
}
# ⭐ 阴阳对照门（940 刚踩了四版 ⇒ 这次先设计对）
_a = out["summary"]["layers"]
out["design_ok"] = {
    "reps_measured_ok": len(runs) == REPS,
    "measured_ok": all(l.get("der") for r in runs for l in r["layers"]),
    # ⭐ 阳性对照：940 说「第 1 次可达」的层，A/B/C 都必须 reached
    "positive_control_ok": all(
        any(l["name"] == "顶栏·生成历史" and l["a"] is not None
            and l["b"] is not None and l["c"] is not None for l in rep)
        for rep in _a),
    # ⭐ 判别力：**至少一个层上 A 与 B 给出不同答案**
    #    （若三者处处相同 ⇒ 本批测不出差别 ⇒ 如实 False，不许调门凑绿）
    "criteria_disagree_ok": all(any(l["a_false_negative"] for l in rep) for rep in _a),
    "reps_identical_ok": (
        len(_a) == 2
        and [(l["name"], l["a"], l["b"], l["c"]) for l in _a[0]]
        == [(l["name"], l["a"], l["b"], l["c"]) for l in _a[1]]),
}
out["design_ok"]["yin_yang_ok"] = (out["design_ok"]["positive_control_ok"]
                                  and out["design_ok"]["criteria_disagree_ok"])
dump(out)
print(json.dumps({"design_ok": out["design_ok"], "summary": out["summary"]},
                 ensure_ascii=False, indent=2), flush=True)
print(f"OUT={OUT}", flush=True)
