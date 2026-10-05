#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 802 汇编器 —— `createImageHdPreset`：从**组内**源节点建组，组会错位

## 判据：**不涉及任何常量**

「新组的位置由源的**绝对**位置决定」⟹ 所以：

> **宿主组移动 Δ，新组也必须移动 Δ。**

实现用的是源的**相对**位置时，新组会纹丝不动 ⟹ 缺陷一眼可见，
而且不需要知道源码里的偏移是 320 还是别的。

## 独立重算

`walk_abs`（本文件自己写的沿 `parentId` 链求和）用来独立算出
「源的绝对位置」与「丢掉的祖先偏移」，不读源码公式。
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRE = ROOT / "raw" / "vb802a-pre.json"
POST = ROOT / "raw" / "vb802a-post.json"
SCAN = ROOT / "raw" / "scan802.json"
OUT = ROOT / "audit-802.json"
SRC = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/src/store/canvasStore.ts")


def rows(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in rd.get("rows", []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def live(tbl, arm):
    return [r for r in tbl.get(arm, []) if not r.get("FAILED")]


# ★ 探针把 `srcPos` / `srcAbs` / `newGroupPos` 都存成**扁平的 {x,y}**
#   （`srcAbs` 多一个 depth），所以三个取值器可以合成一个。
def pos(r, key):
    v = r[key]
    return (v["x"], v["y"]) if "pos" not in v else (v["pos"]["x"], v["pos"]["y"])


def abs_(r, key):
    return pos(r, key)


def walk_abs(nodes, nid):
    """★ 独立重算：沿 parentId 链把**相对**坐标累加成绝对坐标。"""
    idx = dict((n["id"], n) for n in nodes)
    n = idx.get(nid)
    if n is None:
        return None
    x, y = n["pos"]["x"], n["pos"]["y"]
    pid, seen, hops = n.get("parentId"), set([nid]), 0
    while pid and pid in idx and pid not in seen and hops < 32:
        seen.add(pid)
        hops += 1
        p = idx[pid]
        x += p["pos"]["x"]
        y += p["pos"]["y"]
        pid = p.get("parentId")
    return x, y


def main():
    pre = rows(json.loads(PRE.read_text(encoding="utf-8")))
    post = rows(json.loads(POST.read_text(encoding="utf-8")))
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    src = SRC.read_text(encoding="utf-8")
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "pass": bool(ok), "evidence": ev})

    # ── S1 普查覆盖度：数字全部来自机器，不手写
    high = [a["name"] for a in scan["actions"] if a["risk"].startswith("高")]
    add("S1:★★ 普查覆盖：写点 / 动作 / fit 调用三个数由 AST 数出",
        "★ 799、800 各手工找一处 ⟹ 本批改成**机器普查**：把「把 nodes 写进 canvas」"
        "的每一个写点列出来，逐个标注是否经 fit、是否碰坐标系",
        scan["totalWritePoints"] > 0 and scan["totalFitCalls"] > 0
        and len(scan["actions"]) > 0,
        {"写点合计": scan["totalWritePoints"], "动作数": len(scan["actions"]),
         "fit 调用合计": scan["totalFitCalls"], "高风险动作": high})

    # ── S2 阴性对照前提：loose 臂的源**确实**没有祖先
    ev = []
    for phase, tbl in (("pre", pre), ("post", post)):
        for i, r in enumerate(live(tbl, "presetFromLoose")):
            recomputed = walk_abs(r["before"]["nodes"], r["sourceId"])
            ev.append({"相位": phase, "轮": i,
                       "源 abs": list(abs_(r, "srcAbs")),
                       "源 pos": list(pos(r, "srcPos")),
                       "独立重算的绝对": list(recomputed) if recomputed else None,
                       "确实无祖先": recomputed == abs_(r, "srcAbs")})
    add("S2:★★ 阴性对照前提：loose 臂的源**确实**没有祖先",
        "★ 「祖先偏移为 0」是该臂全对的**前提** ⟹ 不成立的话它什么也证明不了",
        ev and all(x["确实无祖先"] for x in ev), ev)

    # ── S3 阳性对照：组与 child 都真的建了、child 挂在新组下
    ev = []
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in ("presetFromLoose", "presetFromGroupedA", "presetFromGroupedB"):
            for i, r in enumerate(live(tbl, arm)):
                ev.append({"相位": phase, "臂": arm, "轮": i,
                           "新建节点数": len(r["freshIds"]),
                           "子节点数": r["kidsCount"],
                           "子节点都挂在新组下": all(r["kidsParented"])})
    add("S3:★ 阳性对照：组与 child 都建了，child 的 `parentId` 指向新组",
        "★ 没有它，「什么都没发生」也会让「新组位置不变」成立 ⟹ 假绿",
        ev and all(x["子节点数"] == 1 and x["子节点都挂在新组下"] for x in ev), ev)

    # ── B1 缺陷复现：宿主组移动 Δ，新组**不动**
    ev = []
    for tbl, phase in ((pre, "pre"), (post, "post")):
        a = live(tbl, "presetFromGroupedA")
        b = live(tbl, "presetFromGroupedB")
        for i, (x, y) in enumerate(zip(a, b)):
            host = (y["hostOrigin"][0] - x["hostOrigin"][0],
                    y["hostOrigin"][1] - x["hostOrigin"][1])
            newg = (pos(y, "newGroupPos")[0] - pos(x, "newGroupPos")[0],
                    pos(y, "newGroupPos")[1] - pos(x, "newGroupPos")[1])
            # ★ 不要叫 `src` —— 同名局部变量会盖掉源码文本，下面 S4 还要用
            srcMoved = (abs_(y, "srcAbs")[0] - abs_(x, "srcAbs")[0],
                        abs_(y, "srcAbs")[1] - abs_(x, "srcAbs")[1])
            ev.append({"相位": phase, "轮": i,
                       "宿主组移动": list(host), "源绝对移动": list(srcMoved),
                       "新组移动": list(newg),
                       "新组跟着动": newg == host,
                       "差的正是被丢掉的祖先": (newg[0] - host[0], newg[1] - host[1])})
    pre_bad = [x for x in ev if x["相位"] == "pre"]
    add("B1:★★ 缺陷复现：pre 里宿主组移动了，新组**纹丝不动**",
        "★ 这是 802 的判据本体 ⟹ 完全不涉及任何常量",
        all(not x["新组跟着动"] and x["宿主组移动"] != (0, 0) for x in pre_bad), ev)

    # ── F1 修复生效：新组跟着宿主组动
    post_ok = [x for x in ev if x["相位"] == "post"]
    add("F1:★★★ 修复生效：post 里新组**跟着宿主组**一起动",
        "★ 判据是「相对关系」而不是绝对坐标 ⟹ 改对改错都判得出来",
        post_ok and all(x["新组跟着动"] for x in post_ok), ev)

    # ── F2 三条臂的「新组 − 源绝对」偏移完全一致（用 loose 臂当基准，不写死）
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in ("presetFromLoose", "presetFromGroupedA", "presetFromGroupedB"):
            ds = set()
            for r in live(tbl, arm):
                ds.add((pos(r, "newGroupPos")[0] - abs_(r, "srcAbs")[0],
                        pos(r, "newGroupPos")[1] - abs_(r, "srcAbs")[1]))
            ev["%s %s" % (phase, arm)] = sorted(list(d) for d in ds)
    post_sets = [tuple(v[0]) for k, v in ev.items()
                 if k.startswith("post") and v]
    add("F2:★★ post 三条臂的「新组 − 源绝对」偏移**完全一致**",
        "★ loose 臂（源无祖先）当作基准，偏移值由读数给出、不写死",
        post_sets and len(set(post_sets)) == 1,
        {"逐臂偏移": ev, "post 的共同偏移": list(post_sets[0]) if post_sets else None})

    # ── R1 无回归：loose 臂 pre/post 逐位相同（parentAbs==0 ⟹ 恒等变换）
    ev, diff = [], []
    for i, (a, b) in enumerate(zip(live(pre, "presetFromLoose"),
                                    live(post, "presetFromLoose"))):
        same = (pos(a, "newGroupPos") == pos(b, "newGroupPos")
                and abs_(a, "srcAbs") == abs_(b, "srcAbs")
                and a["newGroupId"] != b["newGroupId"])
        ev.append({"轮": i, "新组位置一致": pos(a, "newGroupPos") == pos(b, "newGroupPos"),
                   "源绝对一致": abs_(a, "srcAbs") == abs_(b, "srcAbs"),
                   "组 id 确实换了一个": a["newGroupId"] != b["newGroupId"]})
        if not same:
            diff.append(i)
    add("R1:★★ 无回归：loose 臂（源无祖先）pre/post **逐位相同**",
        "★ 修复对「祖先偏移为 0」必须是**恒等**变换 ⟹ 逐位相同是最强证据",
        ev and not diff, {"比对数": len(ev), "不一致的轮": diff})

    # ── S4 静态锚点：改用 `sourceAbsolute`，旧的相对写法已消失
    # ★★ 第四次踩同一个坑：needle 只写 `createImageHdPreset: (imageNodeId`
    #   会**先命中接口声明**（`(imageNodeId: string) => void;`）而不是实现，
    #   段长只剩 112、里面没有函数体 ⟹ 两个检查都假。
    #   799（updateNodeData）、800（ungroupSelectedNodes）、801（duplicateGraphSelection）
    #   各踩过一次。**锚点必须带完整的参数类型标注**才能只命中实现。
    i0 = src.find("createImageHdPreset: (imageNodeId: string) => {")
    j = src.find("\n  createVideoContinuation: (", i0)
    seg = src[i0:j] if (i0 >= 0 and j > i0) else ""
    has_new = "getAbsoluteNodePosition(source, nodesById)" in seg
    has_old = "source.position.x + 320" in seg
    add("S4:★★ 静态锚点：`createImageHdPreset` 改用沿父链求和",
        "★ 旧的「相对位置 + 320」若还在别处复活，这条要红",
        has_new and not has_old,
        {"段长": len(seg), "用了 getAbsoluteNodePosition": has_new,
         "旧的相对写法仍在": has_old})

    report = {"batch": 802, "checks": checks,
              "passed": sum(1 for c in checks if c["pass"]),
              "total": len(checks),
              "survey": {"writePoints": scan["totalWritePoints"],
                         "actions": len(scan["actions"]),
                         "fitCalls": scan["totalFitCalls"]}}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print("  %-4s %s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["why"]))
        print("       %s" % json.dumps(c["evidence"], ensure_ascii=False)[:260])
    print("  %d/%d" % (report["passed"], report["total"]))
    print("wrote %s" % OUT)
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
