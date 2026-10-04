#!/usr/bin/env python3
"""batch 750 验收器：运动/路径/曲线三族

749 把 748 的 223 种「有静态无运行时」残差按前缀归成 283 个族，只验了采集图库
（11 种）与姿势（10 种）两族，并明确写了「运动路径/路径锚点族 20+6 种最大，
只从源码守卫表达式推断、无运行时读数」。本批把那三族打开。

判据 11 条。每条都只判「与采样/随机 id 无关」的性质，异步轨迹不进比对。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch750-2026-10-01"
PROBE = "/tmp/dbg750e.py"

# ---------------------------------------------------------------- 静态侧

TARGET_FAMILIES = ("data-director-motion", "data-director-path", "data-director-curve")


def static_side():
    d = ROOT / "src/components/director"
    union, owner, lines = set(), {}, {}
    for f in sorted(d.glob("*.tsx")):
        src = f.read_text(encoding="utf-8")
        for i, l in enumerate(src.split("\n"), 1):
            for m in re.finditer(r"\b(data-[a-z0-9-]+)", l):
                union.add(m.group(1))
                owner.setdefault(m.group(1), []).append(f"{f.name}:{i}")
            for m in re.finditer(r"\.dataset\.([A-Za-z0-9_]+)\s*=", l):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                union.add("data-" + kebab)
                owner.setdefault("data-" + kebab, []).append(f"{f.name}:{i}")
    fam = {n: owner.get(n, []) for n in sorted(union) if n.startswith(TARGET_FAMILIES)}
    # 找关键实现的行号
    store = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    tl = (d / "DirectorTimeline.tsx").read_text(encoding="utf-8")
    mt = (d / "DirectorCameraMotionTab.tsx").read_text(encoding="utf-8")

    def line_of(text, pat, nth=0):
        hits = [i for i, l in enumerate(text.split("\n"), 1) if re.search(pat, l)]
        return hits[nth] if len(hits) > nth else None

    desk = (d / "DirectorDesk.tsx").read_text(encoding="utf-8")
    page_src = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")

    return {
        "unionTotal": len(union),
        "familyNames": sorted(fam),
        "familyCount": len(fam),
        "familyByPrefix": {
            p: len([n for n in fam if n.startswith(p)]) for p in TARGET_FAMILIES},
        "declAndImpl": {
            "createMotionPath": [line_of(store, r"^\s*createMotionPath:"),
                                 line_of(store, r"^\s*createMotionPath: \(preset")],
            "startMotionPathDrawing": line_of(tl, r"startMotionPathDrawing\(tool\)"),
            "appendDraftAnchor": line_of((d / "DirectorViewport.tsx").read_text(encoding="utf-8"),
                                         r"appendMotionPathDraftAnchor\(pointFromEvent"),
            # 铅笔在 pointerup 里收尾：`if (draft.tool === "pencil")` 在文件里出现两次
            # （onPointerMove 一次、onPointerUp 一次），取**第二处**才是收尾那处
            "finishOnPointerUp": line_of((d / "DirectorViewport.tsx").read_text(encoding="utf-8"),
                                         r"if \(draft\.tool === \"pencil\"\)", nth=1),
            # undoDirector 在接口声明里是 `undoDirector: () => DirectorCommandResult;`
            # （也匹配 `\(\)`），实现体是 `undoDirector: () => {` ⟹ 用 `{` 区分
            "undoDirectorDecl": line_of(store, r"^\s*undoDirector: \(\) => Director"),
            "undoDirectorImpl": line_of(store, r"^\s*undoDirector: \(\) => \{"),
            "redoDirectorImpl": line_of(store, r"^\s*redoDirector: \(\) => \{"),
            "deskHotkeyZ": line_of(desk, r'modifier && event\.key\.toLowerCase\(\) === "z"'),
            "deskHotkeyY": line_of(desk, r'modifier && event\.key\.toLowerCase\(\) === "y"'),
            "canvasHotkeyZ": line_of(page_src, r'modifier && event\.key\.toLowerCase\(\) === "z"'),
            "historyWordsInStore": len(re.findall(r"pushHistory|undoStack|redoStack", store)),
        },
        "entryLines": {
            "createMotionPathTrigger": line_of(tl, r"data-director-create-motion-path"),
            "drawTrail": line_of(tl, r"data-director-track-draw-trail"),
            "curveEditorOpen": line_of(tl, r"data-director-open-curve-editor"),
            "trackLabelRoleButton": line_of(tl, r"data-director-track-row=\{track\.id\}"),
            "pathResetIsReset": line_of((d / "DirectorInspector.tsx").read_text(encoding="utf-8"),
                                        r"resetMotionPath\(path\.id\)"),
            "motionPresetButton": line_of(mt, r"data-director-motion-preset-button"),
            "motionCreatePathButton": line_of(mt, r"data-director-motion-create-path"),
        },
        "deadButtonHasNoOnClick": (
            "onClick" not in mt.split("data-director-motion-preset-button")[0].rsplit("<button", 1)[-1]
            and "onClick" not in mt.split("data-director-motion-create-path")[0].rsplit("<button", 1)[-1]),
    }


# ---------------------------------------------------------------- 归一化

def normalize(d):
    """把随机 id / 时间戳 / 浮点尾数归一，只留与采样无关的性质。

    像素差的三件（deadDiff / controlDiff / threshold）也归一掉：WebGL 3D 场景同一
    状态两次渲染就会有零星抖动像素（实测 0 与 4 交替），原始计数不是稳定性质；
    稳定的是**判定**（noChange / controlChanged），那两个布尔留在比对里。
    """
    unstable = {"deadDiff", "controlDiff", "threshold", "orbitDiff", "orbitPct", "pathRenderDiff"}

    def scrub(o):
        if isinstance(o, dict):
            return {k: ("<UNSTABLE>" if k in unstable else scrub(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [scrub(x) for x in o]
        return o

    s = json.dumps(scrub(d), ensure_ascii=False, sort_keys=True)
    s = re.sub(r"-\d{13}", "-<TS>", s)                       # 路径 id 里的时间戳
    s = re.sub(r"\d{13}", "<TS>", s)
    s = re.sub(r"-?\d+\.\d{6,}", "<F>", s)                   # 浮点尾数
    s = re.sub(r"\s+", " ", s)
    return s


def run_probe():
    r = subprocess.run([sys.executable, PROBE], capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"探针失败 exit={r.returncode}")
    return json.loads(pathlib.Path("/tmp/vb750e.json").read_text(encoding="utf-8"))


def build_checks(st, run):
    g = lambda *k: [run.get(k[0], {})] if len(k) == 1 else [run.get(x, {}) for x in k]
    c = []

    def add(label, ok, detail):
        c.append({"label": label, "pass": bool(ok), "detail": detail})

    # C1 静态
    add("C1 静态：运动/路径/曲线三族共 %d 种；createMotionPath 声明与实现各一处；"
        "entryLines 全部可定位；两个 motion 按钮源码里无 onClick"
        % st["familyCount"],
        st["familyCount"] >= 45
        and len(st["declAndImpl"]["createMotionPath"]) == 2
        and all(v is not None for v in st["entryLines"].values())
        and st["deadButtonHasNoOnClick"] is True,
        {"familyByPrefix": st["familyByPrefix"], "entryLines": st["entryLines"],
         "declAndImpl": st["declAndImpl"]})

    # C1b 本批推翻自己的那一条：历史栈的命名
    di = st["declAndImpl"]
    add("C1b **本批自我推翻**：我先 grep `pushHistory|undoStack|redoStack` 在 directorStore 找到 0 处，"
        "就写下「导演台没有历史栈」——查错了标识符族。真实名字是 undoDirector/redoDirector"
        "（声明与实现**行号不同**：接口是 `() => DirectorCommandResult;`、实现是 `() => {`），"
        "快捷键挂在 DirectorDesk 的 window keydown 上；store 里那三个错词确实 0 处",
        di.get("historyWordsInStore") == 0
        and di.get("undoDirectorDecl") is not None and di.get("undoDirectorImpl") is not None
        and di.get("redoDirectorImpl") is not None
        and di.get("undoDirectorDecl") != di.get("undoDirectorImpl")
        and di.get("deskHotkeyZ") is not None and di.get("deskHotkeyY") is not None
        and di.get("canvasHotkeyZ") is not None
        and di.get("deskHotkeyZ") != di.get("canvasHotkeyZ"),
        {k: di.get(k) for k in ["historyWordsInStore", "undoDirectorDecl", "undoDirectorImpl",
                                "redoDirectorImpl", "deskHotkeyZ", "deskHotkeyY", "canvasHotkeyZ"]})

    # C2 运动页签
    m = run.get("motionTab", {})
    add("C2 门=选中机位→相机页签 motion：顶层 6 种（vcam/qr/record/retry/preset-button/create-path）"
        "同时出现；相机页签三值是 属性/运动轨迹NEW/截图",
        m.get("vcam") and m.get("qr") and m.get("record") and m.get("retry")
        and m.get("presetButton") and m.get("createPath")
        and sorted(x["v"] for x in run.get("cameraTabs", [])) == ["captures", "motion", "properties"],
        {"motionTab": {k: v["n"] for k, v in m.items()}, "cameraTabs": run.get("cameraTabs")})

    # C3 死按钮：props + DOM + 行为三重；截图用「orbit 拖动」标定尺子的量程
    d = run.get("deadButtons", {})
    add("C3 两个 motion 按钮的 React props 无 onClick（另三个有）；点完 0 属性增/0 属性减、"
        "path-count 仍 0；像素尺本身有效（拖动视口旋转的 diff > 视口 10%），"
        "而死按钮点击的 diff 落在 0.1% 噪声门内",
        d.get("presetOnClick") is False and d.get("createOnClick") is False
        and d.get("qrOnClick") is True and d.get("recordOnClick") is True
        and d.get("retryOnClick") is True
        and d.get("attrsAdded") == [] and d.get("attrsRemoved") == []
        and d.get("pathCountAfterClicks") == "0"
        and d.get("rulerWorks") is True and d.get("noChange") is True,
        {k: d.get(k) for k in ["presetOnClick", "createOnClick", "qrOnClick", "recordOnClick",
                               "retryOnClick", "attrsAdded", "attrsRemoved",
                               "pathCountAfterClicks", "deadDiff", "orbitPct", "threshold",
                               "rulerWorks", "noChange"]})

    # C4 路径菜单 + 一跳入口
    pm = run.get("pathMenu", {})
    add("C4 路径菜单 176×204：自由绘制 2 工具(pencil/pen) + 3 预设(line/ring/rectangle) 全 enabled；"
        "`data-director-track-draw-trail` 86×24 一次点击即「选中该轨道 + 开菜单」",
        pm.get("width") == 176 and pm.get("height") == 204
        and pm.get("tools") == ["pencil", "pen"]
        and pm.get("presets") == ["line", "ring", "rectangle"]
        and pm.get("allEnabled") is True
        and run.get("drawTrail", {}).get("width") == 86
        and run.get("drawTrail", {}).get("menuOpened") is True
        and run.get("drawTrail", {}).get("trackSelected") == "director-track-camera-main",
        {"menu": {k: pm.get(k) for k in ["width", "height", "tools", "presets", "allEnabled", "text"]},
         "drawTrail": run.get("drawTrail")})

    # C5 轨道选择的真正可点目标
    ts = run.get("trackSelection", {})
    add("C5 轨道行外壳无 onClick；可点目标是行内**没有 data-*** 的 role=button(tabIndex=0)；"
        "点它才真的换选中轨道（外壳点不动）",
        ts.get("outerClickNoop") is True and ts.get("innerSelectsCamera") is True
        and ts.get("outerHasDataMarker") is False
        and ts.get("innerTitle") == "机位01 · 对峙中景 · 机位",
        {k: ts.get(k) for k in ["outerClickNoop", "innerSelectsCamera", "outerHasDataMarker",
                                "innerTitle", "beforeSel", "afterOuter", "afterInner"]})

    # C6 建路径落点
    cp = run.get("createPath", {})
    add("C6 选中 camera 轨道建 line ⟹ 路径 id 含 director-camera-main、名字「机位自动帧轨迹」、2 个锚点；"
        "sr-only 层 count 0→1 且盒子 1×1，锚点盒子 0 宽",
        cp.get("pathCountBefore") == "0" and cp.get("pathCountAfter") == "1"
        and "director-camera-main" in (cp.get("pathId") or "")
        and cp.get("pathName") == "机位自动帧轨迹" and cp.get("anchorCount") == 2
        and cp.get("layerBox") == {"w": 1, "h": 1} and cp.get("anchorBoxWidth") == 0,
        {k: cp.get(k) for k in ["pathCountBefore", "pathCountAfter", "pathId", "pathName",
                                "anchorCount", "layerBox", "anchorBoxWidth", "familyOpened"]})

    # C7 两种工具的不同手势
    pc, pn = run.get("pencilDrag", {}), run.get("penClick", {})
    add("C7 铅笔=拖拽：pointerdown 播种 + 8 次 move 追加 + pointerup 立刻完成 ⟹ 9 锚点「铅笔路径1」；"
        "钢笔=逐点点击：3 次点击后面板仍在，点「完成钢笔路径」才落地 3 锚点",
        pc.get("gesture") == "drag" and pc.get("anchorCount") == 9
        and pc.get("pathName") == "铅笔路径1"
        and pc.get("panelOpenDuringDrag") is True
        and pn.get("gesture") == "click" and pn.get("countDuringDraft") == "0"
        and pn.get("anchorCount") == 3 and pn.get("panelStillOpenAfterClicks") is True,
        {"pencil": {k: pc.get(k) for k in ["gesture", "anchorCount", "pathName",
                                           "panelOpenDuringDrag", "pathPreset"]},
         "pen": {k: pn.get(k) for k in ["gesture", "countDuringDraft", "anchorCount",
                                        "panelStillOpenAfterClicks", "pathName"]}})

    # C8 reset ≠ delete
    r8 = run.get("resetSemantics", {})
    add("C8 `data-director-path-reset` 走的是 resetMotionPath（重置锚点）不是删除 ⟹ 点完 path-count 与锚点数都不变",
        r8.get("countBefore") == "1" and r8.get("countAfterReset") == "1"
        and r8.get("anchorCountBefore") == r8.get("anchorCountAfterReset")
        and st["entryLines"]["pathResetIsReset"] is not None,
        dict(r8, resetHandlerLine=st["entryLines"]["pathResetIsReset"]))

    # C9 曲线编辑器
    ce = run.get("curveEditor", {})
    want6 = sorted(["data-director-curve-editor", "data-director-curve-track-id",
                    "data-director-curve-preset", "data-director-curve-values",
                    "data-director-curve-handle", "data-director-curve-locked"])
    add("C9 曲线编辑器是**另一个 editorMode**：入口 data-director-open-curve-editor ⟹ "
        "timeline-mode timeline→curve ⟹ 曲线族 6 种齐现，且有「返回时间线」按钮",
        ce.get("modeBefore") == "timeline" and ce.get("modeAfter") == "curve"
        and ce.get("editorModeAttr") == "curve"
        and sorted(ce.get("familyOpened", [])) == want6
        and ce.get("hasBackButton") is True and ce.get("backButtonLabel") == "返回时间线",
        {k: ce.get(k) for k in ["modeBefore", "modeAfter", "editorModeAttr", "familyOpened",
                                "hasBackButton", "backButtonLabel"]})

    # C10 键盘死路
    kb = run.get("keyboard", {})
    add("C10 轨道名那个 role=button **可聚焦**（activeElement 就是它）但 Enter 与 Space 都不改选中态 "
        "⟹ 焦点能停在这、键盘却用不了",
        kb.get("focused") is True and kb.get("isDivRoleButton") is True
        and kb.get("tabIndex") == "0"
        and kb.get("selectedAfterEnter") == kb.get("selectedBefore")
        and kb.get("selectedAfterSpace") == kb.get("selectedBefore")
        and kb.get("hasOnKeyDown") is False,
        {k: kb.get(k) for k in ["focused", "isDivRoleButton", "tabIndex", "title", "selectedBefore",
                                "selectedAfterEnter", "selectedAfterSpace", "hasOnKeyDown"]})

    # C11 残差增量
    rr = run.get("residue", {})
    add("C11 三族残差：起点 N 种 ⟹ 走完整条链（选 camera 轨道 → 建 line → 开曲线编辑器）后 M 种，"
        "本批打开 O 种 = M−N；静态三族共 P 种，仍缺 Q 种",
        rr.get("familyBefore") is not None and rr.get("familyAfter") is not None
        and rr.get("familyAfter", 0) - rr.get("familyBefore", 0) == rr.get("opened")
        and len(run.get("staticUnionOfThreeFamilies", [])) == st["familyCount"],
        {k: rr.get(k) for k in ["familyBefore", "familyAfter", "opened"]}
        | {"staticFamilyCount": st["familyCount"],
           "stillMissingCount": len(rr.get("stillMissing") or [])})

    # C12 撤销/重做：本批最重要的一次自我推翻
    ur = run.get("undoRedo", {})
    ui = run.get("undoRedoUi", {})
    add("C12 导演台撤销/重做**功能完整但只有键盘**：Cmd+Z 1→0、Cmd+Shift+Z 0→1 往返可复原"
        "（名字与锚点数逐项相同）、重做栈空时 Cmd+Shift+Z / Cmd+Y 无操作、连按两次 Cmd+Z 第二次无操作；"
        "但 151 个可交互节点里 **0 个** 是撤销/重做入口（文本/title/aria-label/属性全 0）",
        ur.get("A_control_noKey", {}).get("counts") == ["1"]
        and ur.get("B_cmdZ", {}).get("counts") == ["1", "0"]
        and ur.get("C_cmdShiftZ", {}).get("counts") == ["1", "1"]
        and ur.get("D_cmdZ_then_cmdShiftZ", {}).get("counts") == ["1", "0", "1"]
        and ur.get("D_cmdZ_then_cmdShiftZ", {}).get("names", [None, None, None])[2]
        == ur.get("D_cmdZ_then_cmdShiftZ", {}).get("names", [None, None, None])[0]
        and ur.get("E_cmdY", {}).get("counts") == ["1", "1"]
        and ur.get("F_cmdZ_twice", {}).get("counts") == ["1", "0", "0"]
        and ui.get("hits") == [] and ui.get("undoAttr") == 0 and ui.get("totalNodes", 0) > 100,
        {"counts": {k: v.get("counts") for k, v in ur.items()},
         "roundTripNames": ur.get("D_cmdZ_then_cmdShiftZ", {}).get("names"),
         "ui": ui})

    return c


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    st = static_side()
    print("静态：并集 %d 种；目标三族 %d 种（%s）" % (
        st["unionTotal"], st["familyCount"], st["familyByPrefix"]))
    print("两轮跑探针……")
    r1 = run_probe()
    r2 = run_probe()
    n1, n2 = normalize(r1), normalize(r2)
    idem = n1 == n2
    if not idem:
        import difflib
        d = list(difflib.unified_diff(n1.split(", "), n2.split(", "), lineterm="", n=1))
        print("两轮不一致，前 40 处差异：")
        print("\n".join(d[:40]))

    checks = build_checks(st, r1)
    npass = sum(1 for x in checks if x["pass"])
    report = {
        "batch": 750,
        "title": "运动/路径/曲线三族：把 749 只从源码推断的残差打开",
        "verdict": f"{npass}/{len(checks)}",
        "twoRoundsIdentical": idem,
        "static": st,
        "run": r1,
        "checks": checks,
        "probeCorrections": [
            "探针 a：REACT_PROPS 用 Object.keys().find 前缀匹配，但 __reactFiber$ 排在 "
            "__reactProps$ 前面 ⟹ 命中 fiber，「有没有 onClick」根本没读出来（b 修正）",
            "探针 a：SVG 探针取 document.querySelector('svg') = 第一个 svg（一个 22×14 图标），"
            "而运动轨迹是 react-three-fiber 的 <Line>，不是 SVG ⟹ 那条读数整条作废，"
            "改用视口截图像素对账",
            "探针 a：读 window.__libtv_director 取 store —— 导演台 store 根本没挂 window"
            "（与画布的 __libtv_store 不同）⟹ motionPaths=null 是「没读到」不是「没有」，"
            "差点当成结论；改为一律经 DOM 读",
            "探针 a：基线本来就选中了一条 transform 轨道 ⟹「选轨道带出 0 种」不构成门的证据",
            "探针 b：DUMP 返回 dict，我按 set 用 ⟹ TypeError",
            "探针 b：把 data-director-path-reset 当成「清空路径」，它其实是 resetMotionPath（重置锚点）"
            "⟹ 第二个问题起点已经有 1 条路径，三个问题全部作废（c 改一问一刷新）",
            "探针 c：点 [data-director-track-row] 外壳建路径「落到角色身上」——撤回，"
            "外壳源码里就没有 onClick（DirectorTimeline.tsx:1708-1726），"
            "可点目标是行内一个没有任何 data-* 标记的 role=button（:1751-1756）；"
            "tracksAfter 里 camera 仍 selected=false 本来就说明我没点上",
            "探针 c：「铅笔第一次点视口就死」——撤回。铅笔是拖拽工具"
            "（DirectorViewport.tsx:1678-1711 down 播种 → move 追加 → up 立刻 finish），"
            "我用无移动的 mouse.click 测它 ⟹ 工具本来就该结束。"
            "工具的交互模型不同，不能用同一种手势测两个工具",
            "探针 c：c4 里给 pivot 数值框 fill+Enter 没提交上 ⟹ 那半个读数作废（reset≠delete 那半仍成立）",
            "**判据自己也有三个 bug**（不是探针）：① `ce.get('familyOpened',[]).sort() == sorted([...])` —— "
            "list.sort() 返回 None，恒不等 ⟹ C9 假失败；② C11 把差值写成 "
            "`familyBefore - familyAfter == opened`，符号反了，正确是 `familyAfter - familyBefore`；"
            "③ C8 判据要的 `resetHandler` 键探针根本没采（C8 的实质读数 count 1→1 本来就对）",
            "**PNG 字节相同不是稳定判据**：第一轮两轮比对里同一画面两次渲染的 PNG 长度 72787 vs 72788，"
            "差 1 字节就判「不一致」。改用 PIL 像素级比对",
            "**「像素必须为 0」同样不是稳定判据**：WebGL 3D 场景同一状态两次渲染抖动 0 与 4 个像素交替"
            "（0.00021%）",
            "**用「建路径」当阳性对照也失败**：它只有 ~212 像素的变化（视口 0.0112%），"
            "在 WebGL 合成下时灵时不灵（同一序列一次读到 212、一次读到 0）⟹ 小信号不能当标尺。"
            "第三版改用**拖动视口旋转**（OrbitControls）当标尺：稳定 839034 像素 / 44.26%，"
            "判据只断言「尺子有效（>视口 10%）+ 死按钮点击落在 0.1% 门内」；"
            "建路径的像素差只作记录，不进判据",
            "顺带查清：元素截图与整页裁剪在视口区域只差 5 个像素 ⟹ 元素截图**能**拍到 WebGL，"
            "不是截图工具的锅（「先怀疑探针」这条规矩第二次生效）",
            "探针自己第三轮又踩一次顺序错：`pathCountAfterClicks` 是在建完路径之后才读的，"
            "读到 1 ⟹ C3 假失败。**探针里每个读数都要问「这一刻之前我动过什么」**",
            "**我自己的结论「导演台没有历史栈」被运行时推翻**：grep `pushHistory|undoStack|redoStack` "
            "得 0 处就下了结论，而真实名字是 undoDirector/redoDirector；"
            "Cmd+Z 实测把刚建的路径删掉。规矩：断言「某能力不存在」前先穷举它的全部命名形态",
        ],
        "notClaimed": [
            "除本批打开的三族外，749 的其余残差族（场景/全景/分组/锁定/人群/手机 vcam 面板等）仍未逐族验证",
            "运动轨迹在 3D 场景里的可见渲染只用像素差**间接**证明：同一机位下建一条矩形路径，"
            "视口差约 212 像素（0.0112%）⟹ 确实画了，但占视口不到万分之一；"
            "该差值在 WebGL 合成下时灵时不灵（读到过 212 也读到过 0），"
            "所以只作记录不进判据。没有做像素级定位，也没验证线的颜色/粗细/选中态配色",
            "sr-only 层无条件渲染全部路径、3D 层只画 enabled 的（DirectorViewport.tsx:1582-1583 filter）"
            "——这处不一致是源码读数，本批没有构造「禁用路径 + 读屏」的场景来实测",
            "「role=button 没有键盘通路」只验了轨道名这一个；导演台其他 role=button 未普查",
            "撤销/重做只验了运动路径这一条命令的往返；导演台其他命令的撤销粒度（是否原子）未测",
            "Cmd+Z 走的是 DirectorDesk 的 window keydown（:506-516），与画布 page.tsx:1342 的 "
            "undo() 是两套；两者在导演台打开时是否互相抢键（谁先 preventDefault）本批未测",
            "pencil 拖拽只跑了一次 8 步直线拖动，锚点采样密度与真实手绘的差异未测",
            "pen 的 3 次点击用的是固定屏幕坐标，锚点世界坐标随之确定；没有验证锚点是否落在绘制平面上",
            "未与源站导演台做任何对照（源站关着，需点击授权）",
        ],
    }
    (OUTDIR / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n判据 {npass}/{len(checks)}；两轮一致={idem}")
    for x in checks:
        print(("  ✅ " if x["pass"] else "  ❌ ") + x["label"][:110])
    return 0 if (npass == len(checks) and idem) else 1


if __name__ == "__main__":
    sys.exit(main())
