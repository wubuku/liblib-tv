"""batch 773 验收器：「分支到没到」的直接读数（defaultPrevented）

三层结构（与 753–772 同）：
  1. **静态层** —— 从 `src/` 独立复核：桌内只有**一个** keydown 监听
     （window 冒泡）、`isEditable` 早退排在所有分支**之前**、
     **5 个分支每走到一个就调一次 `preventDefault()`**（行号现读）、
     对话框那个 Tab 处理器只认 Tab（不污染读数）
  2. **产物层** —— 判据条数与 verdict、findings↔evidence 一致性、更正块、
     观察、教训、README 结构、台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb773a.json` + `raw/vb773b.json`
     **重算**：合并规则与覆盖完整性、每格自证、`defaultPrevented` 分类、
     两个信号的分离

⚠ 本批盯住八件容易自欺的事：
  - **读数方法要有中性对照**（R98）：按桌内**不处理**的键必须读到
    `false`。若为 true，「dp=true 就等于分支跑了」整条推理作废。
  - **「分支跑到了」与「东西真被删了」是两个信号**（R97）：只报后者就会把
    「测不出来」写成「没问题」。判据要分别核对两个桶，且 `dpNoEffect` 桶
    必须**非空**（全空就说明还在用副作用型读数）。
  - **`Meta+C/V/Z` 本来就不改对象数**：把它们算进「dp=true 但没副作用」
    是概念错误 —— 验收器要把这一类**单独隔开**。
  - **合并规则独立复核**：773a 的中性臂一次都没跑（for-want 补丁没落进
    文件），由 773b 补 6 格。验收器要自己重算「哪些格来自哪个探针、
    773a 是否真的没有中性臂」，**不许采信产物里的 provenance**。
  - **每格自证**：间谍装上了、收到了事件、读得到布尔值、目标有选中。
  - **`all([])` 是 True**：分类必须铺满；「没有格分支跑到」这种空集
    不许被当成「没测到」而通过。
  - **R99**：某个字段在所有格上取同一个「看起来合理」的值时，先怀疑
    没记。验收器显式检查 `defaultPrevented` 确实是布尔、且**不是**全同一值。
  - **探针产物必须在场**（R43）。

判据 **10 条（10 PASS / 0 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch773-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb773a.json", "vb773b.json"]
PROBE_FILES = ["dbg773a.py", "dbg773b.py", "mk773audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
KEYS = ["Delete", "Backspace", "Meta+z", "Meta+c", "Meta+v"]
DESTRUCTIVE = ("Delete", "Backspace")
NEUTRAL_KEY = "F2"
HAS_EDITABLE = {"export", "crowd", "modellib"}
CAM_ONLY = {"preset", "pathmenu"}
SKIP_LAYERS = sorted(set(IDS) - HAS_EDITABLE)
NE = [(i, "noneditable", k) for i in IDS for k in KEYS]
ED = [(i, "editable", k) for i in sorted(HAS_EDITABLE) for k in KEYS]
NEU = [(i, "neutral", NEUTRAL_KEY) for i in IDS]
CELLS = NE + ED + NEU
J_IDS = ["J%d" % i for i in range(1, 11)]
EXPECT_PASS_IDS = J_IDS
EXPECT_FAIL_IDS = []
EXPECT_LESSON_IDS = ["R96", "R97", "R98", "R99"]
EXPECT_CORRECTION_IDS = ["C773-1"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def strip_comments(s):
    return re.sub(r"//[^\n]*", "", s)


def static_side():
    DD = strip_comments(src("src/components/director/DirectorDesk.tsx"))
    FC = strip_comments(
        src("src/components/director/useDirectorFocusContainment.ts"))
    i0 = DD.index("const handleKeyDown = (event: KeyboardEvent) => {")
    i1 = DD.index('window.addEventListener("keydown", handleKeyDown);')
    lines = DD[:i1].split("\n")
    kd = "\n".join(lines)
    pd = [n for n, ln in enumerate(lines, 1) if "event.preventDefault()" in ln]
    branches = {}
    for label, pat in (("Meta+C", 'toLowerCase() === "c"'),
                       ("Meta+V", 'toLowerCase() === "v"'),
                       ("Meta+Z", 'toLowerCase() === "z"'),
                       ("Meta+Y", 'toLowerCase() === "y"'),
                       ("Delete|Backspace", 'event.key === "Delete"')):
        hit = [n for n, ln in enumerate(lines, 1) if pat in ln]
        inner = [n for n in pd if hit and n > hit[0]]
        branches[label] = {"guardLine": hit[0] if hit else None,
                           "preventDefaultLines": inner,
                           "hasPreventDefault": bool(inner)}
    hook = FC[FC.index("const handleKeyDown = (event: KeyboardEvent) => {"):
              FC.index('root.addEventListener("keydown", handleKeyDown);')]
    return {
        "deskListenerOnWindow":
            'window.addEventListener("keydown", handleKeyDown)' in DD,
        "deskListenerIsCapture":
            'window.addEventListener("keydown", handleKeyDown, true)' in DD,
        "deskKeydownListenerCount": DD.count('addEventListener("keydown"'),
        "guardIsEditableReturn": "if (isEditable) return;" in kd,
        "guardBeforeDelete": kd.index("if (isEditable) return;")
                             < kd.index('event.key === "Delete"'),
        "guardBeforeMetaC": kd.index("if (isEditable) return;")
                            < kd.index('toLowerCase() === "c"'),
        "preventDefaultLines": pd,
        "branches": branches,
        "allFivePrevent": all(v["hasPreventDefault"]
                              for v in branches.values()),
        "tabHookGuardsOnTabOnly": bool(
            re.search(r'if \(event\.key !== "Tab"\) return;', hook)),
        "deleteSubBranches": {"group": "DELETE_GROUP" in kd,
                              "objects": "DELETE_OBJECTS" in kd},
    }


def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    A = json.loads((RAWDIR / "vb773a.json").read_text(encoding="utf-8"))
    B = json.loads((RAWDIR / "vb773b.json").read_text(encoding="utf-8"))
    for nm, r in (("773a", A), ("773b", B)):
        rs = r.get("rounds") or []
        if len(rs) != 2:
            raise SystemExit("%s 轮数 %d（要 2）" % (nm, len(rs)))
    return {"A": A, "B": B}


def derive(rw):
    """★ 全部现算，不采信产物里的 provenance 或派生分类。"""
    A, B = rw["A"], rw["B"]

    def grid(raw, neutral):
        g, skip = {}, set()
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("SKIPPED"):
                    skip.add((r.get("id"), r.get("want")))
                    continue
                k = (r.get("id"), r.get("want"),
                     NEUTRAL_KEY if neutral else r.get("key"))
                g.setdefault(k, []).append(r)
        return g, skip

    ga, sa = grid(A, False)
    gb, sb = grid(B, True)
    D = {"aSkip": sorted("%s/%s" % k for k in sa),
         "aHasNeutral": sorted("%s/%s/%s" % k for k in ga
                               if k[1] == "neutral"),
         "bHasSkip": sorted("%s/%s" % k for k in sb),
         "badMerge": [], "missing": [], "provenance": {}, "merged": {},
         "roundsConsistent": True}
    for nm, raw in (("773a", A), ("773b", B)):
        r0 = json.loads(json.dumps(raw["rounds"][0].get("rows")))
        r1 = json.loads(json.dumps(raw["rounds"][1].get("rows")))
        if r0 != r1:
            D["roundsConsistent"] = False
    if D["aHasNeutral"]:
        D["badMerge"].append("773a 竟有中性臂 —— 合并规则要重算")
    if D["aSkip"] != sorted("%s/editable" % i for i in SKIP_LAYERS):
        D["badMerge"].append("773a 的 SKIP 集合不对：%r" % D["aSkip"])
    if D["bHasSkip"]:
        D["badMerge"].append("773b 不该有 SKIP 格")
    D["missing"] = sorted("%s/%s/%s" % k for k in CELLS
                          if k not in ga and k not in gb)
    # 覆盖不完整也是**合并完整性**的一部分（中性对照那 6 格就是这么丢的）
    if D["missing"]:
        D["badMerge"].append("缺格：%r" % D["missing"])
    for k, v in list(ga.items()) + list(gb.items()):
        if len(v) != 2:
            D["badMerge"].append("%s/%s/%s 轮数 %d"
                                 % (k[0], k[1], k[2], len(v)))
        for r in v:
            if r.get("FAILED"):
                D["badMerge"].append("%s/%s/%s FAILED: %s"
                                     % (k[0], k[1], k[2], r["FAILED"]))
    for k, v in ga.items():
        D["merged"][k] = v
        D["provenance"]["%s/%s/%s" % k] = "773a"
    for k, v in gb.items():
        D["merged"][k] = v
        D["provenance"]["%s/%s/%s" % k] = "773b"

    def cell(r):
        f = r.get("focus") or {}
        return {"focusEditable": f.get("editable") is True,
                "target": r.get("target"),
                "targetUndeletable": r.get("targetUndeletable") is True,
                "selectedIds": r.get("selectedIds") or [],
                "spyInstalled": (r.get("spy") or {}).get("installed") is True,
                "eventsSeen": r.get("eventsSeen") or 0,
                "dp": r.get("defaultPrevented"),
                "objectsDelta": r.get("objectsDelta")}

    D["t"] = {k: [cell(r) for r in v] for k, v in D["merged"].items()}

    def S(keys):
        return sorted("%s/%s/%s" % k for k in keys)

    D["reach"] = {}
    for k in NE + ED:
        dps = {c["dp"] for c in D["t"].get(k, [])}
        D["reach"]["%s/%s/%s" % k] = {
            "dp": dps.pop() if len(dps) == 1 else sorted(map(str, dps)),
            "focusEditable": D["t"][k][0]["focusEditable"] if D["t"].get(k)
            else None,
            "objectsDelta": sorted({c["objectsDelta"]
                                    for c in D["t"].get(k, [])}),
        }
    D["neutral"] = {}
    for k in NEU:
        v = D["t"].get(k) or []
        dps = {c["dp"] for c in v}
        D["neutral"][k[0]] = (dps.pop() if len(dps) == 1
                              else sorted(map(str, dps)))
    D["branchReached"] = S(k for k in NE
                            if D["reach"]["%s/%s/%s" % k]["dp"] is True)
    D["guardHolds"] = S(k for k in ED
                         if D["reach"]["%s/%s/%s" % k]["dp"] is False)
    D["sideEffect"] = S(k for k in NE
                         if k[2] in DESTRUCTIVE
                         and D["reach"]["%s/%s/%s" % k]["dp"] is True
                         and D["reach"]["%s/%s/%s" % k]["objectsDelta"]
                         and D["reach"]["%s/%s/%s" % k]
                         ["objectsDelta"][0] < 0)
    D["dpNoEffect"] = S(k for k in NE
                         if k[2] in DESTRUCTIVE
                         and D["reach"]["%s/%s/%s" % k]["dp"] is True
                         and D["reach"]["%s/%s/%s" % k]["objectsDelta"]
                         and D["reach"]["%s/%s/%s" % k]
                         ["objectsDelta"][0] == 0)
    # ★ Meta 键单独一类（本来就不改对象数）
    D["metaDpTrue"] = S(k for k in NE if k[2].startswith("Meta")
                        and D["reach"]["%s/%s/%s" % k]["dp"] is True)
    D["mismatch"] = S(k for k in NE + ED
                      if D["reach"]["%s/%s/%s" % k]["dp"]
                      is not (k[1] == "noneditable"))
    D["allHadSelection"] = all(c["selectedIds"] for v in D["t"].values()
                               for c in v)
    D["allInstalled"] = all(c["spyInstalled"] for v in D["t"].values()
                            for c in v)
    D["allSawEvent"] = all(c["eventsSeen"] for v in D["t"].values() for c in v)
    D["allReadBoolean"] = all(c["dp"] in (True, False)
                              for v in D["t"].values() for c in v)
    D["dpValueSet"] = sorted({str(c["dp"]) for v in D["t"].values()
                              for c in v})
    return D


def run_checks(a, st, rw):
    D = derive(rw)
    J = {j["id"]: j for j in a.get("judgments") or []}
    F = a.get("findings") or {}
    C = []

    def chk(label, cond, got):
        C.append({"label": label, "pass": bool(cond), "got": got})

    # ── 产物层
    chk("产物：判据 10 条且 id 齐全", sorted(J) == sorted(J_IDS),
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
    chk("产物：观察 ≥3 条", len(a.get("observations") or []) >= 3,
        {"got": len(a.get("observations") or [])})
    chk("产物：本批无新缺陷（只是对 772 的范围更正）",
        a.get("defects") == [], {"got": a.get("defects")})
    corr = a.get("corrections") or []
    chk("产物：更正块 %s" % EXPECT_CORRECTION_IDS,
        sorted(c["id"] for c in corr) == sorted(EXPECT_CORRECTION_IDS),
        {"got": [c["id"] for c in corr]})
    chk("产物：C773-1 明确点名 772 的三处",
        any("772" in str(c.get("targets")) for c in corr
            if c["id"] == "C773-1"),
        {"got": [c.get("targets") for c in corr]})
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
        {"n": st["deskKeydownListenerCount"]})
    chk("静态：★ 5 个分支每走到一个就调一次 preventDefault（行号现读）",
        st["allFivePrevent"] and len(st["preventDefaultLines"]) >= 6,
        {"branches": st["branches"],
         "pdLines": st["preventDefaultLines"]})
    chk("静态：isEditable 早退排在 Delete 与 Meta+C 之前",
        st["guardIsEditableReturn"] and st["guardBeforeDelete"]
        and st["guardBeforeMetaC"],
        {"guard": st["guardIsEditableReturn"]})
    chk("静态：Tab 处理器只认 Tab ⟹ 不污染本批读数",
        st["tabHookGuardsOnTabOnly"], {"got": st["tabHookGuardsOnTabOnly"]})
    chk("产物：静态层与验收器重读的源码一致",
        (a.get("static") or {}).get("preventDefaultLines")
        == st["preventDefaultLines"]
        and (a.get("static") or {}).get("allFiveBranchesPrevent") is True,
        {"got": (a.get("static") or {}).get("preventDefaultLines")})

    # ── 原始读数层
    chk("原始：两个探针各自两轮逐格一致", D["roundsConsistent"],
        {"got": D["roundsConsistent"]})
    chk("原始：★ 合并规则独立复核（773a 无中性臂、SKIP 集合对、无失败）",
        not D["badMerge"], {"got": D["badMerge"]})
    chk("原始：合并铺满 51 格，无缺格",
        not D["missing"] and len(D["merged"]) == len(CELLS),
        {"missing": D["missing"], "merged": len(D["merged"])})
    chk("原始：★ R99 —— defaultPrevented 读到了**两个**不同的值"
        "（不是全 None / 全同）",
        D["allReadBoolean"] and len(D["dpValueSet"]) == 2,
        {"dpValues": D["dpValueSet"]})
    chk("原始：每格间谍装上了、收到了事件、目标有选中",
        D["allInstalled"] and D["allSawEvent"] and D["allHadSelection"],
        {"installed": D["allInstalled"], "events": D["allSawEvent"],
         "selected": D["allHadSelection"]})
    chk("原始：★ 中性键 %s 读到 false（6/6）" % NEUTRAL_KEY,
        D["neutral"] and all(v is False for v in D["neutral"].values()),
        {"got": D["neutral"]})
    chk("原始：★ 分支在 6/6 个浮层跑到了（30/30 格 dp=true）",
        len(D["branchReached"]) == len(NE)
        and len({k.split("/")[0] for k in D["branchReached"]}) == 6,
        {"n": len(D["branchReached"]),
         "disclosures": sorted({k.split("/")[0]
                                for k in D["branchReached"]})})
    chk("原始：★ 守卫对全部五个键一视同仁（15/15 格 dp=false）",
        len(D["guardHolds"]) == len(ED)
        and not D["mismatch"],
        {"n": len(D["guardHolds"]), "mismatch": D["mismatch"]})
    chk("原始：★ 两个信号分开：8 格有副作用、4 格 dp=true 但无副作用",
        len(D["sideEffect"]) == 8 and len(D["dpNoEffect"]) == 4
        and all(k.split("/")[0] in CAM_ONLY for k in D["dpNoEffect"]),
        {"sideEffect": D["sideEffect"], "dpNoEffect": D["dpNoEffect"]})
    chk("原始：★ Meta 键单独归类（18 格 dp=true，且不混进上面两个桶）",
        len(D["metaDpTrue"]) == 18
        and not (set(D["metaDpTrue"]) & set(D["sideEffect"]))
        and not (set(D["metaDpTrue"]) & set(D["dpNoEffect"])),
        {"meta": len(D["metaDpTrue"])})
    chk("产物：与验收器独立重算的结果一致",
        (a.get("branchMap") or {}).get("branchReachedCells")
        == D["branchReached"]
        and (a.get("branchMap") or {}).get("guardHoldsCells")
        == D["guardHolds"]
        and (a.get("branchMap") or {}).get("sideEffectCells")
        == D["sideEffect"]
        and (a.get("branchMap") or {}).get("dpTrueButNoEffectCells")
        == D["dpNoEffect"]
        and (a.get("comparability") or {}).get("provenance")
        == D["provenance"],
        {"branch": (a.get("branchMap") or {}).get("branchReachedCells"),
         "guard": (a.get("branchMap") or {}).get("guardHoldsCells")})
    # ★ S_ 的元素是**字符串**，`k[1]` 取的是第二个字符 —— 这里必须用元组
    desNE = {"%s/%s/%s" % k for k in NE if k[2] in DESTRUCTIVE}
    metaNE = {"%s/%s/%s" % k for k in NE if k[2].startswith("Meta")}
    chk("产物：分类铺满 —— 破坏性 12 格 = 副作用 8 + 无副作用 4，两桶非空且互斥",
        D["dpNoEffect"] and D["sideEffect"]
        and not (set(D["sideEffect"]) & set(D["dpNoEffect"]))
        and set(D["sideEffect"]) | set(D["dpNoEffect"]) == desNE
        and set(D["metaDpTrue"]) == metaNE,
        {"sideEffect": len(D["sideEffect"]),
         "dpNoEffect": len(D["dpNoEffect"]),
         "meta": len(D["metaDpTrue"])})

    # ── README / 台账
    if not README.exists():
        chk("README 存在", False, "缺 README.md")
    else:
        rd = README.read_text(encoding="utf-8")
        chk("README：不含替换字符 U+FFFD", FFFD not in rd,
            {"count": rd.count(FFFD)})
        for need in ("C773-1", "6/6", "defaultPrevented", "R99", "F2"):
            chk("README 提到「%s」" % need, need in rd, None)
        bare = [ln for ln in rd.split("\n")
                if re.match(r"^\|\s*\d+[a-z]?\s*\|", ln)]
        chk("README：表格首格没有裸数字（pre-commit 正则会拦）", not bare,
            {"bare": bare[:3]})
    if not LEDGER.exists():
        chk("台账存在", False, "缺台账")
    else:
        ll = LEDGER.read_text(encoding="utf-8")
        lines = [ln for ln in ll.split("\n") if ln.startswith("| Batch 773 ")]
        chk("台账：Batch 773 恰好一行", len(lines) == 1, {"count": len(lines)})
        if lines:
            chk("台账：该行不含 U+FFFD", FFFD not in lines[0],
                {"count": lines[0].count(FFFD)})
            chk("台账：首格是 `| Batch 773 |`",
                re.match(r"^\|\s*Batch 773\s*\|", lines[0]) is not None,
                {"head": lines[0][:60]})
            chk("台账：恰好 3 列", lines[0].count("|") == 4,
                {"pipes": lines[0].count("|")})
        chk("台账：历史 U+FFFD 仍在 9 处", ll.count(FFFD) == 9,
            {"count": ll.count(FFFD)})
    return C


S_ = ["%s/%s/%s" % k for k in CELLS]


def negative_controls(a, st, rw):
    out = []

    def run(name, mutate, kw):
        rr = copy.deepcopy(rw)
        mutate(rr)
        try:
            cs = run_checks(a, st, rr)
        except SystemExit as e:
            out.append({"name": name, "caught": True, "kwMatchedCount": 1,
                        "why": str(e)[:80]})
            return
        hit = [c for c in cs if kw in c["label"]]
        out.append({"name": name, "kwMatchedCount": len(hit),
                    "kwMatchedAnyLabel": bool(hit),
                    "caught": bool(hit) and not any(c["pass"] for c in hit),
                    "expectFailOn": kw,
                    "stillPassing": [c["label"] for c in hit if c["pass"]]})

    def everyRow(rr, fn, only=None):
        for src in ("A", "B"):
            for rd in rr[src]["rounds"]:
                for r in rd["rows"]:
                    if r.get("SKIPPED"):
                        continue
                    if only and not only(r):
                        continue
                    fn(r)

    def m_neutralTrue(rr):
        """中性键改成 true ⟹ J2 必须红（整批推理作废）"""
        def f(r):
            if r.get("want") == "neutral":
                r["defaultPrevented"] = True
        everyRow(rr, f)

    def m_branchNotReached(rr):
        """把 preset/pathmenu 的 dp 改成 false ⟹ J4/J5 必须红"""
        def f(r):
            if r.get("id") in ("preset", "pathmenu") \
                    and r.get("want") == "noneditable":
                r["defaultPrevented"] = False
        everyRow(rr, f)

    def m_guardBroken(rr):
        """守卫失效（可编辑落点也 dp=true）⟹ J6 必须红"""
        def f(r):
            if r.get("want") == "editable":
                r["defaultPrevented"] = True
        everyRow(rr, f)

    def m_mergeDropNeutral(rr):
        """773b 不再补中性对照 ⟹ 覆盖完整性必须红"""
        rr["B"]["rounds"] = [{"rows": []}, {"rows": []}]

    def m_aGainsNeutral(rr):
        """谎称 773a 也有中性臂 ⟹ 合并规则复核必须红。
        两轮都要加（只加一轮会被「两轮逐格一致」抓到，那就测错了判据）。"""
        for rd in rr["A"]["rounds"]:
            src0 = next(r for r in rd["rows"]
                        if r.get("key") and not r.get("SKIPPED"))
            rd["rows"].append(dict(src0, want="neutral", key=NEUTRAL_KEY,
                                   defaultPrevented=False))

    def m_roundsDiffer(rr):
        rr["A"]["rounds"][1]["rows"][0]["defaultPrevented"] = \
            not rr["A"]["rounds"][0]["rows"][0]["defaultPrevented"]

    def m_dpAllNone(rr):
        """R99：把读数全改成 None ⟹ 必须红"""
        everyRow(rr, lambda r: r.__setitem__("defaultPrevented", None))

    def m_noSelection(rr):
        def f(r):
            if r.get("id") == "export" and r.get("want") == "noneditable" \
                    and r.get("key") == "Delete":
                r["selectedIds"] = []
        everyRow(rr, f)

    def m_nonCamNoEffect(rr):
        """让一个**非** cameraTrack 的层也出现「dp=true 但没副作用」
        ⟹ 「全部落在 cameraTrack 两层」必须红"""
        def f(r):
            if r.get("id") == "crowd" and r.get("want") == "noneditable" \
                    and r.get("key") == "Delete":
                r["objectsDelta"] = 0
        everyRow(rr, f)

    run("中性键改成 true（读数方法的前提被破坏）",
        m_neutralTrue, "中性键")
    run("把 preset/pathmenu 的 dp 改成 false（谎称分支没跑到）",
        m_branchNotReached, "6/6 个浮层跑到了")
    run("守卫失效（可编辑落点也放行）",
        m_guardBroken, "五个键一视同仁")
    run("773b 不再补中性对照（覆盖不完整）",
        m_mergeDropNeutral, "合并规则独立复核")
    run("谎称 773a 也有中性臂（合并规则要重算）",
        m_aGainsNeutral, "合并规则独立复核")
    run("第二轮的读数被改掉",
        m_roundsDiffer, "两轮逐格一致")
    run("★ R99：把 defaultPrevented 全改成 None",
        m_dpAllNone, "读到了**两个**不同的值")
    run("把一格的目标选中抹掉",
        m_noSelection, "目标有选中")
    run("让非 cameraTrack 的层也出现「dp=true 但没副作用」",
        m_nonCamNoEffect, "两个信号分开")

    def aproduct(name, mutate, kw):
        aa = copy.deepcopy(a)
        mutate(aa)
        cs = run_checks(aa, st, rw)
        hit = [c for c in cs if kw in c["label"]]
        out.append({"name": name, "kwMatchedCount": len(hit),
                    "kwMatchedAnyLabel": bool(hit),
                    "caught": bool(hit) and not any(c["pass"] for c in hit),
                    "expectFailOn": kw,
                    "stillPassing": [c["label"] for c in hit if c["pass"]]})

    aproduct("篡改一条判据的 evidence",
             lambda x: [j.update(evidence={"x": 1}) for j in x["judgments"]
                        if j["id"] == "J4"], "evidence 等于 findings")
    aproduct("删掉一个 findings 键",
             lambda x: x["findings"].pop("F3_branchReached", None),
             "evidence 等于 findings")
    aproduct("删掉更正 C773-1",
             lambda x: x.__setitem__("corrections", []), "更正块")
    aproduct("给本批塞一个假的新缺陷",
             lambda x: x.__setitem__("defects", [{"id": "DX"}]),
             "本批无新缺陷")
    aproduct("删掉一条探针教训",
             lambda x: x.__setitem__(
                 "probeLessons",
                 [y for y in x["probeLessons"] if y["id"] != "R99"]),
             "教训")

    def text_run(name, path, old, new, kw):
        if not path.exists():
            out.append({"name": name, "caught": False, "kwMatchedCount": 0,
                        "why": "文件不存在"})
            return
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            out.append({"name": name, "caught": False, "kwMatchedCount": 0,
                        "why": "锚点没找到：%r" % old[:40]})
            return
        try:
            path.write_text(orig.replace(old, new, 1), encoding="utf-8")
            cs = run_checks(a, st, rw)
            hit = [c for c in cs if kw in c["label"]]
            out.append({"name": name, "kwMatchedCount": len(hit),
                        "kwMatchedAnyLabel": bool(hit),
                        "caught": bool(hit) and not any(c["pass"] for c in hit),
                        "expectFailOn": kw,
                        "stillPassing": [c["label"] for c in hit if c["pass"]]})
        finally:
            path.write_text(orig, encoding="utf-8")

    text_run("把台账 Batch 773 行改名", LEDGER, "| Batch 773 ",
             "| Batch 773X ", "台账：Batch 773 恰好一行")
    if README.exists():
        rd = README.read_text(encoding="utf-8")
        anchor = next((ln for ln in rd.split("\n")
                       if ln.startswith("|")), "")
        text_run("把 README 表格首格改成裸数字", README, anchor,
                 "| 773 | x | y |", "首格没有裸数字")
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
    kw_bad = [n["name"] for n in neg if n.get("kwMatchedCount") != 1]
    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg
                 if n["caught"] and n.get("kwMatchedCount") == 1)
    ok = npass == total and neg_ok == len(neg)
    REPORT.write_text(json.dumps(
        {"batch": 773, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "negativeKwBroken": kw_bad,
         "rawError": rawErr, "ok": ok}, ensure_ascii=False, indent=1),
        encoding="utf-8")
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
    print("batch 773 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
