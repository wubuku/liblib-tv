#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 819 验收器 —— ★ **用户知不知道自己撤不掉**？

## 起点（818 自开的「本批最该接着做的一条」）

818 量到：连点 60 次 ⟹ 历史封顶在 50 ⟹ **前 10 份永远撤不掉**。
818 只给了**静态推论**：`page.tsx:496` 的 `canUndo = past.length > 0`
传给 `CanvasContextMenu` ⟹ pane 右键菜单的「撤销」随 `past` 空而 disabled
⟹ 撤到底之后 UI 会说「撤销用完了」，而画布上还有 10 份撤不掉的产物。

## ★★ 「扫不到提示」是**否定性读数** ⟹ 必须先证明扫描器没坏

本批要断言的是「**全页没有任何提示告诉用户撤不掉**」。
否定性读数最容易是**探针自己坏了**（选择器太窄、扫的不是可见元素）。

⟹ 所以 raw 里的每一次扫描都带一个**自检读数**：探针往页面注入一个
带 `role=alert` 的探针节点，**必须扫得到它**。
★ S3 的判据**强制要求自检为真** —— 否则这条判据本身就没有意义。
★ 阴性对照 N6 把自检改成 False ⟹ S3 必须翻红，
  证明这条判据真的依赖扫描器的有效性、而不是无条件成立。

## ★ 判据

- **S1 ★★ 前提**：T3 时**确实还剩 > 0 份**、且 `历史 == 0`（两件同时）。
- **S2 ★★★** pane 菜单「撤销」的 disabled 只跟 `past` 走：
  T1 disabled、T2 enabled、T3 disabled ⟹ 与「还剩几份撤不掉」**无关**。
- **S3 ★★★** T3 扫不到任何提示，**且扫描器自检通过**。
- **S4 ★★★** T3 也没有任何**长得不像提示**的文案在讲「撤不掉」。
- **S5 ★★★** T3 再按一次 `Cmd+Z`：节点数与历史都不变，且没有任何提示出现。
- **S6 ★★** pane 右键菜单**有**「撤销」且此刻 disabled；节点右键菜单**没有**。
- **S7 ★★** 静态锚点：`canUndo` 由 `past.length > 0` 决定。
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB819_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch819-2026-10-01"
                    / "raw" / "vb819a.json"))
OUT = pathlib.Path(os.environ.get("VB819_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch819-2026-10-01"
                    / "verify-report.json"))
PAGE = "src/app/page.tsx"
MENU_SRC = "src/components/CanvasContextMenu.tsx"

F_T1 = "★ T1·起点"
F_T2 = "★ T2·连点之后"
F_T3 = "★ T3·撤到底"
F_CMDZ = "★ T3·再按一次 Cmd+Z"
F_MADE = "★ 建出来的 id 数"
F_T4 = "★ T4·横跳"
F_PANE_MENU = "pane菜单"
F_HINT = "提示"
F_SCAN = "扫到"
F_SELFTEST = "★ 扫描器自检：注入探针能被扫到"
F_SAID = "提到撤销的叶子节点"
F_ITEMS = "菜单项"
F_NAME = "名称"
F_DIS = "disabled"

#: 「像提示的措辞」——只认这些，**不把「撤销」二字本身当提示**
#: （菜单项、快捷键弹窗里都有「撤销」，那些**不是**提示）
HINT_RE = re.compile(
    r"无法撤销|不能撤销|撤销不了|撤销已(经)?(用尽|满|达上限|到上限)"
    r"|撤销次数|历史已(经)?(满|达上限|到上限)|已达上限|超出上限"
    r"|上限|无法回退|回退不了|已超出|记录已满")


def menu_items(t, key=F_PANE_MENU):
    return ((t.get(key) or {}).get("菜单") or {}).get(F_ITEMS) or []


def dis_of(t, name, key=F_PANE_MENU):
    for i in menu_items(t, key):
        if i.get(F_NAME) == name:
            return i.get(F_DIS)
    return None


def run_checks(raw, src_page, src_menu):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    good = [x for x in raw["cells"] if not x.get("FAILED")]

    # ── S1 ★★ 前提：T3 时「历史空 ＋ 还剩着东西」同时成立
    ev = []
    for x in good:
        t3 = x.get(F_T3) or {}
        g3 = t3.get("图") or {}
        ev.append({"历史": g3.get("历史"), "节点数": g3.get("节点数"),
                   "★ 还剩几份撤不掉": g3.get("★ 还剩几份撤不掉"),
                   "建了几份": x.get(F_MADE),
                   "★ 前提成立": g3.get("历史") == 0
                   and (g3.get("★ 还剩几份撤不掉") or 0) > 0})
    add("S1:★★ **前提**：T3（撤到底）时**历史为空**、而画布上**还剩着撤不掉的东西**"
        "（两件同时）",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。"
        "★ 这两条同时成立，才构成本批要研究的那个状态 —— "
        "**「撤销已经用完了」与「还有东西没撤掉」并存**。"
        "★ 若「还剩 0 份」，那本来就是干净状态、本批整批问题不成立",
        bool(ev) and all(x["★ 前提成立"] for x in ev),
        {"逐条": ev})

    # ── S2 ★★★ disabled 只跟 past 走
    ev = []
    for x in good:
        t1, t2, t3 = x.get(F_T1) or {}, x.get(F_T2) or {}, x.get(F_T3) or {}
        remain = ((t3.get("图") or {}).get("★ 还剩几份撤不掉"))
        ev.append({
            "T1 历史": (t1.get("图") or {}).get("历史"),
            "T1 撤销 disabled": dis_of(t1, "撤销"),
            "T2 历史": t2.get("历史"),
            "T2 撤销 disabled": dis_of(t2, "撤销"),
            "T3 历史": (t3.get("图") or {}).get("历史"),
            "T3 撤销 disabled": dis_of(t3, "撤销"),
            "T3 还剩几份撤不掉": remain,
            "★ 读数成立": dis_of(t1, "撤销") is True
            and dis_of(t2, "撤销") is False
            and dis_of(t3, "撤销") is True})
    add("S2:★★★ ★ pane 右键菜单「撤销」的 disabled **只跟 `past` 走**"
        "（T1 空 ⟹ disabled；T2 满 ⟹ 可点；T3 空 ⟹ 又 disabled）",
        "★★ 818 的静态推论在这里**取到行为证据**。"
        "★ 关键在 T3：**`past` 明明是空的、画布上却还剩着撤不掉的东西**，"
        "而「撤销」**照样 disabled** ⟹ "
        "★ **这个信号只回答「历史栈空没空」，完全不回答「画布上还有没有撤不掉的东西」**。"
        "★ T1／T2／T3 三点必须**同时**成立才能排除「它恒为 disabled」与"
        "「它恒为 enabled」两种平凡解释",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 菜单项清单（pane 变体）":
             [i.get(F_NAME) for i in menu_items(good[0].get(F_T1) or {})],
         "★ 变体": (((good[0].get(F_T1) or {}).get(F_PANE_MENU) or {})
                   .get("菜单") or {}).get("变体")})

    # ── S3 ★★★ T3 扫不到提示，且扫描器自检通过
    ev = []
    for x in good:
        t3 = x.get(F_T3) or {}
        hint = t3.get(F_HINT) or {}
        scan = hint.get(F_SCAN) or []
        nonempty = [s for s in scan if (s.get("文本") or "").strip()]
        ev.append({"扫到的元素": scan,
                   "★ 其中带非空可见文本的": nonempty,
                   "★ 扫描器自检": hint.get(F_SELFTEST),
                   "★ 探针被扫到几次": hint.get("★ 探针被扫到几次"),
                   "★ 读数成立": nonempty == []
                   and hint.get(F_SELFTEST) is True})
    add("S3:★★★ ★ T3 时**全页没有任何带可见文本的提示**，"
        "**且扫描器自检通过**",
        "★★ 这是本批最核心的一条否定性读数。"
        "★ **判据的第一版是「扫到 0 个元素」—— 基线直接判红**：真实读数是"
        "扫到了 2 个元素（`[aria-live]` 与 `[class*=alert]`），"
        "**但它们两个的文本都是空串**。"
        "★ 修法**不是放宽成「什么都行」**，而是把「提示」定义成"
        "「**带非空可见文本**的元素」—— 一个空容器**在屏幕上显示不出任何东西**，"
        "它不构成提示 ⟹ 判据应当成立、而原判据是**把容器当成了提示**。"
        "★ 而「扫不到」最容易是**探针自己坏了**（选择器太窄、扫的不是可见元素）"
        "⟹ 所以判据**强制要求自检为真**：raw 里的每次扫描都往页面注入一个"
        "带 `role=alert` 的探针节点、**必须扫得到它**。"
        "★ 反向对照 N10 往扫描结果里塞一个**空文本**元素 ⟹ 期望**不翻**，"
        "以此证明判据没有退化成「选择器一个都扫不到」；"
        "★ 而 N5 把自检改成 False ⟹ 必须翻红 —— 否则它就是一条**恒真**的装饰",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 三个时刻扫到的元素（去重）": sorted({
             (s.get("选择器"), s.get("文本"))
             for k in (F_T1, F_T2, F_T3) for x in good
             for s in (((x.get(k) or {}).get(F_HINT) or {}).get(F_SCAN) or [])}),
         "扫描器自检读数": [((x.get(F_T3) or {}).get(F_HINT) or {})
                      .get(F_SELFTEST) for x in good]})

    # ── S4 ★★★ 也没有「长得不像提示」的文案在讲「撤不掉」
    ev = []
    for x in good:
        t3 = x.get(F_T3) or {}
        said = (t3.get(F_HINT) or {}).get(F_SAID) or []
        hits = [s for s in said if HINT_RE.search(s.get("文本") or "")]
        ev.append({"提到撤销的叶子节点": said,
                   "★ 命中「像提示的措辞」的": hits,
                   "★ 读数成立": hits == []})
    add("S4:★★★ ★ 连「长得不像提示」的文案也**没有**在讲「撤不掉」",
        "★★ S3 用的是**选择器** ⟹ 万一提示长得不像 toast（比如就是节点上"
        "一句普通文字、或某处一行灰字）就会被漏掉。"
        "⟹ 所以再加一条**按文字捞**：把所有**叶子节点**里提到"
        "「撤销/历史/还原/回退」的文案全捞出来，"
        "再用一组**「像提示的措辞」**正则去筛。"
        "★ 正则只认「无法撤销/撤销已用尽/上限/…」这类**措辞**，"
        "**不把「撤销」二字本身当提示** —— 菜单项与快捷键弹窗里都有「撤销」，"
        "那些是**控件**不是**提示**",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 提到的叶子节点都是什么": sorted({
             (s.get("文本"), s.get("tag")) for e in ev
             for s in e["提到撤销的叶子节点"]}),
         "用的措辞正则": HINT_RE.pattern})

    # ── S5 ★★★ T3 再按 Cmd+Z：什么都没发生，也没有提示
    ev = []
    for x in good:
        c = x.get(F_CMDZ) or {}
        b, a = c.get("之前") or {}, c.get("之后") or {}
        ap = c.get("★ 之后有没有出现任何提示") or []
        ap_nonempty = [s for s in ap if (s.get("文本") or "").strip()]
        ev.append({"之前": b, "之后": a,
                   "★ 节点数变了": c.get("节点数变了"),
                   "★ 历史变了": c.get("历史变了"),
                   "★ 之后出现的提示元素": ap,
                   "★ 其中带非空文本的": ap_nonempty,
                   "★ 扫描器自检": c.get("★ 扫描器自检"),
                   "★ 读数成立": c.get("节点数变了") is False
                   and c.get("历史变了") is False
                   and ap_nonempty == []
                   and c.get("★ 扫描器自检") is True})
    add("S5:★★★ ★ T3 再按一次 `Cmd+Z`：**什么都没发生**，也**没有任何提示**",
        "★★ `undo()` 在 `past` 为空时 `return state` ⟹ **静默 no-op**"
        "（811 已记过空历史 `Cmd+Z` 是安全 no-op）。"
        "★ 本条问的是**用户能不能从这一步看出「撤不动了」** —— "
        "节点数不变、历史不变、**一条提示都没有** ⟹ "
        "★ 用户唯一的反馈是「按了没反应」",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev})

    # ── S6 ★★ pane 有「撤销」且 disabled；节点菜单没有「撤销」
    ev = []
    for x in good:
        t3 = x.get(F_T3) or {}
        pane_names = [i.get(F_NAME) for i in menu_items(t3)]
        node_names = [i.get(F_NAME) for i in
                      menu_items(t3, "节点右键菜单")]
        ev.append({"pane 菜单项": pane_names, "节点菜单项": node_names,
                   "★ pane 变体": ((t3.get(F_PANE_MENU) or {})
                                  .get("菜单") or {}).get("变体"),
                   "★ 节点变体": ((t3.get("节点右键菜单") or {})
                                  .get("菜单") or {}).get("变体"),
                   "★ pane 有「撤销」": "撤销" in pane_names,
                   "★ 节点菜单**没有**「撤销」": "撤销" not in node_names,
                   "★ 读数成立": "撤销" in pane_names
                   and "撤销" not in node_names})
    add("S6:★★ pane 右键菜单**有**「撤销」；**节点右键菜单没有**",
        "★★ `CanvasContextMenu.tsx` 的两个变体：pane 六项"
        "（上传／保存到我的资产／添加节点／撤销／重做／粘贴），"
        "node 七项（保存到我的资产／创建主体／复制节点／创建副本／粘贴／删除／复制到剪贴板）"
        "⟹ ★ 节点右键菜单**没有**「撤销」项 —— "
        "★ 这不是死路（键盘 `⌘Z` 还在），但它意味着**右键这条路走不到撤销**",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev})

    # ── S7 ★★ 静态锚点
    m = re.search(r"const canUndo = \((.*?)\) > 0", src_page)
    add("S7:★★ 静态锚点：`canUndo` 就是 `past.length > 0`，"
        "且菜单的「撤销」项由它决定 disabled",
        "★ 静态证据**不能**替代 S2 的行为证据（794 的硬规矩）；"
        "它的作用是把 S2 的读数**归因**到具体那两行，"
        "而不是「菜单碰巧是那样」。"
        "★ 这一条同时把 S2 的结论**钉死**在实现上："
        "判据里用的量就是 `past` 的长度，"
        "★ 而「画布上还剩几份撤不掉」这个量**根本不在判据里**",
        bool(m) and "past" in (m.group(1) or "")
        and 'data-canvas-context-item="撤销"' in src_menu
        and "disabled={!canUndo}" in src_menu,
        {"canUndo 的定义": m.group(0) if m else None,
         "菜单里有撤销项": 'data-canvas-context-item="撤销"' in src_menu,
         "撤销项用 canUndo 设 disabled": "disabled={!canUndo}" in src_menu})

    # ── S8 ★★★ 横跳窄路：能再撤销，但**回不到起点**
    ev = []
    for x in good:
        t3g = (x.get(F_T3) or {}).get("图") or {}
        t4 = x.get(F_T4) or {}
        pts = [(k, t4.get(k) or {}) for k in
               ("T3 之后", "重做一次之后", "连按 12 次重做之后")]
        back = [p for _, p in pts if p.get("★ 回到起点")]
        ns = [p.get("节点数") for _, p in pts]
        ev.append({"采样点": {k: v for k, v in pts},
                   "★ T3 之后 历史": t3g.get("历史"),
                   "★ 重做一次之后 历史": (t4.get("重做一次之后") or {}).get("历史"),
                   "★ 重做之后撤销又可按（历史 > 0）":
                       ((t4.get("重做一次之后") or {}).get("历史") or 0) > 0,
                   "★ 各采样点节点数": ns,
                   "★ 节点数单调不减": all(a <= b for a, b in zip(ns, ns[1:])),
                   "★ 回到起点的采样点": back,
                   "★ 一个采样点都没回到起点": back == [],
                   "★ 读数成立": ((t4.get("重做一次之后") or {}).get("历史") or 0) > 0
                   and back == []
                   and all(a <= b for a, b in zip(ns, ns[1:]))})
    add("S8:★★★ ★ 有一条**横跳窄路**：T3 按一次重做，撤销**又变回可按**；"
        "但沿窄路走的每一个采样点**都没有回到起点**，且节点数**单调不减**",
        "★★★ 这是对「撤不掉」的**重要修正**：不是「完全无解」。"
        "`redo()`（`canvasStore.ts:3965`）会把当前快照**推回 `past`** ⟹ "
        "T3（`past` 空、`future` 50 条）按一次重做，**撤销就又能按了**。"
        "★ 但窄路**只是横跳**：`future` 只能往前走，"
        "沿它走的采样点**没有一个等于起点**（10 节点／历史 0），"
        "而节点数**单调不减**（每一份产物又回来了）。"
        "★ ★ 而 UI 里**没有任何文案**说这条窄路存在 —— "
        "S3／S4 证明了 T3 时全页没有任何带文本的提示",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 窄路起点（T3）": next(
             ({"节点数": (e.get("采样点") or {}).get("T3 之后", {}).get("节点数"),
               "历史": (e.get("采样点") or {}).get("T3 之后", {}).get("历史")}
              for e in ev), None)})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_page = (ROOT / PAGE).read_text(encoding="utf-8")
    src_menu = (ROOT / MENU_SRC).read_text(encoding="utf-8")
    checks = run_checks(raw, src_page, src_menu)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_page, src_menu)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def good_of(d):
        return [x for x in d["cells"] if not x.get("FAILED")]

    def hist_not_empty(d):
        """伪造「T3 时历史不为空」⟹ S1 翻红（前提坏掉）"""
        n = 0
        for x in good_of(d):
            x[F_T3]["图"]["历史"] = 7
            n += 1
        return n

    def nothing_left(d):
        """伪造「T3 时一份都没剩」⟹ S1 翻红（那本来就是干净状态）"""
        n = 0
        for x in good_of(d):
            x[F_T3]["图"]["★ 还剩几份撤不掉"] = 0
            n += 1
        return n

    def undo_always_enabled(d):
        """伪造「撤销项恒为可点」⟹ S2 翻红（排除平凡解释）"""
        n = 0
        for x in good_of(d):
            for k in (F_T1, F_T2, F_T3):
                for i in (x[k][F_PANE_MENU]["菜单"][F_ITEMS]):
                    if i.get(F_NAME) == "撤销":
                        i[F_DIS] = False
                        n += 1
        return n

    def hint_exists(d):
        """伪造「T3 时有一条提示」⟹ S3 翻红"""
        n = 0
        for x in good_of(d):
            x[F_T3][F_HINT][F_SCAN] = [
                {"选择器": "[role=alert]", "文本": "撤销已达上限"}]
            n += 1
        return n

    def selftest_broken(d):
        """★★ 伪造「扫描器自检失败」⟹ S3 必须翻红
        （否则「扫不到」这条读数没有证据支撑，是装饰）"""
        n = 0
        for x in good_of(d):
            x[F_T3][F_HINT][F_SELFTEST] = False
            n += 1
        return n

    def hint_worded(d):
        """伪造「有一条长得不像提示、但文案在讲撤不掉」⟹ S4 翻红"""
        n = 0
        for x in good_of(d):
            x[F_T3][F_HINT][F_SAID] = [
                {"文本": "撤销", "tag": "BUTTON", "禁用": True},
                {"文本": "撤销记录已达上限", "tag": "P", "禁用": False}]
            n += 1
        return n

    def cmdz_does_something(d):
        """伪造「T3 再按 Cmd+Z 节点数变了」⟹ S5 翻红"""
        n = 0
        for x in good_of(d):
            x[F_CMDZ]["节点数变了"] = True
            n += 1
        return n

    def node_menu_has_undo(d):
        """伪造「节点右键菜单里有撤销项」⟹ S6 翻红"""
        n = 0
        for x in good_of(d):
            x[F_T3]["节点右键菜单"]["菜单"][F_ITEMS].append(
                {"名称": "撤销", "disabled": True})
            n += 1
        return n

    def empty_hint_element(d):
        """★ 反向对照：往扫描结果里塞一个**空文本**的元素 ⟹ 期望**不翻**
        （守住 S3 的边界：判据问的是「有没有**带文本**的提示」，
        不是「选择器一个都扫不到」—— 否则它和坏掉的扫描器长得一样）"""
        n = 0
        for x in good_of(d):
            scan = x[F_T3][F_HINT][F_SCAN]
            scan.append({"选择器": "[aria-live]", "文本": ""})
            scan.append({"选择器": "[role=status]", "文本": "   "})
            n += 1
        return n

    def t4_unreachable(d):
        """伪造「窄路某一步回到了起点」⟹ S8 翻红"""
        n = 0
        for x in good_of(d):
            t4 = x.get(F_T4) or {}
            if not t4.get("重做一次之后"):
                continue
            t4["重做一次之后"]["★ 回到起点"] = True
            n += 1
        return n

    def t4_undo_still_dead(d):
        """伪造「重做之后撤销仍然不可按」⟹ S8 翻红"""
        n = 0
        for x in good_of(d):
            t4 = x.get(F_T4) or {}
            if not t4.get("重做一次之后"):
                continue
            t4["重做一次之后"]["历史"] = 0
            n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「T3 时历史不为空」⟹ S1 翻红（前提坏掉）",
            hist_not_empty, "S1"),
        neg("N2", "伪造「T3 时一份都没剩」⟹ S1 翻红（那本来就是干净状态）",
            nothing_left, "S1"),
        neg("N3", "★ 伪造「撤销项恒为可点」⟹ S2 翻红"
                  "（排除「它恒为 disabled/恒为 enabled」两种平凡解释）",
            undo_always_enabled, "S2"),
        neg("N4", "伪造「T3 时有一条提示」⟹ S3 翻红", hint_exists, "S3"),
        neg("N5", "★★ 伪造「扫描器自检失败」⟹ S3 必须翻红"
                  "（否则「扫不到」这条读数没有证据支撑）", selftest_broken, "S3"),
        neg("N6", "★ 伪造「有一条长得不像提示、但文案在讲撤不掉」⟹ S4 翻红",
            hint_worded, "S4"),
        neg("N7", "伪造「T3 再按 Cmd+Z 节点数变了」⟹ S5 翻红",
            cmdz_does_something, "S5"),
        neg("N8", "伪造「节点右键菜单里有撤销项」⟹ S6 翻红",
            node_menu_has_undo, "S6"),
        neg("N9", "★ 伪造「窄路某一步回到了起点」⟹ S8 翻红",
            t4_unreachable, "S8"),
        neg("N10", "★ 伪造「重做之后撤销仍然不可按」⟹ S8 翻红",
            t4_undo_still_dead, "S8"),
        neg("N11", "★ 反向对照：往扫描结果里塞**空文本**元素 ⟹ 期望**不翻**"
                   "（守住 S3 的边界：问的是「有没有带文本的提示」）",
            empty_hint_element, "__NO_FLIP__"),
        neg("N12", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 819,
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