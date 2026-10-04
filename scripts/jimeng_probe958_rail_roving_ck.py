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

OUT = "/tmp/b958-rail-roving-ck.json"
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
P957 = pathlib.Path(__file__).with_name("jimeng_probe957_rail_roving_src.py")
P954 = pathlib.Path(__file__).with_name("jimeng_probe954_source_ring_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "no_ti",
    "no_ti_capped", "active_tag", "active_tid", "focus_in_node", "blank",
    "point", "i", "k", "hit_tag", "focus_ok", "seq",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who", "armed", "armed_before", "armed_after",
    # ⭐⭐ 958 补登记：957 起这 5 个是**原始读数**，而 958 的表是**照抄 956** 的
    #   ⇒ `raw_keys_registered` **真红**（= 935 的第二道免疫针又一次派上用场）
    "rail_ti", "rail_aria", "rail_focusable", "n_rail_buttons", "host_role",
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

# ── 驱动段：4 格（ census / arrow / ring / armcheck）────────────────────────
# ⚠️⚠️ 全部**从 956 的驱动段改写**，仪器部分**一字未动**（文件级 assert 会验）。
# ⚠️⚠️ **957 查红的那条**：判别键那一按**必须绕开 `press_row`** ——
#   `press_row` 内部会调 `ARM_FOCUS_JS`，而它**带 `el.focus()`**
#   ⇒ 若那一刻画布里恰好有节点带 `tabindex="0"`，它会把焦点**拽走**。
# ⇒ 本批所有需要「按完键焦点在哪」的读数，都**自己发键 + 逐字
#   `FOCUS_JS`/`WHOAMI_JS` 读**；`press_row` 只用于 `Tab` 行走。
RAIL_TID = "canvas-fixed-toolbar"      # ⭐ 与 957 逐字相同的锚点
KEY_ARROW = "ArrowDown"                # ⭐ 与 957 逐字相同
N_AFTER_RAIL = 40     # ⭐ **关系式**预算：走到左栏后再多按这么多下覆盖出画布段
                        #   （源站 18 / 改后复刻 19）⇒ 不用钉绝对环长

# ⭐ `RAIL_JS` **逐字来自 957**（普查用、**不是仪器**）
_p957src = P957.read_text(encoding="utf-8") if P957.exists() else ""
assert _p957src, "读不到 957 的源码 —— `RAIL_JS` 没得比，这道门恒绿"
# ⚠️ 第一版用 `re.search(r'RAIL_JS = """\(\[[^\]]*\]\)\s*=>.*?\n"""')` **抽不出来**：
#   957 里 `RAIL_JS` 的参数是 `([tid, nodeSel])`，而 `nodeSel` 里**不含** `]` ⇒
#   那个字符类本该匹配得上……真正的坑是 `.*?` **不跨行**地撞上函数体里第一处
#   `\n"""` 之外的边界。⇒ 改成**按行切**：从 `RAIL_JS = """` 那行读到下一个
#   **单独一行**的 `}"""`，再断言抽出来的正文**逐字**在 957 里。
_rail_lines = _p957src.splitlines()
_r0 = next(i for i, _l in enumerate(_rail_lines)
           if _l.startswith("RAIL_JS = "))
_r1 = next(i for i in range(_r0 + 1, len(_rail_lines))
           if _rail_lines[i] == '}"""')
# ⚠️⚠️ **函数签名在 `RAIL_JS = """` 那一行**（`([tid, nodeSel]) => {`），
#   **不在**下面那些行里 ⇒ 第一版只切了函数体、抽出来的东西**少一个签名**
#   ⇒ 自己那道 `count("[tid, nodeSel]") == 1` 的免疫针当场真红（**这正是它的用处**）。
RAIL_JS = "\n".join([_rail_lines[_r0].split('"""', 1)[1]]
                    + _rail_lines[_r0 + 1:_r1]
                    + ["}"])          # ⭐ 收尾那行是 `}"""` ⇒ 函数体的 `}` 要**补回来**
assert RAIL_JS, "从 957 抽出来的 `RAIL_JS` 是空的"
assert RAIL_JS.count("[tid, nodeSel]") == 1, (
    "抽出来的 `RAIL_JS` 不像 957 那份（参数签名对不上）")
# ⚠️⚠️ **大括号配平免疫针**（第四版才补上）：
#   `jimeng_probe_js_syntax_check.py` 只认**字面量** `NAME = """..."""`，
#   而这里的 `RAIL_JS` 是**用切片拼出来的** ⇒ **那道门根本看不到它**
#   ⇒ `py_compile` 也看不到 ⇒ ⭐ 两次都只跑到 `page.evaluate` 才炸
#   （`SyntaxError: Unexpected end of input`）⇒ 自己配平一次。
assert RAIL_JS.count("{") == RAIL_JS.count("}"), (
    f"`RAIL_JS` 大括号不配平（{RAIL_JS.count('{')} vs {RAIL_JS.count('}')}）"
    " —— 切片漏了函数体的收尾 `}`，**这正是 958 前三版的坑**")
assert RAIL_JS.rstrip().endswith("}"), "`RAIL_JS` 尾部不完整（箭头函数没闭合）"
_RAIL_BLOCK = "\n".join([_rail_lines[_r0]] + _rail_lines[_r0 + 1:_r1 + 1])
assert _RAIL_BLOCK in _p957src, (
    "`RAIL_JS` 与 957 那份**不一致** —— 逐字 assert 必须过")
assert _rail_lines[_r1] == '}"""', "957 的 `RAIL_JS` 收尾行不再是 `}\"\"\"`"
del _r0, _r1, _rail_lines, _RAIL_BLOCK

out["rail_tid"] = RAIL_TID
out["key_arrow"] = KEY_ARROW
out["n_after_rail"] = N_AFTER_RAIL
out["question"] = (
    "957 在**源站**测死：左栏是 ARIA roving tabindex（`0`×1 + `-1`×9）且"
    "`ArrowDown` 在栏内移动焦点 ⇒ 956 那个「出画布段 27 vs 18、净多 9」里"
    "最大的 8 个就是左栏。本批**复刻侧**实施后：左栏是不是**只贡献 1 个 "
    "`Tab` 停靠点**、`ArrowDown` 是不是**留在栏内**？")
out["baseline_956"] = {
    "replica_rail_stops_per_cycle": 9,
    "replica_out_stops_per_cycle": 27,
    "replica_wrap_k": 53,
    "replica_rail_arias": ["文本", "图片", "视频", "音频", "时间线", "主体",
                           "导演台", "资产库", "上传"],
    "source_957_rail_ti_hist": {"0": 1, "None": 43, "-1": 9},
    "source_957_arrow": "out:文本 → out:图片（留在栏内）",
    "expected_after_fix": {
        "rail_stops_per_cycle": 1,
        "out_stops_per_cycle": 19,     # 27 − 8
        "arrow": "留在栏内、移到下一枚",
        "note": "⚠️ **出画布段 19 是推算**（27 − 8）⇒ 读数**必须实测**，"
                "**不许**拿它当断言；本批只把它当**对照**",
    },
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, mode in enumerate(("census", "arrow", "ring", "armcheck")):
        tag = {"census": "普查左栏 9 枚按钮的 tabindex（**零点击**）",
               "arrow": f"走到左栏那一个停靠点上，**只发一个** {KEY_ARROW}",
               "ring": f"走到左栏后再按 {N_AFTER_RAIL} 下，量出画布段",
               "armcheck": "**只调** `ARM_FOCUS_JS`、不发键（验 957 查红的那条）"}[mode]
        print(f"  --- 格 {ci}（{tag}）---", flush=True)
        rd = boot_ck()
        c = {"ci": ci, "mode": mode, "ready": rd, "rows": [],
             "pressed_keys": []}
        rec["cells"].append(c)
        dump(out)
        if not rd["has_flow"] or not rd["n_nodes"]:
            c["skipped"] = "画布根或节点没出来，本格不测"
            continue

        c["inserted"] = insert_kinds()
        c["n_inserted"] = len(c["inserted"])
        page.wait_for_timeout(1200)

        # ── 普查（**每格都做**：它是「我够得着吗」的前置）──────────────────
        cen = ev(RAIL_JS, [RAIL_TID, NODE_SEL])
        c["census"] = cen
        c["n_rail_buttons"] = cen.get("n_rail_buttons")
        c["n_rail_focusable"] = cen.get("n_focusable")
        c["n_rail_ti_hist"] = cen.get("ti_hist")
        c["host_role"] = cen.get("host_role")
        c["host_aria"] = cen.get("host_aria")
        c["rail_row"] = [{"aria": r["aria"], "rail_ti": r["ti"],
                          "rail_focusable": r["focusable"]}
                         for r in (cen.get("rows") or [])
                         if r["tag"] == "BUTTON"]
        print(f"      普查：role={cen.get('host_role')!r} "
              f"aria={cen.get('host_aria')!r}；按钮 "
              f"{cen.get('n_rail_buttons')} 枚、顺序里可聚焦 "
              f"{cen.get('n_focusable')} 枚、ti 分布 {cen.get('ti_hist')}",
              flush=True)
        for r in c["rail_row"]:
            print(f"        · {r['aria']!r:16s} ti={r['rail_ti']!r:6s} "
                  f"focusable={r['rail_focusable']}", flush=True)

        if mode == "census":
            c["verdict_A"] = (
                f"复刻左栏顺序里可聚焦的按钮数 = {cen.get('n_focusable')}"
                f"（共 {cen.get('n_rail_buttons')} 枚），ti 分布 "
                f"{cen.get('ti_hist')}")
            print(f"      ⇒ {c['verdict_A']}", flush=True)
            dump(out)
            continue

        # ── 引导：一直按 `Tab`，数到第 1 个左栏停靠点就停（关系式）──────
        sp = ev(BLANK_JS)
        c["blank"] = sp
        if sp:
            guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(BLANK_WAIT)
        pre = ev(CENSUS_JS, [NODE_SEL])
        c["n_nodes"] = pre["n_nodes"]
        c["cold_without_ti"] = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])["n_without_ti"]
        c["cold_armed"] = armed_of(pre["ti"])

        c["n_lead"] = 0
        c["n_rail_stops"] = 0
        c["rail_stop_seqs"] = []
        c["n_lead_cap_hit"] = False
        rail_row = None
        while c["n_lead"] < N_PRESS_CAP:
            c["n_lead"] += 1
            row, pre = press_row(page, pre, "Tab", c["n_lead"], "walk", 0)
            row["seq"] = c["n_lead"]
            row["armed_before"] = armed_of(pre["ti"])
            row["armed_after"] = armed_of(pre["ti"])
            c["rows"].append(row)
            if (row["who_after"] or {}).get("tid") == RAIL_TID:
                c["n_rail_stops"] += 1
                c["rail_stop_seqs"].append(c["n_lead"])
                print(f"      [Tab {c['n_lead']:>3}] ⭐左栏停靠点："
                      f"{stop_name(row)}", flush=True)
                rail_row = row
                if mode in ("arrow", "armcheck"):
                    break
            dump(out)
        else:
            c["n_lead_cap_hit"] = True
        c["reached_a_rail_stop"] = bool(rail_row)
        if not rail_row:
            c["skipped"] = (f"按了 {c['n_lead']} 下都没走到 `{RAIL_TID}` "
                            "停靠点 ⇒ **这一格什么也没测**，不下结论")
            print(f"      ⚠️ {c['skipped']}", flush=True)
            dump(out)
            continue

        c["pos_who"] = {k: (rail_row["who_after"] or {}).get(k)
                        for k in ("tag", "aria", "tid", "node_index")}

        if mode == "armcheck":
            # ⚠️ **不可逆动作放序列最后**：只调 `ARM_FOCUS_JS`、**一个键都不发**
            _wa = ev(WHOAMI_JS, [NODE_SEL])
            _arm = ev(ARM_FOCUS_JS, [NODE_SEL])
            _wb = ev(WHOAMI_JS, [NODE_SEL])
            c["arm_focus_moved_focus"] = bool(identity(
                {"who_before": _wa, "who_after": _wb}))
            c["arm_focus_ok"] = _arm
            c["arm_to"] = stop_name({"who_after": _wb})
            c["one_key_only"] = True
            c["verdict_C"] = (
                "`ARM_FOCUS_JS` 在复刻左栏停靠点上："
                f"{'**会**' if c['arm_focus_moved_focus'] else '**不会**'}动焦点"
                f"（focus_ok={_arm.get('focus_ok') if _arm else None}、"
                f"{stop_name({'who_after': _wa})} → {c['arm_to']}）")
            print(f"      ⇒ {c['verdict_C']}", flush=True)
            dump(out)
            continue

        if mode == "arrow":
            # ⭐ **绕开 `press_row`**（957 查红的那条）⇒ 自己发键、逐字读
            _f0 = ev(FOCUS_JS, [NODE_SEL])
            _w0 = ev(WHOAMI_JS, [NODE_SEL])
            page.keyboard.press(KEY_ARROW)      # ⭐ **只发这一个键**
            page.wait_for_timeout(SETTLE)
            _f1 = ev(FOCUS_JS, [NODE_SEL])
            _w1 = ev(WHOAMI_JS, [NODE_SEL])
            arow = {"phase": "arrow", "k": 0, "step": 1, "key": KEY_ARROW,
                    "seq": c["n_lead"] + 1,
                    "active_before": _f0, "active_after": _f1,
                    "who_before": _w0, "who_after": _w1,
                    "focus_moved": (_f0.get("active_tag"), _f0.get("active_tid"))
                                   != (_f1.get("active_tag"), _f1.get("active_tid")),
                    "bit": False, "n_added": 0, "identity_stable": True,
                    "removed": [], "added": [], "changed": [], "diff_ids": [],
                    "n_without_ti": 0, "armed_before": None, "armed_after": None,
                    "no_ti_before": [], "no_ti_after": [],
                    "no_ti_capped": False, "pointer_before": None,
                    "pointer_after": None}
            c["arrow_row"] = arow
            c["arrow_read_isolation"] = "**绕开 `press_row`**"
            c["pressed_keys"].append(KEY_ARROW)
            c["one_key_only"] = bool(len(c["pressed_keys"]) == 1
                                     and c["pressed_keys"][0] == KEY_ARROW)
            c["arrow_from"] = stop_name({"who_after": _w0})
            c["arrow_to"] = stop_name({"who_after": _w1})
            c["arrow_moved_weak"] = arow["focus_moved"]
            c["arrow_moved_strong"] = strong_moved(arow)
            c["arrow_stayed_in_rail"] = bool(
                (_w1 or {}).get("tid") == RAIL_TID)
            c["verdict_B"] = (
                f"{KEY_ARROW} 在左栏停靠点上：{c['arrow_from']} → "
                f"{c['arrow_to']}，弱={c['arrow_moved_weak']} "
                f"强={c['arrow_moved_strong']} 仍停左栏={c['arrow_stayed_in_rail']}")
            print(f"      ⇒ {c['verdict_B']}", flush=True)
            dump(out)
            continue

        # ── 格 2 `ring`：再走 N_AFTER_RAIL 下，量出**第一圈**的画布段结构 ───
        # ⚠️⚠️ **第一版两个错，都已修**：
        #   ① 它走的是 `press_row` ⇒ 内部 `ARM_FOCUS_JS` **会动焦点**（格 3 实测）
        #      ⇒ `stop_seq` **不可信** ⇒ 这里**自己发 `Tab` + 逐字 `WHOAMI_JS` 读**。
        #   ② 它按满 `N_AFTER_RAIL` 下就统计 ⇒ **走过不止一圈**（40 > 一圈）
        #      ⇒ 「出画布 60 个」是**两圈多**的数 ⇒ 改成**数到第 2 次命中左栏为止**。
        for _ in range(N_AFTER_RAIL):
            c["n_lead"] += 1
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            _w = ev(WHOAMI_JS, [NODE_SEL])
            row = {"phase": "walk", "k": c["n_lead"], "step": 0, "key": "Tab",
                   "seq": c["n_lead"],
                   "active_before": None,
                   "active_after": ev(FOCUS_JS, [NODE_SEL]),
                   "who_before": None, "who_after": _w,
                   "armed_before": None, "armed_after": None,
                   "no_ti_before": [], "no_ti_after": [],
                   "no_ti_capped": False, "pointer_before": None,
                   "pointer_after": None,
                   "focus_moved": True, "bit": False, "n_added": 0,
                   "identity_stable": None, "removed": [], "added": [],
                   "changed": [], "diff_ids": [], "n_without_ti": 0}
            c["rows"].append(row)
            if (_w or {}).get("tid") == RAIL_TID:
                c["n_rail_stops"] += 1
                c["rail_stop_seqs"].append(c["n_lead"])
                if c["n_rail_stops"] >= 2:
                    break            # ⭐ **数到第 2 次命中左栏 = 走满一圈**
        pre = ev(CENSUS_JS, [NODE_SEL])
        c["ring_read_isolation"] = "**绕开 `press_row`**（格 3 实测它会动焦点）"
        c["n_press"] = c["n_lead"]
        # ⭐ 只取**第一圈**：从第 1 个左栏停靠点之前开始、到第 2 个为止
        # ⭐⭐ **窗口是「左闭右开」**（第一版写成 `(rs[0]-1, rs[1]]` ⇒ **两端都含**
        #   ⇒ 把**第 2 个左栏停靠点也数进了这一圈** ⇒ 「左栏 2 个 / 出画布 20 个」，
        #   而真值是 **1 / 19**）⇒ 一圈 = 第 1 个左栏停靠点**含**
        #   到第 2 个**不含**。
        _rs = c["rail_stop_seqs"]
        c["leg_lo"] = _rs[0] if _rs else 1
        c["leg_hi"] = (_rs[1] - 1) if len(_rs) > 1 else c["n_lead"]
        c["leg_stop_seq"] = [stop_name(r) for r in c["rows"]
                             if c["leg_lo"] <= r["seq"] <= c["leg_hi"]]
        c["leg_n_out"] = sum(1 for s in c["leg_stop_seq"]
                             if classify(s) == "out")
        c["leg_n_rail"] = sum(1 for s in c["leg_stop_seq"]
                              if (s or "").startswith("out:文本")
                              or (s or "").startswith("out:图片")
                              or (s or "").startswith("out:视频")
                              or (s or "").startswith("out:音频")
                              or (s or "").startswith("out:时间线")
                              or (s or "").startswith("out:主体")
                              or (s or "").startswith("out:导演台")
                              or (s or "").startswith("out:资产库")
                              or (s or "").startswith("out:上传"))
        c["stop_seq"] = c["leg_stop_seq"]
        kinds = [classify(s) for s in c["leg_stop_seq"]]
        c["n_stops"] = len(c["leg_stop_seq"])
        c["n_node_stops"] = kinds.count("node")
        c["n_inner_stops"] = kinds.count("inner")
        c["n_out_stops"] = c["leg_n_out"]
        c["out_stops"] = [s for s, kd in zip(c["leg_stop_seq"], kinds)
                          if kd == "out"]
        c["left_the_canvas"] = bool(c["n_out_stops"] > 0)
        c["one_key_only"] = True       # 这一格**一个判别键都没发**
        c["verdict_D"] = (
            f"**一圈**（第 {c['leg_lo'] + 1}–{c['leg_hi']} 按）："
            f"**左栏停靠点 {c['leg_n_rail']} 个**、"
            f"出画布 {c['n_out_stops']} 个"
            f"（956 改前是 9 / 27；源站 954 是 1 / 18）")
        print(f"      ⇒ {c['verdict_D']}", flush=True)
        print(f"      一圈的出画布停靠点：{c['out_stops']}", flush=True)
        dump(out)




# ⭐ 两轮比较**必须在循环之外**（955 第一版栽在这上面 ⇒ 第二轮压根没跑）
n_cells = 4
out["n_cells_total"] = n_cells

# ⭐ `_BEHAVIOR` 换成 **958 自己**的字段表（照抄 956 那份会整片 `None` ⇒ 恒真）
_BEHAVIOR = ("mode", "n_rail_buttons", "n_rail_focusable", "n_rail_ti_hist",
             "host_role", "host_aria", "rail_row",
             "n_inserted", "reached_a_rail_stop", "n_rail_stops",
             "rail_stop_seqs", "arrow_from", "arrow_to", "arrow_moved_weak",
             "arrow_moved_strong", "arrow_stayed_in_rail", "one_key_only",
             "pressed_keys", "arrow_read_isolation", "arm_focus_moved_focus",
             "arm_to", "arm_focus_ok", "leg_lo", "leg_hi", "leg_n_out",
             "leg_n_rail", "ring_read_isolation", "cold_without_ti",
             "cold_armed", "n_nodes", "pos_who")

_KEYS = {"census": ("verdict_A", "n_rail_focusable", "n_rail_ti_hist",
                    "rail_row", "host_role", "host_aria"),
         "arrow": ("verdict_B", "arrow_from", "arrow_to", "arrow_moved_weak",
                   "arrow_moved_strong", "arrow_stayed_in_rail",
                   "one_key_only", "arrow_read_isolation", "n_rail_stops"),
         "ring": ("verdict_D", "leg_lo", "leg_hi", "leg_n_out", "leg_n_rail",
                  "leg_stop_seq", "ring_read_isolation"),
         "armcheck": ("verdict_C", "arm_focus_moved_focus", "arm_focus_ok",
                      "arm_to")}

_same = {}
for _j, _m in enumerate(("census", "arrow", "ring", "armcheck")):
    _got = [{k: r["cells"][_j].get(k) for k in _KEYS[_m]}
            for r in out["runs"] if _j < len(r["cells"])]
    _same[_m] = bool(len(_got) == REPS and _got[0] == _got[1])
out["reps_identical"] = _same
out["all_cells_reproducible"] = bool(all(_same.values()))

# ⭐ 非恒真门：`_BEHAVIOR` 至少要有一半的键在格里**真的存在**
# ⚠️⚠️ **第一版这道门是错的**（红）：它拿**一张共用的 `_BEHAVIOR`** 去要求
#   **每一格**都填满一半以上 —— 而 4 格是**异质**的（census 格没有 `arrow_to`、
#   arrow 格没有 `leg_n_out`……）⇒ **结构上永远红** ⇒ 一个**恒假的门**，
#   比没有门更坏（942 的原话）。⇒ **改代码，不放宽门**：
#   逐格**对「本格自己的键表」**判「非恒真」。
_VACUITY = {}
for _j, _m in enumerate(("census", "arrow", "ring", "armcheck")):
    _keys = _KEYS[_m]
    _hit = [sum(1 for k in _keys if k in r["cells"][_j])
            for r in out["runs"] if _j < len(r["cells"])]
    _VACUITY[_m] = bool(_hit and min(_hit) >= max(2, len(_keys) // 2))
out["vacuity_by_cell"] = _VACUITY
out["behavior_gate_non_vacuous"] = bool(all(_VACUITY.values()))

# ⭐ 「操纵到底动了没有」：格 1 的 `ArrowDown` **必须真的动了**
_arrows = [r["cells"][1].get("arrow_moved_strong") for r in out["runs"]
           if len(r["cells"]) > 1 and "skipped" not in r["cells"][1]]
out["ruler_actually_moved"] = bool(_arrows and all(_arrows))

out["design_gates"] = {
    "js_py_verbatim_from_956": True,      # 文件级 assert 过了才会跑到这
    "classify_verbatim_from_954": True,
    "rail_js_verbatim_from_957": True,
    "zero_button_clicks": bool(all(
        not r["cells"][j].get("clicked_rail")
        for r in out["runs"] for j in range(n_cells) if j < len(r["cells"]))),
    "ruler_actually_moved": out["ruler_actually_moved"],
    "all_cells_reproducible": out["all_cells_reproducible"],
    "behavior_gate_non_vacuous": out["behavior_gate_non_vacuous"],
    # ⭐⭐ 本批的**验收判据**（改前 vs 改后，**关系式**）
    "rail_focusable_is_1": bool(all(
        r["cells"][0].get("n_rail_focusable") == 1
        for r in out["runs"] if len(r["cells"]) > 0)),
    "rail_ti_hist_is_0x1_neg1x8": bool(all(
        (r["cells"][0].get("n_rail_ti_hist") or {}).get("0") == 1
        and (r["cells"][0].get("n_rail_ti_hist") or {}).get("-1") == 8
        for r in out["runs"] if len(r["cells"]) > 0)),
    "arrow_stays_in_rail": bool(all(
        r["cells"][1].get("arrow_stayed_in_rail") is True
        for r in out["runs"] if len(r["cells"]) > 1
        and "skipped" not in r["cells"][1])),
    "arrow_moved_strong": bool(all(
        r["cells"][1].get("arrow_moved_strong") is True
        for r in out["runs"] if len(r["cells"]) > 1
        and "skipped" not in r["cells"][1])),
    "one_lap_rail_stop_is_1": bool(all(
        r["cells"][2].get("leg_n_rail") == 1
        for r in out["runs"] if len(r["cells"]) > 2
        and "skipped" not in r["cells"][2])),
    # ⚠️ **可红、且是本批要报的那条**：`ARM_FOCUS_JS` 在**复刻**左栏也动焦点
    "arm_focus_is_noop_at_rail": bool(all(
        r["cells"][3].get("arm_focus_moved_focus") is False
        for r in out["runs"] if len(r["cells"]) > 3
        and "skipped" not in r["cells"][3])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                    "active_tag", "focus_in_node", "no_ti",
                                    "aria", "node_index", "armed", "seq",
                                    "rail_ti", "rail_aria", "rail_focusable",
                                    "n_rail_buttons", "host_role"))),
}
out["design_gates_note"] = (
    "⚠️ `arm_focus_is_noop_at_rail` **红**：957 在**源站**查红的那条，"
    "**在复刻侧同样成立**（实测 `out:文本 → node#6`）⇒ 本批所有需要"
    "「按完键焦点在哪」的读数都**绕开 `press_row`**，不用它读 `who_after`。")
print("\n设计门：", out["design_gates"], flush=True)
print("两轮相同（逐格）：", out["reps_identical"], flush=True)
for r in out["runs"]:
    for c in r["cells"]:
        if "skipped" in c:
            print(f"rep{r['rep']} 格{c['ci']}（{c['mode']}）：⚠️ {c['skipped']}",
                  flush=True)
            continue
        v = (c.get("verdict_A") or c.get("verdict_B") or c.get("verdict_D")
             or c.get("verdict_C"))
        print(f"rep{r['rep']} 格{c['ci']}（{c['mode']}）：{v}", flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)

