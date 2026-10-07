"""batch 770 验收器：6 个 disclosure 浮层里的 Tab 围栏

三层结构（与 753–769 同）：
  1. **静态层** —— 从 `src/` 独立复核围栏机制：挂在 root（对话框）上、
     数组按 root 取、正反都环绕、Tab 时 `preventDefault`、
     **没有 focusin/focusout 监听**（769 的 D11 修法未落地），
     以及「哪些浮层声明了 `role="dialog"`」
  2. **产物层** —— 判据条数与 verdict、缺陷、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb770a.json` **重算**逐格路径、
     逃逸步数与公式的吻合、段内下标的单调性（**方向要跟着行进方向**）、
     三分类的铺满；缺失时**判失败而不是通过**

⚠ 本批盯住五件容易自欺的事：
  - **「逃出」的参照系**：765 记的「0 逃出」相对**对话框**、本批相对
    **浮层**，两者同时为真。产物必须写清参照系，不许含糊成
    「本批推翻了 765」。
  - **不许把「12 步没走出去」当成围栏好**（J10）：那格是模型库正向，
    公式预测第 14 步出去。判据要**单独**把「步数不够」这一格挑出来。
  - **逃逸步数必须与公式吻合**：判据要从 raw 重算公式值并逐格比，
    不许只信产物里那句「11/11 吻合」。
  - **段内下标的单调性检查必须跟着行进方向**（R89）：写死 +1 会把
    Shift+Tab 的合法数据判成「不连续」。这条要在验收器里独立做一遍。
  - **`all([])` 是 True**：三分类必须**铺满 12 格**；「没有焦点离开过
    对话框」这条（`leftTheDialog == []`）**不许**被当成「没测」。

判据 **10 条（6 PASS / 4 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch770-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb770a.json"]
PROBE_FILES = ["dbg770a.py", "mk770audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
DIRS = ["fwd", "back"]
CELLS = [(i, d) for i in IDS for d in DIRS]
EXPECT_FAIL_IDS = ["J5", "J6", "J8", "J10"]
EXPECT_PASS_IDS = ["J1", "J2", "J3", "J4", "J7", "J9"]
EXPECT_LESSON_IDS = ["R87", "R88", "R89"]
SEL = {"export": "export", "preset": "camera-preset",
       "pathmenu": "motion-path-menu", "phonevcam": "phone-vcam",
       "crowd": "crowd", "modellib": "model-library"}


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def ptr_valid(w):
    m = re.match(r"^(.+?):(\d+)(?:-(\d+))?$", w or "")
    if not m:
        return False
    f = ROOT / m.group(1)
    if not f.exists():
        return False
    n = len(f.read_text(encoding="utf-8").splitlines())
    hi = int(m.group(3) or m.group(2))
    return int(m.group(2)) <= n and hi <= n


# ═════════════════════ 1. 静态层 ═════════════════════
def static_side():
    fc = src("src/components/director/useDirectorFocusContainment.ts")
    desk = src("src/components/director/DirectorDesk.tsx")
    vp = src("src/components/director/DirectorViewport.tsx")
    allsrc = vp + desk

    i = fc.index("const handleKeyDown = (event: KeyboardEvent) => {")
    j = fc.index('root.addEventListener("keydown", handleKeyDown);')
    hook = fc[i:j]

    declares = [x for x in IDS
                if re.search(r'data-director-%s-panel.{0,400}?role="dialog"'
                             % SEL[x], allsrc, re.S)]
    return {
        "listensOnRoot": 'root.addEventListener("keydown", handleKeyDown)'
                         in fc,
        "keydownListenerCount": fc.count('addEventListener("keydown"'),
        "arraySourceIsRoot": "getDirectorFocusableElements(root)" in hook,
        "wrapsForward": "index === focusable.length - 1" in hook,
        "wrapsBackward": "index <= 0" in hook,
        "preventsDefault": "event.preventDefault();" in hook,
        "hasFocusin": "focusin" in fc,
        "hasFocusout": "focusout" in fc,
        "rootIsDialog": 'querySelector(\'[role="dialog"][aria-modal="true"]\')'
                        in fc or "aria-modal" in fc,
        "declaresDialog": declares,
        "getDirectorFocusableElementsCalls":
            fc.count("getDirectorFocusableElements("),
    }


# ═════════════════════ 2. 原始读数交叉核对 ═════════════════════
def raw_files():
    out = {}
    for f in RAW_FILES:
        p = RAWDIR / f
        if not p.exists():
            raise SystemExit("FATAL 缺原始读数 %s" % p)
        out[f] = json.loads(p.read_text(encoding="utf-8"))
    return out


def raw_side_from(files):
    a = files["vb770a.json"]
    g = {}
    for rd in a["rounds"]:
        for r in rd.get("rows") or []:
            g.setdefault((r.get("id"), r.get("mode")), []).append(r)
    out = {"rounds": len(a["rounds"]), "missing": [], "failed": [],
           "cells": {},
           "cleared": [(rd.get("cleared") or {}).get("removed")
                       for rd in a["rounds"]]}
    for k in CELLS:
        if k not in g or len(g[k]) != 2:
            out["missing"].append("%s/%s" % k)
            continue
        cs = []
        for r in g[k]:
            if r.get("FAILED"):
                out["failed"].append("%s/%s" % k)
            st = r.get("start") or {}
            path = [{"step": s.get("step"),
                     "inPanel": s.get("inPanel") is True,
                     "inDialog": s.get("inDialog") is True,
                     "tag": s.get("tag"),
                     "aria": s.get("aria"), "text": s.get("text"),
                     "idxInDialog": s.get("idxInDialog"),
                     "idxInPanel": s.get("idxInPanel")}
                    for s in (r.get("steps") or [])]
            esc = next((p["step"] for p in path if not p["inPanel"]), None)
            first = next((p for p in path if p["step"] == esc), None)
            cs.append({
                "startTag": st.get("tag"),
                "startIdxInPanel": st.get("idxInPanel"),
                "startIdxInDialog": st.get("idxInDialog"),
                "panelFocusables": st.get("panelFocusables"),
                "dialogFocusables": st.get("dialogFocusables"),
                "path": path, "steps": len(path),
                "escapedAtStep": esc,
                "stayedInPanel": esc is None,
                "leftDialog": bool(first and not first["inDialog"]),
                "inPanelSteps": sum(1 for p in path if p["inPanel"]),
            })
        out["cells"]["%s/%s" % k] = cs

    # 起点纪律
    out["startOK"] = True
    for k in CELLS:
        for c in out["cells"].get("%s/%s" % k, []):
            if c["startTag"] is None or c["startIdxInPanel"] is None \
                    or c["startIdxInPanel"] < 0:
                out["startOK"] = False
            if not c["panelFocusables"] or not c["dialogFocusables"]:
                out["startOK"] = False
            if c["panelFocusables"] > c["dialogFocusables"]:
                out["startOK"] = False
            si = c["startIdxInDialog"]
            if si is None or not (0 <= si < c["dialogFocusables"]):
                out["startOK"] = False

    # ★ 段内下标的单调性：**方向跟着行进方向**（R89）
    mono = []
    for k in CELLS:
        d = 1 if k[1] == "fwd" else -1
        for c in out["cells"].get("%s/%s" % k, []):
            run = [p for p in c["path"] if p["inPanel"]]
            ok = all(run[i + 1]["idxInDialog"] == run[i]["idxInDialog"] + d
                     for i in range(len(run) - 1))
            mono.append({"cell": "%s/%s" % k, "dirStep": d, "monotonic": ok,
                         "runLen": len(run)})
    out["monotonic"] = mono
    out["allMonotonic"] = all(m["monotonic"] for m in mono)
    out["nonMonotonic"] = [m["cell"] for m in mono if not m["monotonic"]]
    # 反向的合法性单独再证一次（写死 +1 会在这里露馅）
    out["backNonIncreasing"] = all(m["monotonic"] for m in mono
                                    if m["cell"].endswith("/back"))

    # ★ 逃逸步数 vs 公式
    ef = []
    for k in CELLS:
        c = out["cells"].get("%s/%s" % k, [{}])[0]
        si, npn = c.get("startIdxInPanel"), c.get("panelFocusables")
        if si is None or npn is None:
            continue
        pred = (npn - si) if k[1] == "fwd" else (si + 1)
        got = c.get("escapedAtStep")
        ef.append({"cell": "%s/%s" % k, "predicted": pred, "measured": got,
                   "matches": (got == pred) if got is not None else None,
                   "beyondWalk": got is None and pred > (c.get("steps") or 0)})
    out["escapeFormula"] = ef
    out["matched"] = [e for e in ef if e["matches"] is True]
    out["beyondWalk"] = [e["cell"] for e in ef if e["beyondWalk"]]
    out["mismatched"] = [e for e in ef if e["matches"] is False]

    # 三分类
    def verdict(c):
        if c["stayedInPanel"]:
            return "stayed-in-panel"
        return ("left-the-dialog" if c["leftDialog"]
                else "left-panel-stayed-in-dialog")

    buckets = {}
    mixed = []
    for k in CELLS:
        vs = {verdict(c) for c in out["cells"].get("%s/%s" % k, [])}
        if len(vs) != 1:
            mixed.append("%s/%s" % k)
            continue
        buckets.setdefault(vs.pop(), []).append("%s/%s" % k)
    out["buckets"] = buckets
    out["mixed"] = mixed
    out["stayed"] = buckets.get("stayed-in-panel", [])
    out["leftPanel"] = buckets.get("left-panel-stayed-in-dialog", [])
    out["leftDialog"] = buckets.get("left-the-dialog", [])
    out["covered"] = sum(len(v) for v in buckets.values()) + len(mixed)
    return out


def raw_side():
    files = raw_files()
    out = raw_side_from(files)
    out["__raw__"] = files
    return out


# ═════════════════════ 3. 产物层 + 交叉核对 ═════════════════════
def run_checks(a, st, rw):
    ck = []

    def C(label, cond, got=None):
        ck.append({"label": label, "pass": bool(cond), "got": got})

    f = a["findings"]
    J = a["judgments"]
    tt = f["tabTrap"]
    comp = f["comparability"]
    stat = f["staticLayer"]

    def df(did):
        for x in (a.get("defects") or []) + (a.get("widened") or []):
            if x.get("id") == did:
                return x
        return {}

    def jd(jid):
        for j in J:
            if j["id"] == jid:
                return j
        return {}

    # ── 静态层
    C("★★ 静态：围栏挂在对话框 root 上、且只有这一个 keydown 监听",
      st["listensOnRoot"] and st["keydownListenerCount"] == 1,
      {"root": st["listensOnRoot"], "n": st["keydownListenerCount"]})
    C("★★ 静态：Tab 数组按 root（对话框）取 ⟹ 边界是对话框不是浮层",
      st["arraySourceIsRoot"] is True, st["arraySourceIsRoot"])
    C("★★ 静态：正反两个方向都环绕（所以 Shift+Tab 同样走出去）",
      st["wrapsForward"] and st["wrapsBackward"],
      {"fwd": st["wrapsForward"], "back": st["wrapsBackward"]})
    C("★ 静态：Tab 时 preventDefault（是 hook 接管，不是浏览器原生序）",
      st["preventsDefault"] is True)
    C("★★ 静态：围栏**没有** focusin / focusout 监听"
      "（769 的 D11 修法未落地，机制没变）",
      st["hasFocusin"] is False and st["hasFocusout"] is False,
      {"focusin": st["hasFocusin"], "focusout": st["hasFocusout"]})
    C("★ 静态：声明 role=dialog 的浮层恰好是 crowd 与 modellib",
      st["declaresDialog"] == ["crowd", "modellib"], st["declaresDialog"])
    C("★ 产物里的声明名单与现算一致",
      tt.get("declaresDialog") == st["declaresDialog"],
      tt.get("declaresDialog"))
    C("★ 产物里「声明了却没围栏」的名单与现算一致",
      tt.get("declaresDialogButNoTrap") == st["declaresDialog"],
      tt.get("declaresDialogButNoTrap"))

    # ── 判据
    got_fail = {j["id"] for j in J if j["verdict"] == "FAIL"}
    got_pass = {j["id"] for j in J if j["verdict"] == "PASS"}
    C("★ 判据 10 条（6 PASS / 4 FAIL）",
      len(J) == 10 and len(got_pass) == 6 and len(got_fail) == 4,
      {"n": len(J), "pass": len(got_pass), "fail": len(got_fail)})
    C("★ FAIL 的判据恰好是 %s" % "/".join(EXPECT_FAIL_IDS),
      got_fail == set(EXPECT_FAIL_IDS), sorted(got_fail))
    C("★ PASS 的判据恰好是 %s" % "/".join(EXPECT_PASS_IDS),
      got_pass == set(EXPECT_PASS_IDS), sorted(got_pass))
    C("★★ 每条判据的 evidence 与 findings 同一份（JSON 往返后再查）",
      all(j.get("evidenceKey") in f and f[j["evidenceKey"]] == j.get("evidence")
          for j in J),
      [j["id"] for j in J if not (
          j.get("evidenceKey") in f
          and f[j["evidenceKey"]] == j.get("evidence"))])

    # ── J1 可比性
    C("★★ 两轮逐字段一致", comp.get("allConsistent") is True,
      comp.get("firstDiff"))
    C("★ 可比性里记了「每格重载页面 + 不点外点」与「起点固定为非输入框」",
      ("重载" in (comp.get("protocol") or "")
       or "重新加载" in (comp.get("protocol") or ""))
      and "不点外点" in (comp.get("protocol") or "")
      and "非输入框" in (comp.get("startPoint") or ""),
      {"protocol": comp.get("protocol"), "start": comp.get("startPoint")})
    C("★★ 12 格无缺格、无 FAILED、每格两轮",
      rw["missing"] == [] and rw["failed"] == []
      and all(len(v) == 2 for v in rw["cells"].values()),
      {"missing": rw["missing"], "failed": rw["failed"]})
    C("★ 步数在产物与 raw 上一致且非 0",
      comp.get("steps") and all(c["steps"] == comp["steps"]
                                for v in rw["cells"].values()
                                for c in v),
      {"artifact": comp.get("steps"),
       "raw": sorted({c["steps"] for v in rw["cells"].values()
                      for c in v})})
    C("★★ 起点纪律：起点在浮层内、下标落在对话框数组内、控件存量非 0",
      rw["startOK"] is True, rw["startOK"])

    # ── J2 逃逸公式
    C("★★ 逃逸步数与公式**逐格**吻合（由 raw 现算，不只信产物）",
      rw["mismatched"] == [] and len(rw["matched"]) == 11
      and tt["escapeFormula"]["matchedCount"] == 11,
      {"rawMatched": len(rw["matched"]), "rawMismatch": rw["mismatched"],
       "artifact": tt["escapeFormula"]["matchedCount"]})
    C("★ 产物里逐格的 predicted / measured 与 raw 现算一致",
      [(e["cell"], e["predictedEscapeStep"], e["measuredEscapeStep"])
       for e in tt["escapeFormula"]["perCell"]]
      == [(e["cell"], e["predicted"], e["measured"])
          for e in rw["escapeFormula"]],
      {"artifact": [(e["cell"], e["predictedEscapeStep"],
                     e["measuredEscapeStep"])
                    for e in tt["escapeFormula"]["perCell"]],
       "raw": [(e["cell"], e["predicted"], e["measured"])
               for e in rw["escapeFormula"]]})
    C("★★ 「步数不够所以没走出去」恰好 1 格且是 modellib/fwd",
      rw["beyondWalk"] == ["modellib/fwd"]
      and tt["escapeFormula"]["cellsBeyondWalk"] == ["modellib/fwd"],
      {"raw": rw["beyondWalk"],
       "artifact": tt["escapeFormula"]["cellsBeyondWalk"]})
    C("★★ J10 判据在，且明说「不许把 12 步没走出去当成围栏好」",
      jd("J10").get("verdict") == "FAIL"
      and "不许把" in jd("J10").get("statement", "")
      and "步数" in jd("J10").get("statement", ""))

    # ── J3 连续段
    C("★★ 段内下标在**行进方向上**严格单调（12/12 格，方向由行进方向给）",
      rw["allMonotonic"] is True and rw["nonMonotonic"] == [],
      {"nonMonotonic": rw["nonMonotonic"]})
    C("★ 反向的 6 格单独再证一次单调（写死 +1 会在这里露馅）",
      rw["backNonIncreasing"] is True)
    C("★ 产物里逐格记录了 expectedStepPerStep（+1/-1）",
      all(s.get("expectedStepPerStep") in (1, -1)
          for s in tt["arraySegment"])
      and {s["cell"].rsplit("/", 1)[1]: s["expectedStepPerStep"]
           for s in tt["arraySegment"] if "/" in s["cell"]}.get("fwd") == 1,
      [s.get("expectedStepPerStep") for s in tt["arraySegment"]])
    C("★ J3 判据在（连续段是 Tab 会走出去的机制）",
      jd("J3").get("verdict") == "PASS"
      and "连续的一段" in jd("J3").get("statement", ""))

    # ── J4 对话框边界
    C("★★ 对话框级围栏成立：0/12 格的焦点离开过对话框",
      rw["leftDialog"] == [] and tt.get("leftTheDialog") == [],
      {"raw": rw["leftDialog"], "artifact": tt.get("leftTheDialog")})
    C("★ 所有逃逸落点仍在对话框内",
      all(c["path"][0]["inDialog"] for v in rw["cells"].values()
          for c in v)
      and tt.get("escapeTargetsAllInDialog") is True,
      tt.get("escapeTargetsAllInDialog"))
    C("★★ J4 写明与 765 的 J6 不矛盾（参照系不同）",
      jd("J4").get("verdict") == "PASS"
      and "765" in jd("J4").get("statement", "")
      and "不矛盾" in jd("J4").get("statement", "")
      and "对话框" in jd("J4").get("statement", "")
      and "浮层" in jd("J4").get("statement", ""))
    C("★ O1 把「参照系必须写清」记成了方法论",
      any(o.get("id") == "O1" and "参照系" in (o.get("text") or "")
          for o in a.get("observations") or []))

    # ── J5 / D13
    d13 = df("D13")
    C("★★ D13 在 defects 里，严重度中、标了与 767 的 D10 相关、要改 src",
      bool(d13) and d13.get("severity") == "中"
      and d13.get("newInThisBatch") and d13.get("needsSrcChange") is True
      and d13.get("relatedToD10From767") is True, d13)
    C("★★ 6/6 个浮层**两个方向都**没有围栏（产物现算）",
      set(tt.get("noPanelHasTrap") or []) == set(IDS)
      and {c.rsplit("/", 1)[0] for c in rw["leftPanel"]} == set(IDS),
      {"artifact": tt.get("noPanelHasTrap"),
       "rawLeftPanel": sorted({c.rsplit("/", 1)[0] for c in rw["leftPanel"]})})
    C("★ D13 的 mechanism 点名「全仓没有任何一层按浮层算的围栏」",
      "没有任何一层按浮层算" in (d13.get("mechanism") or ""))
    C("★ D13 的 where 每一项行号都有效",
      d13 and all(ptr_valid(w) for w in d13.get("where") or []),
      d13.get("where") if d13 else None)
    C("★ D13 的 fixDirection 写了「两层围栏会互相抢 Tab」这个坑",
      "互相抢" in (d13.get("fixDirection") or ""))
    C("★ D13 的 relationToD10 说清了 D10 与本批的因果",
      "D10" in (d13.get("relationToD10") or "")
      and "围栏" in (d13.get("relationToD10") or ""))

    # ── J6 声明与行为不一致
    C("★★ J6：声明 role=dialog 的 2 个恰恰都没有围栏（raw 现算）",
      sorted(rw["leftPanel"] + rw["leftDialog"] + rw["stayed"])
      == sorted(rw["leftPanel"] + rw["leftDialog"] + rw["stayed"])
      and set(st["declaresDialog"]) <= {c.rsplit("/", 1)[0]
                                        for c in rw["leftPanel"]},
      {"declares": st["declaresDialog"],
       "leftPanel": rw["leftPanel"]})
    C("★ J6 给了「要么统一成 dialog 并补围栏、要么明确 Tab 走出去是有意」"
      "的二选一", ("要么统一成 dialog" in jd("J6").get("statement", "")
                   and "有意的" in jd("J6").get("statement", "")))

    # ── J7 反向
    C("★★ Shift+Tab 6/6 都走出去（raw 现算）",
      {c.rsplit("/", 1)[0] for c in rw["leftPanel"]
       if c.endswith("/back")} == set(IDS),
      sorted({c.rsplit("/", 1)[0] for c in rw["leftPanel"]
              if c.endswith("/back")}))
    C("★ J7 点名三个「起点下标为 0、第 1 步就出去」的浮层",
      all(x in jd("J7").get("statement", "")
          for x in ("预设运镜", "创建运动轨迹", "虚拟相机", "第 1 步")))

    # ── J8 / J10 不声称
    C("★★ J8 是不声称，且明说「不声称焦点落到了看不见的控件上」",
      jd("J8").get("verdict") == "FAIL"
      and "不声称" in jd("J8").get("statement", "")
      and "遮挡" in jd("J8").get("statement", "")
      and "769" in jd("J8").get("statement", ""))
    C("★ 不声称里保留了「没测视觉遮挡」与「没测从外部进浮层」",
      any("遮挡" in t for t in a.get("notClaimed") or [])
      and any("能不能进浮层" in t for t in a.get("notClaimed") or []),
      [t[:36] for t in a.get("notClaimed") or []])

    # ── 观察与教训
    C("★ 观察 5 条、探针教训 %d 条（%s）"
      % (len(a.get("probeLessons") or []), "/".join(EXPECT_LESSON_IDS)),
      len(a.get("observations") or []) == 5
      and sorted(r["id"] for r in a.get("probeLessons") or [])
      == EXPECT_LESSON_IDS,
      [r["id"] for r in a.get("probeLessons") or []])
    C("★ 每条教训都有 whyItMatters",
      all(r.get("whyItMatters") for r in a.get("probeLessons") or []))
    C("★★ R87 写明「参照系必须写进产物」且举了 765 的例子",
      any(r["id"] == "R87" and "765" in r.get("text", "")
          and "参照系" in r.get("text", "")
          for r in a.get("probeLessons") or []))
    C("★★ R88 写明「步数不够要给机制公式」且点了模型库那一格",
      any(r["id"] == "R88" and "模型库" in r.get("text", "")
          and "没测到" in r.get("whyItMatters", "")
          for r in a.get("probeLessons") or []))
    C("★★ R89 写明「判据里的方向不能写死」并点名 crowd/back",
      any(r["id"] == "R89" and "crowd/back" in r.get("text", "")
          and "方向" in r.get("text", "")
          for r in a.get("probeLessons") or []))

    # ── 产物结构
    C("★ env.srcModified 为 False", a["env"].get("srcModified") is False)
    C("★ 原始读数与探针脚本都随产物提交（R43）",
      all((RAWDIR / f).exists() for f in RAW_FILES)
      and all((PROBEDIR / f).exists() for f in PROBE_FILES),
      {"raw": [f for f in RAW_FILES if not (RAWDIR / f).exists()],
       "probes": [f for f in PROBE_FILES if not (PROBEDIR / f).exists()]})
    C("★ rawSha 覆盖本批原始读数",
      set(a.get("rawSha") or {}) == set(RAW_FILES), a.get("rawSha"))
    C("★ 探针条目标了 steps 与 rounds",
      [(p.get("id"), p.get("steps"), p.get("rounds"))
       for p in a.get("probes") or []] ==
      [("770a", comp.get("steps"), 2)],
      [(p.get("id"), p.get("steps")) for p in a.get("probes") or []])
    C("★ 三分类的 counts 落在产物里且 12 格铺满",
      sum(tt.get("counts", {}).values()) == 12 and rw["covered"] == 12,
      {"artifact": tt.get("counts"), "rawCovered": rw["covered"]})

    # ── README
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        rows = [ln for ln in rt.split("\n") if ln.startswith("| J")]
        C("★ README 判据表 10 行", len(rows) == 10, len(rows))
        C("★★ README 判据表首格不许是裸数字（pre-commit 正则会拦）",
          not any(re.match(r"^\|\s*\d+[a-z]?\s*\|", ln) for ln in rows),
          [ln[:20] for ln in rows
           if re.match(r"^\|\s*\d+[a-z]?\s*\|", ln)])
        vmap = {j["id"]: j["verdict"] for j in J}
        mism = []
        for ln in rows:
            jid = ln.split("|")[1].strip()
            if jid not in vmap:
                mism.append((jid, "不在产物里"))
            elif ("PASS" in ln) != (vmap[jid] == "PASS"):
                mism.append((jid, vmap[jid]))
        C("★ README 判据表的结论与产物 verdict 逐行一致", not mism, mism)
        for sec in ("## 选题", "## 判据", "## 读数全景", "## 新缺陷",
                    "## 与 765 不矛盾", "## 方法论", "## 探针教训",
                    "## 不声称", "## 复现"):
            C("★ README 有「%s」章节" % sec.strip("# "), sec in rt)
        C("★★ README 有 D13 章节", "### D13" in rt)
        C("★ README 写明「不许把 12 步没走出去当成围栏好」",
          "不许把" in rt and "第 14 步" in rt)
        C("★ README 写明「两层围栏会互相抢 Tab」",
          "互相抢 Tab" in rt)
    else:
        C("★ README 存在", False)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    hits = [ln for ln in lt.split("\n") if ln.startswith("| Batch 770 |")]
    C("★★ 台账恰好一行 Batch 770", len(hits) == 1, len(hits))
    if hits:
        ln = hits[0]
        C("★ 台账首格是 Batch 770（不是裸数字）",
          ln.split("|")[1].strip() == "Batch 770", ln[:24])
        C("★★ 台账新行 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行是 3 列", ln.count("|") == 4, ln.count("|"))
        C("★ 台账新行提到了 D13 与「与 765 不矛盾」",
          "D13" in ln and "765" in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个、仍在 522/583/587",
      lt.count(FFFD) == 9
      and [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]
      == [522, 583, 587],
      {"n": lt.count(FFFD),
       "lines": [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]})
    C("★ 台账只有 633 行", len(lt.split("\n")) == 633,
      len(lt.split("\n")))
    return ck


# ═════════════════════ 4. 阴性对照 ═════════════════════
def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        x = copy.deepcopy(a)
        try:
            mutate(x)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(x, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_static(name, mutate):
        s = copy.deepcopy(st)
        try:
            mutate(s)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(a, s, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_raw(name, mutate):
        files = copy.deepcopy(rw["__raw__"])
        try:
            mutate(files)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        try:
            badr = raw_side_from(files)
        except Exception as e:
            cases.append({"name": name, "caught": True,
                          "firstFail": "重算抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(a, st, badr) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_file(name, path, old, new, all_hits=False):
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            cases.append({"name": name, "caught": False,
                          "firstFail": "待替换文本不存在（对照本身失效）"})
            return
        try:
            body = orig.replace(old, new) if all_hits \
                else orig.replace(old, new, 1)
            path.write_text(body, encoding="utf-8")
            failed = [c["label"] for c in run_checks(a, st, rw) if not c["pass"]]
        finally:
            path.write_text(orig, encoding="utf-8")
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def res_all(files, ident, mode, key="rows"):
        out = []
        for rd in files["vb770a.json"]["rounds"]:
            hit = [x for x in (rd.get(key) or [])
                   if x.get("id") == ident and x.get("mode") == mode]
            if not hit:
                raise KeyError((ident, mode))
            out.append(hit[0])
        return out

    def steps_all(files, ident, mode):
        return [s for r in res_all(files, ident, mode)
                for s in (r.get("steps") or [])]

    # ── D13
    inj("★★ 删掉 D13", lambda x: x.__setitem__(
        "defects", [d for d in x["defects"] if d["id"] != "D13"]))
    inj("★★ 把 D13 降级成观察", lambda x: x.__setitem__(
        "defects", [d for d in x["defects"] if d["id"] != "D13"])
        or x.__setitem__("observations",
                         x["observations"] + [{"id": "O9", "text": "D13"}]))
    inj("★ 把 D13 的严重度从中改成低", lambda x:
        [d for d in x["defects"] if d["id"] == "D13"][0].__setitem__(
            "severity", "低"))
    inj("★ 抹掉 D13 的 relatedToD10From767（与 D10 的因果没了）", lambda x:
        [d for d in x["defects"] if d["id"] == "D13"][0].pop(
            "relatedToD10From767"))
    inj("★ 抹掉 D13 的 relationToD10", lambda x:
        [d for d in x["defects"] if d["id"] == "D13"][0].pop(
            "relationToD10"))
    inj("★ 抹掉 D13 的「两层围栏会互相抢 Tab」", lambda x:
        [d for d in x["defects"] if d["id"] == "D13"][0].__setitem__(
            "fixDirection", "加一层围栏即可"))
    inj("★ D13 的 where 指向不存在的行号", lambda x:
        [d for d in x["defects"] if d["id"] == "D13"][0]["where"].append(
            "src/components/director/useDirectorFocusContainment.ts:99999"))
    inj("★ 删掉 J5", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J5"]))

    # ── 「没有浮层有围栏」这个全族结论
    inj("★★ 把 noPanelHasTrap 缩到 4 个（谎称有两个有围栏）", lambda x:
        x["findings"]["tabTrap"].__setitem__("noPanelHasTrap",
                                             IDS[:4]))
    inj("★★ 把 stayed-in-panel 那一桶塞进 export", lambda x:
        x["findings"]["tabTrap"].__setitem__("stayedInPanel",
                                             ["export/fwd", "export/back"]))
    inj("★★ 把 counts 改成 12 格都在浮层内", lambda x:
        x["findings"]["tabTrap"].__setitem__(
            "counts", {"stayed-in-panel": 12}))

    # ── J10：把「步数不够」当成「有围栏」
    inj("★★ 把「步数不够」的格从 cellsBeyondWalk 里抹掉", lambda x:
        x["findings"]["tabTrap"]["escapeFormula"].__setitem__(
            "cellsBeyondWalk", []))
    inj("★★ 删掉 J10（不许把步数不够当围栏好）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J10"]))
    inj("★ 删掉 R88（步数不够要给公式）", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R88"]))

    # ── J4 参照系
    inj("★★ 把 J4 里的「不矛盾」抹掉（会被当成推翻 765）", lambda x:
        [j for j in x["judgments"] if j["id"] == "J4"][0].__setitem__(
            "statement",
            "对话框级围栏是好的：0/12 格的焦点离开过对话框。"
            "本批 11/12 格的焦点离开了浮层。"))
    inj("★ 删掉 O1（参照系这条方法论）", lambda x: x.__setitem__(
        "observations", [o for o in x["observations"] if o["id"] != "O1"]))
    inj("★ 删掉 R87", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R87"]))
    inj("★ 删掉 J4", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J4"]))

    # ── J6 声明与行为
    inj("★★ 把 declaresDialogButNoTrap 清空（说声明的都守住了焦点）",
        lambda x: x["findings"]["tabTrap"].__setitem__(
            "declaresDialogButNoTrap", []))
    inj("★ 删掉 J6", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J6"]))

    # ── 方向（R89）
    inj("★ 删掉 R89", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R89"]))
    inj("★ 把 arraySegment 的 expectedStepPerStep 全写成 1", lambda x:
        [s.__setitem__("expectedStepPerStep", 1)
         for s in x["findings"]["tabTrap"]["arraySegment"]])

    # ── 判据偷改
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS", lambda x: ([j.__setitem__("verdict", "PASS")
                                       for j in x["judgments"]]))
    inj("★ 把判据条数从 10 改成 7", lambda x: x.__setitem__(
        "judgments", x["judgments"][:7]))
    inj("★ 把 J2 的 matchedCount 从 11 改成 12", lambda x:
        x["findings"]["tabTrap"]["escapeFormula"].__setitem__(
            "matchedCount", 12))
    inj("★ 只改 findings 一份（判据的 evidence 不动）", lambda x:
        x["findings"]["tabTrap"].__setitem__("leftTheDialog",
                                             ["export/fwd"]))

    # ── 静态层伪造
    inj_static("伪造：围栏开始监听 focusin（D11 修法已落地）",
               lambda x: x.__setitem__("hasFocusin", True))
    inj_static("伪造：围栏的 keydown 监听变成两个", lambda x:
               x.__setitem__("keydownListenerCount", 2))
    inj_static("伪造：Tab 数组不再按 root 取", lambda x:
               x.__setitem__("arraySourceIsRoot", False))
    inj_static("伪造：反向不再环绕", lambda x:
               x.__setitem__("wrapsBackward", False))
    inj_static("伪造：声明 role=dialog 的变成 6 个", lambda x:
               x.__setitem__("declaresDialog", IDS))
    inj_static("伪造：Tab 时不 preventDefault（改成浏览器原生序）",
               lambda x: x.__setitem__("preventsDefault", False))

    # ── 原始读数：改真正的被检查键
    inj_raw("★★ 原始：把 export/fwd 的第 4 步改成不出浮层（D13 少一格）",
            lambda x: [s.__setitem__("inPanel", True) for s in
                       steps_all(x, "export", "fwd")[3:]])
    inj_raw("★★ 原始：把某格的逃逸落点改成出对话框（J4 破）", lambda x:
            [s.__setitem__("inDialog", False) for s in
             steps_all(x, "export", "fwd")[3:]])
    inj_raw("★★ 原始：改一个下标打断连续段（J3 破）", lambda x:
            [s.__setitem__("idxInDialog", 999)
             for s in steps_all(x, "crowd", "back")[:1]])
    inj_raw("★★ 原始：反向的下标改成递增（应该递减）", lambda x:
            [s.__setitem__("idxInDialog", 41 + i)
             for i, s in enumerate(
                 [q for q in steps_all(x, "crowd", "back") if q["inPanel"]])])
    inj_raw("★★ 原始：把逃逸步数改得与公式不符（J2 破）", lambda x:
            [s.__setitem__("inPanel", False)
             for s in steps_all(x, "export", "fwd")[1:2]])
    inj_raw("★★ 原始：把起点下标改成不在浮层内（起点纪律）", lambda x:
            [r["start"].__setitem__("idxInPanel", -1)
             for r in res_all(x, "export", "fwd")])
    inj_raw("★★ 原始：把起点下标改成落在对话框数组之外", lambda x:
            [r["start"].__setitem__("idxInDialog", 9999)
             for r in res_all(x, "export", "fwd")])
    inj_raw("★ 原始：某格 FAILED", lambda x:
            [r.__setitem__("FAILED", "点不动")
             for r in res_all(x, "modellib", "fwd")])
    inj_raw("★ all([]) 陷阱：把 rows 清空（两轮都清）", lambda x:
            [rd.__setitem__("rows", [])
             for rd in x["vb770a.json"]["rounds"]])
    inj_raw("★ 原始：步数改成 5（与产物不符）", lambda x:
            [r.__setitem__("steps", (r.get("steps") or [])[:5])
             for r in res_all(x, "export", "fwd")])
    inj_raw("★ 原始：浮层控件数改成大于对话框控件数", lambda x:
            [r["start"].__setitem__("panelFocusables", 9999)
             for r in res_all(x, "export", "fwd")])

    # ── 台账 / README
    led = LEDGER.read_text(encoding="utf-8")
    led_line = next((ln for ln in led.split("\n")
                     if ln.startswith("| Batch 770 |")), "")
    if led_line:
        sep = "" if led.endswith(led_line + "\n") else "\n"
        inj_file("★ 台账删掉 Batch 770 行", LEDGER, sep + led_line, "")
        inj_file("★ 台账行首格改成裸数字 770", LEDGER,
                 "| Batch 770 |", "| 770 |")
        inj_file("★ 台账行首格写成 Batch 0770", LEDGER,
                 "| Batch 770 |", "| Batch 0770 |")
        inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
                 led_line[:40], led_line[:40] + FFFD)
        inj_file("★ 台账被追加了 Batch 771（行数断言）", LEDGER,
                 "| Batch 770 |", "| Batch 770 |\n| Batch 771 | x")
        inj_file("★ 台账新行不含 D13", LEDGER, "D13", "D1z",
                 all_hits=True)
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.split("\n")
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 判据表首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D13 章节", README, "### D13", "### 附注")
        inj_file("★ README 删掉「与 765 不矛盾」章节", README,
                 "## 与 765 不矛盾", "## 附注")
        inj_file("★ README 删掉「第 14 步」", README, "第 14 步", "很多步",
                 all_hits=True)
    return cases


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        rw = raw_side()
        rawErr = None
    except Exception as e:
        rw, rawErr = {}, str(e)

    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（raw/ 下 1 份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 770, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:260]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 770 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
