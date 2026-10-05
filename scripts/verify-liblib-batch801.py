#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 801 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

801 是**纯测量批次**（`src/` 一行没改）：`duplicateGraphSelection` 被 800 读源码
觉得对，但**没有行为证据** ⟹ 本批去取证据。要防的错误方向是**假绿**：

- ★★ **配对本身可能出错**，而不是被测对象出错。第一版用「最近邻」配对，
  副本组 `abs(188,-85)` 到「副本组 `(148,-85)`」和到「某个成员 `(188,-45)`」
  距离**都是 40** ⟹ 取到了成员，于是「深度 0 vs 1」被判成结构不一致。
  修法两条：① 最近邻必须**加同类型约束**；② 注入的节点带 `data.tag`（原 id），
  复制时 `data` 会被继承 ⟹ **tag 配对精确无歧义**。两种方式都记进结果，
  不让「配对方式」变成隐式假设（S1 把它们摆出来）。
- ★★ **「什么都没复制」也会让「整体平移」成立** ⟹ 必须有阳性对照（S3）。
- ★ **偏移 40 不写死**（798 的教训）：先用配对算出每个副本的偏移，
  再要求**所有副本完全一致** ⟹ 那个共同值才是偏移。
- ★ **结构变化按臂分开判**：复制**组**时父子关系与深度应**保持**（S4）；
  复制**组内一个成员**时副本应**脱管**、成为顶层（S6）——这是**故意**的行为，
  混成一条判就会把「正确」判成「错误」。
- ★ **本批没改 `src/`** ⟹ S10 用 `git status` 把它钉死，否则后人得重新判断
  「这份 raw 是不是本批代码跑的」。
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch801-2026-10-01"
PRE = OUTDIR / "raw/vb801a-pre.json"
POST = OUTDIR / "raw/vb801a-post.json"
AUDIT = OUTDIR / "audit-801.json"
REPORT = OUTDIR / "verify-report.json"
CS = "src/store/canvasStore.ts"

WANT = {"copyFlatGroup": 3, "copyNested": 5, "copyMember": 1}
GROUP_ARMS = ("copyFlatGroup", "copyNested")


# ============================================================ 独立实现
def index_of(nodes):
    return dict((n["id"], n) for n in nodes)


def rows_of(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in rd.get("rows", []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def live(tbl, arm):
    return [r for r in tbl.get(arm, []) if not r.get("FAILED")]


def match(before, after, copy_ids):
    """★ 优先按 `data.tag` 配对；拿不到 tag 才退回「最近邻 + 同类型」。"""
    b, a = index_of(before), index_of(after)
    out = {}
    for cid in copy_ids:
        c = a[cid]
        tag = c.get("tag")
        if tag and tag in b:
            out[cid] = (tag, "tag")
            continue
        best, bestd, twins = None, None, 0
        for n in before:
            if n["type"] != c["type"]:
                continue
            d = abs(n["abs"]["x"] - c["abs"]["x"]) + abs(n["abs"]["y"] - c["abs"]["y"])
            if bestd is None or d < bestd:
                best, bestd, twins = n, d, 1
            elif d == bestd:
                twins += 1
        out[cid] = (best["id"] if best else None, "nearest(并列%d)" % twins)
    return out


def deltas_of(before, after, copy_ids):
    b, a = index_of(before), index_of(after)
    m = match(before, after, copy_ids)
    out = {}
    for cid, (mid, how) in m.items():
        if not mid:
            out[cid] = (None, how)
            continue
        out[cid] = ((a[cid]["abs"]["x"] - b[mid]["abs"]["x"],
                     a[cid]["abs"]["y"] - b[mid]["abs"]["y"]), how)
    return out


# ============================================================ 检查
def run_checks(pre_raw, post_raw, src, audit, src_dirty):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    pre, post = rows_of(pre_raw), rows_of(post_raw)

    # ── S1 偏移反推 + 配对方式摆出来
    ev, all_off, hows = {}, set(), set()
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in WANT:
            for i, r in enumerate(live(tbl, arm)):
                d = deltas_of(r["before"]["nodes"], r["after"]["nodes"],
                              r["copyIds"])
                ev["%s %s#%d" % (phase, arm, i)] = {
                    k: {"偏移": list(v[0]) if v[0] else None, "配对方式": v[1]}
                    for k, v in d.items()}
                hows |= set(v[1] for v in d.values())
                for v in d.values():
                    if v[0]:
                        all_off.add(v[0])
    add("S1:★★ 偏移由 raw **反推**且所有副本**完全一致**；配对方式显式记账",
        "★ 40 不写死；且「配对方式」不能是隐式假设 —— tag 配对精确、"
        "最近邻可能并列",
        ev and len(all_off) == 1,
        {"共同偏移": sorted(all_off), "用到的配对方式": sorted(hows),
         "逐条": ev})

    off = sorted(all_off)[0] if len(all_off) == 1 else None
    ev, bad = {}, []
    for arm in WANT:
        for i, r in enumerate(live(pre, arm)):
            b, a = index_of(r["before"]["nodes"]), index_of(r["after"]["nodes"])
            m = match(r["before"]["nodes"], r["after"]["nodes"], r["copyIds"])
            for cid, (mid, how) in m.items():
                if not mid or off is None:
                    bad.append("%s#%d %s 配不上" % (arm, i, cid))
                    continue
                want = (b[mid]["abs"]["x"] + off[0], b[mid]["abs"]["y"] + off[1])
                got = (a[cid]["abs"]["x"], a[cid]["abs"]["y"])
                ev["%s#%d %s" % (arm, i, cid[:9])] = {
                    "源": mid[:9], "配对": how,
                    "应有": list(want), "实得": list(got)}
                if want != got:
                    bad.append("%s#%d %s %r≠%r" % (arm, i, cid, want, got))
    add("S2:★★ 每个副本的绝对位置 == 源节点 + 反推出来的偏移",
        "★ 这是「复制 = 整体平移」的逐条核对", ev and not bad,
        {"偏移": off, "逐条": ev, "不符": bad})

    # ── S3 阳性对照
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm, want_n in WANT.items():
            for i, r in enumerate(live(tbl, arm)):
                orig = set(n["id"] for n in r["before"]["nodes"])
                ev["%s %s#%d" % (phase, arm, i)] = {
                    "副本数": len(r["copyIds"]), "预期": want_n,
                    "id 与原不相交": all(c not in orig for c in r["copyIds"])}
    add("S3:★ 阳性对照：副本 id 与原 id 全不相交，且数量符合预期",
        "★ 没有它，「什么都没复制」也会让 S2 成立",
        ev and all(v["id 与原不相交"] and v["副本数"] == v["预期"]
                   for v in ev.values()), ev)

    # ── S4 复制组：父子非空性与深度逐条保持
    ev = {}
    for arm in GROUP_ARMS:
        for i, r in enumerate(live(post, arm)):
            b, a = index_of(r["before"]["nodes"]), index_of(r["after"]["nodes"])
            m = match(r["before"]["nodes"], r["after"]["nodes"], r["copyIds"])
            ev["%s#%d" % (arm, i)] = {
                cid[:9]: {"副本有父": bool(a[cid]["parentId"]),
                          "源有父": bool(b[mid]["parentId"]),
                          "副本深度": a[cid]["abs"]["depth"],
                          "源深度": b[mid]["abs"]["depth"]}
                for cid, (mid, how) in m.items() if mid}
    ok = ev and all(
        v["副本有父"] == v["源有父"] and v["副本深度"] == v["源深度"]
        for d in ev.values() for v in d.values())
    add("S4:★★ 复制**组**时，父子关系与**深度**逐条保持",
        "★ 嵌套那条臂是关键：副本内层组的父必须是**副本外层组**", ok, ev)

    # ── S5 父重映射到副本集合内部
    ev = {}
    for arm in GROUP_ARMS:
        for i, r in enumerate(live(post, arm)):
            a = index_of(r["after"]["nodes"])
            copy_set = set(r["copyIds"])
            ev["%s#%d" % (arm, i)] = {
                cid[:9]: (a[cid]["parentId"] in copy_set
                          if a[cid]["parentId"] else None)
                for cid in r["copyIds"]}
    ok = ev and all(all(v is True for v in d.values() if v is not None)
                    for d in ev.values())
    add("S5:★★ 副本的父指向**副本集合内部**（不是原组）",
        "★ 否则副本成员会挂回原组 ⟹ 两份成员挤在一个框里", ok, ev)

    # ── S6 复制成员：脱管 + 深度 0
    ev = {}
    for i, r in enumerate(live(post, "copyMember")):
        a = index_of(r["after"]["nodes"])
        ev["#%d" % i] = {cid[:9]: [a[cid]["parentId"], a[cid]["abs"]["depth"]]
                         for cid in r["copyIds"]}
    ok = ev and all(p is None and d == 0 for x in ev.values()
                    for p, d in x.values())
    add("S6:★ 复制组内**一个成员**时，副本**脱管**且深度 0",
        "★ 这是**故意**的结构变化 ⟹ 与 S4 分开判，混成一条会把正确判成错误", ok, ev)

    # ── S7 快捷键可用
    ev = {}
    for i, r in enumerate(live(pre, "copyFlatGroup")):
        g = r.get("afterGrouping")
        ev["#%d" % i] = {
            "造组后": g["total"] if g else None,
            "按 Cmd+D 后": r["before"]["total"],
            "增了": (r["before"]["total"] - g["total"]) if g else None,
            "按键前选区": r.get("selectedBeforeKey")}
    add("S7:★★ 快捷键可用：`Cmd+D` 真的复制了 3 个节点",
        "★ 我一度以为「Cmd+D 没生效」⟹ 那是**数错了节点基数**；"
        "`diag801.py` 逐条记 keydown 证明事件送达且被处理",
        ev and all(v["增了"] == 3 for v in ev.values()), ev)

    # ── S8 可复现（没改 src ⟹ 两份 raw 应当一致）
    ev = []
    for arm in WANT:
        for i, (x, y) in enumerate(zip(live(pre, arm), live(post, arm))):
            dx = deltas_of(x["before"]["nodes"], x["after"]["nodes"], x["copyIds"])
            dy = deltas_of(y["before"]["nodes"], y["after"]["nodes"], y["copyIds"])
            ev.append({"臂": arm, "轮": i,
                       "偏移一致": sorted(v[0] for v in dx.values() if v[0])
                       == sorted(v[0] for v in dy.values() if v[0]),
                       "副本数一致": len(dx) == len(dy)})
    add("S8:★★ 可复现：pre 与 post 的偏移与副本数**完全一致**",
        "★ 本批没改 `src/` ⟹ 不一致就说明其中一份不是本批代码跑的",
        ev and all(x["偏移一致"] and x["副本数一致"] for x in ev),
        {"比对数": len(ev),
         "不一致": [x for x in ev if not (x["偏移一致"] and x["副本数一致"])]})

    # ── S9 静态锚点：两个分支都还在
    #    ★ 下界要用**实现**的 `duplicateSelectedNodes: (nodeIds) => {`——
    #      `:380` 那个是接口声明，会把段切成空串（同 800 踩过）。
    i0 = src.find("function duplicateGraphSelection(")
    i1 = src.find("\n  duplicateSelectedNodes: (nodeIds) => {", i0 + 1) if i0 >= 0 else -1
    seg = src[i0:i1] if (i0 >= 0 and i1 > i0) else ""
    has_keep = "copiedNode.position = { ...node.position };" in seg
    has_promote = "delete copiedNode.parentId;" in seg
    add("S9:★★ 静态锚点：两个分支都还在（保持相对 / 提升为顶层）",
        "★ 行为证据（S1–S8）之外，再钉住「代码没被改回去」",
        has_keep and has_promote,
        {"段长": len(seg), "父也被复制时保持相对": has_keep,
         "父没被复制时提升为顶层": has_promote})

    # ── S10 记账：本批没改 src（用 git 钉死）
    add("S10:★★ 记账：本批**没改** `src/`",
        "★ 纯测量批次必须被钉住，否则后人得重新判断「这份 raw 是不是本批代码跑的」",
        not src_dirty, {"git status --porcelain src/": src_dirty})

    if audit:
        add("S11:汇编器零失败", "汇编器自己的断言必须全绿",
            audit.get("passed") == audit.get("total"),
            {"passed": audit.get("passed"), "total": audit.get("total")})

    return checks


# ============================================================ 变异器
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mut_text(path, old, new, allow_superset=False):
    """★ 所有校验都在**写入之前**完成 ⟹ 失败时工作区一个字节都不会脏。"""
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    assert orig.count(old) == 1, "★ needle 不唯一：%r" % old[:70]
    txt = orig.replace(old, new)
    ev = {"新的在": new in txt,
          "行数中性": len(txt.split("\n")) == len(orig.split("\n"))}
    if allow_superset:
        ev["旧串仍在（预期）"] = old in txt
    else:
        ev["旧的不在"] = old not in txt
    assert all(ev.values()), "★ 变异没真改到目标性质：%r" % ev
    p.write_text(txt, encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


def mut_raw(path, fn):
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = fn(d)
    assert hit, "★ raw 变异没命中"
    payload = json.dumps(d, ensure_ascii=False, indent=1)
    p.write_text(payload, encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"file": p.name, "hit": hit}


def find_node(d, arm, member):
    for rd in d["rounds"]:
        for row in rd["rows"]:
            if row.get("arm") == arm and "after" in row:
                for n in row["after"]["nodes"]:
                    if n["id"] == member:
                        return n
    return None


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")
    audit = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else None
    src_dirty = subprocess.run(["git", "status", "--porcelain", "--", "src/"],
                               cwd=str(ROOT), capture_output=True,
                               text=True).stdout.strip()

    src0, pre0, post0 = sha(ROOT / CS), sha(PRE), sha(POST)
    checks = run_checks(pre_raw, post_raw, src, audit, src_dirty)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPass, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                           json.loads(POST.read_text(encoding="utf-8")),
                           (ROOT / CS).read_text(encoding="utf-8"), audit,
                           subprocess.run(
                               ["git", "status", "--porcelain", "--", "src/"],
                               cwd=str(ROOT), capture_output=True,
                               text=True).stdout.strip())
            flipped = [x["id"] for x in c if not x["ok"]]
            if expect == "__NO_FLIP__":
                return {"name": name, "why": why, "evidence": ev,
                        "expectFlipped": "（反向对照：期望不翻）",
                        "flipped": flipped, "ok": not flipped}
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped}
        finally:
            restore()

    # ① post raw：把**副本**的绝对 x 挪 +1
    #    ★ 第一版改的是 after 里那个**原**节点（`g-inner`），结果 S1 一点没红。
    #      原因：偏移算的是 `after[副本] − before[源]` ⟹ after 里的原节点
    #      **根本不参与计算**。阴性对照必须打在**被测性质真正读取的字段**上，
    #      否则「变异成功」是假的。
    def break_delta(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "copyNested" and "after" in row:
                    a = {n["id"]: n for n in row["after"]["nodes"]}
                    a[row["copyIds"][0]]["abs"]["x"] += 1
                    return True
        return False

    negs.append(neg(
        "N1 ★★ post raw：把**一个副本**的绝对 x 挪 +1",
        "★ 验证 S1/S2 真的在算「副本 − 源」这个差；偏移一变反推就不唯一",
        lambda: mut_raw("docs/research/liblib-canvas-batch801-2026-10-01/"
                        "raw/vb801a-post.json", break_delta),
        "S1:★★ 偏移由 raw **反推**且所有副本**完全一致**；配对方式显式记账"))

    # ② post raw：把副本的父改回原组 ⟹ S5 必须翻
    def reparent(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "copyNested" and "after" in row:
                    after = {n["id"]: n for n in row["after"]["nodes"]}
                    before = {n["id"]: n for n in row["before"]["nodes"]}
                    groups = [n for n in row["after"]["nodes"]
                              if n["type"] == "storyboard-group"
                              and n["id"] in row["copyIds"]]
                    if len(groups) < 2:
                        return False
                    groups[1]["parentId"] = groups[0]["id"] + "__原组"
                    return True
        return False

    negs.append(neg(
        "N2 ★★ post raw：把副本内层组的父改成一个**不存在的** id",
        "★ 验证 S5 真的在看父是否落在副本集合内",
        lambda: mut_raw("docs/research/liblib-canvas-batch801-2026-10-01/"
                        "raw/vb801a-post.json", reparent),
        "S5:★★ 副本的父指向**副本集合内部**（不是原组）"))

    # ③ post raw：把「副本 id」换成**已存在的原 id** ⟹ S3 必须翻
    #    ★ 不能去删 after 里的节点 —— 那是把 raw 弄成**结构上不自洽**，
    #      探针自己就会 KeyError，读不到结论。阴性对照要改「被测性质」，
    #      不是破坏数据结构。
    def collide(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "copyMember" and "after" in row:
                    orig_id = row["before"]["nodes"][0]["id"]
                    row["copyIds"] = [orig_id]
                    return True
        return False

    negs.append(neg(
        "N3 ★★ post raw：把副本 id 改成与原 id 相同",
        "★ 验证 S3 阳性对照：id 不相交这条不能被绕过",
        lambda: mut_raw("docs/research/liblib-canvas-batch801-2026-10-01/"
                        "raw/vb801a-post.json", collide),
        "S3:★ 阳性对照：副本 id 与原 id 全不相交，且数量符合预期"))

    # ④ 反向对照：只改注释 ⟹ **除了 S10 之外**一项都不该翻
    #    ★ S10 的职责就是「盯 `src/` 有没有被改脏」⟹ 任何改 src 的变异
    #      都必然让它翻。所以「不翻」只能对**与 src 无关**的检查成立，
    #      期望写成「S10 翻、S9 不翻」⟹ 这恰好同时证明 S9 与 S10 各自有效。
    negs.append(neg(
        "N4 ★★ 反向对照：只改 `duplicateGraphSelection` 那段注释的字",
        "★ 证明 S9 锚的是表达式不是某段文本（S10 应当翻：src 确实被改脏了）",
        lambda: mut_text(CS,
                         "  const nodesById = new Map(canvas.nodes.map("
                         "(node) => [node.id, node]));\n"
                         "  const requested = Array.from(new Set("
                         "requestedIds)).filter((id) => nodesById.has(id));",
                         "  const nodesById = new Map(canvas.nodes.map("
                         "(node) => [node.id, node]));\n"
                         "  const requested = Array.from(new Set("
                         "requestedIds)).filter((id) => nodesById.has(id));  // 801 读过",
                         allow_superset=True),
        "S10:★★ 记账：本批**没改** `src/`"))

    restored = {"cs": sha(ROOT / CS) == src0, "pre": sha(PRE) == pre0,
                "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    negs_ok = sum(1 for n in negs if n["ok"])
    report = {"batch": 801, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": negs_ok, "negativesTotal": len(negs),
              "auditSummary": ({"passed": audit["passed"], "total": audit["total"]}
                               if audit else None),
              "restoreSha": {"src": src0, "pre": pre0, "post": post0,
                             "ok": restored}}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (negs_ok, len(negs)))
    print("★ 阴性对照后字节级复原：%r" % restored)
    return 0 if (nPass == len(checks) and negs_ok == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())
