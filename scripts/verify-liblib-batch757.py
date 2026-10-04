"""batch 757 验收器：storyboard-group 的视觉契约（含一处高严重度缺陷）

三层结构（与 753–756 同）：
  1. **静态层** —— 直接从 `src/` 复核判据依赖的实现事实
     （组件从不读 children、groupKind 零读取点、无 useUpdateNodeInternals、
      标题 -top-8 与 pointer-events-none、selected 分支只改 border、
      两处 style.zIndex=-1001、panOnDrag 的两个分支…）
  2. **产物层** —— 判据条数、三探针两轮一致性、证据链完整性、
     对比度算式、返工条目、不声称清单
  3. **原始读数交叉核对** —— 若 `/tmp/vb757{a,b,c}.json` 还在，把产物里的
     关键读数与探针原始输出逐个对账。缺失时**判失败而不是通过**。

⚠ 本批两个必须固化的坑：
  · 画布带 zoom（fitView 后 0.375）⟹ getBoundingClientRect() 读到的是**变换后**
    尺寸，必须先换算再与 store 宽高比对，否则 430×452 会被读成 161×170。
  · `getBoundingClientRect` 之外，**DOM 的 computed color 可能是 oklab(...)**
    （Tailwind v4 把 `white/10` 编译成 oklab）⟹ 对比度解析失败时要返回 None
    而不是猜。

判据 **18 条**（17 条两轮一致 + 1 条护栏记录）。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch757-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
RAWA = pathlib.Path("/tmp/vb757a.json")
RAWB = pathlib.Path("/tmp/vb757b.json")
RAWC = pathlib.Path("/tmp/vb757c.json")
GEN = re.compile(r"^(group|storyboard-group|image|video|script|text|node|canvas)"
                 r"-\d{10,}-[a-z0-9]{6}$")
G_EMPTY, G_WITH = "g-245IDFh8sB", "g-EFbbHpwq5w"


def _strip(o):
    if isinstance(o, str):
        return "<generated-id>" if GEN.match(o) else o
    if isinstance(o, dict):
        return {_strip(k): _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def _lum(rgb):
    """与汇编器同款：只认 rgb() 与 #rrggbb，oklab(...) 返回 None（不猜）。"""
    if isinstance(rgb, str) and rgb.startswith("#") and len(rgb) == 7:
        rgb = "rgb(%d, %d, %d)" % tuple(int(rgb[i:i + 2], 16) for i in (1, 3, 5))
    if not isinstance(rgb, str) or not rgb.startswith("rgb("):
        return None
    parts = rgb[4:rgb.index(")")].split(",")
    out = []
    for p in parts[:3]:
        v = float(p.strip()) / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(fg, bg):
    l1, l2 = _lum(fg), _lum(bg)
    if l1 is None or l2 is None:
        return None
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def static_side():
    comp = (ROOT / "src/components/nodes/StoryboardGroupNode.tsx").read_text(
        encoding="utf-8")
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")

    # groupKind 的所有出现位置（判据 4 要求「只 1 次且只写不读」）
    # ⚠ 同时记下**行内容**：只记「路径:行号」无法区分「写入」与「读取」
    hits = []
    lines = []
    for p in sorted(list((ROOT / "src").rglob("*.ts"))
                    + list((ROOT / "src").rglob("*.tsx"))):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "groupKind" in line:
                hits.append(f"{p.relative_to(ROOT)}:{i}")
                lines.append(line.strip())

    body = comp[comp.find("function StoryboardGroupNodeComponent("):]
    title_line = next((ln for ln in body.splitlines()
                       if "pointer-events-none" in ln), "")
    sel_line = next((ln for ln in body.splitlines() if "selected &&" in ln), "")

    return {
        "componentReadsNoChildren": "children" not in body,
        "componentReadsNoGroupKind": "groupKind" not in body,
        "groupKindHits": hits,
        "groupKindLines": lines,
        "groupKindOnlyOneWriteNoRead": (len(hits) == 1
                                        and 'groupKind: "selection"' in lines[0]
                                        and "get(" not in lines[0]
                                        and "." + "groupKind" not in lines[0]),
        "noUpdateNodeInternals": "useUpdateNodeInternals" not in page
        and "useUpdateNodeInternals" not in store,
        "noGroupBoundsRecompute": not re.search(
            r"storyboard-group[\s\S]{0,400}?(width\s*=|setNodes|getAbsoluteNodePosition)",
            page),
        "titleTopMinus8": "-top-8" in title_line,
        "titlePointerEventsNone": "pointer-events-none" in title_line,
        "titleGrey777": "text-[#777]" in title_line,
        "titleHasNoSelectedBranch": "selected" not in title_line,
        "selectedBranchOnlyBorderAndShadow":
            "border-[#09caf5]" in sel_line and "shadow-" in sel_line,
        "variantDrivesLook": ('isVideo ? "rounded-[4px] border-white/10 bg-[#212121]"'
                              in body
                              and 'rounded-[20px] border-white/10 bg-white/10' in body),
        "isVideoFromVariant": 'const isVideo = data.variant === "video";' in body,
        "overflowVisible": "overflow-visible" in body,
        "twoHandlesUnconditional": body.count("<Handle") == 2,
        "groupRegisteredInPage": '"storyboard-group": StoryboardGroupNode,' in page,
        # 层叠：种子写在 style.zIndex，groupSelectedNodes 顶层与 style 都写
        "seedStyleZIndex": store.count("style: { width: 430, height: 452, "
                                        "zIndex: -1001 }") >= 1
        and store.count("style: { width: 722, height: 460, "
                        "zIndex: -1001 }") >= 1,
        "groupSelectedNodesSetsZIndex": bool(re.search(
            r"groupNode: Node = \{[\s\S]{0,900}?zIndex: -1001,", store)),
        # 平移三路
        "effectivePanExpr": ("const effectivePan = canvasTool === \"pan\" "
                             "|| isSpacePressed;") in page,
        "panOnDragBothBranches":
            'panOnDrag={effectivePan ? [0, 1] : [1]}' in page,
        "nodesDraggableGuarded": 'nodesDraggable={canvasTool === "select" && '
        '!effectivePan}' in page,
        "cursorGrabWhenEffectivePan": 'effectivePan ? "cursor-grab' in page,
    }


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    checks = []

    def ck(label, ok, got=None):
        checks.append({"label": label, "pass": bool(ok), "got": got})

    J = {j["no"]: j for j in a["judgments"]}
    B = a["boundary"]

    # ================= 静态层 =================
    ck("静态：StoryboardGroupNode 组件体里没有 children（判据 3 的根因）",
       st["componentReadsNoChildren"], st["componentReadsNoChildren"])
    ck("静态：groupKind 在 src/ 里只出现 1 次，且是 selection 写入",
       st["groupKindOnlyOneWriteNoRead"], st["groupKindHits"])
    ck("静态：全仓库无 useUpdateNodeInternals（没有跟随机制）",
       st["noUpdateNodeInternals"], st["groupKindHits"])
    ck("静态：page.tsx 里没有分组边界重算逻辑",
       st["noGroupBoundsRecompute"])
    ck("静态：标题 -top-8 + pointer-events-none + text-[#777]，且该行无 selected 条件",
       st["titleTopMinus8"] and st["titlePointerEventsNone"]
       and st["titleGrey777"] and st["titleHasNoSelectedBranch"],
       st["titleHasNoSelectedBranch"])
    ck("静态：selected 分支只加 border-[#09caf5] 与 shadow",
       st["selectedBranchOnlyBorderAndShadow"])
    ck("静态：variant 驱动两套外观（20px/white10 与 4px/#212121）",
       st["variantDrivesLook"] and st["isVideoFromVariant"])
    ck("静态：容器 overflow-visible（标题才能画到框外）",
       st["overflowVisible"])
    ck("静态：两个 Handle 无条件渲染（空组也有连线端点）",
       st["twoHandlesUnconditional"], st["twoHandlesUnconditional"])
    ck("静态：分组在 page.tsx 的 type→组件映射里注册",
       st["groupRegisteredInPage"])
    ck("静态：层叠 -1001 两处来源都写了（种子 style / groupSelectedNodes 顶层+style）",
       st["seedStyleZIndex"] and st["groupSelectedNodesSetsZIndex"])
    ck("静态：effectivePan = canvasTool==='pan' || isSpacePressed",
       st["effectivePanExpr"])
    ck("静态：panOnDrag 两分支 [0,1] / [1]；nodesDraggable 受 !effectivePan 约束；"
       "effectivePan 时光标 cursor-grab",
       st["panOnDragBothBranches"] and st["nodesDraggableGuarded"]
       and st["cursorGrabWhenEffectivePan"])

    # ================= 产物层 =================
    ck("产物：判据 18 条（17 judgments + 1 boundary）",
       len(a["judgments"]) == 17 and B["no"] == 18 and a["judgeCount"] == 17,
       len(a["judgments"]))
    ck("产物：判据编号连续 1..18",
       sorted(list(J) + [B["no"]]) == list(range(1, 19)),
       sorted(list(J) + [B["no"]]))
    ck("产物：三个探针各自两轮一致，roundDiff 全空",
       a["twoRound"]["consistent"] == {"a": True, "b": True, "c": True}
       and a["twoRound"]["diffCounts"] == {"a": 0, "b": 0, "c": 0},
       a["twoRound"])
    ck("产物：两轮独立性交代了整页 reload + fitView",
       "reload" in a["twoRound"]["independence"]
       and "fitView" in a["twoRound"]["independence"])
    ck("产物：zoom 换算被显式交代（0.375 陷阱）",
       a["seed"]["zoom"] == 0.375 and "换算" in a["seed"]["zoomNote"],
       a["seed"]["zoom"])

    d13 = J[13]["evidence"]["derived"]
    ck("产物：判据 13 的派生四格 = (框不移动, 框不缩放, store不动, 子节点动了)",
       d13 == {"groupDomMoved": False, "groupDomResized": False,
               "groupStoreMoved": False, "childMoved": True}, d13)
    ck("产物：判据 13 的派生四格与 before/after 读数自洽（现算复核）",
       d13["groupDomMoved"] == (J[13]["evidence"]["after"]["groupDom"]["x"]
                                != J[13]["evidence"]["before"]["groupDom"]["x"]
                                or J[13]["evidence"]["after"]["groupDom"]["y"]
                                != J[13]["evidence"]["before"]["groupDom"]["y"])
       and d13["childMoved"] == (J[13]["evidence"]["after"]["childRel"]
                                 != J[13]["evidence"]["before"]["childRel"]))
    ck("产物：判据 13 结论文本与派生四格一致（防止只改文案）",
       # claim 里是 Python bool 的字符串形式（False/True），不是 markdown 的
       # **false** —— 断言要跟**实际排版**对齐，否则会把正确产物判成不一致
       ("groupDomMoved=%s" % d13["groupDomMoved"]) in J[13]["claim"]
       and ("groupDomResized=%s" % d13["groupDomResized"]) in J[13]["claim"]
       and ("groupStoreMoved=%s" % d13["groupStoreMoved"]) in J[13]["claim"]
       and ("childMoved=%s" % d13["childMoved"]) in J[13]["claim"],
       J[13]["claim"][:100])
    ck("产物：判据 13 附了静态依据（无 useUpdateNodeInternals / groupKind 无人读）",
       "useUpdateNodeInternals" in J[13]["evidence"]["static"]
       and "groupKind" in J[13]["evidence"]["static"])
    ck("产物：判据 14 记下 childrenStillLinked 与框外间距",
       J[14]["evidence"]["childrenNow"] == ["v-UGQZzZOpbv"]
       and J[14]["evidence"]["childFullyInsideGroup"] is False
       and J[14]["evidence"]["gapRight"] > 0,
       J[14]["evidence"]["gapRight"])
    ck("产物：判据 3 空组 children=[] 仍渲染完整框 + 标题",
       J[3]["evidence"]["emptyGroup"]["children"] == []
       and J[3]["evidence"]["emptyGroup"]["untransformed"]["w"] == 430
       and bool(J[3]["evidence"]["emptyGroup"]["title"]))
    ck("产物：判据 4 记下 groupKind 的 grep 位置只有 1 条",
       J[4]["evidence"]["grepCount"] == 1
       and len(J[4]["evidence"]["grepLocations"]) == 1)
    ck("产物：判据 5 记下顶层 zIndex 为 null 是路径问题（style 里才有）",
       "null" in J[5]["evidence"]["note"]
       and "style" in J[5]["evidence"]["note"])
    ck("产物：判据 7 两个组的标题颜色前后都相同",
       J[7]["evidence"]["empty"]["changed"] is False
       and J[7]["evidence"]["withChild"]["changed"] is False)
    ck("产物：判据 8 附了「真的进了 selected 态」的阳性对照",
       J[8]["evidence"]["actuallySelected"] == {"empty": True,
                                                "withChild": True},
       J[8]["evidence"]["actuallySelected"])
    ck("产物：判据 9 的两格对比度都由脚本算出且都低于 AA 4.5",
       J[9]["evidence"]["videoGroupContrast"] is not None
       and J[9]["evidence"]["canvasContrast"] is not None
       and J[9]["evidence"]["videoGroupContrast"] < 4.5
       and J[9]["evidence"]["canvasContrast"] < 4.5
       and J[9]["evidence"]["aaThresholdNormalText"] == 4.5,
       [J[9]["evidence"]["videoGroupContrast"],
        J[9]["evidence"]["canvasContrast"]])
    ck("产物：判据 9 的对比度**可复算**（用产物里的颜色与底色重算一致）",
       contrast(J[9]["evidence"]["titleColor"],
                J[9]["evidence"]["videoGroupBg"])
       == J[9]["evidence"]["videoGroupContrast"]
       and contrast(J[9]["evidence"]["titleColor"],
                    J[9]["evidence"]["canvasBg"])
       == J[9]["evidence"]["canvasContrast"])
    ck("产物：判据 10 命中的是标题自身中心点且落在 pane",
       J[10]["evidence"]["titleHit_empty"]["pe"] == "none"
       and J[10]["evidence"]["titleHit_empty"]["inGroup"] is False,
       J[10]["evidence"]["titleHit_empty"])
    ck("产物：判据 12 记下空组的两个 handle 与 zoom",
       len(J[12]["evidence"]["emptyHandles"]) == 2
       and J[12]["evidence"]["zoom"] == 0.375)
    ck("产物：判据 16 三路对照含阴性对照（左键不按 Space deltaX=0）",
       J[16]["evidence"]["b1_leftNoSpace"]["deltaX"] == 0
       and J[16]["evidence"]["b1_leftNoSpace"]["viewportMoved"] is False
       and J[16]["evidence"]["b2_leftSpace"]["viewportMoved"] is True
       and J[16]["evidence"]["b3_middleNoSpace"]["viewportMoved"] is True)
    ck("产物：判据 17 记下 Space 抑制节点拖拽 + cursor-grab",
       J[17]["evidence"]["b4"]["nodeMoved"] is False
       and J[17]["evidence"]["b4"]["pastDelta"] == 0
       and "cursor-grab" in J[17]["evidence"]["b4"]["canvasClassWithSpace"])
    ck("产物：判据 18 记下护栏拦下越界计划并给出平移量",
       B["evidence"]["needRoomPx"] > 0
       and B["evidence"]["panDeltaX"] < 0
       and B["evidence"]["groupRectBefore"]["x"] !=
       B["evidence"]["groupRectAfterPan"]["x"])
    ck("产物：缺陷陈述含「不跟随」「parentId 仍挂着」两要素",
       "跟随" in a["headline"]["defect"]
       and "parentId" in a["headline"]["defect"])
    ck("产物：headline 有 compounds 段说明与 756 的叠加关系",
       "756" in a["headline"].get("compounds", "")
       and "屏幕上是一个原封不动的旧框" in a["headline"]["compounds"])
    ck("产物：证据链 5 条且都带具体读数",
       len(a["headline"]["proofChain"]) == 5
       and all(len(x) > 12 for x in a["headline"]["proofChain"]))
    ck("产物：返工 5 条 R19..R23 齐全且各自带 rule",
       [r["id"] for r in a["rework"]] == ["R19", "R20", "R21", "R22", "R23"]
       and all(r.get("rule") for r in a["rework"]),
       [r["id"] for r in a["rework"]])
    ck("产物：不声称清单 ≥ 9 条",
       len(a["notClaimed"]) >= 9, len(a["notClaimed"]))
    ck("产物：不声称里明确写了「没有与源站对照」与 oklab 解析限制",
       any("源站" in x for x in a["notClaimed"])
       and any("oklab" in x for x in a["notClaimed"]))
    ck("产物：rawProbeFiles 三个探针都有说明",
       sorted(a["rawProbeFiles"]) == ["a", "b", "c"])

    # ================= 原始读数交叉核对 =================
    if RAWA.exists() and RAWB.exists() and RAWC.exists():
        ra = json.loads(RAWA.read_text(encoding="utf-8"))
        rb = json.loads(RAWB.read_text(encoding="utf-8"))
        rc = json.loads(RAWC.read_text(encoding="utf-8"))
        a1, b1, c1 = ra["rounds"][0], rb["rounds"][0], rc["rounds"][0]
        vis = {g["id"]: g for g in a1["vis"]["groups"]}

        leaf = [
            ("j3.emptyGroup", J[3]["evidence"]["emptyGroup"],
             {k: c1["empty"]["after"][k] for k in
              ("id", "children", "untransformed", "title", "borderColor",
               "radius", "background")}),
            ("j3.withChildGroup", J[3]["evidence"]["withChildGroup"],
             {k: c1["withChild"]["after"][k] for k in
              ("id", "children", "untransformed", "title", "borderColor",
               "radius", "background")}),
            ("j6.titleRect", J[6]["evidence"]["titleRect"],
             c1["empty"]["after"]["titleRect"]),
            # ⚠ evidence 里除了读数还带一个 `static` 注释键 ⟹ 逐判据只取
            # **读数子集**来比，否则多出来的注释键会把每一格都判成不一致
            ("j7.titleColors", {k: v for k, v in J[7]["evidence"].items()
                                if k != "static"},
             {"empty": {"before": c1["empty"]["before"]["titleColor"],
                        "after": c1["empty"]["after"]["titleColor"],
                        "changed": c1["empty"]["titleColorChanged"]},
              "withChild": {"before": c1["withChild"]["before"]["titleColor"],
                            "after": c1["withChild"]["after"]["titleColor"],
                            "changed": c1["withChild"]["titleColorChanged"]}}),
            ("j8.actuallySelected", J[8]["evidence"]["actuallySelected"],
             {"empty": c1["empty"]["actuallySelected"],
              "withChild": c1["withChild"]["actuallySelected"]}),
            ("j10.titleHit", J[10]["evidence"]["titleHit_empty"],
             c1["empty"]["after"]["titleHit"]),
            ("j11.blankHit", J[11]["evidence"],
             {"emptyBlank": vis[G_EMPTY]["blankHit"],
              "withChildBlank": vis[G_WITH]["blankHit"]}),
            ("j12.handles", J[12]["evidence"]["emptyHandles"],
             vis[G_EMPTY]["handles"]),
            ("j13.after", J[13]["evidence"]["after"], a1["drag"]["after"]),
            ("j14.evidence", J[14]["evidence"],
             {"childrenNow": a1["drag"]["after"]["childrenNow"],
              "childFullyInsideGroup": a1["drag"]["after"]["childFullyInsideGroup"],
              "gapRight": a1["drag"]["gapRight"],
              "childRelBefore": a1["drag"]["before"]["childRel"],
              "childRelAfter": a1["drag"]["after"]["childRel"]}),
            ("j15", J[15]["evidence"],
             {"before": a1["drag"]["before"]["childRel"],
              "after": a1["drag"]["after"]["childRel"],
              "afterUndo": ra["rounds"][0]["afterUndo"]["childRel"],
              "pastAfterUndo": ra["rounds"][0]["afterUndo"]["past"]}),
            ("j16", {k: v for k, v in J[16]["evidence"].items() if k != "static"},
             {"b1_leftNoSpace": {k: b1["b1_leftNoSpace"].get(k)
                                 for k in ("viewportMoved", "deltaX")},
              "b2_leftSpace": {k: b1["b2_leftSpace"].get(k)
                               for k in ("viewportMoved", "deltaX")},
              "b3_middleNoSpace": {k: b1["b3_middleNoSpace"].get(k)
                                   for k in ("viewportMoved", "deltaX")}}),
            ("j17.b4", J[17]["evidence"]["b4"],
             {k: b1["b4_spaceNodeDrag"].get(k)
              for k in ("nodeMoved", "pastDelta", "hit",
                        "canvasClassWithSpace")}),
            ("b18.needRoom", {"needRoomPx": B["evidence"]["needRoomPx"],
                              "panFrom": B["evidence"]["panFrom"],
                              "groupRectBefore": B["evidence"]["groupRectBefore"],
                              "groupRectAfterPan":
                              B["evidence"]["groupRectAfterPan"]},
             {"needRoomPx": a1["needRoomPx"], "panFrom": a1["panFrom"],
              "groupRectBefore": a1["plan0"]["groupRect"],
              "groupRectAfterPan": a1["plan"]["groupRect"]}),
        ]
        bad = [n for n, x, y in leaf if _strip(x) != _strip(y)]
        ck("原始读数叶子级交叉核对 %d 项（a/b/c 三份）" % len(leaf), not bad, bad)

        ck("原始读数：a/b/c 三份各自两轮一致且 roundDiff 为空",
           ra["consistent"] and rb["consistent"] and rc["consistent"]
           and ra["roundDiff"] == {} and rb["roundDiff"] == {}
           and rc["roundDiff"] == {},
           [len(ra["roundDiff"]), len(rb["roundDiff"]), len(rc["roundDiff"])])
        # 核心缺陷：框不移动不缩放，但子节点动了且归属还在
        ck("原始读数：核心读数四格 = (不移动, 不缩放, store不动, 子节点动了)",
           a1["drag"]["groupDomMoved"] is False
           and a1["drag"]["groupDomResized"] is False
           and a1["drag"]["groupStoreMoved"] is False
           and a1["drag"]["childMoved"] is True)
        ck("原始读数：zoom 换算后 DOM 尺寸 == store 尺寸（两组四项）",
           c1["empty"]["after"]["untransformed"]["w"] == 430
           and c1["empty"]["after"]["untransformed"]["h"] == 452
           and c1["withChild"]["after"]["untransformed"]["w"] == 722
           and c1["withChild"]["after"]["untransformed"]["h"] == 460)
        ck("原始读数：两个种子分组 groupKind 都是 None（死字段的运行时侧证）",
           vis[G_EMPTY]["groupKind"] is None
           and vis[G_WITH]["groupKind"] is None)
        ck("原始读数：空组 DOM 仍在、title 仍在、2 个 handle 仍在",
           vis[G_EMPTY]["children"] == []
           and bool(vis[G_EMPTY]["titleText"])
           and len(vis[G_EMPTY]["handles"]) == 2)
        ck("原始读数：两个分组的 wrapperZ 都是 -1001",
           vis[G_EMPTY]["wrapperZ"] == "-1001"
           and vis[G_WITH]["wrapperZ"] == "-1001")
        ck("原始读数：variant 两组分别是 image / video 且圆角 20px / 4px",
           vis[G_EMPTY]["variant"] == "image"
           and vis[G_WITH]["variant"] == "video"
           and vis[G_EMPTY]["radius"] == "20px"
           and vis[G_WITH]["radius"] == "4px")
        ck("原始读数：选中后 border 变 rgb(9,202,245) 而标题仍是 rgb(119,119,119)",
           c1["empty"]["after"]["borderColor"] == "rgb(9, 202, 245)"
           and c1["empty"]["after"]["titleColor"] == "rgb(119, 119, 119)")
        ck("原始读数：平移三路 0 / 200 / 200（阴性对照为 0）",
           b1["b1_leftNoSpace"]["deltaX"] == 0
           and b1["b2_leftSpace"]["deltaX"] == 200
           and b1["b3_middleNoSpace"]["deltaX"] == 200,
           [b1["b1_leftNoSpace"]["deltaX"], b1["b2_leftSpace"]["deltaX"],
            b1["b3_middleNoSpace"]["deltaX"]])
        ck("原始读数：护栏记录里平移确实把分组 DOM x 往左挪了",
           B["evidence"]["panDeltaX"] == B["evidence"]["groupRectAfterPan"]["x"]
           - B["evidence"]["groupRectBefore"]["x"]
           and B["evidence"]["panDeltaX"] < 0, B["evidence"]["panDeltaX"])
    else:
        checks.append({"label": "原始读数交叉核对（/tmp/vb757{a,b,c}.json 不在本机）",
                       "pass": False, "got": "SKIPPED — 不算通过"})

    npass = sum(1 for c in checks if c["pass"])
    report = {"batch": 757, "checks": checks, "passed": npass,
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
