#!/usr/bin/env python3
r"""batch 971 源站探针（**纯读 / 零副作用**）：⭐⭐⭐⭐⭐ 954 记的那个
`out:测试项目…已保存…分享` —— **它到底是什么、它在线不在线**？

## 这一批的来由

954/959/961/966 一致记着：源站 out 段有 **18** 个停靠点，其中一个
`data-testid` 为 `None`、文本形如 `测试项目…已保存…分享`，历史上被我叫作「项目面板」。

但：

- **969 同轮重测**（2/2）⇒ out 段 **17** 个停靠点**全都带真 `data-testid`**、
  **`host_tid is None` 的 0 个** ⇒ **它本轮不在线**
- ⭐⭐⭐ 而 969 的 `FINGER_JS` 的 `aria` **只读 `getAttribute('aria-label')`、不回退**
  ⇒ **即使它在线，969 也不会用 innerText 认出它** ⇒ 969 只能证明
  「**没有 `tid=None` 的 out 停靠点**」，**不能**证明「没有任何 `tid=None` 的元素被落焦」

⇒ ⇒ ⭐⭐⭐ **问题必须重写成「三套口径并着问」**：

1. `aria_label` = `getAttribute('aria-label')`（**969 口径**）
2. `aria_whoami` = `aria-label || title || innerText.slice(0,30)`（**954 口径**）
3. `inner_text_head` = **原始** innerText 前 40 字 + `contains_saved` 布尔

⇒ 三套**同时**记，任何一枚停靠点都能**按三套口径各认一遍**
⇒ 与 954 的清单**同口径**（954 用的就是第 2 套）

## ⚠️ 为什么这一批**不上副作用**

判据：**纯读能答就不点**。
- 格 0（纯读）要答的是：**这一圈里到底有没有任何元素，其文本含「已保存」**，
  以及**有没有任何落点的 `closest_tid` 是 `None`**
- ⇒ **只有纯读答不了**（「确认在线、只是要触发保存态才出现」），
  **下一批才上改名那种有副作用的手段** ⇒ 不许在答案还不确定时就动状态

## 纪律（承 942–970）

1. ⭐⭐⭐ **同一个字段要对比，就得用同一个口径**（970 的教训 ⇒ 本批**三套并存**）
2. ⭐⭐⭐ **先核「我比的是不是同一个东西」**
3. ⭐ **每道门挂独立分母**；门要能红、也要能不红
4. ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）
5. ⚠️ **落盘排在所有后处理之前**
6. ⚠️ 诊断动作**必须还原**（装/摘成对）；**不 reload、不写 `prototype`**

## 计费边界

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点，⛔ 守卫拦在
`mouse.click` **之前**；其余**只发 `Tab`**、**不点任何东西**、**不改任何状态**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe971_savestate_src.py
"""

import json
import pathlib

OUT = "/tmp/b971-savestate.json"
REPS = 2
SETTLE = 350        # ms（照 952–970）
BLANK_WAIT = 900    # ms（照 952–970）
N_LEAD_CAP = 140     # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = ".react-flow__node"

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

P967 = pathlib.Path(__file__).with_name("jimeng_probe967_armptr_src.py")
P970 = pathlib.Path(__file__).with_name("jimeng_probe970_owntid_ck.py")
P954 = pathlib.Path(__file__).with_name("jimeng_probe954_source_ring_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "self_tid", "closest_tid", "tag", "aria", "title", "id",
    "tabindex", "tab_index_prop", "is_focusable", "rect", "kind",
    "fired", "armed", "n_minus1", "n_nodes_snap", "landed", "node_tid",
    "node_index", "host_tid", "trusted", "installed", "off_after_read",
    "blank", "aria_label", "aria_whoami", "inner_text_head",
    "contains_saved", "n_children",
    "saved_n", "saved_hits",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "target", "url", "reps", "rail_tid", "n_lead_cap", "node_sel",
    "question", "ruler", "baseline", "runs", "recon", "gate_notes",
    "design_gates", "what_971_measures", "discipline_971", "skip_note",
    "ci", "mode", "rows", "n_ready", "n_lead", "n_lead_cap_hit",
    "n_rail_stops", "n_install", "n_read", "off_null_at_end",
    "n_rows", "n_fired_total", "fired_eq_rows", "listener_balanced",
    "boot_saved_n", "boot_saved_sample",
    "out_ids_aria_label", "out_ids_aria_whoami",
    "n_landed_closest_none", "closest_none_detail",
    "n_landed_contains_saved", "contains_saved_detail",
    "n_out_presses", "matches_954_literal", "literal_note",
    "keys_disjoint", "reps_agree",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"


# ── ⭐ 四段仪器**逐字来自 967**（与 968/969/970 同一把尺子）──────────────
_p967src = P967.read_text(encoding="utf-8") if P967.exists() else ""
assert _p967src, "读不到 967 的源码 —— 尺子没得比，这道门恒绿"
_p970src = P970.read_text(encoding="utf-8") if P970.exists() else ""
assert _p970src, "读不到 970 的源码 —— `OWN_JS` 没得比，这道门恒绿"
_p954src = P954.read_text(encoding="utf-8") if P954.exists() else ""
assert _p954src, "读不到 954 的源码 —— `aria` 口径没得比，这道门恒绿"


def _grab(name, src=None):
    # ⚠️⚠️ 这里**不能**在 docstring 里写出三引号本身（会当场自噬）
    """从**文件内容**里把 `NAME = <三引号>…<三引号>` 那一段原样抠出来。"""
    text = _p967src if src is None else src
    marker = name + ' = """'
    i = text.index(marker) + len(marker)
    j = text.index('"""', i)
    return text[i:j]


INSTALL_JS = _grab("INSTALL_JS")
READ_JS = _grab("READ_JS")
OFF_NULL_JS = _grab("OFF_NULL_JS")
BLANK_JS = _grab("BLANK_JS")
OWN_JS = _grab("OWN_JS", _p970src)
del _grab
for _n, _s, _src in (("INSTALL_JS", INSTALL_JS, _p967src),
                      ("READ_JS", READ_JS, _p967src),
                      ("OFF_NULL_JS", OFF_NULL_JS, _p967src),
                      ("BLANK_JS", BLANK_JS, _p967src),
                      ("OWN_JS", OWN_JS, _p970src)):
    assert _s in _src, f"{_n} 抠出来**不等于**原样 ⇒ 尺子分家了"
del _n, _s, _src
assert INSTALL_JS.count("__ap_off = () => {") == 1, (
    "`INSTALL_JS` 里没有可摘的句柄 ⇒ 「装/摘配平」这道门恒绿")
assert (INSTALL_JS.count("addEventListener") == 3
        and INSTALL_JS.count("removeEventListener") == 3), (
    "装 3 个就必须摘 3 个（配平门自己数一遍）")

# ── 新件 ①：`TEXTHO_JS`（**纯读**：三套口径**并着**读）──────────────────
# ⭐⭐⭐ 本批的**整个来由**：`aria` **必须三套并存**，否则任何一套都答不了「954 那枚」
TEXTHO_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {aria_label: null, aria_whoami: null, inner_text_head: null,
                  contains_saved: null, kind: null, n_children: null};
  const node = a.closest(nodeSel);
  const txt = a.innerText || '';
  const al = a.getAttribute('aria-label');
  const ti = a.getAttribute('title');
  return {
    aria_label: al,
    aria_whoami: al || ti || (txt || '').slice(0, 30) || null,
    inner_text_head: (txt || '').slice(0, 40),
    contains_saved: txt.indexOf('已保存') >= 0 || txt.indexOf('保存中') >= 0,
    kind: !node ? 'out' : (a === node ? 'self' : 'inner'),
    n_children: a.childElementCount,
  };
}"""
assert TEXTHO_JS.count("slice(") == 2, (
    f"`TEXTHO_JS` 里有 {TEXTHO_JS.count('slice(')} 处切片，期望 2 处"
    "（`aria_whoami` 一处 + `inner_text_head` 一处）")
assert TEXTHO_JS.count("|| '').slice(0, ") == 2, (
    "`TEXTHO_JS` 里有**非字符串**切片（§131）")
# ⭐ 三套口径**每一套都要有自证门**，少一套这道门就恒红/恒绿
assert TEXTHO_JS.count("aria_label: al,") == 1, (
    "`TEXTHO_JS` 里没有「纯 aria-label」那一套口径 ⇒ 这道门恒绿")
assert TEXTHO_JS.count("aria_whoami: al || ti ||") == 1, (
    "`TEXTHO_JS` 里没有「954 口径」那一套 ⇒ 这道门恒绿")
assert TEXTHO_JS.count(
    "contains_saved: txt.indexOf('已保存') >= 0 || txt.indexOf('保存中') >= 0,") == 1, (
    "`TEXTHO_JS` 里没有 `contains_saved` 的**真读**那一行 ⇒ 这道门恒绿"
    "（⚠️ 第一版写成 `count('contains_saved:') == 1`、**被干跑判红** ⇒ "
    "因为它在 **null 桩**里也出现一次 ⇒ **门要钉真读、不要钉词频**）")

# ── 新件 ②：`SAVED_CENSUS_JS`（**纯读**：boot 后普查「已保存」在不在页面上）──
SAVED_CENSUS_JS = """([nodeSel]) => {
  const hits = [];
  const all = Array.from(document.querySelectorAll('*'));
  all.forEach((el) => {
    const t = el.innerText || '';
    if (t.indexOf('已保存') < 0 && t.indexOf('保存中') < 0) return;
    if (t.length > 120) return;
    const c = el.closest('[data-testid]');
    hits.push({tag: (el.tagName || '').toUpperCase(),
               self_tid: el.getAttribute('data-testid'),
               closest_tid: c ? c.getAttribute('data-testid') : null,
               ti: el.hasAttribute('tabindex')
                     ? el.getAttribute('tabindex') : null,
               tab_index_prop: el.tabIndex,
               n_children: el.childElementCount,
               text_head: (t || '').slice(0, 60)});
  });
  return {saved_n: hits.length, saved_hits: hits};
}"""
assert SAVED_CENSUS_JS.count("slice(") == SAVED_CENSUS_JS.count("|| '').slice(0, "), (
    "`SAVED_CENSUS_JS` 里有**非字符串**切片（§131）")
assert SAVED_CENSUS_JS.count("if (t.length > 120) return;") == 1, (
    "`SAVED_CENSUS_JS` 里**没有**「只看短文本」那道自证 ⇒ 这道门恒绿")


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


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {
    "target": "source", "url": URL, "reps": REPS, "rail_tid": RAIL_TID,
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐ 954 记的那个 `out:测试项目…已保存…分享`"
                "（`data-testid` 为 `None`）**到底在线不在线**？"
                "⇒ 本批把 `aria` 的**三套口径并着读**，"
                "并 boot 后普查「已保存」到底在不在页面上",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "how_proved": "⭐ `_grab(name, src)` 抠出那一段，再 `assert _s in _src`",
        "new_pieces": ["TEXTHO_JS", "SAVED_CENSUS_JS"],
        "why_read_not_instrument": "⭐ 两段都**只读属性/文本**、"
                                   "**从不调 `focus()`** ⇒ 不污染焦点读数",
        "three_calibers": "⭐⭐⭐ `aria` 的**三套口径并着记**："
                          "`aria_label`（969 口径）/ `aria_whoami`（954 口径）/ "
                          "`inner_text_head`（原始）"
                          "⇒ 任何一枚停靠点都能**按三套各认一遍**",
    },
    "baseline": {
        "s954_literal": "out:测试项目…已保存…分享",
        "s954_n_out_stops": 18,
        "s969_n_out_stops": 17,
        "s969_null_tid_rows": 0,
        "s969_caveat": "⚠️⚠️ **969 的 `FINGER_JS` 的 `aria` 只读 "
                       "`getAttribute('aria-label')`、不回退** ⇒ "
                       "**即使那枚在线，969 也不会用 innerText 认出它** ⇒ "
                       "969 只能证明「**没有 `tid=None` 的 out 停靠点**」，"
                       "**不能**证明「没有任何 `tid=None` 的元素被落焦」",
        "s816_decision": "⚠️ `verify-jimeng-batch816-anchors.py` 早就写过："
                         "**「「更多」源站没有 testid，复刻保留自造的 "
                         "`canvas-more-trigger`**」"
                         "⇒ 本批要找的那枚**不是**「更多」"
                         "（970 已证「更多」是 954 之外的一枚、且是**有意偏离**）",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    c = {"ci": 0, "mode": "walk", "n_ready": n, "rows": [],
         "n_install": 0, "n_read": 0, "n_rail_stops": 0,
         "n_lead_cap_hit": False}
    rec["cells"].append(c)
    dump(out)
    if n == 0:
        c["skip_note"] = "左栏入口没出来 ⇒ 本格什么也没测"
        continue

    # ── ⭐ 走查**之前**先普查「已保存」在不在页面上（**纯读**）──────────
    _sv = ev(SAVED_CENSUS_JS, [NODE_SEL])
    c["boot_saved_n"] = _sv.get("saved_n")
    c["boot_saved_sample"] = (_sv.get("saved_hits") or [])[:5]
    print(f"      boot 普查「已保存/保存中」：{c['boot_saved_n']} 处命中", flush=True)
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
            ap = ev(READ_JS)             # ⭐ 读走**并摘监听**（诊断动作必须还原）
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL])
            t = ev(TEXTHO_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o, "text": t}
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
    c["n_rows"] = len(rows)
    out_rows = []
    for r in rows:
        if r["text"].get("kind") == "out":
            out_rows.append((r["k"], r))
    c["n_out_presses"] = len(out_rows)
    # ⭐⭐ **两套口径各出一张清单**，并排摆出来
    # ⚠️⚠️⚠️ **干跑当场抓到的真 bug**：`sorted()` 比较**含 `None`** 的元组会
    #   `TypeError: '<' not supported between NoneType and str`
    #   ⇒ 969/970 **没踩到**是因为它们那一列**全都有值**；971 的「三套口径」
    #   **必然**产出 `aria_label=None` ⇒ 必须**给 key**、不能直接 `sorted()`
    def _srt(items):
        return sorted(items, key=lambda t: tuple("" if y is None else str(y)
                                                for y in t))

    c["out_ids_aria_label"] = _srt({(r["own"].get("tag"),
                                     r["text"].get("aria_label"),
                                     r["own"].get("closest_tid"))
                                    for _k, r in out_rows})
    c["out_ids_aria_whoami"] = _srt({(r["own"].get("tag"),
                                      r["text"].get("aria_whoami"),
                                      r["own"].get("closest_tid"))
                                     for _k, r in out_rows})
    # ── ⭐⭐⭐ 本批的正题：`closest_tid is None` 的落点（**不分 kind**）──
    none_rows = [(r["k"], r) for r in rows
                 if r["own"].get("closest_tid") is None]
    c["n_landed_closest_none"] = len(none_rows)
    c["closest_none_detail"] = [
        {"k": k, "tag": r["own"].get("tag"),
         "aria_label": r["text"].get("aria_label"),
         "aria_whoami": r["text"].get("aria_whoami"),
         "inner_text_head": r["text"].get("inner_text_head"),
         "contains_saved": r["text"].get("contains_saved"),
         "kind": r["text"].get("kind"),
         "is_focusable": r["own"].get("is_focusable")}
        for k, r in none_rows]
    # ── ⭐⭐ `contains_saved` 的落点（**不分 kind**）─────────────────
    saved_rows = [(r["k"], r) for r in rows
                  if r["text"].get("contains_saved")]
    c["n_landed_contains_saved"] = len(saved_rows)
    c["contains_saved_detail"] = [
        {"k": k, "tag": r["own"].get("tag"),
         "self_tid": r["own"].get("self_tid"),
         "closest_tid": r["own"].get("closest_tid"),
         "aria_whoami": r["text"].get("aria_whoami"),
         "inner_text_head": r["text"].get("inner_text_head"),
         "kind": r["text"].get("kind")}
        for k, r in saved_rows]
    # ── 与 954 的字面量对照（**关系式**：只看「有没有哪一枚的文本含那三段」）──
    c["matches_954_literal"] = [
        {"k": r["k"], "aria_whoami": r["text"].get("aria_whoami"),
         "inner_text_head": r["text"].get("inner_text_head")}
        for r in rows
        if r["text"].get("aria_whoami")
        and ("已保存" in str(r["text"].get("aria_whoami"))
             or "测试项目" in str(r["text"].get("aria_whoami")))]
    c["literal_note"] = (
        "954 记的字面量是 `out:测试项目…已保存…分享`，`…` 是**我的省略记法**、"
        "不是原文 ⇒ 本批**不去逐字匹配它**，只问「有没有哪一枚的 "
        "`aria_whoami` 含『已保存』或『测试项目』」")
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}
out["reps_agree"] = (
    _c0.get("out_ids_aria_whoami") == _c1.get("out_ids_aria_whoami")
    and _c0.get("n_landed_closest_none") == _c1.get("n_landed_closest_none")
    and _c0.get("n_landed_contains_saved") == _c1.get("n_landed_contains_saved")
    and _c0.get("boot_saved_n") == _c1.get("boot_saved_n"))
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))
out["design_gates"] = {
    # ① ⭐⭐⭐ **三套口径都进了读数**（少一套就是没做到本批的目的）
    "three_calibers_present_both_reps": bool(
        bool(_c0.get("out_ids_aria_label"))
        and bool(_c0.get("out_ids_aria_whoami"))
        and bool(_c1.get("out_ids_aria_label"))
        and bool(_c1.get("out_ids_aria_whoami"))),
    # ② ⭐⭐ out 段**真的走到了**（分母 = `n_out_presses`，钉关系不钉绝对值）
    "out_segment_walked_both_reps": bool(
        min(_c0.get("n_out_presses") or 0, _c1.get("n_out_presses") or 0) >= 10),
    # ③ ⭐⭐ **`closest_tid is None` 的读法真的会命中东西**
    #    （若恒 0 ⇒ 「没这一枚」与「判据写错了」分不开 ⇒ **如实记红**）
    "closest_none_read_is_live_both_reps": bool(
        min(_c0.get("n_landed_closest_none") or 0,
            _c1.get("n_landed_closest_none") or 0) > 0),
    # ④ 监听器**响了每按一次**
    "fired_eq_rows_both_reps": bool(
        _c0.get("fired_eq_rows") and _c1.get("fired_eq_rows")),
    # ⑤ 装/摘**配平**
    "listener_balanced_both_reps": bool(
        _c0.get("listener_balanced") and _c1.get("listener_balanced")),
    # ⑥ 两轮**逐项一致**
    "reps_agree": bool(out["reps_agree"]),
}
out["recon"] = {
    "rep%d" % i: {
        "n_lead": c.get("n_lead"),
        "boot_saved_n": c.get("boot_saved_n"),
        "boot_saved_sample": c.get("boot_saved_sample"),
        "n_out_presses": c.get("n_out_presses"),
        "out_ids_aria_whoami": c.get("out_ids_aria_whoami"),
        "n_landed_closest_none": c.get("n_landed_closest_none"),
        "closest_none_detail": c.get("closest_none_detail"),
        "n_landed_contains_saved": c.get("n_landed_contains_saved"),
        "contains_saved_detail": c.get("contains_saved_detail"),
        "matches_954_literal": c.get("matches_954_literal"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}
out["gate_notes"] = (
    "⭐ 971 的门围绕「**三套口径**」与「**判据会不会红**」："
    "`three_calibers_present` 要求三套里被用的两套都进了读数；"
    "`closest_none_read_is_live` 要求「`closest_tid is None` 的落点」"
    "**真的会命中东西** ⇒ 恒 0 时「没有这一枚」与「判据写错了」**分不开**，"
    "**必须记红**而不是安静地写「不存在」")
out["what_971_measures"] = (
    "① boot 后**纯读普查**：页面上有没有任何元素的文本含「已保存/保存中」"
    "（`SAVED_CENSUS_JS`，只看**短文本**、避免祖先整片命中）；"
    "② 走查里每个落点**三套口径并读**：`aria_label`（969 口径）/ "
    "`aria_whoami`（954 口径 `aria-label || title || innerText.slice(0,30)`）/ "
    "`inner_text_head`（原始 40 字）+ `contains_saved`；"
    "③ **`closest_tid is None` 的落点**（**不分 kind**）与 "
    "**`contains_saved` 的落点**（**不分 kind**）⇒ "
    "⇒ **只回答「在不在、是什么」，不做机制推断**")
out["discipline_971"] = (
    "① ⭐⭐⭐ **纯读能答就不点** —— 只有「确认在线、只是要触发保存态才出现」"
    "才允许下一批上改名那种**有副作用**的手段；\n"
    "  · ② ⭐⭐⭐ **同一个字段要对比，就得用同一个口径**（970 的教训 ⇒ "
    "本批 `aria` **三套并记**）；\n"
    "  · ③ ⭐ **判据恒 0 必须记红**（`closest_none_read_is_live`）；\n"
    "  · ④ ⭐⭐ **`…` 是我的省略记法、不是原文** ⇒ "
    "**不许去逐字匹配 954 的那个字面量**，只问「有没有哪一枚的文本含那几段」；\n"
    "  · ⑤ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）")
dump(out)
print("WROTE", OUT, flush=True)
