#!/usr/bin/env python3
r"""batch 970 **复刻侧**探针（**纯诊断 / 零节点点击**）：⭐⭐⭐⭐⭐ **同口径重测 out 段** ——
每个停靠点**同时**记「**自身** `data-testid`」与「**最近祖先** `data-testid`」两个字段。

## 这一批的来由（**两次同一种错**）

- **批 968b**：拿 **954 的历史基线**当本轮源站一侧的对照
  ⇒ 把「基线过期」误读成「实现有缺陷」
- **批 969**：拿 **复刻的「自身 testid」**去比 **源站的「最近祖先 testid」**
  ⇒ 又是**口径不同当同一件事比**

⚠️⚠️ **这里原本也是一张两行表格（首格写着批次号）** ⇒ pre-commit 钩子的
`added_batch_numbers` 用 `^\+\|\s*(\d+)[a-z]?\s*\|` 抓「新增的批次行」
⇒ `| 968b |` 会被当成本仓的**新增批次**、而本地绿构建只走到 274 ⇒ **提交被拦**
⇒ **钩子对、我错** ⇒ **改排版、不绕过钩子**（948 早就为此栽过一次，
**三处栽在同一处**）

⇒ 969 的读数里其实**两个字段都记了**，翻出来一看：源站 out 段 17 个停靠点里
**恰好 2 个「自身没有 `data-testid`」**：

- `文本`（左栏入口）：自身 `None`、最近祖先 **`canvas-fixed-toolbar`**
- `更多`：自身 `None`、最近祖先 **`canvas-editor-menu`**

⇒ ⚠️⚠️ 而 `verify-jimeng-batch816-anchors.py` 早就写过：
**「「更多」源站没有 testid，复刻保留自造的 `canvas-more-trigger`」**
并把它列进 `KNOWN_CLONE_ONLY` ⇒ **那是「有意偏离」、有理由的**
⇒ ⇒ ⭐⭐⭐ **969 那句「唯一真实的结构差异是「更多」的 testid」是错的** ——
复刻的处置**本来就对**，是我**读错了字段**

## ⭐ 为什么必须「同口径」

复刻把 `data-testid` 放在**元素自己**上 ⇒ `closest('[data-testid]')` **恰好**返回自身；
源站把 testid 放在**祖先容器**上 ⇒ `closest()` 返回的是**容器**。

⇒ ⚠️⚠️ **只读 `closest()` 的一侧，在两侧天然不可直接比**
⇒ 本批在**复刻侧**把**两个字段都读出来**，与 969 的源站读数**同口径**重做对照。

## 纪律（承 942–969）

1. ⭐⭐⭐ **同一个字段要对比，就得用同一个口径**（本批的整个来由）
2. ⭐ **每道门挂独立分母**；门要能红、也要能不红
3. ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）
4. ⚠️ **落盘排在所有后处理之前**
5. ⚠️ 复刻 `data-testid` 带时间戳 ⇒ **一律按 `tag` + `aria` + 两个 tid 字段**对账，
   **不按时间戳**对账

## 计费边界

**复刻是本地应用，本批零计费。** 插节点走**左栏入口**（不是节点本体）；
⛔ 守卫拦在 `mouse.click` **之前**。按键只有 `Tab`。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe970_owntid_ck.py
"""

import atexit
import json
import pathlib
import time

OUT = "/tmp/b970-replica-owntid.json"
REPS = 2
SETTLE = 350        # ms（照 952–969）
BLANK_WAIT = 900    # ms（照 952–969）
KINDS = []          # ⭐ **不插节点**：本批只量 **out 段**，画布内容不影响它
N_LEAD_CAP = 140     # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = ".react-flow__node"

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

P967 = pathlib.Path(__file__).with_name("jimeng_probe967_armptr_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "self_tid", "closest_tid", "tag", "aria", "title", "id",
    "tabindex", "tab_index_prop", "is_focusable", "rect", "kind",
    "fired", "armed", "n_minus1", "n_nodes_snap", "landed", "node_tid",
    "node_index", "host_tid", "trusted", "installed", "off_after_read",
    "blank", "has_flow", "n_ready_nodes", "flow_aria", "all_kinds",
    "kinds_found", "node_ti_hist",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "target", "url", "reps", "rail_tid", "n_lead_cap", "node_sel", "kinds",
    "question", "ruler", "baseline", "runs", "recon", "gate_notes",
    "design_gates", "what_970_measures", "discipline_970", "skip_note",
    "same_ruler_note", "inserted",
    "ci", "mode", "rows", "n_ready", "n_lead", "n_lead_cap_hit",
    "n_rail_stops", "n_install", "n_read", "off_null_at_end",
    "n_rows", "n_fired_total", "fired_eq_rows", "listener_balanced",
    "out_rows", "n_out_presses", "out_ids", "out_ids_self",
    "self_eq_closest", "n_self_eq_closest", "n_self_none",
    "self_none_aria", "panel_rows",
    "keys_disjoint", "reps_agree_out",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"


# ── ⭐ 四段仪器**逐字来自 967**（与 968/969 同一把尺子）────────────────
_p967src = P967.read_text(encoding="utf-8") if P967.exists() else ""
assert _p967src, "读不到 967 的源码 —— 尺子没得比，这道门恒绿"


def _grab(name):
    # ⚠️⚠️ 这里**不能**在 docstring 里写出三引号本身（会当场自噬）
    """从 967 的**文件内容**里把 `NAME = <三引号>…<三引号>` 那一段原样抠出来。"""
    marker = name + ' = """'
    i = _p967src.index(marker) + len(marker)
    j = _p967src.index('"""', i)
    return _p967src[i:j]


INSTALL_JS = _grab("INSTALL_JS")
READ_JS = _grab("READ_JS")
OFF_NULL_JS = _grab("OFF_NULL_JS")
BLANK_JS = _grab("BLANK_JS")
del _grab
for _n, _s in (("INSTALL_JS", INSTALL_JS), ("READ_JS", READ_JS),
               ("OFF_NULL_JS", OFF_NULL_JS), ("BLANK_JS", BLANK_JS)):
    assert _s in _p967src, f"{_n} 抠出来**不等于** 967 里的那份 ⇒ 尺子分家了"
del _n, _s
assert INSTALL_JS.count("__ap_off = () => {") == 1, (
    "`INSTALL_JS` 里没有可摘的句柄 ⇒ 「装/摘配平」这道门恒绿")
assert (INSTALL_JS.count("addEventListener") == 3
        and INSTALL_JS.count("removeEventListener") == 3), (
    "装 3 个就必须摘 3 个（配平门自己数一遍）")

# ── 新件：`OWN_JS`（**纯读**：本批唯一的重点，两个字段都读）────────────
# ⭐⭐⭐ `self_tid` = **元素自己**的 `data-testid`；
#    `closest_tid` = `closest('[data-testid]')` 的结果（**可能是祖先**）
# ⇒ **两个字段必须同时读**，否则一侧记自身、另一侧记祖先 ⇒ **不可比**
OWN_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {self_tid: null, closest_tid: null, tag: null, aria: null,
                  title: null, id: null, tabindex: null,
                  tab_index_prop: null, is_focusable: null, rect: null,
                  kind: null};
  const node = a.closest(nodeSel);
  const r = a.getBoundingClientRect();
  const c = a.closest('[data-testid]');
  return {
    self_tid: a.getAttribute('data-testid'),
    closest_tid: c ? c.getAttribute('data-testid') : null,
    tag: (a.tagName || '').toUpperCase(),
    aria: a.getAttribute('aria-label') || a.getAttribute('title') || null,
    title: a.getAttribute('title'),
    id: a.id || null,
    tabindex: a.hasAttribute('tabindex') ? a.getAttribute('tabindex') : null,
    tab_index_prop: a.tabIndex,
    is_focusable: a.tabIndex >= 0,
    rect: [Math.round(r.x), Math.round(r.y),
           Math.round(r.width), Math.round(r.height)],
    kind: !node ? 'out' : (a === node ? 'self' : 'inner'),
  };
}"""
assert OWN_JS.count("slice(") == 0, "OWN_JS 不该有切片（§131）"
# ⭐⭐ **两个字段必须都在**，少一个这道门就恒红/恒绿
assert OWN_JS.count("self_tid: a.getAttribute('data-testid'),") == 1, (
    "`OWN_JS` 里没有「自身 testid」这一读数 ⇒ 这道门恒绿")
assert OWN_JS.count("closest_tid: c ? c.getAttribute('data-testid') : null,") == 1, (
    "`OWN_JS` 里没有「最近祖先 testid」这一读数 ⇒ 这道门恒绿")

# ── 新件：`READY_JS`（**纯读**，逐字承 968）────────────────────────────
READY_JS = """([nodeSel, kinds]) => {
  const flow = document.querySelector('.react-flow');
  const nodes = document.querySelectorAll(nodeSel);
  const found = kinds.map(k =>
    !!document.querySelector('button[aria-label="' + k + '"]'));
  return {has_flow: !!flow,
          n_ready_nodes: nodes.length,
          flow_aria: flow ? flow.getAttribute('aria-label') : null,
          all_kinds: found.every(Boolean),
          kinds_found: found,
          node_ti_hist: Array.from(nodes).reduce((acc, el) => {
            const k = el.getAttribute('tabindex');
            const key = k === null ? 'None' : k;
            acc[key] = (acc[key] || 0) + 1;
            return acc;
          }, {})};
}"""
assert READY_JS.count("slice(") == 0, "READY_JS 不该有切片"
assert READY_JS.count("document.querySelectorAll(nodeSel)") == 1, (
    "`READY_JS` 自己就匹配不上它要验的东西 —— 这道门恒绿")

_URL = "http://localhost:4317/jimeng/canvas/demo"

from playwright.sync_api import sync_playwright   # noqa: E402

_pw = sync_playwright().start()
_browser = _pw.chromium.launch()
page = _browser.new_context(
    viewport={"width": 1512, "height": 1200}).new_page()
atexit.register(lambda: (_browser.close(), _pw.stop()))


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


def boot_ck():
    """复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**。"""
    page.goto(_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev(READY_JS, [NODE_SEL, KINDS])


def insert_kinds():
    """本批 `KINDS` 为空 ⇒ **不插任何节点**（out 段与画布内容无关）。"""
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


out = {
    "target": "replica", "url": _URL, "reps": REPS, "rail_tid": RAIL_TID,
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL, "kinds": KINDS,
    "question": "⭐⭐⭐⭐⭐ **同口径重测复刻 out 段**：每个停靠点**同时**记"
                "「**自身** `data-testid`」与「**最近祖先** `data-testid`」—— "
                "969 拿复刻的**自身 tid** 去比源站的**祖先 tid**，**口径不同**",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "how_proved": "⭐ `_grab(name)` 从 967 的**文件内容**里抠出那一段，"
                      "再 `assert _s in _p967src` ⇒ 与 968/969/970 **同一把尺子**",
        "new_pieces": ["OWN_JS", "READY_JS"],
        "why_own_is_read_not_instrument": "⭐ `OWN_JS` **只读属性**、"
                                          "**从不调 `focus()`** ⇒ 不污染焦点读数",
        "insert_kinds": "⭐ 本批 `KINDS` 为空 ⇒ **零插入、零节点点击**"
                        "（out 段与画布内容无关）",
        "own_ruler_note": "⭐⭐ 与 969 的 `FINGER_JS` **同口径**："
                          "969 也同时记了 `tid`（自身）与 `host_tid`（祖先）"
                          "⇒ 本批的读数**可以和 969 的读数直接对账**",
    },
    "baseline_source_969": {
        "n_out_stops": 17,
        "self_tid_none_count": 2,
        "self_tid_none_aria": ["文本", "更多"],
        "source_816_decision": "⚠️⚠️ `verify-jimeng-batch816-anchors.py` 早就写："
                               "**「「更多」源站没有 testid，复刻保留自造的 "
                               "`canvas-more-trigger`**」，并列进 "
                               "`KNOWN_CLONE_ONLY` ⇒ **那是「有意偏离」、有理由的**",
        "note": "⚠️ 这些是**源站**的数 ⇒ 判据是**关系式**的、不是绝对值",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    rd = boot_ck()
    c = {"ci": 0, "mode": "walk", "n_ready": rd.get("n_ready_nodes"),
         "rows": [], "n_install": 0, "n_read": 0, "n_rail_stops": 0,
         "n_lead_cap_hit": False, "has_flow": rd.get("has_flow"),
         "flow_aria": rd.get("flow_aria"), "all_kinds": rd.get("all_kinds"),
         "kinds_found": rd.get("kinds_found"),
         "node_ti_hist": rd.get("node_ti_hist")}
    rec["cells"].append(c)
    dump(out)
    if not rd.get("has_flow"):
        c["skip_note"] = "画布根没出来 ⇒ 本格什么也没测"
        continue

    c["inserted"] = insert_kinds()
    page.wait_for_timeout(800)
    dump(out)

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])       # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    c["n_lead"] = 0
    while c["n_lead"] < N_LEAD_CAP:
        c["n_lead"] += 1
        inst = ev(INSTALL_JS, [NODE_SEL])
        if inst.get("installed"):
            c["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ap = ev(READ_JS)
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o}
        c["rows"].append(row)
        if o.get("closest_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    c["off_null_at_end"] = ev(OFF_NULL_JS)
    dump(out)

    # ── 后处理（全部在 `dump` 之后）──────────────────────────────
    rows = c["rows"]
    out_rows = []
    for r in rows:
        o = r["own"]
        if o.get("kind") == "out":
            out_rows.append((r["k"], o))
    c["n_out_presses"] = len(out_rows)
    # ⭐ 两个字段各出一张清单，**并排**摆出来（口径不同就一眼看得见）
    c["out_ids"] = sorted({(o.get("tag"), o.get("aria"), o.get("closest_tid"))
                           for _k, o in out_rows})
    c["out_ids_self"] = sorted({(o.get("tag"), o.get("aria"), o.get("self_tid"))
                                for _k, o in out_rows})
    eq = 0
    for _k, o in out_rows:
        if o.get("self_tid") == o.get("closest_tid"):
            eq += 1
    c["n_self_eq_closest"] = eq
    c["self_eq_closest"] = (eq == len(out_rows))
    none_rows = [(k, o) for k, o in out_rows if o.get("self_tid") is None]
    c["n_self_none"] = len(none_rows)
    c["self_none_aria"] = [o.get("aria") for _k, o in none_rows]
    c["panel_rows"] = [
        {"k": k, "tag": o.get("tag"), "aria": o.get("aria"),
         "self_tid": o.get("self_tid"), "closest_tid": o.get("closest_tid"),
         "tabindex": o.get("tabindex"), "tab_index_prop": o.get("tab_index_prop"),
         "is_focusable": o.get("is_focusable")}
        for k, o in out_rows
        if (o.get("aria") in ("文本", "更多"))]
    c["n_rows"] = len(rows)
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}
out["reps_agree_out"] = (_c0.get("out_ids") == _c1.get("out_ids")
                         and _c0.get("out_ids_self") == _c1.get("out_ids_self"))
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))
out["design_gates"] = {
    # ① ⭐ out 段**真的走到了**（分母 = `n_out_presses`，钉关系不钉绝对值）
    "out_segment_walked_both_reps": bool(
        min(_c0.get("n_out_presses") or 0, _c1.get("n_out_presses") or 0) >= 10),
    # ② ⭐⭐⭐ **两个字段都在读数里**（否则同口径这件事无从谈起）
    "both_tid_fields_present_both_reps": bool(
        bool(_c0.get("out_ids")) and bool(_c0.get("out_ids_self"))
        and bool(_c1.get("out_ids")) and bool(_c1.get("out_ids_self"))),
    # ③ ⭐ 监听器**响了每按一次**
    "fired_eq_rows_both_reps": bool(
        _c0.get("fired_eq_rows") and _c1.get("fired_eq_rows")),
    # ④ 装/摘**配平**
    "listener_balanced_both_reps": bool(
        _c0.get("listener_balanced") and _c1.get("listener_balanced")),
    # ⑤ 两轮**逐项一致**
    "reps_agree": bool(out["reps_agree_out"]),
}
out["recon"] = {
    "rep%d" % i: {
        "n_lead": c.get("n_lead"),
        "inserted": c.get("inserted"),
        "n_out_presses": c.get("n_out_presses"),
        "out_ids_self": c.get("out_ids_self"),
        "out_ids_closest": c.get("out_ids"),
        "n_self_none": c.get("n_self_none"),
        "self_none_aria": c.get("self_none_aria"),
        "n_self_eq_closest": c.get("n_self_eq_closest"),
        "panel_rows": c.get("panel_rows"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}
out["gate_notes"] = (
    "⭐ 970 的门全部围绕「**同口径**」这一件事：`both_tid_fields_present` 要求"
    "**两个字段都进了读数**（少一个就是没同口径）；`out_segment_walked` 只钉"
    "「走到了 ≥10 个 out 停靠点」这个**关系**，**不钉绝对个数**"
    "（源站 17 / 复刻基数不同）")
out["what_970_measures"] = (
    "复刻 out 段每个停靠点的**两个** tid 字段：`self_tid`（**元素自己**的 "
    "`data-testid`）与 `closest_tid`（`closest('[data-testid]')`，**可能是祖先**）"
    "⇒ 与 969 的源站读数**同口径**，那张对照表**重做一遍**")
out["discipline_970"] = (
    "① ⭐⭐⭐ **同一个字段要对比，就得用同一个口径** —— 969 栽在这里"
    "（复刻记**自身**、源站那侧读到的是**祖先**）⇒ 本批两个字段都记；\n"
    "  · ② ⭐⭐ **两次同一种错**：968b 拿**历史基线**当本轮对照、"
    "969 拿**不同口径**当同一字段比 ⇒ 归成一条：**先核「比的是不是同一个东西」**；\n"
    "  · ③ ⭐ `OWN_JS` **只读属性、不调 `focus()`** ⇒ 不污染焦点读数；\n"
    "  · ④ ⭐ **零插入、零节点点击**（本批只量 out 段）；\n"
    "  · ⑤ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）")
out["same_ruler_note"] = (
    "⭐⭐ 970 与 969 的读数**同口径**：969 的 `FINGER_JS` 也同时记了 "
    "`tid`（自身）与 `host_tid`（祖先）⇒ **两张表可以直接对账**")
dump(out)
print("WROTE", OUT, flush=True)
