"""batch 758 验收器：节点类型的 DOM 契约普查（含一处高严重度缺陷）

三层结构（与 753–757 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （dblclick 监听器的挂载点与阶段、13 个组件的 handle / aria / data 钩子 /
      aria-label / 框外标题、ShotBreakdownResultNode 的单 handle、AudioNode 的
      filename 兜底、种子的原始 filename…）
  2. **产物层** —— 判据条数、普查表完整性、证据链、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb758{a,b,c}.json` 还在，把产物里的关键
     读数与探针原始输出逐个对账。缺失时**判失败而不是通过**。

⚠ 静态普查的边界（判据 14）：本层只统计**组件文件自身**的 role=，
  运行时在 `video` 子树里却测到 1 个 role ⟹ 角色可由子组件贡献。
  所以「role 全为 0」这句话的适用范围必须限定在「组件文件自身」。

判据 **14 条**（普查型单轮，两处可变状态在轮内做了阳性/阴性对照）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch758-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAWA = pathlib.Path("/tmp/vb758a.json")
RAWB = pathlib.Path("/tmp/vb758b.json")
RAWC = pathlib.Path("/tmp/vb758c.json")
RAWD = pathlib.Path("/tmp/vb758d.json")
GEN = re.compile(r"-\d{10,}-[a-z0-9]{6}\b")
NODEDIR = ROOT / "src/components/nodes"
SKIP = {"DeletableEdge.tsx", "AttemptChipIcons.tsx", "ToolbarPillIcons.tsx"}
PANEL_TYPES = ["text", "image", "video", "video-clip", "script-execution",
               "shot-breakdown", "audio"]


def _strip(o):
    if isinstance(o, str):
        return GEN.sub("-<gen>", o)
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def _block(text, key):
    """取 `key:` 的**实现体**（`=> {` 那一处），跳过接口里的类型声明。"""
    start = 0
    while True:
        i = text.find(key, start)
        if i < 0:
            return None
        if re.search(r"=>\s*\{", text[i:i + 160]):
            j = text.find("\n  },", i)
            return text[i:j] if j > 0 else text[i:i + 1600]
        start = i + len(key)


def static_side():
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    audio = (ROOT / "src/components/nodes/AudioNode.tsx").read_text(
        encoding="utf-8")
    result_n = (ROOT / "src/components/nodes/ShotBreakdownResultNode.tsx"
                ).read_text(encoding="utf-8")
    sb = (ROOT / "src/components/nodes/ShotBreakdownNode.tsx").read_text(
        encoding="utf-8")
    add = (ROOT / "src/components/AddNodePanel.tsx").read_text(encoding="utf-8")

    comp = {}
    for p in sorted(NODEDIR.glob("*.tsx")):
        if p.name in SKIP:
            continue
        t = p.read_text(encoding="utf-8")
        body = t[t.find("function "):] if "function " in t else t
        comp[p.stem] = {
            "handleCount": body.count("<Handle"),
            "handleTypes": re.findall(r'<Handle\s+type="(\w+)"', t),
            "dataHooks": sorted(set(re.findall(r"\bdata-[a-z0-9-]+", t))),
            "ariaKeys": sorted(set(re.findall(r"\baria-[a-z0-9]+", t))),
            "ariaLabel": "aria-label" in t,
            "roleAttr": len(re.findall(r"\brole=", t)),
            "outsideTitle": bool(re.search(r"absolute\s+-top-", body)),
        }

    return {
        # ---- 判据 1：面板入口 ----
        "panelEntries": re.findall(r'\{\s*type:\s*"([a-z-]+)",\s*label:',
                                   add),
        "panelDataHook": 'data-add-node-entry={entry.type}' in add
        or "data-add-node-entry=" in add,
        "submenuHook": 'data-add-node-submenu="script"' in add,
        "scriptNewHook": 'data-add-node-entry="script-new"' in add,
        # ---- 判据 2/3：双击入口 ----
        "dblclickHandlerExists": "handleDoubleClick" in page
        and 'addEventListener("dblclick", handleDoubleClick)' in page,
        "dblclickAttachedToRef": bool(re.search(
            r"container\.addEventListener\(\"dblclick\", handleDoubleClick\)",
            page)),
        "dblclickGuardIsPane": 'closest(".react-flow__pane")' in page,
        "dblclickGuardOnlyOpens": bool(re.search(
            r"if \(!state\.isAddNodePanelOpen\) state\.toggleAddNodePanel\(\)", page)),
        "onPaneDoubleClickPropAbsent": "onPaneDoubleClick" not in page,
        "dblclickStopPropagationElsewhere": "stopPropagation" in page,
        # ---- 判据 7：唯一单 handle ----
        "resultNodeOneHandle": result_n.count("<Handle") == 1,
        "resultNodeHandleIsTargetOnly": bool(re.search(
            r'<Handle\s+type="target"', result_n))
        and 'type="source"' not in result_n,
        "shotBreakdownTwoHandles": sb.count("<Handle") == 2,
        # ---- 判据 9：filename 当标题 ----
        "audioFilenameFallback": 'data.filename ?? "新音频"' in audio,
        "seedRawFilenames": re.findall(r'filename: "(image_[^"]+)"', store),
        # ---- 判据 6/13：普查表可被独立重算 ----
        "components": comp,
        "componentCount": len(comp),
        "oneHandleComponents": sorted(k for k, v in comp.items()
                                      if v["handleCount"] == 1),
        "zeroAriaComponents": sorted(k for k, v in comp.items()
                                     if not v["ariaKeys"]),
        "zeroDataComponents": sorted(k for k, v in comp.items()
                                     if not v["dataHooks"]),
        "noAriaLabelComponents": sorted(k for k, v in comp.items()
                                        if not v["ariaLabel"]),
        "noOutsideTitleComponents": sorted(k for k, v in comp.items()
                                           if not v["outsideTitle"]),
        "outsideTitleSpellings": {
            "dashTop8": sorted(p.stem for p in NODEDIR.glob("*.tsx")
                               if p.name not in SKIP
                               and re.search(r"absolute\s+-top-",
                                             p.read_text(encoding="utf-8"))),
            "arbitraryTop": sorted(p.stem for p in NODEDIR.glob("*.tsx")
                                   if p.name not in SKIP
                                   and "top-[-" in p.read_text(encoding="utf-8")),
        },
        "dataHookCounts": {k: len(v["dataHooks"]) for k, v in comp.items()},
        "allRoleAttrZero": all(v["roleAttr"] == 0 for v in comp.values()),
        "registeredTypesInPage": re.findall(r'^\s*(?:"([a-z0-9-]+)"|(\w+)): '
                                            r'\w+Node,?$',
                                            page, re.M),
    }


def main():
    page_txt = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    J = {j["no"]: j for j in a["judgments"]}
    comp = st["components"]

    # ================= 静态层 =================
    ck("静态：面板 9 个条目 + data-add-node-entry / 子菜单钩子都在",
       len(st["panelEntries"]) == 9 and st["panelDataHook"]
       and st["submenuHook"] and st["scriptNewHook"],
       st["panelEntries"])
    ck("静态：dblclick 监听器确实挂在 flowContainerRef 上（冒泡阶段）",
       st["dblclickHandlerExists"] and st["dblclickAttachedToRef"],
       st["dblclickAttachedToRef"])
    ck("静态：dblclick 有 .react-flow__pane 守卫，且**只开不关**（if !isAddNodePanelOpen）",
       st["dblclickGuardIsPane"] and st["dblclickGuardOnlyOpens"])
    ck("静态：page.tsx 里没有 onPaneDoubleClick prop（替代入口不存在）",
       st["onPaneDoubleClickPropAbsent"])
    ck("静态：ShotBreakdownResultNode 恰好 1 个 Handle 且只有 target",
       st["resultNodeOneHandle"] and st["resultNodeHandleIsTargetOnly"],
       [st["resultNodeOneHandle"], st["resultNodeHandleIsTargetOnly"]])
    ck("静态：ShotBreakdownNode 有 2 个 Handle（对照组）",
       st["shotBreakdownTwoHandles"])
    ck("静态：13 个组件里单 handle 的只有 ShotBreakdownResultNode",
       st["oneHandleComponents"] == ["ShotBreakdownResultNode"],
       st["oneHandleComponents"])
    ck("静态：AudioNode 的标题就是 filename 本身（?? 兜底「新音频」）",
       st["audioFilenameFallback"])
    ck("静态：种子里确有 image_ 开头的原始流水线 filename",
       len(st["seedRawFilenames"]) >= 2, st["seedRawFilenames"])

    # ================= 产物层 =================
    ck("产物：判据 14 条且编号连续 1..14",
       len(a["judgments"]) == 14 and a["judgeCount"] == 14
       and sorted(J) == list(range(1, 15)), sorted(J))
    ck("产物：普查表覆盖 13 个组件",
       a["seed"]["registeredNodeTypes"] == 13 == st["componentCount"],
       [a["seed"]["registeredNodeTypes"], st["componentCount"]])
    ck("产物：产物层与独立重算的单 handle 名单一致",
       J[7]["evidence"]["oneHandle"][0]["component"]
       == st["oneHandleComponents"][0])
    ck("产物：aria 为空的组件名单与独立重算一致",
       sorted(J[11]["claim"].split("：")[1].split("；")[0].split("、"))
       == st["zeroAriaComponents"]
       or all(x in J[11]["claim"] for x in st["zeroAriaComponents"]),
       st["zeroAriaComponents"])
    ck("产物：无 aria-label 的组件名单与独立重算一致",
       all(x in J[12]["claim"] for x in st["noAriaLabelComponents"]),
       st["noAriaLabelComponents"])
    ck("产物：data 钩子计数与独立重算一致（最多/最少的具体值）",
       J[13]["evidence"]["dataHookCounts"] == st["dataHookCounts"],
       [J[13]["evidence"]["dataHookCounts"].get("VideoNode"),
        st["dataHookCounts"].get("VideoNode")])
    ck("产物：data 钩子为 0 的组件名单与独立重算一致",
       J[13]["evidence"]["zeroData"] == st["zeroDataComponents"],
       st["zeroDataComponents"])
    ck("静态：框外标题有两种写法（-top-8 与 top-[-Npx]），只匹配一种会误判",
       len(st["outsideTitleSpellings"]["dashTop8"]) >= 1
       and len(st["outsideTitleSpellings"]["arbitraryTop"]) >= 2,
       st["outsideTitleSpellings"])
    ck("产物：更正后「框外无标题的类型」为空集（758c 的旧结论已作废）",
       J[8]["evidence"]["noOutsideTypes"] == [],
       J[8]["evidence"]["noOutsideTypes"])
    ck("产物：判据 6 的 handleCount 运行时表覆盖 7 种类型且全为 2",
       sorted(J[6]["evidence"]) == sorted(PANEL_TYPES)
       and set(J[6]["evidence"].values()) == {2},
       J[6]["evidence"])
    ck("产物：判据 2 记下 pointIsPane=true / 原生 dblclick=+1 / 条目=0",
       J[2]["evidence"]["pointIsPane"] is True
       and J[2]["evidence"]["afterOne"]["nativeDblclick"] == 1
       and J[2]["evidence"]["afterOne"]["panelEntries"] == 0)
    ck("产物：判据 2 的 why 明写阳性对照（左栏按钮双击 +1 且开出 9 条目）",
       "阳性对照" in J[2]["why"] and "9 个条目" in J[2]["why"]
       and "不是探针不行" in J[2]["why"], J[2]["why"][:70])
    ck("产物：判据 3 四处计数器 = 容器捕获 1 / pane 冒泡 1 / 容器冒泡 0 / window 冒泡 0",
       J[3]["evidence"]["countersAfterDblclick"]
       == {"window": 0, "pane": 1, "container": 0, "stopped": 1},
       J[3]["evidence"]["countersAfterDblclick"])
    ck("产物：判据 3 的 why 解释了事件路径（捕获→pane冒泡→断）",
       "stopPropagation" in J[3]["why"] or "掐断" in J[3]["why"])
    ck("产物：判据 4 记下 8 种类型各 +1 且 failures=0（7 种直建 + script 走子菜单）",
       len(J[4]["evidence"]["created"]) == len(PANEL_TYPES) + 1
       and set(J[4]["evidence"]["created"].values()) == {1}
       and J[4]["evidence"]["failures"] == [],
       sorted(J[4]["evidence"]["created"]))
    ck("产物：判据 4 记下 script 走子菜单 script-new",
       "script-new" in json.dumps(J[4]["evidence"], ensure_ascii=False)
       or "scriptNew" in json.dumps(J[4]["evidence"], ensure_ascii=False)
       or "script" in J[4]["why"])
    ck("产物：判据 5 同时记下两个探针各自的 zoom（1.501 / 0.751）",
       "1.501" in J[5]["claim"] and "0.751" in J[5]["claim"]
       and "当轮现取 zoom" in J[5]["why"], J[5]["claim"][:80])
    ck("产物：判据 8 标为「更正」并给出作废的旧结论",
       "更正" in J[8]["title"] and "已作废" in J[8]["evidence"]["corrects"],
       J[8]["title"][:60])
    ck("产物：判据 8 记下 7 种类型 hasOutsideTitle 全为 true",
       all(v["hasOutsideTitle"] for v in J[8]["evidence"]["elementLevel"].values())
       and len(J[8]["evidence"]["elementLevel"]) == 7)
    ck("产物：判据 8 点明根因是「图标 + 裸文本」被叶子扫描跳过",
       "children.length" in J[8]["evidence"]["root_cause"]
       and "裸文本" in J[8]["evidence"]["root_cause"])
    ck("产物：判据 8 记下 7 种类型标题全是裸文本结构",
       len(J[8]["evidence"]["allHaveBareTextTitle"]) == 7,
       J[8]["evidence"]["allHaveBareTextTitle"])
    ck("产物：判据 9 给出种子原始 filename 与新建节点的对照（两侧都在 evidence）",
       "image_2026-06-15" in json.dumps(J[9]["evidence"], ensure_ascii=False)
       and "新图片" in json.dumps(J[9]["evidence"]["createdInstanceTitles"],
                                  ensure_ascii=False))
    ck("产物：判据 14 明确 role 静态全 0 的**适用范围**是组件文件自身",
       J[14]["evidence"]["roleStaticAllZero"] is True
       and "子组件" in J[14]["claim"], J[14]["claim"][:70])
    ck("产物：判据 14 点明 758b 的 missing 是「种子里没有」不是「没标题」",
       "missing" in J[14]["claim"] or "missing" in J[14]["evidence"])
    ck("产物：twoRound 声明了这是普查型单轮并记了 zeroFailures",
       "普查型" in a["twoRound"]["note"] and a["twoRound"]["zeroFailures"] is True)
    ck("产物：缺陷陈述含「从未触发」与 stopPropagation 两个要素",
       "从未触发" in a["headline"]["defect"]
       and "stopPropagation" in a["headline"]["defect"])
    ck("产物：rootCause 指明事件路径与三个修复方向",
       "容器捕获" in a["headline"]["rootCause"]
       and a["headline"]["rootCause"].count("onPaneDoubleClick") == 1)
    ck("产物：证据链 5 条，每条都带具体读数",
       len(a["headline"]["proofChain"]) == 5
       and all(len(x) > 12 for x in a["headline"]["proofChain"]))
    ck("产物：secondary 记了 4 条次要发现",
       len(a["headline"]["secondary"]) == 4,
       len(a["headline"]["secondary"]))
    ck("产物：返工 5 条 R24..R28 齐全且各自带 rule",
       [r["id"] for r in a["rework"]] == ["R24", "R25", "R26", "R27", "R28"]
       and all(r.get("rule") for r in a["rework"]),
       [r["id"] for r in a["rework"]])
    # ⚠ 必须长度守卫：负向对照第八发（删掉 R28）曾让这里 IndexError **崩掉**。
    # 崩掉的检查器比失败的更危险 —— CI 里可能被当成「不适用」而放过，
    # 而且报的是 traceback 而不是「哪条不通过」。
    rw = {r["id"]: r for r in a["rework"]}
    ck("产物：R28 写明这是 R26 的同类错误重演且发生在同一批次",
       "R28" in rw and "R26" in rw["R28"].get("rule", "")
       and "同一个批次" in rw["R28"].get("rule", ""),
       sorted(rw))
    ck("产物：不声称清单 ≥ 9 条",
       len(a["notClaimed"]) >= 9, len(a["notClaimed"]))
    ck("产物：不声称里明确写了「单 handle 结论未做运行时验证」与「没有与源站对照」",
       any("未在运行时验证" in x for x in a["notClaimed"])
       and any("源站" in x for x in a["notClaimed"]))
    ck("产物：rawProbeFiles 三个探针都有说明",
       sorted(a["rawProbeFiles"]) == ["a", "b", "c"])

    # ================= 原始读数交叉核对 =================
    if RAWA.exists() and RAWB.exists() and RAWC.exists() and RAWD.exists():
        ra = json.loads(RAWA.read_text(encoding="utf-8"))
        rb = json.loads(RAWB.read_text(encoding="utf-8"))
        rc = json.loads(RAWC.read_text(encoding="utf-8"))
        mech = rc["mechanism"]
        dbl = rb["dblclick"]
        cs = rc["stripped"]
        ds = json.loads(RAWD.read_text(encoding="utf-8"))["stripped"]
        ds = json.loads(RAWD.read_text(encoding="utf-8"))["stripped"]
        Dt = ds["titles"]

        leaf = [
            ("j1.entries", J[1]["evidence"]["entries"],
             ra["panelSeen"]["entries"]),
            ("j1.sidebarHit", J[1]["evidence"]["sidebarHit"],
             {k: v for k, v in ra["sidebarHit"].items()}),
            ("j2.afterOne", J[2]["evidence"]["afterOne"], dbl["afterOne"]),
            ("j2.afterTwo", J[2]["evidence"]["afterTwo"], dbl["afterTwo"]),
            ("j3.counters", J[3]["evidence"]["countersAfterDblclick"],
             mech["countersAfterDblclick"]),
            ("j3.panelEntries", J[3]["evidence"]["panelEntries"],
             mech["panelEntries"]),
            ("j4.created", J[4]["evidence"]["created"],
             {t: ra["results"][t]["created"] for t in ra["results"]}),
            ("j4.nodesBA", J[4]["evidence"]["nodesBeforeAfter"],
             {t: [ra["results"][t]["nodesBefore"], ra["results"][t]["nodesAfter"]]
              for t in ra["results"]}),
            ("j6.handles", J[6]["evidence"],
             {t: cs["titles"][t]["handleCount"] for t in PANEL_TYPES
              if t in cs["titles"] and "handleCount" in cs["titles"][t]}),
            # j8 已被 758d 更正 ⟹ 这里对账**更正后**的读数；
            # 758c 的旧值单独留一条检查作反证（见下）
            ("j8.elementLevel", J[8]["evidence"]["elementLevel"],
             {t: {"hasOutsideTitle": ds["titles"][t]["hasOutsideTitle"],
                  "outsideTexts": ds["titles"][t]["outsideTexts"],
                  "candidateCount": ds["titles"][t]["candidateCount"],
                  "hasBareTextNode": ds["titles"][t].get("hasBareTextNode")}
              for t in PANEL_TYPES}),
            ("j8.allHaveBareTextTitle", J[8]["evidence"]["allHaveBareTextTitle"],
             sorted(t for t in PANEL_TYPES
                    if ds["titles"][t].get("hasBareTextNode"))),
            ("j8.noOutsideTypes", J[8]["evidence"]["noOutsideTypes"],
             [t for t in PANEL_TYPES
              if ds["titles"][t].get("hasOutsideTitle") is False]),
            ("j9.bSeedTypes", J[9]["evidence"]["bSeedTypes"],
             {k: [x["text"] for x in rb["titles"][k]["leaves"]
                  if x["relY"] == "above"]
              for k in rb["titles"] if "leaves" in rb["titles"][k]}),
            ("j11.runtimeAria", J[11]["evidence"]["runtimeAria"],
             {t: cs["titles"][t]["ariaAttrKeys"] for t in PANEL_TYPES}),
            ("j14.roleRuntime", J[14]["evidence"]["roleRuntime"],
             {t: cs["titles"][t]["roleKeys"] for t in PANEL_TYPES}),
        ]
        bad = [n for n, x, y in leaf if _strip(x) != _strip(y)]
        ck("原始读数叶子级交叉核对 %d 项（a/b/c 三份）" % len(leaf), not bad, bad)

        ck("原始读数：双击后窗口捕获 +1、mousedown +2、但条目 0",
           dbl["afterOne"]["nativeDblclick"] == 1
           and dbl["afterOne"]["nativeMousedown"] == 2
           and dbl["afterOne"]["panelEntries"] == 0)
        ck("原始读数：阳性对照 —— 左栏按钮双击 +%d 且开出 %d 条目"
           % (dbl["sidebarDblclickDelta"], dbl["sidebarEntriesAfter"]),
           dbl["sidebarDblclickDelta"] == 1
           and dbl["sidebarEntriesAfter"] == 9)
        ck("原始读数：双击点确实在 .react-flow__pane 上",
           dbl["pointIsPane"] is True)
        ck("原始读数：容器冒泡=0 而容器捕获=1（传播在 pane 处断）",
           mech["countersAfterDblclick"]["container"] == 0
           and mech["countersAfterDblclick"]["stopped"] == 1
           and mech["countersAfterDblclick"]["pane"] == 1)
        ck("原始读数：8 种类型各 +1，failures 为空",
           all(ra["results"][t]["created"] == 1 for t in ra["results"])
           and ra["failures"] == [])
        ck("原始读数：运行时 7 种类型 handleCount 全为 2",
           all(cs["titles"][t]["handleCount"] == 2 for t in PANEL_TYPES),
           {t: cs["titles"][t]["handleCount"] for t in PANEL_TYPES})
        ck("原始读数（758d 元素级）：7 种类型 hasOutsideTitle 全为 true，"
           "video-clip 的框外标题是「智能剪辑 1」",
           all(Dt[t]["hasOutsideTitle"] for t in PANEL_TYPES)
           and Dt["video-clip"]["outsideTexts"][0] == "智能剪辑 1",
           {t: Dt[t]["outsideTexts"][:1] for t in PANEL_TYPES})
        ck("原始读数（758d）：7 种类型标题全是「图标 + 裸文本」结构",
           all(Dt[t]["hasBareTextNode"] for t in PANEL_TYPES))
        ck("原始读数：758c 的 video-clip aboveTexts 确为空（与 758d 构成对照）",
           cs["titles"]["video-clip"]["aboveTexts"] == [],
           cs["titles"]["video-clip"]["aboveTexts"])
        ck("原始读数：758b 的 missing 名单正好是种子里没有的 4 种",
           sorted(k for k, v in rb["titles"].items() if v.get("missing"))
           == ["audio", "shot-breakdown", "text", "video-clip"],
           sorted(k for k, v in rb["titles"].items() if v.get("missing")))
        # 运行时量到的 7 种类型必须都在 page.tsx 的 type→组件注册表里，
        # 否则「DOM 读数」可能量到了未注册/被覆盖的组件上
        page_types = set()
        for t in re.findall(r'"([a-z0-9-]+)":\s*\w+Node', page_txt):
            page_types.add(t)
        for t in re.findall(r"^\s*([a-z][a-z0-9-]*):\s*\w+Node,", page_txt,
                             re.M):
            page_types.add(t)
        ck("原始读数：运行时量到的 7 种类型都在 page.tsx 注册表里",
           all(t in page_types for t in PANEL_TYPES),
           sorted(t for t in PANEL_TYPES if t not in page_types))
        ck("静态：page.tsx 注册的类型总数 >= 13（普查表不漏）",
           len(page_types) >= 13, len(page_types))
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb758{a,b,c,d}.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 758, "checks": checks, "passed": npass,
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
