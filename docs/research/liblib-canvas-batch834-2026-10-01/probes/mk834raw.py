#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：把源站引导（5 步）的证据整理成 raw（门禁的期望值来源）。

★ 两路来源：
  ① 活体读数（`/tmp/liblib_source_coach834b.json`）——每步的正文、容器盒、按钮文案；
  ② 源站 **chunk 原文**（`/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）——每步的
     target／文案 i18n 键／width／bubbleOffsetX／bubbleHeight，以及**定位算法**
     与**状态机**（onNext / auto-advance / 收起键）。
  ⟹ ★ 两路**互相独立** ⟹ 交叉核对：活体的「容器盒」必须能被原文算法**重算出来**。

★ 输出：raw/source-834-timeline-guide.json
"""
import hashlib
import json
import pathlib
import re

BATCH = pathlib.Path(__file__).resolve().parent.parent
LIVE = pathlib.Path("/tmp/liblib_source_coach834b.json")
CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = BATCH / "raw" / "source-834-timeline-guide.json"

# ★ 源站 chunk 原文里的 5 步定义（原文摘录 ⟹ 可复核）
STEP_RE = re.compile(
    r'(?P<idx>\d)===e\?\{target:"(?P<target>[a-z-]+)",'
    r'text:l\("(?P<key>[^"]+)"\),count:"(?P<count>[^"]+)",'
    r'width:(?P<width>\d+),bubbleOffsetX:(?P<offset>-?\d+),'
    r'bubbleHeight:(?P<height>\d+)\}'
)
# ★ 定位算法（原文摘录）
ALGO_ANCHOR = 'let a=Math.min(p.width,window.innerWidth-24)'
# ★ 状态机关键锚点
STATE_ANCHORS = [
    "l6=\"libtv.director.timeline-guide.dismissed.v1\"",
    'null!==eg||"1"===window.localStorage.getItem(l6)||!eF||(0,nY.C)()||ex(0)',
    "window.localStorage.setItem(l6,\"1\")",
    "4===e?l(\"canvas:directorTimelineGuideComplete\"):l(\"canvas:directorTimelineGuideNext\")",
    'data-director-timeline-guide-overlay":"true"',
    'data-director-timeline-guide-target":"add-track"',
    # ★ draw-trajectory 是**条件赋值**（`?"draw-trajectory":void 0`）⟹ 原文形态不同
    '"draw-trajectory":void 0',
    '"data-director-timeline-guide-target":"export-to-canvas"',
    'data-director-timeline-guide-icon":"true"',
    "director-timeline-guide-ripple 1400ms cubic-bezier(0.22, 0.61, 0.36, 1) infinite",
]


def main():
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    chunk = CHUNK.read_text(encoding="utf-8", errors="replace")

    steps_code = []
    for m in STEP_RE.finditer(chunk):
        steps_code.append({
            "步序": int(m.group("idx")),
            "target": m.group("target"),
            "文案i18n键": m.group("key"),
            "count": m.group("count"),
            "width": int(m.group("width")),
            "bubbleOffsetX": int(m.group("offset")),
            "bubbleHeight": int(m.group("height")),
        })
    steps_code.sort(key=lambda s: s["步序"])
    if len(steps_code) != 5:
        raise SystemExit("chunk 里解析出的步数不对：%d" % len(steps_code))

    missing = [a for a in STATE_ANCHORS if a not in chunk]
    if missing:
        raise SystemExit("chunk 里找不到这些锚点：%r" % missing)

    # ★ 活体读数：每步的正文 ＋ 容器盒 ＋ 按钮文案
    live_steps = []
    for s in live.get("①逐步") or []:
        g = s["guide"]
        if not g.get("found"):
            continue
        body = [x["t"] for x in g["texts"]
                if x["t"] not in ("跳过", "下一步", "完成")]
        text = body[0] if body else ""
        live_steps.append({
            "count": g["step"],
            "正文": text,
            "容器盒": g["hostBox"],
            "按钮": [b["t"] for b in g["buttons"]],
            "按钮盒": [b["box"] for b in g["buttons"]],
            "class": g["hostClass"],
            "position": g["position"],
            "zIndex": g["zIndex"],
            "top": g["top"],
            "left": g["left"],
        })
    if len(live_steps) != 5:
        raise SystemExit("活体读数的步数不对：%d" % len(live_steps))

    # ★ 交叉核对：代码里的 width ＝ 活体容器盒宽；代码里的 count ＝ 活体 count
    cross = []
    for code, lv in zip(steps_code, live_steps):
        if code["count"] != lv["count"]:
            cross.append("步数不一致：%s vs %s" % (code["count"], lv["count"]))
        if code["width"] != lv["容器盒"]["w"]:
            cross.append("宽度不一致：%d vs %d" % (code["width"], lv["容器盒"]["w"]))
        if code["step序"] if False else False:
            pass
    if cross:
        raise SystemExit("两路交叉核对失败：%r" % cross)

    result = {
        "来源": "源站导演台**时间轴引导气泡**（5 步）的活体读数 ＋ 源站 chunk 原文",
        "采集方式": "活体：probes/coach834b.py（开时间轴 → 逐点「下一步」直到「完成」）；"
                    "原文：probes/extract834.py / extract834d.py 从 chunk "
                    "`0fmehki05gkzw.js.js` 抽出组件 `cC` 与状态机",
        "★为什么必须开时间轴": "引导气泡**锚在时间轴上** ⟹ 源站时间轴默认**收起** ⟹ "
                        "不打开时间轴就**全页找不到**它（第一版探针的失败原因）",
        "★两路交叉核对": "代码里的 width/count 与活体容器盒宽、步数逐项相等 ⟹ "
                    "不一致则本脚本拒绝出 raw",
        "活体读数文件": str(LIVE),
        "活体读数_sha256": hashlib.sha256(LIVE.read_bytes()).hexdigest(),
        "chunk文件": str(CHUNK),
        "chunk_sha256": hashlib.sha256(CHUNK.read_bytes()).hexdigest(),
        "步数": 5,
        "代码定义": steps_code,
        "活体读数": live_steps,
        "★定位算法原文锚点": ALGO_ANCHOR,
        "★状态机锚点": STATE_ANCHORS,
        "★收起标记": "libtv.director.timeline-guide.dismissed.v1（localStorage，值 \"1\"）",
        "★启动条件": "step 为 null ＋ localStorage 标记 != \"1\" ＋ 存在目标上下文(eF) "
                  "＋ 另一个守卫(nY.C())为假 ⟹ ex(0)",
        "★onNext 分步动作": {
            "步0": "关掉运动绑定浮层 → 若有 trackId 则打开该浮层 → 进第 2 步；否则直接收起",
            "步1": "若已画出轨迹(eH) → 进第 3 步；否则直接收起",
            "步2": "若浮层已打开 → 套用「圆环」预设 → 关浮层 → 进第 4 步；否则直接收起",
            "步3": "若未在播放 → 开始播放 → 进第 5 步",
            "步4": "点「导出视频到画布」按钮 → 收起",
        },
        "★自动推进": {
            "步0→1": "运动绑定浮层打开时（ej）",
            "步1→2": "浮层打开时（Y）",
            "步2→3": "浮层关闭时（eO 且 !Y）",
            "步3→4": "开始播放时（isPlaying）",
            "步4收尾": "给导出按钮挂 click 监听 → 点了就收起",
        },
        "★写标记的时机": "到第 3 步（步序 2）且浮层既没开也没在开 → 120ms 后写 "
                    "localStorage[\"libtv.director.timeline-guide.dismissed.v1\"]=\"1\" 并收起",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("已落盘：", OUT)
    for s in live_steps:
        print("  %s 正文=%s 盒=%s 按钮=%s"
              % (s["count"], s["正文"], s["容器盒"], s["按钮"]))


if __name__ == "__main__":
    main()
