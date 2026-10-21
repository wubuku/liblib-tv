#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834 验收器 —— clone 导演台**时间轴引导的 5 步**（**实施批次**）。

## 本批做了什么

batch 556 只做了引导的**第 1 步**（文案 ＋ 「1/5」＋ 跳过／下一步，点「下一步」直接收起），
batch 831 记下「源站是 5 步引导、步骤 2–5 **未采样**」。

本批把源站的 5 步**一次采全**并**照抄实现**：

- 源站活体：开时间轴 ⟹ 逐点「下一步」直到「完成」⟹ 5 步的正文／宽度／位置／按钮全读到
  （`probes/coach834b.py`）；
- 源站 **chunk 原文**：组件 `cC` 的 5 步数据（target／文案键／width／bubbleOffsetX／
  bubbleHeight）＋ **定位算法** ＋ **状态机**（`onNext`／auto-advance／收起键）；
- clone：`src/components/director/DirectorTimelineGuide.tsx` 照抄数据 ＋ 算法 ＋ 类名。

★ 期望值全部从 raw 读（`raw/source-834-timeline-guide.json`，
  由 `probes/mk834raw.py` 从**活体 ＋ chunk 原文**两路交叉核对后产出）⟹ 不是手打。

★ 纪律：每条判据都有**只翻它自己那一条**的阴性对照。
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch834-2026-10-01"
RAW = BATCH / "raw"

SRC_RAW = RAW / "source-834-timeline-guide.json"
CLONE_RAW = RAW / "clone-834-timeline-guide.json"
SRC_GUIDE = ROOT / "src" / "components" / "director" / "DirectorTimelineGuide.tsx"
SRC_TIMELINE = ROOT / "src" / "components" / "director" / "DirectorTimeline.tsx"

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 本批的「探针」＝ **读入库读数的键名**（不是 DOM 选择器）：
#   键名一旦漂移，下面这些常量就取不到值 ⟹ 门禁自己会红。
K_CODE = "代码定义"
K_LIVE = "活体读数"
K_STEPS = "步数"
K_COUNT = "count"
K_TEXT = "正文"
K_BOX = "容器盒"
K_BUTTONS = "按钮"
K_TARGET = "target"
K_WIDTH = "width"
K_OFFSET = "bubbleOffsetX"
K_HEIGHT = "bubbleHeight"

K_CLONE_STEPS = "逐步"
K_CLONE_READ = "读数"
K_CLONE_RECALC = "重算"
K_CLONE_BUBBLE = "bubble"
K_CLONE_RING = "ring"
K_CLONE_END = "走完后"
K_CLONE_LS = "localStorage"
K_USED = "usedTarget"
K_VISIBLE_TARGETS = "visibleTargets"
# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# 组件源码里那 5 步的字面量（用来核验「源码里的常量 == raw」）
STEP_SRC_RE = re.compile(
    r'target:\s*"(?P<target>[a-z-]+)",\s*'
    r'text:\s*"(?P<text>[^"]*)",\s*'
    r'count:\s*"(?P<count>[^"]*)",\s*'
    r'width:\s*(?P<width>\d+),\s*'
    r'bubbleOffsetX:\s*(?P<offset>-?\d+),\s*'
    r'bubbleHeight:\s*(?P<height>\d+)'
)


def parse_component_steps(source_text):
    out = []
    for m in STEP_SRC_RE.finditer(source_text):
        out.append({
            "target": m.group("target"),
            "text": m.group("text"),
            "count": m.group("count"),
            K_WIDTH: int(m.group("width")),
            K_OFFSET: int(m.group("offset")),
            K_HEIGHT: int(m.group("height")),
        })
    return out


def build_checks(src_raw, clone_raw, guide_src, timeline_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    code = src_raw.get(K_CODE) or []
    live = src_raw.get(K_LIVE) or []
    steps = clone_raw.get(K_CLONE_STEPS) or []

    # ── S1 源站 raw 的完备性（只读元数据）──
    ok("S1:★★★ **源站 raw 完备**：5 步、**代码定义**与**活体读数**各 5 条、"
       "chunk 锚点齐全 ⟹ ★ 两路交叉核对已在生成时做过（不一致就拒绝出 raw）",
       src_raw.get(K_STEPS) == 5 and len(code) == 5 and len(live) == 5
       and len(src_raw.get("★状态机锚点") or []) >= 8
       and bool(src_raw.get("★收起标记")),
       {"步数": src_raw.get(K_STEPS), "代码定义条数": len(code),
        "活体读数条数": len(live),
        "状态机锚点数": len(src_raw.get("★状态机锚点") or []),
        "收起标记": src_raw.get("★收起标记")})

    # ── S2 5 步的**正文**逐字相同 ──
    s_texts = [x.get(K_TEXT) for x in live]
    c_texts = [((x.get(K_CLONE_READ) or {}).get(K_CLONE_BUBBLE) or {}).get("text")
               for x in steps]
    # ★★ 还要核**组件源码里写死的那 5 条文案** ⟹ 否则「clone 的读数 == 源站的读数」
    #   只证明了**入库那一刻**相等 ⟹ 源码后来被改坏，门禁仍然绿。
    src_texts = [p.get("text") for p in parse_component_steps(guide_src)]
    ok("S2:★★★★★ clone 的 **5 步正文**与源站**逐字相同**"
       "（请选择一个角色或者摄像机后…／点击创建路径…／点击圆环/直线/矩形…／"
       "路径绘制后点击播放…／预览动画效果已确认…）"
       "⟹ ★ 三处相等：源站 raw ↔ clone 活体读数 ↔ **clone 组件源码里写死的那 5 条**",
       s_texts == c_texts and s_texts == src_texts
       and len(c_texts) == 5 and all(s_texts),
       {"源站": s_texts, "clone读数": c_texts, "组件源码": src_texts})

    # ── S3 5 个**步数**相同（1/5…5/5）──
    s_counts = [x.get(K_COUNT) for x in live]
    c_counts = [((x.get(K_CLONE_READ) or {}).get(K_CLONE_BUBBLE) or {}).get("count")
                for x in steps]
    ok("S3:★★★★★ clone 的 **5 个步数**与源站相同（1/5…5/5）"
       "⟹ ★ 源站的步数是**硬编码的字符串**（chunk 原文 `count:\"1/5\"`）",
       s_counts == c_counts == ["1/5", "2/5", "3/5", "4/5", "5/5"],
       {"源站": s_counts, "clone": c_counts})

    # ── S4 5 个**宽度**相同（260/300/360/300/360）──
    s_widths = [(x.get(K_BOX) or {}).get("w") for x in live]
    c_widths = [((x.get(K_CLONE_READ) or {}).get(K_CLONE_BUBBLE) or {}).get("box", {}).get("w")
                for x in steps]
    ok("S4:★★★★★ clone 的 **5 个气泡宽度**与源站相同"
       "（260／300／360／300／360）⟹ ★ 源站**每步宽度不同**（随文案长度定档）",
       s_widths == c_widths == [260, 300, 360, 300, 360],
       {"源站": s_widths, "clone": c_widths})

    # ── S5 **按钮**逐枚相同（前 4 步 跳过/下一步；第 5 步 跳过/完成）──
    s_btns = [x.get(K_BUTTONS) for x in live]
    c_btns = [[b.get("t") for b in
               (((x.get(K_CLONE_READ) or {}).get(K_CLONE_BUBBLE) or {}).get("buttons") or [])]
              for x in steps]
    ok("S5:★★★★★ clone 的 **按钮**与源站逐枚相同"
       "（前 4 步「跳过／下一步」、第 5 步「跳过／**完成**」）"
       "⟹ ★ 源站末步那枚按钮是**另一个词**（chunk 原文 `4===e?…Complete:…Next`）",
       s_btns == c_btns
       and all(b == ["跳过", "下一步"] for b in c_btns[:4])
       and c_btns[4] == ["跳过", "完成"],
       {"源站": s_btns, "clone": c_btns})

    # ── S6 **定位算法**被照抄（渲染位置 == 按源站算法重算的位置）──
    diffs = []
    for x in steps:
        b = ((x.get(K_CLONE_READ) or {}).get(K_CLONE_BUBBLE) or {})
        rc = x.get(K_CLONE_RECALC) or {}
        if b.get("box", {}).get("x") != rc.get("left") or \
           b.get("box", {}).get("y") != rc.get("top"):
            diffs.append({"步序": x.get("步序"), "渲染": [b.get("box", {}).get("x"),
                                                        b.get("box", {}).get("y")],
                          "重算": [rc.get("left"), rc.get("top")]})
    ok("S6:★★★★★ clone 的**定位算法**与源站**逐字同构** ⟹ "
       "**渲染出来的气泡位置** == **按源站 chunk 原文的算法重算出来的位置**（5 步全对）"
       "⟹ ★ 判的是「算法被照抄了」，不是「某个绝对坐标碰巧对」",
       len(steps) == 5 and not diffs,
       {"不一致的步": diffs,
        "每步的重算值": [{"步序": x.get("步序"),
                          "重算": [x.get(K_CLONE_RECALC, {}).get("left"),
                                   x.get(K_CLONE_RECALC, {}).get("top")],
                          "用的目标": x.get(K_CLONE_RECALC, {}).get(K_USED)}
                         for x in steps]})

    # ── S7 光环是 60×60（源站 ring.size）──
    rings = [((x.get(K_CLONE_READ) or {}).get(K_CLONE_RING) or {}).get("box", {})
             for x in steps]
    ok("S7:★★★★★ clone 的**目标光环**是 **60×60**（源站 chunk 原文 `ring.size=60`、"
       "`rippleSize=24`）⟹ ★ 源站用一圈 24px 的涟漪圆在 60px 的盒子里脉动",
       len(rings) == 5 and all(r.get("w") == 60 and r.get("h") == 60 for r in rings),
       {"每步的光环盒": rings})

    # ── S8 兜底链与源站一致（motion-preset-ring 不在 ⟹ 退回 draw-trajectory）──
    used = [x.get(K_CLONE_RECALC, {}).get(K_USED) for x in steps]
    ok("S8:★★★★★ clone 的**兜底链**与源站一致：第 3 步的 target 是 "
       "`motion-preset-ring`（只在运动路径浮层打开时才存在）⟹ 场景里没有时"
       "**退回 draw-trajectory**（源站 chunk 原文的 `?? cs(\"draw-trajectory\")`）",
       len(used) == 5 and used[2] == "draw-trajectory"
       and used[0] == "add-track" and used[3] == "play"
       and used[4] == "export-to-canvas",
       {"每步实际用的目标": used})

    # ── S9 走完会**消失** ＋ 收起标记写入 ──
    end = clone_raw.get(K_CLONE_END) or {}
    ok("S9:★★★★★ clone 点完第 5 步的「完成」后引导**整块消失**（气泡 ＋ 覆盖层）"
       "⟹ 且 localStorage 标记写入 `\"1\"`（源站的收起键是 "
       "`libtv.director.timeline-guide.dismissed.v1`；clone 沿用自己的键，"
       "**因为门禁 36／575 直接断言它**）",
       not (end.get(K_CLONE_BUBBLE)) and not end.get("overlay")
       and clone_raw.get(K_CLONE_LS) == "1",
       {"走完后的气泡": end.get(K_CLONE_BUBBLE),
        "走完后的覆盖层": end.get("overlay"),
        "localStorage": clone_raw.get(K_CLONE_LS)})

    # ── S10 五个 target 标记**齐全** ──
    targets = set()
    for x in steps:
        targets |= set(x.get(K_CLONE_READ, {}).get(K_VISIBLE_TARGETS) or [])
    ok("S10:★★★★★ clone 的 **target 标记齐全**（`add-track`／`draw-trajectory`／"
       "`play`／`export-to-canvas` 四个**常驻**目标；`motion-preset-ring` 只在"
       "运动路径浮层打开时才在 DOM 里）⟹ ★ 源站就是用 `data-director-timeline-guide-target` "
       "标记目标（chunk 原文）",
       {"add-track", "draw-trajectory", "play", "export-to-canvas"} <= targets,
       {"clone 里可见的 target": sorted(targets)})

    # ── S11 组件源码里的 5 步**常量**与 raw 的「代码定义」逐字相符 ──
    parsed = parse_component_steps(guide_src)
    diff = []
    for i, p in enumerate(parsed[:5]):
        if i >= len(code):
            diff.append((i, "组件多出一枚"))
            continue
        c0 = code[i]
        for key in (K_TARGET, K_COUNT, K_WIDTH, K_OFFSET, K_HEIGHT):
            if p.get(key) != c0.get(key):
                diff.append((i, key, p.get(key), c0.get(key)))
    ok("S11:★★★★★ clone 组件源码里那 5 步的**常量**与源站 raw 的「代码定义」"
       "**逐字相符**（target／count／width／bubbleOffsetX／bubbleHeight）"
       "⟹ ★ 期望值来自 raw（chunk 原文）⟹ 源码里不是手打的",
       len(parsed) == 5 and not diff,
       {"解析到几枚": len(parsed), "不一致": diff,
        "解析到的第 0 枚": parsed[0] if parsed else None})

    # ── S12 z-index 必须走 inline style（★ 本批真缺陷的钉子）──
    # ★ 只在 **className 属性**里找 `z-[` ⟹ 注释里提到「z-[1900]」不算数
    #   （第一版判据直接全文搜 `"z-[1900]"` ⟹ 命中了**自己写的注释** ⟹ 恒红）。
    arbitrary_z_in_class = re.findall(r'className="[^"]*\bz-\[[^"]*"', guide_src)
    ok("S12:★★★★★ clone 的**层叠**走 **inline style**（覆盖层 zIndex 1900 ＋ "
       "气泡 1 ＋ 光环 2）⟹ ★★ **不得**用 Tailwind 任意值类"
       "（`z-[1900]`）：4317 的 Tailwind 扫描是**冻结**的（batch 824）⟹ "
       "新增任意值类在 dev 上**不生成** ⟹ z-index 落回 auto ⟹ 整块引导被时间轴的 "
       "z-30 盖住 ⟹ ★★ **「下一步」按钮点不动**（本批实测到的真缺陷）",
       "zIndex: 1900" in guide_src and "zIndex: 1" in guide_src
       and "zIndex: 2" in guide_src
       and not arbitrary_z_in_class,
       {"源码里的 zIndex": [ln.strip() for ln in guide_src.splitlines()
                       if "zIndex" in ln][:4],
        "★className 里是否还有 z-[n] 任意值类": arbitrary_z_in_class})

    # ── S13 「使用教程」会**复位**到第 1 步 ──
    ok("S13:★★★★★ clone 的 rail「帮助 → 使用教程」会把引导**复位到第 1 步**"
       "（`setGuideStep(0)` ＋ 清掉收起标记）⟹ ★ 否则点「使用教程」只会从"
       "「上次的步」继续，而不是从头开始",
       "setGuideStep(0)" in timeline_src
       and 'window.localStorage.removeItem("director-timeline-coach-dismissed")'
       in timeline_src,
       {"timeline 里的锚点": [ln.strip() for ln in timeline_src.splitlines()
                      if "setGuideStep(0)" in ln
                      or "removeItem" in ln][:4]})

    # ── S14 旧属性名保留（门禁 556／557 靠它定位）──
    ok("S14:★★★★★ clone 保留了**旧属性名**（`data-director-timeline-coachmark`／"
       "`data-director-coachmark-skip`／`data-director-coachmark-next`）作为别名"
       "⟹ ★ 门禁 556／557 直接按它们定位 ⟹ 改名会让那两条门禁失效",
       "data-director-timeline-coachmark" in guide_src
       and "data-director-coachmark-skip" in guide_src
       and "data-director-coachmark-next" in guide_src,
       {"组件里的旧属性名": [ln.strip() for ln in guide_src.splitlines()
                      if "coachmark" in ln][:4]})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n1(sr, cr, gs, ts):
        c = copy.deepcopy(sr)
        c[K_LIVE][0][K_TEXT] = "请选择一个角色或者摄像机后"
        return c, cr, gs, ts

    def n2(sr, cr, gs, ts):
        c = copy.deepcopy(sr)
        c[K_LIVE][1][K_COUNT] = "2/4"
        return c, cr, gs, ts

    def n3(sr, cr, gs, ts):
        c = copy.deepcopy(sr)
        c[K_LIVE][2][K_BOX]["w"] = 320
        return c, cr, gs, ts

    def n4(sr, cr, gs, ts):
        c = copy.deepcopy(sr)
        c[K_LIVE][4][K_BUTTONS] = ["跳过", "下一步"]
        return c, cr, gs, ts

    def n5(sr, cr, gs, ts):
        c = copy.deepcopy(cr)
        c[K_CLONE_STEPS][1][K_CLONE_READ][K_CLONE_BUBBLE]["box"]["x"] += 7
        return sr, c, gs, ts

    def n6(sr, cr, gs, ts):
        c = copy.deepcopy(cr)
        c[K_CLONE_STEPS][0][K_CLONE_READ][K_CLONE_RING]["box"]["w"] = 48
        return sr, c, gs, ts

    def n7(sr, cr, gs, ts):
        c = copy.deepcopy(cr)
        c[K_CLONE_STEPS][2][K_CLONE_RECALC][K_USED] = "add-track"
        return sr, c, gs, ts

    def n8(sr, cr, gs, ts):
        c = copy.deepcopy(cr)
        c[K_CLONE_END]["overlay"] = True
        c[K_CLONE_LS] = None
        return sr, c, gs, ts

    def n9(sr, cr, gs, ts):
        # ★ S10 读的是**各步可见 target 的并集** ⟹ 负控必须把**每一步**都砍掉，
        #   只砍第 1 步的话，后 4 步仍然带着完整清单 ⟹ 判据照样绿（没翻）。
        c = copy.deepcopy(cr)
        for x in c[K_CLONE_STEPS]:
            x[K_CLONE_READ][K_VISIBLE_TARGETS] = ["add-track"]
        return sr, c, gs, ts

    def n10(sr, cr, gs, ts):
        g = gs.replace("bubbleOffsetX: -48,", "bubbleOffsetX: -50,", 1)
        return sr, cr, g, ts

    def n11(sr, cr, gs, ts):
        g = gs.replace("zIndex: 1900", "zIndex: 19")
        return sr, cr, g, ts

    def n12(sr, cr, gs, ts):
        t = ts.replace("setGuideStep(0);", "/* removed */")
        return sr, cr, gs, t

    def n13(sr, cr, gs, ts):
        g = gs.replace("data-director-coachmark-skip", "data-director-guide-skip")
        return sr, cr, g, ts

    def n14(sr, cr, gs, ts):
        c = copy.deepcopy(sr)
        c[K_STEPS] = 4
        return c, cr, gs, ts

    def n15(sr, cr, gs, ts):
        # ★ 扰动**组件源码里的文案** ⟹ 只翻 S2（其余判据不读文案）
        g = gs.replace("点击创建路径，弹出选项面板", "点击创建路径，弹出选项", 1)
        return sr, cr, g, ts

    return [
        ("N1 改源站第 1 步的正文 ⟹ S2 翻红", "S2", n1),
        ("N2 改源站第 2 步的步数 ⟹ S3 翻红", "S3", n2),
        ("N3 改源站第 3 步的宽度 ⟹ S4 翻红", "S4", n3),
        ("N4 把源站第 5 步的「完成」改成「下一步」⟹ S5 翻红", "S5", n4),
        ("N5 把 clone 第 2 步的渲染位置挪 7px ⟹ S6 翻红", "S6", n5),
        ("N6 把 clone 第 1 步的光环改成 48px ⟹ S7 翻红", "S7", n6),
        ("N7 把 clone 第 3 步用的目标改成 add-track ⟹ S8 翻红", "S8", n7),
        ("N8 让 clone 走完后引导仍在 ⟹ S9 翻红", "S9", n8),
        ("N9 把 clone 的可见 target 砍到只剩一个 ⟹ S10 翻红", "S10", n9),
        ("N10 改组件源码里第 3 步的 bubbleOffsetX ⟹ S11 翻红", "S11", n10),
        ("N11 把覆盖层的 inline zIndex 改小 ⟹ S12 翻红", "S12", n11),
        ("N12 删掉「使用教程」的复位 ⟹ S13 翻红", "S13", n12),
        ("N13 删掉旧属性名别名 ⟹ S14 翻红", "S14", n13),
        ("N14 把源站的步数改成 4 ⟹ S1 翻红", "S1", n14),
        ("N15 改组件源码里第 2 步的文案 ⟹ S2 翻红", "S2", n15),
    ]


def main():
    src_raw = json.loads(SRC_RAW.read_text(encoding="utf-8"))
    clone_raw = json.loads(CLONE_RAW.read_text(encoding="utf-8"))
    guide_src = SRC_GUIDE.read_text(encoding="utf-8")
    timeline_src = SRC_TIMELINE.read_text(encoding="utf-8")

    checks = build_checks(src_raw, clone_raw, guide_src, timeline_src)
    neg = []
    for label, expect, builder in _negations():
        args = builder(src_raw, clone_raw, guide_src, timeline_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 834, "mode": "offline",
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                           "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:92])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:52]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
