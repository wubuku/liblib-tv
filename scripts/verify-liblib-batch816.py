#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 816 验收器 —— 三份完全重叠的产物，用户**够得着**底下那两份吗

## 起点（815 直接留下的洞）

815 量到 `ImageNode` 七个动作连点三次，三份产物 **x／y／宽高逐像素相同**。
815 的「不声称」里明写：★ **三份压在一起之后用户还能不能选中底下那两份，本批没测**。

## ★ 为什么不能只点一下就下结论（807 起立的纪律）

「点不中底下那一份」有两种完全不同的成因：

- ① 命中测试天然只命中**最上层**那一份（**Z 序**问题）；
- ② 底下那两份**根本没被选中逻辑排除**，只是**没有别的路径**能把它们选出来。

⟹ 本批把**所有可能的选中路径各走一遍**，逐条记录选区变成什么。

## ★ 全部判据都**从 raw 的原始字段重算**

raw 记的是**原始 `selectedNodeIds`**（`选区原文`）与**原始存活 id 列表**，
判据据此**重算**「选中了第几份」；不信探针换算过的 `★ 选中的第几份`。
815 的教训：判据若读探针换算过的字段，阴性对照就打不中真正的读数。

## ★ 判据

- **S1 ★★ 前提**：每条臂都建出 3 份且**三份坐标全同**、拖拽点**确实落在 pane 上**
  —— 前提不满足 ⟹ **臂显式作废**（807 S7／808 S7 的规矩）。
- **S2 ★★★ 核心**：五条路径合起来，**第 1、2 份从未出现在任何一条路径的选区里**。
- **S3 ★★★**：五条路径的结局**逐条列出来**（清单本身是交付物），且**非退化**。
- **S4 ★★**：静态锚点（四个开关 + liblib 画布**没有** `selectAllNodes`）。
- **S5 ★★★**：Delete **只删掉最后建的那一份**，而**撤销能把三份全带回来**
  ⟹ 撤销是**唯一**够得着底下两份的路径。
- **S6 ★★★** ★ 静态读数与实测**相反**：`page.tsx:1545` 写的是
  「带修饰键**不选**」，实测 Cmd+点击**确实把最后一份加进了选区**。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB816_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch816-2026-10-01"
                    / "raw" / "vb816a.json"))
OUT = pathlib.Path(os.environ.get("VB816_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch816-2026-10-01"
                    / "verify-report.json"))
PAGE = "src/app/page.tsx"

LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]

#: 起点：点之前先把选区挪到源图片上（否则「点中心后没变」会被误读）
P0 = "★ 点之前"
#: 四条**选中**路径 —— 路径清单本身是交付物。
#: ★ 「★ 路径四·Delete 前」**不在这份清单里**：它只是「再点一次中心」
#:   （与路径一完全同一条），在 S5 里当 Delete 的**前提**用。
#:   ★ 第一版把它算进清单、于是「五条」与实际条数对不上 ⟹ **假红**。
PSEL = ["★ 路径一·点中心", "★ 路径二·Cmd+点中心",
        "★ 路径三·Cmd+A", "★ 路径五·拖完选区"]
#: 加上「删除」这条动作 ⟹ 清单共 5 条
PATHS = PSEL + ["★ 路径四·Delete"]

#: 判据在读**哪些 raw 原始字段** —— 阴性对照必须打在这些字段上
F_IDS = "建出来的 id"
F_ZO = "Z 序"
F_SEL = "选区原文"          # 原始 selectedNodeIds
F_DEL_ALIVE = "★ 路径四·删完还活着的 id"
F_BACK_ALIVE = "★ 撤销后活着的 id"
F_PANE = "★ 路径五·拖拽点"
F_V0 = "★ 路径五·拖之前视口"
F_V1 = "★ 路径五·拖之后视口"


def picked(cell, key, ids):
    """★ 重算：这条路径的选区里，落进「叠在一起的那几份」的有哪几份（1-based）"""
    sel = set((cell.get(key) or {}).get(F_SEL) or [])
    return [i + 1 for i, v in enumerate(ids) if v in sel]


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    cells = raw["cells"]
    good = [x for x in cells if not x.get("FAILED")]
    rounds = sorted({x["round"] for x in cells})

    # ── S1 ★★ 前提
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        zo = ((x.get(F_ZO) or {}).get("每份") or {})
        rects = [(v["rect"]["x"], v["rect"]["y"], v["rect"]["w"],
                  v["rect"]["h"]) for v in zo.values() if v]
        pane = x.get(F_PANE) or {}
        pane_cls = pane.get("命中类名") or ""
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "建了几份": len(ids),
                   "★ 坐标全同": bool(rects) and len(set(rects)) == 1,
                   "★ 拖拽点在 pane 上": "react-flow__pane" in pane_cls,
                   "★ 前提成立": len(ids) >= 3 and bool(rects)
                   and len(set(rects)) == 1
                   and "react-flow__pane" in pane_cls})
    add("S1:★★ **前提**：每条臂都建出 3 份、**三份坐标全同**、"
        "拖拽点**确实落在 `.react-flow__pane` 上**",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废、不得据此下结论**。"
        "★ 「拖拽点必须在 pane 上」是**探针返工**留下的：第一版在写死的 "
        "`(40,400)` 上拖，**那个点可能根本不在画布里** ⟹ "
        "「视口没变、也没多选」会被我误读成「框选这条路不存在」—— "
        "★ **夹具失败会伪装成读数**（809/810 的老坑）；"
        "★ 三份坐标全同是 815 的 S5，本批**重新取一次**当前提，不引用上一批的结论",
        bool(ev) and all(x["★ 前提成立"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七个动作一个不落": {x["动作"] for x in ev} == set(LABELS),
         "★ 两轮都跑": len({x["round"] for x in ev}) == len(rounds)})

    # ── S2 ★★★ 核心：底下两份从未被选中过
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        ever = {}
        for key in PSEL:
            for i in picked(x, key, ids):
                ever.setdefault(i, []).append(key.split("·")[0])
        bottom = [i for i in ever if i <= len(ids) - 1]
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "建了几份": len(ids),
                   "逐条路径选中了第几份": {
                       k.split("·")[0]: picked(x, k, ids)
                       for k in PSEL},
                   "★ 哪几份被选中过": sorted(ever),
                   "★ 底下两份被选中过": bottom,
                   "★ 底下两份从未被选中": bottom == []})
    add("S2:★★★ ★ 核心读数：五条路径走完，**底下那两份从未被选中过一次**",
        "★★★ 这正是 815 的「不声称」里点名的那个洞。"
        "★ 判据从**原始 `selectedNodeIds`**（`选区原文`）重算「选中了第几份」，"
        "**不信**探针换算过的 `★ 选中的第几份` —— 815 的教训："
        "判据若读探针换算过的字段，阴性对照就打不中真正的读数；"
        "★ 之所以要**五条路径全走**（807 起立的纪律）："
        "「点不中」既可能是 Z 序问题、也可能是「没有别的路径」，"
        "只点一次分不清这两种成因",
        bool(ev) and all(x["★ 底下两份从未被选中"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         # ★ 修一个**证据字段**的 bug：这里原本读 `x.get(F_IDS)`，
         #   而逐条字典里那个键叫「建了几份」⟹ 恒取到 0 ⟹ 恒为 False。
         #   ★ 教训：**证据字段**也是读数，读错键就会把 14/14 的真读数
         #   印成 False —— 它不参与 `ok`，所以基线照样全绿，
         #   ★ **只有把证据字段也当成读数去核**，才会发现。
         "★ 被选中过的永远是最后建的那一份": all(
             x["★ 哪几份被选中过"] in ([], [x["建了几份"]])
             for x in ev),
         "★ 七个动作一个不落": {x["动作"] for x in ev} == set(LABELS)})

    # ── S3 ★★★ 路径清单
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        ends = {}
        for key in PSEL:
            hit = picked(x, key, ids)
            sel = (x.get(key) or {}).get(F_SEL) or []
            other = len([v for v in sel if v not in set(ids)])
            ends[key] = ("%s ／ 其他选区 %d 个"
                         % ("选中第 %s 份" % hit if hit else "什么都没选中",
                            other))
        ends["★ 路径四·Delete"] = "删掉 %d 份" % (
            len(ids) - len(x.get(F_DEL_ALIVE) or []))
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "结局": ends,
                   "★ 五条一个不缺": len(ends) == 5,
                   "★ 结局非退化（至少三种不同）": len(set(ends.values())) >= 3})
    add("S3:★★★ **路径清单**：**四条选中路径 + 一条删除动作**的结局被**逐条列出来**"
        "（清单本身是交付物），且**非退化**",
        "★★★ 813/814/815 都把「清单」当交付物，本批沿用。"
        "★ 清单是「**四条选中路径 + 一条删除动作**」共 5 条——"
        "第一版把「Delete 之前那次点选」也算成一条、于是「五条」与实际条数对不上 "
        "⟹ **假红**；而它其实就是「再点一次中心」，与路径一同一条，不该另算。"
        "★ 「非退化」这条不能省：若五条路径给出一模一样的答案，"
        "清单就只是一张**恒真的表**（815 的 S3 就栽在这类结构性恒真上）—— "
        "★ 两条互相独立的判据（「一个不缺」「至少三种不同」）都要成立，"
        "少一条清单就会被凑数",
        bool(ev) and all(x["★ 五条一个不缺"]
                         and x["★ 结局非退化（至少三种不同）"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"样例（第一轮·旋转）": next(
            (x["结局"] for x in ev
             if x["round"] == rounds[0] and x["动作"] == "旋转"), None),
         "★ 各臂结局完全一致": len({json.dumps(x["结局"], ensure_ascii=True,
                                          sort_keys=True) for x in ev}) == 1,
         "逐条": ev})

    # ── S4 ★★ 静态锚点
    add("S4:★★ 静态锚点：四个开关都在，且 liblib 画布**没有** `selectAllNodes`",
        "★ 静态证据**不能**替代 S2／S3 的行为证据（794 的硬规矩）；"
        "它的作用是把 S3 的清单**归因**到具体那几个开关，"
        "而不是「这五条路径碰巧都没选中」；"
        "★ `selectAllNodes` 只在 FrameOS 与即梦那两个画布里出现过，"
        "liblib 画布**没有** ⟹ 所以 `Cmd+A` 在这条路径上**没有实现**；"
        "★ 注意 `deleteKeyCode={[]}` 而 `page.tsx:1376` 自己处理 Delete ⟹ "
        "S5 里 Delete **确实**有效果，这一点也由 S5 的读数独立确认",
        ("selectionOnDrag={false}" in src
         and "selectNodesOnDrag={false}" in src
         and "deleteKeyCode={[]}" in src
         and "!event.metaKey && !event.ctrlKey" in src
         and "selectAllNodes" not in src),
        {"selectionOnDrag={false}": "selectionOnDrag={false}" in src,
         "selectNodesOnDrag={false}": "selectNodesOnDrag={false}" in src,
         "deleteKeyCode={[]}": "deleteKeyCode={[]}" in src,
         "★ !event.metaKey && !event.ctrlKey": "!event.metaKey && !event.ctrlKey" in src,
         "★ liblib 画布里没有 selectAllNodes": "selectAllNodes" not in src})

    # ── S5 ★★★ Delete 只删一份 + 撤销全回来
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        alive = x.get(F_DEL_ALIVE) or []
        back = x.get(F_BACK_ALIVE) or []
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "★ 路径四·Delete 前": picked(x, "★ 路径四·Delete 前", ids),
                   "删完还活着的份数": len(alive),
                   "★ 撤销后回来的份数": len(back),
                   "★ 只删掉最后建的那一份":
                       sorted(set(ids) - set(alive)) == [ids[-1]],
                   "★ 撤销把三份全带回来": sorted(set(back)) == sorted(ids)})
    add("S5:★★★ Delete **只删掉最后建的那一份**，而**撤销把三份全带回来**",
        "★★★ 于是「够得着底下那两份」的路径**只剩撤销一条**—— "
        "用户没法选中它们、没法单独删它们、也没法把它们拖走；"
        "★ 读数直接从**原始存活 id 列表**重算（`删完还活着的 id` / "
        "`撤销后活着的 id`），不信探针算好的份数；"
        "★ 814/811 已在 VideoNode 上量过「一次 `Cmd+Z` 回到少一份」，"
        "本批在 ImageNode 上**独立重测**（不引用上一批结论）",
        bool(ev) and all(x["★ 只删掉最后建的那一份"]
                         and x["★ 撤销把三份全带回来"] for x in ev)
        and {x["动作"] for x in ev} == set(LABELS),
        {"逐条": ev,
         "★ 七条动作（去重后）的读数一致": len({json.dumps(
             [x["删完还活着的份数"], x["★ 撤销后回来的份数"]],
             ensure_ascii=True) for x in ev}) == 1})

    # ── S6 ★★★ ★ 静态读数与实测相反
    ev = []
    for x in good:
        ids = x.get(F_IDS) or []
        before = set((x.get("★ 点之前") or {}).get(F_SEL) or [])
        after = set((x.get("★ 路径二·Cmd+点中心") or {}).get(F_SEL) or [])
        ev.append({"round": x.get("round"), "动作": x.get("label"),
                   "Cmd 之前选区": sorted(before),
                   "Cmd 之后选区": sorted(after),
                   "★ 点中了最后一份": ids[-1] in after,
                   "★ 旧选区被保留": before and before <= after,
                   "★ 是累加而不是替换": before and before <= after
                   and ids[-1] in after and after != before})
    add("S6:★★★ ★ 静态读数与实测**相反**：源码说「带修饰键不选」，"
        "实测 **Cmd+点击是把最后一份加进选区**（旧选区保留）",
        "★★★ `page.tsx:1545` 的条件是 `if (!event.metaKey && !event.ctrlKey) "
        "selectNode(node.id)` —— 光读这句会以为「Cmd+点击**什么都不选**」。"
        "★ 实测**不是**：app 自己那次 `selectNode` 被跳过了，"
        "**但 React Flow 内部的累加照样发生**（旧选区里的源图片仍在、"
        "最后一份被加了进来）⟹ ★ **那个静态条件只管住 app 自己那次赋值，"
        "管不住框架内部**；"
        "★ 于是「Cmd+点击能不能救我选中底下那两份」的答案是"
        "**仍然不能**——它加进来的**还是最上面那一份**（S2 的读数）",
        ("!event.metaKey && !event.ctrlKey" in src
         and bool(ev) and all(x["★ 是累加而不是替换"] for x in ev)),
        {"源码那一行": "!event.metaKey && !event.ctrlKey" in src,
         "样例": next((x for x in ev if x["round"] == rounds[0]
                       and x["动作"] == "旋转"), None),
         "逐条": ev})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / PAGE).read_text(encoding="utf-8")
    checks = run_checks(raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def every(cells):
        return [x for x in cells if not x.get("FAILED")]

    def bottom_reachable(d):
        """伪造「第 1 份被某条路径选中了」⟹ S2 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x["★ 路径一·点中心"] = dict(x["★ 路径一·点中心"],
                                      **{F_SEL: [ids[0]]})
            n += 1
        return n

    def click_picks_all(d):
        """伪造「点中心一次选中三份」⟹ S2 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x["★ 路径一·点中心"] = dict(x["★ 路径一·点中心"],
                                      **{F_SEL: list(ids)})
            n += 1
        return n

    def select_all_works(d):
        """伪造「Cmd+A 真的全选了」⟹ S2 与 S3 都必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x["★ 路径三·Cmd+A"] = dict(x["★ 路径三·Cmd+A"], **{F_SEL: list(ids)})
            n += 1
        return n

    def delete_kills_all(d):
        """伪造「Delete 一次删掉三份」⟹ S5 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            if not x.get(F_IDS):
                continue
            x[F_DEL_ALIVE] = []
            n += 1
        return n

    def undo_partial(d):
        """伪造「撤销只回来一份」⟹ S5 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x[F_BACK_ALIVE] = [ids[0]]
            n += 1
        return n

    def not_stacked(d):
        """★ 伪造「三份坐标不全同」（前提坏掉）⟹ S1 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            zo = ((x.get(F_ZO) or {}).get("每份") or {})
            for v in zo.values():
                if v:
                    v["rect"]["x"] += 37
                    n += 1
                    break
        return n

    def pane_point_off(d):
        """★ 伪造「拖拽点其实不在 pane 上」⟹ S1 必须翻红
        （第一版探针就是这么栽的：点可能根本不在画布里）"""
        n = 0
        for x in every(d["cells"]):
            x[F_PANE] = dict(x.get(F_PANE) or {}, 命中类名="liblib-left-rail")
            n += 1
        return n

    def cmd_click_no_accum(d):
        """★ 伪造「Cmd+点击没有累加」（只替换成最后一份）⟹ S6 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x["★ 路径二·Cmd+点中心"] = dict(
                x["★ 路径二·Cmd+点中心"], **{F_SEL: [ids[-1]]})
            n += 1
        return n

    def pane_drag_selects(d):
        """★ 伪造「pane 拖拽多选了三份」⟹ S2 与 S3 必须翻红"""
        n = 0
        for x in every(d["cells"]):
            ids = x.get(F_IDS) or []
            if not ids:
                continue
            x["★ 路径五·拖完选区"] = dict(x["★ 路径五·拖完选区"],
                                       **{F_SEL: list(ids)})
            n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「第 1 份被选中了」⟹ S2 翻红",
            bottom_reachable, "S2"),
        neg("N2", "伪造「点中心一次选中三份」⟹ S2 翻红",
            click_picks_all, "S2"),
        neg("N3", "伪造「Cmd+A 真的全选了」⟹ S2 与 S3 翻红",
            select_all_works, "S2"),
        neg("N4", "伪造「Delete 一次删掉三份」⟹ S5 翻红",
            delete_kills_all, "S5"),
        neg("N5", "伪造「撤销只回来一份」⟹ S5 翻红",
            undo_partial, "S5"),
        neg("N6", "★ 伪造「三份坐标不全同」（前提坏掉）⟹ S1 翻红",
            not_stacked, "S1"),
        neg("N7", "★ 伪造「拖拽点其实不在 pane 上」⟹ S1 翻红",
            pane_point_off, "S1"),
        neg("N8", "★ 伪造「Cmd+点击没有累加」⟹ S6 翻红",
            cmd_click_no_accum, "S6"),
        neg("N9", "★ 伪造「pane 拖拽多选了三份」⟹ S2 与 S3 翻红",
            pane_drag_selects, "S2"),
        neg("N10", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 816,
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"]
              + " ｜ 翻红：" + str([f[:4] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())