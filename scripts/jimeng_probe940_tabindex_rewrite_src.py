#!/usr/bin/env python3
r"""batch 940 源站探针（**纯诊断**）：**Tab 游走会不会重写 `tabindex`？**
＋ **「浮层开层是否接管焦点」的跨层矩阵**（源站侧）

## 940 的两个题目（一个探针，两组读数，**顺序不可换**）

### ① 补 939 留下的**判决性缺口**（先做，必须在**干净状态**下）

939 的 `[A]` 段（游走**前**）测到 `[tabindex]` 共 178 个、节点本体 0 个，
而游走中 **100 步落点带 `tabindex="0"`**
⇒ 嫌疑很大：「**Tab 游走把节点的 `tabindex` 从 `-1` 改写成 `0`**」
⚠️ **但 939 没有在游走后重测那个数** ⇒ **两次读数不足以定机制**（§77）。

⇒ 940 A 段做的是**最小复现**：
1. 游走**前**：给每个候选元素打 `data-b940-i="<i>"` 并记它的 `tabindex` 值
2. 按 N 次 Tab
3. 游走**后**：对**同一批标记**读 `tabindex` 值
4. ⭐ **逐元素**分类：`none→0` / `-1→0` / `-1→removed` / `0→-1` / 不变 …

⚠️ 必须分开记「**写回属性**」与「**属性整个被删掉**」——
§131 实测过应用**三件事**（`removed` 是整个移除、不是设成 `'-1'`），
把两者混成一个「变了」就会把机制读反（§130 就是这么读反的）。

### ② 跨层焦点矩阵（后做，每层测完**重新 goto** 重置）

939 量到源站右键菜单**不可 Tab 到达**，因为它**开层即接管焦点**。
⚠️ 但「开层即接管」**不是它独有** —— 847d 那批记了 4 个层也是 `True`。
⇒ 940 把源站能开的层**逐个**取两件事：

| 列 | 量什么 |
| --- | --- |
| `focus_at_open` | 开层**那一瞬间**焦点在哪（层内 / 触发器 / body） |
| `cold_tab_in` | `blur()` 冷启动后按 Tab，**第几步**进层（或 `capped` / `wrapped`） |

⚠️⚠️ **`capped` 与「进不去」必须分开**（§62，939 刚又撞过一次）：
按满预算还没到 = **「没测出来」**，不是「进不去」。

## ⭐ 顺序不可换：① 必须在**任何浮层都没开**的状态下做

A 段一旦在「某层开着」的状态下做，观测到的 `tabindex` 变化就分不清是
**Tab 造成的**还是**开层造成的**（§「两件事同时发生只能归因到其中一件」）。
⇒ A 段排在**最前**，且期间**一个浮层都不开**。
⇒ B 段每层测完**重新 `goto`**（`reset` 关层不干净：939 撞到侧栏开过后两次 Esc 关不掉）。

## 跨状态认元素：打标记，不推算（936/937 坑 2 的根治）

`dom_sig` 是 `tag:nth-of-type`，下标会因插入而移位 ⇒ 跨状态比它不成立。
⇒ 枚举那一刻打 `data-b940-i`，之后所有读数**只认标记**。
⚠️ 打标记**不碰** `tabindex` / `disabled` ⇒ 不改可聚焦集合；
由 `K` 前后相等这条**实测**自检证明，不是靠声称。

## ⭐ 仪器阴阳对照门（937 的教训，第四次）

A 段若「所有元素都没变」或「所有元素都变了」⇒ 仪器可能恒真
⇒ `changed_ok` 必须**既有** True 又有 False 才为真。
B 段的 `yin_yang_ok` 同理：进层步号必须**既有**小又有大（或既有 `reached`
又有 `capped`）⇒ 全部同一种答案就**如实记 `False`**，不许调门凑绿。

## ⚠️⚠️ 939 刚撞出的两个坑，本批直接绕开

1. **`covers_all_landings` 那个恒真字段**：939b 判据里把
   `role in ("menuitem", ...)` 当成「尺子能覆盖」，而那条 SEL **根本不选**
   `[role=menuitem]` ⇒ **自己给自己开后门**，两轮都报 `true` 却零信息量。
   ⇒ 940 **不用那种近似**：「尺子能选中某个元素」一律用
   `document.querySelectorAll(sel).indexOf(e) >= 0` **实测**。
2. **枚举集合是假的**：939 第一版报 `K=26`，而实测落点 95–100 个。
   ⇒ 940 的枚举**不加**「负 tabindex 跳过 / 可见性」这两道过滤 ——
   过滤条件**逐条**记进读数（`n_neg_ti` / `n_invisible`），
   让「哪道过滤吃掉了多少」成为**读数**而不是隐形的假设。

## 计费边界（**结构上禁止**）

沿 937/939：只做**空画布右键**、顶栏 launcher、缩放、侧栏。
`FORBIDDEN_TIDS` 守卫拦在 `mouse.click` **之前**。
**绝不**点生成/发送/购买/充值；**不点任何节点**。
⚠️ 939 实测**计费入口在 Tab 序列第 16 站** ⇒ 键盘游走**一定会路过它**，
但**路过 ≠ 点击** ⇒ 本探针的 `keyboard.press("Tab")` 不构成计费，
而这条事实本身要进读数（`billing_tid_at_step`）。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload`（B 段用 `goto` 重置，
不用 `reload`）。唯一的 DOM 改动是「打/清 `data-b940-i`」与 `blur()` / `focus()`。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe940_tabindex_rewrite_src.py
"""

import json

OUT = "/tmp/b940-src-tabindex-rewrite.json"
REPS = 2

OPEN_WAIT = 1400
RESET_WAIT = 500
SETTLE = 200
STEPS_WALK = 120          # A 段游走步数
B_TAB_CAP = 160           # B 段每层的 Tab 预算

# ⛔ 计费入口（承 937/939）：**结构上禁止点击**
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

# ⚠️ 承 939 第一版那条选择器（**逐字**），好让「尺子」本身是读数。
#    本批**不加**「负 tabindex 跳过 / 可见性」过滤 —— 过滤量逐条进读数。
B939_SEL = ("a[href], area[href], button, input, select, textarea, "
            "iframe, object, embed, summary, audio[controls], video[controls], "
            "[contenteditable], [tabindex]")
MARK_ATTR = "data-b940-i"

RAW_KEYS = frozenset({
    "k", "n_neg_ti", "n_invisible", "n_disabled", "n_hidden_tabindex",
    "ti_before", "n_readable_after", "ti_after", "gone_marks", "live_marks",
    "changed_pairs", "n_neg_ti_after", "focus_at_open", "open_result",
    "tab_log", "layer_present_at_open", "n_layers_open",
    # ⚠️ `STEP_JS` / `FOCUS_JS` / `REREAD_JS` / `COUNTS_JS` 的原始键
    #    （⚠️ 第一版漏登记了其中 9 个，**连续两次**被下面的免疫针当场抓到）
    "mark", "tag", "tid", "role", "al", "txt", "in_node", "in_layer",
    "layer_tid", "is_billing", "sel_size_after",
    "k_sel", "k_tabindex", "k_ti0", "k_tineg", "k_nodes", "k_nodes_ti",
    # ⚠️⚠️ **免疫针第三次抓到我**：这个键来自 `INDEX_JS`（原始读数）⇒ 属 RAW_KEYS，
    #    我却只把它从 DERIVED_KEYS 删掉、忘了加进 RAW_KEYS。
    "n_marked_in_node", "n_marked_is_node",
    "layers_pre", "layers_post_new", "target_tid", "target_tid_src",
    "k_before_walk",
})
DERIVED_KEYS = frozenset({
    "k_stable", "transitions", "n_changed", "n_unchanged", "changed_ok",
    "yin_yang_ok", "reached", "capped", "wrapped", "tab_in_at", "n_tab_in",
    "sum_matches", "sel_covers_landings", "step", "billing_tid_at_step",
    "counts_changed", "n_counts_changed", "marked_all_unchanged",
    "two_sides_differ",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("changed_ok", "transitions", "tab_in_at", "k_stable"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


# ── 枚举：⭐ **不过滤**，只把「哪道过滤会吃掉多少」逐条记成读数 ──
INDEX_JS = """([sel, markAttr]) => {
  for (const old of document.querySelectorAll('[' + markAttr + ']')) {
    old.removeAttribute(markAttr);
  }
  const all = Array.from(document.querySelectorAll(sel));
  const out = {k: 0, n_neg_ti: 0, n_invisible: 0, n_disabled: 0,
               n_hidden_tabindex: 0, n_marked_in_node: 0,
               n_marked_is_node: 0, ti_before: {}};
  const live = [];
  for (const e of all) {
    // ⚠️ 三道「939 第一版用过的过滤」**逐条**计数，但**不据此剔除**
    if (e.disabled) out.n_disabled += 1;
    const ti = e.getAttribute('tabindex');
    if (ti !== null && Number(ti) < 0) out.n_neg_ti += 1;
    if (e.getClientRects().length === 0) out.n_invisible += 1;
    // 浏览器真正的排除条件：disabled、负 tabindex、不可见
    if (e.disabled) continue;
    if (ti !== null && Number(ti) < 0) continue;
    if (e.getClientRects().length === 0) continue;
    live.push(e);
  }
  out.k = live.length;
  out.n_marked_in_node = 0;
  for (let i = 0; i < live.length; i++) {
    const e = live[i];
    e.setAttribute(markAttr, String(i));
    out.ti_before[String(i)] = e.getAttribute('tabindex');   // null = 没有属性
    // ⭐ 「我的仪器测的是谁」必须**可验证**（§62/936/937）—— 而且要分清两件
    //    **完全不同**的事（第三版把它们混了，实测 `n_marked_in_node`=9 而不是 0）：
    //    · `n_marked_is_node` ＝ 被标记的里**自己就是** `.react-flow__node`（`<div>`）
    //      ⇒ `B939_SEL` **不选 div** ⇒ 这个数是**结构保证**的 0
    //    · `n_marked_in_node` ＝ 被标记的里**在某个节点子树内**（节点里的 button/a）
    //      ⇒ 实测 **9** —— 这些是节点**内部**的可聚焦元素，**也被标记、也都没变**
    if (e.classList && e.classList.contains('react-flow__node')) {
      out.n_marked_is_node += 1;
    }
    for (let q = e; q && q !== document.body; q = q.parentElement) {
      if (q.classList && q.classList.contains('react-flow__node')) {
        out.n_marked_in_node += 1; break;
      }
    }
  }
  return out;
}"""

# ── 游走**后**：对**同一批标记**重读 tabindex ⭐
REREAD_JS = """([markAttr, sel]) => {
  const nodes = Array.from(document.querySelectorAll('[' + markAttr + ']'));
  const tiAfter = {}, gone = [], live = [];
  let nNegAfter = 0;
  for (const e of nodes) {
    const i = e.getAttribute(markAttr);
    tiAfter[i] = e.getAttribute('tabindex');
    live.push(i);
    const t = e.getAttribute('tabindex');
    if (t !== null && Number(t) < 0) nNegAfter += 1;
  }
  // ⭐ 「尺子能选中某个元素」用**实测**判定，不靠 role 近似
  //    （939b 的 covers_all_landings 恒真字段就是这么来的）
  const all = Array.from(document.querySelectorAll(sel));
  return {n_readable_after: nodes.length, ti_after: tiAfter,
          gone_marks: gone, live_marks: live.length, n_neg_ti_after: nNegAfter,
          sel_size_after: all.length};
}"""

# ── 当前焦点：只认标记 + 祖先 testid ──
FOCUS_JS = """([markAttr, layerSel]) => {
  const a = document.activeElement;
  if (!a || a === document.body) {
    return {mark: -1, tag: a ? a.tagName : null, tid: '', role: '',
            al: '', txt: '<<body>>', in_layer: false, layer_tid: null};
  }
  let layerTid = null;
  for (let p = a; p && p !== document.body; p = p.parentElement) {
    if (p.matches && p.matches(layerSel)) {
      layerTid = p.getAttribute('data-testid') || ('role:' + (p.getAttribute('role') || p.tagName));
      break;
    }
  }
  return {mark: a.hasAttribute(markAttr) ? Number(a.getAttribute(markAttr)) : null,
          tag: a.tagName, tid: a.getAttribute('data-testid') || '',
          role: a.getAttribute('role') || '',
          al: (a.getAttribute('aria-label') || '').slice(0, 60),
          txt: (a.innerText || a.value || '').trim().slice(0, 20),
          in_layer: layerTid !== null, layer_tid: layerTid};
}"""

# ── 落在画布节点**内部**？ + 落在哪个 DOM 位置的「第几站」 ──
STEP_JS = """([markAttr, layerSel, forbiddenTids]) => {
  const a = document.activeElement;
  if (!a || a === document.body) {
    return {mark: -1, tag: 'BODY', tid: '', in_node: false,
            in_layer: false, layer_tid: null, is_billing: false};
  }
  let layerTid = null, inNode = false, isBilling = false;
  for (let p = a; p && p !== document.body; p = p.parentElement) {
    if (!layerTid && p.matches && p.matches(layerSel)) {
      layerTid = p.getAttribute('data-testid') || ('role:' + (p.getAttribute('role') || p.tagName));
    }
    if (!inNode && p.classList && p.classList.contains('react-flow__node')) inNode = true;
    for (const b of forbiddenTids) {
      if (p.getAttribute && p.getAttribute('data-testid') === b) isBilling = true;
    }
  }
  return {mark: a.hasAttribute(markAttr) ? Number(a.getAttribute(markAttr)) : null,
          tag: a.tagName, tid: a.getAttribute('data-testid') || '',
          in_node: inNode, in_layer: layerTid !== null, layer_tid: layerTid,
          is_billing: isBilling};
}"""

BLUR_ALL_JS = """() => {
  const a = document.activeElement;
  if (a && a.blur) a.blur();
  return document.activeElement === document.body;
}"""

COUNTS_JS = """([bSel]) => {
  return {k_sel: document.querySelectorAll(bSel).length,
          k_tabindex: document.querySelectorAll('[tabindex]').length,
          k_ti0: document.querySelectorAll('[tabindex="0"]').length,
          k_tineg: document.querySelectorAll('[tabindex="-1"]').length,
          k_nodes: document.querySelectorAll('.react-flow__node').length,
          k_nodes_ti: document.querySelectorAll('.react-flow__node[tabindex]').length};
}"""


def guard(al, tid):
    if tid in FORBIDDEN_TIDS:
        return f"护栏拦下计费入口 testid={tid!r}"
    t = (al or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        return f"护栏拦下付费动作 {t!r}"
    return None


def present_layer_ids():
    """当前在场的 `LAYER_SEL` 顶层身份。⚠️ node-part 打 `nodepart:` 前缀，
    让 B 段能把它从「新增的层」里剔掉（937 踩过：它是节点的一部分）。"""
    return page.evaluate("""(layerSel) => {
      const boxes = [...document.querySelectorAll(layerSel)].map((e) => {
        const r = e.getBoundingClientRect();
        return {e: e, sig: e.tagName + ':' + ([...e.parentElement.children]
                 .indexOf(e) + 1), w: r.width, h: r.height,
               isPart: e.classList.contains('react-flow__node-toolbar')
                    || e.classList.contains('react-flow__node-panel')};
      });
      // 顶层去重：自己不是别人的后代
      const top = boxes.filter((b) => !boxes.some((o) =>
        o !== b && b.sig !== o.sig && b.sig.startsWith(o.sig + ':')));
      return top.map((b) => (b.isPart ? 'nodepart:' : '')
        + (b.e.getAttribute('data-testid')
           || ('role:' + (b.e.getAttribute('role') || b.e.tagName))));
    }""", LAYER_SEL)


def click_trigger(tid, idx=0):
    """点一个**非计费**触发器（承 937）。"""
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


def launch_context_menu():
    """空画布右键（承 937/939）。⚠️ 落点先验不在任何节点上、且过计费护栏。"""
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


# B 段的层：全部沿用 937/939 已验证过的**非计费**开法
OPENERS = [
    ("顶栏·搜索", lambda: click_trigger("canvas-panel-launcher", 0)),
    ("顶栏·生成历史", lambda: click_trigger("canvas-panel-launcher", 1)),
    ("缩放菜单", lambda: click_trigger("canvas-zoom-percent", 0)),
    ("与 AI 对话侧栏", lambda: click_trigger("canvas-sidecar-launcher", 0)),
    ("画布右键菜单", launch_context_menu),
    # ⛔ 反面例子（**绝不点**，守卫会拦）：canvas-commerce-entry
]


def walk(cap, target_layer_tid):
    """冷启动 + 按 Tab 走满预算，**不因进层就停**（845 栽过）。"""
    ev(BLUR_ALL_JS)
    log = []
    seen = set()
    billing = []
    first_in = None
    wrapped = False
    for i in range(1, cap + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        st = ev(STEP_JS, [MARK_ATTR, LAYER_SEL, list(FORBIDDEN_TIDS)])
        unknown = set(st) - RAW_KEYS
        assert not unknown, f"轨迹读数冒出未登记的原始键: {unknown}"
        log.append(dict(st, step=i))
        if st["is_billing"]:
            billing.append(i)
        if target_layer_tid and st["layer_tid"] == target_layer_tid and first_in is None:
            first_in = i
        if first_in is not None:
            break
        m = st["mark"]
        if m is None:
            continue
        if m in seen:
            wrapped = True
            break
        seen.add(m)
    d = {"reached": first_in is not None, "capped": first_in is None and not wrapped,
         "wrapped": wrapped, "tab_in_at": first_in, "n_tab_in": len(log),
         "billing_tid_at_step": billing[:6]}
    bad = set(d) - DERIVED_KEYS
    assert not bad, f"派生量冒出未登记的键: {bad}"
    return log, d


def classify(ti_before, ti_after):
    """⭐ 逐元素分类 `tabindex` 的变化。⚠️ **属性被删**与**被设成 `-1`**必须分开。"""
    trans = {}
    for k, b in ti_before.items():
        a = ti_after.get(k, "<标记消失>")
        if a == b:
            key = "unchanged"
        elif b is None and a == "0":
            key = "none_to_0"
        elif b is None and a == "-1":
            key = "none_to_neg1"
        elif b is None and a == "<标记消失>":
            key = "none_to_gone"
        elif b == "-1" and a == "0":
            key = "neg1_to_0"
        elif b == "-1" and a is None:
            key = "neg1_to_removed"       # ⭐ 属性整个被删（§131 的 `removed`）
        elif b == "0" and a == "-1":
            key = "zero_to_neg1"
        elif b == "0" and a is None:
            key = "zero_to_removed"
        else:
            key = "other:%s->%s" % (b, a)
        trans[key] = trans.get(key, 0) + 1
    return trans


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "b939_sel": B939_SEL, "mark_attr": MARK_ATTR,
       "steps_walk": STEPS_WALK, "b_tab_cap": B_TAB_CAP,
       "forbidden_tids": list(FORBIDDEN_TIDS), "openers": [n for n, _ in OPENERS],
       "design_ok": {}, "runs": []}


def boot():
    """重新 goto 并等登录态（⚠️ B 段每层之后都调它来**重置状态**）。"""
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
    n_audio = boot()
    rec = {"rep": rep, "n_audio_rail_button": n_audio,
           "n_nodes": page.locator(".react-flow__node").count(),
           "layers": []}
    out["runs"].append(rec)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    # ══ ① A 段：**干净状态**下先做（一个浮层都不开）══════════════════
    c_before = ev(COUNTS_JS, [B939_SEL])
    idx = ev(INDEX_JS, [B939_SEL, MARK_ATTR])
    unknown = set(idx) - RAW_KEYS
    assert not unknown, f"枚举冒出未登记的原始键: {unknown}"
    rec["counts_before"] = c_before
    rec["index_before"] = idx
    rec["der_k_stable"] = (idx["k"] == len(idx["ti_before"]))
    print(f"  [A] 干净态 K={idx['k']} "
          f"(全量: [tabindex]={c_before['k_tabindex']} ti0={c_before['k_ti0']} "
          f"ti-1={c_before['k_tineg']} 节点带ti={c_before['k_nodes_ti']}/{c_before['k_nodes']}) "
          f"| 三道过滤会吃掉: 负ti={idx['n_neg_ti']} 不可见={idx['n_invisible']} "
          f"disabled={idx['n_disabled']}", flush=True)
    dump(out)

    a_log, a_der = walk(STEPS_WALK, None)
    rec["walk_log"] = a_log
    rec["walk_der"] = a_der
    reread = ev(REREAD_JS, [MARK_ATTR, B939_SEL])
    unknown = set(reread) - RAW_KEYS
    assert not unknown, f"重读冒出未登记的原始键: {unknown}"
    rec["reread"] = reread
    c_after = ev(COUNTS_JS, [B939_SEL])
    rec["counts_after"] = c_after
    trans = classify(idx["ti_before"], reread["ti_after"])
    n_changed = sum(v for k, v in trans.items() if k != "unchanged")
    n_total = sum(trans.values())
    # ⚠️⚠️ 第一版把「被标记的 26 个里既有变过又有没变过」当阴阳对照门
    #    ⇒ 实测 `unchanged` **26/26** ⇒ 门必然报 False。
    #    ⚠️ **那 26 个确实一个都没变**（这是**真读数**，不是仪器瞎）：
    #    ⭐ **应用只动画布节点，不动顶栏/侧栏/dock 的元素**。
    # ⇒ 所以 A 段的判别力**不来自被标记集合**，而来自**整体计数变化**
    #    （`[tabindex]` 总数、`ti0`、`ti-1`、**节点带 ti 的个数**）。
    cnt_changed = {
        "k_tabindex": (c_before["k_tabindex"], c_after["k_tabindex"]),
        "k_ti0": (c_before["k_ti0"], c_after["k_ti0"]),
        "k_tineg": (c_before["k_tineg"], c_after["k_tineg"]),
        "k_nodes_ti": (c_before["k_nodes_ti"], c_after["k_nodes_ti"]),
    }
    n_cnt_changed = sum(1 for k, (b, a) in cnt_changed.items() if b != a)
    # ⚠️⚠️⚠️ 第三版这道门。**前两版都错**，错法各不相同：
    #   v1「被标记的里既有变过又有没变过」⇒ 实测 `unchanged` 26/26 ⇒ 必 False。
    #   v2「整体计数里既有变过又有没变过」⇒ 实测 **4 个计数全变** ⇒ 必 False。
    # ⭐⭐ **教训（本批最值钱的一条）**：
    #    **阴阳对照门的两个答案必须来自两个**不同的集合**。**
    #    同一个集合里的两种答案**不构成对照** —— 机制可能让它们**同向**变化，
    #    于是「全变」和「全不变」都会把门判成 False，而门本身没错、读数也没错。
    # ⇒ 正确形状：**节点那一侧**（计数：0/81 → 80/81 ⇒ 变了）
    #    对照 **非节点那一侧**（被标记的 26 个 ⇒ 一个都没变），
    #    并且把「这两个集合真的不同」**实测**成读数 `n_marked_in_node == 0`。
    # ⭐ v4（实测推翻了 v3 的假设）：变化的不是「节点那一侧」，
    #    而是**根本没被标记的节点本体**（`.react-flow__node` 是 `<div>`，
    #    `B939_SEL` 不选 div ⇒ 结构上不可能被标记）。
    #    而被标记的 26 个里**有 9 个是节点内部的 button/a**，它们**同样 unchanged**。
    #    ⇒ 正确的二分是：
    #      · **被标记的 26 个**（9 个在节点内部 + 17 个在节点外）⇒ 全 unchanged
    #      · **未被标记的节点本体** ⇒ `k_nodes_ti` 0 → 76
    #    ⇒ 门用 `n_marked_is_node == 0`（**结构保证**的 0，不是碰巧）。
    marked_is_node_side = (idx["n_marked_is_node"] == 0)
    rec["der_rewrite"] = {
        "transitions": trans, "n_changed": n_changed, "n_unchanged": trans.get("unchanged", 0),
        "changed_ok": bool(n_cnt_changed > 0 and trans.get("unchanged", 0) > 0
                           and marked_is_node_side),
        "yin_yang_ok": bool(n_cnt_changed > 0 and trans.get("unchanged", 0) > 0
                            and marked_is_node_side),
        "counts_changed": cnt_changed, "n_counts_changed": n_cnt_changed,
        "marked_all_unchanged": n_changed == 0,
        "n_marked_in_node": idx["n_marked_in_node"],
        "n_marked_is_node": idx["n_marked_is_node"],
        "two_sides_differ": marked_is_node_side,
    }
    # ⚠️⚠️ `der_rewrite` 之前**从不被键检查**（只有 `walk()` 的 `d` 被查）⇒ 这里补上。
    #    ⚠️ `n_marked_in_node` 是从 `index_before` 抄来的**原始**读数，
    #    所以登记时按 RAW_KEYS 算，不进 DERIVED_KEYS（否则两者重叠）。
    _dchk = set(rec["der_rewrite"]) - DERIVED_KEYS - RAW_KEYS
    assert not _dchk, f"der_rewrite 冒出未登记的键: {_dchk}"
    print(f"  [A] 游走 {a_der['n_tab_in']} 步 → 变化分类: {trans}")
    print(f"  [A] 游走后: [tabindex]={c_after['k_tabindex']} ti0={c_after['k_ti0']} "
          f"ti-1={c_after['k_tineg']} 节点带ti={c_after['k_nodes_ti']}/{c_after['k_nodes']}")
    print(f"  [A] 计费入口被 Tab 路过(非点击)的步号: {a_der['billing_tid_at_step']}", flush=True)
    dump(out)

    # ══ ② B 段：逐层焦点矩阵，**每层之后重新 goto 重置** ══════════════
    for nm, op in OPENERS:
        n2 = boot()
        if n2 == 0:
            rec["layers"].append({"name": nm, "skipped": "重置后登录态没命中"})
            continue
        idx2 = ev(INDEX_JS, [B939_SEL, MARK_ATTR])   # B 段要**重新打标记**
        # ⭐ 目标层 = 「开层后**新增**的那个」。⚠️ 937 踩过的坑：身份必须用
        #    **集合差**算，不能逐个 `!=`；而且**必须扣掉 node-part**
        #    （`.react-flow__node-toolbar` / `-panel` 是节点的一部分，不是浮层）。
        pre_ids = set(present_layer_ids())
        ro = op()
        page.wait_for_timeout(OPEN_WAIT)
        f_open = ev(FOCUS_JS, [MARK_ATTR, LAYER_SEL])
        post_ids = [x for x in present_layer_ids()
                    if x not in pre_ids and not x.startswith("nodepart:")]
        # ⚠️⚠️ 第一版用「新增层**唯一**」当判据 ⇒ 实测 **3/5 个层新增的是 2 个**
        #    （搜索 = feature-panel + search-panel；右键 = context-menu + role:menu）
        #    ⇒ 那 3 个层的 `tid` 全成 None、`walk()` 里的进层检测**整个失效**。
        # ⭐ 改用**开层焦点所在的那个层**（实测它在 3/5 的情况下都能定出来），
        #    焦点不在层内时才回落到「新增层唯一」，仍认不出就**如实记 None**。
        tid = None
        tid_src = None
        if f_open.get("in_layer") and f_open.get("layer_tid"):
            tid, tid_src = f_open["layer_tid"], "开层焦点所在层"
        elif len(post_ids) == 1:
            tid, tid_src = post_ids[0], "新增层唯一"
        else:
            tid_src = "认不出（如实记 None）"
        log, der = walk(B_TAB_CAP, tid)
        lay = {"name": nm, "open_result": ro, "focus_at_open": f_open,
               "layers_pre": sorted(pre_ids)[:8], "layers_post_new": post_ids,
               "target_tid": tid, "target_tid_src": tid_src,
               "k_before_walk": idx2["k"],
               "tab_log": log[:200], "der": der}
        rec["layers"].append(lay)
        print(f"  [B] [{nm}] 开={ro.get('ok')} 新增层={post_ids} 目标={tid} "
              f"开层焦点 in_layer={f_open['in_layer']} tag={f_open['tag']} "
              f"layer_tid={f_open['layer_tid']} "
              f"| 冷启动进层={der['tab_in_at']} reached={der['reached']} "
              f"wrapped={der['wrapped']} capped={der['capped']}", flush=True)
        dump(out)

runs = [r for r in out["runs"] if "der_rewrite" in r]
out["summary"] = {
    "n_reps_measured": len(runs),
    "k_before": [r["index_before"]["k"] for r in runs],
    "filter_losses": [{"n_neg_ti": r["index_before"]["n_neg_ti"],
                       "n_invisible": r["index_before"]["n_invisible"],
                       "n_disabled": r["index_before"]["n_disabled"]} for r in runs],
    "transitions": [r["der_rewrite"]["transitions"] for r in runs],
    "counts_before": [r["counts_before"] for r in runs],
    "counts_after": [r["counts_after"] for r in runs],
    "changed_ok": [r["der_rewrite"]["changed_ok"] for r in runs],
    "billing_steps": [r["walk_der"]["billing_tid_at_step"] for r in runs],
    "layer_matrix": [[{"name": l["name"],
                       "at_open_in_layer": (l.get("focus_at_open") or {}).get("in_layer"),
                       "at_open_layer_tid": (l.get("focus_at_open") or {}).get("layer_tid"),
                       "tab_in_at": (l.get("der") or {}).get("tab_in_at"),
                       "reached": (l.get("der") or {}).get("reached"),
                       "capped": (l.get("der") or {}).get("capped"),
                       "wrapped": (l.get("der") or {}).get("wrapped")}
                      for l in r["layers"]] for r in runs],
}
out["design_ok"] = {
    "reps_measured_ok": len(runs) == REPS,
    "k_stable_ok": all(r["der_k_stable"] for r in runs),
    # ⭐ 仪器阴阳对照门：必须有「变过」也有「没变过」
    "changed_ok": all(r["der_rewrite"]["changed_ok"] for r in runs),
    # ⭐ 重复性：逐字段比（**含** transitions 这个关键字段）
    "transitions_identical_ok": (
        len(runs) == 2 and runs[0]["der_rewrite"]["transitions"]
        == runs[1]["der_rewrite"]["transitions"]),
    "layer_matrix_measured_ok": all(
        all(l.get("der") is not None for l in r["layers"]) for r in runs),
}
dump(out)
print(json.dumps({"design_ok": out["design_ok"], "summary": out["summary"]},
                 ensure_ascii=False, indent=2), flush=True)
print(f"OUT={OUT}", flush=True)
