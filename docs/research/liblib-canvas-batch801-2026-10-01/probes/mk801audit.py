#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 801 汇编器 —— `duplicateGraphSelection`：副本应该只是原节点**整体平移**

## 起点

800 读了这个函数的源码，逻辑**看起来是对的**，但那只是静态结论。
794 的教训（`removeNode` 那处只有静态证据、不能写成「两处都验过了」）
⟹ 本批去取**行为证据**。

## ★ 判据

- **不变量 C1（平移）**：每个副本节点的**绝对**位置 = 其原节点的绝对位置 + 同一个偏移。
- **不变量 C2（结构）**：复制**组**时，副本与原的父子关系**逐条保持**；
  复制**组内一个成员**时，副本应当**脱管**、提升为顶层（**故意的**结构变化，
  按臂分开判，不与 C2 混成一条）。
- **不变量 C3（阳性）**：副本 id 与原 id **全都不同**，且副本数 = 预期。
  没有它，「什么都没复制」也会让 C1/C2 成立。
- **不变量 C4（父重映射）**：副本的 `parentId` 必须指向**副本集合内部**，
  而不是原来的组 —— 否则副本成员会挂回**原组**，画布上就是两份成员挤在一个框里。

## ★ 偏移 40 **不写死**（798 的教训）

先用「每个副本在 before 里找**最近**的原节点」配对，再要求**所有副本的偏移
向量完全相同**。那个共同值就是偏移 ⟹ 40 是**被反推出来的**，不是写进去的。
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRE = ROOT / "raw" / "vb801a-pre.json"
POST = ROOT / "raw" / "vb801a-post.json"
OUT = ROOT / "audit-801.json"

EXPECT_COPIES = {"copyFlatGroup": 3, "copyNested": 5, "copyMember": 1}
STRUCTURE_ARMS = ("copyFlatGroup", "copyNested")


def rows(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in rd.get("rows", []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def live(row):
    return [r for r in rows({"rounds": row}).get(row["arm"], []) if r]


def nearest(before_nodes, point, same_type=None):
    """★ 找绝对位置最近的原节点（不预设偏移是多少）。

    ★★ **同类型约束不是可有可无的**：副本组 `abs(188,-85)` 到「副本组
    `(148,-85)`」和到「某个成员 `(188,-45)`」的距离**都是 40** ⟹ 第一版
    取到了成员，于是「深度 0 vs 深度 1」被判成结构不一致。
    那不是实现错，是**配对歧义**。
    """
    best, best_d = None, None
    for n in before_nodes:
        if same_type is not None and n["type"] != same_type:
            continue
        d = abs(n["abs"]["x"] - point["x"]) + abs(n["abs"]["y"] - point["y"])
        if best_d is None or d < best_d:
            best, best_d = n, d
    return best, best_d


def pair_up(before_nodes, copy_ids, after_nodes):
    """★ 把每个副本配对到 before 里的原节点。

    ★ 配对**优先用 `data.tag`**（探针注入时写进去的原 id，`duplicateGraphSelection`
      复制时 `data: {...node.data}` 会继承）⟹ 精确、无歧义。
      拿不到 tag 的（UI 臂：种子节点与新组都没有）才退回「最近邻 + 同类型」，
      并把用了哪种方式**记进结果** ⟹ 不让「配对方式」变成隐式假设。
    """
    a = dict((n["id"], n) for n in after_nodes)
    by_id = dict((n["id"], n) for n in before_nodes)
    pairs, deltas, how, ambiguous = {}, [], {}, []
    for cid in copy_ids:
        c = a[cid]
        tag = c.get("tag")
        mate, how[cid] = None, None
        if tag and tag in by_id:
            mate, how[cid] = by_id[tag], "tag"
        if mate is None:
            mate, d = nearest(before_nodes, c["abs"], c["type"])
            how[cid] = "nearest"
            twins = [n for n in before_nodes if n["type"] == c["type"]
                     and abs(n["abs"]["x"] - c["abs"]["x"])
                     + abs(n["abs"]["y"] - c["abs"]["y"]) == d]
            if len(twins) > 1:
                ambiguous.append({"copy": cid, "并列候选": [t["id"] for t in twins]})
        if mate is None:
            pairs[cid] = None
            continue
        pairs[cid] = mate["id"]
        deltas.append((c["abs"]["x"] - mate["abs"]["x"],
                       c["abs"]["y"] - mate["abs"]["y"]))
    return pairs, deltas, {"how": how, "ambiguous": ambiguous}


def analyse(row):
    b = row["before"]["nodes"]
    a = row["after"]["nodes"]
    copy_ids = row["copyIds"]
    orig_ids = set(n["id"] for n in b)
    pairs, deltas, meta = pair_up(b, copy_ids, a)
    a_idx = dict((n["id"], n) for n in a)
    b_idx = dict((n["id"], n) for n in b)
    return {
        "copyIds": copy_ids,
        "pairs": pairs,
        "pairing": meta,
        "uniformDelta": (len(set(deltas)) == 1),
        "delta": deltas[0] if deltas and len(set(deltas)) == 1 else deltas,
        "idsDisjoint": all(c not in orig_ids for c in copy_ids),
        "countOk": len(copy_ids) == EXPECT_COPIES[row["arm"]],
        # 结构：副本的父是否非空，与配对原节点是否一致；深度是否一致
        "parentParity": {c: (bool(a_idx[c]["parentId"]),
                             bool(b_idx[pairs[c]]["parentId"]))
                         for c in copy_ids if pairs.get(c)},
        "depthSame": {c: (a_idx[c]["abs"]["depth"],
                          b_idx[pairs[c]]["abs"]["depth"])
                      for c in copy_ids if pairs.get(c)},
        "parentIsCopy": {c: (a_idx[c]["parentId"] in copy_ids
                             if a_idx[c]["parentId"] else None)
                         for c in copy_ids},
        "copyDetached": {c: (a_idx[c]["parentId"], a_idx[c]["abs"]["depth"])
                         for c in copy_ids},
    }


def main():
    pre = rows(json.loads(PRE.read_text(encoding="utf-8")))
    post = rows(json.loads(POST.read_text(encoding="utf-8")))
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "pass": bool(ok), "evidence": ev})

    # ── C1 偏移反推：所有副本的偏移向量必须**完全相同**（40 由它反推出来）
    ev, deltas = {}, set()
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in EXPECT_COPIES:
            for i, r in enumerate([x for x in tbl.get(arm, [])
                                   if not x.get("FAILED")]):
                a = analyse(r)
                ev["%s %s#%d" % (phase, arm, i)] = a["delta"]
                if a["uniformDelta"]:
                    deltas.add(a["delta"])
    add("C1:★★ 偏移由 raw **反推**得出，且所有副本**完全一致**",
        "★ 40 不写死：先按最近邻配对，再要求所有偏移相同 ⟹ 那个共同值才是偏移",
        ev and len(deltas) == 1, {"逐臂反推": ev, "共同值": sorted(deltas)})

    # ── C2 每个副本的绝对位置 == 配对原节点 + 反推出来的偏移
    off = sorted(deltas)[0] if len(deltas) == 1 else None
    ev, bad = {}, []
    for arm in EXPECT_COPIES:
        for i, r in enumerate([x for x in pre.get(arm, [])
                               if not x.get("FAILED")]):
            a = analyse(r)
            b_idx = dict((n["id"], n) for n in r["before"]["nodes"])
            for c in a["copyIds"]:
                mate = a["pairs"].get(c)
                if not mate or off is None:
                    bad.append("%s#%d %s 配不上" % (arm, i, c))
                    continue
                src = b_idx[mate]
                dst = [n for n in r["after"]["nodes"] if n["id"] == c][0]
                want = (src["abs"]["x"] + off[0], src["abs"]["y"] + off[1])
                got = (dst["abs"]["x"], dst["abs"]["y"])
                ev["%s#%d %s" % (arm, i, c[:10])] = {"配到的原": mate[:10],
                                                      "应有": list(want),
                                                      "实得": list(got)}
                if want != got:
                    bad.append("%s#%d %s %r != %r" % (arm, i, c, want, got))
    add("C2:★★ 每个副本的绝对位置 == 配对原节点 + 反推出来的偏移",
        "★ 这是「复制 = 整体平移」这句话的逐条核对",
        ev and not bad, {"偏移": off, "逐条": ev, "不符": bad})

    # ── C3 阳性对照：id 全不同 + 数量符合预期
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm, want in EXPECT_COPIES.items():
            for i, r in enumerate([x for x in tbl.get(arm, [])
                                   if not x.get("FAILED")]):
                a = analyse(r)
                ev["%s %s#%d" % (phase, arm, i)] = {
                    "副本数": len(a["copyIds"]), "预期": want,
                    "id 与原全不相交": a["idsDisjoint"]}
    add("C3:★ 阳性对照：副本 id 与原 id 全不相交，且副本数符合预期",
        "★ 没有它，「什么都没复制」也会让 C1/C2 成立",
        ev and all(v["id 与原全不相交"] and v["副本数"] == v["预期"]
                   for v in ev.values()), ev)

    # ── C4 结构保持（复制组的两条臂）
    ev = {}
    for arm in STRUCTURE_ARMS:
        for i, r in enumerate([x for x in post.get(arm, [])
                               if not x.get("FAILED")]):
            a = analyse(r)
            ev["%s#%d" % (arm, i)] = {
                "父子非空性一致": a["parentParity"],
                "深度一致": a["depthSame"]}
    ok = ev and all(
        all(p[0] == p[1] for p in d["父子非空性一致"].values())
        and all(x == y for x, y in d["深度一致"].values())
        for d in ev.values())
    add("C4:★★ 复制**组**时，父子关系与**深度**逐条保持",
        "★ 嵌套那条臂是关键：副本内层组的父必须是**副本外层组**，不能是原组",
        ok, ev)

    # ── C5 父重映射：副本的父必须落在副本集合内
    ev = {}
    for arm in STRUCTURE_ARMS:
        for i, r in enumerate([x for x in post.get(arm, [])
                               if not x.get("FAILED")]):
            a = analyse(r)
            ev["%s#%d" % (arm, i)] = {
                c: p for c, p in a["parentIsCopy"].items() if p is not None}
    ok = ev and all(all(v is True for v in d.values()) for d in ev.values())
    add("C5:★★ 副本的父指向**副本集合内部**（不是原组）",
        "★ 否则副本成员会挂回**原组** ⟹ 画布上两份成员挤在一个框里",
        ok, ev)

    # ── C6 复制**成员**时应当脱管、提升为顶层（故意的结构变化）
    ev = {}
    for i, r in enumerate([x for x in post.get("copyMember", [])
                           if not x.get("FAILED")]):
        a = analyse(r)
        ev["#%d" % i] = a["copyDetached"]
    ok = ev and all(all(p is None and d == 0 for p, d in d_.values())
                    for d_ in ev.values())
    add("C6:★ 复制组内**一个成员**时，副本**脱管**且深度为 0",
        "★ 这是**故意**的结构变化（`:889` 那个分支）⟹ 与 C4 分开判，不混成一条",
        ok, ev)

    # ── C7 快捷键可用：`Cmd+D` 之后节点数应 +3
    ev = {}
    for i, r in enumerate([x for x in pre.get("copyFlatGroup", [])
                           if not x.get("FAILED")]):
        g, b = r.get("afterGrouping"), r["before"]
        ev["#%d" % i] = {
            "造组后": g["total"] if g else None, "按 Cmd+D 后": b["total"],
            "增了": (b["total"] - g["total"]) if g else None,
            "按 Cmd+D 前选区": r.get("selectedBeforeKey")}
    ok = ev and all(v["增了"] == 3 for v in ev.values())
    add("C7:★★ 快捷键可用：`Cmd+D` 真的复制了 3 个节点（纯 UI 路径）",
        "★ 第一版我一度以为「Cmd+D 没生效」⟹ 那是**我数错了节点基数**"
        "（种子有 2 个组、造组 +1）。诊断 `diag801.py` 逐条记了 keydown 事件，"
        "证明事件确实送达且被处理",
        ok, ev)

    # ── C8 可复现：pre 与 post 逐位相同（本批**没改** `src/`）
    ev = []
    for arm in EXPECT_COPIES:
        for i, (a, b) in enumerate(zip(pre.get(arm, []), post.get(arm, []))):
            if a.get("FAILED") or b.get("FAILED"):
                continue
            aa, bb = analyse(a), analyse(b)
            # ★ 不能比 id 列表：副本 id 每次都带时间戳，必然不同
            ev.append({"臂": arm, "轮": i, "偏移一致": aa["delta"] == bb["delta"],
                       "副本数一致": len(aa["copyIds"]) == len(bb["copyIds"]),
                       "结构一致": sorted(aa["parentParity"].values())
                       == sorted(bb["parentParity"].values())})
    add("C8:★★ 可复现：pre 与 post 的配对与偏移**完全一致**",
        "★ 本批**没改** `src/` ⟹ 两份 raw 应当一致 ⟹ 不一致就说明其中一份不是本批代码跑的",
        ev and all(x["偏移一致"] and x["副本数一致"] and x["结构一致"]
                   for x in ev),
        {"比对数": len(ev),
         "不一致": [x for x in ev if not (x["偏移一致"] and x["副本数一致"]
                                          and x["结构一致"])]})

    report = {"batch": 801, "checks": checks,
              "passed": sum(1 for c in checks if c["pass"]),
              "total": len(checks)}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print("  %-4s %s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["why"]))
        print("       %s" % json.dumps(c["evidence"], ensure_ascii=False)[:300])
    print("  %d/%d" % (report["passed"], report["total"]))
    print("wrote %s" % OUT)
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
