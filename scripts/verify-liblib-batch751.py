#!/usr/bin/env python3
"""batch 751 验收器：三族剩下的 25 种

750 走的是**一条**链（选 camera 轨道 → 建 line → 开曲线编辑器），三族从 2 种涨到
27 种，静态 52 种里**仍缺 25 种**。本批把 25 种按门分五组各走一遍。

判据只判「与采样/随机 id/指针位置无关」的性质。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch751-2026-10-01"
PROBE = "/tmp/dbg751e.py"
FAM_PREFIXES = ("data-director-motion", "data-director-path", "data-director-curve")


def static_side():
    d = ROOT / "src/components/director"
    union, owner = set(), {}
    for f in sorted(d.glob("*.tsx")):
        for i, l in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            for m in re.finditer(r"\b(data-[a-z0-9-]+)", l):
                union.add(m.group(1))
                owner.setdefault(m.group(1), []).append(f"{f.name}:{i}")
            for m in re.finditer(r"\.dataset\.([A-Za-z0-9_]+)\s*=", l):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                union.add("data-" + kebab)
                owner.setdefault("data-" + kebab, []).append(f"{f.name}:{i}")
    tl = (d / "DirectorTimeline.tsx").read_text(encoding="utf-8")
    mt = (d / "DirectorCameraMotionTab.tsx").read_text(encoding="utf-8")
    insp = (d / "DirectorInspector.tsx").read_text(encoding="utf-8")
    vp = (d / "DirectorViewport.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")

    def lines(text, pat, nth=None):
        hits = [i for i, l in enumerate(text.split("\n"), 1) if re.search(pat, l)]
        return hits if nth is None else ([hits[nth]] if len(hits) > nth else [])

    return {
        "unionTotal": len(union),
        "familyCount": len([n for n in union if n.startswith(FAM_PREFIXES)]),
        "familyByPrefix": {p: len([n for n in union if n.startswith(p)]) for p in FAM_PREFIXES},
        "keyframe": {
            # selectTimelineKeyframe 在组件层的调用点
            "selectCallSitesInTimeline": lines(tl, r"selectTimelineKeyframe\("),
            # 左侧轨道行的菱形：增删 toggle
            "rowToggleAdd": lines(tl, r"addTimelineKeyframe\(track\.id\)"),
            "rowToggleDelete": lines(tl, r"deleteTimelineKeyframe\(keyframe\.id\)"),
            # 泳道区菱形：选中 + seek
            "laneSelect": lines(tl, r"selectTimelineKeyframe\(track\.id, keyframe\.id\)"),
            "laneSeek": lines(tl, r"setTimelineTime\(keyframe\.time\)"),
            "seedSelectedKeyframeId": re.findall(r'selectedKeyframeId:\s*"([^"]+)"',
                                                 store)[:2],
        },
        "motionTabGate": {
            "keyframeEditorGuard": lines(mt, r"\{selectedKeyframe && selectedTransform \?"),
            "sliderFieldComponent": lines(mt, r"function MotionSliderField"),
            "readKeyframeTransform": lines(mt, r"function readKeyframeTransform"),
        },
        "orientGate": {
            "pathControlsRotationY": lines(insp, r"const pathControlsRotationY"),
            "withCondition": lines(insp, r"selectedPath\?\.enabled === true"),
            "orientButton": lines(insp, r"data-director-motion-path-orient"),
            "enableButton": lines(insp, r"data-director-motion-path-enabled"),
            "disabledAxesCall": lines(insp, r"disabledAxes=\{pathControlsRotationY \? \[1\] : \[\]\}"),
            "genericAxisAttrs": lines(insp, r"data-director-transform-field"),
            "pathAxisAttrs": lines(insp, r"data-director-path-transform-field"),
            "rotationHint": lines(insp, r"data-director-motion-path-rotation-hint"),
        },
        "pencil": {
            "pointerDownSeed": lines(vp, r"appendMotionPathDraftAnchor\(pointFromEvent"),
            "finishOnPointerUp": lines(vp, r"if \(draft\.tool === \"pencil\"\)", nth=1),
        },
    }


def static_names():
    d = ROOT / "src/components/director"
    union = set()
    for f in sorted(d.glob("*.tsx")):
        for l in f.read_text(encoding="utf-8").split("\n"):
            union.update(re.findall(r"\b(data-[a-z0-9-]+)", l))
            for m in re.finditer(r"\.dataset\.([A-Za-z0-9_]+)\s*=", l):
                union.add("data-" + re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1)))
    return sorted(n for n in union if n.startswith(FAM_PREFIXES))


def normalize(d):
    unstable = {"value", "time", "laneY", "kfY", "kfId", "id", "heading", "raw"}
    # 路径 id / 世界坐标随时间戳与场景变化，不进两轮比对
    def scrub(o):
        if isinstance(o, dict):
            return {k: ("<UNSTABLE>" if k in unstable else scrub(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [scrub(x) for x in o]
        return o

    s = json.dumps(scrub(d), ensure_ascii=False, sort_keys=True)
    s = re.sub(r"-\d{13}", "-<TS>", s)
    s = re.sub(r"\d{13}", "<TS>", s)
    s = re.sub(r"-?\d+\.\d{4,}", "<F>", s)
    s = re.sub(r"\s+", " ", s)
    return s


def run_probe():
    r = subprocess.run([sys.executable, PROBE], capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"探针失败 exit={r.returncode}")
    return json.loads(pathlib.Path("/tmp/vb751e.json").read_text(encoding="utf-8"))


def build_checks(st, run):
    c = []

    def add(label, ok, detail):
        c.append({"label": label, "pass": bool(ok), "detail": detail})

    k = st["keyframe"]
    add("C1 静态：三族共 %d 种（%s）；`selectTimelineKeyframe` 在时间线里**只有一个**调用点"
        "（泳道区菱形）且同时 seek 播头；左侧轨道行的菱形是 add/delete toggle，"
        "两者行号不同"
        % (st["familyCount"], st["familyByPrefix"]),
        st["familyCount"] == 52
        and len(k["selectCallSitesInTimeline"]) == 1
        and k["selectCallSitesInTimeline"] == k["laneSelect"]
        and len(k["laneSelect"]) == 1 and len(k["rowToggleAdd"]) == 1
        and len(k["rowToggleDelete"]) == 1
        and k["laneSelect"][0] not in (k["rowToggleAdd"][0], k["rowToggleDelete"][0])
        and k["laneSeek"][0] == k["laneSelect"][0] + 1
        and k["seedSelectedKeyframeId"],
        {"familyByPrefix": st["familyByPrefix"], "keyframe": k})

    g = st["motionTabGate"]
    add("C2 静态：运动页签的滑块字段与关键帧编辑器**共用一个守卫**"
        "`{selectedKeyframe && selectedTransform ? ... : null}`（两者在同一个文件同一段）",
        len(g["keyframeEditorGuard"]) == 1 and len(g["sliderFieldComponent"]) == 1
        and len(g["readKeyframeTransform"]) == 1
        and g["sliderFieldComponent"][0] < g["keyframeEditorGuard"][0] < 300,
        g)

    s1 = run.get("s1_motionTabLocked", {})
    add("C3 门未开：进运动页签只带出 6 种顶层，**滑块 0 个、关键帧编辑器不存在** "
        "⟹ 滑块与编辑器确实被那一个守卫挡着",
        len(s1.get("opened", [])) == 6 and s1.get("sliders") == []
        and s1.get("keyframeEditorPresent") is False
        and sorted(s1.get("opened", [])) == [
            "data-director-motion-create-path", "data-director-motion-preset-button",
            "data-director-motion-qr", "data-director-motion-record",
            "data-director-motion-retry", "data-director-motion-vcam"],
        s1)

    s2 = run.get("s2_menu", {})
    add("C4 路径菜单带出 4 种；选「钢笔路径」后绘制态再带出 4 种（面板有完成键与取消键）",
        len(s2.get("menuOpened", [])) == 4 and len(s2.get("drawOpened", [])) == 4
        and (s2.get("draw") or {}).get("open") is True
        and (s2.get("draw") or {}).get("tool") == "pen"
        # 中文按码位排：「取」U+53D6 < 「完」U+5B8C ⟹ 排序后取消在前
        and sorted(x["a"] for x in (s2.get("draw") or {}).get("buttons", []))
        == sorted(["取消路径绘制", "完成钢笔路径"]),
        {"menuOpened": s2.get("menuOpened"), "drawOpened": s2.get("drawOpened"),
         "draw": s2.get("draw")})

    s3 = run.get("s3_anchor", {})
    types = s3.get("typeOptions", [])
    handles = s3.get("handleFields", [])
    anchors = ((s3.get("paths") or {}).get("paths") or [{}])[0].get("anchors") or []
    sym = next((a for a in anchors if a.get("type") == "symmetric"), {})
    inv = [h for h in handles if h["h"] == "in"]
    outv = [h for h in handles if h["h"] == "out"]
    symmetric = (len(inv) == 3 and len(outv) == 3
                 and all(abs(float(i["value"]) + float(o["value"])) < 1e-6
                         for i, o in zip(sorted(inv, key=lambda x: x["axis"]),
                                         sorted(outv, key=lambda x: x["axis"]))))
    add("C5 选中锚点带出 2 种（位置字段 + 锚点类型三档 顶点/对称/非对称）；"
        "改成「对称」再带出 3 种，手柄字段 in/out 各三轴且**数值严格相反**",
        len(s3.get("afterSelectAnchor", [])) == 2 and len(s3.get("afterSymmetric", [])) == 3
        and [t["text"] for t in types] == ["顶点", "对称", "非对称"]
        and sorted(sym.get("handles") or []) == ["in", "out"] and symmetric,
        {"afterSelectAnchor": s3.get("afterSelectAnchor"),
         "afterSymmetric": s3.get("afterSymmetric"),
         "typeOptions": types, "handleFields": handles,
         "symmetricAnchor": sym})

    s4 = run.get("s4_keyframe", {})
    lane = s4.get("laneKeyframes", [])
    cam_lane = [x for x in lane if x["kind"] == "camera"]
    ins = s4.get("inputs", [])
    pairs = sorted((x["field"], x["axis"]) for x in ins)
    add("C6 泳道区关键帧菱形 %d 个（camera 轨道 3 个），点**机位**轨道那个 ⟹ "
        "编辑器标题与被点的时刻一致，9 个输入是 3 字段 × 3 轴**平铺在同一个 input 上**"
        "（不是容器-子元素）；滑块 2 个：时长 0–10 step 0.01、统一缩放 0.1–10 step 0.05"
        % len(lane),
        len(lane) == 6 and len(cam_lane) == 3
        and all(x["w"] == 11 and x["h"] == 11 for x in lane)
        and s4.get("heading") == f"关键帧 {float(s4['picked']['time']):.2f}s"
        and pairs == sorted([(f, str(a)) for f in ("position", "rotation", "scale") for a in (0, 1, 2)])
        and len(ins) == 9
        and sorted((x["t"], x["min"], x["max"], x["step"]) for x in s4.get("sliders", []))
        == [("duration", "0", "10", "0.01"), ("uniform-scale", "0.1", "10", "0.05")],
        {"laneCount": len(lane), "cameraLanes": len(cam_lane),
         "picked": s4.get("picked"), "heading": s4.get("heading"),
         "inputs": ins, "sliders": s4.get("sliders"),
         "rowKeyframeButtons": len(s4.get("rowKeyframeButtons", []))})

    s5 = run.get("s5_orient", {})
    rot_b = s5.get("genRotationBefore") or []
    rot_a = s5.get("genRotationAfter") or []
    yb = next((x for x in rot_b if x["axis"] == "y"), {})
    ya = next((x for x in rot_a if x["axis"] == "y"), {})
    og = st["orientGate"]
    add("C7 **曲线默认就是启用的**（我没点它，`aria-pressed` 已是 true，而 label 恒为「启用曲线」"
        "不随状态变）；只点朝向 ⟹ 提示出现，**且通用 rotation 的 Y 轴真的 `disabled`、"
        "值从一个非零值变成另一个非零值** ⟹ 提示兑现、不是空话",
        (s5.get("enableUntouched") or {}).get("pressed") == "true"
        and (s5.get("enableUntouched") or {}).get("label") == "启用曲线"
        and s5.get("hintBefore") is False and (s5.get("hintAfter") or {}).get("text")
        == "已开启沿路径朝向，Y 轴旋转由运动轨迹控制"
        and s5.get("openedByOrient") == ["data-director-motion-path-rotation-hint"]
        and yb.get("disabled") is False and ya.get("disabled") is True
        and abs(float(yb.get("value", 0))) > 1e-6 and abs(float(ya.get("value", 0))) > 1e-6
        and yb.get("value") != ya.get("value")
        and len(og["disabledAxesCall"]) == 1
        and og["genericAxisAttrs"][0] != og["pathAxisAttrs"][0],
        {"enableUntouched": s5.get("enableUntouched"),
         "orientBefore": s5.get("orientBefore"),
         "hintAfter": s5.get("hintAfter"),
         "genRotationBefore": rot_b, "genRotationAfter": rot_a,
         "orientGate": og})

    rr = run.get("residue", {})
    add("C8 单次线性走链：静态三族 %d 种；走完（选 camera 轨道 → 建 line → 选中锚点 → 改对称 → "
        "开朝向 → 开菜单 → 选钢笔 → 点泳道关键帧 → 进 motion 页签）后剩 %d 种。"
        "**这个数不是「打不开」，是「一次只能开一个互斥面板」**"
        % (rr.get("staticThreeFamilies", 0), len(rr.get("stillMissing", []))),
        rr.get("staticThreeFamilies") == st["familyCount"]
        and rr.get("after", 0) - rr.get("before", 0) == rr.get("opened"),
        {"before": rr.get("before"), "after": rr.get("after"),
         "opened": rr.get("opened"), "stillMissing": rr.get("stillMissing")})

    # C9 并集：五组加起来是否真的把三族全覆盖了（这是 C8 回答不了的那一半）
    per_group = {
        "组1 运动页签": run.get("s1_motionTabLocked", {}).get("opened", []),
        "组2 路径菜单": run.get("s2_menu", {}).get("menuOpened", []),
        "组2 绘制态": run.get("s2_menu", {}).get("drawOpened", []),
        "组3 选中锚点": run.get("s3_anchor", {}).get("afterSelectAnchor", []),
        "组3 改对称": run.get("s3_anchor", {}).get("afterSymmetric", []),
        "组4 关键帧": run.get("s4_keyframe", {}).get("opened", []),
        "组5 朝向": run.get("s5_orient", {}).get("openedByOrient", []),
    }
    # 组5「建路径」这一步带出的属性里含 motion-path-orient —— 它被
    # DirectorTimeline/Inspector 的 `selectedTrack?.kind === "transform"` 挡住
    # （:1169），750 那条链走的是 camera 轨道所以从没出现过
    orient_group = list(run.get("s5_orient", {}).get("afterBuild", []))
    per_group["组5 建路径(transform 轨道)"] = orient_group
    union = set()
    for v in per_group.values():
        union |= set(v)
    static52 = static_names()
    # 750 那条链已在场的种数：直接读 750 已提交的审计产物，不重跑（跨批对账）
    prev_path = OUTDIR.parent / "liblib-canvas-batch750-2026-10-01/runtime-audit.json"
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else {}
    prev_missing = prev.get("run", {}).get("residue", {}).get("stillMissing") or []
    prev_covered = set(static52) - set(prev_missing) if prev_missing else set()
    covered = union | prev_covered
    uncovered = sorted(set(static52) - covered)
    overlap = sorted(union & prev_covered)
    add("C9 **跨批并集**：本批各组新增 %d 种（组4 的 11 种里 6 种与组1 重叠；"
        "`motion-path-orient` 被 `kind === \"transform\"` 挡着、只在组5 的 transform 轨道上出现），"
        "与 750 已提交审计里「已在场」的 %d 种合并 = %d 种，"
        "**正好覆盖静态三族全集 %d 种**、未覆盖 %d 种"
        % (len(union), len(prev_covered), len(covered), len(static52), len(uncovered)),
        len(covered) == len(static52) == 52 and uncovered == [],
        {"perGroup": {k: len(v) for k, v in per_group.items()},
         "unionNew": len(union), "prevBatchCovered": len(prev_covered),
         "overlapWith750": overlap, "covered": len(covered),
         "static52": len(static52), "uncovered": uncovered,
         "readFrom": prev_path.name})

    # C10 为什么不能只看一条链
    s6_lost = sorted(set(prev_covered) - set(run.get("residue", {}).get("namesAfter", [])))
    add("C10 **一条链装不下三族** —— 路径检查器面板与运动页签 / 曲线编辑器模式**互斥**："
        "单次线性走完之后，750 曾开过的 %d 种里有 %d 种不在场 ⟹ 「走完还缺 %d 种」"
        "是互斥面板的假象，不是打不开"
        % (len(prev_covered), len(s6_lost), len(rr.get("stillMissing", []))),
        len(s6_lost) > 0
        and all(n.startswith(FAM_PREFIXES) for n in s6_lost)
        and set(rr.get("stillMissing", [])) == set(static52)
        - (set(run.get("residue", {}).get("namesAfter", [])) & set(static52)),
        {"s6Present": len(run.get("residue", {}).get("namesAfter", [])),
         "lostFromPrevBatch": len(s6_lost), "sample": s6_lost[:8]})

    return c


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    st = static_side()
    print("静态：并集 %d；目标三族 %d（%s）" % (st["unionTotal"], st["familyCount"],
                                          st["familyByPrefix"]))
    print("两轮跑探针……")
    r1 = run_probe()
    r2 = run_probe()
    idem = normalize(r1) == normalize(r2)
    if not idem:
        import difflib
        a, b = normalize(r1), normalize(r2)
        print("两轮不一致，前 30 处差异：")
        print("\n".join(list(difflib.unified_diff(a.split(", "), b.split(", "),
                                                  lineterm="", n=1))[:30]))
    checks = build_checks(st, r1)
    npass = sum(1 for x in checks if x["pass"])
    report = {
        "batch": 751,
        "title": "把三族剩下的 25 种按门分五组打开；关键帧编辑器在泳道区不在轨道行；曲线默认已启用",
        "verdict": f"{npass}/{len(checks)}",
        "twoRoundsIdentical": idem,
        "static": st,
        "run": r1,
        "checks": checks,
        "probeCorrections": [
            "探针 a：组4 点的是**左侧轨道行**里 aria-label 含「关键帧」的按钮 —— 那是"
            "addTimelineKeyframe / deleteTimelineKeyframe 的增删 toggle"
            "（DirectorTimeline.tsx:1794-1798），**不选中**。点到就等于把种子里两个关键帧删了。"
            "selectTimelineKeyframe 全项目只有一个调用点：泳道区的 "
            "`<button data-director-keyframe-id>`（:1999）",
            "探针 b：组5 我去点「启用曲线」想打开它 —— **它默认就是 true**，我点完反而关掉了。"
            "同 745/746：静态断言取值前必须先读一次实际值",
            "探针 c：关键帧字段读成 9 条但每条 inputs 都是空 —— 我按「容器含子元素」读，"
            "而 `data-director-motion-keyframe-field` 与 `-keyframe-axis` 挂在**同一个 input** 上"
            "（DirectorCameraMotionTab.tsx:268-269）。**属性是平铺的，不是一棵树**",
            "探针 c：rotation 三轴 disabled 全 false ⟹ 看着像「提示撒谎」。查源码才发现我查的是"
            "`data-director-path-transform-field`（路径检查器专用，:873），带 `disabledAxes` 的是"
            "**通用**的 `data-director-transform-field`（:179 / :2493）。"
            "同 746/747：**找那个有 X 的元素不能按名字找，先确认它在哪个节点上**",
            "探针 c：JS 里 `document.querySelector(...)` 那段报 SyntaxError，重写一次就好；"
            "同一写法在别处能跑通，没查到底因",
            "751a 那一版把 `path-reset` 之后的起点当干净，其实 750 已经立过规矩："
            "**一条链路只问一个问题，问之前必须能从 path-count 读到 0**",
            "**判据自己又错四处**（不是探针、也不是产品）：① C1 写 `len(selectCallSites)==3`"
            "（以为把 `useDirectorStore` 的解构也算进去），实际该正则只命中真调用点 1 处 —— "
            "**数一个模式有几处命中之前，先确认匹配规则本身**；"
            "② C4 把两个中文按钮按语序写成 `[完成, 取消]`，但 `sorted()` 按码位排，"
            "「取」U+53D6 < 「完」U+5B8C ⟹ 正确顺序是 `[取消, 完成]`。"
            "**拿中文字面量写断言时，先想一遍排序规则**；"
            "③ C6 标签只剩一个 `%d` 却传了两个参数，直接 TypeError；"
            "④ C9 第一版拿**本批单链**的在场种数当「750 已覆盖」⟹ 算出 36/52。"
            "追下去才发现：路径检查器面板与运动页签 / 曲线编辑器模式**互斥**，"
            "进运动页签时 `path-anchor-*`/`path-name`/`curve-*` 整块被顶掉。"
            "**「走完还缺 N 种」在没有说明面板互斥的前提下是没有意义的读数** —— "
            "741 立的「一个对不上的数字自己就是线索」第三次生效。"
            "改法：与 750 已提交的审计产物跨批对账，两批并集正好 52。"
            "对账时又抓到一处归属错误：`motion-path-orient` 被 "
            "`selectedTrack?.kind === \"transform\"` 挡着（DirectorInspector.tsx:1169），"
            "750 那条链走的是 camera 轨道所以它从未在 750 出现过，"
            "我第一版只把组5 的「点朝向」那一步算进并集、漏了「建路径」那一步 ⟹ 51/52。"
            "**一种属性该记在哪一步，要看它的守卫条件挂在哪个状态上**",
        ],
        "notClaimed": [
            "只验了 1 条 camera 轨道与 1 条角色轨道的 3 个关键帧时刻（种子每条轨道只有 t=0/4/8）；"
            "关键帧多的时候编辑器行为未测",
            "只把锚点改成了「对称」，没验「非对称」下 in/out 手柄是否独立可编辑",
            "运动页签的「时长」滑杆量程 0–10 仍是 750 之前的存疑项（源站无交互证据），本批未取证",
            "统一缩放量程 0.1–10 step 0.05 是 Batch 583 定的，本批只复读了显示值没有复跑源站",
            "朝向开启后 Y 轴旋转值从 18 变 71.03 —— 具体是哪个算法、按什么规则算出来的未追查",
            "关键帧编辑器的字段提交（autoKeyframe 开/关两态）本批未测",
            "749 残差里其余族（场景 25 / 全景 9 / 分组 8 / 锁定 / 人群 / 手机 vcam 面板）仍未逐族验证",
            "C9 的「750 已覆盖 27 种」是**读 750 已提交的审计产物**算出来的（`stillMissing` 取补集），"
            "不是本批重跑测出来的；两批的探针版本不同，不构成同一实验下的重复测量",
            "未与源站导演台做任何对照（源站关着，需点击授权）",
        ],
    }
    (OUTDIR / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n判据 {npass}/{len(checks)}；两轮一致={idem}")
    for x in checks:
        print(("  ✅ " if x["pass"] else "  ❌ ") + x["label"][:108])
    return 0 if (npass == len(checks) and idem) else 1


if __name__ == "__main__":
    sys.exit(main())
