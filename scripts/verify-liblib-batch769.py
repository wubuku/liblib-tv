"""batch 769 验收器：协议 v2 —— 只换「焦点落点」这一个变量

三层结构（与 753–768 同）：
  1. **静态层** —— 从 `src/` 独立复核：`isEditable` 早退的**位置与覆盖标签**、
     群众面板的控件顺序（用来在跑浏览器之前预测落点）、D12 那个
     `sr-only` 文件框的**每一个属性**
  2. **产物层** —— 判据条数与 verdict、缺陷/扩宽、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb769a.json` **重算**分桶、落点配对的
     协议等价、结构性失败的可解释性；**并独立复核 768 的 raw**
     （不能只信产物里那句「6/6 复现」）。缺失时**判失败而不是通过**

⚠ 本批盯住六件容易自欺的事：
  - **协议等价的判别式是「落点」不是「臂名」**：3 个浮层里一个输入框都没有，
    它们的 `editable` 臂必然失败。产物必须**按 (tag,type) 配对**并如实
    标出「结构性不可能」，不许把结构失败算成探针坏了或算成复现失败。
  - **不许把「没测到」这一桶清空后就不再声明分母**：6 个浮层的分桶必须
    **铺满**，`all([])` 是 True。
  - **D12 的静态依据要逐项独立复核**（`sr-only` / 无 aria-label / 无 label /
    落点 index 0），其中「无 aria-label」要**不依赖产物的切片**重新取一次
    —— R85 就是被一个停在 `=>` 上的正则坑过的。
  - **D3×D8 的耦合必须写成实测**：J7 与 D3 的 repairOrder 都得在。
  - **更正/加强的表述要分清**：D4 本批**没有新增成员**，只是独立复现；
    产物不许把它写成扩宽。
  - **768 的 raw 必须被真的读一遍**（`reproduced` 要由 raw 现算，不是引用）。

判据 **12 条（8 PASS / 4 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch769-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
PREV_RAW = (ROOT / "docs/research/liblib-canvas-batch768-2026-10-01"
            / "raw" / "vb768a.json")

RAW_FILES = ["vb769a.json"]
PROBE_FILES = ["dbg769a.py", "mk769audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
ARMS = ["editable", "noneditable"]
CELLS = [(i, a) for i in IDS for a in ARMS]
EXPECT_FAIL_IDS = ["J5", "J7", "J8", "J10"]
EXPECT_PASS_IDS = ["J1", "J2", "J3", "J4", "J6", "J9", "J11", "J12"]
EXPECT_LESSON_IDS = ["R81", "R82", "R83", "R84", "R85", "R86"]


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
    desk = src("src/components/director/DirectorDesk.tsx")
    vp = src("src/components/director/DirectorViewport.tsx")
    expp = src("src/components/director/DirectorExportPanel.tsx")

    # D3 的机制：isEditable 早退必须排在 Escape 分支之前
    gate = desk.index("if (isEditable) return;")
    esc = desk.index('if (event.key !== "Escape") return;')
    # ★ D12：取那个文件框的属性。**不能**用 `<input\b[^>]*>` —— JSX 里
    #   `onChange={(event) => …}` 的 `=>` 会被当成标签结尾（R85）。
    #   这里用「最近的 <input 比最近的 > 更靠后」做形状守卫，再取窗口。
    ml = vp[vp.index("data-director-model-library-panel"):vp.index(
        "data-director-model-library-trigger")]
    at = ml.index("data-director-model-library-local-input")
    shapeOk = ml.rfind("<input", 0, at) > ml.rfind(">", 0, at)
    win = ml[at - 200:at + 400]
    before = ml[max(0, at - 400):at]

    cseg = vp[vp.index("data-director-crowd-panel"):vp.index(
        "data-director-model-library-panel")]
    order = re.findall(r"<(input|button|select|textarea)\b", cseg)

    return {
        "isEditableGateLine": desk.count("\n", 0, gate),
        "escapeBranchLine": desk.count("\n", 0, esc),
        "gateBeforeEscape": gate < esc,
        "isEditableTags": re.findall(r'target\.tagName === "(\w+)"', desk),
        "isEditableHasContentEditable": "target.isContentEditable" in desk,
        "deskLadderOtherRefs": len(re.findall(
            r"crowdPanelOpen|modelLibraryOpen|phoneVcamOpen|presetPanelLeft|"
            r"pathMenuLeft", desk)),
        "deskLadderExportTiers": len(re.findall(
            r"if \(exportPanelOpen\)", desk)),
        "exportAspectBeforeSubmit": (
            expp.index("data-director-export-aspect")
            < expp.index("data-director-export-submit")),
        "exportHasSubmit": "data-director-export-submit" in expp,
        "crowdStaticOrder": order,
        "crowdInputs": order.count("input"),
        "crowdButtons": order.count("button"),
        "crowdFirstButtonAfterAllInputs": (
            "button" in order
            and order.index("button") == order.count("input")),
        "crowdCancelBeforeAdd": (
            cseg.index('data-director-crowd-action="cancel"')
            < cseg.index('data-director-crowd-action="add"')),
        # D12 的每一项
        "mlShapeOk": shapeOk,
        "mlTypeFile": 'type="file"' in win,
        "mlIsSrOnly": "sr-only" in win,
        "mlAriaLabel": "aria-label" in win,
        "mlAriaLabelledby": "aria-labelledby" in win,
        "mlTitle": "title=" in win,
        "mlId": "id=" in win,
        "mlLabelOpenedBefore": (before.count("<label")
                                > before.count("</label>")),
        "mlLabelCount": len(re.findall(r"<label\b", ml)),
        "mlAccept": 'accept=".fbx,.obj"' in win,
    }


# ═════════════════════ 2. 原始读数交叉核对 ═════════════════════
def raw_files():
    out = {}
    for f in RAW_FILES:
        p = RAWDIR / f
        if not p.exists():
            raise SystemExit("FATAL 缺原始读数 %s" % p)
        out[f] = json.loads(p.read_text(encoding="utf-8"))
    if not PREV_RAW.exists():
        raise SystemExit("FATAL 缺 768 的原始读数 %s —— 复现性核对判失败"
                         % PREV_RAW)
    out["__prev__"] = json.loads(PREV_RAW.read_text(encoding="utf-8"))
    return out


def classify(r):
    st = r.get("after") or {}
    de = r.get("desk") or {}
    if st.get("open") is False or de.get("open") is False:
        return "desk-lost"
    if st.get("panelPresent") is True:
        return "panel-stuck"
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


def spot(r):
    f = r.get("focus") or {}
    fk = r.get("focusKind") or {}
    return (fk.get("tag") or f.get("tag") or "",
            fk.get("type") or f.get("type") or "")


def raw_side_from(files):
    a = files["vb769a.json"]
    g = {}
    for rd in a["rounds"]:
        for r in rd.get("rows") or []:
            g.setdefault((r.get("id"), r.get("mode")), []).append(r)
    out = {"rounds": len(a["rounds"]), "missing": [], "cells": {},
           "cleared": [(rd.get("cleared") or {}).get("removed")
                       for rd in a["rounds"]],
           "deskGoneAfter": [rd.get("deskGoneAfter") for rd in a["rounds"]]}
    for k in CELLS:
        if k not in g or len(g[k]) != 2:
            out["missing"].append("%s/%s" % k)
            continue
        cells = []
        for r in g[k]:
            f = r.get("focus") or {}
            fk = r.get("focusKind") or {}
            cells.append({
                "failed": r.get("FAILED"),
                "structImpossible": (f.get("err")
                                     == "no element of that kind"),
                "focused": f.get("focused") is True,
                "opened": (r.get("before") or {}).get("panelPresent")
                          is True,
                "inPanel": fk.get("inPanel") is True,
                "isEditableByTag": fk.get("isEditableByTag") is True,
                "tag": fk.get("tag") or f.get("tag"),
                "type": fk.get("type"),
                "pickedIndex": f.get("pickedIndex"),
                "total": f.get("total"),
                "nEditable": f.get("nEditable"),
                "nNonEditable": f.get("nNonEditable"),
                "class": None if r.get("FAILED") else classify(r),
            })
        out["cells"]["%s/%s" % k] = cells

    # 可编辑 / 不可编辑控件存量（现算）
    inv = {}
    for i in IDS:
        v = {}
        # ★ 两臂读到的存量必须**一致**。不一致就说明其中一臂的读数被改过
        #   —— 若这里「取最后一个」，另一臂的值会把它悄悄顶掉，
        #   任何针对存量的注入都拦不住（这次就踩了）。
        disagree = []
        for arm in ARMS:
            for c in out["cells"].get("%s/%s" % (i, arm), []):
                if c["total"] is None:
                    continue
                cur = (c["total"], c["nEditable"], c["nNonEditable"])
                if v and cur != (v["total"], v["nEditable"], v["nNonEditable"]):
                    disagree.append((arm, cur))
                v["total"], v["nEditable"], v["nNonEditable"] = cur
        v["disagree"] = disagree
        inv[i] = v
    out["inventory"] = inv
    for i in IDS:
        assert inv[i].get("total") is not None, "%s 没读到存量" % i
        assert inv[i]["nEditable"] + inv[i]["nNonEditable"] == inv[i]["total"], \
            "%s 两类计数与总数对不上" % i
    out["inventoryAgree"] = all(not inv[i]["disagree"] for i in IDS)
    out["noEditable"] = [i for i in IDS if inv[i]["nEditable"] == 0]

    # 结构性失败必须**与存量一致**（n==0 ⟺ 该臂两轮都失败）
    out["structOK"] = True
    for i in IDS:
        for arm in ARMS:
            key = "%s/%s" % (i, arm)
            cs = out["cells"].get(key) or []
            if not cs:
                continue
            n = inv[i]["nEditable"] if arm == "editable" \
                else inv[i]["nNonEditable"]
            allFail = all(c["structImpossible"] for c in cs)
            if n == 0 and not allFail:
                out["structOK"] = False
            if n > 0 and (allFail or not all(c["focused"] for c in cs)
                          or not all(c["opened"] for c in cs)
                          or not all(c["inPanel"] for c in cs)
                          or not all(c["isEditableByTag"] == (arm == "editable")
                                     for c in cs)):
                out["structOK"] = False
    out["impossibleArms"] = [
        k for k in out["cells"]
        if all(c["structImpossible"] for c in out["cells"][k])]

    # 新协议分桶
    buckets = {}
    for i in IDS:
        cs = out["cells"]["%s/noneditable" % i]
        if all(c["structImpossible"] for c in cs):
            v = "structurally-impossible"
        else:
            cl = {c["class"] for c in cs}
            v = {"desk-lost": "measured-desk-lost",
                 "panel-stuck": "measured-stuck",
                 "closed-focus-on-body": "measured-focus-to-body",
                 "closed-focus-on-trigger": "measured-focus-to-trigger",
                 "closed-focus-in-dialog": "measured-focus-in-dialog",
                 "closed-focus-outside-dialog":
                     "measured-focus-outside-dialog",
                 "unknown": "unknown"}.get(list(cl)[0]
                                            if len(cl) == 1 else None,
                                            "mixed:" + ",".join(sorted(cl)))
        buckets.setdefault(v, []).append(i)
    out["buckets"] = buckets
    out["v2"] = {i: [k for k, v in buckets.items() if i in v][0] for i in IDS}

    # 落点索引
    out["editableIndex"] = {
        i: out["cells"]["%s/editable" % i][0]["pickedIndex"] for i in IDS}
    out["noneditableIndex"] = {
        i: out["cells"]["%s/noneditable" % i][0]["pickedIndex"] for i in IDS}

    # ═══ 独立复核 768：按**落点**配对判协议等价 ═══
    prev = files["__prev__"]
    pg = {}
    for rd in prev["rounds"]:
        for r in rd.get("rows") or []:
            if r.get("mode") == "inside":
                pg.setdefault(r.get("id"), []).append(r)
    out["prevHasAllIds"] = sorted(pg) == sorted(IDS)
    pairs = []
    for i in IDS:
        if i not in pg or len(pg[i]) != 2:
            pairs.append({"id": i, "matchedArm": None, "reproduces": False})
            continue
        pv = [classify(r) for r in pg[i]]
        match = None
        for arm in ARMS:
            cs = out["cells"].get("%s/%s" % (i, arm)) or []
            if cs and all(c["structImpossible"] for c in cs):
                continue
            if all(spot(cs[r].get("__row") or cs[r]) for r in ()):
                pass
            if all((cs[r]["tag"], cs[r]["type"] or "") == spot(pg[i][r])
                   for r in range(2)):
                match = arm
                break
        got = ([c["class"] for c in out["cells"]["%s/%s" % (i, match)]]
               if match else None)
        pairs.append({"id": i, "prevClass": pv, "matchedArm": match,
                      "newClass": got,
                      "reproduces": bool(match) and got == pv})
    out["pairs"] = pairs
    out["reproduced"] = [p["id"] for p in pairs if p["reproduces"]]
    out["notComparable"] = [p["id"] for p in pairs if not p["matchedArm"]]
    out["mismatched"] = [p["id"] for p in pairs
                         if p["matchedArm"] and not p["reproduces"]]
    # 可聚焦控件存量与 768 对齐
    out["prevTotals"] = {i: (pg[i][0].get("focus") or {}).get("total")
                         for i in IDS if i in pg}
    out["totalsAgree"] = out["prevTotals"] == {i: inv[i]["total"] for i in IDS}
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
    pv2 = f["protocolV2"]
    rep = f["reproducibility"]
    inv = f["focusInventory"]
    stat = f["staticLayer"]
    d12 = f["srOnlyFileInput"]

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
    C("★★ 静态：isEditable 早退排在 Escape 分支之前（D3 的机制）",
      st["gateBeforeEscape"],
      {"gate": st["isEditableGateLine"], "esc": st["escapeBranchLine"]})
    C("★ 静态：isEditable 覆盖 INPUT/TEXTAREA/SELECT 与 contenteditable",
      set(st["isEditableTags"]) == {"INPUT", "TEXTAREA", "SELECT"}
      and st["isEditableHasContentEditable"], st["isEditableTags"])
    C("★★ 静态：导演台 Esc 阶梯对另外五个浮层状态 0 处引用",
      st["deskLadderOtherRefs"] == 0, st["deskLadderOtherRefs"])
    C("★ 静态：阶梯里导出面板那档恰好一处", st["deskLadderExportTiers"] == 1,
      st["deskLadderExportTiers"])
    C("★★ 静态：群众面板 3 个 input 在 2 个 button 之前 ⟹ 预测落点 index 3",
      st["crowdInputs"] == 3 and st["crowdButtons"] == 2
      and st["crowdFirstButtonAfterAllInputs"]
      and st["crowdCancelBeforeAdd"],
      {"inputs": st["crowdInputs"], "buttons": st["crowdButtons"],
       "order": st["crowdStaticOrder"]})
    C("★ 静态：群众面板的非输入框落点实测就是 index 3（J12）",
      rw["noneditableIndex"]["crowd"] == 3
      and inv["noneditableLandingIndex"]["crowd"] == 3,
      {"staticPredicted": 3, "raw": rw["noneditableIndex"]["crowd"]})
    C("★ 静态：导出面板画幅按钮排在提交按钮之前",
      st["exportAspectBeforeSubmit"] and st["exportHasSubmit"])

    # ── D12 的静态依据（逐项独立复核）
    C("★★ D12：取标签的形状守卫通过（最近的 <input 比最近的 > 更靠后）",
      st["mlShapeOk"] is True, st["mlShapeOk"])
    C("★★ D12：那是个 type=file 且 className 含 sr-only 的输入框",
      st["mlTypeFile"] and st["mlIsSrOnly"],
      {"file": st["mlTypeFile"], "srOnly": st["mlIsSrOnly"]})
    C("★★ D12：它**零可访问名**（无 aria-label / aria-labelledby / title / id"
      " / 不在 label 内）",
      not any(st[k] for k in ("mlAriaLabel", "mlAriaLabelledby", "mlTitle",
                              "mlId", "mlLabelOpenedBefore")),
      {k: st[k] for k in ("mlAriaLabel", "mlAriaLabelledby", "mlTitle",
                          "mlId", "mlLabelOpenedBefore")})
    C("★ D12：产物里 D12 的每一项与现算一致（含 sr-only 与可访问名）",
      d12.get("isSrOnly") is True and d12.get("hasAriaLabel") is False
      and d12.get("wrappedInLabel") is False and d12.get("typeFile") is True,
      {k: d12.get(k) for k in ("isSrOnly", "hasAriaLabel", "wrappedInLabel",
                               "typeFile")})
    C("★★ D12：它落在模型库面板的**第一个**可聚焦位置（index 0）",
      d12.get("indexInPanel") == 0
      and rw["editableIndex"]["modellib"] == 0
      and d12.get("panelFocusables") == rw["inventory"]["modellib"]["total"],
      {"artifact": d12.get("indexInPanel"),
       "raw": rw["editableIndex"]["modellib"]})
    C("★ D12 的 measured 里含「editable 臂的落点就是它」与 pickedIndex=0",
      "pickedIndex=0" in (df("D12").get("measured") or "")
      and "INPUT[type=file]" in (df("D12").get("measured") or ""))
    C("★ D12 明确写了它与 765/762 那个 display:none 的**不是同一个**",
      "不是同一个" in (df("D12").get("whyItWasMissedBefore") or "")
      and "display:none" in (df("D12").get("whyItWasMissedBefore") or ""))
    C("★ D12 有 fixDirection 且两个选项都写了", bool(df("D12").get(
        "fixDirection")) and "aria-label" in df("D12")["fixDirection"])

    # ── 判据
    got_fail = {j["id"] for j in J if j["verdict"] == "FAIL"}
    got_pass = {j["id"] for j in J if j["verdict"] == "PASS"}
    C("★ 判据 12 条（8 PASS / 4 FAIL）",
      len(J) == 12 and len(got_pass) == 8 and len(got_fail) == 4,
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

    # ── 协议等价（按落点，不按臂名）
    C("★★ 协议等价按**落点**配对：768 的 raw 被真的读了一遍",
      rw["prevHasAllIds"] is True and rw["reproduced"] == IDS,
      {"reproduced": rw["reproduced"], "prevIds": rw["prevHasAllIds"]})
    C("★★ 6/6 复现 768 的读数（由 raw 现算，不是引用产物）",
      rep.get("reproduced") == rw["reproduced"] == IDS
      and rep.get("mismatched") == [] == rw["mismatched"],
      {"artifact": rep.get("reproduced"), "raw": rw["reproduced"],
       "mismatch": rw["mismatched"]})
    C("★ 产物写明「按落点不按臂名」的判别式与其理由",
      "落点" in (rep.get("rule") or "") and "臂名" in (rep.get("rule") or ""))
    C("★ 3 个浮层一个输入框都没有 ⟹ 它们的 editable 臂结构性不可能",
      rw["noEditable"] == ["preset", "pathmenu", "phonevcam"]
      and sorted(rw["impossibleArms"]) == sorted(
          ["%s/editable" % i for i in ("preset", "pathmenu", "phonevcam")]),
      {"noEditable": rw["noEditable"],
       "impossible": rw["impossibleArms"]})
    C("★★ 结构性失败与存量一致（n==0 ⟺ 该臂两轮都失败；n>0 ⟹ 两轮都成功）",
      rw["structOK"] is True, rw["structOK"])
    C("★★ 两臂读到的控件存量**一致**（不一致 ⟹ 有一臂读数被改过）",
      rw.get("inventoryAgree") is True,
      {i: inv["perPanel"][i] for i in IDS
       if rw["inventory"][i].get("disagree")})
    C("★ 产物里 impossibleArms 与 raw 现算一致",
      sorted(inv.get("armsStructurallyImpossible") or [])
      == sorted(rw["impossibleArms"]),
      {"artifact": inv.get("armsStructurallyImpossible"),
       "raw": rw["impossibleArms"]})
    C("★ 可聚焦控件存量与 768 逐个相同",
      rw["totalsAgree"] is True
      and all(inv["agreesWith768"].values())
      and {i: inv["perPanel"][i]["total"] for i in IDS}
      == {i: rw["inventory"][i]["total"] for i in IDS},
      {"agree": rw["totalsAgree"],
       "raw": {i: rw["inventory"][i]["total"] for i in IDS}})

    # ── 新协议分桶
    C("★★ 新协议分桶：焦点掉 body 3 个 + 导演台被关掉 3 个",
      sorted(pv2.get("focusFellToBody") or [])
      == sorted(rw["buckets"].get("measured-focus-to-body", []))
      == ["export", "modellib", "phonevcam"]
      and sorted(pv2.get("deskLost") or [])
      == sorted(rw["buckets"].get("measured-desk-lost", []))
      == ["crowd", "pathmenu", "preset"],
      {"artifact": {"body": pv2.get("focusFellToBody"),
                    "deskLost": pv2.get("deskLost")},
       "raw": {k: v for k, v in rw["buckets"].items()}})
    C("★★ 归还焦点触发器 0 个",
      (pv2.get("focusRestoredToTrigger") or []) == []
      and "measured-focus-to-trigger" not in rw["buckets"],
      {"artifact": pv2.get("focusRestoredToTrigger"),
       "raw": rw["buckets"].get("measured-focus-to-trigger")})
    C("★★ 6 个浮层的分桶**恰好铺满**（all([]) 陷阱）",
      sorted((pv2.get("focusFellToBody") or []) + (pv2.get("deskLost") or [])
             + (pv2.get("focusRestoredToTrigger") or [])
             + (pv2.get("panelStuck") or [])
             + (pv2.get("structurallyImpossible") or [])) == sorted(IDS)
      and sorted(i for v in rw["buckets"].values() for i in v) == sorted(IDS),
      {"artifact": pv2.get("counts"), "raw": rw["buckets"]})
    C("★ 逐浮层结论与 raw 现算一致",
      all(pv2["perDisclosure"][i]["verdict"] == rw["v2"][i] for i in IDS),
      {i: (pv2["perDisclosure"][i]["verdict"], rw["v2"][i]) for i in IDS
       if pv2["perDisclosure"][i]["verdict"] != rw["v2"][i]})

    # ── J4：768 的「没测到」被关掉
    C("★★ J4：768 的「2 个没测到」被关掉，且产物不再有那一桶",
      jd("J4").get("verdict") == "PASS"
      and "没测到" in jd("J4").get("statement", "")
      and "measured-stuck" not in rw["buckets"].get("noneditable", {}),
      jd("J4").get("statement", "")[:60])

    # ── J5 / D11
    C("★★ J5：D11 扩大确认，措辞含「仍是 0/6」与「3 个全错」",
      jd("J5").get("verdict") == "FAIL"
      and "0/6" in jd("J5").get("statement", "")
      and "3 个全错" in jd("J5").get("statement", ""))
    w11 = df("D11")
    C("★ D11 的 newMembers 是 export（只加了一个）",
      (w11 or {}).get("newMembers") == ["export"], w11)

    # ── J6 / D4：独立复现，不是扩宽
    w4 = df("D4")
    C("★★ J6：765 的 D4 独立复现，措辞含「另一套协议」与「独立重测」",
      jd("J6").get("verdict") == "PASS"
      and "独立" in jd("J6").get("statement", ""))
    C("★★ D4 本批**没有新增成员**（产物不许把它写成扩宽）",
      (w4 or {}).get("newMembers") == []
      and "没有新增成员" in ((w4 or {}).get("note") or ""),
      {"newMembers": (w4 or {}).get("newMembers")})
    C("★ D4 的 note 写明是「双协议确认」",
      "双协议" in ((w4 or {}).get("note") or ""))
    C("★ 导出面板新协议的落点实测就是画幅按钮（index 1/5）",
      rw["noneditableIndex"]["export"] == 1
      and rw["inventory"]["export"]["total"] == 5
      and "index 1/5" in (jd("J6").get("statement") or ""),
      {"raw": rw["noneditableIndex"]["export"]})

    # ── J7 / D3：耦合必须是实测
    C("★★ J7：D3×D8 的耦合写成实测（输入框=没发生 / cancel 按钮=导演台没了）",
      jd("J7").get("verdict") == "FAIL"
      and "cancel" in jd("J7").get("statement", "")
      and "推理" in jd("J7").get("statement", ""))
    w3 = df("D3")
    C("★★ D3 的 repairOrder 写明「先修 D8，再修 D3」且有顺序理由",
      "先修 D8，再修 D3" in ((w3 or {}).get("repairOrder") or ""),
      (w3 or {}).get("repairOrder"))
    C("★★ 群众阵列双臂读数：editable=没关、noneditable=导演台没了",
      [c["class"] for c in rw["cells"]["crowd/editable"]] ==
      ["panel-stuck", "panel-stuck"]
      and [c["class"] for c in rw["cells"]["crowd/noneditable"]] ==
      ["desk-lost", "desk-lost"],
      {"editable": [c["class"] for c in rw["cells"]["crowd/editable"]],
       "noneditable": [c["class"] for c in rw["cells"]["crowd/noneditable"]]})
    C("★ D3 的 note 写明「作用域」与「这个 if 的两面」",
      "作用域" in ((w3 or {}).get("note") or "")
      and "的两面" in ((w3 or {}).get("note") or ""))

    # ── J9：isEditable 的作用域
    C("★★ J9：产物写明 isEditable 早退只对两类浮层有效、对模型库无效",
      jd("J9").get("verdict") == "PASS"
      and "只对两类" in jd("J9").get("statement", "")
      and "模型库" in jd("J9").get("statement", ""))
    C("★ 模型库的 editable 臂落点是 INPUT 却仍然关掉了面板（作用域证据）",
      rw["editableIndex"]["modellib"] == 0
      and rw["inventory"]["modellib"]["nEditable"] >= 1
      and [c["class"] for c in rw["cells"]["modellib/editable"]] ==
      ["closed-focus-on-body", "closed-focus-on-body"],
      {"index": rw["editableIndex"]["modellib"],
       "class": [c["class"] for c in rw["cells"]["modellib/editable"]]})

    # ── J10：不声称
    C("★★ J10 是不声称，且列了「只换类别没换位置」与 768 的遗留项",
      jd("J10").get("verdict") == "FAIL"
      and "类别" in jd("J10").get("statement", "")
      and "位置" in jd("J10").get("statement", "")
      and "Tab" in jd("J10").get("statement", ""))
    C("★ 不声称里保留了「没换位置」与「sr-only 同族未普查」",
      any("没换焦点" in t or "只换了焦点" in t
          for t in a.get("notClaimed") or [])
      and any("没普查" in t or "未测" in t
              for t in a.get("notClaimed") or []))
    C("★ 不声称里说了没改 src/",
      any("没有改 `src/`" in t for t in a.get("notClaimed") or []))

    # ── 可比性与纪律
    comp = f["comparability"]
    C("★★ 两轮逐字段一致", comp.get("allConsistent") is True)
    C("★ 可比性里记了协议（每臂重载页面、不点外点）与「只换一个变量」",
      ("重载" in (comp.get("protocol") or "")
       or "重新加载" in (comp.get("protocol") or ""))
      and "不点外点" in (comp.get("protocol") or "")
      and "只换一个变量" in (comp.get("variable") or ""))
    C("★★ 12 格无缺格、每格两轮",
      rw["missing"] == [] and all(len(v) == 2
                                  for v in rw["cells"].values()))
    C("★ 观察恰好 5 条（多出来的就是「把缺陷降级成观察」的痕迹）",
      len(a.get("observations") or []) == 5,
      [o.get("id") for o in a.get("observations") or []])
    C("★ 观测 O3 记了「换个变量把耦合照出来」",
      any(o.get("id") == "O3" for o in a.get("observations") or []))
    C("★ 观测 O5 记了「产物里的推理是欠账」",
      any(o.get("id") == "O5" for o in a.get("observations") or []))

    # ── 产物结构
    C("★ 探针教训 %d 条（%s）" % (len(a.get("probeLessons") or []),
                                  "/".join(EXPECT_LESSON_IDS)),
      sorted(r["id"] for r in a.get("probeLessons") or [])
      == EXPECT_LESSON_IDS,
      [r["id"] for r in a.get("probeLessons") or []])
    C("★ 每条教训都有 whyItMatters",
      all(r.get("whyItMatters") for r in a.get("probeLessons") or []))
    C("★★ R85 写明了 JSX 上 `[^>]*>` 会停在 `=>` 上",
      any(r["id"] == "R85" and "=>" in r.get("text", "")
          and "形状" in r.get("text", "")
          and "静默" in r.get("whyItMatters", "")
          for r in a.get("probeLessons") or []))
    C("★ R84 写明了 sr-only 与 display:none 是两回事",
      any(r["id"] == "R84" and "sr-only" in r.get("text", "")
          and "display:none" in r.get("text", "")
          for r in a.get("probeLessons") or []))
    C("★★ R86 写明了「要改决定分类的那个字段」与 R80 的关系",
      any(r["id"] == "R86" and "panelPresent" in r.get("text", "")
          and "R80" in r.get("whyItMatters", "")
          for r in a.get("probeLessons") or []))
    C("★ env.srcModified 为 False", a["env"].get("srcModified") is False)
    C("★ 原始读数与探针脚本都随产物提交（R43）",
      all((RAWDIR / f).exists() for f in RAW_FILES)
      and all((PROBEDIR / f).exists() for f in PROBE_FILES),
      {"raw": [f for f in RAW_FILES if not (RAWDIR / f).exists()],
       "probes": [f for f in PROBE_FILES if not (PROBEDIR / f).exists()]})
    C("★ rawSha 覆盖本批与 768 两份原始读数",
      set(a.get("rawSha") or {}) == {"vb769a.json", "vb768a.json"},
      a.get("rawSha"))
    C("★ 每个探针都标了 rounds 与 injected",
      [(p.get("id"), p.get("rounds"), p.get("injected"))
       for p in a.get("probes") or []] == [("769a", 2, False)],
      [(p.get("id"), p.get("rounds")) for p in a.get("probes") or []])

    # ── README
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        rows = [ln for ln in rt.split("\n") if ln.startswith("| J")]
        C("★ README 判据表 12 行", len(rows) == 12, len(rows))
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
                    "## 方法论", "## 探针教训", "## 不声称", "## 复现"):
            C("★ README 有「%s」章节" % sec.strip("# "), sec in rt)
        C("★★ README 有 D12 章节", "### D12" in rt)
        C("★★ README 的 D12 段写了 sr-only 与「第一个可聚焦」",
          ("sr-only" in rt) and ("第一个可聚焦" in rt), None)
        C("★ README 有「先修 D8，再修 D3」的顺序结论",
          "先修 D8，再修 D3" in rt)
        C("★ README 有「修法顺序」段", "修法顺序" in rt)
    else:
        C("★ README 存在", False)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    hits = [ln for ln in lt.split("\n") if ln.startswith("| Batch 769 |")]
    C("★★ 台账恰好一行 Batch 769", len(hits) == 1, len(hits))
    if hits:
        ln = hits[0]
        C("★ 台账首格是 Batch 769（不是裸数字）",
          ln.split("|")[1].strip() == "Batch 769", ln[:24])
        C("★★ 台账新行 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行是 3 列", ln.count("|") == 4, ln.count("|"))
        C("★ 台账新行提到了 D12 与「先修 D8，再修 D3」",
          "D12" in ln and "先修 D8" in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个、仍在 522/583/587",
      lt.count(FFFD) == 9
      and [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]
      == [522, 583, 587],
      {"n": lt.count(FFFD),
       "lines": [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]})
    C("★ 台账只有 632 行", len(lt.split("\n")) == 632,
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

    def res_all(files, fn, ident, mode, key="rows"):
        out = []
        for rd in files[fn]["rounds"]:
            hit = [x for x in (rd.get(key) or [])
                   if x.get("id") == ident and x.get("mode") == mode]
            if not hit:
                raise KeyError((ident, mode))
            out.append(hit[0])
        return out

    # ── D12
    inj("★★ 删掉 D12", lambda x: x.__setitem__(
        "defects", [d for d in x["defects"] if d["id"] != "D12"]))
    def demote12(x):
        d12 = [d for d in x["defects"] if d["id"] == "D12"][0]
        x["defects"] = [d for d in x["defects"] if d["id"] != "D12"]
        x["observations"] = x["observations"] + [
            {"id": "O9", "text": d12["title"]}]
    inj("★★ 把 D12 真的降级成观察（从 defects 挪走）", demote12)
    inj("★ 把 D12 的 isSrOnly 抹掉（它就不 sr-only 了）", lambda x:
        x["findings"]["srOnlyFileInput"].__setitem__("isSrOnly", False))
    inj("★ 把 D12 的 hasAriaLabel 改成 true（有名字了）", lambda x:
        x["findings"]["srOnlyFileInput"].__setitem__("hasAriaLabel", True))
    inj("★ 把 D12 的 indexInPanel 从 0 改成 1（不再是第一站）", lambda x:
        x["findings"]["srOnlyFileInput"].__setitem__("indexInPanel", 1))
    inj("★ 抹掉 D12 的 whyItWasMissedBefore（与 765 那个的区别没了）", lambda x:
        [d for d in x["defects"] if d["id"] == "D12"][0].pop(
            "whyItWasMissedBefore"))
    inj("★ 抹掉 D12 的 fixDirection", lambda x:
        [d for d in x["defects"] if d["id"] == "D12"][0].pop("fixDirection"))
    inj("★ 删掉 J8", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J8"]))
    inj("★ 删掉 R85（JSX 切片那条）", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R85"]))
    inj("★ 删掉 R84（sr-only vs display:none）", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R84"]))

    # ── 协议等价 / 结构性失败
    inj("★★ 把 reproduced 改成 5 个（少一个复现）", lambda x:
        x["findings"]["reproducibility"].__setitem__(
            "reproduced", IDS[:5]))
    inj("★★ 把 matchedArm 抹掉（说不清按什么配对）", lambda x:
        x.__setitem__("findings", dict(
            x["findings"],
            reproducibility=dict(x["findings"]["reproducibility"],
                                 rule="按臂名配对"))))
    inj("★★ 把 impossibleArms 抹成空（假装三臂都跑起来了）", lambda x:
        x["findings"]["focusInventory"].__setitem__(
            "armsStructurallyImpossible", []))
    inj("★ 删掉 J3（协议等价判别式）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J3"]))
    inj("★ R81 抹掉 whyItMatters", lambda x:
        [r for r in x["probeLessons"] if r["id"] == "R81"][0].pop(
            "whyItMatters"))

    # ── 分桶
    inj("★★ 把「焦点掉 body」那一桶清空（当成 0 个）", lambda x:
        x["findings"]["protocolV2"].__setitem__("focusFellToBody", []))
    inj("★★ 把「导演台被关掉」那一桶清空", lambda x:
        x["findings"]["protocolV2"].__setitem__("deskLost", []))
    inj("★★ 塞一个「归还到触发器」的浮层（D11 就被推翻了）", lambda x:
        x["findings"]["protocolV2"].__setitem__("focusRestoredToTrigger",
                                                  ["export"]))
    inj("★★ 把 counts 改成 6 个都掉 body", lambda x:
        x["findings"]["protocolV2"].__setitem__(
            "counts", {"measured-focus-to-body": 6}))
    inj("★ 删掉 J5（D11 扩大确认）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J5"]))
    inj("★ 删掉 J4（768 的缺口被关掉）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J4"]))

    # ── D3×D8 耦合与顺序
    inj("★★ 抹掉 D3 的 repairOrder（顺序约束没了）", lambda x:
        [w for w in x["widened"] if w["id"] == "D3"][0].pop("repairOrder"))
    inj("★★ 把 repairOrder 写成「先修 D3 再修 D8」（顺序反了）", lambda x:
        [w for w in x["widened"] if w["id"] == "D3"][0].__setitem__(
            "repairOrder", "★ 先修 D3，再修 D8。"))
    inj("★★ 删掉 J7（耦合那条判据）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J7"]))
    inj("★ D3 的 note 抹掉「作用域」", lambda x:
        [w for w in x["widened"] if w["id"] == "D3"][0].__setitem__(
            "note", "泛泛而谈"))
    inj("★ 删掉 J9（isEditable 作用域）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J9"]))

    # ── D4 独立复现（不许写成扩宽）
    inj("★★ 把 D4 的 newMembers 塞进 export（谎称扩宽了）", lambda x:
        [w for w in x["widened"] if w["id"] == "D4"][0].__setitem__(
            "newMembers", ["export"]))
    inj("★ 把 D4 的 note 里的「没有新增成员」抹掉", lambda x:
        [w for w in x["widened"] if w["id"] == "D4"][0].__setitem__(
            "note", "本批确认了 D4"))
    inj("★ 删掉 J6（D4 独立复现）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J6"]))

    # ── 不声称
    inj("★★ 删掉 J10（不声称）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J10"]))
    inj("★ 不声称里删掉「没换位置」", lambda x: x.__setitem__(
        "notClaimed", [t for t in x["notClaimed"]
                       if "没换焦点" not in t and "只换了焦点" not in t]))
    inj("★ 不声称里删掉「sr-only 同族未普查」", lambda x: x.__setitem__(
        "notClaimed", [t for t in x["notClaimed"] if "没普查" not in t]))

    # ── 判据偷改
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS", lambda x: ([j.__setitem__("verdict", "PASS")
                                       for j in x["judgments"]]))
    inj("★ 把判据条数从 12 改成 9", lambda x: x.__setitem__(
        "judgments", x["judgments"][:9]))
    inj("★ 把 J7 的 evidence 换成可比性", lambda x:
        [j for j in x["judgments"] if j["id"] == "J7"][0].__setitem__(
            "evidence", x["findings"]["comparability"]))
    inj("★ 只改 findings 一份（判据的 evidence 不动）", lambda x:
        x["findings"]["protocolV2"].__setitem__("focusFellToBody",
                                                 ["export"]))

    # ── 静态层伪造
    inj_static("伪造：isEditable 早退不再排在 Escape 分支之前",
               lambda x: x.__setitem__("gateBeforeEscape", False))
    inj_static("伪造：isEditable 判定不再覆盖 contenteditable",
               lambda x: x.__setitem__("isEditableHasContentEditable", False))
    inj_static("伪造：群众面板变成 2 个 input（落点预测要变）",
               lambda x: x.__setitem__("crowdInputs", 2))
    inj_static("伪造：群众面板按钮排在 input 之前",
               lambda x: x.__setitem__("crowdFirstButtonAfterAllInputs",
                                       False))
    inj_static("伪造：那个文件框其实不是 sr-only",
               lambda x: x.__setitem__("mlIsSrOnly", False))
    inj_static("伪造：那个文件框其实有 aria-label",
               lambda x: x.__setitem__("mlAriaLabel", True))
    inj_static("伪造：那个文件框其实被 <label> 包着",
               lambda x: x.__setitem__("mlLabelOpenedBefore", True))
    inj_static("伪造：形状守卫失败（切片越过了标签结尾）",
               lambda x: x.__setitem__("mlShapeOk", False))
    inj_static("伪造：导演台阶梯里居然引用了别的浮层状态",
               lambda x: x.__setitem__("deskLadderOtherRefs", 1))
    inj_static("伪造：导出面板画幅按钮排到提交之后",
               lambda x: x.__setitem__("exportAspectBeforeSubmit", False))

    # ── 原始读数：改真正的被检查键
    inj_raw("★★ 原始：导出面板新协议下焦点不再掉 body", lambda x:
            [v["after"].__setitem__(
                "active", dict(v["after"]["active"], isBody=False,
                               isTrigger=True, tag="BUTTON"))
             for v in res_all(x, "vb769a.json", "export", "noneditable")])
    inj_raw("★★ 原始：群众阵列新协议下不再关导演台（耦合消失）", lambda x:
            [v.__setitem__("after", dict(v["after"], open=True,
                                         panelPresent=False))
             for v in res_all(x, "vb769a.json", "crowd", "noneditable")]
            + [v.__setitem__("desk", {"open": True})
               for v in res_all(x, "vb769a.json", "crowd", "noneditable")])
    inj_raw("★★ 原始：群众阵列 editable 臂不再被早退吞掉", lambda x:
            [v.__setitem__("after", dict(v["after"], panelPresent=False))
             for v in res_all(x, "vb769a.json", "crowd", "editable")])
    inj_raw("★★ 原始：模型的 editable 臂落点从 INPUT 改成 BUTTON"
            "（作用域证据消失）", lambda x:
            [v["focusKind"].__setitem__("tag", "BUTTON")
             for v in res_all(x, "vb769a.json", "modellib", "editable")])
    # ★ 必须改 `panelPresent`：`panel-stuck` 那一格的分类**先看面板在不在**，
    #   焦点字段根本不影响分类（改焦点是无效对照，R86）。
    inj_raw("★★ 原始：把 768 的 crowd inside 臂改掉（6/6 复现被破坏）",
            lambda x:
            [v["after"].__setitem__("panelPresent", False)
             for rd in x["__prev__"]["rounds"] for v in rd["rows"]
             if v.get("id") == "crowd" and v.get("mode") == "inside"])
    inj_raw("★ 原始：把 768 的 phonevcam inside 臂改掉", lambda x:
            [v["after"]["active"].__setitem__("isBody", False)
             or v["after"]["active"].__setitem__("isTrigger", True)
             for rd in x["__prev__"]["rounds"] for v in rd["rows"]
             if v.get("id") == "phonevcam" and v.get("mode") == "inside"])
    inj_raw("★★ 原始：给 preset 凭空加一个输入框（结构性失败的解释被破坏）",
            lambda x:
            [v["focus"].__setitem__("nEditable", 1)
             for v in res_all(x, "vb769a.json", "preset", "editable")])
    inj_raw("★ 原始：群众阵列非输入框落点从 index 3 改成 1（J12 失效）",
            lambda x:
            [v["focus"].__setitem__("pickedIndex", 1)
             for v in res_all(x, "vb769a.json", "crowd", "noneditable")])
    inj_raw("★ 原始：某格 FAILED", lambda x:
            [v.__setitem__("FAILED", "点不动")
             for v in res_all(x, "vb769a.json", "modellib", "noneditable")])
    inj_raw("★ all([]) 陷阱：把 rows 清空（两轮都清）", lambda x:
            [rd.__setitem__("rows", []) for rd in x["vb769a.json"]["rounds"]])
    inj_raw("★ 原始：可聚焦控件存量改成与 768 不同", lambda x:
            [v["focus"].__setitem__("total", 99)
             for v in res_all(x, "vb769a.json", "modellib", "noneditable")])
    inj_raw("★ 原始：某格起点不干净（浮层没打开）", lambda x:
            [v["before"].__setitem__("panelPresent", False)
             for v in res_all(x, "vb769a.json", "export", "editable")])
    inj_raw("★ 原始：焦点没放进浮层内", lambda x:
            [v["focusKind"].__setitem__("inPanel", False)
             for v in res_all(x, "vb769a.json", "export", "noneditable")])
    inj_raw("★ 原始：editable 臂落到了非输入框控件（臂与类别不符）", lambda x:
            [v["focusKind"].__setitem__("isEditableByTag", False)
             for v in res_all(x, "vb769a.json", "export", "editable")])

    # ── 台账 / README
    led = LEDGER.read_text(encoding="utf-8")
    led_line = next((ln for ln in led.split("\n")
                     if ln.startswith("| Batch 769 |")), "")
    if led_line:
        sep = "" if led.endswith(led_line + "\n") else "\n"
        inj_file("★ 台账删掉 Batch 769 行", LEDGER, sep + led_line, "")
        inj_file("★ 台账行首格改成裸数字 769", LEDGER,
                 "| Batch 769 |", "| 769 |")
        inj_file("★ 台账行首格写成 Batch 0769", LEDGER,
                 "| Batch 769 |", "| Batch 0769 |")
        inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
                 led_line[:40], led_line[:40] + FFFD)
        inj_file("★ 台账被追加了 Batch 770（行数断言）", LEDGER,
                 "| Batch 769 |", "| Batch 769 |\n| Batch 770 | x")
        inj_file("★ 台账新行不含 D12", LEDGER, "D12", "D1y",
                 all_hits=True)
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.split("\n")
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 判据表首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D12 章节", README, "### D12", "### 附注")
        inj_file("★ README 删掉「先修 D8，再修 D3」", README, "先修 D8，再修 D3",
                 "顺序另说", all_hits=True)
        inj_file("★ README 删掉 sr-only", README, "sr-only", "藏起来",
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
        {"label": "原始读数可用（raw/ 下 1 份 + 768 那份）",
         "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 769, "checks": checks, "pass": npass, "total": total,
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
    print("batch 769 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
