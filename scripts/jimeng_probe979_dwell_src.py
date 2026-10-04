#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 979 · 实验室探针：⭐⭐⭐⭐⭐ **`BODY` 到底是稳定停靠点，还是一个短暂状态？**

── 978 留下的那个分不开 ────────────────────────────────────────────

978 在空白页上完整复现了那枚 `document.body` 停靠点（2/2 × 5 臂），
但 `n_body_stops` **计数是抖的**（只有 L3：2 vs 3），而 978 **分不开**：

- (a) **读数时序** —— `document.body` 这个状态**本来就短暂**，
  固定 `settle` 偶尔没赶上 ⇒ 那是**测量**的问题
- (b) **页面真的抖** —— 某一圈里那一格**真的没出现**

⇒ ⇒ ⭐⭐⭐ **在分开之前，计数不许当判据**（978 的原话）

── ⭐⭐⭐⭐⭐ 本批把设计**换掉**，而不是再加一个变量 ─────────────────

978 原计划是「同一批臂跑**两种 settle 时长**做对照」。
⚠️⭐⭐⭐ **本批改成：按 `Tab` 之后立刻在页内轮询、记下**转变时间线**。**

理由：⭐⭐⭐ **两种 settle 只告诉你「哪一档更准」，不告诉你「它到底待了多久」**；
而**时间线直接给出停留时长** ⇒ ⇒ **它把「短 / 长两档」这个设计整个包含了**
⇒ ⇒ 而且它便宜得多（每步**一次** `evaluate`，不是几十次往返）

⇒ ⇒ ⭐⭐⭐⭐⭐ **换设计的正当理由是「原设计测不到那个量」，
不是「原设计跑不通」** —— 两者要分清。

── 本批量什么 ──────────────────────────────────────────────────────

每按一次 `Tab`，在页内**纯读**轮询 `document.activeElement`，
记下**每一次转变的时刻** ⇒ 于是每个状态的**停留时长**直接可算：

- `dwell_ms[key]` = 下一个转变时刻 − 本次转变时刻
- `body_seen` = 这一格里 `BODY` 有没有出现过
- `body_dwell_ms` = `BODY` 那一段待了多久

⇒ ⇒ ⭐⭐⭐ **判据要能分开两个方向**：
停留**很短**（一两个 rAF）⇒ (a) 读数时序；
停留**稳定**且仍会漏 ⇒ (b) 页面真抖。
⇒ ⇒ ⚠️ **探针不预写答案**，只输出时间线与停留时长。

⚠️⭐⭐⭐ **纯读**：只用 `document.activeElement` ＋ `requestAnimationFrame`，
**不装 `MutationObserver`、不劫持 `prototype`、不 `focus()`、不 `reload`**
⇒ 诊断动作**不留痕**（977 的纪律）。

**本批零计费**：**根本不打开源站**、**连 `mouse.click` 都没有**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b979-dwell.json"
REPS = 2
WINDOW_MS = 260        # ⭐ 按一次 Tab 之后**轮询多久**
N_STEPS = 8            # ⭐ 够走满两圈（空白页一圈 4 格）
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
# ⚠️⭐⭐ **五臂的定义**逐字继承 978（探针是**模块级代码**、不是字符串字面量
#   ⇒ 拿不到 ⇒ 改为**只继承它那句「每臂只差一个变量」的断言**，
#   并把臂表**重新写一遍**、再钉住「两支探针的臂表**逐格相同**」）
#   —— ⚠️⚠️⚠️ 这是本批**唯一**没法用 `_grab` 带走的东西，**必须记下来**
_p978 = _src("jimeng_probe978_lab_body_stop.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


INJECT_JS = _grab("INJECT_JS", _p976)
UNINJECT_JS = _grab("UNINJECT_JS", _p976)
LAB_PROBE_ID = "b979-lab-injected"

# ── ⭐⭐⭐⭐⭐ 本批**唯一**的新件：页内**纯读**轮询，取「转变时间线」──────
POLL_JS = """([ms]) => {
  // ⚠️⭐⭐⭐ 纯读：只读 `document.activeElement`；**不装监听、不劫持、
  //   不 focus()、不 reload** ⇒ 诊断动作不留痕
  return new Promise(function (resolve) {
    const t0 = performance.now();
    const seq = [];
    let last = null;
    const keyOf = function () {
      const a = document.activeElement;
      if (a === document.body) return 'BODY';
      if (a === null) return 'NULL';
      if (a.id) return a.id;
      const tid = a.getAttribute ? a.getAttribute('data-testid') : null;
      return (tid === null) ? ('<' + (a.tagName || '?') + '>') : tid;
    };
    const tick = function () {
      const t = performance.now() - t0;
      const k = keyOf();
      if (k !== last) { seq.push({t_ms: Math.round(t), key: k}); last = k; }
      if (t >= ms) { resolve({seq: seq, elapsed_ms: Math.round(t)}); return; }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}"""

# ── 五臂：**与 978 逐格相同**（下面那几条 assert 钉住这一点）────────────
# ⚠️⚠️⚠️⭐⭐⭐ **比对要比「模板」、不是「展开后的串」** ——
#   978 存的是 `'<button data-testid="lab-b%d" ...>' % (i, i, i)` 这个**模板**；
#   ⭐⭐⭐ 我第一版拿 `BUTTON_ROW`（**展开后**）去 `_p978` 里找 ⇒ 找不到
#   ⇒ ⇒ ⭐⭐ **又一次「同一个东西要比同一个口径」**（971 起就有的那条）
BUTTON_TPL = '<button data-testid="lab-b%d" id="lab-b%d">B%d</button>'
BUTTON_ROW = "".join(BUTTON_TPL % (i, i, i) for i in range(1, BTN + 1))
SPACER = '<div style="height:2600px;background:#eee">spacer</div>'
CSS_PLAIN = "<style>body{margin:0}button{width:120px;height:40px}</style>"

ARMS = [
    ("L0", "基线：内容装得下 ⇒ 文档**不可滚动**", CSS_PLAIN, BUTTON_ROW),
    ("L1", "同上 ＋ 2600px `spacer` ⇒ 文档**可滚动**", CSS_PLAIN,
     SPACER + BUTTON_ROW),
    ("L2", "**可滚动** ＋ `<body>` **最前面**注入一枚可聚焦元素",
     CSS_PLAIN, SPACER + BUTTON_ROW),
    ("L3", "`spacer` 被 `overflow:hidden` 容器裁住 ⇒ 文档**装得下**",
     CSS_PLAIN,
     '<div id="clip" style="height:300px;overflow:hidden">' + SPACER + "</div>"
     + BUTTON_ROW),
    ("L4", "**可滚动** ＋ 三个按钮塞进 `overflow:auto` 容器", CSS_PLAIN,
     SPACER + '<div id="box">' + BUTTON_ROW + "</div>"),
]

# ── ⭐⭐⭐ 自证与守卫 ────────────────────────────────────────────────
assert INJECT_JS in _p976 and UNINJECT_JS in _p976
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'if (old) old.remove();' in INJECT_JS
# ⚠️⭐⭐⭐ **新件必须纯读** —— 「诊断动作不许留痕」的物理禁止
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **本批第四次撞上「守卫命中注释」**（976/977/978 各一次）
#   ⇒ 这次**不再靠「注释不许抄被禁 API」**（那条太脆弱：
#   **说明纪律的地方恰恰最想提到那个 API**）
# ⇒ ⇒ ⭐⭐⭐⭐⭐ 改成**只扫代码行**：剥掉 `//` 与 `* ` 注释之后再看
#   ⇒ ⇒ 于是注释里**可以**正常写「不 focus()、不 reload」，
#   **门也仍然抓得住真代码**
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
# ⭐⭐⭐⭐⭐ **改门要成对**：钉住反向 —— 真的写了那些 API 时**必须仍被抓到**；
#   而**注释里提到它们不算**（这正是这次改门的全部意义）
for _bad, _tok in (("el.focus();", "focus("),
                   ("new MutationObserver(f);", "MutationObserver"),
                   ("window.addEventListener('x', f);", "addEventListener"),
                   ("HTMLElement.prototype.focus", "prototype"),
                   ("location.reload();", "location.reload")):
    assert _tok in _code_only("var a = 1;\n" + _bad + "\n"), (
        "纯读守卫**失灵**了：%r" % _bad)
    assert _tok not in _code_only("var a = 1;\n// 纪律：不许 " + _bad + "\n"), (
        "注释剥离守卫**失灵**了：%r" % _bad)
# ⚠️⭐⭐⭐ **新件里不许用 or 兜底**（978 收窄后的精确形状：只禁 or 兜底成假值）
OR_FALLBACK_TAILS = ("|| null", "|| ''", '|| ""', "|| 0", "|| {}",
                     "|| false", "|| undefined")


def _or_fallbacks(js):
    return [t for t in OR_FALLBACK_TAILS if t in js]


assert not _or_fallbacks(POLL_JS), _or_fallbacks(POLL_JS)
# ⭐⭐⭐⭐ **改门要成对**（978 定的规矩，本批继续照办）
for _bad in ("var a = x || null;", "var b = y || '';", "var c = z || 0;"):
    assert _or_fallbacks(_bad), "or-兜底守卫**失灵**了：%r" % _bad
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **本批唯一没法 `_grab` 带走的东西，必须**显式钉住**
#   ⇒ 五臂的**内容**（head + body）与 978 逐格相同
assert BUTTON_TPL in _p978 and SPACER in _p978, "978 里找不到同一份臂表"
assert BUTTON_TPL in open(__file__, encoding="utf-8").read(), "臂表模板对不上自己"
assert "".join(a[3] for a in ARMS).count("<button") == len(ARMS) * BTN, (
    "臂表按钮总数对不上")
# ⭐⭐⭐ **逐臂**写死「这一臂有且只有 BTN 个按钮」——
#   免得某一臂**手滑**少写一个、而总数那条仍然绿
for _k, _n, _h, _b in ARMS:
    assert _b.count("<button") == BTN, "%s 臂的按钮数不是 %d" % (_k, BTN)
assert CSS_PLAIN in _p978, "978 里找不到同一份 CSS"
assert len({a[0] for a in ARMS}) == len(ARMS), "臂的 key 重复了"
# ⭐⭐⭐⭐⭐ **「不许自己定义」只针对**继承来的那两件**（978 栽过这个）
assert not re.search(r'^(INJECT_JS|UNINJECT_JS)\s*=\s*r?"""',
                     open(__file__, encoding="utf-8").read(), re.M), (
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了")
for _bad in ('INJECT_JS = """x"""', "UNINJECT_JS = r\"\"\"x\"\"\""):
    assert re.search(r'^(INJECT_JS|UNINJECT_JS)\s*=\s*r?"""', _bad, re.M), (
        "分叉守卫**失灵**了：%r" % _bad)
# ⭐ 而**自己的新件**必须**能**被行首匹配到（证明上面那条不是恒真）
assert re.search(r'^POLL_JS\s*=\s*r?"""', 'POLL_JS = """x"""', re.M)


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
    """⭐⭐⭐⭐⭐ 相邻两个转变时刻之差 ＝ 那个状态的**停留时长**。

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版漏了「最后一个状态」** ——
    轮询窗口结束时**还停着的那个状态**同样有停留时长，
    而 `seq` 里的相邻差**算不到它** ⇒ 于是
    每一格里**只有一个状态**时，`body_dwell_ms` 整个变成 `[]`
    ⇒ ⇒ ⭐⭐ **「汇总层取值错了、原始读数里答案一直在」这一族的第五次**
    （965 / 969 / 970 / 974 / **本批**）：
    原始读数里明明有 `t_ms = 12`、`elapsed_ms = 264` ⇒ **停留约 252ms**，
    而汇总层给的是「**没有样本**」
    ⇒ ⇒ 修法：**用 `elapsed_ms` 给末态补一段**
    """
    o = []
    for i in range(len(seq) - 1):
        o.append({"key": seq[i]["key"],
                  "dwell_ms": seq[i + 1]["t_ms"] - seq[i]["t_ms"]})
    if seq and isinstance(elapsed_ms, (int, float)):
        last = seq[-1]
        o.append({"key": last["key"],
                  "dwell_ms": int(elapsed_ms) - last["t_ms"]})
    return o


out = {
    "target": "lab-blank-page", "url": "about:blank",
    "reps": REPS, "n_steps": N_STEPS, "window_ms": WINDOW_MS,
    "viewport": VIEWPORT, "n_buttons": BTN,
    "question": "⭐⭐⭐⭐⭐ **那枚 `BODY` 停靠点是「稳定停靠点」还是「一个短暂状态」？** ⇒ "
                "978 分不开的 (a) 读数时序 / (b) 页面真抖，**本批用停留时长分开**",
    "ruler": {
        "js_verbatim_from_976": ["INJECT_JS", "UNINJECT_JS"],
        "new_pieces": ["POLL_JS"],
        "why_design_changed": "⭐⭐⭐⭐⭐ **换设计的正当理由是「原设计测不到那个量」，"
                              "不是「原设计跑不通」** —— 978 原计划是"
                              "「两种 settle 时长做对照」，"
                              "⭐⭐⭐ **而两种 settle 只告诉你「哪一档更准」、"
                              "不告诉你「它到底待了多久」**；"
                              "**时间线直接给出停留时长** ⇒ 它把「短 / 长两档」"
                              "**整个包含**了 ⇒ 而且便宜得多（每步**一次** `evaluate`）",
        "what_cannot_be_grabbed": "⚠️⚠️⚠️⭐⭐⭐ **本批唯一没法 `_grab` 带走的东西**："
                                  "五臂的**定义**是**模块级代码**、不是字符串字面量 ⇒ "
                                  "拿不到 ⇒ **只能重写一遍**，"
                                  "**并用 `assert` 钉住臂表与 978 一致** ⇒ "
                                  "⭐⭐⭐ **凡是「靠 `_grab` 带不走的东西，"
                                  "就要显式钉住它没变**",
        "purity": "⚠️⭐⭐⭐ **纯读**：只用 `document.activeElement` ＋ "
                  "`requestAnimationFrame`；**不装 `MutationObserver`、"
                  "不劫持 `prototype`、不 `focus()`、不 `reload`** ⇒ "
                  "**诊断动作不留痕**（977 的纪律）",
        "identity_rule": "⭐⭐⭐⭐⭐ **一枚停靠点是不是 `BODY`，只问一件事**："
                         "`document.activeElement === document.body` ⇒ "
                         "**不用 tag、不用 aria、不用我起的名字**",
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
                # ⭐⭐⭐⭐⭐ **不等 settle，直接进页内轮询** ——
                #   settle 正是 978 那个「测不到停留时长」的量
                r = ev(POLL_JS, [WINDOW_MS])
                seq = (r or {}).get("seq") or []
                steps.append({"k": k, "key": "Tab", "seq": seq,
                              "elapsed_ms": (r or {}).get("elapsed_ms"),
                              "dwell": _dwell(seq, (r or {}).get("elapsed_ms"))})
            cell["steps"] = steps
        finally:
            if key == "L2":
                cell["uninject"] = ev(UNINJECT_JS, [LAB_PROBE_ID])
        # ── ⭐⭐⭐⭐⭐ 汇总：**只做计数与时长，不下结论** ──────────────
        all_dwell = [d for s in cell["steps"] for d in s["dwell"]]
        cell["dwell_all"] = all_dwell
        body_d = [d["dwell_ms"] for d in all_dwell if d["key"] == "BODY"]
        cell["n_body_dwell_samples"] = len(body_d)
        cell["body_dwell_ms"] = body_d
        cell["n_body_dwell_le_32ms"] = sum(1 for x in body_d if x <= 32)
        cell["n_body_dwell_gt_100ms"] = sum(1 for x in body_d if x > 100)
        other = [d["dwell_ms"] for d in all_dwell if d["key"] != "BODY"]
        cell["other_dwell_ms"] = other
        cell["n_steps_with_body"] = sum(
            1 for s in cell["steps"]
            if any(d["key"] == "BODY" for d in s["dwell"]))
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


def _cycle_keys(c):
    """⭐⭐⭐⭐⭐ 跨轮比**顺序关系**、不比绝对数值（974；978 又犯过一次）。"""
    seq = []
    for s in c.get("steps") or []:
        for d in s["dwell"]:
            if not seq or seq[-1] != d["key"]:
                seq.append(d["key"])
    if len(seq) > 1 and seq[0] in seq[1:]:
        return seq[:seq.index(seq[0], 1)]
    return seq


out["reps_agree"] = all(
    _cycle_keys(_cell(_r0, a[0])) == _cycle_keys(_cell(_r1, a[0])) for a in ARMS)

out["design_gates"] = {
    # ⭐ 每一步都拿到了**非空**时间线（否则「没看见 BODY」没有意义）
    "every_step_has_a_timeline_both_reps": _both_arms(
        lambda c: len(c.get("steps") or []) == N_STEPS
        and all(len(s.get("seq") or []) >= 1 for s in c["steps"])),
    # ⭐⭐ 轮询窗口**真的跑满了**（时间线必须覆盖整段，否则时长是残缺的）
    "poll_window_completed_both_reps": _both_arms(
        lambda c: all((s.get("elapsed_ms") or 0) >= WINDOW_MS - 40
                      for s in c.get("steps") or [])),
    # ⭐⭐⭐⭐⭐ **焦点真的在动** ——
    # ⚠️⚠️⚠️ **第一版这条门写错了**：它要求「每个轮询窗口里出现**多次**转变」，
    #   ⭐⭐⭐ 而本批的设计**恰恰相反** —— 每次 `Tab` 之后焦点**落定就不动**，
    #   转变发生在**窗口之间** ⇒ ⇒ 门编码了一个**错的预期**
    # ⇒ ⇒ ⭐⭐ **门红先判门还是数据**：门错。改成「跨窗口**出现过多种状态**」
    "focus_actually_moves_both_reps": _both_arms(
        lambda c: len({d["key"] for s in c.get("steps") or []
                       for d in s["dwell"]}) >= 3),
    # ⭐⭐ **L2 的注入生效且被还原**
    "l2_injection_applied_and_restored_both_reps": all(
        (_cell(a, "L2").get("inject") or {}).get("injected") is True
        and (_cell(a, "L2").get("uninject") or {}).get("removed") is True
        for a in (_r0, _r1) if _cell(a, "L2")),
    # ⭐⭐⭐⭐ **顺序关系**跨轮一致（**不是**绝对数值）
    "cycle_keys_stable_across_reps_both_reps": all(
        _cycle_keys(_cell(a, x[0])) == _cycle_keys(_cell(b, x[0]))
        for a, b in ((_r0, _r1),) for x in ARMS),
}

out["recon"] = {
    "rep%d" % i: {
        a.get("arm"): {
            "cycle_keys": _cycle_keys(a),
            "n_steps_with_body": a.get("n_steps_with_body"),
            "n_body_dwell_samples": a.get("n_body_dwell_samples"),
            "body_dwell_ms": a.get("body_dwell_ms"),
            "n_body_dwell_le_32ms": a.get("n_body_dwell_le_32ms"),
            "n_body_dwell_gt_100ms": a.get("n_body_dwell_gt_100ms"),
            "other_dwell_ms": (a.get("other_dwell_ms") or [])[:12],
        }
        for a in arms
    }
    for i, arms in enumerate((_r0, _r1))
}

out["gate_notes"] = (
    "⭐ 979 的门只管「**实验成立吗**」，**不碰「结论是什么」**：\n"
    "  · ⭐⭐⭐ `focus_actually_transitions` 防的是「时间线只有一个状态」"
    "⇒ 那样的话 `n_body_dwell_samples = 0` **不能**读成「`BODY` 不待」；\n"
    "  · ⭐⭐ `poll_window_completed` 防的是「窗口被截断」⇒ "
    "那样算出来的 `dwell_ms` 是**残缺的**；\n"
    "  · ⭐⭐⭐⭐⭐ `cycle_keys_stable` 比的是**顺序关系**、"
    "**不是绝对数值**（974；978 又犯过一次）；\n"
    "  · ⭐⭐⭐⭐ **`body_dwell_ms` 刻意不判真假** —— "
    "「短 / 长」的分界**由 verifier 判**，**探针不预写**；\n"
    "  · ⚠️ **`n_body_dwell_le_32ms` 与 `n_body_dwell_gt_100ms` 都记下来**，"
    "是为了让「到底是 (a) 还是 (b)」这件事**可以被两条独立的门分别钉**。"
)

out["what_979_measures"] = (
    "① ⭐⭐⭐⭐⭐ 每按一次 `Tab`，**页内纯读轮询** `document.activeElement`，"
    "记下**每一次转变的时刻** ⇒ 每个状态的**停留时长**直接可算；\n"
    "  ② ⭐⭐⭐⭐ 由此分开 978 分不开的那两件事："
    "停留**很短** ⇒ (a) 读数时序；停留**稳定**却仍会漏 ⇒ (b) 页面真抖；\n"
    "  ③ ⭐⭐ 三条独立的计数同时记："
    "`<=32ms` 的次数、`>100ms` 的次数、总样本数 ⇒ "
    "**让 verifier 能用两条独立的门分别钉「短」和「长」**"
)

out["discipline_979"] = (
    "① ⭐⭐⭐⭐⭐ **换设计的正当理由是「原设计测不到那个量」，"
    "不是「原设计跑不通」** —— 这两件事要分清；\n"
    "  ② ⭐⭐⭐⭐⭐ **跨轮比顺序关系、不比绝对数值**（974；978 又犯过一次）；\n"
    "  ③ ⭐⭐⭐⭐ **一次失败不叫「没有」**（978 的原话，979 继续照办）；\n"
    "  ④ ⭐⭐⭐⭐⭐ **凡是「靠 `_grab` 带不走的东西，就要显式钉住它没变」** —— "
    "五臂的**定义**是**模块级代码**、不是字符串字面量 ⇒ 拿不到 ⇒ "
    "只能重写一遍 ＋ 用 `assert` 钉住臂表与 978 一致；\n"
    "  ⑤ ⭐⭐⭐ **纯读**：不装 `MutationObserver`、不劫持 `prototype`、"
    "不 `focus()`、不 `reload` ⇒ **诊断动作不留痕**；\n"
    "  ⑥ ⭐⭐⭐⭐ **过宽的门和过窄的门一样坏**（978 撞过）⇒ "
    "or 兜底那条**收窄成精确形状**、**并成对钉住反向**；\n"
    "  ⑦ ⭐⭐⭐⭐⭐ **本批零计费**：**根本不打开源站**、"
    "**连 `mouse.click` 都没有**"
)

out["skip_note"] = (
    "⚠️ 本批**只回答「`BODY` 停多久」**，"
    "**不回答「是哪一条规范/引擎行为造成的」** ⇒ "
    "⭐⭐⭐ **时长 ≠ 出处**，这两件事不许混成一句话"
)

dump(out)
print("PROBE_979_DONE", out["reps_agree"], flush=True)
