#!/usr/bin/env python3
r"""batch 953 复刻侧对照探针：⭐⭐⭐⭐ 把 952 那把尺子搬到**复刻**上量一遍。

## 为什么要做这一批

940~952 连续十三批都只在**源站**取样，结论全停在基线里。952 刚把「冻住」拆成
「`Tab` 正常走完了工具条的 4 个按钮」，并给出两条**可实现的**读数：

- 指针**只在「从节点本体 `DIV` 出发的那一按」上 +1**（工具条那 4 下一次都不 +）
- `Tab` 周期 = **节点数 + 带工具条的节点数**（源站那一版 9 + 1 = 10）

⇒ **复刻侧到底有没有这两条？** 本批就去量。**不是**再取一次样，是**验收**。

## ⭐ 本批的设计：同一把尺子，唯一变化是「量谁」

- **七段 JS 全部逐字复用 952**（`BLANK_JS` / `CENSUS_JS` / `NO_TI_JS` /
  `POINT_JS` / `FOCUS_JS` / `ARM_FOCUS_JS` / `WHOAMI_JS`）⇒ 本批**零**新件 JS
- **七个 Python 助手也逐字复用 952**（`ev` / `dump` / `guard` / `guard_point` /
  `delta` / `press_row` / `curve_key`），用 `inspect.getsource` 对着 952 的
  **文件内容** assert ⇒ **改一个字就红**
  （⚠️ 这条纪律反过来救了本批：`press_row` 第一版被我塞了 2 行新字段 ⇒
  自己把自己判红了 ⇒ 才发现指针根本不用新仪器，见下）
- 两格设计**照抄 952**：格 0 = `Tab` × **14**；格 1 = `Tab` × **4** 到冻结点，
  再依次跑 `Shift+Tab` → `Tab` → `ArrowDown` → `Escape` → `Tab` × 3
- 唯一自变量 = **URL**（源站 → 本地复刻）

## ⭐ 指针的两种口径（**这件事必须写出来，不许糊过去**）

源站的指针是「**没有 `tabindex` 属性**的那个下标」；复刻的 `armAll` 写的是
`'0'` / `'-1'`，**属性一直都在** ⇒ `NO_TI_JS` 在复刻上**恒为空**，
源站那把尺子**读不出复刻的指针**。

⇒ 但**不需要另加仪器**：`CENSUS_JS` 已经把每个节点的 `ti` 带回来了。
两个口径都从**同一份** `ti` 派生：

- `armed` = 那些 `ti == '0'` 的下标（**复刻**的指针就是它）
- `no_ti`  = 那些 `ti is None` 的下标（**源站**的指针就是它）

⇒ 「指针」统一定义成 `no_ti[0] if no_ti else armed[0]`：**同一件事的两种口径**，
不是两个现象；两个都为空时记 `None`（仪器读不懂的形状，**不许**当成 0）。
⚠️ 这**不是**「判据不同就量出了不同」（890c 的教训），是尺子那头读不出东西
所以必须换一头，而换的那头**仍然是同一段 JS 带回来的数据**。

## 固定前置（两格**完全一样**，不引入自变量）

照 901 的办法插 5 个节点（`文本` / `图片` / `时间线` / `主体` / `导演台`）——
环够长、且**含一个时间线节点**（源站那一版只有时间线节点带工具条）。
⚠️ 插节点走**左栏入口**、不是节点本体 ⇒ `zero_node_clicks` 这道门仍然成立。

## 复刻侧的结构事实（**开跑前的纯读取影**，不是判据）

- 复刻 demo **自带 2 个 video 节点**；节点带 `data-testid="rf__node-<id>"`、
  **不带 `tabindex`**（中性态）⇒ 与 §130 一致
- 画布根 `.react-flow` 带 `aria-label="Canvas"` / `role="application"` /
  `tabindex="0"` / `data-testid="rf__wrapper"` ⇒ 与 889d 一致
- ⚠️ 那个**填了内容的** video 节点带 **5 个内层 `BUTTON`**（`Add tags` /
  `播放` / `底部播放` / `取消静音` / `全屏预览`），**另一个没有**
  ⇒ 源站是时间线节点的 4 个、复刻是 video 节点的 5 个
  ⇒ ⭐ **个数本就不该相等**，该对的是**关系式**：
  **「走完内层控件期间指针一次都不动」**

## ⭐ 六道门（**全部可红**）

1. `js_verbatim_from_952` / `py_verbatim_from_952` —— 尺子没跑偏（文件级 assert）
2. ⭐ `replica_actually_moved` —— **「操纵到底动了没有」必须自己答**：
   复刻侧第 1 按 `Tab` **必须真的动了**（焦点动了或指针动了）。
   ⚠️ 可红：红了就说明这一整批量的是**没动的东西**，全部读数作废
3. `pressed_exactly_n` —— 按压数照 952
4. `curve_reproducible` —— 逐格 2/2 逐条相同
5. `reached_the_freeze` —— 复刻侧**必须也出现**「指针有不动的时候」。
   ⚠️ 可红：红了说明**复刻根本没实现这一段**（那本身就是结论，不是探针失败）
6. `keys_disjoint` / `raw_keys_registered` —— 935 的两道免疫针

## 纪律（承 943→952）

1. ⭐ **尺子自证**：每一段退出前 `pre = cur`；**不许拿陈旧读数当基线**
2. ⭐ `reps_identical` **真算**（945 悬空、946 才补上）
3. ⭐ 派生键不许与原始键重叠、不许重名、原始键不许漏登记（935 两道免疫针）
4. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版漏一个逗号 ⇒ 门恒绿）
5. ⭐ **新件不许混进「逐字相同」那组**（940 的办法）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ 身份不稳的那一段三元组一律不当读数（946）
7. ⚠️ **写推断之前先查基线里有没有反例**（951 栽过）
8. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配挡下
9. ⚠️ **落盘排在所有后处理之前**（935）
10. ⚠️ **不可逆动作放序列最后**；**改既有探针不许删承重前置**

## 计费边界

**复刻是本地应用，本批零计费。** 只点左栏**插入**入口、点画布空白、按键盘；
⛔ 守卫拦在 `click` **之前**，契约是「**我正要点的这个元素**是什么」。
**绝不**点生成/发送/购买/充值，**也绝不**点节点本体。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe953_roving_ring_ck.py
"""

from __future__ import annotations

import inspect
import json
import pathlib
import re
import textwrap
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = pathlib.Path("/tmp/b953-roving-ring-ck.json")
SRC952_PATH = "/tmp/b952-freeze-who.json"
REPS = 2
KINDS = ["文本", "图片", "时间线", "主体", "导演台"]   # 照 901
SETTLE = 350        # ms（照 952）
BLANK_WAIT = 900    # ms（照 952）
NO_TI_CAP = 40      # 照 952
# ⚠️⚠️ **不是照 952 的 14**。第一版用 14 跑出来：复刻的环有
#   7 个节点 + 17 个内层控件 = **24 个停靠点** ⇒ 14 按**根本走不完一圈**
#   ⇒ `周期` 读成 `None`。901 栽过同一类（`OVERRUN=6` 不够、加到 20
#   才是「**故意走过一圈**」）⇒ 这里加到 **24**；第二版跑出来 **24 按仍差
#   一按**（第 24 按落在**最后一个**停靠点 `node#6` 上、还没回卷）⇒
#   `ring_closed=False` ⇒ 再加到 **28**，只为把回卷**看见**。
#   ⚠️ 这**不是放宽判据**，是**把按压预算补到能闭合**；源站那一侧另算
#   （见 `source_side`）：**它 14 按也没回卷** ⇒ 952 的「周期 = 10」被
#   **它自己的数据**推翻，不需要复刻来判。
N_PRESS_BASE = 28
N_PRESS_LEAD = 4    # 格 1：先按 4 下到达冻结点（照 952）
# ⭐ 判别组：照抄 952，**不许**预设方向。
# ⚠️ 唯一一处**刻意不同**：尾部 `Tab` 由 3 下改成 **4 下**。
#   952 那组以 `Tab`×3 收尾，在**源站**上正好停在工具条里；而**复刻**的
#   落点不同（第 3 下**已经离开**工具条）⇒ 组结束在「离开的那一按」上，
#   **后面没有下一按 ⇒ 滞后根本测不到**（第一版 `lag_is_one_press_probe`
#   读成 `False`，那是**预算不够**、不是「没滞后」）。
#   ⇒ 尾部多按 1 下。**这是补预算，不是改判据。**
PROBE_STEPS = [("Shift+Tab", 1), ("Tab", 1), ("ArrowDown", 1),
               ("Escape", 1), ("Tab", 4)]

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
P952 = pathlib.Path(__file__).with_name(
    "jimeng_probe952_freeze_who_src.py")

# ── 原始读数键（935 的第一道免疫针）────────────────────────────────────
RAW_KEYS = frozenset({
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "no_ti",
    "no_ti_capped", "active_tag", "active_tid", "focus_in_node", "blank",
    "point", "i", "k", "hit_tag", "focus_ok", "seq",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who",
    # ⭐ 本批从 CENSUS_JS 的 `ti` 派生的两口径（**没另加仪器**）
    "armed", "armed_before", "armed_after",
})
# ── 派生键（935 的第一道免疫针）────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "ci", "mode", "n_press", "n_inserted", "inserted", "ready",
    "rows", "step_rows", "frozen_presses", "swallowed_presses",
    "left_button_press", "lag_is_one_press", "reached_the_freeze",
    "escape_releases", "shift_tab_moves", "arrow_moves", "cell_ok",
    "reps_identical", "design_gates", "curve_reproducible",
    "toolbar_presses", "toolbar_identities", "pointer", "pointer_seq",
    "wrap_k", "cycle_len", "cycle_relational", "n_toolbar_nodes",
    "replica_actually_moved", "cold_without_ti", "cold_armed",
    # ⭐ 强判据一族（952 那把尺子**自带**的 `focus_moved` 只比 (tag, tid)，
    #   在内层控件之间切换时两者都不变 ⇒ 那是 952 NNNN.5 记的「陷阱」本身）
    "focus_moved_strong", "swallowed_presses_strong", "shift_tab_moves_strong",
    "arrow_moves_strong", "escape_releases_strong", "stop_seq", "n_stops",
    "reps_identical_norm", "curve_reproducible_norm", "norm_note",
    "left_button_press_probe", "lag_is_one_press_probe", "source_side",
    "all_stuck_in_toolbar", "walked_while_in_toolbar", "discrimination_from",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "frozen_presses", "lag_is_one_press",
              "reached_the_freeze", "reps_identical", "curve_reproducible",
              "cycle_len", "cycle_relational", "toolbar_presses"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index", "armed"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"
assert len(DERIVED_KEYS) == len(set(DERIVED_KEYS)), "派生键重名"
assert len(RAW_KEYS) == len(set(RAW_KEYS)), "原始键重名"

# ── 七段 JS：逐字来自 952（本批零新件 JS）──────────────────────────────
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

# ⭐ 七段 JS 全部与 952 **逐字相同**
_p952src = P952.read_text(encoding="utf-8") if P952.exists() else ""
assert _p952src, "读不到 952 的源码 —— 尺子没得比，这道门恒绿"
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS", "WHOAMI_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL
                      + (WHOAMI_JS,)):
    assert _js in _p952src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 952 那份**不一致** —— 两份尺子开始分家了")


# ── 七个助手：也逐字来自 952 ───────────────────────────────────────────
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


# ⭐⭐ 助手也逐字对着 952 的**文件内容** assert（不是对着我自己）
for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key):
    _s = textwrap.dedent(inspect.getsource(_fn)).strip()
    assert _s in _p952src, (
        f"{_fn.__name__} 与 952 那份**不一致** —— 尺子的 Python 侧也开始分家了")
    del _s


# ── 新件：复刻侧的就绪判据（必须自证「我够得着」）────────────────────────
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
assert "READY_JS" not in _p952src, "953 的新件别混进「逐字相同」那组"
assert READY_JS.count("slice(") == 0, "READY_JS 不该有切片"

page = None       # ⭐ 必须挂在模块级：`ev` 是 952 逐字复用来的，闭包拿不到局部


def boot_ck():
    """新件：复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**——
    问的是「画布根在不在 / 几个节点 / 几个插入入口」，不是「我猜它在」。"""
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev(READY_JS, [NODE_SEL, KINDS])


def insert_kinds():
    """固定前置：照 901 插 5 个节点。**左栏入口**、不是节点本体 ⇒ 不破
    `zero_node_clicks`。返回**真的插进去几个** + 哪些。"""
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


def norm_tid(tid):
    """⚠️ **复刻的节点 `data-testid` 带时间戳**（`rf__node-text-1791076289857`）
    ⇒ 逐条身份比较在复刻上**构造性不可复现** ⇒ 逐字的那道
    `curve_reproducible` 在复刻上**恒红**，而那**不是**「读数不稳」。
    源站的 id 是稳定的（`rf__node-node_236ctpehgg`）⇒ 这是**复刻与源站的
    一处真实差异**。
    ⭐ 处置**不是**改产品让门变绿、也**不是**放宽门：逐字那道门**照旧如实
    记红**，另加一道**只把 id 尾部数字归一化**的比较，两道都进读数。"""
    if not tid:
        return tid
    return re.sub(r"-\d{6,}$", "", str(tid))


def norm_row(row):
    """只动 `tid` 里的时间戳；**其余逐字**。"""
    r = dict(row)
    for which in ("before", "after"):
        w = r.get("who_" + which)
        if isinstance(w, dict):
            w = dict(w)
            w["tid"] = norm_tid(w.get("tid"))
            r["who_" + which] = w
    r["armed_before"] = [norm_tid(x) for x in (r.get("armed_before") or [])]
    r["armed_after"] = [norm_tid(x) for x in (r.get("armed_after") or [])]
    return r


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


out = {
    "target": "replica", "url": URL, "reps": REPS, "kinds": KINDS,
    "n_press_base": N_PRESS_BASE, "n_press_lead": N_PRESS_LEAD,
    "probe_steps": PROBE_STEPS, "no_ti_cap": NO_TI_CAP,
    "forbidden_tids": list(FORBIDDEN_TIDS),
    "pointer_definition_note":
        "指针 = no_ti[0] if no_ti else armed[0]，两个都从 CENSUS_JS 已有的 `ti` "
        "派生、**没另加仪器**。源站解除布防是**把 tabindex 属性摘掉**（ti=None）"
        "⇒ 走 no_ti 口径；复刻的 armAll 写的是 '-1'、属性一直在 ⇒ 走 armed 口径"
        "（ti='0'）。**同一件事的两种口径**，不是两个现象；两个都为空记 None。",
    "ruler": {
        "js_verbatim_from_952": ["BLANK_JS", "CENSUS_JS", "NO_TI_JS",
                                 "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS",
                                 "WHOAMI_JS"],
        "py_verbatim_from_952": ["ev", "dump", "guard", "guard_point",
                                 "delta", "press_row", "curve_key"],
        "new_pieces": ["READY_JS", "boot_ck", "insert_kinds", "armed_of",
                       "no_ti_of", "pointer_of", "row_pointer", "in_toolbar",
                       "walk_stuck", "strong_moved", "identity", "norm_tid",
                       "norm_row", "stop_name", "_sid", "_sstrong",
                       "load_source_ref"],
        "only_variable": "URL（源站 → 本地复刻）",
    },
    "source_reference_952": {},
    "runs": [],
}


def _sid(row, which="after"):
    w = row.get("who_" + which) or {}
    return (w.get("tag"), w.get("aria"), w.get("node_index"))


def _sstrong(row):
    return _sid(row, "before") != _sid(row, "after")


def load_source_ref():
    """源站读数（若有）⇒ 只作**并排对照**，**不作判据**。
    ⭐ 这里顺带把 952 的三条结论**用 952 自己的数据**重算一遍：
    强判据下的 `focus_moved`、环到底回没回卷、判别组每一步**按前焦点在哪**。"""
    if not pathlib.Path(SRC952_PATH).exists():
        return {"path": SRC952_PATH, "why": "文件不在"}
    try:
        s = json.loads(pathlib.Path(SRC952_PATH).read_text(encoding="utf-8"))
        runs = s.get("runs") or []
        if not runs:
            return {"path": SRC952_PATH, "why": "runs 为空"}
        c0 = runs[0]["cells"][0]
        c1 = runs[0]["cells"][1]
        rows = [r for r in c0["rows"] if r.get("k", 0) >= 1]
        stops = [(r["k"], (r["who_after"] or {}).get("node_index"),
                  (r["who_after"] or {}).get("tag"),
                  (r["who_after"] or {}).get("aria")) for r in rows]
        node_stops = [x for x in stops if x[2] == "DIV"]
        # 环回没回卷：停靠点序列里有没有**重复出现过同一个节点下标**的第二次
        seen, wrapped_at = set(), None
        for k, ni, tag, _aria in node_stops:
            if ni is None:
                continue
            if ni in seen:
                wrapped_at = k
                break
            seen.add(ni)
        return {
            "path": SRC952_PATH,
            "n_press_recorded": len(rows),
            "cold_without_ti": c0.get("cold_without_ti"),
            "frozen_presses": c0.get("frozen_presses"),
            "swallowed_presses_weak": c0.get("swallowed_presses"),
            "frozen_presses_strong_swallowed": sum(
                1 for r in rows if r["no_ti_before"] == r["no_ti_after"]
                and not _sstrong(r)),
            "frozen_presses_all_moved_focus": sum(
                1 for r in rows if r["no_ti_before"] == r["no_ti_after"]
                and _sstrong(r)),
            "left_button_press": c0.get("left_button_press"),
            "lag_is_one_press": c0.get("lag_is_one_press"),
            "n_node_stops": len(node_stops),
            "node_stop_indices": [x[1] for x in node_stops],
            "wrapped_at_press": wrapped_at,
            "cycle_10_supported": bool(
                c0.get("n_press", 0) and wrapped_at
                and wrapped_at <= 10),
            "discrimination": [
                {"key": r["key"], "step": r["step"],
                 "from": _sid(r, "before"), "to": _sid(r, "after"),
                 "weak": r["focus_moved"], "strong": _sstrong(r)}
                for r in (c1.get("step_rows") or [])],
        }
    except Exception as e:                                  # noqa: BLE001
        return {"path": SRC952_PATH, "why": f"读不出来：{e!r}"}


def main() -> int:
    global page
    out["source_reference_952"] = load_source_ref()
    out["source_side"] = out["source_reference_952"]
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_context(
            viewport={"width": 1512, "height": 1200}).new_page()
        for rep in range(1, REPS + 1):
            print(f"===== rep {rep} =====", flush=True)
            rec = {"rep": rep, "cells": []}
            out["runs"].append(rec)
            dump(out)

            for ci, mode in enumerate(("base", "probe")):
                n_press = N_PRESS_BASE if mode == "base" else N_PRESS_LEAD
                tag = ("照 952 的基线" if mode == "base"
                       else f"先按 {N_PRESS_LEAD} 下到达冻结点，再跑判别组")
                print(f"  --- 格 {ci}（{tag}）---", flush=True)
                rd = boot_ck()
                c = {"ci": ci, "mode": mode, "n_press": n_press,
                     "ready": rd, "rows": [], "step_rows": []}
                rec["cells"].append(c)
                dump(out)
                print(f"      就绪：flow={rd['has_flow']} "
                      f"nodes={rd['n_nodes']} 入口齐={rd['all_kinds']} "
                      f"中性态 ti 分布={rd['node_ti_hist']}", flush=True)
                if not rd["has_flow"] or not rd["n_nodes"]:
                    c["skipped"] = "画布根或节点没出来，本格不测"
                    continue

                # ── 固定前置：插 5 个节点（两格一样）────────────────────
                c["inserted"] = insert_kinds()
                c["n_inserted"] = len(c["inserted"])
                page.wait_for_timeout(1200)
                print(f"      插完 {c['n_inserted']} 个：{c['inserted']}",
                      flush=True)

                sp = ev(BLANK_JS)
                c["blank"] = sp
                if sp:
                    guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点
                    page.mouse.click(sp[0], sp[1])
                    page.wait_for_timeout(BLANK_WAIT)
                pre = ev(CENSUS_JS, [NODE_SEL])
                c["n_nodes"] = pre["n_nodes"]
                nt = ev(NO_TI_JS, [NODE_SEL, NO_TI_CAP])
                c["cold_without_ti"] = nt["n_without_ti"]
                c["cold_armed"] = armed_of(pre["ti"])
                c["rows"].append({
                    "phase": "cold", "step": 0, "k": 0, "key": None,
                    "no_ti_before": nt["no_ti"], "no_ti_after": nt["no_ti"],
                    "no_ti_capped": nt["no_ti_capped"],
                    "pointer_moved": False,
                    "active_before": None, "active_after": None,
                    "was_arm": None, "bit": None, "n_added": None,
                    "w_before": pre["n_without_ti"],
                    "w_after": pre["n_without_ti"],
                    "identity_stable": None,
                    "armed_before": c["cold_armed"],
                    "armed_after": c["cold_armed"],
                    "who_before": None,
                    "who_after": ev(WHOAMI_JS, [NODE_SEL])})
                dump(out)
                print(f"      冷启动：nodes={pre['n_nodes']}、"
                      f"不带ti={nt['n_without_ti']}、"
                      f"armed={c['cold_armed']}、"
                      f"指针={pointer_of(pre['ti'])}", flush=True)

                for k in range(1, n_press + 1):
                    ab = armed_of(pre["ti"])            # ⭐ 按**前**的 ti
                    row, pre = press_row(page, pre, "Tab", k, "base", 0)
                    row["armed_before"] = ab
                    row["armed_after"] = armed_of(pre["ti"])
                    row["seq"] = len(c["rows"])         # ⭐ 跨 base/probe 单调
                    c["rows"].append(row)
                    print(f"      [Tab {k:>2}] 前={row['active_before']}"
                          f" 后={row['active_after']}"
                          f" 焦点动了={row['focus_moved']}"
                          f" armed {ab}→{row['armed_after']}"
                          f"（动={ab != row['armed_after']}）"
                          f" 按后在节点#{row['who_after'].get('node_index')}"
                          f" aria={str(row['who_after'].get('aria'))[:20]!r}",
                          flush=True)
                    dump(out)

                if mode == "probe":
                    step = 0
                    for key, times in PROBE_STEPS:
                        for _ in range(times):
                            step += 1
                            ab = armed_of(pre["ti"])
                            row, pre = press_row(
                                page, pre, key, step, "probe", step)
                            row["armed_before"] = ab
                            row["armed_after"] = armed_of(pre["ti"])
                            row["seq"] = len(c["rows"])  # ⭐ 跨 base/probe 单调
                            c["step_rows"].append(row)
                            c["rows"].append(row)
                            print(f"      [{key} #{step}] "
                                  f"前={row['active_before']}"
                                  f" 后={row['active_after']}"
                                  f" 焦点动了={row['focus_moved']}"
                                  f" armed {ab}→{row['armed_after']}"
                                  f" 按后 aria="
                                  f"{str(row['who_after'].get('aria'))[:20]!r}",
                                  flush=True)
                            dump(out)

                # ── 派生量（**关系式**，不钉绝对值）────────────────────
                main_rows = [r for r in c["rows"]
                             if r["phase"] in ("base", "cold")]
                c["pointer_seq"] = [row_pointer(r) for r in main_rows]
                c["frozen_presses"] = sum(
                    1 for r in main_rows if r["k"] >= 1
                    and r["armed_before"] == r["armed_after"])
                c["swallowed_presses"] = sum(
                    1 for r in main_rows if r["k"] >= 1
                    and r["armed_before"] == r["armed_after"]
                    and not r["focus_moved"])
                # ⭐ 强判据的两条：指针不动的那几按，焦点**到底**动不动
                c["swallowed_presses_strong"] = sum(
                    1 for r in main_rows if r["k"] >= 1
                    and r["armed_before"] == r["armed_after"]
                    and not strong_moved(r))
                c["stop_seq"] = [stop_name(r) for r in main_rows
                                 if r["k"] >= 1]
                c["n_stops"] = len(c["stop_seq"])
                for r in main_rows:
                    r["focus_moved_strong"] = strong_moved(r) \
                        if r["k"] >= 1 else None
                ws = walk_stuck(main_rows)
                c["toolbar_presses"] = ws["n_toolbar_presses"]
                c["toolbar_identities"] = ws["identities"]
                c["walked_while_in_toolbar"] = ws["walked"]
                c["all_stuck_in_toolbar"] = ws["all_stuck"]
                # 「离开内层控件的那一按」= 按前在内层、按后不在（承 952 NNNN.5：
                # 判据**比身份**而不是比 tag）
                c["left_button_press"] = next(
                    (r["k"] for r in main_rows if r["k"] >= 1
                     and in_toolbar(r, "before") and not in_toolbar(r, "after")),
                    None)
                lb = c["left_button_press"]
                c["lag_is_one_press"] = bool(
                    lb is not None
                    and next(r for r in main_rows
                             if r["k"] == lb)["armed_before"]
                    == next(r for r in main_rows
                            if r["k"] == lb)["armed_after"]
                    and next((r["armed_before"] != r["armed_after"]
                              for r in main_rows if r["k"] == lb + 1), False))
                c["reached_the_freeze"] = bool(c["frozen_presses"] > 0)
                # ⭐ 周期：**关系式**（周期长度 = 节点数 + 带工具条的节点数）
                seq = c["pointer_seq"]
                c["wrap_k"] = next(
                    (main_rows[i]["k"] for i in range(1, len(main_rows))
                     if seq[0] is not None and seq[i] == seq[0]
                     and seq[i - 1] is not None and seq[i - 1] != seq[0]),
                    None)
                c["cycle_len"] = c["wrap_k"]
                c["n_toolbar_nodes"] = len(
                    {t["node_index"] for t in ws["identities"]
                     if t.get("node_index") is not None})
                c["cycle_relational"] = {
                    "n_nodes": c.get("n_nodes"),
                    "n_toolbar_nodes": c["n_toolbar_nodes"],
                    "expected": (c.get("n_nodes") or 0) + c["n_toolbar_nodes"],
                    "measured": c["cycle_len"]}
                st = c["step_rows"]
                _mv = lambda key, times: [        # noqa: E731
                    r for r in st if r["key"] == key][:times]
                c["shift_tab_moves"] = any(
                    r["focus_moved"] for r in _mv("Shift+Tab", 1))
                c["arrow_moves"] = any(
                    r["focus_moved"] for r in _mv("ArrowDown", 1))
                c["escape_releases"] = any(
                    r["focus_moved"] for r in _mv("Escape", 1))
                c["shift_tab_moves_strong"] = any(
                    strong_moved(r) for r in _mv("Shift+Tab", 1))
                c["arrow_moves_strong"] = any(
                    strong_moved(r) for r in _mv("ArrowDown", 1))
                c["escape_releases_strong"] = any(
                    strong_moved(r) for r in _mv("Escape", 1))
                # ⚠️ 上面三条 `_mv` 只覆盖判别组**头一次**出现的那个键，
                #    所以「按前焦点在哪」必须一并记下来，否则会把
                #    「键没反应」与「键没在**那个位置**上试」混成一句。
                c["discrimination_from"] = [
                    {"key": r["key"], "step": r["step"],
                     "from": stop_name(r, "before"), "to": stop_name(r, "after"),
                     "weak": r["focus_moved"], "strong": strong_moved(r)}
                    for r in st]
                # ⭐ 格 1 专属：`left_button_press` / `lag_is_one_press` 是
                #   952 逐字复制的**派生量**，而 952 自己只把它们算在
                #   `phase in (base, cold)` 的行上 ⇒ **格 1 恒为 None/False**，
                #   那是**结构性的「不适用」、不是「没发生」**。
                #   ⇒ 另算一份**含判别组**的，且**不覆盖** 952 那两个名字。
                allr = [r for r in c["rows"] if r["k"] >= 1
                        and r["phase"] != "cold"]
                c["left_button_press_probe"] = next(
                    (r["seq"] for r in allr if in_toolbar(r, "before")
                     and not in_toolbar(r, "after")), None)
                _lbp = c["left_button_press_probe"]
                c["lag_is_one_press_probe"] = bool(
                    _lbp is not None
                    and next((r["armed_before"] != r["armed_after"]
                              for r in allr if r["seq"] == _lbp), None) is False
                    and next((r["armed_before"] != r["armed_after"]
                              for r in allr if r["seq"] == _lbp + 1),
                              None) is True)
                c["cell_ok"] = bool(len(main_rows) == n_press + 1)
                print(f"      ⇒ 指针不动 {c['frozen_presses']} 下、"
                      f"其中焦点也没动 {c['swallowed_presses']} 下、"
                      f"内层控件段 {ws['n_toolbar_presses']} 下"
                      f"（走了 {ws['walked']} / 冻住 {ws['stuck']}）"
                      f"、离开的那一按 k={lb}、"
                      f"滞后 1 下={c['lag_is_one_press']}、"
                      f"指针序列={seq}、周期={c['cycle_len']}"
                      f" 关系式={c['cycle_relational']}"
                      + (f"｜Shift+Tab 动了={c['shift_tab_moves']}、"
                         f"方向键动了={c['arrow_moves']}、"
                         f"Esc 动了={c['escape_releases']}" if st else ""),
                      flush=True)
                dump(out)

        b.close()

    _ident = []
    for ci in range(2):
        got = [curve_key(run["cells"][ci]) for run in out["runs"]
               if ci < len(run["cells"]) and "skipped" not in run["cells"][ci]]
        _ident.append(bool(len(got) == REPS and got[0] == got[1]))
    out["reps_identical"] = _ident
    out["curve_reproducible"] = bool(all(_ident))

    # ⭐⭐ 归一化比较：**只**把 tid 尾部的时间戳数字去掉，其余逐字。
    #   逐字那道门照旧如实记红（见 `norm_note`）。
    _ident_n = []
    for ci in range(2):
        got = []
        for run in out["runs"]:
            c = run["cells"][ci]
            if "skipped" in c:
                continue
            got.append({"rows": [norm_row(r) for r in c["rows"]],
                        "step_rows": [norm_row(r) for r in c["step_rows"]],
                        **{k: c.get(k) for k in
                           ("mode", "n_press", "cold_without_ti",
                            "frozen_presses", "swallowed_presses",
                            "swallowed_presses_strong", "left_button_press",
                            "lag_is_one_press", "reached_the_freeze",
                            "escape_releases", "shift_tab_moves",
                            "arrow_moves", "stop_seq")}})
        _ident_n.append(bool(len(got) == REPS and got[0] == got[1]))
    out["reps_identical_norm"] = _ident_n
    out["curve_reproducible_norm"] = bool(all(_ident_n))
    out["norm_note"] = (
        "逐字那道 `curve_reproducible` 在复刻上**恒红**，原因是**被测对象**"
        "不稳定：复刻节点 `data-testid` 带时间戳（`rf__node-text-1791076289857`），"
        "源站的 id 稳定（`rf__node-node_236ctpehgg`）⇒ 这是**复刻与源站的"
        "一处真实差异**。处置**不是**改产品、**也不是**放宽门：逐字那道照旧"
        "如实记红，另加一道**只归一化 tid 尾部数字**的比较，两道都进读数。")

    # ⭐⭐ 「操纵到底动了没有」——自己答，不许默认
    _firsts = [run["cells"][0]["rows"][1] for run in out["runs"]
               if "skipped" not in run["cells"][0]
               and len(run["cells"][0]["rows"]) > 1]
    out["replica_actually_moved"] = bool(
        _firsts and all(r["focus_moved"]
                        or r["armed_before"] != r["armed_after"]
                        for r in _firsts))
    out["design_gates"] = {
        "js_verbatim_from_952": True,      # 文件级 assert 过了才会跑到这
        "py_verbatim_from_952": True,
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
        "curve_reproducible_norm": out["curve_reproducible_norm"],
        "replica_actually_moved": out["replica_actually_moved"],
        "reached_the_freeze": bool(all(
            run["cells"][0].get("reached_the_freeze")
            for run in out["runs"] if "skipped" not in run["cells"][0])),
        # ⭐ 环闭合了没有（**关系式**：停靠点数 > 节点数 + 内层控件数 ⇒ 走完了）
        "ring_closed": bool(all(
            run["cells"][0].get("cycle_len") is not None
            for run in out["runs"] if "skipped" not in run["cells"][0])),
        "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
        "raw_keys_registered": bool(
            all(k in RAW_KEYS for k in ("bit", "identity_stable",
                                        "n_without_ti", "active_tag",
                                        "focus_in_node", "no_ti", "aria",
                                        "node_index", "armed"))),
    }
    print("\n设计门：", out["design_gates"], flush=True)
    print("逐格 2/2 相同（逐字）：", out["reps_identical"], flush=True)
    print("逐格 2/2 相同（归一化 tid）：", out["reps_identical_norm"],
          flush=True)
    for rep in out["runs"]:
        c = rep["cells"][0]
        if "skipped" in c:
            continue
        print(f"rep{rep['rep']} 环：停靠点 {c['n_stops']} 个、"
              f"序列={c['stop_seq']}", flush=True)
        print(f"        强判据下 焦点也没动={c['swallowed_presses_strong']} 下"
              f"（弱判据说 {c['swallowed_presses']} 下）"
              f"｜周期={c['cycle_len']} 关系式={c['cycle_relational']}",
              flush=True)
    c1 = out["runs"][0]["cells"][1]
    if "skipped" not in c1:
        print("格 1 判别组（按前焦点在哪）：", flush=True)
        for d in c1.get("discrimination_from", []):
            print(f"   [{d['key']} #{d['step']}] {d['from']} → {d['to']}"
                  f"  弱={d['weak']} 强={d['strong']}", flush=True)
        print(f"   格 1 专属：离开内层的那一按 seq={c1.get('left_button_press_probe')}"
              f"、滞后 1 下={c1.get('lag_is_one_press_probe')}"
              f"（952 那两个名字在格 1 是**结构性不适用**）", flush=True)
    print("源站对照（952）：", out["source_reference_952"], flush=True)
    dump(out)
    print("\n读数已写入", OUT, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
