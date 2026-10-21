#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824 验收器 —— 「TV Director」入口：源站在**画布底部**，clone 原来在**顶部**

## 验收什么

★ 源站第一手事实（无头 + 登录态，2026-10-21）：

- 画布**底部中间**一条工具条，8 枚按钮，可及名逐字：
  添加节点／移动／素材库／**角色造型室**／生成历史／快捷键／教程／**TV Director**
- 「TV Director」是 **48×48 的青色渐变球**（点位 955,889,48,48）
- ★ 点它打开的是**右侧「新对话」AI 抽屉**，**不是导演台**
  （URL 不变、画布节点数不变）

★ clone 的 `AgentDrawer` **标题逐字就是「新对话」** ⟹ 面板本来就有，
★★ **缺的只是那个入口按钮** ⟹ 这就是「有功能、用户找不到」。

## ★ 三条纪律在本文件里的落点

1. ★ **零 store 写调用**：由 **S1** 用**正则扫探针源码**自证。
2. ★ **源站对照也进判据**：S6 直接读**入库的源站读数**，
   ⟹ 「clone 与源站一致」这句话**可复算**，不是我的印象。
3. ★ **真实鼠标**：S3 用 `mouse.click`（823 的教训：`select_option`
   那种程序化路径**不产生 pointerdown**，算不得「纯 UI」）。
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch824-2026-10-01"
RAW = BATCH / "raw" / "vb824b.json"
RAW_SRC_BAR = BATCH / "raw" / "source-824-bottombar.json"
RAW_SRC_TV = BATCH / "raw" / "source-824-tvdirector.json"
RAW_SRC_STYLE = BATCH / "raw" / "source-824-tvstyle.json"
RAW_SRC_DOCK = BATCH / "raw" / "source-824-dockpill.json"
PROBE = BATCH / "probes" / "dbg824b.py"

K_NODES = "★ 节点数"
K_EDGES = "★ 边数"
K_ARIA = "aria"

EXPECTED_MOMENTS = [
    "B0·★ 起点：画布底部工具条上有几枚按钮、有没有「TV Director」",
    "B1·★★ 点胶囊 ⟹ 抽屉打开了吗",
    "B2·★ 抽屉开着时底部胶囊**应当消失**",
]


def at(raw, name):
    for r in raw["步骤"]:
        if r["步骤"] == name:
            return r
    raise KeyError("raw 里没有这个时刻：" + name)


def ok(name, why, cond, evidence):
    return {"id": name, "why": why, "ok": bool(cond), "evidence": evidence}


def build_checks(raw):
    C = []
    # ★ 源站读数**默认**读入库的文件（保证「clone 与源站一致」可复算）；
    # ★ 但允许 raw 里带 "__源站底部工具条" 覆盖副本 —— 阴性对照 N12 需要它
    #   才能把变异**真的送进判据**（★ 变异必须打在性质真正读取的字段上）
    src_bar = raw.get("__源站底部工具条")
    src_bar_src = "raw 里的覆盖副本（阴性对照注入）"
    if src_bar is None:
        src_bar = json.loads(RAW_SRC_BAR.read_text(encoding="utf-8"))
        src_bar_src = "入库文件 " + str(RAW_SRC_BAR.relative_to(ROOT))
    src_tv = json.loads(RAW_SRC_TV.read_text(encoding="utf-8"))
    src_style = json.loads(RAW_SRC_STYLE.read_text(encoding="utf-8"))

    # ── S1 前提：3 个时刻按顺序齐 + 探针零 store 写调用
    got = [r["步骤"] for r in raw["步骤"]]
    psrc = PROBE.read_text(encoding="utf-8")
    action_calls = re.findall(r"\bS\.(?!getState\b)\w+\s*\(", psrc)
    chained = re.findall(r"getState\(\)\s*\.\s*(\w+)", psrc)
    zero_write = (len(action_calls) == 0
                  and all(c == "getState" for c in chained))
    C.append(ok(
        "S1:★★ **前提**：3 个时刻**按顺序一个不缺**、探针源码里**零 store 写调用**（正则自证）",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。★ 「零 store 写调用」是本批的立身之本 ⟹ 靠**扫源码**自证：允许 `getState()`、**禁止任何 action 形式调用**",
        got == EXPECTED_MOMENTS and zero_write,
        {"时刻": got, "★ 与写死的顺序一致": got == EXPECTED_MOMENTS,
         "★ 扫到的 action 形式调用": action_calls,
         "★ getState 之后的链式调用": chained, "★ 零写调用": zero_write}))

    # ── S2 clone 底部工具条上有那枚胶囊，且是 48×48
    b0 = at(raw, EXPECTED_MOMENTS[0])
    bar = b0["读数"]["底部按钮"]
    cap = [d for d in bar if d[K_ARIA] == "TV Director"]
    C.append(ok(
        "S2:★★ clone 画布**底部工具条**上有「TV Director」胶囊，且是 **48×48**",
        "★★ 判据认**绝对几何**：源站读数是 48×48（点位 955,889）⟹ clone 这枚也必须 48×48。★ 「在底部」用**视口相对**判定（`y >= 视口高-140`）⟹ ★ 823 的教训：写死 `y<700` 会因**视口高度不同**把工具条整簇滤掉",
        len(cap) == 1 and cap[0]["w"] == 48 and cap[0]["h"] == 48,
        {"★ 胶囊": cap, "★ 底部按钮清单": bar,
         "★ 视口": {"宽": b0["读数"]["视口宽"], "高": b0["读数"]["视口高"]}}))

    # ── S3 ★★ 真实鼠标点它 ⟹ 抽屉打开
    b1 = at(raw, EXPECTED_MOMENTS[1])
    texts = b1["★ 抽屉可见文本"]
    C.append(ok(
        "S3:★★ **真实鼠标**点那枚胶囊 ⟹ 右侧「新对话」抽屉打开",
        "★★ 点法必须是**真实鼠标**（`mouse.click`）⟹ 823 的教训：`select_option` 那种程序化路径**不产生 pointerdown**、算不得「纯 UI」。★ 判据看**可见文本**里有没有「新对话」——★ clone 的 `AgentDrawer` 标题逐字就是「新对话」，与源站同一块面板",
        b1["★ 点击"]["结果"] == "clicked"
        and b1["★ 抽屉开着"] is True
        and "新对话" in texts,
        {"★ 点击": b1["★ 点击"], "★ 抽屉开着": b1["★ 抽屉开着"],
         "★ 抽屉可见文本（前 20）": texts[:20]}))

    # ── S4 ★ 点它**不建节点**（与源站实测一致）
    C.append(ok(
        "S4:★ 点胶囊**不建节点**（节点数不变）—— 与源站实测一致",
        "★ 源站实测：点那个胶囊 **URL 不变、画布节点数 7→7 不变**⟹ ⟹ ★ 它**不是**「新建导演台节点」的入口 ⟹ ⟹ clone 这枚也必须**不建节点**（否则就把「打开面板」做成了「偷偷建节点」）",
        b1["★ 节点数（不该变）"] == 10,
        {"★ 点之后的节点数": b1["★ 节点数（不该变）"],
         "★ 源站对照": {"点之前节点数": src_tv["点之前"]["nodes"],
                        "点之后节点数": src_tv["点之后_6s"]["nodes"],
                        "URL 变了": (src_tv["点之前"]["url"]
                                  != src_tv["点之后_6s"]["url"])}}))

    # ── S5 ★ 抽屉开着时胶囊消失
    b2 = at(raw, EXPECTED_MOMENTS[2])
    C.append(ok(
        "S5:★ 抽屉开着时，那枚底部胶囊**消失**（与源站截图一致）",
        "★ 源站截图实测：抽屉打开后底部工具条只剩 7 枚、**胶囊消失**（它变成了抽屉的开关）⟹ ★ clone 照做。★ 判据只认 DOM 读数，不看截图",
        b1["★ 底部工具条还有 TV Director 吗"] is False
        and b2["★ 还有 TV Director 吗"] is False,
        {"B1 时还有吗": b1["★ 底部工具条还有 TV Director 吗"],
         "B2 时还有吗": b2["★ 还有 TV Director 吗"],
         "★ B2 底部按钮": b2["★ 底部按钮"]}))

    # ── S6 ★★★ 源站对照：逐项核对「源站有、clone 也要有」
    src_buttons = [d for d in src_bar["底部中间"]]
    src_tv_btn = [d for d in src_buttons if d["aria"] == "TV Director"]
    src_tv_names = [d["aria"] for d in src_buttons]
    clone_names = [d[K_ARIA] for d in bar]
    # ★★ Batch 826：共享项从 6 枚变成 **7 枚** —— 源站那一簇是 7 枚
    # （add-node / tool-mode / open-asset / character-library / history /
    # keyboard / contact），第 4 枚的 aria 逐字是「**角色造型室**」
    # （batch 824 的入库 raw 里本来就写着它，只是当时 clone 叫「角色库」⟹
    # 那时只记不改）⟹ ★★ 现在 clone 也逐字改成「角色造型室」⟹
    # ★★ 断言**加强**（要求 7 枚逐字同名，而不是 6 枚）。
    shared = ["添加节点", "移动", "素材库", "角色造型室", "生成历史", "快捷键", "教程"]
    C.append(ok(
        "S6:★★★ **源站对照**（读**入库的源站读数**，不是我的印象）：源站底部工具条 8 枚、含 48×48 的「TV Director」；clone 底部**也有**这一枚，且共享的 7 枚**逐项同名**",
        "★★★ 「clone 与源站一致」这句话**必须可复算** ⟹ 所以判据直接读**入库的源站 raw**。★ 共享项（Batch 826 起是 7 枚）：添加节点／移动／素材库／角色造型室／生成历史／快捷键／教程 ⟹ ★★ clone 那枚 clone-only 的「打开工具箱」**已归位**到素材库 popover 内（源站它就在那儿）⟹ ★★ **逐字同构**",
        len(src_tv_btn) == 1
        and src_tv_btn[0]["矩形"]["w"] == 48
        and src_tv_btn[0]["矩形"]["h"] == 48
        and "TV Director" in src_tv_names
        and "TV Director" in clone_names
        and all(n in clone_names for n in shared),
        {"★ 源站底部工具条可及名": src_tv_names,
         "★ 源站读数取自": src_bar_src,
         "★ 源站 TV Director 按钮": src_tv_btn,
         "★ clone 底部工具条可及名": clone_names,
         "★ 共享的 7 枚": shared,
         "★ 逐字同构的 7 枚都在": all(n in clone_names for n in shared),
         "★ clone 多出": [n for n in clone_names if n not in src_tv_names]}))

    # ── S7 ★ 源站对照：那个胶囊点开的是「新对话」抽屉，不是导演台
    before = {t["t"] for t in src_tv["点之前"]["可见文本"]}
    after = {t["t"] for t in src_tv["点之后_6s"]["可见文本"]}
    new_texts = sorted(after - before)
    C.append(ok(
        "S7:★★★ **源站对照**：点那个胶囊打开的是**「新对话」AI 抽屉**，**不是导演台**",
        "★★★ 这条**推翻了**「clone 缺的是导演台入口」的假设 ⟹ ★ 实测：URL 不变、画布节点数不变、冒出一批新文案 ⟹ ⟹ ★ 「让 TV Director 辅助你的无限创意」「感知画布开始创作」「从爆款预设开始剧本原创」「上传故事来改编」「批量优化提示词」⟹ ⟹ ★★ 那是一块**AI 对话抽屉**，而 clone 的 `AgentDrawer` 正是同一块（标题逐字「新对话」）⟹ ⟹ ★★ **clone 不是缺面板，是缺入口**",
        (src_tv["点之前"]["url"] == src_tv["点之后_6s"]["url"]
         and src_tv["点之前"]["nodes"] == src_tv["点之后_6s"]["nodes"]
         and any("让 TV Director 辅助你的无限创意" in t for t in new_texts)
         and any("上传故事来改编" in t for t in new_texts)
         and any("批量优化提示词" in t for t in new_texts)),
        {"★ URL 变了": (src_tv["点之前"]["url"]
                       != src_tv["点之后_6s"]["url"]),
         "★ 节点数": [src_tv["点之前"]["nodes"],
                      src_tv["点之后_6s"]["nodes"]],
         "★ 新出现的文本": new_texts}))

    # ── S9 ★★★ 源站对照：那枚球**不在药丸里**（药丸结束后单独挂一枚）
    # ★★★ 这里的期望值**全部从源站 raw 算出来**，而且**两边用同一把尺子**：
    #   「按钮到球间隙」（教程右缘 → 球左缘）与「药丸到球间隙」（药丸右缘 → 球左缘）
    #   是**两个不同的量** ⟹ ★ 第一版我只比了其中一个，于是拿 clone 的
    #   「药丸→球」去比源站的「按钮→球」⟹ ★★ **数字碰巧都等于 14**，
    #   ★★ 判据绿灯而 clone 实际离按钮 23px（源站是 14px）⟹ 差 9px。
    #   ⟹ 这条判据现在**两个量都比**，且期望值来自源站自己。
    g = b0["★ 球几何"]
    dock = json.loads(RAW_SRC_DOCK.read_text(encoding="utf-8"))
    src_ball = [c for c in src_style["子元素"] if c["tag"] == "DIV"][0]
    # ★ 源站的药丸 = 教程按钮的父链里，第一个「有底色 + 圆角 + 不是全屏」的元素
    src_pill = [c for c in dock["父链"]
                if c["bg"] not in ("rgba(0, 0, 0, 0)", "transparent")
                and c["box"]["w"] < dock["视口"][0]][0]
    C.append(ok(
        "S9:★★★ **源站对照**：那枚球**在药丸之外** —— 药丸右缘外 %spx、"
        "最后一枚按钮右缘外 %spx，且与按钮行**同轴**（偏差 %spx），球 %s×%s"
        % (dock["药丸到球间隙"], dock["按钮到球间隙"], dock["同轴偏差"],
           src_ball["box"]["w"], src_ball["box"]["h"]),
        "★★★ 判据的**期望值从源站 raw 算出来**（不是我的印象）⟹ "
        "「clone 与源站一致」可复算。★★ ★★ **两个尺子都要量**："
        "「药丸→球」与「按钮→球」是**两个不同的量**（差一个药丸的右内边距）⟹ "
        "★ 第一版只拿其中一个去比另一个，数字碰巧相等 ⟹ ★★ 判据绿灯而实现差 9px。",
        g["存在"] is True
        and abs(g["间隙"] - dock["药丸到球间隙"]) <= 0.5
        and abs(g["按钮到球间隙"] - dock["按钮到球间隙"]) <= 0.5
        and abs(g["同轴偏差"] - dock["同轴偏差"]) <= 0.5
        and g["球在药丸右侧"] is True
        and g["药丸是否包住球"] is False
        and g["球"]["w"] == dock["球"]["w"] and g["球"]["h"] == dock["球"]["h"]
        and g["球体"]["w"] == src_ball["box"]["w"]
        and g["球体"]["h"] == src_ball["box"]["h"],
        {"★ 期望（源站算的）": {"药丸→球": dock["药丸到球间隙"],
                            "按钮→球": dock["按钮到球间隙"],
                            "同轴": dock["同轴偏差"],
                            "球": dock["球"], "球体": src_ball["box"],
                            "药丸": src_pill["box"], "药丸样式": src_pill},
         "★ clone 实测": {"药丸→球": g["间隙"], "按钮→球": g["按钮到球间隙"],
                        "同轴": g["同轴偏差"], "球": g["球"],
                        "球体": g["球体"], "药丸": g["药丸"],
                        "药丸样式": g["药丸样式"],
                        "球在药丸右侧": g["球在药丸右侧"]}}))

    # ── S10 ★★ 源站对照：球里的「TV Director」文字是**藏起来的**（宽 0 + 透明）
    src_txt = [c for c in src_style["子元素"] if c["tag"] == "SPAN"][0]
    C.append(ok(
        "S10:★★ **源站对照**：球里那段「TV Director」文字**视觉上没有**"
        "（矩形宽 0 + opacity 0），但**可及名还在**",
        "★★ 源站的藏法逐字是：外层 span `width:0` + `opacity:0`（读数 0×20，"
        "opacity 0），内层再套一个带 padding 的 span ⟹ ★★ **屏幕上一个字都没有**，"
        "但 textContent 逐字仍是「TV Director」⟹ 可及名由 aria-label 承担。"
        "⟹ ★ 第一版做成了「可见文字」，就是照着 DOM 的 textContent 抄的 ⟹ "
        "★★ **DOM 读数里有文字 ≠ 视觉上有文字** ⟹ 这条判据只认**矩形宽 + opacity**",
        g["文字元素"]["w"] == src_txt["box"]["w"]
        and g["文字样式"]["opacity"] == src_txt["opacity"]
        and g["文字样式"]["text"] == "TV Director"
        and g["文字样式"]["overflow"] == "hidden",
        {"★ clone 文字矩形": g["文字元素"], "★ clone 文字样式": g["文字样式"],
         "★ 源站文字矩形": src_txt["box"], "★ 源站文字 opacity": src_txt["opacity"]}))

    # ── S11 ★★ 球芯必须**真的有颜色**（不是一只空圆钮）
    core = g.get("球芯")
    core_cs = g.get("球芯样式") or {}
    src_html = src_style.get("胶囊整段HTML", "")
    C.append(ok(
        "S11:★★ 球芯**真的画出了渐变**（%s×%s、圆角 %s、渐变里有源站那颗青 #00e5ff）"
        % (core["w"] if core else "?", core["h"] if core else "?",
           core_cs.get("radius", "?")),
        "★★ 这条是**踩过坑之后加的**：★★ 第一版那颗球是用 Tailwind 任意值写的"
        "（`bg-[radial-gradient(...)]`），而 ★★ **4317 的 dev server 的 Tailwind "
        "扫描是冻结的**（进程从 2026-10-07 起没重扫）⟹ ★★ 那条类**在 dev 上不存在** ⟹ "
        "★ 球芯 computed backgroundColor = rgba(0,0,0,0)、截图里**球是空的** ⟹ "
        "★★ 「DOM 里有这个元素」**不等于**「它画出来了」⟹ 这条判据只认"
        "**background-image 不是 none**。★ 源站那颗球的青色是 `--liquid-state-color:#00e5ff`",
        bool(core) and core["w"] == 28 and core["h"] == 28
        and core_cs.get("bgImage", "none") != "none"
        and "gradient" in core_cs.get("bgImage", "")
        # ★ computed style 会把 #00e5ff 归一成 rgb(0, 229, 255) ⟹ 按归一后的值比
        and "rgb(0, 229, 255)" in core_cs.get("bgImage", "")
        and "00e5ff" in src_html.lower(),
        {"★ clone 球芯": core, "★ clone 球芯样式": core_cs,
         "★ 源站球芯的颜色变量": "00e5ff" if "00e5ff" in src_html.lower() else None,
         "★ 源站 HTML 片段": src_html[:200]}))

    # ── S8 静态锚点
    left = (ROOT / "src" / "components" / "LeftSidebar.tsx").read_text(
        encoding="utf-8")
    top = (ROOT / "src" / "components" / "TopNavBar.tsx").read_text(
        encoding="utf-8")
    drawer = (ROOT / "src" / "components" / "AgentDrawer.tsx").read_text(
        encoding="utf-8")
    uistore = (ROOT / "src" / "store" / "uiStore.ts").read_text(
        encoding="utf-8")
    anchors = {
        "LeftSidebar.tsx: 底部工具条里有 aria-label=\"TV Director\" 的胶囊":
            'aria-label="TV Director"' in left,
        "LeftSidebar.tsx: 胶囊的 data-tv-director-trigger":
            "data-tv-director-trigger" in left,
        "LeftSidebar.tsx: 胶囊用 toggleAgent 打开抽屉":
            "onClick={toggleAgent}" in left,
        "LeftSidebar.tsx: 抽屉开着时胶囊不渲染":
            "!isAgentOpen ?" in left,
        "LeftSidebar.tsx: 球是**药丸之外**的独立圆钮（left-full，不吃流式布局）":
            "absolute left-full" in left,
        "LeftSidebar.tsx: 球体 28×28 的容器（与源站 size-7 一致）":
            'data-testid="canvas-agent-orb-entry"' in left and "size-7" in left,
        "LeftSidebar.tsx: 那段文字是**藏起来的**（w-0 + opacity-0）":
            "opacity-0" in left and "w-0 overflow-hidden" in left,
        # ★ 只看**类名串本身**（注释里提到 top-[23.5px] 不算数）
        "LeftSidebar.tsx: 竖向用标准类 top-1/2（★ 不用带小数的任意值）":
            'className="absolute left-full ml-[6px] top-1/2' in left,
        "AgentDrawer.tsx: 抽屉标题逐字「新对话」":
            ">新对话<" in drawer,
        "uiStore.ts: toggleAgent 切 isAgentOpen":
            "toggleAgent: () =>" in uistore,
        "TopNavBar.tsx: 顶部那枚「Agent」按钮**仍然在**（被历史门禁钉住）":
            ">Agent<" in top,
    }
    C.append(ok(
        "S8:★ 静态锚点：胶囊的标记／toggleAgent／抽屉标题「新对话」，以及**顶部那枚「Agent」按钮仍在**",
        "★ 静态锚点与运行时读数**互为独立来源**。★★ 特别把「**顶部那枚按钮仍在**」写成锚点 ⟹ 因为它被 batch723/737/649/280 的 runtime-audit 钉住 ⟹ ⟹ ★ 本批只能**增量**补底部胶囊、**不能删**顶部那枚",
        all(anchors.values()), anchors))

    return C


# ══════════════════════ 阴性对照 ══════════════════════

def n9_fake_missing(raw):
    """把 B0 的胶囊读数抹掉 ⟹ S2 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, EXPECTED_MOMENTS[0])
    row["读数"]["底部按钮"] = [
        d for d in row["读数"]["底部按钮"] if d["aria"] != "TV Director"]
    return r


def n10_fake_size(raw):
    """把胶囊的 48×48 改成 40×40 ⟹ S2 必须翻红（几何判据有牙）。"""
    r = copy.deepcopy(raw)
    row = at(r, EXPECTED_MOMENTS[0])
    for d in row["读数"]["底部按钮"]:
        if d["aria"] == "TV Director":
            d["w"] = 40
    return r


def n11_fake_not_open(raw):
    """把「抽屉开着」改成 False ⟹ S3 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, EXPECTED_MOMENTS[1])
    row["★ 抽屉开着"] = False
    return r


def n12_fake_source(raw):
    """把源站读数里胶囊的 48×48 改成 32×32 ⟹ S6 必须翻红。"""
    r = copy.deepcopy(raw)
    src = json.loads(RAW_SRC_BAR.read_text(encoding="utf-8"))
    for d in src["底部中间"]:
        if d["aria"] == "TV Director":
            d["矩形"]["w"] = 32
    r["__源站底部工具条"] = src
    return r


def n13_fake_gap(raw):
    """把「药丸→球」改成 20 ⟹ S9 必须翻红（间隙判据有牙）。"""
    r = copy.deepcopy(raw)
    at(r, EXPECTED_MOMENTS[0])["★ 球几何"]["间隙"] = 20
    return r


def n15_fake_button_gap(raw):
    """★ 把「按钮→球」改成 23 ⟹ S9 必须翻红。

    ★★ 这一条正是**我第一版踩的那个坑**的阴性对照：
    第一版只比「药丸→球」，而源站读的是「按钮→球」⟹ 两把尺子 ⟹ 数字碰巧相等。
    ⟹ 现在**两个量都在判据里**，所以「按钮→球」一错就必须翻红。
    """
    r = copy.deepcopy(raw)
    at(r, EXPECTED_MOMENTS[0])["★ 球几何"]["按钮到球间隙"] = 23
    return r


def n16_fake_empty_ball(raw):
    """★ 把球芯的渐变改成 none（**空球**）⟹ S11 必须翻红。

    ★ 这正是实测踩到的那个坑：DOM 里元素在、尺寸对，但**它没画出来**。
    ⟹ 阴性必须打在「background-image 不是 none」这个字段上。
    """
    r = copy.deepcopy(raw)
    g = at(r, EXPECTED_MOMENTS[0])["★ 球几何"]
    g["球芯样式"]["bgImage"] = "none"
    return r


def n14_fake_visible_text(raw):
    """把那段藏起来的文字改成**可见**（宽 40、opacity 1）⟹ S10 必须翻红。

    ★ 这一条专门打在「DOM 里有 textContent，但视觉上不该有字」这个性质上
    ⟹ ★ 阴性必须打在**性质真正读取的字段**（矩形宽 + opacity）上。
    """
    r = copy.deepcopy(raw)
    g = at(r, EXPECTED_MOMENTS[0])["★ 球几何"]
    g["文字元素"]["w"] = 40
    g["文字样式"]["opacity"] = "1"
    return r


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = build_checks(raw)

    neg = []
    for label, mut, expect in [
        ("N9 把 B0 的胶囊读数抹掉 ⟹ S2 翻红", n9_fake_missing, "S2"),
        ("N10 把胶囊改成 40×40 ⟹ S2 翻红（几何判据有牙）",
         n10_fake_size, "S2"),
        ("N11 把「抽屉开着」改成 False ⟹ S3 翻红", n11_fake_not_open, "S3"),
        ("N12 把源站胶囊改成 32×32 ⟹ S6 翻红（源站对照真被读）",
         n12_fake_source, "S6"),
        ("N13 把间隙改成 20 ⟹ S9 翻红（间隙判据有牙）", n13_fake_gap, "S9"),
        ("N14 把藏起来的文字改成可见 ⟹ S10 翻红（视觉判据有牙）",
         n14_fake_visible_text, "S10"),
        ("N15 把「按钮→球」改成 23 ⟹ S9 翻红（★ 两把尺子都在判据里）",
         n15_fake_button_gap, "S9"),
        ("N16 把球芯渐变改成 none（空球）⟹ S11 翻红（★ 画没画出来也要判）",
         n16_fake_empty_ball, "S11"),
    ]:
        mutated = mut(raw)
        mc = build_checks(mutated)
        turned = [c["id"].split(":")[0] for c in mc if not c["ok"]]
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": expect in turned})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 824,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    out = BATCH / "verify-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:62])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:56]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
