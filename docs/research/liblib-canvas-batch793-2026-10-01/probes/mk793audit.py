#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 793 汇编器 —— 分组框**跟随**成员

## 承重事实（batch 757 待拍板 ①，本批**独立复现**）

把子节点拖出分组框之后，**框的位置与尺寸一动不动**、`parentId` 照旧挂着
⟹ 「**store 说它属于这个组，屏幕说它不在框里**」。757 实测拖 501px 后
子节点左边缘距框右边缘 277 屏幕像素。

## 修法

在 `routeReactFlowChanges` 写 `plan.nextNodes` 的**唯一收口**上，挂一个纯函数
`fitStoryboardGroupsToChildren`：把每个组重算成恰好包住它的子节点，并把子节点的
相对位置一起重基（组 `position` 一变，所有子节点绝对位置都会偏）。

两条刻意边界：

1. **0 成员的组不动** —— 收缩/隐藏空组是 757 待拍板 ②，源站未采样，本批不碰。
2. 组按「先外后内」处理，每轮**重新**从当前列表算绝对位置 ⟹ 嵌套时内层拿到的
   绝对位置已经是对的。

## 读数（同一份探针，pre / post 各 2 轮，3 臂）

| 臂 | pre | post |
| --- | --- | --- |
| ★ 拖子节点出框 | 组 pos **不动**、子节点 `在框内 True→**False**` ✗ | 组 pos **跟上**、子节点 `True→**True**` ✓ |
| 对照一：拖非成员 | 组 pos 不动、`True→True` ✓ | 组 pos 不动、`True→True` ✓ |
| 对照二：拖组本身 | 组 y 动、尺寸不变、子节点跟着走、`True→True` ✓ | 同上 ✓ |

★ 两条对照缺一不可：只测「子节点拖出去框跟着走」的话，一个「凡是拖动就把
**所有**组都重算一遍」的粗糙实现也能全绿。

## ★ 一处**可见变化**必须记账：基线框被归位

种子里 `g-EFbbHpwq5w` 是 722×460，而它**唯一**的成员是 622×350（多出 50/55px
的任意余量）。react-flow 挂载时会发 `dimensions` 变更 ⟹ 走同一条收口 ⟹
post 首屏就把框归位成 **686×414**，并且**精确等于**按 `32×2` 算出的贴合值
（`(2436-32, 50-32)` / `622+64, 350+64`）。

`StoryboardGroupNode` **没有 resize 控件**（只有两条连线用的 `Handle`）⟹
框的尺寸纯属派生值 ⟹ 归位**不覆盖任何用户意图**。但这是对默认画布的可见变化，
必须写出来。
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch793-2026-10-01"
PRE = REPO / (B + "/raw/vb793a-pre.json")
POST = REPO / (B + "/raw/vb793a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
CS = "src/store/canvasStore.ts"

ARMS = ["dragChildOut", "dragNonMember", "dragGroupItself"]
PADDING = 32


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def read(cell):
    """★ 从 raw 的 before/after **重算**这一格的「行为签名」。

    ★ 只取**行为**（组动没动 / 尺寸变没变 / 子节点在不在框内），
    **不取**具体像素：拖拽起点是扫描出来的，每轮差几个像素，
    具体坐标天然不稳定，拿它判「两轮一致」会误报。
    """
    b, a = cell.get("before"), cell.get("after")
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    gs_b, gs_a = b.get("groupStore"), a.get("groupStore")
    kb = (b.get("kids") or [None])[0]
    ka = (a.get("kids") or [None])[0]
    if not (gs_b and gs_a and kb and ka):
        return None
    return {
        "groupMoved": [gs_b["pos"]["x"], gs_b["pos"]["y"]]
        != [gs_a["pos"]["x"], gs_a["pos"]["y"]],
        "groupSizeChanged": [gs_b["w"], gs_b["h"]] != [gs_a["w"], gs_a["h"]],
        "childInside": [kb.get("inside"), ka.get("inside")],
        "childMoved": kb.get("abs") != ka.get("abs"),
        "groupStore": gs_a, "kidsAfter": ka,
        "groupStoreBefore": gs_b, "kidsBefore": kb,
    }


def sig(cell):
    r = read(cell)
    if not r:
        return None
    return {k: r[k] for k in ("groupMoved", "groupSizeChanged", "childInside")}


def tight_fit(kid):
    """★ 按 `GROUP_PADDING` 从子节点**重算**贴合框（独立于源码公式）。"""
    if not kid or not kid.get("abs"):
        return None
    return {"pos": {"x": kid["abs"]["x"] - PADDING, "y": kid["abs"]["y"] - PADDING},
            "w": (kid.get("w") or 0) + PADDING * 2,
            "h": (kid.get("h") or 0) + PADDING * 2}


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── A：源码锚点 ──
    whole = (REPO / CS).read_text(encoding="utf-8")
    lines = whole.split("\n")

    def hits(n):
        return [i + 1 for i, l in enumerate(lines) if n in l]

    det, ok = [], True
    for label, needle, want in [
        ("纯函数存在", "function fitStoryboardGroupsToChildren(", 1),
        ("挂在唯一收口上", "nodes: fitStoryboardGroupsToChildren(", 1),
        ("★ 空组不动", "if (kids.length === 0) continue;", 1),
        ("★ 容差判 no-op", "const EPS = 0.01;", 1),
    ]:
        h = hits(needle)
        good = len(h) == want
        ok = ok and good
        det.append({"label": label, "needle": needle, "ok": good, "lines": h,
                    "code": lines[h[0] - 1].strip()[:96] if h else None})
    c = {"id": "A:四处源码锚点各唯一", "ok": ok, "n": 4, "anchors": det,
         "claim": "★ 纯函数 + 挂在 `routeReactFlowChanges` 的**唯一收口** + "
                  "空组不动 + 容差 no-op"}
    assert ok, "★ 源码锚定失败：\n%r" % det
    checks.append(c)

    # ── B：格数与无 FAILED ──
    shape_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            shape_bad.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                shape_bad.append({"phase": name, "arm": k, "rounds": len(v)})
            for _rd, c2 in v:
                if c2.get("FAILED") or read(c2) is None:
                    shape_bad.append({"phase": name, "arm": k,
                                      "FAILED": c2.get("FAILED") or "读数缺失"})
    add("B:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 或读数缺失就是**空读数**，不能当结论",
        not shape_bad, {"bad": shape_bad})

    # ── C：★★ 处理臂：pre 子节点跑出框、post 留在框里且组跟上 ──
    p = [read(c) for _rd, c in pre["dragChildOut"]]
    q = [read(c) for _rd, c in post["dragChildOut"]]
    add("C:★★ 处理臂：pre 框不动且子节点出框，post 框跟上且子节点在框内",
        "★ pre：`groupMoved=false` 且 `childInside [True, False]`；"
        "post：`groupMoved=true` 且 `childInside [True, True]`",
        all(x and not x["groupMoved"] and x["childInside"] == [True, False]
            and x["childMoved"] for x in p)
        and all(x and x["groupMoved"] and x["childInside"] == [True, True]
                and x["childMoved"] for x in q),
        {"pre": [{k: x[k] for k in ("groupMoved", "childInside", "childMoved")}
                 for x in p],
         "post": [{k: x[k] for k in ("groupMoved", "childInside", "childMoved")}
                  for x in q]})

    # ── D：★ 对照一：拖非成员不得动任何组 ──
    p1 = [read(c) for _rd, c in pre["dragNonMember"]]
    q1 = [read(c) for _rd, c in post["dragNonMember"]]
    add("D:★ 对照一：拖非成员，组在两阶段都不得动",
        "★ 缺了它，一个「凡是拖动就把**所有**组都重算一遍」的粗糙实现"
        "也能让 C 通过",
        all(x and not x["groupMoved"] and not x["groupSizeChanged"]
            and x["childInside"] == [True, True] for x in p1 + q1),
        {"pre": [{k: x[k] for k in ("groupMoved", "groupSizeChanged",
                                    "childInside")} for x in p1],
         "post": [{k: x[k] for k in ("groupMoved", "groupSizeChanged",
                                     "childInside")} for x in q1]})

    # ── E：★ 对照二：拖组本身尺寸不得变、成员要跟着走、且仍在框内 ──
    p2 = [read(c) for _rd, c in pre["dragGroupItself"]]
    q2 = [read(c) for _rd, c in post["dragGroupItself"]]
    add("E:★ 对照二：拖组本身尺寸不变、成员跟着走、仍在框内",
        "★ 组「移动」不等于组「重算」⟹ 拖组时成员的绝对位置没变，"
        "整段必须是 no-op（否则说明重算逻辑在误伤）",
        all(x and x["groupMoved"] and not x["groupSizeChanged"]
            and x["childMoved"] and x["childInside"] == [True, True]
            for x in p2 + q2),
        {"pre": [{k: x[k] for k in ("groupMoved", "groupSizeChanged",
                                    "childMoved", "childInside")} for x in p2],
         "post": [{k: x[k] for k in ("groupMoved", "groupSizeChanged",
                                     "childMoved", "childInside")} for x in q2]})

    # ── F：★★ 基线框被归位，且**精确等于**按 padding 重算的贴合值 ──
    fit_ev, fit_bad = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c2 in idx["dragChildOut"]:
            r = read(c2)
            if not r:
                fit_bad.append({"phase": name, "why": "读数缺失"})
                continue
            want = tight_fit(r["kidsBefore"])
            got = {"pos": r["groupStoreBefore"]["pos"],
                   "w": r["groupStoreBefore"]["w"],
                   "h": r["groupStoreBefore"]["h"]}
            same = (want and got["pos"]["x"] == want["pos"]["x"]
                    and got["pos"]["y"] == want["pos"]["y"]
                    and got["w"] == want["w"] and got["h"] == want["h"])
            fit_ev.append({"phase": name, "group": got, "tightFit": want,
                           "equalsTightFit": same})
            if name == "post" and not same:
                fit_bad.append(fit_ev[-1])
    add("F:★★ post 的基线框**精确等于**按 padding 重算的贴合值",
        "★ 种子里 722×460 的框**并不贴合**它唯一那个 622×350 的成员"
        "（多 50/55px 任意余量）⟹ post 首屏被归位成 686×414。"
        "★ 这条同时独立验证了贴合公式（不依赖源码，只用 raw 里的子节点读数）",
        not fit_bad, {"bad": fit_bad, "evidence": fit_ev})

    # ── G：★ 两轮的**行为签名**一致（不拿像素比）──
    sig_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            s = [sig(c) for _rd, c in lst]
            if s[0] != s[1]:
                sig_bad.append({"phase": name, "arm": arm,
                                "sigs": s})
    add("G:★ 两轮的**行为签名**一致",
        "★ 拖拽起点是扫描出来的、每轮差几个像素 ⟹ 只能比**行为**"
        "（组动没动 / 尺寸变没变 / 在不在框内），拿像素判「一致」会误报",
        not sig_bad, {"bad": sig_bad})

    # ── H：★ 遗留：0 成员的组本批**没有**被处理（757 待拍板 ②）──
    #   本批只观测到「空组仍画完整框」这件事在两阶段都成立，
    #   但**没有**单独的空组探针臂 ⟹ 明确记为未验，不当结论。
    out = {
        "batch": 793,
        "kind": "★ 第四批改 src/ 的批次（分组框跟随成员）",
        "claims": {
            "D793-1": "★ 分组框与成员之间**没有任何跟随关系**：子节点拖出框后，"
                      "框的位置与尺寸**一动不动**、`parentId` 照旧挂着 "
                      "⟹ 「store 说它属于这个组，屏幕说它不在框里」",
            "C793-2": "★ 修法 = 在 `routeReactFlowChanges` 写 `plan.nextNodes` "
                      "的**唯一收口**上挂 `fitStoryboardGroupsToChildren`；"
                      "拖**非成员**时它内部是 no-op ⟹ 不会误伤别的组",
            "C793-3": "★ 两条刻意边界：0 成员的组**不动**（757 待拍板 ②，"
                      "源站未采样）；组按「先外后内」处理且每轮**重算**"
                      "绝对位置 ⟹ 嵌套时内层拿到的是已更新的绝对位置",
            "★ 可见变化": "★ react-flow 挂载时发 `dimensions` 变更 ⟹ "
                          "首屏就把种子那个**并不贴合**的框归位"
                          "（722×460 → 686×414，精确等于按 32×2 重算的值）",
            "★ 未验": "★ **没有**单独的空组探针臂 ⟹ 「空组仍画完整框」"
                      "只是被顺带观测到，不当结论",
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D793-1 修好：pre 组不动且子节点出框，post 组跟上且子节点在框内")
    print("★ 两条对照：拖非成员组不动；拖组本身尺寸不变、成员跟着走")
    print("★ 基线框被归位：722×460 → 686×414（精确等于按 32×2 重算的贴合值）")
    print("★ 未验：没有空组探针臂，757 待拍板 ② 本批不碰")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
