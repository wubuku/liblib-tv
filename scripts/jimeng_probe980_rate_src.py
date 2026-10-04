#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 980 · 实验室探针：⭐⭐⭐⭐⭐ **把 (b) 量化** ——
「那枚 `BODY` 是通常在、但不是每次都在的一格」，这句话现在只有一个
2 vs 3 的印象支撑；本批把它变成**比率**。

── 979 之后剩什么 ────────────────────────────────────────────────────

- 978：空白页上**完整复现** ⇒ **引擎/规范层面**的行为
- 979：⭐⭐⭐⭐⭐ **`BODY` 不是短暂状态** —— 停留 249–252ms，
  **与其他每一格的 248–252 完全一样**
  ⇒ ⇒ 978 的 (a)「读数时序」被否
  ⇒ ⇒ **那 978 的计数抖动只能用 (b) 解释** ——
  **引擎有时真的不走那一格**
  ⇒ ⇒ ⭐⭐⭐ **这直接削弱 H₃ 里的「恒」**

⚠️⚠️⚠️ **但「有时」现在只是个印象** —— 一轮里 2 圈 vs 3 次，
**一个 2 vs 3 撑不起「不是每次都在」这句话**
⇒ ⇒ ⭐⭐⭐⭐⭐ **本批只做一件事：跑够多的圈，数「有几圈没走 `BODY`」。**

── ⭐⭐⭐⭐⭐ 本批的方法上有一处关键选择 ────────────────────────────

979 已经证明：**每次 `Tab` 之后焦点落定、整段窗口都不再变**。
⇒ ⇒ ⭐⭐⭐⭐⭐ **本批不需要长的轮询窗口** ——
窗口只要**够长到确认「落定了」**即可 ⇒ **窗口越短，能跑的圈数越多**
⇒ ⇒ 而「**能跑多少圈**」正是本批的核心（**统计量需要样本量**）

⚠️⭐⭐⭐ **窗口不能短到看不见 `BODY`** ⇒ 两边都有门：
- 门①：979 已证 `BODY` 停留 ≈250ms ⇒ 本批窗口 ≥ 120ms 才算「看得见」
- 门②：**每一圈**的 `BODY` 若出现，其**停留时长**必须 ≥ 门①的量级
  ⇒ 否则说明「这一格没被看见」其实是**窗口太短**，不是**引擎没走**
  ⇒ ⇒ ⭐⭐⭐ **这条是本批的关键前提**：
  **「没看见」必须先排除「没看够」**，否则就是 978 那个错

── ⭐⭐ 不预写比率 ──────────────────────────────────────────────────

探针只输出 `n_cycles` / `cycles_with_body` / `cycles_without_body`
**以及每圈的实际停留时长** ⇒ 比率由 verifier 判。

**本批零计费**：**根本不打开源站**、**连 `mouse.click` 都没有**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b980-rate.json"
REPS = 2
N_STEPS = 72          # ⭐ 4 格一圈 ⇒ 约 18 圈（统计量需要样本量）
WINDOW_MS = 140       # ⭐ 门①：≥120ms 才算「看得见 BODY」
MIN_VISIBLE_MS = 120  # ⭐ 门②：低于它的停留算「没看够」，不算「引擎没走」
VIEWPORT = {"width": 1512, "height": 1200}
BTN = 3

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


_p976 = _src("jimeng_probe976_counterfactual_src.py")
_p979 = _src("jimeng_probe979_dwell_src.py")
_p978 = _src("jimeng_probe978_lab_body_stop.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⭐⭐⭐⭐⭐ **轮询仪器逐字继承 979** ⇒ 「本批与 979 测的是同一件事」
POLL_JS = _grab("POLL_JS", _p979)

# ── 臂：**逐格继承 979**（L0 与 L2 —— 一个 4 格环、一个 5 格环）──────
BUTTON_TPL = '<button data-testid="lab-b%d" id="lab-b%d">B%d</button>'
BUTTON_ROW = "".join(BUTTON_TPL % (i, i, i) for i in range(1, BTN + 1))
SPACER = '<div style="height:2600px;background:#eee">spacer</div>'
CSS_PLAIN = "<style>body{margin:0}button{width:120px;height:40px}</style>"

ARMS = [
    ("L0", "基线：内容装得下 ⇒ 文档**不可滚动**；4 格环",
     CSS_PLAIN, BUTTON_ROW),
    ("L2", "**可滚动** ＋ `<body>` **最前面**注入一枚可聚焦元素；5 格环",
     CSS_PLAIN, SPACER + BUTTON_ROW),
]
INJECT_JS = _grab("INJECT_JS", _p976)
UNINJECT_JS = _grab("UNINJECT_JS", _p976)
LAB_PROBE_ID = "b980-lab-injected"


# ── ⭐⭐⭐ 自证与守卫 ────────────────────────────────────────────────
# ⚠️⭐⭐⭐⭐⭐ **979 的教训照抄**：
#  ① 「不许自己定义」只针对**继承来的**那几件（978 栽过）
assert not re.search(r'^(POLL_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""',
                     open(__file__, encoding="utf-8").read(), re.M), (
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了")
for _bad in ('POLL_JS = """x"""', 'INJECT_JS = r"""x"""',
             "UNINJECT_JS = \"\"\"x\"\"\""):
    assert re.search(r'^(POLL_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""', _bad, re.M), (
        "分叉守卫**失灵**了：%r" % _bad)
# ② 臂表**逐格继承 979 / 978**（模板、CSS、逐臂按钮数）
assert BUTTON_TPL in _p978 and SPACER in _p978 and CSS_PLAIN in _p978, (
    "978 里找不到同一份臂表")
assert BUTTON_TPL in _p979, "979 里找不到同一个按钮模板"
for _k, _n, _h, _b in ARMS:
    assert _b.count("<button") == BTN, "%s 臂的按钮数不是 %d" % (_k, BTN)
# ③ 注入件仍是 976 的那一件（幂等 + 插在最前）
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'if (old) old.remove();' in INJECT_JS
# ④ ⭐⭐⭐⭐⭐ **本批的关键前提**（门②）必须**在探针里**就成立：
#    窗口 ≥ 门① 的可见下限 ⇒ 否则「没看见」分不清是「没看够」还是「没走」
assert WINDOW_MS >= MIN_VISIBLE_MS, "窗口比可见下限还短 ⇒ 前提不成立"
# ⭐⭐⭐⭐ **成对**：钉住反向 —— 窗口一旦短于下限，那道门**必须仍然是红的**
def _window_ok(win, floor):
    return win >= floor


assert _window_ok(WINDOW_MS, MIN_VISIBLE_MS) is True
assert _window_ok(MIN_VISIBLE_MS - 1, MIN_VISIBLE_MS) is False, (
    "窗口门失灵（窗口短于可见下限时仍绿）")
# ⑤ ⭐⭐ 979 的教训：**只扫代码行**（剥掉 `//` 与 `* `）⇒
#    注释里可以正常提到被禁 API，而门仍抓得住真代码


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


POLL_CODE = _code_only(POLL_JS)
for _forbidden in ("focus(", "MutationObserver", "addEventListener",
                   "prototype", "location.reload"):
    assert _forbidden not in POLL_CODE, "POLL_JS 里出现了 %r" % _forbidden
for _bad, _tok in (("el.focus();", "focus("),
                   ("new MutationObserver(f);", "MutationObserver"),
                   ("window.addEventListener('x', f);", "addEventListener"),
                   ("HTMLElement.prototype.focus", "prototype"),
                   ("location.reload();", "location.reload")):
    assert _tok in _code_only("var a = 1;\n" + _bad + "\n"), (
        "纯读守卫**失灵**了：%r" % _bad)
    assert _tok not in _code_only("var a = 1;\n// 纪律：不许 " + _bad + "\n"), (
        "注释剥离守卫**失灵**了：%r" % _bad)


def ev(js, arg=None):
    if arg is None:
        return page.evaluate(js)
    return page.evaluate(js, arg)


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def _build(arm):
    key, _note, head, body = arm
    page.goto("about:blank", wait_until="domcontentloaded")
    page.set_viewport_size(VIEWPORT)
    page.set_content(
        "<!doctype html><html><head>%s</head><body>%s</body></html>"
        % (head, body), wait_until="load")
    page.wait_for_timeout(200)
    return key


def _dwell(seq, elapsed_ms=None):
    """⭐⭐⭐⭐⭐ **与 979 逐字同构**（连同「末态」那段一起继承）——
    979 漏末态导致 `body_dwell_ms` 整个变成 `[]`，
    那是「汇总层取值错了」的第五次 ⇒ 本批不许再漏。"""
    o = []
    for i in range(len(seq) - 1):
        o.append({"key": seq[i]["key"],
                  "dwell_ms": seq[i + 1]["t_ms"] - seq[i]["t_ms"]})
    if seq and isinstance(elapsed_ms, (int, float)):
        last = seq[-1]
        o.append({"key": last["key"],
                  "dwell_ms": int(elapsed_ms) - last["t_ms"]})
    return o


def _cycles(keys):
    """⭐⭐⭐⭐⭐ 把「按键序列」切成**一个个完整圈**。

    ⚠️ **切法必须在读数里写清**：从 `keys[0]` 开始，一直走到 `keys[0]`
    **再次出现**为止，那一段就是**一圈**（首尾同键）。
    ⇒ 最后一圈若没走完（没有再次出现 `keys[0]`），
    **单独记成 `tail`、不许算进 `n_cycles`**。
    """
    full, i, first = [], 0, (keys[0] if keys else None)
    if first is None:
        return full, []
    while True:
        j = i + 1
        while j < len(keys) and keys[j] != first:
            j += 1
        if j >= len(keys):
            return full, keys[i:]          # ⭐ 残段：不完整 ⇒ 不算
        full.append(keys[i:j + 1])
        i = j + 1


def _cycles_len_ok(full, ring_len):
    """⭐⭐⭐⭐⭐ 每一圈都**恰好覆盖环里每一格一次**。

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **我在这里错了两次，两次都是判据选错**：
    · 第一版用「首尾同键」⇒ 切出来的圈**会带着旋转**
      （第一圈 `[a,b,c,B,a]`、第二圈 `[b,c,B,a]`）⇒ **第二圈明明完整、首尾却不同键**
    · 第二版用「长度 = 环长 + 1」⇒ **同样不稳** ——
      起点旋转时有的圈是 5 枚、有的圈是 4 枚（**都是完整的**）
    ⇒ ⇒ ⭐⭐⭐⭐⭐ **判据必须挑一个在旋转下不变的东西**
    ⇒ ⇒ **`len(set(这一圈)) == 环格数`** —— 每一圈**恰好覆盖每一格一次**，
      与起点在哪儿**无关**
    """
    if not full or ring_len < 2:
        return False
    return all(len(set(c)) == ring_len for c in full)


# ⭐⭐⭐⭐⭐ **切圈器自测**（六个用例，含**带旋转**与**残段**两种边界）
# ⚠️⚠️⚠️ **这些期望值是「先在纸上推一遍、再逐个跑出来」的** ——
#   ⭐⭐⭐ **我第一版把期望值写错了三处**（把残段当完整圈、把圈数多算一圈）
#   ⇒ ⇒ ⭐⭐ **切圈这种「自己给自己当分母」的逻辑，必须有自测**
#   ⇒ 否则一个错的切法会**安静地**把「有 BODY 的圈」算成另一个数
# ⚠️⚠️⚠️⭐⭐⭐ **而且「自测的期望值」本身也是我推的、也推错过两处**
#   （把残段当完整圈、圈数多算一圈）⇒ ⇒ ⭐⭐ **期望值错了，自测就是假绿**
#   ⇒ ⇒ 期望值必须**按定义一句一句推**，不能「跑出来是什么就写什么」——
#   **那样自测就恒真了**
for _in, _n, _tail in (
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'], 2, ['b']),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B'], 1, ['b', 'c', 'B']),
        (['a', 'b', 'a', 'b', 'a', 'b'], 2, ['b']),
        (['a'], 0, ['a']),
        ([], 0, []),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a'],
         3, [])):
    _f, _t = _cycles(_in)
    assert len(_f) == _n, "切圈器自测失败：%r ⇒ %d 圈（应为 %d）" % (_in, len(_f), _n)
    assert _t == _tail, "切圈器自测失败（残段）：%r ⇒ %r" % (_in, _t)
assert _cycles_len_ok([['a', 'b', 'c', 'B', 'a'],
                       ['b', 'c', 'B', 'a']], 4) is True
assert _cycles_len_ok([['a', 'b', 'c', 'B', 'a'],
                       ['b', 'c', 'B']], 4) is False, "少一格的那圈必须判红"
assert _cycles_len_ok([], 4) is False
# ⭐⭐⭐⭐⭐ **环格数要从读数里**量**出来（distinct 数），不能假设**
_full4, _tail4 = _cycles(['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'])
assert len(set(_full4[0])) == 4 and len(set(_full4[1])) == 4
assert _cycles_len_ok(_full4, 4) is True
# ⚠️⚠️⚠️⭐⭐ **「`BODY`」那一格在键里长的是 `'BODY'`，而按钮是 `'lab-bN'`**
#   ⇒ ⭐⭐ **`set` 是大小写敏感的**：我用 `set('abcBab')` 想凑 3 格，
#   实际它有 **4** 个（`'B'` 和 `'b'` 是两个）⇒ **期望值又错一次**
#   ⇒ ⇒ 改用真正 3 格的集合来钉「ring_len 必须显式传」
assert _cycles_len_ok(_full4, len(set('abc'))) is False, (
    "3 枚的圈在 3 格环下**合法** ⇒ 判据必须带 ring_len，不能写死")
assert len(set('abcBab')) == 4, "**大小写敏感**这一条也要被钉住"

def _slicer_ok(keys, full, tail):
    """⭐⭐⭐⭐⭐ **切圈器的有效性不变量：连续 ＋ 可重建**（与 `BODY` 无关）。

    ⇒ 把所有圈与残段**按顺序接起来**，必须**逐格等于**原始 `keys`
    ⇒ ⇒ 这条**不会**因为「某一圈少了 `BODY`」而红
    ⇒ ⇒ ⭐⭐ **这才是「切得对不对」该问的问题**
    """
    rebuilt = [k for c in full for k in c] + list(tail)
    return rebuilt == list(keys)


assert _slicer_ok(['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'],
                  _cycles(['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'])[0],
                  _cycles(['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'])[1])
assert _slicer_ok(['a', 'b', 'c', 'B', 'a', 'b'], [], ['a', 'b', 'c', 'B', 'a', 'b'])
# ⭐⭐⭐⭐ **成对**：钉住反向 —— 顺序错 / 多出一枚，**都必须仍红**
# ⚠️⚠️⚠️⭐⭐⭐ 而「少一格」**不算反例**：
#   `[['a','b','c']] + ['B']` **照样能重建** ⇒ ⇒ ⭐⭐⭐⭐⭐
#   **「连续 ＋ 可重建」这条不变量天生看不见「少一格」**
#   ⇒ ⇒ 而那**正是本批要测的东西**、**本来就该由它可见**
#   ⇒ ⇒ ⭐⭐ **一条不变量管不了的事，要另立一条读数**（`laps_missing_a_ring_member`）
assert _slicer_ok(['a', 'b', 'c', 'B'], [['a', 'c', 'b', 'B']], []) is False, (
    "顺序错必须判红")
assert _slicer_ok(['a', 'b', 'c', 'B'], [['a', 'b', 'c', 'B', 'B']], []) is False, (
    "多出一枚必须判红")
assert _slicer_ok(['a', 'b', 'c', 'B'], [['a', 'b', 'c', 'B']], []) is True
assert _slicer_ok(['a', 'b', 'c', 'B'], [['a', 'b', 'c']], ['B']) is True, (
    "**少一格仍算合法重建** —— 这是这条不变量的**已知盲区**，已另立读数")

out = {
    "target": "lab-blank-page", "url": "about:blank",
    "reps": REPS, "n_steps": N_STEPS, "window_ms": WINDOW_MS,
    "min_visible_ms": MIN_VISIBLE_MS, "viewport": VIEWPORT,
    "n_buttons": BTN,
    "question": "⭐⭐⭐⭐⭐ **把「那枚 `BODY` 不是每次都在」量化** —— "
                "跑够多的圈，数「有几圈**没走** `BODY`」⇒ "
                "**一个 2 vs 3 撑不起这句话**",
    "ruler": {
        "js_verbatim_from_979": ["POLL_JS"],
        "js_verbatim_from_976": ["INJECT_JS", "UNINJECT_JS"],
        "new_pieces": [],
        "why_window_is_shorter": "⭐⭐⭐⭐⭐ 979 已证「每次 `Tab` 之后焦点落定、"
                                 "整段窗口都不再变」⇒ 本批**不需要长窗口** ⇒ "
                                 "**窗口越短、能跑的圈数越多** ⇒ "
                                 "而「**能跑多少圈**」正是本批的核心"
                                 "（**统计量需要样本量**）",
        "key_precondition": "⭐⭐⭐⭐⭐ **「没看见」必须先排除「没看够」** —— "
                            "否则就是 978 那个错 ⇒ 门②：若某圈 `BODY` 出现，"
                            "其**停留时长**必须 ≥ `min_visible_ms` "
                            "⇒ 否则算「窗口太短」，**不算「引擎没走」**",
        "inherited_arms": "⭐⭐⭐ 臂表**逐格继承 978 / 979**（模板、CSS、"
                          "逐臂按钮数）⇒ 探针里用 `assert` 钉住"
    },
    "arms": [{"key": a[0], "note": a[1]} for a in ARMS],
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "arms": []}
    out["runs"].append(rec)
    dump(out)

    for arm in ARMS:
        key = _build(arm)
        cell = {"arm": key}
        rec["arms"].append(cell)
        inj = None
        if key == "L2":
            inj = ev(INJECT_JS, [LAB_PROBE_ID])
            page.wait_for_timeout(120)
        cell["inject"] = inj
        try:
            steps = []
            for k in range(1, N_STEPS + 1):
                page.keyboard.press("Tab")
                r = ev(POLL_JS, [WINDOW_MS])
                seq = (r or {}).get("seq") or []
                steps.append({"k": k, "key": "Tab", "seq": seq,
                              "elapsed_ms": (r or {}).get("elapsed_ms"),
                              "dwell": _dwell(seq, (r or {}).get("elapsed_ms"))})
            cell["steps"] = steps
        finally:
            if key == "L2":
                cell["uninject"] = ev(UNINJECT_JS, [LAB_PROBE_ID])
        # ── ⭐⭐⭐⭐⭐ 汇总：切圈、数「有 / 没有 `BODY` 的圈」──
        keys = [d["key"] for s in cell["steps"] for d in s["dwell"]]
        cell["keys"] = keys
        full, tail = _cycles(keys)
        # ⭐⭐⭐⭐⭐ 切圈之后**不完整的那一段不许算进 `n_cycles`**
        cell["cycles"] = full
        cell["tail_keys"] = tail
        cell["n_cycles"] = len(full)
        # ⭐⭐⭐⭐⭐ **环格数从读数里**量**（distinct 数），不假设
        cell["ring_len"] = len(set(keys))
        cell["cycles_with_body"] = sum(1 for c in full if "BODY" in c)
        cell["cycles_without_body"] = sum(1 for c in full if "BODY" not in c)
        # ⭐⭐⭐⭐⭐ **「这一圈少覆盖了环里的格」** —— 这是**被测量的量**、**不是门**
        #   ⇒ 少 `BODY` 的圈会**只覆盖 3/4 格**，而**别的格**少的圈**更严重**
        cell["laps_missing_a_ring_member"] = sum(
            1 for c in full if len(set(c)) < cell["ring_len"])
        cell["ring_len"] = len(set(keys))
        # ⭐⭐⭐⭐⭐ 门② 的读数：`BODY` 出现时它的**停留时长**
        body_d = [d["dwell_ms"] for s in cell["steps"] for d in s["dwell"]
                  if d["key"] == "BODY"]
        cell["body_dwell_ms"] = body_d
        cell["n_body_dwell_below_floor"] = sum(1 for x in body_d
                                               if x < MIN_VISIBLE_MS)
        cell["n_body_dwell_ge_floor"] = sum(1 for x in body_d
                                            if x >= MIN_VISIBLE_MS)
        dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
def _cell(arms, key):
    for a in arms:
        if a.get("arm") == key:
            return a
    return {}


_r0 = out["runs"][0]["arms"] if out["runs"] else []
_r1 = out["runs"][1]["arms"] if len(out["runs"]) > 1 else []


def _both_arms(fn):
    ok = True
    for k, _n, _h, _b in ARMS:
        for arms in (_r0, _r1):
            c = _cell(arms, k)
            if not c:
                return False
            ok = ok and bool(fn(c))
    return ok


out["reps_agree"] = all(
    _cell(_r0, a[0]).get("n_cycles") == _cell(_r1, a[0]).get("n_cycles")
    for a in ARMS)

out["design_gates"] = {
    # ⭐ 圈数**够多**（统计量需要样本量；太少就只是一个印象）
    "enough_cycles_both_reps": _both_arms(
        lambda c: c.get("n_cycles", 0) >= 10),
    # ⭐⭐⭐⭐⭐ **门②**：`BODY` 出现时，**每一段**的停留都 ≥ 可见下限
    #   ⇒ ⇒ **「没看见」就不可能是「没看够」** ⇒ 门是绿的
    "body_dwell_all_above_floor_both_reps": _both_arms(
        lambda c: (c.get("n_body_dwell_below_floor") == 0)
        and (c.get("n_body_dwell_ge_floor") or 0) >= 10),
    # ⭐⭐ 每一步都读到了键（读数不许断档）
    "every_step_has_a_key_both_reps": _both_arms(
        lambda c: len(c.get("steps") or []) == N_STEPS
        and all(s.get("dwell") for s in c["steps"])),
    # ⭐⭐⭐⭐⭐ **切圈器有没有出错** —— 判据是**连续性 ＋ 可重建**：
    #   把所有圈与残段**按顺序接起来**，必须**逐格等于**原始 `keys`
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **这一条第一版写成「每一圈都覆盖环里每一格」⇒ 它判红了 ——
    #   而⭐⭐ **红的不是门、是数据**：少了 `BODY` 的那一圈**真的只覆盖 3/4 格**
    #   （那正是本批要找的东西）⇒ ⇒ ⭐⭐ **一条门只能管一件事**：
    #   「切得对不对」归切得对不对，「有没有少一格」是被测量的量
    # ⇒ ⇒ 处置是**改精确 + 不放宽**：把有效性判据换成**与 BODY 无关**的不变量，
    #   而「少一格」另立一条**记录用**的读数
    "slicer_is_contiguous_and_reconstructible_both_reps": _both_arms(
        lambda c: _slicer_ok(c.get("keys") or [], c.get("cycles") or [],
                             c.get("tail_keys") or [])),
    # ⭐⭐ L2 的注入生效且被还原
    "l2_injection_applied_and_restored_both_reps": all(
        (_cell(a, "L2").get("inject") or {}).get("injected") is True
        and (_cell(a, "L2").get("uninject") or {}).get("removed") is True
        for a in (_r0, _r1) if _cell(a, "L2")),
}

out["recon"] = {
    "rep%d" % i: {
        a.get("arm"): {
            "n_cycles": a.get("n_cycles"),
            "cycles_with_body": a.get("cycles_with_body"),
            "cycles_without_body": a.get("cycles_without_body"),
            "ring_len": a.get("ring_len"),
            "laps_missing_a_ring_member": a.get("laps_missing_a_ring_member"),
            "n_body_dwell_ge_floor": a.get("n_body_dwell_ge_floor"),
            "n_body_dwell_below_floor": a.get("n_body_dwell_below_floor"),
            "body_dwell_ms_sample": (a.get("body_dwell_ms") or [])[:20],
            "tail_keys": a.get("tail_keys"),
        }
        for a in arms
    }
    for i, arms in enumerate((_r0, _r1))
}

out["gate_notes"] = (
    "⭐ 980 的门围绕「**统计量站不站得住**」与「**关键前提**」：\n"
    "  · ⭐⭐⭐⭐⭐ `body_dwell_all_above_floor` 是**本批的关键前提** —— "
    "若 `BODY` 出现时它的停留**每一段**都 ≥ `min_visible_ms`（120ms），"
    "那么「某一圈没看见 `BODY`」就**不能**用「窗口太短」解释 ⇒ "
    "⭐⭐⭐ **「没看见」必须先排除「没看够」**，否则就是 978 那个错；\n"
    "  · ⭐ `enough_cycles` 防的是「圈数太少、结论又变回一个印象」；\n"
    "  · ⭐⭐ `cycles_are_complete` 防的是「把**不完整**的一段也算成一圈」\n"
    "    ⇒ ⭐⭐ **切圈的残段不许算进 `n_cycles`**；\n"
    "  · ⭐⭐⭐⭐ `cycles_without_body` / `n_cycles` 的**比率刻意不判真假** —— "
    "**由 verifier 判** ⇒ **不预写比率是多少**。"
)

out["what_980_measures"] = (
    "① ⭐⭐⭐⭐⭐ **跑够多的圈**（每臂 ≥ 10 圈），"
    "数「有几圈**没走** `BODY`」⇒ 把「通常在、但不是每次都在」"
    "从 2 vs 3 的**印象**变成**比率**；\n"
    "  ② ⭐⭐⭐⭐⭐ **门②**：`BODY` 出现时它的**停留时长**逐段 ≥ 120ms ⇒ "
    "⇒ **「没看见」先排除「没看够」**；\n"
    "  ③ ⭐⭐⭐ 切圈的**残段**单独记 `tail_keys`、**不算进 `n_cycles`**"
)

out["discipline_980"] = (
    "① ⭐⭐⭐⭐⭐ **「没看见」必须先排除「没看够」** —— 否则就是 978 那个错 ⇒ "
    "**门②是本批的关键前提**，不是细节；\n"
    "  ② ⭐⭐⭐⭐ **统计量需要样本量** ⇒ 圈数本身要有门（≥ 10 圈）⇒ "
    "**一个 2 vs 3 撑不起「不是每次都在」这句话**；\n"
    "  ③ ⭐⭐⭐⭐⭐ **换设计的正当理由是「原设计测不到那个量」**（979 的原话）—— "
    "979 证了「落定就不动」⇒ **窗口可以短** ⇒ **能跑的圈数变多**；\n"
    "  ④ ⭐⭐⭐ **切圈的残段不许算进分母**；\n"
    "  ⑤ ⭐⭐⭐⭐ **凡是「靠 `_grab` 带不走的东西，就要显式钉住它没变」**"
    "（臂表是模块级代码）；\n"
    "  ⑥ ⭐⭐⭐⭐⭐ **「不许自己定义」只针对继承来的那几件**（978 栽过）；\n"
    "  ⑦ ⭐⭐⭐⭐ **只扫代码行**（剥掉 `//` 与 `* `）⇒ "
    "**注释里可以正常提到被禁 API，而门仍抓得住真代码**；\n"
    "  ⑧ ⭐⭐⭐⭐⭐ **本批零计费**：**根本不打开源站**、"
    "**连 `mouse.click` 都没有**"
)

out["skip_note"] = (
    "⚠️ 本批**只回答「空白页上 `BODY` 出现的圈数占比」**，"
    "**不回答「源站那个页面上占比是多少」** ⇒ ⭐⭐ "
    "**实验室的比率不等于源站的比率**，两者不许混成一句话"
)

dump(out)
print("PROBE_980_DONE", out["reps_agree"], flush=True)
