#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 800 汇编器 —— `ungroupSelectedNodes`：取消分组时成员**不该跳位**

## 判据

★ **不变量 U**：取消分组**前后**，每个成员的**绝对**位置必须**逐位相同**。
  ——「我只是取消了分组，东西不该跳」。这条与坐标系语义无关，
  只看用户看得见的位置。

★ 独立重算：脱管之后 `position` 就是绝对坐标 ⟹ 它必须等于
  **用 before 的 `parentId` 链**沿路求和算出来的值。本文件自己算这条链，
  **不读源码公式**。

## 三条臂里藏着两个阴性对照

- `keyboardRoundtrip`：**真实 UI 路径**（`page.tsx:1412` 的 `Shift+G`），
  组的沿途没有祖先 ⟹ 必须不动。
- `ungroupOuter`：取消**顶层**组，沿途同样没有祖先 ⟹ 必须不动。
- `ungroupInner`：取消**嵌套**组，沿途有一个祖先 ⟹ 这才是缺陷臂。

★ 前两条与第三条是**同一个操作**在不同祖先深度下的表现 ⟹
  两者的**差**就是缺陷本身，不需要另找对照。
"""
import copy
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRE = ROOT / "raw" / "vb800a-pre.json"
POST = ROOT / "raw" / "vb800a-post.json"
OUT = ROOT / "audit-800.json"
SRC = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/src/store/canvasStore.ts")


# ---------------------------------------------------------------- 读数工具
def rows(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in rd.get("rows", []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def chain_abs(before_nodes, node_id):
    """★ 独立重算：沿 before 的 `parentId` 链把**相对**坐标累加成绝对坐标。

    ★ 第一版把 `abs` 当起点**又**累加各级祖先的 `abs` ⟹ 重复计入，
      重算出 `[720,570]` 这种数。起点必须是 `position`（相对），加的是
      各级祖先的 `position`。
    """
    index = dict((n["id"], n) for n in before_nodes)
    node = index.get(node_id)
    if node is None:
        return None
    x, y = node["pos"]["x"], node["pos"]["y"]
    pid, seen, hops = node.get("parentId"), set([node_id]), 0
    while pid and pid in index and pid not in seen and hops < 32:
        seen.add(pid)
        hops += 1
        parent = index[pid]
        x += parent["pos"]["x"]
        y += parent["pos"]["y"]
        pid = parent.get("parentId")
    return x, y


def moved(before_nodes, after_nodes, watch):
    """返回 {id: (前绝对, 后绝对, 是否动了, 偏移量)}"""
    b = dict((n["id"], n) for n in before_nodes)
    a = dict((n["id"], n) for n in after_nodes)
    out = {}
    for i in watch:
        if i not in b or i not in a:
            out[i] = None
            continue
        bx, by = b[i]["abs"]["x"], b[i]["abs"]["y"]
        ax, ay = a[i]["abs"]["x"], a[i]["abs"]["y"]
        out[i] = {"before": (bx, by), "after": (ax, ay),
                  "moved": (bx, by) != (ax, ay),
                  "delta": (ax - bx, ay - by)}
    return out


def main():
    pre = rows(json.loads(PRE.read_text(encoding="utf-8")))
    post = rows(json.loads(POST.read_text(encoding="utf-8")))
    src = SRC.read_text(encoding="utf-8")
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "pass": bool(ok), "evidence": ev})

    def arms_of(table, arm):
        return [(i, r) for i, r in enumerate(table.get(arm, []))
                if not r.get("FAILED")]

    # ── U1 阳性对照：解除后 `parentId` 确实被删（否则「什么都没发生」也过）
    ev = {}
    for arm in ("ungroupInner", "ungroupOuter"):
        for i, r in arms_of(post, arm):
            after = dict((n["id"], n) for n in r["after"]["nodes"])
            before = dict((n["id"], n) for n in r["before"]["nodes"])
            ev["%s#%d" % (arm, i)] = {
                nid: (before[nid].get("parentId"), after[nid].get("parentId"))
                for nid in r["watch"]}
    ok = ev and all(before is not None and after is None
                    for d in ev.values() for before, after in d.values())
    add("U1:★ 阳性对照：解除后成员的 `parentId` 确实变成空",
        "★ 没有它，「操作什么都没发生」也会让不变量 U 成立 ⟹ 假绿",
        ok, ev)

    # ── U2 阴性对照：键盘臂（真实 UI 路径）必须不动
    ev = {}
    for i, r in arms_of(pre, "keyboardRoundtrip"):
        ev["#%d" % i] = moved(r["before"]["nodes"], r["after"]["nodes"],
                              r["members"])
    add("U2:★★ 阴性对照：`G` → `Shift+G` 键盘往返，成员**不动**",
        "★ 纯 UI 用户路径，组没有父节点 ⟹ 沿途无祖先可丢",
        ev and all(not v["moved"] for d in ev.values() for v in d.values()
                   if v), ev)

    # ── U3 阴性对照：取消**顶层**组必须不动
    ev = {}
    for phase, table in (("pre", pre), ("post", post)):
        for i, r in arms_of(table, "ungroupOuter"):
            ev["%s#%d" % (phase, i)] = moved(
                r["before"]["nodes"], r["after"]["nodes"], r["watch"])
    add("U3:★★ 阴性对照：取消**顶层**组，成员与子组**不动**（pre/post 都要求）",
        "★ 与缺陷臂是**同一个操作**，唯一差别是沿途有没有祖先 ⟹ "
        "两者的差就是缺陷本身",
        ev and all(not v["moved"] for d in ev.values() for v in d.values()
                   if v), ev)

    # ── B1 缺陷复现：pre 取消内层组成员跳位
    ev = {}
    for i, r in arms_of(pre, "ungroupInner"):
        m = moved(r["before"]["nodes"], r["after"]["nodes"], r["watch"])
        ev["#%d" % i] = {k: v["delta"] for k, v in m.items() if v}
    add("B1:★★ 缺陷复现：pre 取消内层组成员**跳位**",
        "★ 799 的姊妹缺陷 —— 同一类坐标系错误（把父的相对位置当成绝对位置）",
        ev and all(d and all(v != (0, 0) for v in d.values())
                   for d in ev.values()), ev)

    # ── B2 跳的量必须**逐位等于**沿途祖先位置的相反数（把「为什么跳」钉死）
    ev = {}
    for i, r in arms_of(pre, "ungroupInner"):
        before = dict((n["id"], n) for n in r["before"]["nodes"])
        m = moved(r["before"]["nodes"], r["after"]["nodes"], r["watch"])
        chain = chain_abs(r["before"]["nodes"], r["watch"][0])
        own = chain_abs(r["before"]["nodes"], r["groupId"])
        for k, v in m.items():
            if not v:
                continue
            # 丢掉的那段 = 组自己的**绝对**位置 - 组自己的**相对** position
            # ★ 第一版把 `abs` 当成「组自身 position」用了 ⟹ 算出「丢掉 0」，
            #   断言红了。取相对位置要用 `pos`，`abs` 是绝对坐标。
            g = before[r["groupId"]]
            lost = (own[0] - g["pos"]["x"], own[1] - g["pos"]["y"])
            ev["#%d %s" % (i, k)] = {
                "跳了": v["delta"],
                "组自身 position（相对）": (g["pos"]["x"], g["pos"]["y"]),
                "组的绝对位置": own,
                "丢掉的那段": lost,
                "恰好相反": v["delta"] == (-lost[0], -lost[1])}
    add("B2:★★ 跳位量 = 沿途祖先偏移的**相反数**（机制被钉死，不是巧合）",
        "★ 只说「跳了」不够；说清「正好跳掉外层组的位置」才是机制",
        ev and all(d["恰好相反"] for d in ev.values()), ev)

    # ── F1 修复生效：post 取消内层组也不动
    ev = {}
    for i, r in arms_of(post, "ungroupInner"):
        m = moved(r["before"]["nodes"], r["after"]["nodes"], r["watch"])
        ev["#%d" % i] = {k: v["delta"] for k, v in m.items() if v}
    add("F1:★★★ 修复生效：post 取消内层组成员**不动**",
        "★ 判据全用绝对位置 ⟹ 改对改错都判得出来",
        ev and all(d == {} or all(v == (0, 0) for v in d.values())
                   for d in ev.values()), ev)

    # ── R1 无回归：顶层组那条臂 pre/post 逐位相同（沿途无祖先 ⟹ 修复是恒等）
    ev = []
    for arm in ("ungroupOuter",):
        for i, (a, b) in enumerate(zip(pre.get(arm, []), post.get(arm, []))):
            if a.get("FAILED") or b.get("FAILED"):
                continue
            for nid in a["watch"]:
                if nid not in [n["id"] for n in b["before"]["nodes"]]:
                    continue
                ev.append({"臂": arm, "轮": i, "id": nid,
                           "abs": (dict((n["id"], n) for n in a["before"]["nodes"])[nid]["abs"],
                                   dict((n["id"], n) for n in b["before"]["nodes"])[nid]["abs"])})
    same = all(x["abs"][0] == x["abs"][1] for x in ev)
    add("R1:★★ 无回归：取消顶层组那条臂 pre/post 读数**逐位相同**",
        "★ 修复对「沿途无祖先」必须是**恒等**变换 ⟹ 逐位相同是最强证据",
        ev and same, {"比对数": len(ev), "不一致": [x for x in ev
                                                  if x["abs"][0] != x["abs"][1]]})

    # ── C1 独立重算：post 脱管后的 `position` 必须等于 before 沿链求和
    ev = {}
    for phase, table in (("pre", pre), ("post", post)):
        for arm in ("ungroupInner", "ungroupOuter"):
            for i, r in arms_of(table, arm):
                after = dict((n["id"], n) for n in r["after"]["nodes"])
                for nid in r["watch"]:
                    want = chain_abs(r["before"]["nodes"], nid)
                    got = after[nid]["abs"]
                    ev["%s %s#%d %s" % (phase, arm, i, nid)] = {
                        "重算": want, "实测": (got["x"], got["y"]),
                        "吻合": want == (got["x"], got["y"])}
    post_keys = [k for k in ev if k.startswith("post")]
    add("C1:★ 独立重算：post 脱管后的坐标 == 用 before 的父链求和",
        "★ 汇编器自己算那条链，不读源码公式 ⟹ 公式写错会被抓出来",
        post_keys and all(ev[k]["吻合"] for k in post_keys),
        {"post 侧": {k: ev[k] for k in post_keys},
         "pre 侧（应当对不上，缺陷就在这）":
             {k: v for k, v in ev.items() if k.startswith("pre")}})

    # ── S1 静态锚点：用 `getAbsoluteNodePosition`，旧的单层加法已消失
    #    ★ 下界要从**实现**那一行之后开始找：`updateNodeData` 的**接口声明**
    #      在文件前部（`nodeId?: string` 那种），先命中它会把段切成空串。
    i0 = src.find("ungroupSelectedNodes: (nodeIds) => {")
    i1 = src.find("\n  updateNodeData: (nodeId", i0 + 1) if i0 >= 0 else -1
    seg = src[i0:i1] if (i0 >= 0 and i1 > i0) else ""
    has_new = "getAbsoluteNodePosition(node, nodesById)" in seg
    has_old = "group.position.x + node.position.x" in seg
    add("S2:★★ 静态锚点：`ungroupSelectedNodes` 改用沿链求和",
        "★ 旧的 `group.position + node.position` 若还在别处复活，这条会红",
        has_new and not has_old,
        {"段长": len(seg), "用了 getAbsoluteNodePosition": has_new,
         "旧的单层加法仍在": has_old})

    # ── S2 记账：799 的修复没被碰
    has_fit = ("position: { x: nextPosition.x - parentAbs.x,"
               " y: nextPosition.y - parentAbs.y },") in src
    add("S3:记账：799 的修复仍在（没被本批改回去）",
        "★ 800 的修复是**另一处**坐标系，两个都要在",
        has_fit, {"parentAbs 写回仍在": has_fit})

    report = {"batch": 800, "checks": checks,
              "passed": sum(1 for c in checks if c["pass"]),
              "total": len(checks)}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print("  %-4s %s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["why"]))
        print("       %s" % json.dumps(c["evidence"], ensure_ascii=False)[:400])
    print("  %d/%d" % (report["passed"], report["total"]))
    print("wrote %s" % OUT)
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
