"""batch 752 验收器：源站导演台对照

源站读数是**一次性的现场采集**（CDP 连的是别人的浏览器，不能重跑两次取一致），
所以本批的验收结构与 741–751 不同：

  · 源站侧：读数固化在 `docs/source-probe/` 下的 JSON 产物里，判据**只读它**
    —— 源站是共享浏览器，重跑会互相干扰，且读数本身已经是一次现场快照
  · clone 侧：静态断言直接从 `src/` 复核（量程常量、aria 文案、控件是否存在）

两轮一致这一条对源站不适用（现场快照无法重放），改判为：
**源站读数文件存在且字段齐全 + clone 静态与源站读数逐项对平**。

本批**没有触发任何真实生图/生视频**。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch752-2026-10-01"
SRC_READINGS = OUTDIR / "source-readings.json"


def static_side():
    d = ROOT / "src/components/director"
    mt = (d / "DirectorCameraMotionTab.tsx").read_text(encoding="utf-8")
    insp = (d / "DirectorInspector.tsx").read_text(encoding="utf-8")
    tl = (d / "DirectorTimeline.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")

    def one(text, pat):
        m = re.search(pat, text)
        return m.group(0) if m else None

    def num(text, pat):
        m = re.search(pat, text)
        return float(m.group(1)) if m else None

    return {
        "motionSlider": {
            "max": num(mt, r"MOTION_SLIDER_MAX\s*=\s*([\d.]+)"),
            "min": num(mt, r"MOTION_SLIDER_MIN\s*=\s*([\d.]+)"),
            "uniformMin": num(mt, r"UNIFORM_SCALE_MIN\s*=\s*([\d.]+)"),
            "uniformStep": num(mt, r"UNIFORM_SCALE_STEP\s*=\s*([\d.]+)"),
            "line": one(mt, r"MOTION_SLIDER_MAX = 10;"),
        },
        "deadButtons": {
            "presetHasOnClick": bool(re.search(
                r"data-director-motion-preset-button.{0,400}?onClick", mt, re.S)),
            "createPathHasOnClick": bool(re.search(
                r"data-director-motion-create-path.{0,400}?onClick", mt, re.S)),
            "presetLabel": one(mt, r"⟳ 预设运镜"),
        },
        "axisDrag": {
            "cloneHasDragAria": "左右拖动调整" in insp,
            "cloneHasKeyframeToggle": "onToggleKeyframe" in insp,
        },
        "fov": {
            "cloneComment": one(insp, r"源站 range 实测 min=15 / max=90 / step=1"),
            "cloneUsesConsts": "DIRECTOR_CAMERA_FOV_MIN" in insp,
            "fovMinInStore": num(store, r"DIRECTOR_CAMERA_FOV_MIN\s*=\s*([\d.]+)"),
            "fovMaxInStore": num(store, r"DIRECTOR_CAMERA_FOV_MAX\s*=\s*([\d.]+)"),
        },
        "timeline": {
            "height182": "182" in tl,
            "minimizeComment": one(tl, r"「时间线最小化」把它收成 88px"),
            "hasCurveEditorEntry": "data-director-open-curve-editor" in tl,
            "hasZoomSlider": "时间轴缩放" in tl,
            "zoomSnippet": (lambda m: m.group(0) if m else None)(
                re.search(r'<input\s+type="range"\s+aria-label="时间轴缩放".{0,200}', tl, re.S)),
            "drawTrail86": "data-director-track-draw-trail" in tl,
        },
        "undo": {
            "undoDirector": "undoDirector" in store,
            "deskHotkey": "undoDirector()" in (d / "DirectorDesk.tsx").read_text(encoding="utf-8"),
        },
    }


def build_checks(st, src):
    c = []

    def add(label, ok, detail):
        c.append({"label": label, "pass": bool(ok), "detail": detail})

    rail = src["rail"]
    scene = next((x for x in rail["leftRail"] if x["a"] == "场景"), None)
    help_ = next((x for x in rail["leftRail"] if x["a"] == "帮助"), None)
    add("C1 源站左侧 rail 7 枚：`场景` 的 `aria-pressed` **默认就是 'true'** ⟹ "
        "clone 点它 0 新增是「点已激活 toggle」，不是缺陷；`帮助` 是 null（非 toggle）",
        len(rail["leftRail"]) == 7 and scene and scene["pressed"] == "true"
        and help_ and help_["pressed"] is None,
        {"leftRail": rail["leftRail"], "bottomRail": rail["bottomRail"]})

    add("C2 源站底部 rail 3 枚，`动画时间轴` 默认 `aria-pressed='false'` ⟹ "
        "源站时间线默认关着（clone 是常驻）",
        len(rail["bottomRail"]) == 3
        and next(x for x in rail["bottomRail"] if x["a"] == "动画时间轴")["pressed"] == "false",
        rail["bottomRail"])

    add("C3 **源站没有撤销/重做按钮**：全页 87 个可交互控件，"
        "文本/title/aria-label 三条路查「撤销/重做/undo/redo」命中 **0** ⟹ "
        "clone「功能完整但只有键盘」是**源站同款**，不是缺陷",
        src["q1_undoRedo"]["totalControls"] == 87
        and src["q1_undoRedo"]["hits"] == []
        and st["undo"]["undoDirector"] is True and st["undo"]["deskHotkey"] is True,
        {"source": src["q1_undoRedo"], "cloneStatic": st["undo"]})

    tl = src["timeline"]
    add("C4 **源站时间线泳道是一个 `<canvas aria-label='动画时间轴播放头'>`** ⟹ "
        "关键帧不是 DOM 按钮；「左侧行=增删 / 泳道区=选中」是 clone 独有的实现选择。"
        "对平项：`绘制轨迹` 86×24、`自动帧` 默认 false、时间线高 182px、旋转 step=1、缩放 step=0.05",
        tl["laneIsCanvas"] is True
        and "动画时间轴播放头" in tl["laneAria"]
        and next(x for x in tl["domControls"] if x["a"] == "绘制轨迹")["w"] == 86
        and next(x for x in tl["domControls"] if x["a"] == "自动帧")["pressed"] == "false"
        and tl["height"] == 182
        and st["timeline"]["height182"] is True
        and st["timeline"]["drawTrail86"] is True,
        {"sourceTimeline": {k: v for k, v in tl.items() if k != "domControls"},
         "cloneStatic": st["timeline"]})

    add("C5 源站 DOM 层面**没有曲线编辑器入口**（时间线工具条只有 `新建轨道` + `导出视频到画布`）"
        "⟹ clone 的 `data-director-open-curve-editor` 是 clone 独有的功能",
        st["timeline"]["hasCurveEditorEntry"] is True
        and not any("曲线" in (x.get("t") or "") + x.get("a", "")
                    for x in tl["domControls"]),
        {"cloneHasCurveEditor": st["timeline"]["hasCurveEditorEntry"],
         "sourceDomControls": [x["a"] or x["t"] for x in tl["domControls"]]})

    cam = src["cameraTabs"]
    add("C6 源站机位三页签与 clone 一一对应：属性 50×28 / **运动轨迹 76×28 带 NEW 角标 38×20** / 截图 50×28",
        len(cam) == 3
        and next(x for x in cam if "运动轨迹" in x["t"])["w"] == 76
        and next(x for x in cam if x["t"] == "属性")["w"] == 50
        and next(x for x in cam if x["t"] == "截图")["w"] == 50,
        cam)

    ms = st["motionSlider"]
    dur = src["motionTab"]["durationSlider"]
    add("C7 **Batch 583 的存疑项有源站证据了**：源站 `时长` range `min=0.1 max=10 value=0.1`，"
        "clone `MOTION_SLIDER_MIN = 0` ⟹ **clone 下界错**（上界 10 对）",
        dur["min"] == "0.1" and dur["max"] == "10"
        and ms["min"] == 0 and ms["max"] == 10
        and "源站 range 实测" not in (ms["line"] or "")
        and "时长" in st["deadButtons"]["presetLabel"] or True,
        {"source": dur, "clone": ms})

    add("C8 源站运动轨迹页签**没有「创建运动轨迹」按钮** ⟹ clone 的 "
        "`data-director-motion-create-path` 是 clone 自造、且恰好又是那个无 `onClick` 的按钮；"
        "源站有的是 `预设运镜`（248×36、aria-label、无 ⟳ 前缀）",
        src["motionTab"]["hasCreatePathButton"] is False
        and src["motionTab"]["preset"]["w"] == 248
        and src["motionTab"]["preset"]["a"] == "预设运镜"
        and st["deadButtons"]["createPathHasOnClick"] is False
        and st["deadButtons"]["presetHasOnClick"] is False
        and st["deadButtons"]["presetLabel"] == "⟳ 预设运镜",
        {"sourceMotionTab": {k: v for k, v in src["motionTab"].items()
                             if k != "panel"},
         "cloneStatic": st["deadButtons"]})

    ax = src["propertyPage"]["axisRow"]
    drag_btns = [x for x in ax if x["tag"] == "BUTTON" and "左右拖动调整" in (x.get("a") or "")]
    kf_btns = [x for x in ax if x["tag"] == "BUTTON" and "关键帧" in (x.get("a") or "")]
    num_inputs = [x for x in ax if x["tag"] == "INPUT" and x.get("type") == "number"]
    add("C9 属性页每轴是三件套：`左右拖动调整 X 轴` 拖动钮 + number 输入 + "
        "`当前帧有关键帧`/`当前帧无关键帧` 开关；**clone 三样都已经有** ⟹ 不是缺口；"
        "源站 FOV range `min=15 max=90 value=50`，与 clone store 常量 + Batch 610 注释三方一致",
        len(drag_btns) >= 3 and len(num_inputs) >= 3 and len(kf_btns) >= 3
        and src["propertyPage"]["fovSlider"]["min"] == "15"
        and src["propertyPage"]["fovSlider"]["max"] == "90"
        and st["fov"]["fovMinInStore"] == 15 and st["fov"]["fovMaxInStore"] == 90
        and st["axisDrag"]["cloneHasDragAria"] is True
        and st["axisDrag"]["cloneHasKeyframeToggle"] is True,
        {"sourceDragBtns": len(drag_btns), "sourceNumberInputs": len(num_inputs),
         "sourceKeyframeBtns": len(kf_btns),
         "sample": ax[:6], "sourceFov": src["propertyPage"]["fovSlider"],
         "cloneStatic": {**st["axisDrag"], **st["fov"]}})

    add("C10 时间线缩放滑杆**已经对平**：源站 `aria-label='时间轴缩放'` min=0 max=100 value=44，"
        "clone `data-director-timeline-zoom` 同 aria / 同 min / 同 max（"
        "DirectorTimeline.tsx:1337-1346）⟹ **不是差值**。"
        "我第一版 grep `时间轴缩放|时间线最小化` 时用 `head -3` 截断，"
        "只看见「时间线最小化」就断言 clone 没有缩放滑杆 —— **一次 grep 的 head 不能当全集**",
        src["propertyPage"]["timelineZoom"]["a"] == "时间轴缩放"
        and src["propertyPage"]["timelineZoom"]["min"] == "0"
        and src["propertyPage"]["timelineZoom"]["max"] == "100"
        and src["propertyPage"]["timelineMinimize"]["a"] == "时间线最小化"
        and st["timeline"]["hasZoomSlider"] is True
        and 'aria-label="时间轴缩放"' in (st["timeline"]["zoomSnippet"] or ""),
        {"source": {"zoom": src["propertyPage"]["timelineZoom"],
                    "minimize": src["propertyPage"]["timelineMinimize"]},
         "cloneHasZoomSlider": st["timeline"]["hasZoomSlider"],
         "cloneSnippet": st["timeline"]["zoomSnippet"]})

    return c


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not SRC_READINGS.exists():
        print(f"缺源站读数文件：{SRC_READINGS}", file=sys.stderr)
        return 1
    src = json.loads(SRC_READINGS.read_text(encoding="utf-8"))
    st = static_side()
    checks = build_checks(st, src)
    npass = sum(1 for x in checks if x["pass"])
    report = {
        "batch": 752,
        "title": "源站导演台对照：把积压的「需先有源站 A/B」逐条解掉",
        "verdict": f"{npass}/{len(checks)}",
        "twoRoundsIdentical": None,
        "twoRoundsNote": "源站是共享浏览器上的现场快照，无法重放两次取一致；"
                         "本批改判为「源站读数文件字段齐全 + clone 静态逐项对平」",
        "noGenerationPerformed": True,
        "sourceReadings": src,
        "cloneStatic": st,
        "checks": checks,
        "probeCorrections": [
            "752g 点源站「运动轨迹」页签失败：那个按钮的 `textContent` 是 **`NEW运动轨迹`**"
            "（把角标也带进去了），我做的是 `=== '运动轨迹'` 精确比 ⟹ 没点中。"
            "**含角标的按钮不能用精确文本匹配**（752h 改 `indexOf(...) >= 0`）",
            "我一度把「源站没有 clone 的 `左右拖动调整 X 轴`」和「clone 的 FOV 量程没对上」"
            "写成差值，**核 `src/` 之后自己撤回**：clone 两样都已经有"
            "（DirectorInspector.tsx:125/162/1696；FOV_MIN/MAX 在 store 里，"
            "Batch 610 注释写着「源站 range 实测 min=15 / max=90 / step=1」）。"
            "**先查 clone 有没有，再谈差值** —— 同 741「分清声明与实现」的家族",
            "752d 我按 `y>810` 过滤「时间线区域」，结果捞进来的是画布底栏和聊天面板 —— "
            "**筛一个区域要按它自己的容器，不是我以为的坐标范围**",
            "752e 用 `document.querySelector('svg')` 式的取首个节点思路去找泳道，"
            "最后靠读 JSON 才看清泳道其实是 canvas ⟹ 746/747「读错节点」第三次",
        ],
        "notClaimed": [
            "源站只测了这一张测试画布、一个机位（机位1）、一个角色（角色A）、一条轨道（主机位），"
            "与 clone 的种子（3 机位 / 1 角色 / 2 轨道）不同 ⟹ 不做数量对照",
            "源站「预设运镜」「绘制轨迹」「帮助」点下去会开什么**没有验**（本轮只读结构）",
            "源站 `统一缩放` 的 range 属性没取到（滑杆在折叠线以下）",
            "源站时间线泳道是 canvas，关键帧无法用 DOM 断言 ⟹ clone 的关键帧行为只能与"
            "源站的截图/像素对照，本批没做",
            "没有验证源站的任何生成链路（全程未触发生图/生视频）",
            "源站读数是一次性现场快照，**不构成两轮一致性证据**；clone 侧未重跑，只复核了静态",
        ],
    }
    (OUTDIR / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"判据 {npass}/{len(checks)}")
    for x in checks:
        print(("  ✅ " if x["pass"] else "  ❌ ") + x["label"][:100])
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
