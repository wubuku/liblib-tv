#!/usr/bin/env python3
"""batch 969 源站探针：⭐⭐⭐⭐ out 段那个 **`tid=None`** 的停靠点（**项目面板**）
**到底是什么**？—— 复刻缺的就是它（968b 已把「18 vs 17」钉死），但**它长什么样还没读过**。

## 这一批的来由

954/959/961/966 一致记着：源站 out 段 **18 个**停靠点，里面有一个
**`data-testid` 为 `None`** 的，历史上被叫做「项目面板」。
复刻那边 968b 实测**真正的** out 停靠点是 **17 个**（第 17 个是 `NEXTJS-PORTAL`
那个 Next.js 开发态产物）⇒ **差的就是这一个**。

⇒ 但**至今没有任何一次读数描述过它**：
- 它是**什么标签**？`<button>`？`<div>`？
- 它**带 `aria-label` 吗**？带 `title` 吗？
- 它的**视觉盒**多大？在屏幕的哪个位置？
- 它**可聚焦吗**（`tabIndex >= 0`）？
- 它**有没有子节点**？里面是什么？

⇒ 不许猜。**这一批只读这些。**

## ⭐ 为什么必须「纯读 + 一次走查里读完」

- ⛔ **不点任何东西**（除每轮开头那次画布空白点击，守卫拦在 `mouse.click` 之前）
- ⛔ **不发 `Shift+Tab`**、不发 `Escape`、只发 `Tab`
- ⛔ **不 `reload`**、不写 `prototype`、不装 `MutationObserver`
- ⛔ **不劫持 `focus()`** ⇒ 逐字绕开 `press_row`（它内部的 `ARM_FOCUS_JS` 带
  `el.focus()`，957 源站查红、958 复刻查红）

## ⚠️ 纪律（承 942–968）

1. ⭐ **一个错的判据比没有判据更坏** ⇒ 「项目面板」**不是**按 aria 匹配的
   （那是我自己起的名字），**按 `data-testid is None` 匹配**
   ⇒ 再加一道**自证门**：这个判据**自己能不能匹配到东西**
2. ⭐ **每道门挂独立分母**
3. ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）
4. ⚠️ **落盘排在所有后处理之前**
5. ⭐ 两轮比较**按身份**、**在 `for rep` 之外**

## 计费边界

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点；其余**只发 `Tab`**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe969_projectpanel_src.py
"""

import json
import pathlib

OUT = "/tmp/b969-projectpanel.json"
REPS = 2
SETTLE = 350        # ms（照 952–967）
BLANK_WAIT = 900    # ms（照 952–967）
N_LEAD_CAP = 140     # ⭐ 硬上限，不是目标（照 967）
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = ".react-flow__node"

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

P967 = pathlib.Path(__file__).with_name("jimeng_probe967_armptr_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "tag", "tid", "host_tid", "aria", "title", "cls", "rect",
    "tabindex", "tab_index_prop", "is_focusable", "n_focusable_desc",
    "desc_tags", "child_count", "in_shadow", "root_kind", "id",
    "n_nodes_snap", "armed", "n_minus1", "fired", "landed", "kind",
    "node_tid", "node_index", "trusted", "installed", "off_after_read",
    "blank",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "target", "url", "reps", "rail_tid", "n_lead_cap", "node_sel",
    "question", "ruler", "baseline", "runs", "recon", "gate_notes",
    "aria_read_policy",
    "design_gates", "what_969_measures", "discipline_969", "skip_note",
    "ci", "mode", "rows", "n_ready", "n_lead", "n_lead_cap_hit",
    "n_rail_stops", "n_install", "n_read", "off_null_at_end",
    "n_out_stops", "out_ids", "n_null_tid_stops", "null_tid_rows",
    "null_tid_aria", "null_tid_tags", "null_tid_rects", "null_tid_focusable",
    "null_tid_desc_tags", "null_tid_n_focusable_desc", "null_tid_child_counts",
    "panel_sample", "n_fired_total", "fired_eq_rows", "listener_balanced",
    "reps_agree_panel", "keys_disjoint",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"


# ── ⭐ 四段仪器**逐字来自 967**（同一把尺子）─────────────────────────
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

# ── 新件：`FINGER_JS`（**纯读**：把焦点那一枚的**全指纹**读出来）────────
# ⭐⭐⭐⭐ 这是**本批唯一的新件**，而且它**只读属性**、**不调 `focus()`**
#   ⇒ 不污染「焦点在哪」的读数（承 957 `RAIL_JS` 的同一条理由）
FINGER_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {tag: null, tid: null, host_tid: null, aria: null,
                  title: null, cls: null, rect: null, tabindex: null,
                  tab_index_prop: null, is_focusable: null,
                  n_focusable_desc: null, desc_tags: null,
                  child_count: null, in_shadow: null, root_kind: null,
                  id: null};
  const r = a.getBoundingClientRect();
  const rt = a.getRootNode();
  const NATIVE = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
  const desc = [];
  let n_focusable_desc = 0;
  Array.from(a.querySelectorAll('*')).forEach((el) => {
    const t = (el.tagName || '').toUpperCase();
    desc.push(t);                                  // ⚠️ **不截断**
    if (NATIVE.indexOf(t) >= 0 || el.hasAttribute('tabindex')) n_focusable_desc += 1;
  });
  return {
    tag: (a.tagName || '').toUpperCase(),
    tid: a.getAttribute('data-testid'),
    host_tid: (a.closest('[data-testid]')
               ? a.closest('[data-testid]').getAttribute('data-testid') : null),
    aria: a.getAttribute('aria-label'),
    title: a.getAttribute('title'),
    cls: String((a.className && a.className.baseVal !== undefined)
                ? a.className.baseVal : (a.className || '')),
    id: a.id || null,
    rect: [Math.round(r.x), Math.round(r.y),
           Math.round(r.width), Math.round(r.height)],
    tabindex: a.hasAttribute('tabindex') ? a.getAttribute('tabindex') : null,
    tab_index_prop: a.tabIndex,
    is_focusable: a.tabIndex >= 0,
    n_focusable_desc: n_focusable_desc,
    desc_tags: desc,
    child_count: a.childElementCount,
    in_shadow: !!(rt && rt.host),
    root_kind: (rt && rt.host) ? 'ShadowRoot'
        : ((rt && rt.nodeName) ? rt.nodeName : null),
  };
}"""
assert FINGER_JS.count("slice(") == 0, "FINGER_JS 不该有切片（§131）"
assert FINGER_JS.count("a.closest('[data-testid]')") == 2, (
    "`FINGER_JS` 里 `host_tid` 的取法被改写了 ⇒ 这道门恒绿")
# ⭐ **判据自己能不能匹配到东西**（946 的教训：守卫常量必须自证）
assert FINGER_JS.count("host_tid: (a.closest('[data-testid]')") == 1, (
    "`host_tid` 的判据**不在**文件里 ⇒ 「按 tid=None 认项目面板」这道门恒绿")


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
    "question": "⭐⭐⭐⭐ 源站 out 段那个 **`data-testid` 为 `None`** 的停靠点"
                "（历史上被我叫作「项目面板」）**到底是什么**？——"
                "复刻缺的就是它（968b 已把「源站 18 vs 复刻 17」钉死）",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "how_proved": "⭐ `_grab(name)` 从 967 的**文件内容**里抠出那一段，"
                      "再 `assert _s in _p967src`",
        "new_pieces": ["FINGER_JS"],
        "why_finger_is_not_instrument": "⭐ `FINGER_JS` 只**读属性**、"
                                        "**从不调 `focus()`** ⇒ 不污染「焦点在哪」"
                                        "（承 957 `RAIL_JS` 的同一条理由）",
        "bypassed": "⚠️ **绕开 `press_row`**：它内部的 `ARM_FOCUS_JS` 带 "
                    "`el.focus()`（957 源站查红、958 复刻查红）",
        "identity": "⭐ 判据是「**`host_tid is None`**」——"
                    "**不是**按 aria 匹配（「项目面板」只是我自己起的名字）",
    },
    "baseline": {
        "source_out_stops_954": 18,
        "replica_real_out_stops_968b": 17,
        "missing_one_is": "源站 out 段那个 `data-testid` 为 `None` 的停靠点",
        "never_described": "⚠️⚠️ **至今没有任何一次读数描述过它** ⇒ "
                           "**不许猜**，本批只读它的指纹",
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
            f = ev(FINGER_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "finger": f}
        c["rows"].append(row)
        # ⭐ 圈 = 第 2 次命中左栏（照 967）
        if f.get("host_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    c["off_null_at_end"] = ev(OFF_NULL_JS)
    dump(out)

    # ── 后处理（全部在 `dump` 之后）──────────────────────────────
    rows = c["rows"]
    out_stops = [r for r in rows if not r["finger"].get("in_node_list")]
    # ⚠️ `FINGER_JS` 不算 `in_node_list`；改用「落点 kind == out」来分
    out_stops = []
    for r in rows:
        for L in (r.get("landed") or []):
            if L.get("kind") == "out":
                out_stops.append((r["k"], r["finger"]))
                break
    c["n_out_stops"] = len(out_stops)
    c["out_ids"] = sorted({(f.get("tag"), f.get("aria"), f.get("host_tid"))
                           for _k, f in out_stops})
    null_rows = [(k, f) for k, f in out_stops if f.get("host_tid") is None]
    c["null_tid_rows"] = len(null_rows)
    c["null_tid_aria"] = [f.get("aria") for _k, f in null_rows]
    c["null_tid_tags"] = [f.get("tag") for _k, f in null_rows]
    c["null_tid_rects"] = [f.get("rect") for _k, f in null_rows]
    c["null_tid_focusable"] = [f.get("is_focusable") for _k, f in null_rows]
    c["null_tid_desc_tags"] = [f.get("desc_tags") for _k, f in null_rows]
    c["null_tid_n_focusable_desc"] = [f.get("n_focusable_desc")
                                      for _k, f in null_rows]
    c["null_tid_child_counts"] = [f.get("child_count") for _k, f in null_rows]
    c["panel_sample"] = null_rows[0][1] if null_rows else None
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}
out["reps_agree_panel"] = (
    _c0.get("null_tid_tags") == _c1.get("null_tid_tags")
    and _c0.get("null_tid_rects") == _c1.get("null_tid_rects")
    and _c0.get("null_tid_focusable") == _c1.get("null_tid_focusable"))
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))
out["design_gates"] = {
    # ① ⭐⭐⭐ **判据自证**：按 `host_tid is None` 真的认出了东西
    #    （若恒 0 ⇒ 要么判据写错了、要么这一轮没走全 ⇒ **如实记红**）
    "panel_judgement_is_live_both_reps": bool(
        (_c0.get("null_tid_rows") or 0) > 0
        and (_c1.get("null_tid_rows") or 0) > 0),
    # ② ⭐ out 段**走到了 18 个左右**（分母 = `n_out_stops`，钉关系不钉绝对值）
    "out_segment_walked_both_reps": bool(
        min(_c0.get("n_out_stops") or 0, _c1.get("n_out_stops") or 0) >= 10),
    # ③ 监听器**响了每按一次**
    "fired_eq_rows_both_reps": bool(
        _c0.get("fired_eq_rows") and _c1.get("fired_eq_rows")),
    # ④ 装/摘**配平**
    "listener_balanced_both_reps": bool(
        _c0.get("listener_balanced") and _c1.get("listener_balanced")),
    # ⑤ 两轮**逐项一致**
    "reps_agree": bool(out["reps_agree_panel"]),
}
out["recon"] = {
    "rep%d" % i: {
        "n_lead": c.get("n_lead"),
        "n_out_stops": c.get("n_out_stops"),
        "out_ids": c.get("out_ids"),
        "null_tid_rows": c.get("null_tid_rows"),
        "panel_sample": c.get("panel_sample"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}
out["gate_notes"] = (
    "⭐ 969 的判据**按身份**（`host_tid is None`）、**不按 aria** —— "
    "「项目面板」只是我自己起的名字，用它匹配就等于把结论写进判据。"
    "`panel_judgement_is_live` 要求**两轮都真的认出东西**，恒 0 就红")
out["what_969_measures"] = (
    "out 段那个 `data-testid` 为 **`None`** 的停靠点的**全指纹**："
    "`tag` / `host_tid` / `aria` / `title` / `className` / `id` / "
    "`rect` / `tabindex` / `el.tabIndex` / `is_focusable` / "
    "内部**可聚焦后代数** / 后代标签清单 / 子节点数 / root 归属 ⇒ "
    "**只读指纹、不做机制推断**\n"
    "  · ⭐⭐ **`aria` 只读 `getAttribute('aria-label')`、**不做任何回退** "
    "—— 这是**判据的一部分**：954 记的 `out:测试项目…已保存…分享` 其文本来自 "
    "`WHOAMI_JS` 的 **innerText 回退**，而 969 **故意不回退** ⇒ "
    "两者不可直接比，这一点在写判词时必须说清楚")
out["aria_read_policy"] = (
    "⭐⭐ `FINGER_JS` 的 `aria` = `a.getAttribute('aria-label')`，"
    "**没有 `||` 兜底、没有 innerText 回退** ⇒ 与 954 的 `WHOAMI_JS` "
    "（`aria-label || title || innerText.slice(0,30)`）**口径不同**")
out["discipline_969"] = (
    "① ⭐ **判据不许用自己起的名字**：「项目面板」是**我的叫法**，"
    "拿它匹配就等于把结论写进判据 ⇒ 判据是「`host_tid is None`」；\n"
    "  · ② ⭐ **不许猜**：至今没有任何一次读数描述过它 ⇒ 本批**只读指纹**；\n"
    "  · ③ ⭐ `FINGER_JS` **只读属性、不调 `focus()`** ⇒ 不污染「焦点在哪」；\n"
    "  · ④ ⚠️ **绕开 `press_row`**（它内部的 `ARM_FOCUS_JS` 带 `el.focus()`）；\n"
    "  · ⑤ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）")
dump(out)
print("WROTE", OUT, flush=True)
