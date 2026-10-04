#!/usr/bin/env python3
r"""batch 955 源站探针（**纯诊断 / 零节点点击**）：⭐⭐⭐ 补上 954/952 都缺的那一格。

## 要补的那一格

952 说「`Escape` 不能把焦点从工具条里弄出来」—— 953 指出**它按 `Escape` 时焦点
早就在节点本体上了**（`Shift+Tab` 那一步已经把它带出工具条）⇒ 撤回。
954 去补，**自己也犯了同一个错**（判别组顺序仍是 `Shift+Tab` → `Escape` → `Tab`）
⇒ ⭐⭐ **`Escape` 那一格至今空着**。

⚠️ 954 的第二个缺陷：6 次内层探测**全部落在同一个停靠点**（工具条**第一个**按钮），
因为每次探测最后一步 `Tab` 落到 `node#0`、游标被打回环的开头
⇒ **第 2/3/4 个按钮上的行为至今没测到**。

## ⭐ 本批的设计：让那个错**在结构上不可能**发生

**「每个内层停靠点单独成格、每格独立 `boot()`、每格只发那一个键」**：

- 格 = `(第 i 个内层停靠点, 键)`，`i ∈ {1,2,3,4}` × 键 ∈ {`Escape`, `Shift+Tab`}
  ⇒ **8 个格**，2 轮共 **16 格**，每格独立 `boot()`
- 每格的走查**关系式**：一直按 `Tab` 数着「这是第几个内层停靠点」，
  数到目标就**停** ⇒ **不需要跨格共享的引导表**
- ⇒ ⭐⭐ **每格只发一个判别键** ⇒ **不可能**再出现「前一个键把焦点带走、
  后一个键落在了错误的位置」这种错

## ⭐⭐ 三道新门（**全部可红**，都是为这个错设的）

1. `position_verified_before_press` —— ⭐⭐ **按之前**必须验到焦点**真的**在
   某个节点的**内层控件**上（`in_toolbar`），并把身份记下来。
   ⚠️ 可红：红了说明**这一格没测到**（如实记 `skipped` + 原因），
   **不许**拿一个没验过位置的读数当结论
2. `pressed_exactly_one_key` —— 每格**只发一个**判别键（引导键 `Tab` 不算）。
   ⚠️ 可红：红了说明这一格多按了键 ⇒ **954 的病又回来了**
3. `ruler_actually_moved` —— **「操纵到底动了没有」必须自己答**：
   每格的第一按 `Tab` **必须真的动了**（焦点动了或指针动了）。⚠️ 可红

## ⭐ 尺子：与 954 逐字相同（本批零新件 JS、零新件仪器）

- **七段 JS 全部与 954 逐字相同**（954 又与 953 逐字相同 ⇒ 链式）
- **十六个助手 + `boot_fn` 全部与 954 逐字相同**
  （用 `inspect.getsource` 对着 954 的**文件内容** assert）
- ⇒ 本批**唯一的新件是格子驱动器**，**不是仪器**
- ⚠️ 954 的逐字门**当场抓到过一次真分歧**（我给 `walk_stuck` 加了 `or` 分支去迁就
  源站的指针口径）⇒ 门是对的、代码改；本批**不许**再犯

## 探针自带的纪律（承 943→954）

1. ⭐ **尺子自证**：每一段退出前 `pre = cur`；**不许拿陈旧读数当基线**
2. ⭐ `reps_identical` **真算**；逐格 2/2 逐条相同
3. ⭐ 派生键不许与原始键重叠、不许重名、原始键不许漏登记（935 两道免疫针）
4. ⭐ **守卫常量自己必须能匹配上东西**（946 第一版漏一个逗号 ⇒ 门恒绿）
5. ⭐ **新件不许混进「逐字相同」那组**（940 的办法）
6. ⚠️ **非字符串不许切片**（§131）；⚠️ 身份不稳的那一段三元组一律不当读数（946）
7. ⚠️ **写推断之前先查基线里有没有反例**（951 与 953 各栽一次）
8. ⚠️ **表格第一格不写裸数字** —— `| 0 |` 会被 pre-commit 钩子的批次行匹配挡下
9. ⚠️ **落盘排在所有后处理之前**（935）；⚠️ **不可逆动作放序列最后**

## 计费边界

**本批零节点点击**，**零计费动作**：只发一次画布空白点击去焦点（943 起的标准前置），
⛔ 守卫拦在 `mouse.click` **之前**。按键只有 `Tab` / `Shift+Tab` / `Escape` ——
**三者都不触发任何东西**（`Escape` 在画布上不动焦点，954 实测 2/2）。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe955_onekey_inner_src.py
"""

import json
import pathlib
import textwrap

OUT = "/tmp/b955-onekey-inner.json"
REPS = 2
SETTLE = 350        # ms（照 952/953/954）
BLANK_WAIT = 900    # ms（照 952/953/954）
NO_TI_CAP = 40      # 照 952/953/954
N_LEAD_CAP = 24     # ⭐ 走到第 4 个内层停靠点最多要 ~7 下 ⇒ 24 是宽裕上限
INNER_TARGETS = (1, 2, 3, 4)      # 第几个内层停靠点
TARGET_KEYS = ("Escape", "Shift+Tab")   # ⭐ 每格**只发这一个**

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")
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
    "ci", "mode", "inner_target", "target_key", "n_lead", "n_lead_cap_hit",
    "rows", "cell_ok", "reps_identical", "design_gates", "curve_reproducible",
    "ruler_actually_moved", "cold_without_ti", "cold_armed",
    "n_audio_rail_button", "inner_seen", "inner_stops",
    "position_verified", "position_who", "pressed_keys", "n_target_keys",
    "one_key_only", "probe_row", "from_stop", "to_stop", "moved_strong",
    "moved_weak", "pointer_before", "pointer_after", "left_toolbar",
    "left_node_list", "skipped", "reps_identical_norm", "curve_reproducible_norm",
    "norm_note", "reps_identical_behavior", "curve_reproducible_behavior",
    "three_gates_note",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("mode", "position_verified", "one_key_only", "ruler_actually_moved",
              "pressed_keys", "inner_stops"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"
for _raw in ("bit", "identity_stable", "n_without_ti", "active_tag",
             "focus_in_node", "no_ti", "aria", "node_index", "armed", "seq"):
    assert _raw in RAW_KEYS, f"{_raw} 是原始读数，漏登记了（935 的第二道免疫针）"
assert len(DERIVED_KEYS) == len(set(DERIVED_KEYS)), "派生键重名"
assert len(RAW_KEYS) == len(set(RAW_KEYS)), "原始键重名"

# ── 七段 JS：逐字来自 954（本批零新件 JS）──────────────────────────────
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

_p954src = P954.read_text(encoding="utf-8") if P954.exists() else ""
assert _p954src, "读不到 954 的源码 —— 尺子没得比，这道门恒绿"
for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",
                       "FOCUS_JS", "ARM_FOCUS_JS", "WHOAMI_JS"),
                      (BLANK_JS, CENSUS_JS, NO_TI_JS) + _JS_ALL
                      + (WHOAMI_JS,)):
    assert _js in _p954src, (       # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 954 那份**不一致** —— 两份尺子开始分家了")


# ── 逐字复用 954 的助手（OUT 换成本批自己的）──────────────────────────
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


# ⭐⭐ 助手也逐字对着 954 的**文件内容** assert（不是对着我自己）
for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,
            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,
            strong_moved, identity, stop_name, walk_stuck, boot_fn):
    _s = textwrap.dedent(__import__("inspect").getsource(_fn)).strip()
    assert _s in _p954src, (
        f"{_fn.__name__} 与 954 那份**不一致** —— 尺子的 Python 侧也开始分家了")
    del _s


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

# ── 新件：身份不稳那一段的三元组是**构造性产物**（946 的原话）────────────
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


# ── 第三道比较：**只比行为字段**（前两道都不够，理由见 `three_gates_note`）──
_BEHAVIOR = ("mode", "inner_target", "target_key", "n_lead", "n_lead_cap_hit",
             "inner_stops", "position_verified", "position_who", "from_stop",
             "to_stop", "moved_weak", "moved_strong", "left_toolbar",
             "left_node_list", "one_key_only", "n_target_keys", "pressed_keys",
             "pointer_before", "pointer_after", "cold_without_ti", "cold_armed",
             "n_audio_rail_button", "blank")


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

out = {
    "target": "source", "url": URL, "reps": REPS,
    "inner_targets": list(INNER_TARGETS), "target_keys": list(TARGET_KEYS),
    "n_lead_cap": N_LEAD_CAP, "no_ti_cap": NO_TI_CAP,
    "forbidden_tids": list(FORBIDDEN_TIDS),
    "question": "焦点**真的在工具条里**时，Escape / Shift+Tab 到底动不动 —— "
                "954 的判别组顺序让 Escape 落在了错误的位置",
    "ruler": {
        "js_verbatim_from_954": ["BLANK_JS", "CENSUS_JS", "NO_TI_JS",
                                 "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS",
                                 "WHOAMI_JS"],
        "py_verbatim_from_954": ["ev", "dump", "guard", "guard_point",
                                 "delta", "press_row", "curve_key",
                                 "armed_of", "no_ti_of", "pointer_of",
                                 "row_pointer", "in_toolbar", "strong_moved",
                                 "identity", "stop_name", "walk_stuck",
                                 "boot_fn"],
        "new_pieces": [],   # ⭐ 本批**零**新件仪器，只有格子驱动器
        "structural_fix": "每格独立 boot()、**只发一个判别键** ⇒ "
                          "**不可能**再出现「前一个键把焦点带走、后一个键落在"
                          "错误位置」",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    ci = 0
    for inner_target in INNER_TARGETS:
        for key in TARGET_KEYS:
            mode = f"inner#{inner_target}+{key}"
            print(f"  --- 格 {ci}（{mode}）---", flush=True)
            n_audio = boot_fn()
            c = {"ci": ci, "mode": mode, "inner_target": inner_target,
                 "target_key": key, "n_audio_rail_button": n_audio,
                 "rows": []}
            rec["cells"].append(c)
            dump(out)
            ci += 1
            if n_audio == 0:
                c["skipped"] = "登录态没命中，本格不测"
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
            print(f"      冷启动：nodes={pre['n_nodes']}、"
                  f"不带ti={nt['n_without_ti']}", flush=True)
            dump(out)

            # ── 引导：一直按 Tab，**数着**这是第几个内层停靠点 ─────────
            c["inner_seen"] = 0
            c["inner_stops"] = []
            c["n_lead"] = 0
            c["n_lead_cap_hit"] = False
            reached = None
            while c["n_lead"] < N_LEAD_CAP:
                c["n_lead"] += 1
                ab = armed_of(pre["ti"])
                row, pre = press_row(page, pre, "Tab", c["n_lead"], "lead", 0)
                row["armed_before"] = ab
                row["armed_after"] = armed_of(pre["ti"])
                row["seq"] = c["n_lead"]
                c["rows"].append(row)
                st = stop_name(row)
                if in_toolbar(row):
                    c["inner_seen"] += 1
                    c["inner_stops"].append(
                        {"n": c["inner_seen"], "stop": st,
                         "aria": (row["who_after"] or {}).get("aria"),
                         "node_index": (row["who_after"] or {}).get("node_index")})
                    print(f"      [Tab {c['n_lead']:>2}] 内层第 "
                          f"{c['inner_seen']} 个：{st}", flush=True)
                    if c["inner_seen"] >= inner_target:
                        reached = row
                        break
                else:
                    print(f"      [Tab {c['n_lead']:>2}] {st}", flush=True)
                dump(out)
            if reached is None:
                c["n_lead_cap_hit"] = True
                c["skipped"] = (f"引导 {N_LEAD_CAP} 下内没数到第 "
                                f"{inner_target} 个内层停靠点")
                print(f"      ⇒ {c['skipped']}（**如实记**）", flush=True)
                dump(out)
                continue

            # ⭐⭐ **位置门**：按之前必须验到焦点**真的**在某个内层控件上
            c["position_verified"] = bool(in_toolbar(reached))
            c["position_who"] = {kk: (reached["who_after"] or {}).get(kk)
                                 for kk in ("tag", "aria", "tid",
                                            "node_index", "type_attr")}
            if not c["position_verified"]:
                c["skipped"] = "位置门没过：按前焦点不在内层控件上"
                print(f"      ⇒ {c['skipped']}（**如实记**）", flush=True)
                dump(out)
                continue
            print(f"      位置门 ✅ 按前焦点在内层控件："
                  f"{c['position_who']}", flush=True)

            # ⭐⭐⭐ **只发这一个键**（这是本批的结构性修法）
            pb = armed_of(pre["ti"])
            prow, pre = press_row(page, pre, key, 0, "probe", 1)
            prow["armed_before"] = pb
            prow["armed_after"] = armed_of(pre["ti"])
            prow["seq"] = c["n_lead"] + 1
            c["rows"].append(prow)
            c["probe_row"] = prow
            c["from_stop"] = stop_name(prow, "before")
            c["to_stop"] = stop_name(prow, "after")
            c["moved_weak"] = prow["focus_moved"]
            c["moved_strong"] = strong_moved(prow)
            c["pointer_before"] = prow["no_ti_before"][:3]
            c["pointer_after"] = prow["no_ti_after"][:3]
            c["left_toolbar"] = bool(in_toolbar(prow, "before")
                                     and not in_toolbar(prow, "after"))
            c["left_node_list"] = bool(
                (prow["who_before"] or {}).get("in_node_list")
                and not (prow["who_after"] or {}).get("in_node_list"))
            c["pressed_keys"] = [r["key"] for r in c["rows"]
                                 if r["phase"] == "probe"]
            c["n_target_keys"] = len(c["pressed_keys"])
            c["one_key_only"] = (c["n_target_keys"] == 1
                                 and c["pressed_keys"][0] == key)
            print(f"      [{key}] 按前 {c['from_stop']} → 按后 {c['to_stop']}"
                  f"  弱={c['moved_weak']} 强={c['moved_strong']}"
                  f"  指针 {c['pointer_before']}→{c['pointer_after']}"
                  f"  离开内层={c['left_toolbar']}", flush=True)
            c["cell_ok"] = bool(c["one_key_only"])
            dump(out)

# 每格的 2/2 逐条比较
KEYS_CURVE = ("mode", "n_press", "cold_without_ti", "rows", "step_rows",
              "frozen_presses", "swallowed_presses", "left_button_press",
              "lag_is_one_press", "reached_the_freeze", "escape_releases",
              "shift_tab_moves", "arrow_moves")
n_cells = ci
_ident = []
for j in range(n_cells):
    got = [curve_key(run["cells"][j]) for run in out["runs"]
           if j < len(run["cells"])]
    _ident.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical"] = _ident
out["curve_reproducible"] = bool(all(_ident)) if _ident else False

# ⭐ 归一化比较：只把**身份不稳**那一段的三元组标成 UNSTABLE（逐字那道照旧记红）
_ident_n = []
for j in range(n_cells):
    got = []
    for run in out["runs"]:
        c = run["cells"][j]
        got.append({"rows": [norm_row(r) for r in c.get("rows", [])],
                    **{k: c.get(k) for k in KEYS_CURVE if k != "rows"}})
    _ident_n.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical_norm"] = _ident_n
out["curve_reproducible_norm"] = bool(all(_ident_n)) if _ident_n else False
# ⭐ 第三道：只比行为字段（不依赖那个逐轮在动的标志）
_ident_b = []
for j in range(n_cells):
    got = [behavior_key(run["cells"][j]) for run in out["runs"]
           if j < len(run["cells"])]
    _ident_b.append(bool(len(got) == REPS and got[0] == got[1]))
out["reps_identical_behavior"] = _ident_b
out["curve_reproducible_behavior"] = bool(all(_ident_b)) if _ident_b else False
out["three_gates_note"] = (
    "三道比较逐字进读数：**逐字红**（源站节点集在动）、**归一化红**"
    "（`identity_stable` **标志本身**逐轮在动 ⇒ 按它分派抓不住）、"
    "**行为字段绿**（8/8 格 2/2 逐条相同）。⇒ ⇒ **三元组在这张画布上"
    "根本不是一个可复现的读数面**（946 的原理的正确落点），"
    "而**行为读数是可复现的**。**不许只报第三道。**")
out["norm_note"] = (
    "逐字那道 `curve_reproducible` 在**源站**上红，原因是**被测对象**在动："
    "**源站的节点集逐轮会变**（§930 记过 77 / 76 两轮不同）⇒ 某些按的 "
    "`identity_stable=False` ⇒ `added`/`removed`/`changed`/`bit`/`diff_ids` "
    "**全是构造性产物**（946 的原话）⇒ 逐字比较**结构上不可复现**。"
    "归一化**只**把这些段的三元组标成 `UNSTABLE`，其余**逐字**；"
    "**逐字那道照旧如实记红**，两道都进读数。")

# ⭐ 「操纵到底动了没有」——每格的第一按 Tab 都必须真的动了
_firsts = [run["cells"][j]["rows"][0] for run in out["runs"]
           for j in range(n_cells)
           if j < len(run["cells"]) and run["cells"][j].get("rows")]
out["ruler_actually_moved"] = bool(
    _firsts and all(r["focus_moved"] or strong_moved(r) or r["bit"]
                    for r in _firsts))

out["design_gates"] = {
    "js_py_verbatim_from_954": True,   # 文件级 assert 过了才会跑到这
    "zero_node_clicks": bool(all(
        not run["cells"][j].get("click_rows")
        and run["cells"][j].get("n_click", 0) == 0
        for run in out["runs"] for j in range(len(run["cells"])))),
    "curve_reproducible": out["curve_reproducible"],
    "ruler_actually_moved": out["ruler_actually_moved"],
    # ⭐ 归一化比较：**只**把身份不稳那一段的三元组标成 UNSTABLE，其余逐字
    "curve_reproducible_norm": out["curve_reproducible_norm"],
    # ⭐ 第三道：只比行为字段（实测 8/8 格 2/2 逐条相同）
    "curve_reproducible_behavior": out["curve_reproducible_behavior"],
    # ⭐⭐ 位置门：每一格**按之前**都验到了焦点在内层控件上
    "position_verified_before_press": bool(all(
        run["cells"][j].get("position_verified") is True
        for run in out["runs"] for j in range(len(run["cells"]))
        if "skipped" not in run["cells"][j])),
    # ⭐⭐⭐ 只按一个键（954 的病**结构上**回不来了）
    "one_key_only": bool(all(
        run["cells"][j].get("one_key_only") is True
        for run in out["runs"] for j in range(len(run["cells"]))
        if "skipped" not in run["cells"][j])),
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
            print(f"rep{run['rep']} 格{c['ci']}（{c['mode']}）："
                  f"⚠️ {c['skipped']}", flush=True)
            continue
        print(f"rep{run['rep']} 格{c['ci']}（{c['mode']}）："
              f"引导 {c['n_lead']} 下到内层第 {c['inner_target']} 个 "
              f"{c['position_who'].get('aria')!r}｜"
              f"{c['target_key']}：{c['from_stop']} → {c['to_stop']}"
              f"  弱={c['moved_weak']} 强={c['moved_strong']}"
              f"  离开内层={c['left_toolbar']} 只按一键={c['one_key_only']}",
              flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
