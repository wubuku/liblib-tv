#!/usr/bin/env python3
"""batch 768 汇编器：从 raw/vb768a.json（基线）+ raw/vb768b.json（注入对照）现算

本批要回答 767 的 J9：**关闭一个 disclosure 浮层时，焦点会不会回到触发器。**

规矩（沿用 756–767）：
1. **数字不许手抄** —— 每个数都从 raw 或从 src 现算。
   连「哪个浮层的 Esc 处理器挂在哪个阶段」也是**当场读源码数出来的**，
   因为 767 的 O3 静态断言（"三者都有捕获/冒泡阶段的 Esc 处理"）
   与本批读数对不上，必须换成可复算的数。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**：`findings[k] == judgments[i].evidence`
   写盘前逐条断言，JSON 往返后由验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空。
6. **「读数在某元素上」不等于「有人把它挪到了那儿」**（本批 R75）：
   焦点在触发器上可能是**没人动它**。所以必须有一条**真的会挪焦点的
   注入对照**来判别 —— 这就是 b 探针存在的唯一理由。
7. **没测到的形态单列成不声称**：本协议对 2/6 浮层**根本没测到**焦点问题
   （被 D3 的 isEditable 早退遮住），对另 2 个**物理上不可能测**
   （触发器随导演台一起被卸载）。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"
REPO = HERE
for _ in range(12):                     # 向上找仓库根：**不数层数**，
    if (REPO / "package.json").exists() and (REPO / "src").is_dir():
        break                           # 找到才算，否则路径错到别处去
    REPO = REPO.parent
else:
    raise SystemExit("FATAL 找不到仓库根（package.json + src）")

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
MODES = ["inside", "trigger"]


def load(name, base=None):
    p = (base or RAW) / name
    if not p.exists():
        raise SystemExit("FATAL 缺原始读数 %s —— 判失败，不许通过" % p)
    return json.loads(p.read_text(encoding="utf-8")), p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm(o):
    if isinstance(o, str):
        return VOLATILE_RE.sub("<volatile>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in sorted(o.items())}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


def round_diff(raw, key):
    rs = raw.get("rounds") or []
    if len(rs) < 2:
        return None, "轮数不足 2"
    x, y = norm(rs[0].get(key)), norm(rs[1].get(key))
    if x == y:
        return True, None

    def walk(u, v, path=""):
        if isinstance(u, dict) and isinstance(v, dict):
            for k in sorted(set(u) | set(v)):
                if k not in u:
                    return "%s.%s 只在 round2" % (path, k)
                if k not in v:
                    return "%s.%s 只在 round1" % (path, k)
                r = walk(u[k], v[k], "%s.%s" % (path, k))
                if r:
                    return r
            return None
        if isinstance(u, list) and isinstance(v, list):
            if len(u) != len(v):
                return "%s 长度 %d vs %d" % (path, len(u), len(v))
            for i, (p_, q_) in enumerate(zip(u, v)):
                r = walk(p_, q_, "%s[%d]" % (path, i))
                if r:
                    return r
            return None
        return None if u == v else "%s: %r vs %r" % (path, u, v)

    return False, walk(x, y, key)


# ═══════════════ 1. 读原始读数 ═══════════════
a, a_p = load("vb768a.json")
b, b_p = load("vb768b.json")
aR, bR = a["rounds"], b["rounds"]
assert len(aR) == 2, "a 轮数 %d" % len(aR)
assert len(bR) == 2, "b 轮数 %d" % len(bR)

comparability = {
    "a": {"keys": ["rows"], "allConsistent":
          all(round_diff(a, k)[0] is True for k in ["rows"]),
          "firstDiff": {k: round_diff(a, k)[1] for k in ["rows"]
                        if round_diff(a, k)[0] is not True},
          "rounds": len(aR),
          "clearedLocalStorage": [(rd.get("cleared") or {}).get("removed")
                                  for rd in aR],
          "deskGoneAfter": [rd.get("deskGoneAfter") for rd in aR]},
    "b": {"keys": ["rows"], "allConsistent":
          all(round_diff(b, k)[0] is True for k in ["rows"]),
          "firstDiff": {k: round_diff(b, k)[1] for k in ["rows"]
                        if round_diff(b, k)[0] is not True},
          "rounds": len(bR),
          "clearedLocalStorage": [(rd.get("cleared") or {}).get("removed")
                                  for rd in bR]},
    "crossArm": "两个探针的 rows 逐格比对（a 无注入 / b 有注入）",
    "protocol": "★ **每个变体都从重新加载的页面开始**，全程**不点外点** —— "
                "767 的 R73：把两件事串在同一条时间线上会互相污染，"
                "而「先试着关掉再继续」也不行，因为「怎么关」本身是被测对象。"
                "全程只点 6 个 disclosure 触发器，其余是 `.focus()` 读操作与 Esc。",
    "note": "★ 注入探针 b 挂在 **window 捕获**阶段 —— 必须是捕获："
            "DirectorPhoneVcamPanel.tsx:294 的 Esc 监听就在捕获里 "
            "stopImmediatePropagation，冒泡阶段根本收不到 keydown。",
}
for k in ("a", "b"):
    assert comparability[k]["allConsistent"], \
        "%s 两轮不一致：%r" % (k, comparability[k]["firstDiff"])


def grid(raw):
    """(id, mode) -> 行；缺格即失败，不许当「没发生」。"""
    out = {}
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            out.setdefault((r.get("id"), r.get("mode")), []).append(r)
    missing = [k for k in [(i, m) for i in IDS for m in MODES] if k not in out]
    assert not missing, "缺格 %r —— 判失败，不许当「没发生」" % (missing,)
    for k, v in out.items():
        assert len(v) == 2, "%s 轮数 %d" % (k, len(v))
    return out


gA, gB = grid(a), grid(b)
failedA = sorted({"%s/%s" % k for k, v in gA.items()
                  for r in v if r.get("FAILED")})
failedB = sorted({"%s/%s" % k for k, v in gB.items()
                  for r in v if r.get("FAILED")})
assert not failedA, "a 有失败格 %r" % (failedA,)
assert not failedB, "b 有失败格 %r" % (failedB,)


# ═══════════════ 2. 逐格现算分类 ═══════════════
def classify(r, state_key="after"):
    """从「导演台还在吗 / 面板还在吗 / 焦点在哪」三件事现算分类。

    ★ 不采信探针自报的派生字段，只用原始 state 快照。
    """
    st = r.get(state_key) or {}
    de = r.get("desk") or {}
    if st.get("open") is False or de.get("open") is False:
        return "desk-lost"                       # 导演台整个没了
    if st.get("panelPresent") is True:
        return "panel-stuck"                     # 面板还在 ⟹ Esc 没生效
    if st.get("panelPresent") is not False:
        return "unknown"
    act = st.get("active") or {}
    if act.get("isTrigger") is True:
        return "closed-focus-on-trigger"
    if act.get("isBody") is True:
        return "closed-focus-on-body"
    if act.get("inDialog") is True:
        return "closed-focus-in-dialog"
    return "closed-focus-outside-dialog"


def cellA(r):
    fo = r.get("focus") or {}
    bf = (r.get("before") or {}).get("active") or {}
    return {
        "opened": (r.get("before") or {}).get("panelPresent") is True,
        "focusPlaced": fo.get("focused") is True,
        "focusedControl": {"tag": fo.get("tag"), "type": fo.get("type"),
                           "text": fo.get("text")},
        "panelFocusables": fo.get("total"),
        "focusWasInPanel": bf.get("inPanel") is True,
        "focusWasOnTrigger": bf.get("isTrigger") is True,
        "triggerAriaExpanded": (r.get("before") or {}).get(
            "triggerAriaExpanded"),
        "class": classify(r, "after"),
        "focusAfter": {"tag": ((r.get("after") or {}).get("active") or {}
                               ).get("tag"),
                       "isTrigger": ((r.get("after") or {}).get("active")
                                     or {}).get("isTrigger"),
                       "isBody": ((r.get("after") or {}).get("active")
                                  or {}).get("isBody"),
                       "inDialog": ((r.get("after") or {}).get("active")
                                    or {}).get("inDialog")},
    }


def cellB(r):
    c = cellA(r)
    a2 = r.get("after2") or {}
    # ★★ b 臂的 `after` 读数是**注入已经生效之后**的（注入在 keydown 后
    #   150ms 触发，而 `after` 在 750ms 才读）⟹ 它**不能**当基线用。
    #   所以本函数把来自 `after` 的分类改名为 `classInInjectedArm`，
    #   免得有人误拿它当「注入前」；基线一律取自 a 臂（tA）。
    c["classInInjectedArm"] = c.pop("class")
    c["injClass"] = classify(r, "after2")
    c["injFocusAfter"] = {"tag": (a2.get("active") or {}).get("tag"),
                          "isTrigger": (a2.get("active") or {}).get(
                              "isTrigger"),
                          "isBody": (a2.get("active") or {}).get("isBody"),
                          "inDialog": (a2.get("active") or {}).get("inDialog")}
    # 注入自己做了什么（这是动作记录，不是派生判断）。
    # ★ 注入**每格都留一条日志**（哪怕它判定「不该动手」），
    #   所以「日志非空」不等于「动了手」⟹ 只认 `focused` 这个键**在场**。
    log = r.get("inj") or []
    c["injLog"] = log
    c["injSetup"] = r.get("injSetup")
    c["injFocusCalled"] = any(rec.get("focused") is not None for rec in log)
    c["injSucceeded"] = any(rec.get("focused") is True for rec in log)
    return c


tA = {k: [cellA(r) for r in v] for k, v in gA.items()}
tB = {k: [cellB(r) for r in v] for k, v in gB.items()}

CLASSES = ["desk-lost", "panel-stuck", "closed-focus-on-trigger",
           "closed-focus-on-body", "closed-focus-in-dialog",
           "closed-focus-outside-dialog", "unknown"]
for k, v in tA.items():
    for c in v:
        assert c["class"] in CLASSES, "%s 分类 %r 不在枚举内" % (k, c["class"])
        assert c["opened"], "%s 起点不干净（浮层没打开）" % (k,)
        assert c["focusPlaced"], "%s 焦点没放进去" % (k,)
        if k[1] == "inside":
            assert c["focusWasInPanel"] is True, "%s 焦点不在浮层内" % (k,)
        else:
            assert c["focusWasOnTrigger"] is True, "%s 焦点不在触发器上" % (k,)

CELLS = [(i, m) for i in IDS for m in MODES]
allA = sorted({c["class"] for k in CELLS for c in tA[k]})
assert "unknown" not in allA, "有 unknown 分类 —— 判失败"


def both(k, fn):
    return all(fn(tA[k][r]) for r in range(2))


def ever(k, fn):
    return any(fn(tA[k][r]) for r in range(2))


deskLost = [k for k in CELLS if both(k, lambda c: c["class"] == "desk-lost")]
stuck = [k for k in CELLS if both(k, lambda c: c["class"] == "panel-stuck")]
onTrigger = [k for k in CELLS
             if both(k, lambda c: c["class"] == "closed-focus-on-trigger")]
onBody = [k for k in CELLS
          if both(k, lambda c: c["class"] == "closed-focus-on-body")]
assert not (set(deskLost) & set(stuck) & set(onTrigger) & set(onBody))
assert len(deskLost) + len(stuck) + len(onTrigger) + len(onBody) == 12, \
    "12 格的分类没有铺满：%r" % {
        "desk-lost": deskLost, "stuck": stuck, "on-trigger": onTrigger,
        "on-body": onBody}


def key2s(ks):
    return ["%s/%s" % k for k in ks]


# ── 「焦点归还」这一问的逐 disclosure 结论 ──
# 只有 inside 变体问的是「焦点在浮层内时，关闭后去哪」；
# trigger 变体量的是「焦点本来就不在浮层内」——那不是归还问题。
restore = {}
for i in IDS:
    k = (i, "inside")
    c = tA[k][0]
    kt = (i, "trigger")
    ct = tA[kt][0]
    if c["class"] == "panel-stuck":
        verdict = "unmeasured-d3-masks-it"
        why = "焦点落在浮层里第一个可聚焦控件上，而那个控件是输入框 ⟹ " \
              "DirectorDesk.tsx:487 的 isEditable 早退把 Esc 吞掉，" \
              "浮层根本没关 ⟹ 焦点还在原地，**焦点去向无从观察**"
    elif c["class"] == "desk-lost":
        verdict = "impossible-trigger-unmounted"
        why = "Esc 把整个导演台关掉了，触发器随之从 DOM 卸载 ⟹ " \
              "「归还焦点到触发器」**物理上不可能**（注入实测 trigThere=false）"
    elif c["class"] == "closed-focus-on-body":
        verdict = "measured-fails"
        why = "浮层确实关了，但焦点掉到 body，逃出对话框"
    else:
        verdict = "measured-passes"
        why = "浮层关了，焦点回到触发器"
    restore[i] = {
        "insideClass": c["class"],
        "insideVerdict": verdict,
        "insideWhy": why,
        "focusedControl": c["focusedControl"],
        "focusablesInPanel": c["panelFocusables"],
        "triggerVariantClass": ct["class"],
        # trigger 变体的「焦点在触发器上」是不是**平凡的**：
        # 判别式 = 焦点本来就在一个**没被卸载**的元素上
        #          且注入真的挪了焦点也不改变读数
        "triggerVariantIsVacuous": (
            ct["class"] == "closed-focus-on-trigger"
            and both(kt, lambda c: c["focusWasOnTrigger"])
            and both((i, "trigger"), lambda c: True)
            and all(tB[kt][r]["injFocusAfter"]["isTrigger"] is True
                    for r in range(2))
            and all(tB[kt][r]["injClass"] == "closed-focus-on-trigger"
                    for r in range(2))),
    }

measuredPass = [i for i in IDS if restore[i]["insideVerdict"] ==
                "measured-passes"]
measuredFail = [i for i in IDS if restore[i]["insideVerdict"] ==
                "measured-fails"]
unmeasured = [i for i in IDS if restore[i]["insideVerdict"] ==
              "unmeasured-d3-masks-it"]
impossible = [i for i in IDS if restore[i]["insideVerdict"] ==
              "impossible-trigger-unmounted"]
assert sorted(measuredPass + measuredFail + unmeasured + impossible) == \
    sorted(IDS), "逐 disclosure 的焦点结论没有铺满 6 个"
# 注入对照：只有「面板确实关了且触发器还在」两格才可能被注入改写
injectable = [k for k in onBody]
assert injectable == onBody, "注入只对 %r 生效" % (key2s(injectable),)
for k in onBody:
    assert all(tB[k][r]["injFocusAfter"]["isTrigger"] is True for r in range(2)), \
        "%s 注入后焦点没回触发器 ⟹ 不能声称「可避免」" % (k,)
    assert all(tB[k][r]["injClass"] == "closed-focus-on-trigger"
               for r in range(2)), "%s 注入后分类没变" % (k,)
# no-op 判别：trigger 变体那几格，注入前后读数必须**完全一样**
for i in IDS:
    kt = (i, "trigger")
    if restore[i]["triggerVariantClass"] == "closed-focus-on-trigger":
        assert restore[i]["triggerVariantIsVacuous"] is True, \
            "%s/trigger 的「焦点在触发器」不是平凡读数？" % i
noopConfirmed = [i for i in IDS
                 if restore[i]["triggerVariantIsVacuous"]]
assert sorted(noopConfirmed) == sorted(onTrigger and
                                      [k[0] for k in onTrigger]), \
    "no-op 确认集合与「焦点在触发器」的集合不一致：%r vs %r" % (
        noopConfirmed, [k[0] for k in onTrigger])

focusRestore = {
    "perDisclosure": restore,
    "implementedRestore": measuredPass,          # 期望为空
    "measuredAndFails": measuredFail,
    "unmeasuredBecauseD3": unmeasured,
    "impossibleBecauseTriggerUnmounted": impossible,
    "cells": {("%s/%s" % k): [tA[k][r] for r in range(2)] for k in CELLS},
    "denominatorNote": "分母是 6 个 disclosure。**4 个没被真正测到焦点问题**："
                       "2 个被 D3 遮住、2 个触发器已被卸载。",
}


# ═══════════════ 3. 注入对照 ═══════════════
injection = {
    "what": "在 window 捕获阶段监听 Escape，150ms 后若**该浮层已从 DOM 消失"
            "且触发器仍在 DOM 里**，就 trigger.focus()。",
    "whyCapture": "DirectorPhoneVcamPanel.tsx:294 在 window 捕获里 "
                  "stopImmediatePropagation()，冒泡阶段收不到 keydown。",
    "perCell": {("%s/%s" % k): {
        "baseClass": [tA[k][r]["class"] for r in range(2)],
        "injClass": [tB[k][r]["injClass"] for r in range(2)],
        "changed": [tA[k][r]["class"] != tB[k][r]["injClass"] for r in range(2)],
        "baseFocus": [tA[k][r]["focusAfter"] for r in range(2)],
        "injFocus": [tB[k][r]["injFocusAfter"] for r in range(2)],
        "injLog": [tB[k][r]["injLog"] for r in range(2)],
    } for k in CELLS},
    "cellsChangedByInjection": key2s([k for k in CELLS if any(
        tA[k][r]["class"] != tB[k][r]["injClass"] for r in range(2))]),
    "cellsInsensitiveToInjection": key2s([k for k in CELLS if all(
        tA[k][r]["class"] == tB[k][r]["injClass"] for r in range(2))]),
}
assert set(injection["cellsChangedByInjection"]) == set(key2s(onBody)), \
    "注入改动的格与预期不符：%r（预期 %r）" % (
        injection["cellsChangedByInjection"], key2s(onBody))
assert len(injection["cellsChangedByInjection"]) + \
    len(injection["cellsInsensitiveToInjection"]) == 12
# 注入在「面板没关」的格上必须**没调 focus**，否则会造出
# 「焦点逃出打开的浮层」的假象（R76）。用行为读数判，不只看日志。
for k in stuck:
    for r in range(2):
        assert tB[k][r]["injFocusCalled"] is False, \
            "%s 面板还开着，注入却调了 focus()" % (k,)
        assert tB[k][r]["injFocusAfter"] == tA[k][r]["focusAfter"], \
            "%s 面板还开着，注入却改了焦点读数：%r -> %r" % (
                k, tA[k][r]["focusAfter"], tB[k][r]["injFocusAfter"])
        assert tB[k][r]["injLog"] == [{"panelGone": False, "trigThere": True}], \
            "%s 注入日志异常：%r" % (k, tB[k][r]["injLog"])
# 触发器被卸载的格：注入必须**没能调用 focus**
for k in deskLost:
    for r in range(2):
        assert tB[k][r]["injFocusCalled"] is False, \
            "%s 导演台都没了，注入却调了 focus()" % (k,)
        assert tB[k][r]["injLog"] and \
            tB[k][r]["injLog"][0]["trigThere"] is False, \
            "%s 导演台都没了，注入日志却说触发器还在：%r" % (
                k, tB[k][r]["injLog"])
# 面板关了、触发器还在的格：注入必须调了且成功
for k in onBody + onTrigger:
    for r in range(2):
        assert tB[k][r]["injFocusCalled"] is True, \
            "%s 该注入却没调 focus()：%r" % (k, tB[k][r]["injLog"])
        assert tB[k][r]["injSucceeded"] is True, \
            "%s 注入调了 focus 但没成功：%r" % (k, tB[k][r]["injLog"])


# ═══════════════ 4. Esc 处理分类：当场读源码数出来 ═══════════════
# ★ 767 的 O3 断言「preset/pathmenu 也有捕获或冒泡阶段的 Esc 处理」，
#   与本批读数对不上：这两个浮层开着时按 Esc 会关掉整个导演台。
#   所以这一节不写死结论，而是把每处 addEventListener 的**阶段**与
#   **是否阻止传播**数出来，让读数和源码自己对上。
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s —— 判失败" % p)
    return p.read_text(encoding="utf-8")


WIN_KEYDOWN = re.compile(
    r'(window|document)\.addEventListener\(\s*"keydown"\s*,\s*(\w+)\s*'
    r'(?:,\s*(true|false))?\s*\)')
DESK = src_text("src/components/director/DirectorDesk.tsx")
TL = src_text("src/components/director/DirectorTimeline.tsx")
PV = src_text("src/components/director/DirectorPhoneVcamPanel.tsx")
VP = src_text("src/components/director/DirectorViewport.tsx")
LF = src_text("src/hooks/useLayerFocus.ts")

def fn_body(text, fn, span=3000):
    """取 `const <fn> = (…) => { … }` 的函数体（按花括号配对）。

    ★ 不能用「注册点往后看 N 个字符」—— 捕获阶段那几处的函数体
      **定义在注册点之前**（`DirectorViewport.tsx:2742` 定义、
      `:2748` 注册），往前看会**漏判 stopImmediatePropagation**，
      于是产物里的字段会和判据文字打架（第一版就踩了）。
    """
    m = re.search(r'const\s+' + re.escape(fn) + r'\s*=\s*\([^)]*\)\s*=>\s*\{',
                  text)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, min(len(text), i + span)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


listeners = []
for fname, text in (("DirectorDesk.tsx", DESK), ("DirectorTimeline.tsx", TL),
                    ("DirectorPhoneVcamPanel.tsx", PV),
                    ("DirectorViewport.tsx", VP)):
    for m in WIN_KEYDOWN.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        target, fn, capture = m.group(1), m.group(2), m.group(3) or "false"
        body = fn_body(text, fn)
        if body is None:
            raise SystemExit(
                "FATAL %s:%d 注册的 %s 找不到函数体 —— 正则失效，判失败"
                % (fname, line, fn))
        listeners.append({
            "file": fname, "line": line, "target": target, "fn": fn,
            "capture": capture == "true",
            "stopsPropagation": "stopImmediatePropagation()" in body
                                or "stopPropagation()" in body,
            "preventsDefault": "preventDefault()" in body,
            "bodyLine": text.count("\n", 0, m.start()) - body.count("\n")
                         + 1,
        })
assert listeners, "一个 keydown 监听都没数到 —— 正则失效，判失败"
captureList = [l for l in listeners if l["capture"]]
bubbleList = [l for l in listeners if not l["capture"]]
assert captureList and bubbleList, "阶段分布反常，判失败"
# 阶段与「是否停止传播」的组合，决定了同一个 keydown 会不会漏到导演台
combo = {"%s/%s" % (("capture" if l["capture"] else "bubble"),
                    "stops" if l["stopsPropagation"] else "leaks")
         for l in listeners}
assert combo == {"capture/stops", "bubble/leaks"}, \
    "keydown 监听出现了第三种组合 %r —— 机制结论要重查" % (combo,)

escTaxonomy = {
    "keydownListeners": listeners,
    "captureCount": len(captureList),
    "bubbleCount": len(bubbleList),
    "totalCount": len(listeners),
    # 阶段 × 是否停止传播 —— 只有两种组合，全仓没有第三种
    "combinations": sorted(combo),
    "preventsDefaultCount": sum(1 for l in listeners
                                 if l["preventsDefault"]),
    "captureStopsAll": ["%s:%d" % (l["file"], l["line"]) for l in captureList
                        if l["stopsPropagation"]],
    "bubbleStopsAny": ["%s:%d" % (l["file"], l["line"]) for l in bubbleList
                       if l["stopsPropagation"]],
    # 导演台的 Esc 阶梯里对另外五个浮层状态的引用数
    "deskLadderReferencesOtherPanels": len(re.findall(
        r"crowdPanelOpen|modelLibraryOpen|phoneVcamOpen|presetPanelLeft|"
        r"pathMenuLeft", DESK)),
    "deskLadderHasExportTier": len(re.findall(
        r"if \(exportPanelOpen\)", DESK)),
    "deskLadderHasCaptureFlag": any(
        l["file"] == "DirectorDesk.tsx" and l["capture"] for l in listeners),
    "useLayerFocusReturnsToOpener": "opener.focus()" in LF,
    "useLayerFocusIsConnectedGuard": "root.isConnected" in LF,
    "useLayerFocusConsumers": sorted(
        p.name for p in (REPO / "src").rglob("*.tsx")
        if "useLayerFocus(ref" in p.read_text(encoding="utf-8")
        or "useLayerFocus(panelRef" in p.read_text(encoding="utf-8")),
    "directorUsesUseLayerFocus": any(
        "useLayerFocus" in p.read_text(encoding="utf-8")
        for p in (REPO / "src/components/director").rglob("*.tsx")),
}
assert escTaxonomy["deskLadderReferencesOtherPanels"] == 0, \
    "导演台 Esc 阶梯居然引用了别的浮层状态，静态结论要重查"
assert escTaxonomy["deskLadderHasExportTier"] == 1, \
    "导演台 Esc 阶梯里导出面板那档的份数变了：%d" % \
    escTaxonomy["deskLadderHasExportTier"]
assert escTaxonomy["deskLadderHasCaptureFlag"] is False, \
    "导演台自己的 keydown 变成捕获阶段了，机制结论要重查"
assert escTaxonomy["bubbleStopsAny"] == [], \
    "竟有冒泡阶段的处理器阻止了传播，机制结论要重查：%r" % \
    (escTaxonomy["bubbleStopsAny"],)
assert escTaxonomy["captureStopsAll"] and \
    len(escTaxonomy["captureStopsAll"]) == escTaxonomy["captureCount"], \
    "捕获阶段有一处没停止传播，机制结论要重查"
assert escTaxonomy["combinations"] == ["bubble/leaks", "capture/stops"], \
    "keydown 监听的组合变了：%r" % (escTaxonomy["combinations"],)
assert escTaxonomy["useLayerFocusReturnsToOpener"] is True, \
    "useLayerFocus 里的 opener.focus() 不见了，修法依据要重查"
assert escTaxonomy["useLayerFocusIsConnectedGuard"] is True
assert escTaxonomy["directorUsesUseLayerFocus"] is False, \
    "导演台开始用 useLayerFocus 了，D11 的修法依据要重查"
assert escTaxonomy["useLayerFocusConsumers"], "useLayerFocus 消费者读数异常"
assert not any("director" in n.lower() for n in
               escTaxonomy["useLayerFocusConsumers"])


# ═══════════════ 5. 跨批交叉核对：可聚焦控件数 ═══════════════
prev_dir = BATCH.parent / "liblib-canvas-batch767-2026-10-01"
prev, prev_p = load("vb767a.json", base=prev_dir / "raw")
prev_focus = {}
for rd in prev["rounds"]:
    for r in rd.get("results") or []:
        prev_focus.setdefault(r.get("id"), set()).add(
            (r.get("afterOpen") or {}).get("panelFocusables"))
this_focus = {i: sorted({tA[(i, "inside")][r]["panelFocusables"]
                         for r in range(2)}) for i in IDS}
crossBatch = {
    "source": "batch767 raw/vb767a.json 的 panelFocusables vs "
              "batch768 raw/vb768a.json 的 focus.total",
    "perId": {i: {"batch767": sorted(x for x in prev_focus.get(i, [])
                                     if x is not None),
                  "batch768": this_focus[i],
                  "agree": sorted(x for x in prev_focus.get(i, [])
                                  if x is not None) == this_focus[i]}
              for i in IDS},
}
assert crossBatch["perId"]["export"]["batch767"], \
    "767 的可聚焦控件数没读到，跨批核对判失败"
assert all(v["agree"] for v in crossBatch["perId"].values()), \
    "跨批可聚焦控件数不一致：%r" % {i: v for i, v
                                  in crossBatch["perId"].items()
                                  if not v["agree"]}

# 767 的 pathmenu 触发器 aria-expanded 是不是 null（768 再验一次 J10）
prev_expanded = {r.get("id"): (r.get("afterOpen") or {}).get(
    "triggerAriaExpanded") for r in prev["rounds"][0]["results"]}
crossBatch["ariaExpandedIn767"] = prev_expanded
crossBatch["ariaExpandedIn768"] = {i: tA[(i, "trigger")][0]["triggerAriaExpanded"]
                                   for i in IDS}
assert crossBatch["ariaExpandedIn768"]["pathmenu"] is None, \
    "768 量到 pathmenu 触发器有 aria-expanded 了，J10 的更正要重写"
assert crossBatch["ariaExpandedIn768"]["export"] == "true"
n_expanded = sum(1 for i in IDS
                 if crossBatch["ariaExpandedIn768"][i] is not None)
crossBatch["withAriaExpanded"] = n_expanded
crossBatch["withAriaPressedOnly"] = [i for i in IDS
                                    if crossBatch["ariaExpandedIn768"][i]
                                    is None]
assert n_expanded == 5 and crossBatch["withAriaPressedOnly"] == ["pathmenu"], \
    "带 aria-expanded 的触发器份数变了：%d 个有、%r 没有" % (
        n_expanded, crossBatch["withAriaPressedOnly"])


# ═══════════════ 6. 判据 ═══════════════
findings = {
    "comparability": comparability,
    "focusRestore": focusRestore,
    "injectionContrast": injection,
    "escTaxonomy": escTaxonomy,
    "crossBatch": crossBatch,
}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "**两轮逐字段一致**（a、b 各自的 `rows` 整棵树归一化 diff "
                  "为空），且先证明可比：本批**不点外点**，每个变体都从"
                  "**重新加载页面**开始 ⟹ 12 格的起点互不干扰"
                  "（767 的 R73：把两件事串在同一条时间线上会互相污染）。"
                  "另外 b 的两轮 localStorage 各清掉一份上一轮遗留的"
                  "导演台项目，a 的第一轮清掉 0 份 —— 读数仍然一致，"
                  "说明清理确实在起作用。",
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "**12 格全部拿到读数**，没有一格 FAILED：6 个 disclosure "
                  "× 2 个变体，起点都验过（浮层确实开着、焦点确实放到了"
                  "该放的地方），并按「导演台还在吗 / 面板还在吗 / "
                  "焦点在哪」三件事现算分类，12 格**恰好铺满**四个分类。",
     "evidenceKey": "focusRestore"},
    {"id": "J3", "verdict": "FAIL",
     "statement": "★ **缺陷 D11（低）：6 个 disclosure 里没有任何一个"
                  "在关闭后把焦点归还触发器。** 真正测到的 2 个"
                  "（虚拟相机、模型库）**都是把焦点丢到 `body`** —— "
                  "逃出对话框，键盘用户下一次 Tab 会从文档开头重新开始。"
                  "另 4 个不是「做对了」：2 个被 D3 遮住根本没测到，"
                  "2 个的触发器随整个导演台一起被卸载、**物理上不可能**归还。",
     "evidenceKey": "focusRestore"},
    {"id": "J4", "verdict": "PASS",
     "statement": "★ **「掉到 `body`」是可避免的，不是必然**：注入对照"
                  "（在浮层确实关闭后 `trigger.focus()`）把"
                  "虚拟相机/模型库这两格从 `body` 变成**触发器**，"
                  "2/2 轮。也就是说缺陷只差「关掉之后挪一下焦点」这一步 —— "
                  "**注入改动的恰好且仅有这两格**，其余 10 格读数不变。",
     "evidenceKey": "injectionContrast"},
    {"id": "J5", "verdict": "PASS",
     "statement": "★ **探针自己摘要里的「焦点回触发器 ✓」是 no-op，已撤回**："
                  "触发器变体那 3 格（导出/虚拟相机/模型库）在按 Esc 之前"
                  "焦点**本来就在触发器上**，而触发器**没有被卸载** ⟹ "
                  "「焦点还在触发器上」是浏览器默认行为，**不需要任何实现**。"
                  "注入对照证实了这一点：真的去调 `focus()` 也不改变这三格读数 ⟹ "
                  "该读数对「有没有归还焦点」**完全不敏感**，不能拿来当通过。",
     "evidenceKey": "injectionContrast"},
    {"id": "J6", "verdict": "FAIL",
     "statement": "★ **缺陷 D8 从 1/6 扩到 3/6（中）**：767 判「添加群众阵列"
                  "按 Esc 关掉整个导演台」，并把另外两个的 Esc 行为"
                  "明确列进「不声称」（因为它们已被外点那一下关掉了）。"
                  "本批补上那两个读数：**预设运镜与创建运动轨迹同样会"
                  "关掉整个导演台**。5/12 格按 Esc 后导演台消失 ⟹ "
                  "半族浮层都有「按 Esc 丢整个工作区」的路径。",
     "evidenceKey": "focusRestore"},
    {"id": "J7", "verdict": "FAIL",
     "statement": "★ **D8 的机制不是一个，是两个，修法也不同** —— 这一条"
                  "**更正 767 的 O3**。"
                  "①群众阵列**根本没有自己的 Esc 处理**，也不在导演台"
                  "阶梯里 ⟹ Esc 一路落到 `closeWorkspace()`；"
                  "②预设运镜与路径菜单**有** Esc 处理"
                  "（`DirectorTimeline.tsx:570/594`），但它挂在 window "
                  "**冒泡**阶段且**既不 `preventDefault()` 也不停止传播** ⟹ "
                  "导演台自己那个同样挂在 window 冒泡阶段的处理器"
                  "（`DirectorDesk.tsx:570`）**照样会跑** ⟹ "
                  "无论两个处理器谁先注册，`closeWorkspace()` 都必然执行。"
                  "767 以为「有 Esc 处理」就够 —— 读数证明不够。",
     "evidenceKey": "escTaxonomy"},
    {"id": "J8", "verdict": "PASS",
     "statement": "**同仓已有做对了的样本，而且它的注释里逐字写着本批的"
                  "症状**：模型库面板（`DirectorViewport.tsx:2748`）的 Esc "
                  "监听是 window **捕获** + `preventDefault()` + "
                  "`stopImmediatePropagation()` ⟹ 事件到不了导演台阶梯，"
                  "所以它只关自己（实测面板关、导演台还在）。"
                  "虚拟相机面板（`DirectorPhoneVcamPanel.tsx:294`）同一招。"
                  "全仓共 %d 处 keydown 监听，其中 %d 处是捕获阶段、"
                  "**冒泡阶段里一处停止传播的都没有**。"
                  % (escTaxonomy["captureCount"] + escTaxonomy["bubbleCount"],
                     escTaxonomy["captureCount"]),
     "evidenceKey": "escTaxonomy"},
    {"id": "J9", "verdict": "FAIL",
     "statement": "★ **缺陷 D3 从 1/6 扩到 2/6（低）**：按 Esc 时焦点落在"
                  "浮层里**第一个可聚焦控件**上，若那是输入框，"
                  "`DirectorDesk.tsx:487` 的 `isEditable` 早退就把 Esc 吞掉、"
                  "**浮层根本不关** —— 导出面板（时长数值框）与"
                  "添加群众阵列面板各命中一次。这也**反过来遮住了本批的"
                  "焦点问题**：这两个浮层恰恰因为「没关」而观察不到焦点去向。",
     "evidenceKey": "focusRestore"},
    {"id": "J10", "verdict": "FAIL",
     "statement": "★ **方法论限制单列（不声称）**：「把焦点放进浮层的"
                  "第一个可聚焦控件」**不是通用的焦点探针** —— "
                  "6 个浮层里有 2 个的第一个可聚焦控件是输入框，"
                  "于是 D3 先发作、把焦点去向整个遮住。注入也救不了："
                  "注入只在「面板确实关了」时才动手。要测到这两个浮层的"
                  "焦点契约，必须**指定一个非输入框的控件**"
                  "（例如导出面板的画幅按钮）。",
     "evidenceKey": "focusRestore"},
    {"id": "J11", "verdict": "PASS",
     "statement": "★ **跨批交叉核对通过**：6 个浮层的**可聚焦控件数**在"
                  "768 与 767 两批独立读数里**逐个相同**"
                  "（导出 5 / 预设 10 / 路径菜单 5 / 虚拟相机 2 / "
                  "群众 5 / 模型库 15）—— 两批用的是不同探针、"
                  "不同轮次、不同代码路径，这是真的一致而不是抄的。",
     "evidenceKey": "crossBatch"},
    {"id": "J12", "verdict": "FAIL",
     "statement": "★ **更正 767 的范围表述**：767 的标题与台账都写"
                  "「导演台 **6 个带 `aria-expanded` 的** disclosure」，"
                  "但本批两个变体都读到 `pathmenu` 触发器的 "
                  "`aria-expanded` 是 `null`（只有 `aria-pressed`）⟹ "
                  "**实际是 5 个带 `aria-expanded` + 1 个只有 "
                  "`aria-pressed`**。767 自己的 J10 已经发现这一点却没回头"
                  "改范围表述。缺陷计数不受影响（路径菜单确实是个浮层），"
                  "但「6 个带 aria-expanded」这句话不成立。",
     "evidenceKey": "crossBatch"},
    {"id": "J13", "verdict": "PASS",
     "statement": "**没点任何有副作用的控件**：只点了 6 个 disclosure 触发器"
                  "（导出面板的提交、虚拟相机的「连接」、模型库的添加"
                  "都没点），其余全是 `.focus()` 读操作与 `Escape` —— "
                  "`focus()` 不触发任何业务动作。",
     "evidenceKey": "comparability"},
    {"id": "J14", "verdict": "PASS",
     "statement": "★ **D11 的修法有现成的、且踩过坑的实现** —— "
                  "`src/hooks/useLayerFocus.ts` 的 cleanup 段"
                  "（记住 opener、卸载时用 `requestAnimationFrame` 归还焦点，"
                  "并用 `root.isConnected` 守卫区分「真关闭」与「假卸载」），"
                  "**注释里逐字写着「实测表现就是『点外面关掉浮层，"
                  "焦点掉到 body』」**。消费者只有即梦的 %s 两个组件，"
                  "**导演台一个都没用**。"
                  % "、".join(escTaxonomy["useLayerFocusConsumers"]),
     "evidenceKey": "escTaxonomy"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]


# ═══════════════ 7. 缺陷 / 观察 / 不声称 / 教训 ═══════════════
audit = {
    "batch": 768,
    "date": "2026-10-01",
    "scope": "补 767 的 J9：6 个导演台 disclosure 浮层的**焦点归还契约**"
             "（焦点在浮层内时按 Esc，关闭之后焦点去哪），"
             "附一条**注入对照**用来把「掉到 body」与"
             "「本来就在触发器上所以没动」分开",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewport": "1440x1000（桌面）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "768a", "file": "probes/dbg768a.py", "raw": "raw/vb768a.json",
         "rounds": len(aR), "injected": False,
         "note": "基线：两个变体各从**重载页面**开始，全程不点外点"},
        {"id": "768b", "file": "probes/dbg768b.py", "raw": "raw/vb768b.json",
         "rounds": len(bR), "injected": True,
         "note": "与 a 同协议，额外注入「浮层关闭后 trigger.focus()」；"
                 "注入挂在 window 捕获阶段（冒泡阶段收不到手机相机"
                 "那个 stopImmediatePropagation）"},
    ],
    "rawSha": {a_p.name: sha(a_p), b_p.name: sha(b_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D11", "severity": "低", "newInThisBatch": True,
         "widensD4From765": True,
         "title": "6 个 disclosure 浮层没有一个在关闭后把焦点归还触发器",
         "where": ["src/components/director/DirectorExportPanel.tsx:38",
                   "src/components/director/DirectorPhoneVcamPanel.tsx:286-296",
                   "src/components/director/DirectorViewport.tsx:2734-2753",
                   "src/components/director/DirectorDesk.tsx:557-560"],
         "mechanism": "6 个浮层的关闭路径里没有一处把焦点交还给触发器。"
                      "765 的 D4 已在导出面板上量到「关闭后焦点掉到 body」"
                      "（`DirectorExportPanel.tsx:38` 的 `if (!open) return null` "
                      "把正在聚焦的元素整个卸载，而 `DirectorDesk.tsx:557-560` "
                      "那一档不碰焦点）。本批把同一机制在**虚拟相机面板**与"
                      "**模型库面板**上也量到 ⟹ 不是导出面板的个案。",
         "measured": "真正测到焦点去向的 2 个浮层（虚拟相机、模型库）"
                     "**都掉到 `body`**，2/2 轮；4/6 的 disclosure "
                     "根本没测到（2 个被 D3 遮住、2 个触发器已被卸载）。"
                     "注入对照：加上「关闭后 focus 回触发器」后这 2 格"
                     "变成正确读数 ⟹ 可避免。",
         "severityRationale": "**低**（与 765 的 D4 同级）：焦点丢到 body "
                              "不会丢数据，但键盘用户关掉浮层后要"
                              "从文档开头重新 Tab 一遍。之所以仍单列一条，"
                              "是因为「0/6 做对」是**全族**结论，"
                              "而 765 只在 1 个浮层上看到过。",
         "inRepoExemplar": "`src/hooks/useLayerFocus.ts` 的 cleanup 段"
                           "（`opener.focus()` + `requestAnimationFrame` + "
                           "`root.isConnected` 守卫）就是标准答案，"
                           "而且那段注释**逐字写着本批的症状**："
                           "「实测表现就是『点外面关掉浮层，焦点掉到 body』」。"
                           "它的消费者只有即梦的 JimengNodeSummaryPopover "
                           "与 JimengAiDrawer，**导演台一个都没接**。",
         "needsSrcChange": True},
    ],
    "widened": [
        {"id": "D8", "from": "1/6", "to": "3/6", "severity": "中",
         "title": "6 个浮层里 3 个的 Esc 会关掉整个导演台（767 只判了群众阵列）",
         "newMembers": ["preset", "pathmenu"],
         "mechanismSplit": {
             "crowd": "**没有**自己的 Esc 处理，也不在导演台阶梯里 ⟹ "
                      "Esc 一路落到 `closeWorkspace()`",
             "preset/pathmenu": "**有** Esc 处理（`DirectorTimeline.tsx:"
                                "570/594`），但挂在 window **冒泡**阶段"
                                "且既不 `preventDefault()` 也不停止传播 ⟹ "
                                "导演台自己那个同样在 window 冒泡阶段的"
                                "处理器（`DirectorDesk.tsx:570`）照样执行 ⟹ "
                                "**与注册顺序无关**，`closeWorkspace()` 必然跑",
         },
         "measured": "5/12 格按 Esc 后导演台 `open=false`："
                     "preset/inside、preset/trigger、pathmenu/inside、"
                     "pathmenu/trigger、crowd/trigger（2/2 轮）。",
         "correctsBatch767": "O3「Esc 的两种正确实现方式在同仓并存」暗示"
                             "「有 Esc 处理」就够了；读数证明**不够**，"
                             "必须同时是捕获阶段 + 停止传播。",
         "fixDirection": "两条路，按机制分别选："
                          "①给阶梯加档（`exportPanelOpen` `:557` 那样）"
                          "—— 但这治不了 ②类；"
                          "②把 `DirectorTimeline.tsx:570/594` 改成"
                          "模型库面板那样：window 捕获 + `preventDefault()` + "
                          "`stopImmediatePropagation()`。**两类都要用 ②**。",
         "needsSrcChange": True},
        {"id": "D3", "from": "1/6", "to": "2/6", "severity": "低",
         "title": "焦点在浮层内的输入框时，Esc 关不掉浮层"
                  "（`DirectorDesk.tsx:487` 的 isEditable 早退）",
         "newMembers": ["crowd"],
         "measured": "export/inside 与 crowd/inside：焦点落在浮层里第一个"
                     "可聚焦控件（都是 `INPUT[type=number]`）时按 Esc，"
                     "**浮层仍然开着**（`panelPresent=true`、"
                     "`aria-expanded` 仍为 `true`），2/2 轮。",
         "compositionNote": "★ **两个缺陷会叠在一起**：群众阵列面板此刻"
                            "之所以没丢工作区，**恰恰是因为 isEditable "
                            "早退把 Esc 吞了**；一旦按 J7 给它补上 Esc 处理"
                            "或按 765 拍板给 isEditable 开特例，这条防线就没了 "
                            "—— 修 D3 的同时必须先修 D8。",
         "needsSrcChange": True},
        {"id": "D4", "from": "1/6", "to": "3/6", "severity": "低",
         "title": "关闭浮层后焦点掉到 body（与 D11 同一机制）",
         "newMembers": ["phonevcam", "modellib"],
         "note": "本批新增的两例都是「浮层确实关了、导演台还在、"
                 "但焦点掉到 body」。导出面板那一例（765）在本批被 D3 "
                 "遮住没重测到 —— 不影响结论，两批的机制已对齐（见 D11）。",
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "★ **触发器变体那 3 个「焦点在触发器上」是平凡读数**。"
                 "按 Esc 之前焦点就在触发器上，触发器在按 Esc 之后"
                 "**仍在 DOM 里**（实测 `triggerPresent=true`）⟹ "
                 "浏览器默认就保住焦点，**不需要任何代码**。"
                 "本批探针自己的摘要一度把它打印成「焦点回触发器 ✓」，"
                 "那是**错的措辞**，已撤回（见 J5）。"
                 "这一条是本批的方法论核心：**读数说「焦点在哪」"
                 "不足以说明「有人把它放到了那儿」。**",
         "verdict": "方法论记录"},
        {"id": "O2",
         "text": "★ **注入对照的读法**：注入只在「浮层确实从 DOM 消失、"
                 "且触发器还在」时才动手。这让注入在三类格上给出三种读数 —— "
                 "改写（面板关、焦点掉 body 的 2 格）、"
                 "不动（面板还开着的 2 格，注入日志 `panelGone=false`）、"
                 "**动手失败**（导演台都没了的 5 格，日志 `trigThere=false`）"
                 "⟹ 「归还焦点」在这些格上**物理上不可能**。"
                 "这三种读数互不重叠，合计 12 格。",
         "verdict": "方法论记录"},
        {"id": "O3",
         "text": "**全仓 keydown 监听的阶段分布**：共 %d 处（导演台组件内），"
                 "捕获阶段 %d 处、冒泡阶段 %d 处；**冒泡阶段里一处"
                 "停止传播的都没有**。这解释了为什么「关面板而不关导演台」"
                 "在同仓有两种能work的写法（导演台阶梯加档 / "
                 "捕获+停止传播），而第三种写法（冒泡+不停止）"
                 "**必然漏到导演台**。"
                 % (escTaxonomy["captureCount"] + escTaxonomy["bubbleCount"],
                    escTaxonomy["captureCount"], escTaxonomy["bubbleCount"]),
         "verdict": "事实记录"},
        {"id": "O4",
         "text": "**「一个症状不一定是同一个机制」在本批再次成立**"
                 "（R60 的第二次）：D8 的两种机制（没有 Esc 处理 / "
                 "有 Esc 处理但不停止传播）修法不同 —— 前者补一档阶梯，"
                 "后者必须改成捕获+停止传播。只按症状去修，"
                 "会把 2/3 的成员修错。",
         "verdict": "方法论记录"},
        {"id": "O5",
         "text": "★ **上一轮留下的一份持久化痕迹被本轮抓到了**：b 探针第 1 轮"
                 "开头清 localStorage 清掉 **0** 份，第 2 轮清掉 **1** 份 "
                 "（`liblib-tv-director-project-v1:%5B%22libtv%22%2C%22canvas-2"
                 "%22%5D`）⟹ 第 1 轮 12 格的准备动作（开导演台、点相机对象）"
                 "在 localStorage 里留下了一份项目。两轮读数仍然一致，"
                 "说明**每轮开头的清理确实在起作用**（763 的 O1）。",
         "verdict": "事实记录（也是每轮清理的正当性证据）"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "★ **导出面板与添加群众阵列面板的焦点归还契约本批没有测到**"
        "（J10）：协议是「把焦点放进浮层的第一个可聚焦控件」，"
        "而这两个浮层的第一个可聚焦控件是输入框 ⟹ D3 先发作、浮层没关 ⟹ "
        "焦点还在原地。**注入也救不了**（注入只在面板真关时才动手）。"
        "要测到得指定一个非输入框的控件（例如导出面板的画幅按钮）。",
        "★ **预设运镜与创建运动轨迹的焦点归还契约无法在本协议下测**："
        "Esc 会把整个导演台关掉、触发器随之卸载 ⟹ 没有可归还的对象。"
        "这条必须**先修 D8** 再测，否则没有测的对象。",
        "**「触发器变体」不能用来回答归还问题**（O1）：它量的是"
        "「焦点本来就不在浮层内」时的行为。",
        "**没有测 6 个浮层里的 Tab 围栏**（765 只量过导出面板与对话框级）。",
        "**没有测打开状态下再点一次触发器**（toggle 关闭 vs 报错）。",
        "**没有测多个浮层同时开着会怎样** —— 每格都从重载页面开始，"
        "永远只有一个浮层开着。",
        "**没有测虚拟相机在录制中的 Esc**"
        "（`DirectorPhoneVcamPanel.tsx:292` 有 `if (!recording) onClose()`）。",
        "**只测了 1440 桌面一档视口**。",
        "**没有改 `src/`**：本批所有结论都是读数 + 源码计数，"
        "修法一律列在缺陷条目里等拍板。",
    ],
    "probeLessons": [
        {"id": "R75",
         "text": "★ **「读数说焦点在某元素上」≠「有人把它放到了那儿」。** "
                 "本批探针的摘要一度把 3 格打印成「焦点回触发器 ✓」，"
                 "看着像通过；实际那 3 格按 Esc 之前焦点**就在触发器上**，"
                 "而触发器没被卸载 ⟹ 焦点不变是浏览器默认行为。"
                 "**判别式只有一条：注入一条「真的会挪焦点」的对照，"
                 "看那一格的读数变不变。** 变了 ⟹ 那格原来量的是行为；"
                 "不变 ⟹ 那一格对被测行为**不敏感**，不能当证据。",
         "whyItMatters": "这条会让「0 个做对」被误报成「5 个做对」—— "
                         "而且是**朝着通过的方向**误报，比漏报更危险。"},
        {"id": "R76",
         "text": "★ **注入的落点要与「面板真的关了」绑定，否则会造假象。** "
                 "若注入无条件 `trigger.focus()`，则在「面板还开着」"
                 "的 2 格上会把焦点从浮层里拽到浮层外 ⟹ 凭空造出"
                 "「焦点逃出打开的浮层」这个新症状。"
                 "本批把动作条件写成「`panelGone && trigThere`」，"
                 "于是 12 格分成改写 / 不动 / 动手失败三类，"
                 "合计正好 12，互不重叠。",
         "whyItMatters": "注入是为了**补一个对照**，不是为了造一个现象。"},
        {"id": "R77",
         "text": "★ **改探针的批量生成脚本时，别在原文里再放一组三引号。** "
                 "我用脚本给探针换 docstring，把新说明插在原文的 `docstring` "
                 "**之前**，结果新插入的文本里那个 `docstring` "
                 "把原文的开头提前闭合 ⟹ 剩下的正文全部被当成 Python 代码，"
                 "生成出来就是语法错的探针。"
                 "教训：批量改脚本之后必须对产物跑 `ast.parse` —— "
                 "R77 与 jscheck 是同一类问题的两个层次。",
         "whyItMatters": "生成器出错的症状出现在产物里，离错误现场很远。"},
        {"id": "R78",
         "text": "★ **jscheck 兑现了它的承诺，省下一次 10 分钟白跑**："
                 "我写的注入 JS 里 `sel.forEach(s)=>{` 少了个 `>`"
                 "（两处）—— 一眼可见、但要起浏览器、跑十几秒"
                 "才在日志末尾看到 `SyntaxError`。jscheck 在 0.1 秒内"
                 "把它连同覆盖率自检一起报了出来。"
                 "与 R71 那个「`in` 用在字符串上」对照着看："
                 "**语法错 jscheck 能抓，语义错只能靠真跑，"
                 "判读错只能靠对照** —— 三个层次，各管一段。",
         "whyItMatters": "R71 曾让我以为 jscheck 是万能的；这次正好"
                         "划清了它的边界。"},
        {"id": "R79",
         "text": "★ **泛化探针要先问「我要点的那个控件会不会触发别的缺陷」。** "
                 "「把焦点放进浮层的第一个可聚焦控件」在 6 个浮层里对 4 个"
                 "是有效的、对 2 个无效 —— 因为那 2 个的第一个控件是输入框，"
                 "会先撞上 D3（`isEditable` 早退）把被测行为整个遮住。"
                 "选探针目标元素时，**要先确认它对被测行为是惰性的**"
                 "（R59/R74 的同族：先量可点性，再点）。",
         "whyItMatters": "它造成的不是「读错」，是「**读不到**」—— "
                         "而读不到很容易被当成「没问题」。"},
        {"id": "R80",
         "text": "★ **注入臂里那个叫 `after` 的读数，其实已经是注入后的状态。** "
                 "注入在 keydown 之后 150ms 触发，而 `after` 在 750ms 才读 ⟹ "
                 "基线**只能取自未注入的那一臂**（a）。汇编器因此把 b 臂里"
                 "来自 `after` 的分类改名成 `classInInjectedArm`，"
                 "免得有人拿它当「注入前」。"
                 "这条是我在做**阴性对照**时撞出来的：我写了一条对照"
                 "「把 `after2` 覆盖成 b 自己的 `after`，模拟注入没生效」，"
                 "结果它**永远漏放**——因为两者本来就相等。",
         "whyItMatters": "★ **无效的阴性对照不会报错，它只会永远「漏放」。** "
                         "所以「某条对照漏放」要当成**待查的事实**去查，"
                         "第一反应不该是「这条对照不重要」或「补个检查就行」—— "
                         "得先问「这条对照本身是不是根本没改动任何东西」。"},
    ],
}

for j in audit["judgments"]:
    k = j["evidenceKey"]
    assert k in findings, "判据 %s 引用了不存在的 findings 键" % j["id"]
    assert findings[k] == j["evidence"], (
        "判据 %s 的 evidence 与 findings[%s] 不相等" % (j["id"], k))

OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("wrote %s" % OUT)
print("判据 %d 条（PASS %d / FAIL %d）| findings %d 键 | 新缺陷 %d | "
      "扩宽 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["widened"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("焦点归还：实现=%r 测到且错=%r 被 D3 遮住=%r 触发器已卸载=%r"
      % (measuredPass, measuredFail, unmeasured, impossible))
print("注入改动的格：%r｜注入不改变读数的格：%d 格"
      % (injection["cellsChangedByInjection"],
         len(injection["cellsInsensitiveToInjection"])))
print("Esc 阶梯引用别的浮层状态 %d 处｜冒泡阶段的 keydown 监听 %d 处，"
      "其中停止传播 %d 处"
      % (escTaxonomy["deskLadderReferencesOtherPanels"],
         escTaxonomy["bubbleCount"], len(escTaxonomy["bubbleStopsAny"])))
