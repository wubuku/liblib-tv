#!/usr/bin/env python3
r"""batch 957 源站探针（**纯诊断 / 零节点点击**）：⭐⭐⭐⭐ 查「左栏那 9 个按钮，源站到底给几个 `Tab` 停靠点」。

## 本批只答一件事：**源站左栏是「9 个 Tab 停靠点」还是「1 个 + 方向键在栏内移动」**

956/956b 在**复刻侧**量到：左栏 `canvas-fixed-toolbar` 的 **9 个按钮
（`文本`/`图片`/`视频`/`音频`/`时间线`/`主体`/`导演台`/`资产库`/`上传`）
每一个都是一个独立的 `Tab` 停靠点**，连排 9 下。
而 954 在**源站**那一侧量到：整个出画布段（18 个停靠点）里
`tid == 'canvas-fixed-toolbar'` 的**只有 1 个**（`out:文本`，seq=84，2/2 逐轮相同）。

⇒ ⚠️⚠️⚠️ **这是一个待查的差异，而且它很可能就是「环权重差异」的成因**：
源站左栏只贡献 1 个停靠点、复刻贡献 9 个 ⇒ 出画布段 18 vs 27（净 +9）
⇒ **956b 那句「复刻多出 10 个、其中左栏 8 个」** 正是这 9 个里的 8 个。

## ⭐ 两种可能，**必须分开**，不许混着报

| 假设 | 判据 | 若为真 |
| --- | --- | --- |
| **A. 源站左栏只有 1 个按钮可聚焦**（其余 8 个 `tabindex` 被摘掉或压根不可聚焦） | 普查每一枚按钮的 `tabindex` 属性 | ⇒ 复刻把 8 个本该不可聚焦的按钮做成了可聚焦 |
| **B. 源站左栏是 ARIA roving toolbar**（`role="toolbar"` + 栏内**方向键**移动，WAI-ARIA 的标准模式） | 焦点在左栏那**一个**停靠点上时按 `ArrowDown`/`ArrowUp`，看焦点动不动 | ⇒ 复刻缺了「方向键在栏内移动」这一整套交互 |

⇒ **本批两格各测一个假设**，互不代替。

## 零、这一批为什么**必须纯读**

- ⚠️ **不点任何按钮**：左栏按钮点下去会**插入节点**（复刻侧是 `insertAtCenter`）、
  源站侧会开面板 ⇒ **点击会改变被测对象** ⇒ 普查一律走
  `document.querySelectorAll` + 取属性，**零点击**。
- ⚠️ 只点**一次画布空白**去焦点（943 起的标准前置），⛔ 守卫拦在 `mouse.click` **之前**。
- ⚠️ 按键只有 `Tab` / `Shift+Tab` / `ArrowDown` / `ArrowUp`。

## 一、尺子

- **七段 JS 与 17 个 Python 助手逐字复用 955**（955 又与 954/953 逐字相同 ⇒ 链式）
  ⇒ **零新件仪器**；`classify` 对着 954
- `boot_fn` **逐字来自 952**（就绪判据两边不能换，换了读数不可比）
- 新件只有 **`RAIL_JS`（普查用，不是仪器）** + 格子驱动器

## 二、两格

| 格 | 做什么 | 测的是 |
| --- | --- | --- |
| **格 0** `census` | 普查左栏每一枚按钮的 `tabindex`/`aria`/`role`/可聚焦性 | **假设 A** |
| **格 1** `arrow` | 走到左栏那**一个**停靠点上，**只发一个** `ArrowDown` | **假设 B** |

⚠️ 格 1 的引导是**关系式**的：一直按 `Tab`，数着「这是第几个 `tid ==
'canvas-fixed-toolbar'` 的停靠点」，数到就**停** ⇒ **不需要钉绝对按压数**
（901 `6→20`、953 `14→24→28`、954 `14→120`、956 `28→120` 全是同一类）。
`N_PRESS_CAP` 只是**硬上限**，触顶**如实记**、**不下结论**。

## 三、五道门（**全部可红**）

1. `js_py_verbatim_from_955` —— 尺子没跑偏（文件级 assert）
2. `classify_verbatim_from_954` —— 停靠点分类没换口径
3. `ruler_actually_moved` —— **「操纵到底动了没有」必须自己答**
4. `reached_a_rail_stop` —— ⭐ **「我没检测到」必须先确认「我够得着」**：
   格 1 若压根没走到左栏停靠点 ⇒ **那一格什么也没测**，如实记、**不下结论**
5. `keys_disjoint` / `raw_keys_registered` —— 935 的两道免疫针

## 四、探针自带的纪律（承 943→956）

1. ⭐ 尺子自证：每段退出前 `pre = cur`
2. ⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）
3. ⭐ 派生键不许与原始键重叠/重名/漏登记
4. ⭐ 守卫常量自己必须能匹配上东西
5. ⭐ 新件不许混进「逐字相同」那组
6. ⭐ **写推断之前先查基线里有没有反例**（951/953 各栽一次）
7. ⚠️ 落盘排在所有后处理之前
8. ⚠️ 不可逆动作放序列最后

## 计费边界

**本批零计费动作。** 只发一次画布空白点击去焦点，⛔ 守卫拦在 `mouse.click` **之前**。
键盘**有可能**走到计费入口上（889d 记过键盘可达性本身是风险面）⇒ 但本批
**只发按键、不点任何东西**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe957_rail_roving_src.py
"""

import json
import pathlib
import textwrap

OUT = "/tmp/b957-rail-roving.json"
REPS = 2
SETTLE = 350        # ms（照 952/953/954/955/956）
BLANK_WAIT = 900    # ms（照 952/953/954/955/956）
NO_TI_CAP = 40      # 照 952/953/954/955/956
# ⚠️ **硬上限，不是目标**。引导是关系式的（数到第 1 个左栏停靠点就停）⇒
#   真实用到的按压数由画布多大决定。源站节点 ~77 ⇒ 实测约 84 下。
N_PRESS_CAP = 120
RAIL_TID = "canvas-fixed-toolbar"      # ⭐ 两边共用的锚点（复刻侧逐字相同）
KEY_ARROW = "ArrowDown"                # ⭐ 格 1 **只发这一个键**

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")
P955 = pathlib.Path(__file__).with_name("jimeng_probe955_onekey_inner_src.py")
P954 = pathlib.Path(__file__).with_name("jimeng_probe954_source_ring_src.py")
P952 = pathlib.Path(__file__).with_name("jimeng_probe952_freeze_who_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "no_ti",
    "no_ti_capped", "active_tag", "active_tid", "focus_in_node", "blank",
    "point", "i", "k", "hit_tag", "focus_ok", "seq",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who", "armed", "armed_before", "armed_after",
    # ⭐ 本批新增的**原始**读数（普查逐字取回，不加工）
    "rail_ti", "rail_aria", "rail_role", "rail_tag", "rail_disabled",
    "rail_focusable", "rail_tabindex_raw", "n_rail_buttons", "host_role",
    "host_aria", "host_tabindex",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "ci", "mode", "rows", "cell_ok", "reps_identical", "design_gates",
    "ruler_actually_moved", "cold_without_ti", "cold_armed", "pointer_seq",
    "stop_seq", "n_stops", "n_node_stops", "n_inner_stops", "n_out_stops",
    "left_the_canvas", "wrap_k", "cycle_len", "out_stops", "repeat_node_at",
    "n_press", "n_lead", "n_lead_cap_hit", "skipped",
    # ⭐ 本批的派生量
    "census", "n_rail_ti_hist", "n_rail_focusable", "n_rail_no_ti",
    "rail_row", "n_rail_stops", "rail_stop_seqs", "reached_a_rail_stop",
    "n_rail_stops_cap_hit", "arrow_row", "arrow_moved_weak", "arrow_moved_strong",
    "arrow_from", "arrow_to", "arrow_from_class", "arrow_to_class",
    "arrow_stayed_in_rail", "arrow_left_rail", "one_key_only", "pressed_keys",
    "arm_focus_moved_focus", "arm_focus_ok", "arrow_read_isolation",
    "arm_to", "arm_who_before", "arm_who_after", "verdict_C",
    "walk_who_before",
    "reps_identical_census", "reps_identical_arrow",
    "replica_rail_n_from_956", "verdict_A", "verdict_B", "design_gates_note",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "census", "reached_a_rail_stop", "ruler_actually_moved",
              "one_key_only", "n_rail_stops", "arrow_moved_strong"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index", "armed", "seq",
             "rail_ti", "rail_aria", "rail_focusable", "n_rail_buttons"):
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
assert _p955src, "读不到 955 的源码 —— 尺子没得比，这道门恒绿"
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS", "WHOAMI_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL
                      + (WHOAMI_JS,)):
    assert _js in _p955src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 955 那份**不一致** —— 两份尺子开始分家了")

# ── 逐字复用 955 的助手（OUT 换成本批自己的）──────────────────────────
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


# ⭐⭐ 助手也逐字对着 955 的**文件内容** assert（`classify` 对着 954）
for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,
            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,
            strong_moved, identity, stop_name, walk_stuck):
    _s = textwrap.dedent(__import__("inspect").getsource(_fn)).strip()
    assert _s in _p955src, (
        f"{_fn.__name__} 与 955 那份**不一致** —— 尺子的 Python 侧也开始分家了")
    del _s
_cs = textwrap.dedent(
    __import__("inspect").getsource(classify)).strip()
_p954src = P954.read_text(encoding="utf-8") if P954.exists() else ""
assert _p954src, "读不到 954 的源码 —— classify 没得比，这道门恒绿"
assert _cs in _p954src, "classify 与 954 那份**不一致** —— 停靠点分类换了口径"
del _cs

# ── 新件：`RAIL_JS`（**普查用，不是仪器**）──────────────────────────────
# ⚠️ 为什么普查 `el.focusable` 而不是直接调 `el.focus()`：**调 focus 会改变
#   焦点** ⇒ 污染后面「焦点在哪」的读数 ⇒ 本批的普查必须**纯读**。
#   `focusable` 的口径：原生可聚焦元素（BUTTON/A/INPUT/…）且未被 `disabled`、
#   且没有被 `tabindex="-1"` 摘出**顺序**。⚠️ 真实可聚焦性最终由**格 1 的
#   `ArrowDown` 实测**兜底（`Tab` 能不能走到它，是**行为**，不是属性）。
RAIL_JS = """([tid, nodeSel]) => {
  const host = document.querySelector('[data-testid="' + tid + '"]');
  if (!host) return {found: false};
  const NATIVE = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
  const rows = Array.from(host.querySelectorAll('*')).map((el) => {
    const tag = (el.tagName || '').toUpperCase();
    const tiRaw = el.getAttribute('tabindex');
    const ti = el.hasAttribute('tabindex') ? tiRaw : null;
    const dis = el.disabled === true;
    const native = NATIVE.indexOf(tag) >= 0;
    // ⚠️ 「顺序里可聚焦」= 原生可聚焦 ∧ 未 disabled ∧ tabindex 不是 -1
    const orderable = native && !dis && ti !== '-1';
    return {tag: tag,
            aria: el.getAttribute('aria-label') || el.getAttribute('title')
                  || (el.innerText || '').slice(0, 20) || null,
            role: el.getAttribute('role'),
            ti: ti,
            ti_raw: tiRaw,
            disabled: dis,
            focusable: orderable,
            in_node: !!el.closest(nodeSel)};
  }).filter((r) => r.tag !== 'SVG' && r.tag !== 'PATH' && r.tag !== 'G');
  const tiHist = {};
  rows.forEach((r) => {
    const k = r.ti === null ? 'None' : r.ti;
    tiHist[k] = (tiHist[k] || 0) + 1;
  });
  return {found: true,
          host_role: host.getAttribute('role'),
          host_aria: host.getAttribute('aria-label'),
          host_tabindex: host.hasAttribute('tabindex')
                         ? host.getAttribute('tabindex') : null,
          n_rail_buttons: rows.filter((r) => r.tag === 'BUTTON').length,
          rows: rows,
          ti_hist: tiHist,
          n_focusable: rows.filter((r) => r.focusable).length,
          n_no_ti: rows.filter((r) => r.ti === null).length};
}"""
assert "RAIL_JS" not in _p955src, "957 的新件别混进「逐字相同」那组"
assert RAIL_JS.count("slice(") == RAIL_JS.count(SLICE_STR), (
    "RAIL_JS 里有**非字符串**切片（§131）")


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
_bs = textwrap.dedent(__import__("inspect").getsource(boot_fn)).strip()
assert _bs in _p952src, "boot_fn 与 952 那份**不一致** —— 就绪判据换了就读数不可比"
del _bs

URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {
    "target": "source", "url": URL, "reps": REPS,
    "rail_tid": RAIL_TID, "key_arrow": KEY_ARROW,
    "n_press_cap": N_PRESS_CAP, "no_ti_cap": NO_TI_CAP,
    "forbidden_tids": list(FORBIDDEN_TIDS),
    "question": "源站左栏 `canvas-fixed-toolbar` 的 9 个按钮，`Tab` 到底给"
                "几个停靠点？954 只看到 1 个（seq=84）⇒ 是「8 个不可聚焦」"
                "还是「ARIA roving、方向键在栏内移动」？",
    "ruler": {
        "js_verbatim_from_955": ["BLANK_JS", "CENSUS_JS", "NO_TI_JS",
                                 "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS",
                                 "WHOAMI_JS"],
        "py_verbatim_from_955": ["ev", "dump", "guard", "guard_point",
                                 "delta", "press_row", "curve_key",
                                 "armed_of", "no_ti_of", "pointer_of",
                                 "row_pointer", "in_toolbar", "strong_moved",
                                 "identity", "stop_name", "walk_stuck"],
        "verbatim_from_954": ["classify"],
        "verbatim_from_952": ["boot_fn"],
        "new_pieces": ["RAIL_JS"],   # ⭐ **普查用，不是仪器**
        "why_not_instrument": "RAIL_JS 只**读属性**、不调 `focus()` ⇒ "
                              "不污染「焦点在哪」的读数",
    },
    "baseline": {
        "source_954_out_stops_per_cycle": 18,
        "source_954_rail_stops": 1,
        "source_954_rail_stop_seq": 84,
        "source_954_rail_stop_aria": "文本",
        "replica_956_rail_stops_per_cycle": 9,
        "replica_956_rail_arias": ["文本", "图片", "视频", "音频", "时间线",
                                   "主体", "导演台", "资产库", "上传"],
        "replica_956_out_stops_per_cycle": 27,
        "note": "⚠️ 954 那个 1 是 **2/2 逐轮相同**的（rep1 seq=84、rep2 seq=84）"
                "⇒ 不是漏测；⚠️ 但 954 **只**数了停靠点、**没**普查过那 9 "
                "枚按钮各自的 `tabindex` ⇒ **本批就是补那一格**",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    for ci, mode in enumerate(("census", "arrow", "armcheck")):
        tag = ("普查左栏 9 枚按钮的 tabindex/aria/role（**零点击**）"
               if mode == "census"
               else f"走到左栏停靠点上，**只发一个** {KEY_ARROW}")
        print(f"  --- 格 {ci}（{tag}）---", flush=True)
        n = boot_fn()
        c = {"ci": ci, "mode": mode, "n_ready": n, "rows": [],
             "pressed_keys": []}
        rec["cells"].append(c)
        dump(out)
        print(f"      就绪：左栏入口数={n}", flush=True)
        if n == 0:
            c["skipped"] = "左栏入口没出来（`button[aria-label=音频]` 为 0）"
            continue

        # ── 普查（**两格都做**：它是「我够得着吗」的前置，不是格 0 的专属）──
        cen = ev(RAIL_JS, [RAIL_TID, NODE_SEL])
        c["census"] = cen
        c["n_rail_buttons"] = cen.get("n_rail_buttons")
        c["n_rail_focusable"] = cen.get("n_focusable")
        c["n_rail_no_ti"] = cen.get("n_no_ti")
        c["n_rail_ti_hist"] = cen.get("ti_hist")
        c["host_role"] = cen.get("host_role")
        c["host_aria"] = cen.get("host_aria")
        c["host_tabindex"] = cen.get("host_tabindex")
        c["rail_row"] = [
            {"tag": r["tag"], "aria": r["aria"], "role": r["role"],
             "rail_ti": r["ti"], "rail_ti_raw": r["ti_raw"],
             "rail_disabled": r["disabled"], "rail_focusable": r["focusable"]}
            for r in (cen.get("rows") or []) if r["tag"] == "BUTTON"]
        print(f"      普查：host role={cen.get('host_role')!r} "
              f"aria={cen.get('host_aria')!r} ti={cen.get('host_tabindex')!r}；"
              f"按钮 {cen.get('n_rail_buttons')} 枚、"
              f"顺序里可聚焦 {cen.get('n_focusable')} 枚、"
              f"ti 分布 {cen.get('ti_hist')}", flush=True)
        for r in c["rail_row"]:
            print(f"        · {r['aria']!r:16s} ti={r['rail_ti']!r:6s} "
                  f"focusable={r['rail_focusable']}", flush=True)
        dump(out)

        if mode == "census":
            c["verdict_A"] = (
                "源站左栏顺序里可聚焦的按钮数 = "
                f"{cen.get('n_focusable')}（共 {cen.get('n_rail_buttons')} 枚）")
            print(f"      ⇒ 假设 A 读数：{c['verdict_A']}", flush=True)
            dump(out)
            continue

        # ── 格 1/2：引导到左栏停靠点上 ──────────────────────────────────
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

        c["n_lead"] = 0
        c["n_lead_cap_hit"] = False
        c["n_rail_stops"] = 0
        c["rail_stop_seqs"] = []
        reached = False
        while c["n_lead"] < N_PRESS_CAP:
            c["n_lead"] += 1
            row, pre = press_row(page, pre, "Tab", c["n_lead"], "walk", 0)
            row["seq"] = c["n_lead"]
            row["armed_before"] = armed_of(pre["ti"])
            c["rows"].append(row)
            tid = (row["who_after"] or {}).get("tid")
            if tid == RAIL_TID:
                c["n_rail_stops"] += 1
                c["rail_stop_seqs"].append(c["n_lead"])
                c["rail_row"] = c.get("rail_row") or None
                c["reached_a_rail_stop"] = True
                print(f"      [Tab {c['n_lead']:>3}] ⭐左栏停靠点："
                      f"{stop_name(row)}", flush=True)
                reached = True
                break
            dump(out)
        else:
            c["n_lead_cap_hit"] = True
        if not reached:
            c["skipped"] = (f"按了 {c['n_lead']} 下都没走到 `{RAIL_TID}` "
                            "停靠点 ⇒ **这一格什么也没测**，不下结论")
            c["reached_a_rail_stop"] = False
            print(f"      ⚠️ {c['skipped']}", flush=True)
            dump(out)
            continue

        # 位置门：**按之前**焦点真的在左栏那枚按钮上，并记下身份
        pos = (row["who_after"] or {})
        c["reached_a_rail_stop"] = bool(pos.get("tid") == RAIL_TID)
        # ⚠️⚠️⚠️ **标签不许指向错的按**（第一版栽在这上面）：
        #   `row` 是**引导行走**里命中左栏的那一按，`row["who_before"]` 是
        #   **上一按之前**的焦点（`node#75`）—— **不是**「`ArrowDown` 之前」的焦点。
        #   ⇒ 标签必须取 `pos`（= `row["who_after"]`，也就是 `ArrowDown` 之前
        #   真实的焦点），并**同时**把 `row["who_before"]` 另存为
        #   `walk_who_before`，免得下一个人再拿它当「按之前」。
        c["walk_who_before"] = stop_name(row, "before")
        c["arrow_from"] = stop_name({"who_after": pos}) or stop_name(row)
        c["arrow_from_class"] = classify(c["arrow_from"])
        # ⭐⭐⭐⭐ **判别键这一按**必须**绕开 `press_row`**（第一版栽在这上面）：
        #   `press_row` 按完键之后会调 `ARM_FOCUS_JS`，而它**带 `el.focus()`**
        #   ⇒ 它**会把焦点从左栏那枚按钮拽回画布节点** ⇒ 而 `who_after`
        #   是在**它之后**读的 ⇒ ⚠️⚠️ **第一版实测就是这样坏的**：
        #   自检那一步把焦点拽到了 `node#75`，随后 `ArrowDown` **是在
        #   `node#75` 上按的** ⇒ 读出来 `node#75 → node#75`
        #   ⇒ **那一格什么也没测到**（不是「`ArrowDown` 不动焦点」！）
        # ⇒ 这里**逐字复用 955 的 `FOCUS_JS`/`WHOAMI_JS`** 自己发键自己读，
        #   **不调 `ARM_FOCUS_JS`** ⇒ 读数不被仪器污染。
        #   ⚠️ 尺子自检（`ARM_FOCUS_JS` 到底动不动焦点）**另起一格 `armcheck`**
        #   ⇒ **不可逆动作放序列最后**（它会永久改变焦点状态）。
        _f0 = ev(FOCUS_JS, [NODE_SEL])
        _w0 = ev(WHOAMI_JS, [NODE_SEL])
        page.keyboard.press(KEY_ARROW)          # ⭐ **只发这一个键**
        page.wait_for_timeout(SETTLE)
        _f1 = ev(FOCUS_JS, [NODE_SEL])
        _w1 = ev(WHOAMI_JS, [NODE_SEL])
        pre = ev(CENSUS_JS, [NODE_SEL])
        arow = {"phase": "arrow", "k": 0, "step": 1, "key": KEY_ARROW,
                "seq": c["n_lead"] + 1,
                "active_before": _f0, "active_after": _f1,
                "who_before": _w0, "who_after": _w1,
                "focus_moved": (_f0.get("active_tag"), _f0.get("active_tid"))
                               != (_f1.get("active_tag"), _f1.get("active_tid")),
                "bit": False, "n_added": 0, "identity_stable": True,
                "removed": [], "added": [], "changed": [], "diff_ids": [],
                "n_without_ti": pre["n_without_ti"],
                "armed_before": None, "armed_after": None,
                "no_ti_before": [], "no_ti_after": [],
                "no_ti_capped": False, "pointer_before": None,
                "pointer_after": pointer_of(pre["ti"])}
        c["arrow_read_isolation"] = ("**绕开 `press_row`**，自己发键 + "
                                     "逐字 `FOCUS_JS`/`WHOAMI_JS` 读")
        arow["seq"] = c["n_lead"] + 1
        if mode == "armcheck":
            # ── 格 2：**只调 `ARM_FOCUS_JS`、不发任何键** ─────────────────
            # ⚠️ 这一格是**不可逆动作**（`el.focus()` 会永久改焦点状态）
            #   ⇒ ⭐ **不可逆动作放序列最后** ⇒ 它排在格 1 之后。
            # ⚠️ 目的：验 954/955/956 那把尺子隐含的前提 ——
            #   「`press_row` 读 `who_after` 时，`ARM_FOCUS_JS` 不会动焦点」。
            _wa = ev(WHOAMI_JS, [NODE_SEL])
            _arm = ev(ARM_FOCUS_JS, [NODE_SEL])
            _wb = ev(WHOAMI_JS, [NODE_SEL])
            c["arm_focus_moved_focus"] = bool(identity(
                {"who_before": _wa, "who_after": _wb}))
            c["arm_focus_ok"] = _arm
            c["arm_who_before"] = _wa
            c["arm_who_after"] = _wb
            c["arm_to"] = stop_name({"who_after": _wb})
            c["one_key_only"] = True      # 这一格**一个键都没发**
            c["verdict_C"] = (
                "`ARM_FOCUS_JS` 在左栏停靠点上："
                f"{'**会**' if c['arm_focus_moved_focus'] else '**不会**'}动焦点"
                f"（focus_ok={_arm.get('focus_ok') if _arm else None}、"
                f"{c['arrow_from']} → {c['arm_to']}）")
            print(f"      ⇒ {c['verdict_C']}", flush=True)
            dump(out)
            continue

        c["arrow_row"] = arow
        c["pressed_keys"].append(KEY_ARROW)
        c["one_key_only"] = bool(len(c["pressed_keys"]) == 1
                                 and c["pressed_keys"][0] == KEY_ARROW)
        c["arrow_moved_weak"] = arow["focus_moved"]
        c["arrow_moved_strong"] = strong_moved(arow)
        c["arrow_to"] = stop_name(arow, "after")
        c["arrow_to_class"] = classify(c["arrow_to"])
        after = arow["who_after"] or {}
        c["arrow_stayed_in_rail"] = bool(after.get("tid") == RAIL_TID)
        c["arrow_left_rail"] = bool(c["reached_a_rail_stop"]
                                    and not c["arrow_stayed_in_rail"])
        c["verdict_B"] = (
            f"{KEY_ARROW} 在左栏停靠点上：弱={c['arrow_moved_weak']} "
            f"强={c['arrow_moved_strong']} "
            f"仍停左栏={c['arrow_stayed_in_rail']} "
            f"（{c['arrow_from']} → {c['arrow_to']}）")
        print(f"      ⇒ 假设 B 读数：{c['verdict_B']}", flush=True)
        dump(out)

# ⭐ 两轮比较**必须在循环之外**（955 第一版栽在这上面）
n_cells = 3
out["n_cells_total"] = n_cells

_census_same, _arrow_same, _arm_same = [], [], []
for j in range(n_cells):
    got = [{"census_ti_hist": r["cells"][j].get("n_rail_ti_hist"),
            "census_focusable": r["cells"][j].get("n_rail_focusable"),
            "census_buttons": r["cells"][j].get("n_rail_buttons"),
            "census_rail_row": r["cells"][j].get("rail_row"),
            "census_host": [r["cells"][j].get("host_role"),
                            r["cells"][j].get("host_aria"),
                            r["cells"][j].get("host_tabindex")]}
           for r in out["runs"] if j < len(r["cells"])]
    if j == 0:
        _census_same.append(bool(len(got) == REPS and got[0] == got[1]))
    elif j == 1:
        got2 = [{"verdict_B": r["cells"][j].get("verdict_B"),
                 "from": r["cells"][j].get("arrow_from"),
                 "to": r["cells"][j].get("arrow_to"),
                 "strong": r["cells"][j].get("arrow_moved_strong"),
                 "stayed": r["cells"][j].get("arrow_stayed_in_rail"),
                 "one_key_only": r["cells"][j].get("one_key_only"),
                 "n_rail_stops": r["cells"][j].get("n_rail_stops")}
                for r in out["runs"] if j < len(r["cells"])]
        _arrow_same.append(bool(len(got2) == REPS and got2[0] == got2[1]))
    else:
        got3 = [{"verdict_C": r["cells"][j].get("verdict_C"),
                 "arm_moved": r["cells"][j].get("arm_focus_moved_focus"),
                 "arm_ok": r["cells"][j].get("arm_focus_ok"),
                 "arm_to": r["cells"][j].get("arm_to")}
                for r in out["runs"] if j < len(r["cells"])]
        _arm_same.append(bool(len(got3) == REPS and got3[0] == got3[1]))
out["reps_identical_census"] = _census_same
out["reps_identical_arrow"] = _arrow_same
out["reps_identical_arm"] = _arm_same

_firsts = [r["cells"][j]["rows"][0] for r in out["runs"]
           for j in range(n_cells) if j < len(r["cells"])
           and r["cells"][j].get("rows")]
out["ruler_actually_moved"] = bool(
    _firsts and all(r["focus_moved"] or strong_moved(r) or r["bit"]
                    for r in _firsts))
out["reached_a_rail_stop"] = [
    r["cells"][j].get("reached_a_rail_stop") for r in out["runs"]
    for j in (1, 2) if len(r["cells"]) > j]

out["design_gates"] = {
    "js_py_verbatim_from_955": True,   # 文件级 assert 过了才会跑到这
    "classify_verbatim_from_954": True,
    "boot_fn_verbatim_from_952": True,
    "zero_button_clicks": bool(all(
        not r["cells"][j].get("clicked_rail")
        for r in out["runs"] for j in range(n_cells) if j < len(r["cells"]))),
    "ruler_actually_moved": out["ruler_actually_moved"],
    # ⭐⭐⭐ 957 特有：**尺子自检**红 ⇒ 格 1 的 `who_after` **不可信**
    "arm_focus_is_noop_at_rail": bool(all(
        r["cells"][2].get("arm_focus_moved_focus") is False
        for r in out["runs"] if len(r["cells"]) > 2
        and "skipped" not in r["cells"][2])),
    "census_reproducible": bool(_census_same and all(_census_same)),
    "arrow_reproducible": bool(_arrow_same and all(_arrow_same)),
    "arm_reproducible": bool(_arm_same and all(_arm_same)),
    # ⭐⭐ 格 1 的读数**必须**是「绕开 press_row」读出来的
    "arrow_read_isolated": bool(all(
        r["cells"][1].get("arrow_read_isolation") is not None
        for r in out["runs"] if len(r["cells"]) > 1
        and "skipped" not in r["cells"][1])),
    "one_key_only": bool(all(
        r["cells"][j].get("one_key_only") is True
        for r in out["runs"] for j in (1, 2)
        if len(r["cells"]) > j and "skipped" not in r["cells"][j])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    "raw_keys_registered": bool(
        all(k in RAW_KEYS for k in ("bit", "identity_stable", "n_without_ti",
                                    "active_tag", "focus_in_node", "no_ti",
                                    "aria", "node_index", "armed", "seq",
                                    "rail_ti", "rail_aria", "rail_focusable",
                                    "n_rail_buttons", "host_role"))),
}
out["design_gates_note"] = (
    "⚠️ `reached_a_rail_stop` **可红**：格 1 若压根没走到左栏停靠点 ⇒ "
    "**那一格什么也没测** ⇒ 如实记、**不下结论**（不拿「没检测到」当「没有」）。")
print("\n设计门：", out["design_gates"], flush=True)
print("两轮相同（普查/ArrowDown/ARM自检）：", out["reps_identical_census"],
      out["reps_identical_arrow"], out["reps_identical_arm"], flush=True)
for r in out["runs"]:
    for c in r["cells"]:
        if "skipped" in c:
            print(f"rep{r['rep']} 格{c['ci']}（{c['mode']}）：⚠️ {c['skipped']}",
                  flush=True)
            continue
        v = (c.get("verdict_A") or c.get("verdict_B") or c.get("verdict_C"))
        print(f"rep{r['rep']} 格{c['ci']}（{c['mode']}）：{v}", flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
