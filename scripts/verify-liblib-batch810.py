#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 810 验收器 —— 组框到底有没有收敛成**不动点**

## ★ 判据

组框必须**恰好包住所有成员**，四边留白**相等**：

    左留白 = min(成员绝对 x) − 组绝对 x
    右留白 = 组绝对 x + 组宽 − max(成员绝对 x + 成员宽)
    上留白 = min(成员绝对 y) − 组绝对 y
    下留白 = 组绝对 y + 组高 − max(成员绝对 y + 成员高)

★ **留白从 raw 独立重算**，不抄源码里的 `GROUP_PADDING = 40`
（805 的「不预设常量」纪律：30 那个数是界面自己写着的，留白同理是**读出来的**）。
★ 四边**相等**就够了 —— 「是不是 40」不在判据里，那是源站对照的事（797 仍挂起）。

## ★ 阳性对照（臂 `badBox`）

把组框手动改成 `10×10` ⟹ fit 必须**自己修回来**。
修不回来 ⟹ 判据抓不到「fit 根本没执行」⟹ 整批作废（806 的 N1 同款）。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB810_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch810-2026-10-01"
                    / "raw" / "vb810a.json"))
OUT = pathlib.Path(os.environ.get("VB810_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch810-2026-10-01"
                    / "verify-report.json"))
CS = "src/store/canvasStore.ts"
TOL = 0.01            # 与源码自己的 no-op 容差同量级（`canvasStore.ts:792`）

ARMS = ["badBox", "seeds", "freshDerived", "dragMember", "shrinkGroup"]


def gaps(snap):
    """★ 独立重算四边留白。`snap` = {"组":…, "成员":[…]}"""
    g, kids = snap.get("组"), (snap.get("成员") or [])
    if not g or not kids:
        return None
    minx = min(k["abs"]["x"] for k in kids)
    miny = min(k["abs"]["y"] for k in kids)
    maxx = max(k["abs"]["x"] + (k["w"] or 0) for k in kids)
    maxy = max(k["abs"]["y"] + (k["h"] or 0) for k in kids)
    gx, gy, gw, gh = g["abs"]["x"], g["abs"]["y"], g["w"], g["h"]
    return {"左": round(minx - gx, 4), "右": round(gx + gw - maxx, 4),
            "上": round(miny - gy, 4), "下": round(gy + gh - maxy, 4),
            "组框": [gx, gy, gw, gh], "成员数": len(kids),
            "成员": [{"id": k["id"], "abs": [k["abs"]["x"], k["abs"]["y"]],
                      "wh": [k["w"], k["h"]]} for k in kids]}


def even(gp):
    """四边留白是否相等（不要求等于 40）"""
    if not gp:
        return False
    vals = [gp["左"], gp["右"], gp["上"], gp["下"]]
    return max(vals) - min(vals) <= TOL


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    rounds = raw["rounds"]

    def cell(rd, arm):
        return next((c for c in rd["cells"] if c.get("arm") == arm), None)

    # ── S1 ★★★ 主判据：扰动沉淀后，四边留白**相等**（独立重算，不预设 40）
    ev = []
    for rd in rounds:
        for arm in ARMS:
            c = cell(rd, arm)
            if not c or c.get("FAILED"):
                continue
            snap = (c.get("观测") or {}).get("第二次") or {}
            gp = gaps(snap)
            ev.append({"round": rd["round"], "臂": arm, "重算": gp,
                       "★ 四边相等": even(gp)})
    add("S1:★★★ 主判据：组框**恰好包住所有成员**（四边留白相等，从 raw 独立重算）",
        "★★★ 这是 793 修 757 ① 时立的不变量；★ 判据只要求「四边相等」，"
        "**不要求等于 40** —— 「是不是 40」是源站对照的事（797 仍挂起），"
        "把两件事混成一件就会在源站没核对时乱改；★ 留白从 raw 重算而不是抄常量",
        ev and all(x["★ 四边相等"] for x in ev)
        and {x["臂"] for x in ev} == set(ARMS), ev)

    # ── S2 ★★★ 阳性对照：**扰动真的生效了**（否则 S1 什么都没测）
    ev = []
    for rd in rounds:
        for arm in ("badBox", "shrinkGroup"):
            c = cell(rd, arm)
            if not c or c.get("FAILED"):
                continue
            inst = (c.get("扰动瞬间") or {}).get("组") or []
            before = ((c.get("扰动前") or {}).get("第一次") or {}).get("组")
            after = ((c.get("观测") or {}).get("第二次") or {}).get("组")
            if not inst or not before or not after:
                continue
            g0 = inst[0]
            ev.append({"round": rd["round"], "臂": arm,
                       "扰动前": [before["w"], before["h"]],
                       "★ 扰动瞬间": [g0["w"], g0["h"]],
                       "★ 确实被改坏了": g0["w"] != before["w"]
                                          or g0["h"] != before["h"],
                       "沉淀后": [after["w"], after["h"]],
                       "★ fit 把它修回来了":
                           [after["w"], after["h"]] == [before["w"], before["h"]],
                       "★ 两件同时": (g0["w"] != before["w"]
                                        or g0["h"] != before["h"])
                           and [after["w"], after["h"]] == [before["w"], before["h"]]})
    add("S2:★★★ 阳性对照：组框被手动改坏之后，**扰动瞬间确实坏了**、"
        "而沉淀后 fit **把它修回原值**",
        "★★★ 没有这条，S1 可能只是「我压根没破坏成功、框一直是对的」⟹ "
        "★ **必须同时记「扰动瞬间」与「沉淀后」**：第一版探针只记了沉淀后，"
        "分不清「扰动没生效」和「生效了又被修回」；"
        "★ 这也证明 `setNodes` 写组的尺寸**确实会**触发 fit（与写子节点不同）",
        ev and all(x["★ 两件同时"] for x in ev)
        and {x["臂"] for x in ev} == {"badBox", "shrinkGroup"}, ev)

    # ── S3 ★★ 收敛：读两次（沉淀后 + 再等一轮）必须**完全相同**
    ev = []
    for rd in rounds:
        for arm in ARMS:
            c = cell(rd, arm)
            if not c or c.get("FAILED"):
                continue
            o = c.get("观测") or {}
            a, b = o.get("第一次"), o.get("第二次")
            ev.append({"round": rd["round"], "臂": arm,
                       "第一次组框": (a or {}).get("组", {}) and
                       [(a or {})["组"]["w"], (a or {})["组"]["h"],
                        (a or {})["组"]["pos"]["x"], (a or {})["组"]["pos"]["y"]],
                       "第二次组框": (b or {}).get("组", {}) and
                       [(b or {})["组"]["w"], (b or {})["组"]["h"],
                        (b or {})["组"]["pos"]["x"], (b or {})["组"]["pos"]["y"]],
                       "★ 两次完全相同": o.get("★ 两次相同（已是不动点）") is True})
    add("S3:★★ 收敛性：再等一轮，组框**一个数字都没再变**（已是不动点）",
        "★★ 799 记的是「单趟不足、靠反馈补齐」⟹ 本条直接问"
        "「**停下来之后**是不是已经是不动点」；★ 两次读数相同**只说明已收敛**，"
        "**不说明**它是第几趟收敛的（趟数未测，见「不声称」）",
        ev and all(x["★ 两次完全相同"] for x in ev)
        and {x["臂"] for x in ev} == set(ARMS), ev)

    # ── S4 ★★★ 拖拽成员：组框要**跟着重新贴合**
    ev = []
    for rd in rounds:
        c = cell(rd, "dragMember")
        if not c or c.get("FAILED"):
            continue
        before = ((c.get("扰动前") or {}).get("第二次") or {})
        after = ((c.get("观测") or {}).get("第二次") or {})
        gb, ga = gaps(before), gaps(after)
        # 成员真的被拖走了吗（相对组的**绝对**位移变了）
        def relpos(sn):
            g = sn.get("组")
            if not g:
                return None
            return [[k["abs"]["x"] - g["abs"]["x"], k["abs"]["y"] - g["abs"]["y"]]
                    for k in sorted(sn.get("成员") or [], key=lambda z: z["id"])]
        rb, ra = relpos(before), relpos(after)
        ev.append({"round": rd["round"], "拖拽": c.get("扰动"),
                   "扰动前四边": gb and {k: gb[k] for k in "左上右下"},
                   "扰动后四边": ga and {k: ga[k] for k in "左上右下"},
                   "成员相对组（之前）": rb, "成员相对组（之后）": ra,
                   "★ 成员真的挪了": rb is not None and ra is not None
                                     and rb != ra,
                   "★ 组框重新贴合": even(ga),
                   "★ 两件同时": (rb is not None and ra is not None and rb != ra)
                                  and even(ga)})
    add("S4:★★★ 真拖拽成员之后，组框**重新贴合**（757 ① 的原始场景）",
        "★★★ 757 ① 修的就是这条：拖 501px 之后子节点与框**没有任何跟随关系**；"
        "★ 这一臂走**真 pointer 拖拽**而不是 store 直写 —— 809 的教训："
        "`setNodes` 绕过了 `onNodesChange`，第一版用 store 直写时组框**没跟上**，"
        "差点被写成缺陷，真因是**我绕过了 fit 的触发点**；"
        "★ 判据同时要求「成员真的挪了」，否则「框没变」可能只是「没拖动」",
        ev and all(x["★ 两件同时"] for x in ev), ev)

    # ── S5 ★★ DOM 侧也要贴合（store 说贴合不够，屏幕也得贴合）
    ev = []
    for rd in rounds:
        for arm in ARMS:
            c = cell(rd, arm)
            if not c or c.get("FAILED"):
                continue
            o = c.get("观测") or {}
            gd, snap = o.get("组DOM"), (o.get("第二次") or {})
            g, kids = snap.get("组"), (snap.get("成员") or [])
            if not gd or not g or not kids:
                continue
            # 组成员在 DOM 里的包围盒 vs 组在 DOM 里的框
            doms = o.get("dom2") or {}
            dks = [doms.get(k["id"]) for k in kids if doms.get(k["id"])]
            if not dks:
                continue
            minx = min(d["x"] for d in dks)
            miny = min(d["y"] for d in dks)
            maxx = max(d["x"] + d["w"] for d in dks)
            maxy = max(d["y"] + d["h"] for d in dks)
            gl = {"左": minx - gd["x"], "右": gd["x"] + gd["w"] - maxx,
                  "上": miny - gd["y"], "下": gd["y"] + gd["h"] - maxy}
            vals = list(gl.values())
            # ★ DOM 读数有亚像素噪声 ⟹ 容差放到 1.5 屏幕像素
            even_dom = (max(vals) - min(vals)) <= 1.5
            ev.append({"round": rd["round"], "臂": arm, "组 DOM": gd,
                       "成员 DOM 包围盒": [minx, miny, maxx - minx, maxy - miny],
                       "DOM 四边留白": {k: round(v, 2) for k, v in gl.items()},
                       "★ 四边相等（容差 1.5 屏幕像素）": even_dom})
    add("S5:★★ DOM 侧也要贴合：组框与成员在**屏幕上**的四边留白相等",
        "★★ store 说贴合不够，用户看见的也得贴合；★ 容差 1.5 屏幕像素："
        "DOM `getBoundingClientRect` 有亚像素噪声（809 实测差 0.01px），"
        "**不写死成逐位相等**",
        ev and all(x["★ 四边相等（容差 1.5 屏幕像素）"] for x in ev)
        and {x["臂"] for x in ev} == set(ARMS), ev)

    # ── S6 ★★ 静态锚点：源码里那条「单趟不足」的注释**确实在那儿**，
    #    而「空组不动」那条边界也在（808 的 S8 同款锚点检查）
    #   ★ 第七次提醒：一律取**最后一次**出现（= 实现），同名声明在前部。
    i_fit = src.rfind("function fitStoryboardGroupsToChildren")
    # ★ 「单趟不足」那句在函数的 **JSDoc 里（函数体上方）** ⟹ 窗口要往前盖，
    #   否则第一版就判成「注释不在实现里」（我自己写的一个假红）
    seg_fit = src[max(0, i_fit - 1200):i_fit + 5200] if i_fit >= 0 else ""
    i_empty = src.rfind("if (kids.length === 0) continue;")
    hits_empty = src.count("if (kids.length === 0) continue;")
    i_eps = src.rfind("const EPS = 0.01;")
    add("S6:★★ 静态锚点：「单趟不足、靠反馈补齐」的注释与「空组不动」的边界都在",
        "★ 静态证据**不能**替代 S1–S5 的行为证据（794 的硬规矩）；"
        "它的作用是把「799 记的那句话」与「808/807 读的那条边界」**钉在实现里**，"
        "并解释为什么 S3 只问「停下来之后是不是不动点」而**不问趟数**；"
        "★ 一律 `rfind`（取实现），同名出现次数一并记进证据",
        i_fit >= 0 and "单趟不足" in seg_fit
        and i_empty >= 0 and "if (kids.length === 0) continue;" in seg_fit
        and i_eps >= 0,
        {"fit 实现位置": i_fit,
         "「单趟不足」在实现段里": "单趟不足" in seg_fit,
         "「空组不动」在实现段里": "if (kids.length === 0) continue;" in seg_fit,
         "同名出现次数（空组跳过）": hits_empty,
         "★ 取的是最后一次": hits_empty > 0,
         "EPS 在实现段里": i_eps >= 0,
         "本验收器用的容差": TOL})

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
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def break_fit(d):
        """★ 把组框改成一个**明显不贴合**的值（四边不等）⟹ S1 必须翻红。
        （不是改成员 —— 那会同时破坏多条判据，分不清谁在起作用）"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                sn = (c.get("观测") or {}).get("第二次") or {}
                g = sn.get("组")
                if g and g.get("w"):
                    g["w"] = g["w"] + 137
                    n += 1
        return n

    def perturb_never_applied(d):
        """★ 阳性对照的对照：假装「扰动没生效」（瞬间读数与之前相同）⟹ S2 翻红"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("arm") in ("badBox", "shrinkGroup") and c.get("扰动前"):
                    inst = c.get("扰动瞬间") or {}
                    before = (inst.get("组") or [None])[0]
                    if before is not None and (c.get("扰动前") or {}).get("第一次"):
                        inst["组"][0] = c["扰动前"]["第一次"]["组"]
                        n += 1
        return n

    def never_healed(d):
        """扰动生效了、但 fit **没修回来** ⟹ S2 必须翻红"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("arm") in ("badBox", "shrinkGroup") and c.get("观测"):
                    sn = c["观测"].get("第二次") or {}
                    g = sn.get("组")
                    inst = ((c.get("扰动瞬间") or {}).get("组") or [None])[0]
                    if g and inst:
                        g["w"], g["h"] = inst["w"], inst["h"]
                        n += 1
        return n

    def still_moving(d):
        """把「第二次」读数改掉 ⟹ S3 的「已是不动点」必须翻红"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                o = c.get("观测") or {}
                a, b = o.get("第一次"), o.get("第二次")
                if a and b and a.get("组") and b.get("组"):
                    b["组"]["w"] = b["组"]["w"] + 9
                    o["★ 两次相同（已是不动点）"] = False
                    n += 1
        return n

    def drag_didnt_happen(d):
        """★ 假装「拖拽其实没生效」（成员相对组的位置没变）⟹ S4 必须翻红。
        —— 否则「框贴合」可能只是「我压根没拖动」"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                if c.get("arm") == "dragMember" and c.get("观测") \
                        and c.get("扰动前"):
                    # ★ 变异条件第一次写成 `o.get("扰动前")` —— 「扰动前」在
                    #   **cell** 上、不在「观测」里 ⟹ 条件恒假、变异打不中，
                    #   断言直接炸。读数与判定都要自己核。
                    # ★ 第二版：只改「第一次」打不中 —— S4 读的是**「第二次」**。
                    #   ★ 这是「阴性对照必须打在性质真正读取的字段上」的第二例
                    #   （809 的 N1 是第一例）；两处都改才对。
                    o = c["观测"]
                    if c["扰动前"].get("第二次"):
                        o["第一次"] = c["扰动前"]["第二次"]
                        o["第二次"] = c["扰动前"]["第二次"]
                        o["★ 两次相同（已是不动点）"] = True
                        n += 1
        return n

    def dom_not_fitted(d):
        """把组的 DOM 框缩小 ⟹ S5 必须翻红"""
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                gd = (c.get("观测") or {}).get("组DOM")
                if gd:
                    gd["w"] = gd["w"] - 200
                    n += 1
        return n

    def comment_removed(d):
        return 0   # 源码不可变异，改由 S6 自身的证据字段承担

    def unrelated(d):
        n = 0
        for rd in d["rounds"]:
            for c in rd["cells"]:
                c["secs"] = 999
                n += 1
        return n

    negs = [
        neg("N1", "★ 打在**性质真正读取的字段**上：把组框改成一个明显不贴合的值 ⟹ S1 翻红",
            break_fit, "S1"),
        neg("N2", "★ 阳性对照的对照：伪造「扰动没生效」（瞬间读数＝之前）⟹ S2 翻红，"
                  "钉死「扰动真的发生了」",
            perturb_never_applied, "S2"),
        neg("N3", "伪造「扰动生效了但 fit 没修回来」⟹ S2 翻红",
            never_healed, "S2"),
        neg("N4", "把「第二次」读数改掉 ⟹ S3 的「已是不动点」翻红",
            still_moving, "S3"),
        neg("N5", "★ 伪造「拖拽其实没生效」⟹ S4 翻红（否则「框贴合」可能只是没拖）",
            drag_didnt_happen, "S4"),
        neg("N6", "把组的 DOM 框缩小 200px ⟹ S5 翻红（store 贴合、屏幕不贴合）",
            dom_not_fitted, "S5"),
        neg("N7", "反向对照：只动 `secs` 这个与任何判据无关的字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 810, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"] + " ｜ 翻红：" +
              str([f[:12] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())
