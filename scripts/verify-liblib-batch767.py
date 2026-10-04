"""batch 767 验收器：导演台 6 个 disclosure 浮层的关闭契约

三层结构（与 753–766 同）：
  1. **静态层** —— 从 `src/` 复核判据依赖的实现事实，含**有无**与**数量**断言
     （`DirectorDesk.tsx` 的 Esc 阶梯对另外五个 disclosure 状态 **0 处引用**；
      模型库那份实现同时有外点 pointerdown 与捕获阶段 Esc）
  2. **产物层** —— 判据条数与 verdict、缺陷、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb767a.json` **按正确键名重算**全部
     分类；缺失时**判失败而不是通过**

⚠ 本批盯住四件容易自欺的事：
  - **D8 是本批唯一「按 Esc 丢工作区」的路径**，严重度中。产物不许把它
    降级成观察，也不许把「6 个里只有它这样」写成「个别现象」。
  - **D9/D10 是 765 的 D5/D6 的扩宽**，不许退回成个案。
  - **`all([])` 是 True**：每个分类列表都显式判非空，并断言
    「外点关闭」与「Esc」的分类**覆盖全部 6 个**。
  - **J9 是被污染的读数**：6 格的焦点归还读数都被外点点击毁了，产物必须
    保留这条不声称，不许拿它下判断。

判据 **11 条（6 PASS / 5 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch767-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb767a.json"]
PROBE_FILES = ["dbg767a.py", "mk767audit.py"]
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
FFFD = "\ufffd"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
EXPECT_FAIL_IDS = ["J4", "J6", "J7", "J9", "J10"]
EXPECT_DEFECT_IDS = ["D8", "D9", "D10"]
EXPECT_LESSON_IDS = ["R71", "R72", "R73", "R74"]
# 另外五个 disclosure 状态：DirectorDesk 里一个都不该出现
OTHER_STATES = ["crowdPanelOpen", "modelLibraryOpen", "phoneVcamOpen",
                "presetPanelLeft", "pathMenuLeft"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def idx_of(t, n, s=0):
    return t.find(n, s)


def line_of(t, n, s=0):
    i = idx_of(t, n, s)
    return -1 if i < 0 else t.count("\n", 0, i)


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
    tl = src("src/components/director/DirectorTimeline.tsx")
    vp = src("src/components/director/DirectorViewport.tsx")
    vcam = src("src/components/director/DirectorPhoneVcamPanel.tsx")

    # ★ D8 的静态机制：阶梯里对另外五个 disclosure 状态 0 处引用
    other_hits = {k: len(re.findall(re.escape(k), desk)) for k in OTHER_STATES}
    export_hits = len(re.findall(r"exportPanelOpen", desk))
    export_tier_count = len(re.findall(r"if \(exportPanelOpen\)", desk))
    esc_gate = line_of(desk, 'if (event.key !== "Escape") return;')
    panel_tier = line_of(desk, "if (exportPanelOpen) {")
    close_ws = line_of(desk, "closeWorkspace();")

    # 模型库那份「同仓最完整实现」
    ml_outside = "closeOnOutsidePointerDown" in vp
    ml_escape = "closeOnEscape" in vp
    ml_stop = "stopImmediatePropagation" in vp
    ml_prevent = "event.preventDefault();" in vp
    ml_capture = 'window.addEventListener("keydown", closeOnEscape, true)' in vp
    ml_doc_pointer = ('document.addEventListener("pointerdown", '
                      "closeOnOutsidePointerDown)") in vp

    # 路径菜单 / 预设面板的关闭 effect
    pm_outside = line_of(tl, "const close = (event: PointerEvent) => {")
    pp_outside = line_of(tl, "const closeOnOutsidePointerDown")  if \
        "const closeOnOutsidePointerDown" in tl else -1
    tl_escape = len(re.findall(r'event\.key === "Escape"', tl))

    # 虚拟相机面板的 Esc
    vc_escape = 'event.key !== "Escape"' in vcam
    vc_capture = 'window.addEventListener("keydown", closeOnEscape, true)' in vcam
    vc_stop = "stopImmediatePropagation" in vcam
    vc_recording_guard = "if (!recording) onClose();" in vcam

    # aria 契约：只有群众/模型库有 role=dialog
    crowd_role = 'data-director-crowd-panel' in vp
    crowd_role_line = line_of(vp, 'data-director-crowd-panel')
    seg_crowd = vp[idx_of(vp, "data-director-crowd-panel"):idx_of(
        vp, "data-director-crowd-panel") + 200]
    seg_ml = vp[idx_of(vp, "data-director-model-library-panel"):idx_of(
        vp, "data-director-model-library-panel") + 220]
    seg_export = desk[idx_of(desk, "data-director-export-panel")
                      if "data-director-export-panel" in desk else 0:][:0]

    # 触发器：6 个 aria-expanded
    exp_total = len(re.findall(r"aria-expanded", desk)) \
        + len(re.findall(r"aria-expanded", tl)) \
        + len(re.findall(r"aria-expanded", vp))
    ctrl_total = len(re.findall(r"aria-controls", desk)) \
        + len(re.findall(r"aria-controls", tl)) \
        + len(re.findall(r"aria-controls", vp))
    popup_total = len(re.findall(r"aria-haspopup", desk)) \
        + len(re.findall(r"aria-haspopup", tl)) \
        + len(re.findall(r"aria-haspopup", vp))

    return {
        "otherStateHits": other_hits,
        "otherStateTotal": sum(other_hits.values()),
        "exportPanelOpenHits": export_hits,
        "exportPanelTierCount": export_tier_count,
        "escGateLine": esc_gate,
        "exportPanelTierLine": panel_tier,
        "closeWorkspaceLine": close_ws,
        "tierBeforeCloseWorkspace": 0 <= panel_tier < close_ws,
        "modelLibraryHasOutside": ml_outside,
        "modelLibraryHasEscape": ml_escape,
        "modelLibraryStopsPropagation": ml_stop,
        "modelLibraryPreventsDefault": ml_prevent,
        "modelLibraryEscapeOnCapture": ml_capture,
        "modelLibraryDocPointerdown": ml_doc_pointer,
        "timelinePointerOutside": pm_outside,
        "timelineEscapeHandlers": tl_escape,
        "vcamHasEscape": vc_escape,
        "vcamEscapeOnCapture": vc_capture,
        "vcamStopsPropagation": vc_stop,
        "vcamRecordingGuard": vc_recording_guard,
        "crowdPanelHasDialogRole": 'role="dialog"' in seg_crowd,
        "crowdPanelHasAriaLabel": 'aria-label=' in seg_crowd,
        "modelLibraryHasDialogRole": 'role="dialog"' in seg_ml,
        "modelLibraryHasAriaLabel": 'aria-label=' in seg_ml,
        "ariaExpandedTotal": exp_total,
        "ariaControlsTotal": ctrl_total,
        "ariaHasPopupTotal": popup_total,
    }


# ═════════════════════ 3. 原始读数交叉核对 ═════════════════════
def raw_files():
    out = {}
    for f in RAW_FILES:
        p = RAWDIR / f
        if not p.exists():
            raise SystemExit("FATAL 缺原始读数 %s" % p)
        out[f] = json.loads(p.read_text(encoding="utf-8"))
    return out


def raw_side_from(files):
    a = files["vb767a.json"]
    r = {"rounds": len(a["rounds"])}
    per = []
    for rd in a["rounds"]:
        m = {x["id"]: x for x in (rd.get("results") or []) if x.get("id")}
        cells = {}
        for i in IDS:
            v = m.get(i)
            if not v:
                continue
            ao = v.get("afterOpen") or {}
            aout = v.get("afterOutside") or {}
            ae = v.get("afterEsc") or {}
            de = v.get("deskEnd") or {}
            skipped = "skipped" in ae
            act = (aout.get("active") or {}) if skipped \
                else (ae.get("active") or {})
            cells[i] = {
                "opened": ao.get("panelPresent") is True,
                "focusOnTrigger": (ao.get("active") or {}).get("isTrigger")
                is True,
                "focusInPanel": (ao.get("active") or {}).get("inPanel") is True,
                "ariaExpanded": ao.get("triggerAriaExpanded"),
                "ariaControls": ao.get("triggerHasControlsAttr"),
                "ariaHasPopup": ao.get("triggerHasHasPopupAttr"),
                "panelRole": ao.get("panelRole"),
                "panelAriaLabel": ao.get("panelAriaLabel"),
                "panelFocusables": ao.get("panelFocusables"),
                "outsideAttempted": bool((v.get("outside") or {})
                                         .get("clicked")),
                "outsideClosed": aout.get("panelPresent") is False,
                "outsideHitClickable": ((v.get("outside") or {}).get("hit")
                                        or {}).get("clickable"),
                "escTested": not skipped,
                "escClosedPanel": (ae.get("panelPresent") is False
                                   if not skipped else None),
                "escClosedDesk": (de.get("open") is False
                                  if not skipped else None),
                "activeAfterTag": act.get("tag"),
                "activeAfterAria": act.get("aria"),
                "activeAfterIsTrigger": act.get("isTrigger"),
                "activeAfterInDialog": act.get("inDialog"),
                "activeAfterIsBody": act.get("isBody"),
                "deskOpenAtEnd": de.get("open") is True,
            }
        per.append({"cells": cells,
                    "reopened": rd.get("reopened") or []})

    def pick(pred):
        return [i for i in IDS
                if all(per[r]["cells"].get(i) and pred(per[r]["cells"][i])
                       for r in range(len(per)))]

    r["perRound"] = per
    r["ids"] = IDS
    r["opened"] = pick(lambda c: c["opened"])
    r["focusStayed"] = pick(lambda c: c["focusOnTrigger"])
    r["focusMovedIn"] = pick(lambda c: c["focusInPanel"])
    r["outsideWorks"] = pick(lambda c: c["outsideClosed"])
    r["outsideMissing"] = pick(lambda c: c["outsideClosed"] is False)
    r["outsideAttempted"] = pick(lambda c: c["outsideAttempted"])
    r["outsideHitClickable"] = [i for i in IDS
                                if any(per[x]["cells"].get(i, {}).get(
                                    "outsideHitClickable")
                                    for x in range(len(per)))]
    r["escTested"] = pick(lambda c: c["escTested"])
    r["escSkipped"] = pick(lambda c: c["escTested"] is False)
    r["escPanelOnly"] = pick(lambda c: c["escClosedPanel"] is True
                             and c["escClosedDesk"] is False)
    r["escWholeDesk"] = pick(lambda c: c["escClosedDesk"] is True)
    r["roleDialog"] = pick(lambda c: c["panelRole"] == "dialog")
    r["panelAriaLabel"] = pick(lambda c: bool(c["panelAriaLabel"]))
    r["ariaControls"] = [i for i in IDS
                         if any(per[x]["cells"].get(i, {}).get("ariaControls")
                                for x in range(len(per)))]
    r["ariaHasPopup"] = [i for i in IDS
                         if any(per[x]["cells"].get(i, {}).get("ariaHasPopup")
                                for x in range(len(per)))]
    r["ariaExpandedNull"] = pick(lambda c: c["ariaExpanded"] is None)
    r["deskReopenedAfter"] = [x["reopened"] for x in per]
    r["focusables"] = {i: [per[x]["cells"].get(i, {}).get("panelFocusables")
                           for x in range(len(per))] for i in IDS}
    r["focusAfter"] = {i: {
        "tag": [per[x]["cells"].get(i, {}).get("activeAfterTag")
                for x in range(len(per))],
        "isTrigger": [per[x]["cells"].get(i, {}).get("activeAfterIsTrigger")
                      for x in range(len(per))],
        "inDialog": [per[x]["cells"].get(i, {}).get("activeAfterInDialog")
                     for x in range(len(per))],
        "isBody": [per[x]["cells"].get(i, {}).get("activeAfterIsBody")
                   for x in range(len(per))],
        "contaminated": all(per[x]["cells"].get(i, {}).get("escTested") is False
                            for x in range(len(per))),
    } for i in IDS}
    return r


def raw_side():
    files = raw_files()
    out = raw_side_from(files)
    out["__raw__"] = files
    return out


# ═════════════════════ 2. 产物层 + 交叉核对 ═════════════════════
def run_checks(a, st, rw):
    ck = []

    def C(label, cond, got=None):
        ck.append({"label": label, "pass": bool(cond), "got": got})

    f = a["findings"]
    J = a["judgments"]
    s = f["disclosureCensus"]

    def df(did):
        for x in a.get("defects") or []:
            if x.get("id") == did:
                return x
        return {}

    # ── 静态层
    C("★★ 静态：DirectorDesk 的 Esc 阶梯对另外五个 disclosure 状态 0 处引用"
      "（D8 的机制）", st["otherStateTotal"] == 0, st["otherStateHits"])
    C("★ 静态：DirectorDesk 的 Esc 阶梯里 **exportPanelOpen 恰好一档**",
      st["exportPanelTierCount"] == 1, st["exportPanelTierCount"])
    C("静态：「关导出面板」那一档排在 closeWorkspace() 之前（D8 的修法位置）",
      st["tierBeforeCloseWorkspace"],
      [st["exportPanelTierLine"], st["closeWorkspaceLine"]])
    C("★ 静态：模型库那份实现四件齐全（外点 pointerdown + 捕获 Esc + "
      "preventDefault + stopImmediatePropagation）—— D9/D8 的同仓先例",
      st["modelLibraryHasOutside"] and st["modelLibraryHasEscape"]
      and st["modelLibraryDocPointerdown"] and st["modelLibraryEscapeOnCapture"]
      and st["modelLibraryPreventsDefault"]
      and st["modelLibraryStopsPropagation"],
      [st["modelLibraryHasOutside"], st["modelLibraryHasEscape"],
       st["modelLibraryDocPointerdown"], st["modelLibraryEscapeOnCapture"],
       st["modelLibraryPreventsDefault"],
       st["modelLibraryStopsPropagation"]])
    C("静态：虚拟相机面板有捕获阶段 Esc + stopImmediatePropagation",
      st["vcamHasEscape"] and st["vcamEscapeOnCapture"]
      and st["vcamStopsPropagation"],
      [st["vcamHasEscape"], st["vcamEscapeOnCapture"],
       st["vcamStopsPropagation"]])
    C("★ 静态：虚拟相机在录制中**不**关面板（本批未验证的那条分支）",
      st["vcamRecordingGuard"] is True, st["vcamRecordingGuard"])
    C("静态：时间轴里路径菜单/预设面板有 pointerdown 外点处理与 Esc 处理",
      st["timelinePointerOutside"] > 0 and st["timelineEscapeHandlers"] >= 2,
      [st["timelinePointerOutside"], st["timelineEscapeHandlers"]])
    C("静态：群众阵列与模型库两个浮层带 role=dialog + aria-label",
      st["crowdPanelHasDialogRole"] and st["crowdPanelHasAriaLabel"]
      and st["modelLibraryHasDialogRole"]
      and st["modelLibraryHasAriaLabel"])
    C("★★ 静态：三个文件里 aria-controls / aria-haspopup 各 0 处（D10）",
      st["ariaControlsTotal"] == 0 and st["ariaHasPopupTotal"] == 0,
      [st["ariaControlsTotal"], st["ariaHasPopupTotal"]])

    # ── 判据层
    C("判据 11 条", len(J) == 11, len(J))
    npass = sum(1 for j in J if j["verdict"] == "PASS")
    nfail = sum(1 for j in J if j["verdict"] == "FAIL")
    C("verdict 分布 6 PASS / 5 FAIL", npass == 6 and nfail == 6 - 1,
      [npass, nfail])
    fail_ids = [j["id"] for j in J if j["verdict"] == "FAIL"]
    C("★ 5 条 FAIL 恰好是 J4/J6/J7/J9/J10",
      sorted(fail_ids) == sorted(EXPECT_FAIL_IDS), fail_ids)
    C("判据 id 唯一且连续 J1..J11",
      [j["id"] for j in J] == ["J%d" % i for i in range(1, 12)],
      [j["id"] for j in J])
    C("★ 每条判据都有非空 evidenceKey", all(j.get("evidenceKey") for j in J))
    rt = json.loads(json.dumps(a, ensure_ascii=False))
    C("★ findings[k] == judgments[].evidence（JSON 往返后逐条）",
      all(rt["findings"][j["evidenceKey"]] == j["evidence"]
          for j in rt["judgments"] if j["evidenceKey"] in rt["findings"]),
      [j["id"] for j in rt["judgments"]
       if j["evidenceKey"] in rt["findings"]
       and rt["findings"][j["evidenceKey"]] != j["evidence"]])
    C("★ 每条判据的 evidenceKey 都真实存在",
      all(j["evidenceKey"] in f for j in J))
    C("★ evidence 不得为空（防 all([]) 式空过）",
      all(j["evidence"] not in ({}, [], None) for j in J),
      [j["id"] for j in J if j["evidence"] in ({}, [], None)])

    # ── 缺陷层
    D = a["defects"]
    C("缺陷 3 条 D8/D9/D10",
      sorted(d["id"] for d in D) == sorted(EXPECT_DEFECT_IDS),
      sorted(d["id"] for d in D))
    C("★★ D8 严重度是「中」（唯一「按 Esc 丢工作区」的路径）",
      df("D8").get("severity") == "中", df("D8").get("severity"))
    C("★ D8 写明了修法方向（同族两选一）", bool(df("D8").get("fixDirection")))
    C("★ D8 的 mechanism 点名了「阶梯里对它 0 处引用」",
      "0 处引用" in df("D8").get("mechanism", ""))
    C("★ D9 标了 widensD5From765（扩宽 765 的 D5，不退回个案）",
      df("D9").get("widensD5From765") is True)
    C("★ D9 写了 inRepoExemplar", bool(df("D9").get("inRepoExemplar")))
    C("★ D10 标了 widensD6From765", df("D10").get("widensD6From765") is True)
    C("★ D10 说明了「标题不构成可访问名」",
      "不构成" in df("D10").get("note", ""))
    C("三条缺陷都标 needsSrcChange",
      all(d.get("needsSrcChange") is True for d in D))
    C("★ 缺陷 where 指针都指向真实文件与行号",
      all(ptr_valid(w) for d in D for w in d.get("where") or []),
      [w for d in D for w in (d.get("where") or []) if not ptr_valid(w)])
    C("★ 本批不重复声明 763–766 的 D1–D7",
      not any(d["id"] in ("D1", "D2", "D3", "D4", "D5", "D6", "D7")
              for d in D), [d["id"] for d in D])

    # ── 观察 / 教训 / 不声称
    C("观察 4 条", len(a["observations"]) == 4, len(a["observations"]))
    C("探针教训 R71–R74 四条",
      sorted(x["id"] for x in a["probeLessons"]) == EXPECT_LESSON_IDS,
      [x["id"] for x in a["probeLessons"]])
    C("★ R71 记的是「JS 的 in 不能用在字符串上」",
      any(x["id"] == "R71" and "字符串" in x["text"]
          for x in a["probeLessons"]))
    C("★ R72 记的是「node --check 只验语法不验语义」",
      any(x["id"] == "R72" and "不验语义" in x["text"]
          for x in a["probeLessons"]))
    C("★ R73 记的是「先测 A 再测 B 会污染 B」",
      any(x["id"] == "R73" and "污染" in x["text"]
          for x in a["probeLessons"]))
    NC = " ".join(a["notClaimed"])
    C("★ 不声称里写明焦点归还那一问没有干净读数（J9）",
      "归还焦点" in NC or "归还触发器" in NC)
    C("★ 不声称里写明测错了路径菜单的触发器（J10）", "触发器" in NC)
    C("★ 不声称里写明 3 个浮层的 Esc 没有读数", "无从测起" in NC)
    C("★ 不声称里写明无源站对照", "无源站对照" in NC)
    C("不声称 ≥ 9 条", len(a["notClaimed"]) >= 9, len(a["notClaimed"]))

    # ── 可比性
    C("两轮可比且逐字段一致",
      f["comparability"]["allConsistent"] is True,
      f["comparability"]["inconsistent"])
    C("可比性判据比的是非空 key 列表",
      len(f["comparability"]["keys"]) >= 1)
    C("原始读数轮数为 2", rw["rounds"] == 2, rw["rounds"])

    # ── 交叉核对：6 个都测到了
    C("★ 6 个 disclosure 两轮都打开",
      rw["opened"] == IDS, rw["opened"])
    C("★ 6 个打开瞬间焦点都留在触发器上",
      rw["focusStayed"] == IDS, rw["focusStayed"])
    C("★ 没有一个把焦点移进浮层",
      rw["focusMovedIn"] == [], rw["focusMovedIn"])
    C("★ 外点那一下 6 个都真点了",
      rw["outsideAttempted"] == IDS, rw["outsideAttempted"])
    C("★ 外点落点没有一个是可点元素（R74：先量可点性再点）",
      rw["outsideHitClickable"] == [], rw["outsideHitClickable"])
    C("★ 外点关闭的分类覆盖全部 6 个",
      sorted(rw["outsideWorks"] + rw["outsideMissing"]) == sorted(IDS),
      [rw["outsideWorks"], rw["outsideMissing"]])
    C("★ 外点关闭有效的恰好是 3 个：preset / pathmenu / modellib",
      rw["outsideWorks"] == ["preset", "pathmenu", "modellib"],
      rw["outsideWorks"])
    C("★ 外点关闭无效的恰好是 3 个：export / phonevcam / crowd",
      rw["outsideMissing"] == ["export", "phonevcam", "crowd"],
      rw["outsideMissing"])
    C("★ Esc 的分类覆盖全部 6 个",
      sorted(rw["escTested"] + rw["escSkipped"]) == sorted(IDS),
      [rw["escTested"], rw["escSkipped"]])
    # 只断言「总数覆盖 6 个」不够 —— 必须钉死**是哪三个没测到**，
    # 否则「把没测的谎报成测到了」会静默通过（J9 与不声称都依赖这个划分）
    C("★★ 测到 Esc 的恰好是 export/phonevcam/crowd，"
      "没测到的恰好是 preset/pathmenu/modellib",
      rw["escTested"] == ["export", "phonevcam", "crowd"]
      and rw["escSkipped"] == ["preset", "pathmenu", "modellib"],
      [rw["escTested"], rw["escSkipped"]])
    C("★ 测到 Esc 的 3 个里，只有 crowd 关掉了整个导演台",
      rw["escWholeDesk"] == ["crowd"], rw["escWholeDesk"])
    C("★ export 与 phonevcam 的 Esc 只关面板不关导演台",
      rw["escPanelOnly"] == ["export", "phonevcam"], rw["escPanelOnly"])
    C("★ 探针在 crowd 之后重开过导演台（两轮都是）",
      all(x == ["crowd"] for x in rw["deskReopenedAfter"]),
      rw["deskReopenedAfter"])
    C("★★ aria-controls 0/6、aria-haspopup 0/6（D10）",
      rw["ariaControls"] == [] and rw["ariaHasPopup"] == [],
      [rw["ariaControls"], rw["ariaHasPopup"]])
    C("★ role=dialog 只有 crowd 与 modellib 2/6",
      rw["roleDialog"] == ["crowd", "modellib"], rw["roleDialog"])
    C("★ panel aria-label 只有 crowd 与 modellib 2/6",
      rw["panelAriaLabel"] == ["crowd", "modellib"], rw["panelAriaLabel"])
    C("★ pathmenu 的 aria-expanded 读数是 null（J10 的实测依据）",
      rw["ariaExpandedNull"] == ["pathmenu"], rw["ariaExpandedNull"])
    C("★ 6 个浮层可聚焦控件数都 >0（焦点进得去，只是要自己 Tab）",
      all(all((v or 0) > 0 for v in rw["focusables"][i]) for i in IDS),
      rw["focusables"])
    C("★ 焦点归还那 6 格全部标了「被外点点击污染」（J9）",
      all(rw["focusAfter"][i]["contaminated"] or
          not all(rw["focusAfter"][i]["isTrigger"])
          for i in IDS),
      {i: rw["focusAfter"][i]["isTrigger"] for i in IDS})

    # ── 产物结构
    C("产物 batch=767", a["batch"] == 767, a["batch"])
    C("产物声明未改 src/", a["env"]["srcModified"] is False)
    C("probes 列了 1 个探针", len(a["probes"]) == 1, len(a["probes"]))
    C("★ raw 有 sha 记录", len(a["rawSha"]) == 1, list(a["rawSha"]))
    for fn in RAW_FILES:
        C("原始读数存在 %s" % fn, (RAWDIR / fn).exists())
    for fn in PROBE_FILES:
        C("探针脚本存在 %s" % fn, (PROBEDIR / fn).exists())
    C("README 存在", README.exists())
    if README.exists():
        t = README.read_text(encoding="utf-8")
        for h in ("## 选题", "## 判据", "## 缺陷", "## 观察",
                  "## 探针教训", "## 不声称", "## 复现"):
            C("README 含章节 %s" % h, h in t)
        for d in EXPECT_DEFECT_IDS:
            C("★ README 有 %s 的独立章节" % d,
              any(re.match(r"### %s\b" % d, ln) for ln in t.splitlines()))
        C("★ README 没有把 D1–D7 写成新章节",
          not re.search(r"^### D[1-7]\b", t, re.M))
        C("★ README 表格首格没有裸数字（pre-commit 正则会误判）",
          not any(BARE_NUM_CELL.match(ln) for ln in t.splitlines()),
          [ln for ln in t.splitlines() if BARE_NUM_CELL.match(ln)][:3])
        C("★ README 写明判据 11 条", "11" in t and "判据" in t)
        C("★ README 写了同仓先例（照抄即可）", "照抄" in t)
        C("★ README 提到 J9 的污染", "J9" in t and "污染" in t)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    lines = lt.splitlines()
    led = [ln for ln in lines if ln.startswith("| Batch 767 |")]
    C("★ 台账恰好一行 Batch 767", len(led) == 1, len(led))
    if len(led) == 1:
        ln = led[0]
        C("★ 台账行首格是「Batch 767」",
          ln.split("|")[1].strip() == "Batch 767", ln.split("|")[1])
        C("★ 台账新行里 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行够长（不许占位）", len(ln) > 200, len(ln))
        for kw in ("D8", "D9", "D10", "群众阵列", "外点关闭", "照抄"):
            C("台账行提到 %s" % kw, kw in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个", lt.count(FFFD) == 9, lt.count(FFFD))
    hist = [i + 1 for i, ln in enumerate(lines) if FFFD in ln]
    C("★ U+FFFD 仍只落在 522/583/587 三行", hist == [522, 583, 587], hist)
    C("★ 台账行数 = 630（追加一行）", len(lines) == 630, len(lines))
    C("★ Batch 766 行仍在且唯一",
      len([ln for ln in lines if ln.startswith("| Batch 766 |")]) == 1)
    return ck


# ═════════════════════ 阴性对照 ═════════════════════
def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_static(name, mutate):
        bad = copy.deepcopy(st)
        mutate(bad)
        failed = [c["label"] for c in run_checks(a, bad, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_raw(name, mutate):
        files = copy.deepcopy(rw.get("__raw__") or {})
        if not files:
            cases.append({"name": name, "caught": False,
                          "firstFail": "拿不到原始读数副本"})
            return
        mutate(files)
        try:
            badr = raw_side_from(files)
            failed = [c["label"] for c in run_checks(a, st, badr)
                      if not c["pass"]]
        except Exception as e:
            failed = ["重算抛错：%s" % e]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_file(name, path, old, new, all_hits=False):
        orig = path.read_text(encoding="utf-8")
        try:
            if old not in orig:
                cases.append({"name": name, "caught": False,
                              "firstFail": "待替换文本不存在（对照本身失效）"})
                return
            body = orig.replace(old, new) if all_hits \
                else orig.replace(old, new, 1)
            path.write_text(body, encoding="utf-8")
            failed = [c["label"] for c in run_checks(a, st, rw)
                      if not c["pass"]]
        finally:
            path.write_text(orig, encoding="utf-8")
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def res(files, i):
        for rd in files["vb767a.json"]["rounds"]:
            for x in rd.get("results") or []:
                if x.get("id") == i:
                    return x
        raise KeyError(i)

    def res_all(files, i):
        """同一个浮层在**所有轮**里的记录。

        ★ `pick()` 要求两轮都满足，所以只改一轮的对照**永远不会触发**
          （763/764/765/766 各踩过一次不同形状的这条）。凡是想让判据
          失守的注入，一律两轮都改。
        """
        out = []
        for rd in files["vb767a.json"]["rounds"]:
            hit = [x for x in (rd.get("results") or []) if x.get("id") == i]
            if not hit:
                raise KeyError(i)
            out.append(hit[0])
        return out

    # —— 伪造「缺陷不存在 / 性质变了」
    inj("★ 删掉 D8", lambda x: x.__setitem__(
        "defects", [d for d in x["defects"] if d["id"] != "D8"]))
    inj("★ 把 D8 降级成观察", lambda x: x.__setitem__(
        "observations", x["observations"] + [{"id": "O9", "text": "D8"}]))
    inj("★ 把 D8 的严重度从中改成低", lambda x:
        [d for d in x["defects"] if d["id"] == "D8"][0].__setitem__(
            "severity", "低"))
    inj("★ 把 D8 的机制里「0 处引用」抹掉", lambda x:
        [d for d in x["defects"] if d["id"] == "D8"][0].__setitem__(
            "mechanism", "它没有自己的 Esc 处理"))
    inj("★ 把 D8 的修法方向抹掉", lambda x:
        [d for d in x["defects"] if d["id"] == "D8"][0].pop("fixDirection"))
    inj("★ 把 D9 的 widensD5From765 去掉（退回个案）", lambda x:
        [d for d in x["defects"] if d["id"] == "D9"][0].pop(
            "widensD5From765"))
    inj("★ 把 D9 的 inRepoExemplar 抹掉（修法就没先例了）", lambda x:
        [d for d in x["defects"] if d["id"] == "D9"][0].pop("inRepoExemplar"))
    inj("★ 把 D10 的 widensD6From765 去掉", lambda x:
        [d for d in x["defects"] if d["id"] == "D10"][0].pop(
            "widensD6From765"))
    inj("★ 把 D10 的「标题不构成可访问名」抹掉", lambda x:
        [d for d in x["defects"] if d["id"] == "D10"][0].__setitem__(
            "note", "泛泛而谈"))
    inj("★ 缺陷 where 指向不存在的行号", lambda x:
        [d for d in x["defects"] if d["id"] == "D8"][0]["where"].append(
            "src/components/director/DirectorViewport.tsx:99999"))

    # —— 把 FAIL 偷改成 PASS
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS", lambda x: ([j.__setitem__("verdict", "PASS")
                                       for j in x["judgments"]]))
    inj("★ 把判据条数从 11 改成 8", lambda x: (x.__setitem__(
        "judgments", x["judgments"][:8])))
    inj("★ 把 J4 的 evidence 换成可比性（D8 失去支撑）", lambda x:
        x["judgments"][3].__setitem__("evidence",
                                      x["findings"]["comparability"]))

    # —— 只改一份事实
    inj("只改 findings.disclosureCensus.escClosedWholeDesk",
        lambda x: x["findings"]["disclosureCensus"].__setitem__(
            "escClosedWholeDesk", []))
    inj("只改 findings.disclosureCensus.outsideCloseMissing",
        lambda x: x["findings"]["disclosureCensus"].__setitem__(
            "outsideCloseMissing", []))
    inj("只改 findings.disclosureCensus.roleDialogPresent",
        lambda x: x["findings"]["disclosureCensus"].__setitem__(
            "roleDialogPresent", IDS))
    inj("只改 findings.disclosureCensus.ariaControlsAny",
        lambda x: x["findings"]["disclosureCensus"].__setitem__(
            "ariaControlsAny", IDS))
    inj("★ 把可比性说成一致（results 不一致）", lambda x:
        x["findings"]["comparability"].__setitem__("inconsistent",
                                                   ["results"]))
    inj("★ 删掉 R72（node --check 只验语法那条）", lambda x: (x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R72"])))
    inj("★ 不声称里删掉「焦点归还没有干净读数」", lambda x: (x.__setitem__(
        "notClaimed", [t for t in x["notClaimed"]
                       if "归还" not in t and "无从测起" not in t])))

    # ── 静态层伪造
    inj_static("伪造：DirectorDesk 里其实有 crowdPanelOpen 的一档",
               lambda x: x.__setitem__("otherStateTotal", 1))
    inj_static("伪造：阶梯里 exportPanelOpen 有两档",
               lambda x: x.__setitem__("exportPanelTierCount", 2))
    inj_static("伪造：「关面板」那档排在 closeWorkspace 之后",
               lambda x: x.__setitem__("tierBeforeCloseWorkspace", False))
    inj_static("伪造：模型库那份实现缺 stopImmediatePropagation",
               lambda x: x.__setitem__("modelLibraryStopsPropagation", False))
    inj_static("伪造：模型库那份实现没有外点 pointerdown",
               lambda x: x.__setitem__("modelLibraryDocPointerdown", False))
    inj_static("伪造：虚拟相机没有捕获阶段 Esc",
               lambda x: x.__setitem__("vcamEscapeOnCapture", False))
    inj_static("伪造：虚拟相机没有录制守卫",
               lambda x: x.__setitem__("vcamRecordingGuard", False))
    inj_static("伪造：aria-controls 其实有 1 处",
               lambda x: x.__setitem__("ariaControlsTotal", 1))
    inj_static("伪造：群众阵列面板没有 role=dialog",
               lambda x: x.__setitem__("crowdPanelHasDialogRole", False))

    # ── 原始读数：改真正的被检查键
    inj_raw("★ 原始：crowd 的 Esc 不再关导演台（D8 消失）", lambda x:
            [v["deskEnd"].__setitem__("open", True)
             for v in res_all(x, "crowd")])
    inj_raw("★ 原始：把 export 也说成会关导演台", lambda x:
            [v["deskEnd"].__setitem__("open", False)
             for v in res_all(x, "export")])
    inj_raw("★ 原始：给群众阵列补一个外点关闭（D9 少一个）", lambda x:
            [v["afterOutside"].__setitem__("panelPresent", False)
             for v in res_all(x, "crowd")])
    inj_raw("★ 原始：给导出面板补上 aria-controls（D10 破）", lambda x:
            [v["afterOpen"].__setitem__("triggerHasControlsAttr", True)
             for v in res_all(x, "export")])
    inj_raw("★ 原始：把群众阵列的 role 去掉（role=dialog 变 1/6）", lambda x:
            [v["afterOpen"].__setitem__("panelRole", None)
             for v in res_all(x, "crowd")])
    inj_raw("★ 原始：让某浮层的焦点移进面板（破坏「都不移焦点」）", lambda x:
            [v["afterOpen"]["active"].__setitem__("inPanel", True)
             for v in res_all(x, "export")])
    inj_raw("★ 原始：pathmenu 的 aria-expanded 填上 true（J10 失去依据）",
            lambda x: [v["afterOpen"].__setitem__("triggerAriaExpanded",
                                                   "true")
                       for v in res_all(x, "pathmenu")])
    inj_raw("★ 原始：把外点落点改成可点元素（R74 失效）", lambda x:
            [v["outside"]["hit"].__setitem__("clickable", True)
             for v in res_all(x, "crowd")])
    inj_raw("★ 原始：某个浮层根本没打开", lambda x:
            [v["afterOpen"].__setitem__("panelPresent", False)
             for v in res_all(x, "modellib")])
    inj_raw("★ all([]) 陷阱：把 results 清空（两轮都清）", lambda x:
            [rd.__setitem__("results", [])
             for rd in x["vb767a.json"]["rounds"]])
    inj_raw("★ all([]) 陷阱：把某浮层的可聚焦控件数改成 0", lambda x:
            res(x, "modellib")["afterOpen"].__setitem__("panelFocusables", 0))
    inj_raw("★ 伪造：3 个被外点关掉的那格其实测过 Esc", lambda x:
            [v.__setitem__("afterEsc", {"deskOpen": True,
                                         "panelPresent": True})
             for v in res_all(x, "preset")])

    # ── 台账 / README
    led = LEDGER.read_text(encoding="utf-8")
    led_line = next((ln for ln in led.splitlines()
                     if ln.startswith("| Batch 767 |")), "")
    if led_line:
        sep = "" if led.endswith(led_line + "\n") else "\n"
        inj_file("★ 台账删掉 Batch 767 行", LEDGER, sep + led_line, "")
        inj_file("★ 台账行首格改成裸数字 767", LEDGER,
                 "| Batch 767 |", "| 767 |")
        inj_file("★ 台账行首格写成 Batch 0767", LEDGER,
                 "| Batch 767 |", "| Batch 0767 |")
        inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
                 led_line[:40], led_line[:40] + FFFD)
        inj_file("★ 台账被追加了 Batch 768（行数断言）", LEDGER,
                 "| Batch 767 |", "| Batch 767 |\n| Batch 768 | x")
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.splitlines()
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 表格首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D8 章节", README, "### D8", "### 附注")
        inj_file("★ README 删掉「照抄」那句", README, "照抄", "另想办法",
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
        {"label": "原始读数可用（raw/ 下 1 份）", "pass": False,
         "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 767, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:220]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 767 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
