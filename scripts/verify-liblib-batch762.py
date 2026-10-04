"""batch 762 验收器：导演台的焦点围栏与键盘可达性（**零缺陷批次**）

三层结构（与 753–761 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
  2. **产物层** —— 判据条数、两段探针轮次、证据链、返工条目、不声称清单
  3. **原始读数交叉核对** —— 从 `docs/research/.../raw/` 两份原始输出
     **按正确键名重算**全部派生量，与产物逐项对账；缺失时**判失败而不是通过**。

⚠ 本批特意盯住「**零缺陷**」这个结论本身**能不能被伪造**：
  一批全是「没问题的」时，最容易出的事就是把某一条读数改成「有问题」再蒙混过关。
  所以阴性对照里有一整组专挑「把结案改回缺陷」的注入。

⚠ 两段探针轮次不同（a 两轮、b 单轮），产物必须**如实**这么写，
  不许把单轮说成两轮 —— 这本身是一条检查。

判据 **12 条**。
"""
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch762-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def static_side():
    desk = src("src/components/director/DirectorDesk.tsx")
    rail = src("src/components/director/DirectorIconRail.tsx")
    page = src("src/app/page.tsx")
    node = src("src/components/nodes/ScriptExecutionNode.tsx")

    all_src = []
    for p in sorted((ROOT / "src").rglob("*.ts*")):
        try:
            all_src.append(p.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "roleDialog": 'role="dialog"' in desk,
        "ariaModal": 'aria-modal="true"' in desk,
        "focusScopeHook": 'data-director-focus-scope="workspace"' in desk,
        "focusReturnHook": "data-director-focus-return={returnDisposition}" in desk,
        "focusStateHook": "data-director-focus-state={" in desk,
        "inertOnTree": ("inert={treeMobileInactive || viewportPanelsCollapsed}"
                        in desk),
        "ariaHiddenOnTree": ("aria-hidden={\n          viewportPanelsCollapsed || "
                             "treeMobileInactive ? \"true\" : undefined" in desk),
        "mountFocus": "workspaceRef.current?.focus({ preventScroll: true })" in desk,
        "escHandlerMobile": 'event.key === "Escape" && activeMobilePanel' in desk,
        "escHandlerSecond": 'if (event.key !== "Escape") return;' in desk,
        # 折叠与恢复
        "toggleHook": 'data-director-panels-toggle' in desk,
        "toggleOnlyWhenExpanded": ("{!viewportPanelsCollapsed ? (" in desk),
        "toggleCollapsesOnlyTrue": "setViewportPanelsCollapsed(true)" in desk,
        "restoreViaRail": 'if (id === "scene") {' in rail
        and "setViewportPanelsCollapsed(false);" in rail,
        "restoreComment": "点图标栏的「场景」条目即恢复" in rail,
        # 入口
        "entryHook": "data-open-director" in node,
        "entryCalls": "openDirectorDesk(id, activeCanvasId)" in node,
        "renderGate": "activeDirectorNodeId && activeDirectorCanvasId" in page,
        # 两个隐藏 file input
        "hiddenFileInputRail": ('aria-label="导入本地角色模型"' in rail
                                and 'className="hidden"' in rail),
        "hiddenFileInputDesk": ('data-director-project-import-input' in desk
                                and 'className="hidden"' in desk),
        "deskInputHasAriaLabel": 'data-director-project-import-input" aria-label'
                                 in desk,
    }


def raw_side():
    data = {}
    for k in ("a", "b"):
        p = RAWDIR / ("vb762%s.json" % k)
        if not p.exists():
            raise FileNotFoundError(str(p))
        data[k] = json.loads(p.read_text(encoding="utf-8"))
    ra = data["a"]["rounds"][0]
    rb = data["b"]["rounds"][0]

    fence_recomputed = {
        "forward": {"presses": ra["D2_tabForward"]["steps"] - 1,
                    "escaped": ra["D2_tabForward"]["escapedCount"],
                    "body": len(ra["D2_tabForward"]["bodyHits"])},
        "backward": {"presses": ra["D4_tabBackward"]["steps"] - 1,
                     "escaped": ra["D4_tabBackward"]["escapedCount"],
                     "body": len(ra["D4_tabBackward"]["bodyHits"])},
    }
    fence_recomputed["totalPresses"] = (fence_recomputed["forward"]["presses"]
                                        + fence_recomputed["backward"]["presses"])
    fence_recomputed["totalEscapes"] = (fence_recomputed["forward"]["escaped"]
                                        + fence_recomputed["backward"]["escaped"])
    fence_recomputed["totalBodyHits"] = (fence_recomputed["forward"]["body"]
                                         + fence_recomputed["backward"]["body"])

    b1 = rb["B1_list"]
    st = rb["B2_after"]
    by_label = {x["ariaLabel"]: x for x in st["panels"]}

    return {
        "aRounds": len(data["a"]["rounds"]),
        "aConsistent": data["a"]["consistent"],
        "bRounds": len(data["b"]["rounds"]),
        "desk": ra["D1_desk"],
        "openActive": ra["D1_activeOnOpen"],
        "fence": fence_recomputed,
        "fenceRawEscapedAt": [ra["D2_tabForward"]["escapedAt"],
                              ra["D4_tabBackward"]["escapedAt"]],
        "escClosed": (ra["D6_afterEsc"].get("desk") or {}).get("open") is False,
        "escFocusIsTrigger": bool(
            ((ra["D6_afterEsc"].get("active") or {}).get("el") or {})
            .get("dataOpenDirector")),
        "escFromChildBefore": rb.get("B4_focusBeforeEsc"),
        "escFromChildAfter": rb.get("B4_afterEsc"),
        "escWhileCollapsed": rb.get("B3_escClosed"),
        "focusAfterSecondClose": rb.get("B3_focusAfter"),
        "focusables": {
            "total": b1["total"], "reachable": b1["reachable"],
            "unreachable": b1["unreachable"],
            "all": [{"tag": u["tag"], "ariaLabel": u["ariaLabel"],
                     "display": u["display"], "cls": u["cls"]}
                    for u in b1["unreachableList"]],
            "allHiddenFileInputs": all(
                u["tag"] == "INPUT" and (u["cls"] or "").startswith("hidden")
                for u in b1["unreachableList"]),
        },
        "collapsed": {
            "attr": st["collapsed"], "togglePresent": st["togglePresent"],
            "tree": by_label.get("场景对象"), "inspector": by_label.get("属性"),
            "reachableBefore": (rb["B1_focusable"] or {}).get("reachable"),
            "reachableAfter": (rb["B2_focusable"] or {}).get("reachable"),
            "tabSteps": rb["B2_tab"]["steps"],
            "tabEscaped": rb["B2_tab"]["escapedCount"],
        },
    }


def run_checks(a, st, rw):
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    try:
        _body(a, st, rw, ck)
    except Exception as e:
        ck("检查器自身未因结构破坏而崩溃", False, repr(e))
    return checks


def _body(a, st, rw, ck):
    J = {j["no"]: j for j in a["judgments"]}
    a1 = a["judgments"]
    f = a["findings"]

    # ================= 静态层 =================
    ck("静态：导演台是 role=dialog + aria-modal=true 的模态框",
       st["roleDialog"] and st["ariaModal"])
    ck("静态：三枚焦点钩子都在（scope / return / state）",
       st["focusScopeHook"] and st["focusReturnHook"] and st["focusStateHook"])
    ck("静态：场景树面板同时挂了 inert 与 aria-hidden",
       st["inertOnTree"] and st["ariaHiddenOnTree"])
    ck("静态：挂载时用 rAF 把焦点打到 workspaceRef",
       st["mountFocus"])
    ck("静态：两个 Escape 处理器都在源码里", st["escHandlerMobile"]
       and st["escHandlerSecond"])
    ck("静态：收起按钮 data-director-panels-toggle 且只在展开态渲染",
       st["toggleHook"] and st["toggleOnlyWhenExpanded"]
       and st["toggleCollapsesOnlyTrue"])
    ck("静态：★ 恢复入口存在 —— rail 里 scene 条目调 "
       "setViewportPanelsCollapsed(false)，且注释写明与源站核对过",
       st["restoreViaRail"] and st["restoreComment"])
    ck("静态：入口链路完整（节点按钮 → openDirectorDesk → page 渲染门）",
       st["entryHook"] and st["entryCalls"] and st["renderGate"])
    ck("静态：两个不可达元素在源码里都是 input[type=file] + className=hidden",
       st["hiddenFileInputRail"] and st["hiddenFileInputDesk"])
    ck("静态：rail 那个 input 有 aria-label、desk 那个没有（记为措辞不一致）",
       (not st["deskInputHasAriaLabel"]) and st["hiddenFileInputRail"])

    # ================= 产物层 =================
    ck("产物：判据 12 条且编号连续 1..12",
       len(a1) == 12 and a["judgeCount"] == 12 and sorted(J) == list(range(1, 13)),
       sorted(J))
    ck("产物：★ 如实记录轮次 —— a 两轮且一致、b 单轮且标注不适用两轮判定",
       rw["aRounds"] == 2 and rw["aConsistent"] is True
       and a["twoRound"]["probeA"]["rounds"] == 2
       and a["twoRound"]["probeA"]["consistent"] is True
       and a["twoRound"]["probeB"]["rounds"] == 1
       and a["twoRound"]["probeB"]["consistent"] is None
       and "单轮" in a["twoRound"]["probeB"]["note"])
    ck("产物：allConsistent 的取值等于探针 a 自己的结论（不掺单轮的 b）",
       a["twoRound"]["allConsistent"] == rw["aConsistent"] is True
       and "762b 是单轮" in a["twoRound"]["caveat"])
    ck("产物：返工 5 条（R48 探针工具写死 / R49 按文案找图标按钮 / "
       "R50 读错元素 / R51 差点误报 / R52 同一个洞第四次复发）",
       len(a["rework"]) == 5
       and {"R48", "R49", "R50", "R51", "R52"} == {r["id"] for r in a["rework"]}
       and any("图标按钮只能按钩子找" in r["lesson"] for r in a["rework"])
       and any("看着不对" in r["lesson"] for r in a["rework"])
       and any(r["id"] == "R52" and "第四次" in r["lesson"]
               for r in a["rework"]))
    ck("产物：不声称 ≥ 8 条，含「没有与源站对照」与「b 是单轮」",
       len(a["notClaimed"]) >= 8
       and any("源站" in s for s in a["notClaimed"])
       and any("单轮" in s for s in a["notClaimed"]))
    ck("产物：headline 写明「0 缺陷」且点名三处结案的理由"
       "（标准做法 / 刻意设计 / 措辞问题）",
       "0 缺陷" in a["headline"]
       and "标准的隐藏 file input" in a["headline"]
       and "刻意设计" in a["headline"]
       and "措辞" in a["headline"])

    # ================= 原始读数交叉核对 =================
    d = rw["desk"]
    ck("原始：dialog 本体读数与重算一致（aria-modal / 三枚焦点 / 最上层）",
       J[1]["evidence"]["ariaModal"] == d["ariaModal"]
       == "true" and J[1]["evidence"]["zIndex"] == d["zIndex"]
       and J[1]["evidence"]["isTopmostAtCenter"] == d["isTopmostAtCenter"]
       and J[2]["evidence"]["focusScope"] == d["focusScope"]
       and J[2]["evidence"]["focusState"] == d["focusState"]
       and J[2]["evidence"]["focusReturn"] == d["focusReturn"])
    ao = rw["openActive"]
    ck("原始：打开瞬间焦点在 dialog 内、不是 body",
       ao["inDialog"] is True and ao["body"] is False
       and ao["el"]["role"] == "dialog"
       and ao["el"]["ariaLabel"] == "3D导演台工作区")
    ck("原始：产物判据 3 的打开焦点证据与重算一致",
       J[3]["evidence"]["inDialog"] == ao["inDialog"]
       and J[3]["evidence"]["isBody"] == ao["body"]
       and J[3]["evidence"]["role"] == ao["el"]["role"])

    fr = rw["fence"]
    ck("原始：★ 围栏计数与重算一致（36 次按键 / 0 次逃出 / 0 次落 body）",
       J[4]["evidence"]["totalPresses"] == fr["totalPresses"] == 36
       and J[4]["evidence"]["totalEscapes"] == fr["totalEscapes"] == 0
       and J[4]["evidence"]["totalBodyHits"] == fr["totalBodyHits"] == 0, fr)
    ck("原始：正向与反向的 escapedAt 都是空数组（不是只看了总数）",
       rw["fenceRawEscapedAt"] == [[], []])
    ck("原始：★ 判据 4 确实写着 36/0/0 的结论",
       "36" in J[4]["text"] and "0 次焦点逃出" in J[4]["text"])

    ck("原始：Esc 关闭与焦点返回触发按钮，与重算一致",
       rw["escClosed"] is True and rw["escFocusIsTrigger"] is True
       and J[5]["evidence"]["closed"] is True
       and J[6]["evidence"]["focusIsTrigger"] is True)
    ck("原始：折叠态下 Esc 也能关闭，关闭后焦点回触发按钮",
       rw["escWhileCollapsed"] is True
       and J[8]["evidence"]["escWorksWhileCollapsed"] is True
       and ((rw["focusAfterSecondClose"] or {}).get("text")
            == "打开导演台 →"))
    ck("原始：焦点在子面板按钮上时 Esc 前后读数都在（前置在 dialog 内、后置关闭）",
       (rw["escFromChildBefore"] or {}).get("inDialog") is True
       and (rw["escFromChildAfter"] or {}).get("open") is False
       and J[7]["evidence"]["beforeEsc"]["inDialog"] is True)

    fx = rw["focusables"]
    ck("原始：可聚焦元素计数（128 / 126 / 2）与重算一致",
       fx["total"] == 128 and fx["reachable"] == 126 and fx["unreachable"] == 2
       and J[9]["evidence"]["total"] == fx["total"]
       and J[9]["evidence"]["reachable"] == fx["reachable"]
       and J[9]["evidence"]["unreachable"] == fx["unreachable"])
    ck("原始：那两个不可达元素逐个点名，且确实是隐藏 file input",
       len(J[9]["evidence"]["unreachableList"]) == 2
       and [u["ariaLabel"] for u in J[9]["evidence"]["unreachableList"]]
       == [u["ariaLabel"] for u in fx["all"]]
       and fx["allHiddenFileInputs"] is True
       and J[10]["evidence"]["allUnreachableAreHiddenFileInputs"] is True)
    ck("原始：★ 判据 10 明确把它判为「不是缺陷」",
       "不是缺陷" in J[10]["text"]
       and "标准做法" in J[10]["text"])

    co = rw["collapsed"]
    ck("原始：折叠后树面板 inert / aria-hidden / display / 宽 0 四项齐全",
       co["attr"] == "true" and co["tree"]["inert"] is True
       and co["tree"]["ariaHidden"] == "true"
       and co["tree"]["display"] == "none" and co["tree"]["w"] == 0)
    ck("原始：折叠后收起按钮本身不存在",
       co["togglePresent"] is False
       and J[12]["evidence"]["togglePresentWhenCollapsed"] is False)
    ck("原始：可达焦点 126 → 125，围栏仍成立（Tab 14 步 0 次逃出）",
       co["reachableBefore"] == 126 and co["reachableAfter"] == 125
       and co["tabSteps"] == 14 and co["tabEscaped"] == 0
       and J[11]["evidence"]["reachableFocusablesBefore"] == 126
       and J[11]["evidence"]["reachableFocusablesAfter"] == 125
       and J[11]["evidence"]["tabAfterCollapse"]["escapedCount"] == 0)
    ck("原始：★ 判据 12 判为刻意设计而非缺陷",
       "不是缺陷" in J[12]["text"] and "Batch 587" in J[12]["text"]
       and "IconRail" in J[12]["evidence"]["static"])

    # ---------- 产物 == 重算（759 的 R33 / 760 的 R38 / 761 的 R46）----------
    ck("结构：findings.dialog 与判据 1 的证据同源",
       f["dialog"] == J[1]["evidence"])
    ck("结构：findings.openFocus 与判据 3 的证据同源",
       f["openFocus"] == J[3]["evidence"])
    ck("结构：findings.fence 与判据 4 的证据同源",
       f["fence"] == J[4]["evidence"])
    ck("结构：findings.focusables 与判据 9 的证据同源",
       f["focusables"] == J[9]["evidence"])
    ck("结构：findings.collapsedFence 与判据 11 的证据同源",
       f["collapsedFence"] == J[11]["evidence"])
    ck("结构：findings.escAndReturn 与判据 6 的关键字段一致",
       f["escAndReturn"]["closed"] == J[5]["evidence"]["closed"]
       and f["escAndReturn"]["focusIsTrigger"]
       == J[6]["evidence"]["focusIsTrigger"]
       and f["escAndReturn"]["escWorksWhileCollapsed"]
       == J[8]["evidence"]["escWorksWhileCollapsed"])


def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # ---- 专门伪造「结案 → 缺陷」，这是零缺陷批次最需要防的一类 ----
    inj("★ 把判据 12（恢复入口）从设计改判成缺陷", lambda x:
        x["judgments"][11].__setitem__("text", "折叠后没有恢复入口，是一个缺陷"))
    inj("★ 把判据 10（隐藏 file input）从结案改判成缺陷", lambda x:
        x["judgments"][9].__setitem__("text", "这两个元素不可达，是一个缺陷"))
    inj("★ 把 headline 的「0 缺陷」抹掉", lambda x:
        x.__setitem__("headline", "导演台的焦点围栏有问题"))
    inj("伪造有焦点逃出了 dialog", lambda x:
        x["judgments"][3]["evidence"].__setitem__("totalEscapes", 1))
    inj("伪造按键次数被少算（24 写成 12）", lambda x:
        x["judgments"][3]["evidence"].__setitem__("totalPresses", 12))
    inj("伪造正向有 3 次落到 body", lambda x:
        x["findings"]["fence"]["forward"].__setitem__("bodyHits", [1, 2, 3]))
    inj("伪造折叠后 Tab 逃出了 dialog", lambda x:
        x["findings"]["collapsedFence"]["tabAfterCollapse"].__setitem__(
            "escapedCount", 2))
    inj("伪造折叠后树面板没 inert", lambda x:
        x["findings"]["collapsedFence"].__setitem__("treeInert", False))
    inj("伪造 inert 与 aria-hidden 不同步", lambda x:
        x["findings"]["collapsedFence"].__setitem__(
            "inertAriaHiddenInSync", False))
    inj("伪造 Esc 关不掉导演台", lambda x:
        x["findings"]["escAndReturn"].__setitem__("closed", False))
    inj("伪造焦点没回到触发按钮", lambda x:
        x["findings"]["escAndReturn"].__setitem__("focusIsTrigger", False))
    inj("伪造打开瞬间焦点停在 body 上", lambda x:
        x["findings"]["openFocus"].__setitem__("inDialog", False))
    inj("伪造 focus-return 不是 trigger", lambda x:
        x["judgments"][1]["evidence"].__setitem__("focusReturn", "none"))
    inj("伪造不可达元素变成 3 个", lambda x:
        x["judgments"][8]["evidence"].__setitem__("unreachable", 3))
    inj("伪造其中有不可达元素不是隐藏 file input", lambda x:
        x["findings"]["focusables"].__setitem__(
            "allUnreachableAreHiddenFileInputs", False))
    inj("★ 把 b 探针的轮次谎报成两轮", lambda x:
        x["twoRound"]["probeB"].__setitem__("rounds", 2))
    inj("把 b 的 consistent 从 null 改成 true", lambda x:
        x["twoRound"]["probeB"].__setitem__("consistent", True))
    inj("删掉返工 R49（按文案找图标按钮）", lambda x:
        x.__setitem__("rework", [r for r in x["rework"] if r["id"] != "R49"]))
    inj("清空不声称清单", lambda x: x.__setitem__("notClaimed", []))
    inj("删掉判据 4", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["no"] != 4]))
    inj("伪造 aria-modal 不是 true", lambda x:
        x["findings"]["dialog"].__setitem__("ariaModal", "false"))
    inj("只改 findings.dialog 的 ariaModal（判据证据那一份不动）", lambda x:
        x["findings"]["dialog"].__setitem__("ariaModal", "false"))
    inj("只改 findings.openFocus 的 inDialog（判据证据那一份不动）", lambda x:
        x["findings"]["openFocus"].__setitem__("inDialog", False))
    inj("只改 findings.fence 的 totalEscapes（判据证据那一份不动）", lambda x:
        x["findings"]["fence"].__setitem__("totalEscapes", 4))
    inj("只改 findings.focusables 的 unreachable（判据证据那一份不动）", lambda x:
        x["findings"]["focusables"].__setitem__("unreachable", 7))
    inj("只改 findings.collapsedFence 的 treeInert（判据证据那一份不动）", lambda x:
        x["findings"]["collapsedFence"].__setitem__("treeInert", False))
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
        {"label": "原始读数可用（raw/ 下两份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 762, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:200]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 762 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
