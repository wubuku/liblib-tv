#!/usr/bin/env python3
"""batch 968 **复刻侧**探针（**纯诊断 / 零节点点击**）：⭐⭐⭐⭐ 用 **967 同一把尺子**
在**复刻**上验两条新钉的机制事实，并核对复刻节点落点的**步长分布**。

## 本批只答两件事（都必须在**复刻侧**各验一遍，不能只凭源站推）

967 在**源站**（2/2 轮逐项一致）新钉了三条：

| 事实 | 源站读数 |
| --- | --- |
| **布防 ⇒ 落焦** | 落焦落在「本体」的 **104 按全部**等于当按布上 `'0'` 的那一枚、**零例外** |
| **`'0'` 不撤** | 按后 **350ms** 仍布着（**140/140**）——正是 ⑦「此后不回撤」 |
| **步长** | 963 记的「恰好少一枚」；**步长分布**从未在**复刻侧**核过 |

⇒ 本批：**同一套仪器**（`INSTALL_JS`/`READ_JS`/`ARMED_ONLY_JS`/`OFF_NULL_JS`
**逐字来自 967**）在复刻上跑一遍，外加**步长分布**。

## ⭐ 为什么必须用「同一把尺子」

复刻与源站是两套实现 ⇒ **两侧的数字不可直接比**，除非**尺子逐字相同**。
⇒ 本批把 967 的四段仪器**逐字搬过来**并 `assert _js in _p967src` 证明
⇒ **两侧的「布防 ⇒ 落焦」「`'0'` 不撤」是同一把尺子下的两个数**。

## ⚠️ 复刻侧的三个特有坑（承 953–958）

1. ⚠️⚠️ **节点 `data-testid` 带时间戳** ⇒ 逐字比较**天然红**（953 红过）
   ⇒ 本批**一律按 DOM 序下标**对账，**不按 tid**
2. ⚠️ **每格重新 `boot()`**（956 起的标准前置）
3. ⚠️ `press_row` 内部的 `ARM_FOCUS_JS` 带 `el.focus()` 会**把焦点拽走**
   ⇒ 本批**自己发键** + 逐字读，**绕开 `press_row`**（958 查红过）

## ⭐ 步长分布怎么算（**先算「绕圈」再算别的**）

走查会**绕一圈**，所以相邻落点的差**必然出现一次回折**（从尾部回到头部）
⇒ ⭐ **「非单调」根本推不出「乱序」**（962 栽过：下降**恰好 1 次**、方向
`high_to_low` ⇒ 那就是折返）
⇒ 本批把差值分成四类，**并把回折单独记成一类**：
`+1` / `+2` / `>+2` / `wrap`（`<= 0`）
⇒ 门挂在**独立分母**上：`n_step_gt2 == 0` 的分母是 `n_steps`（**不是** `n_lead`）

## 纪律（承 942–967）

1. ⭐ **一个错的判据比没有判据更坏** ⇒ 步长判据先问「**能不能区分**」
2. ⭐ **每道门挂独立分母**
3. ⭐ **恒真/恒假门比没有门更坏** ⇒ 每道门配一个「**它会不会红**」的自证
4. ⭐ **干跑**：改完必须 `py_compile` + JS 语法门 + **一次干跑**
5. ⚠️ **落盘排在所有后处理之前**
6. ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）

## 计费边界

**复刻是本地应用，本批零计费。** 插节点走**左栏入口**（不是节点本体）；
只点**画布空白**去焦点，⛔ 守卫拦在 `mouse.click` **之前**。按键只有 `Tab`。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe968_replica_armptr_ck.py
"""

import atexit
import json
import pathlib
import time

OUT = "/tmp/b968-replica-armptr.json"
REPS = 2
SETTLE = 350        # ms（照 952–967）
BLANK_WAIT = 900    # ms（照 952–967）
KINDS = ["文本", "图片", "时间线", "主体", "导演台"]   # 照 901/953/958
N_LEAD_CAP = 140     # ⭐ 硬上限，不是目标（照 967）
RAIL_TID = "canvas-fixed-toolbar"      # ⭐ 两边共用的锚点（复刻侧逐字相同）
NODE_SEL = ".react-flow__node"

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

P967 = pathlib.Path(__file__).with_name("jimeng_probe967_armptr_src.py")
P966 = pathlib.Path(__file__).with_name("jimeng_probe966_clicksel_src.py")
P958 = pathlib.Path(__file__).with_name("jimeng_probe958_rail_roving_ck.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    "n_nodes", "n_with_ti", "n_without_ti", "ti", "ids", "cls",
    "active_tag", "active_tid", "focus_in_node",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who", "tag", "tid", "blank",
    "dom_index", "id", "tabindex",
    "fired", "armed", "n_minus1", "n_nodes_snap",
    "landed", "host_tid", "node_tid", "kind", "trusted",
    "installed", "off_after_read",
    "has_flow", "n_ready_nodes", "flow_aria", "flow_ti", "kinds_found",
    "all_kinds", "node_ti_hist", "inserted",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "target", "url", "reps", "rail_tid", "n_lead_cap", "node_sel", "kinds",
    "question", "ruler", "baseline", "runs", "recon", "gate_notes",
    "design_gates", "what_968_measures", "discipline_968", "skip_note",
    "ci", "mode", "rows", "n_ready", "n_lead", "n_lead_cap_hit",
    "n_rail_stops", "n_install", "n_read",
    "n_nodes_census", "nodes_dom_order", "n_nodes_hist",
    "n_nodes_hist_distinct", "census_stable_in_rep",
    "armed_point_hist", "n_armed_presses", "armed_distinct_tids",
    "ever_armed", "n_landed_self", "n_landed_inner", "n_landed_out",
    "ever_landed_self", "ever_landed_inner", "landed_all",
    "never_armed", "never_landed", "n_never_armed", "n_never_landed",
    "landed_never_armed", "n_landed_never_armed",
    "self_eq_armed", "n_self_rows", "armed_persists_after",
    "n_armed_after_rows", "n_rows", "n_fired_total", "n_post_rows",
    "fired_eq_rows", "listener_balanced", "off_null_at_end",
    "step_pairs", "step_hist", "n_step_plus1", "n_step_plus2",
    "n_step_gt2", "n_step_wrap", "n_step_unknown",
    "landed_seq", "gt2_detail", "armed_persists_after",
    "keys_disjoint", "reps_agree_steps", "reps_agree_self_eq_armed",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"


# ── ⭐⭐ 四段仪器：**逐字来自 967**（复刻与源站**同一把尺子**）──────────
_p967src = P967.read_text(encoding="utf-8") if P967.exists() else ""
assert _p967src, "读不到 967 的源码 —— 尺子没得比，这道门恒绿"
_p966src = P966.read_text(encoding="utf-8") if P966.exists() else ""
assert _p966src, "读不到 966 的源码 —— 尺子没得比，这道门恒绿"


def _grab(name):
    # ⚠️⚠️ 这里**不能**在 docstring 里写出三引号本身（会当场自噬）
    """从 967 的**文件内容**里把 `NAME = <三引号>…<三引号>` 那一段原样抠出来。"""
    marker = name + ' = """'
    i = _p967src.index(marker) + len(marker)
    j = _p967src.index('"""', i)
    return _p967src[i:j]


INSTALL_JS = _grab("INSTALL_JS")
READ_JS = _grab("READ_JS")
ARMED_ONLY_JS = _grab("ARMED_ONLY_JS")
OFF_NULL_JS = _grab("OFF_NULL_JS")
NODECENSUS_JS = _grab("NODECENSUS_JS")
BLANK_JS = _grab("BLANK_JS")
FOCUS_JS = _grab("FOCUS_JS")
WHOAMI_JS = _grab("WHOAMI_JS")
del _grab

# ⭐ 抠出来之后**必须逐字等于**原样（`read_text` 的 index 抠取本身也可能出错）
for _n, _s in (("INSTALL_JS", INSTALL_JS), ("READ_JS", READ_JS),
               ("ARMED_ONLY_JS", ARMED_ONLY_JS), ("OFF_NULL_JS", OFF_NULL_JS),
               ("NODECENSUS_JS", NODECENSUS_JS), ("BLANK_JS", BLANK_JS),
               ("FOCUS_JS", FOCUS_JS), ("WHOAMI_JS", WHOAMI_JS)):
    assert _s in _p967src, f"{_n} 抠出来**不等于** 967 里的那份 ⇒ 尺子分家了"
    assert _s.count("slice(") == 0 or _s.count(
        "|| '').slice(0, ") == _s.count("slice("), (
        f"{_n} 里有**非字符串**切片（§131）")
del _n, _s
# ⭐ 仪器必须**自己就匹配得上它要验的东西**，否则下面几道门恒绿
assert INSTALL_JS.count("__ap_off = () => {") == 1, (
    "`INSTALL_JS` 里没有可摘的句柄 ⇒ 「装/摘配平」这道门恒绿")
assert (INSTALL_JS.count("addEventListener") == 3
        and INSTALL_JS.count("removeEventListener") == 3), (
    "装 3 个就必须摘 3 个（配平门自己数一遍）")
assert INSTALL_JS.count("kind: idx < 0 ? 'out' : (t === node ? 'self' : 'inner')") == 1, (
    "`INSTALL_JS` 里 `self`/`inner` 的判据被改写了 ⇒ 这道门恒绿")

# ── 新件：`READY_JS`（**纯读**）与 `insert_kinds()`（走**左栏入口**）────
READY_JS = """([nodeSel, kinds]) => {
  const flow = document.querySelector('.react-flow');
  const nodes = document.querySelectorAll(nodeSel);
  const found = kinds.map(k =>
    !!document.querySelector('button[aria-label="' + k + '"]'));
  return {has_flow: !!flow,
          n_ready_nodes: nodes.length,
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
    """⛔ 守卫：点之前**纯读**那个坐标上是什么（照 966 的 `guard_point`）。"""
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
    """新件：复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**。"""
    page.goto(_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev(READY_JS, [NODE_SEL, KINDS])


def insert_kinds():
    """固定前置：照 901/953/958 插 5 个节点。**左栏入口**、不是节点本体 ⇒
    不破「零节点点击」。返回**真的插进去几个**。"""
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


POINTS = ("pre", "post", "task", "after")

out = {
    "target": "replica", "url": _URL, "reps": REPS, "rail_tid": RAIL_TID,
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL, "kinds": KINDS,
    "question": "⭐⭐⭐⭐ 967 在源站新钉了三条机制事实（**布防 ⇒ 落焦** / "
                "**`'0'` 不撤** / 步长）；本批用**同一把尺子**在**复刻**上"
                "各验一遍，并核对复刻节点落点的**步长分布**",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "ARMED_ONLY_JS",
                                 "OFF_NULL_JS", "NODECENSUS_JS", "BLANK_JS",
                                 "FOCUS_JS", "WHOAMI_JS"],
        "how_proved": "⭐ 用 `_grab(name)` 从 967 的**文件内容**里抠出那一段，"
                      "再 `assert _s in _p967src` ⇒ **复刻与源站同一把尺子**，"
                      "两侧的数字**才可比**",
        "py_verbatim_from_967": ["ev", "dump", "guard"],
        "new_pieces": ["READY_JS", "boot_ck", "insert_kinds"],
        "bypassed": "⚠️ `press_row` **不用**：它内部的 `ARM_FOCUS_JS` 带 "
                    "`el.focus()`、会把焦点从 chrome 停靠点**拽回画布节点**"
                    "（957 源站查红、958 复刻查红）⇒ 自己发键 + 逐字读",
        "identity": "⚠️⚠️ 复刻节点 `data-testid` **带时间戳**（953 红过）⇒ "
                    "本批**一律按 DOM 序下标**对账，**不按 tid**",
    },
    "baseline_source_967": {
        "n_never_armed": 2,
        "n_never_landed": 1,
        "landed_never_armed": 1,
        "n_armed_never_landed": 0,
        "self_rows_all_equal_armed": "104/104（2/2）",
        "armed_persists_after": "140/140（2/2）",
        "note": "⚠️ 这些是**源站**的数 ⇒ **复刻的数字不要求与它们相等**"
                "（复刻没有那一枚被跳过、节点数也不同）⇒ "
                "本批只验**机制规则**是否成立，**关系式**判据不是**绝对值**判据",
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
         "flow_aria": rd.get("flow_aria"), "flow_ti": rd.get("flow_ti"),
         "all_kinds": rd.get("all_kinds"), "kinds_found": rd.get("kinds_found"),
         "node_ti_hist": rd.get("node_ti_hist")}
    rec["cells"].append(c)
    dump(out)
    if not rd.get("has_flow"):
        c["skip_note"] = "画布根没出来 ⇒ 本格什么也没测"
        continue

    c["inserted"] = insert_kinds()
    page.wait_for_timeout(1200)
    dump(out)

    _nc = ev(NODECENSUS_JS, [NODE_SEL])
    c["n_nodes_census"] = _nc.get("n_nodes")
    c["nodes_dom_order"] = [{"dom_index": n.get("dom_index"),
                             "tid": n.get("tid"), "aria": n.get("aria"),
                             "ti": n.get("ti")}
                            for n in (_nc.get("nodes") or [])]
    print(f"      复刻节点普查：{c['n_nodes_census']} 个（DOM 序）｜"
          f"插入了 {c['inserted']}", flush=True)

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
            _after = ev(ARMED_ONLY_JS, [NODE_SEL])
            d = ev(WHOAMI_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "pre": (ap or {}).get("pre"),
               "post": (ap or {}).get("post"),
               "task": (ap or {}).get("task"),
               "after": {"n_nodes_snap": _after.get("n_nodes_snap"),
                         "armed": _after.get("armed")},
               "landed": (ap or {}).get("landed"),
               "active_after": ev(FOCUS_JS, [NODE_SEL]),
               "who_after": d}
        c["rows"].append(row)
        if d.get("tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    c["off_null_at_end"] = ev(OFF_NULL_JS)
    dump(out)

    # ── 后处理（全部在 `dump` 之后）────────────────────────────────
    rows = c["rows"]
    census = c["nodes_dom_order"]
    c["n_nodes_hist"] = sorted({
        (r["pre"][0]["n_nodes_snap"] if (r.get("pre") or []) else None)
        for r in rows} - {None})
    c["n_nodes_hist_distinct"] = len(c["n_nodes_hist"])
    c["census_stable_in_rep"] = (c["n_nodes_hist_distinct"] == 1
                                 and c["n_nodes_hist"]
                                 and c["n_nodes_hist"][0] == c["n_nodes_census"])
    # ── 布防指针 ────────────────────────────────────────────────────
    armed_point_hist, ever_armed = {}, set()
    n_armed_presses = 0
    for r in rows:
        _seen = None
        for pt in POINTS:
            v = r.get(pt)
            armed_here = (v[0]["armed"] if isinstance(v, list) and v
                          else (v.get("armed") if isinstance(v, dict) else None))
            if armed_here:
                _seen = pt
                for a in armed_here:
                    ever_armed.add(a.get("index"))
                break
        if _seen:
            n_armed_presses += 1
            armed_point_hist[_seen] = armed_point_hist.get(_seen, 0) + 1
    c["armed_point_hist"] = armed_point_hist
    c["n_armed_presses"] = n_armed_presses
    c["armed_distinct_tids"] = len(ever_armed)
    c["ever_armed"] = sorted(ever_armed)
    # ── ⭐⭐ 落焦「本体」的那几按：**是否等于当按布上的那一枚** ─────────
    self_rows = eq = 0
    ls, li, lo = set(), set(), set()
    for r in rows:
        post_a = (r["post"][0]["armed"] if (r.get("post") or []) else []) or []
        post_idx = [a["index"] for a in post_a]
        after_a = (r.get("after") or {}).get("armed") or []
        for L in (r.get("landed") or []):
            if L.get("kind") == "self":
                ls.add(L.get("node_index"))
                self_rows += 1
                if L.get("node_index") in post_idx:
                    eq += 1
            elif L.get("kind") == "inner":
                li.add(L.get("node_index"))
            else:
                lo.add(L.get("host_tid"))
        if after_a:
            c["armed_persists_after"] = c.get("armed_persists_after", 0) + 1
    c["self_eq_armed"] = eq
    c["n_self_rows"] = self_rows
    c["n_armed_after_rows"] = c.get("armed_persists_after", 0)
    c["ever_landed_self"] = sorted(x for x in ls if x is not None)
    c["ever_landed_inner"] = sorted(x for x in li if x is not None)
    c["landed_all"] = sorted(x for x in (ls | li) if x is not None)
    c["n_landed_self"] = len(c["ever_landed_self"])
    c["n_landed_inner"] = len(c["ever_landed_inner"])
    c["n_landed_out"] = len([x for x in lo if x])
    ct = set(range(c["n_nodes_census"] or 0))
    c["never_armed"] = sorted(ct - set(c["ever_armed"]))
    c["never_landed"] = sorted(ct - set(c["landed_all"]))
    c["n_never_armed"] = len(c["never_armed"])
    c["n_never_landed"] = len(c["never_landed"])
    c["landed_never_armed"] = sorted(set(c["landed_all"]) - set(c["ever_armed"]))
    c["n_landed_never_armed"] = len(c["landed_never_armed"])
    # ── ⭐⭐⭐ 步长分布（**回折单独记成一类**，见文件头）────────────────
    seq = []
    for r in rows:
        _ls = [L for L in (r.get("landed") or []) if L.get("kind") == "self"]
        # ⭐ 每一按**只取第一个**「落焦本体」的落点（不去重、不合并）
        if _ls:
            seq.append((r["k"], _ls[0].get("node_index")))
    c["landed_seq"] = seq
    step_hist = {}
    for (k0, i0), (k1, i1) in zip(seq, seq[1:]):
        d = (i1 - i0) if (i0 is not None and i1 is not None) else None
        if d is None:
            cat = "unknown"
        elif d == 1:
            cat = "+1"
        elif d == 2:
            cat = "+2"
        elif d > 2:
            cat = "gt2"
        else:
            cat = "wrap"
        step_hist[cat] = step_hist.get(cat, 0) + 1
    c["step_pairs"] = max(len(seq) - 1, 0)
    c["step_hist"] = step_hist
    for cat in ("+1", "+2", "gt2", "wrap", "unknown"):
        c["n_step_" + ("plus1" if cat == "+1" else
                       "plus2" if cat == "+2" else cat)] = step_hist.get(cat, 0)
    c["gt2_detail"] = [
        {"from_k": k0, "from_i": i0, "to_k": k1, "to_i": i1, "step": i1 - i0}
        for (k0, i0), (k1, i1) in zip(seq, seq[1:])
        if i0 is not None and i1 is not None and (i1 - i0) > 2]
    # ── 门：每道都挂在**独立分母**上 ──────────────────────────────────
    c["n_rows"] = len(rows)
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["n_post_rows"] = sum(len(r.get("post") or []) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}
out["reps_agree_steps"] = (_c0.get("step_hist") == _c1.get("step_hist"))
out["reps_agree_self_eq_armed"] = (
    _c0.get("self_eq_armed") == _c1.get("self_eq_armed")
    and _c0.get("n_self_rows") == _c1.get("n_self_rows"))
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))
# ── ⭐ 设计门：每道都挂在**独立分母**上，且**不许恒真/恒假**（942 的教训）──
out["design_gates"] = {
    # ① 普查期间节点数**不能变**，否则下标不可比（分母 = 取值个数）
    "census_stable_both_reps": bool(
        _c0.get("census_stable_in_rep") and _c1.get("census_stable_in_rep")),
    # ② 监听器**真的响了每按一次**（分母 = `fired` 与 `rows` 的条数）
    "fired_eq_rows_both_reps": bool(
        _c0.get("fired_eq_rows") and _c1.get("fired_eq_rows")),
    # ③ 装/摘**配平**（分母 = `n_install`/`n_read` + `off_null_at_end`）
    "listener_balanced_both_reps": bool(
        _c0.get("listener_balanced") and _c1.get("listener_balanced")),
    # ④ ⭐ **布防那一路读数会动**：既有非空的按、又有多个不同的下标
    #    （若 `n_armed_presses` 恒 0 ⇒ 仪器没抓到；若 `armed_distinct_tids`
    #    恒 1 ⇒ 它读到的可能是常量）
    "armed_read_is_live": bool(
        min(_c0.get("n_armed_presses") or 0, _c1.get("n_armed_presses") or 0) > 0
        and min(_c0.get("armed_distinct_tids") or 0,
                _c1.get("armed_distinct_tids") or 0) >= 5),
    # ⑤ ⭐⭐ **机制规则「布防 ⇒ 落焦」在复刻上成立**（分母 = 落焦本体的按数）
    "self_equals_armed_both_reps": bool(
        min(_c0.get("n_self_rows") or 0, _c1.get("n_self_rows") or 0) > 0
        and _c0.get("self_eq_armed") == _c0.get("n_self_rows")
        and _c1.get("self_eq_armed") == _c1.get("n_self_rows")),
    # ⑥ ⭐⭐ **机制规则「`'0'` 不撤」在复刻上成立**（分母 = 按数）
    "armed_persists_both_reps": bool(
        min(_c0.get("n_armed_after_rows") or 0,
            _c1.get("n_armed_after_rows") or 0) > 0
        and _c0.get("n_armed_after_rows") == _c0.get("n_armed_presses")
        and _c1.get("n_armed_after_rows") == _c1.get("n_armed_presses")),
    # ⑦ ⭐⭐⭐ **步长**：分母是 `step_pairs`（**不是** `n_lead`）
    #    ⚠️⚠️ **第一版这道门太弱**：它只查 `n_step_gt2 == 0` ⇒ 在「全部是 `wrap`、
    #    `+1` 一次都没有」的**退化数据**上也**照样绿**（干跑当场证到）
    #    ⇒ 按 942 的纪律**改严**：除了 `gt2 == 0`，还要求
    #    **`+1` 真的出现过**、且**回折真的出现过**（走查绕圈 ⇒ 必须有）
    "steps_are_dom_order_both_reps": bool(
        min(_c0.get("step_pairs") or 0, _c1.get("step_pairs") or 0) > 0
        and _c0.get("n_step_gt2") == 0 and _c1.get("n_step_gt2") == 0
        and min(_c0.get("n_step_plus1") or 0, _c1.get("n_step_plus1") or 0) > 0
        and min(_c0.get("n_step_wrap") or 0, _c1.get("n_step_wrap") or 0) >= 1),
    # ⑧ ⚠️ **回折必须被单独记成一类**（962 教训：「非单调」推不出「乱序」）
    "wrap_is_its_own_class": bool(
        "wrap" in (_c0.get("step_hist") or {}) and "wrap" in (_c1.get("step_hist") or {})),
    # ⑨ 两轮**逐项一致**
    "reps_agree": bool(out["reps_agree_steps"]
                        and out["reps_agree_self_eq_armed"]),
}
# ⭐ **只搬数字、不写判词**（判词必须在读过原始读数之后才写，965 的教训）
out["recon"] = {
    "rep%d" % i: {
        "n_lead": c.get("n_lead"),
        "n_nodes_census": c.get("n_nodes_census"),
        "inserted": c.get("inserted"),
        "node_ti_hist_at_boot": c.get("node_ti_hist"),
        "armed_point_hist": c.get("armed_point_hist"),
        "n_armed_presses": c.get("n_armed_presses"),
        "armed_distinct_tids": c.get("armed_distinct_tids"),
        "self_eq_armed": c.get("self_eq_armed"),
        "n_self_rows": c.get("n_self_rows"),
        "n_armed_after_rows": c.get("n_armed_after_rows"),
        "n_landed_self": c.get("n_landed_self"),
        "n_landed_inner": c.get("n_landed_inner"),
        "n_landed_out": c.get("n_landed_out"),
        "n_never_armed": c.get("n_never_armed"),
        "never_armed": c.get("never_armed"),
        "n_never_landed": c.get("n_never_landed"),
        "n_landed_never_armed": c.get("n_landed_never_armed"),
        "landed_never_armed": c.get("landed_never_armed"),
        "step_pairs": c.get("step_pairs"),
        "step_hist": c.get("step_hist"),
        "gt2_detail": c.get("gt2_detail"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}
out["gate_notes"] = (
    "⭐ 968 的每道门都挂在**独立分母**上："
    "`steps_all_plus1` 的分母是 **`step_pairs`**（**不是** `n_lead` —— "
    "`n_lead` 里混着 chrome 停靠点）；`self_equals_armed` 的分母是 "
    "**`n_self_rows`**（不是全部按数）；`armed_persists` 的分母是 "
    "**`n_armed_presses`**\n"
    "⚠️⚠️ **步长那道门第一版太弱**（只查 `gt2 == 0` ⇒ 在「全是 `wrap`、"
    "`+1` 一次都没有」的退化数据上也绿）⇒ 干跑抓到后**按 942 的纪律改严**："
    "再加「`+1` 真的出现过」**且**「回折真的出现过」")
out["what_968_measures"] = (
    "**复刻侧**用**与源站逐字相同**的仪器（`assert _s in _p967src`）验三条："
    "① **布防 ⇒ 落焦**（落焦本体的按里，落点下标 == 当按 `post` 布上的下标）；"
    "② **`'0'` 不撤**（`after` 取样点仍读到布防集合）；"
    "③ **步长分布**（`+1`/`+2`/`gt2`/`wrap` 四类，**回折单独一类**）"
    "⇒ ⚠️ **判据是关系式的、不是绝对值**（复刻的节点数与源站不同、"
    "也没有那一枚被跳过 ⇒ 数字本就不该相等）")
out["discipline_968"] = (
    "① ⭐ **同一把尺子**：四段仪器**逐字**来自 967（`_grab` + `assert`）"
    "⇒ 两侧数字**才可比**；\n"
    "② ⭐⭐ **先算「绕圈」再算别的**：走查**必然**回折一次 ⇒ "
    "**「非单调」推不出「乱序」**（962 栽过）⇒ 回折**单独记成一类**；\n"
    "③ ⭐ **分母要对**：步长门的分母是 `step_pairs`、不是 `n_lead`；\n"
    "④ ⚠️ **复刻 tid 带时间戳**（953 红过）⇒ 一律**按 DOM 序下标**对账；\n"
    "⑤ ⭐ **绕开 `press_row`**（它内部的 `ARM_FOCUS_JS` 带 `el.focus()`）"
    "⇒ 自己发键 + 逐字读（957/958 各查红一次）；\n"
    "⑥ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）")
dump(out)
print("WROTE", OUT, flush=True)
