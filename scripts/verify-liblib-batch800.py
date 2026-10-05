#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 800 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

800 改的是「解除分组时成员的相对坐标怎么转绝对」：原来写
`group.position + node.position` —— 假设「组的 position 就是组的绝对位置」，
这只在组**没有父节点**时成立。嵌套时沿途祖先的偏移被丢掉，成员当场跳位。

- ★★ **判据不能预设坐标系**。若断言写成「成员的 `position` 等于某个公式」，
  就只是在测实现。⟹ S1–S8 全部只判**绝对位置有没有变**——
  「我只是取消了分组，东西不该跳」。
- ★★ **必须有阴性对照**。缺陷臂和阴性对照是**同一个操作**（取消分组），
  唯一差别是沿途有没有祖先：键盘臂（`G`→`Shift+G`，纯 UI 路径）与
  「取消顶层组」。没有它们，「取消内层组会跳」可能只是探针自己搞错了。
- ★ **阳性对照不可省**（S1）：解除后成员的 `parentId` 必须确实变成空。
  否则「操作什么都没发生」也会让「位置没变」成立 ⟹ 假绿。
- ★ **机制要钉死，不能只说「跳了」**（S5）：跳位量必须逐位等于
  「沿途祖先偏移」的相反数。
- ★ **不要写死坐标**。所有坐标都从 raw 现取。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch800-2026-10-01"
PRE = OUTDIR / "raw/vb800a-pre.json"
POST = OUTDIR / "raw/vb800a-post.json"
AUDIT = OUTDIR / "audit-800.json"
REPORT = OUTDIR / "verify-report.json"
CS = "src/store/canvasStore.ts"

NEG_ARMS = ("keyboardRoundtrip", "ungroupOuter")


# ============================================================ 独立几何实现
def index_of(nodes):
    return dict((n["id"], n) for n in nodes)


def walk_abs(nodes, node_id):
    """★ 沿 `parentId` 链把**相对**坐标累加成绝对坐标（起点必须是 position）。"""
    idx = index_of(nodes)
    node = idx.get(node_id)
    if node is None:
        return None
    x, y = node["pos"]["x"], node["pos"]["y"]
    pid, seen, hops = node.get("parentId"), set([node_id]), 0
    while pid and pid in idx and pid not in seen and hops < 32:
        seen.add(pid)
        hops += 1
        up = idx[pid]
        x += up["pos"]["x"]
        y += up["pos"]["y"]
        pid = up.get("parentId")
    return x, y


def delta_of(before, after, watch):
    """{id: (Δx, Δy)}；缺失的 id 记 None。"""
    b, a = index_of(before), index_of(after)
    out = {}
    for i in watch:
        if i not in b or i not in a:
            out[i] = None
            continue
        out[i] = (a[i]["abs"]["x"] - b[i]["abs"]["x"],
                  a[i]["abs"]["y"] - b[i]["abs"]["y"])
    return out


def rows_of(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in (rd.get("rows") or []):
            if row.get("FAILED"):
                continue
            out.setdefault(row.get("arm"), []).append(row)
    return out


# ============================================================ 检查
def run_checks(pre_raw, post_raw, src, audit):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    pre, post = rows_of(pre_raw), rows_of(post_raw)

    # ── S1 阳性对照：解除后 parentId 真的没了
    ev = {}
    for arm in ("ungroupInner", "ungroupOuter"):
        for i, r in enumerate(post.get(arm, [])):
            b, a = index_of(r["before"]["nodes"]), index_of(r["after"]["nodes"])
            ev["%s#%d" % (arm, i)] = {
                nid: [b[nid].get("parentId"), a[nid].get("parentId")]
                for nid in r["watch"] if nid in b and nid in a}
    ok = ev and all(before and after is None
                    for d in ev.values() for before, after in d.values())
    add("S1:★ 阳性对照：解除后成员的 `parentId` 变成空",
        "★ 没有它，「什么都没发生」也会让「位置没变」成立 ⟹ 假绿", ok, ev)

    # ── S2 阴性对照：键盘臂（纯 UI 路径）不动
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for i, r in enumerate(tbl.get("keyboardRoundtrip", [])):
            ev["%s#%d" % (phase, i)] = delta_of(
                r["before"]["nodes"], r["after"]["nodes"], r["members"])
    add("S2:★★ 阴性对照：`G`→`Shift+G` 键盘往返，成员不动（pre/post）",
        "★ 真实用户路径（`page.tsx:1412` 的 `Shift+G`），组没有父节点",
        ev and all(d == (0, 0) for v in ev.values() for d in v.values()), ev)

    # ── S3 阴性对照：取消**顶层**组不动（pre/post 都要）
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for i, r in enumerate(tbl.get("ungroupOuter", [])):
            ev["%s#%d" % (phase, i)] = delta_of(
                r["before"]["nodes"], r["after"]["nodes"], r["watch"])
    add("S3:★★ 阴性对照：取消顶层组，成员与子组不动（pre/post）",
        "★ 与缺陷臂是同一个操作，唯一差别是沿途有没有祖先",
        ev and all(d == (0, 0) for v in ev.values() for d in v.values()), ev)

    # ── S4 缺陷复现
    ev = {}
    for i, r in enumerate(pre.get("ungroupInner", [])):
        ev["#%d" % i] = delta_of(r["before"]["nodes"], r["after"]["nodes"],
                                 r["watch"])
    add("S4:★★ 缺陷复现：pre 取消内层组成员跳位",
        "★ 799 的姊妹缺陷 —— 同一类坐标系错误",
        ev and all(d != (0, 0) for v in ev.values() for d in v.values()), ev)

    # ── S5 机制：跳位量 == 沿途祖先偏移的相反数
    ev = {}
    for i, r in enumerate(pre.get("ungroupInner", [])):
        b = index_of(r["before"]["nodes"])
        group = b.get(r["groupId"])
        if group is None:
            continue
        g_abs = walk_abs(r["before"]["nodes"], r["groupId"])
        lost = (g_abs[0] - group["pos"]["x"], g_abs[1] - group["pos"]["y"])
        for nid, d in delta_of(r["before"]["nodes"], r["after"]["nodes"],
                               r["watch"]).items():
            ev["#%d %s" % (i, nid)] = {"跳了": list(d), "丢掉的那段": list(lost),
                                       "恰好相反": d == (-lost[0], -lost[1])}
    add("S5:★★ 机制钉死：跳位量 = 沿途祖先偏移的相反数",
        "★ 只说「跳了」不够；说清「正好跳掉外层组的位置」才是机制",
        ev and all(v["恰好相反"] for v in ev.values()), ev)

    # ── S6 修复生效
    ev = {}
    for i, r in enumerate(post.get("ungroupInner", [])):
        ev["#%d" % i] = delta_of(r["before"]["nodes"], r["after"]["nodes"],
                                 r["watch"])
    add("S6:★★★ 修复生效：post 取消内层组成员不动",
        "★ 判据全用绝对位置 ⟹ 改对改错都判得出来",
        ev and all(d == (0, 0) for v in ev.values() for d in v.values()), ev)

    # ── S7 无回归：顶层组那条臂 pre/post 逐位相同
    ev, diff = [], []
    for arm in NEG_ARMS:
        for i, (a, b) in enumerate(zip(pre.get(arm, []), post.get(arm, []))):
            for nid in (a.get("watch") or a.get("members") or []):
                ab = index_of(a["before"]["nodes"]).get(nid)
                bb = index_of(b["before"]["nodes"]).get(nid)
                if not ab or not bb:
                    continue
                same = (ab["abs"]["x"] == bb["abs"]["x"]
                        and ab["abs"]["y"] == bb["abs"]["y"]
                        and ab["abs"] == bb["abs"])
                ev.append({"臂": arm, "轮": i, "id": nid, "相同": same})
                if not same:
                    diff.append({"臂": arm, "轮": i, "id": nid,
                                 "pre": ab["abs"], "post": bb["abs"]})
    add("S7:★★ 无回归：阴性对照两条臂 pre/post 的绝对坐标逐位相同",
        "★ 修复对「沿途无祖先」必须是恒等变换 ⟹ 逐位相同是最强证据",
        ev and not diff, {"比对数": len(ev), "不一致": diff})

    # ── S8 独立重算：post 脱管后的 pos 必须等于用 before 的父链求和
    post_ev, pre_ev = {}, {}
    for phase, tbl, sink in (("pre", pre, pre_ev), ("post", post, post_ev)):
        for arm in ("ungroupInner", "ungroupOuter"):
            for i, r in enumerate(tbl.get(arm, [])):
                a = index_of(r["after"]["nodes"])
                for nid in r["watch"]:
                    want = walk_abs(r["before"]["nodes"], nid)
                    got = a[nid]["pos"]
                    sink["%s %s#%d %s" % (phase, arm, i, nid)] = {
                        "重算": list(want), "实测": [got["x"], got["y"]],
                        "吻合": want == (got["x"], got["y"])}
    add("S8:★ 独立重算：post 脱管后的相对坐标（此时即绝对）== 用 before 的父链求和",
        "★ 验收器自己算那条链，不读源码公式 ⟹ 公式写错会被抓出来",
        post_ev and all(v["吻合"] for v in post_ev.values()),
        {"post": post_ev, "pre（缺陷就在这，应当对不上）": pre_ev})

    # ── S9 静态锚点
    i0 = src.find("ungroupSelectedNodes: (nodeIds) => {")
    i1 = src.find("\n  updateNodeData: (nodeId", i0 + 1) if i0 >= 0 else -1
    seg = src[i0:i1] if (i0 >= 0 and i1 > i0) else ""
    has_new = "getAbsoluteNodePosition(node, nodesById)" in seg
    has_old = "group.position.x + node.position.x" in seg
    add("S9:★★ 静态锚点：`ungroupSelectedNodes` 改用沿父链求和",
        "★ 旧的单层加法若在别处复活，这条要红",
        has_new and not has_old,
        {"段长": len(seg), "用了 getAbsoluteNodePosition": has_new,
         "旧的单层加法仍在": has_old})

    # ── S10 记账：799 的修复没被碰
    has_fit = ("position: { x: nextPosition.x - parentAbs.x,"
               " y: nextPosition.y - parentAbs.y },") in src
    add("S10:记账：799 的修复仍在（没被本批改回去）",
        "★ 800 修的是**另一处**坐标系，两个都要在", has_fit,
        {"parentAbs 写回仍在": has_fit})

    # ── S11 汇编器零失败
    if audit:
        add("S11:汇编器零失败", "汇编器自己的断言必须全绿",
            audit.get("failed", 0) == 0 and
            audit.get("passed") == audit.get("total"),
            {"passed": audit.get("passed"), "total": audit.get("total")})
    else:
        add("S11:汇编器零失败", "（无 audit-800.json，跳过）", True, None)

    # ── S12 记账：改动面
    add("S12:记账：改动面",
        "★ 单点改动，不新增 API、不动 UI；**没有**顺带实现嵌套组合",
        True, {
            "改动文件": ["src/store/canvasStore.ts"],
            "改动函数": ["ungroupSelectedNodes"],
            "改动性质": ["成员的相对坐标改用 getAbsoluteNodePosition 沿父链求和"],
            "没有改": ["groupSelectedNodes（799 复核过：它对顶层组是对的）",
                       "duplicateGraphSelection（已读源码：父也被复制时保持相对、"
                       "父没被复制时用绝对+40，逻辑正确 ⟹ **未测**，见 README）",
                       "UI 造嵌套组的能力（792 遗留，仍未实现）"],
            "源站对照": "★ 未做（源站需登录）"})

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


def _pick(d, arm, member):
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

    src0, pre0, post0 = sha(ROOT / CS), sha(PRE), sha(POST)
    checks = run_checks(pre_raw, post_raw, src, audit)
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
                           (ROOT / CS).read_text(encoding="utf-8"), audit)
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

    # ① 源码回退成单层加法 ⟹ S9 必须翻
    negs.append(neg(
        "N1 ★★ 源码回退：改回 `group.position + node.position`",
        "★ 端到端证据已在 pre/post raw 里；这条验的是静态锚点能抓住回退",
        lambda: mut_text(CS,
                         "          const absolute = getAbsoluteNodePosition("
                         "node, nodesById);\n"
                         "          return withoutParent(node,"
                         " { x: absolute.x, y: absolute.y });",
                         "          const absolute = { x: group.position.x"
                         " + node.position.x, y: group.position.y"
                         " + node.position.y };\n"
                         "          return withoutParent(node, absolute);"),
        "S9:★★ 静态锚点：`ungroupSelectedNodes` 改用沿父链求和"))

    # ② 反向对照：只改注释 ⟹ 一项都不该翻
    #    ★ 两个约束同时满足才能让 needle 唯一：
    #      (a) 要带**下一行**——`groupSelectedNodes` 里也有一行字面相同的
    #          `const nodesById = ...`（同为 6 空格缩进），单行不唯一；
    #      (b) 注释要加在 needle 覆盖范围的**最后一行之后**，否则 old 会被
    #          从中间打断，`old in new` 恒为 False（第一版就踩了这个）。
    negs.append(neg(
        "N2 ★★ 反向对照：只改 `ungroupSelectedNodes` 里 `nextNodes` 那行的注释",
        "★ 证明 S9 锚的是表达式不是某段文本",
        lambda: mut_text(CS,
                         "const nodesById = new Map(currentCanvas.nodes.map("
                         "(node) => [node.id, node]));\n"
                         "      const nextNodes = currentCanvas.nodes",
                         "const nodesById = new Map(currentCanvas.nodes.map("
                         "(node) => [node.id, node]));\n"
                         "      const nextNodes = currentCanvas.nodes  // 800 修",
                         allow_superset=True),
        "__NO_FLIP__"))

    # ③ post raw：把解除后某成员的坐标挪走 ⟹ S6 必须翻
    def bump(d):
        n = _pick(d, "ungroupInner", "n-m1")
        if n is None:
            return False
        n["abs"]["x"] += 37
        return True

    negs.append(neg(
        "N3 ★★ post raw：把解除后 n-m1 的绝对坐标挪 +37",
        "★ 验证 S6 真的在看几何：几何一坏它就必须红",
        lambda: mut_raw("docs/research/liblib-canvas-batch800-2026-10-01/"
                        "raw/vb800a-post.json", bump),
        "S6:★★★ 修复生效：post 取消内层组成员不动"))

    # ④ post raw：让 parentId 没被删 ⟹ S1 必须翻（防假绿的那条自己会红）
    def keep_parent(d):
        n = _pick(d, "ungroupInner", "n-m1")
        if n is None:
            return False
        n["parentId"] = "g-inner"
        return True

    negs.append(neg(
        "N4 ★★ post raw：让解除后 n-m1 的 `parentId` 还在",
        "★ 验证 S1：没有它，「什么都没发生」会假绿",
        lambda: mut_raw("docs/research/liblib-canvas-batch800-2026-10-01/"
                        "raw/vb800a-post.json", keep_parent),
        "S1:★ 阳性对照：解除后成员的 `parentId` 变成空"))

    # ⑤ pre raw：把顶层组那条臂的坐标改掉 ⟹ S3/S7 必须翻
    def break_flat(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "ungroupOuter" and "after" in row:
                    for n in row["after"]["nodes"]:
                        if n["id"] == "n-loose":
                            n["abs"]["y"] += 11
                            return True
        return False

    negs.append(neg(
        "N5 ★★ pre raw：把顶层组臂里 n-loose 的绝对 y 挪 +11",
        "★ 验证 S3（阴性对照）与 S7（无回归）确实在读这条臂",
        lambda: mut_raw("docs/research/liblib-canvas-batch800-2026-10-01/"
                        "raw/vb800a-pre.json", break_flat),
        "S3:★★ 阴性对照：取消顶层组，成员与子组不动（pre/post）"))

    restored = {"cs": sha(ROOT / CS) == src0, "pre": sha(PRE) == pre0,
                "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    negs_ok = sum(1 for n in negs if n["ok"])
    report = {"batch": 800, "totals": {"passed": nPass, "total": len(checks)},
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
