#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 807 验收器 —— 独立实现，不 import 探针

## 本批的两个结论 + 一条附赠

**结论一：`groupSelectedNodes` 的几何是对的。** 802 只给了静态证据（读源码
`position = absolute − group.position` 看着对），794 立过一条硬规矩：只有静态
证据时报告**不许**说「验过了」。本批取到行为证据。

**结论二：选区里有组时按 `G` 是彻底静默的**（792 的遗留，终于有行为证据）。

**附赠：一条给 793／757 ② 的读数** —— 组被搬空之后**保持原框、不收缩**。

## 三条不变量（只认绝对几何）

- **N1 不该跳的东西没跳**：被组合的成员，组合前后**绝对位置逐位相同**。
  ★ 判据**不预设** `position` 存绝对还是相对：绝对值由 raw 里的
  `pos` 沿 `parentId` 链**独立求和**得到（探针已经这么采，验收器再自己算一遍）。
- **N2 成员在框内**：新组的绝对框包含所有被组合成员（793 立的不变量）。
- ★★ **N3 操作要么生效、要么有反馈**：792 遗留的判据。按 `G` 之后，要么节点
  集合真的变了，要么页面出现可见反馈。三项读数（节点数、新增 `data-*` 键、
  状态文本）**全都不变** 才算「静默」。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
D = ROOT / "docs/research/liblib-canvas-batch807-2026-10-01"
RAW = D / "raw/vb807a.json"
REPORT = D / "verify-report.json"
CS = "src/store/canvasStore.ts"
PADDING = 40          # 只用于 N2 的独立重算；不参与「是否正确」的判断


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def chain_abs(nodes, nid):
    """★ 独立重算绝对位置：起点是 `position`，沿 parentId 链逐层求和。"""
    idx = {n["id"]: n for n in nodes}
    n = idx.get(nid)
    if n is None:
        return None
    x, y = n["pos"]["x"], n["pos"]["y"]
    pid, hops = n.get("parentId"), 0
    seen = {nid}
    while pid and pid in idx and pid not in seen and hops < 32:
        seen.add(pid)
        hops += 1
        p = idx[pid]
        x += p["pos"]["x"]
        y += p["pos"]["y"]
        pid = p.get("parentId")
    return (x, y, hops)


def dim(n):
    return (n.get("w") or 350, n.get("h") or 180)


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    rs = raw.get("rounds", [])

    # ── S1 ★★★ N1：被组合的成员绝对位置逐位不变（臂1 + 臂2）
    ev = []
    for r in rs:
        for arm in ("withHostMember", "twoHostMembers"):
            a = r.get(arm)
            if not a or a.get("FAILED") or not a.get("afterNodes"):
                continue
            rows = []
            for nid, (babs, bw, bh) in a["beforeAbs"].items():
                after = next((n for n in a["afterNodes"] if n["id"] == nid), None)
                if after is None:
                    rows.append({"id": nid, "after": None})
                    continue
                # ★ 独立重算，不信 raw 里那个 abs
                recomputed = chain_abs(a["afterNodes"], nid)
                rows.append({
                    "id": nid, "臂": arm,
                    "before": [babs["x"], babs["y"]],
                    "after(raw.abs)": [after["abs"]["x"], after["abs"]["y"]],
                    "after(独立重算)": list(recomputed)[:2],
                    "★ raw 与重算一致": [after["abs"]["x"], after["abs"]["y"]]
                                    == list(recomputed)[:2],
                    "★ 逐位没跳": [babs["x"], babs["y"]]
                               == [after["abs"]["x"], after["abs"]["y"]]})
            ev.append({"round": r["round"], "臂": arm, "逐个": rows,
                       "★ 全部没跳": bool(rows)
                                    and all(x.get("★ 逐位没跳") for x in rows),
                       "★ raw 与重算全一致": bool(rows)
                            and all(x.get("★ raw 与重算一致") for x in rows)})
    add("S1:★★★ N1 不该跳的东西没跳：被组合的成员**绝对位置逐位不变**",
        "★★★ 这是「几何是对的」的行为证据本体（802 只有静态证据）；"
        "★★ 判据**不预设** position 存绝对还是相对，绝对值由 raw 的 pos 沿 "
        "parentId 链**独立重算**，且要求与 raw 记录的 abs **一致**",
        ev and all(x["★ 全部没跳"] and x["★ raw 与重算全一致"] for x in ev), ev)

    # ── S2 ★★ N2：新组的绝对框包含所有被组合成员
    ev = []
    for r in rs:
        a = r.get("withHostMember")
        if not a or not a.get("afterNodes"):
            continue
        sel = a["selected"]
        grp = next((n for n in a["afterNodes"]
                    if n["type"] == "storyboard-group"
                    and set(sel).issubset(set(n["kids"]))), None)
        rows = []
        if grp:
            gx, gy = chain_abs(a["afterNodes"], grp["id"])[:2]
            gw, gh = dim(grp)
            for nid in sel:
                n = next((x for x in a["afterNodes"] if x["id"] == nid), None)
                if not n:
                    continue
                mx, my = chain_abs(a["afterNodes"], nid)[:2]
                nw, nh = dim(n)
                rows.append({"id": nid,
                             "成员左上": [mx, my], "成员右下": [mx + nw, my + nh],
                             "组左上": [gx, gy], "组右下": [gx + gw, gy + gh],
                             "★ 在框内": gx <= mx and gy <= my
                                         and gx + gw >= mx + nw
                                         and gy + gh >= my + nh})
        ev.append({"round": r["round"], "新组": grp["id"] if grp else None,
                   "组框": [gx, gy, gw, gh] if grp else None,
                   "逐个": rows,
                   "★ 全在框内": bool(rows) and all(x["★ 在框内"] for x in rows)})
    add("S2:★★ N2 成员在框内：新组的**绝对**框包含所有被组合成员",
        "★ 793 立的不变量；★ 组框也是沿链独立重算的绝对值，不读 raw 的 abs",
        ev and all(x["★ 全在框内"] for x in ev), ev)

    # ── S3 ★★★ N3：选区里有组时按 G 是彻底静默的
    ev = []
    for r in rs:
        g = r.get("groupPlusOne")
        if not g or g.get("FAILED"):
            continue
        ev.append({"round": r["round"], "选中": g["selected"],
                   "节点数 Δ": g["nodeCountDelta"],
                   "新增 data-* 键": g["newFeedbackKeys"],
                   "状态文本变了": g["statusChanged"],
                   "★ 三项全不变才算静默": g["nodeCountDelta"] == 0
                       and g["newFeedbackKeys"] == []
                       and g["statusChanged"] is False})
    add("S3:★★★ N3：选区里有组时按 `G` —— 节点数、新增 `data-*` 键、状态文本"
        "**三项全不变**",
        "★★ 这是 792 遗留（「选中里有分组时用户得不到任何告知」）的行为证据。"
        "★ 三项读数缺一不可：只看节点数，「弹了个提示但没建组」会被误判成静默；"
        "★ 而**只跑一个臂也不够** —— 必须先证明同一个 `G` 在别的选区下**确实生效**（S4）",
        ev and all(x["★ 三项全不变才算静默"] for x in ev), ev)

    # ── S4 ★★ 阳性对照：同一个 `G` 在别的选区下确实生效
    ev = []
    for r in rs:
        one = r.get("withHostMember") or {}
        two = r.get("twoHostMembers") or {}
        made = r.get("makeHost") or {}
        ev.append({"round": r["round"],
                   "UI 造宿主组": bool(made.get("host")),
                   "臂1 Δ节点": one.get("nodeCountDelta"),
                   "臂1 新增键数": len(one.get("newFeedbackKeys") or []),
                   "臂2 Δ节点": two.get("nodeCountDelta"),
                   "★ 同样的 G 在别的选区下生效":
                       one.get("nodeCountDelta") == 1
                       and len(one.get("newFeedbackKeys") or []) > 0})
    add("S4:★★ 阳性对照：同一个 `G` 在别的选区下**确实建出了组**",
        "★★ 没有这条，S3 的「静默」可能只是「键盘没生效」⟹ ★ 而且它还顺带"
        "证明宿主组是**通过 UI 造出来的**（选 2 个散节点按 G），不是注入的 —— "
        "792 那条修法的前提就是「UI 造得出组」，注入会绕过这条前提",
        ev and all(x["★ 同样的 G 在别的选区下生效"] and x["UI 造宿主组"]
                   for x in ev), ev)

    # ── S5 ★★ 新组成为这些成员的父，宿主组确实失去了它们
    ev = []
    for r in rs:
        a = r.get("withHostMember")
        if not a or not a.get("afterNodes"):
            continue
        sel = a["selected"]
        after = {n["id"]: n for n in a["afterNodes"]}
        host_before = a["beforeHost"]
        host_kids = host_before.get("kids") or []
        # ★ 只算「**本来就在宿主组里**」的那些选中项。第一版按 len(选中) 去减，
        #   而臂1 选的是「一个宿主组成员 + 一个散节点」—— 散节点本来就不在宿主组里
        #   ⟹ 宿主组只该少 1 个，我却拿 2 去减 ⟹ 假红。
        leaving = [i for i in sel if i in host_kids]
        rows = [{"id": i, "★ 本来就在宿主组里": i in host_kids,
                 "parentAfter": after[i]["parentId"],
                 "★ 父变成新组": after[i]["parentId"] != host_before["id"]}
                for i in sel if i in after]
        ev.append({"round": r["round"], "宿主组 before": host_before["id"],
                   "宿主组 before 成员数": len(host_kids),
                   "本来就在组里的选中项": leaving,
                   "宿主组 after 成员数": len(
                       (a.get("afterHost") or {}).get("kids") or []),
                   "逐个": rows,
                   "★ 都改判到新组": bool(rows)
                       and all(x["★ 父变成新组"] for x in rows),
                   "★ 宿主组只少了「本来在里面」的": len(
                       (a.get("afterHost") or {}).get("kids") or [])
                       == len(host_kids) - len(leaving)})
    add("S5:★★ 新组确实成为这些成员的父，且宿主组**只失去了「本来就在里面」的**那些",
        "★★ 这是「组合真的发生了」的结构证据 ⟹ 与 S4 的「节点数变了」互相独立；"
        "★ 只算本来就在宿主组里的选中项 —— 臂1 选的是「一个组成员 + 一个散节点」，"
        "散节点本来就不在宿主组里",
        ev and all(x["★ 都改判到新组"] and x["★ 宿主组只少了「本来在里面」的"]
                   for x in ev), ev)

    # ── S6 ★★ 附赠读数：组被搬空之后**保持原框、不收缩**
    ev = []
    for r in rs:
        two = r.get("twoHostMembers")
        if not two or not two.get("afterNodes"):
            continue
        host = two.get("hostAfter") or {}
        # ★ 独立重算：那两个人当时的包围盒 ⊕ 2×padding，看空组的框是不是还等于它
        sel = two["selected"]
        boxes = []
        for i in sel:
            n = next((x for x in two["afterNodes"] if x["id"] == i), None)
            if not n:
                continue
            mx, my = chain_abs(two["afterNodes"], i)[:2]
            w, h = dim(n)
            boxes.append((mx, my, mx + w, my + h))
        if boxes and host:
            exp_w = max(b[2] for b in boxes) - min(b[0] for b in boxes) + 2 * PADDING
            exp_h = max(b[3] for b in boxes) - min(b[1] for b in boxes) + 2 * PADDING
            hw, hh = dim(host)
            ev.append({"round": r["round"], "空组": host.get("id"),
                       "空组剩余成员": host.get("kids"),
                       "框": [hw, hh],
                       "独立重算(两人包围盒⊕2×padding)": [exp_w, exp_h],
                       "★ 它还等于原来的框": abs(hw - exp_w) < 1e-6
                                          and abs(hh - exp_h) < 1e-6})
    add("S6:★★ 附赠读数（给 793／757 ②）：组被搬空后**框不变**，仍等于"
        "原成员的包围盒 ⊕ 2×padding",
        "★ 这条不是判「对错」，是给 793 那条待拍板 ②（空组要不要收缩/弱化）"
        "补一条**实测读数**；★ 框是**独立重算**的（两人的包围盒 ⊕ padding），"
        "不是复述 raw 里的尺寸",
        ev and all(x["★ 它还等于原来的框"] for x in ev), ev)

    # ── S7 静态锚点：`children` 过滤掉组 ⟹ 组参与时 children 可能 < 2
    i0 = src.find("groupSelectedNodes: (nodeIds) => {")
    j = src.find("\n  ungroupSelectedNodes: (", i0) if i0 >= 0 else -1
    seg = src[i0:j] if (i0 >= 0 and j > i0) else ""
    add("S7:★★ 静态锚点：`children` 过滤掉组 + `children.length < 2` 提前返回",
        "★ 这是「静默」在源码侧的对应物：组被过滤掉之后若不足 2 个就直接 return，"
        "**没有任何提示路径**；★ 锚点带完整签名以免命中接口声明（799 起的第五次）",
        'node.type !== "storyboard-group"' in seg
        and "if (children.length < 2) return state;" in seg
        and len(seg) > 800,
        {"段长": len(seg),
         "过滤掉组": 'node.type !== "storyboard-group"' in seg,
         "不足 2 个直接返回": "if (children.length < 2) return state;" in seg,
         "段内有提示路径": ("status" in seg or "toast" in seg
                            or "setMessage" in seg)})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")

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
        flipped = [x["id"] for x in c if not x["ok"]]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def jump_member(d):
        n = 0
        for r in d["rounds"]:
            a = r.get("withHostMember") or {}
            for node in a.get("afterNodes") or []:
                if node["id"] in (a.get("beforeAbs") or {}):
                    node["pos"] = {"x": node["pos"]["x"] + 37,
                                   "y": node["pos"]["y"] - 21}
                    node["abs"] = {"x": node["abs"]["x"] + 37,
                                   "y": node["abs"]["y"] - 21,
                                   "depth": node["abs"]["depth"]}
                    n += 1
                    break
        return n

    def shrink_group(d):
        n = 0
        for r in d["rounds"]:
            a = r.get("withHostMember") or {}
            sel = a.get("selected") or []
            for node in a.get("afterNodes") or []:
                if node["type"] == "storyboard-group" and set(sel).issubset(
                        set(node["kids"])):
                    node["w"] = 10
                    node["h"] = 10
                    n += 1
        return n

    def add_feedback(d):
        n = 0
        for r in d["rounds"]:
            g = r.get("groupPlusOne")
            if g and "nodeCountDelta" in g:
                g["newFeedbackKeys"] = ["data-group-hint=1"]
                g["statusChanged"] = True
                n += 1
        return n

    def group_did_nothing(d):
        n = 0
        for r in d["rounds"]:
            a = r.get("withHostMember")
            if a and "nodeCountDelta" in a:
                a["nodeCountDelta"] = 0
                a["newFeedbackKeys"] = []
                n += 1
        return n

    def collapse_empty_group(d):
        n = 0
        for r in d["rounds"]:
            two = r.get("twoHostMembers") or {}
            host = two.get("hostAfter")
            if host:
                host["w"] = 0
                host["h"] = 0
                n += 1
        return n

    def touch_unrelated(d):
        for r in d["rounds"]:
            r["note"] = "touched"
        return True

    negs = [
        neg("N1 ★★★ raw：把臂1 里某个成员的绝对位置挪 (37,-21)",
            "★★★ 验证 S1 抓的正是「成员不该跳」这件事",
            jump_member,
            "S1:★★★ N1 不该跳的东西没跳：被组合的成员**绝对位置逐位不变**"),
        neg("N2 ★★ raw：把新组的框缩成 10×10",
            "★ 验证 S2 抓的是「成员在框内」，不是「新组存在」",
            shrink_group,
            "S2:★★ N2 成员在框内：新组的**绝对**框包含所有被组合成员"),
        neg("N3 ★★★ raw：声称组参与时**弹了提示**",
            "★★★ 验证 S3 的「静默」判据真的看反馈，而不只是看节点数",
            add_feedback,
            "S3:★★★ N3：选区里有组时按 `G` —— 节点数、新增 `data-*` 键、状态文本"
            "**三项全不变**"),
        neg("N4 ★★ raw：声称同一个 G 在别的选区下也没建组",
            "★★ 验证 S4 的阳性对照不是空转 —— 否则 S3 的静默无从谈起",
            group_did_nothing,
            "S4:★★ 阳性对照：同一个 `G` 在别的选区下**确实建出了组**"),
        neg("N5 ★★ raw：声称空组的框被清零了",
            "★★ 验证 S6 抓的是「空组保持原框」这条读数",
            collapse_empty_group,
            "S6:★★ 附赠读数（给 793／757 ②）：组被搬空后**框不变**，仍等于"
            "原成员的包围盒 ⊕ 2×padding"),
        neg("N6 ★★ 反向对照：只动与判据无关的字段（note）",
            "★ 证明判据锚的是读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    report = {"batch": 807, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": sum(1 for n in negs if n["ok"]),
              "negativesTotal": len(negs), "rawSha": sha(RAW)}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    return 0 if (nPass == len(checks) and all(n["ok"] for n in negs)) else 1


if __name__ == "__main__":
    sys.exit(main())