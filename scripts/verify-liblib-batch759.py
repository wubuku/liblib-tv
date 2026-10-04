"""batch 759 验收器：/project 页首轮普查（含一处高严重度缺陷）

三层结构（与 753–758 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （回收站「30 天」文案周边无任何时间运算、卡片副行复用 today、
      侧栏 9 个 stub、openCanvas 先 setActiveCanvas 再 window.open、
      回收站按钮的 onClick 不碰 status、TopNavBar 是唯一 /project 入口…）
  2. **产物层** —— 判据条数、两轮一致性、证据链、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb759{a,b}.json` 还在，把产物里的关键
     读数与探针原始输出逐个对账。缺失时**判失败而不是通过**。

⚠ 本批有一条**跨批次连锁**结论（判据 6）：默认 2 张画布下删不掉画布，
  根因在 batch 755 的行内菜单被 `overflow:hidden` 裁掉。
  这条必须靠**阳性对照**（6 张顶行 4/4 可点）才站得住，否则无法区分
  「不可达」与「我没点到」—— 那是 755 立下的规矩。

判据 **14 条**（759a 两轮一致 + 759b 单轮链路实验）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch759-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAWA = pathlib.Path("/tmp/vb759a.json")
RAWB = pathlib.Path("/tmp/vb759b.json")
GEN = re.compile(r"-\d{10,}-[a-z0-9]{6}\b")


def _strip(o):
    if isinstance(o, str):
        return GEN.sub("-<gen>", o)
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def static_side():
    page = (ROOT / "src/app/project/page.tsx").read_text(encoding="utf-8")
    nav = (ROOT / "src/components/TopNavBar.tsx").read_text(encoding="utf-8")
    dd = (ROOT / "src/components/CanvasTabDropdown.tsx").read_text(
        encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")

    i30 = page.find("剩余 30 天")
    remain_ctx = page[max(0, i30 - 160):i30 + 40]
    i_hdr = page.find("仅显示最近 30 天内删除的内容")

    # 回收站按钮的 onClick
    rb = page[page.find("data-project-recycle") - 300:
              page.find("data-project-recycle") + 700]
    m = re.search(r"data-project-recycle[\s\S]{0,600}?onClick=\{\(\) => ([^}]*)\}",
                  rb)

    return {
        "dataHookCount": len(set(re.findall(r"data-[a-z0-9-]+", page))),
        "header30Copy": i_hdr > 0,
        "remain30Copy": i30 > 0,
        # 「剩余 30 天」周边没有任何时间运算 ⟹ 硬编码
        "remainCtxNoTimeMath": not re.search(
            r"Date|dayjs|moment|diff|getTime|30\s*[-+*/]", remain_ctx),
        "noFilterInRecycle": not re.search(
            r"removedCanvases\s*\.\s*filter", page),
        "removedCanvasesMapOnly": "removedCanvases.map((canvas) => (" in page,
        "todayDeclared": bool(re.search(
            r"const today = new Date\(\)\.toISOString\(\)\.slice\(0, 10\)", page)),
        "cardUsesToday": bool(re.search(r"\{\s*today\s*\}", page)),
        # ⚠ createdAt **在类型里是存在的**（`createdAt: string;`），
        # 真正的问题是：种子画布没赋值 + 页面根本不读它。
        "createdAtInType": bool(re.search(r"createdAt\s*:\s*string", store)),
        "createdAtAssignedInSeed": bool(re.search(
            r"canvas-2[\s\S]{0,600}?createdAt\s*:", store)),
        "pageIgnoresCreatedAt": "canvas.createdAt" not in page,
        "stubCopyCount": len(re.findall(r"本地原型：(.+?)未接入", page)),
        "recycleOnClick": (m.group(1).strip() if m else None),
        "recycleOnClickNoStatus": bool(m) and "setStatus" not in m.group(1),
        "openCanvasOrder": bool(re.search(
            r"const openCanvas[\s\S]{0,300}?setActiveCanvas\(canvasId\);"
            r"[\s\S]{0,120}?window\.open\(", page)),
        "newProjectAlsoWindowOpen": 'addCanvas();\n              window.open("/", "_blank");'
        in page or bool(re.search(
            r"data-sidebar-new-project[\s\S]{0,300}?addCanvas\(\)[\s\S]{0,200}?"
            r"window\.open\(", page)),
        "createCardRouterPush": bool(re.search(
            r"data-project-create-card[\s\S]{0,300}?addCanvas\(\)[\s\S]{0,200}?"
            r"router\.push\(", page)),
        "onlyProjectEntry": len(re.findall(r'"/project"', nav)),
        "topNavMenuItem": 'data-project-menu-item={item}' in nav
        and 'item === "全部项目"' in nav,
        "topNavRenderedByCanvas": "<TopNavBar />" in (
            ROOT / "src/app/page.tsx").read_text(encoding="utf-8"),
        # 755 的根因：行内菜单被祖先 overflow:hidden 裁掉
        "rowMenuTopFull": bool(re.search(
            r'className="absolute right-2 top-full z-50 w-36', dd)),
        "dropdownOverflowHidden": bool(re.search(
            r'data-liblib-overlay="canvas-dropdown"[\s\S]{0,200}?overflow-hidden',
            dd)),
        "deleteItemGated": "canvases.length > 1 && (" in dd,
        "moreBtnOpacity0": "opacity-0 transition-opacity" in dd,
        "moreBtnAria": 'aria-label="更多操作"' in dd,
        "menuOpenIdGated": "menuOpenId === canvas.id && (" in dd,
        "unrecoverableCopy": "此操作不可恢复" in dd,
        "softDeleteRemovedAt": "removedAt" in store,
        "purgeZeroCallers": len(re.findall(r"purgeRemovedCanvas", store)) <= 2,
    }


def main():
    page_txt = ""
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    J = {j["no"]: j for j in a["judgments"]}
    a1 = a["judgments"]

    # ================= 静态层 =================
    ck("静态：/project 页面 21 个 data-* 钩子",
       st["dataHookCount"] == a["seed"]["dataHookCount"] == 21,
       st["dataHookCount"])
    ck("静态：回收站两处「30 天」文案都在",
       st["header30Copy"] and st["remain30Copy"])
    ck("静态：「剩余 30 天」周边 160 字符内无任何时间运算（硬编码）",
       st["remainCtxNoTimeMath"])
    ck("静态：removedCanvases 只有 map、没有 filter（面板不做 30 天过滤）",
       st["noFilterInRecycle"] and st["removedCanvasesMapOnly"])
    ck("静态：卡片副行复用 {today}；createdAt 在类型里存在但种子未赋值、"
       "页面也不读它",
       st["todayDeclared"] and st["cardUsesToday"]
       and st["createdAtInType"] and not st["createdAtAssignedInSeed"]
       and st["pageIgnoresCreatedAt"],
       [st["createdAtInType"], st["createdAtAssignedInSeed"],
        st["pageIgnoresCreatedAt"]])
    ck("静态：源码里 9 处「本地原型：X 未接入」",
       st["stubCopyCount"] == 9, st["stubCopyCount"])
    ck("静态：回收站按钮的 onClick 只 setRecycleOpen、不碰 status",
       st["recycleOnClickNoStatus"], st["recycleOnClick"])
    ck("静态：openCanvas 先 setActiveCanvas 再 window.open",
       st["openCanvasOrder"])
    ck("静态：新建项目也走 window.open；创建卡走 router.push（两者不一致）",
       st["newProjectAlsoWindowOpen"] and st["createCardRouterPush"])
    ck("静态：/project 入口只在 TopNavBar 一处，且由画布页渲染",
       st["onlyProjectEntry"] == 1 and st["topNavMenuItem"]
       and st["topNavRenderedByCanvas"], st["onlyProjectEntry"])
    ck("静态：755 的根因仍在（行内菜单 top-full + 祖先 overflow-hidden）",
       st["rowMenuTopFull"] and st["dropdownOverflowHidden"])
    ck("静态：删除项受 canvases.length > 1 门控",
       st["deleteItemGated"])
    ck("静态：行内菜单由 menuOpenId 门控、开关是 opacity-0 的「更多操作」",
       st["menuOpenIdGated"] and st["moreBtnOpacity0"] and st["moreBtnAria"])
    ck("静态：确认框「此操作不可恢复」与 store 的软删除（removedAt）并存",
       st["unrecoverableCopy"] and st["softDeleteRemovedAt"])

    # ================= 产物层 =================
    ck("产物：判据 14 条且编号连续 1..14",
       len(a1) == 14 and a["judgeCount"] == 14 and sorted(J) == list(range(1, 15)),
       sorted(J))
    ck("产物：759a 两轮一致且 roundDiff 为空",
       a["twoRound"]["consistent"] is True and a["twoRound"]["diff"] == {},
       sorted(a["twoRound"]["diff"].keys()))
    ck("产物：声明 759b 是单轮链路实验、不适用两轮判定",
       "单轮" in a["twoRound"]["bNote"]
       and "阳性/阴性对照" in a["twoRound"]["bNote"])
    # ⚠ 两张卡的 spans **本来就不全等**（名字与节点数不同），只有日期段相同
    # ⟹ 只能比「日期样式的 span」，比整个 spans 会永远判不一致
    ds = J[3]["evidence"]["dateSpansOnly"]
    ck("产物：判据 3 的两张卡日期段相同，且 createdAt 运行时为 null",
       len({tuple(v) for v in ds.values()}) == 1
       and len(list(ds.values())[0]) == 1
       and all(x["createdAt"] is None
               for x in J[3]["evidence"]["storeCanvasFields"]),
       ds)
    ck("产物：判据 4 记下老化前后两组条目文案，且「剩余 30 天」两边都在",
       "剩余 30 天" in json.dumps(J[4]["evidence"]["beforeAging"],
                                  ensure_ascii=False)
       and "剩余 30 天" in json.dumps(J[4]["evidence"]["afterAging"],
                                      ensure_ascii=False)
       and J[4]["evidence"]["staticNoTimeMath"] is True)
    ck("产物：判据 4 明确标注这一格是程序化造数",
       "程序化造数据" in J[4]["evidence"]["seeding"])
    ck("产物：判据 5 证明回收站面板本身功能正常（勾选 + 恢复所选）",
       "已选择 1 项" in J[5]["evidence"]["afterCheck"]["selection"]
       and J[5]["evidence"]["restoreSelectedHit"]["hitSelf"] is True)
    t2 = J[6]["evidence"]["twoCanvases"]["items"]
    s6 = J[7]["evidence"]["sixCanvases"]["items"]
    ck("产物：判据 6/7 的两档构成阳性/阴性对照（2 张 1/4 且删除项不可点、"
       "6 张 4/4）",
       sum(1 for x in t2 if x["hitSelf"]) == 1
       and t2[0]["text"] == "在新窗口打开"
       and next(x for x in t2 if x["text"] == "删除画布")["hitSelf"] is False
       and all(x["hitSelf"] for x in s6),
       (sum(1 for x in t2 if x["hitSelf"]), sum(1 for x in s6 if x["hitSelf"])))
    ck("产物：判据 6 的 deleteItem 自身与 items 列表一致，且 hitSelf=false",
       # ⚠ 负向对照抓到过这个洞：deleteItem.hitSelf 没有任何断言，
       # 把它伪造成 true 竟然能过 51/51。
       J[6]["evidence"]["twoCanvases"]["deleteItem"]["hitSelf"] is False
       and J[6]["evidence"]["twoCanvases"]["deleteItem"]["text"] == "删除画布"
       and J[6]["evidence"]["twoCanvases"]["deleteItem"]["hitSelf"]
       == next(x["hitSelf"] for x in t2 if x["text"] == "删除画布"),
       J[6]["evidence"]["twoCanvases"]["deleteItem"])
    ck("产物：判据 7 的 6 张档 deleteItem 同样 hitSelf=true",
       J[7]["evidence"]["sixCanvases"].get("deleteItem", {}).get("hitSelf")
       is True
       and J[7]["evidence"]["sixCanvases"]["deleteItem"]["topTag"] == "BUTTON",
       J[7]["evidence"]["sixCanvases"].get("deleteItem"))
    ck("产物：判据 6 指出删除项落点命中 IMG（不是按钮、也不是画布背景）",
       J[6]["evidence"]["twoCanvases"]["deleteItem"]["topTag"] == "IMG",
       J[6]["evidence"]["twoCanvases"]["deleteItem"]["topTag"])
    ck("产物：判据 6 明确指出根因在 batch 755",
       "755" in J[6]["why"] and "overflow" in J[6]["why"])
    ck("产物：判据 7 记下 6 张档的确认框按钮尺寸与 removed=1",
       J[7]["evidence"]["sixCanvases"]["confirmDialog"]["present"] is True
       and J[7]["evidence"]["sixCanvases"]["removedAfter"] == 1
       and len(J[7]["evidence"]["sixCanvases"]["recycleItems"]) == 1)
    ck("产物：判据 9 记下两种存续方式（客户端路由保留 / 整页加载丢失）",
       J[9]["evidence"]["sixAfterNav"]["removedCount"] == 1
       # census 的 store.removed 是**计数**不是列表（759a CENSUS 里是 .length）
       and J[9]["evidence"]["freshLoad"]["removed"] == 0)
    ck("产物：判据 9 显式收窄了 755 的说法",
       "收窄" in J[9]["why"] and "755" in J[9]["why"])
    # 有效的对照是「**点的那张** vs 「新标签页里的那张**」，
    # 不是「点之前」vs「新标签页」—— 后者恰好相等（都是 canvas-2），
    # 比较它会得出「没差异」的假结论。
    ck("产物：判据 10 的对照是「点的那张 vs 新标签页里的那张」且两者不同",
       J[10]["evidence"]["activeInThisTab"] !=
       J[10]["evidence"]["popupStore"]["active"]
       and J[10]["evidence"]["expectedId"] == "canvas-1"
       and J[10]["evidence"]["popupStore"]["active"] == "canvas-2",
       [J[10]["evidence"]["activeInThisTab"],
        J[10]["evidence"]["popupStore"]["active"]])
    ck("产物：判据 10 记下节点数差异（肉眼可辨不是同一张）",
       J[10]["evidence"]["popupNodes"] == 10
       and "10" in J[10]["why"])
    ck("产物：判据 11 记下 stale=true 且面板确实开了",
       J[11]["evidence"]["b4"]["staleAfterRecycle"] is True
       and J[11]["evidence"]["b4"]["recyclePanelOpen"] is True)
    ck("产物：判据 2 的 stub 名单为 9 个且不含 recycleBtn",
       len([k for k in J[2]["evidence"]["stubResults"]
            if not k.startswith("__") and k != "recycleBtn"
            and J[2]["evidence"]["stubResults"][k].get("statusAfter")]) == 9,
       sorted(k for k in J[2]["evidence"]["stubResults"]
              if not k.startswith("__")))
    ck("产物：判据 14 逐条列出四处诚实边界（入口单一/程序化造数/无源站对照）",
       all(k in J[14]["claim"] for k in ("只有", "程序化", "源站")),
       J[14]["claim"][:70])
    ck("产物：缺陷陈述含「新标签页不是你点的那张」与根因（内存/种子 store）",
       "不是你点的那张" in a["headline"]["defect"]
       and "无持久化" in a["headline"]["defect"]
       and "只活在内存里" in a["headline"]["rootCause"]
       and "种子 store" in a["headline"]["rootCause"])
    ck("产物：证据链 4 条且都带具体读数",
       len(a["headline"]["proofChain"]) == 4
       and all(len(x) > 10 for x in a["headline"]["proofChain"]))
    ck("产物：secondary 记了 5 条次要发现",
       len(a["headline"]["secondary"]) == 5,
       len(a["headline"]["secondary"]))
    ck("产物：返工 5 条 R29..R33 齐全且各自带 rule",
       [r["id"] for r in a["rework"]] == ["R29", "R30", "R31", "R32", "R33"]
       and all(r.get("rule") for r in a["rework"]),
       [r["id"] for r in a["rework"]])
    ck("产物：R33 记下「负向对照抓到验收器自己的洞」这件事",
       "deleteItem" in a["rework"][4]["detail"]
       and "51/51" in a["rework"][4]["detail"],
       a["rework"][4]["id"])
    ck("产物：R29 点明信号来源是「与已确认结论冲突」",
       "已确认结论冲突" in a["rework"][0]["rule"]
       or "与已确认结论冲突" in a["rework"][0]["detail"],
       a["rework"][0]["detail"][:60])
    ck("产物：不声称清单 ≥ 9 条",
       len(a["notClaimed"]) >= 9, len(a["notClaimed"]))
    ck("产物：不声称里写了「新建项目未单独验」与「没有与源站对照」",
       any("新建项目" in x for x in a["notClaimed"])
       and any("源站" in x for x in a["notClaimed"]))
    ck("产物：rawProbeFiles 两个探针都有说明",
       sorted(a["rawProbeFiles"]) == ["a", "b"])

    # ================= 原始读数交叉核对 =================
    if RAWA.exists() and RAWB.exists():
        ra = json.loads(RAWA.read_text(encoding="utf-8"))
        rb = json.loads(RAWB.read_text(encoding="utf-8"))["stripped"]
        r1 = ra["rounds"][0]
        TWO, SIX, B2, B3, B4 = (rb["B1_two"], rb["B1_six"], rb["B2"],
                                rb["B3"], rb["B4"])

        leaf = [
            ("j1.census", J[1]["evidence"]["census"],
             {k: r1["census"][k] for k in
              ("viewport", "topBanner", "sidebar", "newProject", "promo", "help",
               "back", "recycleBtn", "newFolder", "createCard",
               "createCardText", "h1", "moreMarker", "recycleAriaExpanded",
               "statusNode")}),
            ("j1.cardCount", J[1]["evidence"]["cardCount"],
             r1["census"]["cardCount"]),
            ("j2.stubResults", J[2]["evidence"]["stubResults"],
             r1["stubResults"]),
            ("j3.cardSpans", J[3]["evidence"]["cardSpans"],
             {x["id"]: x["spans"] for x in r1["census"]["cards"]}),
            ("j4.beforeAging", J[4]["evidence"]["beforeAging"],
             [x["text"] for x in B2["recycle"]["items"]]),
            ("j4.afterAging", J[4]["evidence"]["afterAging"],
             [x["text"] for x in B2["recycleAfterAging"]["items"]]),
            ("j4.panelHeader", J[4]["evidence"]["panelHeader"],
             B2["recycleAfterAging"]["paragraphs"][0]),
            ("j5.afterCheck", J[5]["evidence"]["afterCheck"], B2["afterCheck"]),
            ("j5.restoreSelectedHit", J[5]["evidence"]["restoreSelectedHit"],
             B2["restoreSelectedHit"]),
            ("j5.sixRecycle", J[5]["evidence"]["sixCanvasRecycle"],
             SIX["recycle"]),
            ("j6.items", J[6]["evidence"]["twoCanvases"]["items"],
             TWO["rowMenu"]["items"]),
            ("j6.removedAfter", J[6]["evidence"]["twoCanvases"]["removedAfter"],
             TWO["storeAfterDelete"]["removedCount"]),
            ("j7.items", J[7]["evidence"]["sixCanvases"]["items"],
             SIX["rowMenu"]["items"]),
            ("j7.confirmDialog", J[7]["evidence"]["sixCanvases"]["confirmDialog"],
             SIX["confirmDialog"]),
            ("j7.canvasesAfter",
             J[7]["evidence"]["sixCanvases"]["canvasesAfter"],
             [x["id"] for x in SIX["storeAfterDelete"]["canvases"]]),
            ("j8.confirmDialog", J[8]["evidence"]["confirmDialog"],
             SIX["confirmDialog"]),
            ("j9.sixAfterNav", J[9]["evidence"]["sixAfterNav"],
             SIX["storeOnProject"]),
            ("j9.freshLoad", J[9]["evidence"]["freshLoad"], r1["census"]["store"]),
            ("j10.popupStore", J[10]["evidence"]["popupStore"],
             B3["popupStore"]),
            ("j10.popupNodes", J[10]["evidence"]["popupNodes"],
             B3["popupNodes"]),
            ("j11.b4", J[11]["evidence"]["b4"], B4),
            # 判据 12 的 before/after 存的是**状态行文案**（字符串），
            # 不是整个面板对象
            ("j12.after", J[12]["evidence"]["after"],
             B2["afterCheck"]["selection"]),
            ("j12.before", J[12]["evidence"]["before"],
             B2["recycle"]["selection"]),
        ]
        bad = [n for n, x, y in leaf if _strip(x) != _strip(y)]
        ck("原始读数叶子级交叉核对 %d 项（a/b 两份）" % len(leaf), not bad, bad)

        ck("原始读数：759a 两轮 roundDiff 为空",
           ra["consistent"] is True and ra["roundDiff"] == {},
           sorted(ra["roundDiff"].keys()))
        ck("原始读数：9 个 stub 按钮全部 hitSelf=true",
           all(v.get("hit", {}).get("hitSelf") is True
               for k, v in r1["stubResults"].items()
               if not k.startswith("__")),
           [k for k, v in r1["stubResults"].items()
            if not k.startswith("__")
            and not v.get("hit", {}).get("hitSelf")])
        # 只比日期段：两张卡的节点数/名字本来就不同
        ck("原始读数：两张卡的日期段完全相同（span 其余部分本来就不同）",
           [x for x in r1["census"]["cards"][0]["spans"]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", x)] ==
           [x for x in r1["census"]["cards"][1]["spans"]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", x)],
           r1["census"]["cards"][0]["spans"])
        ck("原始读数：老化实验把 removedAt 改成 2025-01-15",
           all(x["removedAt"] == "2025-01-15"
               for x in B2["ageExperiment"]["set"]),
           B2["ageExperiment"])
        ck("原始读数：2 张档删除项落点命中 IMG、removed 仍为 0",
           TWO["deleteItem"]["topTag"] == "IMG"
           and TWO["storeAfterDelete"]["removedCount"] == 0)
        ck("原始读数：6 张档删除项落点命中 BUTTON、确认框出现、removed=1",
           SIX["deleteItem"]["topTag"] == "BUTTON"
           and SIX["confirmDialog"]["present"] is True
           and SIX["storeAfterDelete"]["removedCount"] == 1)
        ck("原始读数：6 张档回收站里出现了被删的那张",
           len(SIX["recycle"]["items"]) == 1
           and SIX["recycle"]["items"][0]["id"] == SIX["targetRow"],
           SIX["recycle"]["items"])
        ck("原始读数：客户端路由后 removed 仍在（1），整页加载后为 0",
           SIX["storeOnProject"]["removedCount"] == 1
           and r1["census"]["store"]["removed"] == 0)
        ck("原始读数：新标签页 active 与被点的卡不同、节点数也不同",
           B3["expectedId"] == "canvas-1"
           and B3["activeInThisTab"] == "canvas-1"
           and B3["popupStore"]["active"] == "canvas-2"
           and B3["popupShowsTarget"] is False and B3["popupNodes"] == 10,
           [B3["expectedId"], B3["activeInThisTab"],
            B3["popupStore"]["active"], B3["popupShowsTarget"]])
        ck("原始读数：点回收站后 status 仍是上一条 stub 文案",
           B4["statusAfterStub"] == B4["statusAfterRecycle"]
           == "本地原型：新建文件夹未接入"
           and B4["recyclePanelOpen"] is True)
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb759{a,b}.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 759, "checks": checks, "passed": npass,
              "total": len(checks), "static": st}
    (OUTDIR / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("判据 %d/%d" % (npass, len(checks)))
    for c in checks:
        print(("  ✅ " if c["pass"] else "  ❌ ") + c["label"][:112])
        if not c["pass"] and c["got"] not in (None, "SKIPPED — 不算通过"):
            print("       got=" + json.dumps(c["got"], ensure_ascii=False)[:240])
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
