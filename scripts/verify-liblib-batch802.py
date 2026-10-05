#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 802 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

802 是**普查驱动**的一批：799、800 各手工找到一处同类坐标系错误（把相对坐标
当绝对坐标）⟹ 本批先用 TypeScript AST 把「把 nodes 写进 canvas」的**全部**写点
普查出来，再逐个读源码，于是找到第三处 `createImageHdPreset`。

- ★★ **判据不涉及任何常量**：「宿主组移动 Δ，新组也必须移动 Δ」。不需要知道
  源码里的偏移是 320 还是 −60，缺陷（用相对位置时新组纹丝不动）一眼可见。
- ★★ **阴性对照有前提**：loose 臂「祖先偏移为 0」必须被验证，而不是默认成立。
- ★ **阳性对照不可省**（S3）：「组与 child 都没建出来」也会让「新组位置不变」成立。
- ★★ **第四次踩同一个坑**：needle 只写 `createImageHdPreset: (imageNodeId`
  会先命中**接口声明**而不是实现 ⟹ 段长只剩 112、里面没有函数体。
  799（`updateNodeData`）、800（`ungroupSelectedNodes`）、
  801（`duplicateGraphSelection`）各踩过一次。**锚点必须带完整的参数类型标注。**
- ★ **普查的数字必须由机器数出**，不能手写（794 的教训：手写的普查数字本身是错的）。
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch802-2026-10-01"
PRE = OUTDIR / "raw/vb802a-pre.json"
POST = OUTDIR / "raw/vb802a-post.json"
SCAN = OUTDIR / "raw/scan802.json"
AUDIT = OUTDIR / "audit-802.json"
REPORT = OUTDIR / "verify-report.json"
CS = "src/store/canvasStore.ts"
SCANNER = OUTDIR / "probes/scan802.mjs"

NESTED_ARMS = ("presetFromGroupedA", "presetFromGroupedB")
ALL_ARMS = ("presetFromLoose",) + NESTED_ARMS


# ============================================================ 独立实现
def rows_of(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in rd.get("rows", []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def live(tbl, arm):
    return [r for r in tbl.get(arm, []) if not r.get("FAILED")]


def xy(rec):
    return (rec["x"], rec["y"])


def chain_abs(nodes, nid):
    """★ 沿 parentId 链求和（起点是 position，不是 abs）。"""
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
    return (x, y)


def shifts(tbl):
    """两条「源在组内」臂之间的位移对照。"""
    a, b = live(tbl, "presetFromGroupedA"), live(tbl, "presetFromGroupedB")
    out = []
    for x, y in zip(a, b):
        host = (y["hostOrigin"][0] - x["hostOrigin"][0],
                y["hostOrigin"][1] - x["hostOrigin"][1])
        newg = (xy(y["newGroupPos"])[0] - xy(x["newGroupPos"])[0],
                xy(y["newGroupPos"])[1] - xy(x["newGroupPos"])[1])
        out.append({"宿主组移动": host, "新组移动": newg,
                    "跟着动": newg == host})
    return out


# ============================================================ 检查
def strip_lines(o):
    """★ 把 `line` / `ownerLine` 剥掉再比。

    行号绑死在源码位置上，而**本批的修复正好在 :1636 之后插了 7 行** ⟹ 之后 32 个
    动作的行号必然整体 +7，拿行号去比会把「修复存在」误判成「普查不可复现」。
    真正该稳定的是：写点**个数**、fit 调用数、动作名集合、以及每个动作的
    `target` 表达式与风险判定。
    """
    if isinstance(o, dict):
        return {k: strip_lines(v) for k, v in o.items()
                if k not in ("line", "ownerLine")}
    if isinstance(o, list):
        return [strip_lines(v) for v in o]
    return o


def run_checks(pre_raw, post_raw, src, scan, audit):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    pre, post = rows_of(pre_raw), rows_of(post_raw)

    # ── S1a 普查器现场重跑**真的跑起来了**
    # ★★ 802 的坑：原先 scanner 只有固定输出路径 ⟹ 「重跑的」读回来的就是
    #   「入库的」那个文件（本已被覆写），自比恒等；而且 subprocess 的退出码
    #   根本没检查，scanner 崩了照样读旧文件 PASS ⟹ 假绿。
    scan_sha0 = sha(SCAN)
    rerun_path = pathlib.Path("/tmp/scan802-rerun.json")
    if rerun_path.exists():
        rerun_path.unlink()
    proc = subprocess.run(["node", str(SCANNER), str(rerun_path)],
                          cwd=str(ROOT), capture_output=True, text=True)
    rerun = (json.loads(rerun_path.read_text(encoding="utf-8"))
             if rerun_path.exists() else {})
    add("S1a:★★ 普查器现场重跑**真的跑起来了**",
        "★★ 原先 scanner 固定写同一个路径 ⟹「重跑的」就是「入库的」那个文件，"
        "自比恒等；且 subprocess 的退出码根本没检查，崩了也 PASS ⟹ 假绿",
        proc.returncode == 0 and bool(rerun),
        {"退出码": proc.returncode, "stderr 尾": proc.stderr.strip()[-300:],
         "重跑产物": str(rerun_path), "产物非空": bool(rerun),
         "★ 入库文件未被覆写": sha(SCAN) == scan_sha0})

    # ── S1b 三个总数：机器数出，且现场重跑一致
    same = (rerun.get("totalWritePoints") == scan["totalWritePoints"]
            and rerun.get("totalFitCalls") == scan["totalFitCalls"]
            and len(rerun.get("actions", [])) == len(scan["actions"]))
    add("S1b:★★ 普查的三个总数由 AST 数出，且**现场重跑**一致",
        "★ 794 的教训：手写的普查数字本身是错的 ⟹ 数字必须机器产出、还能重跑",
        same and scan["totalWritePoints"] > 0 and scan["totalFitCalls"] > 0,
        {"入库的": {"写点": scan["totalWritePoints"],
                    "动作": len(scan["actions"]),
                    "fit 调用": scan["totalFitCalls"]},
         "重跑的": {"写点": rerun.get("totalWritePoints"),
                    "动作": len(rerun.get("actions", [])),
                    "fit 调用": rerun.get("totalFitCalls")},
         "高风险动作": [a["name"] for a in scan["actions"]
                        if a["risk"].startswith("高")]})

    # ── S1c 剥掉行号后逐动作比对：**除 absHelpers 外必须完全一致**
    A = {a["name"]: strip_lines(a) for a in scan["actions"]}
    B = {a["name"]: strip_lines(a) for a in rerun.get("actions", [])}
    drifted, non_abs = [], []
    for n in sorted(set(A) | set(B)):
        if A.get(n) == B.get(n):
            continue
        fields = sorted({k for k in set(A.get(n, {})) | set(B.get(n, {}))
                         if A.get(n, {}).get(k) != B.get(n, {}).get(k)})
        drifted.append({"动作": n, "不同的字段": fields})
        if fields != ["absHelpers"]:
            non_abs.append(n)
    add("S1c:★★ 剥掉行号后逐动作比对：差异**只可能**落在 absHelpers 上",
        "★ 行号被本批的 +7 行修复整体平移，不能参与比较；但写点数、target "
        "表达式、fit 计数、风险判定一旦漂移就说明普查不可复现",
        bool(rerun) and not non_abs,
        {"动作名集合一致": set(A) == set(B),
         "有差异的动作": drifted,
         "★ 差异越界的动作（必须为空）": non_abs,
         "说明": "createImageHdPreset 的 absHelpers 由 [] 变成 "
                 "[getAbsoluteNodePosition] —— 正是本批那一行修复"})

    # ── S2 阴性对照前提
    ev = []
    for phase, tbl in (("pre", pre), ("post", post)):
        for i, r in enumerate(live(tbl, "presetFromLoose")):
            rc = chain_abs(r["before"]["nodes"], r["sourceId"])
            ev.append({"相位": phase, "轮": i, "独立重算": list(rc) if rc else None,
                       "读数里的绝对": list(xy(r["srcAbs"])),
                       "确实无祖先": rc == xy(r["srcAbs"])})
    add("S2:★★ 阴性对照前提：loose 臂的源**确实**没有祖先",
        "★ 「祖先偏移为 0」是前提，不成立就什么也证明不了",
        ev and all(x["确实无祖先"] for x in ev), ev)

    # ── S3 阳性对照
    ev = []
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in ALL_ARMS:
            for i, r in enumerate(live(tbl, arm)):
                ev.append({"相位": phase, "臂": arm, "轮": i,
                           "子节点数": r["kidsCount"],
                           "都挂在新组下": all(r["kidsParented"])})
    add("S3:★ 阳性对照：组与 child 都建了，child 挂在新组下",
        "★ 否则「什么都没发生」也会让「新组不动」成立 ⟹ 假绿",
        ev and all(x["子节点数"] == 1 and x["都挂在新组下"] for x in ev), ev)

    # ── S4 缺陷复现：pre 里新组不动
    ev = shifts(pre)
    add("S4:★★ 缺陷复现：pre 里宿主组移动了，新组**纹丝不动**",
        "★ 判据本体，完全不涉及常量",
        ev and all(not x["跟着动"] and x["宿主组移动"] != (0, 0) for x in ev), ev)

    # ── S5 修复生效
    ev = shifts(post)
    add("S5:★★★ 修复生效：post 里新组**跟着宿主组**一起动",
        "★ 判据是相对关系 ⟹ 改对改错都判得出来",
        ev and all(x["跟着动"] for x in ev), ev)

    # ── S6 三条臂的「新组 − 源绝对」偏移一致（loose 当基准，不写死）
    ev = {}
    for phase, tbl in (("pre", pre), ("post", post)):
        for arm in ALL_ARMS:
            ds = set()
            for r in live(tbl, arm):
                ds.add((xy(r["newGroupPos"])[0] - xy(r["srcAbs"])[0],
                        xy(r["newGroupPos"])[1] - xy(r["srcAbs"])[1]))
            ev["%s %s" % (phase, arm)] = sorted(list(d) for d in ds)
    post_sets = [tuple(v[0]) for k, v in ev.items()
                 if k.startswith("post") and v]
    add("S6:★★ post 三条臂的「新组 − 源绝对」偏移**完全一致**",
        "★ 基准取自 loose 臂的读数，偏移值不写死",
        post_sets and len(set(post_sets)) == 1,
        {"逐臂": ev, "post 共同偏移": list(post_sets[0]) if post_sets else None})

    # ── S7 无回归
    ev, diff = [], []
    for i, (a, b) in enumerate(zip(live(pre, "presetFromLoose"),
                                    live(post, "presetFromLoose"))):
        same = (xy(a["newGroupPos"]) == xy(b["newGroupPos"])
                and xy(a["srcAbs"]) == xy(b["srcAbs"]))
        ev.append({"轮": i, "一致": same})
        if not same:
            diff.append(i)
    add("S7:★★ 无回归：loose 臂 pre/post **逐位相同**",
        "★ 修复对「祖先偏移为 0」必须是恒等变换",
        ev and not diff, {"比对数": len(ev), "不一致的轮": diff})

    # ── S8 静态锚点（★ needle 必须带完整参数类型标注）
    i0 = src.find("createImageHdPreset: (imageNodeId: string) => {")
    j = src.find("\n  createVideoContinuation: (", i0) if i0 >= 0 else -1
    seg = src[i0:j] if (i0 >= 0 and j > i0) else ""
    has_new = "getAbsoluteNodePosition(source, nodesById)" in seg
    has_old = "source.position.x + 320" in seg
    add("S8:★★ 静态锚点：改用沿父链求和，旧的相对写法已消失",
        "★ 段长要够大（实现有 60 行）；只写半截签名会命中接口声明",
        has_new and not has_old and len(seg) > 500,
        {"段长": len(seg), "用了 getAbsoluteNodePosition": has_new,
         "旧的相对写法仍在": has_old})

    if audit:
        add("S9:汇编器零失败", "汇编器自己的断言必须全绿",
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


def find_row(d, arm, phase_first=True):
    for rd in d["rounds"]:
        for row in rd["rows"]:
            if row.get("arm") == arm and "newGroupPos" in row:
                return row
    return None


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")
    audit = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else None

    src0, pre0, post0 = sha(ROOT / CS), sha(PRE), sha(POST)
    checks = run_checks(pre_raw, post_raw, src, scan, audit)
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
                           (ROOT / CS).read_text(encoding="utf-8"),
                           json.loads(SCAN.read_text(encoding="utf-8")), audit)
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

    # ① post raw：把 A 臂的新组位置改成 B 臂那样 ⟹ 「跟着动」翻转
    def flatten(d):
        a = find_row(d, "presetFromGroupedA")
        b = find_row(d, "presetFromGroupedB")
        if not a or not b:
            return False
        a["newGroupPos"] = dict(b["newGroupPos"])
        return True

    negs.append(neg(
        "N1 ★★ post raw：把 A 臂的新组位置改成与 B 臂相同",
        "★ 验证 S5 真的在看「宿主移动 Δ ⟹ 新组也移动 Δ」，而不只是看坐标好看",
        lambda: mut_raw("docs/research/liblib-canvas-batch802-2026-10-01/"
                        "raw/vb802a-post.json", flatten),
        "S5:★★★ 修复生效：post 里新组**跟着宿主组**一起动"))

    # ② pre raw：让 pre 的 A 臂**也「跟着动」** ⟹ 「缺陷复现」必须翻
    # ★★ 第一版把 A 的新组位置改成与 B **相同**（和 N1 一模一样的变异），翻不了红：
    #   S4 的判据是「新组**不动**」——真实缺陷让新组不动、这个变异也让新组不动，
    #   性质根本没被改变 ⟹ 这是个**坏对照**（801 的教训：对照必须打在性质真正
    #   读取的量上）。正确做法是给 A 一个「移动量恰好等于宿主位移」的位置。
    def fix_pre(d):
        a = find_row(d, "presetFromGroupedA")
        b = find_row(d, "presetFromGroupedB")
        if not a or not b:
            return False
        host = (b["hostOrigin"][0] - a["hostOrigin"][0],
                b["hostOrigin"][1] - a["hostOrigin"][1])
        if host == (0, 0):
            return False
        a["newGroupPos"] = {"x": xy(b["newGroupPos"])[0] - host[0],
                            "y": xy(b["newGroupPos"])[1] - host[1]}
        return True

    negs.append(neg(
        "N2 ★★ pre raw：把 A 臂的新组位置改成「移动量 == 宿主位移」",
        "★★ 验证 S4 抓的确实是「新组不动」这件事。★ 第一版改成与 B 相同 —— "
        "那同样让新组不动，性质没变，翻不了红（坏对照）",
        lambda: mut_raw("docs/research/liblib-canvas-batch802-2026-10-01/"
                        "raw/vb802a-pre.json", fix_pre),
        "S4:★★ 缺陷复现：pre 里宿主组移动了，新组**纹丝不动**"))

    # ③ post raw：把子节点的 parentId 改掉 ⟹ 阳性对照必须翻
    def detach(d):
        row = find_row(d, "presetFromGroupedA")
        if not row:
            return False
        row["kidsParented"] = [False]
        return True

    negs.append(neg(
        "N3 ★★ post raw：把 A 臂的「子节点挂在新组下」改成 False",
        "★ 验证 S3 阳性对照：它拦的是「什么都没发生」那种假绿",
        lambda: mut_raw("docs/research/liblib-canvas-batch802-2026-10-01/"
                        "raw/vb802a-post.json", detach),
        "S3:★ 阳性对照：组与 child 都建了，child 挂在新组下"))

    # ④ 反向对照：只改注释 ⟹ 一项都不该翻
    # ★ 这里 old 是被**完整替换**的（新串并不包含旧串：注释插在行尾、`\n` 之前），
    #   所以用默认的「旧的不在」判据，不能用 allow_superset。
    negs.append(neg(
        "N4 ★★ 反向对照：只改 `createImageHdPreset` 那段注释的字",
        "★ 证明 S8 锚的是表达式不是某段文本",
        lambda: mut_text(CS,
                         "    const nodesById = new Map(canvas.nodes.map("
                         "(node) => [node.id, node]));\n"
                         "    const sourceAbsolute = getAbsoluteNodePosition("
                         "source, nodesById);",
                         "    const nodesById = new Map(canvas.nodes.map("
                         "(node) => [node.id, node]));  // 802 修\n"
                         "    const sourceAbsolute = getAbsoluteNodePosition("
                         "source, nodesById);"),
        "__NO_FLIP__"))

    restored = {"cs": sha(ROOT / CS) == src0, "pre": sha(PRE) == pre0,
                "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    negs_ok = sum(1 for n in negs if n["ok"])
    report = {"batch": 802, "totals": {"passed": nPass, "total": len(checks)},
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
