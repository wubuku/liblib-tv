"""batch 772 验收器：浮层开着时导演台的全局快捷键会不会穿透进来

三层结构（与 753–771 同）：
  1. **静态层** —— 从 `src/` 独立复核：桌内只有**一个** keydown 监听
     （window 冒泡）、唯一挡板是 `if (isEditable) return;` 且排在 Delete
     分支之前、主画布页那条 Delete 在导演台开着时已死（活路径只有一条）
  2. **产物层** —— 判据条数与 verdict、findings↔evidence 一致性、缺陷、
     观察、教训、README 结构、台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb772a.json` + `raw/vb772b.json`
     **重算**：合并规则与覆盖完整性、每格自证「按键时有选中」、
     破坏信号、守卫对照、**相机可删性对照**、可判/不可判的划分

⚠ 本批盯住七件容易自欺的事：
  - **「没变化」有两种读法**（R94）：preset / pathmenu 的「没删对象」**不是**
    「没穿透」。判据必须要求一个**只隔离一个变量**的对照格来闭合归因，
    并且**不许**把不可判的格混进「已判安全」的桶。
  - **破坏性读数要先有阳性对照**：`Delete` 分支只在**有选中**时才动手。
    没有选中的「没反应」是退化情况，不是结论 ⟹ 每格都要自证
    `selectedIds` 非空，且**按键那一刻**的读数才算数。
  - **撤销读数要有设置自证**（R86）：每格先在树上删掉并确认对象数真的掉了。
  - **两个信号都要读**：`objectsDropped` 与 `selectionCleared`。相机不可删时
    只有第二个可用 —— 只报一个就会把「测不出来」写成「没问题」。
  - **`all([])` 是 True**：三组分类必须**铺满**；「没有格穿透」这种空集
    不许被当成「没测到」而通过。
  - **合并规则要独立复核**：772a 有 3 格因探针 bug 失效、由 772b 取代。
    验收器要自己重算「哪些格来自哪个探针、失效格是否逐个被补上」，
    **不许采信产物里的 `provenance`**。
  - **探针产物必须在场**（R43）：raw 与 probes 缺一即判失败。

判据 **13 条（13 PASS / 0 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch772-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb772a.json", "vb772b.json"]
PROBE_FILES = ["dbg772a.py", "dbg772b.py", "mk772audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
MODES = ["del-noneditable", "bs-noneditable", "del-editable",
         "undo-noneditable"]
HAS_EDITABLE = {"export", "crowd", "modellib"}
CAM_ONLY = {"preset", "pathmenu"}
CELLS = [(i, m) for i in IDS for m in MODES]
RUN_CELLS = [k for k in CELLS if not (k[1] == "del-editable"
                                      and k[0] not in HAS_EDITABLE)]
SKIP_CELLS = [k for k in CELLS if k not in RUN_CELLS]
A_FAILED = {("preset", m) for m in ("del-noneditable", "bs-noneditable",
                                    "undo-noneditable")}
J_IDS = ["J%d" % i for i in range(1, 14)]
EXPECT_PASS_IDS = J_IDS
EXPECT_FAIL_IDS = []
EXPECT_LESSON_IDS = ["R94", "R95", "R96"]
EXPECT_DEFECT_IDS = ["D14"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def strip_comments(s):
    return re.sub(r"//[^\n]*", "", s)


def static_side():
    DD = strip_comments(src("src/components/director/DirectorDesk.tsx"))
    PG = strip_comments(src("src/app/page.tsx"))
    SELc = strip_comments(src("src/lib/libtvSelectionCommandContext.ts"))
    i0 = DD.index("const handleKeyDown = (event: KeyboardEvent) => {")
    i1 = DD.index('window.addEventListener("keydown", handleKeyDown);')
    kd = DD[i0:i1]
    p0 = PG.index("const handleKeyDown = (event: KeyboardEvent) => {")
    p1 = PG.index('window.addEventListener("keydown", handleKeyDown);', p0)
    pgkd = PG[p0:p1]
    s0 = SELc.index("export function isLibTVEditableCommandTarget(")
    sgt = SELc[s0:SELc.index("\n}", s0)]
    return {
        "deskListenerOnWindow":
            'window.addEventListener("keydown", handleKeyDown)' in DD,
        "deskListenerIsCapture":
            'window.addEventListener("keydown", handleKeyDown, true)' in DD,
        "deskKeydownListenerCount": DD.count('addEventListener("keydown"'),
        "guardIsEditableReturn": "if (isEditable) return;" in kd,
        "guardBeforeDelete": kd.index("if (isEditable) return;")
                             < kd.index('event.key === "Delete"'),
        "deleteBranchPresent":
            'event.key === "Delete" || event.key === "Backspace"' in kd,
        "deleteCallsEntity": "deleteDirectorEntity(" in kd,
        "deleteGuardedBySelection": "selectedObjectIds.length" in kd,
        "deleteHasWorkspaceBusyGuard": "workspaceBusy" in kd,
        "pageDeletePresent":
            'event.key === "Delete" || event.key === "Backspace"' in pgkd,
        "pageReturnsWhenDeskOpen":
            "if (uiState.activeDirectorNodeId) return;" in pgkd,
        "pageGuardBeforeDelete": pgkd.index("activeDirectorNodeId")
                                 < pgkd.index('event.key === "Delete"'),
        "deskGuardIsTagNameOnly": "closest(" not in kd,
        "pageGuardExcludesFileInput": "type='file'" in sgt,
        "pageGuardCoversRoleTextbox": "role='textbox'" in sgt,
    }


def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    A = json.loads((RAWDIR / "vb772a.json").read_text(encoding="utf-8"))
    B = json.loads((RAWDIR / "vb772b.json").read_text(encoding="utf-8"))
    for nm, r in (("772a", A), ("772b", B)):
        rs = r.get("rounds") or []
        if len(rs) != 2:
            raise SystemExit("%s 轮数 %d（要 2）" % (nm, len(rs)))
    return {"A": A, "B": B}


def derive(rw):
    """★ 全部现算。**不采信产物里的 provenance / 派生信号** ——
    阴性对照正是靠改这份结构后重跑这一层来被看见的。"""
    A, B = rw["A"], rw["B"]
    ga, gb = {}, {}
    for rd in A["rounds"]:
        for r in rd.get("rows") or []:
            ga.setdefault((r.get("id"), r.get("mode")), []).append(r)
    for rd in B["rounds"]:
        for r in rd.get("rows") or []:
            plan = r.get("plan") or ""
            key = (("cam", "deletable-control")
                   if plan == "cam-deletable-control"
                   else tuple(plan.split("/")))
            gb.setdefault(key, []).append(r)

    D = {"aFailed": {k for k, v in ga.items() for r in v if r.get("FAILED")},
         "aSkip": {k for k, v in ga.items() for r in v if r.get("SKIPPED")},
         "unexpectedFailed": [], "provenance": {}, "merged": {},
         "badSuperseded": []}
    D["unexpectedFailed"] = sorted(
        {k for k, v in ga.items() for r in v if r.get("FAILED")}
        - A_FAILED)
    for k, v in gb.items():
        for r in v:
            if r.get("FAILED"):
                D["unexpectedFailed"].append("772b %r: %s"
                                             % (k, r["FAILED"]))
    D["unexpectedFailed"] = sorted({str(x) for x in D["unexpectedFailed"]})
    # 772a 的失败格必须逐个被 772b 补上
    for k in D["aFailed"]:
        if k not in gb:
            D["badSuperseded"].append("%s/%s 没被 772b 补上" % k)
    for k, v in gb.items():
        if len(v) != 2:
            D["badSuperseded"].append("772b %r 轮数 %d" % (k, len(v)))
    # 合并必须铺满：缺格要**记成失败**，不许让 derive 崩掉（R86 的同族 ——
    # 一个会崩的验收器和一个放水的验收器同样没用）
    for k in RUN_CELLS + [("cam", "deletable-control")]:
        if k not in gb and k not in ga:
            D["badSuperseded"].append("%s/%s 两份 raw 都没有" % k)
        elif k in ga and k in D["aFailed"] and k not in gb:
            D["badSuperseded"].append("%s/%s 只在 772a 且已失效" % k)
    for k, v in ga.items():
        if len(v) != 2:
            D["badSuperseded"].append("772a %r 轮数 %d" % (k, len(v)))
    # 合并
    for k, v in ga.items():
        if k in D["aSkip"] or k in D["aFailed"]:
            continue
        D["merged"][k] = v
        D["provenance"]["%s/%s" % k] = "772a"
    for k, v in gb.items():
        D["merged"][k] = v
        D["provenance"]["%s/%s" % k] = "772b"

    def cell(r):
        b, a = r.get("before") or {}, r.get("after") or {}
        selB = r.get("selectedBeforeKey", b.get("selectedIds"))
        selA = r.get("selectedAfterKey", a.get("selectedIds"))
        dl = r.get("delta") or {}
        dObj = dl.get("objects")
        if dObj is None:
            dObj = (a.get("objectCount") or 0) - (b.get("objectCount") or 0)
        return {"layer": r.get("layer") or r.get("id"),
                "focus": r.get("focus"), "setup": r.get("setup"),
                "selBefore": selB, "selAfter": selA,
                "deltaObjects": dObj,
                "objectsDropped": dObj is not None and dObj < 0,
                "selectionCleared": bool(selB) and not selA,
                "selectionUnchanged": selB == selA,
                "restored": r.get("restored") is True}

    D["t"] = {k: [cell(r) for r in v] for k, v in D["merged"].items()}

    DEL = [(i, "del-noneditable") for i in IDS]
    BS = [(i, "bs-noneditable") for i in IDS]
    ED = [(i, "del-editable") for i in sorted(HAS_EDITABLE)]
    UNDO = [(i, "undo-noneditable") for i in IDS]
    D["missing"] = sorted("%s/%s" % k for k in
                          DEL + BS + ED + UNDO + [("cam", "deletable-control")]
                          if k not in D["t"])
    D["leak"] = {}
    for k in DEL + BS:
        if k not in D["t"]:
            continue
        v = D["t"][k]
        D["leak"]["/".join(k)] = {
            "classifiable": k[0] not in CAM_ONLY,
            "objectsDropped": all(c["objectsDropped"] for c in v),
            "selectionCleared": all(c["selectionCleared"] for c in v),
            "deltaObjects": sorted({c["deltaObjects"] for c in v}),
            "selBefore": sorted({str(c["selBefore"]) for c in v}),
        }
    D["guard"] = {}
    for k in ED:
        if k not in D["t"]:
            continue
        v = D["t"][k]
        D["guard"]["/".join(k)] = {
            "focusEditable": all((c["focus"] or {}).get("editable") is True
                                 for c in v),
            "blocked": all(not c["objectsDropped"] and c["selectionUnchanged"]
                           for c in v),
            "deltaObjects": sorted({c["deltaObjects"] for c in v}),
        }
    D["undo"] = {}
    for k in UNDO:
        if k not in D["t"]:
            continue
        v = D["t"][k]
        D["undo"]["/".join(k)] = {
            "setupVerified": all(
                (c["setup"] or {}).get("objectsAfter") is not None
                and c["setup"]["objectsAfter"] < c["setup"]["objectsBefore"]
                for c in v),
            "restored": all(c["restored"] for c in v),
            "deltaObjects": sorted({c["deltaObjects"] for c in v}),
        }
    ctrl = D["t"].get(("cam", "deletable-control")) or []
    D["control"] = {
        "objectsDropped": any(c["objectsDropped"] for c in ctrl) if ctrl
                          else None,
        "selectionUnchanged": bool(ctrl)
                              and all(c["selectionUnchanged"] for c in ctrl),
        "deltaObjects": sorted({c["deltaObjects"] for c in ctrl}),
        "focus": ctrl[0]["focus"] if ctrl else None,
    }
    D["leaked"] = sorted(k for k, v in D["leak"].items()
                         if v["classifiable"] and v["objectsDropped"])
    D["confounded"] = sorted(k for k, v in D["leak"].items()
                             if not v["classifiable"])
    D["guardBlocked"] = sorted(k for k, v in D["guard"].items()
                               if v["blocked"])
    D["undoLeaked"] = sorted(k for k, v in D["undo"].items() if v["restored"])
    D["allHadSelection"] = all(
        c["selBefore"] for v in D["t"].values() for c in v)
    D["deskGone"] = [x for rd in (A["rounds"] + B["rounds"])
                     for x in (rd.get("deskGoneAfter") or [])]
    D["roundsConsistent"] = True
    for nm, r in (("a", A), ("b", B)):
        r0 = json.loads(json.dumps(r["rounds"][0].get("rows")))
        r1 = json.loads(json.dumps(r["rounds"][1].get("rows")))
        if r0 != r1:
            D["roundsConsistent"] = False
    return D


def run_checks(a, st, rw):
    D = derive(rw)
    J = {j["id"]: j for j in a.get("judgments") or []}
    F = a.get("findings") or {}
    C = []

    def chk(label, cond, got):
        C.append({"label": label, "pass": bool(cond), "got": got})

    # ── 产物层
    chk("产物：判据 13 条且 id 齐全", sorted(J) == sorted(J_IDS),
        {"got": sorted(J)})
    chk("产物：verdict 与预期一致",
        all(J[j]["verdict"] == "PASS" for j in J_IDS if j in J)
        and not EXPECT_FAIL_IDS,
        {"got": {j: J[j]["verdict"] for j in J_IDS if j in J}})
    bad = [j["id"] for j in J.values()
           if F.get(j["evidenceKey"]) != j["evidence"]]
    chk("产物：每条判据的 evidence 等于 findings[evidenceKey]", not bad,
        {"mismatch": bad})
    chk("产物：教训 %s 齐全" % EXPECT_LESSON_IDS,
        sorted(x["id"] for x in (a.get("probeLessons") or []))
        == sorted(EXPECT_LESSON_IDS),
        {"got": [x["id"] for x in (a.get("probeLessons") or [])]})
    chk("产物：观察 ≥4 条", len(a.get("observations") or []) >= 4,
        {"got": len(a.get("observations") or [])})
    d = a.get("defects") or []
    chk("产物：新缺陷 D14（中）恰好一条",
        [x.get("id") for x in d] == EXPECT_DEFECT_IDS
        and (d[0].get("severity") if d else None) == "中",
        {"got": [(x.get("id"), x.get("severity")) for x in d]})
    chk("产物：D14 的 where 全部带行号",
        bool(d) and all(re.match(r"^.+:\d+", w)
                        for w in (d[0].get("where") or [])),
        {"got": d[0].get("where") if d else None})
    chk("产物：两份 raw 的 sha 都记进产物",
        set(RAW_FILES) <= set((a.get("rawSha") or {})),
        {"got": a.get("rawSha")})
    chk("产物：探针 raw/ 与 probes/ 都在场（R43）",
        all((RAWDIR / f).exists() for f in RAW_FILES)
        and all((PROBEDIR / f).exists() for f in PROBE_FILES),
        {"raw": RAW_FILES, "probes": PROBE_FILES})

    # ── 静态层
    chk("静态：桌内只有 1 个 keydown 监听且在 window 冒泡",
        st["deskKeydownListenerCount"] == 1 and st["deskListenerOnWindow"]
        and not st["deskListenerIsCapture"],
        {"n": st["deskKeydownListenerCount"],
         "window": st["deskListenerOnWindow"],
         "capture": st["deskListenerIsCapture"]})
    chk("静态：唯一挡板是 isEditable 早退，且排在 Delete 分支之前",
        st["guardIsEditableReturn"] and st["guardBeforeDelete"]
        and st["deleteBranchPresent"] and st["deleteCallsEntity"],
        {"guard": st["guardIsEditableReturn"],
         "before": st["guardBeforeDelete"],
         "entity": st["deleteCallsEntity"]})
    chk("静态：★ 主画布页那条 Delete 在桌开时已死 ⟹ 活路径只有一条",
        st["pageDeletePresent"] and st["pageReturnsWhenDeskOpen"]
        and st["pageGuardBeforeDelete"],
        {"exists": st["pageDeletePresent"],
         "returns": st["pageReturnsWhenDeskOpen"],
         "before": st["pageGuardBeforeDelete"]})
    chk("产物：静态层与验收器重读的源码一致",
        (a.get("static") or {}).get("deskKeydownListenerCount")
        == st["deskKeydownListenerCount"]
        and (a.get("static") or {}).get("pageHandlerReturnsWhenDeskOpen")
        is True,
        {"got": {k: (a.get("static") or {}).get(k) for k in
                 ("deskKeydownListenerCount",
                  "pageHandlerReturnsWhenDeskOpen")}})
    chk("静态：两道守卫不等价（观察项）",
        st["deskGuardIsTagNameOnly"] and st["pageGuardExcludesFileInput"]
        and st["pageGuardCoversRoleTextbox"],
        {"deskTagNameOnly": st["deskGuardIsTagNameOnly"],
         "pageExclFile": st["pageGuardExcludesFileInput"],
         "pageRoleTextbox": st["pageGuardCoversRoleTextbox"]})

    # ── 原始读数层
    chk("原始：两个探针各自两轮逐格一致",
        D["roundsConsistent"], {"got": D["roundsConsistent"]})
    chk("原始：没有预期外的失败格，且 772a 的 3 个失效格都被 772b 补上",
        not D["unexpectedFailed"] and not D["badSuperseded"]
        and D["aFailed"] == A_FAILED,
        {"unexpected": D["unexpectedFailed"],
         "badSuperseded": D["badSuperseded"],
         "aFailed": sorted("%s/%s" % k for k in D["aFailed"])})
    chk("原始：合并后 22 格（21 实验 + 1 对照），覆盖完整",
        len(D["merged"]) == len(RUN_CELLS) + 1
        and sorted(D["merged"]) == sorted(RUN_CELLS
                                          + [("cam", "deletable-control")]),
        {"got": len(D["merged"]), "want": len(RUN_CELLS) + 1})
    chk("原始：★ 合并铺满 —— 没有「哪份 raw 都没有」的格",
        not D["missing"], {"got": D["missing"]})
    chk("原始：★ 每格按键那一刻**真的有选中**",
        D["allHadSelection"], {"got": D["allHadSelection"]})
    chk("原始：★ Delete/Backspace 穿透 —— 8/8 可判格 Δ对象<0 且选中被清空",
        len(D["leaked"]) == 8
        and all(D["leak"][k]["objectsDropped"]
                and D["leak"][k]["selectionCleared"] for k in D["leaked"]),
        {"leaked": D["leaked"]})
    chk("原始：Backspace 与 Delete 逐格 Δ 相同（同一条代码路径）",
        all(D["leak"].get("%s/bs-noneditable" % i, {}).get("deltaObjects")
            == D["leak"].get("%s/del-noneditable" % i, {}).get("deltaObjects")
            for i in IDS),
        {"got": {i: (D["leak"].get("%s/del-noneditable" % i, {})
                     .get("deltaObjects"),
                     D["leak"].get("%s/bs-noneditable" % i, {})
                     .get("deltaObjects"))
                 for i in IDS}})
    chk("原始：★ 守卫对照 —— 落可编辑控件时 3/3 被挡住",
        len(D["guardBlocked"]) == 3
        and all(v["focusEditable"] for v in D["guard"].values()),
        {"blocked": D["guardBlocked"],
         "focusEditable": {k: v["focusEditable"]
                           for k, v in D["guard"].items()}})
    chk("原始：★ 相机可删性对照 —— 浮层之外按 Delete 相机**没被删**",
        D["control"].get("objectsDropped") is False
        and D["control"].get("selectionUnchanged") is True,
        {"got": D["control"]})
    chk("原始：★ preset/pathmenu 的 4 格归为**结构上不可判**（不是「没穿透」）",
        sorted(D["confounded"]) == ["pathmenu/bs-noneditable",
                                    "pathmenu/del-noneditable",
                                    "preset/bs-noneditable",
                                    "preset/del-noneditable"]
        and not [k for k in D["confounded"]
                 if D["leak"].get(k, {}).get("objectsDropped")],
        {"got": D["confounded"]})
    chk("原始：★ Meta+Z 穿透 6/6，且每格 setup 都自证过",
        len(D["undoLeaked"]) == 6
        and all(v["setupVerified"] for v in D["undo"].values()),
        {"undoLeaked": D["undoLeaked"],
         "setup": {k: v["setupVerified"] for k, v in D["undo"].items()}})
    chk("原始：★ 这三个键一个都没关掉导演台（与 D8 是两类后果）",
        D["deskGone"] == [], {"got": D["deskGone"]})
    chk("产物：与验收器独立重算的结果一致",
        (a.get("leakage") or {}).get("leakedCells") == D["leaked"]
        and (a.get("leakage") or {}).get("confoundedCells")
        == D["confounded"]
        and (a.get("leakage") or {}).get("undoLeakedCells")
        == D["undoLeaked"]
        and (a.get("leakage") or {}).get("guardBlockedCells")
        == D["guardBlocked"]
        and (a.get("comparability") or {}).get("provenance")
        == D["provenance"],
        {"leaked": (a.get("leakage") or {}).get("leakedCells"),
         "confounded": (a.get("leakage") or {}).get("confoundedCells"),
         "undo": (a.get("leakage") or {}).get("undoLeakedCells"),
         "guard": (a.get("leakage") or {}).get("guardBlockedCells")})
    chk("产物：分类铺满 —— 不可判的桶非空且没混进「已判安全」",
        len(D["leaked"]) + len(D["confounded"]) == len(D["leak"])
        and D["confounded"],
        {"leaked": len(D["leaked"]), "confounded": len(D["confounded"]),
         "totalLeak": len(D["leak"])})

    # ── README / 台账
    if not README.exists():
        chk("README 存在", False, "缺 README.md")
    else:
        rd = README.read_text(encoding="utf-8")
        chk("README：不含替换字符 U+FFFD", FFFD not in rd,
            {"count": rd.count(FFFD)})
        for need in ("D14", "结构上不可判", "相机", "R94", "穿透"):
            chk("README 提到「%s」" % need, need in rd, None)
        bare = [ln for ln in rd.split("\n")
                if re.match(r"^\|\s*\d+[a-z]?\s*\|", ln)]
        chk("README：表格首格没有裸数字（pre-commit 正则会拦）", not bare,
            {"bare": bare[:3]})
    if not LEDGER.exists():
        chk("台账存在", False, "缺台账")
    else:
        ll = LEDGER.read_text(encoding="utf-8")
        lines = [ln for ln in ll.split("\n") if ln.startswith("| Batch 772 ")]
        chk("台账：Batch 772 恰好一行", len(lines) == 1, {"count": len(lines)})
        if lines:
            chk("台账：该行不含 U+FFFD", FFFD not in lines[0],
                {"count": lines[0].count(FFFD)})
            chk("台账：首格是 `| Batch 772 |`",
                re.match(r"^\|\s*Batch 772\s*\|", lines[0]) is not None,
                {"head": lines[0][:60]})
            chk("台账：恰好 3 列", lines[0].count("|") == 4,
                {"pipes": lines[0].count("|")})
        chk("台账：历史 U+FFFD 仍在 9 处", ll.count(FFFD) == 9,
            {"count": ll.count(FFFD)})
    return C


def negative_controls(a, st, rw):
    out = []

    def run(name, mutate, kw):
        aa = copy.deepcopy(a)
        rr = copy.deepcopy(rw)
        mutate(rr)
        try:
            cs = run_checks(aa, st, rr)
        except SystemExit as e:
            out.append({"name": name, "caught": True, "why": str(e)[:80]})
            return
        hit = [c for c in cs if kw in c["label"]]
        out.append({
            "name": name,
            "kwMatchedCount": len(hit),
            # ★ 匹配不到标签 = 阴性对照自己写坏了（R86），不是「产品没洞」
            "kwMatchedAnyLabel": bool(hit),
            "caught": bool(hit) and not any(c["pass"] for c in hit),
            "expectFailOn": kw,
            "matchedLabels": [c["label"] for c in hit],
            "stillPassing": [c["label"] for c in hit if c["pass"]]})

    def m_noSelection(rr):
        """把 export/del 的选中抹掉 ⟹ J3「每格真的有选中」必须红。"""
        for rd in rr["A"]["rounds"]:
            for r in rd["rows"]:
                if r.get("id") == "export" and r.get("mode") == "del-noneditable":
                    r["before"]["selectedIds"] = []
                    r["after"]["selectedIds"] = []
                    r["delta"] = {"objects": 0, "nodes": 0}

    def m_noLeak(rr):
        """把穿透改成「没穿透」⟹ J4 必须红。"""
        for rd in rr["A"]["rounds"]:
            for r in rd["rows"]:
                if r.get("id") == "export" and r.get("mode") in (
                        "del-noneditable", "bs-noneditable"):
                    r["after"]["objectCount"] = r["before"]["objectCount"]
                    r["after"]["selectedIds"] = r["before"]["selectedIds"]
                    r["delta"] = {"objects": 0, "nodes": 0}

    def m_cameraDeletable(rr):
        """把对照格改成「相机删得掉」⟹ J8 必须红。"""
        for rd in rr["B"]["rounds"]:
            for r in rd["rows"]:
                if r.get("plan") == "cam-deletable-control":
                    r["after"]["objectCount"] = r["before"]["objectCount"] - 1
                    r["after"]["selectedIds"] = []
                    r["delta"] = {"objects": -1, "nodes": -1}

    def m_confoundedDropped(rr):
        """把 preset/pathmenu 从「不可判」里谎报成「已判安全」⟹ J7 必须红。

        ★ 两个坑：
          1. 拼写是 `noneditable`（两个 n），写成 `nodeditable` 条件永不成立；
          2. ★ **pathmenu 的格来自 772b 而不是 772a** —— 772b 覆盖了 772a 的
             同名格。只改 772a 那份副本，等于什么也没改（这正是 R86：
             **无效的阴性对照不会报错，只会永远「漏放」**）。
        """
        for rd in rr["B"]["rounds"]:
            for r in rd["rows"]:
                pl = r.get("plan") or ""
                if pl.split("/")[0] in ("preset", "pathmenu") \
                        and pl.endswith("noneditable"):
                    r["after"]["objectCount"] = (
                        r["before"]["objectCount"] - 1)
                    r["after"]["selectedIds"] = []
                    r["delta"] = {"objects": -1, "nodes": -1}

    def m_guardBroken(rr):
        """守卫失效（落输入框也删）⟹ J6 必须红。
        只动**有读数**的那些格 —— 3 个没有可编辑控件的浮层是结构性 SKIP，
        它们没有 `before`，动了反而是在测「SKIP 格被篡改」。"""
        for rd in rr["A"]["rounds"]:
            for r in rd["rows"]:
                if r.get("mode") == "del-editable" and r.get("before"):
                    r["after"]["objectCount"] = r["before"]["objectCount"] - 1
                    r["after"]["selectedIds"] = []
                    r["delta"] = {"objects": -1, "nodes": -1}

    def m_undoSetupUnverified(rr):
        """撤销的设置没自证 ⟹ J9 必须红。**两份 raw 都要动**（preset 在 772b）。"""
        for rd in rr["A"]["rounds"] + rr["B"]["rounds"]:
            for r in rd["rows"]:
                if (r.get("mode") == "undo-noneditable"
                        or (r.get("plan") or "").endswith("undo-noneditable")) \
                        and r.get("setup"):
                    r["setup"] = {"objectsBefore": 5, "objectsAfter": 5}

    def m_supersededDropped(rr):
        """772b 不再补 preset ⟹ J2 的覆盖完整性必须红。"""
        for rd in rr["B"]["rounds"]:
            rd["rows"] = [r for r in rd["rows"]
                          if not (r.get("plan") or "").startswith("preset/")]

    def m_roundsDiffer(rr):
        """第二轮读数被改 ⟹ J1 必须红。"""
        rows = rr["A"]["rounds"][1]["rows"]
        for r in rows:
            if r.get("id") == "crowd" and r.get("mode") == "del-noneditable":
                r["after"]["objectCount"] = 99

    run("把 export/del 的选中抹掉（破坏性读数没有阳性对照）",
        m_noSelection, "每格按键那一刻**真的有选中**")
    run("把 export 的 Delete/Backspace 改成「没穿透」",
        m_noLeak, "Delete/Backspace 穿透")
    run("把相机对照格改成「相机删得掉」",
        m_cameraDeletable, "相机可删性对照")
    run("把 preset/pathmenu 谎报成「已判安全」",
        m_confoundedDropped, "4 格归为")
    run("让守卫失效（落输入框也删）",
        m_guardBroken, "落可编辑控件时 3/3 被挡住")
    run("把撤销臂的设置改成「没自证」",
        m_undoSetupUnverified, "Meta+Z 穿透")
    run("让 772b 不再补 preset（覆盖不完整）",
        m_supersededDropped, "失效格都被 772b 补上")
    run("把第二轮的读数改掉（两轮不一致）",
        m_roundsDiffer, "两轮逐格一致")

    # 产物层：直接改 a
    def aproduct(name, mutate, kw):
        aa = copy.deepcopy(a)
        mutate(aa)
        cs = run_checks(aa, st, rw)
        hit = [c for c in cs if kw in c["label"]]
        out.append({"name": name, "kwMatchedAnyLabel": bool(hit),
                    "kwMatchedCount": len(hit),
                    "caught": bool(hit) and not any(c["pass"] for c in hit),
                    "expectFailOn": kw,
                    "stillPassing": [c["label"] for c in hit if c["pass"]]})

    aproduct("篡改一条判据的 evidence",
             lambda x: [j.update(evidence={"x": 1}) for j in x["judgments"]
                        if j["id"] == "J4"], "evidence 等于 findings")
    aproduct("删掉一个 findings 键",
             lambda x: x["findings"].pop("F2_deleteLeaks", None),
             "evidence 等于 findings")
    aproduct("把新缺陷 D14 删掉",
             lambda x: x.__setitem__("defects", []), "新缺陷 D14")
    aproduct("删掉一条探针教训",
             lambda x: x.__setitem__(
                 "probeLessons",
                 [y for y in x["probeLessons"] if y["id"] != "R95"]),
             "教训 [")
    aproduct("把 D14 的严重度改掉",
             lambda x: x["defects"][0].__setitem__("severity", "低")
             if x.get("defects") else None,
             "新缺陷 D14")

    # 文本类
    def text_run(name, path, old, new, kw):
        if not path.exists():
            out.append({"name": name, "caught": False, "why": "文件不存在"})
            return
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            out.append({"name": name, "caught": False,
                        "why": "锚点没找到：%r" % old[:40]})
            return
        try:
            path.write_text(orig.replace(old, new, 1), encoding="utf-8")
            cs = run_checks(a, st, rw)
            hit = [c for c in cs if kw in c["label"]]
            out.append({"name": name, "kwMatchedAnyLabel": bool(hit),
                        "kwMatchedCount": len(hit),
                        "caught": bool(hit)
                        and not any(c["pass"] for c in hit),
                        "expectFailOn": kw,
                        "stillPassing": [c["label"] for c in hit if c["pass"]]})
        finally:
            path.write_text(orig, encoding="utf-8")

    text_run("把台账 Batch 772 行改名", LEDGER, "| Batch 772 ",
             "| Batch 772X ", "台账：Batch 772 恰好一行")
    if README.exists():
        rd = README.read_text(encoding="utf-8")
        anchor = next((ln for ln in rd.split("\n")
                       if ln.startswith("|")), "")
        text_run("把 README 表格首格改成裸数字", README, anchor,
                 "| 772 | x | y |", "首格没有裸数字")
    return out


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        rw = load_raw()
        rawErr = None
    except Exception as e:
        rw, rawErr = {}, str(e)
    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（两份 raw + 三个 probes/）", "pass": False,
         "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)
    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    # ★ 阴性对照的关键词必须**恰好命中一条**判据。命中 0 条 = 对照写坏了；
    #   命中 ≥2 条 = 撞车（R86：无效的阴性对照不会报错，只会永远「漏放」，
    #   而撞车版本连「漏放」都伪装成「对照有效」）。
    kw_bad = [n["name"] for n in neg if n.get("kwMatchedCount") != 1]
    neg_ok = sum(1 for n in neg if n["caught"] and n.get("kwMatchedCount") == 1)
    ok = npass == total and neg_ok == len(neg)
    REPORT.write_text(json.dumps(
        {"batch": 772, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "negativeKwBroken": kw_bad,
         "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")
    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:260]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if n.get("kwMatchedCount") != 1:
            print("  ✗ 阴性对照自身写坏（关键词命中 %s 条判据）：%s"
                  % (n.get("kwMatchedCount"), n["name"]))
        elif not n["caught"]:
            print("  ✗ 漏放：%s  (%s)" % (n["name"],
                                        n.get("why")
                                        or n.get("expectFailOn")))
    print("batch 772 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
