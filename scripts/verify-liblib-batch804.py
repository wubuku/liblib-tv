#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 804 验收器 —— 独立实现，不 import 探针

## 修的是什么

759 ①（高严重度、挂了 40+ 批次未修）：`/project` 点画布卡开出的新标签页，
**不是你点的那张**。`activeCanvasId` 只活在当前标签页内存里，新标签页有自己的
store 实例，从 `canvasStore.ts:1175` 的默认值 `canvas-2` 起步。

## 本批要防的错误方向

★★ **最关键的一条：不能只跑一个方向。** 默认 active 就是 `canvas-2`，所以
  「点 canvas-2 打开 canvas-2」这条臂在**修复前也是绿的**——它是**默认蒙对**，
  不是功能生效。只跑这一臂会把「完全没修」判成「已修」。S2 专门把这一点拆穿。
- ★ 判据只认 DOM：新标签页「显示的是哪张画布」用 `[data-canvas-active="true"]`
  读，**不读 store**（store 读数只用于「本标签页是否跟着走」这条无回归声明）。
- ★ 「id 对了」不等于「修好了」：还要**内容**对。两张画布节点数 0 / 10 不同，
  S4 借此确认内容真的换了，而不只是标签换了个字符串。
- ★ 修复引入了「新路径」（从 URL 读 id 并切画布）⟹ 它自带一个**新失败模式**：
  参数坏了会怎样。不测它等于把新风险放进代码却不看它（S7）。
- ★ 阴性对照要打在性质真正读取的字段上（801/802/803 各踩过）。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
D = ROOT / "docs/research/liblib-canvas-batch804-2026-10-01"
PRE = D / "raw/vb804a-pre.json"
POST = D / "raw/vb804a-post.json"
REPORT = D / "verify-report.json"
PROJ = "src/app/project/page.tsx"
HOME = "src/app/page.tsx"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def arms_of(raw):
    out = []
    for r in raw.get("rounds", []):
        for a in r.get("arms", []):
            if not a.get("FAILED"):
                out.append((r["round"], a))
    return out


def by_target(raw, target):
    return [a for _, a in arms_of(raw) if a.get("target") == target]


def run_checks(pre_raw, post_raw, proj_src, home_src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    pre_arms, post_arms = arms_of(pre_raw), arms_of(post_raw)

    # ── S1 缺陷复现：pre 里点 canvas-1，开出来的**不是**它
    ev = [{"round": r, "target": a["target"],
           "新标签页显示": a["newTab"]["activeCanvasId"],
           "节点": a["newTab"]["reactFlowNodes"],
           "★ 不是点的": a["newTab"]["activeCanvasId"] != a["target"]}
          for r, a in pre_arms if a["target"] != a["newTab"]["activeCanvasId"]]
    add("S1:★★ 缺陷复现：pre 里点一张卡，新标签页显示的是**另一张**",
        "★ 缺陷本体，全部用 DOM 读数判定（不读 store）",
        ev and len(ev) >= 2, ev)

    # ── S2 ★★ 「点默认那张」在 pre 里也是绿的 —— 它是**蒙对**不是功能
    ev = []
    for r, a in pre_arms:
        if a["newTab"]["activeCanvasId"] != a["target"]:
            continue
        ev.append({"round": r, "target": a["target"],
                   "★ 新标签页 URL": a["newTabUrl"],
                   "URL 里带目标参数": "?canvas=" in a["newTabUrl"],
                   "结论": "pre 里这条臂是绿的，但 URL 里根本没有目标参数 "
                           "⟹ 它只是**默认 active 恰好就是这张**，不构成功能证据"})
    add("S2:★★★ pre 里「点 canvas-2」那条臂是**默认蒙对**，不构成功能证据",
        "★★★ 默认 active 就是 canvas-2 ⟹ 只跑这一个方向会把「完全没修」"
        "判成「已修」。★ 判据不是「这条臂红不红」，而是「它绿的时候，"
        "URL 里到底有没有携带目标」",
        ev and all(x["URL 里带目标参数"] is False for x in ev), ev)

    # ── S3 修复生效：post 里两个方向都对
    ev = [{"round": r, "target": a["target"],
           "新标签页显示": a["newTab"]["activeCanvasId"],
           "★ 显示的就是点的": a["showsTarget"]}
          for r, a in post_arms]
    add("S3:★★★ 修复生效：post 里**两个方向**都显示你点的那张",
        "★ 两个方向都要跑 —— 单方向有「默认蒙对」的假绿（见 S2）",
        ev and len(ev) >= 4 and all(x["★ 显示的就是点的"] for x in ev), ev)

    # ── S4 ★★ 不只是 id：内容也得跟着换
    ev = []
    for r in sorted({rr for rr, _ in post_arms}):
        rs = [a for rr, a in post_arms if rr == r]
        counts = {a["target"]: a["newTab"]["reactFlowNodes"] for a in rs}
        ids = {a["target"]: a["newTab"]["activeCanvasId"] for a in rs}
        # 每张画布自己的节点数在两轮之间必须稳定
        stable = True
        for rr2 in sorted({x for x, _ in post_arms}):
            for a in [y for x, y in post_arms if x == rr2]:
                if a["newTab"]["reactFlowNodes"] != counts[a["target"]]:
                    stable = False
        ev.append({"round": r, "逐张": counts, "逐张id": ids,
                   "★ 节点数互不相同": len(set(counts.values())) == len(counts),
                   "两轮稳定": stable,
                   "★ 内容确实换了": len(set(counts.values())) == len(counts)
                                 and stable})
    add("S4:★★ 不只是 id 对了 —— **内容**也跟着换（两张画布节点数互不相同）",
        "★★ 「activeCanvasId 等于目标」也可能只是把标签换了个字符串；"
        "种子数据里 canvas-1 是 0 节点、canvas-2 是 10 节点 ⟹ 两者互不相同"
        "且两轮稳定，才能说明画布真的换了",
        ev and all(x["★ 内容确实换了"] for x in ev), ev)

    # ── S5 URL 带参数
    ev = [{"round": r, "target": a["target"], "URL": a["newTabUrl"],
           "★ 带了": "?canvas=" + a["target"] in a["newTabUrl"]}
          for r, a in post_arms]
    add("S5:★★ post 里新标签页 URL 真的带上了 `?canvas=<目标>`",
        "★ 机制证据：修复就是把 id 放进 URL，由根页消费",
        ev and all(x["★ 带了"] for x in ev), ev)

    # ── S6 ★ 无回归：本标签页仍然跟着点的那张走
    ev = [{"round": r, "target": a["target"],
           "本标签页 active": a["sameTabAfterClick"].get("activeCanvasId"),
           "storeFound": a["sameTabAfterClick"].get("storeFound"),
           "★ 跟着走": a.get("sameTabFollowed")}
          for r, a in post_arms]
    add("S6:★★ 无回归：post 里**本标签页**仍然跟着点的那张走",
        "★ 这条读 store（`/project` 页面上没有画布页的 `[data-canvas-trigger]`，"
        "DOM 上读不到）；★ 而它必须有证据 —— 第一版的 `sameTabAfterClick` 在"
        "`/project` 上找那个钩子、恒为 null，是一条**恒定无信息**的读数",
        ev and all(x["★ 跟着走"] and x["storeFound"] for x in ev), ev)

    # ── S7 ★★ 新路径的失败模式：参数坏了会怎样
    ev = []
    for r in post_raw.get("rounds", []):
        ip = r.get("invalidParam")
        if not ip or ip.get("FAILED"):
            continue
        ev.append({"round": r["round"], "参数": ip["target"],
                   "回落到": ip["newTab"]["activeCanvasId"],
                   "可见画布行": ip["newTab"]["visibleRows"],
                   "节点": ip["newTab"]["reactFlowNodes"],
                   "★ 页面正常": ip["rendered"],
                   "★ 回落到某张画布": ip["fellBackToSomeCanvas"],
                   "★ 没跟着坏参数跑": ip["newTab"]["activeCanvasId"]
                                      != ip["target"]})
    add("S7:★★ 坏参数回落：认不出来的 `?canvas=` 不会白屏或崩，回落到默认画布",
        "★★ 修复**引入了一条新路径**（从 URL 读 id 并切画布）⟹ 它自带一个新失败"
        "模式。★ 不测它等于把新风险放进代码却不看它。（pre 探针未含此臂："
        "这条路径在 pre 里根本不存在）",
        ev and all(x["★ 页面正常"] and x["★ 回落到某张画布"]
                   and x["★ 没跟着坏参数跑"] for x in ev), ev)

    # ── S8 静态锚点：两处都要在，且**锚点带完整上下文**
    open_ok = "window.open(`/?canvas=${encodeURIComponent(canvasId)}`, \"_blank\")" \
        in proj_src
    consume_ok = ('new URLSearchParams(window.location.search).get("canvas")'
                  in home_src) and ("setActiveCanvas(wanted)" in home_src)
    add("S8:★★ 静态锚点：`/project` 把 id 放进 URL，根页挂载时消费它",
        "★ 两处缺一不可：只改 `/project` 等于把参数丢进虚空",
        open_ok and consume_ok,
        {"/project 里 open 带 ?canvas=": open_ok,
         "根页消费 ?canvas=": consume_ok})

    return checks


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    proj_src = (ROOT / PROJ).read_text(encoding="utf-8")
    home_src = (ROOT / HOME).read_text(encoding="utf-8")

    checks = run_checks(pre_raw, post_raw, proj_src, home_src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        p, q = copy.deepcopy(pre_raw), copy.deepcopy(post_raw)
        hit = mutate(p, q)
        assert hit, "★ raw 变异没命中"
        c = run_checks(p, q, proj_src, home_src)
        flipped = [x["id"] for x in c if not x["ok"]]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def post_wrong(q):
        n = 0
        for r in q["rounds"]:
            for a in r.get("arms", []):
                if a.get("target") == "canvas-1" and not a.get("FAILED"):
                    a["newTab"]["activeCanvasId"] = "canvas-2"
                    a["showsTarget"] = False
                    n += 1
        return n

    def post_bad_fallback(q):
        n = 0
        for r in q["rounds"]:
            ip = r.get("invalidParam")
            if ip and not ip.get("FAILED"):
                ip["newTab"]["activeCanvasId"] = None
                ip["fellBackToSomeCanvas"] = False
                n += 1
        return n

    def pre_fixed(p, q):
        n = 0
        for r in p["rounds"]:
            for a in r.get("arms", []):
                if a.get("target") == "canvas-1" and not a.get("FAILED"):
                    a["newTab"]["activeCanvasId"] = "canvas-1"
                    n += 1
        return n

    def same_node_counts(q):
        n = 0
        for r in q["rounds"]:
            for a in r.get("arms", []):
                if not a.get("FAILED"):
                    a["newTab"]["reactFlowNodes"] = 7
                    n += 1
        return n

    def same_tab_broken(q):
        n = 0
        for r in q["rounds"]:
            for a in r.get("arms", []):
                if not a.get("FAILED"):
                    a["sameTabFollowed"] = False
                    n += 1
        return n

    def touch_unrelated(p, q):
        q["rounds"][0]["cards"] = ["x"]
        return True

    negs = [
        neg("N1 ★★ post raw：声称点 canvas-1 打开的是 canvas-2",
            "★ 验证 S3 抓的是「新标签页显示的是不是目标」",
            lambda p, q: post_wrong(q),
            "S3:★★★ 修复生效：post 里**两个方向**都显示你点的那张"),
        neg("N2 ★★ post raw：声称坏参数没有回落到任何画布",
            "★ 验证 S7 抓的是「有没有回落」",
            lambda p, q: post_bad_fallback(q),
            "S7:★★ 坏参数回落：认不出来的 `?canvas=` 不会白屏或崩，回落到默认画布"),
        neg("N3 ★★ pre raw：声称 pre 里点 canvas-1 打开的就是 canvas-1",
            "★ 验证 S1 抓的确实是「新标签页开错画布」这件事",
            lambda p, q: pre_fixed(p, q),
            "S1:★★ 缺陷复现：pre 里点一张卡，新标签页显示的是**另一张**"),
        neg("N4 ★★ post raw：把两臂的节点数改成相同",
            "★★ 验证 S4 抓的是「内容真的换了」，而不是「id 字符串换了」",
            lambda p, q: same_node_counts(q),
            "S4:★★ 不只是 id 对了 —— **内容**也跟着换（两张画布节点数互不相同）"),
        neg("N5 ★★ post raw：声称本标签页没跟着走",
            "★ 验证 S6 无回归不是空转",
            lambda p, q: same_tab_broken(q),
            "S6:★★ 无回归：post 里**本标签页**仍然跟着点的那张走"),
        neg("N6 ★★ 反向对照：只动一个与判据无关的字段（cards）",
            "★ 证明判据锚的是读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    report = {"batch": 804, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": sum(1 for n in negs if n["ok"]),
              "negativesTotal": len(negs),
              "rawSha": {"pre": sha(PRE), "post": sha(POST)}}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    return 0 if (nPass == len(checks)
                 and all(n["ok"] for n in negs)) else 1


if __name__ == "__main__":
    sys.exit(main())