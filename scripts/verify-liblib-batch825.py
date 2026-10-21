#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 825 验收器 —— 导演台·跟随横幅：「退出跟随」到底点不点得动？

## ★ 这一批推翻了一条**已入库**的结论

batch 605 的 runtime-audit 写着：

    「deliberate deviation: the source's own 取消 pill inherits pointer-events:none
      from the banner panel … elementFromPoint at the pill centre lands on the
      机位视角 button underneath — so the source's cancel is unclickable」

★ **那句话是错的**，错在两处（2026-10-21，源站**代码** + 源站**运行时**双证据）：

1. ★★ 源站那条横幅是 **`collab-follow-banner`**（**协作**跟随，跟别人的视角）：
   它的**内层面板**在 `active` 时是 `pointer-events-auto` ⟹ ★★ **源站在显示时，
   那枚「取消」是点得动的**；按钮自己**没写** pointer-events，是从面板继承的 auto。
   ⟹ 605 量到的那块是**未激活**的横幅（opacity 0 / aria-hidden / inert / pe:none）
   ⟹ 命中穿透是**设计如此**，不是缺陷。
2. ★★ 更要紧的：**源站的「机位跟随目标」根本没有这条横幅**。它的唯一调用点传的是
   `prefix = 正在定位/正在跟随`、`nickname = 对方昵称`、`colorHex = 对方颜色`
   ⟹ ⟹ ★★ clone 这条横幅是 **clone-only 的额外物**，皮肤照抄了源站的**协作**横幅。

## ★ 判据纪律

- ★ 源站对照**读入库的证据**（bundle 片段 + 源站运行时读数），不是我的印象
- ★ 阴性对照打在**性质真正读取的字段**上
- ★ 探针源码**零 store 写调用**（正则自证）
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch825-2026-10-01"
RAW = BATCH / "raw" / "vb825a.json"
RAW_SRC_SNIPPET = BATCH / "raw" / "source-825-followbanner.js"
RAW_SRC_FACTS = BATCH / "raw" / "source-825-followbanner-facts.json"
RAW_SRC_KEYS = BATCH / "raw" / "source-825-follow-keys.json"
RAW_SRC_RUNTIME = BATCH / "raw" / "source-825-desk-follow.json"
PROBE = BATCH / "probes" / "dbg825a.py"
CLONE_SRC = ROOT / "src" / "components" / "director" / "DirectorDesk.tsx"

EXPECTED_MOMENTS = [
    "C0·★ 起点：导演台里相机的跟随目标为空、横幅**不在**",
    "C1·★★ 设上跟随目标 ⟹ 横幅**应当出现**",
    "C2·★★ **真实鼠标**悬停 ⟹ 「按 ESC 退出」应当显形",
    "C3·★★ **真实鼠标点**取消 ⟹ 横幅应当消失、跟随退出",
]


def at(raw, name):
    for r in raw["步骤"]:
        if r["步骤"] == name:
            return r
    raise KeyError("raw 里没有这个时刻：" + name)


def _banner_block(src: str) -> str:
    """取出**跟随横幅那一段**源码（横幅容器 → 提示 span 结束）。

    ★ 用来把否定锚点**限定范围** ⟹ 文件别处的合法措辞不误伤。
    """
    i = src.find("data-director-follow-banner")
    if i < 0:
        return ""
    j = src.find("按 ESC 退出", i)
    return src[i:j + 40] if j > 0 else src[i:i + 3000]


def _btn_cls_no_pointer_events(src: str) -> bool:
    """取「取消按钮」那个 className 串，看它**自己**有没有 pointer-events。

    ★ 不能用「按钮属性到 className 之间的字符数」当条件（中间那段注释
    很长，窗口一窄就漏判）⟹ ★★ 改成：找到属性位置之后**第一个**
    `className="peer rounded-full`，再检查那一段里有没有 pointer-events。
    """
    i = src.find("data-director-follow-cancel")
    if i < 0:
        return False
    m = re.search(r'className="([^"]*)"', src[i:])
    return bool(m) and "pointer-events" not in m.group(1)


def ok(name, why, cond, evidence):
    return {"id": name, "why": why, "ok": bool(cond), "evidence": evidence}


def build_checks(raw):
    C = []
    # ★ 源站片段：默认读入库文件；允许 raw 里的覆盖副本（阴性对照要用）
    snippet = raw.get("__源站横幅片段")
    snippet_src = "raw 里的覆盖副本（阴性对照注入）"
    if snippet is None:
        snippet = RAW_SRC_SNIPPET.read_text(encoding="utf-8")
        snippet_src = "入库文件 " + str(RAW_SRC_SNIPPET.relative_to(ROOT))
    facts = json.loads(RAW_SRC_FACTS.read_text(encoding="utf-8"))
    keys = json.loads(RAW_SRC_KEYS.read_text(encoding="utf-8"))
    runtime = json.loads(RAW_SRC_RUNTIME.read_text(encoding="utf-8"))

    # ── S1 前提：4 个时刻按顺序齐 + 探针零 store 写调用
    got = [r["步骤"] for r in raw["步骤"]]
    psrc = PROBE.read_text(encoding="utf-8")
    action_calls = re.findall(r"\bS\.(?!getState\b)\w+\s*\(", psrc)
    chained = re.findall(r"getState\(\)\s*\.\s*(\w+)", psrc)
    zero_write = (len(action_calls) == 0
                  and all(c == "getState" for c in chained))
    C.append(ok(
        "S1:★★ **前提**：4 个时刻**按顺序一个不缺**、探针源码里**零 store 写调用**",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。★ 本批的探针只读 store"
        "（`__director_store.getState()`）⟹ 靠**扫源码**自证：允许 getState、"
        "**禁止任何 action 形式调用**",
        got == EXPECTED_MOMENTS and zero_write,
        {"时刻": got, "★ 与写死的顺序一致": got == EXPECTED_MOMENTS,
         "★ 扫到的 action 形式调用": action_calls,
         "★ getState 之后的链式调用": chained, "★ 零写调用": zero_write}))

    c0 = at(raw, EXPECTED_MOMENTS[0])
    c1 = at(raw, EXPECTED_MOMENTS[1])
    c2 = at(raw, EXPECTED_MOMENTS[2])
    c3 = at(raw, EXPECTED_MOMENTS[3])

    # ── S2 起点：横幅不在、跟随目标为空
    C.append(ok(
        "S2:★★ 起点：跟随目标**为空** ⟹ 顶部横幅**不在**",
        "★★ 前提的另一半：横幅是**跟随状态**的产物 ⟹ 起点必须是「没有跟随」"
        "⟹ 否则后面「点取消 ⟹ 横幅消失」就没有意义（它本来就该在）",
        c0["★ 横幅"]["存在"] is False
        and c0["★ store 读数"]["★ 跟随目标"] is None
        and c0["★ 跟随目标下拉"]["value"] == "",
        {"★ 横幅": c0["★ 横幅"], "★ store 读数": c0["★ store 读数"],
         "★ 下拉当前值": c0["★ 跟随目标下拉"]["value"]}))

    # ── S3 ★★★ 源站对照：横幅的**几何**与源站逐字对齐
    # ★ 期望值**从源站的运行时读数算出来**（源站那块横幅此刻就在 DOM 里）
    src_banner = runtime["A 画布页读数"]["跟随横幅候选（含未激活）"][0]
    src_btn = runtime["A 画布页读数"]["取消按钮"]
    src_rect = src_banner["rect"]
    src_brect = src_btn["rect"]
    cl = c1["★ 横幅"]
    C.append(ok(
        "S3:★★★ **源站对照**：横幅 %sx%s、按钮 %sx%s —— 与源站那块**逐字同形**"
        % (cl["横幅矩形"]["w"], cl["横幅矩形"]["h"],
           cl["按钮"]["w"], cl["按钮"]["h"]),
        "★★★ 判据的期望值**从源站运行时读数算出来**（源站那块协作横幅此刻就在"
        "DOM 里，rect %sx%s @(x=%s)）⟹ 「clone 与源站同形」可复算。★ 横向坐标"
        "**不该直接比**（源站那个视口是 1920、clone 是 1440）⟹ 比**宽高**与"
        "**水平居中**",
        abs(cl["横幅矩形"]["w"] - src_rect["w"]) <= 1.0
        and abs(cl["横幅矩形"]["h"] - src_rect["h"]) <= 1.0
        and abs(cl["按钮"]["w"] - src_brect["w"]) <= 1.0
        and abs(cl["按钮"]["h"] - src_brect["h"]) <= 1.0
        and abs(cl["横幅矩形"]["cx"] - cl["视口宽"] / 2) <= 0.6,
        {"★ 源站横幅 rect": src_rect, "★ 源站按钮 rect": src_brect,
         "★ clone 横幅 rect": cl["横幅矩形"], "★ clone 按钮 rect": cl["按钮"],
         "★ clone 提示 rect": cl["提示"],
         "★ clone 视口": [cl.get("视口宽"), cl.get("视口高")]}))

    # ── S4 ★★ 那枚按钮**真的点得动**（命中就是它），且**结构与源站同构**
    btn = cl["按钮样式"]
    C.append(ok(
        "S4:★★ 那枚「取消ESC」**命中就是它**（点得动），且**类里没有 pointer-events**"
        "（与源站同构：命中由**面板**的 auto 提供）",
        "★★ 这一条**直接反驳** batch 605 记的那句「源站这枚取消根本点不动」："
        "★ clone 的 computed pointer-events = **auto** ⟹ 命中测试落在按钮自己身上"
        "（`命中.就是它` = true）⟹ ★★ **点得动**。★★ 而且现在 clone 的**按钮自己"
        "不写** pointer-events、**面板**写 `pointer-events-auto` ⟹ ⟹ ★★ 与源站"
        "**逐字同构**（源站：面板 `${active ? pointer-events-auto : "
        "pointer-events-none}`、按钮无 pointer-events 类）",
        cl["命中"]["就是它"] is True
        and btn["pe"] == "auto"
        and "pointer-events" not in btn["cls"]
        and btn["aria"] == "退出跟随"
        and btn["ariaKeyShortcuts"] == "Escape"
        and btn["own"] == "取消ESC"
        and btn["子元素数"] == 0,
        {"★ 命中": cl["命中"], "★ 按钮样式": btn,
         "★ 横幅的 pe": cl["横幅样式"]["pe"],
         "★ 源站按钮类（同一段代码）": src_btn["cls"]}))

    # ── S5 ★★ 悬停 ⟹ 「按 ESC 退出」显形
    hov = c2["★ 悬停"]
    C.append(ok(
        "S5:★★ **真实鼠标**悬停 ⟹ 「按 ESC 退出」显形（opacity 0 → 1）",
        "★★ 这是源站的 **peer-hover** 契约（源站片段：提示 span 是 "
        "`opacity-0 … peer-hover:opacity-100 peer-focus-visible:opacity-100`）⟹ "
        "★ 源站那枚按钮**点得动**，所以它的提示**真的显形**；★ 605 记的"
        "「提示因此永远显不出来」**只对未激活态成立**。★ 判据只认**前后两次"
        "computed opacity**",
        hov.get("结果") == "hovered"
        and hov["★ 悬停前提示"]["opacity"] == "0"
        and hov["★ 悬停后提示"]["opacity"] == "1"
        and c2["★ 悬停时的横幅"]["提示样式"]["role"] == "tooltip",
        {"★ 悬停": hov,
         "★ 提示样式": c2["★ 悬停时的横幅"]["提示样式"]}))

    # ── S6 ★★ 真实鼠标点取消 ⟹ 横幅消失、跟随退出
    C.append(ok(
        "S6:★★ **真实鼠标点**「取消ESC」 ⟹ 横幅**消失**、跟随**退出**",
        "★★ 这一步**全程真实鼠标**（`mouse.move` + `mouse.down` + `mouse.up`）⟹ "
        "★ 是真 pointerdown ⟹ ★ 823 的「纯 UI」判据在这一步**成立**。"
        "★★ 判据看**两处**：横幅从 DOM 里没了 ＋ **store 读数**里跟随目标回 null",
        c3["★ 点击"]["结果"] == "clicked"
        and c3["★ 点之后的横幅"]["存在"] is False
        and c3["★ store 读数"]["★ 跟随目标"] is None,
        {"★ 点击": c3["★ 点击"], "★ 点之后的横幅": c3["★ 点之后的横幅"],
         "★ store 读数": c3["★ store 读数"]}))

    # ── S7 ★★★ 源站对照（读入库的 bundle 片段）：「源站点不动」只在**未激活**态成立
    panel_auto = ('${e?"pointer-events-auto":"pointer-events-none"}' in snippet
                  or "pointer-events-auto" in snippet)
    btn_has_pe = bool(re.search(
        r'aria-label[^}]*\},"data-testid":"collab-follow-banner-close"', snippet)) \
        and "pointer-events" in re.search(
            r'className:"([^"]*)"[^}]*collab-follow-banner-close', snippet).group(1)
    C.append(ok(
        "S7:★★★ **源站对照**（读**入库的 bundle 片段**）：源站那枚按钮**自己没写**"
        "pointer-events；**面板在 active 时是 pointer-events-auto** ⟹ "
        "「源站点不动」**只对未激活态成立**",
        "★★★ 「clone 与源站一致」必须**可复算** ⟹ 判据直接读入库的源站代码片段。"
        "★★ 而 605 那句「按钮从浮层继承 pointer-events:none，所以根本点不动」"
        "**错在没分激活态**：★ 源站的写法是 "
        "`${active ? 'pointer-events-auto' : 'pointer-events-none'}` ⟹ "
        "★ **显示时**面板是 auto ⟹ 按钮**点得动**；★ 605 量的是**未激活**那块"
        "（opacity 0 / aria-hidden / inert / pe:none）⟹ 命中穿透是**设计如此**",
        panel_auto and not btn_has_pe
        and "pointer-events-auto" in snippet
        and "aria-keyshortcuts" in snippet,
        {"★ 源站片段取自": snippet_src,
         "★ 片段里 pointer-events-auto": snippet.count("pointer-events-auto"),
         "★ 片段里按钮类": (re.search(
             r'className:"([^"]*)"[^}]*collab-follow-banner-close', snippet)
             or re.search(r'(x)x', "x")).group(1)
         if re.search(r'className:"([^"]*)"[^}]*collab-follow-banner-close', snippet)
         else None,
         "★ 按钮自己带 pointer-events 吗": btn_has_pe,
         "★ 源站运行时那块横幅的状态": {
             "opacity": src_banner["opacity"], "pe": src_banner["pe"],
             "ariaHidden": src_banner["ariaHidden"], "inert": src_banner["inert"],
             "★ 命中穿透到": src_btn["命中文字"]}}))

    # ── S8 ★★★ 源站对照：这条横幅**只属于协作**，机位跟随**没有**它
    # ★ 调用点数 = `prefix:` 次数 − 参数解构那 1 处（见 recon825a 的注释）
    n_calls = snippet.count("prefix:") - 1
    director_follow_keys = [k for k in keys if k.startswith("directorCameraFollow")]
    banner_keys = [k for k in director_follow_keys if "Banner" in k]
    C.append(ok(
        "S8:★★★ **源站对照**：源站这条横幅**只有一个调用点**、prefix 是**协作**"
        "文案 ⟹ ⟹ **源站的「机位跟随目标」根本没有这条横幅**（导演台那套 i18n 里"
        "**一个 banner 键都没有**）⟹ ⟹ clone 这条是 **clone-only**",
        "★★★ 这是本批**最要紧**的一条：★ 源站的横幅组件 `collab-follow-banner` "
        "只服务**协作跟随**（跟别人的视角）⟹ 它的 prefix 是「正在定位/正在跟随」"
        "＋**对方昵称**、颜色是运行时的 `colorHex`（那个橙色 #E46525 在源站 JS 里"
        "**一个字节都没有**）⟹ ⟹ ★★ **源站的机位跟随**走的是另一套：检查器里的"
        "「跟随目标／不跟随／跟随视角／跟随偏移」＋ 时间轴上的「跟随：」前缀 ⟹ ⟹ "
        "★★ clone 这条横幅是**照抄了协作横幅的皮肤**，**不是源站机位跟随的复刻**"
        "⟹ ★ 「要不要删掉它」是**产品决策**，本批**只记不发明**",
        n_calls == 1
        and not banner_keys
        and "prefix:z" in snippet          # ★ prefix 是**运行时变量**（协作态给的）
        and "collabFollowControllerProcessing2" in keys,
        {"★ 源站片段里的调用点数": n_calls,
         "★ 导演台机位跟随的 i18n 键": director_follow_keys,
         "★ 其中带 banner 的": banner_keys,
         "★ 源站 i18n 里与跟随有关的键数": len(
             [k for k in keys if "follow" in k.lower()]),
         "★ 关键协作键": {k: keys[k] for k in keys
                          if k in ("collabFollowBannerCancelEsc",
                                   "collabFollowBannerPressEsc",
                                   "collabFollowBannerLogout2",
                                   "collabFollowControllerProcessing2",
                                   "directorCameraFollowTarget",
                                   "directorCameraFollowNone",
                                   "directorTimelineFollowTargetPrefix")}}))

    # ── S9 静态锚点：注释不再说错话 + 源站那两个属性已加 + 结构同构
    desk = CLONE_SRC.read_text(encoding="utf-8")
    anchors = {
        # ★★ 否定锚点必须**限定范围**：文件别处（87/386/1302 行）本来就有
        #   合法的「点不动」措辞（说的是别的控件）⟹ ★★ 文件级否定会误伤 ⟹
        #   ★★ 只看**横幅那一段**。
        "DirectorDesk.tsx: 横幅那段注释**不再**声称「源站那枚取消点不动」":
            "点不动" not in _banner_block(desk),
        "DirectorDesk.tsx: 注释写明了真实原因（面板 active 时 auto）":
            "pointer-events-auto" in desk and "激活" in desk,
        "DirectorDesk.tsx: 注释写明「源站的机位跟随没有这条横幅」":
            "机位跟随" in desk and "clone-only" in desk,
        "DirectorDesk.tsx: 取消按钮带 aria-keyshortcuts=\"Escape\"（源站同款）":
            'aria-keyshortcuts="Escape"' in desk,
        "DirectorDesk.tsx: 提示 span 带 role=\"tooltip\"（源站同款）":
            'role="tooltip"' in desk,
        "DirectorDesk.tsx: 按钮**自己没写** pointer-events（与源站同构）":
            _btn_cls_no_pointer_events(desk),
        "DirectorDesk.tsx: 横幅**面板**写 pointer-events-auto（与源站同构）":
            'className="pointer-events-auto flex items-center gap-2 rounded-b-xl' in desk,
    }
    C.append(ok(
        "S9:★ 静态锚点：注释**不再说错话**、源站那两个属性已加、按钮/面板的"
        "pointer-events **与源站同构**",
        "★ 静态锚点与运行时读数**互为独立来源**。★★ 特别把「**注释不再说错话**」"
        "写成锚点 ⟹ 因为 605 那条错结论**就写在这段注释里** ⟹ ⟹ ★ 错的话留在"
        "代码里，下一个人会继续照着它做决定",
        all(anchors.values()), anchors))

    return C


# ══════════════════════ 阴性对照 ══════════════════════

def n1_fake_banner_stays(raw):
    """把 C3 点之后的横幅读数改成「还在」⟹ S6 必须翻红。"""
    r = copy.deepcopy(raw)
    at(r, EXPECTED_MOMENTS[3])["★ 点之后的横幅"]["存在"] = True
    return r


def n2_fake_source_panel_none(raw):
    """★ 把源站片段里的 pointer-events-auto 换成 none ⟹ S7 必须翻红。

    ★ 这条阴性专门打「源站对照真被读」：若判据没读片段，改片段不会有任何反应。
    """
    r = copy.deepcopy(raw)
    snip = RAW_SRC_SNIPPET.read_text(encoding="utf-8")
    r["__源站横幅片段"] = snip.replace("pointer-events-auto", "pointer-events-none")
    return r


def n3_fake_two_callsites(raw):
    """把源站片段里的调用点数改成 2 ⟹ S8 必须翻红。"""
    r = copy.deepcopy(raw)
    snip = RAW_SRC_SNIPPET.read_text(encoding="utf-8")
    r["__源站横幅片段"] = snip.replace("prefix:", "prefix:", 1) + "prefix:z,"
    return r


def n4_fake_no_hover(raw):
    """把悬停后的提示 opacity 改成 0 ⟹ S5 必须翻红。"""
    r = copy.deepcopy(raw)
    at(r, EXPECTED_MOMENTS[2])["★ 悬停"]["★ 悬停后提示"]["opacity"] = "0"
    return r


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = build_checks(raw)

    neg = []
    for label, mut, expect in [
        ("N1 把「点之后横幅还在」⟹ S6 翻红", n1_fake_banner_stays, "S6"),
        ("N2 把源站片段的 pointer-events-auto 换掉 ⟹ S7 翻红（源站对照真被读）",
         n2_fake_source_panel_none, "S7"),
        ("N3 把源站片段的调用点数改成 2 ⟹ S8 翻红", n3_fake_two_callsites, "S8"),
        ("N4 把悬停后提示 opacity 改成 0 ⟹ S5 翻红", n4_fake_no_hover, "S5"),
    ]:
        mutated = mut(raw)
        mc = build_checks(mutated)
        turned = [c["id"].split(":")[0] for c in mc if not c["ok"]]
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": expect in turned})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 825,
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
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:66])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:60]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
