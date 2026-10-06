#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 803 验收器 —— 独立实现，不 import 探针

## 本批是什么

803 是**纯测量批次**：`src/` 一行没改。目的是把 750 留的待拍板 ③「导演台撤销/
重做要不要给按钮」从一句待办，变成**带读数的判断**。

## 本批要防的错误方向

- 测量批次最容易犯的错是**先有结论再填数字**。所以每条判据都要求**从 raw 独立重算**，
  而不是复述探针写好的布尔字段。
- ★ **「放不下」不能靠「余量是个小数」蒙混**：余量小不等于放不下，必须把「两个按钮
  需要多少」算出来，而那个数**从读数里反推** —— 拿右列里**现成的同类按钮**宽度当
  参照（不写死 `size-8 = 32px` 这个常量）。
- ★ **格 4 的主结论必须带格内阳性对照**：没有「重载前撤销确实是活的」这一读数，
  「重载后撤销失效」同样可以由「整格都坏了」造成。
- ★ **阴性对照要打在性质真正读取的字段上**（801/802 各踩过一次）。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
RAW = ROOT / "docs/research/liblib-canvas-batch803-2026-10-01/raw/vb803a-pre.json"
REPORT = ROOT / "docs/research/liblib-canvas-batch803-2026-10-01/verify-report.json"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cnt(x):
    """读数可能是 {count: n}，也可能根本不存在（前提不满足时探针会不记）。"""
    return None if not isinstance(x, dict) else x.get("count")


def rounds_of(raw):
    return [r for r in raw.get("rounds", []) if not r.get("reloadPersistence", {})
            .get("FAILED")]


# ── 独立重算：右列到底还剩多少、两个按钮要多少 ────────────────────────────
def budget_recompute(col):
    """★ 不复述探针的 budget 字段，自己按 flex 排布算一遍。

    容器 `box-sizing: border-box`、左右 padding 各 12 ⟹ 内宽 = 宽 − 24；
    子元素之间 gap 共 (n−1) 段；余量 = 内宽 − 子元素宽之和 − gap 之和。
    """
    if not col or not col.get("found"):
        return None
    cs = col["col"]["computed"]
    w = col["col"]["rect"]["w"]
    # `padding` 简写可能是 1/2/3/4 个值（实测就是单值 `12px`）⟹ 横向内边距取左右两个
    parts = [float(x.replace("px", "")) for x in cs["padding"].split()]
    if len(parts) >= 4:
        pad = parts[1]                      # 左
        assert parts[1] == parts[3], "左右 padding 不等，S2 的算法要重写"
    elif len(parts) == 2:
        pad = parts[1]
    elif len(parts) == 1:
        pad = parts[0]
    else:
        pad = 0.0
    gap = float(cs["gap"].replace("px", ""))   # 实测形如 "8px"
    kids = col["kids"]
    kid_w = [k["rect"]["w"] for k in kids]
    inner = w - 2 * pad
    used = sum(kid_w) + gap * max(0, len(kid_w) - 1)
    return {"inner": inner, "used": used, "gap": gap, "kids": kid_w,
            "slack": inner - used, "reported": col["budget"]}


def two_buttons_need(budget, col):
    """两个图标按钮需要多少 —— **从读数反推**，不写死 32px。

    参照物 = 右列里**现成的同类按钮**（导入/导出那几枚）的实测宽度。
    拿不到的就把 `need` 记 None，让判据红，而不是替它猜一个。
    """
    btn_w = [k["rect"]["w"] for k in col["kids"]
             if k["tag"] == "BUTTON" and k["rect"]["w"] > 0]
    if not btn_w:
        return None, {"why": "右列里取不到现成的按钮宽度当参照"}
    w = min(btn_w)                       # 取最小那枚 = 最保守
    need = 2 * w + 2 * budget["gap"]     # 两枚按钮 + 两段新增 gap
    return need, {"参照按钮宽": w, "参照来源": "右列里现成的 BUTTON 实测宽度",
                  "gap": budget["gap"]}


def run_checks(raw):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    rs = rounds_of(raw)
    live_u = [r for r in rs if not r.get("undoKeyboard", {}).get("FAILED")
              and not r.get("undoKeyboard", {}).get("INVALID")]
    live_p = [r for r in rs if not r.get("reloadPersistence", {}).get("FAILED")]

    # ── S1 两轮几何逐位相同（读数可复现，不是碰巧一次）
    ev, sig = [], []
    for r in rs:
        col = r["headerRightColumn"]
        b = budget_recompute(col)
        s = (col["col"]["rect"]["w"], tuple(k["rect"]["w"] for k in col["kids"]))
        sig.append(s)
        ev.append({"round": r["round"], "容器宽": s[0],
                   "子元素宽": list(s[1]),
                   "独立重算余量": b["slack"] if b else None,
                   "探针自报余量": (col.get("budget") or {}).get("slack"),
                   "两者一致": (b is not None and
                                abs(b["slack"] - col["budget"]["slack"]) < 1e-9)})
    add("S1:★★ 两轮几何读数**逐位相同**，且余量能被独立重算复现",
        "★ 测量批次的基本要求：读数要能复现；且余量不能只信探针自报的那个字段",
        len(sig) == 2 and sig[0] == sig[1] and all(x["两者一致"] for x in ev),
        ev)

    # ── S2 ★ 右列**算出来**放不下两个按钮（需要的宽度从读数反推）
    ev = []
    for r in rs:
        col = r["headerRightColumn"]
        b = budget_recompute(col)
        need, how = two_buttons_need(b, col) if b else (None, {})
        if b is None or need is None:
            ev.append({"round": r["round"], "ok": False, "why": how})
            continue
        ev.append({"round": r["round"], "余量": b["slack"], "需要": need,
                   "放得下": b["slack"] >= need, "缺的": need - b["slack"],
                   "参照": how})
    add("S2:★★ 右列**算出来**放不下两个按钮（需要的宽度从现成按钮反推）",
        "★★ 「余量是个小数」不等于「放不下」 ⟹ 必须把「两个按钮要多少」算出来；"
        "而那个数**不写死 size-8=32px**，拿右列里现成的 BUTTON 实测宽度当参照",
        ev and all(x.get("放得下") is False for x in ev), ev)

    # ── S3 右列每个子元素都被**独立点名**（不是只报个数）
    ev = []
    for r in rs:
        for k in r["headerRightColumn"]["kids"]:
            # ★ `bool(k["data"])` 而不是 `json.dumps(...)` —— 后者对空字典
            #   返回字符串 `"{}"`，**恒为真**，会让这一项永远通过（我自己写错过）。
            own_named = bool(k["ariaLabel"] or k["title"] or k["text"]
                             or k["data"])
            nested = k.get("nested") or []
            nested_named = [n for n in nested
                            if any(x for x in [n.get("ariaLabel"), n.get("title"),
                                               n.get("text")])]
            ev.append({"round": r["round"], "i": k["i"], "tag": k["tag"],
                       "宽": k["rect"]["w"], "高": k["rect"]["h"],
                       "自身可命名": own_named,
                       "内层可命名": len(nested_named) > 0,
                       # ★ 只要求**宽度**为正：右列是横向预算，高度不参与计算。
                       #   反馈层 `data-director-project-io-feedback` 实测
                       #   **高为 0**（空文案时），它照样占 8px 宽度。
                       "宽度为正": k["rect"]["w"] > 0,
                       "高度为正": k["rect"]["h"] > 0,
                       "★ 至少一处能命名": own_named or len(nested_named) > 0,
                       "自身身份": k["ariaLabel"] or k["title"] or k["text"]
                               or (json.dumps(k["data"], ensure_ascii=False)
                                   if k["data"] else None),
                       "内层身份": [(n.get("ariaLabel") or n.get("title")
                                      or n.get("text")) for n in nested_named][:3]})
    add("S3:★★ 右列每个子元素都能被独立点名（自身或内层），且宽度为正",
        "★★ 只报「余量 7.33」而不点名每个子元素 ⟹ 换个数法结论就变了（我自己"
        "静态估成 3 个子元素、余量 176px，实测是 5 个、7.33px）；★ 「点名」"
        "必须允许**内层** —— 右列有一枚匿名包裹层（div.relative 装导出按钮），"
        "自身既无 aria-label 也无文本；★ 只要求宽度：反馈层实测**高为 0**",
        ev and len(ev) > 0 and all(x["★ 至少一处能命名"] and x["宽度为正"]
                                  for x in ev),
        {"子元素总数": len(ev), "高度为 0 的": [x["i"] for x in ev
                                            if not x["高度为正"]],
         "逐个": ev})

    # ── S4 撤销/重做普查命中 0，且命中判定**逐条给出命中字段**
    ev = []
    for r in rs:
        c = r["interactiveCensus"]
        ev.append({"round": r["round"], "可交互": c["total"], "命中": c["hits"],
                   "which": c["which"],
                   "★ 五条路都查过": c["which"] == []})
    add("S4:★★ 撤销/重做入口普查命中 **0**（独立复核 750 的「151 个里 0 入口」）",
        "★ 命中判定必须能逐条检查「命中了哪个字段」，只给一个布尔就等于没查",
        ev and all(x["命中"] == 0 and x["★ 五条路都查过"] == True for x in ev), ev)

    # ── S5 格 3 阳性对照：同会话内撤销/重做完整往返
    ev = []
    for r in live_u:
        u = r["undoKeyboard"]
        ev.append({"round": r["round"], "起点": cnt(u["before"]),
                   "建后": cnt(u["afterCreate"]), "撤销后": cnt(u["afterUndo"]),
                   "重做后": cnt(u["afterRedo"]),
                   "往返成立": cnt(u["before"]) == 0 and cnt(u["afterCreate"]) == 1
                             and cnt(u["afterUndo"]) == 0
                             and cnt(u["afterRedo"]) == 1,
                   "点中的预设": u["clickedPreset"].get("preset")})
    add("S5:★ 格 3 阳性对照：`path-count` 走满 0→1→0→1",
        "★ 它证明「撤销有 DOM 后果、而且后果可测」 ⟹ 否则后面「撤销失效」无从谈起",
        ev and all(x["往返成立"] for x in ev), ev)

    # ── S6 格 3 起点前提闸
    ev = [{"round": r["round"], "起点": cnt(r["undoKeyboard"]["before"]),
           "ensureZero": r["undoKeyboard"].get("ensureZero")}
          for r in live_u]
    add("S6:★★ 每一格起点 `path-count` **确实是 0**（前提闸）",
        "★★ 第一版假设「goto 重新加载 = 回到起点」，被读数打脸（第二轮起点是 1）；"
        "第二版改用「反复 Cmd+Z 撤回 0」，**连按 6 次一次都没降** ⟹ 因为文档被"
        "持久化而历史栈没有 ⟹ 第三版改成**每轮一个全新 context**",
        ev and all(x["起点"] == 0 and (x["ensureZero"] or {}).get("ok") for x in ev),
        ev)

    # ── S7 ★ 格 4 格内阳性对照
    ev = [{"round": r["round"],
           "建后": cnt(r["reloadPersistence"]["afterCreate"]),
           "格内撤销": cnt(r["reloadPersistence"]["inCellUndo"]),
           "格内重做": cnt(r["reloadPersistence"]["inCellRedo"]),
           "成立": cnt(r["reloadPersistence"]["inCellUndo"]) == 0
                 and cnt(r["reloadPersistence"]["inCellRedo"]) == 1}
          for r in live_p]
    add("S7:★★★ 格 4 **格内**阳性对照：重载之前撤销确实是活的",
        "★★★ 没有这一读数，「重载后撤销失效」同样可以由「整格导演台都坏了」造成",
        ev and all(x["成立"] for x in ev), ev)

    # ── S8 ★ 格 4 主结论：文档存活 **且** 撤销失效
    ev = [{"round": r["round"],
           "建后": cnt(r["reloadPersistence"]["afterCreate"]),
           "重载后": cnt(r["reloadPersistence"]["afterReload"]),
           "重载后连按": r["reloadPersistence"]["undoAfterReload"],
           "文档存活": cnt(r["reloadPersistence"]["afterReload"])
                     == cnt(r["reloadPersistence"]["afterCreate"]),
           "撤销失效": not any(c == 0 for c in
                             r["reloadPersistence"]["undoAfterReload"]),
           "★ 必须同时成立": (cnt(r["reloadPersistence"]["afterReload"])
                              == cnt(r["reloadPersistence"]["afterCreate"])
                              and not any(c == 0 for c in
                                          r["reloadPersistence"]["undoAfterReload"]))}
          for r in live_p]
    add("S8:★★★ 格 4 主结论：重载后**文档存活、撤销失效**（两件事同时成立）",
        "★★ 只测一半会得出相反的结论：只看到「文档还在」像是持久化做对了；"
        "只看到「撤销没反应」像是功能坏了 ⟹ 两件事**同时**成立才是真事实",
        ev and all(x["★ 必须同时成立"] for x in ev), ev)

    return checks


def main():
    raw0 = json.loads(RAW.read_text(encoding="utf-8"))
    raw_sha = sha(RAW)

    checks = run_checks(raw0)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw0)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d)
        flipped = [x["id"] for x in c if not x["ok"]]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def shrink_object_name(d):
        """★ 把**对象名 SPAN** 压窄，看会不会「放得下」。

        第一版 N1 去改探针自报的 `budget.slack = 999` ⟹ 翻红的是 **S1**（独立重算
        与自报不一致）而不是 S2。★ 原因是 S2 读的是**独立重算**出来的余量、
        不读自报字段 ⟹ 对照必须打在几何本身（801/802 又一次同款教训）。

        顺带这是一件**有决策含义**的假设：对象名 SPAN 是 `min-width:0` +
        `overflow:hidden`，**它可以被压缩** ⟹ 「放不下」的前提是
        **不牺牲对象名可读性**。压掉多少算够，由 S2 自己算，我不替它定。
        """
        touched = False
        for r in d["rounds"]:
            for k in r["headerRightColumn"]["kids"]:
                if k["data"].get("data-director-header-object-name"):
                    k["rect"]["w"] = max(0.0, k["rect"]["w"] - 80.0)
                    touched = True
        return touched

    def set_hits(d):
        for r in d["rounds"]:
            c = r.get("interactiveCensus")
            if not c:
                return False
            c["hits"] = 1              # 声称存在一个撤销入口
            c["which"] = [{"i": 0, "tag": "BUTTON", "inText": True,
                           "inAria": True, "inTitle": False,
                           "inDataName": False, "inDataValue": False,
                           "text": "撤销", "ariaLabel": "撤销", "title": None}]
        return True

    def undo_alive(d):
        for r in d["rounds"]:
            p = r.get("reloadPersistence")
            if not p or p.get("FAILED"):
                return False
            p["undoAfterReload"] = [1, 0, 1]      # 声称重载后撤销还活着
        return True

    def doc_died(d):
        for r in d["rounds"]:
            p = r.get("reloadPersistence")
            if not p or p.get("FAILED"):
                return False
            p["afterReload"] = {"present": True, "count": 0}   # 文档没存活
        return True

    def drift_round1(d):
        r = d["rounds"][1]
        k = r["headerRightColumn"]["kids"][0]
        k["rect"]["w"] = k["rect"]["w"] + 1.0     # 只动一个子元素 1 像素
        return True

    def touch_unrelated(d):
        for r in d["rounds"]:
            r["headerRightColumn"]["col"]["className"] += " /* touched */"
        return True

    negs = [
        neg("N1 ★★★ raw：把**对象名 SPAN** 压窄 80px（牺牲可读性换空间）",
            "★★★ 验证 S2 真的在算「放得下/放不下」。★ 第一版改探针自报的 "
            "slack，翻红的是 S1 而不是 S2 ⟹ S2 读的是**独立重算**的余量，"
            "对照必须打在几何本身（801/802 同款教训）",
            shrink_object_name,
            "S2:★★ 右列**算出来**放不下两个按钮（需要的宽度从现成按钮反推）"),
        neg("N2 ★★ raw：声称存在 1 个撤销入口",
            "★ 验证 S4 抓的是「命中数」而不是「which 列表非空」这种自证",
            set_hits, "S4:★★ 撤销/重做入口普查命中 **0**（独立复核 750 的「151 个里 0 入口」）"),
        neg("N3 ★★ raw：声称重载后撤销还活着",
            "★ 验证 S8 抓的是「撤销失效」这件事",
            undo_alive, "S8:★★★ 格 4 主结论：重载后**文档存活、撤销失效**（两件事同时成立）"),
        neg("N4 ★★ raw：声称重载后文档没存活",
            "★★ 验证 S8 的「同时成立」是**合取**不是析取：只死一半必须翻红",
            doc_died, "S8:★★★ 格 4 主结论：重载后**文档存活、撤销失效**（两件事同时成立）"),
        neg("N5 ★★ raw：只把第二轮某个子元素宽度改 1 像素",
            "★ 验证 S1 真的在逐位比对两轮，而不是「两轮都跑过了就算」",
            drift_round1, "S1:★★ 两轮几何读数**逐位相同**，且余量能被独立重算复现"),
        neg("N6 ★★ 反向对照：只动一个与判据无关的字段（className）",
            "★ 证明 S1/S2 锚的是几何读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    assert sha(RAW) == raw_sha, "★ 阴性对照是纯内存变异，raw 不该被改"

    negs_ok = sum(1 for n in negs if n["ok"])
    report = {"batch": 803, "phase": "pre", "totals": {"passed": nPass,
                                                        "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": negs_ok, "negativesTotal": len(negs),
              "rawSha": raw_sha, "srcUntouched": True}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (negs_ok, len(negs)))
    return 0 if (nPass == len(checks) and negs_ok == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())