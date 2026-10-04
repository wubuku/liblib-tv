#!/usr/bin/env python3
r"""batch 954 源站探针（**纯诊断 / 零节点点击**）：⭐⭐⭐ 走到源的 Tab 环尽头 + 补上 952 缺的那一格。

## 本批要答的三件事（**都是 953 明确没能测到的**）

1. ⭐⭐⭐ **源站的 `Tab` 到底会不会离开画布？环有多长？**
   - 953 只量到复刻：**画布内 24 个停靠点后焦点跑出画布**（开环）
   - 而 §930/§139/§896 早就记过源站是 **101 / 104** —— 但**那是别人的读数**，
     本项目的规矩是**自己的尺子自己量一遍**
   - ⚠️ 952 引了 101/104 却**没跟自己的「10」对账**（见 `cycle_10_retracted_953`）
2. ⭐⭐⭐ **焦点**真的在工具条里**时**，`Escape` 到底动不动焦点？**
   - 952 说「`Escape` 不能把焦点从工具条里弄出来」，**可它按 `Escape` 时焦点
     早就在节点本体上了**（`Shift+Tab` 那一步已经把它带出工具条）
   - ⇒ 撤回的理由是「压根没在那个位置测过」⇒ **本批就在那个位置测**
3. ⭐⭐⭐ **「`Shift+Tab` 立刻离开工具条」在**每一个**工具条停靠点上都成立吗？**
   - 953 在复刻侧发现它是**位置相关**的（从第 2 个按钮按是「退到第 1 个」）
   - ⇒ 本批**不测一个位置，测每一个位置**（关系式）

## ⭐ 本批的设计：同一把尺子，一路量到底

- **七段 JS 全部与 953 逐字相同** ⇒ 本批**零**新件 JS
- **十五个助手/常量也逐字复用**（`ev`/`dump`/`guard`/`guard_point`/`delta`/
  `press_row`/`curve_key`/`armed_of`/`no_ti_of`/`pointer_of`/`row_pointer`/
  `in_toolbar`/`walk_stuck`/`strong_moved`/`identity`/`stop_name`）——
  全部对着 953 的**文件内容** assert
- 源站的 `boot_fn` **逐字来自 952**（就绪判据两边不能换，换了就读数不可比）
- ⇒ 本批**唯一的新件**是**格子驱动器**（不是仪器）

## 两格

| 格 | 做什么 |
| --- | --- |
| **格 0** | `Tab` × **120** 一直走 ⇒ 环长、回卷点、**焦点有没有跑出画布** |
| **格 1** | 一路走；**每遇到一个「内层控件」停靠点**就当场试 `Shift+Tab` → `Escape` → `Tab` ⇒ 在**每一个**工具条停靠点上各测一遍 |

⚠️ **格 1 的按压预算是关系式的**（不是常量）：每碰到一个内层停靠点就多按 3 下 ⇒
总按压数 = 走完环所需 + 3 × 内层停靠点数 ⇒ **不许**钉一个绝对预算
（901 的 `OVERRUN=6` 不够、953 的 14 → 24 → 28 两次补预算，都是同一类）。
这里用 `N_PRESS_CAP` 做**硬上限**，并**如实记**触顶了没有。

## ⭐ 五道门（**全部可红**）

1. `js_py_verbatim_from_953` —— 尺子没跑偏
2. `ruler_actually_moved` —— **「操纵到底动了没有」必须自己答**：
   第 1 按 `Tab` **必须真的动了**（焦点动了或指针动了）。⚠️ 可红
3. `curve_reproducible` —— 逐格 2/2 逐条相同
4. `reached_an_inner_stop` —— **必须真的走进过内层控件**（否则格 1 什么也没测）。
   ⚠️ 可红：红了就说明这一格**没测到**，如实记、不下结论
5. `keys_disjoint` / `raw_keys_registered` —— 935 的两道免疫针

## 探针自带的纪律（承 943→953）

1. ⭐ **尺子自证**：每一段退出前 `pre = cur`；**不许拿陈旧读数当基线**
2. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
3. ⭐ 派生键不许与原始键重叠、不许重名、原始键不许漏登记（935 两道免疫针）
4. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版漏一个逗号 ⇒ 门恒绿）
5. ⭐ **新件不许混进「逐字相同」那组**（940 的办法）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ 身份不稳的那一段三元组一律不当读数（946）
7. ⚠️ **写推断之前先查基线里有没有反例**（951 与 953 各栽一次，953 那次的反例
   **就在自己引用的下一句**）
8. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配挡下
9. ⚠️ **落盘排在所有后处理之前**（935）
10. ⚠️ **不可逆动作放序列最后**；**不许拿陈旧读数当基线**

## 计费边界

**本批零节点点击。** 只发一次画布空白点击去焦点（943 起的标准前置），
⛔ 守卫拦在 `mouse.click` **之前**，契约是「**我正要点的这个元素**是什么」。
**本批零计费动作。** 键盘**有可能**走到计费入口上（889d 记过键盘可达性本身
就是一条风险面）⇒ 但本批**只发按键、不点任何东西**，且判别组只发
`Shift+Tab`/`Escape`/`Tab` 三个**不触发**的键。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe954_source_ring_src.py
"""

import json
import pathlib
import textwrap

OUT = "/tmp/b954-source-ring.json"
REPS = 2
SETTLE = 350        # ms（照 952/953）
BLANK_WAIT = 900    # ms（照 952/953）
NO_TI_CAP = 40      # 照 952/953
# ⚠️ §139：「到边界之后」的预算必须 > **一个完整周期（本画布 = 101 次按压）**
#   ⇒ 这里给 120。**不是**放宽判据，是把预算补到能闭合（901/953 同一类）。
N_PRESS_CAP = 120
# ⭐ 格 1 的每点预算：碰到一个内层停靠点就多按这三下
PROBE_KEYS = [("Shift+Tab", 1), ("Escape", 1), ("Tab", 1)]
MAX_INNER_PROBES = 6      # 关系式的上限（⚠️ 触顶必须**如实记**）

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")
P953 = pathlib.Path(__file__).with_name("jimeng_probe953_roving_ring_ck.py")
P952 = pathlib.Path(__file__).with_name("jimeng_probe952_freeze_who_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "no_ti",
    "no_ti_capped", "active_tag", "active_tid", "focus_in_node", "blank",
    "point", "i", "k", "hit_tag", "focus_ok", "seq",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who", "armed", "armed_before", "armed_after",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "ci", "mode", "n_press", "rows", "step_rows", "cell_ok", "reps_identical",
    "design_gates", "curve_reproducible", "ruler_actually_moved",
    "cold_without_ti", "cold_armed", "pointer_seq", "stop_seq", "n_stops",
    "n_node_stops", "n_inner_stops", "n_out_stops", "left_the_canvas",
    "wrap_k", "cycle_len", "out_stops", "repeat_node_at",
    "reached_an_inner_stop", "inner_probes", "n_inner_probes",
    "inner_probe_capped", "escape_moved_count", "shift_tab_moved_count",
    "shift_tab_left_toolbar_count", "inner_probe_stops",
    "focus_moved_strong", "swallowed_presses", "swallowed_presses_strong",
    "frozen_presses", "toolbar_presses", "toolbar_identities",
    "walked_while_in_toolbar", "all_stuck_in_toolbar", "n_audio_rail_button",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "cycle_len", "left_the_canvas", "reached_an_inner_stop",
              "ruler_actually_moved", "inner_probes", "n_out_stops"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index", "armed", "seq"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"
assert len(DERIVED_KEYS) == len(set(DERIVED_KEYS)), "派生键重名"
assert len(RAW_KEYS) == len(set(RAW_KEYS)), "原始键重名"

# ── 七段 JS：逐字来自 953（本批零新件 JS）──────────────────────────────
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
# ⭐ 守卫常量自己必须能匹配上东西（946 第一版漏一个逗号 ⇒ 这道门恒绿）
assert any(SLICE_STR in _js for _js in _JS_ALL), (
    "SLICE_STR 自己就匹配不上任何一段 JS —— 这道门恒绿，等于没有门")
for _name, _js in zip(("CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"),
                      _JS_ALL):
    assert _js.count("slice(") == _js.count(SLICE_STR), (
        f"{_name} 里有**非字符串**切片（§131：切片会把规律读反）")
assert WHOAMI_JS.count("slice(") == WHOAMI_JS.count(SLICE_STR), (
    "WHOAMI_JS 里有**非字符串**切片（§131）")

_p953src = P953.read_text(encoding="utf-8") if P953.exists() else ""
assert _p953src, "读不到 953 的源码 —— 尺子没得比，这道门恒绿"
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS", "WHOAMI_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL
                      + (WHOAMI_JS,)):
    assert _js in _p953src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 953 那份**不一致** —— 两份尺子开始分家了")


# ── 逐字复用 953 的助手（源站的 OUT 换成本批自己的）─────────────────────
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


def armed_of(ti):
    """复刻口径的指针：`ti == '0'` 的下标。"""
    return [i for i in sorted(ti, key=lambda x: int(x)) if ti[i] == "0"]


def no_ti_of(ti):
    """源站口径的指针：`ti is None`（属性被摘掉）的下标。"""
    return [i for i in sorted(ti, key=lambda x: int(x)) if ti[i] is None]


def pointer_of(ti):
    """⭐ 指针的**统一口径**：`no_ti[0] if no_ti else armed[0]`。
    两个都为空 = **仪器读不懂的形状**（既没布防也没有摘属性的）⇒ 记 `None`，
    **不许**当成 0。
    ⚠️ 复刻侧 `armAll` 写的是 `'0'`/`'-1'` ⇒ 属性一直都在 ⇒ `no_ti` **恒空**
    ⇒ 走 `armed` 口径；源站解除布防是**摘属性** ⇒ 走 `no_ti` 口径。"""
    nt, ar = no_ti_of(ti), armed_of(ti)
    if nt:
        return nt[0]
    if len(ar) == 1:
        return ar[0]
    return None


def row_pointer(row, which="after"):
    """逐按的指针：优先**源站口径**，否则**复刻口径**，否则 `None`。"""
    nt = row.get("no_ti_" + which) or []
    ar = row.get("armed_" + which) or []
    if nt:
        return nt[0]
    if len(ar) == 1:
        return ar[0]
    return None


def in_toolbar(row, which="after"):
    """焦点是不是落在某个节点的**内层控件**上（不是节点本体 `DIV`）。
    ⚠️ 判据**比 `aria-label`**（952 NNNN.5 的教训：`tag` 相同不代表焦点没动）。"""
    w = row.get("who_" + which) or {}
    return bool(w.get("in_node_list")) and w.get("tag") not in ("DIV", None)


def strong_moved(row, which_before="before", which_after="after"):
    """⭐⭐ **强判据**：焦点**身份**变没变。

    ⚠️⚠️ 为什么必须另立一条：952 那把尺子逐字复用过来的 `focus_moved`
    比的是 `(active_tag, active_tid)`，而 `FOCUS_JS` 的 `active_tid` 取的是
    `closest('[data-testid]')` —— **内层按钮自己没有 `data-testid`**，
    借的是**所属节点**的 ⇒ 按钮之间切换时 `(BUTTON, 节点tid)` **一模一样**
    ⇒ 弱判据一律报「没动」。
    952 自己把这个陷阱写进了基线（NNNN.5），**却还在用它自己的仪器**。
    ⇒ 953 不改 952 的尺子（逐字复用是纪律），**另立一条强的并排记**。
    """
    return identity(row, which_before) != identity(row, which_after)


def identity(row, which="after"):
    w = row.get("who_" + which) or {}
    return (w.get("tag"), w.get("aria"), w.get("tid"),
            w.get("node_index"), w.get("type_attr"))


def stop_name(row, which="after"):
    """一个停靠点的**归一化名字**：节点本体记 `node#<下标>`，内层控件记
    `内层:<aria>`。⇒ 两边（源站的 `节点 2` / 复刻的 `文本 1`）**不可直接比**，
    该比的是**形状**（几个节点停靠点、几个内层停靠点、指针在哪一段不动）。"""
    w = row.get("who_" + which) or {}
    if not w.get("who"):
        return None
    if w.get("tag") == "DIV" and w.get("in_node_list"):
        return f"node#{w.get('node_index')}"
    if w.get("in_node_list"):
        return f"inner:{(w.get('aria') or '')[:18]}"
    return f"out:{(w.get('aria') or '')[:18]}"


def walk_stuck(rows):
    """⭐ 关系式：走完内层控件那段期间，指针**一次都不许动**。"""
    tb = [r for r in rows if r["k"] >= 1 and in_toolbar(r)]
    if not tb:
        return {"n_toolbar_presses": 0, "walked": 0, "stuck": 0,
                "all_stuck": None, "identities": []}
    stuck = sum(1 for r in tb
                if r["armed_before"] == r["armed_after"])
    return {"n_toolbar_presses": len(tb),
            "walked": len(tb) - stuck, "stuck": stuck,
            "all_stuck": bool(stuck == len(tb)),
            "identities": [{"k": r["k"], **{kk: (r["who_after"] or {}).get(kk)
                                            for kk in ("tag", "aria", "tid",
                                                       "node_index",
                                                       "type_attr")}}
                           for r in tb]}


# ⭐⭐ 助手也逐字对着 953 的**文件内容** assert（不是对着我自己）
for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,
            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,
            strong_moved, identity, stop_name, walk_stuck):
    _s = textwrap.dedent(__import__("inspect").getsource(_fn)).strip()
    assert _s in _p953src, (
        f"{_fn.__name__} 与 953 那份**不一致** —— 尺子的 Python 侧也开始分家了")
    del _s


# ── 源站的 boot：逐字来自 952（就绪判据两边不能换）─────────────────────
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


_p952src = P952.read_text(encoding="utf-8") if P952.exists() else ""
assert _p952src, "读不到 952 的源码 —— boot 的尺子没得比，这道门恒绿"
_bs = textwrap.dedent(
    __import__("inspect").getsource(boot_fn)).strip()
assert _bs in _p952src, "boot_fn 与 952 那份**不一致** —— 就绪判据换了就读数不可比"
del _bs

URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")


def classify(stop):
    """停靠点三分：节点本体 / 内层控件 / 出画布。"""
    if stop is None:
        return "none"
    if stop.startswith("node#"):
        return "node"
    if stop.startswith("inner:"):
        return "inner"
    return "out"


out = {
    "target": "source", "url": URL, "reps": REPS,
    "n_press_cap": N_PRESS_CAP, "probe_keys": PROBE_KEYS,
    "max_inner_probes": MAX_INNER_PROBES, "no_ti_cap": NO_TI_CAP,
    "forbidden_tids": list(FORBIDDEN_TIDS),
    "question": "源站的 Tab 环到底有多长、会不会离开画布；"
                "以及焦点**真的在工具条里**时 Escape / Shift+Tab 动不动",
    "ruler": {
        "js_verbatim_from_953": ["BLANK_JS", "CENSUS_JS", "NO_TI_JS",
                                 "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS",
                                 "WHOAMI_JS"],
        "py_verbatim_from_953": ["ev", "dump", "guard", "guard_point",
                                 "delta", "press_row", "curve_key",
                                 "armed_of", "no_ti_of", "pointer_of",
                                 "row_pointer", "in_toolbar", "strong_moved",
                                 "identity", "stop_name", "walk_stuck"],
        "boot_verbatim_from_952": ["boot_fn"],
        "new_pieces": ["classify"],   # 只有格子驱动器是新的，**不是仪器**
        "only_variable": "本批换的是 URL（复刻 → 源站）与格子设计",
    },
    "prior_baseline": {
        "sec930": "源站 `canvas-editor-menu` 两次落点间隔 **101 / 104**"
                  "（两轮不同，节点数 77 / 76 也在变）",
        "sec139": "「到边界之后」的预算必须 > **一个完整周期（本画布 = 101 次按压）**",
        "sec896": "复刻侧 `节点数 + 25 = 101` 次的预算",
        "replica_953": "复刻画布内 **24 个停靠点**后焦点**跑出画布**（开环）",
        "note": "这些**都不是本批的读数** —— 本批用自己的尺子重测；"
                "§930/§139 是**别人**记的，不许当结论用",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, mode in enumerate(("ring", "inner")):
        tag = ("一路 Tab 走到环尽头" if mode == "ring"
               else f"每遇一个内层停靠点就试 {'/'.join(k for k, _ in PROBE_KEYS)}")
        print(f"  --- 格 {ci}（{tag}）---", flush=True)
        n_audio = boot_fn()
        c = {"ci": ci, "mode": mode, "n_audio_rail_button": n_audio,
             "rows": [], "step_rows": [], "inner_probes": []}
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
        c["n_nodes"] = pre["n_nodes"]
        c["cold_without_ti"] = nt["n_without_ti"]
        c["cold_armed"] = armed_of(pre["ti"])
        c["rows"].append({
            "phase": "cold", "step": 0, "k": 0, "seq": 0, "key": None,
            "no_ti_before": nt["no_ti"], "no_ti_after": nt["no_ti"],
            "no_ti_capped": nt["no_ti_capped"], "pointer_moved": False,
            "active_before": None, "active_after": None, "was_arm": None,
            "bit": None, "n_added": None,
            "w_before": pre["n_without_ti"], "w_after": pre["n_without_ti"],
            "identity_stable": None,
            "armed_before": c["cold_armed"], "armed_after": c["cold_armed"],
            "who_before": None, "who_after": ev(WHOAMI_JS, [NODE_SEL])})
        print(f"      冷启动：nodes={pre['n_nodes']}、"
              f"不带ti={nt['n_without_ti']}、armed={c['cold_armed']}",
              flush=True)
        dump(out)

        n_press = 0
        n_inner = 0
        capped = False
        seq = 0
        while n_press < N_PRESS_CAP:
            n_press += 1
            seq += 1
            ab = armed_of(pre["ti"])
            nb = no_ti_of(pre["ti"])
            row, pre = press_row(page, pre, "Tab", n_press, "ring", 0)
            row["armed_before"] = ab
            row["armed_after"] = armed_of(pre["ti"])
            row["no_ti_full_before"] = nb
            row["seq"] = seq
            c["rows"].append(row)
            stop = stop_name(row)
            kind = classify(stop)
            print(f"      [Tab {n_press:>3}] {row['active_before']}→"
                  f"{row['active_after']} 强动={strong_moved(row)} "
                  f"指针 {row['no_ti_before'][:2]}→{row['no_ti_after'][:2]} "
                  f"落点 {kind}:{str(stop)[:26]}", flush=True)
            dump(out)

            # ⭐ 格 1：**在每一个内层停靠点上**当场试那三个键
            if mode == "inner" and kind == "inner":
                if n_inner >= MAX_INNER_PROBES:
                    capped = True
                    print(f"      （内层探测已达上限 {MAX_INNER_PROBES}，"
                          f"**如实记** capped=True）", flush=True)
                    break
                n_inner += 1
                probe = {"at_seq": seq, "stop": stop, "steps": []}
                for key, times in PROBE_KEYS:
                    for _ in range(times):
                        seq += 1
                        pb = armed_of(pre["ti"])
                        prow, pre = press_row(page, pre, key, 0, "inner", seq)
                        prow["armed_before"] = pb
                        prow["armed_after"] = armed_of(pre["ti"])
                        prow["seq"] = seq
                        c["step_rows"].append(prow)
                        c["rows"].append(prow)
                        probe["steps"].append({
                            "key": key, "seq": seq,
                            "from": stop_name(prow, "before"),
                            "to": stop_name(prow, "after"),
                            "weak": prow["focus_moved"],
                            "strong": strong_moved(prow)})
                        print(f"          [{key} @{stop[:18]}] "
                              f"{stop_name(prow, 'before')}"
                              f" → {stop_name(prow, 'after')}"
                              f" 弱={prow['focus_moved']}"
                              f" 强={strong_moved(prow)}", flush=True)
                        dump(out)
                c["inner_probes"].append(probe)
                dump(out)

        c["n_press"] = n_press
        c["inner_probe_capped"] = capped

        # ── 派生量（**关系式**，不钉绝对值）────────────────────────────
        main_rows = [r for r in c["rows"] if r["phase"] == "ring"]
        c["stop_seq"] = [stop_name(r) for r in main_rows if r["k"] >= 1]
        c["n_stops"] = len(c["stop_seq"])
        kinds = [classify(s) for s in c["stop_seq"]]
        c["n_node_stops"] = kinds.count("node")
        c["n_inner_stops"] = kinds.count("inner")
        c["n_out_stops"] = kinds.count("out")
        c["out_stops"] = [s for s, kd in zip(c["stop_seq"], kinds)
                          if kd == "out"]
        # ⭐ 「焦点有没有离开画布」= 停靠点里出现 `out:`（**关系式**）
        c["left_the_canvas"] = bool(c["n_out_stops"] > 0)
        # 回卷 = **同一个节点下标第二次出现**（源站的环按节点下标走）
        seen, c["repeat_node_at"] = set(), None
        for i, r in enumerate(main_rows):
            w = r["who_after"] or {}
            if classify(stop_name(r)) != "node":
                continue
            ni = w.get("node_index")
            if ni is None:
                continue
            if ni in seen:
                c["repeat_node_at"] = {"seq": r["seq"], "node_index": ni}
                break
            seen.add(ni)
        c["wrap_k"] = (c["repeat_node_at"] or {}).get("seq")
        c["cycle_len"] = c["wrap_k"]
        c["pointer_seq"] = [row_pointer(r) for r in main_rows]
        c["frozen_presses"] = sum(
            1 for r in main_rows if r["k"] >= 1
            and r["no_ti_before"] == r["no_ti_after"])
        c["swallowed_presses"] = sum(
            1 for r in main_rows if r["k"] >= 1
            and r["no_ti_before"] == r["no_ti_after"]
            and not r["focus_moved"])
        c["swallowed_presses_strong"] = sum(
            1 for r in main_rows if r["k"] >= 1
            and r["no_ti_before"] == r["no_ti_after"]
            and not strong_moved(r))
        for r in main_rows:
            r["focus_moved_strong"] = strong_moved(r) if r["k"] >= 1 else None
        ws = walk_stuck(main_rows)
        c["toolbar_presses"] = ws["n_toolbar_presses"]
        c["toolbar_identities"] = ws["identities"]
        c["walked_while_in_toolbar"] = ws["walked"]
        c["all_stuck_in_toolbar"] = ws["all_stuck"]
        c["n_inner_probes"] = len(c["inner_probes"])
        c["reached_an_inner_stop"] = bool(c["n_inner_probes"] > 0)
        # ⭐ 格 1 的三条读数：**各判各的**，都不许预设方向
        c["escape_moved_count"] = sum(
            1 for p in c["inner_probes"] for s in p["steps"]
            if s["key"] == "Escape" and s["strong"])
        c["shift_tab_moved_count"] = sum(
            1 for p in c["inner_probes"] for s in p["steps"]
            if s["key"] == "Shift+Tab" and s["strong"])
        c["shift_tab_left_toolbar_count"] = sum(
            1 for p in c["inner_probes"] for s in p["steps"]
            if s["key"] == "Shift+Tab" and s["strong"]
            and (s["to"] or "").startswith(("out:", "node#"))
            and (s["from"] or "").startswith("inner:"))
        c["inner_probe_stops"] = [p["stop"] for p in c["inner_probes"]]
        c["cell_ok"] = bool(main_rows)
        print(f"      ⇒ 走 {c['n_press']} 下：节点停靠 {c['n_node_stops']}、"
              f"内层 {c['n_inner_stops']}、**出画布 {c['n_out_stops']}**"
              f"（left_the_canvas={c['left_the_canvas']}）"
              f"、回卷 seq={c['wrap_k']}、"
              f"指针不动 {c['frozen_presses']} 下"
              f"（强判据下焦点也没动 {c['swallowed_presses_strong']} 下）"
              + (f"｜内层探测 {c['n_inner_probes']} 处："
                 f"Esc 动了 {c['escape_moved_count']}、"
                 f"Shift+Tab 动了 {c['shift_tab_moved_count']}"
                 f"（其中**离开内层** {c['shift_tab_left_toolbar_count']}）"
                 if c["inner_probes"] else ""), flush=True)
        dump(out)

_ident = []
for ci in range(2):
    got = [curve_key(run["cells"][ci]) for run in out["runs"]
           if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["curve_reproducible"] = bool(all(_ident))

# ⭐⭐ 「操纵到底动了没有」——自己答，不许默认
_firsts = [run["cells"][0]["rows"][1] for run in out["runs"]
           if "skipped" not in run["cells"][0]
           and len(run["cells"][0]["rows"]) > 1]
out["ruler_actually_moved"] = bool(
    _firsts and all(r["focus_moved"] or strong_moved(r) or r["bit"]
                    for r in _firsts))

out["design_gates"] = {
    "js_py_verbatim_from_953": True,   # 文件级 assert 过了才会跑到这
    "boot_verbatim_from_952": True,
    "zero_node_clicks": bool(all(
        not run["cells"][ci].get("click_rows")
        and run["cells"][ci].get("n_click", 0) == 0
        for run in out["runs"] for ci in range(2)
        if "skipped" not in run["cells"][ci])),
    "curve_reproducible": out["curve_reproducible"],
    "ruler_actually_moved": out["ruler_actually_moved"],
    "reached_an_inner_stop": bool(all(
        run["cells"][1].get("reached_an_inner_stop")
        for run in out["runs"] if "skipped" not in run["cells"][1])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                    "active_tag", "focus_in_node", "no_ti",
                                    "aria", "node_index", "armed", "seq"))),
}
print("\n设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同：", out["reps_identical"], flush=True)
for run in out["runs"]:
    for c in run["cells"]:
        if "skipped" in c:
            continue
        print(f"rep{run['rep']} 格{c['ci']}（{c['mode']}）："
              f"走 {c.get('n_press')} 下、节点 {c.get('n_node_stops')}、"
              f"内层 {c.get('n_inner_stops')}、出画布 {c.get('n_out_stops')}、"
              f"回卷 {c.get('wrap_k')}"
              f"｜内层探测点={c.get('inner_probe_stops')}", flush=True)
        for p in c.get("inner_probes", []):
            print(f"    在 {p['stop']!r}：", flush=True)
            for s in p["steps"]:
                print(f"      {s['key']:<10} {s['from']} → {s['to']}"
                      f"  弱={s['weak']} 强={s['strong']}", flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
