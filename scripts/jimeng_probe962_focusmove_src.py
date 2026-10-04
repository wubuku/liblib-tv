r"""batch 962 源站探针（**纯诊断 / 零节点点击**）：⭐⭐⭐⭐ 验 961 结尾那个**「只剩一个方向」** —— 源站到底**是不是**在 `keydown` **之后**主动 `focus()`。

⚠️⚠️⚠️ **docstring 头连错了三批**：959/960/961 的文件头**都还写着 「batch 957」**（`cp` 做基底时只改了 `OUT`、没改头）⇒ 962 一并修好，并把「**照抄基底要核的清单**」再加一条：**文件头也算产物**。


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
      scripts/jimeng_probe962_focusmove_src.py
"""

import json
import pathlib
import textwrap

OUT = "/tmp/b962-focusmove.json"
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
    # ⭐ 959 新增的**原始**读数（逐字取回，不加工）
    "dom_index", "tabindex", "dom_tid", "dom_tag", "dom_aria",
    # ⭐ 960 新增的**原始**读数
    "root_kind", "in_shadow", "root_host_tid", "ti_before", "ti_after",
    "ti_now", "ti_attr_now", "same_el_still_connected",
    # ⭐ 961 新增的**原始**读数（全文档普查）
    "ti_hist", "n_native", "n_focusable", "n_positive", "positive",
    "n_all_elements",
    # ⭐ 962 新增的**原始**读数（`FOCUSMOVE_JS` 的整段返回 + arm 的返回）
    "fm", "fm_armed",
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
    # ⭐ 959 的派生量
    "leg", "leg_out", "leg_lo", "leg_hi", "rail_seqs", "n_leg_out",
    "n_leg_rail", "dom_index_monotonic", "n_dom_index_missing", "verdict",
    "census_ti_hist", "n_rail_focusable", "reps_identical",
    "ruler_actually_moved", "n_lead", "n_lead_cap_hit", "n_rail_stops",
    "n_ready", "census",
    # ⭐ 960 的派生量（`ti_pairs` 那一族）
    "ti_pairs", "root_kinds", "n_in_shadow", "n_ti_changed", "all_out_in_document",
    # ⭐ 961 的派生量（`positive`/`ti_hist` 是**原始**读数，上面 RAW 里有；
    #   下面这几个是**在 Python 侧加工出来的**，不许混进 RAW）
    "n_positive_max", "n_out_with_positive", "positive_tids", "positive_sample",
    "ti_hist_stable",
    # ⭐ 962 的派生量
    "n_fm_rows", "n_fm_armed", "n_moved_before_dispatch_end",
    "n_moved_only_after_dispatch", "first_focusin_rel_hist",
    "first_focusin_trusted_hist", "which_bubble_hist", "prevented_at_end_hist",
    "n_no_focusin", "fm_sample", "verdict_fm",
    "n_dom_index_descents", "dom_index_descents", "verdict_domi",
    "n_moved_in_dispatch_leg", "n_leg_rows",
})
# ⚠️ 959 第一版**又**把 `blank` 登记进 DERIVED ⇒ **真红**（935 的 KeyError 免疫针）
#   ⇒ `blank` 是 **957 起就在 `RAW_KEYS` 里的原始读数**（`ev(BLANK_JS)` 的返回值）
#   ⇒ 派生表**不许**再登记它。⭐ 这已是第 3 次栽在这道门上（953/955 各一次）。
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

# ── 新件：`DOMIDX_JS`（**纯读、不是仪器**）──────────────────────────────
# ⭐ 本批只问一件事：**`Tab` 顺序 == DOM 顺序吗？**
# 浏览器规则：正 `tabindex` 升序 → 然后 **DOM 序**（无 `tabindex`/`0` 的按 DOM 序）。
# 源站左栏是 **roving**（957：只有一枚 `0`）⇒ 它在 `Tab` 序里的位置
# **由它自己的 DOM 位置决定** ⇒ 所以「Tab 序」与「DOM 序」的关系
# **必须实测**，**不能**从 954 的停靠点序列反推（那是**结果**，不是**原因**）。
# ⚠️ 口径：`document.querySelectorAll('*')` 的下标 = **文档序**（含 `<html>`/`<head>`）。
#   不用 `compareDocumentPosition`：它给的是**相对**关系，要自己写排序，
#   反而多一处可写错的地方。绝对下标**单调**就够判「是不是 DOM 序」。
DOMIDX_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {who: 0, dom_index: null, tabindex: null,
                  tag: null, tid: null, aria: null, in_node_list: false};
  const all = Array.from(document.querySelectorAll('*'));
  const host = a.closest('[data-testid]');
  return {who: 1,
          dom_index: all.indexOf(a),
          tabindex: a.hasAttribute('tabindex')
                    ? a.getAttribute('tabindex') : null,
          tag: (a.tagName || '').toUpperCase(),
          tid: host ? host.getAttribute('data-testid') : null,
          aria: a.getAttribute('aria-label') || a.getAttribute('title')
                || (a.innerText || '').slice(0, 30) || null,
          in_node_list: !!a.closest(nodeSel)};
}"""
assert "DOMIDX_JS" not in _p955src, "959 的新件别混进「逐字相同」那组"
assert DOMIDX_JS.count("slice(") == DOMIDX_JS.count(SLICE_STR), (
    "DOMIDX_JS 里有**非字符串**切片（§131）")

# ── 新件：`ROOT_JS`（**纯读、不是仪器**）───────────────────────────────
# ⭐ 本批要**逐个否掉或坐实** 959 留下的两个可能性，各自带判据：
#   ① **shadow root？** —— `getRootNode()` 是 `Document` 还是 `ShadowRoot`。
#      ⭐ 若在 shadow root 里 ⇒ `document.querySelectorAll('*')` **根本不进**
#      ⇒ 959 那套 `dom_index` 的**口径**不成立 ⇒ **959 的读数要重做**
#      （**不是**「959 错了」，是「959 用错了口径」）
#   ② **应用在 keydown 里改 `tabindex`？** —— 逐按读**同一个元素**在
#      「按**前**」与「按**后**」的 `tabindex`。⚠️ 959 **只读到「按后」**
#      ⇒ 这次成对读。⭐ 若前=后=`None` ⇒ 这个解释**又被否掉一个**
ROOT_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {who: 0, root_kind: null, root_host_tid: null,
                  ti_before: null, ti_attr_now: null, in_shadow: null};
  const r = a.getRootNode();
  const isShadow = !!(r && r.host);
  // ⭐ 同一个元素在「按前」记的 tabindex（由调用方塞在 window 上）与「现在」
  const before = (window.__preTi === undefined) ? null : window.__preTi;
  return {who: 1,
          root_kind: isShadow ? 'ShadowRoot'
                              : ((r && r.nodeName) ? r.nodeName : null),
          in_shadow: isShadow,
          root_host_tid: (isShadow && r.host)
              ? (r.host.closest('[data-testid]')
                   ? r.host.closest('[data-testid]').getAttribute('data-testid')
                   : null) : null,
          ti_before: before,
          ti_now: a.hasAttribute('tabindex')
                    ? a.getAttribute('tabindex') : null,
          ti_attr_now: a.hasAttribute('tabindex')};
}"""
assert "TICENSUS_JS" not in _p955src, "961 的新件别混进「逐字相同」那组"
assert ROOT_JS.count("slice(") == 0, "ROOT_JS 不该有切片"
# ⭐ 守卫常量自己必须能匹配上东西（946 的教训：漏一个逗号 ⇒ 门恒绿）
assert ROOT_JS.count("getRootNode()") == 1 and "ShadowRoot" in ROOT_JS, (
    "`ROOT_JS` 自己就匹配不上它要验的东西 —— 这道门恒绿，等于没有门")

# ── 新件：`TICENSUS_JS`（**纯读、不是仪器**）────────────────────────────
# ⭐⭐⭐⭐ **本批的整个来由 = 960/959 的一个盲区**：
#   它们读 `tabindex` **只读「焦点所在的那一枚」** ⇒ 读到的是
#   `'0'`（左栏 roving 那一枚）或 `None`。
#   ⚠️⚠️ 而浏览器排 `Tab` 顺序时看的是**所有候选**的 `tabindex`
#   ⇒ **那 6 个画布控件若带着正 `tabindex`（`1`/`2`/…），959/960 一个都没看到**
#   ⇒ 本批普查**全文档所有原生可聚焦元素**的 `tabindex`，并**逐个列出带正值的**。
# ⚠️ 口径与 957 的 `RAIL_JS` 一致：「原生可聚焦」= BUTTON/A/INPUT/SELECT/TEXTAREA
#   且**未** `disabled`。⚠️ 纯读：不调 `focus()`、不改任何属性。
TICENSUS_JS = """([nodeSel]) => {
  const NATIVE = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
  const all = Array.from(document.querySelectorAll('*'));
  const hist = {};
  const positive = [];
  let n_native = 0, n_focusable = 0;
  for (const el of all) {
    const tag = (el.tagName || '').toUpperCase();
    if (NATIVE.indexOf(tag) < 0) continue;
    n_native += 1;
    if (el.disabled === true) continue;
    const raw = el.getAttribute('tabindex');
    const key = raw === null ? 'None' : raw;
    hist[key] = (hist[key] || 0) + 1;
    if (raw === null || raw === '-1') continue;
    n_focusable += 1;
    // ⭐ 只列**正** `tabindex`（`'0'` 是 roving 的那枚，单独统计）
    if (raw !== '0') {
      const host = el.closest('[data-testid]');
      positive.push({tag: tag, tabindex: raw,
                     tid: host ? host.getAttribute('data-testid') : null,
                     aria: el.getAttribute('aria-label')
                           || (el.innerText || '').slice(0, 20) || null,
                     in_node: !!el.closest(nodeSel)});
    }
  }
  return {n_all_elements: all.length, n_native: n_native,
          n_focusable: n_focusable, ti_hist: hist, positive: positive,
          n_positive: positive.length};
}"""
assert TICENSUS_JS.count("slice(") == TICENSUS_JS.count(SLICE_STR), (
    "TICENSUS_JS 里有**非字符串**切片（§131）")
# ⭐ 守卫常量自己必须能匹配上东西（946 的教训）
assert TICENSUS_JS.count("NATIVE.indexOf(tag)") == 1, (
    "`TICENSUS_JS` 自己就匹配不上它要验的东西 —— 这道门恒绿，等于没有门")

# ── 新件：`FOCUSMOVE_JS`（**962 的主角**：判定「焦点是**谁**、在**什么时候**被搬的）
# ⭐⭐⭐⭐ **本批要回答的正是 961 结尾那个「只剩一个方向」**：
#   源站到底**是不是**在 `keydown` **之后**（`focusin` / 宏任务 / rAF）
#   **主动 `focus()` 到下一枚**。
# ⭐⭐⭐⭐ **判决性读数 = 「派发结束那一刻焦点在哪」**：
#   浏览器的**默认动作**（`Tab` 的原生移焦）是在**派发彻底结束之后**才做的
#   ⇒ 所以只要在**派发结束点**（`document` 与 `window` 冒泡里**较晚**的那个）
#   读 `document.activeElement`：
#     · 焦点**已经变了** ⇒ 它**必然**是在**派发过程中**被某段脚本 `focus()` 搬的
#       （默认动作还没轮到跑）⇒ **应用主动搬焦点**（961 的猜想成立）
#     · 焦点**还没变** ⇒ 默认动作之后才搬 ⇒ **浏览器搬的**（那 B 的口径就有问题）
# ⭐ `focusin` 的 `isTrusted` 是**第二道**旁证：
# ⚠️⚠️⚠️ **第一版这里把 `isTrusted` 的语义写错了，被自己抓住**：
#   我写的是「`false` = 脚本调的 `focus()`；`true` = 浏览器/用户动作产生的」
#   ⇒ **错**。**脚本调 `element.focus()` 产生的 focus 事件同样是 trusted**
#   （`isTrusted` 只区分「由用户代理产生」vs「由 `dispatchEvent` 合成」）
#   ⇒ 所以 `isTrusted=True` **不能**用来否掉「应用主动 `focus()`」。
#   ⇒ ⭐ **真正判决性的是「派发末尾 `activeElement` 变没变」**，不是 `isTrusted`。
# ⚠️ **诊断动作必须还原**（承 943 的纪律）：`READ_FM_JS` 会**摘掉全部监听**。
# ⚠️ 纯读：只**加监听 + 读属性**，不调 `focus()`、不改任何属性、不劫持 prototype。
FOCUSMOVE_JS = """() => {
  const WHO = (el) => {
    if (!el || el === document.body) return {tag: el ? el.tagName : null,
                                             tid: null, aria: null,
                                             is_body: true, dom_index: null};
    const host = el.closest ? el.closest('[data-testid]') : null;
    return {tag: el.tagName,
            tid: host ? host.getAttribute('data-testid') : null,
            aria: el.getAttribute('aria-label')
                  || (el.innerText || '').slice(0, 20) || null,
            is_body: false,
            dom_index: null};
  };
  // ⚠️⚠️⚠️ **第一版这里写的是 `if (window.__fm)`，而 `READ_FM_JS` 读完把
  //   `__fm` 置成 `true` 且**再也不清** ⇒ 那个闩锁是**粘的** ⇒ 只有**第 1 按**
  //   真的装了监听，之后每按都直接 `{already:true}` 返回、一个监听都不装
  //   ⇒ 读数只剩 1 按，**而门是绿的**（见 ②）。
  //   ⇒ 改成以 `__fm_rec`（读完会被置 `null`）为判据。
  if (window.__fm_rec) { return {already: true}; }
  // ⚠️⚠️ 第一版这里还有个 `same_target` 字段，比的是 `rec._el0` ——
  //   而 `_el0` **从来没有被赋值过** ⇒ 那个读数**恒为无意义**
  //   ⇒ 已删（**不留恒假的读数**：交付物里每个字段都得是真读数）。
  //   「是不是同一枚」由 Python 侧 `_who_id` 比四个字段来做。
  const rec = {pre: null, post_dispatch: null, prevented_at_end: null,
               t_capture: null, t_bubble: null, t_micro: null, t_task: null,
               t_frame: null, after_micro: null, after_task: null,
               after_frame: null, focusins: [], which_bubble: null,
               n_keys: 0};
  const onKeyCap = (e) => {
    if (rec.n_keys > 0) return;
    rec.n_keys += 1;
    rec.t_capture = performance.now();
    rec.pre = WHO(document.activeElement);
    // ⭐ 只**存引用**，`defaultPrevented` 一律在**派发末尾**才读
    //   （承 892：只在捕获阶段读会**恒真为假**）
    rec._ev = e;
  };
  const onKeyBub = (e) => {
    if (rec.n_keys !== 1) return;
    if (rec.which_bubble === null) rec.which_bubble = 'document';
    rec.t_bubble = performance.now();
    rec.post_dispatch = WHO(document.activeElement);
    rec.prevented_at_end = e.defaultPrevented;
    queueMicrotask(() => {
      rec.t_micro = performance.now();
      rec.after_micro = WHO(document.activeElement);
    });
    setTimeout(() => {
      rec.t_task = performance.now();
      rec.after_task = WHO(document.activeElement);
    }, 0);
    requestAnimationFrame(() => {
      rec.t_frame = performance.now();
      rec.after_frame = WHO(document.activeElement);
    });
  };
  const onKeyBubW = (e) => {
    if (rec.n_keys !== 1) return;
    rec.which_bubble = 'window';
    rec.t_bubble = performance.now();
    rec.post_dispatch = WHO(document.activeElement);
    rec.prevented_at_end = e.defaultPrevented;
  };
  const onFocusIn = (e) => {
    if (rec.n_keys < 1) return;
    const t = performance.now();
    const rel = (rec.t_bubble === null) ? 'during_dispatch'
                : (t <= rec.t_bubble ? 'during_dispatch' : 'after_dispatch');
    rec.focusins.push({t: t, rel: rel, is_trusted: e.isTrusted,
                       who: WHO(e.target)});
  };
  window.addEventListener('keydown', onKeyCap, true);
  document.addEventListener('keydown', onKeyBub, false);
  window.addEventListener('keydown', onKeyBubW, false);
  document.addEventListener('focusin', onFocusIn, true);
  window.__fm_rec = rec;
  window.__fm_off = () => {
    window.removeEventListener('keydown', onKeyCap, true);
    document.removeEventListener('keydown', onKeyBub, false);
    window.removeEventListener('keydown', onKeyBubW, false);
    document.removeEventListener('focusin', onFocusIn, true);
  };
  return {armed: true};
}"""
assert FOCUSMOVE_JS.count("slice(") == FOCUSMOVE_JS.count(SLICE_STR), (
    "FOCUSMOVE_JS 里有**非字符串**切片（§131）")
# ⚠️ 守卫常量自己必须能匹配上东西（946 的教训）
assert FOCUSMOVE_JS.count("onKeyCap") == 3, (
    "`FOCUSMOVE_JS` 里 `onKeyCap` 出现次数不对 —— 这道门恒绿，等于没有门")
# ⚠️⚠️ **第一版的这条守卫写错了，被自己抓住**（还没跑就红了）：
#   我数的是 `__fm_off` 这个**名字**出现几次（= 1 次定义）⇒ 数「名字」根本
#   量不到「监听有没有摘干净」。⇒ 改成量**真正要保的东西**：
#   **`addEventListener` 与 `removeEventListener` 必须配平**（4 : 4），
#   否则就是「装了监听、没还原」⇒ 违反 943 的纯诊断纪律。
assert (FOCUSMOVE_JS.count("addEventListener")
        == FOCUSMOVE_JS.count("removeEventListener") == 4), (
    "`FOCUSMOVE_JS` 的 `add`/`removeEventListener` **没配平** —— "
    "诊断动作必须还原（承 943 的纪律）")

READ_FM_JS = """() => {
  const rec = window.__fm_rec || null;
  if (rec && window.__fm_off) window.__fm_off();
  window.__fm_rec = null; window.__fm_off = null;
  return rec;
}"""

# ── 驱动：走**一圈**，逐按记 DOM 下标 ───────────────────────────────────
# ⚠️⚠️ **绕开 `press_row`**（957 查红、958 复刻侧也证实：它内部的
#   `ARM_FOCUS_JS` 带 `el.focus()`、会把焦点从 chrome 停靠点**拽回节点**）
#   ⇒ 本批所有「按完键焦点在哪 / DOM 下标多少」都**自己发键 + 逐字读**。
# ⚠️ 引导是**关系式**的：走到**第 2 次**命中 `canvas-fixed-toolbar` 为止（= 一圈）。
N_LEAD_CAP = 140

# ⚠️⚠️⚠️ **操作事故（961 自己抓到）**：这一段**原文是 960 照抄来的**、
#   还在讲 960 的两个可能性（shadow root / keydown 改 ti）⇒ 交付的读数文件里
#   **「本批问什么」这项被标错了**（`question` 才是对的）⇒ 已改正并**重跑**。
#   ⇒ 与 960 那个 `OUT` 照抄事故**同类、不同面**：那回毁的是**读数文件**，
#     这回毁的是**读数文件里的一个说明字段** ⇒ 承 960 那条纪律：
#     **`cp` 探针当新基底时，输出路径 / 读数字段 / 说明文字都要逐个核。**
out["domidx_note"] = (
    "⭐ 962 **不问**「顺序长什么样」（954/958/959 都已记过）、"
    "**也不问**「有没有正 `tabindex`」（**961 已查完全文档 = 0 个**）、"
    "**也不问** 960 问过的那两条（**960 已逐条否掉**）—— "
    "962 问的是**时序**：「焦点是**谁**、在**什么时候**被搬的」。"
    "（下面这段原文是 961 照抄来的、留档不改）"
    "⚠️ 961 **不问**「顺序长什么样」（954/958/959 都已记过），"
    "**也不问** 960 问过的那两条（shadow root / keydown 改 ti，"
    "**960 已经逐条否掉**）—— 961 问的是 959/960 读法上的**盲区**："
    "「**全文档**到底有没有**带正 `tabindex`** 的元素」"
    "（959/960 只读**焦点所在的那一枚**，别的候选**根本没读过**）。")
out["out"] = "/tmp/b962-focusmove.json"
out["question"] = (
    "⭐⭐⭐⭐ **961 结尾只剩一个方向**：源站在 `keydown` **之后**"
    "（`focusin` / 宏任务 / rAF）**主动 `focus()` 到下一枚** ⇒ "
    "**这一批就验它**：在**派发结束那一刻**焦点**已经变了**吗？"
    "（浏览器的默认动作是在派发**之后**才做的 ⇒ 派发内就变了 = 必然是脚本搬的）"
    "—— ⭐⚠️ 961 那句「959/960 有个盲区」是**上一批**的问题，留档不改"
    "⇒ 而浏览器排顺序时看的是**所有候选** ⇒ **全文档到底有没有正 "
    "`tabindex` 的元素？**（若那 6 个画布控件带着 `1`/`2`/…，"
    "959/960 一个都没看到 ⇒ 矛盾解开）")
out["blind_spot_960"] = (
    "⚠️⚠️⚠️⭐⭐ **959/960 的读法盲区**（本批的整个来由）："
    "`ti_before`/`ti_after` 读的都是**焦点所在的那一枚**的 `tabindex`；"
    "而 `tabindex='0'` 恰好就是**左栏 roving 那一枚**、其余读出 `None` ⇒ "
    "**「它们没有正 `tabindex`」这个结论只覆盖了「它们各自获得焦点的那一刻」**"
    "⇒ **其它候选**当时的 `tabindex` **959/960 根本没读过**")
out["recheck_892"] = (
    "⚠️⭐⭐ **更正一处出处，但第一版更正本身就错了**（961 自己抓到的）："
    "960 §二 的表把 C 的出处写成 **896**（「早已记过」）—— "
    "**896 确实复读过**：它第 55 行明写「`defaultPrevented` 用 **892 的取法**」、"
    "汇总里有 `keydown_defaultPrevented_seen`、结论是**全 `False`** ⇒ "
    "**960 那处引用不算错**。"
    "**真正该说的是**：「**892 首测**（那一批的主角就是这一项，2/2 `False`）"
    "**＋ 896 复核**（同取法，全 `False`）」⇒ **C 有两个出处、都站得住**。"
    "⚠️⚠️ 我 961 第一版的 audit 写的是「**不是 896**」⇒ **那一句是错的**，"
    "错因是：**只查了 960 指向的那一处，没查「真正测过的还有哪些」**")
# ⚠️⚠️ **口径必须写死，否则下一批会拿两个数互比**（本批差点踩）：
#   `census_ti_hist`（≈50 几）= `RAIL_JS` 扫**左栏那一个容器内部全部 `*`**
#     （含 SVG 之外的一切标签，**不是**「原生可聚焦」口径）；
#   `ti_hist`（≈110 几）= `TICENSUS_JS` 扫**整个 `document` 的原生可聚焦元素**。
#   ⭐ 二者**不可比、不可相加**、**不是同一件事的两个数**。
out["census_scope"] = (
    "⚠️⚠️ **两个普查不是同一件事，数字不可比**："
    "`census_ti_hist` = `RAIL_JS`，范围**只有左栏那一个容器**内部全部 `*`；"
    "`ti_hist` = `TICENSUS_JS`，范围是**整个 `document`** 的原生可聚焦元素。"
    "⇒ 961 的判决**只认 `ti_hist` + `n_positive`**（全文档那一支）")
out["ruler"] = dict(out["ruler"])
out["ruler"]["new_pieces"] = ["RAIL_JS", "DOMIDX_JS", "ROOT_JS"]
out["ruler"]["read_isolation"] = (
    "⭐ **绕开 `press_row`**：它内部的 `ARM_FOCUS_JS` 带 `el.focus()`，"
    "会把焦点从 chrome 停靠点**拽回画布节点**（957 源站实测、958 复刻实测）")

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    n = boot_fn()
    c = {"ci": 0, "mode": "walk", "n_ready": n, "rows": []}
    rec["cells"].append(c)
    dump(out)
    if n == 0:
        c["skipped"] = "左栏入口没出来（`button[aria-label=音频]` 为 0）"
        continue

    cen = ev(RAIL_JS, [RAIL_TID, NODE_SEL])
    c["census_ti_hist"] = cen.get("ti_hist")
    c["n_rail_focusable"] = cen.get("n_focusable")
    print(f"      左栏普查（`RAIL_JS`，范围=左栏容器）：ti 分布 "
          f"{cen.get('ti_hist')}", flush=True)

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    c["n_lead"] = 0
    c["n_rail_stops"] = 0
    c["n_lead_cap_hit"] = False
    # ⚠️⚠️⚠️ **959 只读到「按之后」的 `tabindex`** ⇒ 那个「正 `tabindex` 被否掉」
    #   的结论**只覆盖了按后**。⇒ 960 **成对**读：按**前**先把当前焦点元素的
    #   `tabindex` 记到 `window.__preTi`，按**后**再连同「按前」一起读回来。
    #   ⚠️ `window.__preTi` 只是**传递手段**，不写 `prototype`、不装
    #   `MutationObserver`、不 `reload` ⇒ 仍是**纯读**（承 943 的纯诊断纪律）。
    # ⚠️⚠️⚠️⭐⭐ **第一版的判据是错的，被自己抓住**：
    #   我把 `ti_before`（按**前当前焦点**的 ti）与 `ti_after`（按**后新焦点**的
    #   ti）拿去比 ⇒ 那是**两个不同元素**的 ti，「变了」只说明两者恰好不同，
    #   **不说明任何元素被改过** ⇒ 读出 `n_ti_changed = 2` 也是**无意义的**
    #   ⇒ ⭐ **一个错的判据比没有判据更坏**（942）⇒ 改成**盯住同一个元素**：
    #   按**前**把那个元素的**引用**存进 `window.__preEl`、按**后**回来看
    #   **这个引用**（不是当前焦点）的 ti 有没有变。
    ev("""() => { window.__preTi = undefined; window.__preEl = null; }""")
    while c["n_lead"] < N_LEAD_CAP:
        c["n_lead"] += 1
        # ── ⭐⭐⭐⭐ 962 的**本行重点**：在**按之前**把时序监听装上 ────────────
        #   装在 `window` 捕获（最前）+ `document`/`window` 冒泡（派发末尾）
        #   + `focusin` 捕获 ⇒ 能读出「派发结束那一刻焦点在哪」。
        _armed = ev(FOCUSMOVE_JS)
        # ── 按**前**：记住「此刻焦点元素」的**引用**与它的 tabindex ─────────
        _pre = ev("""([nodeSel]) => {
          const a = document.activeElement;
          window.__preEl = a || null;
          window.__preTi = (a && a.hasAttribute('tabindex'))
                            ? a.getAttribute('tabindex') : null;
          window.__preHad = !!(a && a.hasAttribute('tabindex'));
          return {tid: a ? (a.closest('[data-testid]')
                    ? a.closest('[data-testid]').getAttribute('data-testid')
                    : null) : null};
        }""", [NODE_SEL])
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        # ⚠️⚠️ `setTimeout(0)` 与 `requestAnimationFrame` 的取样**在按后**才跑完
        #   ⇒ `SETTLE` 必须**大于**它们（350ms 足够，承 952–961 的同一常量）
        _fm = ev(READ_FM_JS)          # ⭐ 读走**并摘监听**（诊断动作必须还原）
        d = ev(DOMIDX_JS, [NODE_SEL])
        r = ev(ROOT_JS, [NODE_SEL])
        # ⭐⭐⭐⭐ 961 的**本行重点**：普查**全文档**所有原生可聚焦元素的 `tabindex`
        _tc = ev(TICENSUS_JS, [NODE_SEL])
        # ⭐⭐ **同一个元素**（= 按前那枚）**离开之后**的 tabindex
        _same = ev("""() => {
          const e = window.__preEl;
          if (!e) return {still: null, ti_now: null, had: null};
          return {still: !!(e.isConnected),
                  ti_now: e.hasAttribute('tabindex')
                          ? e.getAttribute('tabindex') : null,
                  had: !!e.hasAttribute('tabindex')};
        }""")
        row = {"phase": "walk", "k": c["n_lead"], "step": 0, "key": "Tab",
               "seq": c["n_lead"], "who_before": None, "armed_before": None,
               "armed_after": None, "no_ti_before": [], "no_ti_after": [],
               "no_ti_capped": False, "pointer_before": None,
               "pointer_after": None, "focus_moved": True, "bit": False,
               "n_added": 0, "identity_stable": None, "removed": [],
               "added": [], "changed": [], "diff_ids": [], "n_without_ti": 0,
               "active_before": None, "active_after": ev(FOCUS_JS, [NODE_SEL]),
               "dom_index": d.get("dom_index"),
               "tabindex": d.get("tabindex"),
               "dom_tid": d.get("tid"), "dom_tag": d.get("tag"),
               "dom_aria": d.get("aria"),
               # ⭐ 960：root 归属
               "root_kind": r.get("root_kind"),
               "in_shadow": r.get("in_shadow"),
               "root_host_tid": r.get("root_host_tid"),
               # ⭐⭐ 「**同一枚**离开之后」ti：before=那枚离开前、after=它离开后
               "ti_before": r.get("ti_before"),
               "ti_after": _same.get("ti_now"),
               "same_el_still_connected": _same.get("still"),
               # ⭐ 961：**全文档** tabindex 普查（逐按一次）
               "ti_hist": _tc.get("ti_hist"),
               "n_native": _tc.get("n_native"),
               "n_focusable": _tc.get("n_focusable"),
               "n_positive": _tc.get("n_positive"),
               "positive": _tc.get("positive"),
               # ⭐⭐⭐⭐ 962：这一按的**焦点时序原始读数**（整段 `FOCUSMOVE_JS`）
               "fm": _fm,
               "fm_armed": _armed,
               "who_after": d}
        c["rows"].append(row)
        if d.get("tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    ev("""() => { window.__preTi = undefined; window.__preHad = undefined; window.__preEl = null; }""")

    # ⭐ 一圈 = 第 1 个左栏停靠点**含**、第 2 个**不含**（958 同一个坑）
    _rs = [r["seq"] for r in c["rows"]
           if r.get("dom_tid") == RAIL_TID]
    c["rail_seqs"] = _rs
    c["leg_lo"] = _rs[0] if _rs else 1
    c["leg_hi"] = (_rs[1] - 1) if len(_rs) > 1 else c["n_lead"]
    leg = [r for r in c["rows"] if c["leg_lo"] <= r["seq"] <= c["leg_hi"]]
    c["leg"] = [{"seq": r["seq"], "stop": stop_name({"who_after": r["who_after"]}),
                 "dom_index": r["dom_index"], "tabindex": r["tabindex"],
                 "dom_tid": r["dom_tid"], "dom_aria": r["dom_aria"],
                 # ⭐ 960 新增的三个读数，逐字带过来
                 "root_kind": r.get("root_kind"),
                 "in_shadow": r.get("in_shadow"),
                 "root_host_tid": r.get("root_host_tid"),
                 "ti_before": r.get("ti_before"),
                 "ti_after": r.get("ti_after"),
                 # ⭐ 961 的**全文档**普查（逐按一次）
                 "ti_hist": r.get("ti_hist"),
                 "n_native": r.get("n_native"),
                 "n_focusable": r.get("n_focusable"),
                 "n_positive": r.get("n_positive"),
                 "positive": r.get("positive")}
                for r in leg]
    _outs = [x for x in c["leg"]
             if (x["stop"] or "").startswith("out:")]
    c["leg_out"] = _outs
    # ── ⭐ 960 的两个判决，各自带**可证伪**的判据 ─────────────────────
    # ① **shadow root？**（959 留下的可能性之一）
    c["n_in_shadow"] = sum(1 for x in _outs if x.get("in_shadow"))
    c["all_out_in_document"] = bool(_outs) and all(
        (x.get("root_kind") or "") == "#document" for x in _outs)
    c["root_kinds"] = sorted({(x.get("root_kind") or "?") for x in _outs})
    # ② **keydown 里改 `tabindex`？**（959 只读到「按后」）
    c["n_ti_changed"] = sum(1 for x in _outs
                            if x.get("ti_before") != x.get("ti_after"))
    c["ti_pairs"] = [{"seq": x["seq"], "tid": x["dom_tid"],
                      "before": x.get("ti_before"), "after": x.get("ti_after"),
                      "same_el_connected": x.get("same_el_still_connected")}
                     for x in _outs]
    # ⭐⭐ **单调不降**（959 判决，本批复核）
    _di = [x["dom_index"] for x in _outs if x["dom_index"] is not None]
    c["dom_index_monotonic"] = bool(_di) and all(
        _di[i] <= _di[i + 1] for i in range(len(_di) - 1))
    c["n_dom_index_missing"] = sum(1 for x in _outs if x["dom_index"] is None)
    c["n_leg_out"] = len(_outs)
    c["n_leg_rail"] = sum(1 for x in _outs
                          if x["dom_tid"] == RAIL_TID)
    # ── ⭐ 961 的判决：**全文档有没有「正 `tabindex`」** ─────────────────
    _hists = {json.dumps(x["ti_hist"], sort_keys=True) for x in _outs
              if x.get("ti_hist")}
    c["ti_hist_stable"] = bool(len(_hists) == 1)
    c["ti_hist"] = _outs[0]["ti_hist"] if _outs else None
    c["n_positive_max"] = max([x.get("n_positive") or 0 for x in _outs] or [0])
    _pos = [x for x in _outs if (x.get("n_positive") or 0) > 0]
    c["n_out_with_positive"] = len(_pos)
    c["positive_sample"] = (_outs[0].get("positive") or []) if _outs else []
    c["positive_tids"] = sorted({p.get("tid")
                                 for x in _outs
                                 for p in (x.get("positive") or [])})
    # ── ⭐⭐⭐⭐ 962 的判决：**焦点是「谁」、在「什么时候」被搬的** ───────────
    # ⚠️ **身份只比四个字段**（tag/tid/aria/is_body）—— DOM 绝对下标逐轮会漂，
    #   那是 959 记过的坑（959/960 只能比**相对关系**）
    def _who_id(w):
        if not isinstance(w, dict):
            return None
        return (w.get("tag"), w.get("tid"), w.get("aria"), w.get("is_body"))

    c["n_fm_rows"] = sum(1 for r in c["rows"] if r.get("fm"))
    _fm_rows = [r["fm"] for r in c["rows"] if r.get("fm")]
    c["n_fm_armed"] = sum(1 for r in c["rows"]
                          if (r.get("fm_armed") or {}).get("armed"))
    # ⭐ 判决 A：**派发结束那一刻**焦点**已经变了**的有几按
    #   ⇒ 那些是**在派发过程中**被脚本 `focus()` 搬的（默认动作还没轮到跑）
    c["n_moved_before_dispatch_end"] = sum(
        1 for f in _fm_rows
        if _who_id(f.get("post_dispatch")) is not None
        and _who_id(f.get("post_dispatch")) != _who_id(f.get("pre")))
    # ⭐ 判决 B：**第一个 `focusin`** 落在派发内还是派发后、是不是 `isTrusted`
    _rel, _trust, _bubble, _prev = {}, {}, {}, {}
    for f in _fm_rows:
        _fis = f.get("focusins") or []
        if not _fis:
            continue
        _rel[_fis[0].get("rel")] = _rel.get(_fis[0].get("rel"), 0) + 1
        _trust[str(_fis[0].get("is_trusted"))] = (
            _trust.get(str(_fis[0].get("is_trusted")), 0) + 1)
        _bubble[f.get("which_bubble")] = _bubble.get(f.get("which_bubble"), 0) + 1
        _prev[str(f.get("prevented_at_end"))] = (
            _prev.get(str(f.get("prevented_at_end")), 0) + 1)
    c["first_focusin_rel_hist"] = _rel
    c["first_focusin_trusted_hist"] = _trust
    c["which_bubble_hist"] = _bubble
    c["prevented_at_end_hist"] = _prev
    c["n_no_focusin"] = sum(1 for f in _fm_rows if not (f.get("focusins") or []))
    # ⭐ 判决 C：**派发结束后**（宏任务里）才变的 ⇒ 那才是浏览器默认动作
    c["n_moved_only_after_dispatch"] = sum(
        1 for f in _fm_rows
        if _who_id(f.get("post_dispatch")) == _who_id(f.get("pre"))
        and _who_id(f.get("after_task")) is not None
        and _who_id(f.get("after_task")) != _who_id(f.get("pre")))
    # ── ⭐⭐⭐⭐⭐ 962 的**头号判决**：`dom_index` 的**下降次数** ────────────
    # ⚠️⚠️⚠️ **959 的判决（「`Tab` 序 ≠ DOM 序」）是用「单调不降」下的**，
    #   而**环形**走查本来就**必然**有下降（走完文档尾部要折返回头部）⇒
    #   「非单调」**推不出「乱序」**。⇒ 这里量的是**关系式**的东西：
    #   **下降了几次、每次是不是「从高索引跳回低索引」**。
    _seq_di = [(r["seq"], r["dom_index"]) for r in c["rows"]
               if r.get("dom_index") is not None]
    c["n_dom_index_descents"] = sum(
        1 for i in range(len(_seq_di) - 1)
        if _seq_di[i + 1][1] < _seq_di[i][1])
    c["dom_index_descents"] = [{"at_seq": _seq_di[i][0],
                                "from": _seq_di[i][1], "to": _seq_di[i + 1][1]}
                               for i in range(len(_seq_di) - 1)
                               if _seq_di[i + 1][1] < _seq_di[i][1]]
    # ⭐ 分段：**只看 out 段**（那 18 个 `out:` chrome 停靠点）——
    #   ⚠️⚠️⚠️ **第一版这里错拿 `leg` 当「out 段」** ⇒ `leg` 是
    #   `leg_lo..leg_hi`（这轮 = 第 84–140 按），而**这一轮没走满一圈**
    #   （140 上限前没到第 2 个左栏停靠点）⇒ `leg` 里**混着 39 个画布节点按**
    #   ⇒ 读出 `29 / 57` ⇒ ⭐ **连我自己的结论文案都和这个数字自相矛盾**
    #   （文案写「几乎全是浏览器搬的」、数字却近一半）⇒ **文案必须跟着数字走**。
    #   ⇒ 改口径：分母 = `_outs`（`leg_out`）的按数，不是 `leg` 的。
    _legseq = {x["seq"] for x in _outs}
    c["n_moved_in_dispatch_leg"] = sum(
        1 for r in c["rows"] if r["seq"] in _legseq and r.get("fm")
        and _who_id((r["fm"] or {}).get("post_dispatch")) is not None
        and _who_id((r["fm"] or {}).get("post_dispatch"))
        != _who_id((r["fm"] or {}).get("pre")))
    c["n_leg_rows"] = len(_legseq)
    c["fm_sample"] = [{
        "k": r["k"], "pre": (r.get("fm") or {}).get("pre"),
        "post_dispatch": (r.get("fm") or {}).get("post_dispatch"),
        "after_task": (r.get("fm") or {}).get("after_task"),
        "n_focusins": len((r.get("fm") or {}).get("focusins") or []),
        "first_rel": (((r.get("fm") or {}).get("focusins") or [{}])[0]).get("rel"),
        "first_trusted": (((r.get("fm") or {}).get("focusins") or [{}])[0]
                           ).get("is_trusted"),
        "prevented_at_end": (r.get("fm") or {}).get("prevented_at_end"),
    } for r in c["rows"] if r.get("fm")][:24]
    c["verdict"] = (
        f"一圈（第 {c['leg_lo']}–{c['leg_hi']} 按）：out 段 {c['n_leg_out']} 个、"
        f"其中左栏 {c['n_leg_rail']} 个；**DOM 下标单调不降 = "
        f"{c['dom_index_monotonic']}**；在 shadow root 里的 = "
        f"{c['n_in_shadow']}；按前/按后 ti 变过的 = {c['n_ti_changed']}；"
        f"⭐ **全文档带正 `tabindex` 的最多 {c['n_positive_max']} 个**、"
        f"out 段里 **{c['n_out_with_positive']}** 个按**看到了**正 `tabindex`")
    c["verdict_fm"] = (
        f"⭐ **派发结束前焦点就变的 = {c['n_moved_before_dispatch_end']} / "
        f"{c['n_fm_rows']} 按**；**只在派发后才变的 = "
        f"{c['n_moved_only_after_dispatch']}**；"
        f"第一个 `focusin` 落在 {c['first_focusin_rel_hist']}、"
        f"`isTrusted` {c['first_focusin_trusted_hist']}；"
        f"派发末尾的 `defaultPrevented` {c['prevented_at_end_hist']}")
    # ⚠️ **文案跟着数字走**：先算出比例，再决定这句话怎么说
    _legm = c["n_moved_in_dispatch_leg"]
    _legn = c["n_leg_rows"]
    c["verdict_domi"] = (
        f"⭐⭐⭐ `dom_index` 下降 **{c['n_dom_index_descents']} 次** "
        f"（方向：{['high_to_low' if (d.get('from') or 0) > (d.get('to') or 0) else 'low_to_high' for d in c['dom_index_descents']]}；"
        f"**绝对下标逐轮会漂、只钉方向**）；"
        f"⭐ **out 段（{_legn} 个 chrome 停靠点）里派发内搬焦点的 = "
        f"{_legm}** ⇒ "
        + ("**全部是浏览器搬的**" if _legm == 0 else
           f"**{_legm} 个是应用在派发中搬的**"))
    print(f"      ⇒ {c['verdict']}", flush=True)
    if _outs:
        print(f"      全文档原生可聚焦 {c['leg'][0].get('n_native')}、"
              f"顺序里 {c['leg'][0].get('n_focusable')}、"
              f"ti 分布 {c['ti_hist']}", flush=True)
    for p in c["positive_sample"][:20]:
        print(f"        · 正ti={p.get('tabindex')!r:5s} {p.get('tag'):8s} "
              f"{(p.get('aria') or '')[:20]!s:22s} tid={p.get('tid')}",
              flush=True)
    dump(out)

# ⭐ 两轮比较**必须在循环之外**
n_cells = 1
out["n_cells_total"] = n_cells
_got = [{"verdict": r["cells"][0].get("verdict"),
         "verdict_fm": r["cells"][0].get("verdict_fm"),
         "verdict_domi": r["cells"][0].get("verdict_domi"),
         # ⚠️⚠️⚠️ **第一版这里比的是 `dom_index_descents` 的**绝对值**
         #   ⇒ `reps_identical` **假红**（959 早就记过：DOM 绝对下标**逐轮会漂**，
         #   本轮两轮正好差 2）⇒ **绝对下标不是可比的量**。
         #   ⇒ 改成比**关系式**：下降**几次** + 每次**是不是「高索引跳回低索引」**。
         "n_descents": r["cells"][0].get("n_dom_index_descents"),
         "descent_directions": [
             ("high_to_low" if (d.get("from") or 0) > (d.get("to") or 0)
              else "low_to_high")
             for d in (r["cells"][0].get("dom_index_descents") or [])],
         "n_moved_in_dispatch_leg": r["cells"][0].get("n_moved_in_dispatch_leg"),
         "ti_pairs": r["cells"][0].get("ti_pairs"),
         "root_kinds": r["cells"][0].get("root_kinds"),
         "n_in_shadow": r["cells"][0].get("n_in_shadow"),
         "n_ti_changed": r["cells"][0].get("n_ti_changed"),
         "monotonic": r["cells"][0].get("dom_index_monotonic"),
         "n_leg_out": r["cells"][0].get("n_leg_out"),
         "n_leg_rail": r["cells"][0].get("n_leg_rail"),
         "n_moved_before_dispatch_end":
             r["cells"][0].get("n_moved_before_dispatch_end"),
         "n_moved_only_after_dispatch":
             r["cells"][0].get("n_moved_only_after_dispatch"),
         "first_focusin_rel_hist":
             r["cells"][0].get("first_focusin_rel_hist"),
         "first_focusin_trusted_hist":
             r["cells"][0].get("first_focusin_trusted_hist"),
         "prevented_at_end_hist": r["cells"][0].get("prevented_at_end_hist")}
        for r in out["runs"]]
out["reps_identical"] = bool(len(_got) == REPS and _got[0] == _got[1])
out["ruler_actually_moved"] = bool(
    out["runs"] and out["runs"][0]["cells"][0].get("rows"))
out["design_gates"] = {
    "js_py_verbatim_from_955": True,
    "classify_verbatim_from_954": True,
    "boot_fn_verbatim_from_952": True,
    "zero_button_clicks": True,
    "read_isolated_from_press_row": True,
    "reps_identical": out["reps_identical"],
    "ruler_actually_moved": out["ruler_actually_moved"],
    "dom_index_monotonic": bool(all(
        r["cells"][0].get("dom_index_monotonic") is True
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    "no_missing_dom_index": bool(all(
        r["cells"][0].get("n_dom_index_missing") == 0
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    # ⭐ 960 的两道**判决**门（**可红**，红的就是被否掉的解释）
    "all_out_in_document": bool(all(
        r["cells"][0].get("all_out_in_document") is True
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    "no_ti_changed_by_tab": bool(all(
        r["cells"][0].get("n_ti_changed") == 0
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    "keys_disjoint": bool(not (RAW_KEYS & DERIVED_KEYS)),
    # ⭐ 961 自己的**判决门**（**可红**，红的就是「正 `tabindex`」没被否掉）
    "no_positive_tabindex": bool(all(
        (r["cells"][0].get("n_positive_max") == 0
         and r["cells"][0].get("positive_tids") == []
         and r["cells"][0].get("n_out_with_positive") == 0)
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    # ⚠️ 这一道保证「两轮看到的是**同一份**分布」——否则「0 个正 ti」只是某一轮的快照
    "ti_hist_stable_across_stops": bool(all(
        r["cells"][0].get("ti_hist_stable") is True
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    # ── ⭐⭐⭐⭐ 962 自己的**判决门**（**可红**）──────────────────────────
    # ⚠️ **不是**「焦点有没有被搬」那种恒真门（每按必然被搬）⇒
    #   这里量的是**三条可证伪的事实**，红的就说明 961 的猜想被否：
    #   ① 每按都**真的装上了监听**（否则整批读数是空的）
    # ⚠️⚠️⚠️ **第一版这条门是恒真的**：`n_fm_armed == n_fm_rows` 在「装 1 按、
    #   测 1 按」时也成立 ⇒ 闩锁 bug 下面它是**绿的**。
    #   ⇒ 改成**和按压总数**比：漏一按就红。
    "fm_armed_every_press": bool(all(
        (r["cells"][0].get("n_fm_rows") or 0) > 0
        and r["cells"][0].get("n_fm_armed") == r["cells"][0].get("n_lead")
        and r["cells"][0].get("n_fm_rows") == r["cells"][0].get("n_lead")
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    #   ② **每一按都听到了 `focusin`**（漏听 ⇒ 读数不可信，不是判决）
    "focusin_heard_every_press": bool(all(
        r["cells"][0].get("n_no_focusin") == 0
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    #   ③ 961 的猜想：**派发结束前**焦点就已改变 ⇒ 应用**在派发中**主动 `focus()`
    #      ⇒ 这一道**红**就说明「应用主动搬焦点」被否掉
    "app_moves_focus_before_dispatch_end": bool(all(
        (r["cells"][0].get("n_moved_before_dispatch_end") or 0)
        == (r["cells"][0].get("n_fm_rows") or -1)
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    # ── ⭐⭐⭐⭐⭐ 962 的**头号判决**（**可红**）──────────────────────────
    # ④ **`dom_index` 的下降次数**：环形走查里「文档尾部 → 头部」那**一次**折返
    #    是**应有**的 ⇒ 「非单调」**不等于**「乱序」。
    #    这一道量的是**关系**：下降几次、且每次是不是「高索引跳回低索引」。
    "dom_index_descents_are_wraps_only": bool(all(
        r["cells"][0].get("n_dom_index_descents") is not None
        and all(d.get("from") > d.get("to")
                for d in (r["cells"][0].get("dom_index_descents") or []))
        for r in out["runs"] if "skipped" not in r["cells"][0])),
    # ⑤ ⭐ **out 段（chrome 停靠点）里几乎没有被应用在派发中搬走** ⇒
    #    961 的猜想对**它关心的那一段**不成立
    "out_stops_moved_by_browser": bool(all(
        (r["cells"][0].get("n_moved_in_dispatch_leg") or 0) == 0
        for r in out["runs"] if "skipped" not in r["cells"][0])),
}
print("\n设计门：", out["design_gates"], flush=True)
for r in out["runs"]:
    for c in r["cells"]:
        if "skipped" in c:
            print(f"rep{r['rep']}：⚠️ {c['skipped']}", flush=True)
        else:
            print(f"rep{r['rep']}：{c['verdict']}", flush=True)
            print(f"rep{r['rep']}：{c['verdict_fm']}", flush=True)
            print(f"rep{r['rep']}：{c['verdict_domi']}", flush=True)
dump(out)
print("\n读数已写入", OUT, flush=True)
