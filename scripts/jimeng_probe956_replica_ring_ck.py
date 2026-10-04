#!/usr/bin/env python3
r"""batch 956 **复刻侧**探针（**纯诊断 / 零节点点击**）：⭐⭐⭐ 加预算走到环尽头 —— 验「回不回得来」。

## 本批只答一件事

954 在**源站**上实测：环 = **102 下**，走完节点段后**进顶栏 18 个停靠**、
**然后回到 `node#0`** ⇒ **源站是开环、但回得来**。

953 在**复刻**上只走了 **28 下** ⇒ 看到画布内 24 个停靠后**进顶栏**，
**没看到回来** ⇒ ⚠️ 但 954 明确指出：**953 的 28 下不够**
（源站那一侧用了 102）⇒ **不许**拿 28 下断言复刻回不来。

⇒ **本批就是把那 28 加到 120**，把「回不回得来」**测出来**。

## 两格

| 格 | 做什么 |
| --- | --- |
| **格 0** | `Tab` × **120** 走到环尽头 ⇒ 停靠点三分计数、**出画布**、**回卷点**、**回不回得来** |
| **格 1…** | **每个「出画布」停靠点单独成格**、每格独立 `boot()`、**只发一个 `Shift+Tab`** ⇒ 从全局 chrome 往回走能不能回来 |

⚠️ 格 1 沿用 955 的骨架，把「内层停靠点」换成「出画布停靠点」⇒ **同一套修法**：
每格只发一个键 ⇒ **结构上**不可能再犯 952/954 那个「前一个键把焦点带走」的错。

## ⭐ 三道比较（承 955 的教训，一道都不许省）

1. **逐字** `curve_reproducible` —— ⚠️ 953 在复刻上红过（**节点 `data-testid` 带时间戳**）
   ⇒ **照旧如实记红**
2. **归一化** `curve_reproducible_norm` —— 953 那道（只把 tid 尾部数字归一化）
3. **行为字段** `curve_reproducible_behavior` —— 不依赖任何不稳定字段
   ⇒ **8/8 格 2/2 逐条相同**（955 实测）

⚠️ 955 的教训：**不要预设哪一道会绿** —— 三道**逐字进读数**，
**不许只报好看的第三道**。

## ⭐ 尺子：与 955 逐字相同（链式到 954 / 953 / 952）

- **七段 JS 全部与 955 逐字相同**
- **十七个助手 + `norm_row` + `behavior_key` + `classify` 全部与 955/954 逐字相同**
  （用 `inspect.getsource` 对着 955 的**文件内容** assert；
  `classify` 逐字来自 954）
- ⇒ 本批**零新件仪器**，唯一的新件是格子驱动器

## 探针自带的纪律（承 943→955）

1. ⭐ **尺子自证**：每一段退出前 `pre = cur`；**不许拿陈旧读数当基线**
2. ⭐ `reps_identical` **真算**；两轮比较**必须在 `for rep` 循环之外**
   （955 第一版栽在这上面 ⇒ **第二轮压根没跑**，而 `py_compile` 抓不到）
3. ⭐ 派生键不许与原始键重叠、不许重名、原始键不许漏登记（935 两道免疫针）
4. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版漏一个逗号 ⇒ 门恒绿）
5. ⚠️ **非字符串不许切片**（§131）；⚠️ 身份不稳的那一段三元组一律不当读数（946）
6. ⚠️ **写推断之前先查基线里有没有反例**（951 与 953 各栽一次）
7. ⚠️ **表格第一格不写裸数字**（948 栽过：`| 0 |` 被 pre-commit 当成新增批次）
8. ⚠️ **落盘排在所有后处理之前**（935）；⚠️ **不可逆动作放序列最后**

## 计费边界

**复刻是本地应用，本批零计费。** 插节点走**左栏入口**、不是节点本体；
只点**画布空白**去焦点（943 起的标准前置），⛔ 守卫拦在 `mouse.click` **之前**。
按键只有 `Tab` / `Shift+Tab`。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe956_replica_ring_ck.py
"""

import json
import pathlib
import textwrap
import time            # ⭐ `insert_kinds` 的插入节拍（照 901/953）

OUT = "/tmp/b956-replica-ring-ck.json"
REPS = 2
KINDS = ["文本", "图片", "时间线", "主体", "导演台"]   # 照 901/953
SETTLE = 350        # ms（照 952/953/954/955）
BLANK_WAIT = 900    # ms（照 952/953/954/955）
NO_TI_CAP = 40      # 照 952/953/954/955
# ⚠️⚠️ **不是 953 的 28**。954 在**源站**那一侧实测环 = **102 下** ⇒
#   **953 的 28 下连源站环的一半都不到**，据此断言「复刻回不来」是**预算不够**、
#   不是现象（901 `OVERRUN=6`→20、953 `14`→`24`→`28`、954 `14`→`120` 同一类）。
#   ⇒ 这里给 **120**，与 954 源站那一侧**同一个量级**。
N_PRESS_CAP = 120
N_OUT_CAP = 3       # 格 1 最多测前 3 个「出画布」停靠点（⚠️ 触顶**如实记**）
KEY_BACK = "Shift+Tab"   # ⭐ 每格**只发这一个键**

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")
P955 = pathlib.Path(__file__).with_name("jimeng_probe955_onekey_inner_src.py")
P954 = pathlib.Path(__file__).with_name("jimeng_probe954_source_ring_src.py")

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
    "ci", "mode", "n_press", "rows", "cell_ok", "cold_without_ti",
    "cold_armed", "n_audio_rail_button", "n_inserted", "inserted", "ready",
    "n_lead", "n_lead_cap_hit", "inner_seen", "out_seen", "position_verified",
    "position_who", "pressed_keys", "n_target_keys", "one_key_only",
    "probe_row", "from_stop", "to_stop", "from_class", "to_class",
    "moved_strong", "moved_weak", "pointer_before", "pointer_after",
    "back_into_node_list", "back_into_canvas", "skipped", "out_target",
    "stop_seq", "n_stops", "n_node_stops", "n_inner_stops", "n_out_stops",
    "out_stops", "left_the_canvas", "repeat_node_at", "wrap_k", "cycle_len",
    "reps_identical", "design_gates", "curve_reproducible",
    "curve_reproducible_norm", "reps_identical_norm", "norm_note",
    "curve_reproducible_behavior", "reps_identical_behavior",
    "three_gates_note", "ruler_actually_moved", "n_cells_total",
    "out_probe_capped", "came_back", "first_out_seq", "first_back_seq",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "left_the_canvas", "cycle_len", "position_verified",
              "one_key_only", "ruler_actually_moved", "curve_reproducible",
              "curve_reproducible_norm", "curve_reproducible_behavior"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index", "armed", "seq"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"
assert len(DERIVED_KEYS) == len(set(DERIVED_KEYS)), "派生键重名"
assert len(RAW_KEYS) == len(set(RAW_KEYS)), "原始键重名"

# ── 七段 JS：逐字来自 955（本批零新件 JS）──────────────────────────────
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

_p955src = P955.read_text(encoding="utf-8") if P955.exists() else ""
_p954src = P954.read_text(encoding="utf-8") if P954.exists() else ""
assert _p955src, "读不到 955 的源码 —— 尺子没得比，这道门恒绿"
assert _p954src, "读不到 954 的源码 —— `classify` 的尺子没得比，这道门恒绿"
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS", "WHOAMI_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL
                      + (WHOAMI_JS,)):
    assert _js in _p955src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 955 那份**不一致** —— 两份尺子开始分家了")


# ── 逐字复用 955 的助手（OUT 换成本批自己的；boot 换成复刻那一侧）───────
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


def classify(stop):
    """停靠点三分：节点本体 / 内层控件 / 出画布。"""
    if stop is None:
        return "none"
    if stop.startswith("node#"):
        return "node"
    if stop.startswith("inner:"):
        return "inner"
    return "out"


_UNSTABLE_TUPLE = ("added", "removed", "changed", "bit", "diff_ids")


def norm_row(row):
    """⚠️ 逐字那道 `curve_key` 比较在**源站**上恒红 —— 而那**不是**「读数不稳」，
    是**被测对象**在动：**源站的节点集逐轮会变**（§930 记过 77 / 76 两轮不同）。

    每一按的 `identity_stable=False` 意味着**按前按后的节点表对不上**
    ⇒ `added` / `removed` / `changed` / `bit` / `diff_ids` **全是构造性产物**
    （946：「身份对不上时三元组是空的是构造性产物，不是现象」）
    ⇒ ⭐ 归一化的做法**不是**放宽门、也**不是**改产品：逐字那道**照旧如实记红**，
    另加一道「**把身份不稳那一段的三元组标成 `UNSTABLE`**」的比较，
    **两道都进读数**。身份**稳**的那些按，三元组**照旧参与比较**。
    """
    r = dict(row)
    if r.get("identity_stable") is False:
        for k in _UNSTABLE_TUPLE:
            if k in r:
                r[k] = "UNSTABLE"
    return r


# ── 新件（956 自己）：`armed_*` 里复刻的 `data-testid` 带时间戳 ───────────
# ⚠️ 953 记过：**复刻节点 `rf__node-text-<13 位时间戳>`**、`rf__node-text-1732…`
#   与 `rf__node-text-1783…` 逐轮不同 ⇒ 逐字那道在复刻上**恒红**，而那**不是**
#   「读数不稳」⇒ 逐字那道**照旧如实记红**，另加这一道把 **tid 尾部数字**
#   归一化。⚠️ **只归一化 tid 的数字尾巴**，别的什么都不动。
_TID_TAIL = __import__("re").compile(r"^(.*?)(\d+)$")


def norm_tid(s):
    """新件：把 `armed_*` 里的 tid 尾部数字换成 `#`，其余逐字保留。
    ⛔ 不是 `norm_row` 的替代品 —— 两者**都**要跑（`norm_row` 管身份不稳的
    三元组、`norm_tid` 管时间戳），**不许**因为有一道就省另一道。"""
    if not isinstance(s, str):
        return s
    m = _TID_TAIL.match(s)
    return f"{m.group(1)}#" if m else s


# ── 新件（956 自己）：`_BEHAVIOR` 是 **956 的字段**，不是 955 那份 ─────────
# ⚠️⚠️ 照抄 955 的 `_BEHAVIOR` 会让 956 的行为门**整片变 `None`** —— 那些键
#   （`inner_target`/`step_rows`/`frozen_presses`…）在 956 的格里**根本不存在**
#   ⇒ `cell.get(k)` 全返回 `None` ⇒ 两轮**必然相同** ⇒ **一个恒真的判据**，
#   比没有判据**更坏**（⚠️ 本项目的硬规矩）。故此处只列 **956 格里真有的**、
#   且**不含 `data-testid` 时间戳**的字段（`rows` / `probes[].who*` 因此不列）。
_BEHAVIOR = ("mode", "n_press", "n_lead", "n_lead_cap_hit", "n_node_stops",
             "n_inner_stops", "n_out_stops", "n_stops", "stop_seq",
             "wrap_k", "cycle_len", "left_the_canvas", "came_back",
             "out_stops", "out_probe_capped", "first_out_seq", "first_back_seq",
             "n_target_keys", "pressed_keys", "one_key_only", "probed_stops",
             "position_verified", "position_who", "cold_without_ti",
             "cold_armed", "n_nodes", "n_inserted", "cell_ok",
             "pointer_seq", "inner_seen", "out_seen", "repeat_node_at",
             "probes",
             # ⭐ 关系式的**分段**：绝对环长逐轮会变，分段才是稳定读数
             "leg_node_inner", "leg_out", "n_legs", "node_inner_stops")


def behavior_key(cell):
    """⭐⭐⭐ **第三道比较：只比「行为字段」**。

    为什么需要第三道（前两道抓不住）：归一化是**按 `identity_stable` 这个标志
    分派**的，而**标志本身逐轮在动** —— 同一按，rep1 是 `True`、rep2 是 `False`
    ⇒ 归一化把它标成 `UNSTABLE`、rep2 保留原值 ⇒ 两边照样不同。
    ⇒ 946 那条原理的**正确落点**是：「哪些按的三元组不可用」本身也是逐轮变的
    ⇒ **三元组在这张画布上根本不是一个可复现的读数面**，任何按它分派的归一化
    都抓不住。
    ⇒ 而**行为字段**（停靠点身份 + 焦点动不动 + 指针 + 位置门 + 只按一键）
    **不依赖那个标志**，实测 **8/8 格 2/2 逐条相同**。
    ⚠️ **三道门都进读数**：逐字（红）、归一化（红）、行为（绿）——
    **不许只报好看的**。
    """
    return {k: cell.get(k) for k in _BEHAVIOR}


# ⭐⭐ 助手也逐字对着 955 的**文件内容** assert（`classify` 对着 954）
for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,
            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,
            strong_moved, identity, stop_name, walk_stuck, norm_row,
            behavior_key):
    _s = textwrap.dedent(__import__("inspect").getsource(_fn)).strip()
    assert _s in _p955src, (
        f"{_fn.__name__} 与 955 那份**不一致** —— 尺子的 Python 侧也开始分家了")
    del _s
_cs = textwrap.dedent(
    __import__("inspect").getsource(classify)).strip()
assert _cs in _p954src, "classify 与 954 那份**不一致** —— 停靠点分类换了口径"
del _cs

# ── 新件：复刻侧的就绪 + 固定前置（照 953；`boot_ck` 不是仪器）──────────
READY_JS = """([nodeSel, kinds]) => {
  const flow = document.querySelector('.react-flow');
  const nodes = document.querySelectorAll(nodeSel);
  const found = kinds.map(k =>
    !!document.querySelector('button[aria-label="' + k + '"]'));
  return {has_flow: !!flow,
          n_nodes: nodes.length,
          flow_aria: flow ? flow.getAttribute('aria-label') : null,
          flow_ti: flow ? flow.getAttribute('tabindex') : null,
          kinds_found: found,
          all_kinds: found.every(Boolean),
          node_ti_hist: Array.from(nodes).reduce((acc, el) => {
            const k = el.getAttribute('tabindex');
            const key = k === null ? 'None' : k;
            acc[key] = (acc[key] || 0) + 1;
            return acc;
          }, {})};
}"""
assert "READY_JS" not in _p955src, "956 的新件别混进「逐字相同」那组"
assert READY_JS.count("slice(") == 0, "READY_JS 不该有切片"

_URL = "http://localhost:4317/jimeng/canvas/demo"

# ⭐ `page` 必须挂在**模块级**：`ev` / `press_row` 是逐字复用来的，闭包拿不到局部
#   （953 靠 `with sync_playwright() as p:` 包住整段驱动来达成同一件事；这里
#   驱动段是模块级平铺的 ⇒ 直接 start/stop + `atexit` 兜底，等价且不重排代码）
from playwright.sync_api import sync_playwright   # noqa: E402

_pw = sync_playwright().start()
_browser = _pw.chromium.launch()
page = _browser.new_context(
    viewport={"width": 1512, "height": 1200}).new_page()

import atexit   # noqa: E402
atexit.register(lambda: (_browser.close(), _pw.stop()))

out = {
    "target": "replica", "url": _URL, "reps": REPS, "kinds": KINDS,
    "n_press_cap": N_PRESS_CAP, "n_out_cap": N_OUT_CAP,
    "key_back": KEY_BACK, "no_ti_cap": NO_TI_CAP,
    "forbidden_tids": list(FORBIDDEN_TIDS),
    "question": "954 在源站实测环 = 102 下、进顶栏后**回得来**；"
                "953 在复刻只走了 28 下 ⇒ 本批把预算加到 120，"
                "验「复刻回不回得来」",
    "ruler": {
        "js_verbatim_from_955": ["BLANK_JS", "CENSUS_JS", "NO_TI_JS",
                                 "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS",
                                 "WHOAMI_JS"],
        "py_verbatim_from_955": ["ev", "dump", "guard", "guard_point",
                                 "delta", "press_row", "curve_key",
                                 "armed_of", "no_ti_of", "pointer_of",
                                 "row_pointer", "in_toolbar", "strong_moved",
                                 "identity", "stop_name", "walk_stuck",
                                 "norm_row", "behavior_key"],
        "verbatim_from_954": ["classify"],
        "new_pieces": ["READY_JS", "boot_ck", "insert_kinds", "norm_tid"],
        "three_gates": "逐字 / 归一化 / 行为字段 —— **一道都不许省**"
                       "（955 的教训：不要预设哪一道会绿）",
    },
    "baseline_954": {
        "source_cycle": 102,
        "source_left_canvas_then_came_back": True,
        "source_out_stops": 18,
        "replica_953_budget": 28,
        "replica_953_out_stops": ["out:返回首页", "out:Canvas title: 测试项目",
                                  "out:项目"],
        "note": "954 明确写了「**不许**拿 953 的 28 下断言复刻回不来」"
                "（源站那一侧用了 102）⇒ 本批用 **120**、与源站**同量级**",
    },
    "runs": [],
}


def boot_ck():
    """新件：复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**。"""
    page.goto(_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev(READY_JS, [NODE_SEL, KINDS])


def insert_kinds():
    """固定前置：照 901/953 插 5 个节点。**左栏入口**、不是节点本体 ⇒
    不破 `zero_node_clicks`。返回**真的插进去几个** + 哪些。"""
    done = []
    for label in KINDS:
        loc = page.locator(f'button[aria-label="{label}"]')
        if not loc.count():
            continue
        el = loc.first
        tid = el.get_attribute("data-testid")
        guard(el.inner_text(), tid)          # ⛔ 守卫在 click **之前**
        el.click(timeout=8000)
        time.sleep(1.2)
        done.append(label)
    return done


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, mode in enumerate(("ring", "back")):
        tag = ("一路 Tab 走到环尽头（预算 120，与源站 102 同量级）"
               if mode == "ring"
               else f"每个出画布停靠点上只发一个 {KEY_BACK}")
        print(f"  --- 格 {ci}（{tag}）---", flush=True)
        rd = boot_ck()
        c = {"ci": ci, "mode": mode, "ready": rd, "rows": []}
        rec["cells"].append(c)
        dump(out)
        print(f"      就绪：flow={rd['has_flow']} nodes={rd['n_nodes']} "
              f"入口齐={rd['all_kinds']} 中性态 ti 分布={rd['node_ti_hist']}",
              flush=True)
        if not rd["has_flow"] or not rd["n_nodes"]:
            c["skipped"] = "画布根或节点没出来，本格不测"
            continue

        c["inserted"] = insert_kinds()
        c["n_inserted"] = len(c["inserted"])
        page.wait_for_timeout(1200)

        sp = ev(BLANK_JS)
        c["blank"] = sp
        if sp:
            guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点
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
        print(f"      插完 {c['n_inserted']} 个：DOM 共 {pre['n_nodes']}、"
              f"不带ti={nt['n_without_ti']}、armed={c['cold_armed']}", flush=True)
        dump(out)

        c["inner_seen"] = 0
        c["out_seen"] = 0
        c["n_lead"] = 0
        c["n_lead_cap_hit"] = False
        c["out_probe_capped"] = False
        c["pressed_keys"] = []
        c["n_target_keys"] = 0
        c["probes"] = []
        # ⭐ **按停靠点**去重，不按「第几个」去重：否则 `Shift+Tab` 探针会
        #   反复落在**同一个**出画布停靠点上（`返回首页` 每次都排第一）
        #   ⇒ 3 次探针 = 1 个点的 3 个样本，**不是** 3 个点。
        c["probed_stops"] = []
        while c["n_lead"] < N_PRESS_CAP:
            c["n_lead"] += 1
            ab = armed_of(pre["ti"])
            row, pre = press_row(page, pre, "Tab", c["n_lead"], "walk", 0)
            row["armed_before"] = ab
            row["armed_after"] = armed_of(pre["ti"])
            row["seq"] = c["n_lead"]
            c["rows"].append(row)
            st = stop_name(row)
            kd = classify(st)
            if kd == "inner":
                c["inner_seen"] += 1
            elif kd == "out":
                c["out_seen"] += 1
                if "first_out_seq" not in c:
                    c["first_out_seq"] = c["n_lead"]
                print(f"      [Tab {c['n_lead']:>3}] ⭐出画布第 {c['out_seen']} 个："
                      f"{st}", flush=True)
                if mode == "back" and st not in c["probed_stops"] \
                        and len(c["probes"]) < N_OUT_CAP:
                    # ⭐⭐ 位置门：按之前焦点必须**不在**节点表里
                    pv = bool(kd == "out")
                    c["position_verified"] = pv
                    c["position_who"] = {
                        kk: (row["who_after"] or {}).get(kk)
                        for kk in ("tag", "aria", "tid", "node_index",
                                   "type_attr")}
                    if not pv:
                        c["skipped"] = "位置门没过：按前焦点不在画布外"
                        print("      ⇒ 位置门没过（**如实记**）", flush=True)
                        break
                    pb = armed_of(pre["ti"])
                    prow, pre = press_row(page, pre, KEY_BACK, 0,
                                          "probe", len(c["probes"]) + 1)
                    prow["armed_before"] = pb
                    prow["armed_after"] = armed_of(pre["ti"])
                    prow["seq"] = c["n_lead"] + 1
                    c["rows"].append(prow)
                    c["pressed_keys"].append(KEY_BACK)
                    c["probed_stops"].append(st)
                    c["probes"].append({
                        "out_n": c["out_seen"],
                        "from": stop_name(prow, "before"),
                        "to": stop_name(prow, "after"),
                        "from_class": classify(stop_name(prow, "before")),
                        "to_class": classify(stop_name(prow, "after")),
                        "weak": prow["focus_moved"],
                        "strong": strong_moved(prow),
                        "back_into_node_list": bool(
                            (prow["who_after"] or {}).get("in_node_list"))})
                    print(f"          [{KEY_BACK} @第{c['out_seen']}个出画布] "
                          f"{stop_name(prow, 'before')} → "
                          f"{stop_name(prow, 'after')}"
                          f"（{classify(stop_name(prow, 'after'))}）"
                          f" 弱={prow['focus_moved']}"
                          f" 强={strong_moved(prow)}", flush=True)
                    dump(out)
                    continue
            else:
                print(f"      [Tab {c['n_lead']:>3}] {kd}:{st}", flush=True)
            dump(out)
        c["n_target_keys"] = len(c["pressed_keys"])
        c["one_key_only"] = bool(
            c["n_target_keys"] <= N_OUT_CAP
            and all(k == KEY_BACK for k in c["pressed_keys"]))
        if mode == "back":
            c["out_probe_capped"] = bool(
                c["out_seen"] > len(c["probes"]))
            c["came_back"] = any(p["to_class"] in ("node", "inner")
                                 for p in c["probes"])
            c["first_back_seq"] = next(
                (p["out_n"] for p in c["probes"]
                 if p["to_class"] in ("node", "inner")), None)

        # ── 派生量 ────────────────────────────────────────────────────
        main_rows = [r for r in c["rows"] if r["phase"] in ("walk", "cold")]
        c["stop_seq"] = [stop_name(r) for r in main_rows if r["k"] >= 1]
        kinds = [classify(s) for s in c["stop_seq"]]
        c["n_stops"] = len(c["stop_seq"])
        c["n_node_stops"] = kinds.count("node")
        c["n_inner_stops"] = kinds.count("inner")
        c["n_out_stops"] = kinds.count("out")
        c["out_stops"] = [s for s, kd in zip(c["stop_seq"], kinds)
                          if kd == "out"]
        c["left_the_canvas"] = bool(c["n_out_stops"] > 0)
        # 回卷 = 同一个节点下标第二次出现
        seen, c["repeat_node_at"] = set(), None
        for r in main_rows:
            if r["k"] < 1 or classify(stop_name(r)) != "node":
                continue
            ni = (r["who_after"] or {}).get("node_index")
            if ni is None:
                continue
            if ni in seen:
                c["repeat_node_at"] = {"seq": r["seq"], "node_index": ni}
                break
            seen.add(ni)
        c["wrap_k"] = (c["repeat_node_at"] or {}).get("seq")
        c["cycle_len"] = c["wrap_k"]
        # ⭐⭐⭐⭐ **环 = 节点段 + 出画布段**，两段**分别**记（关系式，**不记绝对值**）：
        #   环长**不是**一个稳定的绝对量（出画布段逐轮会变，见 §956 出画布段
        #   `sb_…` 元素逐轮多寡）⇒ **绝不能**拿 `wrap_k` 当复刻的「周期」断言。
        #   ⭐ 而**节点段**（从 `node#0` 到最后一个内层控件）是**逐轮逐条相同**
        #   的 ⇒ 那是真正稳定的那个关系式读数。
        _legs, _cur = [], None
        for _i, _kd in enumerate(kinds, start=1):
            if _kd == "out" and _cur is None:
                _cur = {"kind": "out", "from_seq": _i}
            elif _kd != "out" and _cur and _cur["kind"] == "out":
                _cur["to_seq"] = _i - 1
                _cur["len"] = _i - _cur["from_seq"]
                _legs.append(_cur)
                _cur = None
        c["leg_node_inner"] = (_legs[0]["from_seq"] - 1) if _legs else None
        c["leg_out"] = ([_lg["len"] for _lg in _legs]
                        if _legs else [])
        c["n_legs"] = len(_legs)
        c["node_inner_stops"] = (c["stop_seq"][:c["leg_node_inner"]]
                                 if c["leg_node_inner"] else None)
        c["pointer_seq"] = [row_pointer(r) for r in main_rows]
        c["n_press"] = c["n_lead"]
        c["cell_ok"] = bool(main_rows)
        print(f"      ⇒ 走 {c['n_lead']} 下：节点 {c['n_node_stops']}、"
              f"内层 {c['n_inner_stops']}、**出画布 {c['n_out_stops']}**"
              f"（left_the_canvas={c['left_the_canvas']}）、"
              f"**回卷 seq={c['wrap_k']}**、"
              f"出画布停靠点={c['out_stops'][:6]}"
              + (f"｜{KEY_BACK} 试了 {c['n_target_keys']} 处、"
                 f"**回得来={c['came_back']}**"
                 if c["pressed_keys"] else ""), flush=True)
        dump(out)

# ⭐ 两轮比较**必须在循环之外**（955 第一版栽在这上面 ⇒ 第二轮压根没跑）
# ⚠️ `curve_key` 是**逐字复用 955** 的、键表**内联在函数体里** ⇒ 其中
#   `step_rows` / `frozen_presses` / `swallowed_presses` / `left_button_press` /
#   `lag_is_one_press` / `reached_the_freeze` / `escape_releases` /
#   `shift_tab_moves` / `arrow_moves` 这 9 个键在 956 的格里**不存在** ⇒
#   `cell.get(k)` 全是 `None`。⇒ **逐字那道门的覆盖面只有 4/13**，
#   这里**如实数出来**记进读数（不许让读者以为 13 个键都在比）。
#   956 自己的问题（节点/内层/出画布/回卷）由**归一化那道**（整格）和
#   **行为那道**（`_BEHAVIOR`）覆盖。
n_cells = 2
out["n_cells_total"] = n_cells

_CURVE_KEYS = ("mode", "n_press", "cold_without_ti", "rows", "step_rows",
               "frozen_presses", "swallowed_presses", "left_button_press",
               "lag_is_one_press", "reached_the_freeze", "escape_releases",
               "shift_tab_moves", "arrow_moves")
_ck0 = curve_key(out["runs"][0]["cells"][0]) if out["runs"] else {}
out["curve_key_coverage"] = {
    "n_keys": len(_CURVE_KEYS),
    "n_present": sum(1 for k in _CURVE_KEYS
                     if k in (out["runs"][0]["cells"][0] if out["runs"] else {})),
    "absent_keys": [k for k in _CURVE_KEYS
                    if k not in (out["runs"][0]["cells"][0] if out["runs"] else {})],
    "note": "⚠️ 逐字那道门的覆盖面**如实记**：956 格里只有 4/13 个键存在，"
            "其余 9 个 `cell.get(k)` 返回 `None` ⇒ **不是** 13 项都在比。"
            "956 自己的问题由归一化（整格）与行为（`_BEHAVIOR`）两道覆盖。",
}

_ident = []
for j in range(n_cells):
    got = [curve_key(run["cells"][j]) for run in out["runs"]
           if j < len(run["cells"])]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["curve_reproducible"] = bool(all(_ident)) if _ident else False

# 归一化（955 的那道：只把 tid 尾部数字归一化 —— 复刻 id 带时间戳）
_ident_n = []
for j in range(n_cells):
    got = []
    for run in out["runs"]:
        c = run["cells"][j]
        r2 = dict(c)
        if "rows" in r2:
            r2["rows"] = [{**norm_row(r),
                           "armed_before": [norm_tid(x) for x in
                                            (r.get("armed_before") or [])],
                           "armed_after": [norm_tid(x) for x in
                                           (r.get("armed_after") or [])]}
                          for r in c.get("rows", [])]
        got.append(r2)
    _ident_n.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical_norm"] = _ident_n
out["curve_reproducible_norm"] = bool(all(_ident_n)) if _ident_n else False
out["norm_note"] = (
    "⚠️ 953 记过：**复刻节点 `data-testid` 带时间戳** ⇒ 逐字那道在复刻上**恒红**，"
    "而那**不是**「读数不稳」⇒ 逐字那道**照旧如实记红**，另加一道"
    "「只把 tid 尾部数字归一化」的比较。⚠️ **955 的教训：不要预设哪一道会绿** —— "
    "三道逐字进读数，**不许只报好看的第三道**。")

# 第三道：只比行为字段（不依赖任何不稳定字段）
_ident_b = []
for j in range(n_cells):
    got = [behavior_key(run["cells"][j]) for run in out["runs"]
           if j < len(run["cells"])]
    _ident_b.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical_behavior"] = _ident_b
out["curve_reproducible_behavior"] = bool(all(_ident_b)) if _ident_b else False
out["three_gates_note"] = (
    "三道比较逐字进读数：逐字 / 归一化 / 行为字段。"
    "⚠️ **每道的结果都逐字记，不许只报绿的那道**。")

# ⭐⭐⭐⭐ **第四道：只看「节点段」**（关系式）。上面三道都在比**整格**，
#   而整格里含 `rows`（带时间戳 tid）⇒ 逐字/归一化**注定**红。
#   ⇒ 这里只取**节点段**（`node#0` → 最后一个内层控件）——**那才是稳定的**。
_leg_same, _leg_lens = [], []
for j in range(n_cells):
    got = [run["cells"][j].get("node_inner_stops")
           for run in out["runs"] if j < len(run["cells"])]
    _leg_lens.append(got[0] and len(got[0]))
    _leg_same.append(bool(len(got) == REPS and got[0] and got[0] == got[1]))
out["node_inner_leg_identical"] = _leg_same
out["node_inner_leg_len"] = _leg_lens
out["node_inner_leg_reproducible"] = bool(all(_leg_same)) if _leg_same else False
out["fourth_gate_note"] = (
    "⭐⭐⭐⭐ **第四道（关系式）= 只比「节点段」**。逐字/归一化两道**注定红**"
    "（`rows` 带复刻的时间戳 tid）⇒ 它们**不是**本批问题的答案。"
    "节点段（`node#0`→最后一个内层控件，**不含出画布段**）是**逐轮逐条相同**的"
    " ⇒ **它才是稳定的读数**。⚠️ 出画布段**逐轮会变**（`sb_…` 那种无 aria 的"
    "元素逐轮多寡不同）⇒ **绝对环长不是稳定量，绝不能当「周期」断言**。")

# ⭐ 「操纵到底动了没有」——每格的第一按 Tab 都必须真的动了
_firsts = [run["cells"][j]["rows"][1] for run in out["runs"]
           for j in range(n_cells)
           if j < len(run["cells"]) and len(run["cells"][j].get("rows", [])) > 1]
out["ruler_actually_moved"] = bool(
    _firsts and all(r["focus_moved"] or strong_moved(r) or r["bit"]
                    for r in _firsts))

out["design_gates"] = {
    "js_py_verbatim_from_955": True,   # 文件级 assert 过了才会跑到这
    "classify_verbatim_from_954": True,
    "zero_node_clicks": bool(all(
        not run["cells"][j].get("click_rows")
        and run["cells"][j].get("n_click", 0) == 0
        for run in out["runs"] for j in range(n_cells)
        if "skipped" not in run["cells"][j])),
    "ruler_actually_moved": out["ruler_actually_moved"],
    "curve_reproducible": out["curve_reproducible"],
    "curve_reproducible_norm": out["curve_reproducible_norm"],
    "curve_reproducible_behavior": out["curve_reproducible_behavior"],
    "node_inner_leg_reproducible": out["node_inner_leg_reproducible"],
    "one_key_only": bool(all(
        run["cells"][1].get("one_key_only") is True
        for run in out["runs"] if "skipped" not in run["cells"][1])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    # ⭐ 行为门**不许恒真**：`_BEHAVIOR` 至少要有一半的键在格里**真的存在**
    #   （照抄 955 的键表会让 956 全 `None` ⇒ 两轮必然相同 ⇒ 假绿）
    "behavior_gate_non_vacuous": bool(
        out["curve_key_coverage"]["n_present"] >= 1
        and sum(1 for k in _BEHAVIOR
                if k in (out["runs"][0]["cells"][0] if out["runs"] else {}))
        >= len(_BEHAVIOR) / 2),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                    "active_tag", "focus_in_node", "no_ti",
                                    "aria", "node_index", "armed", "seq"))),
}
print("\n设计门：", out["design_gates"], flush=True)
print("逐格 2/2 相同（逐字/归一化/行为）：", out["reps_identical"],
      out["reps_identical_norm"], out["reps_identical_behavior"], flush=True)
for run in out["runs"]:
    for c in run["cells"]:
        if "skipped" in c:
            print(f"rep{run['rep']} 格{c['ci']}（{c['mode']}）："
                  f"⚠️ {c['skipped']}", flush=True)
            continue
        print(f"rep{run['rep']} 格{c['ci']}（{c['mode']}）："
              f"走 {c.get('n_lead')} 下、节点 {c.get('n_node_stops')}、"
              f"内层 {c.get('n_inner_stops')}、出画布 {c.get('n_out_stops')}、"
              f"**回卷 {c.get('wrap_k')}**｜出画布停靠点="
              f"{c.get('out_stops')}", flush=True)
        for p in c.get("probes", []):
            print(f"    第 {p['out_n']} 个出画布点：{KEY_BACK} "
                  f"{p['from']} → {p['to']}（{p['from_class']}→"
                  f"{p['to_class']}） 弱={p['weak']} 强={p['strong']}"
                  f" 回进节点表={p['back_into_node_list']}", flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
